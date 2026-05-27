from __future__ import annotations

import math
import sqlite3
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from .config import (
    KNOWLEDGE_CHROMA_PATH,
    KNOWLEDGE_DB_PATH,
    KNOWLEDGE_EXPERIENCE_DIR,
    KNOWLEDGE_GENERAL_DIR,
    KNOWLEDGE_REFERENCES_DIR,
    KNOWLEDGE_WORKSPACE_DIR,
)
from .logging_config import get_logger

logger = get_logger("search_engine")

_CHROMADB_AVAILABLE: bool | None = None


def _is_chromadb_available() -> bool:
    global _CHROMADB_AVAILABLE
    if _CHROMADB_AVAILABLE is not None:
        return _CHROMADB_AVAILABLE
    try:
        import chromadb
        _CHROMADB_AVAILABLE = True
        return True
    except ImportError:
        _CHROMADB_AVAILABLE = False
        logger.info("ChromaDB not installed, using SQLite FTS5 + BM25 as default search backend")
        return False


@dataclass
class SearchResult:
    source: str
    content: str
    match_type: str
    relevance: float
    metadata: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class SearchEngine(Protocol):
    def search(
        self,
        query: str,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[SearchResult]: ...


class ChromaDBSearchEngine:
    _COLLECTION_NAME = "knowledge"

    def __init__(self, chroma_path: Path | None = None) -> None:
        self._chroma_path = chroma_path or KNOWLEDGE_CHROMA_PATH
        self._client: Any = None

    def _get_client(self) -> Any:
        if self._client is None:
            import chromadb
            self._client = chromadb.PersistentClient(path=str(self._chroma_path))
        return self._client

    def search(
        self,
        query: str,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        min_confidence = (filters or {}).get("min_confidence", 0.0)
        try:
            client = self._get_client()
            collection = client.get_or_create_collection(self._COLLECTION_NAME)
            chroma_where = None
            if filters and "embedding_tier" in filters:
                chroma_where = {"embedding_tier": filters["embedding_tier"]}
            query_kwargs: dict[str, Any] = {"query_texts": [query], "n_results": top_k}
            if chroma_where is not None:
                query_kwargs["where"] = chroma_where
            results = collection.query(**query_kwargs)
            if not results["ids"] or not results["ids"][0]:
                return []
            items: list[SearchResult] = []
            for i, doc_id in enumerate(results["ids"][0]):
                distance = results["distances"][0][i] if results["distances"] else 0
                relevance = max(0, 1 - distance)
                if relevance < min_confidence:
                    continue
                metadata = {}
                if results.get("metadatas") and results["metadatas"][0]:
                    meta = results["metadatas"][0][i]
                    if isinstance(meta, dict):
                        metadata = meta
                items.append(SearchResult(
                    source=doc_id,
                    content=results["documents"][0][i] if results["documents"] else "",
                    match_type="semantic",
                    relevance=round(relevance, 3),
                    metadata=metadata,
                ))
            return items
        except ImportError:
            logger.warning("ChromaDB not available for search")
            return []
        except Exception as exc:
            logger.warning("ChromaDB search failed: %s", exc)
            return []


class SimpleSearchEngine:
    _MAX_FILE_BYTES = 1 * 1024 * 1024

    def __init__(self, search_dirs: list[Path] | None = None) -> None:
        self._search_dirs = search_dirs or [
            KNOWLEDGE_GENERAL_DIR,
            KNOWLEDGE_WORKSPACE_DIR,
            KNOWLEDGE_EXPERIENCE_DIR,
            KNOWLEDGE_REFERENCES_DIR,
        ]

    @staticmethod
    def _compute_tf(tokens: list[str]) -> dict[str, float]:
        if not tokens:
            return {}
        counts: dict[str, int] = {}
        for token in tokens:
            counts[token] = counts.get(token, 0) + 1
        total = len(tokens)
        return {token: count / total for token, count in counts.items()}

    @staticmethod
    def _compute_idf(documents: list[list[str]]) -> dict[str, float]:
        if not documents:
            return {}
        n = len(documents)
        df: dict[str, int] = {}
        for doc_tokens in documents:
            seen = set(doc_tokens)
            for token in seen:
                df[token] = df.get(token, 0) + 1
        return {token: math.log((n + 1) / (count + 1)) + 1 for token, count in df.items()}

    @staticmethod
    def _compute_cosine_similarity(vec_a: dict[str, float], vec_b: dict[str, float]) -> float:
        common_keys = set(vec_a.keys()) & set(vec_b.keys())
        if not common_keys:
            return 0.0
        dot = sum(vec_a[k] * vec_b[k] for k in common_keys)
        norm_a = math.sqrt(sum(v * v for v in vec_a.values()))
        norm_b = math.sqrt(sum(v * v for v in vec_b.values()))
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return dot / (norm_a * norm_b)

    def search(
        self,
        query: str,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        scope = (filters or {}).get("scope")
        min_confidence = (filters or {}).get("min_confidence", 0.0)

        if not query or not query.strip():
            return []

        search_dirs = self._search_dirs
        if scope == "general":
            search_dirs = [KNOWLEDGE_GENERAL_DIR, KNOWLEDGE_REFERENCES_DIR]
        elif scope == "workspace":
            search_dirs = [KNOWLEDGE_WORKSPACE_DIR]
        elif scope == "experience":
            search_dirs = [KNOWLEDGE_EXPERIENCE_DIR]

        query_tokens = query.lower().split()
        if not query_tokens:
            return []

        doc_data: list[tuple[Path, Path, str, list[str]]] = []
        for search_dir in search_dirs:
            if not search_dir.exists():
                continue
            for f in search_dir.rglob("*.md"):
                try:
                    if f.stat().st_size > self._MAX_FILE_BYTES:
                        continue
                    content = f.read_text(encoding="utf-8")
                    tokens = content.lower().split()
                    doc_data.append((f, search_dir, content, tokens))
                except (OSError, UnicodeDecodeError):
                    continue

        if not doc_data:
            return []

        all_doc_tokens = [tokens for _, _, _, tokens in doc_data]
        idf = self._compute_idf(all_doc_tokens + [query_tokens])
        query_tf = self._compute_tf(query_tokens)
        query_vec = {token: query_tf.get(token, 0.0) * idf.get(token, 0.0) for token in query_tf}

        scored: list[tuple[float, Path, Path, str, list[str]]] = []
        for f, search_dir, content, tokens in doc_data:
            doc_tf = self._compute_tf(tokens)
            doc_vec = {token: doc_tf.get(token, 0.0) * idf.get(token, 0.0) for token in doc_tf}
            similarity = self._compute_cosine_similarity(query_vec, doc_vec)
            if similarity > 0.0:
                scored.append((similarity, f, search_dir, content, tokens))

        if not scored:
            return []

        scored.sort(key=lambda x: x[0], reverse=True)

        results: list[SearchResult] = []
        for similarity, f, search_dir, content, tokens in scored:
            relevance = round(min(1.0, max(0.0, similarity)), 4)
            if relevance < min_confidence:
                continue
            content_lower = content.lower()
            snippet_start = 0
            for qt in query_tokens:
                idx = content_lower.find(qt)
                if idx != -1:
                    snippet_start = max(0, idx - 100)
                    break
            snippet_end = min(len(content), snippet_start + 300)
            snippet = content[snippet_start:snippet_end]
            results.append(SearchResult(
                source=str(f.relative_to(search_dir)),
                content=snippet,
                match_type="keyword_fallback",
                relevance=relevance,
            ))
            if len(results) >= top_k:
                break

        return results


class SQLiteFTSSearchEngine:
    def __init__(self, db_path: Path | None = None) -> None:
        self._db_path = db_path or KNOWLEDGE_DB_PATH

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._db_path))
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
        return conn

    @staticmethod
    def _bm25_score_to_relevance(raw_score: float) -> float:
        neg_score = -raw_score
        relevance = min(1.0, max(0.0, neg_score / 20.0 + 0.5))
        return round(relevance, 4)

    def search(
        self,
        query: str,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        min_confidence = (filters or {}).get("min_confidence", 0.0)
        if not self._db_path.exists():
            return []
        try:
            conn = self._get_connection()
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
                items: list[SearchResult] = []
                for row in rows:
                    relevance = self._bm25_score_to_relevance(row["bm25_score"]) if "bm25_score" in row else 0.3
                    if relevance < min_confidence:
                        continue
                    items.append(SearchResult(
                        source=row["id"] if "id" in row else str(row[0]),
                        content=row["content"] if "content" in row else str(row[1]),
                        match_type="fts5_bm25",
                        relevance=relevance,
                    ))
                return items
            finally:
                conn.close()
        except Exception:
            return []


class HybridSearchEngine:
    def __init__(self, chroma_path: Path | None = None, db_path: Path | None = None) -> None:
        self._chroma_engine = ChromaDBSearchEngine(chroma_path)
        self._fts_engine = SQLiteFTSSearchEngine(db_path)

    def search(
        self,
        query: str,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        semantic_results = self._chroma_engine.search(query, top_k=top_k * 2, filters=filters)
        bm25_results = self._fts_engine.search(query, top_k=top_k * 2, filters=filters)
        merged: dict[str, SearchResult] = {}
        scores: dict[str, float] = {}
        for r in semantic_results:
            merged[r.source] = r
            scores[r.source] = r.relevance * 0.6
        for r in bm25_results:
            if r.source in scores:
                scores[r.source] += r.relevance * 0.4
                merged[r.source] = SearchResult(
                    source=r.source,
                    content=r.content,
                    match_type="hybrid",
                    relevance=round(scores[r.source], 4),
                    metadata=r.metadata,
                )
            else:
                merged[r.source] = SearchResult(
                    source=r.source,
                    content=r.content,
                    match_type="hybrid",
                    relevance=round(r.relevance * 0.4, 4),
                    metadata=r.metadata,
                )
                scores[r.source] = r.relevance * 0.4
        for source in merged:
            if merged[source].match_type != "hybrid":
                merged[source] = SearchResult(
                    source=merged[source].source,
                    content=merged[source].content,
                    match_type="hybrid",
                    relevance=round(scores[source], 4),
                    metadata=merged[source].metadata,
                )
        ranked = sorted(merged.values(), key=lambda x: x.relevance, reverse=True)
        return ranked[:top_k]


_SEARCH_ENGINE_REGISTRY: dict[str, type] = {
    "chromadb": ChromaDBSearchEngine,
    "simple": SimpleSearchEngine,
    "sqlite_fts5": SQLiteFTSSearchEngine,
    "hybrid": HybridSearchEngine,
}

_registry_lock = threading.Lock()
_default_engine_name: str = "auto"


def _detect_best_engine() -> str:
    if _is_chromadb_available():
        if KNOWLEDGE_DB_PATH.exists():
            logger.info("Auto-detected search backend: hybrid (ChromaDB + SQLite FTS5 BM25)")
            return "hybrid"
        logger.info("Auto-detected search backend: chromadb (semantic only)")
        return "chromadb"
    if KNOWLEDGE_DB_PATH.exists():
        logger.info("Auto-detected search backend: sqlite_fts5 (BM25, ChromaDB not available)")
        return "sqlite_fts5"
    logger.info("Auto-detected search backend: simple (keyword, no ChromaDB or SQLite FTS5)")
    return "simple"


def register_search_engine(name: str, engine_class: type) -> None:
    with _registry_lock:
        _SEARCH_ENGINE_REGISTRY[name] = engine_class


def get_search_engine(name: str | None = None) -> SearchEngine:
    engine_name = name or _default_engine_name
    if engine_name == "auto":
        engine_name = _detect_best_engine()
    with _registry_lock:
        engine_class = _SEARCH_ENGINE_REGISTRY.get(engine_name)
    if engine_class is None:
        logger.warning("Search engine '%s' not found, falling back to simple", engine_name)
        return SimpleSearchEngine()
    if engine_name in ("chromadb", "hybrid") and not _is_chromadb_available():
        logger.warning("ChromaDB not available, falling back to SQLite FTS5 + BM25")
        return SQLiteFTSSearchEngine()
    return engine_class()


def set_default_search_engine(name: str) -> None:
    global _default_engine_name
    with _registry_lock:
        if name in _SEARCH_ENGINE_REGISTRY or name == "auto":
            _default_engine_name = name
        else:
            logger.warning("Cannot set default search engine to '%s': not registered", name)


def get_available_backends() -> list[str]:
    backends: list[str] = []
    if _is_chromadb_available():
        backends.append("chromadb")
        backends.append("hybrid")
    if KNOWLEDGE_DB_PATH.exists():
        backends.append("sqlite_fts5")
    backends.append("simple")
    return backends
