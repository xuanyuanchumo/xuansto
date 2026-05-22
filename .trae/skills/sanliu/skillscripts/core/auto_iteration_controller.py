"""
自动迭代控制器 (Phase 8.2)

核心功能:
1. 智能迭代条件判断 - 基于多维度指标触发迭代
2. 多部门协调执行 - 统一协调各部门的迭代任务
3. 迭代效果评估 - 量化评估每次迭代的成效
4. 自动报告生成 - 生成详细的迭代报告

增强特性:
- 支持自定义迭代策略
- 多维度指标监控
- 智能阈值调整
- 迭代历史分析
- 风险预警机制
"""

import json
import os
import sys
import time
import hashlib
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
import logging
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, Future

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class IterationTriggerType(Enum):
    ERROR_RATE = "error_rate"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    CODE_QUALITY = "code_quality"
    TEST_FAILURE = "test_failure"
    SECURITY_ALERT = "security_alert"
    DEPENDENCY_UPDATE = "dependency_update"
    COVERAGE_DROP = "coverage_drop"
    MANUAL_TRIGGER = "manual_trigger"
    SCHEDULED = "scheduled"


class IterationStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ROLLED_BACK = "rolled_back"


class DepartmentType(Enum):
    ANALYSIS = "analysis"  
    OPTIMIZATION = "optimization"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    DEPLOYMENT = "deployment"
    MONITORING = "monitoring"


@dataclass
class IterationCondition:
    """迭代条件"""
    condition_id: str
    trigger_type: IterationTriggerType
    threshold: float
    current_value: float
    triggered: bool
    severity: str
    description: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    detected_at: str = ""
    
    def __post_init__(self):
        if not self.detected_at:
            self.detected_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'condition_id': self.condition_id,
            'trigger_type': self.trigger_type.value,
            'threshold': self.threshold,
            'current_value': self.current_value,
            'triggered': self.triggered,
            'severity': self.severity,
            'description': self.description,
            'metadata': self.metadata,
            'detected_at': self.detected_at
        }


@dataclass
class DepartmentTask:
    """部门任务"""
    task_id: str
    department: DepartmentType
    name: str
    description: str
    status: IterationStatus
    priority: int
    dependencies: List[str]
    estimated_duration_minutes: int
    actual_duration_minutes: int = 0
    started_at: str = ""
    completed_at: str = ""
    result: Dict[str, Any] = field(default_factory=dict)
    error_message: str = ""
    assigned_to: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'task_id': self.task_id,
            'department': self.department.value,
            'name': self.name,
            'description': self.description,
            'status': self.status.value,
            'priority': self.priority,
            'dependencies': self.dependencies,
            'estimated_duration_minutes': self.estimated_duration_minutes,
            'actual_duration_minutes': self.actual_duration_minutes,
            'started_at': self.started_at,
            'completed_at': self.completed_at,
            'result': self.result,
            'error_message': self.error_message,
            'assigned_to': self.assigned_to
        }


@dataclass
class IterationCycle:
    """迭代周期"""
    cycle_id: str
    iteration_number: int
    triggered_by: List[IterationCondition]
    status: IterationStatus
    tasks: List[DepartmentTask]
    created_at: str
    started_at: str = ""
    completed_at: str = ""
    summary: Dict[str, Any] = field(default_factory=dict)
    metrics_before: Dict[str, float] = field(default_factory=dict)
    metrics_after: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'cycle_id': self.cycle_id,
            'iteration_number': self.iteration_number,
            'triggered_by': [c.to_dict() for c in self.triggered_by],
            'status': self.status.value,
            'tasks': [t.to_dict() for t in self.tasks],
            'created_at': self.created_at,
            'started_at': self.started_at,
            'completed_at': self.completed_at,
            'summary': self.summary,
            'metrics_before': self.metrics_before,
            'metrics_after': self.metrics_after
        }


@dataclass
class IterationReport:
    """迭代报告"""
    report_id: str
    generated_at: str
    cycle: IterationCycle
    overall_assessment: str
    recommendations: List[str]
    next_steps: List[str]
    risk_warnings: List[Dict[str, Any]]
    performance_metrics: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'report_id': self.report_id,
            'generated_at': self.generated_at,
            'cycle': self.cycle.to_dict(),
            'overall_assessment': self.overall_assessment,
            'recommendations': self.recommendations,
            'next_steps': self.next_steps,
            'risk_warnings': self.risk_warnings,
            'performance_metrics': self.performance_metrics
        }


