#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SOLID原则检查器 - Sanliu 技能 (深度优化版)

提供全面的SOLID原则合规性检查，包括：
- SRP（单一职责原则）检查：方法内聚性分析、数据成员聚类、职责边界识别
- OCP（开闭原则）检查：扩展点检测、修改热点分析、变化点预测
- LSP（里氏替换原则）检查：行为契约验证、前置/后置条件检查、不变量验证
- ISP（接口隔离原则）检查：接口使用频率分析、客户端分组、胖接口检测
- DIP（依赖倒置原则）检查：依赖层次分析、抽象层稳定性、依赖方向验证

使用示例:
    python solid_principle_checker.py
    python solid_principle_checker.py --path ./src
    python solid_principle_checker.py --output json --output-file report.json
    python solid_principle_checker.py --principles SRP,OCP
    python solid_principle_checker.py --strict
    python solid_principle_checker.py --cross-file
"""

import ast
import json
import logging
import re
import sys
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Callable, TypeVar
from functools import lru_cache


class PrincipleType(Enum):
    SRP = "Single Responsibility Principle"
    OCP = "Open/Closed Principle"
    LSP = "Liskov Substitution Principle"
    ISP = "Interface Segregation Principle"
    DIP = "Dependency Inversion Principle"


class SeverityLevel(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ComplianceStatus(Enum):
    COMPLIANT = "compliant"
    PARTIAL = "partial"
    NON_COMPLIANT = "non_compliant"
    NOT_APPLICABLE = "not_applicable"


class CohesionLevel(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


@dataclass
class Violation:
    principle: PrincipleType
    file_path: str
    line_number: int
    code_element: str
    description: str
    severity: SeverityLevel
    suggestion: str
    details: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    impact_score: float = 0.0
    fix_complexity: str = "medium"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "principle": self.principle.name,
            "principle_name": self.principle.value,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "code_element": self.code_element,
            "description": self.description,
            "severity": self.severity.value,
            "suggestion": self.suggestion,
            "details": self.details,
            "confidence": self.confidence,
            "impact_score": self.impact_score,
            "fix_complexity": self.fix_complexity
        }


@dataclass
class CohesionMetrics:
    class_name: str
    lcom_score: float
    cohesion_level: CohesionLevel
    method_groups: List[Set[str]]
    data_clusters: List[Set[str]]
    responsibility_score: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "class_name": self.class_name,
            "lcom_score": self.lcom_score,
            "cohesion_level": self.cohesion_level.value,
            "method_groups": [list(g) for g in self.method_groups],
            "data_clusters": [list(c) for c in self.data_clusters],
            "responsibility_score": self.responsibility_score
        }


@dataclass
class ExtensionPoint:
    file_path: str
    line_number: int
    code_element: str
    extension_type: str
    description: str
    is_abstract: bool
    usage_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "line_number": self.line_number,
            "code_element": self.code_element,
            "extension_type": self.extension_type,
            "description": self.description,
            "is_abstract": self.is_abstract,
            "usage_count": self.usage_count
        }


@dataclass
class BehaviorContract:
    method_name: str
    class_name: str
    preconditions: List[str]
    postconditions: List[str]
    invariants: List[str]
    exceptions: List[str]
    is_compatible: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "method_name": self.method_name,
            "class_name": self.class_name,
            "preconditions": self.preconditions,
            "postconditions": self.postconditions,
            "invariants": self.invariants,
            "exceptions": self.exceptions,
            "is_compatible": self.is_compatible
        }


@dataclass
class InterfaceUsage:
    interface_name: str
    implementing_classes: List[str]
    method_usage: Dict[str, int]
    unused_methods: List[str]
    client_groups: Dict[str, List[str]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "interface_name": self.interface_name,
            "implementing_classes": self.implementing_classes,
            "method_usage": self.method_usage,
            "unused_methods": self.unused_methods,
            "client_groups": self.client_groups
        }


@dataclass
class DependencyLayer:
    module_name: str
    layer_level: int
    abstraction_score: float
    stability_score: float
    depends_on_abstract: int
    depends_on_concrete: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "module_name": self.module_name,
            "layer_level": self.layer_level,
            "abstraction_score": self.abstraction_score,
            "stability_score": self.stability_score,
            "depends_on_abstract": self.depends_on_abstract,
            "depends_on_concrete": self.depends_on_concrete
        }


@dataclass
class PrincipleReport:
    principle: PrincipleType
    status: ComplianceStatus
    score: float
    violations: List[Violation] = field(default_factory=list)
    checked_elements: int = 0
    compliant_elements: int = 0
    metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "principle": self.principle.name,
            "principle_name": self.principle.value,
            "status": self.status.value,
            "score": self.score,
            "violation_count": len(self.violations),
            "violations": [v.to_dict() for v in self.violations],
            "checked_elements": self.checked_elements,
            "compliant_elements": self.compliant_elements,
            "metrics": self.metrics
        }


@dataclass
class SOLIDReport:
    timestamp: str
    project_path: str
    overall_score: float
    overall_status: ComplianceStatus
    principle_reports: Dict[str, PrincipleReport]
    cross_file_analysis: Dict[str, Any] = field(default_factory=dict)
    summary: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "project_path": self.project_path,
            "overall_score": self.overall_score,
            "overall_status": self.overall_status.value,
            "principle_reports": {
                k: v.to_dict() for k, v in self.principle_reports.items()
            },
            "cross_file_analysis": self.cross_file_analysis,
            "summary": self.summary,
            "recommendations": self.recommendations
        }


class LCOMCalculator:
    """Lack of Cohesion of Methods (LCOM) 计算器"""

    @staticmethod
    def calculate(class_node: ast.ClassDef) -> Tuple[float, List[Set[str]]]:
        methods = [
            n for n in class_node.body
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]

        if len(methods) <= 1:
            return 0.0, []

        method_attributes: Dict[str, Set[str]] = {}
        for method in methods:
            attrs = LCOMCalculator._extract_used_attributes(method)
            method_attributes[method.name] = attrs

        m = len(methods)
        shared_pairs = 0
        non_shared_pairs = 0
        method_groups: List[Set[str]] = []

        method_list = list(method_attributes.keys())
        for i in range(len(method_list)):
            for j in range(i + 1, len(method_list)):
                attrs_i = method_attributes[method_list[i]]
                attrs_j = method_attributes[method_list[j]]

                if attrs_i & attrs_j:
                    shared_pairs += 1
                else:
                    non_shared_pairs += 1

        total_pairs = shared_pairs + non_shared_pairs
        if total_pairs == 0:
            return 0.0, []

        lcom = non_shared_pairs / total_pairs if total_pairs > 0 else 0.0

        method_groups = LCOMCalculator._cluster_methods(method_attributes)

        return lcom, method_groups

    @staticmethod
    def _extract_used_attributes(method: ast.FunctionDef) -> Set[str]:
        attributes = set()
        for node in ast.walk(method):
            if isinstance(node, ast.Attribute):
                if isinstance(node.value, ast.Name) and node.value.id == 'self':
                    attributes.add(node.attr)
        return attributes

    @staticmethod
    def _cluster_methods(method_attrs: Dict[str, Set[str]]) -> List[Set[str]]:
        if not method_attrs:
            return []

        groups: List[Set[str]] = []
        method_names = list(method_attrs.keys())

        for method in method_names:
            attrs = method_attrs[method]
            found_group = False

            for group in groups:
                group_attrs = set()
                for m in group:
                    group_attrs.update(method_attrs.get(m, set()))

                if attrs & group_attrs:
                    group.add(method)
                    found_group = True
                    break

            if not found_group:
                groups.append({method})

        merged = True
        while merged:
            merged = False
            new_groups = []
            used = set()

            for i, group1 in enumerate(groups):
                if i in used:
                    continue
                for j, group2 in enumerate(groups[i + 1:], i + 1):
                    if j in used:
                        continue

                    attrs1 = set()
                    attrs2 = set()
                    for m in group1:
                        attrs1.update(method_attrs.get(m, set()))
                    for m in group2:
                        attrs2.update(method_attrs.get(m, set()))

                    if attrs1 & attrs2:
                        group1.update(group2)
                        used.add(j)
                        merged = True

                new_groups.append(group1)

            groups = new_groups

        return groups


class SRPChecker:
    """单一职责原则检查器 (深度优化版)"""

    DEFAULT_THRESHOLDS = {
        "max_public_methods": 10,
        "max_method_categories": 3,
        "max_class_lines": 300,
        "max_dependencies": 5,
        "max_responsibilities": 2,
        "lcom_threshold": 0.5,
        "min_cohesion_score": 0.6
    }

    RESPONSIBILITY_KEYWORDS = {
        "data_access": ["get", "fetch", "find", "query", "load", "read", "retrieve"],
        "data_modification": ["save", "create", "update", "delete", "write", "store", "insert", "remove"],
        "validation": ["validate", "check", "verify", "ensure", "assert"],
        "transformation": ["format", "parse", "convert", "transform", "map", "serialize"],
        "communication": ["send", "notify", "emit", "publish", "dispatch", "broadcast"],
        "computation": ["calculate", "compute", "process", "analyze", "evaluate"],
        "presentation": ["render", "display", "show", "hide", "draw", "print"],
        "persistence": ["persist", "store", "cache", "flush", "sync"],
        "configuration": ["config", "setup", "initialize", "configure"],
        "logging": ["log", "trace", "debug", "info", "warn", "error"]
    }

    def __init__(self, logger: logging.Logger, thresholds: Optional[Dict[str, int]] = None):
        self.logger = logger
        self.thresholds = {**self.DEFAULT_THRESHOLDS, **(thresholds or {})}
        self.violations: List[Violation] = []
        self.cohesion_metrics: Dict[str, CohesionMetrics] = {}

    def check(self, py_file: Path, tree: ast.AST, source: str) -> List[Violation]:
        violations = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                violations.extend(self._check_class_srp(py_file, node, source))

        return violations

    def _check_class_srp(self, py_file: Path, class_node: ast.ClassDef, source: str) -> List[Violation]:
        violations = []
        class_name = class_node.name

        methods = [
            n for n in class_node.body
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
        public_methods = [m for m in methods if not m.name.startswith('_')]

        lcom_score, method_groups = LCOMCalculator.calculate(class_node)

        if lcom_score > self.thresholds["lcom_threshold"]:
            cohesion_level = self._determine_cohesion_level(lcom_score)
            violations.append(Violation(
                principle=PrincipleType.SRP,
                file_path=str(py_file),
                line_number=class_node.lineno,
                code_element=class_name,
                description=f"类 '{class_name}' LCOM得分为 {lcom_score:.2f}，内聚性{cohesion_level.value}，可能承担多个职责",
                severity=SeverityLevel.HIGH if lcom_score > 0.7 else SeverityLevel.MEDIUM,
                suggestion="考虑按方法分组拆分类，每个组代表一个职责",
                details={
                    "lcom_score": lcom_score,
                    "method_groups": [list(g) for g in method_groups],
                    "cohesion_level": cohesion_level.value
                },
                confidence=0.9,
                impact_score=lcom_score * 10
            ))

        responsibilities = self._identify_responsibilities(methods)
        if len(responsibilities) > self.thresholds["max_responsibilities"]:
            violations.append(Violation(
                principle=PrincipleType.SRP,
                file_path=str(py_file),
                line_number=class_node.lineno,
                code_element=class_name,
                description=f"类 '{class_name}' 涉及多个职责领域: {', '.join(responsibilities.keys())}，违反单一职责原则",
                severity=SeverityLevel.HIGH,
                suggestion="按职责拆分类，每个类专注于一个领域",
                details={"responsibilities": dict(responsibilities)},
                confidence=0.85,
                impact_score=len(responsibilities) * 5
            ))

        data_clusters = self._analyze_data_clusters(class_node)
        if len(data_clusters) > 1:
            violations.append(Violation(
                principle=PrincipleType.SRP,
                file_path=str(py_file),
                line_number=class_node.lineno,
                code_element=class_name,
                description=f"类 '{class_name}' 的数据成员可分为 {len(data_clusters)} 个独立集群，建议拆分",
                severity=SeverityLevel.MEDIUM,
                suggestion="根据数据集群拆分为多个类，每个类管理相关数据",
                details={"data_clusters": [list(c) for c in data_clusters]},
                confidence=0.75,
                impact_score=len(data_clusters) * 3
            ))

        if len(public_methods) > self.thresholds["max_public_methods"]:
            violations.append(Violation(
                principle=PrincipleType.SRP,
                file_path=str(py_file),
                line_number=class_node.lineno,
                code_element=class_name,
                description=f"类 '{class_name}' 有 {len(public_methods)} 个公共方法，超过阈值 {self.thresholds['max_public_methods']}，可能承担过多职责",
                severity=SeverityLevel.MEDIUM,
                suggestion="考虑将类拆分为多个更小的类，每个类只负责一个职责",
                details={"public_method_count": len(public_methods)},
                confidence=0.7,
                impact_score=len(public_methods) * 0.5
            ))

        dependencies = self._extract_dependencies(class_node)
        if len(dependencies) > self.thresholds["max_dependencies"]:
            violations.append(Violation(
                principle=PrincipleType.SRP,
                file_path=str(py_file),
                line_number=class_node.lineno,
                code_element=class_name,
                description=f"类 '{class_name}' 依赖了 {len(dependencies)} 个外部类，可能承担过多职责",
                severity=SeverityLevel.MEDIUM,
                suggestion="减少外部依赖，考虑使用依赖注入或接口隔离",
                details={"dependencies": list(dependencies)},
                confidence=0.65,
                impact_score=len(dependencies) * 2
            ))

        class_lines = self._count_class_lines(class_node)
        if class_lines > self.thresholds["max_class_lines"]:
            violations.append(Violation(
                principle=PrincipleType.SRP,
                file_path=str(py_file),
                line_number=class_node.lineno,
                code_element=class_name,
                description=f"类 '{class_name}' 有 {class_lines} 行代码，超过阈值 {self.thresholds['max_class_lines']}，可能过大",
                severity=SeverityLevel.LOW,
                suggestion="考虑拆分为多个更小的类",
                details={"class_lines": class_lines},
                confidence=0.6,
                impact_score=class_lines * 0.01
            ))

        self.cohesion_metrics[class_name] = CohesionMetrics(
            class_name=class_name,
            lcom_score=lcom_score,
            cohesion_level=self._determine_cohesion_level(lcom_score),
            method_groups=method_groups,
            data_clusters=data_clusters,
            responsibility_score=1.0 - (len(responsibilities) / max(len(self.RESPONSIBILITY_KEYWORDS), 1))
        )

        return violations

    def _identify_responsibilities(self, methods: List[ast.FunctionDef]) -> Dict[str, List[str]]:
        responsibilities = defaultdict(list)

        for method in methods:
            method_lower = method.name.lower()
            for responsibility, keywords in self.RESPONSIBILITY_KEYWORDS.items():
                if any(kw in method_lower for kw in keywords):
                    responsibilities[responsibility].append(method.name)
                    break

        return dict(responsibilities)

    def _analyze_data_clusters(self, class_node: ast.ClassDef) -> List[Set[str]]:
        attribute_methods: Dict[str, Set[str]] = {}

        for item in class_node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                used_attrs = set()
                for node in ast.walk(item):
                    if isinstance(node, ast.Attribute):
                        if isinstance(node.value, ast.Name) and node.value.id == 'self':
                            used_attrs.add(node.attr)
                if used_attrs:
                    attribute_methods[item.name] = used_attrs

        if not attribute_methods:
            return []

        clusters: List[Set[str]] = []
        all_attrs = set()
        for attrs in attribute_methods.values():
            all_attrs.update(attrs)

        for attr in all_attrs:
            related_attrs = {attr}
            for method, attrs in attribute_methods.items():
                if attr in attrs:
                    related_attrs.update(attrs)

            merged = False
            for cluster in clusters:
                if cluster & related_attrs:
                    cluster.update(related_attrs)
                    merged = True
                    break

            if not merged:
                clusters.append(related_attrs)

        return clusters

    def _extract_dependencies(self, class_node: ast.ClassDef) -> Set[str]:
        dependencies = set()

        for child in ast.walk(class_node):
            if isinstance(child, ast.Attribute):
                if isinstance(child.value, ast.Name):
                    if child.value.id not in ('self', 'cls', 'ClassVar'):
                        dependencies.add(child.value.id)
            elif isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    if child.func.id[0].isupper():
                        dependencies.add(child.func.id)

        return dependencies

    def _count_class_lines(self, class_node: ast.ClassDef) -> int:
        if hasattr(class_node, 'end_lineno') and class_node.end_lineno:
            return class_node.end_lineno - class_node.lineno
        return 0

    def _determine_cohesion_level(self, lcom_score: float) -> CohesionLevel:
        if lcom_score < 0.3:
            return CohesionLevel.HIGH
        elif lcom_score < 0.6:
            return CohesionLevel.MEDIUM
        elif lcom_score < 0.8:
            return CohesionLevel.LOW
        else:
            return CohesionLevel.NONE


class OCPChecker:
    """开闭原则检查器 (深度优化版)"""

    VIOLATION_PATTERNS = [
        (r"if\s+\w+\.type\s*==", "type_check", "基于type属性的条件判断"),
        (r"if\s+\w+\.kind\s*==", "kind_check", "基于kind属性的条件判断"),
        (r"if\s+\w+\.category\s*==", "category_check", "基于category属性的条件判断"),
        (r"isinstance\s*\([^)]+\)\s*(or|and)", "isinstance_chain", "isinstance链式判断"),
        (r"elif\s+.*type.*==", "elif_type", "elif类型判断链"),
        (r"match\s+\w+\.type", "match_type", "基于type的match语句"),
        (r"if\s+\w+\s+in\s+\[", "type_list_check", "类型列表检查")
    ]

    EXTENSION_INDICATORS = [
        'abstract', 'base', 'interface', 'protocol', 'template',
        'hook', 'callback', 'plugin', 'extension', 'handler'
    ]

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.violations: List[Violation] = []
        self.extension_points: List[ExtensionPoint] = []

    def check(self, py_file: Path, tree: ast.AST, source: str) -> List[Violation]:
        violations = []
        lines = source.split('\n')

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                violations.extend(self._check_class_ocp(py_file, node, lines))
                self._detect_extension_points(py_file, node)

        return violations

    def _check_class_ocp(self, py_file: Path, class_node: ast.ClassDef, lines: List[str]) -> List[Violation]:
        violations = []
        class_name = class_node.name

        type_check_chains = self._detect_type_check_chains(class_node)
        for chain in type_check_chains:
            violations.append(Violation(
                principle=PrincipleType.OCP,
                file_path=str(py_file),
                line_number=chain['line'],
                code_element=f"{class_name}",
                description=f"类 '{class_name}' 中存在类型检查链 ({chain['count']} 个分支)，违反开闭原则",
                severity=SeverityLevel.HIGH if chain['count'] > 4 else SeverityLevel.MEDIUM,
                suggestion="使用策略模式、工厂模式或多态替代类型判断链",
                details={"chain_length": chain['count'], "chain_types": chain.get('types', [])},
                confidence=0.9,
                impact_score=chain['count'] * 3
            ))

        modification_hotspots = self._detect_modification_hotspots(class_node)
        for hotspot in modification_hotspots:
            violations.append(Violation(
                principle=PrincipleType.OCP,
                file_path=str(py_file),
                line_number=hotspot['line'],
                code_element=f"{class_name}.{hotspot['method']}",
                description=f"方法 '{hotspot['method']}' 可能是修改热点，每次新增类型都需要修改",
                severity=SeverityLevel.MEDIUM,
                suggestion="提取变化部分到抽象层，使用模板方法或策略模式",
                details={"modification_count": hotspot['count']},
                confidence=0.7,
                impact_score=hotspot['count'] * 2
            ))

        for child in ast.walk(class_node):
            if isinstance(child, ast.If):
                if self._is_type_based_condition(child):
                    violations.append(Violation(
                        principle=PrincipleType.OCP,
                        file_path=str(py_file),
                        line_number=child.lineno,
                        code_element=f"{class_name}",
                        description=f"类 '{class_name}' 中存在基于类型的条件分支，可能违反开闭原则",
                        severity=SeverityLevel.MEDIUM,
                        suggestion="考虑使用多态或策略模式替代类型判断，使代码对扩展开放，对修改关闭",
                        details={"condition_type": "type_based"},
                        confidence=0.75,
                        impact_score=5
                    ))

        return violations

    def _detect_type_check_chains(self, class_node: ast.ClassDef) -> List[Dict[str, Any]]:
        chains = []

        for item in class_node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                chain_info = self._analyze_if_chain(item)
                if chain_info and chain_info['count'] >= 3:
                    chains.append(chain_info)

        return chains

    def _analyze_if_chain(self, method: ast.FunctionDef) -> Optional[Dict[str, Any]]:
        chain_count = 0
        chain_types = []
        line = method.lineno

        def count_elif_chain(node: ast.AST, depth: int = 0) -> int:
            nonlocal chain_count, line
            if isinstance(node, ast.If):
                if self._is_type_based_condition(node):
                    chain_count += 1
                    if depth == 0:
                        line = node.lineno
                    if isinstance(node.test, ast.Compare):
                        for comp in node.test.comparators:
                            if isinstance(comp, ast.Constant):
                                chain_types.append(str(comp.value))

                if node.orelse:
                    if len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If):
                        count_elif_chain(node.orelse[0], depth + 1)

        count_elif_chain(method)

        if chain_count >= 3:
            return {
                'count': chain_count,
                'types': chain_types,
                'line': line
            }
        return None

    def _detect_modification_hotspots(self, class_node: ast.ClassDef) -> List[Dict[str, Any]]:
        hotspots = []

        for item in class_node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                type_checks = self._count_type_checks(item)
                if type_checks >= 3:
                    hotspots.append({
                        'method': item.name,
                        'line': item.lineno,
                        'count': type_checks
                    })

        return hotspots

    def _count_type_checks(self, method: ast.FunctionDef) -> int:
        count = 0
        for node in ast.walk(method):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == 'isinstance':
                    count += 1
            elif isinstance(node, ast.Compare):
                for comp in node.comparators:
                    if isinstance(comp, ast.Constant):
                        if isinstance(comp.value, str):
                            count += 1
        return count

    def _is_type_based_condition(self, if_node: ast.If) -> bool:
        type_attributes = {'type', 'kind', 'category', 'status', 'mode', 'action'}

        for node in ast.walk(if_node.test):
            if isinstance(node, ast.Attribute):
                if node.attr in type_attributes:
                    return True
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == 'isinstance':
                    return True

        return False

    def _detect_extension_points(self, py_file: Path, class_node: ast.ClassDef) -> None:
        is_abstract = any(
            kw in class_node.name.lower() for kw in ['abstract', 'base', 'interface']
        )

        has_abstract_methods = any(
            any(
                (isinstance(d, ast.Name) and d.id == 'abstractmethod') or
                (isinstance(d, ast.Attribute) and d.attr == 'abstractmethod')
                for d in item.decorator_list
            )
            for item in class_node.body
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
        )

        if is_abstract or has_abstract_methods:
            self.extension_points.append(ExtensionPoint(
                file_path=str(py_file),
                line_number=class_node.lineno,
                code_element=class_node.name,
                extension_type="abstract_class",
                description=f"抽象类 '{class_node.name}' 提供扩展点",
                is_abstract=True
            ))

        for item in class_node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if item.name.startswith('_') and not item.name.startswith('__'):
                    if 'hook' in item.name.lower() or 'template' in item.name.lower():
                        self.extension_points.append(ExtensionPoint(
                            file_path=str(py_file),
                            line_number=item.lineno,
                            code_element=f"{class_node.name}.{item.name}",
                            extension_type="hook_method",
                            description=f"钩子方法 '{item.name}' 提供扩展点",
                            is_abstract=False
                        ))


class LSPChecker:
    """里氏替换原则检查器 (深度优化版)"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.violations: List[Violation] = []
        self._class_methods: Dict[str, Dict[str, ast.FunctionDef]] = {}
        self._class_hierarchy: Dict[str, List[str]] = defaultdict(list)
        self._behavior_contracts: Dict[str, Dict[str, BehaviorContract]] = {}

    def check(self, py_file: Path, tree: ast.AST) -> List[Violation]:
        self._build_class_info(tree)
        violations = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                violations.extend(self._check_class_lsp(py_file, node))

        return violations

    def _build_class_info(self, tree: ast.AST) -> None:
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = {}
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        methods[item.name] = item
                self._class_methods[node.name] = methods

                for base in node.bases:
                    if isinstance(base, ast.Name):
                        self._class_hierarchy[base.id].append(node.name)

    def _check_class_lsp(self, py_file: Path, class_node: ast.ClassDef) -> List[Violation]:
        violations = []
        class_name = class_node.name

        for base in class_node.bases:
            if isinstance(base, ast.Name):
                base_name = base.id
                if base_name in self._class_methods:
                    violations.extend(
                        self._check_method_compatibility(py_file, class_name, base_name)
                    )
                    violations.extend(
                        self._check_behavior_contracts(py_file, class_name, base_name)
                    )

        violations.extend(self._check_class_invariants(py_file, class_node))

        return violations

    def _check_method_compatibility(self, py_file: Path, child_class: str, base_class: str) -> List[Violation]:
        violations = []

        base_methods = self._class_methods.get(base_class, {})
        child_methods = self._class_methods.get(child_class, {})

        for method_name, base_method in base_methods.items():
            if method_name in child_methods:
                child_method = child_methods[method_name]

                base_args = self._get_full_arg_spec(base_method)
                child_args = self._get_full_arg_spec(child_method)

                if not self._is_signature_compatible(base_args, child_args):
                    violations.append(Violation(
                        principle=PrincipleType.LSP,
                        file_path=str(py_file),
                        line_number=child_method.lineno,
                        code_element=f"{child_class}.{method_name}",
                        description=f"子类 '{child_class}' 的方法 '{method_name}' 签名与基类不兼容",
                        severity=SeverityLevel.HIGH,
                        suggestion="子类方法签名应与基类保持一致，确保子类可以替换基类使用",
                        details={
                            "base_signature": base_args,
                            "child_signature": child_args
                        },
                        confidence=0.95,
                        impact_score=8
                    ))

                base_return = self._get_return_type(base_method)
                child_return = self._get_return_type(child_method)
                if base_return and child_return and not self._is_return_type_compatible(base_return, child_return):
                    violations.append(Violation(
                        principle=PrincipleType.LSP,
                        file_path=str(py_file),
                        line_number=child_method.lineno,
                        code_element=f"{child_class}.{method_name}",
                        description=f"子类 '{child_class}' 的方法 '{method_name}' 返回类型 '{child_return}' 与基类 '{base_return}' 不兼容",
                        severity=SeverityLevel.MEDIUM,
                        suggestion="子类返回类型应与基类兼容（协变）",
                        details={
                            "base_return": base_return,
                            "child_return": child_return
                        },
                        confidence=0.8,
                        impact_score=5
                    ))

                base_exceptions = self._get_raised_exceptions(base_method)
                child_exceptions = self._get_raised_exceptions(child_method)
                new_exceptions = child_exceptions - base_exceptions
                if new_exceptions:
                    violations.append(Violation(
                        principle=PrincipleType.LSP,
                        file_path=str(py_file),
                        line_number=child_method.lineno,
                        code_element=f"{child_class}.{method_name}",
                        description=f"子类 '{child_class}' 的方法 '{method_name}' 抛出了新的异常: {new_exceptions}",
                        severity=SeverityLevel.MEDIUM,
                        suggestion="子类不应抛出基类未声明的异常",
                        details={"new_exceptions": list(new_exceptions)},
                        confidence=0.85,
                        impact_score=4
                    ))

        return violations

    def _check_behavior_contracts(self, py_file: Path, child_class: str, base_class: str) -> List[Violation]:
        violations = []

        base_methods = self._class_methods.get(base_class, {})
        child_methods = self._class_methods.get(child_class, {})

        for method_name, base_method in base_methods.items():
            if method_name in child_methods:
                child_method = child_methods[method_name]

                base_contract = self._extract_behavior_contract(base_method, base_class)
                child_contract = self._extract_behavior_contract(child_method, child_class)

                precondition_violation = self._check_precondition_weakening(base_contract, child_contract)
                if precondition_violation:
                    violations.append(Violation(
                        principle=PrincipleType.LSP,
                        file_path=str(py_file),
                        line_number=child_method.lineno,
                        code_element=f"{child_class}.{method_name}",
                        description=f"子类 '{child_class}' 的方法 '{method_name}' 前置条件比基类更严格，违反里氏替换原则",
                        severity=SeverityLevel.HIGH,
                        suggestion="子类前置条件应比基类更宽松或相同",
                        details={"violation": precondition_violation},
                        confidence=0.7,
                        impact_score=6
                    ))

                postcondition_violation = self._check_postcondition_strengthening(base_contract, child_contract)
                if postcondition_violation:
                    violations.append(Violation(
                        principle=PrincipleType.LSP,
                        file_path=str(py_file),
                        line_number=child_method.lineno,
                        code_element=f"{child_class}.{method_name}",
                        description=f"子类 '{child_class}' 的方法 '{method_name}' 后置条件比基类更弱，违反里氏替换原则",
                        severity=SeverityLevel.HIGH,
                        suggestion="子类后置条件应比基类更强或相同",
                        details={"violation": postcondition_violation},
                        confidence=0.7,
                        impact_score=6
                    ))

        return violations

    def _check_class_invariants(self, py_file: Path, class_node: ast.ClassDef) -> List[Violation]:
        violations = []
        class_name = class_node.name

        for base in class_node.bases:
            if isinstance(base, ast.Name):
                base_invariants = self._extract_class_invariants(base.id)
                child_invariants = self._extract_class_invariants(class_name)

                for invariant in base_invariants:
                    if invariant not in child_invariants:
                        violations.append(Violation(
                            principle=PrincipleType.LSP,
                            file_path=str(py_file),
                            line_number=class_node.lineno,
                            code_element=class_name,
                            description=f"子类 '{class_name}' 可能违反基类不变量: {invariant}",
                            severity=SeverityLevel.LOW,
                            suggestion="确保子类维护基类的所有不变量",
                            details={"missing_invariant": invariant},
                            confidence=0.5,
                            impact_score=3
                        ))

        return violations

    def _get_full_arg_spec(self, method: ast.FunctionDef) -> Dict[str, Any]:
        args = method.args
        spec = {
            "positional": [arg.arg for arg in args.args],
            "defaults_count": len(args.defaults),
            "kwonly": [arg.arg for arg in args.kwonlyargs],
            "vararg": args.vararg.arg if args.vararg else None,
            "kwarg": args.kwarg.arg if args.kwarg else None
        }

        annotations = {}
        for arg in args.args + args.kwonlyargs:
            if arg.annotation:
                annotations[arg.arg] = self._get_annotation_str(arg.annotation)
        spec["annotations"] = annotations

        return spec

    def _is_signature_compatible(self, base_spec: Dict, child_spec: Dict) -> bool:
        if len(base_spec["positional"]) != len(child_spec["positional"]):
            return False

        for base_arg, child_arg in zip(base_spec["positional"], child_spec["positional"]):
            base_ann = base_spec["annotations"].get(base_arg)
            child_ann = child_spec["annotations"].get(child_arg)

            if base_ann and child_ann and base_ann != child_ann:
                if not self._is_contravariant(base_ann, child_ann):
                    return False

        return True

    def _is_contravariant(self, base_type: str, child_type: str) -> bool:
        return base_type == child_type or child_type in self._get_parent_types(base_type)

    def _get_parent_types(self, type_name: str) -> Set[str]:
        return set()

    def _get_return_type(self, method: ast.FunctionDef) -> Optional[str]:
        if method.returns:
            return self._get_annotation_str(method.returns)
        return None

    def _get_annotation_str(self, annotation: ast.expr) -> str:
        if isinstance(annotation, ast.Name):
            return annotation.id
        elif isinstance(annotation, ast.Constant):
            return str(annotation.value)
        elif isinstance(annotation, ast.Subscript):
            if hasattr(ast, 'unparse'):
                return ast.unparse(annotation)
        elif hasattr(ast, 'unparse'):
            return ast.unparse(annotation)
        return ""

    def _is_return_type_compatible(self, base_return: str, child_return: str) -> bool:
        if base_return == child_return:
            return True

        if child_return in self._get_subtypes(base_return):
            return True

        return False

    def _get_subtypes(self, type_name: str) -> Set[str]:
        return set()

    def _get_raised_exceptions(self, method: ast.FunctionDef) -> Set[str]:
        exceptions = set()
        for node in ast.walk(method):
            if isinstance(node, ast.Raise):
                if isinstance(node.exc, ast.Call):
                    if isinstance(node.exc.func, ast.Name):
                        exceptions.add(node.exc.func.id)
                elif isinstance(node.exc, ast.Name):
                    exceptions.add(node.exc.id)
        return exceptions

    def _extract_behavior_contract(self, method: ast.FunctionDef, class_name: str) -> BehaviorContract:
        preconditions = []
        postconditions = []
        invariants = []

        for node in ast.walk(method):
            if isinstance(node, ast.Assert):
                if hasattr(ast, 'unparse'):
                    preconditions.append(ast.unparse(node.test))

            if isinstance(node, ast.Return):
                if hasattr(ast, 'unparse'):
                    postconditions.append(f"returns {ast.unparse(node.value)}")

        exceptions = list(self._get_raised_exceptions(method))

        return BehaviorContract(
            method_name=method.name,
            class_name=class_name,
            preconditions=preconditions,
            postconditions=postconditions,
            invariants=invariants,
            exceptions=exceptions
        )

    def _check_precondition_weakening(self, base: BehaviorContract, child: BehaviorContract) -> Optional[str]:
        if len(child.preconditions) > len(base.preconditions):
            return "子类添加了额外的前置条件"
        return None

    def _check_postcondition_strengthening(self, base: BehaviorContract, child: BehaviorContract) -> Optional[str]:
        if len(child.postconditions) < len(base.postconditions):
            return "子类减少了后置条件"
        return None

    def _extract_class_invariants(self, class_name: str) -> List[str]:
        invariants = []

        methods = self._class_methods.get(class_name, {})
        for method_name, method in methods.items():
            if 'invariant' in method_name.lower() or method_name.startswith('_check_'):
                invariants.append(method_name)

        return invariants


