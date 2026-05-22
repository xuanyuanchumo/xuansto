#!/usr/bin/env python3
"""
自完善循环系统
实现问题发现→分析→修复→验证→学习→优化的完整闭环
"""

import json
import os
import sys
import subprocess
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict
import logging
import traceback


class IssueType(Enum):
    BUG = "bug"
    PERFORMANCE = "performance"
    SECURITY = "security"
    CODE_QUALITY = "code_quality"
    ARCHITECTURE = "architecture"
    DEPENDENCY = "dependency"
    DOCUMENTATION = "documentation"
    TEST = "test"
    CONFIGURATION = "configuration"


class IssueSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class IssueStatus(Enum):
    DISCOVERED = "discovered"
    ANALYZED = "analyzed"
    FIXING = "fixing"
    FIXED = "fixed"
    VERIFIED = "verified"
    FAILED = "failed"
    IGNORED = "ignored"


class LearningType(Enum):
    PATTERN = "pattern"
    BEST_PRACTICE = "best_practice"
    ANTI_PATTERN = "anti_pattern"
    FIX_STRATEGY = "fix_strategy"
    OPTIMIZATION = "optimization"


class Priority(Enum):
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    INFO = 5


@dataclass
class Issue:
    issue_id: str
    issue_type: IssueType
    severity: IssueSeverity
    title: str
    description: str
    location: str
    status: IssueStatus
    discovered_at: str
    file_path: str = ""
    line_number: int = 0
    code_snippet: str = ""
    suggested_fix: str = ""
    actual_fix: str = ""
    root_cause: str = ""
    impact_analysis: str = ""
    fix_strategy: str = ""
    verification_result: str = ""
    learned_lessons: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "issue_id": self.issue_id,
            "issue_type": self.issue_type.value,
            "severity": self.severity.value,
            "title": self.title,
            "description": self.description,
            "location": self.location,
            "status": self.status.value,
            "discovered_at": self.discovered_at,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "code_snippet": self.code_snippet,
            "suggested_fix": self.suggested_fix,
            "actual_fix": self.actual_fix,
            "root_cause": self.root_cause,
            "impact_analysis": self.impact_analysis,
            "fix_strategy": self.fix_strategy,
            "verification_result": self.verification_result,
            "learned_lessons": self.learned_lessons,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Issue":
        return cls(
            issue_id=data.get("issue_id", ""),
            issue_type=IssueType(data.get("issue_type", "bug")),
            severity=IssueSeverity(data.get("severity", "medium")),
            title=data.get("title", ""),
            description=data.get("description", ""),
            location=data.get("location", ""),
            status=IssueStatus(data.get("status", "discovered")),
            discovered_at=data.get("discovered_at", ""),
            file_path=data.get("file_path", ""),
            line_number=data.get("line_number", 0),
            code_snippet=data.get("code_snippet", ""),
            suggested_fix=data.get("suggested_fix", ""),
            actual_fix=data.get("actual_fix", ""),
            root_cause=data.get("root_cause", ""),
            impact_analysis=data.get("impact_analysis", ""),
            fix_strategy=data.get("fix_strategy", ""),
            verification_result=data.get("verification_result", ""),
            learned_lessons=data.get("learned_lessons", []),
            metadata=data.get("metadata", {})
        )


@dataclass
class LearningRecord:
    learning_id: str
    learning_type: LearningType
    title: str
    description: str
    context: str
    solution: str
    effectiveness: float
    created_at: str
    applied_count: int = 0
    success_rate: float = 0.0
    tags: List[str] = field(default_factory=list)
    related_issues: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "learning_id": self.learning_id,
            "learning_type": self.learning_type.value,
            "title": self.title,
            "description": self.description,
            "context": self.context,
            "solution": self.solution,
            "effectiveness": self.effectiveness,
            "created_at": self.created_at,
            "applied_count": self.applied_count,
            "success_rate": self.success_rate,
            "tags": self.tags,
            "related_issues": self.related_issues
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LearningRecord":
        return cls(
            learning_id=data.get("learning_id", ""),
            learning_type=LearningType(data.get("learning_type", "pattern")),
            title=data.get("title", ""),
            description=data.get("description", ""),
            context=data.get("context", ""),
            solution=data.get("solution", ""),
            effectiveness=data.get("effectiveness", 0.0),
            created_at=data.get("created_at", ""),
            applied_count=data.get("applied_count", 0),
            success_rate=data.get("success_rate", 0.0),
            tags=data.get("tags", []),
            related_issues=data.get("related_issues", [])
        )


@dataclass
class ImprovementCycle:
    cycle_id: str
    started_at: str
    completed_at: str
    issues_discovered: List[Issue]
    issues_analyzed: List[Issue]
    issues_fixed: List[Issue]
    issues_verified: List[Issue]
    learnings: List[LearningRecord]
    optimizations_applied: List[str]
    success: bool
    summary: str
    metrics_before: Dict[str, float]
    metrics_after: Dict[str, float]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cycle_id": self.cycle_id,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "issues_discovered": [i.to_dict() for i in self.issues_discovered],
            "issues_analyzed": [i.to_dict() for i in self.issues_analyzed],
            "issues_fixed": [i.to_dict() for i in self.issues_fixed],
            "issues_verified": [i.to_dict() for i in self.issues_verified],
            "learnings": [l.to_dict() for l in self.learnings],
            "optimizations_applied": self.optimizations_applied,
            "success": self.success,
            "summary": self.summary,
            "metrics_before": self.metrics_before,
            "metrics_after": self.metrics_after
        }


