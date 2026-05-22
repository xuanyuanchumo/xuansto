#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
综合问题检测器 - Comprehensive Problem Detector

整合多种问题检测能力：
1. 语法错误检测 (Syntax Error Detection)
2. 导入错误检测 (Import Error Detection)
3. 类型错误检测 (Type Error Detection)
4. 安全漏洞检测 (Security Vulnerability Detection)

使用示例:
    python problem_detector.py --file code.py --detect-all
    python problem_detector.py --file code.py --detect-syntax
    python problem_detector.py --file code.py --detect-security
"""

from __future__ import annotations

import ast
import re
import json
import logging
import sys
import os
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ProblemCategory(Enum):
    SYNTAX_ERROR = auto()
    IMPORT_ERROR = auto()
    TYPE_ERROR = auto()
    SECURITY_VULNERABILITY = auto()
    CODE_QUALITY = auto()
    BEST_PRACTICE = auto()


class ProblemSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class DetectedProblem:
    problem_id: str
    category: ProblemCategory
    severity: ProblemSeverity
    problem_type: str
    message: str
    file_path: str
    line_number: int
    column: int = 0
    end_line: int = 0
    end_column: int = 0
    code_snippet: str = ""
    suggestion: str = ""
    confidence: float = 1.0
    context: Dict[str, Any] = field(default_factory=dict)
    auto_fixable: bool = False
    cwe_id: Optional[str] = None
    owasp_category: Optional[str] = None
    detected_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "problem_id": self.problem_id,
            "category": self.category.name,
            "severity": self.severity.value,
            "problem_type": self.problem_type,
            "message": self.message,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "column": self.column,
            "end_line": self.end_line,
            "end_column": self.end_column,
            "code_snippet": self.code_snippet,
            "suggestion": self.suggestion,
            "confidence": self.confidence,
            "context": self.context,
            "auto_fixable": self.auto_fixable,
            "cwe_id": self.cwe_id,
            "owasp_category": self.owasp_category,
            "detected_at": self.detected_at
        }


class SyntaxErrorDetector:
    """语法错误检测器"""

    def __init__(self):
        self._problem_counter = 0

    def detect(self, content: str, file_path: str) -> List[DetectedProblem]:
        problems = []
        
        try:
            ast.parse(content)
        except SyntaxError as e:
            self._problem_counter += 1
            problems.append(DetectedProblem(
                problem_id=f"SYNTAX_{self._problem_counter:06d}",
                category=ProblemCategory.SYNTAX_ERROR,
                severity=ProblemSeverity.CRITICAL,
                problem_type="syntax_error",
                message=f"语法错误: {e.msg}",
                file_path=file_path,
                line_number=e.lineno or 1,
                column=e.offset or 0,
                code_snippet=self._get_error_line(content, e.lineno),
                suggestion=self._generate_syntax_fix_suggestion(e),
                confidence=1.0,
                auto_fixable=self._is_auto_fixable(e),
                context={
                    "error_type": "SyntaxError",
                    "raw_message": str(e)
                }
            ))
        
        problems.extend(self._detect_indentation_issues(content, file_path))
        problems.extend(self._detect_bracket_mismatch(content, file_path))
        problems.extend(self._detect_string_issues(content, file_path))
        problems.extend(self._detect_invalid_syntax_patterns(content, file_path))
        
        return problems

    def _get_error_line(self, content: str, line_number: Optional[int]) -> str:
        if line_number is None:
            return ""
        lines = content.split('\n')
        if 1 <= line_number <= len(lines):
            return lines[line_number - 1]
        return ""

    def _generate_syntax_fix_suggestion(self, error: SyntaxError) -> str:
        msg = error.msg.lower() if error.msg else ""
        
        if "expected ':'" in msg:
            return "在语句末尾添加冒号 ':'"
        elif "unexpected indent" in msg:
            return "检查缩进是否正确，确保与上下文一致"
        elif "unindent does not match" in msg:
            return "检查缩进层级，确保与外层代码块一致"
        elif "unexpected eof" in msg or "eof while scanning" in msg:
            return "检查是否有未闭合的括号、引号或三引号字符串"
        elif "invalid syntax" in msg:
            return "检查语法是否正确，可能缺少关键字或符号"
        elif "eol while scanning string literal" in msg:
            return "字符串未正确闭合，检查引号是否匹配"
        else:
            return "修复语法错误后重试"

    def _is_auto_fixable(self, error: SyntaxError) -> bool:
        msg = error.msg.lower() if error.msg else ""
        auto_fixable_patterns = [
            "expected ':'",
            "missing parenthesis",
            "missing bracket",
        ]
        return any(pattern in msg for pattern in auto_fixable_patterns)

    def _detect_indentation_issues(self, content: str, file_path: str) -> List[DetectedProblem]:
        problems = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            if not line.strip():
                continue
            
            spaces = len(line) - len(line.lstrip())
            
            if spaces % 4 != 0 and not line.strip().startswith('#'):
                self._problem_counter += 1
                problems.append(DetectedProblem(
                    problem_id=f"SYNTAX_{self._problem_counter:06d}",
                    category=ProblemCategory.SYNTAX_ERROR,
                    severity=ProblemSeverity.LOW,
                    problem_type="indentation_inconsistent",
                    message=f"缩进不一致: 使用了 {spaces} 个空格，建议使用 4 的倍数",
                    file_path=file_path,
                    line_number=i,
                    code_snippet=line,
                    suggestion="统一使用 4 个空格作为缩进",
                    confidence=0.8,
                    auto_fixable=True
                ))
        
        return problems

    def _detect_bracket_mismatch(self, content: str, file_path: str) -> List[DetectedProblem]:
        problems = []
        
        stack = []
        bracket_pairs = {'(': ')', '[': ']', '{': '}'}
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            in_string = False
            string_char = None
            escape_next = False
            
            for col, char in enumerate(line, 1):
                if escape_next:
                    escape_next = False
                    continue
                
                if char == '\\':
                    escape_next = True
                    continue
                
                if char in ('"', "'") and not in_string:
                    in_string = True
                    string_char = char
                elif char == string_char and in_string:
                    in_string = False
                    string_char = None
                elif not in_string:
                    if char in bracket_pairs:
                        stack.append((char, line_num, col))
                    elif char in bracket_pairs.values():
                        if stack:
                            expected_open = [k for k, v in bracket_pairs.items() if v == char][0]
                            last_open, open_line, open_col = stack[-1]
                            if last_open != expected_open:
                                self._problem_counter += 1
                                problems.append(DetectedProblem(
                                    problem_id=f"SYNTAX_{self._problem_counter:06d}",
                                    category=ProblemCategory.SYNTAX_ERROR,
                                    severity=ProblemSeverity.HIGH,
                                    problem_type="bracket_mismatch",
                                    message=f"括号不匹配: 期望 '{bracket_pairs[last_open]}' 但找到 '{char}'",
                                    file_path=file_path,
                                    line_number=line_num,
                                    column=col,
                                    code_snippet=line,
                                    suggestion="检查括号是否正确配对",
                                    confidence=0.9,
                                    auto_fixable=False
                                ))
                            else:
                                stack.pop()
                        else:
                            self._problem_counter += 1
                            problems.append(DetectedProblem(
                                problem_id=f"SYNTAX_{self._problem_counter:06d}",
                                category=ProblemCategory.SYNTAX_ERROR,
                                severity=ProblemSeverity.HIGH,
                                problem_type="unmatched_bracket",
                                message=f"未匹配的闭合括号 '{char}'",
                                file_path=file_path,
                                line_number=line_num,
                                column=col,
                                code_snippet=line,
                                suggestion="检查是否有缺失的开放括号",
                                confidence=0.9,
                                auto_fixable=False
                            ))
        
        for open_bracket, line_num, col in stack:
            self._problem_counter += 1
            problems.append(DetectedProblem(
                problem_id=f"SYNTAX_{self._problem_counter:06d}",
                category=ProblemCategory.SYNTAX_ERROR,
                severity=ProblemSeverity.HIGH,
                problem_type="unclosed_bracket",
                message=f"未闭合的括号 '{open_bracket}'",
                file_path=file_path,
                line_number=line_num,
                column=col,
                code_snippet=self._get_error_line(content, line_num),
                suggestion=f"在适当位置添加闭合括号 '{bracket_pairs[open_bracket]}'",
                confidence=0.9,
                auto_fixable=True
            ))
        
        return problems

    def _detect_string_issues(self, content: str, file_path: str) -> List[DetectedProblem]:
        problems = []
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            single_quotes = 0
            double_quotes = 0
            triple_single = line.count("'''")
            triple_double = line.count('"""')
            
            i = 0
            while i < len(line):
                if i + 2 < len(line) and line[i:i+3] in ("'''", '"""'):
                    i += 3
                    continue
                
                if line[i] == "'" and (i == 0 or line[i-1] != '\\'):
                    single_quotes += 1
                elif line[i] == '"' and (i == 0 or line[i-1] != '\\'):
                    double_quotes += 1
                i += 1
            
            if single_quotes % 2 != 0 and triple_single % 2 == 0:
                self._problem_counter += 1
                problems.append(DetectedProblem(
                    problem_id=f"SYNTAX_{self._problem_counter:06d}",
                    category=ProblemCategory.SYNTAX_ERROR,
                    severity=ProblemSeverity.HIGH,
                    problem_type="unclosed_string",
                    message="字符串未闭合: 单引号不匹配",
                    file_path=file_path,
                    line_number=line_num,
                    code_snippet=line,
                    suggestion="检查单引号是否正确配对",
                    confidence=0.85,
                    auto_fixable=True
                ))
            
            if double_quotes % 2 != 0 and triple_double % 2 == 0:
                self._problem_counter += 1
                problems.append(DetectedProblem(
                    problem_id=f"SYNTAX_{self._problem_counter:06d}",
                    category=ProblemCategory.SYNTAX_ERROR,
                    severity=ProblemSeverity.HIGH,
                    problem_type="unclosed_string",
                    message="字符串未闭合: 双引号不匹配",
                    file_path=file_path,
                    line_number=line_num,
                    code_snippet=line,
                    suggestion="检查双引号是否正确配对",
                    confidence=0.85,
                    auto_fixable=True
                ))
        
        return problems

    def _detect_invalid_syntax_patterns(self, content: str, file_path: str) -> List[DetectedProblem]:
        problems = []
        lines = content.split('\n')
        
        patterns = [
            (r'\bprint\s+[^(]', "print 语句语法错误", "使用 print() 函数"),
            (r'\bexec\s+[^(]', "exec 语句语法错误", "使用 exec() 函数"),
            (r'<>', "使用了 <> 运算符", "使用 != 替代 <>"),
            (r'\braw_input\b', "使用了 Python 2 的 raw_input", "使用 input() 替代 raw_input()"),
            (r'\bxrange\b', "使用了 Python 2 的 xrange", "使用 range() 替代 xrange()"),
            (r'^\s*except\s*:', "裸 except 语句", "指定具体的异常类型"),
            (r'^\s*except\s+\w+\s*,', "Python 2 风格的 except 语法", "使用 'as' 关键字: except Exception as e"),
        ]
        
        for line_num, line in enumerate(lines, 1):
            for pattern, message, suggestion in patterns:
                if re.search(pattern, line):
                    self._problem_counter += 1
                    problems.append(DetectedProblem(
                        problem_id=f"SYNTAX_{self._problem_counter:06d}",
                        category=ProblemCategory.SYNTAX_ERROR,
                        severity=ProblemSeverity.MEDIUM,
                        problem_type="invalid_syntax_pattern",
                        message=message,
                        file_path=file_path,
                        line_number=line_num,
                        code_snippet=line,
                        suggestion=suggestion,
                        confidence=0.9,
                        auto_fixable=True
                    ))
        
        return problems


