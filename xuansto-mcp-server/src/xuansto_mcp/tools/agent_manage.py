from __future__ import annotations

import json
import threading
import time
import uuid
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from ..core.config import WORK_DIR
from ..core.errors import make_error_response, make_success_response, XuanstoMCPError, ERR_VALIDATION, ERR_NOT_FOUND, ERR_RATE_LIMIT, ERR_PERMISSION
from ..core import atomic_write
from ..core.logging_config import get_logger
from ..core.validator import validate_input
from ..models.schemas import AgentManageInput

logger = get_logger("agent_manage")


@dataclass
class _AgentInstance:
    agent_id: str
    agent_type: str
    capabilities: list[str]
    status: str = "idle"
    task: str = ""
    created_at: float = field(default_factory=time.time)
    history: list[dict[str, Any]] = field(default_factory=list)
    last_active_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    task_count: int = 0
    total_duration_ms: int = 0
    _task_start: float = 0


_AGENT_INSTANCES: dict[str, _AgentInstance] = {}

_agents_lock = threading.Lock()

_MAX_AGENT_INSTANCES = 20


def _persist_agent_instances() -> None:
    persist_dir = WORK_DIR
    persist_dir.mkdir(parents=True, exist_ok=True)
    with _agents_lock:
        data = {
            aid: {
                "agent_id": inst.agent_id,
                "agent_type": inst.agent_type,
                "capabilities": inst.capabilities,
                "status": inst.status,
                "task": inst.task,
                "created_at": inst.created_at,
                "history": inst.history,
                "last_active_at": inst.last_active_at,
                "task_count": inst.task_count,
                "total_duration_ms": inst.total_duration_ms,
            }
            for aid, inst in _AGENT_INSTANCES.items()
        }
    path = persist_dir / "agent_instances.json"
    atomic_write(path, json.dumps(data, ensure_ascii=False, indent=2))
    logger.info("Persisted %d agent instances to %s", len(data), path)


def _load_agent_instances() -> None:
    path = WORK_DIR / "agent_instances.json"
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        with _agents_lock:
            for aid, d in raw.items():
                _AGENT_INSTANCES[aid] = _AgentInstance(
                    agent_id=d["agent_id"],
                    agent_type=d["agent_type"],
                    capabilities=d["capabilities"],
                    status=d.get("status", "idle"),
                    task=d.get("task", ""),
                    created_at=d.get("created_at", time.time()),
                    history=d.get("history", []),
                    last_active_at=d.get("last_active_at", datetime.now(timezone.utc).isoformat()),
                    task_count=d.get("task_count", 0),
                    total_duration_ms=d.get("total_duration_ms", 0),
                )
        logger.info("Loaded %d agent instances from %s", len(raw), path)
    except FileNotFoundError:
        pass
    except (json.JSONDecodeError, KeyError):
        logger.warning("Failed to parse agent instances from %s", path)


def load_on_startup() -> None:
    _load_agent_instances()


