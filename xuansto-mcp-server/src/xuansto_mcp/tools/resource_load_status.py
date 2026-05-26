from __future__ import annotations

import contextlib
import hashlib
import json
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from ..core import atomic_write
from ..core.cache import LRUCache
from ..core.config import SKILL_ROOT, WORK_DIR
from ..core.errors import ERR_VALIDATION, make_error_response, make_success_response
from ..core.logging_config import get_logger
from ..core.notifications import notify, send_mcp_notification
from ..core.validator import validate_input
from ..models.schemas import DisclosureTransition, ResourceLoadStatusInput

logger = get_logger("resource_load_status")

PHASE_RESOURCE_MAP: dict[int, list[dict[str, str]]] = {
    0: [
        {"id": "skill-config", "type": "config", "path": ".skill-config.yaml"},
    ],
    1: [
        {"id": "agent-registry", "type": "reference", "path": "references/agent-registry.md"},
        {"id": "quality-gates", "type": "reference", "path": "references/quality-gates.md"},
        {"id": "brainstorm-workflow", "type": "workflow", "path": "workflows/brainstorming-workflow.md"},
        {"id": "agent-product-manager", "type": "agent", "path": "agents/product/product-manager.md"},
        {"id": "agent-orchestrator", "type": "agent", "path": "agents/orchestrator/orchestrator.md"},
        {"id": "agent-system-architect", "type": "agent", "path": "agents/product/system-architect.md"},
    ],
    2: [
        {"id": "knowledge-general", "type": "knowledge", "path": ".knowledge/general/"},
        {"id": "sdd-tdd-full", "type": "workflow", "path": "workflows/sdd-tdd-full.md"},
        {"id": "sdd-tdd-medium", "type": "workflow", "path": "workflows/sdd-tdd-medium.md"},
        {"id": "sdd-tdd-fast", "type": "workflow", "path": "workflows/sdd-tdd-fast.md"},
        {"id": "mcp-tools", "type": "reference", "path": "references/mcp-tools.md"},
        {"id": "workflow-phases", "type": "reference", "path": "references/workflow-phases.md"},
        {"id": "agent-registry-full", "type": "agent", "path": "agents/registry.yaml"},
        {"id": "progressive-loading", "type": "reference", "path": "references/progressive-loading.md"},
    ],
    3: [
        {"id": "test-guidelines", "type": "reference", "path": "references/test-guidelines.md"},
        {"id": "coding-standards", "type": "reference", "path": "references/coding-standards.md"},
        {"id": "karpathy-guidelines", "type": "reference", "path": "references/karpathy-guidelines.md"},
        {"id": "security-guidelines", "type": "reference", "path": "references/security-guidelines.md"},
        {"id": "owasp-top10", "type": "reference", "path": "references/owasp-top10-2026.md"},
        {"id": "acceptance-criteria", "type": "reference", "path": "references/acceptance-criteria.md"},
        {"id": "desktop-guidelines", "type": "reference", "path": "references/desktop-dev-guidelines.md"},
        {"id": "ipc-contracts", "type": "reference", "path": "references/ipc-contracts.md"},
        {"id": "knowledge-workflow", "type": "reference", "path": "references/knowledge-workflow-details.md"},
        {"id": "templates-dir", "type": "template", "path": "templates/"},
        {"id": "agents-orchestrator-full", "type": "agent", "path": "agents/orchestrator/"},
        {"id": "agents-product-full", "type": "agent", "path": "agents/product/"},
        {"id": "agents-design-full", "type": "agent", "path": "agents/design/"},
        {"id": "agents-engineering-full", "type": "agent", "path": "agents/engineering/"},
        {"id": "agents-cross-platform-full", "type": "agent", "path": "agents/cross-platform/"},
        {"id": "agents-database-full", "type": "agent", "path": "agents/database/"},
        {"id": "agents-testing-full", "type": "agent", "path": "agents/testing/"},
        {"id": "agents-security-full", "type": "agent", "path": "agents/security/"},
        {"id": "agents-devops-full", "type": "agent", "path": "agents/devops/"},
        {"id": "agents-quality-full", "type": "agent", "path": "agents/quality/"},
        {"id": "agents-documentation-full", "type": "agent", "path": "agents/documentation/"},
        {"id": "agents-knowledge-full", "type": "agent", "path": "agents/knowledge/"},
        {"id": "agents-monitoring-full", "type": "agent", "path": "agents/monitoring/"},
    ],
}

PHASE_TOKEN_BUDGET: dict[int, int] = {
    0: 2000,
    1: 5000,
    2: 10000,
    3: 20000,
}

PHASE_NAME_TOKEN_BUDGET: dict[str, int] = {
    "skeleton": 2000,
    "functional": 5000,
    "enhanced": 10000,
    "full": 20000,
}

PHASE_AVAILABLE_FUNCTIONS: dict[int, dict[str, bool]] = {
    0: {
        "command_routing": True,
        "command_execution": False,
        "quality_gates": False,
        "knowledge_search": False,
        "reference_docs": False,
        "agent_details": False,
        "full_scripts": False,
    },
    1: {
        "command_routing": True,
        "command_execution": True,
        "quality_gates": True,
        "knowledge_search": False,
        "reference_docs": False,
        "agent_details": False,
        "full_scripts": False,
    },
    2: {
        "command_routing": True,
        "command_execution": True,
        "quality_gates": True,
        "knowledge_search": True,
        "reference_docs": True,
        "agent_details": True,
        "full_scripts": False,
    },
    3: {
        "command_routing": True,
        "command_execution": True,
        "quality_gates": True,
        "knowledge_search": True,
        "reference_docs": True,
        "agent_details": True,
        "full_scripts": True,
    },
}

PHASE_RESOURCE_LIST: dict[int, list[str]] = {
    0: [],
    1: ["xuansto://agents/registry"],
    2: ["xuansto://agents/registry", "xuansto://workflows/definitions", "xuansto://gates/definitions"],
    3: ["xuansto://agents/registry", "xuansto://workflows/definitions", "xuansto://gates/definitions", "xuansto://hooks/definitions", "xuansto://templates/"],
}

_PHASE_INHERITS: dict[int, list[int]] = {
    1: [0],
    2: [0, 1],
    3: [0, 1, 2],
}

_LOADED_PROGRESS = {
    "total_resources": 0,
    "loaded_resources": 0,
    "current_phase": None,
    "loading": False,
    "started_at": None,
    "completed_at": None,
}

_loaded_resources: set[str] | None = None

_CACHE_TTL_SECONDS = 3600
_CACHE_MAX_ENTRIES = 100

_resource_lru = LRUCache(maxsize=_CACHE_MAX_ENTRIES)
_RESOURCE_CACHE = _resource_lru

_cache_lock = threading.Lock()

_MAX_RESOURCE_SIZE_BYTES = 10 * 1024 * 1024
_MAX_SINGLE_FILE_BYTES = 1 * 1024 * 1024

_URI_DIR_MAP: dict[str, str] = {
    "xuansto://agents/registry": "agents",
    "xuansto://gates/definitions": "gates",
    "xuansto://hooks/definitions": "hooks",
    "xuansto://workflows/definitions": "workflows",
    "xuansto://templates/": "templates",
}

_LOADING_PHASE_MAP: dict[str, int] = {
    "skeleton": 0,
    "functional": 1,
    "enhanced": 2,
    "full": 3,
}

_LOADING_PHASE_NAMES: dict[int, str] = {v: k for k, v in _LOADING_PHASE_MAP.items()}

PHASE_SKELETON = 0
PHASE_FUNCTIONAL = 1
PHASE_ENHANCED = 2
PHASE_FULL = 3

PHASE_TOKEN_BUDGETS: dict[int, int] = {0: 2000, 1: 5000, 2: 10000, 3: 20000}

PHASE_NAMES: dict[int, str] = {0: "skeleton", 1: "functional", 2: "enhanced", 3: "full"}

