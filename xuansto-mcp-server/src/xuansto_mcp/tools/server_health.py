from __future__ import annotations

import json
import threading
import time
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from ..core.config import DATA_DIR, SKILL_ROOT, WORK_DIR, KNOWLEDGE_CHROMA_PATH, MCP_API_VERSION, MCP_MIN_SUPPORTED_VERSION, API_CHANGELOG, AGENTS_DIR, REFERENCES_DIR, COMMANDS_DIR
from ..core.errors import make_success_response, make_error_response, ERR_VALIDATION
from ..core import atomic_write
from ..core.logging_config import get_logger
from ..core.validator import validate_input
from ..models.schemas import ServerHealthInput

_START_TIME = time.time()

_PERSIST_INTERVAL_SEC: float = 60.0
_PERSIST_CALL_THRESHOLD: int = 100

_SNAPSHOT_CLEANUP_MIN_INTERVAL: float = 300.0
_last_snapshot_cleanup_time: float = 0.0

_DEGRADATION_COUNTS: dict[str, int] = {}

_CHROMADB_DEGRADATION_KEY = "chromadb_unavailable"

_TOOL_METRICS: dict[str, dict[str, Any]] = {}

_metrics_lock = threading.Lock()
_persist_lock = threading.Lock()

_chromadb_client = None

_last_metrics_persist_time: float = 0.0
_metrics_persist_count: int = 0

logger = get_logger("server_health")


def _check_chromadb_health() -> dict[str, Any]:
    global _chromadb_client
    start = time.monotonic()
    try:
        import chromadb
        if _chromadb_client is None:
            _chromadb_client = chromadb.PersistentClient(path=str(KNOWLEDGE_CHROMA_PATH))
        _chromadb_client.get_or_create_collection("knowledge")
        latency_ms = round((time.monotonic() - start) * 1000, 1)
        with _metrics_lock:
            was_degraded = _DEGRADATION_COUNTS.get(_CHROMADB_DEGRADATION_KEY, 0)
            if was_degraded > 0:
                _DEGRADATION_COUNTS[_CHROMADB_DEGRADATION_KEY] = 0
                logger.info("ChromaDB recovered, cleared degradation mark (was %d)", was_degraded)
        return {"available": True, "latency_ms": latency_ms}
    except ImportError:
        latency_ms = round((time.monotonic() - start) * 1000, 1)
        with _metrics_lock:
            _DEGRADATION_COUNTS[_CHROMADB_DEGRADATION_KEY] = _DEGRADATION_COUNTS.get(_CHROMADB_DEGRADATION_KEY, 0) + 1
            logger.warning("ChromaDB not installed, marked as degraded (count=%d)", _DEGRADATION_COUNTS[_CHROMADB_DEGRADATION_KEY])
        return {"available": False, "latency_ms": latency_ms, "reason": "chromadb not installed"}
    except Exception as exc:
        _chromadb_client = None
        latency_ms = round((time.monotonic() - start) * 1000, 1)
        with _metrics_lock:
            _DEGRADATION_COUNTS[_CHROMADB_DEGRADATION_KEY] = _DEGRADATION_COUNTS.get(_CHROMADB_DEGRADATION_KEY, 0) + 1
            logger.warning("ChromaDB unavailable: %s, marked as degraded (count=%d)", exc, _DEGRADATION_COUNTS[_CHROMADB_DEGRADATION_KEY])
        return {"available": False, "latency_ms": latency_ms, "reason": str(exc)}


def _should_persist() -> bool:
    if _metrics_persist_count >= _PERSIST_CALL_THRESHOLD:
        return True
    if _last_metrics_persist_time == 0.0:
        return False
    if (time.time() - _last_metrics_persist_time) >= _PERSIST_INTERVAL_SEC:
        return True
    return False


