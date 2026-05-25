import json
import uuid
from datetime import datetime, timezone

from ..config import make_response, make_error_response, mcp_available
from ..degradation import MCPToolFallback
from ._shared import MCP_JSON_SCHEMA_URI, _scan_agent_registry, _phase_to_layers

if mcp_available:
    from mcp.types import Tool, TextContent, ToolAnnotations


def get_tool_definition():
    if not mcp_available:
        return None
    return Tool(
        name="agent_status",
        description=(
            "[Read-Only] [Idempotent] Agent status query: list, by_phase, detail.\n\n"
            "Use this tool to query the agent registry. List all agents, filter by phase, "
            "or get detailed information about a specific agent.\n\n"
            "Parameters:\n"
            "- action (string, required, enum: list|by_phase|detail|create|match|assign|release|instance_status|destroy|schedule): Operation type.\n"
            "- phase (integer, optional): Phase number for by_phase query (0-8).\n"
            "- agent_name (string, optional): Agent name for detail query.\n"
            "- agent_type (string, optional): Agent type for create.\n"
            "- capabilities (array of strings, optional): Capability list for create/match.\n"
            "- agent_id (string, optional): Agent instance ID for assign/release/instance_status/destroy.\n"
            "- task (string, optional): Task description for assign.\n\n"
            "Returns an object with:\n"
            "- action: The action performed.\n"
            "- agents: Array of agent objects (name, layer, status, capabilities, etc.).\n"
            "- total_agents: Total number of agents.\n"
            "- available_count: Number of available agents.\n\n"
            "Example: List all agents:\n"
            '{"action": "list"}'
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "action": {"type": "string", "description": "Operation: list, by_phase, detail, create, match, assign, release, instance_status, destroy, schedule", "enum": ["list", "by_phase", "detail", "create", "match", "assign", "release", "instance_status", "destroy", "schedule"]},
                "phase": {"type": "integer", "description": "Phase number for by_phase (0-8)"},
                "agent_name": {"type": "string", "description": "Agent name for detail"},
                "agent_type": {"type": "string", "description": "Agent type for create"},
                "capabilities": {"type": "array", "items": {"type": "string"}, "description": "Capability list for create/match"},
                "agent_id": {"type": "string", "description": "Agent instance ID for assign/release/instance_status/destroy"},
                "task": {"type": "string", "description": "Task description for assign"},
            },
            "required": ["action"],
            "additionalProperties": False,
            "$schema": MCP_JSON_SCHEMA_URI,
        },
        outputSchema={
            "type": "object",
            "properties": {
                "action": {"type": "string"},
                "agents": {"type": "array", "items": {"type": "object", "properties": {"name": {"type": "string"}, "layer": {"type": "string"}, "status": {"type": "string"}, "capabilities": {"type": "array", "items": {"type": "string"}}, "assigned_tasks": {"type": "integer"}, "completed_tasks": {"type": "integer"}, "definition_file": {"type": "string"}}}},
                "total_agents": {"type": "integer"},
                "available_count": {"type": "integer"},
            },
        },
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=False, openWorldHint=False),
    )


async def handle_tool(arguments: dict, context: dict):
    action = arguments.get("action", "list")
    agent_instances = context["agent_instances"]
    fallback = context.get("fallback")
    skill_root = fallback._skill_root if fallback else MCPToolFallback.SKILL_ROOT

    if action == "list":
        agents = _scan_agent_registry(skill_root)
        result = {
            "action": "list",
            "agents": agents,
            "total_agents": len(agents),
            "available_count": sum(1 for a in agents if a.get("status", "AVAILABLE") == "AVAILABLE"),
        }
        return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]

    elif action == "by_phase":
        phase = arguments.get("phase", 0)
        all_agents = _scan_agent_registry(skill_root)
        phase_layers = _phase_to_layers(phase)
        filtered = [a for a in all_agents if a.get("layer", "") in phase_layers]
        result = {
            "action": "by_phase",
            "phase": phase,
            "agents": filtered,
            "total_agents": len(filtered),
            "available_count": sum(1 for a in filtered if a.get("status", "AVAILABLE") == "AVAILABLE"),
        }
        return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]

    elif action == "detail":
        agent_name = arguments.get("agent_name", "")
        all_agents = _scan_agent_registry(skill_root)
        matched = [a for a in all_agents if a.get("name", "").lower() == agent_name.lower()]
        if not matched:
            return [TextContent(type="text", text=json.dumps(make_error_response(
                code="NOT_FOUND",
                message=f"Agent not found: {agent_name}",
                details={"agent_name": agent_name},
            ), ensure_ascii=False), isError=True)]
        result = {
            "action": "detail",
            "agent": matched[0],
        }
        return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]

    elif action == "create":
        agent_type = arguments.get("agent_type", "developer")
        capabilities = arguments.get("capabilities", [])
        agent_id = f"agent-{uuid.uuid4().hex[:8]}"
        now_iso = datetime.now(timezone.utc).isoformat()
        instance = {
            "agent_id": agent_id,
            "agent_type": agent_type,
            "capabilities": capabilities,
            "status": "idle",
            "created_at": now_iso,
            "last_active_at": now_iso,
            "task_count": 0,
            "total_duration_ms": 0,
        }
        agent_instances[agent_id] = instance
        result = {"action": "create", **instance}
        return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]

    elif action in ("assign", "release", "instance_status", "destroy"):
        agent_id = arguments.get("agent_id", "")
        instance = agent_instances.get(agent_id)
        if not instance:
            return [TextContent(type="text", text=json.dumps(make_error_response(
                code="NOT_FOUND",
                message=f"Agent instance not found: {agent_id}",
                details={"agent_id": agent_id},
            ), ensure_ascii=False), isError=True)]
        now_iso = datetime.now(timezone.utc).isoformat()
        if action == "assign":
            task = arguments.get("task", "")
            instance["status"] = "busy"
            instance["task_count"] += 1
            instance["last_active_at"] = now_iso
            instance["current_task"] = task
            result = {"action": "assign", "agent_id": agent_id, "task": task, "status": "busy", "task_count": instance["task_count"]}
        elif action == "release":
            instance["status"] = "idle"
            instance["last_active_at"] = now_iso
            completed_task = instance.pop("current_task", "")
            result = {"action": "release", "agent_id": agent_id, "status": "idle", "completed_task": completed_task}
        elif action == "instance_status":
            result = {"action": "instance_status", **instance}
        elif action == "destroy":
            instance["status"] = "destroyed"
            del agent_instances[agent_id]
            result = {"action": "destroy", "agent_id": agent_id, "status": "destroyed"}
        return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]

    elif action == "match":
        capabilities = arguments.get("capabilities", [])
        all_agents = _scan_agent_registry(skill_root)
        matched = [a for a in all_agents if any(c in a.get("capabilities", []) for c in capabilities)]
        result = {
            "action": "match",
            "matched_agents": matched,
            "total_matched": len(matched),
            "requested_capabilities": capabilities,
        }
        return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]

    elif action == "schedule":
        result = {"action": "schedule", "status": "not_implemented", "message": "Scheduling requires external orchestrator"}
        return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]

    return [TextContent(type="text", text=json.dumps(make_error_response(
        code="INVALID_INPUT",
        message=f"Invalid action: {action}",
        details={"action": action},
    ), ensure_ascii=False), isError=True)]
