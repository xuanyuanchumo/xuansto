from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from ..core import atomic_write
from ..core.config import (
    SKILL_ROOT,
    KNOWLEDGE_DB_PATH,
    KNOWLEDGE_CHROMA_PATH,
    KNOWLEDGE_GENERAL_DIR,
    KNOWLEDGE_WORKSPACE_DIR,
    KNOWLEDGE_EXPERIENCE_DIR,
    WORK_DIR,
    PATTERNS_DIR,
    REFERENCES_DIR,
)
from ..core.errors import make_error_response, make_success_response, ERR_VALIDATION
from ..core.logging_config import get_logger
from ..core.search_engine import (
    SearchResult,
    get_search_engine,
    ChromaDBSearchEngine,
    SimpleSearchEngine,
    SQLiteFTSSearchEngine,
)
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
    from ..tools.server_health import _DEGRADATION_COUNTS, _CHROMADB_DEGRADATION_KEY, _metrics_lock
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
                if "bm25_score" in row.keys():
                    raw_score = row["bm25_score"]
                    neg_score = -raw_score
                    relevance = min(1.0, max(0.0, neg_score / 20.0 + 0.5))
                else:
                    relevance = 0.3
                relevance = round(relevance, 4)
                if relevance < min_confidence:
                    continue
                items.append({
                    "source": row["id"] if "id" in row.keys() else str(row[0]),
                    "content": row["content"] if "content" in row.keys() else str(row[1]),
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


def _inject_knowledge(content: str, knowledge_type: str, metadata: dict[str, Any] | None) -> dict[str, Any]:
    type_dir_map = {
        "general": KNOWLEDGE_GENERAL_DIR,
        "workspace": KNOWLEDGE_WORKSPACE_DIR,
        "experience": KNOWLEDGE_EXPERIENCE_DIR,
    }
    target_dir = type_dir_map.get(knowledge_type, KNOWLEDGE_GENERAL_DIR)
    target_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    filename = f"injected-{timestamp}.md"
    filepath = target_dir / filename

    meta_str = json.dumps(metadata or {}, ensure_ascii=False)
    frontmatter = (
        f"---\n"
        f"type: injected\n"
        f"knowledge_type: {knowledge_type}\n"
        f"injected_at: {timestamp}\n"
        f"metadata: {meta_str}\n"
        f"---\n"
        f"{content}\n"
    )
    atomic_write(filepath, frontmatter)

    indexed = False
    try:
        conn = _get_db_connection(KNOWLEDGE_DB_PATH)
        try:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(knowledge_entries)")
            existing_cols = {row[1] for row in cursor.fetchall()}
            inject_cols = _MCP_STANDARD_COLUMNS & existing_cols
            if not inject_cols.issuperset({"id", "title", "content"}):
                logger.warning(
                    "Cannot inject: table missing required columns (has %s, need id/title/content)",
                    existing_cols,
                )
            else:
                now = datetime.now(timezone.utc).isoformat()
                col_values_map: dict[str, str] = {
                    "id": filename,
                    "title": filename,
                    "content": content,
                    "type": knowledge_type,
                    "metadata_json": meta_str,
                    "created_at": now,
                    "updated_at": now,
                }
                ordered_cols = sorted(_MCP_STANDARD_COLUMNS & existing_cols)
                values = [col_values_map[c] for c in ordered_cols]
                col_list = ", ".join(ordered_cols)
                placeholders = ", ".join("?" for _ in ordered_cols)
                cursor.execute(
                    f"INSERT INTO knowledge_entries ({col_list}) VALUES ({placeholders})",
                    values,
                )
                conn.commit()
                indexed = True
        finally:
            conn.close()
    except Exception as exc:
        logger.warning("Failed to index injected knowledge: %s", exc)

    chroma_indexed = False
    if indexed:
        try:
            import chromadb
            client = chromadb.PersistentClient(path=str(KNOWLEDGE_CHROMA_PATH))
            collection = client.get_or_create_collection("knowledge")
            collection.upsert(
                ids=[filename],
                documents=[content],
                metadatas=[{"title": filename, "type": knowledge_type, "source": "mcp_inject"}],
            )
            chroma_indexed = True
        except ImportError:
            logger.warning("ChromaDB not available, skipping vector index for injected knowledge")
        except Exception as exc:
            logger.warning("Failed to index injected knowledge in ChromaDB: %s", exc)

    return {
        "injected_id": filename,
        "path": str(filepath),
        "knowledge_type": knowledge_type,
        "indexed": indexed,
        "chroma_indexed": chroma_indexed,
    }


def _precipitate_experience(pattern_ids: list[str]) -> dict[str, Any]:
    patterns_dir = PATTERNS_DIR
    loaded_patterns: list[dict[str, Any]] = []
    not_found: list[str] = []

    for pid in pattern_ids:
        pattern_file = patterns_dir / f"{pid}.json"
        if pattern_file.exists():
            try:
                data = json.loads(pattern_file.read_text(encoding="utf-8"))
                loaded_patterns.append(data)
            except Exception:
                not_found.append(pid)
        else:
            not_found.append(pid)

    error_type_counts: dict[str, int] = {}
    for pattern in loaded_patterns:
        error_type = pattern.get("error_type", pattern.get("type", "unknown"))
        error_type_counts[error_type] = error_type_counts.get(error_type, 0) + 1

    themes: list[str] = []
    for etype, count in sorted(error_type_counts.items(), key=lambda x: -x[1]):
        themes.append(f"- {etype}: 出现 {count} 次")

    recommendations: list[str] = []
    if error_type_counts:
        top_error = max(error_type_counts, key=lambda k: error_type_counts[k])
        recommendations.append(f"- 重点关注 {top_error} 类问题，出现频率最高")
        recommendations.append("- 建议针对高频错误类型编写防御性代码和自动化测试")
    if not_found:
        recommendations.append(f"- {len(not_found)} 个模式文件未找到，建议补充模式数据")

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    source_list = "\n".join(f"- {pid}" for pid in pattern_ids)
    themes_section = "\n".join(themes) if themes else "- 无共性模式"
    recommendations_section = "\n".join(recommendations) if recommendations else "- 暂无建议"

    doc = (
        f"# 经验沉淀 - {timestamp}\n"
        f"\n"
        f"## 模式来源\n"
        f"{source_list}\n"
        f"\n"
        f"## 共性分析\n"
        f"{themes_section}\n"
        f"\n"
        f"## 建议\n"
        f"{recommendations_section}\n"
    )

    KNOWLEDGE_EXPERIENCE_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"precipitated-{timestamp}.md"
    filepath = KNOWLEDGE_EXPERIENCE_DIR / filename
    atomic_write(filepath, doc)

    return {
        "precipitated_id": filename,
        "path": str(filepath),
        "patterns_analyzed": len(loaded_patterns),
        "themes_found": len(themes),
    }


def register(mcp: FastMCP) -> None:
    @mcp.tool(
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=False,
            openWorldHint=True,
        )
    )
    async def knowledge_search(
        action: str = "retrieve",
        query: str | None = None,
        top_k: int = 5,
        search_type: str = "hybrid",
        scope: str | None = None,
        min_confidence: float = 0.0,
        content: str | None = None,
        knowledge_type: str = "general",
        metadata: dict[str, Any] | None = None,
        pattern_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        """三层知识库（通用/工作区/经验）混合检索引擎。支持语义搜索(ChromaDB)、关键词搜索(SQLite FTS5)和混合模式，自动降级。同时支持inject注入知识和precipitate经验沉淀。"""
        validated, err = validate_input(
            KnowledgeSearchInput,
            action=action,
            query=query,
            top_k=top_k,
            search_type=search_type,
            scope=scope,
            min_confidence=min_confidence,
            content=content,
            knowledge_type=knowledge_type,
            metadata=metadata,
            pattern_ids=pattern_ids,
        )
        if err:
            return err
        logger.info("knowledge_search called: action=%s query=%s", action, query)
        try:
            if action == "inject":
                _ensure_knowledge_index()
                if not content:
                    return make_error_response(ValueError("inject action requires content parameter"), error_code=ERR_VALIDATION)
                result = _inject_knowledge(content, knowledge_type, metadata)
                return make_success_response(data=result)

            if action == "precipitate":
                _ensure_knowledge_index()
                if not pattern_ids:
                    return make_error_response(ValueError("precipitate action requires pattern_ids parameter"), error_code=ERR_VALIDATION)
                result = _precipitate_experience(pattern_ids)
                return make_success_response(data=result)

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
