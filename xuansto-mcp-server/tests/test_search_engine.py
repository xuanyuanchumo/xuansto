from __future__ import annotations

import sqlite3
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from xuansto_mcp.core.search_engine import (
    ChromaDBSearchEngine,
    HybridSearchEngine,
    SimpleSearchEngine,
    SQLiteFTSSearchEngine,
    _is_chromadb_available,
    _detect_best_engine,
    set_default_search_engine,
    get_available_backends,
    get_search_engine,
    _SEARCH_ENGINE_REGISTRY,
    SearchResult,
)


def test_is_chromadb_available_returns_bool():
    result = _is_chromadb_available()
    assert isinstance(result, bool)


def test_is_chromadb_available_caches_result():
    import xuansto_mcp.core.search_engine as se_mod
    original = se_mod._CHROMADB_AVAILABLE
    se_mod._CHROMADB_AVAILABLE = None
    try:
        _is_chromadb_available()
        assert se_mod._CHROMADB_AVAILABLE is not None
    finally:
        se_mod._CHROMADB_AVAILABLE = original


def test_sqlite_fts_search_basic(sqlite_fts_db, patch_config):
    import xuansto_mcp.core.search_engine as se_mod
    orig = se_mod.KNOWLEDGE_DB_PATH
    se_mod.KNOWLEDGE_DB_PATH = sqlite_fts_db
    try:
        engine = SQLiteFTSSearchEngine(db_path=sqlite_fts_db)
        results = engine.search("Python", top_k=5)
        assert isinstance(results, list)
        for r in results:
            assert isinstance(r, SearchResult)
            assert 0.0 <= r.relevance <= 1.0
            assert r.match_type in ("fts5_bm25", "keyword")
    finally:
        se_mod.KNOWLEDGE_DB_PATH = orig


def test_sqlite_fts_search_no_db(tmp_path):
    engine = SQLiteFTSSearchEngine(db_path=tmp_path / "nonexistent.db")
    results = engine.search("test", top_k=5)
    assert results == []


def test_sqlite_fts_search_with_min_confidence(sqlite_fts_db, patch_config):
    import xuansto_mcp.core.search_engine as se_mod
    orig = se_mod.KNOWLEDGE_DB_PATH
    se_mod.KNOWLEDGE_DB_PATH = sqlite_fts_db
    try:
        engine = SQLiteFTSSearchEngine(db_path=sqlite_fts_db)
        results = engine.search("Python", top_k=5, filters={"min_confidence": 0.99})
        for r in results:
            assert r.relevance >= 0.99
    finally:
        se_mod.KNOWLEDGE_DB_PATH = orig


def test_sqlite_fts_bm25_score_to_relevance():
    assert SQLiteFTSSearchEngine._bm25_score_to_relevance(0.0) == 0.5
    relevance_high = SQLiteFTSSearchEngine._bm25_score_to_relevance(-20.0)
    assert relevance_high == 1.5 or relevance_high == 1.0
    relevance_low = SQLiteFTSSearchEngine._bm25_score_to_relevance(20.0)
    assert 0.0 <= relevance_low <= 1.0


def test_hybrid_search_engine(sqlite_fts_db, patch_config):
    import xuansto_mcp.core.search_engine as se_mod
    orig_chroma = se_mod.KNOWLEDGE_CHROMA_PATH
    orig_db = se_mod.KNOWLEDGE_DB_PATH
    se_mod.KNOWLEDGE_DB_PATH = sqlite_fts_db
    try:
        with patch.object(ChromaDBSearchEngine, "search", return_value=[]):
            engine = HybridSearchEngine(db_path=sqlite_fts_db)
            results = engine.search("Python", top_k=5)
            assert isinstance(results, list)
    finally:
        se_mod.KNOWLEDGE_CHROMA_PATH = orig_chroma
        se_mod.KNOWLEDGE_DB_PATH = orig_db


def test_hybrid_search_engine_merges_results(sqlite_fts_db, patch_config):
    import xuansto_mcp.core.search_engine as se_mod
    orig_db = se_mod.KNOWLEDGE_DB_PATH
    se_mod.KNOWLEDGE_DB_PATH = sqlite_fts_db
    try:
        semantic_result = SearchResult(source="doc1", content="semantic content", match_type="semantic", relevance=0.9)
        with patch.object(ChromaDBSearchEngine, "search", return_value=[semantic_result]):
            engine = HybridSearchEngine(db_path=sqlite_fts_db)
            results = engine.search("Python", top_k=5)
            assert isinstance(results, list)
            for r in results:
                assert r.match_type == "hybrid"
    finally:
        se_mod.KNOWLEDGE_DB_PATH = orig_db


def test_detect_best_engine_returns_string():
    engine = _detect_best_engine()
    assert isinstance(engine, str)


def test_detect_best_engine_returns_registered():
    engine = _detect_best_engine()
    assert engine in _SEARCH_ENGINE_REGISTRY or engine == "auto"


