#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能代码异味检测器

TDD蓝阶段 - 刑部重构分析器增强版
支持智能代码异味检测，包括：
- 深度嵌套检测
- 长函数检测
- 重复代码检测
- 高耦合检测
- 低内聚检测
- 代码复杂度分析
- 设计模式违规检测

使用示例:
    python intelligent_code_smell_detector.py
    python intelligent_code_smell_detector.py --output json
    python intelligent_code_smell_detector.py --severity high
"""

import os
import sys
import ast
import re
import json
import hashlib
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict


class SmellCategory(Enum):
    """代码异味类别"""
    BLOATERS = "bloaters"
    OBJECT_ORIENTED_ABUSERS = "oo_abusers"
    CHANGE_PREVENTERS = "change_preventers"
    DISPENSABLES = "dispensables"
    COUPLERS = "couplers"
    COMPLEXITY = "complexity"


class SmellType(Enum):
    """代码异味类型"""
    LONG_METHOD = "long_method"
    LARGE_CLASS = "large_class"
    PRIMITIVE_OBSESSION = "primitive_obsession"
    LONG_PARAMETER_LIST = "long_parameter_list"
    DATA_CLUMPS = "data_clumps"
    SWITCH_STATEMENTS = "switch_statements"
    TEMPORARY_FIELD = "temporary_field"
    REFUSED_BEQUEST = "refused_bequest"
    ALTERNATIVE_CLASSES = "alternative_classes"
    PARALLEL_INHERITANCE = "parallel_inheritance"
    DUPLICATE_CODE = "duplicate_code"
    DEAD_CODE = "dead_code"
    SPECULATIVE_GENERALITY = "speculative_generality"
    LAZY_CLASS = "lazy_class"
    FEATURE_ENVY = "feature_envy"
    INAPPROPRIATE_INTIMACY = "inappropriate_intimacy"
    MESSAGE_CHAINS = "message_chains"
    MIDDLE_MAN = "middle_man"
    DEEP_NESTING = "deep_nesting"
    HIGH_COMPLEXITY = "high_complexity"
    GOD_CLASS = "god_class"
    SHOTGUN_SURGERY = "shotgun_surgery"
    DIVERGENT_CHANGE = "divergent_change"
    PRIMITIVE_WRAPPER = "primitive_wrapper"
    COMMENTS_SMELL = "comments_smell"
    NAMING_SMELL = "naming_smell"
    COUPLING_SMELL = "coupling_smell"
    COHESION_SMELL = "cohesion_smell"


class Severity(Enum):
    """严重程度"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class CodeSmell:
    """代码异味数据类"""
    smell_type: SmellType
    category: SmellCategory
    severity: Severity
    file_path: str
    line_start: int
    line_end: int
    description: str
    code_snippet: str = ""
    metrics: Dict[str, Any] = field(default_factory=dict)
    suggestions: List[str] = field(default_factory=list)
    refactoring_patterns: List[str] = field(default_factory=list)
    priority: int = 0
    impact_score: float = 0.0
    effort_score: float = 1.0
    related_smells: List[str] = field(default_factory=list)
    detection_confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "smell_type": self.smell_type.value,
            "category": self.category.value,
            "severity": self.severity.value,
            "file_path": self.file_path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "description": self.description,
            "code_snippet": self.code_snippet[:100],
            "metrics": self.metrics,
            "suggestions": self.suggestions,
            "refactoring_patterns": self.refactoring_patterns,
            "priority": self.priority,
            "impact_score": round(self.impact_score, 2),
            "effort_score": round(self.effort_score, 2),
            "related_smells": self.related_smells,
            "detection_confidence": round(self.detection_confidence, 2)
        }


@dataclass
class FileAnalysisResult:
    """文件分析结果"""
    file_path: str
    smells: List[CodeSmell] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    lines_of_code: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "smells": [s.to_dict() for s in self.smells],
            "metrics": self.metrics,
            "lines_of_code": self.lines_of_code,
            "smell_count": len(self.smells)
        }


@dataclass
class DetectionReport:
    """检测报告"""
    timestamp: str
    project_root: str
    total_files: int
    total_smells: int
    file_results: List[FileAnalysisResult]
    summary: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "project_root": self.project_root,
            "total_files": self.total_files,
            "total_smells": self.total_smells,
            "summary": self.summary,
            "recommendations": self.recommendations,
            "file_results": [r.to_dict() for r in self.file_results]
        }


class ComplexityCalculator(ast.NodeVisitor):
    """复杂度计算器"""

    def __init__(self):
        self.complexity = 1
        self.nesting_depth = 0
        self.max_nesting_depth = 0

    def visit_If(self, node: ast.If):
        self.complexity += 1
        self._visit_with_nesting(node)

    def visit_For(self, node: ast.For):
        self.complexity += 1
        self._visit_with_nesting(node)

    def visit_While(self, node: ast.While):
        self.complexity += 1
        self._visit_with_nesting(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler):
        self.complexity += 1
        self.generic_visit(node)

    def visit_BoolOp(self, node: ast.BoolOp):
        self.complexity += len(node.values) - 1
        self.generic_visit(node)

    def visit_comprehension(self, node: ast.comprehension):
        self.complexity += 1
        self.generic_visit(node)

    def _visit_with_nesting(self, node: ast.AST):
        self.nesting_depth += 1
        self.max_nesting_depth = max(self.max_nesting_depth, self.nesting_depth)
        self.generic_visit(node)
        self.nesting_depth -= 1


