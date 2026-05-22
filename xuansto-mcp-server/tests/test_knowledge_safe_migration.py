from __future__ import annotations

import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest


_MCP_STANDARD_COLUMNS = {"id", "title", "content", "type", "metadata_json", "created_at", "updated_at"}


def _create_mcp_table(conn: sqlite3.Connection) -> None:
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
    conn.commit()


def _create_ks_table(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS knowledge_entries (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            scope TEXT DEFAULT 'general',
            tags TEXT DEFAULT '[]',
            confidence REAL DEFAULT 0.6,
            source_path TEXT,
            category TEXT DEFAULT 'uncategorized',
            summary TEXT,
            status TEXT DEFAULT 'active',
            content_hash TEXT,
            type TEXT DEFAULT 'unknown',
            metadata_json TEXT DEFAULT '{}',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    conn.commit()


def _insert_ks_row(conn: sqlite3.Connection, entry_id: str = "ks-001") -> None:
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT INTO knowledge_entries "
        "(id, title, content, scope, tags, confidence, category, status, type, metadata_json, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (entry_id, "KS Title", "KS Content", "project", "['tag1']", 0.9, "coding", "active", "tip", "{}", now, now),
    )
    conn.commit()


def _get_column_names(conn: sqlite3.Connection) -> set[str]:
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(knowledge_entries)")
    return {row[1] for row in cursor.fetchall()}


def _setup_temp_knowledge_dirs(tmp_path: Path) -> dict[str, Path]:
    knowledge_dir = tmp_path / "knowledge"
    index_dir = knowledge_dir / "index"
    general_dir = knowledge_dir / "general"
    workspace_dir = knowledge_dir / "workspace"
    experience_dir = knowledge_dir / "experience"
    for d in [index_dir, general_dir, workspace_dir, experience_dir]:
        d.mkdir(parents=True, exist_ok=True)
    db_path = index_dir / "knowledge.db"
    return {
        "knowledge_dir": knowledge_dir,
        "index_dir": index_dir,
        "db_path": db_path,
        "general_dir": general_dir,
        "workspace_dir": workspace_dir,
        "experience_dir": experience_dir,
    }


def _run_ensure_knowledge_index(dirs: dict[str, Path]) -> None:
    from xuansto_mcp.tools.knowledge_search import _ensure_knowledge_index
    with patch("xuansto_mcp.core.config.KNOWLEDGE_DIR", dirs["knowledge_dir"]):
        _ensure_knowledge_index()


def _run_inject_knowledge(dirs: dict[str, Path], content: str = "test content", knowledge_type: str = "general") -> dict:
    from xuansto_mcp.tools.knowledge_search import _inject_knowledge
    with patch("xuansto_mcp.tools.knowledge_search.KNOWLEDGE_DB_PATH", dirs["db_path"]), \
         patch("xuansto_mcp.tools.knowledge_search.KNOWLEDGE_GENERAL_DIR", dirs["general_dir"]), \
         patch("xuansto_mcp.tools.knowledge_search.KNOWLEDGE_WORKSPACE_DIR", dirs["workspace_dir"]), \
         patch("xuansto_mcp.tools.knowledge_search.KNOWLEDGE_EXPERIENCE_DIR", dirs["experience_dir"]):
        return _inject_knowledge(content, knowledge_type, None)


class TestSchemaMigrationNonDestructive:
    def test_existing_data_preserved_after_migration(self, tmp_path: Path) -> None:
        dirs = _setup_temp_knowledge_dirs(tmp_path)
        db_path = dirs["db_path"]

        conn = sqlite3.connect(str(db_path))
        _create_ks_table(conn)
        _insert_ks_row(conn, "ks-001")
        _insert_ks_row(conn, "ks-002")
        conn.close()

        _run_ensure_knowledge_index(dirs)

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM knowledge_entries WHERE id LIKE 'ks-%'")
        count = cursor.fetchone()[0]
        conn.close()

        assert count == 2, f"Expected 2 KS rows preserved, got {count}"

    def test_missing_mcp_columns_added_via_alter(self, tmp_path: Path) -> None:
        dirs = _setup_temp_knowledge_dirs(tmp_path)
        db_path = dirs["db_path"]

        conn = sqlite3.connect(str(db_path))
        conn.execute("""
            CREATE TABLE knowledge_entries (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                content TEXT NOT NULL
            )
        """)
        conn.execute(
            "INSERT INTO knowledge_entries (id, title, content) VALUES (?, ?, ?)",
            ("row-1", "Title 1", "Content 1"),
        )
        conn.commit()
        conn.close()

        _run_ensure_knowledge_index(dirs)

        conn = sqlite3.connect(str(db_path))
        cols = _get_column_names(conn)
        conn.close()

        assert _MCP_STANDARD_COLUMNS.issubset(cols), f"Missing columns after migration: {_MCP_STANDARD_COLUMNS - cols}"

    def test_no_drop_table_executed(self, tmp_path: Path) -> None:
        dirs = _setup_temp_knowledge_dirs(tmp_path)
        db_path = dirs["db_path"]

        conn = sqlite3.connect(str(db_path))
        _create_ks_table(conn)
        _insert_ks_row(conn, "ks-preserve")
        conn.close()

        _run_ensure_knowledge_index(dirs)

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM knowledge_entries WHERE id = 'ks-preserve'")
        row = cursor.fetchone()
        conn.close()

        assert row is not None, "DROP TABLE was executed - existing data was destroyed!"

    def test_extra_ks_columns_survive_migration(self, tmp_path: Path) -> None:
        dirs = _setup_temp_knowledge_dirs(tmp_path)
        db_path = dirs["db_path"]

        conn = sqlite3.connect(str(db_path))
        _create_ks_table(conn)
        _insert_ks_row(conn, "ks-extra")
        conn.close()

        _run_ensure_knowledge_index(dirs)

        conn = sqlite3.connect(str(db_path))
        cols = _get_column_names(conn)
        conn.close()

        ks_extra = {"scope", "tags", "confidence", "category", "summary", "status", "content_hash", "source_path"}
        for col in ks_extra:
            assert col in cols, f"KS column '{col}' was lost during migration"


class TestInjectWithStandardColumns:
    def test_insert_uses_only_standard_columns_on_mcp_table(self, tmp_path: Path) -> None:
        dirs = _setup_temp_knowledge_dirs(tmp_path)
        db_path = dirs["db_path"]

        conn = sqlite3.connect(str(db_path))
        _create_mcp_table(conn)
        conn.close()

        _run_ensure_knowledge_index(dirs)
        result = _run_inject_knowledge(dirs, "hello world", "general")

        assert result["indexed"] is True

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT content, type FROM knowledge_entries WHERE id = ?", (result["injected_id"],))
        row = cursor.fetchone()
        conn.close()

        assert row is not None
        assert row[0] == "hello world"
        assert row[1] == "general"

    def test_insert_works_on_ks_table_with_extra_columns(self, tmp_path: Path) -> None:
        dirs = _setup_temp_knowledge_dirs(tmp_path)
        db_path = dirs["db_path"]

        conn = sqlite3.connect(str(db_path))
        _create_ks_table(conn)
        _insert_ks_row(conn, "ks-existing")
        conn.close()

        _run_ensure_knowledge_index(dirs)
        result = _run_inject_knowledge(dirs, "injected content", "workspace")

        assert result["indexed"] is True

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT content, type FROM knowledge_entries WHERE id = ?", (result["injected_id"],))
        row = cursor.fetchone()
        cursor.execute("SELECT COUNT(*) FROM knowledge_entries WHERE id = 'ks-existing'")
        ks_count = cursor.fetchone()[0]
        conn.close()

        assert row is not None
        assert row[0] == "injected content"
        assert ks_count == 1, "KS existing data was lost after inject"

    def test_insert_on_partial_schema(self, tmp_path: Path) -> None:
        dirs = _setup_temp_knowledge_dirs(tmp_path)
        db_path = dirs["db_path"]

        conn = sqlite3.connect(str(db_path))
        conn.execute("""
            CREATE TABLE knowledge_entries (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                scope TEXT DEFAULT 'general',
                tags TEXT DEFAULT '[]'
            )
        """)
        conn.execute(
            "INSERT INTO knowledge_entries (id, title, content) VALUES (?, ?, ?)",
            ("partial-1", "Partial", "Partial content"),
        )
        conn.commit()
        conn.close()

        _run_ensure_knowledge_index(dirs)
        result = _run_inject_knowledge(dirs, "new inject", "general")

        assert result["indexed"] is True

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT content FROM knowledge_entries WHERE id = ?", (result["injected_id"],))
        row = cursor.fetchone()
        cursor.execute("SELECT COUNT(*) FROM knowledge_entries WHERE id = 'partial-1'")
        partial_count = cursor.fetchone()[0]
        conn.close()

        assert row is not None
        assert row[0] == "new inject"
        assert partial_count == 1


class TestDataSurvivesSchemaMigration:
    def test_ks_data_survives_mcp_startup(self, tmp_path: Path) -> None:
        dirs = _setup_temp_knowledge_dirs(tmp_path)
        db_path = dirs["db_path"]

        conn = sqlite3.connect(str(db_path))
        _create_ks_table(conn)
        _insert_ks_row(conn, "ks-valuable")
        conn.close()

        _run_ensure_knowledge_index(dirs)
        _run_ensure_knowledge_index(dirs)
        _run_ensure_knowledge_index(dirs)

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM knowledge_entries WHERE id = 'ks-valuable'")
        count = cursor.fetchone()[0]
        conn.close()

        assert count == 1, f"Data lost after repeated _ensure_knowledge_index calls: count={count}"

    def test_injected_data_survives_migration(self, tmp_path: Path) -> None:
        dirs = _setup_temp_knowledge_dirs(tmp_path)
        db_path = dirs["db_path"]

        conn = sqlite3.connect(str(db_path))
        _create_mcp_table(conn)
        conn.close()

        _run_ensure_knowledge_index(dirs)
        result = _run_inject_knowledge(dirs, "persistent data", "general")
        assert result["indexed"] is True
        inject_id = result["injected_id"]

        _run_ensure_knowledge_index(dirs)

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT content FROM knowledge_entries WHERE id = ?", (inject_id,))
        row = cursor.fetchone()
        conn.close()

        assert row is not None, "Injected data lost after re-running _ensure_knowledge_index"
        assert row[0] == "persistent data"

    def test_mcp_and_ks_data_coexist(self, tmp_path: Path) -> None:
        dirs = _setup_temp_knowledge_dirs(tmp_path)
        db_path = dirs["db_path"]

        conn = sqlite3.connect(str(db_path))
        _create_ks_table(conn)
        _insert_ks_row(conn, "ks-coexist")
        conn.close()

        _run_ensure_knowledge_index(dirs)
        result = _run_inject_knowledge(dirs, "mcp data", "general")
        assert result["indexed"] is True

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM knowledge_entries")
        total = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM knowledge_entries WHERE id = 'ks-coexist'")
        ks_count = cursor.fetchone()[0]
        cursor.execute("SELECT content FROM knowledge_entries WHERE id = ?", (result["injected_id"],))
        mcp_row = cursor.fetchone()
        conn.close()

        assert total == 2
        assert ks_count == 1
        assert mcp_row is not None
        assert mcp_row[0] == "mcp data"
