import pytest
from unittest.mock import patch, MagicMock
from mcp.server.fastmcp import FastMCP
from xuansto_mcp.tools.workflow_dispatch import (
    _start_workflow,
    _get_workflow_status,
    _abort_workflow,
    _current_phase,
    register,
)


@pytest.fixture
def mcp_server():
    return FastMCP("test-server")


@pytest.fixture(autouse=True)
def reset_workflows():
    from xuansto_mcp.tools import workflow_dispatch as wd
    wd._ACTIVE_WORKFLOWS.clear()
    yield
    wd._ACTIVE_WORKFLOWS.clear()


def test_start_workflow_nonexistent():
    result = _start_workflow("nonexistent-workflow-xyz", ".")
    assert result.get("error") is True
    assert "WORKFLOW_NOT_FOUND" in result.get("code", "")


def test_get_workflow_status_not_found():
    result = _get_workflow_status("wf-nonexistent")
    assert result.get("error") is True


def test_abort_workflow_not_found():
    result = _abort_workflow("wf-nonexistent")
    assert result.get("error") is True


def test_current_phase_not_found():
    result = _current_phase("wf-nonexistent")
    assert result.get("error") is True


@pytest.mark.asyncio
async def test_workflow_dispatch_start_positive(mcp_server):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["workflow_dispatch"].fn
    with patch("xuansto_mcp.tools.workflow_dispatch._start_workflow") as mock_start:
        mock_start.return_value = {
            "workflow_id": "wf-test1234",
            "workflow": "sdd-tdd-fast",
            "project_path": ".",
            "status": "running",
            "current_phase": 0,
        }
        result = await tool_fn(action="start", workflow="sdd-tdd-fast")
        assert result.get("error") is False


@pytest.mark.asyncio
async def test_workflow_dispatch_start_no_workflow(mcp_server):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["workflow_dispatch"].fn
    result = await tool_fn(action="start", workflow=None)
    assert result.get("error") is True


@pytest.mark.asyncio
async def test_workflow_dispatch_status_all(mcp_server):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["workflow_dispatch"].fn
    with patch("xuansto_mcp.tools.workflow_dispatch._load_all_workflows", return_value={}):
        result = await tool_fn(action="status", workflow_id=None)
        assert result.get("error") is False


@pytest.mark.asyncio
async def test_workflow_dispatch_abort_no_id(mcp_server):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["workflow_dispatch"].fn
    result = await tool_fn(action="abort", workflow_id=None)
    assert result.get("error") is True


@pytest.mark.asyncio
async def test_workflow_dispatch_phase_no_id(mcp_server):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["workflow_dispatch"].fn
    result = await tool_fn(action="phase", workflow_id=None)
    assert result.get("error") is True


@pytest.mark.asyncio
async def test_workflow_dispatch_phase_no_phase_action(mcp_server):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["workflow_dispatch"].fn
    result = await tool_fn(action="phase", workflow_id="wf-test", phase_action=None)
    assert result.get("error") is True


@pytest.mark.asyncio
async def test_workflow_dispatch_invalid_action(mcp_server):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["workflow_dispatch"].fn
    result = await tool_fn(action="invalid_action")
    assert result.get("error") is True


@pytest.mark.asyncio
async def test_workflow_dispatch_recover_no_id(mcp_server):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["workflow_dispatch"].fn
    result = await tool_fn(action="recover", workflow_id="")
    assert result.get("error") is True
