#!/usr/bin/env python3
"""
自迭代智能触发增强脚本
实现智能问题检测、迭代计划生成、自迭代触发机制

功能:
- 智能问题检测（代码质量、性能、安全问题检测）
- 迭代计划生成（自动生成改进计划）
- 自迭代触发（根据检测结果自动触发迭代）
"""

import os
import sys
import json
import re
import logging
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
from collections import defaultdict
import hashlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class ProblemType(Enum):
    CODE_QUALITY = "code_quality"
    PERFORMANCE = "performance"
    SECURITY = "security"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    DEPENDENCY = "dependency"
    ARCHITECTURE = "architecture"
    MAINTAINABILITY = "maintainability"


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
    
    def __post_init__(self):
        if not self.detected_at:
            self.detected_at = datetime.now().isoformat()
        if self.metadata is None:
            self.metadata = {}


@dataclass
class IterationTask:
    task_id: str
    title: str
    description: str
    problem_ids: List[str]
    priority: IterationPriority
    status: IterationStatus
    estimated_effort: str
    assigned_to: str = "系统"
    created_at: str = ""
    started_at: str = ""
    completed_at: str = ""
    dependencies: List[str] = None
    steps: List[Dict[str, Any]] = None
    result: Dict[str, Any] = None
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if self.dependencies is None:
            self.dependencies = []
        if self.steps is None:
            self.steps = []
        if self.result is None:
            self.result = {}


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
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


@dataclass
class TriggerCondition:
    condition_id: str
    name: str
    description: str
    condition_type: str
    threshold: float
    current_value: float
    is_triggered: bool
    last_checked: str = ""
    
    def __post_init__(self):
        if not self.last_checked:
            self.last_checked = datetime.now().isoformat()


