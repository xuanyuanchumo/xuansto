import pytest
from unittest.mock import patch, MagicMock
from mcp.server.fastmcp import FastMCP
from xuansto_mcp.tools.token_budget import (
    _get_status,
    _set_budget,
    _recommend,
    _report,
    DEFAULT_PHASE_ALLOCATIONS,
    RECOMMENDATION_MAP,
    register,
)


@pytest.fixture
def mcp_server():
    return FastMCP("test-server")


@pytest.fixture
def budget_file(tmp_path):
    return tmp_path / "token_budget.json"


def test_get_status_no_budget(budget_file):
    with patch("xuansto_mcp.tools.token_budget.BUDGET_FILE", budget_file), \
         patch("xuansto_mcp.tools.token_budget._restore_from_sqlite", return_value=None):
        result = _get_status()
        assert result["total_budget"] == 0
        assert result["status"] == "no_budget_set"


def test_set_budget_total(budget_file):
    with patch("xuansto_mcp.tools.token_budget.BUDGET_FILE", budget_file), \
         patch("xuansto_mcp.tools.token_budget.notify"):
        result = _set_budget(total_budget=100000)
        assert result["total_budget"] == 100000


def test_set_budget_with_allocations(budget_file):
    with patch("xuansto_mcp.tools.token_budget.BUDGET_FILE", budget_file), \
         patch("xuansto_mcp.tools.token_budget.notify"):
        allocs = {"0": 5000, "4": 30000}
        result = _set_budget(total_budget=100000, phase_allocations=allocs)
        assert result["phase_allocations"]["4"] == 30000


def test_recommend_default():
    result = _recommend()
    assert result["recommended_total"] > 0
    assert "recommended_allocations" in result


def test_recommend_small_low():
    result = _recommend(project_size="small", complexity="low")
    assert result["recommended_total"] == 50000


def test_recommend_large_high():
    result = _recommend(project_size="large", complexity="high")
    assert result["recommended_total"] == 500000


def test_recommend_with_team_size():
    result = _recommend(project_size="medium", complexity="medium", team_size=5)
    assert result["adjusted_total"] > result["recommended_total"]
    assert result["adjustment_multiplier"] > 1.0


def test_report_no_budget(budget_file):
    with patch("xuansto_mcp.tools.token_budget.BUDGET_FILE", budget_file), \
         patch("xuansto_mcp.tools.token_budget._restore_from_sqlite", return_value=None):
        result = _report()
        assert result["total_budget"] == 0
        assert result["usage_pct"] == 0


def test_report_daily(budget_file):
    with patch("xuansto_mcp.tools.token_budget.BUDGET_FILE", budget_file):
        result = _report(period="daily")
        assert result["period"] == "daily"
        assert "date" in result


def test_report_weekly(budget_file):
    with patch("xuansto_mcp.tools.token_budget.BUDGET_FILE", budget_file):
        result = _report(period="weekly")
        assert result["period"] == "weekly"
        assert "week" in result


def test_default_phase_allocations():
    assert len(DEFAULT_PHASE_ALLOCATIONS) == 9
    assert "4" in DEFAULT_PHASE_ALLOCATIONS
    assert DEFAULT_PHASE_ALLOCATIONS["4"] > DEFAULT_PHASE_ALLOCATIONS["0"]


def test_recommendation_map_completeness():
    for size in ("small", "medium", "large"):
        for comp in ("low", "medium", "high"):
            assert (size, comp) in RECOMMENDATION_MAP


@pytest.mark.asyncio
async def test_token_budget_status_positive(mcp_server, budget_file):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["token_budget"].fn
    with patch("xuansto_mcp.tools.token_budget.BUDGET_FILE", budget_file):
        result = await tool_fn(action="status")
        assert result.get("error") is False


@pytest.mark.asyncio
async def test_token_budget_set_budget_positive(mcp_server, budget_file):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["token_budget"].fn
    with patch("xuansto_mcp.tools.token_budget.BUDGET_FILE", budget_file), \
         patch("xuansto_mcp.tools.token_budget.notify"):
        result = await tool_fn(action="set_budget", total_budget=200000)
        assert result.get("error") is False


@pytest.mark.asyncio
async def test_token_budget_set_budget_no_params(mcp_server):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["token_budget"].fn
    result = await tool_fn(action="set_budget", total_budget=None, phase_allocations=None)
    assert result.get("error") is True


@pytest.mark.asyncio
async def test_token_budget_recommend_positive(mcp_server):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["token_budget"].fn
    result = await tool_fn(action="recommend", project_size="medium", complexity="high")
    assert result.get("error") is False


@pytest.mark.asyncio
async def test_token_budget_report_positive(mcp_server, budget_file):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["token_budget"].fn
    with patch("xuansto_mcp.tools.token_budget.BUDGET_FILE", budget_file):
        result = await tool_fn(action="report", period="session")
        assert result.get("error") is False


@pytest.mark.asyncio
async def test_token_budget_invalid_action(mcp_server):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["token_budget"].fn
    result = await tool_fn(action="invalid_action")
    assert result.get("error") is True
