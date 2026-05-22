#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复策略库 - Fix Strategy Library

智能修复策略管理系统，包括：
- 策略分类管理（语法、导入、风格、安全）
- 策略匹配算法
- 策略效果评估
- 支持自定义策略扩展

使用示例:
    python fix_strategy_library.py --list-strategies
    python fix_strategy_library.py --evaluate --strategy syntax_fix
    python fix_strategy_library.py --match --file problematic.py
"""

from __future__ import annotations

import argparse
import ast
import json
import logging
import re
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Protocol, Tuple, Type, Union


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)


class StrategyCategory(Enum):
    SYNTAX = "syntax"
    IMPORT = "import"
    STYLE = "style"
    SECURITY = "security"
    PERFORMANCE = "performance"
    LOGIC = "logic"
    DEPRECATED = "deprecated"
    REFACTORING = "refactoring"
    CUSTOM = "custom"


class StrategyPriority(Enum):
    CRITICAL = 0
    HIGH = 1
    MEDIUM = 2
    LOW = 3
    INFO = 4


class MatchResult(Enum):
    FULL_MATCH = "full_match"
    PARTIAL_MATCH = "partial_match"
    NO_MATCH = "no_match"


class StrategyStatus(Enum):
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    EXPERIMENTAL = "experimental"
    DISABLED = "disabled"


class StrategySeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class StrategyMatch:
    strategy_id: str
    result: MatchResult
    confidence: float
    matched_patterns: List[str]
    issues_found: List[Dict[str, Any]]
    metadata: Dict[str, Any] = field(default_factory=dict)
    severity: StrategySeverity = StrategySeverity.MEDIUM
    execution_time_ms: float = 0.0
    fix_suggestions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "strategy_id": self.strategy_id,
            "result": self.result.value,
            "confidence": self.confidence,
            "matched_patterns": self.matched_patterns,
            "issues_found": self.issues_found,
            "metadata": self.metadata,
            "severity": self.severity.value,
            "execution_time_ms": self.execution_time_ms,
            "fix_suggestions": self.fix_suggestions
        }


@dataclass
class StrategyEffect:
    strategy_id: str
    total_applications: int
    successful_applications: int
    failed_applications: int
    average_execution_time: float
    success_rate: float
    last_applied: Optional[str]
    common_issues: List[str]
    effectiveness_score: float
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    false_positives: int = 0
    false_negatives: int = 0
    trend: str = "stable"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "strategy_id": self.strategy_id,
            "total_applications": self.total_applications,
            "successful_applications": self.successful_applications,
            "failed_applications": self.failed_applications,
            "average_execution_time": self.average_execution_time,
            "success_rate": self.success_rate,
            "last_applied": self.last_applied,
            "common_issues": self.common_issues,
            "effectiveness_score": self.effectiveness_score,
            "precision": self.precision,
            "recall": self.recall,
            "f1_score": self.f1_score,
            "false_positives": self.false_positives,
            "false_negatives": self.false_negatives,
            "trend": self.trend
        }


@dataclass
class StrategyDefinition:
    strategy_id: str
    name: str
    description: str
    category: StrategyCategory
    priority: StrategyPriority
    status: StrategyStatus
    patterns: List[str]
    fix_template: str
    preconditions: List[str]
    postconditions: List[str]
    tags: List[str]
    version: str
    author: str
    created_at: str
    updated_at: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "strategy_id": self.strategy_id,
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "priority": self.priority.value,
            "status": self.status.value,
            "patterns": self.patterns,
            "fix_template": self.fix_template,
            "preconditions": self.preconditions,
            "postconditions": self.postconditions,
            "tags": self.tags,
            "version": self.version,
            "author": self.author,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }


class StrategyEvaluator(Protocol):
    def evaluate(self, strategy_id: str, results: List[Dict[str, Any]]) -> StrategyEffect:
        ...


class PatternMatcher:
    """策略模式匹配器"""

    def __init__(self):
        self._compiled_patterns: Dict[str, re.Pattern] = {}
        self._pattern_cache: Dict[str, List[re.Match]] = {}
        self._similarity_threshold: float = 0.7

    def compile_pattern(self, pattern: str) -> re.Pattern:
        if pattern not in self._compiled_patterns:
            try:
                self._compiled_patterns[pattern] = re.compile(pattern, re.MULTILINE)
            except re.error as e:
                logger.error(f"无效的正则表达式模式 '{pattern}': {e}")
                raise ValueError(f"无效的正则表达式模式: {pattern}") from e
        return self._compiled_patterns[pattern]

    def match_text(self, text: str, pattern: str) -> Tuple[bool, List[re.Match]]:
        compiled = self.compile_pattern(pattern)
        matches = list(compiled.finditer(text))
        return len(matches) > 0, matches

    def match_ast(self, tree: ast.AST, pattern_type: str, **kwargs) -> List[ast.AST]:
        matches = []
        for node in ast.walk(tree):
            if self._match_ast_node(node, pattern_type, **kwargs):
                matches.append(node)
        return matches

    def _match_ast_node(self, node: ast.AST, pattern_type: str, **kwargs) -> bool:
        type_map = {
            "function": (ast.FunctionDef, ast.AsyncFunctionDef),
            "class": ast.ClassDef,
            "import": (ast.Import, ast.ImportFrom),
            "call": ast.Call,
            "assign": ast.Assign,
            "for": ast.For,
            "while": ast.While,
            "if": ast.If,
            "try": ast.Try,
            "with": ast.With,
            "return": ast.Return,
            "yield": ast.Yield,
            "await": ast.Await,
            "binary_op": ast.BinOp,
            "compare": ast.Compare,
            "subscript": ast.Subscript,
            "attribute": ast.Attribute,
        }

        expected_type = type_map.get(pattern_type)
        if expected_type is None:
            return False

        if not isinstance(node, expected_type):
            return False

        for key, value in kwargs.items():
            if not hasattr(node, key):
                return False
            if getattr(node, key) != value:
                return False

        return True

    def match_fuzzy(self, text: str, patterns: List[str], threshold: float = None) -> List[Tuple[str, float]]:
        threshold = threshold or self._similarity_threshold
        results = []

        for pattern in patterns:
            similarity = self._calculate_similarity(text, pattern)
            if similarity >= threshold:
                results.append((pattern, similarity))

        return sorted(results, key=lambda x: x[1], reverse=True)

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        from difflib import SequenceMatcher
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

    def match_context(
        self,
        content: str,
        patterns: List[str],
        context_window: int = 3
    ) -> List[Dict[str, Any]]:
        results = []
        lines = content.split('\n')

        for pattern in patterns:
            compiled = self.compile_pattern(pattern)
            for match in compiled.finditer(content):
                line_num = content[:match.start()].count('\n') + 1
                start_line = max(0, line_num - context_window - 1)
                end_line = min(len(lines), line_num + context_window)

                context_lines = lines[start_line:end_line]
                context = '\n'.join(context_lines)

                results.append({
                    'pattern': pattern,
                    'match': match.group(),
                    'line': line_num,
                    'context': context,
                    'start_line': start_line + 1,
                    'end_line': end_line
                })

        return results

    def match_multi_pattern(
        self,
        content: str,
        patterns: List[str],
        mode: str = "any"
    ) -> Tuple[bool, Dict[str, List[re.Match]]]:
        all_matches: Dict[str, List[re.Match]] = {}
        matched_count = 0

        for pattern in patterns:
            is_match, matches = self.match_text(content, pattern)
            all_matches[pattern] = matches
            if is_match:
                matched_count += 1

        if mode == "any":
            return matched_count > 0, all_matches
        elif mode == "all":
            return matched_count == len(patterns), all_matches
        elif mode == "majority":
            return matched_count >= len(patterns) / 2, all_matches
        else:
            return matched_count > 0, all_matches

    def clear_cache(self) -> None:
        self._pattern_cache.clear()


class BaseStrategy(ABC):
    """策略基类"""

    def __init__(
        self,
        strategy_id: str,
        name: str,
        description: str,
        category: StrategyCategory,
        priority: StrategyPriority = StrategyPriority.MEDIUM
    ):
        self.strategy_id = strategy_id
        self.name = name
        self.description = description
        self.category = category
        self.priority = priority
        self.status = StrategyStatus.ACTIVE
        self.patterns: List[str] = []
        self.matcher = PatternMatcher()
        self._application_count = 0
        self._success_count = 0
        self._total_time = 0.0
        self._last_applied: Optional[datetime] = None
        self._issues_history: List[str] = []
        self._true_positives: int = 0
        self._false_positives: int = 0
        self._false_negatives: int = 0
        self._execution_times: List[float] = []
        self._tags: List[str] = []
        self._dependencies: List[str] = []
        self._conflicts: List[str] = []

    @abstractmethod
    def can_apply(self, content: str, file_path: Path, **context) -> StrategyMatch:
        """检查策略是否适用于给定内容"""
        pass

    @abstractmethod
    def apply(self, content: str, issues: List[Dict[str, Any]], **context) -> Tuple[str, List[Dict[str, Any]]]:
        """应用策略进行修复"""
        pass

    def get_definition(self) -> StrategyDefinition:
        return StrategyDefinition(
            strategy_id=self.strategy_id,
            name=self.name,
            description=self.description,
            category=self.category,
            priority=self.priority,
            status=self.status,
            patterns=self.patterns,
            fix_template="",
            preconditions=[],
            postconditions=[],
            tags=self._tags,
            version="1.0.0",
            author="system",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )

    def get_effect(self) -> StrategyEffect:
        total = self._application_count
        success_rate = self._success_count / total if total > 0 else 0.0
        avg_time = self._total_time / total if total > 0 else 0.0

        precision = self._true_positives / (self._true_positives + self._false_positives) if (self._true_positives + self._false_positives) > 0 else 0.0
        recall = self._true_positives / (self._true_positives + self._false_negatives) if (self._true_positives + self._false_negatives) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

        trend = self._calculate_trend()

        return StrategyEffect(
            strategy_id=self.strategy_id,
            total_applications=total,
            successful_applications=self._success_count,
            failed_applications=total - self._success_count,
            average_execution_time=avg_time,
            success_rate=success_rate,
            last_applied=self._last_applied.isoformat() if self._last_applied else None,
            common_issues=self._issues_history[-10:],
            effectiveness_score=success_rate * (1 - avg_time / 1000),
            precision=precision,
            recall=recall,
            f1_score=f1,
            false_positives=self._false_positives,
            false_negatives=self._false_negatives,
            trend=trend
        )

    def _calculate_trend(self) -> str:
        if len(self._execution_times) < 5:
            return "insufficient_data"

        recent_times = self._execution_times[-5:]
        earlier_times = self._execution_times[:-5] if len(self._execution_times) > 5 else self._execution_times

        recent_avg = sum(recent_times) / len(recent_times)
        earlier_avg = sum(earlier_times) / len(earlier_times) if earlier_times else recent_avg

        if recent_avg < earlier_avg * 0.9:
            return "improving"
        elif recent_avg > earlier_avg * 1.1:
            return "degrading"
        else:
            return "stable"

    def record_application(self, success: bool, execution_time: float, issue: str = ""):
        self._application_count += 1
        self._total_time += execution_time
        self._execution_times.append(execution_time)
        if success:
            self._success_count += 1
            self._true_positives += 1
        else:
            self._false_positives += 1
        self._last_applied = datetime.now()
        if issue:
            self._issues_history.append(issue)

    def record_false_negative(self):
        self._false_negatives += 1

    def add_tag(self, tag: str) -> None:
        if tag not in self._tags:
            self._tags.append(tag)

    def add_dependency(self, strategy_id: str) -> None:
        if strategy_id not in self._dependencies:
            self._dependencies.append(strategy_id)

    def add_conflict(self, strategy_id: str) -> None:
        if strategy_id not in self._conflicts:
            self._conflicts.append(strategy_id)

    def get_dependencies(self) -> List[str]:
        return self._dependencies.copy()

    def get_conflicts(self) -> List[str]:
        return self._conflicts.copy()

    def is_compatible_with(self, other_strategy: 'BaseStrategy') -> bool:
        return other_strategy.strategy_id not in self._conflicts

    def validate_preconditions(self, content: str, **context) -> Tuple[bool, List[str]]:
        errors = []
        return len(errors) == 0, errors

    def validate_postconditions(self, original_content: str, fixed_content: str, **context) -> Tuple[bool, List[str]]:
        errors = []
        try:
            ast.parse(fixed_content)
        except SyntaxError as e:
            errors.append(f"修复后代码存在语法错误: {e}")
        return len(errors) == 0, errors


class SyntaxFixStrategy(BaseStrategy):
    """语法修复策略"""

    SYNTAX_PATTERNS = {
        "missing_colon": r'^\s*(if|elif|else|for|while|def|class|try|except|finally|with)\b[^:]*$',
        "unmatched_paren": r'\([^)]*$',
        "unmatched_bracket": r'\[[^\]]*$',
        "unmatched_brace": r'\{[^}]*$',
        "invalid_indentation": r'^[ \t]+[^\s]',
    }

    def __init__(self):
        super().__init__(
            strategy_id="syntax_fix_001",
            name="语法错误修复策略",
            description="检测并修复常见的Python语法错误，包括缺失冒号、括号不匹配、缩进错误等",
            category=StrategyCategory.SYNTAX,
            priority=StrategyPriority.CRITICAL
        )
        self.patterns = list(self.SYNTAX_PATTERNS.values())

    def can_apply(self, content: str, file_path: Path, **context) -> StrategyMatch:
        issues: List[Dict[str, Any]] = []
        matched_patterns: List[str] = []
        total_confidence = 0.0

        try:
            ast.parse(content)
        except SyntaxError as e:
            issues.append({
                "type": "syntax_error",
                "line": e.lineno or 1,
                "message": e.msg,
                "offset": e.offset
            })
            total_confidence += 0.5

        lines = content.split('\n')
        for pattern_name, pattern in self.SYNTAX_PATTERNS.items():
            is_match, matches = self.matcher.match_text(content, pattern)
            if is_match:
                matched_patterns.append(pattern_name)
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    issues.append({
                        "type": pattern_name,
                        "line": line_num,
                        "message": f"检测到语法问题: {pattern_name}",
                        "match_text": match.group()
                    })
                total_confidence += 0.1 * len(matches)

        confidence = min(total_confidence, 1.0)
        result = MatchResult.FULL_MATCH if issues else MatchResult.NO_MATCH

        return StrategyMatch(
            strategy_id=self.strategy_id,
            result=result,
            confidence=confidence,
            matched_patterns=matched_patterns,
            issues_found=issues
        )

    def apply(self, content: str, issues: List[Dict[str, Any]], **context) -> Tuple[str, List[Dict[str, Any]]]:
        import time
        start_time = time.time()

        lines = content.split('\n')
        fixes: List[Dict[str, Any]] = []

        for issue in issues:
            if issue["type"] == "missing_colon":
                line_idx = issue["line"] - 1
                if 0 <= line_idx < len(lines):
                    original = lines[line_idx]
                    if not original.rstrip().endswith(':'):
                        lines[line_idx] = original.rstrip() + ':'
                        fixes.append({
                            "type": "added_colon",
                            "line": issue["line"],
                            "original": original,
                            "fixed": lines[line_idx]
                        })

        result = '\n'.join(lines)
        execution_time = (time.time() - start_time) * 1000
        self.record_application(len(fixes) > 0, execution_time)

        return result, fixes


class ImportFixStrategy(BaseStrategy):
    """导入修复策略"""

    IMPORT_PATTERNS = {
        "unused_import": r'^import\s+(\w+)|^from\s+([\w.]+)\s+import\s+(\w+)',
        "missing_import": r'\b([A-Z][a-zA-Z]+)\b',
        "import_order": r'^(?!import|from|#|"""|\'\'\'|\n)',
    }

    STANDARD_LIBRARY = {
        'os', 'sys', 're', 'json', 'datetime', 'pathlib', 'collections',
        'typing', 'logging', 'argparse', 'subprocess', 'threading',
        'multiprocessing', 'asyncio', 'functools', 'itertools', 'abc'
    }

    def __init__(self):
        super().__init__(
            strategy_id="import_fix_001",
            name="导入错误修复策略",
            description="检测并修复导入相关问题，包括未使用的导入、缺失的导入、导入顺序等",
            category=StrategyCategory.IMPORT,
            priority=StrategyPriority.HIGH
        )
        self.patterns = list(self.IMPORT_PATTERNS.values())

    def can_apply(self, content: str, file_path: Path, **context) -> StrategyMatch:
        issues: List[Dict[str, Any]] = []
        matched_patterns: List[str] = []

        try:
            tree = ast.parse(content)
        except SyntaxError:
            return StrategyMatch(
                strategy_id=self.strategy_id,
                result=MatchResult.NO_MATCH,
                confidence=0.0,
                matched_patterns=[],
                issues_found=[]
            )

        imports: Dict[str, Tuple[int, str]] = {}
        used_names: set = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name.split('.')[0]
                    imports[name] = (node.lineno, alias.name)
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    module = node.module or ""
                    imports[name] = (node.lineno, f"{module}.{alias.name}" if module else alias.name)
            elif isinstance(node, ast.Name):
                if isinstance(node.ctx, ast.Load):
                    used_names.add(node.id)

        for name, (lineno, original) in imports.items():
            if name not in used_names and name not in self.STANDARD_LIBRARY:
                matched_patterns.append("unused_import")
                issues.append({
                    "type": "unused_import",
                    "line": lineno,
                    "message": f"未使用的导入: {original}",
                    "import_name": original
                })

        confidence = min(len(issues) * 0.2, 1.0)
        result = MatchResult.FULL_MATCH if issues else MatchResult.NO_MATCH

        return StrategyMatch(
            strategy_id=self.strategy_id,
            result=result,
            confidence=confidence,
            matched_patterns=list(set(matched_patterns)),
            issues_found=issues
        )

    def apply(self, content: str, issues: List[Dict[str, Any]], **context) -> Tuple[str, List[Dict[str, Any]]]:
        import time
        start_time = time.time()

        lines = content.split('\n')
        fixes: List[Dict[str, Any]] = []
        lines_to_remove: set = set()

        for issue in issues:
            if issue["type"] == "unused_import":
                line_idx = issue["line"] - 1
                if 0 <= line_idx < len(lines):
                    lines_to_remove.add(line_idx)
                    fixes.append({
                        "type": "removed_unused_import",
                        "line": issue["line"],
                        "original": lines[line_idx],
                        "fixed": ""
                    })

        if lines_to_remove:
            new_lines = [line for i, line in enumerate(lines) if i not in lines_to_remove]
            result = '\n'.join(new_lines)
        else:
            result = content

        execution_time = (time.time() - start_time) * 1000
        self.record_application(len(fixes) > 0, execution_time)

        return result, fixes


