#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版修复验证器 - Fix Verification Enhanced

完善的修复执行验证系统，包括：
- 修复后语法验证（Syntax Validation）
- 修复后测试验证（Test Validation）
- 修复后性能验证（Performance Validation）
- 修复后安全验证（Security Validation）
- 修复后兼容性验证（Compatibility Validation）
- 修复后代码质量验证（Code Quality Validation）

使用示例:
    python fix_verification_enhanced.py --file code.py --verify-all
    python fix_verification_enhanced.py --file code.py --verify-syntax
    python fix_verification_enhanced.py --file code.py --verify-security
    python fix_verification_enhanced.py --before before.json --after after.json --report report.json
"""

from __future__ import annotations

import ast
import json
import logging
import os
import re
import subprocess
import sys
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)


class VerificationType(Enum):
    SYNTAX = auto()
    TEST = auto()
    PERFORMANCE = auto()
    SECURITY = auto()
    COMPATIBILITY = auto()
    CODE_QUALITY = auto()
    FUNCTIONALITY = auto()


class VerificationStatus(Enum):
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"
    ERROR = "error"


class SeverityLevel(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class VerificationIssue:
    issue_id: str
    verification_type: VerificationType
    severity: SeverityLevel
    message: str
    file_path: str
    line_number: int = 0
    column: int = 0
    code_snippet: str = ""
    suggestion: str = ""
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "issue_id": self.issue_id,
            "verification_type": self.verification_type.name,
            "severity": self.severity.value,
            "message": self.message,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "column": self.column,
            "code_snippet": self.code_snippet,
            "suggestion": self.suggestion,
            "context": self.context
        }


@dataclass
class VerificationResult:
    result_id: str
    verification_type: VerificationType
    status: VerificationStatus
    score: float
    max_score: float
    issues: List[VerificationIssue]
    execution_time_ms: float
    details: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "result_id": self.result_id,
            "verification_type": self.verification_type.name,
            "status": self.status.value,
            "score": round(self.score, 2),
            "max_score": self.max_score,
            "percentage": round(self.score / self.max_score * 100, 2) if self.max_score > 0 else 0,
            "issues": [i.to_dict() for i in self.issues],
            "execution_time_ms": round(self.execution_time_ms, 2),
            "details": self.details,
            "recommendations": self.recommendations
        }


@dataclass
class VerificationReport:
    report_id: str
    fix_id: str
    file_path: str
    timestamp: str
    overall_status: VerificationStatus
    overall_score: float
    results: List[VerificationResult]
    summary: str
    passed_count: int = 0
    failed_count: int = 0
    warning_count: int = 0
    critical_issues: List[VerificationIssue] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "fix_id": self.fix_id,
            "file_path": self.file_path,
            "timestamp": self.timestamp,
            "overall_status": self.overall_status.value,
            "overall_score": round(self.overall_score, 2),
            "results": [r.to_dict() for r in self.results],
            "summary": self.summary,
            "passed_count": self.passed_count,
            "failed_count": self.failed_count,
            "warning_count": self.warning_count,
            "critical_issues": [i.to_dict() for i in self.critical_issues]
        }


class BaseVerifier(ABC):
    """验证器基类"""

    verification_type: VerificationType = VerificationType.SYNTAX
    name: str = "base_verifier"
    description: str = "基础验证器"

    def __init__(self):
        self._issue_counter = 0
        self._result_counter = 0

    @abstractmethod
    def verify(self, content: str, file_path: str, before_content: Optional[str] = None) -> VerificationResult:
        pass

    def _create_issue(
        self,
        severity: SeverityLevel,
        message: str,
        file_path: str,
        line_number: int = 0,
        code_snippet: str = "",
        suggestion: str = "",
        context: Optional[Dict[str, Any]] = None
    ) -> VerificationIssue:
        self._issue_counter += 1
        return VerificationIssue(
            issue_id=f"ISSUE_{self._issue_counter:04d}",
            verification_type=self.verification_type,
            severity=severity,
            message=message,
            file_path=file_path,
            line_number=line_number,
            code_snippet=code_snippet,
            suggestion=suggestion,
            context=context or {}
        )

    def _create_result(
        self,
        status: VerificationStatus,
        score: float,
        max_score: float,
        issues: List[VerificationIssue],
        execution_time_ms: float,
        details: Optional[Dict[str, Any]] = None,
        recommendations: Optional[List[str]] = None
    ) -> VerificationResult:
        self._result_counter += 1
        return VerificationResult(
            result_id=f"RESULT_{self._result_counter:04d}",
            verification_type=self.verification_type,
            status=status,
            score=score,
            max_score=max_score,
            issues=issues,
            execution_time_ms=execution_time_ms,
            details=details or {},
            recommendations=recommendations or []
        )

    def _get_line_content(self, content: str, line_number: int) -> str:
        lines = content.split('\n')
        if 1 <= line_number <= len(lines):
            return lines[line_number - 1]
        return ""


class SyntaxVerifier(BaseVerifier):
    """语法验证器"""

    verification_type = VerificationType.SYNTAX
    name = "syntax_verifier"
    description = "验证修复后代码的语法正确性"

    def verify(self, content: str, file_path: str, before_content: Optional[str] = None) -> VerificationResult:
        start_time = time.perf_counter()
        issues = []
        score = 100.0

        issues.extend(self._check_syntax_errors(content, file_path))
        issues.extend(self._check_indentation(content, file_path))
        issues.extend(self._check_brackets(content, file_path))
        issues.extend(self._check_quotes(content, file_path))
        issues.extend(self._check_colons(content, file_path))

        for issue in issues:
            if issue.severity == SeverityLevel.CRITICAL:
                score -= 30
            elif issue.severity == SeverityLevel.HIGH:
                score -= 15
            elif issue.severity == SeverityLevel.MEDIUM:
                score -= 5
            elif issue.severity == SeverityLevel.LOW:
                score -= 2

        score = max(0, score)
        execution_time = (time.perf_counter() - start_time) * 1000

        status = VerificationStatus.PASSED if score >= 80 else (
            VerificationStatus.WARNING if score >= 60 else VerificationStatus.FAILED
        )

        recommendations = []
        if issues:
            recommendations.append("修复语法错误后再进行其他验证")

        return self._create_result(
            status=status,
            score=score,
            max_score=100.0,
            issues=issues,
            execution_time_ms=execution_time,
            recommendations=recommendations
        )

    def _check_syntax_errors(self, content: str, file_path: str) -> List[VerificationIssue]:
        issues = []
        try:
            ast.parse(content)
        except SyntaxError as e:
            line_num = e.lineno or 1
            issues.append(self._create_issue(
                severity=SeverityLevel.CRITICAL,
                message=f"语法错误: {e.msg}",
                file_path=file_path,
                line_number=line_num,
                code_snippet=self._get_line_content(content, line_num),
                suggestion="修复语法错误"
            ))
        return issues

    def _check_indentation(self, content: str, file_path: str) -> List[VerificationIssue]:
        issues = []
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            if not line.strip():
                continue

            indent = len(line) - len(line.lstrip())

            if '\t' in line[:indent] and ' ' in line[:indent]:
                issues.append(self._create_issue(
                    severity=SeverityLevel.HIGH,
                    message="混合使用制表符和空格进行缩进",
                    file_path=file_path,
                    line_number=i,
                    code_snippet=line,
                    suggestion="统一使用4个空格进行缩进"
                ))

        return issues

    def _check_brackets(self, content: str, file_path: str) -> List[VerificationIssue]:
        issues = []
        bracket_pairs = {'(': ')', '[': ']', '{': '}'}
        stack = []

        in_string = False
        string_char = None

        for i, char in enumerate(content):
            if char in '\'"' and not in_string:
                in_string = True
                string_char = char
            elif char == string_char and in_string:
                in_string = False
                string_char = None
            elif not in_string:
                if char in bracket_pairs:
                    stack.append((char, i))
                elif char in bracket_pairs.values():
                    if not stack:
                        line_num = content[:i].count('\n') + 1
                        issues.append(self._create_issue(
                            severity=SeverityLevel.CRITICAL,
                            message=f"未匹配的右括号 '{char}'",
                            file_path=file_path,
                            line_number=line_num,
                            suggestion="检查括号匹配"
                        ))
                    else:
                        expected_open = [k for k, v in bracket_pairs.items() if v == char][0]
                        if stack[-1][0] != expected_open:
                            line_num = content[:i].count('\n') + 1
                            issues.append(self._create_issue(
                                severity=SeverityLevel.CRITICAL,
                                message=f"括号类型不匹配",
                                file_path=file_path,
                                line_number=line_num,
                                suggestion="检查括号类型"
                            ))
                        else:
                            stack.pop()

        for bracket, pos in stack:
            line_num = content[:pos].count('\n') + 1
            issues.append(self._create_issue(
                severity=SeverityLevel.CRITICAL,
                message=f"未匹配的左括号 '{bracket}'",
                file_path=file_path,
                line_number=line_num,
                suggestion=f"添加对应的右括号 '{bracket_pairs[bracket]}'"
            ))

        return issues

    def _check_quotes(self, content: str, file_path: str) -> List[VerificationIssue]:
        issues = []
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith('#'):
                continue

            for quote in ['"', "'"]:
                count = line.count(quote) - line.count(f'\\{quote}')
                if count % 2 != 0:
                    triple = quote * 3
                    if triple in content:
                        continue
                    issues.append(self._create_issue(
                        severity=SeverityLevel.HIGH,
                        message=f"未匹配的引号 '{quote}'",
                        file_path=file_path,
                        line_number=i,
                        code_snippet=line,
                        suggestion="检查引号是否成对出现"
                    ))
                    break

        return issues

    def _check_colons(self, content: str, file_path: str) -> List[VerificationIssue]:
        issues = []
        lines = content.split('\n')
        keywords = ['if', 'elif', 'else', 'for', 'while', 'def', 'class', 'try', 'except', 'finally', 'with']

        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith('#'):
                continue

            for kw in keywords:
                if re.match(rf'^{kw}\b', stripped):
                    if not stripped.endswith(':'):
                        issues.append(self._create_issue(
                            severity=SeverityLevel.HIGH,
                            message=f"'{kw}' 语句末尾缺少冒号",
                            file_path=file_path,
                            line_number=i,
                            code_snippet=line,
                            suggestion="在语句末尾添加 ':'"
                        ))
                    break

        return issues


class TestVerifier(BaseVerifier):
    """测试验证器"""

    verification_type = VerificationType.TEST
    name = "test_verifier"
    description = "验证修复后代码的测试通过率"

    def __init__(self, project_root: Optional[Path] = None):
        super().__init__()
        self.project_root = project_root or Path.cwd()

    def verify(self, content: str, file_path: str, before_content: Optional[str] = None) -> VerificationResult:
        start_time = time.perf_counter()
        issues = []

        test_result = self._run_tests(file_path)

        score = 100.0
        if test_result.get("total", 0) > 0:
            pass_rate = test_result.get("passed", 0) / test_result["total"]
            score = pass_rate * 100

            if test_result.get("failed", 0) > 0:
                issues.append(self._create_issue(
                    severity=SeverityLevel.HIGH,
                    message=f"有 {test_result['failed']} 个测试失败",
                    file_path=file_path,
                    suggestion="修复失败的测试用例"
                ))

            for failure in test_result.get("failures", [])[:5]:
                issues.append(self._create_issue(
                    severity=SeverityLevel.MEDIUM,
                    message=f"测试失败: {failure}",
                    file_path=file_path,
                    suggestion="检查测试用例"
                ))

        execution_time = (time.perf_counter() - start_time) * 1000

        status = VerificationStatus.PASSED if score >= 90 else (
            VerificationStatus.WARNING if score >= 70 else VerificationStatus.FAILED
        )

        return self._create_result(
            status=status,
            score=score,
            max_score=100.0,
            issues=issues,
            execution_time_ms=execution_time,
            details=test_result
        )

    def _run_tests(self, file_path: str) -> Dict[str, Any]:
        result = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "failures": []
        }

        try:
            cmd = [sys.executable, "-m", "pytest", "-v", "--tb=short", "-q", file_path]
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(self.project_root)
            )

            output = proc.stdout + proc.stderr

            passed_match = re.search(r'(\d+) passed', output)
            failed_match = re.search(r'(\d+) failed', output)
            skipped_match = re.search(r'(\d+) skipped', output)

            if passed_match:
                result["passed"] = int(passed_match.group(1))
            if failed_match:
                result["failed"] = int(failed_match.group(1))
            if skipped_match:
                result["skipped"] = int(skipped_match.group(1))

            result["total"] = result["passed"] + result["failed"] + result["skipped"]

            for match in re.finditer(r'FAILED (.*?) ', output):
                result["failures"].append(match.group(1).strip())

        except subprocess.TimeoutExpired:
            logger.warning("测试运行超时")
        except Exception as e:
            logger.error(f"运行测试失败: {e}")

        return result


class PerformanceVerifier(BaseVerifier):
    """性能验证器"""

    verification_type = VerificationType.PERFORMANCE
    name = "performance_verifier"
    description = "验证修复后代码的性能影响"

    def verify(self, content: str, file_path: str, before_content: Optional[str] = None) -> VerificationResult:
        start_time = time.perf_counter()
        issues = []
        score = 100.0

        try:
            tree = ast.parse(content)
            issues.extend(self._check_complexity(tree, content, file_path))
            issues.extend(self._check_performance_patterns(tree, content, file_path))
        except SyntaxError:
            pass

        for issue in issues:
            if issue.severity == SeverityLevel.HIGH:
                score -= 15
            elif issue.severity == SeverityLevel.MEDIUM:
                score -= 8
            elif issue.severity == SeverityLevel.LOW:
                score -= 3

        score = max(0, score)
        execution_time = (time.perf_counter() - start_time) * 1000

        status = VerificationStatus.PASSED if score >= 80 else (
            VerificationStatus.WARNING if score >= 60 else VerificationStatus.FAILED
        )

        return self._create_result(
            status=status,
            score=score,
            max_score=100.0,
            issues=issues,
            execution_time_ms=execution_time
        )

    def _check_complexity(self, tree: ast.AST, content: str, file_path: str) -> List[VerificationIssue]:
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                complexity = self._calculate_complexity(node)
                if complexity > 15:
                    issues.append(self._create_issue(
                        severity=SeverityLevel.HIGH if complexity > 20 else SeverityLevel.MEDIUM,
                        message=f"函数 '{node.name}' 圈复杂度过高: {complexity}",
                        file_path=file_path,
                        line_number=node.lineno,
                        suggestion="简化函数逻辑，降低复杂度"
                    ))

        return issues

    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        return complexity

    def _check_performance_patterns(self, tree: ast.AST, content: str, file_path: str) -> List[VerificationIssue]:
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, ast.For):
                if isinstance(node.iter, ast.Call):
                    if isinstance(node.iter.func, ast.Name):
                        if node.iter.func.id == 'range':
                            for child in ast.walk(node):
                                if isinstance(child, ast.Subscript):
                                    issues.append(self._create_issue(
                                        severity=SeverityLevel.MEDIUM,
                                        message="使用 range(len()) 进行索引，建议使用 enumerate()",
                                        file_path=file_path,
                                        line_number=node.lineno,
                                        suggestion="使用 for i, item in enumerate(seq): 替代"
                                    ))
                                    break

            if isinstance(node, ast.AugAssign):
                if isinstance(node.op, ast.Add):
                    issues.append(self._create_issue(
                        severity=SeverityLevel.LOW,
                        message="字符串拼接操作，大量拼接时建议使用 join()",
                        file_path=file_path,
                        line_number=node.lineno,
                        suggestion="使用列表和 ''.join() 进行字符串拼接"
                    ))

        return issues


class SecurityVerifier(BaseVerifier):
    """安全验证器"""

    verification_type = VerificationType.SECURITY
    name = "security_verifier"
    description = "验证修复后代码的安全性"

    DANGEROUS_FUNCTIONS = {
        'eval': '代码注入风险',
        'exec': '代码注入风险',
        'compile': '代码注入风险',
        'os.system': '命令注入风险',
        'pickle.loads': '不安全的反序列化',
        'pickle.load': '不安全的反序列化',
        'yaml.load': '不安全的YAML加载',
    }

    SENSITIVE_PATTERNS = [
        (r'password\s*=\s*["\'][^"\']+["\']', '硬编码密码'),
        (r'api_key\s*=\s*["\'][^"\']+["\']', '硬编码API密钥'),
        (r'secret_key\s*=\s*["\'][^"\']+["\']', '硬编码密钥'),
    ]

    def verify(self, content: str, file_path: str, before_content: Optional[str] = None) -> VerificationResult:
        start_time = time.perf_counter()
        issues = []
        score = 100.0

        try:
            tree = ast.parse(content)
            issues.extend(self._check_dangerous_functions(tree, content, file_path))
            issues.extend(self._check_sql_injection(content, file_path))
            issues.extend(self._check_hardcoded_secrets(content, file_path))
            issues.extend(self._check_path_operations(tree, content, file_path))
        except SyntaxError:
            pass

        for issue in issues:
            if issue.severity == SeverityLevel.CRITICAL:
                score -= 40
            elif issue.severity == SeverityLevel.HIGH:
                score -= 20
            elif issue.severity == SeverityLevel.MEDIUM:
                score -= 10
            elif issue.severity == SeverityLevel.LOW:
                score -= 5

        score = max(0, score)
        execution_time = (time.perf_counter() - start_time) * 1000

        status = VerificationStatus.PASSED if score >= 80 else (
            VerificationStatus.WARNING if score >= 60 else VerificationStatus.FAILED
        )

        recommendations = []
        if any(i.severity == SeverityLevel.CRITICAL for i in issues):
            recommendations.append("存在严重安全问题，建议立即修复")

        return self._create_result(
            status=status,
            score=score,
            max_score=100.0,
            issues=issues,
            execution_time_ms=execution_time,
            recommendations=recommendations
        )

    def _check_dangerous_functions(self, tree: ast.AST, content: str, file_path: str) -> List[VerificationIssue]:
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_func_name(node.func)

                if func_name in self.DANGEROUS_FUNCTIONS:
                    issues.append(self._create_issue(
                        severity=SeverityLevel.CRITICAL,
                        message=f"使用危险函数 '{func_name}': {self.DANGEROUS_FUNCTIONS[func_name]}",
                        file_path=file_path,
                        line_number=node.lineno,
                        suggestion=f"避免使用 '{func_name}'，使用更安全的替代方案"
                    ))

        return issues

    def _get_func_name(self, node: ast.expr) -> str:
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            value_name = self._get_func_name(node.value)
            return f"{value_name}.{node.attr}"
        return ""

    def _check_sql_injection(self, content: str, file_path: str) -> List[VerificationIssue]:
        issues = []
        lines = content.split('\n')

        sql_patterns = [
            r'f["\'].*?(?:SELECT|INSERT|UPDATE|DELETE).*?\{',
            r'\.format\s*\([^)]*\).*?(?:SELECT|INSERT|UPDATE|DELETE)',
        ]

        for i, line in enumerate(lines, 1):
            for pattern in sql_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(self._create_issue(
                        severity=SeverityLevel.CRITICAL,
                        message="潜在的SQL注入漏洞",
                        file_path=file_path,
                        line_number=i,
                        code_snippet=line,
                        suggestion="使用参数化查询"
                    ))
                    break

        return issues

    def _check_hardcoded_secrets(self, content: str, file_path: str) -> List[VerificationIssue]:
        issues = []
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            for pattern, desc in self.SENSITIVE_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(self._create_issue(
                        severity=SeverityLevel.HIGH,
                        message=f"硬编码敏感信息: {desc}",
                        file_path=file_path,
                        line_number=i,
                        code_snippet=line,
                        suggestion="使用环境变量存储敏感信息"
                    ))
                    break

        return issues

    def _check_path_operations(self, tree: ast.AST, content: str, file_path: str) -> List[VerificationIssue]:
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_func_name(node.func)

                if func_name == 'open':
                    for arg in node.args:
                        if isinstance(arg, ast.Name):
                            issues.append(self._create_issue(
                                severity=SeverityLevel.MEDIUM,
                                message="使用变量作为文件路径，可能存在路径遍历风险",
                                file_path=file_path,
                                line_number=node.lineno,
                                suggestion="验证用户输入的路径"
                            ))

        return issues


class CodeQualityVerifier(BaseVerifier):
    """代码质量验证器"""

    verification_type = VerificationType.CODE_QUALITY
    name = "code_quality_verifier"
    description = "验证修复后代码的质量"

    def verify(self, content: str, file_path: str, before_content: Optional[str] = None) -> VerificationResult:
        start_time = time.perf_counter()
        issues = []
        score = 100.0

        try:
            tree = ast.parse(content)
            issues.extend(self._check_docstrings(tree, content, file_path))
            issues.extend(self._check_naming(tree, content, file_path))
            issues.extend(self._check_line_length(content, file_path))
            issues.extend(self._check_imports(tree, content, file_path))
        except SyntaxError:
            pass

        for issue in issues:
            if issue.severity == SeverityLevel.HIGH:
                score -= 10
            elif issue.severity == SeverityLevel.MEDIUM:
                score -= 5
            elif issue.severity == SeverityLevel.LOW:
                score -= 2

        score = max(0, score)
        execution_time = (time.perf_counter() - start_time) * 1000

        status = VerificationStatus.PASSED if score >= 80 else (
            VerificationStatus.WARNING if score >= 60 else VerificationStatus.FAILED
        )

        return self._create_result(
            status=status,
            score=score,
            max_score=100.0,
            issues=issues,
            execution_time_ms=execution_time
        )

    def _check_docstrings(self, tree: ast.AST, content: str, file_path: str) -> List[VerificationIssue]:
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                docstring = ast.get_docstring(node)
                if not docstring:
                    issues.append(self._create_issue(
                        severity=SeverityLevel.LOW,
                        message=f"{'函数' if isinstance(node, ast.FunctionDef) else '类'} '{node.name}' 缺少文档字符串",
                        file_path=file_path,
                        line_number=node.lineno,
                        suggestion="添加文档字符串说明功能和参数"
                    ))

        return issues

    def _check_naming(self, tree: ast.AST, content: str, file_path: str) -> List[VerificationIssue]:
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if not re.match(r'^[a-z_][a-z0-9_]*$', node.name):
                    issues.append(self._create_issue(
                        severity=SeverityLevel.MEDIUM,
                        message=f"函数名 '{node.name}' 不符合命名规范",
                        file_path=file_path,
                        line_number=node.lineno,
                        suggestion="使用小写字母和下划线命名"
                    ))

            elif isinstance(node, ast.ClassDef):
                if not re.match(r'^[A-Z][a-zA-Z0-9]*$', node.name):
                    issues.append(self._create_issue(
                        severity=SeverityLevel.MEDIUM,
                        message=f"类名 '{node.name}' 不符合命名规范",
                        file_path=file_path,
                        line_number=node.lineno,
                        suggestion="使用驼峰命名法"
                    ))

        return issues

    def _check_line_length(self, content: str, file_path: str, max_length: int = 120) -> List[VerificationIssue]:
        issues = []
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            if len(line) > max_length:
                issues.append(self._create_issue(
                    severity=SeverityLevel.LOW,
                    message=f"行长度超过 {max_length} 字符 ({len(line)} 字符)",
                    file_path=file_path,
                    line_number=i,
                    code_snippet=line[:100] + "..." if len(line) > 100 else line,
                    suggestion="拆分长行"
                ))

        return issues

    def _check_imports(self, tree: ast.AST, content: str, file_path: str) -> List[VerificationIssue]:
        issues = []
        imports = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    if name in imports:
                        issues.append(self._create_issue(
                            severity=SeverityLevel.MEDIUM,
                            message=f"重复导入 '{name}'",
                            file_path=file_path,
                            line_number=node.lineno,
                            suggestion="移除重复导入"
                        ))
                    imports.append(name)

        return issues


class FixVerificationEnhanced:
    """增强版修复验证器"""

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self._verifiers: Dict[str, BaseVerifier] = {}
        self._report_counter = 0
        self._register_builtin_verifiers()

    def _register_builtin_verifiers(self) -> None:
        verifiers = [
            SyntaxVerifier(),
            TestVerifier(self.project_root),
            PerformanceVerifier(),
            SecurityVerifier(),
            CodeQualityVerifier(),
        ]

        for verifier in verifiers:
            self._verifiers[verifier.name] = verifier

    def register_verifier(self, verifier: BaseVerifier) -> None:
        self._verifiers[verifier.name] = verifier
        logger.info(f"已注册验证器: {verifier.name}")

    def verify_file(self, file_path: str, before_content: Optional[str] = None,
                   verification_types: Optional[List[VerificationType]] = None) -> VerificationReport:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            logger.error(f"读取文件失败: {file_path}, {e}")
            return self._create_error_report(file_path, str(e))

        results = []
        for name, verifier in self._verifiers.items():
            if verification_types and verifier.verification_type not in verification_types:
                continue

            result = verifier.verify(content, file_path, before_content)
            results.append(result)

        return self._create_report(file_path, results)

    def _create_report(self, file_path: str, results: List[VerificationResult]) -> VerificationReport:
        self._report_counter += 1

        total_score = sum(r.score for r in results)
        max_score = sum(r.max_score for r in results)
        overall_score = (total_score / max_score * 100) if max_score > 0 else 0

        passed = sum(1 for r in results if r.status == VerificationStatus.PASSED)
        failed = sum(1 for r in results if r.status == VerificationStatus.FAILED)
        warning = sum(1 for r in results if r.status == VerificationStatus.WARNING)

        critical_issues = [
            issue for r in results for issue in r.issues
            if issue.severity == SeverityLevel.CRITICAL
        ]

        if failed > 0 or critical_issues:
            overall_status = VerificationStatus.FAILED
        elif warning > 0:
            overall_status = VerificationStatus.WARNING
        else:
            overall_status = VerificationStatus.PASSED

        summary = self._generate_summary(results, overall_score)

        return VerificationReport(
            report_id=f"REPORT_{self._report_counter:04d}",
            fix_id="",
            file_path=file_path,
            timestamp=datetime.now().isoformat(),
            overall_status=overall_status,
            overall_score=overall_score,
            results=results,
            summary=summary,
            passed_count=passed,
            failed_count=failed,
            warning_count=warning,
            critical_issues=critical_issues
        )

    def _create_error_report(self, file_path: str, error_message: str) -> VerificationReport:
        self._report_counter += 1

        return VerificationReport(
            report_id=f"REPORT_{self._report_counter:04d}",
            fix_id="",
            file_path=file_path,
            timestamp=datetime.now().isoformat(),
            overall_status=VerificationStatus.ERROR,
            overall_score=0,
            results=[],
            summary=f"验证失败: {error_message}"
        )

    def _generate_summary(self, results: List[VerificationResult], overall_score: float) -> str:
        parts = [f"验证总分: {overall_score:.1f}/100"]

        for result in results:
            status_icon = {
                VerificationStatus.PASSED: "✅",
                VerificationStatus.FAILED: "❌",
                VerificationStatus.WARNING: "⚠️",
                VerificationStatus.SKIPPED: "⏭️"
            }.get(result.status, "❓")

            parts.append(
                f"{status_icon} {result.verification_type.name}: {result.score:.1f}/{result.max_score}"
            )

        return "\n".join(parts)

    def print_report(self, report: VerificationReport) -> None:
        print("\n" + "=" * 80)
        print("修复验证报告")
        print("=" * 80)
        print(f"报告ID: {report.report_id}")
        print(f"文件路径: {report.file_path}")
        print(f"验证时间: {report.timestamp}")

        status_icons = {
            VerificationStatus.PASSED: "✅",
            VerificationStatus.FAILED: "❌",
            VerificationStatus.WARNING: "⚠️",
            VerificationStatus.ERROR: "🔴"
        }

        icon = status_icons.get(report.overall_status, "❓")
        print(f"总体状态: {icon} {report.overall_status.value.upper()}")
        print(f"总分: {report.overall_score:.1f}/100")

        print(f"\n通过: {report.passed_count}, 失败: {report.failed_count}, 警告: {report.warning_count}")

        print("\n" + "-" * 80)
        print("验证结果详情")
        print("-" * 80)

        for result in report.results:
            icon = status_icons.get(result.status, "❓")
            print(f"\n{icon} [{result.verification_type.name}]")
            print(f"   得分: {result.score:.1f}/{result.max_score}")
            print(f"   状态: {result.status.value}")
            print(f"   耗时: {result.execution_time_ms:.2f}ms")

            if result.issues:
                print(f"   问题 ({len(result.issues)}):")
                for issue in result.issues[:3]:
                    print(f"     - [{issue.severity.value}] {issue.message}")

            if result.recommendations:
                print("   建议:")
                for rec in result.recommendations:
                    print(f"     • {rec}")

        if report.critical_issues:
            print("\n" + "-" * 80)
            print("严重问题")
            print("-" * 80)
            for issue in report.critical_issues:
                print(f"  🔴 [{issue.verification_type.name}] {issue.message}")
                if issue.suggestion:
                    print(f"     建议: {issue.suggestion}")

        print("\n" + "-" * 80)
        print("摘要")
        print("-" * 80)
        print(report.summary)

    def save_report(self, report: VerificationReport, output_path: Optional[Path] = None) -> Path:
        if output_path is None:
            output_dir = get_path_config().REPORTS_DIR / "verification"
            output_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = output_dir / f"verification_{timestamp}.json"

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)

        logger.info(f"报告已保存: {output_path}")
        return output_path


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="增强版修复验证器",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument("--file", type=str, help="要验证的文件路径")
    parser.add_argument("--before", type=str, help="修复前的文件内容路径")
    parser.add_argument("--verify-all", action="store_true", help="执行所有验证")
    parser.add_argument("--verify-syntax", action="store_true", help="验证语法")
    parser.add_argument("--verify-test", action="store_true", help="验证测试")
    parser.add_argument("--verify-performance", action="store_true", help="验证性能")
    parser.add_argument("--verify-security", action="store_true", help="验证安全")
    parser.add_argument("--verify-quality", action="store_true", help="验证代码质量")
    parser.add_argument("--report", type=str, help="报告输出路径")

    args = parser.parse_args()

    if not args.file:
        print("请指定 --file 参数")
        return 1

    verifier = FixVerificationEnhanced()

    verification_types = []
    if args.verify_all:
        verification_types = None
    else:
        if args.verify_syntax:
            verification_types.append(VerificationType.SYNTAX)
        if args.verify_test:
            verification_types.append(VerificationType.TEST)
        if args.verify_performance:
            verification_types.append(VerificationType.PERFORMANCE)
        if args.verify_security:
            verification_types.append(VerificationType.SECURITY)
        if args.verify_quality:
            verification_types.append(VerificationType.CODE_QUALITY)

    if not verification_types and not args.verify_all:
        verification_types = None

    before_content = None
    if args.before:
        with open(args.before, 'r', encoding='utf-8') as f:
            before_content = f.read()

    report = verifier.verify_file(args.file, before_content, verification_types)

    verifier.print_report(report)

    if args.report:
        verifier.save_report(report, Path(args.report))

    return 0 if report.overall_status == VerificationStatus.PASSED else 1


if __name__ == "__main__":
    sys.exit(main())
