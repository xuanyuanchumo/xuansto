import logging
import re
from pathlib import Path
from typing import Optional

from .config import AGENT_RETRIEVAL_PROFILES, KnowledgeConfig
from .db_engine import SQLiteEngine
from .vector_engine import ChromaEngine

logger = logging.getLogger("knowledge-server")


class HybridRetrievalEngine:
    def __init__(self, sqlite_engine: SQLiteEngine, chroma_engine: ChromaEngine, config: KnowledgeConfig):
        self.sqlite = sqlite_engine
        self.chroma = chroma_engine
        self.semantic_weight = config.semantic_weight
        self.keyword_weight = config.keyword_weight
        self.rrf_k = config.retrieval.get("hybrid", {}).get("rrf_k", 60)
        self.knowledge_root = config.knowledge_root

    def search(
        self,
        query: str,
        scope: Optional[str] = None,
        top_k: int = 5,
        strategy: str = "hybrid",
        min_confidence: float = 0.0,
        tag_filters: Optional[list[str]] = None,
        agent_role: Optional[str] = None,
        type_filters: Optional[list[str]] = None,
        category_filters: Optional[list[str]] = None,
    ) -> dict:
        expand_k = min(top_k * 4, 80)

        profile_type_filters = None
        profile_category_filters = None
        profile_min_confidence = 0.0
        profile_priority_layers = None

        if agent_role and agent_role in AGENT_RETRIEVAL_PROFILES:
            profile = AGENT_RETRIEVAL_PROFILES[agent_role]
            profile_filters = profile.get("filters", {})
            profile_type_filters = profile_filters.get("type")
            profile_category_filters = profile_filters.get("category")
            profile_min_confidence = profile.get("min_confidence", 0.0)
            profile_priority_layers = profile.get("priority_layers")

        effective_min_confidence = max(min_confidence, profile_min_confidence)

        effective_type_filters = profile_type_filters or type_filters
        effective_category_filters = profile_category_filters or category_filters

        if strategy == "file_search":
            return self._file_search(query, scope, top_k, tag_filters)

        keyword_results = []
        semantic_results = []

        if strategy in ("hybrid", "keyword_only"):
            try:
                keyword_results = self.sqlite.search_fts(
                    query, scope=scope, top_k=expand_k,
                    type_filters=effective_type_filters,
                    category_filters=effective_category_filters,
                )
            except Exception as e:
                logger.warning("operation=fts_search_failed, error=%s, falling_back=file_search", e)
                return self._file_search(query, scope, top_k, tag_filters)

        if strategy in ("hybrid", "semantic_only") and self.chroma.available:
            semantic_results = self.chroma.search_semantic(query, top_k=expand_k)
            if semantic_results and (scope or effective_type_filters or effective_category_filters):
                entry_ids = [r["id"] for r in semantic_results]
                metadata_map = self.sqlite.batch_get_metadata(entry_ids)
                filtered = []
                for r in semantic_results:
                    meta = metadata_map.get(r["id"])
                    if meta is None:
                        continue
                    if meta.get("status") == "archived":
                        continue
                    if scope and meta["scope"] != scope:
                        continue
                    if effective_type_filters and meta["type"] not in effective_type_filters:
                        continue
                    if effective_category_filters and meta["category"] not in effective_category_filters:
                        continue
                    if meta["embedding_status"] != "ready":
                        continue
                    filtered.append(r)
                semantic_results = filtered
            elif semantic_results:
                entry_ids = [r["id"] for r in semantic_results]
                metadata_map = self.sqlite.batch_get_metadata(entry_ids)
                semantic_results = [
                    r for r in semantic_results
                    if metadata_map.get(r["id"], {}).get("embedding_status") == "ready"
                    and metadata_map.get(r["id"], {}).get("status") != "archived"
                ]

        if strategy == "hybrid" and keyword_results and semantic_results:
            merged = self._rrf_merge(keyword_results, semantic_results, top_k, profile_priority_layers)
        elif strategy == "semantic_only" and semantic_results:
            merged = semantic_results[:top_k]
        else:
            merged = keyword_results[:top_k]

        if effective_min_confidence > 0:
            merged = [r for r in merged if r.get("confidence", 0) >= effective_min_confidence]

        merged = [r for r in merged if r.get("status") != "archived"]

        if tag_filters:
            merged = [
                r for r in merged
                if any(tag in r.get("tags", []) for tag in tag_filters)
            ]

        final_results = []
        for r in merged[:top_k]:
            entry = r.copy()
            entry.pop("_bm25_score", None)
            entry.pop("_cosine_similarity", None)
            entry.pop("_rrf_score", None)
            final_results.append(entry)

        return {
            "results": final_results,
            "total": len(final_results),
            "search_strategy": strategy,
        }

    def _rrf_merge(self, keyword_results: list, semantic_results: list, top_k: int, priority_layers: Optional[list[str]] = None) -> list:
        k = self.rrf_k
        scores: dict[str, float] = {}
        entry_map: dict[str, dict] = {}

        for rank, item in enumerate(keyword_results, start=1):
            eid = item["id"]
            scores[eid] = scores.get(eid, 0.0) + self.keyword_weight / (k + rank)
            entry_map[eid] = item

        for rank, item in enumerate(semantic_results, start=1):
            eid = item["id"]
            scores[eid] = scores.get(eid, 0.0) + self.semantic_weight / (k + rank)
            if eid not in entry_map:
                full = self.sqlite.get_entry(eid)
                if full:
                    entry_map[eid] = full
                    entry_map[eid]["_cosine_similarity"] = item.get("_cosine_similarity", 0.0)
            elif "_cosine_similarity" not in entry_map[eid]:
                entry_map[eid]["_cosine_similarity"] = item.get("_cosine_similarity", 0.0)

        if priority_layers:
            for eid in scores:
                entry = entry_map.get(eid)
                if entry:
                    scope = entry.get("scope", "")
                    if scope in priority_layers:
                        layer_idx = priority_layers.index(scope)
                        scores[eid] *= (1.0 + 0.1 * (len(priority_layers) - layer_idx))

        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
        results = []
        for eid in sorted_ids[:top_k]:
            entry = entry_map[eid].copy()
            entry["_rrf_score"] = scores[eid]
            results.append(entry)
        return results

    def _file_search(self, query: str, scope: Optional[str] = None, top_k: int = 5, tag_filters: Optional[list[str]] = None) -> dict:
        logger.warning("operation=file_search_fallback, query=%s, scope=%s", query, scope)
        results = []
        query_lower = query.lower()
        query_terms = set(re.findall(r'\w+', query_lower))
        search_dirs = [scope] if scope else ("general", "workspace", "experience")

        for search_scope in search_dirs:
            scope_dir = self.knowledge_root / search_scope
            if not scope_dir.is_dir():
                continue
            for md_file in scope_dir.rglob("*.md"):
                try:
                    text = md_file.read_text(encoding="utf-8", errors="ignore")
                    text_lower = text.lower()
                    match_count = sum(1 for term in query_terms if term in text_lower)
                    if match_count > 0:
                        score = match_count / len(query_terms) if query_terms else 0
                        title = md_file.stem
                        rel_path = str(md_file.relative_to(self.knowledge_root))
                        results.append({
                            "id": f"file:{rel_path}",
                            "title": title,
                            "content": text[:500],
                            "scope": search_scope,
                            "source_path": rel_path,
                            "confidence": round(score, 2),
                            "tags": [],
                            "type": "unknown",
                            "category": "uncategorized",
                            "status": "active",
                            "_file_search_score": score,
                        })
                except Exception:
                    continue

        results.sort(key=lambda x: x.get("_file_search_score", 0), reverse=True)

        if tag_filters:
            results = [r for r in results if any(tag in r.get("tags", []) for tag in tag_filters)]

        final_results = []
        for r in results[:top_k]:
            entry = r.copy()
            entry.pop("_file_search_score", None)
            final_results.append(entry)

        return {
            "results": final_results,
            "total": len(final_results),
            "search_strategy": "file_search",
        }
