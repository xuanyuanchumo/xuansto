import json
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from xuansto_mcp.tools import workflow_dispatch


def _write_workflow_file(wf_dir: Path, workflow_id: str, data: dict) -> Path:
    wf_dir.mkdir(parents=True, exist_ok=True)
    p = wf_dir / f"{workflow_id}.json"
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return p


def test_active_workflows_recovered_from_disk_on_startup(tmp_path, monkeypatch):
    monkeypatch.setattr(workflow_dispatch, "WORK_DIR", tmp_path)
    wf_dir = tmp_path / "workflows"
    wf_dir.mkdir(parents=True, exist_ok=True)

    wf_running = {
        "workflow_id": "wf-running01",
        "workflow": "sdd-tdd-full",
        "project_path": ".",
        "status": "running",
        "current_phase": 2,
        "completed_phases": [0, 1],
    }
    wf_completed = {
        "workflow_id": "wf-completed01",
        "workflow": "sdd-tdd-fast",
        "project_path": ".",
        "status": "completed",
        "current_phase": 8,
        "completed_phases": [0, 1, 2, 3, 4, 5, 6, 7],
    }
    _write_workflow_file(wf_dir, "wf-running01", wf_running)
    _write_workflow_file(wf_dir, "wf-completed01", wf_completed)

    workflow_dispatch._ACTIVE_WORKFLOWS.clear()
    with patch("xuansto_mcp.tools.workflow_dispatch.load_workflow_states", return_value=[]):
        workflow_dispatch.load_on_startup()

    assert "wf-running01" in workflow_dispatch._ACTIVE_WORKFLOWS
    assert workflow_dispatch._ACTIVE_WORKFLOWS["wf-running01"]["status"] == "running"
    assert "wf-completed01" in workflow_dispatch._ACTIVE_WORKFLOWS
    assert workflow_dispatch._ACTIVE_WORKFLOWS["wf-completed01"]["status"] == "completed"


def test_aborted_workflows_not_recovered(tmp_path, monkeypatch):
    monkeypatch.setattr(workflow_dispatch, "WORK_DIR", tmp_path)
    wf_dir = tmp_path / "workflows"
    wf_dir.mkdir(parents=True, exist_ok=True)

    wf_aborted = {
        "workflow_id": "wf-aborted01",
        "workflow": "sdd-tdd-full",
        "project_path": ".",
        "status": "aborted",
        "current_phase": 1,
    }
    wf_running = {
        "workflow_id": "wf-running02",
        "workflow": "sdd-tdd-medium",
        "project_path": ".",
        "status": "running",
        "current_phase": 3,
    }
    _write_workflow_file(wf_dir, "wf-aborted01", wf_aborted)
    _write_workflow_file(wf_dir, "wf-running02", wf_running)

    workflow_dispatch._ACTIVE_WORKFLOWS.clear()
    with patch("xuansto_mcp.tools.workflow_dispatch.load_workflow_states", return_value=[]):
        workflow_dispatch.load_on_startup()

    assert "wf-aborted01" not in workflow_dispatch._ACTIVE_WORKFLOWS
    assert "wf-running02" in workflow_dispatch._ACTIVE_WORKFLOWS


def test_corrupt_json_files_skipped_without_crashing(tmp_path, monkeypatch):
    monkeypatch.setattr(workflow_dispatch, "WORK_DIR", tmp_path)
    wf_dir = tmp_path / "workflows"
    wf_dir.mkdir(parents=True, exist_ok=True)

    corrupt_path = wf_dir / "wf-corrupt.json"
    corrupt_path.write_text("{invalid json content!!!", encoding="utf-8")

    wf_ok = {
        "workflow_id": "wf-ok01",
        "workflow": "sdd-tdd-full",
        "project_path": ".",
        "status": "running",
        "current_phase": 0,
    }
    _write_workflow_file(wf_dir, "wf-ok01", wf_ok)

    workflow_dispatch._ACTIVE_WORKFLOWS.clear()
    with patch("xuansto_mcp.tools.workflow_dispatch.load_workflow_states", return_value=[]):
        workflow_dispatch.load_on_startup()

    assert "wf-corrupt" not in workflow_dispatch._ACTIVE_WORKFLOWS
    assert "wf-ok01" in workflow_dispatch._ACTIVE_WORKFLOWS


