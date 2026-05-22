#!/usr/bin/env python3
"""
错误处理系统测试文件
测试错误智能捕获、智能恢复和错误通知功能
"""

import os
import sys
import json
import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from error_handler import (
    ErrorContextRecorder,
    ErrorClassifier,
    ErrorReportGenerator,
    RecoveryEngine,
    RecoveryReportGenerator,
    NotificationManager,
    FixSuggestionEngine,
    ErrorHandler,
    ErrorCategory,
    ErrorSeverity,
    RecoveryStrategy,
    RecoveryStatus,
    NotificationChannel,
    error_handler_decorator,
    with_retry,
    with_fallback,
)


class TestErrorContextRecorder:
    """测试错误上下文记录器"""
    
    def test_record_simple_error(self):
        """测试记录简单错误"""
        recorder = ErrorContextRecorder()
        
        try:
            raise ValueError("测试错误消息")
        except Exception as e:
            context = recorder.record_error(e)
        
        assert context.error_id.startswith("ERR-")
        assert context.error_type == "ValueError"
        assert context.error_message == "测试错误消息"
        assert context.category == ErrorCategory.RUNTIME
        assert len(context.stack_frames) > 0
        assert context.environment is not None
    
    def test_record_error_with_custom_context(self):
        """测试记录带自定义上下文的错误"""
        recorder = ErrorContextRecorder()
        
        try:
            raise FileNotFoundError("文件不存在")
        except Exception as e:
            context = recorder.record_error(
                e,
                custom_context={"user_id": 123, "operation": "file_read"},
                tags=["important", "user_facing"]
            )
        
        assert context.custom_context["user_id"] == 123
        assert context.custom_context["operation"] == "file_read"
        assert "important" in context.tags
        assert "user_facing" in context.tags
    
    def test_sensitive_data_redaction(self):
        """测试敏感数据脱敏"""
        recorder = ErrorContextRecorder()
        
        try:
            password = "secret123"
            api_key = "key123"
            raise ValueError("测试敏感数据")
        except Exception as e:
            context = recorder.record_error(e)
        
        for frame in context.stack_frames:
            for var in frame.local_variables:
                if var.is_sensitive:
                    assert var.value == "***REDACTED***"
    
    def test_environment_capture(self):
        """测试环境信息捕获"""
        recorder = ErrorContextRecorder()
        
        try:
            raise RuntimeError("测试环境")
        except Exception as e:
            context = recorder.record_error(e)
        
        assert context.environment.python_version is not None
        assert context.environment.platform_system is not None
        assert context.environment.working_directory is not None
        assert isinstance(context.environment.installed_packages, list)


class TestErrorClassifier:
    """测试错误分类器"""
    
    def test_classify_syntax_error(self):
        """测试语法错误分类"""
        try:
            eval("invalid syntax here")
        except SyntaxError as e:
            category = ErrorClassifier.classify(e)
            assert category == ErrorCategory.SYNTAX
    
    def test_classify_file_error(self):
        """测试文件错误分类"""
        try:
            open("/nonexistent/path/file.txt")
        except FileNotFoundError as e:
            category = ErrorClassifier.classify(e)
            assert category == ErrorCategory.FILE_SYSTEM
    
    def test_classify_network_error(self):
        """测试网络错误分类"""
        try:
            raise ConnectionError("Connection refused")
        except ConnectionError as e:
            category = ErrorClassifier.classify(e)
            assert category == ErrorCategory.NETWORK
    
    def test_classify_memory_error(self):
        """测试内存错误分类"""
        try:
            raise MemoryError("Out of memory")
        except MemoryError as e:
            category = ErrorClassifier.classify(e)
            assert category == ErrorCategory.MEMORY
    
    def test_assess_severity_critical(self):
        """测试严重程度评估 - 严重"""
        try:
            raise MemoryError("Out of memory")
        except MemoryError as e:
            severity = ErrorClassifier.assess_severity(e, ErrorCategory.MEMORY)
            assert severity == ErrorSeverity.CRITICAL
    
    def test_assess_severity_high(self):
        """测试严重程度评估 - 高"""
        try:
            raise FileNotFoundError("File not found")
        except FileNotFoundError as e:
            severity = ErrorClassifier.assess_severity(e, ErrorCategory.FILE_SYSTEM)
            assert severity == ErrorSeverity.HIGH
    
    def test_assess_severity_medium(self):
        """测试严重程度评估 - 中"""
        try:
            raise KeyError("Key not found")
        except KeyError as e:
            severity = ErrorClassifier.assess_severity(e, ErrorCategory.RUNTIME)
            assert severity == ErrorSeverity.MEDIUM


