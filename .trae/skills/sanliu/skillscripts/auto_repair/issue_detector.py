#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
问题检测器 - Issue Detector

扩展的问题检测能力，包括：
- 语法错误检测
- 导入错误检测
- 类型错误检测
- 安全漏洞检测

使用示例:
    detector = IssueDetector()
    result = detector.detect("code.py")
    for issue in result.issues:
        print(f"{issue.category}: {issue.message}")
"""

from __future__ import annotations

import ast
import re
import os
import sys
import json
import logging
import subprocess
import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from collections import defaultdict

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)


class IssueCategory(Enum):
    SYNTAX_ERROR = auto()
    SYNTAX_INDENTATION = auto()
    SYNTAX_BRACKET_MISMATCH = auto()
    SYNTAX_QUOTE_MISMATCH = auto()
    SYNTAX_COLON_MISSING = auto()
    IMPORT_MISSING = auto()
    IMPORT_PATH_ERROR = auto()
    IMPORT_CIRCULAR = auto()
    IMPORT_UNUSED = auto()
    IMPORT_ALIAS_CONFLICT = auto()
    TYPE_ERROR = auto()
    TYPE_MISMATCH = auto()
    TYPE_MISSING_ANNOTATION = auto()
    TYPE_INVALID_ANNOTATION = auto()
    TYPE_INCOMPATIBLE_RETURN = auto()
    SECURITY_SQL_INJECTION = auto()
    SECURITY_XSS = auto()
    SECURITY_COMMAND_INJECTION = auto()
    SECURITY_PATH_TRAVERSAL = auto()
    SECURITY_HARDCODED_SECRET = auto()
    SECURITY_INSECURE_DESERIALIZE = auto()
    SECURITY_WEAK_CRYPTO = auto()
    SECURITY_SSL_ISSUE = auto()
    PERFORMANCE_ISSUE = auto()
    CODE_QUALITY = auto()
    STYLE_ISSUE = auto()
    DEPRECATED_CODE = auto()
    TEST_FAILURE = auto()
    TEST_ASSERTION_ERROR = auto()
    TEST_TIMEOUT = auto()
    TEST_IMPORT_ERROR = auto()
    TEST_FIXTURE_ERROR = auto()
    CODE_SMELL_DUPLICATION = auto()
    CODE_SMELL_LONG_METHOD = auto()
    CODE_SMELL_LARGE_CLASS = auto()
    CODE_SMELL_LONG_PARAMETER_LIST = auto()
    CODE_SMELL_DEAD_CODE = auto()
    CODE_SMELL_MAGIC_NUMBER = auto()
    CODE_SMELL_COMPLEXITY = auto()
    CODE_SMELL_NESTING = auto()
    DOCUMENTATION_MISSING = auto()
    DOCUMENTATION_INCOMPLETE = auto()
    DOCUMENTATION_OUTDATED = auto()
    DOCUMENTATION_FORMAT_ERROR = auto()
    DOCUMENTATION_BROKEN_LINK = auto()
    CONFIG_MISSING_FILE = auto()
    CONFIG_INVALID_FORMAT = auto()
    CONFIG_MISSING_KEY = auto()
    CONFIG_INVALID_VALUE = auto()
    CONFIG_DEPRECATED = auto()
    CUSTOM = auto()


class IssueSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class DetectionStatus(Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class Issue:
    issue_id: str
    category: IssueCategory
    severity: IssueSeverity
    message: str
    file_path: str
    line_number: int
    column: int = 0
    end_line: int = 0
    end_column: int = 0
    code_snippet: str = ""
    suggested_fix: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    related_issues: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    detector_name: str = ""
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "issue_id": self.issue_id,
            "category": self.category.name,
            "severity": self.severity.value,
            "message": self.message,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "column": self.column,
            "end_line": self.end_line,
            "end_column": self.end_column,
            "code_snippet": self.code_snippet,
            "suggested_fix": self.suggested_fix,
            "context": self.context,
            "related_issues": self.related_issues,
            "created_at": self.created_at,
            "detector_name": self.detector_name,
            "confidence": self.confidence
        }


@dataclass
class DetectionResult:
    result_id: str
    file_path: str
    status: DetectionStatus
    issues: List[Issue]
    total_issues: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    detection_time_ms: float
    detectors_used: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "result_id": self.result_id,
            "file_path": self.file_path,
            "status": self.status.value,
            "issues": [i.to_dict() for i in self.issues],
            "total_issues": self.total_issues,
            "critical_count": self.critical_count,
            "high_count": self.high_count,
            "medium_count": self.medium_count,
            "low_count": self.low_count,
            "detection_time_ms": self.detection_time_ms,
            "detectors_used": self.detectors_used,
            "metadata": self.metadata
        }

    def get_issues_by_category(self, category: IssueCategory) -> List[Issue]:
        return [i for i in self.issues if i.category == category]

    def get_issues_by_severity(self, severity: IssueSeverity) -> List[Issue]:
        return [i for i in self.issues if i.severity == severity]


class BaseDetector(ABC):
    """检测器基类"""

    category: IssueCategory = IssueCategory.CUSTOM
    name: str = "base_detector"
    description: str = "基础检测器"

    def __init__(self):
        self._issue_counter = 0

    @abstractmethod
    def detect(self, content: str, file_path: str) -> List[Issue]:
        pass

    def _create_issue(
        self,
        severity: IssueSeverity,
        message: str,
        file_path: str,
        line_number: int = 0,
        column: int = 0,
        code_snippet: str = "",
        suggested_fix: str = "",
        context: Optional[Dict[str, Any]] = None,
        confidence: float = 1.0
    ) -> Issue:
        self._issue_counter += 1
        return Issue(
            issue_id=f"{self.name}_{self._issue_counter:04d}",
            category=self.category,
            severity=severity,
            message=message,
            file_path=file_path,
            line_number=line_number,
            column=column,
            code_snippet=code_snippet,
            suggested_fix=suggested_fix,
            context=context or {},
            detector_name=self.name,
            confidence=confidence
        )

    def _get_line_content(self, content: str, line_number: int) -> str:
        lines = content.split('\n')
        if 1 <= line_number <= len(lines):
            return lines[line_number - 1]
        return ""


class SyntaxErrorDetector(BaseDetector):
    """语法错误检测器"""

    category = IssueCategory.SYNTAX_ERROR
    name = "syntax_error_detector"
    description = "检测Python语法错误"

    def detect(self, content: str, file_path: str) -> List[Issue]:
        issues = []
        
        syntax_issues = self._check_syntax_errors(content, file_path)
        issues.extend(syntax_issues)
        
        if not syntax_issues:
            issues.extend(self._check_indentation(content, file_path))
            issues.extend(self._check_brackets(content, file_path))
            issues.extend(self._check_quotes(content, file_path))
            issues.extend(self._check_colons(content, file_path))
        
        return issues

    def _check_syntax_errors(self, content: str, file_path: str) -> List[Issue]:
        issues = []
        try:
            ast.parse(content)
        except SyntaxError as e:
            line_num = e.lineno or 1
            col = e.offset or 0
            issues.append(self._create_issue(
                severity=IssueSeverity.CRITICAL,
                message=f"语法错误: {e.msg}",
                file_path=file_path,
                line_number=line_num,
                column=col,
                code_snippet=self._get_line_content(content, line_num),
                suggested_fix=self._suggest_syntax_fix(e.msg, self._get_line_content(content, line_num)),
                confidence=0.9
            ))
        return issues

    def _suggest_syntax_fix(self, error_msg: str, code_line: str) -> str:
        suggestions = {
            "expected ':'": "在语句末尾添加冒号 ':'",
            "invalid syntax": "检查语法结构是否正确",
            "unexpected EOF": "检查是否缺少闭合括号或引号",
            "unterminated string literal": "检查字符串引号是否成对",
            "unexpected indent": "检查缩进是否正确",
            "expected an indented block": "在冒号后添加缩进的代码块",
        }
        
        for key, suggestion in suggestions.items():
            if key in error_msg.lower():
                return suggestion
        return "请检查语法错误"

    def _check_indentation(self, content: str, file_path: str) -> List[Issue]:
        issues = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            if not line.strip():
                continue
            
            indent = len(line) - len(line.lstrip())
            
            if '\t' in line[:indent] and ' ' in line[:indent]:
                issues.append(self._create_issue(
                    severity=IssueSeverity.HIGH,
                    message="混合使用制表符和空格进行缩进",
                    file_path=file_path,
                    line_number=i,
                    code_snippet=line,
                    suggested_fix="统一使用4个空格进行缩进",
                    confidence=0.95
                ))
        
        return issues

    def _check_brackets(self, content: str, file_path: str) -> List[Issue]:
        issues = []
        bracket_pairs = {'(': ')', '[': ']', '{': '}'}
        stack = []
        
        in_string = False
        string_char = None
        escape_next = False
        
        for i, char in enumerate(content):
            if escape_next:
                escape_next = False
                continue
            
            if char == '\\':
                escape_next = True
                continue
            
            if char in '\'"':
                if not in_string:
                    in_string = True
                    string_char = char
                elif char == string_char:
                    in_string = False
                    string_char = None
            elif not in_string:
                if char in bracket_pairs:
                    stack.append((char, i))
                elif char in bracket_pairs.values():
                    if not stack:
                        line_num = content[:i].count('\n') + 1
                        issues.append(self._create_issue(
                            severity=IssueSeverity.CRITICAL,
                            message=f"未匹配的右括号 '{char}'",
                            file_path=file_path,
                            line_number=line_num,
                            suggested_fix=f"检查括号匹配，可能缺少左括号",
                            confidence=0.9
                        ))
                    else:
                        expected_open = [k for k, v in bracket_pairs.items() if v == char][0]
                        if stack[-1][0] != expected_open:
                            line_num = content[:i].count('\n') + 1
                            issues.append(self._create_issue(
                                severity=IssueSeverity.CRITICAL,
                                message=f"括号类型不匹配",
                                file_path=file_path,
                                line_number=line_num,
                                suggested_fix="检查括号类型是否匹配",
                                confidence=0.85
                            ))
                        else:
                            stack.pop()
        
        for bracket, pos in stack:
            line_num = content[:pos].count('\n') + 1
            issues.append(self._create_issue(
                severity=IssueSeverity.CRITICAL,
                message=f"未匹配的左括号 '{bracket}'",
                file_path=file_path,
                line_number=line_num,
                suggested_fix=f"添加对应的右括号 '{bracket_pairs[bracket]}'",
                confidence=0.9
            ))
        
        return issues

    def _check_quotes(self, content: str, file_path: str) -> List[Issue]:
        issues = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith('#'):
                continue
            
            for quote in ['"', "'"]:
                count = 0
                j = 0
                while j < len(line):
                    if line[j] == '\\' and j + 1 < len(line):
                        j += 2
                        continue
                    if line[j] == quote:
                        count += 1
                    j += 1
                
                if count % 2 != 0:
                    triple = quote * 3
                    if content.count(triple) % 2 == 0:
                        continue
                    issues.append(self._create_issue(
                        severity=IssueSeverity.HIGH,
                        message=f"未匹配的引号 '{quote}'",
                        file_path=file_path,
                        line_number=i,
                        code_snippet=line,
                        suggested_fix="检查引号是否成对出现",
                        confidence=0.85
                    ))
                    break
        
        return issues

    def _check_colons(self, content: str, file_path: str) -> List[Issue]:
        issues = []
        lines = content.split('\n')
        keywords = ['if', 'elif', 'else', 'for', 'while', 'def', 'class', 'try', 'except', 'finally', 'with']
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith('#'):
                continue
            
            for kw in keywords:
                if re.match(rf'^{kw}\b', stripped):
                    if not stripped.endswith(':'):
                        issues.append(self._create_issue(
                            severity=IssueSeverity.HIGH,
                            message=f"'{kw}' 语句末尾缺少冒号",
                            file_path=file_path,
                            line_number=i,
                            code_snippet=line,
                            suggested_fix="在语句末尾添加 ':'",
                            confidence=0.95
                        ))
                    break
        
        return issues


class ImportErrorDetector(BaseDetector):
    """导入错误检测器"""

    category = IssueCategory.IMPORT_MISSING
    name = "import_error_detector"
    description = "检测导入相关问题"

    STANDARD_LIBRARY = {
        'os', 'sys', 're', 'json', 'datetime', 'time', 'math', 'random',
        'collections', 'itertools', 'functools', 'typing', 'pathlib',
        'subprocess', 'threading', 'multiprocessing', 'asyncio', 'logging',
        'unittest', 'argparse', 'configparser', 'tempfile', 'shutil',
        'hashlib', 'hmac', 'secrets', 'io', 'pickle', 'csv', 'xml',
        'html', 'urllib', 'http', 'email', 'html', 'xmlrpc', 'sqlite3',
        'socket', 'ssl', 'email', 'base64', 'binascii', 'struct',
        'codecs', 'unicodedata', 'string', 'textwrap', 'difflib',
        'ast', 'tokenize', 'keyword', 'token', 'symbol', 'dis', 'inspect',
        'abc', 'contextlib', 'dataclasses', 'enum', 'copy', 'pprint',
        'reprlib', 'traceback', 'warnings', 'weakref', 'types', 'copy'
    }

    THIRD_PARTY_COMMON = {
        'numpy', 'pandas', 'matplotlib', 'requests', 'flask', 'django',
        'fastapi', 'pydantic', 'sqlalchemy', 'pytest', 'black', 'flake8',
        'mypy', 'isort', 'pillow', 'scipy', 'sklearn', 'torch', 'tensorflow'
    }

    def detect(self, content: str, file_path: str) -> List[Issue]:
        issues = []
        
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return issues
        
        issues.extend(self._check_missing_imports(tree, content, file_path))
        issues.extend(self._check_unused_imports(tree, content, file_path))
        issues.extend(self._check_import_errors(tree, content, file_path))
        
        return issues

    def _check_missing_imports(self, tree: ast.AST, content: str, file_path: str) -> List[Issue]:
        issues = []
        
        imported_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_names.add(alias.asname or alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imported_names.add(node.module.split('.')[0])
                for alias in node.names:
                    imported_names.add(alias.asname or alias.name)
        
        used_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                used_names.add(node.id)
            elif isinstance(node, ast.Attribute):
                if isinstance(node.value, ast.Name):
                    used_names.add(node.value.id)
        
        missing = used_names - imported_names - self.STANDARD_LIBRARY
        
        for name in missing:
            for node in ast.walk(tree):
                if isinstance(node, ast.Name) and node.id == name:
                    issues.append(self._create_issue(
                        severity=IssueSeverity.HIGH,
                        message=f"可能缺少导入: '{name}'",
                        file_path=file_path,
                        line_number=node.lineno,
                        suggested_fix=f"添加导入语句: import {name}",
                        context={"missing_name": name},
                        confidence=0.7
                    ))
                    break
        
        return issues

    def _check_unused_imports(self, tree: ast.AST, content: str, file_path: str) -> List[Issue]:
        issues = []
        
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append((alias.name, alias.asname, node.lineno))
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    name = f"{node.module}.{alias.name}" if node.module else alias.name
                    imports.append((name, alias.asname, node.lineno))
        
        used_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                used_names.add(node.id)
            elif isinstance(node, ast.Attribute):
                if isinstance(node.value, ast.Name):
                    used_names.add(node.value.id)
        
        for name, asname, line_no in imports:
            check_name = asname or name.split('.')[0]
            if check_name not in used_names and check_name not in ['__future__', '__all__']:
                issues.append(self._create_issue(
                    severity=IssueSeverity.LOW,
                    message=f"未使用的导入: '{name}'",
                    file_path=file_path,
                    line_number=line_no,
                    suggested_fix=f"移除未使用的导入: {name}",
                    context={"import_name": name},
                    confidence=0.9
                ))
        
        return issues

    def _check_import_errors(self, tree: ast.AST, content: str, file_path: str) -> List[Issue]:
        issues = []
        
        deprecated_modules = {
            'urlparse': 'urllib.parse',
            'urllib2': 'urllib.request',
            'ConfigParser': 'configparser',
            'cPickle': 'pickle',
            'cStringIO': 'io',
            'StringIO': 'io',
            'Queue': 'queue',
            'SocketServer': 'socketserver',
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in deprecated_modules:
                        issues.append(self._create_issue(
                            severity=IssueSeverity.MEDIUM,
                            message=f"使用已弃用的模块: '{alias.name}'",
                            file_path=file_path,
                            line_number=node.lineno,
                            suggested_fix=f"使用 '{deprecated_modules[alias.name]}' 替代",
                            context={"old_module": alias.name, "new_module": deprecated_modules[alias.name]},
                            confidence=0.95
                        ))
            elif isinstance(node, ast.ImportFrom):
                if node.module and node.module in deprecated_modules:
                    issues.append(self._create_issue(
                        severity=IssueSeverity.MEDIUM,
                        message=f"使用已弃用的模块: '{node.module}'",
                        file_path=file_path,
                        line_number=node.lineno,
                        suggested_fix=f"使用 '{deprecated_modules[node.module]}' 替代",
                        context={"old_module": node.module, "new_module": deprecated_modules[node.module]},
                        confidence=0.95
                    ))
        
        return issues


class TypeErrorDetector(BaseDetector):
    """类型错误检测器"""

    category = IssueCategory.TYPE_ERROR
    name = "type_error_detector"
    description = "检测类型相关错误"

    def detect(self, content: str, file_path: str) -> List[Issue]:
        issues = []
        
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return issues
        
        issues.extend(self._check_type_annotations(tree, content, file_path))
        issues.extend(self._check_type_compatibility(tree, content, file_path))
        issues.extend(self._check_return_types(tree, content, file_path))
        
        return issues

    def _check_type_annotations(self, tree: ast.AST, content: str, file_path: str) -> List[Issue]:
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if not node.returns and not self._is_init_method(node):
                    has_return = any(
                        isinstance(n, ast.Return) and n.value
                        for n in ast.walk(node)
                    )
                    if has_return:
                        issues.append(self._create_issue(
                            severity=IssueSeverity.LOW,
                            message=f"函数 '{node.name}' 缺少返回类型注解",
                            file_path=file_path,
                            line_number=node.lineno,
                            suggested_fix="添加返回类型注解，例如: -> ReturnType",
                            context={"function_name": node.name},
                            confidence=0.8
                        ))
                
                for arg in node.args.args:
                    if arg.annotation is None and arg.arg != 'self' and arg.arg != 'cls':
                        issues.append(self._create_issue(
                            severity=IssueSeverity.LOW,
                            message=f"参数 '{arg.arg}' 缺少类型注解",
                            file_path=file_path,
                            line_number=node.lineno,
                            suggested_fix=f"为参数 '{arg.arg}' 添加类型注解",
                            context={"parameter_name": arg.arg, "function_name": node.name},
                            confidence=0.75
                        ))
        
        return issues

    def _is_init_method(self, node: ast.FunctionDef) -> bool:
        return node.name == '__init__'

    def _check_type_compatibility(self, tree: ast.AST, content: str, file_path: str) -> List[Issue]:
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Compare):
                if len(node.ops) == 1 and isinstance(node.ops[0], (ast.Is, ast.IsNot)):
                    if isinstance(node.comparators[0], ast.Constant):
                        issues.append(self._create_issue(
                            severity=IssueSeverity.MEDIUM,
                            message="使用 'is' 比较字面量，应使用 '=='",
                            file_path=file_path,
                            line_number=node.lineno,
                            suggested_fix="使用 '==' 进行值比较，'is' 用于身份比较",
                            confidence=0.9
                        ))
        
        return issues

    def _check_return_types(self, tree: ast.AST, content: str, file_path: str) -> List[Issue]:
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.returns:
                return_type = node.returns
                return_nodes = [n for n in ast.walk(node) if isinstance(n, ast.Return) and n.value]
                
                if not return_nodes:
                    continue
                
                for ret in return_nodes:
                    inferred_type = self._infer_type(ret.value)
                    if inferred_type and not self._types_compatible(return_type, inferred_type):
                        issues.append(self._create_issue(
                            severity=IssueSeverity.MEDIUM,
                            message=f"返回类型可能与注解不符",
                            file_path=file_path,
                            line_number=ret.lineno,
                            suggested_fix="检查返回值类型是否与注解一致",
                            context={"function_name": node.name},
                            confidence=0.6
                        ))
        
        return issues

    def _infer_type(self, node: ast.AST) -> Optional[str]:
        if isinstance(node, ast.Constant):
            return type(node.value).__name__
        elif isinstance(node, ast.List):
            return "list"
        elif isinstance(node, ast.Dict):
            return "dict"
        elif isinstance(node, ast.Set):
            return "set"
        elif isinstance(node, ast.Tuple):
            return "tuple"
        elif isinstance(node, ast.Name):
            return node.id
        return None

    def _types_compatible(self, annotated: ast.AST, inferred: str) -> bool:
        if isinstance(annotated, ast.Name):
            return annotated.id.lower() == inferred.lower()
        elif isinstance(annotated, ast.Constant):
            return str(annotated.value).lower() == inferred.lower()
        return True


class SecurityVulnerabilityDetector(BaseDetector):
    """安全漏洞检测器"""

    category = IssueCategory.SECURITY_SQL_INJECTION
    name = "security_vulnerability_detector"
    description = "检测安全漏洞"

    DANGEROUS_FUNCTIONS = {
        'eval': ('代码注入风险', IssueSeverity.CRITICAL),
        'exec': ('代码注入风险', IssueSeverity.CRITICAL),
        'compile': ('代码注入风险', IssueSeverity.HIGH),
        'os.system': ('命令注入风险', IssueSeverity.CRITICAL),
        'os.popen': ('命令注入风险', IssueSeverity.CRITICAL),
        'subprocess.call': ('命令注入风险', IssueSeverity.HIGH),
        'subprocess.Popen': ('命令注入风险', IssueSeverity.HIGH),
        'pickle.loads': ('不安全的反序列化', IssueSeverity.CRITICAL),
        'pickle.load': ('不安全的反序列化', IssueSeverity.CRITICAL),
        'yaml.load': ('不安全的YAML加载', IssueSeverity.HIGH),
        'marshal.load': ('不安全的反序列化', IssueSeverity.HIGH),
    }

    SENSITIVE_PATTERNS = [
        (r'password\s*=\s*["\'][^"\']+["\']', '硬编码密码', IssueSeverity.CRITICAL),
        (r'passwd\s*=\s*["\'][^"\']+["\']', '硬编码密码', IssueSeverity.CRITICAL),
        (r'pwd\s*=\s*["\'][^"\']+["\']', '硬编码密码', IssueSeverity.HIGH),
        (r'api_key\s*=\s*["\'][^"\']+["\']', '硬编码API密钥', IssueSeverity.CRITICAL),
        (r'apikey\s*=\s*["\'][^"\']+["\']', '硬编码API密钥', IssueSeverity.CRITICAL),
        (r'secret_key\s*=\s*["\'][^"\']+["\']', '硬编码密钥', IssueSeverity.CRITICAL),
        (r'secret\s*=\s*["\'][^"\']+["\']', '硬编码密钥', IssueSeverity.HIGH),
        (r'token\s*=\s*["\'][^"\']+["\']', '硬编码令牌', IssueSeverity.HIGH),
        (r'private_key\s*=\s*["\'][^"\']+["\']', '硬编码私钥', IssueSeverity.CRITICAL),
    ]

    SQL_INJECTION_PATTERNS = [
        r'f["\'].*?(?:SELECT|INSERT|UPDATE|DELETE|CREATE|DROP|ALTER).*?\{',
        r'\.format\s*\([^)]*\).*?(?:SELECT|INSERT|UPDATE|DELETE|CREATE|DROP)',
        r'["\'].*?(?:SELECT|INSERT|UPDATE|DELETE).*?["\'].*?\+',
        r'%s.*?(?:SELECT|INSERT|UPDATE|DELETE)',
    ]

    def detect(self, content: str, file_path: str) -> List[Issue]:
        issues = []
        
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return issues
        
        issues.extend(self._check_dangerous_functions(tree, content, file_path))
        issues.extend(self._check_sql_injection(content, file_path))
        issues.extend(self._check_hardcoded_secrets(content, file_path))
        issues.extend(self._check_path_traversal(tree, content, file_path))
        issues.extend(self._check_weak_crypto(content, file_path))
        issues.extend(self._check_ssl_issues(content, file_path))
        
        return issues

    def _check_dangerous_functions(self, tree: ast.AST, content: str, file_path: str) -> List[Issue]:
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_func_name(node.func)
                
                if func_name in self.DANGEROUS_FUNCTIONS:
                    desc, severity = self.DANGEROUS_FUNCTIONS[func_name]
                    issues.append(self._create_issue(
                        severity=severity,
                        message=f"使用危险函数 '{func_name}': {desc}",
                        file_path=file_path,
                        line_number=node.lineno,
                        suggested_fix=self._get_safe_alternative(func_name),
                        context={"function_name": func_name},
                        confidence=0.95
                    ))
        
        return issues

    def _get_func_name(self, node: ast.expr) -> str:
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            value_name = self._get_func_name(node.value)
            return f"{value_name}.{node.attr}"
        return ""

    def _get_safe_alternative(self, func_name: str) -> str:
        alternatives = {
            'eval': '使用 ast.literal_eval() 进行安全的表达式求值',
            'exec': '避免动态执行代码，重构代码逻辑',
            'os.system': '使用 subprocess.run() 并设置 shell=False',
            'os.popen': '使用 subprocess.run() 并设置 shell=False',
            'pickle.loads': '使用 JSON 或其他安全的序列化格式',
            'pickle.load': '使用 JSON 或其他安全的序列化格式',
            'yaml.load': '使用 yaml.safe_load() 或 yaml.load(data, Loader=yaml.SafeLoader)',
        }
        return alternatives.get(func_name, f"避免使用 '{func_name}'，使用更安全的替代方案")

    def _check_sql_injection(self, content: str, file_path: str) -> List[Issue]:
        issues = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            for pattern in self.SQL_INJECTION_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(self._create_issue(
                        severity=IssueSeverity.CRITICAL,
                        message="潜在的SQL注入漏洞",
                        file_path=file_path,
                        line_number=i,
                        code_snippet=line.strip()[:100],
                        suggested_fix="使用参数化查询，例如: cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))",
                        context={"pattern": pattern},
                        confidence=0.85
                    ))
                    break
        
        return issues

    def _check_hardcoded_secrets(self, content: str, file_path: str) -> List[Issue]:
        issues = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith('#') or stripped.startswith('"""') or stripped.startswith("'''"):
                continue
            
            for pattern, desc, severity in self.SENSITIVE_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    if 'test' in file_path.lower() or 'example' in file_path.lower():
                        severity = IssueSeverity.LOW
                    
                    issues.append(self._create_issue(
                        severity=severity,
                        message=f"硬编码敏感信息: {desc}",
                        file_path=file_path,
                        line_number=i,
                        code_snippet="[已隐藏敏感信息]",
                        suggested_fix="使用环境变量存储敏感信息，例如: os.environ.get('SECRET_KEY')",
                        context={"pattern_type": desc},
                        confidence=0.9
                    ))
                    break
        
        return issues

    def _check_path_traversal(self, tree: ast.AST, content: str, file_path: str) -> List[Issue]:
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_func_name(node.func)
                
                if func_name in ['open', 'os.path.join', 'os.listdir']:
                    for arg in node.args:
                        if isinstance(arg, ast.BinOp) and isinstance(arg.op, ast.Add):
                            issues.append(self._create_issue(
                                severity=IssueSeverity.HIGH,
                                message="潜在的路径遍历漏洞",
                                file_path=file_path,
                                line_number=node.lineno,
                                suggested_fix="验证和清理用户输入的路径，使用 os.path.basename() 或白名单验证",
                                confidence=0.7
                            ))
                        elif isinstance(arg, ast.Name):
                            issues.append(self._create_issue(
                                severity=IssueSeverity.MEDIUM,
                                message="使用变量作为文件路径，可能存在路径遍历风险",
                                file_path=file_path,
                                line_number=node.lineno,
                                suggested_fix="验证用户输入的路径，确保不包含 '..' 等危险字符",
                                confidence=0.6
                            ))
        
        return issues

    def _check_weak_crypto(self, content: str, file_path: str) -> List[Issue]:
        issues = []
        lines = content.split('\n')
        
        weak_hash_pattern = r'hashlib\.(md5|sha1)\s*\('
        weak_random_pattern = r'random\.(random|randint|choice)\s*\('
        
        for i, line in enumerate(lines, 1):
            if re.search(weak_hash_pattern, line):
                issues.append(self._create_issue(
                    severity=IssueSeverity.MEDIUM,
                    message="使用弱哈希算法 (MD5/SHA1)",
                    file_path=file_path,
                    line_number=i,
                    code_snippet=line.strip()[:80],
                    suggested_fix="使用更强的哈希算法，例如: hashlib.sha256() 或 hashlib.sha512()",
                    confidence=0.85
                ))
            
            if re.search(weak_random_pattern, line):
                if 'password' in line.lower() or 'secret' in line.lower() or 'token' in line.lower():
                    issues.append(self._create_issue(
                        severity=IssueSeverity.HIGH,
                        message="使用不安全的随机数生成器生成敏感数据",
                        file_path=file_path,
                        line_number=i,
                        code_snippet=line.strip()[:80],
                        suggested_fix="使用 secrets 模块生成安全的随机数，例如: secrets.token_hex()",
                        confidence=0.9
                    ))
        
        return issues

    def _check_ssl_issues(self, content: str, file_path: str) -> List[Issue]:
        issues = []
        lines = content.split('\n')
        
        ssl_patterns = [
            (r'ssl\._create_unverified_context', '禁用SSL证书验证', IssueSeverity.CRITICAL),
            (r'verify\s*=\s*False', '禁用SSL证书验证', IssueSeverity.CRITICAL),
            (r'CERT_NONE', '禁用SSL证书验证', IssueSeverity.CRITICAL),
            (r'check_hostname\s*=\s*False', '禁用主机名检查', IssueSeverity.HIGH),
        ]
        
        for i, line in enumerate(lines, 1):
            for pattern, desc, severity in ssl_patterns:
                if re.search(pattern, line):
                    issues.append(self._create_issue(
                        severity=severity,
                        message=f"SSL安全问题: {desc}",
                        file_path=file_path,
                        line_number=i,
                        code_snippet=line.strip()[:80],
                        suggested_fix="启用SSL证书验证，使用 ssl.create_default_context()",
                        confidence=0.95
                    ))
        
        return issues


