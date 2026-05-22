#!/usr/bin/env python3
"""
日志与测试关联器
实现日志与测试用例的关联分析，帮助定位测试失败原因

功能:
- 日志与测试用例关联分析
- 测试失败原因定位
- 问题诊断报告增强
- 根因分析与修复建议
"""

import re
import json
import os
import sys
import ast
import hashlib
import subprocess
import difflib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field, asdict
from collections import defaultdict, Counter
from enum import Enum
import logging


class TestStatus(Enum):
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"
    TIMEOUT = "timeout"


@dataclass
class LogPatternMatch:
    pattern_id: str
    pattern_regex: str
    description: str
    expected_in_test: bool
    actual_in_logs: bool
    confidence: float = 1.0
    test_file: str = ""
    test_line: int = 0
    log_line: int = 0
    context: str = ""
    matched_text: str = ""
    before_text: str = ""
    after_text: str = ""


@dataclass
class TestCaseInfo:
    test_id: str
    test_name: str
    test_file: str
    test_function: str = ""
    test_class: str = ""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_ms: float = 0.0
    status: TestStatus = TestStatus.PASSED
    error_message: str = ""
    error_type: str = ""
    stack_trace: str = ""
    related_logs: List[str] = field(default_factory=list)
    assertions: Dict[str, Any] = field(default_factory=dict)
    fixtures: List[str] = field(default_factory=list)
    setup_teardown: List[str] = field(default_factory=list)
    cleanup_functions: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    markers: List[str] = field(default_factory=list)
    skip_reason: str = ""
    retry_count: int = 0
    max_retries: int = 3
    flaky_threshold: float = 0.0
    is_flaky: bool = False
    priority: str = "medium"
    category: str = "unit"
    confidence: float = 0.5
    related_issues: List[str] = field(default_factory=list)
    fix_suggestions: List[str] = field(default_factory=list)
    diagnostic_steps: List[str] = field(default_factory=list)
    log_patterns: List[str] = field(default_factory=list)
    expected_log_patterns: List[str] = field(default_factory=list)
    actual_log_patterns: List[str] = field(default_factory=list)
    log_mismatch_score: float = 0.0
    root_cause_confidence: float = 0.0
    impact_analysis: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestFailureAnalysis:
    test_id: str
    test_name: str
    failure_type: str
    error_message: str
    stack_trace: str
    related_logs: List[str]
    root_cause: str = ""
    confidence: float = 0.5
    suggested_fixes: List[str] = field(default_factory=list)
    related_test_cases: List[str] = field(default_factory=list)
    log_patterns_matched: List[LogPatternMatch] = field(default_factory=list)
    diagnostic_info: Dict[str, Any] = field(default_factory=dict)
    timeline: Dict[str, Any] = field(default_factory=dict)
    environment_info: Dict[str, Any] = field(default_factory=dict)
    reproduction_steps: List[str] = field(default_factory=list)
    additional_artifacts: List[str] = field(default_factory=list)
    status: TestStatus = TestStatus.PASSED
    priority: str = "medium"
    category: str = "unit"
    duration_ms: float = 0.0
    impact_analysis: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LogTestCorrelationResult:
    test_id: str
    test_name: str
    correlation_score: float
    log_patterns: List[LogPatternMatch]
    root_cause: str
    confidence: float = 1.0
    suggested_fixes: List[str] = field(default_factory=list)
    timeline: Dict[str, Any] = field(default_factory=dict)
    additional_info: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CorrelationReport:
    timestamp: str
    total_tests: int
    total_failures: int
    correlations: List[LogTestCorrelationResult]
    summary: str
    recommendations: List[str]


