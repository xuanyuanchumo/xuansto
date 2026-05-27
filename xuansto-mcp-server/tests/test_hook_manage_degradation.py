from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from mcp.server.fastmcp import FastMCP

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from xuansto_mcp.tools import hook_manage
from xuansto_mcp.tools.hook_manage import register


def _get_hook_manage_fn(mcp: FastMCP):
    for name, fn in mcp._tool_manager._tools.items():
        if name == "hook_manage":
            return fn
    return None


@pytest.mark.asyncio
async def test_script_missing_falls_back_to_inline():
    mcp = FastMCP("test")
    register(mcp)
    tool_fn = _get_hook_manage_fn(mcp)
    assert tool_fn is not None

    with tempfile.TemporaryDirectory() as tmpdir:
        fake_scripts_dir = Path(tmpdir) / "no_scripts"
        fake_scripts_dir.mkdir()

        original_map = dict(hook_manage.HOOK_SCRIPTS_MAP)
        patched_map = dict(original_map)
        patched_map["security-block"] = "nonexistent-script.py"

        with patch("xuansto_mcp.tools.hook_manage.SCRIPTS_DIR", fake_scripts_dir), \
             patch("xuansto_mcp.tools.hook_manage.HOOK_SCRIPTS_MAP", patched_map):
            result = await tool_fn.fn(
                action="execute",
                hook_name="security-block",
                context={"command": "rm -rf /"},
            )

    assert result.get("error") is False
    data = result.get("data", {})
    assert data["hook"] == "security-block"
    assert data["status"] == "block"
    assert data["source"] == "inline_fallback"
    assert "检测到危险命令" in data["message"]


@pytest.mark.asyncio
async def test_script_missing_uses_inline_fallback():
    mcp = FastMCP("test")
    register(mcp)
    tool_fn = _get_hook_manage_fn(mcp)
    assert tool_fn is not None

    with tempfile.TemporaryDirectory() as tmpdir:
        fake_scripts_dir = Path(tmpdir) / "no_scripts"
        fake_scripts_dir.mkdir()

        with patch("xuansto_mcp.tools.hook_manage.SCRIPTS_DIR", fake_scripts_dir):
            result = await tool_fn.fn(
                action="execute",
                hook_name="encoding-check",
                context=None,
            )

    assert result.get("error") is False
    data = result.get("data", {})
    assert data["hook"] == "encoding-check"
    assert data["status"] == "pass"
    assert data["source"] == "inline_fallback"
