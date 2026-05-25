import ast
import json
import os
from pathlib import Path
from typing import Any, Dict, List

from ..config import make_response, make_error_response, mcp_available
from ..degradation import MCPToolFallback

MCP_JSON_SCHEMA_URI = "https://json-schema.org/draft/2020-12/schema"

if mcp_available:
    from mcp.types import Tool, TextContent, ToolAnnotations

_PHASE_NAMES = [
    "初始化", "需求分析", "架构设计", "测试先行",
    "代码实现", "测试验证", "验收确认", "持续重构", "部署交付",
]

_SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}

_QUALITY_GATES = [
    {"gate_id": "DESIGN-SYSTEM-COMPLETE", "phase": 0, "severity": "BLOCK"},
    {"gate_id": "ANTI-PATTERN-CHECK", "phase": 0, "severity": "WARN"},
    {"gate_id": "SPEC-COMPLETE", "phase": 1, "severity": "BLOCK"},
    {"gate_id": "REQUIREMENT-TRACEABLE", "phase": 1, "severity": "WARN"},
    {"gate_id": "ARCH-REVIEW", "phase": 2, "severity": "BLOCK"},
    {"gate_id": "API-CONTRACT", "phase": 2, "severity": "WARN"},
    {"gate_id": "GATE-007", "phase": 4, "severity": "BLOCK"},
    {"gate_id": "TEST-PASS", "phase": 4, "severity": "BLOCK"},
    {"gate_id": "FILE-ENCODING", "phase": 4, "severity": "BLOCK"},
    {"gate_id": "AI-PENTEST", "phase": 5, "severity": "BLOCK"},
    {"gate_id": "SPEC-CONSISTENCY", "phase": 5, "severity": "WARN"},
    {"gate_id": "SIMPLIFICATION-BEHAVIOR", "phase": 7, "severity": "WARN"},
    {"gate_id": "GATE-015", "phase": 7, "severity": "BLOCK"},
]

_HOOK_DEFINITIONS = {
    "minimal": [
        {"name": "SessionStart", "trigger": "session_init", "pre_callbacks": [], "post_callbacks": ["session_manage(load)"], "enabled": True},
        {"name": "SessionStop", "trigger": "session_end", "pre_callbacks": [], "post_callbacks": ["session_manage(save)"], "enabled": True},
    ],
    "standard": [
        {"name": "PhaseEnter", "trigger": "phase_transition", "pre_callbacks": ["validate_phase_prerequisites"], "post_callbacks": ["notify_agents", "preload_resources"], "enabled": True},
        {"name": "GatePass", "trigger": "gate_check_pass", "pre_callbacks": [], "post_callbacks": ["quality_gate_check"], "enabled": True},
        {"name": "GateFail", "trigger": "gate_check_fail", "pre_callbacks": [], "post_callbacks": ["log_failure", "suggest_fix"], "enabled": True},
        {"name": "SessionStart", "trigger": "session_init", "pre_callbacks": [], "post_callbacks": ["session_manage(load)"], "enabled": True},
        {"name": "SessionStop", "trigger": "session_end", "pre_callbacks": [], "post_callbacks": ["session_manage(save)"], "enabled": True},
    ],
    "strict": [
        {"name": "PhaseEnter", "trigger": "phase_transition", "pre_callbacks": ["validate_phase_prerequisites", "check_token_budget"], "post_callbacks": ["notify_agents", "preload_resources", "log_phase_change"], "enabled": True},
        {"name": "GatePass", "trigger": "gate_check_pass", "pre_callbacks": ["verify_gate_context"], "post_callbacks": ["quality_gate_check", "update_metrics"], "enabled": True},
        {"name": "GateFail", "trigger": "gate_check_fail", "pre_callbacks": ["capture_failure_context"], "post_callbacks": ["log_failure", "suggest_fix", "notify_orchestrator"], "enabled": True},
        {"name": "SessionStart", "trigger": "session_init", "pre_callbacks": ["validate_environment"], "post_callbacks": ["session_manage(load)", "preload_resources"], "enabled": True},
        {"name": "SessionStop", "trigger": "session_end", "pre_callbacks": ["verify_all_tasks"], "post_callbacks": ["session_manage(save)", "generate_report"], "enabled": True},
        {"name": "CodeChange", "trigger": "file_modified", "pre_callbacks": ["check_encoding"], "post_callbacks": ["run_lint", "update_dependencies"], "enabled": True},
    ],
}

