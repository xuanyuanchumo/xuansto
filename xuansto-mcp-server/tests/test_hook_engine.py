from __future__ import annotations

import asyncio
import logging
from unittest.mock import patch

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


_EXPECTED_HOOK_TYPES = [
    "pre",
    "post",
    "phase_enter",
    "phase_exit",
    "gate_pass",
    "gate_fail",
    "session_start",
    "session_stop",
]


def test_hook_type_enum_values():
    for ht in _EXPECTED_HOOK_TYPES:
        assert HookType(ht) is not None
    assert len(HookType) == len(_EXPECTED_HOOK_TYPES)


def test_hook_type_enum_members():
    assert HookType.PRE.value == "pre"
    assert HookType.POST.value == "post"
    assert HookType.PHASE_ENTER.value == "phase_enter"
    assert HookType.PHASE_EXIT.value == "phase_exit"
    assert HookType.GATE_PASS.value == "gate_pass"
    assert HookType.GATE_FAIL.value == "gate_fail"
    assert HookType.SESSION_START.value == "session_start"
    assert HookType.SESSION_STOP.value == "session_stop"


def test_register_hook_with_enum(fresh_hook_engine):
    engine = fresh_hook_engine
    handler = lambda tool_name, kwargs: ([], [])
    engine.register_hook(HookType.PRE, handler, tool_name="my_tool")
    assert handler in engine._pre_hooks.get("my_tool", [])


def test_register_hook_with_string_backward_compat(fresh_hook_engine):
    engine = fresh_hook_engine
    handler = lambda tool_name, kwargs: ([], [])
    engine.register_hook("pre", handler, tool_name="my_tool")
    assert handler in engine._pre_hooks.get("my_tool", [])


def test_register_hook_unknown_string_falls_back_to_pre(fresh_hook_engine):
    engine = fresh_hook_engine
    handler = lambda tool_name, kwargs: ([], [])
    engine.register_hook("unknown_type", handler, tool_name="my_tool")
    assert handler in engine._pre_hooks.get("my_tool", [])


def test_register_hook_global_pre(fresh_hook_engine):
    engine = fresh_hook_engine
    handler = lambda tool_name, kwargs: ([], [])
    engine.register_hook(HookType.PRE, handler)
    assert handler in engine._global_pre_hooks


def test_register_hook_global_post(fresh_hook_engine):
    engine = fresh_hook_engine
    handler = lambda tool_name, kwargs, result: []
    engine.register_hook(HookType.POST, handler)
    assert handler in engine._global_post_hooks


def test_register_hook_phase_enter(fresh_hook_engine):
    engine = fresh_hook_engine
    handler = lambda *args, **kwargs: None
    engine.register_hook(HookType.PHASE_ENTER, handler, tool_name="phase_tool")
    assert handler in engine._phase_enter_hooks.get("phase_tool", [])


def test_register_hook_phase_exit_global(fresh_hook_engine):
    engine = fresh_hook_engine
    handler = lambda *args, **kwargs: None
    engine.register_hook(HookType.PHASE_EXIT, handler)
    assert handler in engine._phase_exit_hooks.get("__global__", [])


def test_register_hook_session_start(fresh_hook_engine):
    engine = fresh_hook_engine
    handler = lambda *args, **kwargs: None
    engine.register_hook(HookType.SESSION_START, handler)
    assert handler in engine._session_start_hooks


def test_register_hook_session_stop(fresh_hook_engine):
    engine = fresh_hook_engine
    handler = lambda *args, **kwargs: None
    engine.register_hook(HookType.SESSION_STOP, handler)
    assert handler in engine._session_stop_hooks


@pytest.mark.asyncio
async def test_execute_pre_hooks(fresh_hook_engine):
    engine = fresh_hook_engine
    called = []

    def my_pre_hook(tool_name, kwargs):
        called.append(tool_name)
        return ([], [])

    engine.register_hook("pre", my_pre_hook, tool_name="test_tool")
    results, errors = await engine.execute_pre_hooks("test_tool", {"key": "val"})
    assert "test_tool" in called
    assert isinstance(results, list)
    assert isinstance(errors, list)


@pytest.mark.asyncio
async def test_execute_pre_hooks_with_global(fresh_hook_engine):
    engine = fresh_hook_engine
    called = []

    def global_pre(tool_name, kwargs):
        called.append(("global", tool_name))
        return ([], [])

    def tool_pre(tool_name, kwargs):
        called.append(("tool", tool_name))
        return ([], [])

    engine.register_hook(HookType.PRE, global_pre)
    engine.register_hook(HookType.PRE, tool_pre, tool_name="my_tool")
    await engine.execute_pre_hooks("my_tool", {})
    assert ("global", "my_tool") in called
    assert ("tool", "my_tool") in called
    global_idx = called.index(("global", "my_tool"))
    tool_idx = called.index(("tool", "my_tool"))
    assert global_idx < tool_idx


@pytest.mark.asyncio
async def test_execute_post_hooks(fresh_hook_engine):
    engine = fresh_hook_engine
    called = []

    def my_post_hook(tool_name, kwargs, result):
        called.append(tool_name)
        return []

    engine.register_hook("post", my_post_hook, tool_name="test_tool")
    errors = await engine.execute_post_hooks("test_tool", {"key": "val"}, {"data": 1})
    assert "test_tool" in called
    assert isinstance(errors, list)


