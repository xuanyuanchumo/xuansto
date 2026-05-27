import hashlib
import json
import logging
import os
import sqlite3
import stat
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from .config import SCHEMA_SQL, SCHEMA_VERSION

logger = logging.getLogger("knowledge-server")


class SQLiteEngine:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: Optional[sqlite3.Connection] = None
        self._write_lock = threading.Lock()
        self._initialize_schema()

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA foreign_keys=ON")
        return self._conn

    def _initialize_schema(self):
        conn = self._get_conn()
        conn.executescript(SCHEMA_SQL)
        cur = conn.execute("SELECT MAX(version) FROM schema_version")
        row = cur.fetchone()
        current_version = row[0] if row[0] is not None else 0
        if current_version < SCHEMA_VERSION:
            if current_version < 9:
                self._migrate_v9(conn)
            if current_version < 10:
                self._migrate_v10(conn)
            if current_version < 11:
                self._migrate_v11(conn)
            if current_version < 12:
                self._migrate_v12(conn)
            conn.execute(
                "INSERT OR IGNORE INTO schema_version (version, applied_at, description) VALUES (?, datetime('now'), ?)",
                (SCHEMA_VERSION, 'Add status, last_accessed fields for lifecycle management'),
            )
        conn.commit()
        try:
            os.chmod(str(self.db_path), stat.S_IRUSR | stat.S_IWUSR)
        except OSError:
            pass

    def _migrate_v9(self, conn):
        try:
            cur = conn.execute("PRAGMA table_info(knowledge_entries)")
            columns = {row[1] for row in cur.fetchall()}
            if "embedding_retry_count" not in columns:
                conn.execute("ALTER TABLE knowledge_entries ADD COLUMN embedding_retry_count INTEGER DEFAULT 0")
            conn.execute("UPDATE knowledge_entries SET embedding_status = 'pending' WHERE embedding_status IS NULL")
        except Exception as e:
            logger.warning("operation=migrate_v9, error=%s", e)

    def _migrate_v10(self, conn):
        try:
            cur = conn.execute("PRAGMA table_info(knowledge_entries)")
            columns = {row[1] for row in cur.fetchall()}
            if "source" not in columns:
                conn.execute("ALTER TABLE knowledge_entries ADD COLUMN source TEXT")
            cur = conn.execute("PRAGMA table_info(schema_version)")
            sv_columns = {row[1] for row in cur.fetchall()}
            if "description" not in sv_columns:
                conn.execute("ALTER TABLE schema_version ADD COLUMN description TEXT")
            conn.execute(
                "CREATE TABLE IF NOT EXISTS usage_logs ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "entry_id TEXT, "
                "agent_role TEXT, "
                "query_text TEXT, "
                "result_count INTEGER DEFAULT 0, "
                "elapsed_ms REAL DEFAULT 0.0, "
                "timestamp TEXT DEFAULT (datetime('now')), "
                "FOREIGN KEY (entry_id) REFERENCES knowledge_entries(id) ON DELETE SET NULL)"
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_usage_entry ON usage_logs(entry_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_usage_agent ON usage_logs(agent_role)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_usage_timestamp ON usage_logs(timestamp)")
        except Exception as e:
            logger.warning("operation=migrate_v10, error=%s", e)

    def _migrate_v11(self, conn):
        try:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS backup_history ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "backup_type TEXT NOT NULL, "
                "destination TEXT, "
                "entry_count INTEGER DEFAULT 0, "
                "size_bytes INTEGER DEFAULT 0, "
                "status TEXT DEFAULT 'completed', "
                "created_at TEXT DEFAULT (datetime('now')))"
            )
        except Exception as e:
            logger.warning("operation=migrate_v11, error=%s", e)

    def _migrate_v12(self, conn):
        try:
            cur = conn.execute("PRAGMA table_info(knowledge_entries)")
            columns = {row[1] for row in cur.fetchall()}
            if "status" not in columns:
                conn.execute("ALTER TABLE knowledge_entries ADD COLUMN status TEXT DEFAULT 'active' CHECK(status IN ('active','archived','deleted'))")
            if "last_accessed" not in columns:
                conn.execute("ALTER TABLE knowledge_entries ADD COLUMN last_accessed TEXT")
            conn.execute("UPDATE knowledge_entries SET status = 'active' WHERE status IS NULL")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_entries_status ON knowledge_entries(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_entries_last_accessed ON knowledge_entries(last_accessed)")
        except Exception as e:
            logger.warning("operation=migrate_v12, error=%s", e)

    def close(self):
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def add_entry(self, entry: dict) -> dict:
        with self._write_lock:
            conn = self._get_conn()
            entry_id = entry.get("id") or f"kb-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:6]}"
            content_hash = self._compute_hash(entry["content"])
            tags_json = json.dumps(entry.get("tags", []), ensure_ascii=False)

            try:
                conn.execute(
                    "INSERT INTO knowledge_entries "
                    "(id, title, content, scope, tags, confidence, source_path, source_rating, occurrences, content_hash, "
                    "type, category, summary, content_path, embedding_status) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')",
                    (
                        entry_id,
                        entry["title"],
                        entry["content"],
                        entry.get("scope", "workspace"),
                        tags_json,
                        entry.get("confidence", 0.6),
                        entry.get("source_path"),
                        entry.get("source_rating", 3),
                        entry.get("occurrences", 1),
                        content_hash,
                        entry.get("type", "unknown"),
                        entry.get("category", "uncategorized"),
                        entry.get("summary"),
                        entry.get("content_path"),
                    ),
                )
                tags = entry.get("tags", [])
                if tags:
                    self.sync_tags(entry_id, tags)
                conn.commit()
            except sqlite3.IntegrityError as e:
                conn.rollback()
                raise ValueError(f"条目ID冲突或约束违反: {e}")

            return {"id": entry_id, "content_hash": content_hash}

    def get_entry(self, entry_id: str) -> Optional[dict]:
        conn = self._get_conn()
        cur = conn.execute("SELECT * FROM knowledge_entries WHERE id = ?", (entry_id,))
        row = cur.fetchone()
        if row is None:
            return None
        return self._row_to_dict(row)

    def batch_get_metadata(self, entry_ids: list[str]) -> dict[str, dict]:
        if not entry_ids:
            return {}
        conn = self._get_conn()
        placeholders = ",".join("?" * len(entry_ids))
        cur = conn.execute(
            f"SELECT id, scope, type, category, embedding_status, status FROM knowledge_entries WHERE id IN ({placeholders})",
            entry_ids,
        )
        result = {}
        for row in cur.fetchall():
            result[row["id"]] = {
                "scope": row["scope"],
                "type": row["type"],
                "category": row["category"],
                "embedding_status": row["embedding_status"],
                "status": row["status"],
            }
        return result

    def update_entry(self, entry_id: str, updates: dict, _skip_version_save: bool = False) -> Optional[dict]:
        with self._write_lock:
            conn = self._get_conn()
            existing = self.get_entry(entry_id)
            if existing is None:
                return None

            if "version" in updates:
                expected_version = updates.pop("version")
                if not self.check_version(entry_id, expected_version):
                    return {"error": "version_conflict", "current_version": existing["version"], "expected_version": expected_version}

            if not _skip_version_save:
                self._save_version(entry_id, existing)

            fields = []
            values = []
            for key in ("title", "content", "scope", "confidence", "source_path", "source_rating",
                         "type", "category", "summary", "content_path", "success_count", "failure_count",
                         "occurrences", "created", "status", "last_accessed"):
                if key in updates:
                    fields.append(f"{key} = ?")
                    values.append(updates[key])

            if "tags" in updates:
                tags_json = json.dumps(updates["tags"], ensure_ascii=False)
                fields.append("tags = ?")
                values.append(tags_json)

            if "content" in updates:
                fields.append("content_hash = ?")
                values.append(self._compute_hash(updates["content"]))

            if not fields:
                return existing

            fields.append("updated = datetime('now')")
            fields.append("version = version + 1")
            values.append(entry_id)

            conn.execute(
                f"UPDATE knowledge_entries SET {', '.join(fields)} WHERE id = ?",
                values,
            )

            if "tags" in updates:
                self.sync_tags(entry_id, updates["tags"])

            conn.commit()
            return self.get_entry(entry_id)

    def delete_entry(self, entry_id: str) -> bool:
        with self._write_lock:
            conn = self._get_conn()
            existing = self.get_entry(entry_id)
            if existing is None:
                return False
            self._save_version(entry_id, existing, change_type="delete")
            conn.execute("DELETE FROM knowledge_entries WHERE id = ?", (entry_id,))
            conn.commit()
            return True

    def _save_version(self, entry_id: str, entry: dict, change_type: str = "update", content_snapshot: Optional[str] = None):
        with self._write_lock:
            conn = self._get_conn()
            cur = conn.execute(
                "SELECT MAX(version) FROM version_history WHERE entry_id = ?",
                (entry_id,),
            )
            row = cur.fetchone()
            next_version = (row[0] or 0) + 1

            conn.execute(
                "INSERT INTO version_history "
                "(entry_id, version, title, content, scope, tags, confidence, source_path, source_rating, content_hash, change_type, content_snapshot) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    entry_id,
                    next_version,
                    entry.get("title"),
                    entry.get("content"),
                    entry.get("scope"),
                    json.dumps(entry.get("tags", []), ensure_ascii=False) if isinstance(entry.get("tags"), list) else entry.get("tags"),
                    entry.get("confidence"),
                    entry.get("source_path"),
                    entry.get("source_rating"),
                    entry.get("content_hash"),
                    change_type,
                    content_snapshot,
                ),
            )
            conn.commit()

    def restore_version(self, entry_id: str, target_version: int) -> Optional[dict]:
        conn = self._get_conn()
        cur = conn.execute(
            "SELECT * FROM version_history WHERE entry_id = ? AND version = ?",
            (entry_id, target_version),
        )
        row = cur.fetchone()
        if row is None:
            return None

        version_data = dict(row)
        current = self.get_entry(entry_id)
        if current:
            self._save_version(entry_id, current)

        tags_raw = version_data.get("tags", "[]")
        if isinstance(tags_raw, str):
            try:
                tags_parsed = json.loads(tags_raw)
            except json.JSONDecodeError:
                tags_parsed = []
        else:
            tags_parsed = tags_raw

        updates = {
            "title": version_data["title"],
            "content": version_data["content"],
            "scope": version_data["scope"],
            "tags": tags_parsed,
            "confidence": version_data["confidence"],
            "source_path": version_data["source_path"],
            "source_rating": version_data["source_rating"],
        }

        result = self.update_entry(entry_id, updates)
        return result

    def get_version_history(self, entry_id: str) -> list[dict]:
        conn = self._get_conn()
        cur = conn.execute(
            "SELECT entry_id, version, title, scope, confidence, content_hash, saved_at "
            "FROM version_history WHERE entry_id = ? ORDER BY version DESC",
            (entry_id,),
        )
        return [dict(row) for row in cur.fetchall()]

    def search_fts(self, query: str, scope: Optional[str] = None, top_k: int = 20, type_filters: Optional[list[str]] = None, category_filters: Optional[list[str]] = None) -> list[dict]:
        conn = self._get_conn()
        escaped = query.replace('"', '""')

        conditions = ["knowledge_fts MATCH ?"]
        params: list[Any] = [escaped]

        conditions.append("(ke.status IS NULL OR ke.status != 'archived')")

        if scope:
            conditions.append("ke.scope = ?")
            params.append(scope)

        if type_filters:
            placeholders = ",".join("?" * len(type_filters))
            conditions.append(f"ke.type IN ({placeholders})")
            params.extend(type_filters)

        if category_filters:
            placeholders = ",".join("?" * len(category_filters))
            conditions.append(f"ke.category IN ({placeholders})")
            params.extend(category_filters)

        where_clause = " AND ".join(conditions)
        sql = (
            f"SELECT ke.*, bm25(knowledge_fts) AS rank "
            f"FROM knowledge_fts fts "
            f"JOIN knowledge_entries ke ON ke.rowid = fts.rowid "
            f"WHERE {where_clause} "
            f"ORDER BY rank LIMIT ?"
        )
        params.append(top_k)
        cur = conn.execute(sql, params)

        results = []
        for row in cur.fetchall():
            d = self._row_to_dict(row)
            d["_bm25_score"] = row["rank"]
            results.append(d)
        return results

    def find_by_hash(self, content_hash: str) -> Optional[dict]:
        conn = self._get_conn()
        cur = conn.execute(
            "SELECT * FROM knowledge_entries WHERE content_hash = ? LIMIT 1",
            (content_hash,),
        )
        row = cur.fetchone()
        return self._row_to_dict(row) if row else None

    def count_entries(self) -> dict:
        conn = self._get_conn()
        cur = conn.execute(
            "SELECT scope, COUNT(*) as cnt FROM knowledge_entries GROUP BY scope"
        )
        counts = {"total": 0, "general": 0, "workspace": 0, "experience": 0}
        for row in cur.fetchall():
            counts[row["scope"]] = row["cnt"]
            counts["total"] += row["cnt"]
        return counts

    def is_empty(self) -> bool:
        conn = self._get_conn()
        cur = conn.execute("SELECT COUNT(*) FROM knowledge_entries")
        return cur.fetchone()[0] == 0

    def get_all_entries(self) -> list[dict]:
        conn = self._get_conn()
        cur = conn.execute("SELECT * FROM knowledge_entries ORDER BY id")
        return [self._row_to_dict(row) for row in cur.fetchall()]

    @staticmethod
    def _compute_hash(content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()[:32]

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict:
        d = dict(row)
        if "tags" in d and isinstance(d["tags"], str):
            try:
                d["tags"] = json.loads(d["tags"])
            except json.JSONDecodeError:
                d["tags"] = []
        if "_bm25_score" in d:
            pass
        if "created_at" in d and "created" not in d:
            d["created"] = d.pop("created_at")
        if "updated_at" in d and "updated" not in d:
            d["updated"] = d.pop("updated_at")
        return d

    def sync_tags(self, entry_id: str, tags: list):
        with self._write_lock:
            conn = self._get_conn()
            conn.execute("DELETE FROM knowledge_tags WHERE entry_id = ?", (entry_id,))
            normalized = list(set(tag.lower().strip() for tag in tags if tag and tag.strip()))
            for tag in normalized:
                conn.execute(
                    "INSERT OR IGNORE INTO knowledge_tags (entry_id, tag) VALUES (?, ?)",
                    (entry_id, tag),
                )

    def log_dedup(self, new_entry_id: str, existing_entry_id: str, similarity_score: float, action: str):
        with self._write_lock:
            conn = self._get_conn()
            conn.execute(
                "INSERT INTO dedup_log (new_entry_id, existing_entry_id, similarity_score, action, merged_at) "
                "VALUES (?, ?, ?, ?, datetime('now'))",
                (new_entry_id, existing_entry_id, similarity_score, action),
            )
            conn.commit()

    def get_entries_by_tag(self, tag: str) -> list[dict]:
        conn = self._get_conn()
        normalized = tag.lower().strip()
        cur = conn.execute(
            "SELECT ke.* FROM knowledge_entries ke "
            "JOIN knowledge_tags kt ON ke.id = kt.entry_id "
            "WHERE kt.tag = ? ORDER BY ke.updated DESC",
            (normalized,),
        )
        return [self._row_to_dict(row) for row in cur.fetchall()]

    def check_version(self, entry_id: str, expected_version: int) -> bool:
        conn = self._get_conn()
        cur = conn.execute(
            "SELECT version FROM knowledge_entries WHERE id = ?",
            (entry_id,),
        )
        row = cur.fetchone()
        if row is None:
            return False
        return row["version"] == expected_version

    def count_by_embedding_status(self) -> dict:
        conn = self._get_conn()
        cur = conn.execute(
            "SELECT embedding_status, COUNT(*) as cnt FROM knowledge_entries GROUP BY embedding_status"
        )
        result = {}
        for row in cur.fetchall():
            result[row["embedding_status"]] = row["cnt"]
        return result

    def update_embedding_status(self, entry_id: str, status: str):
        with self._write_lock:
            conn = self._get_conn()
            conn.execute(
                "UPDATE knowledge_entries SET embedding_status = ? WHERE id = ?",
                (status, entry_id),
            )
            conn.commit()

    def get_pending_embeddings(self, limit: int = 50) -> list[dict]:
        conn = self._get_conn()
        cur = conn.execute(
            "SELECT id, content, title, scope FROM knowledge_entries "
            "WHERE embedding_status = 'pending' AND embedding_retry_count < 5 "
            "ORDER BY updated ASC LIMIT ?",
            (limit,),
        )
        return [dict(row) for row in cur.fetchall()]

    def increment_retry_count(self, entry_id: str):
        with self._write_lock:
            conn = self._get_conn()
            conn.execute(
                "UPDATE knowledge_entries SET embedding_retry_count = embedding_retry_count + 1 WHERE id = ?",
                (entry_id,),
            )
            conn.commit()

    def get_ready_entry_ids(self) -> set:
        conn = self._get_conn()
        cur = conn.execute(
            "SELECT id FROM knowledge_entries WHERE embedding_status = 'ready'"
        )
        return {row["id"] for row in cur.fetchall()}

    def log_reconciliation(self, sqlite_ready_count: int, chroma_vector_count: int,
                           missing_in_chroma: int, orphan_in_chroma: int,
                           fixed_count: int, details: str = ""):
        with self._write_lock:
            conn = self._get_conn()
            conn.execute(
                "INSERT INTO reconciliation_log "
                "(check_time, sqlite_ready_count, chroma_vector_count, missing_in_chroma, orphan_in_chroma, fixed_count, details) "
                "VALUES (datetime('now'), ?, ?, ?, ?, ?, ?)",
                (sqlite_ready_count, chroma_vector_count, missing_in_chroma, orphan_in_chroma, fixed_count, details),
            )
            conn.commit()
