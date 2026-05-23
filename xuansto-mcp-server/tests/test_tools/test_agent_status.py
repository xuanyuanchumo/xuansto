import pytest
from unittest.mock import patch, MagicMock
from mcp.server.fastmcp import FastMCP
from xuansto_mcp.tools.agent_status import (
    _parse_agent_registry,
    _get_agent_detail,
    PHASE_AGENT_MAP,
    register,
)


@pytest.fixture
def mcp_server():
    return FastMCP("test-server")


@pytest.fixture(autouse=True)
def reset_agent_instances():
    from xuansto_mcp.tools import agent_status as as_mod
    as_mod._AGENT_INSTANCES.clear()
    yield
    as_mod._AGENT_INSTANCES.clear()


def test_parse_agent_registry_valid(tmp_path):
    reg = tmp_path / "agent-registry.md"
    reg.write_text("# 第一层 Layer\n- **Orchestrator**: desc\n- **PM**: desc\n", encoding="utf-8")
    result = _parse_agent_registry(reg)
    assert len(result) == 2


def test_parse_agent_registry_nonexistent():
    result = _parse_agent_registry(MagicMock(exists=MagicMock(return_value=False)))
    assert result == []


def test_get_agent_detail_no_dir(tmp_path):
    result = _get_agent_detail("Orchestrator", tmp_path)
    assert "name" in result


def test_phase_agent_map_structure():
    for phase in range(9):
        assert phase in PHASE_AGENT_MAP
        assert isinstance(PHASE_AGENT_MAP[phase], list)
        assert len(PHASE_AGENT_MAP[phase]) > 0


@pytest.mark.asyncio
async def test_agent_status_list_positive(mcp_server):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["agent_status"].fn
    with patch("xuansto_mcp.tools.agent_status.REFERENCES_DIR") as mock_ref:
        mock_ref.__truediv__ = MagicMock(return_value=MagicMock(exists=MagicMock(return_value=False)))
        result = await tool_fn(action="list")
        assert result.get("error") is False


@pytest.mark.asyncio
async def test_agent_status_by_phase_positive(mcp_server):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["agent_status"].fn
    result = await tool_fn(action="by_phase", phase=0)
    assert result.get("error") is False
    assert len(result["data"]["agents"]) > 0


@pytest.mark.asyncio
async def test_agent_status_by_phase_no_phase(mcp_server):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["agent_status"].fn
    result = await tool_fn(action="by_phase", phase=None)
    assert result.get("error") is True


@pytest.mark.asyncio
async def test_agent_status_detail_no_name(mcp_server):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["agent_status"].fn
    result = await tool_fn(action="detail", agent_name=None)
    assert result.get("error") is True


@pytest.mark.asyncio
async def test_agent_status_create_positive(mcp_server):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["agent_status"].fn
    with patch("xuansto_mcp.tools.agent_status._persist_agent_instances"):
        result = await tool_fn(action="create", agent_type="test_agent", capabilities=["coding"])
        assert result.get("error") is False
        assert result["data"]["agent_type"] == "test_agent"


@pytest.mark.asyncio
async def test_agent_status_create_no_type(mcp_server):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["agent_status"].fn
    result = await tool_fn(action="create", agent_type=None)
    assert result.get("error") is True


@pytest.mark.asyncio
async def test_agent_status_match_no_capabilities(mcp_server):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["agent_status"].fn
    result = await tool_fn(action="match", capabilities=None)
    assert result.get("error") is True


@pytest.mark.asyncio
async def test_agent_status_assign_no_id(mcp_server):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["agent_status"].fn
    result = await tool_fn(action="assign", agent_id=None, task="do stuff")
    assert result.get("error") is True


@pytest.mark.asyncio
async def test_agent_status_release_no_id(mcp_server):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["agent_status"].fn
    result = await tool_fn(action="release", agent_id=None)
    assert result.get("error") is True


@pytest.mark.asyncio
async def test_agent_status_destroy_no_id(mcp_server):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["agent_status"].fn
    result = await tool_fn(action="destroy", agent_id=None)
    assert result.get("error") is True


@pytest.mark.asyncio
async def test_agent_status_schedule(mcp_server):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["agent_status"].fn
    result = await tool_fn(action="schedule")
    assert result.get("error") is False
    assert result["data"]["status"] == "planned"


@pytest.mark.asyncio
async def test_agent_status_invalid_action(mcp_server):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["agent_status"].fn
    result = await tool_fn(action="invalid_action")
    assert result.get("error") is True


@pytest.mark.asyncio
async def test_agent_status_create_assign_release_lifecycle(mcp_server):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["agent_status"].fn
    with patch("xuansto_mcp.tools.agent_status._persist_agent_instances"):
        create_result = await tool_fn(action="create", agent_type="worker", capabilities=["test"])
        agent_id = create_result["data"]["agent_id"]
        assign_result = await tool_fn(action="assign", agent_id=agent_id, task="run tests")
        assert assign_result["data"]["status"] == "busy"
        release_result = await tool_fn(action="release", agent_id=agent_id)
        assert release_result["data"]["status"] == "idle"
