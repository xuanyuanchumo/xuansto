from __future__ import annotations

from typing import Any


class XuanstoMCPError(Exception):
    def __init__(self, code: str, message: str, details: dict[str, Any] | None = None):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(message)


class PathNotFoundError(XuanstoMCPError):
    def __init__(self, path: str):
        super().__init__(
            code="PATH_NOT_FOUND",
            message=f"路径不存在: {path}",
            details={"path": path, "suggestion": "请检查路径是否正确"},
        )


class ScriptExecutionError(XuanstoMCPError):
    def __init__(self, script: str, reason: str):
        super().__init__(
            code="SCRIPT_EXECUTION_ERROR",
            message=f"脚本执行失败: {script}",
            details={"script": script, "reason": reason},
        )


class DegradationError(XuanstoMCPError):
    def __init__(self, level: str, reason: str):
        super().__init__(
            code="DEGRADATION",
            message=f"服务降级: {level}",
            details={"level": level, "reason": reason},
        )


class ValidationError(XuanstoMCPError):
    def __init__(self, details: list[dict[str, Any]]):
        self.validation_details = details
        super().__init__(
            code="VALIDATION_ERROR",
            message=f"参数校验失败: {len(details)}个错误",
            details={"errors": details},
        )


def make_error_response(error: Exception) -> dict[str, Any]:
    if isinstance(error, XuanstoMCPError):
        return {
            "error": True,
            "code": error.code,
            "message": error.message,
            "details": error.details,
        }
    try:
        from pydantic import ValidationError as PydanticValidationError
        if isinstance(error, PydanticValidationError):
            details = [{"field": ".".join(str(l) for l in e["loc"]), "message": e["msg"]} for e in error.errors()]
            return {
                "error": True,
                "code": "VALIDATION_ERROR",
                "message": f"参数校验失败: {len(details)}个错误",
                "details": {"errors": details},
            }
    except ImportError:
        pass
    return {
        "error": True,
        "code": "INTERNAL_ERROR",
        "message": str(error),
        "details": {},
    }


def make_success_response(data: Any = None, degradation_level: str | None = None) -> dict[str, Any]:
    from .config import MCP_API_VERSION
    result: dict[str, Any] = {"error": False, "api_version": MCP_API_VERSION}
    if data is not None:
        result["data"] = data
    if degradation_level is not None:
        result["degradation_level"] = degradation_level
    return result
