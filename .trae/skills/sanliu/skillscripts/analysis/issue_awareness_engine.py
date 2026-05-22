#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能问题感知引擎 - Issue Awareness Engine

三省六部技能系统的核心问题感知模块，提供：
- 错误模式智能识别（语法错误、运行时错误、逻辑错误等）
- 性能退化检测（响应时间、内存使用、CPU使用等）
- 代码异味检测（长方法、重复代码、复杂条件等）
- 与 log_analyzer.py 和 issue_locator.py 无缝集成
- 异步支持和高性能处理

使用示例:
    from issue_awareness_engine import IssueAwarenessEngine
    
    engine = IssueAwarenessEngine(codebase_path="./src")
    report = await engine.analyze_comprehensive()
"""

import ast
import asyncio
import json
import logging
import os
import re
import sys
import time
import traceback
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import (
    Any,
    AsyncIterator,
    Callable,
    Dict,
    List,
    Optional,
    Pattern,
    Set,
    Tuple,
    TypeVar,
    Union,
)

T = TypeVar('T')


class IssueCategory(Enum):
    """问题类别枚举"""
    SYNTAX_ERROR = "syntax_error"
    RUNTIME_ERROR = "runtime_error"
    LOGIC_ERROR = "logic_error"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    MEMORY_ISSUE = "memory_issue"
    CODE_SMELL = "code_smell"
    SECURITY_VULNERABILITY = "security_vulnerability"
    DEPENDENCY_ISSUE = "dependency_issue"
    CONFIGURATION_ERROR = "configuration_error"
    UNKNOWN = "unknown"


class IssueSeverity(Enum):
    """问题严重程度枚举"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class DetectionConfidence(Enum):
    """检测置信度枚举"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class PerformanceMetricType(Enum):
    """性能指标类型枚举"""
    RESPONSE_TIME = "response_time"
    MEMORY_USAGE = "memory_usage"
    CPU_USAGE = "cpu_usage"
    DISK_IO = "disk_io"
    NETWORK_LATENCY = "network_latency"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"


@dataclass
class CodeLocation:
    """代码位置数据类"""
    file_path: str
    line_number: int
    column: int = 0
    function_name: str = ""
    class_name: str = ""
    code_snippet: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "line_number": self.line_number,
            "column": self.column,
            "function_name": self.function_name,
            "class_name": self.class_name,
            "code_snippet": self.code_snippet[:200] if self.code_snippet else ""
        }


@dataclass
class DetectedIssue:
    """检测到的问题数据类"""
    issue_id: str
    category: IssueCategory
    severity: IssueSeverity
    title: str
    description: str
    location: Optional[CodeLocation]
    confidence: DetectionConfidence
    evidence: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    related_issues: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    detected_at: str = field(default_factory=lambda: datetime.now().isoformat())
    detector_name: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "issue_id": self.issue_id,
            "category": self.category.value,
            "severity": self.severity.value,
            "title": self.title,
            "description": self.description,
            "location": self.location.to_dict() if self.location else None,
            "confidence": self.confidence.value,
            "evidence": self.evidence,
            "suggestions": self.suggestions,
            "related_issues": self.related_issues,
            "metrics": self.metrics,
            "tags": self.tags,
            "detected_at": self.detected_at,
            "detector_name": self.detector_name
        }


@dataclass
class PerformanceMetric:
    """性能指标数据类"""
    metric_type: PerformanceMetricType
    value: float
    unit: str
    timestamp: str
    threshold: float = 0.0
    is_anomaly: bool = False
    deviation_percent: float = 0.0
    baseline_value: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_type": self.metric_type.value,
            "value": self.value,
            "unit": self.unit,
            "timestamp": self.timestamp,
            "threshold": self.threshold,
            "is_anomaly": self.is_anomaly,
            "deviation_percent": round(self.deviation_percent, 2),
            "baseline_value": self.baseline_value
        }


@dataclass
class PerformanceDegradation:
    """性能退化数据类"""
    degradation_id: str
    metric_type: PerformanceMetricType
    current_value: float
    baseline_value: float
    degradation_percent: float
    severity: IssueSeverity
    description: str
    possible_causes: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    affected_components: List[str] = field(default_factory=list)
    trend_data: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "degradation_id": self.degradation_id,
            "metric_type": self.metric_type.value,
            "current_value": self.current_value,
            "baseline_value": self.baseline_value,
            "degradation_percent": round(self.degradation_percent, 2),
            "severity": self.severity.value,
            "description": self.description,
            "possible_causes": self.possible_causes,
            "recommendations": self.recommendations,
            "affected_components": self.affected_components,
            "trend_data": self.trend_data[:10]
        }


@dataclass
class CodeSmellInfo:
    """代码异味信息数据类"""
    smell_type: str
    category: str
    severity: IssueSeverity
    location: CodeLocation
    description: str
    impact_score: float = 0.0
    effort_score: float = 1.0
    refactoring_suggestions: List[str] = field(default_factory=list)
    related_smells: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "smell_type": self.smell_type,
            "category": self.category,
            "severity": self.severity.value,
            "location": self.location.to_dict(),
            "description": self.description,
            "impact_score": round(self.impact_score, 2),
            "effort_score": round(self.effort_score, 2),
            "refactoring_suggestions": self.refactoring_suggestions,
            "related_smells": self.related_smells
        }


@dataclass
class AwarenessReport:
    """感知报告数据类"""
    report_id: str
    generated_at: str
    total_issues: int
    issues_by_category: Dict[str, int]
    issues_by_severity: Dict[str, int]
    detected_issues: List[DetectedIssue]
    performance_degradations: List[PerformanceDegradation]
    code_smells: List[CodeSmellInfo]
    summary: str
    recommendations: List[str]
    health_score: float = 0.0
    analysis_duration_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "generated_at": self.generated_at,
            "total_issues": self.total_issues,
            "issues_by_category": self.issues_by_category,
            "issues_by_severity": self.issues_by_severity,
            "detected_issues": [i.to_dict() for i in self.detected_issues],
            "performance_degradations": [p.to_dict() for p in self.performance_degradations],
            "code_smells": [s.to_dict() for s in self.code_smells],
            "summary": self.summary,
            "recommendations": self.recommendations,
            "health_score": round(self.health_score, 2),
            "analysis_duration_ms": round(self.analysis_duration_ms, 2)
        }


class BaseDetector(ABC):
    """检测器基类"""

    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"issue_awareness.{name}")
        self._issue_counter = 0

    @abstractmethod
    async def detect(self, context: Dict[str, Any]) -> List[DetectedIssue]:
        """执行检测"""
        pass

    def _generate_issue_id(self) -> str:
        self._issue_counter += 1
        return f"{self.name}-{self._issue_counter:04d}"


class ErrorPatternRecognizer(BaseDetector):
    """错误模式识别器
    
    识别各类错误模式，包括：
    - 语法错误：缩进、括号匹配、关键字错误等
    - 运行时错误：类型错误、属性错误、索引错误等
    - 逻辑错误：断言失败、条件判断错误等
    """

    SYNTAX_ERROR_PATTERNS = [
        {
            "pattern": r"IndentationError",
            "name": "缩进错误",
            "severity": IssueSeverity.HIGH,
            "suggestion": "检查代码缩进，确保使用一致的缩进风格（空格或Tab）"
        },
        {
            "pattern": r"SyntaxError",
            "name": "语法错误",
            "severity": IssueSeverity.HIGH,
            "suggestion": "检查语法错误，如括号匹配、关键字拼写、语句结束符等"
        },
        {
            "pattern": r"TabError",
            "name": "Tab错误",
            "severity": IssueSeverity.MEDIUM,
            "suggestion": "避免混用Tab和空格，建议统一使用4个空格缩进"
        },
        {
            "pattern": r"unterminated string literal",
            "name": "未闭合字符串",
            "severity": IssueSeverity.HIGH,
            "suggestion": "检查字符串是否正确闭合，注意引号配对"
        }
    ]

    RUNTIME_ERROR_PATTERNS = [
        {
            "pattern": r"TypeError[:\s]+(.+)",
            "name": "类型错误",
            "severity": IssueSeverity.HIGH,
            "suggestion": "检查参数类型是否正确，添加类型检查或转换"
        },
        {
            "pattern": r"AttributeError[:\s]+(.+)",
            "name": "属性错误",
            "severity": IssueSeverity.HIGH,
            "suggestion": "检查对象是否为None，使用hasattr()验证属性存在"
        },
        {
            "pattern": r"NameError[:\s]+name '(\w+)' is not defined",
            "name": "名称错误",
            "severity": IssueSeverity.HIGH,
            "suggestion": "检查变量或函数是否已定义，注意作用域问题"
        },
        {
            "pattern": r"IndexError[:\s]+(.+)",
            "name": "索引错误",
            "severity": IssueSeverity.MEDIUM,
            "suggestion": "检查索引是否越界，添加边界检查"
        },
        {
            "pattern": r"KeyError[:\s]+(.+)",
            "name": "键错误",
            "severity": IssueSeverity.MEDIUM,
            "suggestion": "使用dict.get()方法或检查键是否存在"
        },
        {
            "pattern": r"ValueError[:\s]+(.+)",
            "name": "值错误",
            "severity": IssueSeverity.MEDIUM,
            "suggestion": "检查值的范围和格式是否正确"
        },
        {
            "pattern": r"ZeroDivisionError",
            "name": "除零错误",
            "severity": IssueSeverity.HIGH,
            "suggestion": "在除法前检查除数是否为零"
        },
        {
            "pattern": r"RecursionError[:\s]+maximum recursion depth exceeded",
            "name": "递归深度超限",
            "severity": IssueSeverity.HIGH,
            "suggestion": "检查递归终止条件，考虑使用迭代替代递归"
        }
    ]

    LOGIC_ERROR_PATTERNS = [
        {
            "pattern": r"AssertionError[:\s]*(.+)",
            "name": "断言失败",
            "severity": IssueSeverity.MEDIUM,
            "suggestion": "检查断言条件是否满足，验证业务逻辑"
        },
        {
            "pattern": r"StopIteration",
            "name": "迭代器终止",
            "severity": IssueSeverity.LOW,
            "suggestion": "检查迭代器使用方式，考虑使用for循环"
        },
        {
            "pattern": r"GeneratorExit",
            "name": "生成器退出",
            "severity": IssueSeverity.LOW,
            "suggestion": "检查生成器的关闭和清理逻辑"
        }
    ]

    def __init__(self):
        super().__init__("error_pattern_recognizer")
        self._compiled_patterns: Dict[str, List[Tuple[Pattern, Dict[str, Any]]]] = {}
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """编译正则表达式模式"""
        self._compiled_patterns = {
            "syntax": [
                (re.compile(p["pattern"], re.IGNORECASE), p)
                for p in self.SYNTAX_ERROR_PATTERNS
            ],
            "runtime": [
                (re.compile(p["pattern"], re.IGNORECASE), p)
                for p in self.RUNTIME_ERROR_PATTERNS
            ],
            "logic": [
                (re.compile(p["pattern"], re.IGNORECASE), p)
                for p in self.LOGIC_ERROR_PATTERNS
            ]
        }

    async def detect(self, context: Dict[str, Any]) -> List[DetectedIssue]:
        """执行错误模式检测
        
        Args:
            context: 检测上下文，包含：
                - error_messages: 错误消息列表
                - stack_traces: 堆栈跟踪列表
                - codebase_path: 代码库路径
                
        Returns:
            检测到的问题列表
        """
        issues: List[DetectedIssue] = []
        
        error_messages = context.get("error_messages", [])
        stack_traces = context.get("stack_traces", [])
        
        for error_msg in error_messages:
            detected = await self._analyze_error_message(error_msg)
            issues.extend(detected)
        
        for trace in stack_traces:
            detected = await self._analyze_stack_trace(trace)
            issues.extend(detected)
        
        return issues

    async def _analyze_error_message(self, error_msg: str) -> List[DetectedIssue]:
        """分析错误消息"""
        issues: List[DetectedIssue] = []
        
        for error_type, patterns in self._compiled_patterns.items():
            for compiled_pattern, pattern_info in patterns:
                match = compiled_pattern.search(error_msg)
                if match:
                    category = self._get_category_from_type(error_type)
                    
                    issue = DetectedIssue(
                        issue_id=self._generate_issue_id(),
                        category=category,
                        severity=pattern_info["severity"],
                        title=pattern_info["name"],
                        description=f"检测到{pattern_info['name']}: {error_msg[:200]}",
                        location=None,
                        confidence=DetectionConfidence.HIGH,
                        evidence=[f"错误消息: {error_msg[:500]}"],
                        suggestions=[pattern_info["suggestion"]],
                        tags=[error_type, pattern_info["name"].replace(" ", "_")],
                        detector_name=self.name
                    )
                    issues.append(issue)
        
        return issues

    async def _analyze_stack_trace(self, trace: str) -> List[DetectedIssue]:
        """分析堆栈跟踪"""
        issues: List[DetectedIssue] = []
        
        frame_pattern = re.compile(
            r'File\s+"([^"]+)",\s+line\s+(\d+),\s+in\s+(\w+)\s*\n\s*(.+)',
            re.MULTILINE
        )
        
        for match in frame_pattern.finditer(trace):
            file_path = match.group(1)
            line_number = int(match.group(2))
            function_name = match.group(3)
            code_line = match.group(4).strip()
            
            location = CodeLocation(
                file_path=file_path,
                line_number=line_number,
                function_name=function_name,
                code_snippet=code_line
            )
            
            error_type = self._extract_error_type(trace)
            if error_type:
                issue = DetectedIssue(
                    issue_id=self._generate_issue_id(),
                    category=IssueCategory.RUNTIME_ERROR,
                    severity=IssueSeverity.HIGH,
                    title=f"运行时错误: {error_type}",
                    description=f"在函数 {function_name} 中发生 {error_type}",
                    location=location,
                    confidence=DetectionConfidence.HIGH,
                    evidence=[f"堆栈跟踪位置: {file_path}:{line_number}"],
                    suggestions=["检查该位置的代码逻辑"],
                    tags=["runtime", error_type.lower()],
                    detector_name=self.name
                )
                issues.append(issue)
        
        return issues[:10]

    def _get_category_from_type(self, error_type: str) -> IssueCategory:
        """从错误类型获取问题类别"""
        mapping = {
            "syntax": IssueCategory.SYNTAX_ERROR,
            "runtime": IssueCategory.RUNTIME_ERROR,
            "logic": IssueCategory.LOGIC_ERROR
        }
        return mapping.get(error_type, IssueCategory.UNKNOWN)

    def _extract_error_type(self, trace: str) -> Optional[str]:
        """从堆栈跟踪提取错误类型"""
        match = re.search(r'(\w+Error|\w+Exception)', trace)
        return match.group(1) if match else None


class PerformanceDegradationDetector(BaseDetector):
    """性能退化检测器
    
    检测各类性能退化问题，包括：
    - 响应时间退化
    - 内存使用异常
    - CPU使用异常
    - 吞吐量下降
    - 错误率上升
    """

    DEFAULT_THRESHOLDS = {
        PerformanceMetricType.RESPONSE_TIME: {
            "warning": 1000.0,
            "critical": 5000.0,
            "unit": "ms"
        },
        PerformanceMetricType.MEMORY_USAGE: {
            "warning": 80.0,
            "critical": 95.0,
            "unit": "%"
        },
        PerformanceMetricType.CPU_USAGE: {
            "warning": 70.0,
            "critical": 90.0,
            "unit": "%"
        },
        PerformanceMetricType.ERROR_RATE: {
            "warning": 1.0,
            "critical": 5.0,
            "unit": "%"
        },
        PerformanceMetricType.THROUGHPUT: {
            "warning": 100.0,
            "critical": 50.0,
            "unit": "req/s"
        }
    }

    DEGRADATION_CAUSES = {
        PerformanceMetricType.RESPONSE_TIME: [
            "数据库查询未优化",
            "缺少缓存机制",
            "网络延迟增加",
            "资源竞争",
            "代码效率问题"
        ],
        PerformanceMetricType.MEMORY_USAGE: [
            "内存泄漏",
            "大对象未释放",
            "缓存无限增长",
            "数据结构选择不当",
            "循环引用"
        ],
        PerformanceMetricType.CPU_USAGE: [
            "计算密集型操作",
            "死循环或无限递归",
            "频繁的GC",
            "锁竞争",
            "低效算法"
        ],
        PerformanceMetricType.ERROR_RATE: [
            "服务依赖不稳定",
            "配置错误",
            "资源不足",
            "代码缺陷",
            "流量异常"
        ]
    }

    def __init__(self):
        super().__init__("performance_degradation_detector")
        self._metrics_history: Dict[PerformanceMetricType, List[PerformanceMetric]] = defaultdict(list)
        self._baselines: Dict[PerformanceMetricType, float] = {}
        self._degradation_counter = 0

    async def detect(self, context: Dict[str, Any]) -> List[DetectedIssue]:
        """执行性能退化检测
        
        Args:
            context: 检测上下文，包含：
                - metrics: 性能指标字典
                - historical_data: 历史数据
                - thresholds: 自定义阈值
                
        Returns:
            检测到的问题列表
        """
        issues: List[DetectedIssue] = []
        
        metrics = context.get("metrics", {})
        thresholds = context.get("thresholds", {})
        historical_data = context.get("historical_data", [])
        
        merged_thresholds = {**self.DEFAULT_THRESHOLDS, **thresholds}
        
        for metric_type, value in metrics.items():
            if isinstance(metric_type, str):
                try:
                    metric_type = PerformanceMetricType(metric_type)
                except ValueError:
                    continue
            
            if not isinstance(value, (int, float)):
                continue
            
            detected = await self._analyze_metric(metric_type, value, merged_thresholds)
            issues.extend(detected)
        
        if historical_data:
            trend_issues = await self._analyze_trends(historical_data)
            issues.extend(trend_issues)
        
        return issues

    async def _analyze_metric(
        self,
        metric_type: PerformanceMetricType,
        value: float,
        thresholds: Dict[str, Any]
    ) -> List[DetectedIssue]:
        """分析单个指标"""
        issues: List[DetectedIssue] = []
        
        threshold_config = thresholds.get(metric_type, {})
        warning_threshold = threshold_config.get("warning", 0)
        critical_threshold = threshold_config.get("critical", 0)
        unit = threshold_config.get("unit", "")
        
        metric = PerformanceMetric(
            metric_type=metric_type,
            value=value,
            unit=unit,
            timestamp=datetime.now().isoformat(),
            threshold=warning_threshold
        )
        
        self._metrics_history[metric_type].append(metric)
        if len(self._metrics_history[metric_type]) > 100:
            self._metrics_history[metric_type] = self._metrics_history[metric_type][-100:]
        
        if critical_threshold and value >= critical_threshold:
            severity = IssueSeverity.CRITICAL
        elif warning_threshold and value >= warning_threshold:
            severity = IssueSeverity.HIGH
        else:
            return issues
        
        metric.is_anomaly = True
        metric.deviation_percent = self._calculate_deviation(metric_type, value)
        
        possible_causes = self.DEGRADATION_CAUSES.get(metric_type, [])
        
        issue = DetectedIssue(
            issue_id=self._generate_issue_id(),
            category=IssueCategory.PERFORMANCE_DEGRADATION,
            severity=severity,
            title=f"性能退化: {metric_type.value}",
            description=f"{metric_type.value} 达到 {value}{unit}，超过阈值",
            location=None,
            confidence=DetectionConfidence.HIGH,
            evidence=[
                f"当前值: {value}{unit}",
                f"警告阈值: {warning_threshold}{unit}",
                f"严重阈值: {critical_threshold}{unit}",
                f"偏离基线: {metric.deviation_percent:.1f}%"
            ],
            suggestions=self._generate_recommendations(metric_type, value, thresholds),
            metrics={"metric_type": metric_type.value, "value": value, "unit": unit},
            tags=["performance", metric_type.value],
            detector_name=self.name
        )
        issues.append(issue)
        
        return issues

    async def _analyze_trends(self, historical_data: List[Dict[str, Any]]) -> List[DetectedIssue]:
        """分析趋势数据"""
        issues: List[DetectedIssue] = []
        
        if len(historical_data) < 5:
            return issues
        
        for metric_type in PerformanceMetricType:
            values = []
            for data in historical_data:
                if metric_type.value in data:
                    values.append(data[metric_type.value])
            
            if len(values) < 5:
                continue
            
            trend = self._calculate_trend(values)
            if trend > 0.2:
                issue = DetectedIssue(
                    issue_id=self._generate_issue_id(),
                    category=IssueCategory.PERFORMANCE_DEGRADATION,
                    severity=IssueSeverity.MEDIUM,
                    title=f"性能趋势退化: {metric_type.value}",
                    description=f"{metric_type.value} 呈上升趋势，增长 {trend*100:.1f}%",
                    location=None,
                    confidence=DetectionConfidence.MEDIUM,
                    evidence=[f"趋势分析基于 {len(values)} 个数据点"],
                    suggestions=["持续监控该指标", "分析增长原因"],
                    tags=["performance", "trend", metric_type.value],
                    detector_name=self.name
                )
                issues.append(issue)
        
        return issues

    def _calculate_deviation(self, metric_type: PerformanceMetricType, value: float) -> float:
        """计算偏离基线的百分比"""
        if metric_type not in self._baselines:
            return 0.0
        
        baseline = self._baselines[metric_type]
        if baseline == 0:
            return 0.0
        
        return abs(value - baseline) / baseline * 100

    def _calculate_trend(self, values: List[float]) -> float:
        """计算趋势（简单线性回归斜率）"""
        if len(values) < 2:
            return 0.0
        
        n = len(values)
        x = list(range(n))
        y = values
        
        x_mean = sum(x) / n
        y_mean = sum(y) / n
        
        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return 0.0
        
        slope = numerator / denominator
        
        if y_mean == 0:
            return 0.0
        
        return slope / y_mean

    def _generate_recommendations(
        self,
        metric_type: PerformanceMetricType,
        value: float,
        thresholds: Dict[str, Any]
    ) -> List[str]:
        """生成优化建议"""
        recommendations = []
        
        if metric_type == PerformanceMetricType.RESPONSE_TIME:
            recommendations.extend([
                "检查数据库查询，添加必要的索引",
                "考虑添加缓存层",
                "优化热点代码路径",
                "检查网络延迟"
            ])
        elif metric_type == PerformanceMetricType.MEMORY_USAGE:
            recommendations.extend([
                "检查是否存在内存泄漏",
                "优化大对象的生命周期",
                "考虑使用对象池",
                "调整GC参数"
            ])
        elif metric_type == PerformanceMetricType.CPU_USAGE:
            recommendations.extend([
                "分析CPU热点，优化计算密集型代码",
                "考虑异步处理",
                "检查是否存在死循环",
                "优化算法复杂度"
            ])
        elif metric_type == PerformanceMetricType.ERROR_RATE:
            recommendations.extend([
                "分析错误日志，定位根本原因",
                "检查依赖服务状态",
                "添加重试和熔断机制",
                "检查配置是否正确"
            ])
        
        return recommendations[:5]

    def get_performance_degradations(self) -> List[PerformanceDegradation]:
        """获取性能退化列表"""
        degradations: List[PerformanceDegradation] = []
        
        for metric_type, metrics in self._metrics_history.items():
            anomaly_metrics = [m for m in metrics if m.is_anomaly]
            if not anomaly_metrics:
                continue
            
            latest = anomaly_metrics[-1]
            self._degradation_counter += 1
            
            degradation = PerformanceDegradation(
                degradation_id=f"PD-{self._degradation_counter:04d}",
                metric_type=metric_type,
                current_value=latest.value,
                baseline_value=latest.baseline_value,
                degradation_percent=latest.deviation_percent,
                severity=IssueSeverity.HIGH if latest.deviation_percent > 50 else IssueSeverity.MEDIUM,
                description=f"{metric_type.value} 退化 {latest.deviation_percent:.1f}%",
                possible_causes=self.DEGRADATION_CAUSES.get(metric_type, []),
                recommendations=self._generate_recommendations(metric_type, latest.value, {}),
                trend_data=[m.to_dict() for m in metrics[-10:]]
            )
            degradations.append(degradation)
        
        return degradations


class CodeSmellDetector(BaseDetector):
    """代码异味检测器
    
    检测各类代码异味，包括：
    - 长方法/长函数
    - 重复代码
    - 深度嵌套
    - 高复杂度
    - 长参数列表
    - 大类
    """

    THRESHOLDS = {
        "long_method_lines": 50,
        "long_method_complexity": 15,
        "deep_nesting": 4,
        "long_parameter_list": 5,
        "large_class_lines": 500,
        "large_class_methods": 20,
        "duplicate_code_min_lines": 6
    }

    REFACTORING_SUGGESTIONS = {
        "long_method": [
            "提取方法 (Extract Method)",
            "使用卫语句减少嵌套",
            "分解条件表达式"
        ],
        "deep_nesting": [
            "使用卫语句提前返回",
            "提取嵌套逻辑到独立方法",
            "使用多态替代条件"
        ],
        "long_parameter_list": [
            "引入参数对象 (Introduce Parameter Object)",
            "使用构建器模式",
            "保持对象完整"
        ],
        "large_class": [
            "提取类 (Extract Class)",
            "提取子类",
            "提取接口"
        ],
        "high_complexity": [
            "分解条件表达式",
            "使用策略模式",
            "使用状态模式"
        ],
        "duplicate_code": [
            "提取方法",
            "上移方法 (Pull Up Method)",
            "提取父类"
        ]
    }

    def __init__(self, codebase_path: Optional[Path] = None):
        super().__init__("code_smell_detector")
        self.codebase_path = codebase_path
        self._ast_cache: Dict[str, ast.AST] = {}
        self._smell_counter = 0

    async def detect(self, context: Dict[str, Any]) -> List[DetectedIssue]:
        """执行代码异味检测
        
        Args:
            context: 检测上下文，包含：
                - codebase_path: 代码库路径
                - file_patterns: 文件模式列表
                - thresholds: 自定义阈值
                
        Returns:
            检测到的问题列表
        """
        issues: List[DetectedIssue] = []
        
        codebase_path = context.get("codebase_path", self.codebase_path)
        if not codebase_path:
            return issues
        
        codebase_path = Path(codebase_path)
        if not codebase_path.exists():
            return issues
        
        thresholds = {**self.THRESHOLDS, **context.get("thresholds", {})}
        file_patterns = context.get("file_patterns", ["*.py"])
        
        for pattern in file_patterns:
            for file_path in codebase_path.rglob(pattern):
                if self._should_skip_file(file_path):
                    continue
                
                file_issues = await self._analyze_file(file_path, thresholds)
                issues.extend(file_issues)
        
        return issues

    def _should_skip_file(self, file_path: Path) -> bool:
        """判断是否跳过文件"""
        skip_patterns = [
            "__pycache__",
            ".git",
            "node_modules",
            "venv",
            ".venv",
            "site-packages",
            "test_",
            "_test.py"
        ]
        return any(p in str(file_path) for p in skip_patterns)

    async def _analyze_file(self, file_path: Path, thresholds: Dict[str, Any]) -> List[DetectedIssue]:
        """分析单个文件"""
        issues: List[DetectedIssue] = []
        
        try:
            tree = await self._get_ast(file_path)
            content = await self._read_file(file_path)
            lines = content.split("\n")
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                    func_issues = self._analyze_function(node, file_path, lines, thresholds)
                    issues.extend(func_issues)
                elif isinstance(node, ast.ClassDef):
                    class_issues = self._analyze_class(node, file_path, lines, thresholds)
                    issues.extend(class_issues)
            
            duplicate_issues = await self._detect_duplicates(file_path, content, thresholds)
            issues.extend(duplicate_issues)
            
        except SyntaxError as e:
            issue = DetectedIssue(
                issue_id=self._generate_issue_id(),
                category=IssueCategory.SYNTAX_ERROR,
                severity=IssueSeverity.HIGH,
                title="语法错误",
                description=f"文件 {file_path.name} 存在语法错误: {str(e)}",
                location=CodeLocation(
                    file_path=str(file_path),
                    line_number=e.lineno or 0,
                    code_snippet=e.text or ""
                ),
                confidence=DetectionConfidence.HIGH,
                suggestions=["修复语法错误"],
                tags=["syntax", "parse_error"],
                detector_name=self.name
            )
            issues.append(issue)
        except Exception as e:
            self.logger.debug(f"分析文件 {file_path} 时出错: {e}")
        
        return issues

    def _analyze_function(
        self,
        node: Union[ast.FunctionDef, ast.AsyncFunctionDef],
        file_path: Path,
        lines: List[str],
        thresholds: Dict[str, Any]
    ) -> List[DetectedIssue]:
        """分析函数"""
        issues: List[DetectedIssue] = []
        
        func_lines = node.end_lineno - node.lineno + 1 if hasattr(node, 'end_lineno') else 0
        
        if func_lines > thresholds["long_method_lines"]:
            location = CodeLocation(
                file_path=str(file_path),
                line_number=node.lineno,
                function_name=node.name,
                code_snippet=lines[node.lineno - 1] if node.lineno <= len(lines) else ""
            )
            
            issue = DetectedIssue(
                issue_id=self._generate_issue_id(),
                category=IssueCategory.CODE_SMELL,
                severity=IssueSeverity.MEDIUM,
                title="长方法",
                description=f"方法 '{node.name}' 有 {func_lines} 行，超过阈值 {thresholds['long_method_lines']} 行",
                location=location,
                confidence=DetectionConfidence.HIGH,
                suggestions=self.REFACTORING_SUGGESTIONS["long_method"],
                metrics={"lines": func_lines, "threshold": thresholds["long_method_lines"]},
                tags=["code_smell", "long_method"],
                detector_name=self.name
            )
            issues.append(issue)
        
        complexity = self._calculate_complexity(node)
        if complexity > thresholds["long_method_complexity"]:
            location = CodeLocation(
                file_path=str(file_path),
                line_number=node.lineno,
                function_name=node.name
            )
            
            issue = DetectedIssue(
                issue_id=self._generate_issue_id(),
                category=IssueCategory.CODE_SMELL,
                severity=IssueSeverity.MEDIUM,
                title="高复杂度方法",
                description=f"方法 '{node.name}' 圈复杂度为 {complexity}，超过阈值 {thresholds['long_method_complexity']}",
                location=location,
                confidence=DetectionConfidence.HIGH,
                suggestions=self.REFACTORING_SUGGESTIONS["high_complexity"],
                metrics={"complexity": complexity, "threshold": thresholds["long_method_complexity"]},
                tags=["code_smell", "high_complexity"],
                detector_name=self.name
            )
            issues.append(issue)
        
        nesting_depth = self._calculate_nesting_depth(node)
        if nesting_depth > thresholds["deep_nesting"]:
            location = CodeLocation(
                file_path=str(file_path),
                line_number=node.lineno,
                function_name=node.name
            )
            
            issue = DetectedIssue(
                issue_id=self._generate_issue_id(),
                category=IssueCategory.CODE_SMELL,
                severity=IssueSeverity.MEDIUM,
                title="深度嵌套",
                description=f"方法 '{node.name}' 嵌套深度为 {nesting_depth}，超过阈值 {thresholds['deep_nesting']}",
                location=location,
                confidence=DetectionConfidence.HIGH,
                suggestions=self.REFACTORING_SUGGESTIONS["deep_nesting"],
                metrics={"nesting_depth": nesting_depth, "threshold": thresholds["deep_nesting"]},
                tags=["code_smell", "deep_nesting"],
                detector_name=self.name
            )
            issues.append(issue)
        
        param_count = len(node.args.args) + len(node.args.kwonlyargs)
        if node.args.vararg:
            param_count += 1
        if node.args.kwarg:
            param_count += 1
        
        if param_count > thresholds["long_parameter_list"]:
            location = CodeLocation(
                file_path=str(file_path),
                line_number=node.lineno,
                function_name=node.name
            )
            
            issue = DetectedIssue(
                issue_id=self._generate_issue_id(),
                category=IssueCategory.CODE_SMELL,
                severity=IssueSeverity.LOW,
                title="长参数列表",
                description=f"方法 '{node.name}' 有 {param_count} 个参数，超过阈值 {thresholds['long_parameter_list']}",
                location=location,
                confidence=DetectionConfidence.HIGH,
                suggestions=self.REFACTORING_SUGGESTIONS["long_parameter_list"],
                metrics={"param_count": param_count, "threshold": thresholds["long_parameter_list"]},
                tags=["code_smell", "long_parameter_list"],
                detector_name=self.name
            )
            issues.append(issue)
        
        return issues

    def _analyze_class(
        self,
        node: ast.ClassDef,
        file_path: Path,
        lines: List[str],
        thresholds: Dict[str, Any]
    ) -> List[DetectedIssue]:
        """分析类"""
        issues: List[DetectedIssue] = []
        
        class_lines = node.end_lineno - node.lineno + 1 if hasattr(node, 'end_lineno') else 0
        method_count = sum(1 for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)))
        
        if class_lines > thresholds["large_class_lines"]:
            location = CodeLocation(
                file_path=str(file_path),
                line_number=node.lineno,
                class_name=node.name
            )
            
            issue = DetectedIssue(
                issue_id=self._generate_issue_id(),
                category=IssueCategory.CODE_SMELL,
                severity=IssueSeverity.MEDIUM,
                title="大类",
                description=f"类 '{node.name}' 有 {class_lines} 行，超过阈值 {thresholds['large_class_lines']} 行",
                location=location,
                confidence=DetectionConfidence.HIGH,
                suggestions=self.REFACTORING_SUGGESTIONS["large_class"],
                metrics={"lines": class_lines, "threshold": thresholds["large_class_lines"]},
                tags=["code_smell", "large_class"],
                detector_name=self.name
            )
            issues.append(issue)
        
        if method_count > thresholds["large_class_methods"]:
            location = CodeLocation(
                file_path=str(file_path),
                line_number=node.lineno,
                class_name=node.name
            )
            
            issue = DetectedIssue(
                issue_id=self._generate_issue_id(),
                category=IssueCategory.CODE_SMELL,
                severity=IssueSeverity.LOW,
                title="方法过多的类",
                description=f"类 '{node.name}' 有 {method_count} 个方法，超过阈值 {thresholds['large_class_methods']}",
                location=location,
                confidence=DetectionConfidence.HIGH,
                suggestions=self.REFACTORING_SUGGESTIONS["large_class"],
                metrics={"method_count": method_count, "threshold": thresholds["large_class_methods"]},
                tags=["code_smell", "large_class"],
                detector_name=self.name
            )
            issues.append(issue)
        
        return issues

    async def _detect_duplicates(
        self,
        file_path: Path,
        content: str,
        thresholds: Dict[str, Any]
    ) -> List[DetectedIssue]:
        """检测重复代码"""
        issues: List[DetectedIssue] = []
        
        lines = content.split("\n")
        min_lines = thresholds["duplicate_code_min_lines"]
        
        code_blocks: Dict[str, List[int]] = defaultdict(list)
        
        for i in range(len(lines) - min_lines + 1):
            block = "\n".join(lines[i:i + min_lines])
            normalized = self._normalize_code_block(block)
            if normalized:
                code_blocks[normalized].append(i + 1)
        
        for normalized_block, line_numbers in code_blocks.items():
            if len(line_numbers) > 1:
                location = CodeLocation(
                    file_path=str(file_path),
                    line_number=line_numbers[0]
                )
                
                issue = DetectedIssue(
                    issue_id=self._generate_issue_id(),
                    category=IssueCategory.CODE_SMELL,
                    severity=IssueSeverity.LOW,
                    title="重复代码",
                    description=f"检测到重复代码块，出现在行: {', '.join(map(str, line_numbers))}",
                    location=location,
                    confidence=DetectionConfidence.MEDIUM,
                    suggestions=self.REFACTORING_SUGGESTIONS["duplicate_code"],
                    metrics={"occurrences": len(line_numbers), "lines": line_numbers},
                    tags=["code_smell", "duplicate_code"],
                    detector_name=self.name
                )
                issues.append(issue)
        
        return issues[:5]

    def _normalize_code_block(self, block: str) -> str:
        """规范化代码块用于比较"""
        lines = []
        for line in block.split("\n"):
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                lines.append(stripped)
        return "\n".join(lines)

    def _calculate_complexity(self, node: ast.AST) -> int:
        """计算圈复杂度"""
        complexity = 1
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            elif isinstance(child, ast.comprehension):
                complexity += 1
                if child.ifs:
                    complexity += len(child.ifs)
        
        return complexity

    def _calculate_nesting_depth(self, node: ast.AST) -> int:
        """计算最大嵌套深度"""
        max_depth = 0
        
        def visit(n: ast.AST, current_depth: int) -> None:
            nonlocal max_depth
            max_depth = max(max_depth, current_depth)
            
            for child in ast.iter_child_nodes(n):
                if isinstance(child, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
                    visit(child, current_depth + 1)
                else:
                    visit(child, current_depth)
        
        visit(node, 0)
        return max_depth

    async def _get_ast(self, file_path: Path) -> ast.AST:
        """获取文件的AST"""
        path_str = str(file_path)
        if path_str not in self._ast_cache:
            content = await self._read_file(file_path)
            self._ast_cache[path_str] = ast.parse(content)
        return self._ast_cache[path_str]

    async def _read_file(self, file_path: Path) -> str:
        """读取文件内容"""
        loop = asyncio.get_event_loop()
        
        def read():
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                return f.read()
        
        return await loop.run_in_executor(None, read)

    def get_code_smells(self, issues: List[DetectedIssue]) -> List[CodeSmellInfo]:
        """从检测结果提取代码异味信息"""
        smells: List[CodeSmellInfo] = []
        
        for issue in issues:
            if issue.category != IssueCategory.CODE_SMELL:
                continue
            
            self._smell_counter += 1
            
            smell_type = "unknown"
            for tag in issue.tags:
                if tag in ["long_method", "deep_nesting", "high_complexity", 
                          "long_parameter_list", "large_class", "duplicate_code"]:
                    smell_type = tag
                    break
            
            smell = CodeSmellInfo(
                smell_type=smell_type,
                category="code_smell",
                severity=issue.severity,
                location=issue.location or CodeLocation(file_path="", line_number=0),
                description=issue.description,
                impact_score=issue.metrics.get("lines", 0) / 10.0,
                effort_score=1.0 if smell_type in ["duplicate_code", "long_parameter_list"] else 2.0,
                refactoring_suggestions=issue.suggestions
            )
            smells.append(smell)
        
        return smells


class IssueAwarenessEngine:
    """智能问题感知引擎
    
    整合所有检测器，提供全面的问题感知能力：
    - 错误模式识别
    - 性能退化检测
    - 代码异味检测
    - 与现有模块集成
    - 异步支持
    """
    
    def __init__(
        self,
        codebase_path: Optional[Union[str, Path]] = None,
        enable_error_detection: bool = True,
        enable_performance_detection: bool = True,
        enable_code_smell_detection: bool = True,
        custom_detectors: Optional[List[BaseDetector]] = None
    ):
        self.codebase_path = Path(codebase_path) if codebase_path else None
        self.logger = logging.getLogger("issue_awareness.engine")
        
        self.detectors: List[BaseDetector] = []
        
        if enable_error_detection:
            self.detectors.append(ErrorPatternRecognizer())
        
        if enable_performance_detection:
            self.detectors.append(PerformanceDegradationDetector())
        
        if enable_code_smell_detection:
            self.detectors.append(CodeSmellDetector(self.codebase_path))
        
        if custom_detectors:
            self.detectors.extend(custom_detectors)
        
        self._report_counter = 0
        self._log_analyzer = None
        self._issue_locator = None

    def integrate_with_log_analyzer(self, log_analyzer: Any) -> None:
        """与 log_analyzer.py 集成
        
        Args:
            log_analyzer: LogAnalyzer 实例
        """
        self._log_analyzer = log_analyzer
        self.logger.info("已与 log_analyzer 集成")

    def integrate_with_issue_locator(self, issue_locator: Any) -> None:
        """与 issue_locator.py 集成
        
        Args:
            issue_locator: IssueLocator 实例
        """
        self._issue_locator = issue_locator
        self.logger.info("已与 issue_locator 集成")

    async def analyze_comprehensive(
        self,
        error_messages: Optional[List[str]] = None,
        stack_traces: Optional[List[str]] = None,
        metrics: Optional[Dict[str, float]] = None,
        historical_data: Optional[List[Dict[str, Any]]] = None,
        thresholds: Optional[Dict[str, Any]] = None,
        file_patterns: Optional[List[str]] = None
    ) -> AwarenessReport:
        """执行全面的问题感知分析
        
        Args:
            error_messages: 错误消息列表
            stack_traces: 堆栈跟踪列表
            metrics: 性能指标字典
            historical_data: 历史数据
            thresholds: 自定义阈值
            file_patterns: 文件模式列表
            
        Returns:
            AwarenessReport 感知报告
        """
        start_time = time.time()
        
        context: Dict[str, Any] = {
            "codebase_path": self.codebase_path,
            "error_messages": error_messages or [],
            "stack_traces": stack_traces or [],
            "metrics": metrics or {},
            "historical_data": historical_data or [],
            "thresholds": thresholds or {},
            "file_patterns": file_patterns or ["*.py"]
        }
        
        if self._log_analyzer:
            try:
                log_context = await self._extract_from_log_analyzer()
                context["error_messages"].extend(log_context.get("error_messages", []))
                context["stack_traces"].extend(log_context.get("stack_traces", []))
            except Exception as e:
                self.logger.warning(f"从 log_analyzer 提取数据失败: {e}")
        
        all_issues: List[DetectedIssue] = []
        
        detection_tasks = [
            detector.detect(context)
            for detector in self.detectors
        ]
        
        if detection_tasks:
            results = await asyncio.gather(*detection_tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, list):
                    all_issues.extend(result)
                elif isinstance(result, Exception):
                    self.logger.error(f"检测器执行出错: {result}")
        
        if self._issue_locator:
            try:
                located_issues = await self._locate_issues(all_issues)
                all_issues.extend(located_issues)
            except Exception as e:
                self.logger.warning(f"使用 issue_locator 定位问题失败: {e}")
        
        performance_degradations = self._extract_performance_degradations()
        code_smells = self._extract_code_smells(all_issues)
        
        report = self._generate_report(
            all_issues,
            performance_degradations,
            code_smells,
            time.time() - start_time
        )
        
        return report

    async def _extract_from_log_analyzer(self) -> Dict[str, Any]:
        """从 log_analyzer 提取数据"""
        result: Dict[str, Any] = {
            "error_messages": [],
            "stack_traces": []
        }
        
        if not self._log_analyzer:
            return result
        
        if hasattr(self._log_analyzer, "get_error_entries"):
            error_entries = self._log_analyzer.get_error_entries()
            for entry in error_entries:
                if hasattr(entry, "message"):
                    result["error_messages"].append(entry.message)
                if hasattr(entry, "raw_line"):
                    result["stack_traces"].append(entry.raw_line)
        
        return result

    async def _locate_issues(self, issues: List[DetectedIssue]) -> List[DetectedIssue]:
        """使用 issue_locator 定位问题"""
        located_issues: List[DetectedIssue] = []
        
        if not self._issue_locator:
            return located_issues
        
        for issue in issues:
            if issue.location:
                continue
            
            try:
                if hasattr(self._issue_locator, "locate"):
                    located = self._issue_locator.locate(issue.description)
                    if located and hasattr(located, "primary_location") and located.primary_location:
                        issue.location = CodeLocation(
                            file_path=located.primary_location.file_path,
                            line_number=located.primary_location.line_number,
                            function_name=located.primary_location.function_name or "",
                            code_snippet=located.primary_location.code_snippet or ""
                        )
            except Exception as e:
                self.logger.debug(f"定位问题失败: {e}")
        
        return located_issues

    def _extract_performance_degradations(self) -> List[PerformanceDegradation]:
        """提取性能退化信息"""
        for detector in self.detectors:
            if isinstance(detector, PerformanceDegradationDetector):
                return detector.get_performance_degradations()
        return []

    def _extract_code_smells(self, issues: List[DetectedIssue]) -> List[CodeSmellInfo]:
        """提取代码异味信息"""
        for detector in self.detectors:
            if isinstance(detector, CodeSmellDetector):
                return detector.get_code_smells(issues)
        return []

    def _generate_report(
        self,
        issues: List[DetectedIssue],
        degradations: List[PerformanceDegradation],
        code_smells: List[CodeSmellInfo],
        duration: float
    ) -> AwarenessReport:
        """生成感知报告"""
        self._report_counter += 1
        
        issues_by_category: Dict[str, int] = defaultdict(int)
        issues_by_severity: Dict[str, int] = defaultdict(int)
        
        for issue in issues:
            issues_by_category[issue.category.value] += 1
            issues_by_severity[issue.severity.value] += 1
        
        health_score = self._calculate_health_score(issues)
        summary = self._generate_summary(issues, degradations, code_smells)
        recommendations = self._generate_recommendations(issues, degradations)
        
        return AwarenessReport(
            report_id=f"AR-{self._report_counter:05d}",
            generated_at=datetime.now().isoformat(),
            total_issues=len(issues),
            issues_by_category=dict(issues_by_category),
            issues_by_severity=dict(issues_by_severity),
            detected_issues=issues,
            performance_degradations=degradations,
            code_smells=code_smells,
            summary=summary,
            recommendations=recommendations,
            health_score=health_score,
            analysis_duration_ms=duration * 1000
        )

    def _calculate_health_score(self, issues: List[DetectedIssue]) -> float:
        """计算健康分数"""
        score = 100.0
        
        severity_weights = {
            IssueSeverity.CRITICAL: 20,
            IssueSeverity.HIGH: 10,
            IssueSeverity.MEDIUM: 5,
            IssueSeverity.LOW: 2,
            IssueSeverity.INFO: 0.5
        }
        
        for issue in issues:
            score -= severity_weights.get(issue.severity, 1)
        
        return max(0.0, min(100.0, score))

    def _generate_summary(
        self,
        issues: List[DetectedIssue],
        degradations: List[PerformanceDegradation],
        code_smells: List[CodeSmellInfo]
    ) -> str:
        """生成摘要"""
        parts = []
        
        if issues:
            critical = sum(1 for i in issues if i.severity == IssueSeverity.CRITICAL)
            high = sum(1 for i in issues if i.severity == IssueSeverity.HIGH)
            
            parts.append(f"检测到 {len(issues)} 个问题")
            if critical > 0:
                parts.append(f"其中 {critical} 个严重")
            if high > 0:
                parts.append(f"{high} 个高优先级")
        
        if degradations:
            parts.append(f"{len(degradations)} 个性能退化")
        
        if code_smells:
            parts.append(f"{len(code_smells)} 个代码异味")
        
        return "，".join(parts) if parts else "未检测到问题"

    def _generate_recommendations(
        self,
        issues: List[DetectedIssue],
        degradations: List[PerformanceDegradation]
    ) -> List[str]:
        """生成建议"""
        recommendations = []
        
        critical_issues = [i for i in issues if i.severity == IssueSeverity.CRITICAL]
        if critical_issues:
            recommendations.append(f"立即处理 {len(critical_issues)} 个严重问题")
        
        high_issues = [i for i in issues if i.severity == IssueSeverity.HIGH]
        if high_issues:
            recommendations.append(f"优先处理 {len(high_issues)} 个高优先级问题")
        
        if degradations:
            recommendations.append("关注性能退化趋势，考虑优化")
        
        code_smell_issues = [i for i in issues if i.category == IssueCategory.CODE_SMELL]
        if len(code_smell_issues) > 5:
            recommendations.append("考虑安排代码重构以改善代码质量")
        
        return recommendations[:5]

    async def analyze_file(self, file_path: Union[str, Path]) -> AwarenessReport:
        """分析单个文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            AwarenessReport 感知报告
        """
        file_path = Path(file_path)
        
        return await self.analyze_comprehensive(
            file_patterns=[file_path.name]
        )

    async def analyze_errors(
        self,
        error_messages: List[str],
        stack_traces: Optional[List[str]] = None
    ) -> AwarenessReport:
        """分析错误消息
        
        Args:
            error_messages: 错误消息列表
            stack_traces: 堆栈跟踪列表
            
        Returns:
            AwarenessReport 感知报告
        """
        return await self.analyze_comprehensive(
            error_messages=error_messages,
            stack_traces=stack_traces
        )

    async def analyze_performance(
        self,
        metrics: Dict[str, float],
        historical_data: Optional[List[Dict[str, Any]]] = None
    ) -> AwarenessReport:
        """分析性能指标
        
        Args:
            metrics: 性能指标字典
            historical_data: 历史数据
            
        Returns:
            AwarenessReport 感知报告
        """
        return await self.analyze_comprehensive(
            metrics=metrics,
            historical_data=historical_data
        )

    async def stream_analyze(
        self,
        context: Dict[str, Any]
    ) -> AsyncIterator[DetectedIssue]:
        """流式分析，逐步返回检测结果
        
        Args:
            context: 检测上下文
            
        Yields:
            DetectedIssue 检测到的问题
        """
        for detector in self.detectors:
            try:
                issues = await detector.detect(context)
                for issue in issues:
                    yield issue
            except Exception as e:
                self.logger.error(f"检测器 {detector.name} 执行出错: {e}")

    def get_detector_statistics(self) -> Dict[str, Any]:
        """获取检测器统计信息"""
        stats = {
            "total_detectors": len(self.detectors),
            "detector_names": [d.name for d in self.detectors],
            "integrations": {
                "log_analyzer": self._log_analyzer is not None,
                "issue_locator": self._issue_locator is not None
            }
        }
        
        for detector in self.detectors:
            stats[f"{detector.name}_issues_detected"] = detector._issue_counter
        
        return stats


async def main():
    """主函数示例"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="智能问题感知引擎",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--codebase",
        type=Path,
        help="代码库路径"
    )
    parser.add_argument(
        "--error",
        type=str,
        action="append",
        help="错误消息（可多次指定）"
    )
    parser.add_argument(
        "--metric",
        type=str,
        action="append",
        help="性能指标，格式: type=value（可多次指定）"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="json",
        choices=["json", "text"],
        help="输出格式"
    )
    
    args = parser.parse_args()
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    
    engine = IssueAwarenessEngine(codebase_path=args.codebase)
    
    error_messages = args.error or []
    
    metrics: Dict[str, float] = {}
    if args.metric:
        for m in args.metric:
            if "=" in m:
                key, value = m.split("=", 1)
                try:
                    metrics[key] = float(value)
                except ValueError:
                    pass
    
    report = await engine.analyze_comprehensive(
        error_messages=error_messages,
        metrics=metrics
    )
    
    if args.output == "json":
        print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
    else:
        print(f"\n{'=' * 60}")
        print(f"智能问题感知报告")
        print(f"{'=' * 60}")
        print(f"报告ID: {report.report_id}")
        print(f"生成时间: {report.generated_at}")
        print(f"健康分数: {report.health_score:.1f}/100")
        print(f"\n摘要: {report.summary}")
        print(f"\n问题统计:")
        for category, count in report.issues_by_category.items():
            print(f"  - {category}: {count}")
        print(f"\n建议:")
        for i, rec in enumerate(report.recommendations, 1):
            print(f"  {i}. {rec}")


if __name__ == "__main__":
    asyncio.run(main())
