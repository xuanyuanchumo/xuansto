import argparse
import json
import re
import sys
from pathlib import Path


class ValidationResult:
    def __init__(self, name, status, message="", details=None):
        self.name = name
        self.status = status
        self.message = message
        self.details = details or []

    def to_dict(self):
        return {
            "name": self.name,
            "status": self.status,
            "message": self.message,
            "details": self.details,
        }


def parse_frontmatter(content):
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if not match:
        return None, content
    fm_text = match.group(1)
    body = content[match.end():]
    fm = {}
    lines = fm_text.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        list_match = re.match(r"^\s+-\s+(.+)$", line)
        if list_match:
            i += 1
            continue
        kv_match = re.match(r"^(\w[\w-]*):\s*(.*)", line)
        if kv_match:
            key = kv_match.group(1)
            value = kv_match.group(2).strip()
            if value.startswith("|"):
                multiline_val = []
                i += 1
                while i < len(lines):
                    next_line = lines[i]
                    if re.match(r"^(\w[\w-]*):\s*", next_line) or re.match(r"^\s+-\s+", next_line):
                        break
                    stripped = next_line.rstrip()
                    if stripped:
                        multiline_val.append(stripped)
                    i += 1
                fm[key] = "\n".join(multiline_val)
                continue
            elif value == "":
                current_list = []
                i += 1
                while i < len(lines):
                    list_item_match = re.match(r"^\s+-\s+(.+)$", lines[i])
                    if list_item_match:
                        current_list.append(list_item_match.group(1).strip())
                        i += 1
                    else:
                        break
                fm[key] = current_list if current_list else ""
                continue
            else:
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                fm[key] = value
        i += 1
    return fm, body


def check_frontmatter(skill_md_path, content, verbose):
    result_name = "YAML Frontmatter Completeness"
    fm, body = parse_frontmatter(content)
    if fm is None:
        return ValidationResult(
            result_name, "ERROR", "No YAML frontmatter found in SKILL.md"
        )
    required_fields = ["name", "version", "description", "tags"]
    missing = []
    for field in required_fields:
        if field not in fm:
            missing.append(field)
        elif field == "tags":
            if not isinstance(fm[field], list) or len(fm[field]) == 0:
                missing.append(f"{field} (empty or not a list)")
        elif isinstance(fm[field], str) and fm[field].strip() == "":
            missing.append(f"{field} (empty)")
    if missing:
        return ValidationResult(
            result_name,
            "ERROR",
            f"Missing or invalid required fields: {', '.join(missing)}",
            missing,
        )
    details = [f"All required fields present: {', '.join(required_fields)}"]
    if verbose:
        for k, v in fm.items():
            if isinstance(v, list):
                val_repr = str(v)
            elif isinstance(v, str) and len(v) > 80:
                val_repr = v[:80] + "..."
            else:
                val_repr = v
            details.append(f"  {k}: {val_repr}")
    return ValidationResult(result_name, "PASS", "All required frontmatter fields present", details)


def check_line_budget(content, verbose):
    result_name = "Three-Layer Structure Line Budget"
    total_lines = len(content.split("\n"))
    max_lines = 150
    details = [f"Total lines: {total_lines} (budget: {max_lines})"]
    if verbose:
        fm, body = parse_frontmatter(content)
        if fm is not None:
            fm_match = re.match(r"^---\s*\n.*?\n---\s*\n", content, re.DOTALL)
            if fm_match:
                fm_lines = len(fm_match.group(0).split("\n"))
                body_lines = len(body.split("\n"))
                details.append(f"  Frontmatter lines: {fm_lines}")
                details.append(f"  Body lines: {body_lines}")
    if total_lines > max_lines:
        return ValidationResult(
            result_name,
            "ERROR",
            f"SKILL.md has {total_lines} lines, exceeds budget of {max_lines}",
            details,
        )
    elif total_lines > max_lines * 0.9:
        return ValidationResult(
            result_name,
            "WARN",
            f"SKILL.md has {total_lines} lines, approaching budget of {max_lines} (>{int(max_lines * 0.9)})",
            details,
        )
    return ValidationResult(result_name, "PASS", f"Line count {total_lines} within budget {max_lines}", details)


