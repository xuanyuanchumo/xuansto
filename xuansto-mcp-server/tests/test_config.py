import os
from pathlib import Path
from unittest.mock import patch

import pytest

from xuansto_mcp.core.config import _find_project_root


def test_find_project_root_finds_trae_dir(tmp_path: Path, monkeypatch):
    project = tmp_path / "myproject"
    project.mkdir()
    (project / ".trae").mkdir()
    (project / "src").mkdir()
    monkeypatch.chdir(project / "src")
    assert _find_project_root() == project


def test_find_project_root_finds_git_dir(tmp_path: Path, monkeypatch):
    project = tmp_path / "myproject"
    project.mkdir()
    (project / ".git").mkdir()
    (project / "sub").mkdir()
    monkeypatch.chdir(project / "sub")
    assert _find_project_root() == project


def test_find_project_root_falls_back_to_cwd(tmp_path: Path, monkeypatch):
    isolated = tmp_path / "isolated"
    isolated.mkdir()
    monkeypatch.chdir(isolated)
    original_is_dir = Path.is_dir

    def mock_is_dir(self):
        name = self.name
        if name in (".trae", ".git"):
            return False
        return original_is_dir(self)

    with patch.object(Path, "is_dir", mock_is_dir):
        assert _find_project_root() == isolated


def test_work_dir_uses_project_root(tmp_path: Path, monkeypatch):
    project = tmp_path / "proj"
    project.mkdir()
    (project / ".trae").mkdir()
    monkeypatch.chdir(project)
    monkeypatch.delenv("XUANSTO_WORK_DIR", raising=False)
    import importlib
    import xuansto_mcp.core.config as cfg
    importlib.reload(cfg)
    assert cfg.WORK_DIR == project / ".xuansto"


def test_work_dir_uses_env_var(tmp_path: Path, monkeypatch):
    custom = tmp_path / "custom_work"
    custom.mkdir()
    monkeypatch.setenv("XUANSTO_WORK_DIR", str(custom))
    import importlib
    import xuansto_mcp.core.config as cfg
    importlib.reload(cfg)
    assert cfg.WORK_DIR == custom
    monkeypatch.delenv("XUANSTO_WORK_DIR", raising=False)
    importlib.reload(cfg)
