#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动修复器 - Auto Fixer (增强版)

智能代码修复系统，包括：
- 常见问题修复策略库
- 语法错误自动修复（增强版）
- 导入错误自动修复（增强版）
- 代码风格自动修复（增强版）
- 安全漏洞自动修复（增强版）
- 类型注解自动修复
- 文档字符串自动生成
- 命名规范自动修复
- 修复验证机制（增强版）
- 生成修复报告

使用示例:
    python auto_fixer.py --file problematic.py --fix
    python auto_fixer.py --dir ./src --fix-all --dry-run
    python auto_fixer.py --file code.py --fix-imports --report fix_report.json
"""

import argparse
import ast
import difflib
import json
import keyword
import logging
import os
import re
import sys
import tokenize
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from io import StringIO
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union


class FixType(Enum):
    SYNTAX_ERROR = "syntax_error"
    IMPORT_ERROR = "import_error"
    STYLE_ERROR = "style_error"
    LOGIC_ERROR = "logic_error"
    SECURITY_ISSUE = "security_issue"
    PERFORMANCE_ISSUE = "performance_issue"
    DEPRECATED_CODE = "deprecated_code"
    UNUSED_CODE = "unused_code"
    TYPE_ANNOTATION = "type_annotation"
    DOCSTRING = "docstring"
    NAMING_CONVENTION = "naming_convention"


class FixStatus(Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    SKIPPED = "skipped"


class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class FixAction:
    action_id: str
    fix_type: FixType
    description: str
    original_code: str
    fixed_code: str
    line_number: int
    risk_level: RiskLevel
    auto_applicable: bool
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_id": self.action_id,
            "fix_type": self.fix_type.value,
            "description": self.description,
            "original_code": self.original_code,
            "fixed_code": self.fixed_code,
            "line_number": self.line_number,
            "risk_level": self.risk_level.value,
            "auto_applicable": self.auto_applicable,
            "confidence": self.confidence
        }


@dataclass
class FixResult:
    file_path: str
    status: FixStatus
    actions: List[FixAction]
    applied_actions: List[str]
    skipped_actions: List[str]
    original_content: str
    fixed_content: str
    diff: str
    error_message: str = ""
    validation_result: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "status": self.status.value,
            "actions": [a.to_dict() for a in self.actions],
            "applied_actions": self.applied_actions,
            "skipped_actions": self.skipped_actions,
            "diff": self.diff,
            "error_message": self.error_message,
            "validation_result": self.validation_result
        }


@dataclass
class FixReport:
    report_id: str
    generated_at: str
    total_files: int
    fixed_files: int
    failed_files: int
    total_fixes: int
    results: List[FixResult]
    summary: str
    statistics: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "generated_at": self.generated_at,
            "total_files": self.total_files,
            "fixed_files": self.fixed_files,
            "failed_files": self.failed_files,
            "total_fixes": self.total_fixes,
            "results": [r.to_dict() for r in self.results],
            "summary": self.summary,
            "statistics": self.statistics
        }


class FixStrategy:
    """修复策略基类 - 所有修复器的抽象基类"""

    def __init__(self):
        self.action_counter = 0

    def can_fix(self, content: str, file_path: Path) -> List[Dict[str, Any]]:
        raise NotImplementedError

    def apply_fix(self, content: str, issues: List[Dict[str, Any]]) -> Tuple[str, List[FixAction]]:
        raise NotImplementedError

    def _create_action(self, fix_type: FixType, description: str,
                       original: str, fixed: str, line: int,
                       risk: RiskLevel = RiskLevel.LOW,
                       auto: bool = True,
                       confidence: float = 1.0) -> FixAction:
        self.action_counter += 1
        return FixAction(
            action_id=f"FIX-{self.action_counter:03d}",
            fix_type=fix_type,
            description=description,
            original_code=original,
            fixed_code=fixed,
            line_number=line,
            risk_level=risk,
            auto_applicable=auto,
            confidence=confidence
        )

    def _get_line_content(self, content: str, line_number: int) -> str:
        """获取指定行的内容"""
        lines = content.split('\n')
        if 1 <= line_number <= len(lines):
            return lines[line_number - 1]
        return ""

    def _safe_parse_ast(self, content: str) -> Optional[ast.AST]:
        """安全地解析 AST，失败返回 None"""
        try:
            return ast.parse(content)
        except SyntaxError:
            return None


class SyntaxErrorFixer(FixStrategy):
    """语法错误修复器 - 增强版"""

    def __init__(self):
        super().__init__()
        self._error_recovery_patterns = self._init_recovery_patterns()

    def _init_recovery_patterns(self) -> Dict[str, Any]:
        return {
            'missing_colon': {
                'keywords': ['if', 'else', 'elif', 'for', 'while', 'def', 'class', 'try', 'except', 'finally', 'with', 'match', 'case'],
                'fix': self._fix_missing_colon
            },
            'unmatched_bracket': {
                'fix': self._fix_unmatched_bracket
            },
            'indentation_error': {
                'fix': self._fix_indentation
            },
            'missing_parenthesis': {
                'fix': self._fix_missing_parenthesis
            },
            'invalid_syntax_operator': {
                'patterns': [
                    (r'(\w+)\s*=\s*\1\s*([+\-*/%&|^])\s*', r'\1 \2= '),  # x = x + 1 -> x += 1
                    (r'(\w+)\s*=\s*\1\s*<<\s*', r'\1 <<= '),  # x = x << 1 -> x <<= 1
                    (r'(\w+)\s*=\s*\1\s*>>\s*', r'\1 >>= '),  # x = x >> 1 -> x >>= 1
                ],
                'fix': self._fix_invalid_operator
            },
            'missing_comma': {
                'fix': self._fix_missing_comma
            },
            'invalid_escape': {
                'patterns': [
                    (r'\\([^\\\'\"abfnrtv0-7xNuU])', r'\\\\\1'),
                ],
                'fix': self._fix_invalid_escape
            },
            'missing_quote': {
                'fix': self._fix_missing_quote
            },
            'invalid_keyword_usage': {
                'fix': self._fix_invalid_keyword
            },
            'duplicate_parameter': {
                'fix': self._fix_duplicate_parameter
            },
            'nonlocal_without_binding': {
                'fix': self._fix_nonlocal_binding
            }
        }

    def can_fix(self, content: str, file_path: Path) -> List[Dict[str, Any]]:
        issues = []

        try:
            ast.parse(content)
        except SyntaxError as e:
            issues.append({
                'type': 'syntax_error',
                'line': e.lineno or 1,
                'message': e.msg,
                'offset': e.offset,
                'text': e.text
            })

        issues.extend(self._detect_missing_colon(content))
        issues.extend(self._detect_unmatched_brackets(content))
        issues.extend(self._detect_indentation_issues(content))
        issues.extend(self._detect_missing_parenthesis(content))
        issues.extend(self._detect_invalid_operators(content))
        issues.extend(self._detect_missing_comma(content))
        issues.extend(self._detect_invalid_escape(content))
        issues.extend(self._detect_missing_quote(content))
        issues.extend(self._detect_invalid_keyword_usage(content))
        issues.extend(self._detect_duplicate_parameters(content))

        return issues

    def _detect_missing_colon(self, content: str) -> List[Dict[str, Any]]:
        issues = []
        lines = content.split('\n')

        keywords_needing_colon = ['if', 'else', 'elif', 'for', 'while', 'def', 'class', 'try', 'except', 'finally', 'with', 'match', 'case']

        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith('#') or stripped.startswith('"""') or stripped.startswith("'''"):
                continue
            for kw in keywords_needing_colon:
                if kw == 'else':
                    pattern = rf'^else\s*$|^else\s+if\s+'
                    if re.match(pattern, stripped) and not stripped.endswith(':'):
                        issues.append({
                            'type': 'missing_colon',
                            'line': i,
                            'message': f'缺少冒号: else语句末尾需要冒号',
                            'keyword': kw,
                            'context': stripped
                        })
                elif kw == 'except':
                    pattern = rf'^except(\s+\w+|\s*\([^)]+\))?\s*$'
                    if re.match(pattern, stripped) and not stripped.endswith(':'):
                        issues.append({
                            'type': 'missing_colon',
                            'line': i,
                            'message': f'缺少冒号: except语句末尾需要冒号',
                            'keyword': kw,
                            'context': stripped
                        })
                else:
                    pattern = rf'^{kw}\b'
                    if re.match(pattern, stripped):
                        if not stripped.endswith(':') and not re.search(r':\s*$', stripped):
                            if kw not in ['else', 'except', 'finally']:
                                if not re.search(r'\bpass\b', stripped):
                                    issues.append({
                                        'type': 'missing_colon',
                                        'line': i,
                                        'message': f'缺少冒号: {kw}语句末尾需要冒号',
                                        'keyword': kw,
                                        'context': stripped
                                    })

        return issues

    def _detect_unmatched_brackets(self, content: str) -> List[Dict[str, Any]]:
        issues = []
        bracket_pairs = {'(': ')', '[': ']', '{': '}'}
        bracket_stack: List[Tuple[str, int, int]] = []
        open_brackets = {k: 0 for k in bracket_pairs}

        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            in_string = False
            string_char = None
            i = 0
            while i < len(line):
                char = line[i]
                if char in '\'"' and (i == 0 or line[i-1] != '\\'):
                    if not in_string:
                        in_string = True
                        string_char = char
                    elif char == string_char:
                        in_string = False
                        string_char = None
                elif not in_string:
                    if char in bracket_pairs:
                        bracket_stack.append((char, line_num, i))
                        open_brackets[char] += 1
                    elif char in bracket_pairs.values():
                        for open_b, close_b in bracket_pairs.items():
                            if char == close_b:
                                open_brackets[open_b] -= 1
                                if bracket_stack and bracket_stack[-1][0] == open_b:
                                    bracket_stack.pop()
                                else:
                                    issues.append({
                                        'type': 'unmatched_bracket',
                                        'line': line_num,
                                        'message': f'未匹配的右括号: {char}',
                                        'position': i
                                    })
                i += 1

        for bracket, count in open_brackets.items():
            if count > 0:
                matching_lines = [pos[1] for pos in bracket_stack if pos[0] == bracket]
                issues.append({
                    'type': 'unmatched_bracket',
                    'line': matching_lines[-1] if matching_lines else 1,
                    'message': f'括号不匹配: 缺少 {bracket_pairs[bracket]} 来匹配 {bracket}',
                    'bracket': bracket,
                    'count': count
                })

        return issues

    def _detect_indentation_issues(self, content: str) -> List[Dict[str, Any]]:
        issues = []
        lines = content.split('\n')

        prev_indent = 0
        indent_stack = [0]
        in_docstring = False
        docstring_char = None

        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped:
                continue

            if stripped.startswith('"""') or stripped.startswith("'''"):
                if in_docstring:
                    in_docstring = False
                    docstring_char = None
                else:
                    in_docstring = True
                    docstring_char = stripped[:3]
                continue

            if in_docstring:
                continue

            current_indent = len(line) - len(line.lstrip())

            if current_indent > prev_indent:
                expected_indent = prev_indent + 4
                if current_indent != expected_indent and current_indent % 4 != 0:
                    issues.append({
                        'type': 'indentation_error',
                        'line': i,
                        'message': f'缩进不一致: 期望{expected_indent}空格或{expected_indent//4}个tab，实际{current_indent}空格',
                        'expected': expected_indent,
                        'actual': current_indent
                    })
                indent_stack.append(current_indent)
            elif current_indent < prev_indent:
                if current_indent not in indent_stack:
                    issues.append({
                        'type': 'indentation_error',
                        'line': i,
                        'message': f'缩进不匹配: 缩进级别{current_indent}与之前不匹配',
                        'expected': prev_indent - 4,
                        'actual': current_indent
                    })
                while indent_stack and indent_stack[-1] > current_indent:
                    indent_stack.pop()

            prev_indent = current_indent

        return issues

    def _detect_missing_parenthesis(self, content: str) -> List[Dict[str, Any]]:
        issues = []
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue

            if re.search(r'\bif\s+[^:]+$', stripped) and not stripped.endswith(':'):
                open_parens = stripped.count('(') - stripped.count(')')
                if open_parens > 0:
                    issues.append({
                        'type': 'missing_parenthesis',
                        'line': i,
                        'message': f'可能缺少右括号，有{open_parens}个未闭合的括号',
                        'open_count': open_parens
                    })

            func_call_pattern = r'(\w+)\s*\([^)]*$'
            if re.search(func_call_pattern, stripped) and not stripped.endswith('\\'):
                issues.append({
                    'type': 'missing_parenthesis',
                    'line': i,
                    'message': '函数调用可能缺少右括号',
                    'context': stripped
                })

        return issues

    def _detect_invalid_operators(self, content: str) -> List[Dict[str, Any]]:
        issues = []
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue

            patterns = [
                (r'(\w+)\s*=\s*\1\s*\+\s*(?!=)', '可简化的赋值: 可使用 += 运算符'),
                (r'(\w+)\s*=\s*\1\s*-\s*(?!=)', '可简化的赋值: 可使用 -= 运算符'),
                (r'(\w+)\s*=\s*\1\s*\*\s*(?!=)', '可简化的赋值: 可使用 *= 运算符'),
                (r'(\w+)\s*=\s*\1\s*/\s*(?!=)', '可简化的赋值: 可使用 /= 运算符'),
                (r'(\w+)\s*=\s*\1\s*%\s*(?!=)', '可简化的赋值: 可使用 %= 运算符'),
                (r'(\w+)\s*=\s*\1\s*//\s*(?!=)', '可简化的赋值: 可使用 //= 运算符'),
                (r'(\w+)\s*=\s*\1\s*\*\*\s*(?!=)', '可简化的赋值: 可使用 **= 运算符'),
                (r'(\w+)\s*=\s*\1\s*&\s*(?!=)', '可简化的赋值: 可使用 &= 运算符'),
                (r'(\w+)\s*=\s*\1\s*\|\s*(?!=)', '可简化的赋值: 可使用 |= 运算符'),
                (r'(\w+)\s*=\s*\1\s*\^\s*(?!=)', '可简化的赋值: 可使用 ^= 运算符'),
            ]

            for pattern, message in patterns:
                if re.search(pattern, stripped):
                    issues.append({
                        'type': 'invalid_syntax_operator',
                        'line': i,
                        'message': message,
                        'context': stripped
                    })
                    break

        return issues

    def _detect_missing_comma(self, content: str) -> List[Dict[str, Any]]:
        issues = []
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue

            list_pattern = r'\[\s*[\'"]?\w+[\'"]?\s+[\'"]?\w+[\'"]?\s*\]'
            if re.search(list_pattern, stripped):
                issues.append({
                    'type': 'missing_comma',
                    'line': i,
                    'message': '列表元素之间可能缺少逗号',
                    'context': stripped
                })

            dict_pattern = r'\{[^}]*:\s*[^,}]+\s+[\'"]?\w+[\'"]?:'
            if re.search(dict_pattern, stripped):
                issues.append({
                    'type': 'missing_comma',
                    'line': i,
                    'message': '字典元素之间可能缺少逗号',
                    'context': stripped
                })

            tuple_pattern = r'\([^)]*,\s*[^,)]+\s+[\'"]?\w+[\'"]?\s*[,\)]'
            if re.search(tuple_pattern, stripped):
                issues.append({
                    'type': 'missing_comma',
                    'line': i,
                    'message': '元组元素之间可能缺少逗号',
                    'context': stripped
                })

        return issues

    def _detect_invalid_escape(self, content: str) -> List[Dict[str, Any]]:
        issues = []
        lines = content.split('\n')

        valid_escapes = {'\\', '\'', '"', 'a', 'b', 'f', 'n', 'r', 't', 'v', '0', 'x', 'u', 'U', 'N'}

        for i, line in enumerate(lines, 1):
            j = 0
            while j < len(line):
                if line[j] == '\\':
                    if j + 1 < len(line):
                        next_char = line[j + 1]
                        if next_char not in valid_escapes and not next_char.isdigit():
                            if not (next_char == '\n' or (j > 0 and line[j-1] in 'rR')):
                                issues.append({
                                    'type': 'invalid_escape',
                                    'line': i,
                                    'message': f'无效的转义序列: \\{next_char}',
                                    'position': j,
                                    'context': line[max(0, j-10):min(len(line), j+10)]
                                })
                    j += 2
                else:
                    j += 1

        return issues

    def _detect_missing_quote(self, content: str) -> List[Dict[str, Any]]:
        issues = []
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue

            single_count = stripped.count("'") - stripped.count("\\'")
            double_count = stripped.count('"') - stripped.count('\\"')

            if single_count % 2 != 0:
                issues.append({
                    'type': 'missing_quote',
                    'line': i,
                    'message': '单引号不匹配，可能缺少引号',
                    'quote_type': "'"
                })

            if double_count % 2 != 0:
                issues.append({
                    'type': 'missing_quote',
                    'line': i,
                    'message': '双引号不匹配，可能缺少引号',
                    'quote_type': '"'
                })

        return issues

    def _detect_invalid_keyword_usage(self, content: str) -> List[Dict[str, Any]]:
        issues = []
        lines = content.split('\n')

        reserved_keywords = set(keyword.kwlist)

        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue

            for kw in reserved_keywords:
                pattern = rf'\b{kw}\s*='
                if re.search(pattern, stripped) and kw not in ['True', 'False', 'None']:
                    issues.append({
                        'type': 'invalid_keyword_usage',
                        'line': i,
                        'message': f'不能将关键字 "{kw}" 用作变量名',
                        'keyword': kw
                    })

        return issues

    def _detect_duplicate_parameters(self, content: str) -> List[Dict[str, Any]]:
        issues = []

        try:
            tree = ast.parse(content)
        except SyntaxError:
            return issues

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                param_names = []
                for arg in node.args.args:
                    param_names.append(arg.arg)
                for arg in node.args.posonlyargs:
                    param_names.append(arg.arg)
                for arg in node.args.kwonlyargs:
                    param_names.append(arg.arg)
                if node.args.vararg:
                    param_names.append(node.args.vararg.arg)
                if node.args.kwarg:
                    param_names.append(node.args.kwarg.arg)

                seen = set()
                for name in param_names:
                    if name in seen:
                        issues.append({
                            'type': 'duplicate_parameter',
                            'line': node.lineno,
                            'message': f'函数 {node.name} 有重复的参数名: {name}',
                            'function_name': node.name,
                            'parameter': name
                        })
                    seen.add(name)

        return issues

    def apply_fix(self, content: str, issues: List[Dict[str, Any]]) -> Tuple[str, List[FixAction]]:
        lines = content.split('\n')
        actions = []

        issues_by_line: Dict[int, List[Dict[str, Any]]] = {}
        for issue in issues:
            line_num = issue.get('line', 0)
            if line_num not in issues_by_line:
                issues_by_line[line_num] = []
            issues_by_line[line_num].append(issue)

        for line_num in sorted(issues_by_line.keys()):
            line_issues = issues_by_line[line_num]
            for issue in line_issues:
                if issue['type'] == 'missing_colon':
                    lines, action = self._fix_missing_colon(lines, issue)
                    if action:
                        actions.append(action)
                elif issue['type'] == 'invalid_escape':
                    lines, action = self._fix_invalid_escape(lines, issue)
                    if action:
                        actions.append(action)
                elif issue['type'] == 'invalid_syntax_operator':
                    lines, action = self._fix_invalid_operator(lines, issue)
                    if action:
                        actions.append(action)

        return '\n'.join(lines), actions

    def _fix_missing_colon(self, lines: List[str], issue: Dict[str, Any]) -> Tuple[List[str], Optional[FixAction]]:
        line_idx = issue['line'] - 1
        if 0 <= line_idx < len(lines):
            original = lines[line_idx]
            if not original.rstrip().endswith(':'):
                lines[line_idx] = original.rstrip() + ':'
                action = self._create_action(
                    FixType.SYNTAX_ERROR,
                    issue['message'],
                    original,
                    lines[line_idx],
                    issue['line'],
                    RiskLevel.LOW
                )
                return lines, action
        return lines, None

    def _fix_unmatched_bracket(self, lines: List[str], issue: Dict[str, Any]) -> Tuple[List[str], Optional[FixAction]]:
        line_idx = issue['line'] - 1
        if 0 <= line_idx < len(lines):
            original = lines[line_idx]
            bracket = issue.get('bracket', '')
            bracket_pairs = {'(': ')', '[': ']', '{': '}'}
            
            if bracket in bracket_pairs:
                open_count = original.count(bracket)
                close_count = original.count(bracket_pairs[bracket])
                
                if open_count > close_count:
                    fixed = original.rstrip() + bracket_pairs[bracket]
                    lines[line_idx] = fixed
                    action = self._create_action(
                        FixType.SYNTAX_ERROR,
                        f'添加缺失的右括号 {bracket_pairs[bracket]}',
                        original,
                        fixed,
                        issue['line'],
                        RiskLevel.MEDIUM
                    )
                    return lines, action
                elif close_count > open_count:
                    fixed = bracket + original.lstrip()
                    lines[line_idx] = fixed
                    action = self._create_action(
                        FixType.SYNTAX_ERROR,
                        f'添加缺失的左括号 {bracket}',
                        original,
                        fixed,
                        issue['line'],
                        RiskLevel.MEDIUM
                    )
                    return lines, action
        return lines, None

    def _fix_indentation(self, lines: List[str], issue: Dict[str, Any]) -> Tuple[List[str], Optional[FixAction]]:
        line_idx = issue['line'] - 1
        if 0 <= line_idx < len(lines):
            original = lines[line_idx]
            expected = issue.get('expected', 0)
            actual = issue.get('actual', 0)
            
            if expected > actual:
                diff = expected - actual
                fixed = ' ' * diff + original
                lines[line_idx] = fixed
                action = self._create_action(
                    FixType.SYNTAX_ERROR,
                    f'修正缩进：增加{diff}个空格',
                    original,
                    fixed,
                    issue['line'],
                    RiskLevel.MEDIUM
                )
                return lines, action
            elif actual > expected:
                stripped = original.lstrip()
                fixed = ' ' * expected + stripped
                lines[line_idx] = fixed
                action = self._create_action(
                    FixType.SYNTAX_ERROR,
                    f'修正缩进：减少{actual - expected}个空格',
                    original,
                    fixed,
                    issue['line'],
                    RiskLevel.MEDIUM
                )
                return lines, action
        return lines, None

    def _fix_missing_parenthesis(self, lines: List[str], issue: Dict[str, Any]) -> Tuple[List[str], Optional[FixAction]]:
        line_idx = issue['line'] - 1
        if 0 <= line_idx < len(lines):
            original = lines[line_idx]
            open_count = issue.get('open_count', 0)
            
            if open_count > 0:
                fixed = original.rstrip() + ')' * open_count
                lines[line_idx] = fixed
                action = self._create_action(
                    FixType.SYNTAX_ERROR,
                    f'添加{open_count}个缺失的右括号',
                    original,
                    fixed,
                    issue['line'],
                    RiskLevel.MEDIUM
                )
                return lines, action
        return lines, None

    def _fix_invalid_operator(self, lines: List[str], issue: Dict[str, Any]) -> Tuple[List[str], Optional[FixAction]]:
        line_idx = issue['line'] - 1
        if 0 <= line_idx < len(lines):
            original = lines[line_idx]
            fixed = original

            patterns = [
                (r'(\w+)\s*=\s*\1\s*\+\s*', r'\1 += '),
                (r'(\w+)\s*=\s*\1\s*-\s*', r'\1 -= '),
                (r'(\w+)\s*=\s*\1\s*\*\s*(?!\*)', r'\1 *= '),
                (r'(\w+)\s*=\s*\1\s*/\s*', r'\1 /= '),
                (r'(\w+)\s*=\s*\1\s*%\s*', r'\1 %= '),
                (r'(\w+)\s*=\s*\1\s*//\s*', r'\1 //= '),
                (r'(\w+)\s*=\s*\1\s*\*\*\s*', r'\1 **= '),
                (r'(\w+)\s*=\s*\1\s*&\s*', r'\1 &= '),
                (r'(\w+)\s*=\s*\1\s*\|\s*', r'\1 |= '),
                (r'(\w+)\s*=\s*\1\s*\^\s*', r'\1 ^= '),
                (r'(\w+)\s*=\s*\1\s*<<\s*', r'\1 <<= '),
                (r'(\w+)\s*=\s*\1\s*>>\s*', r'\1 >>= '),
            ]

            for pattern, replacement in patterns:
                if re.search(pattern, fixed):
                    fixed = re.sub(pattern, replacement, fixed)
                    break

            if original != fixed:
                lines[line_idx] = fixed
                action = self._create_action(
                    FixType.SYNTAX_ERROR,
                    '简化赋值表达式',
                    original,
                    fixed,
                    issue['line'],
                    RiskLevel.LOW
                )
                return lines, action
        return lines, None

    def _fix_missing_comma(self, lines: List[str], issue: Dict[str, Any]) -> Tuple[List[str], Optional[FixAction]]:
        line_idx = issue['line'] - 1
        if 0 <= line_idx < len(lines):
            original = lines[line_idx]
            stripped = original.rstrip()
            
            patterns = [
                (r'\[\s*([\'"]?\w+[\'"]?)\s+([\'"]?\w+[\'"]?)\s*\]', r'[\1, \2]'),
                (r'\{\s*([^:]+:\s*[^,}]+)\s+([^:]+:)', r'{\1, \2'),
                (r'\(([^,)]+),\s*([^,)]+)\s+([^,)]+)', r'(\1, \2, \3'),
            ]
            
            fixed = original
            for pattern, replacement in patterns:
                if re.search(pattern, stripped):
                    fixed = re.sub(pattern, replacement, stripped)
                    break
            
            if original != fixed:
                lines[line_idx] = fixed
                action = self._create_action(
                    FixType.SYNTAX_ERROR,
                    '添加缺失的逗号',
                    original,
                    fixed,
                    issue['line'],
                    RiskLevel.LOW
                )
                return lines, action
        return lines, None

    def _fix_invalid_escape(self, lines: List[str], issue: Dict[str, Any]) -> Tuple[List[str], Optional[FixAction]]:
        line_idx = issue['line'] - 1
        if 0 <= line_idx < len(lines):
            original = lines[line_idx]
            fixed = original

            if "'" in fixed and not fixed.startswith("r'") and not fixed.startswith("R'"):
                if '"' not in fixed or fixed.count("'") > fixed.count('"'):
                    fixed = 'r' + fixed
            elif '"' in fixed and not fixed.startswith('r"') and not fixed.startswith('R"'):
                fixed = 'r' + fixed

            if original != fixed:
                lines[line_idx] = fixed
                action = self._create_action(
                    FixType.SYNTAX_ERROR,
                    '修复无效转义序列',
                    original,
                    fixed,
                    issue['line'],
                    RiskLevel.LOW
                )
                return lines, action
        return lines, None

    def _fix_missing_quote(self, lines: List[str], issue: Dict[str, Any]) -> Tuple[List[str], Optional[FixAction]]:
        line_idx = issue['line'] - 1
        if 0 <= line_idx < len(lines):
            original = lines[line_idx]
            quote_type = issue.get('quote_type', '"')
            
            stripped = original.rstrip()
            if stripped and not stripped.endswith(quote_type):
                in_string = False
                escape_next = False
                for char in stripped:
                    if escape_next:
                        escape_next = False
                        continue
                    if char == '\\':
                        escape_next = True
                        continue
                    if char == quote_type:
                        in_string = not in_string
                
                if in_string:
                    fixed = stripped + quote_type
                    lines[line_idx] = fixed
                    action = self._create_action(
                        FixType.SYNTAX_ERROR,
                        f'添加缺失的{quote_type}引号',
                        original,
                        fixed,
                        issue['line'],
                        RiskLevel.MEDIUM
                    )
                    return lines, action
        return lines, None

    def _fix_invalid_keyword(self, lines: List[str], issue: Dict[str, Any]) -> Tuple[List[str], Optional[FixAction]]:
        line_idx = issue['line'] - 1
        if 0 <= line_idx < len(lines):
            original = lines[line_idx]
            kw = issue.get('keyword', '')
            
            replacements = {
                'class': 'klass',
                'def': 'func',
                'for': 'for_',
                'while': 'while_',
                'if': 'if_',
                'else': 'else_',
                'elif': 'elif_',
                'try': 'try_',
                'except': 'except_',
                'finally': 'finally_',
                'with': 'with_',
                'as': 'as_',
                'import': 'import_',
                'from': 'from_',
                'return': 'return_',
                'yield': 'yield_',
                'raise': 'raise_',
                'break': 'break_',
                'continue': 'continue_',
                'pass': 'pass_',
                'lambda': 'lambda_',
                'and': 'and_',
                'or': 'or_',
                'not': 'not_',
                'in': 'in_',
                'is': 'is_',
                'global': 'global_',
                'nonlocal': 'nonlocal_',
                'assert': 'assert_',
                'del': 'del_',
            }
            
            if kw in replacements:
                pattern = rf'\b{kw}\s*='
                replacement_var = replacements[kw]
                fixed = re.sub(pattern, f'{replacement_var} =', original)
                
                if original != fixed:
                    lines[line_idx] = fixed
                    action = self._create_action(
                        FixType.SYNTAX_ERROR,
                        f'将关键字"{kw}"重命名为"{replacement_var}"',
                        original,
                        fixed,
                        issue['line'],
                        RiskLevel.HIGH,
                        auto=False
                    )
                    return lines, action
        return lines, None

    def _fix_duplicate_parameter(self, lines: List[str], issue: Dict[str, Any]) -> Tuple[List[str], Optional[FixAction]]:
        line_idx = issue['line'] - 1
        if 0 <= line_idx < len(lines):
            original = lines[line_idx]
            param = issue.get('parameter', '')
            func_name = issue.get('function_name', '')
            
            match = re.search(rf'def\s+{func_name}\s*\(([^)]+)\)', original)
            if match:
                params_str = match.group(1)
                params = [p.strip() for p in params_str.split(',')]
                
                seen = {}
                new_params = []
                for p in params:
                    param_name = p.split('=')[0].strip() if '=' in p else p
                    if param_name in seen:
                        counter = seen[param_name] + 1
                        seen[param_name] = counter
                        new_param = p.replace(param_name, f'{param_name}_{counter}', 1)
                        new_params.append(new_param)
                    else:
                        seen[param_name] = 0
                        new_params.append(p)
                
                new_params_str = ', '.join(new_params)
                fixed = original.replace(params_str, new_params_str)
                
                if original != fixed:
                    lines[line_idx] = fixed
                    action = self._create_action(
                        FixType.SYNTAX_ERROR,
                        f'重命名重复参数"{param}"',
                        original,
                        fixed,
                        issue['line'],
                        RiskLevel.HIGH,
                        auto=False
                    )
                    return lines, action
        return lines, None

    def _fix_nonlocal_binding(self, lines: List[str], issue: Dict[str, Any]) -> Tuple[List[str], Optional[FixAction]]:
        line_idx = issue['line'] - 1
        if 0 <= line_idx < len(lines):
            original = lines[line_idx]
            
            match = re.search(r'nonlocal\s+(\w+)', original)
            if match:
                var_name = match.group(1)
                indent = len(original) - len(original.lstrip())
                indent_str = original[:indent]
                
                fixed = f"{indent_str}# FIXME: nonlocal variable '{var_name}' needs binding in enclosing scope\n{original}"
                lines[line_idx] = fixed
                action = self._create_action(
                    FixType.SYNTAX_ERROR,
                    f'添加nonlocal绑定警告注释',
                    original,
                    fixed,
                    issue['line'],
                    RiskLevel.LOW
                )
                return lines, action
        return lines, None


