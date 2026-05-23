from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from ..core.config import SESSION_DIR, PATTERNS_DIR
from ..core.errors import make_error_response, make_success_response, ERR_VALIDATION
from ..core.logging_config import get_logger
from ..core.validator import validate_input
from ..models.schemas import SessionManageInput

logger = get_logger("session_manage")

SESSION_TEMPLATE = """# Session {timestamp}

## 已完成任务
{completed}

## 未完成任务
{pending}

## 关键决策
{decisions}

## 经验沉淀
{experience}
"""


def _save_session(
    completed_tasks: list[str] | None = None,
    pending_tasks: list[str] | None = None,
    decisions: list[str] | None = None,
    experience: list[str] | None = None,
) -> dict[str, Any]:
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"session-{timestamp}.md"
    filepath = SESSION_DIR / filename

    completed = "\n".join(f"- {t}" for t in (completed_tasks or [])) or "- (无)"
    pending = "\n".join(f"- {t}" for t in (pending_tasks or [])) or "- (无)"
    dec = "\n".join(f"- {d}" for d in (decisions or [])) or "- (无)"
    exp = "\n".join(f"- {e}" for e in (experience or [])) or "- (无)"

    content = SESSION_TEMPLATE.format(
        timestamp=timestamp,
        completed=completed,
        pending=pending,
        decisions=dec,
        experience=exp,
    )
    filepath.write_text(content, encoding="utf-8")

    _cleanup_old_sessions()
    return {"path": str(filepath), "filename": filename}


def _load_last_session() -> dict[str, Any]:
    sessions = sorted(SESSION_DIR.glob("session-*.md"), reverse=True)
    if not sessions:
        return {"content": None, "message": "未找到会话记录"}
    content = sessions[0].read_text(encoding="utf-8")
    return {"content": content, "filename": sessions[0].name}


def _list_sessions() -> dict[str, Any]:
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    sessions = sorted(SESSION_DIR.glob("session-*.md"), reverse=True)
    return {"sessions": [s.name for s in sessions], "total": len(sessions)}


