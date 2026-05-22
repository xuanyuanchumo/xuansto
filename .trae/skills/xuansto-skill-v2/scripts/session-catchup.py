#!/usr/bin/env python3

import argparse
import json
import os
import re
import sys


def read_file(path):
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except OSError as e:
        print(f"Error reading file '{path}': {e}")
        return None


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
                    status = parts[2]
                    phases[phase] = status
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


def extract_progress(content):
    progress_str = extract_field(content, "Progress")
    match = re.search(r"(\d+)", progress_str)
    return int(match.group(1)) if match else 0


def build_text_summary(task_name, task_plan, findings, progress):
    lines = []
    lines.append("=" * 50)
    lines.append("Session Catchup Summary")
    lines.append("=" * 50)
    lines.append("")

    if task_plan:
        current_phase = extract_field(task_plan, "Current Phase")
        progress_pct = extract_progress(task_plan)
        phases = extract_phase_status(task_plan)

        lines.append(f"Task Name: {task_name}")
        lines.append(f"Current Phase: {current_phase}")
        lines.append(f"Progress: {progress_pct}%")
        lines.append("")

        completed = [p for p, s in phases.items() if s.lower() in ("completed", "done")]
        in_progress = [p for p, s in phases.items() if s.lower() in ("in progress", "active")]
        pending = [p for p, s in phases.items() if s.lower() == "pending"]

        lines.append("--- Completed Phases ---")
        for p in completed:
            lines.append(f"  [DONE] {p}")
        if not completed:
            lines.append("  (none)")

        lines.append("")
        lines.append("--- In Progress ---")
        for p in in_progress:
            lines.append(f"  [ACTIVE] {p}")
        if not in_progress:
            lines.append("  (none)")

        lines.append("")
        lines.append("--- Pending Phases ---")
        for p in pending:
            lines.append(f"  [PENDING] {p}")
        if not pending:
            lines.append("  (none)")
    else:
        lines.append("Task Name: N/A")
        lines.append("Warning: task_plan.md not found or empty")

    lines.append("")

    if findings:
        research_rows = extract_table_rows(findings, "Research Log")
        discovery_rows = extract_table_rows(findings, "Discoveries")
        decision_rows = extract_table_rows(findings, "Technical Decisions")

        lines.append(f"Research Entries: {len(research_rows)}")
        lines.append(f"Discoveries: {len(discovery_rows)}")
        lines.append(f"Technical Decisions: {len(decision_rows)}")
    else:
        lines.append("Findings: (file not found)")

    lines.append("")

    if progress:
        session_rows = extract_table_rows(progress, "Session Log")
        test_rows = extract_table_rows(progress, "Test Results")
        file_rows = extract_table_rows(progress, "Modified Files")

        lines.append(f"Session Entries: {len(session_rows)}")
        lines.append(f"Test Results: {len(test_rows)}")
        lines.append(f"Modified Files: {len(file_rows)}")
    else:
        lines.append("Progress: (file not found)")

    lines.append("")
    lines.append("=" * 50)

    return "\n".join(lines)


def build_json_summary(task_name, task_plan, findings, progress):
    data = {
        "task_name": task_name,
    }

    if task_plan:
        current_phase = extract_field(task_plan, "Current Phase")
        progress_pct = extract_progress(task_plan)
        phases = extract_phase_status(task_plan)

        completed = [p for p, s in phases.items() if s.lower() in ("completed", "done")]
        in_progress = [p for p, s in phases.items() if s.lower() in ("in progress", "active")]
        pending = [p for p, s in phases.items() if s.lower() == "pending"]

        data["current_phase"] = current_phase
        data["progress"] = progress_pct
        data["completed_phases"] = completed
        data["in_progress_phases"] = in_progress
        data["pending_phases"] = pending
    else:
        data["error"] = "task_plan.md not found"

    if findings:
        data["research_count"] = len(extract_table_rows(findings, "Research Log"))
        data["discoveries_count"] = len(extract_table_rows(findings, "Discoveries"))
        data["decisions_count"] = len(extract_table_rows(findings, "Technical Decisions"))

    if progress:
        data["session_count"] = len(extract_table_rows(progress, "Session Log"))
        data["test_results_count"] = len(extract_table_rows(progress, "Test Results"))
        data["modified_files_count"] = len(extract_table_rows(progress, "Modified Files"))

    return json.dumps(data, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description="Recover session context after /clear by reading planning files"
    )
    parser.add_argument(
        "--task-name",
        required=True,
        help="Task name to recover session for",
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
    findings = read_file(os.path.join(base_dir, "findings.md"))
    progress = read_file(os.path.join(base_dir, "progress.md"))

    if task_plan is None and findings is None and progress is None:
        print(f"Error: No planning files found in {base_dir}")
        sys.exit(1)

    if args.format == "json":
        output = build_json_summary(args.task_name, task_plan, findings, progress)
    else:
        output = build_text_summary(args.task_name, task_plan, findings, progress)

    print(output)
    sys.exit(0)


if __name__ == "__main__":
    main()
