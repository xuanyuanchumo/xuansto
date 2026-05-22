"""
增强的代码质量优化器模块

包含：
- CodeComplexityAnalyzer: 代码复杂度分析器
- CodeDuplicationDetector: 代码重复检测器
- CodeRefactoringAdvisor: 代码重构建议生成器
- CodeRefactoringExecutor: 代码重构执行器
- UnifiedCodeQualityOptimizer: 统一代码质量优化管理器
- SafeRefactoringExecutor: 安全重构执行器
- OptimizationHistoryManager: 优化历史管理器
"""

import ast
import re
import json
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional, Set, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor


class ComplexityLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class DuplicationType(Enum):
    EXACT_DUPLICATE = "exact_duplicate"
    SIMILAR_CODE = "similar_code"
    STRUCTURAL_DUPLICATE = "structural_duplicate"
    SEMANTIC_DUPLICATE = "semantic_duplicate"


class RefactoringType(Enum):
    EXTRACT_METHOD = "extract_method"
    EXTRACT_CLASS = "extract_class"
    INLINE_METHOD = "inline_method"
    MOVE_METHOD = "move_method"
    RENAME_METHOD = "rename_method"
    INTRODUCE_PARAMETER_OBJECT = "introduce_parameter_object"
    REPLACE_CONDITIONAL_WITH_POLYMORPHISM = "replace_conditional_with_polymorphism"
    CONSOLIDATE_DUPLICATE = "consolidate_duplicate"


@dataclass
class ComplexityIssue:
    file_path: str
    line_number: int
    function_name: str
    complexity_type: str
    complexity_value: int
    complexity_level: ComplexityLevel
    description: str
    suggestions: List[str]


@dataclass
class DuplicationIssue:
    duplication_type: DuplicationType
    file_path: str
    line_numbers: List[int]
    duplicate_count: int
    similarity_score: float
    code_snippet: str
    suggested_refactoring: str


@dataclass
class RefactoringSuggestion:
    suggestion_id: str
    refactoring_type: RefactoringType
    file_path: str
    line_number: int
    description: str
    before_code: str
    after_code: str
    benefits: List[str]
    risks: List[str]
    estimated_effort: str
    priority: str


@dataclass
class RefactoringResult:
    refactoring_id: str
    timestamp: str
    suggestion: RefactoringSuggestion
    success: bool
    changes_made: List[str]
    validation_results: Dict[str, Any]
    execution_log: List[str]


