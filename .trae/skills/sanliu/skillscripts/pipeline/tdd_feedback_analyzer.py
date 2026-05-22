#!/usr/bin/env python3
"""
TDD结果分析器 (TDD Feedback Analyzer)

实现测试驱动开发(TDD)结果的分析与反馈机制，是SDD-TDD闭环流程的核心组件。

主要功能模块：
====================

1. 测试结果分析功能 (TestResultParser + FailureAnalyzer)
   - 解析多种测试框架结果格式 (pytest, unittest, jest)
   - 智能失败原因分析和分类
   - 深度分析测试失败结果
   - 失败模式识别和根因链分析
   - 影响范围评估和历史趋势分析

2. 测试结果到规范的反馈机制 (FeedbackGenerator)
   - 根据测试结果反馈规范问题
   - 智能反馈生成和优先级排序
   - 规范元素映射和影响分析
   - 修复建议生成和规范更新提示

3. 规范改进建议生成 (SpecImprovementSuggester)
   - 基于测试结果生成规范改进建议
   - 智能建议分类和影响评估
   - 实施优先级排序和风险评估
   - 实施路径建议生成

4. 规范与代码同步验证 (SpecCodeSyncValidator)
   - 验证规范与实现代码的一致性
   - 语义一致性分析
   - 行为一致性验证
   - 变更影响分析和修复建议生成

5. 覆盖率与规范对应关系分析 (CoverageSpecAnalyzer)
   - 分析测试覆盖率与规范的映射
   - 识别规范中未被测试覆盖的场景

增强功能：
====================
- analyze_failures_deeply(): 深度分析测试失败结果
- generate_intelligent_feedback(): 生成智能反馈到SDD规范
- generate_enhanced_suggestions(): 生成增强的规范改进建议
- validate_sync_comprehensive(): 执行全面的规范与代码同步验证

核心数据结构：
====================
- TestResult: 测试结果数据
- FailureAnalysis: 失败分析结果
- FeedbackItem: 反馈项
- SpecImprovementSuggestion: 规范改进建议
- SyncReport: 同步报告
- AnalysisReport: 分析报告

用法示例：
====================
    # 分析测试结果
    python tdd_feedback_analyzer.py analyze --test-results <测试结果文件>
    
    # 生成规范反馈
    python tdd_feedback_analyzer.py feedback --test-results <测试结果文件> --spec <规范文件>
    
    # 生成改进建议
    python tdd_feedback_analyzer.py suggest --test-results <测试结果文件> --spec <规范文件>
    
    # 验证规范与代码同步
    python tdd_feedback_analyzer.py sync --spec <规范文件> --code <代码目录>
    
    # 分析覆盖率与规范映射
    python tdd_feedback_analyzer.py coverage --test-results <测试结果文件> --spec <规范文件> --coverage <覆盖率报告>
    
    # 识别未覆盖场景
    python tdd_feedback_analyzer.py uncover --spec <规范文件> --coverage <覆盖率报告>

作者: TDD Feedback Analyzer Team
版本: 2.0.0
"""

import argparse
import ast
import json
import logging
import re
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import hashlib


class TestStatus(Enum):
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"
    XFAILED = "xfailed"
    XPASSED = "xpassed"


class FailureCategory(Enum):
    ASSERTION = "assertion"
    EXCEPTION = "exception"
    TIMEOUT = "timeout"
    IMPORT = "import"
    ATTRIBUTE = "attribute"
    TYPE = "type"
    VALUE = "value"
    KEY = "key"
    INDEX = "index"
    SYNTAX = "syntax"
    UNKNOWN = "unknown"


class FeedbackSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class SyncStatus(Enum):
    IN_SYNC = "in_sync"
    OUT_OF_SYNC = "out_of_sync"
    PARTIAL = "partial"
    UNKNOWN = "unknown"


class SuggestionType(Enum):
    SPEC_UPDATE = "spec_update"
    SPEC_ADDITION = "spec_addition"
    SPEC_REMOVAL = "spec_removal"
    SPEC_CLARIFICATION = "spec_clarification"
    CODE_FIX = "code_fix"
    TEST_FIX = "test_fix"


class TestStability(Enum):
    STABLE = "stable"
    FLAKY = "flaky"
    INTERMITTENT = "intermittent"
    UNKNOWN = "unknown"


class ImpactLevel(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    MINIMAL = "minimal"


@dataclass
class TestResult:
    test_id: str
    test_name: str
    status: TestStatus
    duration: float = 0.0
    message: str = ""
    traceback: str = ""
    file_path: str = ""
    line_number: int = 0
    markers: List[str] = field(default_factory=list)
    is_slow: bool = False
    retry_count: int = 0
    flaky_score: float = 0.0
    stability: TestStability = TestStability.UNKNOWN
    spec_references: List[str] = field(default_factory=list)


@dataclass
class TestExecutionStats:
    total_tests: int
    passed: int
    failed: int
    skipped: int
    errors: int
    xpassed: int
    xfailed: int
    pass_rate: float
    failure_rate: float
    skip_rate: float
    error_rate: float
    total_duration: float
    avg_duration: float
    max_duration: float
    min_duration: float
    slow_tests_count: int
    slow_threshold: float
    stability_score: float
    flaky_tests_count: int


@dataclass
class SlowTestInfo:
    test_id: str
    test_name: str
    duration: float
    file_path: str
    line_number: int
    suggested_optimization: str
    impact: str


@dataclass
class TestStabilityInfo:
    test_id: str
    test_name: str
    stability: TestStability
    flaky_score: float
    pass_fail_ratio: float
    historical_runs: int
    suggested_action: str


@dataclass
class FailureAnalysis:
    failure_id: str
    test_id: str
    category: FailureCategory
    root_cause: str
    error_message: str
    suggested_fix: str
    related_spec_element: str = ""
    confidence: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)
    impact_level: ImpactLevel = ImpactLevel.MEDIUM
    affected_components: List[str] = field(default_factory=list)
    fix_complexity: str = "medium"
    estimated_fix_time: str = "unknown"
    related_failures: List[str] = field(default_factory=list)
    code_snippet: str = ""
    assertion_details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FeedbackItem:
    feedback_id: str
    spec_element_id: str
    spec_element_name: str
    feedback_type: str
    severity: FeedbackSeverity
    message: str
    test_ids: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    impact: str = ""
    priority_score: float = 0.0
    impact_level: ImpactLevel = ImpactLevel.MEDIUM
    affected_spec_elements: List[str] = field(default_factory=list)
    code_locations: List[Dict[str, Any]] = field(default_factory=list)
    historical_context: Dict[str, Any] = field(default_factory=dict)
    auto_fix_available: bool = False
    auto_fix_suggestion: str = ""


@dataclass
class SpecImprovementSuggestion:
    suggestion_id: str
    suggestion_type: SuggestionType
    spec_element: str
    current_value: str
    suggested_value: str
    reason: str
    priority: int = 0
    test_evidence: List[str] = field(default_factory=list)
    context_aware: bool = False
    related_suggestions: List[str] = field(default_factory=list)
    implementation_hints: List[str] = field(default_factory=list)
    risk_assessment: str = "low"
    dependencies: List[str] = field(default_factory=list)
    auto_applicable: bool = False
    confidence_score: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SyncIssue:
    issue_id: str
    issue_type: str
    spec_element: str
    code_element: str
    description: str
    severity: FeedbackSeverity
    suggestion: str = ""
    spec_location: Dict[str, Any] = field(default_factory=dict)
    code_location: Dict[str, Any] = field(default_factory=dict)
    parameter_mismatch: Dict[str, Any] = field(default_factory=dict)
    return_type_mismatch: Dict[str, Any] = field(default_factory=dict)
    doc_mismatch: Dict[str, Any] = field(default_factory=dict)
    auto_fix_available: bool = False
    auto_fix_details: str = ""


@dataclass
class SyncReport:
    report_id: str
    spec_id: str
    status: SyncStatus
    sync_percentage: float
    issues: List[SyncIssue] = field(default_factory=list)
    checked_elements: int = 0
    matched_elements: int = 0
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class AnalysisReport:
    report_id: str
    generated_at: str
    total_tests: int
    passed: int
    failed: int
    skipped: int
    errors: int
    pass_rate: float
    failure_analyses: List[FailureAnalysis] = field(default_factory=list)
    feedback_items: List[FeedbackItem] = field(default_factory=list)
    improvement_suggestions: List[SpecImprovementSuggestion] = field(default_factory=list)
    sync_report: Optional[SyncReport] = None
    summary: Dict[str, Any] = field(default_factory=dict)


class TestResultParser:
    """测试结果解析器"""
    
    SLOW_TEST_THRESHOLD = 5.0
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or self._setup_logger()
        self._historical_results: Dict[str, List[TestResult]] = {}
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger("TestResultParser")
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def parse_file(self, file_path: str) -> List[TestResult]:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"测试结果文件不存在: {file_path}")
        
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        
        suffix = path.suffix.lower()
        if suffix == ".json":
            results = self._parse_json_result(content)
        elif suffix == ".xml":
            results = self._parse_junit_xml(content)
        elif suffix in [".txt", ".log"]:
            results = self._parse_text_result(content)
        else:
            results = self._parse_json_result(content)
        
        results = self._enrich_test_results(results)
        self._update_historical_results(results)
        return results
    
    def parse_with_history(
        self, 
        file_path: str, 
        historical_files: Optional[List[str]] = None
    ) -> Tuple[List[TestResult], Dict[str, TestStabilityInfo]]:
        current_results = self.parse_file(file_path)
        
        if historical_files:
            for hist_file in historical_files:
                try:
                    hist_results = self.parse_file(hist_file)
                    self._update_historical_results(hist_results)
                except Exception as e:
                    self.logger.warning(f"无法加载历史结果 {hist_file}: {e}")
        
        stability_info = self._calculate_stability_info(current_results)
        return current_results, stability_info
    
    def calculate_execution_stats(
        self, 
        test_results: List[TestResult],
        slow_threshold: float = None
    ) -> TestExecutionStats:
        if slow_threshold is None:
            slow_threshold = self.SLOW_TEST_THRESHOLD
        
        total = len(test_results)
        if total == 0:
            return TestExecutionStats(
                total_tests=0, passed=0, failed=0, skipped=0, errors=0,
                xpassed=0, xfailed=0, pass_rate=0.0, failure_rate=0.0,
                skip_rate=0.0, error_rate=0.0, total_duration=0.0,
                avg_duration=0.0, max_duration=0.0, min_duration=0.0,
                slow_tests_count=0, slow_threshold=slow_threshold,
                stability_score=0.0, flaky_tests_count=0
            )
        
        passed = len([t for t in test_results if t.status == TestStatus.PASSED])
        failed = len([t for t in test_results if t.status == TestStatus.FAILED])
        skipped = len([t for t in test_results if t.status == TestStatus.SKIPPED])
        errors = len([t for t in test_results if t.status == TestStatus.ERROR])
        xpassed = len([t for t in test_results if t.status == TestStatus.XPASSED])
        xfailed = len([t for t in test_results if t.status == TestStatus.XFAILED])
        
        durations = [t.duration for t in test_results if t.duration > 0]
        total_duration = sum(durations) if durations else 0
        avg_duration = total_duration / len(durations) if durations else 0
        max_duration = max(durations) if durations else 0
        min_duration = min(durations) if durations else 0
        
        slow_tests = [t for t in test_results if t.duration > slow_threshold]
        slow_tests_count = len(slow_tests)
        
        flaky_tests = [t for t in test_results if t.stability == TestStability.FLAKY]
        flaky_tests_count = len(flaky_tests)
        
        stable_tests = [t for t in test_results if t.stability == TestStability.STABLE]
        stability_score = len(stable_tests) / total * 100 if total > 0 else 0
        
        return TestExecutionStats(
            total_tests=total,
            passed=passed,
            failed=failed,
            skipped=skipped,
            errors=errors,
            xpassed=xpassed,
            xfailed=xfailed,
            pass_rate=passed / total * 100,
            failure_rate=failed / total * 100,
            skip_rate=skipped / total * 100,
            error_rate=errors / total * 100,
            total_duration=total_duration,
            avg_duration=avg_duration,
            max_duration=max_duration,
            min_duration=min_duration,
            slow_tests_count=slow_tests_count,
            slow_threshold=slow_threshold,
            stability_score=stability_score,
            flaky_tests_count=flaky_tests_count
        )
    
    def identify_slow_tests(
        self, 
        test_results: List[TestResult],
        threshold: float = None,
        percentile_threshold: float = None
    ) -> List[SlowTestInfo]:
        if threshold is None:
            threshold = self.SLOW_TEST_THRESHOLD
        
        if percentile_threshold is not None:
            durations = sorted([t.duration for t in test_results if t.duration > 0])
            if durations:
                idx = int(len(durations) * percentile_threshold / 100)
                threshold = durations[min(idx, len(durations) - 1)]
        
        slow_tests = []
        for test in test_results:
            if test.duration > threshold:
                optimization = self._suggest_optimization(test)
                impact = self._assess_slow_test_impact(test, test_results)
                
                slow_tests.append(SlowTestInfo(
                    test_id=test.test_id,
                    test_name=test.test_name,
                    duration=test.duration,
                    file_path=test.file_path,
                    line_number=test.line_number,
                    suggested_optimization=optimization,
                    impact=impact
                ))
        
        slow_tests.sort(key=lambda x: x.duration, reverse=True)
        return slow_tests
    
    def _enrich_test_results(self, results: List[TestResult]) -> List[TestResult]:
        for result in results:
            result.is_slow = result.duration > self.SLOW_TEST_THRESHOLD
            result.spec_references = self._extract_spec_references(result)
            result.stability = self._determine_stability(result)
        
        return results
    
    def _extract_spec_references(self, test: TestResult) -> List[str]:
        references = []
        test_name = test.test_name.lower()
        
        patterns = [
            r"test_(\w+)",
            r"should_(\w+)",
            r"when_(\w+)",
            r"given_(\w+)",
            r"(\w+)_scenario",
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, test_name)
            references.extend(matches)
        
        if test.markers:
            for marker in test.markers:
                if marker.startswith("spec:"):
                    references.append(marker[5:])
        
        return list(set(references))
    
    def _determine_stability(self, test: TestResult) -> TestStability:
        test_id = test.test_id
        if test_id not in self._historical_results:
            return TestStability.UNKNOWN
        
        history = self._historical_results[test_id]
        if len(history) < 3:
            return TestStability.UNKNOWN
        
        statuses = [h.status for h in history[-5:]]
        status_changes = sum(1 for i in range(1, len(statuses)) if statuses[i] != statuses[i-1])
        
        if status_changes >= 2:
            return TestStability.FLAKY
        elif status_changes == 1:
            return TestStability.INTERMITTENT
        else:
            return TestStability.STABLE
    
    def _update_historical_results(self, results: List[TestResult]) -> None:
        for result in results:
            if result.test_id not in self._historical_results:
                self._historical_results[result.test_id] = []
            self._historical_results[result.test_id].append(result)
            
            if len(self._historical_results[result.test_id]) > 20:
                self._historical_results[result.test_id] = \
                    self._historical_results[result.test_id][-20:]
    
    def _calculate_stability_info(
        self, 
        results: List[TestResult]
    ) -> Dict[str, TestStabilityInfo]:
        stability_info = {}
        
        for test in results:
            test_id = test.test_id
            history = self._historical_results.get(test_id, [])
            
            if len(history) < 2:
                continue
            
            passes = sum(1 for h in history if h.status == TestStatus.PASSED)
            failures = sum(1 for h in history if h.status in [TestStatus.FAILED, TestStatus.ERROR])
            
            pass_fail_ratio = passes / max(failures, 1)
            
            flaky_score = self._calculate_flaky_score(history)
            
            if flaky_score > 0.5:
                stability = TestStability.FLAKY
                action = "建议调查测试不稳定原因，考虑重写或隔离测试"
            elif flaky_score > 0.2:
                stability = TestStability.INTERMITTENT
                action = "测试存在间歇性失败，建议监控并收集更多信息"
            else:
                stability = TestStability.STABLE
                action = "测试稳定，无需特别处理"
            
            stability_info[test_id] = TestStabilityInfo(
                test_id=test_id,
                test_name=test.test_name,
                stability=stability,
                flaky_score=flaky_score,
                pass_fail_ratio=pass_fail_ratio,
                historical_runs=len(history),
                suggested_action=action
            )
        
        return stability_info
    
    def _calculate_flaky_score(self, history: List[TestResult]) -> float:
        if len(history) < 2:
            return 0.0
        
        statuses = [h.status for h in history]
        changes = sum(1 for i in range(1, len(statuses)) 
                     if statuses[i] != statuses[i-1])
        
        return changes / (len(statuses) - 1)
    
    def _suggest_optimization(self, test: TestResult) -> str:
        suggestions = []
        
        if test.duration > 30:
            suggestions.append("考虑拆分测试为多个更小的测试")
            suggestions.append("检查是否存在不必要的等待或延迟")
        
        if test.duration > 10:
            suggestions.append("检查测试数据准备是否可以优化")
            suggestions.append("考虑使用mock替代真实依赖")
        
        if "integration" in test.test_name.lower():
            suggestions.append("集成测试可能较慢，考虑使用测试容器或内存数据库")
        
        if "e2e" in test.test_name.lower():
            suggestions.append("E2E测试通常较慢，考虑减少测试场景或并行执行")
        
        return "; ".join(suggestions) if suggestions else "检查测试实现以识别性能瓶颈"
    
    def _assess_slow_test_impact(
        self, 
        test: TestResult, 
        all_results: List[TestResult]
    ) -> str:
        total_duration = sum(r.duration for r in all_results)
        test_percentage = test.duration / total_duration * 100 if total_duration > 0 else 0
        
        if test_percentage > 20:
            return f"严重影响：该测试占总执行时间的 {test_percentage:.1f}%"
        elif test_percentage > 10:
            return f"中等影响：该测试占总执行时间的 {test_percentage:.1f}%"
        elif test_percentage > 5:
            return f"轻微影响：该测试占总执行时间的 {test_percentage:.1f}%"
        else:
            return "影响较小"
    
    def _parse_json_result(self, content: str) -> List[TestResult]:
        results = []
        data = json.loads(content)
        
        if "tests" in data:
            for test_data in data["tests"]:
                results.append(self._parse_test_data(test_data))
        elif "testcases" in data:
            for test_data in data["testcases"]:
                results.append(self._parse_test_data(test_data))
        elif isinstance(data, list):
            for test_data in data:
                results.append(self._parse_test_data(test_data))
        
        return results
    
    def _parse_test_data(self, data: Dict[str, Any]) -> TestResult:
        status_str = data.get("status", data.get("outcome", "unknown")).lower()
        status = self._map_status(status_str)
        
        return TestResult(
            test_id=data.get("test_id", data.get("id", data.get("nodeid", ""))),
            test_name=data.get("name", data.get("test_name", data.get("description", ""))),
            status=status,
            duration=data.get("duration", data.get("time", 0.0)),
            message=data.get("message", data.get("failure_message", "")),
            traceback=data.get("traceback", data.get("stack_trace", "")),
            file_path=data.get("file", data.get("file_path", "")),
            line_number=data.get("line", data.get("line_number", 0)),
            markers=data.get("markers", [])
        )
    
    def _parse_junit_xml(self, content: str) -> List[TestResult]:
        results = []
        
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(content)
            
            for testcase in root.iter("testcase"):
                name = testcase.get("name", "")
                classname = testcase.get("classname", "")
                time = float(testcase.get("time", 0))
                
                status = TestStatus.PASSED
                message = ""
                traceback = ""
                
                failure = testcase.find("failure")
                if failure is not None:
                    status = TestStatus.FAILED
                    message = failure.get("message", "")
                    traceback = failure.text or ""
                
                error = testcase.find("error")
                if error is not None:
                    status = TestStatus.ERROR
                    message = error.get("message", "")
                    traceback = error.text or ""
                
                skipped = testcase.find("skipped")
                if skipped is not None:
                    status = TestStatus.SKIPPED
                    message = skipped.get("message", "")
                
                results.append(TestResult(
                    test_id=f"{classname}.{name}",
                    test_name=name,
                    status=status,
                    duration=time,
                    message=message,
                    traceback=traceback,
                    file_path=classname.replace(".", "/") + ".py"
                ))
        except Exception as e:
            self.logger.error(f"解析JUnit XML失败: {e}")
        
        return results
    
    def _parse_text_result(self, content: str) -> List[TestResult]:
        results = []
        
        test_pattern = r"(PASSED|FAILED|ERROR|SKIPPED)\s+(.+?)(?:\s+\((.+?)\))?$"
        
        for line in content.split("\n"):
            match = re.search(test_pattern, line)
            if match:
                status_str = match.group(1)
                test_name = match.group(2).strip()
                duration_str = match.group(3) or "0"
                
                duration = 0.0
                if duration_str:
                    try:
                        duration = float(duration_str.replace("s", ""))
                    except ValueError:
                        pass
                
                results.append(TestResult(
                    test_id=test_name,
                    test_name=test_name,
                    status=self._map_status(status_str),
                    duration=duration
                ))
        
        return results
    
    def _map_status(self, status_str: str) -> TestStatus:
        mapping = {
            "passed": TestStatus.PASSED,
            "pass": TestStatus.PASSED,
            "ok": TestStatus.PASSED,
            "success": TestStatus.PASSED,
            "failed": TestStatus.FAILED,
            "fail": TestStatus.FAILED,
            "failure": TestStatus.FAILED,
            "error": TestStatus.ERROR,
            "skipped": TestStatus.SKIPPED,
            "skip": TestStatus.SKIPPED,
            "xfailed": TestStatus.XFAILED,
            "xfail": TestStatus.XFAILED,
            "xpassed": TestStatus.XPASSED,
            "xpass": TestStatus.XPASSED,
        }
        return mapping.get(status_str.lower(), TestStatus.ERROR)


