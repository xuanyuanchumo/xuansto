import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))


@pytest.fixture
def tmp_db(tmp_path, monkeypatch):
    from xuansto_mcp.core import database, config
    monkeypatch.setattr(database, "WORK_DIR", tmp_path)
    monkeypatch.setattr(config, "WORK_DIR", tmp_path)
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "xuansto.db")
    database.init_db()
    yield tmp_path


class TestSaveToSQLite:
    def test_save_writes_to_sqlite(self, tmp_db, monkeypatch):
        from xuansto_mcp.tools import session_manage
        from xuansto_mcp.core.database import load_state

        monkeypatch.setattr(session_manage, "SESSION_DIR", tmp_db)

        result = session_manage._save_session(
            completed_tasks=["task1", "task2"],
            pending_tasks=["task3"],
            decisions=["use sqlite"],
            experience=["test first"],
        )

        assert result["persisted_to"] == "sqlite"
        assert "session_id" in result

        rows = load_state("session_states")
        assert len(rows) >= 1
        saved = rows[-1]
        data = saved.get("session_data_json", {})
        if isinstance(data, str):
            data = json.loads(data)
        assert "task1" in data["completed_tasks"]
        assert "use sqlite" in data["decisions"]

    def test_save_no_file_by_default(self, tmp_db, monkeypatch):
        from xuansto_mcp.tools import session_manage

        monkeypatch.setattr(session_manage, "SESSION_DIR", tmp_db)

        result = session_manage._save_session(
            completed_tasks=["task1"],
        )

        assert result["persisted_to"] == "sqlite"
        assert "path" not in result
        session_files = list(tmp_db.glob("session-*.md"))
        assert len(session_files) == 0

    def test_save_with_export_to_file(self, tmp_db, monkeypatch):
        from xuansto_mcp.tools import session_manage

        monkeypatch.setattr(session_manage, "SESSION_DIR", tmp_db)

        result = session_manage._save_session(
            completed_tasks=["task1"],
            export_to_file=True,
        )

        assert result["persisted_to"] == "sqlite+file"
        assert "path" in result
        session_files = list(tmp_db.glob("session-*.md"))
        assert len(session_files) == 1


class TestLoadFromSQLite:
    def test_load_reads_from_sqlite(self, tmp_db, monkeypatch):
        from xuansto_mcp.tools import session_manage
        from xuansto_mcp.core.database import persist_state

        monkeypatch.setattr(session_manage, "SESSION_DIR", tmp_db)

        session_data = {
            "completed_tasks": ["task_a"],
            "pending_tasks": ["task_b"],
            "decisions": ["dec_a"],
            "experience": ["exp_a"],
            "timestamp": "20260101-000000",
        }
        persist_state("session_states", {
            "id": "session-20260101-000000",
            "session_data_json": session_data,
        })

        result = session_manage._load_last_session()

        assert result["source"] == "sqlite"
        content = result["content"]
        assert "task_a" in content["completed_tasks"]

    def test_load_fallback_to_file(self, tmp_db, monkeypatch):
        from xuansto_mcp.tools import session_manage

        monkeypatch.setattr(session_manage, "SESSION_DIR", tmp_db)

        (tmp_db / "session-20260101-000000.md").write_text("# Session", encoding="utf-8")

        result = session_manage._load_last_session()

        assert result["source"] == "file"
        assert result["content"] == "# Session"

    def test_load_sqlite_priority_over_file(self, tmp_db, monkeypatch):
        from xuansto_mcp.tools import session_manage
        from xuansto_mcp.core.database import persist_state

        monkeypatch.setattr(session_manage, "SESSION_DIR", tmp_db)

        session_data = {
            "completed_tasks": ["from_sqlite"],
            "pending_tasks": [],
            "decisions": [],
            "experience": [],
            "timestamp": "20260101-000000",
        }
        persist_state("session_states", {
            "id": "session-20260101-000000",
            "session_data_json": session_data,
        })

        (tmp_db / "session-20260101-000000.md").write_text("# From File", encoding="utf-8")

        result = session_manage._load_last_session()

        assert result["source"] == "sqlite"
        assert "from_sqlite" in result["content"]["completed_tasks"]


