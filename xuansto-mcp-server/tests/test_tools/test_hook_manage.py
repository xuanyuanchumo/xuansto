import pytest
from unittest.mock import patch, MagicMock
from mcp.server.fastmcp import FastMCP
from xuansto_mcp.tools.hook_manage import (
    _security_block_logic,
    _dangerous_cmd_confirm_logic,
    _auto_format_logic,
    _console_log_detect_logic,
    INLINE_HOOK_LOGIC,
    register,
)


@pytest.fixture
def mcp_server():
    return FastMCP("test-server")


def test_security_block_logic_dangerous():
    result = _security_block_logic(".", {"command": "rm -rf /"})
    assert result["status"] == "block"


def test_security_block_logic_safe():
    result = _security_block_logic(".", {"command": "ls -la"})
    assert result["status"] == "pass"


def test_security_block_logic_no_command():
    result = _security_block_logic(".", None)
    assert result["status"] == "pass"


def test_dangerous_cmd_confirm_warn():
    result = _dangerous_cmd_confirm_logic(".", {"command": "git push --force"})
    assert result["status"] == "warn"


def test_dangerous_cmd_confirm_safe():
    result = _dangerous_cmd_confirm_logic(".", {"command": "git commit -m 'msg'"})
    assert result["status"] == "pass"


def test_auto_format_logic_nonexistent():
    result = _auto_format_logic("/nonexistent/path")
    assert result["status"] == "pass"


def test_auto_format_logic_clean(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "clean.py").write_text("def hello():\n    return 'world'\n", encoding="utf-8")
    result = _auto_format_logic(str(tmp_path))
    assert result["status"] == "pass"


def test_auto_format_logic_with_issues(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "messy.py").write_text("def hello():\r\n    return 'world'   \n", encoding="utf-8")
    result = _auto_format_logic(str(tmp_path))
    assert result["status"] == "warn"


def test_console_log_detect_nonexistent():
    result = _console_log_detect_logic("/nonexistent/path")
    assert result["status"] == "pass"


def test_console_log_detect_with_logs(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "debug.js").write_text("console.log('debug');\n", encoding="utf-8")
    result = _console_log_detect_logic(str(tmp_path))
    assert result["status"] == "warn"


def test_inline_hook_logic_keys():
    expected = {
        "security-block",
        "dangerous-cmd-confirm",
        "auto-format",
        "console-log-detect",
        "type-check",
        "git-status-check",
        "decision-log-persist",
        "token-budget-check",
        "encoding-check",
        "load-context",
        "kb-health-check",
        "platform-detect",
        "session-save",
        "experience-precipitate",
        "pattern-detect",
        "save-state",
    }
    assert set(INLINE_HOOK_LOGIC.keys()) == expected


@pytest.mark.asyncio
async def test_hook_manage_list_positive(mcp_server):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["hook_manage"].fn
    result = await tool_fn(action="list", profile="standard")
    assert result.get("error") is False
    assert result["data"]["total"] > 0


@pytest.mark.asyncio
async def test_hook_manage_list_invalid_profile(mcp_server):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["hook_manage"].fn
    result = await tool_fn(action="list", profile="nonexistent_profile")
    assert result.get("error") is True


@pytest.mark.asyncio
async def test_hook_manage_execute_no_hook_name(mcp_server):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["hook_manage"].fn
    result = await tool_fn(action="execute", hook_name=None)
    assert result.get("error") is True


@pytest.mark.asyncio
async def test_hook_manage_execute_inline(mcp_server):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["hook_manage"].fn
    result = await tool_fn(action="execute", hook_name="security-block", context={"command": "rm -rf /"})
    assert result.get("error") is False
    assert result["data"]["status"] == "block"


@pytest.mark.asyncio
async def test_hook_manage_execute_unknown_hook(mcp_server):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["hook_manage"].fn
    result = await tool_fn(action="execute", hook_name="nonexistent-hook")
    assert result.get("error") is False
    assert result["data"]["status"] == "skipped"


@pytest.mark.asyncio
async def test_hook_manage_invalid_action(mcp_server):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["hook_manage"].fn
    result = await tool_fn(action="invalid_action")
    assert result.get("error") is True
