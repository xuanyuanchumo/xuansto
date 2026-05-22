#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
质量指标收集器

实现全面的质量指标体系，包括代码质量、测试质量、文档质量和架构质量四个维度。
支持指标自动收集、趋势分析和质量门禁检查。

功能模块:
    1. 质量指标体系定义
    2. 指标自动收集
    3. 质量趋势分析
    4. 质量门禁检查

使用示例:
    python quality_metrics_collector.py --project myproject
    python quality_metrics_collector.py --collect-all
    python quality_metrics_collector.py --gate-check --config gate_config.json
    python quality_metrics_collector.py --trend-analysis --days 30
"""

import ast
import json
import logging
import re
import sys
import argparse
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Callable, Union
import statistics
import math


class MetricCategory(Enum):
    """指标类别"""
    CODE_QUALITY = "code_quality"
    TEST_QUALITY = "test_quality"
    DOCUMENTATION_QUALITY = "documentation_quality"
    ARCHITECTURE_QUALITY = "architecture_quality"


class MetricType(Enum):
    """指标类型"""
    COMPLEXITY = "complexity"
    DUPLICATION = "duplication"
    COVERAGE = "coverage"
    VIOLATION = "violation"
    MAINTAINABILITY = "maintainability"
    RELIABILITY = "reliability"
    SECURITY = "security"
    DOCUMENTATION = "documentation"
    DEPENDENCY = "dependency"
    STRUCTURE = "structure"


class GateStatus(Enum):
    """门禁状态"""
    PASSED = "passed"
    WARNING = "warning"
    FAILED = "failed"
    ERROR = "error"


class Severity(Enum):
    """严重程度"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class MetricDefinition:
    """指标定义"""
    name: str
    category: MetricCategory
    metric_type: MetricType
    description: str
    unit: str
    threshold_pass: float
    threshold_warning: float
    higher_is_better: bool
    weight: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "category": self.category.value,
            "metric_type": self.metric_type.value,
            "description": self.description,
            "unit": self.unit,
            "threshold_pass": self.threshold_pass,
            "threshold_warning": self.threshold_warning,
            "higher_is_better": self.higher_is_better,
            "weight": self.weight
        }


@dataclass
class MetricValue:
    """指标值"""
    name: str
    value: float
    unit: str
    timestamp: str
    category: MetricCategory
    metric_type: MetricType
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "value": round(self.value, 4),
            "unit": self.unit,
            "timestamp": self.timestamp,
            "category": self.category.value,
            "metric_type": self.metric_type.value,
            "details": self.details
        }


@dataclass
class CodeQualityMetrics:
    """代码质量指标"""
    cyclomatic_complexity: float = 0.0
    cognitive_complexity: float = 0.0
    max_nesting_depth: int = 0
    avg_function_complexity: float = 0.0
    code_duplication_rate: float = 0.0
    duplicated_blocks: int = 0
    duplicated_lines: int = 0
    total_violations: int = 0
    error_count: int = 0
    warning_count: int = 0
    code_lines: int = 0
    comment_lines: int = 0
    code_to_comment_ratio: float = 0.0
    maintainability_index: float = 0.0
    high_complexity_functions: List[Dict[str, Any]] = field(default_factory=list)
    duplication_hotspots: List[Dict[str, Any]] = field(default_factory=list)
    top_violations: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cyclomatic_complexity": round(self.cyclomatic_complexity, 2),
            "cognitive_complexity": round(self.cognitive_complexity, 2),
            "max_nesting_depth": self.max_nesting_depth,
            "avg_function_complexity": round(self.avg_function_complexity, 2),
            "code_duplication_rate": round(self.code_duplication_rate, 4),
            "duplicated_blocks": self.duplicated_blocks,
            "duplicated_lines": self.duplicated_lines,
            "total_violations": self.total_violations,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "code_lines": self.code_lines,
            "comment_lines": self.comment_lines,
            "code_to_comment_ratio": round(self.code_to_comment_ratio, 4),
            "maintainability_index": round(self.maintainability_index, 2),
            "high_complexity_functions": self.high_complexity_functions[:20],
            "duplication_hotspots": self.duplication_hotspots[:10],
            "top_violations": self.top_violations[:20]
        }


@dataclass
class TestQualityMetrics:
    """测试质量指标"""
    line_coverage: float = 0.0
    branch_coverage: float = 0.0
    function_coverage: float = 0.0
    test_count: int = 0
    test_pass_rate: float = 0.0
    test_execution_time: float = 0.0
    avg_test_execution_time: float = 0.0
    failed_tests: int = 0
    skipped_tests: int = 0
    test_to_code_ratio: float = 0.0
    test_quality_score: float = 0.0
    uncovered_files: List[str] = field(default_factory=list)
    low_coverage_files: List[Dict[str, Any]] = field(default_factory=list)
    failed_test_details: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "line_coverage": round(self.line_coverage, 2),
            "branch_coverage": round(self.branch_coverage, 2),
            "function_coverage": round(self.function_coverage, 2),
            "test_count": self.test_count,
            "test_pass_rate": round(self.test_pass_rate, 4),
            "test_execution_time": round(self.test_execution_time, 2),
            "avg_test_execution_time": round(self.avg_test_execution_time, 4),
            "failed_tests": self.failed_tests,
            "skipped_tests": self.skipped_tests,
            "test_to_code_ratio": round(self.test_to_code_ratio, 4),
            "test_quality_score": round(self.test_quality_score, 2),
            "uncovered_files": self.uncovered_files[:20],
            "low_coverage_files": self.low_coverage_files[:20],
            "failed_test_details": self.failed_test_details[:10]
        }


@dataclass
class DocumentationQualityMetrics:
    """文档质量指标"""
    total_files: int = 0
    documented_files: int = 0
    documentation_coverage: float = 0.0
    total_functions: int = 0
    documented_functions: int = 0
    function_doc_coverage: float = 0.0
    total_classes: int = 0
    documented_classes: int = 0
    class_doc_coverage: float = 0.0
    readme_exists: bool = False
    api_doc_exists: bool = False
    changelog_exists: bool = False
    broken_links: int = 0
    outdated_docs: int = 0
    doc_quality_score: float = 0.0
    undocumented_items: List[Dict[str, Any]] = field(default_factory=list)
    broken_link_details: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_files": self.total_files,
            "documented_files": self.documented_files,
            "documentation_coverage": round(self.documentation_coverage, 4),
            "total_functions": self.total_functions,
            "documented_functions": self.documented_functions,
            "function_doc_coverage": round(self.function_doc_coverage, 4),
            "total_classes": self.total_classes,
            "documented_classes": self.documented_classes,
            "class_doc_coverage": round(self.class_doc_coverage, 4),
            "readme_exists": self.readme_exists,
            "api_doc_exists": self.api_doc_exists,
            "changelog_exists": self.changelog_exists,
            "broken_links": self.broken_links,
            "outdated_docs": self.outdated_docs,
            "doc_quality_score": round(self.doc_quality_score, 2),
            "undocumented_items": self.undocumented_items[:20],
            "broken_link_details": self.broken_link_details[:10]
        }


@dataclass
class ArchitectureQualityMetrics:
    """架构质量指标"""
    total_modules: int = 0
    circular_dependencies: int = 0
    max_dependency_depth: int = 0
    avg_dependency_depth: float = 0.0
    coupling_score: float = 0.0
    cohesion_score: float = 0.0
    architecture_violations: int = 0
    god_classes: int = 0
    god_classes_list: List[Dict[str, Any]] = field(default_factory=list)
    circular_dependency_details: List[Dict[str, Any]] = field(default_factory=list)
    dependency_graph: Dict[str, List[str]] = field(default_factory=dict)
    module_metrics: List[Dict[str, Any]] = field(default_factory=list)
    architecture_quality_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_modules": self.total_modules,
            "circular_dependencies": self.circular_dependencies,
            "max_dependency_depth": self.max_dependency_depth,
            "avg_dependency_depth": round(self.avg_dependency_depth, 2),
            "coupling_score": round(self.coupling_score, 4),
            "cohesion_score": round(self.cohesion_score, 4),
            "architecture_violations": self.architecture_violations,
            "god_classes": self.god_classes,
            "god_classes_list": self.god_classes_list[:10],
            "circular_dependency_details": self.circular_dependency_details[:10],
            "dependency_graph": dict(list(self.dependency_graph.items())[:20]),
            "module_metrics": self.module_metrics[:20],
            "architecture_quality_score": round(self.architecture_quality_score, 2)
        }


@dataclass
class QualityMetricsCollection:
    """质量指标集合"""
    timestamp: str
    project: str
    code_quality: CodeQualityMetrics
    test_quality: TestQualityMetrics
    documentation_quality: DocumentationQualityMetrics
    architecture_quality: ArchitectureQualityMetrics
    overall_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "project": self.project,
            "code_quality": self.code_quality.to_dict(),
            "test_quality": self.test_quality.to_dict(),
            "documentation_quality": self.documentation_quality.to_dict(),
            "architecture_quality": self.architecture_quality.to_dict(),
            "overall_score": round(self.overall_score, 2),
            "metadata": self.metadata
        }


