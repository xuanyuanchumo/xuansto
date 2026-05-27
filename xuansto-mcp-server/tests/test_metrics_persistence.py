from __future__ import annotations

import json
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from xuansto_mcp.tools.server_health import (
    _DEGRADATION_COUNTS,
    degradation_load_on_startup,
    metrics_load_on_startup,
    record_tool_call,
    track_degradation,
)
from xuansto_mcp.core.metrics import get_metrics_collector


@pytest.fixture(autouse=True)
def _clear_state(tmp_path, monkeypatch):
    mc = get_metrics_collector()
    with mc._lock:
        mc._tool_metrics.clear()
    _DEGRADATION_COUNTS.clear()
    with mc._lock:
        mc._last_persist_time = 0.0
        mc._persist_count = 0
    monkeypatch.setattr("xuansto_mcp.tools.server_health.WORK_DIR", tmp_path)
    monkeypatch.setattr("xuansto_mcp.core.metrics.WORK_DIR", tmp_path)
    yield
    with mc._lock:
        mc._tool_metrics.clear()
    _DEGRADATION_COUNTS.clear()
    with mc._lock:
        mc._last_persist_time = 0.0
        mc._persist_count = 0


def _reset_persist_state():
    mc = get_metrics_collector()
    with mc._lock:
        mc._last_persist_time = 0.0
        mc._persist_count = 0


def _find_metrics_file(tmp_path: Path) -> Path | None:
    candidates = sorted(tmp_path.glob("metrics_*.json"), reverse=True)
    return candidates[0] if candidates else None


def test_metrics_persisted_after_call_threshold(tmp_path):
    mc = get_metrics_collector()
    _reset_persist_state()
    for i in range(mc._persist_call_threshold):
        record_tool_call("tool_a", float(i), True)
    metrics_path = _find_metrics_file(tmp_path)
    assert metrics_path is not None
    data = json.loads(metrics_path.read_text(encoding="utf-8"))
    assert "tool_metrics" in data
    assert "tool_a" in data["tool_metrics"]
    assert data["tool_metrics"]["tool_a"]["call_count"] == mc._persist_call_threshold


def test_metrics_persisted_after_time_threshold(tmp_path):
    mc = get_metrics_collector()
    _reset_persist_state()
    with mc._lock:
        mc._last_persist_time = time.time() - mc._persist_interval - 1
    record_tool_call("tool_b", 50.0, True)
    metrics_path = _find_metrics_file(tmp_path)
    assert metrics_path is not None
    data = json.loads(metrics_path.read_text(encoding="utf-8"))
    assert "tool_metrics" in data
    assert "tool_b" in data["tool_metrics"]


def test_metrics_recovered_from_disk_on_startup(tmp_path):
    mc = get_metrics_collector()
    ts = "20260101T000000Z"
    metrics_path = tmp_path / f"metrics_{ts}.json"
    metrics_data = {
        "schema_version": 1,
        "persisted_at": "2026-01-01T00:00:00+00:00",
        "tool_metrics": {
            "restored_tool": {
                "call_count": 42,
                "success_count": 39,
                "failure_count": 3,
                "total_latency_ms": 500.0,
                "min_latency_ms": 10.0,
                "max_latency_ms": 30.0,
                "latency_samples": [10.0, 20.0, 30.0],
                "total_input_tokens": 0,
                "total_output_tokens": 0,
            }
        },
        "degradation_events": [],
        "quality_gate_results": [],
        "phase_transitions": [],
    }
    metrics_path.write_text(json.dumps(metrics_data), encoding="utf-8")
    with patch("xuansto_mcp.core.metrics.MetricsCollector._load_metrics_from_db"):
        metrics_load_on_startup()
    with mc._lock:
        assert "restored_tool" in mc._tool_metrics
        assert mc._tool_metrics["restored_tool"]["call_count"] == 42
        assert mc._tool_metrics["restored_tool"]["failure_count"] == 3
        assert mc._tool_metrics["restored_tool"]["latency_samples"] == [10.0, 20.0, 30.0]


def test_degradation_counts_persisted_and_recovered(tmp_path):
    mc = get_metrics_collector()
    _reset_persist_state()
    with mc._lock:
        mc._last_persist_time = time.time() - mc._persist_interval - 1
    track_degradation("degraded_tool")
    degr_path = tmp_path / "degradation_stats.json"
    assert degr_path.exists()
    _DEGRADATION_COUNTS.clear()
    degradation_load_on_startup()
    assert "degraded_tool" in _DEGRADATION_COUNTS
    assert _DEGRADATION_COUNTS["degraded_tool"] == 1


