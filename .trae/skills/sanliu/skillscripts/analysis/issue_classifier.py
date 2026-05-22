#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
问题分类器模块 - Issue Classifier

智能问题分类系统，包括：
- 问题分类体系（语法、运行时、逻辑、性能、安全、风格等）
- 问题优先级评估（基于影响范围、严重程度、修复难度）
- 问题关联分析（识别相关问题、构建问题依赖图）

使用示例:
    python issue_classifier.py --input issues.json --output classified_issues.json
    python issue_classifier.py --analyze-dependencies
"""

import json
import logging
import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


class IssueCategory(Enum):
    SYNTAX = "syntax"
    RUNTIME = "runtime"
    LOGIC = "logic"
    PERFORMANCE = "performance"
    SECURITY = "security"
    STYLE = "style"
    DEPENDENCY = "dependency"
    CONFIGURATION = "config"
    COMPATIBILITY = "compatibility"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    ARCHITECTURE = "architecture"


class IssuePriority(Enum):
    P0_CRITICAL = "P0"
    P1_HIGH = "P1"
    P2_MEDIUM = "P2"
    P3_LOW = "P3"
    P4_INFO = "P4"


class IssueSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class IssueStatus(Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    WONT_FIX = "wont_fix"
    DUPLICATE = "duplicate"


class ImpactScope(Enum):
    SYSTEM_WIDE = "system_wide"
    MODULE = "module"
    COMPONENT = "component"
    FUNCTION = "function"
    LOCAL = "local"


class FixDifficulty(Enum):
    TRIVIAL = "trivial"
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    MAJOR = "major"


@dataclass
class ClassificationRule:
    rule_id: str
    category: IssueCategory
    patterns: List[str]
    keywords: List[str]
    severity_base: IssueSeverity
    confidence: float = 0.8
    description: str = ""
    examples: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "category": self.category.value,
            "patterns": self.patterns,
            "keywords": self.keywords,
            "severity_base": self.severity_base.value,
            "confidence": self.confidence,
            "description": self.description,
            "examples": self.examples
        }


@dataclass
class IssueRelation:
    source_id: str
    target_id: str
    relation_type: str
    strength: float
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relation_type": self.relation_type,
            "strength": self.strength,
            "description": self.description
        }


@dataclass
class DependencyNode:
    issue_id: str
    depends_on: List[str]
    depended_by: List[str]
    level: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "issue_id": self.issue_id,
            "depends_on": self.depends_on,
            "depended_by": self.depended_by,
            "level": self.level
        }


@dataclass
class ClassifiedIssue:
    issue_id: str
    title: str
    description: str
    category: IssueCategory
    severity: IssueSeverity
    priority: IssuePriority
    status: IssueStatus
    impact_scope: ImpactScope
    fix_difficulty: FixDifficulty
    file_path: str = ""
    line_number: int = 0
    code_snippet: str = ""
    tags: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    related_issues: List[str] = field(default_factory=list)
    confidence: float = 0.0
    impact_score: float = 0.0
    effort_score: float = 0.0
    created_at: str = ""
    updated_at: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "issue_id": self.issue_id,
            "title": self.title,
            "description": self.description,
            "category": self.category.value,
            "severity": self.severity.value,
            "priority": self.priority.value,
            "status": self.status.value,
            "impact_scope": self.impact_scope.value,
            "fix_difficulty": self.fix_difficulty.value,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "code_snippet": self.code_snippet,
            "tags": self.tags,
            "suggestions": self.suggestions,
            "related_issues": self.related_issues,
            "confidence": self.confidence,
            "impact_score": round(self.impact_score, 2),
            "effort_score": round(self.effort_score, 2),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata
        }


@dataclass
class ClassificationResult:
    timestamp: str
    total_issues: int
    classified_issues: List[ClassifiedIssue]
    by_category: Dict[str, int]
    by_priority: Dict[str, int]
    by_severity: Dict[str, int]
    by_status: Dict[str, int]
    dependency_graph: Dict[str, DependencyNode]
    relations: List[IssueRelation]
    summary: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "total_issues": self.total_issues,
            "classified_issues": [i.to_dict() for i in self.classified_issues],
            "by_category": self.by_category,
            "by_priority": self.by_priority,
            "by_severity": self.by_severity,
            "by_status": self.by_status,
            "dependency_graph": {k: v.to_dict() for k, v in self.dependency_graph.items()},
            "relations": [r.to_dict() for r in self.relations],
            "summary": self.summary
        }


class ClassificationRules:
    SYNTAX_RULES = [
        ClassificationRule(
            rule_id="SYN001",
            category=IssueCategory.SYNTAX,
            patterns=[r"SyntaxError", r"IndentationError", r"TabError"],
            keywords=["syntax", "parse error", "unexpected token"],
            severity_base=IssueSeverity.HIGH,
            description="语法错误"
        ),
        ClassificationRule(
            rule_id="SYN002",
            category=IssueCategory.SYNTAX,
            patterns=[r"missing.*parenthes", r"missing.*bracket", r"unterminated string"],
            keywords=["missing", "unterminated"],
            severity_base=IssueSeverity.HIGH,
            description="语法结构不完整"
        ),
    ]

    RUNTIME_RULES = [
        ClassificationRule(
            rule_id="RUN001",
            category=IssueCategory.RUNTIME,
            patterns=[r"TypeError", r"AttributeError", r"NameError"],
            keywords=["type", "attribute", "name", "undefined"],
            severity_base=IssueSeverity.HIGH,
            description="运行时类型错误"
        ),
        ClassificationRule(
            rule_id="RUN002",
            category=IssueCategory.RUNTIME,
            patterns=[r"IndexError", r"KeyError", r"ValueError"],
            keywords=["index", "key", "value", "out of range"],
            severity_base=IssueSeverity.MEDIUM,
            description="运行时数据访问错误"
        ),
        ClassificationRule(
            rule_id="RUN003",
            category=IssueCategory.RUNTIME,
            patterns=[r"ZeroDivisionError", r"OverflowError", r"ArithmeticError"],
            keywords=["division", "overflow", "arithmetic"],
            severity_base=IssueSeverity.MEDIUM,
            description="运行时算术错误"
        ),
        ClassificationRule(
            rule_id="RUN004",
            category=IssueCategory.RUNTIME,
            patterns=[r"MemoryError", r"RecursionError", r"RuntimeError"],
            keywords=["memory", "recursion", "runtime"],
            severity_base=IssueSeverity.HIGH,
            description="运行时资源错误"
        ),
    ]

    LOGIC_RULES = [
        ClassificationRule(
            rule_id="LOG001",
            category=IssueCategory.LOGIC,
            patterns=[r"AssertionError", r"assert failed", r"logic error"],
            keywords=["assertion", "logic", "unexpected", "incorrect"],
            severity_base=IssueSeverity.MEDIUM,
            description="逻辑断言失败"
        ),
        ClassificationRule(
            rule_id="LOG002",
            category=IssueCategory.LOGIC,
            patterns=[r"infinite loop", r"dead code", r"unreachable"],
            keywords=["infinite", "dead code", "unreachable"],
            severity_base=IssueSeverity.MEDIUM,
            description="逻辑流程问题"
        ),
        ClassificationRule(
            rule_id="LOG003",
            category=IssueCategory.LOGIC,
            patterns=[r"race condition", r"deadlock", r"concurrent"],
            keywords=["race", "deadlock", "concurrent", "thread"],
            severity_base=IssueSeverity.HIGH,
            description="并发逻辑问题"
        ),
    ]

    PERFORMANCE_RULES = [
        ClassificationRule(
            rule_id="PERF001",
            category=IssueCategory.PERFORMANCE,
            patterns=[r"TimeoutError", r"timeout", r"slow"],
            keywords=["timeout", "slow", "performance", "latency"],
            severity_base=IssueSeverity.MEDIUM,
            description="性能超时问题"
        ),
        ClassificationRule(
            rule_id="PERF002",
            category=IssueCategory.PERFORMANCE,
            patterns=[r"O\(n\^2\)", r"O\(n\^3\)", r"inefficient", r"bottleneck"],
            keywords=["complexity", "inefficient", "bottleneck", "optimize"],
            severity_base=IssueSeverity.MEDIUM,
            description="算法复杂度问题"
        ),
        ClassificationRule(
            rule_id="PERF003",
            category=IssueCategory.PERFORMANCE,
            patterns=[r"memory leak", r"high memory", r"memory usage"],
            keywords=["memory leak", "memory usage", "allocation"],
            severity_base=IssueSeverity.HIGH,
            description="内存性能问题"
        ),
    ]

    SECURITY_RULES = [
        ClassificationRule(
            rule_id="SEC001",
            category=IssueCategory.SECURITY,
            patterns=[r"SQL injection", r"XSS", r"CSRF", r"injection"],
            keywords=["injection", "xss", "csrf", "security"],
            severity_base=IssueSeverity.CRITICAL,
            description="安全注入漏洞"
        ),
        ClassificationRule(
            rule_id="SEC002",
            category=IssueCategory.SECURITY,
            patterns=[r"hardcoded.*password", r"hardcoded.*secret", r"hardcoded.*key"],
            keywords=["hardcoded", "password", "secret", "credential"],
            severity_base=IssueSeverity.CRITICAL,
            description="硬编码敏感信息"
        ),
        ClassificationRule(
            rule_id="SEC003",
            category=IssueCategory.SECURITY,
            patterns=[r"PermissionError", r"AccessDenied", r"Unauthorized"],
            keywords=["permission", "access", "unauthorized", "forbidden"],
            severity_base=IssueSeverity.HIGH,
            description="权限安全问题"
        ),
        ClassificationRule(
            rule_id="SEC004",
            category=IssueCategory.SECURITY,
            patterns=[r"eval\(", r"exec\(", r"__import__"],
            keywords=["eval", "exec", "dynamic code"],
            severity_base=IssueSeverity.HIGH,
            description="动态代码执行风险"
        ),
    ]

    STYLE_RULES = [
        ClassificationRule(
            rule_id="STY001",
            category=IssueCategory.STYLE,
            patterns=[r"line too long", r"E501", r"max line length"],
            keywords=["line length", "formatting", "style"],
            severity_base=IssueSeverity.LOW,
            description="代码行长度问题"
        ),
        ClassificationRule(
            rule_id="STY002",
            category=IssueCategory.STYLE,
            patterns=[r"unused import", r"unused variable", r"F401", r"F841"],
            keywords=["unused", "import", "variable"],
            severity_base=IssueSeverity.LOW,
            description="未使用的代码元素"
        ),
        ClassificationRule(
            rule_id="STY003",
            category=IssueCategory.STYLE,
            patterns=[r"naming convention", r"invalid name", r"N801"],
            keywords=["naming", "convention", "style"],
            severity_base=IssueSeverity.LOW,
            description="命名规范问题"
        ),
    ]

    DEPENDENCY_RULES = [
        ClassificationRule(
            rule_id="DEP001",
            category=IssueCategory.DEPENDENCY,
            patterns=[r"ImportError", r"ModuleNotFoundError", r"No module named"],
            keywords=["import", "module", "dependency", "package"],
            severity_base=IssueSeverity.HIGH,
            description="模块导入错误"
        ),
        ClassificationRule(
            rule_id="DEP002",
            category=IssueCategory.DEPENDENCY,
            patterns=[r"version conflict", r"version mismatch", r"incompatible version"],
            keywords=["version", "conflict", "incompatible"],
            severity_base=IssueSeverity.MEDIUM,
            description="依赖版本冲突"
        ),
        ClassificationRule(
            rule_id="DEP003",
            category=IssueCategory.DEPENDENCY,
            patterns=[r"ConnectionError", r"ConnectionRefusedError", r"network"],
            keywords=["connection", "network", "service"],
            severity_base=IssueSeverity.HIGH,
            description="外部依赖连接问题"
        ),
    ]

    CONFIGURATION_RULES = [
        ClassificationRule(
            rule_id="CFG001",
            category=IssueCategory.CONFIGURATION,
            patterns=[r"ConfigError", r"SettingNotFound", r"configuration error"],
            keywords=["config", "setting", "environment"],
            severity_base=IssueSeverity.MEDIUM,
            description="配置错误"
        ),
        ClassificationRule(
            rule_id="CFG002",
            category=IssueCategory.CONFIGURATION,
            patterns=[r"EnvironmentError", r"missing environment", r"env var"],
            keywords=["environment", "env", "variable"],
            severity_base=IssueSeverity.MEDIUM,
            description="环境配置问题"
        ),
    ]

    COMPATIBILITY_RULES = [
        ClassificationRule(
            rule_id="CMP001",
            category=IssueCategory.COMPATIBILITY,
            patterns=[r"not supported", r"incompatible", r"deprecated"],
            keywords=["support", "compatible", "deprecated", "version"],
            severity_base=IssueSeverity.MEDIUM,
            description="兼容性问题"
        ),
        ClassificationRule(
            rule_id="CMP002",
            category=IssueCategory.COMPATIBILITY,
            patterns=[r"Python 2", r"Python 3", r"version.*require"],
            keywords=["python2", "python3", "version"],
            severity_base=IssueSeverity.MEDIUM,
            description="Python版本兼容性"
        ),
    ]

    DOCUMENTATION_RULES = [
        ClassificationRule(
            rule_id="DOC001",
            category=IssueCategory.DOCUMENTATION,
            patterns=[r"missing docstring", r"missing comment", r"undocumented"],
            keywords=["docstring", "documentation", "comment"],
            severity_base=IssueSeverity.LOW,
            description="文档缺失"
        ),
        ClassificationRule(
            rule_id="DOC002",
            category=IssueCategory.DOCUMENTATION,
            patterns=[r"outdated doc", r"doc.*mismatch", r"incorrect doc"],
            keywords=["outdated", "mismatch", "documentation"],
            severity_base=IssueSeverity.LOW,
            description="文档过时或不准确"
        ),
    ]

    TESTING_RULES = [
        ClassificationRule(
            rule_id="TST001",
            category=IssueCategory.TESTING,
            patterns=[r"test failure", r"assertion failed", r"test error"],
            keywords=["test", "assertion", "failure"],
            severity_base=IssueSeverity.MEDIUM,
            description="测试失败"
        ),
        ClassificationRule(
            rule_id="TST002",
            category=IssueCategory.TESTING,
            patterns=[r"missing test", r"no coverage", r"untested"],
            keywords=["coverage", "test", "untested"],
            severity_base=IssueSeverity.LOW,
            description="测试覆盖不足"
        ),
    ]

    ARCHITECTURE_RULES = [
        ClassificationRule(
            rule_id="ARC001",
            category=IssueCategory.ARCHITECTURE,
            patterns=[r"circular dependency", r"circular import", r"cyclic"],
            keywords=["circular", "cyclic", "dependency"],
            severity_base=IssueSeverity.HIGH,
            description="循环依赖"
        ),
        ClassificationRule(
            rule_id="ARC002",
            category=IssueCategory.ARCHITECTURE,
            patterns=[r"violation.*SOLID", r"design pattern", r"architectural"],
            keywords=["solid", "design pattern", "architecture"],
            severity_base=IssueSeverity.MEDIUM,
            description="架构设计问题"
        ),
        ClassificationRule(
            rule_id="ARC003",
            category=IssueCategory.ARCHITECTURE,
            patterns=[r"tight coupling", r"high coupling", r"coupling"],
            keywords=["coupling", "dependency", "tight"],
            severity_base=IssueSeverity.MEDIUM,
            description="耦合度过高"
        ),
    ]

    @classmethod
    def get_all_rules(cls) -> List[ClassificationRule]:
        return (
            cls.SYNTAX_RULES +
            cls.RUNTIME_RULES +
            cls.LOGIC_RULES +
            cls.PERFORMANCE_RULES +
            cls.SECURITY_RULES +
            cls.STYLE_RULES +
            cls.DEPENDENCY_RULES +
            cls.CONFIGURATION_RULES +
            cls.COMPATIBILITY_RULES +
            cls.DOCUMENTATION_RULES +
            cls.TESTING_RULES +
            cls.ARCHITECTURE_RULES
        )

    @classmethod
    def get_rules_by_category(cls, category: IssueCategory) -> List[ClassificationRule]:
        category_map = {
            IssueCategory.SYNTAX: cls.SYNTAX_RULES,
            IssueCategory.RUNTIME: cls.RUNTIME_RULES,
            IssueCategory.LOGIC: cls.LOGIC_RULES,
            IssueCategory.PERFORMANCE: cls.PERFORMANCE_RULES,
            IssueCategory.SECURITY: cls.SECURITY_RULES,
            IssueCategory.STYLE: cls.STYLE_RULES,
            IssueCategory.DEPENDENCY: cls.DEPENDENCY_RULES,
            IssueCategory.CONFIGURATION: cls.CONFIGURATION_RULES,
            IssueCategory.COMPATIBILITY: cls.COMPATIBILITY_RULES,
            IssueCategory.DOCUMENTATION: cls.DOCUMENTATION_RULES,
            IssueCategory.TESTING: cls.TESTING_RULES,
            IssueCategory.ARCHITECTURE: cls.ARCHITECTURE_RULES,
        }
        return category_map.get(category, [])


class PriorityEvaluator:
    SEVERITY_WEIGHTS = {
        IssueSeverity.CRITICAL: 10.0,
        IssueSeverity.HIGH: 7.0,
        IssueSeverity.MEDIUM: 4.0,
        IssueSeverity.LOW: 2.0,
        IssueSeverity.INFO: 1.0
    }

    CATEGORY_WEIGHTS = {
        IssueCategory.SECURITY: 3.0,
        IssueCategory.RUNTIME: 2.5,
        IssueCategory.LOGIC: 2.0,
        IssueCategory.PERFORMANCE: 2.0,
        IssueCategory.DEPENDENCY: 1.8,
        IssueCategory.CONFIGURATION: 1.5,
        IssueCategory.SYNTAX: 1.5,
        IssueCategory.ARCHITECTURE: 1.5,
        IssueCategory.COMPATIBILITY: 1.2,
        IssueCategory.TESTING: 1.0,
        IssueCategory.DOCUMENTATION: 0.8,
        IssueCategory.STYLE: 0.5
    }

    IMPACT_SCOPE_WEIGHTS = {
        ImpactScope.SYSTEM_WIDE: 3.0,
        ImpactScope.MODULE: 2.0,
        ImpactScope.COMPONENT: 1.5,
        ImpactScope.FUNCTION: 1.0,
        ImpactScope.LOCAL: 0.5
    }

    FIX_DIFFICULTY_WEIGHTS = {
        FixDifficulty.TRIVIAL: 0.5,
        FixDifficulty.SIMPLE: 1.0,
        FixDifficulty.MODERATE: 2.0,
        FixDifficulty.COMPLEX: 4.0,
        FixDifficulty.MAJOR: 8.0
    }

    PRIORITY_THRESHOLDS = {
        IssuePriority.P0_CRITICAL: 15.0,
        IssuePriority.P1_HIGH: 10.0,
        IssuePriority.P2_MEDIUM: 5.0,
        IssuePriority.P3_LOW: 2.0,
        IssuePriority.P4_INFO: 0.0
    }

    def __init__(self):
        pass

    def calculate_impact_score(
        self,
        severity: IssueSeverity,
        category: IssueCategory,
        impact_scope: ImpactScope,
        file_importance: float = 1.0,
        user_impact: float = 1.0
    ) -> float:
        severity_weight = self.SEVERITY_WEIGHTS.get(severity, 1.0)
        category_weight = self.CATEGORY_WEIGHTS.get(category, 1.0)
        scope_weight = self.IMPACT_SCOPE_WEIGHTS.get(impact_scope, 1.0)

        return severity_weight * category_weight * scope_weight * file_importance * user_impact

    def calculate_effort_score(
        self,
        fix_difficulty: FixDifficulty,
        complexity: float = 1.0
    ) -> float:
        base_effort = self.FIX_DIFFICULTY_WEIGHTS.get(fix_difficulty, 2.0)
        return base_effort * complexity

    def determine_priority(
        self,
        impact_score: float,
        effort_score: float
    ) -> IssuePriority:
        roi = impact_score / max(effort_score, 0.1)
        adjusted_score = impact_score * (1 + roi / 10)

        if adjusted_score >= self.PRIORITY_THRESHOLDS[IssuePriority.P0_CRITICAL]:
            return IssuePriority.P0_CRITICAL
        elif adjusted_score >= self.PRIORITY_THRESHOLDS[IssuePriority.P1_HIGH]:
            return IssuePriority.P1_HIGH
        elif adjusted_score >= self.PRIORITY_THRESHOLDS[IssuePriority.P2_MEDIUM]:
            return IssuePriority.P2_MEDIUM
        elif adjusted_score >= self.PRIORITY_THRESHOLDS[IssuePriority.P3_LOW]:
            return IssuePriority.P3_LOW
        else:
            return IssuePriority.P4_INFO

    def evaluate(
        self,
        severity: IssueSeverity,
        category: IssueCategory,
        impact_scope: ImpactScope,
        fix_difficulty: FixDifficulty,
        file_importance: float = 1.0,
        user_impact: float = 1.0
    ) -> Tuple[IssuePriority, float, float]:
        impact_score = self.calculate_impact_score(
            severity, category, impact_scope, file_importance, user_impact
        )
        effort_score = self.calculate_effort_score(fix_difficulty)
        priority = self.determine_priority(impact_score, effort_score)

        return priority, impact_score, effort_score


class IssueRelationAnalyzer:
    FILE_RELATION_THRESHOLD = 0.7
    KEYWORD_RELATION_THRESHOLD = 0.6
    CATEGORY_RELATION_STRENGTH = {
        (IssueCategory.SECURITY, IssueCategory.RUNTIME): 0.8,
        (IssueCategory.RUNTIME, IssueCategory.LOGIC): 0.7,
        (IssueCategory.PERFORMANCE, IssueCategory.RUNTIME): 0.6,
        (IssueCategory.DEPENDENCY, IssueCategory.CONFIGURATION): 0.8,
        (IssueCategory.SYNTAX, IssueCategory.STYLE): 0.5,
    }

    def __init__(self):
        self.relations: List[IssueRelation] = []
        self.dependency_graph: Dict[str, DependencyNode] = {}

    def analyze_relations(
        self,
        issues: List[ClassifiedIssue]
    ) -> List[IssueRelation]:
        self.relations = []

        for i, issue1 in enumerate(issues):
            for j, issue2 in enumerate(issues):
                if i >= j:
                    continue

                relation = self._analyze_relation(issue1, issue2)
                if relation:
                    self.relations.append(relation)

        return self.relations

    def _analyze_relation(
        self,
        issue1: ClassifiedIssue,
        issue2: ClassifiedIssue
    ) -> Optional[IssueRelation]:
        strength = 0.0
        relation_type = "unknown"

        if issue1.file_path and issue1.file_path == issue2.file_path:
            strength += 0.4
            relation_type = "same_file"

        keyword_overlap = self._calculate_keyword_overlap(issue1, issue2)
        if keyword_overlap > self.KEYWORD_RELATION_THRESHOLD:
            strength += 0.3
            if relation_type == "unknown":
                relation_type = "keyword_similarity"

        category_strength = self._get_category_relation_strength(
            issue1.category, issue2.category
        )
        if category_strength > 0:
            strength += category_strength * 0.3
            if relation_type == "unknown":
                relation_type = "category_relation"

        if issue1.line_number > 0 and issue2.line_number > 0:
            if issue1.file_path == issue2.file_path:
                line_distance = abs(issue1.line_number - issue2.line_number)
                if line_distance <= 10:
                    strength += 0.2
                    relation_type = "proximity"

        if strength >= 0.3:
            return IssueRelation(
                source_id=issue1.issue_id,
                target_id=issue2.issue_id,
                relation_type=relation_type,
                strength=min(strength, 1.0),
                description=f"{relation_type}: strength={strength:.2f}"
            )

        return None

    def _calculate_keyword_overlap(
        self,
        issue1: ClassifiedIssue,
        issue2: ClassifiedIssue
    ) -> float:
        keywords1 = set(issue1.tags + issue1.title.lower().split())
        keywords2 = set(issue2.tags + issue2.title.lower().split())

        if not keywords1 or not keywords2:
            return 0.0

        intersection = keywords1 & keywords2
        union = keywords1 | keywords2

        return len(intersection) / len(union) if union else 0.0

    def _get_category_relation_strength(
        self,
        cat1: IssueCategory,
        cat2: IssueCategory
    ) -> float:
        if cat1 == cat2:
            return 1.0

        key = (cat1, cat2) if (cat1, cat2) in self.CATEGORY_RELATION_STRENGTH else (cat2, cat1)
        return self.CATEGORY_RELATION_STRENGTH.get(key, 0.0)

    def build_dependency_graph(
        self,
        issues: List[ClassifiedIssue],
        relations: List[IssueRelation]
    ) -> Dict[str, DependencyNode]:
        self.dependency_graph = {}

        for issue in issues:
            self.dependency_graph[issue.issue_id] = DependencyNode(
                issue_id=issue.issue_id,
                depends_on=[],
                depended_by=[],
                level=0
            )

        for relation in relations:
            if relation.relation_type in ["dependency", "causes", "blocks"]:
                source_node = self.dependency_graph.get(relation.source_id)
                target_node = self.dependency_graph.get(relation.target_id)

                if source_node and target_node:
                    source_node.depends_on.append(relation.target_id)
                    target_node.depended_by.append(relation.source_id)

        self._calculate_dependency_levels()

        return self.dependency_graph

    def _calculate_dependency_levels(self):
        visited = set()

        def dfs(node_id: str, level: int):
            if node_id in visited:
                return

            visited.add(node_id)
            node = self.dependency_graph.get(node_id)
            if node:
                node.level = max(node.level, level)
                for dep_id in node.depends_on:
                    dfs(dep_id, level + 1)

        for node_id in self.dependency_graph:
            if node_id not in visited:
                dfs(node_id, 0)

    def find_root_causes(self) -> List[str]:
        root_causes = []
        for node_id, node in self.dependency_graph.items():
            if not node.depends_on and node.depended_by:
                root_causes.append(node_id)
        return root_causes

    def find_leaf_issues(self) -> List[str]:
        leaves = []
        for node_id, node in self.dependency_graph.items():
            if node.depends_on and not node.depended_by:
                leaves.append(node_id)
        return leaves

    def get_fix_order(self) -> List[str]:
        sorted_nodes = sorted(
            self.dependency_graph.items(),
            key=lambda x: x[1].level,
            reverse=True
        )
        return [node_id for node_id, _ in sorted_nodes]


class IssueClassifier:
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.rules = ClassificationRules.get_all_rules()
        self.priority_evaluator = PriorityEvaluator()
        self.relation_analyzer = IssueRelationAnalyzer()
        self.issue_counter = 0
        self.classified_issues: List[ClassifiedIssue] = []

    def _generate_issue_id(self) -> str:
        self.issue_counter += 1
        return f"ISSUE-{self.issue_counter:04d}"

    def classify(
        self,
        title: str,
        description: str,
        file_path: str = "",
        line_number: int = 0,
        code_snippet: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> ClassifiedIssue:
        category, severity, confidence, matched_rule = self._classify_by_rules(
            title, description
        )

        impact_scope = self._determine_impact_scope(file_path, category, severity)
        fix_difficulty = self._determine_fix_difficulty(severity, category, confidence)

        priority, impact_score, effort_score = self.priority_evaluator.evaluate(
            severity, category, impact_scope, fix_difficulty
        )

        suggestions = self._generate_suggestions(category, severity, matched_rule)
        tags = self._generate_tags(category, severity, priority, impact_scope)

        now = datetime.now().isoformat()

        issue = ClassifiedIssue(
            issue_id=self._generate_issue_id(),
            title=title,
            description=description,
            category=category,
            severity=severity,
            priority=priority,
            status=IssueStatus.OPEN,
            impact_scope=impact_scope,
            fix_difficulty=fix_difficulty,
            file_path=file_path,
            line_number=line_number,
            code_snippet=code_snippet,
            tags=tags,
            suggestions=suggestions,
            related_issues=[],
            confidence=confidence,
            impact_score=impact_score,
            effort_score=effort_score,
            created_at=now,
            updated_at=now,
            metadata=metadata or {}
        )

        self.classified_issues.append(issue)
        return issue

    def _classify_by_rules(
        self,
        title: str,
        description: str
    ) -> Tuple[IssueCategory, IssueSeverity, float, Optional[ClassificationRule]]:
        text = f"{title} {description}".lower()
        best_match: Optional[ClassificationRule] = None
        best_confidence = 0.0

        for rule in self.rules:
            pattern_match = False
            for pattern in rule.patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    pattern_match = True
                    break

            keyword_matches = sum(1 for kw in rule.keywords if kw.lower() in text)
            keyword_score = keyword_matches / max(len(rule.keywords), 1)

            if pattern_match and keyword_score > 0:
                confidence = rule.confidence * (0.7 + 0.3 * keyword_score)
            elif pattern_match:
                confidence = rule.confidence * 0.8
            elif keyword_score > 0.5:
                confidence = rule.confidence * keyword_score * 0.6
            else:
                confidence = 0.0

            if confidence > best_confidence:
                best_confidence = confidence
                best_match = rule

        if best_match:
            severity = self._adjust_severity(best_match.severity_base, text)
            return best_match.category, severity, best_confidence, best_match

        return IssueCategory.RUNTIME, IssueSeverity.MEDIUM, 0.3, None

    def _adjust_severity(
        self,
        base_severity: IssueSeverity,
        text: str
    ) -> IssueSeverity:
        severity_boosters = [
            (r"critical", IssueSeverity.CRITICAL),
            (r"urgent", IssueSeverity.HIGH),
            (r"important", IssueSeverity.HIGH),
            (r"security", IssueSeverity.HIGH),
            (r"crash", IssueSeverity.HIGH),
            (r"data loss", IssueSeverity.CRITICAL),
        ]

        severity_reducers = [
            (r"minor", IssueSeverity.LOW),
            (r"cosmetic", IssueSeverity.INFO),
            (r"suggestion", IssueSeverity.INFO),
            (r"optional", IssueSeverity.INFO),
        ]

        for pattern, severity in severity_boosters:
            if re.search(pattern, text, re.IGNORECASE):
                severity_order = [
                    IssueSeverity.INFO,
                    IssueSeverity.LOW,
                    IssueSeverity.MEDIUM,
                    IssueSeverity.HIGH,
                    IssueSeverity.CRITICAL
                ]
                base_idx = severity_order.index(base_severity)
                target_idx = severity_order.index(severity)
                return severity_order[max(base_idx, target_idx)]

        for pattern, severity in severity_reducers:
            if re.search(pattern, text, re.IGNORECASE):
                return severity

        return base_severity

    def _determine_impact_scope(
        self,
        file_path: str,
        category: IssueCategory,
        severity: IssueSeverity
    ) -> ImpactScope:
        if not file_path:
            return ImpactScope.LOCAL

        if category in [IssueCategory.SECURITY, IssueCategory.ARCHITECTURE]:
            return ImpactScope.SYSTEM_WIDE

        if category in [IssueCategory.DEPENDENCY, IssueCategory.CONFIGURATION]:
            return ImpactScope.MODULE

        if severity in [IssueSeverity.CRITICAL, IssueSeverity.HIGH]:
            return ImpactScope.COMPONENT

        return ImpactScope.FUNCTION

    def _determine_fix_difficulty(
        self,
        severity: IssueSeverity,
        category: IssueCategory,
        confidence: float
    ) -> FixDifficulty:
        if category == IssueCategory.SECURITY:
            return FixDifficulty.COMPLEX

        if category in [IssueCategory.ARCHITECTURE, IssueCategory.LOGIC]:
            return FixDifficulty.MODERATE

        if category in [IssueCategory.STYLE, IssueCategory.DOCUMENTATION]:
            return FixDifficulty.SIMPLE

        if severity == IssueSeverity.CRITICAL:
            return FixDifficulty.COMPLEX

        if confidence < 0.5:
            return FixDifficulty.MODERATE

        return FixDifficulty.SIMPLE

    def _generate_suggestions(
        self,
        category: IssueCategory,
        severity: IssueSeverity,
        matched_rule: Optional[ClassificationRule]
    ) -> List[str]:
        suggestions = []

        if matched_rule and matched_rule.examples:
            suggestions.extend(matched_rule.examples[:2])

        category_suggestions = {
            IssueCategory.SYNTAX: [
                "检查代码语法",
                "验证括号和引号匹配",
                "检查缩进是否正确"
            ],
            IssueCategory.RUNTIME: [
                "添加异常处理",
                "检查变量初始化",
                "验证数据类型"
            ],
            IssueCategory.LOGIC: [
                "审查业务逻辑",
                "添加单元测试",
                "检查边界条件"
            ],
            IssueCategory.PERFORMANCE: [
                "分析性能瓶颈",
                "优化算法复杂度",
                "考虑缓存策略"
            ],
            IssueCategory.SECURITY: [
                "进行安全审计",
                "检查输入验证",
                "审查权限控制"
            ],
            IssueCategory.STYLE: [
                "运行代码格式化工具",
                "检查命名规范",
                "移除未使用的代码"
            ],
            IssueCategory.DEPENDENCY: [
                "检查依赖版本",
                "验证模块安装",
                "更新依赖配置"
            ],
            IssueCategory.CONFIGURATION: [
                "检查配置文件",
                "验证环境变量",
                "审查配置项"
            ],
        }

        suggestions.extend(category_suggestions.get(category, ["分析问题原因"])[:3])

        return suggestions

    def _generate_tags(
        self,
        category: IssueCategory,
        severity: IssueSeverity,
        priority: IssuePriority,
        impact_scope: ImpactScope
    ) -> List[str]:
        tags = [
            f"category:{category.value}",
            f"severity:{severity.value}",
            f"priority:{priority.value}",
            f"scope:{impact_scope.value}"
        ]
        return tags

    def classify_batch(
        self,
        issues: List[Dict[str, Any]]
    ) -> List[ClassifiedIssue]:
        results = []
        for issue_data in issues:
            issue = self.classify(
                title=issue_data.get("title", ""),
                description=issue_data.get("description", ""),
                file_path=issue_data.get("file_path", ""),
                line_number=issue_data.get("line_number", 0),
                code_snippet=issue_data.get("code_snippet", ""),
                metadata=issue_data.get("metadata")
            )
            results.append(issue)
        return results

    def analyze_relations(self) -> List[IssueRelation]:
        return self.relation_analyzer.analyze_relations(self.classified_issues)

    def build_dependency_graph(self) -> Dict[str, DependencyNode]:
        relations = self.analyze_relations()
        return self.relation_analyzer.build_dependency_graph(
            self.classified_issues, relations
        )

    def generate_result(self) -> ClassificationResult:
        relations = self.analyze_relations()
        dependency_graph = self.relation_analyzer.build_dependency_graph(
            self.classified_issues, relations
        )

        by_category: Dict[str, int] = defaultdict(int)
        by_priority: Dict[str, int] = defaultdict(int)
        by_severity: Dict[str, int] = defaultdict(int)
        by_status: Dict[str, int] = defaultdict(int)

        for issue in self.classified_issues:
            by_category[issue.category.value] += 1
            by_priority[issue.priority.value] += 1
            by_severity[issue.severity.value] += 1
            by_status[issue.status.value] += 1

        summary = self._generate_summary()

        return ClassificationResult(
            timestamp=datetime.now().isoformat(),
            total_issues=len(self.classified_issues),
            classified_issues=self.classified_issues,
            by_category=dict(by_category),
            by_priority=dict(by_priority),
            by_severity=dict(by_severity),
            by_status=dict(by_status),
            dependency_graph=dependency_graph,
            relations=relations,
            summary=summary
        )

    def _generate_summary(self) -> str:
        if not self.classified_issues:
            return "没有问题需要分类"

        critical_count = sum(
            1 for i in self.classified_issues
            if i.severity == IssueSeverity.CRITICAL
        )
        high_count = sum(
            1 for i in self.classified_issues
            if i.severity == IssueSeverity.HIGH
        )

        p0_count = sum(
            1 for i in self.classified_issues
            if i.priority == IssuePriority.P0_CRITICAL
        )
        p1_count = sum(
            1 for i in self.classified_issues
            if i.priority == IssuePriority.P1_HIGH
        )

        parts = [f"共分类 {len(self.classified_issues)} 个问题"]

        if critical_count > 0:
            parts.append(f"严重 {critical_count} 个")
        if high_count > 0:
            parts.append(f"高优先级 {high_count} 个")
        if p0_count > 0:
            parts.append(f"P0 {p0_count} 个")
        if p1_count > 0:
            parts.append(f"P1 {p1_count} 个")

        return "，".join(parts)

    def get_issues_by_category(self, category: IssueCategory) -> List[ClassifiedIssue]:
        return [i for i in self.classified_issues if i.category == category]

    def get_issues_by_priority(self, priority: IssuePriority) -> List[ClassifiedIssue]:
        return [i for i in self.classified_issues if i.priority == priority]

    def get_issues_by_severity(self, severity: IssueSeverity) -> List[ClassifiedIssue]:
        return [i for i in self.classified_issues if i.severity == severity]

    def get_critical_issues(self) -> List[ClassifiedIssue]:
        return self.get_issues_by_severity(IssueSeverity.CRITICAL)

    def get_high_priority_issues(self) -> List[ClassifiedIssue]:
        return self.get_issues_by_priority(IssuePriority.P0_CRITICAL)

    def export_to_json(self, output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)

        result = self.generate_result()

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)

        self.logger.info(f"分类结果已导出: {output_path}")

    def export_to_markdown(self, output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)

        result = self.generate_result()
        report = self._generate_markdown_report(result)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)

        self.logger.info(f"Markdown报告已导出: {output_path}")

    def _generate_markdown_report(self, result: ClassificationResult) -> str:
        lines = [
            "# 问题分类报告",
            "",
            f"**生成时间**: {result.timestamp}",
            f"**问题总数**: {result.total_issues}",
            "",
            "---",
            "",
            "## 📊 概览",
            "",
            f"| 指标 | 数值 |",
            f"|------|------|",
        ]

        for category, count in sorted(result.by_category.items(), key=lambda x: -x[1]):
            lines.append(f"| {category} | {count} |")

        lines.extend([
            "",
            "---",
            "",
            "## 📋 优先级分布",
            "",
        ])

        priority_emoji = {
            "P0": "🔴",
            "P1": "🟠",
            "P2": "🟡",
            "P3": "🟢",
            "P4": "⚪"
        }

        for priority, count in sorted(result.by_priority.items()):
            emoji = priority_emoji.get(priority, "⚪")
            lines.append(f"- {emoji} **{priority}**: {count} 个")

        lines.extend([
            "",
            "---",
            "",
            "## 🔍 问题详情",
            "",
        ])

        for issue in sorted(result.classified_issues, key=lambda x: x.priority.value):
            emoji = priority_emoji.get(issue.priority.value, "⚪")
            lines.extend([
                f"### {emoji} {issue.issue_id}: {issue.title}",
                "",
                f"- **分类**: {issue.category.value}",
                f"- **严重程度**: {issue.severity.value}",
                f"- **优先级**: {issue.priority.value}",
                f"- **影响范围**: {issue.impact_scope.value}",
                f"- **修复难度**: {issue.fix_difficulty.value}",
                f"- **置信度**: {issue.confidence:.0%}",
            ])

            if issue.file_path:
                lines.append(f"- **文件**: `{issue.file_path}`")
            if issue.line_number > 0:
                lines.append(f"- **行号**: {issue.line_number}")

            if issue.suggestions:
                lines.extend([
                    "",
                    "**建议**:",
                    "",
                ])
                for s in issue.suggestions:
                    lines.append(f"- {s}")

            lines.extend([
                "",
                "---",
                "",
            ])

        if result.relations:
            lines.extend([
                "## 🔗 问题关联",
                "",
            ])
            for relation in result.relations[:10]:
                lines.append(
                    f"- `{relation.source_id}` -> `{relation.target_id}` "
                    f"({relation.relation_type}, 强度: {relation.strength:.2f})"
                )
            lines.append("")

        return "\n".join(lines)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="问题分类器 - 智能问题分类系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 从JSON文件分类问题
  python issue_classifier.py --input issues.json --output classified.json

  # 分析问题依赖关系
  python issue_classifier.py --input issues.json --analyze-dependencies

  # 导出Markdown报告
  python issue_classifier.py --input issues.json --report report.md
        """
    )

    parser.add_argument(
        "--input",
        type=Path,
        help="输入问题JSON文件路径"
    )

    parser.add_argument(
        "--output",
        type=Path,
        help="输出分类结果JSON文件路径"
    )

    parser.add_argument(
        "--report",
        type=Path,
        help="输出Markdown报告路径"
    )

    parser.add_argument(
        "--analyze-dependencies",
        action="store_true",
        help="分析问题依赖关系"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="详细输出"
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    classifier = IssueClassifier(logger=logger)

    if args.input:
        with open(args.input, 'r', encoding='utf-8') as f:
            issues_data = json.load(f)

        if isinstance(issues_data, list):
            issues = issues_data
        elif isinstance(issues_data, dict) and "issues" in issues_data:
            issues = issues_data["issues"]
        else:
            issues = [issues_data]

        classified = classifier.classify_batch(issues)

        print(f"\n分类完成: {len(classified)} 个问题")

        result = classifier.generate_result()

        print(f"\n摘要: {result.summary}")

        print("\n按分类分布:")
        for cat, count in sorted(result.by_category.items(), key=lambda x: -x[1]):
            print(f"  {cat}: {count}")

        print("\n按优先级分布:")
        for pri, count in sorted(result.by_priority.items()):
            print(f"  {pri}: {count}")

        if args.analyze_dependencies:
            print("\n依赖分析:")
            root_causes = classifier.relation_analyzer.find_root_causes()
            print(f"  根因问题: {root_causes}")

            fix_order = classifier.relation_analyzer.get_fix_order()
            print(f"  建议修复顺序: {fix_order[:5]}")

        if args.output:
            classifier.export_to_json(args.output)
            print(f"\n结果已保存: {args.output}")

        if args.report:
            classifier.export_to_markdown(args.report)
            print(f"\n报告已保存: {args.report}")

    else:
        parser.print_help()

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
