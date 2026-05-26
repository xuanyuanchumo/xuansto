from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from ..core.config import WORK_DIR
from ..core.errors import ERR_VALIDATION, make_error_response, make_success_response
from ..core.logging_config import get_logger
from ..core.notifications import notify
from ..core.validator import validate_input
from ..models.schemas import TokenBudgetInput

logger = get_logger("token_budget")

PHASE_TOKEN_BUDGET_MAP: dict[str, int] = {
    "skeleton": 2000,
    "functional": 5000,
    "enhanced": 10000,
    "full": 20000,
}

BUDGET_FILE = WORK_DIR / "token_budget.json"

DEFAULT_PHASE_ALLOCATIONS = {
    "0": 5000,
    "1": 10000,
    "2": 15000,
    "3": 10000,
    "4": 30000,
    "5": 15000,
    "6": 10000,
    "7": 10000,
    "8": 5000,
}

RECOMMENDATION_MAP = {
    ("small", "low"): {"total": 50000, "allocations": {"0": 3000, "1": 5000, "2": 8000, "3": 5000, "4": 15000, "5": 7000, "6": 3000, "7": 3000, "8": 1000}},
    ("small", "medium"): {"total": 80000, "allocations": {"0": 5000, "1": 8000, "2": 12000, "3": 8000, "4": 25000, "5": 10000, "6": 5000, "7": 5000, "8": 2000}},
    ("small", "high"): {"total": 120000, "allocations": {"0": 7000, "1": 12000, "2": 18000, "3": 10000, "4": 38000, "5": 15000, "6": 8000, "7": 8000, "8": 4000}},
    ("medium", "low"): {"total": 100000, "allocations": {"0": 6000, "1": 10000, "2": 15000, "3": 8000, "4": 30000, "5": 12000, "6": 7000, "7": 7000, "8": 5000}},
    ("medium", "medium"): {"total": 150000, "allocations": {"0": 8000, "1": 15000, "2": 22000, "3": 12000, "4": 45000, "5": 18000, "6": 10000, "7": 12000, "8": 8000}},
    ("medium", "high"): {"total": 200000, "allocations": {"0": 12000, "1": 20000, "2": 30000, "3": 15000, "4": 60000, "5": 25000, "6": 13000, "7": 15000, "8": 10000}},
    ("large", "low"): {"total": 200000, "allocations": {"0": 12000, "1": 20000, "2": 30000, "3": 15000, "4": 60000, "5": 25000, "6": 13000, "7": 15000, "8": 10000}},
    ("large", "medium"): {"total": 300000, "allocations": {"0": 18000, "1": 30000, "2": 45000, "3": 20000, "4": 90000, "5": 35000, "6": 20000, "7": 22000, "8": 20000}},
    ("large", "high"): {"total": 500000, "allocations": {"0": 30000, "1": 50000, "2": 75000, "3": 30000, "4": 150000, "5": 60000, "6": 35000, "7": 40000, "8": 30000}},
}


