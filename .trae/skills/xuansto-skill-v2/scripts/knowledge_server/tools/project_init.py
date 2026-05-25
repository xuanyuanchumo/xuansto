import json
import os
from pathlib import Path

from ..config import make_response, make_error_response, mcp_available
from ._shared import MCP_JSON_SCHEMA_URI

if mcp_available:
    from mcp.types import Tool, TextContent, ToolAnnotations


def get_tool_definition():
    if not mcp_available:
        return None
    return Tool(
        name="project_init",
        description=(
            "Project initialization: create, validate, detect_stack.\n\n"
            "Use this tool to create new projects with templates, validate existing project "
            "configurations, or detect the technology stack of a project.\n\n"
            "Parameters:\n"
            "- action (string, required, enum: create|validate|detect_stack): Operation type.\n"
            "- name (string, optional): Project name (create action).\n"
            "- description (string, optional): Project description (create action).\n"
            "- stack (array of strings, optional): Technology stack list (create action).\n"
            "- template (string, optional): Project template (create action).\n"
            "- directory (string, optional): Project directory (create action).\n"
            "- project_path (string, optional): Project path (validate/detect_stack action).\n\n"
            "Returns an object with:\n"
            "- action: The action performed.\n"
            "- name: Project name.\n"
            "- directory: Project directory.\n"
            "- config_path: Configuration file path.\n"
            "- stack: Technology stack.\n"
            "- template: Template used.\n"
            "- valid: Validation result (validate action).\n"
            "- issues: Validation issues (validate action).\n"
            "- detected_stacks: Detected stacks (detect_stack action).\n\n"
            "Example: Create a project:\n"
            '{"action": "create", "name": "my-project", "stack": ["python", "react"]}'
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "action": {"type": "string", "description": "Operation: create, validate, detect_stack", "enum": ["create", "validate", "detect_stack"]},
                "name": {"type": "string", "description": "Project name (create)"},
                "description": {"type": "string", "description": "Project description (create)"},
                "stack": {"type": "array", "items": {"type": "string"}, "description": "Technology stack list (create)"},
                "template": {"type": "string", "description": "Project template (create)"},
                "directory": {"type": "string", "description": "Project directory (create)"},
                "project_path": {"type": "string", "description": "Project path (validate/detect_stack)"},
            },
            "required": ["action"],
            "additionalProperties": False,
            "$schema": MCP_JSON_SCHEMA_URI,
        },
        outputSchema={
            "type": "object",
            "properties": {
                "action": {"type": "string"},
                "name": {"type": "string"},
                "directory": {"type": "string"},
                "config_path": {"type": "string"},
                "stack": {"type": "array", "items": {"type": "string"}},
                "template": {"type": "string"},
                "valid": {"type": "boolean"},
                "issues": {"type": "array", "items": {"type": "object"}},
                "detected_stacks": {"type": "array", "items": {"type": "object"}},
            },
        },
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=False, openWorldHint=False),
    )


async def handle_tool(arguments: dict, context: dict):
    action = arguments.get("action", "")
    valid_actions = {"create", "validate", "detect_stack"}
    if action not in valid_actions:
        return [TextContent(type="text", text=json.dumps(make_error_response(
            code="INVALID_INPUT",
            message=f"Invalid action: {action}. Valid: {sorted(valid_actions)}",
            details={"action": action},
        ), ensure_ascii=False), isError=True)]

    if action == "create":
        name = arguments.get("name", "")
        if not name:
            return [TextContent(type="text", text=json.dumps(make_error_response(
                code="INVALID_INPUT",
                message="name is required for create action",
                details={},
            ), ensure_ascii=False), isError=True)]
        directory = arguments.get("directory", name)
        stack = arguments.get("stack", [])
        template = arguments.get("template", "default")
        description = arguments.get("description", "")
        config_path = os.path.join(directory, ".xuansto-config.yaml")
        result = {
            "action": "create",
            "name": name,
            "description": description,
            "directory": os.path.abspath(directory),
            "config_path": config_path,
            "stack": stack,
            "template": template,
        }
        return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]

    elif action == "validate":
        project_path = arguments.get("project_path", ".")
        ppath = Path(project_path)
        if not ppath.exists():
            return [TextContent(type="text", text=json.dumps(make_error_response(
                code="NOT_FOUND",
                message=f"Project path not found: {project_path}",
                details={"project_path": project_path},
            ), ensure_ascii=False), isError=True)]
        issues = []
        config_file = ppath / ".xuansto-config.yaml"
        if not config_file.exists():
            issues.append({"severity": "WARN", "code": "NO_CONFIG", "message": "No .xuansto-config.yaml found"})
        result = {
            "action": "validate",
            "project_path": str(ppath.resolve()),
            "valid": len([i for i in issues if i.get("severity") == "BLOCK"]) == 0,
            "issues": issues,
            "total_issues": len(issues),
            "block_count": sum(1 for i in issues if i.get("severity") == "BLOCK"),
            "warn_count": sum(1 for i in issues if i.get("severity") == "WARN"),
        }
        return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]

    elif action == "detect_stack":
        project_path = arguments.get("project_path", ".")
        ppath = Path(project_path)
        if not ppath.exists():
            return [TextContent(type="text", text=json.dumps(make_error_response(
                code="NOT_FOUND",
                message=f"Project path not found: {project_path}",
                details={"project_path": project_path},
            ), ensure_ascii=False), isError=True)]
        detected = []
        markers = {
            "python": ["requirements.txt", "pyproject.toml", "setup.py", "Pipfile"],
            "node": ["package.json"],
            "rust": ["Cargo.toml"],
            "go": ["go.mod"],
            "java": ["pom.xml", "build.gradle"],
        }
        for stack_name, marker_files in markers.items():
            found = [m for m in marker_files if (ppath / m).exists()]
            if found:
                detected.append({
                    "stack": stack_name,
                    "confidence": 1.0 if len(found) > 1 else 0.75,
                    "markers_found": found,
                })
        primary = detected[0]["stack"] if detected else "unknown"
        result = {
            "action": "detect_stack",
            "project_path": str(ppath.resolve()),
            "detected_stacks": detected,
            "primary_stack": primary,
            "total_detected": len(detected),
        }
        return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]
