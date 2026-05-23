from __future__ import annotations

import functools
import inspect
from collections.abc import Callable
from typing import Any

from mcp.server.fastmcp import FastMCP

from .core.errors import make_success_response, retry_tool_call
from .core.hook_engine import get_hook_engine
from .core.logging_config import setup_logging
from .core.notifications import notify
from .core.rate_limiter import check_rate_limit

_REGISTERED_TOOL_NAMES: list[str] = []
_REGISTERED_RESOURCE_NAMES: list[str] = []
_TOOL_REGISTRY: dict[str, Any] = {}
_TOOL_FUNCTIONS: dict[str, Callable[..., Any]] = {}

mcp = FastMCP(
    "xuansto-mcp-server",
    instructions="Xuansto Skill MCP服务器 v8.0.0",
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
    agent_manage,
    hook_manage,
    resource_load_status,
    context_compress,
    server_health,
    decision_log,
    token_budget,
    project_init,
    metrics_report,
    config_manage,
)

def _with_hook_interception(tool_name: str, tool_fn: Callable[..., Any]) -> Callable[..., Any]:
    @functools.wraps(tool_fn)
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

        security_hook_failed = False
        for err in pre_errors:
            hook_name = err.get("hook", "")
            if "security" in hook_name.lower():
                security_hook_failed = True
                break

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

        if security_hook_failed:
            latency = (time.time() - start) * 1000
            record_tool_call(tool_name, latency, False)
            notify(f"Tool {tool_name} blocked: security hook failed", "warning")
            result = make_success_response({
                "action": "blocked",
                "tool": tool_name,
                "block_reason": "Security hook execution failed - blocking by default",
                "hook": "security",
            })
            if hook_errors:
                result["hook_errors"] = hook_errors
            return result

        rate_allowed, rate_info = check_rate_limit(tool_name)
        if not rate_allowed:
            latency = (time.time() - start) * 1000
            record_tool_call(tool_name, latency, False)
            notify(f"Tool {tool_name} rate limited", "warning")
            return {
                "error": True,
                "error_code": rate_info.get("error_code", "ERR_RATE_LIMITED"),
                "message": rate_info.get("message", "Rate limit exceeded"),
                "details": rate_info,
            }

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

    wrapped.__signature__ = inspect.signature(tool_fn)
    return wrapped


_original_mcp_tool = mcp.tool


def _tool_with_hooks(**kwargs: Any) -> Callable[..., Any]:
    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        tool_name = fn.__name__
        wrapped = _with_hook_interception(tool_name, fn)
        _TOOL_FUNCTIONS[tool_name] = wrapped
        return _original_mcp_tool(**kwargs)(wrapped)
    return decorator


mcp.tool = _tool_with_hooks

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
    agent_manage,
    hook_manage,
    resource_load_status,
    context_compress,
    server_health,
    decision_log,
    token_budget,
    project_init,
    metrics_report,
    config_manage,
]:
    tool_module.register(mcp)

mcp.tool = _original_mcp_tool

_REGISTERED_TOOL_NAMES = list(_TOOL_FUNCTIONS.keys())
_TOOL_REGISTRY = dict(_TOOL_FUNCTIONS)

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
    from .core.database import init_db
    init_db()
    from .tools.session_manage import restore_on_startup
    restore_on_startup()
    from .tools.workflow_dispatch import load_on_startup as workflow_load_on_startup
    workflow_load_on_startup()
    from .tools.agent_manage import load_on_startup as agent_load_on_startup
    agent_load_on_startup()
    from .tools.server_health import load_on_startup as health_load_on_startup
    health_load_on_startup()
    from .tools.server_health import metrics_load_on_startup, degradation_load_on_startup
    metrics_load_on_startup()
    degradation_load_on_startup()
    from .core.degradation import start_fallback_watcher
    start_fallback_watcher()
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
