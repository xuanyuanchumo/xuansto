from __future__ import annotations

import pytest

from xuansto_mcp.core.errors import (
    ErrorCodes,
    XuanstoMCPError,
    make_response,
    make_success_response,
    make_error_response,
)


class TestMakeResponse:
    def test_success_path_with_data(self):
        result = make_response(data={"foo": "bar"})
        assert result == {"error": False, "data": {"foo": "bar"}}

    def test_success_path_no_data(self):
        result = make_response()
        assert result == {"error": False, "data": None}

    def test_success_path_data_is_none(self):
        result = make_response(data=None)
        assert result["error"] is False
        assert result["data"] is None

    def test_success_path_data_is_list(self):
        result = make_response(data=[1, 2, 3])
        assert result == {"error": False, "data": [1, 2, 3]}

    def test_error_path_basic(self):
        result = make_response(error=True, error_code="SOME_CODE", message="boom")
        assert result["error"] is True
        assert result["error_code"] == "SOME_CODE"
        assert result["message"] == "boom"
        assert result["data"] is None

    def test_error_path_empty_code_and_message(self):
        result = make_response(error=True)
        assert result["error"] is True
        assert result["error_code"] == ""
        assert result["message"] == ""
        assert result["data"] is None

    def test_error_path_has_exactly_four_keys(self):
        result = make_response(error=True, error_code="X", message="y")
        assert set(result.keys()) == {"error", "error_code", "message", "data"}

    def test_success_path_has_exactly_two_keys(self):
        result = make_response(data="hello")
        assert set(result.keys()) == {"error", "data"}


class TestErrorCodes:
    @pytest.mark.parametrize(
        "attr,value",
        [
            ("TOOL_NOT_FOUND", "TOOL_NOT_FOUND"),
            ("INVALID_PARAMS", "INVALID_PARAMS"),
            ("EXECUTION_FAILED", "EXECUTION_FAILED"),
            ("RATE_LIMITED", "RATE_LIMITED"),
            ("BLOCKED_BY_HOOK", "BLOCKED_BY_HOOK"),
            ("SECURITY_VIOLATION", "SECURITY_VIOLATION"),
            ("DEGRADED", "DEGRADED"),
            ("TIMEOUT", "TIMEOUT"),
            ("NOT_FOUND", "NOT_FOUND"),
            ("INTERNAL_ERROR", "INTERNAL_ERROR"),
        ],
    )
    def test_constant_exists(self, attr, value):
        assert getattr(ErrorCodes, attr) == value

    def test_all_constants_count(self):
        expected = {
            "TOOL_NOT_FOUND", "INVALID_PARAMS", "EXECUTION_FAILED",
            "RATE_LIMITED", "BLOCKED_BY_HOOK", "SECURITY_VIOLATION",
            "DEGRADED", "TIMEOUT", "NOT_FOUND", "INTERNAL_ERROR",
        }
        actual = {
            attr for attr in dir(ErrorCodes)
            if not attr.startswith("_")
        }
        assert actual == expected


class TestMakeSuccessResponseBackwardCompat:
    def test_basic_success(self):
        result = make_success_response(data={"key": "val"})
        assert result["error"] is False
        assert result["data"] == {"key": "val"}

    def test_no_data(self):
        result = make_success_response()
        assert result["error"] is False
        assert "data" not in result

    def test_has_api_version(self):
        result = make_success_response(data=42)
        assert "api_version" in result

    def test_degradation_level(self):
        result = make_success_response(data="ok", degradation_level="L2")
        assert result["degradation_level"] == "L2"
        assert result["degraded"] is True


class TestMakeErrorResponseBackwardCompat:
    def test_xuansto_mcp_error(self):
        err = XuanstoMCPError(code="VALIDATION_ERROR", message="bad input")
        result = make_error_response(err)
        assert result["error"] is True
        assert "error_code" in result
        assert result["message"] == "bad input"

    def test_generic_value_error(self):
        result = make_error_response(ValueError("bad"))
        assert result["error"] is True
        assert result["message"] == "bad"

    def test_has_retryable_field(self):
        err = XuanstoMCPError(code="VALIDATION_ERROR", message="bad")
        result = make_error_response(err)
        assert "retryable" in result


class TestDoubleWrapProtection:
    def test_make_response_wraps_dict_with_error_key(self):
        inner = {"error": False, "data": "hello"}
        result = make_response(data=inner)
        assert result["error"] is False
        assert result["data"] == inner

    def test_make_response_does_not_unwrap_nested(self):
        inner = {"error": True, "error_code": "X", "message": "m", "data": None}
        result = make_response(data=inner)
        assert result["error"] is False
        assert result["data"] == inner
