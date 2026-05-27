from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from xuansto_mcp.core.database import (
    DB_PATH,
    _CREATE_INDEXES_SQL,
    _CREATE_TABLES_SQL,
    _FTS5_SQL,
    get_db,
    init_db,
    is_fts5_available,
)


EXPECTED_TABLES = [
    "workflow_instances",
    "session_states",
    "resource_load_states",
    "degradation_states",
    "error_patterns",
    "metrics",
    "decision_records",
    "knowledge_entries",
    "reconciliation_log",
    "token_budget_states",
    "experience_patterns",
    "agent_states",
    "workflow_states",
    "decisions",
    "decision_tags",
    "schema_version",
    "knowledge_tags",
    "dedup_log",
    "version_history",
    "usage_logs",
    "backup_history",
    "kb_reconciliation_log",
    "tool_metrics",
    "degradation_stats",
]

EXPECTED_FTS5_TABLES = [
    "knowledge_fts",
    "decisions_fts",
]

FORBIDDEN_SEPARATE_DBS = [
    "decisions.db",
    "knowledge.db",
]


class TestDatabasePath:
    def test_db_path_points_to_xuansto_db(self):
        assert DB_PATH.name == "xuansto.db"

    def test_db_path_is_under_work_dir(self):
        from xuansto_mcp.core.config import WORK_DIR
        assert DB_PATH.parent == WORK_DIR


class TestDatabaseInit:
    @pytest.fixture
    def tmp_work_dir(self, tmp_path):
        work = tmp_path / ".xuansto"
        work.mkdir()
        return work

    @pytest.fixture
    def tmp_knowledge_dir(self, tmp_path):
        kdir = tmp_path / "knowledge"
        kdir.mkdir()
        (kdir / "general").mkdir()
        (kdir / "workspace").mkdir()
        (kdir / "experience").mkdir()
        idx = kdir / "index"
        idx.mkdir()
        return kdir

    @pytest.fixture
    def patched_db(self, tmp_work_dir, tmp_knowledge_dir):
        db_path = tmp_work_dir / "xuansto.db"
        with patch("xuansto_mcp.core.database.WORK_DIR", tmp_work_dir), \
             patch("xuansto_mcp.core.database.DB_PATH", db_path), \
             patch("xuansto_mcp.core.database.KNOWLEDGE_DIR", tmp_knowledge_dir), \
             patch("xuansto_mcp.core.config.WORK_DIR", tmp_work_dir), \
             patch("xuansto_mcp.core.config.KNOWLEDGE_DIR", tmp_knowledge_dir):
            init_db()
            yield db_path

    def test_init_db_creates_xuansto_db(self, patched_db):
        assert patched_db.exists(), "init_db should create xuansto.db"

    def test_init_db_creates_all_expected_tables(self, patched_db):
        conn = sqlite3.connect(str(patched_db))
        try:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
            existing_tables = {row[0] for row in cursor.fetchall()}
            for table in EXPECTED_TABLES:
                assert table in existing_tables, f"Table '{table}' should exist in xuansto.db"
        finally:
            conn.close()

    def test_init_db_does_not_create_separate_decisions_db(self, patched_db):
        work_dir = patched_db.parent
        decisions_db = work_dir / "decisions.db"
        assert not decisions_db.exists(), "decisions.db should not be created separately"

    def test_init_db_does_not_create_separate_knowledge_db(self, patched_db, tmp_knowledge_dir):
        knowledge_db = tmp_knowledge_dir / "index" / "knowledge.db"
        assert not knowledge_db.exists(), "knowledge.db should not be created separately"

    def test_no_forbidden_separate_dbs_in_work_dir(self, patched_db):
        work_dir = patched_db.parent
        for forbidden in FORBIDDEN_SEPARATE_DBS:
            forbidden_path = work_dir / forbidden
            assert not forbidden_path.exists(), f"Forbidden separate DB '{forbidden}' should not exist"


