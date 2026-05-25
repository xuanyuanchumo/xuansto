import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

V1_SKILL_PATH = Path(__file__).resolve().parent.parent.parent / ".trae" / "skills" / "xuansto-skill" / "SKILL.md"
V2_SKILL_PATH = Path(__file__).resolve().parent.parent.parent / ".trae" / "skills" / "xuansto-skill-v2" / "SKILL.md"

from xuansto_mcp.tools import agent_status
from mcp.server.fastmcp import FastMCP
import asyncio


def _parse_yaml_frontmatter(text: str) -> dict[str, object]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return {}
    fm: dict[str, object] = {}
    for line in lines[1:end]:
        if ":" in line:
            key, _, value = line.partition(":")
            fm[key.strip()] = value.strip()
    return fm


def test_v1_skill_md_deprecated():
    if not V1_SKILL_PATH.exists():
        pytest.skip(f"v1 SKILL.md not found: {V1_SKILL_PATH}")
    text = V1_SKILL_PATH.read_text(encoding="utf-8")
    fm = _parse_yaml_frontmatter(text)
    assert fm.get("deprecated") == "true", f"deprecated should be 'true', got: {fm.get('deprecated')}"


def test_v1_skill_md_migrate_to():
    if not V1_SKILL_PATH.exists():
        pytest.skip(f"v1 SKILL.md not found: {V1_SKILL_PATH}")
    text = V1_SKILL_PATH.read_text(encoding="utf-8")
    fm = _parse_yaml_frontmatter(text)
    assert fm.get("migrate_to") == "xuansto-skill-v2", f"migrate_to should be 'xuansto-skill-v2', got: {fm.get('migrate_to')}"


async def _call_agent_status(action: str, **kwargs) -> dict:
    mcp = FastMCP("test")
    agent_status.register(mcp)
    tools = mcp._tool_manager._tools
    tool_fn = tools["agent_status"].fn
    return await tool_fn(action=action, **kwargs)


def test_agent_status_merge_policy_returns_info():
    result = asyncio.run(_call_agent_status(action="merge_policy"))
    assert result.get("error") is False, f"Expected no error, got: {result}"
    data = result.get("data", {})
    assert "project_scale" in data, f"Expected 'project_scale' in data, got: {data}"


def test_agent_status_merge_policy_default_scale():
    result = asyncio.run(_call_agent_status(action="merge_policy"))
    assert result.get("error") is False, f"Expected no error, got: {result}"
    data = result.get("data", {})
    assert data.get("project_scale") == "medium", f"Expected project_scale='medium', got: {data.get('project_scale')}"