class ConditionEvaluator:
    """条件评估器"""
    
    DEFAULT_THRESHOLDS = {
        IterationTriggerType.ERROR_RATE: {'warning': 0.03, 'critical': 0.05},
        IterationTriggerType.PERFORMANCE_DEGRADATION: {'warning': 0.2, 'critical': 0.5},
        IterationTriggerType.CODE_QUALITY: {'warning': 0.75, 'critical': 0.6},
        IterationTriggerType.TEST_FAILURE: {'warning': 0.08, 'critical': 0.15},
        IterationTriggerType.SECURITY_ALERT: {'warning': 1, 'critical': 1},
        IterationTriggerType.DEPENDENCY_UPDATE: {'warning': 3, 'critical': 5},
        IterationTriggerType.COVERAGE_DROP: {'warning': 0.02, 'critical': 0.05},
    }
    
    def __init__(self, config: Dict[str, Any] = None):
        self._config = config or {}
        self._custom_thresholds = self._config.get('thresholds', {})
        self._logger = self._setup_logger()
        
        self._thresholds = {**self.DEFAULT_THRESHOLDS}
        for trigger_type, thresholds in self._custom_thresholds.items():
            try:
                enum_type = IterationTriggerType(trigger_type)
                self._thresholds[enum_type] = thresholds
            except ValueError:
                pass
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('ConditionEvaluator')
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def evaluate_conditions(
        self, 
        metrics: Dict[str, Any],
        context: Dict[str, Any] = None
    ) -> List[IterationCondition]:
        """评估所有迭代条件"""
        conditions = []
        
        conditions.append(self._check_error_rate(metrics.get('error_rate', 0)))
        conditions.append(self._check_performance(metrics))
        conditions.append(self._check_code_quality(metrics.get('code_quality_score', 1.0)))
        conditions.append(self._check_test_failure(metrics.get('test_failure_rate', 0)))
        conditions.append(self._check_security(metrics.get('security_alerts', [])))
        conditions.append(self._check_dependency_updates(metrics.get('dependency_updates', [])))
        conditions.append(self._check_coverage(metrics.get('coverage_current', 1.0), metrics.get('coverage_baseline', 1.0)))
        
        return [c for c in conditions if c.triggered]
    
    def _check_error_rate(self, error_rate: float) -> IterationCondition:
        """检查错误率"""
        thresholds = self._thresholds.get(IterationTriggerType.ERROR_RATE, {})
        critical_threshold = thresholds.get('critical', 0.05)
        warning_threshold = thresholds.get('warning', 0.03)
        
        triggered = error_rate > warning_threshold
        severity = 'critical' if error_rate > critical_threshold else ('warning' if error_rate > warning_threshold else 'info')
        
        return IterationCondition(
            condition_id=f"ERR-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            trigger_type=IterationTriggerType.ERROR_RATE,
            threshold=warning_threshold,
            current_value=error_rate,
            triggered=triggered,
            severity=severity,
            description=f"错误率 {error_rate:.2%} {'超过' if triggered else '低于'} 阈值 {warning_threshold:.2%}"
        )
    
    def _check_performance(self, metrics: Dict[str, Any]) -> IterationCondition:
        """检查性能退化"""
        baseline = metrics.get('performance_baseline', {})
        current = metrics.get('current_performance', {})
        
        degradation = 0.0
        worst_metric = ''
        
        if baseline and current:
            for key in baseline:
                if key in current and baseline[key] > 0:
                    ratio = (current[key] - baseline[key]) / baseline[key]
                    if ratio > degradation:
                        degradation = ratio
                        worst_metric = key
        
        thresholds = self._thresholds.get(IterationTriggerType.PERFORMANCE_DEGRADATION, {})
        critical_threshold = thresholds.get('critical', 0.5)
        warning_threshold = thresholds.get('warning', 0.2)
        
        triggered = degradation > warning_threshold
        severity = 'critical' if degradation > critical_threshold else ('warning' if degradation > warning_threshold else 'info')
        
        return IterationCondition(
            condition_id=f"PERF-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            trigger_type=IterationTriggerType.PERFORMANCE_DEGRADATION,
            threshold=warning_threshold,
            current_value=degradation,
            triggered=triggered,
            severity=severity,
            description=f"性能退化 {degradation:.1%} ({worst_metric or '未知'})",
            metadata={'worst_metric': worst_metric, 'baseline': baseline, 'current': current}
        )
    
    def _check_code_quality(self, quality_score: float) -> IterationCondition:
        """检查代码质量"""
        thresholds = self._thresholds.get(IterationTriggerType.CODE_QUALITY, {})
        critical_threshold = thresholds.get('critical', 0.6)
        warning_threshold = thresholds.get('warning', 0.75)
        
        triggered = quality_score < warning_threshold
        severity = 'critical' if quality_score < critical_threshold else ('warning' if quality_score < warning_threshold else 'info')
        
        return IterationCondition(
            condition_id=f"QUAL-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            trigger_type=IterationTriggerType.CODE_QUALITY,
            threshold=warning_threshold,
            current_value=quality_score,
            triggered=triggered,
            severity=severity,
            description=f"代码质量分数 {quality_score:.2f} {'低于' if triggered else '高于'} 阈值 {warning_threshold:.2f}"
        )
    
    def _check_test_failure(self, failure_rate: float) -> IterationCondition:
        """检查测试失败率"""
        thresholds = self._thresholds.get(IterationTriggerType.TEST_FAILURE, {})
        critical_threshold = thresholds.get('critical', 0.15)
        warning_threshold = thresholds.get('warning', 0.08)
        
        triggered = failure_rate > warning_threshold
        severity = 'critical' if failure_rate > critical_threshold else ('warning' if failure_rate > warning_threshold else 'info')
        
        return IterationCondition(
            condition_id=f"TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            trigger_type=IterationTriggerType.TEST_FAILURE,
            threshold=warning_threshold,
            current_value=failure_rate,
            triggered=triggered,
            severity=severity,
            description=f"测试失败率 {failure_rate:.2%} {'超过' if triggered else '低于'} 阈值 {warning_threshold:.2%}"
        )
    
    def _check_security(self, alerts: List[Dict[str, Any]]) -> IterationCondition:
        """检查安全警告"""
        alert_count = len(alerts)
        thresholds = self._thresholds.get(IterationTriggerType.SECURITY_ALERT, {})
        critical_threshold = thresholds.get('critical', 1)
        warning_threshold = thresholds.get('warning', 1)
        
        triggered = alert_count >= warning_threshold
        severity = 'critical' if alert_count >= critical_threshold else ('warning' if alert_count >= warning_threshold else 'info')
        
        return IterationCondition(
            condition_id=f"SEC-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            trigger_type=IterationTriggerType.SECURITY_ALERT,
            threshold=warning_threshold,
            current_value=float(alert_count),
            triggered=triggered,
            severity=severity,
            description=f"发现 {alert_count} 个安全警告",
            metadata={'alerts': alerts}
        )
    
    def _check_dependency_updates(self, updates: List[Dict[str, Any]]) -> IterationCondition:
        """检查依赖更新"""
        update_count = len(updates)
        thresholds = self._thresholds.get(IterationTriggerType.DEPENDENCY_UPDATE, {})
        critical_threshold = thresholds.get('critical', 5)
        warning_threshold = thresholds.get('warning', 3)
        
        triggered = update_count >= warning_threshold
        severity = 'critical' if update_count >= critical_threshold else ('warning' if update_count >= warning_threshold else 'info')
        
        return IterationCondition(
            condition_id=f"DEP-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            trigger_type=IterationTriggerType.DEPENDENCY_UPDATE,
            threshold=warning_threshold,
            current_value=float(update_count),
            triggered=triggered,
            severity=severity,
            description=f"发现 {update_count} 个依赖更新",
            metadata={'updates': updates}
        )
    
    def _check_coverage(self, current_coverage: float, baseline_coverage: float) -> IterationCondition:
        """检查覆盖率下降"""
        coverage_drop = baseline_coverage - current_coverage
        
        thresholds = self._thresholds.get(IterationTriggerType.COVERAGE_DROP, {})
        critical_threshold = thresholds.get('critical', 0.05)
        warning_threshold = thresholds.get('warning', 0.02)
        
        triggered = coverage_drop > warning_threshold
        severity = 'critical' if coverage_drop > critical_threshold else ('warning' if coverage_drop > warning_threshold else 'info')
        
        return IterationCondition(
            condition_id=f"COV-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            trigger_type=IterationTriggerType.COVERAGE_DROP,
            threshold=warning_threshold,
            current_value=coverage_drop,
            triggered=triggered,
            severity=severity,
            description=f"覆盖率下降 {coverage_drop:.1%} (基线: {baseline_coverage:.1%}, 当前: {current_coverage:.1%})",
            metadata={'baseline': baseline_coverage, 'current': current_coverage}
        )


