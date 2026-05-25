import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from mcp.server.fastmcp import FastMCP
from xuansto_mcp.tools.skill_analyze import (
    _parse_yaml_frontmatter,
    _scan_directory,
    _parse_agent_registry,
    _scan_script_dependencies,
    _run_skill_validation,
    _assess_project_scale,
    register,
)


@pytest.mark.asyncio
async def test_skill_analyze_positive(mcp_server, tmp_project):
    register(mcp_server)
    tools = await mcp_server.list_tools()
    assert "skill_analyze" in [t.name for t in tools]


@pytest.mark.asyncio
async def test_skill_analyze_nonexistent_path(mcp_server):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["skill_analyze"].fn
    result = await tool_fn(skill_path="/nonexistent/path/xyz")
    assert result.get("error") is True or result.get("data", {}).get("structure", {}).get("exists") is False


def test_parse_yaml_frontmatter_valid(tmp_path):
    md = tmp_path / "SKILL.md"
    md.write_text("---\nname: test-skill\nversion: 2.0\n---\n# Content", encoding="utf-8")
    result = _parse_yaml_frontmatter(md)
    assert result.get("name") == "test-skill"
    assert result.get("version") == 2.0


def test_parse_yaml_frontmatter_nonexistent(tmp_path):
    result = _parse_yaml_frontmatter(tmp_path / "nonexistent_SKILL.md")
    assert result == {}


def test_parse_yaml_frontmatter_no_frontmatter(tmp_path):
    md = tmp_path / "SKILL.md"
    md.write_text("# Just a heading\nSome content", encoding="utf-8")
    result = _parse_yaml_frontmatter(md)
    assert result == {}


def test_scan_directory_basic(tmp_path):
    (tmp_path / "file1.py").write_text("pass", encoding="utf-8")
    sub = tmp_path / "subdir"
    sub.mkdir()
    (sub / "file2.py").write_text("pass", encoding="utf-8")
    result = _scan_directory(tmp_path, 1)
    assert result["exists"] is True
    assert result["files_count"] >= 1
    assert len(result["directories"]) >= 1


def test_scan_directory_nonexistent(tmp_path):
    result = _scan_directory(tmp_path / "nonexistent_dir_xyz", "basic")
    assert result["exists"] is False


def test_scan_directory_full_depth(tmp_path):
    sub = tmp_path / "deep"
    sub.mkdir()
    (sub / "a.py").write_text("pass", encoding="utf-8")
    result = _scan_directory(tmp_path, 3)
    assert result["exists"] is True
    for d in result["directories"]:
        assert "files_count" in d


def test_parse_agent_registry_valid(tmp_path):
    reg = tmp_path / "agent-registry.md"
    reg.write_text("# 第一层 Layer\n- **Orchestrator**: desc\n- **PM**: desc\n", encoding="utf-8")
    result = _parse_agent_registry(reg)
    assert len(result) == 2
    assert result[0]["name"] == "Orchestrator"


def test_parse_agent_registry_nonexistent(tmp_path):
    result = _parse_agent_registry(tmp_path / "nonexistent_registry.md")
    assert result == []


def test_scan_script_dependencies(tmp_path):
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    (scripts / "run.py").write_text("pass", encoding="utf-8")
    sub = scripts / "quality"
    sub.mkdir()
    (sub / "gate.py").write_text("pass", encoding="utf-8")
    result = _scan_script_dependencies(scripts)
    assert result["total_scripts"] >= 1


def test_scan_script_dependencies_nonexistent(tmp_path):
    result = _scan_script_dependencies(tmp_path / "nonexistent_scripts_dir")
    assert result == {}


def test_run_skill_validation_missing_skill_md(tmp_path):
    issues = _run_skill_validation(tmp_path)
    assert any(i["type"] == "missing_file" and i["file"] == "SKILL.md" for i in issues)


def test_run_skill_validation_with_skill_md(tmp_path):
    (tmp_path / "SKILL.md").write_text("# Skill", encoding="utf-8")
    issues = _run_skill_validation(tmp_path)
    assert not any(i["file"] == "SKILL.md" for i in issues)


def test_assess_project_scale_small(tmp_path):
    for i in range(5):
        (tmp_path / f"f{i}.py").write_text("pass", encoding="utf-8")
    result = _assess_project_scale(str(tmp_path))
    assert result["scale"] == "small"
    assert result["workflow_phases"] == 3


def test_assess_project_scale_nonexistent():
    result = _assess_project_scale("/nonexistent/path")
    assert result["scale"] == "small"


@pytest.mark.asyncio
async def test_skill_analyze_returns_structure(mcp_server, tmp_path):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["skill_analyze"].fn
    result = await tool_fn(skill_path=str(tmp_path))
    assert result.get("error") is False
    assert "structure" in result.get("data", {})