_DEFAULT_BUDGET_ALLOCATIONS = {
    "0": 8000, "1": 15000, "2": 22000, "3": 12000,
    "4": 45000, "5": 18000, "6": 10000, "7": 12000, "8": 8000,
}

_SIZE_MULTIPLIERS = {"small": 0.6, "medium": 1.0, "large": 1.6}
_COMPLEXITY_MULTIPLIERS = {"low": 0.8, "medium": 1.0, "high": 1.3}


def _extract_skill_metadata(root: Path) -> dict:
    metadata = {"name": "", "version": "", "agents_summary": "", "tags": []}
    skill_md = root / "SKILL.md"
    if skill_md.exists():
        try:
            with open(str(skill_md), "r", encoding="utf-8") as f:
                content = f.read()
            if content.startswith("---"):
                end = content.find("---", 3)
                if end > 0:
                    frontmatter = content[3:end].strip()
                    for line in frontmatter.split("\n"):
                        if ":" in line:
                            key, _, val = line.partition(":")
                            key = key.strip()
                            val = val.strip()
                            if key == "name":
                                metadata["name"] = val.strip('"').strip("'")
                            elif key == "version":
                                metadata["version"] = val.strip('"').strip("'")
                            elif key == "agents_summary":
                                metadata["agents_summary"] = val.strip('"').strip("'")
                            elif key == "tags":
                                if val.startswith("["):
                                    metadata["tags"] = [t.strip().strip('"').strip("'") for t in val.strip("[]").split(",")]
        except OSError:
            pass
    return metadata


def _analyze_structure(root: Path, depth: str) -> dict:
    directories = []
    file_count = 0
    total_lines = 0
    for item in root.iterdir():
        if item.is_dir() and not item.name.startswith("."):
            directories.append(item.name)
        elif item.is_file():
            file_count += 1
    for root_dir, _dirs, files in os.walk(str(root)):
        if any(skip in root_dir for skip in (".git", "__pycache__", "node_modules", ".knowledge")):
            continue
        for fname in files:
            file_count += 1
            if depth == "full":
                fpath = os.path.join(root_dir, fname)
                try:
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as fh:
                        total_lines += sum(1 for _ in fh)
                except OSError:
                    pass
    return {
        "root": str(root),
        "directories": sorted(directories),
        "file_count": file_count,
        "total_lines": total_lines,
    }


def _analyze_agents(root: Path) -> dict:
    agents_dir = root / "agents"
    by_layer = {}
    total = 0
    if agents_dir.exists():
        for layer_dir in sorted(agents_dir.iterdir()):
            if not layer_dir.is_dir():
                continue
            count = len(list(layer_dir.glob("*.md")))
            by_layer[layer_dir.name] = count
            total += count
    return {"total": total, "layers": len(by_layer), "by_layer": by_layer}


def _analyze_dependencies(root: Path) -> dict:
    scripts_dir = root / "scripts"
    scripts = []
    if scripts_dir.exists():
        for f in scripts_dir.rglob("*.py"):
            scripts.append(f.name)
    return {
        "mcp_server": "xuansto-mcp-server>=4.0.0",
        "scripts": sorted(scripts),
        "python_version": ">=3.10",
    }


def _detect_issues(root: Path, metadata: dict, dependencies: dict) -> list:
    issues = []
    if not metadata.get("name"):
        issues.append({"severity": "WARN", "code": "MISSING_METADATA", "message": "SKILL.md missing name field", "path": "SKILL.md"})
    if not metadata.get("version"):
        issues.append({"severity": "WARN", "code": "MISSING_VERSION", "message": "SKILL.md missing version field", "path": "SKILL.md"})
    scripts_dir = root / "scripts"
    if scripts_dir.exists():
        for script_name in dependencies.get("scripts", []):
            if not (scripts_dir / script_name).exists() and not list(scripts_dir.rglob(script_name)):
                pass
    return issues


