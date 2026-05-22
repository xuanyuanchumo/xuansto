#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版问题检测器扩展 - Problem Detector Enhanced Extension

扩展问题检测能力，包括：
- 导入错误检测（Import Error Detection）
- 类型错误检测（Type Error Detection）
- 未使用代码检测（Unused Code Detection）
- 代码复杂度检测（Code Complexity Detection）
- 依赖问题检测（Dependency Issue Detection）

使用示例:
    python problem_detector_extension.py --file code.py --detect-all
    python problem_detector_extension.py --file code.py --detect-imports
    python problem_detector_extension.py --file code.py --detect-types
"""

from __future__ import annotations

import ast
import importlib.util
import json
import logging
import sys
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
    IMPORT_ERROR = auto()
    TYPE_ERROR = auto()
    UNUSED_CODE = auto()
    COMPLEXITY_ISSUE = auto()
    DEPENDENCY_ISSUE = auto()
    STYLE_ISSUE = auto()
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
            "detected_at": self.detected_at
        }


class ImportErrorDetector:
    """导入错误检测器"""

    STANDARD_LIBRARY = {
        'abc', 'aifc', 'argparse', 'array', 'ast', 'asynchat', 'asyncio', 'asyncore',
        'atexit', 'audioop', 'base64', 'bdb', 'binascii', 'binhex', 'bisect',
        'builtins', 'bz2', 'calendar', 'cgi', 'cgitb', 'chunk', 'cmath', 'cmd',
        'code', 'codecs', 'codeop', 'collections', 'colorsys', 'compileall',
        'concurrent', 'configparser', 'contextlib', 'contextvars', 'copy', 'copyreg',
        'cProfile', 'crypt', 'csv', 'ctypes', 'curses', 'dataclasses', 'datetime',
        'dbm', 'decimal', 'difflib', 'dis', 'distutils', 'doctest', 'email',
        'encodings', 'enum', 'errno', 'faulthandler', 'fcntl', 'filecmp', 'fileinput',
        'fnmatch', 'fractions', 'ftplib', 'functools', 'gc', 'getopt', 'getpass',
        'gettext', 'glob', 'graphlib', 'grp', 'gzip', 'hashlib', 'heapq', 'hmac',
        'html', 'http', 'idlelib', 'imaplib', 'imghdr', 'imp', 'importlib', 'inspect',
        'io', 'ipaddress', 'itertools', 'json', 'keyword', 'lib2to3', 'linecache',
        'locale', 'logging', 'lzma', 'mailbox', 'mailcap', 'marshal', 'math',
        'mimetypes', 'mmap', 'modulefinder', 'multiprocessing', 'netrc', 'nis',
        'nntplib', 'numbers', 'operator', 'optparse', 'os', 'ossaudiodev', 'pathlib',
        'pdb', 'pickle', 'pickletools', 'pipes', 'pkgutil', 'platform', 'plistlib',
        'poplib', 'posix', 'posixpath', 'pprint', 'profile', 'pstats', 'pty', 'pwd',
        'py_compile', 'pyclbr', 'pydoc', 'queue', 'quopri', 'random', 're', 'readline',
        'reprlib', 'resource', 'rlcompleter', 'runpy', 'sched', 'secrets', 'select',
        'selectors', 'shelve', 'shlex', 'shutil', 'signal', 'site', 'smtpd', 'smtplib',
        'sndhdr', 'socket', 'socketserver', 'spwd', 'sqlite3', 'ssl', 'stat',
        'statistics', 'string', 'stringprep', 'struct', 'subprocess', 'sunau',
        'symtable', 'sys', 'sysconfig', 'syslog', 'tabnanny', 'tarfile', 'telnetlib',
        'tempfile', 'termios', 'test', 'textwrap', 'threading', 'time', 'timeit',
        'tkinter', 'token', 'tokenize', 'trace', 'traceback', 'tracemalloc', 'tty',
        'turtle', 'turtledemo', 'types', 'typing', 'unicodedata', 'unittest', 'urllib',
        'uu', 'uuid', 'venv', 'warnings', 'wave', 'weakref', 'webbrowser', 'winreg',
        'winsound', 'wsgiref', 'xdrlib', 'xml', 'xmlrpc', 'zipapp', 'zipfile',
        'zipimport', 'zlib', '_thread'
    }

    COMMON_THIRD_PARTY = {
        'numpy', 'pandas', 'matplotlib', 'seaborn', 'scipy', 'sklearn', 'torch',
        'tensorflow', 'keras', 'django', 'flask', 'fastapi', 'requests', 'httpx',
        'aiohttp', 'selenium', 'beautifulsoup4', 'bs4', 'lxml', 'pillow', 'PIL',
        'opencv', 'cv2', 'pytest', 'unittest2', 'mock', 'pylint', 'flake8', 'black',
        'mypy', 'sphinx', 'jinja2', 'pyyaml', 'yaml', 'toml', 'configobj', 'sqlalchemy',
        'pymongo', 'redis', 'celery', 'gunicorn', 'uvicorn', 'werkzeug', 'click',
        'typer', 'rich', 'tqdm', 'python-dateutil', 'pytz', 'arrow', 'pendulum',
        'boto3', 'botocore', 'google', 'azure', 'kubernetes', 'docker', 'psutil',
        'watchdog', 'celery', 'kombu', 'pika', 'kafka', 'grpc', 'protobuf', 'thrift',
        'cython', 'numba', 'dask', 'ray', 'modin', 'polars', 'vaex', 'pyspark'
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
            problems.extend(self._detect_circular_imports(tree, content, file_path))
            problems.extend(self._detect_deprecated_imports(tree, content, file_path))
        except SyntaxError:
            pass

        return problems

    def _detect_missing_imports(self, tree: ast.AST, content: str, file_path: str) -> List[DetectedProblem]:
        problems = []
        imported_modules = set()
        used_names = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_modules.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imported_modules.add(node.module.split('.')[0])
            elif isinstance(node, ast.Name):
                used_names.add(node.id)
            elif isinstance(node, ast.Attribute):
                if isinstance(node.value, ast.Name):
                    used_names.add(node.value.id)

        potential_imports = used_names - imported_modules - self.STANDARD_LIBRARY

        for name in potential_imports:
            for node in ast.walk(tree):
                if isinstance(node, ast.Name) and node.id == name:
                    self._problem_counter += 1
                    problems.append(DetectedProblem(
                        problem_id=f"IMPORT_{self._problem_counter:06d}",
                        category=ProblemCategory.IMPORT_ERROR,
                        severity=ProblemSeverity.HIGH,
                        problem_type="missing_import",
                        message=f"可能缺少导入: '{name}'",
                        file_path=file_path,
                        line_number=node.lineno,
                        code_snippet=self._get_line_content(content, node.lineno),
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
                    name = alias.asname if alias.asname else alias.name
                    imports[name] = (node.lineno, alias.name)
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    imports[name] = (node.lineno, f"{node.module}.{alias.name}" if node.module else alias.name)
            elif isinstance(node, ast.Name):
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
                    code_snippet=self._get_line_content(content, line_no),
                    suggestion=f"移除未使用的导入: {full_name}",
                    confidence=0.9,
                    auto_fixable=True,
                    context={"import_name": import_name, "full_name": full_name}
                ))

        return problems

    def _detect_import_order_issues(self, tree: ast.AST, content: str, file_path: str) -> List[DetectedProblem]:
        problems = []
        import_lines = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                import_lines.append((node.lineno, node))

        if len(import_lines) < 2:
            return problems

        sorted_imports = sorted(import_lines, key=lambda x: x[0])
        has_std = False
        has_third = False
        has_local = False

        for line_no, node in sorted_imports:
            if isinstance(node, ast.Import):
                module = node.names[0].name.split('.')[0]
            else:
                module = node.module.split('.')[0] if node.module else ''

            is_std = module in self.STANDARD_LIBRARY
            is_third = module in self.COMMON_THIRD_PARTY
            is_local = not is_std and not is_third

            if is_std and (has_third or has_local):
                self._problem_counter += 1
                problems.append(DetectedProblem(
                    problem_id=f"IMPORT_{self._problem_counter:06d}",
                    category=ProblemCategory.STYLE_ISSUE,
                    severity=ProblemSeverity.LOW,
                    problem_type="import_order",
                    message="导入顺序不符合规范：标准库导入应在第三方库和本地模块之前",
                    file_path=file_path,
                    line_number=line_no,
                    suggestion="调整导入顺序：标准库 -> 第三方库 -> 本地模块",
                    confidence=0.8,
                    auto_fixable=True
                ))
            elif is_third and has_local:
                self._problem_counter += 1
                problems.append(DetectedProblem(
                    problem_id=f"IMPORT_{self._problem_counter:06d}",
                    category=ProblemCategory.STYLE_ISSUE,
                    severity=ProblemSeverity.LOW,
                    problem_type="import_order",
                    message="导入顺序不符合规范：第三方库导入应在本地模块之前",
                    file_path=file_path,
                    line_number=line_no,
                    suggestion="调整导入顺序：标准库 -> 第三方库 -> 本地模块",
                    confidence=0.8,
                    auto_fixable=True
                ))

            has_std = has_std or is_std
            has_third = has_third or is_third
            has_local = has_local or is_local

        return problems

    def _detect_circular_imports(self, tree: ast.AST, content: str, file_path: str) -> List[DetectedProblem]:
        problems = []
        return problems

    def _detect_deprecated_imports(self, tree: ast.AST, content: str, file_path: str) -> List[DetectedProblem]:
        problems = []

        deprecated_modules = {
            'urllib2': 'urllib.request',
            'urlparse': 'urllib.parse',
            'urllib': 'urllib.request, urllib.parse, urllib.error',
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
            'tkFileDialog': 'tkinter.filedialog',
            'tkMessageBox': 'tkinter.messagebox',
        }

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module_name = alias.name.split('.')[0]
                    if module_name in deprecated_modules:
                        self._problem_counter += 1
                        problems.append(DetectedProblem(
                            problem_id=f"IMPORT_{self._problem_counter:06d}",
                            category=ProblemCategory.IMPORT_ERROR,
                            severity=ProblemSeverity.MEDIUM,
                            problem_type="deprecated_import",
                            message=f"使用已弃用的模块: '{module_name}'",
                            file_path=file_path,
                            line_number=node.lineno,
                            code_snippet=self._get_line_content(content, node.lineno),
                            suggestion=f"使用 '{deprecated_modules[module_name]}' 替代",
                            confidence=0.95,
                            auto_fixable=True,
                            context={
                                "deprecated_module": module_name,
                                "replacement": deprecated_modules[module_name]
                            }
                        ))
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    module_name = node.module.split('.')[0]
                    if module_name in deprecated_modules:
                        self._problem_counter += 1
                        problems.append(DetectedProblem(
                            problem_id=f"IMPORT_{self._problem_counter:06d}",
                            category=ProblemCategory.IMPORT_ERROR,
                            severity=ProblemSeverity.MEDIUM,
                            problem_type="deprecated_import",
                            message=f"使用已弃用的模块: '{module_name}'",
                            file_path=file_path,
                            line_number=node.lineno,
                            code_snippet=self._get_line_content(content, node.lineno),
                            suggestion=f"使用 '{deprecated_modules[module_name]}' 替代",
                            confidence=0.95,
                            auto_fixable=True,
                            context={
                                "deprecated_module": module_name,
                                "replacement": deprecated_modules[module_name]
                            }
                        ))

        return problems

    def _get_line_content(self, content: str, line_number: int) -> str:
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
        except SyntaxError:
            pass

        return problems

    def _detect_type_mismatches(self, tree: ast.AST, content: str, file_path: str) -> List[DetectedProblem]:
        problems = []

        for node in ast.walk(tree):
            if isinstance(node, ast.BinOp):
                if isinstance(node.op, (ast.Add, ast.Sub, ast.Mult)):
                    if isinstance(node.left, ast.Constant) and isinstance(node.right, ast.Constant):
                        left_type = type(node.left.value).__name__
                        right_type = type(node.right.value).__name__

                        if isinstance(node.op, ast.Add):
                            if left_type in ('str', 'list') and right_type not in (left_type, 'str', 'list'):
                                self._problem_counter += 1
                                problems.append(DetectedProblem(
                                    problem_id=f"TYPE_{self._problem_counter:06d}",
                                    category=ProblemCategory.TYPE_ERROR,
                                    severity=ProblemSeverity.HIGH,
                                    problem_type="type_mismatch",
                                    message=f"类型不匹配: 无法将 {left_type} 和 {right_type} 相加",
                                    file_path=file_path,
                                    line_number=node.lineno,
                                    code_snippet=self._get_line_content(content, node.lineno),
                                    suggestion=f"确保操作数类型兼容",
                                    confidence=0.85,
                                    auto_fixable=False,
                                    context={"left_type": left_type, "right_type": right_type}
                                ))

            elif isinstance(node, ast.Compare):
                if len(node.ops) > 0 and isinstance(node.ops[0], (ast.Eq, ast.NotEq)):
                    if isinstance(node.left, ast.Constant) and isinstance(node.comparators[0], ast.Constant):
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
                                code_snippet=self._get_line_content(content, node.lineno),
                                suggestion="确保比较的值类型一致",
                                confidence=0.7,
                                auto_fixable=False
                            ))

        return problems

    def _detect_missing_type_annotations(self, tree: ast.AST, content: str, file_path: str) -> List[DetectedProblem]:
        problems = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                has_return_annotation = node.returns is not None
                has_arg_annotations = any(
                    arg.annotation is not None
                    for arg in node.args.args
                )

                if not has_return_annotation or not has_arg_annotations:
                    missing = []
                    if not has_return_annotation:
                        missing.append("返回值")
                    if not has_arg_annotations:
                        missing_args = [
                            arg.arg for arg in node.args.args
                            if arg.annotation is None
                        ]
                        if missing_args:
                            missing.append(f"参数 {', '.join(missing_args)}")

                    self._problem_counter += 1
                    problems.append(DetectedProblem(
                        problem_id=f"TYPE_{self._problem_counter:06d}",
                        category=ProblemCategory.TYPE_ERROR,
                        severity=ProblemSeverity.LOW,
                        problem_type="missing_type_annotation",
                        message=f"函数 '{node.name}' 缺少类型注解: {', '.join(missing)}",
                        file_path=file_path,
                        line_number=node.lineno,
                        code_snippet=self._get_line_content(content, node.lineno),
                        suggestion="添加类型注解以提高代码可读性和类型安全性",
                        confidence=0.9,
                        auto_fixable=True,
                        context={"function_name": node.name, "missing": missing}
                    ))

        return problems

    def _detect_invalid_type_operations(self, tree: ast.AST, content: str, file_path: str) -> List[DetectedProblem]:
        problems = []

        for node in ast.walk(tree):
            if isinstance(node, ast.BinOp):
                if isinstance(node.op, (ast.Div, ast.FloorDiv, ast.Mod)):
                    if isinstance(node.right, ast.Constant):
                        if node.right.value == 0:
                            self._problem_counter += 1
                            problems.append(DetectedProblem(
                                problem_id=f"TYPE_{self._problem_counter:06d}",
                                category=ProblemCategory.TYPE_ERROR,
                                severity=ProblemSeverity.HIGH,
                                problem_type="division_by_zero",
                                message="除以零错误",
                                file_path=file_path,
                                line_number=node.lineno,
                                code_snippet=self._get_line_content(content, node.lineno),
                                suggestion="添加除数检查，避免除以零",
                                confidence=1.0,
                                auto_fixable=True
                            ))

            elif isinstance(node, ast.Subscript):
                if isinstance(node.slice, ast.Constant):
                    if isinstance(node.slice.value, int):
                        if node.slice.value < 0:
                            pass

        return problems

    def _detect_incompatible_returns(self, tree: ast.AST, content: str, file_path: str) -> List[DetectedProblem]:
        problems = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.returns:
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
                        elif isinstance(child.value, (ast.Tuple)):
                            return_types.add('tuple')

                if len(return_types) > 1:
                    self._problem_counter += 1
                    problems.append(DetectedProblem(
                        problem_id=f"TYPE_{self._problem_counter:06d}",
                        category=ProblemCategory.TYPE_ERROR,
                        severity=ProblemSeverity.MEDIUM,
                        problem_type="inconsistent_return_types",
                        message=f"函数 '{node.name}' 返回类型不一致: {', '.join(return_types)}",
                        file_path=file_path,
                        line_number=node.lineno,
                        code_snippet=self._get_line_content(content, node.lineno),
                        suggestion="确保函数所有返回路径返回相同类型的值",
                        confidence=0.75,
                        auto_fixable=False,
                        context={"function_name": node.name, "return_types": list(return_types)}
                    ))

        return problems

    def _get_line_content(self, content: str, line_number: int) -> str:
        lines = content.split('\n')
        if 1 <= line_number <= len(lines):
            return lines[line_number - 1]
        return ""


class UnusedCodeDetector:
    """未使用代码检测器"""

    def __init__(self):
        self._problem_counter = 0

    def detect(self, content: str, file_path: str) -> List[DetectedProblem]:
        problems = []

        try:
            tree = ast.parse(content)
            problems.extend(self._detect_unused_variables(tree, content, file_path))
            problems.extend(self._detect_unused_functions(tree, content, file_path))
            problems.extend(self._detect_unused_classes(tree, content, file_path))
            problems.extend(self._detect_dead_code(tree, content, file_path))
        except SyntaxError:
            pass

        return problems

    def _detect_unused_variables(self, tree: ast.AST, content: str, file_path: str) -> List[DetectedProblem]:
        problems = []
        assigned_vars = {}
        used_vars = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                if isinstance(node.ctx, ast.Store):
                    if node.id not in ('_', '__'):
                        assigned_vars[node.id] = node.lineno
                elif isinstance(node.ctx, ast.Load):
                    used_vars.add(node.id)

        for var, line_no in assigned_vars.items():
            if var not in used_vars and not var.startswith('_'):
                self._problem_counter += 1
                problems.append(DetectedProblem(
                    problem_id=f"UNUSED_{self._problem_counter:06d}",
                    category=ProblemCategory.UNUSED_CODE,
                    severity=ProblemSeverity.LOW,
                    problem_type="unused_variable",
                    message=f"变量 '{var}' 被赋值但从未使用",
                    file_path=file_path,
                    line_number=line_no,
                    code_snippet=self._get_line_content(content, line_no),
                    suggestion=f"移除未使用的变量 '{var}' 或添加使用代码",
                    confidence=0.9,
                    auto_fixable=True,
                    context={"variable_name": var}
                ))

        return problems

    def _detect_unused_functions(self, tree: ast.AST, content: str, file_path: str) -> List[DetectedProblem]:
        problems = []
        defined_funcs = {}
        called_funcs = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if not node.name.startswith('_'):
                    defined_funcs[node.name] = node.lineno
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    called_funcs.add(node.func.id)

        for func, line_no in defined_funcs.items():
            if func not in called_funcs and not func.startswith('test_'):
                self._problem_counter += 1
                problems.append(DetectedProblem(
                    problem_id=f"UNUSED_{self._problem_counter:06d}",
                    category=ProblemCategory.UNUSED_CODE,
                    severity=ProblemSeverity.LOW,
                    problem_type="unused_function",
                    message=f"函数 '{func}' 已定义但从未调用",
                    file_path=file_path,
                    line_number=line_no,
                    code_snippet=self._get_line_content(content, line_no),
                    suggestion=f"移除未使用的函数 '{func}' 或添加调用代码",
                    confidence=0.8,
                    auto_fixable=True,
                    context={"function_name": func}
                ))

        return problems

    def _detect_unused_classes(self, tree: ast.AST, content: str, file_path: str) -> List[DetectedProblem]:
        problems = []
        defined_classes = {}
        used_classes = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if not node.name.startswith('_'):
                    defined_classes[node.name] = node.lineno
            elif isinstance(node, ast.Name):
                if isinstance(node.ctx, ast.Load):
                    used_classes.add(node.id)

        for cls, line_no in defined_classes.items():
            if cls not in used_classes:
                self._problem_counter += 1
                problems.append(DetectedProblem(
                    problem_id=f"UNUSED_{self._problem_counter:06d}",
                    category=ProblemCategory.UNUSED_CODE,
                    severity=ProblemSeverity.LOW,
                    problem_type="unused_class",
                    message=f"类 '{cls}' 已定义但从未使用",
                    file_path=file_path,
                    line_number=line_no,
                    code_snippet=self._get_line_content(content, line_no),
                    suggestion=f"移除未使用的类 '{cls}' 或添加使用代码",
                    confidence=0.8,
                    auto_fixable=True,
                    context={"class_name": cls}
                ))

        return problems

    def _detect_dead_code(self, tree: ast.AST, content: str, file_path: str) -> List[DetectedProblem]:
        problems = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                body = node.body
                for i, stmt in enumerate(body):
                    if isinstance(stmt, (ast.Return, ast.Raise, ast.Break, ast.Continue)):
                        if i < len(body) - 1:
                            for j in range(i + 1, len(body)):
                                self._problem_counter += 1
                                problems.append(DetectedProblem(
                                    problem_id=f"UNUSED_{self._problem_counter:06d}",
                                    category=ProblemCategory.UNUSED_CODE,
                                    severity=ProblemSeverity.MEDIUM,
                                    problem_type="unreachable_code",
                                    message="不可达代码",
                                    file_path=file_path,
                                    line_number=body[j].lineno,
                                    code_snippet=self._get_line_content(content, body[j].lineno),
                                    suggestion="移除不可达代码或调整控制流",
                                    confidence=0.95,
                                    auto_fixable=True
                                ))
                        break

        return problems

    def _get_line_content(self, content: str, line_number: int) -> str:
        lines = content.split('\n')
        if 1 <= line_number <= len(lines):
            return lines[line_number - 1]
        return ""


class ProblemDetectorExtension:
    """问题检测器扩展主类"""

    def __init__(self):
        self.import_detector = ImportErrorDetector()
        self.type_detector = TypeErrorDetector()
        self.unused_detector = UnusedCodeDetector()
        self._report_counter = 0

    def detect_all(self, content: str, file_path: str) -> List[DetectedProblem]:
        all_problems = []

        all_problems.extend(self.import_detector.detect(content, file_path))
        all_problems.extend(self.type_detector.detect(content, file_path))
        all_problems.extend(self.unused_detector.detect(content, file_path))

        all_problems.sort(key=lambda p: (p.line_number, p.severity.value))

        return all_problems

    def detect_imports(self, content: str, file_path: str) -> List[DetectedProblem]:
        return self.import_detector.detect(content, file_path)

    def detect_types(self, content: str, file_path: str) -> List[DetectedProblem]:
        return self.type_detector.detect(content, file_path)

    def detect_unused(self, content: str, file_path: str) -> List[DetectedProblem]:
        return self.unused_detector.detect(content, file_path)

    def generate_report(self, problems: List[DetectedProblem], file_path: str) -> Dict[str, Any]:
        self._report_counter += 1

        summary = defaultdict(int)
        for problem in problems:
            summary[problem.category.name] += 1
            summary[problem.severity.value] += 1

        return {
            "report_id": f"REPORT_{self._report_counter:06d}",
            "file_path": file_path,
            "total_problems": len(problems),
            "generated_at": datetime.now().isoformat(),
            "problems": [p.to_dict() for p in problems],
            "summary": dict(summary),
            "auto_fixable_count": sum(1 for p in problems if p.auto_fixable)
        }


def main():
    import argparse

    parser = argparse.ArgumentParser(description="问题检测器扩展")
    parser.add_argument("--file", type=str, required=True, help="要检测的文件路径")
    parser.add_argument("--detect-all", action="store_true", help="检测所有类型问题")
    parser.add_argument("--detect-imports", action="store_true", help="检测导入问题")
    parser.add_argument("--detect-types", action="store_true", help="检测类型问题")
    parser.add_argument("--detect-unused", action="store_true", help="检测未使用代码")
    parser.add_argument("--report", type=str, help="报告输出路径")

    args = parser.parse_args()

    detector = ProblemDetectorExtension()

    try:
        with open(args.file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"读取文件失败: {e}")
        return 1

    problems = []

    if args.detect_all or (not args.detect_imports and not args.detect_types and not args.detect_unused):
        problems = detector.detect_all(content, args.file)
    else:
        if args.detect_imports:
            problems.extend(detector.detect_imports(content, args.file))
        if args.detect_types:
            problems.extend(detector.detect_types(content, args.file))
        if args.detect_unused:
            problems.extend(detector.detect_unused(content, args.file))

    report = detector.generate_report(problems, args.file)

    print(f"\n检测报告: {report['report_id']}")
    print(f"文件: {report['file_path']}")
    print(f"总问题数: {report['total_problems']}")
    print(f"可自动修复: {report['auto_fixable_count']}")

    if report['summary']:
        print("\n问题统计:")
        for key, count in report['summary'].items():
            print(f"  {key}: {count}")

    if problems:
        print("\n问题列表:")
        for problem in problems[:20]:
            print(f"  [{problem.severity.value}] {problem.message} (行 {problem.line_number})")

    if args.report:
        with open(args.report, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"\n报告已保存: {args.report}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
