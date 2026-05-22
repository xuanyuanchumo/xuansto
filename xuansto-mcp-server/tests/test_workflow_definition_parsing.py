import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from xuansto_mcp.tools import workflow_dispatch


def test_parse_workflow_definition_returns_correct_data_for_full():
    result = workflow_dispatch._parse_workflow_definition("sdd-tdd-full")
    assert result is not None
    assert result["name"] == "sdd-tdd-full"
    assert "phases" in result
    phases = result["phases"]
    assert len(phases) == 9
    phase0 = phases[0]
    assert phase0["id"] == 0
    assert phase0["name"] == "初始化"
    assert "DESIGN-SYSTEM-COMPLETE" in phase0["gates"]
    assert "design-reviewer" in phase0["agents"]
    phase3 = phases[3]
    assert phase3["id"] == 3
    assert phase3["name"] == "测试先行"
    assert "TEST-FIRST" in phase3["gates"]
    phase8 = phases[8]
    assert phase8["id"] == 8
    assert phase8["name"] == "桌面发布"
    assert "DESKTOP-BUILD" in phase8["gates"]


def test_parse_workflow_definition_returns_none_for_nonexistent():
    result = workflow_dispatch._parse_workflow_definition("nonexistent-workflow")
    assert result is None


def test_start_workflow_stores_phase_definitions():
    started = workflow_dispatch._start_workflow("sdd-tdd-full", ".")
    wf_id = started["workflow_id"]
    assert "phase_definitions" in started
    phase_defs = started["phase_definitions"]
    assert len(phase_defs) == 9
    assert phase_defs[0]["name"] == "初始化"
    assert "DESIGN-SYSTEM-COMPLETE" in phase_defs[0]["gates"]
    loaded = workflow_dispatch._load_workflow(wf_id)
    assert loaded is not None
    assert "phase_definitions" in loaded
    assert loaded["phase_definitions"][0]["gates"] == phase_defs[0]["gates"]


def test_advance_phase_uses_phase_definitions_gates():
    started = workflow_dispatch._start_workflow("sdd-tdd-fast", ".")
    wf_id = started["workflow_id"]
    phase_defs = started["phase_definitions"]
    phase0_gates = phase_defs[0]["gates"]
    assert "DESIGN-SYSTEM-COMPLETE" in phase0_gates
    assert "TEST-FIRST" in phase0_gates
    with patch("xuansto_mcp.tools.workflow_dispatch.INLINE_CHECKS", {}):
        result = workflow_dispatch._advance_phase(wf_id)
    gates_checked = result.get("gates_checked", [])
    checked_ids = [g["gate_id"] for g in gates_checked]
    for gate_id in phase0_gates:
        assert gate_id in checked_ids


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