class TestFailureDetector(BaseDetector):
    """测试失败检测器"""

    category = IssueCategory.TEST_FAILURE
    name = "test_failure_detector"
    description = "检测测试失败相关问题"

    def detect(self, content: str, file_path: str) -> List[Issue]:
        issues = []
        
        if not self._is_test_file(file_path):
            return issues
        
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return issues
        
        issues.extend(self._check_assertion_issues(tree, content, file_path))
        issues.extend(self._check_test_structure(tree, content, file_path))
        issues.extend(self._check_fixture_issues(tree, content, file_path))
        issues.extend(self._check_mock_issues(tree, content, file_path))
        
        return issues

    def _is_test_file(self, file_path: str) -> bool:
        return 'test' in file_path.lower() or '_test.py' in file_path or 'test_' in file_path

    def _check_assertion_issues(self, tree: ast.AST, content: str, file_path: str) -> List[Issue]:
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Assert):
                if isinstance(node.test, ast.Compare):
                    if len(node.ops) == 1 and isinstance(node.ops[0], (ast.Eq, ast.NotEq)):
                        issues.append(self._create_issue(
                            severity=IssueSeverity.MEDIUM,
                            message="使用简单的断言，建议使用更具体的断言方法",
                            file_path=file_path,
                            line_number=node.lineno,
                            suggested_fix="使用 assertEqual, assertTrue 等更明确的断言方法",
                            context={"assertion_type": "simple_comparison"},
                            confidence=0.7
                        ))
                
                if not node.msg:
                    issues.append(self._create_issue(
                        severity=IssueSeverity.LOW,
                        message="断言缺少错误消息",
                        file_path=file_path,
                        line_number=node.lineno,
                        suggested_fix="为断言添加描述性错误消息，例如: assert x == y, 'x应该等于y'",
                        context={"assertion_type": "no_message"},
                        confidence=0.85
                    ))
        
        return issues

    def _check_test_structure(self, tree: ast.AST, content: str, file_path: str) -> List[Issue]:
        issues = []
        
        test_functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if node.name.startswith('test_'):
                    test_functions.append(node)
        
        if not test_functions:
            issues.append(self._create_issue(
                severity=IssueSeverity.LOW,
                message="测试文件中没有找到测试函数",
                file_path=file_path,
                line_number=1,
                suggested_fix="添加以 'test_' 开头的测试函数",
                confidence=0.9
            ))
        
        for func in test_functions:
            if not func.body or (len(func.body) == 1 and isinstance(func.body[0], ast.Pass)):
                issues.append(self._create_issue(
                    severity=IssueSeverity.MEDIUM,
                    message=f"测试函数 '{func.name}' 为空",
                    file_path=file_path,
                    line_number=func.lineno,
                    suggested_fix="实现测试逻辑或移除空测试",
                    context={"function_name": func.name},
                    confidence=0.95
                ))
            
            has_assertion = any(
                isinstance(n, (ast.Assert, ast.Call)) 
                for n in ast.walk(func)
            )
            
            if not has_assertion:
                issues.append(self._create_issue(
                    severity=IssueSeverity.MEDIUM,
                    message=f"测试函数 '{func.name}' 缺少断言",
                    file_path=file_path,
                    line_number=func.lineno,
                    suggested_fix="添加断言来验证测试结果",
                    context={"function_name": func.name},
                    confidence=0.85
                ))
        
        return issues

    def _check_fixture_issues(self, tree: ast.AST, content: str, file_path: str) -> List[Issue]:
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                for decorator in node.decorator_list:
                    decorator_name = self._get_decorator_name(decorator)
                    
                    if decorator_name == 'pytest.fixture':
                        if node.name.startswith('test_'):
                            issues.append(self._create_issue(
                                severity=IssueSeverity.HIGH,
                                message=f"fixture函数 '{node.name}' 不应以 'test_' 开头",
                                file_path=file_path,
                                line_number=node.lineno,
                                suggested_fix="重命名fixture函数，移除 'test_' 前缀",
                                context={"function_name": node.name},
                                confidence=0.95
                            ))
        
        return issues

    def _check_mock_issues(self, tree: ast.AST, content: str, file_path: str) -> List[Issue]:
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_func_name(node.func)
                
                if 'mock' in func_name.lower() or 'patch' in func_name.lower():
                    for arg in node.args:
                        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                            if not arg.value:
                                issues.append(self._create_issue(
                                    severity=IssueSeverity.MEDIUM,
                                    message="Mock目标为空字符串",
                                    file_path=file_path,
                                    line_number=node.lineno,
                                    suggested_fix="指定正确的mock目标路径",
                                    confidence=0.9
                                ))
        
        return issues

    def _get_decorator_name(self, decorator: ast.expr) -> str:
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            return f"{self._get_decorator_name(decorator.value)}.{decorator.attr}"
        elif isinstance(decorator, ast.Call):
            return self._get_decorator_name(decorator.func)
        return ""

    def _get_func_name(self, node: ast.expr) -> str:
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            value_name = self._get_func_name(node.value)
            return f"{value_name}.{node.attr}"
        return ""


