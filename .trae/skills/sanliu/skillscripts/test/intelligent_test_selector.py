#!/usr/bin/env python3
"""
智能测试选择器 - Sanliu 技能

基于代码变更分析，智能选择需要执行的测试用例，支持：
1. 变更影响分析 - 分析代码变更对测试的影响范围
2. 测试智能选择 - 根据变更内容选择相关测试
3. 测试执行顺序优化 - 基于依赖关系和优先级排序
4. 增量测试支持 - 只运行受变更影响的测试

增强功能：
- 智能选择策略（精确/宽松/保守模式）
- 函数调用链分析与数据流分析
- 基于历史数据的优先级排序
- 并行执行优化与失败快速反馈

使用示例:
    python intelligent_test_selector.py --base main --head feature-branch
    python intelligent_test_selector.py --changed-files file1.py,file2.py
    python intelligent_test_selector.py --incremental --cache .test_cache.json
"""

import argparse
import ast
import hashlib
import json
import logging
import os
import re
import subprocess
import sys
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Callable


class ChangeType(Enum):
    ADDED = "added"
    MODIFIED = "modified"
    DELETED = "deleted"
    RENAMED = "renamed"


class TestPriority(Enum):
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


class ImpactLevel(Enum):
    DIRECT = "direct"
    INDIRECT = "indirect"
    TRANSITIVE = "transitive"
    NONE = "none"


class SelectionStrategy(Enum):
    PRECISE = "precise"
    BALANCED = "balanced"
    CONSERVATIVE = "conservative"


class SelectionMode(Enum):
    FULL = "full"
    INCREMENTAL = "incremental"
    IMPACT_ONLY = "impact_only"
    PRIORITY_BASED = "priority_based"


@dataclass
class CodeChange:
    file_path: str
    change_type: ChangeType
    old_content: Optional[str] = None
    new_content: Optional[str] = None
    diff_hunks: List[Dict[str, Any]] = field(default_factory=list)
    changed_symbols: Set[str] = field(default_factory=set)
    line_ranges: List[Tuple[int, int]] = field(default_factory=list)
    complexity_delta: float = 0.0
    risk_score: float = 0.0


@dataclass
class TestInfo:
    test_id: str
    test_name: str
    test_file: str
    test_type: str
    dependencies: Set[str] = field(default_factory=set)
    covered_files: Set[str] = field(default_factory=set)
    covered_symbols: Set[str] = field(default_factory=set)
    execution_time: float = 0.0
    last_run_time: Optional[datetime] = None
    last_result: Optional[str] = None
    priority: TestPriority = TestPriority.MEDIUM
    historical_failure_rate: float = 0.0
    business_importance: float = 0.5
    code_complexity: float = 0.5
    change_frequency: float = 0.5
    weight: float = 0.0


@dataclass
class ImpactAnalysis:
    changed_files: List[str]
    affected_tests: Dict[str, ImpactLevel]
    dependency_chain: Dict[str, List[str]]
    risk_assessment: Dict[str, float]
    recommendations: List[str]
    call_chain_analysis: Dict[str, List[str]]
    data_flow_impact: Dict[str, Set[str]]
    config_impact: List[str]


@dataclass
class TestSelectionResult:
    selected_tests: List[TestInfo]
    skipped_tests: List[TestInfo]
    execution_order: List[str]
    estimated_time: float
    coverage_impact: Dict[str, float]
    selection_reason: Dict[str, str]
    parallel_groups: List[List[str]]
    priority_scores: Dict[str, float]


@dataclass
class SelectionConfig:
    strategy: SelectionStrategy = SelectionStrategy.BALANCED
    mode: SelectionMode = SelectionMode.FULL
    max_tests: int = 1000
    min_priority: TestPriority = TestPriority.LOW
    include_indirect: bool = True
    include_transitive: bool = False
    weight_factors: Dict[str, float] = field(default_factory=lambda: {
        "failure_rate": 0.25,
        "business_importance": 0.20,
        "code_complexity": 0.15,
        "change_frequency": 0.15,
        "impact_level": 0.15,
        "execution_time": 0.10
    })


