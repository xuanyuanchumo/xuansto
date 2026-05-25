from __future__ import annotations

from unittest.mock import patch

import pytest

from xuansto_mcp.tools.resource_load_status import PHASE_NAME_TOKEN_BUDGET
from xuansto_mcp.tools.token_budget import (
    PHASE_TOKEN_BUDGET_MAP,
    _set_budget_from_phase,
    _set_budget,
    _inline_token_budget,
)


class TestPhaseNameTokenBudgetMapping:
    def test_skeleton_budget(self):
        assert PHASE_NAME_TOKEN_BUDGET["skeleton"] == 2000

    def test_functional_budget(self):
        assert PHASE_NAME_TOKEN_BUDGET["functional"] == 5000

    def test_enhanced_budget(self):
        assert PHASE_NAME_TOKEN_BUDGET["enhanced"] == 10000

    def test_full_budget(self):
        assert PHASE_NAME_TOKEN_BUDGET["full"] == 20000

    def test_mapping_has_four_entries(self):
        assert len(PHASE_NAME_TOKEN_BUDGET) == 4

    def test_budgets_increase_monotonically(self):
        phases = ["skeleton", "functional", "enhanced", "full"]
        for i in range(len(phases) - 1):
            assert PHASE_NAME_TOKEN_BUDGET[phases[i]] < PHASE_NAME_TOKEN_BUDGET[phases[i + 1]]


class TestSetFromPhaseAction:
    @pytest.fixture
    def budget_file(self, tmp_path):
        return tmp_path / "token_budget.json"

    def test_set_from_phase_skeleton(self, budget_file):
        with patch("xuansto_mcp.tools.token_budget.BUDGET_FILE", budget_file), \
             patch("xuansto_mcp.tools.token_budget.notify"):
            result = _set_budget_from_phase("skeleton")
            assert result["total_budget"] == 2000
            assert result["phase"] == "skeleton"
            assert result["budget_source"] == "phase_mapping"

    def test_set_from_phase_functional(self, budget_file):
        with patch("xuansto_mcp.tools.token_budget.BUDGET_FILE", budget_file), \
             patch("xuansto_mcp.tools.token_budget.notify"):
            result = _set_budget_from_phase("functional")
            assert result["total_budget"] == 5000
            assert result["phase"] == "functional"

    def test_set_from_phase_enhanced(self, budget_file):
        with patch("xuansto_mcp.tools.token_budget.BUDGET_FILE", budget_file), \
             patch("xuansto_mcp.tools.token_budget.notify"):
            result = _set_budget_from_phase("enhanced")
            assert result["total_budget"] == 10000
            assert result["phase"] == "enhanced"

    def test_set_from_phase_full(self, budget_file):
        with patch("xuansto_mcp.tools.token_budget.BUDGET_FILE", budget_file), \
             patch("xuansto_mcp.tools.token_budget.notify"):
            result = _set_budget_from_phase("full")
            assert result["total_budget"] == 20000
            assert result["phase"] == "full"

    def test_set_from_phase_invalid_returns_error(self, budget_file):
        with patch("xuansto_mcp.tools.token_budget.BUDGET_FILE", budget_file), \
             patch("xuansto_mcp.tools.token_budget.notify"):
            result = _set_budget_from_phase("nonexistent")
            assert result.get("error") is True
            assert "Unknown phase" in result.get("message", "")

    def test_set_from_phase_empty_string_returns_error(self, budget_file):
        with patch("xuansto_mcp.tools.token_budget.BUDGET_FILE", budget_file), \
             patch("xuansto_mcp.tools.token_budget.notify"):
            result = _set_budget_from_phase("")
            assert result.get("error") is True


class TestInlineTokenBudgetSetFromPhase:
    @pytest.fixture
    def budget_file(self, tmp_path):
        return tmp_path / "token_budget.json"

    def test_inline_set_from_phase_skeleton(self, budget_file):
        with patch("xuansto_mcp.tools.token_budget.BUDGET_FILE", budget_file), \
             patch("xuansto_mcp.tools.token_budget.notify"):
            result = _inline_token_budget("set_from_phase", phase="skeleton")
            assert result["total_budget"] == 2000
            assert result["phase"] == "skeleton"

    def test_inline_set_from_phase_missing_phase_param(self, budget_file):
        with patch("xuansto_mcp.tools.token_budget.BUDGET_FILE", budget_file), \
             patch("xuansto_mcp.tools.token_budget.notify"):
            result = _inline_token_budget("set_from_phase")
            assert result.get("error") is True
            assert "phase" in result.get("message", "")


class TestPhaseTokenBudgetMapConsistency:
    def test_phase_token_budget_map_matches_phase_name_token_budget(self):
        assert PHASE_TOKEN_BUDGET_MAP == PHASE_NAME_TOKEN_BUDGET

    def test_all_phases_present(self):
        expected_phases = {"skeleton", "functional", "enhanced", "full"}
        assert set(PHASE_TOKEN_BUDGET_MAP.keys()) == expected_phases


class TestPhaseAdvanceAdjustsTokenBudget:
    def test_phase_advance_sets_budget(self, tmp_path):
        budget_file = tmp_path / "token_budget.json"
        with patch("xuansto_mcp.tools.token_budget.BUDGET_FILE", budget_file), \
             patch("xuansto_mcp.tools.token_budget.notify"), \
             patch("xuansto_mcp.tools.token_budget._persist_to_sqlite"):
            _set_budget(total_budget=999)
            result = _set_budget_from_phase("enhanced")
            assert result["total_budget"] == 10000
