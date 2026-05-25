import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class LoadPhase(str, Enum):
    SKELETON = "skeleton"
    FUNCTIONAL = "functional"
    ENHANCED = "enhanced"
    FULL = "full"

    @property
    def index(self) -> int:
        return _PHASE_ORDER.index(self)


_PHASE_ORDER = [LoadPhase.SKELETON, LoadPhase.FUNCTIONAL, LoadPhase.ENHANCED, LoadPhase.FULL]

_PHASE_BUDGETS = {
    LoadPhase.SKELETON: 2000,
    LoadPhase.FUNCTIONAL: 5000,
    LoadPhase.ENHANCED: 10000,
    LoadPhase.FULL: 20000,
}

_PHASE_RESOURCE_PRIORITY = {
    LoadPhase.SKELETON: ["P0_must"],
    LoadPhase.FUNCTIONAL: ["P0_must", "P1_important"],
    LoadPhase.ENHANCED: ["P0_must", "P1_important", "P2_enhanced"],
    LoadPhase.FULL: ["P0_must", "P1_important", "P2_enhanced", "P3_optional"],
}

_PHASE_AVAILABLE_RESOURCES = {
    LoadPhase.SKELETON: [
        "skill-config", "command-list", "mcp-dependency", "core-constraints",
    ],
    LoadPhase.FUNCTIONAL: [
        "skill-config", "command-list", "mcp-dependency", "core-constraints",
        "execution-entry", "workflow-phase-overview", "command-route-compact", "core-agent-index",
        "gate-check",
    ],
    LoadPhase.ENHANCED: [
        "skill-config", "command-list", "mcp-dependency", "core-constraints",
        "execution-entry", "workflow-phase-overview", "command-route-compact", "core-agent-index",
        "gate-check",
        "command-route-full", "agent-registry-full", "reference-documents", "mcp-tool-summary",
        "knowledge-search",
    ],
    LoadPhase.FULL: [
        "skill-config", "command-list", "mcp-dependency", "core-constraints",
        "execution-entry", "workflow-phase-overview", "command-route-compact", "core-agent-index",
        "gate-check",
        "command-route-full", "agent-registry-full", "reference-documents", "mcp-tool-summary",
        "knowledge-search",
        "hook-system", "model-routing", "key-rules", "script-set", "disclosure-resources",
        "eval-config",
    ],
}

_PHASE_COMMANDS = {
    LoadPhase.SKELETON: [],
    LoadPhase.FUNCTIONAL: [
        "/init", "/brainstorm", "/clarify", "/plan", "/spec", "/design",
        "/design-system", "/implement", "/test", "/review", "/audit",
        "/fix", "/accept", "/simplify", "/refactor", "/deploy", "/build",
        "/build-desktop", "/release-desktop", "/sprint", "/learn",
        "/execute-plan", "/loop", "/cancel-loop", "/agent-status",
        "/status", "/rollback", "/sdd-tdd-medium", "/sdd-tdd-fast",
        "/decision", "/budget",
    ],
    LoadPhase.ENHANCED: [
        "/init", "/brainstorm", "/clarify", "/plan", "/spec", "/design",
        "/design-system", "/implement", "/test", "/review", "/audit",
        "/fix", "/accept", "/simplify", "/refactor", "/deploy", "/build",
        "/build-desktop", "/release-desktop", "/sprint", "/learn",
        "/execute-plan", "/loop", "/cancel-loop", "/agent-status",
        "/status", "/rollback", "/sdd-tdd-medium", "/sdd-tdd-fast",
        "/decision", "/budget",
    ],
    LoadPhase.FULL: [
        "/init", "/brainstorm", "/clarify", "/plan", "/spec", "/design",
        "/design-system", "/implement", "/test", "/review", "/audit",
        "/fix", "/accept", "/simplify", "/refactor", "/deploy", "/build",
        "/build-desktop", "/release-desktop", "/sprint", "/learn",
        "/execute-plan", "/loop", "/cancel-loop", "/agent-status",
        "/status", "/rollback", "/sdd-tdd-medium", "/sdd-tdd-fast",
        "/decision", "/budget",
    ],
}

