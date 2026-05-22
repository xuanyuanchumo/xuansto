from __future__ import annotations

import json
import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from xuansto_mcp.tools.workflow_dispatch import (
    _advance_phase,
    _load_workflow,
    _persist_workflow,
    _ACTIVE_WORKFLOWS,
)
from xuansto_mcp.core.config import QUALITY_GATES_PHASE_MAP


@pytest.fixture(autouse=True)
def _clear_active_workflows():
    _ACTIVE_WORKFLOWS.clear()
    yield
    _ACTIVE_WORKFLOWS.clear()


@pytest.fixture
def tmp_project(tmp_path):
    return tmp_path


@pytest.fixture
def tmp_workflows_dir(tmp_path):
    wf_dir = tmp_path / ".xuansto" / "workflows"
    wf_dir.mkdir(parents=True, exist_ok=True)
    return wf_dir


def _create_workflow(workflow_id: str, project_path: str, workflows_dir: Path, phase: int = 0):
    entry = {
        "workflow_id": workflow_id,
        "workflow": "sdd-tdd-full",
        "project_path": project_path,
        "status": "running",
        "current_phase": phase,
        "started_at": "2026-01-01T00:00:00",
        "completed_phases": [],
    }
    wf_file = workflows_dir / f"{workflow_id}.json"
    wf_file.write_text(json.dumps(entry, ensure_ascii=False), encoding="utf-8")
    return workflow_id


class TestAdvancePhaseGateChecking:
    def test_gates_are_actually_checked_not_auto_passed(self, tmp_project, tmp_workflows_dir):
        wid = _create_workflow("wf-test1", str(tmp_project), tmp_workflows_dir, phase=0)
        with patch("xuansto_mcp.tools.workflow_dispatch._get_workflows_dir", return_value=tmp_workflows_dir):
            result = _advance_phase(wid)
        gates_checked = result.get("gates_checked", [])
        assert len(gates_checked) > 0, "Phase 0 should have gates"
        for gate in gates_checked:
            assert gate["status"] != "auto_passed", (
                f"Gate {gate['gate_id']} should not be auto_passed, got status: {gate['status']}"
            )
            assert "source" in gate or "message" in gate, (
                f"Gate {gate['gate_id']} should have source or message field"
            )

    def test_gates_fail_phase_does_not_advance(self, tmp_project, tmp_workflows_dir):
        wid = _create_workflow("wf-test2", str(tmp_project), tmp_workflows_dir, phase=0)
        with patch("xuansto_mcp.tools.workflow_dispatch._get_workflows_dir", return_value=tmp_workflows_dir):
            result = _advance_phase(wid)
        assert result["advanced"] is False, "Phase should NOT advance when gates fail"
        assert result["gates_passed"] is False, "gates_passed should be False"
        assert result["current_phase"] == 0, "Phase should remain at 0"
        assert "failed_gates" in result, "Should include failed_gates"
        assert len(result["failed_gates"]) > 0, "Should have at least one failed gate"
        with patch("xuansto_mcp.tools.workflow_dispatch._get_workflows_dir", return_value=tmp_workflows_dir):
            state = _load_workflow(wid)
        assert state["current_phase"] == 0, "Persisted state should still be at phase 0"

    def test_gates_pass_phase_advances(self, tmp_project, tmp_workflows_dir):
        (tmp_project / "tailwind.config.js").write_text("export default {}", encoding="utf-8")
        docs_dir = tmp_project / "docs"
        docs_dir.mkdir(exist_ok=True)
        (docs_dir / "product-review.md").write_text("# Product Review\nApproved.", encoding="utf-8")
        (docs_dir / "tech-review.md").write_text("# Tech Review\nApproved.", encoding="utf-8")
        (docs_dir / "design-review.md").write_text("# Design Review\nApproved.", encoding="utf-8")
        src_dir = tmp_project / "src"
        src_dir.mkdir(exist_ok=True)
        (src_dir / "app.py").write_text("def main():\n    pass\n", encoding="utf-8")
        wid = _create_workflow("wf-test3", str(tmp_project), tmp_workflows_dir, phase=0)
        with patch("xuansto_mcp.tools.workflow_dispatch._get_workflows_dir", return_value=tmp_workflows_dir):
            result = _advance_phase(wid)
        assert result["advanced"] is True, f"Phase should advance when gates pass. Result: {result}"
        assert result["gates_passed"] is True, "gates_passed should be True"
        assert result["new_phase"] == 1, "Phase should advance to 1"
        assert result["previous_phase"] == 0, "Previous phase should be 0"
        with patch("xuansto_mcp.tools.workflow_dispatch._get_workflows_dir", return_value=tmp_workflows_dir):
            state = _load_workflow(wid)
        assert state["current_phase"] == 1, "Persisted state should be at phase 1"
        assert 0 in state["completed_phases"], "Phase 0 should be in completed_phases"

    def test_gate_without_inline_check_gets_skip(self, tmp_workflows_dir, tmp_project):
        phase_with_unknown_gate = "99"
        original_map = QUALITY_GATES_PHASE_MAP.copy()
        QUALITY_GATES_PHASE_MAP[phase_with_unknown_gate] = ["NONEXISTENT-GATE-XYZ"]
        try:
            wid = _create_workflow("wf-test4", str(tmp_project), tmp_workflows_dir, phase=99)
            with patch("xuansto_mcp.tools.workflow_dispatch._get_workflows_dir", return_value=tmp_workflows_dir):
                result = _advance_phase(wid)
            gates_checked = result.get("gates_checked", [])
            assert len(gates_checked) == 1
            assert gates_checked[0]["status"] == "SKIP"
            assert gates_checked[0]["gate_id"] == "NONEXISTENT-GATE-XYZ"
            assert result["advanced"] is True, "Phase should advance when all gates are SKIP (no failures)"
        finally:
            del QUALITY_GATES_PHASE_MAP[phase_with_unknown_gate]

    def test_inline_check_exception_treated_as_failure(self, tmp_workflows_dir, tmp_project):
        from xuansto_mcp.tools import quality_gate_check
        original = quality_gate_check.INLINE_CHECKS.get("DESIGN-SYSTEM-COMPLETE")
        def _boom(project_path: str):
            raise RuntimeError("check exploded")
        quality_gate_check.INLINE_CHECKS["DESIGN-SYSTEM-COMPLETE"] = _boom
        try:
            wid = _create_workflow("wf-test5", str(tmp_project), tmp_workflows_dir, phase=0)
            with patch("xuansto_mcp.tools.workflow_dispatch._get_workflows_dir", return_value=tmp_workflows_dir):
                result = _advance_phase(wid)
            assert result["advanced"] is False, "Phase should NOT advance when inline check throws"
            error_gates = [g for g in result["gates_checked"] if g["status"] == "ERROR"]
            assert len(error_gates) > 0, "Should have at least one ERROR gate"
            assert "check exploded" in error_gates[0]["message"]
        finally:
            if original:
                quality_gate_check.INLINE_CHECKS["DESIGN-SYSTEM-COMPLETE"] = original
            else:
                del quality_gate_check.INLINE_CHECKS["DESIGN-SYSTEM-COMPLETE"]

    def test_advance_nonexistent_workflow(self, tmp_workflows_dir):
        with patch("xuansto_mcp.tools.workflow_dispatch._get_workflows_dir", return_value=tmp_workflows_dir):
            result = _advance_phase("wf-nonexistent")
        assert result.get("error") is True
        assert result.get("code") == "WORKFLOW_NOT_FOUND"
