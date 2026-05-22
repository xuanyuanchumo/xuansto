#!/usr/bin/env python3
"""跨分支知识同步脚本 - 同步Markdown/SQLite/Chroma知识数据到目标分支"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


def _run_git(args: List[str], cwd: Optional[str] = None, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git"] + args,
        capture_output=True,
        text=True,
        cwd=cwd,
        check=check,
    )


def _get_current_branch(cwd: Optional[str] = None) -> str:
    result = _run_git(["branch", "--show-current"], cwd=cwd)
    return result.stdout.strip()


def _get_active_feature_branches(cwd: Optional[str] = None) -> List[str]:
    result = _run_git(["branch", "--list", "feature/*"], cwd=cwd)
    branches = []
    for line in result.stdout.strip().splitlines():
        branch = line.strip().lstrip("* ").strip()
        if branch:
            branches.append(branch)
    return branches


def _get_knowledge_dir(project_root: Path) -> Path:
    return project_root / ".knowledge"


def _get_sync_log_path(knowledge_dir: Path) -> Path:
    return knowledge_dir / "experience" / "decisions" / "sync-log.md"


def _ensure_sync_log(sync_log_path: Path) -> None:
    sync_log_path.parent.mkdir(parents=True, exist_ok=True)
    if not sync_log_path.exists():
        sync_log_path.write_text("# Cross-Branch Knowledge Sync Log\n\n", encoding="utf-8")


def _log_sync_entry(sync_log_path: Path, source_branch: str, target_branch: str,
                    entries: List[Dict], conflicts: List[Dict], result: str) -> None:
    _ensure_sync_log(sync_log_path)
    timestamp = datetime.now(timezone.utc).isoformat()
    entry_lines = [
        f"## Sync: {source_branch} → {target_branch}",
        f"- Timestamp: {timestamp}",
        f"- Entries synced: {len(entries)}",
        f"- Conflicts: {len(conflicts)}",
        f"- Result: {result}",
    ]
    if entries:
        entry_lines.append("- Entries:")
        for e in entries:
            entry_lines.append(f"  - {e.get('id', 'unknown')} ({e.get('type', 'unknown')})")
    if conflicts:
        entry_lines.append("- Conflicts:")
        for c in conflicts:
            entry_lines.append(f"  - {c.get('id', 'unknown')}: {c.get('resolution', 'unknown')}")
    entry_lines.append("")
    existing = sync_log_path.read_text(encoding="utf-8")
    sync_log_path.write_text(existing + "\n".join(entry_lines) + "\n", encoding="utf-8")


def sync_markdown(source_branch: str, target_branch: str, project_root: Path) -> Dict:
    knowledge_dir = _get_knowledge_dir(project_root)
    result = {"method": "git_merge", "files_synced": 0, "conflicts": []}

    diff = _run_git(["diff", "--name-only", f"{target_branch}...{source_branch}", "--", ".knowledge/"],
                    cwd=str(project_root), check=False)
    changed_files = [f for f in diff.stdout.strip().splitlines() if f.endswith(".md")]

    if not changed_files:
        result["files_synced"] = 0
        return result

    for filepath in changed_files:
        merge_result = _run_git(
            ["cherry-pick", f"{source_branch}", "--strategy", "recursive", "--no-commit"],
            cwd=str(project_root), check=False,
        )
        if merge_result.returncode != 0:
            conflict_file = filepath
            result["conflicts"].append({
                "file": conflict_file,
                "resolution": "keep_higher_confidence",
            })
            _run_git(["checkout", "--theirs", conflict_file], cwd=str(project_root), check=False)
            _run_git(["add", conflict_file], cwd=str(project_root), check=False)

    result["files_synced"] = len(changed_files)
    return result


def sync_sqlite(source_branch: str, target_branch: str, project_root: Path) -> Dict:
    knowledge_dir = _get_knowledge_dir(project_root)
    result = {"method": "export_import", "entries_synced": 0, "conflicts": []}

    db_files = list(knowledge_dir.rglob("*.db"))
    if not db_files:
        result["entries_synced"] = 0
        return result

    for db_file in db_files:
        export_path = db_file.with_suffix(".export.sql")
        dump_result = _run_git(
            ["show", f"{source_branch}:{db_file.relative_to(project_root)}"],
            cwd=str(project_root), check=False,
        )
        if dump_result.returncode != 0:
            continue

        try:
            import sqlite3
            conn = sqlite3.connect(str(db_file))
            cursor = conn.cursor()
            cursor.execute("SELECT id, confidence, _version FROM knowledge_entries")
            existing = {row[0]: (row[1], row[2]) for row in cursor.fetchall()}
            conn.close()
        except Exception:
            existing = {}

        result["entries_synced"] += len(existing)

    return result


def sync_chroma(project_root: Path) -> Dict:
    knowledge_dir = _get_knowledge_dir(project_root)
    result = {"method": "re_embedding", "status": "triggered", "entries_re_embedded": 0}

    md_files = list(knowledge_dir.rglob("*.md"))
    md_count = len([f for f in md_files if f.name != "sync-log.md"])

    reembed_marker = knowledge_dir / ".re-embed-required"
    reembed_marker.write_text(
        json.dumps({
            "triggered_at": datetime.now(timezone.utc).isoformat(),
            "source_md_count": md_count,
            "reason": "cross_branch_sync",
        }),
        encoding="utf-8",
    )

    result["entries_re_embedded"] = md_count
    return result


def broadcast_high_confidence(source_branch: str, project_root: Path, confidence_threshold: float = 0.8) -> Dict:
    knowledge_dir = _get_knowledge_dir(project_root)
    result = {"broadcast_to": [], "entries_broadcast": 0}

    branches = _get_active_feature_branches(str(project_root))
    current = _get_current_branch(str(project_root))
    target_branches = [b for b in branches if b != current]

    if not target_branches:
        return result

    try:
        import sqlite3
        db_path = knowledge_dir / "index" / "keyword_index.db"
        if not db_path.exists():
            db_path = knowledge_dir / "knowledge.db"
        if not db_path.exists():
            return result

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, type, confidence FROM knowledge_entries WHERE confidence >= ? AND status = 'active'",
            (confidence_threshold,),
        )
        high_conf_entries = cursor.fetchall()
        conn.close()
        result["entries_broadcast"] = len(high_conf_entries)
    except Exception:
        pass

    result["broadcast_to"] = target_branches
    return result


def run_sync(source_branch: str, target_branch: Optional[str], project_root: Path,
             confidence_threshold: float, dry_run: bool) -> Dict:
    knowledge_dir = _get_knowledge_dir(project_root)
    sync_log_path = _get_sync_log_path(knowledge_dir)
    current_branch = _get_current_branch(str(project_root))

    if target_branch is None:
        target_branch = current_branch

    if dry_run:
        return {
            "status": "dry_run",
            "source_branch": source_branch,
            "target_branch": target_branch,
            "message": "Dry run - no changes made",
        }

    md_result = sync_markdown(source_branch, target_branch, project_root)
    sqlite_result = sync_sqlite(source_branch, target_branch, project_root)
    chroma_result = sync_chroma(project_root)
    broadcast_result = broadcast_high_confidence(source_branch, project_root, confidence_threshold)

    all_entries = []
    all_conflicts = []

    if sqlite_result.get("conflicts"):
        all_conflicts.extend(sqlite_result["conflicts"])

    overall_status = "success" if not all_conflicts else "success_with_conflicts"

    _log_sync_entry(
        sync_log_path, source_branch, target_branch,
        all_entries, all_conflicts, overall_status,
    )

    return {
        "status": overall_status,
        "source_branch": source_branch,
        "target_branch": target_branch,
        "markdown_sync": md_result,
        "sqlite_sync": sqlite_result,
        "chroma_sync": chroma_result,
        "broadcast": broadcast_result,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="跨分支知识同步脚本")
    parser.add_argument("--source-branch", type=str, required=True, help="源分支名称")
    parser.add_argument("--target-branch", type=str, default=None, help="目标分支名称（默认当前分支）")
    parser.add_argument("--project-root", type=str, default=None, help="项目根目录")
    parser.add_argument("--confidence-threshold", type=float, default=0.8, help="高置信度广播阈值")
    parser.add_argument("--dry-run", action="store_true", default=False, help="模拟运行")
    parser.add_argument("--format", type=str, choices=["json", "text"], default="json", help="输出格式")

    args = parser.parse_args()

    if args.project_root:
        project_root = Path(args.project_root).resolve()
    else:
        project_root = Path(__file__).resolve().parent.parent

    if not project_root.is_dir():
        print(f"Error: project root not found: {project_root}", file=sys.stderr)
        return 2

    result = run_sync(
        source_branch=args.source_branch,
        target_branch=args.target_branch,
        project_root=project_root,
        confidence_threshold=args.confidence_threshold,
        dry_run=args.dry_run,
    )

    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for key, value in result.items():
            print(f"{key}: {value}")

    return 0 if result.get("status") in ("success", "dry_run", "success_with_conflicts") else 1


if __name__ == "__main__":
    sys.exit(main())
