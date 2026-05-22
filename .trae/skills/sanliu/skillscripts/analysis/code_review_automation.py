#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代码审查自动化脚本 - Sanliu 技能

自动化代码审查功能，包括：
- 代码质量检查增强
- 审查报告自动生成
- 审查建议自动修复
- 代码复杂度分析
- 安全漏洞检测
- 性能问题检测
- 代码风格检查

使用示例:
    python code_review_automation.py
    python code_review_automation.py --output json
    python code_review_automation.py --auto-fix
    python code_review_automation.py --severity high
"""

import os
import sys
import ast
import re
import json
import argparse
import logging
import tokenize
import io
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict
from abc import ABC, abstractmethod


class ReviewCategory(Enum):
    """审查类别"""
    QUALITY = "quality"
    SECURITY = "security"
    PERFORMANCE = "performance"
    STYLE = "style"
    COMPLEXITY = "complexity"
    MAINTAINABILITY = "maintainability"
    DOCUMENTATION = "documentation"


class IssueSeverity(Enum):
    """问题严重程度"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class FixStatus(Enum):
    """修复状态"""
    PENDING = "pending"
    FIXED = "fixed"
    SKIPPED = "skipped"
    FAILED = "failed"


@dataclass
class ReviewIssue:
    """审查问题数据类"""
    category: ReviewCategory
    severity: IssueSeverity
    file_path: str
    line_number: int
    column: int
    issue_type: str
    description: str
    code_snippet: str = ""
    suggestion: str = ""
    auto_fixable: bool = False
    fix_status: FixStatus = FixStatus.PENDING
    fix_diff: str = ""
    rule_id: str = ""
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category.value,
            "severity": self.severity.value,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "column": self.column,
            "issue_type": self.issue_type,
            "description": self.description,
            "code_snippet": self.code_snippet[:100],
            "suggestion": self.suggestion,
            "auto_fixable": self.auto_fixable,
            "fix_status": self.fix_status.value,
            "fix_diff": self.fix_diff,
            "rule_id": self.rule_id,
            "tags": self.tags
        }


@dataclass
class ComplexityMetrics:
    """复杂度指标数据类"""
    cyclomatic_complexity: int = 0
    cognitive_complexity: int = 0
    nesting_depth: int = 0
    lines_of_code: int = 0
    logical_lines_of_code: int = 0
    parameter_count: int = 0
    function_count: int = 0
    class_count: int = 0
    import_count: int = 0
    comment_lines: int = 0
    maintainability_index: float = 100.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cyclomatic_complexity": self.cyclomatic_complexity,
            "cognitive_complexity": self.cognitive_complexity,
            "nesting_depth": self.nesting_depth,
            "lines_of_code": self.lines_of_code,
            "logical_lines_of_code": self.logical_lines_of_code,
            "parameter_count": self.parameter_count,
            "function_count": self.function_count,
            "class_count": self.class_count,
            "import_count": self.import_count,
            "comment_lines": self.comment_lines,
            "maintainability_index": round(self.maintainability_index, 2)
        }


@dataclass
class FileReviewResult:
    """文件审查结果"""
    file_path: str
    issues: List[ReviewIssue] = field(default_factory=list)
    metrics: ComplexityMetrics = field(default_factory=ComplexityMetrics)
    quality_score: float = 100.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "issues": [i.to_dict() for i in self.issues],
            "metrics": self.metrics.to_dict(),
            "quality_score": round(self.quality_score, 2),
            "issue_count": len(self.issues)
        }


@dataclass
class ReviewReport:
    """审查报告"""
    timestamp: str
    project_root: str
    total_files: int
    total_issues: int
    file_results: List[FileReviewResult]
    summary: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    auto_fix_summary: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "project_root": self.project_root,
            "total_files": self.total_files,
            "total_issues": self.total_issues,
            "summary": self.summary,
            "recommendations": self.recommendations,
            "auto_fix_summary": self.auto_fix_summary,
            "file_results": [r.to_dict() for r in self.file_results]
        }


