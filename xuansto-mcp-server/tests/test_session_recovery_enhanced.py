import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

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


class TestWorkflowDispatchRecovery:
    def test_load_on_startup_restores_active_from_sqlite(self, tmp_db, monkeypatch):
        from xuansto_mcp.tools import workflow_dispatch
        from xuansto_mcp.core.database import persist_state

        monkeypatch.setattr(workflow_dispatch, "WORK_DIR", tmp_db)
        monkeypatch.setattr(workflow_dispatch, "_ACTIVE_WORKFLOWS", {})
        monkeypatch.setattr(workflow_dispatch, "_file_backup_enabled", False)

        persist_state("workflow_instances", {
            "id": "wf-active-001",
            "workflow_type": "sdd-tdd-full",
            "current_phase": 3,
            "status": "running",
            "data_json": {
                "workflow_id": "wf-active-001",
                "workflow": "sdd-tdd-full",
                "status": "running",
                "current_phase": 3,
                "project_path": ".",
                "completed_phases": [0, 1, 2],
            },
        })
        persist_state("workflow_instances", {
            "id": "wf-completed-001",
            "workflow_type": "sdd-tdd-medium",
            "current_phase": 9,
            "status": "completed",
            "data_json": {
                "workflow_id": "wf-completed-001",
                "workflow": "sdd-tdd-medium",
                "status": "completed",
                "current_phase": 9,
            },
        })

        workflow_dispatch.load_on_startup()

        assert "wf-active-001" in workflow_dispatch._ACTIVE_WORKFLOWS
        assert "wf-completed-001" not in workflow_dispatch._ACTIVE_WORKFLOWS

    def test_load_on_startup_restores_from_workflow_states(self, tmp_db, monkeypatch):
        from xuansto_mcp.tools import workflow_dispatch
        from xuansto_mcp.core.database import save_workflow_state

        monkeypatch.setattr(workflow_dispatch, "WORK_DIR", tmp_db)
        monkeypatch.setattr(workflow_dispatch, "_ACTIVE_WORKFLOWS", {})
        monkeypatch.setattr(workflow_dispatch, "_file_backup_enabled", False)

        save_workflow_state(
            workflow_id="wf-state-001",
            workflow_type="sdd-tdd-fast",
            current_phase=2,
            project_path="/tmp/project",
            completed_phases=[0, 1],
            status="active",
        )

        workflow_dispatch.load_on_startup()

        assert "wf-state-001" in workflow_dispatch._ACTIVE_WORKFLOWS
        entry = workflow_dispatch._ACTIVE_WORKFLOWS["wf-state-001"]
        assert entry["current_phase"] == 2


class TestTokenBudgetStartup:
    def test_load_on_startup_loads_historical(self, tmp_db, monkeypatch):
        from xuansto_mcp.tools import token_budget
        from xuansto_mcp.core.database import save_token_budget_state

        monkeypatch.setattr(token_budget, "WORK_DIR", tmp_db)
        monkeypatch.setattr(token_budget, "BUDGET_FILE", tmp_db / "token_budget.json")
        monkeypatch.setattr(token_budget, "_HISTORICAL_BUDGETS", [])
        monkeypatch.setattr(token_budget, "_HISTORICAL_LOADED", False)

        save_token_budget_state(
            session_id="sess-1",
            total_budget=100000,
            used=60000,
            phase_allocations={"0": 5000},
            usage_by_phase={"4": 30000},
            project_size="medium",
        )
        save_token_budget_state(
            session_id="sess-2",
            total_budget=200000,
            used=120000,
            phase_allocations={"0": 10000},
            usage_by_phase={"4": 60000},
            project_size="large",
        )

        result = token_budget.load_on_startup()

        assert result["historical_records_loaded"] >= 2
        assert len(token_budget._HISTORICAL_BUDGETS) >= 2
        assert token_budget._HISTORICAL_LOADED is True

    def test_load_on_startup_empty_db(self, tmp_db, monkeypatch):
        from xuansto_mcp.tools import token_budget

        monkeypatch.setattr(token_budget, "WORK_DIR", tmp_db)
        monkeypatch.setattr(token_budget, "BUDGET_FILE", tmp_db / "token_budget.json")
        monkeypatch.setattr(token_budget, "_HISTORICAL_BUDGETS", [])
        monkeypatch.setattr(token_budget, "_HISTORICAL_LOADED", False)

        result = token_budget.load_on_startup()

        assert result["historical_records_loaded"] == 0
        assert token_budget._HISTORICAL_LOADED is True


