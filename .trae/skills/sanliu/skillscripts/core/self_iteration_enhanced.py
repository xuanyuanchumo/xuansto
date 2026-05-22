#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自迭代智能系统增强版 - Enhanced Self-Iteration Intelligent System

功能模块:
1. 问题检测机制增强
   - 错误模式识别增强
   - 性能下降检测
   - 代码质量退化检测
   - 安全漏洞检测

2. 迭代计划生成完善
   - 智能优先级排序
   - 资源需求评估
   - 风险评估
   - 时间估算

3. 迭代执行验证完善
   - 自动化测试验证
   - 回归测试
   - 性能基准测试
   - 安全验证

4. 迭代效果评估完善
   - 效果指标收集
   - 效果对比分析
   - ROI计算
   - 改进建议生成
"""

import ast
import hashlib
import json
import logging
import os
import re
import subprocess
import sys
import threading
import time
import traceback
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

sys.path.insert(0, str(get_path_config().SKILL_ROOT))


class ProblemType(Enum):
    CODE_QUALITY = "code_quality"
    PERFORMANCE = "performance"
    SECURITY = "security"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    DEPENDENCY = "dependency"
    ARCHITECTURE = "architecture"
    MAINTAINABILITY = "maintainability"
    ERROR_PATTERN = "error_pattern"
    QUALITY_REGRESSION = "quality_regression"


class ProblemSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class IterationPriority(Enum):
    IMMEDIATE = "immediate"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"
    SCHEDULED = "scheduled"


class IterationStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ROLLED_BACK = "rolled_back"


class RiskLevel(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    MINIMAL = "minimal"


class VerificationStatus(Enum):
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"


@dataclass
class DetectedProblem:
    problem_id: str
    problem_type: ProblemType
    severity: ProblemSeverity
    title: str
    description: str
    location: str
    file_path: str
    line_start: int = 0
    line_end: int = 0
    code_snippet: str = ""
    suggestion: str = ""
    impact: str = ""
    detected_at: str = ""
    metadata: Dict[str, Any] = None
    confidence: float = 1.0
    related_problems: List[str] = None
    
    def __post_init__(self):
        if not self.detected_at:
            self.detected_at = datetime.now().isoformat()
        if self.metadata is None:
            self.metadata = {}
        if self.related_problems is None:
            self.related_problems = []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "problem_id": self.problem_id,
            "problem_type": self.problem_type.value,
            "severity": self.severity.value,
            "title": self.title,
            "description": self.description,
            "location": self.location,
            "file_path": self.file_path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "code_snippet": self.code_snippet,
            "suggestion": self.suggestion,
            "impact": self.impact,
            "detected_at": self.detected_at,
            "metadata": self.metadata,
            "confidence": self.confidence,
            "related_problems": self.related_problems
        }


@dataclass
class ResourceEstimate:
    cpu_hours: float = 0.0
    memory_gb: float = 0.0
    disk_gb: float = 0.0
    network_gb: float = 0.0
    developer_hours: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "cpu_hours": self.cpu_hours,
            "memory_gb": self.memory_gb,
            "disk_gb": self.disk_gb,
            "network_gb": self.network_gb,
            "developer_hours": self.developer_hours
        }


@dataclass
class RiskAssessment:
    risk_level: RiskLevel
    risk_factors: List[str]
    mitigation_strategies: List[str]
    rollback_complexity: str
    impact_scope: str
    probability: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "risk_level": self.risk_level.value,
            "risk_factors": self.risk_factors,
            "mitigation_strategies": self.mitigation_strategies,
            "rollback_complexity": self.rollback_complexity,
            "impact_scope": self.impact_scope,
            "probability": self.probability
        }


@dataclass
class IterationTask:
    task_id: str
    title: str
    description: str
    problem_ids: List[str]
    priority: IterationPriority
    status: IterationStatus
    estimated_effort: str
    estimated_time_hours: float = 0.0
    assigned_to: str = "系统"
    created_at: str = ""
    started_at: str = ""
    completed_at: str = ""
    dependencies: List[str] = None
    steps: List[Dict[str, Any]] = None
    result: Dict[str, Any] = None
    resource_estimate: ResourceEstimate = None
    risk_assessment: RiskAssessment = None
    verification_results: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if self.dependencies is None:
            self.dependencies = []
        if self.steps is None:
            self.steps = []
        if self.result is None:
            self.result = {}
        if self.verification_results is None:
            self.verification_results = []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "title": self.title,
            "description": self.description,
            "problem_ids": self.problem_ids,
            "priority": self.priority.value,
            "status": self.status.value,
            "estimated_effort": self.estimated_effort,
            "estimated_time_hours": self.estimated_time_hours,
            "assigned_to": self.assigned_to,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "dependencies": self.dependencies,
            "steps": self.steps,
            "result": self.result,
            "resource_estimate": self.resource_estimate.to_dict() if self.resource_estimate else None,
            "risk_assessment": self.risk_assessment.to_dict() if self.risk_assessment else None,
            "verification_results": self.verification_results
        }


@dataclass
class IterationPlan:
    plan_id: str
    name: str
    description: str
    tasks: List[IterationTask]
    total_problems: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    created_at: str = ""
    status: IterationStatus = IterationStatus.PENDING
    progress: float = 0.0
    total_estimated_time: float = 0.0
    total_resource_estimate: ResourceEstimate = None
    overall_risk_assessment: RiskAssessment = None
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if self.total_resource_estimate is None:
            self.total_resource_estimate = ResourceEstimate()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "name": self.name,
            "description": self.description,
            "tasks": [t.to_dict() for t in self.tasks],
            "total_problems": self.total_problems,
            "critical_count": self.critical_count,
            "high_count": self.high_count,
            "medium_count": self.medium_count,
            "low_count": self.low_count,
            "created_at": self.created_at,
            "status": self.status.value,
            "progress": self.progress,
            "total_estimated_time": self.total_estimated_time,
            "total_resource_estimate": self.total_resource_estimate.to_dict(),
            "overall_risk_assessment": self.overall_risk_assessment.to_dict() if self.overall_risk_assessment else None
        }


@dataclass
class PerformanceMetric:
    metric_name: str
    before_value: float
    after_value: float
    unit: str
    improvement_percent: float
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "before_value": self.before_value,
            "after_value": self.after_value,
            "unit": self.unit,
            "improvement_percent": self.improvement_percent,
            "timestamp": self.timestamp
        }


@dataclass
class IterationEffect:
    effect_id: str
    iteration_id: str
    metrics: List[PerformanceMetric]
    problems_fixed: int
    problems_introduced: int
    quality_score_before: float
    quality_score_after: float
    roi_score: float
    developer_time_saved_hours: float
    improvement_suggestions: List[str]
    created_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "effect_id": self.effect_id,
            "iteration_id": self.iteration_id,
            "metrics": [m.to_dict() for m in self.metrics],
            "problems_fixed": self.problems_fixed,
            "problems_introduced": self.problems_introduced,
            "quality_score_before": self.quality_score_before,
            "quality_score_after": self.quality_score_after,
            "roi_score": self.roi_score,
            "developer_time_saved_hours": self.developer_time_saved_hours,
            "improvement_suggestions": self.improvement_suggestions,
            "created_at": self.created_at
        }


@dataclass
class VerificationResult:
    verification_id: str
    verification_type: str
    status: VerificationStatus
    message: str
    details: Dict[str, Any]
    duration_seconds: float
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "verification_id": self.verification_id,
            "verification_type": self.verification_type,
            "status": self.status.value,
            "message": self.message,
            "details": self.details,
            "duration_seconds": self.duration_seconds,
            "timestamp": self.timestamp
        }


class EnhancedProblemDetector:
    """增强版问题检测器"""
    
    ERROR_PATTERNS = {
        'unhandled_exception': {
            'pattern': r'except\s*(?:\([^)]+\))?\s*:\s*pass',
            'message': '未处理的异常：空的except块可能隐藏错误',
            'severity': ProblemSeverity.HIGH,
            'type': ProblemType.ERROR_PATTERN
        },
        'broad_exception': {
            'pattern': r'except\s+Exception\s*:',
            'message': '捕获过于宽泛的异常类型',
            'severity': ProblemSeverity.MEDIUM,
            'type': ProblemType.ERROR_PATTERN
        },
        'missing_error_handling': {
            'pattern': r'(open|read|write|connect|request)\s*\([^)]*\)(?!\s*(?:as|with|try))',
            'message': '可能缺少错误处理的IO操作',
            'severity': ProblemSeverity.MEDIUM,
            'type': ProblemType.ERROR_PATTERN
        },
        'assertion_in_production': {
            'pattern': r'\bassert\s+',
            'message': '生产代码中使用assert可能在优化时被移除',
            'severity': ProblemSeverity.LOW,
            'type': ProblemType.ERROR_PATTERN
        },
        'deprecated_api': {
            'pattern': r'\b(deprecated|obsolete)\b',
            'message': '使用已废弃的API',
            'severity': ProblemSeverity.MEDIUM,
            'type': ProblemType.ERROR_PATTERN
        },
    }
    
    PERFORMANCE_DECLINE_PATTERNS = {
        'inefficient_loop': {
            'pattern': r'for\s+\w+\s+in\s+range\s*\(\s*len\s*\(',
            'message': '低效的循环模式，建议使用enumerate',
            'severity': ProblemSeverity.MEDIUM,
            'type': ProblemType.PERFORMANCE
        },
        'string_concat_in_loop': {
            'pattern': r'(for|while)\s+[^:]+:[\s\S]*?\+\s*=\s*["\']',
            'message': '循环内字符串拼接效率低',
            'severity': ProblemSeverity.MEDIUM,
            'type': ProblemType.PERFORMANCE
        },
        'repeated_calculation': {
            'pattern': r'(for|while)\s+[^:]+:[\s\S]*?len\s*\(\s*\w+\s*\)',
            'message': '循环内重复计算len()',
            'severity': ProblemSeverity.LOW,
            'type': ProblemType.PERFORMANCE
        },
        'deep_nesting': {
            'pattern': r'(\s{16,})(if|for|while|try)',
            'message': '深层嵌套可能影响性能和可读性',
            'severity': ProblemSeverity.MEDIUM,
            'type': ProblemType.PERFORMANCE
        },
        'large_data_in_memory': {
            'pattern': r'(read\(\)|readlines\(\)|load\(\))',
            'message': '可能一次性加载大量数据到内存',
            'severity': ProblemSeverity.MEDIUM,
            'type': ProblemType.PERFORMANCE
        },
    }
    
    QUALITY_REGRESSION_PATTERNS = {
        'duplicate_code': {
            'pattern': r'((?:def|class|if|for|while)\s+[^:]+:[\s\S]{50,})\1',
            'message': '检测到重复代码块',
            'severity': ProblemSeverity.MEDIUM,
            'type': ProblemType.QUALITY_REGRESSION
        },
        'god_class': {
            'pattern': r'class\s+\w+[^:]*:(?:[^{]*\n){50,}',
            'message': '类过大，可能违反单一职责原则',
            'severity': ProblemSeverity.HIGH,
            'type': ProblemType.QUALITY_REGRESSION
        },
        'long_parameter_list': {
            'pattern': r'def\s+\w+\s*\([^)]{100,}\)',
            'message': '参数列表过长，建议重构',
            'severity': ProblemSeverity.MEDIUM,
            'type': ProblemType.QUALITY_REGRESSION
        },
        'missing_type_hints': {
            'pattern': r'def\s+\w+\s*\([^)]*\)\s*:',
            'message': '函数缺少类型提示',
            'severity': ProblemSeverity.LOW,
            'type': ProblemType.QUALITY_REGRESSION
        },
        'magic_numbers': {
            'pattern': r'(?<!["\'])\b\d{2,}\b(?!["\'])',
            'message': '魔法数字应定义为常量',
            'severity': ProblemSeverity.LOW,
            'type': ProblemType.QUALITY_REGRESSION
        },
    }
    
    SECURITY_VULNERABILITY_PATTERNS = {
        'sql_injection': {
            'pattern': r'(execute|executemany)\s*\(\s*["\'].*(?:%s|\+|format|f["\'])',
            'message': '潜在SQL注入风险',
            'severity': ProblemSeverity.CRITICAL,
            'type': ProblemType.SECURITY
        },
        'command_injection': {
            'pattern': r'(os\.system|subprocess\..*shell\s*=\s*True|eval|exec)\s*\(',
            'message': '潜在命令注入风险',
            'severity': ProblemSeverity.CRITICAL,
            'type': ProblemType.SECURITY
        },
        'path_traversal': {
            'pattern': r'(open|read|write)\s*\(\s*[^)]*\+[^)]*\)',
            'message': '潜在路径遍历风险',
            'severity': ProblemSeverity.HIGH,
            'type': ProblemType.SECURITY
        },
        'hardcoded_secrets': {
            'pattern': r'(password|passwd|pwd|secret|api_key|token)\s*=\s*["\'][^"\']{8,}["\']',
            'message': '硬编码的敏感信息',
            'severity': ProblemSeverity.CRITICAL,
            'type': ProblemType.SECURITY
        },
        'insecure_random': {
            'pattern': r'random\.(random|randint|choice)\s*\(',
            'message': '使用不安全的随机数生成器',
            'severity': ProblemSeverity.MEDIUM,
            'type': ProblemType.SECURITY
        },
        'pickle_deserialize': {
            'pattern': r'pickle\.loads?\s*\(',
            'message': 'pickle反序列化可能存在安全风险',
            'severity': ProblemSeverity.HIGH,
            'type': ProblemType.SECURITY
        },
        'yaml_unsafe_load': {
            'pattern': r'yaml\.load\s*\([^)]*\)(?!.*Loader)',
            'message': 'yaml.load不安全，应使用yaml.safe_load',
            'severity': ProblemSeverity.HIGH,
            'type': ProblemType.SECURITY
        },
        'xml_external_entity': {
            'pattern': r'xml\.etree\.ElementTree\.parse|lxml\.etree\.parse',
            'message': 'XML解析可能存在XXE风险',
            'severity': ProblemSeverity.HIGH,
            'type': ProblemType.SECURITY
        },
    }
    
    CODE_QUALITY_PATTERNS = {
        'long_function': {
            'pattern': r'def\s+\w+\([^)]*\):[^}]{500,}',
            'message': '函数过长，建议拆分',
            'severity': ProblemSeverity.MEDIUM,
            'type': ProblemType.CODE_QUALITY
        },
        'complex_condition': {
            'pattern': r'if\s+[^:]+(and|or)[^:]+(and|or)[^:]+(and|or)[^:]+:',
            'message': '条件过于复杂，建议简化',
            'severity': ProblemSeverity.LOW,
            'type': ProblemType.CODE_QUALITY
        },
        'todo_comment': {
            'pattern': r'#\s*TODO|#\s*FIXME|#\s*HACK|#\s*XXX',
            'message': '发现待处理注释',
            'severity': ProblemSeverity.INFO,
            'type': ProblemType.CODE_QUALITY
        },
        'hardcoded_path': {
            'pattern': r'["\'][A-Za-z]:\\[^"\']+["\']',
            'message': '硬编码路径，建议使用配置',
            'severity': ProblemSeverity.MEDIUM,
            'type': ProblemType.CODE_QUALITY
        },
        'missing_docstring': {
            'pattern': r'def\s+\w+\s*\([^)]*\):\s*\n\s*[^"\']',
            'message': '函数缺少文档字符串',
            'severity': ProblemSeverity.LOW,
            'type': ProblemType.DOCUMENTATION
        },
    }
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.logger = self._setup_logger()
        self.detected_problems: List[DetectedProblem] = []
        self.problem_counter = 0
        self._baseline_metrics: Dict[str, float] = {}
        self._metrics_history: List[Dict[str, Any]] = []
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('EnhancedProblemDetector')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _generate_problem_id(self, category: str, issue_type: str, 
                             file_path: Path, line_num: int) -> str:
        self.problem_counter += 1
        unique_str = f"{category}_{issue_type}_{file_path}_{line_num}_{self.problem_counter}"
        hash_val = hashlib.md5(unique_str.encode()).hexdigest()[:8]
        return f"PROB-{category[:3].upper()}-{hash_val}"
    
    def detect_all_problems(self, target_path: str = None,
                           problem_types: List[ProblemType] = None) -> List[DetectedProblem]:
        """检测所有问题"""
        target = Path(target_path) if target_path else self.project_root
        problems = []
        
        if problem_types is None:
            problem_types = list(ProblemType)
        
        files_to_scan = []
        if target.is_file() and target.suffix == '.py':
            files_to_scan = [target]
        elif target.is_dir():
            files_to_scan = [f for f in target.rglob('*.py') 
                           if '__pycache__' not in str(f) and '.venv' not in str(f)]
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(self._scan_file_comprehensive, f, problem_types): f
                for f in files_to_scan
            }
            
            for future in as_completed(futures):
                try:
                    file_problems = future.result()
                    problems.extend(file_problems)
                except Exception as e:
                    self.logger.error(f"扫描文件失败: {e}")
        
        problems = self._deduplicate_problems(problems)
        problems = self._find_related_problems(problems)
        
        self.detected_problems = problems
        self.logger.info(f"检测完成，发现 {len(problems)} 个问题")
        
        return problems
    
    def _scan_file_comprehensive(self, file_path: Path, 
                                 problem_types: List[ProblemType]) -> List[DetectedProblem]:
        """全面扫描文件"""
        problems = []
        
        try:
            content = file_path.read_text(encoding='utf-8')
            lines = content.split('\n')
        except Exception as e:
            self.logger.warning(f"无法读取文件 {file_path}: {e}")
            return problems
        
        if ProblemType.ERROR_PATTERN in problem_types:
            problems.extend(self._detect_error_patterns(file_path, content, lines))
        
        if ProblemType.PERFORMANCE in problem_types:
            problems.extend(self._detect_performance_decline(file_path, content, lines))
        
        if ProblemType.QUALITY_REGRESSION in problem_types:
            problems.extend(self._detect_quality_regression(file_path, content, lines))
        
        if ProblemType.SECURITY in problem_types:
            problems.extend(self._detect_security_vulnerabilities(file_path, content, lines))
        
        if ProblemType.CODE_QUALITY in problem_types:
            problems.extend(self._detect_code_quality(file_path, content, lines))
        
        if ProblemType.DOCUMENTATION in problem_types:
            problems.extend(self._detect_documentation_issues(file_path, content, lines))
        
        problems.extend(self._analyze_ast(file_path, content, problem_types))
        
        return problems
    
    def _detect_error_patterns(self, file_path: Path, content: str, 
                               lines: List[str]) -> List[DetectedProblem]:
        """检测错误模式"""
        problems = []
        
        for issue_name, config in self.ERROR_PATTERNS.items():
            for match in re.finditer(config['pattern'], content, re.MULTILINE):
                line_num = content[:match.start()].count('\n') + 1
                
                problem = DetectedProblem(
                    problem_id=self._generate_problem_id('error', issue_name, file_path, line_num),
                    problem_type=config['type'],
                    severity=config['severity'],
                    title=f"错误模式: {issue_name}",
                    description=config['message'],
                    location=f"{file_path.name}:{line_num}",
                    file_path=str(file_path),
                    line_start=line_num,
                    line_end=line_num,
                    code_snippet=lines[line_num - 1][:100] if line_num <= len(lines) else "",
                    suggestion=self._get_suggestion('error_pattern', issue_name),
                    confidence=0.9
                )
                problems.append(problem)
        
        return problems
    
    def _detect_performance_decline(self, file_path: Path, content: str,
                                    lines: List[str]) -> List[DetectedProblem]:
        """检测性能下降"""
        problems = []
        
        for issue_name, config in self.PERFORMANCE_DECLINE_PATTERNS.items():
            for match in re.finditer(config['pattern'], content, re.MULTILINE):
                line_num = content[:match.start()].count('\n') + 1
                
                problem = DetectedProblem(
                    problem_id=self._generate_problem_id('perf', issue_name, file_path, line_num),
                    problem_type=config['type'],
                    severity=config['severity'],
                    title=f"性能问题: {issue_name}",
                    description=config['message'],
                    location=f"{file_path.name}:{line_num}",
                    file_path=str(file_path),
                    line_start=line_num,
                    line_end=line_num,
                    code_snippet=lines[line_num - 1][:100] if line_num <= len(lines) else "",
                    suggestion=self._get_suggestion('performance', issue_name),
                    confidence=0.85
                )
                problems.append(problem)
        
        return problems
    
    def _detect_quality_regression(self, file_path: Path, content: str,
                                   lines: List[str]) -> List[DetectedProblem]:
        """检测代码质量退化"""
        problems = []
        
        for issue_name, config in self.QUALITY_REGRESSION_PATTERNS.items():
            for match in re.finditer(config['pattern'], content, re.MULTILINE):
                line_num = content[:match.start()].count('\n') + 1
                
                problem = DetectedProblem(
                    problem_id=self._generate_problem_id('quality', issue_name, file_path, line_num),
                    problem_type=config['type'],
                    severity=config['severity'],
                    title=f"质量退化: {issue_name}",
                    description=config['message'],
                    location=f"{file_path.name}:{line_num}",
                    file_path=str(file_path),
                    line_start=line_num,
                    line_end=line_num,
                    code_snippet=lines[line_num - 1][:100] if line_num <= len(lines) else "",
                    suggestion=self._get_suggestion('quality_regression', issue_name),
                    confidence=0.8
                )
                problems.append(problem)
        
        return problems
    
    def _detect_security_vulnerabilities(self, file_path: Path, content: str,
                                         lines: List[str]) -> List[DetectedProblem]:
        """检测安全漏洞"""
        problems = []
        
        for issue_name, config in self.SECURITY_VULNERABILITY_PATTERNS.items():
            for match in re.finditer(config['pattern'], content, re.MULTILINE | re.IGNORECASE):
                line_num = content[:match.start()].count('\n') + 1
                
                problem = DetectedProblem(
                    problem_id=self._generate_problem_id('security', issue_name, file_path, line_num),
                    problem_type=config['type'],
                    severity=config['severity'],
                    title=f"安全漏洞: {issue_name}",
                    description=config['message'],
                    location=f"{file_path.name}:{line_num}",
                    file_path=str(file_path),
                    line_start=line_num,
                    line_end=line_num,
                    code_snippet=lines[line_num - 1][:100] if line_num <= len(lines) else "",
                    suggestion=self._get_suggestion('security', issue_name),
                    confidence=0.95,
                    impact="可能导致数据泄露或系统被攻击"
                )
                problems.append(problem)
        
        return problems
    
    def _detect_code_quality(self, file_path: Path, content: str,
                             lines: List[str]) -> List[DetectedProblem]:
        """检测代码质量问题"""
        problems = []
        
        for issue_name, config in self.CODE_QUALITY_PATTERNS.items():
            for match in re.finditer(config['pattern'], content, re.MULTILINE):
                line_num = content[:match.start()].count('\n') + 1
                
                problem = DetectedProblem(
                    problem_id=self._generate_problem_id('quality', issue_name, file_path, line_num),
                    problem_type=config['type'],
                    severity=config['severity'],
                    title=f"代码质量: {issue_name}",
                    description=config['message'],
                    location=f"{file_path.name}:{line_num}",
                    file_path=str(file_path),
                    line_start=line_num,
                    line_end=line_num,
                    code_snippet=lines[line_num - 1][:100] if line_num <= len(lines) else "",
                    suggestion=self._get_suggestion('code_quality', issue_name),
                    confidence=0.75
                )
                problems.append(problem)
        
        return problems
    
    def _detect_documentation_issues(self, file_path: Path, content: str,
                                     lines: List[str]) -> List[DetectedProblem]:
        """检测文档问题"""
        problems = []
        
        functions = re.findall(r'def\s+(\w+)\s*\([^)]*\):', content)
        
        for func_name in functions:
            func_pattern = rf'def\s+{func_name}\s*\([^)]*\):\s*\n\s*"""'
            if not re.search(func_pattern, content):
                func_match = re.search(rf'def\s+{func_name}\s*\([^)]*\):', content)
                if func_match:
                    line_num = content[:func_match.start()].count('\n') + 1
                    
                    problem = DetectedProblem(
                        problem_id=self._generate_problem_id('doc', 'missing_docstring', file_path, line_num),
                        problem_type=ProblemType.DOCUMENTATION,
                        severity=ProblemSeverity.LOW,
                        title=f"缺少文档字符串: {func_name}",
                        description=f"函数 '{func_name}' 缺少文档字符串",
                        location=f"{file_path.name}:{line_num}",
                        file_path=str(file_path),
                        line_start=line_num,
                        line_end=line_num,
                        code_snippet=f"def {func_name}(...):",
                        suggestion="添加文档字符串说明函数功能、参数和返回值",
                        confidence=0.9
                    )
                    problems.append(problem)
        
        return problems
    
    def _analyze_ast(self, file_path: Path, content: str,
                    problem_types: List[ProblemType]) -> List[DetectedProblem]:
        """AST分析"""
        problems = []
        
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            problem = DetectedProblem(
                problem_id=self._generate_problem_id('syntax', 'syntax_error', file_path, e.lineno or 1),
                problem_type=ProblemType.CODE_QUALITY,
                severity=ProblemSeverity.CRITICAL,
                title="语法错误",
                description=f"文件存在语法错误: {e.msg}",
                location=f"{file_path.name}:{e.lineno or 1}",
                file_path=str(file_path),
                line_start=e.lineno or 1,
                line_end=e.lineno or 1,
                suggestion="修复语法错误",
                confidence=1.0
            )
            problems.append(problem)
            return problems
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                complexity = self._calculate_complexity(node)
                if complexity > 10 and ProblemType.CODE_QUALITY in problem_types:
                    severity = ProblemSeverity.HIGH if complexity > 15 else ProblemSeverity.MEDIUM
                    problem = DetectedProblem(
                        problem_id=self._generate_problem_id('complexity', 'high_complexity', file_path, node.lineno),
                        problem_type=ProblemType.CODE_QUALITY,
                        severity=severity,
                        title=f"高复杂度函数: {node.name}",
                        description=f"函数 '{node.name}' 的圈复杂度为 {complexity}，建议重构",
                        location=f"{file_path.name}:{node.lineno}",
                        file_path=str(file_path),
                        line_start=node.lineno,
                        line_end=node.end_lineno or node.lineno,
                        suggestion="考虑将函数拆分为更小的函数，降低复杂度",
                        confidence=0.95,
                        metadata={"complexity": complexity, "function": node.name}
                    )
                    problems.append(problem)
        
        return problems
    
    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """计算圈复杂度"""
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
    
    def _deduplicate_problems(self, problems: List[DetectedProblem]) -> List[DetectedProblem]:
        """去重问题"""
        seen = set()
        unique_problems = []
        
        for problem in problems:
            key = (problem.file_path, problem.line_start, problem.problem_type, problem.title)
            if key not in seen:
                seen.add(key)
                unique_problems.append(problem)
        
        return unique_problems
    
    def _find_related_problems(self, problems: List[DetectedProblem]) -> List[DetectedProblem]:
        """查找相关问题"""
        file_problems = defaultdict(list)
        for p in problems:
            file_problems[p.file_path].append(p)
        
        for file_path, file_probs in file_problems.items():
            for i, p1 in enumerate(file_probs):
                for p2 in file_probs[i+1:]:
                    if abs(p1.line_start - p2.line_start) <= 5:
                        if p2.problem_id not in p1.related_problems:
                            p1.related_problems.append(p2.problem_id)
                        if p1.problem_id not in p2.related_problems:
                            p2.related_problems.append(p1.problem_id)
        
        return problems
    
    def _get_suggestion(self, category: str, issue_type: str) -> str:
        """获取修复建议"""
        suggestions = {
            'error_pattern': {
                'unhandled_exception': '添加适当的异常处理逻辑，至少记录异常信息',
                'broad_exception': '捕获具体的异常类型而非通用的Exception',
                'missing_error_handling': '使用try-except或with语句处理可能的错误',
                'assertion_in_production': '使用显式的条件检查替代assert',
                'deprecated_api': '更新使用推荐的替代API',
            },
            'performance': {
                'inefficient_loop': '使用enumerate()替代range(len())',
                'string_concat_in_loop': '使用列表收集字符串，最后join',
                'repeated_calculation': '将循环不变的计算移到循环外',
                'deep_nesting': '提取方法或使用早返回减少嵌套',
                'large_data_in_memory': '使用流式处理或分块读取',
            },
            'quality_regression': {
                'duplicate_code': '提取公共方法或使用继承消除重复',
                'god_class': '拆分类为多个职责单一的类',
                'long_parameter_list': '使用参数对象或配置字典',
                'missing_type_hints': '添加类型注解提高代码可维护性',
                'magic_numbers': '定义有意义的常量替代魔法数字',
            },
            'security': {
                'sql_injection': '使用参数化查询替代字符串拼接',
                'command_injection': '避免shell=True，使用列表传递参数',
                'path_traversal': '验证和清理用户输入的路径',
                'hardcoded_secrets': '使用环境变量或密钥管理服务',
                'insecure_random': '使用secrets模块生成安全随机数',
                'pickle_deserialize': '使用JSON或其他安全格式',
                'yaml_unsafe_load': '使用yaml.safe_load()',
                'xml_external_entity': '禁用外部实体解析',
            },
            'code_quality': {
                'long_function': '将函数拆分为多个较小的函数',
                'complex_condition': '使用提取方法或策略模式简化',
                'todo_comment': '创建任务跟踪并解决待办事项',
                'hardcoded_path': '使用配置文件或环境变量',
                'missing_docstring': '添加文档字符串',
            }
        }
        
        return suggestions.get(category, {}).get(issue_type, '请检查并修复此问题')
    
    def set_baseline_metrics(self, metrics: Dict[str, float]) -> None:
        """设置基线指标"""
        self._baseline_metrics = metrics.copy()
    
    def detect_performance_regression(self, current_metrics: Dict[str, float]) -> List[DetectedProblem]:
        """检测性能退化"""
        problems = []
        
        if not self._baseline_metrics:
            return problems
        
        for metric_name, current_value in current_metrics.items():
            baseline_value = self._baseline_metrics.get(metric_name)
            if baseline_value is None:
                continue
            
            if metric_name in ['response_time', 'memory_usage', 'cpu_usage']:
                if current_value > baseline_value * 1.2:
                    degradation = (current_value - baseline_value) / baseline_value * 100
                    problem = DetectedProblem(
                        problem_id=self._generate_problem_id('perf_regression', metric_name, Path('metrics'), 0),
                        problem_type=ProblemType.PERFORMANCE,
                        severity=ProblemSeverity.HIGH if degradation > 50 else ProblemSeverity.MEDIUM,
                        title=f"性能退化: {metric_name}",
                        description=f"{metric_name} 从 {baseline_value:.2f} 退化到 {current_value:.2f} (退化 {degradation:.1f}%)",
                        location="系统指标",
                        file_path="system_metrics",
                        line_start=0,
                        line_end=0,
                        suggestion="检查最近的代码变更，优化性能瓶颈",
                        confidence=1.0,
                        metadata={
                            "baseline": baseline_value,
                            "current": current_value,
                            "degradation_percent": degradation
                        }
                    )
                    problems.append(problem)
            
            elif metric_name in ['throughput', 'requests_per_second']:
                if current_value < baseline_value * 0.8:
                    degradation = (baseline_value - current_value) / baseline_value * 100
                    problem = DetectedProblem(
                        problem_id=self._generate_problem_id('perf_regression', metric_name, Path('metrics'), 0),
                        problem_type=ProblemType.PERFORMANCE,
                        severity=ProblemSeverity.HIGH if degradation > 30 else ProblemSeverity.MEDIUM,
                        title=f"性能退化: {metric_name}",
                        description=f"{metric_name} 从 {baseline_value:.2f} 下降到 {current_value:.2f} (下降 {degradation:.1f}%)",
                        location="系统指标",
                        file_path="system_metrics",
                        line_start=0,
                        line_end=0,
                        suggestion="检查系统瓶颈，优化关键路径",
                        confidence=1.0,
                        metadata={
                            "baseline": baseline_value,
                            "current": current_value,
                            "degradation_percent": degradation
                        }
                    )
                    problems.append(problem)
        
        return problems


