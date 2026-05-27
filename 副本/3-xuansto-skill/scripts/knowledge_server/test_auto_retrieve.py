#!/usr/bin/env python3

import unittest
import tempfile
import shutil
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, PropertyMock
from datetime import datetime, timezone

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

try:
    from knowledge_server import (
        KnowledgeServer,
        KnowledgeConfig,
        ProgressiveSearcher,
        DegradationManager,
        EmbeddingManager,
        format_knowledge_context,
        detect_tech_stack,
    )
    server_available = True
except ImportError:
    server_available = False


def _skip_if_no_server(test_func):
    return unittest.skipUnless(server_available, "knowledge-server module not available")(test_func)


def _create_test_config(root: Path) -> Path:
    config_path = root / "config.yaml"
    config_data = {
        "knowledge_base": {
            "server": {"host": "127.0.0.1", "port": 0, "transport": "stdio"},
            "database": {
                "sqlite_path": ".knowledge/index/knowledge.db",
                "chroma_path": ".knowledge/index/chroma_db",
            },
            "retrieval": {
                "semantic_weight": 0.7,
                "keyword_weight": 0.3,
                "top_k": 5,
                "default_strategy": "hybrid",
            },
            "dedup": {
                "similarity_threshold": 0.92,
                "action": "merge",
            },
        }
    }
    config_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        import yaml
        config_path.write_text(yaml.dump(config_data, default_flow_style=False), encoding="utf-8")
    except ImportError:
        config_path.write_text(json.dumps(config_data, indent=2), encoding="utf-8")
    return config_path


def _create_node_project(root: Path):
    pkg = {
        "name": "test-project",
        "dependencies": {
            "react": "^18.2.0",
            "express": "^4.18.0",
        },
        "devDependencies": {
            "typescript": "^5.0.0",
        },
    }
    (root / "package.json").write_text(json.dumps(pkg, indent=2), encoding="utf-8")
    (root / "tsconfig.json").write_text("{}", encoding="utf-8")