def check_core_rules(content, verbose):
    result_name = "Core Rules Must-Haves"
    required_sections = [
        ("Critical Rules", "核心规则|不可妥协原则"),
        ("Behavioral Guidelines", "行为准则|Karpathy"),
        ("Workflow Process", "工作流程|九阶段工作流"),
        ("Success Metrics", "成功指标"),
        ("Technical Deliverables", "技术交付物"),
    ]
    missing = []
    found = []
    for en, zh in required_sections:
        en_pattern = re.compile(re.escape(en), re.IGNORECASE)
        zh_pattern = re.compile(zh)
        if en_pattern.search(content) or zh_pattern.search(content):
            found.append(en)
        else:
            missing.append(f"{en}/{zh}")
    details = []
    if verbose:
        for en, zh in required_sections:
            status = "found" if en in found else "MISSING"
            details.append(f"  [{status}] {en} / {zh}")
    if missing:
        return ValidationResult(
            result_name,
            "WARN",
            f"Missing core rule sections (may exist under different names): {', '.join(missing)}",
            details,
        )
    return ValidationResult(result_name, "PASS", "All 5 core rule sections present", details)


def check_reference_paths(skill_md_path, content, verbose):
    result_name = "Reference Path Existence"
    skill_root = skill_md_path.parent
    link_pattern = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")
    matches = link_pattern.findall(content)
    missing = []
    found = []
    for text, path in matches:
        if path.startswith("http://") or path.startswith("https://") or path.startswith("#"):
            continue
        resolved = (skill_root / path).resolve()
        if resolved.exists():
            found.append(path)
        else:
            missing.append(path)
    details = []
    if verbose:
        details.append(f"  Total links checked: {len(found) + len(missing)}")
        details.append(f"  Existing: {len(found)}")
        details.append(f"  Missing: {len(missing)}")
        for m in missing:
            details.append(f"  MISSING: {m}")
    if missing:
        return ValidationResult(
            result_name,
            "ERROR",
            f"{len(missing)} referenced path(s) do not exist on disk",
            details if verbose else missing,
        )
    return ValidationResult(
        result_name,
        "PASS",
        f"All {len(found)} referenced paths exist",
        details if verbose else [f"All {len(found)} paths verified"],
    )


def _expand_phase_ranges(content):
    phases = set()
    for m in re.finditer(r"Phase\s+(\d+)\s*[-~]\s*(\d+)", content, re.IGNORECASE):
        start, end = int(m.group(1)), int(m.group(2))
        for p in range(start, end + 1):
            phases.add(p)
    return phases


def check_phase_index(content, verbose):
    result_name = "Phase Index Completeness"
    expected_phases = list(range(0, 9))
    found = set()
    for phase in expected_phases:
        explicit = re.search(rf"Phase\s+{phase}\b", content, re.IGNORECASE)
        table_row = re.search(rf"\|\s*{phase}\s*\|", content)
        zh_phase = re.search(rf"阶段\s*{phase}", content)
        if explicit or table_row or zh_phase:
            found.add(phase)
    range_phases = _expand_phase_ranges(content)
    found |= range_phases
    missing = [p for p in expected_phases if p not in found]
    details = []
    if verbose:
        for p in expected_phases:
            status = "found" if p in found else "MISSING"
            details.append(f"  [{status}] Phase {p}")
    if missing:
        return ValidationResult(
            result_name,
            "ERROR",
            f"Missing phases: {', '.join(f'Phase {p}' for p in missing)}",
            details,
        )
    return ValidationResult(
        result_name, "PASS", "All phases (0-8) referenced", details
    )


