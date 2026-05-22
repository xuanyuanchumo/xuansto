#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
质量趋势分析器

实现代码质量数据收集、趋势分析、风险预测和报告生成功能。
支持多种质量指标的历史数据追踪和趋势可视化。

功能模块:
    1. 质量数据收集: 复杂度指标、行数统计、函数/类统计、重复代码检测、规范违规
    2. 质量趋势分析: 历史数据存储、趋势计算、可视化数据生成、异常识别
    3. 质量风险预测: 质量变化预测、风险识别、预警报告生成
    4. 报告生成: JSON格式、Markdown格式、自定义模板

使用示例:
    python quality_trend_analyzer.py --project myproject
    python quality_trend_analyzer.py --days 30 --output json
    python quality_trend_analyzer.py --predict --risk-threshold 0.7
    python quality_trend_analyzer.py --report markdown --template custom.md
"""

import ast
import hashlib
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
    """指标类别枚举"""
    COMPLEXITY = "complexity"
    LINES = "lines"
    STRUCTURE = "structure"
    DUPLICATION = "duplication"
    VIOLATION = "violation"
    COVERAGE = "coverage"


class TrendDirection(Enum):
    """趋势方向枚举"""
    IMPROVING = "improving"
    DECLINING = "declining"
    STABLE = "stable"
    VOLATILE = "volatile"


class RiskLevel(Enum):
    """风险等级枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AnomalyType(Enum):
    """异常类型枚举"""
    SPIKE = "spike"
    DROP = "drop"
    TREND_CHANGE = "trend_change"
    OUTLIER = "outlier"


@dataclass
class ComplexityMetrics:
    """复杂度指标数据类"""
    cyclomatic_complexity: float = 0.0
    cognitive_complexity: float = 0.0
    max_nesting_depth: int = 0
    avg_function_complexity: float = 0.0
    high_complexity_functions: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cyclomatic_complexity": round(self.cyclomatic_complexity, 2),
            "cognitive_complexity": round(self.cognitive_complexity, 2),
            "max_nesting_depth": self.max_nesting_depth,
            "avg_function_complexity": round(self.avg_function_complexity, 2),
            "high_complexity_functions": self.high_complexity_functions
        }


@dataclass
class LinesMetrics:
    """代码行数统计数据类"""
    total_lines: int = 0
    code_lines: int = 0
    comment_lines: int = 0
    blank_lines: int = 0
    code_to_comment_ratio: float = 0.0
    avg_file_lines: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_lines": self.total_lines,
            "code_lines": self.code_lines,
            "comment_lines": self.comment_lines,
            "blank_lines": self.blank_lines,
            "code_to_comment_ratio": round(self.code_to_comment_ratio, 4),
            "avg_file_lines": round(self.avg_file_lines, 2)
        }


@dataclass
class StructureMetrics:
    """代码结构统计数据类"""
    total_functions: int = 0
    total_classes: int = 0
    avg_function_length: float = 0.0
    avg_class_methods: float = 0.0
    max_function_length: int = 0
    max_class_methods: int = 0
    long_functions: List[Dict[str, Any]] = field(default_factory=list)
    large_classes: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_functions": self.total_functions,
            "total_classes": self.total_classes,
            "avg_function_length": round(self.avg_function_length, 2),
            "avg_class_methods": round(self.avg_class_methods, 2),
            "max_function_length": self.max_function_length,
            "max_class_methods": self.max_class_methods,
            "long_functions": self.long_functions,
            "large_classes": self.large_classes
        }


@dataclass
class DuplicationMetrics:
    """重复代码检测数据类"""
    duplication_rate: float = 0.0
    duplicated_blocks: int = 0
    duplicated_lines: int = 0
    total_lines_analyzed: int = 0
    duplication_hotspots: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "duplication_rate": round(self.duplication_rate, 4),
            "duplicated_blocks": self.duplicated_blocks,
            "duplicated_lines": self.duplicated_lines,
            "total_lines_analyzed": self.total_lines_analyzed,
            "duplication_hotspots": self.duplication_hotspots
        }


@dataclass
class ViolationMetrics:
    """代码规范违规数据类"""
    total_violations: int = 0
    error_count: int = 0
    warning_count: int = 0
    info_count: int = 0
    violations_by_type: Dict[str, int] = field(default_factory=dict)
    violations_by_file: Dict[str, int] = field(default_factory=dict)
    top_violations: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_violations": self.total_violations,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "info_count": self.info_count,
            "violations_by_type": self.violations_by_type,
            "violations_by_file": dict(list(self.violations_by_file.items())[:20]),
            "top_violations": self.top_violations
        }


@dataclass
class QualityDataPoint:
    """质量数据点数据类"""
    timestamp: str
    project: str
    complexity: ComplexityMetrics
    lines: LinesMetrics
    structure: StructureMetrics
    duplication: DuplicationMetrics
    violations: ViolationMetrics
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "project": self.project,
            "complexity": self.complexity.to_dict(),
            "lines": self.lines.to_dict(),
            "structure": self.structure.to_dict(),
            "duplication": self.duplication.to_dict(),
            "violations": self.violations.to_dict(),
            "metadata": self.metadata
        }


@dataclass
class TrendAnalysis:
    """趋势分析结果数据类"""
    metric_name: str
    category: MetricCategory
    direction: TrendDirection
    slope: float
    r_squared: float
    current_value: float
    predicted_value: float
    confidence: float
    data_points: int
    time_range_days: int
    change_rate: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "category": self.category.value,
            "direction": self.direction.value,
            "slope": round(self.slope, 6),
            "r_squared": round(self.r_squared, 4),
            "current_value": round(self.current_value, 4),
            "predicted_value": round(self.predicted_value, 4),
            "confidence": round(self.confidence, 4),
            "data_points": self.data_points,
            "time_range_days": self.time_range_days,
            "change_rate": round(self.change_rate, 4)
        }


@dataclass
class Anomaly:
    """异常检测结果数据类"""
    anomaly_type: AnomalyType
    metric_name: str
    timestamp: str
    value: float
    expected_value: float
    deviation: float
    severity: str
    description: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "anomaly_type": self.anomaly_type.value,
            "metric_name": self.metric_name,
            "timestamp": self.timestamp,
            "value": round(self.value, 4),
            "expected_value": round(self.expected_value, 4),
            "deviation": round(self.deviation, 4),
            "severity": self.severity,
            "description": self.description
        }


@dataclass
class RiskPrediction:
    """风险预测数据类"""
    risk_level: RiskLevel
    metric_name: str
    probability: float
    description: str
    affected_components: List[str]
    mitigation_suggestions: List[str]
    time_frame: str
    predicted_impact: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "risk_level": self.risk_level.value,
            "metric_name": self.metric_name,
            "probability": round(self.probability, 4),
            "description": self.description,
            "affected_components": self.affected_components,
            "mitigation_suggestions": self.mitigation_suggestions,
            "time_frame": self.time_frame,
            "predicted_impact": self.predicted_impact
        }


@dataclass
class VisualizationData:
    """可视化数据数据类"""
    chart_type: str
    title: str
    labels: List[str]
    datasets: List[Dict[str, Any]]
    options: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chart_type": self.chart_type,
            "title": self.title,
            "labels": self.labels,
            "datasets": self.datasets,
            "options": self.options
        }


