import hashlib
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from xuansto_mcp.tools.resource_load_status import (
    _CACHE_TTL_SECONDS,
    _RESOURCE_CACHE,
    _check_resource_status,
    _compute_file_hash,
    _compute_path_hash,
    _is_cache_valid,
)


@pytest.fixture(autouse=True)
def clear_cache():
    _RESOURCE_CACHE.clear()
    yield
    _RESOURCE_CACHE.clear()


@pytest.fixture
def tmp_resource_file(tmp_path: Path):
    f = tmp_path / "test_resource.md"
    f.write_text("original content", encoding="utf-8")
    return f


@pytest.fixture
def tmp_resource_dir(tmp_path: Path):
    d = tmp_path / "test_dir"
    d.mkdir()
    (d / "a.md").write_text("aaa", encoding="utf-8")
    (d / "b.md").write_text("bbb", encoding="utf-8")
    return d


def _make_cache_entry(content: str, source_path: str, cached_at: float | None = None, ttl_seconds: int | None = None) -> dict:
    return {
        "content": content,
        "cached_at": cached_at if cached_at is not None else time.time(),
        "access_count": 0,
        "content_hash": _compute_path_hash(Path(source_path)) or "",
        "ttl_seconds": ttl_seconds if ttl_seconds is not None else _CACHE_TTL_SECONDS,
        "source_path": source_path,
    }


def test_compute_file_hash(tmp_resource_file: Path):
    h = _compute_file_hash(tmp_resource_file)
    expected = hashlib.sha256(b"original content").hexdigest()
    assert h == expected


def test_compute_path_hash_file(tmp_resource_file: Path):
    h = _compute_path_hash(tmp_resource_file)
    assert h is not None
    expected = hashlib.sha256(b"original content").hexdigest()
    assert h == expected


def test_compute_path_hash_directory(tmp_resource_dir: Path):
    h = _compute_path_hash(tmp_resource_dir)
    assert h is not None
    assert len(h) == 64


def test_compute_path_hash_nonexistent(tmp_path: Path):
    assert _compute_path_hash(tmp_path / "nonexistent") is None


def test_cache_entry_includes_new_fields(tmp_resource_file: Path):
    resource_id = "test-resource"
    _RESOURCE_CACHE[resource_id] = _make_cache_entry("original content", str(tmp_resource_file))
    entry = _RESOURCE_CACHE[resource_id]
    assert "content_hash" in entry
    assert "cached_at" in entry
    assert "ttl_seconds" in entry
    assert isinstance(entry["content_hash"], str)
    assert isinstance(entry["cached_at"], float)
    assert isinstance(entry["ttl_seconds"], int)
    assert len(entry["content_hash"]) == 64


def test_stale_detection_file_changed(tmp_resource_file: Path):
    resource_id = "test-resource"
    _RESOURCE_CACHE[resource_id] = _make_cache_entry("original content", str(tmp_resource_file))
    is_valid, validity = _is_cache_valid(resource_id)
    assert is_valid is True
    assert validity == "valid"

    tmp_resource_file.write_text("modified content", encoding="utf-8")
    is_valid, validity = _is_cache_valid(resource_id)
    assert is_valid is False
    assert validity == "stale"


def test_stale_detection_dir_changed(tmp_resource_dir: Path):
    resource_id = "test-resource"
    _RESOURCE_CACHE[resource_id] = _make_cache_entry("", str(tmp_resource_dir))
    is_valid, validity = _is_cache_valid(resource_id)
    assert is_valid is True
    assert validity == "valid"

    (tmp_resource_dir / "c.md").write_text("ccc", encoding="utf-8")
    is_valid, validity = _is_cache_valid(resource_id)
    assert is_valid is False
    assert validity == "stale"


def test_expired_detection(tmp_resource_file: Path):
    resource_id = "test-resource"
    _RESOURCE_CACHE[resource_id] = _make_cache_entry(
        "original content", str(tmp_resource_file),
        cached_at=time.time() - 7200,
    )
    is_valid, validity = _is_cache_valid(resource_id)
    assert is_valid is False
    assert validity == "expired"


def test_custom_ttl_expired(tmp_resource_file: Path):
    resource_id = "test-resource"
    _RESOURCE_CACHE[resource_id] = _make_cache_entry(
        "original content", str(tmp_resource_file),
        cached_at=time.time() - 60,
        ttl_seconds=30,
    )
    is_valid, validity = _is_cache_valid(resource_id)
    assert is_valid is False
    assert validity == "expired"


