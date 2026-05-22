#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
技术债务追踪器 (增强版)

实现债务识别（TODO/FIXME/HACK注释、过时代码、废弃API、代码异味、复杂度、缺少测试）、
债务状态追踪、偿还计划生成、债务报告生成（JSON/Markdown）和趋势分析。

使用示例:
    python tech_debt_tracker.py
    python tech_debt_tracker.py --project myproject --output json
    python tech_debt_tracker.py --generate-plan --priority-threshold 0.7
    python tech_debt_tracker.py --report-format markdown --output-file debt_report.md
"""

import json
import logging
import sys
import argparse
import ast
import re
import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from collections import defaultdict


class DebtType(Enum):
    """技术债务类型"""
    TODO_COMMENT = "todo_comment"
    FIXME_COMMENT = "fixme_comment"
    HACK_COMMENT = "hack_comment"
    CODE_SMELL = "code_smell"
    DUPLICATE_CODE = "duplicate_code"
    OUTDATED_DEPENDENCY = "outdated_dependency"
    MISSING_DOCUMENTATION = "missing_documentation"
    MISSING_TESTS = "missing_tests"
    COMPLEX_CODE = "complex_code"
    SECURITY_ISSUE = "security_issue"
    PERFORMANCE_ISSUE = "performance_issue"
    ARCHITECTURE_VIOLATION = "architecture_violation"
    DEPRECATED_API = "deprecated_api"
    OUTDATED_CODE = "outdated_code"


class DebtStatus(Enum):
    """债务状态"""
    NEW = "new"
    IDENTIFIED = "identified"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    DEFERRED = "deferred"
    WONT_FIX = "wont_fix"


class DebtPriority(Enum):
    """债务优先级"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    TRIVIAL = "trivial"


class DebtCategory(Enum):
    """债务类别"""
    MAINTAINABILITY = "maintainability"
    RELIABILITY = "reliability"
    SECURITY = "security"
    PERFORMANCE = "performance"
    TESTABILITY = "testability"
    DOCUMENTATION = "documentation"
    CODE_QUALITY = "code_quality"


@dataclass
class DebtItem:
    """技术债务项"""
    debt_id: str
    debt_type: DebtType
    category: DebtCategory
    priority: DebtPriority
    status: DebtStatus
    file_path: str
    line_start: int
    line_end: int
    description: str
    impact_score: float
    effort_estimate: float
    created_at: str
    updated_at: str
    resolved_at: Optional[str] = None
    assignee: str = ""
    tags: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    related_debts: List[str] = field(default_factory=list)
    resolution_notes: str = ""
    comment_text: str = ""
    suggested_fix: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "debt_id": self.debt_id,
            "debt_type": self.debt_type.value,
            "category": self.category.value,
            "priority": self.priority.value,
            "status": self.status.value,
            "file_path": self.file_path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "description": self.description,
            "impact_score": round(self.impact_score, 2),
            "effort_estimate": round(self.effort_estimate, 2),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "resolved_at": self.resolved_at,
            "assignee": self.assignee,
            "tags": self.tags,
            "metrics": self.metrics,
            "related_debts": self.related_debts,
            "resolution_notes": self.resolution_notes,
            "comment_text": self.comment_text,
            "suggested_fix": self.suggested_fix
        }


@dataclass
class RepaymentTask:
    """偿还任务"""
    task_id: str
    debt_ids: List[str]
    title: str
    description: str
    priority: DebtPriority
    estimated_effort: float
    impact_score: float
    dependencies: List[str] = field(default_factory=list)
    steps: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    benefits: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "debt_ids": self.debt_ids,
            "title": self.title,
            "description": self.description,
            "priority": self.priority.value,
            "estimated_effort": round(self.estimated_effort, 2),
            "impact_score": round(self.impact_score, 2),
            "dependencies": self.dependencies,
            "steps": self.steps,
            "risks": self.risks,
            "benefits": self.benefits
        }


@dataclass
class RepaymentPlan:
    """偿还计划"""
    project: str
    created_at: str
    total_debt_count: int
    total_effort: float
    total_impact: float
    phases: Dict[str, List[RepaymentTask]]
    timeline: Dict[str, Any]
    recommendations: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project": self.project,
            "created_at": self.created_at,
            "total_debt_count": self.total_debt_count,
            "total_effort": round(self.total_effort, 2),
            "total_impact": round(self.total_impact, 2),
            "phases": {
                phase: [t.to_dict() for t in tasks]
                for phase, tasks in self.phases.items()
            },
            "timeline": self.timeline,
            "recommendations": self.recommendations
        }


@dataclass
class DebtTrend:
    """债务趋势数据"""
    date: str
    total_debts: int
    new_debts: int
    resolved_debts: int
    open_debts: int
    health_score: float
    by_priority: Dict[str, int] = field(default_factory=dict)
    by_type: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "date": self.date,
            "total_debts": self.total_debts,
            "new_debts": self.new_debts,
            "resolved_debts": self.resolved_debts,
            "open_debts": self.open_debts,
            "health_score": round(self.health_score, 2),
            "by_priority": self.by_priority,
            "by_type": self.by_type
        }


@dataclass
class DebtTrackerReport:
    """债务追踪报告"""
    timestamp: str
    project: str
    total_debts: int
    open_debts: int
    resolved_debts: int
    debts: List[DebtItem]
    summary: Dict[str, Any]
    repayment_plan: Optional[RepaymentPlan] = None
    trends: Dict[str, Any] = field(default_factory=dict)
    trend_history: List[DebtTrend] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "project": self.project,
            "total_debts": self.total_debts,
            "open_debts": self.open_debts,
            "resolved_debts": self.resolved_debts,
            "debts": [d.to_dict() for d in self.debts],
            "summary": self.summary,
            "repayment_plan": self.repayment_plan.to_dict() if self.repayment_plan else None,
            "trends": self.trends,
            "trend_history": [t.to_dict() for t in self.trend_history]
        }


class IDebtDetector(ABC):
    """债务检测器接口"""

    @abstractmethod
    def detect(self, file_path: Path, content: str) -> List[DebtItem]:
        pass

    @abstractmethod
    def get_debt_type(self) -> DebtType:
        pass


