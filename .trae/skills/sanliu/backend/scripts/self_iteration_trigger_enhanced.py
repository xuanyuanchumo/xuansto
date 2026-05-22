#!/usr/bin/env python3
"""
自迭代智能触发增强脚本
实现智能问题检测、迭代计划生成、自动触发决策

功能:
- 智能问题检测（代码质量、测试覆盖率、性能指标）
- 迭代计划生成
- 自动触发决策
- 多维度指标分析
- 迭代历史追踪
"""

import os
import sys
import json
import ast
import re
import argparse
import logging
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from version_iterator import (
    VersionIterator,
    IterationTriggerType,
    VersionBumpType,
    ChangeEntry,
    ChangeType
)


class IssueSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class IssueCategory(Enum):
    CODE_QUALITY = "code_quality"
    TEST_COVERAGE = "test_coverage"
    PERFORMANCE = "performance"
    SECURITY = "security"
    MAINTAINABILITY = "maintainability"
    DOCUMENTATION = "documentation"
    DEPENDENCY = "dependency"
    ARCHITECTURE = "architecture"


class IterationPriority(Enum):
    URGENT = "urgent"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    DEFERRED = "deferred"


@dataclass
class DetectedIssue:
    issue_id: str
    category: IssueCategory
    severity: IssueSeverity
    title: str
    description: str
    location: str
    suggestion: str
    impact_score: float
    detected_at: str
    metrics: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metrics is None:
            self.metrics = {}
        if not self.detected_at:
            self.detected_at = datetime.now().isoformat()


@dataclass
class IterationPlan:
    plan_id: str
    version_bump_type: VersionBumpType
    priority: IterationPriority
    issues: List[DetectedIssue]
    actions: List[Dict[str, Any]]
    estimated_effort: str
    created_at: str
    status: str = "pending"
    dependencies: List[str] = None
    milestones: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.milestones is None:
            self.milestones = []
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