@dataclass
class QualityTrendReport:
    """质量趋势报告数据类"""
    timestamp: str
    project: str
    current_data: QualityDataPoint
    historical_data: List[QualityDataPoint]
    trends: List[TrendAnalysis]
    anomalies: List[Anomaly]
    risks: List[RiskPrediction]
    visualization_data: List[VisualizationData]
    overall_score: float
    health_status: str
    recommendations: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "project": self.project,
            "current_data": self.current_data.to_dict(),
            "historical_data": [d.to_dict() for d in self.historical_data],
            "trends": [t.to_dict() for t in self.trends],
            "anomalies": [a.to_dict() for a in self.anomalies],
            "risks": [r.to_dict() for r in self.risks],
            "visualization_data": [v.to_dict() for v in self.visualization_data],
            "overall_score": round(self.overall_score, 2),
            "health_status": self.health_status,
            "recommendations": self.recommendations
        }


class ComplexityAnalyzer:
    """代码复杂度分析器"""

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)

    def analyze(self, file_path: Path) -> Tuple[float, float, int, List[Dict[str, Any]]]:
        """
        分析单个文件的复杂度
        
        Args:
            file_path: 文件路径
            
        Returns:
            Tuple[圈复杂度, 认知复杂度, 最大嵌套深度, 高复杂度函数列表]
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            cyclomatic = self._calculate_cyclomatic_complexity(tree)
            cognitive, max_nesting = self._calculate_cognitive_complexity(tree, content)
            high_complexity_funcs = self._find_high_complexity_functions(tree, content)
            
            return cyclomatic, cognitive, max_nesting, high_complexity_funcs
            
        except Exception as e:
            self.logger.warning(f"分析文件 {file_path} 失败: {e}")
            return 0.0, 0.0, 0, []

    def _calculate_cyclomatic_complexity(self, tree: ast.AST) -> float:
        """计算圈复杂度"""
        complexity = 1
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
            elif isinstance(node, (ast.And, ast.Or)):
                complexity += 1
        
        return float(complexity)

    def _calculate_cognitive_complexity(self, tree: ast.AST, content: str) -> Tuple[float, int]:
        """计算认知复杂度和最大嵌套深度"""
        cognitive = 0
        max_nesting = 0
        
        def visit_node(node: ast.AST, nesting_level: int = 0) -> None:
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

    def _find_high_complexity_functions(self, tree: ast.AST, content: str) -> List[Dict[str, Any]]:
        """查找高复杂度函数"""
        high_complexity = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_complexity = self._calculate_function_complexity(node)
                if func_complexity > 10:
                    high_complexity.append({
                        "name": node.name,
                        "line": node.lineno,
                        "complexity": func_complexity,
                        "type": "function"
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


class LinesAnalyzer:
    """代码行数分析器"""

    def analyze(self, file_path: Path) -> Tuple[int, int, int, int]:
        """
        分析单个文件的行数统计
        
        Args:
            file_path: 文件路径
            
        Returns:
            Tuple[总行数, 代码行数, 注释行数, 空行数]
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            total = len(lines)
            code = 0
            comments = 0
            blank = 0
            
            in_multiline_string = False
            multiline_char = None
            
            for line in lines:
                stripped = line.strip()
                
                if not stripped:
                    blank += 1
                elif stripped.startswith('#'):
                    comments += 1
                elif in_multiline_string:
                    comments += 1
                    if multiline_char in stripped:
                        in_multiline_string = False
                elif stripped.startswith(('"""', "'''")):
                    comments += 1
                    multiline_char = stripped[:3]
                    if stripped.count(multiline_char) == 1:
                        in_multiline_string = True
                else:
                    code += 1
            
            return total, code, comments, blank
            
        except Exception:
            return 0, 0, 0, 0