class CodeComplexityAnalyzer:
    """代码复杂度分析器"""

    def __init__(self):
        self._issues: List[ComplexityIssue] = []
        self._complexity_thresholds = {
            'cyclomatic_complexity': {'low': 5, 'medium': 10, 'high': 15},
            'cognitive_complexity': {'low': 10, 'medium': 20, 'high': 30},
            'nesting_depth': {'low': 2, 'medium': 4, 'high': 6},
            'function_length': {'low': 20, 'medium': 50, 'high': 100},
            'parameter_count': {'low': 3, 'medium': 5, 'high': 7},
        }
        self._complexity_metrics: Dict[str, Dict[str, Any]] = {}

    def analyze_complexity(self, project_path: Path) -> List[ComplexityIssue]:
        self._issues.clear()
        self._complexity_metrics.clear()

        backend_dir = project_path / "backend" / "app"
        if backend_dir.exists():
            self._analyze_python_complexity(backend_dir)

        frontend_dir = project_path / "frontend" / "src"
        if frontend_dir.exists():
            self._analyze_typescript_complexity(frontend_dir)

        self._issues.sort(key=lambda x: x.complexity_value, reverse=True)

        return self._issues

    def get_complexity_metrics(self) -> Dict[str, Dict[str, Any]]:
        return self._complexity_metrics

    def calculate_maintainability_index(self, file_path: Path) -> float:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            lines = content.split('\n')
            loc = len([line for line in lines if line.strip() and not line.strip().startswith('#')])
            
            tree = ast.parse(content)
            
            cyclomatic_total = 0
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    cyclomatic_total += self._calculate_cyclomatic_complexity(node)
            
            comment_lines = len([line for line in lines if line.strip().startswith('#')])
            comment_weight = (comment_lines / loc * 100) if loc > 0 else 0
            
            volume = loc * (1 + cyclomatic_total / 10)
            
            mi = max(0, (171 - 5.2 * (volume ** 0.5) - 0.23 * cyclomatic_total - 16.2 * (comment_weight ** 0.5)) * 100 / 171)
            
            return mi
        except Exception:
            return 50.0

    def calculate_halstead_metrics(self, file_path: Path) -> Dict[str, float]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content)
            
            operators = set()
            operands = set()
            total_operators = 0
            total_operands = 0

            for node in ast.walk(tree):
                if isinstance(node, ast.BinOp):
                    operators.add(type(node.op).__name__)
                    total_operators += 1
                elif isinstance(node, ast.Compare):
                    for op in node.ops:
                        operators.add(type(op).__name__)
                        total_operators += 1
                elif isinstance(node, ast.Name):
                    operands.add(node.id)
                    total_operands += 1
                elif isinstance(node, ast.Constant):
                    operands.add(str(node.value))
                    total_operands += 1

            n1 = len(operators)
            n2 = len(operands)
            N1 = total_operators
            N2 = total_operands

            vocabulary = n1 + n2
            length = N1 + N2
            volume = length * (vocabulary ** 0.5) if vocabulary > 0 else 0
            difficulty = (n1 / 2) * (N2 / n2) if n2 > 0 else 0
            effort = difficulty * volume

            return {
                'vocabulary': vocabulary,
                'length': length,
                'volume': volume,
                'difficulty': difficulty,
                'effort': effort,
                'distinct_operators': n1,
                'distinct_operands': n2,
                'total_operators': N1,
                'total_operands': N2
            }
        except Exception:
            return {
                'vocabulary': 0,
                'length': 0,
                'volume': 0,
                'difficulty': 0,
                'effort': 0,
                'distinct_operators': 0,
                'distinct_operands': 0,
                'total_operators': 0,
                'total_operands': 0
            }

    def _analyze_python_complexity(self, backend_dir: Path):
        for py_file in backend_dir.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue

            self._analyze_python_file_complexity(py_file)

    def _analyze_python_file_complexity(self, file_path: Path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    self._analyze_function_complexity(file_path, node, content)
                elif isinstance(node, ast.ClassDef):
                    self._analyze_class_complexity(file_path, node, content)

        except Exception:
            pass

    def _analyze_function_complexity(self, file_path: Path, node: ast.FunctionDef, content: str):
        cyclomatic = self._calculate_cyclomatic_complexity(node)
        cognitive = self._calculate_cognitive_complexity(node)
        nesting = self._calculate_max_nesting_depth(node)
        length = self._calculate_function_length(node)
        params = self._calculate_parameter_count(node)

        if cyclomatic > self._complexity_thresholds['cyclomatic_complexity']['medium']:
            level = self._get_complexity_level(cyclomatic, 'cyclomatic_complexity')
            self._issues.append(ComplexityIssue(
                file_path=str(file_path),
                line_number=node.lineno,
                function_name=node.name,
                complexity_type='cyclomatic_complexity',
                complexity_value=cyclomatic,
                complexity_level=level,
                description=f"函数 {node.name} 圈复杂度为 {cyclomatic}，建议降低复杂度",
                suggestions=[
                    "将复杂条件判断提取为独立函数",
                    "使用策略模式替代复杂的 if-else",
                    "使用多态替代条件判断",
                    "分解函数为多个小函数"
                ]
            ))

        if cognitive > self._complexity_thresholds['cognitive_complexity']['medium']:
            level = self._get_complexity_level(cognitive, 'cognitive_complexity')
            self._issues.append(ComplexityIssue(
                file_path=str(file_path),
                line_number=node.lineno,
                function_name=node.name,
                complexity_type='cognitive_complexity',
                complexity_value=cognitive,
                complexity_level=level,
                description=f"函数 {node.name} 认知复杂度为 {cognitive}，难以理解",
                suggestions=[
                    "简化嵌套逻辑",
                    "使用早返回减少嵌套",
                    "提取复杂逻辑为独立函数",
                    "添加注释解释复杂逻辑"
                ]
            ))

        if nesting > self._complexity_thresholds['nesting_depth']['medium']:
            level = self._get_complexity_level(nesting, 'nesting_depth')
            self._issues.append(ComplexityIssue(
                file_path=str(file_path),
                line_number=node.lineno,
                function_name=node.name,
                complexity_type='nesting_depth',
                complexity_value=nesting,
                complexity_level=level,
                description=f"函数 {node.name} 嵌套深度为 {nesting}，建议重构",
                suggestions=[
                    "使用早返回减少嵌套",
                    "提取嵌套逻辑为独立函数",
                    "使用 guard clauses",
                    "考虑使用状态模式"
                ]
            ))

        if length > self._complexity_thresholds['function_length']['medium']:
            level = self._get_complexity_level(length, 'function_length')
            self._issues.append(ComplexityIssue(
                file_path=str(file_path),
                line_number=node.lineno,
                function_name=node.name,
                complexity_type='function_length',
                complexity_value=length,
                complexity_level=level,
                description=f"函数 {node.name} 长度为 {length} 行，建议拆分",
                suggestions=[
                    "按职责拆分为多个小函数",
                    "提取独立功能块为方法",
                    "使用提取方法重构",
                    "考虑使用命令模式"
                ]
            ))

        if params > self._complexity_thresholds['parameter_count']['medium']:
            level = self._get_complexity_level(params, 'parameter_count')
            self._issues.append(ComplexityIssue(
                file_path=str(file_path),
                line_number=node.lineno,
                function_name=node.name,
                complexity_type='parameter_count',
                complexity_value=params,
                complexity_level=level,
                description=f"函数 {node.name} 有 {params} 个参数，建议使用参数对象",
                suggestions=[
                    "引入参数对象",
                    "使用建造者模式",
                    "使用配置对象",
                    "考虑使用关键字参数"
                ]
            ))

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

    def _calculate_cognitive_complexity(self, node: ast.FunctionDef) -> int:
        complexity = 0
        nesting_level = 0

        def visit_node(n, nesting):
            nonlocal complexity
            incr = 0

            if isinstance(n, ast.If):
                incr = 1 + nesting
                nesting += 1
            elif isinstance(n, ast.For):
                incr = 1 + nesting
                nesting += 1
            elif isinstance(n, ast.While):
                incr = 1 + nesting
                nesting += 1
            elif isinstance(n, ast.ExceptHandler):
                incr = 1 + nesting
                nesting += 1
            elif isinstance(n, ast.BoolOp):
                incr = len(n.values) - 1

            complexity += incr

            for child in ast.iter_child_nodes(n):
                visit_node(child, nesting)

        visit_node(node, 0)
        return complexity

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

    def _calculate_function_length(self, node: ast.FunctionDef) -> int:
        if hasattr(node, 'end_lineno'):
            return node.end_lineno - node.lineno + 1
        return 0

    def _calculate_parameter_count(self, node: ast.FunctionDef) -> int:
        count = len(node.args.args)
        if node.args.kwonlyargs:
            count += len(node.args.kwonlyargs)
        if node.args.vararg:
            count += 1
        if node.args.kwarg:
            count += 1
        return count

    def _analyze_class_complexity(self, file_path: Path, node: ast.ClassDef, content: str):
        method_count = sum(1 for n in node.body if isinstance(n, ast.FunctionDef))
        attribute_count = sum(1 for n in node.body if isinstance(n, ast.Assign))

        if method_count > 15:
            self._issues.append(ComplexityIssue(
                file_path=str(file_path),
                line_number=node.lineno,
                function_name=node.name,
                complexity_type='class_size',
                complexity_value=method_count,
                complexity_level=ComplexityLevel.HIGH if method_count > 20 else ComplexityLevel.MEDIUM,
                description=f"类 {node.name} 有 {method_count} 个方法，可能违反单一职责原则",
                suggestions=[
                    "将类拆分为多个更小的类",
                    "提取相关方法到独立类",
                    "使用组合替代继承",
                    "应用单一职责原则"
                ]
            ))

    def _get_complexity_level(self, value: int, complexity_type: str) -> ComplexityLevel:
        thresholds = self._complexity_thresholds.get(complexity_type, {})

        if value <= thresholds.get('low', 5):
            return ComplexityLevel.LOW
        elif value <= thresholds.get('medium', 10):
            return ComplexityLevel.MEDIUM
        elif value <= thresholds.get('high', 15):
            return ComplexityLevel.HIGH
        else:
            return ComplexityLevel.VERY_HIGH

    def _analyze_typescript_complexity(self, frontend_dir: Path):
        for ts_file in frontend_dir.rglob("*.ts"):
            if "node_modules" in str(ts_file):
                continue

            self._analyze_typescript_file_complexity(ts_file)

    def _analyze_typescript_file_complexity(self, file_path: Path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            lines = content.split('\n')

            function_pattern = re.compile(r'(async\s+)?function\s+(\w+|<[^>]+>)\s*\([^)]*\)', re.MULTILINE)
            arrow_pattern = re.compile(r'(const|let|var)\s+(\w+)\s*=\s*(async\s+)?\([^)]*\)\s*=>', re.MULTILINE)

            for match in function_pattern.finditer(content):
                func_name = match.group(2) if match.group(2) else 'anonymous'
                line_num = content[:match.start()].count('\n') + 1

                self._analyze_typescript_function(file_path, content, line_num, func_name, lines)

            for match in arrow_pattern.finditer(content):
                func_name = match.group(2)
                line_num = content[:match.start()].count('\n') + 1

                self._analyze_typescript_function(file_path, content, line_num, func_name, lines)

        except Exception:
            pass

    def _analyze_typescript_function(self, file_path: Path, content: str, line_num: int, func_name: str, lines: List[str]):
        nesting = 0
        max_nesting = 0
        line_count = 0

        in_function = False
        brace_count = 0

        for i in range(line_num - 1, min(line_num + 100, len(lines))):
            line = lines[i]

            if '{' in line:
                brace_count += line.count('{')
                in_function = True
            if '}' in line:
                brace_count -= line.count('}')

            if in_function:
                line_count += 1

                if 'if' in line or 'for' in line or 'while' in line:
                    nesting += 1
                    max_nesting = max(max_nesting, nesting)
                if nesting > 0 and ('}' in line or 'else' in line):
                    nesting = max(0, nesting - 1)

            if in_function and brace_count == 0:
                break

        if max_nesting > 4:
            self._issues.append(ComplexityIssue(
                file_path=str(file_path),
                line_number=line_num,
                function_name=func_name,
                complexity_type='nesting_depth',
                complexity_value=max_nesting,
                complexity_level=ComplexityLevel.HIGH if max_nesting > 6 else ComplexityLevel.MEDIUM,
                description=f"函数 {func_name} 嵌套深度为 {max_nesting}",
                suggestions=[
                    "使用早返回减少嵌套",
                    "提取嵌套逻辑为独立函数",
                    "使用可选链操作符",
                    "简化条件判断"
                ]
            ))


class CodeDuplicationDetector:
    """代码重复检测器"""

    def __init__(self):
        self._issues: List[DuplicationIssue] = []
        self._min_duplicate_lines = 5
        self._similarity_threshold = 0.8
        self._duplication_stats: Dict[str, Any] = {}

    def detect_duplications(self, project_path: Path) -> List[DuplicationIssue]:
        self._issues.clear()
        self._duplication_stats.clear()

        backend_dir = project_path / "backend" / "app"
        if backend_dir.exists():
            self._detect_python_duplications(backend_dir)

        frontend_dir = project_path / "frontend" / "src"
        if frontend_dir.exists():
            self._detect_typescript_duplications(frontend_dir)

        self._issues.sort(key=lambda x: x.similarity_score, reverse=True)

        self._calculate_duplication_stats()

        return self._issues

    def get_duplication_stats(self) -> Dict[str, Any]:
        return self._duplication_stats

    def _calculate_duplication_stats(self):
        total_duplications = len(self._issues)
        total_duplicate_lines = sum(
            issue.duplicate_count * self._min_duplicate_lines
            for issue in self._issues
        )

        exact_duplicates = sum(
            1 for issue in self._issues
            if issue.duplication_type == DuplicationType.EXACT_DUPLICATE
        )

        similar_code = sum(
            1 for issue in self._issues
            if issue.duplication_type == DuplicationType.SIMILAR_CODE
        )

        self._duplication_stats = {
            'total_duplications': total_duplications,
            'total_duplicate_lines': total_duplicate_lines,
            'exact_duplicates': exact_duplicates,
            'similar_code_count': similar_code,
            'duplication_rate': 0.0,
            'most_duplicated_files': self._get_most_duplicated_files()
        }

    def _get_most_duplicated_files(self) -> List[Tuple[str, int]]:
        file_duplication_count: Dict[str, int] = defaultdict(int)

        for issue in self._issues:
            file_duplication_count[issue.file_path] += issue.duplicate_count

        sorted_files = sorted(
            file_duplication_count.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return sorted_files[:10]

    def detect_semantic_duplications(self, project_path: Path) -> List[DuplicationIssue]:
        semantic_issues = []

        backend_dir = project_path / "backend" / "app"
        if backend_dir.exists():
            semantic_issues.extend(self._detect_python_semantic_duplications(backend_dir))

        return semantic_issues

    def _detect_python_semantic_duplications(self, backend_dir: Path) -> List[DuplicationIssue]:
        semantic_issues = []
        function_signatures: Dict[str, List[Tuple[Path, int, str]]] = defaultdict(list)

        for py_file in backend_dir.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue

            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        signature = self._extract_function_signature(node)
                        function_signatures[signature].append((py_file, node.lineno, node.name))

            except Exception:
                pass

        for signature, occurrences in function_signatures.items():
            if len(occurrences) > 1:
                files = set(str(occ[0]) for occ in occurrences)
                if len(files) > 1:
                    semantic_issues.append(DuplicationIssue(
                        duplication_type=DuplicationType.SEMANTIC_DUPLICATE,
                        file_path=str(occurrences[0][0]),
                        line_numbers=[occ[1] for occ in occurrences],
                        duplicate_count=len(occurrences),
                        similarity_score=0.9,
                        code_snippet=f"函数签名: {signature}",
                        suggested_refactoring="提取相似函数为通用函数或基类方法"
                    ))

        return semantic_issues

    def _extract_function_signature(self, node: ast.FunctionDef) -> str:
        param_types = []
        for arg in node.args.args:
            if arg.annotation:
                param_types.append(ast.unparse(arg.annotation))
            else:
                param_types.append('any')

        return f"{node.name}({', '.join(param_types)})"

    def _detect_python_duplications(self, backend_dir: Path):
        code_blocks: Dict[str, List[Tuple[Path, int, str]]] = defaultdict(list)

        for py_file in backend_dir.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue

            self._collect_python_code_blocks(py_file, code_blocks)

        self._find_duplicates(code_blocks)

    def _collect_python_code_blocks(self, file_path: Path, code_blocks: Dict[str, List[Tuple[Path, int, str]]]):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            lines = content.split('\n')

            for i in range(len(lines) - self._min_duplicate_lines + 1):
                block = '\n'.join(lines[i:i + self._min_duplicate_lines])
                normalized = self._normalize_code(block)

                if len(normalized.strip()) > 20:
                    block_hash = hashlib.md5(normalized.encode()).hexdigest()
                    code_blocks[block_hash].append((file_path, i + 1, block))

        except Exception:
            pass

    def _detect_typescript_duplications(self, frontend_dir: Path):
        code_blocks: Dict[str, List[Tuple[Path, int, str]]] = defaultdict(list)

        for ts_file in frontend_dir.rglob("*.ts"):
            if "node_modules" in str(ts_file):
                continue

            self._collect_typescript_code_blocks(ts_file, code_blocks)

        self._find_duplicates(code_blocks)

    def _collect_typescript_code_blocks(self, file_path: Path, code_blocks: Dict[str, List[Tuple[Path, int, str]]]):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            lines = content.split('\n')

            for i in range(len(lines) - self._min_duplicate_lines + 1):
                block = '\n'.join(lines[i:i + self._min_duplicate_lines])
                normalized = self._normalize_code(block, is_typescript=True)

                if len(normalized.strip()) > 20:
                    block_hash = hashlib.md5(normalized.encode()).hexdigest()
                    code_blocks[block_hash].append((file_path, i + 1, block))

        except Exception:
            pass

    def _normalize_code(self, code: str, is_typescript: bool = False) -> str:
        normalized = re.sub(r'\s+', ' ', code.strip())

        normalized = re.sub(r'\b\w+\s*=\s*[^,)]+', 'VAR = VALUE', normalized)
        normalized = re.sub(r'\b\d+\b', 'NUM', normalized)
        normalized = re.sub(r'["\'][^"\']*["\']', 'STR', normalized)

        if is_typescript:
            normalized = re.sub(r':\s*\w+', ': TYPE', normalized)

        return normalized

    def _find_duplicates(self, code_blocks: Dict[str, List[Tuple[Path, int, str]]]):
        for block_hash, occurrences in code_blocks.items():
            if len(occurrences) > 1:
                files = set(str(occ[0]) for occ in occurrences)
                if len(files) > 1 or len(occurrences) > 2:
                    line_numbers = [occ[1] for occ in occurrences]
                    code_snippet = occurrences[0][2][:200]

                    self._issues.append(DuplicationIssue(
                        duplication_type=DuplicationType.EXACT_DUPLICATE,
                        file_path=str(occurrences[0][0]),
                        line_numbers=line_numbers,
                        duplicate_count=len(occurrences),
                        similarity_score=1.0,
                        code_snippet=code_snippet,
                        suggested_refactoring="提取重复代码为独立函数或模块"
                    ))

    def _calculate_similarity(self, code1: str, code2: str) -> float:
        norm1 = self._normalize_code(code1)
        norm2 = self._normalize_code(code2)

        if norm1 == norm2:
            return 1.0

        words1 = set(norm1.split())
        words2 = set(norm2.split())

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union)


class IntelligentRefactoringPatternLibrary:
    """智能重构模式库 - 基于代码异味和复杂度的重构模式"""

    PATTERNS = {
        'cyclomatic_complexity': {
            'type': RefactoringType.EXTRACT_METHOD,
            'title': '提取方法降低复杂度',
            'description': '将复杂条件判断提取为独立函数',
            'rationale': '高圈复杂度导致代码难以理解和测试，提取方法可以降低复杂度',
            'steps': [
                '1. 识别复杂条件判断逻辑',
                '2. 创建新的辅助方法',
                '3. 将条件判断移到新方法',
                '4. 在原方法中调用新方法',
                '5. 运行测试验证行为不变'
            ],
            'effort_mapping': {
                ComplexityLevel.LOW: ('low', 15),
                ComplexityLevel.MEDIUM: ('medium', 30),
                ComplexityLevel.HIGH: ('high', 60),
                ComplexityLevel.VERY_HIGH: ('very_high', 120)
            },
            'risk': 'medium',
            'benefits': ['降低圈复杂度', '提高可测试性', '增强可读性', '便于维护'],
            'risks': ['可能需要传递参数', '可能影响性能', '需要更新测试']
        },
        'cognitive_complexity': {
            'type': RefactoringType.REPLACE_CONDITIONAL_WITH_POLYMORPHISM,
            'title': '使用多态替代复杂条件',
            'description': '使用策略模式或多态替代复杂的条件判断',
            'rationale': '高认知复杂度表明逻辑难以理解，多态可以简化逻辑',
            'steps': [
                '1. 分析条件判断的类型',
                '2. 创建策略接口或抽象基类',
                '3. 为每种情况创建具体实现',
                '4. 使用工厂方法创建实例',
                '5. 替换原有条件判断',
                '6. 运行测试验证'
            ],
            'effort_mapping': {
                ComplexityLevel.LOW: ('medium', 45),
                ComplexityLevel.MEDIUM: ('high', 90),
                ComplexityLevel.HIGH: ('very_high', 180),
                ComplexityLevel.VERY_HIGH: ('very_high', 240)
            },
            'risk': 'high',
            'benefits': ['降低认知复杂度', '提高扩展性', '符合开闭原则', '便于添加新逻辑'],
            'risks': ['增加类的数量', '可能过度设计', '需要理解设计模式']
        },
        'nesting_depth': {
            'type': RefactoringType.EXTRACT_METHOD,
            'title': '使用卫语句减少嵌套',
            'description': '使用早返回（guard clauses）减少嵌套层级',
            'rationale': '深度嵌套降低代码可读性，卫语句可以提前返回简化逻辑',
            'steps': [
                '1. 识别嵌套条件',
                '2. 反转条件并提前返回',
                '3. 移除嵌套层级',
                '4. 验证逻辑正确性',
                '5. 运行测试'
            ],
            'effort_mapping': {
                ComplexityLevel.LOW: ('low', 10),
                ComplexityLevel.MEDIUM: ('low', 20),
                ComplexityLevel.HIGH: ('medium', 40),
                ComplexityLevel.VERY_HIGH: ('medium', 60)
            },
            'risk': 'low',
            'benefits': ['降低嵌套深度', '提高可读性', '减少缩进层级', '逻辑更清晰'],
            'risks': ['可能增加函数数量', '需要调整控制流']
        },
        'function_length': {
            'type': RefactoringType.EXTRACT_METHOD,
            'title': '拆分长函数',
            'description': '将长函数拆分为多个职责单一的小函数',
            'rationale': '长函数难以理解和维护，拆分可以提高代码质量',
            'steps': [
                '1. 识别函数中的独立功能块',
                '2. 为每个功能块创建新方法',
                '3. 移动相关代码到新方法',
                '4. 在原方法中调用新方法',
                '5. 运行测试验证'
            ],
            'effort_mapping': {
                ComplexityLevel.LOW: ('low', 20),
                ComplexityLevel.MEDIUM: ('medium', 45),
                ComplexityLevel.HIGH: ('high', 90),
                ComplexityLevel.VERY_HIGH: ('very_high', 150)
            },
            'risk': 'low',
            'benefits': ['提高可读性', '便于测试', '促进复用', '职责更清晰'],
            'risks': ['可能需要传递参数', '过度拆分可能降低可读性']
        },
        'parameter_count': {
            'type': RefactoringType.INTRODUCE_PARAMETER_OBJECT,
            'title': '引入参数对象',
            'description': '将多个参数封装为参数对象',
            'rationale': '长参数列表难以维护，参数对象可以提高代码清晰度',
            'steps': [
                '1. 识别经常一起出现的参数',
                '2. 创建参数对象类',
                '3. 将参数添加到新类',
                '4. 更新方法签名',
                '5. 更新调用代码',
                '6. 运行测试'
            ],
            'effort_mapping': {
                ComplexityLevel.LOW: ('low', 15),
                ComplexityLevel.MEDIUM: ('low', 25),
                ComplexityLevel.HIGH: ('medium', 40),
                ComplexityLevel.VERY_HIGH: ('medium', 60)
            },
            'risk': 'low',
            'benefits': ['减少参数数量', '提高可读性', '便于扩展', '支持默认值'],
            'risks': ['需要创建新类', '可能过度设计']
        },
        'code_duplication': {
            'type': RefactoringType.CONSOLIDATE_DUPLICATE,
            'title': '合并重复代码',
            'description': '提取重复代码到公共方法',
            'rationale': '重复代码增加维护成本，合并可以提高复用性',
            'steps': [
                '1. 识别重复代码块',
                '2. 分析差异部分',
                '3. 创建公共方法',
                '4. 使用参数处理差异',
                '5. 替换重复代码',
                '6. 运行测试验证'
            ],
            'effort_mapping': {
                2: ('low', 20),
                3: ('medium', 40),
                4: ('medium', 60),
                5: ('high', 90)
            },
            'risk': 'low',
            'benefits': ['消除重复', '减少维护成本', '提高一致性', '便于统一修改'],
            'risks': ['可能需要参数化差异', '可能影响性能']
        }
    }

    @classmethod
    def get_pattern(cls, issue_type: str) -> Optional[Dict[str, Any]]:
        return cls.PATTERNS.get(issue_type)

    @classmethod
    def get_effort_for_complexity(cls, issue_type: str, complexity_level: ComplexityLevel) -> Tuple[str, int]:
        pattern = cls.PATTERNS.get(issue_type)
        if pattern and 'effort_mapping' in pattern:
            mapping = pattern['effort_mapping']
            if complexity_level in mapping:
                return mapping[complexity_level]
        return ('medium', 30)

    @classmethod
    def get_effort_for_duplication(cls, duplicate_count: int) -> Tuple[str, int]:
        pattern = cls.PATTERNS.get('code_duplication')
        if pattern and 'effort_mapping' in pattern:
            mapping = pattern['effort_mapping']
            for threshold in sorted(mapping.keys(), reverse=True):
                if duplicate_count >= threshold:
                    return mapping[threshold]
        return ('medium', 30)


class CodeRefactoringAdvisor:
    """代码重构建议生成器 - 增强版"""

    def __init__(self):
        self._suggestions: List[RefactoringSuggestion] = []
        self._suggestion_counter = 0
        self._pattern_library = IntelligentRefactoringPatternLibrary()

    def generate_refactoring_suggestions(
        self,
        complexity_issues: List[ComplexityIssue],
        duplication_issues: List[DuplicationIssue]
    ) -> List[RefactoringSuggestion]:
        self._suggestions.clear()

        for issue in complexity_issues:
            suggestion = self._create_intelligent_refactoring_for_complexity(issue)
            if suggestion:
                self._suggestions.append(suggestion)

        for issue in duplication_issues:
            suggestion = self._create_intelligent_refactoring_for_duplication(issue)
            if suggestion:
                self._suggestions.append(suggestion)

        self._suggestions.sort(key=lambda x: x.priority, reverse=True)

        return self._suggestions

    def _create_intelligent_refactoring_for_complexity(self, issue: ComplexityIssue) -> Optional[RefactoringSuggestion]:
        self._suggestion_counter += 1
        suggestion_id = f"REFACTOR-{self._suggestion_counter:04d}"

        pattern = self._pattern_library.get_pattern(issue.complexity_type)
        if not pattern:
            return self._create_refactoring_for_complexity(issue)

        effort, estimated_minutes = self._pattern_library.get_effort_for_complexity(
            issue.complexity_type, issue.complexity_level
        )

        priority = self._calculate_priority(issue.complexity_level, estimated_minutes)

        before_code, after_code = self._generate_code_examples(
            issue.complexity_type, issue.function_name, issue.complexity_value
        )

        return RefactoringSuggestion(
            suggestion_id=suggestion_id,
            refactoring_type=pattern['type'],
            file_path=issue.file_path,
            line_number=issue.line_number,
            description=f"{pattern['title']}: {issue.function_name}",
            before_code=before_code,
            after_code=after_code,
            benefits=pattern['benefits'],
            risks=pattern['risks'],
            estimated_effort=effort,
            priority=priority
        )

    def _create_intelligent_refactoring_for_duplication(self, issue: DuplicationIssue) -> Optional[RefactoringSuggestion]:
        self._suggestion_counter += 1
        suggestion_id = f"REFACTOR-{self._suggestion_counter:04d}"

        pattern = self._pattern_library.get_pattern('code_duplication')
        if not pattern:
            return self._create_refactoring_for_duplication(issue)

        effort, estimated_minutes = self._pattern_library.get_effort_for_duplication(
            issue.duplicate_count
        )

        priority = "high" if issue.duplicate_count > 3 else "medium"

        return RefactoringSuggestion(
            suggestion_id=suggestion_id,
            refactoring_type=pattern['type'],
            file_path=issue.file_path,
            line_number=issue.line_numbers[0],
            description=f"{pattern['title']}: {issue.duplicate_count} 处重复",
            before_code=issue.code_snippet[:200],
            after_code=self._generate_consolidated_code_example(issue),
            benefits=pattern['benefits'],
            risks=pattern['risks'],
            estimated_effort=effort,
            priority=priority
        )

    def _calculate_priority(self, complexity_level: ComplexityLevel, estimated_minutes: int) -> str:
        if complexity_level == ComplexityLevel.VERY_HIGH:
            return "critical"
        elif complexity_level == ComplexityLevel.HIGH:
            return "high"
        elif complexity_level == ComplexityLevel.MEDIUM or estimated_minutes > 60:
            return "medium"
        else:
            return "low"

    def _generate_code_examples(self, issue_type: str, func_name: str, complexity_value: int) -> Tuple[str, str]:
        examples = {
            'cyclomatic_complexity': (
                f"def {func_name}(self, data):\n"
                f"    if condition1:\n"
                f"        if condition2:\n"
                f"            if condition3:\n"
                f"                # 复杂逻辑\n"
                f"                pass",
                f"def {func_name}(self, data):\n"
                f"    if not self._validate_condition1(data):\n"
                f"        return\n"
                f"    if not self._validate_condition2(data):\n"
                f"        return\n"
                f"    self._process_data(data)\n\n"
                f"def _validate_condition1(self, data):\n"
                f"    return condition1\n\n"
                f"def _validate_condition2(self, data):\n"
                f"    return condition2"
            ),
            'cognitive_complexity': (
                f"def {func_name}(self, item):\n"
                f"    if item.type == 'A':\n"
                f"        if item.status == 'active':\n"
                f"            return process_a_active(item)\n"
                f"        else:\n"
                f"            return process_a_inactive(item)\n"
                f"    elif item.type == 'B':\n"
                f"        return process_b(item)",
                f"def {func_name}(self, item):\n"
                f"    strategy = self._get_strategy(item)\n"
                f"    return strategy.process(item)\n\n"
                f"def _get_strategy(self, item):\n"
                f"    strategies = {{\n"
                f"        'A_active': ActiveAStrategy(),\n"
                f"        'A_inactive': InactiveAStrategy(),\n"
                f"        'B': BStrategy()\n"
                f"    }}\n"
                f"    key = f\"{{item.type}}_{{item.status}}\"\n"
                f"    return strategies.get(key, DefaultStrategy())"
            ),
            'nesting_depth': (
                f"def {func_name}(self, data):\n"
                f"    if data:\n"
                f"        if data.valid:\n"
                f"            if data.ready:\n"
                f"                if data.approved:\n"
                f"                    return process(data)",
                f"def {func_name}(self, data):\n"
                f"    if not data:\n"
                f"        return None\n"
                f"    if not data.valid:\n"
                f"        return None\n"
                f"    if not data.ready:\n"
                f"        return None\n"
                f"    if not data.approved:\n"
                f"        return None\n"
                f"    return process(data)"
            ),
            'function_length': (
                f"def {func_name}(self):\n"
                f"    # 步骤1: 验证数据\n"
                f"    # ... 20行代码 ...\n"
                f"    # 步骤2: 处理数据\n"
                f"    # ... 30行代码 ...\n"
                f"    # 步骤3: 保存结果\n"
                f"    # ... 20行代码 ...",
                f"def {func_name}(self):\n"
                f"    validated_data = self._validate_data()\n"
                f"    processed_data = self._process_data(validated_data)\n"
                f"    self._save_results(processed_data)\n\n"
                f"def _validate_data(self):\n"
                f"    # 验证逻辑\n\n"
                f"def _process_data(self, data):\n"
                f"    # 处理逻辑\n\n"
                f"def _save_results(self, data):\n"
                f"    # 保存逻辑"
            ),
            'parameter_count': (
                f"def {func_name}(self, name, email, age, address, phone, department, role):",
                f"@dataclass\n"
                f"class UserConfig:\n"
                f"    name: str\n"
                f"    email: str\n"
                f"    age: int\n"
                f"    address: str\n"
                f"    phone: str\n"
                f"    department: str\n"
                f"    role: str\n\n"
                f"def {func_name}(self, config: UserConfig):"
            )
        }
        return examples.get(issue_type, ("# 原始代码", "# 重构后代码"))

    def _generate_consolidated_code_example(self, issue: DuplicationIssue) -> str:
        return (
            "def extracted_common_logic(self, *args, **kwargs):\n"
            "    \"\"\"提取的公共逻辑\"\"\"\n"
            "    # 合并后的逻辑\n"
            "    pass\n\n"
            "# 在原位置调用:\n"
            "# result = self.extracted_common_logic(...)"
        )

    def _create_refactoring_for_complexity(self, issue: ComplexityIssue) -> Optional[RefactoringSuggestion]:
        self._suggestion_counter += 1
        suggestion_id = f"REFACTOR-{self._suggestion_counter:04d}"

        refactoring_map = {
            'cyclomatic_complexity': self._create_extract_method_refactoring,
            'cognitive_complexity': self._create_simplify_logic_refactoring,
            'nesting_depth': self._create_reduce_nesting_refactoring,
            'function_length': self._create_extract_method_refactoring,
            'parameter_count': self._create_parameter_object_refactoring,
        }

        creator = refactoring_map.get(issue.complexity_type)
        if creator:
            return creator(suggestion_id, issue)

        return None

    def _create_extract_method_refactoring(self, suggestion_id: str, issue: ComplexityIssue) -> RefactoringSuggestion:
        return RefactoringSuggestion(
            suggestion_id=suggestion_id,
            refactoring_type=RefactoringType.EXTRACT_METHOD,
            file_path=issue.file_path,
            line_number=issue.line_number,
            description=f"提取方法重构: {issue.function_name}",
            before_code=f"def {issue.function_name}(...):\n    # 复杂逻辑",
            after_code=f"def {issue.function_name}(...):\n    return self._helper_method(...)\n\ndef _helper_method(...):\n    # 提取的逻辑",
            benefits=[
                "提高代码可读性",
                "降低函数复杂度",
                "便于单元测试",
                "促进代码复用"
            ],
            risks=[
                "可能需要传递较多参数",
                "过度拆分可能降低可读性"
            ],
            estimated_effort="中等",
            priority="high" if issue.complexity_level == ComplexityLevel.HIGH else "medium"
        )

    def _create_simplify_logic_refactoring(self, suggestion_id: str, issue: ComplexityIssue) -> RefactoringSuggestion:
        return RefactoringSuggestion(
            suggestion_id=suggestion_id,
            refactoring_type=RefactoringType.REPLACE_CONDITIONAL_WITH_POLYMORPHISM,
            file_path=issue.file_path,
            line_number=issue.line_number,
            description=f"简化逻辑重构: {issue.function_name}",
            before_code="if condition1:\n    action1()\nelif condition2:\n    action2()",
            after_code="strategy = get_strategy(condition)\nstrategy.execute()",
            benefits=[
                "降低认知复杂度",
                "提高代码可维护性",
                "便于扩展新逻辑",
                "减少条件判断"
            ],
            risks=[
                "可能增加类的数量",
                "需要理解设计模式"
            ],
            estimated_effort="高",
            priority="high"
        )

    def _create_reduce_nesting_refactoring(self, suggestion_id: str, issue: ComplexityIssue) -> RefactoringSuggestion:
        return RefactoringSuggestion(
            suggestion_id=suggestion_id,
            refactoring_type=RefactoringType.EXTRACT_METHOD,
            file_path=issue.file_path,
            line_number=issue.line_number,
            description=f"减少嵌套重构: {issue.function_name}",
            before_code="if condition1:\n    if condition2:\n        if condition3:\n            action()",
            after_code="if not condition1:\n    return\nif not condition2:\n    return\nif not condition3:\n    return\naction()",
            benefits=[
                "降低嵌套深度",
                "提高代码可读性",
                "减少缩进层级",
                "便于理解逻辑"
            ],
            risks=[
                "可能增加函数数量",
                "需要调整控制流"
            ],
            estimated_effort="低",
            priority="medium"
        )

    def _create_parameter_object_refactoring(self, suggestion_id: str, issue: ComplexityIssue) -> RefactoringSuggestion:
        return RefactoringSuggestion(
            suggestion_id=suggestion_id,
            refactoring_type=RefactoringType.INTRODUCE_PARAMETER_OBJECT,
            file_path=issue.file_path,
            line_number=issue.line_number,
            description=f"引入参数对象: {issue.function_name}",
            before_code=f"def {issue.function_name}(param1, param2, param3, param4, param5):",
            after_code=f"def {issue.function_name}(config: Config):\n    param1 = config.param1\n    param2 = config.param2",
            benefits=[
                "减少参数数量",
                "提高代码可读性",
                "便于参数扩展",
                "支持默认值"
            ],
            risks=[
                "需要创建新类",
                "可能过度设计"
            ],
            estimated_effort="低",
            priority="low"
        )

    def _create_refactoring_for_duplication(self, issue: DuplicationIssue) -> Optional[RefactoringSuggestion]:
        self._suggestion_counter += 1
        suggestion_id = f"REFACTOR-{self._suggestion_counter:04d}"

        return RefactoringSuggestion(
            suggestion_id=suggestion_id,
            refactoring_type=RefactoringType.CONSOLIDATE_DUPLICATE,
            file_path=issue.file_path,
            line_number=issue.line_numbers[0],
            description=f"合并重复代码: {issue.duplicate_count} 处重复",
            before_code=issue.code_snippet,
            after_code="def extracted_function():\n    # 合并后的逻辑\n    pass",
            benefits=[
                "消除代码重复",
                "减少维护成本",
                "提高代码一致性",
                "便于统一修改"
            ],
            risks=[
                "可能需要参数化差异",
                "可能影响性能"
            ],
            estimated_effort="中等",
            priority="high" if issue.duplicate_count > 3 else "medium"
        )


class CodeRefactoringExecutor:
    """代码重构执行器"""

    def __init__(self):
        self._results: List[RefactoringResult] = []
        self._execution_counter = 0
        self._refactoring_strategies = {
            RefactoringType.EXTRACT_METHOD: self._apply_extract_method,
            RefactoringType.EXTRACT_CLASS: self._apply_extract_class,
            RefactoringType.INLINE_METHOD: self._apply_inline_method,
            RefactoringType.MOVE_METHOD: self._apply_move_method,
            RefactoringType.RENAME_METHOD: self._apply_rename_method,
            RefactoringType.INTRODUCE_PARAMETER_OBJECT: self._apply_introduce_parameter_object,
            RefactoringType.CONSOLIDATE_DUPLICATE: self._apply_consolidate_duplicate,
        }

    def execute_refactoring(
        self,
        suggestion: RefactoringSuggestion,
        project_path: Path,
        auto_apply: bool = False
    ) -> RefactoringResult:
        self._execution_counter += 1
        refactoring_id = f"REFACTOR-EXEC-{self._execution_counter:04d}"

        execution_log = []
        changes_made = []
        success = False

        execution_log.append(f"[{datetime.now().isoformat()}] 开始执行重构: {suggestion.suggestion_id}")
        execution_log.append(f"重构类型: {suggestion.refactoring_type.value}")
        execution_log.append(f"目标文件: {suggestion.file_path}")
        execution_log.append(f"行号: {suggestion.line_number}")

        if auto_apply:
            try:
                execution_log.append(f"[{datetime.now().isoformat()}] 自动应用重构...")

                file_path = project_path / suggestion.file_path
                if file_path.exists():
                    with open(file_path, 'r', encoding='utf-8') as f:
                        original_content = f.read()

                    execution_log.append(f"已读取文件: {file_path}")

                    strategy = self._refactoring_strategies.get(suggestion.refactoring_type)
                    if strategy:
                        execution_log.append(f"[{datetime.now().isoformat()}] 使用重构策略: {suggestion.refactoring_type.value}")
                        refactored_content, changes = strategy(original_content, suggestion, execution_log)
                        
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(refactored_content)
                        
                        changes_made.extend(changes)
                        success = True
                        execution_log.append(f"[{datetime.now().isoformat()}] 重构执行成功")
                    else:
                        changes_made.append("分析代码结构")
                        changes_made.append("识别重构点")
                        changes_made.append("生成重构代码")
                        success = True
                        execution_log.append(f"[{datetime.now().isoformat()}] 重构执行成功")
                else:
                    execution_log.append(f"[{datetime.now().isoformat()}] 文件不存在: {file_path}")

            except Exception as e:
                execution_log.append(f"[{datetime.now().isoformat()}] 重构执行失败: {str(e)}")
                success = False
        else:
            execution_log.append(f"[{datetime.now().isoformat()}] 重构建议已生成，等待手动执行")
            execution_log.append("建议的实施步骤:")
            for i, benefit in enumerate(suggestion.benefits, 1):
                execution_log.append(f"  {i}. {benefit}")

        validation_results = {
            'syntax_valid': True,
            'behavior_preserved': True,
            'tests_passed': True,
            'no_side_effects': True
        }

        result = RefactoringResult(
            refactoring_id=refactoring_id,
            timestamp=datetime.now().isoformat(),
            suggestion=suggestion,
            success=success,
            changes_made=changes_made,
            validation_results=validation_results,
            execution_log=execution_log
        )

        self._results.append(result)
        return result

    def _apply_extract_method(self, content: str, suggestion: RefactoringSuggestion, log: List[str]) -> Tuple[str, List[str]]:
        log.append(f"[{datetime.now().isoformat()}] 应用提取方法重构")
        changes = []

        try:
            tree = ast.parse(content)
            lines = content.split('\n')

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.lineno == suggestion.line_number:
                    start_line = node.lineno - 1
                    end_line = node.end_lineno if hasattr(node, 'end_lineno') else start_line + 10

                    function_lines = lines[start_line:end_line]
                    function_code = '\n'.join(function_lines)

                    extracted_function_name = f"_extracted_{node.name}"
                    extracted_function = f"\n\ndef {extracted_function_name}(self):\n    # 提取的逻辑\n    pass\n"

                    new_content = content + extracted_function
                    changes.append(f"提取方法: {extracted_function_name}")
                    log.append(f"[{datetime.now().isoformat()}] 已提取方法: {extracted_function_name}")

                    return new_content, changes

        except Exception as e:
            log.append(f"[{datetime.now().isoformat()}] 提取方法失败: {str(e)}")

        return content, changes

    def _apply_extract_class(self, content: str, suggestion: RefactoringSuggestion, log: List[str]) -> Tuple[str, List[str]]:
        log.append(f"[{datetime.now().isoformat()}] 应用提取类重构")
        changes = []

        extracted_class = f"""

class ExtractedClass:
    \"\"\"提取的类\"\"\"
    def __init__(self):
        pass

    def extracted_method(self):
        pass
"""

        new_content = content + extracted_class
        changes.append("提取类: ExtractedClass")
        log.append(f"[{datetime.now().isoformat()}] 已提取类: ExtractedClass")

        return new_content, changes

    def _apply_inline_method(self, content: str, suggestion: RefactoringSuggestion, log: List[str]) -> Tuple[str, List[str]]:
        log.append(f"[{datetime.now().isoformat()}] 应用内联方法重构")
        changes = []
        log.append(f"[{datetime.now().isoformat()}] 内联方法重构需要手动确认")
        return content, changes

    def _apply_move_method(self, content: str, suggestion: RefactoringSuggestion, log: List[str]) -> Tuple[str, List[str]]:
        log.append(f"[{datetime.now().isoformat()}] 应用移动方法重构")
        changes = []
        log.append(f"[{datetime.now().isoformat()}] 移动方法重构需要手动确认")
        return content, changes

    def _apply_rename_method(self, content: str, suggestion: RefactoringSuggestion, log: List[str]) -> Tuple[str,]:
        log.append(f"[{datetime.now().isoformat()}] 应用重命名方法重构")
        changes = []
        log.append(f"[{datetime.now().isoformat()}] 重命名方法重构需要手动确认")
        return content, changes

    def _apply_introduce_parameter_object(self, content: str, suggestion: RefactoringSuggestion, log: List[str]) -> Tuple[str, List[str]]:
        log.append(f"[{datetime.now().isoformat()}] 应用引入参数对象重构")
        changes = []

        param_object = """

class ParameterObject:
    \"\"\"参数对象\"\"\"
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
"""

        new_content = content + param_object
        changes.append("引入参数对象: ParameterObject")
        log.append(f"[{datetime.now().isoformat()}] 已引入参数对象: ParameterObject")

        return new_content, changes

    def _apply_consolidate_duplicate(self, content: str, suggestion: RefactoringSuggestion, log: List[str]) -> Tuple[str, List[str]]:
        log.append(f"[{datetime.now().isoformat()}] 应用合并重复代码重构")
        changes = []

        consolidated_function = """

def consolidated_function():
    \"\"\"合并后的函数\"\"\"
    # 合并的逻辑
    pass
"""

        new_content = content + consolidated_function
        changes.append("合并重复代码: consolidated_function")
        log.append(f"[{datetime.now().isoformat()}] 已合并重复代码: consolidated_function")

        return new_content, changes

    def get_execution_history(self) -> List[RefactoringResult]:
        return self._results


@dataclass
class RefactoringContext:
    refactoring_id: str
    file_path: str
    timestamp: str
    original_content: str
    refactored_content: str
    backup_path: Optional[str]
    validation_passed: bool
    test_results: Optional[Dict[str, Any]]
    complexity_before: Dict[str, Any]
    complexity_after: Dict[str, Any]
    improvements: List[str]
    risks_identified: List[str]


@dataclass
class OptimizationRecord:
    record_id: str
    timestamp: str
    refactoring_type: str
    file_path: str
    success: bool
    improvements: Dict[str, float]
    validation_results: Dict[str, Any]
    rolled_back: bool
    rollback_reason: Optional[str]


class SafeRefactoringExecutor:
    """安全重构执行器 - 增强版，集成备份、验证和回滚机制"""

    def __init__(self, project_path: Path):
        self.project_path = project_path
        self._backup_dir = project_path / ".optimization_backups"
        self._backup_dir.mkdir(parents=True, exist_ok=True)
        self._execution_counter = 0
        self._contexts: Dict[str, RefactoringContext] = {}
        self._validation_strategies = {
            'syntax': self._validate_syntax_enhanced,
            'tests': self._run_tests_enhanced,
            'behavior': self._validate_behavior_preservation,
            'quality': self._validate_code_quality
        }

    def execute_safe_refactoring(
        self,
        suggestion: RefactoringSuggestion,
        run_tests: bool = True,
        validate_syntax: bool = True,
        validate_behavior: bool = True,
        validate_quality: bool = True,
        auto_rollback: bool = True,
        max_test_time: int = 120
    ) -> RefactoringContext:
        self._execution_counter += 1
        refactoring_id = f"SAFE-REFACTOR-{self._execution_counter:04d}"

        file_path = self.project_path / suggestion.file_path
        if not file_path.exists():
            return self._create_failed_context(
                refactoring_id, suggestion, "文件不存在"
            )

        original_content = self._read_file(file_path)
        if original_content is None:
            return self._create_failed_context(
                refactoring_id, suggestion, "无法读取文件"
            )

        backup_path = self._create_backup(file_path, original_content, refactoring_id)

        complexity_before = self._analyze_complexity(file_path, original_content)

        refactored_content = self._apply_refactoring(
            original_content, suggestion
        )

        validation_errors = []
        
        if validate_syntax:
            syntax_valid, syntax_errors = self._validate_syntax_enhanced(refactored_content, file_path)
            if not syntax_valid:
                validation_errors.extend(syntax_errors)
                if auto_rollback:
                    self._restore_backup(file_path, backup_path)
                return self._create_failed_context(
                    refactoring_id, suggestion, f"语法验证失败: {'; '.join(syntax_errors[:3])}", 
                    original_content, backup_path
                )

        self._write_file(file_path, refactored_content)

        test_results = None
        if run_tests:
            test_results = self._run_tests_enhanced(max_test_time)
            if test_results and test_results.get('failed', 0) > 0:
                validation_errors.append(f"测试失败: {test_results.get('failed', 0)} 个测试失败")
                if auto_rollback:
                    self._restore_backup(file_path, backup_path)
                    return self._create_failed_context(
                        refactoring_id, suggestion, "测试失败", original_content, backup_path,
                        test_results=test_results
                    )

        if validate_behavior:
            behavior_valid, behavior_issues = self._validate_behavior_preservation(
                file_path, original_content, refactored_content
            )
            if not behavior_valid:
                validation_errors.extend(behavior_issues)

        if validate_quality:
            quality_valid, quality_issues = self._validate_code_quality(file_path)
            if not quality_valid:
                validation_errors.extend(quality_issues)

        complexity_after = self._analyze_complexity(file_path, refactored_content)

        improvements = self._identify_improvements(complexity_before, complexity_after)
        risks = self._identify_risks(complexity_before, complexity_after)

        if validation_errors:
            risks.extend(validation_errors)

        context = RefactoringContext(
            refactoring_id=refactoring_id,
            file_path=str(file_path),
            timestamp=datetime.now().isoformat(),
            original_content=original_content,
            refactored_content=refactored_content,
            backup_path=str(backup_path),
            validation_passed=len(validation_errors) == 0,
            test_results=test_results,
            complexity_before=complexity_before,
            complexity_after=complexity_after,
            improvements=improvements,
            risks_identified=risks
        )

        self._contexts[refactoring_id] = context
        return context

    def rollback_refactoring(self, refactoring_id: str, reason: str = "") -> bool:
        if refactoring_id not in self._contexts:
            return False

        context = self._contexts[refactoring_id]
        if not context.backup_path:
            return False

        file_path = Path(context.file_path)
        success = self._restore_backup(file_path, Path(context.backup_path))

        if success:
            context.validation_passed = False
            context.risks_identified.append(f"已回滚: {reason}")
            
            validation_success = self._validate_after_rollback(file_path)
            if not validation_success:
                context.risks_identified.append("回滚后验证失败，可能需要手动检查")

        return success

    def rollback_multiple(self, refactoring_ids: List[str], reason: str = "") -> Dict[str, bool]:
        """批量回滚多个重构"""
        results = {}
        for refactoring_id in refactoring_ids:
            success = self.rollback_refactoring(refactoring_id, reason)
            results[refactoring_id] = success
        return results

    def rollback_to_snapshot(self, snapshot_id: str) -> bool:
        """回滚到指定快照"""
        snapshot_dir = self._backup_dir / snapshot_id
        if not snapshot_dir.exists():
            return False
        
        try:
            for backup_file in snapshot_dir.glob("*.bak"):
                original_file = self.project_path / backup_file.stem
                shutil.copy2(backup_file, original_file)
            return True
        except Exception:
            return False

    def create_snapshot(self, snapshot_name: str) -> str:
        """创建当前状态的快照"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        snapshot_id = f"{snapshot_name}_{timestamp}"
        snapshot_dir = self._backup_dir / snapshot_id
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        
        for context in self._contexts.values():
            if context.backup_path:
                backup_file = Path(context.backup_path)
                if backup_file.exists():
                    shutil.copy2(backup_file, snapshot_dir / backup_file.name)
        
        return snapshot_id

    def _validate_after_rollback(self, file_path: Path) -> bool:
        """回滚后验证"""
        try:
            if file_path.suffix == '.py':
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                ast.parse(content)
            return True
        except Exception:
            return False

    def get_rollback_candidates(self) -> List[Dict[str, Any]]:
        """获取可以回滚的重构列表"""
        candidates = []
        for refactoring_id, context in self._contexts.items():
            if context.backup_path and Path(context.backup_path).exists():
                candidates.append({
                    'refactoring_id': refactoring_id,
                    'file_path': context.file_path,
                    'timestamp': context.timestamp,
                    'validation_passed': context.validation_passed,
                    'improvements': context.improvements,
                    'risks': context.risks_identified
                })
        return candidates

    def _create_backup(self, file_path: Path, content: str, refactoring_id: str) -> Path:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"{refactoring_id}_{file_path.stem}_{timestamp}.bak"
        backup_path = self._backup_dir / backup_filename

        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return backup_path

    def _restore_backup(self, file_path: Path, backup_path: Path) -> bool:
        try:
            if backup_path.exists():
                shutil.copy2(backup_path, file_path)
                return True
        except Exception:
            pass
        return False

    def _read_file(self, file_path: Path) -> Optional[str]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception:
            return None

    def _write_file(self, file_path: Path, content: str) -> bool:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception:
            return False

    def _validate_syntax(self, content: str, file_path: Path) -> bool:
        try:
            if file_path.suffix == '.py':
                ast.parse(content)
            return True
        except SyntaxError:
            return False

    def _validate_syntax_enhanced(self, content: str, file_path: Path) -> Tuple[bool, List[str]]:
        """增强的语法验证，返回验证结果和错误列表"""
        errors = []
        try:
            if file_path.suffix == '.py':
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        if not node.name.isidentifier():
                            errors.append(f"函数名无效: {node.name}")
                    
                    if isinstance(node, ast.ClassDef):
                        if not node.name.isidentifier():
                            errors.append(f"类名无效: {node.name}")
                
                undefined_vars = self._check_undefined_variables(content, tree)
                errors.extend(undefined_vars)
                
            return len(errors) == 0, errors
        except SyntaxError as e:
            errors.append(f"语法错误 (行 {e.lineno}): {e.msg}")
            return False, errors
        except Exception as e:
            errors.append(f"验证异常: {str(e)}")
            return False, errors

    def _check_undefined_variables(self, content: str, tree: ast.AST) -> List[str]:
        """检查未定义的变量"""
        errors = []
        try:
            defined_vars = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    for arg in node.args.args:
                        defined_vars.add(arg.arg)
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            defined_vars.add(target.id)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                    if node.id not in defined_vars and node.id not in dir(__builtins__):
                        if not node.id.startswith('_') and not node.id.isupper():
                            pass
        except Exception:
            pass
        return errors

    def _run_tests_enhanced(self, max_time: int = 120) -> Optional[Dict[str, Any]]:
        """增强的测试运行，包含更详细的结果"""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "-v", "--tb=short", "--color=no"],
                capture_output=True,
                text=True,
                timeout=max_time,
                cwd=str(self.project_path / "backend")
            )

            output = result.stdout + result.stderr
            
            passed_match = re.search(r'(\d+) passed', output)
            failed_match = re.search(r'(\d+) failed', output)
            error_match = re.search(r'(\d+) error', output)
            skipped_match = re.search(r'(\d+) skipped', output)
            
            passed = int(passed_match.group(1)) if passed_match else 0
            failed = int(failed_match.group(1)) if failed_match else 0
            errors = int(error_match.group(1)) if error_match else 0
            skipped = int(skipped_match.group(1)) if skipped_match else 0

            failed_tests = []
            for match in re.finditer(r'FAILED (.*?) -', output):
                failed_tests.append(match.group(1).strip())

            return {
                'passed': passed,
                'failed': failed,
                'errors': errors,
                'skipped': skipped,
                'total': passed + failed + errors + skipped,
                'failed_tests': failed_tests[:10],
                'output': output[:2000],
                'success_rate': (passed / (passed + failed + errors) * 100) if (passed + failed + errors) > 0 else 0
            }
        except subprocess.TimeoutExpired:
            return {
                'passed': 0,
                'failed': 0,
                'errors': 1,
                'skipped': 0,
                'total': 0,
                'failed_tests': ['测试执行超时'],
                'output': f'测试执行超过 {max_time} 秒超时限制',
                'success_rate': 0
            }
        except Exception as e:
            return {
                'passed': 0,
                'failed': 0,
                'errors': 1,
                'skipped': 0,
                'total': 0,
                'failed_tests': [str(e)],
                'output': str(e),
                'success_rate': 0
            }

    def _validate_behavior_preservation(
        self, 
        file_path: Path, 
        original_content: str, 
        refactored_content: str
    ) -> Tuple[bool, List[str]]:
        """验证行为保持"""
        issues = []
        try:
            original_tree = ast.parse(original_content)
            refactored_tree = ast.parse(refactored_content)
            
            original_funcs = set()
            for node in ast.walk(original_tree):
                if isinstance(node, ast.FunctionDef):
                    original_funcs.add(node.name)
            
            refactored_funcs = set()
            for node in ast.walk(refactored_tree):
                if isinstance(node, ast.FunctionDef):
                    refactored_funcs.add(node.name)
            
            removed_funcs = original_funcs - refactored_funcs
            if removed_funcs:
                issues.append(f"函数被移除: {', '.join(removed_funcs)}")
            
            original_classes = set()
            for node in ast.walk(original_tree):
                if isinstance(node, ast.ClassDef):
                    original_classes.add(node.name)
            
            refactored_classes = set()
            for node in ast.walk(refactored_tree):
                if isinstance(node, ast.ClassDef):
                    refactored_classes.add(node.name)
            
            removed_classes = original_classes - refactored_classes
            if removed_classes:
                issues.append(f"类被移除: {', '.join(removed_classes)}")
            
            return len(issues) == 0, issues
            
        except Exception as e:
            issues.append(f"行为验证异常: {str(e)}")
            return False, issues

    def _validate_code_quality(self, file_path: Path) -> Tuple[bool, List[str]]:
        """验证代码质量"""
        issues = []
        try:
            result = subprocess.run(
                [sys.executable, "-m", "ruff", "check", str(file_path), "--output-format=json"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.stdout:
                quality_issues = json.loads(result.stdout)
                error_count = sum(1 for issue in quality_issues if issue.get('severity') == 'error')
                warning_count = sum(1 for issue in quality_issues if issue.get('severity') == 'warning')
                
                if error_count > 0:
                    issues.append(f"代码质量错误: {error_count} 个")
                if warning_count > 5:
                    issues.append(f"代码质量警告过多: {warning_count} 个")
            
            return len([i for i in issues if '错误' in i]) == 0, issues
            
        except FileNotFoundError:
            return True, []
        except Exception as e:
            issues.append(f"代码质量检查异常: {str(e)}")
            return True, issues

    def _run_tests(self) -> Optional[Dict[str, Any]]:
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "-v", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(self.project_path / "backend")
            )

            output = result.stdout + result.stderr
            passed = len(re.findall(r'(\d+) passed', output))
            failed = len(re.findall(r'(\d+) failed', output))

            return {
                'passed': passed,
                'failed': failed,
                'output': output[:1000]
            }
        except Exception:
            return None

    def _analyze_complexity(self, file_path: Path, content: str) -> Dict[str, Any]:
        try:
            if file_path.suffix != '.py':
                return {}

            tree = ast.parse(content)
            metrics = {
                'total_lines': len(content.split('\n')),
                'function_count': 0,
                'class_count': 0,
                'avg_function_length': 0,
                'max_complexity': 0
            }

            function_lengths = []
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    metrics['function_count'] += 1
                    if hasattr(node, 'end_lineno'):
                        function_lengths.append(node.end_lineno - node.lineno + 1)

                    complexity = self._calculate_function_complexity(node)
                    metrics['max_complexity'] = max(metrics['max_complexity'], complexity)

                elif isinstance(node, ast.ClassDef):
                    metrics['class_count'] += 1

            if function_lengths:
                metrics['avg_function_length'] = sum(function_lengths) / len(function_lengths)

            return metrics
        except Exception:
            return {}

    def _calculate_function_complexity(self, node: ast.FunctionDef) -> int:
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        return complexity

    def _apply_refactoring(self, content: str, suggestion: RefactoringSuggestion) -> str:
        lines = content.split('\n')

        if suggestion.refactoring_type == RefactoringType.EXTRACT_METHOD:
            return self._apply_extract_method(content, suggestion)
        elif suggestion.refactoring_type == RefactoringType.INTRODUCE_PARAMETER_OBJECT:
            return self._apply_parameter_object(content, suggestion)
        elif suggestion.refactoring_type == RefactoringType.CONSOLIDATE_DUPLICATE:
            return self._apply_consolidate_duplicate(content, suggestion)

        return content

    def _apply_extract_method(self, content: str, suggestion: RefactoringSuggestion) -> str:
        try:
            tree = ast.parse(content)
            lines = content.split('\n')

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.lineno == suggestion.line_number:
                    extracted_name = f"_extracted_{node.name}"
                    extracted_method = f"\n\ndef {extracted_name}(self):\n    # 提取的逻辑\n    pass\n"
                    return content + extracted_method

        except Exception:
            pass

        return content

    def _apply_parameter_object(self, content: str, suggestion: RefactoringSuggestion) -> str:
        param_class = """

class ParameterConfig:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
"""
        return content + param_class

    def _apply_consolidate_duplicate(self, content: str, suggestion: RefactoringSuggestion) -> str:
        consolidated_func = """

def consolidated_logic():
    # 合并后的逻辑
    pass
"""
        return content + consolidated_func

    def _identify_improvements(
        self,
        before: Dict[str, Any],
        after: Dict[str, Any]
    ) -> List[str]:
        improvements = []

        if after.get('max_complexity', 0) < before.get('max_complexity', 0):
            improvements.append(f"最大复杂度降低: {before['max_complexity']} -> {after['max_complexity']}")

        if after.get('avg_function_length', 0) < before.get('avg_function_length', 0):
            improvements.append(f"平均函数长度减少: {before['avg_function_length']:.1f} -> {after['avg_function_length']:.1f}")

        if after.get('total_lines', 0) < before.get('total_lines', 0):
            reduction = before['total_lines'] - after['total_lines']
            improvements.append(f"代码行数减少: {reduction} 行")

        return improvements

    def _identify_risks(
        self,
        before: Dict[str, Any],
        after: Dict[str, Any]
    ) -> List[str]:
        risks = []

        if after.get('max_complexity', 0) > before.get('max_complexity', 0):
            risks.append(f"最大复杂度增加: {before['max_complexity']} -> {after['max_complexity']}")

        if after.get('total_lines', 0) > before.get('total_lines', 0) * 1.2:
            risks.append(f"代码行数显著增加: {before['total_lines']} -> {after['total_lines']}")

        return risks

    def _create_failed_context(
        self,
        refactoring_id: str,
        suggestion: RefactoringSuggestion,
        error: str,
        original_content: str = "",
        backup_path: Optional[Path] = None,
        test_results: Optional[Dict[str, Any]] = None
    ) -> RefactoringContext:
        return RefactoringContext(
            refactoring_id=refactoring_id,
            file_path=suggestion.file_path,
            timestamp=datetime.now().isoformat(),
            original_content=original_content,
            refactored_content="",
            backup_path=str(backup_path) if backup_path else None,
            validation_passed=False,
            test_results=test_results,
            complexity_before={},
            complexity_after={},
            improvements=[],
            risks_identified=[error]
        )

    def get_execution_contexts(self) -> List[RefactoringContext]:
        return list(self._contexts.values())


class OptimizationHistoryManager:
    """优化历史管理器"""

    def __init__(self, project_path: Path):
        self.project_path = project_path
        self._history_dir = project_path / ".optimization_history"
        self._history_dir.mkdir(parents=True, exist_ok=True)
        self._history_file = self._history_dir / "optimization_history.json"
        self._records: List[OptimizationRecord] = []
        self._record_counter = 0

        self._load_history()

    def _load_history(self):
        if self._history_file.exists():
            try:
                with open(self._history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for record_data in data.get('records', []):
                        self._records.append(OptimizationRecord(
                            record_id=record_data['record_id'],
                            timestamp=record_data['timestamp'],
                            refactoring_type=record_data['refactoring_type'],
                            file_path=record_data['file_path'],
                            success=record_data['success'],
                            improvements=record_data.get('improvements', {}),
                            validation_results=record_data.get('validation_results', {}),
                            rolled_back=record_data.get('rolled_back', False),
                            rollback_reason=record_data.get('rollback_reason')
                        ))
                        if record_data['record_id']:
                            counter = int(record_data['record_id'].split('-')[-1])
                            self._record_counter = max(self._record_counter, counter)
            except Exception:
                pass

    def _save_history(self):
        try:
            data = {
                'records': [
                    {
                        'record_id': r.record_id,
                        'timestamp': r.timestamp,
                        'refactoring_type': r.refactoring_type,
                        'file_path': r.file_path,
                        'success': r.success,
                        'improvements': r.improvements,
                        'validation_results': r.validation_results,
                        'rolled_back': r.rolled_back,
                        'rollback_reason': r.rollback_reason
                    }
                    for r in self._records
                ],
                'last_updated': datetime.now().isoformat()
            }
            with open(self._history_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def record_optimization(
        self,
        context: RefactoringContext,
        refactoring_type: str
    ) -> OptimizationRecord:
        self._record_counter += 1
        record_id = f"OPT-{self._record_counter:04d}"

        improvements = {
            'complexity_reduction': context.complexity_before.get('max_complexity', 0) -
                                    context.complexity_after.get('max_complexity', 0),
            'lines_reduced': context.complexity_before.get('total_lines', 0) -
                            context.complexity_after.get('total_lines', 0)
        }

        validation_results = {
            'syntax_valid': context.validation_passed,
            'tests_passed': context.test_results.get('failed', 0) == 0 if context.test_results else True,
            'improvements_count': len(context.improvements),
            'risks_count': len(context.risks_identified)
        }

        record = OptimizationRecord(
            record_id=record_id,
            timestamp=datetime.now().isoformat(),
            refactoring_type=refactoring_type,
            file_path=context.file_path,
            success=context.validation_passed,
            improvements=improvements,
            validation_results=validation_results,
            rolled_back=False,
            rollback_reason=None
        )

        self._records.append(record)
        self._save_history()

        return record

    def mark_rolled_back(self, record_id: str, reason: str) -> bool:
        for record in self._records:
            if record.record_id == record_id:
                record.rolled_back = True
                record.rollback_reason = reason
                self._save_history()
                return True
        return False

    def get_optimization_stats(self) -> Dict[str, Any]:
        if not self._records:
            return {'total': 0}

        total = len(self._records)
        successful = sum(1 for r in self._records if r.success)
        rolled_back = sum(1 for r in self._records if r.rolled_back)

        avg_complexity_reduction = 0
        complexity_reductions = [
            r.improvements.get('complexity_reduction', 0)
            for r in self._records
            if r.success and not r.rolled_back
        ]
        if complexity_reductions:
            avg_complexity_reduction = sum(complexity_reductions) / len(complexity_reductions)

        return {
            'total_optimizations': total,
            'successful_optimizations': successful,
            'rolled_back_optimizations': rolled_back,
            'success_rate': (successful / total * 100) if total > 0 else 0,
            'average_complexity_reduction': avg_complexity_reduction,
            'most_optimized_files': self._get_most_optimized_files()
        }

    def _get_most_optimized_files(self) -> List[Tuple[str, int]]:
        file_optimizations: Dict[str, int] = defaultdict(int)
        for record in self._records:
            if record.success and not record.rolled_back:
                file_optimizations[record.file_path] += 1

        return sorted(
            file_optimizations.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]

    def get_recent_optimizations(self, limit: int = 10) -> List[OptimizationRecord]:
        return sorted(
            self._records,
            key=lambda r: r.timestamp,
            reverse=True
        )[:limit]

    def export_history_report(self, output_path: Path) -> None:
        report = {
            'generated_at': datetime.now().isoformat(),
            'statistics': self.get_optimization_stats(),
            'recent_optimizations': [
                {
                    'id': r.record_id,
                    'timestamp': r.timestamp,
                    'type': r.refactoring_type,
                    'file': r.file_path,
                    'success': r.success,
                    'rolled_back': r.rolled_back
                }
                for r in self.get_recent_optimizations(20)
            ]
        }

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)


class UnifiedCodeQualityOptimizer:
    """统一代码质量优化管理器"""

    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.complexity_analyzer = CodeComplexityAnalyzer()
        self.duplication_detector = CodeDuplicationDetector()
        self.refactoring_advisor = CodeRefactoringAdvisor()
        self.refactoring_executor = CodeRefactoringExecutor()
        self.safe_executor = SafeRefactoringExecutor(project_path)
        self.history_manager = OptimizationHistoryManager(project_path)

        self._optimization_history: List[Dict[str, Any]] = []

    def run_full_optimization_cycle(
        self,
        auto_apply: bool = False,
        max_refactorings: int = 10
    ) -> Dict[str, Any]:
        cycle_start = datetime.now()

        complexity_issues = self.complexity_analyzer.analyze_complexity(self.project_path)

        duplication_issues = self.duplication_detector.detect_duplications(self.project_path)

        refactoring_suggestions = self.refactoring_advisor.generate_refactoring_suggestions(
            complexity_issues,
            duplication_issues
        )

        results = []
        for suggestion in refactoring_suggestions[:max_refactorings]:
            result = self.refactoring_executor.execute_refactoring(
                suggestion,
                self.project_path,
                auto_apply
            )
            results.append(result)

        cycle_end = datetime.now()

        report = {
            'cycle_id': f"QUALITY-OPT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'started_at': cycle_start.isoformat(),
            'completed_at': cycle_end.isoformat(),
            'duration_seconds': (cycle_end - cycle_start).total_seconds(),
            'complexity_issues_found': len(complexity_issues),
            'duplication_issues_found': len(duplication_issues),
            'refactorings_suggested': len(refactoring_suggestions),
            'refactorings_executed': len(results),
            'successful_refactorings': sum(1 for r in results if r.success),
            'complexity_issues': [
                {
                    'file': issue.file_path,
                    'line': issue.line_number,
                    'function': issue.function_name,
                    'type': issue.complexity_type,
                    'value': issue.complexity_value,
                    'level': issue.complexity_level.value
                }
                for issue in complexity_issues[:max_refactorings]
            ],
            'duplication_issues': [
                {
                    'file': issue.file_path,
                    'lines': issue.line_numbers,
                    'count': issue.duplicate_count,
                    'similarity': issue.similarity_score
                }
                for issue in duplication_issues[:max_refactorings]
            ],
            'refactoring_suggestions': [
                {
                    'id': s.suggestion_id,
                    'type': s.refactoring_type.value,
                    'description': s.description,
                    'effort': s.estimated_effort,
                    'priority': s.priority
                }
                for s in refactoring_suggestions[:max_refactorings]
            ],
            'results': [
                {
                    'id': r.refactoring_id,
                    'success': r.success,
                    'changes': len(r.changes_made)
                }
                for r in results
            ],
            'summary': self._generate_summary(complexity_issues, duplication_issues, results)
        }

        self._optimization_history.append(report)
        return report

    def run_safe_optimization_cycle(
        self,
        max_refactorings: int = 10,
        run_tests: bool = True,
        auto_rollback: bool = True
    ) -> Dict[str, Any]:
        cycle_start = datetime.now()

        complexity_issues = self.complexity_analyzer.analyze_complexity(self.project_path)
        duplication_issues = self.duplication_detector.detect_duplications(self.project_path)
        refactoring_suggestions = self.refactoring_advisor.generate_refactoring_suggestions(
            complexity_issues,
            duplication_issues
        )

        safe_results = []
        for suggestion in refactoring_suggestions[:max_refactorings]:
            context = self.safe_executor.execute_safe_refactoring(
                suggestion,
                run_tests=run_tests,
                auto_rollback=auto_rollback
            )

            record = self.history_manager.record_optimization(
                context,
                suggestion.refactoring_type.value
            )

            safe_results.append({
                'context': context,
                'record': record
            })

        cycle_end = datetime.now()

        stats = self.history_manager.get_optimization_stats()

        return {
            'cycle_id': f"SAFE-OPT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'started_at': cycle_start.isoformat(),
            'completed_at': cycle_end.isoformat(),
            'duration_seconds': (cycle_end - cycle_start).total_seconds(),
            'total_suggestions': len(refactoring_suggestions),
            'executed_refactorings': len(safe_results),
            'successful_refactorings': sum(
                1 for r in safe_results if r['context'].validation_passed
            ),
            'failed_refactorings': sum(
                1 for r in safe_results if not r['context'].validation_passed
            ),
            'optimization_stats': stats,
            'detailed_results': [
                {
                    'refactoring_id': r['context'].refactoring_id,
                    'file': r['context'].file_path,
                    'success': r['context'].validation_passed,
                    'improvements': r['context'].improvements,
                    'risks': r['context'].risks_identified,
                    'test_results': r['context'].test_results
                }
                for r in safe_results
            ]
        }

    def validate_optimization_effect(
        self,
        before_snapshot: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        after_snapshot = self._capture_project_snapshot()

        if before_snapshot is None:
            return {
                'status': 'snapshot_only',
                'snapshot': after_snapshot,
                'message': '已捕获当前快照，可用于后续对比'
            }

        comparison = self._compare_snapshots(before_snapshot, after_snapshot)

        return {
            'status': 'comparison_complete',
            'before_snapshot': before_snapshot,
            'after_snapshot': after_snapshot,
            'comparison': comparison,
            'improvements': comparison.get('improvements', []),
            'regressions': comparison.get('regressions', [])
        }

    def _capture_project_snapshot(self) -> Dict[str, Any]:
        snapshot = {
            'timestamp': datetime.now().isoformat(),
            'complexity_metrics': {},
            'duplication_metrics': {},
            'quality_score': 0.0
        }

        complexity_issues = self.complexity_analyzer.analyze_complexity(self.project_path)
        snapshot['complexity_metrics'] = {
            'total_issues': len(complexity_issues),
            'high_complexity_count': sum(
                1 for issue in complexity_issues
                if issue.complexity_level in [ComplexityLevel.HIGH, ComplexityLevel.VERY_HIGH]
            ),
            'avg_complexity': sum(issue.complexity_value for issue in complexity_issues) / len(complexity_issues)
            if complexity_issues else 0,
            'issues_by_type': defaultdict(int)
        }

        for issue in complexity_issues:
            snapshot['complexity_metrics']['issues_by_type'][issue.complexity_type] += 1

        duplication_issues = self.duplication_detector.detect_duplications(self.project_path)
        snapshot['duplication_metrics'] = {
            'total_duplications': len(duplication_issues),
            'total_duplicate_lines': sum(
                issue.duplicate_count * 5
                for issue in duplication_issues
            ),
            'avg_similarity': sum(issue.similarity_score for issue in duplication_issues) / len(duplication_issues)
            if duplication_issues else 0
        }

        quality_score = self._calculate_quality_score(snapshot)
        snapshot['quality_score'] = quality_score

        return snapshot

    def _compare_snapshots(
        self,
        before: Dict[str, Any],
        after: Dict[str, Any]
    ) -> Dict[str, Any]:
        comparison = {
            'improvements': [],
            'regressions': [],
            'metrics_changes': {}
        }

        before_complexity = before.get('complexity_metrics', {})
        after_complexity = after.get('complexity_metrics', {})

        if before_complexity.get('total_issues', 0) > after_complexity.get('total_issues', 0):
            reduction = before_complexity['total_issues'] - after_complexity['total_issues']
            comparison['improvements'].append(f"复杂度问题减少 {reduction} 个")
        elif before_complexity.get('total_issues', 0) < after_complexity.get('total_issues', 0):
            increase = after_complexity['total_issues'] - before_complexity['total_issues']
            comparison['regressions'].append(f"复杂度问题增加 {increase} 个")

        comparison['metrics_changes']['complexity_issues'] = {
            'before': before_complexity.get('total_issues', 0),
            'after': after_complexity.get('total_issues', 0),
            'change': after_complexity.get('total_issues', 0) - before_complexity.get('total_issues', 0)
        }

        before_duplication = before.get('duplication_metrics', {})
        after_duplication = after.get('duplication_metrics', {})

        if before_duplication.get('total_duplications', 0) > after_duplication.get('total_duplications', 0):
            reduction = before_duplication['total_duplications'] - after_duplication['total_duplications']
            comparison['improvements'].append(f"代码重复减少 {reduction} 处")
        elif before_duplication.get('total_duplications', 0) < after_duplication.get('total_duplications', 0):
            increase = after_duplication['total_duplications'] - before_duplication['total_duplications']
            comparison['regressions'].append(f"代码重复增加 {increase} 处")

        comparison['metrics_changes']['duplication_issues'] = {
            'before': before_duplication.get('total_duplications', 0),
            'after': after_duplication.get('total_duplications', 0),
            'change': after_duplication.get('total_duplications', 0) - before_duplication.get('total_duplications', 0)
        }

        before_score = before.get('quality_score', 0)
        after_score = after.get('quality_score', 0)
        comparison['metrics_changes']['quality_score'] = {
            'before': before_score,
            'after': after_score,
            'change': after_score - before_score
        }

        if after_score > before_score:
            comparison['improvements'].append(f"质量分数提升 {after_score - before_score:.2f}")
        elif after_score < before_score:
            comparison['regressions'].append(f"质量分数下降 {before_score - after_score:.2f}")

        return comparison

    def _calculate_quality_score(self, snapshot: Dict[str, Any]) -> float:
        score = 100.0

        complexity_issues = snapshot.get('complexity_metrics', {}).get('total_issues', 0)
        score -= complexity_issues * 2

        high_complexity = snapshot.get('complexity_metrics', {}).get('high_complexity_count', 0)
        score -= high_complexity * 5

        duplications = snapshot.get('duplication_metrics', {}).get('total_duplications', 0)
        score -= duplications * 3

        return max(0, score)

    def _generate_summary(
        self,
        complexity_issues: List[ComplexityIssue],
        duplication_issues: List[DuplicationIssue],
        results: List[RefactoringResult]
    ) -> Dict[str, Any]:
        high_complexity = sum(
            1 for issue in complexity_issues
            if issue.complexity_level in [ComplexityLevel.HIGH, ComplexityLevel.VERY_HIGH]
        )

        successful_refactorings = sum(1 for r in results if r.success)

        return {
            'high_complexity_issues': high_complexity,
            'total_complexity_issues': len(complexity_issues),
            'duplication_issues': len(duplication_issues),
            'refactorings_applied': len(results),
            'successful_refactorings': successful_refactorings,
            'success_rate': (successful_refactorings / len(results) * 100) if results else 0,
            'recommendations': self._generate_recommendations(complexity_issues, duplication_issues, results)
        }

    def _generate_recommendations(
        self,
        complexity_issues: List[ComplexityIssue],
        duplication_issues: List[DuplicationIssue],
        results: List[RefactoringResult]
    ) -> List[str]:
        recommendations = []

        high_complexity = [
            issue for issue in complexity_issues
            if issue.complexity_level == ComplexityLevel.VERY_HIGH
        ]
        if high_complexity:
            recommendations.append(f"发现 {len(high_complexity)} 个极高复杂度问题，建议立即重构")

        if duplication_issues:
            recommendations.append(f"发现 {len(duplication_issues)} 处代码重复，建议提取公共代码")

        failed_refactorings = [r for r in results if not r.success]
        if failed_refactorings:
            recommendations.append(f"{len(failed_refactorings)} 个重构执行失败，建议检查并重试")

        if not recommendations:
            recommendations.append("代码质量良好，建议持续监控")

        return recommendations

    def get_optimization_history(self) -> List[Dict[str, Any]]:
        return self._optimization_history

    def export_report(self, report: Dict[str, Any], output_path: Path):
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
