from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from ..core.errors import ERR_NOT_FOUND, ERR_VALIDATION, make_error_response, make_success_response
from ..core.logging_config import get_logger
from ..core.notifications import notify
from ..core.validator import validate_input, validate_path_safety
from ..models.schemas import ProjectInitInput

logger = get_logger("project_init")

STACK_MARKERS: dict[str, list[str]] = {
    "python": ["requirements.txt", "setup.py", "pyproject.toml", "Pipfile", "poetry.lock"],
    "node": ["package.json", "yarn.lock", "pnpm-lock.yaml", ".npmrc"],
    "rust": ["Cargo.toml", "Cargo.lock"],
    "go": ["go.mod", "go.sum"],
    "java": ["pom.xml", "build.gradle", "build.gradle.kts"],
    "dotnet": [".csproj", ".fsproj", "global.json", "Directory.Build.props"],
    "ruby": ["Gemfile", "Rakefile"],
    "php": ["composer.json"],
    "swift": ["Package.swift"],
    "flutter": ["pubspec.yaml"],
}

CONFIG_TEMPLATE = """name: {name}
description: {description}
stack:
{stack_items}
template: {template}
created_at: {created_at}
version: "1.0"
"""


def _create_project(
    name: str | None = None,
    description: str | None = None,
    stack: list[str] | None = None,
    template: str | None = None,
    directory: str | None = None,
) -> dict[str, Any]:
    if not name:
        return {"error": True, "message": "项目名称不能为空"}
    project_dir = Path(directory) if directory else Path.cwd() / name
    project_dir.mkdir(parents=True, exist_ok=True)
    config_path = project_dir / ".xuansto-config.yaml"
    if config_path.exists():
        return {"error": True, "message": f"项目配置已存在: {config_path}"}
    stack_items = "\n".join(f"  - {s}" for s in (stack or []))
    content = CONFIG_TEMPLATE.format(
        name=name,
        description=description or "",
        stack_items=stack_items or "  []",
        template=template or "default",
        created_at=datetime.now().isoformat(),
    )
    config_path.write_text(content, encoding="utf-8")
    notify(f"Project initialized: {name} at {project_dir}", "info")
    return {
        "name": name,
        "directory": str(project_dir),
        "config_path": str(config_path),
        "stack": stack or [],
        "template": template or "default",
    }


def _validate_project(project_path: str | None = None) -> dict[str, Any]:
    if not project_path:
        return {"error": True, "message": "项目路径不能为空"}
    path = Path(project_path)
    if not path.exists():
        return {"error": True, "message": f"路径不存在: {project_path}"}
    config_path = path / ".xuansto-config.yaml"
    issues: list[dict[str, str]] = []
    if not config_path.exists():
        issues.append({"severity": "BLOCK", "code": "NO_CONFIG", "message": "缺少.xuansto-config.yaml配置文件"})
    else:
        try:
            text = config_path.read_text(encoding="utf-8")
            if "name:" not in text:
                issues.append({"severity": "WARN", "code": "MISSING_NAME", "message": "配置文件缺少name字段"})
            if "stack:" not in text:
                issues.append({"severity": "WARN", "code": "MISSING_STACK", "message": "配置文件缺少stack字段"})
        except Exception as e:
            issues.append({"severity": "BLOCK", "code": "CONFIG_READ_ERROR", "message": str(e)})
    return {
        "project_path": str(path),
        "valid": len([i for i in issues if i["severity"] == "BLOCK"]) == 0,
        "issues": issues,
        "total_issues": len(issues),
        "block_count": len([i for i in issues if i["severity"] == "BLOCK"]),
        "warn_count": len([i for i in issues if i["severity"] == "WARN"]),
    }


def _detect_stack(project_path: str | None = None) -> dict[str, Any]:
    if not project_path:
        return {"error": True, "message": "项目路径不能为空"}
    path = Path(project_path)
    if not path.exists():
        return {"error": True, "message": f"路径不存在: {project_path}"}
    detected: list[dict[str, Any]] = []
    for stack_name, markers in STACK_MARKERS.items():
        found_markers = []
        for marker in markers:
            if list(path.glob(marker)) or list(path.rglob(marker)):
                found_markers.append(marker)
        if found_markers:
            detected.append({
                "stack": stack_name,
                "confidence": min(len(found_markers) / len(markers), 1.0),
                "markers_found": found_markers,
            })
    detected.sort(key=lambda x: x["confidence"], reverse=True)
    return {
        "project_path": str(path),
        "detected_stacks": detected,
        "primary_stack": detected[0]["stack"] if detected else None,
        "total_detected": len(detected),
    }


