from __future__ import annotations

import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from xuansto_mcp.core.errors import make_success_response, make_error_response
from xuansto_mcp.tools.resource_load_status import (
    PHASE_NAMES,
    PHASE_SKELETON,
    PHASE_FUNCTIONAL,
    PHASE_ENHANCED,
    PHASE_FULL,
    advance_phase,
    can_advance_to,
    _check_transition_conditions,
    _current_phase,
    _phase_lock,
    _TRANSITION_HISTORY,
    _PHASE_TOKEN_USAGE,
    _PHASE_TOKEN_USAGE_LOCK,
    _cache_lock,
    _resource_lru,
    _loaded_resources,
    _phase_state,
    _get_state_file,
    register as register_resource_load_status,
)


def _reset_phase_module():
    import xuansto_mcp.tools.resource_load_status as rls_mod
    with _phase_lock:
        rls_mod._current_phase = 0
    with _cache_lock:
        rls_mod._TRANSITION_HISTORY.clear()
        rls_mod._resource_lru.clear()
        rls_mod._loaded_resources = None
    with _PHASE_TOKEN_USAGE_LOCK:
        rls_mod._PHASE_TOKEN_USAGE.clear()
    rls_mod._phase_state["phase_metrics"] = {
        "skeleton": {"tokens_consumed": 0, "load_duration_ms": 0, "resources_loaded": 0},
        "functional": {"tokens_consumed": 0, "load_duration_ms": 0, "resources_loaded": 0},
        "enhanced": {"tokens_consumed": 0, "load_duration_ms": 0, "resources_loaded": 0},
        "full": {"tokens_consumed": 0, "load_duration_ms": 0, "resources_loaded": 0},
    }
    rls_mod._phase_state["phase_transition_timestamps"] = {
        "skeleton": None,
        "functional": None,
        "enhanced": None,
        "full": None,
    }
    rls_mod._phase_state["last_transition_at"] = None
    state_file = _get_state_file()
    if state_file.exists():
        try:
            state_file.write_text('{"phase": "skeleton"}', encoding="utf-8")
        except OSError:
            pass


@pytest.fixture(autouse=True)
def _reset_phase():
    _reset_phase_module()
    yield
    _reset_phase_module()


class TestSkillMCPIntegration:

    @pytest.mark.asyncio
    async def test_skill_analyze_tool_returns_analysis(self, tmp_path):
        skill_dir = tmp_path / "test_skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("---\nname: test\n---\nContent", encoding="utf-8")
        (skill_dir / ".skill-config.yaml").write_text("token_budget:\n  default: 100000\n", encoding="utf-8")

        from mcp.server.fastmcp import FastMCP
        mcp = FastMCP("test-skill-analyze")

        from xuansto_mcp.tools.skill_analyze import register as register_sa
        register_sa(mcp)

        handler = mcp._tool_manager._tools["skill_analyze"].fn
        result = await handler(skill_path=str(skill_dir), include_scripts=False, include_agents=False, depth="basic")

        assert isinstance(result, dict)
        assert "error" in result
        assert result["error"] is False
        assert "data" in result
        data = result["data"]
        assert "metadata" in data
        assert "structure" in data
        assert "depth_level" in data
        assert data["depth_level"] == 1

    @pytest.mark.asyncio
    async def test_knowledge_search_action_search_returns_results(self, tmp_path, patch_config):
        from mcp.server.fastmcp import FastMCP
        mcp = FastMCP("test-knowledge-search")

        from xuansto_mcp.tools.knowledge_search import register as register_ks
        register_ks(mcp)

        handler = mcp._tool_manager._tools["knowledge_search"].fn

        mock_result = MagicMock()
        mock_result.source = "test-doc"
        mock_result.content = "test content"
        mock_result.match_type = "keyword"
        mock_result.relevance = 0.8

        mock_engine = MagicMock()
        mock_engine.search.return_value = [mock_result]

        with patch("xuansto_mcp.tools.knowledge_search.get_search_engine", return_value=mock_engine):
            with patch("xuansto_mcp.tools.knowledge_search._ensure_knowledge_index"):
                result = await handler(
                    action="retrieve",
                    query="test query",
                    top_k=5,
                    search_type="keyword_only",
                )

        assert isinstance(result, dict)
        assert "error" in result
        assert result["error"] is False
        assert "data" in result
        data = result["data"]
        assert "results" in data
        assert "total" in data
        assert "strategy" in data
        assert data["total"] >= 0

    @pytest.mark.asyncio
    async def test_degradation_error_response_unified_format(self):
        from xuansto_mcp.core.errors import DegradationCoordinator, XuanstoMCPError

        coordinator = DegradationCoordinator()

        mock_handler = MagicMock(return_value=make_success_response({"degraded": True}))
        coordinator.register_handler("DEGRADATION", mock_handler)

        error = XuanstoMCPError(code="DEGRADATION", message="service degraded", details={"level": "L2"})

        with patch("xuansto_mcp.core.degradation.get_fallback") as mock_get_fallback:
            result = coordinator.handle(error, "test_tool")

        assert isinstance(result, dict)
        assert "error" in result

    @pytest.mark.asyncio
    async def test_skill_analyze_error_response_format(self, tmp_path):
        from mcp.server.fastmcp import FastMCP
        mcp = FastMCP("test-skill-analyze-err")

        from xuansto_mcp.tools.skill_analyze import register as register_sa
        register_sa(mcp)

        handler = mcp._tool_manager._tools["skill_analyze"].fn

        result = await handler(skill_path="/nonexistent/path/that/does/not/exist", depth="basic")

        assert isinstance(result, dict)
        assert result.get("error") is True
        assert "error_code" in result
        assert "message" in result


