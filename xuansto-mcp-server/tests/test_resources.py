import sys
from pathlib import Path

SKILL_PATH = Path(__file__).resolve().parent.parent.parent / ".trae" / "skills" / "xuansto-skill"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from xuansto_mcp.resources import skill_resources
from mcp.server.fastmcp import FastMCP


def test_register():
    mcp = FastMCP("test")
    skill_resources.register(mcp)
    resources = mcp._resource_manager._resources
    assert len(resources) > 0