def test_detect_best_engine_without_chromadb():
    import xuansto_mcp.core.search_engine as se_mod
    orig = se_mod.KNOWLEDGE_DB_PATH
    se_mod.KNOWLEDGE_DB_PATH = Path("/nonexistent_db_path_12345")
    try:
        with patch("xuansto_mcp.core.search_engine._is_chromadb_available", return_value=False):
            engine = _detect_best_engine()
            assert engine == "simple"
    finally:
        se_mod.KNOWLEDGE_DB_PATH = orig


def test_detect_best_engine_with_chromadb_no_db():
    import xuansto_mcp.core.search_engine as se_mod
    orig = se_mod.KNOWLEDGE_DB_PATH
    se_mod.KNOWLEDGE_DB_PATH = Path("/nonexistent_db_path_12345")
    try:
        with patch("xuansto_mcp.core.search_engine._is_chromadb_available", return_value=True):
            engine = _detect_best_engine()
            assert engine == "chromadb"
    finally:
        se_mod.KNOWLEDGE_DB_PATH = orig


def test_detect_best_engine_with_chromadb_and_db(sqlite_fts_db):
    with patch("xuansto_mcp.core.search_engine._is_chromadb_available", return_value=True):
        with patch("xuansto_mcp.core.search_engine.KNOWLEDGE_DB_PATH", sqlite_fts_db):
            engine = _detect_best_engine()
            assert engine == "hybrid"


def test_get_search_engine_auto():
    engine = get_search_engine("auto")
    assert hasattr(engine, "search")


def test_get_search_engine_simple():
    engine = get_search_engine("simple")
    assert isinstance(engine, SimpleSearchEngine)


def test_get_search_engine_sqlite_fts5(sqlite_fts_db, patch_config):
    import xuansto_mcp.core.search_engine as se_mod
    orig = se_mod.KNOWLEDGE_DB_PATH
    se_mod.KNOWLEDGE_DB_PATH = sqlite_fts_db
    try:
        engine = get_search_engine("sqlite_fts5")
        assert isinstance(engine, SQLiteFTSSearchEngine)
    finally:
        se_mod.KNOWLEDGE_DB_PATH = orig


def test_get_search_engine_unknown_falls_back():
    engine = get_search_engine("nonexistent_engine")
    assert isinstance(engine, SimpleSearchEngine)


def test_get_search_engine_hybrid_fallback(sqlite_fts_db, patch_config):
    import xuansto_mcp.core.search_engine as se_mod
    orig_db = se_mod.KNOWLEDGE_DB_PATH
    se_mod.KNOWLEDGE_DB_PATH = sqlite_fts_db
    try:
        with patch("xuansto_mcp.core.search_engine._is_chromadb_available", return_value=False):
            engine = get_search_engine("hybrid")
            assert isinstance(engine, SQLiteFTSSearchEngine)
    finally:
        se_mod.KNOWLEDGE_DB_PATH = orig_db


def test_get_available_backends():
    backends = get_available_backends()
    assert isinstance(backends, list)
    assert "simple" in backends
    for b in backends:
        assert isinstance(b, str)


def test_get_available_backends_with_chromadb():
    with patch("xuansto_mcp.core.search_engine._is_chromadb_available", return_value=True):
        backends = get_available_backends()
        assert "chromadb" in backends
        assert "hybrid" in backends


def test_set_default_search_engine_auto():
    import xuansto_mcp.core.search_engine as se_mod
    original = se_mod._default_engine_name
    try:
        set_default_search_engine("auto")
        assert se_mod._default_engine_name == "auto"
    finally:
        se_mod._default_engine_name = original


def test_set_default_search_engine_invalid():
    import xuansto_mcp.core.search_engine as se_mod
    original = se_mod._default_engine_name
    try:
        set_default_search_engine("nonexistent_engine_xyz")
        assert se_mod._default_engine_name == original
    finally:
        se_mod._default_engine_name = original


def test_simple_search_engine_no_dirs(tmp_path):
    engine = SimpleSearchEngine(search_dirs=[tmp_path / "nonexistent"])
    results = engine.search("test", top_k=5)
    assert results == []


def test_simple_search_engine_with_content(tmp_path):
    search_dir = tmp_path / "knowledge"
    search_dir.mkdir()
    (search_dir / "test.md").write_text("Python testing with pytest is great", encoding="utf-8")
    engine = SimpleSearchEngine(search_dirs=[search_dir])
    results = engine.search("Python", top_k=5)
    assert len(results) >= 1
    assert results[0].match_type == "keyword"


def test_simple_search_engine_with_scope(tmp_path):
    general_dir = tmp_path / "general"
    general_dir.mkdir()
    (general_dir / "doc.md").write_text("general knowledge about Python", encoding="utf-8")
    import xuansto_mcp.core.search_engine as se_mod
    orig_general = se_mod.KNOWLEDGE_GENERAL_DIR
    orig_refs = se_mod.REFERENCES_DIR
    se_mod.KNOWLEDGE_GENERAL_DIR = general_dir
    se_mod.REFERENCES_DIR = tmp_path / "refs"
    try:
        engine = SimpleSearchEngine(search_dirs=[general_dir])
        results = engine.search("Python", top_k=5, filters={"scope": "general"})
        assert isinstance(results, list)
    finally:
        se_mod.KNOWLEDGE_GENERAL_DIR = orig_general
        se_mod.REFERENCES_DIR = orig_refs
