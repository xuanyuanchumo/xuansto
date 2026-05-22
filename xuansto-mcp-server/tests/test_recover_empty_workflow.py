import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from xuansto_mcp.tools.workflow_dispatch import register


@pytest.mark.asyncio
async def test_recover_with_none_workflow_id_returns_error():
    from mcp.server.fastmcp import FastMCP

    test_mcp = FastMCP("test")
    register(test_mcp)
    tool_fn = test_mcp._tool_manager._tools["workflow_dispatch"].fn

    result = await tool_fn(action="recover", workflow_id=None, project_path=".")
    assert result.get("error") is True
    assert "workflow_id" in result.get("message", "")


@pytest.mark.asyncio
async def test_recover_with_empty_string_workflow_id_returns_error():
    from mcp.server.fastmcp import FastMCP

    test_mcp = FastMCP("test")
    register(test_mcp)
    tool_fn = test_mcp._tool_manager._tools["workflow_dispatch"].fn

    result = await tool_fn(action="recover", workflow_id="", project_path=".")
    assert result.get("error") is True
    assert "workflow_id" in result.get("message", "")


@pytest.mark.asyncio
async def test_recover_with_whitespace_workflow_id_returns_error():
    from mcp.server.fastmcp import FastMCP

    test_mcp = FastMCP("test")
    register(test_mcp)
    tool_fn = test_mcp._tool_manager._tools["workflow_dispatch"].fn

    result = await tool_fn(action="recover", workflow_id="   ", project_path=".")
    assert result.get("error") is True
    assert "workflow_id" in result.get("message", "")


@pytest.mark.asyncio
async def test_recover_with_valid_workflow_id_does_not_return_empty_error(tmp_path: Path):
    from xuansto_mcp.tools.workflow_dispatch import _save_snapshot
    from mcp.server.fastmcp import FastMCP

    test_mcp = FastMCP("test")
    register(test_mcp)
    tool_fn = test_mcp._tool_manager._tools["workflow_dispatch"].fn

    wf_id = "wf-recover-test"
    _save_snapshot(wf_id, {"current_phase": 2, "status": "running"}, str(tmp_path))

    result = await tool_fn(action="recover", workflow_id=wf_id, project_path=str(tmp_path))
    assert result.get("error") is not True or result.get("code") != "workflow_id不能为空"
    if not result.get("error"):
        data = result.get("data", result)
        assert data.get("action") == "recover"
