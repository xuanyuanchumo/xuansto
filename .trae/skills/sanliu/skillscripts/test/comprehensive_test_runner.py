#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
综合测试套件运行器 - Comprehensive Test Suite Runner

整合所有测试类型的统一运行器：
- 单元测试 (Unit Tests)
- 集成测试 (Integration Tests)
- 数据库测试 (Database Tests)
- E2E测试 (End-to-End Tests)
- 性能测试 (Performance Tests)
- 安全测试 (Security Tests)
- 回归测试 (Regression Tests)

使用示例:
    python comprehensive_test_runner.py --all
    python comprehensive_test_runner.py --unit --integration
    python comprehensive_test_runner.py --coverage --report
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestType(Enum):
    UNIT = "unit"
    INTEGRATION = "integration"
    DATABASE = "database"
    E2E = "e2e"
    PERFORMANCE = "performance"
    SECURITY = "security"
    REGRESSION = "regression"


class TestStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class TestResult:
    test_type: TestType
    status: TestStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    errors: int = 0
    coverage_percent: float = 0.0
    output: str = ""
    error_message: str = ""
    artifacts: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "test_type": self.test_type.value,
            "status": self.status.value,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.duration_seconds,
            "passed": self.passed,
            "failed": self.failed,
            "skipped": self.skipped,
            "errors": self.errors,
            "coverage_percent": self.coverage_percent,
            "output": self.output[:1000] if self.output else "",
            "error_message": self.error_message,
            "artifacts": self.artifacts,
            "details": self.details
        }


@dataclass
class TestSuiteResult:
    suite_id: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    total_duration_seconds: float = 0.0
    results: List[TestResult] = field(default_factory=list)
    overall_status: TestStatus = TestStatus.PENDING
    total_passed: int = 0
    total_failed: int = 0
    total_skipped: int = 0
    total_errors: int = 0
    overall_coverage: float = 0.0
    report_path: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "suite_id": self.suite_id,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "total_duration_seconds": self.total_duration_seconds,
            "results": [r.to_dict() for r in self.results],
            "overall_status": self.overall_status.value,
            "total_passed": self.total_passed,
            "total_failed": self.total_failed,
            "total_skipped": self.total_skipped,
            "total_errors": self.total_errors,
            "overall_coverage": self.overall_coverage,
            "report_path": self.report_path
        }