@dataclass
class GateCheckResult:
    """门禁检查结果"""
    gate_name: str
    status: GateStatus
    metric_name: str
    actual_value: float
    threshold: float
    message: str
    severity: Severity
    suggestions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gate_name": self.gate_name,
            "status": self.status.value,
            "metric_name": self.metric_name,
            "actual_value": round(self.actual_value, 4),
            "threshold": round(self.threshold, 4),
            "message": self.message,
            "severity": self.severity.value,
            "suggestions": self.suggestions
        }


@dataclass
class QualityGateReport:
    """质量门禁报告"""
    timestamp: str
    project: str
    overall_status: GateStatus
    gate_results: List[GateCheckResult]
    passed_gates: int
    failed_gates: int
    warning_gates: int
    quality_score: float
    recommendations: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "project": self.project,
            "overall_status": self.overall_status.value,
            "gate_results": [g.to_dict() for g in self.gate_results],
            "passed_gates": self.passed_gates,
            "failed_gates": self.failed_gates,
            "warning_gates": self.warning_gates,
            "quality_score": round(self.quality_score, 2),
            "recommendations": self.recommendations
        }


@dataclass
class TrendDataPoint:
    """趋势数据点"""
    timestamp: str
    overall_score: float
    code_quality_score: float
    test_quality_score: float
    doc_quality_score: float
    architecture_quality_score: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "overall_score": round(self.overall_score, 2),
            "code_quality_score": round(self.code_quality_score, 2),
            "test_quality_score": round(self.test_quality_score, 2),
            "doc_quality_score": round(self.doc_quality_score, 2),
            "architecture_quality_score": round(self.architecture_quality_score, 2)
        }


@dataclass
class TrendAnalysis:
    """趋势分析结果"""
    metric_name: str
    direction: str
    slope: float
    current_value: float
    predicted_value: float
    confidence: float
    change_rate: float
    data_points: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "direction": self.direction,
            "slope": round(self.slope, 6),
            "current_value": round(self.current_value, 4),
            "predicted_value": round(self.predicted_value, 4),
            "confidence": round(self.confidence, 4),
            "change_rate": round(self.change_rate, 4),
            "data_points": self.data_points
        }


class QualityMetricsRegistry:
    """质量指标注册表"""

    def __init__(self):
        self._metrics: Dict[str, MetricDefinition] = {}
        self._initialize_default_metrics()

    def _initialize_default_metrics(self):
        """初始化默认指标定义"""
        default_metrics = [
            MetricDefinition(
                name="cyclomatic_complexity",
                category=MetricCategory.CODE_QUALITY,
                metric_type=MetricType.COMPLEXITY,
                description="圈复杂度",
                unit="",
                threshold_pass=10.0,
                threshold_warning=15.0,
                higher_is_better=False,
                weight=1.5
            ),
            MetricDefinition(
                name="code_duplication_rate",
                category=MetricCategory.CODE_QUALITY,
                metric_type=MetricType.DUPLICATION,
                description="代码重复率",
                unit="%",
                threshold_pass=5.0,
                threshold_warning=10.0,
                higher_is_better=False,
                weight=1.2
            ),
            MetricDefinition(
                name="line_coverage",
                category=MetricCategory.TEST_QUALITY,
                metric_type=MetricType.COVERAGE,
                description="行覆盖率",
                unit="%",
                threshold_pass=80.0,
                threshold_warning=70.0,
                higher_is_better=True,
                weight=2.0
            ),
            MetricDefinition(
                name="branch_coverage",
                category=MetricCategory.TEST_QUALITY,
                metric_type=MetricType.COVERAGE,
                description="分支覆盖率",
                unit="%",
                threshold_pass=70.0,
                threshold_warning=60.0,
                higher_is_better=True,
                weight=1.5
            ),
            MetricDefinition(
                name="test_pass_rate",
                category=MetricCategory.TEST_QUALITY,
                metric_type=MetricType.RELIABILITY,
                description="测试通过率",
                unit="%",
                threshold_pass=100.0,
                threshold_warning=95.0,
                higher_is_better=True,
                weight=2.5
            ),
            MetricDefinition(
                name="documentation_coverage",
                category=MetricCategory.DOCUMENTATION_QUALITY,
                metric_type=MetricType.DOCUMENTATION,
                description="文档覆盖率",
                unit="%",
                threshold_pass=80.0,
                threshold_warning=60.0,
                higher_is_better=True,
                weight=1.0
            ),
            MetricDefinition(
                name="function_doc_coverage",
                category=MetricCategory.DOCUMENTATION_QUALITY,
                metric_type=MetricType.DOCUMENTATION,
                description="函数文档覆盖率",
                unit="%",
                threshold_pass=80.0,
                threshold_warning=60.0,
                higher_is_better=True,
                weight=1.0
            ),
            MetricDefinition(
                name="circular_dependencies",
                category=MetricCategory.ARCHITECTURE_QUALITY,
                metric_type=MetricType.DEPENDENCY,
                description="循环依赖数量",
                unit="",
                threshold_pass=0.0,
                threshold_warning=3.0,
                higher_is_better=False,
                weight=2.0
            ),
            MetricDefinition(
                name="coupling_score",
                category=MetricCategory.ARCHITECTURE_QUALITY,
                metric_type=MetricType.STRUCTURE,
                description="耦合度评分",
                unit="",
                threshold_pass=0.3,
                threshold_warning=0.5,
                higher_is_better=False,
                weight=1.5
            ),
            MetricDefinition(
                name="error_count",
                category=MetricCategory.CODE_QUALITY,
                metric_type=MetricType.VIOLATION,
                description="错误数量",
                unit="",
                threshold_pass=0.0,
                threshold_warning=5.0,
                higher_is_better=False,
                weight=2.0
            ),
        ]

        for metric in default_metrics:
            self._metrics[metric.name] = metric

    def register(self, metric: MetricDefinition):
        """注册指标"""
        self._metrics[metric.name] = metric

    def get(self, name: str) -> Optional[MetricDefinition]:
        """获取指标定义"""
        return self._metrics.get(name)

    def get_all(self) -> List[MetricDefinition]:
        """获取所有指标定义"""
        return list(self._metrics.values())

    def get_by_category(self, category: MetricCategory) -> List[MetricDefinition]:
        """按类别获取指标"""
        return [m for m in self._metrics.values() if m.category == category]


