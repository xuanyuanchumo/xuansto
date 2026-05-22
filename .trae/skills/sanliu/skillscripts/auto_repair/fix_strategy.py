#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复策略库 - Fix Strategy Library

完善的修复策略库，包括：
- 语法修复策略
- 导入修复策略
- 类型修复策略
- 安全修复策略

使用示例:
    library = FixStrategyLibrary()
    result = library.apply_fix(issue)
"""

from __future__ import annotations

import ast
import re
import os
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from .issue_detector import Issue, IssueCategory, IssueSeverity

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FixStatus(Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    SKIPPED = "skipped"
    NEEDS_MANUAL_REVIEW = "needs_manual_review"


class StrategyPriority(Enum):
    CRITICAL = 0
    HIGH = 1
    MEDIUM = 2
    LOW = 3
    INFO = 4


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
            "execution_time_ms": round(self.execution_time_ms, 2),
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
    last_applied: Optional[str] = None

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


class FixStrategy(ABC):
    """修复策略基类"""

    name: str = "base_strategy"
    description: str = "基础修复策略"
    applicable_categories: List[IssueCategory] = []
    priority: StrategyPriority = StrategyPriority.MEDIUM

    def __init__(self):
        self.metrics = StrategyMetrics(strategy_name=self.name)
        self._result_counter = 0

    @abstractmethod
    def can_apply(self, issue: Issue) -> bool:
        pass

    @abstractmethod
    def _do_apply(self, issue: Issue, content: str) -> Tuple[FixStatus, str, float, str, List[str]]:
        pass

    def apply(self, issue: Issue, content: str) -> FixResult:
        import time
        start_time = time.perf_counter()
        self._result_counter += 1

        try:
            status, fixed_code, confidence, message, warnings = self._do_apply(issue, content)
        except Exception as e:
            status = FixStatus.FAILED
            fixed_code = content
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

        return FixResult(
            result_id=f"{self.name}_{self._result_counter:04d}",
            issue_id=issue.issue_id,
            strategy_name=self.name,
            status=status,
            original_code=content,
            fixed_code=fixed_code,
            line_number=issue.line_number,
            confidence=confidence,
            execution_time_ms=execution_time_ms,
            message=message,
            warnings=warnings
        )

    def get_metrics(self) -> StrategyMetrics:
        return self.metrics


class SyntaxFixStrategy(FixStrategy):
    """语法修复策略"""

    name = "syntax_fix"
    description = "修复Python语法错误"
    applicable_categories = [
        IssueCategory.SYNTAX_ERROR,
        IssueCategory.SYNTAX_INDENTATION,
        IssueCategory.SYNTAX_BRACKET_MISMATCH,
        IssueCategory.SYNTAX_COLON_MISSING,
    ]
    priority = StrategyPriority.CRITICAL

    BLOCK_KEYWORDS = {'if', 'elif', 'else', 'for', 'while', 'def', 'class', 'try', 'except', 'finally', 'with'}

    def can_apply(self, issue: Issue) -> bool:
        return issue.category in self.applicable_categories

    def _do_apply(self, issue: Issue, content: str) -> Tuple[FixStatus, str, float, str, List[str]]:
        fixed = content
        warnings = []
        confidence = 0.0

        if issue.category == IssueCategory.SYNTAX_COLON_MISSING:
            fixed, confidence = self._fix_missing_colon(content, issue)
            warnings.append("已添加缺失的冒号")
        elif issue.category == IssueCategory.SYNTAX_INDENTATION:
            fixed, confidence = self._fix_indentation(content, issue)
            warnings.append("已修复缩进问题")
        elif issue.category == IssueCategory.SYNTAX_BRACKET_MISMATCH:
            fixed, confidence = self._fix_brackets(content, issue)
            warnings.append("已修复括号匹配")
        else:
            fixed, confidence = self._fix_general_syntax(content, issue)

        if fixed == content:
            return FixStatus.NEEDS_MANUAL_REVIEW, content, 0.5, "无法自动修复", warnings

        status = FixStatus.SUCCESS if confidence >= 0.7 else FixStatus.PARTIAL
        return status, fixed, confidence, "语法错误已修复", warnings

    def _fix_missing_colon(self, content: str, issue: Issue) -> Tuple[str, float]:
        lines = content.split('\n')
        line_idx = issue.line_number - 1
        
        if 0 <= line_idx < len(lines):
            line = lines[line_idx]
            stripped = line.strip()
            first_word = stripped.split()[0] if stripped.split() else ''
            
            if first_word in self.BLOCK_KEYWORDS and not stripped.endswith(':'):
                lines[line_idx] = line.rstrip() + ':'
                return '\n'.join(lines), 0.9
        
        return content, 0.5

    def _fix_indentation(self, content: str, issue: Issue) -> Tuple[str, float]:
        lines = content.split('\n')
        fixed_lines = []
        
        for i, line in enumerate(lines):
            if '\t' in line:
                indent = len(line) - len(line.lstrip())
                fixed_lines.append(' ' * (indent * 4) + line.lstrip())
            else:
                fixed_lines.append(line)
        
        return '\n'.join(fixed_lines), 0.85

    def _fix_brackets(self, content: str, issue: Issue) -> Tuple[str, float]:
        bracket_pairs = {'(': ')', '[': ']', '{': '}'}
        stack = []
        fixed = list(content)
        
        in_string = False
        string_char = None
        
        for i, char in enumerate(content):
            if char in '\'"' and not in_string:
                in_string = True
                string_char = char
            elif char == string_char and in_string:
                in_string = False
                string_char = None
            elif not in_string:
                if char in bracket_pairs:
                    stack.append((char, i))
                elif char in bracket_pairs.values():
                    if stack:
                        expected_open = [k for k, v in bracket_pairs.items() if v == char][0]
                        if stack[-1][0] == expected_open:
                            stack.pop()
                        else:
                            stack.pop()
                    else:
                        for open_bracket, close_bracket in bracket_pairs.items():
                            if close_bracket == char:
                                fixed.insert(i, open_bracket)
                                break
        
        for bracket, pos in reversed(stack):
            close_bracket = bracket_pairs[bracket]
            fixed.append(close_bracket)
        
        return ''.join(fixed), 0.8

    def _fix_general_syntax(self, content: str, issue: Issue) -> Tuple[str, float]:
        try:
            ast.parse(content)
            return content, 1.0
        except SyntaxError:
            pass
        
        fixed = content
        confidence = 0.5
        
        fixed, c1 = self._fix_missing_colon(fixed, issue)
        confidence = max(confidence, c1)
        
        fixed, c2 = self._fix_brackets(fixed, issue)
        confidence = max(confidence, c2)
        
        return fixed, confidence


class ImportFixStrategy(FixStrategy):
    """导入修复策略"""

    name = "import_fix"
    description = "修复导入相关问题"
    applicable_categories = [
        IssueCategory.IMPORT_MISSING,
        IssueCategory.IMPORT_PATH_ERROR,
        IssueCategory.IMPORT_UNUSED,
    ]
    priority = StrategyPriority.HIGH

    COMMON_IMPORTS = {
        'os': 'import os',
        'sys': 'import sys',
        're': 'import re',
        'json': 'import json',
        'datetime': 'from datetime import datetime',
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
        'dataclass': 'from dataclasses import dataclass',
        'Enum': 'from enum import Enum',
        'logging': 'import logging',
        'np': 'import numpy as np',
        'pd': 'import pandas as pd',
        'pytest': 'import pytest',
        'asyncio': 'import asyncio',
        'subprocess': 'import subprocess',
        'shutil': 'import shutil',
        'hashlib': 'import hashlib',
        'time': 'import time',
        'ast': 'import ast',
        'abc': 'from abc import ABC, abstractmethod',
        'contextlib': 'import contextlib',
        'typing': 'import typing',
        'warnings': 'import warnings',
        'traceback': 'import traceback',
        'inspect': 'import inspect',
    }

    PATH_CORRECTIONS = {
        'django.core.urlresolvers': 'django.urls',
        'urlparse': 'urllib.parse.urlparse',
        'urllib2': 'urllib.request',
        'ConfigParser': 'configparser',
        'cPickle': 'pickle',
        'cStringIO': 'io',
        'StringIO': 'io',
        'Queue': 'queue',
        'SocketServer': 'socketserver',
        'sklearn.cross_validation': 'sklearn.model_selection',
    }

    def can_apply(self, issue: Issue) -> bool:
        return issue.category in self.applicable_categories

    def _do_apply(self, issue: Issue, content: str) -> Tuple[FixStatus, str, float, str, List[str]]:
        if issue.category == IssueCategory.IMPORT_MISSING:
            return self._fix_missing_import(issue, content)
        elif issue.category == IssueCategory.IMPORT_PATH_ERROR:
            return self._fix_import_path(issue, content)
        elif issue.category == IssueCategory.IMPORT_UNUSED:
            return self._fix_unused_import(issue, content)
        
        return FixStatus.SKIPPED, content, 0.0, "不支持的导入问题类型", []

    def _fix_missing_import(self, issue: Issue, content: str) -> Tuple[FixStatus, str, float, str, List[str]]:
        warnings = []
        missing_name = issue.context.get('missing_name', '')
        
        if not missing_name:
            return FixStatus.NEEDS_MANUAL_REVIEW, content, 0.5, "无法确定缺失的导入名称", warnings
        
        import_statement = self.COMMON_IMPORTS.get(missing_name)
        
        if not import_statement:
            import_statement = f"import {missing_name}"
            warnings.append(f"未找到 '{missing_name}' 的标准导入路径，使用默认导入")
            confidence = 0.6
        else:
            confidence = 0.95
        
        lines = content.split('\n')
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
        
        if import_statement not in [l.strip() for l in import_lines]:
            import_lines.append(import_statement)
            import_lines.sort()
        
        fixed = '\n'.join(import_lines) + '\n\n' + '\n'.join(code_lines)
        fixed = fixed.strip() + '\n'
        
        return FixStatus.SUCCESS, fixed, confidence, f"已添加导入: {import_statement}", warnings

    def _fix_import_path(self, issue: Issue, content: str) -> Tuple[FixStatus, str, float, str, List[str]]:
        warnings = []
        old_module = issue.context.get('old_module', '')
        new_module = issue.context.get('new_module', '')
        
        if not old_module:
            old_module = issue.context.get('wrong_path', '')
        
        if not new_module and old_module in self.PATH_CORRECTIONS:
            new_module = self.PATH_CORRECTIONS[old_module]
        
        if not old_module or not new_module:
            return FixStatus.NEEDS_MANUAL_REVIEW, content, 0.5, "无法确定导入路径映射", warnings
        
        fixed = content.replace(old_module, new_module)
        
        if fixed == content:
            return FixStatus.FAILED, content, 0.3, "未找到需要替换的导入路径", warnings
        
        return FixStatus.SUCCESS, fixed, 0.85, f"导入路径已修正: {old_module} -> {new_module}", warnings

    def _fix_unused_import(self, issue: Issue, content: str) -> Tuple[FixStatus, str, float, str, List[str]]:
        warnings = []
        import_name = issue.context.get('import_name', '')
        
        if not import_name:
            return FixStatus.NEEDS_MANUAL_REVIEW, content, 0.5, "无法确定要移除的导入", warnings
        
        lines = content.split('\n')
        fixed_lines = []
        removed = False
        
        for line in lines:
            stripped = line.strip()
            if import_name in line and (stripped.startswith('import ') or stripped.startswith('from ')):
                if import_name.split('.')[0] in line:
                    warnings.append(f"已移除未使用的导入: {import_name}")
                    removed = True
                    continue
            fixed_lines.append(line)
        
        if not removed:
            return FixStatus.FAILED, content, 0.3, "未找到要移除的导入", warnings
        
        fixed = '\n'.join(fixed_lines)
        return FixStatus.SUCCESS, fixed, 0.9, f"已移除未使用的导入: {import_name}", warnings


class TypeFixStrategy(FixStrategy):
    """类型修复策略"""

    name = "type_fix"
    description = "修复类型相关问题"
    applicable_categories = [
        IssueCategory.TYPE_ERROR,
        IssueCategory.TYPE_MISMATCH,
        IssueCategory.TYPE_MISSING_ANNOTATION,
    ]
    priority = StrategyPriority.MEDIUM

    def can_apply(self, issue: Issue) -> bool:
        return issue.category in self.applicable_categories

    def _do_apply(self, issue: Issue, content: str) -> Tuple[FixStatus, str, float, str, List[str]]:
        if issue.category == IssueCategory.TYPE_MISSING_ANNOTATION:
            return self._fix_missing_annotation(issue, content)
        elif issue.category == IssueCategory.TYPE_MISMATCH:
            return self._fix_type_mismatch(issue, content)
        
        return FixStatus.SKIPPED, content, 0.0, "不支持的类型问题", []

    def _fix_missing_annotation(self, issue: Issue, content: str) -> Tuple[FixStatus, str, float, str, List[str]]:
        warnings = []
        func_name = issue.context.get('function_name', '')
        param_name = issue.context.get('parameter_name', '')
        
        if param_name:
            fixed, confidence = self._add_param_annotation(content, func_name, param_name)
            warnings.append(f"已为参数 '{param_name}' 添加类型注解")
        elif func_name:
            fixed, confidence = self._add_return_annotation(content, func_name)
            warnings.append(f"已为函数 '{func_name}' 添加返回类型注解")
        else:
            return FixStatus.NEEDS_MANUAL_REVIEW, content, 0.5, "缺少函数或参数信息", warnings
        
        if fixed == content:
            return FixStatus.PARTIAL, content, 0.6, "无法添加类型注解", warnings
        
        return FixStatus.SUCCESS, fixed, confidence, "类型注解已添加", warnings

    def _add_param_annotation(self, content: str, func_name: str, param_name: str) -> Tuple[str, float]:
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return content, 0.3
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == func_name:
                for arg in node.args.args:
                    if arg.arg == param_name and arg.annotation is None:
                        lines = content.split('\n')
                        line_idx = node.lineno - 1
                        if 0 <= line_idx < len(lines):
                            line = lines[line_idx]
                            pattern = rf'\b{param_name}\b(?!\s*:)'
                            replacement = f'{param_name}: Any'
                            lines[line_idx] = re.sub(pattern, replacement, line, count=1)
                            return '\n'.join(lines), 0.75
        
        return content, 0.5

    def _add_return_annotation(self, content: str, func_name: str) -> Tuple[str, float]:
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return content, 0.3
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == func_name:
                if node.returns is None:
                    lines = content.split('\n')
                    line_idx = node.lineno - 1
                    if 0 <= line_idx < len(lines):
                        line = lines[line_idx]
                        if '):' in line:
                            lines[line_idx] = line.replace('):', ') -> Any:')
                        elif '):\n' in line:
                            lines[line_idx] = line.replace('):\n', ') -> Any:\n')
                        return '\n'.join(lines), 0.7
        
        return content, 0.5

    def _fix_type_mismatch(self, issue: Issue, content: str) -> Tuple[FixStatus, str, float, str, List[str]]:
        warnings = []
        warnings.append("类型不匹配问题可能需要手动调整")
        return FixStatus.NEEDS_MANUAL_REVIEW, content, 0.5, "类型不匹配需要手动审查", warnings


class SecurityFixStrategy(FixStrategy):
    """安全修复策略"""

    name = "security_fix"
    description = "修复安全漏洞"
    applicable_categories = [
        IssueCategory.SECURITY_SQL_INJECTION,
        IssueCategory.SECURITY_COMMAND_INJECTION,
        IssueCategory.SECURITY_HARDCODED_SECRET,
        IssueCategory.SECURITY_PATH_TRAVERSAL,
        IssueCategory.SECURITY_INSECURE_DESERIALIZE,
        IssueCategory.SECURITY_SSL_ISSUE,
        IssueCategory.SECURITY_WEAK_CRYPTO,
    ]
    priority = StrategyPriority.CRITICAL

    def can_apply(self, issue: Issue) -> bool:
        return issue.category in self.applicable_categories

    def _do_apply(self, issue: Issue, content: str) -> Tuple[FixStatus, str, float, str, List[str]]:
        if issue.category == IssueCategory.SECURITY_SQL_INJECTION:
            return self._fix_sql_injection(issue, content)
        elif issue.category == IssueCategory.SECURITY_COMMAND_INJECTION:
            return self._fix_command_injection(issue, content)
        elif issue.category == IssueCategory.SECURITY_HARDCODED_SECRET:
            return self._fix_hardcoded_secret(issue, content)
        elif issue.category == IssueCategory.SECURITY_PATH_TRAVERSAL:
            return self._fix_path_traversal(issue, content)
        elif issue.category == IssueCategory.SECURITY_INSECURE_DESERIALIZE:
            return self._fix_insecure_deserialize(issue, content)
        elif issue.category == IssueCategory.SECURITY_SSL_ISSUE:
            return self._fix_ssl_issue(issue, content)
        elif issue.category == IssueCategory.SECURITY_WEAK_CRYPTO:
            return self._fix_weak_crypto(issue, content)
        
        return FixStatus.SKIPPED, content, 0.0, "不支持的安全问题类型", []

    def _fix_sql_injection(self, issue: Issue, content: str) -> Tuple[FixStatus, str, float, str, List[str]]:
        warnings = []
        fixed = content
        
        fstring_pattern = r'f(["\'])(.*?\{.*?\}.*?)\1'
        if re.search(fstring_pattern, content, re.DOTALL):
            fixed = self._convert_fstring_to_param(content)
            warnings.append("已将f-string SQL转换为参数化查询")
        
        format_pattern = r'(["\'].*?["\'])\.format\s*\(([^)]*)\)'
        if re.search(format_pattern, content):
            fixed = self._convert_format_to_param(fixed)
            warnings.append("已将.format() SQL转换为参数化查询")
        
        if fixed == content:
            return FixStatus.NEEDS_MANUAL_REVIEW, content, 0.5, "SQL注入修复需要手动审查", warnings
        
        return FixStatus.SUCCESS, fixed, 0.85, "SQL注入漏洞已修复", warnings

    def _convert_fstring_to_param(self, content: str) -> str:
        def replace_fstring(match):
            quote = match.group(1)
            sql_template = match.group(2)
            param_pattern = r'\{([^}]+)\}'
            param_names = re.findall(param_pattern, sql_template)
            new_sql = re.sub(param_pattern, '%s', sql_template)
            new_sql = new_sql.lstrip('f')
            if param_names:
                param_str = ', '.join(param_names)
                return f'{quote}{new_sql}{quote}, ({param_str})'
            return match.group(0)
        
        return re.sub(r'f(["\'])(.*?\{.*?\}.*?)\1', replace_fstring, content, flags=re.DOTALL)

    def _convert_format_to_param(self, content: str) -> str:
        def replace_format(match):
            sql_template = match.group(1)
            params = match.group(2)
            placeholder_pattern = r'\{(\d*)\}'
            new_sql = re.sub(placeholder_pattern, '%s', sql_template)
            return f'{new_sql}, ({params})'
        
        return re.sub(r'(["\'].*?["\'])\.format\s*\(([^)]*)\)', replace_format, content)

    def _fix_command_injection(self, issue: Issue, content: str) -> Tuple[FixStatus, str, float, str, List[str]]:
        warnings = []
        fixed = content
        
        os_system_pattern = r'os\.system\s*\(\s*([^)]+)\s*\)'
        if re.search(os_system_pattern, fixed):
            fixed = re.sub(os_system_pattern, r'subprocess.run(\1, shell=False)', fixed)
            warnings.append("已将 os.system 替换为 subprocess.run")
        
        eval_pattern = r'eval\s*\(\s*([^)]+)\s*\)'
        if re.search(eval_pattern, fixed):
            fixed = re.sub(eval_pattern, r'ast.literal_eval(\1)', fixed)
            warnings.append("已将 eval 替换为 ast.literal_eval")
        
        if fixed == content:
            return FixStatus.NEEDS_MANUAL_REVIEW, content, 0.5, "命令注入修复需要手动审查", warnings
        
        if 'subprocess.run' in fixed and 'import subprocess' not in fixed:
            lines = fixed.split('\n')
            lines.insert(0, 'import subprocess')
            fixed = '\n'.join(lines)
        
        if 'ast.literal_eval' in fixed and 'import ast' not in fixed:
            lines = fixed.split('\n')
            lines.insert(0, 'import ast')
            fixed = '\n'.join(lines)
        
        return FixStatus.SUCCESS, fixed, 0.85, "命令注入漏洞已修复", warnings

    def _fix_hardcoded_secret(self, issue: Issue, content: str) -> Tuple[FixStatus, str, float, str, List[str]]:
        warnings = []
        fixed = content
        
        secret_patterns = [
            (r'password\s*=\s*["\']([^"\']+)["\']', 'password'),
            (r'passwd\s*=\s*["\']([^"\']+)["\']', 'password'),
            (r'api_key\s*=\s*["\']([^"\']+)["\']', 'api_key'),
            (r'secret_key\s*=\s*["\']([^"\']+)["\']', 'secret_key'),
            (r'secret\s*=\s*["\']([^"\']+)["\']', 'secret'),
            (r'token\s*=\s*["\']([^"\']+)["\']', 'token'),
        ]
        
        for pattern, var_name in secret_patterns:
            if re.search(pattern, fixed, re.IGNORECASE):
                replacement = f'{var_name} = os.environ.get("{var_name.upper()}", "")'
                fixed = re.sub(pattern, replacement, fixed, flags=re.IGNORECASE)
                warnings.append(f"已将硬编码的{var_name}替换为环境变量")
        
        if fixed == content:
            return FixStatus.NEEDS_MANUAL_REVIEW, content, 0.5, "未检测到需要修复的敏感数据", warnings
        
        if 'os.environ' in fixed and 'import os' not in fixed:
            lines = fixed.split('\n')
            lines.insert(0, 'import os')
            fixed = '\n'.join(lines)
        
        return FixStatus.SUCCESS, fixed, 0.85, "敏感数据已替换为环境变量", warnings

    def _fix_path_traversal(self, issue: Issue, content: str) -> Tuple[FixStatus, str, float, str, List[str]]:
        warnings = []
        warnings.append("路径遍历修复需要手动验证")
        return FixStatus.NEEDS_MANUAL_REVIEW, content, 0.6, "路径遍历修复需要手动审查", warnings

    def _fix_insecure_deserialize(self, issue: Issue, content: str) -> Tuple[FixStatus, str, float, str, List[str]]:
        warnings = []
        fixed = content
        
        yaml_load_pattern = r'yaml\.load\s*\(([^)]+)\)'
        if re.search(yaml_load_pattern, fixed):
            fixed = re.sub(yaml_load_pattern, r'yaml.load(\1, Loader=yaml.SafeLoader)', fixed)
            warnings.append("已使用 yaml.SafeLoader")
        
        if fixed == content:
            return FixStatus.NEEDS_MANUAL_REVIEW, content, 0.5, "不安全的反序列化需要手动审查", warnings
        
        return FixStatus.SUCCESS, fixed, 0.85, "反序列化已加固", warnings

    def _fix_ssl_issue(self, issue: Issue, content: str) -> Tuple[FixStatus, str, float, str, List[str]]:
        warnings = []
        fixed = content
        
        fixed = fixed.replace('ssl._create_unverified_context', 'ssl.create_default_context()')
        fixed = re.sub(r'verify\s*=\s*False', 'verify=True', fixed)
        
        if fixed == content:
            return FixStatus.NEEDS_MANUAL_REVIEW, content, 0.5, "SSL问题需要手动审查", warnings
        
        warnings.append("已启用SSL证书验证")
        return FixStatus.SUCCESS, fixed, 0.9, "SSL安全问题已修复", warnings

    def _fix_weak_crypto(self, issue: Issue, content: str) -> Tuple[FixStatus, str, float, str, List[str]]:
        warnings = []
        warnings.append("弱加密算法需要手动替换为更强的算法")
        return FixStatus.NEEDS_MANUAL_REVIEW, content, 0.6, "弱加密算法需要手动审查", warnings


class TestFailureFixStrategy(FixStrategy):
    """测试失败修复策略"""

    name = "test_failure_fix"
    description = "修复测试失败相关问题"
    applicable_categories = [
        IssueCategory.TEST_FAILURE,
        IssueCategory.TEST_ASSERTION_ERROR,
        IssueCategory.TEST_IMPORT_ERROR,
        IssueCategory.TEST_FIXTURE_ERROR,
    ]
    priority = StrategyPriority.HIGH

    def can_apply(self, issue: Issue) -> bool:
        return issue.category in self.applicable_categories

    def _do_apply(self, issue: Issue, content: str) -> Tuple[FixStatus, str, float, str, List[str]]:
        if issue.category == IssueCategory.TEST_ASSERTION_ERROR:
            return self._fix_assertion_error(issue, content)
        elif issue.category == IssueCategory.TEST_IMPORT_ERROR:
            return self._fix_test_import(issue, content)
        elif issue.category == IssueCategory.TEST_FIXTURE_ERROR:
            return self._fix_fixture_error(issue, content)
        elif issue.category == IssueCategory.TEST_FAILURE:
            return self._fix_general_test_failure(issue, content)
        
        return FixStatus.SKIPPED, content, 0.0, "不支持的测试问题类型", []

    def _fix_assertion_error(self, issue: Issue, content: str) -> Tuple[FixStatus, str, float, str, List[str]]:
        warnings = []
        fixed = content
        
        if issue.context.get("assertion_type") == "simple_comparison":
            fixed = self._upgrade_assertion(content, issue)
            warnings.append("已升级断言为更具体的断言方法")
        
        if issue.context.get("assertion_type") == "no_message":
            fixed = self._add_assertion_message(content, issue)
            warnings.append("已为断言添加错误消息")
        
        if fixed == content:
            return FixStatus.NEEDS_MANUAL_REVIEW, content, 0.5, "断言修复需要手动审查", warnings
        
        return FixStatus.SUCCESS, fixed, 0.8, "断言已改进", warnings

    def _upgrade_assertion(self, content: str, issue: Issue) -> str:
        lines = content.split('\n')
        line_idx = issue.line_number - 1
        
        if 0 <= line_idx < len(lines):
            line = lines[line_idx]
            
            if 'assert ' in line and '==' in line:
                parts = line.split('assert ')
                if len(parts) == 2:
                    assertion_part = parts[1].strip()
                    if '==' in assertion_part:
                        left, right = assertion_part.split('==', 1)
                        left = left.strip()
                        right = right.strip().rstrip(',')
                        indent = len(line) - len(line.lstrip())
                        lines[line_idx] = ' ' * indent + f'self.assertEqual({left}, {right})'
            elif 'assert ' in line and '!=' in line:
                parts = line.split('assert ')
                if len(parts) == 2:
                    assertion_part = parts[1].strip()
                    if '!=' in assertion_part:
                        left, right = assertion_part.split('!=', 1)
                        left = left.strip()
                        right = right.strip().rstrip(',')
                        indent = len(line) - len(line.lstrip())
                        lines[line_idx] = ' ' * indent + f'self.assertNotEqual({left}, {right})'
        
        return '\n'.join(lines)

    def _add_assertion_message(self, content: str, issue: Issue) -> str:
        lines = content.split('\n')
        line_idx = issue.line_number - 1
        
        if 0 <= line_idx < len(lines):
            line = lines[line_idx]
            
            if 'assert ' in line and not line.strip().endswith(')'):
                if not re.search(r',\s*[\'"].*[\'"]\s*$', line):
                    func_name = issue.context.get("function_name", "unknown")
                    indent = len(line) - len(line.lstrip())
                    if line.rstrip().endswith(','):
                        lines[line_idx] = line.rstrip() + f" f'Assertion failed in {func_name}'"
                    else:
                        lines[line_idx] = line.rstrip() + f", f'Assertion failed in {func_name}'"
        
        return '\n'.join(lines)

    def _fix_test_import(self, issue: Issue, content: str) -> Tuple[FixStatus, str, float, str, List[str]]:
        warnings = []
        missing_module = issue.context.get("missing_module", "")
        
        if not missing_module:
            return FixStatus.NEEDS_MANUAL_REVIEW, content, 0.5, "无法确定缺失的测试模块", warnings
        
        test_imports = {
            'pytest': 'import pytest',
            'unittest': 'import unittest',
            'mock': 'from unittest.mock import Mock, MagicMock, patch',
            'patch': 'from unittest.mock import patch',
            'MagicMock': 'from unittest.mock import MagicMock',
        }
        
        import_statement = test_imports.get(missing_module, f"import {missing_module}")
        
        lines = content.split('\n')
        import_lines = []
        code_lines = []
        
        for line in lines:
            if line.strip().startswith(('import ', 'from ')):
                import_lines.append(line)
            else:
                code_lines.append(line)
        
        if import_statement not in [l.strip() for l in import_lines]:
            import_lines.append(import_statement)
            import_lines.sort()
        
        fixed = '\n'.join(import_lines) + '\n\n' + '\n'.join(code_lines)
        warnings.append(f"已添加测试导入: {import_statement}")
        
        return FixStatus.SUCCESS, fixed, 0.9, f"测试导入已添加", warnings

    def _fix_fixture_error(self, issue: Issue, content: str) -> Tuple[FixStatus, str, float, str, List[str]]:
        warnings = []
        func_name = issue.context.get("function_name", "")
        
        if not func_name:
            return FixStatus.NEEDS_MANUAL_REVIEW, content, 0.5, "无法确定fixture函数名", warnings
        
        if func_name.startswith('test_'):
            fixed = self._rename_fixture(content, func_name)
            warnings.append(f"已重命名fixture函数: {func_name}")
            return FixStatus.SUCCESS, fixed, 0.85, "fixture函数已重命名", warnings
        
        return FixStatus.NEEDS_MANUAL_REVIEW, content, 0.5, "fixture问题需要手动审查", warnings

    def _rename_fixture(self, content: str, old_name: str) -> str:
        new_name = old_name.replace('test_', 'fixture_')
        if new_name == old_name:
            new_name = f"fixture_{old_name}"
        
        fixed = content.replace(f"def {old_name}(", f"def {new_name}(")
        fixed = fixed.replace(f"@pytest.fixture\ndef {old_name}", f"@pytest.fixture\ndef {new_name}")
        
        return fixed

    def _fix_general_test_failure(self, issue: Issue, content: str) -> Tuple[FixStatus, str, float, str, List[str]]:
        warnings = []
        warnings.append("测试失败可能需要手动检查测试逻辑")
        return FixStatus.NEEDS_MANUAL_REVIEW, content, 0.6, "测试失败需要手动审查", warnings


class CodeSmellFixStrategy(FixStrategy):
    """代码异味修复策略"""

    name = "code_smell_fix"
    description = "修复代码异味问题"
    applicable_categories = [
        IssueCategory.CODE_SMELL_DUPLICATION,
        IssueCategory.CODE_SMELL_LONG_METHOD,
        IssueCategory.CODE_SMELL_LARGE_CLASS,
        IssueCategory.CODE_SMELL_LONG_PARAMETER_LIST,
        IssueCategory.CODE_SMELL_DEAD_CODE,
        IssueCategory.CODE_SMELL_MAGIC_NUMBER,
        IssueCategory.CODE_SMELL_COMPLEXITY,
        IssueCategory.CODE_SMELL_NESTING,
    ]
    priority = StrategyPriority.MEDIUM

    def can_apply(self, issue: Issue) -> bool:
        return issue.category in self.applicable_categories

    def _do_apply(self, issue: Issue, content: str) -> Tuple[FixStatus, str, float, str, List[str]]:
        if issue.category == IssueCategory.CODE_SMELL_MAGIC_NUMBER:
            return self._fix_magic_number(issue, content)
        elif issue.category == IssueCategory.CODE_SMELL_DEAD_CODE:
            return self._fix_dead_code(issue, content)
        elif issue.category == IssueCategory.CODE_SMELL_LONG_PARAMETER_LIST:
            return self._fix_long_parameter_list(issue, content)
        elif issue.category == IssueCategory.CODE_SMELL_DUPLICATION:
            return self._fix_duplication(issue, content)
        
        return FixStatus.NEEDS_MANUAL_REVIEW, content, 0.5, "此代码异味需要手动重构", []

    def _fix_magic_number(self, issue: Issue, content: str) -> Tuple[FixStatus, str, float, str, List[str]]:
        warnings = []
        value = issue.context.get("value")
        
        if value is None:
            return FixStatus.NEEDS_MANUAL_REVIEW, content, 0.5, "无法确定魔法数字值", warnings
        
        lines = content.split('\n')
        line_idx = issue.line_number - 1
        
        if 0 <= line_idx < len(lines):
            line = lines[line_idx]
            
            constant_name = self._suggest_constant_name(value)
            
            if constant_name:
                insert_idx = 0
                for i, l in enumerate(lines):
                    if l.strip() and not l.strip().startswith(('#', '"""', "'''")):
                        insert_idx = i
                        break
                
                constant_line = f"{constant_name} = {value}\n"
                lines.insert(insert_idx, constant_line)
                
                pattern = r'\b' + str(value) + r'\b'
                lines[line_idx + 1] = re.sub(pattern, constant_name, lines[line_idx + 1], count=1)
                
                warnings.append(f"已将魔法数字 {value} 提取为常量 {constant_name}")
                return FixStatus.SUCCESS, '\n'.join(lines), 0.75, "魔法数字已提取为常量", warnings
        
        return FixStatus.NEEDS_MANUAL_REVIEW, content, 0.5, "魔法数字修复需要手动审查", warnings

    def _suggest_constant_name(self, value: Any) -> Optional[str]:
        if isinstance(value, int):
            if value == 100:
                return "PERCENTAGE"
            elif value == 1000:
                return "MILLIS_PER_SECOND"
            elif value == 360:
                return "DEGREES_IN_CIRCLE"
            elif value == 24:
                return "HOURS_PER_DAY"
            elif value == 60:
                return "SECONDS_PER_MINUTE"
            elif value > 0:
                return f"CONSTANT_{value}"
        elif isinstance(value, float):
            return f"CONSTANT_{str(value).replace('.', '_')}"
        
        return None

    def _fix_dead_code(self, issue: Issue, content: str) -> Tuple[FixStatus, str, float, str, List[str]]:
        warnings = []
        func_name = issue.context.get("function_name", "")
        
        if not func_name:
            return FixStatus.NEEDS_MANUAL_REVIEW, content, 0.5, "无法确定未使用的函数", warnings
        
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return FixStatus.FAILED, content, 0.3, "代码存在语法错误", warnings
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == func_name:
                lines = content.split('\n')
                start_line = node.lineno - 1
                end_line = node.end_lineno if hasattr(node, 'end_lineno') else start_line + 1
                
                del lines[start_line:end_line]
                
                fixed = '\n'.join(lines)
                warnings.append(f"已移除未使用的函数: {func_name}")
                return FixStatus.SUCCESS, fixed, 0.7, f"未使用的函数已移除", warnings
        
        return FixStatus.NEEDS_MANUAL_REVIEW, content, 0.5, "未找到要移除的函数", warnings

    def _fix_long_parameter_list(self, issue: Issue, content: str) -> Tuple[FixStatus, str, float, str, List[str]]:
        warnings = []
        func_name = issue.context.get("function_name", "")
        param_count = issue.context.get("param_count", 0)
        
        if not func_name or param_count <= 5:
            return FixStatus.NEEDS_MANUAL_REVIEW, content, 0.5, "参数列表修复需要手动重构", warnings
        
        warnings.append(f"函数 '{func_name}' 有 {param_count} 个参数，建议使用参数对象重构")
        return FixStatus.NEEDS_MANUAL_REVIEW, content, 0.6, "参数列表过长需要手动重构", warnings

    def _fix_duplication(self, issue: Issue, content: str) -> Tuple[FixStatus, str, float, str, List[str]]:
        warnings = []
        warnings.append("代码重复需要手动提取为独立函数")
        return FixStatus.NEEDS_MANUAL_REVIEW, content, 0.5, "代码重复需要手动重构", warnings


