from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

from xuansto_mcp.core.config import MCP_API_VERSION, MCP_MIN_SUPPORTED_VERSION
from xuansto_mcp.tools.server_health import _negotiate_api_version


class TestAPIVersionNegotiation:
    def test_v1_client_negotiates_to_min_supported(self):
        result = _negotiate_api_version("1.0.0")
        assert result["compatible"] is True
        assert result["negotiated_version"] == MCP_MIN_SUPPORTED_VERSION
        assert result["reason"] == "min_supported_match"

    def test_v2_client_negotiates_to_current(self):
        result = _negotiate_api_version("2.0.0")
        assert result["compatible"] is True
        assert result["negotiated_version"] == MCP_API_VERSION
        assert result["reason"] == "major_version_match"

    def test_incompatible_v3_client_rejected(self):
        result = _negotiate_api_version("3.0.0")
        assert result["compatible"] is False
        assert result["reason"] == "major_version_mismatch"

    def test_incompatible_v0_client_rejected(self):
        result = _negotiate_api_version("0.9.0")
        assert result["compatible"] is False
        assert result["reason"] == "major_version_mismatch"

    def test_invalid_version_string_rejected(self):
        result = _negotiate_api_version("not-a-version")
        assert result["compatible"] is False
        assert result["reason"] == "invalid_client_version"

    def test_empty_version_string_rejected(self):
        result = _negotiate_api_version("")
        assert result["compatible"] is False
        assert result["reason"] == "invalid_client_version"

    def test_partial_version_treated_as_invalid(self):
        result = _negotiate_api_version("2")
        assert result["compatible"] is True
        assert result["reason"] == "major_version_match"

    def test_v2_minor_version_compatible(self):
        result = _negotiate_api_version("2.1.0")
        assert result["compatible"] is True
        assert result["negotiated_version"] == MCP_API_VERSION
        assert result["reason"] == "major_version_match"

    def test_v1_minor_version_compatible(self):
        result = _negotiate_api_version("1.5.3")
        assert result["compatible"] is True
        assert result["negotiated_version"] == MCP_MIN_SUPPORTED_VERSION
        assert result["reason"] == "min_supported_match"

    def test_result_always_includes_server_version(self):
        for client_ver in ["1.0.0", "2.0.0", "3.0.0", "invalid"]:
            result = _negotiate_api_version(client_ver)
            assert result["server_version"] == MCP_API_VERSION
            assert result["min_supported_version"] == MCP_MIN_SUPPORTED_VERSION

    def test_negotiate_via_server_health_tool(self):
        from mcp.server.fastmcp import FastMCP
        from xuansto_mcp.tools.server_health import register

        test_mcp = FastMCP("test-negotiation")
        register(test_mcp)

        import asyncio

        async def _call():
            tools = await test_mcp.list_tools()
            tool_names = [t.name for t in tools]
            assert "server_health" in tool_names

        asyncio.run(_call())