class CodeQualityCollector:
    """代码质量指标收集器"""

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)

    def collect(self, project_path: Path) -> CodeQualityMetrics:
        """收集代码质量指标"""
        python_files = self._find_python_files(project_path)

        if not python_files:
            return CodeQualityMetrics()

        complexity_metrics = self._collect_complexity(python_files)
        duplication_metrics = self._collect_duplication(python_files)
        violation_metrics = self._collect_violations(python_files)
        lines_metrics = self._collect_lines(python_files)

        maintainability = self._calculate_maintainability_index(
            complexity_metrics["avg_complexity"],
            lines_metrics["code_lines"],
            lines_metrics["comment_lines"]
        )

        return CodeQualityMetrics(
            cyclomatic_complexity=complexity_metrics["total_cyclomatic"],
            cognitive_complexity=complexity_metrics["total_cognitive"],
            max_nesting_depth=complexity_metrics["max_nesting"],
            avg_function_complexity=complexity_metrics["avg_complexity"],
            code_duplication_rate=duplication_metrics["rate"],
            duplicated_blocks=duplication_metrics["blocks"],
            duplicated_lines=duplication_metrics["lines"],
            total_violations=violation_metrics["total"],
            error_count=violation_metrics["errors"],
            warning_count=violation_metrics["warnings"],
            code_lines=lines_metrics["code_lines"],
            comment_lines=lines_metrics["comment_lines"],
            code_to_comment_ratio=lines_metrics["ratio"],
            maintainability_index=maintainability,
            high_complexity_functions=complexity_metrics["high_complexity_functions"],
            duplication_hotspots=duplication_metrics["hotspots"],
            top_violations=violation_metrics["top_violations"]
        )

    def _find_python_files(self, project_path: Path) -> List[Path]:
        """查找Python文件"""
        python_files = list(project_path.rglob("*.py"))
        python_files = [
            f for f in python_files
            if not any(part.startswith('.') for part in f.parts)
            and 'venv' not in str(f).lower()
            and '__pycache__' not in str(f)
            and 'site-packages' not in str(f)
        ]
        return python_files

    def _collect_complexity(self, file_paths: List[Path]) -> Dict[str, Any]:
        """收集复杂度指标"""
        total_cyclomatic = 0.0
        total_cognitive = 0.0
        max_nesting = 0
        all_high_complexity = []
        function_count = 0

        for file_path in file_paths:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                tree = ast.parse(content)

                cyclomatic = self._calculate_cyclomatic_complexity(tree)
                cognitive, nesting = self._calculate_cognitive_complexity(tree)
                high_complexity = self._find_high_complexity_functions(tree, file_path)

                total_cyclomatic += cyclomatic
                total_cognitive += cognitive
                max_nesting = max(max_nesting, nesting)
                all_high_complexity.extend(high_complexity)
                function_count += len([n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))])

            except Exception as e:
                self.logger.warning(f"分析文件 {file_path} 失败: {e}")

        avg_complexity = total_cyclomatic / function_count if function_count > 0 else 0

        return {
            "total_cyclomatic": total_cyclomatic,
            "total_cognitive": total_cognitive,
            "max_nesting": max_nesting,
            "avg_complexity": avg_complexity,
            "high_complexity_functions": sorted(all_high_complexity, key=lambda x: x["complexity"], reverse=True)[:20]
        }

    def _calculate_cyclomatic_complexity(self, tree: ast.AST) -> float:
        """计算圈复杂度"""
        complexity = 1

        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1

        return float(complexity)

    def _calculate_cognitive_complexity(self, tree: ast.AST) -> Tuple[float, int]:
        """计算认知复杂度和最大嵌套深度"""
        cognitive = 0
        max_nesting = 0

        def visit_node(node: ast.AST, nesting_level: int = 0):
            nonlocal cognitive, max_nesting

            max_nesting = max(max_nesting, nesting_level)

            if isinstance(node, (ast.If, ast.While, ast.For)):
                cognitive += nesting_level + 1
                for child in ast.iter_child_nodes(node):
                    visit_node(child, nesting_level + 1)
            elif isinstance(node, ast.ExceptHandler):
                cognitive += nesting_level + 1
                for child in ast.iter_child_nodes(node):
                    visit_node(child, nesting_level + 1)
            elif isinstance(node, ast.BoolOp):
                cognitive += len(node.values) - 1
                for child in ast.iter_child_nodes(node):
                    visit_node(child, nesting_level)
            else:
                for child in ast.iter_child_nodes(node):
                    visit_node(child, nesting_level)

        visit_node(tree)
        return float(cognitive), max_nesting

    def _find_high_complexity_functions(self, tree: ast.AST, file_path: Path) -> List[Dict[str, Any]]:
        """查找高复杂度函数"""
        high_complexity = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                complexity = self._calculate_function_complexity(node)
                if complexity > 10:
                    high_complexity.append({
                        "name": node.name,
                        "file": str(file_path),
                        "line": node.lineno,
                        "complexity": complexity
                    })

        return high_complexity

    def _calculate_function_complexity(self, node: ast.AST) -> int:
        """计算函数复杂度"""
        complexity = 1

        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1

        return complexity

    def _collect_duplication(self, file_paths: List[Path]) -> Dict[str, Any]:
        """收集重复代码指标"""
        import hashlib

        code_blocks = defaultdict(list)
        total_lines = 0
        min_lines = 6

        for file_path in file_paths:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()

                total_lines += len(lines)

                for i in range(len(lines) - min_lines + 1):
                    block = ''.join(lines[i:i + min_lines])
                    block_hash = hashlib.md5(block.encode()).hexdigest()

                    code_blocks[block_hash].append({
                        "file": str(file_path),
                        "start_line": i + 1,
                        "end_line": i + min_lines
                    })

            except Exception as e:
                self.logger.warning(f"检测文件 {file_path} 重复代码失败: {e}")

        duplicated_blocks = 0
        duplicated_lines = 0
        hotspots = []

        for block_hash, locations in code_blocks.items():
            if len(locations) > 1:
                duplicated_blocks += len(locations)
                duplicated_lines += len(locations) * min_lines

                if len(locations) > 2:
                    hotspots.append({
                        "locations": locations,
                        "occurrences": len(locations),
                        "lines": min_lines
                    })

        hotspots.sort(key=lambda x: x["occurrences"], reverse=True)

        duplication_rate = duplicated_lines / total_lines if total_lines > 0 else 0

        return {
            "rate": duplication_rate,
            "blocks": duplicated_blocks,
            "lines": duplicated_lines,
            "hotspots": hotspots[:10]
        }

    def _collect_violations(self, file_paths: List[Path]) -> Dict[str, Any]:
        """收集违规指标"""
        total_violations = 0
        error_count = 0
        warning_count = 0
        all_violations = []

        violation_patterns = [
            (r"except\s*:", "error", "不应使用裸except"),
            (r"^.{121,}", "warning", "行长度超过120字符"),
            (r".*\s+$", "info", "行尾空白字符"),
        ]

        for file_path in file_paths:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()

                for i, line in enumerate(lines, 1):
                    for pattern, severity, message in violation_patterns:
                        if re.search(pattern, line):
                            total_violations += 1
                            if severity == "error":
                                error_count += 1
                            elif severity == "warning":
                                warning_count += 1

                            all_violations.append({
                                "file": str(file_path),
                                "line": i,
                                "severity": severity,
                                "message": message
                            })

            except Exception as e:
                self.logger.warning(f"检测文件 {file_path} 违规失败: {e}")

        return {
            "total": total_violations,
            "errors": error_count,
            "warnings": warning_count,
            "top_violations": sorted(all_violations, key=lambda x: {"error": 0, "warning": 1, "info": 2}.get(x["severity"], 3))[:20]
        }

    def _collect_lines(self, file_paths: List[Path]) -> Dict[str, Any]:
        """收集行数统计"""
        total_code = 0
        total_comments = 0

        for file_path in file_paths:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()

                for line in lines:
                    stripped = line.strip()
                    if not stripped:
                        continue
                    elif stripped.startswith('#'):
                        total_comments += 1
                    else:
                        total_code += 1

            except Exception:
                pass

        ratio = total_comments / total_code if total_code > 0 else 0

        return {
            "code_lines": total_code,
            "comment_lines": total_comments,
            "ratio": ratio
        }

    def _calculate_maintainability_index(self, avg_complexity: float, code_lines: int, comment_lines: int) -> float:
        """计算可维护性指数"""
        if code_lines == 0:
            return 100.0

        volume = code_lines * (1 + avg_complexity / 10)
        comment_factor = 1 + (comment_lines / code_lines) if code_lines > 0 else 1

        mi = max(0, (171 - 5.2 * math.log(volume + 1) - 0.23 * avg_complexity - 16.2 * math.log(code_lines + 1)) * 100 / 171)

        return min(100, max(0, mi * comment_factor))


