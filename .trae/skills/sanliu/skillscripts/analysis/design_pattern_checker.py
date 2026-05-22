#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
设计模式检查器 - Sanliu 技能 (深度优化版)

提供设计模式识别、验证和推荐功能，包括：
- 创建型模式：单例、工厂、抽象工厂、建造者、原型
- 结构型模式：适配器、桥接、组合、装饰器、外观、享元、代理、仓储
- 行为型模式：责任链、命令、迭代器、中介者、备忘录、观察者、状态、策略、模板方法、访问者
- 架构模式：依赖注入、仓储、工作单元

使用示例:
    python design_pattern_checker.py
    python design_pattern_checker.py --path ./src
    python design_pattern_checker.py --output json --output-file report.json
    python design_pattern_checker.py --patterns singleton,factory,observer
    python design_pattern_checker.py --recommend
    python design_pattern_checker.py --deep-analysis
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


class PatternCategory(Enum):
    CREATIONAL = "创建型模式"
    STRUCTURAL = "结构型模式"
    BEHAVIORAL = "行为型模式"
    ARCHITECTURAL = "架构模式"


class PatternType(Enum):
    SINGLETON = "Singleton"
    FACTORY = "Factory"
    ABSTRACT_FACTORY = "Abstract Factory"
    BUILDER = "Builder"
    PROTOTYPE = "Prototype"
    ADAPTER = "Adapter"
    BRIDGE = "Bridge"
    COMPOSITE = "Composite"
    DECORATOR = "Decorator"
    FACADE = "Facade"
    FLYWEIGHT = "Flyweight"
    PROXY = "Proxy"
    CHAIN_OF_RESPONSIBILITY = "Chain of Responsibility"
    COMMAND = "Command"
    INTERPRETER = "Interpreter"
    ITERATOR = "Iterator"
    MEDIATOR = "Mediator"
    MEMENTO = "Memento"
    OBSERVER = "Observer"
    STATE = "State"
    STRATEGY = "Strategy"
    TEMPLATE_METHOD = "Template Method"
    VISITOR = "Visitor"
    REPOSITORY = "Repository"
    DEPENDENCY_INJECTION = "Dependency Injection"
    UNIT_OF_WORK = "Unit of Work"
    SPECIFICATION = "Specification"


class DetectionConfidence(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class PatternStatus(Enum):
    CORRECT = "correct"
    PARTIAL = "partial"
    INCORRECT = "incorrect"
    MISSING = "missing"
    ANTI_PATTERN = "anti_pattern"


class PatternQuality(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"


@dataclass
class PatternSignature:
    pattern_type: PatternType
    required_elements: List[str]
    optional_elements: List[str]
    forbidden_elements: List[str]
    structural_hints: List[str]
    behavioral_hints: List[str]

    def match_score(self, found_elements: Set[str]) -> float:
        required_matches = sum(1 for e in self.required_elements if e in found_elements)
        optional_matches = sum(1 for e in self.optional_elements if e in found_elements)
        forbidden_matches = sum(1 for e in self.forbidden_elements if e in found_elements)

        if not self.required_elements:
            required_score = 1.0
        else:
            required_score = required_matches / len(self.required_elements)

        if not self.optional_elements:
            optional_score = 1.0
        else:
            optional_score = optional_matches / len(self.optional_elements)

        penalty = forbidden_matches * 0.3

        return max(0, (required_score * 0.7 + optional_score * 0.3) - penalty)


@dataclass
class PatternInstance:
    pattern_type: PatternType
    category: PatternCategory
    file_path: str
    line_number: int
    code_element: str
    confidence: DetectionConfidence
    status: PatternStatus
    description: str
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    quality: PatternQuality = PatternQuality.ACCEPTABLE
    match_score: float = 0.0
    related_patterns: List[str] = field(default_factory=list)
    anti_pattern_warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern_type": self.pattern_type.value,
            "category": self.category.value,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "code_element": self.code_element,
            "confidence": self.confidence.value,
            "status": self.status.value,
            "description": self.description,
            "issues": self.issues,
            "suggestions": self.suggestions,
            "quality": self.quality.value,
            "match_score": self.match_score,
            "related_patterns": self.related_patterns,
            "anti_pattern_warnings": self.anti_pattern_warnings
        }


@dataclass
class PatternRecommendation:
    pattern_type: PatternType
    category: PatternCategory
    context: str
    reason: str
    benefits: List[str]
    implementation_hints: List[str]
    priority: str = "medium"
    estimated_effort: str = "medium"
    related_code_elements: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern_type": self.pattern_type.value,
            "category": self.category.value,
            "context": self.context,
            "reason": self.reason,
            "benefits": self.benefits,
            "implementation_hints": self.implementation_hints,
            "priority": self.priority,
            "estimated_effort": self.estimated_effort,
            "related_code_elements": self.related_code_elements
        }


@dataclass
class PatternRelationship:
    source_pattern: PatternType
    target_pattern: PatternType
    relationship_type: str
    description: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_pattern": self.source_pattern.value,
            "target_pattern": self.target_pattern.value,
            "relationship_type": self.relationship_type,
            "description": self.description
        }


@dataclass
class PatternReport:
    pattern_type: PatternType
    category: PatternCategory
    instances: List[PatternInstance] = field(default_factory=list)
    correct_count: int = 0
    incorrect_count: int = 0
    partial_count: int = 0
    anti_pattern_count: int = 0
    average_quality: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern_type": self.pattern_type.value,
            "category": self.category.value,
            "total_instances": len(self.instances),
            "correct_count": self.correct_count,
            "incorrect_count": self.incorrect_count,
            "partial_count": self.partial_count,
            "anti_pattern_count": self.anti_pattern_count,
            "average_quality": self.average_quality,
            "instances": [i.to_dict() for i in self.instances]
        }


@dataclass
class DesignPatternReport:
    timestamp: str
    project_path: str
    total_patterns_detected: int
    pattern_reports: Dict[str, PatternReport]
    recommendations: List[PatternRecommendation]
    pattern_relationships: List[PatternRelationship]
    anti_pattern_analysis: Dict[str, Any]
    summary: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "project_path": self.project_path,
            "total_patterns_detected": self.total_patterns_detected,
            "pattern_reports": {
                k: v.to_dict() for k, v in self.pattern_reports.items()
            },
            "recommendations": [r.to_dict() for r in self.recommendations],
            "pattern_relationships": [r.to_dict() for r in self.pattern_relationships],
            "anti_pattern_analysis": self.anti_pattern_analysis,
            "summary": self.summary
        }


