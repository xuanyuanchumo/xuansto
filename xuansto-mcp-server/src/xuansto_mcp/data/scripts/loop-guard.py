#!/usr/bin/env python3

import argparse
import os
import re
import sys
from datetime import datetime, timezone


CACHE_DIR = ".agent_cache"
LOOP_STATE_FILENAME = "loop-state.md"

LOOP_STATE_TEMPLATE = """---
task_name: "{task_name}"
status: "active"
original_prompt: "{original_prompt}"
completion_promise: "{completion_promise}"
completion_criteria: "{completion_criteria}"
max_iterations: {max_iterations}
current_iteration: 0
stagnation_count: 0
stagnant: false
started_at: "{started_at}"
last_updated_at: "{started_at}"
---

# Loop Iteration History

| # | Iteration | Description | Progress | Stagnant | Timestamp |
|---|-----------|-------------|----------|----------|-----------|
"""


def read_file(path):
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_file(path, content):
    try:
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
    except OSError as e:
        print(f"Error writing file '{path}': {e}")
        sys.exit(1)


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


def update_frontmatter_field(content, field, value):
    if isinstance(value, bool):
        str_val = "true" if value else "false"
    elif isinstance(value, int):
        str_val = str(value)
    else:
        str_val = f'"{value}"'

    pattern = rf'^({re.escape(field)}\s*:\s*).*$'
    new_line = f"{field}: {str_val}"

    lines = content.split("\n")
    in_frontmatter = False
    updated = False
    new_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped == "---" and not in_frontmatter:
            in_frontmatter = True
            new_lines.append(line)
            continue
        if stripped == "---" and in_frontmatter:
            in_frontmatter = False
            new_lines.append(line)
            continue
        if in_frontmatter and not updated:
            if re.match(pattern, line):
                new_lines.append(new_line)
                updated = True
                continue
        new_lines.append(line)

    return "\n".join(new_lines)


def get_loop_state_path(task_name):
    return os.path.join(CACHE_DIR, task_name, LOOP_STATE_FILENAME)


def do_init(args):
    base_dir = os.path.join(CACHE_DIR, args.task_name)
    if not os.path.isdir(base_dir):
        os.makedirs(base_dir, exist_ok=True)

    state_path = get_loop_state_path(args.task_name)
    if os.path.isfile(state_path) and not args.force:
        print(f"Error: loop-state.md already exists: {state_path}")
        print("Use --force to overwrite.")
        sys.exit(1)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    content = LOOP_STATE_TEMPLATE.format(
        task_name=args.task_name,
        original_prompt=args.original_prompt,
        completion_promise=args.completion_promise,
        completion_criteria=args.completion_criteria,
        max_iterations=args.max_iterations,
        started_at=now,
    )

    write_file(state_path, content)
    print(f"Loop state initialized: {state_path}")
    print(f"  Task: {args.task_name}")
    print(f"  Max iterations: {args.max_iterations}")
    print(f"  Completion promise: {args.completion_promise}")
    print(f"  Started at: {now}")


def do_status(args):
    state_path = get_loop_state_path(args.task_name)
    content = read_file(state_path)
    if content is None:
        print(f"Error: loop-state.md not found: {state_path}")
        sys.exit(1)

    fm = parse_frontmatter(content)

    status = fm.get("status", "unknown")
    current_iter = int(fm.get("current_iteration", 0))
    max_iter = int(fm.get("max_iterations", 50))
    stag_count = int(fm.get("stagnation_count", 0))
    stagnant = fm.get("stagnant", "false").lower() == "true"

    progress_pct = round((current_iter / max_iter) * 100, 1) if max_iter > 0 else 0

    print(f"Loop Status: {status}")
    print(f"  Task: {args.task_name}")
    print(f"  Current iteration: {current_iter}/{max_iter} ({progress_pct}%)")
    print(f"  Stagnation count: {stag_count}")
    print(f"  Stagnant: {stagnant}")
    print(f"  Original prompt: {fm.get('original_prompt', 'N/A')}")
    print(f"  Completion promise: {fm.get('completion_promise', 'N/A')}")
    print(f"  Started at: {fm.get('started_at', 'N/A')}")
    print(f"  Last updated: {fm.get('last_updated_at', 'N/A')}")

    if stagnant:
        print("  WARNING: Loop is stagnant (3+ consecutive iterations with no progress)")
    if status == "cancelled":
        print("  NOTICE: Loop has been cancelled")
    if status == "completed":
        print("  NOTICE: Loop has been completed")


