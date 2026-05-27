from __future__ import annotations

import asyncio
import logging
import time

from xuansto_mcp.core.hook_engine import (
    DEFAULT_HOOK_TIMEOUT_SECONDS,
    HookEngine,
    HookType,
)


def test_default_hook_timeout_is_30():
    assert DEFAULT_HOOK_TIMEOUT_SECONDS == 30.0


def test_normal_hook_completes_within_timeout():
    engine = HookEngine(hook_timeout=5.0)
    called = []

    def fast_hook(tool_name, kwargs):
        called.append(tool_name)
        return ([], [])

    engine.register_hook(HookType.PRE, fast_hook, tool_name="test_tool")
    results, errors = asyncio.run(engine.execute_pre_hooks("test_tool", {}))
    assert "test_tool" in called
    assert len(errors) == 0


def test_async_normal_hook_completes_within_timeout():
    engine = HookEngine(hook_timeout=5.0)
    called = []

    async def async_fast_hook(tool_name, kwargs):
        called.append(tool_name)
        return ([], [])

    engine.register_hook(HookType.PRE, async_fast_hook, tool_name="async_tool")
    results, errors = asyncio.run(engine.execute_pre_hooks("async_tool", {}))
    assert "async_tool" in called
    assert len(errors) == 0


def test_hook_timeout_is_cancelled_and_warning_logged(caplog):
    engine = HookEngine(hook_timeout=0.2)

    def slow_hook(tool_name, kwargs):
        time.sleep(5)
        return ([], [])

    engine.register_hook(HookType.PRE, slow_hook, tool_name="slow_tool")
    with caplog.at_level(logging.WARNING, logger="xuansto-mcp.hook_engine"):
        results, errors = asyncio.run(engine.execute_pre_hooks("slow_tool", {}))
    assert len(errors) >= 1
    timeout_errors = [e for e in errors if "timeout" in e.get("error", "")]
    assert len(timeout_errors) >= 1
    assert any("timed out" in r.message for r in caplog.records)


def test_async_hook_timeout_is_cancelled_and_warning_logged(caplog):
    engine = HookEngine(hook_timeout=0.2)

    async def slow_async_hook(tool_name, kwargs):
        await asyncio.sleep(5)
        return ([], [])

    engine.register_hook(HookType.PRE, slow_async_hook, tool_name="slow_async_tool")
    with caplog.at_level(logging.WARNING, logger="xuansto-mcp.hook_engine"):
        results, errors = asyncio.run(engine.execute_pre_hooks("slow_async_tool", {}))
    assert len(errors) >= 1
    timeout_errors = [e for e in errors if "timeout" in e.get("error", "")]
    assert len(timeout_errors) >= 1


def test_execution_continues_after_timeout():
    engine = HookEngine(hook_timeout=0.2)

    def slow_hook(tool_name, kwargs):
        time.sleep(5)
        return ([], [])

    def fast_hook(tool_name, kwargs):
        return ([{"status": "ok"}], [])

    engine.register_hook(HookType.PRE, slow_hook, tool_name="mixed_tool")
    engine.register_hook(HookType.PRE, fast_hook, tool_name="mixed_tool")
    results, errors = asyncio.run(engine.execute_pre_hooks("mixed_tool", {}))
    assert len(errors) >= 1
    assert any(r.get("status") == "ok" for r in results)


def test_custom_timeout_value_is_respected():
    engine = HookEngine(hook_timeout=0.5)

    def slightly_slow_hook(tool_name, kwargs):
        time.sleep(0.3)
        return ([], [])

    engine.register_hook(HookType.PRE, slightly_slow_hook, tool_name="custom_tool")
    results, errors = asyncio.run(engine.execute_pre_hooks("custom_tool", {}))
    assert len(errors) == 0

    engine2 = HookEngine(hook_timeout=0.1)
    engine2.register_hook(HookType.PRE, slightly_slow_hook, tool_name="custom_tool2")
    results2, errors2 = asyncio.run(engine2.execute_pre_hooks("custom_tool2", {}))
    assert len(errors2) >= 1


def test_post_hook_timeout_continues(caplog):
    engine = HookEngine(hook_timeout=0.2)

    def slow_post_hook(tool_name, kwargs, result):
        time.sleep(5)
        return []

    engine.register_hook(HookType.POST, slow_post_hook, tool_name="slow_post_tool")
    with caplog.at_level(logging.WARNING, logger="xuansto-mcp.hook_engine"):
        errors = asyncio.run(engine.execute_post_hooks("slow_post_tool", {}, {"data": 1}))
    assert len(errors) >= 1
    timeout_errors = [e for e in errors if "timeout" in e.get("error", "")]
    assert len(timeout_errors) >= 1