class TestExecutor:
    def __init__(
        self,
        project_root: Path,
        tests_dir: Path,
        reports_dir: Path,
        skillscripts_path: Path
    ):
        self.project_root = project_root
        self.tests_dir = tests_dir
        self.reports_dir = reports_dir
        self.skillscripts_path = skillscripts_path
        self._register_executors()
    
    def _register_executors(self):
        self._executors: Dict[TestType, Callable] = {
            TestType.UNIT: self._execute_unit_tests,
            TestType.INTEGRATION: self._execute_integration_tests,
            TestType.DATABASE: self._execute_database_tests,
            TestType.E2E: self._execute_e2e_tests,
            TestType.PERFORMANCE: self._execute_performance_tests,
            TestType.SECURITY: self._execute_security_tests,
            TestType.REGRESSION: self._execute_regression_tests,
        }
    
    def execute(self, test_type: TestType, dry_run: bool = False) -> TestResult:
        start_time = datetime.now()
        
        executor = self._executors.get(test_type)
        if not executor:
            return TestResult(
                test_type=test_type,
                status=TestStatus.SKIPPED,
                start_time=start_time,
                error_message=f"未找到测试执行器: {test_type.value}"
            )
        
        try:
            if dry_run:
                logger.info(f"[DRY-RUN] 跳过执行: {test_type.value}")
                return TestResult(
                    test_type=test_type,
                    status=TestStatus.SKIPPED,
                    start_time=start_time,
                    output="Dry-run模式，跳过执行"
                )
            
            return executor(start_time)
        except Exception as e:
            logger.error(f"测试执行失败 {test_type.value}: {e}")
            return TestResult(
                test_type=test_type,
                status=TestStatus.ERROR,
                start_time=start_time,
                end_time=datetime.now(),
                error_message=str(e)
            )
    
    def _execute_unit_tests(self, start_time: datetime) -> TestResult:
        logger.info("执行单元测试...")
        
        unit_test_dir = self.tests_dir / "unit"
        if not unit_test_dir.exists():
            unit_test_dir = self.tests_dir
        
        cmd = [
            sys.executable, "-m", "pytest",
            str(unit_test_dir),
            "-v",
            "--tb=short",
            f"--junitxml={self.reports_dir / 'unit_junit.xml'}",
            "--json-report",
            f"--json-report-file={self.reports_dir / 'unit_results.json'}",
        ]
        
        result = self._run_command(cmd)
        
        passed, failed, skipped, errors = self._parse_pytest_output(result["output"])
        coverage = self._get_coverage()
        
        return TestResult(
            test_type=TestType.UNIT,
            status=TestStatus.PASSED if failed == 0 and errors == 0 else TestStatus.FAILED,
            start_time=start_time,
            end_time=datetime.now(),
            passed=passed,
            failed=failed,
            skipped=skipped,
            errors=errors,
            coverage_percent=coverage,
            output=result["output"],
            error_message=result.get("error", ""),
            artifacts=["unit_junit.xml", "unit_results.json"]
        )
    
    def _execute_integration_tests(self, start_time: datetime) -> TestResult:
        logger.info("执行集成测试...")
        
        integration_test_dir = self.tests_dir / "integration"
        
        cmd = [
            sys.executable, "-m", "pytest",
            str(integration_test_dir),
            "-v",
            "--tb=short",
            f"--junitxml={self.reports_dir / 'integration_junit.xml'}",
        ]
        
        result = self._run_command(cmd)
        
        passed, failed, skipped, errors = self._parse_pytest_output(result["output"])
        
        return TestResult(
            test_type=TestType.INTEGRATION,
            status=TestStatus.PASSED if failed == 0 and errors == 0 else TestStatus.FAILED,
            start_time=start_time,
            end_time=datetime.now(),
            passed=passed,
            failed=failed,
            skipped=skipped,
            errors=errors,
            output=result["output"],
            artifacts=["integration_junit.xml"]
        )
    
    def _execute_database_tests(self, start_time: datetime) -> TestResult:
        logger.info("执行数据库测试...")
        
        db_test_dir = self.tests_dir / "database"
        if not db_test_dir.exists():
            db_test_dir = self.tests_dir / "integration" / "database"
        
        cmd = [
            sys.executable, "-m", "pytest",
            str(db_test_dir) if db_test_dir.exists() else str(self.tests_dir),
            "-v", "-k", "database or db",
            "--tb=short",
            f"--junitxml={self.reports_dir / 'database_junit.xml'}",
        ]
        
        result = self._run_command(cmd)
        
        passed, failed, skipped, errors = self._parse_pytest_output(result["output"])
        
        return TestResult(
            test_type=TestType.DATABASE,
            status=TestStatus.PASSED if failed == 0 and errors == 0 else TestStatus.FAILED,
            start_time=start_time,
            end_time=datetime.now(),
            passed=passed,
            failed=failed,
            skipped=skipped,
            errors=errors,
            output=result["output"],
            artifacts=["database_junit.xml"]
        )
    
    def _execute_e2e_tests(self, start_time: datetime) -> TestResult:
        logger.info("执行E2E测试...")
        
        e2e_test_dir = self.tests_dir / "e2e"
        
        cmd = [
            sys.executable, "-m", "pytest",
            str(e2e_test_dir) if e2e_test_dir.exists() else str(self.tests_dir),
            "-v", "-k", "e2e or end_to_end",
            "--tb=short",
            f"--junitxml={self.reports_dir / 'e2e_junit.xml'}",
        ]
        
        result = self._run_command(cmd)
        
        passed, failed, skipped, errors = self._parse_pytest_output(result["output"])
        
        return TestResult(
            test_type=TestType.E2E,
            status=TestStatus.PASSED if failed == 0 and errors == 0 else TestStatus.FAILED,
            start_time=start_time,
            end_time=datetime.now(),
            passed=passed,
            failed=failed,
            skipped=skipped,
            errors=errors,
            output=result["output"],
            artifacts=["e2e_junit.xml"]
        )
    
    def _execute_performance_tests(self, start_time: datetime) -> TestResult:
        logger.info("执行性能测试...")
        
        perf_script = self.skillscripts_path / "test" / "performance_test_enhancer.py"
        
        if perf_script.exists():
            cmd = [sys.executable, str(perf_script), "--report"]
        else:
            perf_test_dir = self.tests_dir / "performance"
            cmd = [
                sys.executable, "-m", "pytest",
                str(perf_test_dir) if perf_test_dir.exists() else str(self.tests_dir),
                "-v", "-k", "performance or perf",
                "--tb=short",
            ]
        
        result = self._run_command(cmd)
        
        passed, failed, skipped, errors = self._parse_pytest_output(result["output"])
        
        details = {}
        if "avg_response_time" in result["output"].lower():
            details["performance_metrics"] = "已收集"
        
        return TestResult(
            test_type=TestType.PERFORMANCE,
            status=TestStatus.PASSED if failed == 0 and errors == 0 else TestStatus.FAILED,
            start_time=start_time,
            end_time=datetime.now(),
            passed=passed,
            failed=failed,
            skipped=skipped,
            errors=errors,
            output=result["output"],
            details=details,
            artifacts=["performance_report.json"]
        )
    
    def _execute_security_tests(self, start_time: datetime) -> TestResult:
        logger.info("执行安全测试...")
        
        security_script = self.skillscripts_path / "test" / "security_scanner.py"
        
        vulnerabilities = []
        
        if security_script.exists():
            cmd = [sys.executable, str(security_script), "--full"]
            result = self._run_command(cmd)
            
            vulnerabilities = self._parse_security_output(result["output"])
        else:
            security_test_dir = self.tests_dir / "security"
            cmd = [
                sys.executable, "-m", "pytest",
                str(security_test_dir) if security_test_dir.exists() else str(self.tests_dir),
                "-v", "-k", "security or vuln",
                "--tb=short",
            ]
            result = self._run_command(cmd)
        
        passed, failed, skipped, errors = self._parse_pytest_output(result["output"])
        
        critical_vulns = len([v for v in vulnerabilities if v.get("severity") == "critical"])
        
        return TestResult(
            test_type=TestType.SECURITY,
            status=TestStatus.PASSED if critical_vulns == 0 and failed == 0 else TestStatus.FAILED,
            start_time=start_time,
            end_time=datetime.now(),
            passed=passed,
            failed=failed,
            skipped=skipped,
            errors=errors,
            output=result["output"],
            details={
                "vulnerabilities_found": len(vulnerabilities),
                "critical": critical_vulns,
                "high": len([v for v in vulnerabilities if v.get("severity") == "high"]),
                "medium": len([v for v in vulnerabilities if v.get("severity") == "medium"]),
            },
            artifacts=["security_report.json"]
        )
    
    def _execute_regression_tests(self, start_time: datetime) -> TestResult:
        logger.info("执行回归测试...")
        
        regression_script = self.skillscripts_path / "test" / "regression_test.py"
        
        if regression_script.exists():
            cmd = [sys.executable, str(regression_script), "--all"]
        else:
            cmd = [
                sys.executable, "-m", "pytest",
                str(self.tests_dir),
                "-v",
                "--tb=short",
                f"--junitxml={self.reports_dir / 'regression_junit.xml'}",
            ]
        
        result = self._run_command(cmd)
        
        passed, failed, skipped, errors = self._parse_pytest_output(result["output"])
        
        return TestResult(
            test_type=TestType.REGRESSION,
            status=TestStatus.PASSED if failed == 0 and errors == 0 else TestStatus.FAILED,
            start_time=start_time,
            end_time=datetime.now(),
            passed=passed,
            failed=failed,
            skipped=skipped,
            errors=errors,
            output=result["output"],
            artifacts=["regression_junit.xml"]
        )
    
    def _run_command(self, cmd: List[str]) -> Dict[str, Any]:
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,
                cwd=str(self.project_root)
            )
            return {
                "success": result.returncode == 0,
                "output": result.stdout + result.stderr,
                "error": result.stderr if result.returncode != 0 else ""
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "output": "", "error": "命令执行超时"}
        except Exception as e:
            return {"success": False, "output": "", "error": str(e)}
    
    def _parse_pytest_output(self, output: str) -> tuple:
        passed = 0
        failed = 0
        skipped = 0
        errors = 0
        
        import re
        
        passed_match = re.search(r"(\d+)\s+passed", output)
        if passed_match:
            passed = int(passed_match.group(1))
        
        failed_match = re.search(r"(\d+)\s+failed", output)
        if failed_match:
            failed = int(failed_match.group(1))
        
        skipped_match = re.search(r"(\d+)\s+skipped", output)
        if skipped_match:
            skipped = int(skipped_match.group(1))
        
        error_match = re.search(r"(\d+)\s+error", output)
        if error_match:
            errors = int(error_match.group(1))
        
        return passed, failed, skipped, errors
    
    def _parse_security_output(self, output: str) -> List[Dict[str, Any]]:
        vulnerabilities = []
        
        return vulnerabilities
    
    def _get_coverage(self) -> float:
        coverage_file = self.reports_dir / "coverage.json"
        if coverage_file.exists():
            try:
                with open(coverage_file, 'r') as f:
                    data = json.load(f)
                    return data.get("totals", {}).get("percent_covered", 0.0)
            except Exception:
                pass
        
        return 0.0


