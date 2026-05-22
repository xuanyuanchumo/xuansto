from __future__ import annotations

import asyncio
from typing import Any, Callable

from mcp.server.fastmcp import FastMCP

from .core.errors import make_success_response
from .core.logging_config import setup_logging

_REGISTERED_TOOL_NAMES: list[str] = []
_REGISTERED_RESOURCE_NAMES: list[str] = []
_TOOL_REGISTRY: dict[str, Any] = {}

mcp = FastMCP(
    "xuansto-mcp-server",
    instructions="Xuansto Skill MCP服务器 v3.5.0",
)

from .tools import (
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

for tool_module in [
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
    tool_module.register(mcp)

try:
    _REGISTERED_TOOL_NAMES = list(mcp._tool_manager._tools.keys())
    _TOOL_REGISTRY = dict(mcp._tool_manager._tools)
except AttributeError:
    _REGISTERED_TOOL_NAMES = []
    _TOOL_REGISTRY = {}


def _with_hook_interception(tool_name: str, tool_fn: Callable[..., Any]) -> Callable[..., Any]:
    async def wrapped(**kwargs: Any) -> dict[str, Any]:
        import time
        from .tools.hook_manage import async_execute_pre_hooks, async_execute_post_hooks
        from .tools.server_health import record_tool_call

        start = time.time()
        hook_errors: list[dict[str, str]] = []

        pre_results, pre_errors = await async_execute_pre_hooks(tool_name, kwargs)
        hook_errors.extend(pre_errors)
        for pr in pre_results:
            if pr.get("status") == "block":
                latency = (time.time() - start) * 1000
                record_tool_call(tool_name, latency, False)
                result = make_success_response({
                    "action": "blocked",
                    "tool": tool_name,
                    "block_reason": pr.get("reason", "Pre-hook blocked execution"),
                    "hook": pr.get("hook", ""),
                })
                if hook_errors:
                    result["hook_errors"] = hook_errors
                return result

        try:
            if asyncio.iscoroutinefunction(tool_fn):
                result = await tool_fn(**kwargs)
            else:
                result = tool_fn(**kwargs)
            latency = (time.time() - start) * 1000
            record_tool_call(tool_name, latency, True)
        except Exception as e:
            latency = (time.time() - start) * 1000
            record_tool_call(tool_name, latency, False)
            raise

        if isinstance(result, dict):
            post_errors = await async_execute_post_hooks(tool_name, kwargs, result)
            hook_errors.extend(post_errors)
            if hook_errors:
                result["hook_errors"] = hook_errors
            return result
        return {"error": False, "data": result}

    return wrapped


# Wrap tools with hook interception and performance tracking
try:
    for _tname, _tentry in list(mcp._tool_manager._tools.items()):
        _tentry.fn = _with_hook_interception(_tname, _tentry.fn)
except AttributeError:
    pass

from .resources import skill_resources

skill_resources.register(mcp)

try:
    _REGISTERED_RESOURCE_NAMES = list(mcp._resource_manager._resources.keys())
    _REGISTERED_RESOURCE_NAMES.extend(mcp._resource_manager._templates.keys())
except AttributeError:
    _REGISTERED_RESOURCE_NAMES = []


def main() -> None:
    setup_logging()
    from .core.config import start_config_watcher
    start_config_watcher()
    from .tools.session_manage import restore_on_startup
    restore_on_startup()
    from .tools.workflow_dispatch import load_on_startup as workflow_load_on_startup
    workflow_load_on_startup()
    from .tools.agent_status import load_on_startup as agent_load_on_startup
    agent_load_on_startup()
    from .tools.server_health import load_on_startup as health_load_on_startup
    health_load_on_startup()
    from .tools.server_health import metrics_load_on_startup, degradation_load_on_startup
    metrics_load_on_startup()
    degradation_load_on_startup()
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
