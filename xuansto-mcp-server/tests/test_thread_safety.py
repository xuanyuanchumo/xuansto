from __future__ import annotations

import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from xuansto_mcp.tools.server_health import (
    _DEGRADATION_COUNTS,
    _TOOL_METRICS,
    _metrics_lock,
    record_tool_call,
    track_degradation,
)
from xuansto_mcp.tools.workflow_dispatch import (
    _ACTIVE_WORKFLOWS,
    _workflows_lock,
)
from xuansto_mcp.tools.agent_status import (
    _AGENT_INSTANCES,
    _agents_lock,
    _AgentInstance,
)
from xuansto_mcp.tools.resource_load_status import (
    _RESOURCE_CACHE,
    _cache_lock,
)


class TestServerHealthThreadSafety:
    def test_record_tool_call_concurrent(self):
        with _metrics_lock:
            _TOOL_METRICS.clear()
        n_threads = 20
        calls_per_thread = 50
        with ThreadPoolExecutor(max_workers=n_threads) as pool:
            futures = [
                pool.submit(record_tool_call, "test_tool", 10.0 + i, True)
                for i in range(n_threads * calls_per_thread)
            ]
            for f in as_completed(futures):
                f.result()
        with _metrics_lock:
            metrics = _TOOL_METRICS.get("test_tool", {})
            assert metrics.get("call_count", 0) == n_threads * calls_per_thread

    def test_track_degradation_concurrent(self):
        with _metrics_lock:
            _DEGRADATION_COUNTS.clear()
        n_threads = 20
        calls_per_thread = 50
        with ThreadPoolExecutor(max_workers=n_threads) as pool:
            futures = [
                pool.submit(track_degradation, "test_degr")
                for _ in range(n_threads * calls_per_thread)
            ]
            for f in as_completed(futures):
                f.result()
        with _metrics_lock:
            assert _DEGRADATION_COUNTS.get("test_degr", 0) == n_threads * calls_per_thread

    def test_mixed_read_write_metrics(self):
        with _metrics_lock:
            _TOOL_METRICS.clear()
            _DEGRADATION_COUNTS.clear()
        errors = []

        def writer():
            try:
                for i in range(100):
                    record_tool_call("mixed_tool", float(i), i % 3 != 0)
                    track_degradation("mixed_degr")
            except Exception as e:
                errors.append(e)

        def reader():
            try:
                for _ in range(100):
                    with _metrics_lock:
                        _ = dict(_TOOL_METRICS)
                        _ = dict(_DEGRADATION_COUNTS)
            except Exception as e:
                errors.append(e)

        with ThreadPoolExecutor(max_workers=10) as pool:
            futures = []
            for _ in range(5):
                futures.append(pool.submit(writer))
            for _ in range(5):
                futures.append(pool.submit(reader))
            for f in as_completed(futures):
                f.result()
        assert not errors


class TestWorkflowDispatchThreadSafety:
    def test_concurrent_workflow_mutations(self):
        with _workflows_lock:
            _ACTIVE_WORKFLOWS.clear()
        errors = []

        def add_workflow(idx):
            try:
                wid = f"wf-test-{idx}"
                entry = {
                    "workflow_id": wid,
                    "workflow": "test",
                    "project_path": ".",
                    "status": "running",
                    "current_phase": 0,
                }
                with _workflows_lock:
                    _ACTIVE_WORKFLOWS[wid] = entry
            except Exception as e:
                errors.append(e)

        def read_workflows():
            try:
                for _ in range(50):
                    with _workflows_lock:
                        _ = dict(_ACTIVE_WORKFLOWS)
            except Exception as e:
                errors.append(e)

        with ThreadPoolExecutor(max_workers=10) as pool:
            futures = []
            for i in range(5):
                futures.append(pool.submit(add_workflow, i))
            for _ in range(5):
                futures.append(pool.submit(read_workflows))
            for f in as_completed(futures):
                f.result()
        assert not errors
        with _workflows_lock:
            assert len(_ACTIVE_WORKFLOWS) == 5

    def test_concurrent_remove_workflow(self):
        with _workflows_lock:
            _ACTIVE_WORKFLOWS.clear()
            for i in range(20):
                _ACTIVE_WORKFLOWS[f"wf-rm-{i}"] = {
                    "workflow_id": f"wf-rm-{i}",
                    "status": "running",
                }
        errors = []

        def remove_workflow(idx):
            try:
                with _workflows_lock:
                    _ACTIVE_WORKFLOWS.pop(f"wf-rm-{idx}", None)
            except Exception as e:
                errors.append(e)

        with ThreadPoolExecutor(max_workers=20) as pool:
            futures = [pool.submit(remove_workflow, i) for i in range(20)]
            for f in as_completed(futures):
                f.result()
        assert not errors
        with _workflows_lock:
            assert len(_ACTIVE_WORKFLOWS) == 0