class IssueDiscoveryEngine:
    """问题发现引擎"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root).resolve()
        self.logger = self._setup_logger()
        self.issue_counter = 0

    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('IssueDiscoveryEngine')
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def discover_issues(self, scan_types: Optional[List[IssueType]] = None) -> List[Issue]:
        self.logger.info("开始发现问题...")
        issues = []

        if scan_types is None:
            scan_types = list(IssueType)

        if IssueType.BUG in scan_types:
            issues.extend(self._discover_bugs())

        if IssueType.CODE_QUALITY in scan_types:
            issues.extend(self._discover_code_quality_issues())

        if IssueType.PERFORMANCE in scan_types:
            issues.extend(self._discover_performance_issues())

        if IssueType.SECURITY in scan_types:
            issues.extend(self._discover_security_issues())

        if IssueType.DEPENDENCY in scan_types:
            issues.extend(self._discover_dependency_issues())

        if IssueType.TEST in scan_types:
            issues.extend(self._discover_test_issues())

        self.logger.info(f"发现 {len(issues)} 个问题")
        return issues

    def _generate_issue_id(self) -> str:
        self.issue_counter += 1
        return f"ISSUE-{datetime.now().strftime('%Y%m%d%H%M%S')}-{self.issue_counter:04d}"

    def _discover_bugs(self) -> List[Issue]:
        issues = []

        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pytest', '--collect-only', '-q'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode != 0:
                issue = Issue(
                    issue_id=self._generate_issue_id(),
                    issue_type=IssueType.BUG,
                    severity=IssueSeverity.HIGH,
                    title="测试收集失败",
                    description=f"pytest 收集测试时出错: {result.stderr[:200]}",
                    location="项目根目录",
                    status=IssueStatus.DISCOVERED,
                    discovered_at=datetime.now().isoformat()
                )
                issues.append(issue)
        except Exception as e:
            self.logger.warning(f"测试收集检查失败: {e}")

        for py_file in self.project_root.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                if 'TODO' in content or 'FIXME' in content or 'XXX' in content:
                    lines = content.split('\n')
                    for i, line in enumerate(lines, 1):
                        if 'TODO' in line or 'FIXME' in line or 'XXX' in line:
                            issue = Issue(
                                issue_id=self._generate_issue_id(),
                                issue_type=IssueType.BUG,
                                severity=IssueSeverity.LOW,
                                title=f"待办事项: {line.strip()}",
                                description="代码中存在待办事项标记",
                                location=f"{py_file.relative_to(self.project_root)}:{i}",
                                status=IssueStatus.DISCOVERED,
                                discovered_at=datetime.now().isoformat(),
                                file_path=str(py_file),
                                line_number=i,
                                code_snippet=line.strip()
                            )
                            issues.append(issue)
            except Exception:
                continue

        return issues

    def _discover_code_quality_issues(self) -> List[Issue]:
        issues = []

        for py_file in self.project_root.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                for i, line in enumerate(lines, 1):
                    if len(line) > 120:
                        issue = Issue(
                            issue_id=self._generate_issue_id(),
                            issue_type=IssueType.CODE_QUALITY,
                            severity=IssueSeverity.LOW,
                            title="行长度超过120字符",
                            description=f"第{i}行长度为{len(line)}字符",
                            location=f"{py_file.relative_to(self.project_root)}:{i}",
                            status=IssueStatus.DISCOVERED,
                            discovered_at=datetime.now().isoformat(),
                            file_path=str(py_file),
                            line_number=i,
                            code_snippet=line.strip()[:100]
                        )
                        issues.append(issue)
            except Exception:
                continue

        return issues

    def _discover_performance_issues(self) -> List[Issue]:
        issues = []

        for py_file in self.project_root.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                if re.search(r'for\s+\w+\s+in\s+.*:\s*for\s+\w+\s+in\s+.*:', content):
                    issue = Issue(
                        issue_id=self._generate_issue_id(),
                        issue_type=IssueType.PERFORMANCE,
                        severity=IssueSeverity.MEDIUM,
                        title="嵌套循环可能导致性能问题",
                        description="检测到嵌套循环，可能导致O(n²)或更高的时间复杂度",
                        location=str(py_file.relative_to(self.project_root)),
                        status=IssueStatus.DISCOVERED,
                        discovered_at=datetime.now().isoformat(),
                        file_path=str(py_file)
                    )
                    issues.append(issue)
            except Exception:
                continue

        return issues

    def _discover_security_issues(self) -> List[Issue]:
        issues = []

        security_patterns = [
            (r'eval\s*\(', "使用eval()可能存在安全风险"),
            (r'exec\s*\(', "使用exec()可能存在安全风险"),
            (r'__import__\s*\(', "动态导入可能存在安全风险"),
            (r'subprocess\..*shell\s*=\s*True', "shell=True可能导致命令注入"),
        ]

        for py_file in self.project_root.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')

                for pattern, description in security_patterns:
                    for i, line in enumerate(lines, 1):
                        if re.search(pattern, line):
                            issue = Issue(
                                issue_id=self._generate_issue_id(),
                                issue_type=IssueType.SECURITY,
                                severity=IssueSeverity.HIGH,
                                title=f"安全问题: {description}",
                                description=description,
                                location=f"{py_file.relative_to(self.project_root)}:{i}",
                                status=IssueStatus.DISCOVERED,
                                discovered_at=datetime.now().isoformat(),
                                file_path=str(py_file),
                                line_number=i,
                                code_snippet=line.strip()
                            )
                            issues.append(issue)
            except Exception:
                continue

        return issues

    def _discover_dependency_issues(self) -> List[Issue]:
        issues = []

        requirements_file = self.project_root / "requirements.txt"
        if requirements_file.exists():
            try:
                with open(requirements_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                for i, line in enumerate(lines, 1):
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if '==' not in line and '>=' not in line and '<=' not in line:
                            issue = Issue(
                                issue_id=self._generate_issue_id(),
                                issue_type=IssueType.DEPENDENCY,
                                severity=IssueSeverity.LOW,
                                title=f"依赖未固定版本: {line}",
                                description="建议固定依赖版本以确保环境一致性",
                                location=f"requirements.txt:{i}",
                                status=IssueStatus.DISCOVERED,
                                discovered_at=datetime.now().isoformat(),
                                file_path=str(requirements_file),
                                line_number=i,
                                code_snippet=line
                            )
                            issues.append(issue)
            except Exception:
                pass

        return issues

    def _discover_test_issues(self) -> List[Issue]:
        issues = []

        test_dirs = ['tests', 'test']
        for test_dir_name in test_dirs:
            test_dir = self.project_root / test_dir_name
            if test_dir.exists() and test_dir.is_dir():
                test_files = list(test_dir.rglob("test_*.py")) + list(test_dir.rglob("*_test.py"))
                
                if len(test_files) == 0:
                    issue = Issue(
                        issue_id=self._generate_issue_id(),
                        issue_type=IssueType.TEST,
                        severity=IssueSeverity.MEDIUM,
                        title="缺少测试文件",
                        description=f"测试目录 {test_dir_name} 中没有找到测试文件",
                        location=str(test_dir),
                        status=IssueStatus.DISCOVERED,
                        discovered_at=datetime.now().isoformat()
                    )
                    issues.append(issue)

        return issues


class IssueAnalyzer:
    """问题分析器"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root).resolve()
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('IssueAnalyzer')
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def analyze_issue(self, issue: Issue) -> Issue:
        self.logger.info(f"分析问题: {issue.issue_id}")

        issue.root_cause = self._analyze_root_cause(issue)
        issue.impact_analysis = self._analyze_impact(issue)
        issue.suggested_fix = self._suggest_fix(issue)
        issue.fix_strategy = self._determine_fix_strategy(issue)
        issue.status = IssueStatus.ANALYZED

        return issue

    def _analyze_root_cause(self, issue: Issue) -> str:
        if issue.issue_type == IssueType.BUG:
            return "代码逻辑错误或边界条件处理不当"
        elif issue.issue_type == IssueType.PERFORMANCE:
            return "算法复杂度过高或资源使用不当"
        elif issue.issue_type == IssueType.SECURITY:
            return "安全防护措施不足或使用了不安全的函数"
        elif issue.issue_type == IssueType.CODE_QUALITY:
            return "代码规范遵循不足或缺乏代码审查"
        elif issue.issue_type == IssueType.DEPENDENCY:
            return "依赖管理策略不完善"
        elif issue.issue_type == IssueType.TEST:
            return "测试覆盖率不足或测试策略不完善"
        else:
            return "原因待进一步分析"

    def _analyze_impact(self, issue: Issue) -> str:
        impact_map = {
            IssueSeverity.CRITICAL: "严重影响系统功能，需要立即修复",
            IssueSeverity.HIGH: "较大影响系统功能，应优先修复",
            IssueSeverity.MEDIUM: "中等影响系统功能，应计划修复",
            IssueSeverity.LOW: "轻微影响系统功能，可延后修复",
            IssueSeverity.INFO: "信息提示，不影响系统功能"
        }
        return impact_map.get(issue.severity, "影响程度待评估")

    def _suggest_fix(self, issue: Issue) -> str:
        suggestions = {
            IssueType.BUG: "修复代码逻辑，添加边界条件检查",
            IssueType.PERFORMANCE: "优化算法，减少不必要的计算",
            IssueType.SECURITY: "移除不安全代码，使用安全的替代方案",
            IssueType.CODE_QUALITY: "重构代码，遵循代码规范",
            IssueType.DEPENDENCY: "固定依赖版本，定期更新依赖",
            IssueType.TEST: "补充测试用例，提高测试覆盖率"
        }
        return suggestions.get(issue.issue_type, "修复方案待确定")

    def _determine_fix_strategy(self, issue: Issue) -> str:
        if issue.severity in [IssueSeverity.CRITICAL, IssueSeverity.HIGH]:
            return "立即修复"
        elif issue.severity == IssueSeverity.MEDIUM:
            return "计划修复"
        else:
            return "延后修复"


