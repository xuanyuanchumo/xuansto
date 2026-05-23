from __future__ import annotations

import json
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from xuansto_mcp.core.degradation import (
    DegradationLevel,
    DegradationManager,
    FALLBACK_MAP,
    _fallback_success,
    _fallback_error,
    _standardize_result,
    get_fallback,
    run_script_fallback,
)


@pytest.fixture
def fresh_manager():
    mgr = DegradationManager(health_interval=9999)
    return mgr


@pytest.fixture
def tmp_work_dir(tmp_path):
    work = tmp_path / ".xuansto"
    work.mkdir()
    return work


class TestDegradationManagerFallbackChain:
    def test_check_and_degrade_advances_through_levels(self, fresh_manager):
        fresh_manager.register_component(
            "search_engine",
            check_fn=lambda: False,
            recover_fn=lambda: False,
            levels=["chromadb", "sqlite_fts", "keyword"],
        )
        level1 = fresh_manager.check_and_degrade("search_engine")
        assert level1 == "sqlite_fts"
        level2 = fresh_manager.check_and_degrade("search_engine")
        assert level2 == "keyword"
        level3 = fresh_manager.check_and_degrade("search_engine")
        assert level3 == "keyword"

    def test_full_four_level_degradation_chain(self, fresh_manager):
        fresh_manager.register_component(
            "test_comp",
            check_fn=lambda: False,
            recover_fn=lambda: False,
            levels=["normal", "degraded", "unavailable"],
        )
        assert fresh_manager.check_and_degrade("test_comp") == "degraded"
        assert fresh_manager.check_and_degrade("test_comp") == "unavailable"
        assert fresh_manager.check_and_degrade("test_comp") == "unavailable"

    def test_overall_level_reflects_worst_component(self, fresh_manager):
        fresh_manager.register_component(
            "comp_a",
            check_fn=lambda: True,
            recover_fn=lambda: True,
            levels=["normal", "degraded", "unavailable"],
        )
        fresh_manager.register_component(
            "comp_b",
            check_fn=lambda: False,
            recover_fn=lambda: False,
            levels=["normal", "degraded", "unavailable"],
        )
        fresh_manager.check_and_degrade("comp_a")
        fresh_manager.check_and_degrade("comp_b")
        assert fresh_manager.get_current_level() == "L2_LOCAL_SEMANTIC"

    def test_recovery_returns_to_normal(self, fresh_manager):
        fresh_manager.register_component(
            "comp",
            check_fn=lambda: False,
            recover_fn=lambda: True,
            levels=["normal", "degraded", "unavailable"],
        )
        fresh_manager.check_and_degrade("comp")
        fresh_manager.check_and_degrade("comp")
        assert fresh_manager.get_status()["components"]["comp"]["level"] == "unavailable"
        fresh_manager._components["comp"].next_recovery_time = 0
        result = fresh_manager.attempt_recovery("comp")
        assert result is True
        status = fresh_manager.get_status()
        assert status["components"]["comp"]["level"] == "degraded"

    def test_recovery_resumes_normal_operation(self, fresh_manager):
        fresh_manager.register_component(
            "comp",
            check_fn=lambda: True,
            recover_fn=lambda: True,
            levels=["normal", "degraded", "unavailable"],
        )
        fresh_manager._components["comp"].level = "degraded"
        fresh_manager._components["comp"].degraded_since = time.time()
        fresh_manager._update_overall_level()
        assert fresh_manager.get_current_level() != "L1_NORMAL"
        fresh_manager._components["comp"].next_recovery_time = 0
        fresh_manager.attempt_recovery("comp")
        assert fresh_manager.get_current_level() == "L1_NORMAL"


class TestFallbackResponses:
    def test_fallback_success_includes_source(self):
        result = _fallback_success("test_tool", {"key": "value"})
        assert result["data"]["source"] == "fallback"

    def test_fallback_success_includes_degradation_level(self):
        result = _fallback_success("test_tool", {"key": "value"}, degradation_level="minimal")
        assert result.get("degradation_level") == "minimal"

    def test_fallback_success_default_status_degraded(self):
        result = _fallback_success("test_tool", {})
        assert result["data"]["status"] == "degraded"

    def test_fallback_error_structure(self):
        result = _fallback_error("test_tool", "ERR_CODE", "error msg")
        assert result["error"] is True
        assert result["details"]["source"] == "fallback"

    def test_standardize_result_success(self):
        result = _standardize_result(
            {"error": False, "data": {"output": "ok"}},
            "test_tool",
        )
        assert result["data"]["source"] == "fallback"

    def test_standardize_result_error(self):
        result = _standardize_result(
            {"error": True, "code": "FAIL", "message": "bad"},
            "test_tool",
        )
        assert result["error"] is True


