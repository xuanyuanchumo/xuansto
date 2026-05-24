from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from .config import WORK_DIR, KNOWLEDGE_DIR
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
            try:
                conn.execute("ALTER TABLE knowledge_entries ADD COLUMN sync_status TEXT NOT NULL DEFAULT 'ready'")
            except Exception:
                pass
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
                update_sets = ", ".join(f"{col} = excluded.{col}" for col in all_fields.keys())
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
                    try:
                        d[key] = json.loads(d[key])
                    except (json.JSONDecodeError, TypeError):
                        pass
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
