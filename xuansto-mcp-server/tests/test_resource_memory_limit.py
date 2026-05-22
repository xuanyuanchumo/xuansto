from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from xuansto_mcp.tools.resource_load_status import (
    _MAX_RESOURCE_SIZE_BYTES,
    _MAX_SINGLE_FILE_BYTES,
    _read_resource_content,
    _RESOURCE_CACHE,
)


@pytest.fixture(autouse=True)
def clear_cache():
    _RESOURCE_CACHE.clear()
    yield
    _RESOURCE_CACHE.clear()


@pytest.fixture
def resource_dir(tmp_path: Path):
    d = tmp_path / "agents"
    d.mkdir()
    return d


def _patch_resolve(uri: str, source_path: Path | None):
    def _resolve(u: str):
        if u == uri:
            return source_path
        return None

    return _resolve


def test_small_files_read_normally(resource_dir: Path):
    (resource_dir / "a.md").write_text("hello", encoding="utf-8")
    (resource_dir / "b.md").write_text("world", encoding="utf-8")
    uri = "xuansto://agents/registry"
    with patch("xuansto_mcp.tools.resource_load_status._resolve_uri_source_path", _patch_resolve(uri, resource_dir)):
        result = _read_resource_content(uri)
    assert result["content"] is not None
    assert "hello" in result["content"]
    assert "world" in result["content"]
    assert result["truncated"] is False
    assert result["skipped_large_files"] == []


def test_single_file_over_limit_skipped(resource_dir: Path):
    big_file = resource_dir / "big.md"
    big_file.write_bytes(b"x" * (_MAX_SINGLE_FILE_BYTES + 1))
    small_file = resource_dir / "small.md"
    small_file.write_text("ok", encoding="utf-8")
    uri = "xuansto://agents/registry"
    with patch("xuansto_mcp.tools.resource_load_status._resolve_uri_source_path", _patch_resolve(uri, resource_dir)):
        result = _read_resource_content(uri)
    assert result["content"] is not None
    assert "ok" in result["content"]
    assert len(result["skipped_large_files"]) == 1
    assert "big.md" in result["skipped_large_files"][0]
    assert result["truncated"] is False


def test_total_over_limit_truncated(resource_dir: Path):
    for i in range(12):
        f = resource_dir / f"file_{i:02d}.md"
        f.write_bytes(b"x" * (1 * 1024 * 1024))
    uri = "xuansto://agents/registry"
    with patch("xuansto_mcp.tools.resource_load_status._resolve_uri_source_path", _patch_resolve(uri, resource_dir)):
        result = _read_resource_content(uri)
    assert result["truncated"] is True


def test_truncated_flag_in_result(resource_dir: Path):
    small_file = resource_dir / "tiny.md"
    small_file.write_text("hi", encoding="utf-8")
    uri = "xuansto://agents/registry"
    with patch("xuansto_mcp.tools.resource_load_status._resolve_uri_source_path", _patch_resolve(uri, resource_dir)):
        result = _read_resource_content(uri)
    assert "truncated" in result
    assert result["truncated"] is False


def test_skipped_large_files_listed(resource_dir: Path):
    for i in range(3):
        f = resource_dir / f"large_{i}.md"
        f.write_bytes(b"x" * (_MAX_SINGLE_FILE_BYTES + 100))
    uri = "xuansto://agents/registry"
    with patch("xuansto_mcp.tools.resource_load_status._resolve_uri_source_path", _patch_resolve(uri, resource_dir)):
        result = _read_resource_content(uri)
    assert len(result["skipped_large_files"]) == 3
    for name in result["skipped_large_files"]:
        assert "large_" in name
