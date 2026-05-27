#!/usr/bin/env python3
"""Xuansto Skill 自检脚本 - 验证目录结构、Agent定义、质量门禁、命令格式、工作流和知识库"""

import argparse
import json
import os
import re
import socket
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml

    yaml_available = True
except ImportError:
    yaml_available = False

REQUIRED_DIRS = [
    "agents",
    "commands",
    "workflows",
    "templates",
    "scripts",
    "references",
    "configs",
    ".knowledge",
]

REQUIRED_FILES = ["SKILL.md", "configs/default.yaml", ".knowledge/config.yaml"]

REQUIRED_AGENT_FRONTMATTER_FIELDS = ["name", "emoji", "description", "color", "services"]

REQUIRED_GATE_KEYS = ["name", "phase", "blocking", "automation"]

MANDATORY_GATES = ["SCRIPT-SECURITY", "SCRIPT-CLEANUP", "TOKEN-BUDGET"]

VALID_COMMAND_CATEGORIES = ["workflow", "quality", "knowledge", "system"]

REQUIRED_COMMAND_FRONTMATTER = ["name", "category", "description", "trigger"]

EXPECTED_GATE_COUNT = 37
EXPECTED_COMMAND_COUNT = 17
EXPECTED_WORKFLOW_COUNT = 10


def _get_expected_agent_count(skill_root: Path) -> int:
    agents_dir = skill_root / "agents"
    if not agents_dir.is_dir():
        return 0
    return sum(1 for f in agents_dir.rglob("*.md") if f.is_file())


def _make_check(name: str, status: str, detail: str = "") -> Dict[str, str]:
    return {"name": name, "status": status, **({"detail": detail} if detail else {})}


def _count_files(directory: Path) -> int:
    if not directory.is_dir():
        return 0
    return sum(1 for _ in directory.rglob("*") if _.is_file())


def _parse_yaml_frontmatter(content: str) -> Optional[Dict[str, Any]]:
    match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return None
    if not yaml_available:
        lines = match.group(1).split("\n")
        result: Dict[str, Any] = {}
        for line in lines:
            if ":" in line:
                key, _, value = line.partition(":")
                result[key.strip()] = value.strip().strip('"').strip("'")
        return result
    try:
        return yaml.safe_load(match.group(1))
    except yaml.YAMLError:
        return None


def _read_text(filepath: Path) -> Optional[str]:
    try:
        return filepath.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def test_structure(skill_root: Path, verbose: bool) -> Dict[str, Any]:
    """测试目录结构完整性"""
    checks: List[Dict[str, str]] = []
    failed = 0

    for dir_name in REQUIRED_DIRS:
        dir_path = skill_root / dir_name
        if dir_path.is_dir():
            file_count = _count_files(dir_path)
            checks.append(_make_check(f"{dir_name}/ directory", "passed", f"{file_count} files"))
        else:
            checks.append(_make_check(f"{dir_name}/ directory", "failed", "missing"))
            failed += 1

    for file_path in REQUIRED_FILES:
        full_path = skill_root / file_path
        if full_path.is_file():
            checks.append(_make_check(f"{file_path} exists", "passed"))
        else:
            checks.append(_make_check(f"{file_path} exists", "failed", "missing"))
            failed += 1

    status = "passed" if failed == 0 else "failed"
    result: Dict[str, Any] = {"status": status, "checks": checks}
    if verbose:
        result["detail"] = f"{len(checks)} checks, {failed} failed"
    return result


def test_agents(skill_root: Path, verbose: bool) -> Dict[str, Any]:
    """测试Agent定义文件格式"""
    agents_dir = skill_root / "agents"
    agent_files = sorted(agents_dir.rglob("*.md")) if agents_dir.is_dir() else []
    total = len(agent_files)
    valid = 0
    invalid_details: List[str] = []

    for agent_file in agent_files:
        content = _read_text(agent_file)
        if content is None:
            invalid_details.append(f"{agent_file.name}: unreadable")
            continue

        frontmatter = _parse_yaml_frontmatter(content)
        if frontmatter is None:
            invalid_details.append(f"{agent_file.name}: missing frontmatter")
            continue

        missing_fields = [f for f in REQUIRED_AGENT_FRONTMATTER_FIELDS if f not in frontmatter]
        if missing_fields:
            invalid_details.append(f"{agent_file.name}: missing {', '.join(missing_fields)}")
        else:
            valid += 1

    agent_registry_path = skill_root / "references" / "agent-registry.md"
    registry_ok = True
    registry_detail = ""
    if agent_registry_path.is_file():
        registry_content = _read_text(agent_registry_path)
        if registry_content:
            agent_basenames = {f.stem for f in agent_files}
            for basename in agent_basenames:
                if basename not in registry_content:
                    registry_ok = False
                    registry_detail = f"agent-registry.md missing reference to {basename}"
                    break
        else:
            registry_ok = False
            registry_detail = "agent-registry.md unreadable"
    else:
        registry_ok = False
        registry_detail = "agent-registry.md not found"

    expected_count = _get_expected_agent_count(skill_root)
    status = "passed" if valid == total and registry_ok else "failed"
    result: Dict[str, Any] = {
        "status": status,
        "total_agents": total,
        "valid_agents": valid,
        "expected_agents": expected_count,
    }
    if not registry_ok:
        result["registry_check"] = registry_detail
    if verbose and invalid_details:
        result["invalid_details"] = invalid_details
    return result