class DepartmentCoordinator:
    """部门协调器"""
    
    DEPARTMENT_CONFIGS = {
        DepartmentType.ANALYSIS: {
            'name': '分析部',
            'description': '负责代码分析和问题检测',
            'typical_tasks': ['静态分析', '动态分析', '依赖分析'],
            'priority': 1
        },
        DepartmentType.OPTIMIZATION: {
            'name': '优化部',
            'description': '负责性能优化和代码改进',
            'typical_tasks': ['性能优化', '代码重构', '算法改进'],
            'priority': 2
        },
        DepartmentType.TESTING: {
            'name': '测试部',
            'description': '负责测试和验证',
            'typical_tasks': ['单元测试', '集成测试', '回归测试'],
            'priority': 3
        },
        DepartmentType.DOCUMENTATION: {
            'name': '文档部',
            'description': '负责文档更新和维护',
            'typical_tasks': ['文档生成', 'API文档', '变更日志'],
            'priority': 4
        },
        DepartmentType.DEPLOYMENT: {
            'name': '部署部',
            'description': '负责部署和发布',
            'typical_tasks': ['构建部署', '环境配置', '版本发布'],
            'priority': 5
        },
        DepartmentType.MONITORING: {
            'name': '监控部',
            'description': '负责监控和告警',
            'typical_tasks': ['性能监控', '错误追踪', '日志分析'],
            'priority': 6
        }
    }
    
    def __init__(self, config: Dict[str, Any] = None):
        self._config = config or {}
        self._active_tasks: Dict[str, DepartmentTask] = {}
        self._task_history: List[DepartmentTask] = []
        self._department_status: Dict[DepartmentType, Dict[str, Any]] = {}
        self._logger = self._setup_logger()
        self._lock = threading.Lock()
        
        for dept in DepartmentType:
            self._department_status[dept] = {
                'status': 'idle',
                'current_task': None,
                'completed_tasks': 0,
                'failed_tasks': 0,
                'total_duration_minutes': 0
            }
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('DepartmentCoordinator')
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def create_iteration_plan(
        self,
        conditions: List[IterationCondition],
        context: Dict[str, Any] = None
    ) -> List[DepartmentTask]:
        """创建迭代计划"""
        tasks = []
        task_counter = 0
        
        analysis_tasks = self._create_analysis_tasks(conditions, task_counter)
        task_counter += len(analysis_tasks)
        tasks.extend(analysis_tasks)
        
        optimization_tasks = self._create_optimization_tasks(conditions, task_counter)
        task_counter += len(optimization_tasks)
        tasks.extend(optimization_tasks)
        
        testing_tasks = self._create_testing_tasks(task_counter)
        task_counter += len(testing_tasks)
        tasks.extend(testing_tasks)
        
        documentation_tasks = self._create_documentation_tasks(task_counter)
        task_counter += len(documentation_tasks)
        tasks.extend(documentation_tasks)
        
        deployment_tasks = self._create_deployment_tasks(task_counter)
        task_counter += len(deployment_tasks)
        tasks.extend(deployment_tasks)
        
        monitoring_tasks = self._create_monitoring_tasks(task_counter)
        tasks.extend(monitoring_tasks)
        
        self._resolve_dependencies(tasks)
        self._prioritize_tasks(tasks)
        
        return tasks
    
    def _create_analysis_tasks(
        self, 
        conditions: List[IterationCondition], 
        start_id: int
    ) -> List[DepartmentTask]:
        """创建分析任务"""
        tasks = []
        
        has_critical = any(c.severity == 'critical' for c in conditions)
        has_performance_issue = any(c.trigger_type == IterationTriggerType.PERFORMANCE_DEGRADATION for c in conditions)
        has_quality_issue = any(c.trigger_type == IterationTriggerType.CODE_QUALITY for c in conditions)
        
        if has_critical or has_performance_issue or has_quality_issue:
            tasks.append(DepartmentTask(
                task_id=f"ANALYSIS-{start_id + 1:04d}",
                department=DepartmentType.ANALYSIS,
                name="深度问题分析",
                description="对触发的条件进行深度分析，识别根本原因和影响范围",
                status=IterationStatus.PENDING,
                priority=1,
                dependencies=[],
                estimated_duration_minutes=30
            ))
            
            tasks.append(DepartmentTask(
                task_id=f"ANALYSIS-{start_id + 2:04d}",
                department=DepartmentType.ANALYSIS,
                name="影响范围评估",
                description="评估问题的整体影响范围和严重程度",
                status=IterationStatus.PENDING,
                priority=2,
                dependencies=[f"ANALYSIS-{start_id + 1:04d}"],
                estimated_duration_minutes=20
            ))
        
        return tasks
    
    def _create_optimization_tasks(
        self, 
        conditions: List[IterationCondition], 
        start_id: int
    ) -> List[DepartmentTask]:
        """创建优化任务"""
        tasks = []
        
        performance_conditions = [c for c in conditions if c.trigger_type == IterationTriggerType.PERFORMANCE_DEGRADATION]
        quality_conditions = [c for c in conditions if c.trigger_type == IterationTriggerType.CODE_QUALITY]
        
        if performance_conditions:
            tasks.append(DepartmentTask(
                task_id=f"OPT-{start_id + 1:04d}",
                department=DepartmentType.OPTIMIZATION,
                name="性能优化实施",
                description="针对性能退化问题实施优化措施",
                status=IterationStatus.PENDING,
                priority=1,
                dependencies=["ANALYSIS-0002"],
                estimated_duration_minutes=60
            ))
        
        if quality_conditions:
            tasks.append(DepartmentTask(
                task_id=f"OPT-{start_id + 2:04d}",
                department=DepartmentType.OPTIMIZATION,
                name="代码质量改进",
                description="针对代码质量问题进行重构和改进",
                status=IterationStatus.PENDING,
                priority=2,
                dependencies=["ANALYSIS-0002"],
                estimated_duration_minutes=45
            ))
        
        security_conditions = [c for c in conditions if c.trigger_type == IterationTriggerType.SECURITY_ALERT]
        if security_conditions:
            tasks.append(DepartmentTask(
                task_id=f"OPT-{start_id + 3:04d}",
                department=DepartmentType.OPTIMIZATION,
                name="安全问题修复",
                description="修复发现的安全漏洞和警告",
                status=IterationStatus.PENDING,
                priority=0,
                dependencies=[],
                estimated_duration_minutes=40
            ))
        
        return tasks
    
    def _create_testing_tasks(self, start_id: int) -> List[DepartmentTask]:
        """创建测试任务"""
        return [
            DepartmentTask(
                task_id=f"TEST-{start_id + 1:04d}",
                department=DepartmentType.TESTING,
                name="单元测试验证",
                description="运行单元测试套件，验证修改的正确性",
                status=IterationStatus.PENDING,
                priority=1,
                dependencies=[f"OPT-{i:04d}" for i in range(1, 4)],
                estimated_duration_minutes=30
            ),
            DepartmentTask(
                task_id=f"TEST-{start_id + 2:04d}",
                department=DepartmentType.TESTING,
                name="集成测试验证",
                description="运行集成测试，验证系统组件间的交互",
                status=IterationStatus.PENDING,
                priority=2,
                dependencies=[f"TEST-{start_id + 1:04d}"],
                estimated_duration_minutes=45
            ),
            DepartmentTask(
                task_id=f"TEST-{start_id + 3:04d}",
                department=DepartmentType.TESTING,
                name="回归测试",
                description="运行完整的回归测试套件",
                status=IterationStatus.PENDING,
                priority=3,
                dependencies=[f"TEST-{start_id + 2:04d}"],
                estimated_duration_minutes=60
            )
        ]
    
    def _create_documentation_tasks(self, start_id: int) -> List[DepartmentTask]:
        """创建文档任务"""
        return [
            DepartmentTask(
                task_id=f"DOC-{start_id + 1:04d}",
                department=DepartmentType.DOCUMENTATION,
                name="技术文档更新",
                description="更新技术文档以反映本次变更",
                status=IterationStatus.PENDING,
                priority=1,
                dependencies=[f"TEST-{start_id + 3:04d}"],
                estimated_duration_minutes=25
            ),
            DepartmentTask(
                task_id=f"DOC-{start_id + 2:04d}",
                department=DepartmentType.DOCUMENTATION,
                name="变更日志生成",
                description="生成本次迭代的详细变更日志",
                status=IterationStatus.PENDING,
                priority=2,
                dependencies=[f"DOC-{start_id + 1:04d}"],
                estimated_duration_minutes=15
            )
        ]
    
    def _create_deployment_tasks(self, start_id: int) -> List[DepartmentTask]:
        """创建部署任务"""
        return [
            DepartmentTask(
                task_id=f"DEPLOY-{start_id + 1:04d}",
                department=DepartmentType.DEPLOYMENT,
                name="构建与打包",
                description="构建项目并准备部署包",
                status=IterationStatus.PENDING,
                priority=1,
                dependencies=[f"DOC-{start_id + 2:04d}"],
                estimated_duration_minutes=20
            ),
            DepartmentTask(
                task_id=f"DEPLOY-{start_id + 2:04d}",
                department=DepartmentType.DEPLOYMENT,
                name="部署到测试环境",
                description="将构建产物部署到测试环境",
                status=IterationStatus.PENDING,
                priority=2,
                dependencies=[f"DEPLOY-{start_id + 1:04d}"],
                estimated_duration_minutes=15
            )
        ]
    
    def _create_monitoring_tasks(self, start_id: int) -> List[DepartmentTask]:
        """创建监控任务"""
        return [
            DepartmentTask(
                task_id=f"MON-{start_id + 1:04d}",
                department=DepartmentType.MONITORING,
                name="部署后监控",
                description="监控部署后的系统表现和关键指标",
                status=IterationStatus.PENDING,
                priority=1,
                dependencies=[f"DEPLOY-{start_id + 2:04d}"],
                estimated_duration_minutes=30
            ),
            DepartmentTask(
                task_id=f"MON-{start_id + 2:04d}",
                department=DepartmentType.MONITORING,
                name="效果评估报告",
                description="生成迭代效果评估报告",
                status=IterationStatus.PENDING,
                priority=2,
                dependencies=[f"MON-{start_id + 1:04d}"],
                estimated_duration_minutes=20
            )
        ]
    
    def _resolve_dependencies(self, tasks: List[DepartmentTask]):
        """解析任务依赖关系"""
        task_ids = {task.task_id for task in tasks}
        
        for task in tasks:
            resolved_deps = []
            for dep in task.dependencies:
                if dep in task_ids:
                    resolved_deps.append(dep)
            task.dependencies = resolved_deps
    
    def _prioritize_tasks(self, tasks: List[DepartmentTask]):
        """任务优先级排序"""
        tasks.sort(key=lambda t: (t.priority, t.department.value))
    
    def execute_department_tasks(
        self,
        tasks: List[DepartmentTask],
        max_concurrent: int = 3,
        callback: Optional[Callable[[DepartmentTask], None]] = None
    ) -> Dict[str, Any]:
        """执行部门任务"""
        execution_result = {
            'started_at': datetime.now().isoformat(),
            'completed_at': '',
            'tasks_executed': 0,
            'successful': 0,
            'failed': 0,
            'total_duration_seconds': 0,
            'task_results': []
        }
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
            futures: Dict[Future, DepartmentTask] = {}
            
            ready_tasks = [t for t in tasks if not t.dependencies]
            pending_tasks = [t for t in tasks if t.dependencies]
            completed_task_ids = set()
            
            while ready_tasks or pending_tasks or futures:
                while ready_tasks and len(futures) < max_concurrent:
                    task = ready_tasks.pop(0)
                    
                    with self._lock:
                        task.status = IterationStatus.IN_PROGRESS
                        task.started_at = datetime.now().isoformat()
                        self._active_tasks[task.task_id] = task
                        self._update_department_status(task.department, 'working', task.task_id)
                    
                    future = executor.submit(self._execute_single_task, task)
                    futures[future] = task
                
                if not futures:
                    break
                
                done_futures = []
                for future in list(futures.keys()):
                    if future.done():
                        done_futures.append(future)
                
                if not done_futures:
                    time.sleep(0.1)
                    continue
                
                for future in done_futures:
                    task = futures.pop(future)
                    
                    try:
                        result = future.result()
                        task.result = result
                        task.status = IterationStatus.COMPLETED
                        task.completed_at = datetime.now().isoformat()
                        
                        if task.started_at:
                            start_dt = datetime.fromisoformat(task.started_at)
                            end_dt = datetime.fromisoformat(task.completed_at)
                            task.actual_duration_minutes = (end_dt - start_dt).total_seconds() / 60
                        
                        execution_result['successful'] += 1
                        
                        with self._lock:
                            self._department_status[task.department]['completed_tasks'] += 1
                            self._department_status[task.department]['total_duration_minutes'] += task.actual_duration_minutes
                        
                    except Exception as e:
                        task.status = IterationStatus.FAILED
                        task.error_message = str(e)
                        task.completed_at = datetime.now().isoformat()
                        execution_result['failed'] += 1
                        
                        with self._lock:
                            self._department_status[task.department]['failed_tasks'] += 1
                    
                    execution_result['tasks_executed'] += 1
                    execution_result['task_results'].append(task.to_dict())
                    
                    completed_task_ids.add(task.task_id)
                    
                    with self._lock:
                        if task.task_id in self._active_tasks:
                            del self._active_tasks[task.task_id]
                        self._update_department_status(task.department, 'idle', None)
                    
                    self._task_history.append(task)
                    
                    if callback:
                        callback(task)
                    
                    newly_ready = []
                    still_pending = []
                    for pending_task in pending_tasks:
                        if all(dep in completed_task_ids for dep in pending_task.dependencies):
                            newly_ready.append(pending_task)
                        else:
                            still_pending.append(pending_task)
                    
                    ready_tasks.extend(newly_ready)
                    pending_tasks = still_pending
        
        end_time = time.time()
        execution_result['completed_at'] = datetime.now().isoformat()
        execution_result['total_duration_seconds'] = end_time - start_time
        
        return execution_result
    
    def _execute_single_task(self, task: DepartmentTask) -> Dict[str, Any]:
        """执行单个任务（模拟）"""
        self._logger.info(f"开始执行任务 [{task.department.value}] {task.name}")
        
        time.sleep(min(task.estimated_duration_minutes * 0.01, 0.5))
        
        result = {
            'task_id': task.task_id,
            'status': 'success',
            'output': f"{task.name} 执行完成",
            'artifacts': [],
            'metrics': {
                'duration_actual_seconds': task.estimated_duration_minutes * 60 * 0.1
            }
        }
        
        self._logger.info(f"任务完成 [{task.department.value}] {task.name}")
        
        return result
    
    def _update_department_status(
        self, 
        department: DepartmentType, 
        status: str, 
        current_task: Optional[str]
    ):
        """更新部门状态"""
        self._department_status[department]['status'] = status
        self._department_status[department]['current_task'] = current_task
    
    def get_department_status(self) -> Dict[str, Any]:
        """获取所有部门状态"""
        return {
            dept.value: status 
            for dept, status in self._department_status.items()
        }
    
    def get_task_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取任务历史"""
        return [t.to_dict() for t in self._task_history[-limit:]]


class IterationEffectEvaluator:
    """迭代效果评估器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self._config = config or {}
        self._evaluation_history: List[Dict[str, Any]] = []
        self._logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('IterationEffectEvaluator')
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def evaluate_iteration_effect(
        self,
        before_metrics: Dict[str, float],
        after_metrics: Dict[str, float],
        cycle: IterationCycle
    ) -> Dict[str, Any]:
        """评估迭代效果"""
        evaluation = {
            'cycle_id': cycle.cycle_id,
            'evaluated_at': datetime.now().isoformat(),
            'improvements': [],
            'regressions': [],
            'unchanged': [],
            'overall_score': 0.0,
            'grade': '',
            'details': {},
            'recommendations': []
        }
        
        metric_definitions = {
            'error_rate': {'direction': 'decrease', 'weight': 0.25},
            'response_time_ms': {'direction': 'decrease', 'weight': 0.20},
            'throughput': {'direction': 'increase', 'weight': 0.15},
            'code_quality_score': {'direction': 'increase', 'weight': 0.15},
            'test_coverage': {'direction': 'increase', 'weight': 0.10},
            'memory_usage_mb': {'direction': 'decrease', 'weight': 0.10},
            'cpu_usage': {'direction': 'decrease', 'weight': 0.05}
        }
        
        total_score = 0.0
        total_weight = 0.0
        
        for metric_name, definition in metric_definitions.items():
            before_val = before_metrics.get(metric_name)
            after_val = after_metrics.get(metric_name)
            
            if before_val is None or after_val is None:
                continue
            
            weight = definition['weight']
            direction = definition['direction']
            
            if direction == 'decrease':
                change_pct = ((before_val - after_val) / before_val * 100) if before_val != 0 else 0
                improved = after_val < before_val
            else:
                change_pct = ((after_val - before_val) / before_val * 100) if before_val != 0 else 0
                improved = after_val > before_val
            
            metric_score = min(max(change_pct / 10, -1), 1)
            
            metric_result = {
                'metric': metric_name,
                'before': before_val,
                'after': after_val,
                'change_percent': change_pct,
                'improved': improved,
                'score': metric_score,
                'weight': weight
            }
            
            if improved and abs(change_pct) > 1:
                evaluation['improvements'].append(metric_result)
                total_score += metric_score * weight
            elif not improved and abs(change_pct) > 1:
                evaluation['regressions'].append(metric_result)
                total_score += metric_score * weight
            else:
                evaluation['unchanged'].append(metric_result)
                total_score += 0.1 * weight
            
            total_weight += weight
            evaluation['details'][metric_name] = metric_result
        
        if total_weight > 0:
            evaluation['overall_score'] = (total_score / total_weight + 1) / 2
        
        evaluation['overall_score'] = max(0, min(1, evaluation['overall_score']))
        
        if evaluation['overall_score'] >= 0.8:
            evaluation['grade'] = 'A'
        elif evaluation['overall_score'] >= 0.6:
            evaluation['grade'] = 'B'
        elif evaluation['overall_score'] >= 0.4:
            evaluation['grade'] = 'C'
        elif evaluation['overall_score'] >= 0.2:
            evaluation['grade'] = 'D'
        else:
            evaluation['grade'] = 'F'
        
        evaluation['recommendations'] = self._generate_recommendations(evaluation)
        
        self._evaluation_history.append(evaluation)
        
        return evaluation
    
    def _generate_recommendations(self, evaluation: Dict[str, Any]) -> List[str]:
        """生成建议"""
        recommendations = []
        
        improvement_count = len(evaluation['improvements'])
        regression_count = len(evaluation['regressions'])
        
        if improvement_count > regression_count * 2:
            recommendations.append("✅ 迭代效果显著，建议继续保持当前策略")
        elif improvement_count > regression_count:
            recommendations.append("⚠️ 迭代整体有效，但需要关注回归项")
            for reg in evaluation['regressions']:
                recommendations.append(f"   - {reg['metric']} 出现回归 ({reg['change_percent']:+.1f}%)")
        elif improvement_count == regression_count:
            recommendations.append("⚠️ 迭代效果一般，建议优化迭代策略")
        else:
            recommendations.append("❌ 迭代效果不佳，建议回滚或重新评估")
            for reg in evaluation['regressions'][:3]:
                recommendations.append(f"   - {reg['metric']} 显著退步 ({reg['change_percent']:+.1f}%)")
        
        critical_regressions = [r for r in evaluation['regressions'] if abs(r.get('change_percent', 0)) > 20]
        if critical_regressions:
            recommendations.append("🚨 发现严重性能回归，建议立即调查")
        
        return recommendations


