import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from xuansto_mcp.tools.resource_load_status import _RESOURCE_CACHE, register


@pytest.fixture(autouse=True)
def _clear_cache():
    _RESOURCE_CACHE.clear()
    yield
    _RESOURCE_CACHE.clear()


@pytest.mark.asyncio
async def test_phase_preload_stores_nonempty_content_for_file(tmp_path: Path):
    from mcp.server.fastmcp import FastMCP
    from xuansto_mcp.tools import resource_load_status

    resource_file = tmp_path / "test_resource.md"
    resource_file.write_text("hello world content", encoding="utf-8")

    original_map = resource_load_status.PHASE_RESOURCE_MAP.copy()
    resource_load_status.PHASE_RESOURCE_MAP[0] = [
        {"id": "test-res-1", "type": "reference", "path": "test_resource.md"},
    ]
    original_root = resource_load_status.SKILL_ROOT
    resource_load_status.SKILL_ROOT = tmp_path

    try:
        test_mcp = FastMCP("test")
        register(test_mcp)
        tool_fn = test_mcp._tool_manager._tools["resource_load_status"].fn

        result = await tool_fn(action="preload", phase=0)
        data = result.get("data", result)
        assert data.get("phase") == 0
        preloaded = data.get("preloaded", [])
        assert any(p["id"] == "test-res-1" and p["status"] == "loaded" for p in preloaded)

        cached = _RESOURCE_CACHE.get("test-res-1")
        assert cached is not None, "Resource should be in cache"
        assert cached["content"] != "", "Cache content should NOT be empty"
        assert "hello world content" in cached["content"]
    finally:
        resource_load_status.SKILL_ROOT = original_root
        resource_load_status.PHASE_RESOURCE_MAP = original_map


@pytest.mark.asyncio
async def test_phase_preload_stores_nonempty_content_for_dir(tmp_path: Path):
    from mcp.server.fastmcp import FastMCP
    from xuansto_mcp.tools import resource_load_status

    resource_dir = tmp_path / "knowledge_dir"
    resource_dir.mkdir()
    (resource_dir / "file1.md").write_text("content of file1", encoding="utf-8")
    (resource_dir / "file2.md").write_text("content of file2", encoding="utf-8")

    original_map = resource_load_status.PHASE_RESOURCE_MAP.copy()
    resource_load_status.PHASE_RESOURCE_MAP[0] = [
        {"id": "test-dir-1", "type": "knowledge", "path": "knowledge_dir/"},
    ]
    original_root = resource_load_status.SKILL_ROOT
    resource_load_status.SKILL_ROOT = tmp_path

    try:
        test_mcp = FastMCP("test")
        register(test_mcp)
        tool_fn = test_mcp._tool_manager._tools["resource_load_status"].fn

        result = await tool_fn(action="preload", phase=0)
        data = result.get("data", result)
        preloaded = data.get("preloaded", [])
        assert any(p["id"] == "test-dir-1" and p["status"] == "loaded" for p in preloaded)

        cached = _RESOURCE_CACHE.get("test-dir-1")
        assert cached is not None
        assert cached["content"] != "", "Cache content should NOT be empty for directory"
        assert "content of file1" in cached["content"]
        assert "content of file2" in cached["content"]
    finally:
        resource_load_status.SKILL_ROOT = original_root
        resource_load_status.PHASE_RESOURCE_MAP = original_map


@pytest.mark.asyncio
async def test_phase_preload_content_hash_is_valid(tmp_path: Path):
    from mcp.server.fastmcp import FastMCP
    from xuansto_mcp.tools import resource_load_status

    resource_file = tmp_path / "hash_test.md"
    resource_file.write_text("hash me", encoding="utf-8")

    original_map = resource_load_status.PHASE_RESOURCE_MAP.copy()
    resource_load_status.PHASE_RESOURCE_MAP[0] = [
        {"id": "test-hash-1", "type": "reference", "path": "hash_test.md"},
    ]
    original_root = resource_load_status.SKILL_ROOT
    resource_load_status.SKILL_ROOT = tmp_path

    try:
        test_mcp = FastMCP("test")
        register(test_mcp)
        tool_fn = test_mcp._tool_manager._tools["resource_load_status"].fn

        await tool_fn(action="preload", phase=0)

        cached = _RESOURCE_CACHE.get("test-hash-1")
        assert cached is not None
        assert cached["content_hash"] != "", "content_hash should not be empty"
        assert len(cached["content_hash"]) == 64, "SHA-256 hex digest should be 64 chars"
    finally:
        resource_load_status.SKILL_ROOT = original_root
        resource_load_status.PHASE_RESOURCE_MAP = original_map
