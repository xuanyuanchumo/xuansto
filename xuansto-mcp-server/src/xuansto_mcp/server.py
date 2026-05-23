from __future__ import annotations

from typing import Any, Callable

from mcp.server.fastmcp import FastMCP

from .core.errors import make_success_response, retry_tool_call
from .core.hook_engine import get_hook_engine
from .core.logging_config import setup_logging
from .core.notifications import NotificationCallback, set_notification_callback, get_notification_callback, notify

_REGISTERED_TOOL_NAMES: list[str] = []
_REGISTERED_RESOURCE_NAMES: list[str] = []
_TOOL_REGISTRY: dict[str, Any] = {}

mcp = FastMCP(
    "xuansto-mcp-server",
    instructions="Xuansto Skill MCP服务器 v4.1.0",
)

from .tools import (
    skill_analyze,
    knowledge_search,
    knowledge_inject,
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
    decision_log,
    token_budget,
    project_init,
)

for tool_module in [
    skill_analyze,
    knowledge_search,
    knowledge_inject,
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
    decision_log,
    token_budget,
    project_init,
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
        import json as _json
        from .tools.server_health import record_tool_call
        from .tools.resource_load_status import record_token_usage

        start = time.time()
        hook_errors: list[dict[str, str]] = []

        engine = get_hook_engine()
        pre_results, pre_errors = await engine.execute_pre_hooks(tool_name, kwargs)
        hook_errors.extend(pre_errors)
        for pr in pre_results:
            if pr.get("status") == "block":
                latency = (time.time() - start) * 1000
                record_tool_call(tool_name, latency, False)
                notify(f"Tool {tool_name} blocked by pre-hook: {pr.get('reason', '')}", "warning")
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
            result = await retry_tool_call(tool_name, tool_fn, kwargs)
            latency = (time.time() - start) * 1000
            record_tool_call(tool_name, latency, True)
        except Exception as e:
            latency = (time.time() - start) * 1000
            record_tool_call(tool_name, latency, False)
            notify(f"Tool {tool_name} failed: {e}", "error")
            raise

        try:
            input_text = _json.dumps(kwargs, ensure_ascii=False, default=str)
            output_text = _json.dumps(result, ensure_ascii=False, default=str) if isinstance(result, dict) else str(result)
            record_token_usage(tool_name, input_text, output_text)
        except Exception:
            pass

        if isinstance(result, dict):
            post_errors = await engine.execute_post_hooks(tool_name, kwargs, result)
            hook_errors.extend(post_errors)
            if hook_errors:
                result["hook_errors"] = hook_errors
            return result
        return {"error": False, "data": result}

    return wrapped


try:
    for _tname, _tentry in list(mcp._tool_manager._tools.items()):
        _tentry.fn = _with_hook_interception(_tname, _tentry.fn)
except AttributeError:
    pass

_hook_engine = get_hook_engine()
from .tools.hook_manage import execute_pre_hooks, execute_post_hooks
_hook_engine.register_hook("pre", execute_pre_hooks)
_hook_engine.register_hook("post", execute_post_hooks)

from .core.config import HOOKS_PATH
_hook_engine.load_hooks_from_config(HOOKS_PATH)

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