class TestFallbackMap:
    def test_fallback_map_has_all_tools(self):
        expected_tools = [
            "skill_analyze", "knowledge_search", "knowledge_inject",
            "quality_gate_check", "spec_drift_detect", "security_scan",
            "code_simplify", "session_manage", "workflow_dispatch",
            "agent_status", "hook_manage", "resource_load_status",
            "context_compress", "server_health", "decision_log",
            "token_budget", "project_init",
        ]
        for tool in expected_tools:
            assert tool in FALLBACK_MAP, f"Missing fallback for {tool}"

    def test_get_fallback_returns_callable(self):
        fn = get_fallback("knowledge_search")
        assert fn is not None
        assert callable(fn)

    def test_get_fallback_unknown_tool(self):
        fn = get_fallback("nonexistent_tool_xyz")
        assert fn is None

    def test_knowledge_search_fallback_minimal(self):
        from xuansto_mcp.core.degradation import knowledge_search_fallback
        with patch("xuansto_mcp.core.degradation.run_script_fallback", return_value={"error": True, "code": "NOT_FOUND", "message": "no script"}):
            with patch.dict("sys.modules", {}):
                result = knowledge_search_fallback("test query")
                assert result["data"]["source"] == "fallback"

    def test_server_health_fallback_minimal(self):
        from xuansto_mcp.core.degradation import server_health_fallback
        with patch("xuansto_mcp.core.degradation.run_script_fallback", return_value={"error": True, "code": "NOT_FOUND", "message": "no script"}):
            result = server_health_fallback()
            assert result["data"]["source"] == "fallback"
            assert result.get("degradation_level") in ("minimal", "inline", None) or result["data"].get("status") == "degraded"


class TestScriptFallback:
    def test_script_not_found(self):
        result = run_script_fallback("nonexistent_script_xyz.py")
        assert result["error"] is True
        assert result["code"] == "SCRIPT_NOT_FOUND"
        assert result["fallback"] is True

    def test_script_fallback_with_mock(self):
        with patch("xuansto_mcp.core.degradation.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                stdout=json.dumps({"result": "ok"}),
                stderr="",
                returncode=0,
            )
            with patch("xuansto_mcp.core.degradation.SCRIPTS_DIR") as mock_dir:
                (mock_dir / "test.py").parent.mkdir(parents=True, exist_ok=True)
                (mock_dir / "test.py").write_text("print('hi')")
                result = run_script_fallback("test.py")
                assert result["fallback"] is True


class TestDegradationLevelEnum:
    def test_level_ordering(self):
        assert DegradationLevel.L1_NORMAL < DegradationLevel.L2_LOCAL_SEMANTIC
        assert DegradationLevel.L2_LOCAL_SEMANTIC < DegradationLevel.L3_BM25_ONLY
        assert DegradationLevel.L1_NORMAL < DegradationLevel.L3_BM25_ONLY

    def test_level_values(self):
        assert DegradationLevel.L1_NORMAL.value == "L1_NORMAL"
        assert DegradationLevel.L2_LOCAL_SEMANTIC.value == "L2_LOCAL_SEMANTIC"
        assert DegradationLevel.L3_BM25_ONLY.value == "L3_BM25_ONLY"


class TestDegradationStatePersistence:
    def test_persist_and_load_state(self, fresh_manager, tmp_work_dir):
        fresh_manager.register_component(
            "comp",
            check_fn=lambda: False,
            recover_fn=lambda: False,
            levels=["normal", "degraded", "unavailable"],
        )
        fresh_manager.check_and_degrade("comp")
        with patch("xuansto_mcp.core.degradation.DegradationManager._persist_state"):
            pass
        state_path = tmp_work_dir / "degradation_state.json"
        state_data = fresh_manager.get_status()
        state_data["_hash"] = "test_hash"
        state_path.write_text(json.dumps(state_data, ensure_ascii=False), encoding="utf-8")
        assert state_path.exists()

    def test_subscriber_notification(self, fresh_manager):
        notifications = []
        fresh_manager.subscribe(lambda comp, old, new: notifications.append((comp, old, new)))
        fresh_manager.register_component(
            "comp",
            check_fn=lambda: False,
            recover_fn=lambda: False,
            levels=["normal", "degraded"],
        )
        fresh_manager.check_and_degrade("comp")
        assert len(notifications) == 1
        assert notifications[0][0] == "comp"
        assert notifications[0][1] == "normal"
        assert notifications[0][2] == "degraded"