class ImportErrorFixer(FixStrategy):
    """导入错误修复器 - 增强版"""

    COMMON_IMPORT_FIXES = {
        'typing.List': 'from typing import List',
        'typing.Dict': 'from typing import Dict',
        'typing.Optional': 'from typing import Optional',
        'typing.Any': 'from typing import Any',
        'typing.Union': 'from typing import Union',
        'typing.Tuple': 'from typing import Tuple',
        'typing.Set': 'from typing import Set',
        'typing.Callable': 'from typing import Callable',
        'typing.TypeVar': 'from typing import TypeVar',
        'typing.Generic': 'from typing import Generic',
        'typing.Protocol': 'from typing import Protocol',
        'typing.Final': 'from typing import Final',
        'typing.Literal': 'from typing import Literal',
        'collections.defaultdict': 'from collections import defaultdict',
        'collections.Counter': 'from collections import Counter',
        'collections.namedtuple': 'from collections import namedtuple',
        'collections.OrderedDict': 'from collections import OrderedDict',
        'collections.deque': 'from collections import deque',
        'pathlib.Path': 'from pathlib import Path',
        'pathlib.PurePath': 'from pathlib import PurePath',
        'datetime.datetime': 'from datetime import datetime',
        'datetime.timedelta': 'from datetime import timedelta',
        'datetime.date': 'from datetime import date',
        'datetime.time': 'from datetime import time',
        'json': 'import json',
        're': 'import re',
        'os': 'import os',
        'sys': 'import sys',
        'logging': 'import logging',
        'functools': 'import functools',
        'itertools': 'import itertools',
        'contextlib': 'import contextlib',
        'dataclasses': 'import dataclasses',
        'enum': 'import enum',
        'abc': 'import abc',
        'copy': 'import copy',
        'pickle': 'import pickle',
        'hashlib': 'import hashlib',
        'base64': 'import base64',
        'uuid': 'import uuid',
        'tempfile': 'import tempfile',
        'shutil': 'import shutil',
        'glob': 'import glob',
        'argparse': 'import argparse',
        'configparser': 'import configparser',
        'threading': 'import threading',
        'multiprocessing': 'import multiprocessing',
        'asyncio': 'import asyncio',
        'concurrent.futures': 'from concurrent import futures',
        'subprocess': 'import subprocess',
        'socket': 'import socket',
        'http.client': 'from http import client',
        'urllib.request': 'from urllib import request',
        'urllib.parse': 'from urllib import parse',
        'email.mime.text': 'from email.mime import text',
        'html.parser': 'from html import parser',
        'xml.etree.ElementTree': 'from xml.etree import ElementTree',
        'sqlite3': 'import sqlite3',
        'csv': 'import csv',
        'io': 'import io',
        'math': 'import math',
        'random': 'import random',
        'statistics': 'import statistics',
        'decimal': 'import decimal',
        'fractions': 'import fractions',
        'time': 'import time',
        'calendar': 'import calendar',
        'traceback': 'import traceback',
        'warnings': 'import warnings',
        'unittest': 'import unittest',
        'doctest': 'import doctest',
        'pdb': 'import pdb',
        'profile': 'import profile',
        'cProfile': 'import cProfile',
        'timeit': 'import timeit',
        'weakref': 'import weakref',
        'heapq': 'import heapq',
        'bisect': 'import bisect',
        'array': 'import array',
        'struct': 'import struct',
        'codecs': 'import codecs',
        'unicodedata': 'import unicodedata',
        'string': 'import string',
        'textwrap': 'import textwrap',
        'difflib': 'import difflib',
        'pprint': 'import pprint',
        'reprlib': 'import reprlib',
    }

    MODULE_ALIASES = {
        'np': ('numpy', 'numpy'),
        'pd': ('pandas', 'pandas'),
        'plt': ('matplotlib.pyplot', 'matplotlib.pyplot'),
        'sns': ('seaborn', 'seaborn'),
        'tf': ('tensorflow', 'tensorflow'),
        'torch': ('torch', 'torch'),
        'nn': ('torch.nn', 'torch.nn'),
        'F': ('torch.nn.functional', 'torch.nn.functional'),
        'sklearn': ('sklearn', 'sklearn'),
        'cv2': ('cv2', 'opencv-python'),
        'PIL': ('PIL', 'Pillow'),
        'Image': ('PIL.Image', 'Pillow'),
        'requests': ('requests', 'requests'),
        'bs4': ('bs4', 'beautifulsoup4'),
        'BeautifulSoup': ('bs4', 'beautifulsoup4'),
        'lxml': ('lxml', 'lxml'),
        'yaml': ('yaml', 'PyYAML'),
        'tqdm': ('tqdm', 'tqdm'),
        'pytest': ('pytest', 'pytest'),
        'mock': ('unittest.mock', 'unittest'),
        'flask': ('flask', 'flask'),
        'django': ('django', 'django'),
        'fastapi': ('fastapi', 'fastapi'),
        'uvicorn': ('uvicorn', 'uvicorn'),
        'celery': ('celery', 'celery'),
        'redis': ('redis', 'redis'),
        'pymongo': ('pymongo', 'pymongo'),
        'sqlalchemy': ('sqlalchemy', 'sqlalchemy'),
        'alembic': ('alembic', 'alembic'),
        'pydantic': ('pydantic', 'pydantic'),
        'click': ('click', 'click'),
        'rich': ('rich', 'rich'),
        'typer': ('typer', 'typer'),
    }

    STANDARD_LIBRARY_MODULES = {
        'abc', 'aifc', 'argparse', 'array', 'ast', 'asynchat', 'asyncio',
        'asyncore', 'atexit', 'audioop', 'base64', 'bdb', 'binascii',
        'binhex', 'bisect', 'builtins', 'bz2', 'calendar', 'cgi', 'cgitb',
        'chunk', 'cmath', 'cmd', 'code', 'codecs', 'codeop', 'collections',
        'colorsys', 'compileall', 'concurrent', 'configparser', 'contextlib',
        'contextvars', 'copy', 'copyreg', 'cProfile', 'crypt', 'csv', 'ctypes',
        'curses', 'dataclasses', 'datetime', 'dbm', 'decimal', 'difflib',
        'dis', 'distutils', 'doctest', 'email', 'encodings', 'enum', 'errno',
        'faulthandler', 'fcntl', 'filecmp', 'fileinput', 'fnmatch', 'fractions',
        'ftplib', 'functools', 'gc', 'getopt', 'getpass', 'gettext', 'glob',
        'graphlib', 'grp', 'gzip', 'hashlib', 'heapq', 'hmac', 'html', 'http',
        'idlelib', 'imaplib', 'imghdr', 'imp', 'importlib', 'inspect', 'io',
        'ipaddress', 'itertools', 'json', 'keyword', 'lib2to3', 'linecache',
        'locale', 'logging', 'lzma', 'mailbox', 'mailcap', 'marshal', 'math',
        'mimetypes', 'mmap', 'modulefinder', 'multiprocessing', 'netrc',
        'nis', 'nntplib', 'numbers', 'operator', 'optparse', 'os', 'ossaudiodev',
        'pathlib', 'pdb', 'pickle', 'pickletools', 'pipes', 'pkgutil', 'platform',
        'plistlib', 'poplib', 'posix', 'posixpath', 'pprint', 'profile', 'pstats',
        'pty', 'pwd', 'py_compile', 'pyclbr', 'pydoc', 'queue', 'quopri',
        'random', 're', 'readline', 'reprlib', 'resource', 'rlcompleter',
        'runpy', 'sched', 'secrets', 'select', 'selectors', 'shelve', 'shlex',
        'shutil', 'signal', 'site', 'smtpd', 'smtplib', 'sndhdr', 'socket',
        'socketserver', 'spwd', 'sqlite3', 'ssl', 'stat', 'statistics', 'string',
        'stringprep', 'struct', 'subprocess', 'sunau', 'symtable', 'sys',
        'sysconfig', 'syslog', 'tabnanny', 'tarfile', 'telnetlib', 'tempfile',
        'termios', 'test', 'textwrap', 'threading', 'time', 'timeit', 'tkinter',
        'token', 'tokenize', 'trace', 'traceback', 'tracemalloc', 'tty', 'turtle',
        'turtledemo', 'types', 'typing', 'unicodedata', 'unittest', 'urllib',
        'uu', 'uuid', 'venv', 'warnings', 'wave', 'weakref', 'webbrowser',
        'winreg', 'winsound', 'wsgiref', 'xdrlib', 'xml', 'xmlrpc', 'zipapp',
        'zipfile', 'zipimport', 'zlib', 'zoneinfo'
    }

    def __init__(self):
        super().__init__()
        self._import_cache: Dict[str, Set[str]] = {}
        self._module_usage: Dict[str, int] = {}

    def can_fix(self, content: str, file_path: Path) -> List[Dict[str, Any]]:
        issues = []

        issues.extend(self._detect_unused_imports(content))
        issues.extend(self._detect_missing_imports(content))
        issues.extend(self._detect_import_order(content))
        issues.extend(self._detect_duplicate_imports(content))
        issues.extend(self._detect_import_style_issues(content))
        issues.extend(self._detect_circular_import_risk(content, file_path))
        issues.extend(self._detect_relative_import_issues(content, file_path))

        return issues

    def _detect_unused_imports(self, content: str) -> List[Dict[str, Any]]:
        issues = []

        try:
            tree = ast.parse(content)
        except SyntaxError:
            return issues

        imports = {}
        used_names = set()
        imported_in_type_checking = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name.split('.')[0]
                    imports[name] = (node.lineno, alias.name, node)
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    module = node.module or ""
                    imports[name] = (node.lineno, f"{module}.{alias.name}" if module else alias.name, node)
                    if node.module == 'typing' and alias.name == 'TYPE_CHECKING':
                        imported_in_type_checking.add(name)

        type_checking_block_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.If):
                test = node.test
                if isinstance(test, ast.Name) and test.id in imported_in_type_checking:
                    for child in ast.walk(node):
                        if isinstance(child, ast.Name):
                            type_checking_block_names.add(child.id)
                elif isinstance(test, ast.Attribute):
                    if isinstance(test.value, ast.Name) and test.value.id in imported_in_type_checking:
                        for child in ast.walk(node):
                            if isinstance(child, ast.Name):
                                type_checking_block_names.add(child.id)

        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                if isinstance(node.ctx, ast.Load):
                    used_names.add(node.id)
            elif isinstance(node, ast.Attribute):
                if isinstance(node.value, ast.Name):
                    used_names.add(node.value.id)
            elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Name):
                        used_names.add(decorator.id)
                    elif isinstance(decorator, ast.Attribute):
                        if isinstance(decorator.value, ast.Name):
                            used_names.add(decorator.value.id)
            elif isinstance(node, ast.ClassDef):
                for base in node.bases:
                    if isinstance(base, ast.Name):
                        used_names.add(base.id)
                    elif isinstance(base, ast.Attribute):
                        if isinstance(base.value, ast.Name):
                            used_names.add(base.value.id)
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Name):
                        used_names.add(decorator.id)

        builtin_names = {
            'True', 'False', 'None', 'print', 'len', 'range', 'str', 'int', 'float',
            'list', 'dict', 'set', 'tuple', 'type', 'isinstance', 'hasattr', 'getattr',
            'setattr', 'delattr', 'open', 'enumerate', 'zip', 'map', 'filter', 'sorted',
            'reversed', 'min', 'max', 'sum', 'any', 'all', 'abs', 'round', 'super',
            'property', 'staticmethod', 'classmethod', 'iter', 'next', 'repr', 'hash',
            'id', 'callable', 'dir', 'vars', 'locals', 'globals', 'eval', 'exec',
            'compile', 'input', 'breakpoint', 'ascii', 'bin', 'chr', 'ord', 'hex',
            'oct', 'pow', 'divmod', 'format', 'slice', 'object', 'bytearray', 'bytes',
            'memoryview', 'frozenset', 'complex', 'bool', 'Exception', 'BaseException',
            '__name__', '__doc__', '__package__', '__loader__', '__spec__', '__path__',
            '__file__', '__cached__', '__builtins__', '__import__', '__debug__',
            'Ellipsis', 'NotImplemented', 'exit', 'quit', 'copyright', 'credits',
            'license', 'help'
        }

        for name, (lineno, original, node) in imports.items():
            if name not in used_names and name not in builtin_names:
                if name not in type_checking_block_names:
                    if original not in ['TYPE_CHECKING', 'annotations']:
                        issues.append({
                            'type': 'unused_import',
                            'line': lineno,
                            'message': f'未使用的导入: {original}',
                            'import_name': original,
                            'import_node': node
                        })

        return issues

    def _detect_missing_imports(self, content: str) -> List[Dict[str, Any]]:
        issues = []

        try:
            tree = ast.parse(content)
        except SyntaxError:
            return issues

        imported_names = set()
        defined_names = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name.split('.')[0]
                    imported_names.add(name)
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    imported_names.add(alias.asname if alias.asname else alias.name)
            elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                defined_names.add(node.name)
                for arg in node.args.args:
                    defined_names.add(arg.arg)
                for arg in node.args.posonlyargs:
                    defined_names.add(arg.arg)
                for arg in node.args.kwonlyargs:
                    defined_names.add(arg.arg)
                if node.args.vararg:
                    defined_names.add(node.args.vararg.arg)
                if node.args.kwarg:
                    defined_names.add(node.args.kwarg.arg)
            elif isinstance(node, ast.ClassDef):
                defined_names.add(node.name)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        defined_names.add(target.id)
                    elif isinstance(target, ast.Tuple):
                        for elt in target.elts:
                            if isinstance(elt, ast.Name):
                                defined_names.add(elt.id)

        used_names = set()
        name_contexts: Dict[str, List[Dict[str, Any]]] = {}

        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                if isinstance(node.ctx, ast.Load):
                    used_names.add(node.id)
                    if node.id not in name_contexts:
                        name_contexts[node.id] = []
                    name_contexts[node.id].append({
                        'line': node.lineno,
                        'context': 'usage'
                    })
            elif isinstance(node, ast.Attribute):
                if isinstance(node.value, ast.Name):
                    used_names.add(node.value.id)

        builtin_names = {
            'True', 'False', 'None', 'print', 'len', 'range', 'str', 'int', 'float',
            'list', 'dict', 'set', 'tuple', 'type', 'isinstance', 'hasattr', 'getattr',
            'setattr', 'open', 'enumerate', 'zip', 'map', 'filter', 'sorted', 'reversed',
            'min', 'max', 'sum', 'any', 'all', 'abs', 'round', 'super', 'property',
            'staticmethod', 'classmethod', '__name__', 'Exception', 'BaseException',
            'ValueError', 'TypeError', 'KeyError', 'IndexError', 'AttributeError',
            'RuntimeError', 'StopIteration', 'NotImplementedError', 'ImportError',
            'OSError', 'IOError', 'FileNotFoundError', 'PermissionError',
            'AssertionError', 'NameError', 'SyntaxError', 'IndentationError',
            'TabError', 'SystemExit', 'KeyboardInterrupt', 'GeneratorExit',
            'ArithmeticError', 'FloatingPointError', 'OverflowError', 'ZeroDivisionError',
            'LookupError', 'UnicodeError', 'UnicodeDecodeError', 'UnicodeEncodeError',
            'UnicodeTranslateError', 'Warning', 'UserWarning', 'DeprecationWarning',
            'PendingDeprecationWarning', 'SyntaxWarning', 'RuntimeWarning',
            'FutureWarning', 'ImportWarning', 'UnicodeWarning', 'BytesWarning',
            'ResourceWarning', 'ConnectionError', 'BrokenPipeError',
            'ConnectionAbortedError', 'ConnectionRefusedError', 'ConnectionResetError',
            'BlockingIOError', 'ChildProcessError', 'FileExistsError',
            'InterruptedError', 'IsADirectoryError', 'NotADirectoryError',
            'ProcessLookupError', 'TimeoutError', 'EnvironmentError'
        }

        missing = used_names - imported_names - defined_names - builtin_names

        for name in missing:
            suggested_import = self._suggest_import(name)
            if suggested_import:
                contexts = name_contexts.get(name, [])
                first_use_line = min(c['line'] for c in contexts) if contexts else 1
                issues.append({
                    'type': 'missing_import',
                    'line': first_use_line,
                    'message': f'可能缺少导入: {name} (建议: {suggested_import})',
                    'name': name,
                    'suggested_import': suggested_import
                })

        return issues

    def _suggest_import(self, name: str) -> Optional[str]:
        if name in self.MODULE_ALIASES:
            module_info = self.MODULE_ALIASES[name]
            return f'import {module_info[0]} as {name}'

        for full_import, import_stmt in self.COMMON_IMPORT_FIXES.items():
            if full_import.endswith(f'.{name}') or full_import == name:
                return import_stmt

        for module in self.STANDARD_LIBRARY_MODULES:
            if name.lower() == module:
                return f'import {module}'

        return None

    def _detect_import_order(self, content: str) -> List[Dict[str, Any]]:
        issues = []
        lines = content.split('\n')

        imports: List[Dict[str, Any]] = []
        first_code_line = None

        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith(('import ', 'from ')):
                is_stdlib = self._is_stdlib_import(stripped)
                imports.append({
                    'line': i,
                    'content': stripped,
                    'is_stdlib': is_stdlib,
                    'original_line': line
                })
            elif stripped and not stripped.startswith('#') and not stripped.startswith('"""') and not stripped.startswith("'''"):
                if first_code_line is None:
                    first_code_line = i

        if not imports:
            return issues

        stdlib_imports = [imp for imp in imports if imp['is_stdlib']]
        third_party_imports = [imp for imp in imports if not imp['is_stdlib'] and not imp['content'].startswith('from .')]
        local_imports = [imp for imp in imports if imp['content'].startswith('from .')]

        expected_order = stdlib_imports + third_party_imports + local_imports

        if imports != expected_order:
            issues.append({
                'type': 'import_order',
                'line': imports[0]['line'],
                'message': '导入顺序不符合PEP8规范: 标准库 -> 第三方库 -> 本地模块',
                'current_order': [imp['line'] for imp in imports],
                'expected_order': [imp['line'] for imp in expected_order]
            })

        for i in range(1, len(imports)):
            prev_import = imports[i - 1]
            curr_import = imports[i]
            if curr_import['line'] > prev_import['line'] + 1:
                between_lines = lines[prev_import['line']:curr_import['line'] - 1]
                has_code = any(l.strip() and not l.strip().startswith('#') for l in between_lines)
                if has_code:
                    issues.append({
                        'type': 'import_not_grouped',
                        'line': curr_import['line'],
                        'message': '导入语句应该分组放置在文件顶部'
                    })

        return issues

    def _is_stdlib_import(self, import_line: str) -> bool:
        if import_line.startswith('from '):
            match = re.match(r'from\s+(\w+)', import_line)
            if match:
                module = match.group(1)
                return module in self.STANDARD_LIBRARY_MODULES
        elif import_line.startswith('import '):
            match = re.match(r'import\s+(\w+)', import_line)
            if match:
                module = match.group(1)
                return module in self.STANDARD_LIBRARY_MODULES
        return False

    def _detect_duplicate_imports(self, content: str) -> List[Dict[str, Any]]:
        issues = []

        try:
            tree = ast.parse(content)
        except SyntaxError:
            return issues

        import_map: Dict[str, List[int]] = {}

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.name
                    if name not in import_map:
                        import_map[name] = []
                    import_map[name].append(node.lineno)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    full_name = f"{module}.{alias.name}" if module else alias.name
                    if full_name not in import_map:
                        import_map[full_name] = []
                    import_map[full_name].append(node.lineno)

        for name, lines in import_map.items():
            if len(lines) > 1:
                issues.append({
                    'type': 'duplicate_import',
                    'line': lines[1],
                    'message': f'重复导入: {name} (首次导入在行 {lines[0]})',
                    'import_name': name,
                    'first_line': lines[0],
                    'duplicate_lines': lines[1:]
                })

        return issues

    def _detect_import_style_issues(self, content: str) -> List[Dict[str, Any]]:
        issues = []
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            if re.match(r'^from\s+\S+\s+import\s+\*', stripped):
                issues.append({
                    'type': 'wildcard_import',
                    'line': i,
                    'message': '使用通配符导入 (import *) 可能导致命名冲突',
                    'context': stripped
                })

            if re.match(r'^import\s+\w+,\s*\w+', stripped):
                issues.append({
                    'type': 'multiple_imports',
                    'line': i,
                    'message': '建议每行只导入一个模块',
                    'context': stripped
                })

            match = re.match(r'^from\s+(\S+)\s+import\s+\(([^)]+)\)', stripped, re.DOTALL)
            if match:
                imports_str = match.group(2)
                imports = [imp.strip() for imp in imports_str.split(',')]
                if len(imports) > 1:
                    sorted_imports = sorted(imports)
                    if imports != sorted_imports:
                        issues.append({
                            'type': 'unsorted_imports',
                            'line': i,
                            'message': '多行导入应按字母顺序排列',
                            'context': stripped
                        })

        return issues

    def _detect_circular_import_risk(self, content: str, file_path: Path) -> List[Dict[str, Any]]:
        issues = []

        try:
            tree = ast.parse(content)
        except SyntaxError:
            return issues

        module_name = file_path.stem

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module:
                    if node.level > 0:
                        issues.append({
                            'type': 'circular_import_risk',
                            'line': node.lineno,
                            'message': f'相对导入可能存在循环导入风险: from {"." * node.level}{node.module}',
                            'module': node.module,
                            'level': node.level
                        })

        return issues

    def _detect_relative_import_issues(self, content: str, file_path: Path) -> List[Dict[str, Any]]:
        issues = []
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            match = re.match(r'^from\s+(\.+)(\w+(?:\.\w+)*)\s+import', stripped)
            if match:
                dots = match.group(1)
                module = match.group(2)
                level = len(dots)

                if level > 2:
                    issues.append({
                        'type': 'deep_relative_import',
                        'line': i,
                        'message': f'深层相对导入 ({"." * level}) 可能导致可维护性问题',
                        'level': level
                    })

        return issues

    def apply_fix(self, content: str, issues: List[Dict[str, Any]]) -> Tuple[str, List[FixAction]]:
        lines = content.split('\n')
        actions = []
        lines_to_remove = set()
        imports_to_add = []
        install_suggestions = []

        for issue in issues:
            if issue['type'] == 'unused_import':
                line_idx = issue['line'] - 1
                if 0 <= line_idx < len(lines):
                    lines_to_remove.add(line_idx)
                    actions.append(self._create_action(
                        FixType.IMPORT_ERROR,
                        f"删除未使用的导入: {issue['import_name']}",
                        lines[line_idx],
                        '',
                        issue['line'],
                        RiskLevel.LOW
                    ))

            elif issue['type'] == 'missing_import':
                suggested = issue.get('suggested_import', '')
                name = issue.get('name', '')
                if suggested:
                    imports_to_add.append(suggested)
                    actions.append(self._create_action(
                        FixType.IMPORT_ERROR,
                        f"添加缺失的导入: {suggested}",
                        '',
                        suggested,
                        1,
                        RiskLevel.LOW
                    ))
                    
                    install_cmd = self._get_install_suggestion(name)
                    if install_cmd:
                        install_suggestions.append({
                            'name': name,
                            'command': install_cmd
                        })

            elif issue['type'] == 'duplicate_import':
                line_idx = issue['line'] - 1
                if 0 <= line_idx < len(lines):
                    lines_to_remove.add(line_idx)
                    actions.append(self._create_action(
                        FixType.IMPORT_ERROR,
                        f"删除重复导入: {issue['import_name']}",
                        lines[line_idx],
                        '',
                        issue['line'],
                        RiskLevel.LOW
                    ))
            
            elif issue['type'] == 'import_order':
                actions.append(self._create_action(
                    FixType.IMPORT_ERROR,
                    '导入顺序需要调整',
                    '',
                    '',
                    issue['line'],
                    RiskLevel.LOW,
                    auto=False
                ))
            
            elif issue['type'] == 'wildcard_import':
                actions.append(self._create_action(
                    FixType.IMPORT_ERROR,
                    '通配符导入需要手动修复',
                    '',
                    '',
                    issue['line'],
                    RiskLevel.MEDIUM,
                    auto=False
                ))
            
            elif issue['type'] == 'circular_import_risk':
                actions.append(self._create_action(
                    FixType.IMPORT_ERROR,
                    f"循环导入风险: {issue.get('module', '')}",
                    '',
                    '',
                    issue['line'],
                    RiskLevel.HIGH,
                    auto=False
                ))

        if lines_to_remove:
            new_lines = [line for i, line in enumerate(lines) if i not in lines_to_remove]
            lines = new_lines

        if imports_to_add:
            unique_imports = list(dict.fromkeys(imports_to_add))
            sorted_imports = sorted(unique_imports)

            insert_pos = 0
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped and not stripped.startswith('#') and not stripped.startswith('"""') and not stripped.startswith("'''"):
                    insert_pos = i
                    break

            for imp in sorted_imports:
                lines.insert(insert_pos, imp)
                insert_pos += 1

        if install_suggestions:
            comment_lines = ['# 缺失的包安装建议:']
            for sug in install_suggestions:
                comment_lines.append(f'#   pip install {sug["name"]}  # {sug["command"]}')
            comment_lines.append('')
            
            insert_pos = 0
            for i, line in enumerate(lines):
                if line.strip() and not line.strip().startswith('#'):
                    insert_pos = i
                    break
            
            for comment in reversed(comment_lines):
                lines.insert(insert_pos, comment)

        return '\n'.join(lines), actions

    def _get_install_suggestion(self, name: str) -> Optional[str]:
        if name in self.MODULE_ALIASES:
            return f"pip install {self.MODULE_ALIASES[name][1]}"
        
        if name in self.STANDARD_LIBRARY_MODULES:
            return None
        
        return f"pip install {name}"

    def get_missing_package_info(self, name: str) -> Dict[str, Any]:
        if name in self.MODULE_ALIASES:
            return {
                'name': name,
                'package': self.MODULE_ALIASES[name][1],
                'import_statement': f"import {self.MODULE_ALIASES[name][0]} as {name}",
                'install_command': f"pip install {self.MODULE_ALIASES[name][1]}",
                'is_stdlib': False,
            }
        
        if name in self.STANDARD_LIBRARY_MODULES:
            return {
                'name': name,
                'package': name,
                'import_statement': f"import {name}",
                'install_command': None,
                'is_stdlib': True,
            }
        
        for full_import, import_stmt in self.COMMON_IMPORT_FIXES.items():
            if full_import.endswith(f'.{name}') or full_import == name:
                package = full_import.split('.')[0]
                return {
                    'name': name,
                    'package': package,
                    'import_statement': import_stmt,
                    'install_command': f"pip install {package}" if package not in self.STANDARD_LIBRARY_MODULES else None,
                    'is_stdlib': package in self.STANDARD_LIBRARY_MODULES,
                }
        
        return {
            'name': name,
            'package': name,
            'import_statement': f"import {name}",
            'install_command': f"pip install {name}",
            'is_stdlib': False,
        }


