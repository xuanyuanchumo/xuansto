from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any

ERR_VALIDATION = "ERR_VALIDATION"
ERR_NOT_FOUND = "ERR_NOT_FOUND"
ERR_TIMEOUT = "ERR_TIMEOUT"
ERR_DEGRADATION = "ERR_DEGRADATION"
ERR_CONFIG = "ERR_CONFIG"
ERR_INTERNAL = "ERR_INTERNAL"
ERR_RATE_LIMIT = "ERR_RATE_LIMIT"
ERR_PERMISSION = "ERR_PERMISSION"


class ErrorCodes:
    TOOL_NOT_FOUND = "TOOL_NOT_FOUND"
    INVALID_PARAMS = "INVALID_PARAMS"
    EXECUTION_FAILED = "EXECUTION_FAILED"
    RATE_LIMITED = "RATE_LIMITED"
    BLOCKED_BY_HOOK = "BLOCKED_BY_HOOK"
    SECURITY_VIOLATION = "SECURITY_VIOLATION"
    DEGRADED = "DEGRADED"
    TIMEOUT = "TIMEOUT"
    NOT_FOUND = "NOT_FOUND"
    INTERNAL_ERROR = "INTERNAL_ERROR"


def make_response(data: Any = None, error: bool = False, error_code: str = "", message: str = "") -> dict[str, Any]:
    if error:
        return {"error": True, "error_code": error_code, "message": message, "data": None}
    return {"error": False, "data": data}

ERROR_CODE_TO_HTTP_STATUS: dict[str, int] = {
    ERR_VALIDATION: 400,
    ERR_NOT_FOUND: 404,
    ERR_TIMEOUT: 408,
    ERR_DEGRADATION: 503,
    ERR_CONFIG: 500,
    ERR_INTERNAL: 500,
    ERR_RATE_LIMIT: 429,
    ERR_PERMISSION: 403,
}

_ERROR_MESSAGES: dict[str, dict[str, str]] = {
    ERR_VALIDATION: {"zh": "参数校验失败", "en": "Validation failed"},
    ERR_NOT_FOUND: {"zh": "资源未找到", "en": "Resource not found"},
    ERR_TIMEOUT: {"zh": "操作超时", "en": "Operation timed out"},
    ERR_DEGRADATION: {"zh": "服务降级", "en": "Service degradation"},
    ERR_CONFIG: {"zh": "配置错误", "en": "Configuration error"},
    ERR_INTERNAL: {"zh": "内部错误", "en": "Internal error"},
    ERR_RATE_LIMIT: {"zh": "请求频率超限", "en": "Rate limit exceeded"},
    ERR_PERMISSION: {"zh": "权限不足", "en": "Permission denied"},
}

_EXCEPTION_CODE_TO_ERR_CODE: dict[str, str] = {
    "VALIDATION_ERROR": ERR_VALIDATION,
    "PATH_NOT_FOUND": ERR_NOT_FOUND,
    "NOT_FOUND": ERR_NOT_FOUND,
    "AGENT_BUSY": ERR_PERMISSION,
    "SCRIPT_EXECUTION_ERROR": ERR_INTERNAL,
    "DEGRADATION": ERR_DEGRADATION,
    "RECOVER_FAILED": ERR_INTERNAL,
    "TIMEOUT": ERR_TIMEOUT,
    "INTERNAL_ERROR": ERR_INTERNAL,
    "YAML_PARSE_ERROR": ERR_CONFIG,
    "RETRY_EXHAUSTED": ERR_INTERNAL,
}


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


class RetryExhaustedError(XuanstoMCPError):
    def __init__(self, tool_name: str, attempts: int, last_error: Exception):
        self.last_error = last_error
        super().__init__(
            code="RETRY_EXHAUSTED",
            message=f"工具 {tool_name} 重试 {attempts} 次后仍失败: {last_error}",
            details={"tool": tool_name, "attempts": attempts, "last_error": str(last_error)},
        )


_TRANSIENT_ERROR_CODES = frozenset({
    "TIMEOUT",
    "CONNECTION_ERROR",
    "CONNECTION_RESET",
    "SERVICE_UNAVAILABLE",
    "DEGRADATION",
    "RATE_LIMITED",
})

_PERMANENT_ERROR_CODES = frozenset({
    "VALIDATION_ERROR",
    "PATH_NOT_FOUND",
    "WORKFLOW_NOT_FOUND",
    "PERMISSION_DENIED",
    "INVALID_INPUT",
})


def is_transient_error(error: Exception) -> bool:
    if isinstance(error, (asyncio.TimeoutError, TimeoutError, ConnectionError, OSError)):
        return True
    if isinstance(error, XuanstoMCPError):
        return error.code in _TRANSIENT_ERROR_CODES
    try:
        from pydantic import ValidationError as PydanticValidationError
        if isinstance(error, PydanticValidationError):
            return False
    except ImportError:
        pass
    return False


def is_permanent_error(error: Exception) -> bool:
    if isinstance(error, XuanstoMCPError):
        return error.code in _PERMANENT_ERROR_CODES
    return False


def is_retryable_error(error: Exception) -> bool:
    return is_transient_error(error)


def _determine_retryable(error: Exception) -> bool:
    if is_transient_error(error):
        return True
    if is_permanent_error(error):
        return False
    return False


