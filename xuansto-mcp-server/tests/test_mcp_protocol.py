import sys
import json
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters


SERVER_PARAMS = StdioServerParameters(
    command=sys.executable,
    args=["-m", "xuansto_mcp.server"],
    env=None,
)


async def _run_with_session(test_fn):
    async with stdio_client(SERVER_PARAMS) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            await test_fn(session)


@pytest.mark.asyncio
async def test_list_tools_returns_13_tools():
    async def check(session):
        tools_result = await session.list_tools()
        tool_names = [t.name for t in tools_result.tools]
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
        assert len(tool_names) == len(expected_tools), (
            f"Expected {len(expected_tools)} tools, got {len(tool_names)}: {tool_names}"
        )

    await _run_with_session(check)


@pytest.mark.asyncio
async def test_call_server_health():
    async def check(session):
        result = await session.call_tool("server_health", {})
        assert not result.isError
        text = result.content[0].text if result.content else ""
        data = json.loads(text)
        inner = data.get("data", data)
        assert "version" in inner
        assert "status" in inner

    await _run_with_session(check)


@pytest.mark.asyncio
async def test_workflow_lifecycle():
    async def check(session):
        start_result = await session.call_tool("workflow_dispatch", {
            "action": "start",
            "workflow": "sdd-tdd-fast",
        })
        assert not start_result.isError

        status_result = await session.call_tool("workflow_dispatch", {
            "action": "status",
        })
        assert not status_result.isError

        phase_result = await session.call_tool("workflow_dispatch", {
            "action": "phase",
            "phase_action": "current",
        })
        assert not phase_result.isError

    await _run_with_session(check)


@pytest.mark.asyncio
async def test_knowledge_search_retrieve():
    async def check(session):
        result = await session.call_tool("knowledge_search", {
            "query": "test query",
            "action": "retrieve",
        })
        assert not result.isError

    await _run_with_session(check)


@pytest.mark.asyncio
async def test_list_resources():
    async def check(session):
        resources_result = await session.list_resources()
        resource_uris = [str(r.uri) for r in resources_result.resources]
        expected_static = [
            "xuansto://config/skill",
            "xuansto://references/quality-gates",
            "xuansto://references/agent-registry",
            "xuansto://references/workflow-phases",
            "xuansto://sessions/latest",
        ]
        for uri in expected_static:
            assert uri in resource_uris, f"Missing resource: {uri}"

        templates_result = await session.list_resource_templates()
        template_uris = [str(t.uriTemplate) for t in templates_result.resourceTemplates]
        assert "xuansto://templates/{name}" in template_uris, (
            f"Missing resource template, got: {template_uris}"
        )

    await _run_with_session(check)