_DISCLOSURE_NOTES = {
    LoadPhase.SKELETON: "当前处于骨架阶段，仅核心元数据可用。命令步骤、工作流详情、Agent详情、参考文档不可用。请执行任意命令以推进到功能阶段。",
    LoadPhase.FUNCTIONAL: "当前处于功能阶段，命令执行和工作流概览可用。完整命令路由(含降级策略)、完整Agent注册表、参考文档、知识检索不可用。可通过 resource_load_status(preload) 推进到增强阶段。",
    LoadPhase.ENHANCED: "当前处于增强阶段，完整命令路由、Agent注册表、参考文档和知识检索可用。Hook系统详情、模型路由详情、关键规则完整说明不可用。可通过 resource_load_status(preload) 推进到完整阶段。",
    LoadPhase.FULL: "当前处于完整阶段，全部功能可用。",
}

_UPGRADE_HINTS = {
    LoadPhase.SKELETON: "执行任意命令(如 /init, /sprint)可推进到功能阶段，加载命令详细步骤和工作流定义。",
    LoadPhase.FUNCTIONAL: "请求参考文档或查询Agent详情可推进到增强阶段，加载完整路由表和Agent注册表。",
    LoadPhase.ENHANCED: "执行深度分析(/audit)或桌面构建(/build-desktop)可推进到完整阶段，加载Hook系统和模型路由。",
    LoadPhase.FULL: "",
}

_RESOURCE_PRIORITY_MAP = {
    "P0_must": 0,
    "P1_important": 1,
    "P2_enhanced": 2,
    "P3_optional": 3,
}

COMMAND_PHASE_MAP: dict[str, LoadPhase] = {
    "/init": LoadPhase.FUNCTIONAL,
    "/sprint": LoadPhase.FUNCTIONAL,
    "/implement": LoadPhase.FUNCTIONAL,
    "/audit": LoadPhase.ENHANCED,
    "/refactor": LoadPhase.ENHANCED,
    "/loop": LoadPhase.ENHANCED,
    "/build-desktop": LoadPhase.FULL,
    "/deploy": LoadPhase.FULL,
}

PHASE_SKILL_MAP: dict[int, LoadPhase] = {
    0: LoadPhase.SKELETON,
    1: LoadPhase.FUNCTIONAL,
    2: LoadPhase.ENHANCED,
    3: LoadPhase.FULL,
}


@dataclass
class LoadingState:
    current_phase: LoadPhase = LoadPhase.SKELETON
    loaded_resources: list[str] = field(default_factory=list)
    progress: dict[str, dict[str, Any]] = field(default_factory=dict)
    last_updated: float = field(default_factory=time.time)
    degraded: bool = False
    degraded_from: Optional[str] = None

    def to_dict(self) -> dict:
        result = {
            "phase": self.current_phase.value,
            "loaded": self.loaded_resources,
            "progress": self.progress,
            "last_updated": self.last_updated,
        }
        if self.degraded:
            result["degraded"] = True
            result["degraded_from"] = self.degraded_from
        return result

    @classmethod
    def from_dict(cls, data: dict) -> "LoadingState":
        if data is None:
            return cls()
        phase_value = data.get("phase", "skeleton")
        if isinstance(phase_value, int):
            phase = _PHASE_ORDER[phase_value] if phase_value < len(_PHASE_ORDER) else LoadPhase.SKELETON
        elif isinstance(phase_value, str):
            try:
                phase = LoadPhase(phase_value)
            except ValueError:
                phase = LoadPhase.SKELETON
        else:
            phase = LoadPhase.SKELETON

        loaded = data.get("loaded", [])
        if isinstance(loaded, list) and all(isinstance(x, str) for x in loaded):
            pass
        else:
            loaded = []

        progress = data.get("progress", {})
        if not isinstance(progress, dict):
            progress = {}

        last_updated = data.get("last_updated", time.time())
        if not isinstance(last_updated, (int, float)):
            last_updated = time.time()

        degraded = bool(data.get("degraded", False))
        degraded_from = data.get("degraded_from")
        if degraded_from is not None and not isinstance(degraded_from, str):
            degraded_from = None

        return cls(
            current_phase=phase,
            loaded_resources=loaded,
            progress=progress,
            last_updated=last_updated,
            degraded=degraded,
            degraded_from=degraded_from,
        )


