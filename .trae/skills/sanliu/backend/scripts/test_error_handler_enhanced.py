#!/usr/bin/env python3
"""
增强版错误处理系统测试
测试错误智能捕获、智能恢复和错误通知的增强功能
"""

import os
import sys
import json
import time
import threading
import asyncio
import tempfile
import unittest
from pathlib import Path
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from error_handler_enhanced import (
    EnhancedErrorContextRecorder,
    EnhancedErrorClassifier,
    EnhancedErrorReportGenerator,
    EnhancedRecoveryEngine,
    EnhancedRecoveryReportGenerator,
    EnhancedNotificationManager,
    EnhancedFixSuggestionEngine,
    EnhancedErrorDetailPresenter,
    EnhancedErrorHandler,
    ErrorCategory,
    ErrorSeverity,
    RecoveryStrategy,
    RecoveryStatus,
    NotificationChannel,
    ReportFormat,
    error_handler_decorator,
    with_retry,
    with_fallback,
    with_circuit_breaker,
)


class TestEnhancedErrorContextRecorder(unittest.TestCase):
    """测试增强的错误上下文记录器"""
    
    def setUp(self):
        self.recorder = EnhancedErrorContextRecorder()
    
    def test_record_basic_error(self):
        """测试基本错误记录"""
        try:
            raise ValueError("测试错误")
        except Exception as e:
            context = self.recorder.record_error(e)
        
        self.assertIsNotNone(context)
        self.assertTrue(context.error_id.startswith("ERR-"))
        self.assertEqual(context.error_type, "ValueError")
        self.assertEqual(context.error_message, "测试错误")
        self.assertEqual(context.category, ErrorCategory.RUNTIME)
    
    def test_record_error_with_context(self):
        """测试带自定义上下文的错误记录"""
        custom_context = {"user_id": "123", "action": "test"}
        tags = ["unit_test", "demo"]
        
        try:
            raise FileNotFoundError("文件不存在")
        except Exception as e:
            context = self.recorder.record_error(e, custom_context, tags)
        
        self.assertEqual(context.custom_context, custom_context)
        self.assertEqual(context.tags, tags)
        self.assertEqual(context.category, ErrorCategory.FILE_SYSTEM)
    
    def test_capture_thread_states(self):
        """测试线程状态捕获"""
        def worker():
            time.sleep(0.1)
        
        thread = threading.Thread(target=worker, name="test_thread")
        thread.start()
        
        try:
            raise RuntimeError("测试线程状态")
        except Exception as e:
            context = self.recorder.record_error(e)
        
        thread.join()
        
        self.assertTrue(len(context.thread_states) > 0)
        thread_names = [t.thread_name for t in context.thread_states]
        self.assertIn("MainThread", thread_names)
    
    def test_error_pattern_detection(self):
        """测试错误模式检测"""
        for i in range(3):
            try:
                raise ValueError("重复错误测试")
            except Exception as e:
                context = self.recorder.record_error(e)
        
        self.assertEqual(len(self.recorder.error_patterns), 1)
        pattern = list(self.recorder.error_patterns.values())[0]
        self.assertEqual(pattern.occurrence_count, 3)


class TestEnhancedErrorClassifier(unittest.TestCase):
    """测试增强的错误分类器"""
    
    def test_classify_syntax_error(self):
        """测试语法错误分类"""
        try:
            exec("if True")
        except SyntaxError as e:
            category = EnhancedErrorClassifier.classify(e)
        self.assertEqual(category, ErrorCategory.SYNTAX)
    
    def test_classify_network_error(self):
        """测试网络错误分类"""
        e = ConnectionError("连接被拒绝")
        category = EnhancedErrorClassifier.classify(e)
        self.assertEqual(category, ErrorCategory.NETWORK)
    
    def test_classify_file_error(self):
        """测试文件错误分类"""
        e = FileNotFoundError("文件不存在")
        category = EnhancedErrorClassifier.classify(e)
        self.assertEqual(category, ErrorCategory.FILE_SYSTEM)
    
    def test_assess_severity_critical(self):
        """测试严重程度评估 - 关键"""
        e = MemoryError("内存不足")
        severity = EnhancedErrorClassifier.assess_severity(e, ErrorCategory.MEMORY)
        self.assertEqual(severity, ErrorSeverity.FATAL)