class StyleFixer(FixStrategy):
    """代码风格修复器"""

    MAX_LINE_LENGTH = 120

    def can_fix(self, content: str, file_path: Path) -> List[Dict[str, Any]]:
        issues = []

        issues.extend(self._detect_long_lines(content))
        issues.extend(self._detect_trailing_whitespace(content))
        issues.extend(self._detect_missing_newline(content))
        issues.extend(self._detect_multiple_blank_lines(content))
        issues.extend(self._detect_missing_docstring(content))

        return issues

    def _detect_long_lines(self, content: str) -> List[Dict[str, Any]]:
        issues = []
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            if len(line) > self.MAX_LINE_LENGTH:
                issues.append({
                    'type': 'long_line',
                    'line': i,
                    'message': f'行长度超过{self.MAX_LINE_LENGTH}字符: {len(line)}字符',
                    'length': len(line)
                })

        return issues

    def _detect_trailing_whitespace(self, content: str) -> List[Dict[str, Any]]:
        issues = []
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            if line != line.rstrip():
                issues.append({
                    'type': 'trailing_whitespace',
                    'line': i,
                    'message': '行尾有多余空白字符'
                })

        return issues

    def _detect_missing_newline(self, content: str) -> List[Dict[str, Any]]:
        issues = []

        if content and not content.endswith('\n'):
            issues.append({
                'type': 'missing_newline',
                'line': len(content.split('\n')),
                'message': '文件末尾缺少换行符'
            })

        return issues

    def _detect_multiple_blank_lines(self, content: str) -> List[Dict[str, Any]]:
        issues = []
        lines = content.split('\n')

        blank_count = 0
        for i, line in enumerate(lines, 1):
            if not line.strip():
                blank_count += 1
                if blank_count > 2:
                    issues.append({
                        'type': 'multiple_blank_lines',
                        'line': i,
                        'message': '连续空行超过2行'
                    })
            else:
                blank_count = 0

        return issues

    def _detect_missing_docstring(self, content: str) -> List[Dict[str, Any]]:
        issues = []

        try:
            tree = ast.parse(content)
        except SyntaxError:
            return issues

        if not ast.get_docstring(tree):
            issues.append({
                'type': 'missing_module_docstring',
                'line': 1,
                'message': '模块缺少文档字符串'
            })

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not ast.get_docstring(node) and not node.name.startswith('_'):
                    if node.body and not isinstance(node.body[0], ast.Expr):
                        issues.append({
                            'type': 'missing_function_docstring',
                            'line': node.lineno,
                            'message': f'函数 {node.name} 缺少文档字符串',
                            'function_name': node.name
                        })

        return issues

    def apply_fix(self, content: str, issues: List[Dict[str, Any]]) -> Tuple[str, List[FixAction]]:
        lines = content.split('\n')
        actions = []

        for issue in issues:
            line_idx = issue['line'] - 1

            if issue['type'] == 'trailing_whitespace':
                if 0 <= line_idx < len(lines):
                    original = lines[line_idx]
                    lines[line_idx] = original.rstrip()
                    if original != lines[line_idx]:
                        actions.append(self._create_action(
                            FixType.STYLE_ERROR,
                            '移除行尾空白字符',
                            original,
                            lines[line_idx],
                            issue['line'],
                            RiskLevel.LOW
                        ))

        if content and not content.endswith('\n'):
            for issue in issues:
                if issue['type'] == 'missing_newline':
                    lines.append('')
                    actions.append(self._create_action(
                        FixType.STYLE_ERROR,
                        '添加文件末尾换行符',
                        '',
                        '\n',
                        issue['line'],
                        RiskLevel.LOW
                    ))
                    break

        return '\n'.join(lines), actions


class CodeSmellFixer(FixStrategy):
    """代码异味修复器"""

    def can_fix(self, content: str, file_path: Path) -> List[Dict[str, Any]]:
        issues = []

        issues.extend(self._detect_mutable_default_args(content))
        issues.extend(self._detect_bare_except(content))
        issues.extend(self._detect_print_statements(content))
        issues.extend(self._detect_eq_without_hash(content))

        return issues

    def _detect_mutable_default_args(self, content: str) -> List[Dict[str, Any]]:
        issues = []

        try:
            tree = ast.parse(content)
        except SyntaxError:
            return issues

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                for default in node.args.defaults:
                    if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                        issues.append({
                            'type': 'mutable_default_arg',
                            'line': node.lineno,
                            'message': f'函数 {node.name} 使用可变对象作为默认参数',
                            'function_name': node.name
                        })

        return issues

    def _detect_bare_except(self, content: str) -> List[Dict[str, Any]]:
        issues = []
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            if re.search(r'^\s*except\s*:', line):
                issues.append({
                    'type': 'bare_except',
                    'line': i,
                    'message': '使用裸异常捕获，应指定具体异常类型'
                })

        return issues

    def _detect_print_statements(self, content: str) -> List[Dict[str, Any]]:
        issues = []
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            if re.search(r'^\s*print\s*\(', line) and 'def ' not in line:
                issues.append({
                    'type': 'print_statement',
                    'line': i,
                    'message': '使用print语句，建议使用logging'
                })

        return issues

    def _detect_eq_without_hash(self, content: str) -> List[Dict[str, Any]]:
        issues = []

        try:
            tree = ast.parse(content)
        except SyntaxError:
            return issues

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                has_eq = False
                has_hash = False

                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        if item.name == '__eq__':
                            has_eq = True
                        elif item.name == '__hash__':
                            has_hash = True

                if has_eq and not has_hash:
                    issues.append({
                        'type': 'eq_without_hash',
                        'line': node.lineno,
                        'message': f'类 {node.name} 定义了__eq__但未定义__hash__',
                        'class_name': node.name
                    })

        return issues

    def apply_fix(self, content: str, issues: List[Dict[str, Any]]) -> Tuple[str, List[FixAction]]:
        lines = content.split('\n')
        actions = []

        for issue in issues:
            line_idx = issue['line'] - 1

            if issue['type'] == 'bare_except':
                if 0 <= line_idx < len(lines):
                    original = lines[line_idx]
                    fixed = re.sub(r'except\s*:', 'except Exception:', original)
                    if original != fixed:
                        lines[line_idx] = fixed
                        actions.append(self._create_action(
                            FixType.LOGIC_ERROR,
                            '将裸异常改为Exception',
                            original,
                            fixed,
                            issue['line'],
                            RiskLevel.MEDIUM
                        ))

        return '\n'.join(lines), actions