@dataclass
class QualityMetrics:
    code_quality_score: float = 1.0
    test_coverage: float = 0.0
    test_pass_rate: float = 1.0
    performance_score: float = 1.0
    security_score: float = 1.0
    maintainability_index: float = 1.0
    documentation_coverage: float = 0.0
    dependency_health: float = 1.0
    complexity_score: float = 1.0
    duplication_ratio: float = 0.0
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class IntelligentIssueDetector:
    """智能问题检测器"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.logger = self._setup_logger()
        self.issue_counter = 0
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('IntelligentIssueDetector')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _generate_issue_id(self) -> str:
        self.issue_counter += 1
        return f"ISSUE-{datetime.now().strftime('%Y%m%d%H%M%S')}-{self.issue_counter:04d}"
    
    def detect_code_quality_issues(self) -> List[DetectedIssue]:
        """检测代码质量问题"""
        issues = []
        
        for py_file in self.project_root.rglob("*.py"):
            if "__pycache__" in str(py_file) or ".venv" in str(py_file):
                continue
            
            try:
                issues.extend(self._analyze_python_file(py_file))
            except Exception as e:
                self.logger.warning(f"分析文件失败 {py_file}: {e}")
        
        return issues
    
    def _analyze_python_file(self, file_path: Path) -> List[DetectedIssue]:
        """分析Python文件"""
        issues = []
        
        try:
            content = file_path.read_text(encoding='utf-8')
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    complexity = self._calculate_complexity(node)
                    if complexity > 10:
                        issues.append(DetectedIssue(
                            issue_id=self._generate_issue_id(),
                            category=IssueCategory.CODE_QUALITY,
                            severity=IssueSeverity.HIGH if complexity > 15 else IssueSeverity.MEDIUM,
                            title=f"高复杂度函数: {node.name}",
                            description=f"函数 '{node.name}' 的圈复杂度为 {complexity}，建议重构",
                            location=f"{file_path}:{node.lineno}",
                            suggestion="考虑将函数拆分为更小的函数，降低复杂度",
                            impact_score=min(complexity / 20, 1.0),
                            metrics={"complexity": complexity, "function": node.name}
                        ))
                
                if isinstance(node, ast.FunctionDef):
                    if not node.body or (len(node.body) == 1 and isinstance(node.body[0], ast.Pass)):
                        issues.append(DetectedIssue(
                            issue_id=self._generate_issue_id(),
                            category=IssueCategory.CODE_QUALITY,
                            severity=IssueSeverity.LOW,
                            title=f"空函数: {node.name}",
                            description=f"函数 '{node.name}' 为空实现",
                            location=f"{file_path}:{node.lineno}",
                            suggestion="实现函数逻辑或删除空函数",
                            impact_score=0.2,
                            metrics={"function": node.name}
                        ))
            
            if len(content) > 1000 and content.count('\n\n') < 5:
                issues.append(DetectedIssue(
                    issue_id=self._generate_issue_id(),
                    category=IssueCategory.MAINTAINABILITY,
                    severity=IssueSeverity.LOW,
                    title="文件结构需要优化",
                    description=f"文件 {file_path.name} 较长但缺少分段注释",
                    location=str(file_path),
                    suggestion="添加模块级注释和分段标记以提高可读性",
                    impact_score=0.3
                ))
            
            if 'TODO' in content or 'FIXME' in content or 'XXX' in content:
                todo_count = content.count('TODO') + content.count('FIXME') + content.count('XXX')
                if todo_count > 3:
                    issues.append(DetectedIssue(
                        issue_id=self._generate_issue_id(),
                        category=IssueCategory.MAINTAINABILITY,
                        severity=IssueSeverity.MEDIUM,
                        title=f"待办事项过多",
                        description=f"文件 {file_path.name} 包含 {todo_count} 个待办标记",
                        location=str(file_path),
                        suggestion="处理待办事项或创建任务跟踪",
                        impact_score=0.4,
                        metrics={"todo_count": todo_count}
                    ))
        
        except SyntaxError:
            issues.append(DetectedIssue(
                issue_id=self._generate_issue_id(),
                category=IssueCategory.CODE_QUALITY,
                severity=IssueSeverity.CRITICAL,
                title="语法错误",
                description=f"文件 {file_path.name} 存在语法错误",
                location=str(file_path),
                suggestion="修复语法错误",
                impact_score=1.0
            ))
        
        return issues
    
    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """计算圈复杂度"""
        complexity = 1
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity
    
    def detect_test_coverage_issues(self) -> List[DetectedIssue]:
        """检测测试覆盖率问题"""
        issues = []
        
        coverage_file = self.project_root / "coverage.json"
        if coverage_file.exists():
            try:
                with open(coverage_file, 'r', encoding='utf-8') as f:
                    coverage_data = json.load(f)
                
                totals = coverage_data.get('totals', {})
                coverage_percent = totals.get('percent_covered', 0)
                
                if coverage_percent < 50:
                    issues.append(DetectedIssue(
                        issue_id=self._generate_issue_id(),
                        category=IssueCategory.TEST_COVERAGE,
                        severity=IssueSeverity.CRITICAL,
                        title="测试覆盖率过低",
                        description=f"当前测试覆盖率仅为 {coverage_percent:.1f}%",
                        location="项目全局",
                        suggestion="增加单元测试，目标覆盖率至少达到80%",
                        impact_score=1.0 - coverage_percent / 100,
                        metrics={"coverage": coverage_percent}
                    ))
                elif coverage_percent < 80:
                    issues.append(DetectedIssue(
                        issue_id=self._generate_issue_id(),
                        category=IssueCategory.TEST_COVERAGE,
                        severity=IssueSeverity.HIGH,
                        title="测试覆盖率不足",
                        description=f"当前测试覆盖率为 {coverage_percent:.1f}%",
                        location="项目全局",
                        suggestion="继续增加测试用例，目标覆盖率80%以上",
                        impact_score=0.8 - coverage_percent / 100,
                        metrics={"coverage": coverage_percent}
                    ))
                
                for file_path, file_data in coverage_data.get('files', {}).items():
                    file_coverage = file_data.get('summary', {}).get('percent_covered', 0)
                    if file_coverage < 30 and not '__pycache__' in file_path:
                        issues.append(DetectedIssue(
                            issue_id=self._generate_issue_id(),
                            category=IssueCategory.TEST_COVERAGE,
                            severity=IssueSeverity.MEDIUM,
                            title=f"文件测试覆盖不足: {Path(file_path).name}",
                            description=f"文件测试覆盖率仅为 {file_coverage:.1f}%",
                            location=file_path,
                            suggestion="为该文件添加更多测试用例",
                            impact_score=0.5,
                            metrics={"coverage": file_coverage, "file": file_path}
                        ))
            
            except Exception as e:
                self.logger.error(f"解析覆盖率文件失败: {e}")
        else:
            issues.append(DetectedIssue(
                issue_id=self._generate_issue_id(),
                category=IssueCategory.TEST_COVERAGE,
                severity=IssueSeverity.HIGH,
                title="缺少测试覆盖率报告",
                description="未找到 coverage.json 文件",
                location="项目全局",
                suggestion="运行测试并生成覆盖率报告",
                impact_score=0.7
            ))
        
        return issues
    
    def detect_performance_issues(self) -> List[DetectedIssue]:
        """检测性能问题"""
        issues = []
        
        for py_file in self.project_root.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            
            try:
                content = py_file.read_text(encoding='utf-8')
                
                if re.search(r'for\s+\w+\s+in\s+range\(\s*len\(', content):
                    issues.append(DetectedIssue(
                        issue_id=self._generate_issue_id(),
                        category=IssueCategory.PERFORMANCE,
                        severity=IssueSeverity.LOW,
                        title="低效的循环模式",
                        description="发现使用 range(len()) 的循环模式",
                        location=str(py_file),
                        suggestion="考虑使用 enumerate() 或直接迭代",
                        impact_score=0.3
                    ))
                
                if content.count('import ') > 20:
                    issues.append(DetectedIssue(
                        issue_id=self._generate_issue_id(),
                        category=IssueCategory.PERFORMANCE,
                        severity=IssueSeverity.LOW,
                        title="导入过多",
                        description=f"文件 {py_file.name} 导入了 {content.count('import ')} 个模块",
                        location=str(py_file),
                        suggestion="检查是否有未使用的导入，考虑延迟导入",
                        impact_score=0.2,
                        metrics={"import_count": content.count('import ')}
                    ))
                
                if re.search(r'\+\s*["\']', content) and content.count('+ "') + content.count("+ '") > 5:
                    issues.append(DetectedIssue(
                        issue_id=self._generate_issue_id(),
                        category=IssueCategory.PERFORMANCE,
                        severity=IssueSeverity.LOW,
                        title="字符串拼接效率问题",
                        description="发现多次使用 + 进行字符串拼接",
                        location=str(py_file),
                        suggestion="对于大量拼接，考虑使用 join() 或 f-string",
                        impact_score=0.2
                    ))
            
            except Exception:
                continue
        
        return issues
    
    def detect_security_issues(self) -> List[DetectedIssue]:
        """检测安全问题"""
        issues = []
        
        security_patterns = [
            (r'eval\s*\(', "使用 eval() 可能存在代码注入风险", IssueSeverity.CRITICAL),
            (r'exec\s*\(', "使用 exec() 可能存在代码注入风险", IssueSeverity.CRITICAL),
            (r'__import__\s*\(', "动态导入可能存在安全风险", IssueSeverity.HIGH),
            (r'subprocess\..*shell\s*=\s*True', "shell=True 可能存在命令注入风险", IssueSeverity.CRITICAL),
            (r'pickle\.loads?\s*\(', "pickle 反序列化可能存在安全风险", IssueSeverity.HIGH),
            (r'password\s*=\s*["\'][^"\']+["\']', "硬编码密码", IssueSeverity.CRITICAL),
            (r'api_key\s*=\s*["\'][^"\']+["\']', "硬编码API密钥", IssueSeverity.CRITICAL),
            (r'secret\s*=\s*["\'][^"\']+["\']', "硬编码密钥", IssueSeverity.HIGH),
        ]
        
        for py_file in self.project_root.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            
            try:
                content = py_file.read_text(encoding='utf-8')
                
                for pattern, message, severity in security_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        issues.append(DetectedIssue(
                            issue_id=self._generate_issue_id(),
                            category=IssueCategory.SECURITY,
                            severity=severity,
                            title="安全风险检测",
                            description=message,
                            location=f"{py_file}:{line_num}",
                            suggestion="审查并修复安全风险代码",
                            impact_score=1.0 if severity == IssueSeverity.CRITICAL else 0.8,
                            metrics={"pattern": pattern}
                        ))
            
            except Exception:
                continue
        
        return issues
    
    def detect_dependency_issues(self) -> List[DetectedIssue]:
        """检测依赖问题"""
        issues = []
        
        requirements_file = self.project_root / "requirements.txt"
        if requirements_file.exists():
            try:
                content = requirements_file.read_text(encoding='utf-8')
                lines = [l.strip() for l in content.split('\n') if l.strip() and not l.startswith('#')]
                
                unpinned = [l for l in lines if '==' not in l and not l.startswith('-')]
                if unpinned:
                    issues.append(DetectedIssue(
                        issue_id=self._generate_issue_id(),
                        category=IssueCategory.DEPENDENCY,
                        severity=IssueSeverity.MEDIUM,
                        title="未固定版本的依赖",
                        description=f"发现 {len(unpinned)} 个未固定版本的依赖",
                        location="requirements.txt",
                        suggestion="为所有依赖指定具体版本号",
                        impact_score=0.5,
                        metrics={"unpinned": unpinned}
                    ))
            
            except Exception:
                pass
        
        package_json = self.project_root / "package.json"
        if package_json.exists():
            try:
                with open(package_json, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                deps = {**data.get('dependencies', {}), **data.get('devDependencies', {})}
                outdated = [k for k, v in deps.items() if v.startswith('^') or v.startswith('~')]
                
                if len(deps) > 50:
                    issues.append(DetectedIssue(
                        issue_id=self._generate_issue_id(),
                        category=IssueCategory.DEPENDENCY,
                        severity=IssueSeverity.LOW,
                        title="依赖数量较多",
                        description=f"项目依赖了 {len(deps)} 个包",
                        location="package.json",
                        suggestion="检查是否有未使用的依赖",
                        impact_score=0.3,
                        metrics={"dep_count": len(deps)}
                    ))
            
            except Exception:
                pass
        
        return issues
    
    def detect_all_issues(self) -> List[DetectedIssue]:
        """检测所有问题"""
        all_issues = []
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(self.detect_code_quality_issues): "code_quality",
                executor.submit(self.detect_test_coverage_issues): "test_coverage",
                executor.submit(self.detect_performance_issues): "performance",
                executor.submit(self.detect_security_issues): "security",
                executor.submit(self.detect_dependency_issues): "dependency"
            }
            
            for future in as_completed(futures):
                category = futures[future]
                try:
                    issues = future.result()
                    all_issues.extend(issues)
                    self.logger.info(f"检测到 {len(issues)} 个 {category} 问题")
                except Exception as e:
                    self.logger.error(f"检测 {category} 问题失败: {e}")
        
        return all_issues


class IterationPlanGenerator:
    """迭代计划生成器"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.logger = self._setup_logger()
        self.plan_counter = 0
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('IterationPlanGenerator')
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
    
    def generate_plan(self, issues: List[DetectedIssue]) -> IterationPlan:
        """生成迭代计划"""
        severity_weights = {
            IssueSeverity.CRITICAL: 1.0,
            IssueSeverity.HIGH: 0.7,
            IssueSeverity.MEDIUM: 0.4,
            IssueSeverity.LOW: 0.2,
            IssueSeverity.INFO: 0.1
        }
        
        category_weights = {
            IssueCategory.SECURITY: 1.0,
            IssueCategory.CODE_QUALITY: 0.8,
            IssueCategory.TEST_COVERAGE: 0.7,
            IssueCategory.PERFORMANCE: 0.6,
            IssueCategory.MAINTAINABILITY: 0.5,
            IssueCategory.DEPENDENCY: 0.4,
            IssueCategory.DOCUMENTATION: 0.3,
            IssueCategory.ARCHITECTURE: 0.6
        }
        
        total_impact = sum(
            issue.impact_score * severity_weights.get(issue.severity, 0.5) * 
            category_weights.get(issue.category, 0.5)
            for issue in issues
        )
        
        critical_issues = [i for i in issues if i.severity == IssueSeverity.CRITICAL]
        high_issues = [i for i in issues if i.severity == IssueSeverity.HIGH]
        
        if critical_issues:
            priority = IterationPriority.URGENT
            version_bump = VersionBumpType.PATCH
        elif high_issues or total_impact > 5:
            priority = IterationPriority.HIGH
            version_bump = VersionBumpType.PATCH
        elif total_impact > 2:
            priority = IterationPriority.MEDIUM
            version_bump = VersionBumpType.PATCH
        elif total_impact > 0.5:
            priority = IterationPriority.LOW
            version_bump = VersionBumpType.PATCH
        else:
            priority = IterationPriority.DEFERRED
            version_bump = VersionBumpType.BUILD
        
        actions = self._generate_actions(issues)
        
        effort_hours = len(critical_issues) * 4 + len(high_issues) * 2 + len(issues) * 0.5
        if effort_hours < 4:
            estimated_effort = f"{effort_hours:.1f} 小时"
        elif effort_hours < 40:
            estimated_effort = f"{effort_hours/8:.1f} 人天"
        else:
            estimated_effort = f"{effort_hours/40:.1f} 人周"
        
        milestones = self._generate_milestones(issues, actions)
        
        plan = IterationPlan(
            plan_id=self._generate_plan_id(),
            version_bump_type=version_bump,
            priority=priority,
            issues=issues,
            actions=actions,
            estimated_effort=estimated_effort,
            milestones=milestones
        )
        
        return plan
    
    def _generate_actions(self, issues: List[DetectedIssue]) -> List[Dict[str, Any]]:
        """生成行动计划"""
        actions = []
        
        issues_by_category = defaultdict(list)
        for issue in issues:
            issues_by_category[issue.category].append(issue)
        
        if IssueCategory.SECURITY in issues_by_category:
            actions.append({
                "type": "security_fix",
                "priority": "critical",
                "description": "修复安全问题",
                "issues": [i.issue_id for i in issues_by_category[IssueCategory.SECURITY]],
                "estimated_time": f"{len(issues_by_category[IssueCategory.SECURITY]) * 2} 小时"
            })
        
        if IssueCategory.CODE_QUALITY in issues_by_category:
            actions.append({
                "type": "code_refactor",
                "priority": "high",
                "description": "代码质量优化",
                "issues": [i.issue_id for i in issues_by_category[IssueCategory.CODE_QUALITY]],
                "estimated_time": f"{len(issues_by_category[IssueCategory.CODE_QUALITY])} 小时"
            })
        
        if IssueCategory.TEST_COVERAGE in issues_by_category:
            actions.append({
                "type": "test_enhancement",
                "priority": "high",
                "description": "增加测试覆盖率",
                "issues": [i.issue_id for i in issues_by_category[IssueCategory.TEST_COVERAGE]],
                "estimated_time": f"{len(issues_by_category[IssueCategory.TEST_COVERAGE]) * 3} 小时"
            })
        
        if IssueCategory.PERFORMANCE in issues_by_category:
            actions.append({
                "type": "performance_optimization",
                "priority": "medium",
                "description": "性能优化",
                "issues": [i.issue_id for i in issues_by_category[IssueCategory.PERFORMANCE]],
                "estimated_time": f"{len(issues_by_category[IssueCategory.PERFORMANCE]) * 2} 小时"
            })
        
        if IssueCategory.DEPENDENCY in issues_by_category:
            actions.append({
                "type": "dependency_update",
                "priority": "medium",
                "description": "依赖管理优化",
                "issues": [i.issue_id for i in issues_by_category[IssueCategory.DEPENDENCY]],
                "estimated_time": f"{len(issues_by_category[IssueCategory.DEPENDENCY])} 小时"
            })
        
        return actions
    
    def _generate_milestones(self, issues: List[DetectedIssue], 
                            actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """生成里程碑"""
        milestones = []
        base_date = datetime.now()
        
        critical_issues = [i for i in issues if i.severity == IssueSeverity.CRITICAL]
        if critical_issues:
            milestones.append({
                "name": "紧急修复完成",
                "description": "完成所有关键问题的修复",
                "target_date": (base_date + timedelta(days=1)).strftime('%Y-%m-%d'),
                "issues": [i.issue_id for i in critical_issues],
                "status": "pending"
            })
        
        high_issues = [i for i in issues if i.severity == IssueSeverity.HIGH]
        if high_issues:
            milestones.append({
                "name": "高优先级问题解决",
                "description": "解决所有高优先级问题",
                "target_date": (base_date + timedelta(days=3)).strftime('%Y-%m-%d'),
                "issues": [i.issue_id for i in high_issues],
                "status": "pending"
            })
        
        milestones.append({
            "name": "迭代完成",
            "description": "完成本次迭代所有任务",
            "target_date": (base_date + timedelta(days=7)).strftime('%Y-%m-%d'),
            "issues": [i.issue_id for i in issues],
            "status": "pending"
        })
        
        return milestones


class EnhancedSelfIterationTrigger:
    """增强版自迭代触发器"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.iterator = VersionIterator(str(self.project_root))
        self.issue_detector = IntelligentIssueDetector(str(self.project_root))
        self.plan_generator = IterationPlanGenerator(str(self.project_root))
        self.logger = self._setup_logger()
        
        self.plans_dir = self.project_root / 'iteration_plans'
        self.plans_dir.mkdir(parents=True, exist_ok=True)
        
        self.metrics_file = self.project_root / 'metrics_history.json'
        self.trigger_history_file = self.project_root / 'trigger_history.json'
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('EnhancedSelfIterationTrigger')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def analyze_and_trigger(self, auto_execute: bool = False) -> Dict[str, Any]:
        """分析并触发迭代"""
        self.logger.info("开始智能分析...")
        
        self.logger.info("步骤1: 检测问题...")
        issues = self.issue_detector.detect_all_issues()
        
        self.logger.info("步骤2: 生成迭代计划...")
        plan = self.plan_generator.generate_plan(issues)
        
        self.logger.info("步骤3: 评估触发条件...")
        should_trigger = self._evaluate_trigger_conditions(issues, plan)
        
        result = {
            "timestamp": datetime.now().isoformat(),
            "issues_detected": len(issues),
            "issues_by_severity": {
                "critical": len([i for i in issues if i.severity == IssueSeverity.CRITICAL]),
                "high": len([i for i in issues if i.severity == IssueSeverity.HIGH]),
                "medium": len([i for i in issues if i.severity == IssueSeverity.MEDIUM]),
                "low": len([i for i in issues if i.severity == IssueSeverity.LOW])
            },
            "issues_by_category": {
                cat.value: len([i for i in issues if i.category == cat])
                for cat in IssueCategory
            },
            "plan": {
                "plan_id": plan.plan_id,
                "priority": plan.priority.value,
                "version_bump_type": plan.version_bump_type.value,
                "estimated_effort": plan.estimated_effort,
                "actions_count": len(plan.actions),
                "milestones_count": len(plan.milestones)
            },
            "should_trigger": should_trigger,
            "trigger_reason": self._get_trigger_reason(issues, plan) if should_trigger else None
        }
        
        self._save_plan(plan)
        
        if should_trigger and auto_execute:
            self.logger.info("触发条件满足，执行自迭代...")
            entry = self._execute_iteration(plan)
            if entry:
                result["iteration_executed"] = True
                result["new_version"] = entry.version
                self.logger.info(f"自迭代完成: {entry.previous_version} -> {entry.version}")
        
        self._save_trigger_history(result)
        
        return result
    
    def _evaluate_trigger_conditions(self, issues: List[DetectedIssue], 
                                     plan: IterationPlan) -> bool:
        """评估触发条件"""
        if plan.priority == IterationPriority.URGENT:
            return True
        
        if plan.priority == IterationPriority.HIGH:
            return True
        
        critical_count = len([i for i in issues if i.severity == IssueSeverity.CRITICAL])
        if critical_count > 0:
            return True
        
        high_count = len([i for i in issues if i.severity == IssueSeverity.HIGH])
        if high_count >= 3:
            return True
        
        security_issues = [i for i in issues if i.category == IssueCategory.SECURITY]
        if security_issues:
            return True
        
        return False
    
    def _get_trigger_reason(self, issues: List[DetectedIssue], 
                           plan: IterationPlan) -> str:
        """获取触发原因"""
        reasons = []
        
        critical_count = len([i for i in issues if i.severity == IssueSeverity.CRITICAL])
        if critical_count > 0:
            reasons.append(f"发现 {critical_count} 个关键问题")
        
        security_issues = [i for i in issues if i.category == IssueCategory.SECURITY]
        if security_issues:
            reasons.append(f"发现 {len(security_issues)} 个安全问题")
        
        if plan.priority == IterationPriority.URGENT:
            reasons.append("迭代优先级为紧急")
        elif plan.priority == IterationPriority.HIGH:
            reasons.append("迭代优先级为高")
        
        return "; ".join(reasons) if reasons else "综合评估需要迭代"
    
    def _execute_iteration(self, plan: IterationPlan):
        """执行迭代"""
        changes = []
        for issue in plan.issues[:10]:
            change_type = ChangeType.FIX
            if issue.category == IssueCategory.SECURITY:
                change_type = ChangeType.SECURITY
            elif issue.category == IssueCategory.PERFORMANCE:
                change_type = ChangeType.PERF
            
            changes.append(ChangeEntry(
                change_type=change_type,
                description=issue.title,
                scope=issue.category.value,
                impact_level=issue.severity.value
            ))
        
        return self.iterator.iterate(
            bump_type=plan.version_bump_type,
            changes=changes,
            notes=f"自动触发迭代 - 计划ID: {plan.plan_id}"
        )
    
    def _save_plan(self, plan: IterationPlan):
        """保存迭代计划"""
        plan_file = self.plans_dir / f"{plan.plan_id}.json"
        
        plan_data = {
            "plan_id": plan.plan_id,
            "version_bump_type": plan.version_bump_type.value,
            "priority": plan.priority.value,
            "estimated_effort": plan.estimated_effort,
            "created_at": plan.created_at,
            "status": plan.status,
            "issues": [
                {
                    "issue_id": i.issue_id,
                    "category": i.category.value,
                    "severity": i.severity.value,
                    "title": i.title,
                    "description": i.description,
                    "location": i.location,
                    "suggestion": i.suggestion,
                    "impact_score": i.impact_score
                }
                for i in plan.issues
            ],
            "actions": plan.actions,
            "milestones": plan.milestones
        }
        
        with open(plan_file, 'w', encoding='utf-8') as f:
            json.dump(plan_data, f, indent=2, ensure_ascii=False)
    
    def _save_trigger_history(self, result: Dict[str, Any]):
        """保存触发历史"""
        history = []
        
        if self.trigger_history_file.exists():
            try:
                with open(self.trigger_history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            except Exception:
                history = []
        
        history.append(result)
        
        if len(history) > 50:
            history = history[-50:]
        
        with open(self.trigger_history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    
    def get_plan(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """获取迭代计划"""
        plan_file = self.plans_dir / f"{plan_id}.json"
        
        if plan_file.exists():
            with open(plan_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return None
    
    def list_plans(self, limit: int = 10) -> List[Dict[str, Any]]:
        """列出迭代计划"""
        plans = []
        
        for plan_file in sorted(self.plans_dir.glob("PLAN-*.json"), reverse=True)[:limit]:
            try:
                with open(plan_file, 'r', encoding='utf-8') as f:
                    plans.append(json.load(f))
            except Exception:
                continue
        
        return plans
    
    def generate_report(self, output_path: Optional[str] = None) -> str:
        """生成报告"""
        trigger_history = []
        if self.trigger_history_file.exists():
            try:
                with open(self.trigger_history_file, 'r', encoding='utf-8') as f:
                    trigger_history = json.load(f)
            except Exception:
                pass
        
        recent_plans = self.list_plans(5)
        version_status = self.iterator.get_status()
        
        lines = [
            "# 自迭代智能触发报告",
            "",
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## 当前状态",
            "",
            f"- 项目: {version_status['project_name']}",
            f"- 当前版本: {version_status['current_version']}",
            f"- 迭代次数: {version_status['iteration_count']}",
            "",
            "## 最近触发记录",
            "",
        ]
        
        if trigger_history:
            for record in reversed(trigger_history[-10:]):
                status = "✅ 已触发" if record.get('should_trigger') else "❌ 未触发"
                lines.append(f"### {record['timestamp']}")
                lines.append(f"- 状态: {status}")
                lines.append(f"- 检测问题: {record.get('issues_detected', 0)}")
                
                if record.get('iteration_executed'):
                    lines.append(f"- 迭代执行: 是")
                    lines.append(f"- 新版本: {record.get('new_version', 'N/A')}")
                
                if record.get('trigger_reason'):
                    lines.append(f"- 触发原因: {record['trigger_reason']}")
                lines.append("")
        else:
            lines.append("- 无触发记录")
        
        if recent_plans:
            lines.extend([
                "",
                "## 最近迭代计划",
                "",
            ])
            for plan in recent_plans:
                lines.append(f"### {plan['plan_id']}")
                lines.append(f"- 优先级: {plan['priority']}")
                lines.append(f"- 版本升级: {plan['version_bump_type']}")
                lines.append(f"- 预估工作量: {plan['estimated_effort']}")
                lines.append(f"- 问题数: {len(plan.get('issues', []))}")
                lines.append("")
        
        report = '\n'.join(lines)
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)
        
        return report


def main():
    parser = argparse.ArgumentParser(description='自迭代智能触发增强脚本')
    
    parser.add_argument(
        '--project-root', '-p',
        default='.',
        help='项目根目录'
    )
    parser.add_argument(
        '--auto-execute',
        action='store_true',
        help='自动执行迭代'
    )
    parser.add_argument(
        '--report', '-r',
        action='store_true',
        help='生成报告'
    )
    parser.add_argument(
        '--output', '-o',
        help='报告输出路径'
    )
    parser.add_argument(
        '--list-plans',
        action='store_true',
        help='列出迭代计划'
    )
    parser.add_argument(
        '--get-plan',
        help='获取指定计划详情'
    )
    
    args = parser.parse_args()
    
    trigger = EnhancedSelfIterationTrigger(args.project_root)
    
    if args.list_plans:
        plans = trigger.list_plans(10)
        print("=== 最近迭代计划 ===")
        for plan in plans:
            print(f"{plan['plan_id']}: 优先级={plan['priority']}, 问题数={len(plan.get('issues', []))}")
        return 0
    
    if args.get_plan:
        plan = trigger.get_plan(args.get_plan)
        if plan:
            print(json.dumps(plan, indent=2, ensure_ascii=False))
        else:
            print(f"计划 {args.get_plan} 不存在")
        return 0
    
    if args.report:
        output_path = args.output or os.path.join(args.project_root, 'trigger_report.md')
        report = trigger.generate_report(output_path)
        print(f"报告已生成: {output_path}")
        return 0
    
    result = trigger.analyze_and_trigger(auto_execute=args.auto_execute)
    
    print("=== 自迭代智能分析结果 ===")
    print(f"检测问题数: {result['issues_detected']}")
    print(f"关键问题: {result['issues_by_severity']['critical']}")
    print(f"高优先级问题: {result['issues_by_severity']['high']}")
    print(f"建议触发迭代: {'是' if result['should_trigger'] else '否'}")
    
    if result.get('trigger_reason'):
        print(f"触发原因: {result['trigger_reason']}")
    
    if result.get('iteration_executed'):
        print(f"\n迭代已执行: {result['new_version']}")
    
    print(f"\n迭代计划ID: {result['plan']['plan_id']}")
    print(f"优先级: {result['plan']['priority']}")
    print(f"预估工作量: {result['plan']['estimated_effort']}")
    
    return 0


if __name__ == '__main__':
    exit(main())
