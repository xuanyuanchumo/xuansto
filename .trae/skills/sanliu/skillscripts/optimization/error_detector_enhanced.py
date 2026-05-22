#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版错误检测器 - Error Detector Enhanced

全面的错误检测系统，包括：
- 语法错误检测（Syntax Error Detection）
- 运行时错误检测（Runtime Error Detection）
- 逻辑错误检测（Logic Error Detection）
- 安全漏洞检测（Security Vulnerability Detection）
- 性能问题检测（Performance Issue Detection）
- 代码异味检测（Code Smell Detection）

使用示例:
    python error_detector_enhanced.py --file code.py --detect-all
    python error_detector_enhanced.py --file code.py --detect-syntax
    python error_detector_enhanced.py --file code.py --detect-security
    python error_detector_enhanced.py --dir ./src --detect-all --report report.json
"""

from __future__ import annotations

import ast
import json
import logging
import os
import re
import sys
import tokenize
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from io import StringIO
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ErrorCategory(Enum):
    SYNTAX = auto()
    RUNTIME = auto()
    LOGIC = auto()
    SECURITY = auto()
    PERFORMANCE = auto()
    CODE_SMELL = auto()
    STYLE = auto()
    DEPRECATION = auto()


class ErrorSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class DetectionStatus(Enum):
    DETECTED = "detected"
    NOT_DETECTED = "not_detected"
    ERROR = "error"
    SKIPPED = "skipped"


@dataclass
class DetectedError:
    error_id: str
    category: ErrorCategory
    severity: ErrorSeverity
    error_type: str
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
    related_errors: List[str] = field(default_factory=list)
    cwe_id: str = ""
    owasp_category: str = ""
    detected_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error_id": self.error_id,
            "category": self.category.name,
            "severity": self.severity.value,
            "error_type": self.error_type,
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
            "related_errors": self.related_errors,
            "cwe_id": self.cwe_id,
            "owasp_category": self.owasp_category,
            "detected_at": self.detected_at
        }


@dataclass
class DetectionResult:
    result_id: str
    file_path: str
    status: DetectionStatus
    errors: List[DetectedError]
    detection_time_ms: float
    detector_name: str
    summary: Dict[str, int] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "result_id": self.result_id,
            "file_path": self.file_path,
            "status": self.status.value,
            "errors": [e.to_dict() for e in self.errors],
            "detection_time_ms": self.detection_time_ms,
            "detector_name": self.detector_name,
            "summary": self.summary,
            "metadata": self.metadata
        }


@dataclass
class DetectionReport:
    report_id: str
    generated_at: str
    total_files: int
    total_errors: int
    results: List[DetectionResult]
    summary_by_category: Dict[str, int] = field(default_factory=dict)
    summary_by_severity: Dict[str, int] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "generated_at": self.generated_at,
            "total_files": self.total_files,
            "total_errors": self.total_errors,
            "results": [r.to_dict() for r in self.results],
            "summary_by_category": self.summary_by_category,
            "summary_by_severity": self.summary_by_severity,
            "recommendations": self.recommendations
        }


class BaseDetector(ABC):
    """检测器基类"""

    name: str = "base_detector"
    description: str = "基础检测器"
    category: ErrorCategory = ErrorCategory.SYNTAX

    def __init__(self):
        self._error_counter = 0
        self._result_counter = 0

    @abstractmethod
    def detect(self, content: str, file_path: str) -> DetectionResult:
        pass

    def _create_error(
        self,
        error_type: str,
        severity: ErrorSeverity,
        message: str,
        file_path: str,
        line_number: int,
        code_snippet: str = "",
        suggestion: str = "",
        confidence: float = 1.0,
        context: Optional[Dict[str, Any]] = None,
        cwe_id: str = "",
        owasp_category: str = ""
    ) -> DetectedError:
        self._error_counter += 1
        return DetectedError(
            error_id=f"ERR_{self._error_counter:06d}",
            category=self.category,
            severity=severity,
            error_type=error_type,
            message=message,
            file_path=file_path,
            line_number=line_number,
            code_snippet=code_snippet,
            suggestion=suggestion,
            confidence=confidence,
            context=context or {},
            cwe_id=cwe_id,
            owasp_category=owasp_category
        )

    def _create_result(
        self,
        file_path: str,
        status: DetectionStatus,
        errors: List[DetectedError],
        detection_time_ms: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> DetectionResult:
        self._result_counter += 1
        summary = defaultdict(int)
        for error in errors:
            summary[error.severity.value] += 1
            summary[error.category.name] += 1

        return DetectionResult(
            result_id=f"DET_{self._result_counter:06d}",
            file_path=file_path,
            status=status,
            errors=errors,
            detection_time_ms=detection_time_ms,
            detector_name=self.name,
            summary=dict(summary),
            metadata=metadata or {}
        )

    def _get_line_content(self, content: str, line_number: int) -> str:
        lines = content.split('\n')
        if 1 <= line_number <= len(lines):
            return lines[line_number - 1]
        return ""

    def _get_code_snippet(self, content: str, line_number: int, context_lines: int = 3) -> str:
        lines = content.split('\n')
        start = max(0, line_number - context_lines - 1)
        end = min(len(lines), line_number + context_lines)
        return '\n'.join(lines[start:end])


class SyntaxErrorDetector(BaseDetector):
    """语法错误检测器"""

    name = "syntax_error_detector"
    description = "检测Python语法错误"
    category = ErrorCategory.SYNTAX

    def detect(self, content: str, file_path: str) -> DetectionResult:
        import time
        start_time = time.perf_counter()
        errors = []

        errors.extend(self._detect_syntax_errors(content, file_path))
        errors.extend(self._detect_indentation_errors(content, file_path))
        errors.extend(self._detect_bracket_mismatch(content, file_path))
        errors.extend(self._detect_missing_colon(content, file_path))
        errors.extend(self._detect_invalid_operators(content, file_path))
        errors.extend(self._detect_invalid_escape(content, file_path))
        errors.extend(self._detect_missing_quote(content, file_path))

        detection_time = (time.perf_counter() - start_time) * 1000
        status = DetectionStatus.DETECTED if errors else DetectionStatus.NOT_DETECTED

        return self._create_result(file_path, status, errors, detection_time)

    def _detect_syntax_errors(self, content: str, file_path: str) -> List[DetectedError]:
        errors = []
        try:
            ast.parse(content)
        except SyntaxError as e:
            line_num = e.lineno or 1
            errors.append(self._create_error(
                error_type="syntax_error",
                severity=ErrorSeverity.CRITICAL,
                message=f"语法错误: {e.msg}",
                file_path=file_path,
                line_number=line_num,
                code_snippet=self._get_line_content(content, line_num),
                suggestion=self._suggest_syntax_fix(e.msg),
                context={"offset": e.offset, "text": e.text}
            ))
        return errors

    def _detect_indentation_errors(self, content: str, file_path: str) -> List[DetectedError]:
        errors = []
        lines = content.split('\n')
        prev_indent = 0
        indent_stack = [0]

        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue

            current_indent = len(line) - len(line.lstrip())

            if '\t' in line and ' ' in line[:current_indent]:
                errors.append(self._create_error(
                    error_type="mixed_indentation",
                    severity=ErrorSeverity.HIGH,
                    message="混合使用制表符和空格进行缩进",
                    file_path=file_path,
                    line_number=i,
                    code_snippet=line,
                    suggestion="统一使用4个空格进行缩进"
                ))

            if current_indent > prev_indent:
                expected = prev_indent + 4
                if current_indent != expected and current_indent % 4 != 0:
                    errors.append(self._create_error(
                        error_type="inconsistent_indentation",
                        severity=ErrorSeverity.HIGH,
                        message=f"缩进不一致，期望 {expected} 空格，实际 {current_indent} 空格",
                        file_path=file_path,
                        line_number=i,
                        code_snippet=line,
                        suggestion="使用4个空格作为缩进单位"
                    ))
                indent_stack.append(current_indent)
            elif current_indent < prev_indent:
                if current_indent not in indent_stack:
                    errors.append(self._create_error(
                        error_type="unindent_not_matching",
                        severity=ErrorSeverity.HIGH,
                        message="缩进级别与之前不匹配",
                        file_path=file_path,
                        line_number=i,
                        code_snippet=line,
                        suggestion="确保缩进与代码块开始处对齐"
                    ))
                while indent_stack and indent_stack[-1] > current_indent:
                    indent_stack.pop()

            prev_indent = current_indent

        return errors

    def _detect_bracket_mismatch(self, content: str, file_path: str) -> List[DetectedError]:
        errors = []
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
                continue

            if in_string:
                continue

            if char in bracket_pairs:
                stack.append((char, i))
            elif char in bracket_pairs.values():
                if not stack:
                    line_num = content[:i].count('\n') + 1
                    errors.append(self._create_error(
                        error_type="unmatched_closing_bracket",
                        severity=ErrorSeverity.CRITICAL,
                        message=f"未匹配的右括号 '{char}'",
                        file_path=file_path,
                        line_number=line_num,
                        suggestion=f"检查是否缺少对应的左括号"
                    ))
                else:
                    expected_open = [k for k, v in bracket_pairs.items() if v == char][0]
                    if stack[-1][0] != expected_open:
                        line_num = content[:i].count('\n') + 1
                        errors.append(self._create_error(
                            error_type="mismatched_bracket",
                            severity=ErrorSeverity.CRITICAL,
                            message=f"括号类型不匹配，期望 '{bracket_pairs[stack[-1][0]]}'，实际 '{char}'",
                            file_path=file_path,
                            line_number=line_num,
                            suggestion="检查括号类型是否正确"
                        ))
                    else:
                        stack.pop()

        for bracket, pos in stack:
            line_num = content[:pos].count('\n') + 1
            errors.append(self._create_error(
                error_type="unmatched_opening_bracket",
                severity=ErrorSeverity.CRITICAL,
                message=f"未匹配的左括号 '{bracket}'",
                file_path=file_path,
                line_number=line_num,
                suggestion=f"添加对应的右括号 '{bracket_pairs[bracket]}'"
            ))

        return errors

    def _detect_missing_colon(self, content: str, file_path: str) -> List[DetectedError]:
        errors = []
        lines = content.split('\n')
        keywords = ['if', 'elif', 'else', 'for', 'while', 'def', 'class', 'try', 'except', 'finally', 'with', 'match', 'case']

        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith('#'):
                continue

            for kw in keywords:
                pattern = rf'^{kw}\b'
                if re.match(pattern, stripped):
                    if not stripped.endswith(':'):
                        if kw == 'else':
                            if re.match(r'^else\s+if\b', stripped):
                                continue
                        errors.append(self._create_error(
                            error_type="missing_colon",
                            severity=ErrorSeverity.HIGH,
                            message=f"'{kw}' 语句末尾缺少冒号",
                            file_path=file_path,
                            line_number=i,
                            code_snippet=line,
                            suggestion=f"在语句末尾添加 ':'"
                        ))
                    break

        return errors

    def _detect_invalid_operators(self, content: str, file_path: str) -> List[DetectedError]:
        errors = []
        lines = content.split('\n')

        invalid_ops = [
            (r'<>', '!=', 'Python 3 不支持 <> 运算符'),
            (r'=<', '<=', '赋值和比较运算符顺序错误'),
            (r'=>', '>=', '赋值和比较运算符顺序错误'),
            (r'===', '==', 'Python 不支持 === 运算符'),
            (r'!==', '!=', 'Python 不支持 !== 运算符'),
        ]

        for i, line in enumerate(lines, 1):
            for wrong, correct, msg in invalid_ops:
                if wrong in line:
                    errors.append(self._create_error(
                        error_type="invalid_operator",
                        severity=ErrorSeverity.HIGH,
                        message=msg,
                        file_path=file_path,
                        line_number=i,
                        code_snippet=line,
                        suggestion=f"将 '{wrong}' 替换为 '{correct}'"
                    ))

        return errors

    def _detect_invalid_escape(self, content: str, file_path: str) -> List[DetectedError]:
        errors = []
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            matches = re.finditer(r'(?<!\\)(?:\\\\)*\\([^\\\'\"abfnrtv0-7xNuU])', line)
            for match in matches:
                errors.append(self._create_error(
                    error_type="invalid_escape_sequence",
                    severity=ErrorSeverity.MEDIUM,
                    message=f"无效的转义序列 '\\{match.group(1)}'",
                    file_path=file_path,
                    line_number=i,
                    code_snippet=line,
                    suggestion="使用原始字符串(r'')或双重转义('\\\\')"
                ))

        return errors

    def _detect_missing_quote(self, content: str, file_path: str) -> List[DetectedError]:
        errors = []
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith('#'):
                continue

            for quote in ['"', "'"]:
                count = line.count(quote) - line.count(f'\\{quote}')
                if count % 2 != 0:
                    triple = quote * 3
                    if triple in content:
                        continue
                    errors.append(self._create_error(
                        error_type="unmatched_quote",
                        severity=ErrorSeverity.HIGH,
                        message=f"未匹配的引号 '{quote}'",
                        file_path=file_path,
                        line_number=i,
                        code_snippet=line,
                        suggestion="检查引号是否成对出现"
                    ))
                    break

        return errors

    def _suggest_syntax_fix(self, error_msg: str) -> str:
        suggestions = {
            "invalid syntax": "检查语法结构，确保关键字和符号使用正确",
            "unexpected EOF while parsing": "检查代码是否完整，可能缺少括号或引号",
            "unterminated string literal": "确保字符串有闭合的引号",
            "EOL while scanning string literal": "字符串跨越多行，使用三引号或续行符",
            "unexpected indent": "检查缩进是否正确",
            "expected an indented block": "在冒号后添加缩进的代码块",
            "unindent does not match any outer indentation level": "缩进级别不一致，统一使用空格",
        }
        return suggestions.get(error_msg, "检查语法错误")


class RuntimeErrorDetector(BaseDetector):
    """运行时错误检测器"""

    name = "runtime_error_detector"
    description = "检测潜在的运行时错误"
    category = ErrorCategory.RUNTIME

    def detect(self, content: str, file_path: str) -> DetectionResult:
        import time
        start_time = time.perf_counter()
        errors = []

        try:
            tree = ast.parse(content)
            errors.extend(self._detect_undefined_variables(tree, content, file_path))
            errors.extend(self._detect_type_errors(tree, content, file_path))
            errors.extend(self._detect_index_errors(tree, content, file_path))
            errors.extend(self._detect_key_errors(tree, content, file_path))
            errors.extend(self._detect_attribute_errors(tree, content, file_path))
            errors.extend(self._detect_zero_division(tree, content, file_path))
            errors.extend(self._detect_recursion_issues(tree, content, file_path))
        except SyntaxError:
            pass

        detection_time = (time.perf_counter() - start_time) * 1000
        status = DetectionStatus.DETECTED if errors else DetectionStatus.NOT_DETECTED

        return self._create_result(file_path, status, errors, detection_time)

    def _detect_undefined_variables(self, tree: ast.AST, content: str, file_path: str) -> List[DetectedError]:
        errors = []
        defined_vars = set()
        used_vars = set()

        builtins = {
            'print', 'len', 'range', 'str', 'int', 'float', 'list', 'dict', 'set', 'tuple',
            'bool', 'None', 'True', 'False', 'if', 'else', 'for', 'while', 'def', 'class',
            'import', 'from', 'return', 'yield', 'raise', 'try', 'except', 'finally',
            'with', 'as', 'in', 'is', 'not', 'and', 'or', 'lambda', 'pass', 'break', 'continue',
            'open', 'input', 'type', 'isinstance', 'hasattr', 'getattr', 'setattr', 'delattr',
            'sorted', 'reversed', 'enumerate', 'zip', 'map', 'filter', 'any', 'all',
            'min', 'max', 'sum', 'abs', 'round', 'pow', 'divmod', 'hex', 'oct', 'bin',
            'ord', 'chr', 'repr', 'hash', 'id', 'dir', 'vars', 'locals', 'globals',
            'super', 'property', 'classmethod', 'staticmethod', '__name__', '__file__',
            'Exception', 'BaseException', 'ValueError', 'TypeError', 'KeyError',
            'IndexError', 'AttributeError', 'RuntimeError', 'StopIteration',
            'NotImplementedError', 'ImportError', 'OSError', 'IOError', 'FileNotFoundError',
        }

        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                if isinstance(node.ctx, ast.Store):
                    defined_vars.add(node.id)
                elif isinstance(node.ctx, ast.Load):
                    used_vars.add(node.id)
            elif isinstance(node, ast.FunctionDef):
                for arg in node.args.args:
                    defined_vars.add(arg.arg)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name.split('.')[0]
                    defined_vars.add(name)
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    defined_vars.add(name)

        undefined = used_vars - defined_vars - builtins

        for var in undefined:
            for node in ast.walk(tree):
                if isinstance(node, ast.Name) and node.id == var and isinstance(node.ctx, ast.Load):
                    errors.append(self._create_error(
                        error_type="undefined_variable",
                        severity=ErrorSeverity.HIGH,
                        message=f"可能未定义的变量 '{var}'",
                        file_path=file_path,
                        line_number=node.lineno,
                        suggestion=f"确保变量 '{var}' 在使用前已定义"
                    ))
                    break

        return errors

    def _detect_type_errors(self, tree: ast.AST, content: str, file_path: str) -> List[DetectedError]:
        errors = []

        for node in ast.walk(tree):
            if isinstance(node, ast.BinOp):
                if isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)):
                    pass

            elif isinstance(node, ast.Compare):
                if len(node.ops) > 1:
                    pass

            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                    if func_name == 'len':
                        if node.args:
                            pass

        return errors

    def _detect_index_errors(self, tree: ast.AST, content: str, file_path: str) -> List[DetectedError]:
        errors = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Subscript):
                if isinstance(node.slice, ast.Constant):
                    if isinstance(node.slice.value, int) and node.slice.value < 0:
                        errors.append(self._create_error(
                            error_type="potential_index_error",
                            severity=ErrorSeverity.MEDIUM,
                            message=f"使用负索引 {node.slice.value} 可能导致意外行为",
                            file_path=file_path,
                            line_number=node.lineno,
                            suggestion="检查索引是否正确，或使用正向索引"
                        ))

        return errors

    def _detect_key_errors(self, tree: ast.AST, content: str, file_path: str) -> List[DetectedError]:
        errors = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Subscript):
                if isinstance(node.value, ast.Name):
                    if isinstance(node.slice, ast.Constant):
                        errors.append(self._create_error(
                            error_type="potential_key_error",
                            severity=ErrorSeverity.MEDIUM,
                            message=f"直接访问字典键 '{node.slice.value}' 可能引发 KeyError",
                            file_path=file_path,
                            line_number=node.lineno,
                            suggestion="使用 dict.get() 方法或检查键是否存在"
                        ))

        return errors

    def _detect_attribute_errors(self, tree: ast.AST, content: str, file_path: str) -> List[DetectedError]:
        errors = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute):
                if isinstance(node.value, ast.Constant):
                    if isinstance(node.value.value, (int, float, bool)):
                        pass

        return errors

    def _detect_zero_division(self, tree: ast.AST, content: str, file_path: str) -> List[DetectedError]:
        errors = []

        for node in ast.walk(tree):
            if isinstance(node, ast.BinOp):
                if isinstance(node.op, (ast.Div, ast.FloorDiv, ast.Mod)):
                    if isinstance(node.right, ast.Constant) and node.right.value == 0:
                        errors.append(self._create_error(
                            error_type="zero_division",
                            severity=ErrorSeverity.HIGH,
                            message="除以零错误",
                            file_path=file_path,
                            line_number=node.lineno,
                            suggestion="添加除数检查，避免除以零"
                        ))

        return errors

    def _detect_recursion_issues(self, tree: ast.AST, content: str, file_path: str) -> List[DetectedError]:
        errors = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_name = node.name
                has_base_case = False
                has_recursive_call = False

                for child in ast.walk(node):
                    if isinstance(child, ast.Return):
                        if isinstance(child.value, ast.Constant):
                            has_base_case = True
                    if isinstance(child, ast.Call):
                        if isinstance(child.func, ast.Name) and child.func.id == func_name:
                            has_recursive_call = True

                if has_recursive_call and not has_base_case:
                    errors.append(self._create_error(
                        error_type="potential_infinite_recursion",
                        severity=ErrorSeverity.MEDIUM,
                        message=f"递归函数 '{func_name}' 可能缺少基准情况",
                        file_path=file_path,
                        line_number=node.lineno,
                        suggestion="确保递归函数有终止条件"
                    ))

        return errors


class LogicErrorDetector(BaseDetector):
    """逻辑错误检测器"""

    name = "logic_error_detector"
    description = "检测潜在的逻辑错误"
    category = ErrorCategory.LOGIC

    def detect(self, content: str, file_path: str) -> DetectionResult:
        import time
        start_time = time.perf_counter()
        errors = []

        try:
            tree = ast.parse(content)
            errors.extend(self._detect_unreachable_code(tree, content, file_path))
            errors.extend(self._detect_unused_variables(tree, content, file_path))
            errors.extend(self._detect_dead_code(tree, content, file_path))
            errors.extend(self._detect_condition_errors(tree, content, file_path))
            errors.extend(self._detect_loop_errors(tree, content, file_path))
            errors.extend(self._detect_comparison_errors(tree, content, file_path))
        except SyntaxError:
            pass

        detection_time = (time.perf_counter() - start_time) * 1000
        status = DetectionStatus.DETECTED if errors else DetectionStatus.NOT_DETECTED

        return self._create_result(file_path, status, errors, detection_time)

    def _detect_unreachable_code(self, tree: ast.AST, content: str, file_path: str) -> List[DetectedError]:
        errors = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                body = node.body
                for i, stmt in enumerate(body):
                    if isinstance(stmt, (ast.Return, ast.Raise, ast.Break, ast.Continue)):
                        if i < len(body) - 1:
                            for j in range(i + 1, len(body)):
                                errors.append(self._create_error(
                                    error_type="unreachable_code",
                                    severity=ErrorSeverity.MEDIUM,
                                    message="不可达代码",
                                    file_path=file_path,
                                    line_number=body[j].lineno,
                                    suggestion="移除不可达代码或调整控制流"
                                ))
                        break

        return errors

    def _detect_unused_variables(self, tree: ast.AST, content: str, file_path: str) -> List[DetectedError]:
        errors = []
        assigned_vars = {}
        used_vars = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                if isinstance(node.ctx, ast.Store):
                    if node.id not in ('_', '__'):
                        assigned_vars[node.id] = node.lineno
                elif isinstance(node.ctx, ast.Load):
                    used_vars.add(node.id)

        for var, line_num in assigned_vars.items():
            if var not in used_vars and not var.startswith('_'):
                errors.append(self._create_error(
                    error_type="unused_variable",
                    severity=ErrorSeverity.LOW,
                    message=f"变量 '{var}' 被赋值但从未使用",
                    file_path=file_path,
                    line_number=line_num,
                    suggestion=f"移除未使用的变量 '{var}' 或添加使用代码"
                ))

        return errors

    def _detect_dead_code(self, tree: ast.AST, content: str, file_path: str) -> List[DetectedError]:
        errors = []

        for node in ast.walk(tree):
            if isinstance(node, ast.If):
                if isinstance(node.test, ast.Constant):
                    if node.test.value is False:
                        errors.append(self._create_error(
                            error_type="dead_code_branch",
                            severity=ErrorSeverity.MEDIUM,
                            message="if 条件永远为 False，代码块永远不会执行",
                            file_path=file_path,
                            line_number=node.lineno,
                            suggestion="移除死代码或修正条件"
                        ))
                    elif node.test.value is True and node.orelse:
                        errors.append(self._create_error(
                            error_type="dead_code_branch",
                            severity=ErrorSeverity.MEDIUM,
                            message="if 条件永远为 True，else 分支永远不会执行",
                            file_path=file_path,
                            line_number=node.orelse[0].lineno if node.orelse else node.lineno,
                            suggestion="移除死代码或修正条件"
                        ))

        return errors

    def _detect_condition_errors(self, tree: ast.AST, content: str, file_path: str) -> List[DetectedError]:
        errors = []

        for node in ast.walk(tree):
            if isinstance(node, ast.BoolOp):
                if isinstance(node.op, ast.And):
                    values = node.values
                    for i, val in enumerate(values):
                        if isinstance(val, ast.Constant) and val.value is False:
                            errors.append(self._create_error(
                                error_type="always_false_condition",
                                severity=ErrorSeverity.MEDIUM,
                                message="AND 条件中存在永远为 False 的表达式",
                                file_path=file_path,
                                line_number=node.lineno,
                                suggestion="简化条件表达式"
                            ))
                            break

                elif isinstance(node.op, ast.Or):
                    values = node.values
                    for val in values:
                        if isinstance(val, ast.Constant) and val.value is True:
                            errors.append(self._create_error(
                                error_type="always_true_condition",
                                severity=ErrorSeverity.MEDIUM,
                                message="OR 条件中存在永远为 True 的表达式",
                                file_path=file_path,
                                line_number=node.lineno,
                                suggestion="简化条件表达式"
                            ))
                            break

            if isinstance(node, ast.Compare):
                if len(node.ops) == 1 and isinstance(node.ops[0], (ast.Eq, ast.NotEq)):
                    if isinstance(node.left, ast.Constant) and isinstance(node.comparators[0], ast.Constant):
                        errors.append(self._create_error(
                            error_type="constant_comparison",
                            severity=ErrorSeverity.LOW,
                            message="比较两个常量值",
                            file_path=file_path,
                            line_number=node.lineno,
                            suggestion="直接使用比较结果，避免运行时比较"
                        ))

        return errors

    def _detect_loop_errors(self, tree: ast.AST, content: str, file_path: str) -> List[DetectedError]:
        errors = []

        for node in ast.walk(tree):
            if isinstance(node, ast.While):
                if isinstance(node.test, ast.Constant) and node.test.value is True:
                    has_break = False
                    for child in ast.walk(node):
                        if isinstance(child, ast.Break):
                            has_break = True
                            break

                    if not has_break:
                        errors.append(self._create_error(
                            error_type="infinite_loop",
                            severity=ErrorSeverity.HIGH,
                            message="潜在的无限循环",
                            file_path=file_path,
                            line_number=node.lineno,
                            suggestion="添加退出条件或 break 语句"
                        ))

            if isinstance(node, ast.For):
                if isinstance(node.iter, ast.Call):
                    if isinstance(node.iter.func, ast.Name):
                        if node.iter.func.id == 'range':
                            if node.iter.args:
                                if isinstance(node.iter.args[0], ast.Constant):
                                    if isinstance(node.iter.args[0].value, int):
                                        if node.iter.args[0].value <= 0:
                                            errors.append(self._create_error(
                                                error_type="empty_loop",
                                                severity=ErrorSeverity.LOW,
                                                message="循环范围可能为空",
                                                file_path=file_path,
                                                line_number=node.lineno,
                                                suggestion="检查循环范围参数"
                                            ))

        return errors

    def _detect_comparison_errors(self, tree: ast.AST, content: str, file_path: str) -> List[DetectedError]:
        errors = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Compare):
                if isinstance(node.ops[0], ast.Is) and isinstance(node.comparators[0], ast.Constant):
                    if node.comparators[0].value not in (None, True, False):
                        errors.append(self._create_error(
                            error_type="is_comparison_with_literal",
                            severity=ErrorSeverity.MEDIUM,
                            message="使用 'is' 比较字面量，应使用 '=='",
                            file_path=file_path,
                            line_number=node.lineno,
                            suggestion="将 'is' 替换为 '=='"
                        ))

                if len(node.ops) >= 2:
                    for i, op in enumerate(node.ops[:-1]):
                        next_op = node.ops[i + 1]
                        if type(op) != type(next_op):
                            errors.append(self._create_error(
                                error_type="chained_comparison_mismatch",
                                severity=ErrorSeverity.LOW,
                                message="链式比较使用不同运算符可能导致意外结果",
                                file_path=file_path,
                                line_number=node.lineno,
                                suggestion="拆分链式比较或确保运算符一致"
                            ))

        return errors


class SecurityVulnerabilityDetector(BaseDetector):
    """安全漏洞检测器"""

    name = "security_vulnerability_detector"
    description = "检测安全漏洞"
    category = ErrorCategory.SECURITY

    DANGEROUS_FUNCTIONS = {
        'eval': ('CWE-95', 'A03:2021-Injection', '代码注入风险'),
        'exec': ('CWE-95', 'A03:2021-Injection', '代码注入风险'),
        'compile': ('CWE-95', 'A03:2021-Injection', '代码注入风险'),
        'os.system': ('CWE-78', 'A03:2021-Injection', '命令注入风险'),
        'subprocess.call': ('CWE-78', 'A03:2021-Injection', '命令注入风险'),
        'subprocess.Popen': ('CWE-78', 'A03:2021-Injection', '命令注入风险'),
        'pickle.loads': ('CWE-502', 'A08:2021-Software and Data Integrity Failures', '不安全的反序列化'),
        'pickle.load': ('CWE-502', 'A08:2021-Software and Data Integrity Failures', '不安全的反序列化'),
        'yaml.load': ('CWE-502', 'A08:2021-Software and Data Integrity Failures', '不安全的YAML加载'),
        'marshal.load': ('CWE-502', 'A08:2021-Software and Data Integrity Failures', '不安全的反序列化'),
        'shelve.open': ('CWE-502', 'A08:2021-Software and Data Integrity Failures', '不安全的持久化'),
    }

    SENSITIVE_PATTERNS = [
        (r'password\s*=\s*["\'][^"\']+["\']', 'password', '硬编码密码'),
        (r'api_key\s*=\s*["\'][^"\']+["\']', 'api_key', '硬编码API密钥'),
        (r'secret_key\s*=\s*["\'][^"\']+["\']', 'secret_key', '硬编码密钥'),
        (r'private_key\s*=\s*["\'][^"\']+["\']', 'private_key', '硬编码私钥'),
        (r'token\s*=\s*["\'][^"\']+["\']', 'token', '硬编码令牌'),
        (r'access_token\s*=\s*["\'][^"\']+["\']', 'access_token', '硬编码访问令牌'),
        (r'auth_token\s*=\s*["\'][^"\']+["\']', 'auth_token', '硬编码认证令牌'),
    ]

    SQL_INJECTION_PATTERNS = [
        r'f["\'].*?(?:SELECT|INSERT|UPDATE|DELETE|CREATE|DROP|ALTER|TRUNCATE).*?\{',
        r'\.format\s*\([^)]*\).*?(?:SELECT|INSERT|UPDATE|DELETE|CREATE|DROP)',
        r'%\s*\([^)]*\).*?(?:SELECT|INSERT|UPDATE|DELETE|CREATE|DROP)',
        r'\+\s*["\'].*?(?:SELECT|INSERT|UPDATE|DELETE|CREATE|DROP)',
        r'["\'].*?(?:SELECT|INSERT|UPDATE|DELETE|CREATE|DROP).*?["\'].*?\+',
    ]

    XSS_PATTERNS = [
        r'render_template_string\s*\(\s*[^)]*\+',
        r'Markup\s*\(\s*[^)]*\+',
        r'\.format\s*\([^)]*\).*?<[^>]+>',
        r'f["\'].*?<[^>]+>.*?\{',
    ]

    def detect(self, content: str, file_path: str) -> DetectionResult:
        import time
        start_time = time.perf_counter()
        errors = []

        try:
            tree = ast.parse(content)
            errors.extend(self._detect_dangerous_functions(tree, content, file_path))
            errors.extend(self._detect_sql_injection(content, file_path))
            errors.extend(self._detect_xss(content, file_path))
            errors.extend(self._detect_hardcoded_secrets(content, file_path))
            errors.extend(self._detect_path_traversal(tree, content, file_path))
            errors.extend(self._detect_insecure_deserialization(tree, content, file_path))
            errors.extend(self._detect_weak_crypto(tree, content, file_path))
        except SyntaxError:
            pass

        detection_time = (time.perf_counter() - start_time) * 1000
        status = DetectionStatus.DETECTED if errors else DetectionStatus.NOT_DETECTED

        return self._create_result(file_path, status, errors, detection_time)

    def _detect_dangerous_functions(self, tree: ast.AST, content: str, file_path: str) -> List[DetectedError]:
        errors = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_func_name(node.func)

                if func_name in self.DANGEROUS_FUNCTIONS:
                    cwe_id, owasp, desc = self.DANGEROUS_FUNCTIONS[func_name]
                    errors.append(self._create_error(
                        error_type="dangerous_function",
                        severity=ErrorSeverity.CRITICAL,
                        message=f"使用危险函数 '{func_name}': {desc}",
                        file_path=file_path,
                        line_number=node.lineno,
                        suggestion=f"避免使用 '{func_name}'，使用更安全的替代方案",
                        cwe_id=cwe_id,
                        owasp_category=owasp
                    ))

        return errors

    def _get_func_name(self, node: ast.expr) -> str:
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            value_name = self._get_func_name(node.value)
            return f"{value_name}.{node.attr}"
        return ""

    def _detect_sql_injection(self, content: str, file_path: str) -> List[DetectedError]:
        errors = []
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            for pattern in self.SQL_INJECTION_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    errors.append(self._create_error(
                        error_type="sql_injection",
                        severity=ErrorSeverity.CRITICAL,
                        message="潜在的SQL注入漏洞",
                        file_path=file_path,
                        line_number=i,
                        code_snippet=line,
                        suggestion="使用参数化查询，避免字符串拼接SQL",
                        cwe_id="CWE-89",
                        owasp_category="A03:2021-Injection"
                    ))
                    break

        return errors

    def _detect_xss(self, content: str, file_path: str) -> List[DetectedError]:
        errors = []
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            for pattern in self.XSS_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    errors.append(self._create_error(
                        error_type="xss_vulnerability",
                        severity=ErrorSeverity.HIGH,
                        message="潜在的XSS跨站脚本漏洞",
                        file_path=file_path,
                        line_number=i,
                        code_snippet=line,
                        suggestion="对用户输入进行HTML转义处理",
                        cwe_id="CWE-79",
                        owasp_category="A03:2021-Injection"
                    ))
                    break

        return errors

    def _detect_hardcoded_secrets(self, content: str, file_path: str) -> List[DetectedError]:
        errors = []
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            for pattern, secret_type, desc in self.SENSITIVE_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    errors.append(self._create_error(
                        error_type="hardcoded_secret",
                        severity=ErrorSeverity.HIGH,
                        message=f"硬编码敏感信息: {desc}",
                        file_path=file_path,
                        line_number=i,
                        code_snippet=line,
                        suggestion=f"使用环境变量或配置文件存储{secret_type}",
                        cwe_id="CWE-798",
                        owasp_category="A07:2021-Identification and Authentication Failures"
                    ))
                    break

        return errors

    def _detect_path_traversal(self, tree: ast.AST, content: str, file_path: str) -> List[DetectedError]:
        errors = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_func_name(node.func)

                if func_name in ('open', 'os.path.join', 'os.open'):
                    for arg in node.args:
                        if isinstance(arg, ast.BinOp) and isinstance(arg.op, ast.Add):
                            errors.append(self._create_error(
                                error_type="path_traversal",
                                severity=ErrorSeverity.HIGH,
                                message="潜在的路径遍历漏洞",
                                file_path=file_path,
                                line_number=node.lineno,
                                suggestion="验证和清理文件路径，使用白名单",
                                cwe_id="CWE-22",
                                owasp_category="A01:2021-Broken Access Control"
                            ))
                            break

                        if isinstance(arg, ast.Name):
                            errors.append(self._create_error(
                                error_type="potential_path_traversal",
                                severity=ErrorSeverity.MEDIUM,
                                message="潜在的路径遍历风险，使用变量作为路径",
                                file_path=file_path,
                                line_number=node.lineno,
                                suggestion="验证用户输入的路径，使用 os.path.basename 或白名单",
                                cwe_id="CWE-22",
                                owasp_category="A01:2021-Broken Access Control"
                            ))

        return errors

    def _detect_insecure_deserialization(self, tree: ast.AST, content: str, file_path: str) -> List[DetectedError]:
        errors = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_func_name(node.func)

                if func_name in ('pickle.loads', 'pickle.load', 'yaml.load'):
                    errors.append(self._create_error(
                        error_type="insecure_deserialization",
                        severity=ErrorSeverity.CRITICAL,
                        message=f"不安全的反序列化: {func_name}",
                        file_path=file_path,
                        line_number=node.lineno,
                        suggestion="使用安全的序列化格式如JSON，或验证输入来源",
                        cwe_id="CWE-502",
                        owasp_category="A08:2021-Software and Data Integrity Failures"
                    ))

        return errors

    def _detect_weak_crypto(self, tree: ast.AST, content: str, file_path: str) -> List[DetectedError]:
        errors = []

        weak_algorithms = ['MD5', 'md5', 'SHA1', 'sha1', 'DES', 'des']
        weak_modes = ['ECB', 'ecb']

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_func_name(node.func)

                if 'hashlib' in func_name:
                    for arg in node.args:
                        if isinstance(arg, ast.Constant) and arg.value in weak_algorithms:
                            errors.append(self._create_error(
                                error_type="weak_hash_algorithm",
                                severity=ErrorSeverity.HIGH,
                                message=f"使用弱哈希算法: {arg.value}",
                                file_path=file_path,
                                line_number=node.lineno,
                                suggestion="使用 SHA-256 或更强的哈希算法",
                                cwe_id="CWE-328",
                                owasp_category="A02:2021-Cryptographic Failures"
                            ))

                if 'AES' in func_name or 'DES' in func_name:
                    for keyword in node.keywords:
                        if keyword.arg == 'mode':
                            if isinstance(keyword.value, ast.Attribute):
                                mode = keyword.value.attr
                                if mode in weak_modes:
                                    errors.append(self._create_error(
                                        error_type="weak_encryption_mode",
                                        severity=ErrorSeverity.HIGH,
                                        message=f"使用弱加密模式: {mode}",
                                        file_path=file_path,
                                        line_number=node.lineno,
                                        suggestion="使用 CBC、GCM 或更安全的加密模式",
                                        cwe_id="CWE-327",
                                        owasp_category="A02:2021-Cryptographic Failures"
                                    ))

        return errors


class PerformanceIssueDetector(BaseDetector):
    """性能问题检测器"""

    name = "performance_issue_detector"
    description = "检测性能问题"
    category = ErrorCategory.PERFORMANCE

    def detect(self, content: str, file_path: str) -> DetectionResult:
        import time
        start_time = time.perf_counter()
        errors = []

        try:
            tree = ast.parse(content)
            errors.extend(self._detect_inefficient_loops(tree, content, file_path))
            errors.extend(self._detect_string_concatenation(tree, content, file_path))
            errors.extend(self._detect_memory_issues(tree, content, file_path))
            errors.extend(self._detect_unnecessary_operations(tree, content, file_path))
        except SyntaxError:
            pass

        detection_time = (time.perf_counter() - start_time) * 1000
        status = DetectionStatus.DETECTED if errors else DetectionStatus.NOT_DETECTED

        return self._create_result(file_path, status, errors, detection_time)

    def _detect_inefficient_loops(self, tree: ast.AST, content: str, file_path: str) -> List[DetectedError]:
        errors = []

        for node in ast.walk(tree):
            if isinstance(node, ast.For):
                if isinstance(node.iter, ast.Call):
                    if isinstance(node.iter.func, ast.Name):
                        if node.iter.func.id == 'range':
                            if len(node.iter.args) == 1:
                                for child in ast.walk(node):
                                    if isinstance(child, ast.Subscript):
                                        if isinstance(child.value, ast.Name):
                                            errors.append(self._create_error(
                                                error_type="inefficient_loop_indexing",
                                                severity=ErrorSeverity.MEDIUM,
                                                message="使用 range(len()) 进行索引，建议使用 enumerate()",
                                                file_path=file_path,
                                                line_number=node.lineno,
                                                suggestion="使用 for i, item in enumerate(seq): 替代"
                                            ))
                                            break

            if isinstance(node, ast.Compare):
                if isinstance(node.ops[0], ast.In):
                    if isinstance(node.comparators[0], ast.Name):
                        pass

        return errors

    def _detect_string_concatenation(self, tree: ast.AST, content: str, file_path: str) -> List[DetectedError]:
        errors = []

        for node in ast.walk(tree):
            if isinstance(node, ast.AugAssign):
                if isinstance(node.op, ast.Add):
                    if isinstance(node.target, ast.Name):
                        for child in ast.walk(tree):
                            if isinstance(child, ast.For):
                                for stmt in child.body:
                                    if isinstance(stmt, ast.AugAssign):
                                        if isinstance(stmt.target, ast.Name):
                                            if stmt.target.id == node.target.id:
                                                errors.append(self._create_error(
                                                    error_type="inefficient_string_concat",
                                                    severity=ErrorSeverity.MEDIUM,
                                                    message="在循环中使用 += 进行字符串拼接效率低",
                                                    file_path=file_path,
                                                    line_number=stmt.lineno,
                                                    suggestion="使用列表和 ''.join() 进行字符串拼接"
                                                ))

        return errors

    def _detect_memory_issues(self, tree: ast.AST, content: str, file_path: str) -> List[DetectedError]:
        errors = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ListComp):
                pass

            if isinstance(node, ast.With):
                pass

            if isinstance(node, ast.Call):
                func_name = ""
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr

                if func_name == 'read' or func_name == 'readlines':
                    errors.append(self._create_error(
                        error_type="potential_memory_issue",
                        severity=ErrorSeverity.LOW,
                        message="一次性读取大文件可能导致内存问题",
                        file_path=file_path,
                        line_number=node.lineno,
                        suggestion="考虑逐行读取或使用生成器"
                    ))

        return errors

    def _detect_unnecessary_operations(self, tree: ast.AST, content: str, file_path: str) -> List[DetectedError]:
        errors = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id == 'len':
                        for parent in ast.walk(tree):
                            if isinstance(parent, ast.Compare):
                                for comparator in parent.comparators:
                                    if comparator == node:
                                        pass

                    if node.func.id == 'sorted':
                        if node.keywords:
                            for kw in node.keywords:
                                if kw.arg == 'reverse' and isinstance(kw.value, ast.Constant):
                                    if kw.value.value is True:
                                        pass

        return errors


class CodeSmellDetector(BaseDetector):
    """代码异味检测器"""

    name = "code_smell_detector"
    description = "检测代码异味"
    category = ErrorCategory.CODE_SMELL

    def detect(self, content: str, file_path: str) -> DetectionResult:
        import time
        start_time = time.perf_counter()
        errors = []

        try:
            tree = ast.parse(content)
            errors.extend(self._detect_long_functions(tree, content, file_path))
            errors.extend(self._detect_deep_nesting(tree, content, file_path))
            errors.extend(self._detect_duplicate_code(tree, content, file_path))
            errors.extend(self._detect_magic_numbers(tree, content, file_path))
            errors.extend(self._detect_long_parameter_list(tree, content, file_path))
            errors.extend(self._detect_god_class(tree, content, file_path))
        except SyntaxError:
            pass

        detection_time = (time.perf_counter() - start_time) * 1000
        status = DetectionStatus.DETECTED if errors else DetectionStatus.NOT_DETECTED

        return self._create_result(file_path, status, errors, detection_time)

    def _detect_long_functions(self, tree: ast.AST, content: str, file_path: str, max_lines: int = 50) -> List[DetectedError]:
        errors = []
        lines = content.split('\n')

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_lines = node.end_lineno - node.lineno + 1 if hasattr(node, 'end_lineno') else 0
                if func_lines > max_lines:
                    errors.append(self._create_error(
                        error_type="long_function",
                        severity=ErrorSeverity.MEDIUM,
                        message=f"函数 '{node.name}' 过长 ({func_lines} 行)",
                        file_path=file_path,
                        line_number=node.lineno,
                        suggestion="将函数拆分为更小的函数，每个函数只做一件事"
                    ))

        return errors

    def _detect_deep_nesting(self, tree: ast.AST, content: str, file_path: str, max_depth: int = 4) -> List[DetectedError]:
        errors = []

        def check_nesting(node: ast.AST, depth: int, line_num: int):
            if depth > max_depth:
                errors.append(self._create_error(
                    error_type="deep_nesting",
                    severity=ErrorSeverity.MEDIUM,
                    message=f"嵌套层级过深 ({depth} 层)",
                    file_path=file_path,
                    line_number=line_num,
                    suggestion="使用提前返回、提取方法或策略模式减少嵌套"
                ))

            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
                    check_nesting(child, depth + 1, child.lineno)
                else:
                    check_nesting(child, depth, line_num)

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for child in node.body:
                    if isinstance(child, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
                        check_nesting(child, 1, child.lineno)

        return errors

    def _detect_duplicate_code(self, tree: ast.AST, content: str, file_path: str) -> List[DetectedError]:
        errors = []
        code_blocks = {}

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                block_lines = []
                for child in node.body:
                    if isinstance(child, ast.Expr) and isinstance(child.value, ast.Constant):
                        continue
                    block_lines.append(ast.dump(child))

                block_hash = hash(tuple(block_lines))
                if block_hash in code_blocks:
                    errors.append(self._create_error(
                        error_type="duplicate_code",
                        severity=ErrorSeverity.MEDIUM,
                        message=f"函数 '{node.name}' 可能与 '{code_blocks[block_hash]}' 有重复代码",
                        file_path=file_path,
                        line_number=node.lineno,
                        suggestion="提取公共代码到独立函数"
                    ))
                else:
                    code_blocks[block_hash] = node.name

        return errors

    def _detect_magic_numbers(self, tree: ast.AST, content: str, file_path: str) -> List[DetectedError]:
        errors = []
        allowed_numbers = {0, 1, 2, -1, 100, 1000, 3600, 255, 256, 1024}

        for node in ast.walk(tree):
            if isinstance(node, ast.Constant):
                if isinstance(node.value, (int, float)):
                    if node.value not in allowed_numbers:
                        parent_types = []
                        for parent in ast.walk(tree):
                            for child in ast.iter_child_nodes(parent):
                                if child is node:
                                    parent_types.append(type(parent).__name__)

                        if 'Assign' not in parent_types and 'AnnAssign' not in parent_types:
                            errors.append(self._create_error(
                                error_type="magic_number",
                                severity=ErrorSeverity.LOW,
                                message=f"魔法数字 {node.value}",
                                file_path=file_path,
                                line_number=node.lineno,
                                suggestion="将数字定义为有意义的常量"
                            ))

        return errors

    def _detect_long_parameter_list(self, tree: ast.AST, content: str, file_path: str, max_params: int = 5) -> List[DetectedError]:
        errors = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                param_count = len(node.args.args)
                param_count += len(node.args.posonlyargs)
                param_count += len(node.args.kwonlyargs)
                if node.args.vararg:
                    param_count += 1
                if node.args.kwarg:
                    param_count += 1

                if param_count > max_params:
                    errors.append(self._create_error(
                        error_type="long_parameter_list",
                        severity=ErrorSeverity.MEDIUM,
                        message=f"函数 '{node.name}' 参数过多 ({param_count} 个)",
                        file_path=file_path,
                        line_number=node.lineno,
                        suggestion="使用配置对象或拆分函数"
                    ))

        return errors

    def _detect_god_class(self, tree: ast.AST, content: str, file_path: str, max_methods: int = 15) -> List[DetectedError]:
        errors = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                method_count = sum(1 for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)))
                if method_count > max_methods:
                    errors.append(self._create_error(
                        error_type="god_class",
                        severity=ErrorSeverity.MEDIUM,
                        message=f"类 '{node.name}' 方法过多 ({method_count} 个)",
                        file_path=file_path,
                        line_number=node.lineno,
                        suggestion="将类拆分为更小的类，遵循单一职责原则"
                    ))

        return errors


class ErrorDetectorEnhanced:
    """增强版错误检测器"""

    def __init__(self):
        self._detectors: Dict[str, BaseDetector] = {}
        self._result_counter = 0
        self._register_builtin_detectors()

    def _register_builtin_detectors(self):
        detectors = [
            SyntaxErrorDetector(),
            RuntimeErrorDetector(),
            LogicErrorDetector(),
            SecurityVulnerabilityDetector(),
            PerformanceIssueDetector(),
            CodeSmellDetector(),
        ]

        for detector in detectors:
            self._detectors[detector.name] = detector

    def register_detector(self, detector: BaseDetector) -> None:
        self._detectors[detector.name] = detector
        logger.info(f"已注册检测器: {detector.name}")

    def detect_file(self, file_path: str, categories: Optional[List[ErrorCategory]] = None) -> List[DetectionResult]:
        results = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            logger.error(f"读取文件失败: {file_path}, {e}")
            return results

        for name, detector in self._detectors.items():
            if categories and detector.category not in categories:
                continue

            result = detector.detect(content, file_path)
            results.append(result)

        return results

    def detect_directory(self, dir_path: str, categories: Optional[List[ErrorCategory]] = None,
                        recursive: bool = True) -> List[DetectionResult]:
        results = []
        path = Path(dir_path)

        if recursive:
            files = list(path.rglob('*.py'))
        else:
            files = list(path.glob('*.py'))

        for file_path in files:
            file_results = self.detect_file(str(file_path), categories)
            results.extend(file_results)

        return results

    def generate_report(self, results: List[DetectionResult]) -> DetectionReport:
        self._result_counter += 1

        total_errors = sum(len(r.errors) for r in results)
        summary_by_category = defaultdict(int)
        summary_by_severity = defaultdict(int)

        for result in results:
            for error in result.errors:
                summary_by_category[error.category.name] += 1
                summary_by_severity[error.severity.value] += 1

        recommendations = self._generate_recommendations(results)

        return DetectionReport(
            report_id=f"REPORT_{self._result_counter:06d}",
            generated_at=datetime.now().isoformat(),
            total_files=len(set(r.file_path for r in results)),
            total_errors=total_errors,
            results=results,
            summary_by_category=dict(summary_by_category),
            summary_by_severity=dict(summary_by_severity),
            recommendations=recommendations
        )

    def _generate_recommendations(self, results: List[DetectionResult]) -> List[str]:
        recommendations = []

        critical_count = sum(
            1 for r in results for e in r.errors
            if e.severity == ErrorSeverity.CRITICAL
        )
        security_count = sum(
            1 for r in results for e in r.errors
            if e.category == ErrorCategory.SECURITY
        )

        if critical_count > 0:
            recommendations.append(f"发现 {critical_count} 个严重错误，建议立即修复")

        if security_count > 0:
            recommendations.append(f"发现 {security_count} 个安全问题，建议优先处理")

        return recommendations

    def get_all_detectors(self) -> List[BaseDetector]:
        return list(self._detectors.values())

    def get_detector(self, name: str) -> Optional[BaseDetector]:
        return self._detectors.get(name)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="增强版错误检测器",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument("--file", type=str, help="要检测的文件路径")
    parser.add_argument("--dir", type=str, help="要检测的目录路径")
    parser.add_argument("--detect-all", action="store_true", help="检测所有类型错误")
    parser.add_argument("--detect-syntax", action="store_true", help="检测语法错误")
    parser.add_argument("--detect-runtime", action="store_true", help="检测运行时错误")
    parser.add_argument("--detect-logic", action="store_true", help="检测逻辑错误")
    parser.add_argument("--detect-security", action="store_true", help="检测安全漏洞")
    parser.add_argument("--detect-performance", action="store_true", help="检测性能问题")
    parser.add_argument("--detect-smell", action="store_true", help="检测代码异味")
    parser.add_argument("--report", type=str, help="报告输出路径")
    parser.add_argument("--recursive", action="store_true", default=True, help="递归检测目录")

    args = parser.parse_args()

    detector = ErrorDetectorEnhanced()

    categories = []
    if args.detect_all:
        categories = None
    else:
        if args.detect_syntax:
            categories.append(ErrorCategory.SYNTAX)
        if args.detect_runtime:
            categories.append(ErrorCategory.RUNTIME)
        if args.detect_logic:
            categories.append(ErrorCategory.LOGIC)
        if args.detect_security:
            categories.append(ErrorCategory.SECURITY)
        if args.detect_performance:
            categories.append(ErrorCategory.PERFORMANCE)
        if args.detect_smell:
            categories.append(ErrorCategory.CODE_SMELL)

    if not categories and not args.detect_all:
        categories = None

    results = []

    if args.file:
        results = detector.detect_file(args.file, categories)
    elif args.dir:
        results = detector.detect_directory(args.dir, categories, args.recursive)
    else:
        print("请指定 --file 或 --dir 参数")
        return 1

    report = detector.generate_report(results)

    print("\n" + "=" * 80)
    print("错误检测报告")
    print("=" * 80)
    print(f"报告ID: {report.report_id}")
    print(f"生成时间: {report.generated_at}")
    print(f"检测文件数: {report.total_files}")
    print(f"发现问题数: {report.total_errors}")

    print("\n按类别统计:")
    for cat, count in report.summary_by_category.items():
        print(f"  {cat}: {count}")

    print("\n按严重程度统计:")
    for sev, count in report.summary_by_severity.items():
        print(f"  {sev}: {count}")

    if report.recommendations:
        print("\n建议:")
        for rec in report.recommendations:
            print(f"  • {rec}")

    if args.report:
        with open(args.report, 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)
        print(f"\n报告已保存到: {args.report}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
