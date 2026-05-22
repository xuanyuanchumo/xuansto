#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复验证器 - Fix Validator

修复效果验证系统，包括：
- 修复前后对比（代码差异、性能差异、测试结果差异）
- 修复效果评分（基于问题解决程度、代码质量提升等）
- 修复副作用检测（是否引入新问题、是否影响其他功能）
- 验证报告生成

验证维度：
- 问题解决度：原始问题是否完全解决
- 代码质量：修复后代码质量是否提升
- 测试通过率：修复后测试是否通过
- 性能影响：修复是否影响性能
- 副作用检测：是否引入新问题

使用示例:
    python fix_validator.py --before <before_state> --after <after_state>
    python fix_validator.py --fix-id <fix_id> --validate
    python fix_validator.py --file <file_path> --compare
"""

import ast
import difflib
import json
import logging
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union


class ValidationDimension(Enum):
    """验证维度"""
    PROBLEM_RESOLUTION = "problem_resolution"
    CODE_QUALITY = "code_quality"
    TEST_PASS_RATE = "test_pass_rate"
    PERFORMANCE_IMPACT = "performance_impact"
    SIDE_EFFECT = "side_effect"


class ValidationStatus(Enum):
    """验证状态"""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"


class SeverityLevel(Enum):
    """严重程度"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class CodeDifference:
    """代码差异"""
    file_path: str
    added_lines: int
    removed_lines: int
    modified_lines: int
    diff_content: str
    changed_functions: List[str] = field(default_factory=list)
    changed_classes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "added_lines": self.added_lines,
            "removed_lines": self.removed_lines,
            "modified_lines": self.modified_lines,
            "diff_content": self.diff_content[:2000] if len(self.diff_content) > 2000 else self.diff_content,
            "changed_functions": self.changed_functions,
            "changed_classes": self.changed_classes
        }


@dataclass
class PerformanceDifference:
    """性能差异"""
    metric_name: str
    before_value: float
    after_value: float
    change_percent: float
    improvement: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "before_value": round(self.before_value, 4),
            "after_value": round(self.after_value, 4),
            "change_percent": round(self.change_percent, 2),
            "improvement": self.improvement
        }


@dataclass
class TestResultDifference:
    """测试结果差异"""
    before_passed: int
    before_failed: int
    before_total: int
    after_passed: int
    after_failed: int
    after_total: int
    new_failures: List[str] = field(default_factory=list)
    new_passes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "before_passed": self.before_passed,
            "before_failed": self.before_failed,
            "before_total": self.before_total,
            "after_passed": self.after_passed,
            "after_failed": self.after_failed,
            "after_total": self.after_total,
            "new_failures": self.new_failures,
            "new_passes": self.new_passes
        }


@dataclass
class SideEffect:
    """副作用"""
    effect_type: str
    severity: SeverityLevel
    description: str
    affected_area: str
    recommendation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "effect_type": self.effect_type,
            "severity": self.severity.value,
            "description": self.description,
            "affected_area": self.affected_area,
            "recommendation": self.recommendation
        }


@dataclass
class DimensionScore:
    """维度评分"""
    dimension: ValidationDimension
    score: float
    max_score: float
    status: ValidationStatus
    details: Dict[str, Any] = field(default_factory=dict)
    issues: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dimension": self.dimension.value,
            "score": round(self.score, 2),
            "max_score": self.max_score,
            "percentage": round(self.score / self.max_score * 100, 2) if self.max_score > 0 else 0,
            "status": self.status.value,
            "details": self.details,
            "issues": self.issues
        }


@dataclass
class ValidationReport:
    """验证报告"""
    report_id: str
    fix_id: str
    timestamp: str
    overall_score: float
    overall_status: ValidationStatus
    dimension_scores: List[DimensionScore]
    code_differences: List[CodeDifference]
    performance_differences: List[PerformanceDifference]
    test_difference: Optional[TestResultDifference]
    side_effects: List[SideEffect]
    summary: str
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "fix_id": self.fix_id,
            "timestamp": self.timestamp,
            "overall_score": round(self.overall_score, 2),
            "overall_status": self.overall_status.value,
            "dimension_scores": [s.to_dict() for s in self.dimension_scores],
            "code_differences": [d.to_dict() for d in self.code_differences],
            "performance_differences": [p.to_dict() for p in self.performance_differences],
            "test_difference": self.test_difference.to_dict() if self.test_difference else None,
            "side_effects": [s.to_dict() for s in self.side_effects],
            "summary": self.summary,
            "recommendations": self.recommendations
        }


