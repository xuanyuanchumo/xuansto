#!/usr/bin/env python3

import unittest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, call

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

try:
    from knowledge_server.progressive_search import (
        ProgressiveSearcher,
        TASK_TYPE_SEARCH_CONFIG,
        SCOPE_TOKEN_BUDGET,
        _STRATEGY_MAP,
        _CHARS_PER_TOKEN,
    )
    progressive_available = True
except ImportError:
    progressive_available = False


def _skip_if_no_progressive(test_func):
    return unittest.skipUnless(progressive_available, "progressive_search module not available")(test_func)


def _make_entry(entry_id, title, content, scope, confidence, tags=None, entry_type="standard", category="programming", summary=""):
    return {
        "id": entry_id,
        "title": title,
        "content": content,
        "scope": scope,
        "confidence": confidence,
        "tags": tags or [],
        "type": entry_type,
        "category": category,
        "summary": summary,
    }


@_skip_if_no_progressive
class TestProgressiveSearchBugFix(unittest.TestCase):
    def test_progressive_search_bug_fix(self):
        mock_retrieval = MagicMock()
        mock_db = MagicMock()

        experience_results = [_make_entry("exp-1", "Bug Fix A", "Fix for null pointer", "experience", 0.8, ["debugging"], "error-solution")]
        workspace_results = [_make_entry("ws-1", "Workspace Bug", "Workspace debug info", "workspace", 0.7, ["debug"])]
        general_results = [_make_entry("gen-1", "General Debug", "General debugging tips", "general", 0.5)]

        def mock_search(**kwargs):
            scope = kwargs.get("scope", "")
            if scope == "experience":
                return {"results": experience_results}
            elif scope == "workspace":
                return {"results": workspace_results}
            elif scope == "general":
                return {"results": general_results}
            return {"results": []}

        mock_retrieval.search.side_effect = mock_search
        mock_retrieval.keyword_weight = 0.3
        mock_retrieval.semantic_weight = 0.7

        searcher = ProgressiveSearcher(db_engine=mock_db, retrieval_engine=mock_retrieval)
        result = searcher.search(query="null pointer error", task_type="bug_fix", tech_stack={})

        config = TASK_TYPE_SEARCH_CONFIG["bug_fix"]
        self.assertEqual(config["scope_priority"], ["experience", "workspace", "general"])
        self.assertEqual(result["task_type"], "bug_fix")
        self.assertGreater(result["total"], 0)

        scope_calls = [c.kwargs.get("scope") or c[1].get("scope") for c in mock_retrieval.search.call_args_list]
        self.assertEqual(scope_calls[0], "experience")
        if len(scope_calls) > 1:
            self.assertEqual(scope_calls[1], "workspace")
        if len(scope_calls) > 2:
            self.assertEqual(scope_calls[2], "general")


@_skip_if_no_progressive
class TestProgressiveSearchFeature(unittest.TestCase):
    def test_progressive_search_feature(self):
        mock_retrieval = MagicMock()
        mock_db = MagicMock()

        workspace_results = [_make_entry("ws-1", "Feature Pattern", "Pattern for features", "workspace", 0.7)]
        general_results = [_make_entry("gen-1", "General Pattern", "General feature pattern", "general", 0.5)]
        experience_results = [_make_entry("exp-1", "Experience Tip", "Past experience", "experience", 0.6)]

        def mock_search(**kwargs):
            scope = kwargs.get("scope", "")
            if scope == "workspace":
                return {"results": workspace_results}
            elif scope == "general":
                return {"results": general_results}
            elif scope == "experience":
                return {"results": experience_results}
            return {"results": []}

        mock_retrieval.search.side_effect = mock_search
        mock_retrieval.keyword_weight = 0.3
        mock_retrieval.semantic_weight = 0.7

        searcher = ProgressiveSearcher(db_engine=mock_db, retrieval_engine=mock_retrieval)
        result = searcher.search(query="add user auth", task_type="feature", tech_stack={})

        config = TASK_TYPE_SEARCH_CONFIG["feature"]
        self.assertEqual(config["scope_priority"], ["workspace", "general", "experience"])
        self.assertEqual(result["task_type"], "feature")

        scope_calls = [c.kwargs.get("scope") or c[1].get("scope") for c in mock_retrieval.search.call_args_list]
        self.assertEqual(scope_calls[0], "workspace")


@_skip_if_no_progressive
class TestProgressiveSearchTokenBudget(unittest.TestCase):
    def test_progressive_search_token_budget(self):
        mock_retrieval = MagicMock()
        mock_db = MagicMock()

        large_results = [
            _make_entry(f"entry-{i}", f"Entry {i}", "A" * 500, "workspace", 0.7)
            for i in range(20)
        ]
        mock_retrieval.search.return_value = {"results": large_results}
        mock_retrieval.keyword_weight = 0.3
        mock_retrieval.semantic_weight = 0.7

        searcher = ProgressiveSearcher(db_engine=mock_db, retrieval_engine=mock_retrieval)

        result_small = searcher.search(query="test", task_type="feature", tech_stack={}, token_budget=256)
        result_large = searcher.search(query="test", task_type="feature", tech_stack={}, token_budget=8192)

        self.assertLessEqual(result_small["total"], result_large["total"])
        self.assertEqual(result_small["token_budget"], 256)
        self.assertEqual(result_large["token_budget"], 8192)


