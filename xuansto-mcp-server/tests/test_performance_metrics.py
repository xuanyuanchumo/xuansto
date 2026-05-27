import pytest
from mcp.server.fastmcp import FastMCP

from xuansto_mcp.tools.server_health import (
    record_tool_call,
    register,
)
from xuansto_mcp.core.metrics import get_metrics_collector, MetricsCollector


@pytest.fixture(autouse=True)
def _clear_metrics():
    mc = get_metrics_collector()
    with mc._lock:
        mc._tool_metrics.clear()
    yield
    with mc._lock:
        mc._tool_metrics.clear()


def test_record_tool_call_updates_metrics_correctly():
    mc = get_metrics_collector()
    record_tool_call("tool_a", 10.5, True)
    with mc._lock:
        assert "tool_a" in mc._tool_metrics
        assert mc._tool_metrics["tool_a"]["call_count"] == 1
        assert mc._tool_metrics["tool_a"]["failure_count"] == 0
        assert mc._tool_metrics["tool_a"]["latency_samples"] == [10.5]


def test_record_tool_call_tracks_errors():
    mc = get_metrics_collector()
    record_tool_call("tool_b", 20.0, True)
    record_tool_call("tool_b", 30.0, False)
    with mc._lock:
        assert mc._tool_metrics["tool_b"]["call_count"] == 2
        assert mc._tool_metrics["tool_b"]["failure_count"] == 1
        assert mc._tool_metrics["tool_b"]["latency_samples"] == [20.0, 30.0]


def test_record_tool_call_multiple_tools():
    mc = get_metrics_collector()
    record_tool_call("tool_x", 5.0, True)
    record_tool_call("tool_y", 15.0, False)
    with mc._lock:
        assert "tool_x" in mc._tool_metrics
        assert "tool_y" in mc._tool_metrics
        assert mc._tool_metrics["tool_x"]["call_count"] == 1
        assert mc._tool_metrics["tool_y"]["call_count"] == 1
        assert mc._tool_metrics["tool_y"]["failure_count"] == 1


def test_calculate_percentile_empty_list():
    assert MetricsCollector._percentile([], 50) == 0.0


def test_calculate_percentile_single_value():
    assert MetricsCollector._percentile([42.0], 50) == 42.0
    assert MetricsCollector._percentile([42.0], 99) == 42.0


def test_calculate_percentile_p50():
    values = [10.0, 20.0, 30.0, 40.0, 50.0]
    result = MetricsCollector._percentile(values, 50)
    assert result == 30.0


def test_calculate_percentile_p95():
    values = list(range(1, 101))
    result = MetricsCollector._percentile(values, 95)
    assert 94.0 <= result <= 96.0


def test_calculate_percentile_p99():
    values = list(range(1, 101))
    result = MetricsCollector._percentile(values, 99)
    assert 98.0 <= result <= 100.0


def test_latencies_bounded_to_1000():
    mc = get_metrics_collector()
    for i in range(1500):
        record_tool_call("bounded_tool", float(i), True)
    with mc._lock:
        assert len(mc._tool_metrics["bounded_tool"]["latency_samples"]) == 1000
        assert mc._tool_metrics["bounded_tool"]["latency_samples"][0] == 500.0
        assert mc._tool_metrics["bounded_tool"]["latency_samples"][-1] == 1499.0
        assert mc._tool_metrics["bounded_tool"]["call_count"] == 1500


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

    result = await tool_fn.fn(action="check")
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

    result = await tool_fn.fn(action="check")
    data = result["data"]
    assert "performance_metrics" in data
    assert data["performance_metrics"] == {}
