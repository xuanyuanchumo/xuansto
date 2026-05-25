from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def test_server_starts():
    from mcp.server.fastmcp import FastMCP

    server = FastMCP(
        "xuansto-mcp-server-test",
        instructions="Xuansto Skill MCP服务器 v8.0.0",
    )
    assert server is not None
    assert server.name == "xuansto-mcp-server-test"


def test_tool_count():
    from xuansto_mcp.server import _REGISTERED_TOOL_NAMES

    assert len(_REGISTERED_TOOL_NAMES) == 20


def test_resource_count():
    from xuansto_mcp.server import _REGISTERED_RESOURCE_NAMES

    assert len(_REGISTERED_RESOURCE_NAMES) >= 8


@pytest.mark.asyncio
async def test_skill_analyze_tool(fresh_mcp, mock_config_paths, tmp_path):
    from xuansto_mcp.tools import skill_analyze

    test_skill_root = mock_config_paths["skill_root"]
    (test_skill_root / "scripts").mkdir(parents=True, exist_ok=True)
    (test_skill_root / "agents").mkdir(parents=True, exist_ok=True)

    with patch("xuansto_mcp.tools.skill_analyze.SCRIPTS_DIR", test_skill_root / "scripts"), \
         patch("xuansto_mcp.tools.skill_analyze.REFERENCES_DIR", test_skill_root / "references"):
        skill_analyze.register(fresh_mcp)

    tools = fresh_mcp._tool_manager._tools
    assert "skill_analyze" in tools

    tool_fn = tools["skill_analyze"].fn
    result = await tool_fn(skill_path=str(test_skill_root))
    assert isinstance(result, dict)
    assert result.get("error") is False


@pytest.mark.asyncio
async def test_knowledge_search_retrieve(fresh_mcp, mock_config_paths, tmp_path):
    from xuansto_mcp.tools import knowledge_search

    knowledge_dir = mock_config_paths["data_dir"] / "knowledge"
    index_dir = knowledge_dir / "index"
    index_dir.mkdir(parents=True, exist_ok=True)

    with patch("xuansto_mcp.tools.knowledge_search.KNOWLEDGE_DB_PATH", index_dir / "knowledge.db"), \
         patch("xuansto_mcp.tools.knowledge_search.KNOWLEDGE_CHROMA_PATH", index_dir / "chroma_db"), \
         patch("xuansto_mcp.tools.knowledge_search.KNOWLEDGE_GENERAL_DIR", knowledge_dir / "general"), \
         patch("xuansto_mcp.tools.knowledge_search.KNOWLEDGE_WORKSPACE_DIR", knowledge_dir / "workspace"), \
         patch("xuansto_mcp.tools.knowledge_search.KNOWLEDGE_EXPERIENCE_DIR", knowledge_dir / "experience"), \
         patch("xuansto_mcp.tools.knowledge_search.REFERENCES_DIR", mock_config_paths["references_dir"]), \
         patch("xuansto_mcp.core.config.KNOWLEDGE_DIR", knowledge_dir):
        knowledge_search.register(fresh_mcp)

    tools = fresh_mcp._tool_manager._tools
    assert "knowledge_search" in tools

    tool_fn = tools["knowledge_search"].fn
    result = await tool_fn(action="retrieve", query="test query")
    assert isinstance(result, dict)
    assert result.get("error") is False


@pytest.mark.asyncio
async def test_knowledge_search_rejects_inject(fresh_mcp, mock_config_paths, tmp_path):
    from xuansto_mcp.tools import knowledge_search

    knowledge_dir = mock_config_paths["data_dir"] / "knowledge"
    index_dir = knowledge_dir / "index"
    index_dir.mkdir(parents=True, exist_ok=True)

    with patch("xuansto_mcp.tools.knowledge_search.KNOWLEDGE_DB_PATH", index_dir / "knowledge.db"), \
         patch("xuansto_mcp.tools.knowledge_search.KNOWLEDGE_CHROMA_PATH", index_dir / "chroma_db"), \
         patch("xuansto_mcp.tools.knowledge_search.KNOWLEDGE_GENERAL_DIR", knowledge_dir / "general"), \
         patch("xuansto_mcp.tools.knowledge_search.KNOWLEDGE_WORKSPACE_DIR", knowledge_dir / "workspace"), \
         patch("xuansto_mcp.tools.knowledge_search.KNOWLEDGE_EXPERIENCE_DIR", knowledge_dir / "experience"), \
         patch("xuansto_mcp.tools.knowledge_search.REFERENCES_DIR", mock_config_paths["references_dir"]), \
         patch("xuansto_mcp.core.config.KNOWLEDGE_DIR", knowledge_dir):
        knowledge_search.register(fresh_mcp)

    tools = fresh_mcp._tool_manager._tools
    tool_fn = tools["knowledge_search"].fn
    result = await tool_fn(action="inject", query="test")
    assert isinstance(result, dict)
    assert result.get("error") is True


