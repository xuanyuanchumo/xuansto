from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp.server.fastmcp import FastMCP

from xuansto_mcp.resources import skill_resources


@pytest.fixture
def mcp_server():
    return FastMCP("test-resources")


@pytest.fixture
def registered(mcp_server):
    skill_resources.register(mcp_server)
    return mcp_server


def _get_resource_fn(registered, uri: str):
    for tmpl in registered._resource_manager.list_templates():
        if uri in str(tmpl.uri_template):
            return tmpl.fn
    for res in registered._resource_manager.list_resources():
        if uri in str(res.uri):
            return res.fn
    raise KeyError(f"Resource '{uri}' not found")


class TestAgentByNameResource:
    def test_existing_agent(self, registered, tmp_path):
        agents_dir = tmp_path / "agents"
        layer_dir = agents_dir / "core"
        layer_dir.mkdir(parents=True)
        agent_file = layer_dir / "planner.md"
        agent_file.write_text("# Planner Agent\nExecutes planning tasks.", encoding="utf-8")

        fn = _get_resource_fn(registered, "xuansto://agents/{name}")
        with patch.object(skill_resources, "AGENTS_DIR", agents_dir):
            result = fn("planner")
        assert result == "# Planner Agent\nExecutes planning tasks."

    def test_non_existing_agent(self, registered, tmp_path):
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir(parents=True)

        fn = _get_resource_fn(registered, "xuansto://agents/{name}")
        with patch.object(skill_resources, "AGENTS_DIR", agents_dir):
            result = fn("nonexistent")
        data = json.loads(result)
        assert data["status"] == "not_found"
        assert data["name"] == "nonexistent"

    def test_degraded_state(self, registered, tmp_path):
        nonexistent = tmp_path / "no_such_dir"

        fn = _get_resource_fn(registered, "xuansto://agents/{name}")
        with patch.object(skill_resources, "AGENTS_DIR", nonexistent):
            with patch.object(Path, "exists", side_effect=RuntimeError("disk error")):
                result = fn("anything")
        data = json.loads(result)
        assert data["status"] == "degraded"