class CodeSmellDetector(BaseDetector):
    """代码异味检测器"""

    category = IssueCategory.CODE_SMELL_DUPLICATION
    name = "code_smell_detector"
    description = "检测代码异味问题"

    MAX_METHOD_LINES = 50
    MAX_CLASS_LINES = 500
    MAX_PARAMETERS = 5
    MAX_NESTING_DEPTH = 4
    MAX_CYCLOMATIC_COMPLEXITY = 10

    def detect(self, content: str, file_path: str) -> List[Issue]:
        issues = []
        
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return issues
        
        issues.extend(self._check_long_methods(tree, content, file_path))
        issues.extend(self._check_large_classes(tree, content, file_path))
        issues.extend(self._check_long_parameter_lists(tree, content, file_path))
        issues.extend(self._check_nesting_depth(tree, content, file_path))
        issues.extend(self._check_complexity(tree, content, file_path))
        issues.extend(self._check_dead_code(tree, content, file_path))
        issues.extend(self._check_magic_numbers(tree, content, file_path))
        issues.extend(self._check_duplication(content, file_path))
        
        return issues

    def _check_long_methods(self, tree: ast.AST, content: str, file_path: str) -> List[Issue]:
        issues = []
        lines = content.split('\n')
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                method_lines = node.end_lineno - node.lineno + 1 if hasattr(node, 'end_lineno') else 0
                
                if method_lines > self.MAX_METHOD_LINES:
                    issues.append(self._create_issue(
                        severity=IssueSeverity.MEDIUM,
                        message=f"方法 '{node.name}' 过长 ({method_lines} 行)",
                        file_path=file_path,
                        line_number=node.lineno,
                        suggested_fix="将方法拆分为更小的函数，每个函数只做一件事",
                        context={"method_name": node.name, "line_count": method_lines},
                        confidence=0.9
                    ))
        
        return issues

    def _check_large_classes(self, tree: ast.AST, content: str, file_path: str) -> List[Issue]:
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_lines = node.end_lineno - node.lineno + 1 if hasattr(node, 'end_lineno') else 0
                
                if class_lines > self.MAX_CLASS_LINES:
                    issues.append(self._create_issue(
                        severity=IssueSeverity.MEDIUM,
                        message=f"类 '{node.name}' 过大 ({class_lines} 行)",
                        file_path=file_path,
                        line_number=node.lineno,
                        suggested_fix="考虑将类拆分为多个更小的类，遵循单一职责原则",
                        context={"class_name": node.name, "line_count": class_lines},
                        confidence=0.85
                    ))
                
                method_count = sum(1 for n in node.body if isinstance(n, ast.FunctionDef))
                if method_count > 20:
                    issues.append(self._create_issue(
                        severity=IssueSeverity.MEDIUM,
                        message=f"类 '{node.name}' 方法过多 ({method_count} 个)",
                        file_path=file_path,
                        line_number=node.lineno,
                        suggested_fix="考虑将类拆分，每个类职责单一",
                        context={"class_name": node.name, "method_count": method_count},
                        confidence=0.8
                    ))
        
        return issues

    def _check_long_parameter_lists(self, tree: ast.AST, content: str, file_path: str) -> List[Issue]:
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                param_count = len(node.args.args) + len(node.args.kwonlyargs)
                
                if param_count > self.MAX_PARAMETERS:
                    issues.append(self._create_issue(
                        severity=IssueSeverity.MEDIUM,
                        message=f"函数 '{node.name}' 参数过多 ({param_count} 个)",
                        file_path=file_path,
                        line_number=node.lineno,
                        suggested_fix="使用参数对象或配置字典来减少参数数量",
                        context={"function_name": node.name, "param_count": param_count},
                        confidence=0.9
                    ))
        
        return issues

    def _check_nesting_depth(self, tree: ast.AST, content: str, file_path: str) -> List[Issue]:
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                max_depth = self._calculate_max_nesting(node)
                
                if max_depth > self.MAX_NESTING_DEPTH:
                    issues.append(self._create_issue(
                        severity=IssueSeverity.MEDIUM,
                        message=f"函数 '{node.name}' 嵌套层次过深 ({max_depth} 层)",
                        file_path=file_path,
                        line_number=node.lineno,
                        suggested_fix="使用早返回、提取方法等方式减少嵌套",
                        context={"function_name": node.name, "nesting_depth": max_depth},
                        confidence=0.85
                    ))
        
        return issues

    def _calculate_max_nesting(self, node: ast.AST, current_depth: int = 0) -> int:
        max_depth = current_depth
        
        nesting_nodes = (ast.If, ast.For, ast.While, ast.With, ast.Try)
        
        for child in ast.iter_child_nodes(node):
            if isinstance(child, nesting_nodes):
                child_depth = self._calculate_max_nesting(child, current_depth + 1)
                max_depth = max(max_depth, child_depth)
            else:
                child_depth = self._calculate_max_nesting(child, current_depth)
                max_depth = max(max_depth, child_depth)
        
        return max_depth

    def _check_complexity(self, tree: ast.AST, content: str, file_path: str) -> List[Issue]:
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                complexity = self._calculate_cyclomatic_complexity(node)
                
                if complexity > self.MAX_CYCLOMATIC_COMPLEXITY:
                    issues.append(self._create_issue(
                        severity=IssueSeverity.MEDIUM,
                        message=f"函数 '{node.name}' 圈复杂度过高 ({complexity})",
                        file_path=file_path,
                        line_number=node.lineno,
                        suggested_fix="简化条件逻辑，提取独立函数，使用多态替代条件判断",
                        context={"function_name": node.name, "complexity": complexity},
                        confidence=0.85
                    ))
        
        return issues

    def _calculate_cyclomatic_complexity(self, node: ast.FunctionDef) -> int:
        complexity = 1
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            elif isinstance(child, ast.comprehension):
                complexity += 1
                if child.ifs:
                    complexity += len(child.ifs)
        
        return complexity

    def _check_dead_code(self, tree: ast.AST, content: str, file_path: str) -> List[Issue]:
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if node.name.startswith('_') and not node.name.startswith('__'):
                    continue
                
                is_used = self._is_function_used(tree, node.name)
                
                if not is_used:
                    issues.append(self._create_issue(
                        severity=IssueSeverity.LOW,
                        message=f"函数 '{node.name}' 可能未被使用",
                        file_path=file_path,
                        line_number=node.lineno,
                        suggested_fix="检查是否可以移除未使用的函数",
                        context={"function_name": node.name},
                        confidence=0.6
                    ))
        
        return issues

    def _is_function_used(self, tree: ast.AST, func_name: str) -> bool:
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == func_name:
                    return True
                elif isinstance(node.func, ast.Attribute) and node.func.attr == func_name:
                    return True
        return False

    def _check_magic_numbers(self, tree: ast.AST, content: str, file_path: str) -> List[Issue]:
        issues = []
        allowed_numbers = {0, 1, 2, -1, 100, 1000, 255, 360, 24, 60}
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant):
                if isinstance(node.value, (int, float)):
                    if node.value not in allowed_numbers:
                        parent = self._find_parent(tree, node)
                        if parent and not isinstance(parent, (ast.Assign, ast.AnnAssign, ast.FunctionDef)):
                            issues.append(self._create_issue(
                                severity=IssueSeverity.LOW,
                                message=f"发现魔法数字: {node.value}",
                                file_path=file_path,
                                line_number=node.lineno,
                                suggested_fix="将数字定义为常量并赋予有意义的名称",
                                context={"value": node.value},
                                confidence=0.6
                            ))
        
        return issues

    def _find_parent(self, tree: ast.AST, target: ast.AST) -> Optional[ast.AST]:
        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node):
                if child is target:
                    return node
        return None

    def _check_duplication(self, content: str, file_path: str) -> List[Issue]:
        issues = []
        lines = content.split('\n')
        
        line_hashes = {}
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if len(stripped) > 20 and not stripped.startswith('#'):
                line_hash = hashlib.md5(stripped.encode()).hexdigest()
                if line_hash in line_hashes:
                    issues.append(self._create_issue(
                        severity=IssueSeverity.LOW,
                        message=f"可能存在重复代码",
                        file_path=file_path,
                        line_number=i,
                        code_snippet=stripped[:50],
                        suggested_fix="考虑提取重复代码为独立函数",
                        context={"duplicate_line": line_hashes[line_hash]},
                        confidence=0.5
                    ))
                else:
                    line_hashes[line_hash] = i
        
        return issues