class StyleFixStrategy(BaseStrategy):
    """风格修复策略"""

    STYLE_PATTERNS = {
        "trailing_whitespace": r'[ \t]+$',
        "multiple_spaces": r'  +',
        "missing_final_newline": r'[^\n]$',
        "long_line": r'^.{121,}$',
    }

    def __init__(self):
        super().__init__(
            strategy_id="style_fix_001",
            name="代码风格修复策略",
            description="检测并修复代码风格问题，包括行尾空白、过长行、缺失换行等",
            category=StrategyCategory.STYLE,
            priority=StrategyPriority.LOW
        )
        self.patterns = list(self.STYLE_PATTERNS.values())

    def can_apply(self, content: str, file_path: Path, **context) -> StrategyMatch:
        issues: List[Dict[str, Any]] = []
        matched_patterns: List[str] = []

        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if line != line.rstrip():
                matched_patterns.append("trailing_whitespace")
                issues.append({
                    "type": "trailing_whitespace",
                    "line": i,
                    "message": "行尾有多余空白字符"
                })

            if len(line) > 120:
                matched_patterns.append("long_line")
                issues.append({
                    "type": "long_line",
                    "line": i,
                    "message": f"行长度超过120字符: {len(line)}字符"
                })

        if content and not content.endswith('\n'):
            matched_patterns.append("missing_final_newline")
            issues.append({
                "type": "missing_final_newline",
                "line": len(lines),
                "message": "文件末尾缺少换行符"
            })

        confidence = min(len(issues) * 0.1, 1.0)
        result = MatchResult.FULL_MATCH if issues else MatchResult.NO_MATCH

        return StrategyMatch(
            strategy_id=self.strategy_id,
            result=result,
            confidence=confidence,
            matched_patterns=list(set(matched_patterns)),
            issues_found=issues
        )

    def apply(self, content: str, issues: List[Dict[str, Any]], **context) -> Tuple[str, List[Dict[str, Any]]]:
        import time
        start_time = time.time()

        lines = content.split('\n')
        fixes: List[Dict[str, Any]] = []

        for issue in issues:
            if issue["type"] == "trailing_whitespace":
                line_idx = issue["line"] - 1
                if 0 <= line_idx < len(lines):
                    original = lines[line_idx]
                    lines[line_idx] = original.rstrip()
                    if original != lines[line_idx]:
                        fixes.append({
                            "type": "removed_trailing_whitespace",
                            "line": issue["line"],
                            "original": original,
                            "fixed": lines[line_idx]
                        })

        result = '\n'.join(lines)
        if content and not content.endswith('\n'):
            result += '\n'
            fixes.append({
                "type": "added_final_newline",
                "line": len(lines),
                "original": "",
                "fixed": "\\n"
            })

        execution_time = (time.time() - start_time) * 1000
        self.record_application(len(fixes) > 0, execution_time)

        return result, fixes


class SecurityFixStrategy(BaseStrategy):
    """安全修复策略"""

    SECURITY_PATTERNS = {
        "hardcoded_password": r'(?i)(password|passwd|pwd)\s*=\s*[\'"][^\'"]+[\'"]',
        "hardcoded_secret": r'(?i)(secret|api_key|apikey|token)\s*=\s*[\'"][^\'"]+[\'"]',
        "sql_injection_risk": r'execute\s*\(\s*[\'"].*\+.*[\'"]',
        "eval_usage": r'\beval\s*\(',
        "exec_usage": r'\bexec\s*\(',
        "pickle_usage": r'pickle\.loads?\s*\(',
        "subprocess_shell": r'subprocess\..*shell\s*=\s*True',
    }

    def __init__(self):
        super().__init__(
            strategy_id="security_fix_001",
            name="安全问题修复策略",
            description="检测并修复潜在的安全问题，包括硬编码密码、SQL注入风险、危险函数使用等",
            category=StrategyCategory.SECURITY,
            priority=StrategyPriority.CRITICAL
        )
        self.patterns = list(self.SECURITY_PATTERNS.values())

    def can_apply(self, content: str, file_path: Path, **context) -> StrategyMatch:
        issues: List[Dict[str, Any]] = []
        matched_patterns: List[str] = []

        for pattern_name, pattern in self.SECURITY_PATTERNS.items():
            is_match, matches = self.matcher.match_text(content, pattern)
            if is_match:
                matched_patterns.append(pattern_name)
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    issues.append({
                        "type": pattern_name,
                        "line": line_num,
                        "message": f"检测到安全问题: {pattern_name}",
                        "match_text": match.group(),
                        "severity": "high"
                    })

        confidence = min(len(issues) * 0.3, 1.0)
        result = MatchResult.FULL_MATCH if issues else MatchResult.NO_MATCH

        return StrategyMatch(
            strategy_id=self.strategy_id,
            result=result,
            confidence=confidence,
            matched_patterns=list(set(matched_patterns)),
            issues_found=issues
        )

    def apply(self, content: str, issues: List[Dict[str, Any]], **context) -> Tuple[str, List[Dict[str, Any]]]:
        import time
        start_time = time.time()

        lines = content.split('\n')
        fixes: List[Dict[str, Any]] = []

        for issue in issues:
            fixes.append({
                "type": "security_warning",
                "line": issue["line"],
                "original": lines[issue["line"] - 1] if issue["line"] <= len(lines) else "",
                "message": f"安全问题需要手动审查: {issue['type']}",
                "recommendation": self._get_recommendation(issue["type"])
            })

        execution_time = (time.time() - start_time) * 1000
        self.record_application(False, execution_time, "Security issues require manual review")

        return content, fixes

    def _get_recommendation(self, issue_type: str) -> str:
        recommendations = {
            "hardcoded_password": "使用环境变量或配置文件存储密码",
            "hardcoded_secret": "使用环境变量或密钥管理服务",
            "sql_injection_risk": "使用参数化查询代替字符串拼接",
            "eval_usage": "避免使用eval，考虑更安全的替代方案",
            "exec_usage": "避免使用exec，考虑更安全的替代方案",
            "pickle_usage": "避免反序列化不受信任的数据",
            "subprocess_shell": "避免使用shell=True，使用列表参数"
        }
        return recommendations.get(issue_type, "需要手动审查")