def check_command_index(skill_md_path, content, verbose):
    result_name = "Command Index Completeness"
    commands_dir = skill_md_path.parent / "commands"
    expected_commands = []
    if commands_dir.exists() and commands_dir.is_dir():
        for f in sorted(commands_dir.iterdir()):
            if f.is_file() and f.suffix == ".md":
                expected_commands.append(f.stem)
    else:
        return ValidationResult(
            result_name,
            "WARN",
            "commands/ directory not found, cannot verify command index",
        )
    missing = []
    found = []
    for cmd in expected_commands:
        cmd_variants = [
            f"/{cmd}",
            f"`/{cmd}`",
            cmd.replace("-", " "),
            cmd,
        ]
        if any(variant in content for variant in cmd_variants):
            found.append(cmd)
        else:
            missing.append(cmd)
    details = []
    if verbose:
        details.append(f"  Expected commands: {len(expected_commands)}")
        details.append(f"  Found: {len(found)}")
        details.append(f"  Missing: {len(missing)}")
        for m in missing:
            details.append(f"  MISSING: /{m}")
    if missing:
        return ValidationResult(
            result_name,
            "ERROR",
            f"Missing {len(missing)} command(s): {', '.join(f'/{c}' for c in missing)}",
            details,
        )
    return ValidationResult(
        result_name,
        "PASS",
        f"All {len(expected_commands)} commands referenced",
        details,
    )


def _count_quality_gates_from_ref(qg_content):
    in_ref_table = False
    gates = set()
    for line in qg_content.split("\n"):
        stripped = line.strip()
        if stripped.startswith("|") and "门禁ID" in stripped:
            in_ref_table = True
            continue
        if in_ref_table:
            if not stripped.startswith("|") or stripped.startswith("| ---") or stripped.startswith("| -"):
                if gates:
                    break
                continue
            cells = [c.strip() for c in stripped.split("|")]
            if cells and len(cells) >= 2:
                gate_id = cells[1].strip()
                if gate_id and re.match(r"^[A-Z]", gate_id):
                    gates.add(gate_id)
    if gates:
        return len(gates)
    return 37


def _expand_gate_ranges(text):
    expanded = text
    for m in re.finditer(r"GATE-(\d{3})\s*[~\-]\s*GATE-(\d{3})", text):
        start, end = int(m.group(1)), int(m.group(2))
        replacement = ", ".join(f"GATE-{i:03d}" for i in range(start, end + 1))
        expanded = expanded.replace(m.group(0), replacement, 1)
    for m in re.finditer(r"GATE-(\d{3})\s*[~\-]\s*(\d{3})", text):
        start, end = int(m.group(1)), int(m.group(2))
        if end > start:
            replacement = ", ".join(f"GATE-{i:03d}" for i in range(start, end + 1))
            expanded = expanded.replace(m.group(0), replacement, 1)
    return expanded


def check_quality_gate_consistency(skill_md_path, content, verbose):
    result_name = "Quality Gate Index Consistency"
    qg_path = skill_md_path.parent / "references" / "quality-gates.md"
    expected_count = 37
    if qg_path.exists():
        try:
            qg_content = qg_path.read_text(encoding="utf-8")
            ref_count = _count_quality_gates_from_ref(qg_content)
            if ref_count > 0:
                expected_count = ref_count
        except Exception:
            expected_count = 37
    expanded_content = _expand_gate_ranges(content)
    gate_id_pattern = re.compile(
        r"\b(GATE-\d{3}|DESIGN-[A-Z-]+|FILE-ENCODING|COMMENT-LANGUAGE|"
        r"SCRIPT-SECURITY|SCRIPT-CLEANUP|TOKEN-BUDGET|AGENTIC-SECURITY|"
        r"AI-PENTEST|VISUAL-REGRESSION|ACCESSIBILITY|PERFORMANCE|"
        r"INFRA-HEALTH|UX-ACCEPTANCE|DOC-COMPLETENESS|DESKTOP-[A-Z-]+|"
        r"IPC-CONTRACT|TEST-PASS|SPEC-CONSISTENCY)\b"
    )
    skill_gates = set(gate_id_pattern.findall(expanded_content))
    skill_count = len(skill_gates)
    details = []
    if verbose:
        details.append(f"  Expected (from quality-gates.md): {expected_count}")
        details.append(f"  Found in SKILL.md: {skill_count}")
        if skill_gates:
            for g in sorted(skill_gates):
                details.append(f"  + {g}")
    if skill_count < expected_count:
        diff = expected_count - skill_count
        return ValidationResult(
            result_name,
            "WARN",
            f"SKILL.md references {skill_count} quality gates, expected {expected_count} (missing {diff})",
            details,
        )
    elif skill_count > expected_count:
        return ValidationResult(
            result_name,
            "WARN",
            f"SKILL.md references {skill_count} quality gates, more than expected {expected_count}",
            details,
        )
    return ValidationResult(
        result_name,
        "PASS",
        f"Quality gate count matches: {skill_count}",
        details,
    )