class DocumentationFixStrategy(FixStrategy):
    """文档问题修复策略"""

    name = "documentation_fix"
    description = "修复文档相关问题"
    applicable_categories = [
        IssueCategory.DOCUMENTATION_MISSING,
        IssueCategory.DOCUMENTATION_INCOMPLETE,
        IssueCategory.DOCUMENTATION_OUTDATED,
        IssueCategory.DOCUMENTATION_FORMAT_ERROR,
    ]
    priority = StrategyPriority.LOW

    def can_apply(self, issue: Issue) -> bool:
        return issue.category in self.applicable_categories

    def _do_apply(self, issue: Issue, content: str) -> Tuple[FixStatus, str, float, str, List[str]]:
        if issue.category == IssueCategory.DOCUMENTATION_MISSING:
            return self._fix_missing_docstring(issue, content)
        elif issue.category == IssueCategory.DOCUMENTATION_INCOMPLETE:
            return self._fix_incomplete_docstring(issue, content)
        
        return FixStatus.NEEDS_MANUAL_REVIEW, content, 0.5, "文档问题需要手动完善", []

    def _fix_missing_docstring(self, issue: Issue, content: str) -> Tuple[FixStatus, str, float, str, List[str]]:
        warnings = []
        
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return FixStatus.FAILED, content, 0.3, "代码存在语法错误", warnings
        
        func_name = issue.context.get("function_name")
        class_name = issue.context.get("class_name")
        
        if func_name:
            fixed = self._add_function_docstring(content, tree, func_name)
            warnings.append(f"已为函数 '{func_name}' 添加文档字符串模板")
        elif class_name:
            fixed = self._add_class_docstring(content, tree, class_name)
            warnings.append(f"已为类 '{class_name}' 添加文档字符串模板")
        else:
            fixed = self._add_module_docstring(content, tree)
            warnings.append("已为模块添加文档字符串模板")
        
        if fixed == content:
            return FixStatus.NEEDS_MANUAL_REVIEW, content, 0.5, "无法添加文档字符串", warnings
        
        return FixStatus.SUCCESS, fixed, 0.7, "文档字符串已添加", warnings

    def _add_function_docstring(self, content: str, tree: ast.AST, func_name: str) -> str:
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == func_name:
                lines = content.split('\n')
                line_idx = node.lineno - 1
                
                if 0 <= line_idx < len(lines):
                    line = lines[line_idx]
                    indent = len(line) - len(line.lstrip())
                    
                    params = [arg.arg for arg in node.args.args if arg.arg not in ('self', 'cls')]
                    
                    docstring_lines = [' ' * (indent + 4) + '"""']
                    docstring_lines.append(' ' * (indent + 4) + f'{func_name} 函数说明')
                    docstring_lines.append(' ' * (indent + 4) + '')
                    
                    if params:
                        docstring_lines.append(' ' * (indent + 4) + 'Args:')
                        for param in params:
                            docstring_lines.append(' ' * (indent + 8) + f'{param}: 参数说明')
                        docstring_lines.append(' ' * (indent + 4) + '')
                    
                    if node.returns:
                        docstring_lines.append(' ' * (indent + 4) + 'Returns:')
                        docstring_lines.append(' ' * (indent + 8) + '返回值说明')
                        docstring_lines.append(' ' * (indent + 4) + '')
                    
                    docstring_lines.append(' ' * (indent + 4) + '"""')
                    
                    insert_idx = line_idx + 1
                    for i, docline in enumerate(docstring_lines):
                        lines.insert(insert_idx + i, docline)
                    
                    return '\n'.join(lines)
        
        return content

    def _add_class_docstring(self, content: str, tree: ast.AST, class_name: str) -> str:
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                lines = content.split('\n')
                line_idx = node.lineno - 1
                
                if 0 <= line_idx < len(lines):
                    line = lines[line_idx]
                    indent = len(line) - len(line.lstrip())
                    
                    docstring_lines = [
                        ' ' * (indent + 4) + '"""',
                        ' ' * (indent + 4) + f'{class_name} 类说明',
                        ' ' * (indent + 4) + '',
                        ' ' * (indent + 4) + 'Attributes:',
                        ' ' * (indent + 8) + '属性说明',
                        ' ' * (indent + 4) + '"""'
                    ]
                    
                    insert_idx = line_idx + 1
                    for i, docline in enumerate(docstring_lines):
                        lines.insert(insert_idx + i, docline)
                    
                    return '\n'.join(lines)
        
        return content

    def _add_module_docstring(self, content: str, tree: ast.AST) -> str:
        if ast.get_docstring(tree):
            return content
        
        lines = content.split('\n')
        
        docstring_lines = [
            '"""',
            '模块说明',
            '',
            '此模块提供以下功能:',
            '- 功能1',
            '- 功能2',
            '"""',
            ''
        ]
        
        insert_idx = 0
        for i, line in enumerate(lines):
            if line.strip().startswith('#') or line.strip().startswith('from __future__'):
                insert_idx = i + 1
            else:
                break
        
        for i, docline in enumerate(docstring_lines):
            lines.insert(insert_idx + i, docline)
        
        return '\n'.join(lines)

    def _fix_incomplete_docstring(self, issue: Issue, content: str) -> Tuple[FixStatus, str, float, str, List[str]]:
        warnings = []
        param = issue.context.get("parameter")
        func_name = issue.context.get("function_name")
        
        if param and func_name:
            fixed = self._add_param_doc(content, func_name, param)
            warnings.append(f"已为参数 '{param}' 添加文档说明")
            return FixStatus.SUCCESS, fixed, 0.7, "参数文档已补充", warnings
        
        return FixStatus.NEEDS_MANUAL_REVIEW, content, 0.5, "文档完善需要手动处理", warnings

    def _add_param_doc(self, content: str, func_name: str, param: str) -> str:
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return content
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == func_name:
                docstring = ast.get_docstring(node)
                if docstring and 'Args:' in docstring:
                    lines = content.split('\n')
                    
                    for i, line in enumerate(lines):
                        if 'Args:' in line:
                            indent = len(line) - len(line.lstrip())
                            new_param_line = ' ' * (indent + 4) + f'{param}: 参数说明'
                            lines.insert(i + 1, new_param_line)
                            break
                    
                    return '\n'.join(lines)
        
        return content


