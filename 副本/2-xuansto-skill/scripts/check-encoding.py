#!/usr/bin/env python3

import argparse
import os
import re
import sys


if sys.platform == 'win32':
    RED = ""
    GREEN = ""
    YELLOW = ""
    BLUE = ""
    NC = ""
else:
    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    BLUE = "\033[0;34m"
    NC = "\033[0m"

DEFAULT_EXTENSIONS = [
    "py", "js", "ts", "jsx", "tsx", "vue", "go", "java", "kt",
    "rs", "md", "json", "yaml", "yml", "sh",
]


def check_bom(file_path):
    with open(file_path, "rb") as f:
        header = f.read(3)
    return header[:3] == b"\xef\xbb\xbf"


def check_encoding(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            f.read()
        return True
    except (UnicodeDecodeError, UnicodeError):
        return False


def check_line_ending(file_path):
    with open(file_path, "rb") as f:
        content = f.read()
    return b"\r\n" not in content and b"\r" not in content


def check_python_encoding_declaration(file_path):
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        for i, line in enumerate(f):
            if i >= 3:
                break
            if re.search(r"#\s*-\*-\s*coding:", line) or re.search(r"#\s*coding:", line):
                return True
    return False


def check_file(file_path, verbose, quiet):
    errors = []

    if not check_encoding(file_path):
        errors.append("Encoding error (not valid UTF-8)")

    if check_bom(file_path):
        errors.append("Contains BOM")

    if not check_line_ending(file_path):
        errors.append("Line ending is CRLF (should be LF)")

    if file_path.endswith(".py") and check_python_encoding_declaration(file_path):
        errors.append("Contains forbidden PEP 263 coding declaration")

    if not errors:
        if verbose and not quiet:
            print(f"{GREEN}[PASS]{NC} {file_path}")
        return True
    else:
        error_str = "; ".join(errors)
        if not quiet:
            print(f"{RED}[FAIL]{NC} {file_path} - {error_str}")
        return False


def find_files(target_dir, extensions):
    matched = []
    ext_set = {f".{ext.strip()}" for ext in extensions}
    for root, dirs, files in os.walk(target_dir):
        if ".git" in root.split(os.sep) or "/.git/" in root.replace(os.sep, "/"):
            continue
        dirs[:] = [d for d in dirs if d != ".git"]
        for fname in files:
            _, ext = os.path.splitext(fname)
            if ext.lower() in ext_set:
                matched.append(os.path.join(root, fname))
    return matched


def main():
    parser = argparse.ArgumentParser(
        description="Encoding check script - Check files for UTF-8 without BOM encoding"
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Directory path to check (default: current directory)",
    )
    parser.add_argument(
        "extensions",
        nargs="?",
        default=",".join(DEFAULT_EXTENSIONS),
        help=f"File extensions to check, comma-separated (default: {','.join(DEFAULT_EXTENSIONS)})",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show verbose output",
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Quiet mode, only show errors",
    )
    args = parser.parse_args()

    target_dir = args.directory
    extensions = [ext.strip() for ext in args.extensions.split(",")]

    if not os.path.isdir(target_dir):
        print(f"{RED}Error: Directory does not exist: {target_dir}{NC}")
        sys.exit(2)

    if not args.quiet:
        print(f"{BLUE}========================================{NC}")
        print(f"{BLUE}Encoding Check Script{NC}")
        print(f"{BLUE}========================================{NC}")
        print()
        print(f"Check directory: {target_dir}")
        print(f"File extensions: {','.join(extensions)}")
        print()

    files = find_files(target_dir, extensions)

    total = 0
    passed = 0
    failed = 0
    bom_count = 0
    wrong_encoding_count = 0
    crlf_count = 0
    pep263_count = 0

    for file_path in sorted(files):
        total += 1
        if check_file(file_path, args.verbose, args.quiet):
            passed += 1
        else:
            failed += 1
            if check_bom(file_path):
                bom_count += 1
            if not check_encoding(file_path):
                wrong_encoding_count += 1
            if not check_line_ending(file_path):
                crlf_count += 1
            if file_path.endswith(".py") and check_python_encoding_declaration(file_path):
                pep263_count += 1

    if not args.quiet:
        print()
        print(f"{BLUE}========================================{NC}")
        print(f"{BLUE}Check Result Statistics{NC}")
        print(f"{BLUE}========================================{NC}")
        print()
        print(f"Total files checked: {total}")
        print(f"Passed: {GREEN}{passed}{NC}")
        print(f"Failed: {RED}{failed}{NC}")
        print()

        if bom_count > 0:
            print(f"{YELLOW}Warning: Found {bom_count} file(s) containing BOM{NC}")
        if wrong_encoding_count > 0:
            print(f"{YELLOW}Warning: Found {wrong_encoding_count} file(s) with incorrect encoding{NC}")
        if crlf_count > 0:
            print(f"{YELLOW}Warning: Found {crlf_count} file(s) with CRLF line endings{NC}")
        if pep263_count > 0:
            print(f"{YELLOW}Warning: Found {pep263_count} Python file(s) with forbidden PEP 263 coding declaration{NC}")

    sys.exit(1 if failed > 0 else 0)


if __name__ == "__main__":
    main()