class CodeAnalyzer:
    """代码分析器"""

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)

    def analyze_code_quality(self, content: str, file_path: str) -> Dict[str, Any]:
        """分析代码质量"""
        result = {
            "complexity": 0,
            "lines_of_code": 0,
            "function_count": 0,
            "class_count": 0,
            "import_count": 0,
            "comment_ratio": 0.0,
            "issues": []
        }

        try:
            lines = content.split('\n')
            result["lines_of_code"] = len([l for l in lines if l.strip() and not l.strip().startswith('#')])

            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    result["function_count"] += 1
                    complexity = self._calculate_complexity(node)
                    if complexity > 10:
                        result["issues"].append(f"函数 {node.name} 复杂度过高: {complexity}")
                elif isinstance(node, ast.ClassDef):
                    result["class_count"] += 1
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    result["import_count"] += 1

            comment_lines = len([l for l in lines if l.strip().startswith('#')])
            if result["lines_of_code"] > 0:
                result["comment_ratio"] = comment_lines / result["lines_of_code"]

        except SyntaxError as e:
            result["issues"].append(f"语法错误: {e}")

        return result

    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """计算圈复杂度"""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        return complexity

    def extract_structure(self, content: str) -> Dict[str, List[str]]:
        """提取代码结构"""
        structure = {
            "functions": [],
            "classes": [],
            "imports": [],
            "variables": []
        }

        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    structure["functions"].append(node.name)
                elif isinstance(node, ast.ClassDef):
                    structure["classes"].append(node.name)
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        structure["imports"].append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for alias in node.names:
                        structure["imports"].append(f"{module}.{alias.name}")
        except SyntaxError:
            pass

        return structure

    def compare_code(self, before: str, after: str, file_path: str) -> CodeDifference:
        """比较代码差异"""
        before_lines = before.splitlines(keepends=True)
        after_lines = after.splitlines(keepends=True)

        diff = difflib.unified_diff(
            before_lines,
            after_lines,
            fromfile=f"{file_path} (before)",
            tofile=f"{file_path} (after)"
        )
        diff_content = ''.join(diff)

        added = 0
        removed = 0
        modified = 0

        for line in diff_content.split('\n'):
            if line.startswith('+') and not line.startswith('+++'):
                added += 1
            elif line.startswith('-') and not line.startswith('---'):
                removed += 1

        modified = min(added, removed)

        before_structure = self.extract_structure(before)
        after_structure = self.extract_structure(after)

        changed_functions = list(
            set(before_structure["functions"]) ^ set(after_structure["functions"])
        )
        changed_classes = list(
            set(before_structure["classes"]) ^ set(after_structure["classes"])
        )

        return CodeDifference(
            file_path=file_path,
            added_lines=added,
            removed_lines=removed,
            modified_lines=modified,
            diff_content=diff_content,
            changed_functions=changed_functions,
            changed_classes=changed_classes
        )


class PerformanceAnalyzer:
    """性能分析器"""

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self._metrics: Dict[str, List[float]] = {}

    def measure_execution_time(self, func: Callable, *args, **kwargs) -> Tuple[Any, float]:
        """测量执行时间"""
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        return result, end_time - start_time

    def analyze_performance_impact(self, before_metrics: Dict[str, float],
                                   after_metrics: Dict[str, float]) -> List[PerformanceDifference]:
        """分析性能影响"""
        differences = []

        all_metrics = set(before_metrics.keys()) | set(after_metrics.keys())

        for metric in all_metrics:
            before_val = before_metrics.get(metric, 0.0)
            after_val = after_metrics.get(metric, 0.0)

            if before_val > 0:
                change_percent = ((after_val - before_val) / before_val) * 100
            else:
                change_percent = 100.0 if after_val > 0 else 0.0

            improvement = change_percent <= 0

            differences.append(PerformanceDifference(
                metric_name=metric,
                before_value=before_val,
                after_value=after_val,
                change_percent=change_percent,
                improvement=improvement
            ))

        return differences

    def get_memory_usage(self) -> float:
        """获取内存使用"""
        try:
            import psutil
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            return 0.0


