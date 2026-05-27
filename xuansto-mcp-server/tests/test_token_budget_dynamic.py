from __future__ import annotations

from unittest.mock import patch

import pytest

from xuansto_mcp.tools.token_budget import _recommend


_MOCK_DYNAMIC_SCALING_ENABLED = {
    "token_budgets": {
        "dynamic_scaling": {
            "enabled": True,
            "project_sizes": {
                "small": {
                    "file_count_max": 50,
                    "agent_count_max": 10,
                    "budget_multiplier": 0.7,
                },
                "medium": {
                    "file_count_max": 500,
                    "agent_count_max": 30,
                    "budget_multiplier": 1.0,
                },
                "large": {
                    "file_count_max": 99999,
                    "agent_count_max": 999,
                    "budget_multiplier": 1.5,
                },
            },
        },
    },
}

_MOCK_DYNAMIC_SCALING_DISABLED = {
    "token_budgets": {
        "dynamic_scaling": {
            "enabled": False,
        },
    },
}


class TestRecommendSmallProject:
    @patch("xuansto_mcp.tools.token_budget._CONSTRAINTS_CONFIG", _MOCK_DYNAMIC_SCALING_ENABLED)
    def test_small_project_by_file_count(self):
        result = _recommend(file_count=30, agent_count=5)
        assert result["detected_size"] == "small"
        assert result["project_size"] == "small"
        assert result["dynamic_scaling_enabled"] is True
        assert result["budget_multiplier"] == 0.7
        assert result["adjusted_total"] == int(result["recommended_total"] * 0.7)

    @patch("xuansto_mcp.tools.token_budget._CONSTRAINTS_CONFIG", _MOCK_DYNAMIC_SCALING_ENABLED)
    def test_small_project_at_boundary(self):
        result = _recommend(file_count=50, agent_count=10)
        assert result["detected_size"] == "small"
        assert result["budget_multiplier"] == 0.7


class TestRecommendMediumProject:
    @patch("xuansto_mcp.tools.token_budget._CONSTRAINTS_CONFIG", _MOCK_DYNAMIC_SCALING_ENABLED)
    def test_medium_project_by_file_count(self):
        result = _recommend(file_count=200, agent_count=20)
        assert result["detected_size"] == "medium"
        assert result["project_size"] == "medium"
        assert result.get("budget_multiplier", 1.0) == 1.0

    @patch("xuansto_mcp.tools.token_budget._CONSTRAINTS_CONFIG", _MOCK_DYNAMIC_SCALING_ENABLED)
    def test_medium_project_at_boundary(self):
        result = _recommend(file_count=500, agent_count=30)
        assert result["detected_size"] == "medium"


class TestRecommendLargeProject:
    @patch("xuansto_mcp.tools.token_budget._CONSTRAINTS_CONFIG", _MOCK_DYNAMIC_SCALING_ENABLED)
    def test_large_project_by_file_count(self):
        result = _recommend(file_count=1000, agent_count=50)
        assert result["detected_size"] == "large"
        assert result["project_size"] == "large"
        assert result["dynamic_scaling_enabled"] is True
        assert result["budget_multiplier"] == 1.5
        assert result["adjusted_total"] == int(result["recommended_total"] * 1.5)

    @patch("xuansto_mcp.tools.token_budget._CONSTRAINTS_CONFIG", _MOCK_DYNAMIC_SCALING_ENABLED)
    def test_large_project_by_agent_count(self):
        result = _recommend(file_count=100, agent_count=100)
        assert result["detected_size"] == "large"
        assert result["budget_multiplier"] == 1.5


class TestRecommendDynamicScalingDisabled:
    @patch("xuansto_mcp.tools.token_budget._CONSTRAINTS_CONFIG", _MOCK_DYNAMIC_SCALING_DISABLED)
    def test_disabled_returns_default_budget(self):
        result = _recommend(file_count=1000, agent_count=100)
        assert result["project_size"] == "medium"
        assert "dynamic_scaling_enabled" not in result
        assert "budget_multiplier" not in result

    @patch("xuansto_mcp.tools.token_budget._CONSTRAINTS_CONFIG", _MOCK_DYNAMIC_SCALING_DISABLED)
    def test_disabled_explicit_size_still_works(self):
        result = _recommend(project_size="large", file_count=1000)
        assert result["project_size"] == "large"


class TestRecommendNoFileOrAgentCount:
    @patch("xuansto_mcp.tools.token_budget._CONSTRAINTS_CONFIG", _MOCK_DYNAMIC_SCALING_ENABLED)
    def test_no_counts_returns_default(self):
        result = _recommend()
        assert result["project_size"] == "medium"
        assert "detected_size" not in result

    @patch("xuansto_mcp.tools.token_budget._CONSTRAINTS_CONFIG", _MOCK_DYNAMIC_SCALING_ENABLED)
    def test_only_file_count(self):
        result = _recommend(file_count=30)
        assert result["detected_size"] == "small"

    @patch("xuansto_mcp.tools.token_budget._CONSTRAINTS_CONFIG", _MOCK_DYNAMIC_SCALING_ENABLED)
    def test_only_agent_count(self):
        result = _recommend(agent_count=5)
        assert result["detected_size"] == "small"