class ISPChecker:
    """接口隔离原则检查器 (深度优化版)"""

    MAX_ABSTRACT_METHODS = 7
    MAX_METHOD_GROUPS = 2
    MIN_USAGE_RATIO = 0.3

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.violations: List[Violation] = []
        self.interface_usage: Dict[str, InterfaceUsage] = {}

    def check(self, py_file: Path, tree: ast.AST) -> List[Violation]:
        violations = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                violations.extend(self._check_class_isp(py_file, node, tree))

        return violations

    def _check_class_isp(self, py_file: Path, class_node: ast.ClassDef, tree: ast.AST) -> List[Violation]:
        violations = []
        class_name = class_node.name

        abstract_methods = self._get_abstract_methods(class_node)

        if not abstract_methods:
            return violations

        if len(abstract_methods) > self.MAX_ABSTRACT_METHODS:
            violations.append(Violation(
                principle=PrincipleType.ISP,
                file_path=str(py_file),
                line_number=class_node.lineno,
                code_element=class_name,
                description=f"抽象类 '{class_name}' 有 {len(abstract_methods)} 个抽象方法，超过阈值 {self.MAX_ABSTRACT_METHODS}，可能违反接口隔离原则",
                severity=SeverityLevel.MEDIUM,
                suggestion="考虑将接口拆分为多个更小的专用接口，客户端不应依赖它不需要的方法",
                details={"abstract_methods": abstract_methods},
                confidence=0.85,
                impact_score=len(abstract_methods) * 2
            ))

        method_groups = self._group_methods_by_purpose(abstract_methods)
        if len(method_groups) > self.MAX_METHOD_GROUPS:
            violations.append(Violation(
                principle=PrincipleType.ISP,
                file_path=str(py_file),
                line_number=class_node.lineno,
                code_element=class_name,
                description=f"抽象类 '{class_name}' 的方法涉及多个目的: {list(method_groups.keys())}，建议拆分接口",
                severity=SeverityLevel.MEDIUM,
                suggestion="按目的拆分为多个专用接口",
                details={"method_groups": dict(method_groups)},
                confidence=0.8,
                impact_score=len(method_groups) * 3
            ))

        fat_interface_methods = self._detect_fat_interface(class_node, abstract_methods)
        if fat_interface_methods:
            violations.append(Violation(
                principle=PrincipleType.ISP,
                file_path=str(py_file),
                line_number=class_node.lineno,
                code_element=class_name,
                description=f"类 '{class_name}' 可能实现了胖接口，包含不相关的方法: {fat_interface_methods}",
                severity=SeverityLevel.LOW,
                suggestion="将不相关的方法分离到不同的接口中",
                details={"fat_interface_methods": fat_interface_methods},
                confidence=0.7,
                impact_score=len(fat_interface_methods)
            ))

        unused_methods = self._detect_unused_interface_methods(class_node, tree)
        if unused_methods:
            violations.append(Violation(
                principle=PrincipleType.ISP,
                file_path=str(py_file),
                line_number=class_node.lineno,
                code_element=class_name,
                description=f"接口 '{class_name}' 有未使用的方法: {unused_methods}，可能违反接口隔离原则",
                severity=SeverityLevel.MEDIUM,
                suggestion="考虑将未使用的方法移到单独的接口中",
                details={"unused_methods": unused_methods},
                confidence=0.6,
                impact_score=len(unused_methods) * 2
            ))

        client_groups = self._analyze_client_groups(class_node, tree)
        if len(client_groups) > 1:
            violations.append(Violation(
                principle=PrincipleType.ISP,
                file_path=str(py_file),
                line_number=class_node.lineno,
                code_element=class_name,
                description=f"接口 '{class_name}' 被多个客户端组使用，每组使用不同的方法子集",
                severity=SeverityLevel.MEDIUM,
                suggestion="为每个客户端组创建专用接口",
                details={"client_groups": {k: list(v) for k, v in client_groups.items()}},
                confidence=0.75,
                impact_score=len(client_groups) * 2
            ))

        return violations

    def _get_abstract_methods(self, class_node: ast.ClassDef) -> List[str]:
        abstract_methods = []

        for method in class_node.body:
            if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for decorator in method.decorator_list:
                    if isinstance(decorator, ast.Name) and decorator.id == 'abstractmethod':
                        abstract_methods.append(method.name)
                    elif isinstance(decorator, ast.Attribute) and decorator.attr == 'abstractmethod':
                        abstract_methods.append(method.name)

        return abstract_methods

    def _group_methods_by_purpose(self, methods: List[str]) -> Dict[str, List[str]]:
        groups = defaultdict(list)

        for method in methods:
            method_lower = method.lower()
            if any(kw in method_lower for kw in ['get', 'fetch', 'find', 'query']):
                groups['query'].append(method)
            elif any(kw in method_lower for kw in ['save', 'create', 'update', 'delete']):
                groups['command'].append(method)
            elif any(kw in method_lower for kw in ['validate', 'check']):
                groups['validation'].append(method)
            elif any(kw in method_lower for kw in ['handle', 'process']):
                groups['handler'].append(method)
            else:
                groups['other'].append(method)

        return dict(groups)

    def _detect_fat_interface(self, class_node: ast.ClassDef, abstract_methods: List[str]) -> List[str]:
        unrelated_methods = []

        prefixes = set()
        for name in abstract_methods:
            parts = name.split('_')
            if len(parts) > 1:
                prefixes.add(parts[0])

        if len(prefixes) > 2:
            for name in abstract_methods:
                parts = name.split('_')
                if len(parts) > 1:
                    prefix_count = sum(
                        1 for n in abstract_methods
                        if n.startswith(parts[0] + '_')
                    )
                    if prefix_count == 1:
                        unrelated_methods.append(name)

        return unrelated_methods

    def _detect_unused_interface_methods(self, class_node: ast.ClassDef, tree: ast.AST) -> List[str]:
        abstract_methods = self._get_abstract_methods(class_node)
        used_methods = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr in abstract_methods:
                        used_methods.add(node.func.attr)

        unused = [m for m in abstract_methods if m not in used_methods]
        return unused

    def _analyze_client_groups(self, class_node: ast.ClassDef, tree: ast.AST) -> Dict[str, Set[str]]:
        interface_name = class_node.name
        client_methods: Dict[str, Set[str]] = defaultdict(set)

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name != interface_name:
                used_methods = set()
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        if isinstance(child.func, ast.Attribute):
                            if child.func.attr in self._get_abstract_methods(class_node):
                                used_methods.add(child.func.attr)

                if used_methods:
                    client_methods[node.name] = used_methods

        return dict(client_methods)


