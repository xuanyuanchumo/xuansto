import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from xuansto_mcp.tools.agent_status import _AGENT_INSTANCES, _AgentInstance


@pytest.mark.asyncio
async def test_agent_create():
    from xuansto_mcp.tools.agent_status import register
    from mcp.server.fastmcp import FastMCP

    test_mcp = FastMCP("test")
    register(test_mcp)
    tool_fn = test_mcp._tool_manager._tools["agent_status"].fn

    _AGENT_INSTANCES.clear()
    result = await tool_fn(action="create", agent_type="Backend Developer", capabilities=["python", "fastapi"])
    data = result.get("data", result)
    assert data.get("action") == "create"
    assert data.get("agent_type") == "Backend Developer"
    assert "python" in data.get("capabilities", [])
    assert data.get("status") == "idle"
    assert data.get("agent_id", "").startswith("agent-")


@pytest.mark.asyncio
async def test_agent_match():
    from xuansto_mcp.tools.agent_status import register
    from mcp.server.fastmcp import FastMCP

    test_mcp = FastMCP("test")
    register(test_mcp)
    tool_fn = test_mcp._tool_manager._tools["agent_status"].fn

    _AGENT_INSTANCES.clear()
    await tool_fn(action="create", agent_type="Backend", capabilities=["python", "fastapi", "sql"])
    await tool_fn(action="create", agent_type="Frontend", capabilities=["typescript", "react"])

    result = await tool_fn(action="match", capabilities=["python", "sql"])
    data = result.get("data", result)
    assert data.get("action") == "match"
    assert data.get("total", 0) >= 1
    matches = data.get("matches", [])
    assert matches[0]["coverage"] >= 0.5


@pytest.mark.asyncio
async def test_agent_assign_and_status():
    from xuansto_mcp.tools.agent_status import register
    from mcp.server.fastmcp import FastMCP

    test_mcp = FastMCP("test")
    register(test_mcp)
    tool_fn = test_mcp._tool_manager._tools["agent_status"].fn

    _AGENT_INSTANCES.clear()
    create_result = await tool_fn(action="create", agent_type="Backend", capabilities=["python"])
    agent_id = create_result.get("data", create_result).get("agent_id")

    assign_result = await tool_fn(action="assign", agent_id=agent_id, task="Implement auth API")
    data = assign_result.get("data", assign_result)
    assert data.get("status") == "busy"

    status_result = await tool_fn(action="instance_status", agent_id=agent_id)
    status_data = status_result.get("data", status_result)
    assert status_data.get("status") == "busy"
    assert status_data.get("task") == "Implement auth API"


@pytest.mark.asyncio
async def test_agent_destroy():
    from xuansto_mcp.tools.agent_status import register
    from mcp.server.fastmcp import FastMCP

    test_mcp = FastMCP("test")
    register(test_mcp)
    tool_fn = test_mcp._tool_manager._tools["agent_status"].fn

    _AGENT_INSTANCES.clear()
    create_result = await tool_fn(action="create", agent_type="Backend", capabilities=["python"])
    agent_id = create_result.get("data", create_result).get("agent_id")

    destroy_result = await tool_fn(action="destroy", agent_id=agent_id)
    data = destroy_result.get("data", destroy_result)
    assert data.get("status") == "destroyed"

    assert agent_id not in _AGENT_INSTANCES


@pytest.mark.asyncio
async def test_agent_assign_busy_fails():
    from xuansto_mcp.tools.agent_status import register
    from mcp.server.fastmcp import FastMCP

    test_mcp = FastMCP("test")
    register(test_mcp)
    tool_fn = test_mcp._tool_manager._tools["agent_status"].fn

    _AGENT_INSTANCES.clear()
    create_result = await tool_fn(action="create", agent_type="Backend", capabilities=["python"])
    agent_id = create_result.get("data", create_result).get("agent_id")

    await tool_fn(action="assign", agent_id=agent_id, task="Task 1")
    result = await tool_fn(action="assign", agent_id=agent_id, task="Task 2")
    assert result.get("error") is not None


@pytest.mark.asyncio
async def test_agent_release_computes_duration():
    from xuansto_mcp.tools.agent_status import register
    from mcp.server.fastmcp import FastMCP

    test_mcp = FastMCP("test")
    register(test_mcp)
    tool_fn = test_mcp._tool_manager._tools["agent_status"].fn

    _AGENT_INSTANCES.clear()
    create_result = await tool_fn(action="create", agent_type="Backend", capabilities=["python"])
    agent_id = create_result.get("data", create_result).get("agent_id")

    assign_result = await tool_fn(action="assign", agent_id=agent_id, task="Implement auth")
    assert assign_result.get("data", assign_result).get("status") == "busy"

    release_result = await tool_fn(action="release", agent_id=agent_id)
    data = release_result.get("data", release_result)
    assert data.get("action") == "release"
    assert data.get("status") == "idle"
    assert data.get("completed_task") == "Implement auth"
    assert data.get("duration_ms") >= 0
    assert data.get("total_duration_ms") >= 0
    assert data.get("task_count") == 1

    status_result = await tool_fn(action="instance_status", agent_id=agent_id)
    status_data = status_result.get("data", status_result)
    assert status_data.get("status") == "idle"
    assert status_data.get("task") == ""


@pytest.mark.asyncio
async def test_agent_release_not_busy_fails():
    from xuansto_mcp.tools.agent_status import register
    from mcp.server.fastmcp import FastMCP

    test_mcp = FastMCP("test")
    register(test_mcp)
    tool_fn = test_mcp._tool_manager._tools["agent_status"].fn

    _AGENT_INSTANCES.clear()
    create_result = await tool_fn(action="create", agent_type="Backend", capabilities=["python"])
    agent_id = create_result.get("data", create_result).get("agent_id")

    result = await tool_fn(action="release", agent_id=agent_id)
    assert result.get("error") is True