def _persist_metrics() -> None:
    global _last_metrics_persist_time, _metrics_persist_count
    with _metrics_lock:
        trimmed = {}
        for tool_name, metrics in _TOOL_METRICS.items():
            trimmed[tool_name] = {
                "call_count": metrics["call_count"],
                "error_count": metrics["error_count"],
                "latencies": metrics["latencies"][-100:],
            }
        degr_snapshot = dict(_DEGRADATION_COUNTS)
    with _persist_lock:
        persist_dir = WORK_DIR
        persist_dir.mkdir(parents=True, exist_ok=True)
        metrics_path = persist_dir / "tool_metrics.json"
        atomic_write(metrics_path, json.dumps(trimmed, ensure_ascii=False, indent=2))
        logger.info("Persisted tool metrics (%d tools) to %s", len(trimmed), metrics_path)
        degr_path = persist_dir / "degradation_stats.json"
        atomic_write(degr_path, json.dumps(degr_snapshot, ensure_ascii=False, indent=2))
        logger.info("Persisted degradation counts (%d tools) to %s", len(degr_snapshot), degr_path)
    with _metrics_lock:
        _last_metrics_persist_time = time.time()
        _metrics_persist_count = 0


def _load_metrics() -> None:
    metrics_load_on_startup()
    degradation_load_on_startup()


def metrics_load_on_startup() -> None:
    metrics_path = WORK_DIR / "tool_metrics.json"
    try:
        raw = json.loads(metrics_path.read_text(encoding="utf-8"))
        with _metrics_lock:
            for tool_name, d in raw.items():
                _TOOL_METRICS[tool_name] = {
                    "call_count": d.get("call_count", 0),
                    "error_count": d.get("error_count", 0),
                    "latencies": d.get("latencies", []),
                }
        logger.info("Loaded tool metrics (%d tools) from %s", len(raw), metrics_path)
    except FileNotFoundError:
        logger.debug("No persisted tool metrics found at %s", metrics_path)
    except json.JSONDecodeError:
        logger.warning("Failed to parse tool metrics from %s; starting fresh", metrics_path)
    except Exception:
        logger.warning("Unexpected error loading tool metrics from %s; starting fresh", metrics_path)


def degradation_load_on_startup() -> None:
    degr_path = WORK_DIR / "degradation_stats.json"
    try:
        data = json.loads(degr_path.read_text(encoding="utf-8"))
        with _metrics_lock:
            _DEGRADATION_COUNTS.update(data)
        logger.info("Loaded degradation counts from %s", degr_path)
    except FileNotFoundError:
        logger.debug("No persisted degradation stats found at %s", degr_path)
    except json.JSONDecodeError:
        logger.warning("Failed to parse degradation stats from %s; starting fresh", degr_path)
    except Exception:
        logger.warning("Unexpected error loading degradation stats from %s; starting fresh", degr_path)


def load_on_startup() -> None:
    _load_metrics()


def track_degradation(tool_name: str) -> None:
    global _metrics_persist_count
    should_persist = False
    with _metrics_lock:
        _DEGRADATION_COUNTS[tool_name] = _DEGRADATION_COUNTS.get(tool_name, 0) + 1
        _metrics_persist_count += 1
        should_persist = _should_persist()
    if should_persist:
        _persist_metrics()


def record_tool_call(tool_name: str, latency_ms: float, success: bool) -> None:
    global _metrics_persist_count
    should_persist = False
    with _metrics_lock:
        if tool_name not in _TOOL_METRICS:
            _TOOL_METRICS[tool_name] = {
                "call_count": 0,
                "error_count": 0,
                "latencies": [],
            }
        metrics = _TOOL_METRICS[tool_name]
        metrics["call_count"] += 1
        if not success:
            metrics["error_count"] += 1
        metrics["latencies"].append(latency_ms)
        if len(metrics["latencies"]) > 1000:
            metrics["latencies"] = metrics["latencies"][-1000:]
        _metrics_persist_count += 1
        should_persist = _should_persist()
    if should_persist:
        _persist_metrics()


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