@pytest.mark.asyncio
async def test_security_hook_failure_blocks_tool_call(fresh_hook_engine):
    engine = fresh_hook_engine

    def security_hook(tool_name, kwargs):
        raise RuntimeError("Security check failed")

    engine.register_hook("pre", security_hook, tool_name="dangerous_tool")
    results, errors = await engine.execute_pre_hooks("dangerous_tool", {})
    assert len(errors) >= 1
    assert any("security_hook" in e.get("hook", "") for e in errors)


@pytest.mark.asyncio
async def test_pre_hook_returns_block_status(fresh_hook_engine):
    engine = fresh_hook_engine
    call_count = 0

    def blocking_hook(tool_name, kwargs):
        nonlocal call_count
        call_count += 1
        return {"status": "block"}

    def second_hook(tool_name, kwargs):
        nonlocal call_count
        call_count += 1
        return ([], [])

    engine.register_hook(HookType.PRE, blocking_hook, tool_name="blocked_tool")
    engine.register_hook(HookType.PRE, second_hook, tool_name="blocked_tool")
    results, errors = await engine.execute_pre_hooks("blocked_tool", {})
    assert call_count == 1


@pytest.mark.asyncio
async def test_async_pre_hook(fresh_hook_engine):
    engine = fresh_hook_engine
    called = []

    async def async_pre(tool_name, kwargs):
        called.append(tool_name)
        return ([], [])

    engine.register_hook(HookType.PRE, async_pre, tool_name="async_tool")
    results, errors = await engine.execute_pre_hooks("async_tool", {})
    assert "async_tool" in called


@pytest.mark.asyncio
async def test_async_post_hook(fresh_hook_engine):
    engine = fresh_hook_engine
    called = []

    async def async_post(tool_name, kwargs, result):
        called.append(tool_name)
        return []

    engine.register_hook(HookType.POST, async_post, tool_name="async_tool")
    errors = await engine.execute_post_hooks("async_tool", {}, {"data": 1})
    assert "async_tool" in called


def test_hook_failure_counting():
    _hook_failure_counts.pop("test_handler", None)
    _record_hook_failure("test_handler")
    assert _hook_failure_counts.get("test_handler") == 1
    _record_hook_failure("test_handler")
    assert _hook_failure_counts.get("test_handler") == 2
    _reset_hook_failure_count("test_handler")
    assert "test_handler" not in _hook_failure_counts


def test_hook_failure_alert_threshold(caplog):
    _hook_failure_counts.pop("alert_handler", None)
    with caplog.at_level(logging.WARNING, logger="xuansto-mcp.hook_engine"):
        for _ in range(_HOOK_FAILURE_THRESHOLD):
            _record_hook_failure("alert_handler")
    assert any("Alert" in r.message for r in caplog.records)
    _reset_hook_failure_count("alert_handler")


def test_reset_hook_failure_count_nonexistent():
    _reset_hook_failure_count("nonexistent_handler_xyz")
    assert "nonexistent_handler_xyz" not in _hook_failure_counts


def test_unregister_hook(fresh_hook_engine):
    engine = fresh_hook_engine
    handler = lambda tool_name, kwargs: ([], [])
    engine.register_hook(HookType.PRE, handler, tool_name="my_tool")
    assert handler in engine._pre_hooks.get("my_tool", [])
    result = engine.unregister_hook(HookType.PRE, handler, tool_name="my_tool")
    assert result is True
    assert handler not in engine._pre_hooks.get("my_tool", [])


def test_unregister_hook_not_found(fresh_hook_engine):
    engine = fresh_hook_engine
    handler = lambda tool_name, kwargs: ([], [])
    result = engine.unregister_hook(HookType.PRE, handler, tool_name="my_tool")
    assert result is False


def test_unregister_global_hook(fresh_hook_engine):
    engine = fresh_hook_engine
    handler = lambda tool_name, kwargs: ([], [])
    engine.register_hook(HookType.PRE, handler)
    result = engine.unregister_hook(HookType.PRE, handler)
    assert result is True
    assert handler not in engine._global_pre_hooks


def test_unregister_session_hook(fresh_hook_engine):
    engine = fresh_hook_engine
    handler = lambda *args, **kwargs: None
    engine.register_hook(HookType.SESSION_START, handler)
    result = engine.unregister_hook(HookType.SESSION_START, handler)
    assert result is True
    assert handler not in engine._session_start_hooks


def test_resolve_hook_type_enum():
    assert _resolve_hook_type(HookType.PRE) == HookType.PRE
    assert _resolve_hook_type(HookType.POST) == HookType.POST


def test_resolve_hook_type_string():
    assert _resolve_hook_type("pre") == HookType.PRE
    assert _resolve_hook_type("post") == HookType.POST
    assert _resolve_hook_type("phase_enter") == HookType.PHASE_ENTER


def test_resolve_hook_type_unknown_string():
    result = _resolve_hook_type("unknown_type")
    assert result == HookType.PRE


def test_get_failure_counts(fresh_hook_engine):
    _hook_failure_counts.pop("count_test", None)
    _record_hook_failure("count_test")
    counts = fresh_hook_engine.get_failure_counts()
    assert isinstance(counts, dict)
    assert "count_test" in counts
    _reset_hook_failure_count("count_test")