class DocumentationIssueDetector(BaseDetector):
    """文档问题检测器"""

    category = IssueCategory.DOCUMENTATION_MISSING
    name = "documentation_issue_detector"
    description = "检测文档相关问题"

    def detect(self, content: str, file_path: str) -> List[Issue]:
        issues = []
        
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return issues
        
        issues.extend(self._check_module_docstring(tree, content, file_path))
        issues.extend(self._check_function_docstrings(tree, content, file_path))
        issues.extend(self._check_class_docstrings(tree, content, file_path))
        issues.extend(self._check_docstring_quality(tree, content, file_path))
        
        return issues

    def _check_module_docstring(self, tree: ast.AST, content: str, file_path: str) -> List[Issue]:
        issues = []
        
        docstring = ast.get_docstring(tree)
        
        if not docstring:
            issues.append(self._create_issue(
                severity=IssueSeverity.LOW,
                message="模块缺少文档字符串",
                file_path=file_path,
                line_number=1,
                suggested_fix="在文件开头添加模块文档字符串",
                confidence=0.9
            ))
        elif len(docstring) < 20:
            issues.append(self._create_issue(
                severity=IssueSeverity.INFO,
                message="模块文档字符串过于简短",
                file_path=file_path,
                line_number=1,
                suggested_fix="扩展模块文档，说明模块用途和主要功能",
                confidence=0.8
            ))
        
        return issues

    def _check_function_docstrings(self, tree: ast.AST, content: str, file_path: str) -> List[Issue]:
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if node.name.startswith('_') and not node.name.startswith('__'):
                    continue
                
                docstring = ast.get_docstring(node)
                
                if not docstring:
                    issues.append(self._create_issue(
                        severity=IssueSeverity.LOW,
                        message=f"函数 '{node.name}' 缺少文档字符串",
                        file_path=file_path,
                        line_number=node.lineno,
                        suggested_fix="为函数添加文档字符串，说明功能、参数和返回值",
                        context={"function_name": node.name},
                        confidence=0.85
                    ))
                else:
                    issues.extend(self._check_param_documentation(node, docstring, file_path))
        
        return issues

    def _check_param_documentation(self, func: ast.FunctionDef, docstring: str, file_path: str) -> List[Issue]:
        issues = []
        
        params = [arg.arg for arg in func.args.args if arg.arg not in ('self', 'cls')]
        
        for param in params:
            if param not in docstring:
                issues.append(self._create_issue(
                    severity=IssueSeverity.INFO,
                    message=f"参数 '{param}' 未在文档中说明",
                    file_path=file_path,
                    line_number=func.lineno,
                    suggested_fix=f"在文档字符串中添加参数 '{param}' 的说明",
                    context={"parameter": param, "function_name": func.name},
                    confidence=0.75
                ))
        
        return issues

    def _check_class_docstrings(self, tree: ast.AST, content: str, file_path: str) -> List[Issue]:
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                docstring = ast.get_docstring(node)
                
                if not docstring:
                    issues.append(self._create_issue(
                        severity=IssueSeverity.LOW,
                        message=f"类 '{node.name}' 缺少文档字符串",
                        file_path=file_path,
                        line_number=node.lineno,
                        suggested_fix="为类添加文档字符串，说明类的用途和主要属性",
                        context={"class_name": node.name},
                        confidence=0.85
                    ))
        
        return issues

    def _check_docstring_quality(self, tree: ast.AST, content: str, file_path: str) -> List[Issue]:
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Module)):
                docstring = ast.get_docstring(node)
                
                if docstring:
                    if len(docstring) < 10:
                        issues.append(self._create_issue(
                            severity=IssueSeverity.INFO,
                            message=f"文档字符串过于简短",
                            file_path=file_path,
                            line_number=node.lineno if hasattr(node, 'lineno') else 1,
                            suggested_fix="扩展文档内容，提供更详细的说明",
                            confidence=0.7
                        ))
                    
                    if 'TODO' in docstring or 'FIXME' in docstring:
                        issues.append(self._create_issue(
                            severity=IssueSeverity.INFO,
                            message=f"文档中包含待办事项标记",
                            file_path=file_path,
                            line_number=node.lineno if hasattr(node, 'lineno') else 1,
                            suggested_fix="完成待办事项或移除标记",
                            confidence=0.8
                        ))
        
        return issues