class CodeChangeAnalyzer:
    """代码变更分析器 - 分析代码变更的详细信息和风险"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self._file_cache: Dict[str, str] = {}

    def analyze_git_diff(self, base: str, head: str, repo_path: Path) -> List[CodeChange]:
        """分析Git差异，提取变更详情"""
        self.logger.info(f"分析Git差异: {base}...{head}")
        changes = []

        try:
            result = subprocess.run(
                ["git", "diff", "--name-status", f"{base}...{head}"],
                capture_output=True,
                text=True,
                cwd=repo_path
            )

            if result.returncode != 0:
                self.logger.error(f"Git diff失败: {result.stderr}")
                return changes

            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue

                parts = line.split("\t")
                if len(parts) < 2:
                    continue

                status = parts[0]
                file_path = parts[1]

                if not file_path.endswith(".py"):
                    continue

                change_type = self._parse_change_type(status)
                change = CodeChange(
                    file_path=file_path,
                    change_type=change_type
                )

                if change_type != ChangeType.DELETED:
                    change.new_content = self._get_file_content(repo_path / file_path, head)
                    change.old_content = self._get_file_content(repo_path / file_path, base)

                if change.new_content or change.old_content:
                    self._extract_changed_symbols(change)
                    self._calculate_complexity_delta(change)
                    self._calculate_risk_score(change)

                changes.append(change)

        except Exception as e:
            self.logger.error(f"分析Git差异失败: {e}")

        return changes

    def analyze_changed_files(self, changed_files: List[str], repo_path: Path) -> List[CodeChange]:
        """分析指定的变更文件列表"""
        self.logger.info(f"分析变更文件: {changed_files}")
        changes = []

        for file_path in changed_files:
            full_path = repo_path / file_path
            if not full_path.exists():
                continue

            change = CodeChange(
                file_path=file_path,
                change_type=ChangeType.MODIFIED,
                new_content=self._read_file(full_path)
            )

            self._extract_all_symbols(change)
            self._calculate_complexity_delta(change)
            self._calculate_risk_score(change)
            changes.append(change)

        return changes

    def _parse_change_type(self, status: str) -> ChangeType:
        """解析Git状态码为变更类型"""
        status_map = {
            "A": ChangeType.ADDED,
            "M": ChangeType.MODIFIED,
            "D": ChangeType.DELETED,
            "R": ChangeType.RENAMED,
        }
        return status_map.get(status[0], ChangeType.MODIFIED)

    def _get_file_content(self, file_path: Path, ref: str) -> Optional[str]:
        """获取指定Git版本的文件内容"""
        cache_key = f"{ref}:{file_path}"
        if cache_key in self._file_cache:
            return self._file_cache[cache_key]

        try:
            result = subprocess.run(
                ["git", "show", f"{ref}:{file_path}"],
                capture_output=True,
                text=True,
                cwd=file_path.parent
            )

            if result.returncode == 0:
                self._file_cache[cache_key] = result.stdout
                return result.stdout
        except Exception:
            pass

        return None

    def _read_file(self, file_path: Path) -> Optional[str]:
        """读取文件内容"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            return None

    def _extract_changed_symbols(self, change: CodeChange) -> None:
        """提取变更的符号（函数、类等）"""
        old_symbols = self._get_symbols_from_content(change.old_content)
        new_symbols = self._get_symbols_from_content(change.new_content)

        change.changed_symbols = new_symbols.symmetric_difference(old_symbols)

        for symbol in new_symbols:
            if symbol in old_symbols:
                if self._symbol_content_changed(symbol, change.old_content, change.new_content):
                    change.changed_symbols.add(symbol)

    def _extract_all_symbols(self, change: CodeChange) -> None:
        """提取文件中的所有符号"""
        change.changed_symbols = self._get_symbols_from_content(change.new_content)

    def _get_symbols_from_content(self, content: Optional[str]) -> Set[str]:
        """从代码内容中提取符号定义"""
        if not content:
            return set()

        symbols = set()
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                    symbols.add(node.name)
                elif isinstance(node, ast.ClassDef):
                    symbols.add(node.name)
        except SyntaxError:
            pass

        return symbols

    def _symbol_content_changed(self, symbol: str, old_content: Optional[str], new_content: Optional[str]) -> bool:
        """检查符号的具体实现是否发生变更"""
        old_symbol = self._extract_symbol_def(symbol, old_content)
        new_symbol = self._extract_symbol_def(symbol, new_content)
        return old_symbol != new_symbol

    def _extract_symbol_def(self, symbol: str, content: Optional[str]) -> Optional[str]:
        """提取符号的完整定义代码"""
        if not content:
            return None

        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
                    if node.name == symbol:
                        return ast.unparse(node)
        except SyntaxError:
            pass

        return None

    def _calculate_complexity_delta(self, change: CodeChange) -> None:
        """计算代码复杂度变化量"""
        old_complexity = self._calculate_complexity(change.old_content)
        new_complexity = self._calculate_complexity(change.new_content)
        change.complexity_delta = new_complexity - old_complexity

    def _calculate_complexity(self, content: Optional[str]) -> float:
        """计算代码复杂度（基于圈复杂度）"""
        if not content:
            return 0.0

        complexity = 1.0
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.If | ast.While | ast.For | ast.ExceptHandler):
                    complexity += 1
                elif isinstance(node, ast.BoolOp):
                    complexity += len(node.values) - 1
                elif isinstance(node, ast.comprehension):
                    complexity += 1
                    if node.ifs:
                        complexity += len(node.ifs)
        except SyntaxError:
            pass

        return complexity

    def _calculate_risk_score(self, change: CodeChange) -> None:
        """计算变更风险分数"""
        risk = 0.0

        if change.change_type == ChangeType.DELETED:
            risk += 0.3
        elif change.change_type == ChangeType.ADDED:
            risk += 0.2
        elif change.change_type == ChangeType.RENAMED:
            risk += 0.15

        if change.complexity_delta > 10:
            risk += 0.2
        elif change.complexity_delta > 5:
            risk += 0.1

        if len(change.changed_symbols) > 5:
            risk += 0.2
        elif len(change.changed_symbols) > 2:
            risk += 0.1

        change.risk_score = min(risk, 1.0)