PATTERN_SIGNATURES: Dict[PatternType, PatternSignature] = {
    PatternType.SINGLETON: PatternSignature(
        pattern_type=PatternType.SINGLETON,
        required_elements=["private_instance", "static_access"],
        optional_elements=["thread_safety", "lazy_init"],
        forbidden_elements=["public_constructor"],
        structural_hints=["_instance", "get_instance", "__new__"],
        behavioral_hints=["single_instance_check", "instance_creation"]
    ),
    PatternType.FACTORY: PatternSignature(
        pattern_type=PatternType.FACTORY,
        required_elements=["create_method"],
        optional_elements=["product_interface", "factory_interface"],
        forbidden_elements=[],
        structural_hints=["Factory", "Creator", "create", "build"],
        behavioral_hints=["object_creation", "type_selection"]
    ),
    PatternType.ABSTRACT_FACTORY: PatternSignature(
        pattern_type=PatternType.ABSTRACT_FACTORY,
        required_elements=["abstract_factory", "concrete_factory", "abstract_product"],
        optional_elements=["product_family"],
        forbidden_elements=[],
        structural_hints=["AbstractFactory", "ConcreteFactory", "ABC"],
        behavioral_hints=["family_creation", "factory_hierarchy"]
    ),
    PatternType.BUILDER: PatternSignature(
        pattern_type=PatternType.BUILDER,
        required_elements=["builder_class", "build_method"],
        optional_elements=["director", "fluent_interface", "step_methods"],
        forbidden_elements=[],
        structural_hints=["Builder", "build", "with_", "set_"],
        behavioral_hints=["step_by_step_construction", "complex_object_creation"]
    ),
    PatternType.OBSERVER: PatternSignature(
        pattern_type=PatternType.OBSERVER,
        required_elements=["subject", "observer", "notify_method"],
        optional_elements=["attach_method", "detach_method", "update_method"],
        forbidden_elements=[],
        structural_hints=["Observer", "Subject", "Listener", "notify", "subscribe"],
        behavioral_hints=["event_notification", "state_propagation"]
    ),
    PatternType.STRATEGY: PatternSignature(
        pattern_type=PatternType.STRATEGY,
        required_elements=["strategy_interface", "concrete_strategy", "context"],
        optional_elements=["strategy_selection"],
        forbidden_elements=["type_checking_in_context"],
        structural_hints=["Strategy", "Context", "execute", "algorithm"],
        behavioral_hints=["algorithm_interchange", "runtime_selection"]
    ),
    PatternType.DECORATOR: PatternSignature(
        pattern_type=PatternType.DECORATOR,
        required_elements=["component_interface", "decorator_class", "wrapped_component"],
        optional_elements=["concrete_decorator", "additional_behavior"],
        forbidden_elements=[],
        structural_hints=["Decorator", "Wrapper", "_wrapped", "_component"],
        behavioral_hints=["behavior_addition", "delegation"]
    ),
    PatternType.ADAPTER: PatternSignature(
        pattern_type=PatternType.ADAPTER,
        required_elements=["target_interface", "adaptee", "adapter_class"],
        optional_elements=["object_adapter", "class_adapter"],
        forbidden_elements=[],
        structural_hints=["Adapter", "Wrapper", "Converter", "_adaptee"],
        behavioral_hints=["interface_conversion", "delegation_to_adaptee"]
    ),
    PatternType.REPOSITORY: PatternSignature(
        pattern_type=PatternType.REPOSITORY,
        required_elements=["repository_interface", "crud_methods"],
        optional_elements=["query_methods", "unit_of_work"],
        forbidden_elements=["business_logic"],
        structural_hints=["Repository", "DAO", "get", "save", "find", "delete"],
        behavioral_hints=["data_access_abstraction", "collection_like_interface"]
    ),
    PatternType.DEPENDENCY_INJECTION: PatternSignature(
        pattern_type=PatternType.DEPENDENCY_INJECTION,
        required_elements=["dependency_parameter", "injection_point"],
        optional_elements=["container", "injector", "interface_dependency"],
        forbidden_elements=["concrete_instantiation"],
        structural_hints=["__init__", "inject", "container", "register"],
        behavioral_hints=["dependency_passing", "inversion_of_control"]
    ),
    PatternType.COMMAND: PatternSignature(
        pattern_type=PatternType.COMMAND,
        required_elements=["command_interface", "execute_method", "receiver"],
        optional_elements=["undo_method", "command_queue", "invoker"],
        forbidden_elements=[],
        structural_hints=["Command", "execute", "undo", "redo"],
        behavioral_hints=["action_encapsulation", "operation_queueing"]
    ),
    PatternType.TEMPLATE_METHOD: PatternSignature(
        pattern_type=PatternType.TEMPLATE_METHOD,
        required_elements=["template_method", "primitive_operations"],
        optional_elements=["hook_methods", "abstract_class"],
        forbidden_elements=[],
        structural_hints=["template", "hook", "step", "abstract"],
        behavioral_hints=["algorithm_skeleton", "step_override"]
    ),
    PatternType.STATE: PatternSignature(
        pattern_type=PatternType.STATE,
        required_elements=["state_interface", "concrete_states", "context"],
        optional_elements=["state_transitions"],
        forbidden_elements=["state_conditionals"],
        structural_hints=["State", "Context", "handle", "change_state"],
        behavioral_hints=["state_switching", "behavior_variation"]
    ),
    PatternType.CHAIN_OF_RESPONSIBILITY: PatternSignature(
        pattern_type=PatternType.CHAIN_OF_RESPONSIBILITY,
        required_elements=["handler_interface", "successor_link", "handle_method"],
        optional_elements=["chain_construction"],
        forbidden_elements=[],
        structural_hints=["Handler", "successor", "next_", "chain"],
        behavioral_hints=["request_passing", "handler_chain"]
    ),
    PatternType.FACADE: PatternSignature(
        pattern_type=PatternType.FACADE,
        required_elements=["facade_class", "simplified_interface"],
        optional_elements=["subsystem_components"],
        forbidden_elements=[],
        structural_hints=["Facade", "Service", "Manager"],
        behavioral_hints=["interface_simplification", "subsystem_delegation"]
    ),
    PatternType.PROXY: PatternSignature(
        pattern_type=PatternType.PROXY,
        required_elements=["proxy_class", "real_subject", "same_interface"],
        optional_elements=["lazy_init", "access_control", "caching"],
        forbidden_elements=[],
        structural_hints=["Proxy", "_real", "_subject", "remote", "virtual"],
        behavioral_hints=["access_control", "lazy_loading", "caching"]
    ),
    PatternType.COMPOSITE: PatternSignature(
        pattern_type=PatternType.COMPOSITE,
        required_elements=["component_interface", "composite_class", "leaf_class"],
        optional_elements=["child_management"],
        forbidden_elements=[],
        structural_hints=["Component", "Composite", "Leaf", "add", "remove", "children"],
        behavioral_hints=["tree_structure", "uniform_treatment"]
    ),
    PatternType.ITERATOR: PatternSignature(
        pattern_type=PatternType.ITERATOR,
        required_elements=["iterator_interface", "has_next", "next_method"],
        optional_elements=["iterable_collection"],
        forbidden_elements=[],
        structural_hints=["Iterator", "__iter__", "__next__", "has_next"],
        behavioral_hints=["traversal", "element_access"]
    ),
    PatternType.MEDIATOR: PatternSignature(
        pattern_type=PatternType.MEDIATOR,
        required_elements=["mediator_interface", "colleague_classes"],
        optional_elements=["concrete_mediator"],
        forbidden_elements=["direct_colleague_communication"],
        structural_hints=["Mediator", "Colleague", "notify", "send"],
        behavioral_hints=["communication_hub", "decoupling"]
    ),
    PatternType.MEMENTO: PatternSignature(
        pattern_type=PatternType.MEMENTO,
        required_elements=["memento_class", "originator", "caretaker"],
        optional_elements=["state_history"],
        forbidden_elements=[],
        structural_hints=["Memento", "State", "save", "restore", "snapshot"],
        behavioral_hints=["state_capture", "state_restoration"]
    ),
    PatternType.VISITOR: PatternSignature(
        pattern_type=PatternType.VISITOR,
        required_elements=["visitor_interface", "visit_methods", "element_interface"],
        optional_elements=["accept_method", "concrete_visitors"],
        forbidden_elements=[],
        structural_hints=["Visitor", "visit", "accept", "Element"],
        behavioral_hints=["operation_separation", "double_dispatch"]
    ),
    PatternType.BRIDGE: PatternSignature(
        pattern_type=PatternType.BRIDGE,
        required_elements=["abstraction", "implementation", "bridge_link"],
        optional_elements=["refined_abstraction", "concrete_implementation"],
        forbidden_elements=[],
        structural_hints=["Bridge", "Impl", "implementation", "_impl"],
        behavioral_hints=["decoupling", "independent_variation"]
    ),
    PatternType.PROTOTYPE: PatternSignature(
        pattern_type=PatternType.PROTOTYPE,
        required_elements=["clone_method", "prototype_interface"],
        optional_elements=["deep_copy", "shallow_copy"],
        forbidden_elements=[],
        structural_hints=["Prototype", "clone", "copy", "__copy__"],
        behavioral_hints=["object_copying", "instance_duplication"]
    ),
    PatternType.FLYWEIGHT: PatternSignature(
        pattern_type=PatternType.FLYWEIGHT,
        required_elements=["flyweight_factory", "shared_state", "intrinsic_state"],
        optional_elements=["extrinsic_state", "flyweight_pool"],
        forbidden_elements=[],
        structural_hints=["Flyweight", "Factory", "shared", "pool", "cache"],
        behavioral_hints=["state_sharing", "memory_optimization"]
    ),
    PatternType.INTERPRETER: PatternSignature(
        pattern_type=PatternType.INTERPRETER,
        required_elements=["abstract_expression", "terminal_expression", "non_terminal_expression"],
        optional_elements=["context", "parser"],
        forbidden_elements=[],
        structural_hints=["Expression", "interpret", "Context", "parse"],
        behavioral_hints=["language_interpretation", "grammar_evaluation"]
    ),
    PatternType.UNIT_OF_WORK: PatternSignature(
        pattern_type=PatternType.UNIT_OF_WORK,
        required_elements=["transaction_tracking", "commit_method", "rollback_method"],
        optional_elements=["change_tracking", "identity_map"],
        forbidden_elements=[],
        structural_hints=["UnitOfWork", "Transaction", "commit", "rollback"],
        behavioral_hints=["transaction_management", "atomic_operations"]
    ),
    PatternType.SPECIFICATION: PatternSignature(
        pattern_type=PatternType.SPECIFICATION,
        required_elements=["specification_interface", "is_satisfied_method"],
        optional_elements=["composite_specifications", "specification_combiner"],
        forbidden_elements=[],
        structural_hints=["Specification", "is_satisfied", "and", "or", "not"],
        behavioral_hints=["rule_encapsulation", "predicate_composition"]
    ),
}


class PatternSignatureAnalyzer:
    """模式签名分析器"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def analyze_class(self, class_node: ast.ClassDef, py_file: Path) -> Dict[PatternType, float]:
        scores: Dict[PatternType, float] = {}
        found_elements = self._extract_pattern_elements(class_node)

        for pattern_type, signature in PATTERN_SIGNATURES.items():
            score = signature.match_score(found_elements)
            if score > 0.3:
                scores[pattern_type] = score

        return scores

    def _extract_pattern_elements(self, class_node: ast.ClassDef) -> Set[str]:
        elements = set()

        elements.add(f"class:{class_node.name}")

        for item in class_node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                elements.add(f"method:{item.name}")

                if item.name == '__new__':
                    elements.add("private_instance")
                    elements.add("static_access")

                if item.name in ('get_instance', 'getInstance', 'instance'):
                    elements.add("static_access")

                if item.name.startswith('create') or item.name.startswith('build'):
                    elements.add("create_method")

                if item.name in ('build', 'create', 'get_result'):
                    elements.add("build_method")

                if item.name in ('notify', 'emit', 'dispatch', 'publish'):
                    elements.add("notify_method")

                if item.name in ('attach', 'subscribe', 'add_listener', 'register'):
                    elements.add("attach_method")

                if item.name in ('update', 'on_update', 'handle'):
                    elements.add("update_method")

                if item.name in ('execute', 'run', 'apply', 'process'):
                    elements.add("execute_method")

                if item.name in ('clone', 'copy', '__copy__'):
                    elements.add("clone_method")

                if item.name in ('commit', 'save_changes'):
                    elements.add("commit_method")

                if item.name in ('rollback', 'undo_changes'):
                    elements.add("rollback_method")

                if item.name == '__iter__':
                    elements.add("iterator_interface")

                if item.name == '__next__':
                    elements.add("next_method")

                if item.name == 'is_satisfied' or item.name == 'is_satisfied_by':
                    elements.add("is_satisfied_method")

            if isinstance(item, ast.AnnAssign):
                if item.target and isinstance(item.target, ast.Name):
                    attr_name = item.target.id.lower()
                    if attr_name in ('_instance', 'instance', '_singleton'):
                        elements.add("private_instance")
                    if attr_name in ('_wrapped', 'wrapped', '_component', 'component'):
                        elements.add("wrapped_component")
                    if attr_name in ('_adaptee', 'adaptee'):
                        elements.add("adaptee")
                    if attr_name in ('_real_subject', '_real', 'real_subject'):
                        elements.add("real_subject")
                    if attr_name in ('_impl', 'implementation'):
                        elements.add("bridge_link")
                    if attr_name in ('successor', 'next_handler', 'next_'):
                        elements.add("successor_link")
                    if attr_name in ('_strategy', 'strategy'):
                        elements.add("context")
                    if attr_name in ('_state', 'current_state', 'state'):
                        elements.add("context")

        for base in class_node.bases:
            if isinstance(base, ast.Name):
                elements.add(f"base:{base.id}")
                if base.id in ('ABC', 'ABCMeta'):
                    elements.add("abstract_class")
            elif isinstance(base, ast.Attribute):
                elements.add(f"base:{base.attr}")

        if any(m.name == '__init__' for m in class_node.body if isinstance(m, ast.FunctionDef)):
            init_method = next(m for m in class_node.body if isinstance(m, ast.FunctionDef) and m.name == '__init__')
            if len(init_method.args.args) > 1:
                elements.add("dependency_parameter")
                elements.add("injection_point")

        return elements


class SingletonDetector:
    """单例模式检测器 (深度优化版)"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.signature_analyzer = PatternSignatureAnalyzer(logger)

    def detect(self, py_file: Path, tree: ast.AST) -> List[PatternInstance]:
        instances = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                instance = self._check_singleton(py_file, node)
                if instance:
                    instances.append(instance)

        return instances

    def _check_singleton(self, py_file: Path, class_node: ast.ClassDef) -> Optional[PatternInstance]:
        has_new_method = False
        has_instance_var = False
        has_get_instance = False
        instance_var_name = ""
        is_thread_safe = False
        uses_module_level = False

        for item in class_node.body:
            if isinstance(item, ast.FunctionDef):
                if item.name == '__new__':
                    has_new_method = True
                    for child in ast.walk(item):
                        if isinstance(child, ast.Attribute):
                            if child.attr in ('_instance', '_singleton', 'instance'):
                                has_instance_var = True
                                instance_var_name = child.attr

                if item.name in ('get_instance', 'getInstance', 'instance'):
                    has_get_instance = True

        if not (has_new_method or has_get_instance):
            return None

        issues = []
        suggestions = []
        anti_pattern_warnings = []

        if has_new_method and not has_instance_var:
            issues.append("单例实现可能不完整：缺少实例变量")
            suggestions.append("添加类变量存储唯一实例")

        if has_get_instance and not has_instance_var:
            issues.append("get_instance方法可能未正确实现")
            suggestions.append("确保get_instance返回唯一实例")

        is_thread_safe = self._check_thread_safety(class_node)
        if not is_thread_safe:
            issues.append("单例实现可能不是线程安全的")
            suggestions.append("考虑使用线程锁确保线程安全")

        uses_metaclass = self._check_metaclass_singleton(class_node)
        if uses_metaclass:
            suggestions.append("使用元类实现单例是更Pythonic的方式")

        if self._check_global_state_abuse(class_node):
            anti_pattern_warnings.append("过度使用全局状态可能是反模式")
            suggestions.append("考虑使用依赖注入替代全局单例")

        signature_scores = self.signature_analyzer.analyze_class(class_node, py_file)
        match_score = signature_scores.get(PatternType.SINGLETON, 0.0)

        confidence = DetectionConfidence.HIGH if has_instance_var else DetectionConfidence.MEDIUM
        status = PatternStatus.CORRECT if not issues else PatternStatus.PARTIAL
        quality = self._determine_quality(len(issues), len(anti_pattern_warnings))

        return PatternInstance(
            pattern_type=PatternType.SINGLETON,
            category=PatternCategory.CREATIONAL,
            file_path=str(py_file),
            line_number=class_node.lineno,
            code_element=class_node.name,
            confidence=confidence,
            status=status,
            description=f"类 '{class_node.name}' 实现了单例模式",
            issues=issues,
            suggestions=suggestions,
            quality=quality,
            match_score=match_score,
            anti_pattern_warnings=anti_pattern_warnings
        )

    def _check_thread_safety(self, class_node: ast.ClassDef) -> bool:
        for item in class_node.body:
            if isinstance(item, ast.FunctionDef):
                for child in ast.walk(item):
                    if isinstance(child, ast.Name):
                        if child.id in ('Lock', 'RLock', 'threading', 'synchronized'):
                            return True
                    if isinstance(child, ast.Attribute):
                        if child.attr in ('acquire', 'release', 'lock'):
                            return True
        return False

    def _check_metaclass_singleton(self, class_node: ast.ClassDef) -> bool:
        for keyword in class_node.keywords:
            if keyword.arg == 'metaclass':
                if isinstance(keyword.value, ast.Name):
                    if 'Singleton' in keyword.value.id:
                        return True
        return False

    def _check_global_state_abuse(self, class_node: ast.ClassDef) -> bool:
        method_count = sum(1 for item in class_node.body if isinstance(item, ast.FunctionDef))
        return method_count > 15

    def _determine_quality(self, issue_count: int, warning_count: int) -> PatternQuality:
        total = issue_count + warning_count
        if total == 0:
            return PatternQuality.EXCELLENT
        elif total == 1:
            return PatternQuality.GOOD
        elif total <= 3:
            return PatternQuality.ACCEPTABLE
        else:
            return PatternQuality.POOR


