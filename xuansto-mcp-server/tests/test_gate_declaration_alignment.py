from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from xuansto_mcp.tools.quality_gate_check import (
    DECLARED_GATE_IDS,
    INLINE_CHECKS,
    _is_cache_valid,
    _load_gate_cache,
    _save_gate_cache,
    _compute_file_hashes,
    register,
)
from mcp.server.fastmcp import FastMCP


DECLARED_GATE_IDS_SET = set(DECLARED_GATE_IDS)


class TestDeclarationAlignment:
    def test_declared_gate_ids_count(self):
        assert len(DECLARED_GATE_IDS) == 60, f"Expected 60 declared gate IDs, got {len(DECLARED_GATE_IDS)}"

    def test_inline_checks_contains_all_declared_gates(self):
        inline_keys = set(INLINE_CHECKS.keys())
        missing = DECLARED_GATE_IDS_SET - inline_keys
        assert not missing, f"INLINE_CHECKS missing declared gate IDs: {sorted(missing)}"

    def test_inline_checks_no_extra_primary_gates(self):
        inline_keys = set(INLINE_CHECKS.keys())
        extra = inline_keys - DECLARED_GATE_IDS_SET
        assert not extra, f"INLINE_CHECKS has gate IDs not in DECLARED_GATE_IDS: {sorted(extra)}"

    def test_none_valued_gates_are_declared(self):
        none_gates = {gid for gid, val in INLINE_CHECKS.items() if val is None}
        undeclared = none_gates - DECLARED_GATE_IDS_SET
        assert not undeclared, f"None-valued gates not in DECLARED_GATE_IDS: {sorted(undeclared)}"

    def test_function_valued_gates_are_callable(self):
        for gid, val in INLINE_CHECKS.items():
            if val is not None:
                assert callable(val), f"INLINE_CHECKS[{gid}] is not callable and not None"


class TestNoneGateSkipBehavior:
    @pytest.mark.asyncio
    async def test_none_gate_returns_skip_with_no_inline_check(self):
        mcp = FastMCP("test")
        register(mcp)

        none_gates = [gid for gid, val in INLINE_CHECKS.items() if val is None]
        assert len(none_gates) > 0, "Expected at least one None-valued gate"

        test_gate = none_gates[0]
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            tool_fn = None
            for name, fn in mcp._tool_manager._tools.items():
                if name == "quality_gate_check":
                    tool_fn = fn
                    break
            assert tool_fn is not None, "quality_gate_check tool not found"

            result = await tool_fn.fn(gate_ids=[test_gate], project_path=tmpdir, force_refresh=True)
            checks = result.get("data", result).get("checks", [])
            assert len(checks) == 1
            check = checks[0]
            assert check["gate_id"] == test_gate
            assert check["status"] == "SKIP"
            assert check["source"] == "no_inline_check"
            assert check.get("severity") == "WARN"

    @pytest.mark.asyncio
    async def test_all_none_gates_return_skip(self):
        mcp = FastMCP("test")
        register(mcp)

        none_gates = [gid for gid, val in INLINE_CHECKS.items() if val is None]
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            tool_fn = None
            for name, fn in mcp._tool_manager._tools.items():
                if name == "quality_gate_check":
                    tool_fn = fn
                    break
            result = await tool_fn.fn(gate_ids=none_gates, project_path=tmpdir, force_refresh=True)
            checks = result.get("data", result).get("checks", [])
            for check in checks:
                assert check["status"] == "SKIP", f"Gate {check['gate_id']} expected SKIP, got {check['status']}"
                assert check["source"] == "no_inline_check", f"Gate {check['gate_id']} expected source=no_inline_check, got {check.get('source')}"


