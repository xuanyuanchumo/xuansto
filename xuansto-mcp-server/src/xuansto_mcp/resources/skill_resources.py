from __future__ import annotations

import contextlib
import json
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from ..core.config import (
    AGENTS_DIR,
    COMMANDS_DIR,
    HOOKS_PATH,
    KNOWLEDGE_CHROMA_PATH,
    KNOWLEDGE_DB_PATH,
    KNOWLEDGE_DIR,
    REFERENCES_DIR,
    SESSION_DIR,
    TEMPLATES_DIR,
    WORK_DIR,
    _resolve_skill_file,
)
from ..core.logging_config import get_logger
from ..core.validator import validate_path_safety

logger = get_logger("skill_resources")

_resource_subscriptions: dict[str, list[str]] = {}
_subscription_lock = threading.Lock()


def subscribe_resource(uri: str, client_id: str) -> dict[str, Any]:
    with _subscription_lock:
        if uri not in _resource_subscriptions:
            _resource_subscriptions[uri] = []
        if client_id not in _resource_subscriptions[uri]:
            _resource_subscriptions[uri].append(client_id)
    return {"subscribed": True, "uri": uri, "client_id": client_id}


def unsubscribe_resource(uri: str, client_id: str) -> dict[str, Any]:
    with _subscription_lock:
        if uri in _resource_subscriptions:
            _resource_subscriptions[uri] = [
                c for c in _resource_subscriptions[uri] if c != client_id
            ]
            if not _resource_subscriptions[uri]:
                del _resource_subscriptions[uri]
    return {"unsubscribed": True, "uri": uri, "client_id": client_id}