@_skip_if_no_server
class TestAutoRetrieveWithValidProject(unittest.TestCase):
    _tmpdir = None
    _server = None

    @classmethod
    def setUpClass(cls):
        cls._tmpdir = tempfile.mkdtemp(prefix="kb_test_auto_retrieve_")
        root = Path(cls._tmpdir)
        _create_node_project(root)
        config_path = _create_test_config(root)
        with patch.dict(os.environ, {}, clear=False):
            if "OPENAI_API_KEY" in os.environ:
                del os.environ["OPENAI_API_KEY"]
            cls._server = KnowledgeServer(root, config_path)
            cls._server._stop_retry_task()
            cls._server._stop_backup_scheduler()
            cls._server.degradation.stop_periodic_check()

    @classmethod
    def tearDownClass(cls):
        if cls._server:
            cls._server.sqlite.close()
            cls._server.chroma.close()
        if cls._tmpdir:
            shutil.rmtree(cls._tmpdir, ignore_errors=True)

    def test_auto_retrieve_with_valid_project(self):
        mock_results = [
            {
                "id": "entry-1",
                "title": "React Hooks Guide",
                "content": "Hooks let you use state in functional components",
                "scope": "workspace",
                "confidence": 0.85,
                "tags": ["react"],
                "type": "standard",
                "category": "programming",
                "summary": "React hooks overview",
                "updated": "2025-01-01",
            }
        ]
        with patch.object(self._server.retrieval, "search", return_value={"results": mock_results, "total": 1, "search_strategy": "hybrid"}):
            result = self._server.auto_retrieve(
                task_type="feature",
                project_path=self._tmpdir,
                query="React hooks",
            )
        self.assertIn("context", result)
        self.assertIn("tech_stack", result)
        self.assertEqual(result["task_type"], "feature")
        self.assertIn("React", [fw["name"] for fw in result["tech_stack"].get("frameworks", [])])
        self.assertGreater(result["results_count"], 0)
        self.assertIn("📚", result["context"])

    def test_auto_retrieve_detects_tech_stack(self):
        result = self._server.auto_retrieve(
            task_type="feature",
            project_path=self._tmpdir,
        )
        tech = result["tech_stack"]
        self.assertIn("TypeScript", tech["languages"])
        framework_names = [fw["name"] for fw in tech["frameworks"]]
        self.assertIn("React", framework_names)
        self.assertIn("Express", framework_names)

    def test_auto_retrieve_bug_fix_strategy(self):
        mock_results = [
            {
                "id": "bug-1",
                "title": "Null Pointer Fix",
                "content": "Check for null before dereferencing",
                "scope": "experience",
                "confidence": 0.75,
                "tags": ["debugging"],
                "type": "error-solution",
                "category": "programming",
                "summary": "Null pointer fix",
                "updated": "2025-01-01",
            }
        ]
        with patch.object(self._server.retrieval, "search", return_value={"results": mock_results, "total": 1, "search_strategy": "hybrid"}) as mock_search:
            result = self._server.auto_retrieve(
                task_type="bug_fix",
                project_path=self._tmpdir,
                query="null pointer",
            )
            call_kwargs = mock_search.call_args
            self.assertEqual(call_kwargs.kwargs.get("type_filters") or call_kwargs[1].get("type_filters"), ["error-solution", "pattern"])
            self.assertEqual(call_kwargs.kwargs.get("min_confidence") or call_kwargs[1].get("min_confidence"), 0.6)

    def test_auto_retrieve_security_strategy(self):
        mock_results = [
            {
                "id": "sec-1",
                "title": "SQL Injection Prevention",
                "content": "Use parameterized queries",
                "scope": "general",
                "confidence": 0.9,
                "tags": ["security"],
                "type": "standard",
                "category": "security",
                "summary": "SQL injection prevention",
                "updated": "2025-01-01",
            }
        ]
        with patch.object(self._server.retrieval, "search", return_value={"results": mock_results, "total": 1, "search_strategy": "keyword_only"}) as mock_search:
            result = self._server.auto_retrieve(
                task_type="security",
                project_path=self._tmpdir,
                query="sql injection",
            )
            call_kwargs = mock_search.call_args
            self.assertEqual(call_kwargs.kwargs.get("min_confidence") or call_kwargs[1].get("min_confidence"), 0.8)
            self.assertEqual(call_kwargs.kwargs.get("category_filters") or call_kwargs[1].get("category_filters"), ["security"])

    def test_auto_retrieve_token_budget(self):
        long_results = [
            {
                "id": f"entry-{i}",
                "title": f"Entry {i}",
                "content": "A" * 2000,
                "scope": "workspace",
                "confidence": 0.7,
                "tags": [],
                "type": "standard",
                "category": "programming",
                "summary": f"Summary {i}",
                "updated": "2025-01-01",
            }
            for i in range(20)
        ]
        with patch.object(self._server.retrieval, "search", return_value={"results": long_results, "total": 20, "search_strategy": "hybrid"}):
            result_small = self._server.auto_retrieve(
                task_type="feature",
                project_path=self._tmpdir,
                token_budget=256,
            )
            result_large = self._server.auto_retrieve(
                task_type="feature",
                project_path=self._tmpdir,
                token_budget=8192,
            )
        self.assertLessEqual(len(result_small["context"]), len(result_large["context"]))

    def test_auto_retrieve_degraded_mode(self):
        mock_degradation = MagicMock()
        mock_degradation.get_search_strategy.return_value = "keyword_only"
        mock_degradation.level = DegradationManager.LEVEL_BM25_ONLY
        mock_degradation.level_name = "bm25_only"

        original_degradation = self._server.degradation
        self._server.degradation = mock_degradation

        try:
            mock_results = [
                {
                    "id": "degraded-1",
                    "title": "Fallback Result",
                    "content": "Keyword search result",
                    "scope": "workspace",
                    "confidence": 0.5,
                    "tags": [],
                    "type": "standard",
                    "category": "programming",
                    "summary": "Fallback",
                    "updated": "2025-01-01",
                }
            ]
            with patch.object(self._server.retrieval, "search", return_value={"results": mock_results, "total": 1, "search_strategy": "keyword_only"}):
                result = self._server.auto_retrieve(
                    task_type="feature",
                    project_path=self._tmpdir,
                )
            self.assertEqual(result["degradation_level"], DegradationManager.LEVEL_BM25_ONLY)
            self.assertEqual(result["degradation_name"], "bm25_only")
            self.assertIn("context", result)
        finally:
            self._server.degradation = original_degradation


if __name__ == "__main__":
    unittest.main()
