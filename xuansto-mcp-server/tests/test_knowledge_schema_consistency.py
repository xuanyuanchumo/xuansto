import sqlite3
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from xuansto_mcp.tools.knowledge_search import (
    _ensure_knowledge_index,
    _sqlite_search,
)
from xuansto_mcp.core.database import init_db, _CREATE_TABLES_SQL, _FTS5_SQL

_MCP_STANDARD_COLUMNS = {
    "id", "title", "content", "type", "metadata_json", "created_at", "updated_at",
}


def _setup_db(tmp_path: Path) -> Path:
    db_path = tmp_path / "xuansto.db"
    with patch("xuansto_mcp.core.database.DB_PATH", db_path), \
         patch("xuansto_mcp.core.database.WORK_DIR", tmp_path), \
         patch("xuansto_mcp.core.config.WORK_DIR", tmp_path), \
         patch("xuansto_mcp.core.config.KNOWLEDGE_DIR", tmp_path / "knowledge"):
        init_db()
    return db_path


def _insert_test_row(db_path: Path, entry_id: str, title: str, content: str, entry_type: str = "general") -> None:
    conn = sqlite3.connect(str(db_path))
    now = "2026-01-01T00:00:00+00:00"
    conn.execute(
        "INSERT INTO knowledge_entries (id, title, content, type, metadata_json, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (entry_id, title, content, entry_type, "{}", now, now),
    )
    conn.commit()
    conn.close()


@pytest.fixture
def tmp_db(tmp_path):
    return _setup_db(tmp_path)


@pytest.fixture
def patched_db(tmp_path, tmp_db):
    with patch("xuansto_mcp.core.database.DB_PATH", tmp_db):
        yield tmp_db


class TestTableNameConsistency:
    def test_expected_columns_covers_schema(self, tmp_path):
        db_path = _setup_db(tmp_path)
        conn = sqlite3.connect(str(db_path))
        cursor = conn.execute("PRAGMA table_info(knowledge_entries)")
        actual_cols = {row[1] for row in cursor.fetchall()}
        conn.close()
        assert _MCP_STANDARD_COLUMNS.issubset(actual_cols), (
            f"Schema mismatch: _MCP_STANDARD_COLUMNS={_MCP_STANDARD_COLUMNS}, actual={actual_cols}"
        )

    def test_sqlite_search_uses_knowledge_entries(self):
        import inspect
        from xuansto_mcp.tools import knowledge_search as ks

        source = inspect.getsource(ks._sqlite_search)
        assert "knowledge_entries" in source
        assert "knowledge_items" not in source

    def test_sqlite_search_uses_knowledge_fts_for_match(self):
        import inspect
        from xuansto_mcp.tools import knowledge_search as ks

        source = inspect.getsource(ks._sqlite_search)
        assert "knowledge_fts" in source
        assert "JOIN knowledge_fts" in source

    def test_init_db_creates_knowledge_entries(self, tmp_path):
        db_path = _setup_db(tmp_path)
        conn = sqlite3.connect(str(db_path))
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='knowledge_entries'")
        assert cursor.fetchone() is not None
        conn.close()

    def test_fts5_references_knowledge_entries(self):
        import inspect
        from xuansto_mcp.core import database as db

        source = inspect.getsource(db.init_db)
        assert "knowledge_entries" in source


class TestFTS5Search:
    def test_fts5_search_after_index_creation(self, patched_db):
        _insert_test_row(patched_db, "test-1", "Python Testing Guide", "How to write unit tests in Python with pytest")
        _insert_test_row(patched_db, "test-2", "JavaScript Basics", "Introduction to JavaScript programming language")

        result = _sqlite_search("Python testing", 5, None, 0.0)
        assert result is not None
        assert result["total"] >= 1

    def test_fts5_search_returns_correct_fields(self, patched_db):
        _insert_test_row(patched_db, "entry-1", "Test Title", "Searchable content about databases")

        result = _sqlite_search("databases", 5, None, 0.0)
        assert result is not None
        assert result["total"] >= 1
        item = result["results"][0]
        assert "source" in item
        assert "content" in item
        assert "relevance" in item
        assert item["match_type"] == "fts5"

    def test_fts5_like_fallback_when_no_fts_match(self, patched_db):
        _insert_test_row(patched_db, "entry-fb", "Fallback Test", "Some unique content for fallback search test")

        result = _sqlite_search("unique content for fallback", 5, None, 0.0)
        assert result is not None
        assert result["total"] >= 1

    def test_fts5_search_empty_db(self, patched_db):
        result = _sqlite_search("nonexistent", 5, None, 0.0)
        assert result is not None
        assert result["total"] == 0

    def test_fts5_search_nonexistent_db(self, tmp_path):
        nonexistent = tmp_path / "does_not_exist" / "xuansto.db"
        with patch("xuansto_mcp.core.database.DB_PATH", nonexistent):
            result = _sqlite_search("query", 5, None, 0.0)
        assert result is None


