import json
import sys
from pathlib import Path
from unittest.mock import patch

SKILL_PATH = Path(__file__).resolve().parent.parent.parent / ".trae" / "skills" / "xuansto-skill"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from xuansto_mcp.tools import workflow_dispatch
from mcp.server.fastmcp import FastMCP


def _mock_inline_pass(project_path: str) -> dict:
    return {"status": "PASS", "message": "mocked pass"}


def test_register():
    mcp = FastMCP("test")
    workflow_dispatch.register(mcp)
    tools = mcp._tool_manager._tools
    assert "workflow_dispatch" in tools


def test_start_workflow():
    result = workflow_dispatch._start_workflow("sdd-tdd-full", ".")
    assert "workflow_id" in result
    assert result["status"] == "running"
    assert result["current_phase"] == 0


def test_start_nonexistent_workflow():
    result = workflow_dispatch._start_workflow("nonexistent-workflow", ".")
    assert result.get("error") is True
    assert result.get("code") == "WORKFLOW_NOT_FOUND"


def test_abort_workflow():
    started = workflow_dispatch._start_workflow("sdd-tdd-full", ".")
    wf_id = started["workflow_id"]
    result = workflow_dispatch._abort_workflow(wf_id)
    assert result["status"] == "aborted"


def test_abort_nonexistent_workflow():
    result = workflow_dispatch._abort_workflow("wf-nonexistent")
    assert result.get("error") is True


def test_persist_workflow_creates_json_file():
    started = workflow_dispatch._start_workflow("sdd-tdd-full", ".")
    wf_id = started["workflow_id"]
    workflows_dir = workflow_dispatch._get_workflows_dir()
    json_path = workflows_dir / f"{wf_id}.json"
    assert json_path.exists()
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["workflow_id"] == wf_id
    assert data["status"] == "running"


def test_load_workflow_from_file():
    started = workflow_dispatch._start_workflow("sdd-tdd-full", ".")
    wf_id = started["workflow_id"]
    loaded = workflow_dispatch._load_workflow(wf_id)
    assert loaded is not None
    assert loaded["workflow_id"] == wf_id
    assert loaded["status"] == "running"


def test_load_workflow_returns_none_for_missing():
    loaded = workflow_dispatch._load_workflow("wf-doesnotexist")
    assert loaded is None


def test_reload_from_file_after_memory_clear():
    started = workflow_dispatch._start_workflow("sdd-tdd-full", ".")
    wf_id = started["workflow_id"]
    workflow_dispatch._ACTIVE_WORKFLOWS.clear()
    assert wf_id not in workflow_dispatch._ACTIVE_WORKFLOWS
    result = workflow_dispatch._get_workflow_status(wf_id)
    assert result.get("error") is not True
    assert result["workflow_id"] == wf_id
    assert result["status"] == "running"
    assert wf_id in workflow_dispatch._ACTIVE_WORKFLOWS


def test_load_all_workflows():
    wf1 = workflow_dispatch._start_workflow("sdd-tdd-full", ".")
    wf2 = workflow_dispatch._start_workflow("sdd-tdd-full", ".")
    all_wf = workflow_dispatch._load_all_workflows()
    assert wf1["workflow_id"] in all_wf
    assert wf2["workflow_id"] in all_wf


def test_abort_persists_to_file():
    started = workflow_dispatch._start_workflow("sdd-tdd-full", ".")
    wf_id = started["workflow_id"]
    workflow_dispatch._abort_workflow(wf_id)
    loaded = workflow_dispatch._load_workflow(wf_id)
    assert loaded is not None
    assert loaded["status"] == "aborted"
    assert "aborted_at" in loaded


def test_abort_reloads_from_file():
    started = workflow_dispatch._start_workflow("sdd-tdd-full", ".")
    wf_id = started["workflow_id"]
    workflow_dispatch._ACTIVE_WORKFLOWS.clear()
    result = workflow_dispatch._abort_workflow(wf_id)
    assert result["status"] == "aborted"
    loaded = workflow_dispatch._load_workflow(wf_id)
    assert loaded["status"] == "aborted"


@patch("xuansto_mcp.tools.workflow_dispatch.INLINE_CHECKS", {})
def test_phase_advance_increments_phase_no_gates():
    started = workflow_dispatch._start_workflow("sdd-tdd-full", ".")
    wf_id = started["workflow_id"]
    assert started["current_phase"] == 0
    result = workflow_dispatch._advance_phase(wf_id)
    assert result["advanced"] is True
    assert result["previous_phase"] == 0
    assert result["new_phase"] == 1
    assert result["gates_passed"] is True


@patch("xuansto_mcp.tools.workflow_dispatch.INLINE_CHECKS", {})
def test_phase_advance_persists_to_file():
    started = workflow_dispatch._start_workflow("sdd-tdd-full", ".")
    wf_id = started["workflow_id"]
    workflow_dispatch._advance_phase(wf_id)
    loaded = workflow_dispatch._load_workflow(wf_id)
    assert loaded is not None
    assert loaded["current_phase"] == 1
    assert 0 in loaded["completed_phases"]


def test_phase_current_returns_current_state():
    started = workflow_dispatch._start_workflow("sdd-tdd-full", ".")
    wf_id = started["workflow_id"]
    result = workflow_dispatch._current_phase(wf_id)
    assert result["current_phase"] == 0
    assert result["phase_name"] == "初始化"
    assert result["remaining_phases"] == 8
    assert result["status"] == "running"


def test_phase_advance_nonexistent_workflow_returns_error():
    result = workflow_dispatch._advance_phase("wf-nonexistent")
    assert result.get("error") is True
    assert result.get("code") == "WORKFLOW_NOT_FOUND"