class TestErrorReportGenerator:
    """测试错误报告生成器"""
    
    def test_generate_json_report(self):
        """测试生成JSON报告"""
        recorder = ErrorContextRecorder()
        generator = ErrorReportGenerator()
        
        try:
            raise ValueError("JSON报告测试")
        except Exception as e:
            context = recorder.record_error(e)
        
        json_report = generator.generate_json_report(context)
        
        assert json_report is not None
        report_data = json.loads(json_report)
        assert report_data["error"]["error_type"] == "ValueError"
        assert report_data["error"]["message"] == "JSON报告测试"
    
    def test_generate_markdown_report(self):
        """测试生成Markdown报告"""
        recorder = ErrorContextRecorder()
        generator = ErrorReportGenerator()
        
        try:
            raise RuntimeError("Markdown报告测试")
        except Exception as e:
            context = recorder.record_error(e)
        
        md_report = generator.generate_markdown_report(context)
        
        assert md_report is not None
        assert "# 错误报告" in md_report
        assert "RuntimeError" in md_report
        assert "Markdown报告测试" in md_report
    
    def test_save_report(self):
        """测试保存报告"""
        with tempfile.TemporaryDirectory() as tmpdir:
            recorder = ErrorContextRecorder()
            generator = ErrorReportGenerator(tmpdir)
            
            try:
                raise ValueError("保存测试")
            except Exception as e:
                context = recorder.record_error(e)
            
            path = generator.save_report(context, format="markdown")
            
            assert os.path.exists(path)
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            assert "保存测试" in content


class TestRecoveryEngine:
    """测试恢复引擎"""
    
    def test_retry_success(self):
        """测试重试成功"""
        engine = RecoveryEngine(max_retries=3, retry_delay=0.1)
        call_count = [0]
        
        def flaky_function():
            call_count[0] += 1
            if call_count[0] < 2:
                raise ValueError("Temporary error")
            return "success"
        
        result, recovery = engine.retry_with_backoff(
            flaky_function,
            max_retries=3,
            initial_delay=0.1
        )
        
        assert result == "success"
        assert recovery.successful is True
        assert recovery.total_attempts == 2
    
    def test_retry_failure(self):
        """测试重试失败"""
        engine = RecoveryEngine(max_retries=2, retry_delay=0.1)
        
        def always_fail():
            raise ValueError("Always fails")
        
        with pytest.raises(ValueError):
            engine.retry_with_backoff(always_fail, max_retries=2, initial_delay=0.1)
    
    def test_fallback_success(self):
        """测试降级成功"""
        engine = RecoveryEngine()
        
        def primary():
            raise RuntimeError("Primary failed")
        
        def fallback():
            return "fallback result"
        
        result, recovery = engine.execute_with_fallback(primary, fallback)
        
        assert result == "fallback result"
        assert recovery.successful is True
        assert recovery.total_attempts == 2
    
    def test_rollback(self):
        """测试回滚机制"""
        engine = RecoveryEngine()
        rollback_called = [False]
        
        def operation():
            raise RuntimeError("Operation failed")
        
        def rollback():
            rollback_called[0] = True
        
        with pytest.raises(RuntimeError):
            engine.execute_with_rollback(operation, rollback)
        
        assert rollback_called[0] is True
    
    def test_recovery_statistics(self):
        """测试恢复统计"""
        engine = RecoveryEngine(max_retries=2, retry_delay=0.1)
        
        call_count = [0]
        def sometimes_fails():
            call_count[0] += 1
            if call_count[0] % 2 == 0:
                raise ValueError("Error")
            return "ok"
        
        try:
            engine.retry_with_backoff(sometimes_fails, max_retries=2, initial_delay=0.1)
        except:
            pass
        
        stats = engine.get_recovery_statistics()
        assert "total_recoveries" in stats
        assert "success_rate" in stats


