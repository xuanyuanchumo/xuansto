from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, cast

from .config import SCRIPTS_DIR, DATA_DIR
from .errors import XuanstoMCPError, make_error_response, make_success_response, ERR_INTERNAL
from .logging_config import get_logger

logger = get_logger("degradation")

MCP_AVAILABLE = True

_FALLBACK_CONFIG_PATH = DATA_DIR / "fallback_config.yaml"


def check_mcp_available() -> bool:
    global MCP_AVAILABLE
    try:
        from mcp.server.fastmcp import FastMCP
        MCP_AVAILABLE = True
        return True
    except ImportError:
        MCP_AVAILABLE = False
        return False


def run_script_fallback(
    script_name: str,
    args: list[str] | None = None,
    cwd: str = ".",
    timeout: int = 60,
) -> dict[str, Any]:
    script_path = SCRIPTS_DIR / script_name
    if not script_path.exists():
        return {
            "error": True,
            "code": "SCRIPT_NOT_FOUND",
            "message": f"脚本不存在: {script_name}",
            "fallback": True,
        }

    cmd = [sys.executable, str(script_path)]
    if args:
        cmd.extend(args)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
        )
        try:
            parsed = json.loads(result.stdout)
            return {"error": False, "data": parsed, "fallback": True}
        except json.JSONDecodeError:
            return {
                "error": False,
                "data": {"raw_output": result.stdout[:2000]},
                "fallback": True,
            }
    except subprocess.TimeoutExpired:
        return {
            "error": True,
            "code": "TIMEOUT",
            "message": f"脚本执行超时({timeout}s): {script_name}",
            "fallback": True,
        }
    except Exception as e:
        return {
            "error": True,
            "code": "EXECUTION_ERROR",
            "message": str(e),
            "fallback": True,
        }


def _fallback_success(
    tool: str,
    data: dict[str, Any] | None = None,
    degradation_level: str | None = None,
    **extra: Any,
) -> dict[str, Any]:
    base = data if isinstance(data, dict) else {}
    enriched = {"tool": tool, "source": "fallback", **base, **extra}
    if "status" not in enriched:
        enriched["status"] = "degraded"
    if "note" not in enriched:
        enriched["note"] = "主工具不可用，使用降级响应"
    return make_success_response(enriched, degradation_level=degradation_level)


def _fallback_error(tool: str, code: str, message: str) -> dict[str, Any]:
    return make_error_response(XuanstoMCPError(
        code=code,
        message=message,
        details={"tool": tool, "source": "fallback"},
    ), error_code=ERR_INTERNAL)


def _standardize_result(
    result: dict[str, Any],
    tool: str,
    **extra: Any,
) -> dict[str, Any]:
    if result.get("error"):
        return make_error_response(XuanstoMCPError(
            code=result.get("code", "UNKNOWN_ERROR"),
            message=result.get("message", "未知错误"),
            details={"tool": tool, "source": "fallback"},
        ), error_code=ERR_INTERNAL)
    data = result.get("data", {})
    if not isinstance(data, dict):
        data = {"result": data}
    return _fallback_success(tool, data, **extra)


def skill_analyze_fallback(skill_path: str, **kwargs: Any) -> dict[str, Any]:
    logger.warning("Tool %s using fallback", "skill_analyze")
    script_result = run_script_fallback(
        "skill-test.py",
        args=["--analyze", "--path", skill_path, "--format", "json"],
        timeout=30,
    )
    if not script_result.get("error"):
        return _standardize_result(script_result, "skill_analyze")
    script_result = run_script_fallback(
        "skill-test.py",
        args=["--path", skill_path, "--format", "json"],
        timeout=30,
    )
    return _standardize_result(script_result, "skill_analyze")


def knowledge_search_fallback(query: str, **kwargs: Any) -> dict[str, Any]:
    logger.warning("Tool %s using fallback", "knowledge_search")
    script_result = run_script_fallback(
        "knowledge-server.py",
        args=["--search", "--query", query, "--format", "json"],
        timeout=30,
    )
    if not script_result.get("error"):
        return _standardize_result(script_result, "knowledge_search")
    script_result = run_script_fallback(
        "knowledge-server.py",
        args=["search", "--query", query, "--format", "json"],
        timeout=30,
    )
    return _standardize_result(script_result, "knowledge_search")


