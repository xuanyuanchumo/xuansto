import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from xuansto_mcp.core.degradation import (
    check_mcp_available,
    run_script_fallback,
    get_fallback,
    FALLBACK_MAP,
)


def test_check_mcp_available():
    result = check_mcp_available()
    assert result is True


def test_fallback_map_has_all_tools():
    expected_tools = [
        "skill_analyze",
        "knowledge_search",
        "quality_gate_check",
        "spec_drift_detect",
        "security_scan",
        "code_simplify",
        "session_manage",
        "server_health",
    ]
    for tool_name in expected_tools:
        assert tool_name in FALLBACK_MAP, f"Missing fallback for: {tool_name}"


def test_get_fallback():
    fn = get_fallback("skill_analyze")
    assert fn is not None
    assert callable(fn)

    fn = get_fallback("nonexistent_tool")
    assert fn is None


def test_run_script_fallback_nonexistent():
    result = run_script_fallback("nonexistent_script.py")
    assert result["error"] is True
    assert result["code"] == "SCRIPT_NOT_FOUND"
    assert result["fallback"] is True
