#!/usr/bin/env python3
"""
测试流水线编排器 - Sanliu 技能（增强版）

功能：
- 测试套件自动执行（按依赖顺序）
- 并行测试执行
- 测试结果聚合
- 测试失败自动通知
- 支持增量测试
- 测试重试机制（智能重试失败测试）
- 测试报告自动生成（多格式支持）
- 测试历史记录与趋势分析
- 测试覆盖率追踪

使用方法：
    python test_pipeline_orchestrator.py --help
    python test_pipeline_orchestrator.py --target tests/
    python test_pipeline_orchestrator.py --target tests/ --parallel 4
    python test_pipeline_orchestrator.py --target tests/ --incremental
    python test_pipeline_orchestrator.py --target tests/ --retry 3
    python test_pipeline_orchestrator.py --target tests/ --report html
    python test_pipeline_orchestrator.py --config pipeline_config.yaml
"""

import concurrent.futures
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from skillscripts.core.script_base import ScriptBase, ReportFormat, ScriptResult, ScriptStatus


class TestStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class TestPriority(Enum):
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


@dataclass
class TestCase:
    name: str
    file_path: str
    module: str
    dependencies: List[str] = field(default_factory=list)
    priority: TestPriority = TestPriority.MEDIUM
    status: TestStatus = TestStatus.PENDING
    duration: float = 0.0
    error_message: str = ""
    output: str = ""
    markers: List[str] = field(default_factory=list)


@dataclass
class TestSuite:
    name: str
    test_cases: List[TestCase] = field(default_factory=list)
    setup_script: Optional[str] = None
    teardown_script: Optional[str] = None
    parallel: bool = True


@dataclass
class PipelineResult:
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    errors: int = 0
    duration: float = 0.0
    test_suites: List[Dict[str, Any]] = field(default_factory=list)
    failed_tests: List[Dict[str, Any]] = field(default_factory=list)
    coverage_report: Optional[Dict[str, Any]] = None
    retry_count: int = 0
    retry_passed: int = 0
    history: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class TestRetryConfig:
    max_retries: int = 3
    retry_delay: float = 1.0
    retry_on_timeout: bool = True
    retry_on_failure: bool = True
    exponential_backoff: bool = True
    max_delay: float = 30.0


@dataclass
class TestHistory:
    test_name: str
    runs: List[Dict[str, Any]] = field(default_factory=list)
    pass_rate: float = 0.0
    avg_duration: float = 0.0
    flaky: bool = False


class TestRetryHandler:
    """测试重试处理器"""
    
    def __init__(self, config: TestRetryConfig, logger):
        self.config = config
        self.logger = logger
        self.retry_history: Dict[str, List[bool]] = defaultdict(list)
    
    def should_retry(self, test: TestCase, attempt: int) -> bool:
        if attempt >= self.config.max_retries:
            return False
        
        if test.status == TestStatus.FAILED and self.config.retry_on_failure:
            return True
        
        if test.status == TestStatus.ERROR:
            if "超时" in test.error_message and self.config.retry_on_timeout:
                return True
        
        return False
    
    def get_retry_delay(self, attempt: int) -> float:
        if self.config.exponential_backoff:
            delay = self.config.retry_delay * (2 ** attempt)
            return min(delay, self.config.max_delay)
        return self.config.retry_delay
    
    def execute_with_retry(self, test: TestCase, executor: 'TestExecutor') -> TestCase:
        attempt = 0
        original_status = test.status
        
        while attempt < self.config.max_retries:
            if attempt > 0:
                delay = self.get_retry_delay(attempt - 1)
                self.logger.info(f"重试测试 {test.name} (第 {attempt + 1} 次)，等待 {delay:.1f} 秒")
                import time
                time.sleep(delay)
            
            result = executor.execute_test(test)
            
            if result.status in [TestStatus.PASSED, TestStatus.SKIPPED]:
                if attempt > 0:
                    self.retry_history[test.name].append(True)
                    self.logger.info(f"测试 {test.name} 在第 {attempt + 1} 次重试后通过")
                return result
            
            attempt += 1
        
        self.retry_history[test.name].append(False)
        test.status = original_status
        return test
    
    def get_retry_statistics(self) -> Dict[str, Any]:
        total_retries = sum(len(v) for v in self.retry_history.values())
        successful_retries = sum(sum(1 for r in v if r) for v in self.retry_history.values())
        
        return {
            "total_retries": total_retries,
            "successful_retries": successful_retries,
            "retry_success_rate": successful_retries / total_retries if total_retries > 0 else 0,
            "tests_retried": list(self.retry_history.keys())
        }


