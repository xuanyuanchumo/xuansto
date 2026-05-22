#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI辅助代码分析器

集成AI代码分析模型，支持：
- 代码质量评估
- 智能审查建议
- 代码模式识别
- 潜在问题预测
- 最佳实践推荐

使用示例:
    python ai_code_analyzer.py --target backend/app
    python ai_code_analyzer.py --target backend/app --output json
    python ai_code_analyzer.py --target backend/app --mode full
"""

import os
import sys
import ast
import re
import json
import argparse
import logging
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict
from abc import ABC, abstractmethod


class AnalysisMode(Enum):
    """分析模式"""
    QUICK = "quick"
    STANDARD = "standard"
    FULL = "full"


class ConfidenceLevel(Enum):
    """置信度级别"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class SuggestionCategory(Enum):
    """建议类别"""
    PERFORMANCE = "performance"
    SECURITY = "security"
    MAINTAINABILITY = "maintainability"
    BEST_PRACTICE = "best_practice"
    ARCHITECTURE = "architecture"
    STYLE = "style"


@dataclass
class AIInsight:
    """AI洞察数据类"""
    category: SuggestionCategory
    title: str
    description: str
    confidence: ConfidenceLevel
    file_path: str
    line_start: int
    line_end: int
    suggestion: str
    code_example: str = ""
    references: List[str] = field(default_factory=list)
    impact: str = "medium"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category.value,
            "title": self.title,
            "description": self.description,
            "confidence": self.confidence.value,
            "file_path": self.file_path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "suggestion": self.suggestion,
            "code_example": self.code_example,
            "references": self.references,
            "impact": self.impact
        }


@dataclass
class CodePattern:
    """代码模式数据类"""
    pattern_type: str
    pattern_name: str
    description: str
    occurrences: List[Dict[str, Any]] = field(default_factory=list)
    quality_score: float = 0.0
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern_type": self.pattern_type,
            "pattern_name": self.pattern_name,
            "description": self.description,
            "occurrences": self.occurrences,
            "quality_score": self.quality_score,
            "recommendations": self.recommendations
        }


@dataclass
class AIAnalysisResult:
    """AI分析结果数据类"""
    file_path: str
    insights: List[AIInsight] = field(default_factory=list)
    patterns: List[CodePattern] = field(default_factory=list)
    quality_metrics: Dict[str, Any] = field(default_factory=dict)
    ai_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "insights": [i.to_dict() for i in self.insights],
            "patterns": [p.to_dict() for p in self.patterns],
            "quality_metrics": self.quality_metrics,
            "ai_score": self.ai_score
        }


@dataclass
class AIAnalysisReport:
    """AI分析报告数据类"""
    timestamp: str
    project_root: str
    mode: AnalysisMode
    total_files: int
    results: List[AIAnalysisResult]
    summary: Dict[str, Any] = field(default_factory=dict)
    top_recommendations: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "project_root": self.project_root,
            "mode": self.mode.value,
            "total_files": self.total_files,
            "summary": self.summary,
            "top_recommendations": self.top_recommendations,
            "results": [r.to_dict() for r in self.results]
        }


