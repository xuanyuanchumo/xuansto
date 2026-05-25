from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from xuansto_mcp.core.database import (
    _CREATE_TABLES_SQL,
    _CREATE_INDEXES_SQL,
    save_agent_state,
    load_agent_states,
    delete_agent_state,
    save_workflow_state,
    load_workflow_states,
    delete_workflow_state,
)


def _init_temp_db(db_path: Path) -> None:
    conn = sqlite3.connect(str(db_path))
    conn.executescript(_CREATE_TABLES_SQL)
    conn.executescript(_CREATE_INDEXES_SQL)
    conn.commit()
    conn.close()


@pytest.fixture
def temp_db(tmp_path):
    db_path = tmp_path / "test_xuansto.db"
    _init_temp_db(db_path)
    with patch("xuansto_mcp.core.database.DB_PATH", db_path):
        with patch("xuansto_mcp.core.database.get_db") as mock_get_db:
            def _make_conn():
                conn = sqlite3.connect(str(db_path))
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA busy_timeout=5000")
                conn.execute("PRAGMA foreign_keys=ON")
                conn.row_factory = sqlite3.Row
                return conn
            mock_get_db.side_effect = _make_conn
            yield db_path


def test_save_agent_state_inserts_new(temp_db):
    save_agent_state("agent-001", "Planner", "product", phase=1, status="active")
    agents = load_agent_states(status="active")
    assert len(agents) == 1
    a = agents[0]
    assert a["agent_id"] == "agent-001"
    assert a["agent_name"] == "Planner"
    assert a["agent_type"] == "product"
    assert a["phase"] == 1
    assert a["status"] == "active"


def test_load_agent_states_returns_active(temp_db):
    save_agent_state("agent-a", "A", "type_a", status="active")
    save_agent_state("agent-b", "B", "type_b", status="inactive")
    active = load_agent_states(status="active")
    assert len(active) == 1
    assert active[0]["agent_id"] == "agent-a"


def test_load_agent_states_all_when_none(temp_db):
    save_agent_state("agent-a", "A", "type_a", status="active")
    save_agent_state("agent-b", "B", "type_b", status="inactive")
    all_agents = load_agent_states(status=None)
    assert len(all_agents) == 2


def test_delete_agent_state_removes(temp_db):
    save_agent_state("agent-del", "ToDelete", "type_x")
    assert len(load_agent_states(status="active")) == 1
    delete_agent_state("agent-del")
    assert len(load_agent_states(status="active")) == 0


def test_save_workflow_state_inserts_new(temp_db):
    save_workflow_state(
        "wf-001", "sdd-tdd", current_phase=2,
        project_path="/tmp/proj",
        completed_phases=[0, 1],
        tasks={"task1": "done"},
        decisions={"dec1": "approved"},
        status="active",
    )
    workflows = load_workflow_states(status="active")
    assert len(workflows) == 1
    w = workflows[0]
    assert w["workflow_id"] == "wf-001"
    assert w["workflow_type"] == "sdd-tdd"
    assert w["current_phase"] == 2
    assert w["project_path"] == "/tmp/proj"
    assert w["completed_phases_json"] == [0, 1]
    assert w["tasks_json"] == {"task1": "done"}
    assert w["decisions_json"] == {"dec1": "approved"}


def test_load_workflow_states_returns_active(temp_db):
    save_workflow_state("wf-active", "type_a", status="active")
    save_workflow_state("wf-done", "type_b", status="completed")
    active = load_workflow_states(status="active")
    assert len(active) == 1
    assert active[0]["workflow_id"] == "wf-active"


def test_load_workflow_states_all_when_none(temp_db):
    save_workflow_state("wf-active", "type_a", status="active")
    save_workflow_state("wf-done", "type_b", status="completed")
    all_wf = load_workflow_states(status=None)
    assert len(all_wf) == 2


def test_delete_workflow_state_removes(temp_db):
    save_workflow_state("wf-del", "type_x")
    assert len(load_workflow_states(status="active")) == 1
    delete_workflow_state("wf-del")
    assert len(load_workflow_states(status="active")) == 0


def test_save_agent_state_upsert_updates_existing(temp_db):
    save_agent_state("agent-up", "Original", "type_a", phase=0, status="active")
    agents = load_agent_states(status="active")
    assert len(agents) == 1
    assert agents[0]["agent_name"] == "Original"
    assert agents[0]["phase"] == 0

    save_agent_state("agent-up", "Updated", "type_b", phase=3, status="active", config={"key": "val"})
    agents = load_agent_states(status="active")
    assert len(agents) == 1
    a = agents[0]
    assert a["agent_name"] == "Updated"
    assert a["agent_type"] == "type_b"
    assert a["phase"] == 3
    assert a["config_json"] == {"key": "val"}


def test_save_workflow_state_upsert_updates_existing(temp_db):
    save_workflow_state("wf-up", "type_a", current_phase=0, status="active")
    workflows = load_workflow_states(status="active")
    assert len(workflows) == 1
    assert workflows[0]["current_phase"] == 0

    save_workflow_state(
        "wf-up", "type_b", current_phase=5,
        completed_phases=[0, 1, 2, 3, 4],
        tasks={"t1": "done"},
        status="active",
    )
    workflows = load_workflow_states(status="active")
    assert len(workflows) == 1
    w = workflows[0]
    assert w["workflow_type"] == "type_b"
    assert w["current_phase"] == 5
    assert w["completed_phases_json"] == [0, 1, 2, 3, 4]
    assert w["tasks_json"] == {"t1": "done"}