class ComplexityAnalyzer(ast.NodeVisitor):
    """复杂度分析器"""

    def __init__(self):
        self.cyclomatic_complexity = 1
        self.cognitive_complexity = 0
        self.nesting_depth = 0
        self.max_nesting_depth = 0
        self.function_count = 0
        self.class_count = 0
        self.import_count = 0
        self.logical_lines = 0
        self.comment_lines = 0

    def visit_If(self, node: ast.If):
        self.cyclomatic_complexity += 1
        self.cognitive_complexity += (self.nesting_depth + 1)
        self._visit_with_nesting(node)

    def visit_For(self, node: ast.For):
        self.cyclomatic_complexity += 1
        self.cognitive_complexity += (self.nesting_depth + 1)
        self._visit_with_nesting(node)

    def visit_While(self, node: ast.While):
        self.cyclomatic_complexity += 1
        self.cognitive_complexity += (self.nesting_depth + 1)
        self._visit_with_nesting(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler):
        self.cyclomatic_complexity += 1
        self.cognitive_complexity += 1
        self.generic_visit(node)

    def visit_BoolOp(self, node: ast.BoolOp):
        self.cyclomatic_complexity += len(node.values) - 1
        self.cognitive_complexity += len(node.values) - 1
        self.generic_visit(node)

    def visit_comprehension(self, node: ast.comprehension):
        self.cyclomatic_complexity += 1
        self.cognitive_complexity += 1
        if node.ifs:
            self.cyclomatic_complexity += len(node.ifs)
            self.cognitive_complexity += len(node.ifs)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self.function_count += 1
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self.function_count += 1
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        self.class_count += 1
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import):
        self.import_count += len(node.names)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.names:
            self.import_count += len(node.names)
        self.generic_visit(node)

    def _visit_with_nesting(self, node: ast.AST):
        self.nesting_depth += 1
        self.max_nesting_depth = max(self.max_nesting_depth, self.nesting_depth)
        self.generic_visit(node)
        self.nesting_depth -= 1

    def get_metrics(self, lines_of_code: int) -> ComplexityMetrics:
        """获取复杂度指标"""
        lloc = max(1, lines_of_code - self.comment_lines)
        
        mi = max(0, min(100, 171 - 5.2 * (self.cyclomatic_complexity ** 0.5) - 0.23 * self.cognitive_complexity - 16.2 * (lloc ** 0.5)))
        
        return ComplexityMetrics(
            cyclomatic_complexity=self.cyclomatic_complexity,
            cognitive_complexity=self.cognitive_complexity,
            nesting_depth=self.max_nesting_depth,
            lines_of_code=lines_of_code,
            logical_lines_of_code=lloc,
            function_count=self.function_count,
            class_count=self.class_count,
            import_count=self.import_count,
            comment_lines=self.comment_lines,
            maintainability_index=mi
        )