async def retry_tool_call(
    tool_name: str,
    fn: Callable[..., Any],
    kwargs: dict[str, Any],
    max_retries: int = 3,
    base_delay: float = 1.0,
) -> Any:
    from .logging_config import get_logger
    logger = get_logger("retry")

    last_error: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            if asyncio.iscoroutinefunction(fn):
                return await fn(**kwargs)
            else:
                return fn(**kwargs)
        except Exception as e:
            last_error = e
            if is_permanent_error(e) or not is_transient_error(e):
                raise
            if attempt >= max_retries:
                break
            delay = base_delay * (2 ** attempt)
            logger.warning(
                "Tool %s attempt %d/%d failed (transient): %s, retrying in %.1fs",
                tool_name, attempt + 1, max_retries + 1, e, delay,
            )
            await asyncio.sleep(delay)
    raise RetryExhaustedError(tool_name, max_retries + 1, last_error or Exception("unknown"))


def _resolve_error_code(error: Exception, error_code: str | None = None) -> str | None:
    if error_code:
        return error_code
    if isinstance(error, XuanstoMCPError):
        return _EXCEPTION_CODE_TO_ERR_CODE.get(error.code)
    if isinstance(error, ValueError):
        return ERR_VALIDATION
    if isinstance(error, (TimeoutError, asyncio.TimeoutError)):
        return ERR_TIMEOUT
    if isinstance(error, PermissionError):
        return ERR_PERMISSION
    if isinstance(error, RuntimeError):
        return ERR_INTERNAL
    return None


def _get_i18n_message(error_code: str, language: str = "zh") -> str | None:
    messages = _ERROR_MESSAGES.get(error_code)
    if not messages:
        return None
    return messages.get(language, messages.get("zh"))


def make_error_response(error: Exception, error_code: str | None = None, language: str = "zh") -> dict[str, Any]:
    resolved_code = _resolve_error_code(error, error_code)
    if isinstance(error, XuanstoMCPError):
        result: dict[str, Any] = {
            "error": True,
            "error_code": resolved_code or _EXCEPTION_CODE_TO_ERR_CODE.get(error.code, ERR_INTERNAL),
            "message": error.message,
            "details": error.details,
            "retryable": _determine_retryable(error),
        }
        result["code"] = result["error_code"]
        result["_deprecated_exception_type"] = error.code
        if resolved_code:
            i18n_msg = _get_i18n_message(resolved_code, language)
            if i18n_msg and language != "zh":
                result["message_i18n"] = i18n_msg
        result["_migration_note"] = "Field 'code' is deprecated; use 'error_code' instead. Original exception type available in '_deprecated_exception_type'."
        result["language"] = language
        return result
    try:
        from pydantic import ValidationError as PydanticValidationError
        if isinstance(error, PydanticValidationError):
            details = [{"field": ".".join(str(loc) for loc in e["loc"]), "message": e["msg"]} for e in error.errors()]
            result = {
                "error": True,
                "error_code": resolved_code or ERR_VALIDATION,
                "message": f"参数校验失败: {len(details)}个错误",
                "details": {"errors": details},
                "retryable": False,
            }
            result["code"] = result["error_code"]
            result["_deprecated_exception_type"] = "VALIDATION_ERROR"
            if resolved_code:
                i18n_msg = _get_i18n_message(resolved_code, language)
                if i18n_msg and language != "zh":
                    result["message_i18n"] = i18n_msg
            result["_migration_note"] = "Field 'code' is deprecated; use 'error_code' instead. Original exception type available in '_deprecated_exception_type'."
            result["language"] = language
            return result
    except ImportError:
        pass
    result = {
        "error": True,
        "error_code": resolved_code or ERR_INTERNAL,
        "message": _get_i18n_message(ERR_INTERNAL, language) or "内部错误",
        "details": {},
        "retryable": _determine_retryable(error),
    }
    result["code"] = result["error_code"]
    result["_deprecated_exception_type"] = "INTERNAL_ERROR"
    if isinstance(error, (ValueError, TypeError, KeyError)):
        result["message"] = str(error)
        result["_deprecated_exception_type"] = "VALIDATION_ERROR"
        if not resolved_code:
            result["error_code"] = ERR_VALIDATION
    if resolved_code:
        i18n_msg = _get_i18n_message(resolved_code, language)
        if i18n_msg and language != "zh":
            result["message_i18n"] = i18n_msg
    result["_migration_note"] = "Field 'code' is deprecated; use 'error_code' instead. Original exception type available in '_deprecated_exception_type'."
    result["language"] = language
    return result


def make_success_response(data: Any = None, degradation_level: str | None = None) -> dict[str, Any]:
    from .config import MCP_API_VERSION
    result: dict[str, Any] = {"error": False, "api_version": MCP_API_VERSION}
    if data is not None:
        result["data"] = data
    if degradation_level is not None:
        result["degradation_level"] = degradation_level
        result["degraded"] = True
    return result


class DegradationCoordinator:
    def __init__(self):
        self._handlers: dict[str, Callable[..., Any]] = {}

    def register_handler(self, error_code: str, handler: Callable[..., Any]) -> None:
        self._handlers[error_code] = handler

    def handle(self, error: Exception, tool_name: str, **kwargs: Any) -> dict[str, Any]:
        if isinstance(error, XuanstoMCPError):
            handler = self._handlers.get(error.code)
            if handler:
                try:
                    return handler(tool_name, error, **kwargs)
                except Exception:
                    pass
        from .degradation import get_fallback
        fallback = get_fallback(tool_name)
        if fallback:
            try:
                result = fallback(**kwargs)
                if isinstance(result, dict):
                    result["degraded"] = True
                return result
            except Exception:
                pass
        return make_error_response(error)


def is_tool_execution_error(error: Exception) -> bool:
    if isinstance(error, XuanstoMCPError):
        return error.code not in ("PROTOCOL_ERROR", "TRANSPORT_ERROR")
    return not isinstance(error, (ConnectionError, OSError))
