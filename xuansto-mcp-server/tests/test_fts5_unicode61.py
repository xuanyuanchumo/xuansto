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
from xuansto_mcp.core.database import init_db, _FTS5_SQL, _CREATE_TABLES_SQL


def _setup_db(tmp_path: Path) -> Path:
    db_path = tmp_path / "xuansto.db"
    with patch("xuansto_mcp.core.database.DB_PATH", db_path), \
         patch("xuansto_mcp.core.database.WORK_DIR", tmp_path), \
         patch("xuansto_mcp.core.config.WORK_DIR", tmp_path), \
         patch("xuansto_mcp.core.config.KNOWLEDGE_DIR", tmp_path / "knowledge"):
        init_db()
    return db_path


def _insert_row(db_path: Path, entry_id: str, title: str, content: str, entry_type: str = "general") -> None:
    conn = sqlite3.connect(str(db_path))
    now = "2026-01-01T00:00:00+00:00"
    conn.execute(
        "INSERT INTO knowledge_entries (id, title, content, type, scope, category, summary, metadata_json, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (entry_id, title, content, entry_type, "general", "uncategorized", title, "{}", now, now),
    )
    conn.commit()
    conn.close()


def _create_old_fts5_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
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
    conn.execute("""
        CREATE TRIGGER IF NOT EXISTS knowledge_ad AFTER DELETE ON knowledge_entries BEGIN
            INSERT INTO knowledge_fts(knowledge_fts, rowid, title, content, type) VALUES('delete', old.rowid, old.title, old.content, old.type);
        END
    """)
    conn.execute("""
        CREATE TRIGGER IF NOT EXISTS knowledge_au AFTER UPDATE ON knowledge_entries BEGIN
            INSERT INTO knowledge_fts(knowledge_fts, rowid, title, content, type) VALUES('delete', old.rowid, old.title, old.content, old.type);
            INSERT INTO knowledge_fts(rowid, title, content, type) VALUES (new.rowid, new.title, new.content, new.type);
        END
    """)
    conn.commit()
    conn.close()


class TestFTS5Unicode61Tokenizer:
    def test_new_db_uses_unicode61(self, tmp_path):
        db_path = _setup_db(tmp_path)
        conn = sqlite3.connect(str(db_path))
        cursor = conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='knowledge_fts'")
        row = cursor.fetchone()
        conn.close()
        assert row is not None
        create_sql = row[0]
        assert "unicode61" in create_sql

    def test_fts5_indexes_summary_type_category(self, tmp_path):
        db_path = _setup_db(tmp_path)
        conn = sqlite3.connect(str(db_path))
        cursor = conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='knowledge_fts'")
        create_sql = cursor.fetchone()[0]
        conn.close()
        assert "summary" in create_sql
        assert "type" in create_sql
        assert "category" in create_sql
        assert "unicode61" in create_sql

    def test_fts5_vocab_contains_tokens(self, tmp_path):
        db_path = _setup_db(tmp_path)
        _insert_row(db_path, "vocab-1", "Database Guide", "How to use SQL databases effectively")
        _insert_row(db_path, "vocab-2", "数据库优化", "关于SQL查询性能优化")
        conn = sqlite3.connect(str(db_path))
        conn.execute("CREATE VIRTUAL TABLE fts_vocab USING fts5vocab(knowledge_fts, 'instance')")
        cursor = conn.execute("SELECT term FROM fts_vocab ORDER BY term")
        terms = [r[0] for r in cursor.fetchall()]
        conn.close()
        assert len(terms) > 0


