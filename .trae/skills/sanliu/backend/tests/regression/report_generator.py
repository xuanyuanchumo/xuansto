"""
回归测试报告生成器

生成详细的回归测试报告，支持多种格式输出
包括测试摘要、覆盖率分析、趋势分析等
"""

import os
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum


class ReportFormat(Enum):
    JSON = "json"
    HTML = "html"
    MARKDOWN = "markdown"
    CONSOLE = "console"


class TestStatus(Enum):
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class TestResult:
    test_id: str
    test_name: str
    test_file: str
    status: TestStatus
    duration: float
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None


@dataclass
class TestSuiteResult:
    suite_name: str
    total_tests: int
    passed: int
    failed: int
    skipped: int
    errors: int
    duration: float
    results: List[TestResult] = field(default_factory=list)
    coverage_percent: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class RegressionReport:
    project_name: str
    generated_at: str
    summary: Dict[str, Any]
    suites: List[TestSuiteResult]
    coverage: Dict[str, float]
    trends: Dict[str, Any]
    recommendations: List[str]
    failed_tests: List[Dict[str, Any]]
    performance_metrics: Dict[str, float]


class RegressionReportGenerator:
    """回归测试报告生成器"""
    
    def __init__(self, project_path: str, output_dir: str = "docs/reports/regression"):
        self.project_path = Path(project_path)
        self.output_dir = self.project_path / output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.history_file = self.output_dir / "regression_history.json"
        self.history: List[Dict[str, Any]] = []
        
    def run_tests(
        self,
        test_paths: List[str],
        parallel: bool = False,
        timeout: int = 300
    ) -> TestSuiteResult:
        """运行测试"""
        start_time = time.time()
        results = []
        
        cmd = ["python", "-m", "pytest", "-v", "--tb=short", "--json-report"]
        
        if parallel:
            cmd.extend(["-n", "auto"])
        
        cmd.extend(test_paths)
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            results = self._parse_pytest_output(result.stdout, result.stderr)
            
        except subprocess.TimeoutExpired:
            results = [TestResult(
                test_id="timeout",
                test_name="Test Execution",
                test_file="all",
                status=TestStatus.ERROR,
                duration=timeout,
                error_message="测试执行超时"
            )]
        except Exception as e:
            results = [TestResult(
                test_id="error",
                test_name="Test Execution",
                test_file="all",
                status=TestStatus.ERROR,
                duration=0,
                error_message=str(e)
            )]
        
        duration = time.time() - start_time
        
        return self._build_suite_result("regression_tests", results, duration)
    
    def _parse_pytest_output(self, stdout: str, stderr: str) -> List[TestResult]:
        """解析pytest输出"""
        results = []
        import re
        
        pattern = r'(?P<file>[^:]+)::(?P<test>\w+)\s+(?P<status>PASSED|FAILED|SKIPPED|ERROR)'
        
        for match in re.finditer(pattern, stdout):
            test_file = match.group("file")
            test_name = match.group("test")
            status_str = match.group("status")
            
            status_map = {
                "PASSED": TestStatus.PASSED,
                "FAILED": TestStatus.FAILED,
                "SKIPPED": TestStatus.SKIPPED,
                "ERROR": TestStatus.ERROR,
            }
            
            results.append(TestResult(
                test_id=f"{test_file}::{test_name}",
                test_name=test_name,
                test_file=test_file,
                status=status_map.get(status_str, TestStatus.ERROR),
                duration=0.0
            ))
        
        if not results:
            for line in stdout.split("\n"):
                if "test session starts" in line or "passed" in line.lower():
                    continue
                if line.strip().startswith("tests/"):
                    parts = line.split()
                    if len(parts) >= 2:
                        results.append(TestResult(
                            test_id=parts[0],
                            test_name=parts[0].split("::")[-1] if "::" in parts[0] else parts[0],
                            test_file=parts[0].split("::")[0] if "::" in parts[0] else "unknown",
                            status=TestStatus.PASSED if "PASSED" in line else TestStatus.FAILED,
                            duration=0.0
                        ))
        
        return results
    
    def _build_suite_result(
        self,
        suite_name: str,
        results: List[TestResult],
        duration: float
    ) -> TestSuiteResult:
        """构建测试套件结果"""
        passed = sum(1 for r in results if r.status == TestStatus.PASSED)
        failed = sum(1 for r in results if r.status == TestStatus.FAILED)
        skipped = sum(1 for r in results if r.status == TestStatus.SKIPPED)
        errors = sum(1 for r in results if r.status == TestStatus.ERROR)
        
        return TestSuiteResult(
            suite_name=suite_name,
            total_tests=len(results),
            passed=passed,
            failed=failed,
            skipped=skipped,
            errors=errors,
            duration=duration,
            results=results
        )
    
    def generate_report(
        self,
        suites: List[TestSuiteResult],
        format: ReportFormat = ReportFormat.HTML
    ) -> str:
        """生成报告"""
        report = self._build_report(suites)
        
        self._save_history(report)
        
        if format == ReportFormat.JSON:
            return self._generate_json_report(report)
        elif format == ReportFormat.HTML:
            return self._generate_html_report(report)
        elif format == ReportFormat.MARKDOWN:
            return self._generate_markdown_report(report)
        else:
            return self._generate_console_report(report)
    
    def _build_report(self, suites: List[TestSuiteResult]) -> RegressionReport:
        """构建报告数据"""
        total_tests = sum(s.total_tests for s in suites)
        total_passed = sum(s.passed for s in suites)
        total_failed = sum(s.failed for s in suites)
        total_skipped = sum(s.skipped for s in suites)
        total_errors = sum(s.errors for s in suites)
        total_duration = sum(s.duration for s in suites)
        
        pass_rate = (total_passed / max(total_tests, 1)) * 100
        
        failed_tests = []
        for suite in suites:
            for result in suite.results:
                if result.status == TestStatus.FAILED:
                    failed_tests.append({
                        "test_id": result.test_id,
                        "test_name": result.test_name,
                        "test_file": result.test_file,
                        "error_message": result.error_message,
                        "duration": result.duration
                    })
        
        coverage = self._calculate_coverage(suites)
        trends = self._analyze_trends()
        recommendations = self._generate_recommendations(suites, failed_tests)
        
        return RegressionReport(
            project_name=self.project_path.name,
            generated_at=datetime.now().isoformat(),
            summary={
                "total_tests": total_tests,
                "passed": total_passed,
                "failed": total_failed,
                "skipped": total_skipped,
                "errors": total_errors,
                "pass_rate": round(pass_rate, 2),
                "duration": round(total_duration, 2)
            },
            suites=suites,
            coverage=coverage,
            trends=trends,
            recommendations=recommendations,
            failed_tests=failed_tests,
            performance_metrics={
                "avg_test_duration": round(total_duration / max(total_tests, 1), 4),
                "tests_per_second": round(total_tests / max(total_duration, 0.1), 2)
            }
        )
    
    def _calculate_coverage(self, suites: List[TestSuiteResult]) -> Dict[str, float]:
        """计算覆盖率"""
        coverage = {
            "project_management": 0.0,
            "task_management": 0.0,
            "user_authentication": 0.0,
            "report_generation": 0.0,
            "workflow": 0.0,
            "integration": 0.0
        }
        
        for suite in suites:
            for result in suite.results:
                test_file = result.test_file.lower()
                
                if "project" in test_file:
                    coverage["project_management"] += 1
                elif "task" in test_file:
                    coverage["task_management"] += 1
                elif "auth" in test_file or "security" in test_file:
                    coverage["user_authentication"] += 1
                elif "report" in test_file:
                    coverage["report_generation"] += 1
                elif "workflow" in test_file:
                    coverage["workflow"] += 1
                else:
                    coverage["integration"] += 1
        
        total = sum(coverage.values())
        if total > 0:
            for key in coverage:
                coverage[key] = round(coverage[key] / total * 100, 2)
        
        return coverage
    
    def _save_history(self, report: RegressionReport) -> None:
        """保存历史记录"""
        self._load_history()
        
        self.history.append({
            "timestamp": report.generated_at,
            "summary": report.summary,
            "coverage": report.coverage
        })
        
        if len(self.history) > 100:
            self.history = self.history[-100:]
        
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(self.history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存历史记录失败: {e}")
    
    def _load_history(self) -> None:
        """加载历史记录"""
        if self.history_file.exists():
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    self.history = json.load(f)
            except Exception:
                self.history = []
    
    def _analyze_trends(self) -> Dict[str, Any]:
        """分析趋势"""
        self._load_history()
        
        if len(self.history) < 2:
            return {"message": "数据不足，无法分析趋势"}
        
        recent = self.history[-10:] if len(self.history) >= 10 else self.history
        
        pass_rates = [h["summary"]["pass_rate"] for h in recent]
        avg_pass_rate = sum(pass_rates) / len(pass_rates)
        
        trend_direction = "stable"
        if len(pass_rates) >= 3:
            recent_avg = sum(pass_rates[-3:]) / 3
            older_avg = sum(pass_rates[:3]) / 3
            if recent_avg > older_avg + 5:
                trend_direction = "improving"
            elif recent_avg < older_avg - 5:
                trend_direction = "declining"
        
        return {
            "avg_pass_rate": round(avg_pass_rate, 2),
            "trend_direction": trend_direction,
            "total_runs": len(self.history),
            "recent_runs": len(recent)
        }
    
    def _generate_recommendations(
        self,
        suites: List[TestSuiteResult],
        failed_tests: List[Dict[str, Any]]
    ) -> List[str]:
        """生成建议"""
        recommendations = []
        
        total_failed = sum(s.failed for s in suites)
        if total_failed > 0:
            recommendations.append(f"有 {total_failed} 个测试失败，请检查以下测试:")
            for test in failed_tests[:5]:
                recommendations.append(f"  - {test['test_id']}")
        
        total_errors = sum(s.errors for s in suites)
        if total_errors > 0:
            recommendations.append(f"有 {total_errors} 个测试错误，请检查测试环境配置")
        
        pass_rate = sum(s.passed for s in suites) / max(sum(s.total_tests for s in suites), 1) * 100
        if pass_rate < 80:
            recommendations.append(f"通过率 ({pass_rate:.1f}%) 低于80%，建议增加测试稳定性")
        
        trends = self._analyze_trends()
        if trends.get("trend_direction") == "declining":
            recommendations.append("测试通过率呈下降趋势，建议关注代码质量")
        
        if not recommendations:
            recommendations.append("回归测试全部通过，系统运行正常")
        
        recommendations.extend([
            "建议在每次提交前运行回归测试",
            "保持测试用例与代码同步更新",
            "定期检查测试稳定性"
        ])
        
        return recommendations
    
    def _generate_json_report(self, report: RegressionReport) -> str:
        """生成JSON报告"""
        output_path = self.output_dir / f"regression_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        data = {
            "project_name": report.project_name,
            "generated_at": report.generated_at,
            "summary": report.summary,
            "suites": [
                {
                    "suite_name": s.suite_name,
                    "total_tests": s.total_tests,
                    "passed": s.passed,
                    "failed": s.failed,
                    "skipped": s.skipped,
                    "errors": s.errors,
                    "duration": s.duration,
                    "coverage_percent": s.coverage_percent,
                    "timestamp": s.timestamp,
                    "results": [
                        {
                            "test_id": r.test_id,
                            "test_name": r.test_name,
                            "test_file": r.test_file,
                            "status": r.status.value,
                            "duration": r.duration,
                            "error_message": r.error_message
                        }
                        for r in s.results
                    ]
                }
                for s in report.suites
            ],
            "coverage": report.coverage,
            "trends": report.trends,
            "recommendations": report.recommendations,
            "failed_tests": report.failed_tests,
            "performance_metrics": report.performance_metrics
        }
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return str(output_path)
    
    def _generate_html_report(self, report: RegressionReport) -> str:
        """生成HTML报告"""
        output_path = self.output_dir / f"regression_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        
        pass_rate = report.summary["pass_rate"]
        pass_rate_class = "high" if pass_rate >= 80 else "medium" if pass_rate >= 60 else "low"
        
        suites_html = self._generate_suites_html(report.suites)
        coverage_html = self._generate_coverage_html(report.coverage)
        trends_html = self._generate_trends_html(report.trends)
        failed_html = self._generate_failed_tests_html(report.failed_tests)
        recommendations_html = self._generate_recommendations_html(report.recommendations)
        
        html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>回归测试报告 - {report.project_name}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; padding: 20px; }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        .header {{ background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 20px; }}
        .header h1 {{ font-size: 28px; margin-bottom: 10px; }}
        .header p {{ opacity: 0.9; }}
        .summary {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 20px; margin-bottom: 20px; }}
        .card {{ background: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .card h3 {{ color: #333; margin-bottom: 15px; font-size: 14px; text-transform: uppercase; }}
        .card .value {{ font-size: 32px; font-weight: bold; color: #6366f1; }}
        .card .label {{ color: #666; font-size: 12px; margin-top: 5px; }}
        .section {{ background: white; border-radius: 10px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .section h2 {{ color: #333; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #6366f1; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #eee; }}
        th {{ background: #f8f9fa; font-weight: 600; color: #333; }}
        .status-pass {{ color: #10b981; font-weight: bold; }}
        .status-fail {{ color: #ef4444; font-weight: bold; }}
        .status-error {{ color: #ef4444; }}
        .status-skip {{ color: #f59e0b; }}
        .progress-bar {{ height: 8px; background: #e5e7eb; border-radius: 4px; overflow: hidden; margin-top: 10px; }}
        .progress-fill {{ height: 100%; border-radius: 4px; }}
        .progress-fill.high {{ background: #10b981; }}
        .progress-fill.medium {{ background: #f59e0b; }}
        .progress-fill.low {{ background: #ef4444; }}
        .coverage-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-top: 15px; }}
        .coverage-item {{ padding: 15px; background: #f8f9fa; border-radius: 8px; text-align: center; }}
        .coverage-item .coverage-value {{ font-size: 24px; font-weight: bold; color: #6366f1; }}
        .coverage-item .coverage-label {{ font-size: 12px; color: #666; margin-top: 5px; }}
        .recommendation {{ padding: 10px 15px; background: #f8f9fa; border-radius: 8px; margin-bottom: 10px; border-left: 4px solid #6366f1; }}
        .recommendation.warning {{ border-left-color: #f59e0b; }}
        .recommendation.error {{ border-left-color: #ef4444; }}
        .recommendation.success {{ border-left-color: #10b981; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔄 回归测试报告</h1>
            <p>项目: {report.project_name}</p>
            <p>生成时间: {report.generated_at}</p>
        </div>
        
        <div class="summary">
            <div class="card">
                <h3>总测试数</h3>
                <div class="value">{report.summary["total_tests"]}</div>
                <div class="label">测试用例</div>
            </div>
            <div class="card">
                <h3>通过</h3>
                <div class="value" style="color: #10b981;">{report.summary["passed"]}</div>
                <div class="label">成功</div>
            </div>
            <div class="card">
                <h3>失败</h3>
                <div class="value" style="color: #ef4444;">{report.summary["failed"]}</div>
                <div class="label">失败</div>
            </div>
            <div class="card">
                <h3>跳过/错误</h3>
                <div class="value" style="color: #f59e0b;">{report.summary["skipped"]}/{report.summary["errors"]}</div>
                <div class="label">跳过/错误</div>
            </div>
            <div class="card">
                <h3>通过率</h3>
                <div class="value">{pass_rate:.1f}%</div>
                <div class="label">成功率</div>
                <div class="progress-bar">
                    <div class="progress-fill {pass_rate_class}" style="width: {min(pass_rate, 100)}%"></div>
                </div>
            </div>
        </div>
        
        {coverage_html}
        
        {trends_html}
        
        {suites_html}
        
        {failed_html}
        
        {recommendations_html}
    </div>
</body>
</html>'''
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
        
        return str(output_path)
    
    def _generate_suites_html(self, suites: List[TestSuiteResult]) -> str:
        """生成测试套件HTML"""
        rows = ""
        for suite in suites:
            pass_rate = (suite.passed / max(suite.total_tests, 1)) * 100
            rows += f'''
            <tr>
                <td>{suite.suite_name}</td>
                <td>{suite.total_tests}</td>
                <td class="status-pass">{suite.passed}</td>
                <td class="status-fail">{suite.failed}</td>
                <td>{suite.skipped}</td>
                <td>{suite.duration:.2f}s</td>
                <td>{pass_rate:.1f}%</td>
            </tr>'''
        
        return f'''
        <div class="section">
            <h2>📊 测试套件</h2>
            <table>
                <thead>
                    <tr>
                        <th>套件名称</th>
                        <th>总数</th>
                        <th>通过</th>
                        <th>失败</th>
                        <th>跳过</th>
                        <th>耗时</th>
                        <th>通过率</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        </div>'''
    
    def _generate_coverage_html(self, coverage: Dict[str, float]) -> str:
        """生成覆盖率HTML"""
        items = ""
        for name, value in coverage.items():
            label = {
                "project_management": "项目管理",
                "task_management": "任务管理",
                "user_authentication": "用户认证",
                "report_generation": "报告生成",
                "workflow": "工作流",
                "integration": "集成测试"
            }.get(name, name)
            
            items += f'''
            <div class="coverage-item">
                <div class="coverage-value">{value:.1f}%</div>
                <div class="coverage-label">{label}</div>
            </div>'''
        
        return f'''
        <div class="section">
            <h2>📈 功能覆盖率</h2>
            <div class="coverage-grid">
                {items}
            </div>
        </div>'''
    
    def _generate_trends_html(self, trends: Dict[str, Any]) -> str:
        """生成趋势HTML"""
        if "message" in trends:
            return f'''
            <div class="section">
                <h2>📉 趋势分析</h2>
                <p>{trends["message"]}</p>
            </div>'''
        
        trend_icon = "📈" if trends["trend_direction"] == "improving" else "📉" if trends["trend_direction"] == "declining" else "➡️"
        
        return f'''
        <div class="section">
            <h2>📉 趋势分析</h2>
            <div class="coverage-grid">
                <div class="coverage-item">
                    <div class="coverage-value">{trends["avg_pass_rate"]:.1f}%</div>
                    <div class="coverage-label">平均通过率</div>
                </div>
                <div class="coverage-item">
                    <div class="coverage-value">{trend_icon} {trends["trend_direction"]}</div>
                    <div class="coverage-label">趋势方向</div>
                </div>
                <div class="coverage-item">
                    <div class="coverage-value">{trends["total_runs"]}</div>
                    <div class="coverage-label">历史运行次数</div>
                </div>
            </div>
        </div>'''
    
    def _generate_failed_tests_html(self, failed_tests: List[Dict[str, Any]]) -> str:
        """生成失败测试HTML"""
        if not failed_tests:
            return ""
        
        rows = ""
        for test in failed_tests[:10]:
            rows += f'''
            <tr>
                <td>{test["test_id"]}</td>
                <td class="status-fail">失败</td>
                <td>{test.get("error_message", "-")[:100]}</td>
            </tr>'''
        
        return f'''
        <div class="section">
            <h2>❌ 失败测试</h2>
            <table>
                <thead>
                    <tr>
                        <th>测试ID</th>
                        <th>状态</th>
                        <th>错误信息</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        </div>'''
    
    def _generate_recommendations_html(self, recommendations: List[str]) -> str:
        """生成建议HTML"""
        items = ""
        for rec in recommendations:
            css_class = ""
            if "失败" in rec or "错误" in rec:
                css_class = "error"
            elif "警告" in rec or "下降" in rec:
                css_class = "warning"
            elif "通过" in rec or "正常" in rec:
                css_class = "success"
            
            items += f'<div class="recommendation {css_class}">{rec}</div>'
        
        return f'''
        <div class="section">
            <h2>💡 建议</h2>
            {items}
        </div>'''
    
    def _generate_markdown_report(self, report: RegressionReport) -> str:
        """生成Markdown报告"""
        output_path = self.output_dir / f"regression_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        md = f'''# 回归测试报告

## 概述

- **项目**: {report.project_name}
- **生成时间**: {report.generated_at}
- **总测试数**: {report.summary["total_tests"]}
- **通过**: {report.summary["passed"]}
- **失败**: {report.summary["failed"]}
- **跳过**: {report.summary["skipped"]}
- **错误**: {report.summary["errors"]}
- **通过率**: {report.summary["pass_rate"]:.1f}%
- **执行时间**: {report.summary["duration"]:.2f}s

## 功能覆盖率

| 功能模块 | 覆盖率 |
|---------|--------|
'''
        
        for name, value in report.coverage.items():
            md += f"| {name} | {value:.1f}% |\n"
        
        md += '''
## 建议

'''
        for rec in report.recommendations:
            md += f"- {rec}\n"
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(md)
        
        return str(output_path)
    
    def _generate_console_report(self, report: RegressionReport) -> str:
        """生成控制台报告"""
        print("\n" + "=" * 80)
        print("回归测试报告")
        print("=" * 80)
        
        print(f"\n项目: {report.project_name}")
        print(f"生成时间: {report.generated_at}")
        
        print(f"\n测试摘要:")
        print(f"  总测试数: {report.summary['total_tests']}")
        print(f"  通过: {report.summary['passed']}")
        print(f"  失败: {report.summary['failed']}")
        print(f"  跳过: {report.summary['skipped']}")
        print(f"  错误: {report.summary['errors']}")
        print(f"  通过率: {report.summary['pass_rate']:.1f}%")
        print(f"  执行时间: {report.summary['duration']:.2f}s")
        
        print(f"\n建议:")
        for i, rec in enumerate(report.recommendations[:5], 1):
            print(f"  {i}. {rec}")
        
        return "控制台报告已生成"


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="回归测试报告生成器")
    parser.add_argument("--project-path", default=".", help="项目路径")
    parser.add_argument("--test-paths", nargs="+", default=["tests/"], help="测试路径")
    parser.add_argument("--format", choices=["json", "html", "markdown", "console"],
                       default="html", help="报告格式")
    parser.add_argument("--parallel", action="store_true", help="并行执行")
    parser.add_argument("--timeout", type=int, default=300, help="超时时间(秒)")
    
    args = parser.parse_args()
    
    generator = RegressionReportGenerator(args.project_path)
    
    print("运行回归测试...")
    suite = generator.run_tests(args.test_paths, args.parallel, args.timeout)
    
    print("生成报告...")
    report_path = generator.generate_report([suite], ReportFormat(args.format))
    
    print(f"报告已生成: {report_path}")


if __name__ == "__main__":
    main()
