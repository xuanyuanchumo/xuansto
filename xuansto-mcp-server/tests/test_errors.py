from __future__ import annotations

import asyncio
from unittest.mock import patch

import pytest

from xuansto_mcp.core.errors import (
    ERR_VALIDATION,
    ERR_NOT_FOUND,
    ERR_TIMEOUT,
    ERR_DEGRADATION,
    ERR_CONFIG,
    ERR_INTERNAL,
    ERR_RATE_LIMIT,
    ERR_PERMISSION,
    XuanstoMCPError,
    PathNotFoundError,
    ScriptExecutionError,
    DegradationError,
    ValidationError,
    RetryExhaustedError,
    is_transient_error,
    is_permanent_error,
    make_error_response,
    make_success_response,
    retry_tool_call,
    _resolve_error_code,
    _get_i18n_message,
)


def test_error_response_has_error_code_field():
    err = XuanstoMCPError(code="TEST_ERROR", message="test error")
    result = make_error_response(err, error_code=ERR_INTERNAL)
    assert "error_code" in result
    assert result["error_code"] == ERR_INTERNAL
    assert result["error"] is True


def test_error_response_no_code_field():
    err = XuanstoMCPError(code="TEST_ERROR", message="test error")
    result = make_error_response(err, error_code=ERR_INTERNAL)
    assert "code" not in result or "_deprecated_code" in result


def test_error_response_has_deprecated_code():
    err = XuanstoMCPError(code="TEST_ERROR", message="test error")
    result = make_error_response(err, error_code=ERR_INTERNAL)
    assert "_deprecated_code" in result
    assert result["_deprecated_code"] == "TEST_ERROR"


def test_error_response_has_migration_note():
    err = XuanstoMCPError(code="TEST_ERROR", message="test error")
    result = make_error_response(err, error_code=ERR_INTERNAL)
    assert "_migration_note" in result


def test_error_response_xuansto_mcp_error():
    err = XuanstoMCPError(code="VALIDATION_ERROR", message="validation failed", details={"field": "name"})
    result = make_error_response(err)
    assert result["error"] is True
    assert result["message"] == "validation failed"
    assert result["details"] == {"field": "name"}


def test_error_response_path_not_found():
    err = PathNotFoundError("/some/path")
    result = make_error_response(err)
    assert result["error"] is True
    assert result["error_code"] == ERR_NOT_FOUND
    assert "/some/path" in result["message"]


def test_error_response_script_execution_error():
    err = ScriptExecutionError("test.py", "import failed")
    result = make_error_response(err)
    assert result["error"] is True
    assert "test.py" in result["message"]


def test_error_response_degradation_error():
    err = DegradationError("L2", "chromadb down")
    result = make_error_response(err)
    assert result["error"] is True
    assert "L2" in result["message"]


def test_error_response_validation_error():
    err = ValidationError([{"field": "name", "message": "required"}])
    result = make_error_response(err)
    assert result["error"] is True
    assert "error_code" in result


def test_error_response_retry_exhausted():
    err = RetryExhaustedError("my_tool", 3, RuntimeError("boom"))
    result = make_error_response(err)
    assert result["error"] is True
    assert "my_tool" in result["message"]


def test_error_response_generic_exception():
    result = make_error_response(ValueError("bad value"))
    assert result["error"] is True
    assert result["message"] == "bad value"


def test_error_response_type_error():
    result = make_error_response(TypeError("wrong type"))
    assert result["error"] is True
    assert "wrong type" in result["message"]


def test_error_response_with_language():
    err = XuanstoMCPError(code="VALIDATION_ERROR", message="validation failed")
    result = make_error_response(err, language="en")
    assert result["language"] == "en"
    assert "message_i18n" in result


def test_error_response_default_language():
    err = XuanstoMCPError(code="VALIDATION_ERROR", message="validation failed")
    result = make_error_response(err, language="zh")
    assert result["language"] == "zh"


def test_is_transient_error_timeout():
    assert is_transient_error(TimeoutError("timed out")) is True


def test_is_transient_error_connection():
    assert is_transient_error(ConnectionError("refused")) is True


def test_is_transient_error_os_error():
    assert is_transient_error(OSError("broken pipe")) is True


def test_is_transient_error_degradation():
    err = XuanstoMCPError(code="DEGRADATION", message="degraded")
    assert is_transient_error(err) is True


def test_is_transient_error_rate_limited():
    err = XuanstoMCPError(code="RATE_LIMITED", message="too many")
    assert is_transient_error(err) is True


def test_is_transient_error_validation():
    err = XuanstoMCPError(code="VALIDATION_ERROR", message="bad input")
    assert is_transient_error(err) is False


def test_is_permanent_error_validation():
    err = XuanstoMCPError(code="VALIDATION_ERROR", message="bad input")
    assert is_permanent_error(err) is True


