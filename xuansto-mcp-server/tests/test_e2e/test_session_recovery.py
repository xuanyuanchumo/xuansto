import pytest
import json
from unittest.mock import patch, MagicMock
from mcp.server.fastmcp import FastMCP


@pytest.mark.asyncio
async def test_session_save_and_load(tmp_path):
    mcp = FastMCP("test-session-e2e")
    from xuansto_mcp.tools.session_manage import register
    register(mcp)
    tool_fn = mcp._tool_manager._tools["session_manage"].fn
    with patch("xuansto_mcp.tools.session_manage.SESSION_DIR", tmp_path):
        save_result = await tool_fn(
            action="save",
            completed_tasks=["Implement feature X", "Write tests"],
            pending_tasks=["Deploy to staging"],
            decisions=["Use PostgreSQL over MongoDB"],
            experience=["TDD approach worked well"],
        )
        assert save_result["error"] is False
        load_result = await tool_fn(action="load")
        assert load_result["error"] is False
        assert load_result["data"]["content"] is not None


@pytest.mark.asyncio
async def test_session_track_and_restore(tmp_path):
    mcp = FastMCP("test-session-track")
    from xuansto_mcp.tools.session_manage import register
    register(mcp)
    tool_fn = mcp._tool_manager._tools["session_manage"].fn
    with patch("xuansto_mcp.tools.session_manage.SESSION_DIR", tmp_path):
        track_result = await tool_fn(
            action="track",
            current_phase=3,
            current_task="Write unit tests",
            decisions=["Use pytest framework"],
        )
        assert track_result["error"] is False
        assert track_result["data"]["current_phase"] == 3
        restore_result = await tool_fn(action="restore")
        assert restore_result["error"] is False
        assert restore_result["data"]["current_phase"] == 3


@pytest.mark.asyncio
async def test_session_list(tmp_path):
    mcp = FastMCP("test-session-list")
    from xuansto_mcp.tools.session_manage import register
    register(mcp)
    tool_fn = mcp._tool_manager._tools["session_manage"].fn
    with patch("xuansto_mcp.tools.session_manage.SESSION_DIR", tmp_path):
        await tool_fn(action="save", completed_tasks=["t1"])
        import time
        time.sleep(1.1)
        await tool_fn(action="save", completed_tasks=["t2"])
        list_result = await tool_fn(action="list")
        assert list_result["error"] is False
        assert list_result["data"]["total"] >= 1


@pytest.mark.asyncio
async def test_session_detect_and_verify_patterns(tmp_path):
    mcp = FastMCP("test-session-patterns")
    from xuansto_mcp.tools.session_manage import register
    register(mcp)
    tool_fn = mcp._tool_manager._tools["session_manage"].fn
    patterns_dir = tmp_path / "patterns"
    with patch("xuansto_mcp.tools.session_manage.SESSION_DIR", tmp_path), \
         patch("xuansto_mcp.tools.session_manage.PATTERNS_DIR", patterns_dir):
        detect_result = await tool_fn(
            action="detect",
            error_log=["TypeError: cannot read property", "TypeError: cannot read property", "ValueError: invalid input"],
        )
        assert detect_result["error"] is False
        if detect_result["data"]["total_detected"] > 0:
            pattern_path = detect_result["data"]["patterns"][0].get("path")
            if not pattern_path:
                pattern_files = list(patterns_dir.glob("pattern-*.json"))
                if pattern_files:
                    pattern_path = str(pattern_files[0])
            if pattern_path:
                verify_result = await tool_fn(action="verify", pattern_path=pattern_path, success=True)
                assert verify_result["error"] is False


@pytest.mark.asyncio
async def test_session_recovery_after_restart(tmp_path):
    mcp = FastMCP("test-session-recovery")
    from xuansto_mcp.tools.session_manage import register, _track_session, _restore_session
    register(mcp)
    with patch("xuansto_mcp.tools.session_manage.SESSION_DIR", tmp_path):
        _track_session(current_phase=5, current_task="Security review", decisions=["Use OAuth2"])
        from xuansto_mcp.tools import session_manage as sm
        sm._RESTORED_STATE = None
        restore_result = _restore_session()
        assert restore_result.get("current_phase") == 5