def test_gates(skill_root: Path, verbose: bool) -> Dict[str, Any]:
    """测试质量门禁定义完整性"""
    gates_path = skill_root / "references" / "quality-gates.md"
    if not gates_path.is_file():
        return {"status": "failed", "total_gates": 0, "missing_gates": ["quality-gates.md not found"]}

    content = _read_text(gates_path)
    if content is None:
        return {"status": "failed", "total_gates": 0, "missing_gates": ["quality-gates.md unreadable"]}

    table_row_pattern = re.compile(
        r"^\|\s*\*{0,2}Phase[^|]*\*{0,2}\s*\|\s*([A-Za-z][A-Za-z0-9\-]+)\s*\|",
        re.MULTILINE,
    )
    gate_aliases: List[str] = []
    for match in table_row_pattern.finditer(content):
        alias = match.group(1).strip()
        if alias and alias not in gate_aliases:
            gate_aliases.append(alias)

    cross_phase_pattern = re.compile(
        r"^\|\s*跨阶段\s*\|\s*([A-Za-z][A-Za-z0-9\-]+)\s*\|",
        re.MULTILINE,
    )
    for match in cross_phase_pattern.finditer(content):
        alias = match.group(1).strip()
        if alias and alias not in gate_aliases:
            gate_aliases.append(alias)

    total = len(gate_aliases)

    missing_mandatory = [g for g in MANDATORY_GATES if g not in content]

    gates_with_details: List[Dict[str, str]] = []
    for gate_name in gate_aliases:
        gate_section = re.search(
            rf"###?\s+{re.escape(gate_name)}[:\s]", content
        )
        if gate_section is None:
            gates_with_details.append({
                "name": gate_name,
                "has_phase": "skipped",
                "warning": "gate section not found in document",
            })
            continue
        has_phase = bool(re.search(rf"(?:阶段|Phase|phase)[:\s]", content[gate_section.start() : gate_section.start() + 800]))
        gates_with_details.append({
            "name": gate_name,
            "has_phase": str(has_phase),
        })

    status = "passed" if total >= EXPECTED_GATE_COUNT and not missing_mandatory else "failed"
    result: Dict[str, Any] = {
        "status": status,
        "total_gates": total,
        "missing_gates": missing_mandatory,
    }
    if verbose:
        result["gate_details"] = gates_with_details
    return result


def test_commands(skill_root: Path, verbose: bool) -> Dict[str, Any]:
    """测试命令文件格式"""
    commands_dir = skill_root / "commands"
    cmd_files = sorted(commands_dir.glob("*.md")) if commands_dir.is_dir() else []
    total = len(cmd_files)
    valid = 0
    invalid_details: List[str] = []

    for cmd_file in cmd_files:
        content = _read_text(cmd_file)
        if content is None:
            invalid_details.append(f"{cmd_file.name}: unreadable")
            continue

        frontmatter = _parse_yaml_frontmatter(content)
        if frontmatter is None:
            invalid_details.append(f"{cmd_file.name}: missing frontmatter")
            continue

        missing_fields = [f for f in REQUIRED_COMMAND_FRONTMATTER if f not in frontmatter]
        if missing_fields:
            invalid_details.append(f"{cmd_file.name}: missing fields {', '.join(missing_fields)}")
            continue

        name_val = str(frontmatter.get("name", ""))
        if not name_val.startswith("/"):
            invalid_details.append(f"{cmd_file.name}: name '{name_val}' does not start with /")
            continue

        category_val = str(frontmatter.get("category", ""))
        if category_val not in VALID_COMMAND_CATEGORIES:
            invalid_details.append(f"{cmd_file.name}: invalid category '{category_val}'")
            continue

        valid += 1

    status = "passed" if valid == total else "failed"
    result: Dict[str, Any] = {
        "status": status,
        "total_commands": total,
        "valid_commands": valid,
    }
    if verbose and invalid_details:
        result["invalid_details"] = invalid_details
    return result


