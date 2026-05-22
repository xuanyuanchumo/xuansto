import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from xuansto_mcp.core.validator import validate_input
from xuansto_mcp.models.schemas import SkillAnalyzeInput, WorkflowDispatchInput


def test_valid_input():
    result, err = validate_input(SkillAnalyzeInput, skill_path="/tmp")
    assert result is not None
    assert err is None
    assert result.skill_path == "/tmp"


def test_invalid_input():
    result, err = validate_input(SkillAnalyzeInput, skill_path="/tmp", unknown_field="x")
    assert result is None
    assert err is not None
    assert err["error"] is True
    assert err["code"] == "VALIDATION_ERROR"


def test_missing_required():
    result, err = validate_input(WorkflowDispatchInput)
    assert result is None
    assert err is not None
    assert err["code"] == "VALIDATION_ERROR"


def test_valid_workflow_dispatch():
    result, err = validate_input(WorkflowDispatchInput, action="start", workflow="sdd-tdd-full")
    assert result is not None
    assert err is None
    assert result.action == "start"
