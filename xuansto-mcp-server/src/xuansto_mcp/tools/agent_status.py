from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from ..core.config import AGENTS_DIR, DATA_DIR, REFERENCES_DIR
from ..core.errors import ERR_VALIDATION, make_error_response, make_success_response
from ..core.logging_config import get_logger
from ..core.validator import validate_input
from ..models.schemas import AgentStatusInput

logger = get_logger("agent_status")

PHASE_AGENT_MAP: dict[int, list[str]] = {
    0: ["Orchestrator", "Design System Generator", "UI Designer"],
    1: ["Product Manager", "Brainstorming Facilitator", "Knowledge Manager"],
    2: ["System Architect", "Technical Writer", "Knowledge Manager"],
    3: ["Test Architect", "Unit Tester"],
    4: ["Backend Developer", "Frontend Developer", "Fullstack Developer", "Subagent Dispatcher", "Task Coordinator"],
    5: ["Security Auditor", "AI Penetration Tester", "E2E Tester", "Integration Tester"],
    6: ["QA Engineer", "UX Designer", "Compliance Officer"],
    7: ["Refactoring Specialist", "Code Reviewer", "History Analyzer"],
    8: ["Build-Release Engineer", "CI/CD Specialist", "Runtime Supervisor"],
}

_REGISTRY_YAML_PATH = AGENTS_DIR / "registry.yaml"

_registry_cache: dict[str, Any] = {}
_registry_cache_mtime: float = 0.0


