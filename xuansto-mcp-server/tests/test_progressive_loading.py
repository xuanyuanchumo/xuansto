from __future__ import annotations

import json
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from xuansto_mcp.tools.resource_load_status import (
    PHASE_TOKEN_BUDGETS,
    PHASE_NAMES,
    PHASE_AVAILABLE_FUNCTIONS,
    PHASE_RESOURCE_MAP,
    PHASE_SKELETON,
    PHASE_FUNCTIONAL,
    PHASE_ENHANCED,
    PHASE_FULL,
    advance_phase,
    degrade_phase,
    check_token_budget,
    auto_advance_on_command,
    can_advance_to,
    require_phase,
    _current_phase,
    _phase_lock,
    _PHASE_TOKEN_USAGE,
    _PHASE_TOKEN_USAGE_LOCK,
    _TRANSITION_HISTORY,
    _cache_lock,
    DisclosureTransition,
)
from xuansto_mcp.models.schemas import DisclosureTransition as DisclosureTransitionSchema


@pytest.fixture(autouse=True)
def reset_phase_state():
    import xuansto_mcp.tools.resource_load_status as mod
    with _phase_lock:
        original = mod._current_phase
        mod._current_phase = 0
    with _cache_lock:
        mod._TRANSITION_HISTORY.clear()
    with _PHASE_TOKEN_USAGE_LOCK:
        mod._PHASE_TOKEN_USAGE.clear()
    yield
    with _phase_lock:
        mod._current_phase = original


@pytest.fixture
def tmp_work_dir(tmp_path):
    work = tmp_path / ".xuansto"
    work.mkdir()
    return work


class TestPhaseAutoAdvance:
    def test_phase_0_to_1_auto_advance(self):
        result = auto_advance_on_command()
        assert result is not None
        assert result["success"] is True
        assert result["from_phase"] == "skeleton"
        assert result["to_phase"] == "functional"

    def test_auto_advance_only_from_phase_0(self):
        import xuansto_mcp.tools.resource_load_status as mod
        with _phase_lock:
            mod._current_phase = 1
        result = auto_advance_on_command()
        assert result is None


class TestPhaseExplicitAdvance:
    def test_phase_1_to_2_advance(self):
        import xuansto_mcp.tools.resource_load_status as mod
        with _phase_lock:
            mod._current_phase = 1
        result = advance_phase(2)
        assert result["success"] is True
        assert result["from_phase"] == "functional"
        assert result["to_phase"] == "enhanced"

    def test_phase_2_to_3_advance(self):
        import xuansto_mcp.tools.resource_load_status as mod
        with _phase_lock:
            mod._current_phase = 2
        result = advance_phase(3)
        assert result["success"] is True
        assert result["to_phase"] == "full"

    def test_cannot_advance_backwards(self):
        import xuansto_mcp.tools.resource_load_status as mod
        with _phase_lock:
            mod._current_phase = 2
        result = advance_phase(1)
        assert result["success"] is False

    def test_cannot_advance_to_same_phase(self):
        import xuansto_mcp.tools.resource_load_status as mod
        with _phase_lock:
            mod._current_phase = 1
        result = advance_phase(1)
        assert result["success"] is False

    def test_cannot_advance_to_invalid_phase(self):
        result = advance_phase(5)
        assert result["success"] is False
        result = advance_phase(-1)
        assert result["success"] is False


class TestPhaseDegradation:
    def test_degrade_phase_reduces_by_one(self):
        import xuansto_mcp.tools.resource_load_status as mod
        with _phase_lock:
            mod._current_phase = 2
        result = degrade_phase()
        assert result["success"] is True
        assert result["from_phase"] == "enhanced"
        assert result["to_phase"] == "functional"

    def test_degrade_at_minimum_fails(self):
        import xuansto_mcp.tools.resource_load_status as mod
        with _phase_lock:
            mod._current_phase = 0
        result = degrade_phase()
        assert result["success"] is False
        assert result["reason"] == "already_at_minimum"

    def test_token_budget_exceeded_triggers_degradation(self):
        import xuansto_mcp.tools.resource_load_status as mod
        with _phase_lock:
            mod._current_phase = 2
        with _PHASE_TOKEN_USAGE_LOCK:
            mod._PHASE_TOKEN_USAGE[2] = {"estimated_tokens": 9000, "resource_count": 5}
        result = check_token_budget()
        assert result["budget_exceeded_80pct"] is True
        assert "degradation" in result


class TestTokenBudgets:
    def test_phase_token_budgets_defined(self):
        assert PHASE_TOKEN_BUDGETS[0] == 2000
        assert PHASE_TOKEN_BUDGETS[1] == 5000
        assert PHASE_TOKEN_BUDGETS[2] == 10000
        assert PHASE_TOKEN_BUDGETS[3] == 20000

    def test_check_token_budget_within_limit(self):
        import xuansto_mcp.tools.resource_load_status as mod
        with _phase_lock:
            mod._current_phase = 1
        with _PHASE_TOKEN_USAGE_LOCK:
            mod._PHASE_TOKEN_USAGE[1] = {"estimated_tokens": 1000, "resource_count": 2}
        result = check_token_budget()
        assert result["budget_exceeded_80pct"] is False
        assert "degradation" not in result

    def test_check_token_budget_exactly_at_threshold(self):
        import xuansto_mcp.tools.resource_load_status as mod
        with _phase_lock:
            mod._current_phase = 1
        budget = PHASE_TOKEN_BUDGETS[1]
        with _PHASE_TOKEN_USAGE_LOCK:
            mod._PHASE_TOKEN_USAGE[1] = {"estimated_tokens": int(budget * 0.8), "resource_count": 10}
        result = check_token_budget()
        assert result["budget_exceeded_80pct"] is True