class ImportErrorDetector:
    """导入错误检测器"""

    STANDARD_LIBRARY = {
        'abc', 'argparse', 'array', 'ast', 'asyncio', 'atexit', 'base64', 'bisect',
        'builtins', 'bz2', 'calendar', 'cgi', 'cmath', 'cmd', 'code', 'codecs',
        'collections', 'configparser', 'contextlib', 'contextvars', 'copy', 'copyreg',
        'csv', 'ctypes', 'dataclasses', 'datetime', 'decimal', 'difflib', 'dis',
        'doctest', 'email', 'enum', 'errno', 'faulthandler', 'filecmp', 'fileinput',
        'fnmatch', 'fractions', 'ftplib', 'functools', 'gc', 'getopt', 'getpass',
        'gettext', 'glob', 'graphlib', 'gzip', 'hashlib', 'heapq', 'hmac', 'html',
        'http', 'imaplib', 'importlib', 'inspect', 'io', 'ipaddress', 'itertools',
        'json', 'keyword', 'linecache', 'locale', 'logging', 'lzma', 'mailbox',
        'marshal', 'math', 'mimetypes', 'mmap', 'multiprocessing', 'netrc', 'numbers',
        'operator', 'optparse', 'os', 'pathlib', 'pdb', 'pickle', 'pickletools',
        'pkgutil', 'platform', 'plistlib', 'poplib', 'pprint', 'profile', 'pstats',
        'queue', 'quopri', 'random', 're', 'readline', 'reprlib', 'resource',
        'runpy', 'sched', 'secrets', 'select', 'selectors', 'shelve', 'shlex',
        'shutil', 'signal', 'site', 'smtplib', 'socket', 'socketserver', 'sqlite3',
        'ssl', 'stat', 'statistics', 'string', 'stringprep', 'struct', 'subprocess',
        'sys', 'sysconfig', 'tarfile', 'tempfile', 'textwrap', 'threading', 'time',
        'timeit', 'tkinter', 'token', 'tokenize', 'trace', 'traceback', 'types',
        'typing', 'unicodedata', 'unittest', 'urllib', 'uuid', 'venv', 'warnings',
        'wave', 'weakref', 'webbrowser', 'xml', 'xmlrpc', 'zipfile', 'zlib', '_thread'
    }

    COMMON_THIRD_PARTY = {
        'numpy', 'pandas', 'matplotlib', 'seaborn', 'scipy', 'sklearn', 'torch',
        'tensorflow', 'keras', 'django', 'flask', 'fastapi', 'requests', 'httpx',
        'aiohttp', 'selenium', 'bs4', 'lxml', 'PIL', 'cv2', 'pytest', 'pylint',
        'flake8', 'black', 'mypy', 'sphinx', 'jinja2', 'yaml', 'sqlalchemy',
        'pymongo', 'redis', 'celery', 'gunicorn', 'uvicorn', 'click', 'typer',
        'rich', 'tqdm', 'pytz', 'boto3', 'docker', 'psutil', 'watchdog', 'grpc',
        'protobuf', 'cython', 'numba', 'dask', 'ray', 'polars', 'pyspark'
    }

    DEPRECATED_MODULES = {
        'urllib2': 'urllib.request',
        'urlparse': 'urllib.parse',
        'ConfigParser': 'configparser',
        'cPickle': 'pickle',
        'cStringIO': 'io',
        'StringIO': 'io',
        'Queue': 'queue',
        'SocketServer': 'socketserver',
        'SimpleHTTPServer': 'http.server',
        'BaseHTTPServer': 'http.server',
        'Cookie': 'http.cookies',
        'HTMLParser': 'html.parser',
        'Tkinter': 'tkinter',
    }

    def __init__(self):
        self._problem_counter = 0

    def detect(self, content: str, file_path: str) -> List[DetectedProblem]:
        problems = []
        
        try:
            tree = ast.parse(content)
            problems.extend(self._detect_missing_imports(tree, content, file_path))
            problems.extend(self._detect_unused_imports(tree, content, file_path))
            problems.extend(self._detect_import_order_issues(tree, content, file_path))
            problems.extend(self._detect_deprecated_imports(tree, content, file_path))
            problems.extend(self._detect_shadowed_imports(tree, content, file_path))
        except SyntaxError:
            pass
        
        return problems

    def _detect_missing_imports(self, tree: ast.AST, content: str, file_path: str) -> List[DetectedProblem]:
        problems = []
        imported_names = set()
        used_names = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name.split('.')[0]
                    imported_names.add(name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    for alias in node.names:
                        name = alias.asname if alias.asname else alias.name
                        imported_names.add(name)
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                used_names.add(node.id)
        
        potential_missing = used_names - imported_names - self.STANDARD_LIBRARY
        
        for name in potential_missing:
            for node in ast.walk(tree):
                if isinstance(node, ast.Name) and node.id == name and isinstance(node.ctx, ast.Load):
                    self._problem_counter += 1
                    problems.append(DetectedProblem(
                        problem_id=f"IMPORT_{self._problem_counter:06d}",
                        category=ProblemCategory.IMPORT_ERROR,
                        severity=ProblemSeverity.HIGH,
                        problem_type="missing_import",
                        message=f"可能缺少导入: '{name}'",
                        file_path=file_path,
                        line_number=node.lineno,
                        code_snippet=self._get_line(content, node.lineno),
                        suggestion=f"添加导入语句: import {name}",
                        confidence=0.7,
                        auto_fixable=True,
                        context={"missing_name": name}
                    ))
                    break
        
        return problems

    def _detect_unused_imports(self, tree: ast.AST, content: str, file_path: str) -> List[DetectedProblem]:
        problems = []
        imports = {}
        used_names = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name.split('.')[0]
                    imports[name] = (node.lineno, alias.name)
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    imports[name] = (node.lineno, f"{node.module}.{alias.name}" if node.module else alias.name)
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                used_names.add(node.id)
        
        for import_name, (line_no, full_name) in imports.items():
            if import_name not in used_names and not import_name.startswith('_'):
                self._problem_counter += 1
                problems.append(DetectedProblem(
                    problem_id=f"IMPORT_{self._problem_counter:06d}",
                    category=ProblemCategory.IMPORT_ERROR,
                    severity=ProblemSeverity.LOW,
                    problem_type="unused_import",
                    message=f"未使用的导入: '{full_name}'",
                    file_path=file_path,
                    line_number=line_no,
                    code_snippet=self._get_line(content, line_no),
                    suggestion=f"移除未使用的导入: {full_name}",
                    confidence=0.9,
                    auto_fixable=True,
                    context={"import_name": import_name}
                ))
        
        return problems

    def _detect_import_order_issues(self, tree: ast.AST, content: str, file_path: str) -> List[DetectedProblem]:
        problems = []
        import_nodes = []
        
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                module = self._get_module_name(node)
                if module:
                    import_nodes.append((node.lineno, module, node))
        
        if len(import_nodes) < 2:
            return problems
        
        has_std = False
        has_third = False
        has_local = False
        
        for line_no, module, node in import_nodes:
            is_std = module.split('.')[0] in self.STANDARD_LIBRARY
            is_third = module.split('.')[0] in self.COMMON_THIRD_PARTY
            is_local = not is_std and not is_third
            
            if is_std and (has_third or has_local):
                self._problem_counter += 1
                problems.append(DetectedProblem(
                    problem_id=f"IMPORT_{self._problem_counter:06d}",
                    category=ProblemCategory.IMPORT_ERROR,
                    severity=ProblemSeverity.LOW,
                    problem_type="import_order",
                    message="导入顺序不符合 PEP8: 标准库导入应在第三方库和本地模块之前",
                    file_path=file_path,
                    line_number=line_no,
                    code_snippet=self._get_line(content, line_no),
                    suggestion="调整导入顺序: 标准库 -> 第三方库 -> 本地模块",
                    confidence=0.8,
                    auto_fixable=True
                ))
            elif is_third and has_local:
                self._problem_counter += 1
                problems.append(DetectedProblem(
                    problem_id=f"IMPORT_{self._problem_counter:06d}",
                    category=ProblemCategory.IMPORT_ERROR,
                    severity=ProblemSeverity.LOW,
                    problem_type="import_order",
                    message="导入顺序不符合 PEP8: 第三方库导入应在本地模块之前",
                    file_path=file_path,
                    line_number=line_no,
                    code_snippet=self._get_line(content, line_no),
                    suggestion="调整导入顺序: 标准库 -> 第三方库 -> 本地模块",
                    confidence=0.8,
                    auto_fixable=True
                ))
            
            has_std = has_std or is_std
            has_third = has_third or is_third
            has_local = has_local or is_local
        
        return problems

    def _detect_deprecated_imports(self, tree: ast.AST, content: str, file_path: str) -> List[DetectedProblem]:
        problems = []
        
        for node in ast.walk(tree):
            module_name = None
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module_name = alias.name.split('.')[0]
                    if module_name in self.DEPRECATED_MODULES:
                        self._problem_counter += 1
                        problems.append(DetectedProblem(
                            problem_id=f"IMPORT_{self._problem_counter:06d}",
                            category=ProblemCategory.IMPORT_ERROR,
                            severity=ProblemSeverity.MEDIUM,
                            problem_type="deprecated_import",
                            message=f"使用已弃用的模块: '{module_name}'",
                            file_path=file_path,
                            line_number=node.lineno,
                            code_snippet=self._get_line(content, node.lineno),
                            suggestion=f"使用 '{self.DEPRECATED_MODULES[module_name]}' 替代",
                            confidence=0.95,
                            auto_fixable=True,
                            context={
                                "deprecated_module": module_name,
                                "replacement": self.DEPRECATED_MODULES[module_name]
                            }
                        ))
            elif isinstance(node, ast.ImportFrom) and node.module:
                module_name = node.module.split('.')[0]
                if module_name in self.DEPRECATED_MODULES:
                    self._problem_counter += 1
                    problems.append(DetectedProblem(
                        problem_id=f"IMPORT_{self._problem_counter:06d}",
                        category=ProblemCategory.IMPORT_ERROR,
                        severity=ProblemSeverity.MEDIUM,
                        problem_type="deprecated_import",
                        message=f"使用已弃用的模块: '{module_name}'",
                        file_path=file_path,
                        line_number=node.lineno,
                        code_snippet=self._get_line(content, node.lineno),
                        suggestion=f"使用 '{self.DEPRECATED_MODULES[module_name]}' 替代",
                        confidence=0.95,
                        auto_fixable=True,
                        context={
                            "deprecated_module": module_name,
                            "replacement": self.DEPRECATED_MODULES[module_name]
                        }
                    ))
        
        return problems

    def _detect_shadowed_imports(self, tree: ast.AST, content: str, file_path: str) -> List[DetectedProblem]:
        problems = []
        imported_names = {}
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name.split('.')[0]
                    if name in imported_names:
                        self._problem_counter += 1
                        problems.append(DetectedProblem(
                            problem_id=f"IMPORT_{self._problem_counter:06d}",
                            category=ProblemCategory.IMPORT_ERROR,
                            severity=ProblemSeverity.MEDIUM,
                            problem_type="shadowed_import",
                            message=f"导入名称 '{name}' 覆盖了之前的导入",
                            file_path=file_path,
                            line_number=node.lineno,
                            code_snippet=self._get_line(content, node.lineno),
                            suggestion="使用别名(as)避免名称冲突",
                            confidence=0.85,
                            auto_fixable=True,
                            context={"shadowed_name": name}
                        ))
                    imported_names[name] = node.lineno
        
        return problems

    def _get_module_name(self, node: ast.AST) -> Optional[str]:
        if isinstance(node, ast.Import):
            return node.names[0].name if node.names else None
        elif isinstance(node, ast.ImportFrom):
            return node.module
        return None

    def _get_line(self, content: str, line_number: int) -> str:
        lines = content.split('\n')
        if 1 <= line_number <= len(lines):
            return lines[line_number - 1]
        return ""


class TypeErrorDetector:
    """类型错误检测器"""

    def __init__(self):
        self._problem_counter = 0

    def detect(self, content: str, file_path: str) -> List[DetectedProblem]:
        problems = []
        
        try:
            tree = ast.parse(content)
            problems.extend(self._detect_type_mismatches(tree, content, file_path))
            problems.extend(self._detect_missing_type_annotations(tree, content, file_path))
            problems.extend(self._detect_invalid_type_operations(tree, content, file_path))
            problems.extend(self._detect_incompatible_returns(tree, content, file_path))
            problems.extend(self._detect_attribute_errors(tree, content, file_path))
        except SyntaxError:
            pass
        
        return problems

    def _detect_type_mismatches(self, tree: ast.AST, content: str, file_path: str) -> List[DetectedProblem]:
        problems = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.BinOp):
                if isinstance(node.op, ast.Add):
                    if isinstance(node.left, ast.Constant) and isinstance(node.right, ast.Constant):
                        left_type = type(node.left.value).__name__
                        right_type = type(node.right.value).__name__
                        
                        incompatible_pairs = [
                            ('str', 'int'), ('int', 'str'),
                            ('str', 'float'), ('float', 'str'),
                            ('list', 'int'), ('int', 'list'),
                            ('dict', 'int'), ('int', 'dict'),
                        ]
                        
                        if (left_type, right_type) in incompatible_pairs:
                            self._problem_counter += 1
                            problems.append(DetectedProblem(
                                problem_id=f"TYPE_{self._problem_counter:06d}",
                                category=ProblemCategory.TYPE_ERROR,
                                severity=ProblemSeverity.HIGH,
                                problem_type="type_mismatch",
                                message=f"类型不兼容: 无法将 {left_type} 和 {right_type} 相加",
                                file_path=file_path,
                                line_number=node.lineno,
                                code_snippet=self._get_line(content, node.lineno),
                                suggestion="确保操作数类型兼容",
                                confidence=0.85,
                                auto_fixable=False,
                                context={"left_type": left_type, "right_type": right_type}
                            ))
            
            elif isinstance(node, ast.Compare):
                if isinstance(node.left, ast.Constant) and node.comparators:
                    if isinstance(node.comparators[0], ast.Constant):
                        left_type = type(node.left.value).__name__
                        right_type = type(node.comparators[0].value).__name__
                        
                        if left_type != right_type:
                            self._problem_counter += 1
                            problems.append(DetectedProblem(
                                problem_id=f"TYPE_{self._problem_counter:06d}",
                                category=ProblemCategory.TYPE_ERROR,
                                severity=ProblemSeverity.MEDIUM,
                                problem_type="type_comparison",
                                message=f"比较不同类型的值: {left_type} 和 {right_type}",
                                file_path=file_path,
                                line_number=node.lineno,
                                code_snippet=self._get_line(content, node.lineno),
                                suggestion="确保比较的值类型一致",
                                confidence=0.7,
                                auto_fixable=False
                            ))
        
        return problems

    def _detect_missing_type_annotations(self, tree: ast.AST, content: str, file_path: str) -> List[DetectedProblem]:
        problems = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                missing_annotations = []
                
                for arg in node.args.args:
                    if arg.annotation is None:
                        missing_annotations.append(arg.arg)
                
                if node.returns is None and not any(
                    isinstance(n, ast.Return) and n.value is not None
                    for n in ast.walk(node)
                ):
                    pass
                elif node.returns is None:
                    missing_annotations.append("return")
                
                if missing_annotations:
                    self._problem_counter += 1
                    problems.append(DetectedProblem(
                        problem_id=f"TYPE_{self._problem_counter:06d}",
                        category=ProblemCategory.TYPE_ERROR,
                        severity=ProblemSeverity.LOW,
                        problem_type="missing_type_annotation",
                        message=f"函数 '{node.name}' 缺少类型注解: {', '.join(missing_annotations)}",
                        file_path=file_path,
                        line_number=node.lineno,
                        code_snippet=self._get_line(content, node.lineno),
                        suggestion="添加类型注解以提高代码可读性和类型安全性",
                        confidence=0.9,
                        auto_fixable=True,
                        context={"function_name": node.name, "missing": missing_annotations}
                    ))
        
        return problems

    def _detect_invalid_type_operations(self, tree: ast.AST, content: str, file_path: str) -> List[DetectedProblem]:
        problems = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.BinOp):
                if isinstance(node.op, (ast.Div, ast.FloorDiv, ast.Mod)):
                    if isinstance(node.right, ast.Constant) and node.right.value == 0:
                        self._problem_counter += 1
                        problems.append(DetectedProblem(
                            problem_id=f"TYPE_{self._problem_counter:06d}",
                            category=ProblemCategory.TYPE_ERROR,
                            severity=ProblemSeverity.HIGH,
                            problem_type="division_by_zero",
                            message="除以零错误",
                            file_path=file_path,
                            line_number=node.lineno,
                            code_snippet=self._get_line(content, node.lineno),
                            suggestion="添加除数检查，避免除以零",
                            confidence=1.0,
                            auto_fixable=True
                        ))
            
            elif isinstance(node, ast.Subscript):
                if isinstance(node.slice, ast.Constant):
                    if isinstance(node.slice.value, int) and node.slice.value < 0:
                        pass
        
        return problems

    def _detect_incompatible_returns(self, tree: ast.AST, content: str, file_path: str) -> List[DetectedProblem]:
        problems = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                return_types = set()
                
                for child in ast.walk(node):
                    if isinstance(child, ast.Return) and child.value:
                        if isinstance(child.value, ast.Constant):
                            return_types.add(type(child.value.value).__name__)
                        elif isinstance(child.value, ast.Name):
                            return_types.add('variable')
                        elif isinstance(child.value, ast.Call):
                            return_types.add('call_result')
                        elif isinstance(child.value, (ast.List, ast.ListComp)):
                            return_types.add('list')
                        elif isinstance(child.value, (ast.Dict, ast.DictComp)):
                            return_types.add('dict')
                        elif isinstance(child.value, ast.Tuple):
                            return_types.add('tuple')
                        elif isinstance(child.value, ast.Constant) and child.value.value is None:
                            return_types.add('None')
                
                if len(return_types) > 1 and 'None' not in return_types:
                    self._problem_counter += 1
                    problems.append(DetectedProblem(
                        problem_id=f"TYPE_{self._problem_counter:06d}",
                        category=ProblemCategory.TYPE_ERROR,
                        severity=ProblemSeverity.MEDIUM,
                        problem_type="inconsistent_return_types",
                        message=f"函数 '{node.name}' 返回类型不一致: {', '.join(return_types)}",
                        file_path=file_path,
                        line_number=node.lineno,
                        code_snippet=self._get_line(content, node.lineno),
                        suggestion="确保函数所有返回路径返回相同类型的值",
                        confidence=0.75,
                        auto_fixable=False,
                        context={"function_name": node.name, "return_types": list(return_types)}
                    ))
        
        return problems

    def _detect_attribute_errors(self, tree: ast.AST, content: str, file_path: str) -> List[DetectedProblem]:
        problems = []
        
        known_types = {
            'str': {'upper', 'lower', 'strip', 'split', 'join', 'replace', 'find', 'startswith', 'endswith'},
            'list': {'append', 'extend', 'insert', 'remove', 'pop', 'clear', 'index', 'count', 'sort', 'reverse'},
            'dict': {'get', 'keys', 'values', 'items', 'pop', 'popitem', 'clear', 'update', 'setdefault'},
            'set': {'add', 'remove', 'discard', 'pop', 'clear', 'union', 'intersection', 'difference'},
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute):
                if isinstance(node.value, ast.Constant):
                    value_type = type(node.value.value).__name__
                    if value_type in known_types:
                        if node.attr not in known_types[value_type]:
                            self._problem_counter += 1
                            problems.append(DetectedProblem(
                                problem_id=f"TYPE_{self._problem_counter:06d}",
                                category=ProblemCategory.TYPE_ERROR,
                                severity=ProblemSeverity.HIGH,
                                problem_type="attribute_error",
                                message=f"类型 '{value_type}' 没有属性 '{node.attr}'",
                                file_path=file_path,
                                line_number=node.lineno,
                                code_snippet=self._get_line(content, node.lineno),
                                suggestion=f"检查 '{value_type}' 类型的可用属性",
                                confidence=0.9,
                                auto_fixable=False,
                                context={"type": value_type, "attribute": node.attr}
                            ))
        
        return problems

    def _get_line(self, content: str, line_number: int) -> str:
        lines = content.split('\n')
        if 1 <= line_number <= len(lines):
            return lines[line_number - 1]
        return ""