class ProgressiveLoader:
    def __init__(self, initial_state: Optional[LoadingState] = None):
        self._state = initial_state or LoadingState()
        self._last_activity_time: float = time.time()

    def get_current_phase(self) -> LoadPhase:
        return self._state.current_phase

    def advance_phase(self, target_phase: LoadPhase) -> LoadingState:
        if isinstance(target_phase, str):
            try:
                target_phase = LoadPhase(target_phase)
            except ValueError:
                return self._state

        if target_phase.index <= self._state.current_phase.index:
            return self._state

        now = time.time()
        self._state.current_phase = target_phase
        self._state.degraded = False
        self._state.degraded_from = None

        new_resources = _PHASE_AVAILABLE_RESOURCES.get(target_phase, [])
        for res in new_resources:
            if res not in self._state.loaded_resources:
                self._state.loaded_resources.append(res)
                self._state.progress[res] = {
                    "progress": 1.0,
                    "loaded_at": now,
                }

        self._state.last_updated = now
        self._last_activity_time = now
        return self._state

    def can_access(self, resource_priority: str) -> bool:
        priority_level = _RESOURCE_PRIORITY_MAP.get(resource_priority, 999)
        allowed_priorities = _PHASE_RESOURCE_PRIORITY.get(self._state.current_phase, [])
        allowed_levels = [_RESOURCE_PRIORITY_MAP.get(p, 999) for p in allowed_priorities]
        return priority_level <= max(allowed_levels) if allowed_levels else False

    def get_available_resources(self) -> list[str]:
        return list(_PHASE_AVAILABLE_RESOURCES.get(self._state.current_phase, []))

    def get_disclosure_note(self) -> str:
        return _DISCLOSURE_NOTES.get(self._state.current_phase, "")

    def get_upgrade_hint(self) -> str:
        return _UPGRADE_HINTS.get(self._state.current_phase, "")

    def get_available_commands(self) -> list[str]:
        return list(_PHASE_COMMANDS.get(self._state.current_phase, []))

    def check_token_budget(self, current_usage: int, total_budget: int) -> bool:
        if total_budget <= 0:
            return True

        ratio = current_usage / total_budget
        if ratio > 0.95:
            return True
        if ratio > 0.80 and self._state.current_phase == LoadPhase.FULL:
            return True
        return False

    def degrade_phase(self) -> LoadingState:
        now = time.time()
        current = self._state.current_phase

        if current == LoadPhase.FULL:
            self._state.degraded = True
            self._state.degraded_from = current.value
            self._state.current_phase = LoadPhase.ENHANCED
            self._remove_resources_for_phase(LoadPhase.FULL)
        elif current == LoadPhase.ENHANCED:
            self._state.degraded = True
            self._state.degraded_from = current.value
            self._state.current_phase = LoadPhase.FUNCTIONAL
            self._remove_resources_for_phase(LoadPhase.ENHANCED)
        elif current == LoadPhase.FUNCTIONAL:
            idle_seconds = now - self._last_activity_time
            if idle_seconds > 300:
                self._state.degraded = True
                self._state.degraded_from = current.value
                self._state.current_phase = LoadPhase.SKELETON
                self._remove_resources_for_phase(LoadPhase.FUNCTIONAL)
            else:
                return self._state
        else:
            return self._state

        self._state.last_updated = now
        return self._state

    def _remove_resources_for_phase(self, phase: LoadPhase):
        phase_resources = set(_PHASE_AVAILABLE_RESOURCES.get(phase, []))
        lower_resources = set()
        for p in _PHASE_ORDER:
            if p.index < phase.index:
                lower_resources.update(_PHASE_AVAILABLE_RESOURCES.get(p, []))

        to_remove = phase_resources - lower_resources
        self._state.loaded_resources = [
            r for r in self._state.loaded_resources if r not in to_remove
        ]
        for r in to_remove:
            self._state.progress.pop(r, None)

    def record_activity(self):
        self._last_activity_time = time.time()

    def get_phase_for_command(self, command: str) -> Optional[LoadPhase]:
        return COMMAND_PHASE_MAP.get(command)

    def sync_from_skill_phase(self, skill_phase: int) -> LoadingState:
        target = PHASE_SKILL_MAP.get(skill_phase)
        if target is None:
            return self._state
        if target.index > self._state.current_phase.index:
            return self.advance_phase(target)
        return self._state

    def to_dict(self) -> dict:
        return self._state.to_dict()

    @classmethod
    def from_dict(cls, data: dict) -> "ProgressiveLoader":
        state = LoadingState.from_dict(data)
        return cls(initial_state=state)
