from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from ..core import atomic_write
from ..core.config import WORK_DIR
from ..core.database import is_fts5_available, persist_state
from ..core.errors import ERR_NOT_FOUND, ERR_VALIDATION, make_error_response, make_success_response
from ..core.logging_config import get_logger
from ..core.notifications import notify
from ..core.validator import validate_input
from ..models.schemas import DecisionLogInput

logger = get_logger("decision_log")

DECISIONS_DB = WORK_DIR / "decisions.db"
DECISIONS_JSON_FILE = WORK_DIR / "decisions.json"
DECISIONS_FILE = DECISIONS_JSON_FILE

_cache: dict[str, dict[str, Any]] = {}
_cache_lock = threading.Lock()
_db_lock = threading.Lock()

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS decisions (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL DEFAULT '',
    context TEXT NOT NULL DEFAULT '',
    decision TEXT NOT NULL DEFAULT '',
    rationale TEXT NOT NULL DEFAULT '',
    alternatives TEXT NOT NULL DEFAULT '[]',
    status TEXT NOT NULL DEFAULT 'proposed',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
"""

_CREATE_FTS_SQL = """
CREATE VIRTUAL TABLE IF NOT EXISTS decisions_fts USING fts5(
    id UNINDEXED,
    title,
    context,
    decision,
    content='decisions',
    content_rowid='rowid'
)
"""

_CREATE_FTS_TRIGGERS_SQL = """
CREATE TRIGGER IF NOT EXISTS decisions_fts_ai AFTER INSERT ON decisions BEGIN
    INSERT INTO decisions_fts(rowid, id, title, context, decision)
    VALUES (new.rowid, new.id, new.title, new.context, new.decision);
END;

CREATE TRIGGER IF NOT EXISTS decisions_fts_ad AFTER DELETE ON decisions BEGIN
    INSERT INTO decisions_fts(decisions_fts, rowid, id, title, context, decision)
    VALUES ('delete', old.rowid, old.id, old.title, old.context, old.decision);
END;

CREATE TRIGGER IF NOT EXISTS decisions_fts_au AFTER UPDATE ON decisions BEGIN
    INSERT INTO decisions_fts(decisions_fts, rowid, id, title, context, decision)
    VALUES ('delete', old.rowid, old.id, old.title, old.context, old.decision);
    INSERT INTO decisions_fts(rowid, id, title, context, decision)
    VALUES (new.rowid, new.id, new.title, new.context, new.decision);
END;
"""

_CREATE_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_decisions_status ON decisions(status);
CREATE INDEX IF NOT EXISTS idx_decisions_created_at ON decisions(created_at);
"""


def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DECISIONS_DB))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _write_decision_file(entry: dict[str, Any]) -> None:
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    existing: list[dict[str, Any]] = []
    if DECISIONS_JSON_FILE.exists():
        try:
            existing = json.loads(DECISIONS_JSON_FILE.read_text(encoding="utf-8"))
            if not isinstance(existing, list):
                existing = []
        except (json.JSONDecodeError, OSError):
            existing = []
    existing.append(entry)
    atomic_write(DECISIONS_JSON_FILE, json.dumps(existing, ensure_ascii=False, indent=2))


def _ensure_db() -> None:
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    with _db_lock:
        conn = _get_connection()
        try:
            conn.executescript(_CREATE_TABLE_SQL)
            try:
                conn.executescript(_CREATE_FTS_SQL)
                conn.executescript(_CREATE_FTS_TRIGGERS_SQL)
            except sqlite3.OperationalError:
                logger.debug("FTS5 not available for decisions, falling back to LIKE search")
            conn.executescript(_CREATE_INDEX_SQL)
            conn.commit()
        finally:
            conn.close()


def _migrate_json_to_sqlite() -> None:
    if not DECISIONS_JSON_FILE.exists():
        return
    try:
        data = json.loads(DECISIONS_JSON_FILE.read_text(encoding="utf-8"))
        if not isinstance(data, list) or not data:
            return
    except (json.JSONDecodeError, OSError):
        return

    with _db_lock:
        conn = _get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM decisions")
            count = cursor.fetchone()[0]
            if count > 0:
                return
            for entry in data:
                entry_id = entry.get("id", "")
                if not entry_id:
                    continue
                cursor.execute(
                    "INSERT OR IGNORE INTO decisions (id, title, context, decision, rationale, alternatives, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        entry_id,
                        entry.get("title", ""),
                        entry.get("context", ""),
                        entry.get("decision", ""),
                        entry.get("rationale", ""),
                        json.dumps(entry.get("alternatives", []), ensure_ascii=False),
                        entry.get("status", "proposed"),
                        entry.get("created_at", ""),
                        entry.get("updated_at", entry.get("created_at", "")),
                    ),
                )
            conn.commit()
            logger.info("Migrated %d decisions from JSON to SQLite", len(data))
        except Exception as exc:
            logger.warning("Failed to migrate decisions JSON to SQLite: %s", exc)
        finally:
            conn.close()