class TestEnhancedErrorReportGenerator(unittest.TestCase):
    """测试增强的错误报告生成器"""
    
    def setUp(self):
        self.generator = EnhancedErrorReportGenerator()
        self.recorder = EnhancedErrorContextRecorder()
    
    def _create_test_context(self):
        try:
            raise ValueError("测试报告生成")
        except Exception as e:
            return self.recorder.record_error(e)
    
    def test_generate_json_report(self):
        """测试JSON报告生成"""
        context = self._create_test_context()
        report = self.generator.generate_json_report(context)
        
        data = json.loads(report)
        self.assertEqual(data["error"]["error_id"], context.error_id)
        self.assertEqual(data["error"]["error_type"], "ValueError")
        self.assertIn("stack_frames", data)
        self.assertIn("environment", data)
    
    def test_generate_markdown_report(self):
        """测试Markdown报告生成"""
        context = self._create_test_context()
        report = self.generator.generate_markdown_report(context)
        
        self.assertIn("# 错误报告", report)
        self.assertIn(context.error_id, report)
        self.assertIn("ValueError", report)
        self.assertIn("## 堆栈跟踪", report)
    
    def test_generate_html_report(self):
        """测试HTML报告生成"""
        context = self._create_test_context()
        report = self.generator.generate_html_report(context)
        
        self.assertIn("<!DOCTYPE html>", report)
        self.assertIn(context.error_id, report)
        self.assertIn("<title>", report)


class TestEnhancedRecoveryEngine(unittest.TestCase):
    """测试增强的恢复引擎"""
    
    def setUp(self):
        self.engine = EnhancedRecoveryEngine(max_retries=3, retry_delay=0.1)
    
    def test_retry_with_backoff_success(self):
        """测试重试成功"""
        attempts = [0]
        
        def flaky_func():
            attempts[0] += 1
            if attempts[0] < 2:
                raise ConnectionError("临时错误")
            return "成功"
        
        result, recovery = self.engine.retry_with_backoff(
            flaky_func,
            max_retries=3,
            initial_delay=0.05
        )
        
        self.assertEqual(result, "成功")
        self.assertTrue(recovery.successful)
        self.assertEqual(recovery.total_attempts, 2)
    
    def test_retry_with_backoff_failure(self):
        """测试重试失败"""
        def always_fail():
            raise RuntimeError("总是失败")
        
        with self.assertRaises(RuntimeError):
            self.engine.retry_with_backoff(
                always_fail,
                max_retries=2,
                initial_delay=0.05
            )
    
    def test_execute_with_fallback_primary_success(self):
        """测试主函数成功"""
        def primary():
            return "主函数结果"
        
        def fallback():
            return "降级结果"
        
        result, recovery = self.engine.execute_with_fallback(primary, fallback)
        
        self.assertEqual(result, "主函数结果")
        self.assertTrue(recovery.successful)
        self.assertEqual(recovery.total_attempts, 1)
    
    def test_execute_with_fallback_fallback_success(self):
        """测试降级函数成功"""
        def primary():
            raise RuntimeError("主函数失败")
        
        def fallback():
            return "降级结果"
        
        result, recovery = self.engine.execute_with_fallback(primary, fallback)
        
        self.assertEqual(result, "降级结果")
        self.assertTrue(recovery.successful)
        self.assertEqual(recovery.total_attempts, 2)
    
    def test_execute_with_rollback(self):
        """测试回滚执行"""
        executed = []
        
        def main_func():
            executed.append("main")
            raise RuntimeError("主函数失败")
        
        def rollback_func():
            executed.append("rollback")
        
        with self.assertRaises(RuntimeError):
            self.engine.execute_with_rollback(main_func, rollback_func)
        
        self.assertIn("main", executed)
        self.assertIn("rollback", executed)
    
    def test_circuit_breaker(self):
        """测试熔断器"""
        failures = [0]
        
        def failing_func():
            failures[0] += 1
            raise ConnectionError("服务不可用")
        
        for _ in range(5):
            try:
                self.engine.circuit_breaker_execute(
                    failing_func,
                    "test_circuit",
                    failure_threshold=5,
                    recovery_timeout=0.5
                )
            except Exception:
                pass
        
        circuit = self.engine.circuit_breaker_state.get("test_circuit")
        self.assertEqual(circuit["state"], "open")
    
    def test_get_recovery_statistics(self):
        """测试恢复统计"""
        attempts = [0]
        
        def flaky_func():
            attempts[0] += 1
            if attempts[0] < 2:
                raise ConnectionError("临时错误")
            return "成功"
        
        self.engine.retry_with_backoff(flaky_func, max_retries=3, initial_delay=0.05)
        
        stats = self.engine.get_recovery_statistics()
        
        self.assertEqual(stats["total_recoveries"], 1)
        self.assertEqual(stats["successful_recoveries"], 1)
        self.assertEqual(stats["success_rate"], 100.0)


class TestEnhancedNotificationManager(unittest.TestCase):
    """测试增强的通知管理器"""
    
    def setUp(self):
        self.manager = EnhancedNotificationManager()
        self.recorder = EnhancedErrorContextRecorder()
    
    def _create_test_context(self):
        try:
            raise ValueError("测试通知")
        except Exception as e:
            return self.recorder.record_error(e)
    
    def test_notify_console(self):
        """测试控制台通知"""
        context = self._create_test_context()
        record = self.manager.notify_console(context)
        
        self.assertTrue(record.success)
        self.assertEqual(record.channel, NotificationChannel.CONSOLE)
    
    def test_notify_log(self):
        """测试日志通知"""
        context = self._create_test_context()
        record = self.manager.notify_log(context)
        
        self.assertTrue(record.success)
        self.assertEqual(record.channel, NotificationChannel.LOG)
    
    def test_notify_file(self):
        """测试文件通知"""
        context = self._create_test_context()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = EnhancedNotificationManager(tmpdir)
            record = manager.notify_file(context)
            
            self.assertTrue(record.success)
            self.assertEqual(record.channel, NotificationChannel.FILE)
    
    def test_notify_all(self):
        """测试多渠道通知"""
        context = self._create_test_context()
        
        records = self.manager.notify_all(
            context,
            channels=[NotificationChannel.CONSOLE, NotificationChannel.LOG]
        )
        
        self.assertEqual(len(records), 2)
        channels = [r.channel for r in records]
        self.assertIn(NotificationChannel.CONSOLE, channels)
        self.assertIn(NotificationChannel.LOG, channels)


