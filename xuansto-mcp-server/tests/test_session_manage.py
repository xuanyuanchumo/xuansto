import json
from pathlib import Path
from unittest.mock import patch

import pytest

from xuansto_mcp.tools.session_manage import _track_session, _restore_session


@pytest.fixture
def session_dir(tmp_path: Path):
    with patch("xuansto_mcp.tools.session_manage.SESSION_DIR", tmp_path):
        yield tmp_path


def test_track_creates_current_json(session_dir: Path):
    result = _track_session(
        current_phase=1,
        current_task="implement feature",
        decisions=["use pytest"],
        pending_tasks=["write tests"],
    )

    current_path = session_dir / "current.json"
    assert current_path.exists()

    data = json.loads(current_path.read_text(encoding="utf-8"))
    assert data["current_phase"] == 1
    assert data["current_task"] == "implement feature"
    assert "use pytest" in data["decisions"]
    assert "write tests" in data["pending_tasks"]
    assert "timestamp" in data
    assert "updated_at" in data

    assert result["current_phase"] == 1
    assert result["current_task"] == "implement feature"


def test_track_appends_decisions(session_dir: Path):
    _track_session(
        current_phase=1,
        current_task="task1",
        decisions=["decision1"],
        pending_tasks=["task_a"],
    )

    result = _track_session(
        current_phase=2,
        current_task="task2",
        decisions=["decision2"],
        pending_tasks=["task_b"],
    )

    current_path = session_dir / "current.json"
    data = json.loads(current_path.read_text(encoding="utf-8"))

    assert "decision1" in data["decisions"]
    assert "decision2" in data["decisions"]
    assert data["pending_tasks"] == ["task_b"]
    assert 1 in data["completed_phases"]
    assert data["current_phase"] == 2


def test_restore_reads_current_json(session_dir: Path):
    _track_session(
        current_phase=3,
        current_task="review code",
        decisions=["approve PR"],
        pending_tasks=["deploy"],
    )

    result = _restore_session()

    assert result["current_phase"] == 3
    assert result["current_task"] == "review code"
    assert "approve PR" in result["decisions"]
    assert "deploy" in result["pending_tasks"]
    assert result["last_session"] is None


def test_restore_returns_no_tracked_session_when_missing(session_dir: Path):
    result = _restore_session()

    assert result["status"] == "no_tracked_session"
    assert result["message"] == "无追踪状态"