class ProblemDetector:
    """智能问题检测器"""
    
    CODE_QUALITY_PATTERNS = {
        'long_function': {
            'pattern': r'def\s+\w+\([^)]*\):[^}]{500,}',
            'message': '函数过长，建议拆分',
            'severity': ProblemSeverity.MEDIUM
        },
        'complex_condition': {
            'pattern': r'if\s+[^:]+(and|or)[^:]+(and|or)[^:]+(and|or)[^:]+:',
            'message': '条件过于复杂，建议简化',
            'severity': ProblemSeverity.LOW
        },
        'magic_number': {
            'pattern': r'(?<!["\'])\b\d{2,}\b(?!["\'])',
            'message': '发现魔法数字，建议使用常量',
            'severity': ProblemSeverity.LOW
        },
        'todo_comment': {
            'pattern': r'#\s*TODO|#\s*FIXME|#\s*HACK|#\s*XXX',
            'message': '发现待处理注释',
            'severity': ProblemSeverity.INFO
        },
        'empty_except': {
            'pattern': r'except\s*:\s*pass',
            'message': '空的异常处理，可能隐藏问题',
            'severity': ProblemSeverity.HIGH
        },
        'hardcoded_path': {
            'pattern': r'["\'][A-Za-z]:\\[^"\']+["\']',
            'message': '硬编码路径，建议使用配置',
            'severity': ProblemSeverity.MEDIUM
        },
    }
    
    SECURITY_PATTERNS = {
        'sql_injection_risk': {
            'pattern': r'execute\s*\(\s*["\'].*%s.*["\']',
            'message': '可能存在SQL注入风险',
            'severity': ProblemSeverity.CRITICAL
        },
        'eval_usage': {
            'pattern': r'\beval\s*\(',
            'message': '使用eval()可能存在安全风险',
            'severity': ProblemSeverity.HIGH
        },
        'hardcoded_password': {
            'pattern': r'(password|passwd|pwd)\s*=\s*["\'][^"\']+["\']',
            'message': '硬编码密码，存在安全风险',
            'severity': ProblemSeverity.CRITICAL
        },
        'debug_mode': {
            'pattern': r'DEBUG\s*=\s*True',
            'message': '调试模式可能在生产环境中启用',
            'severity': ProblemSeverity.HIGH
        },
    }
    
    PERFORMANCE_PATTERNS = {
        'nested_loop': {
            'pattern': r'for\s+\w+\s+in\s+.*:\s*\n\s*for\s+\w+\s+in\s+.*:',
            'message': '嵌套循环可能影响性能',
            'severity': ProblemSeverity.MEDIUM
        },
        'large_list_comprehension': {
            'pattern': r'\[[^\]]{200,}\]',
            'message': '大型列表推导式可能影响可读性',
            'severity': ProblemSeverity.LOW
        },
    }
    
    def __init__(self):
        self.logger = self._setup_logger()
        self.detected_problems: List[DetectedProblem] = []
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('ProblemDetector')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def detect_problems(self, target_path: str, 
                        problem_types: List[ProblemType] = None) -> List[DetectedProblem]:
        target = Path(target_path)
        problems = []
        
        if problem_types is None:
            problem_types = list(ProblemType)
        
        files_to_scan = []
        
        if target.is_file() and target.suffix == '.py':
            files_to_scan = [target]
        elif target.is_dir():
            files_to_scan = list(target.rglob('*.py'))
        
        for file_path in files_to_scan:
            try:
                file_problems = self._scan_file(file_path, problem_types)
                problems.extend(file_problems)
            except Exception as e:
                self.logger.error(f"扫描文件失败 {file_path}: {e}")
        
        self.detected_problems = problems
        self.logger.info(f"检测完成，发现 {len(problems)} 个问题")
        
        return problems
    
    def _scan_file(self, file_path: Path, problem_types: List[ProblemType]) -> List[DetectedProblem]:
        problems = []
        content = file_path.read_text(encoding='utf-8')
        lines = content.split('\n')
        
        if ProblemType.CODE_QUALITY in problem_types:
            problems.extend(self._detect_code_quality(file_path, content, lines))
        
        if ProblemType.SECURITY in problem_types:
            problems.extend(self._detect_security(file_path, content, lines))
        
        if ProblemType.PERFORMANCE in problem_types:
            problems.extend(self._detect_performance(file_path, content, lines))
        
        if ProblemType.DOCUMENTATION in problem_types:
            problems.extend(self._detect_documentation(file_path, content, lines))
        
        return problems
    
    def _detect_code_quality(self, file_path: Path, content: str, 
                             lines: List[str]) -> List[DetectedProblem]:
        problems = []
        
        for issue_name, config in self.CODE_QUALITY_PATTERNS.items():
            for match in re.finditer(config['pattern'], content, re.MULTILINE):
                line_num = content[:match.start()].count('\n') + 1
                
                problem = DetectedProblem(
                    problem_id=self._generate_problem_id('code_quality', issue_name, file_path, line_num),
                    problem_type=ProblemType.CODE_QUALITY,
                    severity=config['severity'],
                    title=f"代码质量问题: {issue_name}",
                    description=config['message'],
                    location=f"{file_path.name}:{line_num}",
                    file_path=str(file_path),
                    line_start=line_num,
                    line_end=line_num,
                    code_snippet=lines[line_num - 1][:100] if line_num <= len(lines) else "",
                    suggestion=self._get_suggestion('code_quality', issue_name)
                )
                problems.append(problem)
        
        return problems
    
    def _detect_security(self, file_path: Path, content: str, 
                         lines: List[str]) -> List[DetectedProblem]:
        problems = []
        
        for issue_name, config in self.SECURITY_PATTERNS.items():
            for match in re.finditer(config['pattern'], content, re.MULTILINE | re.IGNORECASE):
                line_num = content[:match.start()].count('\n') + 1
                
                problem = DetectedProblem(
                    problem_id=self._generate_problem_id('security', issue_name, file_path, line_num),
                    problem_type=ProblemType.SECURITY,
                    severity=config['severity'],
                    title=f"安全问题: {issue_name}",
                    description=config['message'],
                    location=f"{file_path.name}:{line_num}",
                    file_path=str(file_path),
                    line_start=line_num,
                    line_end=line_num,
                    code_snippet=lines[line_num - 1][:100] if line_num <= len(lines) else "",
                    suggestion=self._get_suggestion('security', issue_name)
                )
                problems.append(problem)
        
        return problems
    
    def _detect_performance(self, file_path: Path, content: str, 
                            lines: List[str]) -> List[DetectedProblem]:
        problems = []
        
        for issue_name, config in self.PERFORMANCE_PATTERNS.items():
            for match in re.finditer(config['pattern'], content, re.MULTILINE):
                line_num = content[:match.start()].count('\n') + 1
                
                problem = DetectedProblem(
                    problem_id=self._generate_problem_id('performance', issue_name, file_path, line_num),
                    problem_type=ProblemType.PERFORMANCE,
                    severity=config['severity'],
                    title=f"性能问题: {issue_name}",
                    description=config['message'],
                    location=f"{file_path.name}:{line_num}",
                    file_path=str(file_path),
                    line_start=line_num,
                    line_end=line_num,
                    code_snippet=lines[line_num - 1][:100] if line_num <= len(lines) else "",
                    suggestion=self._get_suggestion('performance', issue_name)
                )
                problems.append(problem)
        
        return problems
    
    def _detect_documentation(self, file_path: Path, content: str, 
                              lines: List[str]) -> List[DetectedProblem]:
        problems = []
        
        if not content.strip().startswith('#!/usr/bin/env python3') and \
           not content.strip().startswith('# -*- coding:'):
            pass
        
        functions = re.findall(r'def\s+(\w+)\s*\([^)]*\):', content)
        
        for func_name in functions:
            func_pattern = rf'def\s+{func_name}\s*\([^)]*\):\s*\n\s*"""'
            if not re.search(func_pattern, content):
                func_match = re.search(rf'def\s+{func_name}\s*\([^)]*\):', content)
                if func_match:
                    line_num = content[:func_match.start()].count('\n') + 1
                    
                    problem = DetectedProblem(
                        problem_id=self._generate_problem_id('documentation', 'missing_docstring', file_path, line_num),
                        problem_type=ProblemType.DOCUMENTATION,
                        severity=ProblemSeverity.LOW,
                        title=f"缺少文档字符串: {func_name}",
                        description=f"函数 '{func_name}' 缺少文档字符串",
                        location=f"{file_path.name}:{line_num}",
                        file_path=str(file_path),
                        line_start=line_num,
                        line_end=line_num,
                        code_snippet=f"def {func_name}(...):",
                        suggestion="添加文档字符串说明函数功能、参数和返回值"
                    )
                    problems.append(problem)
        
        return problems
    
    def _generate_problem_id(self, category: str, issue_type: str, 
                             file_path: Path, line_num: int) -> str:
        unique_str = f"{category}_{issue_type}_{file_path}_{line_num}"
        hash_val = hashlib.md5(unique_str.encode()).hexdigest()[:8]
        return f"PROB-{category[:3].upper()}-{hash_val}"
    
    def _get_suggestion(self, category: str, issue_type: str) -> str:
        suggestions = {
            'code_quality': {
                'long_function': '将函数拆分为多个较小的函数，每个函数只做一件事',
                'complex_condition': '使用提取方法或策略模式简化条件逻辑',
                'magic_number': '定义有意义的常量替代魔法数字',
                'todo_comment': '创建任务跟踪并解决待办事项',
                'empty_except': '至少记录异常信息，或处理特定异常类型',
                'hardcoded_path': '使用配置文件或环境变量管理路径',
            },
            'security': {
                'sql_injection_risk': '使用参数化查询替代字符串拼接',
                'eval_usage': '使用更安全的替代方案，如ast.literal_eval',
                'hardcoded_password': '使用环境变量或密钥管理服务',
                'debug_mode': '确保生产环境禁用调试模式',
            },
            'performance': {
                'nested_loop': '考虑使用更高效的数据结构或算法',
                'large_list_comprehension': '使用普通循环提高可读性',
            }
        }
        
        return suggestions.get(category, {}).get(issue_type, '请检查并修复此问题')