class DependencyGraphBuilder:
    """依赖关系图构建器 - 构建代码间的依赖关系"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.import_graph: Dict[str, Set[str]] = defaultdict(set)
        self.reverse_graph: Dict[str, Set[str]] = defaultdict(set)
        self.symbol_to_file: Dict[str, Set[str]] = defaultdict(set)
        self.file_to_symbols: Dict[str, Set[str]] = defaultdict(set)
        self.call_graph: Dict[str, Set[str]] = defaultdict(set)
        self.reverse_call_graph: Dict[str, Set[str]] = defaultdict(set)

    def build(self, project_path: Path) -> Dict[str, Set[str]]:
        """构建完整的依赖关系图"""
        self.logger.info("构建依赖关系图...")

        py_files = list(project_path.rglob("*.py"))

        for py_file in py_files:
            if "__pycache__" in str(py_file) or "test" in py_file.name:
                continue

            self._analyze_file(py_file, project_path)

        return dict(self.import_graph)

    def _analyze_file(self, file_path: Path, root: Path) -> None:
        """分析单个文件的依赖关系"""
        try:
            rel_path = str(file_path.relative_to(root))
            content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self.import_graph[rel_path].add(alias.name)
                        self.reverse_graph[alias.name].add(rel_path)

                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        self.import_graph[rel_path].add(node.module)
                        self.reverse_graph[node.module].add(rel_path)

                elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                    symbol = f"{rel_path}::{node.name}"
                    self.symbol_to_file[node.name].add(rel_path)
                    self.file_to_symbols[rel_path].add(node.name)
                    self._analyze_function_calls(node, symbol)

                elif isinstance(node, ast.ClassDef):
                    symbol = f"{rel_path}::{node.name}"
                    self.symbol_to_file[node.name].add(rel_path)
                    self.file_to_symbols[rel_path].add(node.name)

        except Exception as e:
            self.logger.warning(f"分析文件失败 {file_path}: {e}")

    def _analyze_function_calls(self, node: ast.FunctionDef | ast.AsyncFunctionDef, caller_symbol: str) -> None:
        """分析函数内部的调用关系"""
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                called_name = self._get_call_name(child)
                if called_name:
                    self.call_graph[caller_symbol].add(called_name)
                    self.reverse_call_graph[called_name].add(caller_symbol)

    def _get_call_name(self, node: ast.Call) -> Optional[str]:
        """获取调用表达式的名称"""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            return node.func.attr
        return None

    def get_dependents(self, file_path: str) -> Set[str]:
        """获取依赖于指定文件的所有文件"""
        return self.reverse_graph.get(file_path, set())

    def get_dependencies(self, file_path: str) -> Set[str]:
        """获取指定文件依赖的所有文件"""
        return self.import_graph.get(file_path, set())

    def get_transitive_dependents(self, file_path: str, max_depth: int = 5) -> Set[str]:
        """获取传递依赖（间接依赖）"""
        result = set()
        queue = deque([(file_path, 0)])

        while queue:
            current, depth = queue.popleft()

            if depth >= max_depth:
                continue

            for dep in self.reverse_graph.get(current, set()):
                if dep not in result:
                    result.add(dep)
                    queue.append((dep, depth + 1))

        return result

    def get_call_chain(self, symbol: str, max_depth: int = 10) -> List[str]:
        """获取函数调用链"""
        chain = [symbol]
        visited = {symbol}
        current = symbol

        for _ in range(max_depth):
            callers = self.reverse_call_graph.get(current, set())
            if not callers:
                break

            next_caller = None
            for caller in callers:
                if caller not in visited:
                    next_caller = caller
                    break

            if not next_caller:
                break

            chain.append(next_caller)
            visited.add(next_caller)
            current = next_caller

        return chain


class TestDiscovery:
    """测试发现器 - 发现并解析测试用例"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.tests: Dict[str, TestInfo] = {}

    def discover(self, test_path: Path) -> Dict[str, TestInfo]:
        """发现测试用例"""
        self.logger.info(f"发现测试用例: {test_path}")

        if test_path.is_file():
            self._discover_in_file(test_path)
        else:
            for py_file in test_path.rglob("test_*.py"):
                self._discover_in_file(py_file)
            for py_file in test_path.rglob("*_test.py"):
                self._discover_in_file(py_file)

        return self.tests

    def _discover_in_file(self, file_path: Path) -> None:
        """在文件中发现测试"""
        try:
            content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    if node.name.startswith("Test"):
                        for item in node.body:
                            if isinstance(item, ast.FunctionDef) and item.name.startswith("test_"):
                                self._add_test(item, file_path, "class", content)

                elif isinstance(node, ast.FunctionDef):
                    if node.name.startswith("test_"):
                        self._add_test(node, file_path, "function", content)

        except Exception as e:
            self.logger.warning(f"发现测试失败 {file_path}: {e}")

    def _add_test(self, node: ast.FunctionDef, file_path: Path, test_type: str, content: str) -> None:
        """添加测试信息"""
        test_id = f"{file_path}::{node.name}"
        test_info = TestInfo(
            test_id=test_id,
            test_name=node.name,
            test_file=str(file_path),
            test_type=test_type,
            covered_files=self._extract_covered_files(node),
            covered_symbols=self._extract_covered_symbols(node),
            priority=self._determine_priority(node),
            historical_failure_rate=self._estimate_failure_rate(node),
            business_importance=self._estimate_business_importance(node),
            code_complexity=self._calculate_test_complexity(node),
            change_frequency=self._estimate_change_frequency(node, content)
        )

        test_info.weight = self._calculate_weight(test_info)
        self.tests[test_id] = test_info

    def _extract_covered_files(self, node: ast.FunctionDef) -> Set[str]:
        """提取测试覆盖的文件"""
        covered = set()
        for child in ast.walk(node):
            if isinstance(child, ast.Import):
                for alias in child.names:
                    covered.add(alias.name.replace(".", "/") + ".py")
            elif isinstance(child, ast.ImportFrom):
                if child.module:
                    covered.add(child.module.replace(".", "/") + ".py")
        return covered

    def _extract_covered_symbols(self, node: ast.FunctionDef) -> Set[str]:
        """提取测试覆盖的符号"""
        symbols = set()
        for child in ast.walk(node):
            if isinstance(child, ast.Attribute):
                symbols.add(child.attr)
            elif isinstance(child, ast.Name):
                symbols.add(child.id)
        return symbols

    def _determine_priority(self, node: ast.FunctionDef) -> TestPriority:
        """确定测试优先级"""
        name = node.name.lower()

        if any(kw in name for kw in ["critical", "smoke", "core"]):
            return TestPriority.CRITICAL
        elif any(kw in name for kw in ["important", "main", "key"]):
            return TestPriority.HIGH
        elif any(kw in name for kw in ["edge", "boundary", "error"]):
            return TestPriority.MEDIUM
        else:
            return TestPriority.LOW

    def _estimate_failure_rate(self, node: ast.FunctionDef) -> float:
        """估算历史失败率"""
        name = node.name.lower()

        if any(kw in name for kw in ["flaky", "unstable", "wip"]):
            return 0.3
        elif any(kw in name for kw in ["edge", "boundary", "error", "exception"]):
            return 0.15
        elif any(kw in name for kw in ["integration", "e2e", "end_to_end"]):
            return 0.1
        else:
            return 0.05

    def _estimate_business_importance(self, node: ast.FunctionDef) -> float:
        """估算业务重要性"""
        name = node.name.lower()

        if any(kw in name for kw in ["payment", "checkout", "order", "transaction"]):
            return 0.9
        elif any(kw in name for kw in ["auth", "login", "security", "user"]):
            return 0.8
        elif any(kw in name for kw in ["api", "endpoint", "service"]):
            return 0.7
        elif any(kw in name for kw in ["ui", "view", "display"]):
            return 0.5
        else:
            return 0.4

    def _calculate_test_complexity(self, node: ast.FunctionDef) -> float:
        """计算测试复杂度"""
        complexity = 1.0

        for child in ast.walk(node):
            if isinstance(child, ast.If | ast.While | ast.For):
                complexity += 1
            elif isinstance(child, ast.Assert):
                complexity += 0.5
            elif isinstance(child, ast.Call):
                complexity += 0.1

        return min(complexity / 10.0, 1.0)

    def _estimate_change_frequency(self, node: ast.FunctionDef, content: str) -> float:
        """估算变更频率"""
        lines = content.split("\n")
        test_lines = 0

        for line in lines:
            if node.name in line:
                idx = lines.index(line)
                test_lines = len(lines[idx:idx + 50])
                break

        if test_lines > 100:
            return 0.8
        elif test_lines > 50:
            return 0.5
        else:
            return 0.3

    def _calculate_weight(self, test_info: TestInfo) -> float:
        """计算测试权重"""
        weight = (
            test_info.historical_failure_rate * 0.25 +
            test_info.business_importance * 0.20 +
            test_info.code_complexity * 0.15 +
            test_info.change_frequency * 0.15 +
            (1.0 - test_info.priority.value / 4.0) * 0.15 +
            (1.0 - min(test_info.execution_time / 60.0, 1.0)) * 0.10
        )
        return min(weight, 1.0)


