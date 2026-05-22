#!/usr/bin/env python3
"""Comment language compliance checker - validates comment language against project policy."""

import argparse
import fnmatch
import json
import os
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

ZH_UNICODE_RANGES = [
    (0x4E00, 0x9FFF),
    (0x3400, 0x4DBF),
    (0x20000, 0x2A6DF),
    (0x2A700, 0x2B73F),
    (0xF900, 0xFAFF),
]

NON_ASCII_RANGES = {
    "zh": [(0x4E00, 0x9FFF), (0x3400, 0x4DBF), (0x20000, 0x2A6DF), (0x2A700, 0x2B73F), (0xF900, 0xFAFF)],
    "ja": [(0x3040, 0x309F), (0x30A0, 0x30FF), (0x31F0, 0x31FF)],
    "ko": [(0xAC00, 0xD7AF), (0x1100, 0x11FF), (0x3130, 0x318F)],
    "ar": [(0x0600, 0x06FF), (0x0750, 0x077F), (0xFB50, 0xFDFF), (0xFE70, 0xFEFF)],
    "ru": [(0x0400, 0x04FF), (0x0500, 0x052F)],
    "th": [(0x0E00, 0x0E7F)],
    "hi": [(0x0900, 0x097F)],
    "he": [(0x0590, 0x05FF), (0xFB1D, 0xFB4F)],
}

LANGUAGE_NAMES = {
    "zh": "Chinese",
    "ja": "Japanese",
    "ko": "Korean",
    "ar": "Arabic",
    "ru": "Russian",
    "th": "Thai",
    "hi": "Hindi",
    "he": "Hebrew",
}

TECHNICAL_MARKERS = re.compile(
    r"^\s*(?:TODO|FIXME|HACK|XXX|NOTE|BUG)\b",
    re.IGNORECASE,
)

FILE_EXTENSIONS = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".java": "java",
    ".go": "go",
    ".rs": "rust",
    ".c": "c",
    ".cpp": "cpp",
    ".h": "c",
    ".hpp": "cpp",
    ".cs": "csharp",
    ".rb": "ruby",
    ".php": "php",
    ".swift": "swift",
    ".kt": "kotlin",
    ".scala": "scala",
}

COMMENT_PATTERNS = {
    "python": [
        re.compile(r'#(.*)$', re.MULTILINE),
        re.compile(r'"""([\s\S]*?)"""', re.MULTILINE),
        re.compile(r"'''([\s\S]*?)'''", re.MULTILINE),
    ],
    "javascript": [
        re.compile(r'//(.*)$', re.MULTILINE),
        re.compile(r'/\*([\s\S]*?)\*/', re.MULTILINE),
    ],
    "typescript": [
        re.compile(r'//(.*)$', re.MULTILINE),
        re.compile(r'/\*([\s\S]*?)\*/', re.MULTILINE),
    ],
    "java": [
        re.compile(r'//(.*)$', re.MULTILINE),
        re.compile(r'/\*([\s\S]*?)\*/', re.MULTILINE),
    ],
    "go": [
        re.compile(r'//(.*)$', re.MULTILINE),
        re.compile(r'/\*([\s\S]*?)\*/', re.MULTILINE),
    ],
    "rust": [
        re.compile(r'//(!?)(.*)$', re.MULTILINE),
        re.compile(r'/\*([\s\S]*?)\*/', re.MULTILINE),
    ],
    "c": [
        re.compile(r'//(.*)$', re.MULTILINE),
        re.compile(r'/\*([\s\S]*?)\*/', re.MULTILINE),
    ],
    "cpp": [
        re.compile(r'//(.*)$', re.MULTILINE),
        re.compile(r'/\*([\s\S]*?)\*/', re.MULTILINE),
    ],
    "csharp": [
        re.compile(r'//(.*)$', re.MULTILINE),
        re.compile(r'/\*([\s\S]*?)\*/', re.MULTILINE),
    ],
    "ruby": [
        re.compile(r'#(.*)$', re.MULTILINE),
        re.compile(r'=begin([\s\S]*?)=end', re.MULTILINE),
    ],
    "php": [
        re.compile(r'//(.*)$', re.MULTILINE),
        re.compile(r'/\*([\s\S]*?)\*/', re.MULTILINE),
        re.compile(r'#(.*)$', re.MULTILINE),
    ],
    "swift": [
        re.compile(r'//(.*)$', re.MULTILINE),
        re.compile(r'/\*([\s\S]*?)\*/', re.MULTILINE),
    ],
    "kotlin": [
        re.compile(r'//(.*)$', re.MULTILINE),
        re.compile(r'/\*([\s\S]*?)\*/', re.MULTILINE),
    ],
    "scala": [
        re.compile(r'//(.*)$', re.MULTILINE),
        re.compile(r'/\*([\s\S]*?)\*/', re.MULTILINE),
    ],
}

IGNORE_DIRS = {
    "node_modules", ".git", "__pycache__", ".venv", "venv", "env",
    "dist", "build", ".next", ".nuxt", "target", "vendor", ".idea",
    ".vscode", ".cache", "coverage", ".tox", "eggs", "*.egg-info",
}


