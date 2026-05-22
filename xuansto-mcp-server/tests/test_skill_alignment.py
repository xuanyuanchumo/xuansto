import sys
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
    assert V1_SKILL_PATH.exists(), f"v1 SKILL.md not found: {V1_SKILL_PATH}"
    text = V1_SKILL_PATH.read_text(encoding="utf-8")
    fm = _parse_yaml_frontmatter(text)
    assert fm.get("deprecated") == "true", f"deprecated should be 'true', got: {fm.get('deprecated')}"


def test_v1_skill_md_migrate_to():
    assert V1_SKILL_PATH.exists(), f"v1 SKILL.md not found: {V1_SKILL_PATH}"
    text = V1_SKILL_PATH.read_text(encoding="utf-8")
    fm = _parse_yaml_frontmatter(text)
    assert fm.get("migrate_to") == "xuansto-skill-v2", f"migrate_to should be 'xuansto-skill-v2', got: {fm.get('migrate_to')}"


async def _call_agent_status(action: str, **kwargs) -> dict:
    mcp = FastMCP("test")
    agent_status.register(mcp)
    tools = mcp._tool_manager._tools
    tool_fn = tools["agent_status"].fn
    return await tool_fn(action=action, **kwargs)


def test_agent_status_schedule_returns_planned():
    result = asyncio.run(_call_agent_status(action="schedule"))
    assert result.get("error") is False, f"Expected no error, got: {result}"
    data = result.get("data", {})
    assert data.get("status") == "planned", f"Expected status='planned', got: {data.get('status')}"


def test_agent_status_schedule_returns_correct_message():
    result = asyncio.run(_call_agent_status(action="schedule"))
    assert result.get("error") is False, f"Expected no error, got: {result}"
    data = result.get("data", {})
    expected_message = "Agent调度引擎规划中，当前仅支持手动create/match/assign"
    assert data.get("message") == expected_message, f"Expected message='{expected_message}', got: {data.get('message')}"
