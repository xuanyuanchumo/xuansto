from __future__ import annotations

import gzip
import hashlib
import json
import os
import tempfile
import threading
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from ..core.config import QUALITY_GATES_PHASE_MAP, SKILL_ROOT, WORK_DIR, WORKFLOWS_DIR, _resolve_skill_file
from ..core.errors import XuanstoMCPError, make_error_response, make_success_response, ERR_VALIDATION, ERR_NOT_FOUND, ERR_INTERNAL
from ..core import atomic_write
from ..core.logging_config import get_logger
from ..core.notifications import notify
from ..core.validator import validate_input
from ..models.schemas import WorkflowDispatchInput
from .quality_gate_check import INLINE_CHECKS

logger = get_logger("workflow_dispatch")

_DEFAULT_MAX_SNAPSHOTS_PER_WORKFLOW = 20
_DEFAULT_SNAPSHOT_TTL_DAYS = 30

_SNAPSHOT_CLEANUP_CONFIG: dict[str, Any] = {}


def _get_snapshot_cleanup_config() -> dict[str, Any]:
    global _SNAPSHOT_CLEANUP_CONFIG
    if _SNAPSHOT_CLEANUP_CONFIG:
        return _SNAPSHOT_CLEANUP_CONFIG
    try:
        import yaml
        config_path = _resolve_skill_file(".xuansto-config.yaml")
        if config_path.exists():
            raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
            _SNAPSHOT_CLEANUP_CONFIG = {
                "max_snapshots_per_workflow": raw.get("max_snapshots_per_workflow", _DEFAULT_MAX_SNAPSHOTS_PER_WORKFLOW),
                "snapshot_ttl_days": raw.get("snapshot_ttl_days", _DEFAULT_SNAPSHOT_TTL_DAYS),
            }
            return _SNAPSHOT_CLEANUP_CONFIG
    except Exception:
        pass
    _SNAPSHOT_CLEANUP_CONFIG = {
        "max_snapshots_per_workflow": _DEFAULT_MAX_SNAPSHOTS_PER_WORKFLOW,
        "snapshot_ttl_days": _DEFAULT_SNAPSHOT_TTL_DAYS,
    }
    return _SNAPSHOT_CLEANUP_CONFIG

PHASE_NAMES = {
    0: "初始化", 1: "需求分析", 2: "架构设计", 3: "测试先行",
    4: "代码实现", 5: "测试验证", 6: "验收确认", 7: "持续重构", 8: "部署交付"
}

_ACTIVE_WORKFLOWS: dict[str, dict[str, Any]] = {}

_workflows_lock = threading.Lock()
_phase_advance_lock = threading.Lock()

def _get_workflows_dir() -> Path:
    d = WORK_DIR / "workflows"
    d.mkdir(parents=True, exist_ok=True)
    return d

