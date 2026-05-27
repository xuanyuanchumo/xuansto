from __future__ import annotations

import sqlite3
import threading
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from xuansto_mcp.core.database import get_db, init_db, DB_PATH


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "test_knowledge.db"


@pytest.fixture
def initialized_db(tmp_path: Path):
    with patch("xuansto_mcp.core.database.DB_PATH", tmp_path / "xuansto.db"), \
         patch("xuansto_mcp.core.database.WORK_DIR", tmp_path):
        init_db()
        yield tmp_path / "xuansto.db"


class TestWALModeEnabled:
    def test_wal_mode_enabled(self, initialized_db: Path) -> None:
        with patch("xuansto_mcp.core.database.DB_PATH", initialized_db):
            conn = get_db()
            try:
                row = conn.execute("PRAGMA journal_mode").fetchone()
                assert row is not None
                assert row[0].lower() == "wal"
            finally:
                conn.close()


class TestBusyTimeoutSet:
    def test_busy_timeout_set(self, initialized_db: Path) -> None:
        with patch("xuansto_mcp.core.database.DB_PATH", initialized_db):
            conn = get_db()
            try:
                row = conn.execute("PRAGMA busy_timeout").fetchone()
                assert row is not None
                assert row[0] == 5000
            finally:
                conn.close()


class TestConcurrentReadWrite:
    def test_concurrent_read_write(self, initialized_db: Path) -> None:
        with patch("xuansto_mcp.core.database.DB_PATH", initialized_db):
            conn = get_db()
            conn.execute(
                "CREATE TABLE IF NOT EXISTS test_entries "
                "(id TEXT PRIMARY KEY, content TEXT NOT NULL)"
            )
            conn.commit()
            conn.close()

            write_errors: list[str] = []
            read_errors: list[str] = []

            def writer() -> None:
                try:
                    c = get_db()
                    try:
                        for i in range(20):
                            c.execute(
                                "INSERT OR REPLACE INTO test_entries (id, content) VALUES (?, ?)",
                                (f"w-{i}", f"content-{i}"),
                            )
                            c.commit()
                            time.sleep(0.01)
                    finally:
                        c.close()
                except Exception as e:
                    write_errors.append(str(e))

            def reader() -> None:
                try:
                    c = get_db()
                    try:
                        for _ in range(20):
                            c.execute("SELECT COUNT(*) FROM test_entries").fetchone()
                            time.sleep(0.01)
                    finally:
                        c.close()
                except Exception as e:
                    read_errors.append(str(e))

            t_write = threading.Thread(target=writer)
            t_read = threading.Thread(target=reader)
            t_write.start()
            t_read.start()
            t_write.join(timeout=10)
            t_read.join(timeout=10)

            assert not write_errors, f"Write errors: {write_errors}"
            assert not read_errors, f"Read errors: {read_errors}"


class TestGetDbConnectionHelper:
    def test_get_db_connection_helper(self, initialized_db: Path) -> None:
        with patch("xuansto_mcp.core.database.DB_PATH", initialized_db):
            conn = get_db()
            try:
                assert isinstance(conn, sqlite3.Connection)
                jm = conn.execute("PRAGMA journal_mode").fetchone()
                assert jm[0].lower() == "wal"
                bt = conn.execute("PRAGMA busy_timeout").fetchone()
                assert bt[0] == 5000
            finally:
                conn.close()

    def test_get_db_creates_file(self, tmp_path: Path) -> None:
        db_file = tmp_path / "xuansto.db"
        with patch("xuansto_mcp.core.database.DB_PATH", db_file), \
             patch("xuansto_mcp.core.database.WORK_DIR", tmp_path):
            conn = get_db()
            try:
                conn.execute("CREATE TABLE t (x TEXT)")
                conn.commit()
                assert db_file.exists()
            finally:
                conn.close()
