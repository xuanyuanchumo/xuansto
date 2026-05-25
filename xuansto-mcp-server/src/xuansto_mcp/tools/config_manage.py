from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from ..core.config import (
    _CONFIG_VALIDATION_RESULTS,
    GATE_SCRIPTS_MAP,
    HOOK_SCRIPTS_MAP,
    QUALITY_GATES_PHASE_MAP,
    SKILL_ROOT,
    WORK_DIR,
    _resolve_skill_file,
    _validate_config,
    reload_config,
)
from ..core.errors import ERR_VALIDATION, make_error_response, make_success_response
from ..core.logging_config import get_logger
from ..core.validator import validate_input
from ..models.schemas import ConfigManageInput

logger = get_logger("config_manage")


def _validate_all_configs() -> dict[str, Any]:
    results: dict[str, Any] = {}
    try:
        from ..models.config_models import ConstraintsModel, FallbackConfigModel, SkillConfigModel
    except ImportError:
        return {"error": True, "message": "config_models not available"}

    skill_config_path = _resolve_skill_file(".xuansto-config.yaml")
    if skill_config_path.exists():
        try:
            import yaml
            data = yaml.safe_load(skill_config_path.read_text(encoding="utf-8")) or {}
            errors = _validate_config(data, SkillConfigModel, ".xuansto-config.yaml")
            results[".xuansto-config.yaml"] = {
                "valid": len(errors) == 0,
                "errors": errors,
                "path": str(skill_config_path),
            }
        except Exception as exc:
            results[".xuansto-config.yaml"] = {"valid": False, "errors": [str(exc)], "path": str(skill_config_path)}
    else:
        results[".xuansto-config.yaml"] = {"valid": True, "errors": [], "path": str(skill_config_path), "note": "file not found, using defaults"}

    fallback_config_path = _resolve_skill_file("fallback_config.yaml")
    if fallback_config_path.exists():
        try:
            import yaml
            data = yaml.safe_load(fallback_config_path.read_text(encoding="utf-8")) or {}
            errors = _validate_config(data, FallbackConfigModel, "fallback_config.yaml")
            results["fallback_config.yaml"] = {
                "valid": len(errors) == 0,
                "errors": errors,
                "path": str(fallback_config_path),
            }
        except Exception as exc:
            results["fallback_config.yaml"] = {"valid": False, "errors": [str(exc)], "path": str(fallback_config_path)}
    else:
        results["fallback_config.yaml"] = {"valid": True, "errors": [], "path": str(fallback_config_path), "note": "file not found, using defaults"}

    constraints_config_path = _resolve_skill_file("constraints.yaml")
    if constraints_config_path.exists():
        try:
            import yaml
            data = yaml.safe_load(constraints_config_path.read_text(encoding="utf-8")) or {}
            errors = _validate_config(data, ConstraintsModel, "constraints.yaml")
            results["constraints.yaml"] = {
                "valid": len(errors) == 0,
                "errors": errors,
                "path": str(constraints_config_path),
            }
        except Exception as exc:
            results["constraints.yaml"] = {"valid": False, "errors": [str(exc)], "path": str(constraints_config_path)}
    else:
        results["constraints.yaml"] = {"valid": True, "errors": [], "path": str(constraints_config_path), "note": "file not found, using defaults"}

    return results


def _get_config_status() -> dict[str, Any]:
    return {
        "skill_root": str(SKILL_ROOT),
        "work_dir": str(WORK_DIR),
        "gate_scripts_count": len(GATE_SCRIPTS_MAP),
        "gates_by_phase_count": len(QUALITY_GATES_PHASE_MAP),
        "hook_scripts_count": len(HOOK_SCRIPTS_MAP),
        "validation_results": dict(_CONFIG_VALIDATION_RESULTS),
        "config_files": {
            ".xuansto-config.yaml": str(_resolve_skill_file(".xuansto-config.yaml")),
            "fallback_config.yaml": str(_resolve_skill_file("fallback_config.yaml")),
            "constraints.yaml": str(_resolve_skill_file("constraints.yaml")),
        },
    }


def _inline_config_manage(action: str, **kwargs: Any) -> dict[str, Any]:
    if action == "status":
        return {
            "action": "status",
            "config_files": {
                ".xuansto-config.yaml": "not checked",
                "fallback_config.yaml": "not checked",
                "constraints.yaml": "not checked",
            },
            "managed": True,
        }
    elif action == "reload":
        return {
            "action": "reload",
            "reloaded": False,
            "note": "inline fallback cannot reload config",
            "managed": True,
        }
    elif action == "validate":
        return {
            "action": "validate",
            "validation_results": {},
            "managed": True,
        }
    return {"action": action, "config": {}}


def register(mcp: FastMCP) -> None:
    @mcp.tool(
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        )
    )
    async def config_manage(
        action: str,
    ) -> dict[str, Any]:
        """配置管理：重载/查询状态/校验YAML配置文件。reload操作重新读取所有YAML配置并校验，status操作返回当前配置状态和校验结果，validate操作对所有配置文件运行Pydantic校验。"""
        validated, err = validate_input(ConfigManageInput, action=action)
        if err:
            return err
        logger.info("config_manage called: action=%s", action)
        try:
            if action == "reload":
                reload_result = reload_config()
                validation_results = _validate_all_configs()
                reload_result["validation_results"] = validation_results
                return make_success_response(reload_result)
            elif action == "status":
                return make_success_response(_get_config_status())
            elif action == "validate":
                return make_success_response(_validate_all_configs())
            else:
                return make_error_response(ValueError(f"未知操作: {action}，支持: reload, status, validate"), error_code=ERR_VALIDATION)
        except Exception as e:
            logger.error("config_manage error: %s", e)
            return make_error_response(e)