@dataclass
class CommentIssue:
    file_path: str
    line_number: int
    policy: str
    violation: str
    comment_text: str
    detail: str


@dataclass
class FileResult:
    file_path: str
    total_comments: int = 0
    flagged_comments: int = 0
    issues: List[CommentIssue] = field(default_factory=list)


@dataclass
class CheckResult:
    total_files: int = 0
    total_comments: int = 0
    total_flagged: int = 0
    file_results: List[FileResult] = field(default_factory=list)
    language_summary: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    policy: str = "zh-business"


def is_char_in_ranges(char: str, ranges: List[Tuple[int, int]]) -> bool:
    code_point = ord(char)
    for start, end in ranges:
        if start <= code_point <= end:
            return True
    return False


def contains_chinese(text: str) -> Tuple[bool, str]:
    matched = []
    for char in text:
        if is_char_in_ranges(char, ZH_UNICODE_RANGES):
            matched.append(char)
    if matched:
        return True, "".join(matched)
    return False, ""


def detect_non_ascii_languages(text: str) -> Dict[str, str]:
    detected: Dict[str, str] = {}
    for lang_code, ranges in NON_ASCII_RANGES.items():
        matched = []
        for char in text:
            if is_char_in_ranges(char, ranges):
                matched.append(char)
        if matched:
            detected[lang_code] = "".join(matched)
    return detected


def is_technical_marker(comment_text: str) -> bool:
    stripped = comment_text.strip()
    if not stripped:
        return False
    return bool(TECHNICAL_MARKERS.match(stripped))


def is_business_comment(comment_text: str) -> bool:
    stripped = comment_text.strip()
    if not stripped:
        return False
    if len(stripped) < 3:
        return False
    if is_technical_marker(stripped):
        return False
    return True


def extract_comments(source: str, lang_type: str) -> List[Tuple[str, int]]:
    patterns = COMMENT_PATTERNS.get(lang_type, [])
    comments = []
    for pattern in patterns:
        for match in pattern.finditer(source):
            comment_text = match.group(0)
            start_pos = match.start()
            line_number = source[:start_pos].count("\n") + 1
            comments.append((comment_text, line_number))
    return comments


def check_comment_zh_business(comment_text: str, line_number: int, file_path: str) -> Optional[CommentIssue]:
    stripped = comment_text.strip()
    if not stripped:
        return None

    if is_technical_marker(stripped):
        return None

    has_zh, zh_chars = contains_chinese(stripped)
    if has_zh:
        return None

    if is_business_comment(stripped):
        return CommentIssue(
            file_path=file_path,
            line_number=line_number,
            policy="zh-business",
            violation="missing-chinese",
            comment_text=stripped[:120],
            detail="Business logic comment should contain Chinese characters (业务注释简体中文)",
        )

    return None


def check_comment_en_only(comment_text: str, line_number: int, file_path: str) -> Optional[CommentIssue]:
    stripped = comment_text.strip()
    if not stripped:
        return None

    detected = detect_non_ascii_languages(stripped)
    if not detected:
        return None

    lang_names = [LANGUAGE_NAMES.get(code, code) for code in detected.keys()]
    matched_chars = "".join(detected.values())[:50]

    return CommentIssue(
        file_path=file_path,
        line_number=line_number,
        policy="en-only",
        violation="non-english",
        comment_text=stripped[:120],
        detail=f"Non-English characters detected ({', '.join(lang_names)}): {matched_chars}",
    )


def check_file(file_path: str, policy: str) -> Optional[FileResult]:
    ext = Path(file_path).suffix.lower()
    lang_type = FILE_EXTENSIONS.get(ext)
    if not lang_type:
        return None

    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            source = f.read()
    except (OSError, IOError):
        return None

    comments = extract_comments(source, lang_type)
    if not comments:
        return None

    result = FileResult(file_path=file_path)

    for comment_text, line_number in comments:
        result.total_comments += 1

        detected = detect_non_ascii_languages(comment_text)
        for lang_code in detected:
            result.__dict__.setdefault("_lang_counts", defaultdict(int))
            result.__dict__["_lang_counts"][lang_code] += 1

        issue = None
        if policy == "zh-business":
            issue = check_comment_zh_business(comment_text, line_number, file_path)
        elif policy == "en-only":
            issue = check_comment_en_only(comment_text, line_number, file_path)
        elif policy == "mixed":
            issue = None

        if issue is not None:
            result.flagged_comments += 1
            result.issues.append(issue)

    return result


def walk_source_dir(src_dir: str) -> List[str]:
    files = []
    for root, dirs, filenames in os.walk(src_dir):
        dirs[:] = [d for d in dirs if not any(fnmatch.fnmatch(d, pattern) for pattern in IGNORE_DIRS) and not d.startswith(".")]
        for filename in filenames:
            ext = Path(filename).suffix.lower()
            if ext in FILE_EXTENSIONS:
                files.append(os.path.join(root, filename))
    return files