class RefactoringSuggestionEngine:
    """重构建议引擎"""

    REFACTORING_PATTERNS = {
        SmellType.LONG_METHOD: {
            "pattern": "Extract Method",
            "description": "将长方法拆分为多个小方法",
            "steps": [
                "识别方法中的独立功能块",
                "为每个功能块创建新方法",
                "给新方法起一个描述性的名字",
                "用方法调用替换原代码",
                "运行测试验证行为不变"
            ],
            "example": "def process_data(data):\n    # 提取验证逻辑\n    validated = validate_data(data)\n    # 提取转换逻辑\n    transformed = transform_data(validated)\n    # 提取保存逻辑\n    return save_data(transformed)",
            "effort": 2,
            "impact": 3
        },
        SmellType.LARGE_CLASS: {
            "pattern": "Extract Class",
            "description": "将大类拆分为多个小类",
            "steps": [
                "识别类中的不同职责",
                "为每个职责创建新类",
                "移动相关属性和方法",
                "建立类之间的关系",
                "更新客户端代码"
            ],
            "example": "# 将大类拆分\nclass User:\n    def __init__(self, name, email):\n        self.name = name\n        self.email = email\n\nclass UserRepository:\n    def save(self, user): pass\n    def find(self, id): pass",
            "effort": 3,
            "impact": 4
        },
        SmellType.DEEP_NESTING: {
            "pattern": "Replace Nested Conditional with Guard Clauses",
            "description": "使用卫语句减少嵌套",
            "steps": [
                "识别嵌套的条件判断",
                "反转条件，提前返回",
                "逐步减少嵌套层级",
                "简化剩余逻辑"
            ],
            "example": "# 使用卫语句\nif not user:\n    return None\nif not user.is_active:\n    return None\nif not user.has_permission:\n    return None\nreturn process_user(user)",
            "effort": 1,
            "impact": 3
        },
        SmellType.LONG_PARAMETER_LIST: {
            "pattern": "Introduce Parameter Object",
            "description": "引入参数对象封装相关参数",
            "steps": [
                "识别经常一起出现的参数",
                "创建新的参数对象类",
                "修改方法签名使用新对象",
                "更新所有调用点"
            ],
            "example": "@dataclass\nclass SearchParams:\n    query: str\n    page: int\n    size: int\n    sort: str\n\ndef search(params: SearchParams): pass",
            "effort": 2,
            "impact": 2
        },
        SmellType.DUPLICATE_CODE: {
            "pattern": "Extract Method / Pull Up Method",
            "description": "提取公共代码消除重复",
            "steps": [
                "识别重复的代码片段",
                "创建公共方法",
                "用方法调用替换重复代码",
                "考虑使用模板方法模式"
            ],
            "example": "# 提取公共方法\ndef validate_email(email):\n    return '@' in email and '.' in email\n\ndef validate_user(user):\n    return validate_email(user.email)\n\ndef validate_contact(contact):\n    return validate_email(contact.email)",
            "effort": 1,
            "impact": 4
        },
        SmellType.HIGH_COMPLEXITY: {
            "pattern": "Decompose Conditional / Replace Conditional with Polymorphism",
            "description": "分解复杂条件或使用多态",
            "steps": [
                "分析复杂条件表达式",
                "提取条件为独立方法",
                "考虑使用策略模式",
                "或使用状态模式替代条件"
            ],
            "example": "# 使用策略模式\nclass PaymentStrategy:\n    def pay(self, amount): pass\n\nclass CreditCardPayment(PaymentStrategy):\n    def pay(self, amount): pass\n\nclass PayPalPayment(PaymentStrategy):\n    def pay(self, amount): pass",
            "effort": 3,
            "impact": 4
        },
        SmellType.SWITCH_STATEMENTS: {
            "pattern": "Replace Type Code with State/Strategy",
            "description": "用状态模式或策略模式替代switch",
            "steps": [
                "识别switch或if-elif链",
                "为每种情况创建类",
                "使用多态替代条件判断",
                "简化客户端代码"
            ],
            "example": "# 使用状态模式\nclass OrderState:\n    def process(self, order): pass\n\nclass NewOrder(OrderState):\n    def process(self, order): pass\n\nclass ShippedOrder(OrderState):\n    def process(self, order): pass",
            "effort": 2,
            "impact": 3
        },
        SmellType.FEATURE_ENVY: {
            "pattern": "Move Method",
            "description": "将方法移动到它所依赖的类",
            "steps": [
                "识别过度访问其他类的方法",
                "确定方法应该属于哪个类",
                "移动方法到目标类",
                "更新调用点"
            ],
            "example": "# 移动方法到正确的类\nclass Report:\n    def generate(self, data):\n        return self.formatter.format(data)\n\nclass Formatter:\n    def format(self, data):\n        return formatted_data",
            "effort": 2,
            "impact": 2
        },
        SmellType.DATA_CLUMPS: {
            "pattern": "Extract Class / Introduce Parameter Object",
            "description": "将相关数据封装为类",
            "steps": [
                "识别经常一起出现的数据",
                "创建新的数据类",
                "替换原始参数为对象",
                "添加相关行为方法"
            ],
            "example": "@dataclass\nclass Address:\n    street: str\n    city: str\n    zip_code: str\n    country: str\n\nclass User:\n    def __init__(self, name, address: Address): pass",
            "effort": 2,
            "impact": 3
        },
        SmellType.GOD_CLASS: {
            "pattern": "Extract Class / Extract Subclass",
            "description": "拆分上帝类为多个专注的类",
            "steps": [
                "识别类的不同职责",
                "为每个职责创建新类",
                "逐步迁移功能",
                "确保测试覆盖"
            ],
            "example": "# 拆分上帝类\nclass UserService:\n    def create_user(self): pass\n    def update_user(self): pass\n\nclass UserValidator:\n    def validate(self, user): pass\n\nclass UserRepository:\n    def save(self, user): pass",
            "effort": 4,
            "impact": 5
        },
        SmellType.PRIMITIVE_OBSESSION: {
            "pattern": "Replace Data Value with Object",
            "description": "用对象替代基本类型",
            "steps": [
                "识别被过度使用的基本类型",
                "创建新的值对象类",
                "封装验证逻辑",
                "替换所有使用点"
            ],
            "example": "class Money:\n    def __init__(self, amount: int, currency: str):\n        self.amount = amount\n        self.currency = currency",
            "effort": 2,
            "impact": 2
        },
        SmellType.MESSAGE_CHAINS: {
            "pattern": "Hide Delegate",
            "description": "隐藏委托链",
            "steps": [
                "识别长消息链",
                "在中间对象上添加委托方法",
                "简化客户端调用",
                "减少耦合"
            ],
            "example": "# 隐藏委托\n# 之前: manager.department.company.name\n# 之后: manager.get_company_name()",
            "effort": 1,
            "impact": 2
        },
        SmellType.MIDDLE_MAN: {
            "pattern": "Remove Middle Man",
            "description": "移除中间人",
            "steps": [
                "识别过度委托的类",
                "让客户端直接调用目标",
                "移除不必要的委托方法",
                "简化代码结构"
            ],
            "example": "# 移除中间人\n# 之前: class Manager:\n#           def get_department(self): return self.department\n# 之后: 客户端直接访问 department",
            "effort": 1,
            "impact": 1
        },
        SmellType.COMMENTS_SMELL: {
            "pattern": "Extract Method / Rename Variable",
            "description": "用代码本身表达意图",
            "steps": [
                "识别需要注释解释的代码",
                "提取方法并用方法名表达意图",
                "重命名变量使其更有意义",
                "删除多余注释"
            ],
            "example": "# 之前:\n# Check if user is valid and active\nif user and user.status == 'active':\n    ...\n\n# 之后:\nif is_valid_active_user(user):\n    ...",
            "effort": 1,
            "impact": 2
        },
        SmellType.NAMING_SMELL: {
            "pattern": "Rename Method / Rename Variable",
            "description": "重命名以表达意图",
            "steps": [
                "识别命名不清晰的变量或方法",
                "选择能表达意图的名称",
                "使用IDE重构功能重命名",
                "确保所有引用都已更新"
            ],
            "example": "# 之前: def process(d): pass\n# 之后: def process_user_data(user_data): pass",
            "effort": 1,
            "impact": 2
        },
        SmellType.COUPLING_SMELL: {
            "pattern": "Introduce Interface / Dependency Injection",
            "description": "降低耦合度",
            "steps": [
                "识别紧耦合的类",
                "提取接口",
                "使用依赖注入",
                "减少直接依赖"
            ],
            "example": "# 引入接口\nclass IUserRepository(ABC):\n    @abstractmethod\n    def find(self, user_id): pass\n\nclass UserService:\n    def __init__(self, repo: IUserRepository):\n        self.repo = repo",
            "effort": 3,
            "impact": 4
        },
        SmellType.COHESION_SMELL: {
            "pattern": "Extract Class",
            "description": "提高内聚性",
            "steps": [
                "识别低内聚的类",
                "按职责分组方法",
                "提取新类",
                "建立正确的关系"
            ],
            "example": "# 提高内聚\nclass User:\n    def __init__(self, name, email):\n        self.name = name\n        self.email = email\n\nclass UserPersistence:\n    def save(self, user): pass\n    def load(self, user_id): pass",
            "effort": 2,
            "impact": 3
        }
    }

    PRIORITY_WEIGHTS = {
        "severity": 0.4,
        "impact": 0.3,
        "occurrence": 0.2,
        "effort": 0.1
    }

    SEVERITY_SCORES = {
        Severity.CRITICAL: 5,
        Severity.HIGH: 4,
        Severity.MEDIUM: 3,
        Severity.LOW: 2,
        Severity.INFO: 1
    }

    def __init__(self):
        self.suggestions: List[Dict[str, Any]] = []

    def generate_suggestions(self, smells: List[CodeSmell]) -> List[Dict[str, Any]]:
        """根据代码异味生成重构建议"""
        self.suggestions = []
        smell_counts: Dict[SmellType, List[CodeSmell]] = defaultdict(list)

        for smell in smells:
            smell_counts[smell.smell_type].append(smell)

        for smell_type, smell_list in smell_counts.items():
            pattern_info = self.REFACTORING_PATTERNS.get(smell_type)
            if pattern_info:
                suggestion = self._create_suggestion(smell_type, smell_list, pattern_info)
                self.suggestions.append(suggestion)

        self.suggestions.sort(key=lambda x: x["priority_score"], reverse=True)
        return self.suggestions

    def _create_suggestion(self, smell_type: SmellType, smells: List[CodeSmell],
                           pattern_info: Dict[str, Any]) -> Dict[str, Any]:
        """创建重构建议"""
        max_severity = max(smells, key=lambda x: self.SEVERITY_SCORES.get(x.severity, 0))
        
        severity_score = self.SEVERITY_SCORES.get(max_severity.severity, 0)
        impact_score = pattern_info.get("impact", 3)
        occurrence_score = min(len(smells), 10)
        effort_score = pattern_info.get("effort", 2)
        
        priority_score = (
            severity_score * self.PRIORITY_WEIGHTS["severity"] * 10 +
            impact_score * self.PRIORITY_WEIGHTS["impact"] * 10 +
            occurrence_score * self.PRIORITY_WEIGHTS["occurrence"] +
            (6 - effort_score) * self.PRIORITY_WEIGHTS["effort"] * 5
        )

        return {
            "smell_type": smell_type.value,
            "pattern": pattern_info["pattern"],
            "description": pattern_info["description"],
            "priority": max_severity.severity.value,
            "priority_score": round(priority_score, 2),
            "occurrences": len(smells),
            "affected_files": list(set(s.file_path for s in smells[:5])),
            "steps": pattern_info["steps"],
            "example": pattern_info.get("example", ""),
            "effort": effort_score,
            "impact": impact_score,
            "sample_location": {
                "file": smells[0].file_path,
                "line": smells[0].line_start,
                "description": smells[0].description
            }
        }

    def generate_refactoring_plan(self, smells: List[CodeSmell]) -> Dict[str, Any]:
        """生成完整的重构计划"""
        suggestions = self.generate_suggestions(smells)

        phases = {
            "immediate": [],
            "short_term": [],
            "medium_term": [],
            "long_term": []
        }

        for suggestion in suggestions:
            if suggestion["priority"] in ["critical", "high"]:
                phases["immediate"].append(suggestion)
            elif suggestion["priority"] == "medium":
                if suggestion["occurrences"] > 3:
                    phases["short_term"].append(suggestion)
                else:
                    phases["medium_term"].append(suggestion)
            else:
                phases["long_term"].append(suggestion)

        return {
            "total_issues": len(smells),
            "phases": phases,
            "estimated_effort": self._estimate_effort(phases),
            "priorities": {
                "immediate": len(phases["immediate"]),
                "short_term": len(phases["short_term"]),
                "medium_term": len(phases["medium_term"]),
                "long_term": len(phases["long_term"])
            },
            "roi_analysis": self._calculate_roi(suggestions)
        }

    def _estimate_effort(self, phases: Dict[str, List]) -> Dict[str, str]:
        """估算重构工作量"""
        effort_map = {
            "immediate": {"small": "1-2天", "medium": "3-5天", "large": "1-2周"},
            "short_term": {"small": "2-3天", "medium": "1周", "large": "2周"},
            "medium_term": {"small": "3-5天", "medium": "1-2周", "large": "3-4周"},
            "long_term": {"small": "1周", "medium": "2-3周", "large": "1个月+"}
        }

        result = {}
        for phase, items in phases.items():
            count = len(items)
            if count == 0:
                result[phase] = "无需处理"
            elif count <= 3:
                result[phase] = effort_map[phase]["small"]
            elif count <= 7:
                result[phase] = effort_map[phase]["medium"]
            else:
                result[phase] = effort_map[phase]["large"]

        return result

    def _calculate_roi(self, suggestions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """计算投资回报率分析"""
        if not suggestions:
            return {"high_roi": [], "medium_roi": [], "low_roi": []}

        for s in suggestions:
            roi_score = (s.get("impact", 3) * 2) / max(s.get("effort", 2), 1)
            s["roi_score"] = round(roi_score, 2)

        sorted_suggestions = sorted(suggestions, key=lambda x: x.get("roi_score", 0), reverse=True)

        high_roi = [s for s in sorted_suggestions if s.get("roi_score", 0) >= 2]
        medium_roi = [s for s in sorted_suggestions if 1 <= s.get("roi_score", 0) < 2]
        low_roi = [s for s in sorted_suggestions if s.get("roi_score", 0) < 1]

        return {
            "high_roi": [{"pattern": s["pattern"], "roi_score": s["roi_score"]} for s in high_roi[:5]],
            "medium_roi": [{"pattern": s["pattern"], "roi_score": s["roi_score"]} for s in medium_roi[:5]],
            "low_roi": [{"pattern": s["pattern"], "roi_score": s["roi_score"]} for s in low_roi[:5]]
        }

    def prioritize_smells(self, smells: List[CodeSmell]) -> List[CodeSmell]:
        """对代码异味进行优先级排序"""
        for smell in smells:
            pattern_info = self.REFACTORING_PATTERNS.get(smell.smell_type, {})
            
            severity_score = self.SEVERITY_SCORES.get(smell.severity, 0)
            impact_score = pattern_info.get("impact", 3)
            effort_score = pattern_info.get("effort", 2)
            
            smell.priority = int(severity_score * 10 + impact_score * 5)
            smell.impact_score = float(impact_score)
            smell.effort_score = float(effort_score)
            smell.detection_confidence = self._calculate_confidence(smell)

        return sorted(smells, key=lambda x: x.priority, reverse=True)

    def _calculate_confidence(self, smell: CodeSmell) -> float:
        """计算检测置信度"""
        base_confidence = 0.8
        
        if smell.metrics:
            metric_count = len(smell.metrics)
            base_confidence += min(metric_count * 0.05, 0.15)
        
        if smell.code_snippet:
            base_confidence += 0.05
        
        return min(base_confidence, 1.0)


class CodeSmellDetector(ast.NodeVisitor):
    """代码异味检测器"""

    THRESHOLDS = {
        "long_method_lines": 50,
        "large_class_lines": 300,
        "large_class_methods": 20,
        "long_parameter_list": 5,
        "deep_nesting": 4,
        "high_complexity": 10,
        "god_class_methods": 30,
        "god_class_lines": 500,
        "feature_envy_threshold": 0.5,
        "duplicate_code_lines": 6
    }

    def __init__(self, file_path: str, content: str):
        self.file_path = file_path
        self.content = content
        self.lines = content.split('\n')
        self.smells: List[CodeSmell] = []
        self.current_class: Optional[str] = None
        self.class_methods: Dict[str, List[str]] = defaultdict(list)
        self.class_attributes: Dict[str, Set[str]] = defaultdict(set)
        self.method_calls: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self.external_calls: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))

    def detect(self) -> List[CodeSmell]:
        try:
            tree = ast.parse(self.content)
            self.visit(tree)
            self._detect_duplicate_code()
            self._detect_data_clumps(tree)
            self._detect_god_classes()
        except SyntaxError as e:
            self.smells.append(CodeSmell(
                smell_type=SmellType.DEAD_CODE,
                category=SmellCategory.DISPENSABLES,
                severity=Severity.CRITICAL,
                file_path=self.file_path,
                line_start=e.lineno or 1,
                line_end=e.lineno or 1,
                description=f"语法错误: {e.msg}",
                suggestions=["修复语法错误"],
                refactoring_patterns=["fix_syntax"]
            ))
        return self.smells

    def visit_ClassDef(self, node: ast.ClassDef):
        old_class = self.current_class
        self.current_class = node.name

        line_start = node.lineno
        line_end = getattr(node, 'end_lineno', line_start) or line_start
        class_lines = line_end - line_start + 1
        method_count = sum(1 for n in ast.walk(node) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)))

        if class_lines > self.THRESHOLDS["large_class_lines"]:
            self.smells.append(CodeSmell(
                smell_type=SmellType.LARGE_CLASS,
                category=SmellCategory.BLOATERS,
                severity=Severity.HIGH if class_lines > self.THRESHOLDS["large_class_lines"] * 1.5 else Severity.MEDIUM,
                file_path=self.file_path,
                line_start=line_start,
                line_end=line_end,
                description=f"类过大: {class_lines} 行 (阈值: {self.THRESHOLDS['large_class_lines']})",
                metrics={"lines": class_lines, "methods": method_count},
                suggestions=[
                    "将类拆分为多个小类",
                    "使用提取类重构",
                    "考虑单一职责原则"
                ],
                refactoring_patterns=["extract_class", "extract_subclass"]
            ))

        if method_count > self.THRESHOLDS["large_class_methods"]:
            self.smells.append(CodeSmell(
                smell_type=SmellType.LARGE_CLASS,
                category=SmellCategory.BLOATERS,
                severity=Severity.MEDIUM,
                file_path=self.file_path,
                line_start=line_start,
                line_end=line_end,
                description=f"类方法过多: {method_count} 个 (阈值: {self.THRESHOLDS['large_class_methods']})",
                metrics={"methods": method_count},
                suggestions=[
                    "将相关方法分组到新类中",
                    "使用模块替代部分功能"
                ],
                refactoring_patterns=["extract_class", "extract_module"]
            ))

        self.generic_visit(node)
        self.current_class = old_class

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._analyze_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._analyze_function(node)

    def _analyze_function(self, node):
        line_start = node.lineno
        line_end = getattr(node, 'end_lineno', line_start) or line_start
        line_count = line_end - line_start + 1

        param_count = len(node.args.args) + len(node.args.kwonlyargs)
        if node.args.vararg:
            param_count += 1
        if node.args.kwarg:
            param_count += 1

        complexity_calc = ComplexityCalculator()
        complexity_calc.visit(node)
        complexity = complexity_calc.complexity
        max_nesting = complexity_calc.max_nesting_depth

        if line_count > self.THRESHOLDS["long_method_lines"]:
            severity = Severity.HIGH if line_count > self.THRESHOLDS["long_method_lines"] * 1.5 else Severity.MEDIUM
            self.smells.append(CodeSmell(
                smell_type=SmellType.LONG_METHOD,
                category=SmellCategory.BLOATERS,
                severity=severity,
                file_path=self.file_path,
                line_start=line_start,
                line_end=line_end,
                description=f"方法过长: {line_count} 行 (阈值: {self.THRESHOLDS['long_method_lines']})",
                metrics={"lines": line_count, "name": node.name},
                suggestions=[
                    "提取方法: 将部分逻辑提取为独立方法",
                    "使用提取方法对象重构",
                    "分解职责到多个方法"
                ],
                refactoring_patterns=["extract_method", "replace_method_with_method_object"]
            ))

        if param_count > self.THRESHOLDS["long_parameter_list"]:
            self.smells.append(CodeSmell(
                smell_type=SmellType.LONG_PARAMETER_LIST,
                category=SmellCategory.BLOATERS,
                severity=Severity.MEDIUM,
                file_path=self.file_path,
                line_start=line_start,
                line_end=line_end,
                description=f"参数列表过长: {param_count} 个 (阈值: {self.THRESHOLDS['long_parameter_list']})",
                metrics={"parameter_count": param_count},
                suggestions=[
                    "使用参数对象封装相关参数",
                    "使用建造者模式",
                    "考虑使用配置对象"
                ],
                refactoring_patterns=["introduce_parameter_object", "preserve_whole_object"]
            ))

        if max_nesting > self.THRESHOLDS["deep_nesting"]:
            severity = Severity.HIGH if max_nesting > self.THRESHOLDS["deep_nesting"] + 2 else Severity.MEDIUM
            self.smells.append(CodeSmell(
                smell_type=SmellType.DEEP_NESTING,
                category=SmellCategory.COMPLEXITY,
                severity=severity,
                file_path=self.file_path,
                line_start=line_start,
                line_end=line_end,
                description=f"嵌套过深: {max_nesting} 层 (阈值: {self.THRESHOLDS['deep_nesting']})",
                metrics={"nesting_depth": max_nesting},
                suggestions=[
                    "使用卫语句提前返回",
                    "提取嵌套逻辑到独立方法",
                    "使用多态替代条件判断"
                ],
                refactoring_patterns=["replace_nested_conditional_with_guard_clauses", "extract_method"]
            ))

        if complexity > self.THRESHOLDS["high_complexity"]:
            severity = Severity.HIGH if complexity > self.THRESHOLDS["high_complexity"] * 1.5 else Severity.MEDIUM
            self.smells.append(CodeSmell(
                smell_type=SmellType.HIGH_COMPLEXITY,
                category=SmellCategory.COMPLEXITY,
                severity=severity,
                file_path=self.file_path,
                line_start=line_start,
                line_end=line_end,
                description=f"圈复杂度过高: {complexity} (阈值: {self.THRESHOLDS['high_complexity']})",
                metrics={"complexity": complexity},
                suggestions=[
                    "简化条件逻辑",
                    "使用策略模式替代多重条件",
                    "分解复杂方法"
                ],
                refactoring_patterns=["decompose_conditional", "replace_conditional_with_polymorphism"]
            ))

        switch_like = self._detect_switch_like_pattern(node)
        if switch_like:
            self.smells.append(CodeSmell(
                smell_type=SmellType.SWITCH_STATEMENTS,
                category=SmellCategory.OBJECT_ORIENTED_ABUSERS,
                severity=Severity.MEDIUM,
                file_path=self.file_path,
                line_start=line_start,
                line_end=line_end,
                description="检测到类似switch的模式",
                metrics={"case_count": switch_like},
                suggestions=[
                    "使用多态替代switch",
                    "使用状态模式",
                    "使用策略模式"
                ],
                refactoring_patterns=["replace_conditional_with_polymorphism", "replace_type_code_with_state"]
            ))

        self.generic_visit(node)

    def _detect_switch_like_pattern(self, node: ast.FunctionDef) -> int:
        if_count = 0
        elif_count = 0

        for child in ast.walk(node):
            if isinstance(child, ast.If):
                if_count += 1
                for sub in ast.walk(child):
                    if isinstance(sub, ast.If) and sub != child:
                        elif_count += 1

        return if_count + elif_count if if_count >= 3 else 0

    def _detect_duplicate_code(self):
        code_blocks: Dict[str, List[Tuple[int, int, str]]] = defaultdict(list)

        for i in range(len(self.lines) - self.THRESHOLDS["duplicate_code_lines"] + 1):
            block = '\n'.join(self.lines[i:i + self.THRESHOLDS["duplicate_code_lines"]])
            normalized = self._normalize_code(block)
            if normalized and not normalized.strip().startswith('#'):
                block_hash = hashlib.md5(normalized.encode()).hexdigest()
                code_blocks[block_hash].append((i + 1, i + self.THRESHOLDS["duplicate_code_lines"], block))

        for block_hash, locations in code_blocks.items():
            if len(locations) > 1:
                first_loc = locations[0]
                self.smells.append(CodeSmell(
                    smell_type=SmellType.DUPLICATE_CODE,
                    category=SmellCategory.DISPENSABLES,
                    severity=Severity.HIGH,
                    file_path=self.file_path,
                    line_start=first_loc[0],
                    line_end=first_loc[1],
                    description=f"重复代码块: 发现 {len(locations)} 处相似代码",
                    metrics={"occurrences": len(locations)},
                    suggestions=[
                        "提取公共代码到方法",
                        "使用模板方法模式",
                        "考虑使用继承或组合"
                    ],
                    refactoring_patterns=["extract_method", "pull_up_method", "form_template_method"]
                ))

    def _normalize_code(self, code: str) -> str:
        normalized = re.sub(r'#.*$', '', code, flags=re.MULTILINE)
        normalized = re.sub(r'\s+', ' ', normalized)
        return normalized.strip()

    def _detect_data_clumps(self, tree: ast.AST):
        param_groups: Dict[str, List[Tuple[str, int]]] = defaultdict(list)

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                params = [arg.arg for arg in node.args.args if not arg.arg.startswith('_')]
                if len(params) >= 3:
                    param_key = ','.join(sorted(params[:4]))
                    param_groups[param_key].append((node.name, node.lineno))

        for param_key, occurrences in param_groups.items():
            if len(occurrences) > 2:
                params = param_key.split(',')
                self.smells.append(CodeSmell(
                    smell_type=SmellType.DATA_CLUMPS,
                    category=SmellCategory.BLOATERS,
                    severity=Severity.MEDIUM,
                    file_path=self.file_path,
                    line_start=occurrences[0][1],
                    line_end=occurrences[0][1],
                    description=f"数据泥团: 参数 {', '.join(params)} 在多处出现",
                    metrics={"occurrences": len(occurrences), "params": params},
                    suggestions=[
                        "将这些参数封装为类",
                        "使用数据传输对象",
                        "引入参数对象"
                    ],
                    refactoring_patterns=["introduce_parameter_object", "extract_class"]
                ))

    def _detect_god_classes(self):
        pass