class LogTestCorrelator:
    """日志与测试关联器 - 实现日志与测试用例的关联分析"""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.test_patterns = {
            "test_*.py": "unit",
            "test_*.spec.py": "integration",
            "*_test.py": "unit",
        }
        self.log_patterns = {"*.log", "*.json", "*.txt"}
        self.test_cache: Dict[str, TestCaseInfo] = {}
        self.log_cache: Dict[str, List[str]] = defaultdict(list)
        self.correlation_threshold = 0.7
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('LogTestCorrelator')
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger

    def discover_tests(self) -> List[str]:
        """发现测试文件"""
        tests = []
        for pattern in self.test_patterns:
            for test_file in self.project_root.rglob(pattern):
                if test_file.name.startswith('test_') or test_file.name.endswith('_test.py'):
                    tests.append(str(test_file))
        return tests

    def discover_logs(self) -> List[str]:
        """发现日志文件"""
        logs = []
        for pattern in self.log_patterns:
            for log_file in self.project_root.rglob(pattern):
                logs.append(str(log_file))
        return logs

    def load_test(self, test_file: str) -> Optional[TestCaseInfo]:
        """加载测试信息"""
        if test_file not in self.test_cache:
            try:
                with open(test_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                tree = ast.parse(content)
                test_info = TestCaseInfo(
                    test_id=self._extract_test_id(test_file),
                    test_name=self._extract_test_name(tree),
                    test_file=test_file,
                    test_function=self._extract_test_function(tree),
                    test_class=self._extract_test_class(tree),
                    start_time=datetime.now(),
                    status=TestStatus.PASSED
                )
                self.test_cache[test_file] = test_info
                return test_info
            except Exception as e:
                self.logger.error(f"加载测试失败 {test_file}: {e}")
                return None
        return self.test_cache[test_file]

    def load_log(self, log_file: str) -> List[str]:
        """加载日志内容"""
        try:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            return lines
        except Exception as e:
            self.logger.error(f"加载日志失败 {log_file}: {e}")
            return []

    def _extract_test_id(self, test_file: str) -> str:
        return hashlib.md5(test_file.encode()).hexdigest()[:12]

    def _extract_test_name(self, tree: ast.AST) -> str:
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if node.name.startswith('test_'):
                    return node.name
        return "unknown"

    def _extract_test_function(self, tree: ast.AST) -> str:
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if node.name.startswith('test_'):
                    return node.name
        return ""

    def _extract_test_class(self, tree: ast.AST) -> str:
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if node.name.lower().startswith('test') or 'Test' in node.name:
                    return node.name
        return ""

    def run_test(self, test_file: str) -> TestFailureAnalysis:
        """运行测试并分析失败"""
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pytest', test_file, '-v', '--tb=short', '-x'],
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode != 0:
                return self._analyze_test_failure(test_file, result.stdout, result.stderr)
            else:
                return TestFailureAnalysis(
                    test_id=self._extract_test_id(test_file),
                    test_name=Path(test_file).stem,
                    failure_type="passed",
                    error_message="",
                    stack_trace="",
                    related_logs=[],
                    status=TestStatus.PASSED
                )
        except subprocess.TimeoutExpired:
            return TestFailureAnalysis(
                test_id=self._extract_test_id(test_file),
                test_name=Path(test_file).stem,
                failure_type="timeout",
                error_message="Test execution timed out",
                stack_trace="",
                related_logs=[],
                status=TestStatus.TIMEOUT
            )
        except Exception as e:
            return TestFailureAnalysis(
                test_id=self._extract_test_id(test_file),
                test_name=Path(test_file).stem,
                failure_type="error",
                error_message=str(e),
                stack_trace="",
                related_logs=[],
                status=TestStatus.ERROR
            )

    def _analyze_test_failure(
        self,
        test_file: str,
        stdout: str,
        stderr: str
    ) -> TestFailureAnalysis:
        """分析测试失败"""
        error_lines = (stdout + "\n" + stderr).split('\n')
        error_message = ""
        stack_trace = ""
        failure_type = "unknown"

        for line in error_lines:
            if 'FAILED' in line or 'ERROR' in line or 'AssertionError' in line:
                error_message = line
                failure_type = self._classify_error(line)
            elif 'Traceback' in line:
                stack_trace_lines = []
                continue
            if 'stack_trace_lines' in locals():
                stack_trace_lines.append(line)

        if 'stack_trace_lines' in locals():
            stack_trace = '\n'.join(stack_trace_lines)

        root_cause = self._determine_root_cause(error_message, stack_trace)
        suggested_fixes = self._generate_fix_suggestions(error_message, failure_type)

        return TestFailureAnalysis(
            test_id=self._extract_test_id(test_file),
            test_name=Path(test_file).stem,
            failure_type=failure_type,
            error_message=error_message,
            stack_trace=stack_trace,
            related_logs=self._extract_related_logs(stack_trace),
            root_cause=root_cause,
            confidence=0.8,
            suggested_fixes=suggested_fixes
        )

    def _classify_error(self, line: str) -> str:
        if 'FAILED' in line:
            return "assertion"
        elif 'ERROR' in line:
            return "runtime_error"
        elif 'AssertionError' in line:
            return "assertion"
        return "unknown"

    def _determine_root_cause(self, error_message: str, stack_trace: str) -> str:
        error_lower = error_message.lower()
        if 'assertion' in error_lower:
            return "断言失败"
        elif 'not found' in error_lower:
            return "资源未找到"
        elif 'import' in error_lower:
            return "导入错误"
        elif 'connection' in error_lower:
            return "连接错误"
        elif 'timeout' in error_lower:
            return "超时错误"
        elif 'permission' in error_lower:
            return "权限错误"
        elif 'file' in error_lower:
            return "文件错误"
        return "未知错误"

    def _generate_fix_suggestions(self, error_message: str, failure_type: str) -> List[str]:
        suggestions = []
        if failure_type == "assertion":
            suggestions.append("检查断言条件或测试数据")
        elif failure_type == "runtime_error":
            suggestions.append("检查异常处理逻辑或添加缺失的异常处理")
        elif failure_type == "import_error":
            suggestions.append("检查导入路径或安装缺失的依赖")
        elif failure_type == "connection_error":
            suggestions.append("检查网络配置或服务状态")
        elif failure_type == "timeout_error":
            suggestions.append("增加超时时间或优化性能")
        elif failure_type == "permission_error":
            suggestions.append("检查文件权限或运行身份")
        elif failure_type == "file_error":
            suggestions.append("检查文件路径或创建缺失文件")
        return suggestions

    def _extract_related_logs(self, stack_trace: str) -> List[str]:
        """从堆栈跟踪提取相关日志"""
        log_files = []
        for line in stack_trace.split('\n'):
            if line.strip().endswith('.log') or line.strip().endswith('.json'):
                log_files.append(line.strip())
        return log_files

    def correlate(self, test_file: str) -> Optional[LogTestCorrelationResult]:
        """关联测试与日志"""
        test_info = self.test_cache.get(test_file)
        if not test_info:
            test_info = self.load_test(test_file)
        if not test_info:
            return None

        logs = self.discover_logs()
        if not logs:
            return None

        test_logs = []
        for log_file in logs:
            log_lines = self.load_log(log_file)
            test_logs.extend(log_lines)

        log_patterns = self._extract_log_patterns(test_logs)
        expected_patterns = self._extract_expected_log_patterns(test_info)
        matches = self._find_pattern_matches(log_patterns, expected_patterns)

        correlation_score = self._calculate_correlation_score(matches)
        root_cause = self._determine_root_cause_from_matches(matches)
        suggested_fixes = self._generate_fix_suggestions_from_matches(matches)

        return LogTestCorrelationResult(
            test_id=test_info.test_id,
            test_name=test_info.test_name,
            correlation_score=correlation_score,
            log_patterns=matches,
            root_cause=root_cause,
            confidence=0.8,
            suggested_fixes=suggested_fixes,
            timeline={
                "test_start": test_info.start_time.isoformat() if test_info.start_time else None,
                "test_end": test_info.end_time.isoformat() if test_info.end_time else None,
                "duration_ms": test_info.duration_ms,
            }
        )

    def _extract_log_patterns(self, log_lines: List[str]) -> List[str]:
        """从日志行提取模式"""
        patterns = []
        log_pattern = re.compile(
            r'(\d{4}-\d{2}-\d{2}|\d{2}:\d{2}:\d{2}|ERROR|WARNING|INFO|DEBUG|CRITICAL|Exception|Error|Traceback|Failed|SUCCESS)',
            re.IGNORECASE
        )
        for line in log_lines:
            match = log_pattern.search(line)
            if match:
                patterns.append(line.strip())
        return patterns

    def _extract_expected_log_patterns(self, test_info: TestCaseInfo) -> List[str]:
        """提取预期的日志模式"""
        expected = []
        if test_info.test_function:
            expected.append(f"test_function: {test_info.test_function}")
        if test_info.test_class:
            expected.append(f"test_class: {test_info.test_class}")
        expected.append("Test started")
        expected.append("Test passed" if test_info.status == TestStatus.PASSED else "Test failed")
        return expected

    def _find_pattern_matches(
        self,
        log_patterns: List[str],
        expected_patterns: List[str]
    ) -> List[LogPatternMatch]:
        """查找模式匹配"""
        matches = []
        for log_pattern in log_patterns:
            for expected in expected_patterns:
                if expected.lower() in log_pattern.lower():
                    similarity = difflib.SequenceMatcher(
                        None, expected.lower(), log_pattern.lower()
                    ).ratio()
                    if similarity > self.correlation_threshold:
                        matches.append(LogPatternMatch(
                            pattern_id=hashlib.md5(
                                f"{expected}_{log_pattern}".encode()
                            ).hexdigest()[:8],
                            pattern_regex=expected,
                            description=f"Expected: {expected}, Actual: {log_pattern[:50]}...",
                            expected_in_test=True,
                            actual_in_logs=True,
                            confidence=similarity,
                            matched_text=log_pattern[:50],
                        ))
        return matches

    def _calculate_correlation_score(self, matches: List[LogPatternMatch]) -> float:
        """计算关联分数"""
        if not matches:
            return 0.0
        return sum(m.confidence for m in matches) / len(matches)

    def _determine_root_cause_from_matches(self, matches: List[LogPatternMatch]) -> str:
        """从匹配确定根因"""
        if not matches:
            return "Unknown error"
        high_confidence_matches = [m for m in matches if m.confidence > 0.8]
        if high_confidence_matches:
            return high_confidence_matches[0].description
        return matches[0].description

    def _generate_fix_suggestions_from_matches(self, matches: List[LogPatternMatch]) -> List[str]:
        """从匹配生成修复建议"""
        suggestions = []
        for match in matches:
            if match.confidence > 0.8:
                suggestions.append(f"High confidence match: {match.pattern_regex}")
        if not suggestions:
            suggestions.append("Review test logs for more details")
        return suggestions

    def analyze_project(self) -> CorrelationReport:
        """分析整个项目"""
        results = []
        tests = self.discover_tests()
        for test_file in tests:
            result = self.correlate(test_file)
            if result:
                results.append(result)
        return CorrelationReport(
            timestamp=datetime.now().isoformat(),
            total_tests=len(tests),
            total_failures=sum(1 for r in results if r.correlation_score < 0.5),
            correlations=results,
            summary=self._generate_summary(results),
            recommendations=self._generate_recommendations(results)
        )

    def _generate_summary(self, results: List[LogTestCorrelationResult]) -> str:
        """生成摘要"""
        if not results:
            return "No test failures found"
        high_correlation = [r for r in results if r.correlation_score > 0.8]
        if high_correlation:
            return f"Found {len(high_correlation)} tests with high correlation to logs"
        return f"Analyzed {len(results)} tests, {sum(1 for r in results if r.correlation_score > 0.5)} with potential issues"

    def _generate_recommendations(self, results: List[LogTestCorrelationResult]) -> List[str]:
        """生成建议"""
        recommendations = []
        for result in results:
            if result.correlation_score > 0.8:
                recommendations.append(f"Investigate {result.test_name}: {result.root_cause}")
        if not recommendations:
            recommendations.append("All tests passed or low correlation with logs")
        return recommendations

    def generate_report(
        self,
        results: List[LogTestCorrelationResult],
        output_format: str = "markdown"
    ) -> str:
        """生成报告"""
        if output_format == "json":
            return self._generate_json_report(results)
        return self._generate_markdown_report(results)

    def _generate_markdown_report(self, results: List[LogTestCorrelationResult]) -> str:
        """生成Markdown报告"""
        lines = [
            "# 日志与测试关联分析报告",
            f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"\n## 概览",
            f"- 分析测试数: {len(results)}",
            f"- 高关联测试数: {sum(1 for r in results if r.correlation_score > 0.8)}",
            "",
        ]
        for result in results:
            lines.extend([
                f"\n### {result.test_name}",
                f"- 关联分数: {result.correlation_score:.2%}",
                f"- 根因: {result.root_cause}",
                f"- 置信度: {result.confidence:.0%}",
                "",
            ])
            if result.log_patterns:
                lines.extend(["\n**日志模式匹配**:", ""])
                for match in result.log_patterns:
                    lines.append(f"- {match.description} (置信度: {match.confidence:.0%})")
            if result.suggested_fixes:
                lines.extend(["\n**修复建议**:", ""])
                for fix in result.suggested_fixes:
                    lines.append(f"- {fix}")
        return '\n'.join(lines)

    def _generate_json_report(self, results: List[LogTestCorrelationResult]) -> str:
        """生成JSON报告"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_tests": len(results),
            "high_correlation_tests": sum(1 for r in results if r.correlation_score > 0.8),
            "results": [
                {
                    "test_id": r.test_id,
                    "test_name": r.test_name,
                    "correlation_score": r.correlation_score,
                    "root_cause": r.root_cause,
                    "confidence": r.confidence,
                    "log_patterns": [
                        {
                            "pattern_id": m.pattern_id,
                            "description": m.description,
                            "confidence": m.confidence
                        }
                        for m in r.log_patterns
                    ],
                    "suggested_fixes": r.suggested_fixes
                }
                for r in results
            ]
        }
        return json.dumps(report, indent=2, ensure_ascii=False)

    def diagnose_failure(
        self,
        test_file: str,
        log_files: Optional[List[str]] = None
    ) -> TestFailureAnalysis:
        """诊断失败"""
        test_info = self.test_cache.get(test_file)
        if not test_info:
            test_info = self.load_test(test_file)
        if not test_info:
            return TestFailureAnalysis(
                test_id="unknown",
                test_name="unknown",
                failure_type="unknown",
                error_message="Test not found in cache",
                stack_trace="",
                related_logs=[]
            )

        logs = log_files or self.discover_logs()
        test_logs = []
        for log_file in logs:
            test_logs.extend(self.load_log(log_file))

        failure_analysis = self.run_test(test_file)
        log_patterns = self._extract_log_patterns(test_logs)
        expected_patterns = self._extract_expected_log_patterns(test_info)
        matches = self._find_pattern_matches(log_patterns, expected_patterns)

        failure_analysis.log_patterns_matched = matches
        failure_analysis.root_cause = self._determine_root_cause_from_matches(matches)
        failure_analysis.confidence = self._calculate_correlation_score(matches)
        failure_analysis.suggested_fixes = self._generate_fix_suggestions_from_matches(matches)
        failure_analysis.related_logs = test_logs
        failure_analysis.timeline = {
            "test_start": test_info.start_time.isoformat() if test_info.start_time else None,
            "test_end": test_info.end_time.isoformat() if test_info.end_time else None,
            "duration_ms": test_info.duration_ms,
        }
        return failure_analysis

    def get_diagnostic_report(
        self,
        test_file: str,
        output_format: str = "markdown"
    ) -> str:
        """获取诊断报告"""
        failure = self.diagnose_failure(test_file)
        if output_format == "json":
            return json.dumps(asdict(failure), indent=2, ensure_ascii=False, default=str)
        return self._generate_diagnostic_markdown(failure)

    def _generate_diagnostic_markdown(self, failure: TestFailureAnalysis) -> str:
        """生成诊断Markdown报告"""
        lines = [
            "# 测试失败诊断报告",
            f"\n测试: {failure.test_name}",
            f"时间: {failure.timeline.get('test_start', '未知')}",
            f"\n## 概览",
            f"- 失败类型: {failure.failure_type}",
            f"- 置信度: {failure.confidence:.0%}",
            f"- 根因: {failure.root_cause}",
            "",
            f"\n## 错误信息",
            f"```\n{failure.error_message}\n```",
            "",
            f"\n## 堆栈跟踪",
            f"```\n{failure.stack_trace}\n```",
            "",
        ]
        if failure.log_patterns_matched:
            lines.extend([f"\n## 日志模式匹配", ""])
            for match in failure.log_patterns_matched:
                lines.append(f"- {match.description} (置信度: {match.confidence:.0%})")
        if failure.suggested_fixes:
            lines.extend([f"\n## 修复建议", ""])
            for fix in failure.suggested_fixes:
                lines.append(f"- {fix}")
        return '\n'.join(lines)

    def clear_cache(self):
        """清除缓存"""
        self.test_cache.clear()
        self.log_cache.clear()

    def get_test_info(self, test_file: str) -> Optional[TestCaseInfo]:
        """获取测试信息"""
        return self.test_cache.get(test_file)

    def get_all_tests(self) -> List[TestCaseInfo]:
        """获取所有测试信息"""
        return list(self.test_cache.values())

    def get_all_failures(self) -> List[TestFailureAnalysis]:
        """获取所有失败信息"""
        failures = []
        for test_info in self.test_cache.values():
            failure = self.diagnose_failure(test_info.test_file)
            failures.append(failure)
        return failures

    def get_correlation_summary(self) -> Dict[str, Any]:
        """获取关联摘要"""
        summary = {
            "total_tests": len(self.test_cache),
            "tests_with_issues": 0,
            "high_correlation_tests": [],
        }
        for test_file in self.test_cache:
            result = self.correlate(test_file)
            if result and result.correlation_score > 0.7:
                summary["tests_with_issues"] += 1
                summary["high_correlation_tests"].append({
                    "test": test_file,
                    "correlation": result.correlation_score,
                    "root_cause": result.root_cause
                })
        return summary

    def export_results(
        self,
        output_path: str,
        format: str = "json"
    ) -> str:
        """导出结果"""
        results = self.analyze_project()
        if format == "json":
            data = json.dumps(asdict(results), indent=2, ensure_ascii=False, default=str)
        else:
            data = self._generate_markdown_report(results.correlations)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(data)
        return output_path


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="日志与测试关联分析工具")
    parser.add_argument("--project-root", default=".", help="项目根目录")
    parser.add_argument("--output", default="correlation_report.md", help="输出文件路径")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown", help="输出格式")
    args = parser.parse_args()

    correlator = LogTestCorrelator(args.project_root)
    report = correlator.analyze_project()
    correlator.export_results(args.output, args.format)
    print(f"报告已生成: {args.output}")