class TodoCommentDetector(IDebtDetector):
    """TODO/FIXME/HACK注释检测器"""

    PATTERNS = {
        DebtType.TODO_COMMENT: re.compile(r'#\s*TODO(?:\s*\(([^)]+)\))?:?\s*(.+)', re.IGNORECASE),
        DebtType.FIXME_COMMENT: re.compile(r'#\s*FIXME(?:\s*\(([^)]+)\))?:?\s*(.+)', re.IGNORECASE),
        DebtType.HACK_COMMENT: re.compile(r'#\s*HACK(?:\s*\(([^)]+)\))?:?\s*(.+)', re.IGNORECASE),
    }

    PRIORITY_KEYWORDS = {
        "urgent": DebtPriority.CRITICAL,
        "critical": DebtPriority.CRITICAL,
        "important": DebtPriority.HIGH,
        "high": DebtPriority.HIGH,
        "medium": DebtPriority.MEDIUM,
        "low": DebtPriority.LOW,
        "minor": DebtPriority.LOW,
        "trivial": DebtPriority.TRIVIAL,
    }

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)

    def get_debt_type(self) -> DebtType:
        return DebtType.TODO_COMMENT

    def detect(self, file_path: Path, content: str) -> List[DebtItem]:
        debts: List[DebtItem] = []
        timestamp = datetime.now().isoformat()
        lines = content.split('\n')

        for line_num, line in enumerate(lines, 1):
            for debt_type, pattern in self.PATTERNS.items():
                match = pattern.search(line)
                if match:
                    assignee = match.group(1) or ""
                    comment_text = match.group(2).strip()
                    priority = self._extract_priority(comment_text, assignee)

                    debt_id = self._generate_id(str(file_path), line_num, comment_text)

                    description = self._generate_description(debt_type, comment_text, assignee)
                    suggested_fix = self._suggest_fix(debt_type, comment_text)

                    debts.append(DebtItem(
                        debt_id=debt_id,
                        debt_type=debt_type,
                        category=DebtCategory.CODE_QUALITY,
                        priority=priority,
                        status=DebtStatus.NEW,
                        file_path=str(file_path),
                        line_start=line_num,
                        line_end=line_num,
                        description=description,
                        impact_score=self._calculate_impact(priority),
                        effort_estimate=self._estimate_effort(comment_text),
                        created_at=timestamp,
                        updated_at=timestamp,
                        assignee=assignee.strip() if assignee else "",
                        tags=[debt_type.value, "comment", "action-needed"],
                        comment_text=comment_text,
                        suggested_fix=suggested_fix,
                        metrics={"comment_type": debt_type.value}
                    ))

        return debts

    def _extract_priority(self, text: str, assignee: str) -> DebtPriority:
        text_lower = text.lower()
        for keyword, priority in self.PRIORITY_KEYWORDS.items():
            if keyword in text_lower:
                return priority
        if assignee:
            return DebtPriority.MEDIUM
        return DebtPriority.LOW

    def _calculate_impact(self, priority: DebtPriority) -> float:
        impact_map = {
            DebtPriority.CRITICAL: 10.0,
            DebtPriority.HIGH: 7.0,
            DebtPriority.MEDIUM: 5.0,
            DebtPriority.LOW: 3.0,
            DebtPriority.TRIVIAL: 1.0,
        }
        return impact_map.get(priority, 3.0)

    def _estimate_effort(self, text: str) -> float:
        text_lower = text.lower()
        if any(kw in text_lower for kw in ["refactor", "rewrite", "redesign"]):
            return 4.0
        if any(kw in text_lower for kw in ["implement", "add", "create"]):
            return 3.0
        if any(kw in text_lower for kw in ["fix", "update", "change"]):
            return 2.0
        return 1.0

    def _generate_description(self, debt_type: DebtType, text: str, assignee: str) -> str:
        type_names = {
            DebtType.TODO_COMMENT: "待办事项",
            DebtType.FIXME_COMMENT: "需要修复",
            DebtType.HACK_COMMENT: "临时方案",
        }
        base = type_names.get(debt_type, "注释标记")
        if assignee:
            return f"{base} (负责人: {assignee}): {text}"
        return f"{base}: {text}"

    def _suggest_fix(self, debt_type: DebtType, text: str) -> str:
        suggestions = {
            DebtType.TODO_COMMENT: "评估是否需要实现该功能，如需要则创建任务并实现",
            DebtType.FIXME_COMMENT: "分析问题原因，制定修复方案并实施",
            DebtType.HACK_COMMENT: "寻找更优雅的解决方案，替换临时实现",
        }
        return suggestions.get(debt_type, "处理该标记项")

    def _generate_id(self, file_path: str, line: int, text: str) -> str:
        content = f"{file_path}:{line}:{text[:50]}"
        return hashlib.md5(content.encode()).hexdigest()[:12]


class DeprecatedAPIDetector(IDebtDetector):
    """废弃API使用检测器"""

    DEPRECATED_APIS = {
        "python": {
            "execfile": {"since": "3.0", "alternative": "exec(open().read())", "severity": "high"},
            "raw_input": {"since": "3.0", "alternative": "input()", "severity": "high"},
            "xrange": {"since": "3.0", "alternative": "range()", "severity": "high"},
            "unicode": {"since": "3.0", "alternative": "str", "severity": "high"},
            "apply": {"since": "3.0", "alternative": "function(*args, **kwargs)", "severity": "medium"},
            "buffer": {"since": "3.0", "alternative": "memoryview", "severity": "medium"},
            "cmp": {"since": "3.0", "alternative": "(a > b) - (a < b)", "severity": "low"},
            "reload": {"since": "3.4", "alternative": "importlib.reload()", "severity": "medium"},
            "commands.getoutput": {"since": "3.0", "alternative": "subprocess.getoutput()", "severity": "high"},
        }
    }

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)

    def get_debt_type(self) -> DebtType:
        return DebtType.DEPRECATED_API

    def detect(self, file_path: Path, content: str) -> List[DebtItem]:
        debts: List[DebtItem] = []
        timestamp = datetime.now().isoformat()

        try:
            tree = ast.parse(content)
            deprecated_apis = self.DEPRECATED_APIS.get("python", {})

            for node in ast.walk(tree):
                if isinstance(node, ast.Name):
                    if node.id in deprecated_apis:
                        api_info = deprecated_apis[node.id]
                        debt_id = self._generate_id(str(file_path), node.lineno, node.id)

                        debts.append(DebtItem(
                            debt_id=debt_id,
                            debt_type=DebtType.DEPRECATED_API,
                            category=DebtCategory.RELIABILITY,
                            priority=self._get_priority(api_info["severity"]),
                            status=DebtStatus.NEW,
                            file_path=str(file_path),
                            line_start=node.lineno,
                            line_end=node.lineno,
                            description=f"废弃API: {node.id} (自Python {api_info['since']}起废弃)",
                            impact_score=self._get_impact(api_info["severity"]),
                            effort_estimate=1.0,
                            created_at=timestamp,
                            updated_at=timestamp,
                            tags=["deprecated-api", "migration"],
                            suggested_fix=f"替换为: {api_info['alternative']}",
                            metrics={
                                "api_name": node.id,
                                "deprecated_since": api_info["since"],
                                "alternative": api_info["alternative"]
                            }
                        ))

                elif isinstance(node, ast.Attribute):
                    attr_name = f"{node.value.id}.{node.attr}" if isinstance(node.value, ast.Name) else None
                    if attr_name and attr_name in deprecated_apis:
                        api_info = deprecated_apis[attr_name]
                        debt_id = self._generate_id(str(file_path), node.lineno, attr_name)

                        debts.append(DebtItem(
                            debt_id=debt_id,
                            debt_type=DebtType.DEPRECATED_API,
                            category=DebtCategory.RELIABILITY,
                            priority=self._get_priority(api_info["severity"]),
                            status=DebtStatus.NEW,
                            file_path=str(file_path),
                            line_start=node.lineno,
                            line_end=node.lineno,
                            description=f"废弃API: {attr_name} (自Python {api_info['since']}起废弃)",
                            impact_score=self._get_impact(api_info["severity"]),
                            effort_estimate=1.0,
                            created_at=timestamp,
                            updated_at=timestamp,
                            tags=["deprecated-api", "migration"],
                            suggested_fix=f"替换为: {api_info['alternative']}",
                            metrics={
                                "api_name": attr_name,
                                "deprecated_since": api_info["since"],
                                "alternative": api_info["alternative"]
                            }
                        ))

        except SyntaxError as e:
            self.logger.warning(f"语法错误 {file_path}: {e}")

        return debts

    def _get_priority(self, severity: str) -> DebtPriority:
        return {
            "high": DebtPriority.HIGH,
            "medium": DebtPriority.MEDIUM,
            "low": DebtPriority.LOW,
        }.get(severity, DebtPriority.MEDIUM)

    def _get_impact(self, severity: str) -> float:
        return {
            "high": 8.0,
            "medium": 5.0,
            "low": 3.0,
        }.get(severity, 5.0)

    def _generate_id(self, file_path: str, line: int, api_name: str) -> str:
        content = f"{file_path}:{line}:{api_name}"
        return hashlib.md5(content.encode()).hexdigest()[:12]


