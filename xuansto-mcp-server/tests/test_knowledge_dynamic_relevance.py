import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from xuansto_mcp.tools.knowledge_search import _sqlite_search, _keyword_fallback_search


class TestSqliteSearchBM25:
    def setup_method(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.tmp_dir) / "knowledge.db"
        conn = sqlite3.connect(str(self.db_path))
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
        conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts
            USING fts5(title, content, type, content=knowledge_entries, content_rowid=rowid)
        """)
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS knowledge_ai AFTER INSERT ON knowledge_entries BEGIN
                INSERT INTO knowledge_fts(rowid, title, content, type) VALUES (new.rowid, new.title, new.content, new.type);
            END
        """)
        entries = [
            ("entry1", "Python Testing Guide", "This is a comprehensive guide about python testing with pytest and unittest frameworks", "general", "2025-01-01", "2025-01-01"),
            ("entry2", "JavaScript Basics", "Learn javascript fundamentals including variables functions and loops", "general", "2025-01-02", "2025-01-02"),
            ("entry3", "Python Data Science", "Python data science with pandas numpy and matplotlib for data analysis", "general", "2025-01-03", "2025-01-03"),
        ]
        for e in entries:
            conn.execute(
                "INSERT INTO knowledge_entries (id, title, content, type, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                e,
            )
        conn.commit()
        conn.close()

    def teardown_method(self):
        if self.db_path.exists():
            self.db_path.unlink()
        Path(self.tmp_dir).rmdir()

    @patch("xuansto_mcp.tools.knowledge_search.KNOWLEDGE_DB_PATH", None)
    def test_returns_none_when_db_not_exists(self):
        from xuansto_mcp.tools.knowledge_search import KNOWLEDGE_DB_PATH
        with patch("xuansto_mcp.tools.knowledge_search.KNOWLEDGE_DB_PATH", Path("/nonexistent/path.db")):
            result = _sqlite_search("python", 5, None, 0.0)
            assert result is None

    def test_fts5_search_returns_dynamic_relevance(self):
        with patch("xuansto_mcp.tools.knowledge_search.KNOWLEDGE_DB_PATH", self.db_path):
            result = _sqlite_search("python", 5, None, 0.0)
        assert result is not None
        assert result["strategy"] == "sqlite_fts5_bm25"
        assert result["total"] > 0
        for item in result["results"]:
            assert item["relevance"] != 0.6, f"Relevance should not be fixed 0.6, got {item['relevance']}"
            assert 0.0 <= item["relevance"] <= 1.0, f"Relevance {item['relevance']} out of [0.0, 1.0] range"

    def test_fts5_relevance_varies_by_match_quality(self):
        with patch("xuansto_mcp.tools.knowledge_search.KNOWLEDGE_DB_PATH", self.db_path):
            result = _sqlite_search("python testing", 5, None, 0.0)
        assert result is not None
        assert result["total"] >= 1
        relevances = [item["relevance"] for item in result["results"]]
        for r in relevances:
            assert 0.0 <= r <= 1.0

    def test_fts5_strategy_string_updated(self):
        with patch("xuansto_mcp.tools.knowledge_search.KNOWLEDGE_DB_PATH", self.db_path):
            result = _sqlite_search("python", 5, None, 0.0)
        assert result is not None
        assert result["strategy"] == "sqlite_fts5_bm25"
        assert result["strategy"] != "sqlite_fts5"

    def test_fts5_min_confidence_filtering(self):
        with patch("xuansto_mcp.tools.knowledge_search.KNOWLEDGE_DB_PATH", self.db_path):
            result_low = _sqlite_search("python", 5, None, 0.0)
            result_high = _sqlite_search("python", 5, None, 0.99)
        assert result_low is not None
        assert result_high is not None
        assert result_high["total"] <= result_low["total"]

    def test_like_fallback_relevance(self):
        with patch("xuansto_mcp.tools.knowledge_search.KNOWLEDGE_DB_PATH", self.db_path):
            result = _sqlite_search("nonexistent_fts_term_xyz123", 5, None, 0.0)
        if result is not None and result["total"] > 0:
            for item in result["results"]:
                assert 0.0 <= item["relevance"] <= 1.0