class TestEnhancedFixSuggestionEngine(unittest.TestCase):
    """测试增强的修复建议引擎"""
    
    def setUp(self):
        self.engine = EnhancedFixSuggestionEngine()
        self.recorder = EnhancedErrorContextRecorder()
    
    def test_generate_suggestions_key_error(self):
        """测试KeyError建议"""
        try:
            raise KeyError("missing_key")
        except Exception as e:
            context = self.recorder.record_error(e)
        
        suggestions = self.engine.generate_suggestions(context)
        
        self.assertTrue(len(suggestions) > 0)
        self.assertTrue(any("字典键" in s.title for s in suggestions))
    
    def test_generate_suggestions_file_error(self):
        """测试文件错误建议"""
        try:
            raise FileNotFoundError("文件不存在")
        except Exception as e:
            context = self.recorder.record_error(e)
        
        suggestions = self.engine.generate_suggestions(context)
        
        self.assertTrue(len(suggestions) > 0)
        self.assertTrue(any("文件" in s.title for s in suggestions))
    
    def test_suggestion_auto_fixable(self):
        """测试自动修复标记"""
        try:
            raise IndexError("索引越界")
        except Exception as e:
            context = self.recorder.record_error(e)
        
        suggestions = self.engine.generate_suggestions(context)
        
        auto_fixable = [s for s in suggestions if s.auto_fixable]
        self.assertTrue(len(auto_fixable) > 0)


class TestEnhancedErrorHandler(unittest.TestCase):
    """测试增强的错误处理器"""
    
    def setUp(self):
        self.handler = EnhancedErrorHandler()
    
    def test_handle_error(self):
        """测试错误处理"""
        try:
            raise ValueError("测试处理")
        except Exception as e:
            report = self.handler.handle_error(e)
        
        self.assertIsNotNone(report)
        self.assertTrue(report.error_context.error_id.startswith("ERR-"))
        self.assertTrue(len(report.fix_suggestions) > 0)
    
    def test_handle_error_with_tags(self):
        """测试带标签的错误处理"""
        try:
            raise FileNotFoundError("文件不存在")
        except Exception as e:
            report = self.handler.handle_error(
                e,
                tags=["test", "file_error"]
            )
        
        self.assertEqual(report.error_context.tags, ["test", "file_error"])
    
    def test_get_statistics(self):
        """测试统计信息"""
        for i in range(3):
            try:
                raise ValueError(f"错误{i}")
            except Exception as e:
                self.handler.handle_error(e)
        
        stats = self.handler.get_statistics()
        
        self.assertEqual(stats["total_errors"], 3)
        self.assertIn("category_distribution", stats)


class TestDecorators(unittest.TestCase):
    """测试装饰器"""
    
    def test_error_handler_decorator(self):
        """测试错误处理装饰器"""
        @error_handler_decorator(reraise=False)
        def failing_function():
            raise ValueError("装饰器测试错误")
        
        result = failing_function()
        self.assertIsNone(result)
    
    def test_with_retry_decorator(self):
        """测试重试装饰器"""
        attempts = [0]
        
        @with_retry(max_retries=3, delay=0.05)
        def flaky_function():
            attempts[0] += 1
            if attempts[0] < 2:
                raise ConnectionError("临时错误")
            return "成功"
        
        result = flaky_function()
        self.assertEqual(result, "成功")
    
    def test_with_fallback_decorator(self):
        """测试降级装饰器"""
        @with_fallback(lambda: "降级结果")
        def primary_function():
            raise RuntimeError("主函数失败")
        
        result = primary_function()
        self.assertEqual(result, "降级结果")


def run_tests():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestEnhancedErrorContextRecorder))
    suite.addTests(loader.loadTestsFromTestCase(TestEnhancedErrorClassifier))
    suite.addTests(loader.loadTestsFromTestCase(TestEnhancedErrorReportGenerator))
    suite.addTests(loader.loadTestsFromTestCase(TestEnhancedRecoveryEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestEnhancedNotificationManager))
    suite.addTests(loader.loadTestsFromTestCase(TestEnhancedFixSuggestionEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestEnhancedErrorHandler))
    suite.addTests(loader.loadTestsFromTestCase(TestDecorators))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    exit(0 if success else 1)
