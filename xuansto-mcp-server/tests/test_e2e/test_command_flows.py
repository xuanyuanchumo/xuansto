import pytest
from unittest.mock import patch, MagicMock
from mcp.server.fastmcp import FastMCP


@pytest.fixture
def mcp_server():
    return FastMCP("test-e2e")


@pytest.mark.asyncio
async def test_init_command_flow(mcp_server, tmp_path):
    from xuansto_mcp.tools.project_init import register
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["project_init"].fn
    with patch("xuansto_mcp.tools.project_init.notify"):
        create_result = await tool_fn(action="create", name="my-project", stack=["python"], directory=str(tmp_path / "my-project"))
        assert create_result["error"] is False
        validate_result = await tool_fn(action="validate", project_path=str(tmp_path / "my-project"))
        assert validate_result["error"] is False
        assert validate_result["data"]["valid"] is True
        detect_result = await tool_fn(action="detect_stack", project_path=str(tmp_path / "my-project"))
        assert detect_result["error"] is False


@pytest.mark.asyncio
async def test_sprint_command_flow(mcp_server, tmp_path):
    from xuansto_mcp.tools.workflow_dispatch import register as wd_register
    from xuansto_mcp.tools.quality_gate_check import register as qg_register
    wd_register(mcp_server)
    qg_register(mcp_server)
    wd_fn = mcp_server._tool_manager._tools["workflow_dispatch"].fn
    with patch("xuansto_mcp.tools.workflow_dispatch._start_workflow") as mock_start:
        mock_start.return_value = {
            "workflow_id": "wf-sprint-001",
            "workflow": "sdd-tdd-fast",
            "project_path": str(tmp_path),
            "status": "running",
            "current_phase": 0,
        }
        start_result = await wd_fn(action="start", workflow="sdd-tdd-fast", project_path=str(tmp_path))
        assert start_result["error"] is False
    with patch("xuansto_mcp.tools.workflow_dispatch._current_phase") as mock_phase:
        mock_phase.return_value = {
            "workflow_id": "wf-sprint-001",
            "current_phase": 0,
            "phase_name": "初始化",
            "completed_phases": [],
            "remaining_phases": 8,
            "status": "running",
        }
        status_result = await wd_fn(action="phase", workflow_id="wf-sprint-001", phase_action="current")
        assert status_result["error"] is False


@pytest.mark.asyncio
async def test_review_command_flow(mcp_server, tmp_path):
    from xuansto_mcp.tools.quality_gate_check import register as qg_register
    from xuansto_mcp.tools.security_scan import register as sec_register
    qg_register(mcp_server)
    sec_register(mcp_server)
    qg_fn = mcp_server._tool_manager._tools["quality_gate_check"].fn
    sec_fn = mcp_server._tool_manager._tools["security_scan"].fn
    with patch("xuansto_mcp.tools.quality_gate_check._compute_file_hashes", return_value={}):
        gate_result = await qg_fn(gate_ids=["TEST-PASS"], project_path=str(tmp_path))
        assert gate_result["error"] is False
    with patch("xuansto_mcp.tools.security_scan.run_script") as mock_run:
        mock_run.return_value = {"error": True, "message": "script not found"}
        sec_result = await sec_fn(target=str(tmp_path))
        assert sec_result["error"] is False


@pytest.mark.asyncio
async def test_audit_command_flow(mcp_server, tmp_path):
    from xuansto_mcp.tools.quality_gate_check import register as qg_register
    from xuansto_mcp.tools.decision_log import register as dl_register
    qg_register(mcp_server)
    dl_register(mcp_server)
    qg_fn = mcp_server._tool_manager._tools["quality_gate_check"].fn
    dl_fn = mcp_server._tool_manager._tools["decision_log"].fn
    decisions_file = tmp_path / "decisions.json"
    with patch("xuansto_mcp.tools.quality_gate_check._compute_file_hashes", return_value={}):
        gate_result = await qg_fn(gate_ids=["SPEC-CONSISTENCY"], project_path=str(tmp_path))
        assert gate_result["error"] is False
    with patch("xuansto_mcp.tools.decision_log.DECISIONS_FILE", decisions_file), \
         patch("xuansto_mcp.tools.decision_log.notify"):
        log_result = await dl_fn(action="log", title="Audit decision", decision="Pass audit")
        assert log_result["error"] is False
        query_result = await dl_fn(action="query", keyword="audit")
        assert query_result["error"] is False


@pytest.mark.asyncio
async def test_full_init_to_sprint_flow(mcp_server, tmp_path):
    from xuansto_mcp.tools.project_init import register as pi_register
    from xuansto_mcp.tools.token_budget import register as tb_register
    pi_register(mcp_server)
    tb_register(mcp_server)
    pi_fn = mcp_server._tool_manager._tools["project_init"].fn
    tb_fn = mcp_server._tool_manager._tools["token_budget"].fn
    budget_file = tmp_path / "token_budget.json"
    with patch("xuansto_mcp.tools.project_init.notify"):
        init_result = await pi_fn(action="create", name="full-flow-project", directory=str(tmp_path / "full-flow"))
        assert init_result["error"] is False
    with patch("xuansto_mcp.tools.token_budget.BUDGET_FILE", budget_file), \
         patch("xuansto_mcp.tools.token_budget.notify"):
        budget_result = await tb_fn(action="set_budget", total_budget=150000)
        assert budget_result["error"] is False
        rec_result = await tb_fn(action="recommend", project_size="medium", complexity="high")
        assert rec_result["error"] is False
