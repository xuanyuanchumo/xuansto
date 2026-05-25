import pytest
from mcp.server.fastmcp import FastMCP

from xuansto_mcp.tools.server_health import register


@pytest.mark.asyncio
async def test_server_health_registered():
    mcp = FastMCP("test")
    register(mcp)
    tools = await mcp.list_tools()
    tool_names = [t.name for t in tools]
    assert "server_health" in tool_names


@pytest.mark.asyncio
async def test_server_health_returns_healthy_status():
    mcp = FastMCP("test")
    register(mcp)

    tool_fn = None
    for name, fn in mcp._tool_manager._tools.items():
        if name == "server_health":
            tool_fn = fn
            break

    assert tool_fn is not None
    result = await tool_fn.fn(action="check")

    assert result["error"] is False
    data = result["data"]
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_server_health_returns_version():
    mcp = FastMCP("test")
    register(mcp)

    tool_fn = None
    for name, fn in mcp._tool_manager._tools.items():
        if name == "server_health":
            tool_fn = fn
            break

    result = await tool_fn.fn(action="check")
    data = result["data"]
    assert "version" in data
    assert data["version"] == "8.0.0"


@pytest.mark.asyncio
async def test_server_health_returns_config_paths():
    mcp = FastMCP("test")
    register(mcp)

    tool_fn = None
    for name, fn in mcp._tool_manager._tools.items():
        if name == "server_health":
            tool_fn = fn
            break

    result = await tool_fn.fn(action="check")
    data = result["data"]
    assert "config" in data
    config = data["config"]
    assert "data_dir" in config
    assert "skill_root" in config
    assert "work_dir" in config
    assert "data_dir_exists" in config
    assert "skill_root_exists" in config
    assert isinstance(config["data_dir_exists"], bool)
    assert isinstance(config["skill_root_exists"], bool)


@pytest.mark.asyncio
async def test_server_health_returns_uptime():
    mcp = FastMCP("test")
    register(mcp)

    tool_fn = None
    for name, fn in mcp._tool_manager._tools.items():
        if name == "server_health":
            tool_fn = fn
            break

    result = await tool_fn.fn(action="check")
    data = result["data"]
    assert "uptime_seconds" in data
    assert data["uptime_seconds"] >= 0
    assert "tools_count" in data
    assert data["tools_count"] >= 1
    assert "resources_count" in data
    assert data["resources_count"] >= 0
