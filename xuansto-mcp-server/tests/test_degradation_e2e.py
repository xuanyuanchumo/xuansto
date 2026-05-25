from __future__ import annotations

import json
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from xuansto_mcp.core.degradation import (
    DegradationManager,
    DegradationExecutor,
    FALLBACK_MAP,
    get_fallback,
    _fallback_success,
    _fallback_error,
    _standardize_result,
)
from xuansto_mcp.core.errors import make_error_response, make_success_response, XuanstoMCPError
from xuansto_mcp.core.audit_logger import AuditLogger


@pytest.fixture
def audit_log_dir(tmp_path):
    return tmp_path / "audit"


@pytest.fixture
def audit_logger(audit_log_dir):
    return AuditLogger(audit_log_dir)


@pytest.fixture
def fresh_manager():
    mgr = DegradationManager(health_interval=9999)
    return mgr


def _bypass_backoff(mgr, component_name):
    state = mgr._components[component_name]
    state.next_recovery_time = 0.0


class TestDegradationChainOrder:

    def test_mcp_tool_to_script_to_inline_to_error(self, fresh_manager):
        call_chain = []

        def failing_check():
            call_chain.append("mcp_check")
            return False

        def failing_recover():
            call_chain.append("mcp_recover")
            return False

        fresh_manager.register_component(
            "test_component",
            check_fn=failing_check,
            recover_fn=failing_recover,
            levels=["normal", "degraded", "unavailable"],
        )

        level = fresh_manager.check_and_degrade("test_component")
        assert level == "degraded"

        level = fresh_manager.check_and_degrade("test_component")
        assert level == "unavailable"

    def test_degradation_executor_fallback_chain(self, tmp_path):
        executor = DegradationExecutor(scripts_dir=tmp_path / "nonexistent", timeout=5)

        mock_fallback = MagicMock(return_value=make_success_response({
            "tool": "test_tool",
            "status": "degraded",
            "degraded": True,
        }))

        with patch.dict(FALLBACK_MAP, {"test_tool": mock_fallback}):
            executor._fallback_map = {"test_tool": mock_fallback}
            result = executor.execute_sync("test_tool", query="test")

        assert isinstance(result, dict)
        assert result.get("degraded") is True

    def test_degradation_executor_minimal_response(self):
        executor = DegradationExecutor(timeout=5)
        executor._fallback_map = {}

        result = executor.execute_sync("nonexistent_tool", param="value")

        assert isinstance(result, dict)
        data = result.get("data", {})
        assert data.get("degraded") is True
        assert data.get("status") == "unavailable"

    def test_degradation_manager_component_registration(self, fresh_manager):
        fresh_manager.register_component(
            "search_engine",
            check_fn=lambda: True,
            recover_fn=lambda: True,
            levels=["chromadb", "sqlite_fts", "keyword"],
        )

        status = fresh_manager.get_status()
        assert "search_engine" in status["components"]
        assert status["components"]["search_engine"]["level"] == "chromadb"

    def test_degradation_manager_subscriber_notification(self, fresh_manager):
        notifications = []

        def on_change(component, old_level, new_level):
            notifications.append({
                "component": component,
                "old_level": old_level,
                "new_level": new_level,
            })

        fresh_manager.subscribe(on_change)

        fresh_manager.register_component(
            "test_comp",
            check_fn=lambda: False,
            recover_fn=lambda: False,
            levels=["normal", "degraded", "unavailable"],
        )

        fresh_manager.check_and_degrade("test_comp")

        assert len(notifications) >= 1
        assert notifications[0]["component"] == "test_comp"
        assert notifications[0]["old_level"] == "normal"
        assert notifications[0]["new_level"] == "degraded"


class TestAuditLogDegradationEvents:

    def test_audit_log_records_failure(self, audit_logger, audit_log_dir):
        audit_logger.log(
            tool_name="skill_analyze",
            params={"skill_path": "/test"},
            result={"error": True, "error_code": "DEGRADATION"},
            latency_ms=150.5,
            success=False,
        )

        log_path = audit_log_dir / "audit_log.jsonl"
        assert log_path.exists()

        entries = audit_logger.query()
        assert len(entries) >= 1

        failure_entries = [e for e in entries if e.get("success") is False]
        assert len(failure_entries) >= 1
        assert failure_entries[0]["tool"] == "skill_analyze"
        assert failure_entries[0]["success"] is False

    def test_audit_log_records_degraded_tool_call(self, audit_logger, audit_log_dir):
        degraded_result = make_success_response({
            "tool": "knowledge_search",
            "degraded": True,
            "status": "degraded",
        })

        audit_logger.log(
            tool_name="knowledge_search",
            params={"query": "test", "action": "search"},
            result=degraded_result,
            latency_ms=200.0,
            success=False,
        )

        entries = audit_logger.query(tool_name="knowledge_search")
        assert len(entries) >= 1
        assert entries[0]["success"] is False

    def test_audit_log_persists_to_file(self, audit_logger, audit_log_dir):
        for i in range(5):
            audit_logger.log(
                tool_name=f"tool_{i}",
                params={"idx": i},
                result={"error": False},
                latency_ms=10.0 * i,
                success=True,
            )

        log_path = audit_log_dir / "audit_log.jsonl"
        lines = log_path.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 5

        for line in lines:
            entry = json.loads(line)
            assert "timestamp" in entry
            assert "tool" in entry
            assert "success" in entry