class ImpactAnalyzer:
    """变更影响分析器 - 分析代码变更对测试的影响"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.dep_graph: Optional[DependencyGraphBuilder] = None

    def analyze(
        self,
        changes: List[CodeChange],
        tests: Dict[str, TestInfo],
        dep_graph: DependencyGraphBuilder
    ) -> ImpactAnalysis:
        """分析变更影响"""
        self.logger.info("分析变更影响...")
        self.dep_graph = dep_graph

        changed_files = [c.file_path for c in changes]
        changed_symbols = set()
        for c in changes:
            changed_symbols.update(c.changed_symbols)

        affected_tests: Dict[str, ImpactLevel] = {}
        dependency_chain: Dict[str, List[str]] = {}
        call_chain_analysis: Dict[str, List[str]] = {}
        data_flow_impact: Dict[str, Set[str]] = {}

        for test_id, test_info in tests.items():
            impact = self._calculate_impact(
                test_info,
                changed_files,
                changed_symbols,
                dep_graph
            )

            if impact != ImpactLevel.NONE:
                affected_tests[test_id] = impact
                dependency_chain[test_id] = self._build_dependency_chain(
                    test_info,
                    changed_files,
                    dep_graph
                )
                call_chain_analysis[test_id] = self._analyze_call_chain(
                    test_info,
                    changed_symbols,
                    dep_graph
                )
                data_flow_impact[test_id] = self._analyze_data_flow(
                    test_info,
                    changes
                )

        risk_assessment = self._assess_risk(affected_tests, tests, changes)
        recommendations = self._generate_recommendations(affected_tests, changes)
        config_impact = self._analyze_config_impact(changes)

        return ImpactAnalysis(
            changed_files=changed_files,
            affected_tests=affected_tests,
            dependency_chain=dependency_chain,
            risk_assessment=risk_assessment,
            recommendations=recommendations,
            call_chain_analysis=call_chain_analysis,
            data_flow_impact=data_flow_impact,
            config_impact=config_impact
        )

    def _calculate_impact(
        self,
        test_info: TestInfo,
        changed_files: List[str],
        changed_symbols: Set[str],
        dep_graph: DependencyGraphBuilder
    ) -> ImpactLevel:
        """计算影响级别"""
        for changed_file in changed_files:
            if changed_file in test_info.covered_files:
                return ImpactLevel.DIRECT

            if changed_file in test_info.test_file:
                return ImpactLevel.DIRECT

        for symbol in changed_symbols:
            if symbol in test_info.covered_symbols:
                return ImpactLevel.DIRECT

        for changed_file in changed_files:
            transitive = dep_graph.get_transitive_dependents(changed_file)
            if test_info.test_file in transitive:
                return ImpactLevel.INDIRECT

        return ImpactLevel.NONE

    def _build_dependency_chain(
        self,
        test_info: TestInfo,
        changed_files: List[str],
        dep_graph: DependencyGraphBuilder
    ) -> List[str]:
        """构建依赖链"""
        chain = []

        for changed_file in changed_files:
            if changed_file in test_info.covered_files:
                chain.append(f"直接依赖: {changed_file}")

            transitive = dep_graph.get_transitive_dependents(changed_file, max_depth=3)
            if test_info.test_file in transitive:
                chain.append(f"间接依赖: {changed_file}")

        return chain

    def _analyze_call_chain(
        self,
        test_info: TestInfo,
        changed_symbols: Set[str],
        dep_graph: DependencyGraphBuilder
    ) -> List[str]:
        """分析函数调用链"""
        chains = []

        for symbol in changed_symbols:
            if symbol in test_info.covered_symbols:
                call_chain = dep_graph.get_call_chain(symbol)
                if len(call_chain) > 1:
                    chains.append(" -> ".join(call_chain[:5]))

        return chains

    def _analyze_data_flow(
        self,
        test_info: TestInfo,
        changes: List[CodeChange]
    ) -> Set[str]:
        """分析数据流影响"""
        affected_data = set()

        for change in changes:
            if not change.new_content:
                continue

            try:
                tree = ast.parse(change.new_content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Assign):
                        for target in node.targets:
                            if isinstance(target, ast.Name):
                                if target.id in test_info.covered_symbols:
                                    affected_data.add(target.id)
            except SyntaxError:
                pass

        return affected_data

    def _analyze_config_impact(self, changes: List[CodeChange]) -> List[str]:
        """分析配置变更影响"""
        config_files = []
        config_patterns = [
            r".*\.yaml$", r".*\.yml$", r".*\.json$",
            r".*\.toml$", r".*\.ini$", r".*\.env$",
            r".*config.*", r".*settings.*"
        ]

        for change in changes:
            for pattern in config_patterns:
                if re.match(pattern, change.file_path, re.IGNORECASE):
                    config_files.append(change.file_path)
                    break

        return config_files

    def _assess_risk(
        self,
        affected_tests: Dict[str, ImpactLevel],
        all_tests: Dict[str, TestInfo],
        changes: List[CodeChange]
    ) -> Dict[str, float]:
        """评估风险"""
        risk = {}

        base_change_risk = sum(c.risk_score for c in changes) / max(len(changes), 1)

        for test_id, impact in affected_tests.items():
            test_info = all_tests.get(test_id)
            if not test_info:
                continue

            base_risk = {
                ImpactLevel.DIRECT: 0.9,
                ImpactLevel.INDIRECT: 0.6,
                ImpactLevel.TRANSITIVE: 0.3,
                ImpactLevel.NONE: 0.0
            }.get(impact, 0.0)

            priority_factor = {
                TestPriority.CRITICAL: 1.2,
                TestPriority.HIGH: 1.1,
                TestPriority.MEDIUM: 1.0,
                TestPriority.LOW: 0.9
            }.get(test_info.priority, 1.0)

            failure_factor = 1.0 + test_info.historical_failure_rate * 0.5

            risk[test_id] = min(base_risk * priority_factor * failure_factor * (1 + base_change_risk * 0.2), 1.0)

        return risk

    def _generate_recommendations(
        self,
        affected_tests: Dict[str, ImpactLevel],
        changes: List[CodeChange]
    ) -> List[str]:
        """生成建议"""
        recommendations = []

        direct_count = sum(1 for i in affected_tests.values() if i == ImpactLevel.DIRECT)
        indirect_count = sum(1 for i in affected_tests.values() if i == ImpactLevel.INDIRECT)

        if direct_count > 0:
            recommendations.append(f"发现 {direct_count} 个直接受影响的测试，建议优先执行")

        if indirect_count > 10:
            recommendations.append(f"间接影响测试数量较多 ({indirect_count})，建议评估测试范围")

        deleted_files = [c for c in changes if c.change_type == ChangeType.DELETED]
        if deleted_files:
            recommendations.append(f"存在 {len(deleted_files)} 个删除文件，需检查相关测试是否需要更新")

        high_risk_changes = [c for c in changes if c.risk_score > 0.5]
        if high_risk_changes:
            recommendations.append(f"发现 {len(high_risk_changes)} 个高风险变更，建议增加回归测试")

        return recommendations


class TestPriorityCalculator:
    """测试优先级计算器 - 基于多维度因素计算测试优先级"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def calculate_priorities(
        self,
        tests: List[TestInfo],
        impact_analysis: ImpactAnalysis,
        config: SelectionConfig
    ) -> Dict[str, float]:
        """计算所有测试的优先级分数"""
        priorities = {}

        for test in tests:
            score = self._calculate_single_priority(test, impact_analysis, config)
            priorities[test.test_id] = score

        return priorities

    def _calculate_single_priority(
        self,
        test: TestInfo,
        impact_analysis: ImpactAnalysis,
        config: SelectionConfig
    ) -> float:
        """计算单个测试的优先级分数"""
        factors = config.weight_factors

        impact_level = impact_analysis.affected_tests.get(test.test_id, ImpactLevel.NONE)
        impact_score = {
            ImpactLevel.DIRECT: 1.0,
            ImpactLevel.INDIRECT: 0.7,
            ImpactLevel.TRANSITIVE: 0.4,
            ImpactLevel.NONE: 0.1
        }.get(impact_level, 0.0)

        risk_score = impact_analysis.risk_assessment.get(test.test_id, 0.0)

        priority_score = (
            test.historical_failure_rate * factors.get("failure_rate", 0.25) +
            test.business_importance * factors.get("business_importance", 0.20) +
            test.code_complexity * factors.get("code_complexity", 0.15) +
            test.change_frequency * factors.get("change_frequency", 0.15) +
            impact_score * factors.get("impact_level", 0.15) +
            (1.0 - min(test.execution_time / 60.0, 1.0)) * factors.get("execution_time", 0.10) +
            risk_score * 0.1
        )

        return min(priority_score, 1.0)

    def sort_by_priority(
        self,
        tests: List[TestInfo],
        priorities: Dict[str, float]
    ) -> List[TestInfo]:
        """按优先级排序测试"""
        return sorted(tests, key=lambda t: priorities.get(t.test_id, 0.0), reverse=True)