PHASE_RESOURCES: dict[int, list[str]] = {
    0: ["skill_core", "triggers", "routes_index", "registry_index"],
    1: ["commands_detail", "workflow_phases", "quality_gates_summary", "core_agents"],
    2: ["agent_registry_full", "knowledge_search", "mcp_tools", "workflow_yaml"],
    3: ["all_agent_definitions", "templates", "scripts_index", "full_references"],
}

_DISCLOSURE_NOTES: dict[int, str] = {
    0: "骨架阶段：仅核心元数据可用，命令路由受限，无Agent详情",
    1: "功能阶段：命令执行和工作流推进可用，知识检索和参考文档需升级到增强阶段",
    2: "增强阶段：知识检索、参考文档、Agent详情可用，完整脚本集和模板需升级到完整阶段",
    3: "完整阶段：全部功能可用，无限制",
}

_UPGRADE_HINTS: dict[int, str] = {
    0: "升级到功能阶段(Phase 1)可解锁：命令执行、工作流推进、门禁检查、核心Agent(Product Manager/Orchestrator/Architect)",
    1: "升级到增强阶段(Phase 2)可解锁：知识检索、参考文档、Agent完整注册表、工作流定义",
    2: "升级到完整阶段(Phase 3)可解锁：完整脚本集、模板库、全部Agent定义、安全/编码/桌面参考文档",
    3: "已达最高阶段，无需升级",
}

PHASE_TRANSITION_CONDITIONS: dict[str, dict[str, Any]] = {
    "skeleton_to_functional": {
        "min_tools_available": 5,
        "min_resources_loaded": 3,
        "description": "核心工具和基础资源已加载",
    },
    "functional_to_enhanced": {
        "min_tools_available": 12,
        "min_resources_loaded": 10,
        "description": "大部分工具和参考文档已加载",
    },
    "enhanced_to_full": {
        "min_tools_available": 20,
        "min_resources_loaded": 18,
        "description": "所有工具、资源和Hook系统已加载",
    },
}

PHASE_AVAILABLE_FEATURES: dict[str, dict[str, list[str]]] = {
    "skeleton": {
        "available": ["/status", "/help", "/budget", "基础状态查询"],
        "unavailable": ["工作流执行", "Agent管理", "知识检索", "代码分析"],
    },
    "functional": {
        "available": ["/init", "/plan", "/implement", "工作流执行", "Agent管理", "知识检索"],
        "unavailable": ["完整参考文档", "Hook系统", "高级分析"],
    },
    "enhanced": {
        "available": ["/review", "/test", "/fix", "完整参考文档", "高级分析"],
        "unavailable": ["Hook系统", "全部配置选项"],
    },
    "full": {
        "available": ["所有31个命令", "Hook系统", "全部配置选项", "完整审计日志"],
        "unavailable": [],
    },
}

_PHASE_TRANSITION_KEYS: dict[int, str] = {
    0: "skeleton_to_functional",
    1: "functional_to_enhanced",
    2: "enhanced_to_full",
}

SKELETON_ALLOWED_COMMANDS = ["/status", "/help", "/budget"]

_PHASE_AVAILABLE_COMMANDS: dict[int, list[str]] = {
    0: list(SKELETON_ALLOWED_COMMANDS),
    1: ["/sprint", "/clarify", "/plan", "/spec", "/design", "/implement", "/test", "/review", "/fix", "/accept", "/deploy", "/build", "/brainstorm", "/execute-plan", "/status", "/agent-status", "/init"],
    2: ["/sprint", "/clarify", "/plan", "/spec", "/design", "/implement", "/test", "/review", "/fix", "/accept", "/deploy", "/build", "/brainstorm", "/execute-plan", "/audit", "/build-desktop", "/release-desktop", "/refactor", "/simplify", "/loop", "/cancel-loop", "/learn", "/design-system", "/rollback", "/status", "/agent-status", "/init"],
    3: ["/sprint", "/clarify", "/plan", "/spec", "/design", "/implement", "/test", "/review", "/fix", "/accept", "/deploy", "/build-desktop", "/release-desktop", "/refactor", "/audit", "/agent-status", "/learn", "/brainstorm", "/execute-plan", "/design-system", "/simplify", "/loop", "/cancel-loop", "/build", "/init", "/status", "/rollback"],
}

_TRANSITION_HISTORY: list[dict[str, Any]] = []

_MAX_TRANSITION_HISTORY = 50

_TOKEN_ESTIMATE_RATIO = 4

_TOKEN_METRICS: dict[str, dict[str, Any]] = {}

_TOKEN_METRICS_LOCK = threading.Lock()

_PHASE_TOKEN_USAGE: dict[int, dict[str, Any]] = {}

_PHASE_TOKEN_USAGE_LOCK = threading.Lock()

_current_phase: int = 0

_phase_lock = threading.RLock()

_phase_state: dict[str, Any] = {
    "phase_metrics": {
        "skeleton": {"tokens_consumed": 0, "load_duration_ms": 0, "resources_loaded": 0},
        "functional": {"tokens_consumed": 0, "load_duration_ms": 0, "resources_loaded": 0},
        "enhanced": {"tokens_consumed": 0, "load_duration_ms": 0, "resources_loaded": 0},
        "full": {"tokens_consumed": 0, "load_duration_ms": 0, "resources_loaded": 0},
    },
    "phase_transition_timestamps": {
        "skeleton": None,
        "functional": None,
        "enhanced": None,
        "full": None,
    },
    "last_transition_at": None,
}


