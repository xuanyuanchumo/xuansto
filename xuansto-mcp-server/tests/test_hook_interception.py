import asyncio
import sys
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from xuansto_mcp.tools.hook_manage import (
    INLINE_HOOK_LOGIC,
    _HOOK_TOOL_MAP,
    execute_post_hooks,
    execute_pre_hooks,
    get_post_hooks,
    get_pre_hooks,
)
from xuansto_mcp.core.metrics import get_metrics_collector
from xuansto_mcp.core.errors import make_success_response


def test_hook_tool_map_entries():
    assert "code_simplify" in _HOOK_TOOL_MAP["security-block"]
    assert "security_scan" in _HOOK_TOOL_MAP["security-block"]
    assert "spec_drift_detect" in _HOOK_TOOL_MAP["security-block"]
    assert "workflow_dispatch" in _HOOK_TOOL_MAP["dangerous-cmd-confirm"]
    assert "code_simplify" in _HOOK_TOOL_MAP["auto-format"]
    assert "code_simplify" in _HOOK_TOOL_MAP["console-log-detect"]
    assert "quality_gate_check" in _HOOK_TOOL_MAP["type-check"]
    assert "workflow_dispatch" in _HOOK_TOOL_MAP["git-status-check"]
    assert "workflow_dispatch" in _HOOK_TOOL_MAP["decision-log-persist"]
    assert "session_manage" in _HOOK_TOOL_MAP["decision-log-persist"]


def test_get_pre_hooks():
    hooks = get_pre_hooks("code_simplify")
    assert "security-block" in hooks
    assert "auto-format" in hooks
    assert "console-log-detect" in hooks

    hooks = get_pre_hooks("workflow_dispatch")
    assert "dangerous-cmd-confirm" in hooks
    assert "git-status-check" in hooks
    assert "decision-log-persist" in hooks

    hooks = get_pre_hooks("skill_analyze")
    assert "platform-detect" in hooks


def test_get_post_hooks():
    hooks = get_post_hooks("workflow_dispatch")
    assert hooks == ["decision-log-persist"]

    hooks = get_post_hooks("session_manage")
    assert hooks == ["decision-log-persist"]

    hooks = get_post_hooks("code_simplify")
    assert hooks == []


def test_execute_pre_hooks_blocks_dangerous_command():
    kwargs = {
        "project_path": ".",
        "command": "rm -rf /",
    }
    results, errors = execute_pre_hooks("code_simplify", kwargs)
    assert len(results) > 0
    blocked = [r for r in results if r.get("status") == "block"]
    assert len(blocked) > 0
    assert blocked[0]["hook"] == "security-block"
    assert "危险命令" in blocked[0].get("message", "")


def test_execute_pre_hooks_blocks_sudo():
    kwargs = {
        "project_path": ".",
        "command": "sudo apt install foo",
    }
    results, errors = execute_pre_hooks("code_simplify", kwargs)
    assert len(results) > 0
    blocked = [r for r in results if r.get("status") == "block"]
    assert len(blocked) > 0
    assert blocked[0]["hook"] == "security-block"


def test_execute_pre_hooks_passes_safe_command():
    kwargs = {
        "project_path": ".",
        "command": "ls -la",
    }
    results, errors = execute_pre_hooks("code_simplify", kwargs)
    blocked = [r for r in results if r.get("status") == "block"]
    assert len(blocked) == 0


def test_execute_pre_hooks_passes_no_command():
    kwargs = {
        "project_path": ".",
    }
    results, errors = execute_pre_hooks("code_simplify", kwargs)
    blocked = [r for r in results if r.get("status") == "block"]
    assert len(blocked) == 0


def test_execute_pre_hooks_no_hooks_for_unknown_tool():
    kwargs = {
        "project_path": ".",
        "command": "rm -rf /",
    }
    results, errors = execute_pre_hooks("nonexistent_tool_xyz", kwargs)
    assert results == []
    assert errors == []


def test_execute_post_hooks_called():
    with tempfile.TemporaryDirectory() as tmpdir:
        kwargs = {"project_path": tmpdir}
        result_data = {"error": False, "data": {"status": "ok"}}
        errors = execute_post_hooks("workflow_dispatch", kwargs, result_data)
        decisions_dir = Path(tmpdir) / ".xuansto" / "decisions"
        assert decisions_dir.exists()


def test_execute_post_hooks_no_hook_for_tool():
    kwargs = {"project_path": "."}
    result_data = {"error": False, "data": {"status": "ok"}}
    errors = execute_post_hooks("code_simplify", kwargs, result_data)
    assert errors == []


