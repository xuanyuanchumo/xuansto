from __future__ import annotations

import json
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from ..core import atomic_write
from ..core.config import WORK_DIR
from ..core.database import delete_agent_state, load_agent_states, save_agent_state
from ..core.errors import (
    ERR_NOT_FOUND,
    ERR_PERMISSION,
    ERR_RATE_LIMIT,
    ERR_VALIDATION,
    XuanstoMCPError,
    make_error_response,
    make_success_response,
)
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

_file_backup_enabled: bool = False


def _persist_agent_instances() -> None:
    if not _file_backup_enabled:
        return
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
                if aid in _AGENT_INSTANCES:
                    continue
                _AGENT_INSTANCES[aid] = _AgentInstance(
                    agent_id=d["agent_id"],
                    agent_type=d["agent_type"],
                    capabilities=d["capabilities"],
                    status=d.get("status", "idle"),
                    task=d.get("task", ""),
                    created_at=d.get("created_at", datetime.now(timezone.utc).isoformat()),
                    history=d.get("history", []),
                    last_active_at=d.get("last_active_at", datetime.now(timezone.utc).isoformat()),
                    task_count=d.get("task_count", 0),
                    total_duration_ms=d.get("total_duration_ms", 0),
                )
        logger.info("Loaded %d agent instances from %s (file fallback)", len(raw), path)
    except FileNotFoundError:
        pass
    except (json.JSONDecodeError, KeyError):
        logger.warning("Failed to parse agent instances from %s", path)


def load_on_startup() -> None:
    restored_from_db = 0
    try:
        db_agents = load_agent_states(status="active")
        with _agents_lock:
            for db_agent in db_agents:
                aid = db_agent.get("agent_id", "")
                if aid and aid not in _AGENT_INSTANCES:
                    config = db_agent.get("config_json", {})
                    caps = config.get("capabilities", []) if isinstance(config, dict) else []
                    _AGENT_INSTANCES[aid] = _AgentInstance(
                        agent_id=aid,
                        agent_type=db_agent.get("agent_type", "unknown"),
                        capabilities=caps,
                        status=config.get("status", "idle") if isinstance(config, dict) else "idle",
                        task=config.get("task", "") if isinstance(config, dict) else "",
                        created_at=db_agent.get("created_at", datetime.now(timezone.utc).isoformat()),
                        last_active_at=datetime.now(timezone.utc).isoformat(),
                    )
                    restored_from_db += 1
        if restored_from_db > 0:
            logger.info("Restored %d agent instances from SQLite", restored_from_db)
    except Exception as exc:
        logger.warning("Failed to restore agent instances from SQLite: %s", exc)

    _load_agent_instances()


def _inline_agent_manage(action: str, **kwargs: Any) -> dict[str, Any]:
    if action == "create":
        return {
            "action": "create",
            "agent_id": "inline-agent-0",
            "agent_type": kwargs.get("agent_type", "unknown"),
            "capabilities": kwargs.get("capabilities", []),
            "status": "idle",
            "managed": True,
        }
    elif action == "assign":
        return {
            "action": "assign",
            "agent_id": kwargs.get("agent_id", ""),
            "task": kwargs.get("task", ""),
            "status": "busy",
            "managed": True,
        }
    elif action == "release":
        return {
            "action": "release",
            "agent_id": kwargs.get("agent_id", ""),
            "status": "idle",
            "managed": True,
        }
    elif action == "destroy":
        return {
            "action": "destroy",
            "agent_id": kwargs.get("agent_id", ""),
            "status": "destroyed",
            "managed": True,
        }
    elif action == "instance_status":
        return {
            "action": "instance_status",
            "agent_id": kwargs.get("agent_id", ""),
            "status": "unknown",
            "managed": True,
        }
    elif action == "schedule":
        return {
            "action": "schedule",
            "status": "planned",
            "managed": True,
        }
    return {"action": action, "managed": False}


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
                try:
                    save_agent_state(
                        agent_id=new_id,
                        name=new_id,
                        agent_type=agent_type,
                        status="active",
                        config={"capabilities": caps, "status": "idle", "task": ""},
                    )
                except Exception:
                    logger.warning("Failed to persist agent state to SQLite for %s", new_id)
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
                    inst.history.append({"action": "assign", "task": task, "timestamp": datetime.now(timezone.utc).isoformat()})
                try:
                    save_agent_state(
                        agent_id=agent_id,
                        name=agent_id,
                        agent_type=inst.agent_type,
                        status="active",
                        config={"capabilities": inst.capabilities, "status": "busy", "task": task},
                    )
                except Exception:
                    logger.warning("Failed to update agent state in SQLite for %s", agent_id)
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
                    inst.history.append({"action": "release", "task": completed_task, "duration_ms": duration_ms, "timestamp": datetime.now(timezone.utc).isoformat()})
                try:
                    save_agent_state(
                        agent_id=agent_id,
                        name=agent_id,
                        agent_type=inst.agent_type,
                        status="active",
                        config={"capabilities": inst.capabilities, "status": "idle", "task": ""},
                    )
                except Exception:
                    logger.warning("Failed to update agent state in SQLite for %s", agent_id)
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
                try:
                    delete_agent_state(agent_id)
                except Exception:
                    logger.warning("Failed to delete agent state from SQLite for %s", agent_id)
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
