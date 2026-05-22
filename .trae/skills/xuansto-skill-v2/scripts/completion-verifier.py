#!/usr/bin/env python3
"""Verify completion promise, quality gates, and completion criteria.

Checks whether an autonomous loop task has met its completion promise string,
satisfied all defined completion criteria, and passed all blocking quality gates.
Produces text or JSON verification reports.
"""

import argparse
import json
import os
import re
import sys


CACHE_DIR = ".agent_cache"
LOOP_STATE_FILENAME = "loop-state.md"
PROGRESS_FILENAME = "progress.md"
QUALITY_GATES_PATH = os.path.join("references", "quality-gates.md")


def read_file(path):
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def parse_frontmatter(content):
    match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return {}
    fm_text = match.group(1)
    result = {}
    for line in fm_text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        match_kv = re.match(r'^(\w[\w_]*)\s*:\s*(.*)', line)
        if match_kv:
            key = match_kv.group(1)
            val = match_kv.group(2).strip().strip('"').strip("'")
            result[key] = val
    return result


def check_completion_promise(loop_content, output_text):
    fm = parse_frontmatter(loop_content)
    promise = fm.get("completion_promise", "DONE")
    if not promise:
        return {"met": False, "detail": f"No completion promise defined"}
    found = promise in (output_text or "")
    return {"met": found, "detail": f"Promise '{promise}' {'found' if found else 'NOT found'} in output"}


def check_completion_criteria(progress_content, loop_content):
    fm = parse_frontmatter(loop_content)
    criteria = fm.get("completion_criteria", "")
    if not criteria:
        return {"met": True, "detail": "No explicit completion criteria defined (auto-pass)"}

    criteria_items = [c.strip() for c in criteria.split(";") if c.strip()]
    if not criteria_items:
        return {"met": True, "detail": "No explicit completion criteria defined (auto-pass)"}

    unmet = []
    for item in criteria_items:
        if progress_content and item.lower() in progress_content.lower():
            continue
        unmet.append(item)

    if unmet:
        return {"met": False, "detail": f"Unmet criteria: {'; '.join(unmet)}"}
    return {"met": True, "detail": "All completion criteria met"}


def check_quality_gates(task_name):
    gates_content = read_file(QUALITY_GATES_PATH)
    if not gates_content:
        return {"met": True, "detail": "Quality gates file not found, skipping gate check", "gates": []}

    gate_blocks = re.findall(
        r'```yaml\s*\n(.*?)```',
        gates_content,
        re.DOTALL,
    )

    relevant_gates = []
    for block in gate_blocks:
        name_match = re.search(r'^\s*(?:名称|name)\s*:\s*(.+)', block, re.MULTILINE | re.IGNORECASE)
        level_match = re.search(r'^\s*(?:阻塞级别|block_level)\s*:\s*(.+)', block, re.MULTILINE | re.IGNORECASE)
        if name_match:
            gate_name = name_match.group(1).strip()
            block_level = level_match.group(1).strip() if level_match else "BLOCK"
            relevant_gates.append({"name": gate_name, "level": block_level})

    progress_path = os.path.join(CACHE_DIR, task_name, PROGRESS_FILENAME)
    progress_content = read_file(progress_path) or ""

    base_dir = os.path.join(CACHE_DIR, task_name)
    gate_results = []
    all_passed = True

    for gate in relevant_gates:
        gate_status_file = os.path.join(base_dir, f"gate-{gate['name'].lower().replace(' ', '-')}.status")
        status_content = read_file(gate_status_file)
        if status_content and "PASS" in status_content.upper():
            gate_results.append({"name": gate["name"], "level": gate["level"], "status": "PASS"})
        elif status_content and "FAIL" in status_content.upper():
            gate_results.append({"name": gate["name"], "level": gate["level"], "status": "FAIL"})
            if "BLOCK" in gate["level"].upper():
                all_passed = False
        else:
            gate_results.append({"name": gate["name"], "level": gate["level"], "status": "UNKNOWN"})

    failed_gates = [g for g in gate_results if g["status"] == "FAIL" and "BLOCK" in g["level"].upper()]
    if failed_gates:
        names = [g["name"] for g in failed_gates]
        return {"met": False, "detail": f"Blocking gates failed: {', '.join(names)}", "gates": gate_results}

    return {"met": all_passed, "detail": "All blocking quality gates passed" if all_passed else "Some gates have unknown status", "gates": gate_results}


def verify_completion(task_name, output_text=""):
    base_dir = os.path.join(CACHE_DIR, task_name)
    loop_path = os.path.join(base_dir, LOOP_STATE_FILENAME)
    progress_path = os.path.join(base_dir, PROGRESS_FILENAME)

    loop_content = read_file(loop_path)
    progress_content = read_file(progress_path)

    results = {
        "task_name": task_name,
        "checks": {},
        "complete": False,
        "missing": [],
    }

    if loop_content is None:
        results["checks"]["loop_state"] = {"met": False, "detail": "loop-state.md not found"}
        results["missing"].append("loop-state.md file")
        return results

    promise_check = check_completion_promise(loop_content, output_text)
    results["checks"]["completion_promise"] = promise_check
    if not promise_check["met"]:
        results["missing"].append(f"Completion promise: {promise_check['detail']}")

    criteria_check = check_completion_criteria(progress_content, loop_content)
    results["checks"]["completion_criteria"] = criteria_check
    if not criteria_check["met"]:
        results["missing"].append(f"Completion criteria: {criteria_check['detail']}")

    gates_check = check_quality_gates(task_name)
    results["checks"]["quality_gates"] = gates_check
    if not gates_check["met"]:
        results["missing"].append(f"Quality gates: {gates_check['detail']}")

    results["complete"] = (
        promise_check["met"]
        and criteria_check["met"]
        and gates_check["met"]
    )

    return results


def build_text_report(results):
    lines = []
    lines.append("=" * 50)
    lines.append("Completion Verification Report")
    lines.append("=" * 50)
    lines.append("")

    lines.append(f"Task: {results['task_name']}")
    status = "COMPLETE" if results["complete"] else "INCOMPLETE"
    lines.append(f"Status: {status}")
    lines.append("")

    lines.append("--- Check Results ---")
    for check_name, check_result in results["checks"].items():
        marker = "[PASS]" if check_result["met"] else "[FAIL]"
        lines.append(f"  {marker} {check_name}: {check_result['detail']}")
    lines.append("")

    if results["missing"]:
        lines.append("--- Missing Items ---")
        for item in results["missing"]:
            lines.append(f"  - {item}")
    else:
        lines.append("--- Missing Items ---")
        lines.append("  (none)")

    lines.append("")
    lines.append("=" * 50)
    return "\n".join(lines)


def build_json_report(results):
    return json.dumps(results, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description="Verify task completion for autonomous iteration loop"
    )
    parser.add_argument(
        "--task-name",
        required=True,
        help="Task name to verify completion for",
    )
    parser.add_argument(
        "--output-text",
        default="",
        help="Text output from the loop to check for completion promise",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    args = parser.parse_args()

    results = verify_completion(args.task_name, args.output_text)

    if args.format == "json":
        print(build_json_report(results))
    else:
        print(build_text_report(results))

    sys.exit(0 if results["complete"] else 1)


if __name__ == "__main__":
    main()
