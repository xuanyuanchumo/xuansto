from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from xuansto_mcp.tools.server_health import (
    _negotiate_api_version,
    _calculate_percentile,
    record_tool_call,
    _TOOL_METRICS,
    _metrics_lock,
)
from xuansto_mcp.core.config import MCP_API_VERSION, MCP_MIN_SUPPORTED_VERSION, API_CHANGELOG
from xuansto_mcp.core.errors import make_success_response, ERR_VALIDATION


class TestNegotiateVersion:
    def test_compatible_same_version(self):
        result = _negotiate_api_version(MCP_API_VERSION)
        assert result["compatible"] is True
        assert result["server_version"] == MCP_API_VERSION
        assert result["client_version"] == MCP_API_VERSION

    def test_compatible_minor_behind(self):
        result = _negotiate_api_version("3.0.0")
        if MCP_API_VERSION == "3.0.0":
            assert result["compatible"] is True

    def test_compatible_min_supported_version(self):
        result = _negotiate_api_version(MCP_MIN_SUPPORTED_VERSION)
        assert result["compatible"] is True
        assert "deprecated_features" in result

    def test_incompatible_major_mismatch(self):
        result = _negotiate_api_version("1.0.0")
        assert result["compatible"] is False
        assert "upgrade_suggestion" in result
        assert "Major version mismatch" in result["upgrade_suggestion"]

    def test_incompatible_client_newer(self):
        result = _negotiate_api_version("99.0.0")
        assert result["compatible"] is False
        assert "downgrade" in result["upgrade_suggestion"].lower() or "newer" in result["upgrade_suggestion"].lower()

    def test_invalid_version_format(self):
        result = _negotiate_api_version("0.0")
        assert result["compatible"] is False
        assert "upgrade" in result["upgrade_suggestion"].lower() or "mismatch" in result["upgrade_suggestion"].lower()

    def test_result_contains_server_version(self):
        result = _negotiate_api_version("2.0.0")
        assert result["server_version"] == MCP_API_VERSION

    def test_result_contains_client_version(self):
        result = _negotiate_api_version("2.5.0")
        assert result["client_version"] == "2.5.0"

    def test_result_contains_min_supported(self):
        result = _negotiate_api_version("2.0.0")
        assert result["min_supported_version"] == MCP_MIN_SUPPORTED_VERSION


class TestVersionComparison:
    def test_same_major_minor_behind(self):
        result = _negotiate_api_version("2.5.0")
        assert result["compatible"] is True
        assert len(result.get("new_features", [])) >= 0

    def test_same_major_same_minor(self):
        parts = MCP_API_VERSION.split(".")
        client_ver = f"{parts[0]}.{parts[1]}.0"
        result = _negotiate_api_version(client_ver)
        assert result["compatible"] is True

    def test_client_on_min_supported_gets_deprecated(self):
        result = _negotiate_api_version(MCP_MIN_SUPPORTED_VERSION)
        assert result["compatible"] is True
        assert isinstance(result.get("deprecated_features", []), list)

    def test_major_version_one_below_server(self):
        server_major = int(MCP_API_VERSION.split(".")[0])
        if server_major > 1:
            below_major = server_major - 1
            if str(below_major) != MCP_MIN_SUPPORTED_VERSION.split(".")[0]:
                result = _negotiate_api_version(f"{below_major}.0.0")
                assert result["compatible"] is False


class TestServerHealthActions:
    @pytest.mark.asyncio
    async def test_negotiate_version_action(self):
        captured = {}

        def mock_tool_decorator(**dkwargs):
            def dec(fn):
                captured["fn"] = fn
                return fn
            return dec

        mcp_mock = MagicMock()
        mcp_mock.tool = mock_tool_decorator
        from xuansto_mcp.tools.server_health import register
        register(mcp_mock)
        with patch("xuansto_mcp.server._REGISTERED_TOOL_NAMES", []):
            with patch("xuansto_mcp.server._REGISTERED_RESOURCE_NAMES", []):
                result = await captured["fn"](action="negotiate_version", client_version="2.0.0")
                assert result["error"] is False
                assert "compatible" in result["data"]

    @pytest.mark.asyncio
    async def test_negotiate_version_requires_client_version(self):
        captured = {}

        def mock_tool_decorator(**dkwargs):
            def dec(fn):
                captured["fn"] = fn
                return fn
            return dec

        mcp_mock = MagicMock()
        mcp_mock.tool = mock_tool_decorator
        from xuansto_mcp.tools.server_health import register
        register(mcp_mock)
        result = await captured["fn"](action="negotiate_version")
        assert result["error"] is True
        assert result["error_code"] == ERR_VALIDATION

    @pytest.mark.asyncio
    async def test_capabilities_action(self):
        captured = {}

        def mock_tool_decorator(**dkwargs):
            def dec(fn):
                captured["fn"] = fn
                return fn
            return dec

        mcp_mock = MagicMock()
        mcp_mock.tool = mock_tool_decorator
        from xuansto_mcp.tools.server_health import register
        register(mcp_mock)
        with patch("xuansto_mcp.server._REGISTERED_TOOL_NAMES", ["tool_a", "tool_b"]):
            with patch("xuansto_mcp.server._REGISTERED_RESOURCE_NAMES", ["res_a"]):
                with patch("xuansto_mcp.server._TOOL_REGISTRY", {}):
                    result = await captured["fn"](action="capabilities")
                    assert result["error"] is False
                    assert "tools" in result["data"]
                    assert "api_version" in result["data"]


class TestPercentileCalculation:
    def test_empty_values(self):
        assert _calculate_percentile([], 50) == 0.0

    def test_single_value(self):
        assert _calculate_percentile([100.0], 50) == 100.0

    def test_median(self):
        result = _calculate_percentile([10.0, 20.0, 30.0, 40.0, 50.0], 50)
        assert result == 30.0

    def test_p95(self):
        values = [float(i) for i in range(1, 101)]
        result = _calculate_percentile(values, 95)
        assert 94.0 <= result <= 96.0

    def test_p99(self):
        values = [float(i) for i in range(1, 101)]
        result = _calculate_percentile(values, 99)
        assert 98.0 <= result <= 100.0


class TestToolMetrics:
    def test_record_tool_call(self):
        with _metrics_lock:
            _TOOL_METRICS.clear()
        record_tool_call("test_tool", 50.0, True)
        with _metrics_lock:
            assert "test_tool" in _TOOL_METRICS
            assert _TOOL_METRICS["test_tool"]["call_count"] == 1
            assert _TOOL_METRICS["test_tool"]["error_count"] == 0

    def test_record_failed_tool_call(self):
        with _metrics_lock:
            _TOOL_METRICS.clear()
        record_tool_call("failing_tool", 100.0, False)
        with _metrics_lock:
            assert _TOOL_METRICS["failing_tool"]["error_count"] == 1

    def test_latency_tracking(self):
        with _metrics_lock:
            _TOOL_METRICS.clear()
        record_tool_call("lat_tool", 10.0, True)
        record_tool_call("lat_tool", 20.0, True)
        with _metrics_lock:
            assert len(_TOOL_METRICS["lat_tool"]["latencies"]) == 2


class TestApiChangelog:
    def test_changelog_has_entries(self):
        assert len(API_CHANGELOG) > 0

    def test_changelog_keys_are_valid_versions(self):
        for version in API_CHANGELOG:
            parts = version.split(".")
            assert len(parts) >= 2
            assert all(p.isdigit() for p in parts)

    def test_changelog_values_are_lists(self):
        for version, features in API_CHANGELOG.items():
            assert isinstance(features, list)
            for feat in features:
                assert isinstance(feat, str)
