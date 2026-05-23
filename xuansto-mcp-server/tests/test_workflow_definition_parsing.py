import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from xuansto_mcp.tools import workflow_dispatch


def test_parse_workflow_definition_returns_correct_data_for_full():
    result = workflow_dispatch._parse_workflow_definition("sdd-tdd-full")
    assert result is not None
    assert "phases" in result
    phases = result["phases"]
    assert len(phases) >= 1
    phase0 = phases[0]
    assert "id" in phase0 or "name" in phase0


def test_parse_workflow_definition_returns_none_for_nonexistent():
    result = workflow_dispatch._parse_workflow_definition("nonexistent-workflow")
    assert result is None


def test_start_workflow_stores_phase_definitions():
    started = workflow_dispatch._start_workflow("sdd-tdd-full", ".")
    wf_id = started["workflow_id"]
    assert "phase_definitions" in started
    phase_defs = started["phase_definitions"]
    assert len(phase_defs) >= 1
    loaded = workflow_dispatch._load_workflow(wf_id)
    assert loaded is not None
    assert "phase_definitions" in loaded


def test_advance_phase_uses_phase_definitions():
    started = workflow_dispatch._start_workflow("sdd-tdd-full", ".")
    wf_id = started["workflow_id"]
    phase_defs = started["phase_definitions"]
    assert len(phase_defs) >= 1
    with patch("xuansto_mcp.tools.workflow_dispatch.INLINE_CHECKS", {}):
        result = workflow_dispatch._advance_phase(wf_id)
    assert result is not None


def test_advance_phase_falls_back_to_global_map_without_definitions():
    started = workflow_dispatch._start_workflow("sdd-tdd-full", ".")
    wf_id = started["workflow_id"]
    loaded = workflow_dispatch._load_workflow(wf_id)
    if "phase_definitions" in loaded:
        del loaded["phase_definitions"]
    workflow_dispatch._persist_workflow(wf_id, loaded)
    workflow_dispatch._ACTIVE_WORKFLOWS.pop(wf_id, None)
    with patch("xuansto_mcp.tools.workflow_dispatch.INLINE_CHECKS", {}):
        result = workflow_dispatch._advance_phase(wf_id)
    assert result.get("advanced") is True or result.get("gates_checked") is not None
