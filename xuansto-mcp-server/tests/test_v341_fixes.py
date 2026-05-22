from __future__ import annotations

import os
import re
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

TOOLS_DIR = Path(__file__).resolve().parent.parent / "src" / "xuansto_mcp" / "tools"

PERSIST_FUNCTION_PATTERNS = [
    "workflow_dispatch.py",
    "agent_status.py",
    "resource_load_status.py",
    "quality_gate_check.py",
    "knowledge_search.py",
]


def test_no_write_text_in_persist_functions():
    persist_funcs = {
        "workflow_dispatch.py": ["_persist_active_workflows", "_save_snapshot"],
        "agent_status.py": ["_persist_agent_instances"],
        "resource_load_status.py": ["_save_resource_state"],
        "quality_gate_check.py": ["_save_gate_cache"],
        "knowledge_search.py": ["_inject_knowledge", "_precipitate_experience"],
    }
    violations = []
    for filename, funcs in persist_funcs.items():
        filepath = TOOLS_DIR / filename
        if not filepath.exists():
            continue
        content = filepath.read_text(encoding="utf-8")
        for func_name in funcs:
            func_match = re.search(
                rf"def {func_name}\([^)]*\)[^:]*:(.*?)(?=\ndef |\Z)",
                content,
                re.DOTALL,
            )
            if func_match is None:
                continue
            func_body = func_match.group(1)
            if ".write_text(" in func_body:
                violations.append(f"{filename}::{func_name}")
    assert violations == [], (
        f"Found write_text() in persist functions: {violations}. "
        "Use atomic_write() instead."
    )


def test_ensure_index_connection_closed_on_exception():
    mock_conn = MagicMock()
    mock_conn.execute.side_effect = RuntimeError("db error")

    with patch("xuansto_mcp.tools.knowledge_search._get_db_connection", return_value=mock_conn):
        with tempfile.TemporaryDirectory() as tmp:
            with patch("xuansto_mcp.core.config.KNOWLEDGE_DIR", Path(tmp)):
                from xuansto_mcp.tools.knowledge_search import _ensure_knowledge_index

                with pytest.raises(RuntimeError):
                    _ensure_knowledge_index()

    mock_conn.close.assert_called()


def test_keyword_search_skips_large_files(tmp_path):
    from xuansto_mcp.tools.knowledge_search import (
        _MAX_KEYWORD_FILE_BYTES,
        _keyword_fallback_search,
    )

    large_dir = tmp_path / "general"
    large_dir.mkdir()
    large_file = large_dir / "big.md"
    large_file.write_text("x" * (_MAX_KEYWORD_FILE_BYTES + 1), encoding="utf-8")

    with patch(
        "xuansto_mcp.tools.knowledge_search.KNOWLEDGE_GENERAL_DIR", large_dir
    ), patch(
        "xuansto_mcp.tools.knowledge_search.REFERENCES_DIR", tmp_path / "refs"
    ), patch(
        "xuansto_mcp.tools.knowledge_search.KNOWLEDGE_WORKSPACE_DIR",
        tmp_path / "ws",
    ), patch(
        "xuansto_mcp.tools.knowledge_search.KNOWLEDGE_EXPERIENCE_DIR",
        tmp_path / "exp",
    ):
        result = _keyword_fallback_search("x", top_k=10, scope="general")

    assert result["total"] == 0


def test_keyword_search_reads_small_files(tmp_path):
    from xuansto_mcp.tools.knowledge_search import _keyword_fallback_search

    general_dir = tmp_path / "general"
    general_dir.mkdir()
    small_file = general_dir / "small.md"
    small_file.write_text("hello world keyword test", encoding="utf-8")

    with patch(
        "xuansto_mcp.tools.knowledge_search.KNOWLEDGE_GENERAL_DIR", general_dir
    ), patch(
        "xuansto_mcp.tools.knowledge_search.REFERENCES_DIR", tmp_path / "refs"
    ), patch(
        "xuansto_mcp.tools.knowledge_search.KNOWLEDGE_WORKSPACE_DIR",
        tmp_path / "ws",
    ), patch(
        "xuansto_mcp.tools.knowledge_search.KNOWLEDGE_EXPERIENCE_DIR",
        tmp_path / "exp",
    ):
        result = _keyword_fallback_search("hello", top_k=10, scope="general")

    assert result["total"] >= 1
    assert any("small.md" in r["source"] for r in result["results"])