class TestProgressiveLoadingIntegration:

    def test_skeleton_to_full_phase_transition(self):
        import xuansto_mcp.tools.resource_load_status as rls_mod
        with _phase_lock:
            assert rls_mod._current_phase == 0

        result1 = advance_phase(PHASE_FUNCTIONAL, force=True)
        assert result1["success"] is True
        assert result1["from_phase"] == "skeleton"
        assert result1["to_phase"] == "functional"
        with _phase_lock:
            assert rls_mod._current_phase == 1

        result2 = advance_phase(PHASE_ENHANCED, force=True)
        assert result2["success"] is True
        assert result2["from_phase"] == "functional"
        assert result2["to_phase"] == "enhanced"
        with _phase_lock:
            assert rls_mod._current_phase == 2

        result3 = advance_phase(PHASE_FULL, force=True)
        assert result3["success"] is True
        assert result3["from_phase"] == "enhanced"
        assert result3["to_phase"] == "full"
        with _phase_lock:
            assert rls_mod._current_phase == 3

    def test_cannot_advance_to_same_or_lower_phase(self):
        import xuansto_mcp.tools.resource_load_status as rls_mod
        with _phase_lock:
            assert rls_mod._current_phase == 0

        result = advance_phase(0)
        assert result["success"] is False
        assert result["reason"] == "invalid_target"

        result = advance_phase(-1)
        assert result["success"] is False

    def test_transition_condition_check_at_each_phase(self):
        import xuansto_mcp.tools.resource_load_status as rls_mod

        check0 = _check_transition_conditions(0)
        assert "can_transition" in check0
        assert "conditions_met" in check0
        assert "missing" in check0
        assert "transition_key" in check0
        assert check0["transition_key"] == "skeleton_to_functional"

        advance_phase(PHASE_FUNCTIONAL, force=True)
        check1 = _check_transition_conditions(1)
        assert "can_transition" in check1
        assert check1["transition_key"] == "functional_to_enhanced"

        advance_phase(PHASE_ENHANCED, force=True)
        check2 = _check_transition_conditions(2)
        assert "can_transition" in check2
        assert check2["transition_key"] == "enhanced_to_full"

        advance_phase(PHASE_FULL, force=True)
        check3 = _check_transition_conditions(3)
        assert check3["can_transition"] is True
        assert check3["conditions_met"] is True

    def test_transition_feedback_newly_available_and_still_unavailable(self):
        import xuansto_mcp.tools.resource_load_status as rls_mod

        result = advance_phase(PHASE_FUNCTIONAL, force=True)
        assert result["success"] is True
        assert "newly_available" in result
        assert "still_unavailable" in result
        assert isinstance(result["newly_available"], list)
        assert isinstance(result["still_unavailable"], list)

        result2 = advance_phase(PHASE_ENHANCED, force=True)
        assert result2["success"] is True
        assert "newly_available" in result2
        assert "still_unavailable" in result2

        result3 = advance_phase(PHASE_FULL, force=True)
        assert result3["success"] is True
        assert "newly_available" in result3
        assert "still_unavailable" in result3
        assert result3["still_unavailable"] == []

    @pytest.mark.asyncio
    async def test_skeleton_phase_status_command(self, patch_config):
        import xuansto_mcp.tools.resource_load_status as rls_mod
        from mcp.server.fastmcp import FastMCP

        with _phase_lock:
            rls_mod._current_phase = 0

        state_file = _get_state_file()
        if state_file.exists():
            try:
                state_file.write_text('{"phase": "skeleton"}', encoding="utf-8")
            except OSError:
                pass

        mcp = FastMCP("test-rls-status")
        register_resource_load_status(mcp)

        handler = mcp._tool_manager._tools["resource_load_status"].fn

        result = await handler(action="status")

        assert isinstance(result, dict)
        assert result.get("error") is False
        data = result["data"]
        assert "current_phase_name" in data
        assert data["current_phase_name"] == "skeleton"
        assert "skeleton_info" in data
        skeleton_info = data["skeleton_info"]
        assert skeleton_info["phase"] == "skeleton"
        assert skeleton_info["phase_index"] == 0
        assert "available_commands" in skeleton_info
        assert isinstance(skeleton_info["available_commands"], list)
        assert len(skeleton_info["available_commands"]) > 0

    @pytest.mark.asyncio
    async def test_transition_check_action(self, patch_config):
        import xuansto_mcp.tools.resource_load_status as rls_mod
        from mcp.server.fastmcp import FastMCP

        with _phase_lock:
            rls_mod._current_phase = 0

        state_file = _get_state_file()
        if state_file.exists():
            try:
                state_file.write_text('{"phase": "skeleton"}', encoding="utf-8")
            except OSError:
                pass

        mcp = FastMCP("test-rls-tc")
        register_resource_load_status(mcp)

        handler = mcp._tool_manager._tools["resource_load_status"].fn

        result = await handler(action="transition_check")

        assert isinstance(result, dict)
        assert result.get("error") is False
        data = result["data"]
        assert data["action"] == "transition_check"
        assert data["current_phase"] == "skeleton"
        assert data["current_phase_index"] == 0
        assert "can_advance" in data
        assert "conditions_met" in data
        assert "next_phase" in data
        assert data["next_phase"] == "functional"
