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
        name="decision_log",
        description=(
            "Decision log management: log, query, export.\n\n"
            "Use this tool to record architectural decisions (ADRs), query past decisions, "
            "and export decision records. Supports full ADR fields including alternatives, "
            "rationale, and impact assessment.\n\n"
            "Parameters:\n"
            "- action (string, required, enum: log|query|export): Operation type.\n"
            "- title (string, optional): Decision title (log action).\n"
            "- description (string, optional): Decision description (log action).\n"
            "- context (string, optional): Decision context (log action).\n"
            "- alternatives (array of strings, optional): Alternative options (log action).\n"
            "- decision (string, optional): Final decision (log action).\n"
            "- rationale (string, optional): Decision rationale (log action).\n"
            "- impact (string, optional): Impact scope (log action).\n"
            "- decided_by (string, optional): Decision maker (log action).\n"
            "- keyword (string, optional): Search keyword (query action).\n"
            "- tag (string, optional): Tag filter (query action).\n"
            "- date_from (string, optional): Start date ISO8601 (query/export).\n"
            "- date_to (string, optional): End date ISO8601 (query/export).\n"
            "- limit (integer, default=20, range 1-100): Result limit (query action).\n"
            "- format (string, default='json', enum: json|markdown): Export format (export action).\n\n"
            "Returns an object with:\n"
            "- action: The action performed.\n"
            "- id: Decision ID (log action).\n"
            "- entry: Full decision entry (log action).\n"
            "- results: Array of matching decisions (query action).\n"
            "- total_decisions: Total count.\n\n"
            "Example: Log a decision:\n"
            '{"action": "log", "title": "Choose React", "alternatives": ["Vue", "Angular"], "decision": "React", "rationale": "Team experience"}'
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "action": {"type": "string", "description": "Operation: log, query, export", "enum": ["log", "query", "export"]},
                "title": {"type": "string", "description": "Decision title (log)"},
                "description": {"type": "string", "description": "Decision description (log)"},
                "context": {"type": "string", "description": "Decision context (log)"},
                "alternatives": {"type": "array", "items": {"type": "string"}, "description": "Alternative options (log)"},
                "decision": {"type": "string", "description": "Final decision (log)"},
                "rationale": {"type": "string", "description": "Decision rationale (log)"},
                "impact": {"type": "string", "description": "Impact scope (log)"},
                "decided_by": {"type": "string", "description": "Decision maker (log)"},
                "keyword": {"type": "string", "description": "Search keyword (query)"},
                "tag": {"type": "string", "description": "Tag filter (query)"},
                "date_from": {"type": "string", "description": "Start date ISO8601 (query/export)"},
                "date_to": {"type": "string", "description": "End date ISO8601 (query/export)"},
                "limit": {"type": "integer", "description": "Result limit (query)", "default": 20, "minimum": 1, "maximum": 100},
                "format": {"type": "string", "description": "Export format (export): json, markdown", "default": "json", "enum": ["json", "markdown"]},
            },
            "required": ["action"],
            "additionalProperties": False,
            "$schema": MCP_JSON_SCHEMA_URI,
        },
        outputSchema={
            "type": "object",
            "properties": {
                "action": {"type": "string"},
                "id": {"type": "string"},
                "entry": {"type": "object"},
                "results": {"type": "array", "items": {"type": "object"}},
                "total_decisions": {"type": "integer"},
                "format": {"type": "string"},
                "content": {"type": "string"},
            },
        },
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=False, openWorldHint=False),
    )


async def handle_tool(arguments: dict, context: dict):
    action = arguments.get("action", "")
    decisions = context["decisions"]
    valid_actions = {"log", "query", "export"}
    if action not in valid_actions:
        return [TextContent(type="text", text=json.dumps(make_error_response(
            code="INVALID_INPUT",
            message=f"Invalid action: {action}. Valid: {sorted(valid_actions)}",
            details={"action": action},
        ), ensure_ascii=False), isError=True)]

    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

    if action == "log":
        title = arguments.get("title", "")
        if not title:
            return [TextContent(type="text", text=json.dumps(make_error_response(
                code="INVALID_INPUT",
                message="title is required for log action",
                details={},
            ), ensure_ascii=False), isError=True)]
        decision_id = f"ADR-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{len(decisions)+1:03d}"
        entry = {
            "id": decision_id,
            "title": title,
            "description": arguments.get("description", ""),
            "context": arguments.get("context", ""),
            "alternatives": arguments.get("alternatives", []),
            "decision": arguments.get("decision", ""),
            "rationale": arguments.get("rationale", ""),
            "impact": arguments.get("impact", ""),
            "decided_by": arguments.get("decided_by", ""),
            "tags": [],
            "created_at": now_iso,
        }
        decisions.append(entry)
        result = {
            "action": "log",
            "id": decision_id,
            "entry": entry,
            "total_decisions": len(decisions),
        }
        return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]

    elif action == "query":
        keyword = arguments.get("keyword", "")
        tag = arguments.get("tag", "")
        limit = arguments.get("limit", 20)
        date_from = arguments.get("date_from")
        date_to = arguments.get("date_to")
        results = list(decisions)
        if keyword:
            kw_lower = keyword.lower()
            results = [d for d in results if kw_lower in d.get("title", "").lower() or kw_lower in d.get("description", "").lower() or kw_lower in d.get("decision", "").lower()]
        if tag:
            results = [d for d in results if tag in d.get("tags", [])]
        if date_from:
            results = [d for d in results if d.get("created_at", "") >= date_from]
        if date_to:
            results = [d for d in results if d.get("created_at", "") <= date_to]
        results = results[:limit]
        result = {
            "action": "query",
            "results": results,
            "total": len(results),
            "limit": limit,
        }
        return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]

    elif action == "export":
        fmt = arguments.get("format", "json")
        entries = list(decisions)
        if fmt == "markdown":
            lines = ["# Decision Log\n"]
            for d in entries:
                lines.append(f"## {d.get('id', '')}: {d.get('title', '')}\n")
                lines.append(f"- **Decision**: {d.get('decision', '')}")
                lines.append(f"- **Rationale**: {d.get('rationale', '')}")
                lines.append(f"- **Alternatives**: {', '.join(d.get('alternatives', []))}")
                lines.append(f"- **Impact**: {d.get('impact', '')}")
                lines.append(f"- **Date**: {d.get('created_at', '')}\n")
            content = "\n".join(lines)
        else:
            content = json.dumps(entries, ensure_ascii=False, indent=2)
        result = {
            "action": "export",
            "format": fmt,
            "content": content,
            "total": len(entries),
        }
        return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]
