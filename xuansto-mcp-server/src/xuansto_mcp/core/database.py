from __future__ import annotations

import contextlib
import json
import sqlite3
import threading
import time
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import KNOWLEDGE_DIR, WORK_DIR
from .logging_config import get_logger

logger = get_logger("database")

DB_PATH = WORK_DIR / "xuansto.db"

_db_lock = threading.Lock()

_CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS workflow_instances (
    id TEXT PRIMARY KEY,
    workflow_type TEXT NOT NULL DEFAULT '',
    current_phase INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'running',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    data_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS session_states (
    id TEXT PRIMARY KEY,
    session_data_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS resource_load_states (
    id TEXT PRIMARY KEY,
    phase INTEGER NOT NULL DEFAULT 0,
    resources_json TEXT NOT NULL DEFAULT '{}',
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS degradation_states (
    id TEXT PRIMARY KEY,
    component_name TEXT NOT NULL DEFAULT '',
    level TEXT NOT NULL DEFAULT 'none',
    data_json TEXT NOT NULL DEFAULT '{}',
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS error_patterns (
    id TEXT PRIMARY KEY,
    pattern TEXT NOT NULL DEFAULT '',
    error_type TEXT NOT NULL DEFAULT '',
    data_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tool_name TEXT NOT NULL DEFAULT '',
    metric_type TEXT NOT NULL DEFAULT '',
    value_json TEXT NOT NULL DEFAULT '{}',
    timestamp TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS decision_records (
    id TEXT PRIMARY KEY,
    workflow_id TEXT NOT NULL DEFAULT '',
    decision_data_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS knowledge_entries (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL DEFAULT '',
    content TEXT NOT NULL DEFAULT '',
    scope TEXT NOT NULL DEFAULT 'general',
    tags_json TEXT NOT NULL DEFAULT '[]',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    sync_status TEXT NOT NULL DEFAULT 'ready',
    deleted_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS reconciliation_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id TEXT NOT NULL DEFAULT '',
    store TEXT NOT NULL DEFAULT '',
    issue_type TEXT NOT NULL DEFAULT '',
    details_json TEXT NOT NULL DEFAULT '{}',
    resolved INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    resolved_at TEXT
);

CREATE TABLE IF NOT EXISTS token_budget_states (
    id TEXT PRIMARY KEY,
    total_budget INTEGER NOT NULL DEFAULT 0,
    used INTEGER NOT NULL DEFAULT 0,
    phase_allocations_json TEXT NOT NULL DEFAULT '{}',
    usage_by_phase_json TEXT NOT NULL DEFAULT '{}',
    session_id TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS experience_patterns (
    id TEXT PRIMARY KEY,
    error_type TEXT NOT NULL DEFAULT '',
    pattern_json TEXT NOT NULL DEFAULT '{}',
    confidence REAL NOT NULL DEFAULT 0.0,
    status TEXT NOT NULL DEFAULT 'active',
    occurrence_count INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS agent_states (
    agent_id TEXT PRIMARY KEY,
    agent_name TEXT NOT NULL,
    agent_type TEXT NOT NULL,
    phase INTEGER,
    status TEXT DEFAULT 'active',
    config_json TEXT,
    created_at REAL,
    updated_at REAL
);

CREATE TABLE IF NOT EXISTS workflow_states (
    workflow_id TEXT PRIMARY KEY,
    workflow_type TEXT NOT NULL,
    current_phase INTEGER DEFAULT 0,
    project_path TEXT,
    completed_phases_json TEXT,
    tasks_json TEXT,
    decisions_json TEXT,
    status TEXT DEFAULT 'active',
    created_at REAL,
    updated_at REAL
);
"""

_CREATE_INDEXES_SQL = """
CREATE INDEX IF NOT EXISTS idx_workflow_instances_status ON workflow_instances(status);
CREATE INDEX IF NOT EXISTS idx_workflow_instances_updated_at ON workflow_instances(updated_at);
CREATE INDEX IF NOT EXISTS idx_session_states_updated_at ON session_states(updated_at);
CREATE INDEX IF NOT EXISTS idx_resource_load_states_phase ON resource_load_states(phase);
CREATE INDEX IF NOT EXISTS idx_degradation_states_component ON degradation_states(component_name);
CREATE INDEX IF NOT EXISTS idx_error_patterns_error_type ON error_patterns(error_type);
CREATE INDEX IF NOT EXISTS idx_metrics_tool_name ON metrics(tool_name);
CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp);
CREATE INDEX IF NOT EXISTS idx_metrics_metric_type ON metrics(metric_type);
CREATE INDEX IF NOT EXISTS idx_decision_records_workflow_id ON decision_records(workflow_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_entries_scope ON knowledge_entries(scope);
CREATE INDEX IF NOT EXISTS idx_knowledge_entries_deleted_at ON knowledge_entries(deleted_at);
CREATE INDEX IF NOT EXISTS idx_reconciliation_log_resolved ON reconciliation_log(resolved);
CREATE INDEX IF NOT EXISTS idx_reconciliation_log_entry_id ON reconciliation_log(entry_id);
CREATE INDEX IF NOT EXISTS idx_token_budget_states_session ON token_budget_states(session_id);
CREATE INDEX IF NOT EXISTS idx_experience_patterns_error_type ON experience_patterns(error_type);
CREATE INDEX IF NOT EXISTS idx_experience_patterns_status ON experience_patterns(status);
CREATE INDEX IF NOT EXISTS idx_agent_states_status ON agent_states(status);
CREATE INDEX IF NOT EXISTS idx_agent_states_agent_type ON agent_states(agent_type);
CREATE INDEX IF NOT EXISTS idx_workflow_states_status ON workflow_states(status);
CREATE INDEX IF NOT EXISTS idx_workflow_states_workflow_type ON workflow_states(workflow_type);
"""


def get_db() -> sqlite3.Connection:
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    with _db_lock:
        conn = get_db()
        try:
            conn.executescript(_CREATE_TABLES_SQL)
            conn.executescript(_CREATE_INDEXES_SQL)
            with contextlib.suppress(Exception):
                conn.execute("ALTER TABLE knowledge_entries ADD COLUMN sync_status TEXT NOT NULL DEFAULT 'ready'")
            conn.commit()
            logger.info("Database initialized at %s", DB_PATH)
        except Exception as exc:
            logger.error("Failed to initialize database: %s", exc)
            raise
        finally:
            conn.close()


def cleanup_metrics(older_than_days: int = 30) -> int:
    from datetime import timedelta
    cutoff = (datetime.now(timezone.utc) - timedelta(days=older_than_days)).isoformat()
    with _db_lock:
        conn = get_db()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM metrics WHERE timestamp < ?", (cutoff,))
            deleted = cursor.rowcount
            conn.commit()
            if deleted > 0:
                logger.info("Cleaned up %d metrics older than %d days", deleted, older_than_days)
            return deleted
        finally:
            conn.close()


def persist_state(table: str, data: dict[str, Any]) -> None:
    _VALID_TABLES = {
        "workflow_instances", "session_states", "resource_load_states",
        "degradation_states", "error_patterns", "metrics",
        "decision_records", "knowledge_entries", "reconciliation_log",
        "token_budget_states", "experience_patterns",
    }
    _AUTO_INCREMENT_TABLES = {"metrics", "reconciliation_log"}
    if table not in _VALID_TABLES:
        logger.warning("Attempted to persist to invalid table: %s", table)
        return

    now = datetime.now(timezone.utc).isoformat()
    row_id = data.get("id")
    is_auto_increment = table in _AUTO_INCREMENT_TABLES and not row_id

    json_fields = {}
    plain_fields = {}
    for key, value in data.items():
        if key == "id":
            continue
        if key.endswith("_json") and not isinstance(value, str):
            json_fields[key] = json.dumps(value, ensure_ascii=False)
        else:
            plain_fields[key] = value

    all_fields = dict(plain_fields)
    all_fields.update(json_fields)

    if "updated_at" not in all_fields and table not in _AUTO_INCREMENT_TABLES:
        all_fields["updated_at"] = now
    if "created_at" not in all_fields and table not in _AUTO_INCREMENT_TABLES:
        all_fields["created_at"] = now

    with _db_lock:
        conn = get_db()
        try:
            if is_auto_increment:
                columns = list(all_fields.keys())
                placeholders = ", ".join(["?"] * len(columns))
                col_str = ", ".join(columns)
                values = list(all_fields.values())
                insert_sql = f"INSERT INTO {table} ({col_str}) VALUES ({placeholders})"
                conn.execute(insert_sql, values)
            else:
                if not row_id:
                    logger.warning("persist_state requires 'id' in data for table %s", table)
                    return
                columns = ["id"] + list(all_fields.keys())
                placeholders = ", ".join(["?"] * len(columns))
                col_str = ", ".join(columns)
                values = [row_id] + list(all_fields.values())
                update_sets = ", ".join(f"{col} = excluded.{col}" for col in all_fields)
                upsert_sql = f"INSERT INTO {table} ({col_str}) VALUES ({placeholders}) ON CONFLICT(id) DO UPDATE SET {update_sets}"
                conn.execute(upsert_sql, values)
            conn.commit()
        except Exception as exc:
            logger.error("Failed to persist state to %s: %s", table, exc)
            raise
        finally:
            conn.close()


def load_state(table: str, query: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    _VALID_TABLES = {
        "workflow_instances", "session_states", "resource_load_states",
        "degradation_states", "error_patterns", "metrics",
        "decision_records", "knowledge_entries", "reconciliation_log",
        "token_budget_states", "experience_patterns",
    }
    if table not in _VALID_TABLES:
        logger.warning("Attempted to load from invalid table: %s", table)
        return []

    conn = get_db()
    try:
        if query:
            conditions = []
            params: list[Any] = []
            for key, value in query.items():
                conditions.append(f"{key} = ?")
                params.append(value)
            where_clause = " WHERE " + " AND ".join(conditions)
            cursor = conn.execute(f"SELECT * FROM {table}{where_clause}", params)
        else:
            cursor = conn.execute(f"SELECT * FROM {table}")
        rows = cursor.fetchall()
        results = []
        for row in rows:
            d = dict(row)
            for key in list(d.keys()):
                if key.endswith("_json") and isinstance(d[key], str):
                    with contextlib.suppress(json.JSONDecodeError, TypeError):
                        d[key] = json.loads(d[key])
            results.append(d)
        return results
    except Exception as exc:
        logger.error("Failed to load state from %s: %s", table, exc)
        return []
    finally:
        conn.close()


def persist_knowledge_dual_write(
    entry_id: str,
    data: dict[str, Any],
    chroma_write_fn: Callable[[str, dict[str, Any]], bool] | None = None,
) -> dict[str, Any]:
    data["sync_status"] = "pending"
    persist_state("knowledge_entries", {"id": entry_id, **data})

    if chroma_write_fn is not None:
        try:
            success = chroma_write_fn(entry_id, data)
            if success:
                data["sync_status"] = "ready"
                persist_state("knowledge_entries", {"id": entry_id, **data})
                return {"status": "synced", "entry_id": entry_id}
            else:
                persist_state("reconciliation_log", {
                    "entry_id": entry_id,
                    "store": "chromadb",
                    "issue_type": "write_failed",
                    "details_json": {"reason": "chroma_write_returned_false"},
                    "created_at": datetime.now(timezone.utc).isoformat(),
                })
                return {"status": "pending", "entry_id": entry_id}
        except Exception as exc:
            persist_state("reconciliation_log", {
                "entry_id": entry_id,
                "store": "chromadb",
                "issue_type": "write_error",
                "details_json": {"reason": str(exc)},
                "created_at": datetime.now(timezone.utc).isoformat(),
            })
            return {"status": "pending", "entry_id": entry_id}

    return {"status": "pending", "entry_id": entry_id}


def reconcile_knowledge_stores(
    chroma_write_fn: Callable[[str, dict[str, Any]], bool] | None = None,
) -> dict[str, Any]:
    conn = get_db()
    try:
        cursor = conn.execute("SELECT * FROM knowledge_entries WHERE deleted_at IS NULL")
        all_entries = [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()

    pending_entries = [e for e in all_entries if e.get("sync_status") != "ready"]

    total = len(pending_entries)
    repaired = 0
    failed = 0

    for entry in pending_entries:
        entry_id = entry.get("id", "")
        entry_data: dict[str, Any] = {}
        for key, value in entry.items():
            if key.endswith("_json") and isinstance(value, str):
                try:
                    entry_data[key] = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    entry_data[key] = value
            else:
                entry_data[key] = value

        if chroma_write_fn is not None:
            try:
                success = chroma_write_fn(entry_id, entry_data)
                if success:
                    entry_data["sync_status"] = "ready"
                    persist_state("knowledge_entries", {"id": entry_id, **entry_data})
                    persist_state("reconciliation_log", {
                        "entry_id": entry_id,
                        "store": "chromadb",
                        "issue_type": "repair_success",
                        "details_json": {"original_status": entry.get("sync_status", "unknown")},
                        "resolved": 1,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    })
                    repaired += 1
                else:
                    persist_state("reconciliation_log", {
                        "entry_id": entry_id,
                        "store": "chromadb",
                        "issue_type": "repair_failed",
                        "details_json": {"reason": "chroma_write_returned_false"},
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    })
                    failed += 1
            except Exception as exc:
                persist_state("reconciliation_log", {
                    "entry_id": entry_id,
                    "store": "chromadb",
                    "issue_type": "repair_failed",
                    "details_json": {"reason": str(exc)},
                    "created_at": datetime.now(timezone.utc).isoformat(),
                })
                failed += 1
        else:
            failed += 1

    success_rate = (repaired / total * 100) if total > 0 else 100.0

    return {
        "total_pending": total,
        "repaired": repaired,
        "failed": failed,
        "success_rate": round(success_rate, 1),
    }


def cleanup_stale_pending_entries(
    max_age_hours: int = 24,
    chroma_write_fn: Callable[[str, dict[str, Any]], bool] | None = None,
) -> dict[str, Any]:
    from datetime import timedelta

    cutoff = (datetime.now(timezone.utc) - timedelta(hours=max_age_hours)).isoformat()
    conn = get_db()
    try:
        cursor = conn.execute(
            "SELECT * FROM knowledge_entries WHERE sync_status != 'ready' AND updated_at < ? AND deleted_at IS NULL",
            (cutoff,),
        )
        stale_entries = [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()

    retried = 0
    purged = 0
    failed = 0

    for entry in stale_entries:
        entry_id = entry.get("id", "")
        entry_data: dict[str, Any] = {}
        for key, value in entry.items():
            if key.endswith("_json") and isinstance(value, str):
                try:
                    entry_data[key] = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    entry_data[key] = value
            else:
                entry_data[key] = value

        if chroma_write_fn is not None:
            try:
                success = chroma_write_fn(entry_id, entry_data)
                if success:
                    entry_data["sync_status"] = "ready"
                    persist_state("knowledge_entries", {"id": entry_id, **entry_data})
                    persist_state("reconciliation_log", {
                        "entry_id": entry_id,
                        "store": "chromadb",
                        "issue_type": "stale_retry_success",
                        "details_json": {"original_status": entry.get("sync_status", "unknown"), "age_hours": max_age_hours},
                        "resolved": 1,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    })
                    retried += 1
                    continue
            except Exception:
                pass

        now = datetime.now(timezone.utc).isoformat()
        persist_state("knowledge_entries", {"id": entry_id, "deleted_at": now})
        persist_state("reconciliation_log", {
            "entry_id": entry_id,
            "store": "chromadb",
            "issue_type": "stale_purged",
            "details_json": {"reason": "exceeded_max_age", "max_age_hours": max_age_hours},
            "resolved": 1,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        purged += 1

    total = len(stale_entries)
    return {
        "total_stale": total,
        "retried": retried,
        "purged": purged,
        "failed": failed,
    }


def migrate_experience_patterns_from_json(json_path: Path | None = None) -> dict[str, Any]:
    if json_path is None:
        json_path = KNOWLEDGE_DIR / "experience_patterns.json"
    if not json_path.exists():
        return {"migrated": 0, "reason": "no_json_file"}
    import json as json_mod
    try:
        data = json_mod.loads(json_path.read_text(encoding="utf-8"))
    except (json_mod.JSONDecodeError, OSError):
        return {"migrated": 0, "reason": "invalid_json"}

    count = 0
    patterns = data if isinstance(data, list) else data.get("patterns", [])
    for pattern in patterns:
        if isinstance(pattern, dict) and "id" in pattern:
            persist_state("experience_patterns", pattern)
            count += 1
    return {"migrated": count}


_FTS5_AVAILABLE: bool | None = None


def is_fts5_available() -> bool:
    global _FTS5_AVAILABLE
    if _FTS5_AVAILABLE is not None:
        return _FTS5_AVAILABLE
    try:
        import sqlite3 as _sqlite3
        conn = _sqlite3.connect(":memory:")
        conn.execute("CREATE VIRTUAL TABLE fts5_test USING fts5(content)")
        conn.execute("DROP TABLE fts5_test")
        conn.close()
        _FTS5_AVAILABLE = True
    except Exception:
        _FTS5_AVAILABLE = False
    return _FTS5_AVAILABLE


def rollback_schema(version: str) -> dict[str, Any]:
    return {"status": "not_supported", "version": version, "message": "Schema rollback is not yet supported. Use backup/restore instead."}


def cleanup_knowledge_versions(keep_last_n: int = 10, keep_marked: bool = True) -> dict[str, Any]:
    with _db_lock:
        conn = get_db()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM knowledge_entries WHERE deleted_at IS NULL")
            total_active = cursor.fetchone()[0]
            cursor.execute(
                "SELECT scope, title, COUNT(*) as cnt "
                "FROM knowledge_entries "
                "WHERE deleted_at IS NULL "
                "GROUP BY scope, title "
                "HAVING cnt > ?",
                (keep_last_n,),
            )
            groups_to_clean = cursor.fetchall()
            total_deleted = 0
            details: list[dict[str, Any]] = []
            for row in groups_to_clean:
                scope = row["scope"] if "scope" in row else row[0]
                title = row["title"] if "title" in row else row[1]
                count = row["cnt"] if "cnt" in row else row[2]
                if keep_marked:
                    cursor.execute(
                        "SELECT id, metadata_json FROM knowledge_entries "
                        "WHERE scope = ? AND title = ? AND deleted_at IS NULL "
                        "ORDER BY updated_at DESC",
                        (scope, title),
                    )
                    all_entries = cursor.fetchall()
                    ids_to_delete = []
                    for i, entry in enumerate(all_entries):
                        if i < keep_last_n:
                            continue
                        metadata = {}
                        raw_meta = entry["metadata_json"] if "metadata_json" in entry else entry[1]
                        if isinstance(raw_meta, str):
                            with contextlib.suppress(json.JSONDecodeError, TypeError):
                                metadata = json.loads(raw_meta)
                        elif isinstance(raw_meta, dict):
                            metadata = raw_meta
                        if metadata.get("important"):
                            continue
                        ids_to_delete.append(entry["id"] if "id" in entry else entry[0])
                else:
                    cursor.execute(
                        "SELECT id FROM knowledge_entries "
                        "WHERE scope = ? AND title = ? AND deleted_at IS NULL "
                        "ORDER BY updated_at DESC "
                        "LIMIT -1 OFFSET ?",
                        (scope, title, keep_last_n),
                    )
                    ids_to_delete = [r["id"] if "id" in r else r[0] for r in cursor.fetchall()]
                if ids_to_delete:
                    placeholders = ", ".join(["?"] * len(ids_to_delete))
                    now = datetime.now(timezone.utc).isoformat()
                    cursor.execute(
                        f"UPDATE knowledge_entries SET deleted_at = ? WHERE id IN ({placeholders})",
                        [now] + ids_to_delete,
                    )
                    deleted_count = cursor.rowcount
                    total_deleted += deleted_count
                    details.append({
                        "scope": scope,
                        "title": title,
                        "total_versions": count,
                        "deleted": deleted_count,
                        "kept": count - deleted_count,
                    })
            conn.commit()
            logger.info("Knowledge version cleanup: deleted %d entries across %d groups", total_deleted, len(details))
            return {
                "total_active_before": total_active,
                "total_deleted": total_deleted,
                "groups_processed": len(details),
                "keep_last_n": keep_last_n,
                "keep_marked": keep_marked,
                "details": details,
            }
        except Exception as exc:
            logger.error("Knowledge version cleanup failed: %s", exc)
            return {"error": True, "message": str(exc), "total_deleted": 0}
        finally:
            conn.close()


def save_agent_state(
    agent_id: str,
    name: str,
    agent_type: str,
    phase: int | None = None,
    status: str = "active",
    config: dict[str, Any] | None = None,
) -> None:
    now = time.time()
    config_json = json.dumps(config, ensure_ascii=False) if config else None
    with _db_lock:
        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO agent_states (agent_id, agent_name, agent_type, phase, status, config_json, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(agent_id) DO UPDATE SET "
                "agent_name=excluded.agent_name, agent_type=excluded.agent_type, "
                "phase=excluded.phase, status=excluded.status, config_json=excluded.config_json, "
                "updated_at=excluded.updated_at",
                (agent_id, name, agent_type, phase, status, config_json, now, now),
            )
            conn.commit()
            logger.debug("Saved agent state: %s", agent_id)
        except Exception as exc:
            logger.error("Failed to save agent state for %s: %s", agent_id, exc)
        finally:
            conn.close()


def load_agent_states(status: str | None = "active") -> list[dict[str, Any]]:
    try:
        conn = get_db()
        try:
            if status is not None:
                cursor = conn.execute(
                    "SELECT agent_id, agent_name, agent_type, phase, status, config_json, created_at, updated_at "
                    "FROM agent_states WHERE status = ?",
                    (status,),
                )
            else:
                cursor = conn.execute(
                    "SELECT agent_id, agent_name, agent_type, phase, status, config_json, created_at, updated_at "
                    "FROM agent_states",
                )
            rows = cursor.fetchall()
            results: list[dict[str, Any]] = []
            for row in rows:
                d = dict(row)
                if d.get("config_json") and isinstance(d["config_json"], str):
                    with contextlib.suppress(json.JSONDecodeError, TypeError):
                        d["config_json"] = json.loads(d["config_json"])
                results.append(d)
            return results
        finally:
            conn.close()
    except Exception as exc:
        logger.error("Failed to load agent states: %s", exc)
        return []


def delete_agent_state(agent_id: str) -> None:
    with _db_lock:
        conn = get_db()
        try:
            conn.execute("DELETE FROM agent_states WHERE agent_id = ?", (agent_id,))
            conn.commit()
            logger.debug("Deleted agent state: %s", agent_id)
        except Exception as exc:
            logger.error("Failed to delete agent state for %s: %s", agent_id, exc)
        finally:
            conn.close()


def save_workflow_state(
    workflow_id: str,
    workflow_type: str,
    current_phase: int = 0,
    project_path: str | None = None,
    completed_phases: list[int] | None = None,
    tasks: dict[str, Any] | None = None,
    decisions: dict[str, Any] | None = None,
    status: str = "active",
) -> None:
    now = time.time()
    completed_phases_json = json.dumps(completed_phases, ensure_ascii=False) if completed_phases is not None else None
    tasks_json = json.dumps(tasks, ensure_ascii=False) if tasks is not None else None
    decisions_json = json.dumps(decisions, ensure_ascii=False) if decisions is not None else None
    with _db_lock:
        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO workflow_states (workflow_id, workflow_type, current_phase, project_path, "
                "completed_phases_json, tasks_json, decisions_json, status, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(workflow_id) DO UPDATE SET "
                "workflow_type=excluded.workflow_type, current_phase=excluded.current_phase, "
                "project_path=excluded.project_path, completed_phases_json=excluded.completed_phases_json, "
                "tasks_json=excluded.tasks_json, decisions_json=excluded.decisions_json, "
                "status=excluded.status, updated_at=excluded.updated_at",
                (workflow_id, workflow_type, current_phase, project_path,
                 completed_phases_json, tasks_json, decisions_json, status, now, now),
            )
            conn.commit()
            logger.debug("Saved workflow state: %s", workflow_id)
        except Exception as exc:
            logger.error("Failed to save workflow state for %s: %s", workflow_id, exc)
        finally:
            conn.close()


def load_workflow_states(status: str | None = "active") -> list[dict[str, Any]]:
    try:
        conn = get_db()
        try:
            if status is not None:
                cursor = conn.execute(
                    "SELECT workflow_id, workflow_type, current_phase, project_path, "
                    "completed_phases_json, tasks_json, decisions_json, status, created_at, updated_at "
                    "FROM workflow_states WHERE status = ?",
                    (status,),
                )
            else:
                cursor = conn.execute(
                    "SELECT workflow_id, workflow_type, current_phase, project_path, "
                    "completed_phases_json, tasks_json, decisions_json, status, created_at, updated_at "
                    "FROM workflow_states",
                )
            rows = cursor.fetchall()
            results: list[dict[str, Any]] = []
            for row in rows:
                d = dict(row)
                for key in ("completed_phases_json", "tasks_json", "decisions_json"):
                    if d.get(key) and isinstance(d[key], str):
                        with contextlib.suppress(json.JSONDecodeError, TypeError):
                            d[key] = json.loads(d[key])
                results.append(d)
            return results
        finally:
            conn.close()
    except Exception as exc:
        logger.error("Failed to load workflow states: %s", exc)
        return []


def delete_workflow_state(workflow_id: str) -> None:
    with _db_lock:
        conn = get_db()
        try:
            conn.execute("DELETE FROM workflow_states WHERE workflow_id = ?", (workflow_id,))
            conn.commit()
            logger.debug("Deleted workflow state: %s", workflow_id)
        except Exception as exc:
            logger.error("Failed to delete workflow state for %s: %s", workflow_id, exc)
        finally:
            conn.close()