def test_is_permanent_error_not_found():
    err = XuanstoMCPError(code="PATH_NOT_FOUND", message="not found")
    assert is_permanent_error(err) is True


def test_is_permanent_error_permission():
    err = XuanstoMCPError(code="PERMISSION_DENIED", message="denied")
    assert is_permanent_error(err) is True


def test_is_permanent_error_transient():
    err = XuanstoMCPError(code="TIMEOUT", message="timed out")
    assert is_permanent_error(err) is False


def test_is_permanent_error_generic():
    assert is_permanent_error(RuntimeError("generic")) is False


@pytest.mark.asyncio
async def test_retry_tool_call_success():
    call_count = 0

    async def succeed(**kwargs):
        nonlocal call_count
        call_count += 1
        return "ok"

    result = await retry_tool_call("test_tool", succeed, {})
    assert result == "ok"
    assert call_count == 1


@pytest.mark.asyncio
async def test_retry_tool_call_permanent_error():
    async def fail_permanent(**kwargs):
        raise XuanstoMCPError(code="VALIDATION_ERROR", message="bad input")

    with pytest.raises(XuanstoMCPError):
        await retry_tool_call("test_tool", fail_permanent, {}, max_retries=3)


@pytest.mark.asyncio
async def test_retry_tool_call_transient_then_success():
    call_count = 0

    async def fail_then_succeed(**kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise XuanstoMCPError(code="TIMEOUT", message="timed out")
        return "ok"

    result = await retry_tool_call("test_tool", fail_then_succeed, {}, max_retries=3, base_delay=0.01)
    assert result == "ok"
    assert call_count == 3


@pytest.mark.asyncio
async def test_retry_tool_call_exhausted():
    async def always_fail(**kwargs):
        raise XuanstoMCPError(code="TIMEOUT", message="timed out")

    with pytest.raises(RetryExhaustedError):
        await retry_tool_call("test_tool", always_fail, {}, max_retries=2, base_delay=0.01)


@pytest.mark.asyncio
async def test_retry_tool_call_sync_function():
    def sync_fn(**kwargs):
        return "sync_ok"

    result = await retry_tool_call("test_tool", sync_fn, {})
    assert result == "sync_ok"


def test_resolve_error_code_explicit():
    assert _resolve_error_code(Exception(), ERR_VALIDATION) == ERR_VALIDATION


def test_resolve_error_code_xuansto_error():
    err = XuanstoMCPError(code="VALIDATION_ERROR", message="bad")
    result = _resolve_error_code(err)
    assert result == ERR_VALIDATION


def test_resolve_error_code_value_error():
    result = _resolve_error_code(ValueError("bad"))
    assert result == ERR_VALIDATION


def test_resolve_error_code_timeout():
    result = _resolve_error_code(TimeoutError("timed out"))
    assert result == ERR_TIMEOUT


def test_resolve_error_code_permission():
    result = _resolve_error_code(PermissionError("denied"))
    assert result == ERR_PERMISSION


def test_resolve_error_code_runtime():
    result = _resolve_error_code(RuntimeError("fail"))
    assert result == ERR_INTERNAL


def test_resolve_error_code_unknown():
    result = _resolve_error_code(KeyError("missing"))
    assert result is None


def test_get_i18n_message_zh():
    msg = _get_i18n_message(ERR_VALIDATION, "zh")
    assert msg is not None
    assert "校验" in msg


def test_get_i18n_message_en():
    msg = _get_i18n_message(ERR_VALIDATION, "en")
    assert msg is not None
    assert "Validation" in msg


def test_get_i18n_message_unknown_code():
    msg = _get_i18n_message("NONEXISTENT_CODE", "zh")
    assert msg is None


def test_make_success_response():
    result = make_success_response(data={"key": "value"})
    assert result["error"] is False
    assert result["data"] == {"key": "value"}
    assert "api_version" in result


def test_make_success_response_with_degradation_level():
    result = make_success_response(data={"key": "value"}, degradation_level="L2")
    assert result["degradation_level"] == "L2"


def test_make_success_response_no_data():
    result = make_success_response()
    assert result["error"] is False
    assert "data" not in result


def test_error_constants():
    assert ERR_VALIDATION == "ERR_VALIDATION"
    assert ERR_NOT_FOUND == "ERR_NOT_FOUND"
    assert ERR_TIMEOUT == "ERR_TIMEOUT"
    assert ERR_DEGRADATION == "ERR_DEGRADATION"
    assert ERR_CONFIG == "ERR_CONFIG"
    assert ERR_INTERNAL == "ERR_INTERNAL"
    assert ERR_RATE_LIMIT == "ERR_RATE_LIMIT"
    assert ERR_PERMISSION == "ERR_PERMISSION"