class ConfigurationIssueDetector(BaseDetector):
    """配置问题检测器"""

    category = IssueCategory.CONFIG_MISSING_FILE
    name = "configuration_issue_detector"
    description = "检测配置相关问题"

    CONFIG_FILES = {
        'requirements.txt', 'setup.py', 'pyproject.toml', 'setup.cfg',
        'config.yaml', 'config.json', 'config.ini', '.env',
        'pytest.ini', 'tox.ini', '.flake8', '.pylintrc', 'mypy.ini'
    }

    def detect(self, content: str, file_path: str) -> List[Issue]:
        issues = []
        
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return issues
        
        issues.extend(self._check_config_imports(tree, content, file_path))
        issues.extend(self._check_environment_variables(tree, content, file_path))
        issues.extend(self._check_config_patterns(tree, content, file_path))
        
        return issues

    def _check_config_imports(self, tree: ast.AST, content: str, file_path: str) -> List[Issue]:
        issues = []
        
        config_modules = {'configparser', 'yaml', 'toml', 'dotenv', 'pydantic'}
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split('.')[0] in config_modules:
                        issues.extend(self._check_config_usage(tree, alias.name, file_path))
            elif isinstance(node, ast.ImportFrom):
                if node.module and node.module.split('.')[0] in config_modules:
                    issues.extend(self._check_config_usage(tree, node.module, file_path))
        
        return issues

    def _check_config_usage(self, tree: ast.AST, module: str, file_path: str) -> List[Issue]:
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_func_name(node.func)
                
                if 'load' in func_name or 'read' in func_name:
                    for arg in node.args:
                        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                            config_file = arg.value
                            if not self._is_valid_config_reference(config_file):
                                issues.append(self._create_issue(
                                    severity=IssueSeverity.MEDIUM,
                                    message=f"配置文件引用可能无效: {config_file}",
                                    file_path=file_path,
                                    line_number=node.lineno,
                                    suggested_fix="检查配置文件路径是否正确，使用 Path 对象处理路径",
                                    context={"config_file": config_file},
                                    confidence=0.7
                                ))
        
        return issues

    def _is_valid_config_reference(self, config_file: str) -> bool:
        if config_file.startswith(('.', '/', '~')):
            return True
        if any(ext in config_file for ext in ['.yaml', '.yml', '.json', '.ini', '.toml', '.env']):
            return True
        return False

    def _check_environment_variables(self, tree: ast.AST, content: str, file_path: str) -> List[Issue]:
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_func_name(node.func)
                
                if func_name in ['os.environ.get', 'os.getenv']:
                    if node.args:
                        if isinstance(node.args[0], ast.Constant):
                            var_name = node.args[0].value
                            
                            if len(node.args) == 1:
                                issues.append(self._create_issue(
                                    severity=IssueSeverity.MEDIUM,
                                    message=f"环境变量 '{var_name}' 缺少默认值",
                                    file_path=file_path,
                                    line_number=node.lineno,
                                    suggested_fix="为环境变量提供默认值，例如: os.getenv('VAR', 'default')",
                                    context={"variable_name": var_name},
                                    confidence=0.8
                                ))
        
        return issues

    def _check_config_patterns(self, tree: ast.AST, content: str, file_path: str) -> List[Issue]:
        issues = []
        lines = content.split('\n')
        
        hardcoded_paths = []
        for i, line in enumerate(lines, 1):
            if re.search(r'["\'][/\w\\]+\.(yaml|yml|json|ini|toml|env)["\']', line):
                if 'config' in line.lower() or 'setting' in line.lower():
                    hardcoded_paths.append((i, line.strip()))
        
        for line_num, line in hardcoded_paths:
            issues.append(self._create_issue(
                severity=IssueSeverity.LOW,
                message="硬编码配置文件路径",
                file_path=file_path,
                line_number=line_num,
                code_snippet=line[:80],
                suggested_fix="使用配置管理或环境变量来管理配置文件路径",
                confidence=0.7
            ))
        
        return issues

    def _get_func_name(self, node: ast.expr) -> str:
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            value_name = self._get_func_name(node.value)
            return f"{value_name}.{node.attr}"
        return ""


