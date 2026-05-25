import json
import uuid
from datetime import datetime, timezone

from ..config import make_response, make_error_response, mcp_available
from ._shared import MCP_JSON_SCHEMA_URI

if mcp_available:
    from mcp.types import Tool, TextContent, ToolAnnotations


def get_tool_definition():
    if not mcp_available:
        return None
    return Tool(
        name="session_manage",
        description=(
            "Session state management: save, load, list, detect, verify, track, restore.\n\n"
            "Use this tool to manage development session state across interruptions. "
            "Save session progress before context switches, load previous sessions to resume work, "
            "and track task completion and decisions.\n\n"
            "Parameters:\n"
            "- action (string, required, enum: save|load|list|detect|verify|track|restore): Operation type.\n"
            "- completed_tasks (array of strings, optional): Completed task list (save action).\n"
            "- pending_tasks (array of strings, optional): Pending task list (save/track action).\n"
            "- decisions (array of objects, optional): Key decisions list (save/track action).\n"
            "- experience (array of objects, optional): Experience precipitation list (save action).\n"
            "- error_log (array of strings, optional): Error log (detect action).\n"
            "- pattern_path (string, optional): Pattern file path (verify action).\n"
            "- success (boolean, default=true): Verification success (verify action).\n"
            "- current_phase (integer, optional): Current phase number (track action).\n"
            "- current_task (string, optional): Current task description (track action).\n\n"
            "Returns an object with:\n"
            "- action: The action performed.\n"
            "- session_id: Session identifier.\n"
            "- saved_at/state: Action-specific result data.\n\n"
            "Example: Save session:\n"
            '{"action": "save", "completed_tasks": ["task-1"], "pending_tasks": ["task-2"], "decisions": [{"id": "ADR-001", "title": "Choose framework"}]}'
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "action": {"type": "string", "description": "Operation: save, load, list, detect, verify, track, restore", "enum": ["save", "load", "list", "detect", "verify", "track", "restore"]},
                "completed_tasks": {"type": "array", "items": {"type": "string"}, "description": "Completed task list (save)"},
                "pending_tasks": {"type": "array", "items": {"type": "string"}, "description": "Pending task list (save/track)"},
                "decisions": {"type": "array", "items": {"type": "object"}, "description": "Key decisions list (save/track)"},
                "experience": {"type": "array", "items": {"type": "object"}, "description": "Experience precipitation list (save)"},
                "error_log": {"type": "array", "items": {"type": "string"}, "description": "Error log (detect)"},
                "pattern_path": {"type": "string", "description": "Pattern file path (verify)"},
                "success": {"type": "boolean", "description": "Verification success (verify)", "default": True},
                "current_phase": {"type": "integer", "description": "Current phase number (track)"},
                "current_task": {"type": "string", "description": "Current task description (track)"},
            },
            "required": ["action"],
            "additionalProperties": False,
            "$schema": MCP_JSON_SCHEMA_URI,
        },
        outputSchema={
            "type": "object",
            "properties": {
                "action": {"type": "string"},
                "session_id": {"type": "string"},
                "saved_at": {"type": "string"},
                "state": {"type": "object"},
            },
        },
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=False, openWorldHint=False),
    )


async def handle_tool(arguments: dict, context: dict):
    action = arguments.get("action", "")
    sessions = context["sessions"]
    valid_actions = {"save", "load", "list", "detect", "verify", "track", "restore"}
    if action not in valid_actions:
        return [TextContent(type="text", text=json.dumps(make_error_response(
            code="INVALID_INPUT",
            message=f"Invalid action: {action}. Valid: {sorted(valid_actions)}",
            details={"action": action, "valid_actions": sorted(valid_actions)},
        ), ensure_ascii=False), isError=True)]

    now_iso = datetime.now(timezone.utc).isoformat()

    if action == "save":
        session_id = f"sess-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"
        state = {
            "current_phase": arguments.get("current_phase"),
            "completed_tasks": arguments.get("completed_tasks", []),
            "pending_tasks": arguments.get("pending_tasks", []),
            "decisions": arguments.get("decisions", []),
            "experience": arguments.get("experience", []),
        }
        sessions[session_id] = {"state": state, "saved_at": now_iso}
        result = {
            "action": "save",
            "session_id": session_id,
            "saved_at": now_iso,
            "state": state,
        }
        return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]

    elif action == "load":
        if not sessions:
            return [TextContent(type="text", text=json.dumps(make_error_response(
                code="NOT_FOUND",
                message="No saved sessions found",
                details={},
            ), ensure_ascii=False), isError=True)]
        latest_id = max(sessions.keys())
        session = sessions[latest_id]
        result = {
            "action": "load",
            "session_id": latest_id,
            "state": session["state"],
            "saved_at": session["saved_at"],
        }
        return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]

    elif action == "list":
        session_list = [{"session_id": sid, "saved_at": s["saved_at"]} for sid, s in sessions.items()]
        result = {"action": "list", "sessions": session_list, "total": len(session_list)}
        return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]

    elif action == "detect":
        error_log = arguments.get("error_log", [])
        result = {
            "action": "detect",
            "errors_detected": len(error_log),
            "error_log": error_log[:10],
            "recovery_suggested": len(error_log) > 0,
        }
        return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]

    elif action == "verify":
        pattern_path = arguments.get("pattern_path", "")
        success = arguments.get("success", True)
        result = {
            "action": "verify",
            "pattern_path": pattern_path,
            "success": success,
            "verified_at": now_iso,
        }
        return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]

    elif action == "track":
        current_phase = arguments.get("current_phase")
        current_task = arguments.get("current_task", "")
        result = {
            "action": "track",
            "current_phase": current_phase,
            "current_task": current_task,
            "pending_tasks": arguments.get("pending_tasks", []),
            "decisions": arguments.get("decisions", []),
            "tracked_at": now_iso,
        }
        return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]

    elif action == "restore":
        if not sessions:
            return [TextContent(type="text", text=json.dumps(make_error_response(
                code="NOT_FOUND",
                message="No saved sessions to restore",
                details={},
            ), ensure_ascii=False), isError=True)]
        latest_id = max(sessions.keys())
        session = sessions[latest_id]
        result = {
            "action": "restore",
            "session_id": latest_id,
            "state": session["state"],
            "restored_at": now_iso,
        }
        return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]