class StructureAnalyzer:
    """代码结构分析器"""

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)

    def analyze(self, file_path: Path) -> Tuple[int, int, List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        分析单个文件的结构
        
        Args:
            file_path: 文件路径
            
        Returns:
            Tuple[函数数量, 类数量, 长函数列表, 大类列表]
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')
            
            tree = ast.parse(content)
            
            functions = []
            classes = []
            long_functions = []
            large_classes = []
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    func_length = self._get_node_length(node, lines)
                    functions.append({
                        "name": node.name,
                        "line": node.lineno,
                        "length": func_length
                    })
                    if func_length > 50:
                        long_functions.append({
                            "name": node.name,
                            "line": node.lineno,
                            "length": func_length,
                            "file": str(file_path)
                        })
                
                elif isinstance(node, ast.ClassDef):
                    methods = [n for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
                    classes.append({
                        "name": node.name,
                        "line": node.lineno,
                        "methods": len(methods)
                    })
                    if len(methods) > 20:
                        large_classes.append({
                            "name": node.name,
                            "line": node.lineno,
                            "methods": len(methods),
                            "file": str(file_path)
                        })
            
            return len(functions), len(classes), long_functions, large_classes
            
        except Exception as e:
            self.logger.warning(f"分析文件结构 {file_path} 失败: {e}")
            return 0, 0, [], []

    def _get_node_length(self, node: ast.AST, lines: List[str]) -> int:
        """获取节点长度"""
        if hasattr(node, 'end_lineno') and node.end_lineno:
            return node.end_lineno - node.lineno + 1
        return 1


class DuplicationDetector:
    """重复代码检测器"""

    def __init__(self, min_lines: int = 6, logger: Optional[logging.Logger] = None):
        self.min_lines = min_lines
        self.logger = logger or logging.getLogger(__name__)

    def detect(self, file_paths: List[Path]) -> DuplicationMetrics:
        """
        检测重复代码
        
        Args:
            file_paths: 文件路径列表
            
        Returns:
            重复代码指标
        """
        code_blocks: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        total_lines = 0
        
        for file_path in file_paths:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                
                total_lines += len(lines)
                
                for i in range(len(lines) - self.min_lines + 1):
                    block = ''.join(lines[i:i + self.min_lines])
                    block_hash = hashlib.md5(block.encode()).hexdigest()
                    
                    code_blocks[block_hash].append({
                        "file": str(file_path),
                        "start_line": i + 1,
                        "end_line": i + self.min_lines
                    })
                    
            except Exception as e:
                self.logger.warning(f"检测文件 {file_path} 重复代码失败: {e}")
        
        duplicated_blocks = 0
        duplicated_lines = 0
        hotspots = []
        
        for block_hash, locations in code_blocks.items():
            if len(locations) > 1:
                duplicated_blocks += len(locations)
                duplicated_lines += len(locations) * self.min_lines
                
                if len(locations) > 2:
                    hotspots.append({
                        "locations": locations,
                        "occurrences": len(locations),
                        "lines": self.min_lines
                    })
        
        hotspots.sort(key=lambda x: x["occurrences"], reverse=True)
        
        duplication_rate = duplicated_lines / total_lines if total_lines > 0 else 0
        
        return DuplicationMetrics(
            duplication_rate=duplication_rate,
            duplicated_blocks=duplicated_blocks,
            duplicated_lines=duplicated_lines,
            total_lines_analyzed=total_lines,
            duplication_hotspots=hotspots[:10]
        )


class ViolationDetector:
    """代码规范违规检测器"""

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.violation_patterns = self._load_violation_patterns()

    def _load_violation_patterns(self) -> List[Dict[str, Any]]:
        """加载违规检测模式"""
        return [
            {
                "id": "E001",
                "name": "missing_docstring",
                "pattern": r"^(def|class)\s+\w+.*:\s*$",
                "check": lambda m, lines, i: i + 1 < len(lines) and '"""' not in lines[i + 1] and "'''" not in lines[i + 1],
                "severity": "warning",
                "message": "缺少文档字符串"
            },
            {
                "id": "E002",
                "name": "long_line",
                "pattern": r"^.{121,}",
                "severity": "warning",
                "message": "行长度超过120字符"
            },
            {
                "id": "E003",
                "name": "trailing_whitespace",
                "pattern": r".*\s+$",
                "severity": "info",
                "message": "行尾空白字符"
            },
            {
                "id": "E004",
                "name": "multiple_imports",
                "pattern": r"^from\s+\S+\s+import\s+[^,]+,",
                "severity": "warning",
                "message": "多行导入应分开"
            },
            {
                "id": "E005",
                "name": "bare_except",
                "pattern": r"except\s*:",
                "severity": "error",
                "message": "不应使用裸except"
            },
            {
                "id": "E006",
                "name": "todo_without_issue",
                "pattern": r"#\s*TODO",
                "severity": "info",
                "message": "TODO注释应关联issue"
            },
            {
                "id": "E007",
                "name": "magic_number",
                "pattern": r"(?<!['\"])\b\d{2,}\b(?!['\"])",
                "severity": "info",
                "message": "魔法数字应定义为常量"
            }
        ]

    def detect(self, file_path: Path) -> ViolationMetrics:
        """
        检测代码规范违规
        
        Args:
            file_path: 文件路径
            
        Returns:
            违规指标
        """
        violations_by_type: Dict[str, int] = defaultdict(int)
        violations_by_file: Dict[str, int] = defaultdict(int)
        top_violations = []
        total_violations = 0
        error_count = 0
        warning_count = 0
        info_count = 0
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            for i, line in enumerate(lines, 1):
                for pattern_info in self.violation_patterns:
                    pattern = pattern_info["pattern"]
                    if re.search(pattern, line):
                        check_func = pattern_info.get("check")
                        if check_func and not check_func(None, lines, i - 1):
                            continue
                        
                        severity = pattern_info["severity"]
                        violation = {
                            "id": pattern_info["id"],
                            "name": pattern_info["name"],
                            "file": str(file_path),
                            "line": i,
                            "severity": severity,
                            "message": pattern_info["message"]
                        }
                        
                        top_violations.append(violation)
                        violations_by_type[pattern_info["name"]] += 1
                        total_violations += 1
                        
                        if severity == "error":
                            error_count += 1
                        elif severity == "warning":
                            warning_count += 1
                        else:
                            info_count += 1
            
            violations_by_file[str(file_path)] = total_violations
            
        except Exception as e:
            self.logger.warning(f"检测文件 {file_path} 违规失败: {e}")
        
        return ViolationMetrics(
            total_violations=total_violations,
            error_count=error_count,
            warning_count=warning_count,
            info_count=info_count,
            violations_by_type=dict(violations_by_type),
            violations_by_file=dict(violations_by_file),
            top_violations=top_violations[:50]
        )


class QualityDataCollector:
    """质量数据收集器"""

    def __init__(
        self,
        project_path: Path,
        storage_path: Optional[Path] = None,
        logger: Optional[logging.Logger] = None
    ):
        self.project_path = project_path
        self.storage_path = storage_path or project_path / "quality_data"
        self.logger = logger or logging.getLogger(__name__)
        
        self.complexity_analyzer = ComplexityAnalyzer(logger)
        self.lines_analyzer = LinesAnalyzer()
        self.structure_analyzer = StructureAnalyzer(logger)
        self.duplication_detector = DuplicationDetector(logger=logger)
        self.violation_detector = ViolationDetector(logger)

    def collect(self, project: str = "default") -> QualityDataPoint:
        """
        收集项目质量数据
        
        Args:
            project: 项目名称
            
        Returns:
            质量数据点
        """
        self.logger.info(f"开始收集项目 {project} 的质量数据")
        
        python_files = list(self.project_path.rglob("*.py"))
        python_files = [f for f in python_files if not any(part.startswith('.') for part in f.parts)]
        python_files = [f for f in python_files if 'venv' not in str(f).lower() and '__pycache__' not in str(f)]
        
        if not python_files:
            self.logger.warning(f"项目 {project} 中未找到Python文件")
            return self._create_empty_data_point(project)
        
        complexity_metrics = self._collect_complexity_metrics(python_files)
        lines_metrics = self._collect_lines_metrics(python_files)
        structure_metrics = self._collect_structure_metrics(python_files)
        duplication_metrics = self.duplication_detector.detect(python_files)
        violation_metrics = self._collect_violation_metrics(python_files)
        
        data_point = QualityDataPoint(
            timestamp=datetime.now().isoformat(),
            project=project,
            complexity=complexity_metrics,
            lines=lines_metrics,
            structure=structure_metrics,
            duplication=duplication_metrics,
            violations=violation_metrics,
            metadata={
                "files_analyzed": len(python_files),
                "analyzer_version": "2.0.0"
            }
        )
        
        self._save_data_point(data_point, project)
        
        return data_point

    def _collect_complexity_metrics(self, file_paths: List[Path]) -> ComplexityMetrics:
        """收集复杂度指标"""
        total_cyclomatic = 0.0
        total_cognitive = 0.0
        max_nesting = 0
        all_high_complexity = []
        function_count = 0
        
        for file_path in file_paths:
            cyclomatic, cognitive, nesting, high_complexity = self.complexity_analyzer.analyze(file_path)
            total_cyclomatic += cyclomatic
            total_cognitive += cognitive
            max_nesting = max(max_nesting, nesting)
            all_high_complexity.extend([
                {**hc, "file": str(file_path)} for hc in high_complexity
            ])
            function_count += len(high_complexity) if high_complexity else 1
        
        avg_complexity = total_cyclomatic / len(file_paths) if file_paths else 0
        
        return ComplexityMetrics(
            cyclomatic_complexity=total_cyclomatic,
            cognitive_complexity=total_cognitive,
            max_nesting_depth=max_nesting,
            avg_function_complexity=avg_complexity,
            high_complexity_functions=sorted(all_high_complexity, key=lambda x: x["complexity"], reverse=True)[:20]
        )

    def _collect_lines_metrics(self, file_paths: List[Path]) -> LinesMetrics:
        """收集行数统计"""
        total_lines = 0
        total_code = 0
        total_comments = 0
        total_blank = 0
        
        for file_path in file_paths:
            lines, code, comments, blank = self.lines_analyzer.analyze(file_path)
            total_lines += lines
            total_code += code
            total_comments += comments
            total_blank += blank
        
        code_to_comment_ratio = total_comments / total_code if total_code > 0 else 0
        avg_file_lines = total_lines / len(file_paths) if file_paths else 0
        
        return LinesMetrics(
            total_lines=total_lines,
            code_lines=total_code,
            comment_lines=total_comments,
            blank_lines=total_blank,
            code_to_comment_ratio=code_to_comment_ratio,
            avg_file_lines=avg_file_lines
        )

    def _collect_structure_metrics(self, file_paths: List[Path]) -> StructureMetrics:
        """收集结构统计"""
        total_functions = 0
        total_classes = 0
        all_long_functions = []
        all_large_classes = []
        function_lengths = []
        class_methods = []
        
        for file_path in file_paths:
            funcs, classes, long_funcs, large_classes = self.structure_analyzer.analyze(file_path)
            total_functions += funcs
            total_classes += classes
            all_long_functions.extend(long_funcs)
            all_large_classes.extend(large_classes)
            
            for lf in long_funcs:
                function_lengths.append(lf["length"])
            for lc in large_classes:
                class_methods.append(lc["methods"])
        
        avg_func_length = sum(function_lengths) / len(function_lengths) if function_lengths else 0
        avg_class_methods = sum(class_methods) / len(class_methods) if class_methods else 0
        max_func_length = max(function_lengths) if function_lengths else 0
        max_class_methods = max(class_methods) if class_methods else 0
        
        return StructureMetrics(
            total_functions=total_functions,
            total_classes=total_classes,
            avg_function_length=avg_func_length,
            avg_class_methods=avg_class_methods,
            max_function_length=max_func_length,
            max_class_methods=max_class_methods,
            long_functions=sorted(all_long_functions, key=lambda x: x["length"], reverse=True)[:20],
            large_classes=sorted(all_large_classes, key=lambda x: x["methods"], reverse=True)[:20]
        )

    def _collect_violation_metrics(self, file_paths: List[Path]) -> ViolationMetrics:
        """收集违规指标"""
        total_metrics = ViolationMetrics()
        
        for file_path in file_paths:
            metrics = self.violation_detector.detect(file_path)
            total_metrics.total_violations += metrics.total_violations
            total_metrics.error_count += metrics.error_count
            total_metrics.warning_count += metrics.warning_count
            total_metrics.info_count += metrics.info_count
            
            for vtype, count in metrics.violations_by_type.items():
                total_metrics.violations_by_type[vtype] = total_metrics.violations_by_type.get(vtype, 0) + count
            
            for vfile, count in metrics.violations_by_file.items():
                total_metrics.violations_by_file[vfile] = count
            
            total_metrics.top_violations.extend(metrics.top_violations)
        
        total_metrics.top_violations = sorted(
            total_metrics.top_violations,
            key=lambda x: {"error": 0, "warning": 1, "info": 2}.get(x["severity"], 3)
        )[:50]
        
        return total_metrics

    def _create_empty_data_point(self, project: str) -> QualityDataPoint:
        """创建空数据点"""
        return QualityDataPoint(
            timestamp=datetime.now().isoformat(),
            project=project,
            complexity=ComplexityMetrics(),
            lines=LinesMetrics(),
            structure=StructureMetrics(),
            duplication=DuplicationMetrics(),
            violations=ViolationMetrics()
        )

    def _save_data_point(self, data_point: QualityDataPoint, project: str) -> bool:
        """保存数据点"""
        try:
            storage_file = self.storage_path / project / "quality_history.json"
            storage_file.parent.mkdir(parents=True, exist_ok=True)
            
            history = []
            if storage_file.exists():
                with open(storage_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            
            history.append(data_point.to_dict())
            
            with open(storage_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"质量数据已保存到 {storage_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"保存质量数据失败: {e}")
            return False

    def load_historical(self, project: str, days: int = 30) -> List[QualityDataPoint]:
        """
        加载历史数据
        
        Args:
            project: 项目名称
            days: 天数
            
        Returns:
            历史数据点列表
        """
        storage_file = self.storage_path / project / "quality_history.json"
        
        if not storage_file.exists():
            return []
        
        try:
            with open(storage_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
            
            cutoff_date = datetime.now() - timedelta(days=days)
            data_points = []
            
            for item in history:
                timestamp = datetime.fromisoformat(item["timestamp"])
                if timestamp >= cutoff_date:
                    data_point = QualityDataPoint(
                        timestamp=item["timestamp"],
                        project=item["project"],
                        complexity=ComplexityMetrics(**item.get("complexity", {})),
                        lines=LinesMetrics(**item.get("lines", {})),
                        structure=StructureMetrics(**item.get("structure", {})),
                        duplication=DuplicationMetrics(**item.get("duplication", {})),
                        violations=ViolationMetrics(**item.get("violations", {})),
                        metadata=item.get("metadata", {})
                    )
                    data_points.append(data_point)
            
            return sorted(data_points, key=lambda x: x.timestamp)
            
        except Exception as e:
            self.logger.error(f"加载历史数据失败: {e}")
            return []


class TrendCalculator:
    """趋势计算器"""

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)

    def calculate_trends(
        self,
        historical_data: List[QualityDataPoint],
        predict_days: int = 7
    ) -> List[TrendAnalysis]:
        """
        计算质量指标趋势
        
        Args:
            historical_data: 历史数据列表
            predict_days: 预测天数
            
        Returns:
            趋势分析列表
        """
        if len(historical_data) < 2:
            return []
        
        trends = []
        metrics_config = self._get_metrics_config()
        
        for category, metrics in metrics_config.items():
            for metric_name, extractor in metrics.items():
                trend = self._calculate_single_trend(
                    historical_data, metric_name, category, extractor, predict_days
                )
                if trend:
                    trends.append(trend)
        
        return trends

    def _get_metrics_config(self) -> Dict[MetricCategory, Dict[str, Callable]]:
        """获取指标配置"""
        return {
            MetricCategory.COMPLEXITY: {
                "cyclomatic_complexity": lambda d: d.complexity.cyclomatic_complexity,
                "cognitive_complexity": lambda d: d.complexity.cognitive_complexity,
                "max_nesting_depth": lambda d: d.complexity.max_nesting_depth,
                "avg_function_complexity": lambda d: d.complexity.avg_function_complexity
            },
            MetricCategory.LINES: {
                "total_lines": lambda d: d.lines.total_lines,
                "code_lines": lambda d: d.lines.code_lines,
                "comment_lines": lambda d: d.lines.comment_lines,
                "code_to_comment_ratio": lambda d: d.lines.code_to_comment_ratio
            },
            MetricCategory.STRUCTURE: {
                "total_functions": lambda d: d.structure.total_functions,
                "total_classes": lambda d: d.structure.total_classes,
                "avg_function_length": lambda d: d.structure.avg_function_length
            },
            MetricCategory.DUPLICATION: {
                "duplication_rate": lambda d: d.duplication.duplication_rate,
                "duplicated_blocks": lambda d: d.duplication.duplicated_blocks
            },
            MetricCategory.VIOLATION: {
                "total_violations": lambda d: d.violations.total_violations,
                "error_count": lambda d: d.violations.error_count,
                "warning_count": lambda d: d.violations.warning_count
            }
        }

    def _calculate_single_trend(
        self,
        data: List[QualityDataPoint],
        metric_name: str,
        category: MetricCategory,
        extractor: Callable,
        predict_days: int
    ) -> Optional[TrendAnalysis]:
        """计算单个指标趋势"""
        try:
            values = []
            timestamps = []
            
            for point in data:
                value = extractor(point)
                if value is not None:
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
            
            direction = self._determine_direction(slope, metric_name)
            confidence = self._calculate_confidence(r_squared, n)
            
            time_range = (timestamps[-1] - timestamps[0]).days
            
            change_rate = (values[-1] - values[0]) / values[0] * 100 if values[0] != 0 else 0
            
            return TrendAnalysis(
                metric_name=metric_name,
                category=category,
                direction=direction,
                slope=slope,
                r_squared=r_squared,
                current_value=values[-1],
                predicted_value=predicted_value,
                confidence=confidence,
                data_points=n,
                time_range_days=time_range,
                change_rate=change_rate
            )
            
        except Exception as e:
            self.logger.warning(f"计算趋势 {metric_name} 失败: {e}")
            return None

    def _determine_direction(self, slope: float, metric_name: str) -> TrendDirection:
        """确定趋势方向"""
        abs_slope = abs(slope)
        if abs_slope < 0.01:
            return TrendDirection.STABLE
        
        higher_is_better = metric_name in [
            "code_to_comment_ratio",
            "total_functions",
            "total_classes"
        ]
        
        lower_is_better = metric_name in [
            "cyclomatic_complexity",
            "cognitive_complexity",
            "max_nesting_depth",
            "avg_function_complexity",
            "duplication_rate",
            "duplicated_blocks",
            "total_violations",
            "error_count",
            "warning_count",
            "avg_function_length"
        ]
        
        if higher_is_better:
            return TrendDirection.IMPROVING if slope > 0 else TrendDirection.DECLINING
        elif lower_is_better:
            return TrendDirection.IMPROVING if slope < 0 else TrendDirection.DECLINING
        else:
            return TrendDirection.VOLATILE

    def _calculate_confidence(self, r_squared: float, data_points: int) -> float:
        """计算置信度"""
        point_factor = min(data_points / 30, 1.0)
        return r_squared * point_factor


class AnomalyDetector:
    """异常检测器"""

    def __init__(self, threshold: float = 2.0, logger: Optional[logging.Logger] = None):
        self.threshold = threshold
        self.logger = logger or logging.getLogger(__name__)

    def detect(
        self,
        historical_data: List[QualityDataPoint],
        trends: List[TrendAnalysis]
    ) -> List[Anomaly]:
        """
        检测异常
        
        Args:
            historical_data: 历史数据
            trends: 趋势分析结果
            
        Returns:
            异常列表
        """
        anomalies = []
        
        if len(historical_data) < 3:
            return anomalies
        
        metrics_extractors = self._get_metrics_extractors()
        
        for metric_name, extractor in metrics_extractors.items():
            values = [extractor(d) for d in historical_data]
            timestamps = [d.timestamp for d in historical_data]
            
            metric_anomalies = self._detect_metric_anomalies(
                metric_name, values, timestamps
            )
            anomalies.extend(metric_anomalies)
        
        return anomalies

    def _get_metrics_extractors(self) -> Dict[str, Callable]:
        """获取指标提取器"""
        return {
            "cyclomatic_complexity": lambda d: d.complexity.cyclomatic_complexity,
            "duplication_rate": lambda d: d.duplication.duplication_rate,
            "total_violations": lambda d: d.violations.total_violations,
            "error_count": lambda d: d.violations.error_count,
            "avg_function_complexity": lambda d: d.complexity.avg_function_complexity
        }

    def _detect_metric_anomalies(
        self,
        metric_name: str,
        values: List[float],
        timestamps: List[str]
    ) -> List[Anomaly]:
        """检测单个指标的异常"""
        anomalies = []
        
        if len(values) < 3:
            return anomalies
        
        mean = statistics.mean(values[:-1])
        std = statistics.stdev(values[:-1]) if len(values) > 2 else 0
        
        if std == 0:
            return anomalies
        
        last_value = values[-1]
        z_score = abs(last_value - mean) / std
        
        if z_score > self.threshold:
            anomaly_type = AnomalyType.SPIKE if last_value > mean else AnomalyType.DROP
            
            anomalies.append(Anomaly(
                anomaly_type=anomaly_type,
                metric_name=metric_name,
                timestamp=timestamps[-1],
                value=last_value,
                expected_value=mean,
                deviation=z_score,
                severity="high" if z_score > 3 else "medium" if z_score > 2.5 else "low",
                description=f"{metric_name} 出现{'突增' if last_value > mean else '骤降'}，偏离均值 {z_score:.2f} 个标准差"
            ))
        
        return anomalies


class RiskPredictor:
    """风险预测器"""

    def __init__(
        self,
        risk_threshold: float = 0.7,
        logger: Optional[logging.Logger] = None
    ):
        self.risk_threshold = risk_threshold
        self.logger = logger or logging.getLogger(__name__)

    def predict(
        self,
        trends: List[TrendAnalysis],
        current_data: QualityDataPoint,
        anomalies: List[Anomaly]
    ) -> List[RiskPrediction]:
        """
        预测风险
        
        Args:
            trends: 趋势分析结果
            current_data: 当前数据
            anomalies: 异常列表
            
        Returns:
            风险预测列表
        """
        risks = []
        
        for trend in trends:
            if trend.direction == TrendDirection.DECLINING and trend.confidence >= 0.5:
                risk = self._analyze_trend_risk(trend)
                if risk:
                    risks.append(risk)
        
        threshold_risks = self._check_threshold_risks(current_data)
        risks.extend(threshold_risks)
        
        anomaly_risks = self._analyze_anomaly_risks(anomalies)
        risks.extend(anomaly_risks)
        
        return sorted(risks, key=lambda r: r.probability, reverse=True)

    def _analyze_trend_risk(self, trend: TrendAnalysis) -> Optional[RiskPrediction]:
        """分析趋势风险"""
        decline_rate = abs(trend.change_rate)
        probability = min(decline_rate / 100 * trend.confidence + 0.3, 1.0)
        
        if probability < self.risk_threshold:
            return None
        
        risk_level = self._determine_risk_level(probability)
        
        return RiskPrediction(
            risk_level=risk_level,
            metric_name=trend.metric_name,
            probability=probability,
            description=f"{trend.metric_name} 指标呈下降趋势，预计未来将继续恶化",
            affected_components=["代码质量"],
            mitigation_suggestions=self._get_mitigation_suggestions(trend.metric_name),
            time_frame="7-14天",
            predicted_impact="质量下降" if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL] else "质量波动"
        )

    def _check_threshold_risks(self, data: QualityDataPoint) -> List[RiskPrediction]:
        """检查阈值风险"""
        risks = []
        
        thresholds = {
            "cyclomatic_complexity": (data.complexity.cyclomatic_complexity, 100, False),
            "avg_function_complexity": (data.complexity.avg_function_complexity, 15, False),
            "max_nesting_depth": (data.complexity.max_nesting_depth, 5, False),
            "duplication_rate": (data.duplication.duplication_rate, 0.05, False),
            "error_count": (data.violations.error_count, 0, False),
            "code_to_comment_ratio": (data.lines.code_to_comment_ratio, 0.1, True)
        }
        
        for metric_name, (value, threshold, higher_is_better) in thresholds.items():
            if higher_is_better:
                violation = value < threshold
                deviation = (threshold - value) / threshold if threshold > 0 else 0
            else:
                violation = value > threshold
                deviation = (value - threshold) / threshold if threshold > 0 else 0
            
            if violation:
                probability = min(deviation + 0.3, 1.0)
                risk_level = self._determine_risk_level(probability)
                
                risks.append(RiskPrediction(
                    risk_level=risk_level,
                    metric_name=metric_name,
                    probability=probability,
                    description=f"{metric_name} 当前值 {value:.2f} 超出阈值 {threshold}",
                    affected_components=["代码质量"],
                    mitigation_suggestions=self._get_mitigation_suggestions(metric_name),
                    time_frame="立即",
                    predicted_impact="质量风险"
                ))
        
        return risks

    def _analyze_anomaly_risks(self, anomalies: List[Anomaly]) -> List[RiskPrediction]:
        """分析异常风险"""
        risks = []
        
        for anomaly in anomalies:
            if anomaly.severity in ["high", "medium"]:
                probability = min(anomaly.deviation / 5, 1.0)
                risk_level = self._determine_risk_level(probability)
                
                risks.append(RiskPrediction(
                    risk_level=risk_level,
                    metric_name=anomaly.metric_name,
                    probability=probability,
                    description=f"检测到异常: {anomaly.description}",
                    affected_components=["代码质量"],
                    mitigation_suggestions=self._get_mitigation_suggestions(anomaly.metric_name),
                    time_frame="立即",
                    predicted_impact="质量波动"
                ))
        
        return risks

    def _determine_risk_level(self, probability: float) -> RiskLevel:
        """确定风险等级"""
        if probability >= 0.9:
            return RiskLevel.CRITICAL
        elif probability >= 0.75:
            return RiskLevel.HIGH
        elif probability >= 0.5:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    def _get_mitigation_suggestions(self, metric_name: str) -> List[str]:
        """获取缓解建议"""
        suggestions = {
            "cyclomatic_complexity": [
                "重构复杂函数，提取子方法",
                "使用策略模式替代复杂条件判断",
                "减少嵌套层级"
            ],
            "avg_function_complexity": [
                "拆分长函数",
                "提取可复用的辅助方法",
                "应用单一职责原则"
            ],
            "max_nesting_depth": [
                "使用早返回减少嵌套",
                "提取嵌套逻辑到独立函数",
                "使用多态替代条件判断"
            ],
            "duplication_rate": [
                "提取重复代码到公共方法",
                "使用继承或组合消除重复",
                "应用DRY原则"
            ],
            "error_count": [
                "修复所有错误级别违规",
                "进行代码审查",
                "更新编码规范"
            ],
            "code_to_comment_ratio": [
                "为复杂逻辑添加注释",
                "编写文档字符串",
                "添加使用示例"
            ]
        }
        return suggestions.get(metric_name, ["分析问题根因并制定改进计划"])


class VisualizationGenerator:
    """可视化数据生成器"""

    def generate(
        self,
        historical_data: List[QualityDataPoint],
        trends: List[TrendAnalysis]
    ) -> List[VisualizationData]:
        """
        生成可视化数据
        
        Args:
            historical_data: 历史数据
            trends: 趋势分析结果
            
        Returns:
            可视化数据列表
        """
        visualizations = []
        
        if not historical_data:
            return visualizations
        
        complexity_chart = self._create_complexity_chart(historical_data)
        visualizations.append(complexity_chart)
        
        violation_chart = self._create_violation_chart(historical_data)
        visualizations.append(violation_chart)
        
        structure_chart = self._create_structure_chart(historical_data)
        visualizations.append(structure_chart)
        
        trend_chart = self._create_trend_chart(historical_data, trends)
        visualizations.append(trend_chart)
        
        return visualizations

    def _create_complexity_chart(self, data: List[QualityDataPoint]) -> VisualizationData:
        """创建复杂度图表"""
        labels = [d.timestamp[:10] for d in data]
        
        return VisualizationData(
            chart_type="line",
            title="代码复杂度趋势",
            labels=labels,
            datasets=[
                {
                    "label": "圈复杂度",
                    "data": [d.complexity.cyclomatic_complexity for d in data],
                    "borderColor": "#ef4444",
                    "backgroundColor": "rgba(239, 68, 68, 0.1)"
                },
                {
                    "label": "认知复杂度",
                    "data": [d.complexity.cognitive_complexity for d in data],
                    "borderColor": "#f59e0b",
                    "backgroundColor": "rgba(245, 158, 11, 0.1)"
                }
            ],
            options={
                "scales": {
                    "y": {"beginAtZero": True}
                }
            }
        )

    def _create_violation_chart(self, data: List[QualityDataPoint]) -> VisualizationData:
        """创建违规图表"""
        labels = [d.timestamp[:10] for d in data]
        
        return VisualizationData(
            chart_type="bar",
            title="代码违规统计",
            labels=labels,
            datasets=[
                {
                    "label": "错误",
                    "data": [d.violations.error_count for d in data],
                    "backgroundColor": "#ef4444"
                },
                {
                    "label": "警告",
                    "data": [d.violations.warning_count for d in data],
                    "backgroundColor": "#f59e0b"
                },
                {
                    "label": "信息",
                    "data": [d.violations.info_count for d in data],
                    "backgroundColor": "#3b82f6"
                }
            ],
            options={
                "scales": {
                    "x": {"stacked": True},
                    "y": {"stacked": True, "beginAtZero": True}
                }
            }
        )

    def _create_structure_chart(self, data: List[QualityDataPoint]) -> VisualizationData:
        """创建结构图表"""
        latest = data[-1] if data else None
        if not latest:
            return VisualizationData(
                chart_type="doughnut",
                title="代码结构分布",
                labels=[],
                datasets=[],
                options={}
            )
        
        return VisualizationData(
            chart_type="doughnut",
            title="代码结构分布",
            labels=["函数", "类"],
            datasets=[
                {
                    "data": [
                        latest.structure.total_functions,
                        latest.structure.total_classes
                    ],
                    "backgroundColor": ["#3b82f6", "#10b981"]
                }
            ],
            options={}
        )

    def _create_trend_chart(
        self,
        data: List[QualityDataPoint],
        trends: List[TrendAnalysis]
    ) -> VisualizationData:
        """创建趋势图表"""
        labels = [d.timestamp[:10] for d in data]
        
        trend_data = {}
        for trend in trends[:3]:
            trend_data[trend.metric_name] = {
                "direction": trend.direction.value,
                "confidence": trend.confidence
            }
        
        return VisualizationData(
            chart_type="line",
            title="质量趋势概览",
            labels=labels,
            datasets=[
                {
                    "label": "重复代码率 (%)",
                    "data": [d.duplication.duplication_rate * 100 for d in data],
                    "borderColor": "#8b5cf6",
                    "backgroundColor": "rgba(139, 92, 246, 0.1)"
                }
            ],
            options={
                "scales": {
                    "y": {"beginAtZero": True}
                },
                "trendInfo": trend_data
            }
        )


class ReportGenerator:
    """报告生成器"""

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)

    def generate_json_report(self, report: QualityTrendReport) -> str:
        """
        生成JSON格式报告
        
        Args:
            report: 质量趋势报告
            
        Returns:
            JSON字符串
        """
        return json.dumps(report.to_dict(), indent=2, ensure_ascii=False)

    def generate_markdown_report(self, report: QualityTrendReport) -> str:
        """
        生成Markdown格式报告
        
        Args:
            report: 质量趋势报告
            
        Returns:
            Markdown字符串
        """
        md = []
        
        md.append(f"# 质量趋势分析报告")
        md.append(f"")
        md.append(f"**项目**: {report.project}")
        md.append(f"**生成时间**: {report.timestamp}")
        md.append(f"**整体评分**: {report.overall_score:.2f}")
        md.append(f"**健康状态**: {self._get_status_emoji(report.health_status)} {report.health_status}")
        md.append(f"")
        
        md.append(f"## 📊 当前质量指标")
        md.append(f"")
        md.append(f"### 复杂度指标")
        md.append(f"")
        md.append(f"| 指标 | 值 |")
        md.append(f"|------|------|")
        md.append(f"| 圈复杂度 | {report.current_data.complexity.cyclomatic_complexity:.2f} |")
        md.append(f"| 认知复杂度 | {report.current_data.complexity.cognitive_complexity:.2f} |")
        md.append(f"| 最大嵌套深度 | {report.current_data.complexity.max_nesting_depth} |")
        md.append(f"| 平均函数复杂度 | {report.current_data.complexity.avg_function_complexity:.2f} |")
        md.append(f"")
        
        md.append(f"### 代码行数统计")
        md.append(f"")
        md.append(f"| 指标 | 值 |")
        md.append(f"|------|------|")
        md.append(f"| 总行数 | {report.current_data.lines.total_lines:,} |")
        md.append(f"| 代码行 | {report.current_data.lines.code_lines:,} |")
        md.append(f"| 注释行 | {report.current_data.lines.comment_lines:,} |")
        md.append(f"| 空行 | {report.current_data.lines.blank_lines:,} |")
        md.append(f"| 代码注释比 | {report.current_data.lines.code_to_comment_ratio:.2%} |")
        md.append(f"")
        
        md.append(f"### 代码结构统计")
        md.append(f"")
        md.append(f"| 指标 | 值 |")
        md.append(f"|------|------|")
        md.append(f"| 函数数量 | {report.current_data.structure.total_functions:,} |")
        md.append(f"| 类数量 | {report.current_data.structure.total_classes:,} |")
        md.append(f"| 平均函数长度 | {report.current_data.structure.avg_function_length:.2f} 行 |")
        md.append(f"")
        
        md.append(f"### 重复代码检测")
        md.append(f"")
        md.append(f"| 指标 | 值 |")
        md.append(f"|------|------|")
        md.append(f"| 重复代码率 | {report.current_data.duplication.duplication_rate:.2%} |")
        md.append(f"| 重复块数 | {report.current_data.duplication.duplicated_blocks} |")
        md.append(f"| 重复行数 | {report.current_data.duplication.duplicated_lines:,} |")
        md.append(f"")
        
        md.append(f"### 代码规范违规")
        md.append(f"")
        md.append(f"| 指标 | 值 |")
        md.append(f"|------|------|")
        md.append(f"| 总违规数 | {report.current_data.violations.total_violations} |")
        md.append(f"| 错误数 | {report.current_data.violations.error_count} |")
        md.append(f"| 警告数 | {report.current_data.violations.warning_count} |")
        md.append(f"")
        
        if report.trends:
            md.append(f"## 📈 趋势分析")
            md.append(f"")
            md.append(f"| 指标 | 方向 | 当前值 | 预测值 | 置信度 |")
            md.append(f"|------|------|--------|--------|--------|")
            for trend in report.trends[:10]:
                direction_emoji = self._get_direction_emoji(trend.direction)
                md.append(f"| {trend.metric_name} | {direction_emoji} {trend.direction.value} | {trend.current_value:.2f} | {trend.predicted_value:.2f} | {trend.confidence:.0%} |")
            md.append(f"")
        
        if report.anomalies:
            md.append(f"## ⚠️ 异常检测")
            md.append(f"")
            for anomaly in report.anomalies[:5]:
                md.append(f"- **{anomaly.metric_name}**: {anomaly.description} (偏离: {anomaly.deviation:.2f}σ)")
            md.append(f"")
        
        if report.risks:
            md.append(f"## 🚨 风险预测")
            md.append(f"")
            for risk in report.risks[:5]:
                level_emoji = self._get_risk_emoji(risk.risk_level)
                md.append(f"### {level_emoji} {risk.risk_level.value.upper()} - {risk.metric_name}")
                md.append(f"")
                md.append(f"- **概率**: {risk.probability:.0%}")
                md.append(f"- **描述**: {risk.description}")
                md.append(f"- **影响组件**: {', '.join(risk.affected_components)}")
                md.append(f"- **时间范围**: {risk.time_frame}")
                md.append(f"- **缓解建议**:")
                for suggestion in risk.mitigation_suggestions[:3]:
                    md.append(f"  - {suggestion}")
                md.append(f"")
        
        if report.recommendations:
            md.append(f"## 💡 改进建议")
            md.append(f"")
            for i, rec in enumerate(report.recommendations, 1):
                md.append(f"{i}. {rec}")
            md.append(f"")
        
        md.append(f"---")
        md.append(f"*报告由质量趋势分析器自动生成*")
        
        return "\n".join(md)

    def generate_custom_report(
        self,
        report: QualityTrendReport,
        template: str
    ) -> str:
        """
        使用自定义模板生成报告
        
        Args:
            report: 质量趋势报告
            template: 模板内容
            
        Returns:
            生成的报告
        """
        result = template
        
        result = result.replace("{{project}}", report.project)
        result = result.replace("{{timestamp}}", report.timestamp)
        result = result.replace("{{overall_score}}", f"{report.overall_score:.2f}")
        result = result.replace("{{health_status}}", report.health_status)
        
        result = result.replace("{{cyclomatic_complexity}}", f"{report.current_data.complexity.cyclomatic_complexity:.2f}")
        result = result.replace("{{cognitive_complexity}}", f"{report.current_data.complexity.cognitive_complexity:.2f}")
        result = result.replace("{{max_nesting_depth}}", str(report.current_data.complexity.max_nesting_depth))
        result = result.replace("{{total_lines}}", f"{report.current_data.lines.total_lines:,}")
        result = result.replace("{{code_lines}}", f"{report.current_data.lines.code_lines:,}")
        result = result.replace("{{total_functions}}", str(report.current_data.structure.total_functions))
        result = result.replace("{{total_classes}}", str(report.current_data.structure.total_classes))
        result = result.replace("{{duplication_rate}}", f"{report.current_data.duplication.duplication_rate:.2%}")
        result = result.replace("{{total_violations}}", str(report.current_data.violations.total_violations))
        
        if "{{trends_table}}" in result:
            trends_table = self._generate_trends_table(report.trends)
            result = result.replace("{{trends_table}}", trends_table)
        
        if "{{risks_list}}" in result:
            risks_list = self._generate_risks_list(report.risks)
            result = result.replace("{{risks_list}}", risks_list)
        
        return result

    def _generate_trends_table(self, trends: List[TrendAnalysis]) -> str:
        """生成趋势表格"""
        lines = ["| 指标 | 方向 | 当前值 | 预测值 |", "|------|------|--------|--------|"]
        for trend in trends[:10]:
            lines.append(f"| {trend.metric_name} | {trend.direction.value} | {trend.current_value:.2f} | {trend.predicted_value:.2f} |")
        return "\n".join(lines)

    def _generate_risks_list(self, risks: List[RiskPrediction]) -> str:
        """生成风险列表"""
        lines = []
        for risk in risks[:5]:
            lines.append(f"- [{risk.risk_level.value.upper()}] {risk.metric_name}: {risk.description}")
        return "\n".join(lines)

    def _get_status_emoji(self, status: str) -> str:
        """获取状态表情"""
        emojis = {
            "healthy": "✅",
            "moderate": "⚠️",
            "warning": "🔶",
            "critical": "🔴"
        }
        return emojis.get(status, "❓")

    def _get_direction_emoji(self, direction: TrendDirection) -> str:
        """获取方向表情"""
        emojis = {
            TrendDirection.IMPROVING: "📈",
            TrendDirection.DECLINING: "📉",
            TrendDirection.STABLE: "➡️",
            TrendDirection.VOLATILE: "↕️"
        }
        return emojis.get(direction, "❓")

    def _get_risk_emoji(self, level: RiskLevel) -> str:
        """获取风险表情"""
        emojis = {
            RiskLevel.LOW: "🟢",
            RiskLevel.MEDIUM: "🟡",
            RiskLevel.HIGH: "🟠",
            RiskLevel.CRITICAL: "🔴"
        }
        return emojis.get(level, "❓")


class QualityTrendAnalyzer:
    """质量趋势分析器主类"""

    def __init__(
        self,
        project_path: Path,
        storage_path: Optional[Path] = None,
        risk_threshold: float = 0.7,
        logger: Optional[logging.Logger] = None
    ):
        self.project_path = project_path
        self.storage_path = storage_path or project_path / "quality_data"
        self.logger = logger or logging.getLogger(__name__)
        
        self.data_collector = QualityDataCollector(project_path, self.storage_path, logger)
        self.trend_calculator = TrendCalculator(logger)
        self.anomaly_detector = AnomalyDetector(logger=logger)
        self.risk_predictor = RiskPredictor(risk_threshold, logger)
        self.visualization_generator = VisualizationGenerator()
        self.report_generator = ReportGenerator(logger)

    def analyze(
        self,
        project: str = "default",
        days: int = 30,
        predict_days: int = 7
    ) -> QualityTrendReport:
        """
        执行完整的质量趋势分析
        
        Args:
            project: 项目名称
            days: 历史数据天数
            predict_days: 预测天数
            
        Returns:
            质量趋势报告
        """
        self.logger.info(f"开始分析项目 {project}")
        
        current_data = self.data_collector.collect(project)
        historical_data = self.data_collector.load_historical(project, days)
        
        trends = self.trend_calculator.calculate_trends(historical_data + [current_data], predict_days)
        anomalies = self.anomaly_detector.detect(historical_data + [current_data], trends)
        risks = self.risk_predictor.predict(trends, current_data, anomalies)
        visualization_data = self.visualization_generator.generate(historical_data + [current_data], trends)
        
        overall_score = self._calculate_overall_score(current_data, trends, risks)
        health_status = self._determine_health_status(overall_score, risks)
        recommendations = self._generate_recommendations(trends, risks, anomalies)
        
        report = QualityTrendReport(
            timestamp=datetime.now().isoformat(),
            project=project,
            current_data=current_data,
            historical_data=historical_data,
            trends=trends,
            anomalies=anomalies,
            risks=risks,
            visualization_data=visualization_data,
            overall_score=overall_score,
            health_status=health_status,
            recommendations=recommendations
        )
        
        return report

    def _calculate_overall_score(
        self,
        current_data: QualityDataPoint,
        trends: List[TrendAnalysis],
        risks: List[RiskPrediction]
    ) -> float:
        """计算整体评分"""
        score = 100.0
        
        if current_data.complexity.avg_function_complexity > 10:
            score -= (current_data.complexity.avg_function_complexity - 10) * 2
        
        if current_data.duplication.duplication_rate > 0.05:
            score -= current_data.duplication.duplication_rate * 100
        
        score -= current_data.violations.error_count * 5
        score -= current_data.violations.warning_count * 1
        
        for risk in risks:
            if risk.risk_level == RiskLevel.CRITICAL:
                score -= 20
            elif risk.risk_level == RiskLevel.HIGH:
                score -= 10
            elif risk.risk_level == RiskLevel.MEDIUM:
                score -= 5
        
        for trend in trends:
            if trend.direction == TrendDirection.DECLINING and trend.confidence > 0.7:
                score -= 5
        
        return max(0, min(100, score))

    def _determine_health_status(self, score: float, risks: List[RiskPrediction]) -> str:
        """确定健康状态"""
        critical_risks = sum(1 for r in risks if r.risk_level == RiskLevel.CRITICAL)
        high_risks = sum(1 for r in risks if r.risk_level == RiskLevel.HIGH)
        
        if critical_risks > 0 or score < 50:
            return "critical"
        elif high_risks > 0 or score < 70:
            return "warning"
        elif score < 85:
            return "moderate"
        else:
            return "healthy"

    def _generate_recommendations(
        self,
        trends: List[TrendAnalysis],
        risks: List[RiskPrediction],
        anomalies: List[Anomaly]
    ) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        for risk in risks[:3]:
            if risk.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                recommendations.extend(risk.mitigation_suggestions[:2])
        
        for trend in trends[:3]:
            if trend.direction == TrendDirection.DECLINING:
                recommendations.append(f"关注 {trend.metric_name} 指标的下降趋势")
        
        for anomaly in anomalies[:2]:
            recommendations.append(f"调查 {anomaly.metric_name} 的异常变化")
        
        return list(dict.fromkeys(recommendations))[:10]

    def save_report(
        self,
        report: QualityTrendReport,
        output_path: Path,
        format: str = "json"
    ) -> bool:
        """
        保存报告
        
        Args:
            report: 质量趋势报告
            output_path: 输出路径
            format: 格式 (json/markdown)
            
        Returns:
            是否成功
        """
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            if format == "json":
                content = self.report_generator.generate_json_report(report)
            elif format == "markdown":
                content = self.report_generator.generate_markdown_report(report)
            else:
                raise ValueError(f"不支持的格式: {format}")
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.logger.info(f"报告已保存到 {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"保存报告失败: {e}")
            return False


def setup_logger(verbose: bool = False) -> logging.Logger:
    """配置日志记录器"""
    logger = logging.getLogger("QualityTrendAnalyzer")
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
        description="质量趋势分析器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python quality_trend_analyzer.py --project myproject
  python quality_trend_analyzer.py --days 30 --output json
  python quality_trend_analyzer.py --predict --risk-threshold 0.7
  python quality_trend_analyzer.py --report markdown --template custom.md
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
        "--days",
        type=int,
        default=30,
        help="历史数据天数 (默认: 30)"
    )
    
    parser.add_argument(
        "--predict-days",
        type=int,
        default=7,
        help="预测天数 (默认: 7)"
    )
    
    parser.add_argument(
        "--risk-threshold",
        type=float,
        default=0.7,
        help="风险阈值 (默认: 0.7)"
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
        "--template",
        type=str,
        help="自定义报告模板文件路径"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="启用详细日志输出"
    )
    
    args = parser.parse_args()
    
    logger = setup_logger(args.verbose)
    
    print("=" * 80)
    print("质量趋势分析器")
    print("=" * 80)
    
    analyzer = QualityTrendAnalyzer(
        project_path=args.project_path,
        risk_threshold=args.risk_threshold,
        logger=logger
    )
    
    print(f"\n分析项目: {args.project}")
    print(f"项目路径: {args.project_path}")
    print(f"历史数据范围: {args.days} 天")
    print(f"预测范围: {args.predict_days} 天")
    
    report = analyzer.analyze(
        project=args.project,
        days=args.days,
        predict_days=args.predict_days
    )
    
    if args.output == "console":
        print("\n" + "=" * 80)
        print("质量趋势分析报告")
        print("=" * 80)
        print(f"\n生成时间: {report.timestamp}")
        print(f"项目: {report.project}")
        print(f"整体评分: {report.overall_score:.2f}")
        print(f"健康状态: {report.health_status}")
        
        print(f"\n当前质量指标:")
        print(f"  圈复杂度: {report.current_data.complexity.cyclomatic_complexity:.2f}")
        print(f"  认知复杂度: {report.current_data.complexity.cognitive_complexity:.2f}")
        print(f"  最大嵌套深度: {report.current_data.complexity.max_nesting_depth}")
        print(f"  总行数: {report.current_data.lines.total_lines:,}")
        print(f"  代码行: {report.current_data.lines.code_lines:,}")
        print(f"  函数数量: {report.current_data.structure.total_functions}")
        print(f"  类数量: {report.current_data.structure.total_classes}")
        print(f"  重复代码率: {report.current_data.duplication.duplication_rate:.2%}")
        print(f"  总违规数: {report.current_data.violations.total_violations}")
        
        if report.trends:
            print(f"\n趋势分析 ({len(report.trends)} 个):")
            for trend in report.trends[:5]:
                direction_icon = {
                    TrendDirection.IMPROVING: "↑",
                    TrendDirection.DECLINING: "↓",
                    TrendDirection.STABLE: "→",
                    TrendDirection.VOLATILE: "↕"
                }.get(trend.direction, "?")
                print(f"  {direction_icon} {trend.metric_name}: {trend.direction.value}")
                print(f"      当前: {trend.current_value:.2f}, 预测: {trend.predicted_value:.2f}")
        
        if report.risks:
            print(f"\n风险预测 ({len(report.risks)} 个):")
            for risk in report.risks[:5]:
                level_icon = {
                    RiskLevel.LOW: "🟢",
                    RiskLevel.MEDIUM: "🟡",
                    RiskLevel.HIGH: "🟠",
                    RiskLevel.CRITICAL: "🔴"
                }.get(risk.risk_level, "?")
                print(f"  {level_icon} [{risk.risk_level.value}] {risk.metric_name}")
                print(f"      概率: {risk.probability:.2%}")
    
    elif args.output in ["json", "markdown"]:
        if args.output_file:
            output_path = Path(args.output_file)
            
            if args.template and args.output == "markdown":
                with open(args.template, 'r', encoding='utf-8') as f:
                    template = f.read()
                content = analyzer.report_generator.generate_custom_report(report, template)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            else:
                analyzer.save_report(report, output_path, args.output)
            
            print(f"\n报告已保存到: {output_path}")
        else:
            if args.output == "json":
                print(analyzer.report_generator.generate_json_report(report))
            else:
                print(analyzer.report_generator.generate_markdown_report(report))
    
    return 0 if report.health_status != "critical" else 1


if __name__ == "__main__":
    sys.exit(main())
