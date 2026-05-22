import sys
import json
import pytest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from xuansto_mcp.tools.workflow_dispatch import (
    _save_snapshot,
    _list_snapshots,
    _load_latest_snapshot,
    _get_snapshot_dir,
)


def test_save_snapshot_creates_file(tmp_path: Path):
    import gzip
    state = {"workflow": "test", "current_phase": 2, "status": "running"}
    result = _save_snapshot("wf-001", state, str(tmp_path))
    assert result.exists()
    with gzip.open(result, 'rb') as f:
        data = json.loads(f.read().decode('utf-8'))
    assert data["workflow_id"] == "wf-001"
    assert data["phase"] == 2
    assert data["state"]["workflow"] == "test"


def test_list_snapshots_empty(tmp_path: Path):
    snapshots = _list_snapshots("wf-001", str(tmp_path))
    assert snapshots == []


def test_list_snapshots_returns_saved(tmp_path: Path):
    state = {"workflow": "test", "current_phase": 1, "status": "running"}
    _save_snapshot("wf-001", state, str(tmp_path))
    snapshots = _list_snapshots("wf-001", str(tmp_path))
    assert len(snapshots) == 1
    assert snapshots[0]["phase"] == 1


def test_load_latest_snapshot_returns_most_recent(tmp_path: Path):
    _save_snapshot("wf-001", {"current_phase": 1, "status": "running"}, str(tmp_path))
    import time; time.sleep(0.1)
    _save_snapshot("wf-001", {"current_phase": 2, "status": "running"}, str(tmp_path))
    snapshot = _load_latest_snapshot("wf-001", str(tmp_path))
    assert snapshot is not None
    assert snapshot["phase"] == 2


def test_load_latest_snapshot_with_target_phase(tmp_path: Path):
    _save_snapshot("wf-001", {"current_phase": 1, "status": "running"}, str(tmp_path))
    import time; time.sleep(0.1)
    _save_snapshot("wf-001", {"current_phase": 2, "status": "running"}, str(tmp_path))
    snapshot = _load_latest_snapshot("wf-001", str(tmp_path), target_phase=1)
    assert snapshot is not None
    assert snapshot["phase"] == 1


def test_load_latest_snapshot_no_match(tmp_path: Path):
    snapshot = _load_latest_snapshot("nonexistent", str(tmp_path))
    assert snapshot is None


@pytest.mark.asyncio
async def test_workflow_recover_action(tmp_path: Path):
    from xuansto_mcp.tools.workflow_dispatch import register
    from mcp.server.fastmcp import FastMCP

    test_mcp = FastMCP("test")
    register(test_mcp)
    tool_fn = test_mcp._tool_manager._tools["workflow_dispatch"].fn

    result = await tool_fn(action="start", workflow="sdd-tdd-fast", project_path=str(tmp_path))
    assert not result.get("error")
    workflow_id = result.get("data", result).get("workflow_id", "")

    _save_snapshot(workflow_id, {"workflow": "sdd-tdd-fast", "current_phase": 1, "status": "running"}, str(tmp_path))

    recover_result = await tool_fn(action="recover", workflow_id=workflow_id, project_path=str(tmp_path))
    assert not recover_result.get("error")
    data = recover_result.get("data", recover_result)
    assert data.get("action") == "recover"
    assert data.get("recovered_phase") == 1


@pytest.mark.asyncio
async def test_workflow_snapshots_action(tmp_path: Path):
    from xuansto_mcp.tools.workflow_dispatch import register
    from mcp.server.fastmcp import FastMCP

    test_mcp = FastMCP("test")
    register(test_mcp)
    tool_fn = test_mcp._tool_manager._tools["workflow_dispatch"].fn

    result = await tool_fn(action="start", workflow="sdd-tdd-fast", project_path=str(tmp_path))
    workflow_id = result.get("data", result).get("workflow_id", "")

    _save_snapshot(workflow_id, {"current_phase": 1}, str(tmp_path))

    snapshots_result = await tool_fn(action="snapshots", workflow_id=workflow_id, project_path=str(tmp_path))
    data = snapshots_result.get("data", snapshots_result)
    assert data.get("action") == "snapshots"
    assert data.get("total", 0) >= 1
