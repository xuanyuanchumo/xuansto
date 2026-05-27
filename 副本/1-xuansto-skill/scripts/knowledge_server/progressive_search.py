import logging
from typing import Optional

logger = logging.getLogger("knowledge-server")

TASK_TYPE_SEARCH_CONFIG = {
    "bug_fix": {"mode": "hybrid", "confidence_min": 0.6, "scope_priority": ["experience", "workspace", "general"], "keyword_weight_boost": 0.1},
    "feature": {"mode": "semantic", "confidence_min": 0.5, "scope_priority": ["workspace", "general", "experience"], "keyword_weight_boost": 0.0},
    "refactor": {"mode": "context", "confidence_min": 0.6, "scope_priority": ["workspace", "experience", "general"], "keyword_weight_boost": 0.05},
    "review": {"mode": "keyword", "confidence_min": 0.7, "scope_priority": ["general", "experience", "workspace"], "keyword_weight_boost": 0.2},
    "deploy": {"mode": "precise", "confidence_min": 0.8, "scope_priority": ["experience", "general", "workspace"], "keyword_weight_boost": 0.15},
    "security": {"mode": "precise", "confidence_min": 0.8, "scope_priority": ["general", "experience", "workspace"], "keyword_weight_boost": 0.2},
}

SCOPE_TOKEN_BUDGET = {
    "workspace": 1024,
    "experience": 512,
    "general": 512,
}

_CHARS_PER_TOKEN = 3.5

_STRATEGY_MAP = {
    "hybrid": "hybrid",
    "semantic": "semantic_only",
    "keyword": "keyword_only",
    "context": "hybrid",
    "precise": "keyword_only",
}