class TestQualityCollector:
    """测试质量指标收集器"""

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)

    def collect(self, project_path: Path, coverage_path: Optional[Path] = None) -> TestQualityMetrics:
        """收集测试质量指标"""
        test_files = self._find_test_files(project_path)
        test_metrics = self._collect_test_metrics(test_files)

        coverage_metrics = self._collect_coverage_metrics(project_path, coverage_path)

        test_quality_score = self._calculate_test_quality_score(
            coverage_metrics["line_coverage"],
            test_metrics["pass_rate"],
            test_metrics["test_count"]
        )

        return TestQualityMetrics(
            line_coverage=coverage_metrics["line_coverage"],
            branch_coverage=coverage_metrics["branch_coverage"],
            function_coverage=coverage_metrics["function_coverage"],
            test_count=test_metrics["test_count"],
            test_pass_rate=test_metrics["pass_rate"],
            test_execution_time=test_metrics["execution_time"],
            avg_test_execution_time=test_metrics["avg_execution_time"],
            failed_tests=test_metrics["failed_tests"],
            skipped_tests=test_metrics["skipped_tests"],
            test_to_code_ratio=test_metrics["test_to_code_ratio"],
            test_quality_score=test_quality_score,
            uncovered_files=coverage_metrics["uncovered_files"],
            low_coverage_files=coverage_metrics["low_coverage_files"],
            failed_test_details=test_metrics["failed_test_details"]
        )

    def _find_test_files(self, project_path: Path) -> List[Path]:
        """查找测试文件"""
        test_files = list(project_path.rglob("test_*.py"))
        test_files.extend(list(project_path.rglob("*_test.py")))
        test_files.extend(list(project_path.rglob("tests/**/*.py")))

        test_files = [
            f for f in test_files
            if not any(part.startswith('.') for part in f.parts)
            and 'venv' not in str(f).lower()
            and '__pycache__' not in str(f)
        ]

        return list(set(test_files))

    def _collect_test_metrics(self, test_files: List[Path]) -> Dict[str, Any]:
        """收集测试指标"""
        test_count = 0

        for test_file in test_files:
            try:
                with open(test_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        if node.name.startswith('test_'):
                            test_count += 1

            except Exception:
                pass

        code_files = len([f for f in test_files[0].parent.parent.rglob("*.py") if 'test' not in str(f).lower()]) if test_files else 0
        test_to_code_ratio = test_count / code_files if code_files > 0 else 0

        return {
            "test_count": test_count,
            "pass_rate": 1.0,
            "execution_time": 0.0,
            "avg_execution_time": 0.0,
            "failed_tests": 0,
            "skipped_tests": 0,
            "test_to_code_ratio": test_to_code_ratio,
            "failed_test_details": []
        }

    def _collect_coverage_metrics(self, project_path: Path, coverage_path: Optional[Path]) -> Dict[str, Any]:
        """收集覆盖率指标"""
        if coverage_path and coverage_path.exists():
            return self._parse_coverage_report(coverage_path)

        coverage_file = project_path / "coverage.json"
        if coverage_file.exists():
            return self._parse_coverage_report(coverage_file)

        coverage_xml = project_path / "coverage.xml"
        if coverage_xml.exists():
            return self._parse_coverage_xml(coverage_xml)

        return {
            "line_coverage": 0.0,
            "branch_coverage": 0.0,
            "function_coverage": 0.0,
            "uncovered_files": [],
            "low_coverage_files": []
        }

    def _parse_coverage_report(self, coverage_path: Path) -> Dict[str, Any]:
        """解析覆盖率报告"""
        try:
            with open(coverage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if "files" in data:
                files_data = data.get("files", {})
                total_covered = 0
                total_lines = 0
                low_coverage = []

                for file_path, file_info in files_data.items():
                    summary = file_info.get("summary", {})
                    covered = summary.get("covered_lines", 0)
                    total = summary.get("num_statements", 0)

                    total_covered += covered
                    total_lines += total

                    if total > 0:
                        rate = (covered / total) * 100
                        if rate < 80:
                            low_coverage.append({
                                "file": file_path,
                                "coverage": rate
                            })

                line_coverage = (total_covered / total_lines * 100) if total_lines > 0 else 0

                return {
                    "line_coverage": line_coverage,
                    "branch_coverage": data.get("totals", {}).get("percent_covered", 0),
                    "function_coverage": line_coverage,
                    "uncovered_files": [f for f in files_data.keys() if files_data[f].get("summary", {}).get("covered_lines", 0) == 0][:20],
                    "low_coverage_files": sorted(low_coverage, key=lambda x: x["coverage"])[:20]
                }

        except Exception as e:
            self.logger.warning(f"解析覆盖率报告失败: {e}")

        return {
            "line_coverage": 0.0,
            "branch_coverage": 0.0,
            "function_coverage": 0.0,
            "uncovered_files": [],
            "low_coverage_files": []
        }

    def _parse_coverage_xml(self, coverage_path: Path) -> Dict[str, Any]:
        """解析XML覆盖率报告"""
        try:
            from xml.etree import ElementTree

            tree = ElementTree.parse(coverage_path)
            root = tree.getroot()

            line_rate = float(root.get("line-rate", 0)) * 100
            branch_rate = float(root.get("branch-rate", 0)) * 100

            return {
                "line_coverage": line_rate,
                "branch_coverage": branch_rate,
                "function_coverage": line_rate,
                "uncovered_files": [],
                "low_coverage_files": []
            }

        except Exception as e:
            self.logger.warning(f"解析XML覆盖率报告失败: {e}")

        return {
            "line_coverage": 0.0,
            "branch_coverage": 0.0,
            "function_coverage": 0.0,
            "uncovered_files": [],
            "low_coverage_files": []
        }

    def _calculate_test_quality_score(self, line_coverage: float, pass_rate: float, test_count: int) -> float:
        """计算测试质量评分"""
        coverage_score = min(line_coverage / 80, 1.0) * 40
        pass_rate_score = pass_rate * 40
        quantity_score = min(test_count / 50, 1.0) * 20

        return coverage_score + pass_rate_score + quantity_score


class DocumentationQualityCollector:
    """文档质量指标收集器"""

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)

    def collect(self, project_path: Path) -> DocumentationQualityMetrics:
        """收集文档质量指标"""
        python_files = self._find_python_files(project_path)

        doc_metrics = self._collect_doc_metrics(python_files)
        file_metrics = self._collect_file_metrics(project_path)

        doc_quality_score = self._calculate_doc_quality_score(
            doc_metrics["function_doc_coverage"],
            doc_metrics["class_doc_coverage"],
            file_metrics
        )

        return DocumentationQualityMetrics(
            total_files=doc_metrics["total_files"],
            documented_files=doc_metrics["documented_files"],
            documentation_coverage=doc_metrics["documentation_coverage"],
            total_functions=doc_metrics["total_functions"],
            documented_functions=doc_metrics["documented_functions"],
            function_doc_coverage=doc_metrics["function_doc_coverage"],
            total_classes=doc_metrics["total_classes"],
            documented_classes=doc_metrics["documented_classes"],
            class_doc_coverage=doc_metrics["class_doc_coverage"],
            readme_exists=file_metrics["readme_exists"],
            api_doc_exists=file_metrics["api_doc_exists"],
            changelog_exists=file_metrics["changelog_exists"],
            broken_links=0,
            outdated_docs=0,
            doc_quality_score=doc_quality_score,
            undocumented_items=doc_metrics["undocumented_items"],
            broken_link_details=[]
        )

    def _find_python_files(self, project_path: Path) -> List[Path]:
        """查找Python文件"""
        python_files = list(project_path.rglob("*.py"))
        python_files = [
            f for f in python_files
            if not any(part.startswith('.') for part in f.parts)
            and 'venv' not in str(f).lower()
            and '__pycache__' not in str(f)
            and 'site-packages' not in str(f)
        ]
        return python_files

    def _collect_doc_metrics(self, file_paths: List[Path]) -> Dict[str, Any]:
        """收集文档指标"""
        total_functions = 0
        documented_functions = 0
        total_classes = 0
        documented_classes = 0
        documented_files = 0
        undocumented_items = []

        for file_path in file_paths:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                tree = ast.parse(content)
                file_has_doc = False

                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        total_functions += 1
                        if ast.get_docstring(node):
                            documented_functions += 1
                            file_has_doc = True
                        else:
                            if not node.name.startswith('_'):
                                undocumented_items.append({
                                    "type": "function",
                                    "name": node.name,
                                    "file": str(file_path),
                                    "line": node.lineno
                                })

                    elif isinstance(node, ast.ClassDef):
                        total_classes += 1
                        if ast.get_docstring(node):
                            documented_classes += 1
                            file_has_doc = True
                        else:
                            undocumented_items.append({
                                "type": "class",
                                "name": node.name,
                                "file": str(file_path),
                                "line": node.lineno
                            })

                if file_has_doc:
                    documented_files += 1

            except Exception as e:
                self.logger.warning(f"分析文件 {file_path} 文档失败: {e}")

        function_doc_coverage = (documented_functions / total_functions * 100) if total_functions > 0 else 0
        class_doc_coverage = (documented_classes / total_classes * 100) if total_classes > 0 else 0
        documentation_coverage = (documented_files / len(file_paths) * 100) if file_paths else 0

        return {
            "total_files": len(file_paths),
            "documented_files": documented_files,
            "documentation_coverage": documentation_coverage,
            "total_functions": total_functions,
            "documented_functions": documented_functions,
            "function_doc_coverage": function_doc_coverage,
            "total_classes": total_classes,
            "documented_classes": documented_classes,
            "class_doc_coverage": class_doc_coverage,
            "undocumented_items": undocumented_items[:20]
        }

    def _collect_file_metrics(self, project_path: Path) -> Dict[str, Any]:
        """收集文件指标"""
        readme_exists = (project_path / "README.md").exists() or (project_path / "readme.md").exists()
        api_doc_exists = (project_path / "docs" / "api").exists() or (project_path / "API.md").exists()
        changelog_exists = (project_path / "CHANGELOG.md").exists() or (project_path / "HISTORY.md").exists()

        return {
            "readme_exists": readme_exists,
            "api_doc_exists": api_doc_exists,
            "changelog_exists": changelog_exists
        }

    def _calculate_doc_quality_score(
        self,
        function_doc_coverage: float,
        class_doc_coverage: float,
        file_metrics: Dict[str, Any]
    ) -> float:
        """计算文档质量评分"""
        coverage_score = (function_doc_coverage + class_doc_coverage) / 2 * 0.6

        file_score = 0
        if file_metrics["readme_exists"]:
            file_score += 15
        if file_metrics["api_doc_exists"]:
            file_score += 15
        if file_metrics["changelog_exists"]:
            file_score += 10

        return min(coverage_score + file_score, 100)


class ArchitectureQualityCollector:
    """架构质量指标收集器"""

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)

    def collect(self, project_path: Path) -> ArchitectureQualityMetrics:
        """收集架构质量指标"""
        python_files = self._find_python_files(project_path)

        dependency_metrics = self._collect_dependency_metrics(python_files)
        structure_metrics = self._collect_structure_metrics(python_files)

        architecture_quality_score = self._calculate_architecture_score(
            dependency_metrics,
            structure_metrics
        )

        return ArchitectureQualityMetrics(
            total_modules=dependency_metrics["total_modules"],
            circular_dependencies=dependency_metrics["circular_dependencies"],
            max_dependency_depth=dependency_metrics["max_depth"],
            avg_dependency_depth=dependency_metrics["avg_depth"],
            coupling_score=dependency_metrics["coupling_score"],
            cohesion_score=structure_metrics["cohesion_score"],
            architecture_violations=structure_metrics["violations"],
            god_classes=structure_metrics["god_classes_count"],
            god_classes_list=structure_metrics["god_classes"],
            circular_dependency_details=dependency_metrics["circular_details"],
            dependency_graph=dependency_metrics["dependency_graph"],
            module_metrics=dependency_metrics["module_metrics"],
            architecture_quality_score=architecture_quality_score
        )

    def _find_python_files(self, project_path: Path) -> List[Path]:
        """查找Python文件"""
        python_files = list(project_path.rglob("*.py"))
        python_files = [
            f for f in python_files
            if not any(part.startswith('.') for part in f.parts)
            and 'venv' not in str(f).lower()
            and '__pycache__' not in str(f)
            and 'site-packages' not in str(f)
        ]
        return python_files

    def _collect_dependency_metrics(self, file_paths: List[Path]) -> Dict[str, Any]:
        """收集依赖指标"""
        imports = defaultdict(set)
        module_files = defaultdict(list)

        for file_path in file_paths:
            try:
                module_name = self._get_module_name(file_path)
                module_files[module_name].append(str(file_path))

                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports[module_name].add(alias.name.split('.')[0])
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            imports[module_name].add(node.module.split('.')[0])

            except Exception as e:
                self.logger.warning(f"分析文件 {file_path} 依赖失败: {e}")

        circular_deps = self._detect_circular_dependencies(imports)

        coupling_score = self._calculate_coupling_score(imports)

        depths = self._calculate_dependency_depths(imports)
        max_depth = max(depths.values()) if depths else 0
        avg_depth = sum(depths.values()) / len(depths) if depths else 0

        return {
            "total_modules": len(module_files),
            "circular_dependencies": len(circular_deps),
            "max_depth": max_depth,
            "avg_depth": avg_depth,
            "coupling_score": coupling_score,
            "circular_details": circular_deps[:10],
            "dependency_graph": {k: list(v) for k, v in list(imports.items())[:20]},
            "module_metrics": [
                {"module": k, "file_count": len(v)}
                for k, v in list(module_files.items())[:20]
            ]
        }

    def _get_module_name(self, file_path: Path) -> str:
        """获取模块名称"""
        parts = file_path.parts
        if len(parts) > 1:
            return parts[-2]
        return "root"

    def _detect_circular_dependencies(self, imports: Dict[str, set]) -> List[Dict[str, Any]]:
        """检测循环依赖"""
        circular = []

        for module_a, deps_a in imports.items():
            for module_b in deps_a:
                if module_b in imports:
                    if module_a in imports[module_b]:
                        circular.append({
                            "module_a": module_a,
                            "module_b": module_b,
                            "type": "direct"
                        })

        return circular

    def _calculate_coupling_score(self, imports: Dict[str, set]) -> float:
        """计算耦合度评分"""
        if not imports:
            return 0.0

        total_deps = sum(len(deps) for deps in imports.values())
        avg_deps = total_deps / len(imports)

        return min(avg_deps / 10, 1.0)

    def _calculate_dependency_depths(self, imports: Dict[str, set]) -> Dict[str, int]:
        """计算依赖深度"""
        depths = {}

        def get_depth(module: str, visited: set) -> int:
            if module in visited:
                return 0
            if module not in imports:
                return 0

            visited.add(module)
            deps = imports[module]
            if not deps:
                return 0

            return 1 + max(get_depth(dep, visited.copy()) for dep in deps)

        for module in imports.keys():
            depths[module] = get_depth(module, set())

        return depths

    def _collect_structure_metrics(self, file_paths: List[Path]) -> Dict[str, Any]:
        """收集结构指标"""
        god_classes = []
        violations = 0

        for file_path in file_paths:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        methods = [n for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
                        if len(methods) > 20:
                            god_classes.append({
                                "name": node.name,
                                "file": str(file_path),
                                "method_count": len(methods)
                            })

            except Exception as e:
                self.logger.warning(f"分析文件 {file_path} 结构失败: {e}")

        cohesion_score = 1.0 - (len(god_classes) / len(file_paths)) if file_paths else 1.0

        return {
            "god_classes_count": len(god_classes),
            "god_classes": sorted(god_classes, key=lambda x: x["method_count"], reverse=True)[:10],
            "violations": violations,
            "cohesion_score": cohesion_score
        }

    def _calculate_architecture_score(
        self,
        dependency_metrics: Dict[str, Any],
        structure_metrics: Dict[str, Any]
    ) -> float:
        """计算架构质量评分"""
        circular_penalty = dependency_metrics["circular_dependencies"] * 10
        coupling_penalty = dependency_metrics["coupling_score"] * 20
        god_class_penalty = structure_metrics["god_classes_count"] * 5

        score = 100 - circular_penalty - coupling_penalty - god_class_penalty

        return max(0, min(100, score))


class QualityMetricsCollector:
    """质量指标收集器主类"""

    def __init__(
        self,
        project_path: Path,
        storage_path: Optional[Path] = None,
        logger: Optional[logging.Logger] = None
    ):
        self.project_path = project_path
        self.storage_path = storage_path or project_path / "quality_data"
        self.logger = logger or logging.getLogger(__name__)

        self.registry = QualityMetricsRegistry()
        self.code_collector = CodeQualityCollector(logger)
        self.test_collector = TestQualityCollector(logger)
        self.doc_collector = DocumentationQualityCollector(logger)
        self.arch_collector = ArchitectureQualityCollector(logger)

    def collect_all(self, project: str = "default") -> QualityMetricsCollection:
        """收集所有质量指标"""
        self.logger.info(f"开始收集项目 {project} 的质量指标")

        code_quality = self.code_collector.collect(self.project_path)
        test_quality = self.test_collector.collect(self.project_path)
        doc_quality = self.doc_collector.collect(self.project_path)
        architecture_quality = self.arch_collector.collect(self.project_path)

        overall_score = self._calculate_overall_score(
            code_quality,
            test_quality,
            doc_quality,
            architecture_quality
        )

        collection = QualityMetricsCollection(
            timestamp=datetime.now().isoformat(),
            project=project,
            code_quality=code_quality,
            test_quality=test_quality,
            documentation_quality=doc_quality,
            architecture_quality=architecture_quality,
            overall_score=overall_score,
            metadata={
                "collector_version": "1.0.0",
                "project_path": str(self.project_path)
            }
        )

        self._save_collection(collection, project)

        return collection

    def _calculate_overall_score(
        self,
        code_quality: CodeQualityMetrics,
        test_quality: TestQualityMetrics,
        doc_quality: DocumentationQualityMetrics,
        arch_quality: ArchitectureQualityMetrics
    ) -> float:
        """计算整体评分"""
        code_score = self._calculate_code_quality_score(code_quality)
        test_score = test_quality.test_quality_score
        doc_score = doc_quality.doc_quality_score
        arch_score = arch_quality.architecture_quality_score

        weights = {
            "code": 0.35,
            "test": 0.30,
            "doc": 0.15,
            "arch": 0.20
        }

        overall = (
            code_score * weights["code"] +
            test_score * weights["test"] +
            doc_score * weights["doc"] +
            arch_score * weights["arch"]
        )

        return overall

    def _calculate_code_quality_score(self, metrics: CodeQualityMetrics) -> float:
        """计算代码质量评分"""
        score = 100.0

        if metrics.avg_function_complexity > 10:
            score -= (metrics.avg_function_complexity - 10) * 3

        if metrics.code_duplication_rate > 0.05:
            score -= metrics.code_duplication_rate * 100

        score -= metrics.error_count * 5
        score -= metrics.warning_count * 1

        if metrics.code_to_comment_ratio < 0.1:
            score -= 10

        return max(0, min(100, score))

    def _save_collection(self, collection: QualityMetricsCollection, project: str) -> bool:
        """保存指标集合"""
        try:
            storage_file = self.storage_path / project / "metrics_history.json"
            storage_file.parent.mkdir(parents=True, exist_ok=True)

            history = []
            if storage_file.exists():
                with open(storage_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)

            history.append(collection.to_dict())

            with open(storage_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)

            self.logger.info(f"质量指标已保存到 {storage_file}")
            return True

        except Exception as e:
            self.logger.error(f"保存质量指标失败: {e}")
            return False

    def load_history(self, project: str, days: int = 30) -> List[QualityMetricsCollection]:
        """加载历史数据"""
        storage_file = self.storage_path / project / "metrics_history.json"

        if not storage_file.exists():
            return []

        try:
            with open(storage_file, 'r', encoding='utf-8') as f:
                history = json.load(f)

            cutoff_date = datetime.now() - timedelta(days=days)
            collections = []

            for item in history:
                timestamp = datetime.fromisoformat(item["timestamp"])
                if timestamp >= cutoff_date:
                    collection = QualityMetricsCollection(
                        timestamp=item["timestamp"],
                        project=item["project"],
                        code_quality=CodeQualityMetrics(**item.get("code_quality", {})),
                        test_quality=TestQualityMetrics(**item.get("test_quality", {})),
                        documentation_quality=DocumentationQualityMetrics(**item.get("documentation_quality", {})),
                        architecture_quality=ArchitectureQualityMetrics(**item.get("architecture_quality", {})),
                        overall_score=item.get("overall_score", 0),
                        metadata=item.get("metadata", {})
                    )
                    collections.append(collection)

            return sorted(collections, key=lambda x: x.timestamp)

        except Exception as e:
            self.logger.error(f"加载历史数据失败: {e}")
            return []


class QualityTrendAnalyzer:
    """质量趋势分析器"""

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)

    def analyze(
        self,
        historical_data: List[QualityMetricsCollection],
        predict_days: int = 7
    ) -> List[TrendAnalysis]:
        """分析质量趋势"""
        if len(historical_data) < 2:
            return []

        trends = []
        metrics_to_analyze = [
            ("overall_score", lambda c: c.overall_score),
            ("code_quality_score", lambda c: self._get_code_score(c)),
            ("test_quality_score", lambda c: c.test_quality.test_quality_score),
            ("doc_quality_score", lambda c: c.documentation_quality.doc_quality_score),
            ("arch_quality_score", lambda c: c.architecture_quality.architecture_quality_score)
        ]

        for metric_name, extractor in metrics_to_analyze:
            trend = self._analyze_metric(historical_data, metric_name, extractor, predict_days)
            if trend:
                trends.append(trend)

        return trends

    def _get_code_score(self, collection: QualityMetricsCollection) -> float:
        """获取代码质量评分"""
        metrics = collection.code_quality
        score = 100.0

        if metrics.avg_function_complexity > 10:
            score -= (metrics.avg_function_complexity - 10) * 3

        if metrics.code_duplication_rate > 0.05:
            score -= metrics.code_duplication_rate * 100

        score -= metrics.error_count * 5
        score -= metrics.warning_count * 1

        return max(0, min(100, score))

    def _analyze_metric(
        self,
        data: List[QualityMetricsCollection],
        metric_name: str,
        extractor: Callable,
        predict_days: int
    ) -> Optional[TrendAnalysis]:
        """分析单个指标趋势"""
        try:
            values = []
            timestamps = []

            for point in data:
                value = extractor(point)
                values.append(value)
                timestamps.append(datetime.fromisoformat(point.timestamp))

            if len(values) < 2:
                return None

            x = [(t - timestamps[0]).total_seconds() / 86400 for t in timestamps]
            y = values

            n = len(x)
            sum_x = sum(x)
            sum_y = sum(y)
            sum_xy = sum(xi * yi for xi, yi in zip(x, y))
            sum_x2 = sum(xi ** 2 for xi in x)

            denominator = n * sum_x2 - sum_x ** 2
            if denominator == 0:
                slope = 0
                intercept = sum_y / n
            else:
                slope = (n * sum_xy - sum_x * sum_y) / denominator
                intercept = (sum_y - slope * sum_x) / n

            y_mean = sum_y / n
            ss_tot = sum((yi - y_mean) ** 2 for yi in y)
            ss_res = sum((yi - (slope * xi + intercept)) ** 2 for xi, yi in zip(x, y))
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

            last_x = x[-1] if x else 0
            predicted_value = slope * (last_x + predict_days) + intercept

            if abs(slope) < 0.01:
                direction = "stable"
            elif slope > 0:
                direction = "improving"
            else:
                direction = "declining"

            confidence = min(r_squared * min(n / 10, 1.0), 1.0)

            change_rate = (values[-1] - values[0]) / values[0] * 100 if values[0] != 0 else 0

            return TrendAnalysis(
                metric_name=metric_name,
                direction=direction,
                slope=slope,
                current_value=values[-1],
                predicted_value=predicted_value,
                confidence=confidence,
                change_rate=change_rate,
                data_points=n
            )

        except Exception as e:
            self.logger.warning(f"分析趋势 {metric_name} 失败: {e}")
            return None


