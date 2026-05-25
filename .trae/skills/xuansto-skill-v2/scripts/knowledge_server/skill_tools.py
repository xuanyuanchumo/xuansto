import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

from .config import make_response, make_error_response, mcp_available
from .degradation import MCPToolFallback
from .progressive_loader import COMMAND_PHASE_MAP, LoadPhase
from .tools import TOOL_REGISTRY, SKILL_TOOL_NAMES, get_skill_tool_definitions
from .tools._shared import _DEFAULT_BUDGET_ALLOCATIONS

logger = logging.getLogger("knowledge-server")

if mcp_available:
    from mcp.types import TextContent

TOOL_COMMAND_MAP: dict[str, str] = {
    "project_init": "/init",
    "workflow_dispatch": "/sprint",
    "skill_analyze": "/audit",
    "security_scan": "/audit",
    "code_simplify": "/refactor",
    "hook_manage": "/loop",
    "knowledge_inject": "/implement",
    "quality_gate_check": "/audit",
    "spec_drift_detect": "/audit",
}


class SkillToolHandler:
    def __init__(self, server=None, fallback=None):
        self.server = server
        self.fallback = fallback or MCPToolFallback()
        self._sessions: Dict[str, dict] = {}
        self._workflows: Dict[str, dict] = {}
        self._decisions: List[dict] = []
        self._token_budget_state: Dict[str, Any] = {
            "total_budget": 150000,
            "used": 0,
            "remaining": 150000,
            "phase_allocations": dict(_DEFAULT_BUDGET_ALLOCATIONS),
            "usage_by_phase": {},
        }
        self._injected_contexts: List[dict] = []
        self._agent_instances: Dict[str, dict] = {}
        self._start_time = datetime.now(timezone.utc)

    def _build_context(self) -> dict:
        return {
            "sessions": self._sessions,
            "workflows": self._workflows,
            "decisions": self._decisions,
            "token_budget_state": self._token_budget_state,
            "injected_contexts": self._injected_contexts,
            "agent_instances": self._agent_instances,
            "start_time": self._start_time,
            "fallback": self.fallback,
        }

    async def handle(self, name: str, arguments: dict):
        if name not in TOOL_REGISTRY:
            return self._fallback_or_error(name, arguments)
        _, handler = TOOL_REGISTRY[name]
        context = self._build_context()
        try:
            result = await handler(arguments, context)
            self._try_advance_phase(name)
            return result
        except Exception as e:
            logger.error("operation=skill_tool_handle, tool=%s, error=%s", name, e)
            fallback_result = self.fallback.call_tool(name, arguments)
            if fallback_result.get("status") != "error":
                return [TextContent(type="text", text=json.dumps(fallback_result, ensure_ascii=False))]
            return [TextContent(type="text", text=json.dumps(make_error_response(
                code="INTERNAL_ERROR",
                message=f"Tool execution failed: {e}",
                details={"tool_name": name, "error": str(e)},
            ), ensure_ascii=False), isError=True)]

    def _try_advance_phase(self, tool_name: str):
        command = TOOL_COMMAND_MAP.get(tool_name)
        if not command:
            return
        target_phase = COMMAND_PHASE_MAP.get(command)
        if not target_phase:
            return
        loader = getattr(self.server, "progressive_loader", None) if self.server else None
        if not loader:
            return
        if target_phase.index > loader.get_current_phase().index:
            loader.advance_phase(target_phase)
            loader.record_activity()

    def _fallback_or_error(self, name: str, arguments: dict):
        fallback_result = self.fallback.call_tool(name, arguments)
        if fallback_result.get("status") != "error":
            return [TextContent(type="text", text=json.dumps(fallback_result, ensure_ascii=False))]
        return [TextContent(type="text", text=json.dumps(make_error_response(
            code="UNKNOWN_TOOL",
            message=f"Unknown tool: {name}",
            details={"tool_name": name},
        ), ensure_ascii=False), isError=True)]
