from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from xuansto_mcp.core.database import (
    init_db,
    get_db,
    persist_state,
    load_state,
    cleanup_metrics,
    DB_PATH,
)


@pytest.fixture
def tmp_db(tmp_work_dir, patch_config):
    import xuansto_mcp.core.database as db_mod
    original_db_path = db_mod.DB_PATH
    db_mod.DB_PATH = tmp_work_dir / "test_xuansto.db"
    db_mod.WORK_DIR = tmp_work_dir
    try:
        db_mod.init_db()
        yield db_mod
    finally:
        db_mod.DB_PATH = original_db_path


def test_init_db_creates_tables(tmp_db):
    conn = tmp_db.get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        assert "workflow_instances" in tables
        assert "session_states" in tables
        assert "resource_load_states" in tables
        assert "degradation_states" in tables
        assert "error_patterns" in tables
        assert "metrics" in tables
        assert "decision_records" in tables
        assert "knowledge_entries" in tables
    finally:
        conn.close()


def test_init_db_creates_indexes(tmp_db):
    conn = tmp_db.get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = {row[0] for row in cursor.fetchall()}
        assert "idx_workflow_instances_status" in indexes
        assert "idx_metrics_timestamp" in indexes
    finally:
        conn.close()


def test_persist_state_workflow(tmp_db):
    data = {
        "id": "wf-001",
        "workflow_type": "sdd-tdd-full",
        "current_phase": 2,
        "status": "running",
        "data_json": {"steps": ["step1", "step2"]},
    }
    tmp_db.persist_state("workflow_instances", data)
    results = tmp_db.load_state("workflow_instances", {"id": "wf-001"})
    assert len(results) == 1
    assert results[0]["id"] == "wf-001"
    assert results[0]["workflow_type"] == "sdd-tdd-full"
    assert results[0]["data_json"] == {"steps": ["step1", "step2"]}


def test_persist_state_session(tmp_db):
    data = {
        "id": "sess-001",
        "session_data_json": {"tasks": ["task1"]},
    }
    tmp_db.persist_state("session_states", data)
    results = tmp_db.load_state("session_states", {"id": "sess-001"})
    assert len(results) == 1
    assert results[0]["id"] == "sess-001"
    assert results[0]["session_data_json"] == {"tasks": ["task1"]}


def test_persist_state_upsert(tmp_db):
    data = {
        "id": "wf-002",
        "workflow_type": "sdd-tdd-fast",
        "current_phase": 0,
        "status": "running",
        "data_json": {},
    }
    tmp_db.persist_state("workflow_instances", data)
    data["current_phase"] = 3
    data["status"] = "completed"
    tmp_db.persist_state("workflow_instances", data)
    results = tmp_db.load_state("workflow_instances", {"id": "wf-002"})
    assert len(results) == 1
    assert results[0]["current_phase"] == 3
    assert results[0]["status"] == "completed"


def test_persist_state_invalid_table(tmp_db):
    tmp_db.persist_state("nonexistent_table", {"id": "x"})


def test_persist_state_metrics_auto_increment(tmp_db):
    data = {
        "tool_name": "skill_analyze",
        "metric_type": "calls",
        "value_json": {"count": 1},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    tmp_db.persist_state("metrics", data)
    results = tmp_db.load_state("metrics", {"tool_name": "skill_analyze"})
    assert len(results) >= 1


def test_load_state_no_query(tmp_db):
    data = {
        "id": "wf-003",
        "workflow_type": "test",
        "current_phase": 0,
        "status": "running",
        "data_json": {},
    }
    tmp_db.persist_state("workflow_instances", data)
    results = tmp_db.load_state("workflow_instances")
    assert len(results) >= 1


def test_load_state_invalid_table(tmp_db):
    results = tmp_db.load_state("nonexistent_table")
    assert results == []


def test_load_state_json_fields_parsed(tmp_db):
    data = {
        "id": "wf-json",
        "workflow_type": "test",
        "current_phase": 0,
        "status": "running",
        "data_json": {"key": "value", "nested": [1, 2, 3]},
    }
    tmp_db.persist_state("workflow_instances", data)
    results = tmp_db.load_state("workflow_instances", {"id": "wf-json"})
    assert len(results) == 1
    assert isinstance(results[0]["data_json"], dict)
    assert results[0]["data_json"]["key"] == "value"


def test_cleanup_metrics_removes_old(tmp_db):
    old_date = (datetime.now(timezone.utc) - timedelta(days=60)).isoformat()
    data_old = {
        "tool_name": "old_tool",
        "metric_type": "calls",
        "value_json": {"count": 1},
        "timestamp": old_date,
    }
    tmp_db.persist_state("metrics", data_old)
    recent_date = datetime.now(timezone.utc).isoformat()
    data_recent = {
        "tool_name": "recent_tool",
        "metric_type": "calls",
        "value_json": {"count": 2},
        "timestamp": recent_date,
    }
    tmp_db.persist_state("metrics", data_recent)
    deleted = tmp_db.cleanup_metrics(older_than_days=30)
    assert deleted >= 1
    results = tmp_db.load_state("metrics")
    tool_names = [r["tool_name"] for r in results]
    assert "recent_tool" in tool_names


def test_cleanup_metrics_no_old_data(tmp_db):
    recent_date = datetime.now(timezone.utc).isoformat()
    data = {
        "tool_name": "fresh_tool",
        "metric_type": "calls",
        "value_json": {"count": 1},
        "timestamp": recent_date,
    }
    tmp_db.persist_state("metrics", data)
    deleted = tmp_db.cleanup_metrics(older_than_days=30)
    assert deleted == 0


def test_get_db_connection(tmp_db):
    conn = tmp_db.get_db()
    try:
        assert conn is not None
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        assert cursor.fetchone()[0] == 1
    finally:
        conn.close()


def test_persist_state_no_id_for_non_auto_table(tmp_db):
    tmp_db.persist_state("workflow_instances", {"workflow_type": "test"})


def test_knowledge_entries_crud(tmp_db):
    data = {
        "id": "kb-001",
        "title": "Test Entry",
        "content": "Test content for knowledge base",
        "scope": "general",
        "tags_json": ["python", "testing"],
    }
    tmp_db.persist_state("knowledge_entries", data)
    results = tmp_db.load_state("knowledge_entries", {"id": "kb-001"})
    assert len(results) == 1
    assert results[0]["title"] == "Test Entry"
    assert results[0]["tags_json"] == ["python", "testing"]


def test_session_states_update(tmp_db):
    data = {
        "id": "sess-002",
        "session_data_json": {"phase": 0, "status": "init"},
    }
    tmp_db.persist_state("session_states", data)
    data["session_data_json"] = {"phase": 2, "status": "running"}
    tmp_db.persist_state("session_states", data)
    results = tmp_db.load_state("session_states", {"id": "sess-002"})
    assert len(results) == 1
    assert results[0]["session_data_json"]["phase"] == 2
    assert results[0]["session_data_json"]["status"] == "running"