class TestDegradationRecovery:

    def test_recovery_after_degradation(self, fresh_manager):
        healthy = [False]

        def check_fn():
            return healthy[0]

        def recover_fn():
            healthy[0] = True
            return True

        fresh_manager.register_component(
            "recoverable_component",
            check_fn=check_fn,
            recover_fn=recover_fn,
            levels=["normal", "degraded", "unavailable"],
        )

        level = fresh_manager.check_and_degrade("recoverable_component")
        assert level == "degraded"

        level = fresh_manager.check_and_degrade("recoverable_component")
        assert level == "unavailable"

        _bypass_backoff(fresh_manager, "recoverable_component")
        recovered = fresh_manager.attempt_recovery("recoverable_component")
        assert recovered is True

        status = fresh_manager.get_status()
        comp = status["components"]["recoverable_component"]
        assert comp["level"] == "degraded"

        _bypass_backoff(fresh_manager, "recoverable_component")
        fresh_manager.attempt_recovery("recoverable_component")
        status = fresh_manager.get_status()
        comp = status["components"]["recoverable_component"]
        assert comp["level"] == "normal"

    def test_recovery_backoff_timing(self, fresh_manager):
        call_count = [0]

        def check_fn():
            return False

        def recover_fn():
            call_count[0] += 1
            return False

        fresh_manager.register_component(
            "backoff_component",
            check_fn=check_fn,
            recover_fn=recover_fn,
            levels=["normal", "degraded"],
        )

        fresh_manager.check_and_degrade("backoff_component")

        _bypass_backoff(fresh_manager, "backoff_component")
        result = fresh_manager.attempt_recovery("backoff_component")
        assert result is False

        status = fresh_manager.get_status()
        comp = status["components"]["backoff_component"]
        assert comp["recovery_attempts"] >= 1
        assert comp["next_recovery_time"] > time.time()

    def test_recovery_backoff_blocks_early_attempt(self, fresh_manager):
        fresh_manager.register_component(
            "blocked_component",
            check_fn=lambda: False,
            recover_fn=lambda: True,
            levels=["normal", "degraded"],
        )

        fresh_manager.check_and_degrade("blocked_component")

        result = fresh_manager.attempt_recovery("blocked_component")
        assert result is False

    def test_recovery_at_normal_level_returns_true(self, fresh_manager):
        fresh_manager.register_component(
            "healthy_component",
            check_fn=lambda: True,
            recover_fn=lambda: True,
            levels=["normal", "degraded"],
        )

        result = fresh_manager.attempt_recovery("healthy_component")
        assert result is True

    def test_full_degradation_recovery_cycle(self, fresh_manager):
        health_state = {"healthy": False}

        def check_fn():
            return health_state["healthy"]

        def recover_fn():
            health_state["healthy"] = True
            return True

        fresh_manager.register_component(
            "cycle_component",
            check_fn=check_fn,
            recover_fn=recover_fn,
            levels=["normal", "degraded", "unavailable"],
        )

        fresh_manager.check_and_degrade("cycle_component")
        fresh_manager.check_and_degrade("cycle_component")

        status = fresh_manager.get_status()
        assert status["components"]["cycle_component"]["level"] == "unavailable"

        _bypass_backoff(fresh_manager, "cycle_component")
        fresh_manager.attempt_recovery("cycle_component")
        status = fresh_manager.get_status()
        assert status["components"]["cycle_component"]["level"] == "degraded"

        _bypass_backoff(fresh_manager, "cycle_component")
        fresh_manager.attempt_recovery("cycle_component")
        status = fresh_manager.get_status()
        assert status["components"]["cycle_component"]["level"] == "normal"
        assert status["components"]["cycle_component"]["degraded_since"] is None

    def test_get_fallback_returns_function(self):
        fn = get_fallback("skill_analyze")
        assert fn is not None
        assert callable(fn)

    def test_get_fallback_unknown_tool(self):
        fn = get_fallback("totally_unknown_tool_xyz")
        assert fn is None
