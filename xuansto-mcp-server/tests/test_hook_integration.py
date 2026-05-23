from __future__ import annotations

import asyncio
import json
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

from xuansto_mcp.core.hook_engine import (
    HookEngine,
    HookType,
    _hook_failure_counts,
    _HOOK_FAILURE_THRESHOLD,
    _record_hook_failure,
    _reset_hook_failure_count,
    _resolve_hook_type,
)


@pytest.fixture
def fresh_engine():
    import xuansto_mcp.core.hook_engine as mod
    mod._hook_failure_counts.clear()
    return HookEngine()


@pytest.fixture(autouse=True)
def clear_failure_counts():
    import xuansto_mcp.core.hook_engine as mod
    mod._hook_failure_counts.clear()
    yield
    mod._hook_failure_counts.clear()


class TestHookTypeEnum:
    def test_all_hook_types(self):
        assert HookType.PRE.value == "pre"
        assert HookType.POST.value == "post"
        assert HookType.PHASE_ENTER.value == "phase_enter"
        assert HookType.PHASE_EXIT.value == "phase_exit"
        assert HookType.GATE_PASS.value == "gate_pass"
        assert HookType.GATE_FAIL.value == "gate_fail"
        assert HookType.SESSION_START.value == "session_start"
        assert HookType.SESSION_STOP.value == "session_stop"

    def test_resolve_hook_type_from_string(self):
        assert _resolve_hook_type("pre") == HookType.PRE
        assert _resolve_hook_type("post") == HookType.POST
        assert _resolve_hook_type("phase_enter") == HookType.PHASE_ENTER

    def test_resolve_hook_type_from_enum(self):
        assert _resolve_hook_type(HookType.PRE) == HookType.PRE

    def test_resolve_hook_type_unknown_falls_back(self):
        assert _resolve_hook_type("unknown_type") == HookType.PRE


class TestRegisterHook:
    def test_register_pre_hook(self, fresh_engine):
        handler = lambda tool, kwargs: ([], [])
        fresh_engine.register_hook(HookType.PRE, handler, tool_name="test_tool")
        assert handler in fresh_engine._pre_hooks.get("test_tool", [])

    def test_register_global_pre_hook(self, fresh_engine):
        handler = lambda tool, kwargs: ([], [])
        fresh_engine.register_hook(HookType.PRE, handler)
        assert handler in fresh_engine._global_pre_hooks

    def test_register_post_hook(self, fresh_engine):
        handler = lambda tool, kwargs, result: []
        fresh_engine.register_hook(HookType.POST, handler, tool_name="test_tool")
        assert handler in fresh_engine._post_hooks.get("test_tool", [])

    def test_register_phase_enter_hook(self, fresh_engine):
        handler = lambda *a, **kw: None
        fresh_engine.register_hook(HookType.PHASE_ENTER, handler, tool_name="test_tool")
        assert handler in fresh_engine._phase_enter_hooks.get("test_tool", [])

    def test_register_session_hooks(self, fresh_engine):
        handler = lambda *a, **kw: None
        fresh_engine.register_hook(HookType.SESSION_START, handler)
        assert handler in fresh_engine._session_start_hooks
        fresh_engine.register_hook(HookType.SESSION_STOP, handler)
        assert handler in fresh_engine._session_stop_hooks

    def test_register_hook_with_string_type(self, fresh_engine):
        handler = lambda tool, kwargs: ([], [])
        fresh_engine.register_hook("pre", handler, tool_name="test_tool")
        assert handler in fresh_engine._pre_hooks.get("test_tool", [])


class TestUnregisterHook:
    def test_unregister_pre_hook(self, fresh_engine):
        handler = lambda tool, kwargs: ([], [])
        fresh_engine.register_hook(HookType.PRE, handler, tool_name="test_tool")
        result = fresh_engine.unregister_hook(HookType.PRE, handler, tool_name="test_tool")
        assert result is True
        assert handler not in fresh_engine._pre_hooks.get("test_tool", [])

    def test_unregister_nonexistent_returns_false(self, fresh_engine):
        handler = lambda tool, kwargs: ([], [])
        result = fresh_engine.unregister_hook(HookType.PRE, handler, tool_name="test_tool")
        assert result is False