class IssueClassifier:
    """问题分类和定级系统"""

    CATEGORY_HIERARCHY = {
        'critical': ['SYNTAX', 'SECURITY', 'TEST_FAILURE'],
        'high': ['IMPORT', 'TYPE', 'CONFIG'],
        'medium': ['CODE_SMELL', 'PERFORMANCE'],
        'low': ['DOCUMENTATION', 'STYLE', 'DEPRECATED']
    }

    SEVERITY_WEIGHTS = {
        IssueSeverity.CRITICAL: 10,
        IssueSeverity.HIGH: 7,
        IssueSeverity.MEDIUM: 4,
        IssueSeverity.LOW: 2,
        IssueSeverity.INFO: 1
    }

    def __init__(self):
        self._classification_rules = self._build_classification_rules()

    def _build_classification_rules(self) -> Dict[str, Any]:
        return {
            'syntax': {
                'patterns': ['syntax', 'indentation', 'bracket', 'quote', 'colon'],
                'base_severity': IssueSeverity.CRITICAL,
                'auto_fixable': True
            },
            'security': {
                'patterns': ['sql_injection', 'xss', 'command_injection', 'hardcoded', 'ssl'],
                'base_severity': IssueSeverity.CRITICAL,
                'auto_fixable': False
            },
            'test': {
                'patterns': ['test', 'assertion', 'fixture', 'mock'],
                'base_severity': IssueSeverity.HIGH,
                'auto_fixable': True
            },
            'code_smell': {
                'patterns': ['duplication', 'long_method', 'complexity', 'dead_code'],
                'base_severity': IssueSeverity.MEDIUM,
                'auto_fixable': True
            },
            'documentation': {
                'patterns': ['missing_doc', 'incomplete', 'outdated'],
                'base_severity': IssueSeverity.LOW,
                'auto_fixable': True
            }
        }

    def classify_issue(self, issue: Issue) -> Dict[str, Any]:
        classification = {
            'issue_id': issue.issue_id,
            'primary_category': self._determine_primary_category(issue),
            'severity_score': self._calculate_severity_score(issue),
            'auto_fixable': self._is_auto_fixable(issue),
            'priority': self._calculate_priority(issue),
            'tags': self._generate_tags(issue),
            'related_categories': self._find_related_categories(issue)
        }
        
        return classification

    def _determine_primary_category(self, issue: Issue) -> str:
        category_name = issue.category.name
        
        for main_category, patterns in self.CATEGORY_HIERARCHY.items():
            for pattern in patterns:
                if pattern in category_name:
                    return main_category
        
        return 'other'

    def _calculate_severity_score(self, issue: Issue) -> float:
        base_score = self.SEVERITY_WEIGHTS.get(issue.severity, 1)
        
        confidence_modifier = issue.confidence
        
        context_bonus = 0
        if issue.context:
            if 'deprecated' in str(issue.context).lower():
                context_bonus += 1
            if 'security' in str(issue.context).lower():
                context_bonus += 3
        
        return base_score * confidence_modifier + context_bonus

    def _is_auto_fixable(self, issue: Issue) -> bool:
        auto_fixable_categories = {
            IssueCategory.SYNTAX_INDENTATION,
            IssueCategory.SYNTAX_COLON_MISSING,
            IssueCategory.IMPORT_UNUSED,
            IssueCategory.TYPE_MISSING_ANNOTATION,
            IssueCategory.CODE_SMELL_DUPLICATION,
            IssueCategory.DOCUMENTATION_MISSING
        }
        
        return issue.category in auto_fixable_categories

    def _calculate_priority(self, issue: Issue) -> int:
        severity_priority = {
            IssueSeverity.CRITICAL: 100,
            IssueSeverity.HIGH: 75,
            IssueSeverity.MEDIUM: 50,
            IssueSeverity.LOW: 25,
            IssueSeverity.INFO: 10
        }
        
        base_priority = severity_priority.get(issue.severity, 10)
        
        if issue.confidence >= 0.9:
            base_priority += 10
        elif issue.confidence < 0.7:
            base_priority -= 10
        
        return max(1, min(100, base_priority))

    def _generate_tags(self, issue: Issue) -> List[str]:
        tags = []
        
        category_name = issue.category.name.lower()
        tags.extend(category_name.split('_'))
        
        if 'security' in category_name:
            tags.append('security')
        if 'test' in category_name:
            tags.append('testing')
        if 'smell' in category_name:
            tags.append('refactoring')
        
        if issue.confidence >= 0.9:
            tags.append('high-confidence')
        elif issue.confidence < 0.7:
            tags.append('low-confidence')
        
        return list(set(tags))

    def _find_related_categories(self, issue: Issue) -> List[str]:
        related = []
        
        category_relations = {
            IssueCategory.SYNTAX_ERROR: [IssueCategory.SYNTAX_INDENTATION, IssueCategory.SYNTAX_BRACKET_MISMATCH],
            IssueCategory.IMPORT_MISSING: [IssueCategory.IMPORT_UNUSED, IssueCategory.IMPORT_PATH_ERROR],
            IssueCategory.TYPE_ERROR: [IssueCategory.TYPE_MISMATCH, IssueCategory.TYPE_MISSING_ANNOTATION],
            IssueCategory.SECURITY_SQL_INJECTION: [IssueCategory.SECURITY_COMMAND_INJECTION, IssueCategory.SECURITY_XSS]
        }
        
        related = category_relations.get(issue.category, [])
        
        return [cat.name for cat in related]

    def classify_batch(self, issues: List[Issue]) -> Dict[str, Any]:
        classifications = [self.classify_issue(issue) for issue in issues]
        
        summary = {
            'total_issues': len(issues),
            'by_category': defaultdict(int),
            'by_severity': defaultdict(int),
            'by_priority': defaultdict(list),
            'auto_fixable_count': 0,
            'average_severity_score': 0
        }
        
        for classification in classifications:
            summary['by_category'][classification['primary_category']] += 1
            summary['by_severity'][classification['severity_score']] += 1
            summary['by_priority'][classification['priority']].append(classification['issue_id'])
            
            if classification['auto_fixable']:
                summary['auto_fixable_count'] += 1
        
        if classifications:
            summary['average_severity_score'] = sum(
                c['severity_score'] for c in classifications
            ) / len(classifications)
        
        return {
            'classifications': classifications,
            'summary': dict(summary)
        }


class RootCauseAnalyzer:
    """问题根因分析器"""

    def __init__(self):
        self._causality_rules = self._build_causality_rules()
        self._analysis_history: List[Dict[str, Any]] = []

    def _build_causality_rules(self) -> Dict[str, Any]:
        return {
            'syntax_error': {
                'common_causes': [
                    '拼写错误',
                    '复制粘贴错误',
                    '编辑器配置问题',
                    '缺少必要的语法元素'
                ],
                'related_patterns': ['indentation', 'bracket', 'quote']
            },
            'import_error': {
                'common_causes': [
                    '模块未安装',
                    'Python路径配置错误',
                    '虚拟环境问题',
                    '模块名称拼写错误'
                ],
                'related_patterns': ['missing', 'path_error', 'circular']
            },
            'type_error': {
                'common_causes': [
                    '类型注解不完整',
                    '类型推断失败',
                    '不兼容的类型操作',
                    '缺少类型转换'
                ],
                'related_patterns': ['mismatch', 'annotation', 'return']
            },
            'security_issue': {
                'common_causes': [
                    '缺乏安全意识',
                    '快速开发忽略安全',
                    '使用了不安全的默认配置',
                    '缺少输入验证'
                ],
                'related_patterns': ['injection', 'xss', 'hardcoded']
            },
            'test_failure': {
                'common_causes': [
                    '代码逻辑错误',
                    '测试数据问题',
                    '环境配置差异',
                    '依赖版本不匹配'
                ],
                'related_patterns': ['assertion', 'fixture', 'timeout']
            },
            'code_smell': {
                'common_causes': [
                    '快速迭代累积',
                    '缺少重构',
                    '设计模式应用不当',
                    '代码审查不足'
                ],
                'related_patterns': ['duplication', 'complexity', 'long_method']
            }
        }

    def analyze(self, issues: List[Issue]) -> Dict[str, Any]:
        if not issues:
            return {'root_causes': [], 'analysis_summary': {}}
        
        root_causes = []
        
        grouped_issues = self._group_issues_by_category(issues)
        
        for category, category_issues in grouped_issues.items():
            cause_analysis = self._analyze_category_root_causes(category, category_issues)
            root_causes.append(cause_analysis)
        
        cross_category_analysis = self._analyze_cross_category_patterns(issues)
        
        analysis_summary = self._generate_analysis_summary(root_causes, cross_category_analysis)
        
        result = {
            'root_causes': root_causes,
            'cross_category_patterns': cross_category_analysis,
            'analysis_summary': analysis_summary,
            'recommendations': self._generate_recommendations(root_causes)
        }
        
        self._analysis_history.append({
            'timestamp': datetime.now().isoformat(),
            'issue_count': len(issues),
            'root_cause_count': len(root_causes)
        })
        
        return result

    def _group_issues_by_category(self, issues: List[Issue]) -> Dict[str, List[Issue]]:
        groups = defaultdict(list)
        
        for issue in issues:
            category_prefix = issue.category.name.split('_')[0]
            groups[category_prefix].append(issue)
        
        return dict(groups)

    def _analyze_category_root_causes(self, category: str, issues: List[Issue]) -> Dict[str, Any]:
        category_lower = category.lower()
        
        rules = self._causality_rules.get(category_lower, {
            'common_causes': ['未知原因'],
            'related_patterns': []
        })
        
        affected_files = list(set(issue.file_path for issue in issues))
        affected_lines = [issue.line_number for issue in issues]
        
        patterns_found = self._identify_patterns(issues)
        
        primary_cause = self._determine_primary_cause(issues, rules)
        
        return {
            'category': category,
            'issue_count': len(issues),
            'common_causes': rules['common_causes'],
            'primary_cause': primary_cause,
            'affected_files': affected_files,
            'affected_lines_count': len(affected_lines),
            'patterns_identified': patterns_found,
            'severity_distribution': self._calculate_severity_distribution(issues),
            'confidence': self._calculate_analysis_confidence(issues)
        }

    def _identify_patterns(self, issues: List[Issue]) -> List[str]:
        patterns = []
        
        messages = [issue.message.lower() for issue in issues]
        
        if any('missing' in msg for msg in messages):
            patterns.append('缺失模式')
        if any('unused' in msg for msg in messages):
            patterns.append('未使用模式')
        if any('invalid' in msg or 'error' in msg for msg in messages):
            patterns.append('错误模式')
        if any('deprecated' in msg for msg in messages):
            patterns.append('过时模式')
        
        return list(set(patterns))

    def _determine_primary_cause(self, issues: List[Issue], rules: Dict[str, Any]) -> str:
        if not rules['common_causes']:
            return '未知原因'
        
        return rules['common_causes'][0]

    def _calculate_severity_distribution(self, issues: List[Issue]) -> Dict[str, int]:
        distribution = defaultdict(int)
        for issue in issues:
            distribution[issue.severity.value] += 1
        return dict(distribution)

    def _calculate_analysis_confidence(self, issues: List[Issue]) -> float:
        if not issues:
            return 0.0
        
        avg_confidence = sum(issue.confidence for issue in issues) / len(issues)
        
        sample_size_factor = min(1.0, len(issues) / 10)
        
        return avg_confidence * sample_size_factor

    def _analyze_cross_category_patterns(self, issues: List[Issue]) -> List[Dict[str, Any]]:
        patterns = []
        
        file_issue_map = defaultdict(list)
        for issue in issues:
            file_issue_map[issue.file_path].append(issue)
        
        for file_path, file_issues in file_issue_map.items():
            if len(file_issues) >= 3:
                categories = list(set(issue.category.name.split('_')[0] for issue in file_issues))
                
                if len(categories) >= 2:
                    patterns.append({
                        'type': 'multi_category_file',
                        'file_path': file_path,
                        'categories': categories,
                        'issue_count': len(file_issues),
                        'suggestion': f"文件 {file_path} 存在多种类型的问题，建议进行全面重构"
                    })
        
        return patterns

    def _generate_analysis_summary(self, root_causes: List[Dict], cross_patterns: List[Dict]) -> Dict[str, Any]:
        total_issues = sum(rc['issue_count'] for rc in root_causes)
        
        most_common_category = max(root_causes, key=lambda x: x['issue_count'])['category'] if root_causes else 'N/A'
        
        avg_confidence = sum(rc['confidence'] for rc in root_causes) / len(root_causes) if root_causes else 0
        
        return {
            'total_issues_analyzed': total_issues,
            'categories_affected': len(root_causes),
            'most_common_category': most_common_category,
            'cross_category_patterns_count': len(cross_patterns),
            'average_confidence': round(avg_confidence, 2),
            'analysis_quality': 'high' if avg_confidence > 0.8 else 'medium' if avg_confidence > 0.6 else 'low'
        }

    def _generate_recommendations(self, root_causes: List[Dict]) -> List[str]:
        recommendations = []
        
        for rc in root_causes:
            if rc['issue_count'] > 5:
                recommendations.append(
                    f"优先处理 {rc['category']} 类别的问题（{rc['issue_count']} 个），主要原因是: {rc['primary_cause']}"
                )
        
        if any(rc['category'] == 'SECURITY' for rc in root_causes):
            recommendations.append("安全问题需要立即处理，建议进行安全代码审查")
        
        if any(rc['category'] == 'SYNTAX' for rc in root_causes):
            recommendations.append("语法错误阻止代码运行，应首先修复")
        
        if not recommendations:
            recommendations.append("代码质量良好，继续保持代码审查习惯")
        
        return recommendations


