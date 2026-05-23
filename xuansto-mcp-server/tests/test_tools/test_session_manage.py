import pytest
import json
from unittest.mock import patch, MagicMock
from mcp.server.fastmcp import FastMCP
from xuansto_mcp.tools.session_manage import (
    _save_session,
    _load_last_session,
    _list_sessions,
    _detect_patterns,
    _verify_pattern,
    _track_session,
    _restore_session,
    register,
)


@pytest.fixture
def mcp_server():
    return FastMCP("test-server")


@pytest.fixture(autouse=True)
def reset_restored_state():
    from xuansto_mcp.tools import session_manage as sm
    sm._RESTORED_STATE = None
    yield
    sm._RESTORED_STATE = None


def test_save_session(tmp_path):
    with patch("xuansto_mcp.tools.session_manage.SESSION_DIR", tmp_path):
        result = _save_session(
            completed_tasks=["task1"],
            pending_tasks=["task2"],
            decisions=["dec1"],
            experience=["exp1"],
        )
        assert "path" in result
        assert "filename" in result
        assert result["filename"].startswith("session-")


def test_load_last_session_empty(tmp_path):
    with patch("xuansto_mcp.tools.session_manage.SESSION_DIR", tmp_path):
        result = _load_last_session()
        assert result["content"] is None


def test_load_last_session_with_data(tmp_path):
    with patch("xuansto_mcp.tools.session_manage.SESSION_DIR", tmp_path):
        _save_session(completed_tasks=["t1"])
        result = _load_last_session()
        assert result["content"] is not None


def test_list_sessions(tmp_path):
    with patch("xuansto_mcp.tools.session_manage.SESSION_DIR", tmp_path):
        _save_session(completed_tasks=["t1"])
        result = _list_sessions()
        assert result["total"] >= 1


def test_detect_patterns_no_log():
    result = _detect_patterns(None)
    assert result["patterns"] == []


def test_detect_patterns_with_repeats(tmp_path):
    with patch("xuansto_mcp.tools.session_manage.PATTERNS_DIR", tmp_path / "patterns"):
        result = _detect_patterns(["TypeError: x", "TypeError: x", "ValueError: y"])
        assert result["total_detected"] >= 1


def test_verify_pattern_nonexistent():
    result = _verify_pattern("/nonexistent/pattern.json")
    assert result["verified"] is False


def test_verify_pattern_success(tmp_path):
    pattern_file = tmp_path / "pattern-test.json"
    pattern_file.write_text(json.dumps({"error": "test", "count": 3, "confidence": 0.40, "status": "draft", "verified": False}), encoding="utf-8")
    result = _verify_pattern(str(pattern_file), success=True)
    assert result["verified"] is True
    assert result["updated_confidence"] > 0.40


def test_track_session(tmp_path):
    with patch("xuansto_mcp.tools.session_manage.SESSION_DIR", tmp_path):
        result = _track_session(current_phase=2, current_task="implement feature", decisions=["use React"])
        assert result["current_phase"] == 2
        assert result["current_task"] == "implement feature"


def test_restore_session_no_state(tmp_path):
    with patch("xuansto_mcp.tools.session_manage.SESSION_DIR", tmp_path):
        result = _restore_session()
        assert result["status"] == "no_tracked_session"


@pytest.mark.asyncio
async def test_session_manage_save_positive(mcp_server, tmp_path):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["session_manage"].fn
    with patch("xuansto_mcp.tools.session_manage.SESSION_DIR", tmp_path):
        result = await tool_fn(action="save", completed_tasks=["task1"])
        assert result.get("error") is False


@pytest.mark.asyncio
async def test_session_manage_verify_no_path(mcp_server):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["session_manage"].fn
    result = await tool_fn(action="verify", pattern_path=None)
    assert result.get("error") is True


@pytest.mark.asyncio
async def test_session_manage_invalid_action(mcp_server):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["session_manage"].fn
    result = await tool_fn(action="invalid_action")
    assert result.get("error") is True
