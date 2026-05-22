#!/usr/bin/env python3
"""
Review Eligibility Check - Determines if a target requires code review.
Skips: no changes, documentation-only changes, already-reviewed markers.
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path


DOC_EXTENSIONS = {
    ".md", ".txt", ".rst", ".adoc", ".html", ".css",
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico",
    ".pdf", ".doc", ".docx",
}

REVIEWED_MARKER_FILES = {
    ".reviewed",
    ".review-complete",
    "REVIEWED",
}

REVIEWED_MARKER_COMMENTS = {
    "reviewed",
    "review-complete",
    "no-review-needed",
    "skip-review",
}


def is_doc_only(file_paths: list) -> bool:
    if not file_paths:
        return True
    for fp in file_paths:
        ext = Path(fp).suffix.lower()
        if ext not in DOC_EXTENSIONS:
            return False
    return True


def has_reviewed_marker(target: str) -> bool:
    target_path = Path(target)

    for marker in REVIEWED_MARKER_FILES:
        marker_path = target_path / marker if target_path.is_dir() else target_path.parent / marker
        if marker_path.exists():
            return True

    if target_path.is_file():
        try:
            with open(target_path, "r", encoding="utf-8", errors="ignore") as f:
                first_lines = [f.readline().lower() for _ in range(5)]
                for line in first_lines:
                    for marker in REVIEWED_MARKER_COMMENTS:
                        if marker in line:
                            return True
        except (OSError, UnicodeDecodeError):
            pass

    return False


def get_changed_files(target: str) -> list:
    target_path = Path(target)
    if not target_path.exists():
        return []

    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            capture_output=True, text=True, timeout=30,
            cwd=str(target_path) if target_path.is_dir() else str(target_path.parent),
        )
        if result.returncode == 0 and result.stdout.strip():
            changed = [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]
            if target_path.is_dir():
                prefix = str(target_path).replace("\\", "/")
                if not prefix.endswith("/"):
                    prefix += "/"
                changed = [f for f in changed if f.startswith(prefix)]
            else:
                target_rel = str(target_path).replace("\\", "/")
                changed = [f for f in changed if f == target_rel]
            return changed
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass

    return []


def check_file_changes(target: str) -> list:
    target_path = Path(target)
    if target_path.is_file():
        return [str(target_path)]
    elif target_path.is_dir():
        files = []
        for root, _dirs, fnames in os.walk(target_path):
            for fname in fnames:
                fpath = Path(root) / fname
                if fpath.suffix.lower() not in DOC_EXTENSIONS:
                    files.append(str(fpath))
        return files
    return []


def check_eligibility(target: str) -> dict:
    target_path = Path(target)

    if not target_path.exists():
        return {
            "status": "ineligible",
            "reason": "target_does_not_exist",
            "detail": f"Target path does not exist: {target}",
        }

    changed_files = get_changed_files(target)
    if not changed_files:
        code_files = check_file_changes(target)
        if not code_files:
            return {
                "status": "ineligible",
                "reason": "no_code_files",
                "detail": "No code files found in target",
            }
        changed_files = code_files

    if is_doc_only(changed_files):
        return {
            "status": "ineligible",
            "reason": "doc_only_changes",
            "detail": "All changed files are documentation or asset files",
            "changed_files": changed_files,
        }

    if has_reviewed_marker(target):
        return {
            "status": "ineligible",
            "reason": "already_reviewed",
            "detail": "Review marker found indicating prior review completion",
        }

    code_changed = [f for f in changed_files if Path(f).suffix.lower() not in DOC_EXTENSIONS]
    return {
        "status": "eligible",
        "reason": "code_changes_detected",
        "detail": f"{len(code_changed)} code file(s) require review",
        "changed_files": changed_files,
        "code_files": code_changed,
    }


def parse_args():
    parser = argparse.ArgumentParser(
        description="Review Eligibility Check - Determine if target requires code review"
    )
    parser.add_argument(
        "--target",
        type=str,
        required=True,
        help="File path or directory to check for review eligibility",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    result = check_eligibility(args.target)
    output = {
        "timestamp": datetime.now().isoformat(),
        "target": args.target,
        "status": result["status"],
        "reason": result["reason"],
        "detail": result["detail"],
    }
    if "changed_files" in result:
        output["changed_files"] = result["changed_files"]
    if "code_files" in result:
        output["code_files"] = result["code_files"]

    print(json.dumps(output, ensure_ascii=False, indent=2))

    if result["status"] == "eligible":
        sys.exit(0)
    else:
        sys.exit(2)


if __name__ == "__main__":
    main()
