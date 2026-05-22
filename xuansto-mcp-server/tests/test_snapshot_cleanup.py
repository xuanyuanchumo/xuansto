import json
import os
import time
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from xuansto_mcp.tools import workflow_dispatch


def _make_snapshot_dir(tmp_path: Path) -> Path:
    snapshot_dir = tmp_path / ".xuansto" / "workflow_snapshots"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    return snapshot_dir


def _create_snapshot_file(snapshot_dir: Path, workflow_id: str, phase: int, timestamp: float, mtime: float | None = None) -> Path:
    ts_int = int(timestamp)
    filename = f"{workflow_id}_phase{phase}_{ts_int}.json"
    fpath = snapshot_dir / filename
    data = {
        "workflow_id": workflow_id,
        "phase": phase,
        "timestamp": timestamp,
        "time_iso": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(timestamp)),
        "state": {"current_phase": phase, "status": "running"},
    }
    fpath.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    if mtime is not None:
        os.utime(fpath, (mtime, mtime))
    return fpath


def test_cleanup_deletes_oldest_when_exceeding_max(tmp_path):
    snapshot_dir = _make_snapshot_dir(tmp_path)
    workflow_id = "wf-testmax"
    now = time.time()
    for i in range(25):
        _create_snapshot_file(snapshot_dir, workflow_id, i, now - (25 - i), mtime=now - (25 - i))

    result = workflow_dispatch._cleanup_snapshots(workflow_id, str(tmp_path), max_snapshots=20, ttl_days=30)

    assert result["deleted_count"] == 5
    assert result["remaining_count"] == 20
    remaining = list(snapshot_dir.glob(f"{workflow_id}_*.json"))
    assert len(remaining) == 20


def test_cleanup_deletes_expired_by_ttl(tmp_path):
    snapshot_dir = _make_snapshot_dir(tmp_path)
    workflow_id = "wf-testttl"
    now = time.time()
    old_time = now - timedelta(days=31).total_seconds()
    recent_time = now - timedelta(days=5).total_seconds()

    _create_snapshot_file(snapshot_dir, workflow_id, 1, old_time, mtime=old_time)
    _create_snapshot_file(snapshot_dir, workflow_id, 2, old_time + 10, mtime=old_time + 10)
    _create_snapshot_file(snapshot_dir, workflow_id, 3, recent_time, mtime=recent_time)

    result = workflow_dispatch._cleanup_snapshots(workflow_id, str(tmp_path), max_snapshots=20, ttl_days=30)

    assert result["deleted_count"] == 2
    assert result["remaining_count"] == 1
    remaining = list(snapshot_dir.glob(f"{workflow_id}_*.json"))
    assert len(remaining) == 1


def test_cleanup_returns_correct_statistics(tmp_path):
    snapshot_dir = _make_snapshot_dir(tmp_path)
    workflow_id = "wf-stats"
    now = time.time()
    for i in range(10):
        _create_snapshot_file(snapshot_dir, workflow_id, i, now - i, mtime=now - i)

    result = workflow_dispatch._cleanup_snapshots(workflow_id, str(tmp_path), max_snapshots=5, ttl_days=30)

    assert isinstance(result["deleted_count"], int)
    assert isinstance(result["remaining_count"], int)
    assert result["deleted_count"] == 5
    assert result["remaining_count"] == 5
    assert result["deleted_count"] + result["remaining_count"] == 10


def test_cleanup_handles_empty_directory(tmp_path):
    _make_snapshot_dir(tmp_path)
    workflow_id = "wf-empty"

    result = workflow_dispatch._cleanup_snapshots(workflow_id, str(tmp_path), max_snapshots=20, ttl_days=30)

    assert result["deleted_count"] == 0
    assert result["remaining_count"] == 0


def test_cleanup_handles_missing_directory(tmp_path):
    nonexistent = tmp_path / "no_such_project"
    workflow_id = "wf-missing"

    result = workflow_dispatch._cleanup_snapshots(workflow_id, str(nonexistent), max_snapshots=20, ttl_days=30)

    assert result["deleted_count"] == 0
    assert result["remaining_count"] == 0


