import sys
import json
import pytest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from xuansto_mcp.tools.quality_gate_check import (
    _compute_file_hashes,
    _load_gate_cache,
    _save_gate_cache,
    _is_cache_valid,
)


def test_compute_file_hashes_returns_dict(tmp_path: Path):
    (tmp_path / "test.py").write_text("print('hello')", encoding="utf-8")
    hashes = _compute_file_hashes(str(tmp_path))
    assert isinstance(hashes, dict)
    assert len(hashes) > 0
    for k, v in hashes.items():
        assert isinstance(k, str)
        assert isinstance(v, str)
        assert len(v) == 64


def test_compute_file_hashes_skips_git(tmp_path: Path):
    (tmp_path / ".git" / "objects").mkdir(parents=True)
    (tmp_path / ".git" / "objects" / "abc").write_text("data", encoding="utf-8")
    (tmp_path / "src.py").write_text("code", encoding="utf-8")
    hashes = _compute_file_hashes(str(tmp_path))
    assert not any(".git" in k for k in hashes.keys())
    assert any("src.py" in k for k in hashes.keys())


def test_save_and_load_gate_cache(tmp_path: Path):
    cache = {"file_hashes": {"a.py": "abc123"}, "checks": [], "timestamp": 1000.0}
    _save_gate_cache(str(tmp_path), cache)
    loaded = _load_gate_cache(str(tmp_path))
    assert loaded == cache


def test_load_gate_cache_no_file(tmp_path: Path):
    result = _load_gate_cache(str(tmp_path))
    assert result == {}


def test_is_cache_valid_same_hashes():
    hashes = {"a.py": "abc123", "b.py": "def456"}
    cache = {"file_hashes": {"a.py": "abc123", "b.py": "def456"}}
    assert _is_cache_valid(cache, hashes) is True


def test_is_cache_valid_different_hashes():
    hashes = {"a.py": "abc123", "b.py": "CHANGED"}
    cache = {"file_hashes": {"a.py": "abc123", "b.py": "def456"}}
    assert _is_cache_valid(cache, hashes) is False


def test_is_cache_valid_missing_files():
    hashes = {"a.py": "abc123", "b.py": "def456", "c.py": "new"}
    cache = {"file_hashes": {"a.py": "abc123", "b.py": "def456"}}
    assert _is_cache_valid(cache, hashes) is False


def test_is_cache_valid_empty_cache():
    hashes = {"a.py": "abc123"}
    assert _is_cache_valid({}, hashes) is False


@pytest.mark.asyncio
async def test_quality_gate_check_returns_cache_info(tmp_path: Path):
    from xuansto_mcp.tools.quality_gate_check import register
    from mcp.server.fastmcp import FastMCP

    test_mcp = FastMCP("test")
    register(test_mcp)
    tool_fn = test_mcp._tool_manager._tools["quality_gate_check"].fn

    result = await tool_fn(gate_ids=["GATE-007"], project_path=str(tmp_path))
    assert "cache_info" in result.get("data", result)
    cache_info = result["data"]["cache_info"] if "data" in result else result["cache_info"]
    assert "hit" in cache_info
    assert "hit_count" in cache_info
    assert "miss_count" in cache_info
    assert "cache_age_seconds" in cache_info
