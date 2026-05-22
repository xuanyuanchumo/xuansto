from __future__ import annotations

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
from ..core.config import SKILL_ROOT, REFERENCES_DIR, AGENTS_DIR, COMMANDS_DIR, TEMPLATES_DIR, WORK_DIR, DATA_DIR
from ..core.errors import make_error_response, make_success_response, XuanstoMCPError
from ..core.logging_config import get_logger
from ..core.validator import validate_input
from ..models.schemas import ResourceLoadStatusInput

logger = get_logger("resource_load_status")

PHASE_RESOURCE_MAP: dict[int, list[dict[str, str]]] = {
    0: [
        {"id": "skill-config", "type": "config", "path": ".skill-config.yaml"},
        {"id": "agent-registry", "type": "reference", "path": "references/agent-registry.md"},
        {"id": "quality-gates", "type": "reference", "path": "references/quality-gates.md"},
    ],
    1: [
        {"id": "knowledge-general", "type": "knowledge", "path": ".knowledge/general/"},
        {"id": "brainstorm-workflow", "type": "workflow", "path": "workflows/brainstorming-workflow.md"},
    ],
    2: [
        {"id": "knowledge-patterns", "type": "knowledge", "path": ".knowledge/general/patterns/"},
        {"id": "sdd-tdd-full", "type": "workflow", "path": "workflows/sdd-tdd-full.md"},
    ],
    3: [
        {"id": "test-guidelines", "type": "reference", "path": "references/test-guidelines.md"},
    ],
    4: [
        {"id": "coding-standards", "type": "reference", "path": "references/coding-standards.md"},
        {"id": "karpathy-guidelines", "type": "reference", "path": "references/karpathy-guidelines.md"},
    ],
    5: [
        {"id": "security-guidelines", "type": "reference", "path": "references/security-guidelines.md"},
        {"id": "owasp-top10", "type": "reference", "path": "references/owasp-top10-2026.md"},
    ],
    6: [
        {"id": "acceptance-criteria", "type": "reference", "path": "references/acceptance-criteria.md"},
    ],
    7: [
        {"id": "simplification-rules", "type": "reference", "path": "references/karpathy-guidelines.md", "inherits_from": "phase_4"},
    ],
    8: [
        {"id": "desktop-guidelines", "type": "reference", "path": "references/desktop-dev-guidelines.md"},
        {"id": "ipc-contracts", "type": "reference", "path": "references/ipc-contracts.md"},
    ],
}

