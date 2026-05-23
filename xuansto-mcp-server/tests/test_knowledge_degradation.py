from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from xuansto_mcp.core.search_engine import (
    ChromaDBSearchEngine,
    SimpleSearchEngine,
    SQLiteFTSSearchEngine,
    SearchResult,
    get_search_engine,
    register_search_engine,
    set_default_search_engine,
    get_available_backends,
    _SEARCH_ENGINE_REGISTRY,
)
from xuansto_mcp.core.errors import make_success_response, make_error_response, ERR_VALIDATION


@pytest.fixture
def tmp_knowledge_dir(tmp_path):
    kdir = tmp_path / "knowledge"
    kdir.mkdir()
    (kdir / "general").mkdir()
    (kdir / "workspace").mkdir()
    (kdir / "experience").mkdir()
    idx = kdir / "index"
    idx.mkdir()
    return kdir


@pytest.fixture
def tmp_db_path(tmp_knowledge_dir):
    return tmp_knowledge_dir / "index" / "knowledge.db"


@pytest.fixture
def tmp_chroma_path(tmp_knowledge_dir):
    return tmp_knowledge_dir / "index" / "chroma_db"


@pytest.fixture
def sqlite_db_with_data(tmp_db_path):
    conn = sqlite3.connect(str(tmp_db_path))
    conn.execute(
        "CREATE TABLE IF NOT EXISTS knowledge_entries "
        "(id TEXT PRIMARY KEY, title TEXT NOT NULL, content TEXT NOT NULL, "
        "type TEXT DEFAULT 'general', metadata_json TEXT DEFAULT '{}', "
        "created_at TEXT NOT NULL, updated_at TEXT NOT NULL)"
    )
    conn.execute(
        "CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts "
        "USING fts5(content, title, type, content=knowledge_entries, content_rowid=rowid, tokenize='unicode61')"
    )
    conn.execute(
        "CREATE TRIGGER IF NOT EXISTS knowledge_ai AFTER INSERT ON knowledge_entries BEGIN "
        "INSERT INTO knowledge_fts(rowid, content, title, type) VALUES (new.rowid, new.content, new.title, new.type); END"
    )
    now = "2025-01-01T00:00:00"
    conn.executemany(
        "INSERT OR IGNORE INTO knowledge_entries (id, title, content, type, metadata_json, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        [
            ("doc1", "Python Testing", "pytest is a great testing framework for Python", "general", "{}", now, now),
            ("doc2", "FastAPI Guide", "FastAPI is a modern web framework for building APIs", "general", "{}", now, now),
            ("doc3", "MCP Protocol", "Model Context Protocol enables LLM tool integration", "general", "{}", now, now),
        ],
    )
    conn.execute("INSERT INTO knowledge_fts(knowledge_fts) VALUES('rebuild')")
    conn.commit()
    conn.close()
    return tmp_db_path


@pytest.fixture
def keyword_files(tmp_knowledge_dir):
    general = tmp_knowledge_dir / "general"
    f1 = general / "test_doc.md"
    f1.write_text("This document describes integration testing with pytest framework", encoding="utf-8")
    f2 = general / "api_doc.md"
    f2.write_text("FastAPI provides automatic OpenAPI documentation generation", encoding="utf-8")
    return general