def format_report(result: CheckResult, output_format: str) -> str:
    policy_labels = {
        "zh-business": "业务注释简体中文 (Business comments in Chinese)",
        "en-only": "English only",
        "mixed": "Mixed (statistics only)",
    }
    policy_label = policy_labels.get(result.policy, result.policy)

    if output_format == "json":
        data = {
            "summary": {
                "policy": result.policy,
                "policy_description": policy_label,
                "total_files_scanned": result.total_files,
                "total_comments": result.total_comments,
                "total_flagged": result.total_flagged,
            },
            "language_summary": {LANGUAGE_NAMES.get(k, k): v for k, v in result.language_summary.items()},
            "issues": [],
        }
        for fr in result.file_results:
            for issue in fr.issues:
                data["issues"].append(
                    {
                        "file": issue.file_path,
                        "line": issue.line_number,
                        "policy": issue.policy,
                        "violation": issue.violation,
                        "comment": issue.comment_text,
                        "detail": issue.detail,
                    }
                )
        return json.dumps(data, indent=2, ensure_ascii=False)

    if output_format == "csv":
        lines = ["file,line,policy,violation,comment,detail"]
        for fr in result.file_results:
            for issue in fr.issues:
                comment_escaped = issue.comment_text.replace('"', '""')
                detail_escaped = issue.detail.replace('"', '""')
                lines.append(
                    f'"{issue.file_path}",{issue.line_number},{issue.policy},{issue.violation},"{comment_escaped}","{detail_escaped}"'
                )
        return "\n".join(lines)

    lines = []
    lines.append("")
    lines.append("=" * 70)
    lines.append("  Comment Language Compliance Report")
    lines.append("=" * 70)
    lines.append(f"  Policy:           {policy_label}")
    lines.append(f"  Files Scanned:    {result.total_files}")
    lines.append(f"  Total Comments:   {result.total_comments}")
    lines.append(f"  Flagged Comments: {result.total_flagged}")
    lines.append("=" * 70)
    lines.append("")

    if result.language_summary:
        lines.append("  Language Distribution:")
        for lang, count in sorted(result.language_summary.items(), key=lambda x: -x[1]):
            lang_label = LANGUAGE_NAMES.get(lang, lang)
            lines.append(f"    {lang_label}: {count} comments")
        lines.append("")

    if result.total_flagged > 0:
        lines.append("  Flagged Comments:")
        lines.append("-" * 70)
        for fr in result.file_results:
            for issue in fr.issues:
                lines.append(f"  File: {issue.file_path}:{issue.line_number}")
                lines.append(f"  Violation: {issue.violation}")
                lines.append(f"  Comment: {issue.comment_text[:100]}")
                lines.append(f"  Detail: {issue.detail}")
                lines.append("-" * 70)
        lines.append("")

    if result.policy == "mixed":
        status = "INFO"
        icon = "ℹ️"
    else:
        status = "FAILED" if result.total_flagged > 0 else "PASSED"
        icon = "❌" if result.total_flagged > 0 else "✅"
    lines.append(f"  {icon} Check {status}")
    lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Check comment language compliance against project policy"
    )
    parser.add_argument("--src", required=True, help="Source directory to scan")
    parser.add_argument(
        "--policy",
        choices=["zh-business", "en-only", "mixed"],
        default="zh-business",
        help="Language policy: zh-business (default, business comments in Chinese), en-only (English only), mixed (statistics only)",
    )
    parser.add_argument(
        "--output-format",
        choices=["text", "json", "csv"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument("--output-path", help="Write results to a file")
    parser.add_argument("--exclude", nargs="*", help="Additional directory names to exclude")
    args = parser.parse_args()

    if not os.path.isdir(args.src):
        print(f"Error: Source directory not found: {args.src}", file=sys.stderr)
        sys.exit(1)

    if args.exclude:
        IGNORE_DIRS.update(args.exclude)

    policy_labels = {
        "zh-business": "业务注释简体中文",
        "en-only": "English only",
        "mixed": "Mixed (statistics only)",
    }
    print(f"\nScanning comments with policy [{policy_labels[args.policy]}] in: {args.src}")

    source_files = walk_source_dir(args.src)
    print(f"Found {len(source_files)} source files to check\n")

    result = CheckResult(policy=args.policy)

    for file_path in source_files:
        file_result = check_file(file_path, args.policy)
        if file_result is None:
            continue

        result.total_files += 1
        result.total_comments += file_result.total_comments
        result.total_flagged += file_result.flagged_comments

        if file_result.flagged_comments > 0:
            result.file_results.append(file_result)

        lang_counts = file_result.__dict__.get("_lang_counts", {})
        for lang_code, count in lang_counts.items():
            result.language_summary[lang_code] += count

    report = format_report(result, args.output_format)
    print(report)

    if args.output_path:
        with open(args.output_path, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"Report written to: {args.output_path}")

    if args.policy == "mixed":
        sys.exit(0)
    sys.exit(1 if result.total_flagged > 0 else 0)


if __name__ == "__main__":
    main()
