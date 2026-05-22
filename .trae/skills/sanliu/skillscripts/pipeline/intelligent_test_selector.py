#!/usr/bin/env python3
"""
智能测试选择器 - Sanliu 技能流水线版本

基于代码变更分析，智能选择需要执行的测试用例，支持：
1. 变更影响分析 - 分析代码变更对测试的影响范围
2. 测试智能选择 - 根据变更内容选择相关测试
3. 测试执行顺序优化 - 基于依赖关系和优先级排序
4. 增量测试支持 - 只运行受变更影响的测试

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
import subprocess
import sys
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from skillscripts.core.script_base import ScriptBase, ReportFormat, ScriptResult, ScriptStatus


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


class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class CodeChange:
    file_path: str
    change_type: ChangeType
    old_content: Optional[str] = None
    new_content: Optional[str] = None
    diff_hunks: List[Dict[str, Any]] = field(default_factory=list)
    changed_symbols: Set[str] = field(default_factory=set)
    line_ranges: List[Tuple[int, int]] = field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.LOW
    risk_factors: List[str] = field(default_factory=list)


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


@dataclass
class ImpactAnalysis:
    changed_files: List[str]
    affected_tests: Dict[str, ImpactLevel]
    dependency_chain: Dict[str, List[str]]
    risk_assessment: Dict[str, float]
    recommendations: List[str]
    risk_summary: Dict[str, Any]


@dataclass
class TestSelectionResult:
    selected_tests: List[TestInfo]
    skipped_tests: List[TestInfo]
    execution_order: List[str]
    estimated_time: float
    coverage_impact: Dict[str, float]
    selection_reason: Dict[str, str]
    risk_analysis: Dict[str, Any]


class CodeChangeAnalyzer:
    """代码变更分析器"""

    CRITICAL_PATTERNS = [
        r"def\s+__init__",
        r"def\s+__del__",
        r"class\s+\w+\(.*\):",
        r"@abstractmethod",
        r"@property",
        r"async\s+def",
        r"def\s+\w+\s*\([^)]*\)\s*->",
    ]

    HIGH_RISK_PATTERNS = [
        r"def\s+\w+\s*\(",
        r"import\s+",
        r"from\s+\w+\s+import",
        r"raise\s+",
        r"try:",
        r"except\s+",
    ]

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self._file_cache: Dict[str, str] = {}

    def analyze_git_diff(self, base: str, head: str, repo_path: Path) -> List[CodeChange]:
        """分析Git差异"""
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
                    self._analyze_risk(change)

                changes.append(change)

        except Exception as e:
            self.logger.error(f"分析Git差异失败: {e}")

        return changes

    def analyze_changed_files(self, changed_files: List[str], repo_path: Path) -> List[CodeChange]:
        """分析指定的变更文件"""
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
            self._analyze_risk(change)
            changes.append(change)

        return changes

    def _parse_change_type(self, status: str) -> ChangeType:
        """解析变更类型"""
        status_map = {
            "A": ChangeType.ADDED,
            "M": ChangeType.MODIFIED,
            "D": ChangeType.DELETED,
            "R": ChangeType.RENAMED,
        }
        return status_map.get(status[0], ChangeType.MODIFIED)

    def _get_file_content(self, file_path: Path, ref: str) -> Optional[str]:
        """获取指定版本的文件内容"""
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
        """提取变更的符号"""
        old_symbols = self._get_symbols_from_content(change.old_content)
        new_symbols = self._get_symbols_from_content(change.new_content)

        change.changed_symbols = new_symbols.symmetric_difference(old_symbols)

        for symbol in new_symbols:
            if symbol in old_symbols:
                if self._symbol_content_changed(symbol, change.old_content, change.new_content):
                    change.changed_symbols.add(symbol)

    def _extract_all_symbols(self, change: CodeChange) -> None:
        """提取所有符号"""
        change.changed_symbols = self._get_symbols_from_content(change.new_content)

    def _get_symbols_from_content(self, content: Optional[str]) -> Set[str]:
        """从内容中提取符号"""
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
        """检查符号内容是否变更"""
        old_symbol = self._extract_symbol_def(symbol, old_content)
        new_symbol = self._extract_symbol_def(symbol, new_content)
        return old_symbol != new_symbol

    def _extract_symbol_def(self, symbol: str, content: Optional[str]) -> Optional[str]:
        """提取符号定义"""
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

    def _analyze_risk(self, change: CodeChange) -> None:
        """分析变更风险"""
        risk_factors = []
        risk_score = 0

        content = change.new_content or ""
        
        import re
        for pattern in self.CRITICAL_PATTERNS:
            matches = re.findall(pattern, content)
            if matches:
                risk_score += len(matches) * 3
                risk_factors.append(f"关键模式匹配: {pattern}")

        for pattern in self.HIGH_RISK_PATTERNS:
            matches = re.findall(pattern, content)
            if matches:
                risk_score += len(matches)
                risk_factors.append(f"高风险模式匹配: {pattern}")

        if change.change_type == ChangeType.DELETED:
            risk_score += 5
            risk_factors.append("文件删除")
        elif change.change_type == ChangeType.ADDED:
            risk_score += 2
            risk_factors.append("新文件添加")

        if len(change.changed_symbols) > 5:
            risk_score += 3
            risk_factors.append(f"大量符号变更 ({len(change.changed_symbols)} 个)")

        if risk_score >= 10:
            change.risk_level = RiskLevel.CRITICAL
        elif risk_score >= 7:
            change.risk_level = RiskLevel.HIGH
        elif risk_score >= 4:
            change.risk_level = RiskLevel.MEDIUM
        else:
            change.risk_level = RiskLevel.LOW

        change.risk_factors = risk_factors


class DependencyGraphBuilder:
    """依赖关系图构建器"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.import_graph: Dict[str, Set[str]] = defaultdict(set)
        self.reverse_graph: Dict[str, Set[str]] = defaultdict(set)
        self.symbol_to_file: Dict[str, Set[str]] = defaultdict(set)
        self.file_to_symbols: Dict[str, Set[str]] = defaultdict(set)

    def build(self, project_path: Path) -> Dict[str, Set[str]]:
        """构建依赖关系图"""
        self.logger.info("构建依赖关系图...")

        py_files = list(project_path.rglob("*.py"))

        for py_file in py_files:
            if "__pycache__" in str(py_file) or "test" in py_file.name:
                continue

            self._analyze_file(py_file, project_path)

        return dict(self.import_graph)

    def _analyze_file(self, file_path: Path, root: Path) -> None:
        """分析单个文件"""
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

                elif isinstance(node, ast.ClassDef):
                    symbol = f"{rel_path}::{node.name}"
                    self.symbol_to_file[node.name].add(rel_path)
                    self.file_to_symbols[rel_path].add(node.name)

        except Exception as e:
            self.logger.warning(f"分析文件失败 {file_path}: {e}")

    def get_dependents(self, file_path: str) -> Set[str]:
        """获取依赖于指定文件的所有文件"""
        return self.reverse_graph.get(file_path, set())

    def get_dependencies(self, file_path: str) -> Set[str]:
        """获取指定文件依赖的所有文件"""
        return self.import_graph.get(file_path, set())

    def get_transitive_dependents(self, file_path: str, max_depth: int = 5) -> Set[str]:
        """获取传递依赖"""
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