def quality_gate_fallback(gate_ids: list[str] | None = None, **kwargs: Any) -> dict[str, Any]:
    logger.warning("Tool %s using fallback", "quality_gate_check")
    gate_args = ["--gate", "--format", "json"]
    if gate_ids:
        gate_args.extend(["--gate-ids", ",".join(gate_ids)])
    script_result = run_script_fallback(
        "skill-test.py",
        args=gate_args,
        timeout=30,
    )
    if not script_result.get("error"):
        return _standardize_result(script_result, "quality_gate_check")
    from .config import GATE_SCRIPTS_MAP
    if not gate_ids:
        gate_ids = list(GATE_SCRIPTS_MAP.keys())
    results = []
    for gate_id in gate_ids:
        script = GATE_SCRIPTS_MAP.get(gate_id)
        if script:
            result = run_script_fallback(script, args=["--format", "json"], timeout=30)
            results.append({"gate_id": gate_id, **result})
        else:
            results.append({"gate_id": gate_id, "status": "SKIP", "fallback": True})
    return _fallback_success("quality_gate_check", {"checks": results})


def spec_drift_fallback(spec_dir: str = ".trae/specs", src_dir: str = ".", **kwargs: Any) -> dict[str, Any]:
    logger.warning("Tool %s using fallback", "spec_drift_detect")
    script_result = run_script_fallback(
        "spec-drift-detector.py",
        args=["--spec-dir", spec_dir, "--src-dir", src_dir, "--format", "json"],
        timeout=60,
    )
    if not script_result.get("error"):
        return _standardize_result(script_result, "spec_drift_detect")
    from ..tools.spec_drift_detect import _inline_spec_drift
    inline_result = _inline_spec_drift(spec_dir, src_dir)
    return _fallback_success("spec_drift_detect", inline_result, degradation_level="inline")


def security_scan_fallback(target: str = ".", severity_threshold: str = "medium", **kwargs: Any) -> dict[str, Any]:
    logger.warning("Tool %s using fallback", "security_scan")
    from ..tools.security_scan import _inline_agentic_scan, _inline_dependency_scan

    script_path = SCRIPTS_DIR / "agentic-security-scanner.py"
    if script_path.exists():
        result = run_script_fallback(
            "agentic-security-scanner.py",
            args=["--target", target, "--severity-threshold", severity_threshold, "--format", "json"],
            timeout=120,
        )
        if not result.get("error"):
            return _standardize_result(result, "security_scan")

    agentic_result = _inline_agentic_scan(target, severity_threshold)
    return _fallback_success("security_scan", {"agentic_scan": agentic_result}, degradation_level="inline")


def code_simplify_fallback(target: str, scope: str = "recent", **kwargs: Any) -> dict[str, Any]:
    logger.warning("Tool %s using fallback", "code_simplify")
    script_result = run_script_fallback(
        "code-simplifier.py",
        args=["--target", target, "--scope", scope, "--format", "json"],
        timeout=60,
    )
    if not script_result.get("error"):
        return _standardize_result(script_result, "code_simplify")

    from ..tools.code_simplify import _inline_simplify
    inline_result = _inline_simplify(target, scope)
    return _fallback_success("code_simplify", inline_result, degradation_level="inline")


def session_manage_fallback(action: str, **kwargs: Any) -> dict[str, Any]:
    logger.warning("Tool %s using fallback", "session_manage")
    if action in ("save", "init"):
        script_result = run_script_fallback(
            "init-session.py",
            args=["--action", action, "--format", "json"],
            timeout=15,
        )
        if not script_result.get("error"):
            return _standardize_result(script_result, "session_manage")
    if action in ("load", "detect", "restore"):
        script_result = run_script_fallback(
            "session-catchup.py",
            args=["--action", action, "--format", "json"],
            timeout=15,
        )
        if not script_result.get("error"):
            return _standardize_result(script_result, "session_manage")
    args_map = {
        "save": ["save"],
        "load": ["load"],
        "list": ["list"],
    }
    args = args_map.get(action, [action])
    return _standardize_result(
        run_script_fallback(
            "session-persist.py",
            args=args,
            timeout=15,
        ),
        "session_manage",
    )


