import pytest
from pathlib import Path
from xuansto_mcp.tools.skill_analyze import (
    _parse_yaml_frontmatter,
    _scan_directory,
    _parse_agent_registry,
    _scan_script_dependencies,
    _run_skill_validation,
    _assess_project_scale,
)

SKILL_PATH = Path(__file__).resolve().parent.parent.parent / ".trae" / "skills" / "xuansto-skill"


@pytest.mark.asyncio
async def test_skill_analyze_basic():
    from mcp.server.fastmcp import FastMCP
    mcp = FastMCP("test")
    from xuansto_mcp.tools.skill_analyze import register
    register(mcp)
    tools = await mcp.list_tools()
    tool_names = [t.name for t in tools]
    assert "skill_analyze" in tool_names


def test_parse_yaml_frontmatter():
    skill_md = SKILL_PATH / "SKILL.md"
    if not skill_md.exists():
        pytest.skip("SKILL.md not found")
    result = _parse_yaml_frontmatter(skill_md)
    assert "name" in result
    assert result["name"] == "xuansto-skill"
    assert "version" in result


def test_parse_yaml_frontmatter_nonexistent():
    result = _parse_yaml_frontmatter(Path("/nonexistent/SKILL.md"))
    assert result == {}


def test_scan_directory():
    if not SKILL_PATH.exists():
        pytest.skip("Skill path not found")
    result = _scan_directory(SKILL_PATH, "basic")
    assert result["exists"] is True
    assert result["files_count"] > 0
    assert len(result["directories"]) > 0


def test_scan_directory_nonexistent():
    result = _scan_directory(Path("Z:/nonexistent_dir_xyz_12345"), "basic")
    assert result["exists"] is False


def test_parse_agent_registry():
    registry = SKILL_PATH / "references" / "agent-registry.md"
    if not registry.exists():
        pytest.skip("agent-registry.md not found")
    agents = _parse_agent_registry(registry)
    assert len(agents) > 0
    assert "name" in agents[0]


def test_scan_script_dependencies():
    scripts_dir = SKILL_PATH / "scripts"
    if not scripts_dir.exists():
        pytest.skip("scripts dir not found")
    deps = _scan_script_dependencies(scripts_dir)
    assert deps["total_scripts"] > 0


def test_run_skill_validation():
    if not SKILL_PATH.exists():
        pytest.skip("Skill path not found")
    issues = _run_skill_validation(SKILL_PATH)
    assert isinstance(issues, list)
    for issue in issues:
        assert "severity" in issue
        assert "message" in issue


def test_assess_project_scale_nonexistent():
    result = _assess_project_scale("Z:/nonexistent_dir_xyz_12345")
    assert result["file_count"] == 0
    assert result["loc_count"] == 0
    assert result["scale"] == "small"
    assert result["recommended_workflow"] == "sdd-tdd-fast"
    assert result["workflow_phases"] == 3


def test_assess_project_scale_small(tmp_path):
    for i in range(5):
        (tmp_path / f"file{i}.py").write_text("x = 1\n", encoding="utf-8")
    result = _assess_project_scale(str(tmp_path))
    assert result["file_count"] == 5
    assert result["loc_count"] == 5
    assert result["scale"] == "small"
    assert result["recommended_workflow"] == "sdd-tdd-fast"
    assert result["workflow_phases"] == 3


def test_assess_project_scale_medium_by_files(tmp_path):
    for i in range(50):
        (tmp_path / f"file{i}.py").write_text("x = 1\n", encoding="utf-8")
    result = _assess_project_scale(str(tmp_path))
    assert result["file_count"] == 50
    assert result["scale"] == "medium"
    assert result["recommended_workflow"] == "sdd-tdd-medium"
    assert result["workflow_phases"] == 6


def test_assess_project_scale_large_by_files(tmp_path):
    for i in range(150):
        (tmp_path / f"file{i}.py").write_text("x = 1\n", encoding="utf-8")
    result = _assess_project_scale(str(tmp_path))
    assert result["file_count"] == 150
    assert result["scale"] == "large"
    assert result["recommended_workflow"] == "sdd-tdd-full"
    assert result["workflow_phases"] == 9


def test_assess_project_scale_medium_by_loc(tmp_path):
    for i in range(10):
        (tmp_path / f"file{i}.py").write_text("x = 1\n" * 300, encoding="utf-8")
    result = _assess_project_scale(str(tmp_path))
    assert result["file_count"] == 10
    assert result["loc_count"] == 3000
    assert result["scale"] == "medium"
    assert result["recommended_workflow"] == "sdd-tdd-medium"
    assert result["workflow_phases"] == 6


def test_assess_project_scale_loc_overrides_file_count(tmp_path):
    for i in range(5):
        (tmp_path / f"file{i}.py").write_text("x = 1\n" * 5000, encoding="utf-8")
    result = _assess_project_scale(str(tmp_path))
    assert result["file_count"] == 5
    assert result["loc_count"] == 25000
    assert result["scale"] == "large"
    assert result["recommended_workflow"] == "sdd-tdd-full"
    assert result["workflow_phases"] == 9


def test_assess_project_scale_excludes_dirs(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "pkg").mkdir()
    (tmp_path / ".git").mkdir()
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / ".venv").mkdir()
    (tmp_path / "venv").mkdir()
    (tmp_path / "dist").mkdir()
    (tmp_path / "build").mkdir()
    for i in range(3):
        (tmp_path / "src" / f"main{i}.py").write_text("x = 1\n", encoding="utf-8")
    for i in range(10):
        (tmp_path / "node_modules" / f"dep{i}.js").write_text("var x = 1;\n", encoding="utf-8")
        (tmp_path / ".git" / f"obj{i}").write_text("data\n", encoding="utf-8")
        (tmp_path / "__pycache__" / f"cache{i}.pyc").write_text("bytes\n", encoding="utf-8")
        (tmp_path / ".venv" / f"lib{i}.py").write_text("lib\n", encoding="utf-8")
        (tmp_path / "venv" / f"env{i}.py").write_text("env\n", encoding="utf-8")
        (tmp_path / "dist" / f"out{i}.js").write_text("out\n", encoding="utf-8")
        (tmp_path / "build" / f"tmp{i}.o").write_text("obj\n", encoding="utf-8")
    result = _assess_project_scale(str(tmp_path))
    assert result["file_count"] == 3
    assert result["scale"] == "small"


def test_assess_project_scale_on_real_skill():
    if not SKILL_PATH.exists():
        pytest.skip("Skill path not found")
    result = _assess_project_scale(str(SKILL_PATH))
    assert result["file_count"] > 0
    assert result["loc_count"] > 0
    assert result["scale"] in ("small", "medium", "large")
    assert result["recommended_workflow"] in ("sdd-tdd-fast", "sdd-tdd-medium", "sdd-tdd-full")
    assert result["workflow_phases"] in (3, 6, 9)