class TestDiscovery:
    """测试发现器"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.tests: Dict[str, TestInfo] = {}
        self._historical_data: Dict[str, Dict[str, Any]] = {}

    def load_historical_data(self, history_path: Path) -> None:
        """加载历史测试数据"""
        if history_path.exists():
            try:
                with open(history_path, "r", encoding="utf-8") as f:
                    self._historical_data = json.load(f)
                self.logger.info(f"加载历史数据: {len(self._historical_data)} 条记录")
            except Exception as e:
                self.logger.warning(f"加载历史数据失败: {e}")

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
                                self._add_test(item, file_path, "class")

                elif isinstance(node, ast.FunctionDef):
                    if node.name.startswith("test_"):
                        self._add_test(node, file_path, "function")

        except Exception as e:
            self.logger.warning(f"发现测试失败 {file_path}: {e}")

    def _add_test(self, node: ast.FunctionDef, file_path: Path, test_type: str) -> None:
        """添加测试信息"""
        test_id = f"{file_path}::{node.name}"
        
        historical_info = self._historical_data.get(test_id, {})
        
        test_info = TestInfo(
            test_id=test_id,
            test_name=node.name,
            test_file=str(file_path),
            test_type=test_type,
            covered_files=self._extract_covered_files(node),
            covered_symbols=self._extract_covered_symbols(node),
            priority=self._determine_priority(node),
            execution_time=historical_info.get("execution_time", 0.0),
            last_result=historical_info.get("last_result"),
            historical_failure_rate=historical_info.get("failure_rate", 0.0)
        )

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


class ImpactAnalyzer:
    """变更影响分析器"""

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

        risk_assessment = self._assess_risk(affected_tests, tests, changes)
        recommendations = self._generate_recommendations(affected_tests, changes)
        risk_summary = self._build_risk_summary(changes, affected_tests)

        return ImpactAnalysis(
            changed_files=changed_files,
            affected_tests=affected_tests,
            dependency_chain=dependency_chain,
            risk_assessment=risk_assessment,
            recommendations=recommendations,
            risk_summary=risk_summary
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

    def _assess_risk(
        self,
        affected_tests: Dict[str, ImpactLevel],
        all_tests: Dict[str, TestInfo],
        changes: List[CodeChange]
    ) -> Dict[str, float]:
        """评估风险"""
        risk = {}

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

            failure_factor = 1.0 + (test_info.historical_failure_rate * 0.5)

            risk[test_id] = min(base_risk * priority_factor * failure_factor, 1.0)

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

        critical_changes = [c for c in changes if c.risk_level == RiskLevel.CRITICAL]
        if critical_changes:
            recommendations.append(f"发现 {len(critical_changes)} 个关键变更，建议进行全面回归测试")

        high_risk_changes = [c for c in changes if c.risk_level == RiskLevel.HIGH]
        if high_risk_changes:
            recommendations.append(f"发现 {len(high_risk_changes)} 个高风险变更，建议增加测试覆盖率")

        return recommendations

    def _build_risk_summary(
        self,
        changes: List[CodeChange],
        affected_tests: Dict[str, ImpactLevel]
    ) -> Dict[str, Any]:
        """构建风险摘要"""
        risk_distribution = {
            RiskLevel.LOW: 0,
            RiskLevel.MEDIUM: 0,
            RiskLevel.HIGH: 0,
            RiskLevel.CRITICAL: 0
        }

        for change in changes:
            risk_distribution[change.risk_level] += 1

        impact_distribution = {
            ImpactLevel.DIRECT: 0,
            ImpactLevel.INDIRECT: 0,
            ImpactLevel.TRANSITIVE: 0
        }

        for impact in affected_tests.values():
            if impact != ImpactLevel.NONE:
                impact_distribution[impact] += 1

        return {
            "change_risk_distribution": {k.value: v for k, v in risk_distribution.items()},
            "impact_distribution": {k.value: v for k, v in impact_distribution.items()},
            "total_high_risk_changes": risk_distribution[RiskLevel.HIGH] + risk_distribution[RiskLevel.CRITICAL],
            "total_affected_tests": len(affected_tests)
        }


class TestOrderOptimizer:
    """测试执行顺序优化器"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def optimize(
        self,
        tests: List[TestInfo],
        dependency_graph: Dict[str, Set[str]],
        risk_assessment: Dict[str, float]
    ) -> List[str]:
        """优化测试执行顺序"""
        self.logger.info("优化测试执行顺序...")

        def sort_key(t: TestInfo) -> Tuple[int, float, float]:
            risk = risk_assessment.get(t.test_id, 0.0)
            return (
                t.priority.value,
                -risk,
                -t.historical_failure_rate
            )

        sorted_tests = sorted(tests, key=sort_key)

        ordered = []
        remaining = {t.test_id for t in sorted_tests}
        test_map = {t.test_id: t for t in sorted_tests}

        for test in sorted_tests:
            if test.test_id not in remaining:
                continue

            self._add_with_dependencies(test, ordered, remaining, test_map, dependency_graph)

        return ordered

    def _add_with_dependencies(
        self,
        test: TestInfo,
        ordered: List[str],
        remaining: Set[str],
        test_map: Dict[str, TestInfo],
        dep_graph: Dict[str, Set[str]]
    ) -> None:
        """添加测试及其依赖"""
        for dep in test.dependencies:
            if dep in remaining and dep in test_map:
                self._add_with_dependencies(test_map[dep], ordered, remaining, test_map, dep_graph)

        if test.test_id in remaining:
            ordered.append(test.test_id)
            remaining.remove(test.test_id)