def workflow_dispatch_fallback(action: str, **kwargs: Any) -> dict[str, Any]:
    logger.warning("Tool %s using fallback", "workflow_dispatch")
    if action == "start":
        return _standardize_result(
            run_script_fallback("project-initializer.py", args=["--format", "json"], timeout=30),
            "workflow_dispatch",
        )
    elif action == "status":
        try:
            from ..tools.workflow_dispatch import _load_workflow
            workflow_id = kwargs.get("workflow_id", "")
            if workflow_id:
                state = _load_workflow(workflow_id)
                if state:
                    return _fallback_success("workflow_dispatch", state)
        except Exception:
            pass
        return _fallback_success("workflow_dispatch", {"action": action, "status": "unavailable"})
    elif action == "abort":
        return _fallback_success("workflow_dispatch", {"status": "aborted"})
    return _fallback_error("workflow_dispatch", "UNKNOWN_ACTION", f"未知操作: {action}")


def agent_status_fallback(action: str = "list", **kwargs: Any) -> dict[str, Any]:
    logger.warning("Tool %s using fallback", "agent_status")
    from .config import AGENTS_DIR
    if action == "list" and AGENTS_DIR.exists():
        agents = []
        for agent_file in sorted(AGENTS_DIR.rglob("*.md")):
            agents.append({
                "name": agent_file.stem,
                "layer": agent_file.parent.name,
                "source": "static_registry",
            })
        return _fallback_success("agent_status", {"agents": agents, "total": len(agents)})
    if action in ("detail", "by_phase") and AGENTS_DIR.exists():
        agent_name = kwargs.get("agent_name", "")
        phase = kwargs.get("phase", "")
        if agent_name:
            for agent_file in AGENTS_DIR.rglob(f"{agent_name}.md"):
                content = agent_file.read_text(encoding="utf-8", errors="replace")[:2000]
                return _fallback_success("agent_status", {"name": agent_name, "content_preview": content, "source": "static_registry"})
        if phase:
            phase_agents = []
            for agent_file in sorted(AGENTS_DIR.rglob("*.md")):
                phase_agents.append({"name": agent_file.stem, "layer": agent_file.parent.name})
            return _fallback_success("agent_status", {"agents": phase_agents, "phase": phase, "source": "static_registry"})
    script_result = run_script_fallback("skill-test.py", args=["--agents", "--format", "json"], timeout=30)
    return _standardize_result(script_result, "agent_status")


def hook_manage_fallback(action: str = "list", **kwargs: Any) -> dict[str, Any]:
    logger.warning("Tool %s using fallback", "hook_manage")
    if action == "execute" and kwargs.get("hook_name"):
        hook_scripts = {
            "encoding-check": "check-encoding.py",
            "token-budget-check": "token-budget-guard.py",
            "session-save": "session-persist.py",
        }
        script = hook_scripts.get(kwargs["hook_name"])
        if script:
            return _standardize_result(
                run_script_fallback(script, args=["--format", "json"], timeout=30),
                "hook_manage",
            )
    return _fallback_success("hook_manage", {"hooks": []})


def resource_load_status_fallback(action: str = "status", **kwargs: Any) -> dict[str, Any]:
    logger.warning("Tool %s using fallback", "resource_load_status")
    try:
        from .config import WORK_DIR
        state_file = WORK_DIR / "resource_state.json"
        if state_file.exists():
            data = json.loads(state_file.read_text(encoding="utf-8"))
            return _fallback_success("resource_load_status", {"resources": data})
    except Exception:
        pass
    return _fallback_success("resource_load_status", {"resources": {}, "note": "持久化状态不可用"})


def context_compress_fallback(content: str = "", strategy: str = "semantic", **kwargs: Any) -> dict[str, Any]:
    logger.warning("Tool %s using fallback", "context_compress")
    return _standardize_result(
        run_script_fallback("context-compressor.py", args=["--strategy", strategy, "--format", "json"], timeout=30),
        "context_compress",
    )


def server_health_fallback(**kwargs: Any) -> dict[str, Any]:
    logger.warning("Tool %s using fallback", "server_health")
    script_result = run_script_fallback(
        "health-checker.py",
        args=["--format", "json"],
        timeout=15,
    )
    if not script_result.get("error"):
        return _standardize_result(script_result, "server_health")
    return _fallback_success("server_health", {"status": "degraded", "mcp_available": False})


def fallback_decision_log(action: str, **kwargs: Any) -> dict[str, Any]:
    logger.warning("Tool %s using fallback", "decision_log")
    script_result = run_script_fallback(
        "decision-log.py",
        args=["--action", action, "--format", "json"],
        timeout=30,
    )
    if not script_result.get("error"):
        return _standardize_result(script_result, "decision_log")
    from ..tools.decision_log import _inline_decision_log
    inline_result = _inline_decision_log(action, **kwargs)
    return _fallback_success("decision_log", inline_result, degradation_level="inline")


