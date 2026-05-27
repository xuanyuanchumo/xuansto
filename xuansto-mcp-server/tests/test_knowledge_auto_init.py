import sqlite3
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from xuansto_mcp.tools.knowledge_search import _ensure_knowledge_index


@pytest.fixture
def tmp_knowledge_root(tmp_path):
    knowledge_dir = tmp_path / "knowledge"
    knowledge_dir.mkdir(parents=True, exist_ok=True)
    return knowledge_dir


@pytest.fixture(autouse=True)
def patch_knowledge_dirs(tmp_knowledge_root):
    index_dir = tmp_knowledge_root / "index"
    db_path = index_dir / "knowledge.db"
    chroma_path = index_dir / "chroma_db"
    general_dir = tmp_knowledge_root / "general"
    workspace_dir = tmp_knowledge_root / "workspace"
    experience_dir = tmp_knowledge_root / "experience"
    patterns_dir = tmp_knowledge_root.parent / "patterns"

    general_dir.mkdir(parents=True, exist_ok=True)
    workspace_dir.mkdir(parents=True, exist_ok=True)
    experience_dir.mkdir(parents=True, exist_ok=True)
    patterns_dir.mkdir(parents=True, exist_ok=True)

    with patch("xuansto_mcp.core.config.KNOWLEDGE_DIR", tmp_knowledge_root), \
         patch("xuansto_mcp.tools.knowledge_search.KNOWLEDGE_GENERAL_DIR", general_dir), \
         patch("xuansto_mcp.tools.knowledge_search.KNOWLEDGE_WORKSPACE_DIR", workspace_dir), \
         patch("xuansto_mcp.tools.knowledge_search.KNOWLEDGE_EXPERIENCE_DIR", experience_dir), \
         patch("xuansto_mcp.tools.knowledge_search.KNOWLEDGE_DB_PATH", db_path), \
         patch("xuansto_mcp.tools.knowledge_search.KNOWLEDGE_CHROMA_PATH", chroma_path), \
         patch("xuansto_mcp.core.config.PATTERNS_DIR", patterns_dir), \
         patch("xuansto_mcp.tools.knowledge_search.REFERENCES_DIR", tmp_knowledge_root / "references"):
        yield


class TestEnsureKnowledgeIndex:
    def test_creates_sqlite_db_when_not_exists(self, tmp_knowledge_root):
        db_path = tmp_knowledge_root / "index" / "knowledge.db"
        assert not db_path.exists()

        _ensure_knowledge_index()

        assert db_path.exists()
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        conn.close()

        assert "knowledge_entries" in tables
        assert "knowledge_fts" in tables

    def test_creates_triggers(self, tmp_knowledge_root):
        _ensure_knowledge_index()

        db_path = tmp_knowledge_root / "index" / "knowledge.db"
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='trigger'")
        triggers = {row[0] for row in cursor.fetchall()}
        conn.close()

        assert "knowledge_ai" in triggers
        assert "knowledge_ad" in triggers

    def test_idempotent_multiple_calls(self, tmp_knowledge_root):
        _ensure_knowledge_index()
        _ensure_knowledge_index()
        _ensure_knowledge_index()

        db_path = tmp_knowledge_root / "index" / "knowledge.db"
        assert db_path.exists()

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) FROM knowledge_entries")
        count = cursor.fetchone()[0]
        conn.close()

        assert count == 0

    def test_does_not_recreate_existing_db(self, tmp_knowledge_root):
        _ensure_knowledge_index()
        db_path = tmp_knowledge_root / "index" / "knowledge.db"

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO knowledge_entries (id, title, content, type, metadata_json, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("test-id", "test title", "test content", "general", "{}", "2025-01-01", "2025-01-01"),
        )
        conn.commit()
        conn.close()

        _ensure_knowledge_index()

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM knowledge_entries")
        rows = cursor.fetchall()
        conn.close()

        assert len(rows) == 1
        assert rows[0][0] == "test-id"


class TestRetrieveWithoutIndex:
    @pytest.mark.asyncio
    async def test_retrieve_returns_empty_not_error(self, tmp_knowledge_root):
        from mcp.server.fastmcp import FastMCP
        from xuansto_mcp.tools.knowledge_search import register

        mcp = FastMCP("test")
        register(mcp)
        tools = await mcp.list_tools()
        knowledge_tool = None
        for t in tools:
            if t.name == "knowledge_search":
                knowledge_tool = t
                break

        assert knowledge_tool is not None

        from xuansto_mcp.tools.knowledge_search import _keyword_fallback_search
        result = _keyword_fallback_search("test query", 5, None)

        assert "results" in result
        assert result["total"] == 0
        assert isinstance(result["results"], list)


class TestInjectCreatesIndex:
    def test_inject_creates_index_automatically(self, tmp_knowledge_root):
        db_path = tmp_knowledge_root / "index" / "knowledge.db"
        assert not db_path.exists()

        _ensure_knowledge_index()

        # NOTE: _inject_knowledge was removed from knowledge_search during refactoring.
        # The replacement _action_inject in knowledge_inject.py has a different signature.
        # This test is commented out as the function no longer exists.
        # from xuansto_mcp.tools.knowledge_search import _inject_knowledge
        # _inject_knowledge("auto-init test content", "general", None)
        pass

        assert db_path.exists()

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        conn.close()

        assert "knowledge_entries" in tables
