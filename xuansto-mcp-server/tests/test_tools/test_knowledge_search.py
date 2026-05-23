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
async def test_knowledge_search_inject_redirected(mcp_server):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["knowledge_search"].fn
    result = await tool_fn(action="inject")
    assert result.get("error") is True


@pytest.mark.asyncio
async def test_knowledge_search_precipitate_redirected(mcp_server):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["knowledge_search"].fn
    result = await tool_fn(action="precipitate")
    assert result.get("error") is True


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