_PHASE_INHERITS: dict[int, list[int]] = {
    7: [4],
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

_RESOURCE_CACHE: dict[str, dict[str, Any]] = {}

_cache_lock = threading.Lock()

_CACHE_TTL_SECONDS = 3600
_CACHE_MAX_ENTRIES = 100

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

_AVAILABLE_FUNCTIONS_MAP: dict[str, dict[str, bool]] = {
    "skeleton": {
        "command_routing": True,
        "command_execution": False,
        "quality_gates": False,
        "knowledge_search": False,
        "reference_docs": False,
        "agent_details": False,
        "full_scripts": False,
    },
    "functional": {
        "command_routing": True,
        "command_execution": True,
        "quality_gates": True,
        "knowledge_search": False,
        "reference_docs": False,
        "agent_details": False,
        "full_scripts": False,
    },
    "enhanced": {
        "command_routing": True,
        "command_execution": True,
        "quality_gates": True,
        "knowledge_search": True,
        "reference_docs": True,
        "agent_details": True,
        "full_scripts": False,
    },
    "full": {
        "command_routing": True,
        "command_execution": True,
        "quality_gates": True,
        "knowledge_search": True,
        "reference_docs": True,
        "agent_details": True,
        "full_scripts": True,
    },
}

_DISCLOSURE_NOTES: dict[str, str] = {
    "skeleton": "骨架阶段，仅命令路由可用",
    "functional": "功能阶段，知识检索需推进到增强阶段",
    "enhanced": "增强阶段，完整脚本集需推进到完整阶段",
    "full": "完整阶段，全部功能可用",
}


def _get_loading_disclosure() -> tuple[dict[str, bool], str]:
    state_file = WORK_DIR / "resource_state.json"
    current_phase = "skeleton"
    if state_file.exists():
        try:
            data = json.loads(state_file.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                current_phase = data.get("phase", current_phase)
        except (json.JSONDecodeError, OSError):
            pass
    available_functions = _AVAILABLE_FUNCTIONS_MAP.get(
        current_phase, _AVAILABLE_FUNCTIONS_MAP["skeleton"]
    )
    disclosure_note = _DISCLOSURE_NOTES.get(
        current_phase, _DISCLOSURE_NOTES["skeleton"]
    )
    return available_functions, disclosure_note


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
    return DATA_DIR / resource_key


def _is_cache_valid(cache_key: str) -> tuple[bool, str]:
    with _cache_lock:
        if cache_key not in _RESOURCE_CACHE:
            return False, "not_cached"
        entry = _RESOURCE_CACHE[cache_key]
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
            k for k, v in _RESOURCE_CACHE.items()
            if (time.time() - v["cached_at"]) > v.get("ttl_seconds", _CACHE_TTL_SECONDS)
        ]
        for k in expired_keys:
            del _RESOURCE_CACHE[k]
        if len(_RESOURCE_CACHE) > _CACHE_MAX_ENTRIES:
            sorted_keys = sorted(_RESOURCE_CACHE.keys(), key=lambda k: _RESOURCE_CACHE[k]["cached_at"])
            overflow = len(_RESOURCE_CACHE) - _CACHE_MAX_ENTRIES
            for k in sorted_keys[:overflow]:
                del _RESOURCE_CACHE[k]


def _read_resource_content(uri: str) -> dict[str, Any]:
    with _cache_lock:
        if uri in _RESOURCE_CACHE:
            entry = _RESOURCE_CACHE[uri]
            if (time.time() - entry["cached_at"]) > entry.get("ttl_seconds", _CACHE_TTL_SECONDS):
                del _RESOURCE_CACHE[uri]
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
        data = json.loads(state_file.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return set(data)
        if isinstance(data, dict):
            return set(data.get("loaded", []))
    return set()


def _save_resource_state(state: set[str]) -> None:
    state_file = _get_state_file()
    payload = {
        "version": 1,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "loaded": sorted(state),
    }
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
        if resource_id in _RESOURCE_CACHE:
            entry = _RESOURCE_CACHE[resource_id]
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

def register(mcp: FastMCP) -> None:
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
    ) -> dict[str, Any]:
        """渐进式加载状态管理：查询指定Phase的资源加载状态，预加载指定Phase的资源。返回资源ID、状态(loaded/available/missing/stale/expired)和路径。priority控制预加载优先级(critical/normal/background)，batch_mode启用批量并发加载。"""
        validated, err = validate_input(ResourceLoadStatusInput, action=action, phase=phase, resource_ids=resource_ids, resource_uris=resource_uris, priority=priority, batch_mode=batch_mode)
        if err:
            return err
        logger.info("resource_load_status called: action=%s", action)
        if action == "status":
            resources = []
            if phase is not None:
                resources = PHASE_RESOURCE_MAP.get(phase, [])
            elif resource_ids:
                for pid, res_list in PHASE_RESOURCE_MAP.items():
                    for r in res_list:
                        if r["id"] in resource_ids:
                            resources.append(r)
            else:
                for pid, res_list in PHASE_RESOURCE_MAP.items():
                    resources.extend(res_list)
            result = []
            for r in resources:
                status = _check_resource_status(r["id"], r["path"])
                result.append({"id": r["id"], "type": r["type"], "path": r["path"], "status": status})
            loaded = sum(1 for r in result if r["status"] == "loaded")
            stale = sum(1 for r in result if r["status"] == "stale")
            expired = sum(1 for r in result if r["status"] == "expired")
            available_functions, disclosure_note = _get_loading_disclosure()
            return make_success_response({"resources": result, "total": len(result), "loaded": loaded, "stale": stale, "expired": expired, "available_functions": available_functions, "disclosure_note": disclosure_note})
        elif action == "preload":
            if priority not in ("critical", "normal", "background"):
                return make_error_response(ValueError(f"无效优先级: {priority}，支持: critical, normal, background"))
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
                                _RESOURCE_CACHE.pop(uri, None)
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
                                _RESOURCE_CACHE[uri] = {
                                    "content": content,
                                    "cached_at": time.time(),
                                    "access_count": 0,
                                    "content_hash": source_hash or hashlib.sha256(content.encode("utf-8")).hexdigest(),
                                    "ttl_seconds": _CACHE_TTL_SECONDS,
                                    "source_path": str(source_path) if source_path else None,
                                }
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
            if phase is None:
                return make_error_response(ValueError("preload操作需要phase或resource_uris参数"))
            resources = PHASE_RESOURCE_MAP.get(phase, [])
            with _cache_lock:
                _LOADED_PROGRESS["loading"] = True
                _LOADED_PROGRESS["started_at"] = datetime.now(timezone.utc).isoformat()
                _LOADED_PROGRESS["total_resources"] = len(resources)
                _LOADED_PROGRESS["loaded_resources"] = 0
                _LOADED_PROGRESS["current_phase"] = phase
                _LOADED_PROGRESS["completed_at"] = None
            preloaded = []
            current = _get_loaded_resources()
            inherited_paths: set[str] = set()
            for parent_phase in _PHASE_INHERITS.get(phase, []):
                for parent_res in PHASE_RESOURCE_MAP.get(parent_phase, []):
                    inherited_paths.add(parent_res["path"])
            for r in resources:
                if r.get("inherits_from") and r["path"] in inherited_paths:
                    if r["id"] in current or r["id"] in _RESOURCE_CACHE:
                        preloaded.append({"id": r["id"], "status": "loaded", "cache": "inherited"})
                        current.add(r["id"])
                        with _cache_lock:
                            _LOADED_PROGRESS["loaded_resources"] += 1
                        continue
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
                            _RESOURCE_CACHE.pop(r["id"], None)
                    source_hash = _compute_path_hash(full_path)
                    content = None
                    if full_path.is_file():
                        try:
                            content = full_path.read_text(encoding="utf-8")
                        except OSError:
                            pass
                    elif full_path.is_dir():
                        parts: list[str] = []
                        try:
                            for fpath in sorted(full_path.rglob("*")):
                                if fpath.is_file() and fpath.suffix in (".json", ".yaml", ".yml", ".md", ".txt"):
                                    parts.append(fpath.read_text(encoding="utf-8"))
                        except OSError:
                            pass
                        content = "\n---\n".join(parts) if parts else None
                    current.add(r["id"])
                    with _cache_lock:
                        _RESOURCE_CACHE[r["id"]] = {
                            "content": content or "",
                            "cached_at": time.time(),
                            "access_count": 0,
                            "content_hash": source_hash or hashlib.sha256((content or "").encode("utf-8")).hexdigest(),
                            "ttl_seconds": _CACHE_TTL_SECONDS,
                            "source_path": str(full_path),
                        }
                        _LOADED_PROGRESS["loaded_resources"] += 1
                    preloaded.append({"id": r["id"], "status": "loaded", "cache": "refreshed" if validity in ("stale", "expired") else "new"})
                else:
                    preloaded.append({"id": r["id"], "status": "missing"})
                    with _cache_lock:
                        _LOADED_PROGRESS["loaded_resources"] += 1
            _set_loaded_resources(current)
            with _cache_lock:
                _LOADED_PROGRESS["loading"] = False
                _LOADED_PROGRESS["completed_at"] = datetime.now(timezone.utc).isoformat()
            return make_success_response({"phase": phase, "preloaded": preloaded, "total": len(preloaded), "priority": priority, "batch_mode": batch_mode})
        elif action == "cache":
            with _cache_lock:
                cache_snapshot = dict(_RESOURCE_CACHE)
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
                count = len(_RESOURCE_CACHE)
                expired_count = sum(
                    1 for v in _RESOURCE_CACHE.values()
                    if isinstance(v, dict) and (time.time() - v["cached_at"]) > v.get("ttl_seconds", _CACHE_TTL_SECONDS)
                )
                _RESOURCE_CACHE.clear()
            return make_success_response({
                "action": "clear_cache",
                "cleared_entries": count,
                "expired_entries": expired_count,
            })
        elif action == "loading_progress":
            with _cache_lock:
                progress = dict(_LOADED_PROGRESS)
            total = progress["total_resources"]
            loaded = progress["loaded_resources"]
            progress_percent = (loaded / total * 100) if total > 0 else 0
            return make_success_response({
                "action": "loading_progress",
                "total_resources": total,
                "loaded_resources": loaded,
                "progress_percent": round(progress_percent, 2),
                "current_phase": progress["current_phase"],
                "loading": progress["loading"],
                "started_at": progress["started_at"],
                "completed_at": progress["completed_at"],
            })
        else:
            return make_error_response(ValueError(f"未知操作: {action}，支持: status, preload, cache, clear_cache, loading_progress"))