def _load_registry_yaml() -> dict[str, Any]:
    global _registry_cache, _registry_cache_mtime
    if not _REGISTRY_YAML_PATH.exists():
        return {}
    try:
        mtime = _REGISTRY_YAML_PATH.stat().st_mtime
        if mtime == _registry_cache_mtime and _registry_cache:
            return _registry_cache
        import yaml
        raw = yaml.safe_load(_REGISTRY_YAML_PATH.read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            _registry_cache = raw
            _registry_cache_mtime = mtime
            return raw
    except Exception:
        pass
    return {}


def _get_agent_phase_map() -> dict[str, int]:
    registry = _load_registry_yaml()
    phase_map: dict[str, int] = {}
    for layer in registry.get("layers", []):
        for agent in layer.get("agents", []):
            name = agent.get("name", "")
            phase_val = agent.get("phase", 2)
            if name:
                phase_map[name] = phase_val
    return phase_map

def _parse_agent_registry(registry_path: Path) -> list[dict[str, Any]]:
    phase_map = _get_agent_phase_map()
    if not registry_path.exists():
        return []
    content = registry_path.read_text(encoding="utf-8")
    agents = []
    current_layer = ""
    for line in content.splitlines():
        layer_match = re.match(r"^#+\s*(.+层|.+Layer)", line)
        if layer_match:
            current_layer = layer_match.group(1).strip()
            continue
        agent_match = re.match(r"^\s*[-*]\s*\*\*(.+?)\*\*", line)
        if agent_match:
            name = agent_match.group(1).strip()
            agents.append({
                "name": name,
                "layer": current_layer,
                "phase": phase_map.get(name, 2),
            })
    return agents

def _get_agent_detail(agent_name: str, agents_dir: Path) -> dict[str, Any]:
    for subdir in agents_dir.iterdir():
        if subdir.is_dir():
            agent_file = subdir / f"{agent_name.lower().replace(' ', '-')}.md"
            if agent_file.exists():
                content = agent_file.read_text(encoding="utf-8")
                return {"name": agent_name, "file": str(agent_file), "content_length": len(content)}
    detail_dir = REFERENCES_DIR / "agent-details"
    if detail_dir.exists():
        for f in detail_dir.glob("*.md"):
            if agent_name.lower().replace(" ", "-") in f.stem.lower():
                content = f.read_text(encoding="utf-8")
                return {"name": agent_name, "file": str(f), "content_length": len(content)}
    return {"name": agent_name, "detail": "未找到详细定义文件"}


_MERGE_GROUPS: list[dict[str, Any]] = [
    {
        "name": "Developer",
        "absorbs": ["Backend Developer", "Frontend Developer", "Fullstack Developer", "Subagent Dispatcher", "Task Coordinator"],
        "capabilities": ["code_generation", "code_review", "implementation", "task_coordination"],
    },
    {
        "name": "Tester",
        "absorbs": ["Test Architect", "Unit Tester", "E2E Tester", "Integration Tester"],
        "capabilities": ["test_design", "test_execution", "test_automation", "coverage_analysis"],
    },
    {
        "name": "Security Specialist",
        "absorbs": ["Security Auditor", "AI Penetration Tester"],
        "capabilities": ["security_audit", "penetration_testing", "vulnerability_assessment"],
    },
    {
        "name": "Quality Specialist",
        "absorbs": ["QA Engineer", "Compliance Officer", "Code Reviewer"],
        "capabilities": ["quality_assurance", "compliance", "code_review"],
    },
    {
        "name": "DevOps Engineer",
        "absorbs": ["Build-Release Engineer", "CI/CD Specialist", "Runtime Supervisor"],
        "capabilities": ["build", "deployment", "ci_cd", "monitoring"],
    },
    {
        "name": "Refactoring Specialist",
        "absorbs": ["Refactoring Specialist", "History Analyzer"],
        "capabilities": ["refactoring", "code_simplification", "history_analysis"],
    },
]


def _evaluate_merge_policy(project_scale: str = "medium") -> dict[str, Any]:
    if project_scale in ("small", "mini"):
        return {
            "merge_recommended": True,
            "merge_groups": [
                {
                    "name": "security_testing_merged",
                    "agents": ["Security Tester", "Penetration Tester"],
                    "merged_into": "Security Tester",
                    "reason": "project_scale_below_medium",
                },
            ],
        }
    return {"merge_recommended": False, "project_scale": project_scale}


def _load_merge_rules_from_yaml() -> list[dict[str, Any]] | None:
    yaml_path = DATA_DIR / "default.yaml"
    if not yaml_path.exists():
        return None
    try:
        import yaml
        raw = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
        if isinstance(raw, dict) and "agent_merge_groups" in raw:
            groups = raw["agent_merge_groups"]
            if isinstance(groups, list):
                return groups
    except Exception:
        pass
    return None


def _merge_agents(project_file_count: int | None = None) -> dict[str, Any]:
    merge_rules = _load_merge_rules_from_yaml()
    groups = merge_rules if merge_rules is not None else _MERGE_GROUPS

    registry = REFERENCES_DIR / "agent-registry.md"
    all_agents = _parse_agent_registry(registry)

    small_project = project_file_count is not None and project_file_count < 20

    merged = []
    absorbed_names: set[str] = set()
    merge_log: list[dict[str, Any]] = []

    for group in groups:
        group_name = group.get("name", "")
        absorbs = group.get("absorbs", [])
        caps = group.get("capabilities", [])
        matched_absorbs = []
        for a in all_agents:
            if a["name"] in absorbs:
                matched_absorbs.append(a["name"])
                absorbed_names.add(a["name"])
        if matched_absorbs:
            merged.append({
                "name": group_name,
                "capabilities": caps,
                "merged_from": matched_absorbs,
                "layer": "merged",
            })
            merge_log.append({
                "target": group_name,
                "absorbed": matched_absorbs,
            })

    remaining = [a for a in all_agents if a["name"] not in absorbed_names]
    final_agents = remaining + merged

    original_count = len(all_agents)
    merged_count = len(final_agents)

    if small_project:
        for group in groups:
            group_name = group.get("name", "")
            absorbs = group.get("absorbs", [])
            for a in list(remaining):
                if a["name"] in absorbs and a not in [x for x in merged if x["name"] == group_name]:
                    pass

    return {
        "action": "merge",
        "original_count": original_count,
        "merged_count": merged_count,
        "reduction": original_count - merged_count,
        "is_small_project": small_project,
        "project_file_count": project_file_count,
        "agents": final_agents,
        "merge_log": merge_log,
        "merge_rules_source": "default.yaml" if merge_rules is not None else "builtin",
    }


def register(mcp: FastMCP) -> None:
    @mcp.tool(
        annotations=ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        )
    )
    async def agent_status(
        action: str,
        phase: int | None = None,
        agent_name: str | None = None,
        capabilities: list[str] | None = None,
        project_file_count: int | None = None,
    ) -> dict[str, Any]:
        """Agent状态查询：列出全部57个Agent、按Phase查询活跃Agent、查询单个Agent详情、按能力匹配Agent、合并Agent(小项目自动从57合并到~20)。返回Agent名称、层级和匹配状态。"""
        validated, err = validate_input(AgentStatusInput, action=action, phase=phase, agent_name=agent_name, capabilities=capabilities, project_file_count=project_file_count)
        if err:
            return err
        logger.info("agent_status called: action=%s", action)
        try:
            if action == "list":
                registry = REFERENCES_DIR / "agent-registry.md"
                agents = _parse_agent_registry(registry)
                if phase is not None:
                    agents = [a for a in agents if a.get("phase", 2) <= phase]
                return make_success_response({"agents": agents, "total": len(agents), "phase_filter": phase})
            elif action == "by_phase":
                if phase is None:
                    return make_error_response(ValueError("by_phase操作需要phase参数(0-8)"), error_code=ERR_VALIDATION)
                phase_agents = PHASE_AGENT_MAP.get(phase, [])
                phase_map = _get_agent_phase_map()
                enriched = [{"name": name, "phase": phase_map.get(name, 2)} for name in phase_agents]
                return make_success_response({"phase": phase, "agents": enriched, "total": len(enriched)})
            elif action == "detail":
                if not agent_name:
                    return make_error_response(ValueError("detail操作需要agent_name参数"), error_code=ERR_VALIDATION)
                detail = _get_agent_detail(agent_name, AGENTS_DIR)
                phase_map = _get_agent_phase_map()
                detail["phase"] = phase_map.get(agent_name, 2)
                return make_success_response(detail)
            elif action == "match":
                if not capabilities:
                    return make_error_response(ValueError("match操作需要capabilities参数"), error_code=ERR_VALIDATION)
                from .agent_manage import _AGENT_INSTANCES, _agents_lock
                required = set(capabilities)
                matches: list[dict[str, Any]] = []
                with _agents_lock:
                    for inst in _AGENT_INSTANCES.values():
                        inst_caps = set(inst.capabilities)
                        overlap = required & inst_caps
                        if overlap:
                            coverage = len(overlap) / len(required) if required else 0.0
                            matches.append({
                                "agent_id": inst.agent_id,
                                "agent_type": inst.agent_type,
                                "capabilities": inst.capabilities,
                                "status": inst.status,
                                "coverage": round(coverage, 2),
                                "matched_capabilities": sorted(overlap),
                                "missing_capabilities": sorted(required - inst_caps),
                            })
                matches.sort(key=lambda x: x["coverage"], reverse=True)
                return make_success_response({
                    "action": "match",
                    "required_capabilities": sorted(required),
                    "matches": matches,
                    "total": len(matches),
                })
            elif action == "merge":
                result = _merge_agents(project_file_count)
                return make_success_response(result)
            elif action == "merge_policy":
                project_scale = "medium"
                if project_file_count is not None:
                    if project_file_count < 20:
                        project_scale = "small"
                    elif project_file_count < 50:
                        project_scale = "medium"
                    else:
                        project_scale = "large"
                policy = _evaluate_merge_policy(project_scale)
                if policy.get("merge_recommended"):
                    logger.info("merge_policy_applied: scale=%s groups=%s", project_scale, [g["name"] for g in policy.get("merge_groups", [])])
                    try:
                        from .decision_log import _log_decision
                        _log_decision(
                            title="Agent合并策略决策",
                            decision=f"项目规模({project_scale})低于medium，推荐合并: {[g['name'] for g in policy.get('merge_groups', [])]}",
                            rationale="project_scale_below_medium",
                        )
                    except Exception:
                        pass
                return make_success_response({"action": "merge_policy", "project_scale": project_scale, **policy})
            else:
                return make_error_response(ValueError(f"未知操作: {action}，支持: list, by_phase, detail, match, merge, merge_policy"), error_code=ERR_VALIDATION)
        except Exception as e:
            logger.error("agent_status error: %s", e)
            return make_error_response(e)