class TestKnowledgeStatsResource:
    def test_with_knowledge_db(self, registered, tmp_path):
        knowledge_dir = tmp_path / "knowledge"
        index_dir = knowledge_dir / "index"
        index_dir.mkdir(parents=True)
        db_path = index_dir / "knowledge.db"

        conn = sqlite3.connect(str(db_path))
        conn.execute(
            "CREATE TABLE knowledge_entries "
            "(id TEXT PRIMARY KEY, title TEXT, content TEXT, scope TEXT, deleted_at TEXT)"
        )
        conn.executemany(
            "INSERT INTO knowledge_entries (id, title, content, scope, deleted_at) VALUES (?, ?, ?, ?, NULL)",
            [
                ("k1", "Entry 1", "Content 1", "general"),
                ("k2", "Entry 2", "Content 2", "workspace"),
                ("k3", "Entry 3", "Content 3", "general"),
            ],
        )
        conn.commit()
        conn.close()

        chroma_path = index_dir / "chroma_db"

        fn = _get_resource_fn(registered, "xuansto://knowledge/stats")
        with patch.object(skill_resources, "KNOWLEDGE_DIR", knowledge_dir), \
             patch.object(skill_resources, "KNOWLEDGE_DB_PATH", db_path), \
             patch.object(skill_resources, "KNOWLEDGE_CHROMA_PATH", chroma_path):
            result = fn()
        data = json.loads(result)
        assert data["db_entry_count"] == 3
        assert data["db_exists"] is True

    def test_without_knowledge_db(self, registered, tmp_path):
        knowledge_dir = tmp_path / "knowledge"
        knowledge_dir.mkdir(parents=True)
        db_path = knowledge_dir / "index" / "knowledge.db"
        chroma_path = knowledge_dir / "index" / "chroma_db"

        fn = _get_resource_fn(registered, "xuansto://knowledge/stats")
        with patch.object(skill_resources, "KNOWLEDGE_DIR", knowledge_dir), \
             patch.object(skill_resources, "KNOWLEDGE_DB_PATH", db_path), \
             patch.object(skill_resources, "KNOWLEDGE_CHROMA_PATH", chroma_path):
            result = fn()
        data = json.loads(result)
        assert data["db_exists"] is False
        assert "db_entry_count" not in data

    def test_with_chromadb(self, registered, tmp_path):
        knowledge_dir = tmp_path / "knowledge"
        index_dir = knowledge_dir / "index"
        index_dir.mkdir(parents=True)
        db_path = index_dir / "knowledge.db"
        chroma_path = index_dir / "chroma_db"
        chroma_path.mkdir(parents=True)

        mock_collection = MagicMock()
        mock_collection.count.return_value = 42
        mock_client = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection

        mock_chromadb = MagicMock()
        mock_chromadb.PersistentClient.return_value = mock_client

        fn = _get_resource_fn(registered, "xuansto://knowledge/stats")
        with patch.object(skill_resources, "KNOWLEDGE_DIR", knowledge_dir), \
             patch.object(skill_resources, "KNOWLEDGE_DB_PATH", db_path), \
             patch.object(skill_resources, "KNOWLEDGE_CHROMA_PATH", chroma_path), \
             patch.dict("sys.modules", {"chromadb": mock_chromadb}):
            result = fn()
        data = json.loads(result)
        assert data["chroma_exists"] is True
        assert data["chroma_entry_count"] == 42

    def test_degraded_state(self, registered, tmp_path):
        knowledge_dir = tmp_path / "knowledge"
        knowledge_dir.mkdir(parents=True)
        db_path = knowledge_dir / "index" / "knowledge.db"
        chroma_path = knowledge_dir / "index" / "chroma_db"

        fn = _get_resource_fn(registered, "xuansto://knowledge/stats")
        with patch.object(skill_resources, "KNOWLEDGE_DIR", knowledge_dir), \
             patch.object(skill_resources, "KNOWLEDGE_DB_PATH", db_path), \
             patch.object(skill_resources, "KNOWLEDGE_CHROMA_PATH", chroma_path), \
             patch.object(Path, "exists", side_effect=RuntimeError("disk error")):
            result = fn()
        data = json.loads(result)
        assert data["status"] == "degraded"


class TestAuditLogResource:
    def test_with_audit_entries(self, registered, tmp_path):
        log_dir = tmp_path / "audit"
        log_dir.mkdir(parents=True)
        log_path = log_dir / "audit_log.jsonl"

        entries = [
            {"timestamp": 1000.0, "tool": "tool_a", "success": True, "latency_ms": 50.0},
            {"timestamp": 1001.0, "tool": "tool_b", "success": False, "latency_ms": 120.0},
        ]
        with open(log_path, "w", encoding="utf-8") as f:
            for entry in entries:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        from xuansto_mcp.core import audit_logger as al_mod

        original_logger = al_mod._audit_logger
        test_logger = al_mod.AuditLogger(log_dir)
        al_mod._audit_logger = test_logger
        try:
            fn = _get_resource_fn(registered, "xuansto://audit/log")
            result = fn()
        finally:
            al_mod._audit_logger = original_logger

        data = json.loads(result)
        assert data["count"] == 2
        assert len(data["entries"]) == 2

    def test_without_audit_file(self, registered, tmp_path):
        log_dir = tmp_path / "audit"
        log_dir.mkdir(parents=True)

        from xuansto_mcp.core import audit_logger as al_mod

        original_logger = al_mod._audit_logger
        test_logger = al_mod.AuditLogger(log_dir)
        al_mod._audit_logger = test_logger
        try:
            fn = _get_resource_fn(registered, "xuansto://audit/log")
            result = fn()
        finally:
            al_mod._audit_logger = original_logger

        data = json.loads(result)
        assert data["count"] == 0
        assert data["entries"] == []

    def test_degraded_state(self, registered):
        fn = _get_resource_fn(registered, "xuansto://audit/log")
        with patch("xuansto_mcp.core.audit_logger.get_audit_logger", side_effect=RuntimeError("audit unavailable")):
            result = fn()
        data = json.loads(result)
        assert data["status"] == "degraded"


