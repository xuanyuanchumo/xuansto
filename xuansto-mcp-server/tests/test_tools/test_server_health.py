import pytest
from unittest.mock import patch, MagicMock
from mcp.server.fastmcp import FastMCP
from xuansto_mcp.tools.server_health import (
    _check_chromadb_health,
    _negotiate_api_version,
    record_tool_call,
    register,
)
from xuansto_mcp.core.metrics import get_metrics_collector, MetricsCollector


@pytest.fixture
def mcp_server():
    return FastMCP("test-server")


def test_calculate_percentile_empty():
    assert MetricsCollector._percentile([], 50) == 0.0


def test_calculate_percentile_single():
    assert MetricsCollector._percentile([100.0], 50) == 100.0


def test_calculate_percentile_multiple():
    values = [10.0, 20.0, 30.0, 40.0, 50.0]
    p50 = MetricsCollector._percentile(values, 50)
    assert 20.0 <= p50 <= 40.0


def test_negotiate_api_version_major_match():
    from xuansto_mcp.core.config import MCP_API_VERSION
    major = MCP_API_VERSION.split(".")[0]
    result = _negotiate_api_version(f"{major}.0.0")
    assert result["compatible"] is True


def test_negotiate_api_version_mismatch():
    result = _negotiate_api_version("99.0.0")
    assert result["compatible"] is False


def test_negotiate_api_version_invalid():
    result = _negotiate_api_version("not_a_version")
    assert result["compatible"] is False


def test_check_chromadb_health_not_installed():
    with patch.dict("sys.modules", {"chromadb": None}):
        with patch("xuansto_mcp.tools.server_health._metrics_lock"):
            result = _check_chromadb_health()
            assert result["available"] is False


def test_record_tool_call():
    mc = get_metrics_collector()
    with mc._lock:
        mc._tool_metrics.clear()
    record_tool_call("test_tool", 50.0, True)
    with mc._lock:
        assert "test_tool" in mc._tool_metrics
        assert mc._tool_metrics["test_tool"]["call_count"] == 1


@pytest.mark.asyncio
async def test_server_health_check_positive(mcp_server):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["server_health"].fn
    with patch("xuansto_mcp.tools.server_health._check_chromadb_health", return_value={"available": False, "latency_ms": 0}), \
         patch("xuansto_mcp.tools.workflow_dispatch._load_all_workflows", return_value={}), \
         patch("xuansto_mcp.tools.workflow_dispatch._cleanup_all_snapshots", return_value={}):
        result = await tool_fn(action="check")
        assert result["status"] == "success"
        assert result["data"]["status"] == "healthy"


@pytest.mark.asyncio
async def test_server_health_negotiate_version_positive(mcp_server):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["server_health"].fn
    result = await tool_fn(action="negotiate_version", client_version="1.0.0")
    assert result["status"] == "success"
    assert "compatible" in result.get("data", {})


@pytest.mark.asyncio
async def test_server_health_negotiate_no_version(mcp_server):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["server_health"].fn
    result = await tool_fn(action="negotiate_version", client_version=None)
    assert result["status"] == "error"


@pytest.mark.asyncio
async def test_server_health_unknown_action_returns_check(mcp_server):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["server_health"].fn
    with patch("xuansto_mcp.tools.server_health._check_chromadb_health", return_value={"available": False, "latency_ms": 0}), \
         patch("xuansto_mcp.tools.workflow_dispatch._load_all_workflows", return_value={}), \
         patch("xuansto_mcp.tools.workflow_dispatch._cleanup_all_snapshots", return_value={}):
        result = await tool_fn(action="check")
        assert result["status"] == "success"