class QualityGateChecker:
    """质量门禁检查器"""

    def __init__(
        self,
        registry: QualityMetricsRegistry,
        logger: Optional[logging.Logger] = None
    ):
        self.registry = registry
        self.logger = logger or logging.getLogger(__name__)

    def check(self, collection: QualityMetricsCollection) -> QualityGateReport:
        """执行质量门禁检查"""
        gate_results = []

        code_gates = self._check_code_quality_gates(collection.code_quality)
        gate_results.extend(code_gates)

        test_gates = self._check_test_quality_gates(collection.test_quality)
        gate_results.extend(test_gates)

        doc_gates = self._check_documentation_gates(collection.documentation_quality)
        gate_results.extend(doc_gates)

        arch_gates = self._check_architecture_gates(collection.architecture_quality)
        gate_results.extend(arch_gates)

        overall_status = self._determine_overall_status(gate_results)

        passed = sum(1 for g in gate_results if g.status == GateStatus.PASSED)
        failed = sum(1 for g in gate_results if g.status == GateStatus.FAILED)
        warnings = sum(1 for g in gate_results if g.status == GateStatus.WARNING)

        recommendations = self._generate_recommendations(gate_results)

        return QualityGateReport(
            timestamp=datetime.now().isoformat(),
            project=collection.project,
            overall_status=overall_status,
            gate_results=gate_results,
            passed_gates=passed,
            failed_gates=failed,
            warning_gates=warnings,
            quality_score=collection.overall_score,
            recommendations=recommendations
        )

    def _check_code_quality_gates(self, metrics: CodeQualityMetrics) -> List[GateCheckResult]:
        """检查代码质量门禁"""
        results = []

        definition = self.registry.get("cyclomatic_complexity")
        if definition:
            status, severity = self._evaluate_threshold(
                metrics.avg_function_complexity,
                definition.threshold_pass,
                definition.threshold_warning,
                definition.higher_is_better
            )
            results.append(GateCheckResult(
                gate_name="代码复杂度",
                status=status,
                metric_name="avg_function_complexity",
                actual_value=metrics.avg_function_complexity,
                threshold=definition.threshold_pass,
                message=f"平均函数复杂度为 {metrics.avg_function_complexity:.2f}",
                severity=severity,
                suggestions=self._get_complexity_suggestions(status)
            ))

        definition = self.registry.get("code_duplication_rate")
        if definition:
            status, severity = self._evaluate_threshold(
                metrics.code_duplication_rate * 100,
                definition.threshold_pass,
                definition.threshold_warning,
                definition.higher_is_better
            )
            results.append(GateCheckResult(
                gate_name="代码重复",
                status=status,
                metric_name="code_duplication_rate",
                actual_value=metrics.code_duplication_rate * 100,
                threshold=definition.threshold_pass,
                message=f"代码重复率为 {metrics.code_duplication_rate * 100:.2f}%",
                severity=severity,
                suggestions=self._get_duplication_suggestions(status)
            ))

        definition = self.registry.get("error_count")
        if definition:
            status, severity = self._evaluate_threshold(
                metrics.error_count,
                definition.threshold_pass,
                definition.threshold_warning,
                definition.higher_is_better
            )
            results.append(GateCheckResult(
                gate_name="代码违规",
                status=status,
                metric_name="error_count",
                actual_value=metrics.error_count,
                threshold=definition.threshold_pass,
                message=f"发现 {metrics.error_count} 个错误级别违规",
                severity=severity,
                suggestions=self._get_violation_suggestions(status)
            ))

        return results

    def _check_test_quality_gates(self, metrics: TestQualityMetrics) -> List[GateCheckResult]:
        """检查测试质量门禁"""
        results = []

        definition = self.registry.get("line_coverage")
        if definition:
            status, severity = self._evaluate_threshold(
                metrics.line_coverage,
                definition.threshold_pass,
                definition.threshold_warning,
                definition.higher_is_better
            )
            results.append(GateCheckResult(
                gate_name="行覆盖率",
                status=status,
                metric_name="line_coverage",
                actual_value=metrics.line_coverage,
                threshold=definition.threshold_pass,
                message=f"行覆盖率为 {metrics.line_coverage:.2f}%",
                severity=severity,
                suggestions=self._get_coverage_suggestions(status, metrics.line_coverage)
            ))

        definition = self.registry.get("branch_coverage")
        if definition:
            status, severity = self._evaluate_threshold(
                metrics.branch_coverage,
                definition.threshold_pass,
                definition.threshold_warning,
                definition.higher_is_better
            )
            results.append(GateCheckResult(
                gate_name="分支覆盖率",
                status=status,
                metric_name="branch_coverage",
                actual_value=metrics.branch_coverage,
                threshold=definition.threshold_pass,
                message=f"分支覆盖率为 {metrics.branch_coverage:.2f}%",
                severity=severity,
                suggestions=self._get_coverage_suggestions(status, metrics.branch_coverage)
            ))

        definition = self.registry.get("test_pass_rate")
        if definition:
            status, severity = self._evaluate_threshold(
                metrics.test_pass_rate * 100,
                definition.threshold_pass,
                definition.threshold_warning,
                definition.higher_is_better
            )
            results.append(GateCheckResult(
                gate_name="测试通过率",
                status=status,
                metric_name="test_pass_rate",
                actual_value=metrics.test_pass_rate * 100,
                threshold=definition.threshold_pass,
                message=f"测试通过率为 {metrics.test_pass_rate * 100:.2f}%",
                severity=severity,
                suggestions=self._get_test_pass_suggestions(status)
            ))

        return results

    def _check_documentation_gates(self, metrics: DocumentationQualityMetrics) -> List[GateCheckResult]:
        """检查文档质量门禁"""
        results = []

        definition = self.registry.get("documentation_coverage")
        if definition:
            status, severity = self._evaluate_threshold(
                metrics.documentation_coverage,
                definition.threshold_pass,
                definition.threshold_warning,
                definition.higher_is_better
            )
            results.append(GateCheckResult(
                gate_name="文档覆盖率",
                status=status,
                metric_name="documentation_coverage",
                actual_value=metrics.documentation_coverage,
                threshold=definition.threshold_pass,
                message=f"文档覆盖率为 {metrics.documentation_coverage:.2f}%",
                severity=severity,
                suggestions=self._get_doc_suggestions(status)
            ))

        definition = self.registry.get("function_doc_coverage")
        if definition:
            status, severity = self._evaluate_threshold(
                metrics.function_doc_coverage,
                definition.threshold_pass,
                definition.threshold_warning,
                definition.higher_is_better
            )
            results.append(GateCheckResult(
                gate_name="函数文档覆盖率",
                status=status,
                metric_name="function_doc_coverage",
                actual_value=metrics.function_doc_coverage,
                threshold=definition.threshold_pass,
                message=f"函数文档覆盖率为 {metrics.function_doc_coverage:.2f}%",
                severity=severity,
                suggestions=self._get_doc_suggestions(status)
            ))

        return results

    def _check_architecture_gates(self, metrics: ArchitectureQualityMetrics) -> List[GateCheckResult]:
        """检查架构质量门禁"""
        results = []

        definition = self.registry.get("circular_dependencies")
        if definition:
            status, severity = self._evaluate_threshold(
                metrics.circular_dependencies,
                definition.threshold_pass,
                definition.threshold_warning,
                definition.higher_is_better
            )
            results.append(GateCheckResult(
                gate_name="循环依赖",
                status=status,
                metric_name="circular_dependencies",
                actual_value=metrics.circular_dependencies,
                threshold=definition.threshold_pass,
                message=f"发现 {metrics.circular_dependencies} 个循环依赖",
                severity=severity,
                suggestions=self._get_circular_dep_suggestions(status)
            ))

        definition = self.registry.get("coupling_score")
        if definition:
            status, severity = self._evaluate_threshold(
                metrics.coupling_score,
                definition.threshold_pass,
                definition.threshold_warning,
                definition.higher_is_better
            )
            results.append(GateCheckResult(
                gate_name="耦合度",
                status=status,
                metric_name="coupling_score",
                actual_value=metrics.coupling_score,
                threshold=definition.threshold_pass,
                message=f"耦合度评分为 {metrics.coupling_score:.2f}",
                severity=severity,
                suggestions=self._get_coupling_suggestions(status)
            ))

        return results

    def _evaluate_threshold(
        self,
        value: float,
        threshold_pass: float,
        threshold_warning: float,
        higher_is_better: bool
    ) -> Tuple[GateStatus, Severity]:
        """评估阈值"""
        if higher_is_better:
            if value >= threshold_pass:
                return GateStatus.PASSED, Severity.INFO
            elif value >= threshold_warning:
                return GateStatus.WARNING, Severity.MEDIUM
            else:
                return GateStatus.FAILED, Severity.HIGH
        else:
            if value <= threshold_pass:
                return GateStatus.PASSED, Severity.INFO
            elif value <= threshold_warning:
                return GateStatus.WARNING, Severity.MEDIUM
            else:
                return GateStatus.FAILED, Severity.HIGH

    def _determine_overall_status(self, results: List[GateCheckResult]) -> GateStatus:
        """确定整体状态"""
        if any(r.status == GateStatus.FAILED for r in results):
            return GateStatus.FAILED
        elif any(r.status == GateStatus.WARNING for r in results):
            return GateStatus.WARNING
        else:
            return GateStatus.PASSED

    def _generate_recommendations(self, results: List[GateCheckResult]) -> List[str]:
        """生成改进建议"""
        recommendations = []

        failed_results = [r for r in results if r.status == GateStatus.FAILED]
        for result in failed_results[:3]:
            recommendations.extend(result.suggestions[:2])

        warning_results = [r for r in results if r.status == GateStatus.WARNING]
        for result in warning_results[:2]:
            recommendations.extend(result.suggestions[:1])

        return list(dict.fromkeys(recommendations))[:10]

    def _get_complexity_suggestions(self, status: GateStatus) -> List[str]:
        """获取复杂度建议"""
        if status == GateStatus.PASSED:
            return ["继续保持代码简洁"]
        return [
            "重构复杂函数，提取子方法",
            "使用策略模式替代复杂条件判断",
            "减少嵌套层级"
        ]

    def _get_duplication_suggestions(self, status: GateStatus) -> List[str]:
        """获取重复代码建议"""
        if status == GateStatus.PASSED:
            return ["继续保持代码DRY原则"]
        return [
            "提取重复代码到公共方法",
            "使用继承或组合消除重复",
            "应用DRY原则"
        ]

    def _get_violation_suggestions(self, status: GateStatus) -> List[str]:
        """获取违规建议"""
        if status == GateStatus.PASSED:
            return ["继续保持代码规范"]
        return [
            "修复所有错误级别违规",
            "进行代码审查",
            "更新编码规范"
        ]

    def _get_coverage_suggestions(self, status: GateStatus, coverage: float) -> List[str]:
        """获取覆盖率建议"""
        if status == GateStatus.PASSED:
            return ["继续保持测试覆盖率"]
        return [
            f"增加测试用例以达到 {80 - coverage:.0f}% 的覆盖率目标",
            "为未覆盖的代码路径编写测试",
            "关注边界条件和异常情况"
        ]

    def _get_test_pass_suggestions(self, status: GateStatus) -> List[str]:
        """获取测试通过率建议"""
        if status == GateStatus.PASSED:
            return ["继续保持所有测试通过"]
        return [
            "修复失败的测试用例",
            "检查最近的代码变更",
            "确保测试环境正确"
        ]

    def _get_doc_suggestions(self, status: GateStatus) -> List[str]:
        """获取文档建议"""
        if status == GateStatus.PASSED:
            return ["继续保持文档完整"]
        return [
            "为未文档化的函数和类添加文档字符串",
            "补充复杂逻辑的注释",
            "添加使用示例"
        ]

    def _get_circular_dep_suggestions(self, status: GateStatus) -> List[str]:
        """获取循环依赖建议"""
        if status == GateStatus.PASSED:
            return ["继续保持模块独立性"]
        return [
            "重构模块以消除循环依赖",
            "引入中间层或接口",
            "使用依赖注入"
        ]

    def _get_coupling_suggestions(self, status: GateStatus) -> List[str]:
        """获取耦合度建议"""
        if status == GateStatus.PASSED:
            return ["继续保持低耦合"]
        return [
            "减少模块间的直接依赖",
            "使用接口或抽象类",
            "应用依赖倒置原则"
        ]


