#!/usr/bin/env python3

import argparse
import json
import os
import re
import sys


def read_file(path):
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def extract_field(content, field_name):
    pattern = rf"- \*\*{re.escape(field_name)}\*\*:\s*(.+)"
    match = re.search(pattern, content)
    return match.group(1).strip() if match else "N/A"


def extract_phase_status(content):
    phases = {}
    in_phase_table = False
    for line in content.splitlines():
        if "| Phase" in line and "| Name" in line and "| Status" in line:
            in_phase_table = True
            continue
        if in_phase_table:
            if line.startswith("|") and not line.startswith("|---") and not line.startswith("| -"):
                parts = [p.strip() for p in line.split("|")]
                parts = [p for p in parts if p]
                if len(parts) >= 3:
                    phase = parts[0]
                    name = parts[1]
                    status = parts[2]
                    phases[phase] = {"name": name, "status": status}
            elif not line.startswith("|"):
                in_phase_table = False
    return phases


def extract_table_rows(content, section_header):
    rows = []
    in_section = False
    in_table = False
    for line in content.splitlines():
        if section_header in line:
            in_section = True
            continue
        if in_section:
            if line.startswith("|") and "---" in line:
                in_table = True
                continue
            if in_table:
                if line.startswith("|"):
                    parts = [p.strip() for p in line.split("|")]
                    parts = [p for p in parts if p]
                    if parts:
                        rows.append(parts)
                else:
                    in_table = False
                    in_section = False
    return rows


def extract_progress_pct(content):
    progress_str = extract_field(content, "Progress")
    match = re.search(r"(\d+)", progress_str)
    return int(match.group(1)) if match else 0


def analyze_test_results(progress_content):
    if not progress_content:
        return {"total_suites": 0, "total_tests": 0, "passed": 0, "failed": 0, "skipped": 0}

    rows = extract_table_rows(progress_content, "Test Results")
    total_suites = len(rows)
    total_tests = 0
    passed = 0
    failed = 0
    skipped = 0

    for row in rows:
        try:
            if len(row) >= 6:
                total_tests += int(row[2])
                passed += int(row[3])
                failed += int(row[4])
                skipped += int(row[5])
        except (ValueError, IndexError):
            pass

    return {
        "total_suites": total_suites,
        "total_tests": total_tests,
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
    }


def analyze_modified_files(progress_content):
    if not progress_content:
        return []

    rows = extract_table_rows(progress_content, "Modified Files")
    files = []
    for row in rows:
        if len(row) >= 2:
            files.append({
                "path": row[1],
                "change_type": row[2] if len(row) > 2 else "N/A",
            })
    return files


def calculate_completion(phases):
    total = len(phases)
    if total == 0:
        return 0

    completed = sum(1 for p in phases.values() if p["status"].lower() in ("completed", "done"))
    return round((completed / total) * 100, 1)


def build_text_report(task_name, task_plan, progress_content):
    lines = []
    lines.append("=" * 50)
    lines.append("Task Completion Report")
    lines.append("=" * 50)
    lines.append("")

    if not task_plan:
        lines.append("Error: task_plan.md not found or empty")
        return "\n".join(lines)

    current_phase = extract_field(task_plan, "Current Phase")
    progress_pct = extract_progress_pct(task_plan)
    phases = extract_phase_status(task_plan)
    calculated_pct = calculate_completion(phases)

    lines.append(f"Task Name: {task_name}")
    lines.append(f"Current Phase: {current_phase}")
    lines.append(f"Declared Progress: {progress_pct}%")
    lines.append(f"Calculated Completion: {calculated_pct}%")
    lines.append("")

    lines.append("--- Phase Status ---")
    for phase, info in phases.items():
        status = info["status"]
        name = info["name"]
        marker = "[DONE]" if status.lower() in ("completed", "done") else \
                 "[ACTIVE]" if status.lower() in ("in progress", "active") else \
                 "[PENDING]"
        lines.append(f"  {marker} {phase} ({name}): {status}")
    lines.append("")

    test_info = analyze_test_results(progress_content)
    lines.append("--- Test Results ---")
    lines.append(f"  Test Suites: {test_info['total_suites']}")
    lines.append(f"  Total Tests: {test_info['total_tests']}")
    lines.append(f"  Passed: {test_info['passed']}")
    lines.append(f"  Failed: {test_info['failed']}")
    lines.append(f"  Skipped: {test_info['skipped']}")
    if test_info["total_tests"] > 0:
        pass_rate = round((test_info["passed"] / test_info["total_tests"]) * 100, 1)
        lines.append(f"  Pass Rate: {pass_rate}%")
    lines.append("")

    modified = analyze_modified_files(progress_content)
    lines.append("--- Modified Files ---")
    if modified:
        for mf in modified:
            lines.append(f"  [{mf['change_type']}] {mf['path']}")
    else:
        lines.append("  (none)")
    lines.append("")

    lines.append("=" * 50)

    return "\n".join(lines)


def build_json_report(task_name, task_plan, progress_content):
    data = {
        "task_name": task_name,
    }

    if not task_plan:
        data["error"] = "task_plan.md not found"
        return json.dumps(data, ensure_ascii=False, indent=2)

    current_phase = extract_field(task_plan, "Current Phase")
    progress_pct = extract_progress_pct(task_plan)
    phases = extract_phase_status(task_plan)
    calculated_pct = calculate_completion(phases)

    data["current_phase"] = current_phase
    data["declared_progress"] = progress_pct
    data["calculated_completion"] = calculated_pct

    phase_list = []
    for phase, info in phases.items():
        phase_list.append({
            "phase": phase,
            "name": info["name"],
            "status": info["status"],
        })
    data["phases"] = phase_list

    data["test_results"] = analyze_test_results(progress_content)
    data["modified_files"] = analyze_modified_files(progress_content)

    return json.dumps(data, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description="Check task completion status and generate progress report"
    )
    parser.add_argument(
        "--task-name",
        required=True,
        help="Task name to check completion for",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    args = parser.parse_args()

    base_dir = os.path.join(".agent_cache", args.task_name)

    if not os.path.isdir(base_dir):
        print(f"Error: Session directory not found: {base_dir}")
        sys.exit(1)

    task_plan = read_file(os.path.join(base_dir, "task_plan.md"))
    progress_content = read_file(os.path.join(base_dir, "progress.md"))

    if task_plan is None:
        print(f"Error: task_plan.md not found in {base_dir}")
        sys.exit(1)

    if args.format == "json":
        output = build_json_report(args.task_name, task_plan, progress_content)
    else:
        output = build_text_report(args.task_name, task_plan, progress_content)

    print(output)
    sys.exit(0)


if __name__ == "__main__":
    main()
