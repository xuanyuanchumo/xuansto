import json
from pathlib import Path

from ..config import make_response, make_error_response, mcp_available
from ._shared import MCP_JSON_SCHEMA_URI

if mcp_available:
    from mcp.types import Tool, TextContent, ToolAnnotations


def get_tool_definition():
    if not mcp_available:
        return None
    return Tool(
        name="spec_drift_detect",
        description=(
            "[Read-Only] [Idempotent] Detect specification drift between spec directory and source directory.\n\n"
            "Use this tool to check if implementation has diverged from specification documents. "
            "Scans spec files and checks for corresponding implementations, reporting mismatches, "
            "missing implementations, and coverage percentage.\n\n"
            "Parameters:\n"
            "- spec_dir (string, default='.trae/specs'): Specification document directory.\n"
            "- src_dir (string, default='.'): Source code directory.\n\n"
            "Returns an object with:\n"
            "- total_specs: Total spec files found.\n"
            "- drifts_detected: Number of drift items.\n"
            "- drifts: Array of drift items (spec_file, spec_requirement, implementation, drift_type, severity, description, suggestion).\n"
            "- coverage_pct: Implementation coverage percentage.\n\n"
            "Example: Detect drift:\n"
            '{"spec_dir": ".trae/specs", "src_dir": "src"}'
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "spec_dir": {"type": "string", "description": "Specification document directory", "default": ".trae/specs"},
                "src_dir": {"type": "string", "description": "Source code directory", "default": "."},
            },
            "additionalProperties": False,
            "$schema": MCP_JSON_SCHEMA_URI,
        },
        outputSchema={
            "type": "object",
            "properties": {
                "total_specs": {"type": "integer"},
                "drifts_detected": {"type": "integer"},
                "drifts": {"type": "array", "items": {"type": "object", "properties": {"spec_file": {"type": "string"}, "spec_requirement": {"type": "string"}, "implementation": {"type": "string"}, "drift_type": {"type": "string"}, "severity": {"type": "string"}, "description": {"type": "string"}, "suggestion": {"type": "string"}}}},
                "coverage_pct": {"type": "number"},
            },
        },
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False),
    )


async def handle_tool(arguments: dict, context: dict):
    spec_dir = arguments.get("spec_dir", ".trae/specs")
    src_dir = arguments.get("src_dir", ".")
    fallback = context.get("fallback")

    if fallback:
        fallback_result = fallback.call_tool("spec_drift_detect", arguments)
        if fallback_result.get("status") != "error" and fallback_result.get("data", {}).get("degraded"):
            data = fallback_result["data"]
            total_specs = 0
            spec_path = Path(src_dir) / spec_dir
            if spec_path.exists():
                total_specs = len(list(spec_path.rglob("*.md")))
            drifts = []
            for item in data.get("items", []):
                drifts.append({
                    "spec_file": item.get("spec", ""),
                    "spec_requirement": "",
                    "implementation": "",
                    "drift_type": "NO_IMPLEMENTATION",
                    "severity": "HIGH",
                    "description": f"No implementation found for spec: {item.get('spec', '')}",
                    "suggestion": f"Create implementation matching {item.get('spec', '')}",
                })
            coverage = ((total_specs - len(drifts)) / total_specs * 100) if total_specs > 0 else 100.0
            result = {
                "total_specs": total_specs,
                "drifts_detected": len(drifts),
                "drifts": drifts,
                "coverage_pct": round(coverage, 1),
            }
            return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]

    spec_path = Path(src_dir) / spec_dir
    src_path = Path(src_dir)
    if not spec_path.exists():
        return [TextContent(type="text", text=json.dumps(make_error_response(
            code="INVALID_INPUT",
            message=f"Spec directory not found: {spec_dir}",
            details={"spec_dir": spec_dir},
        ), ensure_ascii=False), isError=True)]

    drifts = []
    total_specs = 0
    for spec_file in spec_path.rglob("*.md"):
        total_specs += 1
        spec_name = spec_file.stem
        found_impl = False
        for ext in (".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java"):
            candidates = list(src_path.rglob(f"{spec_name}{ext}"))
            if candidates:
                found_impl = True
                break
        if not found_impl:
            drifts.append({
                "spec_file": str(spec_file.relative_to(src_path)),
                "spec_requirement": spec_name,
                "implementation": "",
                "drift_type": "NO_IMPLEMENTATION",
                "severity": "HIGH",
                "description": f"No implementation found for spec: {spec_name}",
                "suggestion": f"Create implementation matching {spec_name}",
            })

    coverage = ((total_specs - len(drifts)) / total_specs * 100) if total_specs > 0 else 100.0
    result = {
        "total_specs": total_specs,
        "drifts_detected": len(drifts),
        "drifts": drifts,
        "coverage_pct": round(coverage, 1),
    }
    return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]
