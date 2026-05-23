import pytest
from unittest.mock import patch, MagicMock
from mcp.server.fastmcp import FastMCP
from xuansto_mcp.tools.project_init import (
    _create_project,
    _validate_project,
    _detect_stack,
    STACK_MARKERS,
    register,
)


@pytest.fixture
def mcp_server():
    return FastMCP("test-server")


def test_create_project_positive(tmp_path):
    result = _create_project(name="test-project", description="A test", stack=["python"], directory=str(tmp_path / "new-project"))
    assert result["name"] == "test-project"
    assert result["stack"] == ["python"]


def test_create_project_no_name():
    result = _create_project(name=None)
    assert result.get("error") is True


def test_create_project_already_exists(tmp_path):
    proj_dir = tmp_path / "existing"
    proj_dir.mkdir()
    (proj_dir / ".xuansto-config.yaml").write_text("name: existing\n", encoding="utf-8")
    result = _create_project(name="existing", directory=str(proj_dir))
    assert result.get("error") is True


def test_validate_project_no_path():
    result = _validate_project(project_path=None)
    assert result.get("error") is True


def test_validate_project_nonexistent():
    result = _validate_project(project_path="/nonexistent/path")
    assert result.get("error") is True or result.get("valid") is False


def test_validate_project_no_config(tmp_path):
    result = _validate_project(project_path=str(tmp_path))
    assert result["valid"] is False
    assert any(i["code"] == "NO_CONFIG" for i in result["issues"])


def test_validate_project_with_config(tmp_path):
    config = tmp_path / ".xuansto-config.yaml"
    config.write_text("name: test\nstack:\n  - python\n", encoding="utf-8")
    result = _validate_project(project_path=str(tmp_path))
    assert result["valid"] is True


def test_validate_project_missing_name(tmp_path):
    config = tmp_path / ".xuansto-config.yaml"
    config.write_text("stack:\n  - python\n", encoding="utf-8")
    result = _validate_project(project_path=str(tmp_path))
    assert any(i["code"] == "MISSING_NAME" for i in result["issues"])


def test_detect_stack_no_path():
    result = _detect_stack(project_path=None)
    assert result.get("error") is True


def test_detect_stack_nonexistent():
    result = _detect_stack(project_path="/nonexistent/path")
    assert result.get("error") is True or result.get("total_detected") == 0


def test_detect_stack_python(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'test'\n", encoding="utf-8")
    (tmp_path / "requirements.txt").write_text("pytest\n", encoding="utf-8")
    result = _detect_stack(project_path=str(tmp_path))
    assert result["total_detected"] >= 1
    assert result["primary_stack"] == "python"


def test_detect_stack_node(tmp_path):
    (tmp_path / "package.json").write_text('{"name": "test"}', encoding="utf-8")
    result = _detect_stack(project_path=str(tmp_path))
    assert result["total_detected"] >= 1
    assert result["primary_stack"] == "node"


def test_detect_stack_empty(tmp_path):
    result = _detect_stack(project_path=str(tmp_path))
    assert result["total_detected"] == 0
    assert result["primary_stack"] is None


def test_stack_markers_completeness():
    expected = {"python", "node", "rust", "go", "java", "dotnet", "ruby", "php", "swift", "flutter"}
    assert set(STACK_MARKERS.keys()) == expected


@pytest.mark.asyncio
async def test_project_init_create_positive(mcp_server, tmp_path):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["project_init"].fn
    with patch("xuansto_mcp.tools.project_init.notify"):
        result = await tool_fn(action="create", name="test-proj", directory=str(tmp_path / "new-proj"))
        assert result.get("error") is False


@pytest.mark.asyncio
async def test_project_init_create_no_name(mcp_server):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["project_init"].fn
    result = await tool_fn(action="create", name=None)
    assert result.get("error") is True


@pytest.mark.asyncio
async def test_project_init_validate_positive(mcp_server, tmp_path):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["project_init"].fn
    config = tmp_path / ".xuansto-config.yaml"
    config.write_text("name: test\nstack:\n  - python\n", encoding="utf-8")
    result = await tool_fn(action="validate", project_path=str(tmp_path))
    assert result.get("error") is False


@pytest.mark.asyncio
async def test_project_init_validate_no_path(mcp_server):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["project_init"].fn
    result = await tool_fn(action="validate", project_path=None)
    assert result.get("error") is True


@pytest.mark.asyncio
async def test_project_init_detect_stack_positive(mcp_server, tmp_path):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["project_init"].fn
    (tmp_path / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
    result = await tool_fn(action="detect_stack", project_path=str(tmp_path))
    assert result.get("error") is False


@pytest.mark.asyncio
async def test_project_init_detect_stack_no_path(mcp_server):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["project_init"].fn
    result = await tool_fn(action="detect_stack", project_path=None)
    assert result.get("error") is True


@pytest.mark.asyncio
async def test_project_init_invalid_action(mcp_server):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["project_init"].fn
    result = await tool_fn(action="invalid_action")
    assert result.get("error") is True
