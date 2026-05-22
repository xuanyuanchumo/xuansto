import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from mcp.server.fastmcp import FastMCP

NOTE = (
    "For deeper MCP protocol-level integration tests (stdio transport, "
    "real subprocess server, ClientSession-based tool calls and resource "
    "listing), see tests/test_mcp_protocol.py"
)


@pytest.fixture
def mcp_server():
    from xuansto_mcp.server import mcp
    return mcp


@pytest.mark.asyncio
async def test_server_has_all_tools(mcp_server):
    tools = await mcp_server.list_tools()
    tool_names = [t.name for t in tools]
    expected_tools = [
        "skill_analyze",
        "knowledge_search",
        "quality_gate_check",
        "spec_drift_detect",
        "security_scan",
        "code_simplify",
        "session_manage",
        "workflow_dispatch",
        "agent_status",
        "hook_manage",
        "resource_load_status",
        "context_compress",
        "server_health",
    ]
    for tool_name in expected_tools:
        assert tool_name in tool_names, f"Missing tool: {tool_name}"
    assert len(tool_names) == len(expected_tools), f"Expected {len(expected_tools)} tools, got {len(tool_names)}: {tool_names}"


@pytest.mark.asyncio
async def test_server_name(mcp_server):
    assert mcp_server.name == "xuansto-mcp-server"


def test_server_import():
    from xuansto_mcp.server import mcp, main
    assert mcp is not None
    assert callable(main)


def test_all_tool_modules_register():
    from xuansto_mcp.tools import (
        skill_analyze,
        knowledge_search,
        quality_gate_check,
        spec_drift_detect,
        security_scan,
        code_simplify,
        session_manage,
        workflow_dispatch,
        agent_status,
        hook_manage,
        resource_load_status,
        context_compress,
        server_health,
    )
    test_mcp = FastMCP("test-registration")
    for module in [
        skill_analyze,
        knowledge_search,
        quality_gate_check,
        spec_drift_detect,
        security_scan,
        code_simplify,
        session_manage,
        workflow_dispatch,
        agent_status,
        hook_manage,
        resource_load_status,
        context_compress,
        server_health,
    ]:
        module.register(test_mcp)
    registered_tools = list(test_mcp._tool_manager._tools.keys())
    assert len(registered_tools) == 13


def test_pydantic_models_valid():
    from xuansto_mcp.models.schemas import (
        SkillAnalyzeInput,
        KnowledgeSearchInput,
        QualityGateCheckInput,
        SpecDriftDetectInput,
        SecurityScanInput,
        CodeSimplifyInput,
        SessionManageInput,
        WorkflowDispatchInput,
        AgentStatusInput,
        HookManageInput,
        ResourceLoadStatusInput,
        ContextCompressInput,
    )
    sa = SkillAnalyzeInput(skill_path="/tmp/test")
    assert sa.depth == "basic"
    assert sa.include_scripts is True

    ks = KnowledgeSearchInput(query="test query")
    assert ks.top_k == 5
    assert ks.search_type == "hybrid"

    qg = QualityGateCheckInput()
    assert qg.project_path == "."

    sd = SpecDriftDetectInput()
    assert sd.spec_dir == ".trae/specs"

    ss = SecurityScanInput()
    assert ss.severity_threshold == "medium"

    cs = CodeSimplifyInput(target="/tmp/test")
    assert cs.scope == "recent"

    sm = SessionManageInput(action="save")
    assert sm.action == "save"

    wd = WorkflowDispatchInput(action="start", workflow="sdd-tdd-full")
    assert wd.action == "start"
    assert wd.workflow == "sdd-tdd-full"
    assert wd.project_path == "."

    ast = AgentStatusInput(action="list")
    assert ast.action == "list"
    assert ast.phase is None

    hm = HookManageInput(action="list")
    assert hm.action == "list"
    assert hm.profile == "standard"

    rls = ResourceLoadStatusInput(action="status")
    assert rls.action == "status"
    assert rls.phase is None

    cc = ContextCompressInput(content="test content")
    assert cc.strategy == "semantic"
    assert cc.target_tokens == 2000


def test_error_response_format():
    from xuansto_mcp.core.errors import (
        make_error_response,
        make_success_response,
        PathNotFoundError,
        ScriptExecutionError,
        DegradationError,
    )
    err = PathNotFoundError("/bad/path")
    resp = make_error_response(err)
    assert resp["error"] is True
    assert resp["code"] == "PATH_NOT_FOUND"
    assert "/bad/path" in resp["message"]

    resp = make_success_response(data={"key": "value"})
    assert resp["error"] is False
    assert resp["data"]["key"] == "value"

    resp = make_success_response(data=None, degradation_level="bm25_only")
    assert resp["degradation_level"] == "bm25_only"