class TestFTS5Migration:
    def test_init_db_replaces_old_fts5_with_unicode61(self, tmp_path):
        db_path = tmp_path / "xuansto.db"
        _create_old_fts5_db(db_path)

        conn = sqlite3.connect(str(db_path))
        cursor = conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='knowledge_fts'")
        old_sql = cursor.fetchone()[0]
        assert "unicode61" not in old_sql
        conn.close()

        with patch("xuansto_mcp.core.database.DB_PATH", db_path), \
             patch("xuansto_mcp.core.database.WORK_DIR", tmp_path), \
             patch("xuansto_mcp.core.config.WORK_DIR", tmp_path), \
             patch("xuansto_mcp.core.config.KNOWLEDGE_DIR", tmp_path / "knowledge"):
            init_db()

        conn = sqlite3.connect(str(db_path))
        cursor = conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='knowledge_entries'")
        new_table_sql = cursor.fetchone()[0]
        assert "scope" in new_table_sql
        assert "category" in new_table_sql
        conn.close()

    def test_init_db_creates_proper_schema_from_scratch(self, tmp_path):
        db_path = _setup_db(tmp_path)
        conn = sqlite3.connect(str(db_path))
        cursor = conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='knowledge_fts'")
        create_sql = cursor.fetchone()[0]
        assert "unicode61" in create_sql
        assert "summary" in create_sql
        conn.close()

    def test_migration_idempotent(self, tmp_path):
        db_path = _setup_db(tmp_path)

        with patch("xuansto_mcp.core.database.DB_PATH", db_path), \
             patch("xuansto_mcp.core.database.WORK_DIR", tmp_path), \
             patch("xuansto_mcp.core.config.WORK_DIR", tmp_path), \
             patch("xuansto_mcp.core.config.KNOWLEDGE_DIR", tmp_path / "knowledge"):
            init_db()

        conn = sqlite3.connect(str(db_path))
        cursor = conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='knowledge_fts'")
        create_sql = cursor.fetchone()[0]
        assert "unicode61" in create_sql

        cursor = conn.execute("SELECT count(*) FROM sqlite_master WHERE type='trigger' AND name LIKE 'knowledge_entries_%'")
        trigger_count = cursor.fetchone()[0]
        assert trigger_count == 3
        conn.close()

    def test_migration_drops_old_triggers(self, tmp_path):
        db_path = tmp_path / "xuansto.db"
        _create_old_fts5_db(db_path)

        conn = sqlite3.connect(str(db_path))
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='trigger' AND name LIKE 'knowledge_%'")
        old_triggers = {row[0] for row in cursor.fetchall()}
        assert "knowledge_ai" in old_triggers
        conn.close()

        with patch("xuansto_mcp.core.database.DB_PATH", db_path), \
             patch("xuansto_mcp.core.database.WORK_DIR", tmp_path), \
             patch("xuansto_mcp.core.config.WORK_DIR", tmp_path), \
             patch("xuansto_mcp.core.config.KNOWLEDGE_DIR", tmp_path / "knowledge"):
            init_db()

        conn = sqlite3.connect(str(db_path))
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='trigger' AND name LIKE 'knowledge_entries_%'")
        new_triggers = {row[0] for row in cursor.fetchall()}
        assert "knowledge_entries_ai" in new_triggers
        assert "knowledge_entries_au" in new_triggers
        assert "knowledge_entries_ad" in new_triggers
        conn.close()


class TestFTS5Rebuild:
    def test_rebuild_after_manual_data_insert(self, tmp_path):
        db_path = _setup_db(tmp_path)
        _insert_row(db_path, "rebuild-1", "Rebuild Title", "Rebuild content for testing")

        conn = sqlite3.connect(str(db_path))
        conn.execute("INSERT INTO knowledge_fts(knowledge_fts) VALUES('rebuild')")
        conn.commit()
        conn.close()

        with patch("xuansto_mcp.core.database.DB_PATH", db_path):
            result = _sqlite_search("Rebuild", 5, None, 0.0)

        assert result is not None
        assert result["total"] >= 1

    def test_init_db_creates_unicode61_fts5(self, tmp_path):
        db_path = _setup_db(tmp_path)
        conn = sqlite3.connect(str(db_path))
        cursor = conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='knowledge_fts'")
        row = cursor.fetchone()
        assert row is not None
        create_sql = row[0]
        assert "unicode61" in create_sql
        conn.close()


class TestUnicodeTextSearch:
    def test_english_fts5_search(self, tmp_path):
        db_path = _setup_db(tmp_path)
        _insert_row(db_path, "en-1", "Python Testing Guide", "How to write unit tests in Python with pytest")
        _insert_row(db_path, "en-2", "JavaScript Basics", "Introduction to JavaScript programming language")

        with patch("xuansto_mcp.core.database.DB_PATH", db_path):
            result = _sqlite_search("Python", 5, None, 0.0)

        assert result is not None
        assert result["total"] >= 1

    def test_chinese_like_fallback_in_content(self, tmp_path):
        db_path = _setup_db(tmp_path)
        _insert_row(db_path, "zh-1", "数据库优化策略", "关于SQL查询性能优化的详细说明")

        with patch("xuansto_mcp.core.database.DB_PATH", db_path):
            result = _sqlite_search("性能优化", 5, None, 0.0)

        assert result is not None
        assert result["total"] >= 1

    def test_chinese_like_fallback_in_title(self, tmp_path):
        db_path = _setup_db(tmp_path)
        _insert_row(db_path, "zh-2", "数据库优化策略", "关于SQL查询的说明")

        with patch("xuansto_mcp.core.database.DB_PATH", db_path):
            result = _sqlite_search("数据库", 5, None, 0.0)

        assert result is not None
        assert result["total"] >= 1

    def test_mixed_chinese_english_search(self, tmp_path):
        db_path = _setup_db(tmp_path)
        _insert_row(db_path, "mix-1", "React组件开发", "使用React框架开发可复用的UI组件")

        with patch("xuansto_mcp.core.database.DB_PATH", db_path):
            result = _sqlite_search("React", 5, None, 0.0)

        assert result is not None
        assert result["total"] >= 1

    def test_unicode61_search_on_new_db(self, tmp_path):
        db_path = _setup_db(tmp_path)
        _insert_row(db_path, "new-zh-1", "中文测试", "这是一段中文内容用于测试搜索功能")

        with patch("xuansto_mcp.core.database.DB_PATH", db_path):
            result = _sqlite_search("中文", 5, None, 0.0)

        assert result is not None
        assert result["total"] >= 1