class FactoryDetector:
    """工厂模式检测器 (深度优化版)"""

    FACTORY_KEYWORDS = ['Factory', 'Creator', 'Builder', 'Producer']

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.signature_analyzer = PatternSignatureAnalyzer(logger)

    def detect(self, py_file: Path, tree: ast.AST) -> List[PatternInstance]:
        instances = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                instance = self._check_factory(py_file, node, tree)
                if instance:
                    instances.append(instance)

        return instances

    def _check_factory(self, py_file: Path, class_node: ast.ClassDef, tree: ast.AST) -> Optional[PatternInstance]:
        is_factory = any(kw in class_node.name for kw in self.FACTORY_KEYWORDS)

        create_methods = []
        product_types = []
        for item in class_node.body:
            if isinstance(item, ast.FunctionDef):
                method_lower = item.name.lower()
                if any(kw in method_lower for kw in ['create', 'build', 'make', 'produce', 'get']):
                    create_methods.append(item.name)
                    product_type = self._extract_product_type(item)
                    if product_type:
                        product_types.append(product_type)

        if not is_factory and not create_methods:
            return None

        issues = []
        suggestions = []
        anti_pattern_warnings = []

        if not create_methods:
            issues.append("工厂类缺少创建方法")
            suggestions.append("添加create/build方法来创建产品对象")

        has_abstract = self._check_abstract_factory(class_node)
        has_interface = self._check_product_interface(class_node, tree)

        if has_abstract and not has_interface:
            issues.append("抽象工厂缺少产品接口定义")
            suggestions.append("为产品族定义统一的抽象接口")

        if len(product_types) > 3:
            suggestions.append("考虑使用抽象工厂模式处理多个产品类型")

        if self._check_switch_based_creation(class_node):
            anti_pattern_warnings.append("使用switch/if-else选择产品类型可能是反模式")
            suggestions.append("考虑使用注册表或策略模式替代条件判断")

        signature_scores = self.signature_analyzer.analyze_class(class_node, py_file)
        match_score = signature_scores.get(PatternType.FACTORY, 0.0)

        if has_abstract:
            pattern_type = PatternType.ABSTRACT_FACTORY
            description = f"类 '{class_node.name}' 实现了抽象工厂模式"
        else:
            pattern_type = PatternType.FACTORY
            description = f"类 '{class_node.name}' 实现了工厂模式"

        confidence = DetectionConfidence.HIGH if create_methods else DetectionConfidence.LOW
        status = PatternStatus.CORRECT if create_methods and not issues else PatternStatus.PARTIAL
        quality = self._determine_quality(len(issues), len(anti_pattern_warnings))

        return PatternInstance(
            pattern_type=pattern_type,
            category=PatternCategory.CREATIONAL,
            file_path=str(py_file),
            line_number=class_node.lineno,
            code_element=class_node.name,
            confidence=confidence,
            status=status,
            description=description,
            issues=issues,
            suggestions=suggestions,
            quality=quality,
            match_score=match_score,
            anti_pattern_warnings=anti_pattern_warnings
        )

    def _extract_product_type(self, method: ast.FunctionDef) -> Optional[str]:
        for node in ast.walk(method):
            if isinstance(node, ast.Return):
                if isinstance(node.value, ast.Call):
                    if isinstance(node.value.func, ast.Name):
                        return node.value.func.id
        return None

    def _check_abstract_factory(self, class_node: ast.ClassDef) -> bool:
        for base in class_node.bases:
            if isinstance(base, ast.Name):
                if base.id in ('ABC', 'ABCMeta'):
                    return True
            if isinstance(base, ast.Attribute):
                if base.attr in ('ABC', 'ABCMeta'):
                    return True

        for item in class_node.body:
            if isinstance(item, ast.FunctionDef):
                for decorator in item.decorator_list:
                    if isinstance(decorator, ast.Name) and decorator.id == 'abstractmethod':
                        return True

        return False

    def _check_product_interface(self, class_node: ast.ClassDef, tree: ast.AST) -> bool:
        for item in class_node.body:
            if isinstance(item, ast.AnnAssign):
                if item.annotation:
                    return True
        return False

    def _check_switch_based_creation(self, class_node: ast.ClassDef) -> bool:
        for item in class_node.body:
            if isinstance(item, ast.FunctionDef):
                if_count = 0
                for node in ast.walk(item):
                    if isinstance(node, ast.If):
                        if_count += 1
                if if_count > 3:
                    return True
        return False

    def _determine_quality(self, issue_count: int, warning_count: int) -> PatternQuality:
        total = issue_count + warning_count
        if total == 0:
            return PatternQuality.EXCELLENT
        elif total == 1:
            return PatternQuality.GOOD
        elif total <= 3:
            return PatternQuality.ACCEPTABLE
        else:
            return PatternQuality.POOR