class CodeSmellDetector(IDebtDetector):
    """代码异味检测器"""

    THRESHOLDS = {
        "long_method_lines": 50,
        "large_class_lines": 300,
        "long_parameter_list": 5,
        "deep_nesting": 4,
        "high_complexity": 10
    }

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)

    def get_debt_type(self) -> DebtType:
        return DebtType.CODE_SMELL

    def detect(self, file_path: Path, content: str) -> List[DebtItem]:
        debts: List[DebtItem] = []
        timestamp = datetime.now().isoformat()

        try:
            tree = ast.parse(content)
            debts.extend(self._detect_long_methods(tree, str(file_path), timestamp))
            debts.extend(self._detect_large_classes(tree, str(file_path), timestamp))
            debts.extend(self._detect_long_parameters(tree, str(file_path), timestamp))
            debts.extend(self._detect_deep_nesting(tree, str(file_path), timestamp))
            debts.extend(self._detect_high_complexity(tree, str(file_path), timestamp))
        except SyntaxError as e:
            self.logger.warning(f"语法错误 {file_path}: {e}")

        return debts

    def _detect_long_methods(self, tree: ast.AST, file_path: str, timestamp: str) -> List[DebtItem]:
        debts: List[DebtItem] = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                line_start = node.lineno
                line_end = getattr(node, 'end_lineno', line_start) or line_start
                line_count = line_end - line_start + 1

                if line_count > self.THRESHOLDS["long_method_lines"]:
                    debt_id = self._generate_id(file_path, node.name, line_start)
                    debts.append(DebtItem(
                        debt_id=debt_id,
                        debt_type=DebtType.CODE_SMELL,
                        category=DebtCategory.MAINTAINABILITY,
                        priority=DebtPriority.HIGH if line_count > self.THRESHOLDS["long_method_lines"] * 1.5 else DebtPriority.MEDIUM,
                        status=DebtStatus.NEW,
                        file_path=file_path,
                        line_start=line_start,
                        line_end=line_end,
                        description=f"方法过长: {node.name} ({line_count} 行)",
                        impact_score=min(line_count / 10, 10),
                        effort_estimate=line_count / 20,
                        created_at=timestamp,
                        updated_at=timestamp,
                        tags=["long-method", "refactoring"],
                        suggested_fix="将方法拆分为多个更小的方法，每个方法只做一件事",
                        metrics={"lines": line_count, "threshold": self.THRESHOLDS["long_method_lines"]}
                    ))

        return debts

    def _detect_large_classes(self, tree: ast.AST, file_path: str, timestamp: str) -> List[DebtItem]:
        debts: List[DebtItem] = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                line_start = node.lineno
                line_end = getattr(node, 'end_lineno', line_start) or line_start
                class_lines = line_end - line_start + 1

                if class_lines > self.THRESHOLDS["large_class_lines"]:
                    debt_id = self._generate_id(file_path, node.name, line_start)
                    debts.append(DebtItem(
                        debt_id=debt_id,
                        debt_type=DebtType.CODE_SMELL,
                        category=DebtCategory.MAINTAINABILITY,
                        priority=DebtPriority.HIGH if class_lines > self.THRESHOLDS["large_class_lines"] * 1.5 else DebtPriority.MEDIUM,
                        status=DebtStatus.NEW,
                        file_path=file_path,
                        line_start=line_start,
                        line_end=line_end,
                        description=f"类过大: {node.name} ({class_lines} 行)",
                        impact_score=min(class_lines / 20, 10),
                        effort_estimate=class_lines / 30,
                        created_at=timestamp,
                        updated_at=timestamp,
                        tags=["large-class", "refactoring"],
                        suggested_fix="应用单一职责原则，将类拆分为多个更小的类",
                        metrics={"lines": class_lines, "threshold": self.THRESHOLDS["large_class_lines"]}
                    ))

        return debts

    def _detect_long_parameters(self, tree: ast.AST, file_path: str, timestamp: str) -> List[DebtItem]:
        debts: List[DebtItem] = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                param_count = len(node.args.args) + len(node.args.kwonlyargs)
                if node.args.vararg:
                    param_count += 1
                if node.args.kwarg:
                    param_count += 1

                if param_count > self.THRESHOLDS["long_parameter_list"]:
                    debt_id = self._generate_id(file_path, node.name, node.lineno)
                    debts.append(DebtItem(
                        debt_id=debt_id,
                        debt_type=DebtType.CODE_SMELL,
                        category=DebtCategory.MAINTAINABILITY,
                        priority=DebtPriority.MEDIUM,
                        status=DebtStatus.NEW,
                        file_path=file_path,
                        line_start=node.lineno,
                        line_end=node.lineno,
                        description=f"参数列表过长: {node.name} ({param_count} 个参数)",
                        impact_score=param_count / 2,
                        effort_estimate=2.0,
                        created_at=timestamp,
                        updated_at=timestamp,
                        tags=["long-parameter-list", "refactoring"],
                        suggested_fix="使用参数对象或构建器模式封装参数",
                        metrics={"param_count": param_count, "threshold": self.THRESHOLDS["long_parameter_list"]}
                    ))

        return debts

    def _detect_deep_nesting(self, tree: ast.AST, file_path: str, timestamp: str) -> List[DebtItem]:
        debts: List[DebtItem] = []

        class NestingVisitor(ast.NodeVisitor):
            def __init__(self):
                self.max_depth = 0
                self.current_depth = 0
                self.problematic_nodes: List[Tuple[ast.AST, int]] = []

            def _visit_with_depth(self, node: ast.AST):
                self.current_depth += 1
                if self.current_depth > self.max_depth:
                    self.max_depth = self.current_depth
                if self.current_depth > 4:
                    self.problematic_nodes.append((node, self.current_depth))
                self.generic_visit(node)
                self.current_depth -= 1

            def visit_If(self, node: ast.If):
                self._visit_with_depth(node)

            def visit_For(self, node: ast.For):
                self._visit_with_depth(node)

            def visit_While(self, node: ast.While):
                self._visit_with_depth(node)

        visitor = NestingVisitor()
        visitor.visit(tree)

        for node, depth in visitor.problematic_nodes:
            if hasattr(node, 'lineno'):
                debt_id = self._generate_id(file_path, "nesting", node.lineno)
                debts.append(DebtItem(
                    debt_id=debt_id,
                    debt_type=DebtType.CODE_SMELL,
                    category=DebtCategory.MAINTAINABILITY,
                    priority=DebtPriority.HIGH if depth > 5 else DebtPriority.MEDIUM,
                    status=DebtStatus.NEW,
                    file_path=file_path,
                    line_start=node.lineno,
                    line_end=getattr(node, 'end_lineno', node.lineno) or node.lineno,
                    description=f"嵌套过深: {depth} 层",
                    impact_score=depth,
                    effort_estimate=depth / 2,
                    created_at=timestamp,
                    updated_at=timestamp,
                    tags=["deep-nesting", "refactoring"],
                    suggested_fix="使用提取方法、早返回或策略模式减少嵌套层级",
                    metrics={"nesting_depth": depth, "threshold": self.THRESHOLDS["deep_nesting"]}
                ))

        return debts

    def _detect_high_complexity(self, tree: ast.AST, file_path: str, timestamp: str) -> List[DebtItem]:
        debts: List[DebtItem] = []

        class ComplexityVisitor(ast.NodeVisitor):
            def __init__(self):
                self.complexity = 1

            def visit_If(self, node: ast.If):
                self.complexity += 1
                self.generic_visit(node)

            def visit_For(self, node: ast.For):
                self.complexity += 1
                self.generic_visit(node)

            def visit_While(self, node: ast.While):
                self.complexity += 1
                self.generic_visit(node)

            def visit_ExceptHandler(self, node: ast.ExceptHandler):
                self.complexity += 1
                self.generic_visit(node)

            def visit_BoolOp(self, node: ast.BoolOp):
                self.complexity += len(node.values) - 1
                self.generic_visit(node)

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                visitor = ComplexityVisitor()
                visitor.visit(node)

                if visitor.complexity > self.THRESHOLDS["high_complexity"]:
                    debt_id = self._generate_id(file_path, node.name, node.lineno)
                    debts.append(DebtItem(
                        debt_id=debt_id,
                        debt_type=DebtType.COMPLEX_CODE,
                        category=DebtCategory.MAINTAINABILITY,
                        priority=DebtPriority.HIGH if visitor.complexity > 15 else DebtPriority.MEDIUM,
                        status=DebtStatus.NEW,
                        file_path=file_path,
                        line_start=node.lineno,
                        line_end=getattr(node, 'end_lineno', node.lineno) or node.lineno,
                        description=f"圈复杂度过高: {node.name} (复杂度: {visitor.complexity})",
                        impact_score=visitor.complexity / 2,
                        effort_estimate=visitor.complexity / 5,
                        created_at=timestamp,
                        updated_at=timestamp,
                        tags=["high-complexity", "refactoring"],
                        suggested_fix="简化条件逻辑，使用多态或策略模式替代复杂条件",
                        metrics={"complexity": visitor.complexity, "threshold": self.THRESHOLDS["high_complexity"]}
                    ))

        return debts

    def _generate_id(self, file_path: str, name: str, line: int) -> str:
        content = f"{file_path}:{name}:{line}"
        return hashlib.md5(content.encode()).hexdigest()[:12]


