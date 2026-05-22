from __future__ import annotations

import json
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from xuansto_mcp.tools.server_health import (
    _DEGRADATION_COUNTS,
    _PERSIST_CALL_THRESHOLD,
    _PERSIST_INTERVAL_SEC,
    _TOOL_METRICS,
    _last_metrics_persist_time,
    _metrics_persist_count,
    _persist_metrics,
    _should_persist,
    degradation_load_on_startup,
    metrics_load_on_startup,
    record_tool_call,
    track_degradation,
)


@pytest.fixture(autouse=True)
def _clear_state(tmp_path, monkeypatch):
    _TOOL_METRICS.clear()
    _DEGRADATION_COUNTS.clear()
    monkeypatch.setattr("xuansto_mcp.tools.server_health.WORK_DIR", tmp_path)
    yield
    _TOOL_METRICS.clear()
    _DEGRADATION_COUNTS.clear()


def _reset_persist_state():
    import xuansto_mcp.tools.server_health as mod
    mod._last_metrics_persist_time = 0.0
    mod._metrics_persist_count = 0


def test_metrics_persisted_after_call_threshold(tmp_path):
    _reset_persist_state()
    for i in range(_PERSIST_CALL_THRESHOLD):
        record_tool_call("tool_a", float(i), True)
    metrics_path = tmp_path / "tool_metrics.json"
    assert metrics_path.exists()
    data = json.loads(metrics_path.read_text(encoding="utf-8"))
    assert "tool_a" in data
    assert data["tool_a"]["call_count"] == _PERSIST_CALL_THRESHOLD


def test_metrics_persisted_after_time_threshold(tmp_path):
    import xuansto_mcp.tools.server_health as mod
    _reset_persist_state()
    mod._last_metrics_persist_time = time.time() - _PERSIST_INTERVAL_SEC - 1
    record_tool_call("tool_b", 50.0, True)
    metrics_path = tmp_path / "tool_metrics.json"
    assert metrics_path.exists()
    data = json.loads(metrics_path.read_text(encoding="utf-8"))
    assert "tool_b" in data


def test_metrics_recovered_from_disk_on_startup(tmp_path):
    metrics_path = tmp_path / "tool_metrics.json"
    metrics_data = {
        "restored_tool": {
            "call_count": 42,
            "error_count": 3,
            "latencies": [10.0, 20.0, 30.0],
        }
    }
    metrics_path.write_text(json.dumps(metrics_data), encoding="utf-8")
    metrics_load_on_startup()
    assert "restored_tool" in _TOOL_METRICS
    assert _TOOL_METRICS["restored_tool"]["call_count"] == 42
    assert _TOOL_METRICS["restored_tool"]["error_count"] == 3
    assert _TOOL_METRICS["restored_tool"]["latencies"] == [10.0, 20.0, 30.0]


def test_degradation_counts_persisted_and_recovered(tmp_path):
    _reset_persist_state()
    import xuansto_mcp.tools.server_health as mod
    mod._last_metrics_persist_time = time.time() - _PERSIST_INTERVAL_SEC - 1
    track_degradation("degraded_tool")
    degr_path = tmp_path / "degradation_stats.json"
    assert degr_path.exists()
    _DEGRADATION_COUNTS.clear()
    degradation_load_on_startup()
    assert "degraded_tool" in _DEGRADATION_COUNTS
    assert _DEGRADATION_COUNTS["degraded_tool"] == 1


def test_missing_files_do_not_cause_errors(tmp_path):
    _TOOL_METRICS.clear()
    _DEGRADATION_COUNTS.clear()
    metrics_load_on_startup()
    degradation_load_on_startup()
    assert len(_TOOL_METRICS) == 0
    assert len(_DEGRADATION_COUNTS) == 0


def test_corrupt_json_handled_gracefully(tmp_path):
    metrics_path = tmp_path / "tool_metrics.json"
    metrics_path.write_text("{invalid json content", encoding="utf-8")
    degr_path = tmp_path / "degradation_stats.json"
    degr_path.write_text("not json at all!!!", encoding="utf-8")
    metrics_load_on_startup()
    degradation_load_on_startup()
    assert len(_TOOL_METRICS) == 0
    assert len(_DEGRADATION_COUNTS) == 0


def test_throttle_not_every_call_triggers_write(tmp_path):
    _reset_persist_state()
    for i in range(10):
        record_tool_call("throttle_tool", float(i), True)
    metrics_path = tmp_path / "tool_metrics.json"
    assert not metrics_path.exists()


def test_should_persist_count_threshold():
    import xuansto_mcp.tools.server_health as mod
    _reset_persist_state()
    mod._metrics_persist_count = _PERSIST_CALL_THRESHOLD - 1
    assert not _should_persist()
    mod._metrics_persist_count = _PERSIST_CALL_THRESHOLD
    assert _should_persist()


def test_should_persist_time_threshold():
    import xuansto_mcp.tools.server_health as mod
    _reset_persist_state()
    mod._last_metrics_persist_time = time.time() - _PERSIST_INTERVAL_SEC - 1
    mod._metrics_persist_count = 1
    assert _should_persist()


def test_should_persist_no_prior_persist():
    import xuansto_mcp.tools.server_health as mod
    _reset_persist_state()
    mod._metrics_persist_count = 50
    assert not _should_persist()


def test_persist_resets_counters(tmp_path):
    import xuansto_mcp.tools.server_health as mod
    _reset_persist_state()
    mod._metrics_persist_count = 200
    _persist_metrics()
    assert mod._metrics_persist_count == 0
    assert mod._last_metrics_persist_time > 0


def test_degradation_stats_file_name(tmp_path):
    _reset_persist_state()
    import xuansto_mcp.tools.server_health as mod
    mod._last_metrics_persist_time = time.time() - _PERSIST_INTERVAL_SEC - 1
    track_degradation("tool_x")
    degr_path = tmp_path / "degradation_stats.json"
    assert degr_path.exists()
    assert not (tmp_path / "degradation_counts.json").exists()


def test_metrics_load_handles_missing_fields(tmp_path):
    metrics_path = tmp_path / "tool_metrics.json"
    metrics_data = {
        "partial_tool": {
            "call_count": 5,
        }
    }
    metrics_path.write_text(json.dumps(metrics_data), encoding="utf-8")
    metrics_load_on_startup()
    assert "partial_tool" in _TOOL_METRICS
    assert _TOOL_METRICS["partial_tool"]["call_count"] == 5
    assert _TOOL_METRICS["partial_tool"]["error_count"] == 0
    assert _TOOL_METRICS["partial_tool"]["latencies"] == []
