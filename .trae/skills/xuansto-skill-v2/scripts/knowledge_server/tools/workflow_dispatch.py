import json
import uuid
from datetime import datetime, timezone

from ..config import make_response, make_error_response, mcp_available
from ._shared import MCP_JSON_SCHEMA_URI, _PHASE_NAMES

if mcp_available:
    from mcp.types import Tool, TextContent, ToolAnnotations


def get_tool_definition():
    if not mcp_available:
        return None
    return Tool(
        name="workflow_dispatch",
        description=(
            "Workflow dispatch: start, status, abort, phase, recover, snapshots.\n\n"
            "Use this tool to manage development workflows. Start SDD/TDD workflows, "
            "query workflow status, advance phases, recover from failures, and manage snapshots.\n\n"
            "Parameters:\n"
            "- action (string, required, enum: start|status|abort|phase|recover|snapshots): Operation type.\n"
            "- workflow (string, optional): Workflow name (start action): sdd-tdd-full, sdd-tdd-medium, sdd-tdd-fast, etc.\n"
            "- project_path (string, default='.'): Project root directory (start action).\n"
            "- workflow_id (string, optional): Workflow instance ID (status/abort/phase/recover/snapshots).\n"
            "- phase_action (string, optional): Phase operation (phase action): advance, current.\n"
            "- snapshot_phase (integer, optional): Target phase snapshot for recovery (recover action).\n\n"
            "Returns an object with:\n"
            "- action: The action performed.\n"
            "- workflow_id: Workflow instance ID.\n"
            "- workflow_name: Workflow name.\n"
            "- current_phase: Current phase number.\n"
            "- phases: Array of phase objects (phase, name, status).\n"
            "- started_at/aborted_at: Timestamps.\n\n"
            "Example: Start a full workflow:\n"
            '{"action": "start", "workflow": "sdd-tdd-full", "project_path": "/path/to/project"}'
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "action": {"type": "string", "description": "Operation: start, status, abort, phase, recover, snapshots", "enum": ["start", "status", "abort", "phase", "recover", "snapshots"]},
                "workflow": {"type": "string", "description": "Workflow name (start): sdd-tdd-full, sdd-tdd-medium, sdd-tdd-fast"},
                "project_path": {"type": "string", "description": "Project root directory (start)", "default": "."},
                "workflow_id": {"type": "string", "description": "Workflow instance ID (status/abort/phase/recover/snapshots)"},
                "phase_action": {"type": "string", "description": "Phase operation (phase): advance, current", "enum": ["advance", "current"]},
                "snapshot_phase": {"type": "integer", "description": "Target phase snapshot for recovery (recover)"},
            },
            "required": ["action"],
            "additionalProperties": False,
            "$schema": MCP_JSON_SCHEMA_URI,
        },
        outputSchema={
            "type": "object",
            "properties": {
                "action": {"type": "string"},
                "workflow_id": {"type": "string"},
                "workflow_name": {"type": "string"},
                "current_phase": {"type": "integer"},
                "phases": {"type": "array", "items": {"type": "object", "properties": {"phase": {"type": "integer"}, "name": {"type": "string"}, "status": {"type": "string"}}}},
                "started_at": {"type": "string"},
                "aborted_at": {"type": "string"},
            },
        },
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=False, openWorldHint=False),
    )