class DuplicateCodeDetector(IDebtDetector):
    """重复代码检测器"""

    MIN_BLOCK_LINES = 6

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)

    def get_debt_type(self) -> DebtType:
        return DebtType.DUPLICATE_CODE

    def detect(self, file_path: Path, content: str) -> List[DebtItem]:
        debts: List[DebtItem] = []
        timestamp = datetime.now().isoformat()
        lines = content.split('\n')

        code_blocks: Dict[str, List[Tuple[int, int]]] = defaultdict(list)

        for i in range(len(lines) - self.MIN_BLOCK_LINES + 1):
            block = '\n'.join(lines[i:i + self.MIN_BLOCK_LINES])
            normalized = self._normalize_code(block)
            if normalized and not normalized.strip().startswith('#'):
                block_hash = hashlib.md5(normalized.encode()).hexdigest()
                code_blocks[block_hash].append((i + 1, i + self.MIN_BLOCK_LINES))

        for block_hash, locations in code_blocks.items():
            if len(locations) > 1:
                first_loc = locations[0]
                debt_id = hashlib.md5(f"{file_path}:{block_hash}".encode()).hexdigest()[:12]
                debts.append(DebtItem(
                    debt_id=debt_id,
                    debt_type=DebtType.DUPLICATE_CODE,
                    category=DebtCategory.MAINTAINABILITY,
                    priority=DebtPriority.HIGH,
                    status=DebtStatus.NEW,
                    file_path=str(file_path),
                    line_start=first_loc[0],
                    line_end=first_loc[1],
                    description=f"重复代码块: 发现 {len(locations)} 处相似代码",
                    impact_score=len(locations) * 2,
                    effort_estimate=len(locations) * 0.5,
                    created_at=timestamp,
                    updated_at=timestamp,
                    tags=["duplicate-code", "refactoring"],
                    suggested_fix="提取公共方法或类，消除重复代码",
                    metrics={"occurrences": len(locations), "block_lines": self.MIN_BLOCK_LINES}
                ))

        return debts

    def _normalize_code(self, code: str) -> str:
        normalized = re.sub(r'#.*$', '', code, flags=re.MULTILINE)
        normalized = re.sub(r'\s+', ' ', normalized)
        return normalized.strip()


class MissingTestDetector(IDebtDetector):
    """缺失测试检测器"""

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)

    def get_debt_type(self) -> DebtType:
        return DebtType.MISSING_TESTS

    def detect(self, file_path: Path, content: str) -> List[DebtItem]:
        debts: List[DebtItem] = []
        timestamp = datetime.now().isoformat()

        if "test" in str(file_path).lower():
            return debts

        try:
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if not node.name.startswith('_'):
                        debt_id = hashlib.md5(f"{file_path}:{node.name}:test".encode()).hexdigest()[:12]
                        debts.append(DebtItem(
                            debt_id=debt_id,
                            debt_type=DebtType.MISSING_TESTS,
                            category=DebtCategory.TESTABILITY,
                            priority=DebtPriority.MEDIUM,
                            status=DebtStatus.NEW,
                            file_path=str(file_path),
                            line_start=node.lineno,
                            line_end=node.lineno,
                            description=f"缺少测试: 方法 {node.name}",
                            impact_score=3.0,
                            effort_estimate=1.0,
                            created_at=timestamp,
                            updated_at=timestamp,
                            tags=["missing-test", "testing"],
                            suggested_fix=f"为 {node.name} 方法编写单元测试",
                            metrics={"function_name": node.name}
                        ))
        except SyntaxError:
            pass

        return debts


class MissingDocDetector(IDebtDetector):
    """缺失文档检测器"""

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)

    def get_debt_type(self) -> DebtType:
        return DebtType.MISSING_DOCUMENTATION

    def detect(self, file_path: Path, content: str) -> List[DebtItem]:
        debts: List[DebtItem] = []
        timestamp = datetime.now().isoformat()

        try:
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    if not ast.get_docstring(node):
                        debt_id = hashlib.md5(f"{file_path}:{node.name}:doc".encode()).hexdigest()[:12]
                        debts.append(DebtItem(
                            debt_id=debt_id,
                            debt_type=DebtType.MISSING_DOCUMENTATION,
                            category=DebtCategory.DOCUMENTATION,
                            priority=DebtPriority.LOW,
                            status=DebtStatus.NEW,
                            file_path=str(file_path),
                            line_start=node.lineno,
                            line_end=node.lineno,
                            description=f"缺少文档: 类 {node.name}",
                            impact_score=2.0,
                            effort_estimate=0.5,
                            created_at=timestamp,
                            updated_at=timestamp,
                            tags=["missing-doc", "documentation"],
                            suggested_fix=f"为类 {node.name} 添加文档字符串",
                            metrics={"type": "class", "name": node.name}
                        ))

                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if not node.name.startswith('_') and not ast.get_docstring(node):
                        debt_id = hashlib.md5(f"{file_path}:{node.name}:doc".encode()).hexdigest()[:12]
                        debts.append(DebtItem(
                            debt_id=debt_id,
                            debt_type=DebtType.MISSING_DOCUMENTATION,
                            category=DebtCategory.DOCUMENTATION,
                            priority=DebtPriority.LOW,
                            status=DebtStatus.NEW,
                            file_path=str(file_path),
                            line_start=node.lineno,
                            line_end=node.lineno,
                            description=f"缺少文档: 方法 {node.name}",
                            impact_score=1.0,
                            effort_estimate=0.25,
                            created_at=timestamp,
                            updated_at=timestamp,
                            tags=["missing-doc", "documentation"],
                            suggested_fix=f"为方法 {node.name} 添加文档字符串",
                            metrics={"type": "function", "name": node.name}
                        ))
        except SyntaxError:
            pass

        return debts


