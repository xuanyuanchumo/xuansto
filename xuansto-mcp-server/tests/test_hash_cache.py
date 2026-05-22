from __future__ import annotations

import hashlib
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from xuansto_mcp.tools.quality_gate_check import (
    _MAX_SCAN_DEPTH,
    _MAX_SCAN_FILES,
    _SKIP_HASH_DIRS,
    _compute_file_hashes,
    _file_hash_cache,
    _file_mtime_cache,
)


@pytest.fixture(autouse=True)
def _clear_caches():
    keys_before = set(_file_hash_cache.keys()) | set(_file_mtime_cache.keys())
    yield
    for key in list(_file_hash_cache.keys()):
        if key not in keys_before:
            _file_hash_cache.pop(key, None)
    for key in list(_file_mtime_cache.keys()):
        if key not in keys_before:
            _file_mtime_cache.pop(key, None)


@pytest.fixture()
def project_dir(tmp_path: Path) -> Path:
    return tmp_path


def _sha256_of(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def test_hash_cache_hit(project_dir: Path):
    (project_dir / "a.py").write_bytes(b"print('hello')")
    result1 = _compute_file_hashes(str(project_dir))
    assert "a.py" in result1

    with patch("xuansto_mcp.tools.quality_gate_check.hashlib.sha256") as mock_sha:
        result2 = _compute_file_hashes(str(project_dir))
        mock_sha.assert_not_called()

    assert result2 == result1


def test_hash_cache_invalidate_on_change(project_dir: Path):
    f = project_dir / "a.py"
    f.write_bytes(b"v1")
    result1 = _compute_file_hashes(str(project_dir))

    time.sleep(0.05)
    f.write_bytes(b"v2")

    result2 = _compute_file_hashes(str(project_dir))
    assert result2["a.py"] != result1["a.py"]
    assert result2["a.py"] == _sha256_of(b"v2")


def test_hash_cache_remove_deleted(project_dir: Path):
    f = project_dir / "a.py"
    f.write_bytes(b"content")
    result1 = _compute_file_hashes(str(project_dir))
    assert "a.py" in result1

    f.unlink()
    result2 = _compute_file_hashes(str(project_dir))
    assert "a.py" not in result2


def test_hash_cache_add_new(project_dir: Path):
    (project_dir / "a.py").write_bytes(b"existing")
    result1 = _compute_file_hashes(str(project_dir))
    assert "a.py" in result1
    assert "b.py" not in result1

    (project_dir / "b.py").write_bytes(b"new_file")
    result2 = _compute_file_hashes(str(project_dir))
    assert "b.py" in result2
    assert result2["b.py"] == _sha256_of(b"new_file")


def test_hash_cache_force_refresh(project_dir: Path):
    (project_dir / "a.py").write_bytes(b"content")
    result1 = _compute_file_hashes(str(project_dir))

    proj_key = str(project_dir.resolve())
    assert proj_key in _file_hash_cache

    result2 = _compute_file_hashes(str(project_dir), force_refresh=True)
    assert result2 == result1
    assert proj_key in _file_hash_cache


def test_scan_depth_limit(project_dir: Path):
    deep_dir = project_dir
    for i in range(_MAX_SCAN_DEPTH + 2):
        deep_dir = deep_dir / f"level{i}"
    deep_dir.mkdir(parents=True, exist_ok=True)
    (deep_dir / "deep.py").write_bytes(b"deep file")

    shallow_file = project_dir / "shallow.py"
    shallow_file.write_bytes(b"shallow")

    result = _compute_file_hashes(str(project_dir))
    assert "shallow.py" in result
    assert "deep.py" not in result


def test_scan_file_limit(project_dir: Path):
    for i in range(_MAX_SCAN_FILES + 100):
        (project_dir / f"file_{i:05d}.py").write_bytes(f"content {i}".encode())

    result = _compute_file_hashes(str(project_dir))
    assert len(result) <= _MAX_SCAN_FILES


def test_skip_common_dirs(project_dir: Path):
    for skip_dir in _SKIP_HASH_DIRS:
        d = project_dir / skip_dir
        d.mkdir(parents=True, exist_ok=True)
        (d / "skipped.py").write_bytes(b"should be skipped")

    (project_dir / "included.py").write_bytes(b"should be included")

    result = _compute_file_hashes(str(project_dir))
    assert "included.py" in result
    for skip_dir in _SKIP_HASH_DIRS:
        assert f"{skip_dir}/skipped.py" not in result