class PatternRecognizer:
    """代码模式识别器"""

    DESIGN_PATTERNS = {
        "singleton": {
            "indicators": ["__new__", "_instance", "getInstance"],
            "description": "单例模式实现"
        },
        "factory": {
            "indicators": ["create_", "build_", "Factory"],
            "description": "工厂模式实现"
        },
        "observer": {
            "indicators": ["subscribe", "notify", "observer", "listener"],
            "description": "观察者模式实现"
        },
        "strategy": {
            "indicators": ["strategy", "execute", "algorithm"],
            "description": "策略模式实现"
        },
        "decorator": {
            "indicators": ["@wrapper", "decorator", "wrap"],
            "description": "装饰器模式实现"
        },
        "repository": {
            "indicators": ["Repository", "find_", "save_", "delete_"],
            "description": "仓储模式实现"
        },
        "service": {
            "indicators": ["Service", "process_", "handle_"],
            "description": "服务层模式实现"
        }
    }

    ANTI_PATTERNS = {
        "god_object": {
            "indicators": ["too_many_methods", "too_many_attributes"],
            "description": "上帝对象反模式",
            "threshold_methods": 20,
            "threshold_attributes": 15
        },
        "spaghetti_code": {
            "indicators": ["deep_nesting", "high_complexity"],
            "description": "面条代码反模式",
            "threshold_nesting": 5,
            "threshold_complexity": 15
        },
        "copy_paste": {
            "indicators": ["duplicate_blocks"],
            "description": "复制粘贴编程",
            "threshold_similarity": 0.8
        },
        "magic_numbers": {
            "indicators": ["hardcoded_numbers"],
            "description": "魔法数字",
            "threshold_count": 3
        },
        "premature_optimization": {
            "indicators": ["complex_optimization", "unnecessary_caching"],
            "description": "过早优化"
        }
    }

    def __init__(self):
        self.detected_patterns: List[CodePattern] = []

    def recognize_patterns(self, tree: ast.AST, source: str, file_path: str) -> List[CodePattern]:
        """识别代码模式"""
        patterns = []

        patterns.extend(self._detect_design_patterns(tree, source, file_path))
        patterns.extend(self._detect_anti_patterns(tree, source, file_path))
        patterns.extend(self._detect_code_patterns(tree, source, file_path))

        return patterns

    def _detect_design_patterns(self, tree: ast.AST, source: str, file_path: str) -> List[CodePattern]:
        """检测设计模式"""
        patterns = []

        for pattern_name, config in self.DESIGN_PATTERNS.items():
            occurrences = []

            for indicator in config["indicators"]:
                if indicator in source:
                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef):
                            if indicator in node.name:
                                occurrences.append({
                                    "line": node.lineno,
                                    "name": node.name,
                                    "type": "method"
                                })
                        elif isinstance(node, ast.ClassDef):
                            if indicator in node.name:
                                occurrences.append({
                                    "line": node.lineno,
                                    "name": node.name,
                                    "type": "class"
                                })

            if occurrences:
                patterns.append(CodePattern(
                    pattern_type="design_pattern",
                    pattern_name=pattern_name,
                    description=config["description"],
                    occurrences=occurrences[:5],
                    quality_score=self._calculate_pattern_quality(pattern_name, occurrences),
                    recommendations=self._get_pattern_recommendations(pattern_name)
                ))

        return patterns

    def _detect_anti_patterns(self, tree: ast.AST, source: str, file_path: str) -> List[CodePattern]:
        """检测反模式"""
        patterns = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = [n for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
                attributes = set()

                for method in methods:
                    for child in ast.walk(method):
                        if isinstance(child, ast.Attribute):
                            if isinstance(child.value, ast.Name) and child.value.id == 'self':
                                attributes.add(child.attr)

                if len(methods) > 20 or len(attributes) > 15:
                    patterns.append(CodePattern(
                        pattern_type="anti_pattern",
                        pattern_name="god_object",
                        description=f"类 '{node.name}' 可能是上帝对象",
                        occurrences=[{
                            "line": node.lineno,
                            "name": node.name,
                            "methods": len(methods),
                            "attributes": len(attributes)
                        }],
                        quality_score=30.0,
                        recommendations=[
                            "将类拆分为多个小类",
                            "遵循单一职责原则",
                            "使用组合替代继承"
                        ]
                    ))

        complexity_issues = self._check_complexity(tree)
        if complexity_issues:
            patterns.append(CodePattern(
                pattern_type="anti_pattern",
                pattern_name="spaghetti_code",
                description="检测到高复杂度代码",
                occurrences=complexity_issues[:5],
                quality_score=40.0,
                recommendations=[
                    "简化复杂逻辑",
                    "提取方法",
                    "使用早返回减少嵌套"
                ]
            ))

        return patterns

    def _detect_code_patterns(self, tree: ast.AST, source: str, file_path: str) -> List[CodePattern]:
        """检测代码模式"""
        patterns = []

        error_handling = self._analyze_error_handling(tree)
        if error_handling["has_patterns"]:
            patterns.append(CodePattern(
                pattern_type="code_pattern",
                pattern_name="error_handling",
                description="错误处理模式",
                occurrences=error_handling["occurrences"],
                quality_score=error_handling["quality_score"],
                recommendations=error_handling["recommendations"]
            ))

        async_patterns = self._analyze_async_patterns(tree)
        if async_patterns["has_patterns"]:
            patterns.append(CodePattern(
                pattern_type="code_pattern",
                pattern_name="async_patterns",
                description="异步编程模式",
                occurrences=async_patterns["occurrences"],
                quality_score=async_patterns["quality_score"],
                recommendations=async_patterns["recommendations"]
            ))

        return patterns

    def _check_complexity(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """检查复杂度"""
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                complexity = self._calculate_function_complexity(node)
                if complexity > 15:
                    issues.append({
                        "line": node.lineno,
                        "name": node.name,
                        "complexity": complexity
                    })

        return issues

    def _calculate_function_complexity(self, node: ast.FunctionDef) -> int:
        """计算函数复杂度"""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        return complexity

    def _calculate_pattern_quality(self, pattern_name: str, occurrences: List) -> float:
        """计算模式质量分数"""
        base_scores = {
            "singleton": 70,
            "factory": 80,
            "observer": 75,
            "strategy": 80,
            "decorator": 85,
            "repository": 85,
            "service": 90
        }
        return base_scores.get(pattern_name, 70.0)

    def _get_pattern_recommendations(self, pattern_name: str) -> List[str]:
        """获取模式建议"""
        recommendations = {
            "singleton": ["确保线程安全", "考虑使用模块替代", "避免全局状态"],
            "factory": ["使用抽象工厂", "支持依赖注入", "考虑使用构建器"],
            "observer": ["使用弱引用避免内存泄漏", "考虑异步通知", "支持取消订阅"],
            "strategy": ["使用函数替代类", "支持运行时切换", "考虑默认策略"],
            "decorator": ["保持装饰器简单", "支持参数化", "保留函数元信息"],
            "repository": ["定义清晰接口", "支持批量操作", "考虑缓存"],
            "service": ["保持无状态", "支持依赖注入", "单一职责"]
        }
        return recommendations.get(pattern_name, [])

    def _analyze_error_handling(self, tree: ast.AST) -> Dict[str, Any]:
        """分析错误处理模式"""
        try_blocks = []
        bare_except = False
        generic_except = False

        for node in ast.walk(tree):
            if isinstance(node, ast.Try):
                for handler in node.handlers:
                    if handler.type is None:
                        bare_except = True
                    elif isinstance(handler.type, ast.Name) and handler.type.id == 'Exception':
                        generic_except = True
                    try_blocks.append({
                        "line": node.lineno,
                        "has_else": bool(node.orelse),
                        "has_finally": bool(node.finalbody)
                    })

        quality_score = 80.0
        recommendations = []

        if bare_except:
            quality_score -= 20
            recommendations.append("避免使用裸except子句")
        if generic_except:
            quality_score -= 10
            recommendations.append("捕获具体的异常类型")

        return {
            "has_patterns": len(try_blocks) > 0,
            "occurrences": try_blocks[:5],
            "quality_score": quality_score,
            "recommendations": recommendations
        }

    def _analyze_async_patterns(self, tree: ast.AST) -> Dict[str, Any]:
        """分析异步模式"""
        async_functions = []
        has_gather = False
        has_create_task = False

        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef):
                async_functions.append({
                    "line": node.lineno,
                    "name": node.name
                })
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr == 'gather':
                        has_gather = True
                    elif node.func.attr == 'create_task':
                        has_create_task = True

        quality_score = 85.0
        recommendations = []

        if len(async_functions) > 5 and not has_gather:
            recommendations.append("考虑使用asyncio.gather并发执行")

        return {
            "has_patterns": len(async_functions) > 0,
            "occurrences": async_functions[:5],
            "quality_score": quality_score,
            "recommendations": recommendations
        }


class AIInsightGenerator:
    """AI洞察生成器"""

    PERFORMANCE_PATTERNS = [
        {
            "pattern": r"for\s+\w+\s+in\s+\w+:\s*\n\s*for\s+\w+\s+in\s+\w+:",
            "title": "嵌套循环性能问题",
            "suggestion": "考虑使用字典或集合优化查找，或使用itertools优化迭代",
            "impact": "high"
        },
        {
            "pattern": r"\.append\(.*\)\s*\n\s*\.append\(",
            "title": "循环内追加操作",
            "suggestion": "考虑使用列表推导式或extend方法",
            "impact": "medium"
        },
        {
            "pattern": r"str\(.*\)\s*\+",
            "title": "字符串拼接性能问题",
            "suggestion": "对于大量拼接，考虑使用join或f-string",
            "impact": "low"
        }
    ]

    SECURITY_PATTERNS = [
        {
            "pattern": r"eval\s*\(",
            "title": "eval函数安全风险",
            "suggestion": "避免使用eval，考虑使用ast.literal_eval或json解析",
            "impact": "critical"
        },
        {
            "pattern": r"exec\s*\(",
            "title": "exec函数安全风险",
            "suggestion": "避免使用exec，重构代码以避免动态执行",
            "impact": "critical"
        },
        {
            "pattern": r"password\s*=\s*['\"]",
            "title": "硬编码密码",
            "suggestion": "使用环境变量或配置文件存储敏感信息",
            "impact": "critical"
        },
        {
            "pattern": r"sql\s*=\s*['\"].*\+",
            "title": "SQL注入风险",
            "suggestion": "使用参数化查询替代字符串拼接",
            "impact": "critical"
        }
    ]

    BEST_PRACTICE_PATTERNS = [
        {
            "pattern": r"print\s*\(",
            "title": "使用print进行日志记录",
            "suggestion": "使用logging模块替代print语句",
            "impact": "low"
        },
        {
            "pattern": r"except\s*:",
            "title": "裸except子句",
            "suggestion": "捕获具体的异常类型，避免隐藏错误",
            "impact": "medium"
        },
        {
            "pattern": r"import\s+\*",
            "title": "通配符导入",
            "suggestion": "显式导入需要的名称",
            "impact": "low"
        }
    ]

    def __init__(self):
        self.insights: List[AIInsight] = []

    def generate_insights(self, tree: ast.AST, source: str, file_path: str) -> List[AIInsight]:
        """生成AI洞察"""
        self.insights = []

        self.insights.extend(self._analyze_performance(tree, source, file_path))
        self.insights.extend(self._analyze_security(tree, source, file_path))
        self.insights.extend(self._analyze_best_practices(tree, source, file_path))
        self.insights.extend(self._analyze_maintainability(tree, source, file_path))
        self.insights.extend(self._analyze_architecture(tree, source, file_path))

        return self.insights

    def _analyze_performance(self, tree: ast.AST, source: str, file_path: str) -> List[AIInsight]:
        """分析性能问题"""
        insights = []
        lines = source.split('\n')

        for i, line in enumerate(lines, 1):
            for pattern_info in self.PERFORMANCE_PATTERNS:
                if re.search(pattern_info["pattern"], line):
                    insights.append(AIInsight(
                        category=SuggestionCategory.PERFORMANCE,
                        title=pattern_info["title"],
                        description=f"在 {file_path}:{i} 检测到潜在性能问题",
                        confidence=ConfidenceLevel.MEDIUM,
                        file_path=file_path,
                        line_start=i,
                        line_end=i,
                        suggestion=pattern_info["suggestion"],
                        impact=pattern_info["impact"]
                    ))

        for node in ast.walk(tree):
            if isinstance(node, ast.For):
                nested_loops = sum(1 for _ in ast.walk(node) if isinstance(_, ast.For))
                if nested_loops > 2:
                    insights.append(AIInsight(
                        category=SuggestionCategory.PERFORMANCE,
                        title="深度嵌套循环",
                        description=f"检测到 {nested_loops} 层嵌套循环，可能导致O(n^{nested_loops})复杂度",
                        confidence=ConfidenceLevel.HIGH,
                        file_path=file_path,
                        line_start=node.lineno,
                        line_end=getattr(node, 'end_lineno', node.lineno) or node.lineno,
                        suggestion="考虑使用算法优化或数据结构改进",
                        impact="high"
                    ))

        return insights

    def _analyze_security(self, tree: ast.AST, source: str, file_path: str) -> List[AIInsight]:
        """分析安全问题"""
        insights = []
        lines = source.split('\n')

        for i, line in enumerate(lines, 1):
            for pattern_info in self.SECURITY_PATTERNS:
                if re.search(pattern_info["pattern"], line, re.IGNORECASE):
                    insights.append(AIInsight(
                        category=SuggestionCategory.SECURITY,
                        title=pattern_info["title"],
                        description=f"在 {file_path}:{i} 检测到安全风险",
                        confidence=ConfidenceLevel.HIGH,
                        file_path=file_path,
                        line_start=i,
                        line_end=i,
                        suggestion=pattern_info["suggestion"],
                        impact=pattern_info["impact"]
                    ))

        return insights

    def _analyze_best_practices(self, tree: ast.AST, source: str, file_path: str) -> List[AIInsight]:
        """分析最佳实践"""
        insights = []
        lines = source.split('\n')

        for i, line in enumerate(lines, 1):
            for pattern_info in self.BEST_PRACTICE_PATTERNS:
                if re.search(pattern_info["pattern"], line):
                    insights.append(AIInsight(
                        category=SuggestionCategory.BEST_PRACTICE,
                        title=pattern_info["title"],
                        description=f"在 {file_path}:{i} 检测到可改进的实践",
                        confidence=ConfidenceLevel.MEDIUM,
                        file_path=file_path,
                        line_start=i,
                        line_end=i,
                        suggestion=pattern_info["suggestion"],
                        impact=pattern_info["impact"]
                    ))

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if not ast.get_docstring(node):
                    if not node.name.startswith('_'):
                        insights.append(AIInsight(
                            category=SuggestionCategory.BEST_PRACTICE,
                            title="缺少文档字符串",
                            description=f"函数 '{node.name}' 缺少文档字符串",
                            confidence=ConfidenceLevel.LOW,
                            file_path=file_path,
                            line_start=node.lineno,
                            line_end=node.lineno,
                            suggestion="为公共函数添加文档字符串",
                            impact="low"
                        ))

        return insights

    def _analyze_maintainability(self, tree: ast.AST, source: str, file_path: str) -> List[AIInsight]:
        """分析可维护性"""
        insights = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if hasattr(node, 'end_lineno') and node.end_lineno:
                    func_length = node.end_lineno - node.lineno
                    if func_length > 50:
                        insights.append(AIInsight(
                            category=SuggestionCategory.MAINTAINABILITY,
                            title="方法过长",
                            description=f"方法 '{node.name}' 有 {func_length} 行，建议拆分",
                            confidence=ConfidenceLevel.HIGH,
                            file_path=file_path,
                            line_start=node.lineno,
                            line_end=node.end_lineno,
                            suggestion="将方法拆分为多个小方法，每个方法只做一件事",
                            impact="medium"
                        ))

                params = len(node.args.args) + len(node.args.kwonlyargs)
                if params > 5:
                    insights.append(AIInsight(
                        category=SuggestionCategory.MAINTAINABILITY,
                        title="参数过多",
                        description=f"方法 '{node.name}' 有 {params} 个参数",
                        confidence=ConfidenceLevel.MEDIUM,
                        file_path=file_path,
                        line_start=node.lineno,
                        line_end=node.lineno,
                        suggestion="考虑使用参数对象或配置类",
                        impact="medium"
                    ))

        return insights

    def _analyze_architecture(self, tree: ast.AST, source: str, file_path: str) -> List[AIInsight]:
        """分析架构问题"""
        insights = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = [n for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
                public_methods = [m for m in methods if not m.name.startswith('_')]

                if len(public_methods) > 10:
                    insights.append(AIInsight(
                        category=SuggestionCategory.ARCHITECTURE,
                        title="类职责过多",
                        description=f"类 '{node.name}' 有 {len(public_methods)} 个公共方法",
                        confidence=ConfidenceLevel.MEDIUM,
                        file_path=file_path,
                        line_start=node.lineno,
                        line_end=getattr(node, 'end_lineno', node.lineno) or node.lineno,
                        suggestion="考虑将类拆分为多个小类，遵循单一职责原则",
                        impact="high"
                    ))

        return insights


class QualityMetricsCalculator:
    """质量指标计算器"""

    def calculate_metrics(self, tree: ast.AST, source: str) -> Dict[str, Any]:
        """计算质量指标"""
        lines = source.split('\n')

        metrics = {
            "lines_of_code": len(lines),
            "code_lines": sum(1 for line in lines if line.strip() and not line.strip().startswith('#')),
            "comment_lines": sum(1 for line in lines if line.strip().startswith('#')),
            "blank_lines": sum(1 for line in lines if not line.strip()),
            "functions": 0,
            "classes": 0,
            "imports": 0,
            "complexity": 0,
            "maintainability_index": 0.0,
            "cognitive_complexity": 0
        }

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                metrics["functions"] += 1
                metrics["complexity"] += self._calculate_complexity(node)
            elif isinstance(node, ast.ClassDef):
                metrics["classes"] += 1
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                metrics["imports"] += 1

        if metrics["lines_of_code"] > 0:
            comment_ratio = metrics["comment_lines"] / metrics["lines_of_code"]
            avg_complexity = metrics["complexity"] / max(metrics["functions"], 1)

            metrics["maintainability_index"] = max(0, min(100,
                171 - 5.2 * avg_complexity - 0.23 * metrics["complexity"] - 16.2 * metrics["lines_of_code"] / 1000
            ))

        metrics["cognitive_complexity"] = self._calculate_cognitive_complexity(tree)

        return metrics

    def _calculate_complexity(self, node: ast.AST) -> int:
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

    def _calculate_cognitive_complexity(self, tree: ast.AST) -> int:
        """计算认知复杂度"""
        complexity = 0

        def visit(node: ast.AST, nesting: int = 0):
            nonlocal complexity

            if isinstance(node, (ast.If, ast.For, ast.While)):
                complexity += nesting + 1
                for child in ast.iter_child_nodes(node):
                    visit(child, nesting + 1)
            elif isinstance(node, ast.Else):
                complexity += 1
                for child in ast.iter_child_nodes(node):
                    visit(child, nesting)
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
                for child in ast.iter_child_nodes(node):
                    visit(child, nesting)
            else:
                for child in ast.iter_child_nodes(node):
                    visit(child, nesting)

        visit(tree)
        return complexity


class AICodeAnalyzer:
    """AI代码分析器"""

    def __init__(self, project_root: Optional[Path] = None,
                 mode: AnalysisMode = AnalysisMode.STANDARD,
                 logger: Optional[logging.Logger] = None):
        self.project_root = project_root or get_path_config().SKILL_ROOT
        self.mode = mode
        self.logger = logger or logging.getLogger(__name__)
        self.results: List[AIAnalysisResult] = []

        self.pattern_recognizer = PatternRecognizer()
        self.insight_generator = AIInsightGenerator()
        self.metrics_calculator = QualityMetricsCalculator()

    def analyze_project(self) -> AIAnalysisReport:
        """分析整个项目"""
        self.logger.info(f"开始AI代码分析 (模式: {self.mode.value})...")

        files = self._collect_files()
        self.logger.info(f"找到 {len(files)} 个文件需要分析")

        for file_path in files:
            result = self._analyze_file(file_path)
            if result:
                self.results.append(result)

        summary = self._calculate_summary()
        top_recommendations = self._generate_top_recommendations()

        return AIAnalysisReport(
            timestamp=datetime.now().isoformat(),
            project_root=str(self.project_root),
            mode=self.mode,
            total_files=len(files),
            results=self.results,
            summary=summary,
            top_recommendations=top_recommendations
        )

    def _collect_files(self) -> List[Path]:
        """收集需要分析的文件"""
        files = []

        backend_app = self.project_root / "backend" / "app"
        if backend_app.exists():
            for py_file in backend_app.rglob("*.py"):
                if "__pycache__" not in str(py_file):
                    files.append(py_file)

        scripts_dir = self.project_root / "scripts"
        if scripts_dir.exists():
            for py_file in scripts_dir.rglob("*.py"):
                if "__pycache__" not in str(py_file):
                    files.append(py_file)

        return sorted(files)

    def _analyze_file(self, file_path: Path) -> Optional[AIAnalysisResult]:
        """分析单个文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()

            tree = ast.parse(source)

            patterns = self.pattern_recognizer.recognize_patterns(tree, source, str(file_path))
            insights = self.insight_generator.generate_insights(tree, source, str(file_path))
            metrics = self.metrics_calculator.calculate_metrics(tree, source)
            ai_score = self._calculate_ai_score(insights, patterns, metrics)

            return AIAnalysisResult(
                file_path=str(file_path),
                insights=insights,
                patterns=patterns,
                quality_metrics=metrics,
                ai_score=ai_score
            )

        except Exception as e:
            self.logger.error(f"分析文件失败 {file_path}: {e}")
            return None

    def _calculate_ai_score(self, insights: List[AIInsight], patterns: List[CodePattern],
                            metrics: Dict[str, Any]) -> float:
        """计算AI评分"""
        base_score = 100.0

        impact_penalties = {
            "critical": 25,
            "high": 15,
            "medium": 5,
            "low": 1
        }

        for insight in insights:
            penalty = impact_penalties.get(insight.impact, 5)
            base_score -= penalty

        for pattern in patterns:
            if pattern.pattern_type == "anti_pattern":
                base_score -= (100 - pattern.quality_score) * 0.5

        if metrics.get("maintainability_index", 100) < 50:
            base_score -= 10

        return max(0.0, min(100.0, base_score))

    def _calculate_summary(self) -> Dict[str, Any]:
        """计算摘要"""
        if not self.results:
            return {
                "total_insights": 0,
                "total_patterns": 0,
                "average_ai_score": 0.0,
                "insights_by_category": {},
                "insights_by_impact": {}
            }

        total_insights = sum(len(r.insights) for r in self.results)
        total_patterns = sum(len(r.patterns) for r in self.results)
        avg_score = sum(r.ai_score for r in self.results) / len(self.results)

        by_category: Dict[str, int] = defaultdict(int)
        by_impact: Dict[str, int] = defaultdict(int)

        for result in self.results:
            for insight in result.insights:
                by_category[insight.category.value] += 1
                by_impact[insight.impact] += 1

        return {
            "total_insights": total_insights,
            "total_patterns": total_patterns,
            "average_ai_score": round(avg_score, 1),
            "insights_by_category": dict(by_category),
            "insights_by_impact": dict(by_impact),
            "files_analyzed": len(self.results)
        }

    def _generate_top_recommendations(self) -> List[Dict[str, Any]]:
        """生成顶级建议"""
        all_insights = []
        for result in self.results:
            all_insights.extend(result.insights)

        impact_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        all_insights.sort(key=lambda x: impact_order.get(x.impact, 4))

        recommendations = []
        seen_titles = set()

        for insight in all_insights[:20]:
            if insight.title not in seen_titles:
                seen_titles.add(insight.title)
                recommendations.append({
                    "title": insight.title,
                    "category": insight.category.value,
                    "impact": insight.impact,
                    "confidence": insight.confidence.value,
                    "suggestion": insight.suggestion,
                    "file": insight.file_path,
                    "line": insight.line_start
                })

        return recommendations

    def print_report(self, report: AIAnalysisReport):
        """打印报告"""
        print("\n" + "=" * 80)
        print("AI代码分析报告")
        print("=" * 80)
        print(f"项目根目录: {report.project_root}")
        print(f"分析时间: {report.timestamp}")
        print(f"分析模式: {report.mode.value}")
        print(f"分析文件数: {report.total_files}")

        print("\n" + "-" * 80)
        print("摘要")
        print("-" * 80)
        summary = report.summary
        print(f"  总洞察数: {summary.get('total_insights', 0)}")
        print(f"  总模式数: {summary.get('total_patterns', 0)}")
        print(f"  平均AI评分: {summary.get('average_ai_score', 0):.1f}")

        print("\n  按类别统计:")
        for cat, count in summary.get("insights_by_category", {}).items():
            print(f"    {cat}: {count}")

        print("\n  按影响程度统计:")
        for impact, count in summary.get("insights_by_impact", {}).items():
            print(f"    {impact}: {count}")

        if report.top_recommendations:
            print("\n" + "-" * 80)
            print("顶级建议")
            print("-" * 80)
            for i, rec in enumerate(report.top_recommendations[:10], 1):
                impact_icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🔵"}.get(rec["impact"], "⚪")
                print(f"\n{i}. {impact_icon} [{rec['impact'].upper()}] {rec['title']}")
                print(f"   类别: {rec['category']}")
                print(f"   建议: {rec['suggestion']}")
                print(f"   位置: {Path(rec['file']).name}:{rec['line']}")

    def save_report(self, report: AIAnalysisReport, output_dir: Optional[Path] = None) -> Path:
        """保存报告"""
        if output_dir is None:
            output_dir = get_path_config().REPORTS_DIR
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = output_dir / f"ai_analysis_{timestamp}.json"

        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)

        latest_path = output_dir / "ai_analysis_latest.json"
        with open(latest_path, 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)

        self.logger.info(f"报告已保存: {report_path}")
        return report_path


def setup_logger(verbose: bool = False) -> logging.Logger:
    """配置日志记录器"""
    logger = logging.getLogger("AICodeAnalyzer")
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
        description="AI辅助代码分析器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python ai_code_analyzer.py
  python ai_code_analyzer.py --mode full
  python ai_code_analyzer.py --output json
        """
    )

    parser.add_argument(
        "--mode",
        choices=["quick", "standard", "full"],
        default="standard",
        help="分析模式 (默认: standard)"
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

    mode_map = {
        "quick": AnalysisMode.QUICK,
        "standard": AnalysisMode.STANDARD,
        "full": AnalysisMode.FULL
    }

    analyzer = AICodeAnalyzer(mode=mode_map[args.mode], logger=logger)
    report = analyzer.analyze_project()

    analyzer.print_report(report)

    report_path = analyzer.save_report(report)
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

    critical_count = report.summary.get("insights_by_impact", {}).get("critical", 0)
    high_count = report.summary.get("insights_by_impact", {}).get("high", 0)

    if critical_count > 0:
        return 2
    elif high_count > 5:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
