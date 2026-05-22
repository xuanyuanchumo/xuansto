import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from xuansto_mcp.core.config import (
    DEFAULT_GATE_SCRIPTS_MAP,
    DEFAULT_HOOK_SCRIPTS_MAP,
    DEFAULT_QUALITY_GATES_PHASE_MAP,
    reload_config,
)


@pytest.fixture
def config_dir(tmp_path: Path):
    (tmp_path / ".xuansto-config.yaml").write_text("", encoding="utf-8")
    return tmp_path


def _write_config(config_dir: Path, content: str):
    (config_dir / ".xuansto-config.yaml").write_text(content, encoding="utf-8")


def _reload_with_root(config_dir: Path):
    with patch("xuansto_mcp.core.config.SKILL_ROOT", config_dir):
        return reload_config()


def test_invalid_yaml_rejected_and_config_preserved(config_dir: Path):
    _write_config(config_dir, "gate_scripts: [broken\n  indent: bad")
    with patch("xuansto_mcp.core.config.SKILL_ROOT", config_dir):
        with patch("xuansto_mcp.core.config.GATE_SCRIPTS_MAP", DEFAULT_GATE_SCRIPTS_MAP) as old_gate, \
             patch("xuansto_mcp.core.config.QUALITY_GATES_PHASE_MAP", DEFAULT_QUALITY_GATES_PHASE_MAP) as old_phase, \
             patch("xuansto_mcp.core.config.HOOK_SCRIPTS_MAP", DEFAULT_HOOK_SCRIPTS_MAP) as old_hook:
            result = reload_config()

    assert result.get("error") is True
    assert result["code"] == "YAML_PARSE_ERROR"
    assert "message" in result
    assert isinstance(result["message"], str)
    assert "validation_warnings" in result
    assert isinstance(result["validation_warnings"], list)


def test_wrong_field_types_skipped_with_warnings(config_dir: Path):
    _write_config(config_dir, "gate_scripts:\n  - not_a_dict\ngates_by_phase: 42\nhook_scripts: \"string\"")
    result = _reload_with_root(config_dir)

    assert "validation_warnings" in result
    warnings = result["validation_warnings"]
    assert len(warnings) == 3

    assert any("gate_scripts" in w and "list" in w for w in warnings)
    assert any("gates_by_phase" in w and "int" in w for w in warnings)
    assert any("hook_scripts" in w and "str" in w for w in warnings)

    assert result["gate_scripts_count"] == len(DEFAULT_GATE_SCRIPTS_MAP)
    assert result["gates_by_phase_count"] == len(DEFAULT_QUALITY_GATES_PHASE_MAP)
    assert result["hook_scripts_count"] == len(DEFAULT_HOOK_SCRIPTS_MAP)


def test_partial_wrong_types_uses_defaults_for_bad_fields(config_dir: Path):
    _write_config(config_dir, "gate_scripts:\n  CUSTOM-GATE: custom.py\ngates_by_phase: \"wrong\"")
    result = _reload_with_root(config_dir)

    assert result["gate_scripts_count"] == 1
    assert result["gates_by_phase_count"] == len(DEFAULT_QUALITY_GATES_PHASE_MAP)
    assert result["hook_scripts_count"] == len(DEFAULT_HOOK_SCRIPTS_MAP)

    warnings = result["validation_warnings"]
    assert len(warnings) == 1
    assert "gates_by_phase" in warnings[0]


def test_valid_yaml_with_correct_types(config_dir: Path):
    _write_config(config_dir, (
        "gate_scripts:\n"
        "  MY-GATE: my-script.py\n"
        "gates_by_phase:\n"
        "  0:\n"
        "    - GATE-A\n"
        "hook_scripts:\n"
        "  my-hook: my-hook.py\n"
    ))
    result = _reload_with_root(config_dir)

    assert "error" not in result
    assert result["gate_scripts_count"] == 1
    assert result["gates_by_phase_count"] == 1
    assert result["hook_scripts_count"] == 1
    assert result["validation_warnings"] == []


def test_empty_yaml_uses_defaults(config_dir: Path):
    _write_config(config_dir, "")
    result = _reload_with_root(config_dir)

    assert "error" not in result
    assert result["gate_scripts_count"] == len(DEFAULT_GATE_SCRIPTS_MAP)
    assert result["gates_by_phase_count"] == len(DEFAULT_QUALITY_GATES_PHASE_MAP)
    assert result["hook_scripts_count"] == len(DEFAULT_HOOK_SCRIPTS_MAP)
    assert result["validation_warnings"] == []


def test_missing_config_file_uses_defaults(tmp_path: Path):
    empty_dir = tmp_path / "no_config"
    empty_dir.mkdir()
    with patch("xuansto_mcp.core.config.SKILL_ROOT", empty_dir):
        result = reload_config()

    assert "error" not in result
    assert result["gate_scripts_count"] == len(DEFAULT_GATE_SCRIPTS_MAP)
    assert result["gates_by_phase_count"] == len(DEFAULT_QUALITY_GATES_PHASE_MAP)
    assert result["hook_scripts_count"] == len(DEFAULT_HOOK_SCRIPTS_MAP)
    assert result["validation_warnings"] == []


def test_yaml_top_level_non_dict_uses_defaults(config_dir: Path):
    _write_config(config_dir, "- just\n- a\n- list")
    result = _reload_with_root(config_dir)

    assert "error" not in result
    assert result["gate_scripts_count"] == len(DEFAULT_GATE_SCRIPTS_MAP)
    assert result["validation_warnings"] == []