class TestLoadingStatusEnhancedResource:
    def _setup_work_dir(self, tmp_path, state_data=None):
        work_dir = tmp_path / ".xuansto"
        work_dir.mkdir(parents=True)
        if state_data is not None:
            state_file = work_dir / "resource_state.json"
            state_file.write_text(json.dumps(state_data), encoding="utf-8")
        return work_dir

    def test_phase_transition_history_field(self, registered, tmp_path):
        work_dir = self._setup_work_dir(tmp_path)
        fn = _get_resource_fn(registered, "xuansto://loading/status")
        with patch.object(skill_resources, "WORK_DIR", work_dir), \
             patch.object(skill_resources, "REFERENCES_DIR", tmp_path / "refs"):
            result = fn()
        data = json.loads(result)
        assert "phase_transition_history" in data
        assert isinstance(data["phase_transition_history"], list)

    def test_performance_metrics_field(self, registered, tmp_path):
        work_dir = self._setup_work_dir(tmp_path)
        fn = _get_resource_fn(registered, "xuansto://loading/status")
        with patch.object(skill_resources, "WORK_DIR", work_dir), \
             patch.object(skill_resources, "REFERENCES_DIR", tmp_path / "refs"):
            result = fn()
        data = json.loads(result)
        assert "performance_metrics" in data
        assert isinstance(data["performance_metrics"], dict)

    def test_performance_metrics_keys(self, registered, tmp_path):
        work_dir = self._setup_work_dir(tmp_path)
        fn = _get_resource_fn(registered, "xuansto://loading/status")
        with patch.object(skill_resources, "WORK_DIR", work_dir), \
             patch.object(skill_resources, "REFERENCES_DIR", tmp_path / "refs"):
            result = fn()
        data = json.loads(result)
        metrics = data["performance_metrics"]
        assert "total_tokens_consumed" in metrics
        assert "avg_phase_transition_ms" in metrics
        assert "resource_load_count" in metrics

    def test_performance_metrics_with_transition_data(self, registered, tmp_path):
        work_dir = self._setup_work_dir(tmp_path)

        mock_cache_lock = MagicMock()
        mock_cache_lock.__enter__ = MagicMock(return_value=None)
        mock_cache_lock.__exit__ = MagicMock(return_value=False)

        mock_tok_lock = MagicMock()
        mock_tok_lock.__enter__ = MagicMock(return_value=None)
        mock_tok_lock.__exit__ = MagicMock(return_value=False)

        transition_history = [
            {
                "started_at": "2025-01-01T00:00:00",
                "completed_at": "2025-01-01T00:00:01.500",
                "from_phase": "skeleton",
                "to_phase": "functional",
            },
            {
                "started_at": "2025-01-01T00:01:00",
                "completed_at": "2025-01-01T00:01:02.200",
                "from_phase": "functional",
                "to_phase": "enhanced",
            },
        ]
        token_metrics = {
            "tool_a": {"total_input_tokens": 100, "total_output_tokens": 50, "call_count": 5},
            "tool_b": {"total_input_tokens": 200, "total_output_tokens": 80, "call_count": 10},
        }

        mock_module = MagicMock()
        mock_module._TRANSITION_HISTORY = transition_history
        mock_module._TOKEN_METRICS = token_metrics
        mock_module._TOKEN_METRICS_LOCK = mock_tok_lock
        mock_module._cache_lock = mock_cache_lock

        fn = _get_resource_fn(registered, "xuansto://loading/status")
        with patch.object(skill_resources, "WORK_DIR", work_dir), \
             patch.object(skill_resources, "REFERENCES_DIR", tmp_path / "refs"), \
             patch.dict("sys.modules", {"xuansto_mcp.tools.resource_load_status": mock_module}):
            result = fn()
        data = json.loads(result)
        metrics = data["performance_metrics"]
        assert metrics["total_tokens_consumed"] == 430
        assert metrics["resource_load_count"] == 15
        assert metrics["avg_phase_transition_ms"] > 0
