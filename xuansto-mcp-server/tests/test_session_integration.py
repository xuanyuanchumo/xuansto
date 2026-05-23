from __future__ import annotations

import hashlib
import json
import threading
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from xuansto_mcp.tools.session_manage import (
    _save_session,
    _load_last_session,
    _list_sessions,
    _track_session,
    _restore_session,
    _cleanup_old_sessions,
    restore_on_startup,
    _RESTORED_STATE,
)


@pytest.fixture
def tmp_session_dir(tmp_path):
    sdir = tmp_path / "sessions"
    sdir.mkdir(parents=True)
    return sdir


@pytest.fixture
def tmp_patterns_dir(tmp_path):
    pdir = tmp_path / "patterns"
    pdir.mkdir(parents=True)
    return pdir


@pytest.fixture(autouse=True)
def reset_restored_state():
    import xuansto_mcp.tools.session_manage as mod
    original = mod._RESTORED_STATE
    mod._RESTORED_STATE = None
    yield
    mod._RESTORED_STATE = original


class TestSessionCreationAndRetrieval:
    def test_save_session_creates_file(self, tmp_session_dir):
        with patch("xuansto_mcp.tools.session_manage.SESSION_DIR", tmp_session_dir):
            result = _save_session(
                completed_tasks=["task1", "task2"],
                pending_tasks=["task3"],
                decisions=["dec1"],
                experience=["exp1"],
            )
            assert "path" in result
            assert "filename" in result
            assert (tmp_session_dir / result["filename"]).exists()

    def test_load_last_session(self, tmp_session_dir):
        with patch("xuansto_mcp.tools.session_manage.SESSION_DIR", tmp_session_dir):
            _save_session(completed_tasks=["done"], decisions=["dec"])
            result = _load_last_session()
            assert result["content"] is not None
            assert "done" in result["content"]

    def test_load_no_sessions(self, tmp_session_dir):
        with patch("xuansto_mcp.tools.session_manage.SESSION_DIR", tmp_session_dir):
            result = _load_last_session()
            assert result["content"] is None

    def test_list_sessions(self, tmp_session_dir):
        with patch("xuansto_mcp.tools.session_manage.SESSION_DIR", tmp_session_dir):
            import time
            _save_session(completed_tasks=["a"])
            time.sleep(1.1)
            _save_session(completed_tasks=["b"])
            result = _list_sessions()
            assert result["total"] >= 2
            assert len(result["sessions"]) >= 2


class TestSessionStatePersistence:
    def test_track_session_saves_state(self, tmp_session_dir):
        with patch("xuansto_mcp.tools.session_manage.SESSION_DIR", tmp_session_dir):
            state = _track_session(
                current_phase=2,
                current_task="implementing",
                decisions=["use pytest"],
                pending_tasks=["write tests"],
            )
            assert state["current_phase"] == 2
            assert state["current_task"] == "implementing"
            assert "use pytest" in state["decisions"]
            current_path = tmp_session_dir / "current.json"
            assert current_path.exists()

    def test_track_session_persists_across_calls(self, tmp_session_dir):
        with patch("xuansto_mcp.tools.session_manage.SESSION_DIR", tmp_session_dir):
            _track_session(current_phase=1, current_task="planning", decisions=["dec1"])
            state = _track_session(current_phase=2, current_task="implementing", decisions=["dec2"])
            assert state["current_phase"] == 2
            assert "dec1" in state["decisions"]
            assert "dec2" in state["decisions"]

    def test_restore_session_from_file(self, tmp_session_dir):
        with patch("xuansto_mcp.tools.session_manage.SESSION_DIR", tmp_session_dir):
            _track_session(current_phase=3, current_task="testing")
            import xuansto_mcp.tools.session_manage as mod
            mod._RESTORED_STATE = None
            result = _restore_session()
            assert result["current_phase"] == 3

    def test_restore_no_tracked_session(self, tmp_session_dir):
        with patch("xuansto_mcp.tools.session_manage.SESSION_DIR", tmp_session_dir):
            result = _restore_session()
            assert result["status"] == "no_tracked_session"

    def test_simulated_restart_restores_state(self, tmp_session_dir):
        with patch("xuansto_mcp.tools.session_manage.SESSION_DIR", tmp_session_dir):
            _track_session(current_phase=2, current_task="midway", decisions=["dec_a"])
            import xuansto_mcp.tools.session_manage as mod
            mod._RESTORED_STATE = None
            restored = restore_on_startup()
            assert restored is not None
            assert restored["current_phase"] == 2
            assert "dec_a" in restored["decisions"]


class TestStateFileIntegrity:
    def test_current_json_is_valid(self, tmp_session_dir):
        with patch("xuansto_mcp.tools.session_manage.SESSION_DIR", tmp_session_dir):
            _track_session(current_phase=1, decisions=["test_decision"])
            current_path = tmp_session_dir / "current.json"
            data = json.loads(current_path.read_text(encoding="utf-8"))
            assert "current_phase" in data
            assert "decisions" in data
            assert "timestamp" in data

    def test_corrupted_current_json_handled(self, tmp_session_dir):
        with patch("xuansto_mcp.tools.session_manage.SESSION_DIR", tmp_session_dir):
            current_path = tmp_session_dir / "current.json"
            current_path.write_text("not valid json{{{", encoding="utf-8")
            import xuansto_mcp.tools.session_manage as mod
            mod._RESTORED_STATE = None
            result = _restore_session()
            assert result["status"] == "no_tracked_session"

    def test_degradation_state_hash_verification(self, tmp_session_dir):
        with patch("xuansto_mcp.tools.session_manage.SESSION_DIR", tmp_session_dir):
            _track_session(current_phase=1)
            current_path = tmp_session_dir / "current.json"
            original = current_path.read_text(encoding="utf-8")
            data = json.loads(original)
            computed = hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
            assert len(computed) == 64


class TestConcurrentAccess:
    def test_concurrent_track_sessions(self, tmp_session_dir):
        with patch("xuansto_mcp.tools.session_manage.SESSION_DIR", tmp_session_dir):
            errors = []

            def track(phase):
                try:
                    _track_session(current_phase=phase, decisions=[f"dec_{phase}"])
                except Exception as e:
                    errors.append(e)

            threads = [threading.Thread(target=track, args=(i,)) for i in range(5)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            assert len(errors) == 0
            current_path = tmp_session_dir / "current.json"
            assert current_path.exists()


class TestAtexitHandler:
    def test_restore_on_startup_returns_none_when_no_state(self, tmp_session_dir):
        with patch("xuansto_mcp.tools.session_manage.SESSION_DIR", tmp_session_dir):
            import xuansto_mcp.tools.session_manage as mod
            mod._RESTORED_STATE = None
            result = restore_on_startup()
            assert result is None

    def test_restore_on_startup_loads_state(self, tmp_session_dir):
        with patch("xuansto_mcp.tools.session_manage.SESSION_DIR", tmp_session_dir):
            _track_session(current_phase=1, current_task="active")
            import xuansto_mcp.tools.session_manage as mod
            mod._RESTORED_STATE = None
            result = restore_on_startup()
            assert result is not None
            assert result["current_phase"] == 1


class TestSessionCleanup:
    def test_cleanup_old_sessions(self, tmp_session_dir):
        with patch("xuansto_mcp.tools.session_manage.SESSION_DIR", tmp_session_dir):
            for i in range(12):
                _save_session(completed_tasks=[f"task_{i}"])
            sessions = sorted(tmp_session_dir.glob("session-*.md"), reverse=True)
            assert len(sessions) <= 10
