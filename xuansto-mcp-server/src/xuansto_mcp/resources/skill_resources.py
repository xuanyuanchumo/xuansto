from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from ..core.config import SKILL_ROOT, REFERENCES_DIR, TEMPLATES_DIR, SESSION_DIR, WORK_DIR, AGENTS_DIR, _resolve_skill_file
from ..core.logging_config import get_logger
from ..core.validator import validate_path_safety

logger = get_logger("skill_resources")


def _is_safe_path(path_component: str, allowed_base_dirs: list[Path]) -> tuple[Path | None, str | None]:
    return validate_path_safety(path_component, allowed_base_dirs)


def _degraded_resource(uri: str, error: str) -> str:
    logger.warning("Resource degraded: %s - %s", uri, error)
    return json.dumps({
        "status": "degraded",
        "uri": uri,
        "message": f"Resource unavailable: {uri}",
        "error": error,
        "timestamp": time.time(),
    }, ensure_ascii=False, indent=2)


def register(mcp: FastMCP) -> None:
    """Register MCP Resources.

    Resources are read-only snapshots of server state (e.g., config files,
    reference documents, session history, metrics). They differ from Tools
    which provide interactive operations with side effects. Use Resources
    when clients need to inspect current state; use Tools (via config_manage,
    agent_manage, etc.) when clients need to modify state or execute actions.
    """
    @mcp.resource("xuansto://config/skill")
    def skill_config() -> str:
        try:
            config_path = _resolve_skill_file(".skill-config.yaml")
            if config_path.exists():
                return config_path.read_text(encoding="utf-8")
            return "# 配置文件不存在"
        except Exception as e:
            return _degraded_resource("xuansto://config/skill", str(e))

    @mcp.resource("xuansto://references/quality-gates")
    def quality_gates() -> str:
        try:
            ref_path = REFERENCES_DIR / "quality-gates.md"
            if ref_path.exists():
                return ref_path.read_text(encoding="utf-8")
            return "# 质量门禁文档不存在"
        except Exception as e:
            return _degraded_resource("xuansto://references/quality-gates", str(e))

    @mcp.resource("xuansto://references/agent-registry")
    def agent_registry() -> str:
        try:
            ref_path = REFERENCES_DIR / "agent-registry.md"
            if ref_path.exists():
                return ref_path.read_text(encoding="utf-8")
            return "# Agent注册表不存在"
        except Exception as e:
            return _degraded_resource("xuansto://references/agent-registry", str(e))

    @mcp.resource("xuansto://references/workflow-phases")
    def workflow_phases() -> str:
        try:
            ref_path = REFERENCES_DIR / "workflow-phases.md"
            if ref_path.exists():
                return ref_path.read_text(encoding="utf-8")
            return "# 工作流定义不存在"
        except Exception as e:
            return _degraded_resource("xuansto://references/workflow-phases", str(e))

    @mcp.resource("xuansto://templates/{name}")
    def template(name: str) -> str:
        try:
            safe_path, err = _is_safe_path(f"{name}.md", [TEMPLATES_DIR])
            if err or safe_path is None:
                return f"Error: invalid template name '{name}' ({err})"
            if safe_path.resolve().is_relative_to(TEMPLATES_DIR.resolve()) and safe_path.exists():
                return safe_path.read_text(encoding="utf-8")
            return f"Template '{name}' not found"
        except Exception as e:
            return _degraded_resource(f"xuansto://templates/{name}", str(e))

    @mcp.resource("xuansto://sessions/latest")
    def latest_session() -> str:
        try:
            SESSION_DIR.mkdir(parents=True, exist_ok=True)
            sessions = sorted(SESSION_DIR.glob("session-*.md"), reverse=True)
            if sessions:
                return sessions[0].read_text(encoding="utf-8")
            return "# 无会话记录"
        except Exception as e:
            return _degraded_resource("xuansto://sessions/latest", str(e))

    @mcp.resource("xuansto://sessions/{session_id}")
    def session_by_id(session_id: str) -> str:
        try:
            safe_path, err = _is_safe_path(f"session-{session_id}.md", [SESSION_DIR])
            if err or safe_path is None:
                return f"Error: invalid session id '{session_id}' ({err})"
            if safe_path.resolve().is_relative_to(SESSION_DIR.resolve()) and safe_path.exists():
                return safe_path.read_text(encoding="utf-8")
            SESSION_DIR.mkdir(parents=True, exist_ok=True)
            for f in SESSION_DIR.glob(f"*{session_id}*"):
                if f.is_file():
                    return f.read_text(encoding="utf-8")
            return f"Session '{session_id}' not found"
        except Exception as e:
            return _degraded_resource(f"xuansto://sessions/{session_id}", str(e))

    @mcp.resource("xuansto://agents/{layer}/{name}")
    def agent_by_layer_name(layer: str, name: str) -> str:
        try:
            agent_dir = AGENTS_DIR / layer
            safe_path, err = _is_safe_path(f"{name}.md", [agent_dir])
            if err or safe_path is None:
                agent_dir_alt = AGENTS_DIR / layer
                safe_path, err = _is_safe_path(f"{name}.md", [agent_dir_alt])
                if err or safe_path is None:
                    return f"Error: invalid agent path '{layer}/{name}' ({err})"
            if safe_path.resolve().is_relative_to(AGENTS_DIR.resolve()) and safe_path.exists():
                return safe_path.read_text(encoding="utf-8")
            for f in AGENTS_DIR.rglob(f"{name}.md"):
                if f.is_file():
                    return f.read_text(encoding="utf-8")
            return f"Agent '{layer}/{name}' not found"
        except Exception as e:
            return _degraded_resource(f"xuansto://agents/{layer}/{name}", str(e))

    @mcp.resource("xuansto://loading/status")
    def loading_status() -> str:
        try:
            state_file = WORK_DIR / "resource_state.json"
            loaded_resources: list[str] = []
            loading_progress: dict[str, Any] = {}
            current_phase = "skeleton"
            resources_map: dict[str, dict[str, Any]] = {}

            if state_file.exists():
                try:
                    data = json.loads(state_file.read_text(encoding="utf-8"))
                    if isinstance(data, list):
                        loaded_resources = data
                    elif isinstance(data, dict):
                        loaded_resources = data.get("loaded", [])
                        loading_progress = data.get("progress", {})
                        current_phase = data.get("phase", current_phase)
                        resources_map = data.get("resources", {})
                        if isinstance(resources_map, list):
                            resources_map = {}
                except (json.JSONDecodeError, OSError):
                    pass

            phase_map = {
                "skeleton": 0,
                "functional": 1,
                "enhanced": 2,
                "full": 3,
            }
            phase_index = phase_map.get(current_phase, 0)

            available_refs = []
            if REFERENCES_DIR.exists():
                available_refs = [f.name for f in REFERENCES_DIR.glob("*.md")]

            available_functions_map = {
                "skeleton": {
                    "command_routing": True,
                    "command_execution": False,
                    "quality_gates": False,
                    "knowledge_search": False,
                    "reference_docs": False,
                    "agent_details": False,
                    "full_scripts": False,
                },
                "functional": {
                    "command_routing": True,
                    "command_execution": True,
                    "quality_gates": True,
                    "knowledge_search": False,
                    "reference_docs": False,
                    "agent_details": False,
                    "full_scripts": False,
                },
                "enhanced": {
                    "command_routing": True,
                    "command_execution": True,
                    "quality_gates": True,
                    "knowledge_search": True,
                    "reference_docs": True,
                    "agent_details": True,
                    "full_scripts": False,
                },
                "full": {
                    "command_routing": True,
                    "command_execution": True,
                    "quality_gates": True,
                    "knowledge_search": True,
                    "reference_docs": True,
                    "agent_details": True,
                    "full_scripts": True,
                },
            }

            disclosure_notes = {
                "skeleton": "骨架阶段，仅命令路由可用",
                "functional": "功能阶段，知识检索需推进到增强阶段",
                "enhanced": "增强阶段，完整脚本集需推进到完整阶段",
                "full": "完整阶段，全部功能可用",
            }

            available_functions = available_functions_map.get(
                current_phase, available_functions_map["skeleton"]
            )
            disclosure_note = disclosure_notes.get(
                current_phase, disclosure_notes["skeleton"]
            )

            status = {
                "current_phase": current_phase,
                "phase_index": phase_index,
                "loaded_resources": loaded_resources,
                "loaded_count": len(loaded_resources),
                "resources_map": resources_map,
                "available_references": available_refs,
                "available_functions": available_functions,
                "loading_progress": loading_progress,
                "disclosure_note": disclosure_note,
                "timestamp": time.time(),
            }
            return json.dumps(status, ensure_ascii=False, indent=2)
        except Exception as e:
            return _degraded_resource("xuansto://loading/status", str(e))

    @mcp.resource("xuansto://metrics/summary")
    def metrics_summary() -> str:
        try:
            metrics_path = WORK_DIR / "tool_metrics.json"
            degr_path = WORK_DIR / "degradation_stats.json"
            tool_metrics: dict[str, Any] = {}
            degradation_stats: dict[str, int] = {}
            if metrics_path.exists():
                try:
                    tool_metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, OSError):
                    pass
            if degr_path.exists():
                try:
                    degradation_stats = json.loads(degr_path.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, OSError):
                    pass
            total_calls = sum(m.get("call_count", 0) for m in tool_metrics.values())
            total_errors = sum(m.get("error_count", 0) for m in tool_metrics.values())
            summary = {
                "total_tools": len(tool_metrics),
                "total_calls": total_calls,
                "total_errors": total_errors,
                "overall_error_rate": round(total_errors / max(total_calls, 1), 4),
                "degradation_counts": degradation_stats,
                "timestamp": time.time(),
            }
            return json.dumps(summary, ensure_ascii=False, indent=2)
        except Exception as e:
            return _degraded_resource("xuansto://metrics/summary", str(e))

    @mcp.resource("xuansto://degradation/status")
    def degradation_status() -> str:
        try:
            from ..core.degradation import get_degradation_manager
            manager = get_degradation_manager()
            status = manager.get_status()
            return json.dumps(status, ensure_ascii=False, indent=2)
        except Exception as e:
            return _degraded_resource("xuansto://degradation/status", str(e))