class TestRunner:
    """测试运行器"""

    def __init__(self, project_root: Path, logger: Optional[logging.Logger] = None):
        self.project_root = project_root
        self.logger = logger or logging.getLogger(__name__)

    def run_tests(self, test_path: Optional[str] = None) -> Dict[str, Any]:
        """运行测试"""
        result = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": 0,
            "duration": 0.0,
            "failures": []
        }

        cmd = [sys.executable, "-m", "pytest", "-v", "--tb=short", "-q"]

        if test_path:
            cmd.append(test_path)

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
                cwd=str(self.project_root)
            )

            output = proc.stdout + proc.stderr

            passed_match = re.search(r'(\d+) passed', output)
            failed_match = re.search(r'(\d+) failed', output)
            skipped_match = re.search(r'(\d+) skipped', output)
            error_match = re.search(r'(\d+) error', output)

            if passed_match:
                result["passed"] = int(passed_match.group(1))
            if failed_match:
                result["failed"] = int(failed_match.group(1))
            if skipped_match:
                result["skipped"] = int(skipped_match.group(1))
            if error_match:
                result["errors"] = int(error_match.group(1))

            result["total"] = result["passed"] + result["failed"] + result["skipped"] + result["errors"]

            for match in re.finditer(r'FAILED (.*?) ', output):
                result["failures"].append(match.group(1).strip())

        except subprocess.TimeoutExpired:
            self.logger.error("测试运行超时")
            result["errors"] = 1
        except Exception as e:
            self.logger.error(f"运行测试失败: {e}")
            result["errors"] = 1

        return result

    def compare_test_results(self, before: Dict[str, Any],
                            after: Dict[str, Any]) -> TestResultDifference:
        """比较测试结果差异"""
        before_failures = set(before.get("failures", []))
        after_failures = set(after.get("failures", []))

        new_failures = list(after_failures - before_failures)
        new_passes = list(before_failures - after_failures)

        return TestResultDifference(
            before_passed=before.get("passed", 0),
            before_failed=before.get("failed", 0),
            before_total=before.get("total", 0),
            after_passed=after.get("passed", 0),
            after_failed=after.get("failed", 0),
            after_total=after.get("total", 0),
            new_failures=new_failures,
            new_passes=new_passes
        )


