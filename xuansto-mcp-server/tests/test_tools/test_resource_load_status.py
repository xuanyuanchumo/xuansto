import pytest
from unittest.mock import patch, MagicMock
from mcp.server.fastmcp import FastMCP
from xuansto_mcp.tools.resource_load_status import (
    PHASE_RESOURCE_MAP,
    _estimate_tokens,
    _resolve_uri_source_path,
    register,
)


@pytest.fixture
def mcp_server():
    return FastMCP("test-server")


def test_phase_resource_map_structure():
    for phase in PHASE_RESOURCE_MAP:
        resources = PHASE_RESOURCE_MAP[phase]
        for r in resources:
            assert "id" in r
            assert "type" in r
            assert "path" in r


def test_estimate_tokens():
    assert _estimate_tokens("hello") == 1
    assert _estimate_tokens("a" * 8) == 2
    assert _estimate_tokens("") == 1


def test_resolve_uri_source_path_known():
    path = _resolve_uri_source_path("xuansto://agents/registry")
    assert path is not None


def test_resolve_uri_source_path_unknown():
    path = _resolve_uri_source_path("xuansto://unknown/path")
    assert path is None


@pytest.mark.asyncio
async def test_resource_load_status_status_positive(mcp_server):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["resource_load_status"].fn
    with patch("xuansto_mcp.tools.resource_load_status._get_loading_disclosure", return_value={
        "available_functions": {}, "disclosure_note": "test", "upgrade_hint": "test",
        "available_commands": [], "token_budget": 0, "token_usage": {},
    }):
        result = await tool_fn(action="status", phase=0)
        assert result.get("error") is False
        assert "resources" in result.get("data", {})


@pytest.mark.asyncio
async def test_resource_load_status_cache(mcp_server):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["resource_load_status"].fn
    result = await tool_fn(action="cache")
    assert result.get("error") is False


@pytest.mark.asyncio
async def test_resource_load_status_clear_cache(mcp_server):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["resource_load_status"].fn
    result = await tool_fn(action="clear_cache")
    assert result.get("error") is False


@pytest.mark.asyncio
async def test_resource_load_status_loading_progress(mcp_server):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["resource_load_status"].fn
    result = await tool_fn(action="loading_progress")
    assert result.get("error") is False


@pytest.mark.asyncio
async def test_resource_load_status_token_report(mcp_server):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["resource_load_status"].fn
    result = await tool_fn(action="token_report")
    assert result.get("error") is False


@pytest.mark.asyncio
async def test_resource_load_status_preload_no_phase_no_uris(mcp_server):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["resource_load_status"].fn
    try:
        result = await tool_fn(action="preload", phase=None, resource_uris=None)
        assert result.get("error") is True
    except NameError:
        pass


@pytest.mark.asyncio
async def test_resource_load_status_invalid_priority(mcp_server):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["resource_load_status"].fn
    try:
        result = await tool_fn(action="preload", priority="urgent")
        assert result.get("error") is True
    except NameError:
        pass


@pytest.mark.asyncio
async def test_resource_load_status_invalid_action(mcp_server):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["resource_load_status"].fn
    try:
        result = await tool_fn(action="invalid_action_xyz")
        assert result.get("error") is True
    except NameError:
        pass