class TestExecutePreHooks:
    @pytest.mark.asyncio
    async def test_pre_hooks_executed(self, fresh_engine):
        results_log = []

        def handler(tool_name, kwargs):
            results_log.append(tool_name)
            return ([{"hook": "test", "status": "ok"}], [])

        fresh_engine.register_hook(HookType.PRE, handler, tool_name="my_tool")
        results, errors = await fresh_engine.execute_pre_hooks("my_tool", {"key": "val"})
        assert "my_tool" in results_log
        assert len(results) == 1
        assert results[0]["status"] == "ok"

    @pytest.mark.asyncio
    async def test_pre_hook_block_stops_execution(self, fresh_engine):
        def blocking_handler(tool_name, kwargs):
            return ([{"status": "block", "reason": "forbidden", "hook": "security_check"}], [])

        fresh_engine.register_hook(HookType.PRE, blocking_handler, tool_name="my_tool")
        results, errors = await fresh_engine.execute_pre_hooks("my_tool", {})
        assert any(r.get("status") == "block" for r in results)

    @pytest.mark.asyncio
    async def test_pre_hook_failure_recorded(self, fresh_engine):
        def failing_handler(tool_name, kwargs):
            raise RuntimeError("hook failed")

        failing_handler.__name__ = "failing_handler"
        fresh_engine.register_hook(HookType.PRE, failing_handler, tool_name="my_tool")
        results, errors = await fresh_engine.execute_pre_hooks("my_tool", {})
        assert len(errors) == 1
        assert errors[0]["hook"] == "failing_handler"

    @pytest.mark.asyncio
    async def test_global_pre_hooks_execute(self, fresh_engine):
        call_log = []

        def global_handler(tool_name, kwargs):
            call_log.append(("global", tool_name))
            return ([], [])

        fresh_engine.register_hook(HookType.PRE, global_handler)
        await fresh_engine.execute_pre_hooks("any_tool", {})
        assert ("global", "any_tool") in call_log


class TestExecutePostHooks:
    @pytest.mark.asyncio
    async def test_post_hooks_executed(self, fresh_engine):
        errors_log = []

        def post_handler(tool_name, kwargs, result):
            errors_log.append(tool_name)
            return []

        fresh_engine.register_hook(HookType.POST, post_handler, tool_name="my_tool")
        errors = await fresh_engine.execute_post_hooks("my_tool", {}, {"data": "ok"})
        assert "my_tool" in errors_log

    @pytest.mark.asyncio
    async def test_post_hook_failure_recorded(self, fresh_engine):
        def failing_post(tool_name, kwargs, result):
            raise RuntimeError("post hook error")

        failing_post.__name__ = "failing_post"
        fresh_engine.register_hook(HookType.POST, failing_post, tool_name="my_tool")
        errors = await fresh_engine.execute_post_hooks("my_tool", {}, {})
        assert len(errors) == 1
        assert errors[0]["hook"] == "failing_post"


class TestHookFailureCounting:
    def test_failure_count_increments(self):
        _record_hook_failure("test_handler")
        _record_hook_failure("test_handler")
        counts = _hook_failure_counts
        assert counts.get("test_handler") == 2

    def test_failure_reset(self):
        _record_hook_failure("test_handler")
        _reset_hook_failure_count("test_handler")
        assert "test_handler" not in _hook_failure_counts

    def test_failure_threshold_alert(self, caplog):
        for _ in range(_HOOK_FAILURE_THRESHOLD):
            _record_hook_failure("alert_handler")
        counts = _hook_failure_counts
        assert counts.get("alert_handler") == _HOOK_FAILURE_THRESHOLD

    def test_get_failure_counts(self, fresh_engine):
        _record_hook_failure("handler_a")
        _record_hook_failure("handler_b")
        _record_hook_failure("handler_a")
        counts = fresh_engine.get_failure_counts()
        assert counts["handler_a"] == 2
        assert counts["handler_b"] == 1