class QualityChecker:
    """代码质量检查器"""

    RULES = {
        "line_too_long": {
            "threshold": 120,
            "severity": IssueSeverity.LOW,
            "category": ReviewCategory.STYLE,
            "auto_fixable": False
        },
        "trailing_whitespace": {
            "threshold": 0,
            "severity": IssueSeverity.LOW,
            "category": ReviewCategory.STYLE,
            "auto_fixable": True
        },
        "missing_docstring": {
            "threshold": 0,
            "severity": IssueSeverity.LOW,
            "category": ReviewCategory.DOCUMENTATION,
            "auto_fixable": False
        },
        "too_many_arguments": {
            "threshold": 5,
            "severity": IssueSeverity.MEDIUM,
            "category": ReviewCategory.COMPLEXITY,
            "auto_fixable": False
        },
        "too_many_locals": {
            "threshold": 15,
            "severity": IssueSeverity.MEDIUM,
            "category": ReviewCategory.COMPLEXITY,
            "auto_fixable": False
        },
        "magic_number": {
            "threshold": 0,
            "severity": IssueSeverity.LOW,
            "category": ReviewCategory.MAINTAINABILITY,
            "auto_fixable": False
        },
        "unused_import": {
            "threshold": 0,
            "severity": IssueSeverity.LOW,
            "category": ReviewCategory.QUALITY,
            "auto_fixable": True
        },
        "bare_except": {
            "threshold": 0,
            "severity": IssueSeverity.HIGH,
            "category": ReviewCategory.QUALITY,
            "auto_fixable": False
        }
    }

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.issues: List[ReviewIssue] = []

    def check_file(self, file_path: Path, content: str, tree: ast.AST) -> List[ReviewIssue]:
        """检查文件"""
        self.issues = []
        lines = content.split('\n')

        self._check_line_length(file_path, lines)
        self._check_trailing_whitespace(file_path, lines)
        self._check_docstrings(file_path, tree)
        self._check_function_complexity(file_path, tree)
        self._check_magic_numbers(file_path, tree)
        self._check_bare_except(file_path, tree)
        self._check_unused_imports(file_path, tree, content)

        return self.issues

    def _check_line_length(self, file_path: Path, lines: List[str]):
        """检查行长度"""
        threshold = self.RULES["line_too_long"]["threshold"]
        for i, line in enumerate(lines, 1):
            if len(line) > threshold:
                self.issues.append(ReviewIssue(
                    category=ReviewCategory.STYLE,
                    severity=IssueSeverity.LOW,
                    file_path=str(file_path),
                    line_number=i,
                    column=threshold,
                    issue_type="line_too_long",
                    description=f"行长度超过 {threshold} 字符 (当前: {len(line)})",
                    code_snippet=line[:50] + "..." if len(line) > 50 else line,
                    suggestion="拆分行或简化代码",
                    auto_fixable=False,
                    rule_id="E501",
                    tags=["style", "formatting"]
                ))

    def _check_trailing_whitespace(self, file_path: Path, lines: List[str]):
        """检查尾随空格"""
        for i, line in enumerate(lines, 1):
            stripped = line.rstrip('\n\r')
            if stripped != stripped.rstrip():
                self.issues.append(ReviewIssue(
                    category=ReviewCategory.STYLE,
                    severity=IssueSeverity.LOW,
                    file_path=str(file_path),
                    line_number=i,
                    column=len(stripped.rstrip()),
                    issue_type="trailing_whitespace",
                    description="行尾存在空白字符",
                    code_snippet=line[:50],
                    suggestion="删除尾随空格",
                    auto_fixable=True,
                    rule_id="W291",
                    tags=["style", "formatting"]
                ))

    def _check_docstrings(self, file_path: Path, tree: ast.AST):
        """检查文档字符串"""
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not node.body:
                    continue
                first_stmt = node.body[0]
                if not isinstance(first_stmt, ast.Expr):
                    self.issues.append(ReviewIssue(
                        category=ReviewCategory.DOCUMENTATION,
                        severity=IssueSeverity.LOW,
                        file_path=str(file_path),
                        line_number=node.lineno,
                        column=0,
                        issue_type="missing_docstring",
                        description=f"函数 '{node.name}' 缺少文档字符串",
                        suggestion="添加文档字符串说明函数用途",
                        auto_fixable=False,
                        rule_id="D103",
                        tags=["documentation"]
                    ))

            elif isinstance(node, ast.ClassDef):
                if not node.body:
                    continue
                first_stmt = node.body[0]
                if not isinstance(first_stmt, ast.Expr):
                    self.issues.append(ReviewIssue(
                        category=ReviewCategory.DOCUMENTATION,
                        severity=IssueSeverity.LOW,
                        file_path=str(file_path),
                        line_number=node.lineno,
                        column=0,
                        issue_type="missing_docstring",
                        description=f"类 '{node.name}' 缺少文档字符串",
                        suggestion="添加文档字符串说明类用途",
                        auto_fixable=False,
                        rule_id="D101",
                        tags=["documentation"]
                    ))

    def _check_function_complexity(self, file_path: Path, tree: ast.AST):
        """检查函数复杂度"""
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                param_count = len(node.args.args) + len(node.args.kwonlyargs)
                if node.args.vararg:
                    param_count += 1
                if node.args.kwarg:
                    param_count += 1

                threshold = self.RULES["too_many_arguments"]["threshold"]
                if param_count > threshold:
                    self.issues.append(ReviewIssue(
                        category=ReviewCategory.COMPLEXITY,
                        severity=IssueSeverity.MEDIUM,
                        file_path=str(file_path),
                        line_number=node.lineno,
                        column=0,
                        issue_type="too_many_arguments",
                        description=f"函数 '{node.name}' 参数过多 ({param_count} > {threshold})",
                        suggestion="使用参数对象或配置字典减少参数数量",
                        auto_fixable=False,
                        rule_id="PLR0913",
                        tags=["complexity", "refactoring"]
                    ))

                local_vars = self._count_local_variables(node)
                threshold = self.RULES["too_many_locals"]["threshold"]
                if local_vars > threshold:
                    self.issues.append(ReviewIssue(
                        category=ReviewCategory.COMPLEXITY,
                        severity=IssueSeverity.MEDIUM,
                        file_path=str(file_path),
                        line_number=node.lineno,
                        column=0,
                        issue_type="too_many_locals",
                        description=f"函数 '{node.name}' 局部变量过多 ({local_vars} > {threshold})",
                        suggestion="拆分函数或提取子方法",
                        auto_fixable=False,
                        rule_id="PLR0914",
                        tags=["complexity", "refactoring"]
                    ))

    def _count_local_variables(self, node: ast.FunctionDef) -> int:
        """计算局部变量数量"""
        local_vars = set()
        for child in ast.walk(node):
            if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Store):
                local_vars.add(child.id)
        return len(local_vars)

    def _check_magic_numbers(self, file_path: Path, tree: ast.AST):
        """检查魔法数字"""
        allowed_numbers = {0, 1, 2, -1, 0.0, 1.0, 2.0, 10, 100, 1000, 255, 256, 3600}
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant):
                if isinstance(node.value, (int, float)):
                    if node.value not in allowed_numbers:
                        self.issues.append(ReviewIssue(
                            category=ReviewCategory.MAINTAINABILITY,
                            severity=IssueSeverity.LOW,
                            file_path=str(file_path),
                            line_number=node.lineno,
                            column=node.col_offset,
                            issue_type="magic_number",
                            description=f"发现魔法数字: {node.value}",
                            suggestion="将数字定义为有意义的常量",
                            auto_fixable=False,
                            rule_id="PLR2004",
                            tags=["maintainability", "refactoring"]
                        ))

    def _check_bare_except(self, file_path: Path, tree: ast.AST):
        """检查裸except"""
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler):
                if node.type is None:
                    self.issues.append(ReviewIssue(
                        category=ReviewCategory.QUALITY,
                        severity=IssueSeverity.HIGH,
                        file_path=str(file_path),
                        line_number=node.lineno,
                        column=0,
                        issue_type="bare_except",
                        description="使用裸except会捕获所有异常，包括系统退出信号",
                        suggestion="指定具体的异常类型，如 Exception 或更具体的异常",
                        auto_fixable=False,
                        rule_id="E722",
                        tags=["quality", "error-handling"]
                    ))

    def _check_unused_imports(self, file_path: Path, tree: ast.AST, content: str):
        """检查未使用的导入"""
        imports = set()
        used_names = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    imports.add((name, node.lineno))
            elif isinstance(node, ast.ImportFrom):
                if node.names:
                    for alias in node.names:
                        name = alias.asname if alias.asname else alias.name
                        imports.add((name, node.lineno))

            if isinstance(node, ast.Name):
                used_names.add(node.id)
            elif isinstance(node, ast.Attribute):
                if isinstance(node.value, ast.Name):
                    used_names.add(node.value.id)

        for import_name, line_no in imports:
            if import_name not in used_names:
                self.issues.append(ReviewIssue(
                    category=ReviewCategory.QUALITY,
                    severity=IssueSeverity.LOW,
                    file_path=str(file_path),
                    line_number=line_no,
                    column=0,
                    issue_type="unused_import",
                    description=f"未使用的导入: {import_name}",
                    suggestion="移除未使用的导入",
                    auto_fixable=True,
                    rule_id="F401",
                    tags=["quality", "cleanup"]
                ))


