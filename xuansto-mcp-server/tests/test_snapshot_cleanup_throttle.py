import sys
import time
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from xuansto_mcp.tools import server_health


def test_cleanup_not_triggered_within_interval():
    server_health._last_snapshot_cleanup_time = time.time()
    should_run = time.time() - server_health._last_snapshot_cleanup_time >= server_health._SNAPSHOT_CLEANUP_MIN_INTERVAL
    assert not should_run, "Cleanup should NOT run within the minimum interval"
    server_health._last_snapshot_cleanup_time = 0.0


def test_cleanup_triggered_after_interval():
    server_health._last_snapshot_cleanup_time = time.time() - server_health._SNAPSHOT_CLEANUP_MIN_INTERVAL - 1.0
    should_run = time.time() - server_health._last_snapshot_cleanup_time >= server_health._SNAPSHOT_CLEANUP_MIN_INTERVAL
    assert should_run, "Cleanup SHOULD run after the minimum interval has elapsed"
    server_health._last_snapshot_cleanup_time = 0.0


def test_first_call_always_triggers():
    server_health._last_snapshot_cleanup_time = 0.0
    should_run = time.time() - 0.0 >= server_health._SNAPSHOT_CLEANUP_MIN_INTERVAL
    assert should_run, "First call (time=0) should always trigger cleanup"
    server_health._last_snapshot_cleanup_time = 0.0


@pytest.mark.asyncio
async def test_server_health_calls_cleanup_on_first_call():
    server_health._last_snapshot_cleanup_time = 0.0

    with patch("xuansto_mcp.tools.workflow_dispatch._cleanup_all_snapshots", return_value={}) as mock_cleanup, \
         patch("xuansto_mcp.tools.workflow_dispatch._load_all_workflows", return_value={}), \
         patch("xuansto_mcp.tools.server_health._TOOL_METRICS", {}), \
         patch("xuansto_mcp.tools.server_health._DEGRADATION_COUNTS", {}):
        from mcp.server.fastmcp import FastMCP
        test_mcp = FastMCP("test")
        server_health.register(test_mcp)
        tool_fn = test_mcp._tool_manager._tools["server_health"].fn

        await tool_fn()
        mock_cleanup.assert_called_once()

    server_health._last_snapshot_cleanup_time = 0.0


@pytest.mark.asyncio
async def test_server_health_skips_cleanup_within_interval():
    server_health._last_snapshot_cleanup_time = time.time()

    with patch("xuansto_mcp.tools.workflow_dispatch._cleanup_all_snapshots", return_value={}) as mock_cleanup, \
         patch("xuansto_mcp.tools.workflow_dispatch._load_all_workflows", return_value={}), \
         patch("xuansto_mcp.tools.server_health._TOOL_METRICS", {}), \
         patch("xuansto_mcp.tools.server_health._DEGRADATION_COUNTS", {}):
        from mcp.server.fastmcp import FastMCP
        test_mcp = FastMCP("test")
        server_health.register(test_mcp)
        tool_fn = test_mcp._tool_manager._tools["server_health"].fn

        await tool_fn()
        mock_cleanup.assert_not_called()

    server_health._last_snapshot_cleanup_time = 0.0


@pytest.mark.asyncio
async def test_server_health_calls_cleanup_after_interval_elapses():
    server_health._last_snapshot_cleanup_time = time.time() - server_health._SNAPSHOT_CLEANUP_MIN_INTERVAL - 1.0

    with patch("xuansto_mcp.tools.workflow_dispatch._cleanup_all_snapshots", return_value={}) as mock_cleanup, \
         patch("xuansto_mcp.tools.workflow_dispatch._load_all_workflows", return_value={}), \
         patch("xuansto_mcp.tools.server_health._TOOL_METRICS", {}), \
         patch("xuansto_mcp.tools.server_health._DEGRADATION_COUNTS", {}):
        from mcp.server.fastmcp import FastMCP
        test_mcp = FastMCP("test")
        server_health.register(test_mcp)
        tool_fn = test_mcp._tool_manager._tools["server_health"].fn

        await tool_fn()
        mock_cleanup.assert_called_once()

    server_health._last_snapshot_cleanup_time = 0.0


def test_snapshot_cleanup_min_interval_is_300_seconds():
    assert server_health._SNAPSHOT_CLEANUP_MIN_INTERVAL == 300.0


def test_last_snapshot_cleanup_time_updates_after_cleanup():
    server_health._last_snapshot_cleanup_time = 0.0
    before = time.time()

    should_run = time.time() - server_health._last_snapshot_cleanup_time >= server_health._SNAPSHOT_CLEANUP_MIN_INTERVAL
    assert should_run

    server_health._last_snapshot_cleanup_time = time.time()
    after = time.time()

    assert before <= server_health._last_snapshot_cleanup_time <= after
    server_health._last_snapshot_cleanup_time = 0.0
