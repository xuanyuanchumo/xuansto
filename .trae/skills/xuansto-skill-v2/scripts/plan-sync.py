#!/usr/bin/env python3

import argparse
import os
import re
import shutil
import sys
from datetime import datetime, timezone


ARCHIVE_BASE_DIR = os.path.join(".knowledge", "workflow-checkpoints")
CACHE_DIR = ".agent_cache"
CORE_FILES = ["task_plan.md", "findings.md", "progress.md"]


def read_file(path):
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def extract_field(content, field_name):
    pattern = rf"- \*\*{re.escape(field_name)}\*\*:\s*(.+)"
    match = re.search(pattern, content)
    return match.group(1).strip() if match else "N/A"


def validate_phase(phase_str):
    match = re.match(r"^phase[_-]?(\d+)$", phase_str, re.IGNORECASE)
    if match:
        return f"phase-{match.group(1)}"
    match = re.match(r"^(\d+)$", phase_str)
    if match:
        return f"phase-{match.group(1)}"
    return None


def main():
    parser = argparse.ArgumentParser(
        description="Archive session planning files to workflow checkpoints on phase completion"
    )
    parser.add_argument(
        "--task-name",
        required=True,
        help="Task name whose session files should be archived",
    )
    parser.add_argument(
        "--phase",
        required=True,
        help="Phase number to archive (e.g., '1', 'phase-1', 'phase_1')",
    )
    args = parser.parse_args()

    normalized_phase = validate_phase(args.phase)
    if normalized_phase is None:
        print(f"Error: Invalid phase format: {args.phase}")
        print("Expected formats: '1', 'phase-1', 'phase_1'")
        sys.exit(1)

    source_dir = os.path.join(CACHE_DIR, args.task_name)
    if not os.path.isdir(source_dir):
        print(f"Error: Session directory not found: {source_dir}")
        sys.exit(1)

    archive_dir = os.path.join(ARCHIVE_BASE_DIR, normalized_phase)
    os.makedirs(archive_dir, exist_ok=True)

    task_subdir = os.path.join(archive_dir, args.task_name)
    os.makedirs(task_subdir, exist_ok=True)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    archived_files = []
    for filename in CORE_FILES:
        src = os.path.join(source_dir, filename)
        if os.path.isfile(src):
            dst = os.path.join(task_subdir, filename)
            shutil.copy2(src, dst)
            archived_files.append(filename)
        else:
            print(f"Warning: Source file not found, skipping: {src}")

    manifest_path = os.path.join(task_subdir, "archive-manifest.md")
    task_plan_content = read_file(os.path.join(source_dir, "task_plan.md"))
    current_phase = extract_field(task_plan_content, "Current Phase") if task_plan_content else "N/A"

    manifest_content = (
        f"# Archive Manifest\n\n"
        f"- **Task Name**: {args.task_name}\n"
        f"- **Phase**: {normalized_phase}\n"
        f"- **Current Phase (at archive time)**: {current_phase}\n"
        f"- **Archived At**: {now}\n"
        f"- **Archived Files**: {', '.join(archived_files)}\n"
        f"- **Source Directory**: {source_dir}\n"
    )
    with open(manifest_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(manifest_content)

    print(f"Archive completed successfully.")
    print(f"  Phase: {normalized_phase}")
    print(f"  Task: {args.task_name}")
    print(f"  Archive directory: {task_subdir}")
    print(f"  Archived files: {', '.join(archived_files)}")
    print(f"  Archived at: {now}")
    print(f"  Source files preserved (not deleted).")

    sys.exit(0)


if __name__ == "__main__":
    main()