class DiagnosticReportGenerator:
    """问题诊断报告生成器"""

    def __init__(self):
        self.classifier = IssueClassifier()
        self.root_cause_analyzer = RootCauseAnalyzer()

    def generate_report(
        self, 
        detection_result: DetectionResult,
        include_recommendations: bool = True
    ) -> Dict[str, Any]:
        report = {
            'report_id': self._generate_report_id(),
            'generated_at': datetime.now().isoformat(),
            'file_path': detection_result.file_path,
            'summary': self._generate_summary(detection_result),
            'issues_detail': self._generate_issues_detail(detection_result),
            'classification': self._generate_classification(detection_result),
            'root_cause_analysis': self._generate_root_cause_analysis(detection_result),
            'statistics': self._generate_statistics(detection_result)
        }
        
        if include_recommendations:
            report['recommendations'] = self._generate_recommendations(detection_result)
        
        report['quality_metrics'] = self._calculate_quality_metrics(detection_result)
        
        return report

    def _generate_report_id(self) -> str:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        random_suffix = hashlib.md5(str(datetime.now().timestamp()).encode()).hexdigest()[:8]
        return f"DIAG_{timestamp}_{random_suffix}"

    def _generate_summary(self, result: DetectionResult) -> Dict[str, Any]:
        return {
            'status': result.status.value,
            'total_issues': result.total_issues,
            'critical_count': result.critical_count,
            'high_count': result.high_count,
            'medium_count': result.medium_count,
            'low_count': result.low_count,
            'detection_time_ms': round(result.detection_time_ms, 2),
            'detectors_used': result.detectors_used,
            'health_score': self._calculate_health_score(result)
        }

    def _calculate_health_score(self, result: DetectionResult) -> float:
        if result.total_issues == 0:
            return 100.0
        
        penalty = (
            result.critical_count * 20 +
            result.high_count * 10 +
            result.medium_count * 5 +
            result.low_count * 2
        )
        
        score = max(0, 100 - penalty)
        
        return round(score, 1)

    def _generate_issues_detail(self, result: DetectionResult) -> List[Dict[str, Any]]:
        details = []
        
        for issue in result.issues:
            detail = {
                'issue_id': issue.issue_id,
                'category': issue.category.name,
                'severity': issue.severity.value,
                'message': issue.message,
                'location': {
                    'file': issue.file_path,
                    'line': issue.line_number,
                    'column': issue.column,
                    'end_line': issue.end_line,
                    'end_column': issue.end_column
                },
                'code_snippet': issue.code_snippet,
                'suggested_fix': issue.suggested_fix,
                'confidence': issue.confidence,
                'detector': issue.detector_name
            }
            details.append(detail)
        
        return details

    def _generate_classification(self, result: DetectionResult) -> Dict[str, Any]:
        return self.classifier.classify_batch(result.issues)

    def _generate_root_cause_analysis(self, result: DetectionResult) -> Dict[str, Any]:
        return self.root_cause_analyzer.analyze(result.issues)

    def _generate_statistics(self, result: DetectionResult) -> Dict[str, Any]:
        if not result.issues:
            return {
                'by_category': {},
                'by_severity': {},
                'by_detector': {},
                'average_confidence': 0
            }
        
        by_category = defaultdict(int)
        by_severity = defaultdict(int)
        by_detector = defaultdict(int)
        confidences = []
        
        for issue in result.issues:
            by_category[issue.category.name] += 1
            by_severity[issue.severity.value] += 1
            by_detector[issue.detector_name] += 1
            confidences.append(issue.confidence)
        
        return {
            'by_category': dict(by_category),
            'by_severity': dict(by_severity),
            'by_detector': dict(by_detector),
            'average_confidence': round(sum(confidences) / len(confidences), 2) if confidences else 0
        }

    def _generate_recommendations(self, result: DetectionResult) -> List[Dict[str, Any]]:
        recommendations = []
        
        if result.critical_count > 0:
            recommendations.append({
                'priority': 'immediate',
                'category': 'critical_issues',
                'message': f"发现 {result.critical_count} 个严重问题需要立即修复",
                'action': "优先处理所有 CRITICAL 级别的问题"
            })
        
        if result.high_count > 0:
            recommendations.append({
                'priority': 'high',
                'category': 'high_priority_issues',
                'message': f"发现 {result.high_count} 个高优先级问题",
                'action': "在下一个开发周期内修复 HIGH 级别的问题"
            })
        
        security_issues = [i for i in result.issues if 'SECURITY' in i.category.name]
        if security_issues:
            recommendations.append({
                'priority': 'immediate',
                'category': 'security',
                'message': f"发现 {len(security_issues)} 个安全问题",
                'action': "进行安全代码审查，修复所有安全漏洞"
            })
        
        test_issues = [i for i in result.issues if 'TEST' in i.category.name]
        if test_issues:
            recommendations.append({
                'priority': 'high',
                'category': 'testing',
                'message': f"发现 {len(test_issues)} 个测试相关问题",
                'action': "完善测试用例，确保测试覆盖率"
            })
        
        doc_issues = [i for i in result.issues if 'DOCUMENTATION' in i.category.name]
        if len(doc_issues) > 5:
            recommendations.append({
                'priority': 'low',
                'category': 'documentation',
                'message': f"发现 {len(doc_issues)} 个文档问题",
                'action': "补充和完善代码文档"
            })
        
        return recommendations

    def _calculate_quality_metrics(self, result: DetectionResult) -> Dict[str, Any]:
        if not result.issues:
            return {
                'code_quality_score': 100,
                'security_score': 100,
                'maintainability_score': 100,
                'test_quality_score': 100,
                'documentation_score': 100
            }
        
        security_issues = sum(1 for i in result.issues if 'SECURITY' in i.category.name)
        test_issues = sum(1 for i in result.issues if 'TEST' in i.category.name)
        doc_issues = sum(1 for i in result.issues if 'DOCUMENTATION' in i.category.name)
        smell_issues = sum(1 for i in result.issues if 'CODE_SMELL' in i.category.name)
        
        security_score = max(0, 100 - security_issues * 15)
        test_quality_score = max(0, 100 - test_issues * 10)
        documentation_score = max(0, 100 - doc_issues * 5)
        maintainability_score = max(0, 100 - smell_issues * 8)
        
        code_quality_score = (
            security_score * 0.3 +
            test_quality_score * 0.2 +
            documentation_score * 0.2 +
            maintainability_score * 0.3
        )
        
        return {
            'code_quality_score': round(code_quality_score, 1),
            'security_score': round(security_score, 1),
            'maintainability_score': round(maintainability_score, 1),
            'test_quality_score': round(test_quality_score, 1),
            'documentation_score': round(documentation_score, 1)
        }

    def generate_summary_report(self, results: Dict[str, DetectionResult]) -> Dict[str, Any]:
        total_issues = sum(r.total_issues for r in results.values())
        total_critical = sum(r.critical_count for r in results.values())
        total_high = sum(r.high_count for r in results.values())
        
        files_with_issues = sum(1 for r in results.values() if r.total_issues > 0)
        
        all_issues = []
        for result in results.values():
            all_issues.extend(result.issues)
        
        root_cause_analysis = self.root_cause_analyzer.analyze(all_issues)
        
        return {
            'report_id': self._generate_report_id(),
            'generated_at': datetime.now().isoformat(),
            'project_summary': {
                'files_analyzed': len(results),
                'files_with_issues': files_with_issues,
                'total_issues': total_issues,
                'critical_issues': total_critical,
                'high_issues': total_high
            },
            'root_cause_analysis': root_cause_analysis,
            'top_issues': self._get_top_issues(all_issues, 10),
            'recommendations': root_cause_analysis.get('recommendations', [])
        }

    def _get_top_issues(self, issues: List[Issue], limit: int) -> List[Dict[str, Any]]:
        severity_order = {
            IssueSeverity.CRITICAL: 0,
            IssueSeverity.HIGH: 1,
            IssueSeverity.MEDIUM: 2,
            IssueSeverity.LOW: 3,
            IssueSeverity.INFO: 4
        }
        
        sorted_issues = sorted(
            issues,
            key=lambda i: (severity_order.get(i.severity, 5), -i.confidence)
        )
        
        return [
            {
                'issue_id': issue.issue_id,
                'category': issue.category.name,
                'severity': issue.severity.value,
                'message': issue.message,
                'file': issue.file_path,
                'line': issue.line_number
            }
            for issue in sorted_issues[:limit]
        ]

    def export_report(self, report: Dict[str, Any], output_path: str, format: str = 'json') -> None:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        if format == 'json':
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
        elif format == 'text':
            text_report = self._format_text_report(report)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(text_report)
        else:
            raise ValueError(f"不支持的格式: {format}")

    def _format_text_report(self, report: Dict[str, Any]) -> str:
        lines = []
        
        lines.append("=" * 80)
        lines.append("问题诊断报告")
        lines.append("=" * 80)
        lines.append(f"报告ID: {report.get('report_id', 'N/A')}")
        lines.append(f"生成时间: {report.get('generated_at', 'N/A')}")
        lines.append(f"文件路径: {report.get('file_path', 'N/A')}")
        lines.append("")
        
        if 'summary' in report:
            summary = report['summary']
            lines.append("-" * 80)
            lines.append("摘要")
            lines.append("-" * 80)
            lines.append(f"状态: {summary.get('status', 'N/A')}")
            lines.append(f"总问题数: {summary.get('total_issues', 0)}")
            lines.append(f"健康分数: {summary.get('health_score', 0)}")
            lines.append(f"  严重: {summary.get('critical_count', 0)}")
            lines.append(f"  高: {summary.get('high_count', 0)}")
            lines.append(f"  中: {summary.get('medium_count', 0)}")
            lines.append(f"  低: {summary.get('low_count', 0)}")
            lines.append("")
        
        if 'issues_detail' in report and report['issues_detail']:
            lines.append("-" * 80)
            lines.append("问题详情")
            lines.append("-" * 80)
            for issue in report['issues_detail'][:20]:
                lines.append(f"[{issue['severity']}] {issue['category']}: {issue['message']}")
                lines.append(f"  位置: {issue['location']['file']}:{issue['location']['line']}")
                if issue.get('suggested_fix'):
                    lines.append(f"  建议: {issue['suggested_fix']}")
                lines.append("")
        
        if 'recommendations' in report and report['recommendations']:
            lines.append("-" * 80)
            lines.append("建议")
            lines.append("-" * 80)
            for rec in report['recommendations']:
                lines.append(f"[{rec['priority']}] {rec['message']}")
                lines.append(f"  行动: {rec['action']}")
                lines.append("")
        
        lines.append("=" * 80)
        
        return "\n".join(lines)