class SideEffectDetector:
    """副作用检测器"""

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)

    def detect_side_effects(self, before_code: str, after_code: str,
                           before_structure: Dict[str, Any],
                           after_structure: Dict[str, Any]) -> List[SideEffect]:
        """检测副作用"""
        side_effects = []

        side_effects.extend(self._check_removed_functions(before_structure, after_structure))
        side_effects.extend(self._check_removed_classes(before_structure, after_structure))
        side_effects.extend(self._check_import_changes(before_structure, after_structure))
        side_effects.extend(self._check_api_changes(before_code, after_code))
        side_effects.extend(self._check_syntax_issues(after_code))

        return side_effects

    def _check_removed_functions(self, before: Dict[str, Any],
                                 after: Dict[str, Any]) -> List[SideEffect]:
        """检查移除的函数"""
        effects = []
        before_funcs = set(before.get("functions", []))
        after_funcs = set(after.get("functions", []))
        removed = before_funcs - after_funcs

        for func in removed:
            effects.append(SideEffect(
                effect_type="removed_function",
                severity=SeverityLevel.HIGH,
                description=f"函数 '{func}' 已被移除",
                affected_area="API",
                recommendation="检查是否有其他代码依赖此函数"
            ))

        return effects

    def _check_removed_classes(self, before: Dict[str, Any],
                               after: Dict[str, Any]) -> List[SideEffect]:
        """检查移除的类"""
        effects = []
        before_classes = set(before.get("classes", []))
        after_classes = set(after.get("classes", []))
        removed = before_classes - after_classes

        for cls in removed:
            effects.append(SideEffect(
                effect_type="removed_class",
                severity=SeverityLevel.HIGH,
                description=f"类 '{cls}' 已被移除",
                affected_area="API",
                recommendation="检查是否有其他代码依赖此类"
            ))

        return effects

    def _check_import_changes(self, before: Dict[str, Any],
                              after: Dict[str, Any]) -> List[SideEffect]:
        """检查导入变化"""
        effects = []
        before_imports = set(before.get("imports", []))
        after_imports = set(after.get("imports", []))
        removed = before_imports - after_imports

        for imp in removed:
            effects.append(SideEffect(
                effect_type="removed_import",
                severity=SeverityLevel.MEDIUM,
                description=f"导入 '{imp}' 已被移除",
                affected_area="Dependencies",
                recommendation="确认是否仍需要此依赖"
            ))

        return effects

    def _check_api_changes(self, before: str, after: str) -> List[SideEffect]:
        """检查API变化"""
        effects = []

        before_public = self._extract_public_api(before)
        after_public = self._extract_public_api(after)

        removed_public = before_public - after_public
        for api in removed_public:
            effects.append(SideEffect(
                effect_type="removed_public_api",
                severity=SeverityLevel.HIGH,
                description=f"公共API '{api}' 已被移除或修改",
                affected_area="Public API",
                recommendation="此更改可能影响外部调用者"
            ))

        return effects

    def _check_syntax_issues(self, code: str) -> List[SideEffect]:
        """检查语法问题"""
        effects = []

        try:
            ast.parse(code)
        except SyntaxError as e:
            effects.append(SideEffect(
                effect_type="syntax_error",
                severity=SeverityLevel.CRITICAL,
                description=f"语法错误: {e.msg} (行 {e.lineno})",
                affected_area="Syntax",
                recommendation="修复语法错误"
            ))

        return effects

    def _extract_public_api(self, code: str) -> Set[str]:
        """提取公共API"""
        public_api = set()

        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if not node.name.startswith('_'):
                        public_api.add(node.name)
                elif isinstance(node, ast.ClassDef):
                    if not node.name.startswith('_'):
                        public_api.add(node.name)
                        for item in node.body:
                            if isinstance(item, ast.FunctionDef):
                                if not item.name.startswith('_'):
                                    public_api.add(f"{node.name}.{item.name}")
        except SyntaxError:
            pass

        return public_api


