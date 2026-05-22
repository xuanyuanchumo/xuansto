import json
import subprocess
import sys

import pytest

from xuansto_mcp.cli import _health_check, _invoke_tool


def test_health_check_returns_healthy_status():
    result = _health_check()
    assert result["error"] is False
    assert result["data"]["status"] == "healthy"


def test_invoke_server_health():
    result = _invoke_tool("server_health", "{}")
    assert result["error"] is False
    assert result["data"]["status"] == "healthy"


def test_invoke_nonexistent_tool_returns_tool_not_found():
    result = _invoke_tool("nonexistent_tool", "{}")
    assert result["error"] is True
    assert result["code"] == "TOOL_NOT_FOUND"
    assert "nonexistent_tool" in result["message"]
    assert "available" in result.get("details", {})


def test_invoke_invalid_json_params_returns_invalid_json():
    result = _invoke_tool("server_health", "not-valid-json")
    assert result["error"] is True
    assert result["code"] == "INVALID_JSON"


def test_cli_health_subprocess():
    result = subprocess.run(
        [sys.executable, "-m", "xuansto_mcp.cli", "health"],
        capture_output=True,
        text=True,
        cwd=str(pytest.rootdir) if hasattr(pytest, "rootdir") else None,
    )
    output = json.loads(result.stdout)
    assert output["error"] is False
    assert output["data"]["status"] == "healthy"


def test_cli_invoke_subprocess():
    result = subprocess.run(
        [sys.executable, "-m", "xuansto_mcp.cli", "invoke", "server_health"],
        capture_output=True,
        text=True,
    )
    output = json.loads(result.stdout)
    assert output["error"] is False
    assert output["data"]["status"] == "healthy"


def test_cli_invoke_nonexistent_subprocess():
    result = subprocess.run(
        [sys.executable, "-m", "xuansto_mcp.cli", "invoke", "nonexistent_tool"],
        capture_output=True,
        text=True,
    )
    output = json.loads(result.stdout)
    assert output["error"] is True
    assert output["code"] == "TOOL_NOT_FOUND"


def test_cli_invoke_invalid_json_subprocess():
    result = subprocess.run(
        [sys.executable, "-m", "xuansto_mcp.cli", "invoke", "server_health", "--params", "{invalid}"],
        capture_output=True,
        text=True,
    )
    output = json.loads(result.stdout)
    assert output["error"] is True
    assert output["code"] == "INVALID_JSON"