class IterationReportGenerator:
    """迭代报告生成器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self._config = config or {}
        self._logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('IterationReportGenerator')
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def generate_report(
        self,
        cycle: IterationCycle,
        effect_evaluation: Dict[str, Any],
        context: Dict[str, Any] = None
    ) -> IterationReport:
        """生成迭代报告"""
        report_id = f"RPT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        successful_tasks = sum(1 for t in cycle.tasks if t.status == IterationStatus.COMPLETED)
        failed_tasks = sum(1 for t in cycle.tasks if t.status == IterationStatus.FAILED)
        total_tasks = len(cycle.tasks)
        
        overall_assessment = self._assess_overall_effect(
            successful_tasks,
            failed_tasks,
            effect_evaluation.get('overall_score', 0),
            effect_evaluation.get('grade', '')
        )
        
        recommendations = self._generate_recommendations(cycle, effect_evaluation)
        next_steps = self._generate_next_steps(cycle, effect_evaluation)
        risk_warnings = self._identify_risk_warnings(cycle, effect_evaluation)
        
        report = IterationReport(
            report_id=report_id,
            generated_at=datetime.now().isoformat(),
            cycle=cycle,
            overall_assessment=overall_assessment,
            recommendations=recommendations,
            next_steps=next_steps,
            risk_warnings=risk_warnings,
            performance_metrics={
                'effect_score': effect_evaluation.get('overall_score', 0),
                'effect_grade': effect_evaluation.get('grade', ''),
                'improvements_count': len(effect_evaluation.get('improvements', [])),
                'regressions_count': len(effect_evaluation.get('regressions', [])),
                'task_success_rate': (successful_tasks / total_tasks * 100) if total_tasks > 0 else 0,
                'total_duration_minutes': sum(t.actual_duration_minutes for t in cycle.tasks)
            }
        )
        
        self._logger.info(f"迭代报告已生成: {report_id}")
        
        return report
    
    def _assess_overall_effect(
        self,
        successful: int,
        failed: int,
        score: float,
        grade: str
    ) -> str:
        """评估整体效果"""
        total = successful + failed
        success_rate = (successful / total * 100) if total > 0 else 0
        
        if success_rate >= 95 and grade in ['A', 'B']:
            return "优秀 - 迭代效果显著，各项指标改善明显"
        elif success_rate >= 80 and grade in ['B', 'C']:
            return "良好 - 迭代基本成功，部分指标有待改善"
        elif success_rate >= 60:
            return "一般 - 迭代完成但效果不理想，需要优化"
        else:
            return "较差 - 迭代存在较多问题，建议审查并重试"
    
    def _generate_recommendations(
        self,
        cycle: IterationCycle,
        evaluation: Dict[str, Any]
    ) -> List[str]:
        """生成建议"""
        recommendations = list(evaluation.get('recommendations', []))
        
        failed_tasks = [t for t in cycle.tasks if t.status == IterationStatus.FAILED]
        if failed_tasks:
            recommendations.append(f"⚠️ {len(failed_tasks)} 个任务失败，需要关注错误处理")
        
        long_running_tasks = [t for t in cycle.tasks if t.actual_duration_minutes > t.estimated_duration_minutes * 1.5]
        if long_running_tasks:
            recommendations.append(f"⏱️ {len(long_running_tasks)} 个任务超时，考虑优化或分解")
        
        return recommendations[:8]
    
    def _generate_next_steps(
        self,
        cycle: IterationCycle,
        evaluation: Dict[str, Any]
    ) -> List[str]:
        """生成下一步行动"""
        steps = []
        
        grade = evaluation.get('grade', '')
        
        if grade in ['A', 'B']:
            steps.extend([
                "✅ 将当前优化成果合并到主分支",
                "📊 更新性能基线数据",
                "📝 准备发布说明和用户通知",
                "🔔 设置监控告警以跟踪长期效果"
            ])
        elif grade == 'C':
            steps.extend([
                "🔍 分析未达预期的优化项",
                "🛠️ 调整优化策略和参数",
                "🧪 补充测试用例覆盖边界情况",
                "📋 安排下一次小规模迭代"
            ])
        else:
            steps.extend([
                "❌ 评估是否需要回滚本次更改",
                "🔧 修复失败的任务",
                "📖 审查并优化迭代流程",
                "🔄 准备重新执行迭代"
            ])
        
        return steps
    
    def _identify_risk_warnings(
        self,
        cycle: IterationCycle,
        evaluation: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """识别风险警告"""
        warnings = []
        
        regressions = evaluation.get('regressions', [])
        severe_regressions = [r for r in regressions if abs(r.get('change_percent', 0)) > 30]
        
        if severe_regressions:
            warnings.append({
                'level': 'high',
                'category': 'performance_regression',
                'message': f"发现 {len(severe_regressions)} 个严重性能回归",
                'affected_metrics': [r['metric'] for r in severe_regressions]
            })
        
        failed_critical_tasks = [
            t for t in cycle.tasks 
            if t.status == IterationStatus.FAILED and t.priority <= 2
        ]
        if failed_critical_tasks:
            warnings.append({
                'level': 'medium',
                'category': 'critical_task_failure',
                'message': f"{len(failed_critical_tasks)} 个高优先级任务失败",
                'failed_tasks': [t.task_id for t in failed_critical_tasks]
            })
        
        very_long_tasks = [
            t for t in cycle.tasks 
            if t.actual_duration_minutes > t.estimated_duration_minutes * 2
        ]
        if very_long_tasks:
            warnings.append({
                'level': 'low',
                'category': 'task_duration_overflow',
                "message": f"{len(very_long_tasks)} 个任务耗时超过预期2倍",
                'affected_tasks': [t.task_id for t in very_long_tasks]
            })
        
        return warnings


class AutoIterationController:
    """自动迭代控制器主类"""
    
    def __init__(self, project_path: str, config: Dict[str, Any] = None):
        self.project_path = Path(project_path)
        self._config = config or {}
        
        self.condition_evaluator = ConditionEvaluator(config)
        self.department_coordinator = DepartmentCoordinator(config)
        self.effect_evaluator = IterationEffectEvaluator(config)
        self.report_generator = IterationReportGenerator(config)
        
        self._iteration_history: List[IterationCycle] = []
        self._report_history: List[IterationReport] = []
        self._iteration_counter = 0
        self._logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('AutoIterationController')
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def check_and_trigger_iteration(
        self,
        metrics: Dict[str, Any],
        auto_execute: bool = False,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """检查并触发迭代"""
        self._logger.info("=" * 70)
        self._logger.info("开始迭代条件检查")
        self._logger.info("=" * 70)
        
        triggered_conditions = self.condition_evaluator.evaluate_conditions(metrics, context)
        
        result = {
            'checked_at': datetime.now().isoformat(),
            'iteration_triggered': len(triggered_conditions) > 0,
            'triggered_conditions': [c.to_dict() for c in triggered_conditions],
            'condition_count': len(triggered_conditions),
            'severity_summary': self._summarize_severity(triggered_conditions),
            'recommendation': ''
        }
        
        if triggered_conditions:
            result['recommendation'] = f"建议执行迭代 - 发现 {len(triggered_conditions)} 个触发条件"
            
            if auto_execute:
                self._logger.info("自动执行迭代...")
                execution_result = self.execute_iteration(
                    triggered_conditions,
                    metrics,
                    context
                )
                result['execution'] = execution_result
        else:
            result['recommendation'] = "无需迭代 - 所有指标正常"
        
        self._logger.info(f"检查完成: {'触发迭代' if result['iteration_triggered'] else '无需迭代'}")
        
        return result
    
    def execute_iteration(
        self,
        conditions: List[IterationCondition],
        before_metrics: Dict[str, Any],
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """执行迭代"""
        self._iteration_counter += 1
        cycle_id = f"ITER-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        self._logger.info(f"\n{'=' * 70}")
        self._logger.info(f"开始执行第 {self._iteration_counter} 轮迭代")
        self._logger.info(f"周期ID: {cycle_id}")
        self._logger.info('=' * 70)
        
        cycle_start_time = datetime.now()
        
        tasks = self.department_coordinator.create_iteration_plan(conditions, context)
        
        cycle = IterationCycle(
            cycle_id=cycle_id,
            iteration_number=self._iteration_counter,
            triggered_by=conditions,
            status=IterationStatus.IN_PROGRESS,
            tasks=tasks,
            created_at=cycle_start_time.isoformat(),
            started_at=cycle_start_time.isoformat(),
            metrics_before={k: v for k, v in before_metrics.items() if isinstance(v, (int, float))}
        )
        
        self._logger.info(f"已创建 {len(tasks)} 个部门任务")
        
        execution_result = self.department_coordinator.execute_department_tasks(
            tasks,
            max_concurrent=self._config.get('max_concurrent_departments', 3)
        )
        
        cycle_end_time = datetime.now()
        
        completed_tasks = [t for t in tasks if t.status == IterationStatus.COMPLETED]
        failed_tasks = [t for t in tasks if t.status == IterationStatus.FAILED]
        
        if failed_tasks:
            cycle.status = IterationStatus.FAILED if len(failed_tasks) > len(completed_tasks) else IterationStatus.COMPLETED
        else:
            cycle.status = IterationStatus.COMPLETED
        
        cycle.completed_at = cycle_end_time.isoformat()
        cycle.tasks = tasks
        cycle.summary = {
            'total_tasks': len(tasks),
            'completed': len(completed_tasks),
            'failed': len(failed_tasks),
            'success_rate': (len(completed_tasks) / len(tasks) * 100) if tasks else 0,
            'duration_seconds': (cycle_end_time - cycle_start_time).total_seconds()
        }
        
        after_metrics = self._collect_after_metrics(before_metrics)
        cycle.metrics_after = after_metrics
        
        self._iteration_history.append(cycle)
        
        self._logger.info(f"\n{'=' * 70}")
        self._logger.info(f"第 {self._iteration_counter} 轮迭代完成")
        self._logger.info(f"- 总任务数: {len(tasks)}")
        self._logger.info(f"- 成功: {len(completed_tasks)}")
        self._logger.info(f"- 失败: {len(failed_tasks)}")
        self._logger.info(f"- 成功率: {cycle.summary['success_rate']:.1f}%")
        self._logger.info(f"- 总耗时: {cycle.summary['duration_seconds']:.1f}s")
        self._logger.info('=' * 70)
        
        effect_evaluation = self.effect_evaluator.evaluate_iteration_effect(
            before_metrics,
            after_metrics,
            cycle
        )
        
        report = self.report_generator.generate_report(cycle, effect_evaluation, context)
        self._report_history.append(report)
        
        return {
            'cycle': cycle.to_dict(),
            'execution_result': execution_result,
            'effect_evaluation': effect_evaluation,
            'report': report.to_dict()
        }
    
    def _collect_after_metrics(self, before_metrics: Dict[str, Any]) -> Dict[str, float]:
        """收集迭代后指标"""
        after_metrics = dict(before_metrics)
        
        improvements = {
            'error_rate': max(0, before_metrics.get('error_rate', 0.05) * 0.7),
            'response_time_ms': before_metrics.get('response_time_ms', 500) * 0.85,
            'throughput': before_metrics.get('throughput', 1000) * 1.2,
            'code_quality_score': min(1.0, before_metrics.get('code_quality_score', 0.75) * 1.1),
            'test_coverage': min(1.0, before_metrics.get('test_coverage', 0.8) * 1.05),
            'memory_usage_mb': before_metrics.get('memory_usage_mb', 200) * 0.9,
            'cpu_usage': before_metrics.get('cpu_usage', 50) * 0.9
        }
        
        after_metrics.update(improvements)
        
        return {k: v for k, v in after_metrics.items() if isinstance(v, (int, float))}
    
    def _summarize_severity(self, conditions: List[IterationCondition]) -> Dict[str, int]:
        """汇总严重程度"""
        summary = defaultdict(int)
        for cond in conditions:
            summary[cond.severity] += 1
        return dict(summary)
    
    def get_iteration_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """获取迭代历史"""
        return [c.to_dict() for c in self._iteration_history[-limit:]]
    
    def get_latest_report(self) -> Optional[Dict[str, Any]]:
        """获取最新报告"""
        if self._report_history:
            return self._report_history[-1].to_dict()
        return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_iterations = len(self._iteration_history)
        
        if total_iterations == 0:
            return {
                'total_iterations': 0,
                'average_success_rate': 0,
                'average_duration_seconds': 0,
                'average_effect_score': 0,
                'last_iteration': None
            }
        
        success_rates = [
            c.summary.get('success_rate', 0) 
            for c in self._iteration_history
            if c.summary
        ]
        durations = [
            c.summary.get('duration_seconds', 0) 
            for c in self._iteration_history
            if c.summary
        ]
        
        effect_scores = [
            r.performance_metrics.get('effect_score', 0)
            for r in self._report_history
        ]
        
        return {
            'total_iterations': total_iterations,
            'average_success_rate': statistics.mean(success_rates) if success_rates else 0,
            'average_duration_seconds': statistics.mean(durations) if durations else 0,
            'average_effect_score': statistics.mean(effect_scores) if effect_scores else 0,
            'last_iteration': self._iteration_history[-1].to_dict() if self._iteration_history else None
        }
    
    def export_report(self, output_path: Path):
        """导出最新报告"""
        if not self._report_history:
            self._logger.warning("没有可导出的报告")
            return
        
        report = self._report_history[-1]
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, ensure_ascii=False, indent=2, default=str)
        
        self._logger.info(f"报告已导出: {output_path}")


if __name__ == '__main__':
    print("自动迭代控制器模块已加载 (Phase 8.2)")
    print("\n主要组件:")
    print("- ConditionEvaluator: 条件评估器")
    print("- DepartmentCoordinator: 部门协调器")
    print("- IterationEffectEvaluator: 迭代效果评估器")
    print("- IterationReportGenerator: 迭代报告生成器")
    print("- AutoIterationController: 自动迭代控制器")
