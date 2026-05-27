from __future__ import annotations

import pytest

from xuansto_mcp.core.metrics import MetricsCollector, get_metrics_collector
from xuansto_mcp.tools.server_health import record_tool_call


@pytest.fixture(autouse=True)
def _reset_metrics_collector():
    collector = get_metrics_collector()
    collector.reset()
    yield
    collector.reset()


def test_tool_metrics_not_in_server_health_module():
    import xuansto_mcp.tools.server_health as sh_mod
    assert not hasattr(sh_mod, "_TOOL_METRICS"), (
        "_TOOL_METRICS should be removed from server_health module"
    )


def test_record_tool_call_writes_to_metrics_collector():
    collector = get_metrics_collector()
    record_tool_call("test_tool", 12.5, True)
    record_tool_call("test_tool", 25.0, False)
    summary = collector.get_tool_summary()
    assert "test_tool" in summary
    assert summary["test_tool"]["call_count"] == 2
    assert summary["test_tool"]["failure_count"] == 1


def test_check_action_reads_from_metrics_collector():
    collector = get_metrics_collector()
    collector.record_tool_call("check_tool", 50.0, True)
    collector.record_tool_call("check_tool", 100.0, False)
    summary = collector.get_tool_summary()
    assert "check_tool" in summary
    assert summary["check_tool"]["call_count"] == 2
    assert summary["check_tool"]["failure_count"] == 1
    assert summary["check_tool"]["success_count"] == 1


def test_metrics_report_uses_collector_not_tool_metrics():
    from xuansto_mcp.tools.metrics_report import _summary_metrics, _evaluate_metrics
    collector = get_metrics_collector()
    collector.record_tool_call("report_tool", 30.0, True)
    collector.record_tool_call("report_tool", 60.0, False)
    summary_result = _summary_metrics("all")
    assert summary_result["total_calls"] >= 2
    assert summary_result["total_errors"] >= 1
    eval_result = _evaluate_metrics("all")
    assert eval_result["total_calls"] >= 2
    assert eval_result["total_errors"] >= 1


def test_metrics_collector_is_singleton():
    c1 = get_metrics_collector()
    c2 = get_metrics_collector()
    assert c1 is c2


def test_record_tool_call_and_collector_share_data():
    collector = get_metrics_collector()
    record_tool_call("shared_tool", 15.0, True)
    summary = collector.get_tool_summary()
    assert "shared_tool" in summary
    assert summary["shared_tool"]["call_count"] == 1