class TestAgentStatusThreadSafety:
    def test_concurrent_create_destroy(self):
        with _agents_lock:
            _AGENT_INSTANCES.clear()
        errors = []
        created_ids = []

        def create_agent(idx):
            try:
                aid = f"agent-test-{idx}"
                inst = _AgentInstance(
                    agent_id=aid,
                    agent_type="test",
                    capabilities=["coding"],
                )
                with _agents_lock:
                    _AGENT_INSTANCES[aid] = inst
                return aid
            except Exception as e:
                errors.append(e)
                return None

        with ThreadPoolExecutor(max_workers=20) as pool:
            futures = [pool.submit(create_agent, i) for i in range(20)]
            for f in as_completed(futures):
                aid = f.result()
                if aid:
                    created_ids.append(aid)

        def destroy_agent(aid):
            try:
                with _agents_lock:
                    _AGENT_INSTANCES.pop(aid, None)
            except Exception as e:
                errors.append(e)

        with ThreadPoolExecutor(max_workers=20) as pool:
            futures = [pool.submit(destroy_agent, aid) for aid in created_ids]
            for f in as_completed(futures):
                f.result()
        assert not errors
        with _agents_lock:
            assert len(_AGENT_INSTANCES) == 0

    def test_concurrent_assign_read(self):
        with _agents_lock:
            _AGENT_INSTANCES.clear()
            aid = "agent-assign-test"
            _AGENT_INSTANCES[aid] = _AgentInstance(
                agent_id=aid,
                agent_type="test",
                capabilities=["coding"],
                status="idle",
            )
        errors = []

        def assign_task():
            try:
                with _agents_lock:
                    inst = _AGENT_INSTANCES.get(aid)
                    if inst and inst.status == "idle":
                        inst.status = "busy"
                        inst.task = "test_task"
                        inst.history.append({"action": "assign", "task": "test_task", "timestamp": time.time()})
            except Exception as e:
                errors.append(e)

        def read_status():
            try:
                with _agents_lock:
                    _ = _AGENT_INSTANCES.get(aid)
            except Exception as e:
                errors.append(e)

        with ThreadPoolExecutor(max_workers=10) as pool:
            futures = []
            for _ in range(5):
                futures.append(pool.submit(assign_task))
            for _ in range(5):
                futures.append(pool.submit(read_status))
            for f in as_completed(futures):
                f.result()
        assert not errors


class TestResourceLoadStatusThreadSafety:
    def test_concurrent_cache_write(self):
        with _cache_lock:
            _RESOURCE_CACHE.clear()
        errors = []

        def write_cache(idx):
            try:
                key = f"res-{idx}"
                with _cache_lock:
                    _RESOURCE_CACHE[key] = {
                        "content": f"content-{idx}",
                        "cached_at": time.time(),
                        "access_count": 0,
                        "content_hash": f"hash-{idx}",
                        "ttl_seconds": 3600,
                        "source_path": None,
                    }
            except Exception as e:
                errors.append(e)

        with ThreadPoolExecutor(max_workers=20) as pool:
            futures = [pool.submit(write_cache, i) for i in range(100)]
            for f in as_completed(futures):
                f.result()
        assert not errors
        with _cache_lock:
            assert len(_RESOURCE_CACHE) == 100

    def test_concurrent_read_write_cache(self):
        with _cache_lock:
            _RESOURCE_CACHE.clear()
            for i in range(50):
                _RESOURCE_CACHE[f"existing-{i}"] = {
                    "content": f"content-{i}",
                    "cached_at": time.time(),
                    "access_count": 0,
                    "content_hash": f"hash-{i}",
                    "ttl_seconds": 3600,
                    "source_path": None,
                }
        errors = []

        def writer():
            try:
                for i in range(50):
                    with _cache_lock:
                        _RESOURCE_CACHE[f"new-{threading.current_thread().name}-{i}"] = {
                            "content": "new",
                            "cached_at": time.time(),
                            "access_count": 0,
                            "content_hash": "new_hash",
                            "ttl_seconds": 3600,
                            "source_path": None,
                        }
            except Exception as e:
                errors.append(e)

        def reader():
            try:
                for _ in range(50):
                    with _cache_lock:
                        _ = dict(_RESOURCE_CACHE)
            except Exception as e:
                errors.append(e)

        with ThreadPoolExecutor(max_workers=10) as pool:
            futures = []
            for _ in range(5):
                futures.append(pool.submit(writer))
            for _ in range(5):
                futures.append(pool.submit(reader))
            for f in as_completed(futures):
                f.result()
        assert not errors

    def test_concurrent_clear_cache(self):
        with _cache_lock:
            _RESOURCE_CACHE.clear()
            for i in range(50):
                _RESOURCE_CACHE[f"clear-{i}"] = {
                    "content": f"content-{i}",
                    "cached_at": time.time(),
                    "access_count": 0,
                    "content_hash": f"hash-{i}",
                    "ttl_seconds": 3600,
                    "source_path": None,
                }
        errors = []

        def clear_and_check():
            try:
                with _cache_lock:
                    count = len(_RESOURCE_CACHE)
                    _RESOURCE_CACHE.clear()
                assert count >= 0
            except Exception as e:
                errors.append(e)

        with ThreadPoolExecutor(max_workers=10) as pool:
            futures = [pool.submit(clear_and_check) for _ in range(10)]
            for f in as_completed(futures):
                f.result()
        assert not errors
        with _cache_lock:
            assert len(_RESOURCE_CACHE) == 0


class TestLockExistence:
    def test_server_health_lock_exists(self):
        assert isinstance(_metrics_lock, type(threading.Lock()))

    def test_workflow_lock_exists(self):
        assert isinstance(_workflows_lock, type(threading.Lock()))

    def test_agent_lock_exists(self):
        assert isinstance(_agents_lock, type(threading.Lock()))

    def test_cache_lock_exists(self):
        assert isinstance(_cache_lock, type(threading.Lock()))