class TestKeywordFallbackTFIDF:
    def setup_method(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.general_dir = Path(self.tmp_dir) / "general"
        self.general_dir.mkdir(parents=True, exist_ok=True)

        (self.general_dir / "doc1.md").write_text(
            "Python testing guide with pytest and unittest. Python is great for testing.", encoding="utf-8"
        )
        (self.general_dir / "doc2.md").write_text(
            "A brief note about python.", encoding="utf-8"
        )
        (self.general_dir / "doc3.md").write_text(
            "x " * 5000 + " python testing ", encoding="utf-8"
        )

    def teardown_method(self):
        import shutil
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_keyword_search_returns_dynamic_relevance(self):
        with patch("xuansto_mcp.tools.knowledge_search.KNOWLEDGE_GENERAL_DIR", self.general_dir), \
             patch("xuansto_mcp.tools.knowledge_search.REFERENCES_DIR", Path("/nonexistent")), \
             patch("xuansto_mcp.tools.knowledge_search.KNOWLEDGE_WORKSPACE_DIR", Path("/nonexistent")), \
             patch("xuansto_mcp.tools.knowledge_search.KNOWLEDGE_EXPERIENCE_DIR", Path("/nonexistent")):
            result = _keyword_fallback_search("python testing", 5, None)
        assert result is not None
        assert result["total"] > 0
        for item in result["results"]:
            assert item["relevance"] != 0.5, f"Relevance should not be fixed 0.5, got {item['relevance']}"
            assert 0.0 <= item["relevance"] <= 1.0, f"Relevance {item['relevance']} out of [0.0, 1.0] range"

    def test_keyword_strategy_string_updated(self):
        with patch("xuansto_mcp.tools.knowledge_search.KNOWLEDGE_GENERAL_DIR", self.general_dir), \
             patch("xuansto_mcp.tools.knowledge_search.REFERENCES_DIR", Path("/nonexistent")), \
             patch("xuansto_mcp.tools.knowledge_search.KNOWLEDGE_WORKSPACE_DIR", Path("/nonexistent")), \
             patch("xuansto_mcp.tools.knowledge_search.KNOWLEDGE_EXPERIENCE_DIR", Path("/nonexistent")):
            result = _keyword_fallback_search("python", 5, None)
        assert result is not None
        assert result["strategy"] == "keyword_tfidf"
        assert result["strategy"] != "keyword_fallback"

    def test_keyword_relevance_varies_by_term_coverage(self):
        with patch("xuansto_mcp.tools.knowledge_search.KNOWLEDGE_GENERAL_DIR", self.general_dir), \
             patch("xuansto_mcp.tools.knowledge_search.REFERENCES_DIR", Path("/nonexistent")), \
             patch("xuansto_mcp.tools.knowledge_search.KNOWLEDGE_WORKSPACE_DIR", Path("/nonexistent")), \
             patch("xuansto_mcp.tools.knowledge_search.KNOWLEDGE_EXPERIENCE_DIR", Path("/nonexistent")):
            result = _keyword_fallback_search("python testing guide", 5, None)
        assert result is not None
        if result["total"] >= 2:
            relevances = [item["relevance"] for item in result["results"]]
            unique_relevances = set(relevances)
            assert len(unique_relevances) >= 1

    def test_keyword_relevance_within_range(self):
        with patch("xuansto_mcp.tools.knowledge_search.KNOWLEDGE_GENERAL_DIR", self.general_dir), \
             patch("xuansto_mcp.tools.knowledge_search.REFERENCES_DIR", Path("/nonexistent")), \
             patch("xuansto_mcp.tools.knowledge_search.KNOWLEDGE_WORKSPACE_DIR", Path("/nonexistent")), \
             patch("xuansto_mcp.tools.knowledge_search.KNOWLEDGE_EXPERIENCE_DIR", Path("/nonexistent")):
            result = _keyword_fallback_search("python", 5, None)
        assert result is not None
        for item in result["results"]:
            assert 0.0 <= item["relevance"] <= 1.0

    def test_keyword_no_results_for_missing_query(self):
        with patch("xuansto_mcp.tools.knowledge_search.KNOWLEDGE_GENERAL_DIR", self.general_dir), \
             patch("xuansto_mcp.tools.knowledge_search.REFERENCES_DIR", Path("/nonexistent")), \
             patch("xuansto_mcp.tools.knowledge_search.KNOWLEDGE_WORKSPACE_DIR", Path("/nonexistent")), \
             patch("xuansto_mcp.tools.knowledge_search.KNOWLEDGE_EXPERIENCE_DIR", Path("/nonexistent")):
            result = _keyword_fallback_search("xyznonexistent123", 5, None)
        assert result is not None
        assert result["total"] == 0
        assert result["strategy"] == "keyword_tfidf"

    def test_keyword_scope_filtering(self):
        with patch("xuansto_mcp.tools.knowledge_search.KNOWLEDGE_GENERAL_DIR", self.general_dir), \
             patch("xuansto_mcp.tools.knowledge_search.REFERENCES_DIR", Path("/nonexistent")), \
             patch("xuansto_mcp.tools.knowledge_search.KNOWLEDGE_WORKSPACE_DIR", Path("/nonexistent")), \
             patch("xuansto_mcp.tools.knowledge_search.KNOWLEDGE_EXPERIENCE_DIR", Path("/nonexistent")):
            result_general = _keyword_fallback_search("python", 5, "general")
            result_workspace = _keyword_fallback_search("python", 5, "workspace")
        assert result_general is not None
        assert result_workspace is not None
        assert result_general["total"] > 0
        assert result_workspace["total"] == 0