class ComprehensiveTestRunner:
    DEFAULT_TEST_TYPES = [
        TestType.UNIT,
        TestType.INTEGRATION,
        TestType.DATABASE,
        TestType.E2E,
        TestType.PERFORMANCE,
        TestType.SECURITY,
        TestType.REGRESSION,
    ]
    
    def __init__(
        self,
        project_root: str,
        tests_dir: Optional[str] = None,
        reports_dir: Optional[str] = None,
        skillscripts_path: Optional[str] = None
    ):
        self.project_root = Path(project_root)
        self.tests_dir = Path(tests_dir) if tests_dir else self.project_root / "tests"
        self.reports_dir = Path(reports_dir) if reports_dir else self.project_root / "docs" / "reports"
        self.skillscripts_path = Path(skillscripts_path) if skillscripts_path else self.project_root / "skillscripts"
        
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        self.executor = TestExecutor(
            self.project_root,
            self.tests_dir,
            self.reports_dir,
            self.skillscripts_path
        )
        
        self.suite_id = f"SUITE-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    def run(
        self,
        test_types: Optional[List[TestType]] = None,
        dry_run: bool = False,
        stop_on_failure: bool = False
    ) -> TestSuiteResult:
        test_types = test_types or self.DEFAULT_TEST_TYPES
        
        logger.info(f"启动测试套件: {self.suite_id}")
        logger.info(f"测试类型: {[t.value for t in test_types]}")
        
        suite_result = TestSuiteResult(
            suite_id=self.suite_id,
            started_at=datetime.now()
        )
        
        for test_type in test_types:
            logger.info(f"\n{'='*40}")
            logger.info(f"执行测试: {test_type.value}")
            logger.info(f"{'='*40}")
            
            result = self.executor.execute(test_type, dry_run)
            suite_result.results.append(result)
            
            suite_result.total_passed += result.passed
            suite_result.total_failed += result.failed
            suite_result.total_skipped += result.skipped
            suite_result.total_errors += result.errors
            
            if result.status in [TestStatus.FAILED, TestStatus.ERROR]:
                if stop_on_failure:
                    logger.error(f"测试失败，停止执行: {test_type.value}")
                    break
        
        suite_result.completed_at = datetime.now()
        suite_result.total_duration_seconds = (
            suite_result.completed_at - suite_result.started_at
        ).total_seconds()
        
        if suite_result.total_failed == 0 and suite_result.total_errors == 0:
            suite_result.overall_status = TestStatus.PASSED
        else:
            suite_result.overall_status = TestStatus.FAILED
        
        suite_result.overall_coverage = self._calculate_overall_coverage(suite_result.results)
        
        return suite_result
    
    def _calculate_overall_coverage(self, results: List[TestResult]) -> float:
        coverages = [r.coverage_percent for r in results if r.coverage_percent > 0]
        return sum(coverages) / len(coverages) if coverages else 0.0
    
    def generate_report(
        self,
        suite_result: TestSuiteResult,
        output_path: Optional[str] = None,
        format: str = "markdown"
    ) -> str:
        if format == "json":
            return self._generate_json_report(suite_result, output_path)
        return self._generate_markdown_report(suite_result, output_path)
    
    def _generate_markdown_report(
        self,
        suite_result: TestSuiteResult,
        output_path: Optional[str] = None
    ) -> str:
        lines = [
            "# 综合测试套件报告",
            "",
            f"**套件ID**: {suite_result.suite_id}",
            f"**执行时间**: {suite_result.started_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**总耗时**: {suite_result.total_duration_seconds:.2f}秒",
            f"**总体状态**: {'✅ 通过' if suite_result.overall_status == TestStatus.PASSED else '❌ 失败'}",
            "",
            "## 测试统计",
            "",
            f"| 指标 | 数量 |",
            f"|------|------|",
            f"| 通过 | {suite_result.total_passed} |",
            f"| 失败 | {suite_result.total_failed} |",
            f"| 跳过 | {suite_result.total_skipped} |",
            f"| 错误 | {suite_result.total_errors} |",
            f"| 覆盖率 | {suite_result.overall_coverage:.1f}% |",
            "",
            "## 测试类型详情",
            "",
        ]
        
        status_emoji = {
            TestStatus.PASSED: "✅",
            TestStatus.FAILED: "❌",
            TestStatus.SKIPPED: "⏭️",
            TestStatus.ERROR: "⚠️",
            TestStatus.RUNNING: "🔄",
            TestStatus.PENDING: "⏳",
        }
        
        for result in suite_result.results:
            emoji = status_emoji.get(result.status, "❓")
            lines.extend([
                f"### {emoji} {result.test_type.value.upper()}",
                "",
                f"- **状态**: {result.status.value}",
                f"- **耗时**: {result.duration_seconds:.2f}秒",
                f"- **通过/失败/跳过**: {result.passed}/{result.failed}/{result.skipped}",
            ])
            
            if result.coverage_percent > 0:
                lines.append(f"- **覆盖率**: {result.coverage_percent:.1f}%")
            
            if result.details:
                lines.append("- **详情**:")
                for key, value in result.details.items():
                    lines.append(f"  - {key}: {value}")
            
            if result.error_message:
                lines.append(f"- **错误**: {result.error_message[:200]}")
            
            lines.append("")
        
        report = "\n".join(lines)
        
        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)
            suite_result.report_path = output_path
            logger.info(f"报告已保存: {output_path}")
        
        return report
    
    def _generate_json_report(
        self,
        suite_result: TestSuiteResult,
        output_path: Optional[str] = None
    ) -> str:
        report = json.dumps(suite_result.to_dict(), indent=2, ensure_ascii=False, default=str)
        
        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)
            suite_result.report_path = output_path
            logger.info(f"报告已保存: {output_path}")
        
        return report