class IntelligentCodeSmellDetector:
    """智能代码异味检测器"""

    def __init__(self, project_root: Optional[Path] = None,
                 min_severity: Severity = Severity.LOW,
                 logger: Optional[logging.Logger] = None):
        self.project_root = project_root or get_path_config().SKILL_ROOT
        self.min_severity = min_severity
        self.logger = logger or logging.getLogger(__name__)
        self.file_results: List[FileAnalysisResult] = []
        self.refactoring_engine = RefactoringSuggestionEngine()

    def detect_project(self) -> DetectionReport:
        """检测整个项目"""
        self.logger.info("开始智能代码异味检测...")

        python_files = self._collect_python_files()
        self.logger.info(f"找到 {len(python_files)} 个Python文件")

        for py_file in python_files:
            result = self._analyze_file(py_file)
            if result.smells:
                self.file_results.append(result)

        summary = self._calculate_summary()
        recommendations = self._generate_recommendations()
        refactoring_plan = self._generate_refactoring_plan()

        return DetectionReport(
            timestamp=datetime.now().isoformat(),
            project_root=str(self.project_root),
            total_files=len(python_files),
            total_smells=sum(len(r.smells) for r in self.file_results),
            file_results=self.file_results,
            summary=summary,
            recommendations=recommendations
        )

    def _generate_refactoring_plan(self) -> Dict[str, Any]:
        """生成重构计划"""
        all_smells = []
        for result in self.file_results:
            all_smells.extend(result.smells)

        return self.refactoring_engine.generate_refactoring_plan(all_smells)

    def _collect_python_files(self) -> List[Path]:
        python_files = []

        backend_dir = self.project_root / "backend"
        if backend_dir.exists():
            for py_file in backend_dir.rglob("*.py"):
                if "__pycache__" not in str(py_file):
                    python_files.append(py_file)

        scripts_dir = self.project_root / "scripts"
        if scripts_dir.exists():
            for py_file in scripts_dir.rglob("*.py"):
                if "__pycache__" not in str(py_file):
                    python_files.append(py_file)

        return python_files

    def _analyze_file(self, file_path: Path) -> FileAnalysisResult:
        """分析单个文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            detector = CodeSmellDetector(str(file_path), content)
            smells = detector.detect()

            severity_order = {
                Severity.CRITICAL: 0,
                Severity.HIGH: 1,
                Severity.MEDIUM: 2,
                Severity.LOW: 3,
                Severity.INFO: 4
            }
            filtered_smells = [
                s for s in smells
                if severity_order.get(s.severity, 99) <= severity_order.get(self.min_severity, 99)
            ]

            return FileAnalysisResult(
                file_path=str(file_path),
                smells=filtered_smells,
                lines_of_code=len(content.split('\n'))
            )
        except Exception as e:
            self.logger.error(f"分析文件失败 {file_path}: {e}")
            return FileAnalysisResult(file_path=str(file_path))

    def _calculate_summary(self) -> Dict[str, Any]:
        """计算摘要"""
        if not self.file_results:
            return {
                "total_smells": 0,
                "by_category": {},
                "by_severity": {},
                "by_type": {},
                "top_smelly_files": []
            }

        by_category: Dict[str, int] = defaultdict(int)
        by_severity: Dict[str, int] = defaultdict(int)
        by_type: Dict[str, int] = defaultdict(int)

        for result in self.file_results:
            for smell in result.smells:
                by_category[smell.category.value] += 1
                by_severity[smell.severity.value] += 1
                by_type[smell.smell_type.value] += 1

        file_smell_counts = [
            (r.file_path, len(r.smells))
            for r in self.file_results
        ]
        file_smell_counts.sort(key=lambda x: x[1], reverse=True)

        return {
            "total_smells": sum(len(r.smells) for r in self.file_results),
            "by_category": dict(by_category),
            "by_severity": dict(by_severity),
            "by_type": dict(by_type),
            "top_smelly_files": file_smell_counts[:10]
        }

    def _generate_recommendations(self) -> List[str]:
        """生成重构建议"""
        recommendations = []

        if not self.file_results:
            return ["代码质量良好，未发现明显代码异味"]

        summary = self._calculate_summary()

        by_type = summary.get("by_type", {})

        if by_type.get("long_method", 0) > 5:
            recommendations.append("建议优先处理长方法问题，使用提取方法重构")

        if by_type.get("deep_nesting", 0) > 3:
            recommendations.append("建议重构深度嵌套代码，使用卫语句简化逻辑")

        if by_type.get("duplicate_code", 0) > 0:
            recommendations.append("发现重复代码，建议提取公共方法消除重复")

        if by_type.get("high_complexity", 0) > 3:
            recommendations.append("存在高复杂度方法，建议分解简化")

        if by_type.get("long_parameter_list", 0) > 2:
            recommendations.append("参数列表过长，建议使用参数对象封装")

        if not recommendations:
            recommendations.append("建议按照严重程度优先处理高优先级问题")

        return recommendations

    def print_report(self, report: DetectionReport):
        """打印报告"""
        print("\n" + "=" * 80)
        print("智能代码异味检测报告")
        print("=" * 80)
        print(f"项目根目录: {report.project_root}")
        print(f"检测时间: {report.timestamp}")
        print(f"扫描文件数: {report.total_files}")
        print(f"发现问题数: {report.total_smells}")

        print("\n" + "-" * 80)
        print("摘要统计")
        print("-" * 80)

        summary = report.summary
        print(f"\n按类别统计:")
        for cat, count in summary.get("by_category", {}).items():
            print(f"  {cat}: {count}")

        print(f"\n按严重程度统计:")
        for sev, count in summary.get("by_severity", {}).items():
            print(f"  {sev}: {count}")

        print(f"\n按类型统计 (Top 10):")
        by_type = summary.get("by_type", {})
        sorted_types = sorted(by_type.items(), key=lambda x: x[1], reverse=True)
        for smell_type, count in sorted_types[:10]:
            print(f"  {smell_type}: {count}")

        print(f"\n问题最多的文件 (Top 5):")
        for file_path, count in summary.get("top_smelly_files", [])[:5]:
            print(f"  {Path(file_path).name}: {count} 个问题")

        if report.recommendations:
            print("\n" + "-" * 80)
            print("重构建议")
            print("-" * 80)
            for i, rec in enumerate(report.recommendations, 1):
                print(f"{i}. {rec}")

        if report.file_results:
            print("\n" + "-" * 80)
            print("详细问题列表")
            print("-" * 80)

            severity_order = {
                Severity.CRITICAL: 0,
                Severity.HIGH: 1,
                Severity.MEDIUM: 2,
                Severity.LOW: 3,
                Severity.INFO: 4
            }

            all_smells = []
            for result in report.file_results:
                for smell in result.smells:
                    all_smells.append((result.file_path, smell))

            all_smells.sort(key=lambda x: severity_order.get(x[1].severity, 99))

            for i, (file_path, smell) in enumerate(all_smells[:30], 1):
                severity_icon = {
                    Severity.CRITICAL: "🔴",
                    Severity.HIGH: "🟠",
                    Severity.MEDIUM: "🟡",
                    Severity.LOW: "🔵",
                    Severity.INFO: "⚪"
                }.get(smell.severity, "⚪")

                print(f"\n{i}. {severity_icon} [{smell.severity.value.upper()}] {smell.smell_type.value}")
                print(f"   文件: {Path(file_path).name}:{smell.line_start}")
                print(f"   描述: {smell.description}")
                if smell.suggestions:
                    print(f"   建议: {smell.suggestions[0]}")

            if len(all_smells) > 30:
                print(f"\n... 还有 {len(all_smells) - 30} 个问题未显示")

    def save_report(self, report: DetectionReport, output_dir: Optional[Path] = None) -> Path:
        """保存报告"""
        if output_dir is None:
            output_dir = get_path_config().REPORTS_DIR
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = output_dir / f"code_smell_detection_{timestamp}.json"

        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)

        latest_path = output_dir / "code_smell_detection_latest.json"
        with open(latest_path, 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)

        self.logger.info(f"报告已保存: {report_path}")
        return report_path


def setup_logger(verbose: bool = False) -> logging.Logger:
    """配置日志记录器"""
    logger = logging.getLogger("IntelligentCodeSmellDetector")
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
        description="智能代码异味检测器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python intelligent_code_smell_detector.py
  python intelligent_code_smell_detector.py --severity high
  python intelligent_code_smell_detector.py --output json
        """
    )

    parser.add_argument(
        "--severity",
        choices=["critical", "high", "medium", "low", "info"],
        default="low",
        help="最低严重程度 (默认: low)"
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

    severity_map = {
        "critical": Severity.CRITICAL,
        "high": Severity.HIGH,
        "medium": Severity.MEDIUM,
        "low": Severity.LOW,
        "info": Severity.INFO
    }

    detector = IntelligentCodeSmellDetector(
        min_severity=severity_map[args.severity],
        logger=logger
    )
    report = detector.detect_project()

    detector.print_report(report)

    report_path = detector.save_report(report)
    print(f"\n报告已保存到: {report_path}")

    if args.output == "json":
        output_data = json.dumps(report.to_dict(), ensure_ascii=False, indent=2)

        if args.output_file:
            output_path = Path(args.output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(output_data)
            print(f"\nJSON结果已保存到: {output_path}")
        else:
            print("\nJSON结果:")
            print(output_data)

    return 0 if report.total_smells == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
