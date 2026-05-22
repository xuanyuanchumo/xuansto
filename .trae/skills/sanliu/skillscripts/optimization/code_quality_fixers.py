"""
代码质量优化修复器模块

包含：
- CodeComplexityFixer: 代码复杂度优化
- CodeDuplicationFixer: 代码重复检测和消除
- NamingConventionFixer: 命名规范优化
- DocumentationFixer: 注释和文档优化
"""

import ast
import re
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime

from .auto_fixer import (
    FixStrategy,
    FixAction,
    FixType,
    RiskLevel,
)


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
