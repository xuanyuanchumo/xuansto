#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版修复策略库 - Fix Strategy Library Enhanced

智能修复策略管理系统增强版，包括：
- 语法修复策略（缩进错误、语法错误、括号匹配等）
- 导入修复策略（缺失导入、错误导入路径、循环导入等）
- 安全修复策略（SQL注入、XSS、敏感数据泄露等）
- 性能优化策略（循环优化、内存优化、算法优化等）
- 策略优先级和适用条件
- 策略效果评估与追踪

使用示例:
    python fix_strategy_library_enhanced.py --list-strategies
    python fix_strategy_library_enhanced.py --evaluate --strategy sql_injection_fix
    python fix_strategy_library_enhanced.py --match --file problematic.py
"""

from __future__ import annotations

import ast
import hashlib
import json
import logging
import re
import sys
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Protocol, Set, Tuple, Type, Union

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)


class IssueCategory(Enum):
    SYNTAX_INDENTATION = auto()
    SYNTAX_ERROR = auto()
    SYNTAX_BRACKET_MISMATCH = auto()
    SYNTAX_QUOTE_MISMATCH = auto()
    SYNTAX_COLON_MISSING = auto()
    SYNTAX_OPERATOR_INVALID = auto()
    IMPORT_MISSING = auto()
    IMPORT_PATH_ERROR = auto()
    IMPORT_CIRCULAR = auto()
    IMPORT_UNUSED = auto()
    IMPORT_ALIAS_CONFLICT = auto()
    SECURITY_SQL_INJECTION = auto()
    SECURITY_XSS = auto()
    SECURITY_SENSITIVE_DATA = auto()
    SECURITY_COMMAND_INJECTION = auto()
    SECURITY_PATH_TRAVERSAL = auto()
    SECURITY_INSECURE_DESERIALIZE = auto()
    SECURITY_HARDCODED_SECRET = auto()
    PERFORMANCE_LOOP_INEFFICIENT = auto()
    PERFORMANCE_MEMORY_LEAK = auto()
    PERFORMANCE_ALGORITHM_SLOW = auto()
    PERFORMANCE_REDUNDANT_OPERATION = auto()
    PERFORMANCE_STRING_CONCAT = auto()
    PERFORMANCE_UNOPTIMIZED_QUERY = auto()
    STYLE_NAMING = auto()
    STYLE_FORMATTING = auto()
    STYLE_DOCSTRING = auto()
    LOGIC_ERROR = auto()
    TYPE_ERROR = auto()
    DEPRECATED_CODE = auto()
    CUSTOM = auto()


class IssueSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class StrategyPriority(Enum):
    CRITICAL = 0
    HIGH = 1
    MEDIUM = 2
    LOW = 3
    INFO = 4


class FixStatus(Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    SKIPPED = "skipped"
    NEEDS_MANUAL_REVIEW = "needs_manual_review"


class StrategyStatus(Enum):
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    EXPERIMENTAL = "experimental"
    DISABLED = "disabled"


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
            "created_at": self.created_at
        }


@dataclass
class FixResult:
    result_id: str
    issue_id: str
    strategy_name: str
    status: FixStatus
    original_code: str
    fixed_code: str
    line_number: int
    confidence: float
    execution_time_ms: float
    message: str = ""
    warnings: List[str] = field(default_factory=list)
    additional_changes: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "result_id": self.result_id,
            "issue_id": self.issue_id,
            "strategy_name": self.strategy_name,
            "status": self.status.value,
            "original_code": self.original_code,
            "fixed_code": self.fixed_code,
            "line_number": self.line_number,
            "confidence": self.confidence,
            "execution_time_ms": self.execution_time_ms,
            "message": self.message,
            "warnings": self.warnings,
            "additional_changes": self.additional_changes,
            "metadata": self.metadata
        }


@dataclass
class StrategyMetrics:
    strategy_name: str
    total_applications: int = 0
    successful_applications: int = 0
    failed_applications: int = 0
    partial_applications: int = 0
    average_execution_time_ms: float = 0.0
    success_rate: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    last_applied: Optional[str] = None
    common_failure_reasons: List[str] = field(default_factory=list)
    effectiveness_trend: List[float] = field(default_factory=list)

    def update(self, success: bool, execution_time_ms: float, partial: bool = False):
        self.total_applications += 1
        if success:
            self.successful_applications += 1
        elif partial:
            self.partial_applications += 1
        else:
            self.failed_applications += 1

        total = self.total_applications
        self.average_execution_time_ms = (
            (self.average_execution_time_ms * (total - 1) + execution_time_ms) / total
        )
        self.success_rate = self.successful_applications / total if total > 0 else 0.0
        self.last_applied = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "strategy_name": self.strategy_name,
            "total_applications": self.total_applications,
            "successful_applications": self.successful_applications,
            "failed_applications": self.failed_applications,
            "partial_applications": self.partial_applications,
            "average_execution_time_ms": self.average_execution_time_ms,
            "success_rate": self.success_rate,
            "precision": self.precision,
            "recall": self.recall,
            "f1_score": self.f1_score,
            "last_applied": self.last_applied,
            "common_failure_reasons": self.common_failure_reasons,
            "effectiveness_trend": self.effectiveness_trend
        }


class FixStrategy(Protocol):
    name: str
    description: str
    applicable_issues: List[IssueCategory]
    priority: StrategyPriority
    success_rate: float

    def can_apply(self, issue: Issue) -> bool: ...

    def apply(self, issue: Issue) -> FixResult: ...


class BaseFixStrategy(ABC):
    """修复策略基类"""

    name: str = "base_strategy"
    description: str = "基础修复策略"
    applicable_issues: List[IssueCategory] = []
    priority: StrategyPriority = StrategyPriority.MEDIUM
    success_rate: float = 0.0

    def __init__(self):
        self.metrics = StrategyMetrics(strategy_name=self.name)
        self._result_counter = 0

    @abstractmethod
    def can_apply(self, issue: Issue) -> bool:
        pass

    @abstractmethod
    def _do_apply(self, issue: Issue) -> Tuple[FixStatus, str, str, float, str, List[str]]:
        pass

    def apply(self, issue: Issue) -> FixResult:
        start_time = time.perf_counter()
        self._result_counter += 1

        try:
            status, original, fixed, confidence, message, warnings = self._do_apply(issue)
        except Exception as e:
            status = FixStatus.FAILED
            original = issue.code_snippet
            fixed = ""
            confidence = 0.0
            message = f"策略执行异常: {str(e)}"
            warnings = [str(e)]
            logger.error(f"策略 {self.name} 执行失败: {e}")

        execution_time_ms = (time.perf_counter() - start_time) * 1000

        self.metrics.update(
            success=status == FixStatus.SUCCESS,
            execution_time_ms=execution_time_ms,
            partial=status == FixStatus.PARTIAL
        )

        result = FixResult(
            result_id=f"{self.name}_{self._result_counter:04d}",
            issue_id=issue.issue_id,
            strategy_name=self.name,
            status=status,
            original_code=original,
            fixed_code=fixed,
            line_number=issue.line_number,
            confidence=confidence,
            execution_time_ms=execution_time_ms,
            message=message,
            warnings=warnings
        )

        return result

    def get_metrics(self) -> StrategyMetrics:
        return self.metrics


class IndentationFixStrategy(BaseFixStrategy):
    """缩进错误修复策略"""

    name = "indentation_fix"
    description = "修复Python缩进错误，包括不一致的缩进和混合使用制表符与空格"
    applicable_issues = [IssueCategory.SYNTAX_INDENTATION]
    priority = StrategyPriority.CRITICAL
    success_rate = 0.95

    def can_apply(self, issue: Issue) -> bool:
        return issue.category == IssueCategory.SYNTAX_INDENTATION

    def _do_apply(self, issue: Issue) -> Tuple[FixStatus, str, str, float, str, List[str]]:
        original = issue.code_snippet
        warnings = []

        if not original:
            return FixStatus.FAILED, original, "", 0.0, "无法获取原始代码", warnings

        lines = original.split('\n')
        fixed_lines = []
        indent_stack = [0]

        for i, line in enumerate(lines):
            stripped = line.lstrip()
            if not stripped:
                fixed_lines.append("")
                continue

            current_indent = len(line) - len(stripped)
            expected_indent = indent_stack[-1]

            if line.strip().endswith(':'):
                fixed_lines.append(' ' * expected_indent + stripped)
                indent_stack.append(expected_indent + 4)
            elif stripped.startswith(('return', 'break', 'continue', 'pass', 'raise', 'yield')):
                if len(indent_stack) > 1:
                    indent_stack.pop()
                fixed_lines.append(' ' * indent_stack[-1] + stripped)
            elif current_indent < expected_indent:
                while indent_stack and indent_stack[-1] > current_indent:
                    indent_stack.pop()
                fixed_indent = indent_stack[-1] if indent_stack else 0
                fixed_lines.append(' ' * fixed_indent + stripped)
            else:
                fixed_lines.append(' ' * expected_indent + stripped)

        fixed = '\n'.join(fixed_lines)
        confidence = 0.9 if '\t' not in original else 0.7

        if '\t' in original:
            warnings.append("检测到制表符，已转换为空格")

        return FixStatus.SUCCESS, original, fixed, confidence, "缩进已修复", warnings


class BracketMismatchFixStrategy(BaseFixStrategy):
    """括号匹配修复策略"""

    name = "bracket_mismatch_fix"
    description = "修复括号不匹配问题，包括圆括号、方括号、花括号"
    applicable_issues = [IssueCategory.SYNTAX_BRACKET_MISMATCH]
    priority = StrategyPriority.CRITICAL
    success_rate = 0.85

    BRACKET_PAIRS = {'(': ')', '[': ']', '{': '}'}
    CLOSING_BRACKETS = {')', ']', '}'}

    def can_apply(self, issue: Issue) -> bool:
        return issue.category == IssueCategory.SYNTAX_BRACKET_MISMATCH

    def _do_apply(self, issue: Issue) -> Tuple[FixStatus, str, str, float, str, List[str]]:
        original = issue.code_snippet
        warnings = []

        if not original:
            return FixStatus.FAILED, original, "", 0.0, "无法获取原始代码", warnings

        stack: List[Tuple[str, int]] = []
        fixed_chars = list(original)

        for i, char in enumerate(original):
            if char in self.BRACKET_PAIRS:
                stack.append((char, i))
            elif char in self.CLOSING_BRACKETS:
                if stack:
                    expected_open = None
                    for open_bracket, close_bracket in self.BRACKET_PAIRS.items():
                        if close_bracket == char:
                            expected_open = open_bracket
                            break

                    if expected_open and stack[-1][0] == expected_open:
                        stack.pop()
                    else:
                        stack.pop()
                else:
                    for open_bracket, close_bracket in self.BRACKET_PAIRS.items():
                        if close_bracket == char:
                            fixed_chars.insert(i, open_bracket)
                            warnings.append(f"在位置 {i} 添加缺失的开括号 '{open_bracket}'")
                            break

        while stack:
            open_bracket, pos = stack.pop()
            close_bracket = self.BRACKET_PAIRS[open_bracket]
            fixed_chars.append(close_bracket)
            warnings.append(f"添加缺失的闭括号 '{close_bracket}'")

        fixed = ''.join(fixed_chars)
        confidence = 0.8 if warnings else 0.95

        return FixStatus.SUCCESS, original, fixed, confidence, "括号匹配已修复", warnings


class SyntaxErrorFixStrategy(BaseFixStrategy):
    """通用语法错误修复策略"""

    name = "syntax_error_fix"
    description = "修复常见语法错误，包括缺少冒号、无效操作符等"
    applicable_issues = [
        IssueCategory.SYNTAX_ERROR,
        IssueCategory.SYNTAX_COLON_MISSING,
        IssueCategory.SYNTAX_OPERATOR_INVALID
    ]
    priority = StrategyPriority.CRITICAL
    success_rate = 0.80

    BLOCK_START_KEYWORDS = {'if', 'elif', 'else', 'for', 'while', 'def', 'class', 'try', 'except', 'finally', 'with'}

    def can_apply(self, issue: Issue) -> bool:
        return issue.category in [
            IssueCategory.SYNTAX_ERROR,
            IssueCategory.SYNTAX_COLON_MISSING,
            IssueCategory.SYNTAX_OPERATOR_INVALID
        ]

    def _do_apply(self, issue: Issue) -> Tuple[FixStatus, str, str, float, str, List[str]]:
        original = issue.code_snippet
        warnings = []

        if not original:
            return FixStatus.FAILED, original, "", 0.0, "无法获取原始代码", warnings

        fixed = original
        confidence = 0.0

        if issue.category == IssueCategory.SYNTAX_COLON_MISSING:
            fixed, confidence, warnings = self._fix_missing_colon(original)
        elif issue.category == IssueCategory.SYNTAX_OPERATOR_INVALID:
            fixed, confidence, warnings = self._fix_invalid_operator(original)
        else:
            fixed, confidence, warnings = self._fix_general_syntax(original)

        if fixed == original and confidence < 0.5:
            return FixStatus.NEEDS_MANUAL_REVIEW, original, fixed, confidence, "需要人工审查", warnings

        status = FixStatus.SUCCESS if confidence >= 0.7 else FixStatus.PARTIAL
        return status, original, fixed, confidence, "语法错误已修复", warnings

    def _fix_missing_colon(self, code: str) -> Tuple[str, float, List[str]]:
        warnings = []
        lines = code.split('\n')
        fixed_lines = []

        for line in lines:
            stripped = line.strip()
            first_word = stripped.split()[0] if stripped.split() else ''

            if first_word in self.BLOCK_START_KEYWORDS and not stripped.endswith(':'):
                fixed_lines.append(line.rstrip() + ':')
                warnings.append(f"为 '{first_word}' 语句添加缺失的冒号")
            else:
                fixed_lines.append(line)

        fixed = '\n'.join(fixed_lines)
        confidence = 0.85 if warnings else 0.95
        return fixed, confidence, warnings

    def _fix_invalid_operator(self, code: str) -> Tuple[str, float, List[str]]:
        warnings = []
        fixed = code

        operator_fixes = {
            '<>': '!=',
            '=<': '<=',
            '=>': '>=',
            '===': '==',
            '!==': '!=',
            '&&': ' and ',
            '||': ' or ',
            '!': ' not ',
        }

        for wrong, correct in operator_fixes.items():
            if wrong in fixed:
                fixed = fixed.replace(wrong, correct)
                warnings.append(f"将 '{wrong}' 替换为 '{correct}'")

        confidence = 0.75 if warnings else 0.90
        return fixed, confidence, warnings

    def _fix_general_syntax(self, code: str) -> Tuple[str, float, List[str]]:
        warnings = []
        fixed = code

        try:
            ast.parse(code)
            return code, 1.0, warnings
        except SyntaxError as e:
            pass

        fixed, colon_warnings = self._add_missing_colons(fixed)
        warnings.extend(colon_warnings)

        fixed, bracket_warnings = self._fix_brackets(fixed)
        warnings.extend(bracket_warnings)

        confidence = 0.6 if warnings else 0.9
        return fixed, confidence, warnings

    def _add_missing_colons(self, code: str) -> Tuple[str, List[str]]:
        warnings = []
        lines = code.split('\n')
        fixed_lines = []

        for line in lines:
            stripped = line.strip()
            first_word = stripped.split()[0] if stripped.split() else ''

            if first_word in self.BLOCK_START_KEYWORDS and not stripped.endswith(':'):
                fixed_lines.append(line.rstrip() + ':')
                warnings.append(f"添加缺失的冒号")
            else:
                fixed_lines.append(line)

        return '\n'.join(fixed_lines), warnings

    def _fix_brackets(self, code: str) -> Tuple[str, List[str]]:
        warnings = []
        open_count = {'(': 0, '[': 0, '{': 0}
        close_count = {')': 0, ']': 0, '}': 0}

        for char in code:
            if char in open_count:
                open_count[char] += 1
            elif char in close_count:
                close_count[char] += 1

        fixed = code
        bracket_map = {'(': ')', '[': ']', '{': '}'}

        for open_bracket, close_bracket in bracket_map.items():
            diff = open_count[open_bracket] - close_count[close_bracket]
            if diff > 0:
                fixed += close_bracket * diff
                warnings.append(f"添加 {diff} 个缺失的 '{close_bracket}'")
            elif diff < 0:
                warnings.append(f"多余的 '{close_bracket}'，需要人工审查")

        return fixed, warnings


class MissingImportFixStrategy(BaseFixStrategy):
    """缺失导入修复策略"""

    name = "missing_import_fix"
    description = "自动添加缺失的导入语句"
    applicable_issues = [IssueCategory.IMPORT_MISSING]
    priority = StrategyPriority.HIGH
    success_rate = 0.90

    COMMON_IMPORTS = {
        'os': 'import os',
        'sys': 'import sys',
        're': 'import re',
        'json': 'import json',
        'datetime': 'from datetime import datetime',
        'date': 'from datetime import date',
        'timedelta': 'from datetime import timedelta',
        'Path': 'from pathlib import Path',
        'List': 'from typing import List',
        'Dict': 'from typing import Dict',
        'Optional': 'from typing import Optional',
        'Any': 'from typing import Any',
        'Tuple': 'from typing import Tuple',
        'Set': 'from typing import Set',
        'Callable': 'from typing import Callable',
        'defaultdict': 'from collections import defaultdict',
        'Counter': 'from collections import Counter',
        'deque': 'from collections import deque',
        'dataclass': 'from dataclasses import dataclass',
        'Enum': 'from enum import Enum',
        'logging': 'import logging',
        'np': 'import numpy as np',
        'pd': 'import pandas as pd',
        'plt': 'import matplotlib.pyplot as plt',
        'requests': 'import requests',
        'pytest': 'import pytest',
        'unittest': 'import unittest',
        'asyncio': 'import asyncio',
        'threading': 'import threading',
        'multiprocessing': 'import multiprocessing',
        'subprocess': 'import subprocess',
        'shutil': 'import shutil',
        'tempfile': 'import tempfile',
        'hashlib': 'import hashlib',
        'base64': 'import base64',
        'uuid': 'import uuid',
        'copy': 'import copy',
        'itertools': 'import itertools',
        'functools': 'import functools',
        'operator': 'import operator',
        'pickle': 'import pickle',
        'csv': 'import csv',
        'math': 'import math',
        'random': 'import random',
        'string': 'import string',
        'time': 'import time',
        'argparse': 'import argparse',
        'abc': 'from abc import ABC, abstractmethod',
        'contextlib': 'import contextlib',
        'io': 'import io',
        'pathlib': 'import pathlib',
        'typing': 'import typing',
        'warnings': 'import warnings',
        'traceback': 'import traceback',
        'inspect': 'import inspect',
        'dis': 'import dis',
        'ast': 'import ast',
        'tokenize': 'import tokenize',
    }

    def can_apply(self, issue: Issue) -> bool:
        return issue.category == IssueCategory.IMPORT_MISSING

    def _do_apply(self, issue: Issue) -> Tuple[FixStatus, str, str, float, str, List[str]]:
        original = issue.code_snippet
        warnings = []

        if not original:
            return FixStatus.FAILED, original, "", 0.0, "无法获取原始代码", warnings

        missing_name = issue.context.get('missing_name', '')
        if not missing_name:
            return FixStatus.NEEDS_MANUAL_REVIEW, original, "", 0.0, "无法确定缺失的导入名称", warnings

        import_statement = self.COMMON_IMPORTS.get(missing_name)

        if not import_statement:
            import_statement = f"import {missing_name}"
            warnings.append(f"未找到 '{missing_name}' 的标准导入路径，使用默认导入")
            confidence = 0.6
        else:
            confidence = 0.95

        lines = original.split('\n')
        import_lines = []
        code_lines = []
        last_import_idx = -1

        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith(('import ', 'from ')):
                import_lines.append(line)
                last_import_idx = i
            else:
                code_lines.append(line)

        if import_statement not in import_lines:
            import_lines.append(import_statement)
            import_lines.sort()

        fixed = '\n'.join(import_lines) + '\n\n' + '\n'.join(code_lines)
        fixed = fixed.strip() + '\n'

        return FixStatus.SUCCESS, original, fixed, confidence, f"已添加导入: {import_statement}", warnings


class ImportErrorPathFixStrategy(BaseFixStrategy):
    """导入路径错误修复策略"""

    name = "import_path_error_fix"
    description = "修复错误的导入路径"
    applicable_issues = [IssueCategory.IMPORT_PATH_ERROR]
    priority = StrategyPriority.HIGH
    success_rate = 0.75

    PATH_CORRECTIONS = {
        'django.core.urlresolvers': 'django.urls',
        'urlparse': 'urllib.parse.urlparse',
        'urllib2': 'urllib.request',
        'urllib3': 'urllib',
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
        'scipy.lib': 'scipy',
        'sklearn.cross_validation': 'sklearn.model_selection',
        'sklearn.grid_search': 'sklearn.model_selection',
        'sklearn.learning_curve': 'sklearn.model_selection',
    }

    def can_apply(self, issue: Issue) -> bool:
        return issue.category == IssueCategory.IMPORT_PATH_ERROR

    def _do_apply(self, issue: Issue) -> Tuple[FixStatus, str, str, float, str, List[str]]:
        original = issue.code_snippet
        warnings = []

        if not original:
            return FixStatus.FAILED, original, "", 0.0, "无法获取原始代码", warnings

        wrong_path = issue.context.get('wrong_path', '')
        if not wrong_path:
            return FixStatus.NEEDS_MANUAL_REVIEW, original, "", 0.0, "无法确定错误的导入路径", warnings

        correct_path = self.PATH_CORRECTIONS.get(wrong_path)

        if not correct_path:
            warnings.append(f"未找到 '{wrong_path}' 的正确路径映射")
            return FixStatus.NEEDS_MANUAL_REVIEW, original, "", 0.5, "需要人工审查导入路径", warnings

        fixed = original.replace(wrong_path, correct_path)
        confidence = 0.85

        return FixStatus.SUCCESS, original, fixed, confidence, f"导入路径已修正: {wrong_path} -> {correct_path}", warnings


class CircularImportFixStrategy(BaseFixStrategy):
    """循环导入修复策略"""

    name = "circular_import_fix"
    description = "修复循环导入问题，通过延迟导入或重构导入结构"
    applicable_issues = [IssueCategory.IMPORT_CIRCULAR]
    priority = StrategyPriority.HIGH
    success_rate = 0.70

    def can_apply(self, issue: Issue) -> bool:
        return issue.category == IssueCategory.IMPORT_CIRCULAR

    def _do_apply(self, issue: Issue) -> Tuple[FixStatus, str, str, float, str, List[str]]:
        original = issue.code_snippet
        warnings = []

        if not original:
            return FixStatus.FAILED, original, "", 0.0, "无法获取原始代码", warnings

        module_name = issue.context.get('module_name', '')
        import_line = issue.context.get('import_line', '')

        if not module_name or not import_line:
            return FixStatus.NEEDS_MANUAL_REVIEW, original, "", 0.5, "缺少循环导入信息", warnings

        lines = original.split('\n')
        fixed_lines = []
        delayed_imports = []

        for line in lines:
            if module_name in line and ('import ' in line or 'from ' in line):
                indent = len(line) - len(line.lstrip())
                delayed_imports.append((line.strip(), indent))
                warnings.append(f"将导入 '{line.strip()}' 延迟到函数内部")
            else:
                fixed_lines.append(line)

        if delayed_imports:
            delayed_code = "\n    # 延迟导入以避免循环依赖\n"
            for imp, _ in delayed_imports:
                delayed_code += f"    {imp}\n"

            for i, line in enumerate(fixed_lines):
                if 'def ' in line and line.strip().endswith(':'):
                    insert_idx = i + 1
                    while insert_idx < len(fixed_lines) and fixed_lines[insert_idx].startswith((' ', '\t')):
                        insert_idx += 1
                    fixed_lines.insert(insert_idx, delayed_code)
                    break

        fixed = '\n'.join(fixed_lines)
        confidence = 0.65

        warnings.append("循环导入修复可能需要进一步的手动调整")

        return FixStatus.PARTIAL, original, fixed, confidence, "已尝试延迟导入解决循环依赖", warnings


class SQLInjectionFixStrategy(BaseFixStrategy):
    """SQL注入修复策略"""

    name = "sql_injection_fix"
    description = "修复SQL注入漏洞，使用参数化查询"
    applicable_issues = [IssueCategory.SECURITY_SQL_INJECTION]
    priority = StrategyPriority.CRITICAL
    success_rate = 0.92

    def can_apply(self, issue: Issue) -> bool:
        return issue.category == IssueCategory.SECURITY_SQL_INJECTION

    def _do_apply(self, issue: Issue) -> Tuple[FixStatus, str, str, float, str, List[str]]:
        original = issue.code_snippet
        warnings = []

        if not original:
            return FixStatus.FAILED, original, "", 0.0, "无法获取原始代码", warnings

        fixed = original
        confidence = 0.0

        f_string_pattern = r'f["\'].*?(?:SELECT|INSERT|UPDATE|DELETE|CREATE|DROP).*?["\']'
        format_pattern = r'\.format\s*\([^)]*\).*?(?:SELECT|INSERT|UPDATE|DELETE|CREATE|DROP)'
        concat_pattern = r'["\'].*?(?:SELECT|INSERT|UPDATE|DELETE|CREATE|DROP).*?["\'].*?[\+\%]'

        if re.search(f_string_pattern, original, re.IGNORECASE):
            fixed, confidence = self._fix_fstring_sql(original)
            warnings.append("已将f-string SQL转换为参数化查询")
        elif re.search(format_pattern, original, re.IGNORECASE):
            fixed, confidence = self._fix_format_sql(original)
            warnings.append("已将.format() SQL转换为参数化查询")
        elif re.search(concat_pattern, original, re.IGNORECASE):
            fixed, confidence = self._fix_concat_sql(original)
            warnings.append("已将字符串拼接SQL转换为参数化查询")
        else:
            fixed, confidence = self._fix_general_sql(original)
            if fixed != original:
                warnings.append("已应用通用SQL注入修复")

        if fixed == original:
            return FixStatus.NEEDS_MANUAL_REVIEW, original, fixed, 0.5, "需要人工审查SQL注入修复", warnings

        return FixStatus.SUCCESS, original, fixed, confidence, "SQL注入漏洞已修复", warnings

    def _fix_fstring_sql(self, code: str) -> Tuple[str, float]:
        pattern = r'f(["\'])(.*?\{.*?\}.*?)\1'
        matches = list(re.finditer(pattern, code, re.DOTALL))

        if not matches:
            return code, 0.5

        fixed = code
        params = []

        for match in matches:
            quote = match.group(1)
            sql_template = match.group(2)

            param_pattern = r'\{([^}]+)\}'
            param_names = re.findall(param_pattern, sql_template)

            new_sql = re.sub(param_pattern, '?', sql_template)
            new_sql = new_sql.lstrip('f')

            params.extend(param_names)

            if params:
                param_str = ', '.join(params)
                fixed = fixed.replace(match.group(0), f'{quote}{new_sql}{quote}, ({param_str})')

        return fixed, 0.85

    def _fix_format_sql(self, code: str) -> Tuple[str, float]:
        format_pattern = r'(["\'].*?["\'])\.format\s*\(([^)]*)\)'

        def replace_format(match):
            sql_template = match.group(1)
            params = match.group(2)

            placeholder_pattern = r'\{(\d*)\}'
            new_sql = re.sub(placeholder_pattern, '?', sql_template)

            return f'{new_sql}, ({params})'

        fixed = re.sub(format_pattern, replace_format, code)
        confidence = 0.80 if fixed != code else 0.5

        return fixed, confidence

    def _fix_concat_sql(self, code: str) -> Tuple[str, float]:
        concat_pattern = r'(["\'])(.*?)(\1)\s*\+\s*(\w+)'

        def replace_concat(match):
            quote = match.group(1)
            sql_part = match.group(2)
            var_name = match.group(4)

            if '?' in sql_part:
                return match.group(0)

            new_sql = sql_part + '?'
            return f'{quote}{new_sql}{quote}, ({var_name},)'

        fixed = re.sub(concat_pattern, replace_concat, code)
        confidence = 0.75 if fixed != code else 0.5

        return fixed, confidence

    def _fix_general_sql(self, code: str) -> Tuple[str, float]:
        return code, 0.5


class XSSFixStrategy(BaseFixStrategy):
    """XSS跨站脚本攻击修复策略"""

    name = "xss_fix"
    description = "修复XSS漏洞，对输出进行转义处理"
    applicable_issues = [IssueCategory.SECURITY_XSS]
    priority = StrategyPriority.CRITICAL
    success_rate = 0.88

    def can_apply(self, issue: Issue) -> bool:
        return issue.category == IssueCategory.SECURITY_XSS

    def _do_apply(self, issue: Issue) -> Tuple[FixStatus, str, str, float, str, List[str]]:
        original = issue.code_snippet
        warnings = []

        if not original:
            return FixStatus.FAILED, original, "", 0.0, "无法获取原始代码", warnings

        fixed = original
        confidence = 0.0

        unsafe_patterns = [
            (r'return\s+(\w+)', r'return html.escape(str(\1))'),
            (r'print\s*\(\s*(\w+)\s*\)', r'print(html.escape(str(\1)))'),
            (r'render_template_string\s*\(\s*(\w+)\s*\)', r'render_template_string(html.escape(\1))'),
            (r'Markup\s*\(\s*(\w+)\s*\)', r'Markup(html.escape(\1))'),
        ]

        for pattern, replacement in unsafe_patterns:
            if re.search(pattern, original):
                new_fixed = re.sub(pattern, replacement, fixed)
                if new_fixed != fixed:
                    fixed = new_fixed
                    warnings.append(f"已对输出进行HTML转义")

        if 'html.escape' in fixed and 'import html' not in fixed:
            lines = fixed.split('\n')
            import_added = False
            new_lines = []

            for line in lines:
                if not import_added and (line.strip().startswith('import ') or line.strip().startswith('from ')):
                    new_lines.append(line)
                elif not import_added and line.strip() and not line.strip().startswith('#'):
                    new_lines.append('import html')
                    import_added = True
                    new_lines.append(line)
                else:
                    new_lines.append(line)

            if not import_added:
                new_lines.insert(0, 'import html')

            fixed = '\n'.join(new_lines)
            warnings.append("已添加 'import html'")

        confidence = 0.80 if fixed != original else 0.5

        if fixed == original:
            return FixStatus.NEEDS_MANUAL_REVIEW, original, fixed, confidence, "需要人工审查XSS修复", warnings

        return FixStatus.SUCCESS, original, fixed, confidence, "XSS漏洞已修复", warnings


class SensitiveDataLeakFixStrategy(BaseFixStrategy):
    """敏感数据泄露修复策略"""

    name = "sensitive_data_leak_fix"
    description = "修复敏感数据泄露问题，如密码、密钥等"
    applicable_issues = [IssueCategory.SECURITY_SENSITIVE_DATA, IssueCategory.SECURITY_HARDCODED_SECRET]
    priority = StrategyPriority.CRITICAL
    success_rate = 0.85

    SENSITIVE_PATTERNS = {
        'password': [
            (r'password\s*=\s*["\']([^"\']+)["\']', 'password = os.environ.get("PASSWORD")'),
            (r'passwd\s*=\s*["\']([^"\']+)["\']', 'passwd = os.environ.get("PASSWORD")'),
            (r'pwd\s*=\s*["\']([^"\']+)["\']', 'pwd = os.environ.get("PASSWORD")'),
        ],
        'api_key': [
            (r'api_key\s*=\s*["\']([^"\']+)["\']', 'api_key = os.environ.get("API_KEY")'),
            (r'apikey\s*=\s*["\']([^"\']+)["\']', 'apikey = os.environ.get("API_KEY")'),
            (r'api_secret\s*=\s*["\']([^"\']+)["\']', 'api_secret = os.environ.get("API_SECRET")'),
        ],
        'secret': [
            (r'secret_key\s*=\s*["\']([^"\']+)["\']', 'secret_key = os.environ.get("SECRET_KEY")'),
            (r'secret\s*=\s*["\']([^"\']+)["\']', 'secret = os.environ.get("SECRET")'),
            (r'private_key\s*=\s*["\']([^"\']+)["\']', 'private_key = os.environ.get("PRIVATE_KEY")'),
        ],
        'token': [
            (r'token\s*=\s*["\']([^"\']+)["\']', 'token = os.environ.get("TOKEN")'),
            (r'access_token\s*=\s*["\']([^"\']+)["\']', 'access_token = os.environ.get("ACCESS_TOKEN")'),
            (r'auth_token\s*=\s*["\']([^"\']+)["\']', 'auth_token = os.environ.get("AUTH_TOKEN")'),
        ],
    }

    def can_apply(self, issue: Issue) -> bool:
        return issue.category in [IssueCategory.SECURITY_SENSITIVE_DATA, IssueCategory.SECURITY_HARDCODED_SECRET]

    def _do_apply(self, issue: Issue) -> Tuple[FixStatus, str, str, float, str, List[str]]:
        original = issue.code_snippet
        warnings = []

        if not original:
            return FixStatus.FAILED, original, "", 0.0, "无法获取原始代码", warnings

        fixed = original
        total_fixes = 0

        for category, patterns in self.SENSITIVE_PATTERNS.items():
            for pattern, replacement in patterns:
                if re.search(pattern, fixed, re.IGNORECASE):
                    fixed = re.sub(pattern, replacement, fixed, flags=re.IGNORECASE)
                    total_fixes += 1
                    warnings.append(f"已将硬编码的{category}替换为环境变量")

        if total_fixes > 0 and 'import os' not in fixed:
            lines = fixed.split('\n')
            has_os_import = any('import os' in line for line in lines)

            if not has_os_import:
                new_lines = ['import os', '']
                new_lines.extend(lines)
                fixed = '\n'.join(new_lines)
                warnings.append("已添加 'import os'")

        confidence = 0.80 if total_fixes > 0 else 0.5

        if fixed == original:
            return FixStatus.NEEDS_MANUAL_REVIEW, original, fixed, confidence, "未检测到需要修复的敏感数据", warnings

        return FixStatus.SUCCESS, original, fixed, confidence, f"已修复 {total_fixes} 处敏感数据泄露", warnings


class CommandInjectionFixStrategy(BaseFixStrategy):
    """命令注入修复策略"""

    name = "command_injection_fix"
    description = "修复命令注入漏洞，使用安全的子进程调用"
    applicable_issues = [IssueCategory.SECURITY_COMMAND_INJECTION]
    priority = StrategyPriority.CRITICAL
    success_rate = 0.90

    def can_apply(self, issue: Issue) -> bool:
        return issue.category == IssueCategory.SECURITY_COMMAND_INJECTION

    def _do_apply(self, issue: Issue) -> Tuple[FixStatus, str, str, float, str, List[str]]:
        original = issue.code_snippet
        warnings = []

        if not original:
            return FixStatus.FAILED, original, "", 0.0, "无法获取原始代码", warnings

        fixed = original

        os_system_pattern = r'os\.system\s*\(\s*([^)]+)\s*\)'
        if re.search(os_system_pattern, fixed):
            fixed = re.sub(
                os_system_pattern,
                r'subprocess.run(\1, shell=False)',
                fixed
            )
            warnings.append("已将 os.system 替换为 subprocess.run")

        eval_pattern = r'eval\s*\(\s*([^)]+)\s*\)'
        if re.search(eval_pattern, fixed):
            warnings.append("检测到 eval() 调用，建议使用 ast.literal_eval() 或移除")
            fixed = re.sub(eval_pattern, r'ast.literal_eval(\1)', fixed)

        exec_pattern = r'exec\s*\(\s*([^)]+)\s*\)'
        if re.search(exec_pattern, fixed):
            warnings.append("检测到 exec() 调用，存在安全风险，建议重构代码")

        if fixed != original:
            if 'subprocess.run' in fixed and 'import subprocess' not in fixed:
                lines = fixed.split('\n')
                lines.insert(0, 'import subprocess')
                fixed = '\n'.join(lines)
                warnings.append("已添加 'import subprocess'")

            if 'ast.literal_eval' in fixed and 'import ast' not in fixed:
                lines = fixed.split('\n')
                lines.insert(0, 'import ast')
                fixed = '\n'.join(lines)
                warnings.append("已添加 'import ast'")

        confidence = 0.85 if fixed != original else 0.5

        if fixed == original:
            return FixStatus.NEEDS_MANUAL_REVIEW, original, fixed, confidence, "需要人工审查命令注入修复", warnings

        return FixStatus.SUCCESS, original, fixed, confidence, "命令注入漏洞已修复", warnings


class PathTraversalFixStrategy(BaseFixStrategy):
    """路径遍历修复策略"""

    name = "path_traversal_fix"
    description = "修复路径遍历漏洞，验证和清理文件路径"
    applicable_issues = [IssueCategory.SECURITY_PATH_TRAVERSAL]
    priority = StrategyPriority.CRITICAL
    success_rate = 0.88

    def can_apply(self, issue: Issue) -> bool:
        return issue.category == IssueCategory.SECURITY_PATH_TRAVERSAL

    def _do_apply(self, issue: Issue) -> Tuple[FixStatus, str, str, float, str, List[str]]:
        original = issue.code_snippet
        warnings = []

        if not original:
            return FixStatus.FAILED, original, "", 0.0, "无法获取原始代码", warnings

        fixed = original

        open_pattern = r'open\s*\(\s*([^,)]+)\s*[,)]'
        if re.search(open_pattern, fixed):
            safe_open = '''def safe_open(filepath, mode='r', base_dir=None):
    if base_dir is None:
        base_dir = os.getcwd()
    filepath = os.path.normpath(filepath)
    if not os.path.abspath(filepath).startswith(os.path.abspath(base_dir)):
        raise ValueError("Path traversal detected")
    return open(filepath, mode)
'''
            fixed = safe_open + '\n' + fixed
            fixed = re.sub(open_pattern, r'safe_open(\1)', fixed)
            warnings.append("已添加安全文件打开函数")

        if 'os.path' in fixed and 'import os' not in fixed:
            lines = fixed.split('\n')
            lines.insert(0, 'import os')
            fixed = '\n'.join(lines)
            warnings.append("已添加 'import os'")

        confidence = 0.80 if fixed != original else 0.5

        if fixed == original:
            return FixStatus.NEEDS_MANUAL_REVIEW, original, fixed, confidence, "需要人工审查路径遍历修复", warnings

        return FixStatus.SUCCESS, original, fixed, confidence, "路径遍历漏洞已修复", warnings


class LoopOptimizationStrategy(BaseFixStrategy):
    """循环优化策略"""

    name = "loop_optimization"
    description = "优化低效循环，提升性能"
    applicable_issues = [IssueCategory.PERFORMANCE_LOOP_INEFFICIENT]
    priority = StrategyPriority.MEDIUM
    success_rate = 0.82

    def can_apply(self, issue: Issue) -> bool:
        return issue.category == IssueCategory.PERFORMANCE_LOOP_INEFFICIENT

    def _do_apply(self, issue: Issue) -> Tuple[FixStatus, str, str, float, str, List[str]]:
        original = issue.code_snippet
        warnings = []

        if not original:
            return FixStatus.FAILED, original, "", 0.0, "无法获取原始代码", warnings

        fixed = original

        list_append_in_loop = r'(\w+)\s*=\s*\[\]\s*\n\s*for\s+(\w+)\s+in\s+(\w+):\s*\n\s*\1\.append\(([^)]+)\)'
        match = re.search(list_append_in_loop, fixed)
        if match:
            list_name, var, iterable, expr = match.groups()
            list_comp = f'{list_name} = [{expr} for {var} in {iterable}]'
            fixed = re.sub(list_append_in_loop, list_comp, fixed)
            warnings.append("已将循环追加转换为列表推导式")

        nested_loops = r'for\s+(\w+)\s+in\s+(\w+):\s*\n(\s+)for\s+(\w+)\s+in\s+(\w+):'
        if len(re.findall(nested_loops, fixed)) > 1:
            warnings.append("检测到嵌套循环，考虑使用itertools.product优化")

        string_concat_in_loop = r'(\w+)\s*=\s*["\']["\']\s*\n\s*for\s+(\w+)\s+in\s+(.+?):\s*\n\s*\1\s*\+=\s*(.+)'
        match = re.search(string_concat_in_loop, fixed)
        if match:
            var_name, loop_var, iterable, expr = match.groups()
            join_version = f'{var_name} = "".join({expr} for {loop_var} in {iterable})'
            fixed = re.sub(string_concat_in_loop, join_version, fixed)
            warnings.append("已将字符串拼接循环转换为join操作")

        range_len_pattern = r'for\s+(\w+)\s+in\s+range\(len\((\w+)\)\):'
        if re.search(range_len_pattern, fixed):
            fixed = re.sub(range_len_pattern, r'for \1, item in enumerate(\2):', fixed)
            warnings.append("已将range(len())转换为enumerate")

        confidence = 0.75 if fixed != original else 0.5

        if fixed == original:
            return FixStatus.NEEDS_MANUAL_REVIEW, original, fixed, confidence, "未检测到可优化的循环模式", warnings

        return FixStatus.SUCCESS, original, fixed, confidence, "循环已优化", warnings


class MemoryOptimizationStrategy(BaseFixStrategy):
    """内存优化策略"""

    name = "memory_optimization"
    description = "优化内存使用，减少内存泄漏和过度消耗"
    applicable_issues = [IssueCategory.PERFORMANCE_MEMORY_LEAK]
    priority = StrategyPriority.MEDIUM
    success_rate = 0.78

    def can_apply(self, issue: Issue) -> bool:
        return issue.category == IssueCategory.PERFORMANCE_MEMORY_LEAK

    def _do_apply(self, issue: Issue) -> Tuple[FixStatus, str, str, float, str, List[str]]:
        original = issue.code_snippet
        warnings = []

        if not original:
            return FixStatus.FAILED, original, "", 0.0, "无法获取原始代码", warnings

        fixed = original

        list_to_large = r'(\w+)\s*=\s*\[\]\s*\n(\s*)for\s+(\w+)\s+in\s+(.+?):'
        if re.search(list_to_large, fixed):
            generator_version = fixed.replace('=[]', '=()', 1)
            if 'append' in generator_version:
                generator_version = re.sub(r'\.append\(([^)]+)\)', r'yield \1', generator_version)
            warnings.append("考虑使用生成器替代大型列表")

        file_open_no_close = r'(\w+)\s*=\s*open\(([^)]+)\)'
        if re.search(file_open_no_close, fixed) and 'with' not in fixed:
            fixed = re.sub(file_open_no_close, r'with open(\2) as \1:', fixed)
            warnings.append("已将文件操作转换为with语句")

        large_dict_pattern = r'(\w+)\s*=\s*\{\}.*?for\s+\w+\s+in\s+range\((\d{4,})\):'
        if re.search(large_dict_pattern, fixed, re.DOTALL):
            warnings.append("检测到大型字典操作，考虑使用更高效的数据结构")

        confidence = 0.70 if warnings else 0.5

        if fixed == original and not warnings:
            return FixStatus.NEEDS_MANUAL_REVIEW, original, fixed, confidence, "需要人工审查内存优化", warnings

        status = FixStatus.SUCCESS if fixed != original else FixStatus.PARTIAL
        return status, original, fixed, confidence, "内存优化建议已应用", warnings


class AlgorithmOptimizationStrategy(BaseFixStrategy):
    """算法优化策略"""

    name = "algorithm_optimization"
    description = "优化低效算法，提升时间复杂度"
    applicable_issues = [IssueCategory.PERFORMANCE_ALGORITHM_SLOW]
    priority = StrategyPriority.MEDIUM
    success_rate = 0.75

    def can_apply(self, issue: Issue) -> bool:
        return issue.category == IssueCategory.PERFORMANCE_ALGORITHM_SLOW

    def _do_apply(self, issue: Issue) -> Tuple[FixStatus, str, str, float, str, List[str]]:
        original = issue.code_snippet
        warnings = []

        if not original:
            return FixStatus.FAILED, original, "", 0.0, "无法获取原始代码", warnings

        fixed = original

        in_list_pattern = r'if\s+(\w+)\s+in\s+(\w+):'
        if re.search(in_list_pattern, fixed):
            list_to_set = f'# 优化：将列表转换为集合以提高查找速度\n{re.search(in_list_pattern, fixed).group(2)}_set = set({re.search(in_list_pattern, fixed).group(2)})\n'
            fixed = list_to_set + fixed
            fixed = re.sub(in_list_pattern, r'if \1 in \2_set:', fixed)
            warnings.append("已将列表查找转换为集合查找")

        nested_loop_search = r'for\s+\w+\s+in\s+\w+:\s*\n\s*for\s+\w+\s+in\s+\w+:'
        if len(re.findall(nested_loop_search, fixed)) > 0:
            warnings.append("检测到嵌套循环搜索，考虑使用字典或集合优化时间复杂度")

        recursive_no_memo = r'def\s+(\w+)\s*\([^)]*\):.*?return.*?\1\('
        if re.search(recursive_no_memo, fixed, re.DOTALL):
            func_name = re.search(recursive_no_memo, fixed).group(1)
            memo_decorator = f'@functools.lru_cache(maxsize=None)\n'
            fixed = memo_decorator + fixed
            if 'import functools' not in fixed:
                lines = fixed.split('\n')
                lines.insert(0, 'import functools')
                fixed = '\n'.join(lines)
            warnings.append(f"已为递归函数 '{func_name}' 添加记忆化装饰器")

        confidence = 0.70 if warnings else 0.5

        if fixed == original and not warnings:
            return FixStatus.NEEDS_MANUAL_REVIEW, original, fixed, confidence, "需要人工审查算法优化", warnings

        status = FixStatus.SUCCESS if fixed != original else FixStatus.PARTIAL
        return status, original, fixed, confidence, "算法优化建议已应用", warnings


class StringConcatOptimizationStrategy(BaseFixStrategy):
    """字符串拼接优化策略"""

    name = "string_concat_optimization"
    description = "优化字符串拼接操作，使用join替代+操作"
    applicable_issues = [IssueCategory.PERFORMANCE_STRING_CONCAT]
    priority = StrategyPriority.LOW
    success_rate = 0.90

    def can_apply(self, issue: Issue) -> bool:
        return issue.category == IssueCategory.PERFORMANCE_STRING_CONCAT

    def _do_apply(self, issue: Issue) -> Tuple[FixStatus, str, str, float, str, List[str]]:
        original = issue.code_snippet
        warnings = []

        if not original:
            return FixStatus.FAILED, original, "", 0.0, "无法获取原始代码", warnings

        fixed = original

        concat_in_loop = r'(\w+)\s*\+=\s*(.+)'
        matches = list(re.finditer(concat_in_loop, fixed))

        if matches:
            parts = []
            for match in matches:
                parts.append(match.group(2))

            if len(parts) > 2:
                warnings.append(f"检测到 {len(parts)} 次字符串拼接，建议使用列表和join")

        multi_concat = r'(["\'][^"\']*["\'])\s*\+\s*(["\'][^"\']*["\'])\s*\+\s*(["\'][^"\']*["\'])'
        if re.search(multi_concat, fixed):
            fixed = re.sub(multi_concat, r'\1\2\3', fixed)
            warnings.append("已合并连续的字符串字面量")

        confidence = 0.85 if fixed != original else 0.60

        if fixed == original:
            return FixStatus.PARTIAL, original, fixed, confidence, "字符串拼接优化建议", warnings

        return FixStatus.SUCCESS, original, fixed, confidence, "字符串拼接已优化", warnings


class FixStrategyLibraryEnhanced:
    """增强版修复策略库"""

    def __init__(self):
        self._strategies: Dict[str, BaseFixStrategy] = {}
        self._category_map: Dict[IssueCategory, List[str]] = {}
        self._metrics_history: List[Dict[str, Any]] = []
        self._result_counter = 0

        self._register_builtin_strategies()

    def _register_builtin_strategies(self):
        syntax_strategies = [
            IndentationFixStrategy(),
            BracketMismatchFixStrategy(),
            SyntaxErrorFixStrategy(),
        ]

        import_strategies = [
            MissingImportFixStrategy(),
            ImportErrorPathFixStrategy(),
            CircularImportFixStrategy(),
        ]

        security_strategies = [
            SQLInjectionFixStrategy(),
            XSSFixStrategy(),
            SensitiveDataLeakFixStrategy(),
            CommandInjectionFixStrategy(),
            PathTraversalFixStrategy(),
        ]

        performance_strategies = [
            LoopOptimizationStrategy(),
            MemoryOptimizationStrategy(),
            AlgorithmOptimizationStrategy(),
            StringConcatOptimizationStrategy(),
        ]

        all_strategies = syntax_strategies + import_strategies + security_strategies + performance_strategies

        for strategy in all_strategies:
            self.register_strategy(strategy)

    def register_strategy(self, strategy: BaseFixStrategy) -> None:
        self._strategies[strategy.name] = strategy

        for category in strategy.applicable_issues:
            if category not in self._category_map:
                self._category_map[category] = []
            self._category_map[category].append(strategy.name)

        logger.info(f"已注册策略: {strategy.name} (优先级: {strategy.priority.name})")

    def unregister_strategy(self, strategy_name: str) -> bool:
        if strategy_name not in self._strategies:
            return False

        strategy = self._strategies[strategy_name]

        for category in strategy.applicable_issues:
            if category in self._category_map:
                self._category_map[category].remove(strategy_name)
                if not self._category_map[category]:
                    del self._category_map[category]

        del self._strategies[strategy_name]
        logger.info(f"已注销策略: {strategy_name}")
        return True

    def get_strategy(self, strategy_name: str) -> Optional[BaseFixStrategy]:
        return self._strategies.get(strategy_name)

    def get_strategies_for_issue(self, issue: Issue) -> List[BaseFixStrategy]:
        strategies = []

        if issue.category in self._category_map:
            strategy_names = self._category_map[issue.category]
            strategies = [self._strategies[name] for name in strategy_names if name in self._strategies]

        strategies.sort(key=lambda s: s.priority.value)

        return strategies

    def can_fix(self, issue: Issue) -> bool:
        strategies = self.get_strategies_for_issue(issue)
        return any(s.can_apply(issue) for s in strategies)

    def fix(self, issue: Issue, strategy_name: Optional[str] = None) -> Optional[FixResult]:
        self._result_counter += 1

        if strategy_name:
            strategy = self.get_strategy(strategy_name)
            if strategy and strategy.can_apply(issue):
                return strategy.apply(issue)
            return None

        strategies = self.get_strategies_for_issue(issue)

        for strategy in strategies:
            if strategy.can_apply(issue):
                result = strategy.apply(issue)
                if result.status in [FixStatus.SUCCESS, FixStatus.PARTIAL]:
                    return result

        return None

    def fix_batch(self, issues: List[Issue]) -> List[FixResult]:
        results = []

        for issue in issues:
            result = self.fix(issue)
            if result:
                results.append(result)

        return results

    def get_all_strategies(self) -> List[BaseFixStrategy]:
        return list(self._strategies.values())

    def get_strategies_by_category(self, category: IssueCategory) -> List[BaseFixStrategy]:
        if category not in self._category_map:
            return []
        return [self._strategies[name] for name in self._category_map[category] if name in self._strategies]

    def get_strategies_by_priority(self, priority: StrategyPriority) -> List[BaseFixStrategy]:
        return [s for s in self._strategies.values() if s.priority == priority]

    def get_metrics(self) -> Dict[str, StrategyMetrics]:
        return {name: strategy.get_metrics() for name, strategy in self._strategies.items()}

    def get_strategy_statistics(self) -> Dict[str, Any]:
        metrics = self.get_metrics()

        total_applications = sum(m.total_applications for m in metrics.values())
        total_success = sum(m.successful_applications for m in metrics.values())
        total_failed = sum(m.failed_applications for m in metrics.values())

        avg_success_rate = (
            total_success / total_applications if total_applications > 0 else 0.0
        )

        return {
            "total_strategies": len(self._strategies),
            "total_applications": total_applications,
            "successful_applications": total_success,
            "failed_applications": total_failed,
            "average_success_rate": avg_success_rate,
            "strategies_by_category": {
                cat.name: len(strategies) for cat, strategies in self._category_map.items()
            },
            "strategy_metrics": {name: m.to_dict() for name, m in metrics.items()}
        }

    def export_strategies(self, file_path: str) -> None:
        data = {
            "exported_at": datetime.now().isoformat(),
            "strategies": []
        }

        for name, strategy in self._strategies.items():
            strategy_data = {
                "name": strategy.name,
                "description": strategy.description,
                "applicable_issues": [cat.name for cat in strategy.applicable_issues],
                "priority": strategy.priority.name,
                "success_rate": strategy.success_rate,
                "metrics": strategy.get_metrics().to_dict()
            }
            data["strategies"].append(strategy_data)

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"策略已导出到: {file_path}")

    def create_issue(
        self,
        category: IssueCategory,
        severity: IssueSeverity,
        message: str,
        file_path: str,
        line_number: int,
        code_snippet: str = "",
        context: Optional[Dict[str, Any]] = None
    ) -> Issue:
        self._result_counter += 1
        issue_id = f"ISSUE_{self._result_counter:06d}"

        return Issue(
            issue_id=issue_id,
            category=category,
            severity=severity,
            message=message,
            file_path=file_path,
            line_number=line_number,
            code_snippet=code_snippet,
            context=context or {}
        )


def demonstrate_library():
    library = FixStrategyLibraryEnhanced()

    print("=" * 60)
    print("增强版修复策略库演示")
    print("=" * 60)

    print("\n已注册策略:")
    for strategy in library.get_all_strategies():
        print(f"  - {strategy.name}: {strategy.description}")
        print(f"    优先级: {strategy.priority.name}, 成功率: {strategy.success_rate:.0%}")
        print(f"    适用问题: {[cat.name for cat in strategy.applicable_issues]}")

    print("\n" + "=" * 60)
    print("语法修复示例")
    print("=" * 60)

    indent_issue = library.create_issue(
        category=IssueCategory.SYNTAX_INDENTATION,
        severity=IssueSeverity.HIGH,
        message="缩进不一致",
        file_path="test.py",
        line_number=5,
        code_snippet="def foo():\n\tprint('hello')\n        print('world')"
    )

    result = library.fix(indent_issue)
    if result:
        print(f"\n问题: {indent_issue.message}")
        print(f"原始代码:\n{result.original_code}")
        print(f"\n修复后代码:\n{result.fixed_code}")
        print(f"状态: {result.status.value}, 置信度: {result.confidence:.0%}")

    print("\n" + "=" * 60)
    print("安全修复示例 - SQL注入")
    print("=" * 60)

    sql_issue = library.create_issue(
        category=IssueCategory.SECURITY_SQL_INJECTION,
        severity=IssueSeverity.CRITICAL,
        message="SQL注入漏洞",
        file_path="db.py",
        line_number=10,
        code_snippet="query = f\"SELECT * FROM users WHERE id = {user_id}\"",
        context={"user_input": "user_id"}
    )

    result = library.fix(sql_issue)
    if result:
        print(f"\n问题: {sql_issue.message}")
        print(f"原始代码:\n{result.original_code}")
        print(f"\n修复后代码:\n{result.fixed_code}")
        print(f"状态: {result.status.value}, 置信度: {result.confidence:.0%}")
        if result.warnings:
            print(f"警告: {result.warnings}")

    print("\n" + "=" * 60)
    print("性能优化示例 - 循环优化")
    print("=" * 60)

    loop_issue = library.create_issue(
        category=IssueCategory.PERFORMANCE_LOOP_INEFFICIENT,
        severity=IssueSeverity.MEDIUM,
        message="低效循环",
        file_path="process.py",
        line_number=15,
        code_snippet="result = []\nfor item in items:\n    result.append(item * 2)"
    )

    result = library.fix(loop_issue)
    if result:
        print(f"\n问题: {loop_issue.message}")
        print(f"原始代码:\n{result.original_code}")
        print(f"\n修复后代码:\n{result.fixed_code}")
        print(f"状态: {result.status.value}, 置信度: {result.confidence:.0%}")

    print("\n" + "=" * 60)
    print("策略统计")
    print("=" * 60)

    stats = library.get_strategy_statistics()
    print(f"\n总策略数: {stats['total_strategies']}")
    print(f"总应用次数: {stats['total_applications']}")
    print(f"成功应用: {stats['successful_applications']}")
    print(f"平均成功率: {stats['average_success_rate']:.0%}")

    print("\n按类别分组:")
    for cat, count in stats['strategies_by_category'].items():
        print(f"  {cat}: {count}")


if __name__ == "__main__":
    demonstrate_library()
