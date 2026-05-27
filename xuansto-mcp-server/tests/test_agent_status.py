import sys
import pytest
from pathlib import Path

SKILL_PATH = Path(__file__).resolve().parent.parent.parent / ".trae" / "skills" / "xuansto-skill"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from xuansto_mcp.tools import agent_status
from mcp.server.fastmcp import FastMCP


def test_register():
    mcp = FastMCP("test")
    agent_status.register(mcp)
    tools = mcp._tool_manager._tools
    assert "agent_status" in tools


def test_phase_agent_map():
    assert 0 in agent_status.PHASE_AGENT_MAP
    assert 4 in agent_status.PHASE_AGENT_MAP
    assert len(agent_status.PHASE_AGENT_MAP) == 9


def test_parse_agent_registry():
    registry_path = SKILL_PATH / "references" / "agent-registry.md"
    if registry_path.exists():
        agents = agent_status._parse_agent_registry(registry_path)
        assert isinstance(agents, list)
        if len(agents) > 0:
            assert "name" in agents[0]
            assert "layer" in agents[0]
    else:
        agents = agent_status._parse_agent_registry(Path("/nonexistent"))
        assert agents == []


def test_parse_agent_registry_from_data_dir():
    from xuansto_mcp.core.config import REFERENCES_DIR
    registry_path = REFERENCES_DIR / "agent-registry.md"
    if not registry_path.exists():
        pytest.skip("agent-registry.md not found in REFERENCES_DIR")
    agents = agent_status._parse_agent_registry(registry_path)
    assert isinstance(agents, list)