class TestDisclosureTransition:
    def test_disclosure_transition_structure(self):
        dt = DisclosureTransitionSchema(
            from_phase="skeleton",
            to_phase="functional",
            resources_affected=["resource1", "resource2"],
            status="completed",
        )
        assert dt.from_phase == "skeleton"
        assert dt.to_phase == "functional"
        assert len(dt.resources_affected) == 2
        assert dt.status == "completed"

    def test_disclosure_transition_with_state_machine_fields(self):
        dt = DisclosureTransitionSchema(
            current_phase="skeleton",
            target_phase="enhanced",
            required_resources=["res1", "res2"],
            estimated_tokens=5000,
            available_alternatives=["functional"],
            transition_hint="upgrade hint",
        )
        assert dt.current_phase == "skeleton"
        assert dt.target_phase == "enhanced"
        assert dt.estimated_tokens == 5000

    def test_require_phase_returns_transition(self):
        import xuansto_mcp.tools.resource_load_status as mod
        with _phase_lock:
            mod._current_phase = 0
        transition = require_phase(2)
        assert transition is not None
        assert isinstance(transition, DisclosureTransitionSchema)
        assert transition.current_phase == "skeleton"
        assert transition.target_phase == "enhanced"

    def test_require_phase_returns_none_when_satisfied(self):
        import xuansto_mcp.tools.resource_load_status as mod
        with _phase_lock:
            mod._current_phase = 3
        transition = require_phase(2)
        assert transition is None


class TestCanAdvanceTo:
    def test_can_advance_to_higher_phase(self):
        import xuansto_mcp.tools.resource_load_status as mod
        with _phase_lock:
            mod._current_phase = 0
        assert can_advance_to(1) is True
        assert can_advance_to(2) is True
        assert can_advance_to(3) is True

    def test_cannot_advance_to_lower_or_same(self):
        import xuansto_mcp.tools.resource_load_status as mod
        with _phase_lock:
            mod._current_phase = 2
        assert can_advance_to(2) is False
        assert can_advance_to(1) is False
        assert can_advance_to(0) is False

    def test_cannot_advance_to_invalid(self):
        assert can_advance_to(-1) is False
        assert can_advance_to(5) is False


class TestPhaseAvailableFunctions:
    def test_phase_0_restrictions(self):
        funcs = PHASE_AVAILABLE_FUNCTIONS[0]
        assert funcs["command_routing"] is True
        assert funcs["command_execution"] is False
        assert funcs["knowledge_search"] is False

    def test_phase_1_unlocks_execution(self):
        funcs = PHASE_AVAILABLE_FUNCTIONS[1]
        assert funcs["command_execution"] is True
        assert funcs["quality_gates"] is True
        assert funcs["knowledge_search"] is False

    def test_phase_2_unlocks_knowledge(self):
        funcs = PHASE_AVAILABLE_FUNCTIONS[2]
        assert funcs["knowledge_search"] is True
        assert funcs["reference_docs"] is True

    def test_phase_3_full_access(self):
        funcs = PHASE_AVAILABLE_FUNCTIONS[3]
        assert funcs["full_scripts"] is True
        assert all(funcs.values())


class TestPhaseResourceMap:
    def test_phase_0_has_minimal_resources(self):
        assert len(PHASE_RESOURCE_MAP[0]) >= 1

    def test_resources_increase_with_phase(self):
        for i in range(3):
            assert len(PHASE_RESOURCE_MAP[i + 1]) >= len(PHASE_RESOURCE_MAP[i])

    def test_phase_names_defined(self):
        assert PHASE_NAMES[0] == "skeleton"
        assert PHASE_NAMES[1] == "functional"
        assert PHASE_NAMES[2] == "enhanced"
        assert PHASE_NAMES[3] == "full"


class TestTransitionHistory:
    def test_transition_recorded_on_advance(self):
        import xuansto_mcp.tools.resource_load_status as mod
        with _phase_lock:
            mod._current_phase = 0
        advance_phase(1)
        with _cache_lock:
            history = list(mod._TRANSITION_HISTORY)
        assert len(history) >= 1
        last = history[-1]
        assert last["from_phase"] == "skeleton"
        assert last["to_phase"] == "functional"
        assert last["status"] == "completed"

    def test_transition_recorded_on_degrade(self):
        import xuansto_mcp.tools.resource_load_status as mod
        with _phase_lock:
            mod._current_phase = 2
        degrade_phase()
        with _cache_lock:
            history = list(mod._TRANSITION_HISTORY)
        assert len(history) >= 1
        last = history[-1]
        assert last["status"] == "completed"