class SecurityChecker:
    """安全检查器"""

    SECURITY_PATTERNS = [
        {
            "pattern": r"eval\s*\(",
            "issue_type": "dangerous_eval",
            "description": "使用eval()存在代码注入风险",
            "severity": IssueSeverity.CRITICAL,
            "suggestion": "避免使用eval()，使用更安全的替代方案"
        },
        {
            "pattern": r"exec\s*\(",
            "issue_type": "dangerous_exec",
            "description": "使用exec()存在代码注入风险",
            "severity": IssueSeverity.CRITICAL,
            "suggestion": "避免使用exec()，使用更安全的替代方案"
        },
        {
            "pattern": r"subprocess\..*shell\s*=\s*True",
            "issue_type": "shell_injection",
            "description": "subprocess使用shell=True存在命令注入风险",
            "severity": IssueSeverity.HIGH,
            "suggestion": "避免使用shell=True，使用列表形式传递命令"
        },
        {
            "pattern": r"pickle\.loads?\s*\(",
            "issue_type": "pickle_insecure",
            "description": "pickle反序列化不可信数据存在安全风险",
            "severity": IssueSeverity.HIGH,
            "suggestion": "使用json或其他安全的序列化方式"
        },
        {
            "pattern": r"password\s*=\s*['\"]",
            "issue_type": "hardcoded_password",
            "description": "代码中存在硬编码密码",
            "severity": IssueSeverity.CRITICAL,
            "suggestion": "使用环境变量或配置文件存储敏感信息"
        },
        {
            "pattern": r"secret\s*=\s*['\"]",
            "issue_type": "hardcoded_secret",
            "description": "代码中存在硬编码密钥",
            "severity": IssueSeverity.CRITICAL,
            "suggestion": "使用环境变量或密钥管理服务"
        },
        {
            "pattern": r"api_key\s*=\s*['\"]",
            "issue_type": "hardcoded_api_key",
            "description": "代码中存在硬编码API密钥",
            "severity": IssueSeverity.CRITICAL,
            "suggestion": "使用环境变量或配置文件存储API密钥"
        },
        {
            "pattern": r"SQL\s*=.*%s.*\+",
            "issue_type": "sql_injection_risk",
            "description": "可能存在SQL注入风险",
            "severity": IssueSeverity.HIGH,
            "suggestion": "使用参数化查询"
        }
    ]

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.issues: List[ReviewIssue] = []

    def check_file(self, file_path: Path, content: str, tree: ast.AST) -> List[ReviewIssue]:
        """检查文件安全"""
        self.issues = []
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            for pattern_info in self.SECURITY_PATTERNS:
                if re.search(pattern_info["pattern"], line, re.IGNORECASE):
                    self.issues.append(ReviewIssue(
                        category=ReviewCategory.SECURITY,
                        severity=pattern_info["severity"],
                        file_path=str(file_path),
                        line_number=i,
                        column=0,
                        issue_type=pattern_info["issue_type"],
                        description=pattern_info["description"],
                        code_snippet=line.strip()[:50],
                        suggestion=pattern_info["suggestion"],
                        auto_fixable=False,
                        tags=["security", "vulnerability"]
                    ))

        return self.issues


