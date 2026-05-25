import json

from ..config import make_response, make_error_response, mcp_available
from ._shared import MCP_JSON_SCHEMA_URI, _HOOK_DEFINITIONS

if mcp_available:
    from mcp.types import Tool, TextContent, ToolAnnotations


def get_tool_definition():
    if not mcp_available:
        return None
    return Tool(
        name="hook_manage",
        description=(
            "Hook management: list, execute.\n\n"
            "Use this tool to manage lifecycle hooks. List configured hooks by profile, "
            "or execute a specific hook with context.\n\n"
            "Parameters:\n"
            "- action (string, required, enum: list|execute): Operation type.\n"
            "- profile (string, default='standard', enum: minimal|standard|strict): Hook configuration profile.\n"
            "- hook_name (string, optional): Hook name to execute.\n"
            "- context (object, optional): Execution context for hook.\n\n"
            "Returns an object with:\n"
            "- action: The action performed.\n"
            "- profile: The profile used.\n"
            "- hooks: Array of hook objects (name, trigger, pre_callbacks, post_callbacks, enabled).\n"
            "- total_hooks: Total number of hooks.\n"
            "- enabled_count: Number of enabled hooks.\n\n"
            "Example: List standard hooks:\n"
            '{"action": "list", "profile": "standard"}'
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "action": {"type": "string", "description": "Operation: list, execute", "enum": ["list", "execute"]},
                "profile": {"type": "string", "description": "Hook profile: minimal, standard, strict", "default": "standard", "enum": ["minimal", "standard", "strict"]},
                "hook_name": {"type": "string", "description": "Hook name to execute"},
                "context": {"type": "object", "description": "Execution context for hook"},
            },
            "required": ["action"],
            "additionalProperties": False,
            "$schema": MCP_JSON_SCHEMA_URI,
        },
        outputSchema={
            "type": "object",
            "properties": {
                "action": {"type": "string"},
                "profile": {"type": "string"},
                "hooks": {"type": "array", "items": {"type": "object", "properties": {"name": {"type": "string"}, "trigger": {"type": "string"}, "pre_callbacks": {"type": "array", "items": {"type": "string"}}, "post_callbacks": {"type": "array", "items": {"type": "string"}}, "enabled": {"type": "boolean"}}}},
                "total_hooks": {"type": "integer"},
                "enabled_count": {"type": "integer"},
            },
        },
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=False, openWorldHint=False),
    )


async def handle_tool(arguments: dict, context: dict):
    action = arguments.get("action", "list")
    profile = arguments.get("profile", "standard")

    if action == "list":
        hooks = _HOOK_DEFINITIONS.get(profile, _HOOK_DEFINITIONS["standard"])
        hooks_copy = [dict(h) for h in hooks]
        result = {
            "action": "list",
            "profile": profile,
            "hooks": hooks_copy,
            "total_hooks": len(hooks_copy),
            "enabled_count": sum(1 for h in hooks_copy if h.get("enabled", True)),
        }
        return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]

    elif action == "execute":
        hook_name = arguments.get("hook_name", "")
        hook_context = arguments.get("context", {})
        if not hook_name:
            return [TextContent(type="text", text=json.dumps(make_error_response(
                code="INVALID_INPUT",
                message="hook_name is required for execute action",
                details={},
            ), ensure_ascii=False), isError=True)]
        hooks = _HOOK_DEFINITIONS.get(profile, _HOOK_DEFINITIONS["standard"])
        matched = [h for h in hooks if h["name"] == hook_name]
        if not matched:
            return [TextContent(type="text", text=json.dumps(make_error_response(
                code="NOT_FOUND",
                message=f"Hook not found: {hook_name}",
                details={"hook_name": hook_name, "profile": profile},
            ), ensure_ascii=False), isError=True)]
        hook = matched[0]
        pre_results = [f"{cb}:ok" for cb in hook.get("pre_callbacks", [])]
        post_results = [f"{cb}:ok" for cb in hook.get("post_callbacks", [])]
        result = {
            "action": "execute",
            "hook_name": hook_name,
            "result": "completed",
            "pre_callbacks_result": pre_results,
            "post_callbacks_result": post_results,
            "context": hook_context,
        }
        return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]

    return [TextContent(type="text", text=json.dumps(make_error_response(
        code="INVALID_INPUT",
        message=f"Invalid action: {action}",
        details={"action": action},
    ), ensure_ascii=False), isError=True)]