class DebtStateManager:
    """债务状态管理器"""

    def __init__(self, storage_path: Optional[Path] = None, logger: Optional[logging.Logger] = None):
        self.storage_path = storage_path
        self.logger = logger or logging.getLogger(__name__)
        self._debts: Dict[str, DebtItem] = {}
        self._trend_history: List[DebtTrend] = []

    def load(self) -> Dict[str, DebtItem]:
        """加载已保存的债务"""
        if not self.storage_path or not self.storage_path.exists():
            return {}

        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            for item in data.get("debts", []):
                debt = DebtItem(
                    debt_id=item["debt_id"],
                    debt_type=DebtType(item["debt_type"]),
                    category=DebtCategory(item["category"]),
                    priority=DebtPriority(item["priority"]),
                    status=DebtStatus(item["status"]),
                    file_path=item["file_path"],
                    line_start=item["line_start"],
                    line_end=item["line_end"],
                    description=item["description"],
                    impact_score=item["impact_score"],
                    effort_estimate=item["effort_estimate"],
                    created_at=item["created_at"],
                    updated_at=item["updated_at"],
                    resolved_at=item.get("resolved_at"),
                    assignee=item.get("assignee", ""),
                    tags=item.get("tags", []),
                    metrics=item.get("metrics", {}),
                    related_debts=item.get("related_debts", []),
                    resolution_notes=item.get("resolution_notes", ""),
                    comment_text=item.get("comment_text", ""),
                    suggested_fix=item.get("suggested_fix", "")
                )
                self._debts[debt.debt_id] = debt

            for trend_data in data.get("trend_history", []):
                trend = DebtTrend(
                    date=trend_data["date"],
                    total_debts=trend_data["total_debts"],
                    new_debts=trend_data["new_debts"],
                    resolved_debts=trend_data["resolved_debts"],
                    open_debts=trend_data["open_debts"],
                    health_score=trend_data["health_score"],
                    by_priority=trend_data.get("by_priority", {}),
                    by_type=trend_data.get("by_type", {})
                )
                self._trend_history.append(trend)

            self.logger.info(f"加载了 {len(self._debts)} 条债务记录")
            return self._debts
        except Exception as e:
            self.logger.error(f"加载债务记录失败: {e}")
            return {}

    def save(self, debts: List[DebtItem], trend_history: Optional[List[DebtTrend]] = None) -> bool:
        """保存债务记录"""
        if not self.storage_path:
            return True

        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)

            data = {
                "debts": [d.to_dict() for d in debts],
                "trend_history": [t.to_dict() for t in (trend_history or self._trend_history)],
                "last_updated": datetime.now().isoformat(),
                "total_count": len(debts)
            }

            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"保存了 {len(debts)} 条债务记录")
            return True
        except Exception as e:
            self.logger.error(f"保存债务记录失败: {e}")
            return False

    def update_status(self, debt_id: str, new_status: DebtStatus, notes: str = "") -> Optional[DebtItem]:
        """更新债务状态"""
        if debt_id not in self._debts:
            return None

        debt = self._debts[debt_id]
        old_status = debt.status
        debt.status = new_status
        debt.updated_at = datetime.now().isoformat()

        if new_status == DebtStatus.RESOLVED:
            debt.resolved_at = datetime.now().isoformat()

        if notes:
            debt.resolution_notes = notes

        return debt

    def merge_debts(self, new_debts: List[DebtItem]) -> List[DebtItem]:
        """合并新旧债务"""
        timestamp = datetime.now().isoformat()

        for debt in new_debts:
            if debt.debt_id in self._debts:
                existing = self._debts[debt.debt_id]
                existing.updated_at = timestamp
                if existing.status == DebtStatus.RESOLVED:
                    existing.status = DebtStatus.NEW
                    existing.resolved_at = None
            else:
                self._debts[debt.debt_id] = debt

        return list(self._debts.values())

    def record_trend(self, debts: List[DebtItem]) -> DebtTrend:
        """记录趋势数据"""
        today = datetime.now().strftime("%Y-%m-%d")

        open_debts = [d for d in debts if d.status not in [DebtStatus.RESOLVED, DebtStatus.WONT_FIX]]
        resolved_debts = [d for d in debts if d.status == DebtStatus.RESOLVED]
        new_debts = [d for d in debts if d.status == DebtStatus.NEW]

        by_priority: Dict[str, int] = defaultdict(int)
        by_type: Dict[str, int] = defaultdict(int)

        for debt in open_debts:
            by_priority[debt.priority.value] += 1
            by_type[debt.debt_type.value] += 1

        health_score = max(0, 100 - len(open_debts) * 2)

        trend = DebtTrend(
            date=today,
            total_debts=len(debts),
            new_debts=len(new_debts),
            resolved_debts=len(resolved_debts),
            open_debts=len(open_debts),
            health_score=health_score,
            by_priority=dict(by_priority),
            by_type=dict(by_type)
        )

        self._trend_history.append(trend)
        return trend


