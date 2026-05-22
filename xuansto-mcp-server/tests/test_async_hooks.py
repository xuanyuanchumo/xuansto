from __future__ import annotations

import asyncio
import inspect
from pathlib import Path

from xuansto_mcp import __version__
from xuansto_mcp.tools.hook_manage import async_execute_pre_hooks, async_execute_post_hooks


def test_async_pre_hooks_exist():
    assert callable(async_execute_pre_hooks)
    assert inspect.iscoroutinefunction(async_execute_pre_hooks)


def test_async_post_hooks_exist():
    assert callable(async_execute_post_hooks)
    assert inspect.iscoroutinefunction(async_execute_post_hooks)


def test_async_hooks_use_to_thread():
    hook_manage_path = Path(__file__).resolve().parent.parent / "src" / "xuansto_mcp" / "tools" / "hook_manage.py"
    source = hook_manage_path.read_text(encoding="utf-8")
    assert "asyncio.to_thread" in source


def test_server_wrapped_uses_async_hooks():
    server_path = Path(__file__).resolve().parent.parent / "src" / "xuansto_mcp" / "server.py"
    source = server_path.read_text(encoding="utf-8")
    assert "async_execute_pre_hooks" in source
    assert "async_execute_post_hooks" in source


def test_version_is_350():
    assert __version__ == "3.5.0"