class BuilderDetector:
    """建造者模式检测器 (深度优化版)"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.signature_analyzer = PatternSignatureAnalyzer(logger)

    def detect(self, py_file: Path, tree: ast.AST) -> List[PatternInstance]:
        instances = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                instance = self._check_builder(py_file, node)
                if instance:
                    instances.append(instance)

        return instances

    def _check_builder(self, py_file: Path, class_node: ast.ClassDef) -> Optional[PatternInstance]:
        if 'Builder' not in class_node.name:
            return None

        setter_methods = []
        build_method = False
        has_fluent_interface = False
        has_director = False

        for item in class_node.body:
            if isinstance(item, ast.FunctionDef):
                if item.name.lower() in ('build', 'create', 'get_result'):
                    build_method = True
                elif item.name.startswith('set_') or item.name.startswith('with_'):
                    setter_methods.append(item.name)
                    if self._returns_self(item):
                        has_fluent_interface = True

        issues = []
        suggestions = []
        anti_pattern_warnings = []

        if not build_method:
            issues.append("建造者类缺少build方法")
            suggestions.append("添加build方法返回最终构建的对象")

        if len(setter_methods) < 2:
            issues.append("建造者类设置方法较少")
            suggestions.append("添加更多链式设置方法")

        if not has_fluent_interface and setter_methods:
            suggestions.append("考虑实现流式接口（返回self）以支持链式调用")

        signature_scores = self.signature_analyzer.analyze_class(class_node, py_file)
        match_score = signature_scores.get(PatternType.BUILDER, 0.0)

        confidence = DetectionConfidence.HIGH if build_method and setter_methods else DetectionConfidence.MEDIUM
        status = PatternStatus.CORRECT if build_method else PatternStatus.PARTIAL
        quality = self._determine_quality(len(issues), len(anti_pattern_warnings), has_fluent_interface)

        return PatternInstance(
            pattern_type=PatternType.BUILDER,
            category=PatternCategory.CREATIONAL,
            file_path=str(py_file),
            line_number=class_node.lineno,
            code_element=class_node.name,
            confidence=confidence,
            status=status,
            description=f"类 '{class_node.name}' 实现了建造者模式",
            issues=issues,
            suggestions=suggestions,
            quality=quality,
            match_score=match_score
        )

    def _returns_self(self, method: ast.FunctionDef) -> bool:
        for node in ast.walk(method):
            if isinstance(node, ast.Return):
                if isinstance(node.value, ast.Name) and node.value.id == 'self':
                    return True
        return False

    def _determine_quality(self, issue_count: int, warning_count: int, has_fluent: bool) -> PatternQuality:
        total = issue_count + warning_count
        if total == 0 and has_fluent:
            return PatternQuality.EXCELLENT
        elif total <= 1:
            return PatternQuality.GOOD
        elif total <= 3:
            return PatternQuality.ACCEPTABLE
        else:
            return PatternQuality.POOR


class ObserverDetector:
    """观察者模式检测器 (深度优化版)"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.signature_analyzer = PatternSignatureAnalyzer(logger)

    def detect(self, py_file: Path, tree: ast.AST) -> List[PatternInstance]:
        instances = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                instance = self._check_observer(py_file, node)
                if instance:
                    instances.append(instance)

        return instances

    def _check_observer(self, py_file: Path, class_node: ast.ClassDef) -> Optional[PatternInstance]:
        observer_keywords = ['Observer', 'Listener', 'Subscriber', 'EventHandler', 'Callback']
        subject_keywords = ['Subject', 'Observable', 'Publisher', 'Emitter', 'EventSource']

        is_observer = any(kw in class_node.name for kw in observer_keywords)
        is_subject = any(kw in class_node.name for kw in subject_keywords)

        if not is_observer and not is_subject:
            return None

        has_notify = False
        has_subscribe = False
        has_unsubscribe = False
        has_update = False
        observer_list = False

        for item in class_node.body:
            if isinstance(item, ast.FunctionDef):
                method_lower = item.name.lower()
                if any(kw in method_lower for kw in ['notify', 'emit', 'dispatch', 'publish']):
                    has_notify = True
                if any(kw in method_lower for kw in ['subscribe', 'attach', 'add_listener', 'register']):
                    has_subscribe = True
                if any(kw in method_lower for kw in ['unsubscribe', 'detach', 'remove_listener']):
                    has_unsubscribe = True
                if any(kw in method_lower for kw in ['update', 'on_', 'handle']):
                    has_update = True

            if isinstance(item, ast.AnnAssign):
                if item.target and isinstance(item.target, ast.Name):
                    attr_lower = item.target.id.lower()
                    if any(kw in attr_lower for kw in ['observer', 'listener', 'subscriber', 'callback']):
                        observer_list = True

        issues = []
        suggestions = []
        anti_pattern_warnings = []

        if is_subject:
            if not has_notify:
                issues.append("Subject类缺少通知方法")
                suggestions.append("添加notify方法通知所有观察者")
            if not has_subscribe:
                issues.append("Subject类缺少订阅管理方法")
                suggestions.append("添加subscribe/unsubscribe方法管理观察者")
            if not observer_list:
                suggestions.append("添加观察者列表存储订阅者")

        if is_observer and not has_update:
            issues.append("Observer类缺少更新方法")
            suggestions.append("添加update方法接收通知")

        if is_subject and not has_unsubscribe:
            suggestions.append("添加取消订阅方法以防止内存泄漏")

        signature_scores = self.signature_analyzer.analyze_class(class_node, py_file)
        match_score = signature_scores.get(PatternType.OBSERVER, 0.0)

        confidence = DetectionConfidence.HIGH if (has_notify or has_update) else DetectionConfidence.MEDIUM
        status = PatternStatus.CORRECT if not issues else PatternStatus.PARTIAL
        quality = self._determine_quality(len(issues), len(anti_pattern_warnings))

        return PatternInstance(
            pattern_type=PatternType.OBSERVER,
            category=PatternCategory.BEHAVIORAL,
            file_path=str(py_file),
            line_number=class_node.lineno,
            code_element=class_node.name,
            confidence=confidence,
            status=status,
            description=f"类 '{class_node.name}' 实现了观察者模式",
            issues=issues,
            suggestions=suggestions,
            quality=quality,
            match_score=match_score
        )

    def _determine_quality(self, issue_count: int, warning_count: int) -> PatternQuality:
        total = issue_count + warning_count
        if total == 0:
            return PatternQuality.EXCELLENT
        elif total == 1:
            return PatternQuality.GOOD
        elif total <= 3:
            return PatternQuality.ACCEPTABLE
        else:
            return PatternQuality.POOR


class StrategyDetector:
    """策略模式检测器 (深度优化版)"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.signature_analyzer = PatternSignatureAnalyzer(logger)

    def detect(self, py_file: Path, tree: ast.AST) -> List[PatternInstance]:
        instances = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                instance = self._check_strategy(py_file, node)
                if instance:
                    instances.append(instance)

        return instances

    def _check_strategy(self, py_file: Path, class_node: ast.ClassDef) -> Optional[PatternInstance]:
        strategy_keywords = ['Strategy', 'Policy', 'Algorithm', 'Rule']
        context_keywords = ['Context', 'Processor', 'Executor', 'Runner']

        is_strategy = any(kw in class_node.name for kw in strategy_keywords)
        is_context = any(kw in class_node.name for kw in context_keywords)

        if not is_strategy and not is_context:
            return None

        has_execute = False
        has_strategy_field = False
        has_strategy_setter = False
        strategy_type = ""

        for item in class_node.body:
            if isinstance(item, ast.FunctionDef):
                method_lower = item.name.lower()
                if any(kw in method_lower for kw in ['execute', 'run', 'apply', 'process', 'calculate', 'do']):
                    has_execute = True

                if 'set_strategy' in method_lower or 'set_policy' in method_lower:
                    has_strategy_setter = True

            if isinstance(item, ast.AnnAssign):
                if item.annotation:
                    ann_str = ""
                    if isinstance(item.annotation, ast.Name):
                        ann_str = item.annotation.id
                    elif isinstance(item.annotation, ast.Subscript):
                        if hasattr(ast, 'unparse'):
                            ann_str = ast.unparse(item.annotation)

                    if any(kw in ann_str for kw in ['Strategy', 'Policy', 'Algorithm']):
                        has_strategy_field = True
                        strategy_type = ann_str

        issues = []
        suggestions = []
        anti_pattern_warnings = []

        if is_strategy and not has_execute:
            issues.append("策略类缺少执行方法")
            suggestions.append("添加execute方法定义算法接口")

        if is_context and not has_strategy_field:
            issues.append("上下文类可能缺少策略引用")
            suggestions.append("添加策略字段并支持运行时切换")

        if is_context and not has_strategy_setter:
            suggestions.append("添加策略设置方法以支持运行时切换")

        if self._has_type_checking_in_context(class_node):
            anti_pattern_warnings.append("上下文类中使用类型检查可能是反模式")
            suggestions.append("使用策略对象的方法替代类型判断")

        signature_scores = self.signature_analyzer.analyze_class(class_node, py_file)
        match_score = signature_scores.get(PatternType.STRATEGY, 0.0)

        confidence = DetectionConfidence.MEDIUM
        status = PatternStatus.CORRECT if not issues else PatternStatus.PARTIAL
        quality = self._determine_quality(len(issues), len(anti_pattern_warnings))

        return PatternInstance(
            pattern_type=PatternType.STRATEGY,
            category=PatternCategory.BEHAVIORAL,
            file_path=str(py_file),
            line_number=class_node.lineno,
            code_element=class_node.name,
            confidence=confidence,
            status=status,
            description=f"类 '{class_node.name}' 实现了策略模式",
            issues=issues,
            suggestions=suggestions,
            quality=quality,
            match_score=match_score,
            anti_pattern_warnings=anti_pattern_warnings
        )

    def _has_type_checking_in_context(self, class_node: ast.ClassDef) -> bool:
        for item in class_node.body:
            if isinstance(item, ast.FunctionDef):
                for node in ast.walk(item):
                    if isinstance(node, ast.Call):
                        if isinstance(node.func, ast.Name) and node.func.id == 'isinstance':
                            return True
        return False

    def _determine_quality(self, issue_count: int, warning_count: int) -> PatternQuality:
        total = issue_count + warning_count
        if total == 0:
            return PatternQuality.EXCELLENT
        elif total == 1:
            return PatternQuality.GOOD
        elif total <= 3:
            return PatternQuality.ACCEPTABLE
        else:
            return PatternQuality.POOR


class RepositoryDetector:
    """仓储模式检测器 (深度优化版)"""

    CRUD_METHODS = {'get', 'find', 'save', 'delete', 'update', 'create', 'add', 'remove', 'list', 'query', 'exists', 'count'}

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.signature_analyzer = PatternSignatureAnalyzer(logger)

    def detect(self, py_file: Path, tree: ast.AST) -> List[PatternInstance]:
        instances = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                instance = self._check_repository(py_file, node)
                if instance:
                    instances.append(instance)

        return instances

    def _check_repository(self, py_file: Path, class_node: ast.ClassDef) -> Optional[PatternInstance]:
        if 'Repository' not in class_node.name:
            return None

        found_methods = set()
        method_details = {}
        has_business_logic = False

        for item in class_node.body:
            if isinstance(item, ast.FunctionDef):
                method_lower = item.name.lower()
                for crud in self.CRUD_METHODS:
                    if crud in method_lower:
                        found_methods.add(crud)
                        method_details[crud] = item.name

                if self._has_business_logic(item):
                    has_business_logic = True

        issues = []
        suggestions = []
        anti_pattern_warnings = []

        if len(found_methods) < 2:
            issues.append("仓储类缺少标准CRUD方法")
            suggestions.append("实现标准的增删改查操作")

        if has_business_logic:
            anti_pattern_warnings.append("仓储类包含业务逻辑可能是反模式")
            suggestions.append("将业务逻辑移至服务层或领域服务")

        is_abstract = self._check_is_abstract(class_node)

        signature_scores = self.signature_analyzer.analyze_class(class_node, py_file)
        match_score = signature_scores.get(PatternType.REPOSITORY, 0.0)

        confidence = DetectionConfidence.HIGH if len(found_methods) >= 2 else DetectionConfidence.MEDIUM
        status = PatternStatus.CORRECT if len(found_methods) >= 2 and not has_business_logic else PatternStatus.PARTIAL
        quality = self._determine_quality(len(issues), len(anti_pattern_warnings))

        return PatternInstance(
            pattern_type=PatternType.REPOSITORY,
            category=PatternCategory.STRUCTURAL,
            file_path=str(py_file),
            line_number=class_node.lineno,
            code_element=class_node.name,
            confidence=confidence,
            status=status,
            description=f"类 '{class_node.name}' 实现了仓储模式",
            issues=issues,
            suggestions=suggestions,
            quality=quality,
            match_score=match_score,
            anti_pattern_warnings=anti_pattern_warnings
        )

    def _has_business_logic(self, method: ast.FunctionDef) -> bool:
        business_keywords = ['calculate', 'validate', 'process', 'transform', 'compute']
        for node in ast.walk(method):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if any(kw in node.func.id.lower() for kw in business_keywords):
                        return True
        return False

    def _check_is_abstract(self, class_node: ast.ClassDef) -> bool:
        for base in class_node.bases:
            if isinstance(base, ast.Name) and base.id in ('ABC', 'ABCMeta'):
                return True
        return False

    def _determine_quality(self, issue_count: int, warning_count: int) -> PatternQuality:
        total = issue_count + warning_count
        if total == 0:
            return PatternQuality.EXCELLENT
        elif total == 1:
            return PatternQuality.GOOD
        elif total <= 3:
            return PatternQuality.ACCEPTABLE
        else:
            return PatternQuality.POOR


class DecoratorDetector:
    """装饰器模式检测器 (深度优化版)"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.signature_analyzer = PatternSignatureAnalyzer(logger)

    def detect(self, py_file: Path, tree: ast.AST) -> List[PatternInstance]:
        instances = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                instance = self._check_decorator(py_file, node, tree)
                if instance:
                    instances.append(instance)

        return instances

    def _check_decorator(self, py_file: Path, class_node: ast.ClassDef, tree: ast.AST) -> Optional[PatternInstance]:
        decorator_keywords = ['Decorator', 'Wrapper']

        is_decorator = any(kw in class_node.name for kw in decorator_keywords)

        has_same_interface = False
        has_wrapped_field = False
        has_delegation = False
        wrapped_type = ""

        for base in class_node.bases:
            if isinstance(base, ast.Name):
                has_same_interface = True

        for item in class_node.body:
            if isinstance(item, ast.AnnAssign):
                if item.target and isinstance(item.target, ast.Name):
                    if item.target.id in ('_wrapped', '_component', 'wrapped', 'component'):
                        has_wrapped_field = True
                        if item.annotation:
                            wrapped_type = self._get_annotation_str(item.annotation)

            if isinstance(item, ast.FunctionDef):
                if self._has_delegation_to_wrapped(item):
                    has_delegation = True

        if not is_decorator and not (has_same_interface and has_wrapped_field):
            return None

        issues = []
        suggestions = []
        anti_pattern_warnings = []

        if not has_wrapped_field:
            issues.append("装饰器类缺少被装饰对象的引用")
            suggestions.append("添加_wrapped或_component字段")

        if not has_delegation:
            suggestions.append("确保装饰器正确委托调用到被装饰对象")

        if not has_same_interface:
            issues.append("装饰器类应实现与被装饰对象相同的接口")
            suggestions.append("继承或实现相同的接口")

        signature_scores = self.signature_analyzer.analyze_class(class_node, py_file)
        match_score = signature_scores.get(PatternType.DECORATOR, 0.0)

        confidence = DetectionConfidence.MEDIUM
        status = PatternStatus.CORRECT if has_wrapped_field and has_delegation else PatternStatus.PARTIAL
        quality = self._determine_quality(len(issues), len(anti_pattern_warnings))

        return PatternInstance(
            pattern_type=PatternType.DECORATOR,
            category=PatternCategory.STRUCTURAL,
            file_path=str(py_file),
            line_number=class_node.lineno,
            code_element=class_node.name,
            confidence=confidence,
            status=status,
            description=f"类 '{class_node.name}' 实现了装饰器模式",
            issues=issues,
            suggestions=suggestions,
            quality=quality,
            match_score=match_score
        )

    def _has_delegation_to_wrapped(self, method: ast.FunctionDef) -> bool:
        for node in ast.walk(method):
            if isinstance(node, ast.Attribute):
                if node.attr in ('_wrapped', '_component', 'wrapped', 'component'):
                    return True
        return False

    def _get_annotation_str(self, annotation: ast.expr) -> str:
        if isinstance(annotation, ast.Name):
            return annotation.id
        elif hasattr(ast, 'unparse'):
            return ast.unparse(annotation)
        return ""

    def _determine_quality(self, issue_count: int, warning_count: int) -> PatternQuality:
        total = issue_count + warning_count
        if total == 0:
            return PatternQuality.EXCELLENT
        elif total == 1:
            return PatternQuality.GOOD
        elif total <= 3:
            return PatternQuality.ACCEPTABLE
        else:
            return PatternQuality.POOR


