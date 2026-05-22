import pytest
from mcp.server.fastmcp import FastMCP

from xuansto_mcp.tools.server_health import (
    _TOOL_METRICS,
    _calculate_percentile,
    record_tool_call,
    register,
)


@pytest.fixture(autouse=True)
def _clear_metrics():
    _TOOL_METRICS.clear()
    yield
    _TOOL_METRICS.clear()


def test_record_tool_call_updates_metrics_correctly():
    record_tool_call("tool_a", 10.5, True)
    assert "tool_a" in _TOOL_METRICS
    assert _TOOL_METRICS["tool_a"]["call_count"] == 1
    assert _TOOL_METRICS["tool_a"]["error_count"] == 0
    assert _TOOL_METRICS["tool_a"]["latencies"] == [10.5]


def test_record_tool_call_tracks_errors():
    record_tool_call("tool_b", 20.0, True)
    record_tool_call("tool_b", 30.0, False)
    assert _TOOL_METRICS["tool_b"]["call_count"] == 2
    assert _TOOL_METRICS["tool_b"]["error_count"] == 1
    assert _TOOL_METRICS["tool_b"]["latencies"] == [20.0, 30.0]


def test_record_tool_call_multiple_tools():
    record_tool_call("tool_x", 5.0, True)
    record_tool_call("tool_y", 15.0, False)
    assert "tool_x" in _TOOL_METRICS
    assert "tool_y" in _TOOL_METRICS
    assert _TOOL_METRICS["tool_x"]["call_count"] == 1
    assert _TOOL_METRICS["tool_y"]["call_count"] == 1
    assert _TOOL_METRICS["tool_y"]["error_count"] == 1


def test_calculate_percentile_empty_list():
    assert _calculate_percentile([], 50) == 0.0


def test_calculate_percentile_single_value():
    assert _calculate_percentile([42.0], 50) == 42.0
    assert _calculate_percentile([42.0], 99) == 42.0


def test_calculate_percentile_p50():
    values = [10.0, 20.0, 30.0, 40.0, 50.0]
    result = _calculate_percentile(values, 50)
    assert result == 30.0


def test_calculate_percentile_p95():
    values = list(range(1, 101))
    result = _calculate_percentile(values, 95)
    assert result == 95.0


def test_calculate_percentile_p99():
    values = list(range(1, 101))
    result = _calculate_percentile(values, 99)
    assert result == 99.0


def test_latencies_bounded_to_1000():
    for i in range(1500):
        record_tool_call("bounded_tool", float(i), True)
    assert len(_TOOL_METRICS["bounded_tool"]["latencies"]) == 1000
    assert _TOOL_METRICS["bounded_tool"]["latencies"][0] == 500.0
    assert _TOOL_METRICS["bounded_tool"]["latencies"][-1] == 1499.0
    assert _TOOL_METRICS["bounded_tool"]["call_count"] == 1500


@pytest.mark.asyncio
async def test_server_health_includes_performance_metrics():
    mcp = FastMCP("test")
    register(mcp)

    record_tool_call("sample_tool", 100.0, True)
    record_tool_call("sample_tool", 200.0, False)

    tool_fn = None
    for name, fn in mcp._tool_manager._tools.items():
        if name == "server_health":
            tool_fn = fn
            break

    result = await tool_fn.fn()
    data = result["data"]
    assert "performance_metrics" in data
    pm = data["performance_metrics"]
    assert "sample_tool" in pm
    assert pm["sample_tool"]["call_count"] == 2
    assert pm["sample_tool"]["error_count"] == 1
    assert pm["sample_tool"]["error_rate"] == 0.5
    assert "latency_p50_ms" in pm["sample_tool"]
    assert "latency_p95_ms" in pm["sample_tool"]
    assert "latency_p99_ms" in pm["sample_tool"]


@pytest.mark.asyncio
async def test_server_health_empty_performance_metrics():
    mcp = FastMCP("test")
    register(mcp)

    tool_fn = None
    for name, fn in mcp._tool_manager._tools.items():
        if name == "server_health":
            tool_fn = fn
            break

    result = await tool_fn.fn()
    data = result["data"]
    assert "performance_metrics" in data
    assert data["performance_metrics"] == {}