def register(mcp: FastMCP) -> None:
    @mcp.tool(
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=True,
            idempotentHint=False,
            openWorldHint=False,
        )
    )
    async def agent_manage(
        action: str,
        agent_type: str | None = None,
        capabilities: list[str] | None = None,
        agent_id: str | None = None,
        task: str | None = None,
    ) -> dict[str, Any]:
        """Agent实例管理：创建/分配/释放/销毁Agent实例，查询实例状态，调度规划。变更操作，非只读。"""
        validated, err = validate_input(AgentManageInput, action=action, agent_type=agent_type, capabilities=capabilities, agent_id=agent_id, task=task)
        if err:
            return err
        logger.info("agent_manage called: action=%s", action)
        try:
            if action == "create":
                if not agent_type:
                    return make_error_response(XuanstoMCPError("VALIDATION_ERROR", "agent_type is required for create action"), error_code=ERR_VALIDATION)
                new_id = f"agent-{uuid.uuid4().hex[:8]}"
                caps = capabilities or []
                now_iso = datetime.now(timezone.utc).isoformat()
                instance = _AgentInstance(agent_id=new_id, agent_type=agent_type, capabilities=caps, last_active_at=now_iso)
                with _agents_lock:
                    if len(_AGENT_INSTANCES) >= _MAX_AGENT_INSTANCES:
                        return make_error_response(RuntimeError(f"Agent实例数量已达上限({_MAX_AGENT_INSTANCES})"), error_code=ERR_RATE_LIMIT)
                    _AGENT_INSTANCES[new_id] = instance
                _persist_agent_instances()
                return make_success_response({
                    "action": "create",
                    "agent_id": new_id,
                    "agent_type": agent_type,
                    "capabilities": caps,
                    "status": "idle",
                    "created_at": now_iso,
                    "last_active_at": now_iso,
                    "task_count": 0,
                    "total_duration_ms": 0,
                })
            elif action == "assign":
                if not agent_id or not task:
                    return make_error_response(XuanstoMCPError("VALIDATION_ERROR", "agent_id and task are required for assign action"), error_code=ERR_VALIDATION)
                with _agents_lock:
                    if agent_id not in _AGENT_INSTANCES:
                        return make_error_response(XuanstoMCPError("NOT_FOUND", f"Agent {agent_id} not found"), error_code=ERR_NOT_FOUND)
                    inst = _AGENT_INSTANCES[agent_id]
                    if inst.status == "busy":
                        return make_error_response(XuanstoMCPError("AGENT_BUSY", f"Agent {agent_id} is busy with: {inst.task}"), error_code=ERR_PERMISSION)
                    inst.status = "busy"
                    inst.task = task
                    inst.task_count += 1
                    inst.last_active_at = datetime.now(timezone.utc).isoformat()
                    inst._task_start = time.time()
                    inst.history.append({"action": "assign", "task": task, "timestamp": time.time()})
                _persist_agent_instances()
                return make_success_response({
                    "action": "assign",
                    "agent_id": agent_id,
                    "task": task,
                    "status": "busy",
                    "task_count": inst.task_count,
                    "last_active_at": inst.last_active_at,
                })
            elif action == "release":
                if not agent_id:
                    return make_error_response(XuanstoMCPError("VALIDATION_ERROR", "agent_id is required for release action"), error_code=ERR_VALIDATION)
                with _agents_lock:
                    if agent_id not in _AGENT_INSTANCES:
                        return make_error_response(XuanstoMCPError("NOT_FOUND", f"Agent {agent_id} not found"), error_code=ERR_NOT_FOUND)
                    inst = _AGENT_INSTANCES[agent_id]
                    if inst.status != "busy":
                        return make_error_response(XuanstoMCPError("VALIDATION_ERROR", f"Agent {agent_id} is not busy (status: {inst.status})"), error_code=ERR_VALIDATION)
                    duration_ms = int((time.time() - inst._task_start) * 1000) if inst._task_start > 0 else 0
                    inst.total_duration_ms += duration_ms
                    completed_task = inst.task
                    inst.status = "idle"
                    inst.task = ""
                    inst._task_start = 0
                    inst.last_active_at = datetime.now(timezone.utc).isoformat()
                    inst.history.append({"action": "release", "task": completed_task, "duration_ms": duration_ms, "timestamp": time.time()})
                _persist_agent_instances()
                return make_success_response({
                    "action": "release",
                    "agent_id": agent_id,
                    "status": "idle",
                    "completed_task": completed_task,
                    "duration_ms": duration_ms,
                    "total_duration_ms": inst.total_duration_ms,
                    "task_count": inst.task_count,
                    "last_active_at": inst.last_active_at,
                })
            elif action == "instance_status":
                if not agent_id:
                    return make_error_response(XuanstoMCPError("VALIDATION_ERROR", "agent_id is required for instance_status action"), error_code=ERR_VALIDATION)
                with _agents_lock:
                    if agent_id not in _AGENT_INSTANCES:
                        return make_error_response(XuanstoMCPError("NOT_FOUND", f"Agent {agent_id} not found"), error_code=ERR_NOT_FOUND)
                    inst = _AGENT_INSTANCES[agent_id]
                    result = {
                        "action": "instance_status",
                        "agent_id": inst.agent_id,
                        "agent_type": inst.agent_type,
                        "capabilities": inst.capabilities,
                        "status": inst.status,
                        "task": inst.task,
                        "created_at": inst.created_at,
                        "history_count": len(inst.history),
                        "last_active_at": inst.last_active_at,
                        "task_count": inst.task_count,
                        "total_duration_ms": inst.total_duration_ms,
                    }
                return make_success_response(result)
            elif action == "destroy":
                if not agent_id:
                    return make_error_response(XuanstoMCPError("VALIDATION_ERROR", "agent_id is required for destroy action"), error_code=ERR_VALIDATION)
                with _agents_lock:
                    if agent_id not in _AGENT_INSTANCES:
                        return make_error_response(XuanstoMCPError("NOT_FOUND", f"Agent {agent_id} not found"), error_code=ERR_NOT_FOUND)
                    inst = _AGENT_INSTANCES.pop(agent_id)
                    if inst.status == "busy" and inst._task_start > 0:
                        inst.total_duration_ms += int((time.time() - inst._task_start) * 1000)
                _persist_agent_instances()
                return make_success_response({
                    "action": "destroy",
                    "agent_id": agent_id,
                    "status": "destroyed",
                    "task_count": inst.task_count,
                    "total_duration_ms": inst.total_duration_ms,
                    "last_active_at": inst.last_active_at,
                })
            elif action == "schedule":
                return make_success_response({
                    "status": "planned",
                    "message": "Agent调度引擎规划中，当前仅支持手动create/match/assign",
                    "available_actions": ["create", "assign", "release", "destroy", "instance_status"],
                })
            else:
                return make_error_response(ValueError(f"未知操作: {action}，支持: create, assign, release, instance_status, destroy, schedule"), error_code=ERR_VALIDATION)
        except Exception as e:
            logger.error("agent_manage error: %s", e)
            return make_error_response(e)