@_skip_if_no_progressive
class TestProgressiveSearchTechStackFilters(unittest.TestCase):
    def test_progressive_search_tech_stack_filters(self):
        mock_retrieval = MagicMock()
        mock_db = MagicMock()

        mock_retrieval.search.return_value = {"results": []}
        mock_retrieval.keyword_weight = 0.3
        mock_retrieval.semantic_weight = 0.7

        searcher = ProgressiveSearcher(db_engine=mock_db, retrieval_engine=mock_retrieval)

        tech_stack = {
            "languages": ["Python", "TypeScript"],
            "frameworks": ["React", "FastAPI"],
            "runtimes": ["Node.js"],
        }

        searcher.search(query="api design", task_type="feature", tech_stack=tech_stack)

        for call_args in mock_retrieval.search.call_args_list:
            tag_filters = call_args.kwargs.get("tag_filters") or call_args[1].get("tag_filters")
            if tag_filters:
                filter_lower = [t.lower() for t in tag_filters]
                self.assertTrue(
                    "python" in filter_lower or "typescript" in filter_lower
                    or "react" in filter_lower or "fastapi" in filter_lower
                    or "node.js" in filter_lower,
                    f"Expected tech stack tags in filters, got: {filter_lower}",
                )


@_skip_if_no_progressive
class TestDeepLoad(unittest.TestCase):
    def test_deep_load(self):
        mock_db = MagicMock()
        mock_conn = MagicMock()
        mock_db._get_conn.return_value = mock_conn
        mock_db.get_entry.return_value = {
            "id": "deep-1",
            "title": "Deep Entry",
            "content": "Full content for deep load",
            "scope": "experience",
            "confidence": 0.9,
        }

        searcher = ProgressiveSearcher(db_engine=mock_db)
        result = searcher.deep_load("deep-1")

        self.assertIsNotNone(result)
        self.assertEqual(result["id"], "deep-1")
        self.assertEqual(result["content"], "Full content for deep load")
        mock_db.get_entry.assert_called_once_with("deep-1")

    def test_deep_load_not_found(self):
        mock_db = MagicMock()
        mock_db.get_entry.return_value = None

        searcher = ProgressiveSearcher(db_engine=mock_db)
        result = searcher.deep_load("nonexistent")

        self.assertIn("error", result)
        self.assertEqual(result["error"], "not_found")


@_skip_if_no_progressive
class TestProgressiveSearchPrunePriority(unittest.TestCase):
    def test_progressive_search_prune_priority(self):
        mock_retrieval = MagicMock()
        mock_db = MagicMock()

        results = [
            _make_entry("low-1", "Low Confidence", "Low conf content", "general", 0.3, [], "standard"),
            _make_entry("mid-1", "Medium Confidence", "Medium conf content", "workspace", 0.65, ["react"], "standard"),
            _make_entry("high-1", "High Confidence", "High conf content", "experience", 0.9, ["debugging"], "error-solution"),
            _make_entry("mid-2", "Medium No Tags", "Medium no tags content", "workspace", 0.6, [], "standard"),
        ]

        mock_retrieval.search.return_value = {"results": results}
        mock_retrieval.keyword_weight = 0.3
        mock_retrieval.semantic_weight = 0.7

        searcher = ProgressiveSearcher(db_engine=mock_db, retrieval_engine=mock_retrieval)
        result = searcher.search(query="test", task_type="bug_fix", tech_stack={}, token_budget=512)

        returned_ids = [r["id"] for r in result["results"]]
        if "high-1" in returned_ids and "low-1" in returned_ids:
            high_idx = returned_ids.index("high-1")
            low_idx = returned_ids.index("low-1")
            self.assertLess(high_idx, low_idx)

    def test_prune_by_token_budget_truncation(self):
        mock_retrieval = MagicMock()
        mock_db = MagicMock()

        results = [
            _make_entry("big-1", "Big Entry", "A" * 2000, "workspace", 0.9, summary="Short summary"),
            _make_entry("big-2", "Big Entry 2", "B" * 2000, "workspace", 0.8, summary="Short summary 2"),
        ]

        mock_retrieval.search.return_value = {"results": results}
        mock_retrieval.keyword_weight = 0.3
        mock_retrieval.semantic_weight = 0.7

        searcher = ProgressiveSearcher(db_engine=mock_db, retrieval_engine=mock_retrieval)
        result = searcher.search(query="test", task_type="feature", tech_stack={}, token_budget=200)

        for r in result["results"]:
            estimated_tokens = max(1, int(len(r.get("content", "")) / _CHARS_PER_TOKEN))
            self.assertLessEqual(estimated_tokens, 200)


if __name__ == "__main__":
    unittest.main()