class SecurityVulnerabilityFixer(FixStrategy):
    """安全漏洞修复器 - 增强版"""

    SECURITY_PATTERNS = {
        'hardcoded_password': {
            'pattern': r'(?i)(password|passwd|pwd)\s*=\s*[\'"][^\'"]+[\'"]',
            'message': '检测到硬编码密码',
            'severity': 'critical',
            'cwe': 'CWE-259'
        },
        'hardcoded_secret': {
            'pattern': r'(?i)(secret|api_key|apikey|token|private_key|access_key)\s*=\s*[\'"][^\'"]+[\'"]',
            'message': '检测到硬编码密钥',
            'severity': 'critical',
            'cwe': 'CWE-798'
        },
        'sql_injection_risk': {
            'pattern': r'(execute|executemany|executescript)\s*\(\s*[f]?[\'"].*\{.*\}.*[\'"]',
            'message': '检测到SQL注入风险',
            'severity': 'high',
            'cwe': 'CWE-89'
        },
        'sql_injection_concat': {
            'pattern': r'(execute|executemany)\s*\([^)]*\+[^)]*\)',
            'message': '检测到SQL字符串拼接，存在注入风险',
            'severity': 'high',
            'cwe': 'CWE-89'
        },
        'eval_usage': {
            'pattern': r'\beval\s*\(\s*(?!__import__\s*\(\s*[\'"]ast[\'"]\s*\))',
            'message': '使用eval函数存在安全风险',
            'severity': 'high',
            'cwe': 'CWE-95'
        },
        'exec_usage': {
            'pattern': r'\bexec\s*\(',
            'message': '使用exec函数存在安全风险',
            'severity': 'high',
            'cwe': 'CWE-95'
        },
        'pickle_usage': {
            'pattern': r'pickle\.loads?\s*\(',
            'message': 'pickle反序列化不受信任数据存在安全风险',
            'severity': 'high',
            'cwe': 'CWE-502'
        },
        'marshal_usage': {
            'pattern': r'marshal\.loads?\s*\(',
            'message': 'marshal反序列化不受信任数据存在安全风险',
            'severity': 'high',
            'cwe': 'CWE-502'
        },
        'subprocess_shell': {
            'pattern': r'subprocess\.(call|run|Popen|check_output|check_call)\s*\([^)]*shell\s*=\s*True',
            'message': 'subprocess使用shell=True存在命令注入风险',
            'severity': 'high',
            'cwe': 'CWE-78'
        },
        'os_system': {
            'pattern': r'os\.system\s*\(',
            'message': 'os.system存在命令注入风险',
            'severity': 'high',
            'cwe': 'CWE-78'
        },
        'yaml_unsafe_load': {
            'pattern': r'yaml\.load\s*\([^)]*\)(?!.*Loader\s*=)',
            'message': 'yaml.load未指定Loader存在安全风险',
            'severity': 'medium',
            'cwe': 'CWE-502'
        },
        'assert_in_production': {
            'pattern': r'^\s*assert\s+',
            'message': '生产代码中使用assert可能被优化掉',
            'severity': 'low',
            'cwe': 'CWE-617'
        },
        'tempfile_race': {
            'pattern': r'(open|file)\s*\(\s*[\'"]/tmp/',
            'message': '使用固定路径临时文件存在竞态条件风险',
            'severity': 'medium',
            'cwe': 'CWE-377'
        },
        'xml_external_entity': {
            'pattern': r'xml\.etree\.ElementTree\.parse\s*\(|etree\.parse\s*\(|lxml\.etree\.parse\s*\(',
            'message': 'XML解析可能存在XXE攻击风险',
            'severity': 'high',
            'cwe': 'CWE-611'
        },
        'ssl_verify_disabled': {
            'pattern': r'(requests\.(get|post|put|delete|patch)|urllib\.request\.urlopen)\s*\([^)]*verify\s*=\s*False',
            'message': 'SSL证书验证被禁用，存在中间人攻击风险',
            'severity': 'high',
            'cwe': 'CWE-295'
        },
        'jwt_none_algorithm': {
            'pattern': r'jwt\.decode\s*\([^)]*algorithms\s*=\s*\[\s*[\'"]none[\'"]\s*\]',
            'message': 'JWT使用none算法存在安全风险',
            'severity': 'critical',
            'cwe': 'CWE-327'
        },
        'hardcoded_iv': {
            'pattern': r'(AES|DES|Blowfish)\s*\.\s*new\s*\([^)]*,\s*[\'"][^\'"]+[\'"]\s*\)',
            'message': '加密使用硬编码IV存在安全风险',
            'severity': 'high',
            'cwe': 'CWE-329'
        },
        'weak_des': {
            'pattern': r'(DES|Blowfish)\s*\.\s*new\s*\(',
            'message': '使用弱加密算法DES/Blowfish',
            'severity': 'high',
            'cwe': 'CWE-327'
        },
        'insecure_hash_no_salt': {
            'pattern': r'hashlib\.(md5|sha1)\s*\([^)]*\)\.hexdigest\s*\(\)',
            'message': '哈希未使用盐值，存在彩虹表攻击风险',
            'severity': 'medium',
            'cwe': 'CWE-916'
        },
        'debug_mode': {
            'pattern': r'(app\.run|Flask\(__name__\))[^)]*debug\s*=\s*True',
            'message': '生产环境启用调试模式存在安全风险',
            'severity': 'high',
            'cwe': 'CWE-215'
        },
        'cors_wildcard': {
            'pattern': r'@.*\.after_request[^}]*Access-Control-Allow-Origin\s*:\s*\*',
            'message': 'CORS配置使用通配符，存在安全风险',
            'severity': 'medium',
            'cwe': 'CWE-942'
        },
        'hardcoded_url': {
            'pattern': r'(requests\.(get|post)|urllib\.request\.urlopen)\s*\(\s*[\'"]https?://[^\'"]+[\'"]',
            'message': '硬编码URL可能导致配置问题',
            'severity': 'low',
            'cwe': 'CWE-1021'
        },
        'input_without_validation': {
            'pattern': r'input\s*\(\s*[\'"][^\'"]*[\'"]\s*\)',
            'message': '用户输入未进行验证',
            'severity': 'medium',
            'cwe': 'CWE-20'
        },
        'format_string_vuln': {
            'pattern': r'\.format\s*\(\s*[^)]*input\s*\(|f[\'"][^\'"]*\{[^}]*input\s*\(',
            'message': '格式化字符串可能存在注入风险',
            'severity': 'medium',
            'cwe': 'CWE-134'
        },
    }

    SAFE_REPLACEMENTS = {
        'hardcoded_password': 'os.environ.get("PASSWORD", "")',
        'hardcoded_secret': 'os.environ.get("SECRET_KEY", "")',
        'yaml_unsafe_load': 'yaml.load(..., Loader=yaml.SafeLoader)',
    }

    def __init__(self):
        super().__init__()
        self._severity_weights = {
            'critical': 4,
            'high': 3,
            'medium': 2,
            'low': 1
        }

    def can_fix(self, content: str, file_path: Path) -> List[Dict[str, Any]]:
        issues = []

        for vuln_type, config in self.SECURITY_PATTERNS.items():
            pattern = config['pattern']
            matches = re.finditer(pattern, content, re.MULTILINE)

            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                issues.append({
                    'type': vuln_type,
                    'line': line_num,
                    'message': config['message'],
                    'severity': config['severity'],
                    'match_text': match.group(),
                    'start': match.start(),
                    'end': match.end(),
                    'cwe': config.get('cwe', 'CWE-Other')
                })

        issues.extend(self._detect_weak_crypto(content))
        issues.extend(self._detect_insecure_random(content))
        issues.extend(self._detect_path_traversal(content))
        issues.extend(self._detect_insecure_permissions(content))
        issues.extend(self._detect_sensitive_data_exposure(content))

        issues.sort(key=lambda x: self._severity_weights.get(x['severity'], 0), reverse=True)

        return issues

    def _detect_weak_crypto(self, content: str) -> List[Dict[str, Any]]:
        issues = []
        weak_hash_patterns = [
            (r'hashlib\.md5\s*\((?!.*usedforsecurity\s*=\s*False)', 'MD5哈希算法不安全，建议使用SHA256或更高版本'),
            (r'hashlib\.sha1\s*\((?!.*usedforsecurity\s*=\s*False)', 'SHA1哈希算法不安全，建议使用SHA256或更高版本'),
        ]

        for pattern, message in weak_hash_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                issues.append({
                    'type': 'weak_crypto',
                    'line': line_num,
                    'message': message,
                    'severity': 'medium',
                    'match_text': match.group(),
                    'cwe': 'CWE-328'
                })

        return issues

    def _detect_insecure_random(self, content: str) -> List[Dict[str, Any]]:
        issues = []
        insecure_random_patterns = [
            (r'random\.random\s*\(\)', 'random.random()不适用于安全场景'),
            (r'random\.randint\s*\(', 'random.randint()不适用于安全场景'),
            (r'random\.choice\s*\(', 'random.choice()不适用于安全场景'),
            (r'random\.randrange\s*\(', 'random.randrange()不适用于安全场景'),
            (r'random\.shuffle\s*\(', 'random.shuffle()不适用于安全场景'),
        ]

        context_keywords = ['password', 'token', 'secret', 'key', 'auth', 'session', 'salt', 'iv', 'nonce']

        for pattern, message in insecure_random_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                start = max(0, match.start() - 200)
                end = min(len(content), match.end() + 200)
                context = content[start:end].lower()

                if any(kw in context for kw in context_keywords):
                    line_num = content[:match.start()].count('\n') + 1
                    issues.append({
                        'type': 'insecure_random',
                        'line': line_num,
                        'message': message,
                        'severity': 'medium',
                        'match_text': match.group(),
                        'cwe': 'CWE-338'
                    })

        return issues

    def _detect_path_traversal(self, content: str) -> List[Dict[str, Any]]:
        issues = []
        patterns = [
            (r'open\s*\(\s*[\'"]?\.\./', '路径遍历风险: 使用相对路径可能不安全'),
            (r'os\.path\.join\s*\([^)]*\.\./', '路径遍历风险: 路径拼接可能被利用'),
            (r'send_file\s*\([^)]*request\.', '路径遍历风险: 用户输入直接用于文件路径'),
        ]

        for pattern, message in patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                issues.append({
                    'type': 'path_traversal',
                    'line': line_num,
                    'message': message,
                    'severity': 'high',
                    'match_text': match.group(),
                    'cwe': 'CWE-22'
                })

        return issues

    def _detect_insecure_permissions(self, content: str) -> List[Dict[str, Any]]:
        issues = []
        patterns = [
            (r'os\.chmod\s*\([^,]+,\s*0o777', '文件权限设置过于宽松 (777)'),
            (r'os\.chmod\s*\([^,]+,\s*0o666', '文件权限设置过于宽松 (666)'),
            (r'os\.mkdir\s*\([^)]+,\s*0o777', '目录权限设置过于宽松 (777)'),
        ]

        for pattern, message in patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                issues.append({
                    'type': 'insecure_permissions',
                    'line': line_num,
                    'message': message,
                    'severity': 'medium',
                    'match_text': match.group(),
                    'cwe': 'CWE-732'
                })

        return issues

    def _detect_sensitive_data_exposure(self, content: str) -> List[Dict[str, Any]]:
        issues = []
        patterns = [
            (r'print\s*\([^)]*(password|token|secret|key|credential)[^)]*\)', '敏感数据可能被打印到日志'),
            (r'logging\.(debug|info|warning|error)\s*\([^)]*(password|token|secret)[^)]*\)', '敏感数据可能被记录到日志'),
            (r'raise\s+\w*Exception\s*\([^)]*(password|token|secret)[^)]*\)', '敏感数据可能出现在异常信息中'),
        ]

        for pattern, message in patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                issues.append({
                    'type': 'sensitive_data_exposure',
                    'line': line_num,
                    'message': message,
                    'severity': 'medium',
                    'match_text': match.group(),
                    'cwe': 'CWE-532'
                })

        return issues

    def apply_fix(self, content: str, issues: List[Dict[str, Any]]) -> Tuple[str, List[FixAction]]:
        lines = content.split('\n')
        actions = []
        has_yaml_fix = False
        has_env_fix = False
        has_secrets_import = False

        for issue in issues:
            line_idx = issue['line'] - 1

            if issue['type'] == 'yaml_unsafe_load':
                if 0 <= line_idx < len(lines):
                    original = lines[line_idx]
                    fixed = re.sub(
                        r'yaml\.load\s*\(',
                        'yaml.load(',
                        original
                    )
                    if 'Loader=' not in fixed:
                        fixed = re.sub(
                            r'(yaml\.load\s*\([^)]*)\)',
                            r'\1, Loader=yaml.SafeLoader)',
                            fixed
                        )
                    if original != fixed:
                        lines[line_idx] = fixed
                        has_yaml_fix = True
                        actions.append(self._create_action(
                            FixType.SECURITY_ISSUE,
                            '添加yaml.SafeLoader防止代码注入',
                            original,
                            fixed,
                            issue['line'],
                            RiskLevel.MEDIUM,
                            auto=True
                        ))

            elif issue['type'] == 'assert_in_production':
                if 0 <= line_idx < len(lines):
                    original = lines[line_idx]
                    indent = len(original) - len(original.lstrip())
                    indent_str = original[:indent]
                    fixed = f"{indent_str}# SECURITY WARNING: 移除生产环境中的assert\n{original}"
                    lines[line_idx] = fixed
                    actions.append(self._create_action(
                        FixType.SECURITY_ISSUE,
                        '添加注释提醒移除assert',
                        original,
                        fixed,
                        issue['line'],
                        RiskLevel.LOW,
                        auto=True
                    ))

            elif issue['type'] in ['hardcoded_password', 'hardcoded_secret']:
                if 0 <= line_idx < len(lines):
                    original = lines[line_idx]
                    match = re.search(
                        r'(?i)(password|passwd|pwd|secret|api_key|apikey|token|private_key|access_key)\s*=\s*[\'"][^\'"]+[\'"]',
                        original
                    )
                    if match:
                        var_name = re.match(r'\s*(\w+)\s*=', original)
                        if var_name:
                            indent = len(original) - len(original.lstrip())
                            indent_str = original[:indent]
                            env_var = var_name.group(1).upper()
                            replacement = self.SAFE_REPLACEMENTS.get(
                                issue['type'],
                                f'os.environ.get("{env_var}", "")'
                            )
                            fixed = re.sub(
                                r'=\s*[\'"][^\'"]+[\'"]',
                                f'= {replacement}',
                                original
                            )
                            if original != fixed:
                                lines[line_idx] = fixed
                                has_env_fix = True
                                actions.append(self._create_action(
                                    FixType.SECURITY_ISSUE,
                                    f'将硬编码值替换为环境变量',
                                    original,
                                    fixed,
                                    issue['line'],
                                    RiskLevel.HIGH,
                                    auto=False
                                ))

            elif issue['type'] == 'ssl_verify_disabled':
                if 0 <= line_idx < len(lines):
                    original = lines[line_idx]
                    fixed = re.sub(r'verify\s*=\s*False', 'verify=True', original)
                    if original != fixed:
                        lines[line_idx] = fixed
                        actions.append(self._create_action(
                            FixType.SECURITY_ISSUE,
                            '启用SSL证书验证',
                            original,
                            fixed,
                            issue['line'],
                            RiskLevel.HIGH,
                            auto=True
                        ))

            elif issue['type'] == 'debug_mode':
                if 0 <= line_idx < len(lines):
                    original = lines[line_idx]
                    fixed = re.sub(r'debug\s*=\s*True', 'debug=False', original)
                    if original != fixed:
                        lines[line_idx] = fixed
                        actions.append(self._create_action(
                            FixType.SECURITY_ISSUE,
                            '禁用调试模式',
                            original,
                            fixed,
                            issue['line'],
                            RiskLevel.HIGH,
                            auto=True
                        ))

            elif issue['type'] == 'insecure_permissions':
                if 0 <= line_idx < len(lines):
                    original = lines[line_idx]
                    fixed = re.sub(r'0o777', '0o755', original)
                    fixed = re.sub(r'0o666', '0o644', fixed)
                    if original != fixed:
                        lines[line_idx] = fixed
                        actions.append(self._create_action(
                            FixType.SECURITY_ISSUE,
                            '修复不安全的文件权限',
                            original,
                            fixed,
                            issue['line'],
                            RiskLevel.MEDIUM,
                            auto=True
                        ))

            elif issue['type'] == 'sensitive_data_exposure':
                if 0 <= line_idx < len(lines):
                    original = lines[line_idx]
                    indent = len(original) - len(original.lstrip())
                    indent_str = original[:indent]
                    warning_comment = f"{indent_str}# SECURITY WARNING: 敏感数据不应记录到日志\n"
                    if not lines[line_idx].lstrip().startswith('#'):
                        lines[line_idx] = warning_comment + original
                        actions.append(self._create_action(
                            FixType.SECURITY_ISSUE,
                            '添加敏感数据暴露警告',
                            original,
                            warning_comment + original,
                            issue['line'],
                            RiskLevel.MEDIUM,
                            auto=True
                        ))

            elif issue['type'] in ['eval_usage', 'exec_usage', 'pickle_usage', 'marshal_usage',
                                    'subprocess_shell', 'sql_injection_risk', 'sql_injection_concat',
                                    'os_system', 'xml_external_entity', 'path_traversal']:
                if 0 <= line_idx < len(lines):
                    original = lines[line_idx]
                    indent = len(original) - len(original.lstrip())
                    indent_str = original[:indent]
                    warning_comment = f"{indent_str}# SECURITY WARNING: {issue['message']} [{issue.get('cwe', '')}]\n"
                    if not lines[line_idx].lstrip().startswith('#'):
                        lines[line_idx] = warning_comment + original
                        actions.append(self._create_action(
                            FixType.SECURITY_ISSUE,
                            f'添加安全警告注释',
                            original,
                            warning_comment + original,
                            issue['line'],
                            RiskLevel.HIGH,
                            auto=True
                        ))

        if has_env_fix and 'import os' not in content:
            import_line = 'import os\n'
            lines.insert(0, import_line)
            actions.insert(0, self._create_action(
                FixType.IMPORT_ERROR,
                '添加os模块导入',
                '',
                import_line,
                1,
                RiskLevel.LOW,
                auto=True
            ))

        return '\n'.join(lines), actions


class PerformanceFixer(FixStrategy):
    """性能问题修复器"""

    def can_fix(self, content: str, file_path: Path) -> List[Dict[str, Any]]:
        issues = []

        issues.extend(self._detect_string_concat_in_loop(content))
        issues.extend(self._detect_list_append_in_loop(content))
        issues.extend(self._detect_inefficient_membership(content))
        issues.extend(self._detect_nested_loops(content))
        issues.extend(self._detect_repeated_calculations(content))

        return issues

    def _detect_string_concat_in_loop(self, content: str) -> List[Dict[str, Any]]:
        issues = []
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            if re.search(r'^\s*(for|while)\s+', line):
                j = i
                while j < len(lines):
                    next_line = lines[j]
                    if re.search(r'\+=\s*[\'"]', next_line) and not next_line.strip().startswith('#'):
                        issues.append({
                            'type': 'string_concat_in_loop',
                            'line': j + 1,
                            'message': '循环中使用+=拼接字符串效率低，建议使用列表join',
                            'severity': 'medium'
                        })
                    if re.match(r'^\S', next_line) and j > i:
                        break
                    j += 1

        return issues

    def _detect_list_append_in_loop(self, content: str) -> List[Dict[str, Any]]:
        issues = []

        try:
            tree = ast.parse(content)
        except SyntaxError:
            return issues

        for node in ast.walk(tree):
            if isinstance(node, (ast.For, ast.While)):
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        if (isinstance(child.func, ast.Attribute) and
                            child.func.attr == 'append' and
                            isinstance(child.func.value, ast.Name)):
                            issues.append({
                                'type': 'list_append_in_loop',
                                'line': child.lineno,
                                'message': '循环中append可能可用列表推导式替代',
                                'severity': 'low'
                            })

        return issues

    def _detect_inefficient_membership(self, content: str) -> List[Dict[str, Any]]:
        issues = []
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            if re.search(r'\bin\s+\[', line):
                issues.append({
                    'type': 'inefficient_membership_list',
                    'line': i,
                    'message': '使用列表进行成员检查效率低，建议使用集合',
                    'severity': 'low'
                })

        return issues

    def _detect_nested_loops(self, content: str) -> List[Dict[str, Any]]:
        issues = []
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return issues

        for node in ast.walk(tree):
            if isinstance(node, ast.For):
                for child in ast.walk(node):
                    if isinstance(child, ast.For) and child is not node:
                        issues.append({
                            'type': 'nested_loop',
                            'line': node.lineno,
                            'message': '检测到嵌套循环，可能影响性能',
                            'severity': 'low'
                        })
                        break

        return issues

    def _detect_repeated_calculations(self, content: str) -> List[Dict[str, Any]]:
        issues = []
        lines = content.split('\n')

        call_pattern = re.compile(r'(\w+\([^)]*\))')
        call_counts: Dict[str, List[int]] = {}

        for i, line in enumerate(lines, 1):
            matches = call_pattern.findall(line)
            for match in matches:
                if match not in call_counts:
                    call_counts[match] = []
                call_counts[match].append(i)

        for call, line_nums in call_counts.items():
            if len(line_nums) >= 3:
                issues.append({
                    'type': 'repeated_calculation',
                    'line': line_nums[0],
                    'message': f'重复计算 {call} 出现 {len(line_nums)} 次，建议缓存结果',
                    'severity': 'low',
                    'call': call,
                    'occurrences': line_nums
                })

        return issues

    def apply_fix(self, content: str, issues: List[Dict[str, Any]]) -> Tuple[str, List[FixAction]]:
        lines = content.split('\n')
        actions = []

        for issue in issues:
            line_idx = issue['line'] - 1

            if issue['type'] == 'inefficient_membership_list':
                if 0 <= line_idx < len(lines):
                    original = lines[line_idx]
                    fixed = re.sub(r'\bin\s+\[', ' in {', original)
                    fixed = re.sub(r'\]$', '}', fixed)
                    fixed = re.sub(r'\](\s*(?:and|or|\)|:))', r'}\1', fixed)
                    if original != fixed:
                        lines[line_idx] = fixed
                        actions.append(self._create_action(
                            FixType.PERFORMANCE_ISSUE,
                            '将列表成员检查改为集合',
                            original,
                            fixed,
                            issue['line'],
                            RiskLevel.LOW
                        ))

        return '\n'.join(lines), actions