def test_custom_ttl_not_expired(tmp_resource_file: Path):
    resource_id = "test-resource"
    _RESOURCE_CACHE[resource_id] = _make_cache_entry(
        "original content", str(tmp_resource_file),
        cached_at=time.time() - 60,
        ttl_seconds=120,
    )
    is_valid, validity = _is_cache_valid(resource_id)
    assert is_valid is True
    assert validity == "valid"


def test_not_cached_returns_not_cached():
    is_valid, validity = _is_cache_valid("nonexistent-key")
    assert is_valid is False
    assert validity == "not_cached"


def test_check_resource_status_stale(tmp_resource_file: Path):
    resource_id = "test-resource"
    _RESOURCE_CACHE[resource_id] = _make_cache_entry("original content", str(tmp_resource_file))
    with patch("xuansto_mcp.tools.resource_load_status._get_loaded_resources", return_value=set()):
        status = _check_resource_status(resource_id, str(tmp_resource_file))
    assert status == "loaded"

    tmp_resource_file.write_text("modified content", encoding="utf-8")
    with patch("xuansto_mcp.tools.resource_load_status._get_loaded_resources", return_value=set()):
        status = _check_resource_status(resource_id, str(tmp_resource_file))
    assert status == "stale"


def test_check_resource_status_expired(tmp_resource_file: Path):
    resource_id = "test-resource"
    _RESOURCE_CACHE[resource_id] = _make_cache_entry(
        "original content", str(tmp_resource_file),
        cached_at=time.time() - 7200,
    )
    with patch("xuansto_mcp.tools.resource_load_status._get_loaded_resources", return_value=set()):
        status = _check_resource_status(resource_id, str(tmp_resource_file))
    assert status == "expired"


def test_check_resource_status_valid_cache(tmp_resource_file: Path):
    resource_id = "test-resource"
    _RESOURCE_CACHE[resource_id] = _make_cache_entry("original content", str(tmp_resource_file))
    with patch("xuansto_mcp.tools.resource_load_status._get_loaded_resources", return_value=set()):
        status = _check_resource_status(resource_id, str(tmp_resource_file))
    assert status == "loaded"


def test_preload_refreshes_stale(tmp_resource_file: Path):
    resource_id = "test-resource"
    _RESOURCE_CACHE[resource_id] = _make_cache_entry("original content", str(tmp_resource_file))

    tmp_resource_file.write_text("modified content", encoding="utf-8")
    is_valid, validity = _is_cache_valid(resource_id)
    assert validity == "stale"

    del _RESOURCE_CACHE[resource_id]
    _RESOURCE_CACHE[resource_id] = _make_cache_entry("modified content", str(tmp_resource_file))
    is_valid, validity = _is_cache_valid(resource_id)
    assert is_valid is True
    assert validity == "valid"


def test_preload_refreshes_expired(tmp_resource_file: Path):
    resource_id = "test-resource"
    _RESOURCE_CACHE[resource_id] = _make_cache_entry(
        "original content", str(tmp_resource_file),
        cached_at=time.time() - 7200,
    )
    is_valid, validity = _is_cache_valid(resource_id)
    assert validity == "expired"

    del _RESOURCE_CACHE[resource_id]
    _RESOURCE_CACHE[resource_id] = _make_cache_entry("original content", str(tmp_resource_file))
    is_valid, validity = _is_cache_valid(resource_id)
    assert is_valid is True
    assert validity == "valid"


def test_valid_cache_not_reloaded(tmp_resource_file: Path):
    resource_id = "test-resource"
    _RESOURCE_CACHE[resource_id] = _make_cache_entry("original content", str(tmp_resource_file))
    is_valid, validity = _is_cache_valid(resource_id)
    assert is_valid is True
    assert validity == "valid"
    original_cached_at = _RESOURCE_CACHE[resource_id]["cached_at"]
    original_hash = _RESOURCE_CACHE[resource_id]["content_hash"]
    time.sleep(0.01)
    is_valid2, validity2 = _is_cache_valid(resource_id)
    assert is_valid2 is True
    assert validity2 == "valid"
    assert _RESOURCE_CACHE[resource_id]["cached_at"] == original_cached_at
    assert _RESOURCE_CACHE[resource_id]["content_hash"] == original_hash


def test_hash_mismatch_takes_precedence_over_expired(tmp_resource_file: Path):
    resource_id = "test-resource"
    _RESOURCE_CACHE[resource_id] = _make_cache_entry(
        "original content", str(tmp_resource_file),
        cached_at=time.time() - 7200,
    )
    tmp_resource_file.write_text("modified content", encoding="utf-8")
    is_valid, validity = _is_cache_valid(resource_id)
    assert is_valid is False
    assert validity == "expired"
