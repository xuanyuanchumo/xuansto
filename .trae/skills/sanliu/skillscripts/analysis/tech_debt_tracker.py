#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
技术债务追踪器

实现债务识别（代码异味、重复代码、过时依赖等）、债务状态追踪、偿还计划生成。
支持债务优先级排序和债务影响分析。

使用示例:
    python tech_debt_tracker.py
    python tech_debt_tracker.py --project myproject --output json
    python tech_debt_tracker.py --generate-plan --priority-threshold 0.7
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

from skillscripts.utils.path_config_manager import PathConfigManager


class DebtType(Enum):
    """技术债务类型"""
    CODE_SMELL = "code_smell"
    DUPLICATE_CODE = "duplicate_code"
    OUTDATED_DEPENDENCY = "outdated_dependency"
    VULNERABLE_DEPENDENCY = "vulnerable_dependency"
    MISSING_DOCUMENTATION = "missing_documentation"
    MISSING_TESTS = "missing_tests"
    COMPLEX_CODE = "complex_code"
    SECURITY_ISSUE = "security_issue"
    PERFORMANCE_ISSUE = "performance_issue"
    ARCHITECTURE_VIOLATION = "architecture_violation"
    DEPRECATED_API = "deprecated_api"
    TODO_COMMENT = "todo_comment"
    FIXME_COMMENT = "fixme_comment"
    HARDCODED_VALUE = "hardcoded_value"
    MAGIC_NUMBER = "magic_number"
    LONG_FILE = "long_file"


class DebtStatus(Enum):
    """债务状态"""
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
            "resolution_notes": self.resolution_notes
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
            "trends": self.trends
        }