class TestRecoveryReportGenerator:
    """测试恢复报告生成器"""
    
    def test_generate_json_report(self):
        """测试生成JSON恢复报告"""
        engine = RecoveryEngine(max_retries=2, retry_delay=0.1)
        generator = RecoveryReportGenerator()
        
        def success_func():
            return "ok"
        
        _, recovery = engine.retry_with_backoff(success_func, max_retries=2, initial_delay=0.1)
        
        json_report = generator.generate_json_report(recovery)
        
        assert json_report is not None
        report_data = json.loads(json_report)
        assert report_data["recovery"]["successful"] is True
    
    def test_generate_markdown_report(self):
        """测试生成Markdown恢复报告"""
        engine = RecoveryEngine(max_retries=2, retry_delay=0.1)
        generator = RecoveryReportGenerator()
        
        def success_func():
            return "ok"
        
        _, recovery = engine.retry_with_backoff(success_func, max_retries=2, initial_delay=0.1)
        
        md_report = generator.generate_markdown_report(recovery)
        
        assert md_report is not None
        assert "# 恢复报告" in md_report


class TestNotificationManager:
    """测试通知管理器"""
    
    def test_notify_console(self):
        """测试控制台通知"""
        with tempfile.TemporaryDirectory() as tmpdir:
            recorder = ErrorContextRecorder()
            manager = NotificationManager(tmpdir)
            
            try:
                raise ValueError("控制台通知测试")
            except Exception as e:
                context = recorder.record_error(e)
            
            record = manager.notify_console(context)
            
            assert record.success is True
            assert record.channel == NotificationChannel.CONSOLE
    
    def test_notify_log(self):
        """测试日志通知"""
        with tempfile.TemporaryDirectory() as tmpdir:
            recorder = ErrorContextRecorder()
            manager = NotificationManager(tmpdir)
            
            try:
                raise RuntimeError("日志通知测试")
            except Exception as e:
                context = recorder.record_error(e)
            
            record = manager.notify_log(context)
            
            assert record.success is True
            assert record.channel == NotificationChannel.LOG
    
    def test_notify_file(self):
        """测试文件通知"""
        with tempfile.TemporaryDirectory() as tmpdir:
            recorder = ErrorContextRecorder()
            manager = NotificationManager(tmpdir)
            
            try:
                raise ValueError("文件通知测试")
            except Exception as e:
                context = recorder.record_error(e)
            
            record = manager.notify_file(context)
            
            assert record.success is True
            assert record.channel == NotificationChannel.FILE
    
    def test_notify_all(self):
        """测试多渠道通知"""
        with tempfile.TemporaryDirectory() as tmpdir:
            recorder = ErrorContextRecorder()
            manager = NotificationManager(tmpdir)
            
            try:
                raise ValueError("多渠道通知测试")
            except Exception as e:
                context = recorder.record_error(e)
            
            records = manager.notify_all(
                context,
                channels=[NotificationChannel.CONSOLE, NotificationChannel.LOG]
            )
            
            assert len(records) == 2


class TestFixSuggestionEngine:
    """测试修复建议引擎"""
    
    def test_generate_suggestions_key_error(self):
        """测试KeyError修复建议"""
        recorder = ErrorContextRecorder()
        engine = FixSuggestionEngine()
        
        try:
            d = {}
            _ = d["missing_key"]
        except KeyError as e:
            context = recorder.record_error(e)
        
        suggestions = engine.generate_suggestions(context)
        
        assert len(suggestions) > 0
        assert any("字典" in s.title or "键" in s.title for s in suggestions)
    
    def test_generate_suggestions_file_error(self):
        """测试文件错误修复建议"""
        recorder = ErrorContextRecorder()
        engine = FixSuggestionEngine()
        
        try:
            open("/nonexistent/file.txt")
        except FileNotFoundError as e:
            context = recorder.record_error(e)
        
        suggestions = engine.generate_suggestions(context)
        
        assert len(suggestions) > 0
        assert any("文件" in s.title or "路径" in s.title for s in suggestions)
    
    def test_suggestion_confidence(self):
        """测试建议置信度"""
        recorder = ErrorContextRecorder()
        engine = FixSuggestionEngine()
        
        try:
            raise ValueError("测试置信度")
        except Exception as e:
            context = recorder.record_error(e)
        
        suggestions = engine.generate_suggestions(context)
        
        for suggestion in suggestions:
            assert 0 <= suggestion.confidence <= 1