def _persist_workflow(workflow_id: str, data: dict[str, Any]) -> None:
    core_data = {k: v for k, v in data.items() if k not in ("_timestamp", "_hash")}
    payload = dict(core_data)
    payload["_timestamp"] = time.time()
    payload["_hash"] = hashlib.sha256(json.dumps(core_data, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
    path = _get_workflows_dir() / f"{workflow_id}.json"
    atomic_write(path, json.dumps(payload, ensure_ascii=False, indent=2))

def _load_workflow(workflow_id: str) -> dict[str, Any] | None:
    path = _get_workflows_dir() / f"{workflow_id}.json"
    if not path.exists():
        return None
    try:
        loaded: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
        stored_hash = loaded.get("_hash")
        if stored_hash is not None:
            core_data = {k: v for k, v in loaded.items() if k not in ("_timestamp", "_hash")}
            computed_hash = hashlib.sha256(json.dumps(core_data, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
            if computed_hash != stored_hash:
                logger.warning("Workflow %s state hash mismatch, skipping load", workflow_id)
                return None
        else:
            logger.warning("Workflow %s state file has no integrity hash, loading without verification", workflow_id)
        return loaded
    except Exception:
        return None

def _load_all_workflows() -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for f in _get_workflows_dir().glob("*.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            wid = data.get("workflow_id", f.stem)
            result[wid] = data
        except Exception:
            continue
    return result

def _persist_active_workflows() -> None:
    persist_dir = WORK_DIR
    persist_dir.mkdir(parents=True, exist_ok=True)
    with _workflows_lock:
        snapshot = dict(_ACTIVE_WORKFLOWS)
    core_data = {k: v for k, v in snapshot.items() if k not in ("_timestamp", "_hash")}
    payload = dict(core_data)
    payload["_timestamp"] = time.time()
    payload["_hash"] = hashlib.sha256(json.dumps(core_data, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
    path = persist_dir / "workflow_states.json"
    atomic_write(path, json.dumps(payload, ensure_ascii=False, indent=2))
    logger.info("Persisted %d active workflows to %s", len(snapshot), path)

def _load_active_workflows() -> None:
    path = WORK_DIR / "workflow_states.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        stored_hash = data.pop("_hash", None)
        data.pop("_timestamp", None)
        if stored_hash is not None:
            computed_hash = hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
            if computed_hash != stored_hash:
                logger.warning("Active workflows state hash mismatch, skipping load")
                return
        else:
            logger.warning("Active workflows state file has no integrity hash, loading without verification")
        with _workflows_lock:
            _ACTIVE_WORKFLOWS.update(data)
        logger.info("Loaded %d active workflows from %s", len(data), path)
    except FileNotFoundError:
        pass
    except json.JSONDecodeError:
        logger.warning("Failed to parse workflow states from %s", path)

def load_on_startup() -> None:
    workflows_dir = _get_workflows_dir()
    recovered = 0
    skipped_aborted = 0
    skipped_corrupt = 0
    entries: dict[str, dict[str, Any]] = {}
    for f in workflows_dir.glob("*.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            skipped_corrupt += 1
            logger.warning("Skipping corrupt workflow file %s: %s", f.name, exc)
            continue
        wid = data.get("workflow_id", f.stem)
        status = data.get("status", "")
        if status == "aborted":
            skipped_aborted += 1
            logger.debug("Skipping aborted workflow %s from %s", wid, f.name)
            continue
        entries[wid] = data
        recovered += 1
    with _workflows_lock:
        _ACTIVE_WORKFLOWS.update(entries)
    logger.info(
        "Startup recovery: %d workflows restored, %d aborted skipped, %d corrupt skipped",
        recovered, skipped_aborted, skipped_corrupt,
    )
    _persist_active_workflows()

def _list_workflows() -> list[dict[str, Any]]:
    if not WORKFLOWS_DIR.exists():
        return []
    workflows = []
    for f in WORKFLOWS_DIR.glob("*.md"):
        workflows.append({"name": f.stem, "path": str(f)})
    return workflows

def _parse_workflow_definition(workflow_name: str) -> dict[str, Any] | None:
    workflow_path = WORKFLOWS_DIR / f"{workflow_name}.md"
    if not workflow_path.exists():
        return None
    content = workflow_path.read_text(encoding="utf-8")
    if not content.startswith("---"):
        return None
    end = content.find("---", 3)
    if end == -1:
        return None
    yaml_str = content[3:end].strip()
    try:
        import yaml
        parsed: dict[str, Any] = yaml.safe_load(yaml_str)
        return parsed
    except Exception:
        return None

def _start_workflow(workflow: str, project_path: str) -> dict[str, Any]:
    workflow_file = WORKFLOWS_DIR / f"{workflow}.md"
    if not workflow_file.exists():
        available = [w["name"] for w in _list_workflows()]
        return {"error": True, "code": "WORKFLOW_NOT_FOUND", "message": f"工作流不存在: {workflow}", "available": available}
    workflow_id = f"wf-{uuid.uuid4().hex[:8]}"
    entry = {
        "workflow_id": workflow_id,
        "workflow": workflow,
        "project_path": project_path,
        "status": "running",
        "current_phase": 0,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "completed_phases": [],
    }
    definition = _parse_workflow_definition(workflow)
    if definition and "phases" in definition:
        entry["phase_definitions"] = definition["phases"]
    with _workflows_lock:
        _ACTIVE_WORKFLOWS[workflow_id] = entry
    _persist_workflow(workflow_id, entry)
    _persist_active_workflows()
    notify(f"Workflow {workflow} started: {workflow_id}", "info")
    return entry

def _get_workflow_status(workflow_id: str) -> dict[str, Any]:
    with _workflows_lock:
        if workflow_id in _ACTIVE_WORKFLOWS:
            return _ACTIVE_WORKFLOWS[workflow_id]
    loaded = _load_workflow(workflow_id)
    if loaded is not None:
        with _workflows_lock:
            _ACTIVE_WORKFLOWS[workflow_id] = loaded
        return loaded
    return {"error": True, "code": "WORKFLOW_NOT_FOUND", "message": f"工作流实例不存在: {workflow_id}"}

def _abort_workflow(workflow_id: str) -> dict[str, Any]:
    with _workflows_lock:
        if workflow_id not in _ACTIVE_WORKFLOWS:
            loaded = _load_workflow(workflow_id)
            if loaded is None:
                return {"error": True, "code": "WORKFLOW_NOT_FOUND", "message": f"工作流实例不存在: {workflow_id}"}
            _ACTIVE_WORKFLOWS[workflow_id] = loaded
        entry = _ACTIVE_WORKFLOWS.pop(workflow_id)
    entry["status"] = "aborted"
    entry["aborted_at"] = datetime.now(timezone.utc).isoformat()
    _persist_workflow(workflow_id, entry)
    _persist_active_workflows()
    notify(f"Workflow aborted: {workflow_id}", "warning")
    return entry

def _advance_phase(workflow_id: str) -> dict[str, Any]:
    with _phase_advance_lock:
        state = _load_workflow(workflow_id)
        if state is None:
            return {"error": True, "code": "WORKFLOW_NOT_FOUND", "message": f"工作流实例不存在: {workflow_id}"}
        current_phase = state.get("current_phase", 0)
        project_path = state.get("project_path", ".")
        phase_defs = state.get("phase_definitions", [])
        phase_gates = []
        for p in phase_defs:
            if p.get("id") == current_phase:
                phase_gates = p.get("gates", [])
                break
        gates = phase_gates if phase_gates else QUALITY_GATES_PHASE_MAP.get(str(current_phase), [])

        gates_checked = []
        failed_gates = []
        for gate_id in gates:
            if gate_id in INLINE_CHECKS:
                try:
                    result = INLINE_CHECKS[gate_id](project_path)
                    status = result.get("status", "SKIP")
                    gate_result = {
                        "gate_id": gate_id,
                        "status": status,
                        "message": result.get("message", ""),
                        "source": "inline",
                    }
                    if status == "FAIL":
                        gate_result["suggestion"] = f"修复 {gate_id} 相关问题后重试"
                        failed_gates.append(gate_result)
                except Exception as e:
                    gate_result = {"gate_id": gate_id, "status": "ERROR", "message": str(e), "source": "inline"}
                    failed_gates.append(gate_result)
            else:
                gate_result = {"gate_id": gate_id, "status": "SKIP", "message": "无内嵌检查，需手动验证"}
            gates_checked.append(gate_result)

        gates_passed = len(failed_gates) == 0

        if not gates_passed:
            failed_ids = [g.get("gate_id", "") for g in failed_gates]
            notify(
                f"Phase {PHASE_NAMES.get(current_phase, current_phase)} gates failed for {workflow_id}: {failed_ids}",
                "warning",
            )
            suggestions = []
            for check in gates_checked:
                if check.get("status") == "FAIL" and check.get("suggestion"):
                    suggestions.append({
                        "gate_id": check.get("gate_id", ""),
                        "suggestion": check.get("suggestion", ""),
                        "retry_command": f"quality_gate_check(gate_ids=['{check.get('gate_id', '')}'])",
                    })
            return {
                "workflow_id": workflow_id,
                "current_phase": current_phase,
                "phase_name": PHASE_NAMES.get(current_phase, f"Phase {current_phase}"),
                "advanced": False,
                "gates_passed": False,
                "gates_checked": gates_checked,
                "failed_gates": failed_gates,
                "recovery_suggestions": suggestions,
                "message": f"阶段 {PHASE_NAMES.get(current_phase, f'Phase {current_phase}')} 门禁未通过，{len(failed_gates)} 个失败",
            }

        previous_phase = current_phase
        new_phase = current_phase + 1
        state["current_phase"] = new_phase
        completed = state.get("completed_phases", [])
        if previous_phase not in completed:
            completed.append(previous_phase)
        state["completed_phases"] = completed
        if new_phase > 8:
            state["status"] = "completed"
            state["completed_at"] = datetime.now(timezone.utc).isoformat()
        _persist_workflow(workflow_id, state)
        with _workflows_lock:
            if workflow_id in _ACTIVE_WORKFLOWS:
                _ACTIVE_WORKFLOWS[workflow_id] = state
            active_state = _ACTIVE_WORKFLOWS.get(workflow_id, state)
        _persist_active_workflows()
        _save_snapshot(workflow_id, active_state, project_path)
        if new_phase > 8:
            notify(f"Workflow completed: {workflow_id}", "info")
        else:
            notify(
                f"Phase advanced: {PHASE_NAMES.get(previous_phase, previous_phase)} -> {PHASE_NAMES.get(new_phase, new_phase)} ({workflow_id})",
                "info",
            )
        return {
            "workflow_id": workflow_id,
            "previous_phase": previous_phase,
            "new_phase": new_phase,
            "advanced": True,
            "gates_passed": True,
            "gates_checked": gates_checked,
            "message": f"阶段推进: {PHASE_NAMES.get(previous_phase, f'Phase {previous_phase}')} -> {PHASE_NAMES.get(new_phase, f'Phase {new_phase}')}"
        }

def _current_phase(workflow_id: str) -> dict[str, Any]:
    state = _load_workflow(workflow_id)
    if state is None:
        return {"error": True, "code": "WORKFLOW_NOT_FOUND", "message": f"工作流实例不存在: {workflow_id}"}
    current = state.get("current_phase", 0)
    completed = state.get("completed_phases", [])
    total_phases = 9
    remaining = max(0, total_phases - current - 1)
    return {
        "workflow_id": workflow_id,
        "current_phase": current,
        "phase_name": PHASE_NAMES.get(current, f"Phase {current}"),
        "completed_phases": completed,
        "remaining_phases": remaining,
        "status": state.get("status", "unknown")
    }

_SNAPSHOT_DIR_NAME = "workflow_snapshots"


def _get_snapshot_dir(project_path: str) -> Path:
    return Path(project_path).resolve() / ".xuansto" / _SNAPSHOT_DIR_NAME


def _save_snapshot(workflow_id: str, state: dict[str, Any], project_path: str) -> Path:
    snapshot_dir = _get_snapshot_dir(project_path)
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    phase = state.get("current_phase", 0)
    now = time.time()
    timestamp = int(now)
    filename = f"{workflow_id}_phase{phase}_{timestamp}.json"
    snapshot_path = snapshot_dir / filename
    snapshot_data = {
        "workflow_id": workflow_id,
        "phase": phase,
        "timestamp": now,
        "time_iso": datetime.fromtimestamp(now, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "state": state,
    }
    gz_path = snapshot_path.with_suffix(".json.gz")
    json_bytes = json.dumps(snapshot_data, ensure_ascii=False, indent=2).encode("utf-8")
    compressed = gzip.compress(json_bytes, compresslevel=6)
    gz_path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=str(gz_path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(compressed)
        if gz_path.exists():
            gz_path.unlink()
        os.replace(tmp_path, str(gz_path))
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
    if snapshot_path.exists():
        try:
            snapshot_path.unlink()
        except OSError:
            pass
    _cleanup_snapshots(workflow_id, project_path)
    return gz_path


def _cleanup_snapshots(
    workflow_id: str,
    project_path: str,
    max_snapshots: int | None = None,
    ttl_days: int | None = None,
) -> dict[str, Any]:
    config = _get_snapshot_cleanup_config()
    if max_snapshots is None:
        max_snapshots = config["max_snapshots_per_workflow"]
    if ttl_days is None:
        ttl_days = config["snapshot_ttl_days"]

    snapshot_dir = _get_snapshot_dir(project_path)
    if not snapshot_dir.exists():
        return {"deleted_count": 0, "remaining_count": 0}

    snapshot_files = sorted(
        list(snapshot_dir.glob(f"{workflow_id}_*.json")) + list(snapshot_dir.glob(f"{workflow_id}_*.json.gz")),
        key=lambda f: f.stat().st_mtime,
    )

    if not snapshot_files:
        return {"deleted_count": 0, "remaining_count": 0}

    ttl_cutoff = time.time() - timedelta(days=ttl_days).total_seconds()
    deleted_count = 0
    to_keep: list[Path] = []

    for fpath in snapshot_files:
        mtime = fpath.stat().st_mtime
        if mtime < ttl_cutoff:
            try:
                fpath.unlink()
                deleted_count += 1
                logger.debug("Deleted expired snapshot: %s (mtime=%.0f, cutoff=%.0f)", fpath.name, mtime, ttl_cutoff)
            except OSError as exc:
                logger.warning("Failed to delete snapshot %s: %s", fpath.name, exc)
            continue
        to_keep.append(fpath)

    if len(to_keep) > max_snapshots:
        excess = len(to_keep) - max_snapshots
        for fpath in to_keep[:excess]:
            try:
                fpath.unlink()
                deleted_count += 1
                logger.debug("Deleted excess snapshot: %s", fpath.name)
            except OSError as exc:
                logger.warning("Failed to delete snapshot %s: %s", fpath.name, exc)
        to_keep = to_keep[excess:]

    remaining_count = len(to_keep)
    if deleted_count > 0:
        logger.info("Snapshot cleanup for %s: deleted %d, remaining %d", workflow_id, deleted_count, remaining_count)
    return {"deleted_count": deleted_count, "remaining_count": remaining_count}


def _cleanup_all_snapshots() -> dict[str, dict[str, Any]]:
    results: dict[str, dict[str, Any]] = {}
    with _workflows_lock:
        snapshot = dict(_ACTIVE_WORKFLOWS)
    for workflow_id, entry in snapshot.items():
        project_path = entry.get("project_path", ".")
        results[workflow_id] = _cleanup_snapshots(workflow_id, project_path)
    return results


def _load_snapshot_file(fpath: Path) -> dict[str, Any] | None:
    if fpath.suffix == ".gz":
        try:
            with gzip.open(fpath, 'rb') as f:
                return json.loads(f.read().decode('utf-8'))
        except (gzip.BadGzipFile, json.JSONDecodeError, OSError):
            return None
    else:
        try:
            return json.loads(fpath.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None


def _list_snapshots(workflow_id: str, project_path: str) -> list[dict[str, Any]]:
    snapshot_dir = _get_snapshot_dir(project_path)
    if not snapshot_dir.exists():
        return []
    snapshots: list[dict[str, Any]] = []
    snapshot_files = list(snapshot_dir.glob(f"{workflow_id}_*.json")) + list(snapshot_dir.glob(f"{workflow_id}_*.json.gz"))
    for fpath in sorted(snapshot_files):
        data = _load_snapshot_file(fpath)
        if data is None:
            continue
        snapshots.append({
            "phase": data.get("phase", 0),
            "timestamp": data.get("timestamp", 0),
            "time_iso": data.get("time_iso", ""),
            "filename": fpath.name,
            "state_summary": {
                "workflow": data.get("state", {}).get("workflow", ""),
                "current_phase": data.get("state", {}).get("current_phase", 0),
                "status": data.get("state", {}).get("status", ""),
            },
        })
    return snapshots


def _load_latest_snapshot(workflow_id: str, project_path: str, target_phase: int | None = None) -> dict[str, Any] | None:
    snapshot_dir = _get_snapshot_dir(project_path)
    if not snapshot_dir.exists():
        return None
    candidates: list[tuple[int, dict[str, Any]]] = []
    snapshot_files = list(snapshot_dir.glob(f"{workflow_id}_*.json")) + list(snapshot_dir.glob(f"{workflow_id}_*.json.gz"))
    for fpath in snapshot_files:
        data = _load_snapshot_file(fpath)
        if data is None:
            continue
        phase = data.get("phase", 0)
        if target_phase is not None and phase != target_phase:
            continue
        candidates.append((data.get("timestamp", 0), data))
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1]


def register(mcp: FastMCP) -> None:
    @mcp.tool(
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=False,
            openWorldHint=False,
        )
    )
    async def workflow_dispatch(
        action: str,
        workflow: str | None = None,
        project_path: str = ".",
        workflow_id: str | None = None,
        phase_action: str | None = None,
        snapshot_phase: int | None = None,
    ) -> dict[str, Any]:
        """工作流调度：启动/查询/中止/阶段推进工作流执行。支持sdd-tdd-full/medium/fast等15种工作流，返回工作流实例ID和当前状态。"""
        validated, err = validate_input(WorkflowDispatchInput, action=action, workflow=workflow, project_path=project_path, workflow_id=workflow_id, phase_action=phase_action, snapshot_phase=snapshot_phase)
        if err:
            return err
        logger.info("workflow_dispatch called: action=%s", action)
        try:
            if action == "start":
                if not workflow:
                    return make_error_response(ValueError("start操作需要workflow参数"), error_code=ERR_VALIDATION)
                result = _start_workflow(workflow, project_path)
                if result.get("error"):
                    return result
                return make_success_response(result)
            elif action == "status":
                if not workflow_id:
                    with _workflows_lock:
                        all_workflows = dict(_ACTIVE_WORKFLOWS)
                    disk_workflows = _load_all_workflows()
                    for wid, data in disk_workflows.items():
                        if wid not in all_workflows:
                            all_workflows[wid] = data
                    return make_success_response({"workflows": all_workflows})
                result = _get_workflow_status(workflow_id)
                if result.get("error"):
                    return result
                return make_success_response(result)
            elif action == "abort":
                if not workflow_id:
                    return make_error_response(ValueError("abort操作需要workflow_id参数"), error_code=ERR_VALIDATION)
                result = _abort_workflow(workflow_id)
                if result.get("error"):
                    return result
                return make_success_response(result)
            elif action == "phase":
                if not workflow_id:
                    return make_error_response(ValueError("phase操作需要workflow_id参数"), error_code=ERR_VALIDATION)
                if not phase_action:
                    return make_error_response(ValueError("phase操作需要phase_action参数: advance, current"), error_code=ERR_VALIDATION)
                if phase_action == "advance":
                    result = _advance_phase(workflow_id)
                    if result.get("error"):
                        return result
                    return make_success_response(result)
                elif phase_action == "current":
                    result = _current_phase(workflow_id)
                    if result.get("error"):
                        return result
                    return make_success_response(result)
                else:
                    return make_error_response(ValueError(f"未知phase_action: {phase_action}，支持: advance, current"), error_code=ERR_VALIDATION)
            elif action == "recover":
                if not workflow_id or workflow_id.strip() == "":
                    return make_error_response(ValueError("workflow_id不能为空"), error_code=ERR_VALIDATION)
                snapshot = _load_latest_snapshot(workflow_id, project_path, snapshot_phase)
                if snapshot is None:
                    return make_error_response(XuanstoMCPError("RECOVER_FAILED", f"No snapshot found for workflow {workflow_id}"), error_code=ERR_INTERNAL)
                state = snapshot.get("state", {})
                with _workflows_lock:
                    if workflow_id and workflow_id in _ACTIVE_WORKFLOWS:
                        _ACTIVE_WORKFLOWS[workflow_id] = state.copy()
                _persist_workflow(workflow_id, state.copy())
                _persist_active_workflows()
                return make_success_response({
                    "action": "recover",
                    "workflow_id": workflow_id,
                    "recovered_phase": snapshot.get("phase", 0),
                    "snapshot_time": snapshot.get("time_iso", ""),
                    "state": state,
                })
            elif action == "snapshots":
                snapshots = _list_snapshots(workflow_id or "", project_path)
                return make_success_response({
                    "action": "snapshots",
                    "workflow_id": workflow_id,
                    "snapshots": snapshots,
                    "total": len(snapshots),
                })
            else:
                return make_error_response(ValueError(f"未知操作: {action}，支持: start, status, abort, phase, recover, snapshots"), error_code=ERR_VALIDATION)
        except Exception as e:
            logger.error("workflow_dispatch error: %s", e)
            return make_error_response(e)
