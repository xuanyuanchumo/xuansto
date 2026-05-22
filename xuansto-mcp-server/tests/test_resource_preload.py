import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from xuansto_mcp.tools.resource_load_status import _RESOURCE_CACHE, _read_resource_content


def test_read_resource_content_returns_none_for_unknown():
    result = _read_resource_content("xuansto://unknown/resource")
    assert result is not None
    assert result.get("content") is None


def test_resource_cache_starts_empty():
    _RESOURCE_CACHE.clear()
    assert len(_RESOURCE_CACHE) == 0


@pytest.mark.asyncio
async def test_preload_action():
    from xuansto_mcp.tools.resource_load_status import register
    from mcp.server.fastmcp import FastMCP

    test_mcp = FastMCP("test")
    register(test_mcp)
    tool_fn = test_mcp._tool_manager._tools["resource_load_status"].fn

    _RESOURCE_CACHE.clear()
    result = await tool_fn(action="preload", resource_uris=["xuansto://agents/registry"])
    data = result.get("data", result)
    assert data.get("action") == "preload"
    assert "loaded_count" in data
    assert "total_size_bytes" in data


@pytest.mark.asyncio
async def test_cache_action():
    from xuansto_mcp.tools.resource_load_status import register
    from mcp.server.fastmcp import FastMCP

    test_mcp = FastMCP("test")
    register(test_mcp)
    tool_fn = test_mcp._tool_manager._tools["resource_load_status"].fn

    result = await tool_fn(action="cache")
    data = result.get("data", result)
    assert data.get("action") == "cache"
    assert "cached_uris" in data
    assert "total_entries" in data


@pytest.mark.asyncio
async def test_clear_cache_action():
    from xuansto_mcp.tools.resource_load_status import register
    from mcp.server.fastmcp import FastMCP

    test_mcp = FastMCP("test")
    register(test_mcp)
    tool_fn = test_mcp._tool_manager._tools["resource_load_status"].fn

    _RESOURCE_CACHE["test://uri"] = "test content"
    result = await tool_fn(action="clear_cache")
    data = result.get("data", result)
    assert data.get("action") == "clear_cache"
    assert data.get("cleared_entries", 0) >= 1
    assert len(_RESOURCE_CACHE) == 0
