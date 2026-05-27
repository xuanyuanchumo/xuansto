from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def _isolated_db(tmp_path, monkeypatch):
    db_path = tmp_path / "xuansto.db"
    monkeypatch.setenv("XUANSTO_WORK_DIR", str(tmp_path))
    from xuansto_mcp.core import database as db_mod
    monkeypatch.setattr(db_mod, "DB_PATH", db_path)
    monkeypatch.setattr(db_mod, "WORK_DIR", tmp_path)
    db_mod.init_db()
    yield
    db_mod._FTS5_AVAILABLE = None


class TestSaveTokenBudgetState:
    def test_save_returns_saved_status(self):
        from xuansto_mcp.core.database import save_token_budget_state
        result = save_token_budget_state(
            session_id="sess-001",
            total_budget=100000,
            used=35000,
            phase_allocations={"0": 5000, "1": 10000},
            usage_by_phase={"0": 3000, "1": 8000},
            project_size="medium",
        )
        assert result["status"] == "saved"
        assert result["session_id"] == "sess-001"

    def test_save_creates_db_record(self):
        from xuansto_mcp.core.database import load_state, save_token_budget_state
        save_token_budget_state(
            session_id="sess-002",
            total_budget=200000,
            used=50000,
            phase_allocations={"0": 10000},
            usage_by_phase={"0": 5000},
            project_size="large",
        )
        rows = load_state("token_budget_states", {"session_id": "sess-002"})
        assert len(rows) >= 1
        row = rows[0]
        assert row["total_budget"] == 200000
        assert row["used"] == 50000
        assert row["project_size"] == "large"

    def test_save_upsert_same_session(self):
        from xuansto_mcp.core.database import load_state, save_token_budget_state
        save_token_budget_state(
            session_id="sess-003",
            total_budget=100000,
            used=10000,
            phase_allocations={},
            usage_by_phase={},
        )
        save_token_budget_state(
            session_id="sess-003",
            total_budget=150000,
            used=20000,
            phase_allocations={"0": 8000},
            usage_by_phase={"0": 5000},
        )
        rows = load_state("token_budget_states", {"session_id": "sess-003"})
        assert len(rows) == 1
        assert rows[0]["total_budget"] == 150000
        assert rows[0]["used"] == 20000


class TestLoadTokenBudgetStates:
    def test_load_returns_recent_records(self):
        from xuansto_mcp.core.database import load_token_budget_states, save_token_budget_state
        for i in range(5):
            save_token_budget_state(
                session_id=f"sess-{i:03d}",
                total_budget=100000 + i * 10000,
                used=10000 + i * 5000,
                phase_allocations={},
                usage_by_phase={},
            )
        results = load_token_budget_states(limit=3)
        assert len(results) == 3

    def test_load_filter_by_session_id(self):
        from xuansto_mcp.core.database import load_token_budget_states, save_token_budget_state
        save_token_budget_state(
            session_id="target-sess",
            total_budget=100000,
            used=10000,
            phase_allocations={},
            usage_by_phase={},
        )
        save_token_budget_state(
            session_id="other-sess",
            total_budget=200000,
            used=20000,
            phase_allocations={},
            usage_by_phase={},
        )
        results = load_token_budget_states(session_id="target-sess")
        assert all(r["session_id"] == "target-sess" for r in results)

    def test_load_empty_when_no_records(self):
        from xuansto_mcp.core.database import load_token_budget_states
        results = load_token_budget_states()
        assert results == []


class TestCrossSessionPersistence:
    def test_save_then_load_data_consistency(self):
        from xuansto_mcp.core.database import load_token_budget_states, save_token_budget_state
        phase_alloc = {"0": 5000, "1": 10000, "2": 15000}
        usage_phase = {"0": 3000, "1": 8000, "2": 12000}
        save_result = save_token_budget_state(
            session_id="consistency-sess",
            total_budget=150000,
            used=75000,
            phase_allocations=phase_alloc,
            usage_by_phase=usage_phase,
            project_size="medium",
        )
        assert save_result["status"] == "saved"

        loaded = load_token_budget_states(session_id="consistency-sess")
        assert len(loaded) == 1
        row = loaded[0]
        assert row["total_budget"] == 150000
        assert row["used"] == 75000
        assert row["project_size"] == "medium"
        assert row["session_id"] == "consistency-sess"

        loaded_alloc = row.get("phase_allocations_json", {})
        if isinstance(loaded_alloc, str):
            loaded_alloc = json.loads(loaded_alloc)
        assert loaded_alloc == phase_alloc

        loaded_usage = row.get("usage_by_phase_json", {})
        if isinstance(loaded_usage, str):
            loaded_usage = json.loads(loaded_usage)
        assert loaded_usage == usage_phase

    def test_multiple_sessions_persisted(self):
        from xuansto_mcp.core.database import load_token_budget_states, save_token_budget_state
        for i in range(3):
            save_token_budget_state(
                session_id=f"multi-sess-{i}",
                total_budget=100000 * (i + 1),
                used=10000 * (i + 1),
                phase_allocations={str(i): 5000 * (i + 1)},
                usage_by_phase={str(i): 2000 * (i + 1)},
                project_size=["small", "medium", "large"][i],
            )
        all_records = load_token_budget_states()
        assert len(all_records) == 3
        sizes = {r["project_size"] for r in all_records}
        assert sizes == {"small", "medium", "large"}


class TestReportPersistence:
    def test_report_action_persists_to_sqlite(self, tmp_path):
        from xuansto_mcp.core.database import init_db, load_token_budget_states
        from xuansto_mcp.tools.token_budget import _report, _set_budget

        _set_budget(total_budget=100000)

        result = _report(period="session")
        assert "persistence" in result
        assert result["persistence"]["status"] == "saved"

    def test_status_includes_historical_usage(self, tmp_path):
        from xuansto_mcp.core.database import init_db, save_token_budget_state
        from xuansto_mcp.tools.token_budget import _get_status

        save_token_budget_state(
            session_id="hist-sess-1",
            total_budget=100000,
            used=50000,
            phase_allocations={},
            usage_by_phase={},
            project_size="medium",
        )

        status = _get_status()
        assert "historical_usage" in status
        assert isinstance(status["historical_usage"], list)

    def test_status_recommended_budget(self, tmp_path):
        from xuansto_mcp.core.database import init_db, save_token_budget_state
        from xuansto_mcp.tools.token_budget import _get_status, _set_budget

        for i in range(3):
            save_token_budget_state(
                session_id=f"rec-sess-{i}",
                total_budget=100000,
                used=60000 + i * 5000,
                phase_allocations={},
                usage_by_phase={},
                project_size="medium",
            )

        _set_budget(total_budget=100000)
        status = _get_status()
        assert "recommended_budget" in status
        if status["historical_usage"]:
            assert status["recommended_budget"] is not None
            assert status["recommended_budget"] > 0