class ReportGenerator:
    """报告生成器"""

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)

    def generate_metrics_report(self, collection: QualityMetricsCollection, format: str = "json") -> str:
        """生成指标报告"""
        if format == "json":
            return json.dumps(collection.to_dict(), indent=2, ensure_ascii=False)
        elif format == "markdown":
            return self._generate_markdown_report(collection)
        else:
            return json.dumps(collection.to_dict(), indent=2, ensure_ascii=False)

    def generate_gate_report(self, report: QualityGateReport, format: str = "json") -> str:
        """生成门禁报告"""
        if format == "json":
            return json.dumps(report.to_dict(), indent=2, ensure_ascii=False)
        elif format == "markdown":
            return self._generate_gate_markdown(report)
        else:
            return json.dumps(report.to_dict(), indent=2, ensure_ascii=False)

    def _generate_markdown_report(self, collection: QualityMetricsCollection) -> str:
        """生成Markdown格式报告"""
        md = f"""# 质量指标报告

## 概览

| 指标 | 值 |
|------|-----|
| **项目** | {collection.project} |
| **生成时间** | {collection.timestamp} |
| **整体评分** | {collection.overall_score:.2f} |

## 代码质量指标

| 指标 | 值 |
|------|-----|
| 圈复杂度 | {collection.code_quality.cyclomatic_complexity:.2f} |
| 平均函数复杂度 | {collection.code_quality.avg_function_complexity:.2f} |
| 最大嵌套深度 | {collection.code_quality.max_nesting_depth} |
| 代码重复率 | {collection.code_quality.code_duplication_rate * 100:.2f}% |
| 错误数量 | {collection.code_quality.error_count} |
| 警告数量 | {collection.code_quality.warning_count} |
| 代码行数 | {collection.code_quality.code_lines} |
| 注释行数 | {collection.code_quality.comment_lines} |
| 代码注释比 | {collection.code_quality.code_to_comment_ratio:.4f} |

## 测试质量指标

| 指标 | 值 |
|------|-----|
| 行覆盖率 | {collection.test_quality.line_coverage:.2f}% |
| 分支覆盖率 | {collection.test_quality.branch_coverage:.2f}% |
| 函数覆盖率 | {collection.test_quality.function_coverage:.2f}% |
| 测试数量 | {collection.test_quality.test_count} |
| 测试通过率 | {collection.test_quality.test_pass_rate * 100:.2f}% |
| 测试质量评分 | {collection.test_quality.test_quality_score:.2f} |

## 文档质量指标

| 指标 | 值 |
|------|-----|
| 文档覆盖率 | {collection.documentation_quality.documentation_coverage:.2f}% |
| 函数文档覆盖率 | {collection.documentation_quality.function_doc_coverage:.2f}% |
| 类文档覆盖率 | {collection.documentation_quality.class_doc_coverage:.2f}% |
| README存在 | {'是' if collection.documentation_quality.readme_exists else '否'} |
| API文档存在 | {'是' if collection.documentation_quality.api_doc_exists else '否'} |
| 文档质量评分 | {collection.documentation_quality.doc_quality_score:.2f} |

## 架构质量指标

| 指标 | 值 |
|------|-----|
| 模块数量 | {collection.architecture_quality.total_modules} |
| 循环依赖 | {collection.architecture_quality.circular_dependencies} |
| 最大依赖深度 | {collection.architecture_quality.max_dependency_depth} |
| 耦合度评分 | {collection.architecture_quality.coupling_score:.4f} |
| 内聚度评分 | {collection.architecture_quality.cohesion_score:.4f} |
| 架构质量评分 | {collection.architecture_quality.architecture_quality_score:.2f} |

---
*报告由质量指标收集器自动生成*
"""
        return md

    def _generate_gate_markdown(self, report: QualityGateReport) -> str:
        """生成门禁Markdown报告"""
        status_emoji = {
            GateStatus.PASSED: "✅",
            GateStatus.WARNING: "⚠️",
            GateStatus.FAILED: "❌",
            GateStatus.ERROR: "🔴"
        }

        md = f"""# 质量门禁报告

## 概览

| 指标 | 值 |
|------|-----|
| **项目** | {report.project} |
| **生成时间** | {report.timestamp} |
| **整体状态** | {status_emoji.get(report.overall_status, '❓')} {report.overall_status.value.upper()} |
| **质量评分** | {report.quality_score:.2f} |
| **通过门禁** | {report.passed_gates} |
| **警告门禁** | {report.warning_gates} |
| **失败门禁** | {report.failed_gates} |

## 门禁检查结果

| 门禁 | 状态 | 实际值 | 阈值 | 消息 |
|------|------|--------|------|------|
"""
        for gate in report.gate_results:
            emoji = status_emoji.get(gate.status, '❓')
            md += f"| {gate.gate_name} | {emoji} {gate.status.value} | {gate.actual_value:.2f} | {gate.threshold:.2f} | {gate.message} |\n"

        if report.recommendations:
            md += "\n## 改进建议\n\n"
            for i, rec in enumerate(report.recommendations, 1):
                md += f"{i}. {rec}\n"

        md += "\n---\n*报告由质量门禁检查器自动生成*\n"

        return md