class TestInlineGateSourceField:
    @pytest.mark.asyncio
    async def test_inline_gate_returns_source_inline(self):
        from xuansto_mcp.core.config import GATE_SCRIPTS_MAP

        mcp = FastMCP("test")
        register(mcp)

        inline_gates_no_script = [
            gid for gid, val in INLINE_CHECKS.items()
            if val is not None and gid not in GATE_SCRIPTS_MAP
        ]
        assert len(inline_gates_no_script) > 0, "Expected at least one inline gate without script mapping"

        test_gate = inline_gates_no_script[0]
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            tool_fn = None
            for name, fn in mcp._tool_manager._tools.items():
                if name == "quality_gate_check":
                    tool_fn = fn
                    break
            result = await tool_fn.fn(gate_ids=[test_gate], project_path=tmpdir, force_refresh=True)
            checks = result.get("data", result).get("checks", [])
            assert len(checks) >= 1
            check = checks[0]
            assert check["source"] == "inline", f"Expected source=inline for {test_gate}, got {check.get('source')}"

    @pytest.mark.asyncio
    async def test_inline_gate_with_missing_script_returns_source_inline(self):
        mcp = FastMCP("test")
        register(mcp)

        inline_gates = [gid for gid, val in INLINE_CHECKS.items() if val is not None]
        assert len(inline_gates) > 0

        test_gate = inline_gates[0]
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            tool_fn = None
            for name, fn in mcp._tool_manager._tools.items():
                if name == "quality_gate_check":
                    tool_fn = fn
                    break
            with patch("xuansto_mcp.tools.quality_gate_check.SCRIPTS_DIR") as mock_scripts:
                mock_scripts.__truediv__ = lambda s, o: Path("/nonexistent/scripts") / o
                result = await tool_fn.fn(gate_ids=[test_gate], project_path=tmpdir, force_refresh=True)
            checks = result.get("data", result).get("checks", [])
            assert len(checks) >= 1
            check = checks[0]
            assert check["source"] == "inline", f"Expected source=inline for {test_gate} (script fallback), got {check.get('source')}"


class TestCacheSourceField:
    def test_cached_results_include_source_cache(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir)
            cache_dir = project / ".xuansto"
            cache_dir.mkdir()

            fake_checks = [
                {
                    "gate_id": "TEST-PASS",
                    "status": "PASS",
                    "source": "inline",
                    "details": {"message": "Tests pass"},
                },
                {
                    "gate_id": "DESIGN-REVIEW-PRODUCT",
                    "status": "PASS",
                    "source": "inline",
                    "details": {"message": "Design review product passed"},
                },
            ]

            current_hashes = _compute_file_hashes(tmpdir)
            cache_data = {
                "file_hashes": current_hashes,
                "checks": fake_checks,
                "timestamp": time.time(),
            }
            _save_gate_cache(tmpdir, cache_data)

            loaded = _load_gate_cache(tmpdir)
            assert "checks" in loaded

            for c in loaded["checks"]:
                c["source"] = "cache"

            for c in loaded["checks"]:
                assert c["source"] == "cache", f"Cached check for {c['gate_id']} should have source=cache"

    @pytest.mark.asyncio
    async def test_cache_hit_path_adds_source_cache(self):
        mcp = FastMCP("test")
        register(mcp)

        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            tool_fn = None
            for name, fn in mcp._tool_manager._tools.items():
                if name == "quality_gate_check":
                    tool_fn = fn
                    break

            result = await tool_fn.fn(gate_ids=["TEST-PASS"], project_path=tmpdir, force_refresh=True)
            checks = result.get("data", result).get("checks", [])

            result2 = await tool_fn.fn(gate_ids=["TEST-PASS"], project_path=tmpdir, force_refresh=False)
            checks2 = result2.get("data", result2).get("checks", [])

            if result2.get("data", result2).get("cache_info", {}).get("hit"):
                for c in checks2:
                    assert c["source"] == "cache", f"Cache hit check for {c['gate_id']} should have source=cache, got {c.get('source')}"


class TestGateIdIntegrity:
    def test_declared_gate_ids_unique(self):
        assert len(DECLARED_GATE_IDS) == len(set(DECLARED_GATE_IDS)), "DECLARED_GATE_IDS contains duplicates"

    def test_inline_checks_keys_unique(self):
        keys = list(INLINE_CHECKS.keys())
        assert len(keys) == len(set(keys)), "INLINE_CHECKS contains duplicate keys"