def _detect_patterns(error_log: list[str] | None = None) -> dict[str, Any]:
    PATTERNS_DIR.mkdir(parents=True, exist_ok=True)
    if not error_log:
        return {"patterns": [], "message": "无错误日志提供"}

    error_counts: dict[str, int] = {}
    for error in error_log:
        key = error.strip()
        error_counts[key] = error_counts.get(key, 0) + 1

    patterns = []
    for error, count in error_counts.items():
        if count >= 2:
            pattern_file = PATTERNS_DIR / f"pattern-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
            pattern_data = {
                "error": error,
                "count": count,
                "confidence": 0.40,
                "status": "draft",
                "created_at": datetime.now().isoformat(),
                "verified": False,
            }
            pattern_file.write_text(
                json.dumps(pattern_data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            patterns.append(pattern_data)

    return {"patterns": patterns, "total_detected": len(patterns)}


def _verify_pattern(pattern_path: str, success: bool = True) -> dict[str, Any]:
    path = Path(pattern_path)
    if not path.exists():
        return {"verified": False, "message": f"模式文件不存在: {pattern_path}"}

    data = json.loads(path.read_text(encoding="utf-8"))
    if success:
        data["confidence"] = min(data.get("confidence", 0.40) + 0.05, 1.0)
        if data["confidence"] >= 0.80:
            data["status"] = "verified"
            data["verified"] = True

    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"verified": True, "updated_confidence": data["confidence"], "status": data.get("status", "draft")}


def _track_session(
    current_phase: int | None = None,
    current_task: str | None = None,
    decisions: list[str] | None = None,
    pending_tasks: list[str] | None = None,
) -> dict[str, Any]:
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    current_path = SESSION_DIR / "current.json"
    existing: dict[str, Any] = {}
    if current_path.exists():
        try:
            existing = json.loads(current_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            existing = {}

    now = datetime.now().isoformat()
    existing_decisions: list[str] = existing.get("decisions", [])
    if decisions:
        existing_decisions.extend(decisions)

    completed_phases: list[int] = existing.get("completed_phases", [])
    if current_phase is not None and current_phase not in completed_phases:
        prev_phase = existing.get("current_phase")
        if prev_phase is not None and prev_phase not in completed_phases:
            completed_phases.append(prev_phase)
            completed_phases.sort()

    state: dict[str, Any] = {
        "current_phase": current_phase if current_phase is not None else existing.get("current_phase"),
        "current_task": current_task if current_task is not None else existing.get("current_task"),
        "decisions": existing_decisions,
        "pending_tasks": pending_tasks if pending_tasks is not None else existing.get("pending_tasks", []),
        "completed_phases": completed_phases,
        "timestamp": existing.get("timestamp", now),
        "updated_at": now,
    }

    current_path.write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return state


def _restore_session() -> dict[str, Any]:
    if _RESTORED_STATE is not None:
        state = _RESTORED_STATE.copy()
    else:
        current_path = SESSION_DIR / "current.json"
        if not current_path.exists():
            return {"status": "no_tracked_session", "message": "无追踪状态"}
        try:
            state = json.loads(current_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {"status": "no_tracked_session", "message": "无追踪状态"}
    sessions = sorted(SESSION_DIR.glob("session-*.md"), reverse=True)
    if sessions:
        state["last_session"] = sessions[0].read_text(encoding="utf-8")
    else:
        state["last_session"] = None
    return state


_RESTORED_STATE: dict[str, Any] | None = None


def restore_on_startup() -> dict[str, Any] | None:
    global _RESTORED_STATE
    current_path = SESSION_DIR / "current.json"
    if not current_path.exists():
        _RESTORED_STATE = None
        return None
    try:
        state: dict[str, Any] = json.loads(current_path.read_text(encoding="utf-8"))
        _RESTORED_STATE = state
        logger.info("Session restored from %s", current_path)
        return state
    except (json.JSONDecodeError, OSError):
        _RESTORED_STATE = None
        return None


def _cleanup_old_sessions(max_sessions: int = 10) -> None:
    sessions = sorted(SESSION_DIR.glob("session-*.md"), reverse=True)
    for old in sessions[max_sessions:]:
        old.unlink(missing_ok=True)


def register(mcp: FastMCP) -> None:
    @mcp.tool(
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=False,
            openWorldHint=False,
        )
    )
    async def session_manage(
        action: str,
        completed_tasks: list[str] | None = None,
        pending_tasks: list[str] | None = None,
        decisions: list[str] | None = None,
        experience: list[str] | None = None,
        error_log: list[str] | None = None,
        pattern_path: str | None = None,
        success: bool = True,
        current_phase: int | None = None,
        current_task: str | None = None,
    ) -> dict[str, Any]:
        """会话状态管理：保存/加载/列出会话记录，检测重复错误模式，验证经验模式，追踪/恢复会话状态。save操作持久化当前进度，detect操作从错误日志中提取模式，verify操作提升模式置信度，track操作追踪当前阶段状态，restore操作恢复上次追踪状态。"""
        validated, err = validate_input(SessionManageInput, action=action, completed_tasks=completed_tasks, pending_tasks=pending_tasks, decisions=decisions, experience=experience, error_log=error_log, pattern_path=pattern_path, success=success, current_phase=current_phase, current_task=current_task)
        if err:
            return err
        logger.info("session_manage called: action=%s", action)
        if action == "save":
            return make_success_response(_save_session(completed_tasks, pending_tasks, decisions, experience))
        elif action == "load":
            return make_success_response(_load_last_session())
        elif action == "list":
            return make_success_response(_list_sessions())
        elif action == "detect":
            return make_success_response(_detect_patterns(error_log))
        elif action == "verify":
            if not pattern_path:
                return make_error_response(ValueError("verify操作需要pattern_path参数"), error_code=ERR_VALIDATION)
            return make_success_response(_verify_pattern(pattern_path, success))
        elif action == "track":
            return make_success_response(_track_session(current_phase, current_task, decisions, pending_tasks))
        elif action == "restore":
            return make_success_response(_restore_session())
        else:
            return make_error_response(ValueError(f"未知操作: {action}，支持: save, load, list, detect, verify, track, restore"), error_code=ERR_VALIDATION)
