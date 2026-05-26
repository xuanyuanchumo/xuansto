import json
from datetime import datetime, timezone

from ..config import make_response, make_error_response, mcp_available
from ._shared import MCP_JSON_SCHEMA_URI, _estimate_tokens

if mcp_available:
    from mcp.types import Tool, TextContent, ToolAnnotations


def get_tool_definition():
    if not mcp_available:
        return None
    return Tool(
        name="knowledge_inject",
        description=(
            "Knowledge injection into context: inject, preview, clear.\n\n"
            "Use this tool to inject retrieved knowledge content into the current session context "
            "for agents to reference during task execution. Supports previewing injection impact "
            "and clearing injected content.\n\n"
            "Parameters:\n"
            "- action (string, required, enum: inject|preview|clear): Operation type.\n"
            "- content (string, optional): Content to inject (inject action).\n"
            "- scope (string, default='session', enum: session|workflow|global): Injection scope.\n"
            "- source (string, optional): Knowledge source identifier.\n"
            "- priority (string, default='normal', enum: low|normal|high): Injection priority.\n\n"
            "Returns an object with:\n"
            "- action: The action performed.\n"
            "- scope: Injection scope.\n"
            "- injected_tokens: Estimated tokens injected.\n"
            "- source: Source identifier.\n"
            "- priority: Priority level.\n"
            "- context_window_usage_pct: Context window usage percentage.\n\n"
            "Example: Inject knowledge:\n"
            '{"action": "inject", "content": "React best practices...", "scope": "session", "priority": "high"}'
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "action": {"type": "string", "description": "Operation: inject, preview, clear", "enum": ["inject", "preview", "clear"]},
                "content": {"type": "string", "description": "Content to inject (inject)"},
                "scope": {"type": "string", "description": "Injection scope: session, workflow, global", "default": "session", "enum": ["session", "workflow", "global"]},
                "source": {"type": "string", "description": "Knowledge source identifier"},
                "priority": {"type": "string", "description": "Priority: low, normal, high", "default": "normal", "enum": ["low", "normal", "high"]},
            },
            "required": ["action"],
            "additionalProperties": False,
            "$schema": MCP_JSON_SCHEMA_URI,
        },
        outputSchema={
            "type": "object",
            "properties": {
                "action": {"type": "string"},
                "scope": {"type": "string"},
                "injected_tokens": {"type": "integer"},
                "source": {"type": "string"},
                "priority": {"type": "string"},
                "context_window_usage_pct": {"type": "number"},
            },
        },
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=False, openWorldHint=False),
    )


async def handle_tool(arguments: dict, context: dict):
    action = arguments.get("action", "")
    injected_contexts = context["injected_contexts"]
    valid_actions = {"inject", "preview", "clear"}
    if action not in valid_actions:
        return [TextContent(type="text", text=json.dumps(make_error_response(
            code="INVALID_INPUT",
            message=f"Invalid action: {action}. Valid: {sorted(valid_actions)}",
            details={"action": action},
        ), ensure_ascii=False), isError=True)]

    if action == "inject":
        content = arguments.get("content", "")
        if not content:
            return [TextContent(type="text", text=json.dumps(make_error_response(
                code="INVALID_INPUT",
                message="content is required for inject action",
                details={},
            ), ensure_ascii=False), isError=True)]
        scope = arguments.get("scope", "session")
        source = arguments.get("source", "")
        priority = arguments.get("priority", "normal")
        injected_tokens = _estimate_tokens(content)
        injected_contexts.append({
            "content": content,
            "scope": scope,
            "source": source,
            "priority": priority,
            "injected_at": datetime.now(timezone.utc).isoformat(),
            "tokens": injected_tokens,
        })
        total_injected = sum(c["tokens"] for c in injected_contexts)
        context_usage = min(100.0, (total_injected / 200000) * 100)
        result = {
            "action": "inject",
            "scope": scope,
            "injected_tokens": injected_tokens,
            "source": source,
            "priority": priority,
            "context_window_usage_pct": round(context_usage, 1),
        }
        return [TextContent(type="text", text=json.dumps(make_response("success", result), ensure_ascii=False))]

    elif action == "preview":
        content = arguments.get("content", "")
        scope = arguments.get("scope", "session")
        priority = arguments.get("priority", "normal")
        preview_tokens = _estimate_tokens(content) if content else 0
        total_injected = sum(c["tokens"] for c in injected_contexts) + preview_tokens
        context_usage = min(100.0, (total_injected / 200000) * 100)
        result = {
            "action": "preview",
            "scope": scope,
            "estimated_tokens": preview_tokens,
            "priority": priority,
            "context_window_usage_pct": round(context_usage, 1),
            "would_exceed": context_usage > 90,
        }
        return [TextContent(type="text", text=json.dumps(make_response("success", result), ensure_ascii=False))]

    elif action == "clear":
        cleared_count = len(injected_contexts)
        injected_contexts.clear()
        result = {
            "action": "clear",
            "cleared_items": cleared_count,
            "context_window_usage_pct": 0.0,
        }
        return [TextContent(type="text", text=json.dumps(make_response("success", result), ensure_ascii=False))]
