from __future__ import annotations

import math
import sqlite3
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from ..core.config import (
    KNOWLEDGE_CHROMA_PATH,
    KNOWLEDGE_DB_PATH,
    KNOWLEDGE_EXPERIENCE_DIR,
    KNOWLEDGE_GENERAL_DIR,
    KNOWLEDGE_WORKSPACE_DIR,
    REFERENCES_DIR,
)
from ..core.errors import ERR_VALIDATION, make_error_response, make_success_response
from ..core.logging_config import get_logger
from ..core.search_engine import get_search_engine
from ..core.validator import validate_input
from ..models.schemas import KnowledgeSearchInput

logger = get_logger("knowledge_search")

_knowledge_index_initialized_paths: set[str] = set()


_MAX_KEYWORD_FILE_BYTES = 1 * 1024 * 1024

_MCP_STANDARD_COLUMNS = {"id", "title", "content", "type", "metadata_json", "created_at", "updated_at"}

_MCP_COLUMN_DEFAULTS: dict[str, str] = {
    "type": "'general'",
    "metadata_json": "'{}'",
}


def _get_db_connection(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


def _migrate_fts5_to_unicode61(conn) -> None:
    cursor = conn.cursor()
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='knowledge_fts'")
    row = cursor.fetchone()

    if row is not None:
        create_sql = row[0] or ""
        if "unicode61" in create_sql:
            return
        logger.warning("Migrating FTS5 table to unicode61 tokenizer")
        for trigger_name in ('knowledge_ai', 'knowledge_ad', 'knowledge_au'):
            conn.execute(f"DROP TRIGGER IF EXISTS {trigger_name}")
        conn.execute("DROP TABLE IF EXISTS knowledge_fts")

    conn.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts
        USING fts5(content, title, type, content=knowledge_entries, content_rowid=rowid, tokenize='unicode61')
    """)
    conn.execute("""
        CREATE TRIGGER IF NOT EXISTS knowledge_ai AFTER INSERT ON knowledge_entries BEGIN
            INSERT INTO knowledge_fts(rowid, content, title, type) VALUES (new.rowid, new.content, new.title, new.type);
        END
    """)
    conn.execute("""
        CREATE TRIGGER IF NOT EXISTS knowledge_ad AFTER DELETE ON knowledge_entries BEGIN
            INSERT INTO knowledge_fts(knowledge_fts, rowid, content, title, type) VALUES('delete', old.rowid, old.content, old.title, old.type);
        END
    """)
    conn.execute("""
        CREATE TRIGGER IF NOT EXISTS knowledge_au AFTER UPDATE ON knowledge_entries BEGIN
            INSERT INTO knowledge_fts(knowledge_fts, rowid, content, title, type) VALUES('delete', old.rowid, old.content, old.title, old.type);
            INSERT INTO knowledge_fts(rowid, content, title, type) VALUES (new.rowid, new.content, new.title, new.type);
        END
    """)
    conn.execute("INSERT INTO knowledge_fts(knowledge_fts) VALUES('rebuild')")
    conn.commit()
    if row is not None:
        logger.info("FTS5 migration to unicode61 complete, index rebuilt")
    else:
        logger.info("Created FTS5 index with unicode61 tokenizer")


def _ensure_knowledge_index() -> None:
    global _knowledge_index_initialized_paths
    from ..core.config import KNOWLEDGE_DIR
    _db_key = str(KNOWLEDGE_DIR.resolve())
    if _db_key in _knowledge_index_initialized_paths:
        return
    index_dir = KNOWLEDGE_DIR / "index"
    index_dir.mkdir(parents=True, exist_ok=True)

    db_path = index_dir / "knowledge.db"
    conn = _get_db_connection(db_path)
    try:
        need_create = not db_path.exists() or db_path.stat().st_size == 0

        if not need_create:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='knowledge_entries'")
                if cursor.fetchone() is None:
                    need_create = True
                else:
                    cursor.execute("PRAGMA table_info(knowledge_entries)")
                    existing_cols = {row[1] for row in cursor.fetchall()}
                    missing = _MCP_STANDARD_COLUMNS - existing_cols
                    if missing:
                        for col in sorted(missing):
                            default = _MCP_COLUMN_DEFAULTS.get(col, "NULL")
                            logger.warning(
                                "Schema migration: adding missing column '%s' with default %s",
                                col, default,
                            )
                            col_type = "TEXT"
                            if col == "id":
                                col_type = "TEXT PRIMARY KEY"
                            elif col in ("title", "content"):
                                col_type = "TEXT NOT NULL"
                            conn.execute(
                                f"ALTER TABLE knowledge_entries ADD COLUMN {col} {col_type} DEFAULT {default}"
                            )
                        conn.commit()
                        logger.info("Schema migration complete: added %d missing columns", len(missing))
            except Exception as exc:
                logger.warning("Schema migration failed, will create table: %s", exc)
                need_create = True

        if need_create:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_entries (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    type TEXT NOT NULL DEFAULT 'general',
                    metadata_json TEXT DEFAULT '{}',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            conn.commit()

        _migrate_fts5_to_unicode61(conn)
    finally:
        conn.close()

    try:
        import chromadb
        client = chromadb.PersistentClient(path=str(KNOWLEDGE_CHROMA_PATH))
        client.get_or_create_collection("knowledge")
    except ImportError:
        pass
    except Exception:
        pass

    _knowledge_index_initialized_paths.add(_db_key)


def _chromadb_search(query: str, top_k: int, scope: str | None, min_confidence: float) -> dict[str, Any] | None:
    from ..tools.server_health import _CHROMADB_DEGRADATION_KEY, _DEGRADATION_COUNTS, _metrics_lock
    with _metrics_lock:
        _degradation_count = _DEGRADATION_COUNTS.get(_CHROMADB_DEGRADATION_KEY, 0)
    if _degradation_count > 0:
        logger.info("ChromaDB degraded (count=%d), skipping semantic search", _degradation_count)
        return None
    try:
        import chromadb
        client = chromadb.PersistentClient(path=str(KNOWLEDGE_CHROMA_PATH))
        collection = client.get_or_create_collection("knowledge")
        results = collection.query(query_texts=[query], n_results=top_k)
        if not results["ids"] or not results["ids"][0]:
            return None
        items = []
        for i, doc_id in enumerate(results["ids"][0]):
            distance = results["distances"][0][i] if results["distances"] else 0
            relevance = max(0, 1 - distance)
            if relevance < min_confidence:
                continue
            items.append({
                "source": doc_id,
                "content": results["documents"][0][i] if results["documents"] else "",
                "match_type": "semantic",
                "relevance": round(relevance, 3),
            })
        return {"results": items, "total": len(items), "strategy": "chromadb_semantic"}
    except Exception:
        return None


def _sqlite_search(query: str, top_k: int, scope: str | None, min_confidence: float) -> dict[str, Any] | None:
    if not KNOWLEDGE_DB_PATH.exists():
        return None
    try:
        conn = _get_db_connection(KNOWLEDGE_DB_PATH)
        try:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "SELECT ke.id, ke.content, bm25(knowledge_fts) as bm25_score "
                    "FROM knowledge_entries ke "
                    "JOIN knowledge_fts ON ke.rowid = knowledge_fts.rowid "
                    "WHERE knowledge_fts MATCH ? ORDER BY bm25_score LIMIT ?",
                    (query, top_k),
                )
                rows = cursor.fetchall()
                if not rows:
                    cursor.execute(
                        "SELECT id, content FROM knowledge_entries WHERE content LIKE ? OR title LIKE ? LIMIT ?",
                        (f"%{query}%", f"%{query}%", top_k),
                    )
                    rows = cursor.fetchall()
            except sqlite3.OperationalError:
                cursor.execute(
                    "SELECT id, content FROM knowledge_entries WHERE content LIKE ? OR title LIKE ? LIMIT ?",
                    (f"%{query}%", f"%{query}%", top_k),
                )
                rows = cursor.fetchall()
            items = []
            for row in rows:
                if "bm25_score" in row:
                    raw_score = row["bm25_score"]
                    neg_score = -raw_score
                    relevance = min(1.0, max(0.0, neg_score / 20.0 + 0.5))
                else:
                    relevance = 0.3
                relevance = round(relevance, 4)
                if relevance < min_confidence:
                    continue
                items.append({
                    "source": row["id"] if "id" in row else str(row[0]),
                    "content": row["content"] if "content" in row else str(row[1]),
                    "match_type": "fts5",
                    "relevance": relevance,
                })
            return {"results": items, "total": len(items), "strategy": "sqlite_fts5_bm25"}
        finally:
            conn.close()
    except Exception:
        return None


def _keyword_fallback_search(query: str, top_k: int, scope: str | None) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    search_dirs = []
    if scope in (None, "general"):
        search_dirs.extend([KNOWLEDGE_GENERAL_DIR, REFERENCES_DIR])
    if scope in (None, "workspace"):
        search_dirs.append(KNOWLEDGE_WORKSPACE_DIR)
    if scope in (None, "experience"):
        search_dirs.append(KNOWLEDGE_EXPERIENCE_DIR)
    query_terms = set(query.lower().split())
    total_query_terms = len(query_terms)
    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
        for f in search_dir.rglob("*.md"):
            try:
                if f.stat().st_size > _MAX_KEYWORD_FILE_BYTES:
                    continue
                content = f.read_text(encoding="utf-8")
                content_lower = content.lower()
                if query.lower() in content_lower:
                    matched_terms = sum(1 for term in query_terms if term in content_lower)
                    content_length = len(content)
                    length_factor = 1.0 / (1.0 + max(0.0, math.log(max(content_length, 1) / 1000)))
                    relevance = min(1.0, max(0.0, matched_terms / total_query_terms * length_factor)) if total_query_terms > 0 else 0.0
                    relevance = round(relevance, 4)
                    snippet_start = max(0, content_lower.index(query.lower()) - 100)
                    snippet_end = min(len(content), content_lower.index(query.lower()) + len(query) + 100)
                    snippet = content[snippet_start:snippet_end]
                    results.append({
                        "source": str(f.relative_to(search_dir)),
                        "content": snippet,
                        "match_type": "keyword",
                        "relevance": relevance,
                    })
                    if len(results) >= top_k:
                        break
            except (OSError, UnicodeDecodeError):
                continue
        if len(results) >= top_k:
            break
    return {"results": results, "total": len(results), "strategy": "keyword_tfidf"}


_MAX_CHROMA_RETRY_ATTEMPTS = 3


async def _retry_pending_chroma() -> dict[str, Any]:
    from ..core.database import load_state, persist_state
    pending_entries = load_state("knowledge_entries", {"sync_status": "pending"})
    if not pending_entries:
        return {"retried": 0, "succeeded": 0, "failed": 0}

    retried = 0
    succeeded = 0
    failed = 0

    for entry in pending_entries:
        entry_id = entry.get("id", "")
        if not entry_id:
            continue
        retried += 1
        retry_count = 0
        chroma_ok = False

        while retry_count < _MAX_CHROMA_RETRY_ATTEMPTS and not chroma_ok:
            retry_count += 1
            try:
                import chromadb
                client = chromadb.PersistentClient(path=str(KNOWLEDGE_CHROMA_PATH))
                collection = client.get_or_create_collection("knowledge")
                content = entry.get("content", "")
                title = entry.get("title", "")
                metadata = {"title": title, "type": entry.get("scope", "general")}
                collection.upsert(
                    ids=[entry_id],
                    documents=[content],
                    metadatas=[metadata],
                )
                chroma_ok = True
            except ImportError:
                logger.warning("ChromaDB not available during retry for %s", entry_id)
                break
            except Exception as exc:
                logger.debug("ChromaDB retry %d/%d for %s failed: %s", retry_count, _MAX_CHROMA_RETRY_ATTEMPTS, entry_id, exc)

        if chroma_ok:
            succeeded += 1
            try:
                entry["sync_status"] = "ready"
                persist_state("knowledge_entries", entry)
            except Exception:
                logger.debug("Failed to update sync_status to ready for %s", entry_id)
        else:
            failed += 1
            logger.warning(
                "ChromaDB write failed after %d retries for entry %s, marking as failed",
                _MAX_CHROMA_RETRY_ATTEMPTS, entry_id,
            )
            try:
                entry["sync_status"] = "failed"
                persist_state("knowledge_entries", entry)
            except Exception:
                logger.debug("Failed to update sync_status to failed for %s", entry_id)

    return {"retried": retried, "succeeded": succeeded, "failed": failed}


def _reconcile_chroma_sqlite() -> dict[str, Any]:
    from ..core.database import load_state
    all_entries = load_state("knowledge_entries")
    if not all_entries:
        return {"total": 0, "in_sync": 0, "pending": 0, "failed": 0, "missing_in_chroma": 0}

    chroma_ids: set[str] = set()
    try:
        import chromadb
        client = chromadb.PersistentClient(path=str(KNOWLEDGE_CHROMA_PATH))
        collection = client.get_or_create_collection("knowledge")
        chroma_results = collection.get(include=[])
        chroma_ids = set(chroma_results.get("ids", []))
    except ImportError:
        logger.warning("ChromaDB not available for reconciliation")
    except Exception as exc:
        logger.warning("Failed to read ChromaDB during reconciliation: %s", exc)

    in_sync = 0
    pending = 0
    failed = 0
    missing_in_chroma = 0

    for entry in all_entries:
        entry_id = entry.get("id", "")
        sync_status = entry.get("sync_status", "ready")
        if sync_status == "ready":
            in_sync += 1
        elif sync_status == "pending":
            pending += 1
            if entry_id not in chroma_ids:
                missing_in_chroma += 1
        elif sync_status == "failed":
            failed += 1
            if entry_id not in chroma_ids:
                missing_in_chroma += 1

    return {
        "total": len(all_entries),
        "in_sync": in_sync,
        "pending": pending,
        "failed": failed,
        "missing_in_chroma": missing_in_chroma,
    }


def register(mcp: FastMCP) -> None:
    @mcp.tool(
        annotations=ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        )
    )
    async def knowledge_search(
        action: str,
        query: str | None = None,
        top_k: int = 5,
        search_type: str = "hybrid",
        scope: str | None = None,
        min_confidence: float = 0.0,
        keep_last_n: int = 10,
    ) -> dict[str, Any]:
        """三层知识库（通用/工作区/经验）混合检索引擎。支持语义搜索(ChromaDB)、关键词搜索(SQLite FTS5)和混合模式，自动降级。仅支持retrieve和cleanup_versions操作，写入操作请使用knowledge_inject工具。"""
        if action in ("inject", "precipitate"):
            return make_error_response(
                ValueError(
                    f"action='{action}' is not supported by knowledge_search. "
                    f"Use the knowledge_inject tool for write operations (inject, precipitate, add, update)."
                ),
                error_code=ERR_VALIDATION,
            )
        validated, err = validate_input(
            KnowledgeSearchInput,
            action=action,
            query=query,
            top_k=top_k,
            search_type=search_type,
            scope=scope,
            min_confidence=min_confidence,
            keep_last_n=keep_last_n,
        )
        if err:
            return err
        logger.info("knowledge_search called: action=%s query=%s", action, query)
        try:
            if action == "cleanup_versions":
                from ..core.database import cleanup_knowledge_versions
                result = cleanup_knowledge_versions(keep_last_n=keep_last_n, keep_marked=True)
                return make_success_response(result)

            if not query:
                return make_error_response(ValueError("retrieve action requires query parameter"), error_code=ERR_VALIDATION)
            _ensure_knowledge_index()

            if search_type in ("hybrid", "semantic_only"):
                chroma_engine = get_search_engine("chromadb")
                chroma_results = chroma_engine.search(query, top_k, {"scope": scope, "min_confidence": min_confidence})
                if chroma_results:
                    items = [{"source": r.source, "content": r.content, "match_type": r.match_type, "relevance": r.relevance} for r in chroma_results]
                    return make_success_response(data={"results": items, "total": len(items), "strategy": "chromadb_semantic"}, degradation_level="chromadb")

            if search_type in ("hybrid", "keyword_only") or (search_type == "semantic_only" and not chroma_results):
                sqlite_engine = get_search_engine("sqlite_fts5")
                sqlite_results = sqlite_engine.search(query, top_k, {"scope": scope, "min_confidence": min_confidence})
                if sqlite_results:
                    items = [{"source": r.source, "content": r.content, "match_type": r.match_type, "relevance": r.relevance} for r in sqlite_results]
                    return make_success_response(data={"results": items, "total": len(items), "strategy": "sqlite_fts5_bm25"}, degradation_level="sqlite_fts5")

            simple_engine = get_search_engine("simple")
            simple_results = simple_engine.search(query, top_k, {"scope": scope})
            items = [{"source": r.source, "content": r.content, "match_type": r.match_type, "relevance": r.relevance} for r in simple_results]
            return make_success_response(data={"results": items, "total": len(items), "strategy": "keyword_tfidf"}, degradation_level="keyword_fallback")
        except Exception as e:
            logger.error("knowledge_search error: %s", e)
            return make_error_response(e)
