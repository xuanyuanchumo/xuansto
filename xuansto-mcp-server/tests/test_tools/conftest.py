import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from mcp.server.fastmcp import FastMCP


@pytest.fixture
def mcp_server():
    return FastMCP("test-server")


@pytest.fixture
def tmp_project(tmp_path):
    (tmp_path / "SKILL.md").write_text("---\nname: test-skill\nversion: 1.0\n---\n# Test", encoding="utf-8")
    (tmp_path / ".skill-config.yaml").write_text("name: test\nversion: 1.0\n", encoding="utf-8")
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    (scripts / "test.py").write_text("print('hello')", encoding="utf-8")
    return tmp_path


@pytest.fixture
def tmp_project_with_source(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("def main():\n    pass\n", encoding="utf-8")
    (tmp_path / "SKILL.md").write_text("---\nname: test\n---\n# Test", encoding="utf-8")
    return tmp_path


@pytest.fixture
def mock_session_dir(tmp_path):
    session_dir = tmp_path / "sessions"
    session_dir.mkdir()
    return session_dir


@pytest.fixture
def mock_work_dir(tmp_path):
    work_dir = tmp_path / "work"
    work_dir.mkdir()
    return work_dir