class SecurityVulnerabilityDetector:
    """安全漏洞检测器"""

    def __init__(self):
        self._problem_counter = 0

    VULNERABILITY_PATTERNS = [
        {
            'pattern': r'password\s*=\s*["\'][^"\']+["\']',
            'type': 'hardcoded_password',
            'message': '硬编码密码',
            'severity': ProblemSeverity.CRITICAL,
            'suggestion': '使用环境变量或配置文件存储密码',
            'cwe': 'CWE-259',
            'owasp': 'A07:2021 - Identification and Authentication Failures'
        },
        {
            'pattern': r'secret\s*=\s*["\'][^"\']+["\']',
            'type': 'hardcoded_secret',
            'message': '硬编码密钥',
            'severity': ProblemSeverity.CRITICAL,
            'suggestion': '使用环境变量或密钥管理服务',
            'cwe': 'CWE-798',
            'owasp': 'A07:2021 - Identification and Authentication Failures'
        },
        {
            'pattern': r'api_key\s*=\s*["\'][^"\']+["\']',
            'type': 'hardcoded_api_key',
            'message': '硬编码 API 密钥',
            'severity': ProblemSeverity.CRITICAL,
            'suggestion': '使用环境变量存储 API 密钥',
            'cwe': 'CWE-798',
            'owasp': 'A07:2021 - Identification and Authentication Failures'
        },
        {
            'pattern': r'token\s*=\s*["\'][^"\']+["\']',
            'type': 'hardcoded_token',
            'message': '硬编码令牌',
            'severity': ProblemSeverity.CRITICAL,
            'suggestion': '使用环境变量或安全的令牌存储',
            'cwe': 'CWE-798',
            'owasp': 'A07:2021 - Identification and Authentication Failures'
        },
        {
            'pattern': r'eval\s*\(',
            'type': 'eval_usage',
            'message': '使用 eval() 函数，存在代码注入风险',
            'severity': ProblemSeverity.HIGH,
            'suggestion': '使用 ast.literal_eval() 或其他安全的替代方案',
            'cwe': 'CWE-95',
            'owasp': 'A03:2021 - Injection'
        },
        {
            'pattern': r'exec\s*\(',
            'type': 'exec_usage',
            'message': '使用 exec() 函数，存在代码注入风险',
            'severity': ProblemSeverity.HIGH,
            'suggestion': '避免动态执行代码，使用更安全的替代方案',
            'cwe': 'CWE-95',
            'owasp': 'A03:2021 - Injection'
        },
        {
            'pattern': r'yaml\.load\s*\((?!.*Loader)',
            'type': 'unsafe_yaml_load',
            'message': '不安全的 YAML 加载，可能导致代码执行',
            'severity': ProblemSeverity.HIGH,
            'suggestion': '使用 yaml.safe_load() 或 yaml.load(..., Loader=yaml.SafeLoader)',
            'cwe': 'CWE-502',
            'owasp': 'A08:2021 - Software and Data Integrity Failures'
        },
        {
            'pattern': r'pickle\.loads?\s*\(',
            'type': 'pickle_usage',
            'message': '使用 pickle 可能导致反序列化漏洞',
            'severity': ProblemSeverity.HIGH,
            'suggestion': '避免使用 pickle 处理不可信数据，考虑使用 JSON',
            'cwe': 'CWE-502',
            'owasp': 'A08:2021 - Software and Data Integrity Failures'
        },
        {
            'pattern': r'subprocess\.(?:call|run|Popen)\s*\([^)]*shell\s*=\s*True',
            'type': 'shell_injection',
            'message': '使用 shell=True 存在命令注入风险',
            'severity': ProblemSeverity.HIGH,
            'suggestion': '避免使用 shell=True，使用列表形式传递参数',
            'cwe': 'CWE-78',
            'owasp': 'A03:2021 - Injection'
        },
        {
            'pattern': r'os\.system\s*\(',
            'type': 'os_system',
            'message': '使用 os.system() 存在命令注入风险',
            'severity': ProblemSeverity.HIGH,
            'suggestion': '使用 subprocess 模块并避免 shell=True',
            'cwe': 'CWE-78',
            'owasp': 'A03:2021 - Injection'
        },
        {
            'pattern': r'cursor\.execute\s*\([^)]*\+',
            'type': 'sql_injection',
            'message': 'SQL 字符串拼接，存在注入风险',
            'severity': ProblemSeverity.HIGH,
            'suggestion': '使用参数化查询: cursor.execute("SELECT * FROM table WHERE id = %s", (id,))',
            'cwe': 'CWE-89',
            'owasp': 'A03:2021 - Injection'
        },
        {
            'pattern': r'execute\s*\([^)]*["\'].*%s.*["\'].*\%',
            'type': 'sql_injection_format',
            'message': '使用字符串格式化构建 SQL，存在注入风险',
            'severity': ProblemSeverity.HIGH,
            'suggestion': '使用参数化查询而非字符串格式化',
            'cwe': 'CWE-89',
            'owasp': 'A03:2021 - Injection'
        },
        {
            'pattern': r'ssl\._create_unverified_context',
            'type': 'ssl_verification_disabled',
            'message': '禁用 SSL 证书验证，存在中间人攻击风险',
            'severity': ProblemSeverity.HIGH,
            'suggestion': '使用 ssl.create_default_context() 并启用证书验证',
            'cwe': 'CWE-295',
            'owasp': 'A02:2021 - Cryptographic Failures'
        },
        {
            'pattern': r'verify\s*=\s*False',
            'type': 'ssl_verify_false',
            'message': '禁用 SSL 证书验证',
            'severity': ProblemSeverity.HIGH,
            'suggestion': '启用 SSL 证书验证: verify=True',
            'cwe': 'CWE-295',
            'owasp': 'A02:2021 - Cryptographic Failures'
        },
        {
            'pattern': r'(?:md5|sha1)\s*\(',
            'type': 'weak_hash',
            'message': '使用弱哈希算法 (MD5/SHA1)',
            'severity': ProblemSeverity.MEDIUM,
            'suggestion': '使用更强的哈希算法如 SHA-256 或 SHA-3',
            'cwe': 'CWE-328',
            'owasp': 'A02:2021 - Cryptographic Failures'
        },
        {
            'pattern': r'random\.(?:random|randint|choice)\s*\(',
            'type': 'insecure_random',
            'message': '使用不安全的随机数生成器',
            'severity': ProblemSeverity.MEDIUM,
            'suggestion': '对于安全相关用途，使用 secrets 模块',
            'cwe': 'CWE-338',
            'owasp': 'A02:2021 - Cryptographic Failures'
        },
        {
            'pattern': r'tempfile\.mktemp\s*\(',
            'type': 'insecure_tempfile',
            'message': '使用不安全的临时文件创建方式',
            'severity': ProblemSeverity.MEDIUM,
            'suggestion': '使用 tempfile.mkstemp() 或 tempfile.TemporaryFile()',
            'cwe': 'CWE-377',
            'owasp': 'A01:2021 - Broken Access Control'
        },
        {
            'pattern': r'chmod\s*\([^)]*0o?777',
            'type': 'insecure_permission',
            'message': '设置过于宽松的文件权限 (777)',
            'severity': ProblemSeverity.MEDIUM,
            'suggestion': '使用更严格的权限，如 0o644 或 0o755',
            'cwe': 'CWE-732',
            'owasp': 'A01:2021 - Broken Access Control'
        },
        {
            'pattern': r'assert\s+',
            'type': 'assert_usage',
            'message': '使用 assert 进行安全检查，在生产环境中可能被禁用',
            'severity': ProblemSeverity.MEDIUM,
            'suggestion': '使用显式的条件检查和异常',
            'cwe': 'CWE-617',
            'owasp': 'A05:2021 - Security Misconfiguration'
        },
        {
            'pattern': r'input\s*\(',
            'type': 'input_usage',
            'message': '使用 input() 函数，需验证输入',
            'severity': ProblemSeverity.LOW,
            'suggestion': '验证和清理用户输入',
            'cwe': 'CWE-20',
            'owasp': 'A03:2021 - Injection'
        },
    ]

    def detect(self, content: str, file_path: str) -> List[DetectedProblem]:
        problems = []
        
        problems.extend(self._detect_pattern_vulnerabilities(content, file_path))
        problems.extend(self._detect_ast_vulnerabilities(content, file_path))
        
        return problems

    def _detect_pattern_vulnerabilities(self, content: str, file_path: str) -> List[DetectedProblem]:
        problems = []
        lines = content.split('\n')
        
        for vuln in self.VULNERABILITY_PATTERNS:
            pattern = re.compile(vuln['pattern'], re.IGNORECASE)
            
            for line_num, line in enumerate(lines, 1):
                if pattern.search(line):
                    self._problem_counter += 1
                    problems.append(DetectedProblem(
                        problem_id=f"SECURITY_{self._problem_counter:06d}",
                        category=ProblemCategory.SECURITY_VULNERABILITY,
                        severity=vuln['severity'],
                        problem_type=vuln['type'],
                        message=vuln['message'],
                        file_path=file_path,
                        line_number=line_num,
                        code_snippet=line.strip(),
                        suggestion=vuln['suggestion'],
                        confidence=0.9,
                        auto_fixable=vuln['severity'] in [ProblemSeverity.LOW, ProblemSeverity.MEDIUM],
                        cwe_id=vuln.get('cwe'),
                        owasp_category=vuln.get('owasp'),
                        context={"pattern": vuln['pattern']}
                    ))
        
        return problems

    def _detect_ast_vulnerabilities(self, content: str, file_path: str) -> List[DetectedProblem]:
        problems = []
        
        try:
            tree = ast.parse(content)
            problems.extend(self._detect_unsafe_deserialization(tree, content, file_path))
            problems.extend(self._detect_path_traversal(tree, content, file_path))
            problems.extend(self._detect_insecure_file_operations(tree, content, file_path))
        except SyntaxError:
            pass
        
        return problems

    def _detect_unsafe_deserialization(self, tree: ast.AST, content: str, file_path: str) -> List[DetectedProblem]:
        problems = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr in ('loads', 'load'):
                        if isinstance(node.func.value, ast.Name):
                            if node.func.value.id == 'pickle':
                                self._problem_counter += 1
                                problems.append(DetectedProblem(
                                    problem_id=f"SECURITY_{self._problem_counter:06d}",
                                    category=ProblemCategory.SECURITY_VULNERABILITY,
                                    severity=ProblemSeverity.HIGH,
                                    problem_type="pickle_deserialization",
                                    message="pickle 反序列化可能导致远程代码执行",
                                    file_path=file_path,
                                    line_number=node.lineno,
                                    code_snippet=self._get_line(content, node.lineno),
                                    suggestion="避免使用 pickle 处理不可信数据",
                                    confidence=0.9,
                                    auto_fixable=False,
                                    cwe_id="CWE-502",
                                    owasp_category="A08:2021 - Software and Data Integrity Failures"
                                ))
        
        return problems

    def _detect_path_traversal(self, tree: ast.AST, content: str, file_path: str) -> List[DetectedProblem]:
        problems = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr in ('open', 'read', 'write', 'send_file'):
                        if node.args:
                            arg = node.args[0]
                            if isinstance(arg, ast.BinOp) and isinstance(arg.op, ast.Add):
                                self._problem_counter += 1
                                problems.append(DetectedProblem(
                                    problem_id=f"SECURITY_{self._problem_counter:06d}",
                                    category=ProblemCategory.SECURITY_VULNERABILITY,
                                    severity=ProblemSeverity.MEDIUM,
                                    problem_type="potential_path_traversal",
                                    message="潜在的路径遍历漏洞",
                                    file_path=file_path,
                                    line_number=node.lineno,
                                    code_snippet=self._get_line(content, node.lineno),
                                    suggestion="验证和清理文件路径，使用 os.path.basename() 或白名单",
                                    confidence=0.7,
                                    auto_fixable=False,
                                    cwe_id="CWE-22",
                                    owasp_category="A01:2021 - Broken Access Control"
                                ))
        
        return problems

    def _detect_insecure_file_operations(self, tree: ast.AST, content: str, file_path: str) -> List[DetectedProblem]:
        problems = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id == 'open':
                        has_encoding = any(
                            kw.arg == 'encoding' for kw in node.keywords
                        )
                        if not has_encoding:
                            self._problem_counter += 1
                            problems.append(DetectedProblem(
                                problem_id=f"SECURITY_{self._problem_counter:06d}",
                                category=ProblemCategory.SECURITY_VULNERABILITY,
                                severity=ProblemSeverity.LOW,
                                problem_type="missing_encoding",
                                message="打开文件时未指定编码，可能导致编码问题",
                                file_path=file_path,
                                line_number=node.lineno,
                                code_snippet=self._get_line(content, node.lineno),
                                suggestion="指定编码: open(file, mode, encoding='utf-8')",
                                confidence=0.8,
                                auto_fixable=True
                            ))
        
        return problems

    def _get_line(self, content: str, line_number: int) -> str:
        lines = content.split('\n')
        if 1 <= line_number <= len(lines):
            return lines[line_number - 1]
        return ""