def test_workflows(skill_root: Path, verbose: bool) -> Dict[str, Any]:
    """测试工作流文件格式"""
    workflows_dir = skill_root / "workflows"
    wf_files = sorted(workflows_dir.glob("*.md")) if workflows_dir.is_dir() else []
    total = len(wf_files)
    valid = 0
    invalid_details: List[str] = []

    for wf_file in wf_files:
        content = _read_text(wf_file)
        if content is None:
            invalid_details.append(f"{wf_file.name}: unreadable")
            continue

        if len(content.strip()) == 0:
            invalid_details.append(f"{wf_file.name}: empty file")
            continue

        has_phases = bool(re.search(r"(?:Phase|阶段)\s*\d", content, re.IGNORECASE))
        has_gates = bool(re.search(r"(?:质量门禁|Quality\s*Gate|gate)", content, re.IGNORECASE))

        if not has_phases and not has_gates:
            invalid_details.append(f"{wf_file.name}: missing Phase definitions and quality gates")
        else:
            valid += 1

    status = "passed" if valid == total else "failed"
    result: Dict[str, Any] = {
        "status": status,
        "total_workflows": total,
        "valid_workflows": valid,
    }
    if verbose and invalid_details:
        result["invalid_details"] = invalid_details
    return result


def test_knowledge(skill_root: Path, verbose: bool) -> Dict[str, Any]:
    """测试知识库服务连通性"""
    config_path = skill_root / ".knowledge" / "config.yaml"
    platform_config_path = skill_root / ".knowledge" / "platform-config.yaml"
    server_script = skill_root / "scripts" / "knowledge-server.py"

    config_valid = False
    server_host = "127.0.0.1"
    server_port = 8765
    config_error = ""

    if not config_path.is_file():
        config_error = ".knowledge/config.yaml not found"
    else:
        content = _read_text(config_path)
        if content is None:
            config_error = ".knowledge/config.yaml unreadable"
        elif yaml_available:
            try:
                cfg = yaml.safe_load(content)
                server_cfg = cfg.get("server", {}) if isinstance(cfg, dict) else {}
                server_host = server_cfg.get("host", "127.0.0.1")
                server_port = int(server_cfg.get("port", 8765))
                config_valid = True
            except (yaml.YAMLError, ValueError, TypeError):
                config_error = ".knowledge/config.yaml parse error"
        else:
            host_match = re.search(r"host:\s*[\"']?([^\"'\s]+)", content)
            port_match = re.search(r"port:\s+(\d+)", content)
            if host_match:
                server_host = host_match.group(1)
            if port_match:
                server_port = int(port_match.group(1))
            config_valid = True

    platform_config_exists = platform_config_path.is_file()
    server_script_exists = server_script.is_file()

    server_reachable = False
    reach_message = ""
    if config_valid:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex((server_host, server_port))
            sock.close()
            if result == 0:
                server_reachable = True
            else:
                reach_message = "Knowledge server not running"
        except (socket.error, OSError) as e:
            reach_message = f"Connection error: {e}"
    else:
        reach_message = config_error

    if not config_valid:
        status = "failed"
    elif not server_reachable:
        status = "warning"
    else:
        status = "passed"

    result: Dict[str, Any] = {
        "status": status,
        "config_valid": config_valid,
        "platform_config_exists": platform_config_exists,
        "server_script_exists": server_script_exists,
        "server_reachable": server_reachable,
    }
    if reach_message:
        result["message"] = reach_message
    if verbose:
        result["server_host"] = server_host
        result["server_port"] = server_port
    return result


TEST_MAP = {
    "structure": test_structure,
    "agents": test_agents,
    "gates": test_gates,
    "commands": test_commands,
    "workflows": test_workflows,
    "knowledge": test_knowledge,
}


