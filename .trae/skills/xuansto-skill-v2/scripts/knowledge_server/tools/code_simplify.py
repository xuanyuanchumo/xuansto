import json
import os
from pathlib import Path

from ..config import make_response, make_error_response, mcp_available
from ._shared import MCP_JSON_SCHEMA_URI, _analyze_python_file, _detect_code_duplication

if mcp_available:
    from mcp.types import Tool, TextContent, ToolAnnotations


def get_tool_definition():
    if not mcp_available:
        return None
    return Tool(
        name="code_simplify",
        description=(
            "[Read-Only] [Idempotent] Code simplification analysis.\n\n"
            "Use this tool to detect code simplification opportunities including dead code, "
            "duplication, excessive complexity, and naming issues. Returns actionable suggestions "
            "with safety ratings and estimated line reductions.\n\n"
            "Parameters:\n"
            "- target (string, required): Target file or directory path.\n"
            "- scope (string, default='recent', enum: file|dir|recent): Scan scope.\n"
            "- include_dedup (boolean, default=true): Include duplicate code detection.\n\n"
            "Returns an object with:\n"
            "- total_suggestions: Total simplification suggestions.\n"
            "- by_type: Counts by suggestion type (dead_code, duplication, complexity, naming).\n"
            "- suggestions: Array of suggestions (id, type, file, line_start, line_end, description, safety, action, estimated_reduction).\n"
            "- total_lines_reducible: Total lines that could be reduced.\n"
            "- safe_count: Number of safe suggestions.\n"
            "- caution_count: Number of caution-level suggestions.\n\n"
            "Example: Analyze a directory:\n"
            '{"target": "src/utils", "scope": "dir", "include_dedup": true}'
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "target": {"type": "string", "description": "Target file or directory path"},
                "scope": {"type": "string", "description": "Scan scope: file, dir, recent", "default": "recent", "enum": ["file", "dir", "recent"]},
                "include_dedup": {"type": "boolean", "description": "Include duplicate code detection", "default": True},
            },
            "required": ["target"],
            "additionalProperties": False,
            "$schema": MCP_JSON_SCHEMA_URI,
        },
        outputSchema={
            "type": "object",
            "properties": {
                "total_suggestions": {"type": "integer"},
                "by_type": {"type": "object", "properties": {"dead_code": {"type": "integer"}, "duplication": {"type": "integer"}, "complexity": {"type": "integer"}, "naming": {"type": "integer"}}},
                "suggestions": {"type": "array", "items": {"type": "object", "properties": {"id": {"type": "string"}, "type": {"type": "string"}, "file": {"type": "string"}, "line_start": {"type": "integer"}, "line_end": {"type": "integer"}, "description": {"type": "string"}, "safety": {"type": "string"}, "action": {"type": "string"}, "estimated_reduction": {"type": "integer"}}}},
                "total_lines_reducible": {"type": "integer"},
                "safe_count": {"type": "integer"},
                "caution_count": {"type": "integer"},
            },
        },
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False),
    )


async def handle_tool(arguments: dict, context: dict):
    target = arguments.get("target", "")
    scope = arguments.get("scope", "recent")
    include_dedup = arguments.get("include_dedup", True)

    if not target:
        return [TextContent(type="text", text=json.dumps(make_error_response(
            code="INVALID_INPUT",
            message="target is required",
            details={},
        ), ensure_ascii=False), isError=True)]

    target_path = Path(target)
    if not target_path.exists():
        return [TextContent(type="text", text=json.dumps(make_error_response(
            code="NOT_FOUND",
            message=f"Target not found: {target}",
            details={"target": target},
        ), ensure_ascii=False), isError=True)]

    suggestions = []
    by_type = {"dead_code": 0, "duplication": 0, "complexity": 0, "naming": 0}

    if target_path.is_file() and target_path.suffix == ".py":
        _analyze_python_file(target_path, suggestions, by_type, target_path)
    elif target_path.is_dir():
        for root_dir, _dirs, files in os.walk(str(target_path)):
            if any(skip in root_dir for skip in ("node_modules", ".git", "__pycache__", ".venv", ".knowledge")):
                continue
            for fname in files:
                if not fname.endswith(".py"):
                    continue
                fpath = Path(root_dir) / fname
                _analyze_python_file(fpath, suggestions, by_type, target_path)

    if include_dedup:
        dup_suggestions = _detect_code_duplication(target_path)
        for ds in dup_suggestions:
            suggestions.append(ds)
            by_type["duplication"] += 1

    total_reducible = sum(s.get("estimated_reduction", 0) for s in suggestions)
    safe_count = sum(1 for s in suggestions if s.get("safety") == "SAFE")
    caution_count = len(suggestions) - safe_count

    result = {
        "total_suggestions": len(suggestions),
        "by_type": by_type,
        "suggestions": suggestions[:50],
        "total_lines_reducible": total_reducible,
        "safe_count": safe_count,
        "caution_count": caution_count,
    }
    return [TextContent(type="text", text=json.dumps(make_response("success", result), ensure_ascii=False))]
