import json
from pathlib import Path

from ..config import make_response, make_error_response, mcp_available
from ._shared import MCP_JSON_SCHEMA_URI, _QUALITY_GATES, _check_single_gate

if mcp_available:
    from mcp.types import Tool, TextContent, ToolAnnotations


def get_tool_definition():
    if not mcp_available:
        return None
    return Tool(
        name="quality_gate_check",
        description=(
            "[Read-Only] [Idempotent] Check 54 quality gates by gate_ids or phase.\n\n"
            "Use this tool to validate project quality at any development phase. "
            "Supports checking specific gates by ID, all gates for a phase, or all gates. "
            "Returns pass/fail status with severity levels (BLOCK/WARN) and detailed results.\n\n"
            "Parameters:\n"
            "- gate_ids (array of strings, optional): Specific gate IDs to check. Empty checks all.\n"
            "- phase (string, optional): Phase number (0-8) to filter gates.\n"
            "- project_path (string, default='.'): Project root directory path.\n"
            "- severity_filter (string, default='all', enum: all|BLOCK|WARN): Filter by severity.\n"
            "- force_refresh (boolean, default=false): Force refresh, ignoring file hash cache.\n\n"
            "Returns an object with:\n"
            "- gates_checked: Number of gates evaluated.\n"
            "- gates_passed: Number of passing gates.\n"
            "- gates_failed: Number of failing gates.\n"
            "- results: Array of gate results (gate_id, status, severity, message, details).\n"
            "- phase: The phase filter used.\n"
            "- can_proceed: Whether all BLOCK gates passed.\n\n"
            "Example: Check specific gates:\n"
            '{"gate_ids": ["TEST-PASS", "FILE-ENCODING"], "project_path": "/path/to/project"}'
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "gate_ids": {"type": "array", "items": {"type": "string"}, "description": "Gate IDs to check; empty checks all"},
                "phase": {"type": "string", "description": "Phase number (0-8) to filter gates"},
                "project_path": {"type": "string", "description": "Project root directory path", "default": "."},
                "severity_filter": {"type": "string", "description": "Severity filter: all, BLOCK, WARN", "default": "all", "enum": ["all", "BLOCK", "WARN"]},
                "force_refresh": {"type": "boolean", "description": "Force refresh ignoring cache", "default": False},
            },
            "additionalProperties": False,
            "$schema": MCP_JSON_SCHEMA_URI,
        },
        outputSchema={
            "type": "object",
            "properties": {
                "gates_checked": {"type": "integer"},
                "gates_passed": {"type": "integer"},
                "gates_failed": {"type": "integer"},
                "results": {"type": "array", "items": {"type": "object", "properties": {"gate_id": {"type": "string"}, "status": {"type": "string"}, "severity": {"type": "string"}, "message": {"type": "string"}, "details": {"type": "object"}}}},
                "phase": {"type": "string"},
                "can_proceed": {"type": "boolean"},
            },
        },
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False),
    )


async def handle_tool(arguments: dict, context: dict):
    gate_ids = arguments.get("gate_ids")
    phase = arguments.get("phase")
    project_path = arguments.get("project_path", ".")
    severity_filter = arguments.get("severity_filter", "all")
    force_refresh = arguments.get("force_refresh", False)

    root = Path(project_path)
    if not root.exists():
        return [TextContent(type="text", text=json.dumps(make_error_response(
            code="PROJECT_NOT_FOUND",
            message=f"Project path not found: {project_path}",
            details={"project_path": project_path},
        ), ensure_ascii=False), isError=True)]

    gates_to_check = list(_QUALITY_GATES)
    if gate_ids:
        gate_id_set = set(gate_ids)
        gates_to_check = [g for g in gates_to_check if g["gate_id"] in gate_id_set]
    if phase is not None:
        try:
            phase_int = int(phase)
            gates_to_check = [g for g in gates_to_check if g["phase"] == phase_int]
        except (ValueError, TypeError):
            pass
    if severity_filter != "all":
        gates_to_check = [g for g in gates_to_check if g["severity"] == severity_filter]

    results = []
    for gate in gates_to_check:
        gate_result = _check_single_gate(gate, root)
        results.append(gate_result)

    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = len(results) - passed
    can_proceed = all(r["status"] == "PASS" or r["severity"] != "BLOCK" for r in results)

    result = {
        "gates_checked": len(results),
        "gates_passed": passed,
        "gates_failed": failed,
        "results": results,
        "phase": phase,
        "can_proceed": can_proceed,
    }
    return [TextContent(type="text", text=json.dumps(make_response("success", result), ensure_ascii=False))]
