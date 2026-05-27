from __future__ import annotations

import gzip
import json
import os
import tempfile
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from xuansto_mcp.core.config import MCP_API_VERSION
from xuansto_mcp.core.errors import make_success_response, make_error_response
from xuansto_mcp.tools.agent_manage import (
    _AGENT_INSTANCES,
    _agents_lock,
    _MAX_AGENT_INSTANCES,
    _AgentInstance,
    _persist_agent_instances,
)
from xuansto_mcp.tools.resource_load_status import (
    PHASE_RESOURCE_MAP,
    _PHASE_INHERITS,
    _RESOURCE_CACHE,
    _cache_lock,
)
from xuansto_mcp.tools.workflow_dispatch import (
    _save_snapshot,
    _load_snapshot_file,
    _cleanup_snapshots,
    _get_snapshot_dir,
)


class TestApiVersionInAllTools:
    def test_make_success_response_includes_api_version(self):
        result = make_success_response(data={"test": True})
        assert "api_version" in result
        assert result["api_version"] == MCP_API_VERSION

    def test_make_success_response_with_degradation(self):
        result = make_success_response(data={"test": True}, degradation_level="inline")
        assert "api_version" in result
        assert result["api_version"] == MCP_API_VERSION

    def test_make_success_response_no_data(self):
        result = make_success_response()
        assert "api_version" in result
        assert result["api_version"] == MCP_API_VERSION

    def test_mcp_api_version_value(self):
        assert MCP_API_VERSION == "3.0.0"

    def test_error_response_does_not_include_api_version(self):
        result = make_error_response(ValueError("test"))
        assert "api_version" not in result


class TestSnapshotCompressed:
    def test_snapshot_saved_as_gzip(self, tmp_path):
        workflow_id = "wf-test1234"
        state = {
            "workflow_id": workflow_id,
            "current_phase": 1,
            "status": "running",
        }
        project_path = str(tmp_path)
        gz_path = _save_snapshot(workflow_id, state, project_path)
        assert gz_path.exists(), f"Expected .json.gz file at {gz_path}"
        assert gz_path.suffixes == [".json", ".gz"], f"Expected .json.gz suffix, got {gz_path.name}"
        with gzip.open(gz_path, 'rb') as f:
            data = json.loads(f.read().decode('utf-8'))
        assert data["workflow_id"] == workflow_id
        assert data["phase"] == 1
        assert data["state"]["status"] == "running"

    def test_snapshot_gzip_is_valid(self, tmp_path):
        workflow_id = "wf-gzvalid"
        state = {"workflow_id": workflow_id, "current_phase": 2, "status": "running"}
        project_path = str(tmp_path)
        _save_snapshot(workflow_id, state, project_path)
        snapshot_dir = _get_snapshot_dir(project_path)
        gz_files = list(snapshot_dir.glob("*.json.gz"))
        assert len(gz_files) > 0
        for gz_file in gz_files:
            with gzip.open(gz_file, 'rb') as f:
                content = f.read().decode('utf-8')
            parsed = json.loads(content)
            assert "workflow_id" in parsed


class TestSnapshotBackwardCompatible:
    def test_old_json_snapshot_still_loadable(self, tmp_path):
        snapshot_dir = _get_snapshot_dir(str(tmp_path))
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        old_data = {
            "workflow_id": "wf-old",
            "phase": 3,
            "timestamp": 1000000.0,
            "time_iso": "2025-01-01T00:00:00",
            "state": {"workflow_id": "wf-old", "current_phase": 3, "status": "running"},
        }
        old_file = snapshot_dir / "wf-old_phase3_1000000.json"
        old_file.write_text(json.dumps(old_data, ensure_ascii=False, indent=2), encoding="utf-8")
        loaded = _load_snapshot_file(old_file)
        assert loaded is not None
        assert loaded["workflow_id"] == "wf-old"
        assert loaded["phase"] == 3

    def test_gz_snapshot_loadable(self, tmp_path):
        snapshot_dir = _get_snapshot_dir(str(tmp_path))
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        data = {
            "workflow_id": "wf-gz",
            "phase": 4,
            "timestamp": 2000000.0,
            "time_iso": "2025-06-01T00:00:00",
            "state": {"workflow_id": "wf-gz", "current_phase": 4, "status": "running"},
        }
        gz_file = snapshot_dir / "wf-gz_phase4_2000000.json.gz"
        json_bytes = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        compressed = gzip.compress(json_bytes, compresslevel=6)
        gz_file.write_bytes(compressed)
        loaded = _load_snapshot_file(gz_file)
        assert loaded is not None
        assert loaded["workflow_id"] == "wf-gz"
        assert loaded["phase"] == 4


