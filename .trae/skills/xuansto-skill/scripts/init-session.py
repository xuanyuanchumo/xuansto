#!/usr/bin/env python3

import argparse
import os
import sys
from datetime import datetime, timezone


TASK_PLAN_TEMPLATE = """# Task Plan

- **Task Name**: {task_name}
- **Created At**: {created_at}
- **Current Phase**: Phase 0
- **Progress**: 0%

## Phase Status

| Phase | Name | Status |
|-------|------|--------|
| Phase 0 | Design | Pending |
| Phase 1 | Requirements | Pending |
| Phase 2 | Architecture | Pending |
| Phase 3 | Test Design | Pending |
| Phase 4 | Implementation | Pending |
| Phase 5 | Test Verification | Pending |
| Phase 6 | Acceptance | Pending |
| Phase 7 | Iteration | Pending |
| Phase 8 | Desktop | Pending |

## Decision Log

| # | Decision | Rationale | Timestamp |
|---|----------|-----------|-----------|
"""

FINDINGS_TEMPLATE = """# Findings

- **Task Name**: {task_name}

## Research Log

| # | Topic | Source | Key Insight | Timestamp |
|---|-------|--------|-------------|-----------|

## Discoveries

| # | Finding | Impact | Confidence | Timestamp |
|---|---------|--------|------------|-----------|

## Technical Decisions

| # | Decision | Alternatives Considered | Chosen Because | Timestamp |
|---|----------|------------------------|----------------|-----------|
"""

PROGRESS_TEMPLATE = """# Progress

- **Task Name**: {task_name}

## Session Log

| # | Session | Phase | Actions Taken | Timestamp |
|---|---------|-------|---------------|-----------|

## Test Results

| # | Test Suite | Total | Passed | Failed | Skipped | Timestamp |
|---|------------|-------|--------|--------|---------|-----------|

## Modified Files

| # | File Path | Change Type | Description | Timestamp |
|---|-----------|-------------|-------------|-----------|
"""


def create_file(path, content):
    try:
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
    except OSError as e:
        print(f"Error creating file '{path}': {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Initialize session cache directory and planning files"
    )
    parser.add_argument(
        "--task-name",
        required=True,
        help="Task name for the session (used as directory name under .agent_cache)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force overwrite if the session directory already exists",
    )
    args = parser.parse_args()

    base_dir = os.path.join(".agent_cache", args.task_name)

    if os.path.exists(base_dir):
        if not args.force:
            print(f"Error: Session directory already exists: {base_dir}")
            print("Use --force to overwrite.")
            sys.exit(1)
    else:
        os.makedirs(base_dir, exist_ok=True)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    template_vars = {
        "task_name": args.task_name,
        "created_at": now,
    }

    files = {
        "task_plan.md": TASK_PLAN_TEMPLATE.format(**template_vars),
        "findings.md": FINDINGS_TEMPLATE.format(**template_vars),
        "progress.md": PROGRESS_TEMPLATE.format(**template_vars),
    }

    for filename, content in files.items():
        filepath = os.path.join(base_dir, filename)
        create_file(filepath, content)
        print(f"Created: {filepath}")

    print(f"\nSession initialized: {base_dir}")
    print(f"Task name: {args.task_name}")
    print(f"Created at: {now}")

    sys.exit(0)


if __name__ == "__main__":
    main()
