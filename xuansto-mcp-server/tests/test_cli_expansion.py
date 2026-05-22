import json
import subprocess
import sys

import pytest

from xuansto_mcp.cli import _invoke_tool


def test_cli_version_returns_version_json():
    result = subprocess.run(
        [sys.executable, "-m", "xuansto_mcp.cli", "version"],
        capture_output=True,
        text=True,
    )
    output = json.loads(result.stdout)
    assert "version" in output
    assert isinstance(output["version"], str)
    assert len(output["version"]) > 0


def test_cli_config_returns_config_json():
    result = subprocess.run(
        [sys.executable, "-m", "xuansto_mcp.cli", "config"],
        capture_output=True,
        text=True,
    )
    output = json.loads(result.stdout)
    assert "data_dir" in output
    assert "skill_root" in output
    assert "work_dir" in output
    assert "data_dir_exists" in output
    assert "skill_root_exists" in output
    assert "work_dir_exists" in output
    assert isinstance(output["data_dir_exists"], bool)
    assert isinstance(output["skill_root_exists"], bool)
    assert isinstance(output["work_dir_exists"], bool)


def test_cli_gate_invokes_quality_gate_check():
    result = _invoke_tool(
        "quality_gate_check",
        json.dumps({"gate_ids": ["GATE-007"], "project_path": "."}),
    )
    assert "error" in result
    if not result.get("error"):
        assert "data" in result or "results" in result or "gate_ids" in result
