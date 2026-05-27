#!/usr/bin/env python3

import unittest
import json
import tempfile
import shutil
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, PropertyMock

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

try:
    from knowledge_server.kb_client import KnowledgeBaseClient
    kb_client_available = True
except ImportError:
    kb_client_available = False


def _skip_if_no_client(test_func):
    return unittest.skipUnless(kb_client_available, "kb_client module not available")(test_func)


def _create_knowledge_dir(project_path: str):
    knowledge_dir = Path(project_path) / ".knowledge"
    for scope in ("general", "workspace", "experience"):
        scope_dir = knowledge_dir / scope
        scope_dir.mkdir(parents=True, exist_ok=True)
    return knowledge_dir


def _write_md_entry(knowledge_dir: Path, scope: str, filename: str, title: str, content: str, tags=None):
    scope_dir = knowledge_dir / scope
    scope_dir.mkdir(parents=True, exist_ok=True)
    meta = {"title": title, "tags": tags or [], "type": "standard", "category": "programming", "id": f"file:{scope}/{filename}"}
    try:
        import yaml
        frontmatter = yaml.dump(meta, default_flow_style=False, allow_unicode=True, sort_keys=False)
    except ImportError:
        frontmatter = json.dumps(meta, ensure_ascii=False, indent=2)
    filepath = scope_dir / filename
    filepath.write_text(f"---\n{frontmatter}---\n{content}", encoding="utf-8")


@_skip_if_no_client
class TestClientMcpFirst(unittest.TestCase):
    _tmpdir = None

    @classmethod
    def setUpClass(cls):
        cls._tmpdir = tempfile.mkdtemp(prefix="kb_test_client_mcp_")

    @classmethod
    def tearDownClass(cls):
        if cls._tmpdir:
            shutil.rmtree(cls._tmpdir, ignore_errors=True)

    def test_client_mcp_first(self):
        client = KnowledgeBaseClient(project_path=self._tmpdir)

        mcp_result = [{"id": "mcp-1", "title": "MCP Result", "content": "From MCP", "confidence": 0.9}]
        rest_result = [{"id": "rest-1", "title": "REST Result", "content": "From REST", "confidence": 0.8}]

        with patch.object(client, "_search_via_mcp", return_value=mcp_result) as mock_mcp, \
             patch.object(client, "_search_via_rest", return_value=rest_result) as mock_rest:
            results = client.search("test query")

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], "mcp-1")
        mock_mcp.assert_called_once()
        mock_rest.assert_not_called()


@_skip_if_no_client
class TestClientRestFallback(unittest.TestCase):
    _tmpdir = None

    @classmethod
    def setUpClass(cls):
        cls._tmpdir = tempfile.mkdtemp(prefix="kb_test_client_rest_")

    @classmethod
    def tearDownClass(cls):
        if cls._tmpdir:
            shutil.rmtree(cls._tmpdir, ignore_errors=True)

    def test_client_rest_fallback(self):
        client = KnowledgeBaseClient(project_path=self._tmpdir)

        rest_result = [{"id": "rest-1", "title": "REST Result", "content": "From REST", "confidence": 0.8}]

        def _rest_search(**kwargs):
            client.mode = "rest"
            return rest_result

        with patch.object(client, "_search_via_mcp", return_value=None), \
             patch.object(client, "_search_via_rest", side_effect=lambda **kw: _rest_search(**kw)):
            results = client.search("test query")

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], "rest-1")
        self.assertEqual(client.mode, "rest")


@_skip_if_no_client
class TestClientFilesystemFallback(unittest.TestCase):
    _tmpdir = None
    _knowledge_dir = None

    @classmethod
    def setUpClass(cls):
        cls._tmpdir = tempfile.mkdtemp(prefix="kb_test_client_fs_")
        cls._knowledge_dir = _create_knowledge_dir(cls._tmpdir)
        _write_md_entry(
            cls._knowledge_dir, "workspace", "react-hooks.md",
            "React Hooks", "Hooks let you use state in functional components",
            tags=["react", "hooks"],
        )

    @classmethod
    def tearDownClass(cls):
        if cls._tmpdir:
            shutil.rmtree(cls._tmpdir, ignore_errors=True)

    def test_client_filesystem_fallback(self):
        client = KnowledgeBaseClient(project_path=self._tmpdir)

        with patch.object(client, "_search_via_mcp", return_value=None), \
             patch.object(client, "_search_via_rest", return_value=None):
            results = client.search("React Hooks")

        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
        self.assertEqual(client.mode, "filesystem")
        self.assertIn("React", results[0].get("title", ""))


@_skip_if_no_client
class TestClientSearchAllFail(unittest.TestCase):
    _tmpdir = None

    @classmethod
    def setUpClass(cls):
        cls._tmpdir = tempfile.mkdtemp(prefix="kb_test_client_allfail_")

    @classmethod
    def tearDownClass(cls):
        if cls._tmpdir:
            shutil.rmtree(cls._tmpdir, ignore_errors=True)

    def test_client_search_all_fail(self):
        client = KnowledgeBaseClient(project_path=self._tmpdir)

        def _failing_method(**kwargs):
            raise Exception("method failed")

        with patch.object(client, "_search_via_mcp", _failing_method), \
             patch.object(client, "_search_via_rest", _failing_method), \
             patch.object(client, "_search_via_filesystem", _failing_method):
            results = client.search("test query")

        self.assertEqual(results, [])


@_skip_if_no_client
class TestClientAddViaMcp(unittest.TestCase):
    _tmpdir = None

    @classmethod
    def setUpClass(cls):
        cls._tmpdir = tempfile.mkdtemp(prefix="kb_test_client_add_mcp_")

    @classmethod
    def tearDownClass(cls):
        if cls._tmpdir:
            shutil.rmtree(cls._tmpdir, ignore_errors=True)

    def test_client_add_via_mcp(self):
        client = KnowledgeBaseClient(project_path=self._tmpdir)

        mcp_add_result = {"id": "mcp-new-1", "status": "created", "dedup_status": "new"}

        with patch.object(client, "_add_via_mcp", return_value=mcp_add_result) as mock_mcp, \
             patch.object(client, "_add_via_rest") as mock_rest:
            result = client.add(
                title="New Entry",
                content="New content via MCP",
                scope="workspace",
                tags=["test"],
            )

        self.assertEqual(result["id"], "mcp-new-1")
        self.assertEqual(result["status"], "created")
        mock_mcp.assert_called_once()
        mock_rest.assert_not_called()


@_skip_if_no_client
class TestClientAddViaRest(unittest.TestCase):
    _tmpdir = None

    @classmethod
    def setUpClass(cls):
        cls._tmpdir = tempfile.mkdtemp(prefix="kb_test_client_add_rest_")

    @classmethod
    def tearDownClass(cls):
        if cls._tmpdir:
            shutil.rmtree(cls._tmpdir, ignore_errors=True)

    def test_client_add_via_rest(self):
        client = KnowledgeBaseClient(project_path=self._tmpdir)

        rest_add_result = {"id": "rest-new-1", "status": "created"}

        def _rest_add(**kwargs):
            client.mode = "rest"
            return rest_add_result

        with patch.object(client, "_add_via_mcp", return_value=None), \
             patch.object(client, "_add_via_rest", side_effect=_rest_add):
            result = client.add(
                title="New Entry",
                content="New content via REST",
                scope="workspace",
                tags=["test"],
            )

        self.assertEqual(result["id"], "rest-new-1")
        self.assertEqual(result["status"], "created")
        self.assertEqual(client.mode, "rest")


if __name__ == "__main__":
    unittest.main()
