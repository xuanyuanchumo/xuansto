import pytest
from unittest.mock import patch, MagicMock
from mcp.server.fastmcp import FastMCP
from xuansto_mcp.tools.security_scan import register as security_register
from xuansto_mcp.tools.knowledge_search import register as knowledge_register


@pytest.mark.asyncio
async def test_security_scan_degrades_to_inline():
    mcp = FastMCP("test-degradation")
    security_register(mcp)
    tool_fn = mcp._tool_manager._tools["security_scan"].fn
    with patch("xuansto_mcp.tools.security_scan.run_script") as mock_run, \
         patch("xuansto_mcp.tools.security_scan.SCRIPTS_DIR") as mock_scripts:
        mock_scripts.__truediv__ = MagicMock(return_value=MagicMock(exists=MagicMock(return_value=False)))
        mock_run.return_value = {"error": True, "message": "script not found"}
        result = await tool_fn(target=".", include_agentic=True, include_dependency=True)
        assert result.get("error") is False
        data = result.get("data", {})
        assert "agentic_scan" in data or "dependency_scan" in data


@pytest.mark.asyncio
async def test_knowledge_search_degrades_to_keyword():
    mcp = FastMCP("test-degradation-kw")
    knowledge_register(mcp)
    tool_fn = mcp._tool_manager._tools["knowledge_search"].fn
    with patch("xuansto_mcp.tools.knowledge_search._ensure_knowledge_index"), \
         patch("xuansto_mcp.tools.knowledge_search.get_search_engine") as mock_engine:
        mock_se = MagicMock()
        mock_se.search.return_value = []
        mock_engine.return_value = mock_se
        result = await tool_fn(action="retrieve", query="test query")
        assert result.get("error") is False


@pytest.mark.asyncio
async def test_degradation_chain_mcp_to_inline():
    mcp = FastMCP("test-chain")
    security_register(mcp)
    tool_fn = mcp._tool_manager._tools["security_scan"].fn
    with patch("xuansto_mcp.tools.security_scan.run_script") as mock_run, \
         patch("xuansto_mcp.tools.security_scan.SCRIPTS_DIR") as mock_scripts:
        mock_scripts.__truediv__ = MagicMock(return_value=MagicMock(exists=MagicMock(return_value=False)))
        mock_run.return_value = {"error": True, "message": "script not found"}
        result = await tool_fn(target=".", include_agentic=True, include_dependency=False)
        data = result.get("data", {})
        if "agentic_scan" in data:
            assert data["agentic_scan"].get("degradation_level") == "inline" or "vulnerabilities" in data["agentic_scan"]


@pytest.mark.asyncio
async def test_degradation_tracking():
    from xuansto_mcp.tools.server_health import track_degradation, _DEGRADATION_COUNTS, _metrics_lock
    with _metrics_lock:
        _DEGRADATION_COUNTS.clear()
    with patch("xuansto_mcp.tools.server_health._persist_metrics"):
        track_degradation("test_tool")
    with _metrics_lock:
        assert _DEGRADATION_COUNTS.get("test_tool", 0) >= 1


@pytest.mark.asyncio
async def test_chromadb_degradation_blocks_semantic():
    from xuansto_mcp.tools.server_health import _DEGRADATION_COUNTS, _CHROMADB_DEGRADATION_KEY, _metrics_lock
    with _metrics_lock:
        original = _DEGRADATION_COUNTS.get(_CHROMADB_DEGRADATION_KEY, 0)
        _DEGRADATION_COUNTS[_CHROMADB_DEGRADATION_KEY] = 5
    mcp = FastMCP("test-chroma-deg")
    knowledge_register(mcp)
    tool_fn = mcp._tool_manager._tools["knowledge_search"].fn
    with patch("xuansto_mcp.tools.knowledge_search._ensure_knowledge_index"), \
         patch("xuansto_mcp.tools.knowledge_search.get_search_engine") as mock_engine:
        mock_se = MagicMock()
        mock_se.search.return_value = []
        mock_engine.return_value = mock_se
        result = await tool_fn(action="retrieve", query="test")
        assert result.get("error") is False
    with _metrics_lock:
        _DEGRADATION_COUNTS[_CHROMADB_DEGRADATION_KEY] = original


@pytest.mark.asyncio
async def test_hook_degradation_inline_fallback():
    mcp = FastMCP("test-hook-deg")
    from xuansto_mcp.tools.hook_manage import register as hook_register
    hook_register(mcp)
    tool_fn = mcp._tool_manager._tools["hook_manage"].fn
    with patch("xuansto_mcp.tools.hook_manage.HOOK_SCRIPTS_MAP", {"security-block": "nonexistent-script.py"}):
        result = await tool_fn(action="execute", hook_name="security-block", context={"command": "rm -rf /"})
        assert result.get("error") is False
        assert result["data"]["status"] == "block"