async def handle_tool(arguments: dict, context: dict):
    action = arguments.get("action", "")
    workflows = context["workflows"]
    valid_actions = {"start", "status", "abort", "phase", "recover", "snapshots"}
    if action not in valid_actions:
        return [TextContent(type="text", text=json.dumps(make_error_response(
            code="INVALID_INPUT",
            message=f"Invalid action: {action}. Valid: {sorted(valid_actions)}",
            details={"action": action, "valid_actions": sorted(valid_actions)},
        ), ensure_ascii=False), isError=True)]

    now_iso = datetime.now(timezone.utc).isoformat()

    if action == "start":
        workflow_name = arguments.get("workflow", "sdd-tdd-full")
        project_path = arguments.get("project_path", ".")
        workflow_id = f"wf-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"
        phases = []
        for i, name in enumerate(_PHASE_NAMES):
            status = "IN_PROGRESS" if i == 0 else "PENDING"
            phases.append({"phase": i, "name": name, "status": status})
        workflows[workflow_id] = {
            "workflow_name": workflow_name,
            "project_path": project_path,
            "current_phase": 0,
            "phases": phases,
            "started_at": now_iso,
            "status": "RUNNING",
        }
        result = {
            "action": "start",
            "workflow_id": workflow_id,
            "workflow_name": workflow_name,
            "current_phase": 0,
            "phases": phases,
            "started_at": now_iso,
        }
        return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]

    elif action == "status":
        workflow_id = arguments.get("workflow_id", "")
        wf = workflows.get(workflow_id)
        if not wf:
            return [TextContent(type="text", text=json.dumps(make_error_response(
                code="NOT_FOUND",
                message=f"Workflow not found: {workflow_id}",
                details={"workflow_id": workflow_id},
            ), ensure_ascii=False), isError=True)]
        result = {
            "action": "status",
            "workflow_id": workflow_id,
            "workflow_name": wf["workflow_name"],
            "current_phase": wf["current_phase"],
            "phases": wf["phases"],
            "status": wf["status"],
            "started_at": wf["started_at"],
        }
        return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]

    elif action == "abort":
        workflow_id = arguments.get("workflow_id", "")
        wf = workflows.get(workflow_id)
        if not wf:
            return [TextContent(type="text", text=json.dumps(make_error_response(
                code="NOT_FOUND",
                message=f"Workflow not found: {workflow_id}",
                details={"workflow_id": workflow_id},
            ), ensure_ascii=False), isError=True)]
        wf["status"] = "ABORTED"
        result = {
            "action": "abort",
            "workflow_id": workflow_id,
            "aborted_at": now_iso,
        }
        return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]

    elif action == "phase":
        workflow_id = arguments.get("workflow_id", "")
        phase_action = arguments.get("phase_action", "current")
        wf = workflows.get(workflow_id)
        if not wf:
            return [TextContent(type="text", text=json.dumps(make_error_response(
                code="NOT_FOUND",
                message=f"Workflow not found: {workflow_id}",
                details={"workflow_id": workflow_id},
            ), ensure_ascii=False), isError=True)]
        if phase_action == "advance":
            current = wf["current_phase"]
            next_phase = min(current + 1, 8)
            wf["current_phase"] = next_phase
            for p in wf["phases"]:
                if p["phase"] == current:
                    p["status"] = "COMPLETED"
                elif p["phase"] == next_phase:
                    p["status"] = "IN_PROGRESS"
            result = {
                "action": "phase",
                "workflow_id": workflow_id,
                "previous_phase": current,
                "current_phase": next_phase,
            }
        else:
            result = {
                "action": "phase",
                "workflow_id": workflow_id,
                "current_phase": wf["current_phase"],
            }
        return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]

    elif action == "recover":
        workflow_id = arguments.get("workflow_id", "")
        snapshot_phase = arguments.get("snapshot_phase")
        wf = workflows.get(workflow_id)
        if not wf:
            return [TextContent(type="text", text=json.dumps(make_error_response(
                code="NOT_FOUND",
                message=f"Workflow not found: {workflow_id}",
                details={"workflow_id": workflow_id},
            ), ensure_ascii=False), isError=True)]
        target = snapshot_phase if snapshot_phase is not None else wf["current_phase"]
        wf["current_phase"] = target
        wf["status"] = "RUNNING"
        for p in wf["phases"]:
            if p["phase"] < target:
                p["status"] = "COMPLETED"
            elif p["phase"] == target:
                p["status"] = "IN_PROGRESS"
            else:
                p["status"] = "PENDING"
        result = {
            "action": "recover",
            "workflow_id": workflow_id,
            "recovered_to_phase": target,
            "recovered_at": now_iso,
        }
        return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]

    elif action == "snapshots":
        workflow_id = arguments.get("workflow_id", "")
        wf = workflows.get(workflow_id)
        if not wf:
            return [TextContent(type="text", text=json.dumps(make_error_response(
            code="NOT_FOUND",
            message=f"Workflow not found: {workflow_id}",
            details={"workflow_id": workflow_id},
        ), ensure_ascii=False), isError=True)]
        snapshots = []
        for p in wf["phases"]:
            if p["status"] in ("COMPLETED", "IN_PROGRESS"):
                snapshots.append({"phase": p["phase"], "name": p["name"], "status": p["status"]})
        result = {
            "action": "snapshots",
            "workflow_id": workflow_id,
            "snapshots": snapshots,
            "total": len(snapshots),
        }
        return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]
