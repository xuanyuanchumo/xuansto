import sys
import pytest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from xuansto_mcp.core.config import reload_config, _get_config_mtime, start_config_watcher, stop_config_watcher


def test_reload_config_returns_counts(tmp_path):
    valid_config = tmp_path / ".xuansto-config.yaml"
    valid_config.write_text("gate_scripts: {}\ngates_by_phase: {}\nhook_scripts: {}\n", encoding="utf-8")
    with patch("xuansto_mcp.core.config.SKILL_ROOT", tmp_path):
        result = reload_config()
    assert "gate_scripts_count" in result
    assert "gates_by_phase_count" in result
    assert "hook_scripts_count" in result
    assert isinstance(result["gate_scripts_count"], int)


def test_get_config_mtime_returns_float():
    mtime = _get_config_mtime()
    assert isinstance(mtime, float)
    assert mtime >= 0


def test_start_stop_config_watcher():
    start_config_watcher()
    stop_config_watcher()