class TestReportGenerator:
    """测试报告生成器"""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_report(self, result: PipelineResult, format: str = "html") -> Path:
        if format == "html":
            return self._generate_html_report(result)
        elif format == "json":
            return self._generate_json_report(result)
        elif format == "markdown":
            return self._generate_markdown_report(result)
        elif format == "junit":
            return self._generate_junit_report(result)
        else:
            return self._generate_html_report(result)
    
    def _generate_html_report(self, result: PipelineResult) -> Path:
        report_path = self.output_dir / f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        
        pass_rate = (result.passed / result.total_tests * 100) if result.total_tests > 0 else 0
        
        html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>测试报告 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</title>
    <style>
        * {{ box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 20px; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin-bottom: 20px; }}
        .stat-card {{ background: white; padding: 20px; border-radius: 10px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .stat-value {{ font-size: 32px; font-weight: bold; }}
        .stat-label {{ color: #666; margin-top: 5px; }}
        .passed {{ color: #10b981; }}
        .failed {{ color: #ef4444; }}
        .skipped {{ color: #f59e0b; }}
        .errors {{ color: #dc2626; }}
        .progress-bar {{ height: 20px; background: #e5e7eb; border-radius: 10px; overflow: hidden; margin: 20px 0; }}
        .progress {{ height: 100%; transition: width 0.3s; }}
        .test-list {{ background: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .test-item {{ padding: 15px; border-bottom: 1px solid #e5e7eb; display: flex; justify-content: space-between; align-items: center; }}
        .test-item:last-child {{ border-bottom: none; }}
        .test-name {{ font-weight: 500; }}
        .test-duration {{ color: #666; font-size: 0.9em; }}
        .badge {{ padding: 4px 12px; border-radius: 20px; font-size: 0.8em; font-weight: 500; }}
        .badge-passed {{ background: #d1fae5; color: #065f46; }}
        .badge-failed {{ background: #fee2e2; color: #991b1b; }}
        .badge-skipped {{ background: #fef3c7; color: #92400e; }}
        .badge-error {{ background: #fecaca; color: #7f1d1d; }}
        .section {{ margin-bottom: 20px; }}
        .section-title {{ font-size: 1.2em; font-weight: 600; margin-bottom: 15px; color: #374151; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧪 测试执行报告</h1>
            <p>执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 总耗时: {result.duration:.2f}秒</p>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-value">{result.total_tests}</div>
                <div class="stat-label">总测试数</div>
            </div>
            <div class="stat-card">
                <div class="stat-value passed">{result.passed}</div>
                <div class="stat-label">通过</div>
            </div>
            <div class="stat-card">
                <div class="stat-value failed">{result.failed}</div>
                <div class="stat-label">失败</div>
            </div>
            <div class="stat-card">
                <div class="stat-value skipped">{result.skipped}</div>
                <div class="stat-label">跳过</div>
            </div>
            <div class="stat-card">
                <div class="stat-value errors">{result.errors}</div>
                <div class="stat-label">错误</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{pass_rate:.1f}%</div>
                <div class="stat-label">通过率</div>
            </div>
        </div>
        
        <div class="section">
            <div class="section-title">📊 通过率</div>
            <div class="progress-bar">
                <div class="progress" style="width: {pass_rate}%; background: {'#10b981' if pass_rate >= 80 else '#f59e0b' if pass_rate >= 60 else '#ef4444'};"></div>
            </div>
        </div>
        
        {self._generate_retry_section_html(result)}
        
        {self._generate_failed_tests_html(result)}
        
        {self._generate_coverage_section_html(result)}
    </div>
</body>
</html>"""
        
        report_path.write_text(html_content, encoding='utf-8')
        return report_path
    
    def _generate_retry_section_html(self, result: PipelineResult) -> str:
        if result.retry_count == 0:
            return ""
        
        return f"""
        <div class="section">
            <div class="section-title">🔄 重试统计</div>
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-value">{result.retry_count}</div>
                    <div class="stat-label">重试次数</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value passed">{result.retry_passed}</div>
                    <div class="stat-label">重试后通过</div>
                </div>
            </div>
        </div>
        """
    
    def _generate_failed_tests_html(self, result: PipelineResult) -> str:
        if not result.failed_tests:
            return '<div class="section"><div class="section-title">✅ 所有测试通过</div></div>'
        
        items = []
        for test in result.failed_tests[:20]:
            items.append(f"""
            <div class="test-item">
                <div>
                    <div class="test-name">{test['name']}</div>
                    <div class="test-duration">{test.get('error', '')[:100]}...</div>
                </div>
                <span class="badge badge-failed">失败</span>
            </div>
            """)
        
        return f"""
        <div class="section">
            <div class="section-title">❌ 失败测试 ({len(result.failed_tests)})</div>
            <div class="test-list">
                {''.join(items)}
            </div>
        </div>
        """
    
    def _generate_coverage_section_html(self, result: PipelineResult) -> str:
        if not result.coverage_report:
            return ""
        
        coverage = result.coverage_report.get('totals', {}).get('percent_covered', 0)
        return f"""
        <div class="section">
            <div class="section-title">📈 代码覆盖率</div>
            <div class="progress-bar">
                <div class="progress" style="width: {coverage}%; background: {'#10b981' if coverage >= 80 else '#f59e0b' if coverage >= 60 else '#ef4444'};"></div>
            </div>
            <p style="text-align: center; margin-top: 10px;">{coverage:.1f}%</p>
        </div>
        """
    
    def _generate_json_report(self, result: PipelineResult) -> Path:
        report_path = self.output_dir / f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": result.total_tests,
                "passed": result.passed,
                "failed": result.failed,
                "skipped": result.skipped,
                "errors": result.errors,
                "duration": result.duration,
                "pass_rate": (result.passed / result.total_tests * 100) if result.total_tests > 0 else 0,
                "retry_count": result.retry_count,
                "retry_passed": result.retry_passed
            },
            "failed_tests": result.failed_tests,
            "coverage": result.coverage_report,
            "test_suites": result.test_suites
        }
        
        report_path.write_text(json.dumps(report_data, indent=2, ensure_ascii=False), encoding='utf-8')
        return report_path
    
    def _generate_markdown_report(self, result: PipelineResult) -> Path:
        report_path = self.output_dir / f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        pass_rate = (result.passed / result.total_tests * 100) if result.total_tests > 0 else 0
        
        lines = [
            f"# 测试执行报告",
            f"",
            f"**执行时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**总耗时**: {result.duration:.2f}秒",
            f"",
            f"## 📊 测试统计",
            f"",
            f"| 指标 | 数量 |",
            f"|------|------|",
            f"| 总测试数 | {result.total_tests} |",
            f"| 通过 | {result.passed} |",
            f"| 失败 | {result.failed} |",
            f"| 跳过 | {result.skipped} |",
            f"| 错误 | {result.errors} |",
            f"| 通过率 | {pass_rate:.1f}% |",
        ]
        
        if result.retry_count > 0:
            lines.extend([
                f"",
                f"## 🔄 重试统计",
                f"",
                f"- 重试次数: {result.retry_count}",
                f"- 重试后通过: {result.retry_passed}",
            ])
        
        if result.failed_tests:
            lines.extend([
                f"",
                f"## ❌ 失败测试",
                f"",
            ])
            for test in result.failed_tests[:10]:
                lines.append(f"- **{test['name']}**: {test.get('error', 'Unknown error')[:50]}...")
        
        report_path.write_text('\n'.join(lines), encoding='utf-8')
        return report_path
    
    def _generate_junit_report(self, result: PipelineResult) -> Path:
        report_path = self.output_dir / f"junit_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml"
        
        xml_lines = [
            f'<?xml version="1.0" encoding="UTF-8"?>',
            f'<testsuites tests="{result.total_tests}" failures="{result.failed}" errors="{result.errors}" time="{result.duration}">',
        ]
        
        for suite in result.test_suites:
            xml_lines.append(f'  <testsuite name="{suite.get("name", "unknown")}" tests="{suite.get("total", 0)}" failures="{suite.get("failed", 0)}" errors="{suite.get("errors", 0)}" time="{suite.get("duration", 0)}">')
            for test in suite.get("tests", []):
                xml_lines.append(f'    <testcase name="{test.get("name", "unknown")}" classname="{test.get("classname", "")}" time="{test.get("duration", 0)}">')
                if test.get("status") in ["failed", "error"]:
                    xml_lines.append(f'      <failure message="{test.get("error", "")[:200]}"/>')
                xml_lines.append(f'    </testcase>')
            xml_lines.append(f'  </testsuite>')
        
        xml_lines.append(f'</testsuites>')
        
        report_path.write_text('\n'.join(xml_lines), encoding='utf-8')
        return report_path


class TestHistoryTracker:
    """测试历史追踪器"""
    
    def __init__(self, history_dir: Path):
        self.history_dir = history_dir
        self.history_dir.mkdir(parents=True, exist_ok=True)
        self.history_file = history_dir / "test_history.json"
        self._history: Dict[str, TestHistory] = {}
        self._load_history()
    
    def _load_history(self):
        if self.history_file.exists():
            try:
                data = json.loads(self.history_file.read_text(encoding='utf-8'))
                for name, info in data.items():
                    self._history[name] = TestHistory(
                        test_name=name,
                        runs=info.get('runs', []),
                        pass_rate=info.get('pass_rate', 0.0),
                        avg_duration=info.get('avg_duration', 0.0),
                        flaky=info.get('flaky', False)
                    )
            except Exception:
                pass
    
    def _save_history(self):
        data = {}
        for name, history in self._history.items():
            data[name] = {
                'runs': history.runs[-50:],
                'pass_rate': history.pass_rate,
                'avg_duration': history.avg_duration,
                'flaky': history.flaky
            }
        self.history_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')
    
    def record_test_run(self, test: TestCase):
        if test.name not in self._history:
            self._history[test.name] = TestHistory(test_name=test.name)
        
        history = self._history[test.name]
        history.runs.append({
            'timestamp': datetime.now().isoformat(),
            'status': test.status.value,
            'duration': test.duration,
            'error': test.error_message[:100] if test.error_message else None
        })
        
        passed_runs = [r for r in history.runs if r['status'] == 'passed']
        history.pass_rate = len(passed_runs) / len(history.runs) if history.runs else 0
        history.avg_duration = sum(r['duration'] for r in history.runs) / len(history.runs)
        
        if len(history.runs) >= 5:
            recent = [r['status'] for r in history.runs[-5:]]
            history.flaky = 'passed' in recent and 'failed' in recent
        
        self._save_history()
    
    def get_flaky_tests(self) -> List[str]:
        return [name for name, history in self._history.items() if history.flaky]
    
    def get_test_trends(self) -> Dict[str, Any]:
        if not self._history:
            return {}
        
        total_tests = len(self._history)
        flaky_count = len(self.get_flaky_tests())
        avg_pass_rate = sum(h.pass_rate for h in self._history.values()) / total_tests if total_tests > 0 else 0
        
        return {
            'total_tracked_tests': total_tests,
            'flaky_tests': flaky_count,
            'average_pass_rate': avg_pass_rate,
            'flaky_test_names': self.get_flaky_tests()
        }


class DependencyResolver:
    def __init__(self):
        self.graph: Dict[str, Set[str]] = defaultdict(set)
        self.reverse_graph: Dict[str, Set[str]] = defaultdict(set)

    def add_test(self, test_name: str, dependencies: List[str]):
        self.graph[test_name] = set(dependencies)
        for dep in dependencies:
            self.reverse_graph[dep].add(test_name)

    def resolve_order(self, tests: List[TestCase]) -> List[List[TestCase]]:
        test_map = {t.name: t for t in tests}
        in_degree = {t.name: len(t.dependencies) for t in tests}
        queue = [t for t in tests if in_degree[t.name] == 0]
        levels = []

        while queue:
            current_level = queue.copy()
            levels.append(current_level)
            queue.clear()

            for test in current_level:
                for dependent in self.reverse_graph[test.name]:
                    if dependent in in_degree:
                        in_degree[dependent] -= 1
                        if in_degree[dependent] == 0:
                            queue.append(test_map[dependent])

        all_scheduled = sum(len(level) for level in levels)
        if all_scheduled < len(tests):
            unscheduled = [t for t in tests if t not in [t for level in levels for t in level]]
            for test in unscheduled:
                test.status = TestStatus.SKIPPED
                test.error_message = "循环依赖检测，跳过测试"
            levels.append(unscheduled)

        return levels


class TestDiscovery:
    def __init__(self, target_dir: Path):
        self.target_dir = target_dir

    def discover_tests(self) -> List[TestCase]:
        tests = []
        test_files = list(self.target_dir.rglob("test_*.py")) + list(self.target_dir.rglob("*_test.py"))

        for test_file in test_files:
            file_tests = self._parse_test_file(test_file)
            tests.extend(file_tests)

        return tests

    def _parse_test_file(self, file_path: Path) -> List[TestCase]:
        tests = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            test_functions = re.findall(r'def\s+(test_\w+)\s*\(', content)
            test_classes = re.findall(r'class\s+(Test\w*)\s*[:\(]', content)

            for func_name in test_functions:
                markers = self._extract_markers(content, func_name)
                dependencies = self._extract_dependencies(content, func_name)
                priority = self._determine_priority(markers)

                tests.append(TestCase(
                    name=f"{file_path.stem}::{func_name}",
                    file_path=str(file_path),
                    module=file_path.stem,
                    dependencies=dependencies,
                    priority=priority,
                    markers=markers
                ))

            for class_name in test_classes:
                class_methods = re.findall(
                    rf'class\s+{class_name}.*?def\s+(test_\w+)\s*\(',
                    content,
                    re.DOTALL
                )
                for method_name in class_methods:
                    markers = self._extract_markers(content, method_name)
                    dependencies = self._extract_dependencies(content, method_name)
                    priority = self._determine_priority(markers)

                    tests.append(TestCase(
                        name=f"{file_path.stem}::{class_name}::{method_name}",
                        file_path=str(file_path),
                        module=file_path.stem,
                        dependencies=dependencies,
                        priority=priority,
                        markers=markers
                    ))

        except Exception as e:
            pass

        return tests

    def _extract_markers(self, content: str, test_name: str) -> List[str]:
        markers = []
        pattern = rf'@pytest\.mark\.(\w+).*?def\s+{test_name}'
        matches = re.findall(pattern, content, re.DOTALL)
        markers.extend(matches)
        return markers

    def _extract_dependencies(self, content: str, test_name: str) -> List[str]:
        dependencies = []
        dep_pattern = rf'@pytest\.mark\.depends_on\(["\']([^"\']+)["\']\)'
        func_pattern = rf'{dep_pattern}.*?def\s+{test_name}'
        matches = re.findall(func_pattern, content, re.DOTALL)
        dependencies.extend(matches)
        return dependencies

    def _determine_priority(self, markers: List[str]) -> TestPriority:
        if 'critical' in markers:
            return TestPriority.CRITICAL
        elif 'high' in markers:
            return TestPriority.HIGH
        elif 'slow' in markers:
            return TestPriority.LOW
        return TestPriority.MEDIUM


class TestExecutor:
    def __init__(self, parallel_workers: int = 4, timeout: int = 300):
        self.parallel_workers = parallel_workers
        self.timeout = timeout

    def execute_test(self, test: TestCase) -> TestCase:
        test.status = TestStatus.RUNNING
        start_time = datetime.now()

        try:
            result = subprocess.run(
                ['python', '-m', 'pytest', test.file_path, '-v', '--tb=short', '-k', test.name.split('::')[-1]],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            test.duration = (datetime.now() - start_time).total_seconds()
            test.output = result.stdout + result.stderr

            if result.returncode == 0:
                test.status = TestStatus.PASSED
            else:
                test.status = TestStatus.FAILED
                test.error_message = self._extract_error_message(result.stdout + result.stderr)

        except subprocess.TimeoutExpired:
            test.status = TestStatus.ERROR
            test.error_message = f"测试超时（{self.timeout}秒）"
            test.duration = self.timeout

        except Exception as e:
            test.status = TestStatus.ERROR
            test.error_message = str(e)

        return test

    def execute_parallel(self, tests: List[TestCase]) -> List[TestCase]:
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.parallel_workers) as executor:
            future_to_test = {executor.submit(self.execute_test, test): test for test in tests}
            for future in concurrent.futures.as_completed(future_to_test):
                test = future_to_test[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    test.status = TestStatus.ERROR
                    test.error_message = str(e)
                    results.append(test)

        return results

    def _extract_error_message(self, output: str) -> str:
        error_lines = []
        in_error = False
        for line in output.split('\n'):
            if 'FAILED' in line or 'ERROR' in line:
                in_error = True
            if in_error:
                error_lines.append(line)
                if len(error_lines) > 10:
                    break
        return '\n'.join(error_lines[:10])


class NotificationHandler:
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.notifications: List[Dict[str, Any]] = []

    def notify_failure(self, test: TestCase, context: Dict[str, Any]):
        notification = {
            "type": "test_failure",
            "test_name": test.name,
            "file_path": test.file_path,
            "error_message": test.error_message,
            "duration": test.duration,
            "timestamp": datetime.now().isoformat(),
            "context": context
        }
        self.notifications.append(notification)
        self._send_notification(notification)

    def notify_pipeline_complete(self, result: PipelineResult):
        notification = {
            "type": "pipeline_complete",
            "total_tests": result.total_tests,
            "passed": result.passed,
            "failed": result.failed,
            "duration": result.duration,
            "timestamp": datetime.now().isoformat()
        }
        self.notifications.append(notification)
        self._send_notification(notification)

    def _send_notification(self, notification: Dict[str, Any]):
        if self.config.get('webhook_url'):
            try:
                import requests
                requests.post(self.config['webhook_url'], json=notification, timeout=5)
            except Exception:
                pass

        if self.config.get('email_recipients'):
            pass


class CoverageCollector:
    def __init__(self, source_dir: Path):
        self.source_dir = source_dir
        self.coverage_data: Dict[str, Any] = {}

    def collect_coverage(self, test_results: List[TestCase]) -> Dict[str, Any]:
        try:
            result = subprocess.run(
                ['python', '-m', 'coverage', 'report', '--json'],
                capture_output=True,
                text=True,
                cwd=self.source_dir
            )

            if result.returncode == 0:
                coverage_file = self.source_dir / 'coverage.json'
                if coverage_file.exists():
                    with open(coverage_file, 'r') as f:
                        self.coverage_data = json.load(f)

        except Exception:
            pass

        return self.coverage_data


class IncrementalTestSelector:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.changed_files: Set[str] = set()

    def detect_changes(self, base_branch: str = 'main') -> Set[str]:
        try:
            result = subprocess.run(
                ['git', 'diff', '--name-only', f'origin/{base_branch}...HEAD'],
                capture_output=True,
                text=True,
                cwd=self.project_dir
            )

            if result.returncode == 0:
                self.changed_files = set(result.stdout.strip().split('\n'))

        except Exception:
            pass

        return self.changed_files

    def select_tests(self, all_tests: List[TestCase]) -> List[TestCase]:
        if not self.changed_files:
            return all_tests

        selected = []
        for test in all_tests:
            test_file = Path(test.file_path)
            if any(changed in str(test_file) for changed in self.changed_files):
                selected.append(test)
            elif self._test_covers_changed_files(test, self.changed_files):
                selected.append(test)

        return selected if selected else all_tests

    def _test_covers_changed_files(self, test: TestCase, changed_files: Set[str]) -> bool:
        test_module = test.module.replace('test_', '')
        for changed in changed_files:
            if test_module in changed.replace('.py', ''):
                return True
        return False


class TestPipelineOrchestrator(ScriptBase):
    def __init__(self):
        super().__init__(
            name="test_pipeline_orchestrator",
            version="2.0.0",
            description="测试流水线编排器（增强版） - 支持依赖解析、并行执行、增量测试、智能重试和报告生成",
            author="Sanliu"
        )
        self._setup_arguments()
        self.tests: List[TestCase] = []
        self.result = PipelineResult()
        self.executor: Optional[TestExecutor] = None
        self.notification_handler: Optional[NotificationHandler] = None
        self.retry_handler: Optional[TestRetryHandler] = None
        self.report_generator: Optional[TestReportGenerator] = None
        self.history_tracker: Optional[TestHistoryTracker] = None

    def _setup_arguments(self):
        self._command_parser.add_argument(
            '--target',
            type=str,
            default='./tests',
            help='测试目录路径'
        )
        self._command_parser.add_argument(
            '--parallel',
            type=int,
            default=4,
            help='并行执行的工作进程数'
        )
        self._command_parser.add_argument(
            '--timeout',
            type=int,
            default=300,
            help='单个测试超时时间（秒）'
        )
        self._command_parser.add_argument(
            '--incremental',
            action='store_true',
            help='启用增量测试模式'
        )
        self._command_parser.add_argument(
            '--base-branch',
            type=str,
            default='main',
            help='增量测试的基准分支'
        )
        self._command_parser.add_argument(
            '--fail-fast',
            action='store_true',
            help='遇到失败立即停止'
        )
        self._command_parser.add_argument(
            '--notify',
            action='store_true',
            help='启用测试失败通知'
        )
        self._command_parser.add_argument(
            '--webhook-url',
            type=str,
            help='通知webhook URL'
        )
        self._command_parser.add_argument(
            '--coverage',
            action='store_true',
            help='收集测试覆盖率'
        )
        self._command_parser.add_argument(
            '--source-dir',
            type=str,
            help='源代码目录（用于覆盖率收集）'
        )
        self._command_parser.add_argument(
            '--retry',
            type=int,
            default=0,
            help='失败测试重试次数'
        )
        self._command_parser.add_argument(
            '--retry-delay',
            type=float,
            default=1.0,
            help='重试延迟时间（秒）'
        )
        self._command_parser.add_argument(
            '--report',
            type=str,
            choices=['html', 'json', 'markdown', 'junit'],
            default='html',
            help='报告格式'
        )
        self._command_parser.add_argument(
            '--report-dir',
            type=str,
            default=str(get_path_config().REPORTS_DIR / "tests"),
            help='报告输出目录'
        )
        self._command_parser.add_argument(
            '--history',
            action='store_true',
            help='启用测试历史追踪'
        )
        self._command_parser.add_argument(
            '--history-dir',
            type=str,
            default=str(get_path_config().REPORTS_DIR / "test_history"),
            help='测试历史目录'
        )
        self._command_parser.add_argument(
            '--flaky-detection',
            action='store_true',
            help='启用不稳定测试检测'
        )

    def initialize(self, config: Dict[str, Any]) -> None:
        super().initialize(config)
        self.executor = TestExecutor(
            parallel_workers=config.get('parallel', 4),
            timeout=config.get('timeout', 300)
        )
        self.notification_handler = NotificationHandler({
            'webhook_url': config.get('webhook_url'),
            'email_recipients': config.get('email_recipients', [])
        })
        
        retry_config = TestRetryConfig(
            max_retries=config.get('retry', 0),
            retry_delay=config.get('retry_delay', 1.0),
            retry_on_timeout=True,
            retry_on_failure=True,
            exponential_backoff=True
        )
        self.retry_handler = TestRetryHandler(retry_config, self._logger)
        
        self.report_generator = TestReportGenerator(Path(config.get('report_dir', str(get_path_config().REPORTS_DIR / 'tests'))))
        
        if config.get('history', False):
            self.history_tracker = TestHistoryTracker(Path(config.get('history_dir', str(get_path_config().REPORTS_DIR / 'test_history'))))

    def validate_inputs(self, *args, **kwargs) -> bool:
        target = kwargs.get('target', './tests')
        target_path = Path(target)
        if not target_path.exists():
            self._logger.error(f"测试目录不存在: {target}")
            return False
        return True

    def run(self, *args, **kwargs) -> Any:
        target = kwargs.get('target', './tests')
        parallel = kwargs.get('parallel', 4)
        incremental = kwargs.get('incremental', False)
        base_branch = kwargs.get('base_branch', 'main')
        fail_fast = kwargs.get('fail_fast', False)
        enable_notify = kwargs.get('notify', False)
        enable_coverage = kwargs.get('coverage', False)
        source_dir = kwargs.get('source_dir', '.')
        retry_count = kwargs.get('retry', 0)
        retry_delay = kwargs.get('retry_delay', 1.0)
        report_format = kwargs.get('report', 'html')
        report_dir = kwargs.get('report_dir', str(get_path_config().REPORTS_DIR / 'tests'))
        enable_history = kwargs.get('history', False)
        history_dir = kwargs.get('history_dir', str(get_path_config().REPORTS_DIR / 'test_history'))
        flaky_detection = kwargs.get('flaky_detection', False)

        start_time = datetime.now()

        self._logger.info(f"开始测试流水线编排（增强版） - 目标: {target}")
        self._report.add_section("配置信息", {
            "target": target,
            "parallel_workers": parallel,
            "incremental": incremental,
            "fail_fast": fail_fast,
            "retry_count": retry_count,
            "report_format": report_format,
            "history_enabled": enable_history
        })

        retry_config = TestRetryConfig(
            max_retries=retry_count,
            retry_delay=retry_delay,
            retry_on_timeout=True,
            retry_on_failure=True,
            exponential_backoff=True
        )
        self.retry_handler = TestRetryHandler(retry_config, self._logger)
        self.report_generator = TestReportGenerator(Path(report_dir))
        
        if enable_history:
            self.history_tracker = TestHistoryTracker(Path(history_dir))

        discovery = TestDiscovery(Path(target))
        self.tests = discovery.discover_tests()
        self._logger.info(f"发现 {len(self.tests)} 个测试用例")

        if incremental:
            selector = IncrementalTestSelector(Path.cwd())
            selector.detect_changes(base_branch)
            self.tests = selector.select_tests(self.tests)
            self._logger.info(f"增量测试选择 {len(self.tests)} 个测试用例")

        if not self.tests:
            self._logger.warning("没有发现测试用例")
            return {"total_tests": 0, "message": "没有发现测试用例"}

        resolver = DependencyResolver()
        for test in self.tests:
            resolver.add_test(test.name, test.dependencies)

        execution_levels = resolver.resolve_order(self.tests)
        self._logger.info(f"测试执行分为 {len(execution_levels)} 个层级")

        all_results = []
        total_retries = 0
        retry_passed = 0
        
        for level_idx, level_tests in enumerate(execution_levels):
            self._logger.info(f"执行第 {level_idx + 1} 层级，共 {len(level_tests)} 个测试")

            if fail_fast and any(t.status == TestStatus.FAILED for t in all_results):
                for test in level_tests:
                    test.status = TestStatus.SKIPPED
                    test.error_message = "由于fail-fast模式，跳过后续测试"
                all_results.extend(level_tests)
                continue

            level_results = self.executor.execute_parallel(level_tests)
            
            for test in level_results:
                if enable_history and self.history_tracker:
                    self.history_tracker.record_test_run(test)
                
                if retry_count > 0 and test.status in [TestStatus.FAILED, TestStatus.ERROR]:
                    original_status = test.status
                    retried_test = self.retry_handler.execute_with_retry(test, self.executor)
                    if retried_test.status == TestStatus.PASSED:
                        total_retries += 1
                        retry_passed += 1
                    all_results.append(retried_test)
                else:
                    all_results.append(test)

            if enable_notify:
                for test in level_results:
                    if test.status == TestStatus.FAILED:
                        self.notification_handler.notify_failure(test, {"level": level_idx})

        self.result = self._aggregate_results(all_results)
        self.result.duration = (datetime.now() - start_time).total_seconds()
        self.result.retry_count = total_retries
        self.result.retry_passed = retry_passed

        if enable_coverage:
            collector = CoverageCollector(Path(source_dir))
            self.result.coverage_report = collector.collect_coverage(all_results)

        if enable_notify:
            self.notification_handler.notify_pipeline_complete(self.result)

        report_path = self.report_generator.generate_report(self.result, report_format)
        self._logger.info(f"测试报告已生成: {report_path}")

        self._report.add_section("执行结果", {
            "total_tests": self.result.total_tests,
            "passed": self.result.passed,
            "failed": self.result.failed,
            "skipped": self.result.skipped,
            "errors": self.result.errors,
            "duration": f"{self.result.duration:.2f}秒",
            "retry_count": total_retries,
            "retry_passed": retry_passed,
            "report_path": str(report_path)
        })

        if self.result.failed_tests:
            self._report.add_section("失败测试", self.result.failed_tests[:10])

        if enable_history and self.history_tracker:
            trends = self.history_tracker.get_test_trends()
            self._report.add_section("测试趋势", trends)
            
            if flaky_detection:
                flaky_tests = self.history_tracker.get_flaky_tests()
                if flaky_tests:
                    self._report.add_section("不稳定测试", flaky_tests)
                    self._logger.warning(f"检测到 {len(flaky_tests)} 个不稳定测试")

        return {
            "total_tests": self.result.total_tests,
            "passed": self.result.passed,
            "failed": self.result.failed,
            "skipped": self.result.skipped,
            "errors": self.result.errors,
            "duration": self.result.duration,
            "failed_tests": self.result.failed_tests,
            "coverage": self.result.coverage_report,
            "retry_count": total_retries,
            "retry_passed": retry_passed,
            "report_path": str(report_path)
        }

    def _aggregate_results(self, test_results: List[TestCase]) -> PipelineResult:
        result = PipelineResult()
        result.total_tests = len(test_results)

        for test in test_results:
            if test.status == TestStatus.PASSED:
                result.passed += 1
            elif test.status == TestStatus.FAILED:
                result.failed += 1
                result.failed_tests.append({
                    "name": test.name,
                    "file": test.file_path,
                    "error": test.error_message,
                    "duration": test.duration
                })
            elif test.status == TestStatus.SKIPPED:
                result.skipped += 1
            elif test.status == TestStatus.ERROR:
                result.errors += 1
                result.failed_tests.append({
                    "name": test.name,
                    "file": test.file_path,
                    "error": test.error_message,
                    "duration": test.duration
                })

        return result

    def cleanup(self) -> None:
        self._logger.info("清理测试流水线资源")


def main():
    orchestrator = TestPipelineOrchestrator()
    result = orchestrator.run_from_command_line()

    print("\n" + "=" * 60)
    print("测试流水线执行报告（增强版）")
    print("=" * 60)
    print(f"总测试数: {result.data.get('total_tests', 0)}")
    print(f"通过: {result.data.get('passed', 0)}")
    print(f"失败: {result.data.get('failed', 0)}")
    print(f"跳过: {result.data.get('skipped', 0)}")
    print(f"错误: {result.data.get('errors', 0)}")
    print(f"执行时长: {result.data.get('duration', 0):.2f}秒")
    
    retry_count = result.data.get('retry_count', 0)
    if retry_count > 0:
        print(f"\n重试统计:")
        print(f"  重试次数: {retry_count}")
        print(f"  重试后通过: {result.data.get('retry_passed', 0)}")
    
    report_path = result.data.get('report_path', '')
    if report_path:
        print(f"\n报告路径: {report_path}")

    if result.data.get('failed_tests'):
        print("\n失败测试:")
        for test in result.data.get('failed_tests', [])[:5]:
            print(f"  - {test['name']}: {test['error'][:50]}...")

    print("=" * 60)

    if result.status == ScriptStatus.SUCCESS and result.data.get('failed', 0) > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
