#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自迭代冲突安全处理功能单元测试

测试增强功能:
1. temp_file_manager.py - 运行状态智能检测、超时等待和重试机制、原子性文件替换验证、临时文件清理策略
2. self_iteration_rollback.py - 版本快照自动创建、智能回滚触发机制、失败通知和日志记录、回滚验证功能
"""

import os
import sys
import time
import tempfile
import threading
import unittest
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(get_path_config().SCRIPTS_DIR / "utils"))

from temp_file_manager import (
    TempFileManager,
    EnhancedTempFileManager,
    IntelligentProcessStateDetector,
    EnhancedTimeoutManager,
    EnhancedAtomicVerifier,
    IntelligentCleanupStrategy,
    ProcessDetector,
    TempFileState,
    WaitStrategy,
    VerificationLevel,
    CleanupPriority,
    CleanupPolicy
)

from self_iteration_rollback import (
    SelfIterationRollback,
    EnhancedSelfIterationRollback,
    IntelligentSnapshotCreator,
    IntelligentRollbackTrigger,
    EnhancedNotificationManager,
    EnhancedRollbackVerifier,
    SnapshotStatus,
    RollbackTrigger,
    VerificationLevel as RollbackVerificationLevel,
    AutoSnapshotConfig,
    NotificationConfig,
    HealthStatus
)


class TestIntelligentProcessStateDetector(unittest.TestCase):
    """测试智能进程状态检测器"""
    
    def setUp(self):
        self.detector = IntelligentProcessStateDetector(ProcessDetector())
    
    def test_detect_not_running_script(self):
        """测试检测未运行的脚本"""
        result = self.detector.detect_intelligent_state("non_existent_script.py")
        
        self.assertEqual(result['status'], 'not_running')
        self.assertEqual(result['confidence'], 1.0)
        self.assertIn('脚本未运行', result['recommendations'])
    
    def test_state_history_recording(self):
        """测试状态历史记录"""
        result = self.detector.detect_intelligent_state("test_script.py")
        
        if 'pid' in result:
            history = self.detector.get_state_history(result['pid'])
            self.assertIsInstance(history, list)


class TestEnhancedTimeoutManager(unittest.TestCase):
    """测试增强超时管理器"""
    
    def setUp(self):
        self.manager = EnhancedTimeoutManager()
    
    def test_smart_wait_success(self):
        """测试智能等待成功"""
        counter = [0]
        
        def check_func():
            counter[0] += 1
            return counter[0] >= 3
        
        result = self.manager.smart_wait(check_func, timeout=10.0, strategy='exponential')
        
        self.assertTrue(result['success'])
        self.assertGreater(result['iterations'], 0)
    
    def test_smart_wait_timeout(self):
        """测试智能等待超时"""
        result = self.manager.smart_wait(
            lambda: False,
            timeout=1.0,
            strategy='linear',
            initial_interval=0.1
        )
        
        self.assertFalse(result['success'])
        self.assertTrue(result['timeout'])
    
    def test_different_strategies(self):
        """测试不同等待策略"""
        strategies = ['linear', 'exponential', 'fibonacci', 'adaptive']
        
        for strategy in strategies:
            result = self.manager.smart_wait(
                lambda: True,
                timeout=5.0,
                strategy=strategy
            )
            self.assertTrue(result['success'])
    
    def test_statistics(self):
        """测试统计信息"""
        self.manager.smart_wait(lambda: True, timeout=5.0)
        
        stats = self.manager.get_statistics()
        self.assertIn('total_waits', stats)


class TestEnhancedAtomicVerifier(unittest.TestCase):
    """测试增强原子性验证器"""
    
    def setUp(self):
        self.verifier = EnhancedAtomicVerifier()
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = Path(self.temp_dir) / "test_file.txt"
        self.test_file.write_text("test content")
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_multi_stage_verify_success(self):
        """测试多阶段验证成功"""
        result = self.verifier.multi_stage_verify(
            str(self.test_file),
            str(self.test_file),
            stages=['existence', 'readability']
        )
        
        self.assertTrue(result['success'])
        self.assertGreater(result['stages_passed'], 0)
    
    def test_multi_stage_verify_failure(self):
        """测试多阶段验证失败"""
        non_existent = Path(self.temp_dir) / "non_existent.txt"
        
        result = self.verifier.multi_stage_verify(
            str(non_existent),
            str(non_existent),
            stages=['existence']
        )
        
        self.assertFalse(result['success'])
    
    def test_verification_statistics(self):
        """测试验证统计"""
        self.verifier.multi_stage_verify(
            str(self.test_file),
            str(self.test_file),
            stages=['existence']
        )
        
        stats = self.verifier.get_verification_statistics()
        self.assertIn('total_verifications', stats)


class TestIntelligentCleanupStrategy(unittest.TestCase):
    """测试智能临时文件清理策略"""
    
    def setUp(self):
        self.manager = TempFileManager()
        self.strategy = IntelligentCleanupStrategy(self.manager)
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_analyze_files(self):
        """测试文件分析"""
        test_file = Path(self.temp_dir) / "test_temp_123.txt"
        test_file.write_text("test content")
        
        analysis = self.strategy._analyze_files([test_file])
        
        self.assertEqual(analysis['total_files'], 1)
        self.assertIn('by_age', analysis)
        self.assertIn('by_size', analysis)
    
    def test_cleanup_statistics(self):
        """测试清理统计"""
        stats = self.strategy.get_cleanup_statistics()
        self.assertIn('total_cleanups', stats)


class TestEnhancedTempFileManager(unittest.TestCase):
    """测试增强临时文件管理器"""
    
    def setUp(self):
        self.manager = EnhancedTempFileManager()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_detect_intelligent_state(self):
        """测试智能状态检测"""
        result = self.manager.detect_intelligent_state("non_existent.py")
        
        self.assertIn('status', result)
        self.assertIn('confidence', result)
    
    def test_smart_wait_with_timeout(self):
        """测试智能等待"""
        result = self.manager.smart_wait_with_timeout(
            lambda: True,
            timeout=5.0,
            strategy='adaptive'
        )
        
        self.assertTrue(result['success'])
    
    def test_multi_stage_verify(self):
        """测试多阶段验证"""
        test_file = Path(self.temp_dir) / "test.txt"
        test_file.write_text("test")
        
        result = self.manager.multi_stage_verify(
            str(test_file),
            str(test_file),
            stages=['existence', 'readability']
        )
        
        self.assertIn('success', result)
    
    def test_intelligent_cleanup(self):
        """测试智能清理"""
        result = self.manager.intelligent_cleanup(
            self.temp_dir,
            strategy='conservative',
            dry_run=True
        )
        
        self.assertIn('cleaned', result)
    
    def test_enhanced_statistics(self):
        """测试增强统计"""
        stats = self.manager.get_enhanced_statistics()
        
        self.assertIn('registered_temp_files', stats)
        self.assertIn('enhanced', stats)


class TestIntelligentSnapshotCreator(unittest.TestCase):
    """测试智能快照创建器"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.temp_dir) / "project"
        self.project_dir.mkdir()
        (self.project_dir / "__init__.py").write_text("")
        (self.project_dir / "main.py").write_text("print('hello')")
        
        from self_iteration_rollback import SnapshotManager
        self.snapshot_dir = Path(self.temp_dir) / "snapshots"
        self.snapshot_manager = SnapshotManager(str(self.snapshot_dir))
        self.creator = IntelligentSnapshotCreator(
            self.snapshot_manager,
            str(self.project_dir)
        )
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_create_pre_operation_snapshot(self):
        """测试创建操作前快照"""
        snapshot = self.creator.create_pre_operation_snapshot(
            "test_operation",
            metadata={'key': 'value'}
        )
        
        self.assertIsNotNone(snapshot)
        self.assertIn("pre_operation", snapshot.version)
    
    def test_change_history(self):
        """测试变化历史"""
        history = self.creator.get_change_history()
        self.assertIsInstance(history, list)