class IterationPlanner:
    """迭代计划生成器"""
    
    def __init__(self):
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('IterationPlanner')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def generate_plan(self, problems: List[DetectedProblem], 
                      plan_name: str = "自动迭代计划") -> IterationPlan:
        self.logger.info(f"开始生成迭代计划，问题数: {len(problems)}")
        
        problems_by_type = defaultdict(list)
        for problem in problems:
            problems_by_type[problem.problem_type].append(problem)
        
        problems_by_severity = defaultdict(list)
        for problem in problems:
            problems_by_severity[problem.severity].append(problem)
        
        tasks = self._create_tasks(problems, problems_by_type)
        
        critical_count = len(problems_by_severity.get(ProblemSeverity.CRITICAL, []))
        high_count = len(problems_by_severity.get(ProblemSeverity.HIGH, []))
        medium_count = len(problems_by_severity.get(ProblemSeverity.MEDIUM, []))
        low_count = len(problems_by_severity.get(ProblemSeverity.LOW, []))
        
        plan = IterationPlan(
            plan_id=f"PLAN-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            name=plan_name,
            description=f"基于 {len(problems)} 个检测问题生成的迭代计划",
            tasks=tasks,
            total_problems=len(problems),
            critical_count=critical_count,
            high_count=high_count,
            medium_count=medium_count,
            low_count=low_count
        )
        
        self.logger.info(f"迭代计划生成完成，任务数: {len(tasks)}")
        return plan
    
    def _create_tasks(self, problems: List[DetectedProblem], 
                      problems_by_type: Dict) -> List[IterationTask]:
        tasks = []
        
        critical_problems = [p for p in problems if p.severity == ProblemSeverity.CRITICAL]
        if critical_problems:
            task = self._create_task(
                "修复关键问题",
                "修复所有关键级别的安全和严重问题",
                critical_problems,
                IterationPriority.IMMEDIATE
            )
            tasks.append(task)
        
        high_problems = [p for p in problems if p.severity == ProblemSeverity.HIGH]
        if high_problems:
            task = self._create_task(
                "修复高优先级问题",
                "修复所有高级别问题",
                high_problems,
                IterationPriority.HIGH
            )
            tasks.append(task)
        
        for problem_type, type_problems in problems_by_type.items():
            medium_low = [p for p in type_problems 
                         if p.severity in [ProblemSeverity.MEDIUM, ProblemSeverity.LOW]]
            
            if medium_low:
                task = self._create_task(
                    f"改进{problem_type.value}",
                    f"改进{problem_type.value}相关问题",
                    medium_low,
                    IterationPriority.NORMAL
                )
                tasks.append(task)
        
        info_problems = [p for p in problems if p.severity == ProblemSeverity.INFO]
        if info_problems:
            task = self._create_task(
                "处理信息级问题",
                "处理TODO注释和信息级提示",
                info_problems,
                IterationPriority.LOW
            )
            tasks.append(task)
        
        return tasks
    
    def _create_task(self, title: str, description: str, 
                     problems: List[DetectedProblem], 
                     priority: IterationPriority) -> IterationTask:
        steps = []
        
        for i, problem in enumerate(problems[:10], 1):
            steps.append({
                'step_id': f"STEP-{i}",
                'description': f"修复: {problem.title}",
                'file_path': problem.file_path,
                'line_start': problem.line_start,
                'suggestion': problem.suggestion,
                'status': 'pending'
            })
        
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
            steps=steps
        )
    
    def prioritize_tasks(self, tasks: List[IterationTask]) -> List[IterationTask]:
        priority_order = {
            IterationPriority.IMMEDIATE: 0,
            IterationPriority.HIGH: 1,
            IterationPriority.NORMAL: 2,
            IterationPriority.LOW: 3,
            IterationPriority.SCHEDULED: 4
        }
        
        return sorted(tasks, key=lambda t: priority_order.get(t.priority, 5))


