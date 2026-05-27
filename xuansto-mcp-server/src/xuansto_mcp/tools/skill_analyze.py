from __future__ import annotations

import contextlib
import re
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from ..core.config import REFERENCES_DIR, SCRIPTS_DIR
from ..core.errors import ERR_NOT_FOUND, ERR_VALIDATION, PathNotFoundError, make_error_response, make_success_response
from ..core.logging_config import get_logger
from ..core.validator import validate_input, validate_path_safety
from ..models.schemas import SkillAnalyzeInput

logger = get_logger("skill_analyze")

_EXCLUDED_DIRS = {"node_modules", ".git", "__pycache__", ".venv", "venv", "dist", "build"}

_SOURCE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".c", ".cpp", ".h", ".hpp",
    ".cs", ".go", ".rs", ".rb", ".php", ".swift", ".kt", ".scala", ".sh",
    ".bash", ".ps1", ".html", ".css", ".scss", ".less", ".vue", ".svelte",
    ".sql", ".r", ".m", ".mm", ".lua", ".pl", ".ex", ".exs", ".erl",
    ".dart", ".zig", ".nim", ".toml", ".yaml", ".yml", ".json", ".xml",
    ".md", ".rst", ".txt",
}


def _assess_project_scale(project_path: str) -> dict[str, Any]:
    root = Path(project_path)
    if not root.exists() or not root.is_dir():
        return {
            "file_count": 0,
            "loc_count": 0,
            "scale": "small",
            "recommended_workflow": "sdd-tdd-fast",
            "workflow_phases": 3,
        }

    file_count = 0
    loc_count = 0

    for item in root.rglob("*"):
        if not item.is_file():
            continue
        if any(part in _EXCLUDED_DIRS for part in item.parts):
            continue
        if item.suffix.lower() in _SOURCE_EXTENSIONS:
            file_count += 1
            with contextlib.suppress(Exception):
                loc_count += sum(1 for _ in item.open(encoding="utf-8", errors="ignore"))

    scale_by_files = "small" if file_count < 20 else ("medium" if file_count <= 100 else "large")
    scale_by_loc = "small" if loc_count < 2000 else ("medium" if loc_count <= 20000 else "large")

    scale_rank = {"small": 0, "medium": 1, "large": 2}
    scale = max(scale_by_files, scale_by_loc, key=lambda s: scale_rank[s])

    workflow_map = {
        "small": ("sdd-tdd-fast", 3),
        "medium": ("sdd-tdd-medium", 6),
        "large": ("sdd-tdd-full", 9),
    }
    recommended_workflow, workflow_phases = workflow_map[scale]

    return {
        "file_count": file_count,
        "loc_count": loc_count,
        "scale": scale,
        "recommended_workflow": recommended_workflow,
        "workflow_phases": workflow_phases,
    }


def _parse_yaml_frontmatter(file_path: Path) -> dict[str, Any]:
    if not file_path.exists():
        return {}
    content = file_path.read_text(encoding="utf-8")
    match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return {}
    try:
        import yaml
        return yaml.safe_load(match.group(1)) or {}
    except Exception:
        return {"raw_frontmatter": match.group(1)}


_DEPTH_MAP = {
    "1": 1, "basic": 1,
    "2": 2, "detailed": 2,
    "3": 3, "full": 3, "comprehensive": 3,
}


def _normalize_depth(depth: str | int) -> int:
    if isinstance(depth, int):
        return min(max(depth, 1), 3)
    if isinstance(depth, str) and depth.isdigit():
        return min(max(int(depth), 1), 3)
    return _DEPTH_MAP.get(depth, 1)


def _scan_directory(root: Path, depth_level: int) -> dict[str, Any]:
    structure: dict[str, Any] = {
        "root": str(root),
        "exists": root.exists(),
        "directories": [],
        "files_count": 0,
    }
    if not root.exists() or not root.is_dir():
        return structure
    for item in sorted(root.iterdir()):
        if item.is_dir():
            sub: dict[str, Any] = {"name": item.name, "files_count": 0}
            if depth_level >= 3:
                sub_files = list(item.rglob("*"))
                sub["files_count"] = sum(1 for f in sub_files if f.is_file())
                sub["subdirs"] = [d.name for d in item.iterdir() if d.is_dir()]
            elif depth_level >= 2:
                sub_files = list(item.iterdir())
                sub["files_count"] = sum(1 for f in sub_files if f.is_file())
                sub["subdirs"] = [d.name for d in item.iterdir() if d.is_dir()]
            else:
                sub["files_count"] = sum(1 for f in item.iterdir() if f.is_file())
            structure["directories"].append(sub)
        elif item.is_file():
            structure["files_count"] += 1
    return structure