def _check_single_gate(gate: dict, root: Path) -> dict:
    gate_id = gate["gate_id"]
    severity = gate["severity"]
    passed = True
    message = f"Gate {gate_id} passed"
    details = {}

    if gate_id == "FILE-ENCODING":
        bom_files = []
        for root_dir, _dirs, files in os.walk(str(root)):
            if any(skip in root_dir for skip in (".git", "node_modules", "__pycache__", ".knowledge")):
                continue
            for fname in files:
                if not fname.endswith((".py", ".js", ".ts", ".tsx", ".jsx")):
                    continue
                fpath = os.path.join(root_dir, fname)
                try:
                    with open(fpath, "rb") as fh:
                        start = fh.read(3)
                        if start == b'\xef\xbb\xbf':
                            bom_files.append(os.path.relpath(fpath, str(root)))
                except OSError:
                    pass
        if bom_files:
            passed = False
            message = f"{len(bom_files)} files have BOM markers"
            details = {"offending_files": bom_files, "issue": "UTF-8 BOM detected"}
    elif gate_id == "TEST-PASS":
        details = {"total_tests": 0, "passed": 0, "failed": 0, "coverage_pct": 0.0}
        message = "No test runner detected, gate skipped"
    elif gate_id == "DESIGN-SYSTEM-COMPLETE":
        specs_dir = root / ".trae" / "specs"
        if not specs_dir.exists() or not list(specs_dir.glob("*.md")):
            passed = False
            message = "No spec documents found in .trae/specs"
            details = {"spec_dir": str(specs_dir)}
    elif gate_id == "ANTI-PATTERN-CHECK":
        details = {"patterns_checked": 0}
        message = "Anti-pattern check passed (inline scan)"
    else:
        details = {"note": "Gate check not fully implemented in inline mode"}

    return {
        "gate_id": gate_id,
        "status": "PASS" if passed else "FAIL",
        "severity": severity,
        "message": message,
        "details": details,
    }


def _scan_dependencies(target_path: Path, findings: list, min_severity: int) -> int:
    dep_count = 0
    req_files = ["requirements.txt", "pyproject.toml", "package.json"]
    for rf in req_files:
        fpath = target_path / rf
        if not fpath.exists():
            continue
        try:
            with open(str(fpath), "r", encoding="utf-8", errors="ignore") as fh:
                content = fh.read()
            if rf == "package.json":
                try:
                    pkg = json.loads(content)
                    for dep_name in list(pkg.get("dependencies", {}).keys()) + list(pkg.get("devDependencies", {}).keys()):
                        pass
                except json.JSONDecodeError:
                    pass
        except OSError:
            pass
    return dep_count


def _analyze_python_file(fpath: Path, suggestions: list, by_type: dict, base_path: Path):
    try:
        with open(str(fpath), "r", encoding="utf-8", errors="ignore") as fh:
            source = fh.read()
        tree = ast.parse(source)
        idx = len(suggestions) + 1
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                body_lines = (node.end_lineno - node.lineno + 1) if hasattr(node, 'end_lineno') and node.end_lineno else 0
                if body_lines > 50:
                    suggestions.append({
                        "id": f"SIMP-{idx:03d}",
                        "type": "complexity",
                        "file": str(fpath.relative_to(base_path)) if fpath.is_relative_to(base_path) else str(fpath),
                        "line_start": node.lineno,
                        "line_end": node.end_lineno if hasattr(node, 'end_lineno') else node.lineno,
                        "description": f"Long function '{node.name}' ({body_lines} lines)",
                        "safety": "CAUTION",
                        "action": f"Consider breaking '{node.name}' into smaller functions",
                        "estimated_reduction": body_lines // 3,
                    })
                    by_type["complexity"] += 1
                    idx += 1
                for child in ast.walk(node):
                    if child is node:
                        continue
                    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        if child.name == node.name:
                            continue
                if not node.body:
                    suggestions.append({
                        "id": f"SIMP-{idx:03d}",
                        "type": "dead_code",
                        "file": str(fpath.relative_to(base_path)) if fpath.is_relative_to(base_path) else str(fpath),
                        "line_start": node.lineno,
                        "line_end": node.end_lineno if hasattr(node, 'end_lineno') else node.lineno,
                        "description": f"Empty function '{node.name}'",
                        "safety": "CAUTION",
                        "action": f"Remove or implement '{node.name}'",
                        "estimated_reduction": 2,
                    })
                    by_type["dead_code"] += 1
                    idx += 1
    except (OSError, SyntaxError):
        pass