def _load_budget() -> dict[str, Any]:
    if BUDGET_FILE.exists():
        try:
            data = json.loads(BUDGET_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except (json.JSONDecodeError, OSError):
            pass
    sqlite_data = _restore_from_sqlite()
    if sqlite_data is not None:
        return sqlite_data
    return {}


def _save_budget(budget: dict[str, Any]) -> None:
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    BUDGET_FILE.write_text(
        json.dumps(budget, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    _persist_to_sqlite(budget)


def _persist_to_sqlite(budget: dict[str, Any]) -> None:
    try:
        from ..core.database import persist_state
        session_id = budget.get("session_id", "default")
        persist_state("token_budget_states", {
            "id": f"budget_{session_id}",
            "total_budget": budget.get("total_budget", 0),
            "used": budget.get("used", 0),
            "phase_allocations_json": budget.get("phase_allocations", DEFAULT_PHASE_ALLOCATIONS),
            "usage_by_phase_json": budget.get("usage_by_phase", {}),
            "session_id": session_id,
        })
    except Exception:
        pass


def _restore_from_sqlite(session_id: str = "default") -> dict[str, Any] | None:
    try:
        from ..core.database import load_state
        results = load_state("token_budget_states", {"id": f"budget_{session_id}"})
        if results:
            row = results[0]
            return {
                "total_budget": row.get("total_budget", 0),
                "used": row.get("used", 0),
                "phase_allocations": row.get("phase_allocations_json", DEFAULT_PHASE_ALLOCATIONS),
                "usage_by_phase": row.get("usage_by_phase_json", {}),
                "session_id": row.get("session_id", session_id),
            }
    except Exception:
        pass
    return None


def _get_status() -> dict[str, Any]:
    budget = _load_budget()
    if not budget:
        return {
            "total_budget": 0,
            "used": 0,
            "remaining": 0,
            "phase_allocations": DEFAULT_PHASE_ALLOCATIONS,
            "usage_by_phase": {},
            "status": "no_budget_set",
        }
    total = budget.get("total_budget", 0)
    used = budget.get("used", 0)
    return {
        "total_budget": total,
        "used": used,
        "remaining": total - used,
        "phase_allocations": budget.get("phase_allocations", DEFAULT_PHASE_ALLOCATIONS),
        "usage_by_phase": budget.get("usage_by_phase", {}),
    }


def _set_budget(
    total_budget: int | None = None,
    phase_allocations: dict[str, int] | None = None,
) -> dict[str, Any]:
    budget = _load_budget()
    if total_budget is not None:
        budget["total_budget"] = total_budget
    if phase_allocations is not None:
        budget["phase_allocations"] = phase_allocations
    budget["updated_at"] = datetime.now().isoformat()
    if "used" not in budget:
        budget["used"] = 0
    if "usage_by_phase" not in budget:
        budget["usage_by_phase"] = {}
    _save_budget(budget)
    notify(f"Token budget updated: total={budget.get('total_budget', 0)}", "info")
    enforcement = _check_and_enforce(budget.get("total_budget", 0), budget.get("used", 0))
    return {
        "total_budget": budget.get("total_budget", 0),
        "phase_allocations": budget.get("phase_allocations", DEFAULT_PHASE_ALLOCATIONS),
        "updated_at": budget["updated_at"],
        "enforcement": enforcement,
    }


def _set_budget_from_phase(phase: str) -> dict[str, Any]:
    budget_value = PHASE_TOKEN_BUDGET_MAP.get(phase)
    if budget_value is None:
        valid_phases = ", ".join(sorted(PHASE_TOKEN_BUDGET_MAP.keys()))
        return make_error_response(ValueError(f"Unknown phase: {phase}. Valid phases: {valid_phases}"), error_code=ERR_VALIDATION)
    result = _set_budget(total_budget=budget_value)
    result["phase"] = phase
    result["budget_source"] = "phase_mapping"
    logger.info("Token budget set from phase '%s': %d", phase, budget_value)
    notify(f"Token budget set from phase '{phase}': {budget_value}", "info")
    return result


def _recommend(
    project_size: str | None = None,
    complexity: str | None = None,
    team_size: int | None = None,
) -> dict[str, Any]:
    size = project_size or "medium"
    comp = complexity or "medium"
    key = (size, comp)
    rec = RECOMMENDATION_MAP.get(key, RECOMMENDATION_MAP[("medium", "medium")])
    result: dict[str, Any] = {
        "recommended_total": rec["total"],
        "recommended_allocations": rec["allocations"],
        "project_size": size,
        "complexity": comp,
    }
    if team_size is not None:
        multiplier = 1.0 + (team_size - 1) * 0.15
        result["team_size"] = team_size
        result["adjusted_total"] = int(rec["total"] * multiplier)
        result["adjustment_multiplier"] = round(multiplier, 2)
    return result


def _report(period: str = "session") -> dict[str, Any]:
    budget = _load_budget()
    usage_by_phase = budget.get("usage_by_phase", {})
    total_used = budget.get("used", 0)
    total_budget = budget.get("total_budget", 0)
    now = datetime.now()
    report: dict[str, Any] = {
        "period": period,
        "total_budget": total_budget,
        "total_used": total_used,
        "remaining": total_budget - total_used,
        "usage_pct": round((total_used / total_budget * 100) if total_budget > 0 else 0, 1),
        "usage_by_phase": usage_by_phase,
        "generated_at": now.isoformat(),
    }
    if period == "daily":
        report["date"] = now.strftime("%Y-%m-%d")
    elif period == "weekly":
        report["week"] = now.strftime("%Y-W%W")
    return report


def _check_and_enforce(total_budget: int, used: int) -> dict[str, Any]:
    if total_budget <= 0:
        return {"action": "none", "usage_ratio": 0.0}
    ratio = used / total_budget
    if ratio >= 0.95:
        logger.warning("Token usage at %.1f%% (>=95%%), triggering phase degradation", ratio * 100)
        return {"action": "degrade_phase", "reason": "token_usage_95pct", "usage_ratio": round(ratio, 4)}
    if ratio >= 0.8:
        logger.warning("Token usage at %.1f%% (>=80%%), recommending context compression", ratio * 100)
        return {"action": "context_compress", "reason": "token_usage_80pct", "usage_ratio": round(ratio, 4)}
    return {"action": "none", "usage_ratio": round(ratio, 4)}


def _inline_token_budget(action: str, **kwargs: Any) -> dict[str, Any]:
    if action == "status":
        return _get_status()
    elif action == "set_budget":
        return _set_budget(**{k: v for k, v in kwargs.items() if k in ("total_budget", "phase_allocations")})
    elif action == "set_from_phase":
        phase = kwargs.get("phase")
        if not phase:
            return make_error_response(ValueError("set_from_phase requires 'phase' parameter"), error_code=ERR_VALIDATION)
        return _set_budget_from_phase(phase)
    elif action == "recommend":
        return _recommend(**{k: v for k, v in kwargs.items() if k in ("project_size", "complexity", "team_size")})
    elif action == "report":
        return _report(**{k: v for k, v in kwargs.items() if k in ("period",)})
    return make_error_response(ValueError(f"未知操作: {action}"), error_code=ERR_VALIDATION)


def register(mcp: FastMCP) -> None:
    @mcp.tool(
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=False,
            openWorldHint=False,
        )
    )
    async def token_budget(
        action: str,
        total_budget: int | None = None,
        phase_allocations: dict[str, int] | None = None,
        project_size: str | None = None,
        complexity: str | None = None,
        team_size: int | None = None,
        period: str = "session",
        phase: str | None = None,
    ) -> dict[str, Any]:
        """Token预算管理：查询预算状态、设置预算、获取推荐、生成使用报告、运行时强制执行、基于阶段设置预算。status操作获取当前Token预算状态(总预算/已用/剩余/阶段分配)，set_budget操作设置Token总预算和阶段分配，set_from_phase操作根据阶段名称(skeleton/functional/enhanced/full)自动设置预算，recommend操作根据项目规模/复杂度/团队人数获取预算推荐，report操作生成Token使用报告，enforce操作检查Token使用率并触发强制措施(80%触发context_compress，95%触发degrade_phase)。"""
        validated, err = validate_input(TokenBudgetInput, action=action, total_budget=total_budget, phase_allocations=phase_allocations, project_size=project_size, complexity=complexity, team_size=team_size, period=period, phase=phase)
        if err:
            return err
        logger.info("token_budget called: action=%s", action)
        try:
            if action == "status":
                return make_success_response(_get_status())
            elif action == "set_budget":
                if total_budget is None and phase_allocations is None:
                    return make_error_response(ValueError("set_budget操作需要total_budget或phase_allocations参数"), error_code=ERR_VALIDATION)
                return make_success_response(_set_budget(total_budget, phase_allocations))
            elif action == "set_from_phase":
                if not phase:
                    return make_error_response(ValueError("set_from_phase操作需要phase参数(skeleton/functional/enhanced/full)"), error_code=ERR_VALIDATION)
                result = _set_budget_from_phase(phase)
                if result.get("status") == "error":
                    return result
                return make_success_response(result)
            elif action == "recommend":
                return make_success_response(_recommend(project_size, complexity, team_size))
            elif action == "report":
                return make_success_response(_report(period))
            elif action == "enforce":
                status = _get_status()
                total = status.get("total_budget", 0)
                used = status.get("used", 0)
                enforcement = _check_and_enforce(total, used)
                if enforcement["action"] == "degrade_phase":
                    from .resource_load_status import degrade_phase
                    degradation = degrade_phase()
                    enforcement["degradation_result"] = degradation
                return make_success_response({
                    "enforcement": enforcement,
                    "status": status,
                })
            else:
                return make_error_response(ValueError(f"未知操作: {action}，支持: status, set_budget, set_from_phase, recommend, report, enforce"), error_code=ERR_VALIDATION)
        except Exception as e:
            logger.error("token_budget error: %s", e)
            return make_error_response(e)