class FixStrategyLibrary:
    """修复策略库"""

    def __init__(self):
        self._strategies: Dict[str, FixStrategy] = {}
        self._category_map: Dict[IssueCategory, List[str]] = {}
        self._result_counter = 0
        self._register_builtin_strategies()

    def _register_builtin_strategies(self) -> None:
        strategies = [
            SyntaxFixStrategy(),
            ImportFixStrategy(),
            TypeFixStrategy(),
            SecurityFixStrategy(),
            TestFailureFixStrategy(),
            CodeSmellFixStrategy(),
            DocumentationFixStrategy(),
        ]
        
        for strategy in strategies:
            self.register_strategy(strategy)

    def register_strategy(self, strategy: FixStrategy) -> None:
        self._strategies[strategy.name] = strategy
        
        for category in strategy.applicable_categories:
            if category not in self._category_map:
                self._category_map[category] = []
            self._category_map[category].append(strategy.name)
        
        logger.info(f"已注册策略: {strategy.name}")

    def get_strategy(self, name: str) -> Optional[FixStrategy]:
        return self._strategies.get(name)

    def get_strategies_for_issue(self, issue: Issue) -> List[FixStrategy]:
        strategies = []
        
        if issue.category in self._category_map:
            strategy_names = self._category_map[issue.category]
            strategies = [self._strategies[name] for name in strategy_names if name in self._strategies]
        
        strategies.sort(key=lambda s: s.priority.value)
        return strategies

    def can_fix(self, issue: Issue) -> bool:
        strategies = self.get_strategies_for_issue(issue)
        return any(s.can_apply(issue) for s in strategies)

    def apply_fix(self, issue: Issue, content: str, strategy_name: Optional[str] = None) -> Optional[FixResult]:
        if strategy_name:
            strategy = self.get_strategy(strategy_name)
            if strategy and strategy.can_apply(issue):
                return strategy.apply(issue, content)
            return None
        
        strategies = self.get_strategies_for_issue(issue)
        
        for strategy in strategies:
            if strategy.can_apply(issue):
                result = strategy.apply(issue, content)
                if result.status in [FixStatus.SUCCESS, FixStatus.PARTIAL]:
                    return result
        
        return None

    def apply_fix_batch(self, issues: List[Issue], content: str) -> Tuple[str, List[FixResult]]:
        results = []
        fixed_content = content
        
        sorted_issues = sorted(issues, key=lambda i: i.line_number, reverse=True)
        
        for issue in sorted_issues:
            result = self.apply_fix(issue, fixed_content)
            if result:
                results.append(result)
                if result.status in [FixStatus.SUCCESS, FixStatus.PARTIAL]:
                    fixed_content = result.fixed_code
        
        return fixed_content, results

    def get_all_strategies(self) -> List[FixStrategy]:
        return list(self._strategies.values())

    def get_metrics(self) -> Dict[str, StrategyMetrics]:
        return {name: strategy.get_metrics() for name, strategy in self._strategies.items()}


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="修复策略库")
    parser.add_argument("--list", action="store_true", help="列出所有策略")
    parser.add_argument("--metrics", action="store_true", help="显示策略指标")
    
    args = parser.parse_args()
    
    library = FixStrategyLibrary()
    
    if args.list:
        print("\n已注册策略:")
        for strategy in library.get_all_strategies():
            print(f"  - {strategy.name}: {strategy.description}")
            print(f"    优先级: {strategy.priority.name}")
            print(f"    适用类别: {[c.name for c in strategy.applicable_categories]}")
    
    elif args.metrics:
        metrics = library.get_metrics()
        for name, m in metrics.items():
            print(f"\n策略: {name}")
            print(f"  总应用次数: {m.total_applications}")
            print(f"  成功次数: {m.successful_applications}")
            print(f"  成功率: {m.success_rate:.1%}")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
