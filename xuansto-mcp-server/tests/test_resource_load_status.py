import json
from pathlib import Path
from unittest.mock import patch

import pytest

from xuansto_mcp.tools.resource_load_status import (
    _check_resource_status,
    _get_loaded_resources,
    _get_state_file,
    _load_resource_state,
    _save_resource_state,
    _set_loaded_resources,
)


@pytest.fixture
def tmp_work_dir(tmp_path: Path):
    with patch("xuansto_mcp.tools.resource_load_status.WORK_DIR", tmp_path):
        yield tmp_path


@pytest.fixture(autouse=True)
def reset_loaded_resources():
    import xuansto_mcp.tools.resource_load_status as mod
    original = mod._loaded_resources
    mod._loaded_resources = None
    yield
    mod._loaded_resources = original


def test_preload_writes_to_file(tmp_work_dir: Path):
    state_file = tmp_work_dir / "resource_state.json"
    assert not state_file.exists()
    _set_loaded_resources({"skill-config", "agent-registry"})
    assert state_file.exists()
    data = json.loads(state_file.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    assert data["version"] == 1
    assert "updated_at" in data
    assert set(data["loaded"]) == {"skill-config", "agent-registry"}


def test_state_recovered_after_clearing_memory(tmp_work_dir: Path):
    import xuansto_mcp.tools.resource_load_status as mod

    _set_loaded_resources({"skill-config", "quality-gates"})
    mod._loaded_resources = None
    recovered = _get_loaded_resources()
    assert recovered == {"skill-config", "quality-gates"}


def test_status_reads_from_file(tmp_work_dir: Path):
    import xuansto_mcp.tools.resource_load_status as mod

    state_file = tmp_work_dir / "resource_state.json"
    state_file.write_text(json.dumps(["skill-config"]), encoding="utf-8")
    mod._loaded_resources = None
    with patch("xuansto_mcp.tools.resource_load_status.SKILL_ROOT", Path("/nonexistent")):
        status = _check_resource_status("skill-config", "references/agent-registry.md")
    assert status == "loaded"


def test_load_resource_state_empty(tmp_work_dir: Path):
    result = _load_resource_state()
    assert result == set()


def test_load_resource_state_from_file(tmp_work_dir: Path):
    state_file = tmp_work_dir / "resource_state.json"
    state_file.write_text(json.dumps(["a", "b", "c"]), encoding="utf-8")
    result = _load_resource_state()
    assert result == {"a", "b", "c"}


def test_load_resource_state_from_dict_format(tmp_work_dir: Path):
    state_file = tmp_work_dir / "resource_state.json"
    state_file.write_text(json.dumps({"version": 1, "updated_at": "2025-01-01T00:00:00Z", "loaded": ["a", "b"]}), encoding="utf-8")
    result = _load_resource_state()
    assert result == {"a", "b"}


def test_save_and_load_roundtrip(tmp_work_dir: Path):
    original = {"x", "y", "z"}
    _save_resource_state(original)
    loaded = _load_resource_state()
    assert loaded == original


def test_get_state_file_creates_work_dir(tmp_path: Path):
    nested = tmp_path / "deep" / "nested"
    with patch("xuansto_mcp.tools.resource_load_status.WORK_DIR", nested):
        result = _get_state_file()
        assert nested.exists()
        assert result == nested / "resource_state.json"