_ensure_db()
_migrate_json_to_sqlite()


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    d = dict(row)
    try:
        d["alternatives"] = json.loads(d.get("alternatives", "[]"))
    except (json.JSONDecodeError, TypeError):
        d["alternatives"] = []
    return d


def _log_decision(
    title: str | None = None,
    description: str | None = None,
    context: str | None = None,
    alternatives: list[str] | None = None,
    decision: str | None = None,
    rationale: str | None = None,
    impact: str | None = None,
    decided_by: str | None = None,
    status: str | None = None,
) -> dict[str, Any]:
    now = datetime.now()
    entry_id = ""
    now_iso = now.isoformat()
    valid_status = status if status in ("proposed", "accepted", "deprecated", "superseded") else "proposed"
    alts_json = json.dumps(alternatives or [], ensure_ascii=False)
    entry: dict[str, Any] = {
        "id": "",
        "title": title or "",
        "description": description or "",
        "context": context or "",
        "alternatives": alternatives or [],
        "decision": decision or "",
        "rationale": rationale or "",
        "impact": impact or "",
        "decided_by": decided_by or "",
        "status": valid_status,
        "created_at": now_iso,
        "updated_at": now_iso,
    }

    with _db_lock:
        conn = _get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM decisions WHERE created_at LIKE ?", (now.strftime("%Y-%m-%d") + "%",))
            day_count = cursor.fetchone()[0]
            entry_id = f"ADR-{now.strftime('%Y%m%d')}-{day_count + 1:03d}"
            entry["id"] = entry_id
            cursor.execute(
                "INSERT INTO decisions (id, title, context, decision, rationale, alternatives, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (entry_id, title or "", context or "", decision or "", rationale or "", alts_json, valid_status, now_iso, now_iso),
            )
            conn.commit()

            try:
                _write_decision_file(entry)
            except Exception as file_exc:
                logger.warning("Decision file write failed for %s, rolling back SQLite: %s", entry_id, file_exc)
                try:
                    cursor.execute("DELETE FROM decisions WHERE id = ?", (entry_id,))
                    conn.commit()
                except Exception as rollback_exc:
                    logger.error("Failed to rollback SQLite decision for %s: %s", entry_id, rollback_exc)
                raise

            with _cache_lock:
                _cache[entry_id] = entry
        except Exception:
            raise
        finally:
            conn.close()

    notify(f"Decision logged: {entry_id} - {title or 'untitled'}", "info")
    try:
        persist_state("decision_records", {
            "id": entry_id,
            "workflow_id": "",
            "decision_data_json": {
                "title": title or "",
                "context": context or "",
                "decision": decision or "",
                "rationale": rationale or "",
                "alternatives": alternatives or [],
                "status": valid_status,
            },
            "created_at": now_iso,
        })
    except Exception:
        logger.debug("Failed to dual-write decision_record for %s", entry_id)
    return {"id": entry_id, "entry": entry, "total_decisions": _get_total_count()}


def _get_total_count() -> int:
    conn = _get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM decisions")
        return cursor.fetchone()[0]
    finally:
        conn.close()