def _configure_project(
    project_path: str | None = None,
    name: str | None = None,
    description: str | None = None,
    stack: list[str] | None = None,
) -> dict[str, Any]:
    if not project_path:
        return {"error": True, "message": "项目路径不能为空"}
    path = Path(project_path)
    if not path.exists():
        return {"error": True, "message": f"路径不存在: {project_path}"}
    config_path = path / ".xuansto-config.yaml"
    if config_path.exists():
        try:
            import yaml
            existing = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        except Exception:
            existing = {}
    else:
        existing = {}
    if name:
        existing["name"] = name
    if description:
        existing["description"] = description
    if stack:
        existing["stack"] = stack
    if not existing.get("name"):
        existing["name"] = path.name
    if "created_at" not in existing:
        existing["created_at"] = datetime.now().isoformat()
    existing["updated_at"] = datetime.now().isoformat()
    stack_items = "\n".join(f"  - {s}" for s in existing.get("stack", []))
    content = CONFIG_TEMPLATE.format(
        name=existing.get("name", ""),
        description=existing.get("description", ""),
        stack_items=stack_items or "  []",
        template=existing.get("template", "default"),
        created_at=existing.get("created_at", ""),
    )
    config_path.write_text(content, encoding="utf-8")
    notify(f"Project configured: {existing.get('name', '')} at {path}", "info")
    return {
        "name": existing.get("name", ""),
        "directory": str(path),
        "config_path": str(config_path),
        "stack": existing.get("stack", []),
        "configured": True,
    }


def _inline_project_init(action: str, **kwargs: Any) -> dict[str, Any]:
    if action == "create":
        return _create_project(**{k: v for k, v in kwargs.items() if k in ("name", "description", "stack", "template", "directory")})
    elif action == "validate":
        return _validate_project(kwargs.get("project_path"))
    elif action == "detect_stack":
        return _detect_stack(kwargs.get("project_path"))
    return {"error": True, "message": f"未知操作: {action}"}


def register(mcp: FastMCP) -> None:
    @mcp.tool(
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=False,
            openWorldHint=False,
        )
    )
    async def project_init(
        action: str,
        name: str | None = None,
        description: str | None = None,
        stack: list[str] | None = None,
        template: str | None = None,
        directory: str | None = None,
        project_path: str | None = None,
    ) -> dict[str, Any]:
        """项目初始化管理：创建项目、验证项目配置、检测技术栈、配置已有项目。create/init操作初始化新项目(含名称/描述/技术栈/模板/目录)，validate操作验证项目配置完整性，detect_stack/detect操作自动检测项目使用的技术栈，configure操作配置已有项目。"""
        validated, err = validate_input(ProjectInitInput, action=action, name=name, description=description, stack=stack, template=template, directory=directory, project_path=project_path)
        if err:
            return err
        logger.info("project_init called: action=%s", action)
        try:
            if action in ("create", "init"):
                if not name:
                    return make_error_response(ValueError("create操作需要name参数"), error_code=ERR_VALIDATION)
                if directory:
                    safe_dir, dir_err = validate_path_safety(directory, allow_absolute=True)
                    if dir_err:
                        return make_error_response(ValueError(dir_err), error_code=ERR_VALIDATION)
                result = _create_project(name, description, stack, template, directory)
                if result.get("error"):
                    return make_error_response(ValueError(result["message"]), error_code=ERR_VALIDATION)
                return make_success_response(result)
            elif action == "validate":
                if not project_path:
                    return make_error_response(ValueError("validate操作需要project_path参数"), error_code=ERR_VALIDATION)
                safe_path, path_err = validate_path_safety(project_path, allow_absolute=True)
                if path_err:
                    return make_error_response(ValueError(path_err), error_code=ERR_VALIDATION)
                result = _validate_project(project_path)
                if result.get("error"):
                    return make_error_response(ValueError(result["message"]), error_code=ERR_NOT_FOUND)
                return make_success_response(result)
            elif action in ("detect_stack", "detect"):
                if not project_path:
                    return make_error_response(ValueError("detect操作需要project_path参数"), error_code=ERR_VALIDATION)
                safe_path, path_err = validate_path_safety(project_path, allow_absolute=True)
                if path_err:
                    return make_error_response(ValueError(path_err), error_code=ERR_VALIDATION)
                result = _detect_stack(project_path)
                if result.get("error"):
                    return make_error_response(ValueError(result["message"]), error_code=ERR_NOT_FOUND)
                return make_success_response(result)
            elif action == "configure":
                if not project_path:
                    return make_error_response(ValueError("configure操作需要project_path参数"), error_code=ERR_VALIDATION)
                safe_path, path_err = validate_path_safety(project_path, allow_absolute=True)
                if path_err:
                    return make_error_response(ValueError(path_err), error_code=ERR_VALIDATION)
                result = _configure_project(project_path, name, description, stack)
                if result.get("error"):
                    return make_error_response(ValueError(result["message"]), error_code=ERR_VALIDATION)
                return make_success_response(result)
            else:
                return make_error_response(ValueError(f"未知操作: {action}，支持: create, init, validate, detect_stack, detect, configure"), error_code=ERR_VALIDATION)
        except Exception as e:
            logger.error("project_init error: %s", e)
            return make_error_response(e)
