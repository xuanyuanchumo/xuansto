#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
演化循环执行器 - Evolution Cycle Executor

实现演化周期的各个子循环执行器，包括问题检测、自动修复、优化学习和验证反馈。

核心功能:
- 问题检测循环（ProblemDetectionLoop）
- 自动修复循环（AutoFixLoop）
- 优化学习循环（OptimizationLearningLoop）
- 验证反馈循环（VerificationFeedbackLoop）
- 主执行器（EvolutionCycleExecutor）

使用示例:
    from evolution_cycle_executor import EvolutionCycleExecutor
    
    executor = EvolutionCycleExecutor(project_dir='./')
    await executor.run_full_cycle()
"""

import asyncio
import json
import logging
import os
import re
import threading
import time
import traceback
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
import uuid


class ProblemSeverity(Enum):
    """问题严重程度枚举"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ProblemCategory(Enum):
    """问题类别枚举"""
    SYNTAX_ERROR = "syntax_error"
    RUNTIME_ERROR = "runtime_error"
    LOGIC_ERROR = "logic_error"
    PERFORMANCE = "performance"
    SECURITY = "security"
    STYLE = "style"
    DEPENDENCY = "dependency"
    CONFIGURATION = "configuration"
    UNKNOWN = "unknown"


class FixStatus(Enum):
    """修复状态枚举"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    SKIPPED = "skipped"


class FixStrategy(Enum):
    """修复策略枚举"""
    AUTO_FIX = "auto_fix"
    TEMPLATE_BASED = "template_based"
    PATTERN_BASED = "pattern_based"
    LLM_ASSISTED = "llm_assisted"
    MANUAL_REQUIRED = "manual_required"


class LearningType(Enum):
    """学习类型枚举"""
    PATTERN_LEARNING = "pattern_learning"
    PERFORMANCE_LEARNING = "performance_learning"
    ERROR_LEARNING = "error_learning"
    BEST_PRACTICE = "best_practice"


class VerificationResult(Enum):
    """验证结果枚举"""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"


class CyclePhase(Enum):
    """循环阶段枚举"""
    INITIALIZATION = "initialization"
    DETECTION = "detection"
    ANALYSIS = "analysis"
    FIXING = "fixing"
    VERIFICATION = "verification"
    LEARNING = "learning"
    COMPLETED = "completed"
    FAILED = "failed"


class DetectorType(Enum):
    """检测器类型枚举"""
    CODE_SCANNER = "code_scanner"
    LOG_ANALYZER = "log_analyzer"
    PERFORMANCE_MONITOR = "performance_monitor"
    CUSTOM = "custom"


@dataclass
class DetectedProblem:
    """检测到的问题数据类"""
    problem_id: str
    title: str
    description: str
    severity: ProblemSeverity
    category: ProblemCategory
    location: Optional[Dict[str, Any]] = None
    pattern: Optional[str] = None
    occurrence_count: int = 1
    first_seen: datetime = field(default_factory=datetime.now)
    last_seen: datetime = field(default_factory=datetime.now)
    context: Dict[str, Any] = field(default_factory=dict)
    related_problems: List[str] = field(default_factory=list)
    detector_type: Optional[DetectorType] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "problem_id": self.problem_id,
            "title": self.title,
            "description": self.description,
            "severity": self.severity.value,
            "category": self.category.value,
            "location": self.location,
            "pattern": self.pattern,
            "occurrence_count": self.occurrence_count,
            "first_seen": self.first_seen.isoformat(),
            "last_seen": self.last_seen.isoformat(),
            "context": self.context,
            "related_problems": self.related_problems,
            "detector_type": self.detector_type.value if self.detector_type else None
        }


@dataclass
class FixAction:
    """修复动作数据类"""
    action_id: str
    problem_id: str
    strategy: FixStrategy
    description: str
    file_path: Optional[str] = None
    original_content: Optional[str] = None
    modified_content: Optional[str] = None
    status: FixStatus = FixStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    executed_at: Optional[datetime] = None
    rollback_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    validation_result: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_id": self.action_id,
            "problem_id": self.problem_id,
            "strategy": self.strategy.value,
            "description": self.description,
            "file_path": self.file_path,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
            "error_message": self.error_message,
            "validation_result": self.validation_result
        }


@dataclass
class PerformanceMetric:
    """性能指标数据类"""
    metric_id: str
    name: str
    value: float
    unit: str
    timestamp: datetime = field(default_factory=datetime.now)
    baseline: Optional[float] = None
    improvement: Optional[float] = None
    context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_id": self.metric_id,
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "timestamp": self.timestamp.isoformat(),
            "baseline": self.baseline,
            "improvement": self.improvement,
            "context": self.context
        }


@dataclass
class LearningRecord:
    """学习记录数据类"""
    record_id: str
    learning_type: LearningType
    problem_pattern: str
    solution_pattern: str
    success_rate: float
    application_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    last_applied: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    evaluation_score: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "record_id": self.record_id,
            "learning_type": self.learning_type.value,
            "problem_pattern": self.problem_pattern,
            "solution_pattern": self.solution_pattern,
            "success_rate": self.success_rate,
            "application_count": self.application_count,
            "created_at": self.created_at.isoformat(),
            "last_applied": self.last_applied.isoformat() if self.last_applied else None,
            "metadata": self.metadata,
            "evaluation_score": self.evaluation_score
        }


@dataclass
class VerificationRecord:
    """验证记录数据类"""
    verification_id: str
    target_type: str
    target_id: str
    result: VerificationResult
    test_cases: List[Dict[str, Any]] = field(default_factory=list)
    passed_count: int = 0
    failed_count: int = 0
    skipped_count: int = 0
    duration_seconds: float = 0.0
    feedback: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    performance_metrics: Optional[Dict[str, Any]] = None
    user_feedback: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "verification_id": self.verification_id,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "result": self.result.value,
            "test_cases": self.test_cases,
            "passed_count": self.passed_count,
            "failed_count": self.failed_count,
            "skipped_count": self.skipped_count,
            "duration_seconds": self.duration_seconds,
            "feedback": self.feedback,
            "created_at": self.created_at.isoformat(),
            "performance_metrics": self.performance_metrics,
            "user_feedback": self.user_feedback
        }


@dataclass
class CycleResult:
    """循环执行结果数据类"""
    cycle_id: str
    phase: CyclePhase
    success: bool
    started_at: datetime
    completed_at: Optional[datetime] = None
    problems_detected: List[DetectedProblem] = field(default_factory=list)
    fixes_applied: List[FixAction] = field(default_factory=list)
    learnings: List[LearningRecord] = field(default_factory=list)
    verifications: List[VerificationRecord] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "cycle_id": self.cycle_id,
            "phase": self.phase.value,
            "success": self.success,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "problems_detected": [p.to_dict() for p in self.problems_detected],
            "fixes_applied": [f.to_dict() for f in self.fixes_applied],
            "learnings": [l.to_dict() for l in self.learnings],
            "verifications": [v.to_dict() for v in self.verifications],
            "metrics": self.metrics,
            "errors": self.errors
        }


@dataclass
class FixHistory:
    """修复历史数据类"""
    history_id: str
    problem_id: str
    action_id: str
    strategy: FixStrategy
    status: FixStatus
    timestamp: datetime
    file_path: Optional[str] = None
    error_message: Optional[str] = None
    rollback_performed: bool = False
    duration_seconds: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "history_id": self.history_id,
            "problem_id": self.problem_id,
            "action_id": self.action_id,
            "strategy": self.strategy.value,
            "status": self.status.value,
            "timestamp": self.timestamp.isoformat(),
            "file_path": self.file_path,
            "error_message": self.error_message,
            "rollback_performed": self.rollback_performed,
            "duration_seconds": self.duration_seconds
        }


@dataclass
class VerificationReport:
    """验证报告数据类"""
    report_id: str
    cycle_id: str
    generated_at: datetime
    summary: str
    test_results: Dict[str, Any]
    performance_results: Dict[str, Any]
    user_feedback_summary: Dict[str, Any]
    recommendations: List[str]
    details: List[VerificationRecord]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "cycle_id": self.cycle_id,
            "generated_at": self.generated_at.isoformat(),
            "summary": self.summary,
            "test_results": self.test_results,
            "performance_results": self.performance_results,
            "user_feedback_summary": self.user_feedback_summary,
            "recommendations": self.recommendations,
            "details": [d.to_dict() for d in self.details]
        }


class BaseLoopExecutor(ABC):
    """循环执行器基类"""
    
    def __init__(self, project_dir: str, config: Optional[Dict[str, Any]] = None):
        self._project_dir = Path(project_dir)
        self._config = config or {}
        self._logger = logging.getLogger(self.__class__.__name__)
        self._lock = threading.Lock()
        self._running = False
        self._last_execution: Optional[datetime] = None
        self._execution_count = 0
    
    @abstractmethod
    async def execute(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行循环"""
        pass
    
    def _generate_id(self, prefix: str = "ID") -> str:
        return f"{prefix}-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"
    
    def _get_timestamp(self) -> datetime:
        return datetime.now()
    
    def is_running(self) -> bool:
        return self._running
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "running": self._running,
            "execution_count": self._execution_count,
            "last_execution": self._last_execution.isoformat() if self._last_execution else None
        }


