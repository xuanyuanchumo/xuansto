from __future__ import annotations

import sqlite3
import threading
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from xuansto_mcp.tools.knowledge_search import _get_db_connection


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "test_knowledge.db"


class TestWALModeEnabled:
    def test_wal_mode_enabled(self, db_path: Path) -> None:
        conn = _get_db_connection(db_path)
        try:
            row = conn.execute("PRAGMA journal_mode").fetchone()
            assert row is not None
            assert row[0].lower() == "wal"
        finally:
            conn.close()


class TestBusyTimeoutSet:
    def test_busy_timeout_set(self, db_path: Path) -> None:
        conn = _get_db_connection(db_path)
        try:
            row = conn.execute("PRAGMA busy_timeout").fetchone()
            assert row is not None
            assert row[0] == 5000
        finally:
            conn.close()


class TestConcurrentReadWrite:
    def test_concurrent_read_write(self, db_path: Path) -> None:
        conn = _get_db_connection(db_path)
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
                c = _get_db_connection(db_path)
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
                c = _get_db_connection(db_path)
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
    def test_get_db_connection_helper(self, db_path: Path) -> None:
        conn = _get_db_connection(db_path)
        try:
            assert isinstance(conn, sqlite3.Connection)
            jm = conn.execute("PRAGMA journal_mode").fetchone()
            assert jm[0].lower() == "wal"
            bt = conn.execute("PRAGMA busy_timeout").fetchone()
            assert bt[0] == 5000
        finally:
            conn.close()

    def test_get_db_connection_creates_file(self, tmp_path: Path) -> None:
        path = tmp_path / "subdir" / "new.db"
        path.parent.mkdir(parents=True, exist_ok=True)
        conn = _get_db_connection(path)
        try:
            conn.execute("CREATE TABLE t (x TEXT)")
            conn.commit()
            assert path.exists()
        finally:
            conn.close()
