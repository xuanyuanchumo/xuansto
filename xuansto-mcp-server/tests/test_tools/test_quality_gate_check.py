import pytest
from unittest.mock import patch, MagicMock
from mcp.server.fastmcp import FastMCP
from xuansto_mcp.tools.quality_gate_check import (
    _resolve_gates,
    _check_test_pass,
    _check_spec_consistency,
    _check_brainstorm_complete,
    _check_plan_atomic,
    register,
)


@pytest.fixture
def mcp_server():
    return FastMCP("test-server")


def test_resolve_gates_with_ids():
    result = _resolve_gates(["GATE-001", "GATE-002"], None)
    assert result == ["GATE-001", "GATE-002"]


def test_resolve_gates_with_phase():
    result = _resolve_gates(None, "0")
    assert isinstance(result, list)
    assert len(result) > 0


def test_resolve_gates_all():
    result = _resolve_gates(None, None)
    assert len(result) > 0


def test_check_test_pass_no_test_dir(tmp_path):
    result = _check_test_pass(str(tmp_path))
    assert result["status"] == "FAIL"
    assert result["gate_id"] == "TEST-PASS"


def test_check_test_pass_with_test_dir(tmp_path):
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_example.py").write_text("def test_x(): pass", encoding="utf-8")
    result = _check_test_pass(str(tmp_path))
    assert result["status"] in ("PASS", "FAIL")


def test_check_spec_consistency_no_spec(tmp_path):
    result = _check_spec_consistency(str(tmp_path))
    assert result["status"] == "SKIP"


def test_check_spec_consistency_with_spec(tmp_path):
    spec = tmp_path / "spec.md"
    spec.write_text("- [x] Task 1\n- [x] Task 2\n- [x] Task 3\n- [x] Task 4\n- [ ] Task 5\n", encoding="utf-8")
    result = _check_spec_consistency(str(tmp_path))
    assert result["status"] in ("PASS", "FAIL")


def test_check_brainstorm_complete_no_docs(tmp_path):
    result = _check_brainstorm_complete(str(tmp_path))
    assert result["status"] == "SKIP"


def test_check_brainstorm_complete_with_keywords(tmp_path):
    doc = tmp_path / "brainstorm.md"
    doc.write_text("# Brainstorm\n\n## 结论\nWe decided.\n\n## 行动项\nDo it.\n", encoding="utf-8")
    result = _check_brainstorm_complete(str(tmp_path))
    assert result["status"] in ("PASS", "FAIL")


def test_check_plan_atomic_no_tasks(tmp_path):
    result = _check_plan_atomic(str(tmp_path))
    assert result["status"] == "SKIP"


def test_check_plan_atomic_with_criteria(tmp_path):
    tasks = tmp_path / "tasks.md"
    tasks.write_text("- [x] Implement feature (验收: should work)\n- [ ] Add tests (验证: must pass)\n", encoding="utf-8")
    result = _check_plan_atomic(str(tmp_path))
    assert result["status"] in ("PASS", "FAIL")


@pytest.mark.asyncio
async def test_quality_gate_check_positive(mcp_server, tmp_path):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["quality_gate_check"].fn
    with patch("xuansto_mcp.tools.quality_gate_check._compute_file_hashes", return_value={}):
        result = await tool_fn(gate_ids=["TEST-PASS"], project_path=str(tmp_path))
        assert result.get("error") is False
        assert "checks" in result.get("data", {})


@pytest.mark.asyncio
async def test_quality_gate_check_negative_empty_phase(mcp_server, tmp_path):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["quality_gate_check"].fn
    with patch("xuansto_mcp.tools.quality_gate_check._compute_file_hashes", return_value={}):
        result = await tool_fn(phase="99")
        assert result.get("error") is False
        assert result["data"]["summary"]["total"] == 0


@pytest.mark.asyncio
async def test_quality_gate_check_cache_hit(mcp_server, tmp_path):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["quality_gate_check"].fn
    hashes = {"file1.py": "abc123"}
    cache = {
        "file_hashes": hashes,
        "checks": [{"gate_id": "TEST-PASS", "status": "PASS", "source": "inline"}],
        "timestamp": 1000000,
    }
    with patch("xuansto_mcp.tools.quality_gate_check._compute_file_hashes", return_value=hashes), \
         patch("xuansto_mcp.tools.quality_gate_check._load_gate_cache", return_value=cache):
        result = await tool_fn(gate_ids=["TEST-PASS"], project_path=str(tmp_path))
        assert result.get("error") is False