class TestIntelligentRollbackTrigger(unittest.TestCase):
    """测试智能回滚触发器"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.temp_dir) / "project"
        self.project_dir.mkdir()
        
        from self_iteration_rollback import (
            SnapshotManager,
            HealthMonitor
        )
        
        self.snapshot_dir = Path(self.temp_dir) / "snapshots"
        self.snapshot_manager = SnapshotManager(str(self.snapshot_dir))
        
        self.rollback = SelfIterationRollback(str(self.project_dir))
        self.health_monitor = HealthMonitor(str(self.project_dir))
        
        self.trigger = IntelligentRollbackTrigger(
            self.rollback,
            self.health_monitor
        )
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_evaluate_healthy_system(self):
        """测试评估健康系统"""
        from self_iteration_rollback import HealthMetrics
        
        metrics = HealthMetrics(
            status=HealthStatus.HEALTHY,
            score=95.0,
            test_pass_rate=1.0,
            build_success_rate=1.0,
            error_count=0,
            warning_count=0,
            last_check_time=datetime.now().isoformat()
        )
        
        result = self.trigger.evaluate(metrics)
        
        self.assertFalse(result['should_rollback'])
    
    def test_evaluate_critical_system(self):
        """测试评估关键系统"""
        from self_iteration_rollback import HealthMetrics
        
        metrics = HealthMetrics(
            status=HealthStatus.CRITICAL,
            score=20.0,
            test_pass_rate=0.3,
            build_success_rate=0.5,
            error_count=30,
            warning_count=10,
            last_check_time=datetime.now().isoformat()
        )
        
        result = self.trigger.evaluate(metrics)
        
        self.assertTrue(result['should_rollback'])
    
    def test_add_custom_rule(self):
        """测试添加自定义规则"""
        self.trigger.add_custom_rule(
            "custom_rule",
            lambda m: m.score < 50,
            "assess_and_rollback",
            priority=60
        )
        
        self.assertEqual(len(self.trigger._trigger_rules), 6)
    
    def test_trigger_history(self):
        """测试触发历史"""
        from self_iteration_rollback import HealthMetrics
        
        metrics = HealthMetrics(
            status=HealthStatus.HEALTHY,
            score=90.0,
            test_pass_rate=1.0,
            build_success_rate=1.0,
            error_count=0,
            warning_count=0,
            last_check_time=datetime.now().isoformat()
        )
        
        self.trigger.evaluate(metrics)
        
        history = self.trigger.get_trigger_history()
        self.assertIsInstance(history, list)


class TestEnhancedNotificationManager(unittest.TestCase):
    """测试增强通知管理器"""
    
    def setUp(self):
        self.config = NotificationConfig(
            enabled=True,
            notification_types=[]
        )
        self.manager = EnhancedNotificationManager(self.config)
    
    def test_send_enhanced_notification(self):
        """测试发送增强通知"""
        result = self.manager.send_enhanced_notification(
            "Test Title",
            "Test Message",
            severity="info"
        )
        
        self.assertTrue(result['sent'])
    
    def test_deduplication(self):
        """测试去重"""
        self.manager.send_enhanced_notification(
            "Test",
            "Message",
            dedup_key="test_key"
        )
        
        result = self.manager.send_enhanced_notification(
            "Test",
            "Message",
            dedup_key="test_key"
        )
        
        self.assertFalse(result['sent'])
        self.assertEqual(result['reason'], 'deduplicated')
    
    def test_notification_statistics(self):
        """测试通知统计"""
        self.manager.send_enhanced_notification("Test", "Message", severity="info")
        
        stats = self.manager.get_notification_statistics()
        self.assertIn('total_notifications', stats)


class TestEnhancedRollbackVerifier(unittest.TestCase):
    """测试增强回滚验证器"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.temp_dir) / "project"
        self.project_dir.mkdir()
        (self.project_dir / "__init__.py").write_text("")
        (self.project_dir / "main.py").write_text("print('hello')")
        
        self.verifier = EnhancedRollbackVerifier(str(self.project_dir))
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_verify_rollback_basic(self):
        """测试基础回滚验证"""
        result = self.verifier.verify_rollback(
            level=RollbackVerificationLevel.BASIC
        )
        
        self.assertIn('passed', result)
        self.assertIn('checks', result)
    
    def test_verify_rollback_standard(self):
        """测试标准回滚验证"""
        result = self.verifier.verify_rollback(
            level=RollbackVerificationLevel.STANDARD
        )
        
        self.assertIn('python_syntax', result['checks'])
    
    def test_add_custom_check(self):
        """测试添加自定义检查"""
        self.verifier.add_custom_check(lambda: True)
        
        result = self.verifier.verify_rollback()
        
        self.assertIn('custom_check_1', result['checks'])
    
    def test_verification_history(self):
        """测试验证历史"""
        self.verifier.verify_rollback()
        
        history = self.verifier.get_verification_history()
        self.assertIsInstance(history, list)