class SelfIterationTrigger:
    """自迭代触发器"""
    
    DEFAULT_CONDITIONS = [
        {
            'name': 'critical_issues',
            'type': 'problem_count',
            'threshold': 1,
            'severity_filter': 'critical'
        },
        {
            'name': 'high_issues',
            'type': 'problem_count',
            'threshold': 5,
            'severity_filter': 'high'
        },
        {
            'name': 'security_issues',
            'type': 'problem_count',
            'threshold': 1,
            'type_filter': 'security'
        },
        {
            'name': 'quality_score',
            'type': 'quality_score',
            'threshold': 0.6
        },
    ]
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path
        self.conditions: List[TriggerCondition] = []
        self.logger = self._setup_logger()
        self._load_conditions()
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('SelfIterationTrigger')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _load_conditions(self) -> None:
        if self.config_path and Path(self.config_path).exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    conditions_data = config.get('trigger_conditions', [])
            except Exception:
                conditions_data = self.DEFAULT_CONDITIONS
        else:
            conditions_data = self.DEFAULT_CONDITIONS
        
        for cond_data in conditions_data:
            condition = TriggerCondition(
                condition_id=f"COND-{cond_data['name'].upper()}",
                name=cond_data['name'],
                description=cond_data.get('description', ''),
                condition_type=cond_data['type'],
                threshold=cond_data['threshold'],
                current_value=0.0,
                is_triggered=False
            )
            self.conditions.append(condition)
    
    def check_triggers(self, problems: List[DetectedProblem], 
                       quality_score: float = None) -> List[TriggerCondition]:
        triggered = []
        
        for condition in self.conditions:
            condition.last_checked = datetime.now().isoformat()
            
            if condition.condition_type == 'problem_count':
                severity_filter = getattr(condition, 'severity_filter', None)
                type_filter = getattr(condition, 'type_filter', None)
                
                filtered = problems
                if severity_filter:
                    filtered = [p for p in filtered if p.severity.value == severity_filter]
                if type_filter:
                    filtered = [p for p in filtered if p.problem_type.value == type_filter]
                
                condition.current_value = len(filtered)
                condition.is_triggered = condition.current_value >= condition.threshold
            
            elif condition.condition_type == 'quality_score' and quality_score is not None:
                condition.current_value = quality_score
                condition.is_triggered = condition.current_value < condition.threshold
            
            if condition.is_triggered:
                triggered.append(condition)
                self.logger.warning(f"触发条件满足: {condition.name}")
        
        return triggered
    
    def should_trigger_iteration(self, problems: List[DetectedProblem], 
                                  quality_score: float = None) -> Tuple[bool, str]:
        triggered = self.check_triggers(problems, quality_score)
        
        if not triggered:
            return False, "无触发条件满足"
        
        critical_triggered = [c for c in triggered if 'critical' in c.name.lower()]
        if critical_triggered:
            return True, f"发现关键问题，需要立即迭代"
        
        security_triggered = [c for c in triggered if 'security' in c.name.lower()]
        if security_triggered:
            return True, f"发现安全问题，需要迭代修复"
        
        return True, f"{len(triggered)} 个触发条件满足，建议进行迭代"
    
    def get_trigger_report(self) -> str:
        lines = [
            "# 自迭代触发报告",
            "",
            f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## 触发条件状态",
            "",
            "| 条件名称 | 阈值 | 当前值 | 状态 |",
            "|----------|------|--------|------|",
        ]
        
        for condition in self.conditions:
            status = "🔴 触发" if condition.is_triggered else "🟢 正常"
            lines.append(
                f"| {condition.name} | {condition.threshold} | "
                f"{condition.current_value} | {status} |"
            )
        
        return '\n'.join(lines)