def test_with_hook_interception_blocks():
    from xuansto_mcp.server import _with_hook_interception
    from xuansto_mcp.core.hook_engine import get_hook_engine
    from xuansto_mcp.tools.hook_manage import execute_pre_hooks as hook_manage_pre

    engine = get_hook_engine()
    if not engine._pre_hooks.get("code_simplify") and not engine._global_pre_hooks:
        engine.register_hook("pre", hook_manage_pre)

    async def fake_tool(**kwargs):
        return make_success_response({"status": "ok"})

    wrapped = _with_hook_interception("code_simplify", fake_tool)
    result = asyncio.run(wrapped(project_path=".", command="rm -rf /"))
    assert result["action"] == "blocked"
    assert result["hook"] == "security-block"
    assert result["tool"] == "code_simplify"


def test_with_hook_interception_passes():
    from xuansto_mcp.server import _with_hook_interception

    async def fake_tool(**kwargs):
        return make_success_response({"status": "ok"})

    wrapped = _with_hook_interception("code_simplify", fake_tool)
    result = asyncio.run(wrapped(project_path=".", command="ls -la"))
    assert result["data"]["status"] == "ok"


def test_with_hook_interception_records_metrics_on_block():
    from xuansto_mcp.server import _with_hook_interception
    from xuansto_mcp.core.hook_engine import get_hook_engine

    mc = get_metrics_collector()
    with mc._lock:
        mc._tool_metrics.pop("__test_hook_block__", None)

    async def fake_tool(**kwargs):
        return make_success_response({"status": "ok"})

    wrapped = _with_hook_interception("__test_hook_block__", fake_tool)

    async def mock_pre(tool_name, kwargs):
        return ([{"status": "block", "hook": "security-block", "message": "blocked"}], [])

    engine = get_hook_engine()
    with patch.object(engine, "execute_pre_hooks", side_effect=mock_pre):
        result = asyncio.run(wrapped(project_path="."))
        assert result["action"] == "blocked"

    with mc._lock:
        metrics = mc._tool_metrics.get("__test_hook_block__")
    assert metrics is not None
    assert metrics["call_count"] == 1
    assert metrics["failure_count"] == 1
    assert len(metrics["latency_samples"]) == 1


def test_with_hook_interception_records_metrics_on_success():
    from xuansto_mcp.server import _with_hook_interception
    from xuansto_mcp.core.hook_engine import get_hook_engine

    mc = get_metrics_collector()
    with mc._lock:
        mc._tool_metrics.pop("__test_hook_success__", None)

    async def fake_tool(**kwargs):
        return make_success_response({"status": "ok"})

    wrapped = _with_hook_interception("__test_hook_success__", fake_tool)

    engine = get_hook_engine()
    with patch.object(engine, "execute_pre_hooks", return_value=([], [])):
        with patch.object(engine, "execute_post_hooks", return_value=[]):
            result = asyncio.run(wrapped(project_path="."))
            assert result["data"]["status"] == "ok"

    with mc._lock:
        metrics = mc._tool_metrics.get("__test_hook_success__")
    assert metrics is not None
    assert metrics["call_count"] == 1
    assert metrics["failure_count"] == 0
    assert len(metrics["latency_samples"]) == 1


def test_with_hook_interception_records_metrics_on_exception():
    from xuansto_mcp.server import _with_hook_interception
    from xuansto_mcp.core.hook_engine import get_hook_engine

    mc = get_metrics_collector()
    with mc._lock:
        mc._tool_metrics.pop("__test_hook_exc__", None)

    async def fake_tool(**kwargs):
        raise RuntimeError("test error")

    wrapped = _with_hook_interception("__test_hook_exc__", fake_tool)

    engine = get_hook_engine()
    with patch.object(engine, "execute_pre_hooks", return_value=([], [])):
        try:
            asyncio.run(wrapped(project_path="."))
        except RuntimeError:
            pass

    with mc._lock:
        metrics = mc._tool_metrics.get("__test_hook_exc__")
    assert metrics is not None
    assert metrics["call_count"] == 1
    assert metrics["failure_count"] == 1


def test_with_hook_interception_post_hooks_called():
    from xuansto_mcp.server import _with_hook_interception
    from xuansto_mcp.core.hook_engine import get_hook_engine

    async def fake_tool(**kwargs):
        return make_success_response({"status": "ok"})

    wrapped = _with_hook_interception("workflow_dispatch", fake_tool)

    engine = get_hook_engine()
    with patch.object(engine, "execute_pre_hooks", return_value=([], [])) as mock_pre:
        with patch.object(engine, "execute_post_hooks", return_value=[]) as mock_post:
            result = asyncio.run(wrapped(project_path="."))
            assert result["data"]["status"] == "ok"
            mock_pre.assert_called_once()
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert call_args[0][0] == "workflow_dispatch"