class TestEnhancedSelfIterationRollback(unittest.TestCase):
    """测试增强自迭代回滚器"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.temp_dir) / "project"
        self.project_dir.mkdir()
        (self.project_dir / "__init__.py").write_text("")
        (self.project_dir / "main.py").write_text("print('hello')")
        
        self.rollback = EnhancedSelfIterationRollback(
            project_root=str(self.project_dir)
        )
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_create_pre_operation_snapshot(self):
        """测试创建操作前快照"""
        snapshot = self.rollback.create_pre_operation_snapshot("test_op")
        
        self.assertIsNotNone(snapshot)
    
    def test_evaluate_rollback_trigger(self):
        """测试评估回滚触发"""
        result = self.rollback.evaluate_rollback_trigger()
        
        self.assertIn('should_rollback', result)
    
    def test_send_enhanced_notification(self):
        """测试发送增强通知"""
        result = self.rollback.send_enhanced_notification(
            "Test Title",
            "Test Message",
            severity="info"
        )
        
        self.assertTrue(result['sent'])
    
    def test_verify_rollback_enhanced(self):
        """测试增强回滚验证"""
        result = self.rollback.verify_rollback_enhanced(
            level=RollbackVerificationLevel.BASIC
        )
        
        self.assertIn('passed', result)
    
    def test_add_verification_check(self):
        """测试添加验证检查"""
        self.rollback.add_verification_check(lambda: True)
    
    def test_get_enhanced_statistics(self):
        """测试获取增强统计"""
        stats = self.rollback.get_enhanced_statistics()
        
        self.assertIn('total_snapshots', stats)
        self.assertIn('enhanced', stats)


class TestIntegration(unittest.TestCase):
    """集成测试"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.temp_dir) / "project"
        self.project_dir.mkdir()
        (self.project_dir / "__init__.py").write_text("")
        (self.project_dir / "main.py").write_text("print('hello')")
    
    def tearDown(self):
        import shutil