@pytest.mark.asyncio
async def test_server_health_capabilities(fresh_mcp, mock_config_paths, tmp_path):
    from xuansto_mcp.tools import server_health

    with patch("xuansto_mcp.tools.server_health.DATA_DIR", mock_config_paths["data_dir"]), \
         patch("xuansto_mcp.tools.server_health.SKILL_ROOT", mock_config_paths["skill_root"]), \
         patch("xuansto_mcp.tools.server_health.WORK_DIR", tmp_path / ".xuansto"), \
         patch("xuansto_mcp.tools.server_health.KNOWLEDGE_CHROMA_PATH", tmp_path / "chroma_db"), \
         patch("xuansto_mcp.tools.server_health.AGENTS_DIR", mock_config_paths["agents_dir"]), \
         patch("xuansto_mcp.tools.server_health.REFERENCES_DIR", mock_config_paths["references_dir"]), \
         patch("xuansto_mcp.tools.server_health.COMMANDS_DIR", mock_config_paths["commands_dir"]):
        server_health.register(fresh_mcp)

    tools = fresh_mcp._tool_manager._tools
    assert "server_health" in tools

    tool_fn = tools["server_health"].fn
    result = await tool_fn(action="capabilities")
    assert isinstance(result, dict)
    assert result.get("error") is False
    assert "tools" in result.get("data", {})


@pytest.mark.asyncio
async def test_server_health_negotiate_version(fresh_mcp, mock_config_paths, tmp_path):
    from xuansto_mcp.tools import server_health

    with patch("xuansto_mcp.tools.server_health.DATA_DIR", mock_config_paths["data_dir"]), \
         patch("xuansto_mcp.tools.server_health.SKILL_ROOT", mock_config_paths["skill_root"]), \
         patch("xuansto_mcp.tools.server_health.WORK_DIR", tmp_path / ".xuansto"), \
         patch("xuansto_mcp.tools.server_health.KNOWLEDGE_CHROMA_PATH", tmp_path / "chroma_db"), \
         patch("xuansto_mcp.tools.server_health.AGENTS_DIR", mock_config_paths["agents_dir"]), \
         patch("xuansto_mcp.tools.server_health.REFERENCES_DIR", mock_config_paths["references_dir"]), \
         patch("xuansto_mcp.tools.server_health.COMMANDS_DIR", mock_config_paths["commands_dir"]):
        server_health.register(fresh_mcp)

    tools = fresh_mcp._tool_manager._tools
    tool_fn = tools["server_health"].fn
    result = await tool_fn(action="negotiate_version", client_version="3.0.0")
    assert isinstance(result, dict)
    assert result.get("error") is False
    data = result.get("data", {})
    assert data.get("compatible") is True


@pytest.mark.asyncio
async def test_agent_status_list(fresh_mcp, mock_config_paths, tmp_path):
    from xuansto_mcp.tools import agent_status

    with patch("xuansto_mcp.tools.agent_status.AGENTS_DIR", mock_config_paths["agents_dir"]), \
         patch("xuansto_mcp.tools.agent_status.REFERENCES_DIR", mock_config_paths["references_dir"]), \
         patch("xuansto_mcp.tools.agent_status.DATA_DIR", mock_config_paths["data_dir"]):
        agent_status.register(fresh_mcp)

    tools = fresh_mcp._tool_manager._tools
    assert "agent_status" in tools

    tool_fn = tools["agent_status"].fn
    result = await tool_fn(action="list")
    assert isinstance(result, dict)
    assert result.get("error") is False


@pytest.mark.asyncio
async def test_agent_manage_create(fresh_mcp, mock_config_paths, tmp_path):
    from xuansto_mcp.tools import agent_manage

    work_dir = tmp_path / ".xuansto"
    work_dir.mkdir(parents=True, exist_ok=True)

    with patch("xuansto_mcp.tools.agent_manage.WORK_DIR", work_dir):
        agent_manage.register(fresh_mcp)

    tools = fresh_mcp._tool_manager._tools
    assert "agent_manage" in tools

    tool_fn = tools["agent_manage"].fn
    result = await tool_fn(action="create", agent_type="developer", capabilities=["code_review"])
    assert isinstance(result, dict)
    assert result.get("error") is False
    data = result.get("data", {})
    assert data.get("agent_type") == "developer"
    assert "agent_id" in data


@pytest.mark.asyncio
async def test_metrics_report_query(fresh_mcp, mock_config_paths, tmp_path):
    from xuansto_mcp.tools import metrics_report

    work_dir = tmp_path / ".xuansto"
    work_dir.mkdir(parents=True, exist_ok=True)

    with patch("xuansto_mcp.tools.metrics_report.WORK_DIR", work_dir):
        metrics_report.register(fresh_mcp)

    tools = fresh_mcp._tool_manager._tools
    assert "metrics_report" in tools

    tool_fn = tools["metrics_report"].fn
    result = await tool_fn(action="query")
    assert isinstance(result, dict)
    assert result.get("error") is False


@pytest.mark.asyncio
async def test_config_manage_validate(fresh_mcp, mock_config_paths, tmp_path):
    from xuansto_mcp.tools import config_manage

    with patch("xuansto_mcp.tools.config_manage.SKILL_ROOT", mock_config_paths["skill_root"]), \
         patch("xuansto_mcp.tools.config_manage.WORK_DIR", tmp_path / ".xuansto"):
        config_manage.register(fresh_mcp)

    tools = fresh_mcp._tool_manager._tools
    assert "config_manage" in tools

    tool_fn = tools["config_manage"].fn
    result = await tool_fn(action="validate")
    assert isinstance(result, dict)
    assert result.get("error") is False