class ProblemDetector(ABC):
    """问题检测器基类"""
    
    def __init__(self, detector_type: DetectorType):
        self._detector_type = detector_type
        self._logger = logging.getLogger(self.__class__.__name__)
    
    @property
    def detector_type(self) -> DetectorType:
        return self._detector_type
    
    @abstractmethod
    async def detect(self, project_dir: Path, context: Optional[Dict[str, Any]] = None) -> List[DetectedProblem]:
        """执行检测"""
        pass


class CodeScanner(ProblemDetector):
    """代码扫描检测器"""
    
    CODE_PATTERNS: List[Tuple[str, ProblemSeverity, ProblemCategory, str]] = [
        (r"TODO|FIXME|XXX|HACK", ProblemSeverity.LOW, ProblemCategory.STYLE, "代码待办"),
        (r"print\s*\(", ProblemSeverity.LOW, ProblemCategory.STYLE, "调试打印语句"),
        (r"except\s*:", ProblemSeverity.MEDIUM, ProblemCategory.LOGIC_ERROR, "空异常捕获"),
        (r"except\s*Exception\s*:", ProblemSeverity.MEDIUM, ProblemCategory.LOGIC_ERROR, "宽泛异常捕获"),
        (r"pass\s*$", ProblemSeverity.LOW, ProblemCategory.STYLE, "空代码块"),
        (r"import\s*\*", ProblemSeverity.MEDIUM, ProblemCategory.STYLE, "通配符导入"),
        (r"eval\s*\(", ProblemSeverity.HIGH, ProblemCategory.SECURITY, "不安全的eval调用"),
        (r"exec\s*\(", ProblemSeverity.HIGH, ProblemCategory.SECURITY, "不安全的exec调用"),
    ]
    
    def __init__(self):
        super().__init__(DetectorType.CODE_SCANNER)
    
    async def detect(self, project_dir: Path, context: Optional[Dict[str, Any]] = None) -> List[DetectedProblem]:
        problems = []
        code_extensions = context.get("code_extensions", ['.py', '.js', '.ts', '.java', '.go']) if context else ['.py', '.js', '.ts', '.java', '.go']
        
        for ext in code_extensions:
            for code_file in project_dir.rglob(f"*{ext}"):
                if 'node_modules' in str(code_file) or '__pycache__' in str(code_file) or '.git' in str(code_file):
                    continue
                
                try:
                    problems.extend(await self._scan_file(code_file))
                except Exception as e:
                    self._logger.debug(f"扫描文件失败 {code_file}: {e}")
        
        return problems
    
    async def _scan_file(self, file_path: Path) -> List[DetectedProblem]:
        problems = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            for pattern, severity, category, desc in self.CODE_PATTERNS:
                matches = re.finditer(pattern, content, re.MULTILINE)
                
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    
                    problem = DetectedProblem(
                        problem_id=self._generate_problem_id("CODE"),
                        title=desc,
                        description=f"在 {file_path.name} 中发现: {match.group()}",
                        severity=severity,
                        category=category,
                        location={
                            "file": str(file_path),
                            "line": line_num
                        },
                        pattern=pattern,
                        detector_type=DetectorType.CODE_SCANNER
                    )
                    problems.append(problem)
                    
        except Exception as e:
            self._logger.error(f"读取文件失败 {file_path}: {e}")
        
        return problems
    
    def _generate_problem_id(self, prefix: str) -> str:
        return f"{prefix}-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"


class LogAnalyzer(ProblemDetector):
    """日志分析检测器"""
    
    ERROR_PATTERNS: Dict[str, Tuple[ProblemSeverity, ProblemCategory]] = {
        r"SyntaxError": (ProblemSeverity.CRITICAL, ProblemCategory.SYNTAX_ERROR),
        r"ImportError": (ProblemSeverity.HIGH, ProblemCategory.DEPENDENCY),
        r"ModuleNotFoundError": (ProblemSeverity.HIGH, ProblemCategory.DEPENDENCY),
        r"TypeError": (ProblemSeverity.HIGH, ProblemCategory.RUNTIME_ERROR),
        r"ValueError": (ProblemSeverity.MEDIUM, ProblemCategory.RUNTIME_ERROR),
        r"KeyError": (ProblemSeverity.MEDIUM, ProblemCategory.RUNTIME_ERROR),
        r"AttributeError": (ProblemSeverity.MEDIUM, ProblemCategory.RUNTIME_ERROR),
        r"IndexError": (ProblemSeverity.MEDIUM, ProblemCategory.RUNTIME_ERROR),
        r"FileNotFoundError": (ProblemSeverity.HIGH, ProblemCategory.CONFIGURATION),
        r"PermissionError": (ProblemSeverity.HIGH, ProblemCategory.CONFIGURATION),
        r"TimeoutError": (ProblemSeverity.MEDIUM, ProblemCategory.PERFORMANCE),
        r"MemoryError": (ProblemSeverity.CRITICAL, ProblemCategory.PERFORMANCE),
        r"RecursionError": (ProblemSeverity.HIGH, ProblemCategory.LOGIC_ERROR),
        r"ConnectionError": (ProblemSeverity.HIGH, ProblemCategory.CONFIGURATION),
    }
    
    LOG_LEVEL_PATTERNS: Dict[str, Tuple[ProblemSeverity, ProblemCategory, str]] = {
        r"\[ERROR\]": (ProblemSeverity.HIGH, ProblemCategory.RUNTIME_ERROR, "error_log"),
        r"\[WARN(ING)?\]": (ProblemSeverity.MEDIUM, ProblemCategory.RUNTIME_ERROR, "warning_log"),
        r"\[CRITICAL\]": (ProblemSeverity.CRITICAL, ProblemCategory.RUNTIME_ERROR, "critical_log"),
        r"\[FATAL\]": (ProblemSeverity.CRITICAL, ProblemCategory.RUNTIME_ERROR, "fatal_log"),
    }
    
    def __init__(self):
        super().__init__(DetectorType.LOG_ANALYZER)
    
    async def detect(self, project_dir: Path, context: Optional[Dict[str, Any]] = None) -> List[DetectedProblem]:
        problems = []
        log_dirs = context.get("log_dirs", ["logs", "log", "."]) if context else ["logs", "log", "."]
        
        for log_dir_name in log_dirs:
            log_dir = project_dir / log_dir_name
            if not log_dir.exists():
                continue
            
            for log_file in log_dir.rglob("*.log"):
                try:
                    problems.extend(await self._analyze_log_file(log_file))
                except Exception as e:
                    self._logger.warning(f"分析日志文件失败 {log_file}: {e}")
        
        return problems
    
    async def _analyze_log_file(self, log_file: Path) -> List[DetectedProblem]:
        problems = []
        
        try:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            for pattern, (severity, category, log_type) in self.LOG_LEVEL_PATTERNS.items():
                matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
                
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    line_content = content.split('\n')[line_num - 1] if line_num > 0 else ""
                    
                    problem = DetectedProblem(
                        problem_id=self._generate_problem_id("LOG"),
                        title=f"日志{log_type}: {pattern}",
                        description=line_content[:500],
                        severity=severity,
                        category=category,
                        location={
                            "file": str(log_file),
                            "line": line_num
                        },
                        pattern=pattern,
                        context={"log_type": log_type, "match": match.group()},
                        detector_type=DetectorType.LOG_ANALYZER
                    )
                    problems.append(problem)
            
            for pattern, (severity, category) in self.ERROR_PATTERNS.items():
                matches = re.finditer(pattern, content, re.MULTILINE)
                
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    
                    problem = DetectedProblem(
                        problem_id=self._generate_problem_id("ERR"),
                        title=f"错误类型: {match.group()}",
                        description=f"在日志中发现 {match.group()} 错误",
                        severity=severity,
                        category=category,
                        location={
                            "file": str(log_file),
                            "line": line_num
                        },
                        pattern=pattern,
                        detector_type=DetectorType.LOG_ANALYZER
                    )
                    problems.append(problem)
                    
        except Exception as e:
            self._logger.error(f"读取日志文件失败 {log_file}: {e}")
        
        return problems
    
    def _generate_problem_id(self, prefix: str) -> str:
        return f"{prefix}-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"


