import pytest
from unittest.mock import patch, MagicMock
from mcp.server.fastmcp import FastMCP


@pytest.mark.asyncio
async def test_security_scan_mcp_to_inline_degradation():
    mcp = FastMCP("test-deg-e2e-sec")
    from xuansto_mcp.tools.security_scan import register
    register(mcp)
    tool_fn = mcp._tool_manager._tools["security_scan"].fn
    with patch("xuansto_mcp.tools.security_scan.run_script") as mock_run, \
         patch("xuansto_mcp.tools.security_scan.SCRIPTS_DIR") as mock_scripts:
        mock_scripts.__truediv__ = MagicMock(return_value=MagicMock(exists=MagicMock(return_value=False)))
        mock_run.return_value = {"error": True, "message": "script not found"}
        result = await tool_fn(target=".", include_agentic=True, include_dependency=True)
        assert result.get("error") is False
        data = result.get("data", {})
        if "agentic_scan" in data:
            assert "vulnerabilities" in data["agentic_scan"] or "degradation_level" in data["agentic_scan"]


@pytest.mark.asyncio
async def test_knowledge_search_mcp_to_keyword_degradation():
    mcp = FastMCP("test-deg-e2e-kw")
    from xuansto_mcp.tools.knowledge_search import register
    register(mcp)
    tool_fn = mcp._tool_manager._tools["knowledge_search"].fn
    with patch("xuansto_mcp.tools.knowledge_search._ensure_knowledge_index"), \
         patch("xuansto_mcp.tools.knowledge_search.get_search_engine") as mock_engine:
        mock_se = MagicMock()
        mock_se.search.return_value = []
        mock_engine.return_value = mock_se
        result = await tool_fn(action="retrieve", query="test query")
        assert result.get("error") is False


@pytest.mark.asyncio
async def test_hook_script_to_inline_degradation():
    mcp = FastMCP("test-deg-e2e-hook")
    from xuansto_mcp.tools.hook_manage import register
    register(mcp)
    tool_fn = mcp._tool_manager._tools["hook_manage"].fn
    with patch("xuansto_mcp.tools.hook_manage.HOOK_SCRIPTS_MAP", {"security-block": "nonexistent.py"}):
        result = await tool_fn(action="execute", hook_name="security-block", context={"command": "rm -rf /"})
        assert result.get("error") is False
        assert result["data"]["status"] == "block"


@pytest.mark.asyncio
async def test_quality_gate_script_to_inline_degradation(tmp_path):
    mcp = FastMCP("test-deg-e2e-qg")
    from xuansto_mcp.tools.quality_gate_check import register
    register(mcp)
    tool_fn = mcp._tool_manager._tools["quality_gate_check"].fn
    with patch("xuansto_mcp.tools.quality_gate_check._compute_file_hashes", return_value={}):
        result = await tool_fn(gate_ids=["TEST-PASS"], project_path=str(tmp_path))
        assert result.get("error") is False
        checks = result["data"]["checks"]
        for c in checks:
            assert c["source"] in ("inline", "script", "no_inline_check", "cache")


@pytest.mark.asyncio
async def test_full_degradation_chain_security():
    mcp = FastMCP("test-deg-chain-full")
    from xuansto_mcp.tools.security_scan import register
    from xuansto_mcp.tools.server_health import track_degradation
    register(mcp)
    tool_fn = mcp._tool_manager._tools["security_scan"].fn
    with patch("xuansto_mcp.tools.security_scan.run_script") as mock_run, \
         patch("xuansto_mcp.tools.security_scan.SCRIPTS_DIR") as mock_scripts, \
         patch("xuansto_mcp.tools.server_health.track_degradation") as mock_track:
        mock_scripts.__truediv__ = MagicMock(return_value=MagicMock(exists=MagicMock(return_value=False)))
        mock_run.return_value = {"error": True, "message": "script not found"}
        result = await tool_fn(target=".", include_agentic=True, include_dependency=False)
        assert result.get("error") is False
