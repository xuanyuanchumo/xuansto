import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from mcp.server.fastmcp import FastMCP
from xuansto_mcp.tools.hook_manage import (
    _security_block_logic,
    _dangerous_cmd_confirm_logic,
    INLINE_HOOK_LOGIC,
    execute_pre_hooks,
    execute_post_hooks,
    get_pre_hooks,
    get_post_hooks,
)


def test_security_block_pre_hook_blocks_dangerous_command():
    result = _security_block_logic(".", {"command": "rm -rf /"})
    assert result["status"] == "block"


def test_security_block_pre_hook_passes_safe_command():
    result = _security_block_logic(".", {"command": "git commit -m 'msg'"})
    assert result["status"] == "pass"


def test_dangerous_cmd_confirm_warns():
    result = _dangerous_cmd_confirm_logic(".", {"command": "git push --force"})
    assert result["status"] == "warn"


def test_execute_pre_hooks_blocks_on_security():
    kwargs = {"target": ".", "command": "rm -rf /"}
    results, errors = execute_pre_hooks("security_scan", kwargs)
    blocked = [r for r in results if r.get("status") == "block"]
    assert len(blocked) > 0


def test_execute_pre_hooks_passes_safe():
    kwargs = {"target": ".", "command": "ls -la"}
    results, errors = execute_pre_hooks("security_scan", kwargs)
    blocked = [r for r in results if r.get("status") == "block"]
    assert len(blocked) == 0


def test_execute_pre_hooks_no_hooks_for_unknown_tool():
    kwargs = {"target": "."}
    results, errors = execute_pre_hooks("unknown_tool_no_hooks", kwargs)
    assert len(results) == 0


def test_get_pre_hooks_returns_hooks():
    hooks = get_pre_hooks("security_scan")
    assert "security-block" in hooks


def test_get_pre_hooks_no_hooks():
    hooks = get_pre_hooks("unknown_tool")
    assert len(hooks) == 0


def test_get_post_hooks_decision_log():
    hooks = get_post_hooks("workflow_dispatch")
    assert "decision-log-persist" in hooks


def test_get_post_hooks_no_hooks():
    hooks = get_post_hooks("skill_analyze")
    assert len(hooks) == 0


def test_execute_post_hooks_decision_log():
    kwargs = {"project_path": "."}
    result_data = {"error": False, "data": {"workflow_id": "wf-test"}}
    errors = execute_post_hooks("workflow_dispatch", kwargs, result_data)
    assert isinstance(errors, list)


@pytest.mark.asyncio
async def test_hook_interception_in_server_wrapping():
    from xuansto_mcp.tools.hook_manage import register as hook_register
    mcp = FastMCP("test-interception")
    hook_register(mcp)
    tool_fn = mcp._tool_manager._tools["hook_manage"].fn
    result = await tool_fn(action="execute", hook_name="security-block", context={"command": "rm -rf /"})
    assert result["data"]["status"] == "block"


@pytest.mark.asyncio
async def test_hook_interception_safe_passes():
    from xuansto_mcp.tools.hook_manage import register as hook_register
    mcp = FastMCP("test-interception-safe")
    hook_register(mcp)
    tool_fn = mcp._tool_manager._tools["hook_manage"].fn
    result = await tool_fn(action="execute", hook_name="security-block", context={"command": "python script.py"})
    assert result["data"]["status"] == "pass"


@pytest.mark.asyncio
async def test_post_hook_modification():
    from xuansto_mcp.tools.hook_manage import register as hook_register
    mcp = FastMCP("test-post-hook")
    hook_register(mcp)
    tool_fn = mcp._tool_manager._tools["hook_manage"].fn
    result = await tool_fn(action="execute", hook_name="decision-log-persist", context={"project_path": "."})
    assert result["data"]["status"] == "pass"
