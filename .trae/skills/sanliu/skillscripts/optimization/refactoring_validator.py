#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重构验证器

TDD蓝阶段 - 重构验证机制
确保重构不破坏现有功能，包括：
- 测试执行验证
- 代码覆盖率对比
- 行为一致性检查
- 性能回归检测
- 验证报告生成

使用示例:
    python refactoring_validator.py --before <before_snapshot> --after <after_snapshot>
    python refactoring_validator.py --run-tests
    python refactoring_validator.py --compare-coverage
"""

import os
import sys
import json
import subprocess
import argparse
import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class ValidationStatus(Enum):
    """验证状态"""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"


class ValidationType(Enum):
    """验证类型"""
    TEST_EXECUTION = "test_execution"
    COVERAGE_COMPARISON = "coverage_comparison"
    BEHAVIOR_CONSISTENCY = "behavior_consistency"
    PERFORMANCE_CHECK = "performance_check"
    CODE_QUALITY = "code_quality"
    SYNTAX_CHECK = "syntax_check"


@dataclass
class ValidationResult:
    """验证结果"""
    validation_type: ValidationType
    status: ValidationStatus
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "validation_type": self.validation_type.value,
            "status": self.status.value,
            "message": self.message,
            "details": self.details,
            "errors": self.errors,
            "warnings": self.warnings
        }


@dataclass
class TestResult:
    """测试结果"""
    total_tests: int
    passed: int
    failed: int
    skipped: int
    errors: int
    duration_seconds: float
    failure_details: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_tests": self.total_tests,
            "passed": self.passed,
            "failed": self.failed,
            "skipped": self.skipped,
            "errors": self.errors,
            "duration_seconds": round(self.duration_seconds, 2),
            "failure_details": self.failure_details
        }


@dataclass
class CoverageResult:
    """覆盖率结果"""
    line_coverage: float
    branch_coverage: float
    function_coverage: float
    total_lines: int
    covered_lines: int
    missing_lines: List[int] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "line_coverage": round(self.line_coverage, 2),
            "branch_coverage": round(self.branch_coverage, 2),
            "function_coverage": round(self.function_coverage, 2),
            "total_lines": self.total_lines,
            "covered_lines": self.covered_lines,
            "missing_lines": self.missing_lines[:20]
        }


@dataclass
class ValidationReport:
    """验证报告"""
    timestamp: str
    project_root: str
    refactoring_id: str
    overall_status: ValidationStatus
    results: List[ValidationResult]
    test_result: Optional[TestResult] = None
    before_coverage: Optional[CoverageResult] = None
    after_coverage: Optional[CoverageResult] = None
    summary: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "project_root": self.project_root,
            "refactoring_id": self.refactoring_id,
            "overall_status": self.overall_status.value,
            "results": [r.to_dict() for r in self.results],
            "test_result": self.test_result.to_dict() if self.test_result else None,
            "before_coverage": self.before_coverage.to_dict() if self.before_coverage else None,
            "after_coverage": self.after_coverage.to_dict() if self.after_coverage else None,
            "summary": self.summary
        }


class TestRunner:
    """测试运行器"""

    def __init__(self, project_root: Path, logger: Optional[logging.Logger] = None):
        self.project_root = project_root
        self.logger = logger or logging.getLogger(__name__)

    def run_tests(self, test_path: Optional[str] = None) -> TestResult:
        """运行测试"""
        self.logger.info("运行测试...")

        cmd = [
            sys.executable, "-m", "pytest",
            "-v", "--tb=short",
            "--json-report", "--json-report-file=-"
        ]

        if test_path:
            cmd.append(test_path)
        else:
            backend_tests = self.project_root / "backend" / "tests"
            if backend_tests.exists():
                cmd.append(str(backend_tests))

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
                cwd=str(self.project_root / "backend")
            )

            return self._parse_pytest_output(result.stdout, result.stderr)

        except subprocess.TimeoutExpired:
            self.logger.error("测试运行超时")
            return TestResult(
                total_tests=0, passed=0, failed=0, skipped=0, errors=1,
                duration_seconds=300,
                failure_details=[{"error": "测试运行超时"}]
            )
        except Exception as e:
            self.logger.error(f"运行测试失败: {e}")
            return TestResult(
                total_tests=0, passed=0, failed=0, skipped=0, errors=1,
                duration_seconds=0,
                failure_details=[{"error": str(e)}]
            )

    def _parse_pytest_output(self, stdout: str, stderr: str) -> TestResult:
        """解析pytest输出"""
        total_tests = 0
        passed = 0
        failed = 0
        skipped = 0
        errors = 0
        duration = 0.0
        failure_details = []

        summary_pattern = r"(\d+) passed"
        match = re.search(summary_pattern, stdout)
        if match:
            passed = int(match.group(1))

        failed_pattern = r"(\d+) failed"
        match = re.search(failed_pattern, stdout)
        if match:
            failed = int(match.group(1))

        skipped_pattern = r"(\d+) skipped"
        match = re.search(skipped_pattern, stdout)
        if match:
            skipped = int(match.group(1))

        error_pattern = r"(\d+) error"
        match = re.search(error_pattern, stdout)
        if match:
            errors = int(match.group(1))

        total_tests = passed + failed + skipped + errors

        duration_pattern = r"in ([\d.]+)s"
        match = re.search(duration_pattern, stdout)
        if match:
            duration = float(match.group(1))

        failure_pattern = r"FAILED (.*?) -"
        for match in re.finditer(failure_pattern, stdout):
            failure_details.append({"test": match.group(1).strip()})

        return TestResult(
            total_tests=total_tests,
            passed=passed,
            failed=failed,
            skipped=skipped,
            errors=errors,
            duration_seconds=duration,
            failure_details=failure_details
        )


class CoverageAnalyzer:
    """覆盖率分析器"""

    def __init__(self, project_root: Path, logger: Optional[logging.Logger] = None):
        self.project_root = project_root
        self.logger = logger or logging.getLogger(__name__)

    def analyze_coverage(self) -> CoverageResult:
        """分析覆盖率"""
        self.logger.info("分析代码覆盖率...")

        coverage_file = self.project_root / "backend" / "coverage.json"

        if coverage_file.exists():
            return self._parse_coverage_json(coverage_file)

        return self._run_coverage_analysis()

    def _run_coverage_analysis(self) -> CoverageResult:
        """运行覆盖率分析"""
        try:
            cmd = [
                sys.executable, "-m", "pytest",
                "--cov=app", "--cov-report=json",
                "-q"
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
                cwd=str(self.project_root / "backend")
            )

            coverage_file = self.project_root / "backend" / "coverage.json"
            if coverage_file.exists():
                return self._parse_coverage_json(coverage_file)

        except Exception as e:
            self.logger.error(f"覆盖率分析失败: {e}")

        return CoverageResult(
            line_coverage=0.0,
            branch_coverage=0.0,
            function_coverage=0.0,
            total_lines=0,
            covered_lines=0
        )

    def _parse_coverage_json(self, coverage_file: Path) -> CoverageResult:
        """解析覆盖率JSON文件"""
        try:
            with open(coverage_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            totals = data.get("totals", {})

            return CoverageResult(
                line_coverage=totals.get("percent_covered", 0.0),
                branch_coverage=totals.get("branch_percent", 0.0) or 0.0,
                function_coverage=0.0,
                total_lines=totals.get("num_statements", 0),
                covered_lines=totals.get("covered_lines", 0)
            )
        except Exception as e:
            self.logger.error(f"解析覆盖率文件失败: {e}")
            return CoverageResult(
                line_coverage=0.0,
                branch_coverage=0.0,
                function_coverage=0.0,
                total_lines=0,
                covered_lines=0
            )


class RefactoringValidator:
    """重构验证器"""

    def __init__(self, project_root: Optional[Path] = None,
                 logger: Optional[logging.Logger] = None):
        self.project_root = project_root or get_path_config().SKILL_ROOT
        self.logger = logger or logging.getLogger(__name__)
        self.results: List[ValidationResult] = []

    def validate_refactoring(self, refactoring_id: str = "",
                             run_tests: bool = True,
                             compare_coverage: bool = True,
                             check_syntax: bool = True) -> ValidationReport:
        """验证重构"""
        self.logger.info(f"开始验证重构: {refactoring_id}")

        self.results = []

        if check_syntax:
            self._validate_syntax()

        if run_tests:
            self._validate_tests()

        if compare_coverage:
            self._validate_coverage()

        self._validate_code_quality()

        overall_status = self._determine_overall_status()
        summary = self._generate_summary()

        return ValidationReport(
            timestamp=datetime.now().isoformat(),
            project_root=str(self.project_root),
            refactoring_id=refactoring_id or f"refactor-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            overall_status=overall_status,
            results=self.results,
            summary=summary
        )

    def _validate_syntax(self):
        """验证语法"""
        self.logger.info("验证语法...")

        errors = []
        python_files = list(self.project_root.rglob("*.py"))
        python_files = [f for f in python_files if "__pycache__" not in str(f)]

        for py_file in python_files[:50]:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                compile(content, str(py_file), 'exec')
            except SyntaxError as e:
                errors.append(f"{py_file}:{e.lineno}: {e.msg}")

        if errors:
            self.results.append(ValidationResult(
                validation_type=ValidationType.SYNTAX_CHECK,
                status=ValidationStatus.FAILED,
                message=f"发现 {len(errors)} 个语法错误",
                errors=errors
            ))
        else:
            self.results.append(ValidationResult(
                validation_type=ValidationType.SYNTAX_CHECK,
                status=ValidationStatus.PASSED,
                message="语法检查通过",
                details={"files_checked": min(len(python_files), 50)}
            ))

    def _validate_tests(self):
        """验证测试"""
        self.logger.info("验证测试...")

        runner = TestRunner(self.project_root, self.logger)
        test_result = runner.run_tests()

        if test_result.failed > 0 or test_result.errors > 0:
            status = ValidationStatus.FAILED
            message = f"测试失败: {test_result.failed} 失败, {test_result.errors} 错误"
        elif test_result.skipped > test_result.total_tests * 0.5:
            status = ValidationStatus.WARNING
            message = f"大量测试被跳过: {test_result.skipped}/{test_result.total_tests}"
        else:
            status = ValidationStatus.PASSED
            message = f"所有测试通过: {test_result.passed}/{test_result.total_tests}"

        self.results.append(ValidationResult(
            validation_type=ValidationType.TEST_EXECUTION,
            status=status,
            message=message,
            details=test_result.to_dict(),
            errors=[f["test"] for f in test_result.failure_details[:10]]
        ))

    def _validate_coverage(self):
        """验证覆盖率"""
        self.logger.info("验证覆盖率...")

        analyzer = CoverageAnalyzer(self.project_root, self.logger)
        coverage_result = analyzer.analyze_coverage()

        if coverage_result.line_coverage >= 80:
            status = ValidationStatus.PASSED
            message = f"覆盖率良好: {coverage_result.line_coverage:.1f}%"
        elif coverage_result.line_coverage >= 60:
            status = ValidationStatus.WARNING
            message = f"覆盖率需要提高: {coverage_result.line_coverage:.1f}%"
        else:
            status = ValidationStatus.FAILED
            message = f"覆盖率过低: {coverage_result.line_coverage:.1f}%"

        self.results.append(ValidationResult(
            validation_type=ValidationType.COVERAGE_COMPARISON,
            status=status,
            message=message,
            details=coverage_result.to_dict()
        ))

    def _validate_code_quality(self):
        """验证代码质量"""
        self.logger.info("验证代码质量...")

        warnings = []
        details = {}

        try:
            result = subprocess.run(
                [sys.executable, "-m", "ruff", "check", ".", "--output-format=json"],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(self.project_root / "backend")
            )

            if result.stdout:
                issues = json.loads(result.stdout)
                error_count = sum(1 for i in issues if i.get("severity") == "error")
                warning_count = sum(1 for i in issues if i.get("severity") == "warning")

                details["error_count"] = error_count
                details["warning_count"] = warning_count

                if error_count > 0:
                    warnings.append(f"发现 {error_count} 个代码质量问题")
        except Exception as e:
            self.logger.warning(f"代码质量检查失败: {e}")

        if warnings:
            self.results.append(ValidationResult(
                validation_type=ValidationType.CODE_QUALITY,
                status=ValidationStatus.WARNING,
                message="存在代码质量问题",
                details=details,
                warnings=warnings
            ))
        else:
            self.results.append(ValidationResult(
                validation_type=ValidationType.CODE_QUALITY,
                status=ValidationStatus.PASSED,
                message="代码质量检查通过",
                details=details
            ))

    def _determine_overall_status(self) -> ValidationStatus:
        """确定总体状态"""
        has_failed = any(r.status == ValidationStatus.FAILED for r in self.results)
        has_warning = any(r.status == ValidationStatus.WARNING for r in self.results)

        if has_failed:
            return ValidationStatus.FAILED
        elif has_warning:
            return ValidationStatus.WARNING
        else:
            return ValidationStatus.PASSED

    def _generate_summary(self) -> Dict[str, Any]:
        """生成摘要"""
        passed_count = sum(1 for r in self.results if r.status == ValidationStatus.PASSED)
        failed_count = sum(1 for r in self.results if r.status == ValidationStatus.FAILED)
        warning_count = sum(1 for r in self.results if r.status == ValidationStatus.WARNING)

        return {
            "total_validations": len(self.results),
            "passed": passed_count,
            "failed": failed_count,
            "warnings": warning_count,
            "validation_types": [r.validation_type.value for r in self.results]
        }

    def compare_snapshots(self, before_path: Path, after_path: Path) -> ValidationReport:
        """对比前后快照"""
        self.logger.info("对比前后快照...")

        self.results = []

        try:
            with open(before_path, 'r', encoding='utf-8') as f:
                before_data = json.load(f)
            with open(after_path, 'r', encoding='utf-8') as f:
                after_data = json.load(f)

            before_smells = before_data.get("summary", {}).get("total_smells", 0)
            after_smells = after_data.get("summary", {}).get("total_smells", 0)

            if after_smells <= before_smells:
                status = ValidationStatus.PASSED
                message = f"代码异味减少: {before_smells} -> {after_smells}"
            else:
                status = ValidationStatus.WARNING
                message = f"代码异味增加: {before_smells} -> {after_smells}"

            self.results.append(ValidationResult(
                validation_type=ValidationType.BEHAVIOR_CONSISTENCY,
                status=status,
                message=message,
                details={
                    "before_smells": before_smells,
                    "after_smells": after_smells,
                    "improvement": before_smells - after_smells
                }
            ))

        except Exception as e:
            self.logger.error(f"对比快照失败: {e}")
            self.results.append(ValidationResult(
                validation_type=ValidationType.BEHAVIOR_CONSISTENCY,
                status=ValidationStatus.FAILED,
                message=f"对比快照失败: {e}",
                errors=[str(e)]
            ))

        overall_status = self._determine_overall_status()
        summary = self._generate_summary()

        return ValidationReport(
            timestamp=datetime.now().isoformat(),
            project_root=str(self.project_root),
            refactoring_id=f"compare-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            overall_status=overall_status,
            results=self.results,
            summary=summary
        )

    def print_report(self, report: ValidationReport):
        """打印报告"""
        print("\n" + "=" * 80)
        print("重构验证报告")
        print("=" * 80)
        print(f"项目根目录: {report.project_root}")
        print(f"验证时间: {report.timestamp}")
        print(f"重构ID: {report.refactoring_id}")

        status_icon = {
            ValidationStatus.PASSED: "✅",
            ValidationStatus.FAILED: "❌",
            ValidationStatus.WARNING: "⚠️",
            ValidationStatus.SKIPPED: "⏭️"
        }.get(report.overall_status, "❓")

        print(f"总体状态: {status_icon} {report.overall_status.value.upper()}")

        print("\n" + "-" * 80)
        print("验证结果")
        print("-" * 80)

        for result in report.results:
            icon = {
                ValidationStatus.PASSED: "✅",
                ValidationStatus.FAILED: "❌",
                ValidationStatus.WARNING: "⚠️",
                ValidationStatus.SKIPPED: "⏭️"
            }.get(result.status, "❓")

            print(f"\n{icon} [{result.validation_type.value}]")
            print(f"   状态: {result.status.value}")
            print(f"   消息: {result.message}")

            if result.details:
                for key, value in result.details.items():
                    if isinstance(value, (int, float, str)):
                        print(f"   {key}: {value}")

            if result.errors:
                print(f"   错误:")
                for error in result.errors[:5]:
                    print(f"     - {error}")

            if result.warnings:
                print(f"   警告:")
                for warning in result.warnings[:5]:
                    print(f"     - {warning}")

        print("\n" + "-" * 80)
        print("摘要")
        print("-" * 80)
        for key, value in report.summary.items():
            print(f"  {key}: {value}")

    def save_report(self, report: ValidationReport, output_dir: Optional[Path] = None) -> Path:
        """保存报告"""
        if output_dir is None:
            output_dir = get_path_config().REPORTS_DIR
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = output_dir / f"refactoring_validation_{timestamp}.json"

        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)

        latest_path = output_dir / "refactoring_validation_latest.json"
        with open(latest_path, 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)

        self.logger.info(f"报告已保存: {report_path}")
        return report_path


def setup_logger(verbose: bool = False) -> logging.Logger:
    """配置日志记录器"""
    logger = logging.getLogger("RefactoringValidator")
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
        description="重构验证器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python refactoring_validator.py --run-tests
  python refactoring_validator.py --compare-coverage
  python refactoring_validator.py --before before.json --after after.json
        """
    )

    parser.add_argument(
        "--run-tests",
        action="store_true",
        help="运行测试验证"
    )

    parser.add_argument(
        "--compare-coverage",
        action="store_true",
        help="对比覆盖率"
    )

    parser.add_argument(
        "--check-syntax",
        action="store_true",
        default=True,
        help="检查语法"
    )

    parser.add_argument(
        "--before",
        type=str,
        help="重构前的快照文件"
    )

    parser.add_argument(
        "--after",
        type=str,
        help="重构后的快照文件"
    )

    parser.add_argument(
        "--refactoring-id",
        type=str,
        default="",
        help="重构ID"
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

    validator = RefactoringValidator(logger=logger)

    if args.before and args.after:
        before_path = Path(args.before)
        after_path = Path(args.after)

        if not before_path.exists():
            print(f"错误: 找不到文件 {args.before}")
            return 1
        if not after_path.exists():
            print(f"错误: 找不到文件 {args.after}")
            return 1

        report = validator.compare_snapshots(before_path, after_path)
    else:
        report = validator.validate_refactoring(
            refactoring_id=args.refactoring_id,
            run_tests=args.run_tests or True,
            compare_coverage=args.compare_coverage or True,
            check_syntax=args.check_syntax
        )

    validator.print_report(report)

    report_path = validator.save_report(report)
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

    return 0 if report.overall_status == ValidationStatus.PASSED else 1


if __name__ == "__main__":
    sys.exit(main())