def fallback_token_budget(action: str, **kwargs: Any) -> dict[str, Any]:
    logger.warning("Tool %s using fallback", "token_budget")
    script_result = run_script_fallback(
        "token-budget-guard.py",
        args=["--action", action, "--format", "json"],
        timeout=30,
    )
    if not script_result.get("error"):
        return _standardize_result(script_result, "token_budget")
    from ..tools.token_budget import _inline_token_budget
    inline_result = _inline_token_budget(action, **kwargs)
    return _fallback_success("token_budget", inline_result, degradation_level="inline")


def fallback_project_init(action: str, **kwargs: Any) -> dict[str, Any]:
    logger.warning("Tool %s using fallback", "project_init")
    script_result = run_script_fallback(
        "project-initializer.py",
        args=["--action", action, "--format", "json"],
        timeout=30,
    )
    if not script_result.get("error"):
        return _standardize_result(script_result, "project_init")
    from ..tools.project_init import _inline_project_init
    inline_result = _inline_project_init(action, **kwargs)
    return _fallback_success("project_init", inline_result, degradation_level="inline")


FALLBACK_MAP = {
    "skill_analyze": skill_analyze_fallback,
    "knowledge_search": knowledge_search_fallback,
    "quality_gate_check": quality_gate_fallback,
    "spec_drift_detect": spec_drift_fallback,
    "security_scan": security_scan_fallback,
    "code_simplify": code_simplify_fallback,
    "session_manage": session_manage_fallback,
    "workflow_dispatch": workflow_dispatch_fallback,
    "agent_status": agent_status_fallback,
    "hook_manage": hook_manage_fallback,
    "resource_load_status": resource_load_status_fallback,
    "context_compress": context_compress_fallback,
    "server_health": server_health_fallback,
    "decision_log": fallback_decision_log,
    "token_budget": fallback_token_budget,
    "project_init": fallback_project_init,
}

_INLINE_FALLBACK_MAP = {
    "quality_gate_fallback": quality_gate_fallback,
    "spec_drift_fallback": spec_drift_fallback,
    "security_scan_fallback": security_scan_fallback,
    "code_simplify_fallback": code_simplify_fallback,
    "workflow_dispatch_fallback": workflow_dispatch_fallback,
    "agent_status_fallback": agent_status_fallback,
    "hook_manage_fallback": hook_manage_fallback,
    "resource_load_status_fallback": resource_load_status_fallback,
    "server_health_fallback": server_health_fallback,
}


def _load_fallback_config_from_yaml() -> dict[str, Any] | None:
    if not _FALLBACK_CONFIG_PATH.exists():
        return None
    try:
        import yaml
        raw = yaml.safe_load(_FALLBACK_CONFIG_PATH.read_text(encoding="utf-8"))
        if isinstance(raw, dict) and "fallback_map" in raw:
            return raw["fallback_map"]
    except Exception as exc:
        logger.warning("Failed to load fallback config from YAML: %s", exc)
    return None


def _build_fallback_map_from_yaml(yaml_config: dict[str, Any]) -> dict[str, Callable[..., Any]]:
    built: dict[str, Callable[..., Any]] = {}
    for tool_name, entry in yaml_config.items():
        inline_name = entry.get("inline") if isinstance(entry, dict) else None
        if inline_name and inline_name in _INLINE_FALLBACK_MAP:
            built[tool_name] = _INLINE_FALLBACK_MAP[inline_name]
        elif tool_name in FALLBACK_MAP:
            built[tool_name] = FALLBACK_MAP[tool_name]
    return built


def _resolve_fallback_map() -> dict[str, Callable[..., Any]]:
    yaml_config = _load_fallback_config_from_yaml()
    if yaml_config is not None:
        merged = _build_fallback_map_from_yaml(yaml_config)
        for tool_name, fn in FALLBACK_MAP.items():
            if tool_name not in merged:
                merged[tool_name] = fn
        return merged
    return dict(FALLBACK_MAP)


_RESOLVED_FALLBACK_MAP: dict[str, Callable[..., Any]] = _resolve_fallback_map()


def get_fallback(tool_name: str) -> Callable[..., Any] | None:
    fn = _RESOLVED_FALLBACK_MAP.get(tool_name)
    if fn:
        return cast(Callable[..., Any], fn)
    logger.warning("No fallback function for tool: %s", tool_name)
    return None