def test_missing_directory_handled_gracefully(tmp_path, monkeypatch):
    nonexistent = tmp_path / "no_such_dir"
    monkeypatch.setattr(workflow_dispatch, "WORK_DIR", nonexistent)

    workflow_dispatch._ACTIVE_WORKFLOWS.clear()
    with patch("xuansto_mcp.tools.workflow_dispatch.load_workflow_states", return_value=[]):
        workflow_dispatch.load_on_startup()

    assert workflow_dispatch._ACTIVE_WORKFLOWS == {}
    assert (nonexistent / "workflows").exists()


def test_state_changes_persisted_to_disk(tmp_path, monkeypatch):
    monkeypatch.setattr(workflow_dispatch, "WORK_DIR", tmp_path)
    monkeypatch.setattr(workflow_dispatch, "INLINE_CHECKS", {})

    wf_dir = tmp_path / "workflows"
    wf_dir.mkdir(parents=True, exist_ok=True)

    result = workflow_dispatch._start_workflow("sdd-tdd-full", ".")
    wf_id = result["workflow_id"]

    wf_path = wf_dir / f"{wf_id}.json"
    assert wf_path.exists()
    data = json.loads(wf_path.read_text(encoding="utf-8"))
    assert data["status"] == "running"
    assert data["current_phase"] == 0

    workflow_dispatch._advance_phase(wf_id)
    data = json.loads(wf_path.read_text(encoding="utf-8"))
    assert data["current_phase"] == 1
    assert 0 in data["completed_phases"]

    workflow_dispatch._abort_workflow(wf_id)
    data = json.loads(wf_path.read_text(encoding="utf-8"))
    assert data["status"] == "aborted"
    assert "aborted_at" in data


def test_recover_action_persists_to_individual_file(tmp_path, monkeypatch):
    monkeypatch.setattr(workflow_dispatch, "WORK_DIR", tmp_path)

    wf_dir = tmp_path / "workflows"
    wf_dir.mkdir(parents=True, exist_ok=True)

    result = workflow_dispatch._start_workflow("sdd-tdd-full", str(tmp_path))
    wf_id = result["workflow_id"]

    snapshot_state = {
        "workflow": "sdd-tdd-full",
        "current_phase": 3,
        "status": "running",
        "completed_phases": [0, 1, 2],
    }
    workflow_dispatch._save_snapshot(wf_id, snapshot_state, str(tmp_path))

    from xuansto_mcp.tools.workflow_dispatch import _load_latest_snapshot
    snapshot = _load_latest_snapshot(wf_id, str(tmp_path))
    assert snapshot is not None

    state = snapshot.get("state", {})
    if wf_id in workflow_dispatch._ACTIVE_WORKFLOWS:
        workflow_dispatch._ACTIVE_WORKFLOWS[wf_id] = state.copy()
        workflow_dispatch._persist_workflow(wf_id, state.copy())
        workflow_dispatch._persist_active_workflows()

    wf_path = wf_dir / f"{wf_id}.json"
    assert wf_path.exists()
    persisted = json.loads(wf_path.read_text(encoding="utf-8"))
    assert persisted["current_phase"] == 3


def test_load_on_startup_syncs_persist_active_workflows(tmp_path, monkeypatch):
    monkeypatch.setattr(workflow_dispatch, "WORK_DIR", tmp_path)
    wf_dir = tmp_path / "workflows"
    wf_dir.mkdir(parents=True, exist_ok=True)

    wf1 = {
        "workflow_id": "wf-sync01",
        "workflow": "sdd-tdd-full",
        "project_path": ".",
        "status": "running",
        "current_phase": 1,
    }
    _write_workflow_file(wf_dir, "wf-sync01", wf1)

    workflow_dispatch._ACTIVE_WORKFLOWS.clear()
    with patch("xuansto_mcp.tools.workflow_dispatch.load_workflow_states", return_value=[]):
        workflow_dispatch.load_on_startup()

    states_path = tmp_path / "workflow_states.json"
    assert states_path.exists()
    states = json.loads(states_path.read_text(encoding="utf-8"))
    assert "wf-sync01" in states