class RepaymentPlanGenerator:
    """偿还计划生成器"""

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)

    def generate(self, debts: List[DebtItem], project: str) -> RepaymentPlan:
        """生成偿还计划"""
        open_debts = [d for d in debts if d.status not in [DebtStatus.RESOLVED, DebtStatus.WONT_FIX]]

        sorted_debts = self._prioritize_debts(open_debts)

        phases = self._create_phases(sorted_debts)

        timeline = self._estimate_timeline(phases)

        recommendations = self._generate_recommendations(open_debts)

        total_effort = sum(d.effort_estimate for d in open_debts)
        total_impact = sum(d.impact_score for d in open_debts)

        return RepaymentPlan(
            project=project,
            created_at=datetime.now().isoformat(),
            total_debt_count=len(open_debts),
            total_effort=total_effort,
            total_impact=total_impact,
            phases=phases,
            timeline=timeline,
            recommendations=recommendations
        )

    def _prioritize_debts(self, debts: List[DebtItem]) -> List[DebtItem]:
        """优先级排序"""
        priority_scores = {
            DebtPriority.CRITICAL: 5,
            DebtPriority.HIGH: 4,
            DebtPriority.MEDIUM: 3,
            DebtPriority.LOW: 2,
            DebtPriority.TRIVIAL: 1
        }

        return sorted(
            debts,
            key=lambda d: (
                -priority_scores.get(d.priority, 0),
                -d.impact_score,
                d.effort_estimate
            )
        )

    def _create_phases(self, debts: List[DebtItem]) -> Dict[str, List[RepaymentTask]]:
        """创建偿还阶段"""
        phases: Dict[str, List[RepaymentTask]] = {
            "immediate": [],
            "short_term": [],
            "medium_term": [],
            "long_term": []
        }

        grouped = self._group_related_debts(debts)

        for group in grouped:
            task = self._create_task(group)

            if task.priority in [DebtPriority.CRITICAL]:
                phases["immediate"].append(task)
            elif task.priority == DebtPriority.HIGH:
                phases["short_term"].append(task)
            elif task.priority == DebtPriority.MEDIUM:
                phases["medium_term"].append(task)
            else:
                phases["long_term"].append(task)

        return phases

    def _group_related_debts(self, debts: List[DebtItem]) -> List[List[DebtItem]]:
        """分组相关债务"""
        groups: List[List[DebtItem]] = []
        used: Set[str] = set()

        for debt in debts:
            if debt.debt_id in used:
                continue

            group = [debt]
            used.add(debt.debt_id)

            for related_id in debt.related_debts:
                related = next((d for d in debts if d.debt_id == related_id), None)
                if related and related.debt_id not in used:
                    group.append(related)
                    used.add(related.debt_id)

            same_file_debts = [
                d for d in debts
                if d.file_path == debt.file_path and d.debt_id not in used
            ]
            for same_file_debt in same_file_debts[:3]:
                group.append(same_file_debt)
                used.add(same_file_debt.debt_id)

            groups.append(group)

        return groups

    def _create_task(self, debts: List[DebtItem]) -> RepaymentTask:
        """创建偿还任务"""
        debt_ids = [d.debt_id for d in debts]
        task_id = hashlib.md5(','.join(debt_ids).encode()).hexdigest()[:12]

        priorities = [d.priority for d in debts]
        priority = max(priorities, key=lambda p: {
            DebtPriority.CRITICAL: 5,
            DebtPriority.HIGH: 4,
            DebtPriority.MEDIUM: 3,
            DebtPriority.LOW: 2,
            DebtPriority.TRIVIAL: 1
        }.get(p, 0))

        total_effort = sum(d.effort_estimate for d in debts)
        total_impact = sum(d.impact_score for d in debts)

        descriptions = [d.description for d in debts[:3]]
        title = f"解决 {debts[0].debt_type.value} 问题 ({len(debts)} 项)"

        steps = self._generate_steps(debts)
        risks = self._identify_risks(debts)
        benefits = self._identify_benefits(debts)

        return RepaymentTask(
            task_id=task_id,
            debt_ids=debt_ids,
            title=title,
            description="; ".join(descriptions),
            priority=priority,
            estimated_effort=total_effort,
            impact_score=total_impact,
            steps=steps,
            risks=risks,
            benefits=benefits
        )

    def _generate_steps(self, debts: List[DebtItem]) -> List[str]:
        """生成解决步骤"""
        steps = []

        debt_types = set(d.debt_type for d in debts)

        if DebtType.TODO_COMMENT in debt_types or DebtType.FIXME_COMMENT in debt_types:
            steps.extend([
                "评估TODO/FIXME的重要性和紧急程度",
                "创建对应的任务或工单",
                "实施解决方案",
                "移除注释标记"
            ])

        if DebtType.HACK_COMMENT in debt_types:
            steps.extend([
                "分析临时方案的问题",
                "设计更优雅的解决方案",
                "重构代码替换临时实现",
                "添加测试确保功能正确"
            ])

        if DebtType.CODE_SMELL in debt_types:
            steps.extend([
                "分析代码结构，识别重构点",
                "编写测试确保行为不变",
                "应用重构模式优化代码",
                "验证重构后功能正确"
            ])

        if DebtType.DUPLICATE_CODE in debt_types:
            steps.extend([
                "识别重复代码的共同模式",
                "提取公共方法或类",
                "替换重复代码为公共实现",
                "添加单元测试覆盖"
            ])

        if DebtType.DEPRECATED_API in debt_types:
            steps.extend([
                "确认废弃API的使用位置",
                "查找推荐的替代API",
                "更新代码使用新API",
                "测试确保功能正常"
            ])

        if DebtType.MISSING_TESTS in debt_types:
            steps.extend([
                "分析方法功能和边界条件",
                "编写单元测试用例",
                "确保测试覆盖率达标",
                "集成到CI/CD流程"
            ])

        if DebtType.MISSING_DOCUMENTATION in debt_types:
            steps.extend([
                "分析代码功能和行为",
                "编写文档字符串",
                "添加使用示例",
                "更新相关文档"
            ])

        return steps[:6] if steps else ["分析问题", "制定解决方案", "实施修复", "验证结果"]

    def _identify_risks(self, debts: List[DebtItem]) -> List[str]:
        """识别风险"""
        risks = []

        total_effort = sum(d.effort_estimate for d in debts)
        if total_effort > 10:
            risks.append("工作量较大，需要合理安排时间")

        if any(d.debt_type == DebtType.DUPLICATE_CODE for d in debts):
            risks.append("消除重复代码可能影响多处调用")

        if any(d.debt_type == DebtType.DEPRECATED_API for d in debts):
            risks.append("API迁移可能需要兼容性测试")

        if any(d.priority == DebtPriority.CRITICAL for d in debts):
            risks.append("高优先级问题需要谨慎处理")

        return risks if risks else ["风险较低，按计划执行即可"]

    def _identify_benefits(self, debts: List[DebtItem]) -> List[str]:
        """识别收益"""
        benefits = []

        if any(d.debt_type in [DebtType.TODO_COMMENT, DebtType.FIXME_COMMENT, DebtType.HACK_COMMENT] for d in debts):
            benefits.append("清理待办事项，提高代码整洁度")

        if any(d.debt_type == DebtType.CODE_SMELL for d in debts):
            benefits.append("提高代码可读性和可维护性")

        if any(d.debt_type == DebtType.DUPLICATE_CODE for d in debts):
            benefits.append("减少代码冗余，降低维护成本")

        if any(d.debt_type == DebtType.DEPRECATED_API for d in debts):
            benefits.append("使用最新API，提高兼容性")

        if any(d.debt_type == DebtType.MISSING_TESTS for d in debts):
            benefits.append("提高代码可靠性，减少回归风险")

        if any(d.debt_type == DebtType.MISSING_DOCUMENTATION for d in debts):
            benefits.append("提高代码可理解性，便于团队协作")

        total_impact = sum(d.impact_score for d in debts)
        benefits.append(f"预计提升代码质量评分 {total_impact:.1f} 分")

        return benefits

    def _estimate_timeline(self, phases: Dict[str, List[RepaymentTask]]) -> Dict[str, Any]:
        """估算时间线"""
        phase_estimates = {
            "immediate": {"min_days": 1, "max_days": 3},
            "short_term": {"min_days": 3, "max_days": 7},
            "medium_term": {"min_days": 7, "max_days": 14},
            "long_term": {"min_days": 14, "max_days": 30}
        }

        timeline = {}
        current_date = datetime.now()

        for phase_name, tasks in phases.items():
            if not tasks:
                continue

            total_effort = sum(t.estimated_effort for t in tasks)
            estimates = phase_estimates[phase_name]

            estimated_days = max(estimates["min_days"], min(total_effort / 2, estimates["max_days"]))

            start_date = current_date
            end_date = current_date + timedelta(days=estimated_days)
            current_date = end_date + timedelta(days=1)

            timeline[phase_name] = {
                "task_count": len(tasks),
                "total_effort": round(total_effort, 2),
                "estimated_days": round(estimated_days, 1),
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d")
            }

        return timeline

    def _generate_recommendations(self, debts: List[DebtItem]) -> List[str]:
        """生成建议"""
        recommendations = []

        by_type: Dict[DebtType, int] = defaultdict(int)
        for debt in debts:
            by_type[debt.debt_type] += 1

        if by_type.get(DebtType.TODO_COMMENT, 0) > 10:
            recommendations.append("TODO注释过多，建议定期清理和评估")

        if by_type.get(DebtType.FIXME_COMMENT, 0) > 5:
            recommendations.append("存在较多FIXME标记，建议优先处理已知问题")

        if by_type.get(DebtType.HACK_COMMENT, 0) > 0:
            recommendations.append("发现临时方案代码，建议寻找更优雅的解决方案")

        if by_type.get(DebtType.CODE_SMELL, 0) > 5:
            recommendations.append("建议优先处理代码异味问题，提高代码质量")

        if by_type.get(DebtType.DUPLICATE_CODE, 0) > 0:
            recommendations.append("发现重复代码，建议提取公共组件")

        if by_type.get(DebtType.DEPRECATED_API, 0) > 0:
            recommendations.append("存在废弃API使用，建议迁移到新API")

        if by_type.get(DebtType.MISSING_TESTS, 0) > 10:
            recommendations.append("测试覆盖率不足，建议制定测试补充计划")

        if by_type.get(DebtType.MISSING_DOCUMENTATION, 0) > 10:
            recommendations.append("文档缺失较多，建议逐步补充关键模块文档")

        critical_count = sum(1 for d in debts if d.priority == DebtPriority.CRITICAL)
        if critical_count > 0:
            recommendations.append(f"存在 {critical_count} 个严重问题，建议立即处理")

        if not recommendations:
            recommendations.append("技术债务状况良好，继续保持代码质量")

        return recommendations


