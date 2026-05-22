import sys
import pytest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from xuansto_mcp.tools.resource_load_status import _LOADED_PROGRESS, _RESOURCE_CACHE, register


@pytest.fixture
def tool_fn():
    from mcp.server.fastmcp import FastMCP
    test_mcp = FastMCP("test")
    register(test_mcp)
    return test_mcp._tool_manager._tools["resource_load_status"].fn


@pytest.fixture(autouse=True)
def reset_progress():
    import xuansto_mcp.tools.resource_load_status as mod
    mod._LOADED_PROGRESS["total_resources"] = 0
    mod._LOADED_PROGRESS["loaded_resources"] = 0
    mod._LOADED_PROGRESS["current_phase"] = None
    mod._LOADED_PROGRESS["loading"] = False
    mod._LOADED_PROGRESS["started_at"] = None
    mod._LOADED_PROGRESS["completed_at"] = None
    _RESOURCE_CACHE.clear()
    yield


@pytest.mark.asyncio
async def test_loading_progress_action_exists(tool_fn):
    result = await tool_fn(action="loading_progress")
    assert result is not None
    data = result.get("data", result)
    assert data.get("action") == "loading_progress"


@pytest.mark.asyncio
async def test_loading_progress_returns_fields(tool_fn):
    result = await tool_fn(action="loading_progress")
    data = result.get("data", result)
    required_fields = [
        "total_resources",
        "loaded_resources",
        "progress_percent",
        "current_phase",
        "loading",
        "started_at",
        "completed_at",
    ]
    for field in required_fields:
        assert field in data, f"Missing field: {field}"


@pytest.mark.asyncio
async def test_loading_progress_initial_state(tool_fn):
    result = await tool_fn(action="loading_progress")
    data = result.get("data", result)
    assert data["total_resources"] == 0
    assert data["loaded_resources"] == 0
    assert data["progress_percent"] == 0
    assert data["current_phase"] is None
    assert data["loading"] is False
    assert data["started_at"] is None
    assert data["completed_at"] is None


@pytest.mark.asyncio
async def test_loading_progress_after_preload(tool_fn):
    result = await tool_fn(action="preload", resource_uris=["xuansto://agents/registry"])
    assert result is not None

    progress_result = await tool_fn(action="loading_progress")
    data = progress_result.get("data", progress_result)
    assert data["total_resources"] == 1
    assert data["loaded_resources"] == 1
    assert data["loading"] is False
    assert data["started_at"] is not None
    assert data["completed_at"] is not None


@pytest.mark.asyncio
async def test_loading_progress_percent_calculation(tool_fn):
    import xuansto_mcp.tools.resource_load_status as mod

    mod._LOADED_PROGRESS["total_resources"] = 4
    mod._LOADED_PROGRESS["loaded_resources"] = 2

    result = await tool_fn(action="loading_progress")
    data = result.get("data", result)
    assert data["progress_percent"] == 50.0

    mod._LOADED_PROGRESS["loaded_resources"] = 3
    result = await tool_fn(action="loading_progress")
    data = result.get("data", result)
    assert data["progress_percent"] == 75.0

    mod._LOADED_PROGRESS["total_resources"] = 0
    mod._LOADED_PROGRESS["loaded_resources"] = 0
    result = await tool_fn(action="loading_progress")
    data = result.get("data", result)
    assert data["progress_percent"] == 0