class SelfIterationOrchestrator:
    """自迭代编排器"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.storage_path = self.project_root / ".trae" / "skills" / "sanliu" / "iteration"
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.detector = ProblemDetector()
        self.planner = IterationPlanner()
        self.trigger = SelfIterationTrigger()
        
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('SelfIterationOrchestrator')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def run_iteration_cycle(self, target_path: str = None, 
                            auto_trigger: bool = True) -> Dict[str, Any]:
        self.logger.info("开始自迭代周期")
        
        if target_path is None:
            target_path = str(self.project_root)
        
        problems = self.detector.detect_problems(target_path)
        
        quality_score = self._calculate_quality_score(problems)
        
        should_trigger, trigger_message = self.trigger.should_trigger_iteration(
            problems, quality_score
        )
        
        result = {
            'timestamp': datetime.now().isoformat(),
            'target_path': target_path,
            'problems_detected': len(problems),
            'quality_score': quality_score,
            'should_trigger': should_trigger,
            'trigger_message': trigger_message,
            'plan': None,
            'problems': [asdict(p) for p in problems[:20]]
        }
        
        if should_trigger or not auto_trigger:
            plan = self.planner.generate_plan(problems)
            result['plan'] = asdict(plan)
            
            self._save_plan(plan)
            
            self.logger.info(f"迭代计划已生成: {plan.plan_id}")
        
        self._save_iteration_result(result)
        
        return result
    
    def _calculate_quality_score(self, problems: List[DetectedProblem]) -> float:
        if not problems:
            return 1.0
        
        severity_weights = {
            ProblemSeverity.CRITICAL: 0.5,
            ProblemSeverity.HIGH: 0.3,
            ProblemSeverity.MEDIUM: 0.15,
            ProblemSeverity.LOW: 0.05,
            ProblemSeverity.INFO: 0.0
        }
        
        total_penalty = sum(severity_weights.get(p.severity, 0) for p in problems)
        
        score = max(0.0, 1.0 - total_penalty)
        
        return round(score, 2)
    
    def _save_plan(self, plan: IterationPlan) -> None:
        plan_file = self.storage_path / f"plan_{plan.plan_id}.json"
        plan_file.write_text(json.dumps(asdict(plan), ensure_ascii=False, indent=2), 
                            encoding='utf-8')
    
    def _save_iteration_result(self, result: Dict[str, Any]) -> None:
        result_file = self.storage_path / f"iteration_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
        result_file.write_text(json.dumps(result, ensure_ascii=False, indent=2), 
                              encoding='utf-8')
    
    def get_iteration_status(self) -> Dict[str, Any]:
        plans = list(self.storage_path.glob("plan_*.json"))
        
        latest_plan = None
        if plans:
            latest_plan_file = max(plans, key=lambda p: p.stat().st_mtime)
            latest_plan = json.loads(latest_plan_file.read_text(encoding='utf-8'))
        
        return {
            'total_plans': len(plans),
            'latest_plan': latest_plan,
            'trigger_conditions': [asdict(c) for c in self.trigger.conditions]
        }
    
    def generate_iteration_report(self) -> str:
        status = self.get_iteration_status()
        
        lines = [
            "# 自迭代状态报告",
            "",
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## 触发条件状态",
            "",
        ]
        
        for condition in self.trigger.conditions:
            status_text = "🔴 触发" if condition.is_triggered else "🟢 正常"
            lines.append(f"- **{condition.name}**: {status_text}")
            lines.append(f"  - 阈值: {condition.threshold}")
            lines.append(f"  - 当前值: {condition.current_value}")
            lines.append("")
        
        if status['latest_plan']:
            plan = status['latest_plan']
            lines.extend([
                "## 最新迭代计划",
                "",
                f"- **计划ID**: {plan['plan_id']}",
                f"- **名称**: {plan['name']}",
                f"- **问题总数**: {plan['total_problems']}",
                f"- **关键问题**: {plan['critical_count']}",
                f"- **高级问题**: {plan['high_count']}",
                f"- **中级问题**: {plan['medium_count']}",
                f"- **低级问题**: {plan['low_count']}",
                f"- **任务数**: {len(plan['tasks'])}",
                "",
            ])
            
            lines.append("### 任务列表")
            lines.append("")
            
            for task in plan['tasks']:
                lines.append(f"#### {task['title']}")
                lines.append(f"- 优先级: {task['priority']}")
                lines.append(f"- 状态: {task['status']}")
                lines.append(f"- 涉及问题: {len(task['problem_ids'])}")
                lines.append("")
        
        return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description='自迭代智能触发脚本')
    
    parser.add_argument('--project-root', '-p', default='.', help='项目根目录')
    parser.add_argument('--target', '-t', help='检测目标路径')
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    detect_parser = subparsers.add_parser('detect', help='检测问题')
    detect_parser.add_argument('--types', help='问题类型(逗号分隔)')
    detect_parser.add_argument('--output', '-o', help='输出文件路径')
    
    plan_parser = subparsers.add_parser('plan', help='生成迭代计划')
    plan_parser.add_argument('--name', default='自动迭代计划', help='计划名称')
    plan_parser.add_argument('--output', '-o', help='输出文件路径')
    
    trigger_parser = subparsers.add_parser('trigger', help='检查触发条件')
    
    cycle_parser = subparsers.add_parser('cycle', help='执行完整迭代周期')
    cycle_parser.add_argument('--auto', action='store_true', help='自动触发模式')
    
    status_parser = subparsers.add_parser('status', help='获取迭代状态')
    
    report_parser = subparsers.add_parser('report', help='生成迭代报告')
    report_parser.add_argument('--output', '-o', help='输出文件路径')
    
    args = parser.parse_args()
    
    orchestrator = SelfIterationOrchestrator(args.project_root)
    
    if args.command == 'detect':
        target = args.target or args.project_root
        
        types = None
        if args.types:
            types = [ProblemType(t.strip()) for t in args.types.split(',')]
        
        problems = orchestrator.detector.detect_problems(target, types)
        
        output = {
            'total_problems': len(problems),
            'problems': [asdict(p) for p in problems]
        }
        
        if args.output:
            Path(args.output).write_text(json.dumps(output, ensure_ascii=False, indent=2), 
                                         encoding='utf-8')
            print(f"检测结果已保存: {args.output}")
        else:
            print(f"\n发现 {len(problems)} 个问题:")
            for p in problems[:20]:
                print(f"  [{p.severity.value}] {p.title} - {p.location}")
    
    elif args.command == 'plan':
        target = args.target or args.project_root
        problems = orchestrator.detector.detect_problems(target)
        plan = orchestrator.planner.generate_plan(problems, args.name)
        
        if args.output:
            Path(args.output).write_text(json.dumps(asdict(plan), ensure_ascii=False, indent=2), 
                                         encoding='utf-8')
            print(f"计划已保存: {args.output}")
        else:
            print(f"\n迭代计划: {plan.name}")
            print(f"任务数: {len(plan.tasks)}")
            for task in plan.tasks:
                print(f"  - {task.title} ({task.priority.value})")
    
    elif args.command == 'trigger':
        target = args.target or args.project_root
        problems = orchestrator.detector.detect_problems(target)
        triggered = orchestrator.trigger.check_triggers(problems)
        
        print("\n触发条件状态:")
        for condition in orchestrator.trigger.conditions:
            status = "🔴 触发" if condition.is_triggered else "🟢 正常"
            print(f"  {condition.name}: {status} (阈值: {condition.threshold}, 当前: {condition.current_value})")
    
    elif args.command == 'cycle':
        result = orchestrator.run_iteration_cycle(args.target, args.auto)
        
        print(f"\n迭代周期完成:")
        print(f"  问题数: {result['problems_detected']}")
        print(f"  质量分: {result['quality_score']}")
        print(f"  触发状态: {result['trigger_message']}")
        
        if result['plan']:
            print(f"  计划ID: {result['plan']['plan_id']}")
    
    elif args.command == 'status':
        status = orchestrator.get_iteration_status()
        print(json.dumps(status, ensure_ascii=False, indent=2))
    
    elif args.command == 'report':
        report = orchestrator.generate_iteration_report()
        
        if args.output:
            Path(args.output).write_text(report, encoding='utf-8')
            print(f"报告已保存: {args.output}")
        else:
            print(report)
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