class ReportGenerator:
    """报告生成器"""

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)

    def generate_json_report(self, report: DebtTrackerReport) -> str:
        """生成JSON格式报告"""
        return json.dumps(report.to_dict(), ensure_ascii=False, indent=2)

    def generate_markdown_report(self, report: DebtTrackerReport) -> str:
        """生成Markdown格式报告"""
        lines = []

        lines.append("# 技术债务追踪报告")
        lines.append("")
        lines.append(f"**项目**: {report.project}")
        lines.append(f"**生成时间**: {report.timestamp}")
        lines.append("")

        lines.append("## 📊 概览")
        lines.append("")
        lines.append(f"| 指标 | 数值 |")
        lines.append(f"|------|------|")
        lines.append(f"| 总债务数 | {report.total_debts} |")
        lines.append(f"| 未解决 | {report.open_debts} |")
        lines.append(f"| 已解决 | {report.resolved_debts} |")
        lines.append(f"| 健康评分 | {report.trends.get('health_score', 0):.1f} |")
        lines.append(f"| 总影响分 | {report.summary['total_impact']:.1f} |")
        lines.append(f"| 总工作量 | {report.summary['total_effort']:.1f} 人天 |")
        lines.append("")

        lines.append("## 📈 按类型统计")
        lines.append("")
        lines.append("| 债务类型 | 数量 |")
        lines.append("|----------|------|")
        for debt_type, count in sorted(report.summary['by_type'].items(), key=lambda x: -x[1]):
            lines.append(f"| {debt_type} | {count} |")
        lines.append("")

        lines.append("## 🔥 按优先级统计")
        lines.append("")
        lines.append("| 优先级 | 数量 |")
        lines.append("|--------|------|")
        priority_icons = {
            "critical": "🔴",
            "high": "🟠",
            "medium": "🟡",
            "low": "🔵",
            "trivial": "⚪"
        }
        for priority, count in report.summary['by_priority'].items():
            icon = priority_icons.get(priority, "⚪")
            lines.append(f"| {icon} {priority.upper()} | {count} |")
        lines.append("")

        lines.append("## 📁 债务最多的文件")
        lines.append("")
        lines.append("| 文件 | 债务数 |")
        lines.append("|------|--------|")
        for file_name, count in report.summary['top_debt_files'][:10]:
            lines.append(f"| {file_name} | {count} |")
        lines.append("")

        if report.repayment_plan:
            plan = report.repayment_plan
            lines.append("## 📋 偿还计划")
            lines.append("")
            lines.append(f"- **总任务数**: {plan.total_debt_count}")
            lines.append(f"- **预计工作量**: {plan.total_effort:.1f} 人天")
            lines.append(f"- **预期影响**: {plan.total_impact:.1f} 分")
            lines.append("")

            for phase_name, tasks in plan.phases.items():
                if tasks:
                    phase_names = {
                        "immediate": "🚨 立即处理",
                        "short_term": "⏰ 短期处理",
                        "medium_term": "📅 中期处理",
                        "long_term": "🕐 长期处理"
                    }
                    lines.append(f"### {phase_names.get(phase_name, phase_name)} ({len(tasks)} 个任务)")
                    lines.append("")

                    for task in tasks[:5]:
                        lines.append(f"#### {task.title}")
                        lines.append("")
                        lines.append(f"- **描述**: {task.description}")
                        lines.append(f"- **工作量**: {task.estimated_effort:.1f} 人天")
                        lines.append(f"- **影响**: {task.impact_score:.1f}")
                        lines.append("")

                        if task.steps:
                            lines.append("**解决步骤**:")
                            lines.append("")
                            for i, step in enumerate(task.steps, 1):
                                lines.append(f"{i}. {step}")
                            lines.append("")

                        if task.benefits:
                            lines.append("**预期收益**:")
                            lines.append("")
                            for benefit in task.benefits:
                                lines.append(f"- {benefit}")
                            lines.append("")

            if plan.timeline:
                lines.append("### ⏱️ 时间线")
                lines.append("")
                lines.append("| 阶段 | 开始日期 | 结束日期 | 预计天数 |")
                lines.append("|------|----------|----------|----------|")
                for phase, info in plan.timeline.items():
                    lines.append(f"| {phase} | {info['start_date']} | {info['end_date']} | {info['estimated_days']} |")
                lines.append("")

            if plan.recommendations:
                lines.append("### 💡 建议")
                lines.append("")
                for i, rec in enumerate(plan.recommendations, 1):
                    lines.append(f"{i}. {rec}")
                lines.append("")

        open_debts = [d for d in report.debts if d.status != DebtStatus.RESOLVED]
        if open_debts:
            lines.append("## 📝 待处理债务详情")
            lines.append("")

            sorted_debts = sorted(
                open_debts,
                key=lambda d: (
                    -{"critical": 5, "high": 4, "medium": 3, "low": 2, "trivial": 1}.get(d.priority.value, 0),
                    -d.impact_score
                )
            )

            for i, debt in enumerate(sorted_debts[:20], 1):
                icon = priority_icons.get(debt.priority.value, "⚪")
                lines.append(f"### {i}. {icon} [{debt.priority.value.upper()}] {debt.debt_type.value}")
                lines.append("")
                lines.append(f"- **文件**: `{Path(debt.file_path).name}:{debt.line_start}`")
                lines.append(f"- **描述**: {debt.description}")
                lines.append(f"- **影响**: {debt.impact_score:.1f} | **工作量**: {debt.effort_estimate:.1f}")

                if debt.suggested_fix:
                    lines.append(f"- **建议修复**: {debt.suggested_fix}")

                if debt.comment_text:
                    lines.append(f"- **注释内容**: {debt.comment_text}")

                lines.append("")

        if report.trend_history:
            lines.append("## 📊 趋势分析")
            lines.append("")
            lines.append("| 日期 | 总债务 | 新增 | 已解决 | 健康评分 |")
            lines.append("|------|--------|------|--------|----------|")
            for trend in report.trend_history[-10:]:
                lines.append(f"| {trend.date} | {trend.total_debts} | {trend.new_debts} | {trend.resolved_debts} | {trend.health_score:.1f} |")
            lines.append("")

        lines.append("---")
        lines.append(f"*报告由技术债务追踪器自动生成*")

        return '\n'.join(lines)