def check_skill_md_line_count(content, verbose):
    result_name = "SKILL.md Line Count"
    total_lines = len(content.split("\n"))
    max_lines = 300
    details = [f"Total lines: {total_lines} (max: {max_lines})"]
    if total_lines > max_lines:
        return ValidationResult(
            result_name,
            "ERROR",
            f"SKILL.md has {total_lines} lines, exceeds maximum of {max_lines}",
            details,
        )
    return ValidationResult(result_name, "PASS", f"SKILL.md line count {total_lines} within limit {max_lines}", details)


def run_validation(skill_root, fmt, verbose):
    skill_md_path = skill_root / "SKILL.md"
    if not skill_md_path.exists():
        print(f"ERROR: SKILL.md not found at {skill_md_path}", file=sys.stderr)
        sys.exit(1)
    try:
        content = skill_md_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"ERROR: Cannot read SKILL.md: {e}", file=sys.stderr)
        sys.exit(1)
    checks = [
        check_frontmatter(skill_md_path, content, verbose),
        check_line_budget(content, verbose),
        check_core_rules(content, verbose),
        check_reference_paths(skill_md_path, content, verbose),
        check_phase_index(content, verbose),
        check_command_index(skill_md_path, content, verbose),
        check_quality_gate_consistency(skill_md_path, content, verbose),
        check_skill_md_line_count(content, verbose),
    ]
    total = len(checks)
    passed = sum(1 for c in checks if c.status == "PASS")
    warned = sum(1 for c in checks if c.status == "WARN")
    errored = sum(1 for c in checks if c.status == "ERROR")
    if fmt == "json":
        output = {
            "skill_root": str(skill_root),
            "checks": [c.to_dict() for c in checks],
            "summary": {
                "total": total,
                "passed": passed,
                "warnings": warned,
                "errors": errored,
            },
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print(f"SKILL.md Validation Report")
        print(f"{'=' * 60}")
        print(f"Root: {skill_root}")
        print()
        for c in checks:
            status_mark = {"PASS": "[PASS]", "WARN": "[WARN]", "ERROR": "[FAIL]"}
            mark = status_mark.get(c.status, "[????]")
            print(f"{mark} {c.name}")
            print(f"       {c.message}")
            for d in c.details:
                print(f"       {d}")
            print()
        print(f"{'=' * 60}")
        print(f"Summary: {total} checks | {passed} passed | {warned} warnings | {errored} errors")
    return 1 if errored > 0 else 0


def main():
    parser = argparse.ArgumentParser(
        description="Validate SKILL.md structure per xuansto-skill 8.6.5 requirements"
    )
    parser.add_argument(
        "--skill-root",
        type=str,
        default=None,
        help="Path to the skill root directory (default: parent of this script's location)",
    )
    parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        default=False,
        help="Show detailed information for each check",
    )
    args = parser.parse_args()
    if args.skill_root:
        skill_root = Path(args.skill_root).resolve()
    else:
        script_dir = Path(__file__).resolve().parent
        skill_root = script_dir.parent
    if not skill_root.exists():
        print(f"ERROR: Skill root not found: {skill_root}", file=sys.stderr)
        sys.exit(1)
    exit_code = run_validation(skill_root, args.format, args.verbose)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