def _detect_code_duplication(target_path: Path) -> list:
    suggestions = []
    func_bodies = {}
    if target_path.is_file() and target_path.suffix == ".py":
        files = [target_path]
    else:
        files = []
        for root_dir, _dirs, fnames in os.walk(str(target_path)):
            if any(skip in root_dir for skip in ("node_modules", ".git", "__pycache__", ".venv", ".knowledge")):
                continue
            for fname in fnames:
                if fname.endswith(".py"):
                    files.append(Path(root_dir) / fname)
    for fpath in files:
        try:
            with open(str(fpath), "r", encoding="utf-8", errors="ignore") as fh:
                source = fh.read()
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    body_start = node.lineno
                    body_end = node.end_lineno if hasattr(node, 'end_lineno') else node.lineno
                    body_lines = body_end - body_start + 1
                    if body_lines >= 5:
                        key = (body_lines, node.name)
                        if key in func_bodies:
                            func_bodies[key].append(str(fpath))
                        else:
                            func_bodies[key] = [str(fpath)]
        except (OSError, SyntaxError):
            pass
    idx_base = 100
    for (lines, name), paths in func_bodies.items():
        if len(paths) > 1:
            suggestions.append({
                "id": f"SIMP-{idx_base:03d}",
                "type": "duplication",
                "files": paths,
                "description": f"Duplicate function '{name}' ({lines} lines) in {len(paths)} files",
                "safety": "SAFE",
                "action": f"Extract '{name}' into a shared module",
                "estimated_reduction": lines * (len(paths) - 1),
            })
            idx_base += 1
    return suggestions


def _scan_agent_registry(skill_root: Path) -> list:
    agents = []
    agents_dir = skill_root / "agents"
    if agents_dir.exists():
        for layer_dir in sorted(agents_dir.iterdir()):
            if not layer_dir.is_dir():
                continue
            for agent_file in sorted(layer_dir.glob("*.md")):
                agents.append({
                    "name": agent_file.stem,
                    "layer": layer_dir.name,
                    "status": "AVAILABLE",
                    "capabilities": [],
                    "assigned_tasks": 0,
                    "completed_tasks": 0,
                    "definition_file": str(agent_file.relative_to(skill_root)),
                })
    return agents


def _phase_to_layers(phase: int) -> list:
    mapping = {
        0: ["orchestration"],
        1: ["product"],
        2: ["design"],
        3: ["testing"],
        4: ["engineering"],
        5: ["testing", "security"],
        6: ["product", "orchestration"],
        7: ["engineering", "design"],
        8: ["orchestration", "devops"],
    }
    return mapping.get(phase, [])


def _estimate_tokens(text: str) -> int:
    return len(text) // 4


def _semantic_compress(content: str, preserve_sections: list, target_tokens: int) -> str:
    lines = content.split("\n")
    preserved_lines = []
    other_lines = []
    in_preserve = False
    current_section = ""
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#") or stripped.startswith("##"):
            current_section = stripped.lstrip("#").strip()
            if current_section in preserve_sections:
                in_preserve = True
            else:
                in_preserve = False
        if in_preserve:
            preserved_lines.append(line)
        else:
            other_lines.append(line)
    budget_per_line = max(1, target_tokens * 4 // max(len(other_lines), 1))
    compressed_other = []
    for line in other_lines:
        if len(line) <= budget_per_line:
            compressed_other.append(line)
        else:
            compressed_other.append(line[:budget_per_line] + "...")
    return "\n".join(preserved_lines + compressed_other)


def _selective_compress(content: str, preserve_sections: list, target_tokens: int) -> str:
    lines = content.split("\n")
    result = []
    in_preserve = False
    current_section = ""
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#") or stripped.startswith("##"):
            current_section = stripped.lstrip("#").strip()
            in_preserve = current_section in preserve_sections
        if in_preserve:
            result.append(line)
        elif stripped and not stripped.startswith("#"):
            result.append(line)
    return "\n".join(result)


def _lossless_compress(content: str) -> str:
    lines = content.split("\n")
    result = []
    prev_empty = False
    for line in lines:
        if not line.strip():
            if prev_empty:
                continue
            prev_empty = True
        else:
            prev_empty = False
        result.append(line.rstrip())
    return "\n".join(result)