class TestErrorHandler:
    """测试统一错误处理器"""
    
    def test_handle_error(self):
        """测试错误处理"""
        tmpdir = tempfile.mkdtemp()
        try:
            handler = ErrorHandler(output_dir=tmpdir)
            
            try:
                raise ValueError("统一处理测试")
            except Exception as e:
                report = handler.handle_error(e)
            
            assert report.error_context is not None
            assert len(report.fix_suggestions) > 0
            assert len(report.notifications) > 0
        finally:
            for h in handler.logger.handlers[:]:
                h.close()
                handler.logger.removeHandler(h)
            shutil.rmtree(tmpdir, ignore_errors=True)
    
    def test_handle_with_recovery(self):
        """测试带恢复的错误处理"""
        tmpdir = tempfile.mkdtemp()
        try:
            handler = ErrorHandler(output_dir=tmpdir)
            
            recovery_called = [False]
            def recovery_func():
                recovery_called[0] = True
                return "recovered"
            
            try:
                raise ValueError("恢复测试")
            except Exception as e:
                report, recovery = handler.handle_with_recovery(
                    e,
                    recovery_func=recovery_func,
                    recovery_strategy=RecoveryStrategy.RETRY
                )
            
            assert report is not None
        finally:
            for h in handler.logger.handlers[:]:
                h.close()
                handler.logger.removeHandler(h)
            shutil.rmtree(tmpdir, ignore_errors=True)
    
    def test_get_statistics(self):
        """测试获取统计信息"""
        tmpdir = tempfile.mkdtemp()
        try:
            handler = ErrorHandler(output_dir=tmpdir)
            
            for msg in ["错误1", "错误2", "错误3"]:
                try:
                    raise ValueError(msg)
                except Exception as e:
                    handler.handle_error(e, save_report=False)
            
            stats = handler.get_statistics()
            
            assert stats["total_errors"] == 3
            assert "category_distribution" in stats
            assert "severity_distribution" in stats
        finally:
            for h in handler.logger.handlers[:]:
                h.close()
                handler.logger.removeHandler(h)
            shutil.rmtree(tmpdir, ignore_errors=True)
    
    def test_generate_summary_report(self):
        """测试生成摘要报告"""
        tmpdir = tempfile.mkdtemp()
        try:
            handler = ErrorHandler(output_dir=tmpdir)
            
            try:
                raise ValueError("摘要测试")
            except Exception as e:
                handler.handle_error(e)
            
            report = handler.generate_summary_report()
            
            assert "错误处理系统报告" in report
            assert "统计概览" in report
        finally:
            for h in handler.logger.handlers[:]:
                h.close()
                handler.logger.removeHandler(h)
            shutil.rmtree(tmpdir, ignore_errors=True)


class TestDecorators:
    """测试装饰器"""
    
    def test_error_handler_decorator(self):
        """测试错误处理装饰器"""
        tmpdir = tempfile.mkdtemp()
        try:
            handler = ErrorHandler(output_dir=tmpdir)
            
            @error_handler_decorator(handler=handler, reraise=False)
            def failing_function():
                raise ValueError("装饰器测试")
            
            result = failing_function()
            assert result is None
            
            stats = handler.get_statistics()
            assert stats["total_errors"] == 1
        finally:
            for h in handler.logger.handlers[:]:
                h.close()
                handler.logger.removeHandler(h)
            shutil.rmtree(tmpdir, ignore_errors=True)
    
    def test_with_retry_decorator(self):
        """测试重试装饰器"""
        call_count = [0]
        
        @with_retry(max_retries=3, delay=0.1)
        def flaky_function():
            call_count[0] += 1
            if call_count[0] < 2:
                raise ValueError("Temporary")
            return "success"
        
        result = flaky_function()
        assert result == "success"
        assert call_count[0] == 2
    
    def test_with_fallback_decorator(self):
        """测试降级装饰器"""
        def fallback():
            return "fallback"
        
        @with_fallback(fallback)
        def primary():
            raise RuntimeError("Primary failed")
        
        result = primary()
        assert result == "fallback"


def run_tests():
    """运行所有测试"""
    pytest.main([__file__, "-v", "--tb=short"])


if __name__ == "__main__":
    run_tests()