class PerformanceChecker:
    """性能检查器"""

    PERFORMANCE_PATTERNS = [
        {
            "pattern": r"for\s+\w+\s+in\s+range\(len\(",
            "issue_type": "enumerate_instead_of_range_len",
            "description": "使用range(len())而不是enumerate()",
            "severity": IssueSeverity.LOW,
            "suggestion": "使用enumerate()替代range(len())"
        },
        {
            "pattern": r"\+\s*=\s*['\"]",
            "issue_type": "string_concat_in_loop",
            "description": "循环中字符串拼接效率低",
            "severity": IssueSeverity.MEDIUM,
            "suggestion": "使用join()或列表推导式"
        },
        {
            "pattern": r"list\(.*keys?\(\)\)",
            "issue_type": "unnecessary_list_keys",
            "description": "不必要的list(dict.keys())转换",
            "severity": IssueSeverity.LOW,
            "suggestion": "直接迭代字典或使用dict.keys()"
        }
    ]

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.issues: List[ReviewIssue] = []

    def check_file(self, file_path: Path, content: str, tree: ast.AST) -> List[ReviewIssue]:
        """检查性能问题"""
        self.issues = []
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            for pattern_info in self.PERFORMANCE_PATTERNS:
                if re.search(pattern_info["pattern"], line):
                    self.issues.append(ReviewIssue(
                        category=ReviewCategory.PERFORMANCE,
                        severity=pattern_info["severity"],
                        file_path=str(file_path),
                        line_number=i,
                        column=0,
                        issue_type=pattern_info["issue_type"],
                        description=pattern_info["description"],
                        code_snippet=line.strip()[:50],
                        suggestion=pattern_info["suggestion"],
                        auto_fixable=False,
                        tags=["performance", "optimization"]
                    ))

        self._check_loop_complexity(file_path, tree)

        return self.issues

    def _check_loop_complexity(self, file_path: Path, tree: ast.AST):
        """检查循环复杂度"""
        for node in ast.walk(tree):
            if isinstance(node, (ast.For, ast.While)):
                nested_loops = sum(1 for _ in ast.walk(node) if isinstance(_, (ast.For, ast.While)) and _ != node)
                if nested_loops > 1:
                    self.issues.append(ReviewIssue(
                        category=ReviewCategory.PERFORMANCE,
                        severity=IssueSeverity.MEDIUM,
                        file_path=str(file_path),
                        line_number=node.lineno,
                        column=0,
                        issue_type="nested_loops",
                        description=f"发现嵌套循环 (深度: {nested_loops})，可能影响性能",
                        suggestion="考虑使用更高效的算法或数据结构",
                        auto_fixable=False,
                        tags=["performance", "complexity"]
                    ))


