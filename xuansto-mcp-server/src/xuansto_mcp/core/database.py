from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import WORK_DIR
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
    deleted_at TEXT,
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
        "decision_records", "knowledge_entries",
    }
    _AUTO_INCREMENT_TABLES = {"metrics"}
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
        "decision_records", "knowledge_entries",
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