class TestKnowledgeSearchRetrieve:
    @pytest.mark.asyncio
    async def test_retrieve_action_with_sqlite(self, sqlite_db_with_data, tmp_chroma_path):
        with patch("xuansto_mcp.tools.knowledge_search.KNOWLEDGE_DB_PATH", sqlite_db_with_data):
            with patch("xuansto_mcp.tools.knowledge_search.KNOWLEDGE_CHROMA_PATH", tmp_chroma_path):
                with patch("xuansto_mcp.tools.knowledge_search._ensure_knowledge_index"):
                    with patch("xuansto_mcp.tools.knowledge_search.get_search_engine") as mock_get:
                        mock_engine = MagicMock()
                        mock_engine.search.return_value = [
                            SearchResult(source="doc1", content="pytest testing", match_type="fts5_bm25", relevance=0.8),
                        ]
                        mock_get.return_value = mock_engine
                        captured = {}
                        def mock_tool_decorator(**dkwargs):
                            def dec(fn):
                                captured["fn"] = fn
                                return fn
                            return dec
                        mcp_mock = MagicMock()
                        mcp_mock.tool = mock_tool_decorator
                        from xuansto_mcp.tools.knowledge_search import register
                        register(mcp_mock)
                        result = await captured["fn"](action="retrieve", query="pytest", search_type="keyword_only")
                        assert result["error"] is False

    @pytest.mark.asyncio
    async def test_inject_action_returns_validation_error(self):
        captured = {}
        def mock_tool_decorator(**dkwargs):
            def dec(fn):
                captured["fn"] = fn
                return fn
            return dec
        mcp_mock = MagicMock()
        mcp_mock.tool = mock_tool_decorator
        from xuansto_mcp.tools.knowledge_search import register
        register(mcp_mock)
        result = await captured["fn"](action="inject", query="test")
        assert result["error"] is True
        assert result["error_code"] == ERR_VALIDATION

    @pytest.mark.asyncio
    async def test_precipitate_action_returns_validation_error(self):
        captured = {}
        def mock_tool_decorator(**dkwargs):
            def dec(fn):
                captured["fn"] = fn
                return fn
            return dec
        mcp_mock = MagicMock()
        mcp_mock.tool = mock_tool_decorator
        from xuansto_mcp.tools.knowledge_search import register
        register(mcp_mock)
        result = await captured["fn"](action="precipitate", query="test")
        assert result["error"] is True


class TestKnowledgeInjectActions:
    @pytest.mark.asyncio
    async def test_inject_action_requires_topics(self):
        captured = {}
        def mock_tool_decorator(**dkwargs):
            def dec(fn):
                captured["fn"] = fn
                return fn
            return dec
        mcp_mock = MagicMock()
        mcp_mock.tool = mock_tool_decorator
        from xuansto_mcp.tools.knowledge_inject import register
        register(mcp_mock)
        result = await captured["fn"](action="inject")
        assert result["error"] is True

    @pytest.mark.asyncio
    async def test_precipitate_action_requires_fields(self):
        captured = {}
        def mock_tool_decorator(**dkwargs):
            def dec(fn):
                captured["fn"] = fn
                return fn
            return dec
        mcp_mock = MagicMock()
        mcp_mock.tool = mock_tool_decorator
        from xuansto_mcp.tools.knowledge_inject import register
        register(mcp_mock)
        result = await captured["fn"](action="precipitate")
        assert result["error"] is True

    @pytest.mark.asyncio
    async def test_add_action_writes_file(self, tmp_knowledge_dir, tmp_db_path, tmp_chroma_path):
        with patch("xuansto_mcp.tools.knowledge_inject.KNOWLEDGE_GENERAL_DIR", tmp_knowledge_dir / "general"):
            with patch("xuansto_mcp.tools.knowledge_inject.KNOWLEDGE_WORKSPACE_DIR", tmp_knowledge_dir / "workspace"):
                with patch("xuansto_mcp.tools.knowledge_inject.KNOWLEDGE_EXPERIENCE_DIR", tmp_knowledge_dir / "experience"):
                    with patch("xuansto_mcp.tools.knowledge_inject.KNOWLEDGE_DB_PATH", tmp_db_path):
                        with patch("xuansto_mcp.tools.knowledge_inject.KNOWLEDGE_CHROMA_PATH", tmp_chroma_path):
                            captured = {}
                            def mock_tool_decorator(**dkwargs):
                                def dec(fn):
                                    captured["fn"] = fn
                                    return fn
                                return dec
                            mcp_mock = MagicMock()
                            mcp_mock.tool = mock_tool_decorator
                            from xuansto_mcp.tools.knowledge_inject import register
                            register(mcp_mock)
                            result = await captured["fn"](action="add", title="Test Title", content="Test content body", scope="general")
                            assert result["error"] is False
                            assert result["data"]["title"] == "Test Title"