class ProblemDetector:
    """综合问题检测器主类"""

    def __init__(self):
        self.syntax_detector = SyntaxErrorDetector()
        self.import_detector = ImportErrorDetector()
        self.type_detector = TypeErrorDetector()
        self.security_detector = SecurityVulnerabilityDetector()
        self._report_counter = 0

    def detect_all(self, content: str, file_path: str) -> List[DetectedProblem]:
        all_problems = []
        
        all_problems.extend(self.syntax_detector.detect(content, file_path))
        all_problems.extend(self.import_detector.detect(content, file_path))
        all_problems.extend(self.type_detector.detect(content, file_path))
        all_problems.extend(self.security_detector.detect(content, file_path))
        
        all_problems.sort(key=lambda p: (
            p.line_number,
            {'critical': 0, 'high': 1, 'medium': 2, 'low': 3, 'info': 4}.get(p.severity.value, 5)
        ))
        
        return all_problems

    def detect_syntax(self, content: str, file_path: str) -> List[DetectedProblem]:
        return self.syntax_detector.detect(content, file_path)

    def detect_imports(self, content: str, file_path: str) -> List[DetectedProblem]:
        return self.import_detector.detect(content, file_path)

    def detect_types(self, content: str, file_path: str) -> List[DetectedProblem]:
        return self.type_detector.detect(content, file_path)

    def detect_security(self, content: str, file_path: str) -> List[DetectedProblem]:
        return self.security_detector.detect(content, file_path)

    def generate_report(self, problems: List[DetectedProblem], file_path: str) -> Dict[str, Any]:
        self._report_counter += 1
        
        summary = defaultdict(int)
        severity_counts = defaultdict(int)
        category_counts = defaultdict(int)
        
        for problem in problems:
            summary[problem.category.name] += 1
            summary[problem.severity.value] += 1
            severity_counts[problem.severity.value] += 1
            category_counts[problem.category.name] += 1
        
        return {
            "report_id": f"REPORT_{self._report_counter:06d}",
            "file_path": file_path,
            "total_problems": len(problems),
            "generated_at": datetime.now().isoformat(),
            "problems": [p.to_dict() for p in problems],
            "summary": dict(summary),
            "severity_distribution": dict(severity_counts),
            "category_distribution": dict(category_counts),
            "auto_fixable_count": sum(1 for p in problems if p.auto_fixable),
            "security_issues": sum(1 for p in problems if p.category == ProblemCategory.SECURITY_VULNERABILITY),
            "critical_issues": sum(1 for p in problems if p.severity == ProblemSeverity.CRITICAL),
        }

    def scan_file(self, file_path: str) -> Dict[str, Any]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return {
                "error": str(e),
                "file_path": file_path
            }
        
        problems = self.detect_all(content, file_path)
        return self.generate_report(problems, file_path)

    def scan_directory(self, directory: str, pattern: str = "*.py") -> List[Dict[str, Any]]:
        reports = []
        dir_path = Path(directory)
        
        for file_path in dir_path.rglob(pattern):
            if file_path.is_file():
                report = self.scan_file(str(file_path))
                reports.append(report)
        
        return reports