def main():
    parser = argparse.ArgumentParser(
        description="综合测试套件运行器",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--project-root",
        type=str,
        default=".",
        help="项目根目录"
    )
    parser.add_argument(
        "--tests-dir",
        type=str,
        help="测试目录"
    )
    parser.add_argument(
        "--reports-dir",
        type=str,
        help="报告输出目录"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="运行所有测试类型"
    )
    parser.add_argument(
        "--unit",
        action="store_true",
        help="运行单元测试"
    )
    parser.add_argument(
        "--integration",
        action="store_true",
        help="运行集成测试"
    )
    parser.add_argument(
        "--database",
        action="store_true",
        help="运行数据库测试"
    )
    parser.add_argument(
        "--e2e",
        action="store_true",
        help="运行E2E测试"
    )
    parser.add_argument(
        "--performance",
        action="store_true",
        help="运行性能测试"
    )
    parser.add_argument(
        "--security",
        action="store_true",
        help="运行安全测试"
    )
    parser.add_argument(
        "--regression",
        action="store_true",
        help="运行回归测试"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="预览模式，不实际执行"
    )
    parser.add_argument(
        "--stop-on-failure",
        action="store_true",
        help="测试失败后停止"
    )
    parser.add_argument(
        "--report",
        type=str,
        help="报告输出路径"
    )
    parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="报告格式"
    )
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="生成覆盖率报告"
    )
    
    args = parser.parse_args()
    
    project_root = Path(args.project_root).resolve()
    
    runner = ComprehensiveTestRunner(
        project_root=str(project_root),
        tests_dir=args.tests_dir,
        reports_dir=args.reports_dir,
        skillscripts_path=str(project_root / "skillscripts")
    )
    
    test_types = []
    if args.all:
        test_types = ComprehensiveTestRunner.DEFAULT_TEST_TYPES
    else:
        if args.unit:
            test_types.append(TestType.UNIT)
        if args.integration:
            test_types.append(TestType.INTEGRATION)
        if args.database:
            test_types.append(TestType.DATABASE)
        if args.e2e:
            test_types.append(TestType.E2E)
        if args.performance:
            test_types.append(TestType.PERFORMANCE)
        if args.security:
            test_types.append(TestType.SECURITY)
        if args.regression:
            test_types.append(TestType.REGRESSION)
    
    if not test_types:
        test_types = [TestType.UNIT]
    
    print(f"\n{'='*60}")
    print("综合测试套件运行器")
    print(f"{'='*60}")
    print(f"套件ID: {runner.suite_id}")
    print(f"项目根目录: {project_root}")
    print(f"测试类型: {[t.value for t in test_types]}")
    print(f"{'='*60}\n")
    
    suite_result = runner.run(
        test_types=test_types,
        dry_run=args.dry_run,
        stop_on_failure=args.stop_on_failure
    )
    
    print(f"\n{'='*60}")
    print("测试执行完成")
    print(f"{'='*60}")
    print(f"总体状态: {suite_result.overall_status.value}")
    print(f"通过: {suite_result.total_passed}")
    print(f"失败: {suite_result.total_failed}")
    print(f"跳过: {suite_result.total_skipped}")
    print(f"错误: {suite_result.total_errors}")
    print(f"覆盖率: {suite_result.overall_coverage:.1f}%")
    print(f"总耗时: {suite_result.total_duration_seconds:.2f}秒")
    print(f"{'='*60}\n")
    
    if args.report:
        runner.generate_report(suite_result, args.report, args.format)
    else:
        report = runner.generate_report(suite_result, format=args.format)
        print(report)
    
    return 0 if suite_result.overall_status == TestStatus.PASSED else 1


if __name__ == "__main__":
    sys.exit(main())
