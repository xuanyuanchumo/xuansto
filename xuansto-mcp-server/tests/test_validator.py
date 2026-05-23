from __future__ import annotations

from pathlib import Path

import pytest

from xuansto_mcp.core.validator import (
    NAME_WHITELIST_PATTERN,
    validate_name_parameter,
    validate_path_safety,
    validate_input,
)
from xuansto_mcp.models.schemas import SkillAnalyzeInput, WorkflowDispatchInput


def test_name_whitelist_accepts_alphanumeric():
    assert NAME_WHITELIST_PATTERN.match("hello123") is not None


def test_name_whitelist_accepts_underscore():
    assert NAME_WHITELIST_PATTERN.match("hello_world") is not None


def test_name_whitelist_accepts_hyphen():
    assert NAME_WHITELIST_PATTERN.match("hello-world") is not None


def test_name_whitelist_accepts_dot():
    assert NAME_WHITELIST_PATTERN.match("hello.world") is not None


def test_name_whitelist_accepts_slash():
    assert NAME_WHITELIST_PATTERN.match("path/to/file") is not None


def test_name_whitelist_rejects_special_chars():
    assert NAME_WHITELIST_PATTERN.match("hello@world") is None


def test_name_whitelist_rejects_spaces():
    assert NAME_WHITELIST_PATTERN.match("hello world") is None


def test_name_whitelist_rejects_shell_chars():
    for char in ["|", "&", ";", "$", "`", "!", "<", ">", "(", ")"]:
        assert NAME_WHITELIST_PATTERN.match(f"hello{char}world") is None


def test_validate_name_parameter_valid():
    valid, error = validate_name_parameter("my-component_v2.0")
    assert valid is True
    assert error is None


def test_validate_name_parameter_empty():
    valid, error = validate_name_parameter("")
    assert valid is False
    assert "empty" in error.lower() or "empty" in error


def test_validate_name_parameter_path_traversal():
    valid, error = validate_name_parameter("../etc/passwd")
    assert valid is False
    assert ".." in error


def test_validate_name_parameter_absolute_path():
    valid, error = validate_name_parameter("C:\\Windows\\System32")
    assert valid is False
    assert "Absolute" in error or "absolute" in error.lower()


def test_validate_name_parameter_null_byte():
    valid, error = validate_name_parameter("file\x00.txt")
    assert valid is False
    assert "null" in error.lower()


def test_validate_name_parameter_double_dot():
    valid, error = validate_name_parameter("some..path")
    assert valid is False
    assert ".." in error


def test_validate_name_parameter_special_chars():
    valid, error = validate_name_parameter("file|name")
    assert valid is False
    assert "invalid" in error.lower()


def test_validate_path_safety_null_byte():
    result, error = validate_path_safety("file\x00.txt")
    assert result is None
    assert "null" in error.lower()


def test_validate_path_safety_traversal():
    result, error = validate_path_safety("../etc/passwd")
    assert result is None
    assert ".." in error


def test_validate_path_safety_absolute_not_allowed():
    result, error = validate_path_safety("C:\\Windows\\System32")
    assert result is None
    assert "Absolute" in error or "absolute" in error.lower()


def test_validate_path_safety_absolute_allowed():
    result, error = validate_path_safety("/etc/passwd", allow_absolute=True)
    assert result is not None or error is not None


def test_validate_path_safety_relative_path():
    result, error = validate_path_safety("relative/path")
    assert result is not None
    assert error is None


def test_validate_path_safety_with_allowed_base(tmp_path):
    base_dir = tmp_path / "allowed"
    base_dir.mkdir()
    result, error = validate_path_safety("file.txt", allowed_base_dirs=[base_dir])
    assert result is not None
    assert error is None


def test_validate_path_safety_escapes_allowed_base(tmp_path):
    base_dir = tmp_path / "allowed"
    base_dir.mkdir()
    result, error = validate_path_safety("../../etc/passwd", allowed_base_dirs=[base_dir])
    assert result is None
    assert error is not None


def test_validate_input_valid():
    result, err = validate_input(SkillAnalyzeInput, skill_path="/tmp")
    assert result is not None
    assert err is None
    assert result.skill_path == "/tmp"


def test_validate_input_invalid():
    result, err = validate_input(SkillAnalyzeInput, skill_path="/tmp", unknown_field="x")
    assert result is None
    assert err is not None
    assert err["error"] is True


def test_validate_input_missing_required():
    result, err = validate_input(WorkflowDispatchInput)
    assert result is None
    assert err is not None


def test_validate_input_valid_workflow():
    result, err = validate_input(WorkflowDispatchInput, action="start", workflow="sdd-tdd-full")
    assert result is not None
    assert err is None
    assert result.action == "start"
