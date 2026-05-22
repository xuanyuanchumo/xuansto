import pytest
from mcp.server.fastmcp import FastMCP
from xuansto_mcp.tools.quality_gate_check import _resolve_gates


@pytest.mark.asyncio
async def test_quality_gate_check_registered():
    mcp = FastMCP("test")
    from xuansto_mcp.tools.quality_gate_check import register
    register(mcp)
    tools = await mcp.list_tools()
    tool_names = [t.name for t in tools]
    assert "quality_gate_check" in tool_names


def test_resolve_gates_by_phase():
    gates = _resolve_gates(None, "4")
    assert "GATE-007" in gates
    assert "TEST-PASS" in gates


def test_resolve_gates_by_ids():
    gates = _resolve_gates(["GATE-007", "TEST-PASS"], None)
    assert gates == ["GATE-007", "TEST-PASS"]


def test_resolve_gates_all():
    gates = _resolve_gates(None, None)
    assert len(gates) > 0
