#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优化报告生成器

整合多种扫描器的结果，生成综合优化报告，并提供自动修复功能：
1. 收集优化结果 - 从 systematic_optimizer.py 收集扫描结果
2. 收集安全扫描结果 - 从 security_scanner.py 收集安全扫描结果
3. 收集测试结果 - 从 regression_test.py 收集测试结果
4. 生成综合优化报告 - 汇总所有发现的问题，按严重程度排序，按模块分组
5. 自动修复功能 - 根据问题类型选择修复策略，执行自动修复，验证修复结果
6. 修复验证机制 - 重新运行相关测试，验证问题是否解决，生成修复报告

使用示例:
    python optimization_report_generator.py
    python optimization_report_generator.py --auto-fix
    python optimization_report_generator.py --fix-types code_smell,unused_import
    python optimization_report_generator.py --output json --output-file report.json
    python optimization_report_generator.py --verbose
"""

import os
import re
import ast
import json
import argparse
import logging
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from abc import ABC, abstractmethod


class IssueSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class IssueCategory(Enum):
    ARCHITECTURE = "architecture"
    SECURITY = "security"
    CODE_QUALITY = "code_quality"
    PERFORMANCE = "performance"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    STYLE = "style"


class FixStatus(Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    MANUAL_REQUIRED = "manual_required"


@dataclass
class UnifiedIssue:
    issue_id: str
    source: str
    category: IssueCategory
    issue_type: str
    description: str
    severity: IssueSeverity
    file_path: str
    line_number: Optional[int] = None
    line_end: Optional[int] = None
    code_snippet: str = ""
    suggestion: str = ""
    fix_strategy: str = ""
    auto_fixable: bool = False
    fix_status: FixStatus = FixStatus.PENDING
    fix_details: str = ""
    related_issues: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "issue_id": self.issue_id,
            "source": self.source,
            "category": self.category.value,
            "issue_type": self.issue_type,
            "description": self.description,
            "severity": self.severity.value,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "line_end": self.line_end,
            "code_snippet": self.code_snippet,
            "suggestion": self.suggestion,
            "fix_strategy": self.fix_strategy,
            "auto_fixable": self.auto_fixable,
            "fix_status": self.fix_status.value,
            "fix_details": self.fix_details,
            "related_issues": self.related_issues
        }


@dataclass
class ModuleSummary:
    module_name: str
    total_issues: int
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    info_count: int = 0
    issues: List[UnifiedIssue] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "module_name": self.module_name,
            "total_issues": self.total_issues,
            "critical_count": self.critical_count,
            "high_count": self.high_count,
            "medium_count": self.medium_count,
            "low_count": self.low_count,
            "info_count": self.info_count,
            "issues": [i.to_dict() for i in self.issues]
        }


@dataclass
class FixResult:
    issue_id: str
    status: FixStatus
    details: str
    changes_made: List[Dict[str, Any]] = field(default_factory=list)
    verification_passed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "issue_id": self.issue_id,
            "status": self.status.value,
            "details": self.details,
            "changes_made": self.changes_made,
            "verification_passed": self.verification_passed
        }


@dataclass
class OptimizationReport:
    timestamp: str
    project_root: str
    total_issues: int
    modules: List[ModuleSummary]
    severity_summary: Dict[str, int]
    category_summary: Dict[str, int]
    source_summary: Dict[str, int]
    auto_fixable_count: int
    fix_results: List[FixResult]
    verification_report: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "project_root": self.project_root,
            "total_issues": self.total_issues,
            "modules": [m.to_dict() for m in self.modules],
            "severity_summary": self.severity_summary,
            "category_summary": self.category_summary,
            "source_summary": self.source_summary,
            "auto_fixable_count": self.auto_fixable_count,
            "fix_results": [f.to_dict() for f in self.fix_results],
            "verification_report": self.verification_report
        }


class BaseFixer(ABC):
    def __init__(self, project_root: Path, logger: logging.Logger):
        self.project_root = project_root
        self.logger = logger

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def supported_types(self) -> List[str]:
        pass

    @abstractmethod
    def can_fix(self, issue: UnifiedIssue) -> bool:
        pass

    @abstractmethod
    def fix(self, issue: UnifiedIssue) -> FixResult:
        pass

    def _read_file(self, file_path: Path) -> Optional[str]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            self.logger.warning(f"无法读取文件 {file_path}: {e}")
            return None

    def _write_file(self, file_path: Path, content: str) -> bool:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            self.logger.error(f"无法写入文件 {file_path}: {e}")
            return False

    def _backup_file(self, file_path: Path) -> Optional[Path]:
        try:
            backup_path = file_path.with_suffix(file_path.suffix + '.bak')
            shutil.copy2(file_path, backup_path)
            return backup_path
        except Exception as e:
            self.logger.warning(f"无法备份文件 {file_path}: {e}")
            return None


class UnusedImportFixer(BaseFixer):
    @property
    def name(self) -> str:
        return "未使用导入修复器"

    @property
    def supported_types(self) -> List[str]:
        return ["unused_import"]

    def can_fix(self, issue: UnifiedIssue) -> bool:
        return issue.issue_type in self.supported_types

    def fix(self, issue: UnifiedIssue) -> FixResult:
        file_path = self.project_root / issue.file_path
        if not file_path.exists():
            return FixResult(
                issue_id=issue.issue_id,
                status=FixStatus.FAILED,
                details=f"文件不存在: {file_path}"
            )

        content = self._read_file(file_path)
        if not content:
            return FixResult(
                issue_id=issue.issue_id,
                status=FixStatus.FAILED,
                details="无法读取文件内容"
            )

        self._backup_file(file_path)

        lines = content.split('\n')
        new_lines = []
        removed_imports = []

        import_match = re.search(r"import\s+(\w+)", issue.description)
        if not import_match:
            import_match = re.search(r"from\s+\S+\s+import\s+(\w+)", issue.description)

        if import_match:
            import_name = import_match.group(1)
        else:
            words = issue.description.split()
            import_name = words[-1] if words else ""

        for i, line in enumerate(lines):
            if issue.line_number and i + 1 == issue.line_number:
                if import_name and import_name in line:
                    if line.strip().startswith("import "):
                        continue
                    elif line.strip().startswith("from "):
                        if "," in line:
                            new_line = self._remove_import_from_line(line, import_name)
                            if new_line.strip():
                                new_lines.append(new_line)
                            removed_imports.append(import_name)
                            continue
                        else:
                            continue
            new_lines.append(line)

        new_content = '\n'.join(new_lines)

        if self._write_file(file_path, new_content):
            return FixResult(
                issue_id=issue.issue_id,
                status=FixStatus.SUCCESS,
                details=f"已移除未使用的导入: {import_name}",
                changes_made=[{
                    "file": str(file_path),
                    "action": "remove_import",
                    "import_name": import_name
                }]
            )
        else:
            return FixResult(
                issue_id=issue.issue_id,
                status=FixStatus.FAILED,
                details="写入文件失败"
            )

    def _remove_import_from_line(self, line: str, import_name: str) -> str:
        parts = line.split("import")
        if len(parts) == 2:
            imports = [i.strip() for i in parts[1].split(",")]
            imports = [i for i in imports if i and i != import_name]
            if imports:
                return parts[0] + "import " + ", ".join(imports)
        return line


class TrailingWhitespaceFixer(BaseFixer):
    @property
    def name(self) -> str:
        return "尾随空格修复器"

    @property
    def supported_types(self) -> List[str]:
        return ["trailing_whitespace"]

    def can_fix(self, issue: UnifiedIssue) -> bool:
        return issue.issue_type in self.supported_types

    def fix(self, issue: UnifiedIssue) -> FixResult:
        file_path = self.project_root / issue.file_path
        if not file_path.exists():
            return FixResult(
                issue_id=issue.issue_id,
                status=FixStatus.FAILED,
                details=f"文件不存在: {file_path}"
            )

        content = self._read_file(file_path)
        if not content:
            return FixResult(
                issue_id=issue.issue_id,
                status=FixStatus.FAILED,
                details="无法读取文件内容"
            )

        self._backup_file(file_path)

        lines = content.split('\n')
        fixed_lines = 0

        for i, line in enumerate(lines):
            if issue.line_number and i + 1 == issue.line_number:
                stripped = line.rstrip()
                if stripped != line.rstrip('\n').rstrip():
                    lines[i] = stripped
                    fixed_lines += 1

        new_content = '\n'.join(lines)

        if self._write_file(file_path, new_content):
            return FixResult(
                issue_id=issue.issue_id,
                status=FixStatus.SUCCESS,
                details=f"已移除尾随空格",
                changes_made=[{
                    "file": str(file_path),
                    "action": "remove_trailing_whitespace",
                    "line": issue.line_number
                }]
            )
        else:
            return FixResult(
                issue_id=issue.issue_id,
                status=FixStatus.FAILED,
                details="写入文件失败"
            )


class LineTooLongFixer(BaseFixer):
    @property
    def name(self) -> str:
        return "行过长修复器"

    @property
    def supported_types(self) -> List[str]:
        return ["line_too_long"]

    def can_fix(self, issue: UnifiedIssue) -> bool:
        return issue.issue_type in self.supported_types

    def fix(self, issue: UnifiedIssue) -> FixResult:
        file_path = self.project_root / issue.file_path
        if not file_path.exists():
            return FixResult(
                issue_id=issue.issue_id,
                status=FixStatus.FAILED,
                details=f"文件不存在: {file_path}"
            )

        content = self._read_file(file_path)
        if not content:
            return FixResult(
                issue_id=issue.issue_id,
                status=FixStatus.FAILED,
                details="无法读取文件内容"
            )

        lines = content.split('\n')
        line_idx = (issue.line_number or 1) - 1

        if line_idx >= len(lines):
            return FixResult(
                issue_id=issue.issue_id,
                status=FixStatus.FAILED,
                details="行号超出范围"
            )

        original_line = lines[line_idx]

        if len(original_line) <= 120:
            return FixResult(
                issue_id=issue.issue_id,
                status=FixStatus.SKIPPED,
                details="行长度已在限制内"
            )

        return FixResult(
            issue_id=issue.issue_id,
            status=FixStatus.MANUAL_REQUIRED,
            details="行过长问题需要手动修复，建议拆分代码或简化表达式",
            changes_made=[{
                "file": str(file_path),
                "line": issue.line_number,
                "original_length": len(original_line)
            }]
        )


class MissingDocstringFixer(BaseFixer):
    @property
    def name(self) -> str:
        return "缺少文档字符串修复器"

    @property
    def supported_types(self) -> List[str]:
        return ["missing_docstring"]

    def can_fix(self, issue: UnifiedIssue) -> bool:
        return issue.issue_type in self.supported_types

    def fix(self, issue: UnifiedIssue) -> FixResult:
        file_path = self.project_root / issue.file_path
        if not file_path.exists():
            return FixResult(
                issue_id=issue.issue_id,
                status=FixStatus.FAILED,
                details=f"文件不存在: {file_path}"
            )

        content = self._read_file(file_path)
        if not content:
            return FixResult(
                issue_id=issue.issue_id,
                status=FixStatus.FAILED,
                details="无法读取文件内容"
            )

        self._backup_file(file_path)

        lines = content.split('\n')
        line_idx = (issue.line_number or 1) - 1

        if line_idx >= len(lines):
            return FixResult(
                issue_id=issue.issue_id,
                status=FixStatus.FAILED,
                details="行号超出范围"
            )

        line = lines[line_idx]
        indent = len(line) - len(line.lstrip())
        indent_str = ' ' * indent

        name_match = re.search(r'(def|class)\s+(\w+)', line)
        if name_match:
            item_type = name_match.group(1)
            item_name = name_match.group(2)
        else:
            item_type = "function"
            item_name = "unknown"

        docstring = f'{indent_str}"""{item_name} 的文档字符串"""'

        lines.insert(line_idx + 1, docstring)
        new_content = '\n'.join(lines)

        if self._write_file(file_path, new_content):
            return FixResult(
                issue_id=issue.issue_id,
                status=FixStatus.SUCCESS,
                details=f"已添加文档字符串",
                changes_made=[{
                    "file": str(file_path),
                    "action": "add_docstring",
                    "line": issue.line_number
                }]
            )
        else:
            return FixResult(
                issue_id=issue.issue_id,
                status=FixStatus.FAILED,
                details="写入文件失败"
            )


class BareExceptFixer(BaseFixer):
    @property
    def name(self) -> str:
        return "裸异常修复器"

    @property
    def supported_types(self) -> List[str]:
        return ["bare_except"]

    def can_fix(self, issue: UnifiedIssue) -> bool:
        return issue.issue_type in self.supported_types

    def fix(self, issue: UnifiedIssue) -> FixResult:
        file_path = self.project_root / issue.file_path
        if not file_path.exists():
            return FixResult(
                issue_id=issue.issue_id,
                status=FixStatus.FAILED,
                details=f"文件不存在: {file_path}"
            )

        content = self._read_file(file_path)
        if not content:
            return FixResult(
                issue_id=issue.issue_id,
                status=FixStatus.FAILED,
                details="无法读取文件内容"
            )

        self._backup_file(file_path)

        lines = content.split('\n')
        line_idx = (issue.line_number or 1) - 1

        if line_idx >= len(lines):
            return FixResult(
                issue_id=issue.issue_id,
                status=FixStatus.FAILED,
                details="行号超出范围"
            )

        line = lines[line_idx]
        if re.match(r'\s*except\s*:', line):
            indent = len(line) - len(line.lstrip())
            indent_str = ' ' * indent
            lines[line_idx] = f'{indent_str}except Exception as e:'
            new_content = '\n'.join(lines)

            if self._write_file(file_path, new_content):
                return FixResult(
                    issue_id=issue.issue_id,
                    status=FixStatus.SUCCESS,
                    details="已将裸异常改为 Exception",
                    changes_made=[{
                        "file": str(file_path),
                        "action": "fix_bare_except",
                        "line": issue.line_number
                    }]
                )

        return FixResult(
            issue_id=issue.issue_id,
            status=FixStatus.FAILED,
            details="无法修复此裸异常"
        )


class CodeSmellFixer(BaseFixer):
    @property
    def name(self) -> str:
        return "代码异味修复器"

    @property
    def supported_types(self) -> List[str]:
        return ["code_smell", "mutable_default"]

    def can_fix(self, issue: UnifiedIssue) -> bool:
        return issue.issue_type in self.supported_types

    def fix(self, issue: UnifiedIssue) -> FixResult:
        if issue.issue_type == "mutable_default":
            return self._fix_mutable_default(issue)
        return FixResult(
            issue_id=issue.issue_id,
            status=FixStatus.MANUAL_REQUIRED,
            details="此代码异味需要手动修复"
        )

    def _fix_mutable_default(self, issue: UnifiedIssue) -> FixResult:
        file_path = self.project_root / issue.file_path
        if not file_path.exists():
            return FixResult(
                issue_id=issue.issue_id,
                status=FixStatus.FAILED,
                details=f"文件不存在: {file_path}"
            )

        content = self._read_file(file_path)
        if not content:
            return FixResult(
                issue_id=issue.issue_id,
                status=FixStatus.FAILED,
                details="无法读取文件内容"
            )

        self._backup_file(file_path)

        lines = content.split('\n')
        line_idx = (issue.line_number or 1) - 1

        if line_idx >= len(lines):
            return FixResult(
                issue_id=issue.issue_id,
                status=FixStatus.FAILED,
                details="行号超出范围"
            )

        line = lines[line_idx]

        line = re.sub(r'=\s*\[\s*\]', '= None', line)
        line = re.sub(r'=\s*\{\s*\}', '= None', line)

        lines[line_idx] = line

        func_match = re.search(r'def\s+(\w+)\s*\(([^)]*)\)', line)
        if func_match:
            func_name = func_match.group(1)
            params = func_match.group(2)

            if '= None' in params:
                indent = len(line) - len(line.lstrip())
                indent_str = ' ' * (indent + 4)

                param_names = re.findall(r'(\w+)\s*=\s*None', params)
                init_lines = []
                for param_name in param_names:
                    init_lines.append(f'{indent_str}if {param_name} is None:')
                    init_lines.append(f'{indent_str}    {param_name} = []')

                if init_lines:
                    insert_idx = line_idx + 1
                    while insert_idx < len(lines) and lines[insert_idx].strip().startswith('"""'):
                        insert_idx += 1
                    for i, init_line in enumerate(init_lines):
                        lines.insert(insert_idx + i, init_line)

        new_content = '\n'.join(lines)

        if self._write_file(file_path, new_content):
            return FixResult(
                issue_id=issue.issue_id,
                status=FixStatus.SUCCESS,
                details="已修复可变默认参数",
                changes_made=[{
                    "file": str(file_path),
                    "action": "fix_mutable_default",
                    "line": issue.line_number
                }]
            )
        else:
            return FixResult(
                issue_id=issue.issue_id,
                status=FixStatus.FAILED,
                details="写入文件失败"
            )