class TestSessionManageRecovery:
    def test_restore_on_startup_from_sqlite(self, tmp_db, monkeypatch):
        from xuansto_mcp.tools import session_manage
        from xuansto_mcp.core.database import persist_state

        monkeypatch.setattr(session_manage, "SESSION_DIR", tmp_db)
        monkeypatch.setattr(session_manage, "_RESTORED_STATE", None)

        state_data = {
            "current_phase": 4,
            "current_task": "implementing feature",
            "decisions": ["use sqlite"],
            "pending_tasks": ["write tests"],
            "completed_phases": [0, 1, 2, 3],
        }
        persist_state("session_states", {
            "id": "current_session",
            "session_data_json": state_data,
        })

        result = session_manage.restore_on_startup()

        assert result is not None
        assert result["current_phase"] == 4
        assert result["current_task"] == "implementing feature"
        assert "use sqlite" in result["decisions"]

    def test_restore_on_startup_fallback_to_file(self, tmp_db, monkeypatch):
        from xuansto_mcp.tools import session_manage

        monkeypatch.setattr(session_manage, "SESSION_DIR", tmp_db)
        monkeypatch.setattr(session_manage, "_RESTORED_STATE", None)

        state = {"current_phase": 2, "current_task": "designing"}
        (tmp_db / "current.json").write_text(json.dumps(state), encoding="utf-8")

        result = session_manage.restore_on_startup()

        assert result is not None
        assert result["current_phase"] == 2

    def test_restore_on_startup_sqlite_priority_over_file(self, tmp_db, monkeypatch):
        from xuansto_mcp.tools import session_manage
        from xuansto_mcp.core.database import persist_state

        monkeypatch.setattr(session_manage, "SESSION_DIR", tmp_db)
        monkeypatch.setattr(session_manage, "_RESTORED_STATE", None)

        sqlite_state = {"current_phase": 5, "current_task": "from sqlite"}
        persist_state("session_states", {
            "id": "current_session",
            "session_data_json": sqlite_state,
        })

        file_state = {"current_phase": 2, "current_task": "from file"}
        (tmp_db / "current.json").write_text(json.dumps(file_state), encoding="utf-8")

        result = session_manage.restore_on_startup()

        assert result is not None
        assert result["current_phase"] == 5
        assert result["current_task"] == "from sqlite"

    def test_full_restart_cycle(self, tmp_db, monkeypatch):
        from xuansto_mcp.tools import session_manage
        from xuansto_mcp.core.database import persist_state

        monkeypatch.setattr(session_manage, "SESSION_DIR", tmp_db)

        state = {
            "current_phase": 3,
            "current_task": "testing",
            "decisions": ["use pytest"],
            "pending_tasks": ["deploy"],
            "completed_phases": [0, 1, 2],
        }
        persist_state("session_states", {
            "id": "current_session",
            "session_data_json": state,
        })

        monkeypatch.setattr(session_manage, "_RESTORED_STATE", None)
        result = session_manage.restore_on_startup()
        assert result is not None
        assert result["current_phase"] == 3

        monkeypatch.setattr(session_manage, "_RESTORED_STATE", None)
        result2 = session_manage.restore_on_startup()
        assert result2 is not None
        assert result2["current_phase"] == 3
        assert "use pytest" in result2["decisions"]
