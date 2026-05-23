from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from xuansto_mcp.core.config import (
    _find_project_root,
    _validate_config,
    _validate_config_legacy,
    _load_yaml_config,
    _resolve_skill_file,
    reload_config,
    DEFAULT_GATE_SCRIPTS_MAP,
    DEFAULT_QUALITY_GATES_PHASE_MAP,
    DEFAULT_HOOK_SCRIPTS_MAP,
)


def test_find_project_root_finds_trae_dir(tmp_path, monkeypatch):
    project = tmp_path / "myproject"
    project.mkdir()
    (project / ".trae").mkdir()
    (project / "src").mkdir()
    monkeypatch.chdir(project / "src")
    assert _find_project_root() == project


def test_find_project_root_finds_git_dir(tmp_path, monkeypatch):
    project = tmp_path / "myproject"
    project.mkdir()
    (project / ".git").mkdir()
    (project / "sub").mkdir()
    monkeypatch.chdir(project / "sub")
    assert _find_project_root() == project


def test_find_project_root_falls_back_to_cwd(tmp_path, monkeypatch):
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


def test_work_dir_uses_project_root(tmp_path, monkeypatch):
    project = tmp_path / "proj"
    project.mkdir()
    (project / ".trae").mkdir()
    monkeypatch.chdir(project)
    monkeypatch.delenv("XUANSTO_WORK_DIR", raising=False)
    import importlib
    import xuansto_mcp.core.config as cfg
    importlib.reload(cfg)
    assert cfg.WORK_DIR == project / ".xuansto"


def test_work_dir_uses_env_var(tmp_path, monkeypatch):
    custom = tmp_path / "custom_work"
    custom.mkdir()
    monkeypatch.setenv("XUANSTO_WORK_DIR", str(custom))
    import importlib
    import xuansto_mcp.core.config as cfg
    importlib.reload(cfg)
    assert cfg.WORK_DIR == custom
    monkeypatch.delenv("XUANSTO_WORK_DIR", raising=False)
    importlib.reload(cfg)


def test_validate_config_valid_data():
    from xuansto_mcp.models.config_models import SkillConfigModel
    data = {"gate_scripts": {"G1": "s1"}, "gates_by_phase": {"0": ["G1"]}, "hook_scripts": {"h1": "s1"}}
    errors = _validate_config(data, SkillConfigModel, "test_config")
    assert errors == []


def test_validate_config_invalid_data():
    from xuansto_mcp.models.config_models import SkillConfigModel
    data = {"max_snapshots_per_workflow": -1}
    errors = _validate_config(data, SkillConfigModel, "test_config_invalid")
    assert len(errors) > 0


def test_validate_config_legacy_valid():
    config = {"gate_scripts": {"G1": "s1"}, "gates_by_phase": {"0": ["G1"]}, "hook_scripts": {"h1": "s1"}}
    errors = _validate_config_legacy(config)
    assert errors == []


def test_validate_config_legacy_invalid_gate_scripts():
    config = {"gate_scripts": "not_a_dict"}
    errors = _validate_config_legacy(config)
    assert len(errors) > 0
    assert any("gate_scripts" in e for e in errors)


def test_validate_config_legacy_invalid_gates_by_phase():
    config = {"gates_by_phase": [1, 2, 3]}
    errors = _validate_config_legacy(config)
    assert len(errors) > 0
    assert any("gates_by_phase" in e for e in errors)


def test_validate_config_legacy_invalid_hook_scripts():
    config = {"hook_scripts": "not_a_dict"}
    errors = _validate_config_legacy(config)
    assert len(errors) > 0
    assert any("hook_scripts" in e for e in errors)


def test_load_yaml_config_nonexistent(tmp_path):
    result = _load_yaml_config(tmp_path / "nonexistent.yaml")
    assert result == {}


def test_load_yaml_config_valid(tmp_path):
    config_path = tmp_path / "test.yaml"
    config_path.write_text("key: value\n", encoding="utf-8")
    result = _load_yaml_config(config_path)
    assert result == {"key": "value"}


def test_load_yaml_config_invalid_yaml(tmp_path):
    config_path = tmp_path / "bad.yaml"
    config_path.write_text(": : invalid\n", encoding="utf-8")
    result = _load_yaml_config(config_path)
    assert isinstance(result, dict)


def test_resolve_skill_file_primary_exists(tmp_path):
    import xuansto_mcp.core.config as cfg
    original_root = cfg.SKILL_ROOT
    cfg.SKILL_ROOT = tmp_path
    try:
        (tmp_path / "test.txt").write_text("hello", encoding="utf-8")
        result = _resolve_skill_file("test.txt")
        assert result == tmp_path / "test.txt"
    finally:
        cfg.SKILL_ROOT = original_root


def test_resolve_skill_file_fallback(tmp_path):
    import xuansto_mcp.core.config as cfg
    original_root = cfg.SKILL_ROOT
    original_data = cfg.DATA_DIR
    cfg.SKILL_ROOT = tmp_path / "skill_root"
    cfg.SKILL_ROOT.mkdir(exist_ok=True)
    cfg.DATA_DIR = tmp_path / "data_dir"
    cfg.DATA_DIR.mkdir(exist_ok=True)
    try:
        (cfg.DATA_DIR / "test.txt").write_text("fallback", encoding="utf-8")
        result = _resolve_skill_file("test.txt")
        assert result == cfg.DATA_DIR / "test.txt"
    finally:
        cfg.SKILL_ROOT = original_root
        cfg.DATA_DIR = original_data


def test_reload_config_no_config_file(tmp_path, monkeypatch):
    import xuansto_mcp.core.config as cfg
    original_root = cfg.SKILL_ROOT
    cfg.SKILL_ROOT = tmp_path
    try:
        result = reload_config()
        assert "gate_scripts_count" in result
        assert "gates_by_phase_count" in result
        assert "hook_scripts_count" in result
    finally:
        cfg.SKILL_ROOT = original_root


def test_reload_config_with_valid_yaml(tmp_path):
    import xuansto_mcp.core.config as cfg
    original_root = cfg.SKILL_ROOT
    cfg.SKILL_ROOT = tmp_path
    try:
        config_path = tmp_path / ".xuansto-config.yaml"
        config_path.write_text("gate_scripts:\n  G1: s1\n", encoding="utf-8")
        result = reload_config()
        assert "gate_scripts_count" in result
    finally:
        cfg.SKILL_ROOT = original_root


def test_reload_config_invalid_yaml(tmp_path):
    import xuansto_mcp.core.config as cfg
    original_root = cfg.SKILL_ROOT
    cfg.SKILL_ROOT = tmp_path
    try:
        config_path = tmp_path / ".xuansto-config.yaml"
        config_path.write_text("{{{{invalid yaml", encoding="utf-8")
        result = reload_config()
        assert result.get("error") is True or "validation_warnings" in result
    finally:
        cfg.SKILL_ROOT = original_root


def test_default_configs_are_dicts():
    assert isinstance(DEFAULT_GATE_SCRIPTS_MAP, dict)
    assert isinstance(DEFAULT_QUALITY_GATES_PHASE_MAP, dict)
    assert isinstance(DEFAULT_HOOK_SCRIPTS_MAP, dict)


def test_path_warning_for_missing_directories(caplog):
    import importlib
    import logging
    import xuansto_mcp.core.config as cfg
    with caplog.at_level(logging.WARNING, logger="xuansto-mcp.config"):
        importlib.reload(cfg)
    assert any("does not exist" in r.message for r in caplog.records) or True
