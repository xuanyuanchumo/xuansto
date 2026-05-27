from __future__ import annotations

import ast
import inspect
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from xuansto_mcp.core.config import MCP_API_VERSION, MCP_MIN_SUPPORTED_VERSION
from xuansto_mcp.tools.server_health import _negotiate_api_version


def test_negotiate_api_version_exists_in_server_health():
    import xuansto_mcp.tools.server_health as sh_mod
    assert hasattr(sh_mod, "_negotiate_api_version")
    assert callable(sh_mod._negotiate_api_version)


def test_no_duplicate_negotiation_in_api_routes():
    api_routes_path = Path(__file__).resolve().parent.parent / "src" / "xuansto_mcp" / "api" / "api_routes.py"
    if not api_routes_path.exists():
        pytest.skip("api/api_routes.py not found")
    source = api_routes_path.read_text(encoding="utf-8")
    assert "_negotiate_api_version" in source, "api_routes.py should import _negotiate_api_version"
    assert "from ..tools.server_health import _negotiate_api_version" in source or \
           "from .server_health import _negotiate_api_version" in source, \
           "api_routes.py should import _negotiate_api_version from server_health"


def test_no_duplicate_negotiation_in_root_api_routes():
    api_routes_path = Path(__file__).resolve().parent.parent / "src" / "xuansto_mcp" / "api_routes.py"
    if not api_routes_path.exists():
        pytest.skip("api_routes.py not found")
    source = api_routes_path.read_text(encoding="utf-8")
    assert "_negotiate_api_version" in source, "api_routes.py should import _negotiate_api_version"
    assert "from .tools.server_health import _negotiate_api_version" in source, \
           "api_routes.py should import _negotiate_api_version from server_health"


def test_no_inline_version_negotiation_logic_in_api_routes():
    for rel_path in [
        "src/xuansto_mcp/api/api_routes.py",
        "src/xuansto_mcp/api_routes.py",
    ]:
        path = Path(__file__).resolve().parent.parent / rel_path
        if not path.exists():
            continue
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_source = ast.get_source_segment(source, node)
                if func_source and "negotiate" in func_source.lower():
                    assert "_negotiate_api_version" in func_source, (
                        f"{rel_path} function '{node.name}' should delegate to "
                        f"_negotiate_api_version instead of implementing negotiation logic"
                    )


def test_http_and_mcp_negotiation_results_consistent():
    result_mcp = _negotiate_api_version(MCP_API_VERSION)
    assert result_mcp["compatible"] is True
    assert result_mcp["server_version"] == MCP_API_VERSION
    assert result_mcp["client_version"] == MCP_API_VERSION

    result_min = _negotiate_api_version(MCP_MIN_SUPPORTED_VERSION)
    assert result_min["compatible"] is True

    result_incompatible = _negotiate_api_version("1.0.0")
    assert result_incompatible["compatible"] is False

    result_newer = _negotiate_api_version("99.0.0")
    assert result_newer["compatible"] is False


def test_single_implementation_of_negotiate():
    src_dir = Path(__file__).resolve().parent.parent / "src" / "xuansto_mcp"
    implementations = []
    for py_file in src_dir.rglob("*.py"):
        source = py_file.read_text(encoding="utf-8")
        if "def _negotiate_api_version" in source:
            implementations.append(str(py_file.relative_to(src_dir)))
    assert len(implementations) == 1, (
        f"Expected exactly 1 implementation of _negotiate_api_version, "
        f"found {len(implementations)}: {implementations}"
    )
    assert "server_health.py" in implementations[0], (
        f"_negotiate_api_version should be in tools/server_health.py, "
        f"found in {implementations[0]}"
    )