class AdapterDetector:
    """适配器模式检测器 (深度优化版)"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.signature_analyzer = PatternSignatureAnalyzer(logger)

    def detect(self, py_file: Path, tree: ast.AST) -> List[PatternInstance]:
        instances = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                instance = self._check_adapter(py_file, node)
                if instance:
                    instances.append(instance)

        return instances

    def _check_adapter(self, py_file: Path, class_node: ast.ClassDef) -> Optional[PatternInstance]:
        adapter_keywords = ['Adapter', 'Wrapper', 'Converter', 'Translator']

        is_adapter = any(kw in class_node.name for kw in adapter_keywords)

        if not is_adapter:
            return None

        has_adaptee = False
        has_target_interface = False
        adaptee_type = ""
        delegation_count = 0

        for base in class_node.bases:
            if isinstance(base, ast.Name):
                has_target_interface = True

        for item in class_node.body:
            if isinstance(item, ast.AnnAssign):
                if item.target and isinstance(item.target, ast.Name):
                    if item.target.id in ('_adaptee', 'adaptee', '_wrapped', 'wrapped', '_service', 'service'):
                        has_adaptee = True
                        if item.annotation:
                            adaptee_type = self._get_annotation_str(item.annotation)

            if isinstance(item, ast.FunctionDef):
                if self._has_adaptee_delegation(item):
                    delegation_count += 1

        issues = []
        suggestions = []
        anti_pattern_warnings = []

        if not has_adaptee:
            issues.append("适配器类缺少被适配对象的引用")
            suggestions.append("添加_adaptee字段存储被适配对象")

        if not has_target_interface:
            suggestions.append("实现目标接口以符合客户端期望")

        if delegation_count == 0:
            suggestions.append("添加委托方法调用被适配对象")

        signature_scores = self.signature_analyzer.analyze_class(class_node, py_file)
        match_score = signature_scores.get(PatternType.ADAPTER, 0.0)

        confidence = DetectionConfidence.MEDIUM
        status = PatternStatus.CORRECT if has_adaptee else PatternStatus.PARTIAL
        quality = self._determine_quality(len(issues), len(anti_pattern_warnings))

        return PatternInstance(
            pattern_type=PatternType.ADAPTER,
            category=PatternCategory.STRUCTURAL,
            file_path=str(py_file),
            line_number=class_node.lineno,
            code_element=class_node.name,
            confidence=confidence,
            status=status,
            description=f"类 '{class_node.name}' 实现了适配器模式",
            issues=issues,
            suggestions=suggestions,
            quality=quality,
            match_score=match_score
        )

    def _has_adaptee_delegation(self, method: ast.FunctionDef) -> bool:
        for node in ast.walk(method):
            if isinstance(node, ast.Attribute):
                if node.attr in ('_adaptee', 'adaptee', '_wrapped', 'wrapped'):
                    return True
        return False

    def _get_annotation_str(self, annotation: ast.expr) -> str:
        if isinstance(annotation, ast.Name):
            return annotation.id
        elif hasattr(ast, 'unparse'):
            return ast.unparse(annotation)
        return ""

    def _determine_quality(self, issue_count: int, warning_count: int) -> PatternQuality:
        total = issue_count + warning_count
        if total == 0:
            return PatternQuality.EXCELLENT
        elif total == 1:
            return PatternQuality.GOOD
        elif total <= 3:
            return PatternQuality.ACCEPTABLE
        else:
            return PatternQuality.POOR


class DependencyInjectionDetector:
    """依赖注入模式检测器 (深度优化版)"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.signature_analyzer = PatternSignatureAnalyzer(logger)

    def detect(self, py_file: Path, tree: ast.AST) -> List[PatternInstance]:
        instances = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                instance = self._check_di(py_file, node)
                if instance:
                    instances.append(instance)

        return instances

    def _check_di(self, py_file: Path, class_node: ast.ClassDef) -> Optional[PatternInstance]:
        service_indicators = ['Service', 'Manager', 'Handler', 'Controller', 'Processor', 'UseCase']

        is_service = any(kw in class_node.name for kw in service_indicators)

        if not is_service:
            return None

        has_constructor_di = False
        has_setter_di = False
        has_interface_di = False
        injected_deps = []
        concrete_deps = []

        for item in class_node.body:
            if isinstance(item, ast.FunctionDef) and item.name == '__init__':
                if len(item.args.args) > 1:
                    has_constructor_di = True
                    for arg in item.args.args[1:]:
                        injected_deps.append(arg.arg)
                        if arg.annotation:
                            ann_str = self._get_annotation_str(arg.annotation)
                            if self._is_interface_annotation(ann_str):
                                has_interface_di = True
                            elif self._is_concrete_annotation(ann_str):
                                concrete_deps.append(ann_str)

            if isinstance(item, ast.FunctionDef) and item.name.startswith('set_'):
                if len(item.args.args) > 1:
                    has_setter_di = True

        if not has_constructor_di and not has_setter_di:
            return None

        issues = []
        suggestions = []
        anti_pattern_warnings = []

        if not has_constructor_di:
            issues.append("建议使用构造函数注入而非setter注入")
            suggestions.append("通过构造函数注入依赖，提高不可变性")

        if not has_interface_di:
            suggestions.append("依赖抽象接口而非具体实现")

        if concrete_deps:
            anti_pattern_warnings.append(f"直接依赖具体实现: {concrete_deps}")
            suggestions.append("使用接口或抽象类替代具体实现")

        signature_scores = self.signature_analyzer.analyze_class(class_node, py_file)
        match_score = signature_scores.get(PatternType.DEPENDENCY_INJECTION, 0.0)

        confidence = DetectionConfidence.HIGH if has_constructor_di else DetectionConfidence.MEDIUM
        status = PatternStatus.CORRECT if has_constructor_di and has_interface_di else PatternStatus.PARTIAL
        quality = self._determine_quality(len(issues), len(anti_pattern_warnings))

        return PatternInstance(
            pattern_type=PatternType.DEPENDENCY_INJECTION,
            category=PatternCategory.ARCHITECTURAL,
            file_path=str(py_file),
            line_number=class_node.lineno,
            code_element=class_node.name,
            confidence=confidence,
            status=status,
            description=f"类 '{class_node.name}' 使用了依赖注入模式",
            issues=issues,
            suggestions=suggestions,
            quality=quality,
            match_score=match_score,
            anti_pattern_warnings=anti_pattern_warnings
        )

    def _get_annotation_str(self, annotation: ast.expr) -> str:
        if isinstance(annotation, ast.Name):
            return annotation.id
        elif isinstance(annotation, ast.Attribute):
            if isinstance(annotation.value, ast.Name):
                return f"{annotation.value.id}.{annotation.attr}"
        elif hasattr(ast, 'unparse'):
            return ast.unparse(annotation)
        return ""

    def _is_interface_annotation(self, annotation: str) -> bool:
        interface_indicators = ['Interface', 'Abstract', 'Base', 'I', 'Protocol']
        return any(ind in annotation for ind in interface_indicators)

    def _is_concrete_annotation(self, annotation: str) -> bool:
        concrete_indicators = ['Impl', 'Concrete', 'Service', 'Repository']
        return any(ind in annotation for ind in concrete_indicators)

    def _determine_quality(self, issue_count: int, warning_count: int) -> PatternQuality:
        total = issue_count + warning_count
        if total == 0:
            return PatternQuality.EXCELLENT
        elif total == 1:
            return PatternQuality.GOOD
        elif total <= 3:
            return PatternQuality.ACCEPTABLE
        else:
            return PatternQuality.POOR


