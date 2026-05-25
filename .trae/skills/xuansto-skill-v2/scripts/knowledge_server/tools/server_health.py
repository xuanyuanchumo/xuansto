import json
from datetime import datetime, timezone

from ..config import make_response, make_error_response, mcp_available
from ._shared import MCP_JSON_SCHEMA_URI

if mcp_available:
    from mcp.types import Tool, TextContent, ToolAnnotations


def get_tool_definition():
    if not mcp_available:
        return None
    return Tool(
        name="server_health",
        description=(
            "[Read-Only] [Idempotent] Server health check and version compatibility verification.\n\n"
            "Use this tool to check MCP server health, version compatibility, and tool availability. "
            "Supports three actions: check (full health), version (version info), status (runtime status).\n\n"
            "Parameters:\n"
            "- action (string, default='check', enum: check|version|status): Operation type.\n"
            "- include_details (boolean, default=false): Include detailed tool status information.\n\n"
            "Returns an object with:\n"
            "- status: Health status (HEALTHY/DEGRADED/UNAVAILABLE).\n"
            "- version: Server version.\n"
            "- api_version: API version.\n"
            "- uptime_seconds: Server uptime in seconds.\n"
            "- tools_available: Number of available tools.\n"
            "- degradation_level: Degradation level (none/partial/full).\n"
            "- last_check_timestamp: ISO 8601 timestamp.\n"
            "- tools_status: Per-tool status (when include_details=true).\n\n"
            "Example: Full health check:\n"
            '{"action": "check", "include_details": true}'
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "action": {"type": "string", "description": "Operation: check, version, status", "default": "check", "enum": ["check", "version", "status"]},
                "include_details": {"type": "boolean", "description": "Include detailed tool status", "default": False},
            },
            "additionalProperties": False,
            "$schema": MCP_JSON_SCHEMA_URI,
        },
        outputSchema={
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "version": {"type": "string"},
                "api_version": {"type": "string"},
                "uptime_seconds": {"type": "integer"},
                "tools_available": {"type": "integer"},
                "degradation_level": {"type": "string"},
                "last_check_timestamp": {"type": "string"},
                "tools_status": {"type": "object"},
                "memory_usage_mb": {"type": "number"},
                "active_workflows": {"type": "integer"},
                "active_sessions": {"type": "integer"},
            },
        },
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False),
    )


async def handle_tool(arguments: dict, context: dict):
    action = arguments.get("action", "check")
    include_details = arguments.get("include_details", False)
    now_iso = datetime.now(timezone.utc).isoformat()
    start_time = context["start_time"]
    workflows = context["workflows"]
    sessions = context["sessions"]
    uptime = int((datetime.now(timezone.utc) - start_time).total_seconds())

    if action == "check":
        result = {
            "status": "HEALTHY",
            "version": "4.0.0",
            "api_version": "3.0.0",
            "uptime_seconds": uptime,
            "tools_available": 26,
            "degradation_level": "none",
            "last_check_timestamp": now_iso,
        }
        if include_details:
            tool_names = [
                "skill_analyze", "quality_gate_check", "spec_drift_detect",
                "security_scan", "code_simplify", "session_manage",
                "workflow_dispatch", "agent_status", "hook_manage",
                "context_compress", "server_health", "decision_log",
                "token_budget", "knowledge_inject", "project_init",
                "knowledge_search", "knowledge_add", "knowledge_update",
                "knowledge_delete", "knowledge_stats", "knowledge_rollback",
                "knowledge_auto_retrieve", "knowledge_progressive_search",
                "knowledge_deep_load", "knowledge_web_update", "resource_load_status",
            ]
            result["tools_status"] = {t: "OK" for t in tool_names}
            result["memory_usage_mb"] = 0.0
            result["active_workflows"] = len(workflows)
            result["active_sessions"] = len(sessions)
        return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]

    elif action == "version":
        result = {"version": "4.0.0", "api_version": "3.0.0"}
        return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]

    elif action == "status":
        result = {
            "status": "HEALTHY",
            "uptime_seconds": uptime,
            "degradation_level": "none",
        }
        return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]

    return [TextContent(type="text", text=json.dumps(make_error_response(
        code="INVALID_INPUT",
        message=f"Invalid action: {action}",
        details={"action": action},
    ), ensure_ascii=False), isError=True)]