class IncrementalTestCache:
    """增量测试缓存"""

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
        """获取文件哈希"""
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
        """获取测试结果"""
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


class IntelligentTestSelector(ScriptBase):
    """智能测试选择器主类"""

    def __init__(self):
        super().__init__(
            name="intelligent_test_selector",
            version="2.0.0",
            description="智能测试选择器 - 支持变更影响分析、测试智能选择和执行顺序优化",
            author="Sanliu"
        )
        self._setup_arguments()
        
        self.change_analyzer: Optional[CodeChangeAnalyzer] = None
        self.dep_builder: Optional[DependencyGraphBuilder] = None
        self.test_discovery: Optional[TestDiscovery] = None
        self.impact_analyzer: Optional[ImpactAnalyzer] = None
        self.order_optimizer: Optional[TestOrderOptimizer] = None

        self._dep_graph: Optional[DependencyGraphBuilder] = None
        self._tests: Dict[str, TestInfo] = {}
        self._cache: Optional[IncrementalTestCache] = None

    def _setup_arguments(self) -> None:
        self._command_parser.add_argument(
            "--project-path",
            type=str,
            default=".",
            help="项目路径"
        )
        self._command_parser.add_argument(
            "--base",
            type=str,
            help="Git基础分支"
        )
        self._command_parser.add_argument(
            "--head",
            type=str,
            help="Git目标分支"
        )
        self._command_parser.add_argument(
            "--changed-files",
            type=str,
            help="变更文件列表 (逗号分隔)"
        )
        self._command_parser.add_argument(
            "--test-path",
            type=str,
            help="测试目录路径"
        )
        self._command_parser.add_argument(
            "--incremental",
            action="store_true",
            help="启用增量测试"
        )
        self._command_parser.add_argument(
            "--cache",
            type=str,
            default=".test_cache.json",
            help="缓存文件路径"
        )
        self._command_parser.add_argument(
            "--history",
            type=str,
            help="历史测试数据文件路径"
        )
        self._command_parser.add_argument(
            "--output",
            type=str,
            choices=["console", "json", "pytest"],
            default="console",
            help="输出格式"
        )
        self._command_parser.add_argument(
            "--output-file",
            type=str,
            help="输出文件路径"
        )

    def initialize(self, config: Dict[str, Any]) -> None:
        super().initialize(config)
        
        self.change_analyzer = CodeChangeAnalyzer(self._logger)
        self.dep_builder = DependencyGraphBuilder(self._logger)
        self.test_discovery = TestDiscovery(self._logger)
        self.impact_analyzer = ImpactAnalyzer(self._logger)
        self.order_optimizer = TestOrderOptimizer(self._logger)

    def validate_inputs(self, *args, **kwargs) -> bool:
        project_path = kwargs.get("project_path", ".")
        target_path = Path(project_path)
        if not target_path.exists():
            self._logger.error(f"项目路径不存在: {project_path}")
            return False
        return True

    def run(self, *args, **kwargs) -> Any:
        project_path = Path(kwargs.get("project_path", ".")).resolve()
        base = kwargs.get("base")
        head = kwargs.get("head")
        changed_files_str = kwargs.get("changed_files")
        test_path_str = kwargs.get("test_path")
        incremental = kwargs.get("incremental", False)
        cache_path_str = kwargs.get("cache", ".test_cache.json")
        history_path_str = kwargs.get("history")

        self._logger.info("开始智能测试选择...")

        self._dep_graph = self.dep_builder
        self._dep_graph.build(project_path)

        test_dir = Path(test_path_str) if test_path_str else project_path / "tests"
        self._tests = self.test_discovery.discover(test_dir)

        if history_path_str:
            self.test_discovery.load_historical_data(Path(history_path_str))

        changes: List[CodeChange] = []
        if base and head:
            changes = self.change_analyzer.analyze_git_diff(base, head, project_path)
        elif changed_files_str:
            changed_files = [f.strip() for f in changed_files_str.split(",")]
            changes = self.change_analyzer.analyze_changed_files(changed_files, project_path)

        if incremental:
            cache_path = Path(cache_path_str)
            self._cache = IncrementalTestCache(cache_path, self._logger)
            changes = self._filter_by_cache(changes)

        impact = self.impact_analyzer.analyze(
            changes,
            self._tests,
            self._dep_graph
        )

        selected_tests = []
        skipped_tests = []
        selection_reason = {}

        for test_id, impact_level in impact.affected_tests.items():
            test_info = self._tests.get(test_id)
            if test_info:
                if impact_level != ImpactLevel.NONE:
                    selected_tests.append(test_info)
                    selection_reason[test_id] = f"受变更影响 ({impact_level.value})"
                else:
                    skipped_tests.append(test_info)

        for test_id, test_info in self._tests.items():
            if test_id not in impact.affected_tests:
                skipped_tests.append(test_info)

        execution_order = self.order_optimizer.optimize(
            selected_tests,
            dict(self._dep_graph.import_graph),
            impact.risk_assessment
        )

        estimated_time = sum(t.execution_time for t in selected_tests if t.execution_time)

        coverage_impact = self._calculate_coverage_impact(selected_tests, changes)

        result = TestSelectionResult(
            selected_tests=selected_tests,
            skipped_tests=skipped_tests,
            execution_order=execution_order,
            estimated_time=estimated_time,
            coverage_impact=coverage_impact,
            selection_reason=selection_reason,
            risk_analysis=impact.risk_summary
        )

        self._report.add_section("选择统计", {
            "selected_count": len(selected_tests),
            "skipped_count": len(skipped_tests),
            "estimated_time": estimated_time,
            "risk_summary": impact.risk_summary
        })

        return {
            "selected_tests": [t.test_id for t in result.selected_tests],
            "skipped_tests": [t.test_id for t in result.skipped_tests],
            "execution_order": result.execution_order,
            "estimated_time": result.estimated_time,
            "coverage_impact": result.coverage_impact,
            "selection_reason": result.selection_reason,
            "risk_analysis": result.risk_analysis,
            "recommendations": impact.recommendations
        }

    def _filter_by_cache(self, changes: List[CodeChange]) -> List[CodeChange]:
        """根据缓存过滤变更"""
        if not self._cache:
            return changes

        filtered = []
        for change in changes:
            file_path = Path(change.file_path)
            if self._cache.is_file_changed(file_path):
                filtered.append(change)
                self._cache.update_file_hash(file_path)

        self._logger.info(f"缓存过滤: {len(changes)} -> {len(filtered)} 个变更文件")
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
        output_format: str = "standard"
    ) -> str:
        """生成pytest命令"""
        if not result.execution_order:
            return "echo 'No tests selected'"

        test_ids = result.execution_order
        cmd_parts = ["pytest"]

        if output_format == "verbose":
            cmd_parts.append("-v")
        elif output_format == "quiet":
            cmd_parts.append("-q")

        cmd_parts.extend(test_ids)

        return " ".join(cmd_parts)

    def print_report(self, result: Dict[str, Any]) -> None:
        """打印选择报告"""
        print("\n" + "=" * 80)
        print("智能测试选择报告")
        print("=" * 80)

        print(f"\n选择统计:")
        print(f"  已选择测试: {len(result['selected_tests'])}")
        print(f"  跳过测试: {len(result['skipped_tests'])}")
        print(f"  预计执行时间: {result['estimated_time']:.2f}秒")

        print(f"\n执行顺序 (前10个):")
        for i, test_id in enumerate(result['execution_order'][:10], 1):
            reason = result['selection_reason'].get(test_id, "N/A")
            print(f"  {i}. {test_id}")
            print(f"     原因: {reason}")

        if len(result['execution_order']) > 10:
            print(f"  ... 还有 {len(result['execution_order']) - 10} 个测试")

        if result.get('risk_analysis'):
            print(f"\n风险分析:")
            risk = result['risk_analysis']
            print(f"  高风险变更: {risk.get('total_high_risk_changes', 0)}")
            print(f"  受影响测试: {risk.get('total_affected_tests', 0)}")

        if result.get('recommendations'):
            print(f"\n建议:")
            for rec in result['recommendations']:
                print(f"  - {rec}")

        print(f"\n覆盖率影响:")
        for file_path, impact in sorted(result['coverage_impact'].items(), key=lambda x: -x[1])[:5]:
            print(f"  {file_path}: {impact:.1%}")

    def save_selection(self, result: Dict[str, Any], output_path: Path) -> None:
        """保存选择结果"""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "timestamp": datetime.now().isoformat(),
            **result
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        self._logger.info(f"选择结果已保存: {output_path}")

    def cleanup(self) -> None:
        if self._cache:
            self._cache.save()
        self._logger.info("清理智能测试选择器资源")


def main() -> int:
    selector = IntelligentTestSelector()
    result = selector.run_from_command_line()

    args = selector._command_parser.parse()
    output_format = args.get("output", "console")
    output_file = args.get("output_file")

    if output_format == "console":
        selector.print_report(result.data)
    elif output_format == "json":
        print(json.dumps(result.data, indent=2, ensure_ascii=False))
    elif output_format == "pytest":
        print(selector.generate_pytest_command(
            TestSelectionResult(
                selected_tests=[],
                skipped_tests=[],
                execution_order=result.data.get("execution_order", []),
                estimated_time=result.data.get("estimated_time", 0),
                coverage_impact=result.data.get("coverage_impact", {}),
                selection_reason=result.data.get("selection_reason", {}),
                risk_analysis=result.data.get("risk_analysis", {})
            )
        ))

    if output_file:
        selector.save_selection(result.data, Path(output_file))

    return 0


if __name__ == "__main__":
    sys.exit(main())
