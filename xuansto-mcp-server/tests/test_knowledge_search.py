import pytest
from mcp.server.fastmcp import FastMCP


@pytest.mark.asyncio
async def test_knowledge_search_registered():
    mcp = FastMCP("test")
    from xuansto_mcp.tools.knowledge_search import register
    register(mcp)
    tools = await mcp.list_tools()
    tool_names = [t.name for t in tools]
    assert "knowledge_search" in tool_names