class TestTrackSessionSQLite:
    def test_track_writes_to_sqlite(self, tmp_db, monkeypatch):
        from xuansto_mcp.tools import session_manage
        from xuansto_mcp.core.database import load_state

        monkeypatch.setattr(session_manage, "SESSION_DIR", tmp_db)
        monkeypatch.setattr(session_manage, "_RESTORED_STATE", None)

        result = session_manage._track_session(
            current_phase=2,
            current_task="implementing",
            decisions=["use sqlite"],
            pending_tasks=["test"],
        )

        assert result["current_phase"] == 2
        assert "use sqlite" in result["decisions"]

        rows = load_state("session_states", {"id": "current_session"})
        assert len(rows) == 1
        data = rows[0].get("session_data_json", {})
        if isinstance(data, str):
            data = json.loads(data)
        assert data["current_phase"] == 2

    def test_track_reads_existing_from_sqlite(self, tmp_db, monkeypatch):
        from xuansto_mcp.tools import session_manage
        from xuansto_mcp.core.database import persist_state

        monkeypatch.setattr(session_manage, "SESSION_DIR", tmp_db)
        monkeypatch.setattr(session_manage, "_RESTORED_STATE", None)

        persist_state("session_states", {
            "id": "current_session",
            "session_data_json": {
                "current_phase": 1,
                "current_task": "design",
                "decisions": ["dec1"],
                "pending_tasks": ["task1"],
                "completed_phases": [0],
                "timestamp": "2026-01-01T00:00:00+00:00",
            },
        })

        result = session_manage._track_session(
            current_phase=2,
            current_task="implement",
            decisions=["dec2"],
        )

        assert result["current_phase"] == 2
        assert "dec1" in result["decisions"]
        assert "dec2" in result["decisions"]
        assert 1 in result["completed_phases"]


class TestRestoreSessionSQLite:
    def test_restore_reads_from_sqlite(self, tmp_db, monkeypatch):
        from xuansto_mcp.tools import session_manage
        from xuansto_mcp.core.database import persist_state

        monkeypatch.setattr(session_manage, "SESSION_DIR", tmp_db)
        monkeypatch.setattr(session_manage, "_RESTORED_STATE", None)

        persist_state("session_states", {
            "id": "current_session",
            "session_data_json": {
                "current_phase": 3,
                "current_task": "testing",
                "decisions": ["use pytest"],
                "pending_tasks": ["deploy"],
                "completed_phases": [0, 1, 2],
            },
        })

        result = session_manage._restore_session()

        assert result["current_phase"] == 3
        assert result["current_task"] == "testing"
        assert "use pytest" in result["decisions"]

    def test_restore_fallback_to_file(self, tmp_db, monkeypatch):
        from xuansto_mcp.tools import session_manage

        monkeypatch.setattr(session_manage, "SESSION_DIR", tmp_db)
        monkeypatch.setattr(session_manage, "_RESTORED_STATE", None)

        state = {"current_phase": 1, "current_task": "from_file"}
        (tmp_db / "current.json").write_text(json.dumps(state), encoding="utf-8")

        result = session_manage._restore_session()

        assert result["current_phase"] == 1
        assert result["current_task"] == "from_file"


class TestSaveLoadRoundTrip:
    def test_save_then_load_from_sqlite(self, tmp_db, monkeypatch):
        from xuansto_mcp.tools import session_manage

        monkeypatch.setattr(session_manage, "SESSION_DIR", tmp_db)

        session_manage._save_session(
            completed_tasks=["task1", "task2"],
            pending_tasks=["task3"],
            decisions=["dec1"],
            experience=["exp1"],
        )

        result = session_manage._load_last_session()

        assert result["source"] == "sqlite"
        content = result["content"]
        assert "task1" in content["completed_tasks"]
        assert "task2" in content["completed_tasks"]
        assert "task3" in content["pending_tasks"]
        assert "dec1" in content["decisions"]
        assert "exp1" in content["experience"]

    def test_track_then_restore_roundtrip(self, tmp_db, monkeypatch):
        from xuansto_mcp.tools import session_manage

        monkeypatch.setattr(session_manage, "SESSION_DIR", tmp_db)
        monkeypatch.setattr(session_manage, "_RESTORED_STATE", None)

        session_manage._track_session(
            current_phase=4,
            current_task="coding",
            decisions=["use fastapi"],
            pending_tasks=["write tests", "deploy"],
        )

        result = session_manage._restore_session()

        assert result["current_phase"] == 4
        assert result["current_task"] == "coding"
        assert "use fastapi" in result["decisions"]
        assert "write tests" in result["pending_tasks"]