def setup_logger(verbose: bool = False) -> logging.Logger:
    """配置日志记录器"""
    logger = logging.getLogger("QualityMetricsCollector")
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG if verbose else logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="质量指标收集器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python quality_metrics_collector.py --project myproject
  python quality_metrics_collector.py --collect-all
  python quality_metrics_collector.py --gate-check
  python quality_metrics_collector.py --trend-analysis --days 30
        """
    )

    parser.add_argument(
        "--project",
        type=str,
        default="default",
        help="项目名称 (默认: default)"
    )

    parser.add_argument(
        "--project-path",
        type=Path,
        default=Path("."),
        help="项目路径 (默认: 当前目录)"
    )

    parser.add_argument(
        "--collect-all",
        action="store_true",
        help="收集所有质量指标"
    )

    parser.add_argument(
        "--gate-check",
        action="store_true",
        help="执行质量门禁检查"
    )

    parser.add_argument(
        "--trend-analysis",
        action="store_true",
        help="执行趋势分析"
    )

    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="历史数据天数 (默认: 30)"
    )

    parser.add_argument(
        "--output",
        choices=["console", "json", "markdown"],
        default="console",
        help="输出格式 (默认: console)"
    )

    parser.add_argument(
        "--output-file",
        type=str,
        help="输出文件路径"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="启用详细日志输出"
    )

    args = parser.parse_args()

    logger = setup_logger(args.verbose)

    print("=" * 80)
    print("质量指标收集器")
    print("=" * 80)

    collector = QualityMetricsCollector(
        project_path=args.project_path,
        logger=logger
    )

    report_generator = ReportGenerator(logger)

    if args.collect_all or not (args.gate_check or args.trend_analysis):
        print(f"\n收集项目 {args.project} 的质量指标...")
        collection = collector.collect_all(args.project)

        if args.output == "console":
            print(f"\n整体评分: {collection.overall_score:.2f}")
            print(f"\n代码质量:")
            print(f"  圈复杂度: {collection.code_quality.cyclomatic_complexity:.2f}")
            print(f"  代码重复率: {collection.code_quality.code_duplication_rate * 100:.2f}%")
            print(f"  错误数量: {collection.code_quality.error_count}")

            print(f"\n测试质量:")
            print(f"  行覆盖率: {collection.test_quality.line_coverage:.2f}%")
            print(f"  分支覆盖率: {collection.test_quality.branch_coverage:.2f}%")
            print(f"  测试数量: {collection.test_quality.test_count}")

            print(f"\n文档质量:")
            print(f"  文档覆盖率: {collection.documentation_quality.documentation_coverage:.2f}%")
            print(f"  函数文档覆盖率: {collection.documentation_quality.function_doc_coverage:.2f}%")

            print(f"\n架构质量:")
            print(f"  循环依赖: {collection.architecture_quality.circular_dependencies}")
            print(f"  耦合度: {collection.architecture_quality.coupling_score:.4f}")

        if args.output_file:
            output_path = Path(args.output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            content = report_generator.generate_metrics_report(collection, args.output if args.output != "console" else "json")
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"\n报告已保存到: {output_path}")

    if args.gate_check:
        print(f"\n执行质量门禁检查...")
        collection = collector.collect_all(args.project)

        gate_checker = QualityGateChecker(collector.registry, logger)
        gate_report = gate_checker.check(collection)

        if args.output == "console":
            status_emoji = {
                GateStatus.PASSED: "✅",
                GateStatus.WARNING: "⚠️",
                GateStatus.FAILED: "❌"
            }
            emoji = status_emoji.get(gate_report.overall_status, "❓")
            print(f"\n门禁状态: {emoji} {gate_report.overall_status.value.upper()}")
            print(f"通过: {gate_report.passed_gates} | 警告: {gate_report.warning_gates} | 失败: {gate_report.failed_gates}")

            print(f"\n门禁详情:")
            for gate in gate_report.gate_results:
                gate_emoji = status_emoji.get(gate.status, "❓")
                print(f"  {gate_emoji} {gate.gate_name}: {gate.message}")

        if args.output_file and not args.collect_all:
            output_path = Path(args.output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            content = report_generator.generate_gate_report(gate_report, args.output if args.output != "console" else "json")
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"\n门禁报告已保存到: {output_path}")

    if args.trend_analysis:
        print(f"\n执行趋势分析...")
        historical_data = collector.load_history(args.project, args.days)

        if len(historical_data) < 2:
            print("历史数据不足，无法进行趋势分析")
        else:
            trend_analyzer = QualityTrendAnalyzer(logger)
            trends = trend_analyzer.analyze(historical_data)

            if args.output == "console":
                print(f"\n趋势分析结果:")
                for trend in trends:
                    direction_icons = {
                        "improving": "📈",
                        "declining": "📉",
                        "stable": "➡️"
                    }
                    icon = direction_icons.get(trend.direction, "❓")
                    print(f"  {icon} {trend.metric_name}: {trend.direction}")
                    print(f"      当前: {trend.current_value:.2f}, 预测: {trend.predicted_value:.2f}")
                    print(f"      置信度: {trend.confidence:.2%}, 变化率: {trend.change_rate:.2f}%")

    return 0


if __name__ == "__main__":
    sys.exit(main())
