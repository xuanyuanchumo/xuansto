from __future__ import annotations

import asyncio
import inspect
from typing import Any

import pytest

from xuansto_mcp.core.degradation import (
    FALLBACK_MAP,
    DegradationExecutor,
    DegradationLevel,
    DegradationManager,
    _INLINE_FALLBACK_MAP,
    _LEVEL_ORDER,
    _RESOLVED_FALLBACK_MAP,
)

EXPECTED_TOOL_NAMES = [
    "skill_analyze",
    "knowledge_search",
    "knowledge_inject",
    "quality_gate_check",
    "spec_drift_detect",
    "security_scan",
    "code_simplify",
    "session_manage",
    "workflow_dispatch",
    "agent_status",
    "hook_manage",
    "resource_load_status",
    "resource_subscribe",
    "context_compress",
    "server_health",
    "decision_log",
    "token_budget",
    "project_init",
    "agent_manage",
    "metrics_report",
    "config_manage",
    "audit_query",
]


class TestFallbackMapCompleteness:
    def test_fallback_map_is_dict(self):
        assert isinstance(FALLBACK_MAP, dict)

    def test_fallback_map_covers_all_22_tools(self):
        assert len(FALLBACK_MAP) >= 22, f"FALLBACK_MAP should cover at least 22 tools, got {len(FALLBACK_MAP)}"
        for tool_name in EXPECTED_TOOL_NAMES:
            assert tool_name in FALLBACK_MAP, f"FALLBACK_MAP should contain fallback for '{tool_name}'"

    def test_fallback_map_entries_are_callable(self):
        for tool_name, fallback_fn in FALLBACK_MAP.items():
            assert callable(fallback_fn), f"FALLBACK_MAP['{tool_name}'] should be callable"

    def test_fallback_map_entries_are_async(self):
        for tool_name, fallback_fn in FALLBACK_MAP.items():
            assert inspect.iscoroutinefunction(fallback_fn), (
                f"FALLBACK_MAP['{tool_name}'] should be an async function"
            )


class TestResolvedFallbackMap:
    def test_resolved_fallback_map_is_dict(self):
        assert isinstance(_RESOLVED_FALLBACK_MAP, dict)

    def test_resolved_fallback_map_covers_all_tools(self):
        for tool_name in EXPECTED_TOOL_NAMES:
            assert tool_name in _RESOLVED_FALLBACK_MAP, (
                f"_RESOLVED_FALLBACK_MAP should contain '{tool_name}'"
            )


class TestInlineFallbackMap:
    def test_inline_fallback_map_is_dict(self):
        assert isinstance(_INLINE_FALLBACK_MAP, dict)

    def test_inline_fallback_map_entries_are_callable(self):
        for name, fn in _INLINE_FALLBACK_MAP.items():
            assert callable(fn), f"_INLINE_FALLBACK_MAP['{name}'] should be callable"


class TestDegradationLevels:
    def test_degradation_level_enum_values(self):
        assert DegradationLevel.L1_NORMAL.value == "L1_NORMAL"
        assert DegradationLevel.L2_LOCAL_SEMANTIC.value == "L2_LOCAL_SEMANTIC"
        assert DegradationLevel.L3_BM25_ONLY.value == "L3_BM25_ONLY"

    def test_level_order_is_l1_l2_l3(self):
        assert _LEVEL_ORDER == [
            DegradationLevel.L1_NORMAL,
            DegradationLevel.L2_LOCAL_SEMANTIC,
            DegradationLevel.L3_BM25_ONLY,
        ]

    def test_l1_less_than_l2(self):
        assert DegradationLevel.L1_NORMAL < DegradationLevel.L2_LOCAL_SEMANTIC

    def test_l2_less_than_l3(self):
        assert DegradationLevel.L2_LOCAL_SEMANTIC < DegradationLevel.L3_BM25_ONLY

    def test_l1_less_than_l3(self):
        assert DegradationLevel.L1_NORMAL < DegradationLevel.L3_BM25_ONLY