def _parse_agent_registry(registry_path: Path) -> list[dict[str, Any]]:
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
            agents.append({
                "name": agent_match.group(1).strip(),
                "layer": current_layer,
            })
    return agents


def _scan_script_dependencies(scripts_dir: Path) -> dict[str, Any]:
    if not scripts_dir.exists():
        return {}
    deps: dict[str, Any] = {"total_scripts": 0, "by_type": {}}
    for f in scripts_dir.iterdir():
        if f.is_file() and f.suffix == ".py":
            deps["total_scripts"] += 1
            category = "root"
        elif f.is_dir() and f.name != "__pycache__":
            count = sum(1 for x in f.rglob("*.py") if x.is_file())
            category = f.name
            deps["by_type"][category] = count
    return deps


def _run_skill_validation(root: Path) -> list[dict[str, Any]]:
    issues = []
    skill_md = root / "SKILL.md"
    if not skill_md.exists():
        issues.append({"type": "missing_file", "file": "SKILL.md", "severity": "critical"})
    config_yaml = root / ".skill-config.yaml"
    if not config_yaml.exists():
        issues.append({"type": "missing_file", "file": ".skill-config.yaml", "severity": "high"})
    scripts_dir = root / "scripts"
    if scripts_dir.exists():
        for f in scripts_dir.iterdir():
            if f.is_file() and f.suffix == ".py":
                try:
                    content = f.read_text(encoding="utf-8")
                    if "\ufffd" in content:
                        issues.append({"type": "encoding", "file": str(f.name), "severity": "high", "detail": "包含U+FFFD替换字符"})
                except Exception:
                    pass
    return issues


def register(mcp: FastMCP) -> None:
    @mcp.tool(
        annotations=ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        )
    )
    async def skill_analyze(
        skill_path: str,
        include_scripts: bool = True,
        include_agents: bool = True,
        depth: str = "basic",
    ) -> dict[str, Any]:
        """分析技能项目结构，提取YAML元数据、目录结构、Agent注册表、脚本依赖和验证问题。返回结构化分析结果，支持basic(1)、detailed(2)、full/comprehensive(3)三种深度模式。"""
        validated, err = validate_input(SkillAnalyzeInput, skill_path=skill_path, include_scripts=include_scripts, include_agents=include_agents, depth=depth)
        if err:
            return err
        logger.info("skill_analyze called: skill_path=%s depth=%s", skill_path, depth)
        try:
            depth_level = _normalize_depth(depth)
            safe_path, path_err = validate_path_safety(skill_path, allow_absolute=True)
            if path_err:
                return make_error_response(ValueError(path_err), error_code=ERR_VALIDATION)
            root = Path(skill_path)
            if not root.exists():
                return make_error_response(PathNotFoundError(skill_path), error_code=ERR_NOT_FOUND)

            skill_md = root / "SKILL.md"
            metadata = _parse_yaml_frontmatter(skill_md)

            structure = _scan_directory(root, depth_level)

            agents: list[dict[str, Any]] = []
            if include_agents and depth_level >= 2:
                registry = root / "references" / "agent-registry.md"
                if not registry.exists():
                    registry = REFERENCES_DIR / "agent-registry.md"
                agents = _parse_agent_registry(registry)

            dependencies: dict[str, Any] = {}
            if include_scripts and depth_level >= 2:
                scripts_dir = root / "scripts"
                if not scripts_dir.exists():
                    scripts_dir = SCRIPTS_DIR
                dependencies = _scan_script_dependencies(scripts_dir)

            issues: list[dict[str, Any]] = []
            if depth_level >= 3:
                issues = _run_skill_validation(root)

            scale_assessment: dict[str, Any] = {}
            if depth_level >= 3:
                scale_assessment = _assess_project_scale(skill_path)

            result: dict[str, Any] = {
                "metadata": metadata,
                "structure": structure,
                "depth_level": depth_level,
            }
            if depth_level >= 2:
                result["agents"] = agents
                result["dependencies"] = dependencies
            if depth_level >= 3:
                result["issues"] = issues
                result["project_scale"] = scale_assessment.get("scale", "unknown")
                result["recommended_workflow"] = scale_assessment.get("recommended_workflow", "")
                result["scale_details"] = scale_assessment

            return make_success_response(result)
        except Exception as e:
            logger.error("skill_analyze error: %s", e)
            return make_error_response(e)
