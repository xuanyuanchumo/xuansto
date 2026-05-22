import json
import sys
import time
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from xuansto_mcp.tools.agent_status import (
    _AGENT_INSTANCES,
    _AgentInstance,
    _load_agent_instances,
    _persist_agent_instances,
    load_on_startup,
    register,
)
from mcp.server.fastmcp import FastMCP


@pytest.fixture
def tmp_work_dir(tmp_path):
    work_dir = tmp_path / ".xuansto"
    work_dir.mkdir()
    with patch("xuansto_mcp.tools.agent_status.WORK_DIR", work_dir):
        yield work_dir


@pytest.fixture
def clean_instances():
    _AGENT_INSTANCES.clear()
    yield
    _AGENT_INSTANCES.clear()


@pytest.fixture
def mcp_tool():
    test_mcp = FastMCP("test")
    register(test_mcp)
    return test_mcp._tool_manager._tools["agent_status"].fn


@pytest.mark.asyncio
async def test_create_persists_to_disk(tmp_work_dir, clean_instances, mcp_tool):
    result = await mcp_tool(
        action="create",
        agent_type="Backend Developer",
        capabilities=["python", "fastapi"],
    )
    data = result.get("data", result)
    agent_id = data["agent_id"]

    persist_file = tmp_work_dir / "agent_instances.json"
    assert persist_file.exists(), "持久化文件应在 create 后存在"

    raw = json.loads(persist_file.read_text(encoding="utf-8"))
    assert agent_id in raw
    assert raw[agent_id]["agent_type"] == "Backend Developer"
    assert raw[agent_id]["capabilities"] == ["python", "fastapi"]
    assert raw[agent_id]["status"] == "idle"
    assert raw[agent_id]["task"] == ""
    assert isinstance(raw[agent_id]["created_at"], float)
    assert raw[agent_id]["history"] == []


@pytest.mark.asyncio
async def test_destroy_removes_from_disk(tmp_work_dir, clean_instances, mcp_tool):
    create_result = await mcp_tool(
        action="create",
        agent_type="Frontend Developer",
        capabilities=["react"],
    )
    agent_id = create_result.get("data", create_result)["agent_id"]

    persist_file = tmp_work_dir / "agent_instances.json"
    assert persist_file.exists()
    raw_before = json.loads(persist_file.read_text(encoding="utf-8"))
    assert agent_id in raw_before

    await mcp_tool(action="destroy", agent_id=agent_id)

    raw_after = json.loads(persist_file.read_text(encoding="utf-8"))
    assert agent_id not in raw_after


@pytest.mark.asyncio
async def test_assign_persists_to_disk(tmp_work_dir, clean_instances, mcp_tool):
    create_result = await mcp_tool(
        action="create",
        agent_type="QA Engineer",
        capabilities=["testing"],
    )
    agent_id = create_result.get("data", create_result)["agent_id"]

    await mcp_tool(action="assign", agent_id=agent_id, task="Run integration tests")

    persist_file = tmp_work_dir / "agent_instances.json"
    raw = json.loads(persist_file.read_text(encoding="utf-8"))
    assert raw[agent_id]["status"] == "busy"
    assert raw[agent_id]["task"] == "Run integration tests"
    assert len(raw[agent_id]["history"]) == 1
    assert raw[agent_id]["history"][0]["action"] == "assign"


def test_load_on_startup_restores_agents(tmp_work_dir, clean_instances):
    persist_file = tmp_work_dir / "agent_instances.json"
    now = time.time()
    data = {
        "agent-abc12345": {
            "agent_id": "agent-abc12345",
            "agent_type": "Backend Developer",
            "capabilities": ["python", "sql"],
            "status": "busy",
            "task": "Build API",
            "created_at": now,
            "history": [
                {"action": "assign", "task": "Build API", "timestamp": now}
            ],
        },
        "agent-xyz99999": {
            "agent_id": "agent-xyz99999",
            "agent_type": "Frontend Developer",
            "capabilities": ["react", "typescript"],
            "status": "idle",
            "task": "",
            "created_at": now + 1,
            "history": [],
        },
    }
    persist_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    assert len(_AGENT_INSTANCES) == 0

    load_on_startup()

    assert len(_AGENT_INSTANCES) == 2
    assert "agent-abc12345" in _AGENT_INSTANCES
    assert "agent-xyz99999" in _AGENT_INSTANCES

    inst = _AGENT_INSTANCES["agent-abc12345"]
    assert isinstance(inst, _AgentInstance)
    assert inst.agent_type == "Backend Developer"
    assert inst.capabilities == ["python", "sql"]
    assert inst.status == "busy"
    assert inst.task == "Build API"
    assert inst.created_at == now
    assert len(inst.history) == 1
    assert inst.history[0]["action"] == "assign"

    inst2 = _AGENT_INSTANCES["agent-xyz99999"]
    assert inst2.status == "idle"
    assert inst2.capabilities == ["react", "typescript"]


def test_load_on_startup_missing_file_no_error(tmp_work_dir, clean_instances):
    persist_file = tmp_work_dir / "agent_instances.json"
    assert not persist_file.exists()

    load_on_startup()

    assert len(_AGENT_INSTANCES) == 0


def test_load_on_startup_corrupt_json_no_crash(tmp_work_dir, clean_instances):
    persist_file = tmp_work_dir / "agent_instances.json"
    persist_file.write_text("NOT VALID JSON {{{", encoding="utf-8")

    load_on_startup()

    assert len(_AGENT_INSTANCES) == 0


def test_persist_empty_instances(tmp_work_dir, clean_instances):
    _persist_agent_instances()

    persist_file = tmp_work_dir / "agent_instances.json"
    assert persist_file.exists()
    raw = json.loads(persist_file.read_text(encoding="utf-8"))
    assert raw == {}


@pytest.mark.asyncio
async def test_roundtrip_create_and_restore(tmp_work_dir, clean_instances, mcp_tool):
    create_result = await mcp_tool(
        action="create",
        agent_type="Security Auditor",
        capabilities=["penetration-testing", "code-review"],
    )
    agent_id = create_result.get("data", create_result)["agent_id"]

    await mcp_tool(action="assign", agent_id=agent_id, task="Audit auth module")

    original_inst = _AGENT_INSTANCES[agent_id]
    original_status = original_inst.status
    original_task = original_inst.task
    original_history_len = len(original_inst.history)

    _AGENT_INSTANCES.clear()
    assert len(_AGENT_INSTANCES) == 0

    load_on_startup()

    assert len(_AGENT_INSTANCES) == 1
    restored = _AGENT_INSTANCES[agent_id]
    assert restored.agent_type == "Security Auditor"
    assert restored.capabilities == ["penetration-testing", "code-review"]
    assert restored.status == original_status
    assert restored.task == original_task
    assert len(restored.history) == original_history_len
    assert restored.history[0]["action"] == "assign"
    assert restored.history[0]["task"] == "Audit auth module"