class FixValidator:
    """修复验证器"""

    def __init__(self, project_root: Optional[Path] = None,
                 logger: Optional[logging.Logger] = None):
        self.project_root = project_root or Path.cwd()
        self.logger = logger or logging.getLogger(__name__)
        self.code_analyzer = CodeAnalyzer(logger)
        self.performance_analyzer = PerformanceAnalyzer(logger)
        self.test_runner = TestRunner(self.project_root, logger)
        self.side_effect_detector = SideEffectDetector(logger)

    def validate_fix(self, fix_id: str,
                    before_state: Dict[str, Any],
                    after_state: Dict[str, Any],
                    original_issues: List[Dict[str, Any]]) -> ValidationReport:
        """验证修复"""
        self.logger.info(f"开始验证修复: {fix_id}")

        dimension_scores = []
        code_differences = []
        performance_differences = []
        test_difference = None
        side_effects = []

        dimension_scores.append(self._validate_problem_resolution(
            original_issues, after_state
        ))

        code_diff = self._validate_code_quality(before_state, after_state)
        dimension_scores.append(code_diff["score"])
        code_differences = code_diff["differences"]

        test_result = self._validate_tests(before_state, after_state)
        dimension_scores.append(test_result["score"])
        test_difference = test_result["difference"]

        perf_result = self._validate_performance(before_state, after_state)
        dimension_scores.append(perf_result["score"])
        performance_differences = perf_result["differences"]

        side_effect_result = self._validate_side_effects(before_state, after_state)
        dimension_scores.append(side_effect_result["score"])
        side_effects = side_effect_result["effects"]

        overall_score = sum(s.score for s in dimension_scores)
        overall_status = self._determine_overall_status(dimension_scores)
        summary = self._generate_summary(dimension_scores, side_effects)
        recommendations = self._generate_recommendations(dimension_scores, side_effects)

        return ValidationReport(
            report_id=f"validation-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            fix_id=fix_id,
            timestamp=datetime.now().isoformat(),
            overall_score=overall_score,
            overall_status=overall_status,
            dimension_scores=dimension_scores,
            code_differences=code_differences,
            performance_differences=performance_differences,
            test_difference=test_difference,
            side_effects=side_effects,
            summary=summary,
            recommendations=recommendations
        )

    def _validate_problem_resolution(self, original_issues: List[Dict[str, Any]],
                                     after_state: Dict[str, Any]) -> DimensionScore:
        """验证问题解决度"""
        total_issues = len(original_issues)
        if total_issues == 0:
            return DimensionScore(
                dimension=ValidationDimension.PROBLEM_RESOLUTION,
                score=20.0,
                max_score=20.0,
                status=ValidationStatus.PASSED,
                details={"message": "没有原始问题需要验证"}
            )

        resolved_count = 0
        remaining_issues = []

        after_issues = after_state.get("issues", [])

        for issue in original_issues:
            issue_id = issue.get("id", "")
            issue_type = issue.get("type", "")
            issue_location = issue.get("location", "")

            is_resolved = True
            for after_issue in after_issues:
                if (after_issue.get("type") == issue_type and
                    after_issue.get("location") == issue_location):
                    is_resolved = False
                    remaining_issues.append(issue)
                    break

            if is_resolved:
                resolved_count += 1

        resolution_rate = resolved_count / total_issues
        score = resolution_rate * 20.0

        if resolution_rate >= 1.0:
            status = ValidationStatus.PASSED
        elif resolution_rate >= 0.7:
            status = ValidationStatus.WARNING
        else:
            status = ValidationStatus.FAILED

        return DimensionScore(
            dimension=ValidationDimension.PROBLEM_RESOLUTION,
            score=score,
            max_score=20.0,
            status=status,
            details={
                "total_issues": total_issues,
                "resolved_issues": resolved_count,
                "resolution_rate": round(resolution_rate * 100, 2)
            },
            issues=[f"未解决问题: {i.get('type', 'unknown')}" for i in remaining_issues[:5]]
        )

    def _validate_code_quality(self, before_state: Dict[str, Any],
                               after_state: Dict[str, Any]) -> Dict[str, Any]:
        """验证代码质量"""
        before_quality = before_state.get("code_quality", {})
        after_quality = after_state.get("code_quality", {})

        differences = []

        before_files = before_state.get("files", {})
        after_files = after_state.get("files", {})

        for file_path, after_content in after_files.items():
            before_content = before_files.get(file_path, "")
            if before_content:
                diff = self.code_analyzer.compare_code(
                    before_content, after_content, file_path
                )
                differences.append(diff)

        before_complexity = before_quality.get("avg_complexity", 0)
        after_complexity = after_quality.get("avg_complexity", 0)

        complexity_improved = after_complexity <= before_complexity

        before_issues = before_quality.get("issue_count", 0)
        after_issues = after_quality.get("issue_count", 0)

        issues_reduced = after_issues <= before_issues

        score = 20.0
        issues = []

        if not complexity_improved:
            score -= 5
            issues.append(f"代码复杂度增加: {before_complexity} -> {after_complexity}")

        if not issues_reduced:
            score -= 5
            issues.append(f"代码问题数量增加: {before_issues} -> {after_issues}")

        status = ValidationStatus.PASSED if score >= 15 else (
            ValidationStatus.WARNING if score >= 10 else ValidationStatus.FAILED
        )

        return {
            "score": DimensionScore(
                dimension=ValidationDimension.CODE_QUALITY,
                score=max(0, score),
                max_score=20.0,
                status=status,
                details={
                    "complexity_before": before_complexity,
                    "complexity_after": after_complexity,
                    "issues_before": before_issues,
                    "issues_after": after_issues
                },
                issues=issues
            ),
            "differences": differences
        }

    def _validate_tests(self, before_state: Dict[str, Any],
                       after_state: Dict[str, Any]) -> Dict[str, Any]:
        """验证测试通过率"""
        before_tests = before_state.get("test_results", {})
        after_tests = after_state.get("test_results", {})

        difference = None
        if before_tests and after_tests:
            difference = self.test_runner.compare_test_results(before_tests, after_tests)

        before_pass_rate = 0.0
        if before_tests.get("total", 0) > 0:
            before_pass_rate = before_tests.get("passed", 0) / before_tests.get("total", 1)

        after_pass_rate = 0.0
        if after_tests.get("total", 0) > 0:
            after_pass_rate = after_tests.get("passed", 0) / after_tests.get("total", 1)

        score = after_pass_rate * 20.0
        issues = []

        if difference and difference.new_failures:
            issues.append(f"新增失败测试: {len(difference.new_failures)}")
            score -= len(difference.new_failures) * 2

        if after_pass_rate >= 1.0:
            status = ValidationStatus.PASSED
        elif after_pass_rate >= 0.8:
            status = ValidationStatus.WARNING
        else:
            status = ValidationStatus.FAILED

        return {
            "score": DimensionScore(
                dimension=ValidationDimension.TEST_PASS_RATE,
                score=max(0, score),
                max_score=20.0,
                status=status,
                details={
                    "before_pass_rate": round(before_pass_rate * 100, 2),
                    "after_pass_rate": round(after_pass_rate * 100, 2)
                },
                issues=issues
            ),
            "difference": difference
        }

    def _validate_performance(self, before_state: Dict[str, Any],
                             after_state: Dict[str, Any]) -> Dict[str, Any]:
        """验证性能影响"""
        before_metrics = before_state.get("performance_metrics", {})
        after_metrics = after_state.get("performance_metrics", {})

        differences = []
        if before_metrics and after_metrics:
            differences = self.performance_analyzer.analyze_performance_impact(
                before_metrics, after_metrics
            )

        score = 20.0
        issues = []

        for diff in differences:
            if not diff.improvement:
                if diff.change_percent > 20:
                    score -= 5
                    issues.append(f"性能下降: {diff.metric_name} 下降 {abs(diff.change_percent):.2f}%")
                elif diff.change_percent > 10:
                    score -= 2
                    issues.append(f"性能轻微下降: {diff.metric_name}")

        status = ValidationStatus.PASSED if score >= 15 else (
            ValidationStatus.WARNING if score >= 10 else ValidationStatus.FAILED
        )

        return {
            "score": DimensionScore(
                dimension=ValidationDimension.PERFORMANCE_IMPACT,
                score=max(0, score),
                max_score=20.0,
                status=status,
                details={
                    "metrics_compared": len(differences),
                    "degraded_metrics": len([d for d in differences if not d.improvement])
                },
                issues=issues
            ),
            "differences": differences
        }

    def _validate_side_effects(self, before_state: Dict[str, Any],
                               after_state: Dict[str, Any]) -> Dict[str, Any]:
        """验证副作用"""
        before_files = before_state.get("files", {})
        after_files = after_state.get("files", {})

        all_effects = []

        for file_path, after_content in after_files.items():
            before_content = before_files.get(file_path, "")
            if before_content:
                before_structure = self.code_analyzer.extract_structure(before_content)
                after_structure = self.code_analyzer.extract_structure(after_content)

                effects = self.side_effect_detector.detect_side_effects(
                    before_content, after_content,
                    before_structure, after_structure
                )
                all_effects.extend(effects)

        critical_count = sum(1 for e in all_effects if e.severity == SeverityLevel.CRITICAL)
        high_count = sum(1 for e in all_effects if e.severity == SeverityLevel.HIGH)
        medium_count = sum(1 for e in all_effects if e.severity == SeverityLevel.MEDIUM)

        score = 20.0
        score -= critical_count * 10
        score -= high_count * 5
        score -= medium_count * 2

        if critical_count > 0:
            status = ValidationStatus.FAILED
        elif high_count > 0:
            status = ValidationStatus.WARNING
        else:
            status = ValidationStatus.PASSED

        return {
            "score": DimensionScore(
                dimension=ValidationDimension.SIDE_EFFECT,
                score=max(0, score),
                max_score=20.0,
                status=status,
                details={
                    "critical_effects": critical_count,
                    "high_effects": high_count,
                    "medium_effects": medium_count,
                    "total_effects": len(all_effects)
                },
                issues=[e.description for e in all_effects[:5]]
            ),
            "effects": all_effects
        }

    def _determine_overall_status(self, scores: List[DimensionScore]) -> ValidationStatus:
        """确定总体状态"""
        has_failed = any(s.status == ValidationStatus.FAILED for s in scores)
        has_warning = any(s.status == ValidationStatus.WARNING for s in scores)

        if has_failed:
            return ValidationStatus.FAILED
        elif has_warning:
            return ValidationStatus.WARNING
        else:
            return ValidationStatus.PASSED

    def _generate_summary(self, scores: List[DimensionScore],
                         side_effects: List[SideEffect]) -> str:
        """生成摘要"""
        total_score = sum(s.score for s in scores)
        max_score = sum(s.max_score for s in scores)
        percentage = (total_score / max_score * 100) if max_score > 0 else 0

        summary_parts = [
            f"验证总分: {total_score:.1f}/{max_score} ({percentage:.1f}%)"
        ]

        for score in scores:
            summary_parts.append(
                f"- {score.dimension.value}: {score.score:.1f}/{score.max_score}"
            )

        if side_effects:
            summary_parts.append(f"检测到 {len(side_effects)} 个副作用")

        return "\n".join(summary_parts)

    def _generate_recommendations(self, scores: List[DimensionScore],
                                  side_effects: List[SideEffect]) -> List[str]:
        """生成建议"""
        recommendations = []

        for score in scores:
            if score.status == ValidationStatus.FAILED:
                if score.dimension == ValidationDimension.PROBLEM_RESOLUTION:
                    recommendations.append("建议重新检查未解决的问题，确保修复完整")
                elif score.dimension == ValidationDimension.CODE_QUALITY:
                    recommendations.append("建议进行代码审查，提升代码质量")
                elif score.dimension == ValidationDimension.TEST_PASS_RATE:
                    recommendations.append("建议修复失败的测试用例")
                elif score.dimension == ValidationDimension.PERFORMANCE_IMPACT:
                    recommendations.append("建议优化性能下降的部分")
                elif score.dimension == ValidationDimension.SIDE_EFFECT:
                    recommendations.append("建议处理检测到的副作用")

        for effect in side_effects:
            if effect.severity in [SeverityLevel.CRITICAL, SeverityLevel.HIGH]:
                recommendations.append(effect.recommendation)

        return list(set(recommendations))

    def validate_file_fix(self, file_path: str, before_content: str,
                         after_content: str, original_issues: List[Dict[str, Any]]) -> ValidationReport:
        """验证文件修复"""
        before_state = {
            "files": {file_path: before_content},
            "code_quality": self.code_analyzer.analyze_code_quality(before_content, file_path),
            "issues": original_issues
        }

        after_state = {
            "files": {file_path: after_content},
            "code_quality": self.code_analyzer.analyze_code_quality(after_content, file_path),
            "issues": []
        }

        return self.validate_fix(
            fix_id=f"file-{Path(file_path).stem}",
            before_state=before_state,
            after_state=after_state,
            original_issues=original_issues
        )

    def print_report(self, report: ValidationReport):
        """打印报告"""
        print("\n" + "=" * 80)
        print("修复验证报告")
        print("=" * 80)
        print(f"报告ID: {report.report_id}")
        print(f"修复ID: {report.fix_id}")
        print(f"验证时间: {report.timestamp}")

        status_icons = {
            ValidationStatus.PASSED: "✅",
            ValidationStatus.FAILED: "❌",
            ValidationStatus.WARNING: "⚠️",
            ValidationStatus.SKIPPED: "⏭️"
        }

        icon = status_icons.get(report.overall_status, "❓")
        print(f"总体状态: {icon} {report.overall_status.value.upper()}")
        print(f"总分: {report.overall_score:.1f}/100")

        print("\n" + "-" * 80)
        print("维度评分")
        print("-" * 80)

        for score in report.dimension_scores:
            icon = status_icons.get(score.status, "❓")
            pct = score.score / score.max_score * 100 if score.max_score > 0 else 0
            print(f"\n{icon} [{score.dimension.value}]")
            print(f"   得分: {score.score:.1f}/{score.max_score} ({pct:.1f}%)")
            print(f"   状态: {score.status.value}")

            if score.issues:
                print("   问题:")
                for issue in score.issues[:3]:
                    print(f"     - {issue}")

        if report.side_effects:
            print("\n" + "-" * 80)
            print("副作用检测")
            print("-" * 80)
            for effect in report.side_effects:
                severity_icons = {
                    SeverityLevel.CRITICAL: "🔴",
                    SeverityLevel.HIGH: "🟠",
                    SeverityLevel.MEDIUM: "🟡",
                    SeverityLevel.LOW: "🟢",
                    SeverityLevel.INFO: "ℹ️"
                }
                icon = severity_icons.get(effect.severity, "❓")
                print(f"\n{icon} [{effect.severity.value}] {effect.effect_type}")
                print(f"   描述: {effect.description}")
                print(f"   影响区域: {effect.affected_area}")
                print(f"   建议: {effect.recommendation}")

        print("\n" + "-" * 80)
        print("摘要")
        print("-" * 80)
        print(report.summary)

        if report.recommendations:
            print("\n建议:")
            for rec in report.recommendations:
                print(f"  • {rec}")

    def save_report(self, report: ValidationReport, output_path: Optional[Path] = None) -> Path:
        """保存报告"""
        if output_path is None:
            output_dir = get_path_config().REPORTS_DIR / "fix_validation"
            output_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = output_dir / f"validation_{report.fix_id}_{timestamp}.json"

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)

        self.logger.info(f"报告已保存: {output_path}")
        return output_path


