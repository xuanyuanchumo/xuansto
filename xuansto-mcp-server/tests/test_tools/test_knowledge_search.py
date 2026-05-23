import pytest
from unittest.mock import patch, MagicMock
from mcp.server.fastmcp import FastMCP
from xuansto_mcp.tools.knowledge_search import register


@pytest.fixture
def mcp_server():
    return FastMCP("test-server")


@pytest.mark.asyncio
async def test_knowledge_search_retrieve_positive(mcp_server):
    register(mcp_server)
    tools = await mcp_server.list_tools()
    assert "knowledge_search" in [t.name for t in tools]


@pytest.mark.asyncio
async def test_knowledge_search_retrieve_no_query(mcp_server):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["knowledge_search"].fn
    with patch("xuansto_mcp.tools.knowledge_search._ensure_knowledge_index"), \
         patch("xuansto_mcp.tools.knowledge_search.get_search_engine") as mock_engine:
        mock_se = MagicMock()
        mock_se.search.return_value = []
        mock_engine.return_value = mock_se
        result = await tool_fn(action="retrieve", query=None)
        assert result.get("error") is True


@pytest.mark.asyncio
async def test_knowledge_search_inject_no_content(mcp_server):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["knowledge_search"].fn
    with patch("xuansto_mcp.tools.knowledge_search._ensure_knowledge_index"):
        result = await tool_fn(action="inject", content=None)
        assert result.get("error") is True


@pytest.mark.asyncio
async def test_knowledge_search_precipitate_no_pattern_ids(mcp_server):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["knowledge_search"].fn
    with patch("xuansto_mcp.tools.knowledge_search._ensure_knowledge_index"):
        result = await tool_fn(action="precipitate", pattern_ids=None)
        assert result.get("error") is True


@pytest.mark.asyncio
async def test_knowledge_search_inject_positive(mcp_server, tmp_path):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["knowledge_search"].fn
    with patch("xuansto_mcp.tools.knowledge_search._ensure_knowledge_index"), \
         patch("xuansto_mcp.tools.knowledge_search._inject_knowledge") as mock_inject, \
         patch("xuansto_mcp.tools.knowledge_search.KNOWLEDGE_GENERAL_DIR", tmp_path / "general"):
        mock_inject.return_value = {
            "injected_id": "test-inject.md",
            "path": str(tmp_path / "test-inject.md"),
            "knowledge_type": "general",
            "indexed": True,
            "chroma_indexed": False,
        }
        result = await tool_fn(action="inject", content="test knowledge content")
        assert result.get("error") is False
        assert result["data"]["injected_id"] == "test-inject.md"


@pytest.mark.asyncio
async def test_knowledge_search_precipitate_positive(mcp_server, tmp_path):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["knowledge_search"].fn
    with patch("xuansto_mcp.tools.knowledge_search._ensure_knowledge_index"), \
         patch("xuansto_mcp.tools.knowledge_search._precipitate_experience") as mock_precip:
        mock_precip.return_value = {
            "precipitated_id": "test-precip.md",
            "path": str(tmp_path / "test-precip.md"),
            "patterns_analyzed": 2,
            "themes_found": 1,
        }
        result = await tool_fn(action="precipitate", pattern_ids=["p1", "p2"])
        assert result.get("error") is False
        assert result["data"]["precipitated_id"] == "test-precip.md"


@pytest.mark.asyncio
async def test_knowledge_search_retrieve_with_query(mcp_server):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["knowledge_search"].fn
    with patch("xuansto_mcp.tools.knowledge_search._ensure_knowledge_index"), \
         patch("xuansto_mcp.tools.knowledge_search.get_search_engine") as mock_engine:
        from xuansto_mcp.core.search_engine import SearchResult
        mock_se = MagicMock()
        mock_se.search.return_value = [
            SearchResult(source="doc1", content="test content", match_type="semantic", relevance=0.9)
        ]
        mock_engine.return_value = mock_se
        result = await tool_fn(action="retrieve", query="test query")
        assert result.get("error") is False


@pytest.mark.asyncio
async def test_knowledge_search_invalid_action(mcp_server):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["knowledge_search"].fn
    result = await tool_fn(action="invalid_action_xyz")
    assert result.get("error") is True


@pytest.mark.asyncio
async def test_knowledge_search_retrieve_returns_strategy(mcp_server):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["knowledge_search"].fn
    with patch("xuansto_mcp.tools.knowledge_search._ensure_knowledge_index"), \
         patch("xuansto_mcp.tools.knowledge_search.get_search_engine") as mock_engine:
        mock_se = MagicMock()
        mock_se.search.return_value = []
        mock_engine.return_value = mock_se
        result = await tool_fn(action="retrieve", query="test query")
        assert result.get("error") is False
        assert "strategy" in result.get("data", {})