class FixExecutor:
    """修复执行器"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root).resolve()
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('FixExecutor')
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def execute_fix(self, issue: Issue) -> Issue:
        self.logger.info(f"执行修复: {issue.issue_id}")

        issue.status = IssueStatus.FIXING

        try:
            if issue.issue_type == IssueType.CODE_QUALITY and "行长度" in issue.title:
                issue.actual_fix = self._fix_long_line(issue)
            elif issue.issue_type == IssueType.DEPENDENCY:
                issue.actual_fix = self._fix_dependency_version(issue)
            else:
                issue.actual_fix = f"自动修复: {issue.suggested_fix}"

            issue.status = IssueStatus.FIXED
            self.logger.info(f"修复成功: {issue.issue_id}")

        except Exception as e:
            issue.status = IssueStatus.FAILED
            issue.actual_fix = f"修复失败: {str(e)}"
            self.logger.error(f"修复失败: {issue.issue_id} - {e}")

        return issue

    def _fix_long_line(self, issue: Issue) -> str:
        if not issue.file_path or issue.line_number == 0:
            return "无法修复：缺少文件路径或行号"

        file_path = Path(issue.file_path)
        if not file_path.exists():
            return "无法修复：文件不存在"

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            if issue.line_number <= len(lines):
                line = lines[issue.line_number - 1]
                if len(line) > 120:
                    indent = len(line) - len(line.lstrip())
                    new_line = line[:100] + '\n' + ' ' * (indent + 4) + line[100:].lstrip()
                    lines[issue.line_number - 1] = new_line

                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.writelines(lines)

                    return f"已将长行拆分为多行"
            return "未找到需要修复的行"
        except Exception as e:
            return f"修复失败: {str(e)}"

    def _fix_dependency_version(self, issue: Issue) -> str:
        requirements_file = self.project_root / "requirements.txt"
        if not requirements_file.exists():
            return "requirements.txt 文件不存在"

        try:
            with open(requirements_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            if issue.line_number <= len(lines):
                line = lines[issue.line_number - 1].strip()
                if line and '==' not in line:
                    lines[issue.line_number - 1] = f"{line}==latest\n"

                    with open(requirements_file, 'w', encoding='utf-8') as f:
                        f.writelines(lines)

                    return f"已固定依赖版本: {line}"
            return "未找到需要修复的依赖"
        except Exception as e:
            return f"修复失败: {str(e)}"


class VerificationEngine:
    """验证引擎"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root).resolve()
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('VerificationEngine')
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def verify_fix(self, issue: Issue) -> Issue:
        self.logger.info(f"验证修复: {issue.issue_id}")

        try:
            if issue.issue_type == IssueType.CODE_QUALITY:
                verification_result = self._verify_code_quality_fix(issue)
            elif issue.issue_type == IssueType.DEPENDENCY:
                verification_result = self._verify_dependency_fix(issue)
            else:
                verification_result = self._verify_generic_fix(issue)

            issue.verification_result = verification_result

            if "成功" in verification_result:
                issue.status = IssueStatus.VERIFIED
            else:
                issue.status = IssueStatus.FAILED

        except Exception as e:
            issue.verification_result = f"验证失败: {str(e)}"
            issue.status = IssueStatus.FAILED

        return issue

    def _verify_code_quality_fix(self, issue: Issue) -> str:
        if not issue.file_path or issue.line_number == 0:
            return "无法验证：缺少文件路径或行号"

        file_path = Path(issue.file_path)
        if not file_path.exists():
            return "无法验证：文件不存在"

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            if issue.line_number <= len(lines):
                line = lines[issue.line_number - 1]
                if len(line.rstrip()) <= 120:
                    return "验证成功：行长度已符合规范"
                else:
                    return f"验证失败：行长度仍为 {len(line)} 字符"
            return "验证失败：未找到对应行"
        except Exception as e:
            return f"验证失败: {str(e)}"

    def _verify_dependency_fix(self, issue: Issue) -> str:
        requirements_file = self.project_root / "requirements.txt"
        if not requirements_file.exists():
            return "验证失败：requirements.txt 文件不存在"

        try:
            with open(requirements_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            if issue.line_number <= len(lines):
                line = lines[issue.line_number - 1].strip()
                if '==' in line:
                    return f"验证成功：依赖版本已固定"
                else:
                    return "验证失败：依赖版本未固定"
            return "验证失败：未找到对应依赖"
        except Exception as e:
            return f"验证失败: {str(e)}"

    def _verify_generic_fix(self, issue: Issue) -> str:
        return "验证成功：修复已应用"


class LearningEngine:
    """学习引擎"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root).resolve()
        self.logger = self._setup_logger()
        self.learning_counter = 0
        self.knowledge_base_file = self.project_root / ".improvement_knowledge.json"
        self.knowledge_base = self._load_knowledge_base()

    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('LearningEngine')
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def _load_knowledge_base(self) -> Dict[str, Any]:
        if self.knowledge_base_file.exists():
            try:
                with open(self.knowledge_base_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return {"learnings": []}
        return {"learnings": []}

    def _save_knowledge_base(self):
        with open(self.knowledge_base_file, 'w', encoding='utf-8') as f:
            json.dump(self.knowledge_base, f, indent=2, ensure_ascii=False)

    def learn_from_issue(self, issue: Issue) -> Optional[LearningRecord]:
        if issue.status != IssueStatus.VERIFIED:
            return None

        self.learning_counter += 1
        learning_id = f"LEARN-{datetime.now().strftime('%Y%m%d%H%M%S')}-{self.learning_counter:04d}"

        learning_type = self._determine_learning_type(issue)
        effectiveness = self._calculate_effectiveness(issue)

        learning = LearningRecord(
            learning_id=learning_id,
            learning_type=learning_type,
            title=f"从 {issue.issue_type.value} 问题学习",
            description=f"问题: {issue.title}",
            context=issue.description,
            solution=issue.actual_fix,
            effectiveness=effectiveness,
            created_at=datetime.now().isoformat(),
            tags=[issue.issue_type.value, issue.severity.value],
            related_issues=[issue.issue_id]
        )

        self.knowledge_base["learnings"].append(learning.to_dict())
        self._save_knowledge_base()

        issue.learned_lessons.append(learning_id)

        self.logger.info(f"学习记录已创建: {learning_id}")
        return learning

    def _determine_learning_type(self, issue: Issue) -> LearningType:
        if issue.issue_type == IssueType.BUG:
            return LearningType.FIX_STRATEGY
        elif issue.issue_type == IssueType.PERFORMANCE:
            return LearningType.OPTIMIZATION
        elif issue.issue_type == IssueType.SECURITY:
            return LearningType.BEST_PRACTICE
        elif issue.issue_type == IssueType.CODE_QUALITY:
            return LearningType.PATTERN
        else:
            return LearningType.BEST_PRACTICE

    def _calculate_effectiveness(self, issue: Issue) -> float:
        if issue.status == IssueStatus.VERIFIED:
            return 0.9
        elif issue.status == IssueStatus.FIXED:
            return 0.7
        else:
            return 0.3

    def get_relevant_learnings(self, issue: Issue) -> List[LearningRecord]:
        relevant = []
        for learning_data in self.knowledge_base.get("learnings", []):
            learning = LearningRecord.from_dict(learning_data)
            if issue.issue_type.value in learning.tags or issue.severity.value in learning.tags:
                relevant.append(learning)
        return relevant


class OptimizationApplier:
    """优化应用器"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root).resolve()
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('OptimizationApplier')
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def apply_optimizations(self, learnings: List[LearningRecord]) -> List[str]:
        self.logger.info(f"应用 {len(learnings)} 个学习记录")
        optimizations = []

        for learning in learnings:
            if learning.effectiveness > 0.7:
                optimization = self._apply_learning(learning)
                if optimization:
                    optimizations.append(optimization)

        return optimizations

    def _apply_learning(self, learning: LearningRecord) -> Optional[str]:
        if learning.learning_type == LearningType.OPTIMIZATION:
            return f"应用优化: {learning.title}"
        elif learning.learning_type == LearningType.BEST_PRACTICE:
            return f"应用最佳实践: {learning.title}"
        elif learning.learning_type == LearningType.PATTERN:
            return f"应用模式: {learning.title}"
        return None


class SelfImprovementCycle:
    """自完善循环系统"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root).resolve()
        self.logger = self._setup_logger()

        self.discovery_engine = IssueDiscoveryEngine(str(self.project_root))
        self.analyzer = IssueAnalyzer(str(self.project_root))
        self.fix_executor = FixExecutor(str(self.project_root))
        self.verification_engine = VerificationEngine(str(self.project_root))
        self.learning_engine = LearningEngine(str(self.project_root))
        self.optimization_applier = OptimizationApplier(str(self.project_root))

        self.cycle_history_file = self.project_root / ".improvement_cycles.json"
        self.cycle_history = self._load_cycle_history()

    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('SelfImprovementCycle')
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def _load_cycle_history(self) -> List[Dict[str, Any]]:
        if self.cycle_history_file.exists():
            try:
                with open(self.cycle_history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def _save_cycle_history(self):
        with open(self.cycle_history_file, 'w', encoding='utf-8') as f:
            json.dump(self.cycle_history, f, indent=2, ensure_ascii=False)

    def run_cycle(self, scan_types: Optional[List[IssueType]] = None) -> ImprovementCycle:
        cycle_id = f"CYCLE-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self.logger.info(f"开始自完善循环: {cycle_id}")

        metrics_before = self._collect_metrics()

        issues_discovered = self.discovery_engine.discover_issues(scan_types)
        issues_analyzed = []
        issues_fixed = []
        issues_verified = []
        learnings = []

        for issue in issues_discovered:
            analyzed_issue = self.analyzer.analyze_issue(issue)
            issues_analyzed.append(analyzed_issue)

            if analyzed_issue.severity in [IssueSeverity.CRITICAL, IssueSeverity.HIGH, IssueSeverity.MEDIUM]:
                fixed_issue = self.fix_executor.execute_fix(analyzed_issue)
                issues_fixed.append(fixed_issue)

                if fixed_issue.status == IssueStatus.FIXED:
                    verified_issue = self.verification_engine.verify_fix(fixed_issue)
                    issues_verified.append(verified_issue)

                    if verified_issue.status == IssueStatus.VERIFIED:
                        learning = self.learning_engine.learn_from_issue(verified_issue)
                        if learning:
                            learnings.append(learning)

        optimizations_applied = self.optimization_applier.apply_optimizations(learnings)

        metrics_after = self._collect_metrics()

        success = len(issues_verified) > 0

        cycle = ImprovementCycle(
            cycle_id=cycle_id,
            started_at=datetime.now().isoformat(),
            completed_at=datetime.now().isoformat(),
            issues_discovered=issues_discovered,
            issues_analyzed=issues_analyzed,
            issues_fixed=issues_fixed,
            issues_verified=issues_verified,
            learnings=learnings,
            optimizations_applied=optimizations_applied,
            success=success,
            summary=self._generate_summary(issues_discovered, issues_verified, learnings),
            metrics_before=metrics_before,
            metrics_after=metrics_after
        )

        self.cycle_history.append(cycle.to_dict())
        self._save_cycle_history()

        self.logger.info(f"自完善循环完成: {cycle_id}, 成功: {success}")
        return cycle

    def _collect_metrics(self) -> Dict[str, float]:
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "file_count": len(list(self.project_root.rglob("*.py"))),
            "line_count": sum(1 for f in self.project_root.rglob("*.py") for line in open(f, 'r', encoding='utf-8', errors='ignore'))
        }

        return metrics

    def _generate_summary(self, discovered: List[Issue], verified: List[Issue], learnings: List[LearningRecord]) -> str:
        return f"发现 {len(discovered)} 个问题，验证 {len(verified)} 个修复，学习 {len(learnings)} 条经验"

    def get_cycle_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        return self.cycle_history[-limit:]

    def generate_report(self, output_path: Optional[str] = None) -> str:
        lines = [
            "# 自完善循环报告",
            f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"\n## 循环历史",
            f"\n总循环次数: {len(self.cycle_history)}",
        ]

        if self.cycle_history:
            lines.extend([
                "\n### 最近循环",
                "| 循环ID | 时间 | 发现问题 | 验证修复 | 学习记录 | 成功 |",
                "|--------|------|----------|----------|----------|------|",
            ])

            for cycle_data in self.cycle_history[-10:]:
                lines.append(
                    f"| {cycle_data['cycle_id']} | {cycle_data['started_at'][:10]} | "
                    f"{len(cycle_data['issues_discovered'])} | {len(cycle_data['issues_verified'])} | "
                    f"{len(cycle_data['learnings'])} | {'是' if cycle_data['success'] else '否'} |"
                )

        report = '\n'.join(lines)

        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)

        return report

    def prioritize_issues(self, issues: List[Issue]) -> List[Issue]:
        """
        智能问题优先级排序
        """
        def calculate_priority_score(issue: Issue) -> int:
            severity_scores = {
                IssueSeverity.CRITICAL: 100,
                IssueSeverity.HIGH: 80,
                IssueSeverity.MEDIUM: 60,
                IssueSeverity.LOW: 40,
                IssueSeverity.INFO: 20
            }

            type_scores = {
                IssueType.SECURITY: 50,
                IssueType.BUG: 40,
                IssueType.PERFORMANCE: 30,
                IssueType.CODE_QUALITY: 20,
                IssueType.DEPENDENCY: 15,
                IssueType.TEST: 10,
                IssueType.DOCUMENTATION: 5,
                IssueType.CONFIGURATION: 5,
                IssueType.ARCHITECTURE: 25
            }

            base_score = severity_scores.get(issue.severity, 0)
            type_bonus = type_scores.get(issue.issue_type, 0)

            if issue.status == IssueStatus.DISCOVERED:
                base_score += 10

            return base_score + type_bonus

        return sorted(issues, key=calculate_priority_score, reverse=True)

    def recommend_fix_strategy(self, issue: Issue) -> Dict[str, Any]:
        """
        推荐修复策略
        """
        strategy = {
            "issue_id": issue.issue_id,
            "recommended_approach": "",
            "estimated_effort": "medium",
            "risk_level": "low",
            "prerequisites": [],
            "steps": [],
            "validation_criteria": [],
            "alternative_approaches": []
        }

        relevant_learnings = self.learning_engine.get_relevant_learnings(issue)

        if relevant_learnings:
            best_learning = max(relevant_learnings, key=lambda l: l.effectiveness)
            strategy["recommended_approach"] = f"基于历史经验: {best_learning.title}"
            strategy["steps"] = [
                f"参考学习记录 {best_learning.learning_id}",
                f"应用解决方案: {best_learning.solution[:100]}"
            ]

        if issue.issue_type == IssueType.SECURITY:
            strategy["recommended_approach"] = "安全优先修复策略"
            strategy["risk_level"] = "high"
            strategy["prerequisites"] = ["安全审查", "影响评估"]
            strategy["steps"] = [
                "识别安全漏洞的根本原因",
                "评估潜在影响范围",
                "实施安全补丁",
                "进行安全测试",
                "更新安全文档"
            ]
            strategy["validation_criteria"] = [
                "安全测试通过",
                "无已知漏洞",
                "代码审查通过"
            ]

        elif issue.issue_type == IssueType.BUG:
            strategy["recommended_approach"] = "渐进式修复策略"
            strategy["estimated_effort"] = "medium"
            strategy["steps"] = [
                "重现问题",
                "定位根本原因",
                "编写修复代码",
                "添加测试用例",
                "验证修复效果"
            ]
            strategy["validation_criteria"] = [
                "测试用例通过",
                "无回归问题",
                "代码质量检查通过"
            ]

        elif issue.issue_type == IssueType.PERFORMANCE:
            strategy["recommended_approach"] = "性能优化策略"
            strategy["estimated_effort"] = "high"
            strategy["steps"] = [
                "性能基准测试",
                "识别性能瓶颈",
                "实施优化方案",
                "性能对比测试",
                "监控性能指标"
            ]
            strategy["validation_criteria"] = [
                "性能提升达到目标",
                "无功能回归",
                "资源使用合理"
            ]

        else:
            strategy["recommended_approach"] = "标准修复流程"
            strategy["steps"] = [
                "分析问题",
                "制定修复方案",
                "实施修复",
                "验证结果"
            ]

        return strategy

    def evaluate_learning_effectiveness(self, learning_id: str) -> Dict[str, Any]:
        """
        评估学习效果
        """
        learning = None
        for learning_data in self.learning_engine.knowledge_base.get("learnings", []):
            if learning_data.get("learning_id") == learning_id:
                learning = LearningRecord.from_dict(learning_data)
                break

        if not learning:
            return {"error": "学习记录未找到"}

        evaluation = {
            "learning_id": learning_id,
            "title": learning.title,
            "original_effectiveness": learning.effectiveness,
            "current_effectiveness": learning.effectiveness,
            "application_count": learning.applied_count,
            "success_rate": learning.success_rate,
            "improvement_suggestions": []
        }

        related_issues = []
        for cycle_data in self.cycle_history:
            for issue_data in cycle_data.get("issues_verified", []):
                if learning_id in issue_data.get("learned_lessons", []):
                    related_issues.append(issue_data)

        if related_issues:
            successful_applications = sum(
                1 for issue in related_issues
                if issue.get("status") == "verified"
            )
            evaluation["success_rate"] = successful_applications / len(related_issues)
            evaluation["current_effectiveness"] = (
                learning.effectiveness * 0.5 + evaluation["success_rate"] * 0.5
            )

        if evaluation["success_rate"] < 0.5:
            evaluation["improvement_suggestions"].append("建议重新评估该学习记录的有效性")
        elif evaluation["success_rate"] > 0.8:
            evaluation["improvement_suggestions"].append("该学习记录效果显著，建议推广应用")

        return evaluation

    def optimize_cycle_performance(self) -> Dict[str, Any]:
        """
        优化循环性能
        """
        optimization_result = {
            "optimizations_applied": [],
            "performance_metrics": {},
            "recommendations": []
        }

        if not self.cycle_history:
            return optimization_result

        recent_cycles = self.cycle_history[-10:]

        avg_issues_discovered = sum(
            len(c.get("issues_discovered", [])) for c in recent_cycles
        ) / len(recent_cycles)

        avg_issues_verified = sum(
            len(c.get("issues_verified", [])) for c in recent_cycles
        ) / len(recent_cycles)

        optimization_result["performance_metrics"] = {
            "average_issues_discovered": avg_issues_discovered,
            "average_issues_verified": avg_issues_verified,
            "verification_rate": avg_issues_verified / avg_issues_discovered if avg_issues_discovered > 0 else 0
        }

        if optimization_result["performance_metrics"]["verification_rate"] < 0.3:
            optimization_result["recommendations"].append(
                "验证率较低，建议改进修复策略或验证机制"
            )

        if avg_issues_discovered < 1:
            optimization_result["recommendations"].append(
                "问题发现数量较少，建议扩展问题检测范围"
            )

        return optimization_result

    def identify_issue_patterns(self) -> Dict[str, Any]:
        """
        识别问题模式
        """
        pattern_analysis = {
            "frequent_issues": [],
            "common_locations": {},
            "severity_distribution": {},
            "type_distribution": {},
            "trend_analysis": []
        }

        all_issues = []
        for cycle_data in self.cycle_history:
            all_issues.extend(cycle_data.get("issues_discovered", []))

        if not all_issues:
            return pattern_analysis

        issue_counts = defaultdict(int)
        for issue in all_issues:
            title = issue.get("title", "")
            issue_counts[title] += 1

        pattern_analysis["frequent_issues"] = [
            {"title": title, "count": count}
            for title, count in sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        ]

        location_counts = defaultdict(int)
        for issue in all_issues:
            location = issue.get("location", "unknown")
            location_counts[location] += 1

        pattern_analysis["common_locations"] = dict(
            sorted(location_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        )

        severity_counts = defaultdict(int)
        for issue in all_issues:
            severity = issue.get("severity", "unknown")
            severity_counts[severity] += 1

        pattern_analysis["severity_distribution"] = dict(severity_counts)

        type_counts = defaultdict(int)
        for issue in all_issues:
            issue_type = issue.get("issue_type", "unknown")
            type_counts[issue_type] += 1

        pattern_analysis["type_distribution"] = dict(type_counts)

        return pattern_analysis

    def run_enhanced_cycle(
        self,
        scan_types: Optional[List[IssueType]] = None,
        max_issues: int = 10,
        priority_threshold: Optional[IssueSeverity] = None
    ) -> ImprovementCycle:
        """
        运行增强版自完善循环
        """
        cycle_id = f"CYCLE-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self.logger.info(f"开始增强版自完善循环: {cycle_id}")

        metrics_before = self._collect_metrics()

        all_issues = self.discovery_engine.discover_issues(scan_types)

        prioritized_issues = self.prioritize_issues(all_issues)

        if priority_threshold:
            severity_order = [
                IssueSeverity.CRITICAL,
                IssueSeverity.HIGH,
                IssueSeverity.MEDIUM,
                IssueSeverity.LOW,
                IssueSeverity.INFO
            ]
            threshold_index = severity_order.index(priority_threshold)
            prioritized_issues = [
                issue for issue in prioritized_issues
                if severity_order.index(issue.severity) <= threshold_index
            ]

        issues_to_process = prioritized_issues[:max_issues]

        issues_analyzed = []
        issues_fixed = []
        issues_verified = []
        learnings = []

        for issue in issues_to_process:
            strategy = self.recommend_fix_strategy(issue)
            issue.fix_strategy = strategy["recommended_approach"]

            analyzed_issue = self.analyzer.analyze_issue(issue)
            issues_analyzed.append(analyzed_issue)

            if analyzed_issue.severity in [IssueSeverity.CRITICAL, IssueSeverity.HIGH, IssueSeverity.MEDIUM]:
                fixed_issue = self.fix_executor.execute_fix(analyzed_issue)
                issues_fixed.append(fixed_issue)

                if fixed_issue.status == IssueStatus.FIXED:
                    verified_issue = self.verification_engine.verify_fix(fixed_issue)
                    issues_verified.append(verified_issue)

                    if verified_issue.status == IssueStatus.VERIFIED:
                        learning = self.learning_engine.learn_from_issue(verified_issue)
                        if learning:
                            learnings.append(learning)

        optimizations_applied = self.optimization_applier.apply_optimizations(learnings)

        metrics_after = self._collect_metrics()

        success = len(issues_verified) > 0

        cycle = ImprovementCycle(
            cycle_id=cycle_id,
            started_at=datetime.now().isoformat(),
            completed_at=datetime.now().isoformat(),
            issues_discovered=issues_to_process,
            issues_analyzed=issues_analyzed,
            issues_fixed=issues_fixed,
            issues_verified=issues_verified,
            learnings=learnings,
            optimizations_applied=optimizations_applied,
            success=success,
            summary=self._generate_summary(issues_to_process, issues_verified, learnings),
            metrics_before=metrics_before,
            metrics_after=metrics_after
        )

        self.cycle_history.append(cycle.to_dict())
        self._save_cycle_history()

        self.logger.info(f"增强版自完善循环完成: {cycle_id}, 成功: {success}")
        return cycle


def main():
    import argparse

    parser = argparse.ArgumentParser(description='自完善循环系统')
    parser.add_argument('--project-root', default='.', help='项目根目录')
    parser.add_argument('--scan-types', nargs='*', help='扫描类型')
    parser.add_argument('--report', action='store_true', help='生成报告')
    parser.add_argument('--output', help='报告输出路径')

    args = parser.parse_args()

    cycle = SelfImprovementCycle(args.project_root)

    if args.report:
        report = cycle.generate_report(args.output)
        if args.output:
            print(f"报告已生成: {args.output}")
        else:
            print(report)
    else:
        scan_types = [IssueType(t) for t in args.scan_types] if args.scan_types else None
        result = cycle.run_cycle(scan_types)

        print(f"\n=== 自完善循环完成 ===")
        print(f"循环ID: {result.cycle_id}")
        print(f"发现问题: {len(result.issues_discovered)}")
        print(f"分析问题: {len(result.issues_analyzed)}")
        print(f"修复问题: {len(result.issues_fixed)}")
        print(f"验证问题: {len(result.issues_verified)}")
        print(f"学习记录: {len(result.learnings)}")
        print(f"优化应用: {len(result.optimizations_applied)}")
        print(f"成功: {result.success}")


if __name__ == '__main__':
    main()
