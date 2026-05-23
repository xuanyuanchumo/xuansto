from __future__ import annotations

import json
import threading
import time
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from ..core.config import WORK_DIR
from ..core.errors import make_error_response, make_success_response, ERR_VALIDATION
from ..core.logging_config import get_logger
from ..core.validator import validate_input
from ..models.schemas import MetricsReportInput

logger = get_logger("metrics_report")

_metrics_lock = threading.Lock()


def _load_persisted_metrics() -> dict[str, dict[str, Any]]:
    metrics_path = WORK_DIR / "tool_metrics.json"
    try:
        raw = json.loads(metrics_path.read_text(encoding="utf-8"))
        return raw
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def _load_degradation_stats() -> dict[str, int]:
    degr_path = WORK_DIR / "degradation_stats.json"
    try:
        data = json.loads(degr_path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def _calculate_percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    sorted_values = sorted(values)
    n = len(sorted_values)
    rank = percentile / 100.0 * (n - 1)
    lower = int(rank)
    upper = min(lower + 1, n - 1)
    fraction = rank - lower
    result = sorted_values[lower] + fraction * (sorted_values[upper] - sorted_values[lower])
    return round(result, 1)


_TIME_RANGE_SECONDS: dict[str, float] = {
    "1h": 3600.0,
    "6h": 21600.0,
    "24h": 86400.0,
    "7d": 604800.0,
    "all": 0.0,
}


def _query_metrics(tool_name: str | None, time_range: str, metric_type: str) -> dict[str, Any]:
    try:
        from .server_health import _TOOL_METRICS, _metrics_lock as health_lock
        with health_lock:
            metrics_snapshot = {
                name: {
                    "call_count": m["call_count"],
                    "error_count": m["error_count"],
                    "latencies": list(m.get("latencies", [])),
                }
                for name, m in _TOOL_METRICS.items()
            }
    except ImportError:
        metrics_snapshot = _load_persisted_metrics()

    if tool_name:
        if tool_name in metrics_snapshot:
            metrics_snapshot = {tool_name: metrics_snapshot[tool_name]}
        else:
            return {"tools": {}, "total_tools": 0}

    results: dict[str, Any] = {}
    for name, m in metrics_snapshot.items():
        entry: dict[str, Any] = {}
        latencies = m.get("latencies", [])
        if metric_type in ("calls", "all"):
            entry["call_count"] = m.get("call_count", 0)
        if metric_type in ("errors", "all"):
            entry["error_count"] = m.get("error_count", 0)
            call_count = m.get("call_count", 0)
            entry["error_rate"] = round(m.get("error_count", 0) / max(call_count, 1), 4)
        if metric_type in ("latency", "all"):
            entry["latency_p50_ms"] = _calculate_percentile(latencies, 50)
            entry["latency_p95_ms"] = _calculate_percentile(latencies, 95)
            entry["latency_p99_ms"] = _calculate_percentile(latencies, 99)
            entry["latency_avg_ms"] = round(sum(latencies) / len(latencies), 1) if latencies else 0.0
        results[name] = entry

    return {
        "tools": results,
        "total_tools": len(results),
        "time_range": time_range,
        "metric_type": metric_type,
    }


def _summary_metrics(time_range: str) -> dict[str, Any]:
    try:
        from .server_health import _TOOL_METRICS, _DEGRADATION_COUNTS, _metrics_lock as health_lock
        with health_lock:
            metrics_snapshot = dict(_TOOL_METRICS)
            degradation_snapshot = dict(_DEGRADATION_COUNTS)
    except ImportError:
        metrics_snapshot = _load_persisted_metrics()
        degradation_snapshot = _load_degradation_stats()

    total_calls = 0
    total_errors = 0
    all_latencies: list[float] = []
    tool_summaries: list[dict[str, Any]] = []

    for name, m in metrics_snapshot.items():
        calls = m.get("call_count", 0)
        errors = m.get("error_count", 0)
        latencies = m.get("latencies", [])
        total_calls += calls
        total_errors += errors
        all_latencies.extend(latencies)
        tool_summaries.append({
            "tool_name": name,
            "call_count": calls,
            "error_count": errors,
            "error_rate": round(errors / max(calls, 1), 4),
            "latency_p50_ms": _calculate_percentile(latencies, 50),
            "latency_p95_ms": _calculate_percentile(latencies, 95),
        })

    tool_summaries.sort(key=lambda x: x["call_count"], reverse=True)

    return {
        "total_calls": total_calls,
        "total_errors": total_errors,
        "overall_error_rate": round(total_errors / max(total_calls, 1), 4),
        "latency_p50_ms": _calculate_percentile(all_latencies, 50),
        "latency_p95_ms": _calculate_percentile(all_latencies, 95),
        "latency_p99_ms": _calculate_percentile(all_latencies, 99),
        "latency_avg_ms": round(sum(all_latencies) / len(all_latencies), 1) if all_latencies else 0.0,
        "total_tools": len(tool_summaries),
        "top_tools": tool_summaries[:10],
        "degradation_counts": degradation_snapshot,
        "time_range": time_range,
    }


def register(mcp: FastMCP) -> None:
    @mcp.tool(
        annotations=ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        )
    )
    async def metrics_report(
        action: str,
        tool_name: str | None = None,
        time_range: str = "all",
        metric_type: str = "all",
    ) -> dict[str, Any]:
        """指标报告：查询工具调用指标(按工具名/时间/类型)，汇总统计(总调用/错误率/延迟分布/降级计数)。"""
        validated, err = validate_input(MetricsReportInput, action=action, tool_name=tool_name, time_range=time_range, metric_type=metric_type)
        if err:
            return err
        logger.info("metrics_report called: action=%s", action)
        try:
            if action == "query":
                result = _query_metrics(tool_name, time_range, metric_type)
                return make_success_response(result)
            elif action == "summary":
                result = _summary_metrics(time_range)
                return make_success_response(result)
            else:
                return make_error_response(ValueError(f"未知操作: {action}，支持: query, summary"), error_code=ERR_VALIDATION)
        except Exception as e:
            logger.error("metrics_report error: %s", e)
            return make_error_response(e)
