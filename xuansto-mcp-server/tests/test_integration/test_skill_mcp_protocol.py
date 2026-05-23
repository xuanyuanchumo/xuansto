import pytest
from unittest.mock import patch, MagicMock
from mcp.server.fastmcp import FastMCP
from xuansto_mcp.core.errors import make_success_response, make_error_response


@pytest.fixture
def mcp_server():
    return FastMCP("test-server")


@pytest.mark.asyncio
async def test_skill_analyze_tool_call_response_format(mcp_server, tmp_path):
    from xuansto_mcp.tools.skill_analyze import register
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["skill_analyze"].fn
    result = await tool_fn(skill_path=str(tmp_path))
    assert isinstance(result, dict)
    assert "error" in result
    assert result["error"] is False
    assert "data" in result
    assert "api_version" in result


@pytest.mark.asyncio
async def test_knowledge_search_tool_call_response_format(mcp_server):
    from xuansto_mcp.tools.knowledge_search import register
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["knowledge_search"].fn
    with patch("xuansto_mcp.tools.knowledge_search._ensure_knowledge_index"), \
         patch("xuansto_mcp.tools.knowledge_search.get_search_engine") as mock_engine:
        mock_se = MagicMock()
        mock_se.search.return_value = []
        mock_engine.return_value = mock_se
        result = await tool_fn(action="retrieve", query="test")
        assert isinstance(result, dict)
        assert "error" in result
        assert "api_version" in result


@pytest.mark.asyncio
async def test_quality_gate_check_tool_call_response_format(mcp_server, tmp_path):
    from xuansto_mcp.tools.quality_gate_check import register
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["quality_gate_check"].fn
    with patch("xuansto_mcp.tools.quality_gate_check._compute_file_hashes", return_value={}):
        result = await tool_fn(gate_ids=["TEST-PASS"], project_path=str(tmp_path))
        assert isinstance(result, dict)
        assert result["error"] is False
        assert "data" in result
        data = result["data"]
        assert "checks" in data
        assert "summary" in data
        assert "cache_info" in data


@pytest.mark.asyncio
async def test_workflow_dispatch_tool_call_response_format(mcp_server):
    from xuansto_mcp.tools.workflow_dispatch import register
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["workflow_dispatch"].fn
    with patch("xuansto_mcp.tools.workflow_dispatch._load_all_workflows", return_value={}):
        result = await tool_fn(action="status")
        assert isinstance(result, dict)
        assert "error" in result


@pytest.mark.asyncio
async def test_session_manage_tool_call_response_format(mcp_server, tmp_path):
    from xuansto_mcp.tools.session_manage import register
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["session_manage"].fn
    with patch("xuansto_mcp.tools.session_manage.SESSION_DIR", tmp_path):
        result = await tool_fn(action="save", completed_tasks=["t1"])
        assert isinstance(result, dict)
        assert result["error"] is False
        assert "data" in result


@pytest.mark.asyncio
async def test_hook_manage_tool_call_response_format(mcp_server):
    from xuansto_mcp.tools.hook_manage import register
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["hook_manage"].fn
    result = await tool_fn(action="list", profile="minimal")
    assert isinstance(result, dict)
    assert result["error"] is False
    assert "data" in result
    assert "profile" in result["data"]
    assert "hooks" in result["data"]


@pytest.mark.asyncio
async def test_agent_status_tool_call_response_format(mcp_server):
    from xuansto_mcp.tools.agent_status import register
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["agent_status"].fn
    with patch("xuansto_mcp.tools.agent_status.REFERENCES_DIR") as mock_ref:
        mock_ref.__truediv__ = MagicMock(return_value=MagicMock(exists=MagicMock(return_value=False)))
        result = await tool_fn(action="list")
        assert isinstance(result, dict)
        assert result["error"] is False


@pytest.mark.asyncio
async def test_server_health_tool_call_response_format(mcp_server):
    from xuansto_mcp.tools.server_health import register
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["server_health"].fn
    with patch("xuansto_mcp.tools.server_health._check_chromadb_health", return_value={"available": False, "latency_ms": 0}), \
         patch("xuansto_mcp.tools.workflow_dispatch._load_all_workflows", return_value={}), \
         patch("xuansto_mcp.tools.workflow_dispatch._cleanup_all_snapshots", return_value={}):
        result = await tool_fn(action="check")
        assert isinstance(result, dict)
        assert result["data"]["status"] == "healthy"
        assert "version" in result["data"]
        assert "uptime_seconds" in result["data"]


@pytest.mark.asyncio
async def test_context_compress_tool_call_response_format(mcp_server):
    from xuansto_mcp.tools.context_compress import register
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["context_compress"].fn
    result = await tool_fn(content="test content", strategy="semantic")
    assert isinstance(result, dict)
    assert result["error"] is False
    assert "compressed" in result["data"]
    assert "compression_ratio" in result["data"]


@pytest.mark.asyncio
async def test_decision_log_tool_call_response_format(mcp_server, tmp_path):
    from xuansto_mcp.tools.decision_log import register
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["decision_log"].fn
    budget_file = tmp_path / "decisions.json"
    budget_db = tmp_path / "decisions.db"
    import sqlite3
    from xuansto_mcp.tools.decision_log import _CREATE_TABLE_SQL, _CREATE_INDEX_SQL, _CREATE_FTS_SQL, _CREATE_FTS_TRIGGERS_SQL
    conn = sqlite3.connect(str(budget_db))
    conn.executescript(_CREATE_TABLE_SQL)
    try:
        conn.executescript(_CREATE_FTS_SQL)
        conn.executescript(_CREATE_FTS_TRIGGERS_SQL)
    except sqlite3.OperationalError:
        pass
    conn.executescript(_CREATE_INDEX_SQL)
    conn.commit()
    conn.close()
    with patch("xuansto_mcp.tools.decision_log.DECISIONS_FILE", budget_file), \
         patch("xuansto_mcp.tools.decision_log.DECISIONS_DB", budget_db), \
         patch("xuansto_mcp.tools.decision_log.notify"):
        result = await tool_fn(action="log", title="Test")
        assert isinstance(result, dict)
        assert result["error"] is False
        assert "id" in result["data"]


@pytest.mark.asyncio
async def test_token_budget_tool_call_response_format(mcp_server, tmp_path):
    from xuansto_mcp.tools.token_budget import register
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["token_budget"].fn
    budget_file = tmp_path / "token_budget.json"
    with patch("xuansto_mcp.tools.token_budget.BUDGET_FILE", budget_file):
        result = await tool_fn(action="status")
        assert isinstance(result, dict)
        assert result["error"] is False


@pytest.mark.asyncio
async def test_project_init_tool_call_response_format(mcp_server, tmp_path):
    from xuansto_mcp.tools.project_init import register
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["project_init"].fn
    with patch("xuansto_mcp.tools.project_init.notify"):
        result = await tool_fn(action="create", name="test-proj", directory=str(tmp_path / "new-proj"))
        assert isinstance(result, dict)
        assert result["error"] is False


@pytest.mark.asyncio
async def test_error_response_format_consistency(mcp_server):
    from xuansto_mcp.tools.session_manage import register
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["session_manage"].fn
    result = await tool_fn(action="invalid_action")
    assert isinstance(result, dict)
    assert result["error"] is True
    assert "code" in result
    assert "message" in result


@pytest.mark.asyncio
async def test_success_response_has_api_version(mcp_server, tmp_path):
    from xuansto_mcp.tools.context_compress import register
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["context_compress"].fn
    result = await tool_fn(content="test")
    assert "api_version" in result