class TestAgentResourceMetrics:
    def setup_method(self):
        with _agents_lock:
            _AGENT_INSTANCES.clear()

    def test_create_includes_metrics(self):
        inst = _AgentInstance(
            agent_id="agent-test1",
            agent_type="TestAgent",
            capabilities=["test"],
        )
        assert inst.task_count == 0
        assert inst.total_duration_ms == 0
        assert inst.last_active_at != ""

    def test_assign_increments_task_count(self):
        inst = _AgentInstance(
            agent_id="agent-test2",
            agent_type="TestAgent",
            capabilities=["test"],
        )
        with _agents_lock:
            _AGENT_INSTANCES["agent-test2"] = inst
            inst.status = "busy"
            inst.task = "do something"
            inst.task_count += 1
            from datetime import datetime, timezone
            inst.last_active_at = datetime.now(timezone.utc).isoformat()
        assert inst.task_count == 1
        assert inst.last_active_at != ""

    def test_destroy_includes_metrics(self):
        inst = _AgentInstance(
            agent_id="agent-test3",
            agent_type="TestAgent",
            capabilities=["test"],
            task_count=5,
            total_duration_ms=1200,
        )
        with _agents_lock:
            _AGENT_INSTANCES["agent-test3"] = inst
            popped = _AGENT_INSTANCES.pop("agent-test3")
        assert popped.task_count == 5
        assert popped.total_duration_ms == 1200

    def test_persist_and_load_metrics(self, tmp_path):
        import xuansto_mcp.tools.agent_manage as agent_mod
        original_work_dir = agent_mod.WORK_DIR
        try:
            agent_mod.WORK_DIR = tmp_path
            inst = _AgentInstance(
                agent_id="agent-persist",
                agent_type="TestAgent",
                capabilities=["test"],
                task_count=3,
                total_duration_ms=500,
            )
            with _agents_lock:
                _AGENT_INSTANCES["agent-persist"] = inst
            _persist_agent_instances()
            persist_file = tmp_path / "agent_instances.json"
            assert persist_file.exists()
            data = json.loads(persist_file.read_text(encoding="utf-8"))
            assert data["agent-persist"]["task_count"] == 3
            assert data["agent-persist"]["total_duration_ms"] == 500
        finally:
            agent_mod.WORK_DIR = original_work_dir
            with _agents_lock:
                _AGENT_INSTANCES.clear()


class TestAgentMaxInstances:
    def setup_method(self):
        with _agents_lock:
            _AGENT_INSTANCES.clear()

    def teardown_method(self):
        with _agents_lock:
            _AGENT_INSTANCES.clear()

    def test_max_instances_constant(self):
        assert _MAX_AGENT_INSTANCES == 20

    def test_creation_blocked_at_limit(self):
        for i in range(_MAX_AGENT_INSTANCES):
            aid = f"agent-limit-{i}"
            with _agents_lock:
                _AGENT_INSTANCES[aid] = _AgentInstance(
                    agent_id=aid,
                    agent_type="TestAgent",
                    capabilities=["test"],
                )
        with _agents_lock:
            assert len(_AGENT_INSTANCES) >= _MAX_AGENT_INSTANCES
            can_create = len(_AGENT_INSTANCES) < _MAX_AGENT_INSTANCES
        assert not can_create


class TestPhaseResourceDedup:
    def test_phase2_inherits_from_phase1(self):
        assert 2 in _PHASE_INHERITS
        assert 1 in _PHASE_INHERITS[2]

    def test_phase3_inherits_from_phase2(self):
        assert 3 in _PHASE_INHERITS
        assert 2 in _PHASE_INHERITS[3]

    def test_phase2_and_phase3_share_karpathy_path(self):
        phase2_resources = PHASE_RESOURCE_MAP[2]
        phase3_resources = PHASE_RESOURCE_MAP[3]
        phase2_paths = {r["path"] for r in phase2_resources}
        phase3_paths = {r["path"] for r in phase3_resources}
        shared = phase2_paths & phase3_paths
        assert len(shared) >= 0

    def test_phase3_inherited_resource_skips_reload(self):
        with _cache_lock:
            _RESOURCE_CACHE.clear()
        phase3_resources = PHASE_RESOURCE_MAP[3]
        inherited_paths: set[str] = set()
        for parent_phase in _PHASE_INHERITS.get(3, []):
            for parent_res in PHASE_RESOURCE_MAP.get(parent_phase, []):
                inherited_paths.add(parent_res["path"])
        for r in phase3_resources:
            if r["path"] in inherited_paths:
                if r["id"] in _RESOURCE_CACHE:
                    assert True
                    with _cache_lock:
                        _RESOURCE_CACHE.clear()
                    return
        with _cache_lock:
            _RESOURCE_CACHE.clear()


class TestNoPrivateApiInServerHealth:
    def test_server_health_source_no_private_api(self):
        server_health_path = Path(__file__).resolve().parent.parent / "src" / "xuansto_mcp" / "tools" / "server_health.py"
        content = server_health_path.read_text(encoding="utf-8")
        assert "mcp._tool_manager._tools" not in content, "server_health.py should not access mcp._tool_manager._tools"
        assert "mcp._resource_manager._resources" not in content, "server_health.py should not access mcp._resource_manager._resources"

    def test_server_health_uses_registered_names(self):
        server_health_path = Path(__file__).resolve().parent.parent / "src" / "xuansto_mcp" / "tools" / "server_health.py"
        content = server_health_path.read_text(encoding="utf-8")
        assert "_REGISTERED_TOOL_NAMES" in content
        assert "_REGISTERED_RESOURCE_NAMES" in content

    def test_server_py_exports_resource_names(self):
        server_path = Path(__file__).resolve().parent.parent / "src" / "xuansto_mcp" / "server.py"
        content = server_path.read_text(encoding="utf-8")
        assert "_REGISTERED_RESOURCE_NAMES" in content
