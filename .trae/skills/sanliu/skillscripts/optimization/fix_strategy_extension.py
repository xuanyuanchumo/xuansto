#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版修复策略库扩展 - Fix Strategy Library Extension

扩展修复策略，包括：
- 导入修复策略（Import Fix Strategies）
- 类型注解修复策略（Type Annotation Fix Strategies）
- 未使用代码修复策略（Unused Code Fix Strategies）
- 代码简化策略（Code Simplification Strategies）

使用示例:
    python fix_strategy_extension.py --list-strategies
    python fix_strategy_extension.py --file problematic.py --fix
"""

from __future__ import annotations

import ast
import json
import logging
import re
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FixCategory(Enum):
    IMPORT_FIX = auto()
    TYPE_FIX = auto()
    UNUSED_CODE_FIX = auto()
    CODE_SIMPLIFICATION = auto()
    STYLE_FIX = auto()


class FixPriority(Enum):
    CRITICAL = 0
    HIGH = 1
    MEDIUM = 2
    LOW = 3


class FixStatus(Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    SKIPPED = "skipped"
    NEEDS_MANUAL_REVIEW = "needs_manual_review"


@dataclass
class FixContext:
    file_path: str
    line_number: int
    original_code: str
    problem_type: str
    problem_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FixResult:
    result_id: str
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

    def to_dict(self) -> Dict[str, Any]:
        return {
            "result_id": self.result_id,
            "strategy_name": self.strategy_name,
            "status": self.status.value,
            "original_code": self.original_code,
            "fixed_code": self.fixed_code,
            "line_number": self.line_number,
            "confidence": self.confidence,
            "execution_time_ms": self.execution_time_ms,
            "message": self.message,
            "warnings": self.warnings,
            "additional_changes": self.additional_changes
        }


class BaseFixStrategy:
    """修复策略基类"""

    name: str = "base_strategy"
    description: str = "基础修复策略"
    category: FixCategory = FixCategory.STYLE_FIX
    priority: FixPriority = FixPriority.MEDIUM
    applicable_problems: List[str] = []

    def __init__(self):
        self._result_counter = 0

    def can_fix(self, problem_type: str) -> bool:
        return problem_type in self.applicable_problems

    def apply(self, context: FixContext) -> FixResult:
        start_time = time.perf_counter()
        self._result_counter += 1

        try:
            status, fixed_code, confidence, message, warnings = self._do_fix(context)
        except Exception as e:
            status = FixStatus.FAILED
            fixed_code = context.original_code
            confidence = 0.0
            message = f"策略执行异常: {str(e)}"
            warnings = [str(e)]
            logger.error(f"策略 {self.name} 执行失败: {e}")

        execution_time_ms = (time.perf_counter() - start_time) * 1000

        return FixResult(
            result_id=f"{self.name}_{self._result_counter:04d}",
            strategy_name=self.name,
            status=status,
            original_code=context.original_code,
            fixed_code=fixed_code,
            line_number=context.line_number,
            confidence=confidence,
            execution_time_ms=execution_time_ms,
            message=message,
            warnings=warnings
        )

    def _do_fix(self, context: FixContext) -> Tuple[FixStatus, str, float, str, List[str]]:
        raise NotImplementedError


class AddMissingImportStrategy(BaseFixStrategy):
    """添加缺失导入策略"""

    name = "add_missing_import"
    description = "自动添加缺失的导入语句"
    category = FixCategory.IMPORT_FIX
    priority = FixPriority.HIGH
    applicable_problems = ["missing_import"]

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
        'ast': 'import ast',
        'tokenize': 'import tokenize',
    }

    def _do_fix(self, context: FixContext) -> Tuple[FixStatus, str, float, str, List[str]]:
        original_code = context.original_code
        warnings = []

        missing_name = context.problem_data.get("missing_name", "")
        if not missing_name:
            return FixStatus.FAILED, original_code, 0.0, "无法确定缺失的导入名称", warnings

        import_statement = self.COMMON_IMPORTS.get(missing_name)

        if not import_statement:
            import_statement = f"import {missing_name}"
            warnings.append(f"未找到 '{missing_name}' 的标准导入路径，使用默认导入")
            confidence = 0.6
        else:
            confidence = 0.95

        lines = original_code.split('\n')
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

        fixed_code = '\n'.join(import_lines) + '\n\n' + '\n'.join(code_lines)
        fixed_code = fixed_code.strip() + '\n'

        return FixStatus.SUCCESS, fixed_code, confidence, f"已添加导入: {import_statement}", warnings


class RemoveUnusedImportStrategy(BaseFixStrategy):
    """移除未使用导入策略"""

    name = "remove_unused_import"
    description = "移除未使用的导入语句"
    category = FixCategory.IMPORT_FIX
    priority = FixPriority.LOW
    applicable_problems = ["unused_import"]

    def _do_fix(self, context: FixContext) -> Tuple[FixStatus, str, float, str, List[str]]:
        original_code = context.original_code
        warnings = []

        import_name = context.problem_data.get("import_name", "")
        full_name = context.problem_data.get("full_name", "")

        if not import_name:
            return FixStatus.FAILED, original_code, 0.0, "无法确定要移除的导入名称", warnings

        lines = original_code.split('\n')
        fixed_lines = []

        for line in lines:
            stripped = line.strip()

            should_remove = False

            if stripped.startswith('import '):
                names = [n.strip() for n in stripped[7:].split(',')]
                if import_name in names or full_name in names:
                    if len(names) == 1:
                        should_remove = True
                    else:
                        remaining = [n for n in names if n != import_name and n != full_name]
                        if remaining:
                            indent = len(line) - len(line.lstrip())
                            fixed_lines.append(' ' * indent + 'import ' + ', '.join(remaining))
                            continue
                        else:
                            should_remove = True

            elif stripped.startswith('from '):
                if import_name in stripped or (full_name and full_name in stripped):
                    match = re.match(r'from\s+(\S+)\s+import\s+(.+)', stripped)
                    if match:
                        module = match.group(1)
                        names = [n.strip() for n in match.group(2).split(',')]
                        if import_name in names:
                            if len(names) == 1:
                                should_remove = True
                            else:
                                remaining = [n for n in names if n != import_name]
                                if remaining:
                                    indent = len(line) - len(line.lstrip())
                                    fixed_lines.append(' ' * indent + f'from {module} import ' + ', '.join(remaining))
                                    continue
                                else:
                                    should_remove = True

            if not should_remove:
                fixed_lines.append(line)

        fixed_code = '\n'.join(fixed_lines)

        while '\n\n\n' in fixed_code:
            fixed_code = fixed_code.replace('\n\n\n', '\n\n')

        return FixStatus.SUCCESS, fixed_code, 0.95, f"已移除未使用的导入: {full_name or import_name}", warnings


class FixDeprecatedImportStrategy(BaseFixStrategy):
    """修复已弃用导入策略"""

    name = "fix_deprecated_import"
    description = "将已弃用的导入替换为现代替代"
    category = FixCategory.IMPORT_FIX
    priority = FixPriority.MEDIUM
    applicable_problems = ["deprecated_import"]

    REPLACEMENTS = {
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
        'tkFileDialog': 'tkinter.filedialog',
        'tkMessageBox': 'tkinter.messagebox',
    }

    def _do_fix(self, context: FixContext) -> Tuple[FixStatus, str, float, str, List[str]]:
        original_code = context.original_code
        warnings = []

        deprecated_module = context.problem_data.get("deprecated_module", "")
        replacement = context.problem_data.get("replacement", "")

        if not deprecated_module or not replacement:
            return FixStatus.FAILED, original_code, 0.0, "缺少弃用模块信息", warnings

        fixed_code = original_code

        if deprecated_module in self.REPLACEMENTS:
            fixed_code = fixed_code.replace(deprecated_module, replacement)
            warnings.append(f"已将 '{deprecated_module}' 替换为 '{replacement}'")

        confidence = 0.95

        return FixStatus.SUCCESS, fixed_code, confidence, f"已修复弃用导入: {deprecated_module} -> {replacement}", warnings


class AddTypeAnnotationStrategy(BaseFixStrategy):
    """添加类型注解策略"""

    name = "add_type_annotation"
    description = "为函数添加类型注解"
    category = FixCategory.TYPE_FIX
    priority = FixPriority.LOW
    applicable_problems = ["missing_type_annotation"]

    TYPE_INFERENCE = {
        'str': ['text', 'message', 'name', 'path', 'filename', 'url', 'email', 'password'],
        'int': ['count', 'index', 'size', 'length', 'num', 'age', 'port', 'timeout'],
        'float': ['rate', 'ratio', 'price', 'score', 'temperature', 'weight'],
        'bool': ['is_', 'has_', 'can_', 'should_', 'enable', 'disable', 'flag'],
        'List': ['items', 'list', 'values', 'elements', 'rows', 'records'],
        'Dict': ['data', 'config', 'options', 'params', 'kwargs', 'mapping'],
        'Optional': ['maybe', 'optional', 'nullable'],
    }

    def _do_fix(self, context: FixContext) -> Tuple[FixStatus, str, float, str, List[str]]:
        original_code = context.original_code
        warnings = []

        function_name = context.problem_data.get("function_name", "")
        missing = context.problem_data.get("missing", [])

        if not function_name:
            return FixStatus.FAILED, original_code, 0.0, "无法确定函数名称", warnings

        try:
            tree = ast.parse(original_code)
        except SyntaxError:
            return FixStatus.FAILED, original_code, 0.0, "代码存在语法错误", warnings

        fixed_code = original_code

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == function_name:
                lines = original_code.split('\n')
                func_line = lines[node.lineno - 1]

                args_with_types = []
                for arg in node.args.args:
                    if arg.annotation is None:
                        inferred_type = self._infer_type(arg.arg)
                        args_with_types.append(f"{arg.arg}: {inferred_type}")
                    else:
                        args_with_types.append(arg.arg)

                args_str = ', '.join(args_with_types)

                return_annotation = ""
                if node.returns is None:
                    return_annotation = " -> None"
                    for child in ast.walk(node):
                        if isinstance(child, ast.Return) and child.value:
                            return_annotation = " -> Any"
                            break

                indent = len(func_line) - len(func_line.lstrip())
                new_def = f"{' ' * indent}def {function_name}({args_str}){return_annotation}:"

                lines[node.lineno - 1] = new_def
                fixed_code = '\n'.join(lines)

                if 'Any' in return_annotation:
                    warnings.append("返回类型推断为 Any，建议手动指定具体类型")

                break

        confidence = 0.7

        return FixStatus.SUCCESS, fixed_code, confidence, f"已为函数 '{function_name}' 添加类型注解", warnings

    def _infer_type(self, arg_name: str) -> str:
        arg_lower = arg_name.lower()

        for type_name, patterns in self.TYPE_INFERENCE.items():
            for pattern in patterns:
                if pattern in arg_lower or arg_lower.startswith(pattern):
                    return type_name

        return "Any"


class RemoveUnusedVariableStrategy(BaseFixStrategy):
    """移除未使用变量策略"""

    name = "remove_unused_variable"
    description = "移除未使用的变量"
    category = FixCategory.UNUSED_CODE_FIX
    priority = FixPriority.LOW
    applicable_problems = ["unused_variable"]

    def _do_fix(self, context: FixContext) -> Tuple[FixStatus, str, float, str, List[str]]:
        original_code = context.original_code
        warnings = []

        variable_name = context.problem_data.get("variable_name", "")

        if not variable_name:
            return FixStatus.FAILED, original_code, 0.0, "无法确定变量名称", warnings

        lines = original_code.split('\n')
        fixed_lines = []

        for i, line in enumerate(lines, 1):
            if i == context.line_number:
                stripped = line.strip()

                if stripped.startswith(f"{variable_name} =") or stripped.startswith(f"{variable_name}="):
                    continue
                else:
                    pattern = rf'\b{variable_name}\s*='
                    if re.match(pattern, stripped):
                        continue

            fixed_lines.append(line)

        fixed_code = '\n'.join(fixed_lines)

        while '\n\n\n' in fixed_code:
            fixed_code = fixed_code.replace('\n\n\n', '\n\n')

        return FixStatus.SUCCESS, fixed_code, 0.9, f"已移除未使用的变量 '{variable_name}'", warnings


class RemoveUnusedFunctionStrategy(BaseFixStrategy):
    """移除未使用函数策略"""

    name = "remove_unused_function"
    description = "移除未使用的函数"
    category = FixCategory.UNUSED_CODE_FIX
    priority = FixPriority.LOW
    applicable_problems = ["unused_function"]

    def _do_fix(self, context: FixContext) -> Tuple[FixStatus, str, float, str, List[str]]:
        original_code = context.original_code
        warnings = []

        function_name = context.problem_data.get("function_name", "")

        if not function_name:
            return FixStatus.FAILED, original_code, 0.0, "无法确定函数名称", warnings

        try:
            tree = ast.parse(original_code)
        except SyntaxError:
            return FixStatus.FAILED, original_code, 0.0, "代码存在语法错误", warnings

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == function_name:
                start_line = node.lineno
                end_line = node.end_lineno if hasattr(node, 'end_lineno') else start_line

                lines = original_code.split('\n')
                fixed_lines = []

                for i, line in enumerate(lines, 1):
                    if i < start_line or i > end_line:
                        fixed_lines.append(line)

                fixed_code = '\n'.join(fixed_lines)

                while '\n\n\n' in fixed_code:
                    fixed_code = fixed_code.replace('\n\n\n', '\n\n')

                warnings.append(f"已移除函数 '{function_name}'，请确保没有其他代码依赖此函数")

                return FixStatus.SUCCESS, fixed_code, 0.85, f"已移除未使用的函数 '{function_name}'", warnings

        return FixStatus.FAILED, original_code, 0.0, f"未找到函数 '{function_name}'", warnings


class RemoveDeadCodeStrategy(BaseFixStrategy):
    """移除死代码策略"""

    name = "remove_dead_code"
    description = "移除不可达的死代码"
    category = FixCategory.UNUSED_CODE_FIX
    priority = FixPriority.MEDIUM
    applicable_problems = ["unreachable_code"]

    def _do_fix(self, context: FixContext) -> Tuple[FixStatus, str, float, str, List[str]]:
        original_code = context.original_code
        warnings = []

        lines = original_code.split('\n')

        if context.line_number <= 0 or context.line_number > len(lines):
            return FixStatus.FAILED, original_code, 0.0, "无效的行号", warnings

        fixed_lines = []
        skip_until_next_block = False
        current_indent = 0

        for i, line in enumerate(lines, 1):
            if i == context.line_number:
                skip_until_next_block = True
                current_indent = len(line) - len(line.lstrip())
                continue

            if skip_until_next_block:
                if line.strip() == '':
                    continue

                line_indent = len(line) - len(line.lstrip())

                if line_indent <= current_indent:
                    skip_until_next_block = False
                    fixed_lines.append(line)
            else:
                fixed_lines.append(line)

        fixed_code = '\n'.join(fixed_lines)

        return FixStatus.SUCCESS, fixed_code, 0.95, "已移除不可达代码", warnings


class SimplifyAssignmentStrategy(BaseFixStrategy):
    """简化赋值语句策略"""

    name = "simplify_assignment"
    description = "将 x = x op value 简化为 x op= value"
    category = FixCategory.CODE_SIMPLIFICATION
    priority = FixPriority.LOW
    applicable_problems = ["invalid_syntax_operator"]

    OPERATOR_MAP = {
        '+': '+=',
        '-': '-=',
        '*': '*=',
        '/': '/=',
        '%': '%=',
        '//': '//=',
        '**': '**=',
        '&': '&=',
        '|': '|=',
        '^': '^=',
        '<<': '<<=',
        '>>': '>>=',
    }

    def _do_fix(self, context: FixContext) -> Tuple[FixStatus, str, float, str, List[str]]:
        original_code = context.original_code
        warnings = []

        lines = original_code.split('\n')
        fixed_lines = []

        for line in lines:
            fixed_line = line

            for op, compound_op in self.OPERATOR_MAP.items():
                pattern = rf'(\w+)\s*=\s*\1\s*{re.escape(op)}\s*'
                if re.search(pattern, line):
                    fixed_line = re.sub(pattern, rf'\1 {compound_op} ', line)
                    warnings.append(f"已简化赋值语句: {op} -> {compound_op}")
                    break

            fixed_lines.append(fixed_line)

        fixed_code = '\n'.join(fixed_lines)

        return FixStatus.SUCCESS, fixed_code, 0.9, "已简化赋值语句", warnings


class FixStrategyExtension:
    """修复策略库扩展主类"""

    def __init__(self):
        self._strategies: Dict[str, BaseFixStrategy] = {}
        self._problem_type_map: Dict[str, List[str]] = {}
        self._register_builtin_strategies()

    def _register_builtin_strategies(self):
        strategies = [
            AddMissingImportStrategy(),
            RemoveUnusedImportStrategy(),
            FixDeprecatedImportStrategy(),
            AddTypeAnnotationStrategy(),
            RemoveUnusedVariableStrategy(),
            RemoveUnusedFunctionStrategy(),
            RemoveDeadCodeStrategy(),
            SimplifyAssignmentStrategy(),
        ]

        for strategy in strategies:
            self.register_strategy(strategy)

    def register_strategy(self, strategy: BaseFixStrategy) -> None:
        self._strategies[strategy.name] = strategy

        for problem_type in strategy.applicable_problems:
            if problem_type not in self._problem_type_map:
                self._problem_type_map[problem_type] = []
            self._problem_type_map[problem_type].append(strategy.name)

        logger.info(f"已注册策略: {strategy.name}")

    def get_strategy(self, strategy_name: str) -> Optional[BaseFixStrategy]:
        return self._strategies.get(strategy_name)

    def get_strategies_for_problem(self, problem_type: str) -> List[BaseFixStrategy]:
        strategy_names = self._problem_type_map.get(problem_type, [])
        strategies = [self._strategies[name] for name in strategy_names if name in self._strategies]
        strategies.sort(key=lambda s: s.priority.value)
        return strategies

    def fix(self, context: FixContext, strategy_name: Optional[str] = None) -> Optional[FixResult]:
        if strategy_name:
            strategy = self.get_strategy(strategy_name)
            if strategy and strategy.can_fix(context.problem_type):
                return strategy.apply(context)
            return None

        strategies = self.get_strategies_for_problem(context.problem_type)

        for strategy in strategies:
            if strategy.can_fix(context.problem_type):
                result = strategy.apply(context)
                if result.status in [FixStatus.SUCCESS, FixStatus.PARTIAL]:
                    return result

        return None

    def list_strategies(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": s.name,
                "description": s.description,
                "category": s.category.name,
                "priority": s.priority.name,
                "applicable_problems": s.applicable_problems
            }
            for s in self._strategies.values()
        ]


def main():
    import argparse

    parser = argparse.ArgumentParser(description="修复策略库扩展")
    parser.add_argument("--list-strategies", action="store_true", help="列出所有策略")
    parser.add_argument("--file", type=str, help="要修复的文件路径")
    parser.add_argument("--problem-type", type=str, help="问题类型")
    parser.add_argument("--line", type=int, default=0, help="问题所在行号")
    parser.add_argument("--data", type=str, help="问题数据（JSON格式）")

    args = parser.parse_args()

    library = FixStrategyExtension()

    if args.list_strategies:
        print("\n可用修复策略:")
        for strategy in library.list_strategies():
            print(f"\n  {strategy['name']}:")
            print(f"    描述: {strategy['description']}")
            print(f"    类别: {strategy['category']}")
            print(f"    优先级: {strategy['priority']}")
            print(f"    适用问题: {', '.join(strategy['applicable_problems'])}")
        return 0

    if args.file and args.problem_type:
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"读取文件失败: {e}")
            return 1

        problem_data = {}
        if args.data:
            try:
                problem_data = json.loads(args.data)
            except:
                pass

        context = FixContext(
            file_path=args.file,
            line_number=args.line,
            original_code=content,
            problem_type=args.problem_type,
            problem_data=problem_data
        )

        result = library.fix(context)

        if result:
            print(f"\n修复结果:")
            print(f"  策略: {result.strategy_name}")
            print(f"  状态: {result.status.value}")
            print(f"  置信度: {result.confidence:.0%}")
            print(f"  消息: {result.message}")

            if result.warnings:
                print(f"  警告:")
                for warning in result.warnings:
                    print(f"    - {warning}")

            print(f"\n修复后代码:")
            print(result.fixed_code)
        else:
            print("未找到适用的修复策略")

        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