class TestIdempotency:
    def test_init_db_called_twice_does_not_fail(self, tmp_path):
        db_path = tmp_path / "xuansto.db"
        with patch("xuansto_mcp.core.database.DB_PATH", db_path), \
             patch("xuansto_mcp.core.database.WORK_DIR", tmp_path), \
             patch("xuansto_mcp.core.config.WORK_DIR", tmp_path), \
             patch("xuansto_mcp.core.config.KNOWLEDGE_DIR", tmp_path / "knowledge"):
            init_db()
            init_db()

        assert db_path.exists()
        conn = sqlite3.connect(str(db_path))
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='knowledge_entries'")
        assert cursor.fetchone() is not None
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='knowledge_fts'")
        assert cursor.fetchone() is not None
        conn.close()

    def test_init_db_preserves_data_on_second_call(self, tmp_path):
        db_path = tmp_path / "xuansto.db"
        with patch("xuansto_mcp.core.database.DB_PATH", db_path), \
             patch("xuansto_mcp.core.database.WORK_DIR", tmp_path), \
             patch("xuansto_mcp.core.config.WORK_DIR", tmp_path), \
             patch("xuansto_mcp.core.config.KNOWLEDGE_DIR", tmp_path / "knowledge"):
            init_db()

        _insert_test_row(db_path, "persist-1", "Persistent", "This data should survive idempotent calls")

        with patch("xuansto_mcp.core.database.DB_PATH", db_path), \
             patch("xuansto_mcp.core.database.WORK_DIR", tmp_path), \
             patch("xuansto_mcp.core.config.WORK_DIR", tmp_path), \
             patch("xuansto_mcp.core.config.KNOWLEDGE_DIR", tmp_path / "knowledge"):
            init_db()

        conn = sqlite3.connect(str(db_path))
        cursor = conn.execute("SELECT id FROM knowledge_entries WHERE id='persist-1'")
        assert cursor.fetchone() is not None
        conn.close()

    def test_init_db_recreates_on_wrong_schema(self, tmp_path):
        db_path = tmp_path / "xuansto.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute("""
            CREATE TABLE knowledge_entries (
                id TEXT PRIMARY KEY,
                content TEXT
            )
        """)
        conn.commit()
        conn.close()

        with patch("xuansto_mcp.core.database.DB_PATH", db_path), \
             patch("xuansto_mcp.core.database.WORK_DIR", tmp_path), \
             patch("xuansto_mcp.core.config.WORK_DIR", tmp_path), \
             patch("xuansto_mcp.core.config.KNOWLEDGE_DIR", tmp_path / "knowledge"):
            init_db()

        conn = sqlite3.connect(str(db_path))
        cursor = conn.execute("PRAGMA table_info(knowledge_entries)")
        cols = {row[1] for row in cursor.fetchall()}
        assert "title" in cols
        assert "created_at" in cols
        assert "updated_at" in cols
        conn.close()

    def test_init_db_creates_update_trigger(self, tmp_path):
        db_path = _setup_db(tmp_path)
        conn = sqlite3.connect(str(db_path))
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='trigger' AND name='knowledge_entries_au'")
        assert cursor.fetchone() is not None
        conn.close()

    def test_fts5_index_syncs_on_update(self, patched_db):
        _insert_test_row(patched_db, "upd-1", "Original Title", "Original content about apples")

        result_before = _sqlite_search("bananas", 5, None, 0.0)
        assert result_before is not None
        assert result_before["total"] == 0

        conn = sqlite3.connect(str(patched_db))
        conn.execute(
            "UPDATE knowledge_entries SET content='Updated content about bananas', updated_at=? WHERE id=?",
            ("2026-01-02T00:00:00+00:00", "upd-1"),
        )
        conn.commit()
        conn.close()

        result_after = _sqlite_search("bananas", 5, None, 0.0)
        assert result_after is not None
        assert result_after["total"] >= 1

    def test_init_db_handles_empty_db_file(self, tmp_path):
        db_path = tmp_path / "xuansto.db"
        db_path.touch()

        with patch("xuansto_mcp.core.database.DB_PATH", db_path), \
             patch("xuansto_mcp.core.database.WORK_DIR", tmp_path), \
             patch("xuansto_mcp.core.config.WORK_DIR", tmp_path), \
             patch("xuansto_mcp.core.config.KNOWLEDGE_DIR", tmp_path / "knowledge"):
            init_db()

        conn = sqlite3.connect(str(db_path))
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='knowledge_entries'")
        assert cursor.fetchone() is not None
        conn.close()