class PerformanceMonitor(ProblemDetector):
    """性能监控检测器"""
    
    def __init__(self):
        super().__init__(DetectorType.PERFORMANCE_MONITOR)
        self._metrics_history: List[Dict[str, Any]] = []
    
    async def detect(self, project_dir: Path, context: Optional[Dict[str, Any]] = None) -> List[DetectedProblem]:
        problems = []
        
        metrics = context.get("performance_metrics", {}) if context else {}
        
        if not metrics:
            metrics = await self._collect_basic_metrics(project_dir)
        
        problems.extend(self._check_performance_thresholds(metrics))
        
        self._metrics_history.append({
            "timestamp": datetime.now().isoformat(),
            "metrics": metrics
        })
        
        if len(self._metrics_history) > 100:
            self._metrics_history = self._metrics_history[-100:]
        
        return problems
    
    async def _collect_basic_metrics(self, project_dir: Path) -> Dict[str, Any]:
        metrics = {}
        
        try:
            file_count = sum(1 for _ in project_dir.rglob("*.py") if '__pycache__' not in str(_))
            metrics["file_count"] = file_count
            
            total_size = sum(f.stat().st_size for f in project_dir.rglob("*.py") if '__pycache__' not in str(f) and f.exists())
            metrics["total_code_size_mb"] = total_size / (1024 * 1024)
            
            if metrics["total_code_size_mb"] > 10:
                metrics["large_codebase"] = True
            
        except Exception as e:
            self._logger.error(f"收集性能指标失败: {e}")
        
        return metrics
    
    def _check_performance_thresholds(self, metrics: Dict[str, Any]) -> List[DetectedProblem]:
        problems = []
        
        if metrics.get("total_code_size_mb", 0) > 50:
            problem = DetectedProblem(
                problem_id=self._generate_problem_id("PERF"),
                title="代码库体积过大",
                description=f"代码库总大小: {metrics['total_code_size_mb']:.2f} MB",
                severity=ProblemSeverity.MEDIUM,
                category=ProblemCategory.PERFORMANCE,
                context=metrics,
                detector_type=DetectorType.PERFORMANCE_MONITOR
            )
            problems.append(problem)
        
        if metrics.get("file_count", 0) > 500:
            problem = DetectedProblem(
                problem_id=self._generate_problem_id("PERF"),
                title="代码文件数量过多",
                description=f"代码文件数量: {metrics['file_count']}",
                severity=ProblemSeverity.LOW,
                category=ProblemCategory.PERFORMANCE,
                context=metrics,
                detector_type=DetectorType.PERFORMANCE_MONITOR
            )
            problems.append(problem)
        
        return problems
    
    def _generate_problem_id(self, prefix: str) -> str:
        return f"{prefix}-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"


