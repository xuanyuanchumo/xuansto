#!/usr/bin/env python3
"""Script Security Scanner - 临时脚本安全沙箱静态分析脚本

扫描脚本文件，检测是否违反安全沙箱约束：
- 文件系统写入白名单
- 进程调用禁止
- 网络访问禁止
- 动态代码执行禁止

用法:
    python script-security-scanner.py <script_path> [--format json|text]
"""

import argparse
import ast
import json
import os
import re
import sys


WRITE_WHITELIST = [
    "src/",
    "test/",
    "tests/",
    ".knowledge/",
    ".skill-logs/",
    "tmp/",
    "temp/",
]

DANGEROUS_IMPORTS = {
    "subprocess": "进程调用禁止：使用subprocess模块",
    "os.system": "进程调用禁止：使用os.system()",
    "os.popen": "进程调用禁止：使用os.popen()",
    "requests": "网络访问禁止：使用requests库",
    "urllib.request": "网络访问禁止：使用urllib库",
    "http.client": "网络访问禁止：使用http.client",
    "socket": "网络访问禁止：使用socket",
}

DANGEROUS_FUNCTIONS = {
    "eval": "动态代码执行禁止：使用eval()",
    "exec": "动态代码执行禁止：使用exec()",
    "compile": "动态代码执行禁止：使用compile()",
    "__import__": "动态代码执行禁止：使用__import__()",
}

JS_DANGEROUS_PATTERNS = {
    r"require\s*\(\s*['\"]child_process['\"]\s*\)": "进程调用禁止：使用child_process",
    r"require\s*\(\s*['\"]http['\"]\s*\)": "网络访问禁止：使用http模块",
    r"require\s*\(\s*['\"]https['\"]\s*\)": "网络访问禁止：使用https模块",
    r"require\s*\(\s*['\"]net['\"]\s*\)": "网络访问禁止：使用net模块",
    r"require\s*\(\s*['\"]request['\"]\s*\)": "网络访问禁止：使用request库",
    r"require\s*\(\s*['\"]axios['\"]\s*\)": "网络访问禁止：使用axios库",
    r"new\s+Function\s*\(": "动态代码执行禁止：使用new Function()",
    r"\beval\s*\(": "动态代码执行禁止：使用eval()",
}