def setup_logger(verbose: bool = False) -> logging.Logger:
    """配置日志记录器"""
    logger = logging.getLogger("FixValidator")
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
    import argparse

    parser = argparse.ArgumentParser(
        description="修复验证器",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--fix-id",
        type=str,
        default="",
        help="修复ID"
    )

    parser.add_argument(
        "--before",
        type=str,
        help="修复前状态文件"
    )

    parser.add_argument(
        "--after",
        type=str,
        help="修复后状态文件"
    )

    parser.add_argument(
        "--file",
        type=str,
        help="要验证的文件路径"
    )

    parser.add_argument(
        "--output",
        type=str,
        help="报告输出路径"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="启用详细日志"
    )

    args = parser.parse_args()

    logger = setup_logger(args.verbose)
    validator = FixValidator(logger=logger)

    if args.before and args.after:
        with open(args.before, 'r', encoding='utf-8') as f:
            before_state = json.load(f)
        with open(args.after, 'r', encoding='utf-8') as f:
            after_state = json.load(f)

        original_issues = before_state.get("issues", [])

        report = validator.validate_fix(
            fix_id=args.fix_id or "unknown",
            before_state=before_state,
            after_state=after_state,
            original_issues=original_issues
        )
    else:
        print("请提供 --before 和 --after 参数")
        return 1

    validator.print_report(report)

    output_path = Path(args.output) if args.output else None
    saved_path = validator.save_report(report, output_path)
    print(f"\n报告已保存到: {saved_path}")

    return 0 if report.overall_status == ValidationStatus.PASSED else 1


if __name__ == "__main__":
    sys.exit(main())