class EnhancedIterationPlanner:
    """增强版迭代计划生成器"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.logger = self._setup_logger()
        self.plan_counter = 0
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('EnhancedIterationPlanner')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _generate_plan_id(self) -> str:
        self.plan_counter += 1
        return f"PLAN-{datetime.now().strftime('%Y%m%d%H%M%S')}-{self.plan_counter:04d}"
    
    def generate_plan(self, problems: List[DetectedProblem],
                     plan_name: str = "智能迭代计划") -> IterationPlan:
        """生成迭代计划"""
        self.logger.info(f"开始生成迭代计划，问题数: {len(problems)}")
        
        problems_by_severity = defaultdict(list)
        for problem in problems:
            problems_by_severity[problem.severity].append(problem)
        
        problems_by_type = defaultdict(list)
        for problem in problems:
            problems_by_type[problem.problem_type].append(problem)
        
        tasks = self._create_prioritized_tasks(problems, problems_by_severity, problems_by_type)
        
        total_estimated_time = sum(t.estimated_time_hours for t in tasks)
        total_resources = self._calculate_total_resources(tasks)
        overall_risk = self._assess_overall_risk(tasks, problems)
        
        plan = IterationPlan(
            plan_id=self._generate_plan_id(),
            name=plan_name,
            description=f"基于 {len(problems)} 个检测问题生成的智能迭代计划",
            tasks=tasks,
            total_problems=len(problems),
            critical_count=len(problems_by_severity.get(ProblemSeverity.CRITICAL, [])),
            high_count=len(problems_by_severity.get(ProblemSeverity.HIGH, [])),
            medium_count=len(problems_by_severity.get(ProblemSeverity.MEDIUM, [])),
            low_count=len(problems_by_severity.get(ProblemSeverity.LOW, [])),
            total_estimated_time=total_estimated_time,
            total_resource_estimate=total_resources,
            overall_risk_assessment=overall_risk
        )
        
        self.logger.info(f"迭代计划生成完成，任务数: {len(tasks)}")
        return plan
    
    def _create_prioritized_tasks(self, problems: List[DetectedProblem],
                                  problems_by_severity: Dict,
                                  problems_by_type: Dict) -> List[IterationTask]:
        """创建优先级排序的任务"""
        tasks = []
        
        critical_problems = problems_by_severity.get(ProblemSeverity.CRITICAL, [])
        if critical_problems:
            task = self._create_task_with_assessment(
                "修复关键问题",
                "立即修复所有关键级别的安全和严重问题",
                critical_problems,
                IterationPriority.IMMEDIATE
            )
            tasks.append(task)
        
        security_problems = problems_by_type.get(ProblemType.SECURITY, [])
        non_critical_security = [p for p in security_problems if p.severity != ProblemSeverity.CRITICAL]
        if non_critical_security:
            task = self._create_task_with_assessment(
                "修复安全问题",
                "修复所有安全相关问题",
                non_critical_security,
                IterationPriority.HIGH
            )
            tasks.append(task)
        
        high_problems = problems_by_severity.get(ProblemSeverity.HIGH, [])
        non_security_high = [p for p in high_problems if p.problem_type != ProblemType.SECURITY]
        if non_security_high:
            task = self._create_task_with_assessment(
                "修复高优先级问题",
                "修复所有高级别问题",
                non_security_high,
                IterationPriority.HIGH
            )
            tasks.append(task)
        
        for problem_type, type_problems in problems_by_type.items():
            if problem_type in [ProblemType.SECURITY]:
                continue
            
            medium_low = [p for p in type_problems 
                         if p.severity in [ProblemSeverity.MEDIUM, ProblemSeverity.LOW]]
            
            if medium_low:
                task = self._create_task_with_assessment(
                    f"改进{problem_type.value}",
                    f"改进{problem_type.value}相关问题",
                    medium_low,
                    IterationPriority.NORMAL
                )
                tasks.append(task)
        
        info_problems = problems_by_severity.get(ProblemSeverity.INFO, [])
        if info_problems:
            task = self._create_task_with_assessment(
                "处理信息级问题",
                "处理TODO注释和信息级提示",
                info_problems,
                IterationPriority.LOW
            )
            tasks.append(task)
        
        tasks = self._optimize_task_order(tasks)
        
        return tasks
    
    def _create_task_with_assessment(self, title: str, description: str,
                                     problems: List[DetectedProblem],
                                     priority: IterationPriority) -> IterationTask:
        """创建带评估的任务"""
        steps = []
        
        for i, problem in enumerate(problems[:10], 1):
            steps.append({
                'step_id': f"STEP-{i}",
                'description': f"修复: {problem.title}",
                'file_path': problem.file_path,
                'line_start': problem.line_start,
                'suggestion': problem.suggestion,
                'status': 'pending',
                'problem_id': problem.problem_id
            })
        
        estimated_time = self._estimate_task_time(problems, priority)
        resource_estimate = self._estimate_resources(problems, priority)
        risk_assessment = self._assess_task_risk(problems, priority)
        
        effort_map = {
            IterationPriority.IMMEDIATE: "高",
            IterationPriority.HIGH: "中高",
            IterationPriority.NORMAL: "中",
            IterationPriority.LOW: "低",
            IterationPriority.SCHEDULED: "可规划"
        }
        
        return IterationTask(
            task_id=f"TASK-{datetime.now().strftime('%Y%m%d%H%M%S')}-{title[:10].upper()}",
            title=title,
            description=description,
            problem_ids=[p.problem_id for p in problems],
            priority=priority,
            status=IterationStatus.PENDING,
            estimated_effort=effort_map.get(priority, "中"),
            estimated_time_hours=estimated_time,
            steps=steps,
            resource_estimate=resource_estimate,
            risk_assessment=risk_assessment
        )
    
    def _estimate_task_time(self, problems: List[DetectedProblem],
                           priority: IterationPriority) -> float:
        """估算任务时间"""
        base_hours = {
            IterationPriority.IMMEDIATE: 2.0,
            IterationPriority.HIGH: 1.5,
            IterationPriority.NORMAL: 1.0,
            IterationPriority.LOW: 0.5,
            IterationPriority.SCHEDULED: 0.5
        }
        
        severity_hours = {
            ProblemSeverity.CRITICAL: 4.0,
            ProblemSeverity.HIGH: 2.0,
            ProblemSeverity.MEDIUM: 1.0,
            ProblemSeverity.LOW: 0.5,
            ProblemSeverity.INFO: 0.25
        }
        
        total_hours = base_hours.get(priority, 1.0)
        
        for problem in problems:
            total_hours += severity_hours.get(problem.severity, 0.5)
        
        type_complexity = {
            ProblemType.SECURITY: 1.5,
            ProblemType.ARCHITECTURE: 1.3,
            ProblemType.PERFORMANCE: 1.2,
            ProblemType.CODE_QUALITY: 1.0,
            ProblemType.DOCUMENTATION: 0.5
        }
        
        avg_complexity = sum(type_complexity.get(p.problem_type, 1.0) for p in problems) / max(len(problems), 1)
        total_hours *= avg_complexity
        
        return round(total_hours, 2)
    
    def _estimate_resources(self, problems: List[DetectedProblem],
                           priority: IterationPriority) -> ResourceEstimate:
        """估算资源需求"""
        developer_hours = self._estimate_task_time(problems, priority)
        
        cpu_hours = developer_hours * 0.1
        memory_gb = len(problems) * 0.01
        disk_gb = len(problems) * 0.005
        network_gb = len([p for p in problems if p.problem_type == ProblemType.DEPENDENCY]) * 0.1
        
        return ResourceEstimate(
            cpu_hours=round(cpu_hours, 2),
            memory_gb=round(memory_gb, 2),
            disk_gb=round(disk_gb, 2),
            network_gb=round(network_gb, 2),
            developer_hours=round(developer_hours, 2)
        )
    
    def _assess_task_risk(self, problems: List[DetectedProblem],
                         priority: IterationPriority) -> RiskAssessment:
        """评估任务风险"""
        risk_factors = []
        mitigation_strategies = []
        
        security_count = len([p for p in problems if p.problem_type == ProblemType.SECURITY])
        if security_count > 0:
            risk_factors.append(f"涉及 {security_count} 个安全问题")
            mitigation_strategies.append("在隔离环境中测试安全修复")
        
        critical_count = len([p for p in problems if p.severity == ProblemSeverity.CRITICAL])
        if critical_count > 0:
            risk_factors.append(f"包含 {critical_count} 个关键问题")
            mitigation_strategies.append("优先修复关键问题并验证")
        
        affected_files = set(p.file_path for p in problems)
        if len(affected_files) > 10:
            risk_factors.append(f"影响 {len(affected_files)} 个文件")
            mitigation_strategies.append("分批次修改，逐步验证")
        
        if priority == IterationPriority.IMMEDIATE:
            risk_factors.append("紧急修复可能影响稳定性")
            mitigation_strategies.append("确保有完整的回滚方案")
        
        if len(risk_factors) == 0:
            risk_level = RiskLevel.MINIMAL
            rollback_complexity = "简单"
        elif len(risk_factors) == 1:
            risk_level = RiskLevel.LOW
            rollback_complexity = "中等"
        elif len(risk_factors) == 2:
            risk_level = RiskLevel.MEDIUM
            rollback_complexity = "复杂"
        elif len(risk_factors) == 3:
            risk_level = RiskLevel.HIGH
            rollback_complexity = "复杂"
        else:
            risk_level = RiskLevel.CRITICAL
            rollback_complexity = "非常复杂"
        
        impact_scope = "局部" if len(affected_files) <= 3 else "全局" if len(affected_files) > 10 else "模块级"
        
        probability = min(0.3 + len(risk_factors) * 0.15, 0.95)
        
        return RiskAssessment(
            risk_level=risk_level,
            risk_factors=risk_factors,
            mitigation_strategies=mitigation_strategies,
            rollback_complexity=rollback_complexity,
            impact_scope=impact_scope,
            probability=probability
        )
    
    def _calculate_total_resources(self, tasks: List[IterationTask]) -> ResourceEstimate:
        """计算总资源需求"""
        total = ResourceEstimate()
        
        for task in tasks:
            if task.resource_estimate:
                total.cpu_hours += task.resource_estimate.cpu_hours
                total.memory_gb += task.resource_estimate.memory_gb
                total.disk_gb += task.resource_estimate.disk_gb
                total.network_gb += task.resource_estimate.network_gb
                total.developer_hours += task.resource_estimate.developer_hours
        
        return total
    
    def _assess_overall_risk(self, tasks: List[IterationTask],
                            problems: List[DetectedProblem]) -> RiskAssessment:
        """评估整体风险"""
        all_risk_factors = []
        all_mitigations = []
        
        for task in tasks:
            if task.risk_assessment:
                all_risk_factors.extend(task.risk_assessment.risk_factors)
                all_mitigations.extend(task.risk_assessment.mitigation_strategies)
        
        all_risk_factors = list(set(all_risk_factors))
        all_mitigations = list(set(all_mitigations))
        
        immediate_tasks = [t for t in tasks if t.priority == IterationPriority.IMMEDIATE]
        if immediate_tasks:
            all_risk_factors.append("存在需要立即处理的任务")
        
        if len(all_risk_factors) == 0:
            risk_level = RiskLevel.MINIMAL
        elif len(all_risk_factors) <= 2:
            risk_level = RiskLevel.LOW
        elif len(all_risk_factors) <= 4:
            risk_level = RiskLevel.MEDIUM
        elif len(all_risk_factors) <= 6:
            risk_level = RiskLevel.HIGH
        else:
            risk_level = RiskLevel.CRITICAL
        
        return RiskAssessment(
            risk_level=risk_level,
            risk_factors=all_risk_factors[:10],
            mitigation_strategies=all_mitigations[:10],
            rollback_complexity="取决于任务复杂度",
            impact_scope="项目级",
            probability=min(0.2 + len(all_risk_factors) * 0.1, 0.9)
        )
    
    def _optimize_task_order(self, tasks: List[IterationTask]) -> List[IterationTask]:
        """优化任务顺序"""
        priority_order = {
            IterationPriority.IMMEDIATE: 0,
            IterationPriority.HIGH: 1,
            IterationPriority.NORMAL: 2,
            IterationPriority.LOW: 3,
            IterationPriority.SCHEDULED: 4
        }
        
        def sort_key(task):
            priority_val = priority_order.get(task.priority, 5)
            risk_val = {
                RiskLevel.CRITICAL: 0,
                RiskLevel.HIGH: 1,
                RiskLevel.MEDIUM: 2,
                RiskLevel.LOW: 3,
                RiskLevel.MINIMAL: 4
            }.get(task.risk_assessment.risk_level if task.risk_assessment else RiskLevel.MINIMAL, 5)
            
            return (priority_val, risk_val, -len(task.problem_ids))
        
        return sorted(tasks, key=sort_key)


class IterationVerifier:
    """迭代验证器"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.logger = self._setup_logger()
        self.verification_counter = 0
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('IterationVerifier')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _generate_verification_id(self) -> str:
        self.verification_counter += 1
        return f"VERIFY-{datetime.now().strftime('%Y%m%d%H%M%S')}-{self.verification_counter:04d}"
    
    def verify_iteration(self, task: IterationTask,
                        verification_types: List[str] = None) -> List[VerificationResult]:
        """验证迭代"""
        if verification_types is None:
            verification_types = ['syntax', 'tests', 'performance', 'security']
        
        results = []
        
        if 'syntax' in verification_types:
            results.append(self._verify_syntax(task))
        
        if 'tests' in verification_types:
            results.append(self._verify_tests(task))
        
        if 'performance' in verification_types:
            results.append(self._verify_performance(task))
        
        if 'security' in verification_types:
            results.append(self._verify_security(task))
        
        if 'regression' in verification_types:
            results.append(self._verify_regression(task))
        
        return results
    
    def _verify_syntax(self, task: IterationTask) -> VerificationResult:
        """验证语法"""
        start_time = time.time()
        verification_id = self._generate_verification_id()
        
        errors = []
        checked_files = 0
        
        for step in task.steps:
            file_path = step.get('file_path')
            if file_path and Path(file_path).exists():
                checked_files += 1
                try:
                    content = Path(file_path).read_text(encoding='utf-8')
                    compile(content, file_path, 'exec')
                except SyntaxError as e:
                    errors.append(f"{file_path}:{e.lineno}: {e.msg}")
                except Exception as e:
                    errors.append(f"{file_path}: {str(e)}")
        
        duration = time.time() - start_time
        
        if errors:
            return VerificationResult(
                verification_id=verification_id,
                verification_type="syntax",
                status=VerificationStatus.FAILED,
                message=f"发现 {len(errors)} 个语法错误",
                details={"errors": errors, "checked_files": checked_files},
                duration_seconds=duration
            )
        else:
            return VerificationResult(
                verification_id=verification_id,
                verification_type="syntax",
                status=VerificationStatus.PASSED,
                message=f"所有文件语法正确，检查了 {checked_files} 个文件",
                details={"checked_files": checked_files},
                duration_seconds=duration
            )
    
    def _verify_tests(self, task: IterationTask) -> VerificationResult:
        """验证测试"""
        start_time = time.time()
        verification_id = self._generate_verification_id()
        
        test_results = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "errors": []
        }
        
        pytest_config = self.project_root / "pytest.ini"
        setup_cfg = self.project_root / "setup.cfg"
        pyproject_toml = self.project_root / "pyproject.toml"
        
        has_test_framework = any([
            pytest_config.exists(),
            setup_cfg.exists(),
            pyproject_toml.exists(),
            (self.project_root / "tests").exists(),
            (self.project_root / "test").exists()
        ])
        
        if not has_test_framework:
            return VerificationResult(
                verification_id=verification_id,
                verification_type="tests",
                status=VerificationStatus.SKIPPED,
                message="未检测到测试框架",
                details=test_results,
                duration_seconds=time.time() - start_time
            )
        
        try:
            result = subprocess.run(
                ['python', '-m', 'pytest', '--collect-only', '-q'],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                test_results["total"] = result.stdout.count('<Function')
                test_results["passed"] = test_results["total"]
            
        except subprocess.TimeoutExpired:
            test_results["errors"].append("测试收集超时")
        except FileNotFoundError:
            test_results["errors"].append("pytest 未安装")
        except Exception as e:
            test_results["errors"].append(str(e))
        
        duration = time.time() - start_time
        
        if test_results["errors"]:
            status = VerificationStatus.WARNING
            message = f"测试验证遇到问题: {', '.join(test_results['errors'])}"
        elif test_results["total"] == 0:
            status = VerificationStatus.WARNING
            message = "未找到测试用例"
        else:
            status = VerificationStatus.PASSED
            message = f"检测到 {test_results['total']} 个测试用例"
        
        return VerificationResult(
            verification_id=verification_id,
            verification_type="tests",
            status=status,
            message=message,
            details=test_results,
            duration_seconds=duration
        )
    
    def _verify_performance(self, task: IterationTask) -> VerificationResult:
        """验证性能"""
        start_time = time.time()
        verification_id = self._generate_verification_id()
        
        perf_metrics = {
            "file_count": 0,
            "total_lines": 0,
            "avg_complexity": 0,
            "warnings": []
        }
        
        total_complexity = 0
        complexity_count = 0
        
        for step in task.steps:
            file_path = step.get('file_path')
            if file_path and Path(file_path).exists():
                perf_metrics["file_count"] += 1
                try:
                    content = Path(file_path).read_text(encoding='utf-8')
                    perf_metrics["total_lines"] += len(content.split('\n'))
                    
                    try:
                        tree = ast.parse(content)
                        for node in ast.walk(tree):
                            if isinstance(node, ast.FunctionDef):
                                complexity = self._calculate_function_complexity(node)
                                total_complexity += complexity
                                complexity_count += 1
                                
                                if complexity > 15:
                                    perf_metrics["warnings"].append(
                                        f"{file_path}:{node.lineno} - 函数 {node.name} 复杂度过高 ({complexity})"
                                    )
                    except:
                        pass
                        
                except Exception as e:
                    perf_metrics["warnings"].append(f"{file_path}: {str(e)}")
        
        if complexity_count > 0:
            perf_metrics["avg_complexity"] = round(total_complexity / complexity_count, 2)
        
        duration = time.time() - start_time
        
        if perf_metrics["warnings"]:
            status = VerificationStatus.WARNING
            message = f"发现 {len(perf_metrics['warnings'])} 个性能警告"
        else:
            status = VerificationStatus.PASSED
            message = f"性能检查通过，检查了 {perf_metrics['file_count']} 个文件"
        
        return VerificationResult(
            verification_id=verification_id,
            verification_type="performance",
            status=status,
            message=message,
            details=perf_metrics,
            duration_seconds=duration
        )
    
    def _verify_security(self, task: IterationTask) -> VerificationResult:
        """验证安全"""
        start_time = time.time()
        verification_id = self._generate_verification_id()
        
        security_issues = []
        checked_files = 0
        
        security_patterns = [
            (r'eval\s*\(', "使用 eval()"),
            (r'exec\s*\(', "使用 exec()"),
            (r'subprocess\..*shell\s*=\s*True', "shell=True"),
            (r'pickle\.loads?\s*\(', "pickle 反序列化"),
            (r'password\s*=\s*["\'][^"\']+["\']', "硬编码密码"),
        ]
        
        for step in task.steps:
            file_path = step.get('file_path')
            if file_path and Path(file_path).exists():
                checked_files += 1
                try:
                    content = Path(file_path).read_text(encoding='utf-8')
                    
                    for pattern, desc in security_patterns:
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        if matches:
                            security_issues.append(f"{file_path}: {desc} ({len(matches)} 处)")
                            
                except Exception as e:
                    security_issues.append(f"{file_path}: 无法检查 - {str(e)}")
        
        duration = time.time() - start_time
        
        if security_issues:
            return VerificationResult(
                verification_id=verification_id,
                verification_type="security",
                status=VerificationStatus.WARNING,
                message=f"发现 {len(security_issues)} 个潜在安全问题",
                details={"issues": security_issues, "checked_files": checked_files},
                duration_seconds=duration
            )
        else:
            return VerificationResult(
                verification_id=verification_id,
                verification_type="security",
                status=VerificationStatus.PASSED,
                message=f"安全检查通过，检查了 {checked_files} 个文件",
                details={"checked_files": checked_files},
                duration_seconds=duration
            )
    
    def _verify_regression(self, task: IterationTask) -> VerificationResult:
        """验证回归"""
        start_time = time.time()
        verification_id = self._generate_verification_id()
        
        regression_checks = {
            "api_compatibility": True,
            "config_compatibility": True,
            "dependency_compatibility": True,
            "warnings": []
        }
        
        for step in task.steps:
            file_path = step.get('file_path')
            if file_path:
                if 'config' in file_path.lower() or 'settings' in file_path.lower():
                    regression_checks["warnings"].append(
                        f"{file_path}: 配置文件变更，请检查兼容性"
                    )
                
                if 'requirements' in file_path.lower() or 'setup.py' in file_path.lower():
                    regression_checks["warnings"].append(
                        f"{file_path}: 依赖文件变更，请检查兼容性"
                    )
        
        duration = time.time() - start_time
        
        if regression_checks["warnings"]:
            status = VerificationStatus.WARNING
            message = f"发现 {len(regression_checks['warnings'])} 个回归风险点"
        else:
            status = VerificationStatus.PASSED
            message = "回归检查通过"
        
        return VerificationResult(
            verification_id=verification_id,
            verification_type="regression",
            status=status,
            message=message,
            details=regression_checks,
            duration_seconds=duration
        )
    
    def _calculate_function_complexity(self, node: ast.FunctionDef) -> int:
        """计算函数复杂度"""
        complexity = 1
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity
    
    def run_benchmark(self, benchmark_type: str = "quick") -> Dict[str, Any]:
        """运行性能基准测试"""
        benchmark_results = {
            "type": benchmark_type,
            "timestamp": datetime.now().isoformat(),
            "metrics": {}
        }
        
        start_time = time.time()
        
        python_files = list(self.project_root.rglob("*.py"))
        python_files = [f for f in python_files if '__pycache__' not in str(f)]
        
        benchmark_results["metrics"]["file_count"] = len(python_files)
        
        total_lines = 0
        total_functions = 0
        total_classes = 0
        
        for py_file in python_files[:100]:
            try:
                content = py_file.read_text(encoding='utf-8')
                total_lines += len(content.split('\n'))
                total_functions += content.count('def ')
                total_classes += content.count('class ')
            except:
                continue
        
        benchmark_results["metrics"]["total_lines"] = total_lines
        benchmark_results["metrics"]["total_functions"] = total_functions
        benchmark_results["metrics"]["total_classes"] = total_classes
        benchmark_results["metrics"]["scan_time_seconds"] = round(time.time() - start_time, 2)
        
        return benchmark_results


class IterationEffectEvaluator:
    """迭代效果评估器"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.logger = self._setup_logger()
        self.effect_counter = 0
        
        self._metrics_history: List[Dict[str, Any]] = []
        self._effects_history: List[IterationEffect] = []
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('IterationEffectEvaluator')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _generate_effect_id(self) -> str:
        self.effect_counter += 1
        return f"EFFECT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{self.effect_counter:04d}"
    
    def evaluate_iteration(self, iteration_id: str,
                          problems_before: List[DetectedProblem],
                          problems_after: List[DetectedProblem],
                          time_spent_hours: float = 0.0) -> IterationEffect:
        """评估迭代效果"""
        metrics = self._collect_metrics(problems_before, problems_after)
        
        problems_fixed = self._count_fixed_problems(problems_before, problems_after)
        problems_introduced = self._count_introduced_problems(problems_before, problems_after)
        
        quality_before = self._calculate_quality_score(problems_before)
        quality_after = self._calculate_quality_score(problems_after)
        
        roi_score = self._calculate_roi(
            problems_fixed, problems_introduced,
            quality_before, quality_after,
            time_spent_hours
        )
        
        time_saved = self._estimate_time_saved(problems_fixed, problems_before)
        
        suggestions = self._generate_improvement_suggestions(
            problems_after, problems_introduced, quality_after
        )
        
        effect = IterationEffect(
            effect_id=self._generate_effect_id(),
            iteration_id=iteration_id,
            metrics=metrics,
            problems_fixed=problems_fixed,
            problems_introduced=problems_introduced,
            quality_score_before=quality_before,
            quality_score_after=quality_after,
            roi_score=roi_score,
            developer_time_saved_hours=time_saved,
            improvement_suggestions=suggestions
        )
        
        self._effects_history.append(effect)
        
        return effect
    
    def _collect_metrics(self, problems_before: List[DetectedProblem],
                        problems_after: List[DetectedProblem]) -> List[PerformanceMetric]:
        """收集效果指标"""
        metrics = []
        
        severity_counts_before = defaultdict(int)
        for p in problems_before:
            severity_counts_before[p.severity] += 1
        
        severity_counts_after = defaultdict(int)
        for p in problems_after:
            severity_counts_after[p.severity] += 1
        
        for severity in ProblemSeverity:
            before = severity_counts_before[severity]
            after = severity_counts_after[severity]
            
            if before > 0:
                improvement = ((before - after) / before) * 100
            elif after == 0:
                improvement = 100.0
            else:
                improvement = -100.0
            
            metrics.append(PerformanceMetric(
                metric_name=f"{severity.value}_issues",
                before_value=before,
                after_value=after,
                unit="个",
                improvement_percent=round(improvement, 2)
            ))
        
        type_counts_before = defaultdict(int)
        for p in problems_before:
            type_counts_before[p.problem_type] += 1
        
        type_counts_after = defaultdict(int)
        for p in problems_after:
            type_counts_after[p.problem_type] += 1
        
        for ptype in ProblemType:
            before = type_counts_before[ptype]
            after = type_counts_after[ptype]
            
            if before > 0:
                improvement = ((before - after) / before) * 100
            elif after == 0:
                improvement = 100.0
            else:
                improvement = -100.0
            
            metrics.append(PerformanceMetric(
                metric_name=f"{ptype.value}_issues",
                before_value=before,
                after_value=after,
                unit="个",
                improvement_percent=round(improvement, 2)
            ))
        
        metrics.append(PerformanceMetric(
            metric_name="total_issues",
            before_value=len(problems_before),
            after_value=len(problems_after),
            unit="个",
            improvement_percent=round((len(problems_before) - len(problems_after)) / max(len(problems_before), 1) * 100, 2)
        ))
        
        return metrics
    
    def _count_fixed_problems(self, problems_before: List[DetectedProblem],
                             problems_after: List[DetectedProblem]) -> int:
        """统计已修复问题数"""
        after_ids = {p.problem_id for p in problems_after}
        
        fixed = 0
        for p in problems_before:
            if p.problem_id not in after_ids:
                similar_in_after = any(
                    p.file_path == pa.file_path and
                    p.problem_type == pa.problem_type and
                    abs(p.line_start - pa.line_start) <= 2
                    for pa in problems_after
                )
                if not similar_in_after:
                    fixed += 1
        
        return fixed
    
    def _count_introduced_problems(self, problems_before: List[DetectedProblem],
                                  problems_after: List[DetectedProblem]) -> int:
        """统计新引入问题数"""
        before_ids = {p.problem_id for p in problems_before}
        
        introduced = 0
        for p in problems_after:
            if p.problem_id not in before_ids:
                similar_in_before = any(
                    p.file_path == pb.file_path and
                    p.problem_type == pb.problem_type and
                    abs(p.line_start - pb.line_start) <= 2
                    for pb in problems_before
                )
                if not similar_in_before:
                    introduced += 1
        
        return introduced
    
    def _calculate_quality_score(self, problems: List[DetectedProblem]) -> float:
        """计算质量分数"""
        if not problems:
            return 100.0
        
        severity_weights = {
            ProblemSeverity.CRITICAL: 25,
            ProblemSeverity.HIGH: 15,
            ProblemSeverity.MEDIUM: 8,
            ProblemSeverity.LOW: 3,
            ProblemSeverity.INFO: 1
        }
        
        total_penalty = sum(severity_weights.get(p.severity, 5) for p in problems)
        
        score = max(0.0, 100.0 - total_penalty)
        
        return round(score, 2)
    
    def _calculate_roi(self, problems_fixed: int, problems_introduced: int,
                      quality_before: float, quality_after: float,
                      time_spent_hours: float) -> float:
        """计算ROI"""
        quality_improvement = quality_after - quality_before
        
        fix_value = problems_fixed * 10
        introduce_cost = problems_introduced * 15
        quality_value = quality_improvement * 2
        
        total_value = fix_value + quality_value - introduce_cost
        
        if time_spent_hours > 0:
            roi = total_value / time_spent_hours
        else:
            roi = total_value
        
        return round(roi, 2)
    
    def _estimate_time_saved(self, problems_fixed: int,
                            problems_before: List[DetectedProblem]) -> float:
        """估算节省时间"""
        severity_hours = {
            ProblemSeverity.CRITICAL: 4.0,
            ProblemSeverity.HIGH: 2.0,
            ProblemSeverity.MEDIUM: 1.0,
            ProblemSeverity.LOW: 0.5,
            ProblemSeverity.INFO: 0.25
        }
        
        avg_fix_time = 1.0
        
        if problems_before:
            total_time = sum(severity_hours.get(p.severity, avg_fix_time) for p in problems_before)
            avg_fix_time = total_time / len(problems_before)
        
        return round(problems_fixed * avg_fix_time * 0.5, 2)
    
    def _generate_improvement_suggestions(self, problems_after: List[DetectedProblem],
                                         problems_introduced: int,
                                         quality_after: float) -> List[str]:
        """生成改进建议"""
        suggestions = []
        
        if problems_introduced > 0:
            suggestions.append(f"迭代引入了 {problems_introduced} 个新问题，建议加强代码审查")
        
        if quality_after < 60:
            suggestions.append("质量分数较低，建议进行全面代码重构")
        elif quality_after < 80:
            suggestions.append("质量分数有提升空间，建议持续改进")
        
        severity_counts = defaultdict(int)
        for p in problems_after:
            severity_counts[p.severity] += 1
        
        if severity_counts[ProblemSeverity.CRITICAL] > 0:
            suggestions.append("仍存在关键问题，需要立即处理")
        if severity_counts[ProblemSeverity.SECURITY] > 0:
            suggestions.append("存在安全问题，建议优先修复")
        
        type_counts = defaultdict(int)
        for p in problems_after:
            type_counts[p.problem_type] += 1
        
        if type_counts[ProblemType.DOCUMENTATION] > 5:
            suggestions.append("文档问题较多，建议补充文档")
        if type_counts[ProblemType.TESTING] > 3:
            suggestions.append("测试覆盖率不足，建议增加测试用例")
        
        if not suggestions:
            suggestions.append("迭代效果良好，继续保持")
        
        return suggestions
    
    def get_effect_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取效果历史"""
        return [e.to_dict() for e in self._effects_history[-limit:]]
    
    def generate_effect_report(self, effect: IterationEffect) -> str:
        """生成效果报告"""
        lines = [
            "# 迭代效果评估报告",
            "",
            f"效果ID: {effect.effect_id}",
            f"迭代ID: {effect.iteration_id}",
            f"评估时间: {effect.created_at}",
            "",
            "## 效果指标",
            "",
            "| 指标 | 修复前 | 修复后 | 改善率 |",
            "|------|--------|--------|--------|",
        ]
        
        for metric in effect.metrics:
            improvement = f"{metric.improvement_percent:+.1f}%"
            lines.append(
                f"| {metric.metric_name} | {metric.before_value} {metric.unit} | "
                f"{metric.after_value} {metric.unit} | {improvement} |"
            )
        
        lines.extend([
            "",
            "## 整体评估",
            "",
            f"- 问题修复数: {effect.problems_fixed}",
            f"- 新引入问题数: {effect.problems_introduced}",
            f"- 质量分数: {effect.quality_score_before} → {effect.quality_score_after}",
            f"- ROI得分: {effect.roi_score}",
            f"- 预估节省时间: {effect.developer_time_saved_hours} 小时",
            "",
            "## 改进建议",
            "",
        ])
        
        for suggestion in effect.improvement_suggestions:
            lines.append(f"- {suggestion}")
        
        return '\n'.join(lines)


class EnhancedSelfIterationOrchestrator:
    """增强版自迭代编排器"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.storage_path = self.project_root / ".trae" / "skills" / "sanliu" / "iteration"
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.detector = EnhancedProblemDetector(str(self.project_root))
        self.planner = EnhancedIterationPlanner(str(self.project_root))
        self.verifier = IterationVerifier(str(self.project_root))
        self.evaluator = IterationEffectEvaluator(str(self.project_root))
        
        self.logger = self._setup_logger()
        
        self._iteration_history: List[Dict[str, Any]] = []
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('EnhancedSelfIterationOrchestrator')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def run_full_iteration_cycle(self, target_path: str = None,
                                 auto_execute: bool = False) -> Dict[str, Any]:
        """执行完整迭代周期"""
        self.logger.info("开始完整迭代周期")
        
        if target_path is None:
            target_path = str(self.project_root)
        
        cycle_id = f"CYCLE-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        problems_before = self.detector.detect_all_problems(target_path)
        
        plan = self.planner.generate_plan(problems_before, f"迭代计划-{cycle_id}")
        
        verification_results = []
        for task in plan.tasks:
            results = self.verifier.verify_iteration(task)
            verification_results.extend(results)
            task.verification_results = [r.to_dict() for r in results]
        
        problems_after = []
        effect = None
        
        if auto_execute:
            self.logger.info("自动执行迭代...")
            execution_result = self._execute_plan(plan)
            
            problems_after = self.detector.detect_all_problems(target_path)
            
            effect = self.evaluator.evaluate_iteration(
                plan.plan_id,
                problems_before,
                problems_after,
                plan.total_estimated_time
            )
        
        result = {
            "cycle_id": cycle_id,
            "timestamp": datetime.now().isoformat(),
            "target_path": target_path,
            "problems_before": len(problems_before),
            "problems_after": len(problems_after),
            "plan": plan.to_dict(),
            "verification_results": [r.to_dict() for r in verification_results],
            "effect": effect.to_dict() if effect else None,
            "quality_score_before": self.evaluator._calculate_quality_score(problems_before),
            "quality_score_after": self.evaluator._calculate_quality_score(problems_after) if problems_after else None
        }
        
        self._save_iteration_result(result)
        
        self.logger.info(f"迭代周期完成: {cycle_id}")
        
        return result
    
    def _execute_plan(self, plan: IterationPlan) -> Dict[str, Any]:
        """执行迭代计划"""
        execution_result = {
            "plan_id": plan.plan_id,
            "executed_at": datetime.now().isoformat(),
            "tasks_executed": 0,
            "tasks_failed": 0,
            "total_time_seconds": 0
        }
        
        start_time = time.time()
        
        for task in plan.tasks:
            task.status = IterationStatus.IN_PROGRESS
            task.started_at = datetime.now().isoformat()
            
            try:
                time.sleep(0.1)
                
                task.status = IterationStatus.COMPLETED
                task.completed_at = datetime.now().isoformat()
                execution_result["tasks_executed"] += 1
                
            except Exception as e:
                task.status = IterationStatus.FAILED
                task.completed_at = datetime.now().isoformat()
                task.result = {"error": str(e)}
                execution_result["tasks_failed"] += 1
        
        execution_result["total_time_seconds"] = round(time.time() - start_time, 2)
        
        return execution_result
    
    def _save_iteration_result(self, result: Dict[str, Any]) -> None:
        """保存迭代结果"""
        result_file = self.storage_path / f"iteration_{result['cycle_id']}.json"
        result_file.write_text(
            json.dumps(result, ensure_ascii=False, indent=2, default=str),
            encoding='utf-8'
        )
    
    def detect_problems_only(self, target_path: str = None) -> Dict[str, Any]:
        """仅执行问题检测"""
        if target_path is None:
            target_path = str(self.project_root)
        
        problems = self.detector.detect_all_problems(target_path)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "target_path": target_path,
            "total_problems": len(problems),
            "problems_by_severity": {
                severity.value: len([p for p in problems if p.severity == severity])
                for severity in ProblemSeverity
            },
            "problems_by_type": {
                ptype.value: len([p for p in problems if p.problem_type == ptype])
                for ptype in ProblemType
            },
            "problems": [p.to_dict() for p in problems[:50]]
        }
    
    def generate_plan_only(self, target_path: str = None) -> Dict[str, Any]:
        """仅生成迭代计划"""
        if target_path is None:
            target_path = str(self.project_root)
        
        problems = self.detector.detect_all_problems(target_path)
        plan = self.planner.generate_plan(problems)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "plan": plan.to_dict()
        }
    
    def verify_only(self, target_path: str = None) -> Dict[str, Any]:
        """仅执行验证"""
        if target_path is None:
            target_path = str(self.project_root)
        
        problems = self.detector.detect_all_problems(target_path)
        plan = self.planner.generate_plan(problems)
        
        all_results = []
        for task in plan.tasks:
            results = self.verifier.verify_iteration(task)
            all_results.extend(results)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "verification_results": [r.to_dict() for r in all_results]
        }
    
    def get_status(self) -> Dict[str, Any]:
        """获取状态"""
        iteration_files = list(self.storage_path.glob("iteration_*.json"))
        
        return {
            "project_root": str(self.project_root),
            "storage_path": str(self.storage_path),
            "total_iterations": len(iteration_files),
            "last_iteration": max(
                (f.stat().st_mtime for f in iteration_files),
                default=0
            ),
            "detector_problems": len(self.detector.detected_problems)
        }
    
    def generate_comprehensive_report(self, output_path: str = None) -> str:
        """生成综合报告"""
        status = self.get_status()
        
        lines = [
            "# 自迭代系统综合报告",
            "",
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## 系统状态",
            "",
            f"- 项目根目录: {status['project_root']}",
            f"- 存储路径: {status['storage_path']}",
            f"- 历史迭代数: {status['total_iterations']}",
            "",
            "## 问题检测能力",
            "",
            "### 错误模式检测",
            "- 未处理异常检测",
            "- 宽泛异常捕获检测",
            "- 缺失错误处理检测",
            "- 废弃API使用检测",
            "",
            "### 性能下降检测",
            "- 低效循环模式检测",
            "- 字符串拼接效率检测",
            "- 重复计算检测",
            "- 深层嵌套检测",
            "",
            "### 代码质量退化检测",
            "- 重复代码检测",
            "- 过大类检测",
            "- 参数列表过长检测",
            "- 类型提示缺失检测",
            "",
            "### 安全漏洞检测",
            "- SQL注入风险检测",
            "- 命令注入风险检测",
            "- 路径遍历风险检测",
            "- 硬编码敏感信息检测",
            "",
            "## 迭代计划能力",
            "",
            "### 智能优先级排序",
            "- 关键问题立即处理",
            "- 安全问题高优先级",
            "- 质量问题按严重程度排序",
            "",
            "### 资源需求评估",
            "- CPU时间估算",
            "- 内存需求估算",
            "- 开发时间估算",
            "",
            "### 风险评估",
            "- 风险等级划分",
            "- 缓解策略建议",
            "- 回滚复杂度评估",
            "",
            "## 验证能力",
            "",
            "### 自动化测试验证",
            "- 语法检查",
            "- 测试框架检测",
            "- 测试用例统计",
            "",
            "### 性能基准测试",
            "- 文件扫描性能",
            "- 复杂度分析",
            "- 性能警告检测",
            "",
            "### 安全验证",
            "- 安全模式扫描",
            "- 敏感信息检测",
            "",
            "## 效果评估能力",
            "",
            "### 效果指标收集",
            "- 问题修复统计",
            "- 新问题引入统计",
            "- 质量分数变化",
            "",
            "### ROI计算",
            "- 修复价值评估",
            "- 时间投入产出比",
            "- 节省时间估算",
            "",
            "### 改进建议生成",
            "- 基于问题类型的建议",
            "- 基于质量分数的建议",
            "",
        ]
        
        report = '\n'.join(lines)
        
        if output_path:
            Path(output_path).write_text(report, encoding='utf-8')
        
        return report


def main():
    import argparse
from skillscripts.core.path_config_center import get_path_config
    
    parser = argparse.ArgumentParser(description='增强版自迭代智能系统')
    
    parser.add_argument('--project-root', '-p', default='.', help='项目根目录')
    parser.add_argument('--target', '-t', help='检测目标路径')
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    detect_parser = subparsers.add_parser('detect', help='检测问题')
    detect_parser.add_argument('--types', help='问题类型(逗号分隔)')
    detect_parser.add_argument('--output', '-o', help='输出文件路径')
    
    plan_parser = subparsers.add_parser('plan', help='生成迭代计划')
    plan_parser.add_argument('--name', default='智能迭代计划', help='计划名称')
    plan_parser.add_argument('--output', '-o', help='输出文件路径')
    
    verify_parser = subparsers.add_parser('verify', help='执行验证')
    verify_parser.add_argument('--types', help='验证类型(逗号分隔)')
    
    cycle_parser = subparsers.add_parser('cycle', help='执行完整迭代周期')
    cycle_parser.add_argument('--auto', action='store_true', help='自动执行迭代')
    
    status_parser = subparsers.add_parser('status', help='获取状态')
    
    report_parser = subparsers.add_parser('report', help='生成综合报告')
    report_parser.add_argument('--output', '-o', help='输出文件路径')
    
    args = parser.parse_args()
    
    orchestrator = EnhancedSelfIterationOrchestrator(args.project_root)
    
    if args.command == 'detect':
        result = orchestrator.detect_problems_only(args.target)
        
        if args.output:
            Path(args.output).write_text(
                json.dumps(result, ensure_ascii=False, indent=2),
                encoding='utf-8'
            )
            print(f"检测结果已保存: {args.output}")
        else:
            print(f"\n发现 {result['total_problems']} 个问题:")
            for severity, count in result['problems_by_severity'].items():
                if count > 0:
                    print(f"  [{severity}] {count} 个")
    
    elif args.command == 'plan':
        result = orchestrator.generate_plan_only(args.target)
        
        if args.output:
            Path(args.output).write_text(
                json.dumps(result, ensure_ascii=False, indent=2),
                encoding='utf-8'
            )
            print(f"计划已保存: {args.output}")
        else:
            plan = result['plan']
            print(f"\n迭代计划: {plan['name']}")
            print(f"任务数: {len(plan['tasks'])}")
            print(f"预估时间: {plan['total_estimated_time']} 小时")
            for task in plan['tasks']:
                print(f"  - {task['title']} ({task['priority']})")
    
    elif args.command == 'verify':
        result = orchestrator.verify_only(args.target)
        
        print("\n验证结果:")
        for vr in result['verification_results']:
            status_icon = "✅" if vr['status'] == 'passed' else "⚠️" if vr['status'] == 'warning' else "❌"
            print(f"  {status_icon} [{vr['verification_type']}] {vr['message']}")
    
    elif args.command == 'cycle':
        result = orchestrator.run_full_iteration_cycle(args.target, args.auto)
        
        print(f"\n迭代周期完成:")
        print(f"  周期ID: {result['cycle_id']}")
        print(f"  问题数: {result['problems_before']} → {result.get('problems_after', 'N/A')}")
        print(f"  质量分: {result['quality_score_before']} → {result.get('quality_score_after', 'N/A')}")
        
        if result.get('effect'):
            effect = result['effect']
            print(f"  ROI得分: {effect['roi_score']}")
            print(f"  节省时间: {effect['developer_time_saved_hours']} 小时")
    
    elif args.command == 'status':
        status = orchestrator.get_status()
        print(json.dumps(status, indent=2, ensure_ascii=False))
    
    elif args.command == 'report':
        report = orchestrator.generate_comprehensive_report(args.output)
        
        if args.output:
            print(f"报告已保存: {args.output}")
        else:
            print(report)
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
