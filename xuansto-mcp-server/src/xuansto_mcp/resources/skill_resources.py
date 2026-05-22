from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from ..core.config import SKILL_ROOT, REFERENCES_DIR, TEMPLATES_DIR, SESSION_DIR, WORK_DIR

# URI-to-filename mapping convention:
# Each MCP Resource URI path segment (after the category prefix) must match
# the corresponding data filename exactly. For example:
#   URI  "xuansto://references/quality-gates"  -> file "quality-gates.md"
#   URI  "xuansto://references/workflow-phases" -> file "workflow-phases.md"
# This ensures discoverability and avoids confusion between URI paths and
# the actual files they resolve to.  Do NOT use different names for the
# URI segment and the file it reads.


def register(mcp: FastMCP) -> None:
    @mcp.resource("xuansto://config/skill")
    def skill_config() -> str:
        config_path = SKILL_ROOT / ".skill-config.yaml"
        if config_path.exists():
            return config_path.read_text(encoding="utf-8")
        return "# 配置文件不存在"

    @mcp.resource("xuansto://references/quality-gates")
    def quality_gates() -> str:
        ref_path = REFERENCES_DIR / "quality-gates.md"
        if ref_path.exists():
            return ref_path.read_text(encoding="utf-8")
        return "# 质量门禁文档不存在"

    @mcp.resource("xuansto://references/agent-registry")
    def agent_registry() -> str:
        ref_path = REFERENCES_DIR / "agent-registry.md"
        if ref_path.exists():
            return ref_path.read_text(encoding="utf-8")
        return "# Agent注册表不存在"

    @mcp.resource("xuansto://references/workflow-phases")
    def workflow_phases() -> str:
        ref_path = REFERENCES_DIR / "workflow-phases.md"
        if ref_path.exists():
            return ref_path.read_text(encoding="utf-8")
        return "# 工作流定义不存在"

    @mcp.resource("xuansto://templates/{name}")
    def template(name: str) -> str:
        if "/" in name or "\\" in name or ".." in name:
            return f"Error: invalid template name '{name}'"
        template_path = TEMPLATES_DIR / f"{name}.md"
        try:
            if template_path.resolve().is_relative_to(TEMPLATES_DIR.resolve()) and template_path.exists():
                return template_path.read_text(encoding="utf-8")
        except (OSError, ValueError):
            pass
        return f"Template '{name}' not found"

    @mcp.resource("xuansto://sessions/latest")
    def latest_session() -> str:
        SESSION_DIR.mkdir(parents=True, exist_ok=True)
        sessions = sorted(SESSION_DIR.glob("session-*.md"), reverse=True)
        if sessions:
            return sessions[0].read_text(encoding="utf-8")
        return "# 无会话记录"

    @mcp.resource("xuansto://loading/status")
    def loading_status() -> str:
        state_file = WORK_DIR / "resource_state.json"
        loaded_resources: list[str] = []
        loading_progress: dict[str, Any] = {}
        current_phase = "skeleton"

        if state_file.exists():
            try:
                data = json.loads(state_file.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    loaded_resources = data
                elif isinstance(data, dict):
                    loaded_resources = data.get("loaded", [])
                    loading_progress = data.get("progress", {})
                    current_phase = data.get("phase", current_phase)
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
            "available_references": available_refs,
            "available_functions": available_functions,
            "loading_progress": loading_progress,
            "disclosure_note": disclosure_note,
            "timestamp": time.time(),
        }
        return json.dumps(status, ensure_ascii=False, indent=2)