class ProblemDetectionLoop(BaseLoopExecutor):
    """问题检测循环
    
    负责扫描代码、分析日志、监控性能，并对问题进行分类和优先级排序。
    支持自定义问题检测器注册。
    """
    
    def __init__(
        self,
        project_dir: str,
        config: Optional[Dict[str, Any]] = None,
        log_dirs: Optional[List[str]] = None
    ):
        super().__init__(project_dir, config)
        self._log_dirs = log_dirs or ["logs", "log", "."]
        self._detected_problems: Dict[str, DetectedProblem] = {}
        self._problem_history: List[DetectedProblem] = []
        self._pattern_cache: Dict[str, int] = {}
        
        self._detectors: Dict[DetectorType, ProblemDetector] = {
            DetectorType.CODE_SCANNER: CodeScanner(),
            DetectorType.LOG_ANALYZER: LogAnalyzer(),
            DetectorType.PERFORMANCE_MONITOR: PerformanceMonitor(),
        }
        
        self._custom_detectors: List[ProblemDetector] = []
    
    def register_detector(self, detector: ProblemDetector) -> None:
        """注册自定义问题检测器"""
        self._custom_detectors.append(detector)
        self._logger.info(f"已注册自定义检测器: {detector.__class__.__name__}")
    
    def unregister_detector(self, detector: ProblemDetector) -> bool:
        """注销自定义问题检测器"""
        if detector in self._custom_detectors:
            self._custom_detectors.remove(detector)
            self._logger.info(f"已注销自定义检测器: {detector.__class__.__name__}")
            return True
        return False
    
    def get_registered_detectors(self) -> List[str]:
        """获取已注册的检测器列表"""
        detectors = [d.__class__.__name__ for d in self._detectors.values()]
        detectors.extend([d.__class__.__name__ for d in self._custom_detectors])
        return detectors
    
    async def execute(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行问题检测循环"""
        with self._lock:
            self._running = True
        
        start_time = self._get_timestamp()
        cycle_id = self._generate_id("DETECT")
        context = context or {}
        
        try:
            self._logger.info(f"开始问题检测循环: {cycle_id}")
            
            all_problems = []
            
            for detector_type, detector in self._detectors.items():
                try:
                    problems = await detector.detect(self._project_dir, context)
                    all_problems.extend(problems)
                    self._logger.debug(f"检测器 {detector_type.value} 发现 {len(problems)} 个问题")
                except Exception as e:
                    self._logger.error(f"检测器 {detector_type.value} 执行失败: {e}")
            
            for custom_detector in self._custom_detectors:
                try:
                    problems = await custom_detector.detect(self._project_dir, context)
                    all_problems.extend(problems)
                    self._logger.debug(f"自定义检测器发现 {len(problems)} 个问题")
                except Exception as e:
                    self._logger.error(f"自定义检测器执行失败: {e}")
            
            pattern_problems = await self._detect_patterns()
            all_problems.extend(pattern_problems)
            
            classified_problems = self._classify_and_prioritize(all_problems)
            
            self._detected_problems = {p.problem_id: p for p in classified_problems}
            self._problem_history.extend(classified_problems)
            
            self._execution_count += 1
            self._last_execution = self._get_timestamp()
            
            result = {
                "success": True,
                "cycle_id": cycle_id,
                "problems_detected": len(classified_problems),
                "by_severity": self._count_by_severity(classified_problems),
                "by_category": self._count_by_category(classified_problems),
                "by_detector": self._count_by_detector(classified_problems),
                "problems": [p.to_dict() for p in classified_problems],
                "detectors_used": self.get_registered_detectors(),
                "duration_seconds": (self._get_timestamp() - start_time).total_seconds()
            }
            
            self._logger.info(f"问题检测完成: 发现 {len(classified_problems)} 个问题")
            return result
            
        except Exception as e:
            self._logger.error(f"问题检测失败: {e}")
            return {
                "success": False,
                "cycle_id": cycle_id,
                "error": str(e),
                "traceback": traceback.format_exc()
            }
        finally:
            with self._lock:
                self._running = False
    
    async def _detect_patterns(self) -> List[DetectedProblem]:
        """检测重复模式"""
        problems = []
        
        pattern_counts: Dict[str, int] = defaultdict(int)
        pattern_locations: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        
        for ext in ['.py', '.log']:
            for file_path in self._project_dir.rglob(f"*{ext}"):
                if 'node_modules' in str(file_path) or '__pycache__' in str(file_path):
                    continue
                
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    error_pattern = r"(Error|Exception|Failed|Warning):\s*(.+)"
                    matches = re.finditer(error_pattern, content, re.IGNORECASE)
                    
                    for match in matches:
                        pattern_key = match.group(0)[:100]
                        pattern_counts[pattern_key] += 1
                        
                        line_num = content[:match.start()].count('\n') + 1
                        pattern_locations[pattern_key].append({
                            "file": str(file_path),
                            "line": line_num
                        })
                        
                except Exception:
                    pass
        
        for pattern, count in pattern_counts.items():
            if count >= 3:
                problem = DetectedProblem(
                    problem_id=self._generate_id("PATTERN"),
                    title=f"重复模式检测 (出现 {count} 次)",
                    description=f"检测到重复出现的模式: {pattern[:200]}",
                    severity=ProblemSeverity.MEDIUM if count >= 5 else ProblemSeverity.LOW,
                    category=ProblemCategory.RUNTIME_ERROR,
                    pattern=pattern,
                    occurrence_count=count,
                    context={"locations": pattern_locations[pattern][:10]},
                    detector_type=DetectorType.CODE_SCANNER
                )
                problems.append(problem)
        
        return problems
    
    def _classify_and_prioritize(self, problems: List[DetectedProblem]) -> List[DetectedProblem]:
        """分类和优先级排序"""
        severity_order = {
            ProblemSeverity.CRITICAL: 0,
            ProblemSeverity.HIGH: 1,
            ProblemSeverity.MEDIUM: 2,
            ProblemSeverity.LOW: 3,
            ProblemSeverity.INFO: 4
        }
        
        deduplicated: Dict[str, DetectedProblem] = {}
        for problem in problems:
            key = f"{problem.category.value}:{problem.pattern or problem.title}"
            if key in deduplicated:
                deduplicated[key].occurrence_count += 1
                deduplicated[key].last_seen = problem.last_seen
            else:
                deduplicated[key] = problem
        
        return sorted(
            deduplicated.values(),
            key=lambda p: (severity_order.get(p.severity, 99), -p.occurrence_count)
        )
    
    def _count_by_severity(self, problems: List[DetectedProblem]) -> Dict[str, int]:
        counts: Dict[str, int] = defaultdict(int)
        for p in problems:
            counts[p.severity.value] += 1
        return dict(counts)
    
    def _count_by_category(self, problems: List[DetectedProblem]) -> Dict[str, int]:
        counts: Dict[str, int] = defaultdict(int)
        for p in problems:
            counts[p.category.value] += 1
        return dict(counts)
    
    def _count_by_detector(self, problems: List[DetectedProblem]) -> Dict[str, int]:
        counts: Dict[str, int] = defaultdict(int)
        for p in problems:
            detector_name = p.detector_type.value if p.detector_type else "unknown"
            counts[detector_name] += 1
        return dict(counts)
    
    def get_detected_problems(self) -> List[DetectedProblem]:
        return list(self._detected_problems.values())
    
    def get_problem_by_id(self, problem_id: str) -> Optional[DetectedProblem]:
        return self._detected_problems.get(problem_id)
    
    def get_problem_history(self, limit: int = 100) -> List[DetectedProblem]:
        return self._problem_history[-limit:]


class AutoFixLoop(BaseLoopExecutor):
    """自动修复循环
    
    负责选择修复策略、执行修复、验证修复结果，并支持回滚机制。
    记录完整的修复历史。
    """
    
    FIX_TEMPLATES: Dict[str, Dict[str, Any]] = {
        "empty_except": {
            "pattern": r"except\s*:",
            "fix": "except Exception as e:\n    logger.error(f\"Error: {e}\")",
            "strategy": FixStrategy.TEMPLATE_BASED,
            "risk": "low"
        },
        "broad_except": {
            "pattern": r"except\s*Exception\s*:",
            "fix": "except Exception as e:\n    logger.error(f\"Unexpected error: {e}\")",
            "strategy": FixStrategy.TEMPLATE_BASED,
            "risk": "low"
        },
        "print_statement": {
            "pattern": r"print\s*\(",
            "fix": "logger.info(",
            "strategy": FixStrategy.PATTERN_BASED,
            "risk": "low"
        },
        "wildcard_import": {
            "pattern": r"from\s+(\S+)\s+import\s+\*",
            "fix": "from \\1 import ",
            "strategy": FixStrategy.TEMPLATE_BASED,
            "risk": "medium"
        }
    }
    
    def __init__(
        self,
        project_dir: str,
        config: Optional[Dict[str, Any]] = None,
        dry_run: bool = False
    ):
        super().__init__(project_dir, config)
        self._dry_run = dry_run
        self._fix_actions: Dict[str, FixAction] = {}
        self._rollback_stack: List[Dict[str, Any]] = []
        self._max_rollback_depth = 10
        self._fix_history: List[FixHistory] = []
    
    async def execute(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行自动修复循环"""
        with self._lock:
            self._running = True
        
        start_time = self._get_timestamp()
        cycle_id = self._generate_id("FIX")
        context = context or {}
        
        try:
            self._logger.info(f"开始自动修复循环: {cycle_id}")
            
            problems = context.get("problems", [])
            if problems and isinstance(problems, list):
                problems = [DetectedProblem(**p) if isinstance(p, dict) else p for p in problems]
            
            fix_actions = await self._select_fix_strategies(problems)
            
            executed_fixes = await self._execute_fixes(fix_actions)
            
            verified_fixes = await self._verify_fixes(executed_fixes)
            
            self._fix_actions = {f.action_id: f for f in verified_fixes}
            
            self._record_fix_history(verified_fixes)
            
            self._execution_count += 1
            self._last_execution = self._get_timestamp()
            
            result = {
                "success": True,
                "cycle_id": cycle_id,
                "fixes_attempted": len(fix_actions),
                "fixes_successful": sum(1 for f in verified_fixes if f.status == FixStatus.SUCCESS),
                "fixes_failed": sum(1 for f in verified_fixes if f.status == FixStatus.FAILED),
                "fixes_rolled_back": sum(1 for f in verified_fixes if f.status == FixStatus.ROLLED_BACK),
                "fixes": [f.to_dict() for f in verified_fixes],
                "dry_run": self._dry_run,
                "duration_seconds": (self._get_timestamp() - start_time).total_seconds()
            }
            
            self._logger.info(f"自动修复完成: {result['fixes_successful']}/{result['fixes_attempted']} 成功")
            return result
            
        except Exception as e:
            self._logger.error(f"自动修复失败: {e}")
            return {
                "success": False,
                "cycle_id": cycle_id,
                "error": str(e),
                "traceback": traceback.format_exc()
            }
        finally:
            with self._lock:
                self._running = False
    
    async def _select_fix_strategies(self, problems: List[DetectedProblem]) -> List[FixAction]:
        """选择修复策略"""
        actions = []
        
        for problem in problems:
            strategy = self._determine_strategy(problem)
            
            action = FixAction(
                action_id=self._generate_id("ACTION"),
                problem_id=problem.problem_id,
                strategy=strategy,
                description=f"修复: {problem.title}",
                file_path=problem.location.get("file") if problem.location else None,
                status=FixStatus.PENDING
            )
            actions.append(action)
        
        return actions
    
    def _determine_strategy(self, problem: DetectedProblem) -> FixStrategy:
        """确定修复策略"""
        if problem.category == ProblemCategory.SYNTAX_ERROR:
            return FixStrategy.AUTO_FIX
        
        if problem.pattern:
            for template_name, template in self.FIX_TEMPLATES.items():
                if re.search(template["pattern"], problem.pattern or ""):
                    return FixStrategy.TEMPLATE_BASED
        
        if problem.category in [ProblemCategory.STYLE, ProblemCategory.PERFORMANCE]:
            return FixStrategy.PATTERN_BASED
        
        if problem.severity in [ProblemSeverity.CRITICAL, ProblemSeverity.HIGH]:
            return FixStrategy.LLM_ASSISTED
        
        return FixStrategy.MANUAL_REQUIRED
    
    async def _execute_fixes(self, actions: List[FixAction]) -> List[FixAction]:
        """执行修复"""
        executed = []
        
        for action in actions:
            action_start_time = self._get_timestamp()
            try:
                action.status = FixStatus.IN_PROGRESS
                
                if action.strategy == FixStrategy.TEMPLATE_BASED:
                    result = await self._apply_template_fix(action)
                elif action.strategy == FixStrategy.PATTERN_BASED:
                    result = await self._apply_pattern_fix(action)
                elif action.strategy == FixStrategy.AUTO_FIX:
                    result = await self._apply_auto_fix(action)
                else:
                    result = {"success": False, "reason": "需要手动修复"}
                
                if result.get("success"):
                    action.status = FixStatus.SUCCESS
                    action.executed_at = self._get_timestamp()
                    
                    if result.get("rollback_data"):
                        action.rollback_data = result["rollback_data"]
                        self._push_rollback(action)
                else:
                    action.status = FixStatus.FAILED
                    action.error_message = result.get("reason", "未知错误")
                
            except Exception as e:
                action.status = FixStatus.FAILED
                action.error_message = str(e)
                self._logger.error(f"执行修复失败 {action.action_id}: {e}")
            
            executed.append(action)
        
        return executed
    
    async def _apply_template_fix(self, action: FixAction) -> Dict[str, Any]:
        """应用模板修复"""
        if not action.file_path or not os.path.exists(action.file_path):
            return {"success": False, "reason": "文件不存在"}
        
        try:
            with open(action.file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            action.original_content = original_content
            
            modified_content = original_content
            for template_name, template in self.FIX_TEMPLATES.items():
                if re.search(template["pattern"], original_content):
                    modified_content = re.sub(
                        template["pattern"],
                        template["fix"],
                        modified_content
                    )
            
            if modified_content == original_content:
                return {"success": False, "reason": "未找到匹配的模板"}
            
            if not self._dry_run:
                with open(action.file_path, 'w', encoding='utf-8') as f:
                    f.write(modified_content)
            
            action.modified_content = modified_content
            
            return {
                "success": True,
                "rollback_data": {
                    "file_path": action.file_path,
                    "original_content": original_content
                }
            }
            
        except Exception as e:
            return {"success": False, "reason": str(e)}
    
    async def _apply_pattern_fix(self, action: FixAction) -> Dict[str, Any]:
        """应用模式修复"""
        return await self._apply_template_fix(action)
    
    async def _apply_auto_fix(self, action: FixAction) -> Dict[str, Any]:
        """应用自动修复"""
        return await self._apply_template_fix(action)
    
    async def _verify_fixes(self, actions: List[FixAction]) -> List[FixAction]:
        """验证修复结果"""
        verified = []
        
        for action in actions:
            if action.status != FixStatus.SUCCESS:
                verified.append(action)
                continue
            
            try:
                if action.file_path and os.path.exists(action.file_path):
                    with open(action.file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    syntax_valid = self._check_syntax(content, action.file_path)
                    
                    action.validation_result = {
                        "syntax_valid": syntax_valid,
                        "verified_at": self._get_timestamp().isoformat()
                    }
                    
                    if not syntax_valid:
                        self._logger.warning(f"修复后语法检查失败，回滚: {action.action_id}")
                        rollback_success = await self._rollback_fix(action)
                        if rollback_success:
                            action.status = FixStatus.ROLLED_BACK
                        else:
                            action.status = FixStatus.FAILED
                            action.error_message = "语法检查失败且回滚失败"
                
            except Exception as e:
                self._logger.error(f"验证修复失败: {e}")
            
            verified.append(action)
        
        return verified
    
    def _check_syntax(self, content: str, file_path: str) -> bool:
        """检查语法"""
        if file_path.endswith('.py'):
            try:
                compile(content, file_path, 'exec')
                return True
            except SyntaxError:
                return False
        return True
    
    def _push_rollback(self, action: FixAction) -> None:
        """压入回滚栈"""
        if len(self._rollback_stack) >= self._max_rollback_depth:
            self._rollback_stack.pop(0)
        
        self._rollback_stack.append({
            "action_id": action.action_id,
            "file_path": action.file_path,
            "original_content": action.original_content,
            "timestamp": self._get_timestamp().isoformat()
        })
    
    async def _rollback_fix(self, action: FixAction) -> bool:
        """回滚修复"""
        if not action.rollback_data:
            return False
        
        try:
            file_path = action.rollback_data.get("file_path")
            original_content = action.rollback_data.get("original_content")
            
            if file_path and original_content is not None:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(original_content)
                
                self._logger.info(f"已回滚修复: {action.action_id}")
                return True
                
        except Exception as e:
            self._logger.error(f"回滚失败: {e}")
        
        return False
    
    async def rollback_all(self) -> Dict[str, Any]:
        """回滚所有修复"""
        rolled_back = 0
        failed = 0
        
        for action in self._fix_actions.values():
            if action.status == FixStatus.SUCCESS:
                success = await self._rollback_fix(action)
                if success:
                    action.status = FixStatus.ROLLED_BACK
                    rolled_back += 1
                else:
                    failed += 1
        
        return {
            "success": failed == 0,
            "rolled_back": rolled_back,
            "failed": failed
        }
    
    def _record_fix_history(self, actions: List[FixAction]) -> None:
        """记录修复历史"""
        for action in actions:
            history = FixHistory(
                history_id=self._generate_id("HIST"),
                problem_id=action.problem_id,
                action_id=action.action_id,
                strategy=action.strategy,
                status=action.status,
                timestamp=action.executed_at or self._get_timestamp(),
                file_path=action.file_path,
                error_message=action.error_message,
                rollback_performed=action.status == FixStatus.ROLLED_BACK,
                duration_seconds=(action.executed_at - action.created_at).total_seconds() if action.executed_at else 0
            )
            self._fix_history.append(history)
        
        if len(self._fix_history) > 1000:
            self._fix_history = self._fix_history[-1000:]
    
    def get_fix_actions(self) -> List[FixAction]:
        return list(self._fix_actions.values())
    
    def get_fix_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取修复历史"""
        return [h.to_dict() for h in self._fix_history[-limit:]]
    
    def get_fix_statistics(self) -> Dict[str, Any]:
        """获取修复统计信息"""
        if not self._fix_history:
            return {"total_fixes": 0}
        
        total = len(self._fix_history)
        by_status: Dict[str, int] = defaultdict(int)
        by_strategy: Dict[str, int] = defaultdict(int)
        
        for h in self._fix_history:
            by_status[h.status.value] += 1
            by_strategy[h.strategy.value] += 1
        
        return {
            "total_fixes": total,
            "by_status": dict(by_status),
            "by_strategy": dict(by_strategy),
            "success_rate": by_status.get("success", 0) / total if total > 0 else 0
        }


class OptimizationLearningLoop(BaseLoopExecutor):
    """优化学习循环
    
    负责收集性能指标、生成优化建议、更新知识库，并支持学习结果评估。
    """
    
    def __init__(
        self,
        project_dir: str,
        config: Optional[Dict[str, Any]] = None,
        knowledge_base_path: Optional[str] = None
    ):
        super().__init__(project_dir, config)
        self._knowledge_base_path = Path(knowledge_base_path or self._project_dir / ".evolution" / "knowledge_base.json")
        self._knowledge_base_path.parent.mkdir(parents=True, exist_ok=True)
        self._metrics: List[PerformanceMetric] = []
        self._learnings: Dict[str, LearningRecord] = {}
        self._optimization_suggestions: List[Dict[str, Any]] = []
        self._evaluation_results: List[Dict[str, Any]] = []
        self._load_knowledge_base()
    
    def _load_knowledge_base(self) -> None:
        """加载知识库"""
        if self._knowledge_base_path.exists():
            try:
                with open(self._knowledge_base_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for record_data in data.get("learnings", []):
                    record = LearningRecord(
                        record_id=record_data["record_id"],
                        learning_type=LearningType(record_data["learning_type"]),
                        problem_pattern=record_data["problem_pattern"],
                        solution_pattern=record_data["solution_pattern"],
                        success_rate=record_data["success_rate"],
                        application_count=record_data.get("application_count", 0),
                        created_at=datetime.fromisoformat(record_data["created_at"]),
                        last_applied=datetime.fromisoformat(record_data["last_applied"]) if record_data.get("last_applied") else None,
                        metadata=record_data.get("metadata", {}),
                        evaluation_score=record_data.get("evaluation_score")
                    )
                    self._learnings[record.record_id] = record
                    
                self._logger.info(f"已加载知识库: {len(self._learnings)} 条学习记录")
                
            except Exception as e:
                self._logger.error(f"加载知识库失败: {e}")
    
    def _save_knowledge_base(self) -> None:
        """保存知识库"""
        try:
            data = {
                "version": "1.0",
                "updated_at": datetime.now().isoformat(),
                "learnings": [l.to_dict() for l in self._learnings.values()]
            }
            
            with open(self._knowledge_base_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self._logger.error(f"保存知识库失败: {e}")
    
    async def execute(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行优化学习循环"""
        with self._lock:
            self._running = True
        
        start_time = self._get_timestamp()
        cycle_id = self._generate_id("LEARN")
        context = context or {}
        
        try:
            self._logger.info(f"开始优化学习循环: {cycle_id}")
            
            metrics = await self._collect_metrics(context)
            
            suggestions = await self._generate_suggestions(metrics, context)
            
            new_learnings = await self._update_knowledge_base(context)
            
            evaluation_results = await self._evaluate_learnings(new_learnings)
            
            self._metrics.extend(metrics)
            self._optimization_suggestions.extend(suggestions)
            self._evaluation_results.extend(evaluation_results)
            
            self._execution_count += 1
            self._last_execution = self._get_timestamp()
            
            result = {
                "success": True,
                "cycle_id": cycle_id,
                "metrics_collected": len(metrics),
                "suggestions_generated": len(suggestions),
                "learnings_updated": len(new_learnings),
                "evaluations_performed": len(evaluation_results),
                "metrics": [m.to_dict() for m in metrics],
                "suggestions": suggestions,
                "learnings": [l.to_dict() for l in new_learnings],
                "evaluations": evaluation_results,
                "duration_seconds": (self._get_timestamp() - start_time).total_seconds()
            }
            
            self._logger.info(f"优化学习完成: 收集 {len(metrics)} 个指标, 生成 {len(suggestions)} 条建议")
            return result
            
        except Exception as e:
            self._logger.error(f"优化学习失败: {e}")
            return {
                "success": False,
                "cycle_id": cycle_id,
                "error": str(e),
                "traceback": traceback.format_exc()
            }
        finally:
            with self._lock:
                self._running = False
    
    async def _collect_metrics(self, context: Dict[str, Any]) -> List[PerformanceMetric]:
        """收集性能指标"""
        metrics = []
        
        if "fixes" in context:
            fix_count = len(context["fixes"])
            success_count = sum(1 for f in context["fixes"] if f.get("status") == "success")
            
            metrics.append(PerformanceMetric(
                metric_id=self._generate_id("METRIC"),
                name="fix_success_rate",
                value=success_count / fix_count if fix_count > 0 else 0,
                unit="ratio",
                context={"total_fixes": fix_count, "successful_fixes": success_count}
            ))
        
        if "problems" in context:
            problem_count = len(context["problems"])
            by_severity = defaultdict(int)
            for p in context["problems"]:
                if isinstance(p, dict):
                    by_severity[p.get("severity", "unknown")] += 1
            
            metrics.append(PerformanceMetric(
                metric_id=self._generate_id("METRIC"),
                name="problem_count",
                value=problem_count,
                unit="count",
                context={"by_severity": dict(by_severity)}
            ))
        
        metrics.append(PerformanceMetric(
            metric_id=self._generate_id("METRIC"),
            name="cycle_execution_count",
            value=self._execution_count + 1,
            unit="count"
        ))
        
        file_count = sum(1 for _ in self._project_dir.rglob("*.py") if '__pycache__' not in str(_))
        metrics.append(PerformanceMetric(
            metric_id=self._generate_id("METRIC"),
            name="code_file_count",
            value=file_count,
            unit="count"
        ))
        
        performance_metrics = await self._detect_performance_optimizations()
        metrics.extend(performance_metrics)
        
        return metrics
    
    async def _detect_performance_optimizations(self) -> List[PerformanceMetric]:
        """检测性能优化机会"""
        metrics = []
        
        try:
            total_size = 0
            large_files = []
            
            for py_file in self._project_dir.rglob("*.py"):
                if '__pycache__' in str(py_file):
                    continue
                
                try:
                    size = py_file.stat().st_size
                    total_size += size
                    
                    if size > 50000:
                        large_files.append({
                            "file": str(py_file.relative_to(self._project_dir)),
                            "size_kb": size / 1024
                        })
                except Exception:
                    pass
            
            metrics.append(PerformanceMetric(
                metric_id=self._generate_id("METRIC"),
                name="total_code_size_kb",
                value=total_size / 1024,
                unit="KB",
                context={"large_files": large_files[:10]}
            ))
            
            if large_files:
                metrics.append(PerformanceMetric(
                    metric_id=self._generate_id("METRIC"),
                    name="large_file_count",
                    value=len(large_files),
                    unit="count",
                    context={"threshold_kb": 50}
                ))
                
        except Exception as e:
            self._logger.error(f"检测性能优化失败: {e}")
        
        return metrics
    
    async def _generate_suggestions(
        self,
        metrics: List[PerformanceMetric],
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """生成优化建议"""
        suggestions = []
        
        for metric in metrics:
            if metric.name == "fix_success_rate" and metric.value < 0.7:
                suggestions.append({
                    "type": "fix_strategy",
                    "priority": "high",
                    "suggestion": "修复成功率较低，建议优化修复策略或增加人工审核",
                    "metric": metric.name,
                    "value": metric.value
                })
            
            if metric.name == "problem_count" and metric.value > 20:
                suggestions.append({
                    "type": "code_quality",
                    "priority": "medium",
                    "suggestion": "问题数量较多，建议进行代码重构或增加代码审查",
                    "metric": metric.name,
                    "value": metric.value
                })
            
            if metric.name == "large_file_count" and metric.value > 0:
                suggestions.append({
                    "type": "performance",
                    "priority": "medium",
                    "suggestion": f"发现 {metric.value} 个大文件，建议拆分以提高可维护性",
                    "metric": metric.name,
                    "value": metric.value
                })
        
        if context.get("fixes"):
            failed_fixes = [f for f in context["fixes"] if f.get("status") == "failed"]
            if len(failed_fixes) > 0:
                suggestions.append({
                    "type": "fix_improvement",
                    "priority": "high",
                    "suggestion": f"有 {len(failed_fixes)} 个修复失败，建议分析失败原因并改进修复模板",
                    "failed_fixes": [f.get("action_id") for f in failed_fixes]
                })
        
        best_practices = await self._learn_best_practices(context)
        suggestions.extend(best_practices)
        
        return suggestions
    
    async def _learn_best_practices(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """学习最佳实践"""
        suggestions = []
        
        if context.get("verifications"):
            passed_verifications = [v for v in context["verifications"] if v.get("result") == "passed"]
            
            if passed_verifications:
                suggestions.append({
                    "type": "best_practice",
                    "priority": "low",
                    "suggestion": f"记录 {len(passed_verifications)} 个成功验证案例作为最佳实践",
                    "count": len(passed_verifications)
                })
        
        return suggestions
    
    async def _update_knowledge_base(self, context: Dict[str, Any]) -> List[LearningRecord]:
        """更新知识库"""
        new_learnings = []
        
        if context.get("fixes"):
            for fix in context["fixes"]:
                if fix.get("status") == "success" and fix.get("strategy"):
                    pattern_key = f"{fix.get('strategy')}:{fix.get('problem_id', '')[:50]}"
                    
                    existing = None
                    for learning in self._learnings.values():
                        if learning.problem_pattern == pattern_key:
                            existing = learning
                            break
                    
                    if existing:
                        existing.application_count += 1
                        existing.last_applied = self._get_timestamp()
                        existing.success_rate = (
                            existing.success_rate * (existing.application_count - 1) + 1.0
                        ) / existing.application_count
                    else:
                        record = LearningRecord(
                            record_id=self._generate_id("LEARN"),
                            learning_type=LearningType.PATTERN_LEARNING,
                            problem_pattern=pattern_key,
                            solution_pattern=fix.get("description", ""),
                            success_rate=1.0,
                            application_count=1,
                            metadata={"strategy": fix.get("strategy")}
                        )
                        self._learnings[record.record_id] = record
                        new_learnings.append(record)
        
        self._save_knowledge_base()
        
        return new_learnings
    
    async def _evaluate_learnings(self, learnings: List[LearningRecord]) -> List[Dict[str, Any]]:
        """评估学习结果"""
        evaluations = []
        
        for learning in learnings:
            evaluation_score = self._calculate_evaluation_score(learning)
            learning.evaluation_score = evaluation_score
            
            evaluation = {
                "record_id": learning.record_id,
                "learning_type": learning.learning_type.value,
                "evaluation_score": evaluation_score,
                "success_rate": learning.success_rate,
                "application_count": learning.application_count,
                "recommendation": self._get_learning_recommendation(evaluation_score)
            }
            evaluations.append(evaluation)
        
        return evaluations
    
    def _calculate_evaluation_score(self, learning: LearningRecord) -> float:
        """计算学习评估分数"""
        score = 0.0
        
        score += learning.success_rate * 0.5
        
        if learning.application_count >= 5:
            score += 0.3
        elif learning.application_count >= 2:
            score += 0.15
        
        if learning.learning_type == LearningType.BEST_PRACTICE:
            score += 0.2
        elif learning.learning_type == LearningType.PATTERN_LEARNING:
            score += 0.1
        
        return min(score, 1.0)
    
    def _get_learning_recommendation(self, score: float) -> str:
        """获取学习建议"""
        if score >= 0.8:
            return "高质量学习结果，建议广泛应用"
        elif score >= 0.6:
            return "中等质量学习结果，建议谨慎应用"
        elif score >= 0.4:
            return "低质量学习结果，建议进一步验证"
        else:
            return "学习结果质量较差，建议重新学习"
    
    def get_learnings(self) -> List[LearningRecord]:
        return list(self._learnings.values())
    
    def get_metrics(self) -> List[PerformanceMetric]:
        return self._metrics.copy()
    
    def get_suggestions(self) -> List[Dict[str, Any]]:
        return self._optimization_suggestions.copy()
    
    def get_evaluation_results(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取评估结果"""
        return self._evaluation_results[-limit:]


class VerificationFeedbackLoop(BaseLoopExecutor):
    """验证反馈循环
    
    负责执行测试验证、性能验证、收集用户反馈，并生成验证报告。
    """
    
    def __init__(
        self,
        project_dir: str,
        config: Optional[Dict[str, Any]] = None,
        test_command: Optional[str] = None
    ):
        super().__init__(project_dir, config)
        self._test_command = test_command or self._config.get("test_command", "pytest")
        self._verifications: Dict[str, VerificationRecord] = {}
        self._feedback_history: List[Dict[str, Any]] = []
        self._verification_reports: List[VerificationReport] = []
    
    async def execute(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行验证反馈循环"""
        with self._lock:
            self._running = True
        
        start_time = self._get_timestamp()
        cycle_id = self._generate_id("VERIFY")
        context = context or {}
        
        try:
            self._logger.info(f"开始验证反馈循环: {cycle_id}")
            
            test_results = await self._run_tests(context)
            
            performance_results = await self._verify_performance(context)
            
            verification_records = await self._verify_results(test_results, context)
            
            user_feedback = await self._collect_user_feedback(verification_records, context)
            
            feedback = await self._collect_feedback(verification_records, context)
            
            analysis = self._analyze_feedback(feedback)
            
            report = await self._generate_verification_report(
                cycle_id, verification_records, test_results, performance_results, user_feedback
            )
            
            for record in verification_records:
                self._verifications[record.verification_id] = record
            
            self._feedback_history.extend(feedback)
            
            if report:
                self._verification_reports.append(report)
            
            self._execution_count += 1
            self._last_execution = self._get_timestamp()
            
            result = {
                "success": True,
                "cycle_id": cycle_id,
                "tests_run": sum(v.passed_count + v.failed_count + v.skipped_count for v in verification_records),
                "tests_passed": sum(v.passed_count for v in verification_records),
                "tests_failed": sum(v.failed_count for v in verification_records),
                "verifications": [v.to_dict() for v in verification_records],
                "feedback": feedback,
                "analysis": analysis,
                "report_id": report.report_id if report else None,
                "duration_seconds": (self._get_timestamp() - start_time).total_seconds()
            }
            
            self._logger.info(f"验证反馈完成: {result['tests_passed']}/{result['tests_run']} 测试通过")
            return result
            
        except Exception as e:
            self._logger.error(f"验证反馈失败: {e}")
            return {
                "success": False,
                "cycle_id": cycle_id,
                "error": str(e),
                "traceback": traceback.format_exc()
            }
        finally:
            with self._lock:
                self._running = False
    
    async def _run_tests(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行测试验证"""
        test_results = {
            "success": True,
            "tests": [],
            "output": "",
            "error": None
        }
        
        try:
            if self._test_command:
                proc = await asyncio.create_subprocess_shell(
                    self._test_command,
                    cwd=str(self._project_dir),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=300
                )
                
                test_results["output"] = stdout.decode('utf-8', errors='ignore')
                test_results["error"] = stderr.decode('utf-8', errors='ignore') if stderr else None
                test_results["success"] = proc.returncode == 0
                
                test_results["tests"] = self._parse_test_output(test_results["output"])
            else:
                test_results["tests"] = self._mock_tests(context)
                
        except asyncio.TimeoutError:
            test_results["success"] = False
            test_results["error"] = "测试执行超时"
        except Exception as e:
            test_results["success"] = False
            test_results["error"] = str(e)
        
        return test_results
    
    async def _verify_performance(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行性能验证"""
        performance_results = {
            "success": True,
            "metrics": {},
            "issues": []
        }
        
        try:
            start_time = time.time()
            
            file_count = sum(1 for _ in self._project_dir.rglob("*.py") if '__pycache__' not in str(_))
            
            end_time = time.time()
            scan_duration = end_time - start_time
            
            performance_results["metrics"] = {
                "file_count": file_count,
                "scan_duration_seconds": scan_duration,
                "files_per_second": file_count / scan_duration if scan_duration > 0 else 0
            }
            
            if scan_duration > 10:
                performance_results["issues"].append({
                    "type": "slow_scan",
                    "message": f"项目扫描耗时较长: {scan_duration:.2f}秒"
                })
            
        except Exception as e:
            performance_results["success"] = False
            performance_results["issues"].append({
                "type": "error",
                "message": str(e)
            })
        
        return performance_results
    
    def _parse_test_output(self, output: str) -> List[Dict[str, Any]]:
        """解析测试输出"""
        tests = []
        
        passed_pattern = r"(\d+)\s+passed"
        failed_pattern = r"(\d+)\s+failed"
        skipped_pattern = r"(\d+)\s+skipped"
        
        passed_match = re.search(passed_pattern, output)
        failed_match = re.search(failed_pattern, output)
        skipped_match = re.search(skipped_pattern, output)
        
        if passed_match:
            tests.append({"type": "summary", "passed": int(passed_match.group(1))})
        if failed_match:
            tests.append({"type": "summary", "failed": int(failed_match.group(1))})
        if skipped_match:
            tests.append({"type": "summary", "skipped": int(skipped_match.group(1))})
        
        return tests
    
    def _mock_tests(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """模拟测试（当没有测试命令时）"""
        return [
            {"name": "syntax_check", "status": "passed", "duration": 0.1},
            {"name": "import_check", "status": "passed", "duration": 0.05}
        ]
    
    async def _verify_results(
        self,
        test_results: Dict[str, Any],
        context: Dict[str, Any]
    ) -> List[VerificationRecord]:
        """验证结果"""
        records = []
        
        verification = VerificationRecord(
            verification_id=self._generate_id("VER"),
            target_type="test_suite",
            target_id="all",
            result=VerificationResult.PASSED if test_results["success"] else VerificationResult.FAILED,
            test_cases=test_results.get("tests", []),
            created_at=self._get_timestamp()
        )
        
        for test in test_results.get("tests", []):
            if test.get("type") == "summary":
                verification.passed_count = test.get("passed", 0)
                verification.failed_count = test.get("failed", 0)
                verification.skipped_count = test.get("skipped", 0)
        
        records.append(verification)
        
        if context.get("fixes"):
            for fix in context["fixes"]:
                if fix.get("status") == "success":
                    fix_verification = VerificationRecord(
                        verification_id=self._generate_id("VER"),
                        target_type="fix",
                        target_id=fix.get("action_id", ""),
                        result=VerificationResult.PASSED if test_results["success"] else VerificationResult.FAILED,
                        test_cases=[{"fix_id": fix.get("action_id")}],
                        passed_count=1 if test_results["success"] else 0,
                        failed_count=0 if test_results["success"] else 1
                    )
                    records.append(fix_verification)
        
        return records
    
    async def _collect_user_feedback(
        self,
        verifications: List[VerificationRecord],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """收集用户反馈"""
        user_feedback = {
            "collected": False,
            "feedback_items": [],
            "summary": {}
        }
        
        feedback_items = context.get("user_feedback", [])
        
        if feedback_items:
            user_feedback["collected"] = True
            user_feedback["feedback_items"] = feedback_items
            
            positive_count = sum(1 for f in feedback_items if f.get("sentiment") == "positive")
            negative_count = sum(1 for f in feedback_items if f.get("sentiment") == "negative")
            neutral_count = sum(1 for f in feedback_items if f.get("sentiment") == "neutral")
            
            user_feedback["summary"] = {
                "total": len(feedback_items),
                "positive": positive_count,
                "negative": negative_count,
                "neutral": neutral_count,
                "satisfaction_rate": positive_count / len(feedback_items) if feedback_items else 0
            }
        
        for verification in verifications:
            if verification.result == VerificationResult.FAILED:
                user_feedback["feedback_items"].append({
                    "type": "auto_generated",
                    "target": verification.target_id,
                    "message": f"验证失败需要关注: {verification.failed_count} 个测试失败",
                    "sentiment": "negative"
                })
        
        return user_feedback
    
    async def _collect_feedback(
        self,
        verifications: List[VerificationRecord],
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """收集反馈"""
        feedback = []
        
        for verification in verifications:
            if verification.result == VerificationResult.FAILED:
                feedback.append({
                    "type": "verification_failure",
                    "target": verification.target_id,
                    "message": f"验证失败: {verification.failed_count} 个测试失败",
                    "severity": "high",
                    "timestamp": self._get_timestamp().isoformat()
                })
            
            if verification.result == VerificationResult.PASSED:
                feedback.append({
                    "type": "verification_success",
                    "target": verification.target_id,
                    "message": f"验证通过: {verification.passed_count} 个测试通过",
                    "severity": "info",
                    "timestamp": self._get_timestamp().isoformat()
                })
        
        if context.get("problems"):
            high_severity_count = sum(
                1 for p in context["problems"]
                if isinstance(p, dict) and p.get("severity") in ["critical", "high"]
            )
            if high_severity_count > 0:
                feedback.append({
                    "type": "high_severity_issues",
                    "message": f"发现 {high_severity_count} 个高严重性问题",
                    "severity": "high",
                    "timestamp": self._get_timestamp().isoformat()
                })
        
        return feedback
    
    def _analyze_feedback(self, feedback: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析反馈"""
        analysis = {
            "total_feedback": len(feedback),
            "by_type": defaultdict(int),
            "by_severity": defaultdict(int),
            "recommendations": []
        }
        
        for fb in feedback:
            analysis["by_type"][fb.get("type", "unknown")] += 1
            analysis["by_severity"][fb.get("severity", "info")] += 1
        
        if analysis["by_severity"].get("high", 0) > 0:
            analysis["recommendations"].append("存在高严重性问题，建议优先处理")
        
        if analysis["by_type"].get("verification_failure", 0) > 0:
            analysis["recommendations"].append("存在验证失败，建议检查修复是否正确")
        
        analysis["by_type"] = dict(analysis["by_type"])
        analysis["by_severity"] = dict(analysis["by_severity"])
        
        return analysis
    
    async def _generate_verification_report(
        self,
        cycle_id: str,
        verifications: List[VerificationRecord],
        test_results: Dict[str, Any],
        performance_results: Dict[str, Any],
        user_feedback: Dict[str, Any]
    ) -> Optional[VerificationReport]:
        """生成验证报告"""
        try:
            report_id = self._generate_id("RPT")
            
            total_passed = sum(v.passed_count for v in verifications)
            total_failed = sum(v.failed_count for v in verifications)
            total_tests = total_passed + total_failed
            
            if total_tests > 0:
                pass_rate = total_passed / total_tests
                if pass_rate >= 0.9:
                    summary = f"验证结果优秀: {total_passed}/{total_tests} 测试通过 ({pass_rate:.1%})"
                elif pass_rate >= 0.7:
                    summary = f"验证结果良好: {total_passed}/{total_tests} 测试通过 ({pass_rate:.1%})"
                else:
                    summary = f"验证结果需要改进: {total_passed}/{total_tests} 测试通过 ({pass_rate:.1%})"
            else:
                summary = "无测试结果"
            
            recommendations = []
            if total_failed > 0:
                recommendations.append(f"建议修复 {total_failed} 个失败的测试")
            if performance_results.get("issues"):
                recommendations.extend([i["message"] for i in performance_results["issues"]])
            if user_feedback.get("summary", {}).get("negative", 0) > 0:
                recommendations.append("存在负面用户反馈，建议关注")
            
            report = VerificationReport(
                report_id=report_id,
                cycle_id=cycle_id,
                generated_at=self._get_timestamp(),
                summary=summary,
                test_results=test_results,
                performance_results=performance_results,
                user_feedback_summary=user_feedback.get("summary", {}),
                recommendations=recommendations,
                details=verifications
            )
            
            self._save_verification_report(report)
            
            return report
            
        except Exception as e:
            self._logger.error(f"生成验证报告失败: {e}")
            return None
    
    def _save_verification_report(self, report: VerificationReport) -> None:
        """保存验证报告"""
        try:
            report_dir = self._project_dir / ".evolution" / "reports"
            report_dir.mkdir(parents=True, exist_ok=True)
            
            report_path = report_dir / f"verification_report_{report.report_id}.json"
            
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)
            
            self._logger.info(f"验证报告已保存: {report_path}")
            
        except Exception as e:
            self._logger.error(f"保存验证报告失败: {e}")
    
    def get_verifications(self) -> List[VerificationRecord]:
        return list(self._verifications.values())
    
    def get_feedback_history(self) -> List[Dict[str, Any]]:
        return self._feedback_history.copy()
    
    def get_verification_reports(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取验证报告"""
        return [r.to_dict() for r in self._verification_reports[-limit:]]


class EvolutionCycleExecutor:
    """演化周期执行器主类
    
    整合所有循环执行器，实现完整的演化周期。
    """
    
    def __init__(
        self,
        project_dir: str,
        config: Optional[Dict[str, Any]] = None
    ):
        self._project_dir = Path(project_dir)
        self._config = config or {}
        self._logger = logging.getLogger('EvolutionCycleExecutor')
        
        self._detection_loop = ProblemDetectionLoop(
            str(self._project_dir),
            self._config.get("detection", {}),
            self._config.get("log_dirs")
        )
        
        self._fix_loop = AutoFixLoop(
            str(self._project_dir),
            self._config.get("fix", {}),
            self._config.get("dry_run", False)
        )
        
        self._learning_loop = OptimizationLearningLoop(
            str(self._project_dir),
            self._config.get("learning", {}),
            self._config.get("knowledge_base_path")
        )
        
        self._verification_loop = VerificationFeedbackLoop(
            str(self._project_dir),
            self._config.get("verification", {}),
            self._config.get("test_command")
        )
        
        self._current_phase = CyclePhase.INITIALIZATION
        self._cycle_history: List[CycleResult] = []
        self._running = False
        self._lock = threading.Lock()
    
    @property
    def current_phase(self) -> CyclePhase:
        return self._current_phase
    
    @property
    def detection_loop(self) -> ProblemDetectionLoop:
        return self._detection_loop
    
    @property
    def fix_loop(self) -> AutoFixLoop:
        return self._fix_loop
    
    @property
    def learning_loop(self) -> OptimizationLearningLoop:
        return self._learning_loop
    
    @property
    def verification_loop(self) -> VerificationFeedbackLoop:
        return self._verification_loop
    
    async def run_full_cycle(self, context: Optional[Dict[str, Any]] = None) -> CycleResult:
        """运行完整演化周期"""
        with self._lock:
            if self._running:
                raise RuntimeError("演化周期正在运行中")
            self._running = True
        
        cycle_id = self._generate_id("CYCLE")
        start_time = self._get_timestamp()
        
        result = CycleResult(
            cycle_id=cycle_id,
            phase=CyclePhase.INITIALIZATION,
            success=False,
            started_at=start_time
        )
        
        try:
            self._logger.info(f"开始完整演化周期: {cycle_id}")
            
            self._current_phase = CyclePhase.DETECTION
            result.phase = CyclePhase.DETECTION
            detection_result = await self._detection_loop.execute(context)
            
            if not detection_result.get("success"):
                result.errors.append(f"问题检测失败: {detection_result.get('error')}")
                result.phase = CyclePhase.FAILED
                return result
            
            result.problems_detected = [
                DetectedProblem(**p) if isinstance(p, dict) else p
                for p in detection_result.get("problems", [])
            ]
            
            self._current_phase = CyclePhase.FIXING
            result.phase = CyclePhase.FIXING
            fix_context = {
                "problems": detection_result.get("problems", [])
            }
            fix_result = await self._fix_loop.execute(fix_context)
            
            if not fix_result.get("success"):
                result.errors.append(f"自动修复失败: {fix_result.get('error')}")
            
            result.fixes_applied = [
                FixAction(**f) if isinstance(f, dict) else f
                for f in fix_result.get("fixes", [])
            ]
            
            self._current_phase = CyclePhase.VERIFICATION
            result.phase = CyclePhase.VERIFICATION
            verify_context = {
                "problems": detection_result.get("problems", []),
                "fixes": fix_result.get("fixes", [])
            }
            verify_result = await self._verification_loop.execute(verify_context)
            
            if not verify_result.get("success"):
                result.errors.append(f"验证失败: {verify_result.get('error')}")
            
            result.verifications = [
                VerificationRecord(**v) if isinstance(v, dict) else v
                for v in verify_result.get("verifications", [])
            ]
            
            self._current_phase = CyclePhase.LEARNING
            result.phase = CyclePhase.LEARNING
            learn_context = {
                "problems": detection_result.get("problems", []),
                "fixes": fix_result.get("fixes", []),
                "verifications": verify_result.get("verifications", [])
            }
            learn_result = await self._learning_loop.execute(learn_context)
            
            if not learn_result.get("success"):
                result.errors.append(f"学习失败: {learn_result.get('error')}")
            
            result.learnings = [
                LearningRecord(**l) if isinstance(l, dict) else l
                for l in learn_result.get("learnings", [])
            ]
            
            self._current_phase = CyclePhase.COMPLETED
            result.phase = CyclePhase.COMPLETED
            result.success = len(result.errors) == 0
            result.completed_at = self._get_timestamp()
            
            result.metrics = {
                "problems_detected": len(result.problems_detected),
                "fixes_applied": len(result.fixes_applied),
                "fixes_successful": sum(1 for f in result.fixes_applied if f.status == FixStatus.SUCCESS),
                "verifications_passed": sum(1 for v in result.verifications if v.result == VerificationResult.PASSED),
                "learnings_recorded": len(result.learnings),
                "duration_seconds": (result.completed_at - result.started_at).total_seconds()
            }
            
            self._cycle_history.append(result)
            
            self._logger.info(f"演化周期完成: {cycle_id}, 成功: {result.success}")
            return result
            
        except Exception as e:
            self._logger.error(f"演化周期执行失败: {e}")
            result.phase = CyclePhase.FAILED
            result.errors.append(str(e))
            result.completed_at = self._get_timestamp()
            self._cycle_history.append(result)
            return result
            
        finally:
            self._current_phase = CyclePhase.INITIALIZATION
            with self._lock:
                self._running = False
    
    async def run_detection_only(self) -> Dict[str, Any]:
        """仅运行问题检测"""
        return await self._detection_loop.execute()
    
    async def run_fix_only(self, problems: List[DetectedProblem]) -> Dict[str, Any]:
        """仅运行自动修复"""
        context = {"problems": [p.to_dict() if hasattr(p, 'to_dict') else p for p in problems]}
        return await self._fix_loop.execute(context)
    
    async def run_verification_only(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """仅运行验证"""
        return await self._verification_loop.execute(context)
    
    async def run_learning_only(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """仅运行学习"""
        return await self._learning_loop.execute(context)
    
    async def rollback_fixes(self) -> Dict[str, Any]:
        """回滚所有修复"""
        return await self._fix_loop.rollback_all()
    
    def register_custom_detector(self, detector: ProblemDetector) -> None:
        """注册自定义问题检测器"""
        self._detection_loop.register_detector(detector)
    
    def get_status(self) -> Dict[str, Any]:
        """获取执行器状态"""
        return {
            "running": self._running,
            "current_phase": self._current_phase.value,
            "cycle_count": len(self._cycle_history),
            "detection_stats": self._detection_loop.get_stats(),
            "fix_stats": self._fix_loop.get_stats(),
            "learning_stats": self._learning_loop.get_stats(),
            "verification_stats": self._verification_loop.get_stats()
        }
    
    def get_cycle_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取周期历史"""
        return [c.to_dict() for c in self._cycle_history[-limit:]]
    
    def get_last_cycle(self) -> Optional[CycleResult]:
        """获取最后一个周期"""
        return self._cycle_history[-1] if self._cycle_history else None
    
    def _generate_id(self, prefix: str = "ID") -> str:
        return f"{prefix}-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"
    
    def _get_timestamp(self) -> datetime:
        return datetime.now()
    
    def save_report(self, output_path: Optional[str] = None) -> str:
        """保存报告"""
        output_path = output_path or str(self._project_dir / ".evolution" / "reports" / f"cycle_report_{datetime.now().strftime('%Y%m%d%H%M%S')}.json")
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        report = {
            "generated_at": datetime.now().isoformat(),
            "total_cycles": len(self._cycle_history),
            "cycles": self.get_cycle_history(),
            "current_status": self.get_status(),
            "fix_statistics": self._fix_loop.get_fix_statistics(),
            "learning_evaluations": self._learning_loop.get_evaluation_results(10),
            "verification_reports": self._verification_loop.get_verification_reports(5)
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        self._logger.info(f"报告已保存: {output_path}")
        return output_path


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='演化周期执行器')
    parser.add_argument('--project', default='.', help='项目目录')
    parser.add_argument('--config', help='配置文件路径')
    parser.add_argument('--detect-only', action='store_true', help='仅运行问题检测')
    parser.add_argument('--dry-run', action='store_true', help='试运行模式（不实际修改文件）')
    parser.add_argument('--report', help='报告输出路径')
    
    args = parser.parse_args()
    
    config = {}
    if args.config:
        with open(args.config, 'r', encoding='utf-8') as f:
            config = json.load(f)
    
    if args.dry_run:
        config["dry_run"] = True
    
    executor = EvolutionCycleExecutor(args.project, config)
    
    if args.detect_only:
        result = await executor.run_detection_only()
    else:
        result = await executor.run_full_cycle()
    
    print(json.dumps(result.to_dict() if hasattr(result, 'to_dict') else result, indent=2, default=str, ensure_ascii=False))
    
    if args.report:
        executor.save_report(args.report)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    asyncio.run(main())