class CommandDetector:
    """命令模式检测器"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.signature_analyzer = PatternSignatureAnalyzer(logger)

    def detect(self, py_file: Path, tree: ast.AST) -> List[PatternInstance]:
        instances = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                instance = self._check_command(py_file, node)
                if instance:
                    instances.append(instance)

        return instances

    def _check_command(self, py_file: Path, class_node: ast.ClassDef) -> Optional[PatternInstance]:
        command_keywords = ['Command', 'Action', 'Operation', 'Task']

        is_command = any(kw in class_node.name for kw in command_keywords)

        has_execute = False
        has_undo = False
        has_receiver = False

        for item in class_node.body:
            if isinstance(item, ast.FunctionDef):
                if item.name.lower() in ('execute', 'run', 'do', 'perform'):
                    has_execute = True
                if item.name.lower() in ('undo', 'rollback', 'reverse'):
                    has_undo = True

            if isinstance(item, ast.AnnAssign):
                if item.target and isinstance(item.target, ast.Name):
                    if item.target.id in ('_receiver', 'receiver'):
                        has_receiver = True

        if not is_command and not has_execute:
            return None

        issues = []
        suggestions = []

        if not has_execute:
            issues.append("命令类缺少execute方法")

        if not has_undo:
            suggestions.append("考虑添加undo方法支持操作撤销")

        signature_scores = self.signature_analyzer.analyze_class(class_node, py_file)
        match_score = signature_scores.get(PatternType.COMMAND, 0.0)

        confidence = DetectionConfidence.MEDIUM
        status = PatternStatus.CORRECT if has_execute else PatternStatus.PARTIAL

        return PatternInstance(
            pattern_type=PatternType.COMMAND,
            category=PatternCategory.BEHAVIORAL,
            file_path=str(py_file),
            line_number=class_node.lineno,
            code_element=class_node.name,
            confidence=confidence,
            status=status,
            description=f"类 '{class_node.name}' 实现了命令模式",
            issues=issues,
            suggestions=suggestions,
            match_score=match_score
        )


class TemplateMethodDetector:
    """模板方法模式检测器"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.signature_analyzer = PatternSignatureAnalyzer(logger)

    def detect(self, py_file: Path, tree: ast.AST) -> List[PatternInstance]:
        instances = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                instance = self._check_template_method(py_file, node)
                if instance:
                    instances.append(instance)

        return instances

    def _check_template_method(self, py_file: Path, class_node: ast.ClassDef) -> Optional[PatternInstance]:
        is_abstract = False
        template_methods = []
        hook_methods = []
        primitive_methods = []

        for base in class_node.bases:
            if isinstance(base, ast.Name) and base.id in ('ABC', 'ABCMeta'):
                is_abstract = True

        for item in class_node.body:
            if isinstance(item, ast.FunctionDef):
                has_abstract_decorator = any(
                    (isinstance(d, ast.Name) and d.id == 'abstractmethod')
                    for d in item.decorator_list
                )

                if has_abstract_decorator:
                    primitive_methods.append(item.name)
                elif item.name.startswith('_') and not item.name.startswith('__'):
                    if 'hook' in item.name.lower():
                        hook_methods.append(item.name)
                    else:
                        primitive_methods.append(item.name)
                else:
                    calls_primitives = self._calls_other_methods(item, class_node)
                    if calls_primitives:
                        template_methods.append(item.name)

        if not template_methods or not primitive_methods:
            return None

        issues = []
        suggestions = []

        if not is_abstract:
            suggestions.append("考虑将模板方法类声明为抽象类")

        signature_scores = self.signature_analyzer.analyze_class(class_node, py_file)
        match_score = signature_scores.get(PatternType.TEMPLATE_METHOD, 0.0)

        confidence = DetectionConfidence.MEDIUM
        status = PatternStatus.CORRECT

        return PatternInstance(
            pattern_type=PatternType.TEMPLATE_METHOD,
            category=PatternCategory.BEHAVIORAL,
            file_path=str(py_file),
            line_number=class_node.lineno,
            code_element=class_node.name,
            confidence=confidence,
            status=status,
            description=f"类 '{class_node.name}' 实现了模板方法模式",
            issues=issues,
            suggestions=suggestions,
            match_score=match_score,
            details={
                "template_methods": template_methods,
                "primitive_methods": primitive_methods,
                "hook_methods": hook_methods
            }
        )

    def _calls_other_methods(self, method: ast.FunctionDef, class_node: ast.ClassDef) -> bool:
        class_methods = {
            item.name for item in class_node.body
            if isinstance(item, ast.FunctionDef)
        }

        for node in ast.walk(method):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    if isinstance(node.func.value, ast.Name) and node.func.value.id == 'self':
                        if node.func.attr in class_methods and node.func.attr != method.name:
                            return True
        return False


class StateDetector:
    """状态模式检测器"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.signature_analyzer = PatternSignatureAnalyzer(logger)

    def detect(self, py_file: Path, tree: ast.AST) -> List[PatternInstance]:
        instances = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                instance = self._check_state(py_file, node)
                if instance:
                    instances.append(instance)

        return instances

    def _check_state(self, py_file: Path, class_node: ast.ClassDef) -> Optional[PatternInstance]:
        state_keywords = ['State', 'Context']

        is_state = any(kw in class_node.name for kw in state_keywords)

        if not is_state:
            return None

        has_state_field = False
        has_state_change = False
        has_handle = False

        for item in class_node.body:
            if isinstance(item, ast.AnnAssign):
                if item.target and isinstance(item.target, ast.Name):
                    if 'state' in item.target.id.lower():
                        has_state_field = True

            if isinstance(item, ast.FunctionDef):
                if 'handle' in item.name.lower() or 'process' in item.name.lower():
                    has_handle = True

                for node in ast.walk(item):
                    if isinstance(node, ast.Assign):
                        for target in node.targets:
                            if isinstance(target, ast.Attribute):
                                if 'state' in target.attr.lower():
                                    has_state_change = True

        if not has_state_field and not has_state_change:
            return None

        issues = []
        suggestions = []

        if self._has_state_conditionals(class_node):
            suggestions.append("避免使用条件判断切换状态，使用多态替代")

        signature_scores = self.signature_analyzer.analyze_class(class_node, py_file)
        match_score = signature_scores.get(PatternType.STATE, 0.0)

        confidence = DetectionConfidence.MEDIUM
        status = PatternStatus.CORRECT

        return PatternInstance(
            pattern_type=PatternType.STATE,
            category=PatternCategory.BEHAVIORAL,
            file_path=str(py_file),
            line_number=class_node.lineno,
            code_element=class_node.name,
            confidence=confidence,
            status=status,
            description=f"类 '{class_node.name}' 实现了状态模式",
            issues=issues,
            suggestions=suggestions,
            match_score=match_score
        )

    def _has_state_conditionals(self, class_node: ast.ClassDef) -> bool:
        for item in class_node.body:
            if isinstance(item, ast.FunctionDef):
                for node in ast.walk(item):
                    if isinstance(node, ast.Compare):
                        for comp in node.comparators:
                            if isinstance(comp, ast.Attribute):
                                if 'state' in comp.attr.lower():
                                    return True
        return False


class ChainOfResponsibilityDetector:
    """责任链模式检测器"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.signature_analyzer = PatternSignatureAnalyzer(logger)

    def detect(self, py_file: Path, tree: ast.AST) -> List[PatternInstance]:
        instances = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                instance = self._check_chain(py_file, node)
                if instance:
                    instances.append(instance)

        return instances

    def _check_chain(self, py_file: Path, class_node: ast.ClassDef) -> Optional[PatternInstance]:
        chain_keywords = ['Handler', 'Chain', 'Middleware', 'Interceptor']

        is_handler = any(kw in class_node.name for kw in chain_keywords)

        has_successor = False
        has_handle = False
        has_pass_to_next = False

        for item in class_node.body:
            if isinstance(item, ast.AnnAssign):
                if item.target and isinstance(item.target, ast.Name):
                    if item.target.id in ('_successor', 'successor', '_next', 'next_handler'):
                        has_successor = True

            if isinstance(item, ast.FunctionDef):
                if 'handle' in item.name.lower():
                    has_handle = True

                    for node in ast.walk(item):
                        if isinstance(node, ast.Call):
                            if isinstance(node.func, ast.Attribute):
                                if node.func.attr in ('handle', 'pass_to_next'):
                                    has_pass_to_next = True

        if not is_handler and not (has_successor and has_handle):
            return None

        issues = []
        suggestions = []

        if not has_successor:
            issues.append("处理器缺少后继者引用")

        if not has_pass_to_next:
            suggestions.append("确保在适当条件下将请求传递给下一个处理器")

        signature_scores = self.signature_analyzer.analyze_class(class_node, py_file)
        match_score = signature_scores.get(PatternType.CHAIN_OF_RESPONSIBILITY, 0.0)

        confidence = DetectionConfidence.MEDIUM
        status = PatternStatus.CORRECT if has_successor and has_handle else PatternStatus.PARTIAL

        return PatternInstance(
            pattern_type=PatternType.CHAIN_OF_RESPONSIBILITY,
            category=PatternCategory.BEHAVIORAL,
            file_path=str(py_file),
            line_number=class_node.lineno,
            code_element=class_node.name,
            confidence=confidence,
            status=status,
            description=f"类 '{class_node.name}' 实现了责任链模式",
            issues=issues,
            suggestions=suggestions,
            match_score=match_score
        )


