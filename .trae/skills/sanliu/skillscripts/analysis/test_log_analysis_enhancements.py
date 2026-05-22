#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志分析与问题定位功能单元测试

测试覆盖：
- log_analyzer.py 增强功能
- log_correlation_analyzer.py 增强功能
- issue_locator.py 增强功能
"""

import unittest
from datetime import datetime, timedelta
from pathlib import Path
import sys
import os

sys.path.insert(0, str(get_path_config().SCRIPTS_DIR / "analysis"))

from log_analyzer import (
    LogEntry, LogLevel, ErrorCategory,
    LogAggregator, SyntaxErrorDetector, LogicErrorDetector
)
from log_correlation_analyzer import (
    LogEvent, LogSource,
    MultiSourceLogCorrelator, ErrorPropagationChainAnalyzer,
    TimeSeriesAdvancedAnalyzer, CorrelationReportEnhancer
)
from issue_locator import (
from skillscripts.core.path_config_center import get_path_config
    IssueLocation, IssueType, Severity, Confidence, CodeLocation,
    StackTraceFrame, RootCause, ImpactScope, FixPriority,
    EnhancedImpactAnalyzer, EnhancedFixPriorityEvaluator,
    CodeLocationPreciseLocator, IssueLocationReportEnhancer,
    IssueLocationReport
)


class TestLogAggregator(unittest.TestCase):
    """测试日志聚合统计功能"""
    
    def setUp(self):
        self.aggregator = LogAggregator()
        self.entries = self._create_test_entries()
    
    def _create_test_entries(self):
        entries = []
        base_time = datetime.now() - timedelta(hours=1)
        
        for i in range(20):
            entry = LogEntry(
                timestamp=base_time + timedelta(minutes=i * 3),
                level=LogLevel.ERROR if i % 3 == 0 else LogLevel.INFO if i % 2 == 0 else LogLevel.WARNING,
                message=f"Test message {i}: Error occurred" if i % 3 == 0 else f"Test message {i}",
                source="test_app",
                file_path=f"/app/test_{i % 3}.py",
                line_number=i * 10,
                error_category=ErrorCategory.RUNTIME if i % 3 == 0 else None
            )
            entries.append(entry)
        
        return entries
    
    def test_aggregate_returns_dict(self):
        result = self.aggregator.aggregate(self.entries)
        self.assertIsInstance(result, dict)
    
    def test_aggregate_contains_required_keys(self):
        result = self.aggregator.aggregate(self.entries)
        required_keys = [
            'time_window_aggregation', 'level_distribution',
            'category_distribution', 'source_distribution',
            'error_clustering', 'statistical_summary'
        ]
        for key in required_keys:
            self.assertIn(key, result)
    
    def test_level_distribution(self):
        result = self.aggregator.aggregate(self.entries)
        level_dist = result['level_distribution']
        self.assertIn('counts', level_dist)
        self.assertIn('total', level_dist)
        self.assertEqual(level_dist['total'], 20)
    
    def test_error_clustering(self):
        result = self.aggregator.aggregate(self.entries)
        clusters = result['error_clustering']
        self.assertIsInstance(clusters, list)
    
    def test_statistical_summary(self):
        result = self.aggregator.aggregate(self.entries)
        summary = result['statistical_summary']
        self.assertEqual(summary['total_entries'], 20)
        self.assertIn('error_rate', summary)
    
    def test_empty_entries(self):
        result = self.aggregator.aggregate([])
        self.assertIn('error', result)


class TestSyntaxErrorDetector(unittest.TestCase):
    """测试语法错误检测功能"""
    
    def setUp(self):
        self.detector = SyntaxErrorDetector()
    
    def test_detect_python_syntax_error(self):
        entry = LogEntry(
            timestamp=datetime.now(),
            level=LogLevel.ERROR,
            message="SyntaxError: invalid syntax at line 10",
            source="test"
        )
        errors = self.detector.detect(entry)
        self.assertTrue(len(errors) > 0)
        self.assertEqual(errors[0]['error_type'], 'python_syntax')
    
    def test_detect_json_parse_error(self):
        entry = LogEntry(
            timestamp=datetime.now(),
            level=LogLevel.ERROR,
            message="JSONDecodeError: Expecting property name enclosed in double quotes",
            source="test"
        )
        errors = self.detector.detect(entry)
        self.assertTrue(len(errors) > 0)
        self.assertEqual(errors[0]['error_type'], 'json_parse')
    
    def test_detect_sql_syntax_error(self):
        entry = LogEntry(
            timestamp=datetime.now(),
            level=LogLevel.ERROR,
            message="SQL syntax error near 'SELECT * FORM'",
            source="test"
        )
        errors = self.detector.detect(entry)
        self.assertTrue(len(errors) > 0)
    
    def test_detect_all_method(self):
        entries = [
            LogEntry(timestamp=datetime.now(), level=LogLevel.ERROR, 
                    message="SyntaxError: invalid syntax", source="test"),
            LogEntry(timestamp=datetime.now(), level=LogLevel.ERROR,
                    message="IndentationError: expected an indented block", source="test"),
        ]
        result = self.detector.detect_all(entries)
        self.assertIn('total_syntax_errors', result)
        self.assertEqual(result['total_syntax_errors'], 2)
    
    def test_no_syntax_error(self):
        entry = LogEntry(
            timestamp=datetime.now(),
            level=LogLevel.ERROR,
            message="Connection refused error",
            source="test"
        )
        errors = self.detector.detect(entry)
        self.assertEqual(len(errors), 0)


class TestLogicErrorDetector(unittest.TestCase):
    """测试逻辑错误检测功能"""
    
    def setUp(self):
        self.detector = LogicErrorDetector()
    
    def test_detect_assertion_error(self):
        entry = LogEntry(
            timestamp=datetime.now(),
            level=LogLevel.ERROR,
            message="AssertionError: expected value to be true",
            source="test"
        )
        errors = self.detector.detect(entry)
        self.assertTrue(len(errors) > 0)
        self.assertEqual(errors[0]['error_type'], 'assertion_failed')
    
    def test_detect_invalid_state(self):
        entry = LogEntry(
            timestamp=datetime.now(),
            level=LogLevel.ERROR,
            message="Invalid state: object is not initialized",
            source="test"
        )
        errors = self.detector.detect(entry)
        self.assertTrue(len(errors) > 0)
    
    def test_detect_validation_failed(self):
        entry = LogEntry(
            timestamp=datetime.now(),
            level=LogLevel.ERROR,
            message="Validation failed: email format is invalid",
            source="test"
        )
        errors = self.detector.detect(entry)
        self.assertTrue(len(errors) > 0)
    
    def test_error_categorization(self):
        entry = LogEntry(
            timestamp=datetime.now(),
            level=LogLevel.ERROR,
            message="AssertionError: test failed",
            source="test"
        )
        errors = self.detector.detect(entry)
        self.assertIn('category', errors[0])
        self.assertEqual(errors[0]['category'], 'assertion')


class TestMultiSourceLogCorrelator(unittest.TestCase):
    """测试多源日志关联功能"""
    
    def setUp(self):
        self.correlator = MultiSourceLogCorrelator()
    
    def test_classify_application_source(self):
        source = LogSource(
            source_id="app1",
            name="Application Log",
            path="/var/log/app.log",
            system="myapp",
            log_format="json"
        )
        source_type = self.correlator.classify_source(source)
        self.assertEqual(source_type, 'application')
    
    def test_classify_database_source(self):
        source = LogSource(
            source_id="db1",
            name="MySQL Database",
            path="/var/log/mysql/error.log",
            system="mysql",
            log_format="text"
        )
        source_type = self.correlator.classify_source(source)
        self.assertEqual(source_type, 'database')
    
    def test_correlate_multi_source(self):
        sources = [
            LogSource(source_id="app1", name="App", path="/app.log", system="app", log_format="json"),
            LogSource(source_id="db1", name="DB", path="/db.log", system="db", log_format="text"),
        ]
        
        base_time = datetime.now()
        events = [
            LogEvent(
                event_id="e1",
                timestamp=base_time,
                level="ERROR",
                message="Connection timeout to database",
                source=sources[0]
            ),
            LogEvent(
                event_id="e2",
                timestamp=base_time + timedelta(seconds=5),
                level="ERROR",
                message="slow query execution time exceeded",
                source=sources[1]
            ),
        ]
        
        correlations = self.correlator.correlate_multi_source(events, sources)
        self.assertIsInstance(correlations, list)


class TestErrorPropagationChainAnalyzer(unittest.TestCase):
    """测试错误传播链分析功能"""
    
    def setUp(self):
        self.analyzer = ErrorPropagationChainAnalyzer()
        self.events = self._create_test_events()
    
    def _create_test_events(self):
        events = []
        base_time = datetime.now()
        
        source = LogSource(
            source_id="test",
            name="Test",
            path="/test.log",
            system="test_system",
            log_format="text"
        )
        
        for i in range(10):
            event = LogEvent(
                event_id=f"e{i}",
                timestamp=base_time + timedelta(seconds=i * 10),
                level="ERROR" if i % 2 == 0 else "WARNING",
                message=f"Error occurred caused by previous error" if i % 3 == 0 else f"Event {i}",
                source=source
            )
            events.append(event)
        
        return events
    
    def test_analyze_propagation_patterns(self):
        result = self.analyzer.analyze_propagation_patterns(self.events)
        self.assertIn('summary', result)
        self.assertIn('direct_propagation_chains', result)
        self.assertIn('indirect_propagation_chains', result)
    
    def test_summary_contains_counts(self):
        result = self.analyzer.analyze_propagation_patterns(self.events)
        summary = result['summary']
        self.assertIn('total_chains', summary)


class TestTimeSeriesAdvancedAnalyzer(unittest.TestCase):
    """测试高级时间序列分析功能"""
    
    def setUp(self):
        self.analyzer = TimeSeriesAdvancedAnalyzer()
        self.events = self._create_test_events()
    
    def _create_test_events(self):
        events = []
        base_time = datetime.now() - timedelta(hours=2)
        
        source = LogSource(
            source_id="test",
            name="Test",
            path="/test.log",
            system="test",
            log_format="text"
        )
        
        for i in range(50):
            event = LogEvent(
                event_id=f"e{i}",
                timestamp=base_time + timedelta(minutes=i * 2),
                level="ERROR" if i % 4 == 0 else "INFO",
                message=f"Event {i}",
                source=source
            )
            events.append(event)
        
        return events
    
    def test_analyze_returns_dict(self):
        result = self.analyzer.analyze(self.events)
        self.assertIsInstance(result, dict)
    
    def test_analyze_contains_required_keys(self):
        result = self.analyzer.analyze(self.events)
        self.assertIn('error_time_series', result)
        self.assertIn('volume_time_series', result)
        self.assertIn('cross_correlation', result)
        self.assertIn('periodicity_analysis', result)
    
    def test_trend_calculation(self):
        result = self.analyzer.analyze(self.events)
        error_series = result['error_time_series']
        self.assertIn('trend', error_series)
    
    def test_empty_events(self):
        result = self.analyzer.analyze([])
        self.assertIn('error', result)


class TestCorrelationReportEnhancer(unittest.TestCase):
    """测试关联分析报告增强功能"""
    
    def test_enhancer_initialization(self):
        enhancer = CorrelationReportEnhancer()
        self.assertIsNotNone(enhancer)


class TestEnhancedImpactAnalyzer(unittest.TestCase):
    """测试增强影响范围分析功能"""
    
    def setUp(self):
        self.analyzer = EnhancedImpactAnalyzer()
    
    def test_analyze_service_impact(self):
        location = CodeLocation(
            file_path="/app/services/user_service.py",
            line_number=100,
            function_name="get_user",
            class_name="UserService"
        )
        result = self.analyzer.analyze_enhanced(location)
        self.assertIn('service_impact', result)
        self.assertIn('database_impact', result)
        self.assertIn('cache_impact', result)
    
    def test_analyze_database_impact(self):
        location = CodeLocation(
            file_path="/app/repository.py",
            line_number=50,
            function_name="save_user",
            code_snippet="session.execute('INSERT INTO users')"
        )
        result = self.analyzer.analyze_enhanced(location)
        db_impact = result['database_impact']
        self.assertTrue(len(db_impact['db_operations']) > 0)
    
    def test_analyze_user_experience_impact(self):
        location = CodeLocation(
            file_path="/app/api/controller.py",
            line_number=100,
            function_name="handle_request"
        )
        result = self.analyzer.analyze_enhanced(location)
        ux_impact = result['user_experience_impact']
        self.assertTrue(ux_impact['user_facing'])


class TestEnhancedFixPriorityEvaluator(unittest.TestCase):
    """测试增强修复优先级评估功能"""
    
    def setUp(self):
        self.evaluator = EnhancedFixPriorityEvaluator()
    
    def _create_test_issue(self, severity=Severity.HIGH, issue_type=IssueType.RUNTIME_ERROR):
        return IssueLocation(
            location_id="TEST-001",
            issue_type=issue_type,
            severity=severity,
            title="Test Issue",
            description="TypeError: 'NoneType' object has no attribute 'x'",
            primary_location=CodeLocation(
                file_path="/app/payment_service.py",
                line_number=100,
                function_name="process_payment"
            ),
            root_cause=RootCause(
                cause_id="RC-001",
                description="Null reference",
                location=None,
                confidence=Confidence.HIGH,
                evidence=["Test evidence"],
                contributing_factors=["根因类型: 空值引用"],
                fix_complexity="medium"
            ),
            call_chain=None,
            impact_scope=None,
            suggestions=["Add null check"],
            related_issues=[]
        )
    
    def test_evaluate_returns_dict(self):
        issue = self._create_test_issue()
        result = self.evaluator.evaluate_enhanced(issue)
        self.assertIsInstance(result, dict)
    
    def test_evaluate_contains_required_keys(self):
        issue = self._create_test_issue()
        result = self.evaluator.evaluate_enhanced(issue)
        required_keys = [
            'priority_id', 'business_impact_score', 'security_risk_score',
            'composite_score', 'priority_level', 'recommended_action'
        ]
        for key in required_keys:
            self.assertIn(key, result)
    
    def test_security_issue_high_priority(self):
        issue = self._create_test_issue(issue_type=IssueType.SECURITY_ISSUE)
        result = self.evaluator.evaluate_enhanced(issue)
        self.assertEqual(result['security_risk_score'], 1.0)
    
    def test_critical_severity_high_priority(self):
        issue = self._create_test_issue(severity=Severity.CRITICAL)
        result = self.evaluator.evaluate_enhanced(issue)
        self.assertTrue(any('严重' in f for f in result['risk_factors']))


class TestCodeLocationPreciseLocator(unittest.TestCase):
    """测试代码位置精确定位功能"""
    
    def setUp(self):
        self.locator = CodeLocationPreciseLocator()
    
    def test_locate_from_error_message(self):
        error_message = 'File "/app/test.py", line 42, in main\nTypeError: test error'
        result = self.locator.locate_precise(error_message)
        self.assertIsNotNone(result['primary_location'])
        self.assertEqual(result['primary_location']['line_number'], 42)
    
    def test_locate_with_stack_trace(self):
        frames = [
            StackTraceFrame(
                file_path="/app/test.py",
                line_number=100,
                function_name="main",
                code_line="result = process()",
                is_user_code=True
            ),
            StackTraceFrame(
                file_path="/app/processor.py",
                line_number=50,
                function_name="process",
                code_line="return compute()",
                is_user_code=True
            )
        ]
        result = self.locator.locate_precise("Error occurred", frames)
        self.assertIsNotNone(result['primary_location'])
        self.assertEqual(result['primary_location']['function_name'], 'main')
    
    def test_build_call_graph(self):
        frames = [
            StackTraceFrame(file_path="/a.py", line_number=1, function_name="a", code_line="", is_user_code=True),
            StackTraceFrame(file_path="/b.py", line_number=2, function_name="b", code_line="", is_user_code=True),
        ]
        result = self.locator.locate_precise("Error", frames)
        call_graph = result['call_graph']
        self.assertEqual(len(call_graph['nodes']), 2)
        self.assertEqual(len(call_graph['edges']), 1)


class TestIssueLocationReportEnhancer(unittest.TestCase):
    """测试问题定位报告增强功能"""
    
    def setUp(self):
        self.enhancer = IssueLocationReportEnhancer()
        self.report = self._create_test_report()
    
    def _create_test_report(self):
        issues = [
            IssueLocation(
                location_id="ISSUE-001",
                issue_type=IssueType.RUNTIME_ERROR,
                severity=Severity.HIGH,
                title="Test Issue 1",
                description="TypeError",
                primary_location=CodeLocation(file_path="/app/test.py", line_number=100),
                root_cause=None,
                call_chain=None,
                impact_scope=None,
                suggestions=[],
                related_issues=[]
            ),
            IssueLocation(
                location_id="ISSUE-002",
                issue_type=IssueType.SECURITY_ISSUE,
                severity=Severity.CRITICAL,
                title="Security Issue",
                description="SQL Injection vulnerability",
                primary_location=CodeLocation(file_path="/app/db.py", line_number=50),
                root_cause=None,
                call_chain=None,
                impact_scope=None,
                suggestions=[],
                related_issues=[]
            )
        ]
        
        return IssueLocationReport(
            report_id="TEST-001",
            generated_at=datetime.now().isoformat(),
            issues=issues,
            summary="Test summary",
            total_issues=2,
            critical_count=1,
            high_count=1,
            medium_count=0,
            low_count=0
        )
    
    def test_enhance_report_returns_dict(self):
        result = self.enhancer.enhance_report(self.report)
        self.assertIsInstance(result, dict)
    
    def test_enhance_report_contains_required_keys(self):
        result = self.enhancer.enhance_report(self.report)
        required_keys = [
            'enhanced_summary', 'issue_breakdown', 'trend_analysis',
            'fix_recommendations', 'resource_estimation', 'risk_assessment'
        ]
        for key in required_keys:
            self.assertIn(key, result)
    
    def test_health_score_calculation(self):
        result = self.enhancer.enhance_report(self.report)
        health_score = result['enhanced_summary']['health_score']
        self.assertLess(health_score, 100)
        self.assertGreaterEqual(health_score, 0)
    
    def test_risk_assessment(self):
        result = self.enhancer.enhance_report(self.report)
        risk = result['risk_assessment']
        self.assertEqual(risk['overall_risk'], 'high')


class TestIntegration(unittest.TestCase):
    """集成测试"""
    
    def test_log_analyzer_to_correlator_integration(self):
        log_entries = [
            LogEntry(
                timestamp=datetime.now(),
                level=LogLevel.ERROR,
                message="SyntaxError: invalid syntax at line 10",
                source="app"
            )
        ]
        
        detector = SyntaxErrorDetector()
        syntax_errors = detector.detect_all(log_entries)
        
        self.assertGreater(syntax_errors['total_syntax_errors'], 0)
    
    def test_issue_locator_priority_integration(self):
        issue = IssueLocation(
            location_id="INT-001",
            issue_type=IssueType.SECURITY_ISSUE,
            severity=Severity.CRITICAL,
            title="Security Issue",
            description="SQL Injection in payment module",
            primary_location=CodeLocation(
                file_path="/app/payment.py",
                line_number=100,
                function_name="process_payment"
            ),
            root_cause=None,
            call_chain=None,
            impact_scope=None,
            suggestions=["Use parameterized queries"],
            related_issues=[]
        )
        
        evaluator = EnhancedFixPriorityEvaluator()
        priority = evaluator.evaluate_enhanced(issue)
        
        self.assertLessEqual(priority['priority_level'], 2)


if __name__ == '__main__':
    unittest.main(verbosity=2)
