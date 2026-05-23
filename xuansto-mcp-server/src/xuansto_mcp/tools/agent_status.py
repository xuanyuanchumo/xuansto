from __future__ import annotations

import json
import re
import threading
import time
import uuid
from datetime import datetime, timezone
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from ..core.config import REFERENCES_DIR, AGENTS_DIR, WORK_DIR
from ..core.errors import make_error_response, make_success_response, XuanstoMCPError, ERR_VALIDATION, ERR_NOT_FOUND, ERR_INTERNAL, ERR_RATE_LIMIT, ERR_PERMISSION
from ..core import atomic_write
from ..core.logging_config import get_logger
from ..core.validator import validate_input
from ..models.schemas import AgentStatusInput

logger = get_logger("agent_status")

PHASE_AGENT_MAP: dict[int, list[str]] = {
    0: ["Orchestrator", "Design System Generator", "UI Designer"],
    1: ["Product Manager", "Brainstorming Facilitator", "Knowledge Manager"],
    2: ["System Architect", "Technical Writer", "Knowledge Manager"],
    3: ["Test Architect", "Unit Tester"],
    4: ["Backend Developer", "Frontend Developer", "Fullstack Developer", "Subagent Dispatcher", "Task Coordinator"],
    5: ["Security Auditor", "AI Penetration Tester", "E2E Tester", "Integration Tester"],
    6: ["QA Engineer", "UX Designer", "Compliance Officer"],
    7: ["Refactoring Specialist", "Code Reviewer", "History Analyzer"],
    8: ["Build-Release Engineer", "CI/CD Specialist", "Runtime Supervisor"],
}

def _parse_agent_registry(registry_path: Path) -> list[dict[str, Any]]:
    if not registry_path.exists():
        return []
    content = registry_path.read_text(encoding="utf-8")
    agents = []
    current_layer = ""
    for line in content.splitlines():
        layer_match = re.match(r"^#+\s*(.+层|.+Layer)", line)
        if layer_match:
            current_layer = layer_match.group(1).strip()
            continue
        agent_match = re.match(r"^\s*[-*]\s*\*\*(.+?)\*\*", line)
        if agent_match:
            agents.append({"name": agent_match.group(1).strip(), "layer": current_layer})
    return agents

def _get_agent_detail(agent_name: str, agents_dir: Path) -> dict[str, Any]:
    for subdir in agents_dir.iterdir():
        if subdir.is_dir():
            agent_file = subdir / f"{agent_name.lower().replace(' ', '-')}.md"
            if agent_file.exists():
                content = agent_file.read_text(encoding="utf-8")
                return {"name": agent_name, "file": str(agent_file), "content_length": len(content)}
    detail_dir = REFERENCES_DIR / "agent-details"
    if detail_dir.exists():
        for f in detail_dir.glob("*.md"):
            if agent_name.lower().replace(" ", "-") in f.stem.lower():
                content = f.read_text(encoding="utf-8")
                return {"name": agent_name, "file": str(f), "content_length": len(content)}
    return {"name": agent_name, "detail": "未找到详细定义文件"}

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
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        )
    )
    async def agent_status(
        action: str,
        phase: int | None = None,
        agent_name: str | None = None,
        agent_type: str | None = None,
        capabilities: list[str] | None = None,
        agent_id: str | None = None,
        task: str | None = None,
    ) -> dict[str, Any]:
        """Agent状态查询：列出全部57个Agent、按Phase查询活跃Agent、查询单个Agent详情、调度Agent(schedule规划中)。返回Agent名称、层级、模型偏好和分配状态。"""
        validated, err = validate_input(AgentStatusInput, action=action, phase=phase, agent_name=agent_name, agent_type=agent_type, capabilities=capabilities, agent_id=agent_id, task=task)
        if err:
            return err
        logger.info("agent_status called: action=%s", action)
        if action == "list":
            registry = REFERENCES_DIR / "agent-registry.md"
            agents = _parse_agent_registry(registry)
            return make_success_response({"agents": agents, "total": len(agents)})
        elif action == "by_phase":
            if phase is None:
                return make_error_response(ValueError("by_phase操作需要phase参数(0-8)"), error_code=ERR_VALIDATION)
            phase_agents = PHASE_AGENT_MAP.get(phase, [])
            return make_success_response({"phase": phase, "agents": phase_agents, "total": len(phase_agents)})
        elif action == "detail":
            if not agent_name:
                return make_error_response(ValueError("detail操作需要agent_name参数"), error_code=ERR_VALIDATION)
            detail = _get_agent_detail(agent_name, AGENTS_DIR)
            return make_success_response(detail)
        elif action == "create":
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
        elif action == "match":
            if not capabilities:
                return make_error_response(XuanstoMCPError("VALIDATION_ERROR", "capabilities is required for match action"), error_code=ERR_VALIDATION)
            required = set(capabilities)
            matches: list[dict[str, Any]] = []
            with _agents_lock:
                for inst in _AGENT_INSTANCES.values():
                    inst_caps = set(inst.capabilities)
                    overlap = required & inst_caps
                    if overlap:
                        coverage = len(overlap) / len(required) if required else 0.0
                        matches.append({
                            "agent_id": inst.agent_id,
                            "agent_type": inst.agent_type,
                            "capabilities": inst.capabilities,
                            "status": inst.status,
                            "coverage": round(coverage, 2),
                            "matched_capabilities": sorted(overlap),
                            "missing_capabilities": sorted(required - inst_caps),
                        })
            matches.sort(key=lambda x: x["coverage"], reverse=True)
            return make_success_response({
                "action": "match",
                "required_capabilities": sorted(required),
                "matches": matches,
                "total": len(matches),
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
                "available_actions": ["create", "match", "assign", "release", "list", "destroy", "status"],
            })
        else:
            return make_error_response(ValueError(f"未知操作: {action}，支持: list, by_phase, detail, create, match, assign, release, instance_status, destroy, schedule"), error_code=ERR_VALIDATION)