class TestFTS5VirtualTables:
    @pytest.fixture
    def tmp_work_dir(self, tmp_path):
        work = tmp_path / ".xuansto"
        work.mkdir()
        return work

    @pytest.fixture
    def tmp_knowledge_dir(self, tmp_path):
        kdir = tmp_path / "knowledge"
        kdir.mkdir()
        (kdir / "general").mkdir()
        (kdir / "workspace").mkdir()
        (kdir / "experience").mkdir()
        idx = kdir / "index"
        idx.mkdir()
        return kdir

    @pytest.fixture
    def patched_db(self, tmp_work_dir, tmp_knowledge_dir):
        db_path = tmp_work_dir / "xuansto.db"
        with patch("xuansto_mcp.core.database.WORK_DIR", tmp_work_dir), \
             patch("xuansto_mcp.core.database.DB_PATH", db_path), \
             patch("xuansto_mcp.core.database.KNOWLEDGE_DIR", tmp_knowledge_dir), \
             patch("xuansto_mcp.core.config.WORK_DIR", tmp_work_dir), \
             patch("xuansto_mcp.core.config.KNOWLEDGE_DIR", tmp_knowledge_dir):
            init_db()
            yield db_path

    def test_fts5_availability_check(self):
        result = is_fts5_available()
        assert isinstance(result, bool)

    @pytest.mark.skipif(not is_fts5_available(), reason="FTS5 not available")
    def test_knowledge_fts_table_exists(self, patched_db):
        conn = sqlite3.connect(str(patched_db))
        try:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='knowledge_fts'"
            )
            assert cursor.fetchone() is not None, "knowledge_fts virtual table should exist"
        finally:
            conn.close()

    @pytest.mark.skipif(not is_fts5_available(), reason="FTS5 not available")
    def test_decisions_fts_table_exists(self, patched_db):
        conn = sqlite3.connect(str(patched_db))
        try:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='decisions_fts'"
            )
            assert cursor.fetchone() is not None, "decisions_fts virtual table should exist"
        finally:
            conn.close()

    @pytest.mark.skipif(not is_fts5_available(), reason="FTS5 not available")
    def test_fts5_tables_use_unicode61_tokenizer(self, patched_db):
        conn = sqlite3.connect(str(patched_db))
        try:
            cursor = conn.execute(
                "SELECT sql FROM sqlite_master WHERE type='table' AND name IN ('knowledge_fts', 'decisions_fts')"
            )
            for row in cursor.fetchall():
                sql = row[0]
                assert "unicode61" in sql.lower(), "FTS5 tables should use unicode61 tokenizer"
        finally:
            conn.close()


class TestDatabaseSchemaSQL:
    def test_create_tables_sql_contains_all_expected_tables(self):
        for table in EXPECTED_TABLES:
            assert f"CREATE TABLE IF NOT EXISTS {table}" in _CREATE_TABLES_SQL, (
                f"_CREATE_TABLES_SQL should contain CREATE TABLE for '{table}'"
            )

    def test_fts5_sql_contains_knowledge_fts(self):
        assert "knowledge_fts" in _FTS5_SQL

    def test_fts5_sql_contains_decisions_fts(self):
        assert "decisions_fts" in _FTS5_SQL

    def test_fts5_sql_contains_triggers(self):
        assert "knowledge_entries_ai" in _FTS5_SQL
        assert "knowledge_entries_ad" in _FTS5_SQL
        assert "knowledge_entries_au" in _FTS5_SQL
        assert "decisions_fts_ai" in _FTS5_SQL
        assert "decisions_fts_ad" in _FTS5_SQL
        assert "decisions_fts_au" in _FTS5_SQL

    def test_create_indexes_sql_not_empty(self):
        assert len(_CREATE_INDEXES_SQL.strip()) > 0