class IssueDetector:
    """问题检测器主类"""

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self._detectors: Dict[str, BaseDetector] = {}
        self._result_counter = 0
        self._register_builtin_detectors()

    def _register_builtin_detectors(self) -> None:
        detectors = [
            SyntaxErrorDetector(),
            ImportErrorDetector(),
            TypeErrorDetector(),
            SecurityVulnerabilityDetector(),
            TestFailureDetector(),
            CodeSmellDetector(),
            DocumentationIssueDetector(),
            ConfigurationIssueDetector(),
        ]
        
        for detector in detectors:
            self._detectors[detector.name] = detector
            logger.info(f"已注册检测器: {detector.name}")

    def register_detector(self, detector: BaseDetector) -> None:
        self._detectors[detector.name] = detector
        logger.info(f"已注册检测器: {detector.name}")

    def detect_file(self, file_path: str, detectors: Optional[List[str]] = None) -> DetectionResult:
        import time
        start_time = time.perf_counter()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            logger.error(f"读取文件失败: {file_path}, {e}")
            return self._create_error_result(file_path, str(e))
        
        all_issues = []
        detectors_used = []
        
        detector_list = (
            [self._detectors[d] for d in detectors if d in self._detectors]
            if detectors
            else list(self._detectors.values())
        )
        
        for detector in detector_list:
            try:
                issues = detector.detect(content, file_path)
                all_issues.extend(issues)
                detectors_used.append(detector.name)
            except Exception as e:
                logger.error(f"检测器 {detector.name} 执行失败: {e}")
        
        detection_time = (time.perf_counter() - start_time) * 1000
        
        return self._create_result(file_path, all_issues, detection_time, detectors_used)

    def _create_result(
        self,
        file_path: str,
        issues: List[Issue],
        detection_time: float,
        detectors_used: List[str]
    ) -> DetectionResult:
        self._result_counter += 1
        
        critical = sum(1 for i in issues if i.severity == IssueSeverity.CRITICAL)
        high = sum(1 for i in issues if i.severity == IssueSeverity.HIGH)
        medium = sum(1 for i in issues if i.severity == IssueSeverity.MEDIUM)
        low = sum(1 for i in issues if i.severity == IssueSeverity.LOW)
        
        status = DetectionStatus.SUCCESS if issues else DetectionStatus.SUCCESS
        if critical > 0:
            status = DetectionStatus.PARTIAL
        
        return DetectionResult(
            result_id=f"DETECT_{self._result_counter:04d}",
            file_path=file_path,
            status=status,
            issues=issues,
            total_issues=len(issues),
            critical_count=critical,
            high_count=high,
            medium_count=medium,
            low_count=low,
            detection_time_ms=detection_time,
            detectors_used=detectors_used
        )

    def _create_error_result(self, file_path: str, error_message: str) -> DetectionResult:
        self._result_counter += 1
        
        return DetectionResult(
            result_id=f"DETECT_{self._result_counter:04d}",
            file_path=file_path,
            status=DetectionStatus.FAILED,
            issues=[],
            total_issues=0,
            critical_count=0,
            high_count=0,
            medium_count=0,
            low_count=0,
            detection_time_ms=0,
            detectors_used=[],
            metadata={"error": error_message}
        )

    def detect_project(self, file_pattern: str = "*.py") -> Dict[str, DetectionResult]:
        results = {}
        
        for py_file in self.project_root.rglob(file_pattern):
            if '.git' in str(py_file) or '__pycache__' in str(py_file):
                continue
            
            result = self.detect_file(str(py_file))
            results[str(py_file)] = result
        
        return results

    def get_detector(self, name: str) -> Optional[BaseDetector]:
        return self._detectors.get(name)

    def list_detectors(self) -> List[str]:
        return list(self._detectors.keys())


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="问题检测器")
    parser.add_argument("--file", type=str, help="要检测的文件")
    parser.add_argument("--project", action="store_true", help="检测整个项目")
    parser.add_argument("--detectors", type=str, nargs="+", help="指定检测器")
    parser.add_argument("--output", type=str, help="输出文件路径")
    parser.add_argument("--report", action="store_true", help="生成诊断报告")
    parser.add_argument("--format", type=str, choices=['json', 'text'], default='json', help="报告格式")
    
    args = parser.parse_args()
    
    detector = IssueDetector()
    report_generator = DiagnosticReportGenerator()
    
    if args.file:
        result = detector.detect_file(args.file, args.detectors)
        
        print(f"\n检测结果: {result.file_path}")
        print(f"状态: {result.status.value}")
        print(f"总问题数: {result.total_issues}")
        print(f"严重: {result.critical_count}, 高: {result.high_count}, 中: {result.medium_count}, 低: {result.low_count}")
        print(f"检测耗时: {result.detection_time_ms:.2f}ms")
        
        print("\n问题列表:")
        for issue in result.issues:
            print(f"  [{issue.severity.value}] {issue.category.name}: {issue.message}")
            print(f"    位置: 行 {issue.line_number}")
            if issue.suggested_fix:
                print(f"    建议: {issue.suggested_fix}")
        
        if args.report or args.output:
            report = report_generator.generate_report(result)
            
            if args.output:
                report_generator.export_report(report, args.output, args.format)
                print(f"\n诊断报告已保存到: {args.output}")
            else:
                print("\n" + "="*80)
                print("诊断报告摘要:")
                print("="*80)
                print(f"健康分数: {report['summary']['health_score']}")
                print(f"质量指标:")
                for key, value in report['quality_metrics'].items():
                    print(f"  {key}: {value}")
                
                if report.get('recommendations'):
                    print("\n建议:")
                    for rec in report['recommendations']:
                        print(f"  [{rec['priority']}] {rec['message']}")
    
    elif args.project:
        results = detector.detect_project()
        
        total_issues = sum(r.total_issues for r in results.values())
        total_critical = sum(r.critical_count for r in results.values())
        
        print(f"\n项目检测结果:")
        print(f"检测文件数: {len(results)}")
        print(f"总问题数: {total_issues}")
        print(f"严重问题: {total_critical}")
        
        if args.report or args.output:
            summary_report = report_generator.generate_summary_report(results)
            
            if args.output:
                report_generator.export_report(summary_report, args.output, args.format)
                print(f"\n项目诊断报告已保存到: {args.output}")
            else:
                print("\n" + "="*80)
                print("项目诊断报告摘要:")
                print("="*80)
                print(f"分析文件数: {summary_report['project_summary']['files_analyzed']}")
                print(f"存在问题文件数: {summary_report['project_summary']['files_with_issues']}")
                
                if summary_report.get('recommendations'):
                    print("\n建议:")
                    for rec in summary_report['recommendations']:
                        print(f"  - {rec}")
        
        elif args.output:
            output_data = {k: v.to_dict() for k, v in results.items()}
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