class TestOrderOptimizer:
    """测试执行顺序优化器 - 优化测试执行顺序以提高效率"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def optimize(
        self,
        tests: List[TestInfo],
        dependency_graph: Dict[str, Set[str]],
        priorities: Dict[str, float]
    ) -> Tuple[List[str], List[List[str]]]:
        """优化测试执行顺序，返回顺序列表和并行分组"""
        self.logger.info("优化测试执行顺序...")

        sorted_tests = sorted(tests, key=lambda t: (
            -priorities.get(t.test_id, 0.0),
            t.priority.value,
            -t.execution_time if t.execution_time else 0
        ))

        ordered = []
        remaining = {t.test_id for t in sorted_tests}
        test_map = {t.test_id: t for t in sorted_tests}

        for test in sorted_tests:
            if test.test_id not in remaining:
                continue

            self._add_with_dependencies(test, ordered, remaining, test_map, dependency_graph)

        parallel_groups = self._create_parallel_groups(ordered, tests, dependency_graph)

        return ordered, parallel_groups

    def _add_with_dependencies(
        self,
        test: TestInfo,
        ordered: List[str],
        remaining: Set[str],
        test_map: Dict[str, TestInfo],
        dep_graph: Dict[str, Set[str]]
    ) -> None:
        """添加测试及其依赖到执行列表"""
        for dep in test.dependencies:
            if dep in remaining and dep in test_map:
                self._add_with_dependencies(test_map[dep], ordered, remaining, test_map, dep_graph)

        if test.test_id in remaining:
            ordered.append(test.test_id)
            remaining.remove(test.test_id)

    def _create_parallel_groups(
        self,
        ordered: List[str],
        tests: List[TestInfo],
        dependency_graph: Dict[str, Set[str]]
    ) -> List[List[str]]:
        """创建可并行执行的测试分组"""
        test_map = {t.test_id: t for t in tests}
        groups = []
        current_group = []
        used_resources = set()

        for test_id in ordered:
            test = test_map.get(test_id)
            if not test:
                continue

            test_resources = self._get_test_resources(test)

            if test_resources & used_resources:
                if current_group:
                    groups.append(current_group)
                current_group = [test_id]
                used_resources = test_resources
            else:
                current_group.append(test_id)
                used_resources |= test_resources

        if current_group:
            groups.append(current_group)

        return groups

    def _get_test_resources(self, test: TestInfo) -> Set[str]:
        """获取测试所需的资源"""
        resources = set()

        resources.add(test.test_file)

        for covered_file in test.covered_files:
            resources.add(covered_file)

        if "database" in test.test_name.lower():
            resources.add("database")
        if "api" in test.test_name.lower():
            resources.add("api")
        if "file" in test.test_name.lower():
            resources.add("filesystem")

        return resources

    def optimize_for_fast_feedback(
        self,
        tests: List[TestInfo],
        priorities: Dict[str, float],
        max_time: float = 300.0
    ) -> List[str]:
        """优化测试顺序以实现快速反馈（优先执行快速且重要的测试）"""
        scored_tests = []

        for test in tests:
            time = test.execution_time if test.execution_time else 10.0
            priority = priorities.get(test.test_id, 0.5)
            score = priority / max(time, 1.0)
            scored_tests.append((test.test_id, score, time))

        scored_tests.sort(key=lambda x: -x[1])

        selected = []
        total_time = 0.0

        for test_id, score, time in scored_tests:
            if total_time + time <= max_time:
                selected.append(test_id)
                total_time += time

        return selected


class IntelligentTestSelector:
    """智能测试选择器主类 - 整合所有功能"""

    def __init__(self, project_path: Path, logger: Optional[logging.Logger] = None):
        self.project_path = project_path
        self.logger = logger or self._setup_logger()

        self.change_analyzer = CodeChangeAnalyzer(self.logger)
        self.dep_builder = DependencyGraphBuilder(self.logger)
        self.test_discovery = TestDiscovery(self.logger)
        self.impact_analyzer = ImpactAnalyzer(self.logger)
        self.priority_calculator = TestPriorityCalculator(self.logger)
        self.order_optimizer = TestOrderOptimizer(self.logger)

        self._dep_graph: Optional[DependencyGraphBuilder] = None
        self._tests: Dict[str, TestInfo] = {}
        self._cache: Optional[IncrementalTestCache] = None

    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger("IntelligentTestSelector")
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setLevel(logging.INFO)
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def select(
        self,
        changes: Optional[List[CodeChange]] = None,
        base: Optional[str] = None,
        head: Optional[str] = None,
        changed_files: Optional[List[str]] = None,
        test_path: Optional[Path] = None,
        incremental: bool = False,
        cache_path: Optional[Path] = None,
        config: Optional[SelectionConfig] = None
    ) -> TestSelectionResult:
        """执行智能测试选择"""
        self.logger.info("开始智能测试选择...")

        config = config or SelectionConfig()

        self._dep_graph = self.dep_builder
        self._dep_graph.build(self.project_path)

        test_dir = test_path or self.project_path / "tests"
        self._tests = self.test_discovery.discover(test_dir)

        if changes is None:
            if base and head:
                changes = self.change_analyzer.analyze_git_diff(base, head, self.project_path)
            elif changed_files:
                changes = self.change_analyzer.analyze_changed_files(changed_files, self.project_path)
            else:
                changes = []

        if incremental and cache_path:
            self._cache = IncrementalTestCache(cache_path, self.logger)
            changes = self._filter_by_cache(changes)

        impact = self.impact_analyzer.analyze(
            changes,
            self._tests,
            self._dep_graph
        )

        selected_tests = []
        skipped_tests = []
        selection_reason = {}

        selected_tests, skipped_tests, selection_reason = self._apply_selection_strategy(
            impact, config
        )

        priorities = self.priority_calculator.calculate_priorities(
            selected_tests, impact, config
        )

        execution_order, parallel_groups = self.order_optimizer.optimize(
            selected_tests,
            dict(self._dep_graph.import_graph),
            priorities
        )

        estimated_time = sum(t.execution_time for t in selected_tests if t.execution_time)

        coverage_impact = self._calculate_coverage_impact(selected_tests, changes)

        return TestSelectionResult(
            selected_tests=selected_tests,
            skipped_tests=skipped_tests,
            execution_order=execution_order,
            estimated_time=estimated_time,
            coverage_impact=coverage_impact,
            selection_reason=selection_reason,
            parallel_groups=parallel_groups,
            priority_scores=priorities
        )

    def _apply_selection_strategy(
        self,
        impact: ImpactAnalysis,
        config: SelectionConfig
    ) -> Tuple[List[TestInfo], List[TestInfo], Dict[str, str]]:
        """应用选择策略"""
        selected = []
        skipped = []
        reasons = {}

        for test_id, test_info in self._tests.items():
            impact_level = impact.affected_tests.get(test_id, ImpactLevel.NONE)

            should_select, reason = self._should_select_test(
                test_id, impact_level, test_info, config, impact
            )

            if should_select:
                selected.append(test_info)
                reasons[test_id] = reason
            else:
                skipped.append(test_info)

        return selected, skipped, reasons

    def _should_select_test(
        self,
        test_id: str,
        impact_level: ImpactLevel,
        test_info: TestInfo,
        config: SelectionConfig,
        impact: ImpactAnalysis
    ) -> Tuple[bool, str]:
        """判断是否应该选择该测试"""
        if config.strategy == SelectionStrategy.PRECISE:
            if impact_level == ImpactLevel.DIRECT:
                return True, "直接受变更影响"
            return False, "未受直接影响"

        elif config.strategy == SelectionStrategy.BALANCED:
            if impact_level == ImpactLevel.DIRECT:
                return True, "直接受变更影响"
            elif impact_level == ImpactLevel.INDIRECT and config.include_indirect:
                return True, "间接受变更影响"
            elif test_info.priority == TestPriority.CRITICAL:
                return True, "关键测试（始终执行）"
            return False, "未受影响"

        elif config.strategy == SelectionStrategy.CONSERVATIVE:
            if impact_level != ImpactLevel.NONE:
                return True, f"受变更影响 ({impact_level.value})"
            elif test_info.priority in [TestPriority.CRITICAL, TestPriority.HIGH]:
                return True, f"高优先级测试 ({test_info.priority.name})"
            elif test_info.historical_failure_rate > 0.2:
                return True, "历史失败率较高"
            return False, "未受影响且优先级较低"

        return False, "未知策略"

    def _filter_by_cache(self, changes: List[CodeChange]) -> List[CodeChange]:
        """根据缓存过滤变更"""
        if not self._cache:
            return changes

        filtered = []
        for change in changes:
            file_path = self.project_path / change.file_path
            if self._cache.is_file_changed(file_path):
                filtered.append(change)
                self._cache.update_file_hash(file_path)

        self.logger.info(f"缓存过滤: {len(changes)} -> {len(filtered)} 个变更文件")
        return filtered

    def _calculate_coverage_impact(
        self,
        selected_tests: List[TestInfo],
        changes: List[CodeChange]
    ) -> Dict[str, float]:
        """计算覆盖率影响"""
        impact = {}

        for change in changes:
            covered_count = sum(
                1 for t in selected_tests
                if change.file_path in t.covered_files
            )

            total_tests = len(selected_tests)
            if total_tests > 0:
                impact[change.file_path] = covered_count / total_tests
            else:
                impact[change.file_path] = 0.0

        return impact

    def generate_pytest_command(
        self,
        result: TestSelectionResult,
        output_format: str = "standard",
        parallel: bool = False
    ) -> str:
        """生成pytest执行命令"""
        if not result.execution_order:
            return "echo 'No tests selected'"

        cmd_parts = ["pytest"]

        if output_format == "verbose":
            cmd_parts.append("-v")
        elif output_format == "quiet":
            cmd_parts.append("-q")

        if parallel and len(result.execution_order) > 1:
            cmd_parts.extend(["-n", "auto"])

        cmd_parts.extend(result.execution_order)

        return " ".join(cmd_parts)

    def print_report(self, result: TestSelectionResult) -> None:
        """打印选择报告"""
        print("\n" + "=" * 80)
        print("智能测试选择报告")
        print("=" * 80)

        print(f"\n选择统计:")
        print(f"  已选择测试: {len(result.selected_tests)}")
        print(f"  跳过测试: {len(result.skipped_tests)}")
        print(f"  预计执行时间: {result.estimated_time:.2f}秒")

        print(f"\n执行顺序 (前10个):")
        for i, test_id in enumerate(result.execution_order[:10], 1):
            reason = result.selection_reason.get(test_id, "N/A")
            priority = result.priority_scores.get(test_id, 0.0)
            print(f"  {i}. {test_id}")
            print(f"     原因: {reason}")
            print(f"     优先级分数: {priority:.3f}")

        if len(result.execution_order) > 10:
            print(f"  ... 还有 {len(result.execution_order) - 10} 个测试")

        if result.parallel_groups:
            print(f"\n并行执行分组: {len(result.parallel_groups)} 个组")
            for i, group in enumerate(result.parallel_groups[:3], 1):
                print(f"  组 {i}: {len(group)} 个测试")
            if len(result.parallel_groups) > 3:
                print(f"  ... 还有 {len(result.parallel_groups) - 3} 个组")

        print(f"\n覆盖率影响:")
        for file_path, impact in sorted(result.coverage_impact.items(), key=lambda x: -x[1])[:5]:
            print(f"  {file_path}: {impact:.1%}")

    def save_selection(self, result: TestSelectionResult, output_path: Path) -> None:
        """保存选择结果到文件"""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "timestamp": datetime.now().isoformat(),
            "selected_count": len(result.selected_tests),
            "skipped_count": len(result.skipped_tests),
            "estimated_time": result.estimated_time,
            "execution_order": result.execution_order,
            "selection_reason": result.selection_reason,
            "coverage_impact": result.coverage_impact,
            "parallel_groups": result.parallel_groups,
            "priority_scores": result.priority_scores
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        self.logger.info(f"选择结果已保存: {output_path}")


class IncrementalTestCache:
    """增量测试缓存 - 支持增量测试选择"""

    def __init__(self, cache_path: Path, logger: logging.Logger):
        self.cache_path = cache_path
        self.logger = logger
        self._cache: Dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        """加载缓存"""
        if self.cache_path.exists():
            try:
                with open(self.cache_path, "r", encoding="utf-8") as f:
                    self._cache = json.load(f)
                self.logger.info(f"加载测试缓存: {len(self._cache)} 条记录")
            except Exception as e:
                self.logger.warning(f"加载缓存失败: {e}")
                self._cache = {}

    def save(self) -> None:
        """保存缓存"""
        try:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_path, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, indent=2, ensure_ascii=False)
            self.logger.info(f"保存测试缓存: {len(self._cache)} 条记录")
        except Exception as e:
            self.logger.error(f"保存缓存失败: {e}")

    def get_file_hash(self, file_path: Path) -> str:
        """获取文件哈希值"""
        try:
            content = file_path.read_bytes()
            return hashlib.sha256(content).hexdigest()
        except Exception:
            return ""

    def is_file_changed(self, file_path: Path) -> bool:
        """检查文件是否变更"""
        current_hash = self.get_file_hash(file_path)
        cached_hash = self._cache.get("file_hashes", {}).get(str(file_path))

        if cached_hash is None:
            return True

        return current_hash != cached_hash

    def update_file_hash(self, file_path: Path) -> None:
        """更新文件哈希"""
        if "file_hashes" not in self._cache:
            self._cache["file_hashes"] = {}

        self._cache["file_hashes"][str(file_path)] = self.get_file_hash(file_path)

    def get_test_result(self, test_id: str) -> Optional[Dict[str, Any]]:
        """获取测试历史结果"""
        return self._cache.get("test_results", {}).get(test_id)

    def update_test_result(self, test_id: str, result: str, execution_time: float) -> None:
        """更新测试结果"""
        if "test_results" not in self._cache:
            self._cache["test_results"] = {}

        self._cache["test_results"][test_id] = {
            "result": result,
            "execution_time": execution_time,
            "timestamp": datetime.now().isoformat()
        }


def main() -> int:
    """主函数"""
    parser = argparse.ArgumentParser(
        description="智能测试选择器",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--project-path",
        type=str,
        default=".",
        help="项目路径"
    )
    parser.add_argument(
        "--base",
        type=str,
        help="Git基础分支"
    )
    parser.add_argument(
        "--head",
        type=str,
        help="Git目标分支"
    )
    parser.add_argument(
        "--changed-files",
        type=str,
        help="变更文件列表 (逗号分隔)"
    )
    parser.add_argument(
        "--test-path",
        type=str,
        help="测试目录路径"
    )
    parser.add_argument(
        "--incremental",
        action="store_true",
        help="启用增量测试"
    )
    parser.add_argument(
        "--cache",
        type=str,
        default=".test_cache.json",
        help="缓存文件路径"
    )
    parser.add_argument(
        "--strategy",
        type=str,
        choices=["precise", "balanced", "conservative"],
        default="balanced",
        help="选择策略"
    )
    parser.add_argument(
        "--output",
        type=str,
        choices=["console", "json", "pytest"],
        default="console",
        help="输出格式"
    )
    parser.add_argument(
        "--output-file",
        type=str,
        help="输出文件路径"
    )
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="生成并行执行命令"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="详细输出"
    )

    args = parser.parse_args()

    logger = logging.getLogger("IntelligentTestSelector")
    logger.setLevel(logging.DEBUG if args.verbose else logging.INFO)

    project_path = Path(args.project_path).resolve()
    test_path = Path(args.test_path) if args.test_path else None
    cache_path = Path(args.cache) if args.incremental else None

    config = SelectionConfig(
        strategy=SelectionStrategy(args.strategy)
    )

    selector = IntelligentTestSelector(project_path, logger)

    changed_files = None
    if args.changed_files:
        changed_files = [f.strip() for f in args.changed_files.split(",")]

    result = selector.select(
        base=args.base,
        head=args.head,
        changed_files=changed_files,
        test_path=test_path,
        incremental=args.incremental,
        cache_path=cache_path,
        config=config
    )

    if args.output == "console":
        selector.print_report(result)
    elif args.output == "json":
        print(json.dumps({
            "selected_tests": [t.test_id for t in result.selected_tests],
            "skipped_tests": [t.test_id for t in result.skipped_tests],
            "execution_order": result.execution_order,
            "estimated_time": result.estimated_time,
            "parallel_groups": result.parallel_groups,
            "priority_scores": result.priority_scores
        }, indent=2))
    elif args.output == "pytest":
        print(selector.generate_pytest_command(result, parallel=args.parallel))

    if args.output_file:
        selector.save_selection(result, Path(args.output_file))

    if selector._cache:
        selector._cache.save()

    return 0


if __name__ == "__main__":
    sys.exit(main())