def run_tests(skill_root: Path, test_types: List[str], verbose: bool) -> Dict[str, Any]:
    """执行所有指定类型的测试"""
    results: Dict[str, Any] = {}
    passed = 0
    failed = 0
    warnings = 0

    for ttype in test_types:
        if ttype not in TEST_MAP:
            results[ttype] = {"status": "failed", "message": f"Unknown test type: {ttype}"}
            failed += 1
            continue
        try:
            result = TEST_MAP[ttype](skill_root, verbose)
        except Exception as e:
            result = {"status": "failed", "message": str(e)}
        results[ttype] = result
        status = result.get("status", "failed")
        if status == "passed":
            passed += 1
        elif status == "warning":
            warnings += 1
        else:
            failed += 1

    total_tests = len(test_types)
    pass_rate = round(passed / total_tests, 3) if total_tests > 0 else 0.0

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "skill_root": str(skill_root),
        "summary": {
            "total_tests": total_tests,
            "passed": passed,
            "failed": failed,
            "warnings": warnings,
            "pass_rate": pass_rate,
        },
        "results": results,
    }


def format_text_output(report: Dict[str, Any]) -> str:
    """将报告格式化为可读文本"""
    lines: List[str] = []
    lines.append(f"Xuansto Skill Self-Test Report")
    lines.append(f"{'=' * 50}")
    lines.append(f"Timestamp: {report['timestamp']}")
    lines.append(f"Skill Root: {report['skill_root']}")
    lines.append("")

    summary = report["summary"]
    lines.append(f"Summary:")
    lines.append(f"  Total:   {summary['total_tests']}")
    lines.append(f"  Passed:  {summary['passed']}")
    lines.append(f"  Failed:  {summary['failed']}")
    lines.append(f"  Warnings:{summary['warnings']}")
    lines.append(f"  Rate:    {summary['pass_rate']:.1%}")
    lines.append("")

    for ttype, result in report["results"].items():
        status = result.get("status", "unknown")
        icon = {"passed": "✓", "failed": "✗", "warning": "⚠"}.get(status, "?")
        lines.append(f"[{icon}] {ttype}: {status}")

        if ttype == "structure" and "checks" in result:
            for check in result["checks"]:
                ci = "✓" if check["status"] == "passed" else "✗"
                detail = f" ({check['detail']})" if "detail" in check else ""
                lines.append(f"    {ci} {check['name']}{detail}")

        elif ttype == "agents":
            lines.append(f"    Agents: {result.get('valid_agents', 0)}/{result.get('total_agents', 0)} (expected: {result.get('expected_agents', '?')})")
            if "registry_check" in result:
                lines.append(f"    Registry: {result['registry_check']}")

        elif ttype == "gates":
            lines.append(f"    Gates: {result.get('total_gates', 0)}/{EXPECTED_GATE_COUNT}")
            if result.get("missing_gates"):
                lines.append(f"    Missing: {', '.join(result['missing_gates'])}")

        elif ttype == "commands":
            lines.append(f"    Commands: {result.get('valid_commands', 0)}/{result.get('total_commands', 0)}")

        elif ttype == "workflows":
            lines.append(f"    Workflows: {result.get('valid_workflows', 0)}/{result.get('total_workflows', 0)}")

        elif ttype == "knowledge":
            lines.append(f"    Config valid: {result.get('config_valid', False)}")
            lines.append(f"    Server reachable: {result.get('server_reachable', False)}")
            if "message" in result:
                lines.append(f"    Message: {result['message']}")

        lines.append("")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Xuansto Skill 自检脚本")
    parser.add_argument(
        "--skill-root",
        type=str,
        default=None,
        help="Skill根目录（默认从脚本位置自动检测）",
    )
    parser.add_argument(
        "--type",
        type=str,
        default="all",
        help="测试类型，逗号分隔: structure/agents/gates/commands/workflows/knowledge/all",
    )
    parser.add_argument(
        "--format",
        type=str,
        choices=["json", "text"],
        default="json",
        help="输出格式（默认: json）",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="输出文件路径（默认: stdout）",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        default=False,
        help="显示详细输出",
    )

    args = parser.parse_args()

    if args.skill_root:
        skill_root = Path(args.skill_root).resolve()
    else:
        skill_root = Path(__file__).resolve().parent.parent

    if not skill_root.is_dir():
        print(f"Error: skill root not found: {skill_root}", file=sys.stderr)
        return 2

    type_str = args.type.strip()
    if type_str == "all":
        test_types = list(TEST_MAP.keys())
    else:
        test_types = [t.strip() for t in type_str.split(",") if t.strip()]

    try:
        report = run_tests(skill_root, test_types, args.verbose)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2

    if args.format == "json":
        output = json.dumps(report, ensure_ascii=False, indent=2)
    else:
        output = format_text_output(report)

    if args.output:
        try:
            Path(args.output).write_text(output, encoding="utf-8")
        except OSError as e:
            print(f"Error writing output: {e}", file=sys.stderr)
            return 2
    else:
        print(output)

    summary = report.get("summary", {})
    if summary.get("failed", 0) > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