class AutoFixer:
    """自动修复器"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.fix_count = 0
        self.skip_count = 0
        self.fail_count = 0

    def fix_issue(self, file_path: Path, issue: ReviewIssue, content: str) -> Tuple[str, FixStatus]:
        """修复问题"""
        if not issue.auto_fixable:
            return content, FixStatus.SKIPPED

        lines = content.split('\n')
        
        try:
            if issue.issue_type == "trailing_whitespace":
                line_idx = issue.line_number - 1
                if 0 <= line_idx < len(lines):
                    lines[line_idx] = lines[line_idx].rstrip() + '\n'
                    self.fix_count += 1
                    return '\n'.join(lines), FixStatus.FIXED

            elif issue.issue_type == "unused_import":
                line_idx = issue.line_number - 1
                if 0 <= line_idx < len(lines):
                    lines[line_idx] = ""
                    self.fix_count += 1
                    return '\n'.join(lines), FixStatus.FIXED

        except Exception as e:
            self.logger.warning(f"自动修复失败 {file_path}:{issue.line_number}: {e}")
            self.fail_count += 1
            return content, FixStatus.FAILED

        self.skip_count += 1
        return content, FixStatus.SKIPPED

    def apply_fixes(self, file_path: Path, issues: List[ReviewIssue], content: str) -> Tuple[str, List[ReviewIssue]]:
        """应用所有可自动修复的问题"""
        fixed_issues = []
        current_content = content

        for issue in issues:
            if issue.auto_fixable and issue.fix_status == FixStatus.PENDING:
                new_content, status = self.fix_issue(file_path, issue, current_content)
                if status == FixStatus.FIXED:
                    issue.fix_status = FixStatus.FIXED
                    fixed_issues.append(issue)
                    current_content = new_content
                else:
                    issue.fix_status = status

        return current_content, fixed_issues

    def get_summary(self) -> Dict[str, int]:
        """获取修复摘要"""
        return {
            "fixed": self.fix_count,
            "skipped": self.skip_count,
            "failed": self.fail_count
        }


class CodeReviewAutomation:
    """代码审查自动化"""

    def __init__(self, project_root: Optional[Path] = None,
                 auto_fix: bool = False,
                 min_severity: IssueSeverity = IssueSeverity.LOW,
                 logger: Optional[logging.Logger] = None):
        self.project_root = project_root or get_path_config().SKILL_ROOT
        self.auto_fix = auto_fix
        self.min_severity = min_severity
        self.logger = logger or logging.getLogger(__name__)
        
        self.quality_checker = QualityChecker(self.logger)
        self.security_checker = SecurityChecker(self.logger)
        self.performance_checker = PerformanceChecker(self.logger)
        self.auto_fixer = AutoFixer(self.logger)
        
        self.file_results: List[FileReviewResult] = []

    def review_project(self) -> ReviewReport:
        """审查整个项目"""
        self.logger.info("开始代码审查...")

        python_files = self._collect_python_files()
        self.logger.info(f"找到 {len(python_files)} 个Python文件")

        for py_file in python_files:
            result = self._review_file(py_file)
            self.file_results.append(result)

        summary = self._calculate_summary()
        recommendations = self._generate_recommendations()
        auto_fix_summary = self.auto_fixer.get_summary() if self.auto_fix else {}

        return ReviewReport(
            timestamp=datetime.now().isoformat(),
            project_root=str(self.project_root),
            total_files=len(python_files),
            total_issues=sum(len(r.issues) for r in self.file_results),
            file_results=self.file_results,
            summary=summary,
            recommendations=recommendations,
            auto_fix_summary=auto_fix_summary
        )

    def _collect_python_files(self) -> List[Path]:
        """收集Python文件"""
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

    def _review_file(self, file_path: Path) -> FileReviewResult:
        """审查单个文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content)
            lines = content.split('\n')

            all_issues = []
            all_issues.extend(self.quality_checker.check_file(file_path, content, tree))
            all_issues.extend(self.security_checker.check_file(file_path, content, tree))
            all_issues.extend(self.performance_checker.check_file(file_path, content, tree))

            severity_order = {
                IssueSeverity.CRITICAL: 0,
                IssueSeverity.HIGH: 1,
                IssueSeverity.MEDIUM: 2,
                IssueSeverity.LOW: 3,
                IssueSeverity.INFO: 4
            }
            filtered_issues = [
                i for i in all_issues
                if severity_order.get(i.severity, 99) <= severity_order.get(self.min_severity, 99)
            ]

            if self.auto_fix:
                content, fixed = self.auto_fixer.apply_fixes(file_path, filtered_issues, content)
                if fixed:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)

            complexity_analyzer = ComplexityAnalyzer()
            complexity_analyzer.visit(tree)
            metrics = complexity_analyzer.get_metrics(len(lines))

            quality_score = self._calculate_quality_score(filtered_issues, metrics)

            return FileReviewResult(
                file_path=str(file_path),
                issues=filtered_issues,
                metrics=metrics,
                quality_score=quality_score
            )
        except Exception as e:
            self.logger.error(f"审查文件失败 {file_path}: {e}")
            return FileReviewResult(file_path=str(file_path))

    def _calculate_quality_score(self, issues: List[ReviewIssue], metrics: ComplexityMetrics) -> float:
        """计算质量评分"""
        score = 100.0

        severity_penalties = {
            IssueSeverity.CRITICAL: 20,
            IssueSeverity.HIGH: 10,
            IssueSeverity.MEDIUM: 5,
            IssueSeverity.LOW: 2,
            IssueSeverity.INFO: 0
        }

        for issue in issues:
            score -= severity_penalties.get(issue.severity, 0)

        if metrics.cyclomatic_complexity > 10:
            score -= (metrics.cyclomatic_complexity - 10) * 2

        if metrics.nesting_depth > 4:
            score -= (metrics.nesting_depth - 4) * 3

        if metrics.maintainability_index < 65:
            score -= (65 - metrics.maintainability_index) * 0.5

        return max(0, min(100, score))

    def _calculate_summary(self) -> Dict[str, Any]:
        """计算摘要"""
        if not self.file_results:
            return {
                "total_issues": 0,
                "by_category": {},
                "by_severity": {},
                "by_type": {},
                "average_quality_score": 100.0,
                "files_below_threshold": 0
            }

        by_category: Dict[str, int] = defaultdict(int)
        by_severity: Dict[str, int] = defaultdict(int)
        by_type: Dict[str, int] = defaultdict(int)

        for result in self.file_results:
            for issue in result.issues:
                by_category[issue.category.value] += 1
                by_severity[issue.severity.value] += 1
                by_type[issue.issue_type] += 1

        quality_scores = [r.quality_score for r in self.file_results]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 100.0

        files_below_threshold = sum(1 for s in quality_scores if s < 70)

        return {
            "total_issues": sum(len(r.issues) for r in self.file_results),
            "by_category": dict(by_category),
            "by_severity": dict(by_severity),
            "by_type": dict(by_type),
            "average_quality_score": round(avg_quality, 2),
            "files_below_threshold": files_below_threshold,
            "quality_distribution": {
                "excellent": sum(1 for s in quality_scores if s >= 90),
                "good": sum(1 for s in quality_scores if 70 <= s < 90),
                "fair": sum(1 for s in quality_scores if 50 <= s < 70),
                "poor": sum(1 for s in quality_scores if s < 50)
            }
        }

    def _generate_recommendations(self) -> List[str]:
        """生成建议"""
        recommendations = []

        if not self.file_results:
            return ["代码质量良好"]

        summary = self._calculate_summary()
        by_severity = summary.get("by_severity", {})
        by_category = summary.get("by_category", {})

        if by_severity.get("critical", 0) > 0:
            recommendations.append("发现严重安全问题，请立即修复")

        if by_severity.get("high", 0) > 0:
            recommendations.append("存在高优先级问题，建议优先处理")

        if by_category.get("security", 0) > 0:
            recommendations.append("发现安全相关问题，请进行安全审计")

        if by_category.get("complexity", 0) > 3:
            recommendations.append("代码复杂度较高，建议进行重构")

        if by_category.get("performance", 0) > 0:
            recommendations.append("发现性能优化机会，建议进行性能测试")

        if summary.get("files_below_threshold", 0) > 0:
            recommendations.append(f"{summary['files_below_threshold']} 个文件质量评分低于阈值，需要重点关注")

        if not recommendations:
            recommendations.append("代码质量良好，继续保持")

        return recommendations

    def print_report(self, report: ReviewReport):
        """打印报告"""
        print("\n" + "=" * 80)
        print("代码审查报告")
        print("=" * 80)
        print(f"项目根目录: {report.project_root}")
        print(f"审查时间: {report.timestamp}")
        print(f"扫描文件数: {report.total_files}")
        print(f"发现问题数: {report.total_issues}")

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

        print(f"\n质量评分: {summary.get('average_quality_score', 100):.2f}")

        quality_dist = summary.get("quality_distribution", {})
        print(f"\n质量分布:")
        print(f"  优秀 (>=90): {quality_dist.get('excellent', 0)} 个文件")
        print(f"  良好 (70-89): {quality_dist.get('good', 0)} 个文件")
        print(f"  一般 (50-69): {quality_dist.get('fair', 0)} 个文件")
        print(f"  较差 (<50): {quality_dist.get('poor', 0)} 个文件")

        if report.auto_fix_summary:
            print("\n" + "-" * 80)
            print("自动修复摘要")
            print("-" * 80)
            print(f"  已修复: {report.auto_fix_summary.get('fixed', 0)}")
            print(f"  已跳过: {report.auto_fix_summary.get('skipped', 0)}")
            print(f"  修复失败: {report.auto_fix_summary.get('failed', 0)}")

        if report.recommendations:
            print("\n" + "-" * 80)
            print("改进建议")
            print("-" * 80)
            for i, rec in enumerate(report.recommendations, 1):
                print(f"{i}. {rec}")

        if report.file_results:
            print("\n" + "-" * 80)
            print("详细问题列表 (按严重程度排序)")
            print("-" * 80)

            severity_order = {
                IssueSeverity.CRITICAL: 0,
                IssueSeverity.HIGH: 1,
                IssueSeverity.MEDIUM: 2,
                IssueSeverity.LOW: 3,
                IssueSeverity.INFO: 4
            }

            all_issues = []
            for result in report.file_results:
                for issue in result.issues:
                    all_issues.append((result.file_path, issue))

            all_issues.sort(key=lambda x: severity_order.get(x[1].severity, 99))

            for i, (file_path, issue) in enumerate(all_issues[:30], 1):
                severity_icon = {
                    IssueSeverity.CRITICAL: "🔴",
                    IssueSeverity.HIGH: "🟠",
                    IssueSeverity.MEDIUM: "🟡",
                    IssueSeverity.LOW: "🔵",
                    IssueSeverity.INFO: "⚪"
                }.get(issue.severity, "⚪")

                print(f"\n{i}. {severity_icon} [{issue.severity.value.upper()}] {issue.issue_type}")
                print(f"   文件: {Path(file_path).name}:{issue.line_number}")
                print(f"   类别: {issue.category.value}")
                print(f"   描述: {issue.description}")
                if issue.suggestion:
                    print(f"   建议: {issue.suggestion}")

            if len(all_issues) > 30:
                print(f"\n... 还有 {len(all_issues) - 30} 个问题未显示")

    def save_report(self, report: ReviewReport, output_dir: Optional[Path] = None) -> Path:
        """保存报告"""
        if output_dir is None:
            output_dir = get_path_config().REPORTS_DIR
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = output_dir / f"code_review_{timestamp}.json"

        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)

        latest_path = output_dir / "code_review_latest.json"
        with open(latest_path, 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)

        self.logger.info(f"报告已保存: {report_path}")
        return report_path


def setup_logger(verbose: bool = False) -> logging.Logger:
    """配置日志记录器"""
    logger = logging.getLogger("CodeReviewAutomation")
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
        description="代码审查自动化脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python code_review_automation.py
  python code_review_automation.py --auto-fix
  python code_review_automation.py --severity high
  python code_review_automation.py --output json
        """
    )

    parser.add_argument(
        "--auto-fix",
        action="store_true",
        help="自动修复可修复的问题"
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
        "critical": IssueSeverity.CRITICAL,
        "high": IssueSeverity.HIGH,
        "medium": IssueSeverity.MEDIUM,
        "low": IssueSeverity.LOW,
        "info": IssueSeverity.INFO
    }

    reviewer = CodeReviewAutomation(
        auto_fix=args.auto_fix,
        min_severity=severity_map[args.severity],
        logger=logger
    )
    report = reviewer.review_project()

    reviewer.print_report(report)

    report_path = reviewer.save_report(report)
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

    return 0 if report.total_issues == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
