import json
from datetime import datetime, timezone

from ..config import make_response, make_error_response, mcp_available
from ._shared import MCP_JSON_SCHEMA_URI, _DEFAULT_BUDGET_ALLOCATIONS, _SIZE_MULTIPLIERS, _COMPLEXITY_MULTIPLIERS

if mcp_available:
    from mcp.types import Tool, TextContent, ToolAnnotations


def get_tool_definition():
    if not mcp_available:
        return None
    return Tool(
        name="token_budget",
        description=(
            "Token budget management: status, set_budget, recommend, report.\n\n"
            "Use this tool to manage token budgets across development phases. "
            "Check current budget status, set custom allocations, get recommendations based on "
            "project characteristics, and generate usage reports.\n\n"
            "Parameters:\n"
            "- action (string, required, enum: status|set_budget|recommend|report): Operation type.\n"
            "- total_budget (integer, optional, >=1000): Total token budget (set_budget action).\n"
            "- phase_allocations (object, optional): Per-phase allocation (set_budget action).\n"
            "- project_size (string, optional, enum: small|medium|large): Project size (recommend action).\n"
            "- complexity (string, optional, enum: low|medium|high): Complexity level (recommend action).\n"
            "- team_size (integer, optional, range 1-50): Team size (recommend action).\n"
            "- period (string, default='session', enum: daily|weekly|session): Report period (report action).\n\n"
            "Returns an object with:\n"
            "- action: The action performed.\n"
            "- total_budget: Total token budget.\n"
            "- used: Tokens used.\n"
            "- remaining: Tokens remaining.\n"
            "- phase_allocations: Per-phase allocation map.\n"
            "- usage_by_phase: Per-phase usage map.\n\n"
            "Example: Check budget status:\n"
            '{"action": "status"}'
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "action": {"type": "string", "description": "Operation: status, set_budget, recommend, report", "enum": ["status", "set_budget", "recommend", "report"]},
                "total_budget": {"type": "integer", "description": "Total token budget (set_budget, >=1000)", "minimum": 1000},
                "phase_allocations": {"type": "object", "description": "Per-phase allocation (set_budget)"},
                "project_size": {"type": "string", "description": "Project size (recommend): small, medium, large", "enum": ["small", "medium", "large"]},
                "complexity": {"type": "string", "description": "Complexity (recommend): low, medium, high", "enum": ["low", "medium", "high"]},
                "team_size": {"type": "integer", "description": "Team size (recommend, 1-50)", "minimum": 1, "maximum": 50},
                "period": {"type": "string", "description": "Report period (report): daily, weekly, session", "default": "session", "enum": ["daily", "weekly", "session"]},
            },
            "required": ["action"],
            "additionalProperties": False,
            "$schema": MCP_JSON_SCHEMA_URI,
        },
        outputSchema={
            "type": "object",
            "properties": {
                "action": {"type": "string"},
                "total_budget": {"type": "integer"},
                "used": {"type": "integer"},
                "remaining": {"type": "integer"},
                "phase_allocations": {"type": "object"},
                "usage_by_phase": {"type": "object"},
            },
        },
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=False, openWorldHint=False),
    )


async def handle_tool(arguments: dict, context: dict):
    action = arguments.get("action", "")
    token_budget_state = context["token_budget_state"]
    valid_actions = {"status", "set_budget", "recommend", "report"}
    if action not in valid_actions:
        return [TextContent(type="text", text=json.dumps(make_error_response(
            code="INVALID_INPUT",
            message=f"Invalid action: {action}. Valid: {sorted(valid_actions)}",
            details={"action": action},
        ), ensure_ascii=False), isError=True)]

    if action == "status":
        result = dict(token_budget_state)
        result["action"] = "status"
        return [TextContent(type="text", text=json.dumps(make_response("success", result), ensure_ascii=False))]

    elif action == "set_budget":
        total_budget = arguments.get("total_budget")
        if total_budget is not None and total_budget < 1000:
            return [TextContent(type="text", text=json.dumps(make_error_response(
                code="INVALID_INPUT",
                message="total_budget must be >= 1000",
                details={"total_budget": total_budget},
            ), ensure_ascii=False), isError=True)]
        if total_budget is not None:
            token_budget_state["total_budget"] = total_budget
            token_budget_state["remaining"] = total_budget - token_budget_state["used"]
        phase_allocations = arguments.get("phase_allocations")
        if phase_allocations:
            token_budget_state["phase_allocations"].update(phase_allocations)
        now_iso = datetime.now(timezone.utc).isoformat()
        result = {
            "action": "set_budget",
            "total_budget": token_budget_state["total_budget"],
            "phase_allocations": token_budget_state["phase_allocations"],
            "updated_at": now_iso,
        }
        return [TextContent(type="text", text=json.dumps(make_response("success", result), ensure_ascii=False))]

    elif action == "recommend":
        project_size = arguments.get("project_size", "medium")
        complexity = arguments.get("complexity", "medium")
        team_size = arguments.get("team_size", 1)
        base = 150000
        size_mult = _SIZE_MULTIPLIERS.get(project_size, 1.0)
        comp_mult = _COMPLEXITY_MULTIPLIERS.get(complexity, 1.0)
        team_mult = 1.0 + (team_size - 1) * 0.1
        recommended = int(base * size_mult * comp_mult * team_mult)
        allocations = {}
        for phase, amount in _DEFAULT_BUDGET_ALLOCATIONS.items():
            allocations[phase] = int(amount * size_mult * comp_mult)
        result = {
            "action": "recommend",
            "recommended_total": recommended,
            "recommended_allocations": allocations,
            "project_size": project_size,
            "complexity": complexity,
            "team_size": team_size,
            "adjusted_total": recommended,
        }
        return [TextContent(type="text", text=json.dumps(make_response("success", result), ensure_ascii=False))]

    elif action == "report":
        period = arguments.get("period", "session")
        total = token_budget_state["total_budget"]
        used = token_budget_state["used"]
        remaining = token_budget_state["remaining"]
        usage_pct = (used / total * 100) if total > 0 else 0
        result = {
            "action": "report",
            "period": period,
            "total_budget": total,
            "total_used": used,
            "remaining": remaining,
            "usage_pct": round(usage_pct, 1),
        }
        return [TextContent(type="text", text=json.dumps(make_response("success", result), ensure_ascii=False))]
