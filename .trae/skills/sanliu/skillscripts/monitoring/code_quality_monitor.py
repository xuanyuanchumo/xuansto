#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代码质量指标采集器 (CodeQualityMonitor)
======================================

采集和分析代码质量指标，包括：
- 圈复杂度 (Cyclomatic Complexity)
- 代码重复率 (Code Duplication)
- 代码异味检测 (Code Smells)
- 代码行数统计 (Lines of Code)
- 注释覆盖率 (Comment Coverage)

使用示例:
    >>> from skillscripts.monitoring.code_quality_monitor import CodeQualityMonitor
    >>> monitor = CodeQualityMonitor()
    >>> results = monitor.collect('path/to/project')
    >>> print(results['cyclomatic_complexity'])
"""

import ast
import json
import logging
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict


class CodeQualityMonitor:
    """
    代码质量指标采集器

    通过静态分析Python源码，采集多项代码质量指标，
    为六维质量监控提供代码维度数据。

    Attributes:
        METRICS: 支持的指标定义和阈值配置
    """

    METRICS: Dict[str, Dict[str, Any]] = {
        'cyclomatic_complexity': {
            'threshold': 10,
            'unit': 'score',
            'description': '函数圈复杂度'
        },
        'code_duplication': {
            'threshold': 5,
            'unit': '%',
            'description': '代码重复率'
        },
        'code_smells': {
            'threshold': 0,
            'unit': 'count',
            'description': '检测到的代码异味数'
        },
        'loc': {
            'threshold': None,
            'unit': 'lines',
            'description': '代码总行数'
        },
        'comment_coverage': {
            'threshold': 20,
            'unit': '%',
            'description': '注释覆盖率'
        }
    }

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        初始化代码质量监控器

        Args:
            logger: 可选的日志记录器
        """
        self.logger = logger or logging.getLogger(__name__)
        self._setup_logging()

    def _setup_logging(self):
        """配置日志"""
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def collect(self, project_path: str) -> Dict[str, Any]:
        """
        采集代码质量指标

        对指定项目路径进行全面的代码质量分析。

        Args:
            project_path: 项目根目录路径

        Returns:
            包含所有指标的字典，格式为：
            {
                'metric_name': {
                    'value': 实际值,
                    'threshold': 阈值,
                    'status': 'pass' | 'warning' | 'fail',
                    'details': 详细信息
                },
                ...
            }

        示例:
            >>> monitor = CodeQualityMonitor()
            >>> results = monitor.collect('myproject')
            >>> print(results['cyclomatic_complexity']['value'])
            7.5
        """
        self.logger.info(f"开始采集代码质量指标: {project_path}")

        results = {}

        for metric_name, config in self.METRICS.items():
            method_name = f'_collect_{metric_name}'
            method = getattr(self, method_name, None)

            if method:
                try:
                    metric_data = method(project_path)
                    results[metric_name] = {
                        **metric_data,
                        'threshold': config['threshold'],
                        'unit': config['unit'],
                        'description': config['description']
                    }
                    self.logger.debug(f"采集完成 [{metric_name}]: {metric_data.get('value')}")
                except Exception as e:
                    self.logger.error(f"采集失败 [{metric_name}]: {e}")
                    results[metric_name] = {
                        'value': None,
                        'threshold': config['threshold'],
                        'status': 'error',
                        'error': str(e),
                        'unit': config['unit'],
                        'description': config['description']
                    }

        self.logger.info("代码质量指标采集完成")

        return results

    def _collect_cyclomatic_complexity(self, project_path: str) -> Dict[str, Any]:
        """
        采集圈复杂度指标

        分析所有函数的圈复杂度并计算统计值

        Args:
            project_path: 项目路径

        Returns:
            圈复杂度数据字典
        """
        complexities = []
        high_complexity_functions = []

        for py_file in self._get_python_files(project_path):
            try:
                with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        complexity = self._calculate_complexity(node)
                        complexities.append(complexity)

                        if complexity > 10:
                            high_complexity_functions.append({
                                'file': str(py_file),
                                'function': node.name,
                                'line': node.lineno,
                                'complexity': complexity
                            })

            except SyntaxError:
                continue

        if not complexities:
            return {
                'value': 0,
                'status': 'pass',
                'details': {'message': '未找到可分析的函数'}
            }

        avg_complexity = sum(complexities) / len(complexities)
        max_complexity = max(complexities)

        status = 'pass' if avg_complexity <= 10 else ('warning' if avg_complexity <= 15 else 'fail')

        return {
            'value': round(avg_complexity, 2),
            'status': status,
            'details': {
                'average': round(avg_complexity, 2),
                'max': max_complexity,
                'functions_analyzed': len(complexities),
                'high_complexity_count': len(high_complexity_functions),
                'high_complexity_functions': high_complexity_functions[:10]
            }
        }

    def _calculate_complexity(self, node: ast.AST) -> int:
        """
        计算单个函数的圈复杂度

        Args:
            node: AST节点

        Returns:
            圈复杂度值
        """
        complexity = 1

        class ComplexityVisitor(ast.NodeVisitor):
            def visit_If(self, node):
                nonlocal complexity
                complexity += 1
                self.generic_visit(node)

            def visit_For(self, node):
                nonlocal complexity
                complexity += 1
                self.generic_visit(node)

            def visit_While(self, node):
                nonlocal complexity
                complexity += 1
                self.generic_visit(node)

            def visit_ExceptHandler(self, node):
                nonlocal complexity
                complexity += 1
                self.generic_visit(node)

            def visit_BoolOp(self, node):
                nonlocal complexity
                complexity += len(node.values) - 1
                self.generic_visit(node)

        visitor = ComplexityVisitor()
        visitor.visit(node)

        return complexity

    def _collect_code_duplication(self, project_path: str) -> Dict[str, Any]:
        """
        采集代码重复率指标

        检测重复的代码块并计算重复率

        Args:
            project_path: 项目路径

        Returns:
            代码重复率数据字典
        """
        BLOCK_SIZE = 6
        code_blocks: Dict[str, List[Tuple[Path, int]]] = defaultdict(list)
        total_blocks = 0

        for py_file in self._get_python_files(project_path):
            try:
                with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()

                for i in range(len(lines) - BLOCK_SIZE + 1):
                    block = ''.join(lines[i:i + BLOCK_SIZE])
                    normalized = re.sub(r'\s+', ' ', block).strip()

                    if normalized and not normalized.startswith('#'):
                        block_hash = hash(normalized)
                        code_blocks[block_hash].append((py_file, i + 1))
                        total_blocks += 1

            except Exception:
                continue

        duplicated_blocks = sum(1 for blocks in code_blocks.values() if len(blocks) > 1)
        duplication_rate = (duplicated_blocks / total_blocks * 100) if total_blocks > 0 else 0

        top_duplicates = sorted(
            [(hash_val, locations) for hash_val, locations in code_blocks.items() if len(locations) > 1],
            key=lambda x: len(x[1]),
            reverse=True
        )[:10]

        status = 'pass' if duplication_rate <= 5 else ('warning' if duplication_rate <= 10 else 'fail')

        return {
            'value': round(duplication_rate, 2),
            'status': status,
            'details': {
                'total_blocks': total_blocks,
                'duplicated_blocks': duplicated_blocks,
                'duplication_rate': round(duplication_rate, 2),
                'top_duplicates': [
                    {
                        'occurrences': len(locations),
                        'locations': [(str(f), line) for f, line in locations[:3]]
                    }
                    for _, locations in top_duplicates
                ]
            }
        }

    def _collect_code_smells(self, project_path: str) -> Dict[str, Any]:
        """
        采集代码异味指标

        检测常见的代码异味模式

        Args:
            project_path: 项目路径

        Returns:
            代码异味数据字典
        """
        smells = []

        THRESHOLDS = {
            'long_method': 50,
            'large_class': 300,
            'long_parameter_list': 5,
            'deep_nesting': 4
        }

        for py_file in self._get_python_files(project_path):
            try:
                with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        start_line = node.lineno
                        end_line = getattr(node, 'end_lineno', start_line) or start_line
                        line_count = end_line - start_line + 1

                        if line_count > THRESHOLDS['long_method']:
                            smells.append({
                                'type': 'long_method',
                                'file': str(py_file),
                                'name': node.name,
                                'line': start_line,
                                'lines': line_count,
                                'severity': 'high' if line_count > 100 else 'medium'
                            })

                        param_count = len(node.args.args) + len(node.args.kwonlyargs)
                        if param_count > THRESHOLDS['long_parameter_list']:
                            smells.append({
                                'type': 'long_parameter_list',
                                'file': str(py_file),
                                'name': node.name,
                                'line': start_line,
                                'parameters': param_count,
                                'severity': 'medium'
                            })

                    elif isinstance(node, ast.ClassDef):
                        start_line = node.lineno
                        end_line = getattr(node, 'end_lineno', start_line) or start_line
                        class_lines = end_line - start_line + 1

                        if class_lines > THRESHOLDS['large_class']:
                            smells.append({
                                'type': 'large_class',
                                'file': str(py_file),
                                'name': node.name,
                                'line': start_line,
                                'lines': class_lines,
                                'severity': 'high' if class_lines > 500 else 'medium'
                            })

            except SyntaxError:
                continue

        smell_count = len(smells)
        status = 'pass' if smell_count == 0 else ('warning' if smell_count <= 10 else 'fail')

        smells_by_type = defaultdict(list)
        for smell in smells:
            smells_by_type[smell['type']].append(smell)

        return {
            'value': smell_count,
            'status': status,
            'details': {
                'total_smells': smell_count,
                'by_type': {
                    smell_type: len(smell_list)
                    for smell_type, smell_list in smells_by_type.items()
                },
                'top_smells': sorted(smells, key=lambda x: (
                    {'high': 0, 'medium': 1, 'low': 2}.get(x.get('severity', 'low'), 2),
                    x.get('lines', 0) or x.get('parameters', 0)
                ), reverse=True)[:20]
            }
        }

    def _collect_loc(self, project_path: str) -> Dict[str, Any]:
        """
        采集代码行数指标

        统计项目的代码行数、注释行数等

        Args:
            project_path: 项目路径

        Returns:
            代码行数数据字典
        """
        total_lines = 0
        code_lines = 0
        comment_lines = 0
        blank_lines = 0
        file_count = 0

        for py_file in self._get_python_files(project_path):
            try:
                with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()

                file_count += 1
                for line in lines:
                    total_lines += 1
                    stripped = line.strip()

                    if not stripped:
                        blank_lines += 1
                    elif stripped.startswith('#'):
                        comment_lines += 1
                    else:
                        code_lines += 1

            except Exception:
                continue

        return {
            'value': total_lines,
            'status': 'pass',
            'details': {
                'total_lines': total_lines,
                'code_lines': code_lines,
                'comment_lines': comment_lines,
                'blank_lines': blank_lines,
                'files_analyzed': file_count,
                'avg_lines_per_file': round(total_lines / file_count, 1) if file_count > 0 else 0
            }
        }

    def _collect_comment_coverage(self, project_path: str) -> Dict[str, Any]:
        """
        采集注释覆盖率指标

        计算注释占代码行的比例

        Args:
            project_path: 项目路径

        Returns:
            注释覆盖率数据字典
        """
        loc_data = self._collect_loc(project_path)
        details = loc_data.get('details', {})

        code_lines = details.get('code_lines', 0)
        comment_lines = details.get('comment_lines', 0)

        coverage = (comment_lines / code_lines * 100) if code_lines > 0 else 0

        status = 'pass' if coverage >= 20 else ('warning' if coverage >= 10 else 'fail')

        return {
            'value': round(coverage, 2),
            'status': status,
            'details': {
                'coverage_percentage': round(coverage, 2),
                'code_lines': code_lines,
                'comment_lines': comment_lines,
                'target_threshold': 20
            }
        }

    def _get_python_files(self, project_path: Path) -> List[Path]:
        """
        获取项目中的所有Python文件

        Args:
            project_path: 项目路径

        Returns:
            Python文件路径列表
        """
        project = Path(project_path)

        exclude_dirs = {
            '__pycache__', '.git', '.venv', 'venv', 'node_modules',
            '.pytest_cache', 'build', 'dist', '.tox', '.mypy_cache',
            'htmlcov', '.idea', '.vscode'
        }

        python_files = []

        for py_file in project.rglob('*.py'):
            if not any(excluded in py_file.parts for excluded in exclude_dirs):
                python_files.append(py_file)

        return python_files


def main():
    """测试代码质量监控功能"""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    print("=" * 80)
    print("📊 代码质量监控测试")
    print("=" * 80)

    if len(sys.argv) > 1:
        project_path = sys.argv[1]
    else:
        project_path = str(Path(__file__).parent.parent.parent)

    monitor = CodeQualityMonitor()
    results = monitor.collect(project_path)

    print("\n📈 代码质量指标结果:\n")

    for metric_name, data in results.items():
        value = data.get('value')
        threshold = data.get('threshold')
        status = data.get('status', 'unknown')
        unit = data.get('unit', '')
        description = data.get('description', '')

        status_icon = {'pass': '✅', 'warning': '⚠️', 'fail': '❌', 'error': '💥'}.get(status, '❓')

        print(f"{status_icon} {description}")
        print(f"   当前值: {value}{unit}")

        if threshold is not None:
            print(f"   阈值: ≤{threshold}{unit}")

        details = data.get('details', {})
        if isinstance(details, dict):
            for key, val in details.items():
                if key not in ('high_complexity_functions', 'top_duplicates', 'top_smells'):
                    print(f"   {key}: {val}")

        print()

    print("✅ 测试完成!")


if __name__ == "__main__":
    main()