def _list_decisions(
    limit: int = 20,
    offset: int = 0,
    status: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict[str, Any]:
    conn = _get_connection()
    try:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        conditions: list[str] = []
        params: list[Any] = []
        if status:
            conditions.append("status = ?")
            params.append(status)
        if date_from:
            conditions.append("created_at >= ?")
            params.append(date_from)
        if date_to:
            conditions.append("created_at <= ?")
            params.append(date_to)
        where_clause = (" WHERE " + " AND ".join(conditions)) if conditions else ""
        cursor.execute(f"SELECT COUNT(*) FROM decisions{where_clause}", params)
        total = cursor.fetchone()[0]
        cursor.execute(
            f"SELECT * FROM decisions{where_clause} ORDER BY created_at DESC LIMIT ? OFFSET ?",
            params + [limit, offset],
        )
        rows = cursor.fetchall()
        results = [_row_to_dict(row) for row in rows]
        return {"results": results, "total": total, "limit": limit, "offset": offset}
    finally:
        conn.close()


def _query_decisions(
    keyword: str | None = None,
    tag: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> dict[str, Any]:
    conn = _get_connection()
    try:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if keyword and is_fts5_available():
            results = _fts_search(conn, cursor, keyword, date_from, date_to, limit, offset)
        else:
            results = _like_search(cursor, keyword, date_from, date_to, limit, offset)

        if tag:
            results = [d for d in results if tag in d.get("tags", [])]

        total = len(results) if not keyword else _get_query_total(conn, keyword, date_from, date_to)
        return {"results": results, "total": total, "limit": limit, "offset": offset}
    finally:
        conn.close()


def _fts_search(
    conn: sqlite3.Connection,
    cursor: sqlite3.Cursor,
    keyword: str,
    date_from: str | None,
    date_to: str | None,
    limit: int,
    offset: int,
) -> list[dict[str, Any]]:
    conditions: list[str] = []
    params: list[Any] = []
    try:
        fts_query = " OR ".join(keyword.split())
        conditions.append("d.id IN (SELECT id FROM decisions_fts WHERE decisions_fts MATCH ?)")
        params.append(fts_query)
    except sqlite3.OperationalError:
        kw_lower = keyword.lower()
        conditions.append("(LOWER(d.title) LIKE ? OR LOWER(d.context) LIKE ? OR LOWER(d.decision) LIKE ?)")
        like_pattern = f"%{kw_lower}%"
        params.extend([like_pattern, like_pattern, like_pattern])

    if date_from:
        conditions.append("d.created_at >= ?")
        params.append(date_from)
    if date_to:
        conditions.append("d.created_at <= ?")
        params.append(date_to)

    where_clause = " WHERE " + " AND ".join(conditions)
    cursor.execute(
        f"SELECT d.* FROM decisions d{where_clause} ORDER BY d.created_at DESC LIMIT ? OFFSET ?",
        params + [limit, offset],
    )
    return [_row_to_dict(row) for row in cursor.fetchall()]


def _like_search(
    cursor: sqlite3.Cursor,
    keyword: str | None,
    date_from: str | None,
    date_to: str | None,
    limit: int,
    offset: int,
) -> list[dict[str, Any]]:
    conditions: list[str] = []
    params: list[Any] = []
    if keyword:
        kw_lower = keyword.lower()
        like_pattern = f"%{kw_lower}%"
        conditions.append("(LOWER(title) LIKE ? OR LOWER(context) LIKE ? OR LOWER(decision) LIKE ?)")
        params.extend([like_pattern, like_pattern, like_pattern])
    if date_from:
        conditions.append("created_at >= ?")
        params.append(date_from)
    if date_to:
        conditions.append("created_at <= ?")
        params.append(date_to)

    where_clause = (" WHERE " + " AND ".join(conditions)) if conditions else ""
    cursor.execute(
        f"SELECT * FROM decisions{where_clause} ORDER BY created_at DESC LIMIT ? OFFSET ?",
        params + [limit, offset],
    )
    return [_row_to_dict(row) for row in cursor.fetchall()]


def _get_query_total(conn: sqlite3.Connection, keyword: str | None, date_from: str | None, date_to: str | None) -> int:
    cursor = conn.cursor()
    conditions: list[str] = []
    params: list[Any] = []
    if keyword:
        try:
            fts_query = " OR ".join(keyword.split())
            conditions.append("id IN (SELECT id FROM decisions_fts WHERE decisions_fts MATCH ?)")
            params.append(fts_query)
        except sqlite3.OperationalError:
            kw_lower = keyword.lower()
            like_pattern = f"%{kw_lower}%"
            conditions.append("(LOWER(title) LIKE ? OR LOWER(context) LIKE ? OR LOWER(decision) LIKE ?)")
            params.extend([like_pattern, like_pattern, like_pattern])
    if date_from:
        conditions.append("created_at >= ?")
        params.append(date_from)
    if date_to:
        conditions.append("created_at <= ?")
        params.append(date_to)

    where_clause = (" WHERE " + " AND ".join(conditions)) if conditions else ""
    cursor.execute(f"SELECT COUNT(*) FROM decisions{where_clause}", params)
    return cursor.fetchone()[0]


def _update_decision(
    decision_id: str,
    status: str | None = None,
) -> dict[str, Any]:
    valid_statuses = ("proposed", "accepted", "deprecated", "superseded")
    if status and status not in valid_statuses:
        return {"error": True, "message": f"无效状态: {status}，支持: {', '.join(valid_statuses)}"}

    with _db_lock:
        conn = _get_connection()
        try:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM decisions WHERE id = ?", (decision_id,))
            row = cursor.fetchone()
            if not row:
                return {"error": True, "message": f"决策未找到: {decision_id}"}

            now_iso = datetime.now().isoformat()
            if status:
                cursor.execute(
                    "UPDATE decisions SET status = ?, updated_at = ? WHERE id = ?",
                    (status, now_iso, decision_id),
                )
            conn.commit()

            cursor.execute("SELECT * FROM decisions WHERE id = ?", (decision_id,))
            updated_row = cursor.fetchone()
            entry = _row_to_dict(updated_row)
            with _cache_lock:
                _cache[decision_id] = entry
            return {"id": decision_id, "entry": entry, "updated": True}
        finally:
            conn.close()


def _export_decisions(
    export_format: str = "json",
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict[str, Any]:
    conn = _get_connection()
    try:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        conditions: list[str] = []
        params: list[Any] = []
        if date_from:
            conditions.append("created_at >= ?")
            params.append(date_from)
        if date_to:
            conditions.append("created_at <= ?")
            params.append(date_to)
        where_clause = (" WHERE " + " AND ".join(conditions)) if conditions else ""
        cursor.execute(f"SELECT * FROM decisions{where_clause} ORDER BY created_at ASC", params)
        rows = cursor.fetchall()
        decisions = [_row_to_dict(row) for row in rows]
    finally:
        conn.close()

    if export_format == "markdown":
        lines = ["# Architecture Decision Records\n"]
        for d in decisions:
            lines.append(f"## {d.get('id', '')}: {d.get('title', '')}\n")
            lines.append(f"- **Status**: {d.get('status', 'proposed')}")
            lines.append(f"- **Context**: {d.get('context', '')}")
            lines.append(f"- **Decision**: {d.get('decision', '')}")
            lines.append(f"- **Rationale**: {d.get('rationale', '')}")
            alts = d.get("alternatives", [])
            if alts:
                lines.append("- **Alternatives**:")
                for alt in alts:
                    lines.append(f"  - {alt}")
            lines.append(f"- **Created At**: {d.get('created_at', '')}")
            lines.append(f"- **Updated At**: {d.get('updated_at', '')}")
            lines.append("")
        exported = "\n".join(lines)
        return {"format": "markdown", "content": exported, "total": len(decisions)}
    return {"format": "json", "content": decisions, "total": len(decisions)}


def _stats_decisions(
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict[str, Any]:
    conn = _get_connection()
    try:
        cursor = conn.cursor()
        conditions: list[str] = []
        params: list[Any] = []
        if date_from:
            conditions.append("created_at >= ?")
            params.append(date_from)
        if date_to:
            conditions.append("created_at <= ?")
            params.append(date_to)
        where_clause = (" WHERE " + " AND ".join(conditions)) if conditions else ""

        cursor.execute(f"SELECT COUNT(*) FROM decisions{where_clause}", params)
        total = cursor.fetchone()[0]

        cursor.execute(f"SELECT status, COUNT(*) as cnt FROM decisions{where_clause} GROUP BY status", params)
        by_status: dict[str, int] = {}
        for row in cursor.fetchall():
            by_status[row[0]] = row[1]

        cursor.execute(f"SELECT SUBSTR(created_at, 1, 10) as day, COUNT(*) as cnt FROM decisions{where_clause} GROUP BY day ORDER BY day DESC LIMIT 30", params)
        by_date: dict[str, int] = {}
        for row in cursor.fetchall():
            by_date[row[0]] = row[1]

        return {
            "total": total,
            "by_status": by_status,
            "by_date": by_date,
            "date_range": {"from": date_from, "to": date_to},
        }
    finally:
        conn.close()


def _reconcile_decisions() -> dict[str, Any]:
    sqlite_ids: set[str] = set()
    with _db_lock:
        conn = _get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM decisions")
            sqlite_ids = {row[0] for row in cursor.fetchall()}
        finally:
            conn.close()

    file_ids: set[str] = set()
    file_entries: dict[str, dict[str, Any]] = {}
    if DECISIONS_JSON_FILE.exists():
        try:
            data = json.loads(DECISIONS_JSON_FILE.read_text(encoding="utf-8"))
            if isinstance(data, list):
                for entry in data:
                    eid = entry.get("id", "")
                    if eid:
                        file_ids.add(eid)
                        file_entries[eid] = entry
        except (json.JSONDecodeError, OSError):
            pass

    only_in_sqlite = sqlite_ids - file_ids
    only_in_file = file_ids - sqlite_ids
    repaired = 0
    failed = 0

    for entry_id in only_in_sqlite:
        with _db_lock:
            conn = _get_connection()
            try:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM decisions WHERE id = ?", (entry_id,))
                row = cursor.fetchone()
                if row:
                    entry = _row_to_dict(row)
                    try:
                        _write_decision_file(entry)
                        repaired += 1
                    except Exception as exc:
                        logger.warning("Reconcile: failed to write file for %s: %s", entry_id, exc)
                        failed += 1
            finally:
                conn.close()

    for entry_id in only_in_file:
        entry = file_entries.get(entry_id)
        if not entry:
            failed += 1
            continue
        with _db_lock:
            conn = _get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM decisions WHERE id = ?", (entry_id,))
                if cursor.fetchone() is None:
                    alts_json = json.dumps(entry.get("alternatives", []), ensure_ascii=False)
                    cursor.execute(
                        "INSERT OR IGNORE INTO decisions (id, title, context, decision, rationale, alternatives, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (
                            entry_id,
                            entry.get("title", ""),
                            entry.get("context", ""),
                            entry.get("decision", ""),
                            entry.get("rationale", ""),
                            alts_json,
                            entry.get("status", "proposed"),
                            entry.get("created_at", ""),
                            entry.get("updated_at", entry.get("created_at", "")),
                        ),
                    )
                    conn.commit()
                    repaired += 1
            except Exception as exc:
                logger.warning("Reconcile: failed to insert SQLite for %s: %s", entry_id, exc)
                failed += 1
            finally:
                conn.close()

    total_inconsistencies = len(only_in_sqlite) + len(only_in_file)
    return {
        "total_inconsistencies": total_inconsistencies,
        "only_in_sqlite": len(only_in_sqlite),
        "only_in_file": len(only_in_file),
        "repaired": repaired,
        "failed": failed,
        "success_rate": (repaired / total_inconsistencies * 100) if total_inconsistencies > 0 else 100.0,
    }


def register(mcp: FastMCP) -> None:
    @mcp.tool(
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=False,
            openWorldHint=False,
        )
    )
    async def decision_log(
        action: str,
        title: str | None = None,
        description: str | None = None,
        context: str | None = None,
        alternatives: list[str] | None = None,
        decision: str | None = None,
        rationale: str | None = None,
        impact: str | None = None,
        decided_by: str | None = None,
        keyword: str | None = None,
        tag: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        limit: int = 20,
        offset: int = 0,
        export_format: str = "json",
        decision_id: str | None = None,
        status: str | None = None,
    ) -> dict[str, Any]:
        """决策日志管理：记录决策条目、搜索决策、导出决策记录。log操作记录一条决策(含标题/描述/上下文/备选方案/最终决策/理由/影响/决策者)，list操作分页列出决策，query操作按关键词/标签/日期范围搜索决策，update操作更新决策状态，export操作导出决策为JSON或Markdown ADR格式，stats操作返回决策统计信息。"""
        validated, err = validate_input(DecisionLogInput, action=action, title=title, description=description, context=context, alternatives=alternatives, decision=decision, rationale=rationale, impact=impact, decided_by=decided_by, keyword=keyword, tag=tag, date_from=date_from, date_to=date_to, limit=limit, offset=offset, format=export_format, decision_id=decision_id, status=status)
        if err:
            return err
        logger.info("decision_log called: action=%s", action)
        try:
            if action == "log":
                if not title:
                    return make_error_response(ValueError("log操作需要title参数"), error_code=ERR_VALIDATION)
                return make_success_response(_log_decision(title, description, context, alternatives, decision, rationale, impact, decided_by, status))
            elif action == "list":
                return make_success_response(_list_decisions(limit, offset, status, date_from, date_to))
            elif action == "query":
                return make_success_response(_query_decisions(keyword, tag, date_from, date_to, limit, offset))
            elif action == "update":
                if not decision_id:
                    return make_error_response(ValueError("update操作需要decision_id参数"), error_code=ERR_VALIDATION)
                result = _update_decision(decision_id, status)
                if result.get("error"):
                    return make_error_response(ValueError(result["message"]), error_code=ERR_NOT_FOUND)
                return make_success_response(result)
            elif action == "export":
                return make_success_response(_export_decisions(export_format, date_from, date_to))
            elif action == "stats":
                return make_success_response(_stats_decisions(date_from, date_to))
            elif action == "reconcile":
                return make_success_response(_reconcile_decisions())
            else:
                return make_error_response(ValueError(f"未知操作: {action}，支持: log, list, query, update, export, stats, reconcile"), error_code=ERR_VALIDATION)
        except Exception as e:
            logger.error("decision_log error: %s", e)
            return make_error_response(e)