class DIPChecker:
    """依赖倒置原则检查器 (深度优化版)"""

    CONCRETE_PATTERNS = [
        "impl", "concrete", "service", "repository", "dao", "client", "adapter"
    ]

    HIGH_LEVEL_INDICATORS = [
        'Service', 'Manager', 'Controller', 'Handler', 'Processor', 'Coordinator', 'Orchestrator'
    ]

    ABSTRACT_INDICATORS = [
        'Abstract', 'Base', 'Interface', 'I', 'Protocol', 'ABC'
    ]

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.violations: List[Violation] = []
        self.dependency_layers: Dict[str, DependencyLayer] = {}

    def check(self, py_file: Path, tree: ast.AST, source: str) -> List[Violation]:
        violations = []

        violations.extend(self._check_imports(py_file, tree))
        violations.extend(self._check_class_dependencies(py_file, tree))
        violations.extend(self._check_dependency_direction(py_file, tree))
        violations.extend(self._check_abstraction_stability(py_file, tree))

        return violations

    def _check_imports(self, py_file: Path, tree: ast.AST) -> List[Violation]:
        violations = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module:
                    for alias in node.names:
                        module_lower = node.module.lower()
                        if any(kw in module_lower for kw in self.CONCRETE_PATTERNS):
                            if not self._is_abstract_name(alias.name):
                                violations.append(Violation(
                                    principle=PrincipleType.DIP,
                                    file_path=str(py_file),
                                    line_number=node.lineno,
                                    code_element=alias.name,
                                    description=f"可能直接依赖了具体实现 '{alias.name}' (from {node.module})，建议依赖抽象",
                                    severity=SeverityLevel.LOW,
                                    suggestion="考虑通过依赖注入或抽象接口来解耦，高层模块不应依赖低层模块",
                                    details={"module": node.module, "import_name": alias.name},
                                    confidence=0.6,
                                    impact_score=2
                                ))

        return violations

    def _check_class_dependencies(self, py_file: Path, tree: ast.AST) -> List[Violation]:
        violations = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if self._is_high_level_module(node):
                    concrete_deps = self._find_concrete_dependencies(node)
                    for dep in concrete_deps:
                        violations.append(Violation(
                            principle=PrincipleType.DIP,
                            file_path=str(py_file),
                            line_number=node.lineno,
                            code_element=node.name,
                            description=f"高层模块 '{node.name}' 直接依赖具体实现 '{dep}'",
                            severity=SeverityLevel.MEDIUM,
                            suggestion="通过接口或抽象类进行依赖，实现依赖倒置",
                            details={"concrete_dependency": dep},
                            confidence=0.8,
                            impact_score=4
                        ))

        return violations

    def _check_dependency_direction(self, py_file: Path, tree: ast.AST) -> List[Violation]:
        violations = []

        class_layers: Dict[str, int] = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_layers[node.name] = self._determine_layer(node)

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                current_layer = class_layers.get(node.name, 0)

                for dep in self._get_class_dependencies(node):
                    dep_layer = class_layers.get(dep, 0)

                    if current_layer > 0 and dep_layer > 0 and current_layer < dep_layer:
                        violations.append(Violation(
                            principle=PrincipleType.DIP,
                            file_path=str(py_file),
                            line_number=node.lineno,
                            code_element=node.name,
                            description=f"高层模块 '{node.name}' (层{current_layer}) 依赖低层模块 '{dep}' (层{dep_layer})，违反依赖方向",
                            severity=SeverityLevel.MEDIUM,
                            suggestion="高层模块应依赖抽象，抽象不应依赖细节",
                            details={
                                "current_layer": current_layer,
                                "dependency_layer": dep_layer,
                                "dependency": dep
                            },
                            confidence=0.7,
                            impact_score=5
                        ))

        return violations

    def _check_abstraction_stability(self, py_file: Path, tree: ast.AST) -> List[Violation]:
        violations = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if self._is_abstract_class(node):
                    concrete_deps = self._find_concrete_dependencies(node)
                    if concrete_deps:
                        violations.append(Violation(
                            principle=PrincipleType.DIP,
                            file_path=str(py_file),
                            line_number=node.lineno,
                            code_element=node.name,
                            description=f"抽象类 '{node.name}' 依赖具体实现: {concrete_deps}，抽象应依赖抽象",
                            severity=SeverityLevel.HIGH,
                            suggestion="抽象类应只依赖其他抽象，保持稳定性",
                            details={"concrete_dependencies": concrete_deps},
                            confidence=0.85,
                            impact_score=6
                        ))

        return violations

    def _is_high_level_module(self, class_node: ast.ClassDef) -> bool:
        return any(kw in class_node.name for kw in self.HIGH_LEVEL_INDICATORS)

    def _is_abstract_class(self, class_node: ast.ClassDef) -> bool:
        for base in class_node.bases:
            if isinstance(base, ast.Name) and base.id in ('ABC', 'ABCMeta'):
                return True

        for item in class_node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for decorator in item.decorator_list:
                    if isinstance(decorator, ast.Name) and decorator.id == 'abstractmethod':
                        return True

        return False

    def _is_abstract_name(self, name: str) -> bool:
        return any(name.startswith(indicator) or name.endswith(indicator)
                   for indicator in self.ABSTRACT_INDICATORS)

    def _find_concrete_dependencies(self, class_node: ast.ClassDef) -> List[str]:
        concrete_deps = []

        for child in ast.walk(class_node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    name = child.func.id
                    if not self._is_abstract_name(name):
                        if name[0].isupper() and name not in ('List', 'Dict', 'Set', 'Tuple', 'Optional', 'Any'):
                            if name not in concrete_deps:
                                concrete_deps.append(name)

        return concrete_deps

    def _determine_layer(self, class_node: ast.ClassDef) -> int:
        name = class_node.name

        if any(kw in name for kw in ['Controller', 'API', 'View', 'Handler']):
            return 1
        elif any(kw in name for kw in ['Service', 'Manager', 'Processor', 'Orchestrator']):
            return 2
        elif any(kw in name for kw in ['Repository', 'DAO', 'Gateway', 'Client']):
            return 3
        elif any(kw in name for kw in ['Model', 'Entity', 'Domain']):
            return 4
        else:
            return 0

    def _get_class_dependencies(self, class_node: ast.ClassDef) -> Set[str]:
        deps = set()

        for item in class_node.body:
            if isinstance(item, ast.AnnAssign):
                if item.annotation:
                    type_name = self._extract_type_name(item.annotation)
                    if type_name:
                        deps.add(type_name)

            if isinstance(item, ast.FunctionDef) and item.name == '__init__':
                for arg in item.args.args[1:]:
                    if arg.annotation:
                        type_name = self._extract_type_name(arg.annotation)
                        if type_name:
                            deps.add(type_name)

        return deps

    def _extract_type_name(self, annotation: ast.expr) -> Optional[str]:
        if isinstance(annotation, ast.Name):
            return annotation.id
        elif isinstance(annotation, ast.Attribute):
            if isinstance(annotation.value, ast.Name):
                return f"{annotation.value.id}.{annotation.attr}"
        return None


class CrossFileAnalyzer:
    """跨文件分析器"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self._class_locations: Dict[str, Path] = {}
        self._inheritance_graph: Dict[str, List[str]] = defaultdict(list)

    def analyze(self, project_path: Path) -> Dict[str, Any]:
        self._build_class_index(project_path)

        return {
            "class_count": len(self._class_locations),
            "inheritance_depth": self._calculate_max_inheritance_depth(),
            "potential_srp_violations": self._find_potential_srp_violations(),
            "dependency_clusters": self._find_dependency_clusters()
        }

    def _build_class_index(self, project_path: Path) -> None:
        py_files = list(project_path.rglob("*.py"))

        for py_file in py_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    source = f.read()
                tree = ast.parse(source)

                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        self._class_locations[node.name] = py_file

                        for base in node.bases:
                            if isinstance(base, ast.Name):
                                self._inheritance_graph[base.id].append(node.name)

            except Exception as e:
                self.logger.warning(f"分析文件失败 {py_file}: {e}")

    def _calculate_max_inheritance_depth(self) -> int:
        def get_depth(class_name: str, visited: Set[str]) -> int:
            if class_name in visited:
                return 0
            visited.add(class_name)

            children = self._inheritance_graph.get(class_name, [])
            if not children:
                return 1

            return 1 + max(get_depth(child, visited.copy()) for child in children)

        if not self._inheritance_graph:
            return 0

        root_classes = set(self._inheritance_graph.keys()) - set(
            child for children in self._inheritance_graph.values() for child in children
        )

        if not root_classes:
            return 0

        return max(get_depth(root, set()) for root in root_classes)

    def _find_potential_srp_violations(self) -> List[Dict[str, Any]]:
        violations = []

        for class_name, file_path in self._class_locations.items():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    source = f.read()
                tree = ast.parse(source)

                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef) and node.name == class_name:
                        lcom, groups = LCOMCalculator.calculate(node)
                        if lcom > 0.6 and len(groups) > 2:
                            violations.append({
                                "class_name": class_name,
                                "file_path": str(file_path),
                                "lcom_score": lcom,
                                "method_groups": len(groups)
                            })

            except Exception:
                pass

        return violations

    def _find_dependency_clusters(self) -> List[List[str]]:
        clusters: List[Set[str]] = []

        for class_name in self._class_locations.keys():
            related = {class_name}
            related.update(self._inheritance_graph.get(class_name, []))

            for parent, children in self._inheritance_graph.items():
                if class_name in children:
                    related.add(parent)

            merged = False
            for cluster in clusters:
                if cluster & related:
                    cluster.update(related)
                    merged = True
                    break

            if not merged:
                clusters.append(related)

        return [list(c) for c in clusters if len(c) > 1]


class SOLIDPrincipleChecker:
    """SOLID原则检查器主类 (深度优化版)"""

    def __init__(
        self,
        project_path: Optional[Path] = None,
        thresholds: Optional[Dict[str, int]] = None,
        logger: Optional[logging.Logger] = None,
        enable_cross_file: bool = True
    ):
        self.project_path = project_path or Path.cwd()
        self.logger = logger or self._setup_logger()
        self.enable_cross_file = enable_cross_file

        self.srp_checker = SRPChecker(self.logger, thresholds)
        self.ocp_checker = OCPChecker(self.logger)
        self.lsp_checker = LSPChecker(self.logger)
        self.isp_checker = ISPChecker(self.logger)
        self.dip_checker = DIPChecker(self.logger)
        self.cross_file_analyzer = CrossFileAnalyzer(self.logger)

        self._checked_files: int = 0
        self._total_elements: int = 0

    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger("SOLIDPrincipleChecker")
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setLevel(logging.INFO)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def analyze(self, target_path: Optional[Path] = None) -> SOLIDReport:
        self.logger.info("开始SOLID原则深度检查...")

        target = target_path or self.project_path
        py_files = list(target.rglob("*.py")) if target.is_dir() else [target]

        principle_violations: Dict[str, List[Violation]] = {
            "SRP": [],
            "OCP": [],
            "LSP": [],
            "ISP": [],
            "DIP": []
        }

        for py_file in py_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    source = f.read()
                tree = ast.parse(source)

                principle_violations["SRP"].extend(
                    self.srp_checker.check(py_file, tree, source)
                )
                principle_violations["OCP"].extend(
                    self.ocp_checker.check(py_file, tree, source)
                )
                principle_violations["LSP"].extend(
                    self.lsp_checker.check(py_file, tree)
                )
                principle_violations["ISP"].extend(
                    self.isp_checker.check(py_file, tree)
                )
                principle_violations["DIP"].extend(
                    self.dip_checker.check(py_file, tree, source)
                )

                self._checked_files += 1

            except Exception as e:
                self.logger.warning(f"分析文件失败 {py_file}: {e}")

        principle_reports = self._build_principle_reports(principle_violations)
        overall_score = self._calculate_overall_score(principle_reports)
        overall_status = self._determine_overall_status(overall_score)

        cross_file_analysis = {}
        if self.enable_cross_file:
            cross_file_analysis = self.cross_file_analyzer.analyze(target)

        summary = self._build_summary(principle_reports, cross_file_analysis)
        recommendations = self._generate_detailed_recommendations(principle_reports)

        return SOLIDReport(
            timestamp=datetime.now().isoformat(),
            project_path=str(target),
            overall_score=overall_score,
            overall_status=overall_status,
            principle_reports=principle_reports,
            cross_file_analysis=cross_file_analysis,
            summary=summary,
            recommendations=recommendations
        )

    def _build_principle_reports(
        self,
        violations: Dict[str, List[Violation]]
    ) -> Dict[str, PrincipleReport]:
        reports = {}

        principle_map = {
            "SRP": PrincipleType.SRP,
            "OCP": PrincipleType.OCP,
            "LSP": PrincipleType.LSP,
            "ISP": PrincipleType.ISP,
            "DIP": PrincipleType.DIP
        }

        for key, principle in principle_map.items():
            principle_violations = violations[key]

            critical_count = sum(1 for v in principle_violations if v.severity == SeverityLevel.CRITICAL)
            high_count = sum(1 for v in principle_violations if v.severity == SeverityLevel.HIGH)
            medium_count = sum(1 for v in principle_violations if v.severity == SeverityLevel.MEDIUM)
            low_count = sum(1 for v in principle_violations if v.severity == SeverityLevel.LOW)

            weighted_score = (
                critical_count * 25 +
                high_count * 15 +
                medium_count * 8 +
                low_count * 3
            )
            score = max(0, 100 - weighted_score)

            if score >= 80:
                status = ComplianceStatus.COMPLIANT
            elif score >= 50:
                status = ComplianceStatus.PARTIAL
            else:
                status = ComplianceStatus.NON_COMPLIANT

            metrics = {}
            if key == "SRP":
                metrics["cohesion_analysis"] = {
                    k: v.to_dict() for k, v in self.srp_checker.cohesion_metrics.items()
                }
            elif key == "OCP":
                metrics["extension_points"] = [
                    ep.to_dict() for ep in self.ocp_checker.extension_points
                ]

            reports[key] = PrincipleReport(
                principle=principle,
                status=status,
                score=score,
                violations=principle_violations,
                checked_elements=self._checked_files,
                compliant_elements=max(0, self._checked_files - len(principle_violations)),
                metrics=metrics
            )

        return reports

    def _calculate_overall_score(self, reports: Dict[str, PrincipleReport]) -> float:
        if not reports:
            return 100.0

        weights = {
            "SRP": 1.0,
            "OCP": 1.0,
            "LSP": 1.2,
            "ISP": 0.8,
            "DIP": 1.0
        }

        total_weight = sum(weights.values())
        weighted_sum = sum(
            reports[k].score * weights.get(k, 1.0)
            for k in reports.keys()
        )

        return weighted_sum / total_weight

    def _determine_overall_status(self, score: float) -> ComplianceStatus:
        if score >= 80:
            return ComplianceStatus.COMPLIANT
        elif score >= 50:
            return ComplianceStatus.PARTIAL
        else:
            return ComplianceStatus.NON_COMPLIANT

    def _build_summary(
        self,
        reports: Dict[str, PrincipleReport],
        cross_file: Dict[str, Any]
    ) -> Dict[str, Any]:
        total_violations = sum(len(r.violations) for r in reports.values())

        severity_breakdown = defaultdict(int)
        for report in reports.values():
            for violation in report.violations:
                severity_breakdown[violation.severity.value] += 1

        impact_analysis = self._analyze_impact(reports)

        return {
            "total_files_checked": self._checked_files,
            "total_violations": total_violations,
            "severity_breakdown": dict(severity_breakdown),
            "principle_scores": {
                k: v.score for k, v in reports.items()
            },
            "impact_analysis": impact_analysis,
            "cross_file_metrics": cross_file
        }

    def _analyze_impact(self, reports: Dict[str, PrincipleReport]) -> Dict[str, Any]:
        total_impact = 0.0
        high_impact_violations = []

        for key, report in reports.items():
            for violation in report.violations:
                total_impact += violation.impact_score
                if violation.impact_score > 5:
                    high_impact_violations.append({
                        "principle": key,
                        "element": violation.code_element,
                        "impact": violation.impact_score,
                        "file": violation.file_path
                    })

        return {
            "total_impact_score": total_impact,
            "high_impact_count": len(high_impact_violations),
            "high_impact_violations": sorted(
                high_impact_violations,
                key=lambda x: x["impact"],
                reverse=True
            )[:10]
        }

    def _generate_detailed_recommendations(
        self,
        reports: Dict[str, PrincipleReport]
    ) -> List[Dict[str, Any]]:
        recommendations = []

        for key, report in reports.items():
            if report.score < 80:
                if key == "SRP":
                    recommendations.append({
                        "priority": "high" if report.score < 50 else "medium",
                        "principle": "SRP",
                        "title": "拆分大类，提高内聚性",
                        "description": "发现多个类承担过多职责，建议按职责拆分",
                        "actions": [
                            "使用LCOM指标识别低内聚类",
                            "按方法分组拆分类",
                            "分离数据集群到独立类"
                        ],
                        "affected_count": len(report.violations)
                    })
                elif key == "OCP":
                    recommendations.append({
                        "priority": "high" if report.score < 50 else "medium",
                        "principle": "OCP",
                        "title": "消除类型判断，使用多态",
                        "description": "发现多处类型检查链，建议使用设计模式重构",
                        "actions": [
                            "使用策略模式替代if-else类型判断",
                            "使用工厂模式封装对象创建",
                            "提取扩展点，支持未来扩展"
                        ],
                        "affected_count": len(report.violations)
                    })
                elif key == "LSP":
                    recommendations.append({
                        "priority": "high",
                        "principle": "LSP",
                        "title": "确保子类可替换基类",
                        "description": "发现继承关系中的行为不一致",
                        "actions": [
                            "检查并修复方法签名不兼容",
                            "确保前置条件不加强",
                            "确保后置条件不减弱"
                        ],
                        "affected_count": len(report.violations)
                    })
                elif key == "ISP":
                    recommendations.append({
                        "priority": "medium",
                        "principle": "ISP",
                        "title": "拆分胖接口",
                        "description": "发现接口包含过多方法，建议拆分",
                        "actions": [
                            "按客户端需求拆分接口",
                            "移除未使用的方法",
                            "创建专用接口"
                        ],
                        "affected_count": len(report.violations)
                    })
                elif key == "DIP":
                    recommendations.append({
                        "priority": "high" if report.score < 50 else "medium",
                        "principle": "DIP",
                        "title": "依赖抽象而非具体实现",
                        "description": "发现高层模块直接依赖低层实现",
                        "actions": [
                            "引入抽象接口",
                            "使用依赖注入",
                            "确保抽象层稳定性"
                        ],
                        "affected_count": len(report.violations)
                    })

        return sorted(recommendations, key=lambda x: (
            {"high": 0, "medium": 1, "low": 2}[x["priority"]]
        ))

    def print_report(self, report: SOLIDReport) -> None:
        print("\n" + "=" * 80)
        print("SOLID原则合规性检查报告 (深度优化版)")
        print("=" * 80)
        print(f"项目路径: {report.project_path}")
        print(f"检查时间: {report.timestamp}")
        print(f"总体得分: {report.overall_score:.1f}/100")
        print(f"总体状态: {report.overall_status.value}")

        print("\n" + "-" * 80)
        print("各原则得分")
        print("-" * 80)

        for key, principle_report in report.principle_reports.items():
            status_icon = "✅" if principle_report.status == ComplianceStatus.COMPLIANT else "⚠️" if principle_report.status == ComplianceStatus.PARTIAL else "❌"
            print(f"  {status_icon} {key} ({principle_report.principle.value}): {principle_report.score:.1f}/100")
            if principle_report.violations:
                print(f"      违规数: {len(principle_report.violations)}")

        print("\n" + "-" * 80)
        print("违规详情")
        print("-" * 80)

        for key, principle_report in report.principle_reports.items():
            if principle_report.violations:
                print(f"\n【{key}】违规:")
                for violation in principle_report.violations[:5]:
                    severity_icon = {
                        SeverityLevel.CRITICAL: "🔴",
                        SeverityLevel.HIGH: "🟠",
                        SeverityLevel.MEDIUM: "🟡",
                        SeverityLevel.LOW: "🔵",
                        SeverityLevel.INFO: "⚪"
                    }.get(violation.severity, "⚪")
                    print(f"  {severity_icon} [{violation.severity.value.upper()}] {violation.file_path}:{violation.line_number}")
                    print(f"      元素: {violation.code_element}")
                    print(f"      描述: {violation.description}")
                    print(f"      建议: {violation.suggestion}")
                    print(f"      置信度: {violation.confidence:.0%} | 影响分: {violation.impact_score:.1f}")

                if len(principle_report.violations) > 5:
                    print(f"  ... 还有 {len(principle_report.violations) - 5} 个违规未显示")

        if report.cross_file_analysis:
            print("\n" + "-" * 80)
            print("跨文件分析")
            print("-" * 80)
            print(f"  类总数: {report.cross_file_analysis.get('class_count', 0)}")
            print(f"  最大继承深度: {report.cross_file_analysis.get('inheritance_depth', 0)}")

        print("\n" + "-" * 80)
        print("改进建议")
        print("-" * 80)
        for i, rec in enumerate(report.recommendations[:10], 1):
            priority_icon = {"high": "🔴", "medium": "🟡", "low": "🔵"}.get(rec["priority"], "⚪")
            print(f"  {i}. {priority_icon} [{rec['principle']}] {rec['title']}")
            print(f"     {rec['description']}")

    def save_report(self, report: SOLIDReport, output_path: str) -> None:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)

        self.logger.info(f"报告已保存: {path}")


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="SOLID原则检查器 (深度优化版)",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--path",
        type=str,
        default=".",
        help="要检查的路径 (默认: 当前目录)"
    )
    parser.add_argument(
        "--output",
        type=str,
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
        "--principles",
        type=str,
        help="要检查的原则，逗号分隔 (如: SRP,OCP)"
    )
    parser.add_argument(
        "--cross-file",
        action="store_true",
        default=True,
        help="启用跨文件分析 (默认: 启用)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="启用详细日志输出"
    )

    args = parser.parse_args()

    logger = logging.getLogger("SOLIDPrincipleChecker")
    logger.setLevel(logging.DEBUG if args.verbose else logging.INFO)

    checker = SOLIDPrincipleChecker(
        project_path=Path(args.path),
        logger=logger,
        enable_cross_file=args.cross_file
    )

    report = checker.analyze()

    if args.output == "console":
        checker.print_report(report)
    else:
        print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))

    if args.output_file:
        checker.save_report(report, args.output_file)

    return 0 if report.overall_status == ComplianceStatus.COMPLIANT else 1


if __name__ == "__main__":
    sys.exit(main())
