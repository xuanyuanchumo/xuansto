from __future__ import annotations

import importlib
import sys
import textwrap
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from xuansto_mcp.core.config import (
    DEFAULT_GATE_SCRIPTS_MAP,
    DEFAULT_HOOK_SCRIPTS_MAP,
    DEFAULT_QUALITY_GATES_PHASE_MAP,
    _load_yaml_config,
)


def test_load_yaml_config_nonexistent_file(tmp_path: Path):
    result = _load_yaml_config(tmp_path / "nonexistent.yaml")
    assert result == {}


def test_load_yaml_config_valid_file(tmp_path: Path):
    config_file = tmp_path / "test-config.yaml"
    config_file.write_text(
        textwrap.dedent("""\
        gate_scripts:
          GATE-999: custom-gate.py
        gates_by_phase:
          "9":
            - CUSTOM-GATE
        hook_scripts:
          custom-hook: custom-script.py
    """),
        encoding="utf-8",
    )
    result = _load_yaml_config(config_file)
    assert result["gate_scripts"]["GATE-999"] == "custom-gate.py"
    assert result["gates_by_phase"]["9"] == ["CUSTOM-GATE"]
    assert result["hook_scripts"]["custom-hook"] == "custom-script.py"


def test_load_yaml_config_invalid_yaml(tmp_path: Path):
    config_file = tmp_path / "bad-config.yaml"
    config_file.write_text("{{invalid: yaml: [", encoding="utf-8")
    result = _load_yaml_config(config_file)
    assert result == {}


def test_load_yaml_config_empty_file(tmp_path: Path):
    config_file = tmp_path / "empty-config.yaml"
    config_file.write_text("", encoding="utf-8")
    result = _load_yaml_config(config_file)
    assert result == {}


def test_defaults_used_when_no_yaml_config(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("XUANSTO_SKILL_ROOT", str(tmp_path))
    import xuansto_mcp.core.config as cfg

    importlib.reload(cfg)
    assert cfg.GATE_SCRIPTS_MAP == DEFAULT_GATE_SCRIPTS_MAP
    assert cfg.QUALITY_GATES_PHASE_MAP == DEFAULT_QUALITY_GATES_PHASE_MAP
    assert cfg.HOOK_SCRIPTS_MAP == DEFAULT_HOOK_SCRIPTS_MAP


def test_yaml_overrides_gate_scripts(tmp_path: Path, monkeypatch):
    config_file = tmp_path / ".xuansto-config.yaml"
    config_file.write_text(
        textwrap.dedent("""\
        gate_scripts:
          GATE-999: custom-gate.py
    """),
        encoding="utf-8",
    )
    monkeypatch.setenv("XUANSTO_SKILL_ROOT", str(tmp_path))
    import xuansto_mcp.core.config as cfg

    importlib.reload(cfg)
    assert cfg.GATE_SCRIPTS_MAP == {"GATE-999": "custom-gate.py"}
    assert cfg.QUALITY_GATES_PHASE_MAP == DEFAULT_QUALITY_GATES_PHASE_MAP
    assert cfg.HOOK_SCRIPTS_MAP == DEFAULT_HOOK_SCRIPTS_MAP


def test_yaml_overrides_gates_by_phase(tmp_path: Path, monkeypatch):
    config_file = tmp_path / ".xuansto-config.yaml"
    config_file.write_text(
        textwrap.dedent("""\
        gates_by_phase:
          "0":
            - CUSTOM-GATE
    """),
        encoding="utf-8",
    )
    monkeypatch.setenv("XUANSTO_SKILL_ROOT", str(tmp_path))
    import xuansto_mcp.core.config as cfg

    importlib.reload(cfg)
    assert cfg.QUALITY_GATES_PHASE_MAP == {"0": ["CUSTOM-GATE"]}
    assert cfg.GATE_SCRIPTS_MAP == DEFAULT_GATE_SCRIPTS_MAP


def test_yaml_overrides_hook_scripts(tmp_path: Path, monkeypatch):
    config_file = tmp_path / ".xuansto-config.yaml"
    config_file.write_text(
        textwrap.dedent("""\
        hook_scripts:
          my-hook: my-script.py
    """),
        encoding="utf-8",
    )
    monkeypatch.setenv("XUANSTO_SKILL_ROOT", str(tmp_path))
    import xuansto_mcp.core.config as cfg

    importlib.reload(cfg)
    assert cfg.HOOK_SCRIPTS_MAP == {"my-hook": "my-script.py"}


def test_invalid_yaml_falls_back_to_defaults(tmp_path: Path, monkeypatch):
    config_file = tmp_path / ".xuansto-config.yaml"
    config_file.write_text("{{invalid: yaml: [", encoding="utf-8")
    monkeypatch.setenv("XUANSTO_SKILL_ROOT", str(tmp_path))
    import xuansto_mcp.core.config as cfg

    importlib.reload(cfg)
    assert cfg.GATE_SCRIPTS_MAP == DEFAULT_GATE_SCRIPTS_MAP
    assert cfg.QUALITY_GATES_PHASE_MAP == DEFAULT_QUALITY_GATES_PHASE_MAP
    assert cfg.HOOK_SCRIPTS_MAP == DEFAULT_HOOK_SCRIPTS_MAP


def test_hook_manage_imports_hook_scripts_from_config():
    mcp = pytest.importorskip("mcp")
    from xuansto_mcp.tools import hook_manage

    assert hook_manage.HOOK_SCRIPTS_MAP == DEFAULT_HOOK_SCRIPTS_MAP