def test_cleanup_only_affects_target_workflow(tmp_path):
    snapshot_dir = _make_snapshot_dir(tmp_path)
    wf_a = "wf-alpha"
    wf_b = "wf-beta"
    now = time.time()
    for i in range(5):
        _create_snapshot_file(snapshot_dir, wf_a, i, now - i, mtime=now - i)
    for i in range(5):
        _create_snapshot_file(snapshot_dir, wf_b, i, now - i, mtime=now - i)

    workflow_dispatch._cleanup_snapshots(wf_a, str(tmp_path), max_snapshots=2, ttl_days=30)

    remaining_a = list(snapshot_dir.glob(f"{wf_a}_*.json"))
    remaining_b = list(snapshot_dir.glob(f"{wf_b}_*.json"))
    assert len(remaining_a) == 2
    assert len(remaining_b) == 5


def test_cleanup_both_ttl_and_max_apply(tmp_path):
    snapshot_dir = _make_snapshot_dir(tmp_path)
    workflow_id = "wf-both"
    now = time.time()
    old_time = now - timedelta(days=35).total_seconds()
    for i in range(3):
        _create_snapshot_file(snapshot_dir, workflow_id, i, old_time + i, mtime=old_time + i)
    for i in range(10):
        _create_snapshot_file(snapshot_dir, workflow_id, i + 3, now - i, mtime=now - i)

    result = workflow_dispatch._cleanup_snapshots(workflow_id, str(tmp_path), max_snapshots=5, ttl_days=30)

    assert result["deleted_count"] == 3 + 5
    assert result["remaining_count"] == 5


def test_cleanup_all_snapshots_iterates_active_workflows(tmp_path):
    snapshot_dir = _make_snapshot_dir(tmp_path)
    wf_a = "wf-all-a"
    wf_b = "wf-all-b"
    now = time.time()

    workflow_dispatch._ACTIVE_WORKFLOWS[wf_a] = {"workflow_id": wf_a, "project_path": str(tmp_path), "status": "running"}
    workflow_dispatch._ACTIVE_WORKFLOWS[wf_b] = {"workflow_id": wf_b, "project_path": str(tmp_path), "status": "running"}

    for i in range(25):
        _create_snapshot_file(snapshot_dir, wf_a, i, now - i, mtime=now - i)
    for i in range(3):
        _create_snapshot_file(snapshot_dir, wf_b, i, now - i, mtime=now - i)

    results = workflow_dispatch._cleanup_all_snapshots()

    assert wf_a in results
    assert wf_b in results
    assert results[wf_a]["deleted_count"] == 5
    assert results[wf_a]["remaining_count"] == 20
    assert results[wf_b]["deleted_count"] == 0
    assert results[wf_b]["remaining_count"] == 3

    workflow_dispatch._ACTIVE_WORKFLOWS.pop(wf_a, None)
    workflow_dispatch._ACTIVE_WORKFLOWS.pop(wf_b, None)


def test_save_snapshot_triggers_cleanup(tmp_path):
    snapshot_dir = _make_snapshot_dir(tmp_path)
    workflow_id = "wf-autoclean"
    now = time.time()
    state = {"current_phase": 0, "status": "running"}

    with patch.object(workflow_dispatch, "_cleanup_snapshots", return_value={"deleted_count": 0, "remaining_count": 1}) as mock_cleanup:
        workflow_dispatch._save_snapshot(workflow_id, state, str(tmp_path))
        mock_cleanup.assert_called_once_with(workflow_id, str(tmp_path))


def test_get_snapshot_cleanup_config_defaults():
    workflow_dispatch._SNAPSHOT_CLEANUP_CONFIG.clear()
    config = workflow_dispatch._get_snapshot_cleanup_config()
    assert config["max_snapshots_per_workflow"] == 20
    assert config["snapshot_ttl_days"] == 30
    workflow_dispatch._SNAPSHOT_CLEANUP_CONFIG.clear()