class StrategyLibrary:
    """策略库管理器"""

    def __init__(self):
        self._strategies: Dict[str, BaseStrategy] = {}
        self._categories: Dict[StrategyCategory, List[str]] = {cat: [] for cat in StrategyCategory}
        self._matcher = PatternMatcher()
        self._effect_history: Dict[str, List[StrategyEffect]] = {}
        self._custom_strategy_factories: Dict[str, Callable[..., BaseStrategy]] = {}
        self._strategy_graph: Dict[str, List[str]] = {}
        self._execution_order: List[str] = []
        self._performance_threshold: float = 0.5
        self._strategy_groups: Dict[str, List[str]] = {}
        self._strategy_versions: Dict[str, List[str]] = {}
        self._active_version: Dict[str, str] = {}

        self._register_builtin_strategies()

    def _register_builtin_strategies(self):
        builtin_strategies = [
            SyntaxFixStrategy(),
            ImportFixStrategy(),
            StyleFixStrategy(),
            SecurityFixStrategy()
        ]

        for strategy in builtin_strategies:
            self.register_strategy(strategy)

    def register_strategy(self, strategy: BaseStrategy) -> bool:
        if strategy.strategy_id in self._strategies:
            logger.warning(f"策略ID已存在: {strategy.strategy_id}")
            return False

        self._strategies[strategy.strategy_id] = strategy
        self._categories[strategy.category].append(strategy.strategy_id)
        self._update_strategy_graph(strategy)
        self._init_strategy_version(strategy)
        logger.info(f"已注册策略: {strategy.name} ({strategy.strategy_id})")
        return True

    def _init_strategy_version(self, strategy: BaseStrategy) -> None:
        if strategy.strategy_id not in self._strategy_versions:
            self._strategy_versions[strategy.strategy_id] = ['1.0.0']
            self._active_version[strategy.strategy_id] = '1.0.0'

    def _update_strategy_graph(self, strategy: BaseStrategy) -> None:
        self._strategy_graph[strategy.strategy_id] = strategy.get_dependencies()

    def unregister_strategy(self, strategy_id: str) -> bool:
        if strategy_id not in self._strategies:
            logger.warning(f"策略不存在: {strategy_id}")
            return False

        strategy = self._strategies[strategy_id]
        self._categories[strategy.category].remove(strategy_id)
        del self._strategies[strategy_id]
        if strategy_id in self._strategy_graph:
            del self._strategy_graph[strategy_id]
        if strategy_id in self._strategy_versions:
            del self._strategy_versions[strategy_id]
        if strategy_id in self._active_version:
            del self._active_version[strategy_id]
        logger.info(f"已注销策略: {strategy_id}")
        return True

    def get_strategy(self, strategy_id: str) -> Optional[BaseStrategy]:
        return self._strategies.get(strategy_id)

    def get_strategies_by_category(self, category: StrategyCategory) -> List[BaseStrategy]:
        return [self._strategies[sid] for sid in self._categories[category] if sid in self._strategies]

    def get_strategies_by_tag(self, tag: str) -> List[BaseStrategy]:
        return [s for s in self.get_all_strategies() if tag in s._tags]

    def get_all_strategies(self) -> List[BaseStrategy]:
        return list(self._strategies.values())

    def get_strategies_by_priority(self, priority: StrategyPriority) -> List[BaseStrategy]:
        return [s for s in self.get_all_strategies() if s.priority == priority]

    def create_strategy_group(self, group_name: str, strategy_ids: List[str]) -> bool:
        for sid in strategy_ids:
            if sid not in self._strategies:
                logger.warning(f"策略不存在: {sid}")
                return False

        self._strategy_groups[group_name] = strategy_ids
        logger.info(f"已创建策略组: {group_name}")
        return True

    def get_strategy_group(self, group_name: str) -> List[BaseStrategy]:
        if group_name not in self._strategy_groups:
            return []
        return [self._strategies[sid] for sid in self._strategy_groups[group_name] if sid in self._strategies]

    def list_strategy_groups(self) -> List[str]:
        return list(self._strategy_groups.keys())

    def delete_strategy_group(self, group_name: str) -> bool:
        if group_name in self._strategy_groups:
            del self._strategy_groups[group_name]
            return True
        return False

    def update_strategy_version(self, strategy_id: str, new_version: str) -> bool:
        if strategy_id not in self._strategies:
            return False

        if new_version not in self._strategy_versions[strategy_id]:
            self._strategy_versions[strategy_id].append(new_version)

        self._active_version[strategy_id] = new_version
        logger.info(f"策略 {strategy_id} 版本更新为 {new_version}")
        return True

    def get_strategy_versions(self, strategy_id: str) -> List[str]:
        return self._strategy_versions.get(strategy_id, [])

    def get_active_version(self, strategy_id: str) -> Optional[str]:
        return self._active_version.get(strategy_id)

    def rollback_strategy_version(self, strategy_id: str) -> bool:
        if strategy_id not in self._strategy_versions:
            return False

        versions = self._strategy_versions[strategy_id]
        if len(versions) <= 1:
            return False

        current_idx = versions.index(self._active_version[strategy_id])
        if current_idx > 0:
            self._active_version[strategy_id] = versions[current_idx - 1]
            logger.info(f"策略 {strategy_id} 回滚到版本 {self._active_version[strategy_id]}")
            return True
        return False

    def match_strategies(
        self,
        content: str,
        file_path: Path,
        categories: Optional[List[StrategyCategory]] = None,
        min_confidence: float = 0.0
    ) -> List[StrategyMatch]:
        matches: List[StrategyMatch] = []

        strategies_to_check = []
        if categories:
            for cat in categories:
                strategies_to_check.extend(self.get_strategies_by_category(cat))
        else:
            strategies_to_check = self.get_all_strategies()

        sorted_strategies = sorted(strategies_to_check, key=lambda s: s.priority.value)

        for strategy in sorted_strategies:
            try:
                match = strategy.can_apply(content, file_path)
                if match.result != MatchResult.NO_MATCH and match.confidence >= min_confidence:
                    matches.append(match)
            except Exception as e:
                logger.error(f"策略 {strategy.strategy_id} 匹配失败: {e}")

        return matches

    def match_with_context(
        self,
        content: str,
        file_path: Path,
        context_window: int = 3
    ) -> List[Dict[str, Any]]:
        results = []
        matches = self.match_strategies(content, file_path)

        for match in matches:
            strategy = self.get_strategy(match.strategy_id)
            if strategy:
                context_matches = self._matcher.match_context(
                    content,
                    strategy.patterns,
                    context_window
                )
                results.append({
                    'match': match,
                    'contexts': context_matches
                })

        return results

    def apply_strategy(
        self,
        strategy_id: str,
        content: str,
        issues: List[Dict[str, Any]],
        **context
    ) -> Tuple[str, List[Dict[str, Any]]]:
        strategy = self.get_strategy(strategy_id)
        if not strategy:
            raise ValueError(f"策略不存在: {strategy_id}")

        valid, errors = strategy.validate_preconditions(content, **context)
        if not valid:
            raise ValueError(f"前置条件不满足: {errors}")

        result_content, fixes = strategy.apply(content, issues, **context)

        valid, errors = strategy.validate_postconditions(content, result_content, **context)
        if not valid:
            logger.warning(f"后置条件验证失败: {errors}")

        return result_content, fixes

    def apply_best_strategies(
        self,
        content: str,
        file_path: Path,
        max_strategies: int = 5,
        min_confidence: float = 0.3
    ) -> Tuple[str, List[Dict[str, Any]]]:
        matches = self.match_strategies(content, file_path, min_confidence=min_confidence)
        matches.sort(key=lambda m: (m.confidence, -len(m.issues_found)), reverse=True)

        top_matches = matches[:max_strategies]
        all_fixes: List[Dict[str, Any]] = []
        current_content = content

        for match in top_matches:
            try:
                current_content, fixes = self.apply_strategy(
                    match.strategy_id,
                    current_content,
                    match.issues_found
                )
                all_fixes.extend(fixes)
            except Exception as e:
                logger.error(f"应用策略 {match.strategy_id} 失败: {e}")

        return current_content, all_fixes

    def evaluate_strategy(self, strategy_id: str) -> Optional[StrategyEffect]:
        strategy = self.get_strategy(strategy_id)
        if not strategy:
            return None

        effect = strategy.get_effect()

        if strategy_id not in self._effect_history:
            self._effect_history[strategy_id] = []
        self._effect_history[strategy_id].append(effect)

        return effect

    def evaluate_all_strategies(self) -> Dict[str, StrategyEffect]:
        return {
            sid: self.evaluate_strategy(sid)
            for sid in self._strategies
        }

    def get_strategy_performance_report(self) -> Dict[str, Any]:
        effects = self.evaluate_all_strategies()

        total_applications = sum(e.total_applications for e in effects.values() if e)
        total_successes = sum(e.successful_applications for e in effects.values() if e)

        avg_success_rate = sum(e.success_rate for e in effects.values() if e) / len(effects) if effects else 0
        avg_f1_score = sum(e.f1_score for e in effects.values() if e) / len(effects) if effects else 0

        improving = sum(1 for e in effects.values() if e and e.trend == "improving")
        degrading = sum(1 for e in effects.values() if e and e.trend == "degrading")
        stable = sum(1 for e in effects.values() if e and e.trend == "stable")

        return {
            "total_strategies": len(self._strategies),
            "total_applications": total_applications,
            "total_successes": total_successes,
            "overall_success_rate": total_successes / total_applications if total_applications > 0 else 0,
            "average_success_rate": avg_success_rate,
            "average_f1_score": avg_f1_score,
            "trend_distribution": {
                "improving": improving,
                "degrading": degrading,
                "stable": stable
            },
            "top_performers": self._get_top_performers(effects, 5),
            "underperformers": self._get_underperformers(effects, 5)
        }

    def _get_top_performers(self, effects: Dict[str, StrategyEffect], n: int) -> List[Dict[str, Any]]:
        sorted_effects = sorted(
            [(sid, e) for sid, e in effects.items() if e],
            key=lambda x: x[1].effectiveness_score,
            reverse=True
        )[:n]

        return [
            {
                "strategy_id": sid,
                "name": self._strategies[sid].name,
                "effectiveness_score": e.effectiveness_score,
                "success_rate": e.success_rate
            }
            for sid, e in sorted_effects
        ]

    def _get_underperformers(self, effects: Dict[str, StrategyEffect], n: int) -> List[Dict[str, Any]]:
        sorted_effects = sorted(
            [(sid, e) for sid, e in effects.items() if e and e.total_applications > 0],
            key=lambda x: x[1].effectiveness_score
        )[:n]

        return [
            {
                "strategy_id": sid,
                "name": self._strategies[sid].name,
                "effectiveness_score": e.effectiveness_score,
                "success_rate": e.success_rate
            }
            for sid, e in sorted_effects
        ]

    def get_best_strategy(
        self,
        content: str,
        file_path: Path,
        category: Optional[StrategyCategory] = None
    ) -> Optional[Tuple[BaseStrategy, StrategyMatch]]:
        categories = [category] if category else None
        matches = self.match_strategies(content, file_path, categories)

        if not matches:
            return None

        best_match = max(matches, key=lambda m: (m.confidence, -len(m.issues_found)))
        strategy = self.get_strategy(best_match.strategy_id)

        if strategy:
            return strategy, best_match
        return None

    def get_execution_order(self, strategy_ids: List[str]) -> List[str]:
        from collections import deque

        in_degree: Dict[str, int] = {sid: 0 for sid in strategy_ids}
        graph: Dict[str, List[str]] = {sid: [] for sid in strategy_ids}

        for sid in strategy_ids:
            strategy = self.get_strategy(sid)
            if strategy:
                for dep in strategy.get_dependencies():
                    if dep in strategy_ids:
                        graph[dep].append(sid)
                        in_degree[sid] += 1

        queue = deque([sid for sid in strategy_ids if in_degree[sid] == 0])
        result = []

        while queue:
            current = queue.popleft()
            result.append(current)

            for neighbor in graph[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(result) != len(strategy_ids):
            logger.warning("检测到策略依赖循环")

        return result

    def check_compatibility(self, strategy_ids: List[str]) -> Tuple[bool, List[str]]:
        conflicts = []

        for i, sid1 in enumerate(strategy_ids):
            strategy1 = self.get_strategy(sid1)
            if not strategy1:
                continue

            for sid2 in strategy_ids[i + 1:]:
                strategy2 = self.get_strategy(sid2)
                if not strategy2:
                    continue

                if not strategy1.is_compatible_with(strategy2):
                    conflicts.append(f"{sid1} 与 {sid2} 冲突")
                if not strategy2.is_compatible_with(strategy1):
                    conflicts.append(f"{sid2} 与 {sid1} 冲突")

        return len(conflicts) == 0, conflicts

    def register_custom_strategy(
        self,
        strategy_id: str,
        name: str,
        description: str,
        category: StrategyCategory,
        patterns: List[str],
        apply_func: Callable[[str, List[Dict[str, Any]]], Tuple[str, List[Dict[str, Any]]]],
        priority: StrategyPriority = StrategyPriority.MEDIUM
    ) -> bool:
        class CustomStrategy(BaseStrategy):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self._apply_func = apply_func
                self.patterns = patterns

            def can_apply(self, content: str, file_path: Path, **context) -> StrategyMatch:
                issues: List[Dict[str, Any]] = []
                matched_patterns: List[str] = []

                for pattern in patterns:
                    is_match, matches = self.matcher.match_text(content, pattern)
                    if is_match:
                        matched_patterns.append(pattern)
                        for match in matches:
                            line_num = content[:match.start()].count('\n') + 1
                            issues.append({
                                "type": "pattern_match",
                                "pattern": pattern,
                                "line": line_num,
                                "match_text": match.group()
                            })

                confidence = min(len(issues) * 0.2, 1.0)
                result = MatchResult.FULL_MATCH if issues else MatchResult.NO_MATCH

                return StrategyMatch(
                    strategy_id=self.strategy_id,
                    result=result,
                    confidence=confidence,
                    matched_patterns=matched_patterns,
                    issues_found=issues
                )

            def apply(self, content: str, issues: List[Dict[str, Any]], **context) -> Tuple[str, List[Dict[str, Any]]]:
                return self._apply_func(content, issues)

        strategy = CustomStrategy(
            strategy_id=strategy_id,
            name=name,
            description=description,
            category=category,
            priority=priority
        )

        return self.register_strategy(strategy)

    def export_strategies(self, output_path: Path) -> bool:
        try:
            data = {
                "exported_at": datetime.now().isoformat(),
                "strategies": [s.get_definition().to_dict() for s in self.get_all_strategies()],
                "effects": {sid: e.to_dict() for sid, e in self.evaluate_all_strategies().items()},
                "performance_report": self.get_strategy_performance_report(),
                "strategy_groups": self._strategy_groups,
                "strategy_versions": self._strategy_versions,
                "active_versions": self._active_version
            }

            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.info(f"策略已导出到: {output_path}")
            return True
        except Exception as e:
            logger.error(f"导出策略失败: {e}")
            return False

    def import_strategies(self, input_path: Path) -> int:
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            imported_count = 0
            for strategy_def in data.get("strategies", []):
                try:
                    category = StrategyCategory(strategy_def["category"])
                    priority = StrategyPriority(strategy_def["priority"])

                    self.register_custom_strategy(
                        strategy_id=strategy_def["strategy_id"],
                        name=strategy_def["name"],
                        description=strategy_def["description"],
                        category=category,
                        patterns=strategy_def.get("patterns", []),
                        apply_func=lambda c, i: (c, []),
                        priority=priority
                    )
                    imported_count += 1
                except Exception as e:
                    logger.warning(f"导入策略失败 {strategy_def.get('strategy_id')}: {e}")

            if "strategy_groups" in data:
                for group_name, strategy_ids in data["strategy_groups"].items():
                    self.create_strategy_group(group_name, strategy_ids)

            logger.info(f"已导入 {imported_count} 个策略")
            return imported_count
        except Exception as e:
            logger.error(f"导入策略失败: {e}")
            return 0

    def get_statistics(self) -> Dict[str, Any]:
        total_applications = sum(s._application_count for s in self.get_all_strategies())
        total_successes = sum(s._success_count for s in self.get_all_strategies())

        return {
            "total_strategies": len(self._strategies),
            "strategies_by_category": {
                cat.value: len(sids) for cat, sids in self._categories.items()
            },
            "total_applications": total_applications,
            "total_successes": total_successes,
            "overall_success_rate": total_successes / total_applications if total_applications > 0 else 0.0,
            "strategy_groups": len(self._strategy_groups)
        }

    def optimize_strategy_order(self) -> List[str]:
        effects = self.evaluate_all_strategies()

        sorted_strategies = sorted(
            effects.items(),
            key=lambda x: (
                -x[1].success_rate if x[1] else 0,
                -x[1].effectiveness_score if x[1] else 0,
                self._strategies[x[0]].priority.value if x[0] in self._strategies else 999
            )
        )

        return [sid for sid, _ in sorted_strategies]

    def reset_statistics(self) -> None:
        for strategy in self.get_all_strategies():
            strategy._application_count = 0
            strategy._success_count = 0
            strategy._total_time = 0.0
            strategy._true_positives = 0
            strategy._false_positives = 0
            strategy._false_negatives = 0
            strategy._execution_times = []
            strategy._issues_history = []

        self._effect_history.clear()
        logger.info("策略统计信息已重置")


class IntelligentStrategyMatcher:
    """智能策略匹配器 - 使用机器学习方法进行策略匹配"""

    def __init__(self, library: StrategyLibrary):
        self._library = library
        self._feature_weights: Dict[str, float] = {}
        self._pattern_importance: Dict[str, float] = {}
        self._context_weights: Dict[str, float] = {}
        self._match_history: List[Dict[str, Any]] = []
        self._learning_rate: float = 0.1
        self._decay_factor: float = 0.95
        self._initialize_weights()

    def _initialize_weights(self) -> None:
        strategies = self._library.get_all_strategies()
        for strategy in strategies:
            self._feature_weights[strategy.strategy_id] = 1.0
            for pattern in strategy.patterns:
                self._pattern_importance[f"{strategy.strategy_id}:{pattern}"] = 1.0

    def intelligent_match(
        self,
        content: str,
        file_path: Path,
        context: Optional[Dict[str, Any]] = None
    ) -> List[StrategyMatch]:
        base_matches = self._library.match_strategies(content, file_path)

        enhanced_matches = []
        for match in base_matches:
            enhanced_confidence = self._calculate_enhanced_confidence(
                match, content, file_path, context
            )

            enhanced_match = StrategyMatch(
                strategy_id=match.strategy_id,
                result=match.result,
                confidence=enhanced_confidence,
                matched_patterns=match.matched_patterns,
                issues_found=match.issues_found,
                metadata=match.metadata,
                severity=match.severity,
                execution_time_ms=match.execution_time_ms,
                fix_suggestions=match.fix_suggestions
            )
            enhanced_matches.append(enhanced_match)

        enhanced_matches.sort(key=lambda m: m.confidence, reverse=True)
        return enhanced_matches

    def _calculate_enhanced_confidence(
        self,
        match: StrategyMatch,
        content: str,
        file_path: Path,
        context: Optional[Dict[str, Any]] = None
    ) -> float:
        base_confidence = match.confidence

        strategy_id = match.strategy_id
        feature_weight = self._feature_weights.get(strategy_id, 1.0)

        pattern_boost = 0.0
        for pattern in match.matched_patterns:
            pattern_key = f"{strategy_id}:{pattern}"
            pattern_boost += self._pattern_importance.get(pattern_key, 1.0) * 0.1

        context_boost = 0.0
        if context:
            for key, value in context.items():
                context_key = f"{strategy_id}:{key}"
                if context_key in self._context_weights:
                    context_boost += self._context_weights[context_key] * 0.05

        issue_count_factor = min(len(match.issues_found) * 0.05, 0.3)

        enhanced = base_confidence * feature_weight + pattern_boost + context_boost + issue_count_factor
        return min(enhanced, 1.0)

    def record_match_feedback(
        self,
        match: StrategyMatch,
        was_successful: bool,
        user_rating: Optional[float] = None
    ) -> None:
        feedback = {
            'strategy_id': match.strategy_id,
            'confidence': match.confidence,
            'was_successful': was_successful,
            'user_rating': user_rating,
            'timestamp': datetime.now().isoformat(),
            'matched_patterns': match.matched_patterns
        }
        self._match_history.append(feedback)

        self._update_weights(feedback)

    def _update_weights(self, feedback: Dict[str, Any]) -> None:
        strategy_id = feedback['strategy_id']
        was_successful = feedback['was_successful']
        user_rating = feedback.get('user_rating')

        current_weight = self._feature_weights.get(strategy_id, 1.0)

        if was_successful:
            adjustment = self._learning_rate
            if user_rating:
                adjustment *= user_rating
        else:
            adjustment = -self._learning_rate

        new_weight = max(0.1, min(2.0, current_weight + adjustment))
        self._feature_weights[strategy_id] = new_weight

        for pattern in feedback.get('matched_patterns', []):
            pattern_key = f"{strategy_id}:{pattern}"
            current_pattern_weight = self._pattern_importance.get(pattern_key, 1.0)
            pattern_adjustment = adjustment * 0.5
            self._pattern_importance[pattern_key] = max(0.1, min(2.0, current_pattern_weight + pattern_adjustment))

    def get_match_statistics(self) -> Dict[str, Any]:
        if not self._match_history:
            return {'total_matches': 0}

        successful = sum(1 for h in self._match_history if h['was_successful'])
        total = len(self._match_history)

        strategy_stats: Dict[str, Dict[str, int]] = {}
        for h in self._match_history:
            sid = h['strategy_id']
            if sid not in strategy_stats:
                strategy_stats[sid] = {'total': 0, 'successful': 0}
            strategy_stats[sid]['total'] += 1
            if h['was_successful']:
                strategy_stats[sid]['successful'] += 1

        return {
            'total_matches': total,
            'successful_matches': successful,
            'success_rate': successful / total,
            'strategy_statistics': strategy_stats,
            'feature_weights': self._feature_weights.copy()
        }

    def decay_weights(self) -> None:
        for strategy_id in self._feature_weights:
            self._feature_weights[strategy_id] *= self._decay_factor

        for pattern_key in self._pattern_importance:
            self._pattern_importance[pattern_key] *= self._decay_factor

    def reset_learning(self) -> None:
        self._match_history.clear()
        self._initialize_weights()


class StrategyEffectEvaluator:
    """策略效果评估器 - 高级策略效果评估"""

    def __init__(self, library: StrategyLibrary):
        self._library = library
        self._evaluation_history: Dict[str, List[Dict[str, Any]]] = {}
        self._ab_test_groups: Dict[str, Dict[str, Any]] = {}
        self._metrics_config: Dict[str, Dict[str, float]] = {}

    def evaluate_comprehensive(
        self,
        strategy_id: str,
        time_window: Optional[int] = None
    ) -> Dict[str, Any]:
        strategy = self._library.get_strategy(strategy_id)
        if not strategy:
            return {'error': 'Strategy not found'}

        base_effect = strategy.get_effect()

        comprehensive = {
            'strategy_id': strategy_id,
            'basic_metrics': {
                'success_rate': base_effect.success_rate,
                'precision': base_effect.precision,
                'recall': base_effect.recall,
                'f1_score': base_effect.f1_score,
                'effectiveness_score': base_effect.effectiveness_score
            },
            'advanced_metrics': self._calculate_advanced_metrics(strategy_id),
            'trend_analysis': self._analyze_trend(strategy_id),
            'performance_over_time': self._get_performance_over_time(strategy_id, time_window),
            'recommendations': []
        }

        comprehensive['recommendations'] = self._generate_recommendations(comprehensive)

        if strategy_id not in self._evaluation_history:
            self._evaluation_history[strategy_id] = []
        self._evaluation_history[strategy_id].append({
            'timestamp': datetime.now().isoformat(),
            'metrics': comprehensive
        })

        return comprehensive

    def _calculate_advanced_metrics(self, strategy_id: str) -> Dict[str, float]:
        strategy = self._library.get_strategy(strategy_id)
        if not strategy:
            return {}

        effect = strategy.get_effect()

        stability = 1.0 - (effect.false_positives / max(effect.total_applications, 1))
        reliability = effect.success_rate * stability

        execution_stability = 1.0
        if len(strategy._execution_times) > 1:
            times = strategy._execution_times
            avg = sum(times) / len(times)
            variance = sum((t - avg) ** 2 for t in times) / len(times)
            std_dev = variance ** 0.5
            execution_stability = 1.0 / (1.0 + std_dev / max(avg, 1))

        return {
            'stability': stability,
            'reliability': reliability,
            'execution_stability': execution_stability,
            'overall_quality': (reliability + execution_stability) / 2
        }

    def _analyze_trend(self, strategy_id: str) -> Dict[str, Any]:
        strategy = self._library.get_strategy(strategy_id)
        if not strategy:
            return {'trend': 'unknown'}

        effect = strategy.get_effect()
        history = self._evaluation_history.get(strategy_id, [])

        if len(history) < 2:
            return {
                'trend': effect.trend,
                'confidence': 'low',
                'data_points': len(history)
            }

        recent_scores = [h['metrics']['basic_metrics']['effectiveness_score'] for h in history[-5:]]
        if len(recent_scores) >= 2:
            slope = (recent_scores[-1] - recent_scores[0]) / len(recent_scores)
            if slope > 0.01:
                detailed_trend = 'improving'
            elif slope < -0.01:
                detailed_trend = 'declining'
            else:
                detailed_trend = 'stable'
        else:
            detailed_trend = effect.trend

        return {
            'trend': detailed_trend,
            'base_trend': effect.trend,
            'confidence': 'high' if len(history) >= 5 else 'medium',
            'data_points': len(history),
            'recent_improvement': recent_scores[-1] - recent_scores[0] if len(recent_scores) >= 2 else 0
        }

    def _get_performance_over_time(
        self,
        strategy_id: str,
        time_window: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        history = self._evaluation_history.get(strategy_id, [])

        if time_window:
            cutoff = datetime.now().timestamp() - time_window * 3600
            history = [
                h for h in history
                if datetime.fromisoformat(h['timestamp']).timestamp() >= cutoff
            ]

        return [
            {
                'timestamp': h['timestamp'],
                'effectiveness_score': h['metrics']['basic_metrics']['effectiveness_score'],
                'success_rate': h['metrics']['basic_metrics']['success_rate']
            }
            for h in history
        ]

    def _generate_recommendations(self, metrics: Dict[str, Any]) -> List[str]:
        recommendations = []

        basic = metrics.get('basic_metrics', {})
        advanced = metrics.get('advanced_metrics', {})
        trend = metrics.get('trend_analysis', {})

        if basic.get('success_rate', 0) < 0.5:
            recommendations.append("成功率较低，建议检查策略模式是否准确")

        if basic.get('precision', 0) < 0.7:
            recommendations.append("精确度不足，可能存在过多误报")

        if basic.get('recall', 0) < 0.7:
            recommendations.append("召回率不足，可能遗漏部分问题")

        if advanced.get('stability', 0) < 0.8:
            recommendations.append("稳定性不足，建议优化策略逻辑")

        if trend.get('trend') == 'declining':
            recommendations.append("效果呈下降趋势，建议重新评估策略")

        if not recommendations:
            recommendations.append("策略表现良好，继续保持")

        return recommendations

    def create_ab_test(
        self,
        test_id: str,
        strategy_a: str,
        strategy_b: str,
        config: Optional[Dict[str, Any]] = None
    ) -> bool:
        if test_id in self._ab_test_groups:
            return False

        self._ab_test_groups[test_id] = {
            'strategy_a': strategy_a,
            'strategy_b': strategy_b,
            'config': config or {},
            'results_a': [],
            'results_b': [],
            'created_at': datetime.now().isoformat(),
            'status': 'running'
        }
        return True

    def record_ab_test_result(
        self,
        test_id: str,
        variant: str,
        result: Dict[str, Any]
    ) -> bool:
        if test_id not in self._ab_test_groups:
            return False

        test = self._ab_test_groups[test_id]
        if variant == 'a':
            test['results_a'].append(result)
        elif variant == 'b':
            test['results_b'].append(result)
        else:
            return False

        return True

    def get_ab_test_results(self, test_id: str) -> Optional[Dict[str, Any]]:
        if test_id not in self._ab_test_groups:
            return None

        test = self._ab_test_groups[test_id]

        def calculate_stats(results: List[Dict[str, Any]]) -> Dict[str, float]:
            if not results:
                return {'count': 0, 'success_rate': 0, 'avg_time': 0}

            successes = sum(1 for r in results if r.get('success', False))
            times = [r.get('execution_time', 0) for r in results]

            return {
                'count': len(results),
                'success_rate': successes / len(results),
                'avg_time': sum(times) / len(times) if times else 0
            }

        stats_a = calculate_stats(test['results_a'])
        stats_b = calculate_stats(test['results_b'])

        winner = None
        if stats_a['count'] >= 10 and stats_b['count'] >= 10:
            if stats_a['success_rate'] > stats_b['success_rate'] + 0.05:
                winner = 'a'
            elif stats_b['success_rate'] > stats_a['success_rate'] + 0.05:
                winner = 'b'

        return {
            'test_id': test_id,
            'strategy_a': test['strategy_a'],
            'strategy_b': test['strategy_b'],
            'stats_a': stats_a,
            'stats_b': stats_b,
            'winner': winner,
            'status': test['status']
        }

    def end_ab_test(self, test_id: str) -> bool:
        if test_id not in self._ab_test_groups:
            return False

        self._ab_test_groups[test_id]['status'] = 'completed'
        return True


class StrategyAutoLearner:
    """策略自动学习器 - 从历史数据自动优化策略"""

    def __init__(self, library: StrategyLibrary):
        self._library = library
        self._learning_data: List[Dict[str, Any]] = []
        self._optimized_patterns: Dict[str, List[str]] = {}
        self._pattern_suggestions: Dict[str, List[str]] = {}
        self._learning_threshold: int = 100
        self._optimization_history: List[Dict[str, Any]] = []

    def record_learning_data(
        self,
        strategy_id: str,
        content: str,
        issues: List[Dict[str, Any]],
        fix_result: Dict[str, Any]
    ) -> None:
        data = {
            'strategy_id': strategy_id,
            'content_hash': hash(content),
            'issues': issues,
            'fix_result': fix_result,
            'timestamp': datetime.now().isoformat(),
            'success': fix_result.get('success', False)
        }
        self._learning_data.append(data)

        if len(self._learning_data) >= self._learning_threshold:
            self._run_learning_cycle()

    def _run_learning_cycle(self) -> None:
        strategy_data: Dict[str, List[Dict[str, Any]]] = {}

        for data in self._learning_data:
            sid = data['strategy_id']
            if sid not in strategy_data:
                strategy_data[sid] = []
            strategy_data[sid].append(data)

        for strategy_id, data_list in strategy_data.items():
            self._optimize_strategy_patterns(strategy_id, data_list)

        self._learning_data = self._learning_data[-self._learning_threshold // 2:]

    def _optimize_strategy_patterns(
        self,
        strategy_id: str,
        data_list: List[Dict[str, Any]]
    ) -> None:
        strategy = self._library.get_strategy(strategy_id)
        if not strategy:
            return

        successful_patterns: Dict[str, int] = {}
        failed_patterns: Dict[str, int] = {}

        for data in data_list:
            for issue in data.get('issues', []):
                pattern = issue.get('pattern', '')
                if not pattern:
                    continue

                if data['success']:
                    successful_patterns[pattern] = successful_patterns.get(pattern, 0) + 1
                else:
                    failed_patterns[pattern] = failed_patterns.get(pattern, 0) + 1

        pattern_scores: Dict[str, float] = {}
        for pattern, success_count in successful_patterns.items():
            fail_count = failed_patterns.get(pattern, 0)
            total = success_count + fail_count
            if total >= 3:
                pattern_scores[pattern] = success_count / total

        if pattern_scores:
            optimized = sorted(pattern_scores.items(), key=lambda x: x[1], reverse=True)
            self._optimized_patterns[strategy_id] = [p for p, s in optimized if s >= 0.7]

        self._generate_pattern_suggestions(strategy_id, data_list)

    def _generate_pattern_suggestions(
        self,
        strategy_id: str,
        data_list: List[Dict[str, Any]]
    ) -> None:
        successful_issues: List[Dict[str, Any]] = [
            d for d in data_list if d['success']
        ]

        if len(successful_issues) < 5:
            return

        common_patterns: Dict[str, int] = {}
        for data in successful_issues:
            for issue in data.get('issues', []):
                match_text = issue.get('match_text', '')
                if match_text and len(match_text) > 5:
                    common_patterns[match_text] = common_patterns.get(match_text, 0) + 1

        suggestions = [
            pattern for pattern, count in common_patterns.items()
            if count >= 3
        ]

        if suggestions:
            self._pattern_suggestions[strategy_id] = suggestions[:5]

    def get_optimized_patterns(self, strategy_id: str) -> List[str]:
        return self._optimized_patterns.get(strategy_id, [])

    def get_pattern_suggestions(self, strategy_id: str) -> List[str]:
        return self._pattern_suggestions.get(strategy_id, [])

    def apply_learned_optimizations(self, strategy_id: str) -> Dict[str, Any]:
        strategy = self._library.get_strategy(strategy_id)
        if not strategy:
            return {'success': False, 'error': 'Strategy not found'}

        optimized_patterns = self.get_optimized_patterns(strategy_id)
        if not optimized_patterns:
            return {'success': False, 'error': 'No optimized patterns available'}

        original_patterns = strategy.patterns.copy()

        new_patterns = list(set(original_patterns + optimized_patterns))

        optimization_record = {
            'strategy_id': strategy_id,
            'timestamp': datetime.now().isoformat(),
            'original_patterns': original_patterns,
            'new_patterns': new_patterns,
            'added_patterns': list(set(new_patterns) - set(original_patterns))
        }

        strategy.patterns = new_patterns

        self._optimization_history.append(optimization_record)

        return {
            'success': True,
            'added_patterns': optimization_record['added_patterns'],
            'total_patterns': len(new_patterns)
        }

    def get_learning_statistics(self) -> Dict[str, Any]:
        total_data = len(self._learning_data)
        successful_data = sum(1 for d in self._learning_data if d.get('success'))

        strategy_stats: Dict[str, Dict[str, int]] = {}
        for data in self._learning_data:
            sid = data['strategy_id']
            if sid not in strategy_stats:
                strategy_stats[sid] = {'total': 0, 'successful': 0}
            strategy_stats[sid]['total'] += 1
            if data['success']:
                strategy_stats[sid]['successful'] += 1

        return {
            'total_learning_data': total_data,
            'successful_data': successful_data,
            'success_rate': successful_data / total_data if total_data > 0 else 0,
            'strategies_with_optimized_patterns': len(self._optimized_patterns),
            'strategies_with_suggestions': len(self._pattern_suggestions),
            'optimization_history_count': len(self._optimization_history),
            'strategy_statistics': strategy_stats
        }

    def export_learning_data(self, output_path: Path) -> bool:
        try:
            data = {
                'exported_at': datetime.now().isoformat(),
                'learning_data': self._learning_data[-1000:],
                'optimized_patterns': self._optimized_patterns,
                'pattern_suggestions': self._pattern_suggestions,
                'optimization_history': self._optimization_history,
                'statistics': self.get_learning_statistics()
            }

            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            return True
        except Exception as e:
            logger.error(f"导出学习数据失败: {e}")
            return False

    def import_learning_data(self, input_path: Path) -> int:
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            imported = 0
            for learning_item in data.get('learning_data', []):
                self._learning_data.append(learning_item)
                imported += 1

            self._optimized_patterns.update(data.get('optimized_patterns', {}))
            self._pattern_suggestions.update(data.get('pattern_suggestions', {}))

            return imported
        except Exception as e:
            logger.error(f"导入学习数据失败: {e}")
            return 0

    def reset_learning(self) -> None:
        self._learning_data.clear()
        self._optimized_patterns.clear()
        self._pattern_suggestions.clear()
        self._optimization_history.clear()


class StrategyOrchestrator:
    """策略编排器 - 协调多个策略的执行"""

    def __init__(self, library: StrategyLibrary):
        self._library = library
        self._matcher = IntelligentStrategyMatcher(library)
        self._evaluator = StrategyEffectEvaluator(library)
        self._learner = StrategyAutoLearner(library)
        self._execution_history: List[Dict[str, Any]] = []

    def orchestrate_fix(
        self,
        content: str,
        file_path: Path,
        max_strategies: int = 5,
        use_learning: bool = True
    ) -> Dict[str, Any]:
        matches = self._matcher.intelligent_match(content, file_path)

        top_matches = matches[:max_strategies]

        execution_plan = self._create_execution_plan(top_matches)

        result = {
            'original_content': content,
            'fixed_content': content,
            'execution_plan': execution_plan,
            'applied_strategies': [],
            'failed_strategies': [],
            'all_fixes': [],
            'learning_applied': use_learning
        }

        current_content = content
        for plan_item in execution_plan:
            strategy_id = plan_item['strategy_id']
            match = plan_item['match']

            try:
                fixed_content, fixes = self._library.apply_strategy(
                    strategy_id,
                    current_content,
                    match.issues_found
                )

                result['applied_strategies'].append(strategy_id)
                result['all_fixes'].extend(fixes)
                current_content = fixed_content

                if use_learning:
                    self._learner.record_learning_data(
                        strategy_id,
                        content,
                        match.issues_found,
                        {'success': True, 'fixes': fixes}
                    )

            except Exception as e:
                result['failed_strategies'].append({
                    'strategy_id': strategy_id,
                    'error': str(e)
                })

                if use_learning:
                    self._learner.record_learning_data(
                        strategy_id,
                        content,
                        match.issues_found,
                        {'success': False, 'error': str(e)}
                    )

        result['fixed_content'] = current_content

        self._execution_history.append({
            'file_path': str(file_path),
            'timestamp': datetime.now().isoformat(),
            'applied_count': len(result['applied_strategies']),
            'failed_count': len(result['failed_strategies'])
        })

        return result

    def _create_execution_plan(
        self,
        matches: List[StrategyMatch]
    ) -> List[Dict[str, Any]]:
        strategy_ids = [m.strategy_id for m in matches]

        execution_order = self._library.get_execution_order(strategy_ids)

        match_map = {m.strategy_id: m for m in matches}

        plan = []
        for sid in execution_order:
            if sid in match_map:
                plan.append({
                    'strategy_id': sid,
                    'match': match_map[sid],
                    'priority': self._library.get_strategy(sid).priority.value if self._library.get_strategy(sid) else 999
                })

        return plan

    def get_execution_statistics(self) -> Dict[str, Any]:
        if not self._execution_history:
            return {'total_executions': 0}

        total = len(self._execution_history)
        total_applied = sum(e['applied_count'] for e in self._execution_history)
        total_failed = sum(e['failed_count'] for e in self._execution_history)

        return {
            'total_executions': total,
            'total_strategies_applied': total_applied,
            'total_strategies_failed': total_failed,
            'average_strategies_per_execution': total_applied / total,
            'success_rate': (total_applied - total_failed) / total_applied if total_applied > 0 else 0,
            'learning_statistics': self._learner.get_learning_statistics()
        }

    def get_matcher(self) -> IntelligentStrategyMatcher:
        return self._matcher

    def get_evaluator(self) -> StrategyEffectEvaluator:
        return self._evaluator

    def get_learner(self) -> StrategyAutoLearner:
        return self._learner


@dataclass
class StrategyTemplate:
    """策略模板 - 用于快速创建新策略"""
    template_id: str
    name: str
    description: str
    category: StrategyCategory
    priority: StrategyPriority
    pattern_template: str
    fix_template: str
    preconditions_template: List[str]
    postconditions_template: List[str]
    variables: Dict[str, str]
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def instantiate(self, variables: Dict[str, str]) -> Dict[str, Any]:
        """根据变量实例化模板"""
        result = {
            'name': self.name.format(**variables),
            'description': self.description.format(**variables),
            'category': self.category,
            'priority': self.priority,
            'patterns': [self.pattern_template.format(**variables)],
            'fix_template': self.fix_template.format(**variables),
            'preconditions': [p.format(**variables) for p in self.preconditions_template],
            'postconditions': [p.format(**variables) for p in self.postconditions_template]
        }
        return result

    def to_dict(self) -> Dict[str, Any]:
        return {
            'template_id': self.template_id,
            'name': self.name,
            'description': self.description,
            'category': self.category.value,
            'priority': self.priority.value,
            'pattern_template': self.pattern_template,
            'fix_template': self.fix_template,
            'preconditions_template': self.preconditions_template,
            'postconditions_template': self.postconditions_template,
            'variables': self.variables,
            'created_at': self.created_at
        }


class StrategyLifecycleManager:
    """策略生命周期管理器 - 管理策略的完整生命周期"""

    def __init__(self, library: StrategyLibrary):
        self._library = library
        self._strategy_lifecycle: Dict[str, Dict[str, Any]] = {}
        self._templates: Dict[str, StrategyTemplate] = {}
        self._config_path: Optional[Path] = None
        self._auto_save: bool = True
        self._initialize_default_templates()

    def _initialize_default_templates(self) -> None:
        """初始化默认策略模板"""
        default_templates = [
            StrategyTemplate(
                template_id="syntax_error_template",
                name="语法错误修复 - {error_type}",
                description="修复 {error_type} 类型的语法错误",
                category=StrategyCategory.SYNTAX,
                priority=StrategyPriority.CRITICAL,
                pattern_template=r'{pattern}',
                fix_template='{fix_pattern}',
                preconditions_template=['代码必须包含语法错误'],
                postconditions_template=['修复后代码必须可解析'],
                variables={'error_type': '', 'pattern': '', 'fix_pattern': ''}
            ),
            StrategyTemplate(
                template_id="import_error_template",
                name="导入修复 - {module_name}",
                description="修复 {module_name} 模块的导入问题",
                category=StrategyCategory.IMPORT,
                priority=StrategyPriority.HIGH,
                pattern_template=r'import\s+{module_name}|from\s+{module_name}',
                fix_template='from {module_name} import {imports}',
                preconditions_template=['模块必须存在'],
                postconditions_template=['导入必须成功'],
                variables={'module_name': '', 'imports': ''}
            ),
            StrategyTemplate(
                template_id="security_issue_template",
                name="安全问题修复 - {issue_type}",
                description="修复 {issue_type} 类型的安全问题",
                category=StrategyCategory.SECURITY,
                priority=StrategyPriority.CRITICAL,
                pattern_template=r'{pattern}',
                fix_template='# TODO: 安全问题需要手动修复\n{original_line}',
                preconditions_template=['必须审查安全问题'],
                postconditions_template=['安全问题必须得到处理'],
                variables={'issue_type': '', 'pattern': '', 'original_line': ''}
            )
        ]

        for template in default_templates:
            self._templates[template.template_id] = template

    def create_strategy_from_template(
        self,
        template_id: str,
        strategy_id: str,
        variables: Dict[str, str]
    ) -> Optional[BaseStrategy]:
        """从模板创建策略"""
        template = self._templates.get(template_id)
        if not template:
            logger.error(f"模板不存在: {template_id}")
            return None

        instance = template.instantiate(variables)

        def apply_func(content: str, issues: List[Dict[str, Any]]) -> Tuple[str, List[Dict[str, Any]]]:
            fixes = []
            for issue in issues:
                fixes.append({
                    'type': 'template_fix',
                    'line': issue.get('line', 0),
                    'message': f"应用模板修复: {template.name}"
                })
            return content, fixes

        success = self._library.register_custom_strategy(
            strategy_id=strategy_id,
            name=instance['name'],
            description=instance['description'],
            category=instance['category'],
            patterns=instance['patterns'],
            apply_func=apply_func,
            priority=instance['priority']
        )

        if success:
            self._record_lifecycle_event(strategy_id, 'created_from_template', {
                'template_id': template_id,
                'variables': variables
            })
            return self._library.get_strategy(strategy_id)
        return None

    def register_template(self, template: StrategyTemplate) -> bool:
        """注册新模板"""
        if template.template_id in self._templates:
            logger.warning(f"模板ID已存在: {template.template_id}")
            return False

        self._templates[template.template_id] = template
        logger.info(f"已注册模板: {template.name}")
        return True

    def get_template(self, template_id: str) -> Optional[StrategyTemplate]:
        """获取模板"""
        return self._templates.get(template_id)

    def list_templates(self) -> List[StrategyTemplate]:
        """列出所有模板"""
        return list(self._templates.values())

    def _record_lifecycle_event(
        self,
        strategy_id: str,
        event: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """记录生命周期事件"""
        if strategy_id not in self._strategy_lifecycle:
            self._strategy_lifecycle[strategy_id] = {
                'created_at': datetime.now().isoformat(),
                'events': [],
                'status': 'active'
            }

        self._strategy_lifecycle[strategy_id]['events'].append({
            'event': event,
            'timestamp': datetime.now().isoformat(),
            'details': details or {}
        })

        if self._auto_save and self._config_path:
            self._save_lifecycle_state()

    def activate_strategy(self, strategy_id: str) -> bool:
        """激活策略"""
        strategy = self._library.get_strategy(strategy_id)
        if not strategy:
            return False

        strategy.status = StrategyStatus.ACTIVE
        self._record_lifecycle_event(strategy_id, 'activated')
        logger.info(f"策略已激活: {strategy_id}")
        return True

    def deactivate_strategy(self, strategy_id: str) -> bool:
        """停用策略"""
        strategy = self._library.get_strategy(strategy_id)
        if not strategy:
            return False

        strategy.status = StrategyStatus.DISABLED
        self._record_lifecycle_event(strategy_id, 'deactivated')
        logger.info(f"策略已停用: {strategy_id}")
        return True

    def deprecate_strategy(self, strategy_id: str, reason: str) -> bool:
        """废弃策略"""
        strategy = self._library.get_strategy(strategy_id)
        if not strategy:
            return False

        strategy.status = StrategyStatus.DEPRECATED
        self._record_lifecycle_event(strategy_id, 'deprecated', {'reason': reason})
        logger.info(f"策略已废弃: {strategy_id}, 原因: {reason}")
        return True

    def mark_experimental(self, strategy_id: str) -> bool:
        """标记策略为实验性"""
        strategy = self._library.get_strategy(strategy_id)
        if not strategy:
            return False

        strategy.status = StrategyStatus.EXPERIMENTAL
        self._record_lifecycle_event(strategy_id, 'marked_experimental')
        logger.info(f"策略已标记为实验性: {strategy_id}")
        return True

    def get_strategy_lifecycle(self, strategy_id: str) -> Optional[Dict[str, Any]]:
        """获取策略生命周期信息"""
        return self._strategy_lifecycle.get(strategy_id)

    def get_active_strategies(self) -> List[BaseStrategy]:
        """获取所有活跃策略"""
        return [
            s for s in self._library.get_all_strategies()
            if s.status == StrategyStatus.ACTIVE
        ]

    def get_deprecated_strategies(self) -> List[BaseStrategy]:
        """获取所有废弃策略"""
        return [
            s for s in self._library.get_all_strategies()
            if s.status == StrategyStatus.DEPRECATED
        ]

    def get_experimental_strategies(self) -> List[BaseStrategy]:
        """获取所有实验性策略"""
        return [
            s for s in self._library.get_all_strategies()
            if s.status == StrategyStatus.EXPERIMENTAL
        ]

    def set_config_path(self, path: Path) -> None:
        """设置配置文件路径"""
        self._config_path = path

    def _save_lifecycle_state(self) -> bool:
        """保存生命周期状态"""
        if not self._config_path:
            return False

        try:
            data = {
                'saved_at': datetime.now().isoformat(),
                'lifecycle': self._strategy_lifecycle,
                'templates': [t.to_dict() for t in self._templates.values()]
            }

            self._config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"保存生命周期状态失败: {e}")
            return False

    def load_lifecycle_state(self, path: Path) -> bool:
        """加载生命周期状态"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self._strategy_lifecycle = data.get('lifecycle', {})

            for template_data in data.get('templates', []):
                template = StrategyTemplate(
                    template_id=template_data['template_id'],
                    name=template_data['name'],
                    description=template_data['description'],
                    category=StrategyCategory(template_data['category']),
                    priority=StrategyPriority(template_data['priority']),
                    pattern_template=template_data['pattern_template'],
                    fix_template=template_data['fix_template'],
                    preconditions_template=template_data['preconditions_template'],
                    postconditions_template=template_data['postconditions_template'],
                    variables=template_data['variables'],
                    created_at=template_data.get('created_at', datetime.now().isoformat())
                )
                self._templates[template.template_id] = template

            self._config_path = path
            logger.info(f"已加载生命周期状态: {path}")
            return True
        except Exception as e:
            logger.error(f"加载生命周期状态失败: {e}")
            return False

    def cleanup_deprecated_strategies(self, days: int = 30) -> int:
        """清理废弃超过指定天数的策略"""
        removed_count = 0
        cutoff = datetime.now().timestamp() - days * 24 * 3600

        strategies_to_remove = []
        for strategy_id, lifecycle in self._strategy_lifecycle.items():
            for event in lifecycle.get('events', []):
                if event['event'] == 'deprecated':
                    event_time = datetime.fromisoformat(event['timestamp']).timestamp()
                    if event_time < cutoff:
                        strategies_to_remove.append(strategy_id)
                        break

        for strategy_id in strategies_to_remove:
            if self._library.unregister_strategy(strategy_id):
                del self._strategy_lifecycle[strategy_id]
                removed_count += 1

        if removed_count > 0:
            logger.info(f"已清理 {removed_count} 个废弃策略")

        return removed_count


class EnhancedIntelligentMatcher(IntelligentStrategyMatcher):
    """增强型智能策略匹配器 - 多特征融合和上下文感知"""

    def __init__(self, library: StrategyLibrary):
        super().__init__(library)
        self._match_cache: Dict[str, List[StrategyMatch]] = {}
        self._cache_max_size: int = 1000
        self._context_analyzers: List[Callable[[str, Path], Dict[str, Any]]] = []
        self._feature_extractors: List[Callable[[str, Path], Dict[str, float]]] = []
        self._semantic_analyzers: List[Callable[[str, Path], Dict[str, Any]]] = []
        self._pattern_embeddings: Dict[str, List[float]] = {}
        self._similarity_matrix: Dict[str, Dict[str, float]] = {}
        self._initialize_default_analyzers()

    def _initialize_default_analyzers(self) -> None:
        self._context_analyzers = [
            self._analyze_file_context,
            self._analyze_code_structure,
            self._analyze_error_context,
            self._analyze_project_context
        ]
        self._feature_extractors = [
            self._extract_syntax_features,
            self._extract_import_features,
            self._extract_style_features,
            self._extract_security_features,
            self._extract_complexity_features,
            self._extract_semantic_features
        ]
        self._semantic_analyzers = [
            self._analyze_data_flow,
            self._analyze_control_flow,
            self._analyze_dependency_graph
        ]

    def _analyze_file_context(self, content: str, file_path: Path) -> Dict[str, Any]:
        return {
            'file_extension': file_path.suffix,
            'file_name': file_path.name,
            'file_size': len(content),
            'line_count': content.count('\n') + 1,
            'is_test_file': 'test' in file_path.name.lower(),
            'is_config_file': file_path.suffix in ['.json', '.yaml', '.yml', '.toml', '.ini'],
            'directory_depth': len(file_path.parts) - 1,
            'is_init_file': file_path.name == '__init__.py',
            'is_main_file': file_path.stem == '__main__',
            'has_shebang': content.startswith('#!'),
            'encoding_hint': 'coding:' in content.split('\n')[0] if content else ''
        }

    def _analyze_code_structure(self, content: str, file_path: Path) -> Dict[str, Any]:
        try:
            tree = ast.parse(content)
            functions = [node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
            classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
            imports = [node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]
            decorators = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]

            max_depth = 0
            for node in ast.walk(tree):
                depth = self._get_node_depth(node)
                max_depth = max(max_depth, depth)

            return {
                'has_functions': len(functions) > 0,
                'has_classes': len(classes) > 0,
                'has_imports': len(imports) > 0,
                'function_count': len(functions),
                'class_count': len(classes),
                'import_count': len(imports),
                'decorator_count': len(decorators),
                'is_module': len(functions) > 0 or len(classes) > 0,
                'max_nesting_depth': max_depth,
                'has_main_block': any(isinstance(n, ast.If) and n.body and isinstance(n.body[0], ast.If) for n in ast.walk(tree)),
                'has_docstrings': any(isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str) for node in ast.walk(tree))
            }
        except SyntaxError:
            return {
                'has_syntax_error': True,
                'is_module': False,
                'parse_error': True
            }

        except Exception as e:
            return {
                'has_parse_error': True,
                'error_message': str(e)
            }

    def _get_node_depth(self, node: ast.AST, current_depth: int = 0) -> int:
        max_depth = current_depth
        for child in ast.iter_child_nodes(node):
            child_depth = self._get_node_depth(child, current_depth + 1)
            max_depth = max(max_depth, child_depth)
        return max_depth

    def _analyze_error_context(self, content: str, file_path: Path) -> Dict[str, Any]:
        error_indicators = {
            'has_syntax_errors': False,
            'has_indentation_errors': False,
            'has_import_errors': False,
            'has_type_errors': False,
            'error_count': 0,
            'error_types': [],
            'error_lines': []
        }

        try:
            ast.parse(content)
        except SyntaxError as e:
            error_indicators['has_syntax_errors'] = True
            error_indicators['error_count'] += 1
            error_indicators['error_types'].append('syntax')
            error_indicators['error_lines'].append(e.lineno or 0)
            if 'indent' in str(e.msg).lower():
                error_indicators['has_indentation_errors'] = True
            if 'import' in str(e.msg).lower():
                error_indicators['has_import_errors'] = True

        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if 'TODO' in stripped or 'FIXME' in stripped or 'XXX' in stripped:
                error_indicators['error_count'] += 1
                error_indicators['error_types'].append('todo')
            if 'TypeError' in stripped or 'AttributeError' in stripped:
                error_indicators['has_type_errors'] = True
                error_indicators['error_count'] += 1

        return error_indicators

    def _analyze_project_context(self, content: str, file_path: Path) -> Dict[str, Any]:
        context = {
            'relative_imports': [],
            'absolute_imports': [],
            'local_modules': [],
            'is_part_of_package': False
        }
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    if node.level > 0:
                        context['relative_imports'].append(node.module or '')
                    else:
                        context['absolute_imports'].append(node.module or '')
        except SyntaxError:
            pass
        parent_dir = file_path.parent
        context['is_part_of_package'] = (parent_dir / '__init__.py').exists()
        context['local_modules'] = [f.stem for f in parent_dir.glob('*.py') if f != file_path]

        return context

    def _extract_syntax_features(self, content: str, file_path: Path) -> Dict[str, float]:
        features = {
            'syntax_complexity': 0.0,
            'indentation_consistency': 1.0,
            'bracket_balance': 1.0,
            'quote_balance': 1.0,
            'keyword_density': 0.0,
            'operator_variety': 0.0
        }
        lines = content.split('\n')
        indentations = []
        for line in lines:
            if line.strip():
                indent = len(line) - len(line.lstrip())
                indentations.append(indent)
        if len(set(indentations)) > 1:
            indent_set = set(indentations)
            if len(indent_set) > 1:
                features['indentation_consistency'] = 0.8
            if max(indent_set) - min(indent_set) > 8:
                features['indentation_consistency'] = 0.5
        open_brackets = content.count('(') + content.count('[') + content.count('{')
        close_brackets = content.count(')') + content.count(']') + content.count('}')
        if open_brackets != close_brackets:
            diff = abs(open_brackets - close_brackets)
            features['bracket_balance'] = max(0.0, 1.0 - diff * 0.05)
        single_quotes = content.count("'") - content.count("\\'")
        double_quotes = content.count('"') - content.count('\\"')
        if (single_quotes + double_quotes) % 2 != 0:
            features['quote_balance'] = 0.5
        keywords = ['def', 'class', 'if', 'for', 'while', 'try', 'except', 'with', 'return', 'yield', 'import', 'from']
        keyword_count = sum(content.count(f'\\b{kw}\\b') for kw in keywords)
        features['keyword_density'] = min(keyword_count / max(len(lines), 1) * 0.5, 1.0)
        operators = ['+', '-', '*', '/', '//', '%', '**', '==', '!=', '<', '>', '<=', '>=', 'and', 'or', 'not']
        operator_count = sum(content.count(op) for op in operators)
        features['operator_variety'] = min(operator_count / max(len(content), 1) * 0.01, 1.0)
        return features

    def _extract_import_features(self, content: str, file_path: Path) -> Dict[str, float]:
        features = {
            'import_count': 0.0,
            'from_import_ratio': 0.0,
            'wildcard_import': 0.0,
            'relative_import_ratio': 0.0,
            'stdlib_ratio': 0.0,
            'third_party_ratio': 0.0
        }
        import_lines = [line for line in content.split('\n') if line.strip().startswith(('import ', 'from '))]
        features['import_count'] = min(len(import_lines) / 10.0, 1.0)
        from_imports = sum(1 for line in import_lines if line.strip().startswith('from '))
        if import_lines:
            features['from_import_ratio'] = from_imports / len(import_lines)
        if 'import *' in content:
            features['wildcard_import'] = 1.0
        relative_imports = sum(1 for line in import_lines if line.strip().startswith('from .'))
        if import_lines:
            features['relative_import_ratio'] = relative_imports / len(import_lines)
        stdlib_modules = {'os', 'sys', 're', 'json', 'datetime', 'pathlib', 'collections', 'typing', 'logging', 'argparse', 'functools', 'itertools', 'abc', 'io', 'math', 'random', 'time', 'copy', 'pickle', 'hashlib', 'base64', 'uuid', 'tempfile', 'shutil', 'subprocess', 'threading', 'multiprocessing', 'asyncio', 'socket', 'http', 'urllib', 'email', 'html', 'xml', 'csv', 'sqlite3'}
        stdlib_count = sum(1 for line in import_lines if any(m in line for m in stdlib_modules))
        if import_lines:
            features['stdlib_ratio'] = stdlib_count / len(import_lines)
            features['third_party_ratio'] = 1.0 - features['stdlib_ratio']
        return features
    def _extract_style_features(self, content: str, file_path: Path) -> Dict[str, float]:
        lines = content.split('\n')
        features = {
            'avg_line_length': 0.0,
            'long_line_ratio': 0.0,
            'trailing_whitespace_ratio': 0.0,
            'empty_line_ratio': 0.0,
            'comment_ratio': 0.0,
            'docstring_coverage': 0.0
        }
        if lines:
            total_length = sum(len(line) for line in lines)
            features['avg_line_length'] = min(total_length / len(lines) / 80.0, 1.0)
            long_lines = sum(1 for line in lines if len(line) > 120)
            features['long_line_ratio'] = min(long_lines / len(lines), 1.0)
            trailing_whitespace = sum(1 for line in lines if line != line.rstrip())
            features['trailing_whitespace_ratio'] = min(trailing_whitespace / len(lines), 1.0)
            empty_lines = sum(1 for line in lines if not line.strip())
            features['empty_line_ratio'] = min(empty_lines / len(lines), 1.0)
            comment_lines = sum(1 for line in lines if line.strip().startswith('#'))
            features['comment_ratio'] = min(comment_lines / len(lines), 1.0)
        try:
            tree = ast.parse(content)
            total_items = 0
            documented_items = 0
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    total_items += 1
                    if ast.get_docstring(node):
                        documented_items += 1
            if total_items > 0:
                features['docstring_coverage'] = documented_items / total_items
        except SyntaxError:
            pass
        return features
    def _extract_security_features(self, content: str, file_path: Path) -> Dict[str, float]:
        features = {
            'has_hardcoded_secrets': 0.0,
            'has_dangerous_functions': 0.0,
            'has_sql_concat': 0.0,
            'has_shell_execution': 0.0,
            'has_pickle_usage': 0.0,
            'has_weak_crypto': 0.0,
            'security_risk_score': 0.0
        }
        secret_patterns = [
            r'password\s*=\s*[\'"]',
            r'api_key\s*=\s*[\'"]',
            r'secret\s*=\s*[\'"]',
            r'token\s*=\s*[\'"]',
            r'private_key\s*=\s*[\'"]'
        ]
        for pattern in secret_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                features['has_hardcoded_secrets'] = 1.0
                break
        dangerous_funcs = ['eval(', 'exec(', 'compile(', '__import__(']
        for func in dangerous_funcs:
            if func in content:
                features['has_dangerous_functions'] = 1.0
                break
        if re.search(r'execute\s*\([^)]*\+', content):
            features['has_sql_concat'] = 1.0
        shell_patterns = ['os.system(', 'subprocess.', 'shell=True']
        for pattern in shell_patterns:
            if pattern in content:
                features['has_shell_execution'] = 1.0
                break
        if 'pickle.loads' in content or 'pickle.load' in content:
            features['has_pickle_usage'] = 1.0
        weak_crypto = ['hashlib.md5', 'hashlib.sha1', 'DES.new']
        for crypto in weak_crypto:
            if crypto in content:
                features['has_weak_crypto'] = 1.0
                break
        risk_factors = [
            features['has_hardcoded_secrets'],
            features['has_dangerous_functions'],
            features['has_sql_concat'],
            features['has_shell_execution'],
            features['has_pickle_usage'],
            features['has_weak_crypto']
        ]
        features['security_risk_score'] = sum(risk_factors) / len(risk_factors)
        return features
    def _extract_complexity_features(self, content: str, file_path: Path) -> Dict[str, float]:
        features = {
            'cyclomatic_complexity': 0.0,
            'cognitive_complexity': 0.0,
            'nesting_depth': 0.0,
            'function_length_avg': 0.0,
            'parameter_count_avg': 0.0
        }
        try:
            tree = ast.parse(content)
            complexity = 1
            max_nesting = 0
            function_lengths = []
            param_counts = []
            for node in ast.walk(tree):
                if isinstance(node, (ast.If, ast.For, ast.While, ast.ExceptHandler)):
                    complexity += 1
                if isinstance(node, (ast.And, ast.Or)):
                    complexity += 1
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if hasattr(node, 'end_lineno'):
                        func_length = node.end_lineno - node.lineno + 1
                        function_lengths.append(func_length)
                    param_counts.append(len(node.args.args))
            depth = self._get_node_depth(node)
            max_nesting = max(max_nesting, depth)
            features['cyclomatic_complexity'] = min(complexity / 50.0, 1.0)
            features['nesting_depth'] = min(max_nesting / 10.0, 1.0)
            if function_lengths:
                features['function_length_avg'] = min(sum(function_lengths) / len(function_lengths) / 100.0, 1.0)
            if param_counts:
                features['parameter_count_avg'] = min(sum(param_counts) / len(param_counts) / 10.0, 1.0)
        except SyntaxError:
            pass
        return features
    def _extract_semantic_features(self, content: str, file_path: Path) -> Dict[str, float]:
        features = {
            'data_flow_complexity': 0.0,
            'api_usage': 0.0,
            'database_usage': 0.0,
            'file_io_usage': 0.0,
            'network_usage': 0.0
        }
        api_patterns = ['@app.route', '@api_view', 'FastAPI', 'flask.', 'django.']
        for pattern in api_patterns:
            if pattern in content:
                features['api_usage'] = 1.0
                break
        db_patterns = ['sqlite3', 'sqlalchemy', 'pymongo', 'redis', 'database']
        for pattern in db_patterns:
            if pattern in content:
                features['database_usage'] = 1.0
                break
        io_patterns = ['open(', 'read(', 'write(', 'Path(', 'os.path']
        for pattern in io_patterns:
            if pattern in content:
                features['file_io_usage'] = 1.0
                break
        net_patterns = ['requests.', 'urllib', 'httpx', 'aiohttp', 'socket.']
        for pattern in net_patterns:
            if pattern in content:
                features['network_usage'] = 1.0
                break
        features['data_flow_complexity'] = sum([
            features['api_usage'],
            features['database_usage'],
            features['file_io_usage'],
            features['network_usage']
        ]) / 4.0
        return features
    def _analyze_data_flow(self, content: str, file_path: Path) -> Dict[str, Any]:
        return {
            'has_input_validation': bool(re.search(r'if\s+.*\s*(isinstance|type|hasattr)', content)),
            'has_output_sanitization': bool(re.search(r'(escape|sanitize|clean)', content, re.IGNORECASE)),
            'has_error_handling': 'try:' in content and 'except' in content
        }
    def _analyze_control_flow(self, content: str, file_path: Path) -> Dict[str, Any]:
        return {
            'has_loops': bool(re.search(r'\b(for|while)\b', content)),
            'has_conditionals': bool(re.search(r'\bif\b', content)),
            'has_exceptions': 'try:' in content,
            'has_recursion': bool(re.search(r'\bdef\s+(\w+)\s*\(.*\n.*\1\(', content, re.DOTALL))
        }
    def _analyze_dependency_graph(self, content: str, file_path: Path) -> Dict[str, Any]:
        try:
            tree = ast.parse(content)
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name.split('.')[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module.split('.')[0])
            return {
                'dependency_count': len(set(imports)),
                'has_circular_dependency_risk': len(imports) != len(set(imports))
            }
        except SyntaxError:
            return {'dependency_count': 0}
    def enhanced_match(
        self,
        content: str,
        file_path: Path,
        use_cache: bool = True
    ) -> List[StrategyMatch]:
        cache_key = f"{hash(content)}:{file_path}"
        if use_cache and cache_key in self._match_cache:
            return self._match_cache[cache_key]
        context = self._gather_context(content, file_path)
        features = self._extract_features(content, file_path)
        semantic_info = self._gather_semantic_info(content, file_path)
        base_matches = self.intelligent_match(content, file_path, context)
        enhanced_matches = []
        for match in base_matches:
            feature_score = self._calculate_feature_score(match, features)
            context_score = self._calculate_context_score(match, context)
            semantic_score = self._calculate_semantic_score(match, semantic_info)
            history_score = self._calculate_history_score(match.strategy_id)
            weights = self._get_adaptive_weights(features, context)
            final_confidence = (
                match.confidence * weights['base'] +
                feature_score * weights['feature'] +
                context_score * weights['context'] +
                semantic_score * weights['semantic'] +
                history_score * weights['history']
            )
            enhanced_match = StrategyMatch(
                strategy_id=match.strategy_id,
                result=match.result,
                confidence=min(final_confidence, 1.0),
                matched_patterns=match.matched_patterns,
                issues_found=match.issues_found,
                metadata={
                    **match.metadata,
                    'feature_score': feature_score,
                    'context_score': context_score,
                    'semantic_score': semantic_score,
                    'history_score': history_score,
                    'weights': weights,
                    'context': context,
                    'features': features
                },
                severity=match.severity,
                execution_time_ms=match.execution_time_ms,
                fix_suggestions=match.fix_suggestions
            )
            enhanced_matches.append(enhanced_match)
        enhanced_matches.sort(key=lambda m: (m.confidence, -len(m.issues_found)), reverse=True)
        if use_cache:
            self._update_cache(cache_key, enhanced_matches)
        return enhanced_matches
    def _gather_context(self, content: str, file_path: Path) -> Dict[str, Any]:
        context = {}
        for analyzer in self._context_analyzers:
            try:
                result = analyzer(content, file_path)
                context.update(result)
            except Exception as e:
                logger.debug(f"上下文分析器失败: {e}")
        return context
    def _extract_features(self, content: str, file_path: Path) -> Dict[str, float]:
        features = {}
        for extractor in self._feature_extractors:
            try:
                result = extractor(content, file_path)
                features.update(result)
            except Exception as e:
                logger.debug(f"特征提取器失败: {e}")
        return features
    def _gather_semantic_info(self, content: str, file_path: Path) -> Dict[str, Any]:
        semantic_info = {}
        for analyzer in self._semantic_analyzers:
            try:
                result = analyzer(content, file_path)
                semantic_info.update(result)
            except Exception as e:
                logger.debug(f"语义分析器失败: {e}")
        return semantic_info
    def _calculate_feature_score(
        self,
        match: StrategyMatch,
        features: Dict[str, float]
    ) -> float:
        strategy = self._library.get_strategy(match.strategy_id)
        if not strategy:
            return 0.0
        score = 0.0
        weight_sum = 0.0
        if strategy.category == StrategyCategory.SYNTAX:
            if features.get('has_syntax_errors', False):
                score += 1.0
            score += (1.0 - features.get('bracket_balance', 1.0)) * 0.5
            score += (1.0 - features.get('quote_balance', 1.0)) * 0.3
            weight_sum += 1.8
        elif strategy.category == StrategyCategory.IMPORT:
            score += features.get('import_count', 0.0)
            score += features.get('wildcard_import', 0.0) * 0.5
            score += features.get('relative_import_ratio', 0.0) * 0.3
            weight_sum += 1.8
        elif strategy.category == StrategyCategory.STYLE:
            score += (1.0 - features.get('indentation_consistency', 1.0))
            score += features.get('long_line_ratio', 0.0)
            score += features.get('trailing_whitespace_ratio', 0.0)
            score += (1.0 - features.get('docstring_coverage', 1.0)) * 0.3
            weight_sum += 22.3
        elif strategy.category == StrategyCategory.SECURITY:
            score += features.get('has_hardcoded_secrets', 0.0) * 1.5
            score += features.get('has_dangerous_functions', 0.0) * 1.2
            score += features.get('has_sql_concat', 0.0)
            score += features.get('has_shell_execution', 0.0)
            score += features.get('security_risk_score', 0.0)
            weight_sum += 4.7
        return min(score / weight_sum if weight_sum > 0 else 0.0, 1.0)
    def _calculate_context_score(
        self,
        match: StrategyMatch,
        context: Dict[str, Any]
    ) -> float:
        strategy = self._library.get_strategy(match.strategy_id)
        if not strategy:
            return 0.0
        score = 0.5
        if strategy.category == StrategyCategory.SYNTAX:
            if context.get('has_syntax_errors'):
                score += 0.3
            if context.get('has_indentation_errors'):
                score += 0.2
        elif strategy.category == StrategyCategory.STYLE:
            if context.get('is_test_file'):
                score += 0.1
            if context.get('line_count', 0) > 100:
                score += 0.1
        elif strategy.category == StrategyCategory.SECURITY:
            if context.get('is_config_file'):
                score += 0.3
            if context.get('has_hardcoded_secrets'):
                score += 0.2
        elif strategy.category == StrategyCategory.IMPORT:
            if context.get('import_count', 0) > 5:
                score += 0.2
            if context.get('relative_imports'):
                score += 0.1
        return min(score, 1.0)
    def _calculate_semantic_score(
        self,
        match: StrategyMatch,
        semantic_info: Dict[str, Any]
    ) -> float:
        strategy = self._library.get_strategy(match.strategy_id)
        if not strategy:
            return 0.0
        score = 0.5
        if strategy.category == StrategyCategory.SECURITY:
            if semantic_info.get('has_input_validation') is False:
                score += 0.2
            if semantic_info.get('has_error_handling') is False:
                score += 0.1
        elif strategy.category == StrategyCategory.SYNTAX:
            if semantic_info.get('has_recursion'):
                score += 0.1
        return min(score, 1.0)
    def _calculate_history_score(self, strategy_id: str) -> float:
        strategy = self._library.get_strategy(strategy_id)
        if not strategy:
            return 0.0
        effect = strategy.get_effect()
        if effect.total_applications == 0:
            return 0.5
        return effect.success_rate
    def _get_adaptive_weights(
        self,
        features: Dict[str, float],
        context: Dict[str, Any]
    ) -> Dict[str, float]:
        weights = {
            'base': 0.3,
            'feature': 0.3,
            'context': 0.2,
            'semantic': 0.1,
            'history': 0.1
        }
        if features.get('security_risk_score', 0) > 0.5:
            weights['feature'] = 0.4
            weights['base'] = 0.2
        if context.get('has_syntax_errors'):
            weights['feature'] = 0.35
            weights['context'] = 0.25
        if context.get('is_test_file'):
            weights['history'] = 0.15
            weights['semantic'] = 0.05
        return weights
    def _update_cache(self, key: str, matches: List[StrategyMatch]) -> None:
        if len(self._match_cache) >= self._cache_max_size:
            oldest_key = next(iter(self._match_cache))
            del self._match_cache[oldest_key]
        self._match_cache[key] = matches
    def clear_cache(self) -> None:
        self._match_cache.clear()
    def get_cache_stats(self) -> Dict[str, int]:
        return {
            'cache_size': len(self._match_cache),
            'max_size': self._cache_max_size
        }
    def learn_from_feedback(
        self,
        match: StrategyMatch,
        actual_success: bool,
        user_feedback: Optional[float] = None
    ) -> None:
        super().record_match_feedback(match, actual_success, user_feedback)
        strategy = self._library.get_strategy(match.strategy_id)
        if strategy:
            self._update_pattern_embeddings(strategy, match, actual_success)
    def _update_pattern_embeddings(
        self,
        strategy: BaseStrategy,
        match: StrategyMatch,
        success: bool
    ) -> None:
        strategy_id = strategy.strategy_id
        if strategy_id not in self._pattern_embeddings:
            self._pattern_embeddings[strategy_id] = [0.5] * len(strategy.patterns)
        embeddings = self._pattern_embeddings[strategy_id]
        for i, pattern in enumerate(strategy.patterns):
            if i < len(embeddings):
                adjustment = 0.1 if success else -0.1
                embeddings[i] = max(0.1, min(0.9, embeddings[i] + adjustment))

    def _extract_syntax_features_old(self, content: str, file_path: Path) -> Dict[str, float]:
        """提取语法特征"""
        features = {
            'syntax_complexity': 0.0,
            'indentation_consistency': 1.0,
            'bracket_balance': 1.0
        }

        lines = content.split('\n')
        indentations = []
        for line in lines:
            if line.strip():
                indent = len(line) - len(line.lstrip())
                indentations.append(indent)

        if len(set(indentations)) > 1:
            features['indentation_consistency'] = 0.8

        open_brackets = content.count('(') + content.count('[') + content.count('{')
        close_brackets = content.count(')') + content.count(']') + content.count('}')
        if open_brackets != close_brackets:
            features['bracket_balance'] = 0.5

        return features

    def _extract_import_features(self, content: str, file_path: Path) -> Dict[str, float]:
        """提取导入特征"""
        features = {
            'import_count': 0.0,
            'from_import_ratio': 0.0,
            'wildcard_import': 0.0
        }

        import_lines = [line for line in content.split('\n') if line.strip().startswith(('import ', 'from '))]
        features['import_count'] = len(import_lines) / 10.0

        from_imports = sum(1 for line in import_lines if line.strip().startswith('from '))
        if import_lines:
            features['from_import_ratio'] = from_imports / len(import_lines)

        if 'import *' in content:
            features['wildcard_import'] = 1.0

        return features

    def _extract_style_features(self, content: str, file_path: Path) -> Dict[str, float]:
        """提取风格特征"""
        lines = content.split('\n')
        features = {
            'avg_line_length': 0.0,
            'long_line_ratio': 0.0,
            'trailing_whitespace_ratio': 0.0,
            'empty_line_ratio': 0.0
        }

        if lines:
            total_length = sum(len(line) for line in lines)
            features['avg_line_length'] = total_length / len(lines) / 100.0

            long_lines = sum(1 for line in lines if len(line) > 120)
            features['long_line_ratio'] = long_lines / len(lines)

            trailing_whitespace = sum(1 for line in lines if line != line.rstrip())
            features['trailing_whitespace_ratio'] = trailing_whitespace / len(lines)

            empty_lines = sum(1 for line in lines if not line.strip())
            features['empty_line_ratio'] = empty_lines / len(lines)

        return features

    def _extract_security_features(self, content: str, file_path: Path) -> Dict[str, float]:
        """提取安全特征"""
        features = {
            'has_hardcoded_secrets': 0.0,
            'has_dangerous_functions': 0.0,
            'has_sql_concat': 0.0
        }

        secret_patterns = [
            r'password\s*=\s*[\'"]',
            r'api_key\s*=\s*[\'"]',
            r'secret\s*=\s*[\'"]'
        ]
        for pattern in secret_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                features['has_hardcoded_secrets'] = 1.0
                break

        dangerous_funcs = ['eval(', 'exec(', 'compile(']
        for func in dangerous_funcs:
            if func in content:
                features['has_dangerous_functions'] = 1.0
                break

        if re.search(r'execute\s*\([^)]*\+', content):
            features['has_sql_concat'] = 1.0

        return features

    def enhanced_match(
        self,
        content: str,
        file_path: Path,
        use_cache: bool = True
    ) -> List[StrategyMatch]:
        """增强型匹配 - 多特征融合"""
        cache_key = f"{hash(content)}:{file_path}"

        if use_cache and cache_key in self._match_cache:
            return self._match_cache[cache_key]

        context = self._gather_context(content, file_path)
        features = self._extract_features(content, file_path)

        base_matches = self.intelligent_match(content, file_path, context)

        enhanced_matches = []
        for match in base_matches:
            feature_score = self._calculate_feature_score(match, features)
            context_score = self._calculate_context_score(match, context)

            final_confidence = (
                match.confidence * 0.5 +
                feature_score * 0.3 +
                context_score * 0.2
            )

            enhanced_match = StrategyMatch(
                strategy_id=match.strategy_id,
                result=match.result,
                confidence=min(final_confidence, 1.0),
                matched_patterns=match.matched_patterns,
                issues_found=match.issues_found,
                metadata={
                    **match.metadata,
                    'feature_score': feature_score,
                    'context_score': context_score,
                    'context': context,
                    'features': features
                },
                severity=match.severity,
                execution_time_ms=match.execution_time_ms,
                fix_suggestions=match.fix_suggestions
            )
            enhanced_matches.append(enhanced_match)

        enhanced_matches.sort(key=lambda m: m.confidence, reverse=True)

        if use_cache:
            self._update_cache(cache_key, enhanced_matches)

        return enhanced_matches

    def _gather_context(self, content: str, file_path: Path) -> Dict[str, Any]:
        """收集上下文信息"""
        context = {}
        for analyzer in self._context_analyzers:
            try:
                result = analyzer(content, file_path)
                context.update(result)
            except Exception as e:
                logger.debug(f"上下文分析器失败: {e}")
        return context

    def _extract_features(self, content: str, file_path: Path) -> Dict[str, float]:
        """提取特征"""
        features = {}
        for extractor in self._feature_extractors:
            try:
                result = extractor(content, file_path)
                features.update(result)
            except Exception as e:
                logger.debug(f"特征提取器失败: {e}")
        return features

    def _calculate_feature_score(
        self,
        match: StrategyMatch,
        features: Dict[str, float]
    ) -> float:
        """计算特征得分"""
        strategy = self._library.get_strategy(match.strategy_id)
        if not strategy:
            return 0.0

        score = 0.0
        weight_sum = 0.0

        if strategy.category == StrategyCategory.SYNTAX:
            if features.get('has_syntax_errors', False):
                score += 1.0
            score += features.get('bracket_balance', 1.0) * 0.5
            weight_sum += 1.5

        elif strategy.category == StrategyCategory.IMPORT:
            score += features.get('import_count', 0.0)
            score += features.get('wildcard_import', 0.0)
            weight_sum += 2.0

        elif strategy.category == StrategyCategory.STYLE:
            score += 1.0 - features.get('indentation_consistency', 1.0)
            score += features.get('long_line_ratio', 0.0)
            score += features.get('trailing_whitespace_ratio', 0.0)
            weight_sum += 3.0

        elif strategy.category == StrategyCategory.SECURITY:
            score += features.get('has_hardcoded_secrets', 0.0)
            score += features.get('has_dangerous_functions', 0.0)
            score += features.get('has_sql_concat', 0.0)
            weight_sum += 3.0

        return score / weight_sum if weight_sum > 0 else 0.0

    def _calculate_context_score(
        self,
        match: StrategyMatch,
        context: Dict[str, Any]
    ) -> float:
        """计算上下文得分"""
        strategy = self._library.get_strategy(match.strategy_id)
        if not strategy:
            return 0.0

        score = 0.5

        if strategy.category == StrategyCategory.SYNTAX:
            if context.get('has_syntax_errors'):
                score += 0.5

        elif strategy.category == StrategyCategory.STYLE:
            if context.get('is_test_file'):
                score += 0.2

        return min(score, 1.0)

    def _update_cache(self, key: str, matches: List[StrategyMatch]) -> None:
        """更新缓存"""
        if len(self._match_cache) >= self._cache_max_size:
            oldest_key = next(iter(self._match_cache))
            del self._match_cache[oldest_key]

        self._match_cache[key] = matches

    def clear_cache(self) -> None:
        """清空缓存"""
        self._match_cache.clear()

    def get_cache_stats(self) -> Dict[str, int]:
        """获取缓存统计"""
        return {
            'cache_size': len(self._match_cache),
            'max_size': self._cache_max_size
        }


class AdvancedEffectEvaluator(StrategyEffectEvaluator):
    """高级策略效果评估器 - 详细指标和时间序列分析"""

    def __init__(self, library: StrategyLibrary):
        super().__init__(library)
        self._time_series_data: Dict[str, List[Dict[str, Any]]] = {}
        self._benchmark_data: Dict[str, Dict[str, float]] = {}
        self._optimization_suggestions: Dict[str, List[str]] = {}

    def evaluate_with_time_series(
        self,
        strategy_id: str,
        time_granularity: str = 'hour'
    ) -> Dict[str, Any]:
        """带时间序列的评估"""
        base_evaluation = self.evaluate_comprehensive(strategy_id)

        time_series = self._build_time_series(strategy_id, time_granularity)

        trends = self._analyze_time_series_trends(time_series)

        return {
            **base_evaluation,
            'time_series': time_series,
            'trend_analysis': trends,
            'granularity': time_granularity
        }

    def _build_time_series(
        self,
        strategy_id: str,
        granularity: str
    ) -> List[Dict[str, Any]]:
        """构建时间序列数据"""
        history = self._evaluation_history.get(strategy_id, [])

        if not history:
            return []

        grouped_data: Dict[str, List[Dict[str, Any]]] = {}

        for entry in history:
            timestamp = datetime.fromisoformat(entry['timestamp'])

            if granularity == 'hour':
                key = timestamp.strftime('%Y-%m-%d %H:00')
            elif granularity == 'day':
                key = timestamp.strftime('%Y-%m-%d')
            elif granularity == 'week':
                key = timestamp.strftime('%Y-W%W')
            else:
                key = timestamp.strftime('%Y-%m-%d %H:00')

            if key not in grouped_data:
                grouped_data[key] = []
            grouped_data[key].append(entry)

        time_series = []
        for key in sorted(grouped_data.keys()):
            entries = grouped_data[key]
            avg_effectiveness = sum(
                e['metrics']['basic_metrics']['effectiveness_score']
                for e in entries
            ) / len(entries)

            avg_success_rate = sum(
                e['metrics']['basic_metrics']['success_rate']
                for e in entries
            ) / len(entries)

            time_series.append({
                'period': key,
                'avg_effectiveness': avg_effectiveness,
                'avg_success_rate': avg_success_rate,
                'sample_count': len(entries)
            })

        return time_series

    def _analyze_time_series_trends(
        self,
        time_series: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """分析时间序列趋势"""
        if len(time_series) < 2:
            return {'trend': 'insufficient_data'}

        effectiveness_values = [t['avg_effectiveness'] for t in time_series]
        success_values = [t['avg_success_rate'] for t in time_series]

        effectiveness_trend = self._calculate_trend_direction(effectiveness_values)
        success_trend = self._calculate_trend_direction(success_values)

        volatility = self._calculate_volatility(effectiveness_values)

        return {
            'effectiveness_trend': effectiveness_trend,
            'success_rate_trend': success_trend,
            'volatility': volatility,
            'data_points': len(time_series)
        }

    def _calculate_trend_direction(self, values: List[float]) -> str:
        """计算趋势方向"""
        if len(values) < 2:
            return 'stable'

        first_half = values[:len(values)//2]
        second_half = values[len(values)//2:]

        first_avg = sum(first_half) / len(first_half)
        second_avg = sum(second_half) / len(second_half)

        change = (second_avg - first_avg) / max(first_avg, 0.001)

        if change > 0.1:
            return 'improving'
        elif change < -0.1:
            return 'declining'
        else:
            return 'stable'

    def _calculate_volatility(self, values: List[float]) -> float:
        """计算波动性"""
        if len(values) < 2:
            return 0.0

        avg = sum(values) / len(values)
        variance = sum((v - avg) ** 2 for v in values) / len(values)
        return variance ** 0.5

    def generate_optimization_suggestions(
        self,
        strategy_id: str
    ) -> List[str]:
        """生成优化建议"""
        evaluation = self.evaluate_comprehensive(strategy_id)
        suggestions = []

        basic_metrics = evaluation.get('basic_metrics', {})
        advanced_metrics = evaluation.get('advanced_metrics', {})
        trend_analysis = evaluation.get('trend_analysis', {})

        if basic_metrics.get('success_rate', 1.0) < 0.5:
            suggestions.append("成功率低于50%，建议检查策略模式匹配规则是否过于宽泛")

        if basic_metrics.get('precision', 1.0) < 0.7:
            suggestions.append("精确度较低，存在较多误报，建议收紧匹配条件")

        if basic_metrics.get('recall', 1.0) < 0.7:
            suggestions.append("召回率较低，可能遗漏部分问题，建议扩展匹配模式")

        if advanced_metrics.get('stability', 1.0) < 0.8:
            suggestions.append("稳定性不足，建议增加前置条件检查")

        if advanced_metrics.get('execution_stability', 1.0) < 0.8:
            suggestions.append("执行时间波动较大，建议优化策略执行逻辑")

        if trend_analysis.get('trend') == 'declining':
            suggestions.append("效果呈下降趋势，建议重新评估策略适用性")

        if basic_metrics.get('f1_score', 1.0) < 0.6:
            suggestions.append("F1分数较低，建议同时优化精确度和召回率")

        if not suggestions:
            suggestions.append("策略表现良好，建议继续保持当前配置")

        self._optimization_suggestions[strategy_id] = suggestions
        return suggestions

    def compare_strategies(
        self,
        strategy_ids: List[str]
    ) -> Dict[str, Any]:
        """比较多个策略的效果"""
        comparisons = {}

        for sid in strategy_ids:
            evaluation = self.evaluate_comprehensive(sid)
            comparisons[sid] = {
                'effectiveness_score': evaluation.get('basic_metrics', {}).get('effectiveness_score', 0),
                'success_rate': evaluation.get('basic_metrics', {}).get('success_rate', 0),
                'f1_score': evaluation.get('basic_metrics', {}).get('f1_score', 0),
                'stability': evaluation.get('advanced_metrics', {}).get('stability', 0)
            }

        rankings = {
            'by_effectiveness': sorted(strategy_ids, key=lambda x: comparisons[x]['effectiveness_score'], reverse=True),
            'by_success_rate': sorted(strategy_ids, key=lambda x: comparisons[x]['success_rate'], reverse=True),
            'by_f1_score': sorted(strategy_ids, key=lambda x: comparisons[x]['f1_score'], reverse=True),
            'by_stability': sorted(strategy_ids, key=lambda x: comparisons[x]['stability'], reverse=True)
        }

        return {
            'comparisons': comparisons,
            'rankings': rankings
        }

    def set_benchmark(
        self,
        strategy_id: str,
        metrics: Dict[str, float]
    ) -> None:
        """设置基准指标"""
        self._benchmark_data[strategy_id] = metrics

    def compare_to_benchmark(
        self,
        strategy_id: str
    ) -> Dict[str, Any]:
        """与基准比较"""
        if strategy_id not in self._benchmark_data:
            return {'error': 'No benchmark set for this strategy'}

        evaluation = self.evaluate_comprehensive(strategy_id)
        benchmark = self._benchmark_data[strategy_id]

        comparison = {}
        for metric, benchmark_value in benchmark.items():
            actual_value = evaluation.get('basic_metrics', {}).get(metric, 0)
            comparison[metric] = {
                'actual': actual_value,
                'benchmark': benchmark_value,
                'difference': actual_value - benchmark_value,
                'meets_benchmark': actual_value >= benchmark_value
            }

        return comparison

    def get_optimization_suggestions(self, strategy_id: str) -> List[str]:
        """获取优化建议"""
        return self._optimization_suggestions.get(strategy_id, [])


class AdvancedAutoLearner(StrategyAutoLearner):
    """高级策略自动学习器 - 在线学习和模式挖掘"""

    def __init__(self, library: StrategyLibrary):
        super().__init__(library)
        self._pattern_miner = PatternMiner()
        self._online_learner = OnlineLearner()
        self._strategy_generator = StrategyGenerator(library)
        self._learning_queue: List[Dict[str, Any]] = []
        self._batch_size: int = 50

    def record_learning_data_batch(
        self,
        data_list: List[Dict[str, Any]]
    ) -> None:
        """批量记录学习数据"""
        for data in data_list:
            self._learning_queue.append(data)

        if len(self._learning_queue) >= self._batch_size:
            self._process_learning_batch()

    def _process_learning_batch(self) -> None:
        """处理学习批次"""
        if not self._learning_queue:
            return

        batch = self._learning_queue[:self._batch_size]
        self._learning_queue = self._learning_queue[self._batch_size:]

        for data in batch:
            super().record_learning_data(
                data['strategy_id'],
                data['content'],
                data['issues'],
                data['fix_result']
            )

        self._run_advanced_learning(batch)

    def _run_advanced_learning(self, batch: List[Dict[str, Any]]) -> None:
        """运行高级学习"""
        self._pattern_miner.mine_patterns(batch)

        self._online_learner.update(batch)

        new_patterns = self._pattern_miner.get_discovered_patterns()
        if new_patterns:
            self._strategy_generator.suggest_new_strategies(new_patterns)

    def discover_new_patterns(
        self,
        min_support: float = 0.3
    ) -> List[Dict[str, Any]]:
        """发现新模式"""
        return self._pattern_miner.get_discovered_patterns(min_support)

    def get_pattern_confidence(
        self,
        pattern: str
    ) -> float:
        """获取模式置信度"""
        return self._pattern_miner.get_pattern_confidence(pattern)

    def generate_new_strategy(
        self,
        pattern: str,
        category: StrategyCategory
    ) -> Optional[Dict[str, Any]]:
        """生成新策略"""
        return self._strategy_generator.generate_strategy(pattern, category)

    def get_learning_progress(self) -> Dict[str, Any]:
        """获取学习进度"""
        base_stats = self.get_learning_statistics()

        return {
            **base_stats,
            'queue_size': len(self._learning_queue),
            'discovered_patterns_count': len(self._pattern_miner.get_discovered_patterns()),
            'online_learner_state': self._online_learner.get_state()
        }

    def force_learning_cycle(self) -> Dict[str, Any]:
        """强制执行学习周期"""
        if self._learning_queue:
            self._process_learning_batch()

        self._run_learning_cycle()

        return {
            'processed': True,
            'discovered_patterns': len(self._pattern_miner.get_discovered_patterns()),
            'timestamp': datetime.now().isoformat()
        }


class PatternMiner:
    """模式挖掘器 - 从数据中发现新模式"""

    def __init__(self):
        self._discovered_patterns: Dict[str, Dict[str, Any]] = {}
        self._pattern_frequency: Dict[str, int] = {}
        self._pattern_success_rate: Dict[str, float] = {}
        self._min_confidence: float = 0.6

    def mine_patterns(
        self,
        data_batch: List[Dict[str, Any]]
    ) -> None:
        """挖掘模式"""
        for data in data_batch:
            issues = data.get('issues', [])
            success = data.get('fix_result', {}).get('success', False)

            for issue in issues:
                pattern = self._extract_pattern(issue)
                if pattern:
                    self._update_pattern_stats(pattern, success)

        self._identify_high_value_patterns()

    def _extract_pattern(
        self,
        issue: Dict[str, Any]
    ) -> Optional[str]:
        """从问题中提取模式"""
        pattern = issue.get('pattern', '')
        if not pattern:
            match_text = issue.get('match_text', '')
            if match_text and len(match_text) > 5:
                pattern = self._generalize_pattern(match_text)

        return pattern if pattern else None

    def _generalize_pattern(
        self,
        text: str
    ) -> str:
        """泛化模式"""
        generalized = re.sub(r'\d+', r'\\d+', text)
        generalized = re.sub(r'\'[^\']*\'', r'\'.*\'', generalized)
        generalized = re.sub(r'"[^"]*"', r'".*"', generalized)

        return generalized

    def _update_pattern_stats(
        self,
        pattern: str,
        success: bool
    ) -> None:
        """更新模式统计"""
        self._pattern_frequency[pattern] = self._pattern_frequency.get(pattern, 0) + 1

        current_rate = self._pattern_success_rate.get(pattern, 0.5)
        count = self._pattern_frequency[pattern]
        new_rate = (current_rate * (count - 1) + (1.0 if success else 0.0)) / count
        self._pattern_success_rate[pattern] = new_rate

    def _identify_high_value_patterns(self) -> None:
        """识别高价值模式"""
        for pattern, frequency in self._pattern_frequency.items():
            success_rate = self._pattern_success_rate.get(pattern, 0)

            if frequency >= 3 and success_rate >= self._min_confidence:
                if pattern not in self._discovered_patterns:
                    self._discovered_patterns[pattern] = {
                        'pattern': pattern,
                        'frequency': frequency,
                        'success_rate': success_rate,
                        'discovered_at': datetime.now().isoformat(),
                        'confidence': success_rate * min(frequency / 10.0, 1.0)
                    }

    def get_discovered_patterns(
        self,
        min_confidence: float = 0.0
    ) -> List[Dict[str, Any]]:
        """获取发现的模式"""
        patterns = list(self._discovered_patterns.values())
        return [p for p in patterns if p['confidence'] >= min_confidence]

    def get_pattern_confidence(
        self,
        pattern: str
    ) -> float:
        """获取模式置信度"""
        if pattern in self._discovered_patterns:
            return self._discovered_patterns[pattern]['confidence']
        return 0.0

    def reset(self) -> None:
        """重置挖掘器"""
        self._discovered_patterns.clear()
        self._pattern_frequency.clear()
        self._pattern_success_rate.clear()


class OnlineLearner:
    """在线学习器 - 实时更新学习模型"""

    def __init__(self):
        self._model_weights: Dict[str, float] = {}
        self._learning_rate: float = 0.01
        self._update_count: int = 0
        self._recent_errors: List[float] = []

    def update(
        self,
        data_batch: List[Dict[str, Any]]
    ) -> None:
        """更新模型"""
        for data in data_batch:
            features = self._extract_features(data)
            target = 1.0 if data.get('fix_result', {}).get('success', False) else 0.0

            prediction = self._predict(features)
            error = target - prediction

            self._update_weights(features, error)
            self._recent_errors.append(abs(error))

        self._update_count += len(data_batch)

        if len(self._recent_errors) > 100:
            self._recent_errors = self._recent_errors[-100:]

    def _extract_features(
        self,
        data: Dict[str, Any]
    ) -> Dict[str, float]:
        """提取特征"""
        features = {
            'issue_count': len(data.get('issues', [])),
            'has_pattern': 1.0 if any('pattern' in i for i in data.get('issues', [])) else 0.0,
            'content_length': len(str(data.get('content', ''))) / 1000.0
        }

        return features

    def _predict(
        self,
        features: Dict[str, float]
    ) -> float:
        """预测"""
        prediction = 0.0
        for feature, value in features.items():
            weight = self._model_weights.get(feature, 0.5)
            prediction += weight * value

        return max(0.0, min(1.0, prediction / max(len(features), 1)))

    def _update_weights(
        self,
        features: Dict[str, float],
        error: float
    ) -> None:
        """更新权重"""
        for feature, value in features.items():
            current_weight = self._model_weights.get(feature, 0.5)
            gradient = error * value
            new_weight = current_weight + self._learning_rate * gradient
            self._model_weights[feature] = max(0.0, min(1.0, new_weight))

    def get_state(self) -> Dict[str, Any]:
        """获取状态"""
        avg_error = sum(self._recent_errors) / len(self._recent_errors) if self._recent_errors else 0.0

        return {
            'update_count': self._update_count,
            'feature_count': len(self._model_weights),
            'average_error': avg_error,
            'weights': self._model_weights.copy()
        }

    def reset(self) -> None:
        """重置学习器"""
        self._model_weights.clear()
        self._update_count = 0
        self._recent_errors.clear()


class StrategyGenerator:
    """策略生成器 - 自动生成新策略"""

    def __init__(self, library: StrategyLibrary):
        self._library = library
        self._generated_strategies: List[Dict[str, Any]] = []
        self._strategy_counter: int = 0

    def generate_strategy(
        self,
        pattern: str,
        category: StrategyCategory
    ) -> Optional[Dict[str, Any]]:
        """生成策略"""
        self._strategy_counter += 1
        strategy_id = f"auto_generated_{self._strategy_counter:04d}"

        strategy_data = {
            'strategy_id': strategy_id,
            'name': f"自动生成策略 - {category.value}",
            'description': f"基于模式 '{pattern[:50]}...' 自动生成的策略",
            'category': category,
            'priority': StrategyPriority.MEDIUM,
            'patterns': [pattern],
            'generated_at': datetime.now().isoformat(),
            'status': 'suggested'
        }

        self._generated_strategies.append(strategy_data)
        return strategy_data

    def suggest_new_strategies(
        self,
        patterns: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """建议新策略"""
        suggestions = []

        for pattern_data in patterns:
            pattern = pattern_data.get('pattern', '')
            if not pattern:
                continue

            category = self._infer_category(pattern)
            strategy = self.generate_strategy(pattern, category)
            if strategy:
                suggestions.append(strategy)

        return suggestions

    def _infer_category(
        self,
        pattern: str
    ) -> StrategyCategory:
        """推断策略类别"""
        syntax_indicators = ['syntax', 'error', 'parse', 'indent', 'colon', 'bracket']
        import_indicators = ['import', 'from', 'module', 'package']
        style_indicators = ['style', 'whitespace', 'line', 'format']
        security_indicators = ['password', 'secret', 'sql', 'eval', 'exec']

        pattern_lower = pattern.lower()

        for indicator in syntax_indicators:
            if indicator in pattern_lower:
                return StrategyCategory.SYNTAX

        for indicator in import_indicators:
            if indicator in pattern_lower:
                return StrategyCategory.IMPORT

        for indicator in style_indicators:
            if indicator in pattern_lower:
                return StrategyCategory.STYLE

        for indicator in security_indicators:
            if indicator in pattern_lower:
                return StrategyCategory.SECURITY

        return StrategyCategory.CUSTOM

    def get_generated_strategies(self) -> List[Dict[str, Any]]:
        """获取生成的策略"""
        return self._generated_strategies.copy()

    def apply_generated_strategy(
        self,
        strategy_data: Dict[str, Any]
    ) -> bool:
        """应用生成的策略"""
        def default_apply(content: str, issues: List[Dict[str, Any]]) -> Tuple[str, List[Dict[str, Any]]]:
            fixes = []
            for issue in issues:
                fixes.append({
                    'type': 'auto_generated_fix',
                    'line': issue.get('line', 0),
                    'message': '自动生成策略修复'
                })
            return content, fixes

        return self._library.register_custom_strategy(
            strategy_id=strategy_data['strategy_id'],
            name=strategy_data['name'],
            description=strategy_data['description'],
            category=strategy_data['category'],
            patterns=strategy_data['patterns'],
            apply_func=default_apply,
            priority=strategy_data['priority']
        )


class EnhancedStrategyOrchestrator(StrategyOrchestrator):
    """增强型策略编排器 - 整合所有增强功能"""

    def __init__(self, library: StrategyLibrary):
        super().__init__(library)
        self._lifecycle_manager = StrategyLifecycleManager(library)
        self._enhanced_matcher = EnhancedIntelligentMatcher(library)
        self._advanced_evaluator = AdvancedEffectEvaluator(library)
        self._advanced_learner = AdvancedAutoLearner(library)

    def orchestrate_fix_enhanced(
        self,
        content: str,
        file_path: Path,
        max_strategies: int = 5,
        use_learning: bool = True,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """增强型编排修复"""
        matches = self._enhanced_matcher.enhanced_match(content, file_path, use_cache)

        active_matches = [
            m for m in matches
            if self._is_strategy_active(m.strategy_id)
        ]

        top_matches = active_matches[:max_strategies]

        execution_plan = self._create_execution_plan(top_matches)

        result = {
            'original_content': content,
            'fixed_content': content,
            'execution_plan': execution_plan,
            'applied_strategies': [],
            'failed_strategies': [],
            'all_fixes': [],
            'learning_applied': use_learning,
            'cache_used': use_cache,
            'match_count': len(matches),
            'active_match_count': len(active_matches)
        }

        current_content = content
        for plan_item in execution_plan:
            strategy_id = plan_item['strategy_id']
            match = plan_item['match']

            try:
                fixed_content, fixes = self._library.apply_strategy(
                    strategy_id,
                    current_content,
                    match.issues_found
                )

                result['applied_strategies'].append(strategy_id)
                result['all_fixes'].extend(fixes)
                current_content = fixed_content

                if use_learning:
                    self._advanced_learner.record_learning_data(
                        strategy_id,
                        content,
                        match.issues_found,
                        {'success': True, 'fixes': fixes}
                    )

                self._lifecycle_manager._record_lifecycle_event(
                    strategy_id,
                    'applied',
                    {'fixes_count': len(fixes)}
                )

            except Exception as e:
                result['failed_strategies'].append({
                    'strategy_id': strategy_id,
                    'error': str(e)
                })

                if use_learning:
                    self._advanced_learner.record_learning_data(
                        strategy_id,
                        content,
                        match.issues_found,
                        {'success': False, 'error': str(e)}
                    )

        result['fixed_content'] = current_content

        return result

    def _is_strategy_active(
        self,
        strategy_id: str
    ) -> bool:
        """检查策略是否活跃"""
        strategy = self._library.get_strategy(strategy_id)
        return strategy is not None and strategy.status == StrategyStatus.ACTIVE

    def get_lifecycle_manager(self) -> StrategyLifecycleManager:
        """获取生命周期管理器"""
        return self._lifecycle_manager

    def get_enhanced_matcher(self) -> EnhancedIntelligentMatcher:
        """获取增强型匹配器"""
        return self._enhanced_matcher

    def get_advanced_evaluator(self) -> AdvancedEffectEvaluator:
        """获取高级评估器"""
        return self._advanced_evaluator

    def get_advanced_learner(self) -> AdvancedAutoLearner:
        """获取高级学习器"""
        return self._advanced_learner

    def get_comprehensive_report(self) -> Dict[str, Any]:
        """获取综合报告"""
        return {
            'execution_statistics': self.get_execution_statistics(),
            'learning_progress': self._advanced_learner.get_learning_progress(),
            'cache_statistics': self._enhanced_matcher.get_cache_stats(),
            'active_strategies': len(self._lifecycle_manager.get_active_strategies()),
            'deprecated_strategies': len(self._lifecycle_manager.get_deprecated_strategies()),
            'experimental_strategies': len(self._lifecycle_manager.get_experimental_strategies()),
            'templates_count': len(self._lifecycle_manager.list_templates())
        }


class DynamicPriorityManager:
    """动态策略优先级管理器 - 智能调整策略执行优先级"""

    def __init__(self, library: StrategyLibrary):
        self._library = library
        self._priority_history: Dict[str, List[Dict[str, Any]]] = {}
        self._adjustment_rules: List[Callable[[str, Dict[str, Any]], Optional[int]]] = []
        self._priority_weights: Dict[str, float] = {
            'success_rate': 0.3,
            'execution_speed': 0.2,
            'recent_usage': 0.2,
            'user_feedback': 0.15,
            'error_rate': 0.15
        }
        self._adjustment_interval: int = 100
        self._adjustment_count: int = 0
        self._initialize_default_rules()

    def _initialize_default_rules(self) -> None:
        self._adjustment_rules = [
            self._rule_success_rate_based,
            self._rule_execution_speed_based,
            self._rule_error_rate_based,
            self._rule_usage_frequency_based,
            self._rule_user_feedback_based,
            self._rule_category_priority,
            self._rule_time_decay
        ]

    def _rule_success_rate_based(self, strategy_id: str, metrics: Dict[str, Any]) -> Optional[int]:
        success_rate = metrics.get('success_rate', 0.5)
        if success_rate >= 0.9:
            return 2
        elif success_rate >= 0.7:
            return 1
        elif success_rate < 0.3:
            return -2
        elif success_rate < 0.5:
            return -1
        return None

    def _rule_execution_speed_based(self, strategy_id: str, metrics: Dict[str, Any]) -> Optional[int]:
        avg_time = metrics.get('average_execution_time', 100)
        if avg_time < 10:
            return 1
        elif avg_time > 500:
            return -1
        return None

    def _rule_error_rate_based(self, strategy_id: str, metrics: Dict[str, Any]) -> Optional[int]:
        error_rate = metrics.get('error_rate', 0)
        if error_rate > 0.3:
            return -2
        elif error_rate > 0.1:
            return -1
        return None

    def _rule_usage_frequency_based(self, strategy_id: str, metrics: Dict[str, Any]) -> Optional[int]:
        usage_count = metrics.get('usage_count', 0)
        if usage_count > 100:
            return 1
        elif usage_count < 5:
            return -1
        return None

    def _rule_user_feedback_based(self, strategy_id: str, metrics: Dict[str, Any]) -> Optional[int]:
        feedback_score = metrics.get('user_feedback_score', 0.5)
        if feedback_score >= 0.8:
            return 2
        elif feedback_score >= 0.6:
            return 1
        elif feedback_score < 0.3:
            return -2
        elif feedback_score < 0.5:
            return -1
        return None

    def _rule_category_priority(self, strategy_id: str, metrics: Dict[str, Any]) -> Optional[int]:
        strategy = self._library.get_strategy(strategy_id)
        if not strategy:
            return None
        category = strategy.category
        if category == StrategyCategory.SECURITY:
            return 2
        elif category == StrategyCategory.SYNTAX:
            return 1
        return None

    def _rule_time_decay(self, strategy_id: str, metrics: Dict[str, Any]) -> Optional[int]:
        last_used = metrics.get('last_used_timestamp')
        if last_used:
            try:
                last_used_dt = datetime.fromisoformat(last_used)
                days_since_use = (datetime.now() - last_used_dt).days
                if days_since_use > 30:
                    return -1
                elif days_since_use > 60:
                    return -2
            except (ValueError, TypeError):
                pass
        return None

    def calculate_dynamic_priority(self, strategy_id: str) -> int:
        strategy = self._library.get_strategy(strategy_id)
        if not strategy:
            return 0
        base_priority = strategy.priority.value
        effect = strategy.get_effect()
        metrics = {
            'success_rate': effect.success_rate if effect.total_applications > 0 else 0.5,
            'average_execution_time': effect.average_execution_time,
            'error_rate': 1 - effect.success_rate if effect.total_applications > 0 else 0,
            'usage_count': effect.total_applications,
            'user_feedback_score': 0.5,
            'last_used_timestamp': None
        }
        total_adjustment = 0
        for rule in self._adjustment_rules:
            try:
                adjustment = rule(strategy_id, metrics)
                if adjustment is not None:
                    total_adjustment += adjustment
            except Exception as e:
                logger.debug(f"优先级规则执行失败: {e}")
        new_priority = max(1, min(10, base_priority + total_adjustment))
        return new_priority

    def adjust_all_priorities(self) -> Dict[str, int]:
        adjustments = {}
        strategies = self._library.get_all_strategies()
        for strategy in strategies:
            old_priority = strategy.priority.value
            new_priority = self.calculate_dynamic_priority(strategy.strategy_id)
            if new_priority != old_priority:
                adjustments[strategy.strategy_id] = new_priority
                self._record_priority_change(strategy.strategy_id, old_priority, new_priority)
        self._adjustment_count += 1
        return adjustments

    def _record_priority_change(self, strategy_id: str, old_priority: int, new_priority: int) -> None:
        if strategy_id not in self._priority_history:
            self._priority_history[strategy_id] = []
        self._priority_history[strategy_id].append({
            'timestamp': datetime.now().isoformat(),
            'old_priority': old_priority,
            'new_priority': new_priority,
            'change': new_priority - old_priority
        })

    def get_priority_history(self, strategy_id: str) -> List[Dict[str, Any]]:
        return self._priority_history.get(strategy_id, [])

    def get_priority_trend(self, strategy_id: str) -> str:
        history = self.get_priority_history(strategy_id)
        if len(history) < 2:
            return 'stable'
        recent_changes = [h['change'] for h in history[-5:]]
        avg_change = sum(recent_changes) / len(recent_changes)
        if avg_change > 0.5:
            return 'increasing'
        elif avg_change < -0.5:
            return 'decreasing'
        return 'stable'

    def set_priority_weight(self, weight_name: str, weight_value: float) -> None:
        if weight_name in self._priority_weights:
            self._priority_weights[weight_name] = max(0.0, min(1.0, weight_value))
            total = sum(self._priority_weights.values())
            if total > 0:
                for key in self._priority_weights:
                    self._priority_weights[key] /= total

    def get_priority_weights(self) -> Dict[str, float]:
        return self._priority_weights.copy()

    def add_custom_rule(self, rule: Callable[[str, Dict[str, Any]], Optional[int]]) -> None:
        self._adjustment_rules.append(rule)

    def get_strategies_by_dynamic_priority(self) -> List[Tuple[str, int]]:
        strategies = self._library.get_all_strategies()
        priority_list = []
        for strategy in strategies:
            dynamic_priority = self.calculate_dynamic_priority(strategy.strategy_id)
            priority_list.append((strategy.strategy_id, dynamic_priority))
        priority_list.sort(key=lambda x: x[1], reverse=True)
        return priority_list

    def get_adjustment_statistics(self) -> Dict[str, Any]:
        total_adjustments = sum(len(h) for h in self._priority_history.values())
        strategies_adjusted = len(self._priority_history)
        increase_count = sum(
            1 for h in self._priority_history.values()
            for entry in h if entry['change'] > 0
        )
        decrease_count = sum(
            1 for h in self._priority_history.values()
            for entry in h if entry['change'] < 0
        )
        return {
            'total_adjustments': total_adjustments,
            'strategies_adjusted': strategies_adjusted,
            'increase_count': increase_count,
            'decrease_count': decrease_count,
            'adjustment_cycles': self._adjustment_count
        }

    def reset_priorities(self) -> None:
        strategies = self._library.get_all_strategies()
        for strategy in strategies:
            strategy.priority = StrategyPriority.MEDIUM
        self._priority_history.clear()
        self._adjustment_count = 0


class PriorityAwareOrchestrator(EnhancedStrategyOrchestrator):
    """优先级感知的策略编排器 - 整合动态优先级管理"""

    def __init__(self, library: StrategyLibrary):
        super().__init__(library)
        self._priority_manager = DynamicPriorityManager(library)

    def orchestrate_with_priority(
        self,
        content: str,
        file_path: Path,
        max_strategies: int = 5,
        use_dynamic_priority: bool = True
    ) -> Dict[str, Any]:
        if use_dynamic_priority:
            self._priority_manager.adjust_all_priorities()
        matches = self._enhanced_matcher.enhanced_match(content, file_path)
        if use_dynamic_priority:
            priority_order = self._priority_manager.get_strategies_by_dynamic_priority()
            priority_map = {sid: pri for sid, pri in priority_order}
            matches.sort(
                key=lambda m: (
                    priority_map.get(m.strategy_id, 0),
                    m.confidence
                ),
                reverse=True
            )
        top_matches = matches[:max_strategies]
        result = self.orchestrate_fix_enhanced(
            content,
            file_path,
            max_strategies,
            use_learning=True,
            use_cache=True
        )
        result['dynamic_priority_used'] = use_dynamic_priority
        if use_dynamic_priority:
            result['priority_adjustments'] = self._priority_manager.get_adjustment_statistics()
        return result

    def get_priority_manager(self) -> DynamicPriorityManager:
        return self._priority_manager

    def get_priority_report(self) -> Dict[str, Any]:
        priority_order = self._priority_manager.get_strategies_by_dynamic_priority()
        adjustment_stats = self._priority_manager.get_adjustment_statistics()
        trends = {}
        for sid, _ in priority_order[:10]:
            trends[sid] = self._priority_manager.get_priority_trend(sid)
        return {
            'priority_order': priority_order,
            'adjustment_statistics': adjustment_stats,
            'priority_trends': trends,
            'priority_weights': self._priority_manager.get_priority_weights()
        }


def main():
    parser = argparse.ArgumentParser(
        description="修复策略库 - 智能修复策略管理系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 列出所有策略
  python fix_strategy_library.py --list-strategies

  # 按类别列出策略
  python fix_strategy_library.py --list-strategies --category syntax

  # 评估策略效果
  python fix_strategy_library.py --evaluate --strategy syntax_fix_001

  # 匹配文件问题
  python fix_strategy_library.py --match --file problematic.py

  # 导出策略
  python fix_strategy_library.py --export strategies.json

  # 导入策略
  python fix_strategy_library.py --import strategies.json
        """
    )

    parser.add_argument(
        "--list-strategies",
        action="store_true",
        help="列出所有策略"
    )

    parser.add_argument(
        "--category",
        type=str,
        choices=[c.value for c in StrategyCategory],
        help="按类别筛选"
    )

    parser.add_argument(
        "--evaluate",
        action="store_true",
        help="评估策略效果"
    )

    parser.add_argument(
        "--strategy",
        type=str,
        help="指定策略ID"
    )

    parser.add_argument(
        "--match",
        action="store_true",
        help="匹配文件问题"
    )

    parser.add_argument(
        "--file",
        type=Path,
        help="要分析的文件"
    )

    parser.add_argument(
        "--export",
        type=Path,
        help="导出策略到文件"
    )

    parser.add_argument(
        "--import",
        dest="import_file",
        type=Path,
        help="从文件导入策略"
    )

    parser.add_argument(
        "--statistics",
        action="store_true",
        help="显示策略库统计信息"
    )

    parser.add_argument(
        "--performance-report",
        action="store_true",
        help="显示策略性能报告"
    )

    parser.add_argument(
        "--optimize-order",
        action="store_true",
        help="优化策略执行顺序"
    )

    parser.add_argument(
        "--check-compatibility",
        nargs="+",
        help="检查策略兼容性"
    )

    parser.add_argument(
        "--apply-best",
        action="store_true",
        help="应用最佳策略"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="详细输出"
    )

    parser.add_argument(
        "--lifecycle",
        action="store_true",
        help="显示策略生命周期信息"
    )

    parser.add_argument(
        "--templates",
        action="store_true",
        help="列出所有策略模板"
    )

    parser.add_argument(
        "--create-from-template",
        type=str,
        help="从模板创建策略 (格式: template_id:strategy_id:var1=val1,var2=val2)"
    )

    parser.add_argument(
        "--enhanced-match",
        action="store_true",
        help="使用增强型匹配"
    )

    parser.add_argument(
        "--advanced-evaluate",
        action="store_true",
        help="使用高级评估"
    )

    parser.add_argument(
        "--time-series",
        action="store_true",
        help="显示时间序列分析"
    )

    parser.add_argument(
        "--granularity",
        type=str,
        choices=['hour', 'day', 'week'],
        default='day',
        help="时间序列粒度"
    )

    parser.add_argument(
        "--optimization-suggestions",
        action="store_true",
        help="生成优化建议"
    )

    parser.add_argument(
        "--comprehensive-report",
        action="store_true",
        help="显示综合报告"
    )

    parser.add_argument(
        "--activate",
        type=str,
        help="激活指定策略"
    )

    parser.add_argument(
        "--deactivate",
        type=str,
        help="停用指定策略"
    )

    parser.add_argument(
        "--deprecate",
        type=str,
        help="废弃指定策略 (格式: strategy_id:reason)"
    )

    parser.add_argument(
        "--discover-patterns",
        action="store_true",
        help="发现新模式"
    )

    parser.add_argument(
        "--force-learn",
        action="store_true",
        help="强制执行学习周期"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    library = StrategyLibrary()
    orchestrator = EnhancedStrategyOrchestrator(library)

    if args.list_strategies:
        print("\n" + "=" * 60)
        print("已注册的策略")
        print("=" * 60)

        category = StrategyCategory(args.category) if args.category else None

        if category:
            strategies = library.get_strategies_by_category(category)
        else:
            strategies = library.get_all_strategies()

        for strategy in sorted(strategies, key=lambda s: s.priority.value):
            print(f"\n[{strategy.category.value.upper()}] {strategy.name}")
            print(f"  ID: {strategy.strategy_id}")
            print(f"  优先级: {strategy.priority.name}")
            print(f"  描述: {strategy.description}")

    elif args.evaluate:
        print("\n" + "=" * 60)
        print("策略效果评估")
        print("=" * 60)

        if args.strategy:
            effect = library.evaluate_strategy(args.strategy)
            if effect:
                print(f"\n策略: {args.strategy}")
                print(f"  总应用次数: {effect.total_applications}")
                print(f"  成功次数: {effect.successful_applications}")
                print(f"  失败次数: {effect.failed_applications}")
                print(f"  成功率: {effect.success_rate:.2%}")
                print(f"  平均执行时间: {effect.average_execution_time:.2f}ms")
                print(f"  效果得分: {effect.effectiveness_score:.3f}")
            else:
                print(f"策略不存在: {args.strategy}")
        else:
            effects = library.evaluate_all_strategies()
            for sid, effect in effects.items():
                print(f"\n{sid}:")
                print(f"  成功率: {effect.success_rate:.2%}")
                print(f"  效果得分: {effect.effectiveness_score:.3f}")

    elif args.match and args.file:
        print("\n" + "=" * 60)
        print(f"匹配分析: {args.file}")
        print("=" * 60)

        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"读取文件失败: {e}")
            return 1

        matches = library.match_strategies(content, args.file)

        if matches:
            print(f"\n找到 {len(matches)} 个匹配的策略:\n")
            for match in matches:
                strategy = library.get_strategy(match.strategy_id)
                if strategy:
                    print(f"[{strategy.category.value.upper()}] {strategy.name}")
                    print(f"  匹配结果: {match.result.value}")
                    print(f"  置信度: {match.confidence:.2%}")
                    print(f"  发现问题: {len(match.issues_found)}")
                    if match.matched_patterns:
                        print(f"  匹配模式: {', '.join(match.matched_patterns)}")
                    print()
        else:
            print("\n未发现匹配的策略")

    elif args.export:
        if library.export_strategies(args.export):
            print(f"\n策略已导出到: {args.export}")
        else:
            print("\n导出失败")
            return 1

    elif args.import_file:
        count = library.import_strategies(args.import_file)
        print(f"\n已导入 {count} 个策略")

    elif args.statistics:
        stats = library.get_statistics()
        print("\n" + "=" * 60)
        print("策略库统计信息")
        print("=" * 60)
        print(f"\n总策略数: {stats['total_strategies']}")
        print(f"\n按类别分布:")
        for cat, count in stats['strategies_by_category'].items():
            if count > 0:
                print(f"  {cat}: {count}")
        print(f"\n总应用次数: {stats['total_applications']}")
        print(f"总成功次数: {stats['total_successes']}")
        print(f"整体成功率: {stats['overall_success_rate']:.2%}")

    elif args.performance_report:
        report = library.get_strategy_performance_report()
        print("\n" + "=" * 60)
        print("策略性能报告")
        print("=" * 60)
        print(f"\n总策略数: {report['total_strategies']}")
        print(f"总应用次数: {report['total_applications']}")
        print(f"总成功次数: {report['total_successes']}")
        print(f"整体成功率: {report['overall_success_rate']:.2%}")
        print(f"平均成功率: {report['average_success_rate']:.2%}")
        print(f"平均F1分数: {report['average_f1_score']:.3f}")
        print(f"\n趋势分布:")
        for trend, count in report['trend_distribution'].items():
            print(f"  {trend}: {count}")
        print(f"\n表现最佳策略:")
        for performer in report['top_performers']:
            print(f"  - {performer['name']}: 效果得分 {performer['effectiveness_score']:.3f}")
        print(f"\n表现欠佳策略:")
        for performer in report['underperformers']:
            print(f"  - {performer['name']}: 效果得分 {performer['effectiveness_score']:.3f}")

    elif args.optimize_order:
        print("\n" + "=" * 60)
        print("优化后的策略执行顺序")
        print("=" * 60)
        optimized_order = library.optimize_strategy_order()
        for i, sid in enumerate(optimized_order, 1):
            strategy = library.get_strategy(sid)
            if strategy:
                print(f"{i}. {strategy.name} ({sid})")

    elif args.check_compatibility:
        print("\n" + "=" * 60)
        print("策略兼容性检查")
        print("=" * 60)
        is_compatible, conflicts = library.check_compatibility(args.check_compatibility)
        if is_compatible:
            print("\n所有策略兼容")
        else:
            print("\n检测到冲突:")
            for conflict in conflicts:
                print(f"  - {conflict}")

    elif args.apply_best and args.file:
        print("\n" + "=" * 60)
        print(f"应用最佳策略: {args.file}")
        print("=" * 60)

        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"读取文件失败: {e}")
            return 1

        fixed_content, fixes = library.apply_best_strategies(content, args.file)

        print(f"\n应用了 {len(fixes)} 个修复:")
        for fix in fixes:
            print(f"  - 行 {fix.get('line', 'N/A')}: {fix.get('type', 'unknown')}")

        if args.verbose:
            print("\n修复后代码:")
            print("-" * 40)
            print(fixed_content)

    elif args.lifecycle:
        print("\n" + "=" * 60)
        print("策略生命周期信息")
        print("=" * 60)

        lifecycle_manager = orchestrator.get_lifecycle_manager()
        active = lifecycle_manager.get_active_strategies()
        deprecated = lifecycle_manager.get_deprecated_strategies()
        experimental = lifecycle_manager.get_experimental_strategies()

        print(f"\n活跃策略: {len(active)}")
        for s in active:
            lc = lifecycle_manager.get_strategy_lifecycle(s.strategy_id)
            event_count = len(lc.get('events', [])) if lc else 0
            print(f"  - {s.name} ({s.strategy_id}): {event_count} 个事件")

        print(f"\n废弃策略: {len(deprecated)}")
        for s in deprecated:
            print(f"  - {s.name} ({s.strategy_id})")

        print(f"\n实验性策略: {len(experimental)}")
        for s in experimental:
            print(f"  - {s.name} ({s.strategy_id})")

    elif args.templates:
        print("\n" + "=" * 60)
        print("策略模板列表")
        print("=" * 60)

        lifecycle_manager = orchestrator.get_lifecycle_manager()
        templates = lifecycle_manager.list_templates()

        for template in templates:
            print(f"\n[{template.category.value.upper()}] {template.name}")
            print(f"  ID: {template.template_id}")
            print(f"  描述: {template.description}")
            print(f"  变量: {list(template.variables.keys())}")

    elif args.create_from_template:
        print("\n" + "=" * 60)
        print("从模板创建策略")
        print("=" * 60)

        parts = args.create_from_template.split(':')
        if len(parts) < 2:
            print("错误: 格式应为 template_id:strategy_id:var1=val1,var2=val2")
            return 1

        template_id = parts[0]
        strategy_id = parts[1]
        variables = {}

        if len(parts) > 2:
            for var_pair in parts[2].split(','):
                if '=' in var_pair:
                    key, value = var_pair.split('=', 1)
                    variables[key.strip()] = value.strip()

        lifecycle_manager = orchestrator.get_lifecycle_manager()
        strategy = lifecycle_manager.create_strategy_from_template(
            template_id, strategy_id, variables
        )

        if strategy:
            print(f"\n成功创建策略: {strategy.name} ({strategy_id})")
        else:
            print(f"\n创建策略失败")

    elif args.enhanced_match and args.file:
        print("\n" + "=" * 60)
        print(f"增强型匹配分析: {args.file}")
        print("=" * 60)

        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"读取文件失败: {e}")
            return 1

        matcher = orchestrator.get_enhanced_matcher()
        matches = matcher.enhanced_match(content, args.file)

        if matches:
            print(f"\n找到 {len(matches)} 个匹配的策略:\n")
            for match in matches[:10]:
                strategy = library.get_strategy(match.strategy_id)
                if strategy:
                    print(f"[{strategy.category.value.upper()}] {strategy.name}")
                    print(f"  置信度: {match.confidence:.2%}")
                    feature_score = match.metadata.get('feature_score', 0)
                    context_score = match.metadata.get('context_score', 0)
                    print(f"  特征得分: {feature_score:.3f}, 上下文得分: {context_score:.3f}")
                    print(f"  发现问题: {len(match.issues_found)}")
                    print()

            cache_stats = matcher.get_cache_stats()
            print(f"\n缓存统计: {cache_stats['cache_size']}/{cache_stats['max_size']}")
        else:
            print("\n未发现匹配的策略")

    elif args.advanced_evaluate and args.strategy:
        print("\n" + "=" * 60)
        print(f"高级策略评估: {args.strategy}")
        print("=" * 60)

        evaluator = orchestrator.get_advanced_evaluator()

        if args.time_series:
            result = evaluator.evaluate_with_time_series(
                args.strategy, args.granularity
            )
            print(f"\n时间序列分析 (粒度: {args.granularity}):")
            for ts in result.get('time_series', [])[:10]:
                print(f"  {ts['period']}: 效果={ts['avg_effectiveness']:.3f}, 成功率={ts['avg_success_rate']:.2%}")

            trend = result.get('trend_analysis', {})
            print(f"\n趋势分析:")
            print(f"  效果趋势: {trend.get('effectiveness_trend', 'N/A')}")
            print(f"  成功率趋势: {trend.get('success_rate_trend', 'N/A')}")
            print(f"  波动性: {trend.get('volatility', 0):.4f}")
        else:
            result = evaluator.evaluate_comprehensive(args.strategy)

            basic = result.get('basic_metrics', {})
            advanced = result.get('advanced_metrics', {})

            print(f"\n基础指标:")
            print(f"  成功率: {basic.get('success_rate', 0):.2%}")
            print(f"  精确度: {basic.get('precision', 0):.2%}")
            print(f"  召回率: {basic.get('recall', 0):.2%}")
            print(f"  F1分数: {basic.get('f1_score', 0):.3f}")
            print(f"  效果得分: {basic.get('effectiveness_score', 0):.3f}")

            print(f"\n高级指标:")
            print(f"  稳定性: {advanced.get('stability', 0):.2%}")
            print(f"  可靠性: {advanced.get('reliability', 0):.2%}")
            print(f"  执行稳定性: {advanced.get('execution_stability', 0):.2%}")
            print(f"  整体质量: {advanced.get('overall_quality', 0):.2%}")

    elif args.optimization_suggestions and args.strategy:
        print("\n" + "=" * 60)
        print(f"优化建议: {args.strategy}")
        print("=" * 60)

        evaluator = orchestrator.get_advanced_evaluator()
        suggestions = evaluator.generate_optimization_suggestions(args.strategy)

        print(f"\n优化建议:")
        for i, suggestion in enumerate(suggestions, 1):
            print(f"  {i}. {suggestion}")

    elif args.comprehensive_report:
        print("\n" + "=" * 60)
        print("综合报告")
        print("=" * 60)

        report = orchestrator.get_comprehensive_report()

        exec_stats = report.get('execution_statistics', {})
        print(f"\n执行统计:")
        print(f"  总执行次数: {exec_stats.get('total_executions', 0)}")
        print(f"  总应用策略数: {exec_stats.get('total_strategies_applied', 0)}")
        print(f"  成功率: {exec_stats.get('success_rate', 0):.2%}")

        learning = report.get('learning_progress', {})
        print(f"\n学习进度:")
        print(f"  学习数据量: {learning.get('total_learning_data', 0)}")
        print(f"  成功率: {learning.get('success_rate', 0):.2%}")
        print(f"  发现模式数: {learning.get('discovered_patterns_count', 0)}")

        cache = report.get('cache_statistics', {})
        print(f"\n缓存统计:")
        print(f"  缓存大小: {cache.get('cache_size', 0)}/{cache.get('max_size', 0)}")

        print(f"\n策略状态分布:")
        print(f"  活跃策略: {report.get('active_strategies', 0)}")
        print(f"  废弃策略: {report.get('deprecated_strategies', 0)}")
        print(f"  实验性策略: {report.get('experimental_strategies', 0)}")
        print(f"  模板数量: {report.get('templates_count', 0)}")

    elif args.activate:
        print("\n" + "=" * 60)
        print(f"激活策略: {args.activate}")
        print("=" * 60)

        lifecycle_manager = orchestrator.get_lifecycle_manager()
        if lifecycle_manager.activate_strategy(args.activate):
            print(f"\n策略 {args.activate} 已激活")
        else:
            print(f"\n激活失败")

    elif args.deactivate:
        print("\n" + "=" * 60)
        print(f"停用策略: {args.deactivate}")
        print("=" * 60)

        lifecycle_manager = orchestrator.get_lifecycle_manager()
        if lifecycle_manager.deactivate_strategy(args.deactivate):
            print(f"\n策略 {args.deactivate} 已停用")
        else:
            print(f"\n停用失败")

    elif args.deprecate:
        print("\n" + "=" * 60)
        print(f"废弃策略")
        print("=" * 60)

        parts = args.deprecate.split(':', 1)
        strategy_id = parts[0]
        reason = parts[1] if len(parts) > 1 else "未指定原因"

        lifecycle_manager = orchestrator.get_lifecycle_manager()
        if lifecycle_manager.deprecate_strategy(strategy_id, reason):
            print(f"\n策略 {strategy_id} 已废弃")
            print(f"原因: {reason}")
        else:
            print(f"\n废弃失败")

    elif args.discover_patterns:
        print("\n" + "=" * 60)
        print("发现新模式")
        print("=" * 60)

        learner = orchestrator.get_advanced_learner()
        patterns = learner.discover_new_patterns(min_support=0.3)

        if patterns:
            print(f"\n发现 {len(patterns)} 个高价值模式:\n")
            for p in patterns[:10]:
                print(f"模式: {p['pattern'][:60]}...")
                print(f"  频率: {p['frequency']}, 成功率: {p['success_rate']:.2%}")
                print(f"  置信度: {p['confidence']:.3f}")
                print()
        else:
            print("\n暂未发现高价值模式，请先运行更多修复任务积累数据")

    elif args.force_learn:
        print("\n" + "=" * 60)
        print("强制执行学习周期")
        print("=" * 60)

        learner = orchestrator.get_advanced_learner()
        result = learner.force_learning_cycle()

        print(f"\n学习周期完成:")
        print(f"  处理状态: {result.get('processed', False)}")
        print(f"  发现模式数: {result.get('discovered_patterns', 0)}")
        print(f"  时间: {result.get('timestamp', 'N/A')}")

    else:
        parser.print_help()

    return 0


if __name__ == "__main__":
    sys.exit(main())
