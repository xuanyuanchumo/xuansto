#!/usr/bin/env python3
"""脚本清理检查器 - 扫描临时脚本目录，检测残留文件、命名合规性和过期文件"""

import argparse
import json
import re
import sys
import time
from pathlib import Path

RESIDUAL_EXTENSIONS = {".py", ".js", ".ps1"}
SHELL_EXTENSIONS = {".sh"}
GITKEEP = ".gitkeep"

SCRIPT_NAME_PATTERN = re.compile(
    r"^[a-zA-Z0-9_-]+-[a-f0-9]{6,}-\d{10,}\.(py|js|ps1|sh|ts)$"
)

EXPIRY_SECONDS = 24 * 60 * 60

SCAN_DIRS = [
    ".knowledge/temp-scripts",
    ".temp-scripts",
]


def check_filename_compliance(filename: str) -> bool:
    return bool(SCRIPT_NAME_PATTERN.match(filename))


def is_expired(file_path: Path, now: float) -> bool:
    try:
        mtime = file_path.stat().st_mtime
        return (now - mtime) > EXPIRY_SECONDS
    except OSError:
        return False


def scan_directory(temp_dir: Path, now: float) -> dict:
    if not temp_dir.exists() or not temp_dir.is_dir():
        return {
            "exists": False,
            "total_files": 0,
            "compliant_files": 0,
            "non_compliant_files": 0,
            "expired_files": 0,
            "residual_files": [],
            "non_compliant_list": [],
            "expired_list": [],
        }

    all_files = [f for f in temp_dir.rglob("*") if f.is_file() and f.name != GITKEEP]

    residual_files = [f for f in all_files if f.suffix in RESIDUAL_EXTENSIONS | SHELL_EXTENSIONS]
    compliant = []
    non_compliant = []
    expired = []

    for f in residual_files:
        if not check_filename_compliance(f.name):
            non_compliant.append(f.name)
        else:
            compliant.append(f.name)

        if is_expired(f, now):
            expired.append(f.name)

    return {
        "exists": True,
        "total_files": len(residual_files),
        "compliant_files": len(compliant),
        "non_compliant_files": len(non_compliant),
        "expired_files": len(expired),
        "residual_files": [f.name for f in residual_files],
        "non_compliant_list": non_compliant,
        "expired_list": expired,
    }


def auto_clean_expired(temp_dir: Path, now: float) -> list[str]:
    if not temp_dir.exists() or not temp_dir.is_dir():
        return []

    cleaned = []
    for f in temp_dir.rglob("*"):
        if f.is_file() and f.name != GITKEEP and is_expired(f, now):
            try:
                f.unlink()
                cleaned.append(f.name)
            except OSError:
                pass

    return cleaned


def build_report(dirs_data: list[dict], cleaned_files: list[str]) -> dict:
    total = sum(d["total_files"] for d in dirs_data)
    compliant = sum(d["compliant_files"] for d in dirs_data)
    non_compliant = sum(d["non_compliant_files"] for d in dirs_data)
    expired = sum(d["expired_files"] for d in dirs_data)

    has_non_compliant = non_compliant > 0
    has_expired = expired > 0

    if has_non_compliant:
        status = "FAIL"
    elif has_expired:
        status = "WARN"
    else:
        status = "PASS"

    report = {
        "status": status,
        "total_files": total,
        "compliant_files": compliant,
        "non_compliant_files": non_compliant,
        "expired_files": expired,
        "cleaned_files": len(cleaned_files),
        "cleaned_list": cleaned_files,
        "directories": dirs_data,
    }

    if has_non_compliant:
        report["error"] = "存在命名不合规的临时脚本"
    if has_expired:
        report["warning"] = "存在超过24小时的过期临时脚本"

    return report


def format_text_report(report: dict) -> str:
    lines = []
    lines.append("=" * 50)
    lines.append("脚本清理检查报告")
    lines.append("=" * 50)
    lines.append(f"  总文件数:     {report['total_files']}")
    lines.append(f"  合规文件数:   {report['compliant_files']}")
    lines.append(f"  不合规文件数: {report['non_compliant_files']}")
    lines.append(f"  过期文件数:   {report['expired_files']}")
    lines.append(f"  已清理文件数: {report['cleaned_files']}")

    if report.get("error"):
        lines.append(f"  错误: {report['error']}")
    if report.get("warning"):
        lines.append(f"  警告: {report['warning']}")

    for dir_data in report["directories"]:
        dir_path = dir_data.get("path", "unknown")
        lines.append("")
        lines.append(f"  目录: {dir_path}")
        if not dir_data.get("exists", False):
            lines.append("    [跳过] 目录不存在")
            continue
        if dir_data["non_compliant_list"]:
            lines.append("    不合规文件:")
            for name in dir_data["non_compliant_list"]:
                lines.append(f"      - {name}")
        if dir_data["expired_list"]:
            lines.append("    过期文件 (>24h):")
            for name in dir_data["expired_list"]:
                lines.append(f"      - {name}")
        if dir_data["residual_files"] and not dir_data["non_compliant_list"] and not dir_data["expired_list"]:
            lines.append("    残留文件 (合规且未过期):")
            for name in dir_data["residual_files"]:
                lines.append(f"      - {name}")

    if report["cleaned_list"]:
        lines.append("")
        lines.append("  已自动清理:")
        for name in report["cleaned_list"]:
            lines.append(f"    - {name}")

    lines.append("=" * 50)
    lines.append(f"结果: {report['status']}")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="扫描临时脚本目录，检测残留文件、命名合规性和过期文件"
    )
    parser.add_argument(
        "--temp-dir",
        default=None,
        help="指定临时脚本目录路径（默认扫描 .knowledge/temp-scripts 和 .temp-scripts）",
    )
    parser.add_argument(
        "--auto-clean",
        action="store_true",
        help="自动清理超过24小时的过期临时脚本",
    )
    parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="json",
        help="输出格式: json 或 text（默认: json）",
    )
    args = parser.parse_args()

    now = time.time()

    scan_dirs = [args.temp_dir] if args.temp_dir else SCAN_DIRS

    dirs_data = []
    all_cleaned = []

    for dir_path_str in scan_dirs:
        temp_dir = Path(dir_path_str)
        dir_result = scan_directory(temp_dir, now)
        dir_result["path"] = dir_path_str

        if args.auto_clean and dir_result.get("exists", False):
            cleaned = auto_clean_expired(temp_dir, now)
            all_cleaned.extend(cleaned)

        dirs_data.append(dir_result)

    report = build_report(dirs_data, all_cleaned)

    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(format_text_report(report))

    if report["status"] == "FAIL":
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