class SecurityScanner:
    def __init__(self):
        self.violations = []

    def scan_file(self, filepath):
        if not os.path.exists(filepath):
            return [{"rule": "FILE_NOT_FOUND", "message": f"File not found: {filepath}", "severity": "ERROR"}]

        ext = os.path.splitext(filepath)[1].lower()
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        if ext == ".py":
            self._scan_python(filepath, content)
        elif ext in (".js", ".ts", ".jsx", ".tsx"):
            self._scan_javascript(filepath, content)
        elif ext in (".ps1", ".sh"):
            self._scan_shell(filepath, content)
        else:
            self.violations.append({
                "file": filepath,
                "rule": "UNKNOWN_FILE_TYPE",
                "message": f"Unsupported file type: {ext}",
                "severity": "WARN",
            })

        self._check_write_paths(filepath, content)
        return self.violations

    def _scan_python(self, filepath, content):
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name in DANGEROUS_IMPORTS:
                            self.violations.append({
                                "file": filepath,
                                "line": node.lineno,
                                "rule": "DANGEROUS_IMPORT",
                                "message": DANGEROUS_IMPORTS[alias.name],
                                "severity": "BLOCK",
                            })
                elif isinstance(node, ast.ImportFrom):
                    if node.module and any(node.module.startswith(k) for k in DANGEROUS_IMPORTS):
                        matching = [k for k in DANGEROUS_IMPORTS if node.module.startswith(k)][0]
                        self.violations.append({
                            "file": filepath,
                            "line": node.lineno,
                            "rule": "DANGEROUS_IMPORT",
                            "message": DANGEROUS_IMPORTS[matching],
                            "severity": "BLOCK",
                        })
                elif isinstance(node, ast.Call):
                    func_name = None
                    if isinstance(node.func, ast.Name):
                        func_name = node.func.id
                    elif isinstance(node.func, ast.Attribute):
                        func_name = node.func.attr
                    if func_name in DANGEROUS_FUNCTIONS:
                        self.violations.append({
                            "file": filepath,
                            "line": node.lineno,
                            "rule": "DANGEROUS_FUNCTION",
                            "message": DANGEROUS_FUNCTIONS[func_name],
                            "severity": "BLOCK",
                        })
        except SyntaxError:
            self._scan_python_regex(filepath, content)

    def _scan_python_regex(self, filepath, content):
        for line_num, line in enumerate(content.split("\n"), 1):
            for imp, msg in DANGEROUS_IMPORTS.items():
                if re.search(rf"\b{re.escape(imp)}\b", line):
                    self.violations.append({
                        "file": filepath,
                        "line": line_num,
                        "rule": "DANGEROUS_IMPORT",
                        "message": msg,
                        "severity": "BLOCK",
                    })
            for func, msg in DANGEROUS_FUNCTIONS.items():
                if re.search(rf"\b{re.escape(func)}\s*\(", line):
                    self.violations.append({
                        "file": filepath,
                        "line": line_num,
                        "rule": "DANGEROUS_FUNCTION",
                        "message": msg,
                        "severity": "BLOCK",
                    })

    def _scan_javascript(self, filepath, content):
        for line_num, line in enumerate(content.split("\n"), 1):
            for pattern, msg in JS_DANGEROUS_PATTERNS.items():
                if re.search(pattern, line):
                    self.violations.append({
                        "file": filepath,
                        "line": line_num,
                        "rule": "DANGEROUS_PATTERN",
                        "message": msg,
                        "severity": "BLOCK",
                    })

    def _scan_shell(self, filepath, content):
        shell_dangerous = [
            (r"curl\s+", "网络访问禁止：使用curl"),
            (r"wget\s+", "网络访问禁止：使用wget"),
            (r"Invoke-WebRequest", "网络访问禁止：使用Invoke-WebRequest"),
            (r"Invoke-RestMethod", "网络访问禁止：使用Invoke-RestMethod"),
        ]
        for line_num, line in enumerate(content.split("\n"), 1):
            for pattern, msg in shell_dangerous:
                if re.search(pattern, line):
                    self.violations.append({
                        "file": filepath,
                        "line": line_num,
                        "rule": "DANGEROUS_PATTERN",
                        "message": msg,
                        "severity": "BLOCK",
                    })

    def _check_write_paths(self, filepath, content):
        write_patterns = [
            r"open\s*\([^)]*['\"]w",
            r"with\s+open\s*\([^)]*['\"]w",
            r"Path\s*\([^)]*\)\s*/\s*['\"]",
            r"os\.path\.join\s*\(",
            r"fs\.write",
            r"fs\.createWriteStream",
        ]
        for line_num, line in enumerate(content.split("\n"), 1):
            for pattern in write_patterns:
                if re.search(pattern, line):
                    in_whitelist = any(w in line for w in WRITE_WHITELIST)
                    if not in_whitelist:
                        self.violations.append({
                            "file": filepath,
                            "line": line_num,
                            "rule": "WRITE_PATH_NOT_IN_WHITELIST",
                            "message": f"文件写入路径不在白名单内: {line.strip()}",
                            "severity": "WARN",
                        })
                    break

    def generate_report(self, violations, format_type="text"):
        if format_type == "json":
            return json.dumps(violations, ensure_ascii=False, indent=2)

        if not violations:
            return "[PASS] No security violations found."

        lines = ["=" * 60, "Script Security Scan Report", "=" * 60]
        block_count = sum(1 for v in violations if v.get("severity") == "BLOCK")
        warn_count = sum(1 for v in violations if v.get("severity") == "WARN")
        lines.append(f"Total violations: {len(violations)} (BLOCK: {block_count}, WARN: {warn_count})")
        lines.append("-" * 60)

        for v in violations:
            severity = v.get("severity", "UNKNOWN")
            rule = v.get("rule", "UNKNOWN")
            msg = v.get("message", "")
            line = v.get("line", "?")
            file = v.get("file", "?")
            lines.append(f"[{severity}] {rule} at {file}:{line}")
            lines.append(f"  {msg}")

        lines.append("=" * 60)
        if block_count > 0:
            lines.append("RESULT: FAIL - BLOCK violations found")
        else:
            lines.append("RESULT: PASS - No BLOCK violations")
        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Script Security Scanner")
    parser.add_argument("script_path", help="Path to script file to scan")
    parser.add_argument("--format", choices=["json", "text"], default="text", help="Output format")
    args = parser.parse_args()

    scanner = SecurityScanner()
    violations = scanner.scan_file(args.script_path)
    report = scanner.generate_report(violations, args.format)
    print(report)

    if any(v.get("severity") == "BLOCK" for v in violations):
        sys.exit(1)


if __name__ == "__main__":
    main()