class TestSearchEngineFallback:
    def test_chromadb_search_returns_empty_on_import_error(self, tmp_chroma_path):
        engine = ChromaDBSearchEngine(tmp_chroma_path)
        with patch.dict("sys.modules", {"chromadb": None}):
            results = engine.search("test query")
            assert results == []

    def test_sqlite_fts_search_with_data(self, sqlite_db_with_data):
        engine = SQLiteFTSSearchEngine(sqlite_db_with_data)
        results = engine.search("pytest")
        assert len(results) >= 1
        assert any("pytest" in r.content.lower() or "testing" in r.content.lower() for r in results)

    def test_sqlite_fts_search_empty_db(self, tmp_db_path):
        conn = sqlite3.connect(str(tmp_db_path))
        conn.execute("CREATE TABLE IF NOT EXISTS knowledge_entries (id TEXT PRIMARY KEY, title TEXT, content TEXT)")
        conn.commit()
        conn.close()
        engine = SQLiteFTSSearchEngine(tmp_db_path)
        results = engine.search("nonexistent")
        assert results == []

    def test_simple_keyword_search(self, keyword_files):
        engine = SimpleSearchEngine(search_dirs=[keyword_files])
        results = engine.search("pytest")
        assert len(results) >= 1
        assert results[0].match_type == "keyword"

    def test_simple_search_no_results(self, tmp_knowledge_dir):
        engine = SimpleSearchEngine(search_dirs=[tmp_knowledge_dir / "general"])
        results = engine.search("zzzznonexistentxyz")
        assert results == []

    def test_search_engine_registry_has_all_backends(self):
        assert "chromadb" in _SEARCH_ENGINE_REGISTRY
        assert "sqlite_fts5" in _SEARCH_ENGINE_REGISTRY
        assert "simple" in _SEARCH_ENGINE_REGISTRY
        assert "hybrid" in _SEARCH_ENGINE_REGISTRY

    def test_get_search_engine_simple(self):
        engine = get_search_engine("simple")
        assert isinstance(engine, SimpleSearchEngine)

    def test_get_search_engine_unknown_falls_back(self):
        engine = get_search_engine("nonexistent_backend")
        assert isinstance(engine, SimpleSearchEngine)

    def test_register_custom_search_engine(self):
        class CustomEngine:
            def search(self, query, top_k=5, filters=None):
                return []
        register_search_engine("custom_test", CustomEngine)
        engine = get_search_engine("custom_test")
        assert isinstance(engine, CustomEngine)


class TestChromaDBUnavailableDegradation:
    def test_chromadb_unavailable_falls_to_sqlite(self, sqlite_db_with_data):
        with patch("xuansto_mcp.core.search_engine._is_chromadb_available", return_value=False):
            engine = get_search_engine("chromadb")
            assert isinstance(engine, SQLiteFTSSearchEngine)

    def test_chromadb_unavailable_falls_to_simple(self, tmp_knowledge_dir):
        with patch("xuansto_mcp.core.search_engine._is_chromadb_available", return_value=False):
            with patch("xuansto_mcp.core.search_engine.KNOWLEDGE_DB_PATH", tmp_knowledge_dir / "nonexistent"):
                engine = get_search_engine("chromadb")
                assert isinstance(engine, SQLiteFTSSearchEngine) or isinstance(engine, SimpleSearchEngine)

    def test_search_result_dataclass(self):
        result = SearchResult(source="test", content="hello", match_type="keyword", relevance=0.9)
        assert result.source == "test"
        assert result.relevance == 0.9

    def test_bm25_score_conversion(self):
        relevance = SQLiteFTSSearchEngine._bm25_score_to_relevance(-10.0)
        assert 0.0 <= relevance <= 1.0
        relevance_zero = SQLiteFTSSearchEngine._bm25_score_to_relevance(0.0)
        assert relevance_zero == 0.5