class TestDatabaseIndexes:
    @pytest.fixture
    def tmp_work_dir(self, tmp_path):
        work = tmp_path / ".xuansto"
        work.mkdir()
        return work

    @pytest.fixture
    def tmp_knowledge_dir(self, tmp_path):
        kdir = tmp_path / "knowledge"
        kdir.mkdir()
        (kdir / "general").mkdir()
        (kdir / "workspace").mkdir()
        (kdir / "experience").mkdir()
        idx = kdir / "index"
        idx.mkdir()
        return kdir

    @pytest.fixture
    def patched_db(self, tmp_work_dir, tmp_knowledge_dir):
        db_path = tmp_work_dir / "xuansto.db"
        with patch("xuansto_mcp.core.database.WORK_DIR", tmp_work_dir), \
             patch("xuansto_mcp.core.database.DB_PATH", db_path), \
             patch("xuansto_mcp.core.database.KNOWLEDGE_DIR", tmp_knowledge_dir), \
             patch("xuansto_mcp.core.config.WORK_DIR", tmp_work_dir), \
             patch("xuansto_mcp.core.config.KNOWLEDGE_DIR", tmp_knowledge_dir):
            init_db()
            yield db_path

    def test_indexes_created(self, patched_db):
        conn = sqlite3.connect(str(patched_db))
        try:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'"
            )
            indexes = {row[0] for row in cursor.fetchall()}
            assert len(indexes) > 0, "Database should have indexes created"
        finally:
            conn.close()


class TestGetDbConnection:
    @pytest.fixture
    def tmp_work_dir(self, tmp_path):
        work = tmp_path / ".xuansto"
        work.mkdir()
        return work

    @pytest.fixture
    def tmp_knowledge_dir(self, tmp_path):
        kdir = tmp_path / "knowledge"
        kdir.mkdir()
        (kdir / "general").mkdir()
        (kdir / "workspace").mkdir()
        (kdir / "experience").mkdir()
        idx = kdir / "index"
        idx.mkdir()
        return kdir

    @pytest.fixture
    def patched_db(self, tmp_work_dir, tmp_knowledge_dir):
        db_path = tmp_work_dir / "xuansto.db"
        with patch("xuansto_mcp.core.database.WORK_DIR", tmp_work_dir), \
             patch("xuansto_mcp.core.database.DB_PATH", db_path), \
             patch("xuansto_mcp.core.database.KNOWLEDGE_DIR", tmp_knowledge_dir), \
             patch("xuansto_mcp.core.config.WORK_DIR", tmp_work_dir), \
             patch("xuansto_mcp.core.config.KNOWLEDGE_DIR", tmp_knowledge_dir):
            init_db()
            yield db_path

    def test_get_db_returns_connection(self, patched_db):
        with patch("xuansto_mcp.core.database.DB_PATH", patched_db), \
             patch("xuansto_mcp.core.database.WORK_DIR", patched_db.parent):
            conn = get_db()
            assert conn is not None
            conn.close()

    def test_get_db_has_row_factory(self, patched_db):
        with patch("xuansto_mcp.core.database.DB_PATH", patched_db), \
             patch("xuansto_mcp.core.database.WORK_DIR", patched_db.parent):
            conn = get_db()
            assert conn.row_factory == sqlite3.Row
            conn.close()

    def test_get_db_wal_mode(self, patched_db):
        with patch("xuansto_mcp.core.database.DB_PATH", patched_db), \
             patch("xuansto_mcp.core.database.WORK_DIR", patched_db.parent):
            conn = get_db()
            cursor = conn.execute("PRAGMA journal_mode")
            mode = cursor.fetchone()[0]
            assert mode == "wal"
            conn.close()


class TestLegacyMigration:
    def test_migrate_legacy_databases_function_exists(self):
        from xuansto_mcp.core.database import _migrate_legacy_databases
        assert callable(_migrate_legacy_databases)

    def test_v13_migration_function_exists(self):
        from xuansto_mcp.core.database import _run_v13_migration
        assert callable(_run_v13_migration)

    def test_copy_v13_legacy_data_function_exists(self):
        from xuansto_mcp.core.database import _copy_v13_legacy_data
        assert callable(_copy_v13_legacy_data)