def main():
    import argparse

    parser = argparse.ArgumentParser(description="综合问题检测器")
    parser.add_argument("--file", type=str, help="要检测的文件路径")
    parser.add_argument("--directory", type=str, help="要扫描的目录")
    parser.add_argument("--detect-all", action="store_true", help="检测所有类型问题")
    parser.add_argument("--detect-syntax", action="store_true", help="检测语法错误")
    parser.add_argument("--detect-imports", action="store_true", help="检测导入问题")
    parser.add_argument("--detect-types", action="store_true", help="检测类型问题")
    parser.add_argument("--detect-security", action="store_true", help="检测安全漏洞")
    parser.add_argument("--report", type=str, help="报告输出路径")
    parser.add_argument("--format", choices=['json', 'text'], default='text', help="输出格式")

    args = parser.parse_args()

    detector = ProblemDetector()

    if args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"读取文件失败: {e}")
            return 1

        problems = []

        if args.detect_all or not (args.detect_syntax or args.detect_imports or args.detect_types or args.detect_security):
            problems = detector.detect_all(content, args.file)
        else:
            if args.detect_syntax:
                problems.extend(detector.detect_syntax(content, args.file))
            if args.detect_imports:
                problems.extend(detector.detect_imports(content, args.file))
            if args.detect_types:
                problems.extend(detector.detect_types(content, args.file))
            if args.detect_security:
                problems.extend(detector.detect_security(content, args.file))

        report = detector.generate_report(problems, args.file)

        if args.format == 'json':
            output = json.dumps(report, indent=2, ensure_ascii=False)
        else:
            lines = [
                f"\n{'='*60}",
                f"问题检测报告: {report['report_id']}",
                f"{'='*60}",
                f"文件: {report['file_path']}",
                f"总问题数: {report['total_problems']}",
                f"可自动修复: {report['auto_fixable_count']}",
                f"安全问题: {report['security_issues']}",
                f"严重问题: {report['critical_issues']}",
                "",
            ]
            
            if report['severity_distribution']:
                lines.append("严重程度分布:")
                for severity, count in sorted(report['severity_distribution'].items()):
                    lines.append(f"  {severity}: {count}")
                lines.append("")
            
            if report['category_distribution']:
                lines.append("问题类别分布:")
                for category, count in sorted(report['category_distribution'].items()):
                    lines.append(f"  {category}: {count}")
                lines.append("")
            
            if problems:
                lines.append("问题列表:")
                for problem in problems[:30]:
                    severity_marker = {
                        'critical': '🔴',
                        'high': '🟠',
                        'medium': '🟡',
                        'low': '🔵',
                        'info': 'ℹ️'
                    }.get(problem.severity.value, '❓')
                    lines.append(f"  {severity_marker} [{problem.category.name}] {problem.message} (行 {problem.line_number})")
                    if problem.suggestion:
                        lines.append(f"      建议: {problem.suggestion}")
            
            output = '\n'.join(lines)

        print(output)

        if args.report:
            with open(args.report, 'w', encoding='utf-8') as f:
                f.write(json.dumps(report, indent=2, ensure_ascii=False))
            print(f"\n报告已保存: {args.report}")

    elif args.directory:
        reports = detector.scan_directory(args.directory)
        total_problems = sum(r.get('total_problems', 0) for r in reports)
        total_files = len(reports)
        files_with_issues = sum(1 for r in reports if r.get('total_problems', 0) > 0)
        
        print(f"\n扫描完成:")
        print(f"  扫描文件数: {total_files}")
        print(f"  有问题的文件: {files_with_issues}")
        print(f"  总问题数: {total_problems}")
        
        if args.report:
            with open(args.report, 'w', encoding='utf-8') as f:
                json.dump({
                    "summary": {
                        "total_files": total_files,
                        "files_with_issues": files_with_issues,
                        "total_problems": total_problems
                    },
                    "reports": reports
                }, f, indent=2, ensure_ascii=False)
            print(f"\n报告已保存: {args.report}")

    else:
        parser.print_help()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