class PatternRecommender:
    """模式推荐器 (深度优化版)"""

    RECOMMENDATION_RULES = [
        {
            "condition": lambda c: c.get('type_checks', 0) > 3,
            "pattern": PatternType.STRATEGY,
            "reason": "存在多个类型判断条件，策略模式可以消除条件分支",
            "benefits": ["消除条件分支", "易于扩展新策略", "符合开闭原则"],
            "hints": ["定义策略接口", "为每种情况实现具体策略", "上下文持有策略引用"],
            "priority": "high"
        },
        {
            "condition": lambda c: c.get('class_instantiations', 0) > 5,
            "pattern": PatternType.FACTORY,
            "reason": "存在大量类实例化代码，工厂模式可以封装创建逻辑",
            "benefits": ["封装创建逻辑", "降低耦合", "便于切换实现"],
            "hints": ["创建工厂类", "定义创建方法", "客户端通过工厂创建对象"],
            "priority": "medium"
        },
        {
            "condition": lambda c: c.get('complex_constructor_args', 0) > 3,
            "pattern": PatternType.BUILDER,
            "reason": "构造函数参数过多，建造者模式可以简化对象构建",
            "benefits": ["分步构建对象", "链式调用", "参数可选"],
            "hints": ["创建Builder类", "实现链式设置方法", "添加build方法"],
            "priority": "high"
        },
        {
            "condition": lambda c: c.get('event_handlers', 0) > 2,
            "pattern": PatternType.OBSERVER,
            "reason": "存在事件处理逻辑，观察者模式可以实现松耦合的事件通知",
            "benefits": ["松耦合", "动态订阅", "广播通知"],
            "hints": ["定义Subject和Observer接口", "Subject维护观察者列表", "Observer实现更新方法"],
            "priority": "medium"
        },
        {
            "condition": lambda c: c.get('global_state_access', 0) > 3,
            "pattern": PatternType.SINGLETON,
            "reason": "存在全局状态访问，单例模式可以统一管理",
            "benefits": ["全局唯一实例", "延迟初始化", "受控访问"],
            "hints": ["私有化构造函数", "添加类变量存储实例", "提供获取实例方法"],
            "priority": "low"
        },
        {
            "condition": lambda c: c.get('incompatible_interfaces', 0) > 0,
            "pattern": PatternType.ADAPTER,
            "reason": "存在不兼容接口调用，适配器模式可以统一接口",
            "benefits": ["接口兼容", "复用现有类", "解耦客户端"],
            "hints": ["创建适配器类", "实现目标接口", "持有被适配对象"],
            "priority": "medium"
        },
        {
            "condition": lambda c: c.get('state_conditionals', 0) > 2,
            "pattern": PatternType.STATE,
            "reason": "存在大量状态条件判断，状态模式可以简化状态转换",
            "benefits": ["消除状态条件", "状态转换清晰", "易于添加新状态"],
            "hints": ["定义状态接口", "为每个状态实现类", "上下文委托状态处理"],
            "priority": "high"
        },
        {
            "condition": lambda c: c.get('algorithm_variations', 0) > 0,
            "pattern": PatternType.TEMPLATE_METHOD,
            "reason": "存在算法骨架变化，模板方法可以固定骨架、延迟实现",
            "benefits": ["代码复用", "控制扩展点", "符合好莱坞原则"],
            "hints": ["定义抽象类", "实现模板方法", "定义抽象原语操作"],
            "priority": "medium"
        },
        {
            "condition": lambda c: c.get('operation_undo', 0) > 0,
            "pattern": PatternType.COMMAND,
            "reason": "存在需要撤销的操作，命令模式可以封装操作支持撤销",
            "benefits": ["操作封装", "支持撤销", "支持队列"],
            "hints": ["定义命令接口", "实现execute和undo", "调用者持有命令"],
            "priority": "medium"
        },
        {
            "condition": lambda c: c.get('nested_conditionals', 0) > 2,
            "pattern": PatternType.CHAIN_OF_RESPONSIBILITY,
            "reason": "存在嵌套条件判断，责任链模式可以解耦处理逻辑",
            "benefits": ["解耦发送者和处理者", "动态组合处理链", "单一职责"],
            "hints": ["定义处理器接口", "每个处理器处理一类请求", "链接处理器"],
            "priority": "high"
        }
    ]

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def analyze_and_recommend(self, py_file: Path, tree: ast.AST) -> List[PatternRecommendation]:
        context = self._analyze_context(tree)
        recommendations = []

        for rule in self.RECOMMENDATION_RULES:
            if rule["condition"](context):
                category = self._get_category(rule["pattern"])
                recommendations.append(PatternRecommendation(
                    pattern_type=rule["pattern"],
                    category=category,
                    context=str(py_file),
                    reason=rule["reason"],
                    benefits=rule["benefits"],
                    implementation_hints=rule["hints"],
                    priority=rule.get("priority", "medium"),
                    related_code_elements=context.get("related_elements", [])
                ))

        return recommendations

    def _analyze_context(self, tree: ast.AST) -> Dict[str, Any]:
        context = {
            'type_checks': 0,
            'class_instantiations': 0,
            'complex_constructor_args': 0,
            'event_handlers': 0,
            'global_state_access': 0,
            'incompatible_interfaces': 0,
            'state_conditionals': 0,
            'algorithm_variations': 0,
            'operation_undo': 0,
            'nested_conditionals': 0,
            'related_elements': []
        }

        for node in ast.walk(tree):
            if isinstance(node, ast.If):
                if self._is_type_check(node):
                    context['type_checks'] += 1
                if self._is_state_check(node):
                    context['state_conditionals'] += 1
                if self._count_nesting(node) > 2:
                    context['nested_conditionals'] += 1

            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id[0].isupper():
                    context['class_instantiations'] += 1
                    context['related_elements'].append(node.func.id)

            if isinstance(node, ast.FunctionDef) and node.name == '__init__':
                if len(node.args.args) > 4:
                    context['complex_constructor_args'] += 1

            if isinstance(node, ast.FunctionDef):
                if any(kw in node.name.lower() for kw in ['on_', 'handle', 'callback']):
                    context['event_handlers'] += 1
                if 'undo' in node.name.lower() or 'rollback' in node.name.lower():
                    context['operation_undo'] += 1

            if isinstance(node, ast.Global):
                context['global_state_access'] += len(node.names)

        return context

    def _is_type_check(self, if_node: ast.If) -> bool:
        for node in ast.walk(if_node.test):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == 'isinstance':
                    return True
            if isinstance(node, ast.Attribute):
                if node.attr in ('type', 'kind', 'category'):
                    return True
        return False

    def _is_state_check(self, if_node: ast.If) -> bool:
        for node in ast.walk(if_node.test):
            if isinstance(node, ast.Attribute):
                if 'state' in node.attr.lower() or 'status' in node.attr.lower():
                    return True
        return False

    def _count_nesting(self, node: ast.AST, depth: int = 0) -> int:
        max_depth = depth
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.If):
                max_depth = max(max_depth, self._count_nesting(child, depth + 1))
            else:
                max_depth = max(max_depth, self._count_nesting(child, depth))
        return max_depth

    def _get_category(self, pattern: PatternType) -> PatternCategory:
        creational = {PatternType.SINGLETON, PatternType.FACTORY, PatternType.ABSTRACT_FACTORY,
                     PatternType.BUILDER, PatternType.PROTOTYPE}
        structural = {PatternType.ADAPTER, PatternType.BRIDGE, PatternType.COMPOSITE,
                     PatternType.DECORATOR, PatternType.FACADE, PatternType.FLYWEIGHT,
                     PatternType.PROXY, PatternType.REPOSITORY, PatternType.DEPENDENCY_INJECTION}
        behavioral = {PatternType.CHAIN_OF_RESPONSIBILITY, PatternType.COMMAND, PatternType.INTERPRETER,
                     PatternType.ITERATOR, PatternType.MEDIATOR, PatternType.MEMENTO,
                     PatternType.OBSERVER, PatternType.STATE, PatternType.STRATEGY,
                     PatternType.TEMPLATE_METHOD, PatternType.VISITOR}

        if pattern in creational:
            return PatternCategory.CREATIONAL
        elif pattern in structural:
            return PatternCategory.STRUCTURAL
        elif pattern in behavioral:
            return PatternCategory.BEHAVIORAL
        else:
            return PatternCategory.ARCHITECTURAL