class IDebtDetector(ABC):
    """债务检测器接口"""

    @abstractmethod
    def detect(self, file_path: Path, content: str) -> List[DebtItem]:
        pass

    @abstractmethod
    def get_debt_type(self) -> DebtType:
        pass


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
                        status=DebtStatus.IDENTIFIED,
                        file_path=file_path,
                        line_start=line_start,
                        line_end=line_end,
                        description=f"方法过长: {node.name} ({line_count} 行)",
                        impact_score=min(line_count / 10, 10),
                        effort_estimate=line_count / 20,
                        created_at=timestamp,
                        updated_at=timestamp,
                        tags=["long-method", "refactoring"],
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
                        status=DebtStatus.IDENTIFIED,
                        file_path=file_path,
                        line_start=line_start,
                        line_end=line_end,
                        description=f"类过大: {node.name} ({class_lines} 行)",
                        impact_score=min(class_lines / 20, 10),
                        effort_estimate=class_lines / 30,
                        created_at=timestamp,
                        updated_at=timestamp,
                        tags=["large-class", "refactoring"],
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
                        status=DebtStatus.IDENTIFIED,
                        file_path=file_path,
                        line_start=node.lineno,
                        line_end=node.lineno,
                        description=f"参数列表过长: {node.name} ({param_count} 个参数)",
                        impact_score=param_count / 2,
                        effort_estimate=2.0,
                        created_at=timestamp,
                        updated_at=timestamp,
                        tags=["long-parameter-list", "refactoring"],
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
                    status=DebtStatus.IDENTIFIED,
                    file_path=file_path,
                    line_start=node.lineno,
                    line_end=getattr(node, 'end_lineno', node.lineno) or node.lineno,
                    description=f"嵌套过深: {depth} 层",
                    impact_score=depth,
                    effort_estimate=depth / 2,
                    created_at=timestamp,
                    updated_at=timestamp,
                    tags=["deep-nesting", "refactoring"],
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
                        status=DebtStatus.IDENTIFIED,
                        file_path=file_path,
                        line_start=node.lineno,
                        line_end=getattr(node, 'end_lineno', node.lineno) or node.lineno,
                        description=f"圈复杂度过高: {node.name} (复杂度: {visitor.complexity})",
                        impact_score=visitor.complexity / 2,
                        effort_estimate=visitor.complexity / 5,
                        created_at=timestamp,
                        updated_at=timestamp,
                        tags=["high-complexity", "refactoring"],
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
                    status=DebtStatus.IDENTIFIED,
                    file_path=str(file_path),
                    line_start=first_loc[0],
                    line_end=first_loc[1],
                    description=f"重复代码块: 发现 {len(locations)} 处相似代码",
                    impact_score=len(locations) * 2,
                    effort_estimate=len(locations) * 0.5,
                    created_at=timestamp,
                    updated_at=timestamp,
                    tags=["duplicate-code", "refactoring"],
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
                            status=DebtStatus.IDENTIFIED,
                            file_path=str(file_path),
                            line_start=node.lineno,
                            line_end=node.lineno,
                            description=f"缺少测试: 方法 {node.name}",
                            impact_score=3.0,
                            effort_estimate=1.0,
                            created_at=timestamp,
                            updated_at=timestamp,
                            tags=["missing-test", "testing"],
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
                            status=DebtStatus.IDENTIFIED,
                            file_path=str(file_path),
                            line_start=node.lineno,
                            line_end=node.lineno,
                            description=f"缺少文档: 类 {node.name}",
                            impact_score=2.0,
                            effort_estimate=0.5,
                            created_at=timestamp,
                            updated_at=timestamp,
                            tags=["missing-doc", "documentation"],
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
                            status=DebtStatus.IDENTIFIED,
                            file_path=str(file_path),
                            line_start=node.lineno,
                            line_end=node.lineno,
                            description=f"缺少文档: 方法 {node.name}",
                            impact_score=1.0,
                            effort_estimate=0.25,
                            created_at=timestamp,
                            updated_at=timestamp,
                            tags=["missing-doc", "documentation"],
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
                    resolution_notes=item.get("resolution_notes", "")
                )
                self._debts[debt.debt_id] = debt

            self.logger.info(f"加载了 {len(self._debts)} 条债务记录")
            return self._debts
        except Exception as e:
            self.logger.error(f"加载债务记录失败: {e}")
            return {}

    def save(self, debts: List[DebtItem]) -> bool:
        """保存债务记录"""
        if not self.storage_path:
            return True

        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)

            data = {
                "debts": [d.to_dict() for d in debts],
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
                    existing.status = DebtStatus.IDENTIFIED
                    existing.resolved_at = None
            else:
                self._debts[debt.debt_id] = debt

        return list(self._debts.values())


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

        if any(d.priority == DebtPriority.CRITICAL for d in debts):
            risks.append("高优先级问题需要谨慎处理")

        return risks if risks else ["风险较低，按计划执行即可"]

    def _identify_benefits(self, debts: List[DebtItem]) -> List[str]:
        """识别收益"""
        benefits = []

        if any(d.debt_type == DebtType.CODE_SMELL for d in debts):
            benefits.append("提高代码可读性和可维护性")

        if any(d.debt_type == DebtType.DUPLICATE_CODE for d in debts):
            benefits.append("减少代码冗余，降低维护成本")

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

        if by_type.get(DebtType.CODE_SMELL, 0) > 5:
            recommendations.append("建议优先处理代码异味问题，提高代码质量")

        if by_type.get(DebtType.DUPLICATE_CODE, 0) > 0:
            recommendations.append("发现重复代码，建议提取公共组件")

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


class TechDebtTracker:
    """技术债务追踪器主类"""

    def __init__(
        self,
        project_root: Optional[Path] = None,
        storage_path: Optional[Path] = None,
        logger: Optional[logging.Logger] = None
    ):
        self.path_manager = PathConfigManager(auto_detect=True)
        self.project_root = project_root or self.path_manager.get_project_root()
        self.logger = logger or logging.getLogger(__name__)

        self.detectors: List[IDebtDetector] = [
            CodeSmellDetector(logger),
            DuplicateCodeDetector(logger),
            MissingTestDetector(logger),
            MissingDocDetector(logger)
        ]

        if storage_path:
            self.storage_path = storage_path
        else:
            self.storage_path = self.path_manager.get_data_path() / "tech_debt" / "debts.json"

        self.state_manager = DebtStateManager(self.storage_path, logger)
        self.plan_generator = RepaymentPlanGenerator(logger)

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
            trends=trends
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

    def save_report(self, report: DebtTrackerReport, output_path: Path) -> bool:
        """保存报告"""
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)

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
        description="技术债务追踪器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python tech_debt_tracker.py
  python tech_debt_tracker.py --project myproject --output json
  python tech_debt_tracker.py --generate-plan --output-file report.json
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
        choices=["console", "json"],
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
    path_manager = PathConfigManager(auto_detect=True)

    print("=" * 80)
    print("技术债务追踪器")
    print("=" * 80)

    project_root = Path(args.project_root) if args.project_root else path_manager.get_project_root()
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

    if args.output == "json" or args.output_file:
        output_data = report.to_dict()
        output_json = json.dumps(output_data, ensure_ascii=False, indent=2)

        if args.output_file:
            output_path = Path(args.output_file)
        else:
            output_path = path_manager.get_docs_reports_path() / f"tech_debt_report_{args.project}.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(output_json)
        print(f"\n报告已保存到: {output_path}")

    return 0 if report.open_debts == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