class ResultCollector:
    def __init__(self, project_root: Path, logger: logging.Logger):
        self.project_root = project_root
        self.logger = logger
        self.issues: List[UnifiedIssue] = []

    def collect_systematic_optimizer_results(self) -> List[UnifiedIssue]:
        self.logger.info("收集系统性优化扫描结果...")
        issues = []

        report_file = self.project_root / "reports" / "systematic_optimization_latest.json"
        if not report_file.exists():
            self.logger.warning(f"未找到系统性优化报告: {report_file}")
            return issues

        try:
            with open(report_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            for result in data.get("results", []):
                scanner_name = result.get("scanner_name", "unknown")
                category_str = result.get("category", "code_review")

                try:
                    category = IssueCategory(category_str)
                except ValueError:
                    category = IssueCategory.CODE_QUALITY

                for issue_data in result.get("issues", []):
                    severity_str = issue_data.get("severity", "medium")
                    try:
                        severity = IssueSeverity(severity_str)
                    except ValueError:
                        severity = IssueSeverity.MEDIUM

                    issue = UnifiedIssue(
                        issue_id=self._generate_issue_id("sys", issue_data),
                        source=f"systematic_optimizer:{scanner_name}",
                        category=category,
                        issue_type=issue_data.get("issue_type", "unknown"),
                        description=issue_data.get("description", ""),
                        severity=severity,
                        file_path=issue_data.get("file_path", ""),
                        line_number=issue_data.get("line_number"),
                        code_snippet=issue_data.get("code_snippet", ""),
                        suggestion=issue_data.get("suggestion", ""),
                        auto_fixable=self._is_auto_fixable(issue_data.get("issue_type", ""))
                    )
                    issues.append(issue)

        except Exception as e:
            self.logger.error(f"解析系统性优化报告失败: {e}")

        self.logger.info(f"从系统性优化扫描收集到 {len(issues)} 个问题")
        return issues

    def collect_security_scanner_results(self) -> List[UnifiedIssue]:
        self.logger.info("收集安全扫描结果...")
        issues = []

        report_file = self.project_root / "reports" / "security_scan_latest.json"
        if not report_file.exists():
            self.logger.warning(f"未找到安全扫描报告: {report_file}")
            return issues

        try:
            with open(report_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            for result in data.get("results", []):
                check_name = result.get("check_name", "unknown")

                for issue_data in result.get("issues", []):
                    severity_str = issue_data.get("severity", "medium")
                    try:
                        severity = IssueSeverity(severity_str)
                    except ValueError:
                        severity = IssueSeverity.MEDIUM

                    issue = UnifiedIssue(
                        issue_id=self._generate_issue_id("sec", issue_data),
                        source=f"security_scanner:{check_name}",
                        category=IssueCategory.SECURITY,
                        issue_type=issue_data.get("issue_type", "unknown"),
                        description=issue_data.get("description", ""),
                        severity=severity,
                        file_path=issue_data.get("file_path", ""),
                        line_number=issue_data.get("line_number"),
                        code_snippet=issue_data.get("code_snippet", ""),
                        suggestion=issue_data.get("suggestion", ""),
                        auto_fixable=False
                    )
                    issues.append(issue)

        except Exception as e:
            self.logger.error(f"解析安全扫描报告失败: {e}")

        self.logger.info(f"从安全扫描收集到 {len(issues)} 个问题")
        return issues

    def collect_regression_test_results(self) -> List[UnifiedIssue]:
        self.logger.info("收集回归测试结果...")
        issues = []

        report_file = self.project_root / "reports" / "regression_report_latest.json"
        if not report_file.exists():
            self.logger.warning(f"未找到回归测试报告: {report_file}")
            return issues

        try:
            with open(report_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            for issue_data in data.get("issues", []):
                severity_str = issue_data.get("severity", "medium")
                try:
                    severity = IssueSeverity(severity_str)
                except ValueError:
                    severity = IssueSeverity.MEDIUM

                issue = UnifiedIssue(
                    issue_id=issue_data.get("issue_id", self._generate_issue_id("test", issue_data)),
                    source="regression_test",
                    category=IssueCategory.TESTING,
                    issue_type="test_failure",
                    description=issue_data.get("description", ""),
                    severity=severity,
                    file_path=issue_data.get("file_path", ""),
                    line_number=issue_data.get("line_start"),
                    line_end=issue_data.get("line_end"),
                    suggestion=issue_data.get("suggested_fix", ""),
                    auto_fixable=False
                )
                issues.append(issue)

            for suite_data in data.get("test_suites", []):
                for test_case in suite_data.get("test_cases", []):
                    if test_case.get("status") in ["failed", "error"]:
                        severity = IssueSeverity.HIGH if test_case.get("status") == "error" else IssueSeverity.MEDIUM
                        issue = UnifiedIssue(
                            issue_id=self._generate_issue_id("test", test_case),
                            source=f"regression_test:{suite_data.get('name', 'unknown')}",
                            category=IssueCategory.TESTING,
                            issue_type="test_case_failure",
                            description=f"测试用例失败: {test_case.get('error_message', '未知错误')}",
                            severity=severity,
                            file_path=test_case.get("file_path", ""),
                            line_number=test_case.get("line_number"),
                            auto_fixable=False
                        )
                        issues.append(issue)

        except Exception as e:
            self.logger.error(f"解析回归测试报告失败: {e}")

        self.logger.info(f"从回归测试收集到 {len(issues)} 个问题")
        return issues

    def collect_all_results(self) -> List[UnifiedIssue]:
        self.issues = []
        self.issues.extend(self.collect_systematic_optimizer_results())
        self.issues.extend(self.collect_security_scanner_results())
        self.issues.extend(self.collect_regression_test_results())

        self._deduplicate_issues()
        self._find_related_issues()

        return self.issues

    def _generate_issue_id(self, prefix: str, data: Dict[str, Any]) -> str:
        import hashlib
        content = json.dumps(data, sort_keys=True)
        hash_val = hashlib.md5(content.encode()).hexdigest()[:8]
        return f"{prefix.upper()}-{hash_val}"

    def _is_auto_fixable(self, issue_type: str) -> bool:
        auto_fixable_types = [
            "unused_import",
            "trailing_whitespace",
            "missing_docstring",
            "bare_except",
            "mutable_default"
        ]
        return issue_type in auto_fixable_types

    def _deduplicate_issues(self):
        seen = {}
        unique_issues = []

        for issue in self.issues:
            key = (issue.file_path, issue.line_number, issue.issue_type)
            if key not in seen:
                seen[key] = issue
                unique_issues.append(issue)
            else:
                existing = seen[key]
                if issue.severity.value < existing.severity.value:
                    idx = unique_issues.index(existing)
                    unique_issues[idx] = issue
                    seen[key] = issue

        self.issues = unique_issues

    def _find_related_issues(self):
        file_issues: Dict[str, List[UnifiedIssue]] = {}
        for issue in self.issues:
            if issue.file_path:
                if issue.file_path not in file_issues:
                    file_issues[issue.file_path] = []
                file_issues[issue.file_path].append(issue)

        for file_path, issues in file_issues.items():
            if len(issues) > 1:
                for issue in issues:
                    issue.related_issues = [i.issue_id for i in issues if i.issue_id != issue.issue_id]


class OptimizationReportGenerator:
    FIXERS = [
        UnusedImportFixer,
        TrailingWhitespaceFixer,
        LineTooLongFixer,
        MissingDocstringFixer,
        BareExceptFixer,
        CodeSmellFixer
    ]

    SEVERITY_ORDER = {
        IssueSeverity.CRITICAL: 0,
        IssueSeverity.HIGH: 1,
        IssueSeverity.MEDIUM: 2,
        IssueSeverity.LOW: 3,
        IssueSeverity.INFO: 4
    }

    def __init__(self, project_root: Optional[Path] = None,
                 logger: Optional[logging.Logger] = None):
        self.project_root = project_root or get_path_config().SKILL_ROOT
        self.logger = logger or logging.getLogger(__name__)
        self.collector = ResultCollector(self.project_root, self.logger)
        self.fixers: List[BaseFixer] = []
        self.fix_results: List[FixResult] = []
        self._init_fixers()

    def _init_fixers(self):
        for fixer_class in self.FIXERS:
            self.fixers.append(fixer_class(self.project_root, self.logger))

    def collect_results(self) -> List[UnifiedIssue]:
        return self.collector.collect_all_results()

    def generate_report(self, issues: List[UnifiedIssue]) -> OptimizationReport:
        self.logger.info("生成综合优化报告...")

        issues.sort(key=lambda x: self.SEVERITY_ORDER.get(x.severity, 99))

        modules = self._group_by_module(issues)
        severity_summary = self._count_by_severity(issues)
        category_summary = self._count_by_category(issues)
        source_summary = self._count_by_source(issues)
        auto_fixable_count = sum(1 for i in issues if i.auto_fixable)

        return OptimizationReport(
            timestamp=datetime.now().isoformat(),
            project_root=str(self.project_root),
            total_issues=len(issues),
            modules=modules,
            severity_summary=severity_summary,
            category_summary=category_summary,
            source_summary=source_summary,
            auto_fixable_count=auto_fixable_count,
            fix_results=self.fix_results,
            verification_report={}
        )

    def _group_by_module(self, issues: List[UnifiedIssue]) -> List[ModuleSummary]:
        modules: Dict[str, ModuleSummary] = {}

        for issue in issues:
            module = self._extract_module(issue.file_path)
            if module not in modules:
                modules[module] = ModuleSummary(module_name=module, total_issues=0)

            modules[module].total_issues += 1
            modules[module].issues.append(issue)

            if issue.severity == IssueSeverity.CRITICAL:
                modules[module].critical_count += 1
            elif issue.severity == IssueSeverity.HIGH:
                modules[module].high_count += 1
            elif issue.severity == IssueSeverity.MEDIUM:
                modules[module].medium_count += 1
            elif issue.severity == IssueSeverity.LOW:
                modules[module].low_count += 1
            else:
                modules[module].info_count += 1

        return sorted(modules.values(), key=lambda x: x.total_issues, reverse=True)

    def _extract_module(self, file_path: str) -> str:
        if not file_path:
            return "unknown"

        parts = file_path.replace('\\', '/').split('/')
        if 'backend' in parts:
            idx = parts.index('backend')
            if idx + 1 < len(parts):
                return f"backend/{parts[idx + 1]}"
            return "backend"
        elif 'frontend' in parts:
            idx = parts.index('frontend')
            if idx + 1 < len(parts):
                return f"frontend/{parts[idx + 1]}"
            return "frontend"
        elif '.trae' in file_path:
            return "trae_skills"
        else:
            return parts[0] if parts else "root"

    def _count_by_severity(self, issues: List[UnifiedIssue]) -> Dict[str, int]:
        counts = {s.value: 0 for s in IssueSeverity}
        for issue in issues:
            counts[issue.severity.value] += 1
        return counts

    def _count_by_category(self, issues: List[UnifiedIssue]) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for issue in issues:
            cat = issue.category.value
            counts[cat] = counts.get(cat, 0) + 1
        return counts

    def _count_by_source(self, issues: List[UnifiedIssue]) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for issue in issues:
            source = issue.source.split(':')[0]
            counts[source] = counts.get(source, 0) + 1
        return counts

    def auto_fix(self, issues: List[UnifiedIssue],
                 fix_types: Optional[List[str]] = None,
                 dry_run: bool = False) -> List[FixResult]:
        self.logger.info("开始自动修复...")
        self.fix_results = []

        fixable_issues = [i for i in issues if i.auto_fixable]

        if fix_types:
            fixable_issues = [i for i in fixable_issues if i.issue_type in fix_types]

        self.logger.info(f"可自动修复的问题数: {len(fixable_issues)}")

        for issue in fixable_issues:
            fixer = self._get_fixer(issue)
            if fixer:
                if dry_run:
                    result = FixResult(
                        issue_id=issue.issue_id,
                        status=FixStatus.SKIPPED,
                        details="试运行模式，跳过修复"
                    )
                else:
                    result = fixer.fix(issue)
                    issue.fix_status = result.status
                    issue.fix_details = result.details

                self.fix_results.append(result)
            else:
                result = FixResult(
                    issue_id=issue.issue_id,
                    status=FixStatus.MANUAL_REQUIRED,
                    details="没有可用的自动修复器"
                )
                self.fix_results.append(result)

        success_count = sum(1 for r in self.fix_results if r.status == FixStatus.SUCCESS)
        self.logger.info(f"自动修复完成: {success_count}/{len(self.fix_results)} 成功")

        return self.fix_results

    def _get_fixer(self, issue: UnifiedIssue) -> Optional[BaseFixer]:
        for fixer in self.fixers:
            if fixer.can_fix(issue):
                return fixer
        return None

    def verify_fixes(self, issues: List[UnifiedIssue]) -> Dict[str, Any]:
        self.logger.info("验证修复结果...")

        verification_report = {
            "timestamp": datetime.now().isoformat(),
            "total_fixes": len(self.fix_results),
            "successful_fixes": sum(1 for r in self.fix_results if r.status == FixStatus.SUCCESS),
            "failed_fixes": sum(1 for r in self.fix_results if r.status == FixStatus.FAILED),
            "manual_required": sum(1 for r in self.fix_results if r.status == FixStatus.MANUAL_REQUIRED),
            "test_results": {},
            "remaining_issues": []
        }

        fixed_files = set()
        for result in self.fix_results:
            if result.status == FixStatus.SUCCESS:
                for change in result.changes_made:
                    if "file" in change:
                        fixed_files.add(change["file"])

        if fixed_files:
            test_result = self._run_related_tests(fixed_files)
            verification_report["test_results"] = test_result

        remaining = [i for i in issues if i.fix_status != FixStatus.SUCCESS]
        verification_report["remaining_issues"] = [i.to_dict() for i in remaining]

        return verification_report

    def _run_related_tests(self, fixed_files: Set[str]) -> Dict[str, Any]:
        self.logger.info(f"运行相关测试，涉及 {len(fixed_files)} 个文件...")

        result = {
            "status": "skipped",
            "message": "",
            "passed": 0,
            "failed": 0,
            "total": 0
        }

        backend_dir = self.project_root / "backend"
        if not backend_dir.exists():
            result["message"] = "后端目录不存在"
            return result

        has_backend_fixes = any('backend' in f for f in fixed_files)
        if not has_backend_fixes:
            result["message"] = "没有后端文件被修改"
            return result

        try:
            proc = subprocess.run(
                [sys.executable, "-m", "pytest", "-v", "-q", "--tb=no"],
                cwd=backend_dir,
                capture_output=True,
                text=True,
                timeout=300
            )

            output = proc.stdout + proc.stderr

            passed_match = re.search(r'(\d+) passed', output)
            failed_match = re.search(r'(\d+) failed', output)

            result["passed"] = int(passed_match.group(1)) if passed_match else 0
            result["failed"] = int(failed_match.group(1)) if failed_match else 0
            result["total"] = result["passed"] + result["failed"]
            result["status"] = "passed" if proc.returncode == 0 else "failed"
            result["message"] = f"测试完成: {result['passed']} 通过, {result['failed']} 失败"

        except subprocess.TimeoutExpired:
            result["status"] = "timeout"
            result["message"] = "测试运行超时"
        except Exception as e:
            result["status"] = "error"
            result["message"] = f"测试运行失败: {e}"

        return result

    def print_report(self, report: OptimizationReport):
        print("\n" + "=" * 80)
        print("综合优化报告")
        print("=" * 80)
        print(f"项目根目录: {report.project_root}")
        print(f"生成时间: {report.timestamp}")
        print(f"发现问题总数: {report.total_issues}")

        print("\n" + "-" * 80)
        print("严重程度统计")
        print("-" * 80)
        for severity in IssueSeverity:
            count = report.severity_summary.get(severity.value, 0)
            icon = {
                IssueSeverity.CRITICAL: "🔴",
                IssueSeverity.HIGH: "🟠",
                IssueSeverity.MEDIUM: "🟡",
                IssueSeverity.LOW: "🔵",
                IssueSeverity.INFO: "⚪"
            }.get(severity, "⚪")
            print(f"  {icon} {severity.value.upper()}: {count}")

        print("\n" + "-" * 80)
        print("问题类别统计")
        print("-" * 80)
        for category, count in sorted(report.category_summary.items(), key=lambda x: -x[1]):
            print(f"  {category}: {count}")

        print("\n" + "-" * 80)
        print("来源统计")
        print("-" * 80)
        for source, count in sorted(report.source_summary.items(), key=lambda x: -x[1]):
            print(f"  {source}: {count}")

        print(f"\n可自动修复的问题: {report.auto_fixable_count}")

        if report.modules:
            print("\n" + "-" * 80)
            print("模块问题分布 (Top 10)")
            print("-" * 80)
            for module in report.modules[:10]:
                print(f"\n  [{module.module_name}] 总计: {module.total_issues}")
                if module.critical_count:
                    print(f"    🔴 严重: {module.critical_count}")
                if module.high_count:
                    print(f"    🟠 高危: {module.high_count}")
                if module.medium_count:
                    print(f"    🟡 中等: {module.medium_count}")
                if module.low_count:
                    print(f"    🔵 低危: {module.low_count}")

        if report.fix_results:
            print("\n" + "-" * 80)
            print("修复结果")
            print("-" * 80)
            success = sum(1 for r in report.fix_results if r.status == FixStatus.SUCCESS)
            failed = sum(1 for r in report.fix_results if r.status == FixStatus.FAILED)
            manual = sum(1 for r in report.fix_results if r.status == FixStatus.MANUAL_REQUIRED)
            print(f"  成功: {success}")
            print(f"  失败: {failed}")
            print(f"  需手动修复: {manual}")

        if report.verification_report:
            print("\n" + "-" * 80)
            print("验证报告")
            print("-" * 80)
            vr = report.verification_report
            print(f"  总修复数: {vr.get('total_fixes', 0)}")
            print(f"  成功修复: {vr.get('successful_fixes', 0)}")
            print(f"  剩余问题: {len(vr.get('remaining_issues', []))}")

            test_results = vr.get('test_results', {})
            if test_results.get('status') != 'skipped':
                print(f"\n  测试结果: {test_results.get('status', 'unknown')}")
                print(f"  {test_results.get('message', '')}")

        all_issues = []
        for module in report.modules:
            all_issues.extend(module.issues)

        if all_issues:
            print("\n" + "-" * 80)
            print("发现的问题 (按严重程度排序，显示前 50 个)")
            print("-" * 80)

            for issue in all_issues[:50]:
                icon = {
                    IssueSeverity.CRITICAL: "🔴",
                    IssueSeverity.HIGH: "🟠",
                    IssueSeverity.MEDIUM: "🟡",
                    IssueSeverity.LOW: "🔵",
                    IssueSeverity.INFO: "⚪"
                }.get(issue.severity, "⚪")

                print(f"\n{icon} [{issue.severity.value.upper()}] {issue.issue_type}")
                print(f"   ID: {issue.issue_id}")
                print(f"   来源: {issue.source}")
                print(f"   文件: {issue.file_path}")
                if issue.line_number:
                    print(f"   行号: {issue.line_number}")
                print(f"   描述: {issue.description}")
                if issue.suggestion:
                    print(f"   建议: {issue.suggestion}")
                if issue.auto_fixable:
                    fix_icon = "✅" if issue.fix_status == FixStatus.SUCCESS else "⏳"
                    print(f"   可自动修复: 是 {fix_icon}")

            if len(all_issues) > 50:
                print(f"\n... 还有 {len(all_issues) - 50} 个问题未显示")

    def save_report(self, report: OptimizationReport, output_dir: Optional[Path] = None) -> Path:
        if output_dir is None:
            output_dir = get_path_config().REPORTS_DIR
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = output_dir / f"optimization_comprehensive_{timestamp}.json"

        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)

        latest_path = output_dir / "optimization_comprehensive_latest.json"
        with open(latest_path, 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)

        self.logger.info(f"报告已保存: {report_path}")
        return report_path


def setup_logger(verbose: bool = False) -> logging.Logger:
    logger = logging.getLogger("OptimizationReportGenerator")
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
    parser = argparse.ArgumentParser(
        description="优化报告生成器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python optimization_report_generator.py
  python optimization_report_generator.py --auto-fix
  python optimization_report_generator.py --fix-types unused_import,trailing_whitespace
  python optimization_report_generator.py --dry-run
  python optimization_report_generator.py --output json --output-file report.json
  python optimization_report_generator.py --verbose
        """
    )

    parser.add_argument(
        "--auto-fix",
        action="store_true",
        help="自动修复可修复的问题"
    )

    parser.add_argument(
        "--fix-types",
        type=str,
        help="指定要修复的问题类型，用逗号分隔"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="试运行模式，不实际修改文件"
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

    generator = OptimizationReportGenerator(logger=logger)

    issues = generator.collect_results()

    if args.auto_fix:
        fix_types = None
        if args.fix_types:
            fix_types = [t.strip() for t in args.fix_types.split(",")]

        generator.auto_fix(issues, fix_types, args.dry_run)

        verification = generator.verify_fixes(issues)

        report = generator.generate_report(issues)
        report.verification_report = verification
    else:
        report = generator.generate_report(issues)

    generator.print_report(report)

    report_path = generator.save_report(report)
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

    critical_count = report.severity_summary.get("critical", 0)
    high_count = report.severity_summary.get("high", 0)

    if critical_count > 0:
        return 2
    elif high_count > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
