from __future__ import annotations

import json
import os
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def test_sqlite_connection_closed_on_exception():
    from xuansto_mcp.tools.knowledge_search import _sqlite_search

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "index" / "knowledge.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(db_path))
        conn.execute(
            "CREATE TABLE knowledge_entries (id TEXT PRIMARY KEY, title TEXT, content TEXT, type TEXT, metadata_json TEXT, created_at TEXT, updated_at TEXT)"
        )
        conn.execute(
            "CREATE VIRTUAL TABLE knowledge_fts USING fts5(content, title, type, content=knowledge_entries, content_rowid=rowid, tokenize='unicode61')"
        )
        conn.commit()
        conn.close()

        with patch("xuansto_mcp.tools.knowledge_search.KNOWLEDGE_DB_PATH", db_path):
            result = _sqlite_search("test query", 5, None, 0.0)

        assert result is None or isinstance(result, dict)

        conn2 = sqlite3.connect(str(db_path))
        try:
            conn2.execute("PRAGMA integrity_check")
        finally:
            conn2.close()


def test_sqlite_inject_connection_closed_on_error():
    try:
        from xuansto_mcp.tools.knowledge_inject import _inject_knowledge
    except ImportError:
        pytest.skip("_inject_knowledge not available in knowledge_inject module")

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "index" / "knowledge.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)

        with patch("xuansto_mcp.tools.knowledge_inject.KNOWLEDGE_DB_PATH", db_path), \
             patch("xuansto_mcp.tools.knowledge_inject.KNOWLEDGE_GENERAL_DIR", Path(tmpdir) / "general"):
            result = _inject_knowledge("test content", "general", None)

        assert isinstance(result, dict)
        assert result["indexed"] is False


def test_atomic_write_creates_file():
    from xuansto_mcp.core import atomic_write

    with tempfile.TemporaryDirectory() as tmpdir:
        target = Path(tmpdir) / "test_file.json"
        content = '{"key": "value"}'
        atomic_write(target, content)

        assert target.exists()
        assert target.read_text(encoding="utf-8") == content


def test_atomic_write_cleanup_on_failure():
    from xuansto_mcp.core import atomic_write

    with tempfile.TemporaryDirectory() as tmpdir:
        target = Path(tmpdir) / "test_file.json"
        target.write_text("original", encoding="utf-8")

        with patch("os.replace", side_effect=OSError("rename failed")):
            with pytest.raises(OSError, match="rename failed"):
                atomic_write(target, "new content")

        assert target.read_text(encoding="utf-8") == "original"

        tmp_files = list(Path(tmpdir).glob("*.tmp"))
        assert len(tmp_files) == 0


def test_datetime_uses_utc():
    import inspect
    from xuansto_mcp.tools import workflow_dispatch

    source = inspect.getsource(workflow_dispatch)

    assert "datetime.now()" not in source or "datetime.now(timezone.utc)" in source
    assert "datetime.now(timezone.utc)" in source

    for line in source.splitlines():
        if "datetime.now()" in line and "timezone.utc" not in line:
            pytest.fail(f"Found bare datetime.now() in workflow_dispatch: {line.strip()}")


def test_tools_count_dynamic():
    import inspect
    from xuansto_mcp.tools import server_health

    source = inspect.getsource(server_health)

    assert '"tools_count": 13' not in source
    assert "'tools_count': 13" not in source
    assert "tools_count" in source
    assert "len(_REGISTERED_TOOL_NAMES)" in source


def test_recover_empty_workflow_id_format():
    from xuansto_mcp.core.errors import make_error_response, ERR_VALIDATION

    result = make_error_response(ValueError("workflow_id不能为空"))

    assert result["error"] is True
    assert "error_code" in result
    assert "message" in result
    assert result["message"] == "workflow_id不能为空"
    assert result["error_code"] == ERR_VALIDATION
