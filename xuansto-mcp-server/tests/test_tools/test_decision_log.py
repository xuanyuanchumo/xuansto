import pytest
import json
from unittest.mock import patch, MagicMock
from mcp.server.fastmcp import FastMCP
from xuansto_mcp.tools.decision_log import (
    _log_decision,
    _query_decisions,
    _export_decisions,
    register,
)


@pytest.fixture
def mcp_server():
    return FastMCP("test-server")


@pytest.fixture
def decisions_dir(tmp_path):
    decisions_file = tmp_path / "decisions.json"
    return decisions_file


def test_log_decision_positive(decisions_dir):
    with patch("xuansto_mcp.tools.decision_log.DECISIONS_FILE", decisions_dir), \
         patch("xuansto_mcp.tools.decision_log.notify"):
        result = _log_decision(
            title="Use React",
            description="Frontend framework choice",
            decision="React with TypeScript",
            rationale="Better ecosystem",
        )
        assert "id" in result
        assert result["entry"]["title"] == "Use React"
        assert result["total_decisions"] == 1


def test_log_decision_multiple(decisions_dir):
    with patch("xuansto_mcp.tools.decision_log.DECISIONS_FILE", decisions_dir), \
         patch("xuansto_mcp.tools.decision_log.notify"):
        _log_decision(title="First")
        result = _log_decision(title="Second")
        assert result["total_decisions"] == 2


def test_query_decisions_empty(decisions_dir):
    with patch("xuansto_mcp.tools.decision_log.DECISIONS_FILE", decisions_dir):
        result = _query_decisions()
        assert result["total"] == 0


def test_query_decisions_with_keyword(decisions_dir):
    with patch("xuansto_mcp.tools.decision_log.DECISIONS_FILE", decisions_dir), \
         patch("xuansto_mcp.tools.decision_log.notify"):
        _log_decision(title="Use React", decision="React")
        _log_decision(title="Use Vue", decision="Vue")
        result = _query_decisions(keyword="react")
        assert result["total"] == 1


def test_query_decisions_with_date_range(decisions_dir):
    with patch("xuansto_mcp.tools.decision_log.DECISIONS_FILE", decisions_dir), \
         patch("xuansto_mcp.tools.decision_log.notify"):
        _log_decision(title="Old decision")
        result = _query_decisions(date_from="2020-01-01", date_to="2099-12-31")
        assert result["total"] >= 1


def test_query_decisions_limit(decisions_dir):
    with patch("xuansto_mcp.tools.decision_log.DECISIONS_FILE", decisions_dir), \
         patch("xuansto_mcp.tools.decision_log.notify"):
        for i in range(5):
            _log_decision(title=f"Decision {i}")
        result = _query_decisions(limit=2)
        assert len(result["results"]) == 2


def test_export_decisions_json(decisions_dir):
    with patch("xuansto_mcp.tools.decision_log.DECISIONS_FILE", decisions_dir), \
         patch("xuansto_mcp.tools.decision_log.notify"):
        _log_decision(title="Export test")
        result = _export_decisions(format="json")
        assert result["format"] == "json"
        assert result["total"] >= 1


def test_export_decisions_markdown(decisions_dir):
    with patch("xuansto_mcp.tools.decision_log.DECISIONS_FILE", decisions_dir), \
         patch("xuansto_mcp.tools.decision_log.notify"):
        _log_decision(title="MD Export", decision="Use MD")
        result = _export_decisions(format="markdown")
        assert result["format"] == "markdown"
        assert "Decision Log" in result["content"]


@pytest.mark.asyncio
async def test_decision_log_log_positive(mcp_server, decisions_dir):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["decision_log"].fn
    with patch("xuansto_mcp.tools.decision_log.DECISIONS_FILE", decisions_dir), \
         patch("xuansto_mcp.tools.decision_log.notify"):
        result = await tool_fn(action="log", title="Test Decision")
        assert result.get("error") is False


@pytest.mark.asyncio
async def test_decision_log_log_no_title(mcp_server):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["decision_log"].fn
    result = await tool_fn(action="log", title=None)
    assert result.get("error") is True


@pytest.mark.asyncio
async def test_decision_log_query_positive(mcp_server, decisions_dir):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["decision_log"].fn
    with patch("xuansto_mcp.tools.decision_log.DECISIONS_FILE", decisions_dir):
        result = await tool_fn(action="query")
        assert result.get("error") is False


@pytest.mark.asyncio
async def test_decision_log_export_positive(mcp_server, decisions_dir):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["decision_log"].fn
    with patch("xuansto_mcp.tools.decision_log.DECISIONS_FILE", decisions_dir):
        result = await tool_fn(action="export", format="json")
        assert result.get("error") is False


@pytest.mark.asyncio
async def test_decision_log_invalid_action(mcp_server):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["decision_log"].fn
    result = await tool_fn(action="invalid_action")
    assert result.get("error") is True
