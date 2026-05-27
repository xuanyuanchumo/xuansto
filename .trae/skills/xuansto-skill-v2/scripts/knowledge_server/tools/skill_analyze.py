import json
from pathlib import Path

from ..config import make_response, make_error_response, mcp_available
from ._shared import (
    MCP_JSON_SCHEMA_URI,
    _extract_skill_metadata,
    _analyze_structure,
    _analyze_agents,
    _analyze_dependencies,
    _detect_issues,
)

if mcp_available:
    from mcp.types import Tool, TextContent, ToolAnnotations


def get_tool_definition():
    if not mcp_available:
        return None
    return Tool(
        name="skill_analyze",
        description=(
            "[Read-Only] [Idempotent] Analyze skill project structure, extract YAML metadata, "
            "directory structure, agent registry, script dependencies, and validation issues.\n\n"
            "Use this tool to inspect a skill project's overall health and structure. "
            "Returns metadata from SKILL.md frontmatter, directory tree, agent layer breakdown, "
            "script dependency graph, and any detected issues (missing scripts, parse errors, etc.).\n\n"
            "Parameters:\n"
            "- skill_path (string, required): Absolute path to the skill root directory.\n"
            "- include_scripts (boolean, default=true): Whether to analyze the scripts directory.\n"
            "- include_agents (boolean, default=true): Whether to analyze the agents directory.\n"
            "- depth (string, default='basic', enum: basic|full): Analysis depth. 'full' includes "
            "line counts, dependency graphs, and deeper validation.\n\n"
            "Returns an object with:\n"
            "- metadata: Extracted YAML frontmatter (name, version, agents_summary, tags).\n"
            "- structure: Directory info (root, directories, file_count, total_lines).\n"
            "- agents: Agent registry info (total, layers, by_layer).\n"
            "- dependencies: Script and MCP dependencies.\n"
            "- issues: List of detected issues (severity, code, message, path).\n\n"
            "Example: Full analysis of a skill project:\n"
            '{"skill_path": "/path/to/skill", "depth": "full", "include_agents": true}'
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "skill_path": {"type": "string", "description": "Absolute path to the skill root directory"},
                "include_scripts": {"type": "boolean", "description": "Whether to analyze scripts directory", "default": True},
                "include_agents": {"type": "boolean", "description": "Whether to analyze agents directory", "default": True},
                "depth": {"type": "string", "description": "Analysis depth: basic or full", "default": "basic", "enum": ["basic", "full"]},
            },
            "required": ["skill_path"],
            "additionalProperties": False,
            "$schema": MCP_JSON_SCHEMA_URI,
        },
        outputSchema={
            "type": "object",
            "properties": {
                "metadata": {"type": "object", "properties": {"name": {"type": "string"}, "version": {"type": "string"}, "agents_summary": {"type": "string"}, "tags": {"type": "array", "items": {"type": "string"}}}},
                "structure": {"type": "object", "properties": {"root": {"type": "string"}, "directories": {"type": "array", "items": {"type": "string"}}, "file_count": {"type": "integer"}, "total_lines": {"type": "integer"}}},
                "agents": {"type": "object", "properties": {"total": {"type": "integer"}, "layers": {"type": "integer"}, "by_layer": {"type": "object"}}},
                "dependencies": {"type": "object", "properties": {"mcp_server": {"type": "string"}, "scripts": {"type": "array", "items": {"type": "string"}}, "python_version": {"type": "string"}}},
                "issues": {"type": "array", "items": {"type": "object", "properties": {"severity": {"type": "string"}, "code": {"type": "string"}, "message": {"type": "string"}, "path": {"type": "string"}}}},
            },
        },
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False),
    )


async def handle_tool(arguments: dict, context: dict):
    skill_path = arguments.get("skill_path", "")
    include_scripts = arguments.get("include_scripts", True)
    include_agents = arguments.get("include_agents", True)
    depth = arguments.get("depth", "basic")

    if not skill_path:
        return [TextContent(type="text", text=json.dumps(make_error_response(
            code="INVALID_INPUT",
            message="skill_path is required",
            details={},
        ), ensure_ascii=False), isError=True)]

    root = Path(skill_path)
    if not root.exists():
        return [TextContent(type="text", text=json.dumps(make_error_response(
            code="NOT_FOUND",
            message=f"Skill directory not found: {skill_path}",
            details={"skill_path": skill_path},
        ), ensure_ascii=False), isError=True)]

    metadata = _extract_skill_metadata(root)
    structure = _analyze_structure(root, depth)
    agents = _analyze_agents(root) if include_agents else {"total": 0, "layers": 0, "by_layer": {}}
    dependencies = _analyze_dependencies(root) if include_scripts else {"scripts": [], "python_version": ">=3.10"}
    issues = _detect_issues(root, metadata, dependencies)

    result = {
        "metadata": metadata,
        "structure": structure,
        "agents": agents,
        "dependencies": dependencies,
        "issues": issues,
    }
    return [TextContent(type="text", text=json.dumps(make_response("success", result), ensure_ascii=False))]