def _negotiate_api_version(client_version: str) -> dict[str, Any]:
    server_major = MCP_API_VERSION.split(".")[0]
    server_minor = int(MCP_API_VERSION.split(".")[1])
    min_major = MCP_MIN_SUPPORTED_VERSION.split(".")[0]

    def _features_between(low_ver: str, high_ver: str) -> list[str]:
        features: list[str] = []
        for ver, items in API_CHANGELOG.items():
            parts = ver.split(".")
            v_major, v_minor = int(parts[0]), int(parts[1]) if len(parts) > 1 else 0
            low_parts = low_ver.split(".")
            low_maj, low_min = int(low_parts[0]), int(low_parts[1]) if len(low_parts) > 1 else 0
            high_parts = high_ver.split(".")
            high_maj, high_min = int(high_parts[0]), int(high_parts[1]) if len(high_parts) > 1 else 0
            if (v_major, v_minor) > (low_maj, low_min) and (v_major, v_minor) <= (high_maj, high_min):
                features.extend(items)
        return features

    base_result = {
        "server_version": MCP_API_VERSION,
        "client_version": client_version,
        "min_supported_version": MCP_MIN_SUPPORTED_VERSION,
    }

    try:
        client_parts = client_version.split(".")
        client_major = client_parts[0]
        client_minor = int(client_parts[1]) if len(client_parts) > 1 else 0
        if not client_major.isdigit():
            return {
                **base_result,
                "compatible": False,
                "deprecated_features": [],
                "new_features": [],
                "upgrade_suggestion": "Invalid client version format. Please provide a valid semver version.",
            }
    except (ValueError, IndexError):
        return {
            **base_result,
            "compatible": False,
            "deprecated_features": [],
            "new_features": [],
            "upgrade_suggestion": "Invalid client version format. Please provide a valid semver version.",
        }

    client_maj_int = int(client_major)

    if client_maj_int == int(server_major):
        if client_minor < server_minor:
            new_feats = _features_between(client_version, MCP_API_VERSION)
            return {
                **base_result,
                "compatible": True,
                "deprecated_features": [],
                "new_features": new_feats,
                "upgrade_suggestion": f"Client is behind server by minor versions. New features available: {len(new_feats)}. Consider upgrading to {MCP_API_VERSION}.",
            }
        return {
            **base_result,
            "compatible": True,
            "deprecated_features": [],
            "new_features": [],
            "upgrade_suggestion": "Client is up to date with server version.",
        }

    if client_maj_int == int(min_major):
        depr_feats = _features_between(MCP_MIN_SUPPORTED_VERSION, client_version)
        new_feats = _features_between(client_version, MCP_API_VERSION)
        return {
            **base_result,
            "compatible": True,
            "deprecated_features": depr_feats,
            "new_features": new_feats,
            "upgrade_suggestion": f"Client is on minimum supported version. {len(new_feats)} new features available. Upgrade to {MCP_API_VERSION} recommended.",
        }

    if client_maj_int > int(server_major):
        return {
            **base_result,
            "compatible": False,
            "deprecated_features": [],
            "new_features": [],
            "upgrade_suggestion": f"Client version ({client_version}) is newer than server ({MCP_API_VERSION}). Please downgrade client or upgrade server.",
        }

    return {
        **base_result,
        "compatible": False,
        "deprecated_features": [],
        "new_features": _features_between(client_version, MCP_API_VERSION),
        "upgrade_suggestion": f"Major version mismatch. Client ({client_version}) is not compatible with server ({MCP_API_VERSION}). Minimum supported: {MCP_MIN_SUPPORTED_VERSION}.",
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
    async def server_health(action: str, client_version: str | None = None) -> dict[str, Any]:
        """MCP Server 健康检查：返回服务器状态、版本、运行时间、配置路径和工具统计。支持API版本协商。"""
        validated, val_err = validate_input(ServerHealthInput, action=action, client_version=client_version)
        if val_err:
            return val_err
        logger.info("server_health called: action=%s", action)
        try:
            from .. import __version__
            from ..server import _REGISTERED_TOOL_NAMES, _REGISTERED_RESOURCE_NAMES

            if action == "negotiate_version":
                if not client_version:
                    return make_error_response(ValueError("negotiate_version操作需要client_version参数"), error_code=ERR_VALIDATION)
                return make_success_response(_negotiate_api_version(client_version))

            if action == "capabilities":
                from ..server import _REGISTERED_TOOL_NAMES, _REGISTERED_RESOURCE_NAMES, _TOOL_REGISTRY
                tool_capabilities = []
                for tool_name in sorted(_REGISTERED_TOOL_NAMES):
                    tool_fn = _TOOL_REGISTRY.get(tool_name)
                    annotations = None
                    if tool_fn is not None:
                        try:
                            annotations = getattr(tool_fn, "annotations", None)
                        except Exception:
                            pass
                    tool_entry: dict[str, Any] = {"name": tool_name, "available": True}
                    if annotations is not None:
                        try:
                            tool_entry["annotations"] = {
                                "read_only": getattr(annotations, "readOnlyHint", None),
                                "destructive": getattr(annotations, "destructiveHint", None),
                                "idempotent": getattr(annotations, "idempotentHint", None),
                            }
                        except Exception:
                            pass
                    tool_capabilities.append(tool_entry)
                resource_capabilities = []
                for res_name in sorted(_REGISTERED_RESOURCE_NAMES):
                    resource_capabilities.append({"name": res_name, "available": True})
                with _metrics_lock:
                    degradation_snapshot = dict(_DEGRADATION_COUNTS)
                degraded_tools = [k for k, v in degradation_snapshot.items() if v > 0]
                return make_success_response({
                    "tools": tool_capabilities,
                    "tools_count": len(tool_capabilities),
                    "resources": resource_capabilities,
                    "resources_count": len(resource_capabilities),
                    "degraded_tools": degraded_tools,
                    "api_version": MCP_API_VERSION,
                })

            from .workflow_dispatch import _load_all_workflows, _cleanup_all_snapshots

            active_workflows = len(_load_all_workflows())
            global _last_snapshot_cleanup_time
            snapshot_cleanup: dict[str, dict[str, Any]] = {}
            if time.time() - _last_snapshot_cleanup_time >= _SNAPSHOT_CLEANUP_MIN_INTERVAL:
                snapshot_cleanup = _cleanup_all_snapshots()
                _last_snapshot_cleanup_time = time.time()
            total_deleted = sum(r["deleted_count"] for r in snapshot_cleanup.values())
            total_remaining = sum(r["remaining_count"] for r in snapshot_cleanup.values())
            performance_metrics = {}
            with _metrics_lock:
                for tool_name, metrics in _TOOL_METRICS.items():
                    latencies = metrics.get("latencies", [])
                    performance_metrics[tool_name] = {
                        "call_count": metrics["call_count"],
                        "error_count": metrics["error_count"],
                        "error_rate": round(metrics["error_count"] / max(metrics["call_count"], 1), 4),
                        "latency_p50_ms": _calculate_percentile(latencies, 50),
                        "latency_p95_ms": _calculate_percentile(latencies, 95),
                        "latency_p99_ms": _calculate_percentile(latencies, 99),
                    }
                degradation_snapshot = dict(_DEGRADATION_COUNTS)
            chromadb_health = _check_chromadb_health()
            tools_count = len(_REGISTERED_TOOL_NAMES) if _REGISTERED_TOOL_NAMES else 13
            resources_count = len(_REGISTERED_RESOURCE_NAMES) if _REGISTERED_RESOURCE_NAMES else 7
            return make_success_response({
                "status": "healthy",
                "version": __version__,
                "api_version": MCP_API_VERSION,
                "api_changelog": API_CHANGELOG,
                "uptime_seconds": round(time.time() - _START_TIME, 1),
                "tools_count": tools_count,
                "resources_count": resources_count,
                "active_workflows": active_workflows,
                "snapshot_cleanup": {
                    "workflows_checked": len(snapshot_cleanup),
                    "total_deleted": total_deleted,
                    "total_remaining": total_remaining,
                },
                "degradation_stats": degradation_snapshot,
                "performance_metrics": performance_metrics,
                "services": {
                    "chromadb": chromadb_health,
                },
                "config": {
                    "data_dir": str(DATA_DIR),
                    "skill_root": str(SKILL_ROOT),
                    "work_dir": str(WORK_DIR),
                    "data_dir_exists": DATA_DIR.exists(),
                    "skill_root_exists": SKILL_ROOT.exists(),
                },
                "path_warnings": [
                    w for w in [
                        {"path": str(KNOWLEDGE_CHROMA_PATH), "exists": KNOWLEDGE_CHROMA_PATH.exists(), "type": "knowledge_chroma"} if not KNOWLEDGE_CHROMA_PATH.exists() else None,
                        {"path": str(AGENTS_DIR), "exists": AGENTS_DIR.exists(), "type": "agents_dir"} if not AGENTS_DIR.exists() else None,
                        {"path": str(REFERENCES_DIR), "exists": REFERENCES_DIR.exists(), "type": "references_dir"} if not REFERENCES_DIR.exists() else None,
                        {"path": str(COMMANDS_DIR), "exists": COMMANDS_DIR.exists(), "type": "commands_dir"} if not COMMANDS_DIR.exists() else None,
                    ] if w is not None
                ],
            })
        except Exception as e:
            logger.error("server_health error: %s", e)
            return make_error_response(e)