class TechDebtTracker:
    """技术债务追踪器主类"""

    def __init__(
        self,
        project_root: Optional[Path] = None,
        storage_path: Optional[Path] = None,
        logger: Optional[logging.Logger] = None
    ):
        self.project_root = project_root or Path.cwd()
        self.logger = logger or logging.getLogger(__name__)

        self.detectors: List[IDebtDetector] = [
            TodoCommentDetector(logger),
            DeprecatedAPIDetector(logger),
            CodeSmellDetector(logger),
            DuplicateCodeDetector(logger),
            MissingTestDetector(logger),
            MissingDocDetector(logger)
        ]

        self.state_manager = DebtStateManager(storage_path, logger)
        self.plan_generator = RepaymentPlanGenerator(logger)
        self.report_generator = ReportGenerator(logger)

        self._debts: List[DebtItem] = []

    def scan(self) -> List[DebtItem]:
        """扫描项目技术债务"""
        self.logger.info(f"开始扫描项目: {self.project_root}")

        existing_debts = self.state_manager.load()

        python_files = self._collect_python_files()
        self.logger.info(f"找到 {len(python_files)} 个Python文件")

        all_debts: List[DebtItem] = []

        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                for detector in self.detectors:
                    debts = detector.detect(py_file, content)
                    all_debts.extend(debts)

            except Exception as e:
                self.logger.warning(f"扫描文件失败 {py_file}: {e}")

        self._debts = self.state_manager.merge_debts(all_debts)
        self.state_manager.record_trend(self._debts)
        self.state_manager.save(self._debts)

        self.logger.info(f"扫描完成，发现 {len(self._debts)} 条技术债务")
        return self._debts

    def _collect_python_files(self) -> List[Path]:
        """收集Python文件"""
        python_files: List[Path] = []

        exclude_dirs = {
            '__pycache__', '.git', '.venv', 'venv', 'node_modules',
            '.pytest_cache', 'build', 'dist', '.tox', '.mypy_cache'
        }

        for py_file in self.project_root.rglob("*.py"):
            if not any(excluded in py_file.parts for excluded in exclude_dirs):
                python_files.append(py_file)

        return python_files

    def generate_report(self, project: str = "default", generate_plan: bool = True) -> DebtTrackerReport:
        """生成报告"""
        if not self._debts:
            self.scan()

        open_debts = [d for d in self._debts if d.status not in [DebtStatus.RESOLVED, DebtStatus.WONT_FIX]]
        resolved_debts = [d for d in self._debts if d.status == DebtStatus.RESOLVED]

        summary = self._calculate_summary()
        trends = self._calculate_trends()

        repayment_plan = None
        if generate_plan and open_debts:
            repayment_plan = self.plan_generator.generate(open_debts, project)

        return DebtTrackerReport(
            timestamp=datetime.now().isoformat(),
            project=project,
            total_debts=len(self._debts),
            open_debts=len(open_debts),
            resolved_debts=len(resolved_debts),
            debts=self._debts,
            summary=summary,
            repayment_plan=repayment_plan,
            trends=trends,
            trend_history=self.state_manager._trend_history
        )

    def _calculate_summary(self) -> Dict[str, Any]:
        """计算摘要"""
        by_type: Dict[str, int] = defaultdict(int)
        by_priority: Dict[str, int] = defaultdict(int)
        by_status: Dict[str, int] = defaultdict(int)
        by_category: Dict[str, int] = defaultdict(int)

        total_impact = 0.0
        total_effort = 0.0

        for debt in self._debts:
            by_type[debt.debt_type.value] += 1
            by_priority[debt.priority.value] += 1
            by_status[debt.status.value] += 1
            by_category[debt.category.value] += 1
            total_impact += debt.impact_score
            total_effort += debt.effort_estimate

        file_debt_counts: Dict[str, int] = defaultdict(int)
        for debt in self._debts:
            file_debt_counts[debt.file_path] += 1

        top_files = sorted(
            file_debt_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]

        return {
            "by_type": dict(by_type),
            "by_priority": dict(by_priority),
            "by_status": dict(by_status),
            "by_category": dict(by_category),
            "total_impact": round(total_impact, 2),
            "total_effort": round(total_effort, 2),
            "top_debt_files": [(Path(f).name, c) for f, c in top_files]
        }

    def _calculate_trends(self) -> Dict[str, Any]:
        """计算趋势"""
        resolved_count = sum(1 for d in self._debts if d.status == DebtStatus.RESOLVED)
        in_progress_count = sum(1 for d in self._debts if d.status == DebtStatus.IN_PROGRESS)

        resolution_rate = (resolved_count / len(self._debts) * 100) if self._debts else 0

        return {
            "total_identified": len(self._debts),
            "resolved_count": resolved_count,
            "in_progress_count": in_progress_count,
            "resolution_rate": round(resolution_rate, 2),
            "health_score": round(max(0, 100 - (len(self._debts) - resolved_count) * 2), 2)
        }

    def update_debt_status(
        self,
        debt_id: str,
        new_status: DebtStatus,
        notes: str = ""
    ) -> Optional[DebtItem]:
        """更新债务状态"""
        debt = self.state_manager.update_status(debt_id, new_status, notes)
        if debt:
            self.state_manager.save(self._debts)
        return debt

    def save_report(self, report: DebtTrackerReport, output_path: Path, format: str = "json") -> bool:
        """保存报告"""
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

    def print_report(self, report: DebtTrackerReport) -> None:
        """打印报告"""
        print("\n" + "=" * 80)
        print("技术债务追踪报告")
        print("=" * 80)
        print(f"项目: {report.project}")
        print(f"时间: {report.timestamp}")
        print(f"\n总债务数: {report.total_debts}")
        print(f"未解决: {report.open_debts}")
        print(f"已解决: {report.resolved_debts}")

        summary = report.summary
        print(f"\n健康评分: {report.trends.get('health_score', 0):.1f}")
        print(f"总影响分: {summary['total_impact']:.1f}")
        print(f"总工作量: {summary['total_effort']:.1f} 人天")

        print(f"\n按类型统计:")
        for debt_type, count in sorted(summary['by_type'].items(), key=lambda x: -x[1]):
            print(f"  {debt_type}: {count}")

        print(f"\n按优先级统计:")
        for priority, count in summary['by_priority'].items():
            print(f"  {priority}: {count}")

        print(f"\n按状态统计:")
        for status, count in summary['by_status'].items():
            print(f"  {status}: {count}")

        if summary['top_debt_files']:
            print(f"\n债务最多的文件:")
            for file_name, count in summary['top_debt_files'][:5]:
                print(f"  {file_name}: {count} 项")

        if report.repayment_plan:
            plan = report.repayment_plan
            print(f"\n" + "-" * 80)
            print("偿还计划")
            print("-" * 80)

            for phase_name, tasks in plan.phases.items():
                if tasks:
                    print(f"\n{phase_name.upper()} 阶段 ({len(tasks)} 个任务):")
                    for task in tasks[:5]:
                        print(f"  - {task.title}")
                        print(f"    工作量: {task.estimated_effort:.1f} 人天 | 影响: {task.impact_score:.1f}")

            if plan.timeline:
                print(f"\n时间线:")
                for phase, info in plan.timeline.items():
                    print(f"  {phase}: {info['start_date']} - {info['end_date']} ({info['estimated_days']} 天)")

            if plan.recommendations:
                print(f"\n建议:")
                for i, rec in enumerate(plan.recommendations, 1):
                    print(f"  {i}. {rec}")

        open_debts = [d for d in report.debts if d.status != DebtStatus.RESOLVED]
        if open_debts:
            print(f"\n" + "-" * 80)
            print("待处理债务 (前10项)")
            print("-" * 80)

            sorted_debts = sorted(
                open_debts,
                key=lambda d: (
                    -{"critical": 5, "high": 4, "medium": 3, "low": 2, "trivial": 1}.get(d.priority.value, 0),
                    -d.impact_score
                )
            )

            for i, debt in enumerate(sorted_debts[:10], 1):
                priority_icons = {
                    DebtPriority.CRITICAL: "🔴",
                    DebtPriority.HIGH: "🟠",
                    DebtPriority.MEDIUM: "🟡",
                    DebtPriority.LOW: "🔵",
                    DebtPriority.TRIVIAL: "⚪"
                }
                icon = priority_icons.get(debt.priority, "⚪")
                print(f"\n{i}. {icon} [{debt.priority.value.upper()}] {debt.debt_type.value}")
                print(f"   文件: {Path(debt.file_path).name}:{debt.line_start}")
                print(f"   描述: {debt.description}")
                print(f"   影响: {debt.impact_score:.1f} | 工作量: {debt.effort_estimate:.1f}")
                if debt.suggested_fix:
                    print(f"   建议: {debt.suggested_fix}")


def setup_logger(verbose: bool = False) -> logging.Logger:
    """配置日志记录器"""
    logger = logging.getLogger("TechDebtTracker")
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
        description="技术债务追踪器 (增强版)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python tech_debt_tracker.py
  python tech_debt_tracker.py --project myproject --output json
  python tech_debt_tracker.py --generate-plan --output-file report.json
  python tech_debt_tracker.py --report-format markdown --output-file debt_report.md
        """
    )

    parser.add_argument(
        "--project",
        type=str,
        default="default",
        help="项目名称 (默认: default)"
    )

    parser.add_argument(
        "--project-root",
        type=str,
        help="项目根目录"
    )

    parser.add_argument(
        "--storage-file",
        type=str,
        help="债务存储文件路径"
    )

    parser.add_argument(
        "--generate-plan",
        action="store_true",
        help="生成偿还计划"
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
    print("技术债务追踪器 (增强版)")
    print("=" * 80)

    project_root = Path(args.project_root) if args.project_root else Path.cwd()
    storage_path = Path(args.storage_file) if args.storage_file else None

    tracker = TechDebtTracker(
        project_root=project_root,
        storage_path=storage_path,
        logger=logger
    )

    report = tracker.generate_report(
        project=args.project,
        generate_plan=args.generate_plan
    )

    if args.output == "console":
        tracker.print_report(report)

    if args.output in ["json", "markdown"] or args.output_file:
        output_format = args.output if args.output in ["json", "markdown"] else "json"

        if args.output_file:
            output_path = Path(args.output_file)
            tracker.save_report(report, output_path, output_format)
            print(f"\n报告已保存到: {output_path}")
        else:
            if output_format == "json":
                print("\nJSON 输出:")
                print(tracker.report_generator.generate_json_report(report))
            else:
                print("\nMarkdown 输出:")
                print(tracker.report_generator.generate_markdown_report(report))

    return 0 if report.open_debts == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