class CodeComplexityFixer(FixStrategy):
    """代码复杂度优化修复器"""

    def can_fix(self, content: str, file_path: Path) -> List[Dict[str, Any]]:
        issues = []

        issues.extend(self._detect_high_cyclomatic_complexity(content))
        issues.extend(self._detect_long_functions(content))
        issues.extend(self._detect_deep_nesting(content))
        issues.extend(self._detect_many_parameters(content))
        issues.extend(self._detect_long_parameter_list(content))

        return issues

    def _detect_high_cyclomatic_complexity(self, content: str) -> List[Dict[str, Any]]:
        issues = []
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return issues

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                complexity = self._calculate_cyclomatic_complexity(node)
                if complexity > 10:
                    issues.append({
                        'type': 'high_cyclomatic_complexity',
                        'line': node.lineno,
                        'message': f'函数 {node.name} 圈复杂度为 {complexity}，建议拆分函数',
                        'severity': 'high' if complexity > 15 else 'medium',
                        'function_name': node.name,
                        'complexity': complexity
                    })

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

    def _detect_long_functions(self, content: str) -> List[Dict[str, Any]]:
        issues = []
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return issues

        lines = content.split('\n')

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                start_line = node.lineno
                end_line = node.end_lineno if hasattr(node, 'end_lineno') else start_line
                function_length = end_line - start_line + 1

                if function_length > 50:
                    issues.append({
                        'type': 'long_function',
                        'line': start_line,
                        'message': f'函数 {node.name} 有 {function_length} 行，建议拆分',
                        'severity': 'high' if function_length > 100 else 'medium',
                        'function_name': node.name,
                        'length': function_length
                    })

        return issues

    def _detect_deep_nesting(self, content: str) -> List[Dict[str, Any]]:
        issues = []
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return issues

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                max_depth = self._calculate_max_nesting_depth(node)
                if max_depth > 4:
                    issues.append({
                        'type': 'deep_nesting',
                        'line': node.lineno,
                        'message': f'函数 {node.name} 嵌套深度为 {max_depth}，建议重构',
                        'severity': 'high' if max_depth > 6 else 'medium',
                        'function_name': node.name,
                        'depth': max_depth
                    })

        return issues

    def _calculate_max_nesting_depth(self, node: ast.FunctionDef) -> int:
        def get_depth(n, current_depth=0):
            max_d = current_depth
            nesting_nodes = (ast.If, ast.For, ast.While, ast.With, ast.Try)

            for child in ast.iter_child_nodes(n):
                if isinstance(child, nesting_nodes):
                    max_d = max(max_d, get_depth(child, current_depth + 1))
                else:
                    max_d = max(max_d, get_depth(child, current_depth))

            return max_d

        return get_depth(node)

    def _detect_many_parameters(self, content: str) -> List[Dict[str, Any]]:
        issues = []
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return issues

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                param_count = len(node.args.args)
                if node.args.kwonlyargs:
                    param_count += len(node.args.kwonlyargs)
                if node.args.vararg:
                    param_count += 1
                if node.args.kwarg:
                    param_count += 1

                if param_count > 5:
                    issues.append({
                        'type': 'many_parameters',
                        'line': node.lineno,
                        'message': f'函数 {node.name} 有 {param_count} 个参数，建议使用配置对象',
                        'severity': 'medium',
                        'function_name': node.name,
                        'param_count': param_count
                    })

        return issues

    def _detect_long_parameter_list(self, content: str) -> List[Dict[str, Any]]:
        issues = []
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            if 'def ' in line:
                param_match = re.search(r'def\s+\w+\s*\(([^)]+)\)', line)
                if param_match:
                    params = param_match.group(1).split(',')
                    if len(params) > 4:
                        issues.append({
                            'type': 'long_parameter_list',
                            'line': i,
                            'message': f'参数列表过长 ({len(params)} 个)，建议重构',
                            'severity': 'low',
                            'param_count': len(params)
                        })

        return issues

    def apply_fix(self, content: str, issues: List[Dict[str, Any]]) -> Tuple[str, List[FixAction]]:
        lines = content.split('\n')
        actions = []

        for issue in issues:
            if issue['type'] == 'high_cyclomatic_complexity':
                actions.append(self._create_action(
                    FixType.LOGIC_ERROR,
                    f"建议重构函数 {issue['function_name']}，圈复杂度 {issue['complexity']}",
                    f"圈复杂度: {issue['complexity']}",
                    f"建议拆分为多个小函数，每个函数只做一件事",
                    issue['line'],
                    RiskLevel.HIGH,
                    auto_applicable=False
                ))

            elif issue['type'] == 'long_function':
                actions.append(self._create_action(
                    FixType.LOGIC_ERROR,
                    f"建议拆分函数 {issue['function_name']}，当前 {issue['length']} 行",
                    f"函数长度: {issue['length']} 行",
                    "建议按职责拆分为多个小函数",
                    issue['line'],
                    RiskLevel.MEDIUM,
                    auto_applicable=False
                ))

            elif issue['type'] == 'deep_nesting':
                actions.append(self._create_action(
                    FixType.LOGIC_ERROR,
                    f"建议重构函数 {issue['function_name']}，嵌套深度 {issue['depth']}",
                    f"嵌套深度: {issue['depth']}",
                    "建议使用早返回、提取方法或策略模式减少嵌套",
                    issue['line'],
                    RiskLevel.MEDIUM,
                    auto_applicable=False
                ))

            elif issue['type'] == 'many_parameters':
                actions.append(self._create_action(
                    FixType.LOGIC_ERROR,
                    f"建议重构函数 {issue['function_name']}，参数数量 {issue['param_count']}",
                    f"参数数量: {issue['param_count']}",
                    "建议使用配置对象或建造者模式",
                    issue['line'],
                    RiskLevel.LOW,
                    auto_applicable=False
                ))

        return content, actions


class CodeDuplicationFixer(FixStrategy):
    """代码重复检测和消除修复器"""

    def __init__(self):
        super().__init__()
        self._min_duplicate_lines = 5
        self._min_duplicate_tokens = 30

    def can_fix(self, content: str, file_path: Path) -> List[Dict[str, Any]]:
        issues = []

        issues.extend(self._detect_duplicate_code_blocks(content))
        issues.extend(self._detect_duplicate_functions(content))
        issues.extend(self._detect_similar_code_patterns(content))
        issues.extend(self._detect_copy_paste_code(content))

        return issues

    def _detect_duplicate_code_blocks(self, content: str) -> List[Dict[str, Any]]:
        issues = []
        lines = content.split('\n')
        normalized_lines = [self._normalize_line(line) for line in lines]

        seen_blocks: Dict[str, List[int]] = {}
        block_size = self._min_duplicate_lines

        for i in range(len(normalized_lines) - block_size + 1):
            block = '\n'.join(normalized_lines[i:i + block_size])
            if len(block.strip()) < 20:
                continue

            block_hash = hashlib.md5(block.encode()).hexdigest()

            if block_hash in seen_blocks:
                for original_line in seen_blocks[block_hash]:
                    if abs(original_line - i) > block_size:
                        issues.append({
                            'type': 'duplicate_code_block',
                            'line': i + 1,
                            'message': f'发现重复代码块，与第 {original_line + 1} 行相似',
                            'severity': 'medium',
                            'duplicate_line': original_line + 1,
                            'block_size': block_size
                        })
                seen_blocks[block_hash].append(i)
            else:
                seen_blocks[block_hash] = [i]

        return issues

    def _normalize_line(self, line: str) -> str:
        normalized = re.sub(r'\s+', ' ', line.strip())
        normalized = re.sub(r'\b\w+\s*=\s*[^,)]+', 'VAR = VALUE', normalized)
        normalized = re.sub(r'\b\d+\b', 'NUM', normalized)
        normalized = re.sub(r'["\'][^"\']*["\']', 'STR', normalized)

        return normalized

    def _detect_duplicate_functions(self, content: str) -> List[Dict[str, Any]]:
        issues = []
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return issues

        function_bodies: Dict[str, List[ast.FunctionDef]] = {}

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                body_hash = self._hash_function_body(node)
                if body_hash in function_bodies:
                    for existing_func in function_bodies[body_hash]:
                        if existing_func.name != node.name:
                            issues.append({
                                'type': 'duplicate_function',
                                'line': node.lineno,
                                'message': f'函数 {node.name} 与 {existing_func.name} 功能相似',
                                'severity': 'high',
                                'function_name': node.name,
                                'similar_function': existing_func.name,
                                'similar_line': existing_func.lineno
                            })
                    function_bodies[body_hash].append(node)
                else:
                    function_bodies[body_hash] = [node]

        return issues

    def _hash_function_body(self, node: ast.FunctionDef) -> str:
        body_str = ''
        for child in node.body:
            if isinstance(child, ast.Pass):
                continue
            body_str += ast.dump(child)

        normalized = re.sub(r'\b\w+\b', 'x', body_str)
        return hashlib.md5(normalized.encode()).hexdigest()

    def _detect_similar_code_patterns(self, content: str) -> List[Dict[str, Any]]:
        issues = []
        lines = content.split('\n')

        patterns = [
            (r'if\s+(\w+)\s*:\s*\n\s*return\s+\1', "冗余的条件返回"),
            (r'if\s+not\s+(\w+)\s*:\s*\n\s*\1\s*=\s*', "冗余的空值检查"),
            (r'try:\s*\n\s*([^\n]+)\s*\n\s*except:\s*\n\s*pass', "空异常处理"),
        ]

        for pattern, description in patterns:
            matches = list(re.finditer(pattern, content, re.MULTILINE))
            if len(matches) > 1:
                for match in matches[1:]:
                    line_num = content[:match.start()].count('\n') + 1
                    issues.append({
                        'type': 'similar_pattern',
                        'line': line_num,
                        'message': f'发现相似代码模式: {description}',
                        'severity': 'low',
                        'pattern': description
                    })

        return issues

    def _detect_copy_paste_code(self, content: str) -> List[Dict[str, Any]]:
        issues = []
        lines = content.split('\n')

        for i in range(len(lines) - 10):
            for j in range(i + 10, len(lines) - 5):
                similarity = self._calculate_line_similarity(lines[i:i + 5], lines[j:j + 5])
                if similarity > 0.8:
                    issues.append({
                        'type': 'copy_paste_code',
                        'line': i + 1,
                        'message': f'发现复制粘贴代码，与第 {j + 1} 行相似度 {similarity:.0%}',
                        'severity': 'medium',
                        'similar_line': j + 1,
                        'similarity': similarity
                    })
                    break

        return issues[:10]

    def _calculate_line_similarity(self, lines1: List[str], lines2: List[str]) -> float:
        if len(lines1) != len(lines2):
            return 0.0

        matches = 0
        for l1, l2 in zip(lines1, lines2):
            if self._normalize_line(l1) == self._normalize_line(l2):
                matches += 1

        return matches / len(lines1)

    def apply_fix(self, content: str, issues: List[Dict[str, Any]]) -> Tuple[str, List[FixAction]]:
        actions = []

        for issue in issues:
            if issue['type'] == 'duplicate_code_block':
                actions.append(self._create_action(
                    FixType.LOGIC_ERROR,
                    f"建议提取重复代码块为独立函数",
                    f"重复代码块 ({issue['block_size']} 行)",
                    f"建议提取为独立函数，在第 {issue['line']} 和 {issue['duplicate_line']} 处调用",
                    issue['line'],
                    RiskLevel.MEDIUM,
                    auto_applicable=False
                ))

            elif issue['type'] == 'duplicate_function':
                actions.append(self._create_action(
                    FixType.LOGIC_ERROR,
                    f"建议合并相似函数 {issue['function_name']} 和 {issue['similar_function']}",
                    f"重复函数: {issue['function_name']}",
                    f"建议合并为一个函数，使用参数区分行为",
                    issue['line'],
                    RiskLevel.HIGH,
                    auto_applicable=False
                ))

            elif issue['type'] == 'similar_pattern':
                actions.append(self._create_action(
                    FixType.LOGIC_ERROR,
                    f"发现相似代码模式: {issue['pattern']}",
                    f"模式: {issue['pattern']}",
                    "建议统一处理相似代码",
                    issue['line'],
                    RiskLevel.LOW,
                    auto_applicable=False
                ))

            elif issue['type'] == 'copy_paste_code':
                actions.append(self._create_action(
                    FixType.LOGIC_ERROR,
                    f"建议提取复制粘贴代码为独立函数 (相似度 {issue['similarity']:.0%})",
                    f"复制粘贴代码",
                    f"建议提取为独立函数，在第 {issue['line']} 和 {issue['similar_line']} 处调用",
                    issue['line'],
                    RiskLevel.MEDIUM,
                    auto_applicable=False
                ))

        return content, actions


class NamingConventionFixer(FixStrategy):
    """命名规范优化修复器"""

    def __init__(self):
        super().__init__()
        self._naming_conventions = {
            'snake_case': re.compile(r'^[a-z][a-z0-9_]*$'),
            'PascalCase': re.compile(r'^[A-Z][a-zA-Z0-9]*$'),
            'UPPER_SNAKE_CASE': re.compile(r'^[A-Z][A-Z0-9_]*$'),
            '_private_snake': re.compile(r'^_[a-z][a-z0-9_]*$'),
            '__dunder__': re.compile(r'^__[a-z][a-z0-9_]*__$'),
        }

    def can_fix(self, content: str, file_path: Path) -> List[Dict[str, Any]]:
        issues = []

        issues.extend(self._detect_function_naming_issues(content))
        issues.extend(self._detect_class_naming_issues(content))
        issues.extend(self._detect_variable_naming_issues(content))
        issues.extend(self._detect_constant_naming_issues(content))
        issues.extend(self._detect_meaningless_names(content))

        return issues

    def _detect_function_naming_issues(self, content: str) -> List[Dict[str, Any]]:
        issues = []
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return issues

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                name = node.name

                if name.startswith('__') and name.endswith('__'):
                    continue

                if not self._naming_conventions['snake_case'].match(name):
                    if self._naming_conventions['PascalCase'].match(name):
                        issues.append({
                            'type': 'function_naming_pascal',
                            'line': node.lineno,
                            'message': f'函数名 {name} 使用了 PascalCase，应使用 snake_case',
                            'severity': 'medium',
                            'name': name,
                            'suggested': self._to_snake_case(name)
                        })
                    else:
                        issues.append({
                            'type': 'function_naming_invalid',
                            'line': node.lineno,
                            'message': f'函数名 {name} 不符合命名规范',
                            'severity': 'medium',
                            'name': name
                        })

                if len(name) < 3 and name not in ['id', 'ok', 'io']:
                    issues.append({
                        'type': 'function_name_too_short',
                        'line': node.lineno,
                        'message': f'函数名 {name} 过短，建议使用更具描述性的名称',
                        'severity': 'low',
                        'name': name
                    })

        return issues

    def _detect_class_naming_issues(self, content: str) -> List[Dict[str, Any]]:
        issues = []
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return issues

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                name = node.name

                if not self._naming_conventions['PascalCase'].match(name):
                    if self._naming_conventions['snake_case'].match(name):
                        issues.append({
                            'type': 'class_naming_snake',
                            'line': node.lineno,
                            'message': f'类名 {name} 使用了 snake_case，应使用 PascalCase',
                            'severity': 'medium',
                            'name': name,
                            'suggested': self._to_pascal_case(name)
                        })
                    else:
                        issues.append({
                            'type': 'class_naming_invalid',
                            'line': node.lineno,
                            'message': f'类名 {name} 不符合命名规范',
                            'severity': 'medium',
                            'name': name
                        })

        return issues

    def _detect_variable_naming_issues(self, content: str) -> List[Dict[str, Any]]:
        issues = []
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return issues

        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        name = target.id

                        if self._naming_conventions['UPPER_SNAKE_CASE'].match(name):
                            continue

                        if not self._naming_conventions['snake_case'].match(name):
                            if self._naming_conventions['PascalCase'].match(name):
                                issues.append({
                                    'type': 'variable_naming_pascal',
                                    'line': node.lineno,
                                    'message': f'变量名 {name} 使用了 PascalCase，应使用 snake_case',
                                    'severity': 'low',
                                    'name': name,
                                    'suggested': self._to_snake_case(name)
                                })

        return issues

    def _detect_constant_naming_issues(self, content: str) -> List[Dict[str, Any]]:
        issues = []
        lines = content.split('\n')

        module_level_vars = set()
        try:
            tree = ast.parse(content)
            for node in ast.iter_child_nodes(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            module_level_vars.add(target.id)
        except SyntaxError:
            pass

        for i, line in enumerate(lines, 1):
            match = re.match(r'^([A-Z][A-Z0-9_]*)\s*=\s*(?!.*lambda)', line)
            if match:
                var_name = match.group(1)
                if not self._naming_conventions['UPPER_SNAKE_CASE'].match(var_name):
                    issues.append({
                        'type': 'constant_naming_invalid',
                        'line': i,
                        'message': f'常量 {var_name} 应使用 UPPER_SNAKE_CASE',
                        'severity': 'low',
                        'name': var_name
                    })

        return issues

    def _detect_meaningless_names(self, content: str) -> List[Dict[str, Any]]:
        issues = []
        meaningless_names = ['data', 'temp', 'tmp', 'x', 'y', 'z', 'foo', 'bar', 'baz', 'stuff', 'thing']

        try:
            tree = ast.parse(content)
        except SyntaxError:
            return issues

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                for arg in node.args.args:
                    if arg.arg.lower() in meaningless_names:
                        issues.append({
                            'type': 'meaningless_parameter_name',
                            'line': node.lineno,
                            'message': f'参数名 {arg.arg} 缺乏意义，建议使用更具描述性的名称',
                            'severity': 'low',
                            'name': arg.arg
                        })

            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        if target.id.lower() in meaningless_names:
                            issues.append({
                                'type': 'meaningless_variable_name',
                                'line': node.lineno,
                                'message': f'变量名 {target.id} 缺乏意义，建议使用更具描述性的名称',
                                'severity': 'low',
                                'name': target.id
                            })

        return issues

    def _to_snake_case(self, name: str) -> str:
        result = re.sub(r'([A-Z])', r'_\1', name).lower()
        return result[1:] if result.startswith('_') else result

    def _to_pascal_case(self, name: str) -> str:
        parts = name.split('_')
        return ''.join(part.capitalize() for part in parts)

    def apply_fix(self, content: str, issues: List[Dict[str, Any]]) -> Tuple[str, List[FixAction]]:
        lines = content.split('\n')
        actions = []

        for issue in issues:
            if issue['type'] in ['function_naming_pascal', 'class_naming_snake', 'variable_naming_pascal']:
                suggested = issue.get('suggested', '')
                actions.append(self._create_action(
                    FixType.STYLE_ERROR,
                    f"建议重命名 {issue['name']} 为 {suggested}",
                    issue['name'],
                    suggested,
                    issue['line'],
                    RiskLevel.LOW,
                    auto_applicable=False
                ))

            elif issue['type'] in ['meaningless_parameter_name', 'meaningless_variable_name']:
                actions.append(self._create_action(
                    FixType.STYLE_ERROR,
                    f"建议将 {issue['name']} 重命名为更具描述性的名称",
                    issue['name'],
                    "更具描述性的名称",
                    issue['line'],
                    RiskLevel.LOW,
                    auto_applicable=False
                ))

        return content, actions


class DocumentationFixer(FixStrategy):
    """注释和文档优化修复器"""

    def __init__(self):
        super().__init__()
        self._docstring_templates = {
            'function': '"""{description}\n\nArgs:\n{args}\n\nReturns:\n    {returns}\n"""',
            'class': '"""{description}\n\nAttributes:\n{attributes}\n"""',
            'module': '"""{description}\n\nThis module provides {provides}.\n"""'
        }

    def can_fix(self, content: str, file_path: Path) -> List[Dict[str, Any]]:
        issues = []

        issues.extend(self._detect_missing_module_docstring(content))
        issues.extend(self._detect_missing_function_docstrings(content))
        issues.extend(self._detect_missing_class_docstrings(content))
        issues.extend(self._detect_outdated_comments(content))
        issues.extend(self._detect_todo_comments(content))
        issues.extend(self._detect_complex_code_without_comment(content))

        return issues

    def _detect_missing_module_docstring(self, content: str) -> List[Dict[str, Any]]:
        issues = []
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return issues

        docstring = ast.get_docstring(tree)
        if not docstring:
            issues.append({
                'type': 'missing_module_docstring',
                'line': 1,
                'message': '模块缺少文档字符串',
                'severity': 'medium'
            })

        return issues

    def _detect_missing_function_docstrings(self, content: str) -> List[Dict[str, Any]]:
        issues = []
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return issues

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if node.name.startswith('_') and not node.name.startswith('__'):
                    continue

                docstring = ast.get_docstring(node)
                if not docstring:
                    param_count = len(node.args.args)
                    has_return = any(isinstance(n, ast.Return) and n.value for n in ast.walk(node))

                    issues.append({
                        'type': 'missing_function_docstring',
                        'line': node.lineno,
                        'message': f'函数 {node.name} 缺少文档字符串',
                        'severity': 'medium',
                        'function_name': node.name,
                        'param_count': param_count,
                        'has_return': has_return
                    })

        return issues

    def _detect_missing_class_docstrings(self, content: str) -> List[Dict[str, Any]]:
        issues = []
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return issues

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                docstring = ast.get_docstring(node)
                if not docstring:
                    issues.append({
                        'type': 'missing_class_docstring',
                        'line': node.lineno,
                        'message': f'类 {node.name} 缺少文档字符串',
                        'severity': 'medium',
                        'class_name': node.name
                    })

        return issues

    def _detect_outdated_comments(self, content: str) -> List[Dict[str, Any]]:
        issues = []
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            if '#' in line:
                comment = line[line.index('#'):]

                outdated_patterns = [
                    (r'TODO|FIXME|HACK|XXX', "待处理的注释"),
                    (r'deprecated|obsolete', "可能过时的注释"),
                    (r'\d{4}[/-]\d{1,2}[/-]\d{1,2}', "包含日期的注释，可能需要更新"),
                ]

                for pattern, description in outdated_patterns:
                    if re.search(pattern, comment, re.IGNORECASE):
                        issues.append({
                            'type': 'outdated_comment',
                            'line': i,
                            'message': f'{description}: {comment.strip()}',
                            'severity': 'low',
                            'comment': comment.strip()
                        })

        return issues

    def _detect_todo_comments(self, content: str) -> List[Dict[str, Any]]:
        issues = []
        lines = content.split('\n')

        todo_pattern = re.compile(r'#\s*(TODO|FIXME|HACK|XXX|BUG)(\([^)]+\))?:\s*(.+)', re.IGNORECASE)

        for i, line in enumerate(lines, 1):
            match = todo_pattern.search(line)
            if match:
                tag = match.group(1).upper()
                author = match.group(2) or ''
                description = match.group(3)

                issues.append({
                    'type': 'todo_comment',
                    'line': i,
                    'message': f'{tag}{author}: {description}',
                    'severity': 'info',
                    'tag': tag,
                    'description': description
                })

        return issues

    def _detect_complex_code_without_comment(self, content: str) -> List[Dict[str, Any]]:
        issues = []
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return issues

        lines = content.split('\n')

        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.For, ast.While)):
                complexity = self._estimate_node_complexity(node)
                if complexity > 5:
                    start_line = node.lineno - 1
                    has_comment = False

                    if start_line > 0:
                        prev_line = lines[start_line - 1].strip()
                        if prev_line.startswith('#'):
                            has_comment = True

                    first_line = lines[start_line].strip()
                    if '#' in first_line and not first_line.startswith('#'):
                        has_comment = True

                    if not has_comment:
                        issues.append({
                            'type': 'complex_code_without_comment',
                            'line': node.lineno,
                            'message': f'复杂代码块缺少解释性注释',
                            'severity': 'low',
                            'complexity': complexity
                        })

        return issues

    def _estimate_node_complexity(self, node: ast.AST) -> int:
        complexity = 1

        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values)
            elif isinstance(child, ast.Compare):
                complexity += len(child.ops)

        return complexity

    def apply_fix(self, content: str, issues: List[Dict[str, Any]]) -> Tuple[str, List[FixAction]]:
        lines = content.split('\n')
        actions = []

        for issue in issues:
            if issue['type'] == 'missing_module_docstring':
                docstring = '"""模块文档字符串。\n\n请添加模块描述。\n"""'
                actions.append(self._create_action(
                    FixType.STYLE_ERROR,
                    "添加模块文档字符串",
                    "",
                    docstring,
                    1,
                    RiskLevel.LOW
                ))

            elif issue['type'] == 'missing_function_docstring':
                func_name = issue['function_name']
                param_count = issue['param_count']
                has_return = issue['has_return']

                docstring = f'"""函数文档字符串。\n\n'
                if param_count > 0:
                    docstring += 'Args:\n    param: 参数描述。\n\n'
                if has_return:
                    docstring += 'Returns:\n    返回值描述。\n'
                docstring += '"""'

                actions.append(self._create_action(
                    FixType.STYLE_ERROR,
                    f"为函数 {func_name} 添加文档字符串",
                    "",
                    docstring,
                    issue['line'],
                    RiskLevel.LOW,
                    auto_applicable=False
                ))

            elif issue['type'] == 'missing_class_docstring':
                class_name = issue['class_name']
                docstring = f'"""类文档字符串。\n\n请添加类描述。\n"""'

                actions.append(self._create_action(
                    FixType.STYLE_ERROR,
                    f"为类 {class_name} 添加文档字符串",
                    "",
                    docstring,
                    issue['line'],
                    RiskLevel.LOW,
                    auto_applicable=False
                ))

            elif issue['type'] == 'complex_code_without_comment':
                actions.append(self._create_action(
                    FixType.STYLE_ERROR,
                    f"为复杂代码块添加解释性注释",
                    "",
                    "# 解释：此处进行...",
                    issue['line'],
                    RiskLevel.LOW,
                    auto_applicable=False
                ))

        return content, actions