class FailureAnalyzer:
    """测试失败分析器"""
    
    FAILURE_PATTERNS = {
        FailureCategory.ASSERTION: [
            r"AssertionError",
            r"assert\s+",
            r"Expected\s+",
            r"but\s+got\s+",
        ],
        FailureCategory.EXCEPTION: [
            r"Exception",
            r"Error:",
            r"Traceback\s+\(most\s+recent\s+call\s+last\)",
        ],
        FailureCategory.TIMEOUT: [
            r"TimeoutError",
            r"timed\s+out",
            r"TimeoutExpired",
        ],
        FailureCategory.IMPORT: [
            r"ImportError",
            r"ModuleNotFoundError",
            r"No\s+module\s+named",
        ],
        FailureCategory.ATTRIBUTE: [
            r"AttributeError",
            r"has\s+no\s+attribute",
            r"object\s+has\s+no\s+attribute",
        ],
        FailureCategory.TYPE: [
            r"TypeError",
            r"type\s+error",
            r"unsupported\s+operand",
            r"not\s+callable",
        ],
        FailureCategory.VALUE: [
            r"ValueError",
            r"invalid\s+value",
            r"could\s+not\s+convert",
        ],
        FailureCategory.KEY: [
            r"KeyError",
            r"key\s+not\s+found",
        ],
        FailureCategory.INDEX: [
            r"IndexError",
            r"index\s+out\s+of\s+range",
            r"list\s+index\s+out\s+of\s+range",
        ],
        FailureCategory.SYNTAX: [
            r"SyntaxError",
            r"IndentationError",
            r"invalid\s+syntax",
        ],
    }
    
    FIX_SUGGESTIONS = {
        FailureCategory.ASSERTION: [
            "检查断言条件是否正确",
            "验证预期值与实际值是否匹配",
            "检查测试数据是否正确设置",
        ],
        FailureCategory.EXCEPTION: [
            "添加适当的异常处理",
            "检查异常抛出的条件",
            "验证异常类型是否正确",
        ],
        FailureCategory.TIMEOUT: [
            "增加超时时间",
            "优化代码性能",
            "检查是否存在死循环",
        ],
        FailureCategory.IMPORT: [
            "安装缺失的依赖包",
            "检查模块路径是否正确",
            "验证导入语句是否正确",
        ],
        FailureCategory.ATTRIBUTE: [
            "检查对象是否有该属性",
            "验证属性名称是否正确",
            "检查对象是否正确初始化",
        ],
        FailureCategory.TYPE: [
            "检查变量类型",
            "添加类型转换",
            "验证操作数类型是否兼容",
        ],
        FailureCategory.VALUE: [
            "验证输入值是否在有效范围内",
            "检查值的格式是否正确",
            "添加值验证逻辑",
        ],
        FailureCategory.KEY: [
            "检查键是否存在",
            "使用.get()方法提供默认值",
            "验证字典内容",
        ],
        FailureCategory.INDEX: [
            "检查索引是否在有效范围内",
            "验证列表/数组长度",
            "使用安全的索引访问方法",
        ],
        FailureCategory.SYNTAX: [
            "检查语法错误",
            "验证缩进是否正确",
            "检查括号和引号是否匹配",
        ],
    }
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or self._setup_logger()
        self.analysis_counter = 0
        self._failure_history: Dict[str, List[FailureAnalysis]] = {}
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger("FailureAnalyzer")
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def analyze_failures(
        self,
        test_results: List[TestResult],
        spec_elements: Optional[Dict[str, Any]] = None
    ) -> List[FailureAnalysis]:
        analyses = []
        
        failed_tests = [
            tr for tr in test_results
            if tr.status in [TestStatus.FAILED, TestStatus.ERROR]
        ]
        
        for test in failed_tests:
            analysis = self._analyze_single_failure(test, spec_elements)
            analyses.append(analysis)
            self._update_failure_history(analysis)
        
        analyses = self._find_related_failures(analyses)
        
        self.logger.info(f"分析了 {len(analyses)} 个失败测试")
        return analyses
    
    def analyze_failures_advanced(
        self,
        test_results: List[TestResult],
        spec_elements: Optional[Dict[str, Any]] = None,
        code_context: Optional[Dict[str, str]] = None
    ) -> List[FailureAnalysis]:
        analyses = self.analyze_failures(test_results, spec_elements)
        
        if code_context:
            for analysis in analyses:
                self._enrich_with_code_context(analysis, code_context)
        
        for analysis in analyses:
            self._calculate_impact_level(analysis, test_results)
            self._estimate_fix_complexity(analysis)
            self._generate_assertion_details(analysis)
        
        return analyses
    
    def _analyze_single_failure(
        self, 
        test: TestResult,
        spec_elements: Optional[Dict[str, Any]] = None
    ) -> FailureAnalysis:
        self.analysis_counter += 1
        failure_id = f"FA-{datetime.now().strftime('%Y%m%d%H%M%S')}-{self.analysis_counter:03d}"
        
        category = self._categorize_failure(test)
        root_cause = self._identify_root_cause(test, category)
        suggested_fix = self._generate_fix_suggestion(category, test)
        confidence = self._calculate_confidence(test, category)
        related_spec = self._extract_related_spec_element(test)
        
        affected_components = self._identify_affected_components(test, spec_elements)
        code_snippet = self._extract_code_snippet(test)
        
        return FailureAnalysis(
            failure_id=failure_id,
            test_id=test.test_id,
            category=category,
            root_cause=root_cause,
            error_message=test.message or test.traceback[:500] if test.traceback else "",
            suggested_fix=suggested_fix,
            related_spec_element=related_spec,
            confidence=confidence,
            details={
                "test_name": test.test_name,
                "file_path": test.file_path,
                "line_number": test.line_number,
                "duration": test.duration,
                "is_slow": test.is_slow,
                "stability": test.stability.value if test.stability else "unknown"
            },
            affected_components=affected_components,
            code_snippet=code_snippet
        )
    
    def _update_failure_history(self, analysis: FailureAnalysis) -> None:
        test_id = analysis.test_id
        if test_id not in self._failure_history:
            self._failure_history[test_id] = []
        self._failure_history[test_id].append(analysis)
        
        if len(self._failure_history[test_id]) > 10:
            self._failure_history[test_id] = self._failure_history[test_id][-10:]
    
    def _find_related_failures(self, analyses: List[FailureAnalysis]) -> List[FailureAnalysis]:
        for analysis in analyses:
            related = []
            
            for other in analyses:
                if other.failure_id == analysis.failure_id:
                    continue
                
                if (other.category == analysis.category and 
                    other.related_spec_element == analysis.related_spec_element):
                    related.append(other.failure_id)
                
                if (other.file_path == analysis.details.get("file_path") and
                    other.failure_id not in related):
                    related.append(other.failure_id)
            
            analysis.related_failures = related[:5]
        
        return analyses
    
    def _identify_affected_components(
        self, 
        test: TestResult,
        spec_elements: Optional[Dict[str, Any]]
    ) -> List[str]:
        components = []
        
        if test.spec_references:
            components.extend(test.spec_references)
        
        if spec_elements:
            for iface in spec_elements.get("interfaces", []):
                iface_name = iface.get("name", "").lower()
                if iface_name in test.test_name.lower():
                    components.append(iface_name)
            
            for model in spec_elements.get("data_models", []):
                model_name = model.get("name", "").lower()
                if model_name in test.test_name.lower():
                    components.append(model_name)
        
        if test.file_path:
            file_component = Path(test.file_path).stem
            components.append(file_component)
        
        return list(set(components))
    
    def _extract_code_snippet(self, test: TestResult) -> str:
        if not test.file_path or not Path(test.file_path).exists():
            return ""
        
        try:
            with open(test.file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            start = max(0, test.line_number - 5)
            end = min(len(lines), test.line_number + 10)
            
            snippet_lines = lines[start:end]
            return "".join(snippet_lines)
        except Exception:
            return ""
    
    def _enrich_with_code_context(
        self, 
        analysis: FailureAnalysis,
        code_context: Dict[str, str]
    ) -> None:
        file_path = analysis.details.get("file_path", "")
        if file_path in code_context:
            context = code_context[file_path]
            
            if analysis.category == FailureCategory.ASSERTION:
                self._enrich_assertion_context(analysis, context)
            elif analysis.category == FailureCategory.TYPE:
                self._enrich_type_context(analysis, context)
    
    def _enrich_assertion_context(self, analysis: FailureAnalysis, context: str) -> None:
        assert_patterns = [
            r"assert\s+(.+?)\s*==\s*(.+)",
            r"assert\s+(.+?)\s*!=\s*(.+)",
            r"assert\s+(.+?)\s+in\s+(.+)",
        ]
        
        for pattern in assert_patterns:
            match = re.search(pattern, context)
            if match:
                analysis.assertion_details["assertion_type"] = "equality"
                analysis.assertion_details["left"] = match.group(1).strip()
                analysis.assertion_details["right"] = match.group(2).strip()
                break
    
    def _enrich_type_context(self, analysis: FailureAnalysis, context: str) -> None:
        type_hints = re.findall(r":\s*(\w+(?:\[.+?\])?)", context)
        if type_hints:
            analysis.details["detected_types"] = type_hints
    
    def _calculate_impact_level(
        self, 
        analysis: FailureAnalysis,
        all_results: List[TestResult]
    ) -> None:
        total = len(all_results)
        if total == 0:
            analysis.impact_level = ImpactLevel.MINIMAL
            return
        
        failed_count = len([r for r in all_results if r.status in [TestStatus.FAILED, TestStatus.ERROR]])
        failure_rate = failed_count / total
        
        if analysis.category in [FailureCategory.IMPORT, FailureCategory.SYNTAX]:
            analysis.impact_level = ImpactLevel.CRITICAL
        elif failure_rate > 0.3 or len(analysis.affected_components) > 3:
            analysis.impact_level = ImpactLevel.HIGH
        elif failure_rate > 0.1 or len(analysis.affected_components) > 1:
            analysis.impact_level = ImpactLevel.MEDIUM
        elif failure_rate > 0.05:
            analysis.impact_level = ImpactLevel.LOW
        else:
            analysis.impact_level = ImpactLevel.MINIMAL
    
    def _estimate_fix_complexity(self, analysis: FailureAnalysis) -> None:
        complexity_indicators = {
            FailureCategory.SYNTAX: ("low", "分钟级"),
            FailureCategory.IMPORT: ("low", "分钟级"),
            FailureCategory.KEY: ("low", "分钟级"),
            FailureCategory.INDEX: ("low", "分钟级"),
            FailureCategory.ATTRIBUTE: ("medium", "小时级"),
            FailureCategory.TYPE: ("medium", "小时级"),
            FailureCategory.VALUE: ("medium", "小时级"),
            FailureCategory.ASSERTION: ("medium", "小时级"),
            FailureCategory.EXCEPTION: ("high", "天级"),
            FailureCategory.TIMEOUT: ("high", "天级"),
            FailureCategory.UNKNOWN: ("unknown", "未知"),
        }
        
        complexity, time_estimate = complexity_indicators.get(
            analysis.category, ("unknown", "未知")
        )
        
        if len(analysis.related_failures) > 2:
            complexity = "high" if complexity != "unknown" else complexity
        
        if len(analysis.affected_components) > 2:
            complexity = "high"
        
        analysis.fix_complexity = complexity
        analysis.estimated_fix_time = time_estimate
    
    def _generate_assertion_details(self, analysis: FailureAnalysis) -> None:
        if analysis.category != FailureCategory.ASSERTION:
            return
        
        error_msg = analysis.error_message
        
        expected_patterns = [
            (r"Expected[:：]\s*['\"]?(.+?)['\"]?(?:\s|$)", "expected"),
            (r"expected\s+['\"]?(.+?)['\"]?(?:\s|$)", "expected"),
            (r"but\s+was[:：]\s*['\"]?(.+?)['\"]?(?:\s|$)", "actual"),
            (r"actual[:：]\s*['\"]?(.+?)['\"]?(?:\s|$)", "actual"),
            (r"got[:：]\s*['\"]?(.+?)['\"]?(?:\s|$)", "actual"),
        ]
        
        for pattern, key in expected_patterns:
            match = re.search(pattern, error_msg, re.IGNORECASE)
            if match:
                analysis.assertion_details[key] = match.group(1).strip()
        
        if "assert True" in error_msg or "assert False" in error_msg:
            analysis.assertion_details["assertion_type"] = "boolean"
        elif "assert " in error_msg and "==" in error_msg:
            analysis.assertion_details["assertion_type"] = "equality"
        elif "assert " in error_msg and "in " in error_msg:
            analysis.assertion_details["assertion_type"] = "membership"
    
    def _categorize_failure(self, test: TestResult) -> FailureCategory:
        combined_text = f"{test.message} {test.traceback}"
        
        for category, patterns in self.FAILURE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, combined_text, re.IGNORECASE):
                    return category
        
        return FailureCategory.UNKNOWN
    
    def _identify_root_cause(
        self,
        test: TestResult,
        category: FailureCategory
    ) -> str:
        if category == FailureCategory.ASSERTION:
            return self._analyze_assertion_failure(test)
        elif category == FailureCategory.EXCEPTION:
            return self._analyze_exception_failure(test)
        elif category == FailureCategory.IMPORT:
            return self._analyze_import_failure(test)
        else:
            return f"检测到 {category.value} 类型的失败"
    
    def _analyze_assertion_failure(self, test: TestResult) -> str:
        message = test.message or test.traceback
        
        expected_match = re.search(r"Expected[:：]\s*(.+?)(?:\n|$)", message)
        actual_match = re.search(r"(?:Actual|Got|But)[:：]\s*(.+?)(?:\n|$)", message)
        
        if expected_match and actual_match:
            return f"预期值 '{expected_match.group(1).strip()}' 与实际值 '{actual_match.group(1).strip()}' 不匹配"
        
        return "断言条件不满足"
    
    def _analyze_exception_failure(self, test: TestResult) -> str:
        traceback = test.traceback
        
        exc_match = re.search(r"(\w+Error|\w+Exception):\s*(.+?)(?:\n|$)", traceback)
        if exc_match:
            return f"抛出异常: {exc_match.group(1)} - {exc_match.group(2)}"
        
        return "执行过程中抛出异常"
    
    def _analyze_import_failure(self, test: TestResult) -> str:
        message = test.message or test.traceback
        
        module_match = re.search(r"No module named '(.+?)'", message)
        if module_match:
            return f"缺少模块: {module_match.group(1)}"
        
        return "模块导入失败"
    
    def _generate_fix_suggestion(
        self,
        category: FailureCategory,
        test: TestResult
    ) -> str:
        suggestions = self.FIX_SUGGESTIONS.get(category, ["检查测试代码"])
        
        specific_suggestion = self._generate_specific_suggestion(category, test)
        if specific_suggestion:
            return specific_suggestion
        
        return "; ".join(suggestions[:2])
    
    def _generate_specific_suggestion(
        self,
        category: FailureCategory,
        test: TestResult
    ) -> str:
        if category == FailureCategory.ASSERTION:
            return self._suggest_assertion_fix(test)
        elif category == FailureCategory.KEY:
            return self._suggest_key_fix(test)
        elif category == FailureCategory.ATTRIBUTE:
            return self._suggest_attribute_fix(test)
        
        return ""
    
    def _suggest_assertion_fix(self, test: TestResult) -> str:
        message = test.message or test.traceback
        
        if "None" in message:
            return "检查返回值是否为None，可能需要先初始化对象或检查前置条件"
        
        if "type" in message.lower():
            return "验证数据类型是否正确，可能需要类型转换"
        
        return ""
    
    def _suggest_key_fix(self, test: TestResult) -> str:
        message = test.message or test.traceback
        
        key_match = re.search(r"KeyError[:：]\s*['\"](.+?)['\"]", message)
        if key_match:
            return f"检查字典是否包含键 '{key_match.group(1)}'，或使用 dict.get('{key_match.group(1)}', default) 提供默认值"
        
        return ""
    
    def _suggest_attribute_fix(self, test: TestResult) -> str:
        message = test.message or test.traceback
        
        attr_match = re.search(r"has no attribute '(.+?)'", message)
        if attr_match:
            return f"检查对象是否有属性 '{attr_match.group(1)}'，可能需要检查对象类型或初始化"
        
        return ""
    
    def _calculate_confidence(
        self,
        test: TestResult,
        category: FailureCategory
    ) -> float:
        confidence = 0.5
        
        if test.message:
            confidence += 0.1
        if test.traceback:
            confidence += 0.2
        if test.file_path:
            confidence += 0.1
        if category != FailureCategory.UNKNOWN:
            confidence += 0.2
        
        return min(1.0, confidence)
    
    def _extract_related_spec_element(self, test: TestResult) -> str:
        test_name = test.test_name
        
        patterns = [
            r"test_(\w+)_",
            r"test(\w+)",
            r"Test(\w+)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, test_name)
            if match:
                return match.group(1).lower()
        
        return ""
    
    def analyze_failures_deeply(
        self,
        test_results: List[TestResult],
        spec_elements: Optional[Dict[str, Any]] = None,
        code_context: Optional[Dict[str, str]] = None,
        historical_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        深度分析测试失败结果
        
        该方法提供更全面的失败分析，包括：
        - 失败模式识别：识别常见的失败模式
        - 根因链分析：分析失败的因果关系链
        - 影响范围评估：评估失败对系统的影响
        - 历史趋势分析：基于历史数据分析失败趋势
        - 关联性分析：分析失败之间的关联关系
        
        参数:
            test_results: 测试结果列表
            spec_elements: 规范元素字典
            code_context: 代码上下文信息
            historical_data: 历史数据
            
        返回:
            包含深度分析结果的字典
        """
        self.logger.info("开始深度分析测试失败结果...")
        
        basic_analyses = self.analyze_failures_advanced(
            test_results, spec_elements, code_context
        )
        
        failure_patterns = self._identify_failure_patterns(basic_analyses)
        
        root_cause_chains = self._analyze_root_cause_chains(basic_analyses, test_results)
        
        impact_assessment = self._assess_failure_impact(basic_analyses, spec_elements)
        
        trend_analysis = {}
        if historical_data:
            trend_analysis = self._analyze_failure_trends(basic_analyses, historical_data)
        
        correlation_analysis = self._analyze_failure_correlations(basic_analyses)
        
        actionable_insights = self._generate_actionable_insights(
            basic_analyses,
            failure_patterns,
            root_cause_chains,
            impact_assessment
        )
        
        return {
            "basic_analyses": basic_analyses,
            "failure_patterns": failure_patterns,
            "root_cause_chains": root_cause_chains,
            "impact_assessment": impact_assessment,
            "trend_analysis": trend_analysis,
            "correlation_analysis": correlation_analysis,
            "actionable_insights": actionable_insights,
            "summary": self._generate_deep_analysis_summary(
                basic_analyses, failure_patterns, impact_assessment
            )
        }
    
    def _identify_failure_patterns(
        self,
        analyses: List[FailureAnalysis]
    ) -> Dict[str, Any]:
        """识别失败模式"""
        patterns = {
            "by_category": {},
            "by_component": {},
            "by_error_signature": {},
            "recurring_patterns": []
        }
        
        for analysis in analyses:
            category = analysis.category.value
            patterns["by_category"][category] = patterns["by_category"].get(category, 0) + 1
            
            for component in analysis.affected_components:
                patterns["by_component"][component] = patterns["by_component"].get(component, 0) + 1
            
            error_sig = self._generate_error_signature(analysis)
            patterns["by_error_signature"][error_sig] = patterns["by_error_signature"].get(error_sig, 0) + 1
        
        for sig, count in patterns["by_error_signature"].items():
            if count >= 2:
                patterns["recurring_patterns"].append({
                    "signature": sig,
                    "count": count,
                    "severity": "high" if count >= 3 else "medium"
                })
        
        patterns["recurring_patterns"].sort(key=lambda x: x["count"], reverse=True)
        
        return patterns
    
    def _generate_error_signature(self, analysis: FailureAnalysis) -> str:
        """生成错误签名用于模式识别"""
        sig_parts = [
            analysis.category.value,
            analysis.root_cause[:50] if analysis.root_cause else "",
            analysis.details.get("file_path", "").split("/")[-1] if analysis.details.get("file_path") else ""
        ]
        return "|".join(sig_parts)
    
    def _analyze_root_cause_chains(
        self,
        analyses: List[FailureAnalysis],
        test_results: List[TestResult]
    ) -> List[Dict[str, Any]]:
        """分析根因链"""
        chains = []
        
        for analysis in analyses:
            chain = {
                "failure_id": analysis.failure_id,
                "test_id": analysis.test_id,
                "primary_cause": analysis.root_cause,
                "secondary_causes": [],
                "contributing_factors": []
            }
            
            if analysis.category == FailureCategory.ASSERTION:
                if "None" in analysis.error_message:
                    chain["secondary_causes"].append("可能的空值引用")
                if "type" in analysis.error_message.lower():
                    chain["secondary_causes"].append("可能的类型不匹配")
            
            elif analysis.category == FailureCategory.EXCEPTION:
                if "connection" in analysis.error_message.lower():
                    chain["contributing_factors"].append("网络或连接问题")
                if "timeout" in analysis.error_message.lower():
                    chain["contributing_factors"].append("性能或超时问题")
            
            if len(analysis.related_failures) > 0:
                chain["contributing_factors"].append(f"关联 {len(analysis.related_failures)} 个其他失败")
            
            chains.append(chain)
        
        return chains
    
    def _assess_failure_impact(
        self,
        analyses: List[FailureAnalysis],
        spec_elements: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """评估失败影响"""
        impact = {
            "overall_severity": "low",
            "affected_areas": [],
            "critical_failures": [],
            "blocking_issues": [],
            "risk_score": 0.0
        }
        
        critical_count = len([a for a in analyses if a.impact_level == ImpactLevel.CRITICAL])
        high_count = len([a for a in analyses if a.impact_level == ImpactLevel.HIGH])
        
        if critical_count > 0:
            impact["overall_severity"] = "critical"
        elif high_count > 2:
            impact["overall_severity"] = "high"
        elif high_count > 0:
            impact["overall_severity"] = "medium"
        
        impact["critical_failures"] = [
            {
                "test_id": a.test_id,
                "category": a.category.value,
                "root_cause": a.root_cause
            }
            for a in analyses if a.impact_level in [ImpactLevel.CRITICAL, ImpactLevel.HIGH]
        ]
        
        for analysis in analyses:
            if analysis.category in [FailureCategory.IMPORT, FailureCategory.SYNTAX]:
                impact["blocking_issues"].append({
                    "test_id": analysis.test_id,
                    "reason": f"{analysis.category.value} 可能阻塞其他测试"
                })
        
        if spec_elements:
            for analysis in analyses:
                for component in analysis.affected_components:
                    if component not in [a["name"] for a in impact["affected_areas"]]:
                        impact["affected_areas"].append({
                            "name": component,
                            "failure_count": 1,
                            "severity": analysis.impact_level.value
                        })
        
        risk_score = critical_count * 30 + high_count * 15 + len(analyses) * 5
        impact["risk_score"] = min(100, risk_score)
        
        return impact
    
    def _analyze_failure_trends(
        self,
        analyses: List[FailureAnalysis],
        historical_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """分析失败趋势"""
        trends = {
            "improving": [],
            "worsening": [],
            "stable": [],
            "new_issues": []
        }
        
        previous_failures = historical_data.get("previous_failures", {})
        
        for analysis in analyses:
            test_id = analysis.test_id
            prev_count = previous_failures.get(test_id, 0)
            
            if prev_count == 0:
                trends["new_issues"].append({
                    "test_id": test_id,
                    "category": analysis.category.value
                })
            elif prev_count > 3:
                trends["worsening"].append({
                    "test_id": test_id,
                    "historical_count": prev_count
                })
            elif prev_count > 0:
                trends["stable"].append({
                    "test_id": test_id,
                    "historical_count": prev_count
                })
        
        return trends
    
    def _analyze_failure_correlations(
        self,
        analyses: List[FailureAnalysis]
    ) -> Dict[str, Any]:
        """分析失败之间的关联性"""
        correlations = {
            "by_file": {},
            "by_component": {},
            "by_category": {},
            "strong_correlations": []
        }
        
        file_failures = {}
        for analysis in analyses:
            file_path = analysis.details.get("file_path", "unknown")
            if file_path not in file_failures:
                file_failures[file_path] = []
            file_failures[file_path].append(analysis.test_id)
        
        correlations["by_file"] = file_failures
        
        component_pairs = {}
        for analysis in analyses:
            components = tuple(sorted(analysis.affected_components))
            if components not in component_pairs:
                component_pairs[components] = 0
            component_pairs[components] += 1
        
        for components, count in component_pairs.items():
            if count >= 2 and len(components) > 1:
                correlations["strong_correlations"].append({
                    "components": list(components),
                    "co_occurrence_count": count
                })
        
        return correlations
    
    def _generate_actionable_insights(
        self,
        analyses: List[FailureAnalysis],
        patterns: Dict[str, Any],
        root_cause_chains: List[Dict[str, Any]],
        impact_assessment: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """生成可操作的洞察"""
        insights = []
        
        for pattern in patterns.get("recurring_patterns", [])[:3]:
            insights.append({
                "type": "recurring_pattern",
                "priority": "high",
                "description": f"发现重复出现的失败模式: {pattern['signature']}",
                "occurrence_count": pattern["count"],
                "recommended_action": "建议优先解决该模式相关的失败"
            })
        
        for chain in root_cause_chains:
            if len(chain.get("contributing_factors", [])) >= 2:
                insights.append({
                    "type": "complex_failure",
                    "priority": "medium",
                    "description": f"测试 {chain['test_id']} 有多个贡献因素",
                    "factors": chain["contributing_factors"],
                    "recommended_action": "建议系统性排查所有贡献因素"
                })
        
        if impact_assessment.get("risk_score", 0) > 50:
            insights.append({
                "type": "high_risk",
                "priority": "critical",
                "description": f"当前失败风险评分为 {impact_assessment['risk_score']}",
                "recommended_action": "建议立即处理关键和高优先级失败"
            })
        
        return insights
    
    def _generate_deep_analysis_summary(
        self,
        analyses: List[FailureAnalysis],
        patterns: Dict[str, Any],
        impact_assessment: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成深度分析摘要"""
        return {
            "total_failures": len(analyses),
            "unique_patterns": len(patterns.get("recurring_patterns", [])),
            "overall_severity": impact_assessment.get("overall_severity", "unknown"),
            "risk_score": impact_assessment.get("risk_score", 0),
            "top_categories": sorted(
                patterns.get("by_category", {}).items(),
                key=lambda x: x[1],
                reverse=True
            )[:3],
            "recommendation": self._generate_summary_recommendation(analyses, impact_assessment)
        }
    
    def _generate_summary_recommendation(
        self,
        analyses: List[FailureAnalysis],
        impact_assessment: Dict[str, Any]
    ) -> str:
        """生成摘要建议"""
        if impact_assessment.get("overall_severity") == "critical":
            return "存在严重失败，建议立即停止开发并修复关键问题"
        elif impact_assessment.get("overall_severity") == "high":
            return "存在高优先级失败，建议优先处理后再继续开发"
        elif len(analyses) > 5:
            return "失败数量较多，建议进行系统性排查"
        else:
            return "失败数量可控，建议按优先级逐个处理"


class FeedbackGenerator:
    """测试结果到规范的反馈生成器"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or self._setup_logger()
        self.feedback_counter = 0
        self._feedback_history: Dict[str, List[FeedbackItem]] = {}
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger("FeedbackGenerator")
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def generate_feedback(
        self,
        test_results: List[TestResult],
        failure_analyses: List[FailureAnalysis],
        spec_elements: Optional[Dict[str, Any]] = None
    ) -> List[FeedbackItem]:
        feedback_items = []
        
        element_failures = self._group_failures_by_element(failure_analyses)
        
        for element, analyses in element_failures.items():
            feedback = self._create_feedback_for_element(
                element,
                analyses,
                test_results,
                spec_elements
            )
            if feedback:
                feedback_items.append(feedback)
        
        overall_feedback = self._create_overall_feedback(test_results, failure_analyses)
        if overall_feedback:
            feedback_items.append(overall_feedback)
        
        for feedback in feedback_items:
            self._calculate_priority_score(feedback, test_results)
            self._determine_impact_level(feedback, failure_analyses)
            self._find_affected_spec_elements(feedback, spec_elements)
            self._extract_code_locations(feedback, failure_analyses)
            self._check_auto_fix_availability(feedback, failure_analyses)
        
        self._update_feedback_history(feedback_items)
        
        self.logger.info(f"生成了 {len(feedback_items)} 条反馈")
        return feedback_items
    
    def generate_feedback_advanced(
        self,
        test_results: List[TestResult],
        failure_analyses: List[FailureAnalysis],
        spec_elements: Optional[Dict[str, Any]] = None,
        historical_data: Optional[Dict[str, Any]] = None
    ) -> List[FeedbackItem]:
        feedback_items = self.generate_feedback(
            test_results, failure_analyses, spec_elements
        )
        
        for feedback in feedback_items:
            if historical_data:
                self._add_historical_context(feedback, historical_data)
            
            self._generate_auto_fix_suggestion(feedback, failure_analyses, spec_elements)
        
        feedback_items.sort(key=lambda x: x.priority_score, reverse=True)
        
        return feedback_items
    
    def _group_failures_by_element(
        self,
        failure_analyses: List[FailureAnalysis]
    ) -> Dict[str, List[FailureAnalysis]]:
        grouped = {}
        
        for analysis in failure_analyses:
            element = analysis.related_spec_element or "unknown"
            if element not in grouped:
                grouped[element] = []
            grouped[element].append(analysis)
        
        return grouped
    
    def _create_feedback_for_element(
        self,
        element: str,
        analyses: List[FailureAnalysis],
        test_results: List[TestResult],
        spec_elements: Optional[Dict[str, Any]]
    ) -> Optional[FeedbackItem]:
        self.feedback_counter += 1
        feedback_id = f"FB-{datetime.now().strftime('%Y%m%d%H%M%S')}-{self.feedback_counter:03d}"
        
        test_ids = [a.test_id for a in analyses]
        
        categories = [a.category for a in analyses]
        most_common_category = max(set(categories), key=categories.count)
        
        severity = self._determine_severity(analyses)
        
        feedback_type = self._determine_feedback_type(most_common_category)
        
        message = self._generate_feedback_message(element, analyses)
        
        suggestions = self._generate_feedback_suggestions(analyses)
        
        impact = self._assess_impact(analyses, test_results)
        
        return FeedbackItem(
            feedback_id=feedback_id,
            spec_element_id=element,
            spec_element_name=element,
            feedback_type=feedback_type,
            severity=severity,
            message=message,
            test_ids=test_ids,
            suggestions=suggestions,
            impact=impact
        )
    
    def _calculate_priority_score(
        self,
        feedback: FeedbackItem,
        test_results: List[TestResult]
    ) -> None:
        score = 0.0
        
        severity_scores = {
            FeedbackSeverity.CRITICAL: 40.0,
            FeedbackSeverity.HIGH: 30.0,
            FeedbackSeverity.MEDIUM: 20.0,
            FeedbackSeverity.LOW: 10.0,
            FeedbackSeverity.INFO: 5.0,
        }
        score += severity_scores.get(feedback.severity, 0)
        
        score += len(feedback.test_ids) * 5
        
        total_tests = len(test_results)
        if total_tests > 0:
            failure_ratio = len(feedback.test_ids) / total_tests
            score += failure_ratio * 20
        
        if feedback.feedback_type in ["dependency_issue", "syntax_issue"]:
            score += 15
        
        feedback.priority_score = min(100.0, score)
    
    def _determine_impact_level(
        self,
        feedback: FeedbackItem,
        failure_analyses: List[FailureAnalysis]
    ) -> None:
        related_analyses = [
            a for a in failure_analyses 
            if a.test_id in feedback.test_ids
        ]
        
        if not related_analyses:
            feedback.impact_level = ImpactLevel.MINIMAL
            return
        
        max_impact = max(a.impact_level for a in related_analyses)
        
        impact_order = [
            ImpactLevel.MINIMAL,
            ImpactLevel.LOW,
            ImpactLevel.MEDIUM,
            ImpactLevel.HIGH,
            ImpactLevel.CRITICAL,
        ]
        
        if len(related_analyses) > 3:
            idx = impact_order.index(max_impact)
            max_impact = impact_order[min(idx + 1, len(impact_order) - 1)]
        
        feedback.impact_level = max_impact
    
    def _find_affected_spec_elements(
        self,
        feedback: FeedbackItem,
        spec_elements: Optional[Dict[str, Any]]
    ) -> None:
        if not spec_elements:
            return
        
        affected = []
        element_name = feedback.spec_element_name.lower()
        
        for iface in spec_elements.get("interfaces", []):
            iface_name = iface.get("name", "").lower()
            if element_name in iface_name or iface_name in element_name:
                affected.append(iface.get("name", ""))
        
        for model in spec_elements.get("data_models", []):
            model_name = model.get("name", "").lower()
            if element_name in model_name or model_name in element_name:
                affected.append(model.get("name", ""))
        
        for rule in spec_elements.get("behavior_rules", []):
            rule_name = rule.get("name", "").lower()
            if element_name in rule_name or rule_name in element_name:
                affected.append(rule.get("name", ""))
        
        feedback.affected_spec_elements = list(set(affected))
    
    def _extract_code_locations(
        self,
        feedback: FeedbackItem,
        failure_analyses: List[FailureAnalysis]
    ) -> None:
        locations = []
        
        for analysis in failure_analyses:
            if analysis.test_id in feedback.test_ids:
                location = {
                    "file_path": analysis.details.get("file_path", ""),
                    "line_number": analysis.details.get("line_number", 0),
                    "test_id": analysis.test_id,
                }
                if location["file_path"]:
                    locations.append(location)
        
        feedback.code_locations = locations
    
    def _check_auto_fix_availability(
        self,
        feedback: FeedbackItem,
        failure_analyses: List[FailureAnalysis]
    ) -> None:
        auto_fixable_types = [
            "dependency_issue",
            "syntax_issue",
            "data_structure_issue",
        ]
        
        if feedback.feedback_type in auto_fixable_types:
            feedback.auto_fix_available = True
            return
        
        for analysis in failure_analyses:
            if analysis.test_id in feedback.test_ids:
                if analysis.category in [
                    FailureCategory.KEY,
                    FailureCategory.INDEX,
                    FailureCategory.IMPORT,
                ]:
                    feedback.auto_fix_available = True
                    return
    
    def _update_feedback_history(self, feedback_items: List[FeedbackItem]) -> None:
        for feedback in feedback_items:
            element = feedback.spec_element_id
            if element not in self._feedback_history:
                self._feedback_history[element] = []
            self._feedback_history[element].append(feedback)
            
            if len(self._feedback_history[element]) > 10:
                self._feedback_history[element] = self._feedback_history[element][-10:]
    
    def _add_historical_context(
        self,
        feedback: FeedbackItem,
        historical_data: Dict[str, Any]
    ) -> None:
        element = feedback.spec_element_id
        
        if element in historical_data.get("previous_failures", {}):
            feedback.historical_context["previous_failure_count"] = \
                historical_data["previous_failures"][element]
        
        if element in historical_data.get("fix_history", {}):
            feedback.historical_context["last_fix"] = \
                historical_data["fix_history"][element]
        
        if element in self._feedback_history:
            previous = self._feedback_history[element]
            if len(previous) > 1:
                feedback.historical_context["recurrence"] = True
                feedback.historical_context["recurrence_count"] = len(previous)
    
    def _generate_auto_fix_suggestion(
        self,
        feedback: FeedbackItem,
        failure_analyses: List[FailureAnalysis],
        spec_elements: Optional[Dict[str, Any]]
    ) -> None:
        if not feedback.auto_fix_available:
            return
        
        related_analyses = [
            a for a in failure_analyses 
            if a.test_id in feedback.test_ids
        ]
        
        if not related_analyses:
            return
        
        analysis = related_analyses[0]
        
        if analysis.category == FailureCategory.KEY:
            key_match = re.search(r"KeyError[:：]\s*['\"](.+?)['\"]", analysis.error_message)
            if key_match:
                key = key_match.group(1)
                feedback.auto_fix_suggestion = f"添加键 '{key}' 的检查或使用 dict.get('{key}', default)"
        
        elif analysis.category == FailureCategory.IMPORT:
            module_match = re.search(r"No module named '(.+?)'", analysis.error_message)
            if module_match:
                module = module_match.group(1)
                feedback.auto_fix_suggestion = f"安装缺失模块: pip install {module}"
        
        elif analysis.category == FailureCategory.INDEX:
            feedback.auto_fix_suggestion = "添加边界检查或使用安全的索引访问方法"
        
        elif feedback.feedback_type == "syntax_issue":
            feedback.auto_fix_suggestion = "检查并修复语法错误"
    
    def _determine_severity(self, analyses: List[FailureAnalysis]) -> FeedbackSeverity:
        high_severity_categories = [
            FailureCategory.EXCEPTION,
            FailureCategory.IMPORT,
            FailureCategory.SYNTAX
        ]
        
        for analysis in analyses:
            if analysis.category in high_severity_categories:
                return FeedbackSeverity.HIGH
        
        if len(analyses) >= 3:
            return FeedbackSeverity.HIGH
        elif len(analyses) >= 2:
            return FeedbackSeverity.MEDIUM
        else:
            return FeedbackSeverity.LOW
    
    def _determine_feedback_type(self, category: FailureCategory) -> str:
        type_mapping = {
            FailureCategory.ASSERTION: "specification_mismatch",
            FailureCategory.EXCEPTION: "error_handling_issue",
            FailureCategory.TIMEOUT: "performance_issue",
            FailureCategory.IMPORT: "dependency_issue",
            FailureCategory.ATTRIBUTE: "interface_mismatch",
            FailureCategory.TYPE: "type_specification_issue",
            FailureCategory.VALUE: "validation_issue",
            FailureCategory.KEY: "data_structure_issue",
            FailureCategory.INDEX: "boundary_issue",
            FailureCategory.SYNTAX: "syntax_issue",
            FailureCategory.UNKNOWN: "unknown_issue",
        }
        return type_mapping.get(category, "unknown_issue")
    
    def _generate_feedback_message(
        self,
        element: str,
        analyses: List[FailureAnalysis]
    ) -> str:
        failure_count = len(analyses)
        
        categories = set(a.category.value for a in analyses)
        
        message = f"规范元素 '{element}' 存在 {failure_count} 个测试失败"
        
        if failure_count == 1:
            message = f"规范元素 '{element}' 存在测试失败"
            analysis = analyses[0]
            message += f": {analysis.root_cause}"
        else:
            message += f"，涉及 {len(categories)} 种失败类型"
        
        return message
    
    def _generate_feedback_suggestions(
        self,
        analyses: List[FailureAnalysis]
    ) -> List[str]:
        suggestions = []
        
        for analysis in analyses[:3]:
            if analysis.suggested_fix not in suggestions:
                suggestions.append(analysis.suggested_fix)
        
        return suggestions
    
    def _assess_impact(
        self,
        analyses: List[FailureAnalysis],
        test_results: List[TestResult]
    ) -> str:
        total_tests = len(test_results)
        failed_tests = len([t for t in test_results if t.status in [TestStatus.FAILED, TestStatus.ERROR]])
        
        if total_tests == 0:
            return "无法评估"
        
        failure_rate = failed_tests / total_tests
        
        if failure_rate >= 0.5:
            return "严重影响：超过50%的测试失败"
        elif failure_rate >= 0.2:
            return "中等影响：20%-50%的测试失败"
        elif failure_rate >= 0.1:
            return "轻微影响：10%-20%的测试失败"
        else:
            return "影响较小：少于10%的测试失败"
    
    def _create_overall_feedback(
        self,
        test_results: List[TestResult],
        failure_analyses: List[FailureAnalysis]
    ) -> Optional[FeedbackItem]:
        self.feedback_counter += 1
        feedback_id = f"FB-{datetime.now().strftime('%Y%m%d%H%M%S')}-{self.feedback_counter:03d}"
        
        total = len(test_results)
        passed = len([t for t in test_results if t.status == TestStatus.PASSED])
        failed = len([t for t in test_results if t.status == TestStatus.FAILED])
        errors = len([t for t in test_results if t.status == TestStatus.ERROR])
        
        if failed == 0 and errors == 0:
            return None
        
        pass_rate = (passed / total * 100) if total > 0 else 0
        
        severity = FeedbackSeverity.HIGH if pass_rate < 50 else FeedbackSeverity.MEDIUM
        
        message = f"整体测试通过率为 {pass_rate:.1f}%，{failed + errors} 个测试失败"
        
        suggestions = []
        if pass_rate < 50:
            suggestions.append("建议优先修复核心功能的测试失败")
        if errors > 0:
            suggestions.append("存在执行错误，建议先检查环境配置和依赖")
        
        return FeedbackItem(
            feedback_id=feedback_id,
            spec_element_id="overall",
            spec_element_name="整体测试",
            feedback_type="overall_quality",
            severity=severity,
            message=message,
            test_ids=[t.test_id for t in test_results if t.status in [TestStatus.FAILED, TestStatus.ERROR]],
            suggestions=suggestions,
            impact=f"通过率: {pass_rate:.1f}%"
        )
    
    def generate_intelligent_feedback(
        self,
        test_results: List[TestResult],
        failure_analyses: List[FailureAnalysis],
        spec_elements: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        生成测试结果到SDD规范的智能反馈
        
        该方法实现智能反馈机制，包括：
        - 规范元素映射：将测试失败映射到规范元素
        - 影响分析：分析失败对规范的影响程度
        - 反馈优先级排序：根据影响和严重程度排序
        - 修复建议生成：生成具体的修复建议
        - 规范更新提示：提示需要更新的规范部分
        
        参数:
            test_results: 测试结果列表
            failure_analyses: 失败分析列表
            spec_elements: 规范元素字典
            context: 上下文信息
            
        返回:
            包含智能反馈结果的字典
        """
        self.logger.info("开始生成智能反馈...")
        
        basic_feedback = self.generate_feedback_advanced(
            test_results, failure_analyses, spec_elements, context
        )
        
        spec_mapping = self._map_failures_to_spec_elements(
            failure_analyses, spec_elements
        )
        
        impact_analysis = self._analyze_spec_impact(
            failure_analyses, spec_elements, test_results
        )
        
        prioritized_feedback = self._prioritize_feedback(
            basic_feedback, impact_analysis
        )
        
        fix_recommendations = self._generate_fix_recommendations(
            failure_analyses, spec_elements, impact_analysis
        )
        
        spec_update_hints = self._generate_spec_update_hints(
            failure_analyses, spec_elements, impact_analysis
        )
        
        feedback_report = self._create_intelligent_feedback_report(
            prioritized_feedback,
            spec_mapping,
            impact_analysis,
            fix_recommendations,
            spec_update_hints
        )
        
        return feedback_report
    
    def _map_failures_to_spec_elements(
        self,
        failure_analyses: List[FailureAnalysis],
        spec_elements: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """将失败映射到规范元素"""
        mapping = {
            "direct_mappings": [],
            "indirect_mappings": [],
            "unmapped_failures": []
        }
        
        if not spec_elements:
            return mapping
        
        spec_interfaces = {i.get("name", "").lower(): i for i in spec_elements.get("interfaces", [])}
        spec_models = {m.get("name", "").lower(): m for m in spec_elements.get("data_models", [])}
        spec_rules = {r.get("name", "").lower(): r for r in spec_elements.get("behavior_rules", [])}
        
        for analysis in failure_analyses:
            element_name = analysis.related_spec_element.lower()
            mapped = False
            
            if element_name in spec_interfaces:
                mapping["direct_mappings"].append({
                    "failure_id": analysis.failure_id,
                    "test_id": analysis.test_id,
                    "spec_element": element_name,
                    "spec_type": "interface",
                    "spec_details": spec_interfaces[element_name]
                })
                mapped = True
            elif element_name in spec_models:
                mapping["direct_mappings"].append({
                    "failure_id": analysis.failure_id,
                    "test_id": analysis.test_id,
                    "spec_element": element_name,
                    "spec_type": "data_model",
                    "spec_details": spec_models[element_name]
                })
                mapped = True
            elif element_name in spec_rules:
                mapping["direct_mappings"].append({
                    "failure_id": analysis.failure_id,
                    "test_id": analysis.test_id,
                    "spec_element": element_name,
                    "spec_type": "behavior_rule",
                    "spec_details": spec_rules[element_name]
                })
                mapped = True
            
            if not mapped:
                for component in analysis.affected_components:
                    comp_lower = component.lower()
                    if comp_lower in spec_interfaces or comp_lower in spec_models:
                        mapping["indirect_mappings"].append({
                            "failure_id": analysis.failure_id,
                            "test_id": analysis.test_id,
                            "spec_element": comp_lower,
                            "spec_type": "interface" if comp_lower in spec_interfaces else "data_model",
                            "relation": "component_match"
                        })
                        mapped = True
                        break
            
            if not mapped:
                mapping["unmapped_failures"].append({
                    "failure_id": analysis.failure_id,
                    "test_id": analysis.test_id,
                    "category": analysis.category.value,
                    "root_cause": analysis.root_cause
                })
        
        return mapping
    
    def _analyze_spec_impact(
        self,
        failure_analyses: List[FailureAnalysis],
        spec_elements: Optional[Dict[str, Any]],
        test_results: List[TestResult]
    ) -> Dict[str, Any]:
        """分析失败对规范的影响"""
        impact = {
            "by_spec_element": {},
            "by_spec_type": {},
            "critical_spec_elements": [],
            "affected_constraints": []
        }
        
        for analysis in failure_analyses:
            element = analysis.related_spec_element
            if element not in impact["by_spec_element"]:
                impact["by_spec_element"][element] = {
                    "failure_count": 0,
                    "categories": [],
                    "severity": "low",
                    "tests": []
                }
            
            impact["by_spec_element"][element]["failure_count"] += 1
            impact["by_spec_element"][element]["categories"].append(analysis.category.value)
            impact["by_spec_element"][element]["tests"].append(analysis.test_id)
            
            if analysis.impact_level in [ImpactLevel.CRITICAL, ImpactLevel.HIGH]:
                impact["by_spec_element"][element]["severity"] = "high"
                if element not in [e["element"] for e in impact["critical_spec_elements"]]:
                    impact["critical_spec_elements"].append({
                        "element": element,
                        "reason": analysis.root_cause,
                        "tests": [analysis.test_id]
                    })
        
        if spec_elements:
            for constraint in spec_elements.get("constraints", []):
                constraint_name = constraint.get("name", "").lower()
                for analysis in failure_analyses:
                    if constraint_name in analysis.root_cause.lower():
                        impact["affected_constraints"].append({
                            "constraint": constraint_name,
                            "failure_id": analysis.failure_id,
                            "description": constraint.get("description", "")
                        })
        
        for element_data in impact["by_spec_element"].values():
            categories = element_data["categories"]
            element_data["dominant_category"] = max(set(categories), key=categories.count) if categories else "unknown"
        
        return impact
    
    def _prioritize_feedback(
        self,
        feedback_items: List[FeedbackItem],
        impact_analysis: Dict[str, Any]
    ) -> List[FeedbackItem]:
        """对反馈进行优先级排序"""
        for feedback in feedback_items:
            element = feedback.spec_element_name.lower()
            if element in impact_analysis.get("by_spec_element", {}):
                element_impact = impact_analysis["by_spec_element"][element]
                feedback.priority_score += element_impact["failure_count"] * 5
                
                if element_impact["severity"] == "high":
                    feedback.priority_score += 20
            
            if feedback.spec_element_name.lower() in [e["element"] for e in impact_analysis.get("critical_spec_elements", [])]:
                feedback.priority_score += 30
        
        return sorted(feedback_items, key=lambda x: x.priority_score, reverse=True)
    
    def _generate_fix_recommendations(
        self,
        failure_analyses: List[FailureAnalysis],
        spec_elements: Optional[Dict[str, Any]],
        impact_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """生成修复建议"""
        recommendations = []
        
        for element, impact_data in impact_analysis.get("by_spec_element", {}).items():
            if impact_data["failure_count"] >= 2:
                rec = {
                    "spec_element": element,
                    "priority": "high" if impact_data["severity"] == "high" else "medium",
                    "issue_summary": f"规范元素 '{element}' 有 {impact_data['failure_count']} 个相关失败",
                    "dominant_category": impact_data.get("dominant_category", "unknown"),
                    "affected_tests": impact_data["tests"],
                    "recommended_actions": []
                }
                
                category = impact_data.get("dominant_category", "")
                if category == "assertion":
                    rec["recommended_actions"].append("检查规范中的预期结果定义是否正确")
                    rec["recommended_actions"].append("验证测试用例是否符合规范描述")
                elif category == "type":
                    rec["recommended_actions"].append("检查规范中的类型定义")
                    rec["recommended_actions"].append("确保代码实现与类型定义一致")
                elif category == "exception":
                    rec["recommended_actions"].append("检查规范中的异常处理定义")
                    rec["recommended_actions"].append("添加缺失的异常场景描述")
                
                recommendations.append(rec)
        
        for critical in impact_analysis.get("critical_spec_elements", []):
            rec = {
                "spec_element": critical["element"],
                "priority": "critical",
                "issue_summary": f"关键规范元素 '{critical['element']}' 存在严重问题",
                "reason": critical["reason"],
                "affected_tests": critical["tests"],
                "recommended_actions": [
                    "立即检查该规范元素的定义",
                    "验证相关实现代码",
                    "考虑更新规范或修复实现"
                ]
            }
            recommendations.append(rec)
        
        recommendations.sort(key=lambda x: {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(x["priority"], 4))
        
        return recommendations
    
    def _generate_spec_update_hints(
        self,
        failure_analyses: List[FailureAnalysis],
        spec_elements: Optional[Dict[str, Any]],
        impact_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """生成规范更新提示"""
        hints = []
        
        if not spec_elements:
            return hints
        
        for analysis in failure_analyses:
            if analysis.category == FailureCategory.ASSERTION:
                hints.append({
                    "type": "specification_mismatch",
                    "spec_element": analysis.related_spec_element,
                    "hint": "测试断言失败表明规范定义可能与实际需求不符",
                    "suggested_action": "审查规范中的预期结果定义",
                    "test_evidence": analysis.test_id
                })
            
            elif analysis.category == FailureCategory.EXCEPTION:
                hints.append({
                    "type": "missing_exception_spec",
                    "spec_element": analysis.related_spec_element,
                    "hint": "测试抛出异常，但规范可能缺少异常处理定义",
                    "suggested_action": "在规范中添加异常处理场景",
                    "test_evidence": analysis.test_id
                })
            
            elif analysis.category == FailureCategory.TYPE:
                hints.append({
                    "type": "type_specification_issue",
                    "spec_element": analysis.related_spec_element,
                    "hint": "类型错误表明规范中的类型定义可能不完整或不正确",
                    "suggested_action": "审查并更新规范中的类型定义",
                    "test_evidence": analysis.test_id
                })
        
        seen = set()
        unique_hints = []
        for hint in hints:
            key = (hint["type"], hint["spec_element"])
            if key not in seen:
                seen.add(key)
                unique_hints.append(hint)
        
        return unique_hints
    
    def _create_intelligent_feedback_report(
        self,
        prioritized_feedback: List[FeedbackItem],
        spec_mapping: Dict[str, Any],
        impact_analysis: Dict[str, Any],
        fix_recommendations: List[Dict[str, Any]],
        spec_update_hints: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """创建智能反馈报告"""
        return {
            "feedback_items": [
                {
                    "feedback_id": f.feedback_id,
                    "spec_element": f.spec_element_name,
                    "feedback_type": f.feedback_type,
                    "severity": f.severity.value,
                    "message": f.message,
                    "priority_score": f.priority_score,
                    "suggestions": f.suggestions,
                    "auto_fix_available": f.auto_fix_available
                }
                for f in prioritized_feedback
            ],
            "spec_mapping": {
                "direct_mappings_count": len(spec_mapping["direct_mappings"]),
                "indirect_mappings_count": len(spec_mapping["indirect_mappings"]),
                "unmapped_count": len(spec_mapping["unmapped_failures"]),
                "details": spec_mapping
            },
            "impact_analysis": {
                "affected_elements_count": len(impact_analysis["by_spec_element"]),
                "critical_elements_count": len(impact_analysis["critical_spec_elements"]),
                "affected_constraints_count": len(impact_analysis["affected_constraints"]),
                "details": impact_analysis
            },
            "fix_recommendations": fix_recommendations,
            "spec_update_hints": spec_update_hints,
            "summary": {
                "total_feedback_items": len(prioritized_feedback),
                "high_priority_count": len([f for f in prioritized_feedback if f.priority_score >= 50]),
                "auto_fixable_count": len([f for f in prioritized_feedback if f.auto_fix_available]),
                "spec_updates_needed": len(spec_update_hints)
            }
        }


class SpecImprovementSuggester:
    """规范改进建议生成器"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or self._setup_logger()
        self.suggestion_counter = 0
        self._suggestion_history: Dict[str, List[SpecImprovementSuggestion]] = {}
        self._dependency_graph: Dict[str, List[str]] = {}
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger("SpecImprovementSuggester")
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def generate_suggestions(
        self,
        test_results: List[TestResult],
        failure_analyses: List[FailureAnalysis],
        spec: Optional[Dict[str, Any]] = None
    ) -> List[SpecImprovementSuggestion]:
        suggestions = []
        
        for analysis in failure_analyses:
            suggestion = self._create_suggestion_from_analysis(analysis, spec)
            if suggestion:
                suggestions.append(suggestion)
        
        pattern_suggestions = self._analyze_failure_patterns(test_results, failure_analyses)
        suggestions.extend(pattern_suggestions)
        
        if spec:
            coverage_suggestions = self._analyze_spec_coverage(test_results, spec)
            suggestions.extend(coverage_suggestions)
        
        suggestions = self._deduplicate_suggestions(suggestions)
        
        for suggestion in suggestions:
            self._enrich_with_context(suggestion, spec, failure_analyses)
            self._analyze_dependencies(suggestion, spec)
            self._calculate_auto_priority(suggestion, test_results)
            self._assess_risk(suggestion, spec)
        
        suggestions.sort(key=lambda x: x.priority, reverse=True)
        
        self._update_suggestion_history(suggestions)
        
        self.logger.info(f"生成了 {len(suggestions)} 条规范改进建议")
        return suggestions
    
    def generate_suggestions_advanced(
        self,
        test_results: List[TestResult],
        failure_analyses: List[FailureAnalysis],
        spec: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> List[SpecImprovementSuggestion]:
        suggestions = self.generate_suggestions(test_results, failure_analyses, spec)
        
        if context:
            for suggestion in suggestions:
                self._apply_context_awareness(suggestion, context)
        
        suggestions = self._find_related_suggestions(suggestions)
        
        for suggestion in suggestions:
            self._generate_implementation_hints(suggestion, spec, context)
            self._check_auto_applicability(suggestion)
        
        return suggestions
    
    def _create_suggestion_from_analysis(
        self,
        analysis: FailureAnalysis,
        spec: Optional[Dict[str, Any]]
    ) -> Optional[SpecImprovementSuggestion]:
        self.suggestion_counter += 1
        suggestion_id = f"SUG-{datetime.now().strftime('%Y%m%d%H%M%S')}-{self.suggestion_counter:03d}"
        
        suggestion_type = self._determine_suggestion_type(analysis)
        
        if suggestion_type == SuggestionType.SPEC_UPDATE:
            return SpecImprovementSuggestion(
                suggestion_id=suggestion_id,
                suggestion_type=suggestion_type,
                spec_element=analysis.related_spec_element,
                current_value="当前定义",
                suggested_value=self._generate_spec_update(analysis),
                reason=f"基于测试失败分析: {analysis.root_cause}",
                priority=self._calculate_priority(analysis),
                test_evidence=[analysis.test_id],
                confidence_score=analysis.confidence
            )
        elif suggestion_type == SuggestionType.SPEC_ADDITION:
            return SpecImprovementSuggestion(
                suggestion_id=suggestion_id,
                suggestion_type=suggestion_type,
                spec_element=analysis.related_spec_element,
                current_value="未定义",
                suggested_value=self._generate_spec_addition(analysis),
                reason="测试覆盖了规范中未明确定义的行为",
                priority=self._calculate_priority(analysis),
                test_evidence=[analysis.test_id],
                confidence_score=analysis.confidence
            )
        elif suggestion_type == SuggestionType.SPEC_CLARIFICATION:
            return SpecImprovementSuggestion(
                suggestion_id=suggestion_id,
                suggestion_type=suggestion_type,
                spec_element=analysis.related_spec_element,
                current_value="定义不清晰",
                suggested_value=self._generate_clarification(analysis),
                reason="测试失败表明规范定义不够清晰",
                priority=self._calculate_priority(analysis) - 1,
                test_evidence=[analysis.test_id],
                confidence_score=analysis.confidence
            )
        
        return None
    
    def _enrich_with_context(
        self,
        suggestion: SpecImprovementSuggestion,
        spec: Optional[Dict[str, Any]],
        failure_analyses: List[FailureAnalysis]
    ) -> None:
        if not spec:
            return
        
        element = suggestion.spec_element
        
        spec_element = self._find_spec_element(element, spec)
        if spec_element:
            suggestion.context_aware = True
            suggestion.details = suggestion.details if hasattr(suggestion, 'details') else {}
            suggestion.details["spec_context"] = {
                "type": spec_element.get("type", "unknown"),
                "location": spec_element.get("location", ""),
                "related_elements": spec_element.get("related_elements", [])
            }
        
        related_analyses = [
            a for a in failure_analyses 
            if a.related_spec_element == element
        ]
        if len(related_analyses) > 1:
            suggestion.test_evidence.extend(
                [a.test_id for a in related_analyses if a.test_id not in suggestion.test_evidence]
            )
    
    def _find_spec_element(
        self, 
        element: str, 
        spec: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        for iface in spec.get("interfaces", []):
            if iface.get("name", "").lower() == element.lower():
                return {"type": "interface", **iface}
        
        for model in spec.get("data_models", []):
            if model.get("name", "").lower() == element.lower():
                return {"type": "data_model", **model}
        
        for rule in spec.get("behavior_rules", []):
            if rule.get("name", "").lower() == element.lower():
                return {"type": "behavior_rule", **rule}
        
        return None
    
    def _analyze_dependencies(
        self,
        suggestion: SpecImprovementSuggestion,
        spec: Optional[Dict[str, Any]]
    ) -> None:
        if not spec:
            return
        
        element = suggestion.spec_element
        dependencies = []
        
        for iface in spec.get("interfaces", []):
            if element.lower() in str(iface.get("parameters", [])).lower():
                dependencies.append(iface.get("name", ""))
        
        for model in spec.get("data_models", []):
            attrs = str(model.get("attributes", []))
            if element.lower() in attrs.lower():
                dependencies.append(model.get("name", ""))
        
        for rule in spec.get("behavior_rules", []):
            condition = rule.get("condition", "")
            action = rule.get("action", "")
            if element.lower() in condition.lower() or element.lower() in action.lower():
                dependencies.append(rule.get("name", ""))
        
        suggestion.dependencies = list(set(dependencies))
        
        self._dependency_graph[element] = suggestion.dependencies
    
    def _calculate_auto_priority(
        self,
        suggestion: SpecImprovementSuggestion,
        test_results: List[TestResult]
    ) -> None:
        base_priority = suggestion.priority
        
        evidence_count = len(suggestion.test_evidence)
        evidence_bonus = min(evidence_count * 2, 10)
        
        dependency_penalty = len(suggestion.dependencies) * 2
        
        confidence_bonus = int(suggestion.confidence_score * 5)
        
        auto_priority = base_priority + evidence_bonus - dependency_penalty + confidence_bonus
        
        if suggestion.suggestion_type == SuggestionType.SPEC_ADDITION:
            auto_priority += 2
        elif suggestion.suggestion_type == SuggestionType.SPEC_CLARIFICATION:
            auto_priority -= 1
        
        suggestion.priority = max(1, min(10, auto_priority))
    
    def _assess_risk(
        self,
        suggestion: SpecImprovementSuggestion,
        spec: Optional[Dict[str, Any]]
    ) -> None:
        risk_factors = []
        
        if len(suggestion.dependencies) > 3:
            risk_factors.append("high_dependency_count")
        
        if suggestion.suggestion_type == SuggestionType.SPEC_REMOVAL:
            risk_factors.append("removal_operation")
        
        if suggestion.suggestion_type == SuggestionType.SPEC_UPDATE:
            risk_factors.append("update_operation")
        
        if suggestion.context_aware and suggestion.details.get("spec_context", {}).get("type") == "interface":
            risk_factors.append("interface_change")
        
        if len(risk_factors) >= 3:
            suggestion.risk_assessment = "high"
        elif len(risk_factors) >= 1:
            suggestion.risk_assessment = "medium"
        else:
            suggestion.risk_assessment = "low"
    
    def _apply_context_awareness(
        self,
        suggestion: SpecImprovementSuggestion,
        context: Dict[str, Any]
    ) -> None:
        project_phase = context.get("project_phase", "development")
        
        if project_phase == "production":
            if suggestion.risk_assessment == "high":
                suggestion.priority -= 2
        elif project_phase == "development":
            if suggestion.suggestion_type == SuggestionType.SPEC_ADDITION:
                suggestion.priority += 1
        
        team_size = context.get("team_size", 1)
        if team_size > 5 and len(suggestion.dependencies) > 2:
            suggestion.risk_assessment = "high"
        
        deadline = context.get("deadline")
        if deadline:
            suggestion.implementation_hints.append(
                f"建议在截止日期前优先处理优先级 >= 7 的建议"
            )
    
    def _find_related_suggestions(
        self,
        suggestions: List[SpecImprovementSuggestion]
    ) -> List[SpecImprovementSuggestion]:
        element_to_suggestions: Dict[str, List[str]] = {}
        
        for suggestion in suggestions:
            element = suggestion.spec_element
            if element not in element_to_suggestions:
                element_to_suggestions[element] = []
            element_to_suggestions[element].append(suggestion.suggestion_id)
        
        for suggestion in suggestions:
            related = []
            
            for dep in suggestion.dependencies:
                if dep in element_to_suggestions:
                    related.extend(element_to_suggestions[dep])
            
            if suggestion.spec_element in element_to_suggestions:
                for sid in element_to_suggestions[suggestion.spec_element]:
                    if sid != suggestion.suggestion_id:
                        related.append(sid)
            
            suggestion.related_suggestions = list(set(related))[:5]
        
        return suggestions
    
    def _generate_implementation_hints(
        self,
        suggestion: SpecImprovementSuggestion,
        spec: Optional[Dict[str, Any]],
        context: Optional[Dict[str, Any]]
    ) -> None:
        hints = []
        
        if suggestion.suggestion_type == SuggestionType.SPEC_ADDITION:
            hints.append("建议先添加规范定义，再更新相关文档")
            hints.append("确保新定义与现有规范风格一致")
        
        elif suggestion.suggestion_type == SuggestionType.SPEC_UPDATE:
            hints.append("更新规范前，检查是否有依赖该定义的其他规范")
            if suggestion.dependencies:
                hints.append(f"注意：该变更可能影响 {len(suggestion.dependencies)} 个相关元素")
        
        elif suggestion.suggestion_type == SuggestionType.SPEC_CLARIFICATION:
            hints.append("建议添加示例说明以增强清晰度")
            hints.append("考虑添加边界条件说明")
        
        if suggestion.risk_assessment == "high":
            hints.append("高风险变更：建议进行团队评审")
        
        if context and context.get("code_review_required"):
            hints.append("该变更需要代码审查")
        
        suggestion.implementation_hints = hints
    
    def _check_auto_applicability(
        self,
        suggestion: SpecImprovementSuggestion
    ) -> None:
        auto_applicable_types = [
            SuggestionType.SPEC_CLARIFICATION,
        ]
        
        if suggestion.suggestion_type in auto_applicable_types:
            if suggestion.risk_assessment == "low":
                suggestion.auto_applicable = True
        
        if (suggestion.suggestion_type == SuggestionType.SPEC_ADDITION and
            len(suggestion.dependencies) == 0 and
            suggestion.confidence_score >= 0.8):
            suggestion.auto_applicable = True
    
    def _update_suggestion_history(
        self, 
        suggestions: List[SpecImprovementSuggestion]
    ) -> None:
        for suggestion in suggestions:
            element = suggestion.spec_element
            if element not in self._suggestion_history:
                self._suggestion_history[element] = []
            self._suggestion_history[element].append(suggestion)
            
            if len(self._suggestion_history[element]) > 20:
                self._suggestion_history[element] = self._suggestion_history[element][-20:]
    
    def _determine_suggestion_type(self, analysis: FailureAnalysis) -> SuggestionType:
        if analysis.category == FailureCategory.ASSERTION:
            return SuggestionType.SPEC_UPDATE
        elif analysis.category in [FailureCategory.EXCEPTION, FailureCategory.VALUE]:
            return SuggestionType.SPEC_ADDITION
        elif analysis.category in [FailureCategory.TYPE, FailureCategory.ATTRIBUTE]:
            return SuggestionType.SPEC_CLARIFICATION
        else:
            return SuggestionType.SPEC_UPDATE
    
    def _generate_spec_update(self, analysis: FailureAnalysis) -> str:
        updates = []
        
        if analysis.category == FailureCategory.ASSERTION:
            updates.append("更新预期结果定义")
            updates.append("明确边界条件")
        
        if "None" in analysis.error_message:
            updates.append("添加空值处理说明")
        
        if not updates:
            updates.append("根据测试结果更新规范定义")
        
        return "; ".join(updates)
    
    def _generate_spec_addition(self, analysis: FailureAnalysis) -> str:
        additions = []
        
        if analysis.category == FailureCategory.EXCEPTION:
            additions.append("添加异常处理规范")
            additions.append(f"定义异常: {analysis.error_message[:100]}")
        
        if analysis.category == FailureCategory.VALUE:
            additions.append("添加值验证规则")
            additions.append("定义有效值范围")
        
        if not additions:
            additions.append("补充规范定义以覆盖测试场景")
        
        return "; ".join(additions)
    
    def _generate_clarification(self, analysis: FailureAnalysis) -> str:
        clarifications = []
        
        if analysis.category == FailureCategory.TYPE:
            clarifications.append("明确数据类型定义")
            clarifications.append("添加类型约束说明")
        
        if analysis.category == FailureCategory.ATTRIBUTE:
            clarifications.append("明确接口属性定义")
            clarifications.append("添加属性访问说明")
        
        if not clarifications:
            clarifications.append("提供更详细的规范说明")
        
        return "; ".join(clarifications)
    
    def _calculate_priority(self, analysis: FailureAnalysis) -> int:
        priority = 5
        
        if analysis.confidence >= 0.8:
            priority += 2
        elif analysis.confidence >= 0.6:
            priority += 1
        
        if analysis.category in [FailureCategory.EXCEPTION, FailureCategory.ASSERTION]:
            priority += 1
        
        return min(10, priority)
    
    def _analyze_failure_patterns(
        self,
        test_results: List[TestResult],
        failure_analyses: List[FailureAnalysis]
    ) -> List[SpecImprovementSuggestion]:
        suggestions = []
        
        category_counts = {}
        for analysis in failure_analyses:
            category = analysis.category
            category_counts[category] = category_counts.get(category, 0) + 1
        
        for category, count in category_counts.items():
            if count >= 3:
                self.suggestion_counter += 1
                suggestion_id = f"SUG-{datetime.now().strftime('%Y%m%d%H%M%S')}-{self.suggestion_counter:03d}"
                
                suggestions.append(SpecImprovementSuggestion(
                    suggestion_id=suggestion_id,
                    suggestion_type=SuggestionType.SPEC_UPDATE,
                    spec_element="整体规范",
                    current_value="当前定义",
                    suggested_value=f"加强 {category.value} 相关的规范定义",
                    reason=f"发现 {count} 个相同类型的失败，表明规范在该方面定义不足",
                    priority=7,
                    test_evidence=[a.test_id for a in failure_analyses if a.category == category][:5]
                ))
        
        return suggestions
    
    def _analyze_spec_coverage(
        self,
        test_results: List[TestResult],
        spec: Dict[str, Any]
    ) -> List[SpecImprovementSuggestion]:
        suggestions = []
        
        spec_elements = set()
        
        if "interfaces" in spec:
            for iface in spec["interfaces"]:
                spec_elements.add(iface.get("name", ""))
        
        if "data_models" in spec:
            for model in spec["data_models"]:
                spec_elements.add(model.get("name", ""))
        
        if "behavior_rules" in spec:
            for rule in spec["behavior_rules"]:
                spec_elements.add(rule.get("name", ""))
        
        tested_elements = set()
        for test in test_results:
            test_name = test.test_name.lower()
            for element in spec_elements:
                if element.lower() in test_name:
                    tested_elements.add(element)
        
        untested = spec_elements - tested_elements
        if untested:
            self.suggestion_counter += 1
            suggestion_id = f"SUG-{datetime.now().strftime('%Y%m%d%H%M%S')}-{self.suggestion_counter:03d}"
            
            suggestions.append(SpecImprovementSuggestion(
                suggestion_id=suggestion_id,
                suggestion_type=SuggestionType.SPEC_ADDITION,
                spec_element="测试覆盖",
                current_value="当前测试覆盖",
                suggested_value=f"为以下元素添加测试: {', '.join(list(untested)[:5])}",
                reason="规范元素缺少测试覆盖",
                priority=6,
                test_evidence=[]
            ))
        
        return suggestions
    
    def _deduplicate_suggestions(
        self,
        suggestions: List[SpecImprovementSuggestion]
    ) -> List[SpecImprovementSuggestion]:
        seen = set()
        unique = []
        
        for suggestion in suggestions:
            key = (suggestion.spec_element, suggestion.suggestion_type, suggestion.suggested_value[:50])
            if key not in seen:
                seen.add(key)
                unique.append(suggestion)
        
        return unique
    
    def generate_enhanced_suggestions(
        self,
        test_results: List[TestResult],
        failure_analyses: List[FailureAnalysis],
        spec: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        生成增强的规范改进建议
        
        该方法提供更全面的规范改进建议，包括：
        - 智能建议分类：根据失败类型智能分类建议
        - 影响范围评估：评估建议对规范的影响范围
        - 实施优先级排序：根据影响和可行性排序
        - 风险评估：评估实施建议的风险
        - 实施路径建议：提供具体的实施步骤
        
        参数:
            test_results: 测试结果列表
            failure_analyses: 失败分析列表
            spec: 规范字典
            context: 上下文信息
            
        返回:
            包含增强建议结果的字典
        """
        self.logger.info("开始生成增强的规范改进建议...")
        
        basic_suggestions = self.generate_suggestions_advanced(
            test_results, failure_analyses, spec, context
        )
        
        categorized_suggestions = self._categorize_suggestions_intelligently(
            basic_suggestions, failure_analyses
        )
        
        impact_assessment = self._assess_suggestion_impact(
            basic_suggestions, spec
        )
        
        prioritized_suggestions = self._prioritize_suggestions_by_impact(
            basic_suggestions, impact_assessment
        )
        
        risk_assessment = self._assess_implementation_risks(
            basic_suggestions, spec
        )
        
        implementation_paths = self._generate_implementation_paths(
            basic_suggestions, spec, risk_assessment
        )
        
        return {
            "suggestions": [
                {
                    "suggestion_id": s.suggestion_id,
                    "suggestion_type": s.suggestion_type.value,
                    "spec_element": s.spec_element,
                    "current_value": s.current_value,
                    "suggested_value": s.suggested_value,
                    "reason": s.reason,
                    "priority": s.priority,
                    "confidence_score": s.confidence_score,
                    "auto_applicable": s.auto_applicable,
                    "risk_assessment": s.risk_assessment,
                    "dependencies": s.dependencies
                }
                for s in prioritized_suggestions
            ],
            "categorization": categorized_suggestions,
            "impact_assessment": impact_assessment,
            "risk_assessment": risk_assessment,
            "implementation_paths": implementation_paths,
            "summary": self._generate_suggestion_summary(
                prioritized_suggestions, impact_assessment, risk_assessment
            )
        }
    
    def _categorize_suggestions_intelligently(
        self,
        suggestions: List[SpecImprovementSuggestion],
        failure_analyses: List[FailureAnalysis]
    ) -> Dict[str, Any]:
        """智能分类建议"""
        categories = {
            "interface_updates": [],
            "data_model_updates": [],
            "behavior_rule_updates": [],
            "constraint_additions": [],
            "documentation_improvements": [],
            "clarification_needed": []
        }
        
        for suggestion in suggestions:
            if suggestion.suggestion_type == SuggestionType.SPEC_UPDATE:
                if "interface" in suggestion.spec_element.lower():
                    categories["interface_updates"].append(suggestion.suggestion_id)
                elif "model" in suggestion.spec_element.lower():
                    categories["data_model_updates"].append(suggestion.suggestion_id)
                else:
                    categories["behavior_rule_updates"].append(suggestion.suggestion_id)
            
            elif suggestion.suggestion_type == SuggestionType.SPEC_ADDITION:
                if "constraint" in suggestion.suggested_value.lower():
                    categories["constraint_additions"].append(suggestion.suggestion_id)
                else:
                    categories["behavior_rule_updates"].append(suggestion.suggestion_id)
            
            elif suggestion.suggestion_type == SuggestionType.SPEC_CLARIFICATION:
                categories["clarification_needed"].append(suggestion.suggestion_id)
        
        for category, ids in categories.items():
            categories[category] = {
                "count": len(ids),
                "suggestion_ids": ids,
                "avg_priority": sum(
                    s.priority for s in suggestions if s.suggestion_id in ids
                ) / len(ids) if ids else 0
            }
        
        return categories
    
    def _assess_suggestion_impact(
        self,
        suggestions: List[SpecImprovementSuggestion],
        spec: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """评估建议的影响"""
        impact = {
            "by_suggestion": {},
            "high_impact_suggestions": [],
            "breaking_changes": [],
            "backward_compatible": []
        }
        
        for suggestion in suggestions:
            suggestion_impact = {
                "scope": "local",
                "affected_elements": [],
                "breaking": False,
                "effort_estimate": "low"
            }
            
            if len(suggestion.dependencies) > 2:
                suggestion_impact["scope"] = "wide"
                suggestion_impact["affected_elements"] = suggestion.dependencies
            
            if suggestion.suggestion_type == SuggestionType.SPEC_REMOVAL:
                suggestion_impact["breaking"] = True
                impact["breaking_changes"].append(suggestion.suggestion_id)
            elif suggestion.suggestion_type == SuggestionType.SPEC_UPDATE:
                if suggestion.risk_assessment == "high":
                    suggestion_impact["breaking"] = True
                    impact["breaking_changes"].append(suggestion.suggestion_id)
                else:
                    impact["backward_compatible"].append(suggestion.suggestion_id)
            else:
                impact["backward_compatible"].append(suggestion.suggestion_id)
            
            if suggestion.priority >= 7:
                suggestion_impact["effort_estimate"] = "high"
            elif suggestion.priority >= 4:
                suggestion_impact["effort_estimate"] = "medium"
            
            impact["by_suggestion"][suggestion.suggestion_id] = suggestion_impact
            
            if suggestion_impact["scope"] == "wide" or suggestion_impact["breaking"]:
                impact["high_impact_suggestions"].append({
                    "suggestion_id": suggestion.suggestion_id,
                    "spec_element": suggestion.spec_element,
                    "reason": "wide_scope" if suggestion_impact["scope"] == "wide" else "breaking_change"
                })
        
        return impact
    
    def _prioritize_suggestions_by_impact(
        self,
        suggestions: List[SpecImprovementSuggestion],
        impact_assessment: Dict[str, Any]
    ) -> List[SpecImprovementSuggestion]:
        """根据影响排序建议"""
        for suggestion in suggestions:
            impact_info = impact_assessment.get("by_suggestion", {}).get(suggestion.suggestion_id, {})
            
            if impact_info.get("breaking", False):
                suggestion.priority -= 2
            
            if impact_info.get("scope") == "wide":
                suggestion.priority += 1
            
            if suggestion.confidence_score >= 0.8:
                suggestion.priority += 1
            
            suggestion.priority = max(1, min(10, suggestion.priority))
        
        return sorted(suggestions, key=lambda x: (x.priority, x.confidence_score), reverse=True)
    
    def _assess_implementation_risks(
        self,
        suggestions: List[SpecImprovementSuggestion],
        spec: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """评估实施风险"""
        risks = {
            "overall_risk_level": "low",
            "risk_factors": [],
            "mitigation_strategies": [],
            "by_suggestion": {}
        }
        
        breaking_count = len([s for s in suggestions if s.risk_assessment == "high"])
        high_dependency_count = len([s for s in suggestions if len(s.dependencies) > 3])
        
        if breaking_count > 3 or high_dependency_count > 5:
            risks["overall_risk_level"] = "high"
        elif breaking_count > 0 or high_dependency_count > 2:
            risks["overall_risk_level"] = "medium"
        
        for suggestion in suggestions:
            suggestion_risks = []
            
            if suggestion.risk_assessment == "high":
                suggestion_risks.append("高风险变更类型")
            
            if len(suggestion.dependencies) > 3:
                suggestion_risks.append(f"影响 {len(suggestion.dependencies)} 个依赖元素")
            
            if suggestion.confidence_score < 0.5:
                suggestion_risks.append("置信度较低")
            
            if not suggestion.test_evidence:
                suggestion_risks.append("缺少测试证据")
            
            risks["by_suggestion"][suggestion.suggestion_id] = {
                "risk_level": "high" if len(suggestion_risks) >= 2 else "medium" if suggestion_risks else "low",
                "risk_factors": suggestion_risks
            }
        
        if risks["overall_risk_level"] in ["medium", "high"]:
            risks["mitigation_strategies"] = [
                "建议分阶段实施变更",
                "每个变更后运行完整测试套件",
                "保持规范的版本控制",
                "进行同行评审"
            ]
        
        return risks
    
    def _generate_implementation_paths(
        self,
        suggestions: List[SpecImprovementSuggestion],
        spec: Optional[Dict[str, Any]],
        risk_assessment: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """生成实施路径"""
        paths = []
        
        auto_applicable = [s for s in suggestions if s.auto_applicable]
        if auto_applicable:
            paths.append({
                "phase": "auto_apply",
                "description": "自动应用低风险变更",
                "suggestions": [s.suggestion_id for s in auto_applicable],
                "estimated_effort": "low",
                "order": 1
            })
        
        high_priority = [
            s for s in suggestions 
            if s.priority >= 7 and not s.auto_applicable and s.risk_assessment != "high"
        ]
        if high_priority:
            paths.append({
                "phase": "high_priority",
                "description": "处理高优先级建议",
                "suggestions": [s.suggestion_id for s in high_priority],
                "estimated_effort": "medium",
                "order": 2
            })
        
        breaking_changes = [
            s for s in suggestions if s.risk_assessment == "high"
        ]
        if breaking_changes:
            paths.append({
                "phase": "breaking_changes",
                "description": "处理破坏性变更（需要仔细规划）",
                "suggestions": [s.suggestion_id for s in breaking_changes],
                "estimated_effort": "high",
                "order": 3,
                "requires_review": True
            })
        
        remaining = [
            s for s in suggestions 
            if s.suggestion_id not in [sid for p in paths for sid in p["suggestions"]]
        ]
        if remaining:
            paths.append({
                "phase": "remaining",
                "description": "处理剩余建议",
                "suggestions": [s.suggestion_id for s in remaining],
                "estimated_effort": "medium",
                "order": 4
            })
        
        return sorted(paths, key=lambda x: x["order"])
    
    def _generate_suggestion_summary(
        self,
        suggestions: List[SpecImprovementSuggestion],
        impact_assessment: Dict[str, Any],
        risk_assessment: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成建议摘要"""
        return {
            "total_suggestions": len(suggestions),
            "by_type": {
                "update": len([s for s in suggestions if s.suggestion_type == SuggestionType.SPEC_UPDATE]),
                "addition": len([s for s in suggestions if s.suggestion_type == SuggestionType.SPEC_ADDITION]),
                "removal": len([s for s in suggestions if s.suggestion_type == SuggestionType.SPEC_REMOVAL]),
                "clarification": len([s for s in suggestions if s.suggestion_type == SuggestionType.SPEC_CLARIFICATION])
            },
            "by_priority": {
                "high": len([s for s in suggestions if s.priority >= 7]),
                "medium": len([s for s in suggestions if 4 <= s.priority < 7]),
                "low": len([s for s in suggestions if s.priority < 4])
            },
            "auto_applicable_count": len([s for s in suggestions if s.auto_applicable]),
            "breaking_changes_count": len(impact_assessment.get("breaking_changes", [])),
            "overall_risk_level": risk_assessment.get("overall_risk_level", "unknown"),
            "recommended_action": self._get_recommended_action(suggestions, risk_assessment)
        }
    
    def _get_recommended_action(
        self,
        suggestions: List[SpecImprovementSuggestion],
        risk_assessment: Dict[str, Any]
    ) -> str:
        """获取推荐行动"""
        if risk_assessment.get("overall_risk_level") == "high":
            return "建议先进行风险评估和团队讨论，再逐步实施变更"
        elif len([s for s in suggestions if s.priority >= 7]) > 3:
            return "建议优先处理高优先级建议，然后运行测试验证"
        elif len([s for s in suggestions if s.auto_applicable]) > 0:
            return "可以自动应用部分建议，然后手动处理其余建议"
        else:
            return "建议按优先级顺序逐步实施变更"


class SpecCodeSyncValidator:
    """规范与代码同步验证器"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or self._setup_logger()
        self.issue_counter = 0
        self._validation_cache: Dict[str, Any] = {}
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger("SpecCodeSyncValidator")
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def validate_sync(
        self,
        spec: Dict[str, Any],
        code_dir: str
    ) -> SyncReport:
        code_path = Path(code_dir)
        if not code_path.exists():
            raise FileNotFoundError(f"代码目录不存在: {code_dir}")
        
        spec_id = spec.get("id", spec.get("spec_id", "unknown"))
        
        code_elements = self._extract_code_elements(code_path)
        
        spec_elements = self._extract_spec_elements(spec)
        
        issues = self._compare_elements(spec_elements, code_elements)
        
        issues.extend(self._validate_parameter_signatures(spec_elements, code_elements))
        issues.extend(self._validate_return_types(spec_elements, code_elements))
        issues.extend(self._validate_documentation_consistency(spec_elements, code_elements, code_path))
        
        checked = len(spec_elements)
        matched = checked - len(set(i.spec_element for i in issues if i.severity in [FeedbackSeverity.HIGH, FeedbackSeverity.CRITICAL]))
        
        sync_percentage = (matched / checked * 100) if checked > 0 else 100
        
        if sync_percentage >= 90:
            status = SyncStatus.IN_SYNC
        elif sync_percentage >= 70:
            status = SyncStatus.PARTIAL
        else:
            status = SyncStatus.OUT_OF_SYNC
        
        report_id = f"SYNC-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        return SyncReport(
            report_id=report_id,
            spec_id=spec_id,
            status=status,
            sync_percentage=sync_percentage,
            issues=issues,
            checked_elements=checked,
            matched_elements=matched
        )
    
    def validate_sync_advanced(
        self,
        spec: Dict[str, Any],
        code_dir: str,
        options: Optional[Dict[str, Any]] = None
    ) -> SyncReport:
        report = self.validate_sync(spec, code_dir)
        
        if options is None:
            options = {}
        
        code_path = Path(code_dir)
        code_elements = self._extract_code_elements(code_path)
        spec_elements = self._extract_spec_elements(spec)
        
        if options.get("check_type_hints", True):
            type_issues = self._validate_type_hints(spec_elements, code_elements)
            report.issues.extend(type_issues)
        
        if options.get("check_naming_conventions", True):
            naming_issues = self._validate_naming_conventions(spec_elements, code_elements)
            report.issues.extend(naming_issues)
        
        if options.get("check_deprecation", False):
            deprecation_issues = self._check_deprecation_status(spec_elements, code_elements)
            report.issues.extend(deprecation_issues)
        
        for issue in report.issues:
            self._check_issue_auto_fix(issue, spec_elements, code_elements)
        
        report.checked_elements = len(spec_elements)
        report.matched_elements = report.checked_elements - len(
            set(i.spec_element for i in report.issues if i.severity in [FeedbackSeverity.HIGH, FeedbackSeverity.CRITICAL])
        )
        report.sync_percentage = (report.matched_elements / report.checked_elements * 100) if report.checked_elements > 0 else 100
        
        return report
    
    def _extract_code_elements(self, code_dir: Path) -> Dict[str, Any]:
        elements = {
            "functions": [],
            "classes": [],
            "methods": [],
            "variables": [],
            "type_hints": {},
            "docstrings": {}
        }
        
        for py_file in code_dir.rglob("*.py"):
            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()
                
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        func_info = {
                            "name": node.name,
                            "file": str(py_file),
                            "line": node.lineno,
                            "args": self._extract_args_info(node),
                            "returns": self._get_annotation(node.returns),
                            "docstring": ast.get_docstring(node) or "",
                            "decorators": [d.id if isinstance(d, ast.Name) else str(d) for d in node.decorator_list]
                        }
                        elements["functions"].append(func_info)
                        
                        doc_key = f"{py_file}::{node.name}"
                        elements["docstrings"][doc_key] = func_info["docstring"]
                        
                    elif isinstance(node, ast.ClassDef):
                        class_info = {
                            "name": node.name,
                            "file": str(py_file),
                            "line": node.lineno,
                            "methods": [],
                            "attributes": [],
                            "docstring": ast.get_docstring(node) or "",
                            "bases": [self._get_annotation(b) for b in node.bases]
                        }
                        
                        for item in node.body:
                            if isinstance(item, ast.FunctionDef):
                                class_info["methods"].append({
                                    "name": item.name,
                                    "args": self._extract_args_info(item),
                                    "returns": self._get_annotation(item.returns),
                                    "docstring": ast.get_docstring(item) or ""
                                })
                            elif isinstance(item, ast.AnnAssign) and item.target:
                                class_info["attributes"].append({
                                    "name": item.target.id if isinstance(item.target, ast.Name) else str(item.target),
                                    "type": self._get_annotation(item.annotation)
                                })
                        
                        elements["classes"].append(class_info)
                        
                        doc_key = f"{py_file}::{node.name}"
                        elements["docstrings"][doc_key] = class_info["docstring"]
                        
            except SyntaxError:
                self.logger.warning(f"无法解析文件: {py_file}")
            except Exception as e:
                self.logger.error(f"解析文件时出错 {py_file}: {e}")
        
        return elements
    
    def _extract_args_info(self, node: ast.FunctionDef) -> List[Dict[str, Any]]:
        args_info = []
        
        for arg in node.args.args:
            arg_info = {
                "name": arg.arg,
                "type": self._get_annotation(arg.annotation),
                "default": None
            }
            args_info.append(arg_info)
        
        defaults = node.args.defaults
        if defaults:
            for i, default in enumerate(defaults):
                arg_idx = len(node.args.args) - len(defaults) + i
                if arg_idx < len(args_info):
                    args_info[arg_idx]["default"] = self._get_annotation(default)
        
        return args_info
    
    def _get_annotation(self, node) -> str:
        if node is None:
            return "None"
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Constant):
            return str(node.value)
        if isinstance(node, ast.Subscript):
            if isinstance(node.value, ast.Name):
                return f"{node.value.id}[{self._get_annotation(node.slice)}]"
        if isinstance(node, ast.Attribute):
            return f"{self._get_annotation(node.value)}.{node.attr}"
        if isinstance(node, ast.Tuple):
            return ", ".join(self._get_annotation(el) for el in node.elts)
        return "unknown"
    
    def _extract_spec_elements(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        elements = {
            "interfaces": [],
            "data_models": [],
            "functions": [],
            "constraints": [],
            "deprecated": []
        }
        
        for iface in spec.get("interfaces", []):
            elements["interfaces"].append({
                "name": iface.get("name", ""),
                "parameters": iface.get("parameters", []),
                "return_type": iface.get("return_type", ""),
                "description": iface.get("description", ""),
                "deprecated": iface.get("deprecated", False),
                "deprecation_message": iface.get("deprecation_message", "")
            })
        
        for model in spec.get("data_models", []):
            elements["data_models"].append({
                "name": model.get("name", ""),
                "attributes": model.get("attributes", []),
                "description": model.get("description", ""),
                "deprecated": model.get("deprecated", False)
            })
        
        for rule in spec.get("behavior_rules", []):
            elements["functions"].append({
                "name": rule.get("name", ""),
                "condition": rule.get("condition", ""),
                "action": rule.get("action", ""),
                "description": rule.get("description", "")
            })
        
        for constraint in spec.get("constraints", []):
            elements["constraints"].append({
                "name": constraint.get("name", ""),
                "rule": constraint.get("rule", ""),
                "description": constraint.get("description", "")
            })
        
        return elements
    
    def _validate_parameter_signatures(
        self,
        spec_elements: Dict[str, Any],
        code_elements: Dict[str, Any]
    ) -> List[SyncIssue]:
        issues = []
        
        code_functions = {f["name"]: f for f in code_elements.get("functions", [])}
        
        for iface in spec_elements.get("interfaces", []):
            iface_name = iface.get("name", "")
            spec_params = iface.get("parameters", [])
            
            if iface_name in code_functions:
                code_func = code_functions[iface_name]
                code_args = code_func.get("args", [])
                
                param_issues = self._compare_parameters(
                    iface_name, spec_params, code_args
                )
                issues.extend(param_issues)
        
        return issues
    
    def _compare_parameters(
        self,
        func_name: str,
        spec_params: List[Dict[str, Any]],
        code_args: List[Dict[str, Any]]
    ) -> List[SyncIssue]:
        issues = []
        
        spec_param_names = {p.get("name", p) if isinstance(p, str) else p.get("name", "") for p in spec_params}
        code_arg_names = {a.get("name", "") for a in code_args}
        
        missing_in_code = spec_param_names - code_arg_names
        if missing_in_code:
            self.issue_counter += 1
            issues.append(SyncIssue(
                issue_id=f"ISSUE-{self.issue_counter:03d}",
                issue_type="missing_parameters",
                spec_element=func_name,
                code_element=func_name,
                description=f"函数 '{func_name}' 缺少参数: {', '.join(missing_in_code)}",
                severity=FeedbackSeverity.HIGH,
                suggestion=f"添加缺失的参数: {', '.join(missing_in_code)}",
                parameter_mismatch={"missing": list(missing_in_code)}
            ))
        
        extra_in_code = code_arg_names - spec_param_names
        if extra_in_code:
            self.issue_counter += 1
            issues.append(SyncIssue(
                issue_id=f"ISSUE-{self.issue_counter:03d}",
                issue_type="extra_parameters",
                spec_element=func_name,
                code_element=func_name,
                description=f"函数 '{func_name}' 有额外参数: {', '.join(extra_in_code)}",
                severity=FeedbackSeverity.MEDIUM,
                suggestion=f"检查是否需要更新规范以包含这些参数",
                parameter_mismatch={"extra": list(extra_in_code)}
            ))
        
        for spec_param in spec_params:
            param_name = spec_param.get("name", "") if isinstance(spec_param, dict) else spec_param
            spec_type = spec_param.get("type", "") if isinstance(spec_param, dict) else ""
            
            for code_arg in code_args:
                if code_arg.get("name", "") == param_name and spec_type:
                    code_type = code_arg.get("type", "")
                    if code_type and code_type != "None" and spec_type.lower() != code_type.lower():
                        self.issue_counter += 1
                        issues.append(SyncIssue(
                            issue_id=f"ISSUE-{self.issue_counter:03d}",
                            issue_type="parameter_type_mismatch",
                            spec_element=func_name,
                            code_element=func_name,
                            description=f"参数 '{param_name}' 类型不匹配: 规范={spec_type}, 代码={code_type}",
                            severity=FeedbackSeverity.MEDIUM,
                            suggestion=f"统一参数 '{param_name}' 的类型定义",
                            parameter_mismatch={
                                "param_name": param_name,
                                "spec_type": spec_type,
                                "code_type": code_type
                            }
                        ))
        
        return issues
    
    def _validate_return_types(
        self,
        spec_elements: Dict[str, Any],
        code_elements: Dict[str, Any]
    ) -> List[SyncIssue]:
        issues = []
        
        code_functions = {f["name"]: f for f in code_elements.get("functions", [])}
        
        for iface in spec_elements.get("interfaces", []):
            iface_name = iface.get("name", "")
            spec_return = iface.get("return_type", "")
            
            if iface_name in code_functions and spec_return:
                code_func = code_functions[iface_name]
                code_return = code_func.get("returns", "")
                
                if code_return and code_return != "None":
                    if spec_return.lower() != code_return.lower():
                        self.issue_counter += 1
                        issues.append(SyncIssue(
                            issue_id=f"ISSUE-{self.issue_counter:03d}",
                            issue_type="return_type_mismatch",
                            spec_element=iface_name,
                            code_element=iface_name,
                            description=f"返回类型不匹配: 规范={spec_return}, 代码={code_return}",
                            severity=FeedbackSeverity.MEDIUM,
                            suggestion=f"统一返回类型定义",
                            return_type_mismatch={
                                "spec_type": spec_return,
                                "code_type": code_return
                            }
                        ))
        
        return issues
    
    def _validate_documentation_consistency(
        self,
        spec_elements: Dict[str, Any],
        code_elements: Dict[str, Any],
        code_path: Path
    ) -> List[SyncIssue]:
        issues = []
        
        code_functions = {f["name"]: f for f in code_elements.get("functions", [])}
        code_classes = {c["name"]: c for c in code_elements.get("classes", [])}
        
        for iface in spec_elements.get("interfaces", []):
            iface_name = iface.get("name", "")
            spec_desc = iface.get("description", "")
            
            if iface_name in code_functions:
                code_func = code_functions[iface_name]
                code_doc = code_func.get("docstring", "")
                
                doc_issues = self._check_doc_consistency(
                    iface_name, spec_desc, code_doc, "function"
                )
                issues.extend(doc_issues)
        
        for model in spec_elements.get("data_models", []):
            model_name = model.get("name", "")
            spec_desc = model.get("description", "")
            spec_attrs = model.get("attributes", [])
            
            if model_name in code_classes:
                code_class = code_classes[model_name]
                code_doc = code_class.get("docstring", "")
                
                doc_issues = self._check_doc_consistency(
                    model_name, spec_desc, code_doc, "class"
                )
                issues.extend(doc_issues)
                
                attr_issues = self._check_attribute_docs(model_name, spec_attrs, code_class)
                issues.extend(attr_issues)
        
        return issues
    
    def _check_doc_consistency(
        self,
        element_name: str,
        spec_desc: str,
        code_doc: str,
        element_type: str
    ) -> List[SyncIssue]:
        issues = []
        
        if spec_desc and not code_doc:
            self.issue_counter += 1
            issues.append(SyncIssue(
                issue_id=f"ISSUE-{self.issue_counter:03d}",
                issue_type="missing_docstring",
                spec_element=element_name,
                code_element=element_name,
                description=f"{element_type} '{element_name}' 缺少文档字符串",
                severity=FeedbackSeverity.LOW,
                suggestion=f"添加文档字符串: {spec_desc[:100]}...",
                doc_mismatch={"spec_description": spec_desc, "code_docstring": ""}
            ))
        
        elif spec_desc and code_doc:
            spec_keywords = set(spec_desc.lower().split())
            doc_keywords = set(code_doc.lower().split())
            
            overlap = len(spec_keywords & doc_keywords)
            total = len(spec_keywords)
            
            if total > 0 and overlap / total < 0.3:
                self.issue_counter += 1
                issues.append(SyncIssue(
                    issue_id=f"ISSUE-{self.issue_counter:03d}",
                    issue_type="docstring_inconsistent",
                    spec_element=element_name,
                    code_element=element_name,
                    description=f"{element_type} '{element_name}' 文档与规范描述不一致",
                    severity=FeedbackSeverity.LOW,
                    suggestion="更新文档字符串以匹配规范描述",
                    doc_mismatch={
                        "spec_description": spec_desc,
                        "code_docstring": code_doc,
                        "overlap_ratio": overlap / total if total > 0 else 0
                    }
                ))
        
        return issues
    
    def _check_attribute_docs(
        self,
        model_name: str,
        spec_attrs: List[Dict[str, Any]],
        code_class: Dict[str, Any]
    ) -> List[SyncIssue]:
        issues = []
        
        code_attrs = {a.get("name", ""): a for a in code_class.get("attributes", [])}
        
        for spec_attr in spec_attrs:
            attr_name = spec_attr.get("name", "") if isinstance(spec_attr, dict) else spec_attr
            attr_desc = spec_attr.get("description", "") if isinstance(spec_attr, dict) else ""
            
            if attr_name in code_attrs:
                code_attr = code_attrs[attr_name]
                code_type = code_attr.get("type", "")
                spec_type = spec_attr.get("type", "") if isinstance(spec_attr, dict) else ""
                
                if spec_type and code_type and spec_type.lower() != code_type.lower():
                    self.issue_counter += 1
                    issues.append(SyncIssue(
                        issue_id=f"ISSUE-{self.issue_counter:03d}",
                        issue_type="attribute_type_mismatch",
                        spec_element=f"{model_name}.{attr_name}",
                        code_element=f"{model_name}.{attr_name}",
                        description=f"属性 '{attr_name}' 类型不匹配: 规范={spec_type}, 代码={code_type}",
                        severity=FeedbackSeverity.MEDIUM,
                        suggestion=f"统一属性 '{attr_name}' 的类型定义"
                    ))
        
        return issues
    
    def _validate_type_hints(
        self,
        spec_elements: Dict[str, Any],
        code_elements: Dict[str, Any]
    ) -> List[SyncIssue]:
        issues = []
        
        code_functions = {f["name"]: f for f in code_elements.get("functions", [])}
        
        for iface in spec_elements.get("interfaces", []):
            iface_name = iface.get("name", "")
            
            if iface_name in code_functions:
                code_func = code_functions[iface_name]
                
                for arg in code_func.get("args", []):
                    if arg.get("type", "") in ["None", "unknown", ""]:
                        self.issue_counter += 1
                        issues.append(SyncIssue(
                            issue_id=f"ISSUE-{self.issue_counter:03d}",
                            issue_type="missing_type_hint",
                            spec_element=iface_name,
                            code_element=iface_name,
                            description=f"参数 '{arg.get('name', '')}' 缺少类型提示",
                            severity=FeedbackSeverity.LOW,
                            suggestion=f"为参数 '{arg.get('name', '')}' 添加类型提示"
                        ))
                
                if code_func.get("returns", "") in ["None", "unknown", ""]:
                    self.issue_counter += 1
                    issues.append(SyncIssue(
                        issue_id=f"ISSUE-{self.issue_counter:03d}",
                        issue_type="missing_return_type_hint",
                        spec_element=iface_name,
                        code_element=iface_name,
                        description=f"函数 '{iface_name}' 缺少返回类型提示",
                        severity=FeedbackSeverity.LOW,
                        suggestion=f"为函数 '{iface_name}' 添加返回类型提示"
                    ))
        
        return issues
    
    def _validate_naming_conventions(
        self,
        spec_elements: Dict[str, Any],
        code_elements: Dict[str, Any]
    ) -> List[SyncIssue]:
        issues = []
        
        for iface in spec_elements.get("interfaces", []):
            iface_name = iface.get("name", "")
            
            if not iface_name.islower() and "_" not in iface_name:
                if not iface_name[0].isupper():
                    self.issue_counter += 1
                    issues.append(SyncIssue(
                        issue_id=f"ISSUE-{self.issue_counter:03d}",
                        issue_type="naming_convention",
                        spec_element=iface_name,
                        code_element=iface_name,
                        description=f"接口名称 '{iface_name}' 不符合命名规范",
                        severity=FeedbackSeverity.INFO,
                        suggestion="建议使用 snake_case 或 PascalCase 命名"
                    ))
        
        for model in spec_elements.get("data_models", []):
            model_name = model.get("name", "")
            
            if model_name and model_name[0].islower():
                self.issue_counter += 1
                issues.append(SyncIssue(
                    issue_id=f"ISSUE-{self.issue_counter:03d}",
                    issue_type="naming_convention",
                    spec_element=model_name,
                    code_element=model_name,
                    description=f"数据模型名称 '{model_name}' 应使用 PascalCase",
                    severity=FeedbackSeverity.INFO,
                    suggestion=f"建议将 '{model_name}' 改为 PascalCase 格式"
                ))
        
        return issues
    
    def _check_deprecation_status(
        self,
        spec_elements: Dict[str, Any],
        code_elements: Dict[str, Any]
    ) -> List[SyncIssue]:
        issues = []
        
        code_functions = {f["name"]: f for f in code_elements.get("functions", [])}
        code_classes = {c["name"]: c for c in code_elements.get("classes", [])}
        
        for iface in spec_elements.get("interfaces", []):
            if iface.get("deprecated", False):
                iface_name = iface.get("name", "")
                deprecation_msg = iface.get("deprecation_message", "")
                
                if iface_name in code_functions:
                    code_func = code_functions[iface_name]
                    decorators = code_func.get("decorators", [])
                    
                    if "deprecated" not in str(decorators).lower():
                        self.issue_counter += 1
                        issues.append(SyncIssue(
                            issue_id=f"ISSUE-{self.issue_counter:03d}",
                            issue_type="missing_deprecation",
                            spec_element=iface_name,
                            code_element=iface_name,
                            description=f"函数 '{iface_name}' 已在规范中标记为废弃，但代码中缺少废弃标记",
                            severity=FeedbackSeverity.MEDIUM,
                            suggestion=f"添加 @deprecated 装饰器: {deprecation_msg}"
                        ))
        
        return issues
    
    def _check_issue_auto_fix(
        self,
        issue: SyncIssue,
        spec_elements: Dict[str, Any],
        code_elements: Dict[str, Any]
    ) -> None:
        auto_fixable_types = [
            "missing_type_hint",
            "missing_docstring",
            "naming_convention",
            "missing_deprecation"
        ]
        
        if issue.issue_type in auto_fixable_types:
            issue.auto_fix_available = True
            
            if issue.issue_type == "missing_type_hint":
                issue.auto_fix_details = "可以自动从规范推断类型并添加"
            elif issue.issue_type == "missing_docstring":
                issue.auto_fix_details = "可以自动从规范描述生成文档字符串"
            elif issue.issue_type == "missing_deprecation":
                issue.auto_fix_details = "可以自动添加废弃装饰器"
    
    def _compare_elements(
        self,
        spec_elements: Dict[str, Any],
        code_elements: Dict[str, Any]
    ) -> List[SyncIssue]:
        issues = []
        
        code_functions = {f["name"] for f in code_elements.get("functions", [])}
        code_classes = {c["name"] for c in code_elements.get("classes", [])}
        
        for iface in spec_elements.get("interfaces", []):
            iface_name = iface["name"]
            
            if iface_name not in code_functions and iface_name not in code_classes:
                self.issue_counter += 1
                issues.append(SyncIssue(
                    issue_id=f"ISSUE-{self.issue_counter:03d}",
                    issue_type="missing_implementation",
                    spec_element=iface_name,
                    code_element="N/A",
                    description=f"接口 '{iface_name}' 在代码中未找到实现",
                    severity=FeedbackSeverity.HIGH,
                    suggestion=f"实现接口 '{iface_name}'"
                ))
        
        for model in spec_elements.get("data_models", []):
            model_name = model["name"]
            
            if model_name not in code_classes:
                self.issue_counter += 1
                issues.append(SyncIssue(
                    issue_id=f"ISSUE-{self.issue_counter:03d}",
                    issue_type="missing_model",
                    spec_element=model_name,
                    code_element="N/A",
                    description=f"数据模型 '{model_name}' 在代码中未找到对应类",
                    severity=FeedbackSeverity.HIGH,
                    suggestion=f"创建数据模型类 '{model_name}'"
                ))
            else:
                code_class = next(
                    (c for c in code_elements.get("classes", []) if c["name"] == model_name),
                    None
                )
                if code_class:
                    spec_attrs = {a.get("name") for a in model.get("attributes", [])}
                    code_methods = set(code_class.get("methods", []))
                    
                    missing_attrs = spec_attrs - code_methods
                    if missing_attrs:
                        self.issue_counter += 1
                        issues.append(SyncIssue(
                            issue_id=f"ISSUE-{self.issue_counter:03d}",
                            issue_type="missing_attributes",
                            spec_element=model_name,
                            code_element=model_name,
                            description=f"数据模型 '{model_name}' 缺少属性: {', '.join(missing_attrs)}",
                            severity=FeedbackSeverity.MEDIUM,
                            suggestion=f"为 '{model_name}' 添加缺失的属性"
                        ))
        
        for func in spec_elements.get("functions", []):
            func_name = func["name"]
            
            if func_name not in code_functions:
                self.issue_counter += 1
                issues.append(SyncIssue(
                    issue_id=f"ISSUE-{self.issue_counter:03d}",
                    issue_type="missing_function",
                    spec_element=func_name,
                    code_element="N/A",
                    description=f"函数 '{func_name}' 在代码中未找到实现",
                    severity=FeedbackSeverity.MEDIUM,
                    suggestion=f"实现函数 '{func_name}'"
                ))
        
        return issues
    
    def validate_sync_comprehensive(
        self,
        spec: Dict[str, Any],
        code_dir: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        执行全面的规范与代码同步验证
        
        该方法提供更全面的同步验证，包括：
        - 深度一致性检查：检查规范与代码的深度一致性
        - 语义分析：分析规范描述与代码实现的语义一致性
        - 行为验证：验证代码行为是否符合规范定义
        - 变更影响分析：分析不同步变更的影响范围
        - 修复建议生成：生成具体的修复建议
        
        参数:
            spec: 规范字典
            code_dir: 代码目录路径
            options: 验证选项
            
        返回:
            包含全面验证结果的字典
        """
        self.logger.info("开始执行全面的规范与代码同步验证...")
        
        basic_report = self.validate_sync_advanced(spec, code_dir, options)
        
        semantic_analysis = self._analyze_semantic_consistency(spec, code_dir)
        
        behavior_validation = self._validate_behavior_consistency(spec, code_dir)
        
        impact_analysis = self._analyze_sync_impact(basic_report)
        
        fix_suggestions = self._generate_sync_fix_suggestions(
            basic_report, semantic_analysis, behavior_validation
        )
        
        return {
            "sync_report": {
                "report_id": basic_report.report_id,
                "spec_id": basic_report.spec_id,
                "status": basic_report.status.value,
                "sync_percentage": basic_report.sync_percentage,
                "checked_elements": basic_report.checked_elements,
                "matched_elements": basic_report.matched_elements
            },
            "issues": [
                {
                    "issue_id": issue.issue_id,
                    "issue_type": issue.issue_type,
                    "spec_element": issue.spec_element,
                    "code_element": issue.code_element,
                    "description": issue.description,
                    "severity": issue.severity.value,
                    "suggestion": issue.suggestion,
                    "auto_fix_available": issue.auto_fix_available
                }
                for issue in basic_report.issues
            ],
            "semantic_analysis": semantic_analysis,
            "behavior_validation": behavior_validation,
            "impact_analysis": impact_analysis,
            "fix_suggestions": fix_suggestions,
            "summary": self._generate_sync_summary(
                basic_report, semantic_analysis, behavior_validation
            )
        }
    
    def _analyze_semantic_consistency(
        self,
        spec: Dict[str, Any],
        code_dir: str
    ) -> Dict[str, Any]:
        """分析语义一致性"""
        analysis = {
            "consistent_elements": [],
            "inconsistent_elements": [],
            "ambiguous_elements": [],
            "missing_descriptions": []
        }
        
        code_path = Path(code_dir)
        code_elements = self._extract_code_elements(code_path)
        
        for iface in spec.get("interfaces", []):
            iface_name = iface.get("name", "")
            spec_desc = iface.get("description", "")
            
            code_func = next(
                (f for f in code_elements.get("functions", []) if f["name"] == iface_name),
                None
            )
            
            if code_func:
                code_doc = code_func.get("docstring", "")
                
                if spec_desc and code_doc:
                    consistency = self._calculate_semantic_similarity(spec_desc, code_doc)
                    
                    if consistency >= 0.7:
                        analysis["consistent_elements"].append({
                            "element": iface_name,
                            "type": "interface",
                            "similarity": consistency
                        })
                    elif consistency >= 0.4:
                        analysis["inconsistent_elements"].append({
                            "element": iface_name,
                            "type": "interface",
                            "similarity": consistency,
                            "spec_desc_preview": spec_desc[:100],
                            "code_doc_preview": code_doc[:100]
                        })
                    else:
                        analysis["ambiguous_elements"].append({
                            "element": iface_name,
                            "type": "interface",
                            "similarity": consistency
                        })
                elif spec_desc and not code_doc:
                    analysis["missing_descriptions"].append({
                        "element": iface_name,
                        "type": "interface"
                    })
        
        for model in spec.get("data_models", []):
            model_name = model.get("name", "")
            spec_desc = model.get("description", "")
            
            code_class = next(
                (c for c in code_elements.get("classes", []) if c["name"] == model_name),
                None
            )
            
            if code_class:
                code_doc = code_class.get("docstring", "")
                
                if spec_desc and code_doc:
                    consistency = self._calculate_semantic_similarity(spec_desc, code_doc)
                    
                    if consistency >= 0.7:
                        analysis["consistent_elements"].append({
                            "element": model_name,
                            "type": "data_model",
                            "similarity": consistency
                        })
                    elif consistency >= 0.4:
                        analysis["inconsistent_elements"].append({
                            "element": model_name,
                            "type": "data_model",
                            "similarity": consistency
                        })
        
        return analysis
    
    def _calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """计算语义相似度"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union) if union else 0.0
    
    def _validate_behavior_consistency(
        self,
        spec: Dict[str, Any],
        code_dir: str
    ) -> Dict[str, Any]:
        """验证行为一致性"""
        validation = {
            "validated_rules": [],
            "unvalidated_rules": [],
            "behavior_mismatches": [],
            "suggestions": []
        }
        
        code_path = Path(code_dir)
        code_elements = self._extract_code_elements(code_path)
        
        for rule in spec.get("behavior_rules", []):
            rule_name = rule.get("name", "")
            condition = rule.get("condition", "")
            action = rule.get("action", "")
            
            matching_functions = self._find_matching_functions(
                rule_name, condition, code_elements
            )
            
            if matching_functions:
                validation["validated_rules"].append({
                    "rule_name": rule_name,
                    "matching_functions": matching_functions,
                    "condition": condition,
                    "action": action
                })
            else:
                validation["unvalidated_rules"].append({
                    "rule_name": rule_name,
                    "condition": condition,
                    "action": action,
                    "reason": "未找到匹配的实现函数"
                })
        
        for constraint in spec.get("constraints", []):
            constraint_name = constraint.get("name", "")
            constraint_rule = constraint.get("rule", "")
            
            has_validation = self._check_constraint_validation(
                constraint_name, constraint_rule, code_elements
            )
            
            if not has_validation:
                validation["suggestions"].append({
                    "type": "missing_validation",
                    "constraint": constraint_name,
                    "suggestion": f"建议为约束 '{constraint_name}' 添加验证逻辑"
                })
        
        return validation
    
    def _find_matching_functions(
        self,
        rule_name: str,
        condition: str,
        code_elements: Dict[str, Any]
    ) -> List[str]:
        """查找匹配的函数"""
        matching = []
        rule_lower = rule_name.lower()
        
        for func in code_elements.get("functions", []):
            func_name = func.get("name", "").lower()
            
            if rule_lower in func_name or func_name in rule_lower:
                matching.append(func.get("name", ""))
        
        return matching
    
    def _check_constraint_validation(
        self,
        constraint_name: str,
        constraint_rule: str,
        code_elements: Dict[str, Any]
    ) -> bool:
        """检查约束验证"""
        constraint_lower = constraint_name.lower()
        
        for func in code_elements.get("functions", []):
            func_name = func.get("name", "").lower()
            docstring = func.get("docstring", "").lower()
            
            if constraint_lower in func_name or constraint_lower in docstring:
                return True
            
            if "validate" in func_name and constraint_lower in docstring:
                return True
        
        return False
    
    def _analyze_sync_impact(self, sync_report: SyncReport) -> Dict[str, Any]:
        """分析同步影响"""
        impact = {
            "overall_impact": "low",
            "critical_issues": [],
            "affected_components": [],
            "recommended_actions": []
        }
        
        critical_issues = [
            i for i in sync_report.issues 
            if i.severity in [FeedbackSeverity.CRITICAL, FeedbackSeverity.HIGH]
        ]
        
        if len(critical_issues) > 5:
            impact["overall_impact"] = "high"
        elif len(critical_issues) > 2:
            impact["overall_impact"] = "medium"
        
        impact["critical_issues"] = [
            {
                "issue_type": i.issue_type,
                "spec_element": i.spec_element,
                "description": i.description
            }
            for i in critical_issues[:5]
        ]
        
        affected = set()
        for issue in sync_report.issues:
            affected.add(issue.spec_element)
            if issue.code_element and issue.code_element != "N/A":
                affected.add(issue.code_element)
        
        impact["affected_components"] = list(affected)[:10]
        
        if impact["overall_impact"] == "high":
            impact["recommended_actions"] = [
                "立即处理关键同步问题",
                "暂停新功能开发直到同步问题解决",
                "进行全面代码审查"
            ]
        elif impact["overall_impact"] == "medium":
            impact["recommended_actions"] = [
                "优先处理高严重性问题",
                "安排时间修复同步问题",
                "更新规范或代码以保持一致"
            ]
        else:
            impact["recommended_actions"] = [
                "按优先级逐步处理同步问题",
                "定期检查规范与代码一致性"
            ]
        
        return impact
    
    def _generate_sync_fix_suggestions(
        self,
        sync_report: SyncReport,
        semantic_analysis: Dict[str, Any],
        behavior_validation: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """生成同步修复建议"""
        suggestions = []
        
        for issue in sync_report.issues:
            if issue.auto_fix_available:
                suggestions.append({
                    "type": "auto_fix",
                    "priority": "high",
                    "issue_id": issue.issue_id,
                    "description": issue.description,
                    "suggested_fix": issue.suggestion,
                    "auto_fix_details": issue.auto_fix_details
                })
            else:
                suggestions.append({
                    "type": "manual_fix",
                    "priority": "medium",
                    "issue_id": issue.issue_id,
                    "description": issue.description,
                    "suggested_fix": issue.suggestion
                })
        
        for inconsistent in semantic_analysis.get("inconsistent_elements", []):
            suggestions.append({
                "type": "semantic_update",
                "priority": "low",
                "element": inconsistent["element"],
                "description": f"语义一致性较低 ({inconsistent['similarity']:.0%})",
                "suggested_fix": "更新代码文档或规范描述以提高一致性"
            })
        
        for unvalidated in behavior_validation.get("unvalidated_rules", []):
            suggestions.append({
                "type": "missing_implementation",
                "priority": "high",
                "rule": unvalidated["rule_name"],
                "description": f"行为规则 '{unvalidated['rule_name']}' 未找到匹配实现",
                "suggested_fix": f"实现规则 '{unvalidated['rule_name']}' 或更新规范"
            })
        
        suggestions.sort(key=lambda x: {"high": 0, "medium": 1, "low": 2}.get(x.get("priority", "medium"), 1))
        
        return suggestions
    
    def _generate_sync_summary(
        self,
        sync_report: SyncReport,
        semantic_analysis: Dict[str, Any],
        behavior_validation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成同步摘要"""
        return {
            "sync_status": sync_report.status.value,
            "sync_percentage": round(sync_report.sync_percentage, 2),
            "total_issues": len(sync_report.issues),
            "critical_issues": len([
                i for i in sync_report.issues 
                if i.severity in [FeedbackSeverity.CRITICAL, FeedbackSeverity.HIGH]
            ]),
            "semantic_consistency": {
                "consistent_count": len(semantic_analysis.get("consistent_elements", [])),
                "inconsistent_count": len(semantic_analysis.get("inconsistent_elements", [])),
                "missing_desc_count": len(semantic_analysis.get("missing_descriptions", []))
            },
            "behavior_validation": {
                "validated_count": len(behavior_validation.get("validated_rules", [])),
                "unvalidated_count": len(behavior_validation.get("unvalidated_rules", []))
            },
            "overall_health": self._calculate_sync_health(
                sync_report, semantic_analysis, behavior_validation
            )
        }
    
    def _calculate_sync_health(
        self,
        sync_report: SyncReport,
        semantic_analysis: Dict[str, Any],
        behavior_validation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """计算同步健康度"""
        sync_score = sync_report.sync_percentage
        
        semantic_score = 0
        total_semantic = (
            len(semantic_analysis.get("consistent_elements", [])) +
            len(semantic_analysis.get("inconsistent_elements", [])) +
            len(semantic_analysis.get("ambiguous_elements", []))
        )
        if total_semantic > 0:
            semantic_score = (
                len(semantic_analysis.get("consistent_elements", [])) / total_semantic * 100
            )
        
        behavior_score = 0
        total_rules = (
            len(behavior_validation.get("validated_rules", [])) +
            len(behavior_validation.get("unvalidated_rules", []))
        )
        if total_rules > 0:
            behavior_score = (
                len(behavior_validation.get("validated_rules", [])) / total_rules * 100
            )
        
        overall_health = (sync_score * 0.5 + semantic_score * 0.25 + behavior_score * 0.25)
        
        if overall_health >= 80:
            health_status = "healthy"
        elif overall_health >= 60:
            health_status = "moderate"
        elif overall_health >= 40:
            health_status = "needs_attention"
        else:
            health_status = "critical"
        
        return {
            "overall_score": round(overall_health, 2),
            "sync_score": round(sync_score, 2),
            "semantic_score": round(semantic_score, 2),
            "behavior_score": round(behavior_score, 2),
            "status": health_status
        }


class CoverageLevel(Enum):
    FULL = "full"
    PARTIAL = "partial"
    MINIMAL = "minimal"
    NONE = "none"


@dataclass
class CoverageData:
    file_path: str
    line_rate: float
    branch_rate: float
    covered_lines: int
    total_lines: int
    missing_lines: List[int] = field(default_factory=list)


@dataclass
class SpecCoverageMapping:
    spec_element_id: str
    spec_element_name: str
    spec_element_type: str
    coverage_level: CoverageLevel
    coverage_percentage: float
    covered_scenarios: List[str] = field(default_factory=list)
    uncovered_scenarios: List[str] = field(default_factory=list)
    related_files: List[str] = field(default_factory=list)


@dataclass
class UncoveredScenario:
    scenario_id: str
    scenario_name: str
    spec_element: str
    scenario_type: str
    description: str
    priority: int
    suggested_test: str
    related_code: List[str] = field(default_factory=list)


@dataclass
class CoverageSpecReport:
    report_id: str
    spec_id: str
    generated_at: str
    overall_coverage: float
    spec_coverage_mappings: List[SpecCoverageMapping] = field(default_factory=list)
    uncovered_scenarios: List[UncoveredScenario] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)


class CoverageSpecAnalyzer:
    """覆盖率与规范对应关系分析器"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or self._setup_logger()
        self.mapping_counter = 0
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger("CoverageSpecAnalyzer")
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def analyze_coverage_spec_mapping(
        self,
        coverage_data: Dict[str, CoverageData],
        spec: Dict[str, Any],
        test_results: Optional[List[TestResult]] = None
    ) -> CoverageSpecReport:
        spec_id = spec.get("id", spec.get("spec_id", "unknown"))
        
        spec_coverage_mappings = self._build_spec_coverage_mappings(
            coverage_data, spec, test_results
        )
        
        uncovered_scenarios = self._identify_uncovered_scenarios(
            spec, spec_coverage_mappings, test_results
        )
        
        overall_coverage = self._calculate_overall_coverage(spec_coverage_mappings)
        
        recommendations = self._generate_coverage_recommendations(
            spec_coverage_mappings, uncovered_scenarios
        )
        
        summary = self._build_summary(
            spec_coverage_mappings, uncovered_scenarios, overall_coverage
        )
        
        report_id = f"COV-SPEC-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        return CoverageSpecReport(
            report_id=report_id,
            spec_id=spec_id,
            generated_at=datetime.now().isoformat(),
            overall_coverage=overall_coverage,
            spec_coverage_mappings=spec_coverage_mappings,
            uncovered_scenarios=uncovered_scenarios,
            recommendations=recommendations,
            summary=summary
        )
    
    def parse_coverage_report(self, report_path: str) -> Dict[str, CoverageData]:
        path = Path(report_path)
        if not path.exists():
            raise FileNotFoundError(f"覆盖率报告不存在: {report_path}")
        
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        
        suffix = path.suffix.lower()
        if suffix == ".xml":
            return self._parse_coverage_xml(content)
        elif suffix == ".json":
            return self._parse_coverage_json(content)
        else:
            return self._parse_coverage_xml(content)
    
    def _parse_coverage_xml(self, content: str) -> Dict[str, CoverageData]:
        coverage_data = {}
        
        try:
            root = ET.fromstring(content)
            
            for package in root.findall(".//package"):
                package_name = package.get("name", "")
                
                for cls in package.findall("classes/class"):
                    filename = cls.get("filename", "")
                    if not filename:
                        continue
                    
                    file_path = f"{package_name}/{filename}" if package_name else filename
                    
                    line_rate = float(cls.get("line-rate", 0)) * 100
                    branch_rate = float(cls.get("branch-rate", 0)) * 100
                    
                    lines = cls.findall("lines/line")
                    covered_lines = sum(1 for l in lines if l.get("hits", "0") != "0")
                    total_lines = len(lines)
                    missing_lines = [int(l.get("number", 0)) for l in lines if l.get("hits", "0") == "0"]
                    
                    coverage_data[file_path] = CoverageData(
                        file_path=file_path,
                        line_rate=line_rate,
                        branch_rate=branch_rate,
                        covered_lines=covered_lines,
                        total_lines=total_lines,
                        missing_lines=missing_lines
                    )
        except Exception as e:
            self.logger.error(f"解析覆盖率XML失败: {e}")
        
        return coverage_data
    
    def _parse_coverage_json(self, content: str) -> Dict[str, CoverageData]:
        coverage_data = {}
        
        try:
            data = json.loads(content)
            files_data = data.get("files", {})
            
            for file_path, file_info in files_data.items():
                summary = file_info.get("summary", {})
                executed_lines = file_info.get("executed_lines", [])
                missing_lines = file_info.get("missing_lines", [])
                
                covered_lines = len(executed_lines)
                total_lines = covered_lines + len(missing_lines)
                line_rate = (covered_lines / total_lines * 100) if total_lines > 0 else 0
                
                coverage_data[file_path] = CoverageData(
                    file_path=file_path,
                    line_rate=line_rate,
                    branch_rate=summary.get("covered_branches", 0) / max(summary.get("num_branches", 1), 1) * 100,
                    covered_lines=covered_lines,
                    total_lines=total_lines,
                    missing_lines=missing_lines
                )
        except Exception as e:
            self.logger.error(f"解析覆盖率JSON失败: {e}")
        
        return coverage_data
    
    def _build_spec_coverage_mappings(
        self,
        coverage_data: Dict[str, CoverageData],
        spec: Dict[str, Any],
        test_results: Optional[List[TestResult]]
    ) -> List[SpecCoverageMapping]:
        mappings = []
        
        for iface in spec.get("interfaces", []):
            mapping = self._create_element_mapping(
                iface, "interface", coverage_data, test_results
            )
            if mapping:
                mappings.append(mapping)
        
        for model in spec.get("data_models", []):
            mapping = self._create_element_mapping(
                model, "data_model", coverage_data, test_results
            )
            if mapping:
                mappings.append(mapping)
        
        for rule in spec.get("behavior_rules", []):
            mapping = self._create_element_mapping(
                rule, "behavior_rule", coverage_data, test_results
            )
            if mapping:
                mappings.append(mapping)
        
        for scenario in spec.get("spec", {}).get("scenarios", []):
            mapping = self._create_element_mapping(
                scenario, "scenario", coverage_data, test_results
            )
            if mapping:
                mappings.append(mapping)
        
        return mappings
    
    def _create_element_mapping(
        self,
        element: Dict[str, Any],
        element_type: str,
        coverage_data: Dict[str, CoverageData],
        test_results: Optional[List[TestResult]]
    ) -> Optional[SpecCoverageMapping]:
        self.mapping_counter += 1
        element_name = element.get("name", "")
        element_id = element.get("id", f"EL-{self.mapping_counter:03d}")
        
        related_files = self._find_related_files(element_name, coverage_data)
        
        covered_scenarios = []
        uncovered_scenarios = []
        
        if test_results:
            for test in test_results:
                test_name_lower = test.test_name.lower()
                if element_name.lower() in test_name_lower:
                    if test.status == TestStatus.PASSED:
                        covered_scenarios.append(test.test_name)
                    else:
                        uncovered_scenarios.append(test.test_name)
        
        if element_type == "interface":
            expected_scenarios = ["valid_input", "invalid_input", "boundary_condition", "exception_handling"]
        elif element_type == "data_model":
            expected_scenarios = ["creation", "validation", "serialization", "equality"]
        elif element_type == "behavior_rule":
            expected_scenarios = ["condition_met", "condition_not_met", "edge_case"]
        else:
            expected_scenarios = ["happy_path", "error_path"]
        
        for expected in expected_scenarios:
            scenario_name = f"{element_name}_{expected}"
            if not any(expected in s.lower() for s in covered_scenarios):
                if not any(expected in s.lower() for s in uncovered_scenarios):
                    uncovered_scenarios.append(scenario_name)
        
        if related_files:
            avg_coverage = sum(
                coverage_data[f].line_rate for f in related_files if f in coverage_data
            ) / len(related_files)
        else:
            avg_coverage = 0.0
        
        if avg_coverage >= 80:
            coverage_level = CoverageLevel.FULL
        elif avg_coverage >= 50:
            coverage_level = CoverageLevel.PARTIAL
        elif avg_coverage >= 20:
            coverage_level = CoverageLevel.MINIMAL
        else:
            coverage_level = CoverageLevel.NONE
        
        return SpecCoverageMapping(
            spec_element_id=element_id,
            spec_element_name=element_name,
            spec_element_type=element_type,
            coverage_level=coverage_level,
            coverage_percentage=avg_coverage,
            covered_scenarios=covered_scenarios,
            uncovered_scenarios=uncovered_scenarios,
            related_files=related_files
        )
    
    def _find_related_files(
        self,
        element_name: str,
        coverage_data: Dict[str, CoverageData]
    ) -> List[str]:
        related = []
        name_lower = element_name.lower()
        name_snake = re.sub(r'([A-Z])', r'_\1', element_name).lower().strip('_')
        
        for file_path in coverage_data.keys():
            file_lower = file_path.lower()
            if name_lower in file_lower or name_snake in file_lower:
                related.append(file_path)
        
        return related
    
    def _identify_uncovered_scenarios(
        self,
        spec: Dict[str, Any],
        spec_coverage_mappings: List[SpecCoverageMapping],
        test_results: Optional[List[TestResult]]
    ) -> List[UncoveredScenario]:
        uncovered = []
        scenario_counter = 0
        
        for mapping in spec_coverage_mappings:
            for scenario_name in mapping.uncovered_scenarios:
                scenario_counter += 1
                scenario_id = f"US-{scenario_counter:03d}"
                
                scenario_type = self._determine_scenario_type(scenario_name)
                priority = self._calculate_scenario_priority(
                    mapping.spec_element_type, scenario_type
                )
                suggested_test = self._generate_suggested_test(
                    mapping.spec_element_name, scenario_name, scenario_type
                )
                
                uncovered.append(UncoveredScenario(
                    scenario_id=scenario_id,
                    scenario_name=scenario_name,
                    spec_element=mapping.spec_element_name,
                    scenario_type=scenario_type,
                    description=f"规范元素 '{mapping.spec_element_name}' 的场景 '{scenario_name}' 未被测试覆盖",
                    priority=priority,
                    suggested_test=suggested_test,
                    related_code=mapping.related_files
                ))
        
        for constraint in spec.get("constraints", []):
            constraint_name = constraint.get("name", "")
            if test_results:
                has_test = any(
                    constraint_name.lower() in t.test_name.lower()
                    for t in test_results
                )
                if not has_test:
                    scenario_counter += 1
                    uncovered.append(UncoveredScenario(
                        scenario_id=f"US-{scenario_counter:03d}",
                        scenario_name=f"{constraint_name}_validation",
                        spec_element=constraint_name,
                        scenario_type="constraint",
                        description=f"约束 '{constraint_name}' 缺少验证测试",
                        priority=6,
                        suggested_test=f"test_{constraint_name.lower()}_constraint_validation",
                        related_code=[]
                    ))
        
        uncovered.sort(key=lambda x: x.priority, reverse=True)
        return uncovered
    
    def _determine_scenario_type(self, scenario_name: str) -> str:
        name_lower = scenario_name.lower()
        
        if "boundary" in name_lower or "edge" in name_lower:
            return "boundary"
        elif "exception" in name_lower or "error" in name_lower or "invalid" in name_lower:
            return "negative"
        elif "valid" in name_lower or "success" in name_lower or "happy" in name_lower:
            return "positive"
        elif "performance" in name_lower:
            return "performance"
        elif "security" in name_lower:
            return "security"
        else:
            return "functional"
    
    def _calculate_scenario_priority(self, element_type: str, scenario_type: str) -> int:
        base_priority = {
            "interface": 7,
            "data_model": 6,
            "behavior_rule": 5,
            "scenario": 4,
            "constraint": 6
        }.get(element_type, 5)
        
        type_modifier = {
            "positive": 2,
            "negative": 1,
            "boundary": 1,
            "functional": 0,
            "performance": -1,
            "security": 3
        }.get(scenario_type, 0)
        
        return min(10, max(1, base_priority + type_modifier))
    
    def _generate_suggested_test(
        self,
        element_name: str,
        scenario_name: str,
        scenario_type: str
    ) -> str:
        element_snake = re.sub(r'([A-Z])', r'_\1', element_name).lower().strip('_')
        scenario_snake = re.sub(r'([A-Z])', r'_\1', scenario_name).lower().strip('_')
        
        return f"test_{element_snake}_{scenario_snake}"
    
    def _calculate_overall_coverage(
        self,
        spec_coverage_mappings: List[SpecCoverageMapping]
    ) -> float:
        if not spec_coverage_mappings:
            return 0.0
        
        total = sum(m.coverage_percentage for m in spec_coverage_mappings)
        return total / len(spec_coverage_mappings)
    
    def _generate_coverage_recommendations(
        self,
        spec_coverage_mappings: List[SpecCoverageMapping],
        uncovered_scenarios: List[UncoveredScenario]
    ) -> List[str]:
        recommendations = []
        
        no_coverage = [m for m in spec_coverage_mappings if m.coverage_level == CoverageLevel.NONE]
        if no_coverage:
            recommendations.append(
                f"以下规范元素完全没有测试覆盖: {', '.join(m.spec_element_name for m in no_coverage[:5])}"
            )
        
        partial_coverage = [m for m in spec_coverage_mappings if m.coverage_level == CoverageLevel.PARTIAL]
        if partial_coverage:
            recommendations.append(
                f"以下规范元素测试覆盖不完整: {', '.join(m.spec_element_name for m in partial_coverage[:5])}"
            )
        
        high_priority_uncovered = [s for s in uncovered_scenarios if s.priority >= 7]
        if high_priority_uncovered:
            recommendations.append(
                f"发现 {len(high_priority_uncovered)} 个高优先级未覆盖场景，建议优先处理"
            )
        
        boundary_uncovered = [s for s in uncovered_scenarios if s.scenario_type == "boundary"]
        if boundary_uncovered:
            recommendations.append(
                f"发现 {len(boundary_uncovered)} 个边界条件场景未被覆盖"
            )
        
        negative_uncovered = [s for s in uncovered_scenarios if s.scenario_type == "negative"]
        if negative_uncovered:
            recommendations.append(
                f"发现 {len(negative_uncovered)} 个异常/负面场景未被覆盖"
            )
        
        return recommendations
    
    def _build_summary(
        self,
        spec_coverage_mappings: List[SpecCoverageMapping],
        uncovered_scenarios: List[UncoveredScenario],
        overall_coverage: float
    ) -> Dict[str, Any]:
        coverage_distribution = {
            "full": len([m for m in spec_coverage_mappings if m.coverage_level == CoverageLevel.FULL]),
            "partial": len([m for m in spec_coverage_mappings if m.coverage_level == CoverageLevel.PARTIAL]),
            "minimal": len([m for m in spec_coverage_mappings if m.coverage_level == CoverageLevel.MINIMAL]),
            "none": len([m for m in spec_coverage_mappings if m.coverage_level == CoverageLevel.NONE]),
        }
        
        scenario_type_distribution = {}
        for scenario in uncovered_scenarios:
            scenario_type_distribution[scenario.scenario_type] = \
                scenario_type_distribution.get(scenario.scenario_type, 0) + 1
        
        return {
            "total_spec_elements": len(spec_coverage_mappings),
            "overall_coverage": round(overall_coverage, 2),
            "coverage_distribution": coverage_distribution,
            "total_uncovered_scenarios": len(uncovered_scenarios),
            "scenario_type_distribution": scenario_type_distribution,
            "health_score": self._calculate_health_score(overall_coverage, uncovered_scenarios)
        }
    
    def _calculate_health_score(
        self,
        overall_coverage: float,
        uncovered_scenarios: List[UncoveredScenario]
    ) -> float:
        coverage_score = overall_coverage / 100 * 50
        
        high_priority_count = len([s for s in uncovered_scenarios if s.priority >= 7])
        penalty = min(50, high_priority_count * 5)
        
        return max(0, coverage_score + (50 - penalty))


class TddFeedbackAnalyzer:
    """TDD结果分析器主类"""
    
    def __init__(
        self,
        output_dir: str = None,
        logger: Optional[logging.Logger] = None
    ):
        if output_dir is None:
            try:
                from skillscripts.utils.enhanced_path_config_manager import create_path_manager, OutputType
                _path_mgr = create_path_manager()
                self.output_dir = _path_mgr.get_output_path(OutputType.REPORT, subdirectory="tdd_feedback")
            except Exception:
                self.output_dir = Path("output/tdd_feedback")
        else:
            self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logger or self._setup_logger()
        
        self.result_parser = TestResultParser(self.logger)
        self.failure_analyzer = FailureAnalyzer(self.logger)
        self.feedback_generator = FeedbackGenerator(self.logger)
        self.improvement_suggester = SpecImprovementSuggester(self.logger)
        self.sync_validator = SpecCodeSyncValidator(self.logger)
        self.coverage_analyzer = CoverageSpecAnalyzer(self.logger)
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger("TddFeedbackAnalyzer")
        logger.setLevel(logging.INFO)
        
        log_file = self.output_dir / "tdd_feedback_analyzer.log"
        handler = logging.FileHandler(log_file, encoding="utf-8")
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        return logger
    
    def analyze_test_results(
        self,
        test_results_path: str
    ) -> AnalysisReport:
        self.logger.info(f"分析测试结果: {test_results_path}")
        
        test_results = self.result_parser.parse_file(test_results_path)
        
        failure_analyses = self.failure_analyzer.analyze_failures(test_results)
        
        feedback_items = self.feedback_generator.generate_feedback(
            test_results,
            failure_analyses
        )
        
        report = self._create_analysis_report(
            test_results,
            failure_analyses,
            feedback_items
        )
        
        self._save_report(report)
        
        return report
    
    def generate_feedback_to_spec(
        self,
        test_results_path: str,
        spec_path: str
    ) -> AnalysisReport:
        self.logger.info(f"生成规范反馈: 测试结果={test_results_path}, 规范={spec_path}")
        
        test_results = self.result_parser.parse_file(test_results_path)
        
        failure_analyses = self.failure_analyzer.analyze_failures(test_results)
        
        spec = self._load_spec(spec_path)
        
        spec_elements = self._extract_spec_elements(spec)
        
        feedback_items = self.feedback_generator.generate_feedback(
            test_results,
            failure_analyses,
            spec_elements
        )
        
        improvement_suggestions = self.improvement_suggester.generate_suggestions(
            test_results,
            failure_analyses,
            spec
        )
        
        report = self._create_analysis_report(
            test_results,
            failure_analyses,
            feedback_items,
            improvement_suggestions
        )
        
        self._save_report(report)
        
        return report
    
    def generate_improvement_suggestions(
        self,
        test_results_path: str,
        spec_path: str
    ) -> List[SpecImprovementSuggestion]:
        self.logger.info(f"生成改进建议: 测试结果={test_results_path}, 规范={spec_path}")
        
        test_results = self.result_parser.parse_file(test_results_path)
        failure_analyses = self.failure_analyzer.analyze_failures(test_results)
        spec = self._load_spec(spec_path)
        
        suggestions = self.improvement_suggester.generate_suggestions(
            test_results,
            failure_analyses,
            spec
        )
        
        self._save_suggestions(suggestions, spec.get("id", "unknown"))
        
        return suggestions
    
    def validate_spec_code_sync(
        self,
        spec_path: str,
        code_dir: str
    ) -> SyncReport:
        self.logger.info(f"验证规范与代码同步: 规范={spec_path}, 代码={code_dir}")
        
        spec = self._load_spec(spec_path)
        
        sync_report = self.sync_validator.validate_sync(spec, code_dir)
        
        self._save_sync_report(sync_report)
        
        return sync_report
    
    def run_full_analysis(
        self,
        test_results_path: str,
        spec_path: Optional[str] = None,
        code_dir: Optional[str] = None
    ) -> AnalysisReport:
        self.logger.info("=" * 60)
        self.logger.info("开始 TDD 完整分析流程")
        self.logger.info("=" * 60)
        
        test_results = self.result_parser.parse_file(test_results_path)
        
        failure_analyses = self.failure_analyzer.analyze_failures(test_results)
        
        spec = None
        spec_elements = None
        if spec_path:
            spec = self._load_spec(spec_path)
            spec_elements = self._extract_spec_elements(spec)
        
        feedback_items = self.feedback_generator.generate_feedback(
            test_results,
            failure_analyses,
            spec_elements
        )
        
        improvement_suggestions = []
        if spec:
            improvement_suggestions = self.improvement_suggester.generate_suggestions(
                test_results,
                failure_analyses,
                spec
            )
        
        sync_report = None
        if spec_path and code_dir:
            sync_report = self.sync_validator.validate_sync(spec, code_dir)
        
        report = self._create_analysis_report(
            test_results,
            failure_analyses,
            feedback_items,
            improvement_suggestions,
            sync_report
        )
        
        self._save_report(report)
        
        self.logger.info("=" * 60)
        self.logger.info("TDD 分析流程完成")
        self.logger.info(f"通过率: {report.pass_rate:.1f}%")
        self.logger.info(f"反馈项: {len(feedback_items)}")
        self.logger.info(f"改进建议: {len(improvement_suggestions)}")
        self.logger.info("=" * 60)
        
        return report
    
    def run_comprehensive_analysis(
        self,
        test_results_path: str,
        spec_path: Optional[str] = None,
        code_dir: Optional[str] = None,
        historical_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        运行完整的TDD增强分析流程
        
        该方法整合所有增强功能，提供全面的分析结果：
        - 深度失败分析
        - 智能反馈生成
        - 增强建议生成
        - 全面同步验证
        
        参数:
            test_results_path: 测试结果文件路径
            spec_path: 规范文件路径
            code_dir: 代码目录路径
            historical_data: 历史数据
            
        返回:
            包含完整分析结果的字典
        """
        self.logger.info("=" * 60)
        self.logger.info("开始 TDD 增强完整分析流程")
        self.logger.info("=" * 60)
        
        test_results = self.result_parser.parse_file(test_results_path)
        
        spec = None
        spec_elements = None
        if spec_path:
            spec = self._load_spec(spec_path)
            spec_elements = self._extract_spec_elements(spec)
        
        deep_analysis = self.failure_analyzer.analyze_failures_deeply(
            test_results, spec_elements, None, historical_data
        )
        
        intelligent_feedback = self.feedback_generator.generate_intelligent_feedback(
            test_results,
            deep_analysis["basic_analyses"],
            spec_elements,
            historical_data
        )
        
        enhanced_suggestions = {}
        if spec:
            enhanced_suggestions = self.improvement_suggester.generate_enhanced_suggestions(
                test_results,
                deep_analysis["basic_analyses"],
                spec,
                historical_data
            )
        
        comprehensive_sync = {}
        if spec_path and code_dir:
            comprehensive_sync = self.sync_validator.validate_sync_comprehensive(
                spec, code_dir
            )
        
        basic_report = self._create_analysis_report(
            test_results,
            deep_analysis["basic_analyses"],
            intelligent_feedback.get("feedback_items", []),
            enhanced_suggestions.get("suggestions", []),
            comprehensive_sync.get("sync_report")
        )
        
        comprehensive_report = {
            "report_id": basic_report.report_id,
            "generated_at": basic_report.generated_at,
            "test_summary": {
                "total_tests": basic_report.total_tests,
                "passed": basic_report.passed,
                "failed": basic_report.failed,
                "skipped": basic_report.skipped,
                "errors": basic_report.errors,
                "pass_rate": basic_report.pass_rate
            },
            "deep_analysis": deep_analysis,
            "intelligent_feedback": intelligent_feedback,
            "enhanced_suggestions": enhanced_suggestions,
            "comprehensive_sync": comprehensive_sync,
            "overall_summary": self._generate_comprehensive_summary(
                deep_analysis, intelligent_feedback, enhanced_suggestions, comprehensive_sync
            )
        }
        
        self._save_comprehensive_report(comprehensive_report)
        
        self.logger.info("=" * 60)
        self.logger.info("TDD 增强完整分析流程完成")
        self.logger.info(f"通过率: {basic_report.pass_rate:.1f}%")
        self.logger.info(f"失败模式: {len(deep_analysis.get('failure_patterns', {}).get('recurring_patterns', []))}")
        self.logger.info(f"反馈项: {len(intelligent_feedback.get('feedback_items', []))}")
        self.logger.info(f"改进建议: {len(enhanced_suggestions.get('suggestions', []))}")
        self.logger.info("=" * 60)
        
        return comprehensive_report
    
    def _generate_comprehensive_summary(
        self,
        deep_analysis: Dict[str, Any],
        intelligent_feedback: Dict[str, Any],
        enhanced_suggestions: Dict[str, Any],
        comprehensive_sync: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成综合摘要"""
        summary = {
            "overall_health": "unknown",
            "key_findings": [],
            "priority_actions": [],
            "metrics": {}
        }
        
        deep_summary = deep_analysis.get("summary", {})
        if deep_summary:
            summary["metrics"]["failure_severity"] = deep_summary.get("overall_severity", "unknown")
            summary["metrics"]["risk_score"] = deep_summary.get("risk_score", 0)
            
            if deep_summary.get("overall_severity") == "critical":
                summary["key_findings"].append("存在严重失败需要立即处理")
            elif deep_summary.get("risk_score", 0) > 50:
                summary["key_findings"].append("风险评分较高，建议优先处理")
        
        feedback_summary = intelligent_feedback.get("summary", {})
        if feedback_summary:
            summary["metrics"]["high_priority_feedback"] = feedback_summary.get("high_priority_count", 0)
            summary["metrics"]["auto_fixable"] = feedback_summary.get("auto_fixable_count", 0)
            
            if feedback_summary.get("high_priority_count", 0) > 3:
                summary["priority_actions"].append("处理高优先级反馈项")
        
        suggestion_summary = enhanced_suggestions.get("summary", {})
        if suggestion_summary:
            summary["metrics"]["total_suggestions"] = suggestion_summary.get("total_suggestions", 0)
            summary["metrics"]["breaking_changes"] = suggestion_summary.get("breaking_changes_count", 0)
            
            if suggestion_summary.get("overall_risk_level") == "high":
                summary["key_findings"].append("规范变更风险较高")
        
        sync_summary = comprehensive_sync.get("summary", {})
        if sync_summary:
            health_info = sync_summary.get("overall_health", {})
            summary["metrics"]["sync_health_score"] = health_info.get("overall_score", 0)
            summary["metrics"]["sync_status"] = health_info.get("status", "unknown")
            
            if health_info.get("status") in ["critical", "needs_attention"]:
                summary["key_findings"].append("规范与代码同步状态需要关注")
        
        if len(summary["key_findings"]) == 0:
            summary["overall_health"] = "healthy"
        elif any("严重" in f or "critical" in f.lower() for f in summary["key_findings"]):
            summary["overall_health"] = "critical"
        elif len(summary["key_findings"]) > 2:
            summary["overall_health"] = "needs_attention"
        else:
            summary["overall_health"] = "moderate"
        
        if not summary["priority_actions"]:
            if summary["overall_health"] == "healthy":
                summary["priority_actions"].append("继续保持代码质量")
            else:
                summary["priority_actions"].append("按优先级处理发现的问题")
        
        return summary
    
    def _save_comprehensive_report(self, report: Dict[str, Any]) -> None:
        """保存综合报告"""
        output_file = self.output_dir / "comprehensive_reports" / f"{report['report_id']}.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)
        
        md_report = self._generate_comprehensive_markdown_report(report)
        md_file = output_file.with_suffix(".md")
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(md_report)
    
    def _generate_comprehensive_markdown_report(self, report: Dict[str, Any]) -> str:
        """生成综合Markdown报告"""
        lines = [
            "# TDD 增强完整分析报告",
            "",
            f"**报告ID**: {report['report_id']}",
            f"**生成时间**: {report['generated_at']}",
            "",
            "## 测试结果概览",
            "",
            f"- 总测试数: {report['test_summary']['total_tests']}",
            f"- 通过: {report['test_summary']['passed']}",
            f"- 失败: {report['test_summary']['failed']}",
            f"- 错误: {report['test_summary']['errors']}",
            f"- 跳过: {report['test_summary']['skipped']}",
            f"- 通过率: {report['test_summary']['pass_rate']:.1f}%",
            "",
            "## 综合评估",
            "",
            f"- **整体健康度**: {report['overall_summary']['overall_health']}",
            "",
            "### 关键发现",
            "",
        ]
        
        for finding in report['overall_summary']['key_findings']:
            lines.append(f"- {finding}")
        
        lines.extend([
            "",
            "### 优先行动",
            "",
        ])
        
        for action in report['overall_summary']['priority_actions']:
            lines.append(f"- {action}")
        
        lines.extend([
            "",
            "## 指标汇总",
            "",
        ])
        
        for key, value in report['overall_summary']['metrics'].items():
            lines.append(f"- {key}: {value}")
        
        return "\n".join(lines)
    
    def _load_spec(self, spec_path: str) -> Dict[str, Any]:
        path = Path(spec_path)
        if not path.exists():
            raise FileNotFoundError(f"规范文件不存在: {spec_path}")
        
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        
        suffix = path.suffix.lower()
        if suffix == ".json":
            return json.loads(content)
        elif suffix in [".yaml", ".yml"]:
            try:
                import yaml
                return yaml.safe_load(content)
            except ImportError:
                raise RuntimeError("需要安装 PyYAML: pip install pyyaml")
        else:
            return {"raw_content": content}
    
    def _extract_spec_elements(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "interfaces": spec.get("interfaces", []),
            "data_models": spec.get("data_models", []),
            "behavior_rules": spec.get("behavior_rules", []),
            "constraints": spec.get("constraints", [])
        }
    
    def _create_analysis_report(
        self,
        test_results: List[TestResult],
        failure_analyses: List[FailureAnalysis],
        feedback_items: List[FeedbackItem],
        improvement_suggestions: Optional[List[SpecImprovementSuggestion]] = None,
        sync_report: Optional[SyncReport] = None
    ) -> AnalysisReport:
        total = len(test_results)
        passed = len([t for t in test_results if t.status == TestStatus.PASSED])
        failed = len([t for t in test_results if t.status == TestStatus.FAILED])
        skipped = len([t for t in test_results if t.status == TestStatus.SKIPPED])
        errors = len([t for t in test_results if t.status == TestStatus.ERROR])
        
        pass_rate = (passed / total * 100) if total > 0 else 0
        
        report_id = f"RPT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        summary = {
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "errors": errors,
            "pass_rate": pass_rate,
            "failure_categories": self._count_failure_categories(failure_analyses),
            "top_issues": self._get_top_issues(failure_analyses, 5)
        }
        
        return AnalysisReport(
            report_id=report_id,
            generated_at=datetime.now().isoformat(),
            total_tests=total,
            passed=passed,
            failed=failed,
            skipped=skipped,
            errors=errors,
            pass_rate=pass_rate,
            failure_analyses=failure_analyses,
            feedback_items=feedback_items,
            improvement_suggestions=improvement_suggestions or [],
            sync_report=sync_report,
            summary=summary
        )
    
    def _count_failure_categories(
        self,
        failure_analyses: List[FailureAnalysis]
    ) -> Dict[str, int]:
        counts = {}
        for analysis in failure_analyses:
            category = analysis.category.value
            counts[category] = counts.get(category, 0) + 1
        return counts
    
    def _get_top_issues(
        self,
        failure_analyses: List[FailureAnalysis],
        limit: int
    ) -> List[Dict[str, Any]]:
        sorted_analyses = sorted(
            failure_analyses,
            key=lambda x: x.confidence,
            reverse=True
        )
        
        return [
            {
                "test_id": a.test_id,
                "category": a.category.value,
                "root_cause": a.root_cause[:100]
            }
            for a in sorted_analyses[:limit]
        ]
    
    def _save_report(self, report: AnalysisReport) -> None:
        output_file = self.output_dir / "reports" / f"{report.report_id}.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        report_dict = {
            "report_id": report.report_id,
            "generated_at": report.generated_at,
            "total_tests": report.total_tests,
            "passed": report.passed,
            "failed": report.failed,
            "skipped": report.skipped,
            "errors": report.errors,
            "pass_rate": report.pass_rate,
            "failure_analyses": [
                {
                    "failure_id": fa.failure_id,
                    "test_id": fa.test_id,
                    "category": fa.category.value,
                    "root_cause": fa.root_cause,
                    "suggested_fix": fa.suggested_fix,
                    "confidence": fa.confidence
                }
                for fa in report.failure_analyses
            ],
            "feedback_items": [
                {
                    "feedback_id": fi.feedback_id,
                    "spec_element": fi.spec_element_name,
                    "feedback_type": fi.feedback_type,
                    "severity": fi.severity.value,
                    "message": fi.message,
                    "suggestions": fi.suggestions
                }
                for fi in report.feedback_items
            ],
            "improvement_suggestions": [
                {
                    "suggestion_id": s.suggestion_id,
                    "suggestion_type": s.suggestion_type.value,
                    "spec_element": s.spec_element,
                    "suggested_value": s.suggested_value,
                    "reason": s.reason,
                    "priority": s.priority
                }
                for s in report.improvement_suggestions
            ],
            "summary": report.summary
        }
        
        if report.sync_report:
            report_dict["sync_report"] = {
                "report_id": report.sync_report.report_id,
                "status": report.sync_report.status.value,
                "sync_percentage": report.sync_report.sync_percentage,
                "issues_count": len(report.sync_report.issues)
            }
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(report_dict, f, ensure_ascii=False, indent=2)
        
        md_report = self._generate_markdown_report(report)
        md_file = output_file.with_suffix(".md")
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(md_report)
    
    def _generate_markdown_report(self, report: AnalysisReport) -> str:
        lines = [
            "# TDD 反馈分析报告",
            "",
            f"**报告ID**: {report.report_id}",
            f"**生成时间**: {report.generated_at}",
            "",
            "## 测试结果概览",
            "",
            f"- 总测试数: {report.total_tests}",
            f"- 通过: {report.passed}",
            f"- 失败: {report.failed}",
            f"- 错误: {report.errors}",
            f"- 跳过: {report.skipped}",
            f"- 通过率: {report.pass_rate:.1f}%",
            "",
            "## 失败分析",
            "",
        ]
        
        if report.failure_analyses:
            for fa in report.failure_analyses[:10]:
                lines.extend([
                    f"### {fa.test_id}",
                    f"- **类别**: {fa.category.value}",
                    f"- **根因**: {fa.root_cause}",
                    f"- **建议修复**: {fa.suggested_fix}",
                    f"- **置信度**: {fa.confidence:.0%}",
                    "",
                ])
        else:
            lines.append("无失败测试")
            lines.append("")
        
        lines.extend([
            "## 反馈项",
            "",
        ])
        
        if report.feedback_items:
            for fi in report.feedback_items:
                lines.extend([
                    f"### {fi.spec_element_name}",
                    f"- **类型**: {fi.feedback_type}",
                    f"- **严重程度**: {fi.severity.value}",
                    f"- **消息**: {fi.message}",
                    "",
                    "**建议**:",
                    "",
                ])
                for suggestion in fi.suggestions:
                    lines.append(f"- {suggestion}")
                lines.append("")
        else:
            lines.append("无反馈项")
            lines.append("")
        
        if report.improvement_suggestions:
            lines.extend([
                "## 规范改进建议",
                "",
            ])
            
            for s in report.improvement_suggestions[:10]:
                lines.extend([
                    f"### {s.spec_element}",
                    f"- **类型**: {s.suggestion_type.value}",
                    f"- **建议值**: {s.suggested_value}",
                    f"- **原因**: {s.reason}",
                    f"- **优先级**: {s.priority}",
                    "",
                ])
        
        if report.sync_report:
            lines.extend([
                "## 规范与代码同步状态",
                "",
                f"- **状态**: {report.sync_report.status.value}",
                f"- **同步率**: {report.sync_report.sync_percentage:.1f}%",
                f"- **检查元素**: {report.sync_report.checked_elements}",
                f"- **匹配元素**: {report.sync_report.matched_elements}",
                "",
            ])
            
            if report.sync_report.issues:
                lines.append("### 同步问题")
                lines.append("")
                for issue in report.sync_report.issues[:5]:
                    lines.append(f"- **{issue.spec_element}**: {issue.description}")
                lines.append("")
        
        return "\n".join(lines)
    
    def _save_suggestions(
        self,
        suggestions: List[SpecImprovementSuggestion],
        spec_id: str
    ) -> None:
        output_file = self.output_dir / "suggestions" / f"{spec_id}_suggestions.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        suggestions_dict = [
            {
                "suggestion_id": s.suggestion_id,
                "suggestion_type": s.suggestion_type.value,
                "spec_element": s.spec_element,
                "current_value": s.current_value,
                "suggested_value": s.suggested_value,
                "reason": s.reason,
                "priority": s.priority,
                "test_evidence": s.test_evidence
            }
            for s in suggestions
        ]
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(suggestions_dict, f, ensure_ascii=False, indent=2)
    
    def _save_sync_report(self, report: SyncReport) -> None:
        output_file = self.output_dir / "sync_reports" / f"{report.report_id}.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        report_dict = {
            "report_id": report.report_id,
            "spec_id": report.spec_id,
            "status": report.status.value,
            "sync_percentage": report.sync_percentage,
            "checked_elements": report.checked_elements,
            "matched_elements": report.matched_elements,
            "issues": [
                {
                    "issue_id": i.issue_id,
                    "issue_type": i.issue_type,
                    "spec_element": i.spec_element,
                    "code_element": i.code_element,
                    "description": i.description,
                    "severity": i.severity.value,
                    "suggestion": i.suggestion
                }
                for i in report.issues
            ],
            "generated_at": report.generated_at
        }
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(report_dict, f, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description="TDD结果分析器",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    analyze_parser = subparsers.add_parser("analyze", help="分析测试结果")
    analyze_parser.add_argument("--test-results", required=True, help="测试结果文件路径")
    analyze_parser.add_argument("--output-dir", default="output/tdd_feedback", help="输出目录")
    
    feedback_parser = subparsers.add_parser("feedback", help="生成规范反馈")
    feedback_parser.add_argument("--test-results", required=True, help="测试结果文件路径")
    feedback_parser.add_argument("--spec", required=True, help="规范文件路径")
    feedback_parser.add_argument("--output-dir", default="output/tdd_feedback", help="输出目录")
    
    suggest_parser = subparsers.add_parser("suggest", help="生成改进建议")
    suggest_parser.add_argument("--test-results", required=True, help="测试结果文件路径")
    suggest_parser.add_argument("--spec", required=True, help="规范文件路径")
    suggest_parser.add_argument("--output-dir", default="output/tdd_feedback", help="输出目录")
    
    sync_parser = subparsers.add_parser("sync", help="验证规范与代码同步")
    sync_parser.add_argument("--spec", required=True, help="规范文件路径")
    sync_parser.add_argument("--code", required=True, help="代码目录路径")
    sync_parser.add_argument("--output-dir", default="output/tdd_feedback", help="输出目录")
    
    full_parser = subparsers.add_parser("full", help="运行完整分析")
    full_parser.add_argument("--test-results", required=True, help="测试结果文件路径")
    full_parser.add_argument("--spec", help="规范文件路径")
    full_parser.add_argument("--code", help="代码目录路径")
    full_parser.add_argument("--output-dir", default="output/tdd_feedback", help="输出目录")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        analyzer = TddFeedbackAnalyzer(output_dir=args.output_dir)
        
        if args.command == "analyze":
            report = analyzer.analyze_test_results(args.test_results)
            print(f"测试结果分析完成:")
            print(f"  总测试数: {report.total_tests}")
            print(f"  通过: {report.passed}")
            print(f"  失败: {report.failed}")
            print(f"  通过率: {report.pass_rate:.1f}%")
            print(f"  反馈项: {len(report.feedback_items)}")
            
        elif args.command == "feedback":
            report = analyzer.generate_feedback_to_spec(args.test_results, args.spec)
            print(f"规范反馈生成完成:")
            print(f"  反馈项: {len(report.feedback_items)}")
            print(f"  改进建议: {len(report.improvement_suggestions)}")
            
        elif args.command == "suggest":
            suggestions = analyzer.generate_improvement_suggestions(
                args.test_results,
                args.spec
            )
            print(f"改进建议生成完成:")
            print(f"  建议数量: {len(suggestions)}")
            for s in suggestions[:5]:
                print(f"  - [{s.suggestion_type.value}] {s.spec_element}: {s.suggested_value[:50]}...")
                
        elif args.command == "sync":
            sync_report = analyzer.validate_spec_code_sync(args.spec, args.code)
            print(f"同步验证完成:")
            print(f"  状态: {sync_report.status.value}")
            print(f"  同步率: {sync_report.sync_percentage:.1f}%")
            print(f"  问题数: {len(sync_report.issues)}")
            
        elif args.command == "full":
            report = analyzer.run_full_analysis(
                args.test_results,
                args.spec,
                args.code
            )
            print(f"完整分析完成:")
            print(f"  报告ID: {report.report_id}")
            print(f"  通过率: {report.pass_rate:.1f}%")
            print(f"  失败分析: {len(report.failure_analyses)}")
            print(f"  反馈项: {len(report.feedback_items)}")
            print(f"  改进建议: {len(report.improvement_suggestions)}")
            if report.sync_report:
                print(f"  同步状态: {report.sync_report.status.value}")
                print(f"  同步率: {report.sync_report.sync_percentage:.1f}%")
    
    except FileNotFoundError as e:
        print(f"错误: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"执行错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


class EnhancedCoverageAnalyzer:
    """
    增强的覆盖率分析器
    
    提供深度覆盖率分析功能：
    - 分支覆盖率分析
    - 条件覆盖率分析
    - 规范元素覆盖率映射
    - 未覆盖场景识别
    - 覆盖率趋势分析
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or self._setup_logger()
        self.coverage_history: List[Dict[str, Any]] = []
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger("EnhancedCoverageAnalyzer")
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def analyze_coverage_deeply(
        self,
        coverage_data: Dict[str, CoverageData],
        spec: Dict[str, Any],
        test_results: Optional[List[TestResult]] = None
    ) -> Dict[str, Any]:
        """
        执行深度覆盖率分析
        
        Args:
            coverage_data: 覆盖率数据
            spec: 规范字典
            test_results: 测试结果列表
            
        Returns:
            Dict[str, Any]: 深度分析结果
        """
        self.logger.info("开始深度覆盖率分析...")
        
        line_coverage = self._analyze_line_coverage(coverage_data)
        
        branch_coverage = self._analyze_branch_coverage(coverage_data)
        
        condition_coverage = self._analyze_condition_coverage(coverage_data, spec)
        
        spec_mapping = self._map_coverage_to_spec(coverage_data, spec)
        
        gaps = self._identify_coverage_gaps(coverage_data, spec, test_results)
        
        trends = self._analyze_coverage_trends(coverage_data)
        
        recommendations = self._generate_coverage_recommendations_enhanced(
            line_coverage, branch_coverage, condition_coverage, gaps
        )
        
        return {
            "line_coverage": line_coverage,
            "branch_coverage": branch_coverage,
            "condition_coverage": condition_coverage,
            "spec_mapping": spec_mapping,
            "coverage_gaps": gaps,
            "trends": trends,
            "recommendations": recommendations,
            "summary": self._create_coverage_summary(
                line_coverage, branch_coverage, condition_coverage, gaps
            )
        }
    
    def _analyze_line_coverage(
        self, 
        coverage_data: Dict[str, CoverageData]
    ) -> Dict[str, Any]:
        """分析行覆盖率"""
        total_lines = 0
        covered_lines = 0
        file_details = []
        
        for file_path, data in coverage_data.items():
            total_lines += data.total_lines
            covered_lines += data.covered_lines
            
            file_details.append({
                "file": file_path,
                "line_rate": data.line_rate,
                "covered": data.covered_lines,
                "total": data.total_lines,
                "missing_lines": data.missing_lines[:20]
            })
        
        overall_rate = (covered_lines / total_lines * 100) if total_lines > 0 else 0
        
        file_details.sort(key=lambda x: x["line_rate"])
        
        return {
            "overall_rate": overall_rate,
            "total_lines": total_lines,
            "covered_lines": covered_lines,
            "uncovered_lines": total_lines - covered_lines,
            "file_details": file_details,
            "low_coverage_files": [
                f for f in file_details if f["line_rate"] < 50
            ][:10]
        }
    
    def _analyze_branch_coverage(
        self, 
        coverage_data: Dict[str, CoverageData]
    ) -> Dict[str, Any]:
        """分析分支覆盖率"""
        total_branches = 0
        covered_branches = 0
        branch_details = []
        
        for file_path, data in coverage_data.items():
            estimated_branches = max(
                data.total_lines // 5,
                int(data.branch_rate * data.total_lines / 100) if data.branch_rate > 0 else 0
            )
            estimated_covered = int(data.branch_rate * estimated_branches / 100)
            
            total_branches += estimated_branches
            covered_branches += estimated_covered
            
            branch_details.append({
                "file": file_path,
                "branch_rate": data.branch_rate,
                "estimated_branches": estimated_branches,
                "estimated_covered": estimated_covered
            })
        
        overall_rate = (covered_branches / total_branches * 100) if total_branches > 0 else 0
        
        return {
            "overall_rate": overall_rate,
            "total_branches": total_branches,
            "covered_branches": covered_branches,
            "branch_details": branch_details,
            "low_branch_files": [
                b for b in branch_details if b["branch_rate"] < 50
            ][:10]
        }
    
    def _analyze_condition_coverage(
        self,
        coverage_data: Dict[str, CoverageData],
        spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        """分析条件覆盖率"""
        conditions = []
        
        for rule in spec.get("behavior_rules", []):
            condition = rule.get("condition", "")
            if condition:
                conditions.append({
                    "rule": rule.get("name", ""),
                    "condition": condition,
                    "covered": self._check_condition_coverage(condition, coverage_data)
                })
        
        for constraint in spec.get("constraints", []):
            rule_str = constraint.get("rule", "")
            if rule_str:
                conditions.append({
                    "constraint": constraint.get("name", ""),
                    "condition": rule_str,
                    "covered": self._check_condition_coverage(rule_str, coverage_data)
                })
        
        covered_count = sum(1 for c in conditions if c["covered"])
        total_count = len(conditions)
        rate = (covered_count / total_count * 100) if total_count > 0 else 100
        
        return {
            "overall_rate": rate,
            "total_conditions": total_count,
            "covered_conditions": covered_count,
            "uncovered_conditions": [c for c in conditions if not c["covered"]]
        }
    
    def _check_condition_coverage(
        self, 
        condition: str, 
        coverage_data: Dict[str, CoverageData]
    ) -> bool:
        """检查条件是否被覆盖"""
        keywords = condition.lower().split()
        
        for file_path, data in coverage_data.items():
            if data.line_rate > 0:
                for keyword in keywords:
                    if keyword in file_path.lower():
                        return True
        
        return len(keywords) == 0
    
    def _map_coverage_to_spec(
        self,
        coverage_data: Dict[str, CoverageData],
        spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        """将覆盖率映射到规范元素"""
        mappings = {}
        
        for iface in spec.get("interfaces", []):
            name = iface.get("name", "")
            related_files = self._find_related_files_for_element(name, coverage_data)
            avg_coverage = self._calculate_avg_coverage(related_files, coverage_data)
            mappings[f"interface:{name}"] = {
                "type": "interface",
                "name": name,
                "coverage": avg_coverage,
                "files": related_files
            }
        
        for model in spec.get("data_models", []):
            name = model.get("name", "")
            related_files = self._find_related_files_for_element(name, coverage_data)
            avg_coverage = self._calculate_avg_coverage(related_files, coverage_data)
            mappings[f"model:{name}"] = {
                "type": "data_model",
                "name": name,
                "coverage": avg_coverage,
                "files": related_files
            }
        
        for rule in spec.get("behavior_rules", []):
            name = rule.get("name", "")
            related_files = self._find_related_files_for_element(name, coverage_data)
            avg_coverage = self._calculate_avg_coverage(related_files, coverage_data)
            mappings[f"rule:{name}"] = {
                "type": "behavior_rule",
                "name": name,
                "coverage": avg_coverage,
                "files": related_files
            }
        
        return mappings
    
    def _find_related_files_for_element(
        self,
        element_name: str,
        coverage_data: Dict[str, CoverageData]
    ) -> List[str]:
        """查找与规范元素相关的文件"""
        related = []
        name_lower = element_name.lower()
        name_snake = re.sub(r'([A-Z])', r'_\1', element_name).lower().strip('_')
        
        for file_path in coverage_data.keys():
            file_lower = file_path.lower()
            if name_lower in file_lower or name_snake in file_lower:
                related.append(file_path)
        
        return related
    
    def _calculate_avg_coverage(
        self,
        files: List[str],
        coverage_data: Dict[str, CoverageData]
    ) -> float:
        """计算平均覆盖率"""
        if not files:
            return 0.0
        
        total = sum(coverage_data[f].line_rate for f in files if f in coverage_data)
        return total / len(files)
    
    def _identify_coverage_gaps(
        self,
        coverage_data: Dict[str, CoverageData],
        spec: Dict[str, Any],
        test_results: Optional[List[TestResult]]
    ) -> List[Dict[str, Any]]:
        """识别覆盖缺口"""
        gaps = []
        
        for file_path, data in coverage_data.items():
            if data.line_rate < 50:
                gaps.append({
                    "type": "low_coverage_file",
                    "file": file_path,
                    "coverage": data.line_rate,
                    "missing_lines": len(data.missing_lines),
                    "priority": 10 - int(data.line_rate / 10),
                    "suggestion": f"增加对 {file_path} 的测试覆盖"
                })
        
        for iface in spec.get("interfaces", []):
            name = iface.get("name", "")
            related_files = self._find_related_files_for_element(name, coverage_data)
            
            if not related_files:
                gaps.append({
                    "type": "uncovered_interface",
                    "element": name,
                    "priority": 8,
                    "suggestion": f"为接口 '{name}' 添加测试"
                })
        
        for scenario in spec.get("spec", {}).get("scenarios", []):
            scenario_name = scenario.get("name", "")
            
            if test_results:
                has_test = any(
                    scenario_name.lower() in t.test_name.lower()
                    for t in test_results
                )
                if not has_test:
                    gaps.append({
                        "type": "uncovered_scenario",
                        "element": scenario_name,
                        "priority": 6,
                        "suggestion": f"为场景 '{scenario_name}' 添加测试用例"
                    })
        
        gaps.sort(key=lambda x: x["priority"], reverse=True)
        return gaps[:20]
    
    def _analyze_coverage_trends(
        self, 
        coverage_data: Dict[str, CoverageData]
    ) -> Dict[str, Any]:
        """分析覆盖率趋势"""
        current_total = sum(d.total_lines for d in coverage_data.values())
        current_covered = sum(d.covered_lines for d in coverage_data.values())
        current_rate = (current_covered / current_total * 100) if current_total > 0 else 0
        
        trend_data = {
            "current_rate": current_rate,
            "history_count": len(self.coverage_history),
            "trend": "stable"
        }
        
        if self.coverage_history:
            last_rate = self.coverage_history[-1].get("rate", 0)
            diff = current_rate - last_rate
            
            if diff > 2:
                trend_data["trend"] = "improving"
            elif diff < -2:
                trend_data["trend"] = "declining"
        
        self.coverage_history.append({
            "rate": current_rate,
            "timestamp": datetime.now().isoformat()
        })
        
        if len(self.coverage_history) > 20:
            self.coverage_history = self.coverage_history[-20:]
        
        return trend_data
    
    def _generate_coverage_recommendations_enhanced(
        self,
        line_coverage: Dict[str, Any],
        branch_coverage: Dict[str, Any],
        condition_coverage: Dict[str, Any],
        gaps: List[Dict[str, Any]]
    ) -> List[str]:
        """生成增强的覆盖率建议"""
        recommendations = []
        
        if line_coverage["overall_rate"] < 70:
            recommendations.append(
                f"行覆盖率 ({line_coverage['overall_rate']:.1f}%) 低于70%，建议优先提高核心模块的测试覆盖"
            )
        
        if branch_coverage["overall_rate"] < 60:
            recommendations.append(
                f"分支覆盖率 ({branch_coverage['overall_rate']:.1f}%) 较低，建议增加边界条件测试"
            )
        
        if condition_coverage["overall_rate"] < 80:
            uncovered = condition_coverage["uncovered_conditions"]
            if uncovered:
                recommendations.append(
                    f"发现 {len(uncovered)} 个未覆盖的条件，建议添加相应的测试场景"
                )
        
        high_priority_gaps = [g for g in gaps if g["priority"] >= 7]
        if high_priority_gaps:
            recommendations.append(
                f"发现 {len(high_priority_gaps)} 个高优先级覆盖缺口，建议优先处理"
            )
        
        low_coverage_files = line_coverage.get("low_coverage_files", [])
        if low_coverage_files:
            files_str = ", ".join(f["file"].split("/")[-1] for f in low_coverage_files[:3])
            recommendations.append(
                f"以下文件覆盖率较低: {files_str}"
            )
        
        return recommendations
    
    def _create_coverage_summary(
        self,
        line_coverage: Dict[str, Any],
        branch_coverage: Dict[str, Any],
        condition_coverage: Dict[str, Any],
        gaps: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """创建覆盖率摘要"""
        overall_score = (
            line_coverage["overall_rate"] * 0.5 +
            branch_coverage["overall_rate"] * 0.3 +
            condition_coverage["overall_rate"] * 0.2
        )
        
        if overall_score >= 80:
            grade = "A"
            status = "excellent"
        elif overall_score >= 70:
            grade = "B"
            status = "good"
        elif overall_score >= 60:
            grade = "C"
            status = "acceptable"
        elif overall_score >= 50:
            grade = "D"
            status = "needs_improvement"
        else:
            grade = "F"
            status = "critical"
        
        return {
            "overall_score": round(overall_score, 2),
            "grade": grade,
            "status": status,
            "line_coverage": round(line_coverage["overall_rate"], 2),
            "branch_coverage": round(branch_coverage["overall_rate"], 2),
            "condition_coverage": round(condition_coverage["overall_rate"], 2),
            "total_gaps": len(gaps),
            "high_priority_gaps": len([g for g in gaps if g["priority"] >= 7])
        }


class FailurePatternRecognizer:
    """
    失败模式识别器
    
    智能识别测试失败的模式：
    - 重复失败模式识别
    - 根因聚类分析
    - 失败趋势预测
    - 关联失败分析
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or self._setup_logger()
        self.pattern_history: Dict[str, List[Dict[str, Any]]] = {}
        self.failure_clusters: Dict[str, List[str]] = {}
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger("FailurePatternRecognizer")
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def recognize_patterns(
        self,
        test_results: List[TestResult],
        failure_analyses: List[FailureAnalysis],
        historical_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        识别失败模式
        
        Args:
            test_results: 测试结果列表
            failure_analyses: 失败分析列表
            historical_data: 历史数据
            
        Returns:
            Dict[str, Any]: 模式识别结果
        """
        self.logger.info("开始失败模式识别...")
        
        recurring_patterns = self._find_recurring_patterns(
            test_results, failure_analyses, historical_data
        )
        
        root_cause_clusters = self._cluster_by_root_cause(failure_analyses)
        
        failure_trends = self._analyze_failure_trends(test_results, historical_data)
        
        related_failures = self._analyze_related_failures(test_results, failure_analyses)
        
        predictions = self._predict_future_failures(
            test_results, failure_analyses, historical_data
        )
        
        return {
            "recurring_patterns": recurring_patterns,
            "root_cause_clusters": root_cause_clusters,
            "failure_trends": failure_trends,
            "related_failures": related_failures,
            "predictions": predictions,
            "summary": self._create_pattern_summary(
                recurring_patterns, root_cause_clusters, failure_trends
            )
        }
    
    def _find_recurring_patterns(
        self,
        test_results: List[TestResult],
        failure_analyses: List[FailureAnalysis],
        historical_data: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """发现重复出现的失败模式"""
        patterns = []
        
        error_messages = {}
        for test in test_results:
            if test.status == TestStatus.FAILED and test.error_message:
                normalized = self._normalize_error_message(test.error_message)
                if normalized not in error_messages:
                    error_messages[normalized] = []
                error_messages[normalized].append(test.test_name)
        
        for normalized_msg, tests in error_messages.items():
            if len(tests) >= 2:
                patterns.append({
                    "pattern_type": "recurring_error",
                    "normalized_message": normalized_msg[:100],
                    "occurrence_count": len(tests),
                    "affected_tests": tests[:5],
                    "severity": "high" if len(tests) >= 3 else "medium"
                })
        
        category_counts = {}
        for analysis in failure_analyses:
            category = analysis.category.value
            if category not in category_counts:
                category_counts[category] = []
            category_counts[category].append(analysis.test_id)
        
        for category, test_ids in category_counts.items():
            if len(test_ids) >= 3:
                patterns.append({
                    "pattern_type": "category_cluster",
                    "category": category,
                    "occurrence_count": len(test_ids),
                    "affected_tests": test_ids[:5],
                    "severity": "high"
                })
        
        if historical_data and "previous_failures" in historical_data:
            for test in test_results:
                if test.status == TestStatus.FAILED:
                    if test.test_name in historical_data["previous_failures"]:
                        patterns.append({
                            "pattern_type": "persistent_failure",
                            "test_name": test.test_name,
                            "severity": "critical",
                            "suggestion": "该测试持续失败，需要深入分析根因"
                        })
        
        patterns.sort(key=lambda x: {"critical": 0, "high": 1, "medium": 2}.get(x.get("severity", "medium"), 2))
        return patterns[:15]
    
    def _normalize_error_message(self, message: str) -> str:
        """规范化错误消息"""
        normalized = re.sub(r'\d+', 'N', message)
        normalized = re.sub(r'0x[0-9a-fA-F]+', 'ADDR', normalized)
        normalized = re.sub(r"'.*?'", "'...'", normalized)
        normalized = re.sub(r'".*?"', '"..."', normalized)
        normalized = re.sub(r'/[\w/]+/', '/PATH/', normalized)
        return normalized
    
    def _cluster_by_root_cause(
        self, 
        failure_analyses: List[FailureAnalysis]
    ) -> Dict[str, Any]:
        """按根因聚类"""
        clusters = {}
        
        for analysis in failure_analyses:
            root_cause_key = self._extract_root_cause_key(analysis.root_cause)
            
            if root_cause_key not in clusters:
                clusters[root_cause_key] = {
                    "root_cause_pattern": root_cause_key,
                    "count": 0,
                    "tests": [],
                    "categories": set()
                }
            
            clusters[root_cause_key]["count"] += 1
            clusters[root_cause_key]["tests"].append(analysis.test_id)
            clusters[root_cause_key]["categories"].add(analysis.category.value)
        
        for cluster in clusters.values():
            cluster["categories"] = list(cluster["categories"])
        
        sorted_clusters = sorted(
            clusters.values(),
            key=lambda x: x["count"],
            reverse=True
        )
        
        return {
            "total_clusters": len(clusters),
            "top_clusters": sorted_clusters[:10],
            "cluster_distribution": {
                "single_failure": len([c for c in clusters.values() if c["count"] == 1]),
                "multiple_failures": len([c for c in clusters.values() if c["count"] > 1])
            }
        }
    
    def _extract_root_cause_key(self, root_cause: str) -> str:
        """提取根因关键字"""
        keywords = [
            "null", "None", "undefined", "type", "value", "index",
            "key", "attribute", "import", "syntax", "timeout",
            "connection", "permission", "memory", "assertion"
        ]
        
        root_lower = root_cause.lower()
        for keyword in keywords:
            if keyword in root_lower:
                return f"{keyword}_related"
        
        return "other"
    
    def _analyze_failure_trends(
        self,
        test_results: List[TestResult],
        historical_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """分析失败趋势"""
        current_failed = len([t for t in test_results if t.status == TestStatus.FAILED])
        current_total = len(test_results)
        current_rate = (current_failed / current_total * 100) if current_total > 0 else 0
        
        trend = {
            "current_failure_rate": current_rate,
            "current_failed_count": current_failed,
            "trend_direction": "stable",
            "prediction": "stable"
        }
        
        if historical_data and "failure_history" in historical_data:
            history = historical_data["failure_history"]
            if len(history) >= 2:
                rates = [h.get("rate", 0) for h in history[-5:]]
                rates.append(current_rate)
                
                if len(rates) >= 3:
                    recent_avg = sum(rates[-3:]) / 3
                    older_avg = sum(rates[:-3]) / len(rates[:-3]) if len(rates) > 3 else rates[0]
                    
                    if recent_avg > older_avg * 1.2:
                        trend["trend_direction"] = "increasing"
                        trend["prediction"] = "failure_rate_rising"
                    elif recent_avg < older_avg * 0.8:
                        trend["trend_direction"] = "decreasing"
                        trend["prediction"] = "failure_rate_falling"
        
        return trend
    
    def _analyze_related_failures(
        self,
        test_results: List[TestResult],
        failure_analyses: List[FailureAnalysis]
    ) -> List[Dict[str, Any]]:
        """分析关联失败"""
        related_groups = []
        
        failed_tests = [t for t in test_results if t.status == TestStatus.FAILED]
        
        by_module = {}
        for test in failed_tests:
            module = self._extract_module(test.test_name)
            if module not in by_module:
                by_module[module] = []
            by_module[module].append(test.test_name)
        
        for module, tests in by_module.items():
            if len(tests) >= 2:
                related_groups.append({
                    "relation_type": "same_module",
                    "module": module,
                    "failed_tests": tests,
                    "count": len(tests),
                    "suggestion": f"模块 '{module}' 有多个测试失败，可能存在共同问题"
                })
        
        by_spec_element = {}
        for analysis in failure_analyses:
            element = analysis.related_spec_element
            if element:
                if element not in by_spec_element:
                    by_spec_element[element] = []
                by_spec_element[element].append(analysis.test_id)
        
        for element, tests in by_spec_element.items():
            if len(tests) >= 2:
                related_groups.append({
                    "relation_type": "same_spec_element",
                    "spec_element": element,
                    "failed_tests": tests,
                    "count": len(tests),
                    "suggestion": f"规范元素 '{element}' 相关的多个测试失败"
                })
        
        return related_groups[:10]
    
    def _extract_module(self, test_name: str) -> str:
        """从测试名称提取模块"""
        parts = test_name.replace("_", ".").split(".")
        if len(parts) > 1:
            return parts[0]
        return "unknown"
    
    def _predict_future_failures(
        self,
        test_results: List[TestResult],
        failure_analyses: List[FailureAnalysis],
        historical_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """预测未来可能的失败"""
        predictions = {
            "high_risk_tests": [],
            "predicted_failure_areas": [],
            "confidence": 0.0
        }
        
        flaky_tests = []
        if historical_data and "test_history" in historical_data:
            for test_name, history in historical_data["test_history"].items():
                if len(history) >= 3:
                    failure_rate = sum(1 for h in history if h == "failed") / len(history)
                    if 0.2 <= failure_rate <= 0.8:
                        flaky_tests.append({
                            "test_name": test_name,
                            "failure_rate": failure_rate,
                            "risk": "high" if failure_rate >= 0.5 else "medium"
                        })
        
        predictions["high_risk_tests"] = flaky_tests[:5]
        
        for analysis in failure_analyses:
            if analysis.confidence >= 0.8 and analysis.category in [
                FailureCategory.EXCEPTION, FailureCategory.ASSERTION
            ]:
                predictions["predicted_failure_areas"].append({
                    "area": analysis.related_spec_element,
                    "reason": analysis.root_cause[:100],
                    "confidence": analysis.confidence
                })
        
        if predictions["high_risk_tests"] or predictions["predicted_failure_areas"]:
            predictions["confidence"] = 0.7
        else:
            predictions["confidence"] = 0.5
        
        return predictions
    
    def _create_pattern_summary(
        self,
        recurring_patterns: List[Dict[str, Any]],
        root_cause_clusters: Dict[str, Any],
        failure_trends: Dict[str, Any]
    ) -> Dict[str, Any]:
        """创建模式摘要"""
        critical_patterns = len([p for p in recurring_patterns if p.get("severity") == "critical"])
        high_patterns = len([p for p in recurring_patterns if p.get("severity") == "high"])
        
        return {
            "total_patterns": len(recurring_patterns),
            "critical_patterns": critical_patterns,
            "high_severity_patterns": high_patterns,
            "total_clusters": root_cause_clusters.get("total_clusters", 0),
            "trend_direction": failure_trends.get("trend_direction", "stable"),
            "overall_risk": self._calculate_overall_risk(
                critical_patterns, high_patterns, failure_trends
            )
        }
    
    def _calculate_overall_risk(
        self,
        critical: int,
        high: int,
        trends: Dict[str, Any]
    ) -> str:
        """计算整体风险等级"""
        if critical >= 2 or trends.get("trend_direction") == "increasing":
            return "high"
        elif critical >= 1 or high >= 3:
            return "medium"
        elif high >= 1:
            return "low"
        else:
            return "minimal"


class IntelligentFeedbackGenerator:
    """
    智能反馈生成器
    
    实现测试结果到规范的智能反馈：
    - 规范不一致检测
    - 缺失规范识别
    - 规范改进建议
    - 自动修复建议
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or self._setup_logger()
        self.feedback_templates = self._load_feedback_templates()
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger("IntelligentFeedbackGenerator")
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def _load_feedback_templates(self) -> Dict[str, Any]:
        """加载反馈模板"""
        return {
            "spec_inconsistency": {
                "template": "规范元素 '{element}' 的定义与测试行为不一致",
                "suggestion": "更新规范定义或修改实现以保持一致"
            },
            "missing_spec": {
                "template": "测试覆盖了规范中未定义的行为: {behavior}",
                "suggestion": "在规范中添加该行为的定义"
            },
            "ambiguous_spec": {
                "template": "规范元素 '{element}' 的定义不够明确",
                "suggestion": "添加更详细的描述和示例"
            },
            "outdated_spec": {
                "template": "规范元素 '{element}' 可能已过时",
                "suggestion": "检查并更新规范以反映当前实现"
            }
        }
    
    def generate_intelligent_feedback_enhanced(
        self,
        test_results: List[TestResult],
        failure_analyses: List[FailureAnalysis],
        spec: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        生成增强的智能反馈
        
        Args:
            test_results: 测试结果列表
            failure_analyses: 失败分析列表
            spec: 规范字典
            context: 上下文信息
            
        Returns:
            Dict[str, Any]: 智能反馈结果
        """
        self.logger.info("生成增强的智能反馈...")
        
        spec_inconsistencies = self._detect_spec_inconsistencies(
            test_results, failure_analyses, spec
        )
        
        missing_specs = self._identify_missing_specs(
            test_results, failure_analyses, spec
        )
        
        improvement_suggestions = self._generate_improvement_suggestions_intelligent(
            test_results, failure_analyses, spec, context
        )
        
        auto_fix_suggestions = self._generate_auto_fix_suggestions(
            test_results, failure_analyses, spec
        )
        
        return {
            "spec_inconsistencies": spec_inconsistencies,
            "missing_specs": missing_specs,
            "improvement_suggestions": improvement_suggestions,
            "auto_fix_suggestions": auto_fix_suggestions,
            "summary": self._create_feedback_summary(
                spec_inconsistencies, missing_specs, improvement_suggestions
            )
        }
    
    def _detect_spec_inconsistencies(
        self,
        test_results: List[TestResult],
        failure_analyses: List[FailureAnalysis],
        spec: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """检测规范不一致"""
        inconsistencies = []
        
        if not spec:
            return inconsistencies
        
        for analysis in failure_analyses:
            element = analysis.related_spec_element
            if element:
                spec_element = self._find_spec_element(spec, element)
                
                if spec_element:
                    if analysis.category == FailureCategory.ASSERTION:
                        inconsistencies.append({
                            "type": "behavior_mismatch",
                            "element": element,
                            "expected": spec_element.get("description", ""),
                            "actual": analysis.error_message[:100],
                            "test_id": analysis.test_id,
                            "severity": "high",
                            "suggestion": self._generate_consistency_fix(element, analysis)
                        })
                    
                    if analysis.category == FailureCategory.TYPE:
                        inconsistencies.append({
                            "type": "type_mismatch",
                            "element": element,
                            "spec_type": spec_element.get("type", ""),
                            "actual_type": self._extract_type_from_error(analysis.error_message),
                            "test_id": analysis.test_id,
                            "severity": "medium",
                            "suggestion": "统一规范和代码中的类型定义"
                        })
        
        return inconsistencies
    
    def _find_spec_element(
        self, 
        spec: Dict[str, Any], 
        element_name: str
    ) -> Optional[Dict[str, Any]]:
        """在规范中查找元素"""
        for iface in spec.get("interfaces", []):
            if iface.get("name", "").lower() == element_name.lower():
                return iface
        
        for model in spec.get("data_models", []):
            if model.get("name", "").lower() == element_name.lower():
                return model
        
        for rule in spec.get("behavior_rules", []):
            if rule.get("name", "").lower() == element_name.lower():
                return rule
        
        return None
    
    def _generate_consistency_fix(
        self, 
        element: str, 
        analysis: FailureAnalysis
    ) -> str:
        """生成一致性修复建议"""
        if "expected" in analysis.error_message.lower():
            return f"更新规范元素 '{element}' 的预期行为定义"
        else:
            return f"检查 '{element}' 的实现是否符合规范定义"
    
    def _extract_type_from_error(self, error_message: str) -> str:
        """从错误消息中提取类型"""
        type_patterns = [
            r"expected\s+(\w+)",
            r"got\s+(\w+)",
            r"type\s+'(\w+)'",
        ]
        
        for pattern in type_patterns:
            match = re.search(pattern, error_message, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return "unknown"
    
    def _identify_missing_specs(
        self,
        test_results: List[TestResult],
        failure_analyses: List[FailureAnalysis],
        spec: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """识别缺失的规范"""
        missing = []
        
        if not spec:
            return missing
        
        spec_elements = set()
        for iface in spec.get("interfaces", []):
            spec_elements.add(iface.get("name", "").lower())
        for model in spec.get("data_models", []):
            spec_elements.add(model.get("name", "").lower())
        
        for test in test_results:
            test_elements = self._extract_elements_from_test(test.test_name)
            
            for element in test_elements:
                if element.lower() not in spec_elements:
                    missing.append({
                        "type": "missing_element",
                        "element": element,
                        "test_name": test.test_name,
                        "suggestion": f"在规范中添加 '{element}' 的定义"
                    })
        
        for analysis in failure_analyses:
            if analysis.category == FailureCategory.EXCEPTION:
                exception_type = self._extract_exception_type(analysis.error_message)
                if exception_type:
                    spec_exceptions = self._get_spec_exceptions(spec, analysis.related_spec_element)
                    if exception_type not in spec_exceptions:
                        missing.append({
                            "type": "missing_exception_spec",
                            "element": analysis.related_spec_element,
                            "exception": exception_type,
                            "test_id": analysis.test_id,
                            "suggestion": f"在规范中添加异常 '{exception_type}' 的定义"
                        })
        
        return missing[:15]
    
    def _extract_elements_from_test(self, test_name: str) -> List[str]:
        """从测试名称提取元素"""
        elements = []
        
        parts = re.split(r"[_\s]", test_name)
        for part in parts:
            if len(part) > 3 and not part.lower().startswith("test"):
                elements.append(part)
        
        return elements
    
    def _extract_exception_type(self, error_message: str) -> Optional[str]:
        """从错误消息提取异常类型"""
        match = re.search(r"(\w+Error|\w+Exception)", error_message)
        return match.group(1) if match else None
    
    def _get_spec_exceptions(
        self, 
        spec: Dict[str, Any], 
        element_name: str
    ) -> List[str]:
        """获取规范中定义的异常"""
        spec_element = self._find_spec_element(spec, element_name)
        if spec_element:
            return spec_element.get("exceptions", [])
        return []
    
    def _generate_improvement_suggestions_intelligent(
        self,
        test_results: List[TestResult],
        failure_analyses: List[FailureAnalysis],
        spec: Optional[Dict[str, Any]],
        context: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """智能生成改进建议"""
        suggestions = []
        
        category_failures = {}
        for analysis in failure_analyses:
            category = analysis.category.value
            if category not in category_failures:
                category_failures[category] = []
            category_failures[category].append(analysis)
        
        for category, analyses in category_failures.items():
            if len(analyses) >= 3:
                suggestions.append({
                    "type": "category_improvement",
                    "category": category,
                    "count": len(analyses),
                    "priority": "high",
                    "suggestion": f"建议加强 {category} 相关的规范定义和测试覆盖"
                })
        
        if spec:
            for iface in spec.get("interfaces", []):
                name = iface.get("name", "")
                description = iface.get("description", "")
                
                if not description or len(description) < 20:
                    suggestions.append({
                        "type": "missing_description",
                        "element": name,
                        "priority": "medium",
                        "suggestion": f"为接口 '{name}' 添加更详细的描述"
                    })
        
        if context and context.get("project_phase") == "production":
            critical_suggestions = [s for s in suggestions if s.get("priority") == "high"]
            for s in critical_suggestions:
                s["priority"] = "critical"
                s["note"] = "生产环境需要优先处理"
        
        return suggestions[:10]
    
    def _generate_auto_fix_suggestions(
        self,
        test_results: List[TestResult],
        failure_analyses: List[FailureAnalysis],
        spec: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """生成自动修复建议"""
        auto_fixes = []
        
        for analysis in failure_analyses:
            if analysis.category == FailureCategory.TYPE:
                auto_fixes.append({
                    "type": "type_annotation",
                    "element": analysis.related_spec_element,
                    "test_id": analysis.test_id,
                    "auto_fixable": True,
                    "fix_description": "可以自动添加或更新类型注解"
                })
            
            if "None" in analysis.error_message or "null" in analysis.error_message.lower():
                auto_fixes.append({
                    "type": "null_check",
                    "element": analysis.related_spec_element,
                    "test_id": analysis.test_id,
                    "auto_fixable": True,
                    "fix_description": "可以自动添加空值检查"
                })
            
            if analysis.category == FailureCategory.ASSERTION:
                expected_value = self._extract_expected_value(analysis.error_message)
                if expected_value:
                    auto_fixes.append({
                        "type": "update_expected",
                        "element": analysis.related_spec_element,
                        "test_id": analysis.test_id,
                        "expected_value": expected_value,
                        "auto_fixable": True,
                        "fix_description": f"可以自动更新预期值为 '{expected_value}'"
                    })
        
        return auto_fixes[:10]
    
    def _extract_expected_value(self, error_message: str) -> Optional[str]:
        """从错误消息提取预期值"""
        match = re.search(r"expected\s+['\"]?([^'\"]+)['\"]?", error_message, re.IGNORECASE)
        return match.group(1) if match else None
    
    def _create_feedback_summary(
        self,
        inconsistencies: List[Dict[str, Any]],
        missing_specs: List[Dict[str, Any]],
        suggestions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """创建反馈摘要"""
        return {
            "total_inconsistencies": len(inconsistencies),
            "total_missing_specs": len(missing_specs),
            "total_suggestions": len(suggestions),
            "high_priority_count": len([s for s in suggestions if s.get("priority") in ["high", "critical"]]),
            "auto_fixable_count": len([s for s in suggestions if s.get("auto_fixable")]),
            "overall_status": self._determine_overall_status(
                inconsistencies, missing_specs, suggestions
            )
        }
    
    def _determine_overall_status(
        self,
        inconsistencies: List[Dict[str, Any]],
        missing_specs: List[Dict[str, Any]],
        suggestions: List[Dict[str, Any]]
    ) -> str:
        """确定整体状态"""
        critical = len([s for s in suggestions if s.get("priority") == "critical"])
        high = len([s for s in suggestions if s.get("priority") == "high"])
        
        if critical > 0 or len(inconsistencies) > 5:
            return "needs_immediate_attention"
        elif high > 3 or len(missing_specs) > 5:
            return "needs_attention"
        elif len(suggestions) > 0:
            return "has_suggestions"
        else:
            return "healthy"


if __name__ == "__main__":
    main()