class ProgressiveSearcher:

    def __init__(self, db_engine, vector_engine=None, retrieval_engine=None):
        self.db_engine = db_engine
        self.vector_engine = vector_engine
        self.retrieval_engine = retrieval_engine

    def search(self, query: str, task_type: str, tech_stack: dict, token_budget: int = 2048) -> dict:
        config = TASK_TYPE_SEARCH_CONFIG.get(task_type, TASK_TYPE_SEARCH_CONFIG["feature"])
        tech_filters = self._build_tech_stack_filters(tech_stack)
        all_results = []
        seen_ids = set()
        remaining_budget = token_budget

        for scope in config["scope_priority"]:
            scope_budget = min(
                SCOPE_TOKEN_BUDGET.get(scope, 512),
                remaining_budget,
            )
            if scope_budget <= 0:
                continue

            scope_results = self._search_by_scope(query, scope, config, tech_filters, scope_budget)

            for r in scope_results:
                rid = r.get("id")
                if rid and rid not in seen_ids:
                    seen_ids.add(rid)
                    all_results.append(r)

            used_tokens = sum(self._estimate_tokens(r) for r in scope_results)
            remaining_budget -= used_tokens

        pruned_results, pruned_ids = self._prune_by_token_budget(all_results, token_budget)

        return {
            "results": pruned_results,
            "total": len(pruned_results),
            "task_type": task_type,
            "search_config": {
                "mode": config["mode"],
                "confidence_min": config["confidence_min"],
                "scope_priority": config["scope_priority"],
            },
            "token_budget": token_budget,
            "pruned_entry_ids": pruned_ids,
        }

    def _build_tech_stack_filters(self, tech_stack: dict) -> dict:
        filters = {"tag_filters": [], "type_filters": [], "category_filters": []}
        if not tech_stack:
            return filters

        tag_parts = []
        for lang in tech_stack.get("languages", []):
            tag_parts.append(lang.lower().strip())
        for fw in tech_stack.get("frameworks", []):
            tag_parts.append(fw.lower().strip())
        for rt in tech_stack.get("runtimes", []):
            tag_parts.append(rt.lower().strip())

        filters["tag_filters"] = tag_parts
        return filters

    def _search_by_scope(self, query: str, scope: str, config: dict, tech_filters: dict, token_budget: int) -> list:
        if self.retrieval_engine is None:
            return []

        strategy = _STRATEGY_MAP.get(config["mode"], "hybrid")
        confidence_min = config["confidence_min"]
        keyword_boost = config.get("keyword_weight_boost", 0.0)

        original_kw_weight = None
        original_sw_weight = None
        if keyword_boost > 0:
            original_kw_weight = self.retrieval_engine.keyword_weight
            original_sw_weight = self.retrieval_engine.semantic_weight
            self.retrieval_engine.keyword_weight = min(1.0, original_kw_weight + keyword_boost)
            self.retrieval_engine.semantic_weight = max(0.0, 1.0 - self.retrieval_engine.keyword_weight)

        try:
            max_entries_by_budget = max(3, token_budget // 100)
            top_k = min(max_entries_by_budget, 10)

            result = self.retrieval_engine.search(
                query=query,
                scope=scope,
                top_k=top_k,
                strategy=strategy,
                min_confidence=confidence_min,
                tag_filters=tech_filters.get("tag_filters") or None,
                type_filters=tech_filters.get("type_filters") or None,
                category_filters=tech_filters.get("category_filters") or None,
            )
            return result.get("results", [])
        except Exception as e:
            logger.warning("operation=progressive_search_by_scope, scope=%s, error=%s", scope, e)
            return []
        finally:
            if original_kw_weight is not None:
                self.retrieval_engine.keyword_weight = original_kw_weight
                self.retrieval_engine.semantic_weight = original_sw_weight

    def _prune_by_token_budget(self, results: list, token_budget: int) -> tuple:
        if not results:
            return [], []

        scored = []
        for r in results:
            priority = 0
            confidence = r.get("confidence", 0)
            if confidence >= 0.8:
                priority += 3
            elif confidence >= 0.6:
                priority += 1

            tags = r.get("tags", [])
            if tags:
                priority += 1

            scope = r.get("scope", "")
            if scope == "experience":
                entry_type = r.get("type", "")
                if entry_type == "error-solution":
                    priority += 2

            scored.append((priority, confidence, r))

        scored.sort(key=lambda x: (x[0], x[1]), reverse=True)

        pruned = []
        pruned_ids = []
        used_tokens = 0

        for _priority, _confidence, r in scored:
            entry_tokens = self._estimate_tokens(r)
            content = r.get("content", "")
            summary = r.get("summary", "")

            if used_tokens + entry_tokens <= token_budget:
                pruned.append(r)
                used_tokens += entry_tokens
            elif summary:
                summary_tokens = self._estimate_tokens({"content": summary})
                if used_tokens + summary_tokens <= token_budget:
                    pruned_entry = r.copy()
                    pruned_entry["content"] = summary
                    pruned_entry["_truncated"] = True
                    pruned.append(pruned_entry)
                    used_tokens += summary_tokens
                    pruned_ids.append(r["id"])
                else:
                    pruned_ids.append(r["id"])
            else:
                max_content_tokens = token_budget - used_tokens
                if max_content_tokens > 20:
                    max_chars = int(max_content_tokens * _CHARS_PER_TOKEN)
                    truncated_entry = r.copy()
                    truncated_entry["content"] = content[:max_chars]
                    truncated_entry["_truncated"] = True
                    pruned.append(truncated_entry)
                    used_tokens += max_content_tokens
                    pruned_ids.append(r["id"])
                else:
                    pruned_ids.append(r["id"])

        return pruned, pruned_ids

    def deep_load(self, entry_id: str) -> dict:
        entry = self.db_engine.get_entry(entry_id)
        if entry is None:
            return {"error": "not_found", "entry_id": entry_id}

        try:
            conn = self.db_engine._get_conn()
            conn.execute(
                "INSERT INTO usage_logs (entry_id, agent_role, query_text, result_count, elapsed_ms) "
                "VALUES (?, 'progressive_deep_load', ?, 1, 0.0)",
                (entry_id, f"deep_load:{entry_id}"),
            )
            conn.commit()
        except Exception as e:
            logger.warning("operation=deep_load_log, entry_id=%s, error=%s", entry_id, e)

        return entry

    @staticmethod
    def _estimate_tokens(entry: dict) -> int:
        content = entry.get("content", "")
        return max(1, int(len(content) / _CHARS_PER_TOKEN))