def test_missing_files_do_not_cause_errors(tmp_path):
    mc = get_metrics_collector()
    with mc._lock:
        mc._tool_metrics.clear()
    _DEGRADATION_COUNTS.clear()
    with patch("xuansto_mcp.core.metrics.MetricsCollector._load_metrics_from_db"):
        metrics_load_on_startup()
    degradation_load_on_startup()
    with mc._lock:
        assert len(mc._tool_metrics) == 0
    assert len(_DEGRADATION_COUNTS) == 0


def test_corrupt_json_handled_gracefully(tmp_path):
    mc = get_metrics_collector()
    with mc._lock:
        mc._tool_metrics.clear()
    ts = "20260101T000000Z"
    metrics_path = tmp_path / f"metrics_{ts}.json"
    metrics_path.write_text("{invalid json content", encoding="utf-8")
    degr_path = tmp_path / "degradation_stats.json"
    degr_path.write_text("not json at all!!!", encoding="utf-8")
    with patch("xuansto_mcp.core.metrics.MetricsCollector._load_metrics_from_db"):
        metrics_load_on_startup()
    degradation_load_on_startup()
    with mc._lock:
        assert len(mc._tool_metrics) == 0
    assert len(_DEGRADATION_COUNTS) == 0


def test_throttle_not_every_call_triggers_write(tmp_path):
    _reset_persist_state()
    for i in range(10):
        record_tool_call("throttle_tool", float(i), True)
    metrics_path = _find_metrics_file(tmp_path)
    assert metrics_path is None


def test_should_persist_count_threshold():
    mc = get_metrics_collector()
    _reset_persist_state()
    with mc._lock:
        mc._persist_count = mc._persist_call_threshold - 1
    assert not mc._should_auto_persist()
    with mc._lock:
        mc._persist_count = mc._persist_call_threshold
    assert mc._should_auto_persist()


def test_should_persist_time_threshold():
    mc = get_metrics_collector()
    _reset_persist_state()
    with mc._lock:
        mc._last_persist_time = time.time() - mc._persist_interval - 1
        mc._persist_count = 1
    assert mc._should_auto_persist()


def test_should_persist_no_prior_persist():
    mc = get_metrics_collector()
    _reset_persist_state()
    with mc._lock:
        mc._persist_count = 50
    assert not mc._should_auto_persist()


def test_persist_resets_counters(tmp_path):
    mc = get_metrics_collector()
    _reset_persist_state()
    with mc._lock:
        mc._persist_count = 200
    mc.persist()
    with mc._lock:
        assert mc._persist_count == 0
        assert mc._last_persist_time > 0


def test_degradation_stats_file_name(tmp_path):
    mc = get_metrics_collector()
    _reset_persist_state()
    with mc._lock:
        mc._last_persist_time = time.time() - mc._persist_interval - 1
    track_degradation("tool_x")
    degr_path = tmp_path / "degradation_stats.json"
    assert degr_path.exists()
    assert not (tmp_path / "degradation_counts.json").exists()


def test_metrics_load_handles_missing_fields(tmp_path):
    mc = get_metrics_collector()
    ts = "20260101T000000Z"
    metrics_path = tmp_path / f"metrics_{ts}.json"
    metrics_data = {
        "schema_version": 1,
        "persisted_at": "2026-01-01T00:00:00+00:00",
        "tool_metrics": {
            "partial_tool": {
                "call_count": 5,
            }
        },
        "degradation_events": [],
        "quality_gate_results": [],
        "phase_transitions": [],
    }
    metrics_path.write_text(json.dumps(metrics_data), encoding="utf-8")
    with patch("xuansto_mcp.core.metrics.MetricsCollector._load_metrics_from_db"):
        metrics_load_on_startup()
    with mc._lock:
        assert "partial_tool" in mc._tool_metrics
        assert mc._tool_metrics["partial_tool"]["call_count"] == 5
        assert mc._tool_metrics["partial_tool"]["failure_count"] == 0
        assert mc._tool_metrics["partial_tool"]["latency_samples"] == []