class AntiPatternAnalyzer:
    """反模式分析器"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def analyze(self, instances: List[PatternInstance]) -> Dict[str, Any]:
        anti_patterns = []
        warnings = []

        for instance in instances:
            if instance.anti_pattern_warnings:
                anti_patterns.append({
                    "pattern": instance.pattern_type.value,
                    "element": instance.code_element,
                    "warnings": instance.anti_pattern_warnings,
                    "file": instance.file_path
                })

            if instance.status == PatternStatus.INCORRECT:
                warnings.append({
                    "pattern": instance.pattern_type.value,
                    "element": instance.code_element,
                    "issues": instance.issues
                })

        return {
            "anti_pattern_count": len(anti_patterns),
            "anti_patterns": anti_patterns,
            "incorrect_implementations": warnings,
            "summary": self._generate_summary(anti_patterns, warnings)
        }

    def _generate_summary(self, anti_patterns: List, warnings: List) -> str:
        if not anti_patterns and not warnings:
            return "未检测到明显的反模式"

        summary_parts = []
        if anti_patterns:
            summary_parts.append(f"检测到 {len(anti_patterns)} 个潜在反模式")
        if warnings:
            summary_parts.append(f"{len(warnings)} 个模式实现存在问题")

        return "，".join(summary_parts)


class DesignPatternChecker:
    """设计模式检查器主类 (深度优化版)"""

    def __init__(
        self,
        project_path: Optional[Path] = None,
        logger: Optional[logging.Logger] = None
    ):
        self.project_path = project_path or Path.cwd()
        self.logger = logger or self._setup_logger()

        self.detectors = {
            PatternType.SINGLETON: SingletonDetector(self.logger),
            PatternType.FACTORY: FactoryDetector(self.logger),
            PatternType.BUILDER: BuilderDetector(self.logger),
            PatternType.OBSERVER: ObserverDetector(self.logger),
            PatternType.STRATEGY: StrategyDetector(self.logger),
            PatternType.REPOSITORY: RepositoryDetector(self.logger),
            PatternType.DECORATOR: DecoratorDetector(self.logger),
            PatternType.ADAPTER: AdapterDetector(self.logger),
            PatternType.DEPENDENCY_INJECTION: DependencyInjectionDetector(self.logger),
            PatternType.COMMAND: CommandDetector(self.logger),
            PatternType.TEMPLATE_METHOD: TemplateMethodDetector(self.logger),
            PatternType.STATE: StateDetector(self.logger),
            PatternType.CHAIN_OF_RESPONSIBILITY: ChainOfResponsibilityDetector(self.logger),
        }

        self.recommender = PatternRecommender(self.logger)
        self.anti_pattern_analyzer = AntiPatternAnalyzer(self.logger)

        self._checked_files: int = 0

    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger("DesignPatternChecker")
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

    def analyze(self, target_path: Optional[Path] = None) -> DesignPatternReport:
        self.logger.info("开始设计模式深度检查...")

        target = target_path or self.project_path
        py_files = list(target.rglob("*.py")) if target.is_dir() else [target]

        pattern_instances: Dict[PatternType, List[PatternInstance]] = {
            pt: [] for pt in self.detectors.keys()
        }
        all_recommendations: List[PatternRecommendation] = []

        for py_file in py_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    source = f.read()
                tree = ast.parse(source)

                for pattern_type, detector in self.detectors.items():
                    instances = detector.detect(py_file, tree)
                    pattern_instances[pattern_type].extend(instances)

                recommendations = self.recommender.analyze_and_recommend(py_file, tree)
                all_recommendations.extend(recommendations)

                self._checked_files += 1

            except Exception as e:
                self.logger.warning(f"分析文件失败 {py_file}: {e}")

        pattern_reports = self._build_pattern_reports(pattern_instances)
        total_detected = sum(len(instances) for instances in pattern_instances.values())

        all_instances = [
            inst for instances in pattern_instances.values() for inst in instances
        ]
        anti_pattern_analysis = self.anti_pattern_analyzer.analyze(all_instances)

        pattern_relationships = self._analyze_pattern_relationships(pattern_instances)

        summary = self._build_summary(pattern_reports, all_recommendations, anti_pattern_analysis)

        return DesignPatternReport(
            timestamp=datetime.now().isoformat(),
            project_path=str(target),
            total_patterns_detected=total_detected,
            pattern_reports=pattern_reports,
            recommendations=all_recommendations,
            pattern_relationships=pattern_relationships,
            anti_pattern_analysis=anti_pattern_analysis,
            summary=summary
        )

    def _build_pattern_reports(
        self,
        instances: Dict[PatternType, List[PatternInstance]]
    ) -> Dict[str, PatternReport]:
        reports = {}

        for pattern_type, pattern_instances in instances.items():
            if not pattern_instances:
                continue

            correct_count = sum(1 for i in pattern_instances if i.status == PatternStatus.CORRECT)
            incorrect_count = sum(1 for i in pattern_instances if i.status == PatternStatus.INCORRECT)
            partial_count = sum(1 for i in pattern_instances if i.status == PatternStatus.PARTIAL)
            anti_pattern_count = sum(1 for i in pattern_instances if i.anti_pattern_warnings)

            quality_scores = {
                PatternQuality.EXCELLENT: 4,
                PatternQuality.GOOD: 3,
                PatternQuality.ACCEPTABLE: 2,
                PatternQuality.POOR: 1
            }
            avg_quality = sum(quality_scores.get(i.quality, 2) for i in pattern_instances) / len(pattern_instances)

            category = self._get_pattern_category(pattern_type)

            reports[pattern_type.name] = PatternReport(
                pattern_type=pattern_type,
                category=category,
                instances=pattern_instances,
                correct_count=correct_count,
                incorrect_count=incorrect_count,
                partial_count=partial_count,
                anti_pattern_count=anti_pattern_count,
                average_quality=avg_quality
            )

        return reports

    def _get_pattern_category(self, pattern_type: PatternType) -> PatternCategory:
        creational = {PatternType.SINGLETON, PatternType.FACTORY, PatternType.ABSTRACT_FACTORY,
                     PatternType.BUILDER, PatternType.PROTOTYPE}
        structural = {PatternType.ADAPTER, PatternType.BRIDGE, PatternType.COMPOSITE,
                     PatternType.DECORATOR, PatternType.FACADE, PatternType.FLYWEIGHT,
                     PatternType.PROXY, PatternType.REPOSITORY, PatternType.DEPENDENCY_INJECTION}
        behavioral = {PatternType.CHAIN_OF_RESPONSIBILITY, PatternType.COMMAND, PatternType.INTERPRETER,
                     PatternType.ITERATOR, PatternType.MEDIATOR, PatternType.MEMENTO,
                     PatternType.OBSERVER, PatternType.STATE, PatternType.STRATEGY,
                     PatternType.TEMPLATE_METHOD, PatternType.VISITOR}

        if pattern_type in creational:
            return PatternCategory.CREATIONAL
        elif pattern_type in structural:
            return PatternCategory.STRUCTURAL
        elif pattern_type in behavioral:
            return PatternCategory.BEHAVIORAL
        else:
            return PatternCategory.ARCHITECTURAL

    def _analyze_pattern_relationships(self, instances: Dict[PatternType, List[PatternInstance]]) -> List[PatternRelationship]:
        relationships = []

        relationships.append(PatternRelationship(
            source_pattern=PatternType.FACTORY,
            target_pattern=PatternType.ABSTRACT_FACTORY,
            relationship_type="specialization",
            description="抽象工厂是工厂模式的扩展，用于创建产品族"
        ))

        relationships.append(PatternRelationship(
            source_pattern=PatternType.BUILDER,
            target_pattern=PatternType.FACTORY,
            relationship_type="alternative",
            description="建造者模式和工厂模式都用于对象创建，但建造者关注分步构建"
        ))

        relationships.append(PatternRelationship(
            source_pattern=PatternType.STRATEGY,
            target_pattern=PatternType.STATE,
            relationship_type="similar",
            description="策略和状态模式结构相似，但意图不同：策略用于算法切换，状态用于状态转换"
        ))

        relationships.append(PatternRelationship(
            source_pattern=PatternType.DECORATOR,
            target_pattern=PatternType.ADAPTER,
            relationship_type="similar",
            description="装饰器和适配器都使用包装，但装饰器添加行为，适配器转换接口"
        ))

        return relationships

    def _build_summary(
        self,
        reports: Dict[str, PatternReport],
        recommendations: List[PatternRecommendation],
        anti_pattern_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        category_counts = defaultdict(int)
        for report in reports.values():
            category_counts[report.category.value] += len(report.instances)

        status_counts = defaultdict(int)
        quality_avg = 0.0
        total_instances = 0

        for report in reports.values():
            status_counts['correct'] += report.correct_count
            status_counts['partial'] += report.partial_count
            status_counts['incorrect'] += report.incorrect_count
            quality_avg += report.average_quality * len(report.instances)
            total_instances += len(report.instances)

        if total_instances > 0:
            quality_avg /= total_instances

        return {
            "total_files_checked": self._checked_files,
            "patterns_by_category": dict(category_counts),
            "implementation_status": dict(status_counts),
            "average_quality_score": quality_avg,
            "recommendation_count": len(recommendations),
            "anti_pattern_count": anti_pattern_analysis.get("anti_pattern_count", 0),
            "most_common_patterns": self._get_most_common_patterns(reports),
            "quality_distribution": self._get_quality_distribution(reports)
        }

    def _get_most_common_patterns(self, reports: Dict[str, PatternReport]) -> List[str]:
        sorted_patterns = sorted(
            reports.items(),
            key=lambda x: len(x[1].instances),
            reverse=True
        )
        return [p[0] for p in sorted_patterns[:5]]

    def _get_quality_distribution(self, reports: Dict[str, PatternReport]) -> Dict[str, int]:
        distribution = defaultdict(int)
        for report in reports.values():
            for instance in report.instances:
                distribution[instance.quality.value] += 1
        return dict(distribution)

    def print_report(self, report: DesignPatternReport) -> None:
        print("\n" + "=" * 80)
        print("设计模式检查报告 (深度优化版)")
        print("=" * 80)
        print(f"项目路径: {report.project_path}")
        print(f"检查时间: {report.timestamp}")
        print(f"检测到的模式实例: {report.total_patterns_detected}")

        print("\n" + "-" * 80)
        print("检测到的设计模式")
        print("-" * 80)

        for pattern_name, pattern_report in report.pattern_reports.items():
            status_icon = "✅" if pattern_report.correct_count > 0 else "⚠️"
            quality_icon = {
                PatternQuality.EXCELLENT: "⭐",
                PatternQuality.GOOD: "👍",
                PatternQuality.ACCEPTABLE: "👌",
                PatternQuality.POOR: "⚠️"
            }.get(PatternQuality.GOOD, "⚪")

            print(f"\n{status_icon} {pattern_name} ({pattern_report.category.value})")
            print(f"   实例数: {len(pattern_report.instances)}")
            print(f"   正确实现: {pattern_report.correct_count}, 部分实现: {pattern_report.partial_count}")
            print(f"   平均质量: {pattern_report.average_quality:.2f}/4.0")

            for instance in pattern_report.instances[:3]:
                print(f"   - {instance.file_path}:{instance.line_number} - {instance.code_element}")
                if instance.issues:
                    print(f"     问题: {', '.join(instance.issues[:2])}")
                if instance.anti_pattern_warnings:
                    print(f"     ⚠️ 反模式警告: {', '.join(instance.anti_pattern_warnings[:2])}")

        if report.anti_pattern_analysis.get("anti_patterns"):
            print("\n" + "-" * 80)
            print("反模式分析")
            print("-" * 80)

            for ap in report.anti_pattern_analysis["anti_patterns"][:5]:
                print(f"  ⚠️ {ap['pattern']} - {ap['element']}")
                print(f"     {', '.join(ap['warnings'][:2])}")

        if report.recommendations:
            print("\n" + "-" * 80)
            print("模式推荐")
            print("-" * 80)

            for rec in report.recommendations[:5]:
                priority_icon = {"high": "🔴", "medium": "🟡", "low": "🔵"}.get(rec.priority, "⚪")
                print(f"\n{priority_icon} {rec.pattern_type.value} ({rec.category.value})")
                print(f"   原因: {rec.reason}")
                print(f"   好处: {', '.join(rec.benefits[:3])}")

    def save_report(self, report: DesignPatternReport, output_path: str) -> None:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)

        self.logger.info(f"报告已保存: {path}")


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="设计模式检查器 (深度优化版)",
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
        "--patterns",
        type=str,
        help="要检查的模式，逗号分隔 (如: singleton,factory,observer)"
    )
    parser.add_argument(
        "--recommend",
        action="store_true",
        help="显示模式推荐"
    )
    parser.add_argument(
        "--deep-analysis",
        action="store_true",
        default=True,
        help="启用深度分析 (默认: 启用)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="启用详细日志输出"
    )

    args = parser.parse_args()

    logger = logging.getLogger("DesignPatternChecker")
    logger.setLevel(logging.DEBUG if args.verbose else logging.INFO)

    checker = DesignPatternChecker(
        project_path=Path(args.path),
        logger=logger
    )

    report = checker.analyze()

    if args.output == "console":
        checker.print_report(report)
    else:
        print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))

    if args.output_file:
        checker.save_report(report, args.output_file)

    return 0


if __name__ == "__main__":
    sys.exit(main())