class TestDegradationManager:
    def test_manager_can_be_created(self):
        mgr = DegradationManager(health_interval=9999)
        assert mgr is not None

    def test_manager_register_component(self):
        mgr = DegradationManager(health_interval=9999)
        mgr.register_component(
            "test_component",
            check_fn=lambda: True,
            recover_fn=lambda: True,
            levels=["normal", "degraded", "unavailable"],
        )
        status = mgr.get_status()
        assert "test_component" in status["components"]

    def test_manager_initial_level_is_l1(self):
        mgr = DegradationManager(health_interval=9999)
        assert mgr.get_current_level() == "L1_NORMAL"

    def test_manager_degradation_chain_l1_to_l2(self):
        mgr = DegradationManager(health_interval=9999)
        mgr.register_component(
            "test_comp",
            check_fn=lambda: False,
            recover_fn=lambda: True,
            levels=["normal", "degraded", "unavailable"],
        )
        level = mgr.check_and_degrade("test_comp")
        assert level == "degraded"

    def test_manager_degradation_chain_l2_to_l3(self):
        mgr = DegradationManager(health_interval=9999)
        mgr.register_component(
            "test_comp2",
            check_fn=lambda: False,
            recover_fn=lambda: False,
            levels=["normal", "degraded", "unavailable"],
        )
        mgr.check_and_degrade("test_comp2")
        level = mgr.check_and_degrade("test_comp2")
        assert level == "unavailable"

    def test_manager_overall_level_reflects_worst(self):
        mgr = DegradationManager(health_interval=9999)
        mgr.register_component(
            "healthy_comp",
            check_fn=lambda: True,
            recover_fn=lambda: True,
            levels=["normal", "degraded", "unavailable"],
        )
        mgr.register_component(
            "failing_comp",
            check_fn=lambda: False,
            recover_fn=lambda: False,
            levels=["normal", "degraded", "unavailable"],
        )
        mgr.check_and_degrade("failing_comp")
        mgr.check_and_degrade("failing_comp")
        assert mgr.get_current_level() == "L3_BM25_ONLY"


class TestDegradationExecutor:
    def test_executor_can_be_created(self):
        executor = DegradationExecutor()
        assert executor is not None

    def test_executor_has_execute_method(self):
        executor = DegradationExecutor()
        assert hasattr(executor, "execute")
        assert callable(executor.execute)

    def test_executor_has_execute_sync_method(self):
        executor = DegradationExecutor()
        assert hasattr(executor, "execute_sync")
        assert callable(executor.execute_sync)

    def test_executor_fallback_map_covers_all_tools(self):
        executor = DegradationExecutor()
        fallback_map = executor._fallback_map
        for tool_name in EXPECTED_TOOL_NAMES:
            assert tool_name in fallback_map, f"Executor fallback map should contain '{tool_name}'"

    @pytest.mark.asyncio
    async def test_executor_returns_degraded_response(self):
        executor = DegradationExecutor(timeout=5)
        result = await executor.execute("unknown_tool_xyz")
        assert isinstance(result, dict)
        assert result.get("status") == "success" or result.get("degraded") is True or result.get("data", {}).get("degraded") is True


class TestFallbackFunctionSignatures:
    def test_skill_analyze_fallback_signature(self):
        from xuansto_mcp.core.degradation import skill_analyze_fallback
        sig = inspect.signature(skill_analyze_fallback)
        assert "skill_path" in sig.parameters

    def test_knowledge_search_fallback_signature(self):
        from xuansto_mcp.core.degradation import knowledge_search_fallback
        sig = inspect.signature(knowledge_search_fallback)
        assert "query" in sig.parameters

    def test_knowledge_inject_fallback_signature(self):
        from xuansto_mcp.core.degradation import knowledge_inject_fallback
        sig = inspect.signature(knowledge_inject_fallback)
        assert "action" in sig.parameters

    def test_quality_gate_fallback_signature(self):
        from xuansto_mcp.core.degradation import quality_gate_fallback
        sig = inspect.signature(quality_gate_fallback)
        assert "gate_ids" in sig.parameters

    def test_security_scan_fallback_signature(self):
        from xuansto_mcp.core.degradation import security_scan_fallback
        sig = inspect.signature(security_scan_fallback)
        assert "target" in sig.parameters

    def test_session_manage_fallback_signature(self):
        from xuansto_mcp.core.degradation import session_manage_fallback
        sig = inspect.signature(session_manage_fallback)
        assert "action" in sig.parameters

    def test_workflow_dispatch_fallback_signature(self):
        from xuansto_mcp.core.degradation import workflow_dispatch_fallback
        sig = inspect.signature(workflow_dispatch_fallback)
        assert "action" in sig.parameters

    def test_agent_status_fallback_signature(self):
        from xuansto_mcp.core.degradation import agent_status_fallback
        sig = inspect.signature(agent_status_fallback)
        assert "action" in sig.parameters

    def test_decision_log_fallback_signature(self):
        from xuansto_mcp.core.degradation import fallback_decision_log
        sig = inspect.signature(fallback_decision_log)
        assert "action" in sig.parameters

    def test_token_budget_fallback_signature(self):
        from xuansto_mcp.core.degradation import fallback_token_budget
        sig = inspect.signature(fallback_token_budget)
        assert "action" in sig.parameters

    def test_project_init_fallback_signature(self):
        from xuansto_mcp.core.degradation import fallback_project_init
        sig = inspect.signature(fallback_project_init)
        assert "action" in sig.parameters

    def test_config_manage_fallback_signature(self):
        from xuansto_mcp.core.degradation import config_manage_fallback
        sig = inspect.signature(config_manage_fallback)
        assert "action" in sig.parameters

    def test_audit_query_fallback_signature(self):
        from xuansto_mcp.core.degradation import audit_query_fallback
        sig = inspect.signature(audit_query_fallback)
        assert "tool_name" in sig.parameters or "limit" in sig.parameters