def _get_loading_disclosure() -> dict[str, Any]:
    state_file = WORK_DIR / "resource_state.json"
    current_phase = 0
    if state_file.exists():
        try:
            data = json.loads(state_file.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                phase_val = data.get("phase", "skeleton")
                if isinstance(phase_val, int):
                    current_phase = phase_val
                elif isinstance(phase_val, str):
                    current_phase = _LOADING_PHASE_MAP.get(phase_val, 0)
        except (json.JSONDecodeError, OSError):
            pass
    available_functions = PHASE_AVAILABLE_FUNCTIONS.get(current_phase, PHASE_AVAILABLE_FUNCTIONS[0])
    disclosure_note = _DISCLOSURE_NOTES.get(current_phase, _DISCLOSURE_NOTES[0])
    upgrade_hint = _UPGRADE_HINTS.get(current_phase, _UPGRADE_HINTS[0])
    available_commands = _PHASE_AVAILABLE_COMMANDS.get(current_phase, _PHASE_AVAILABLE_COMMANDS[0])
    token_budget = PHASE_TOKEN_BUDGET.get(current_phase, PHASE_TOKEN_BUDGET[0])
    with _PHASE_TOKEN_USAGE_LOCK:
        phase_usage = _PHASE_TOKEN_USAGE.get(current_phase, {"estimated_tokens": 0, "resource_count": 0})
    if not isinstance(phase_usage, dict):
        phase_usage = {"estimated_tokens": 0, "resource_count": 0}
    phase_usage = {
        "estimated_tokens": _safe_int(phase_usage.get("estimated_tokens")),
        "resource_count": _safe_int(phase_usage.get("resource_count")),
    }
    return {
        "available_functions": available_functions,
        "disclosure_note": disclosure_note,
        "upgrade_hint": upgrade_hint,
        "available_commands": available_commands,
        "token_budget": token_budget,
        "token_usage": phase_usage,
    }


def _get_current_phase_index() -> int:
    state_file = WORK_DIR / "resource_state.json"
    if state_file.exists():
        try:
            data = json.loads(state_file.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                phase_val = data.get("phase", "skeleton")
                if isinstance(phase_val, int):
                    return phase_val
                if isinstance(phase_val, str):
                    return _LOADING_PHASE_MAP.get(phase_val, 0)
        except (json.JSONDecodeError, OSError):
            pass
    return 0


def _get_current_phase_name() -> str:
    return _LOADING_PHASE_NAMES.get(_get_current_phase_index(), "skeleton")


def _phase_index_to_name(phase: int | None) -> str:
    if phase is None:
        return _get_current_phase_name()
    return _LOADING_PHASE_NAMES.get(phase, "skeleton")


def _record_transition(from_phase: str, to_phase: str, resources_affected: list[str], status: str = "completed") -> None:
    transition = DisclosureTransition(
        from_phase=from_phase,
        to_phase=to_phase,
        started_at=datetime.now(timezone.utc).isoformat(),
        completed_at=datetime.now(timezone.utc).isoformat() if status in ("completed", "failed") else None,
        resources_affected=resources_affected,
        status=status,
    )
    with _cache_lock:
        _TRANSITION_HISTORY.append(transition.model_dump())
        if len(_TRANSITION_HISTORY) > _MAX_TRANSITION_HISTORY:
            del _TRANSITION_HISTORY[:len(_TRANSITION_HISTORY) - _MAX_TRANSITION_HISTORY]
    logger.info("DisclosureTransition: %s -> %s (%s, %d resources)", from_phase, to_phase, status, len(resources_affected))


def _estimate_tokens(text: str) -> int:
    return max(1, len(text) // _TOKEN_ESTIMATE_RATIO)


def _safe_int(value: Any, default: int = 0) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, (float, str)):
        try:
            return int(value)
        except (ValueError, TypeError):
            return default
    return default


def _update_phase_token_usage(phase: int, estimated_tokens: int) -> None:
    with _PHASE_TOKEN_USAGE_LOCK:
        if phase not in _PHASE_TOKEN_USAGE:
            _PHASE_TOKEN_USAGE[phase] = {"estimated_tokens": 0, "resource_count": 0}
        _PHASE_TOKEN_USAGE[phase]["estimated_tokens"] = _safe_int(_PHASE_TOKEN_USAGE[phase].get("estimated_tokens")) + estimated_tokens
        _PHASE_TOKEN_USAGE[phase]["resource_count"] = _safe_int(_PHASE_TOKEN_USAGE[phase].get("resource_count")) + 1


def record_token_usage(tool_name: str, input_text: str, output_text: str) -> None:
    input_tokens = _estimate_tokens(input_text)
    output_tokens = _estimate_tokens(output_text)
    with _TOKEN_METRICS_LOCK:
        if tool_name not in _TOKEN_METRICS:
            _TOKEN_METRICS[tool_name] = {
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "call_count": 0,
            }
        metrics = _TOKEN_METRICS[tool_name]
        metrics["total_input_tokens"] = _safe_int(metrics.get("total_input_tokens")) + input_tokens
        metrics["total_output_tokens"] = _safe_int(metrics.get("total_output_tokens")) + output_tokens
        metrics["call_count"] = _safe_int(metrics.get("call_count")) + 1


def _compute_file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _compute_path_hash(path: Path) -> str | None:
    if not path.exists():
        return None
    if path.is_file():
        return _compute_file_hash(path)
    if path.is_dir():
        h = hashlib.sha256()
        for fpath in sorted(path.rglob("*")):
            if fpath.is_file() and fpath.suffix in (".json", ".yaml", ".yml", ".md", ".txt"):
                h.update(_compute_file_hash(fpath).encode("utf-8"))
                h.update(str(fpath.relative_to(path)).encode("utf-8"))
        return h.hexdigest()
    return None


def _resolve_uri_source_path(uri: str) -> Path | None:
    resource_key = _URI_DIR_MAP.get(uri)
    if resource_key is None:
        for prefix in _URI_DIR_MAP:
            if uri.startswith(prefix):
                resource_key = _URI_DIR_MAP[prefix]
                break
    if resource_key is None:
        return None
    return SKILL_ROOT / resource_key


def _is_cache_valid(cache_key: str) -> tuple[bool, str]:
    with _cache_lock:
        entry = _resource_lru.get(cache_key)
        if entry is None:
            return False, "not_cached"
    ttl = entry.get("ttl_seconds", _CACHE_TTL_SECONDS)
    if (time.time() - entry["cached_at"]) > ttl:
        return False, "expired"
    source_path = entry.get("source_path")
    if source_path is not None:
        current_hash = _compute_path_hash(Path(source_path))
        if current_hash is not None and current_hash != entry.get("content_hash"):
            return False, "stale"
    return True, "valid"


def _cleanup_cache() -> None:
    with _cache_lock:
        expired_keys = [
            k for k, v in _resource_lru.items()
            if (time.time() - v["cached_at"]) > v.get("ttl_seconds", _CACHE_TTL_SECONDS)
        ]
        for k in expired_keys:
            _resource_lru.delete(k)


def _read_resource_content(uri: str) -> dict[str, Any]:
    with _cache_lock:
        entry = _resource_lru.get(uri)
        if entry is not None:
            if (time.time() - entry["cached_at"]) > entry.get("ttl_seconds", _CACHE_TTL_SECONDS):
                _resource_lru.delete(uri)
                return {"content": None, "truncated": False, "skipped_large_files": []}
            entry["access_count"] += 1
            return {"content": entry["content"], "truncated": False, "skipped_large_files": []}
    source_path = _resolve_uri_source_path(uri)
    if source_path is None:
        return {"content": None, "truncated": False, "skipped_large_files": []}
    try:
        data_dir = source_path
        if data_dir.is_dir():
            contents: list[str] = []
            total_bytes = 0
            truncated = False
            skipped_large_files: list[str] = []
            for fpath in sorted(data_dir.rglob("*")):
                if fpath.is_file() and fpath.suffix in (".json", ".yaml", ".yml", ".md", ".txt"):
                    file_size = fpath.stat().st_size
                    if file_size > _MAX_SINGLE_FILE_BYTES:
                        skipped_large_files.append(str(fpath))
                        continue
                    if total_bytes + file_size > _MAX_RESOURCE_SIZE_BYTES:
                        truncated = True
                        break
                    contents.append(fpath.read_text(encoding="utf-8"))
                    total_bytes += file_size
            return {
                "content": "\n---\n".join(contents) if contents else None,
                "truncated": truncated,
                "skipped_large_files": skipped_large_files,
            }
    except OSError:
        pass
    return {"content": None, "truncated": False, "skipped_large_files": []}


def _get_state_file() -> Path:
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    return WORK_DIR / "resource_state.json"


def _load_resource_state() -> set[str]:
    state_file = _get_state_file()
    if state_file.exists():
        try:
            data = json.loads(state_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return set()
        if isinstance(data, list):
            _save_resource_state(set(data))
            return set(data)
        if isinstance(data, dict):
            stored_hash = data.get("_hash")
            if stored_hash is not None:
                resources_data = data.get("resources", {})
                computed_hash = hashlib.sha256(json.dumps(resources_data, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
                if computed_hash != stored_hash:
                    logger.warning("Resource state hash mismatch, resetting state")
                    return set()
            else:
                logger.warning("Resource state file has no integrity hash, loading without verification")
            if "resources" in data and isinstance(data["resources"], list):
                loaded = set(data.get("loaded", []))
                for r in data["resources"]:
                    if isinstance(r, str):
                        loaded.add(r)
                _save_resource_state(loaded)
                return loaded
            return set(data.get("loaded", []))
    return set()


def _save_resource_state(state: set[str]) -> None:
    state_file = _get_state_file()
    resource_map = {}
    for rid in sorted(state):
        resource_map[rid] = {"status": "loaded"}
        for pid, res_list in PHASE_RESOURCE_MAP.items():
            for r in res_list:
                if r["id"] == rid:
                    resource_map[rid]["phase"] = pid
                    resource_map[rid]["type"] = r["type"]
                    resource_map[rid]["path"] = r["path"]
                    break
    current_phase = _get_current_phase_index()
    payload = {
        "version": 3,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "phase": _LOADING_PHASE_NAMES.get(current_phase, "skeleton"),
        "loaded": sorted(state),
        "resources": resource_map,
        "_timestamp": time.time(),
    }
    payload["_hash"] = hashlib.sha256(json.dumps(resource_map, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
    atomic_write(state_file, json.dumps(payload, ensure_ascii=False, indent=2))


def _get_loaded_resources() -> set[str]:
    global _loaded_resources
    with _cache_lock:
        if _loaded_resources is None:
            _loaded_resources = _load_resource_state()
        return _loaded_resources


def _set_loaded_resources(resources: set[str]) -> None:
    global _loaded_resources
    with _cache_lock:
        _loaded_resources = resources
    _save_resource_state(resources)


def _check_resource_status(resource_id: str, resource_path: str) -> str:
    with _cache_lock:
        entry = _resource_lru.get(resource_id)
        if entry is not None:
            ttl = entry.get("ttl_seconds", _CACHE_TTL_SECONDS)
            if (time.time() - entry["cached_at"]) > ttl:
                return "expired"
            source_path = entry.get("source_path")
            if source_path is not None:
                current_hash = _compute_path_hash(Path(source_path))
                if current_hash is not None and current_hash != entry.get("content_hash"):
                    return "stale"
            return "loaded"
    if resource_id in _get_loaded_resources():
        return "loaded"
    full_path = SKILL_ROOT / resource_path
    if full_path.exists():
        return "available"
    return "missing"


def _collect_resources_up_to_phase(target_phase: int) -> list[dict[str, str]]:
    seen_ids: set[str] = set()
    result: list[dict[str, str]] = []
    for p in range(target_phase + 1):
        for r in PHASE_RESOURCE_MAP.get(p, []):
            if r["id"] not in seen_ids:
                seen_ids.add(r["id"])
                result.append(r)
    return result


def _estimate_resource_tokens(resource: dict[str, str]) -> int:
    full_path = SKILL_ROOT / resource["path"]
    if not full_path.exists():
        return 0
    try:
        if full_path.is_file():
            return _estimate_tokens(full_path.read_text(encoding="utf-8"))
        if full_path.is_dir():
            total = 0
            for fpath in sorted(full_path.rglob("*")):
                if fpath.is_file() and fpath.suffix in (".json", ".yaml", ".yml", ".md", ".txt"):
                    total += _estimate_tokens(fpath.read_text(encoding="utf-8"))
            return total
    except OSError:
        pass
    return 0


def can_advance_to(target_phase: int) -> bool:
    if target_phase < 0 or target_phase > 3:
        return False
    with _phase_lock:
        return target_phase > _current_phase


def _check_transition_conditions(from_phase: int) -> dict[str, Any]:
    transition_key = _PHASE_TRANSITION_KEYS.get(from_phase)
    if transition_key is None:
        return {"can_transition": True, "conditions_met": True, "missing": [], "description": "已达最高阶段或无需条件"}
    conditions = PHASE_TRANSITION_CONDITIONS.get(transition_key, {})
    min_tools = conditions.get("min_tools_available", 0)
    min_resources = conditions.get("min_resources_loaded", 0)
    description = conditions.get("description", "")
    loaded_resources = _get_loaded_resources()
    loaded_count = len(loaded_resources)
    with _PHASE_TOKEN_USAGE_LOCK:
        tools_snapshot = dict(_PHASE_TOKEN_USAGE)
    tools_available = sum(1 for v in tools_snapshot.values() if isinstance(v, dict) and _safe_int(v.get("resource_count")) > 0)
    missing: list[str] = []
    if loaded_count < min_resources:
        missing.append(f"资源加载不足: 当前{loaded_count}, 需要{min_resources}")
    if tools_available < min_tools:
        missing.append(f"工具可用不足: 当前{tools_available}, 需要{min_tools}")
    can_transition = len(missing) == 0
    return {
        "can_transition": can_transition,
        "conditions_met": can_transition,
        "transition_key": transition_key,
        "description": description,
        "current_tools_available": tools_available,
        "min_tools_available": min_tools,
        "current_resources_loaded": loaded_count,
        "min_resources_loaded": min_resources,
        "missing": missing,
    }


def advance_phase(target_phase: int, force: bool = False) -> dict[str, Any]:
    global _current_phase
    if not can_advance_to(target_phase):
        return {"success": False, "reason": "invalid_target", "current_phase": _current_phase, "target_phase": target_phase}
    with _phase_lock:
        from_phase = _current_phase
        if not force:
            transition_check = _check_transition_conditions(from_phase)
            if not transition_check["can_transition"]:
                return {
                    "success": False,
                    "reason": "conditions_not_met",
                    "current_phase": from_phase,
                    "target_phase": target_phase,
                    "transition_check": transition_check,
                    "hint": "使用 force=True 可跳过条件验证",
                }
        now_iso = datetime.now(timezone.utc).isoformat()
        now_ts = time.time()
        from_name = PHASE_NAMES.get(from_phase, "skeleton")
        to_name = PHASE_NAMES.get(target_phase, "skeleton")
        last_transition_at = _phase_state.get("last_transition_at")
        duration_ms = 0
        if last_transition_at is not None:
            try:
                from datetime import datetime as _dt
                last_dt = _dt.fromisoformat(last_transition_at)
                duration_ms = int((now_ts - last_dt.timestamp()) * 1000)
            except (ValueError, OSError):
                pass
        with _PHASE_TOKEN_USAGE_LOCK:
            phase_usage = dict(_PHASE_TOKEN_USAGE)
        cumulative_tokens = 0
        for v in phase_usage.values():
            if isinstance(v, dict):
                cumulative_tokens += _safe_int(v.get("estimated_tokens"))
        phase_resources = PHASE_RESOURCE_MAP.get(target_phase, [])
        resources_loaded_count = sum(1 for r in phase_resources if r["id"] in _get_loaded_resources())
        _phase_state["phase_metrics"][to_name] = {
            "tokens_consumed": cumulative_tokens,
            "load_duration_ms": duration_ms,
            "resources_loaded": resources_loaded_count,
        }
        _phase_state["phase_transition_timestamps"][to_name] = now_iso
        _phase_state["last_transition_at"] = now_iso
        _current_phase = target_phase
    from_name = PHASE_NAMES.get(from_phase, "skeleton")
    to_name = PHASE_NAMES.get(target_phase, "skeleton")
    resources = PHASE_RESOURCES.get(target_phase, [])
    _record_transition(from_name, to_name, resources, "completed")
    send_mcp_notification("phase_transition", {
        "from": from_name,
        "to": to_name,
        "status": "complete",
        "loaded_resources": resources,
    })
    send_mcp_notification("tools/list_changed", {
        "reason": "phase_transition",
        "from_phase": from_name,
        "to_phase": to_name,
    })
    notify(f"Phase advanced: {from_name} -> {to_name}", "info")
    new_budget = PHASE_TOKEN_BUDGET.get(target_phase, PHASE_TOKEN_BUDGET[3])
    try:
        from .token_budget import _set_budget
        budget_result = _set_budget(total_budget=new_budget)
        logger.info("Token budget auto-updated on phase advance to %s: %d", to_name, new_budget)
        notify(f"Token budget auto-set to {new_budget} for phase {to_name}", "info")
    except Exception as exc:
        budget_result = {"error": str(exc)}
        logger.warning("Failed to auto-update token budget on phase advance: %s", exc)
    state_file = _get_state_file()
    try:
        state_data = json.loads(state_file.read_text(encoding="utf-8")) if state_file.exists() else {}
        state_data["phase"] = to_name
        atomic_write(state_file, json.dumps(state_data, ensure_ascii=False, indent=2))
    except (json.JSONDecodeError, OSError):
        pass
    from_features = PHASE_AVAILABLE_FEATURES.get(from_name, {})
    to_features = PHASE_AVAILABLE_FEATURES.get(to_name, {})
    newly_available = [f for f in to_features.get("available", []) if f not in from_features.get("available", [])]
    still_unavailable = to_features.get("unavailable", [])
    result = {
        "success": True,
        "from_phase": from_name,
        "to_phase": to_name,
        "loaded_resources": resources,
        "newly_available": newly_available,
        "still_unavailable": still_unavailable,
        "phase_metrics": _phase_state["phase_metrics"].get(to_name, {}),
    }
    if isinstance(budget_result, dict) and "error" not in budget_result:
        result["token_budget_update"] = budget_result
    return result


def degrade_phase() -> dict[str, Any]:
    global _current_phase
    with _phase_lock:
        if _current_phase <= 0:
            return {"success": False, "reason": "already_at_minimum", "current_phase": _current_phase}
        from_phase = _current_phase
        _current_phase -= 1
        to_phase = _current_phase
    from_name = PHASE_NAMES.get(from_phase, "skeleton")
    to_name = PHASE_NAMES.get(to_phase, "skeleton")
    _record_transition(from_name, to_name, [], "completed")
    send_mcp_notification("phase_degradation", {
        "from": from_name,
        "to": to_name,
        "reason": "token_budget",
    })
    send_mcp_notification("tools/list_changed", {
        "reason": "phase_degradation",
        "from_phase": from_name,
        "to_phase": to_name,
    })
    notify(f"Phase degraded: {from_name} -> {to_name} (token budget)", "warning")
    state_file = _get_state_file()
    try:
        state_data = json.loads(state_file.read_text(encoding="utf-8")) if state_file.exists() else {}
        state_data["phase"] = to_name
        atomic_write(state_file, json.dumps(state_data, ensure_ascii=False, indent=2))
    except (json.JSONDecodeError, OSError):
        pass
    return {"success": True, "from_phase": from_name, "to_phase": to_name, "reason": "token_budget"}


def check_token_budget() -> dict[str, Any]:
    with _phase_lock:
        current = _current_phase
    budget = PHASE_TOKEN_BUDGETS.get(current, 2000)
    budget = _safe_int(budget, 2000)
    with _PHASE_TOKEN_USAGE_LOCK:
        usage_data = _PHASE_TOKEN_USAGE.get(current, {"estimated_tokens": 0})
    estimated_tokens = _safe_int(usage_data.get("estimated_tokens", 0)) if isinstance(usage_data, dict) else 0
    usage_ratio = estimated_tokens / budget if budget > 0 else 0
    exceeded = usage_ratio >= 0.8
    result: dict[str, Any] = {
        "current_phase": current,
        "token_budget": budget,
        "estimated_tokens": estimated_tokens,
        "usage_ratio": round(usage_ratio, 4),
        "budget_exceeded_80pct": exceeded,
    }
    if exceeded and current > 0:
        degradation = degrade_phase()
        result["degradation"] = degradation
    return result


def auto_advance_on_command() -> dict[str, Any] | None:
    with _phase_lock:
        if _current_phase == PHASE_SKELETON:
            return advance_phase(PHASE_FUNCTIONAL)
    return None


def require_phase(required_phase: int) -> DisclosureTransition | None:
    with _phase_lock:
        if _current_phase >= required_phase:
            return None
        current = _current_phase
    current_name = PHASE_NAMES.get(current, "skeleton")
    target_name = PHASE_NAMES.get(required_phase, "full")
    required_resources: list[str] = []
    for p in range(current + 1, required_phase + 1):
        for r in PHASE_RESOURCES.get(p, []):
            if r not in required_resources:
                required_resources.append(r)
    estimated = 0
    for p in range(current + 1, required_phase + 1):
        for r in PHASE_RESOURCE_MAP.get(p, []):
            estimated += _estimate_resource_tokens(r)
    alternatives: list[str] = []
    for p in range(current + 1, required_phase):
        name = PHASE_NAMES.get(p, "")
        if name:
            alternatives.append(name)
    hint = _UPGRADE_HINTS.get(current, "")
    return DisclosureTransition(
        current_phase=current_name,
        target_phase=target_name,
        required_resources=required_resources,
        estimated_tokens=estimated,
        available_alternatives=alternatives,
        transition_hint=hint,
    )


def check_phase_for_capability(capability: str) -> DisclosureTransition | None:
    with _phase_lock:
        current = _current_phase
    available = PHASE_AVAILABLE_FUNCTIONS.get(current, PHASE_AVAILABLE_FUNCTIONS[0])
    if available.get(capability, False):
        return None
    required_phase: int | None = None
    for p in range(current + 1, 4):
        phase_available = PHASE_AVAILABLE_FUNCTIONS.get(p, {})
        if phase_available.get(capability, False):
            required_phase = p
            break
    if required_phase is None:
        return None
    return require_phase(required_phase)


def can_execute_command(command: str) -> dict[str, Any]:
    with _phase_lock:
        current = _current_phase
    if current == PHASE_SKELETON:
        allowed = command in SKELETON_ALLOWED_COMMANDS
        if allowed:
            return {"allowed": True, "command": command, "phase": current, "phase_name": "skeleton", "reason": "skeleton_allowed_command"}
        return {"allowed": False, "command": command, "phase": current, "phase_name": "skeleton", "reason": "command_not_available_in_skeleton", "skeleton_allowed_commands": list(SKELETON_ALLOWED_COMMANDS), "upgrade_hint": _UPGRADE_HINTS.get(PHASE_SKELETON, "")}
    available = _PHASE_AVAILABLE_COMMANDS.get(current, [])
    if command in available:
        return {"allowed": True, "command": command, "phase": current, "phase_name": PHASE_NAMES.get(current, "unknown")}
    return {"allowed": False, "command": command, "phase": current, "phase_name": PHASE_NAMES.get(current, "unknown"), "reason": "command_not_in_available_list", "available_commands": available}


def register(mcp: FastMCP) -> None:
    global _current_phase
    with _phase_lock:
        _current_phase = _get_current_phase_index()

    @mcp.tool(
        annotations=ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        )
    )
    async def resource_load_status(
        action: str,
        phase: int | None = None,
        resource_ids: list[str] | None = None,
        resource_uris: list[str] | None = None,
        priority: str = "normal",
        batch_mode: bool = False,
        auto_upgrade: bool = False,
        target_phase: str | None = None,
    ) -> dict[str, Any]:
        """渐进式加载状态管理：查询指定Phase的资源加载状态，预加载指定Phase的资源。返回资源ID、状态(loaded/available/missing/stale/expired)和路径。priority控制预加载优先级(critical/normal/background)，batch_mode启用批量并发加载，auto_upgrade启用Token预算超限时自动升级阶段。disclosure_transition返回阶段转换所需资源和估算。"""
        validated, err = validate_input(ResourceLoadStatusInput, action=action, phase=phase, resource_ids=resource_ids, resource_uris=resource_uris, priority=priority, batch_mode=batch_mode, auto_upgrade=auto_upgrade, target_phase=target_phase)
        if err:
            return err
        logger.info("resource_load_status called: action=%s", action)
        try:
            if action == "status":
                with _phase_lock:
                    current_phase_idx = _current_phase
                resources = []
                if phase is not None:
                    resources = _collect_resources_up_to_phase(phase)
                elif resource_ids:
                    for _pid, res_list in PHASE_RESOURCE_MAP.items():
                        for r in res_list:
                            if r["id"] in resource_ids:
                                resources.append(r)
                else:
                    resources = _collect_resources_up_to_phase(3)
                result = []
                resource_map = {}
                for r in resources:
                    r_status = _check_resource_status(r["id"], r["path"])
                    entry = {"id": r["id"], "type": r["type"], "path": r["path"], "status": r_status, "phase": None}
                    for pid, res_list in PHASE_RESOURCE_MAP.items():
                        if any(res["id"] == r["id"] for res in res_list):
                            entry["phase"] = pid
                            break
                    result.append(entry)
                    resource_map[r["id"]] = {"status": r_status, "type": r["type"], "path": r["path"], "phase": entry["phase"]}
                loaded = sum(1 for r in result if r["status"] == "loaded")
                stale = sum(1 for r in result if r["status"] == "stale")
                expired = sum(1 for r in result if r["status"] == "expired")
                disclosure = _get_loading_disclosure()
                with _cache_lock:
                    recent_transitions = list(_TRANSITION_HISTORY[-5:])
                with _PHASE_TOKEN_USAGE_LOCK:
                    phase_token_snapshot = dict(_PHASE_TOKEN_USAGE)
                current_phase_name = PHASE_NAMES.get(current_phase_idx, "skeleton")
                current_features = PHASE_AVAILABLE_FEATURES.get(current_phase_name, {"available": [], "unavailable": []})
                transition_check = _check_transition_conditions(current_phase_idx)
                response_data: dict[str, Any] = {
                    "resources": result,
                    "resources_map": resource_map,
                    "total": len(result),
                    "loaded": loaded,
                    "stale": stale,
                    "expired": expired,
                    "current_phase": current_phase_idx,
                    "current_phase_name": current_phase_name,
                    "available_functions": disclosure["available_functions"],
                    "disclosure_note": disclosure["disclosure_note"],
                    "upgrade_hint": disclosure["upgrade_hint"],
                    "available_commands": disclosure["available_commands"],
                    "available_features": current_features,
                    "token_budget": disclosure["token_budget"],
                    "token_usage": disclosure["token_usage"],
                    "phase_token_usage": phase_token_snapshot,
                    "phase_metrics": dict(_phase_state.get("phase_metrics", {})),
                    "transition_check": transition_check,
                    "transitions": recent_transitions,
                }
                if current_phase_idx == PHASE_SKELETON:
                    skeleton_allowed = _PHASE_AVAILABLE_COMMANDS.get(PHASE_SKELETON, [])
                    response_data["skeleton_info"] = {
                        "phase": "skeleton",
                        "phase_index": PHASE_SKELETON,
                        "available_commands": skeleton_allowed,
                        "command_execution": False,
                        "skeleton_allowed_commands": skeleton_allowed,
                        "disclosure_note": _DISCLOSURE_NOTES.get(PHASE_SKELETON, ""),
                        "upgrade_hint": _UPGRADE_HINTS.get(PHASE_SKELETON, ""),
                    }
                return make_success_response(response_data)
            elif action == "preload":
                if priority not in ("critical", "normal", "background"):
                    return make_error_response(ValueError(f"无效优先级: {priority}，支持: critical, normal, background"), error_code=ERR_VALIDATION)
                if resource_uris:
                    with _cache_lock:
                        _LOADED_PROGRESS["loading"] = True
                        _LOADED_PROGRESS["started_at"] = datetime.now(timezone.utc).isoformat()
                        _LOADED_PROGRESS["total_resources"] = len(resource_uris)
                        _LOADED_PROGRESS["loaded_resources"] = 0
                        _LOADED_PROGRESS["current_phase"] = None
                        _LOADED_PROGRESS["completed_at"] = None
                    loaded_count = 0
                    skipped_count = 0
                    refreshed_count = 0
                    total_size = 0
                    errors: list[str] = []
                    all_truncated = False
                    all_skipped_large_files: list[str] = []
                    for uri in resource_uris:
                        try:
                            is_valid, validity = _is_cache_valid(uri)
                            if is_valid:
                                skipped_count += 1
                                with _cache_lock:
                                    _LOADED_PROGRESS["loaded_resources"] += 1
                                continue
                            if validity in ("stale", "expired"):
                                with _cache_lock:
                                    _resource_lru.delete(uri)
                                refreshed_count += 1
                            result = _read_resource_content(uri)
                            content = result["content"]
                            if result["truncated"]:
                                all_truncated = True
                            all_skipped_large_files.extend(result["skipped_large_files"])
                            if content is not None:
                                _cleanup_cache()
                                source_path = _resolve_uri_source_path(uri)
                                source_hash = _compute_path_hash(source_path) if source_path else None
                                with _cache_lock:
                                    _resource_lru.put(uri, {
                                        "content": content,
                                        "cached_at": time.time(),
                                        "access_count": 0,
                                        "content_hash": source_hash or hashlib.sha256(content.encode("utf-8")).hexdigest(),
                                        "ttl_seconds": _CACHE_TTL_SECONDS,
                                        "source_path": str(source_path) if source_path else None,
                                    })
                                    _LOADED_PROGRESS["loaded_resources"] += 1
                                loaded_count += 1
                                total_size += len(content)
                            else:
                                errors.append(f"Resource not found: {uri}")
                                with _cache_lock:
                                    _LOADED_PROGRESS["loaded_resources"] += 1
                        except Exception as e:
                            errors.append(f"Failed to load {uri}: {str(e)}")
                            with _cache_lock:
                                _LOADED_PROGRESS["loaded_resources"] += 1
                    with _cache_lock:
                        _LOADED_PROGRESS["loading"] = False
                        _LOADED_PROGRESS["completed_at"] = datetime.now(timezone.utc).isoformat()
                    return make_success_response({
                        "action": "preload",
                        "loaded_count": loaded_count,
                        "skipped_count": skipped_count,
                        "refreshed_count": refreshed_count,
                        "total_uris": len(resource_uris),
                        "total_size_bytes": total_size,
                        "truncated": all_truncated,
                        "skipped_large_files": all_skipped_large_files if all_skipped_large_files else None,
                        "errors": errors if errors else None,
                        "priority": priority,
                        "batch_mode": batch_mode,
                    })
                if phase is None and target_phase is None:
                    return make_error_response(ValueError("preload操作需要phase或resource_uris参数"), error_code=ERR_VALIDATION)
                if phase is not None:
                    actual_phase = phase
                elif target_phase is not None:
                    if target_phase.isdigit():
                        actual_phase = int(target_phase)
                    else:
                        actual_phase = _LOADING_PHASE_MAP.get(target_phase, 0)
                else:
                    actual_phase = 0
                original_target = actual_phase
                with _phase_lock:
                    if actual_phase <= _current_phase:
                        current_name = PHASE_NAMES.get(_current_phase, "skeleton")
                        target_name = PHASE_NAMES.get(actual_phase, "skeleton")
                        disclosure = DisclosureTransition(
                            current_phase=current_name,
                            target_phase=target_name,
                            required_resources=[],
                            estimated_tokens=0,
                            available_alternatives=[PHASE_NAMES.get(p, "") for p in range(_current_phase + 1, 4) if PHASE_NAMES.get(p)],
                            transition_hint=_UPGRADE_HINTS.get(_current_phase, ""),
                        )
                        return make_success_response({
                            "action": "preload",
                            "phase": actual_phase,
                            "preloaded": [],
                            "total": 0,
                            "priority": priority,
                            "batch_mode": batch_mode,
                            "validation_error": "target_phase_must_be_higher_than_current",
                            "current_phase": current_name,
                            "current_phase_index": _current_phase,
                            "disclosure_transition": disclosure.model_dump(),
                        })
                if auto_upgrade:
                    current_phase_idx = _get_current_phase_index()
                    resources_to_load = _collect_resources_up_to_phase(actual_phase)
                    total_estimated = sum(_estimate_resource_tokens(r) for r in resources_to_load)
                    budget = PHASE_TOKEN_BUDGET.get(actual_phase, PHASE_TOKEN_BUDGET[3])
                    while total_estimated > budget and actual_phase < 3:
                        actual_phase += 1
                        resources_to_load = _collect_resources_up_to_phase(actual_phase)
                        total_estimated = sum(_estimate_resource_tokens(r) for r in resources_to_load)
                        budget = PHASE_TOKEN_BUDGET.get(actual_phase, PHASE_TOKEN_BUDGET[3])
                    if actual_phase != phase:
                        logger.info("auto_upgrade: phase %d -> %d (estimated %d tokens > budget %d)", phase, actual_phase, total_estimated, PHASE_TOKEN_BUDGET.get(phase, 0))
                else:
                    resources_to_load = _collect_resources_up_to_phase(actual_phase)
                    total_estimated = sum(_estimate_resource_tokens(r) for r in resources_to_load)
                    budget = PHASE_TOKEN_BUDGET.get(actual_phase, PHASE_TOKEN_BUDGET[3])
                    if total_estimated > budget and actual_phase < 3:
                        next_phase = actual_phase + 1
                        hint = _UPGRADE_HINTS.get(actual_phase, "")
                        send_mcp_notification("token_budget_exceeded", {
                            "phase": actual_phase,
                            "estimated_tokens": total_estimated,
                            "token_budget": budget,
                            "suggested_phase": next_phase,
                        })
                        return make_success_response({
                            "action": "preload",
                            "phase": actual_phase,
                            "preloaded": [],
                            "total": 0,
                            "priority": priority,
                            "batch_mode": batch_mode,
                            "token_budget_exceeded": True,
                            "estimated_tokens": total_estimated,
                            "token_budget": budget,
                            "upgrade_hint": hint,
                            "suggested_phase": next_phase,
                        })
                resources = PHASE_RESOURCE_MAP.get(actual_phase, [])
                with _cache_lock:
                    _LOADED_PROGRESS["loading"] = True
                    _LOADED_PROGRESS["started_at"] = datetime.now(timezone.utc).isoformat()
                    _LOADED_PROGRESS["total_resources"] = len(resources)
                    _LOADED_PROGRESS["loaded_resources"] = 0
                    _LOADED_PROGRESS["current_phase"] = actual_phase
                    _LOADED_PROGRESS["completed_at"] = None
                preloaded = []
                current = _get_loaded_resources()
                phase_estimated_tokens = 0
                for r in resources:
                    full_path = SKILL_ROOT / r["path"]
                    if full_path.exists():
                        is_valid, validity = _is_cache_valid(r["id"])
                        if is_valid:
                            preloaded.append({"id": r["id"], "status": "loaded", "cache": "valid"})
                            current.add(r["id"])
                            with _cache_lock:
                                _LOADED_PROGRESS["loaded_resources"] += 1
                            continue
                        if validity in ("stale", "expired"):
                            with _cache_lock:
                                _resource_lru.delete(r["id"])
                        source_hash = _compute_path_hash(full_path)
                        content = None
                        if full_path.is_file():
                            with contextlib.suppress(OSError):
                                content = full_path.read_text(encoding="utf-8")
                        elif full_path.is_dir():
                            parts: list[str] = []
                            try:
                                for fpath in sorted(full_path.rglob("*")):
                                    if fpath.is_file() and fpath.suffix in (".json", ".yaml", ".yml", ".md", ".txt"):
                                        parts.append(fpath.read_text(encoding="utf-8"))
                            except OSError:
                                pass
                            content = "\n---\n".join(parts) if parts else None
                        if content is not None:
                            res_tokens = _estimate_tokens(content)
                            phase_estimated_tokens += res_tokens
                            _update_phase_token_usage(actual_phase, res_tokens)
                        current.add(r["id"])
                        with _cache_lock:
                            _resource_lru.put(r["id"], {
                                "content": content or "",
                                "cached_at": time.time(),
                                "access_count": 0,
                                "content_hash": source_hash or hashlib.sha256((content or "").encode("utf-8")).hexdigest(),
                                "ttl_seconds": _CACHE_TTL_SECONDS,
                                "source_path": str(full_path),
                            })
                            _LOADED_PROGRESS["loaded_resources"] += 1
                        preloaded.append({"id": r["id"], "status": "loaded", "cache": "refreshed" if validity in ("stale", "expired") else "new"})
                    else:
                        preloaded.append({"id": r["id"], "status": "missing"})
                        with _cache_lock:
                            _LOADED_PROGRESS["loaded_resources"] += 1
                _set_loaded_resources(current)
                transition_result = advance_phase(actual_phase, force=True)
                with _cache_lock:
                    _LOADED_PROGRESS["loading"] = False
                    _LOADED_PROGRESS["completed_at"] = datetime.now(timezone.utc).isoformat()
                with _cache_lock:
                    transitions = list(_TRANSITION_HISTORY)
                disclosure = _get_loading_disclosure()
                budget_check = check_token_budget()
                result_data: dict[str, Any] = {
                    "phase": actual_phase,
                    "phase_name": transition_result.get("to_phase", _phase_index_to_name(actual_phase)),
                    "preloaded": preloaded,
                    "total": len(preloaded),
                    "priority": priority,
                    "batch_mode": batch_mode,
                    "auto_upgrade": auto_upgrade,
                    "estimated_tokens": phase_estimated_tokens,
                    "token_budget": PHASE_TOKEN_BUDGETS.get(actual_phase, PHASE_TOKEN_BUDGETS[3]),
                    "disclosure_note": disclosure["disclosure_note"],
                    "upgrade_hint": disclosure["upgrade_hint"],
                    "available_commands": disclosure["available_commands"],
                    "transitions": transitions[-5:],
                    "transition_result": transition_result,
                    "budget_check": budget_check,
                }
                if auto_upgrade and actual_phase != original_target:
                    result_data["auto_upgraded_from"] = original_target
                return make_success_response(result_data)
            elif action == "cache":
                with _cache_lock:
                    cache_snapshot = dict(_resource_lru.items())
                expired_count = sum(
                    1 for v in cache_snapshot.values()
                    if isinstance(v, dict) and (time.time() - v["cached_at"]) > v.get("ttl_seconds", _CACHE_TTL_SECONDS)
                )
                stale_count = 0
                for v in cache_snapshot.values():
                    source_path = v.get("source_path")
                    if source_path is not None:
                        current_hash = _compute_path_hash(Path(source_path))
                        if current_hash is not None and current_hash != v.get("content_hash"):
                            stale_count += 1
                return make_success_response({
                    "action": "cache",
                    "cached_uris": list(cache_snapshot.keys()),
                    "cache_size": sum(len(v.get("content", "")) for v in cache_snapshot.values()),
                    "total_entries": len(cache_snapshot),
                    "ttl_seconds": _CACHE_TTL_SECONDS,
                    "max_entries": _CACHE_MAX_ENTRIES,
                    "expired_entries": expired_count,
                    "stale_entries": stale_count,
                })
            elif action == "clear_cache":
                with _cache_lock:
                    count = _resource_lru.size()
                    expired_count = sum(
                        1 for _, v in _resource_lru.items()
                        if isinstance(v, dict) and (time.time() - v["cached_at"]) > v.get("ttl_seconds", _CACHE_TTL_SECONDS)
                    )
                    _resource_lru.clear()
                return make_success_response({
                    "action": "clear_cache",
                    "cleared_entries": count,
                    "expired_entries": expired_count,
                })
            elif action == "loading_progress":
                with _cache_lock:
                    progress = dict(_LOADED_PROGRESS)
                total = _safe_int(progress.get("total_resources"))
                loaded = _safe_int(progress.get("loaded_resources"))
                progress_percent = (loaded / total * 100) if total > 0 else 0
                with _phase_lock:
                    current_phase_idx = _current_phase
                target_phase_idx = progress.get("current_phase") or current_phase_idx
                loaded_list = sorted(_get_loaded_resources())
                pending_list = []
                for pid, res_list in PHASE_RESOURCE_MAP.items():
                    if pid > current_phase_idx:
                        for r in res_list:
                            if r["id"] not in loaded_list:
                                pending_list.append(r["id"])
                target_resources = PHASE_RESOURCES.get(target_phase_idx, [])
                target_loaded = sum(1 for r in target_resources if r in loaded_list)
                target_total = len(target_resources)
                target_progress = (target_loaded / target_total) if target_total > 0 else (1.0 if current_phase_idx >= target_phase_idx else 0.0)
                started_at = progress.get("started_at")
                elapsed_ms = 0
                if started_at:
                    try:
                        from datetime import datetime as _dt
                        started_dt = _dt.fromisoformat(started_at)
                        elapsed_ms = int((time.time() - started_dt.timestamp()) * 1000)
                    except (ValueError, OSError):
                        pass
                remaining = max(0, total - loaded)
                estimated_remaining_ms = int((elapsed_ms / max(loaded, 1)) * remaining) if loaded > 0 and remaining > 0 else 0
                budget_status = check_token_budget()
                return make_success_response({
                    "current_phase": current_phase_idx,
                    "target_phase": target_phase_idx,
                    "progress": round(target_progress, 4),
                    "loaded_resources": loaded_list,
                    "pending_resources": pending_list,
                    "estimated_time_remaining_ms": estimated_remaining_ms,
                    "total_resources": total,
                    "loaded_count": loaded,
                    "progress_percent": round(progress_percent, 2),
                    "target_phase_progress": round(target_progress, 4),
                    "target_phase_loaded": target_loaded,
                    "target_phase_total": target_total,
                    "loading": progress["loading"],
                    "started_at": progress.get("started_at"),
                    "completed_at": progress.get("completed_at"),
                    "budget_status": budget_status,
                })
            elif action == "token_report":
                with _TOKEN_METRICS_LOCK:
                    metrics_snapshot = {}
                    for tool_name, metrics in _TOKEN_METRICS.items():
                        inp = _safe_int(metrics.get("total_input_tokens"))
                        out = _safe_int(metrics.get("total_output_tokens"))
                        cnt = _safe_int(metrics.get("call_count"), 1)
                        metrics_snapshot[tool_name] = {
                            "total_input_tokens": inp,
                            "total_output_tokens": out,
                            "total_tokens": inp + out,
                            "call_count": cnt,
                            "avg_input_tokens": round(inp / max(cnt, 1), 1),
                            "avg_output_tokens": round(out / max(cnt, 1), 1),
                        }
                total_input = sum(m["total_input_tokens"] for m in metrics_snapshot.values())
                total_output = sum(m["total_output_tokens"] for m in metrics_snapshot.values())
                with _PHASE_TOKEN_USAGE_LOCK:
                    phase_token_snapshot = dict(_PHASE_TOKEN_USAGE)
                return make_success_response({
                    "action": "token_report",
                    "tools": metrics_snapshot,
                    "phase_token_usage": phase_token_snapshot,
                    "phase_token_budgets": PHASE_TOKEN_BUDGET,
                    "summary": {
                        "total_tools": len(metrics_snapshot),
                        "total_input_tokens": total_input,
                        "total_output_tokens": total_output,
                        "total_tokens": total_input + total_output,
                        "estimate_method": f"char_count/{_TOKEN_ESTIMATE_RATIO}",
                    },
                })
            elif action == "disclosure_transition":
                with _phase_lock:
                    current_phase_idx = _current_phase
                current_phase_name = PHASE_NAMES.get(current_phase_idx, "skeleton")
                target_phase_name = target_phase or "full"
                target_phase_idx = _LOADING_PHASE_MAP.get(target_phase_name, 3)
                required_resources: list[str] = []
                for pid in range(current_phase_idx + 1, target_phase_idx + 1):
                    for r in PHASE_RESOURCE_MAP.get(pid, []):
                        if r["id"] not in required_resources:
                            required_resources.append(r["id"])
                    for r in PHASE_RESOURCES.get(pid, []):
                        if r not in required_resources:
                            required_resources.append(r)
                estimated = 0
                for pid in range(current_phase_idx + 1, target_phase_idx + 1):
                    for r in PHASE_RESOURCE_MAP.get(pid, []):
                        estimated += _estimate_resource_tokens(r)
                available_alternatives: list[str] = []
                for pid in range(current_phase_idx + 1, target_phase_idx):
                    alt_name = PHASE_NAMES.get(pid, "")
                    if alt_name:
                        available_alternatives.append(alt_name)
                hint = _UPGRADE_HINTS.get(current_phase_idx, "")
                can_advance = can_advance_to(target_phase_idx)
                disclosure = DisclosureTransition(
                    current_phase=current_phase_name,
                    target_phase=target_phase_name,
                    required_resources=required_resources,
                    estimated_tokens=estimated,
                    available_alternatives=available_alternatives,
                    transition_hint=hint,
                )
                return make_success_response({
                    "current_phase": current_phase_name,
                    "target_phase": target_phase_name,
                    "required_resources": required_resources,
                    "estimated_tokens": estimated,
                    "available_alternatives": available_alternatives,
                    "transition_hint": hint,
                    "can_advance": can_advance,
                    "disclosure_transition": disclosure.model_dump(),
                })
            elif action == "transition_check":
                with _phase_lock:
                    current_phase_idx = _current_phase
                current_phase_name = PHASE_NAMES.get(current_phase_idx, "skeleton")
                next_phase_idx = current_phase_idx + 1 if current_phase_idx < 3 else None
                next_phase_name = PHASE_NAMES.get(next_phase_idx) if next_phase_idx is not None else None
                transition_check = _check_transition_conditions(current_phase_idx)
                return make_success_response({
                    "action": "transition_check",
                    "current_phase": current_phase_name,
                    "current_phase_index": current_phase_idx,
                    "next_phase": next_phase_name,
                    "next_phase_index": next_phase_idx,
                    "can_advance": transition_check["can_transition"],
                    "conditions_met": transition_check["conditions_met"],
                    "missing": transition_check["missing"],
                    "description": transition_check.get("description", ""),
                    "transition_key": transition_check.get("transition_key", ""),
                    "current_tools_available": transition_check.get("current_tools_available", 0),
                    "min_tools_available": transition_check.get("min_tools_available", 0),
                    "current_resources_loaded": transition_check.get("current_resources_loaded", 0),
                    "min_resources_loaded": transition_check.get("min_resources_loaded", 0),
                })
            elif action == "features":
                with _phase_lock:
                    current_phase_idx = _current_phase
                current_phase_name = PHASE_NAMES.get(current_phase_idx, "skeleton")
                features = PHASE_AVAILABLE_FEATURES.get(current_phase_name, {"available": [], "unavailable": []})
                return make_success_response({
                    "action": "features",
                    "current_phase": current_phase_name,
                    "current_phase_index": current_phase_idx,
                    "available": features.get("available", []),
                    "unavailable": features.get("unavailable", []),
                    "all_phases": {k: v for k, v in PHASE_AVAILABLE_FEATURES.items()},
                })
            elif action == "metrics":
                with _phase_lock:
                    current_phase_idx = _current_phase
                current_phase_name = PHASE_NAMES.get(current_phase_idx, "skeleton")
                phase_metrics = dict(_phase_state.get("phase_metrics", {}))
                total_tokens = sum(_safe_int(m.get("tokens_consumed")) for m in phase_metrics.values() if isinstance(m, dict))
                total_duration = sum(_safe_int(m.get("load_duration_ms")) for m in phase_metrics.values() if isinstance(m, dict))
                total_resources = sum(_safe_int(m.get("resources_loaded")) for m in phase_metrics.values() if isinstance(m, dict))
                with _PHASE_TOKEN_USAGE_LOCK:
                    phase_token_snapshot = dict(_PHASE_TOKEN_USAGE)
                return make_success_response({
                    "action": "metrics",
                    "current_phase": current_phase_name,
                    "current_phase_index": current_phase_idx,
                    "phase_metrics": phase_metrics,
                    "phase_transition_timestamps": dict(_phase_state.get("phase_transition_timestamps", {})),
                    "total": {
                        "tokens_consumed": total_tokens,
                        "load_duration_ms": total_duration,
                        "resources_loaded": total_resources,
                    },
                    "phase_token_usage": phase_token_snapshot,
                })
            else:
                return make_error_response(ValueError(f"未知操作: {action}，支持: status, preload, cache, clear_cache, loading_progress, token_report, disclosure_transition, transition_check, features, metrics"), error_code=ERR_VALIDATION)
        except Exception as e:
            logger.error("resource_load_status error: %s", e)
            return make_error_response(e)
