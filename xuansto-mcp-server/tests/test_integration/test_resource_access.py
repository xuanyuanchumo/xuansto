import pytest
from unittest.mock import patch, MagicMock
from mcp.server.fastmcp import FastMCP


@pytest.fixture
def mcp_server():
    return FastMCP("test-resources")


@pytest.mark.asyncio
async def test_resource_load_status_status_action(mcp_server):
    from xuansto_mcp.tools.resource_load_status import register
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["resource_load_status"].fn
    with patch("xuansto_mcp.tools.resource_load_status._get_loading_disclosure", return_value={
        "available_functions": {}, "disclosure_note": "test", "upgrade_hint": "test",
        "available_commands": [], "token_budget": 0, "token_usage": {},
    }):
        result = await tool_fn(action="status", phase=0)
        assert result.get("error") is False
        data = result["data"]
        assert "resources" in data
        assert len(data["resources"]) > 0
        for r in data["resources"]:
            assert "id" in r
            assert "status" in r
            assert "type" in r


@pytest.mark.asyncio
async def test_resource_load_status_all_phases(mcp_server):
    from xuansto_mcp.tools.resource_load_status import register
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["resource_load_status"].fn
    with patch("xuansto_mcp.tools.resource_load_status._get_loading_disclosure", return_value={
        "available_functions": {}, "disclosure_note": "test", "upgrade_hint": "test",
        "available_commands": [], "token_budget": 0, "token_usage": {},
    }):
        result = await tool_fn(action="status")
        assert result.get("error") is False
        data = result["data"]
        assert data["total"] > 0


@pytest.mark.asyncio
async def test_resource_cache_action(mcp_server):
    from xuansto_mcp.tools.resource_load_status import register
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["resource_load_status"].fn
    result = await tool_fn(action="cache")
    assert result.get("error") is False
    data = result["data"]
    assert "cached_uris" in data
    assert "cache_size" in data
    assert "total_entries" in data


@pytest.mark.asyncio
async def test_resource_clear_cache_action(mcp_server):
    from xuansto_mcp.tools.resource_load_status import register
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["resource_load_status"].fn
    result = await tool_fn(action="clear_cache")
    assert result.get("error") is False
    data = result["data"]
    assert "cleared_entries" in data


@pytest.mark.asyncio
async def test_resource_loading_progress_action(mcp_server):
    from xuansto_mcp.tools.resource_load_status import register
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["resource_load_status"].fn
    result = await tool_fn(action="loading_progress")
    assert result.get("error") is False
    data = result["data"]
    assert "progress_percent" in data
    assert "loading" in data


@pytest.mark.asyncio
async def test_resource_token_report_action(mcp_server):
    from xuansto_mcp.tools.resource_load_status import register
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["resource_load_status"].fn
    result = await tool_fn(action="token_report")
    assert result.get("error") is False
    data = result["data"]
    assert "tools" in data
    assert "summary" in data


@pytest.mark.asyncio
async def test_resource_preload_with_uris(mcp_server):
    from xuansto_mcp.tools.resource_load_status import register
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["resource_load_status"].fn
    with patch("xuansto_mcp.tools.resource_load_status._read_resource_content", return_value={"content": "test", "truncated": False, "skipped_large_files": []}), \
         patch("xuansto_mcp.tools.resource_load_status._is_cache_valid", return_value=(False, "not_cached")), \
         patch("xuansto_mcp.tools.resource_load_status._resolve_uri_source_path", return_value=None), \
         patch("xuansto_mcp.tools.resource_load_status._compute_path_hash", return_value="abc"):
        result = await tool_fn(action="preload", resource_uris=["xuansto://agents/registry"])
        assert result.get("error") is False