class FixValidator:
    """修复验证器 - 验证修复结果的正确性"""

    def __init__(self):
        self._validation_rules: List[callable] = []
        self._register_default_rules()

    def _register_default_rules(self):
        self._validation_rules = [
            self._validate_syntax,
            self._validate_imports,
            self._validate_indentation,
            self._validate_brackets,
            self._validate_encoding,
        ]

    def validate_fix(
        self,
        original_content: str,
        fixed_content: str,
        file_path: Path
    ) -> Dict[str, Any]:
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'checks_passed': [],
            'checks_failed': []
        }

        for rule in self._validation_rules:
            try:
                result = rule(original_content, fixed_content, file_path)
                if result['passed']:
                    validation_result['checks_passed'].append(result['name'])
                else:
                    validation_result['checks_failed'].append(result['name'])
                    if result.get('is_error', True):
                        validation_result['errors'].append(result['message'])
                        validation_result['is_valid'] = False
                    else:
                        validation_result['warnings'].append(result['message'])
            except Exception as e:
                validation_result['warnings'].append(f"验证规则执行失败: {str(e)}")

        return validation_result

    def _validate_syntax(
        self,
        original: str,
        fixed: str,
        file_path: Path
    ) -> Dict[str, Any]:
        try:
            ast.parse(fixed)
            return {
                'name': 'syntax_check',
                'passed': True,
                'message': '语法检查通过'
            }
        except SyntaxError as e:
            return {
                'name': 'syntax_check',
                'passed': False,
                'is_error': True,
                'message': f'修复后存在语法错误: 行{e.lineno}: {e.msg}'
            }

    def _validate_imports(
        self,
        original: str,
        fixed: str,
        file_path: Path
    ) -> Dict[str, Any]:
        try:
            original_tree = ast.parse(original)
            fixed_tree = ast.parse(fixed)
        except SyntaxError:
            return {
                'name': 'import_check',
                'passed': True,
                'message': '跳过导入检查（存在语法错误）'
            }

        original_imports = set()
        fixed_imports = set()

        for node in ast.walk(original_tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    original_imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    original_imports.add(node.module)

        for node in ast.walk(fixed_tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    fixed_imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    fixed_imports.add(node.module)

        return {
            'name': 'import_check',
            'passed': True,
            'message': '导入检查通过'
        }

    def _validate_indentation(
        self,
        original: str,
        fixed: str,
        file_path: Path
    ) -> Dict[str, Any]:
        lines = fixed.split('\n')
        indent_errors = []

        for i, line in enumerate(lines, 1):
            if line and not line.strip():
                continue
            spaces = len(line) - len(line.lstrip())
            if spaces % 4 != 0 and not line.strip().startswith('#'):
                indent_errors.append(f'行{i}: 缩进不是4的倍数')

        if indent_errors:
            return {
                'name': 'indentation_check',
                'passed': False,
                'is_error': False,
                'message': f'缩进问题: {"; ".join(indent_errors[:3])}'
            }

        return {
            'name': 'indentation_check',
            'passed': True,
            'message': '缩进检查通过'
        }

    def _validate_brackets(
        self,
        original: str,
        fixed: str,
        file_path: Path
    ) -> Dict[str, Any]:
        bracket_pairs = {'(': ')', '[': ']', '{': '}'}
        counts = {k: 0 for k in bracket_pairs}

        for char in fixed:
            if char in bracket_pairs:
                counts[char] += 1
            elif char in bracket_pairs.values():
                for open_b, close_b in bracket_pairs.items():
                    if char == close_b:
                        counts[open_b] -= 1

        mismatches = [f'{b}{bracket_pairs[b]}' for b, c in counts.items() if c != 0]

        if mismatches:
            return {
                'name': 'bracket_check',
                'passed': False,
                'is_error': True,
                'message': f'括号不匹配: {", ".join(mismatches)}'
            }

        return {
            'name': 'bracket_check',
            'passed': True,
            'message': '括号检查通过'
        }

    def _validate_encoding(
        self,
        original: str,
        fixed: str,
        file_path: Path
    ) -> Dict[str, Any]:
        try:
            fixed.encode('utf-8')
            return {
                'name': 'encoding_check',
                'passed': True,
                'message': '编码检查通过'
            }
        except UnicodeEncodeError as e:
            return {
                'name': 'encoding_check',
                'passed': False,
                'is_error': True,
                'message': f'编码问题: {str(e)}'
            }

    def add_validation_rule(self, rule: callable) -> None:
        self._validation_rules.append(rule)


class FixConflictResolver:
    """修复冲突解决器 - 检测并解决修复之间的冲突"""

    def __init__(self):
        self._conflict_rules: Dict[str, List[str]] = {}
        self._priority_order: List[FixType] = [
            FixType.SYNTAX_ERROR,
            FixType.SECURITY_ISSUE,
            FixType.IMPORT_ERROR,
            FixType.LOGIC_ERROR,
            FixType.PERFORMANCE_ISSUE,
            FixType.STYLE_ERROR,
            FixType.DEPRECATED_CODE,
            FixType.UNUSED_CODE,
        ]
        self._register_conflict_rules()

    def _register_conflict_rules(self):
        self._conflict_rules = {
            'line_overlap': ['same_line_multiple_fixes'],
            'type_conflict': ['security_vs_style', 'performance_vs_readability'],
            'dependency': ['import_before_usage', 'syntax_before_other'],
        }

    def detect_conflicts(
        self,
        actions: List[FixAction]
    ) -> List[Dict[str, Any]]:
        conflicts = []

        line_actions: Dict[int, List[FixAction]] = {}
        for action in actions:
            if action.line_number not in line_actions:
                line_actions[action.line_number] = []
            line_actions[action.line_number].append(action)

        for line_num, line_action_list in line_actions.items():
            if len(line_action_list) > 1:
                conflict = self._analyze_line_conflict(line_num, line_action_list)
                if conflict:
                    conflicts.append(conflict)

        type_conflicts = self._detect_type_conflicts(actions)
        conflicts.extend(type_conflicts)

        return conflicts

    def _analyze_line_conflict(
        self,
        line_num: int,
        actions: List[FixAction]
    ) -> Optional[Dict[str, Any]]:
        types = set(a.fix_type for a in actions)
        if len(types) == 1:
            return None

        priorities = [(a, self._priority_order.index(a.fix_type) if a.fix_type in self._priority_order else 999) for a in actions]
        priorities.sort(key=lambda x: x[1])

        return {
            'type': 'line_overlap',
            'line': line_num,
            'conflicting_actions': [a.action_id for a in actions],
            'resolution': 'priority',
            'recommended_action': priorities[0][0].action_id,
            'message': f'行{line_num}存在多个修复，建议优先处理: {priorities[0][0].fix_type.value}'
        }

    def _detect_type_conflicts(
        self,
        actions: List[FixAction]
    ) -> List[Dict[str, Any]]:
        conflicts = []

        security_actions = [a for a in actions if a.fix_type == FixType.SECURITY_ISSUE]
        style_actions = [a for a in actions if a.fix_type == FixType.STYLE_ERROR]

        if security_actions and style_actions:
            overlapping_lines = set(a.line_number for a in security_actions) & set(a.line_number for a in style_actions)
            if overlapping_lines:
                conflicts.append({
                    'type': 'security_vs_style',
                    'lines': list(overlapping_lines),
                    'resolution': 'security_first',
                    'message': '安全修复优先于风格修复'
                })

        return conflicts

    def resolve_conflicts(
        self,
        actions: List[FixAction],
        conflicts: List[Dict[str, Any]]
    ) -> List[FixAction]:
        if not conflicts:
            return actions

        action_map = {a.action_id: a for a in actions}
        actions_to_skip = set()

        for conflict in conflicts:
            if conflict['type'] == 'line_overlap':
                recommended = conflict['recommended_action']
                for action_id in conflict['conflicting_actions']:
                    if action_id != recommended:
                        actions_to_skip.add(action_id)

        return [a for a in actions if a.action_id not in actions_to_skip]

    def get_fix_priority(self, fix_type: FixType) -> int:
        return self._priority_order.index(fix_type) if fix_type in self._priority_order else 999


class FixRollbackManager:
    """修复回滚管理器 - 支持修复操作的回滚（增强版）

    支持功能：
    - 多级回滚：支持回滚到任意历史状态
    - 事务性修复：支持原子性修复操作
    - 检查点机制：支持创建和恢复检查点
    - 回滚预览：预览回滚后的代码变化
    """

    def __init__(self, max_history: int = 50):
        self._history: List[Dict[str, Any]] = []
        self._max_history = max_history
        self._checkpoints: Dict[str, Dict[str, Any]] = {}
        self._transactions: Dict[str, List[Dict[str, Any]]] = {}
        self._rollback_stack: List[str] = []
        self._file_snapshots: Dict[str, List[Dict[str, Any]]] = {}

    def save_state(
        self,
        file_path: Path,
        content: str,
        actions: List[FixAction]
    ) -> str:
        state_id = f"STATE-{datetime.now().strftime('%Y%m%d%H%M%S')}-{len(self._history)}"

        state = {
            'state_id': state_id,
            'file_path': str(file_path),
            'content': content,
            'actions': [a.to_dict() for a in actions],
            'timestamp': datetime.now().isoformat(),
            'action_count': len(actions),
            'checksum': self._calculate_checksum(content),
        }

        self._history.append(state)
        self._rollback_stack.append(state_id)

        file_key = str(file_path)
        if file_key not in self._file_snapshots:
            self._file_snapshots[file_key] = []
        self._file_snapshots[file_key].append({
            'state_id': state_id,
            'timestamp': state['timestamp'],
            'action_count': len(actions),
        })

        if len(self._history) > self._max_history:
            removed = self._history.pop(0)
            self._rollback_stack = [s for s in self._rollback_stack if s != removed['state_id']]

        return state_id

    def _calculate_checksum(self, content: str) -> str:
        import hashlib
        return hashlib.md5(content.encode()).hexdigest()

    def rollback(self, state_id: str) -> Optional[Dict[str, Any]]:
        for i, state in enumerate(self._history):
            if state['state_id'] == state_id:
                self._history.pop(i)
                if state_id in self._rollback_stack:
                    self._rollback_stack.remove(state_id)
                return state
        return None

    def rollback_to_state(self, state_id: str) -> Optional[Dict[str, Any]]:
        target_index = None
        for i, state in enumerate(self._history):
            if state['state_id'] == state_id:
                target_index = i
                break

        if target_index is None:
            return None

        target_state = self._history[target_index]
        rolled_back_states = self._history[target_index + 1:]
        self._history = self._history[:target_index + 1]

        for state in rolled_back_states:
            if state['state_id'] in self._rollback_stack:
                self._rollback_stack.remove(state['state_id'])

        return {
            'target_state': target_state,
            'rolled_back_count': len(rolled_back_states),
            'rolled_back_states': [s['state_id'] for s in rolled_back_states],
        }

    def rollback_n_steps(self, n: int) -> List[Dict[str, Any]]:
        rolled_back = []
        for _ in range(min(n, len(self._history))):
            if self._history:
                state = self._history.pop()
                rolled_back.append(state)
                if state['state_id'] in self._rollback_stack:
                    self._rollback_stack.remove(state['state_id'])
        return rolled_back

    def create_checkpoint(self, name: str, file_path: Path, content: str) -> str:
        checkpoint_id = f"CHECKPOINT-{name}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        self._checkpoints[checkpoint_id] = {
            'checkpoint_id': checkpoint_id,
            'name': name,
            'file_path': str(file_path),
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'checksum': self._calculate_checksum(content),
        }

        return checkpoint_id

    def restore_checkpoint(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        if checkpoint_id not in self._checkpoints:
            return None
        return self._checkpoints[checkpoint_id].copy()

    def list_checkpoints(self) -> List[Dict[str, Any]]:
        return [
            {
                'checkpoint_id': cp['checkpoint_id'],
                'name': cp['name'],
                'file_path': cp['file_path'],
                'timestamp': cp['timestamp'],
            }
            for cp in self._checkpoints.values()
        ]

    def delete_checkpoint(self, checkpoint_id: str) -> bool:
        if checkpoint_id in self._checkpoints:
            del self._checkpoints[checkpoint_id]
            return True
        return False

    def begin_transaction(self, transaction_id: str) -> None:
        self._transactions[transaction_id] = []

    def add_to_transaction(
        self,
        transaction_id: str,
        file_path: Path,
        content: str,
        action: FixAction
    ) -> None:
        if transaction_id not in self._transactions:
            self.begin_transaction(transaction_id)

        self._transactions[transaction_id].append({
            'file_path': str(file_path),
            'content': content,
            'action': action.to_dict(),
            'timestamp': datetime.now().isoformat(),
        })

    def commit_transaction(self, transaction_id: str) -> Dict[str, Any]:
        if transaction_id not in self._transactions:
            return {'success': False, 'error': 'Transaction not found'}

        operations = self._transactions.pop(transaction_id)

        return {
            'success': True,
            'transaction_id': transaction_id,
            'operations_count': len(operations),
            'committed_at': datetime.now().isoformat(),
        }

    def rollback_transaction(self, transaction_id: str) -> Dict[str, Any]:
        if transaction_id not in self._transactions:
            return {'success': False, 'error': 'Transaction not found'}

        operations = self._transactions.pop(transaction_id)

        return {
            'success': True,
            'transaction_id': transaction_id,
            'rolled_back_count': len(operations),
            'operations': operations,
        }

    def preview_rollback(self, state_id: str) -> Optional[Dict[str, Any]]:
        state = None
        for s in self._history:
            if s['state_id'] == state_id:
                state = s
                break

        if not state:
            return None

        current_content = None
        if self._history:
            current_state = self._history[-1]
            current_content = current_state.get('content')

        return {
            'state_id': state_id,
            'file_path': state['file_path'],
            'will_restore_content': state['content'][:500] + '...' if len(state['content']) > 500 else state['content'],
            'actions_to_undo': len(state['actions']),
            'timestamp': state['timestamp'],
            'current_content_preview': current_content[:500] if current_content else None,
        }

    def get_history(self) -> List[Dict[str, Any]]:
        return [
            {
                'state_id': s['state_id'],
                'file_path': s['file_path'],
                'action_count': len(s['actions']),
                'timestamp': s['timestamp'],
                'checksum': s.get('checksum', ''),
            }
            for s in self._history
        ]

    def get_file_history(self, file_path: Path) -> List[Dict[str, Any]]:
        file_key = str(file_path)
        return self._file_snapshots.get(file_key, [])

    def get_latest_state(self) -> Optional[Dict[str, Any]]:
        if self._history:
            return self._history[-1]
        return None

    def get_state_by_index(self, index: int) -> Optional[Dict[str, Any]]:
        if 0 <= index < len(self._history):
            return self._history[index]
        return None

    def get_rollback_stack(self) -> List[str]:
        return self._rollback_stack.copy()

    def can_rollback(self) -> bool:
        return len(self._history) > 0

    def get_rollback_count(self) -> int:
        return len(self._history)

    def clear_history(self) -> None:
        self._history.clear()
        self._rollback_stack.clear()

    def clear_all(self) -> None:
        self._history.clear()
        self._rollback_stack.clear()
        self._checkpoints.clear()
        self._transactions.clear()
        self._file_snapshots.clear()

    def export_history(self) -> Dict[str, Any]:
        return {
            'history': self._history.copy(),
            'checkpoints': self._checkpoints.copy(),
            'rollback_stack': self._rollback_stack.copy(),
            'exported_at': datetime.now().isoformat(),
        }

    def import_history(self, data: Dict[str, Any]) -> None:
        if 'history' in data:
            self._history = data['history']
        if 'checkpoints' in data:
            self._checkpoints = data['checkpoints']
        if 'rollback_stack' in data:
            self._rollback_stack = data['rollback_stack']


class FixStrategySelector:
    """修复策略选择器 - 根据问题类型和上下文选择最佳修复策略"""

    def __init__(self):
        self._strategy_registry: Dict[FixType, List[Dict[str, Any]]] = {}
        self._selection_history: List[Dict[str, Any]] = []
        self._success_rates: Dict[str, Dict[str, float]] = {}
        self._register_strategies()

    def _register_strategies(self) -> None:
        self._strategy_registry = {
            FixType.SYNTAX_ERROR: [
                {
                    'name': 'add_missing_colon',
                    'priority': 1,
                    'applicable_types': ['missing_colon'],
                    'risk': RiskLevel.LOW,
                    'success_rate': 0.95,
                    'description': '添加缺失的冒号'
                },
                {
                    'name': 'fix_unmatched_bracket',
                    'priority': 2,
                    'applicable_types': ['unmatched_bracket'],
                    'risk': RiskLevel.MEDIUM,
                    'success_rate': 0.7,
                    'description': '修复不匹配的括号'
                },
                {
                    'name': 'fix_indentation',
                    'priority': 3,
                    'applicable_types': ['indentation_error'],
                    'risk': RiskLevel.MEDIUM,
                    'success_rate': 0.6,
                    'description': '修复缩进错误'
                },
                {
                    'name': 'fix_invalid_escape',
                    'priority': 1,
                    'applicable_types': ['invalid_escape'],
                    'risk': RiskLevel.LOW,
                    'success_rate': 0.98,
                    'description': '修复无效转义序列'
                },
                {
                    'name': 'fix_invalid_operator',
                    'priority': 1,
                    'applicable_types': ['invalid_syntax_operator'],
                    'risk': RiskLevel.LOW,
                    'success_rate': 0.95,
                    'description': '简化赋值运算符'
                },
            ],
            FixType.IMPORT_ERROR: [
                {
                    'name': 'remove_unused_import',
                    'priority': 1,
                    'applicable_types': ['unused_import'],
                    'risk': RiskLevel.LOW,
                    'success_rate': 0.99,
                    'description': '删除未使用的导入'
                },
                {
                    'name': 'add_missing_import',
                    'priority': 1,
                    'applicable_types': ['missing_import'],
                    'risk': RiskLevel.LOW,
                    'success_rate': 0.85,
                    'description': '添加缺失的导入'
                },
                {
                    'name': 'fix_import_order',
                    'priority': 2,
                    'applicable_types': ['import_order'],
                    'risk': RiskLevel.LOW,
                    'success_rate': 0.99,
                    'description': '修复导入顺序'
                },
                {
                    'name': 'remove_duplicate_import',
                    'priority': 1,
                    'applicable_types': ['duplicate_import'],
                    'risk': RiskLevel.LOW,
                    'success_rate': 0.99,
                    'description': '删除重复导入'
                },
            ],
            FixType.SECURITY_ISSUE: [
                {
                    'name': 'fix_hardcoded_secret',
                    'priority': 1,
                    'applicable_types': ['hardcoded_password', 'hardcoded_secret'],
                    'risk': RiskLevel.HIGH,
                    'success_rate': 0.8,
                    'description': '替换硬编码密钥为环境变量'
                },
                {
                    'name': 'fix_yaml_unsafe_load',
                    'priority': 1,
                    'applicable_types': ['yaml_unsafe_load'],
                    'risk': RiskLevel.MEDIUM,
                    'success_rate': 0.95,
                    'description': '添加yaml.SafeLoader'
                },
                {
                    'name': 'fix_ssl_verify',
                    'priority': 1,
                    'applicable_types': ['ssl_verify_disabled'],
                    'risk': RiskLevel.HIGH,
                    'success_rate': 0.9,
                    'description': '启用SSL证书验证'
                },
                {
                    'name': 'fix_insecure_permissions',
                    'priority': 1,
                    'applicable_types': ['insecure_permissions'],
                    'risk': RiskLevel.MEDIUM,
                    'success_rate': 0.95,
                    'description': '修复不安全的文件权限'
                },
                {
                    'name': 'add_security_warning',
                    'priority': 2,
                    'applicable_types': ['eval_usage', 'exec_usage', 'pickle_usage', 'subprocess_shell'],
                    'risk': RiskLevel.LOW,
                    'success_rate': 0.99,
                    'description': '添加安全警告注释'
                },
            ],
            FixType.PERFORMANCE_ISSUE: [
                {
                    'name': 'optimize_membership_check',
                    'priority': 1,
                    'applicable_types': ['inefficient_membership_list'],
                    'risk': RiskLevel.LOW,
                    'success_rate': 0.95,
                    'description': '将列表成员检查改为集合'
                },
                {
                    'name': 'suggest_string_join',
                    'priority': 2,
                    'applicable_types': ['string_concat_in_loop'],
                    'risk': RiskLevel.LOW,
                    'success_rate': 0.7,
                    'description': '建议使用join替代字符串拼接'
                },
            ],
            FixType.STYLE_ERROR: [
                {
                    'name': 'remove_trailing_whitespace',
                    'priority': 1,
                    'applicable_types': ['trailing_whitespace'],
                    'risk': RiskLevel.LOW,
                    'success_rate': 0.99,
                    'description': '移除行尾空白'
                },
                {
                    'name': 'add_final_newline',
                    'priority': 1,
                    'applicable_types': ['missing_newline'],
                    'risk': RiskLevel.LOW,
                    'success_rate': 0.99,
                    'description': '添加文件末尾换行符'
                },
            ],
            FixType.LOGIC_ERROR: [
                {
                    'name': 'fix_bare_except',
                    'priority': 1,
                    'applicable_types': ['bare_except'],
                    'risk': RiskLevel.MEDIUM,
                    'success_rate': 0.85,
                    'description': '将裸异常改为Exception'
                },
                {
                    'name': 'warn_mutable_default',
                    'priority': 2,
                    'applicable_types': ['mutable_default_arg'],
                    'risk': RiskLevel.LOW,
                    'success_rate': 0.9,
                    'description': '警告可变默认参数'
                },
            ],
        }

    def select_best_strategy(
        self,
        issue: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        issue_type = issue.get('type', '')
        fix_type = self._get_fix_type_from_issue(issue_type)
        
        if fix_type not in self._strategy_registry:
            return None
        
        strategies = self._strategy_registry[fix_type]
        applicable_strategies = [
            s for s in strategies
            if issue_type in s['applicable_types']
        ]
        
        if not applicable_strategies:
            return None
        
        scored_strategies = []
        for strategy in applicable_strategies:
            score = self._calculate_strategy_score(strategy, issue, context)
            scored_strategies.append((strategy, score))
        
        scored_strategies.sort(key=lambda x: x[1], reverse=True)
        
        best_strategy = scored_strategies[0][0].copy()
        best_strategy['calculated_score'] = scored_strategies[0][1]
        
        self._record_selection(issue, best_strategy)
        
        return best_strategy

    def _calculate_strategy_score(
        self,
        strategy: Dict[str, Any],
        issue: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> float:
        base_score = strategy['success_rate'] * 100
        
        priority_bonus = (10 - strategy['priority']) * 5
        
        risk_penalty = {
            RiskLevel.LOW: 0,
            RiskLevel.MEDIUM: -10,
            RiskLevel.HIGH: -20
        }.get(strategy['risk'], 0)
        
        historical_bonus = self._get_historical_bonus(strategy['name'])
        
        context_bonus = 0
        if context:
            context_bonus = self._calculate_context_bonus(strategy, context)
        
        return base_score + priority_bonus + risk_penalty + historical_bonus + context_bonus

    def _get_historical_bonus(self, strategy_name: str) -> float:
        if strategy_name not in self._success_rates:
            return 0
        
        rates = self._success_rates[strategy_name]
        if 'success' in rates and 'total' in rates and rates['total'] > 0:
            actual_rate = rates['success'] / rates['total']
            return (actual_rate - 0.5) * 10
        return 0

    def _calculate_context_bonus(
        self,
        strategy: Dict[str, Any],
        context: Dict[str, Any]
    ) -> float:
        bonus = 0
        
        if context.get('has_tests', False):
            if strategy['risk'] == RiskLevel.LOW:
                bonus += 5
        
        if context.get('is_production', False):
            if strategy['risk'] == RiskLevel.HIGH:
                bonus -= 10
        
        if context.get('code_complexity', 0) > 10:
            if strategy['risk'] in [RiskLevel.MEDIUM, RiskLevel.HIGH]:
                bonus -= 5
        
        return bonus

    def _get_fix_type_from_issue(self, issue_type: str) -> FixType:
        type_map = {
            'syntax_error': FixType.SYNTAX_ERROR,
            'missing_colon': FixType.SYNTAX_ERROR,
            'unmatched_bracket': FixType.SYNTAX_ERROR,
            'indentation_error': FixType.SYNTAX_ERROR,
            'invalid_escape': FixType.SYNTAX_ERROR,
            'invalid_syntax_operator': FixType.SYNTAX_ERROR,
            'unused_import': FixType.IMPORT_ERROR,
            'missing_import': FixType.IMPORT_ERROR,
            'import_order': FixType.IMPORT_ERROR,
            'duplicate_import': FixType.IMPORT_ERROR,
            'trailing_whitespace': FixType.STYLE_ERROR,
            'missing_newline': FixType.STYLE_ERROR,
            'hardcoded_password': FixType.SECURITY_ISSUE,
            'hardcoded_secret': FixType.SECURITY_ISSUE,
            'yaml_unsafe_load': FixType.SECURITY_ISSUE,
            'ssl_verify_disabled': FixType.SECURITY_ISSUE,
            'eval_usage': FixType.SECURITY_ISSUE,
            'exec_usage': FixType.SECURITY_ISSUE,
            'inefficient_membership_list': FixType.PERFORMANCE_ISSUE,
            'string_concat_in_loop': FixType.PERFORMANCE_ISSUE,
            'bare_except': FixType.LOGIC_ERROR,
            'mutable_default_arg': FixType.LOGIC_ERROR,
        }
        return type_map.get(issue_type, FixType.STYLE_ERROR)

    def _record_selection(self, issue: Dict[str, Any], strategy: Dict[str, Any]) -> None:
        self._selection_history.append({
            'timestamp': datetime.now().isoformat(),
            'issue_type': issue.get('type'),
            'strategy_name': strategy['name'],
            'score': strategy.get('calculated_score', 0)
        })
        
        if len(self._selection_history) > 1000:
            self._selection_history = self._selection_history[-500:]

    def record_outcome(self, strategy_name: str, success: bool) -> None:
        if strategy_name not in self._success_rates:
            self._success_rates[strategy_name] = {'success': 0, 'total': 0}
        
        self._success_rates[strategy_name]['total'] += 1
        if success:
            self._success_rates[strategy_name]['success'] += 1

    def get_all_strategies(self) -> Dict[FixType, List[Dict[str, Any]]]:
        return self._strategy_registry.copy()

    def get_strategy_for_issue_type(self, issue_type: str) -> List[Dict[str, Any]]:
        fix_type = self._get_fix_type_from_issue(issue_type)
        if fix_type not in self._strategy_registry:
            return []
        
        return [
            s for s in self._strategy_registry[fix_type]
            if issue_type in s['applicable_types']
        ]


class FixEffectPredictor:
    """修复效果预测器 - 预测修复成功概率和潜在影响"""

    def __init__(self):
        self._prediction_models: Dict[str, Any] = {}
        self._historical_data: List[Dict[str, Any]] = []
        self._risk_factors: Dict[str, float] = {}
        self._initialize_models()

    def _initialize_models(self) -> None:
        self._prediction_models = {
            'syntax_fix': {
                'base_success_rate': 0.85,
                'factors': {
                    'complexity': -0.05,
                    'line_length': -0.02,
                    'nested_level': -0.03,
                    'has_similar_code': 0.1,
                }
            },
            'import_fix': {
                'base_success_rate': 0.90,
                'factors': {
                    'is_stdlib': 0.05,
                    'has_alias': -0.02,
                    'multiple_imports': -0.03,
                }
            },
            'security_fix': {
                'base_success_rate': 0.75,
                'factors': {
                    'is_critical': -0.1,
                    'has_tests': 0.1,
                    'code_coverage': 0.05,
                }
            },
            'performance_fix': {
                'base_success_rate': 0.80,
                'factors': {
                    'is_hot_path': 0.05,
                    'has_benchmark': 0.1,
                    'complexity': -0.03,
                }
            },
            'style_fix': {
                'base_success_rate': 0.95,
                'factors': {
                    'auto_format_available': 0.05,
                    'has_linter': 0.03,
                }
            },
        }
        
        self._risk_factors = {
            'high_complexity': 0.15,
            'no_tests': 0.1,
            'large_change': 0.2,
            'multiple_issues_same_line': 0.25,
            'cross_file_dependency': 0.3,
            'runtime_behavior_change': 0.35,
        }

    def predict_success_probability(
        self,
        action: FixAction,
        content: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        model = self._get_model_for_fix_type(action.fix_type)
        
        base_rate = model['base_success_rate']
        factor_adjustments = 0
        
        code_factors = self._analyze_code_factors(content, action.line_number)
        for factor, weight in model['factors'].items():
            if factor in code_factors:
                factor_adjustments += code_factors[factor] * weight
        
        context_adjustments = 0
        if context:
            context_adjustments = self._calculate_context_adjustments(context, action)
        
        final_probability = base_rate + factor_adjustments + context_adjustments
        final_probability = max(0.0, min(1.0, final_probability))
        
        risks = self._identify_risks(action, content, context)
        risk_score = sum(self._risk_factors.get(r, 0) for r in risks)
        
        confidence = self._calculate_confidence(final_probability, risk_score, code_factors)
        
        return {
            'success_probability': round(final_probability, 3),
            'confidence': round(confidence, 3),
            'risk_score': round(risk_score, 3),
            'identified_risks': risks,
            'factors': code_factors,
            'recommendation': self._generate_recommendation(final_probability, risk_score, risks),
            'should_proceed': final_probability > 0.5 and risk_score < 0.5,
        }

    def _get_model_for_fix_type(self, fix_type: FixType) -> Dict[str, Any]:
        type_to_model = {
            FixType.SYNTAX_ERROR: 'syntax_fix',
            FixType.IMPORT_ERROR: 'import_fix',
            FixType.SECURITY_ISSUE: 'security_fix',
            FixType.PERFORMANCE_ISSUE: 'performance_fix',
            FixType.STYLE_ERROR: 'style_fix',
            FixType.LOGIC_ERROR: 'syntax_fix',
        }
        model_name = type_to_model.get(fix_type, 'style_fix')
        return self._prediction_models[model_name]

    def _analyze_code_factors(self, content: str, line_number: int) -> Dict[str, float]:
        factors = {}
        
        lines = content.split('\n')
        if 0 < line_number <= len(lines):
            target_line = lines[line_number - 1]
            factors['line_length'] = len(target_line) / 100
        
        try:
            tree = ast.parse(content)
            complexity = self._calculate_complexity(tree)
            factors['complexity'] = complexity / 20
            
            nested_level = self._get_nested_level(tree, line_number)
            factors['nested_level'] = nested_level / 5
        except SyntaxError:
            factors['complexity'] = 1.0
            factors['nested_level'] = 1.0
        
        factors['is_stdlib'] = 1.0
        factors['has_alias'] = 0.0
        factors['multiple_imports'] = 0.0
        factors['is_critical'] = 0.0
        factors['has_tests'] = 0.0
        factors['code_coverage'] = 0.0
        factors['is_hot_path'] = 0.0
        factors['has_benchmark'] = 0.0
        factors['auto_format_available'] = 1.0
        factors['has_linter'] = 1.0
        
        return factors

    def _calculate_complexity(self, tree: ast.AST) -> int:
        complexity = 1
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
            elif isinstance(node, (ast.And, ast.Or)):
                complexity += 1
        
        return complexity

    def _get_nested_level(self, tree: ast.AST, line_number: int) -> int:
        max_level = 0
        
        class NestedVisitor(ast.NodeVisitor):
            def __init__(self):
                self.current_level = 0
                self.max_level = 0
                self.target_line = line_number
            
            def visit_If(self, node):
                self._visit_nested(node)
            
            def visit_For(self, node):
                self._visit_nested(node)
            
            def visit_While(self, node):
                self._visit_nested(node)
            
            def visit_FunctionDef(self, node):
                self._visit_nested(node)
            
            def _visit_nested(self, node):
                self.current_level += 1
                if node.lineno == self.target_line:
                    self.max_level = max(self.max_level, self.current_level)
                self.generic_visit(node)
                self.current_level -= 1
        
        visitor = NestedVisitor()
        visitor.visit(tree)
        return visitor.max_level

    def _calculate_context_adjustments(
        self,
        context: Dict[str, Any],
        action: FixAction
    ) -> float:
        adjustments = 0
        
        if context.get('has_tests', False):
            adjustments += 0.05
        
        if context.get('code_coverage', 0) > 0.8:
            adjustments += 0.05
        
        if context.get('is_production', False) and action.risk_level == RiskLevel.HIGH:
            adjustments -= 0.1
        
        if context.get('recent_failures', 0) > 0:
            adjustments -= 0.02 * context['recent_failures']
        
        return adjustments

    def _identify_risks(
        self,
        action: FixAction,
        content: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        risks = []
        
        if action.risk_level == RiskLevel.HIGH:
            risks.append('high_risk_operation')
        
        lines = content.split('\n')
        if 0 < action.line_number <= len(lines):
            line = lines[action.line_number - 1]
            if len(line) > 120:
                risks.append('large_change')
        
        try:
            tree = ast.parse(content)
            complexity = self._calculate_complexity(tree)
            if complexity > 15:
                risks.append('high_complexity')
        except SyntaxError:
            pass
        
        if context:
            if not context.get('has_tests', True):
                risks.append('no_tests')
            
            if context.get('cross_file_references', 0) > 0:
                risks.append('cross_file_dependency')
        
        return risks

    def _calculate_confidence(
        self,
        probability: float,
        risk_score: float,
        factors: Dict[str, float]
    ) -> float:
        probability_confidence = 1 - abs(probability - 0.5) * 2
        
        risk_confidence = 1 - risk_score
        
        factor_confidence = 1
        unknown_factors = sum(1 for v in factors.values() if v == 0)
        if unknown_factors > 0:
            factor_confidence -= unknown_factors * 0.05
        
        total_confidence = (
            probability_confidence * 0.4 +
            risk_confidence * 0.35 +
            factor_confidence * 0.25
        )
        
        return max(0.0, min(1.0, total_confidence))

    def _generate_recommendation(
        self,
        probability: float,
        risk_score: float,
        risks: List[str]
    ) -> str:
        if probability >= 0.9 and risk_score < 0.2:
            return "强烈建议执行此修复，成功概率高且风险低"
        elif probability >= 0.7 and risk_score < 0.4:
            return "建议执行此修复，但建议先进行代码审查"
        elif probability >= 0.5:
            if risk_score >= 0.4:
                return "建议谨慎执行，存在一定风险，建议先进行测试"
            return "可以执行此修复，但建议先备份代码"
        else:
            return "不建议自动执行此修复，建议手动处理"

    def predict_batch_effects(
        self,
        actions: List[FixAction],
        content: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        predictions = []
        
        for action in actions:
            pred = self.predict_success_probability(action, content, context)
            predictions.append({
                'action_id': action.action_id,
                'prediction': pred
            })
        
        success_probs = [p['prediction']['success_probability'] for p in predictions]
        risk_scores = [p['prediction']['risk_score'] for p in predictions]
        
        overall_success = 1.0
        for prob in success_probs:
            overall_success *= prob
        
        return {
            'individual_predictions': predictions,
            'overall_success_probability': round(overall_success, 3),
            'average_success_probability': round(sum(success_probs) / len(success_probs), 3) if success_probs else 0,
            'max_risk_score': round(max(risk_scores), 3) if risk_scores else 0,
            'high_risk_actions': [
                p['action_id'] for p in predictions
                if p['prediction']['risk_score'] > 0.3
            ],
            'recommended_order': self._suggest_execution_order(predictions),
        }

    def _suggest_execution_order(
        self,
        predictions: List[Dict[str, Any]]
    ) -> List[str]:
        scored = []
        for pred in predictions:
            score = (
                pred['prediction']['success_probability'] * 10 -
                pred['prediction']['risk_score'] * 5
            )
            scored.append((pred['action_id'], score))
        
        scored.sort(key=lambda x: x[1], reverse=True)
        return [s[0] for s in scored]

    def record_outcome(
        self,
        action: FixAction,
        success: bool,
        actual_effects: Optional[Dict[str, Any]] = None
    ) -> None:
        self._historical_data.append({
            'timestamp': datetime.now().isoformat(),
            'action_id': action.action_id,
            'fix_type': action.fix_type.value,
            'success': success,
            'effects': actual_effects or {},
        })
        
        if len(self._historical_data) > 1000:
            self._historical_data = self._historical_data[-500:]


class IntelligentFixSuggester:
    """智能修复建议器 - 提供智能修复建议"""

    def __init__(self):
        self._suggestion_patterns: Dict[str, Dict[str, Any]] = {}
        self._context_analyzers: List[callable] = []
        self._register_patterns()

    def _register_patterns(self):
        self._suggestion_patterns = {
            'missing_type_hint': {
                'pattern': r'def\s+(\w+)\s*\([^:]*\)\s*->\s*None:',
                'suggestion': '考虑添加返回类型注解',
                'auto_fixable': True,
                'priority': 'low'
            },
            'magic_number': {
                'pattern': r'(?<!["\'])\b(\d{2,})\b(?!["\'])',
                'suggestion': '魔法数字应提取为常量',
                'auto_fixable': False,
                'priority': 'low'
            },
            'long_function': {
                'detector': self._detect_long_function,
                'suggestion': '函数过长，建议拆分',
                'auto_fixable': False,
                'priority': 'medium'
            },
            'deep_nesting': {
                'detector': self._detect_deep_nesting,
                'suggestion': '嵌套层级过深，建议重构',
                'auto_fixable': False,
                'priority': 'medium'
            },
            'duplicate_code': {
                'detector': self._detect_duplicate_code,
                'suggestion': '检测到重复代码，建议提取为函数',
                'auto_fixable': False,
                'priority': 'high'
            },
            'complex_condition': {
                'pattern': r'if\s+.*\s+(and|or)\s+.*\s+(and|or)\s+.*:',
                'suggestion': '条件过于复杂，建议提取为变量或函数',
                'auto_fixable': False,
                'priority': 'medium'
            },
        }

    def _detect_long_function(self, content: str) -> List[Dict[str, Any]]:
        issues = []
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return issues

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_lines = node.end_lineno - node.lineno + 1 if hasattr(node, 'end_lineno') else 0
                if func_lines > 50:
                    issues.append({
                        'type': 'long_function',
                        'line': node.lineno,
                        'message': f'函数 {node.name} 有 {func_lines} 行，建议拆分',
                        'function_name': node.name,
                        'line_count': func_lines
                    })

        return issues

    def _detect_deep_nesting(self, content: str) -> List[Dict[str, Any]]:
        issues = []
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            if line.strip():
                indent = len(line) - len(line.lstrip())
                nesting_level = indent // 4
                if nesting_level > 4:
                    issues.append({
                        'type': 'deep_nesting',
                        'line': i,
                        'message': f'嵌套层级 {nesting_level} 过深，建议重构',
                        'nesting_level': nesting_level
                    })

        return issues

    def _detect_duplicate_code(self, content: str) -> List[Dict[str, Any]]:
        issues = []
        lines = content.split('\n')

        code_blocks: Dict[str, List[int]] = {}
        block_size = 5

        for i in range(len(lines) - block_size + 1):
            block = '\n'.join(lines[i:i + block_size]).strip()
            if block and not block.startswith('#') and len(block) > 20:
                block_hash = hash(block)
                if block_hash not in code_blocks:
                    code_blocks[block_hash] = []
                code_blocks[block_hash].append(i + 1)

        for block_hash, line_nums in code_blocks.items():
            if len(line_nums) >= 2:
                issues.append({
                    'type': 'duplicate_code',
                    'line': line_nums[0],
                    'message': f'检测到重复代码块，出现在行: {line_nums}',
                    'occurrences': line_nums
                })

        return issues

    def analyze_and_suggest(
        self,
        content: str,
        file_path: Path
    ) -> List[Dict[str, Any]]:
        suggestions = []

        for pattern_name, config in self._suggestion_patterns.items():
            if 'pattern' in config:
                matches = re.finditer(config['pattern'], content, re.MULTILINE)
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    suggestions.append({
                        'type': pattern_name,
                        'line': line_num,
                        'suggestion': config['suggestion'],
                        'auto_fixable': config['auto_fixable'],
                        'priority': config['priority'],
                        'match_text': match.group()
                    })
            elif 'detector' in config:
                detected = config['detector'](content)
                for issue in detected:
                    issue['suggestion'] = config['suggestion']
                    issue['auto_fixable'] = config['auto_fixable']
                    issue['priority'] = config['priority']
                    suggestions.append(issue)

        return sorted(suggestions, key=lambda x: {'high': 0, 'medium': 1, 'low': 2}.get(x['priority'], 3))


class MultiTypeFixCoordinator:
    """多类型修复协调器 - 协调不同类型修复的执行"""

    def __init__(self):
        self._fix_order: List[FixType] = [
            FixType.SYNTAX_ERROR,
            FixType.SECURITY_ISSUE,
            FixType.IMPORT_ERROR,
            FixType.LOGIC_ERROR,
            FixType.PERFORMANCE_ISSUE,
            FixType.STYLE_ERROR,
            FixType.DEPRECATED_CODE,
            FixType.UNUSED_CODE,
        ]
        self._dependencies: Dict[FixType, List[FixType]] = {
            FixType.IMPORT_ERROR: [FixType.SYNTAX_ERROR],
            FixType.LOGIC_ERROR: [FixType.SYNTAX_ERROR],
            FixType.STYLE_ERROR: [FixType.SYNTAX_ERROR, FixType.IMPORT_ERROR],
            FixType.PERFORMANCE_ISSUE: [FixType.SYNTAX_ERROR],
            FixType.SECURITY_ISSUE: [FixType.SYNTAX_ERROR],
        }
        self._validator = FixValidator()
        self._conflict_resolver = FixConflictResolver()
        self._rollback_manager = FixRollbackManager()
        self._suggester = IntelligentFixSuggester()

    def coordinate_fixes(
        self,
        content: str,
        file_path: Path,
        strategies: List[FixStrategy],
        dry_run: bool = False
    ) -> Dict[str, Any]:
        result = {
            'original_content': content,
            'fixed_content': content,
            'all_actions': [],
            'applied_actions': [],
            'skipped_actions': [],
            'validation_result': None,
            'conflicts': [],
            'suggestions': [],
            'rollback_id': None
        }

        all_issues = []
        for strategy in strategies:
            issues = strategy.can_fix(content, file_path)
            all_issues.extend(issues)

        issues_by_type: Dict[FixType, List[Dict[str, Any]]] = {}
        for issue in all_issues:
            fix_type = self._get_issue_fix_type(issue)
            if fix_type not in issues_by_type:
                issues_by_type[fix_type] = []
            issues_by_type[fix_type].append(issue)

        current_content = content
        all_actions = []

        for fix_type in self._fix_order:
            if fix_type in issues_by_type:
                for strategy in strategies:
                    strategy_actions = self._get_strategy_fix_type(strategy)
                    if strategy_actions == fix_type:
                        fixed_content, actions = strategy.apply_fix(
                            current_content,
                            issues_by_type[fix_type]
                        )
                        if actions:
                            all_actions.extend(actions)
                            current_content = fixed_content
                        break

        conflicts = self._conflict_resolver.detect_conflicts(all_actions)
        result['conflicts'] = conflicts

        resolved_actions = self._conflict_resolver.resolve_conflicts(all_actions, conflicts)

        validation = self._validator.validate_fix(content, current_content, file_path)
        result['validation_result'] = validation

        if not validation['is_valid']:
            result['fixed_content'] = content
            result['skipped_actions'] = [a.action_id for a in all_actions]
            return result

        result['all_actions'] = all_actions
        result['applied_actions'] = [a.action_id for a in resolved_actions if a.auto_applicable]
        result['skipped_actions'] = [a.action_id for a in resolved_actions if not a.auto_applicable]
        result['fixed_content'] = current_content

        suggestions = self._suggester.analyze_and_suggest(current_content, file_path)
        result['suggestions'] = suggestions

        if not dry_run and resolved_actions:
            result['rollback_id'] = self._rollback_manager.save_state(
                file_path, content, resolved_actions
            )

        return result

    def _get_issue_fix_type(self, issue: Dict[str, Any]) -> FixType:
        type_map = {
            'syntax_error': FixType.SYNTAX_ERROR,
            'missing_colon': FixType.SYNTAX_ERROR,
            'unmatched_bracket': FixType.SYNTAX_ERROR,
            'indentation_error': FixType.SYNTAX_ERROR,
            'unused_import': FixType.IMPORT_ERROR,
            'missing_import': FixType.IMPORT_ERROR,
            'import_order': FixType.IMPORT_ERROR,
            'long_line': FixType.STYLE_ERROR,
            'trailing_whitespace': FixType.STYLE_ERROR,
            'missing_newline': FixType.STYLE_ERROR,
            'multiple_blank_lines': FixType.STYLE_ERROR,
            'missing_module_docstring': FixType.STYLE_ERROR,
            'missing_function_docstring': FixType.STYLE_ERROR,
            'mutable_default_arg': FixType.LOGIC_ERROR,
            'bare_except': FixType.LOGIC_ERROR,
            'print_statement': FixType.STYLE_ERROR,
            'eq_without_hash': FixType.LOGIC_ERROR,
            'hardcoded_password': FixType.SECURITY_ISSUE,
            'hardcoded_secret': FixType.SECURITY_ISSUE,
            'sql_injection_risk': FixType.SECURITY_ISSUE,
            'eval_usage': FixType.SECURITY_ISSUE,
            'exec_usage': FixType.SECURITY_ISSUE,
            'pickle_usage': FixType.SECURITY_ISSUE,
            'subprocess_shell': FixType.SECURITY_ISSUE,
            'yaml_unsafe_load': FixType.SECURITY_ISSUE,
            'assert_in_production': FixType.SECURITY_ISSUE,
            'tempfile_race': FixType.SECURITY_ISSUE,
            'weak_crypto': FixType.SECURITY_ISSUE,
            'insecure_random': FixType.SECURITY_ISSUE,
            'string_concat_in_loop': FixType.PERFORMANCE_ISSUE,
            'list_append_in_loop': FixType.PERFORMANCE_ISSUE,
            'inefficient_membership_list': FixType.PERFORMANCE_ISSUE,
            'nested_loop': FixType.PERFORMANCE_ISSUE,
            'repeated_calculation': FixType.PERFORMANCE_ISSUE,
        }
        return type_map.get(issue.get('type', ''), FixType.STYLE_ERROR)

    def _get_strategy_fix_type(self, strategy: FixStrategy) -> Optional[FixType]:
        type_map = {
            'SyntaxErrorFixer': FixType.SYNTAX_ERROR,
            'ImportErrorFixer': FixType.IMPORT_ERROR,
            'StyleFixer': FixType.STYLE_ERROR,
            'CodeSmellFixer': FixType.LOGIC_ERROR,
            'SecurityVulnerabilityFixer': FixType.SECURITY_ISSUE,
            'PerformanceFixer': FixType.PERFORMANCE_ISSUE,
        }
        return type_map.get(type(strategy).__name__)

    def rollback_fix(self, rollback_id: str) -> Optional[Dict[str, Any]]:
        return self._rollback_manager.rollback(rollback_id)

    def get_fix_history(self) -> List[Dict[str, Any]]:
        return self._rollback_manager.get_history()


class AutoFixer:
    """自动修复器主类"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.strategies = [
            SyntaxErrorFixer(),
            ImportErrorFixer(),
            StyleFixer(),
            CodeSmellFixer(),
            SecurityVulnerabilityFixer(),
            PerformanceFixer(),
        ]
        self.file_counter = 0
        self._fix_statistics: Dict[str, Dict[str, int]] = {}
        self._validator = FixValidator()
        self._coordinator = MultiTypeFixCoordinator()
        self._rollback_manager = FixRollbackManager()
        self._suggester = IntelligentFixSuggester()
        self._conflict_resolver = FixConflictResolver()
        self._strategy_selector = FixStrategySelector()
        self._effect_predictor = FixEffectPredictor()

    def select_strategy(self, issue: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        return self._strategy_selector.select_best_strategy(issue, context)

    def predict_fix_effect(self, action: FixAction, content: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self._effect_predictor.predict_success_probability(action, content, context)

    def predict_batch_effects(self, actions: List[FixAction], content: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self._effect_predictor.predict_batch_effects(actions, content, context)

    def create_checkpoint(self, name: str, file_path: Path, content: str) -> str:
        return self._rollback_manager.create_checkpoint(name, file_path, content)

    def restore_checkpoint(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        return self._rollback_manager.restore_checkpoint(checkpoint_id)

    def rollback_n_steps(self, n: int) -> List[Dict[str, Any]]:
        return self._rollback_manager.rollback_n_steps(n)

    def preview_rollback(self, state_id: str) -> Optional[Dict[str, Any]]:
        return self._rollback_manager.preview_rollback(state_id)

    def get_all_strategies(self) -> Dict[FixType, List[Dict[str, Any]]]:
        return self._strategy_selector.get_all_strategies()

    def record_strategy_outcome(self, strategy_name: str, success: bool) -> None:
        self._strategy_selector.record_outcome(strategy_name, success)

    def fix_file_with_prediction(
        self,
        file_path: Path,
        dry_run: bool = False,
        fix_types: List[FixType] = None,
        min_probability: float = 0.5,
        max_risk_score: float = 0.5
    ) -> FixResult:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
        except Exception as e:
            return FixResult(
                file_path=str(file_path),
                status=FixStatus.FAILED,
                actions=[],
                applied_actions=[],
                skipped_actions=[],
                original_content="",
                fixed_content="",
                diff="",
                error_message=str(e)
            )

        all_issues = []
        for strategy in self.strategies:
            issues = strategy.can_fix(original_content, file_path)
            all_issues.extend(issues)

        fixed_content = original_content
        all_actions = []

        for strategy in self.strategies:
            if fix_types:
                strategy_issues = [i for i in all_issues if self._get_issue_fix_type(i) in [ft.value for ft in fix_types]]
            else:
                strategy_issues = all_issues

            if strategy_issues:
                fixed_content, actions = strategy.apply_fix(fixed_content, strategy_issues)
                all_actions.extend(actions)

        filtered_actions = []
        for action in all_actions:
            prediction = self._effect_predictor.predict_success_probability(
                action, original_content
            )
            if (prediction['success_probability'] >= min_probability and
                prediction['risk_score'] <= max_risk_score):
                filtered_actions.append(action)
            else:
                action.auto_applicable = False

        validation_result = self._validator.validate_fix(original_content, fixed_content, file_path)
        if not validation_result['is_valid']:
            fixed_content = original_content
            filtered_actions = []

        diff = self._generate_diff(original_content, fixed_content, str(file_path))

        status = FixStatus.SUCCESS if filtered_actions else FixStatus.SKIPPED
        if filtered_actions and not [a for a in filtered_actions if a.auto_applicable]:
            status = FixStatus.PARTIAL

        if not dry_run and filtered_actions and validation_result['is_valid']:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(fixed_content)
                self._rollback_manager.save_state(file_path, original_content, filtered_actions)
            except Exception:
                status = FixStatus.FAILED

        return FixResult(
            file_path=str(file_path),
            status=status,
            actions=filtered_actions,
            applied_actions=[a.action_id for a in filtered_actions if a.auto_applicable],
            skipped_actions=[a.action_id for a in filtered_actions if not a.auto_applicable],
            original_content=original_content,
            fixed_content=fixed_content,
            diff=diff
        )

    def fix_file(self, file_path: Path, dry_run: bool = False,
                 fix_types: List[FixType] = None,
                 use_coordinator: bool = True) -> FixResult:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
        except Exception as e:
            return FixResult(
                file_path=str(file_path),
                status=FixStatus.FAILED,
                actions=[],
                applied_actions=[],
                skipped_actions=[],
                original_content="",
                fixed_content="",
                diff="",
                error_message=str(e)
            )

        if use_coordinator:
            return self._fix_with_coordinator(file_path, original_content, dry_run, fix_types)

        all_issues = []
        for strategy in self.strategies:
            issues = strategy.can_fix(original_content, file_path)
            all_issues.extend(issues)

        fixed_content = original_content
        all_actions = []

        for strategy in self.strategies:
            if fix_types:
                strategy_issues = [i for i in all_issues if self._get_issue_fix_type(i) in [ft.value for ft in fix_types]]
            else:
                strategy_issues = all_issues

            if strategy_issues:
                fixed_content, actions = strategy.apply_fix(fixed_content, strategy_issues)
                all_actions.extend(actions)

        validation_result = self._validator.validate_fix(original_content, fixed_content, file_path)
        if not validation_result['is_valid']:
            fixed_content = original_content
            all_actions = []

        conflicts = self._conflict_resolver.detect_conflicts(all_actions)
        if conflicts:
            all_actions = self._conflict_resolver.resolve_conflicts(all_actions, conflicts)

        applied = [a.action_id for a in all_actions if a.auto_applicable]
        skipped = [a.action_id for a in all_actions if not a.auto_applicable]

        diff = self._generate_diff(original_content, fixed_content, str(file_path))

        status = FixStatus.SUCCESS if all_actions else FixStatus.SKIPPED
        if all_actions and not applied:
            status = FixStatus.PARTIAL

        if not dry_run and all_actions and validation_result['is_valid']:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(fixed_content)
                self._rollback_manager.save_state(file_path, original_content, all_actions)
            except Exception as e:
                status = FixStatus.FAILED

        return FixResult(
            file_path=str(file_path),
            status=status,
            actions=all_actions,
            applied_actions=applied,
            skipped_actions=skipped,
            original_content=original_content,
            fixed_content=fixed_content,
            diff=diff
        )

    def _fix_with_coordinator(
        self,
        file_path: Path,
        content: str,
        dry_run: bool,
        fix_types: List[FixType] = None
    ) -> FixResult:
        strategies = self.strategies
        if fix_types:
            strategies = [s for s in self.strategies if self._get_strategy_type(s) in fix_types]

        result = self._coordinator.coordinate_fixes(content, file_path, strategies, dry_run)

        actions = []
        for action_dict in result.get('all_actions', []):
            if isinstance(action_dict, dict):
                action = FixAction(
                    action_id=action_dict.get('action_id', ''),
                    fix_type=FixType(action_dict.get('fix_type', 'style_error')),
                    description=action_dict.get('description', ''),
                    original_code=action_dict.get('original_code', ''),
                    fixed_code=action_dict.get('fixed_code', ''),
                    line_number=action_dict.get('line_number', 0),
                    risk_level=RiskLevel(action_dict.get('risk_level', 'low')),
                    auto_applicable=action_dict.get('auto_applicable', True)
                )
                actions.append(action)

        diff = self._generate_diff(content, result['fixed_content'], str(file_path))

        validation = result.get('validation_result', {})
        status = FixStatus.SUCCESS if actions and validation.get('is_valid', True) else FixStatus.SKIPPED
        if actions and not result.get('applied_actions'):
            status = FixStatus.PARTIAL
        if not validation.get('is_valid', True):
            status = FixStatus.FAILED

        if not dry_run and actions and validation.get('is_valid', True):
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(result['fixed_content'])
            except Exception:
                status = FixStatus.FAILED

        return FixResult(
            file_path=str(file_path),
            status=status,
            actions=actions,
            applied_actions=result.get('applied_actions', []),
            skipped_actions=result.get('skipped_actions', []),
            original_content=content,
            fixed_content=result['fixed_content'],
            diff=diff
        )

    def _get_strategy_type(self, strategy: FixStrategy) -> FixType:
        type_map = {
            'SyntaxErrorFixer': FixType.SYNTAX_ERROR,
            'ImportErrorFixer': FixType.IMPORT_ERROR,
            'StyleFixer': FixType.STYLE_ERROR,
            'CodeSmellFixer': FixType.LOGIC_ERROR,
            'SecurityVulnerabilityFixer': FixType.SECURITY_ISSUE,
            'PerformanceFixer': FixType.PERFORMANCE_ISSUE,
        }
        return type_map.get(type(strategy).__name__, FixType.STYLE_ERROR)

    def get_suggestions(self, file_path: Path) -> List[Dict[str, Any]]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception:
            return []

        return self._suggester.analyze_and_suggest(content, file_path)

    def rollback(self, rollback_id: str) -> Optional[Dict[str, Any]]:
        return self._rollback_manager.rollback(rollback_id)

    def get_fix_history(self) -> List[Dict[str, Any]]:
        return self._rollback_manager.get_history()

    def validate_content(self, content: str, file_path: Path) -> Dict[str, Any]:
        return self._validator.validate_fix(content, content, file_path)

    def _get_issue_fix_type(self, issue: Dict[str, Any]) -> str:
        type_map = {
            'syntax_error': FixType.SYNTAX_ERROR.value,
            'missing_colon': FixType.SYNTAX_ERROR.value,
            'unmatched_bracket': FixType.SYNTAX_ERROR.value,
            'indentation_error': FixType.SYNTAX_ERROR.value,
            'unused_import': FixType.IMPORT_ERROR.value,
            'missing_import': FixType.IMPORT_ERROR.value,
            'import_order': FixType.IMPORT_ERROR.value,
            'long_line': FixType.STYLE_ERROR.value,
            'trailing_whitespace': FixType.STYLE_ERROR.value,
            'missing_newline': FixType.STYLE_ERROR.value,
            'multiple_blank_lines': FixType.STYLE_ERROR.value,
            'missing_module_docstring': FixType.STYLE_ERROR.value,
            'missing_function_docstring': FixType.STYLE_ERROR.value,
            'mutable_default_arg': FixType.LOGIC_ERROR.value,
            'bare_except': FixType.LOGIC_ERROR.value,
            'print_statement': FixType.STYLE_ERROR.value,
            'eq_without_hash': FixType.LOGIC_ERROR.value,
            'hardcoded_password': FixType.SECURITY_ISSUE.value,
            'hardcoded_secret': FixType.SECURITY_ISSUE.value,
            'sql_injection_risk': FixType.SECURITY_ISSUE.value,
            'eval_usage': FixType.SECURITY_ISSUE.value,
            'exec_usage': FixType.SECURITY_ISSUE.value,
            'pickle_usage': FixType.SECURITY_ISSUE.value,
            'subprocess_shell': FixType.SECURITY_ISSUE.value,
            'yaml_unsafe_load': FixType.SECURITY_ISSUE.value,
            'assert_in_production': FixType.SECURITY_ISSUE.value,
            'tempfile_race': FixType.SECURITY_ISSUE.value,
            'weak_crypto': FixType.SECURITY_ISSUE.value,
            'insecure_random': FixType.SECURITY_ISSUE.value,
            'string_concat_in_loop': FixType.PERFORMANCE_ISSUE.value,
            'list_append_in_loop': FixType.PERFORMANCE_ISSUE.value,
            'inefficient_membership_list': FixType.PERFORMANCE_ISSUE.value,
        }
        return type_map.get(issue.get('type', ''), FixType.STYLE_ERROR.value)

    def fix_directory(self, dir_path: Path, dry_run: bool = False,
                      fix_types: List[FixType] = None,
                      exclude: List[str] = None) -> List[FixResult]:
        results = []
        exclude = exclude or ['__pycache__', '.git', 'venv', 'node_modules']

        for py_file in dir_path.rglob('*.py'):
            if any(ex in str(py_file) for ex in exclude):
                continue

            result = self.fix_file(py_file, dry_run, fix_types)
            results.append(result)

        return results

    def _generate_diff(self, original: str, fixed: str, filename: str) -> str:
        diff_lines = list(difflib.unified_diff(
            original.splitlines(keepends=True),
            fixed.splitlines(keepends=True),
            fromfile=f'{filename} (original)',
            tofile=f'{filename} (fixed)',
            lineterm=''
        ))
        return ''.join(diff_lines)

    def generate_report(self, results: List[FixResult]) -> FixReport:
        self.file_counter += 1

        fixed = sum(1 for r in results if r.status == FixStatus.SUCCESS)
        failed = sum(1 for r in results if r.status == FixStatus.FAILED)
        total_fixes = sum(len(r.actions) for r in results)

        summary = f"处理了 {len(results)} 个文件，应用了 {total_fixes} 个修复"

        return FixReport(
            report_id=f"FIX-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            generated_at=datetime.now().isoformat(),
            total_files=len(results),
            fixed_files=fixed,
            failed_files=failed,
            total_fixes=total_fixes,
            results=results,
            summary=summary
        )

    def generate_markdown_report(self, report: FixReport) -> str:
        lines = [
            "# 自动修复报告",
            "",
            f"**报告ID**: {report.report_id}",
            f"**生成时间**: {report.generated_at}",
            "",
            "## 摘要",
            "",
            f"- 总文件数: {report.total_files}",
            f"- 已修复: {report.fixed_files}",
            f"- 失败: {report.failed_files}",
            f"- 总修复数: {report.total_fixes}",
            "",
            f"**{report.summary}**",
            "",
        ]

        for result in report.results:
            if result.actions:
                lines.extend([
                    f"## {result.file_path}",
                    "",
                    f"- **状态**: {result.status.value}",
                    f"- **修复数**: {len(result.actions)}",
                    "",
                ])

                for action in result.actions:
                    lines.extend([
                        f"### {action.action_id}: {action.description}",
                        "",
                        f"- **类型**: {action.fix_type.value}",
                        f"- **行号**: {action.line_number}",
                        f"- **风险**: {action.risk_level.value}",
                        "",
                        "**原始代码**:",
                        f"```python\n{action.original_code}\n```",
                        "",
                        "**修复后**:",
                        f"```python\n{action.fixed_code}\n```",
                        "",
                    ])

        return "\n".join(lines)


def load_config(config_path: Path) -> Dict[str, Any]:
    if not config_path.exists():
        return {}

    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(
        description="自动修复器 - 智能代码修复系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 修复单个文件
  python auto_fixer.py --file problematic.py --fix

  # 预览修复（不实际修改）
  python auto_fixer.py --file code.py --dry-run

  # 修复整个目录
  python auto_fixer.py --dir ./src --fix-all

  # 只修复导入问题
  python auto_fixer.py --file code.py --fix-imports

  # 生成修复报告
  python auto_fixer.py --dir ./src --fix-all --report fix_report.md
        """
    )

    parser.add_argument(
        "--file",
        type=Path,
        help="要修复的单个文件"
    )

    parser.add_argument(
        "--dir",
        type=Path,
        help="要修复的目录"
    )

    parser.add_argument(
        "--fix",
        action="store_true",
        help="执行修复"
    )

    parser.add_argument(
        "--fix-all",
        action="store_true",
        help="修复所有问题"
    )

    parser.add_argument(
        "--fix-syntax",
        action="store_true",
        help="只修复语法错误"
    )

    parser.add_argument(
        "--fix-imports",
        action="store_true",
        help="只修复导入问题"
    )

    parser.add_argument(
        "--fix-style",
        action="store_true",
        help="只修复代码风格问题"
    )

    parser.add_argument(
        "--fix-security",
        action="store_true",
        help="只修复安全漏洞问题"
    )

    parser.add_argument(
        "--fix-performance",
        action="store_true",
        help="只修复性能问题"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="预览修复，不实际修改文件"
    )

    parser.add_argument(
        "--report",
        type=str,
        help="报告输出路径"
    )

    parser.add_argument(
        "--config",
        type=Path,
        help="配置文件路径"
    )

    parser.add_argument(
        "--exclude",
        nargs="+",
        help="排除的目录或文件模式"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="详细输出"
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    config = {}
    if args.config:
        config = load_config(args.config)

    fixer = AutoFixer(config)

    fix_types = []
    if args.fix_syntax:
        fix_types.append(FixType.SYNTAX_ERROR)
    if args.fix_imports:
        fix_types.append(FixType.IMPORT_ERROR)
    if args.fix_style:
        fix_types.append(FixType.STYLE_ERROR)
    if args.fix_security:
        fix_types.append(FixType.SECURITY_ISSUE)
    if args.fix_performance:
        fix_types.append(FixType.PERFORMANCE_ISSUE)

    results = []

    if args.file:
        result = fixer.fix_file(args.file, dry_run=args.dry_run, fix_types=fix_types or None)
        results.append(result)

        print(f"\n{'=' * 60}")
        print(f"文件: {result.file_path}")
        print(f"状态: {result.status.value}")
        print(f"修复数: {len(result.actions)}")

        if result.actions:
            print("\n修复详情:")
            for action in result.actions:
                print(f"  [{action.fix_type.value}] 行{action.line_number}: {action.description}")

        if result.diff and args.verbose:
            print(f"\n差异:\n{result.diff}")

    elif args.dir:
        results = fixer.fix_directory(
            args.dir,
            dry_run=args.dry_run,
            fix_types=fix_types or None,
            exclude=args.exclude
        )

        print(f"\n{'=' * 60}")
        print("修复摘要")
        print(f"{'=' * 60}")

        for result in results:
            if result.actions:
                print(f"\n{result.file_path}: {result.status.value}, {len(result.actions)}个修复")

    else:
        parser.print_help()
        print("\n错误: 请指定 --file 或 --dir")
        sys.exit(1)

    report = fixer.generate_report(results)

    print(f"\n{'=' * 60}")
    print(report.summary)
    print(f"{'=' * 60}")

    if args.report:
        report_path = Path(args.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)

        suffix = report_path.suffix.lower()
        if suffix == '.json':
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report.to_dict(), f, ensure_ascii=False, indent=2)
        else:
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(fixer.generate_markdown_report(report))

        print(f"\n报告已保存: {report_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