from skillscripts.core.path_config_center import get_path_config
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_full_workflow(self):
        """测试完整工作流"""
        rollback = EnhancedSelfIterationRollback(
            project_root=str(self.project_dir)
        )
        
        snapshot = rollback.create_snapshot(
            version="v1.0.0",
            description="Initial snapshot"
        )
        self.assertIsNotNone(snapshot)
        
        trigger_result = rollback.evaluate_rollback_trigger()
        self.assertIn('should_rollback', trigger_result)
        
        verify_result = rollback.verify_rollback_enhanced(
            level=RollbackVerificationLevel.BASIC
        )
        self.assertIn('passed', verify_result)
        
        stats = rollback.get_enhanced_statistics()
        self.assertGreater(stats['total_snapshots'], 0)
    
    def test_temp_file_workflow(self):
        """测试临时文件工作流"""
        manager = EnhancedTempFileManager()
        
        test_file = Path(self.temp_dir) / "test.py"
        test_file.write_text("print('test')")
        
        temp_result = manager.create_temp_file(str(test_file), content="modified content")
        self.assertTrue(temp_result.success)
        
        state = manager.detect_intelligent_state(str(test_file))
        self.assertIn('status', state)
        
        stats = manager.get_enhanced_statistics()
        self.assertIn('registered_temp_files', stats)


if __name__ == '__main__':
    unittest.main(verbosity=2)