class TestWithHookInterception:
    @pytest.mark.asyncio
    async def test_blocked_by_pre_hook(self):
        from xuansto_mcp.core.hook_engine import HookEngine

        engine = HookEngine()

        def security_block(tool_name, kwargs):
            return ([{"status": "block", "reason": "dangerous", "hook": "security_check"}], [])

        engine.register_hook(HookType.PRE, security_block, tool_name="test_tool")

        with patch("xuansto_mcp.server.get_hook_engine", return_value=engine):
            with patch("xuansto_mcp.tools.server_health.record_tool_call"):
                with patch("xuansto_mcp.core.notifications.notify"):
                    from xuansto_mcp.server import _with_hook_interception

                    async def dummy_tool(**kwargs):
                        return {"error": False, "data": "should not reach"}

                    wrapped = _with_hook_interception("test_tool", dummy_tool)
                    result = await wrapped(param="test")
                    assert result["data"]["action"] == "blocked"
                    assert "dangerous" in result["data"]["block_reason"].lower() or result["data"]["block_reason"] != ""

    @pytest.mark.asyncio
    async def test_security_hook_failure_blocks(self):
        from xuansto_mcp.core.hook_engine import HookEngine

        engine = HookEngine()

        def failing_security(tool_name, kwargs):
            raise RuntimeError("security check crashed")

        failing_security.__name__ = "security_check"
        engine.register_hook(HookType.PRE, failing_security, tool_name="test_tool")

        with patch("xuansto_mcp.server.get_hook_engine", return_value=engine):
            with patch("xuansto_mcp.tools.server_health.record_tool_call"):
                with patch("xuansto_mcp.core.notifications.notify"):
                    from xuansto_mcp.server import _with_hook_interception

                    async def dummy_tool(**kwargs):
                        return {"error": False, "data": "should not reach"}

                    wrapped = _with_hook_interception("test_tool", dummy_tool)
                    result = await wrapped(param="test")
                    assert result["data"]["action"] == "blocked"
                    assert "security" in result["data"]["block_reason"].lower()

    @pytest.mark.asyncio
    async def test_normal_execution_passes_through(self):
        from xuansto_mcp.core.hook_engine import HookEngine

        engine = HookEngine()

        with patch("xuansto_mcp.server.get_hook_engine", return_value=engine):
            with patch("xuansto_mcp.tools.server_health.record_tool_call"):
                with patch("xuansto_mcp.tools.resource_load_status.record_token_usage"):
                    with patch("xuansto_mcp.core.rate_limiter.check_rate_limit", return_value=(True, {})):
                        from xuansto_mcp.server import _with_hook_interception

                        async def dummy_tool(**kwargs):
                            return {"error": False, "data": {"result": "ok"}}

                        wrapped = _with_hook_interception("test_tool", dummy_tool)
                        result = await wrapped(param="test")
                        assert result["data"]["result"] == "ok"


class TestLoadHooksFromConfig:
    def test_load_from_nonexistent_file(self, fresh_engine, tmp_path):
        fresh_engine.load_hooks_from_config(tmp_path / "nonexistent.json")
        assert len(fresh_engine._global_pre_hooks) == 0

    def test_load_from_invalid_json(self, fresh_engine, tmp_path):
        config_file = tmp_path / "hooks.json"
        config_file.write_text("not valid json{{{", encoding="utf-8")
        fresh_engine.load_hooks_from_config(config_file)
        assert len(fresh_engine._global_pre_hooks) == 0

    def test_load_from_valid_config(self, fresh_engine, tmp_path):
        config_file = tmp_path / "hooks.json"
        config_data = {
            "hooks": [
                {
                    "type": "pre",
                    "tool_name": "test_tool",
                    "module": "os.path",
                    "function": "exists",
                }
            ]
        }
        config_file.write_text(json.dumps(config_data), encoding="utf-8")
        fresh_engine.load_hooks_from_config(config_file)
        assert len(fresh_engine._pre_hooks.get("test_tool", [])) == 1