def do_update(args):
    state_path = get_loop_state_path(args.task_name)
    content = read_file(state_path)
    if content is None:
        print(f"Error: loop-state.md not found: {state_path}")
        sys.exit(1)

    fm = parse_frontmatter(content)
    status = fm.get("status", "active")
    if status == "cancelled":
        print("Error: Cannot update a cancelled loop.")
        sys.exit(1)
    if status == "completed":
        print("Error: Cannot update a completed loop.")
        sys.exit(1)

    current_iter = int(fm.get("current_iteration", 0))
    max_iter = int(fm.get("max_iterations", 50))
    stag_count = int(fm.get("stagnation_count", 0))
    prev_progress = fm.get("_last_progress", "")

    new_iter = current_iter + 1
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    is_stagnant_iteration = False
    if args.progress_description and args.progress_description == prev_progress:
        stag_count += 1
        is_stagnant_iteration = True
    else:
        stag_count = 0

    is_stagnant = stag_count >= 3

    content = update_frontmatter_field(content, "current_iteration", new_iter)
    content = update_frontmatter_field(content, "stagnation_count", stag_count)
    content = update_frontmatter_field(content, "stagnant", is_stagnant)
    content = update_frontmatter_field(content, "last_updated_at", now)
    content = update_frontmatter_field(content, "_last_progress", args.progress_description or "")

    stag_marker = "YES" if is_stagnant_iteration else "no"
    iter_row = f"| {new_iter} | {new_iter} | {args.progress_description or '-'} | {args.progress or 'N/A'} | {stag_marker} | {now} |"

    lines = content.rstrip().split("\n")
    last_table_idx = -1
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].startswith("|") and not lines[i].startswith("|---"):
            last_table_idx = i
            break

    if last_table_idx >= 0:
        lines.insert(last_table_idx + 1, iter_row)
    else:
        lines.append(iter_row)

    content = "\n".join(lines)
    write_file(state_path, content)

    print(f"Loop updated: iteration {new_iter}/{max_iter}")
    print(f"  Progress: {args.progress or 'N/A'}")
    print(f"  Description: {args.progress_description or '-'}")
    print(f"  Stagnation count: {stag_count}")
    if is_stagnant:
        print("  WARNING: Loop marked as STAGNANT (3+ consecutive iterations with no progress)")

    if new_iter >= max_iter:
        print(f"  NOTICE: Maximum iterations reached ({max_iter})")


def do_cancel(args):
    state_path = get_loop_state_path(args.task_name)
    content = read_file(state_path)
    if content is None:
        print(f"Error: loop-state.md not found: {state_path}")
        sys.exit(1)

    fm = parse_frontmatter(content)
    status = fm.get("status", "active")
    if status == "cancelled":
        print("Loop is already cancelled.")
        sys.exit(0)
    if status == "completed":
        print("Loop is already completed. Cannot cancel.")
        sys.exit(1)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    content = update_frontmatter_field(content, "status", "cancelled")
    content = update_frontmatter_field(content, "last_updated_at", now)

    write_file(state_path, content)
    print(f"Loop cancelled: {args.task_name}")
    print(f"  Cancelled at: {now}")


def main():
    parser = argparse.ArgumentParser(
        description="Loop state management for autonomous iteration"
    )
    parser.add_argument(
        "--task-name",
        required=True,
        help="Task name (directory name under .agent_cache)",
    )

    subparsers = parser.add_subparsers(dest="action", required=True)

    init_parser = subparsers.add_parser("init", help="Initialize loop state")
    init_parser.add_argument(
        "--original-prompt",
        default="",
        help="Original user prompt for the loop task",
    )
    init_parser.add_argument(
        "--max-iterations",
        type=int,
        default=50,
        help="Maximum number of iterations (default: 50)",
    )
    init_parser.add_argument(
        "--completion-promise",
        default="DONE",
        help="Completion promise string (default: DONE)",
    )
    init_parser.add_argument(
        "--completion-criteria",
        default="",
        help="Completion criteria description",
    )
    init_parser.add_argument(
        "--force",
        action="store_true",
        help="Force overwrite if loop-state.md already exists",
    )

    status_parser = subparsers.add_parser("status", help="Show loop status")

    update_parser = subparsers.add_parser("update", help="Update loop iteration")
    update_parser.add_argument(
        "--progress",
        default="",
        help="Progress percentage or description",
    )
    update_parser.add_argument(
        "--progress-description",
        default="",
        help="Detailed description of current iteration progress",
    )

    cancel_parser = subparsers.add_parser("cancel", help="Cancel the loop")

    args = parser.parse_args()

    if args.action == "init":
        do_init(args)
    elif args.action == "status":
        do_status(args)
    elif args.action == "update":
        do_update(args)
    elif args.action == "cancel":
        do_cancel(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