def get_subscriptions(uri: str | None = None) -> dict[str, Any]:
    with _subscription_lock:
        if uri:
            subscribers = list(_resource_subscriptions.get(uri, []))
            return {"uri": uri, "subscribers": subscribers, "count": len(subscribers)}
        return {
            "subscriptions": {k: list(v) for k, v in _resource_subscriptions.items()},
            "total_uris": len(_resource_subscriptions),
        }


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

    @mcp.resource("xuansto://agents/{name}")
    def agent_by_name(name: str) -> str:
        try:
            if AGENTS_DIR.exists():
                for agent_file in AGENTS_DIR.rglob(f"{name}.md"):
                    if agent_file.is_file():
                        return agent_file.read_text(encoding="utf-8")
            return json.dumps({"status": "not_found", "name": name}, ensure_ascii=False, indent=2)
        except Exception as e:
            return _degraded_resource(f"xuansto://agents/{name}", str(e))

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

            phase_transition_history: list[dict[str, Any]] = []
            performance_metrics: dict[str, Any] = {
                "total_tokens_consumed": 0,
                "avg_phase_transition_ms": 0,
                "resource_load_count": 0,
            }
            try:
                from ..tools.resource_load_status import (  # noqa: I001
                    _TRANSITION_HISTORY as _TRANS_HIST,
                    _TOKEN_METRICS as _TOK_METRICS,
                    _TOKEN_METRICS_LOCK as _TOK_LOCK,
                    _cache_lock as _rsrc_cache_lock,
                )
                with _rsrc_cache_lock:
                    phase_transition_history = list(_TRANS_HIST[-20:])
                with _TOK_LOCK:
                    total_tokens = sum(
                        m.get("total_input_tokens", 0) + m.get("total_output_tokens", 0)
                        for m in _TOK_METRICS.values()
                    )
                    resource_load_count = sum(
                        m.get("call_count", 0) for m in _TOK_METRICS.values()
                    )
                transition_durations: list[float] = []
                for t in phase_transition_history:
                    started = t.get("started_at")
                    completed = t.get("completed_at")
                    if started and completed:
                        try:
                            from datetime import datetime as _dt
                            s = _dt.fromisoformat(started).timestamp()
                            c = _dt.fromisoformat(completed).timestamp()
                            transition_durations.append((c - s) * 1000)
                        except (ValueError, OSError):
                            pass
                avg_transition_ms = (
                    sum(transition_durations) / len(transition_durations)
                    if transition_durations
                    else 0
                )
                performance_metrics = {
                    "total_tokens_consumed": total_tokens,
                    "avg_phase_transition_ms": round(avg_transition_ms, 2),
                    "resource_load_count": resource_load_count,
                }
            except Exception:
                pass

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
                "phase_transition_history": phase_transition_history,
                "performance_metrics": performance_metrics,
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
                with contextlib.suppress(json.JSONDecodeError, OSError):
                    tool_metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
            if degr_path.exists():
                with contextlib.suppress(json.JSONDecodeError, OSError):
                    degradation_stats = json.loads(degr_path.read_text(encoding="utf-8"))
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

    @mcp.resource("xuansto://skill/config")
    def skill_config_unified() -> str:
        try:
            config_path = _resolve_skill_file(".skill-config.yaml")
            if config_path.exists():
                return config_path.read_text(encoding="utf-8")
            return json.dumps({"status": "not_found", "message": "配置文件不存在"}, ensure_ascii=False, indent=2)
        except Exception as e:
            return _degraded_resource("xuansto://skill/config", str(e))

    @mcp.resource("xuansto://skill/constraints")
    def skill_constraints() -> str:
        try:
            constraints_path = _resolve_skill_file("constraints.md")
            if constraints_path.exists():
                return constraints_path.read_text(encoding="utf-8")
            constraints = {
                "max_retries": 3,
                "timeout_seconds": 30,
                "chain_timeout_seconds": 120,
                "max_chain_retries": 2,
            }
            return json.dumps(constraints, ensure_ascii=False, indent=2)
        except Exception as e:
            return _degraded_resource("xuansto://skill/constraints", str(e))

    @mcp.resource("xuansto://agents/registry")
    def agents_registry() -> str:
        try:
            ref_path = REFERENCES_DIR / "agent-registry.md"
            if ref_path.exists():
                return ref_path.read_text(encoding="utf-8")
            agents: list[dict[str, Any]] = []
            if AGENTS_DIR.exists():
                for agent_file in sorted(AGENTS_DIR.rglob("*.md")):
                    agents.append({
                        "name": agent_file.stem,
                        "layer": agent_file.parent.name,
                    })
            return json.dumps({"agents": agents, "total": len(agents)}, ensure_ascii=False, indent=2)
        except Exception as e:
            return _degraded_resource("xuansto://agents/registry", str(e))

    @mcp.resource("xuansto://gates/definitions")
    def gates_definitions() -> str:
        try:
            ref_path = REFERENCES_DIR / "quality-gates.md"
            if ref_path.exists():
                return ref_path.read_text(encoding="utf-8")
            from ..core.config import GATE_SCRIPTS_MAP
            gates = {gate_id: {"script": script} for gate_id, script in GATE_SCRIPTS_MAP.items()}
            return json.dumps({"gates": gates}, ensure_ascii=False, indent=2)
        except Exception as e:
            return _degraded_resource("xuansto://gates/definitions", str(e))

    @mcp.resource("xuansto://workflows/definitions")
    def workflows_definitions() -> str:
        try:
            ref_path = REFERENCES_DIR / "workflow-phases.md"
            if ref_path.exists():
                return ref_path.read_text(encoding="utf-8")
            from ..core.config import WORKFLOWS_DIR
            workflows: list[dict[str, Any]] = []
            if WORKFLOWS_DIR.exists():
                for wf_file in sorted(WORKFLOWS_DIR.glob("*.md")):
                    workflows.append({"name": wf_file.stem, "path": str(wf_file.relative_to(WORKFLOWS_DIR))})
            return json.dumps({"workflows": workflows}, ensure_ascii=False, indent=2)
        except Exception as e:
            return _degraded_resource("xuansto://workflows/definitions", str(e))

    @mcp.resource("xuansto://hooks/definitions")
    def hooks_definitions() -> str:
        try:
            if HOOKS_PATH.exists():
                return HOOKS_PATH.read_text(encoding="utf-8")
            from ..core.config import HOOK_SCRIPTS_MAP
            hooks = {hook_id: {"script": script} for hook_id, script in HOOK_SCRIPTS_MAP.items()}
            return json.dumps({"hooks": hooks}, ensure_ascii=False, indent=2)
        except Exception as e:
            return _degraded_resource("xuansto://hooks/definitions", str(e))

    @mcp.resource("xuansto://knowledge/status")
    def knowledge_status() -> str:
        try:
            status: dict[str, Any] = {
                "knowledge_dir_exists": KNOWLEDGE_DIR.exists(),
                "db_exists": KNOWLEDGE_DB_PATH.exists(),
                "chroma_exists": KNOWLEDGE_CHROMA_PATH.exists(),
            }
            if KNOWLEDGE_DB_PATH.exists():
                try:
                    import sqlite3
                    conn = sqlite3.connect(str(KNOWLEDGE_DB_PATH))
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM knowledge_entries WHERE deleted_at IS NULL")
                    status["db_entry_count"] = cursor.fetchone()[0]
                    conn.close()
                except Exception:
                    status["db_entry_count"] = -1
            if KNOWLEDGE_CHROMA_PATH.exists():
                try:
                    import chromadb
                    client = chromadb.PersistentClient(path=str(KNOWLEDGE_CHROMA_PATH))
                    collection = client.get_or_create_collection("knowledge")
                    status["chroma_entry_count"] = collection.count()
                except Exception:
                    status["chroma_entry_count"] = -1
            status["timestamp"] = time.time()
            return json.dumps(status, ensure_ascii=False, indent=2)
        except Exception as e:
            return _degraded_resource("xuansto://knowledge/status", str(e))

    @mcp.resource("xuansto://knowledge/stats")
    def knowledge_stats() -> str:
        try:
            stats: dict[str, Any] = {
                "knowledge_dir_exists": KNOWLEDGE_DIR.exists(),
                "db_exists": KNOWLEDGE_DB_PATH.exists(),
                "chroma_exists": KNOWLEDGE_CHROMA_PATH.exists(),
            }
            if KNOWLEDGE_DB_PATH.exists():
                try:
                    import sqlite3
                    conn = sqlite3.connect(str(KNOWLEDGE_DB_PATH))
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM knowledge_entries WHERE deleted_at IS NULL")
                    stats["db_entry_count"] = cursor.fetchone()[0]
                    cursor.execute("SELECT scope, COUNT(*) FROM knowledge_entries WHERE deleted_at IS NULL GROUP BY scope")
                    stats["by_scope"] = dict(cursor.fetchall())
                    conn.close()
                except Exception:
                    stats["db_entry_count"] = -1
            if KNOWLEDGE_CHROMA_PATH.exists():
                try:
                    import chromadb
                    client = chromadb.PersistentClient(path=str(KNOWLEDGE_CHROMA_PATH))
                    collection = client.get_or_create_collection("knowledge")
                    stats["chroma_entry_count"] = collection.count()
                except Exception:
                    stats["chroma_entry_count"] = -1
            stats["timestamp"] = time.time()
            return json.dumps(stats, ensure_ascii=False, indent=2)
        except Exception as e:
            return _degraded_resource("xuansto://knowledge/stats", str(e))

    @mcp.resource("xuansto://templates/index")
    def templates_index() -> str:
        try:
            templates: list[dict[str, Any]] = []
            if TEMPLATES_DIR.exists():
                for tmpl_file in sorted(TEMPLATES_DIR.glob("*.md")):
                    templates.append({"name": tmpl_file.stem, "filename": tmpl_file.name})
            return json.dumps({"templates": templates, "total": len(templates)}, ensure_ascii=False, indent=2)
        except Exception as e:
            return _degraded_resource("xuansto://templates/index", str(e))

    @mcp.resource("xuansto://commands/routes")
    def commands_routes() -> str:
        try:
            routes: list[dict[str, Any]] = []
            if COMMANDS_DIR.exists():
                for cmd_file in sorted(COMMANDS_DIR.rglob("*.md")):
                    routes.append({
                        "name": cmd_file.stem,
                        "path": str(cmd_file.relative_to(COMMANDS_DIR)),
                    })
            return json.dumps({"routes": routes, "total": len(routes)}, ensure_ascii=False, indent=2)
        except Exception as e:
            return _degraded_resource("xuansto://commands/routes", str(e))

    @mcp.resource("xuansto://session/state")
    def session_state() -> str:
        try:
            from ..core.database import load_state
            states = load_state("session_states")
            if states:
                latest = states[-1]
                return json.dumps(latest, ensure_ascii=False, indent=2)
            SESSION_DIR.mkdir(parents=True, exist_ok=True)
            sessions = sorted(SESSION_DIR.glob("session-*.md"), reverse=True)
            if sessions:
                return sessions[0].read_text(encoding="utf-8")
            return json.dumps({"status": "no_active_session"}, ensure_ascii=False, indent=2)
        except Exception as e:
            return _degraded_resource("xuansto://session/state", str(e))

    @mcp.resource("xuansto://health/status")
    def health_status() -> str:
        try:
            from ..core.degradation import get_degradation_manager
            manager = get_degradation_manager()
            degr_status = manager.get_status()
            health: dict[str, Any] = {
                "status": "healthy" if degr_status.get("overall_level") == "L1_NORMAL" else "degraded",
                "degradation_level": degr_status.get("overall_level", "unknown"),
                "components": {},
                "timestamp": time.time(),
            }
            for comp_name, comp_data in degr_status.get("components", {}).items():
                health["components"][comp_name] = {
                    "level": comp_data.get("level", "unknown"),
                    "healthy": comp_data.get("last_check_healthy", False),
                }
            return json.dumps(health, ensure_ascii=False, indent=2)
        except Exception as e:
            return _degraded_resource("xuansto://health/status", str(e))

    @mcp.resource("xuansto://audit/log")
    def audit_log() -> str:
        try:
            from ..core.audit_logger import get_audit_logger
            logger = get_audit_logger()
            entries = logger.query(limit=50)
            return json.dumps({"entries": entries, "count": len(entries)}, ensure_ascii=False, indent=2)
        except Exception as e:
            return _degraded_resource("xuansto://audit/log", str(e))

    @mcp.resource("xuansto://decisions/latest")
    def decisions_latest() -> str:
        try:
            from ..tools.decision_log import _get_connection, _row_to_dict
            conn = _get_connection()
            try:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM decisions ORDER BY created_at DESC LIMIT 10"
                )
                rows = cursor.fetchall()
                if not rows:
                    return "# 无决策记录"
                lines = ["# 最近决策记录\n"]
                for row in rows:
                    d = _row_to_dict(row)
                    lines.append(f"## {d.get('id', '')}: {d.get('title', '')}\n")
                    lines.append(f"- **状态**: {d.get('status', 'proposed')}")
                    lines.append(f"- **上下文**: {d.get('context', '')}")
                    lines.append(f"- **决策**: {d.get('decision', '')}")
                    lines.append(f"- **理由**: {d.get('rationale', '')}")
                    alts = d.get("alternatives", [])
                    if alts:
                        lines.append("- **备选方案**:")
                        for alt in alts:
                            lines.append(f"  - {alt}")
                    lines.append(f"- **创建时间**: {d.get('created_at', '')}")
                    lines.append(f"- **更新时间**: {d.get('updated_at', '')}")
                    lines.append("")
                return "\n".join(lines)
            finally:
                conn.close()
        except Exception as e:
            return _degraded_resource("xuansto://decisions/latest", str(e))

    @mcp.resource("xuansto://workflows/active")
    def workflows_active() -> str:
        try:
            from ..core.database import load_workflow_states
            workflows = load_workflow_states(status="active")
            if not workflows:
                return "# 无活跃工作流"
            lines = ["# 当前活跃的工作流实例\n"]
            for wf in workflows:
                lines.append(f"## {wf.get('workflow_id', '')}\n")
                lines.append(f"- **类型**: {wf.get('workflow_type', '')}")
                lines.append(f"- **当前阶段**: {wf.get('current_phase', 0)}")
                lines.append(f"- **项目路径**: {wf.get('project_path', '') or '未指定'}")
                lines.append(f"- **状态**: {wf.get('status', 'active')}")
                completed = wf.get("completed_phases_json", [])
                if isinstance(completed, str):
                    with contextlib.suppress(json.JSONDecodeError):
                        completed = json.loads(completed)
                if completed:
                    lines.append(f"- **已完成阶段**: {', '.join(str(p) for p in completed)}")
                tasks = wf.get("tasks_json", {})
                if isinstance(tasks, str):
                    with contextlib.suppress(json.JSONDecodeError):
                        tasks = json.loads(tasks)
                if tasks:
                    lines.append(f"- **任务数**: {len(tasks) if isinstance(tasks, list) else len(tasks.keys())}")
                decisions = wf.get("decisions_json", {})
                if isinstance(decisions, str):
                    with contextlib.suppress(json.JSONDecodeError):
                        decisions = json.loads(decisions)
                if decisions:
                    lines.append(f"- **决策数**: {len(decisions) if isinstance(decisions, list) else len(decisions.keys())}")
                created_at = wf.get("created_at")
                if created_at:
                    lines.append(f"- **创建时间**: {created_at}")
                updated_at = wf.get("updated_at")
                if updated_at:
                    lines.append(f"- **更新时间**: {updated_at}")
                lines.append("")
            return "\n".join(lines)
        except Exception as e:
            return _degraded_resource("xuansto://workflows/active", str(e))
