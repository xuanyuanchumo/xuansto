"""
自动优化器测试模块
测试性能优化器的所有功能
"""

import sys
import os
import json
import unittest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from skillscripts.core.performance_optimizer import (
    PerformanceBottleneckIdentifier,
    PerformanceOptimizationAdvisor,
    PerformanceOptimizationExecutor,
    PerformanceOptimizationValidator,
    UnifiedPerformanceOptimizer,
    PerformanceBottleneck,
    OptimizationSuggestion,
    OptimizationResult,
    BottleneckType,
    OptimizationPriority,
    OptimizationStatus
)
from skillscripts.core.auto_optimizer import (
    AutoOptimizer,
    AutoOptimizationConfig,
    AutoOptimizationMode,
    AutoOptimizationState
)


class TestPerformanceBottleneckIdentifier(unittest.TestCase):
    """测试性能瓶颈识别器"""
    
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_file = self.temp_dir / "test_sample.py"
        
        test_code = '''
def inefficient_function():
    result = []
    for i in range(100):
        for j in range(100):
            for k in range(10):
                result.append(i * j * k)
    return result

def database_query_in_loop():
    items = []
    for item in items:
        db_item = query_db(item.id)
    return items

def blocking_operation():
    import time
    time.sleep(0.1)
    return "done"

def memory_intensive():
    data = list(range(10000))
    return data
'''
        with open(self.test_file, 'w') as f:
            f.write(test_code)
    
    def test_identify_bottlenecks(self):
        identifier = PerformanceBottleneckIdentifier()
        bottlenecks = identifier.identify_bottlenecks(self.temp_dir)
        
        self.assertGreater(len(bottlenecks), 0)
        
        bottleneck_types = [b.bottleneck_type for b in bottlenecks]
        self.assertIn(BottleneckType.CPU_INTENSIVE, bottleneck_types)
    
    def test_identify_runtime_bottlenecks(self):
        identifier = PerformanceBottleneckIdentifier()
        
        def sample_function():
            total = 0
            for i in range(1000):
                total += i
            return total
        
        bottlenecks = identifier.identify_runtime_bottlenecks(sample_function)
        
        self.assertGreater(len(bottlenecks), 0)
    
    def tearDown(self):
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)


class TestPerformanceOptimizationAdvisor(unittest.TestCase):
    """测试性能优化建议生成器"""
    
    def setUp(self):
        self.bottleneck = PerformanceBottleneck(
            bottleneck_type=BottleneckType.CPU_INTENSIVE,
            file_path="test.py",
            line_number=10,
            function_name="inefficient_function",
            description="测试瓶颈",
            impact_score=8.0,
            priority=OptimizationPriority.HIGH,
            code_snippet="test code",
            suggestions=["优化建议"],
            estimated_improvement="50%"
        )
        self.advisor = PerformanceOptimizationAdvisor()
    
    def test_generate_suggestions(self):
        suggestions = self.advisor.generate_suggestions([self.bottleneck])
        
        self.assertEqual(len(suggestions), 1)
        self.assertEqual(suggestions[0].optimization_type, "cpu_optimization")
        self.assertEqual(len(suggestions[0].implementation_steps), 5)
        self.assertTrue(len(suggestions[0].code_example) > 0)
    
    def test_suggestion_for_database_bottleneck(self):
        db_bottleneck = PerformanceBottleneck(
            bottleneck_type=BottleneckType.DATABASE_N_PLUS_1,
            file_path="test.py",
            line_number=20,
            function_name="database_query_in_loop",
            description="N+1 查询问题",
            impact_score=9.0,
            priority=OptimizationPriority.CRITICAL,
            code_snippet="test code",
            suggestions=["优化建议"],
            estimated_improvement="80%"
        )
        suggestions = self.advisor.generate_suggestions([db_bottleneck])
        
        self.assertEqual(len(suggestions), 1)
        self.assertEqual(suggestions[0].optimization_type, "database_optimization")


class TestPerformanceOptimizationExecutor(unittest.TestCase):
    """测试性能优化执行器"""
    
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_file = self.temp_dir / "test_sample.py"
        
        with open(self.test_file, 'w') as f:
            f.write('''
def test_function():
    result = []
    for i in range(10):
        result.append(i)
    return result
''')
        
        self.executor = PerformanceOptimizationExecutor()
    
    def test_execute_optimization_dry_run(self):
        suggestion = OptimizationSuggestion(
            suggestion_id="TEST-001",
            bottleneck=PerformanceBottleneck(
                bottleneck_type=BottleneckType.CPU_INTENSIVE,
                file_path=str(self.test_file),
                line_number=10,
                function_name="test_function",
                description="Test",
                impact_score=5.0,
                priority=OptimizationPriority.MEDIUM,
                code_snippet="",
                suggestions=[],
                estimated_improvement="10%"
            ),
            optimization_type="cpu_optimization",
            description="Test optimization",
            implementation_steps=["Step 1", "Step 2"],
            code_example="",
            estimated_effort="Low",
            risk_level="Low",
            dependencies=[],
            expected_metrics={}
        )
        
        result = self.executor.execute_optimization(
            suggestion,
            self.temp_dir,
            auto_apply=False
        )
        
        self.assertFalse(result.success)
        self.assertEqual(result.status, OptimizationStatus.PENDING)
    
    def tearDown(self):
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)


class TestPerformanceOptimizationValidator(unittest.TestCase):
    """测试性能优化效果验证器"""
    
    def setUp(self):
        self.validator = PerformanceOptimizationValidator()
    
    def test_validate_optimization_success(self):
        result = OptimizationResult(
            optimization_id="TEST-001",
            timestamp=datetime.now().isoformat(),
            bottleneck=PerformanceBottleneck(
                bottleneck_type=BottleneckType.CPU_INTENSIVE,
                file_path="test.py",
                line_number=10,
                function_name="test",
                description="Test",
                impact_score=5.0,
                priority=OptimizationPriority.MEDIUM,
                code_snippet="",
                suggestions=[],
                estimated_improvement="10%"
            ),
            suggestion=OptimizationSuggestion(
                suggestion_id="TEST-001",
                bottleneck=None,
                optimization_type="cpu_optimization",
                description="Test",
                implementation_steps=[],
                code_example="",
                estimated_effort="Low",
                risk_level="Low",
                dependencies=[],
                expected_metrics={}
            ),
            before_metrics={'cpu_usage': 80.0, 'memory_usage_mb': 100.0, 'response_time_ms': 500.0},
            after_metrics={'cpu_usage': 40.0, 'memory_usage_mb': 50.0, 'response_time_ms': 250.0},
            improvement_percent=0.0,
            success=True,
            execution_log=["Test optimization"],
            status=OptimizationStatus.COMPLETED
        )
        
        validation = self.validator.validate_optimization(result)
        
        self.assertTrue(validation['improvement_verified'])
        self.assertIn('cpu_usage', validation['metrics_improved'])


class TestUnifiedPerformanceOptimizer(unittest.TestCase):
    """测试统一性能优化管理器"""
    
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_file = self.temp_dir / "test_sample.py"
        
        with open(self.test_file, 'w') as f:
            f.write('''
def test_function():
    result = []
    for i in range(10):
        result.append(i)
    return result
''')
        
        self.optimizer = UnifiedPerformanceOptimizer(self.temp_dir)
    
    def test_run_full_optimization_cycle(self):
        report = self.optimizer.run_full_optimization_cycle(auto_apply=False)
        
        self.assertIsNotNone(report)
        self.assertIn('cycle_id', report)
        self.assertIn('bottlenecks_found', report)
        self.assertIn('suggestions_generated', report)
    
    def test_export_report(self):
        report = self.optimizer.run_full_optimization_cycle(auto_apply=False)
        
        output_path = self.temp_dir / "report.json"
        self.optimizer.export_report(report, output_path)
        
        self.assertTrue(output_path.exists())
        
        with open(output_path, 'r') as f:
            saved_report = json.load(f)
        
        self.assertEqual(saved_report['cycle_id'], report['cycle_id'])
    
    def tearDown(self):
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)


class TestAutoOptimizer(unittest.TestCase):
    """测试自动优化器"""
    
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_file = self.temp_dir / "test_sample.py"
        
        with open(self.test_file, 'w') as f:
            f.write('''
def test_function():
    result = []
    for i in range(100):
        result.append(i)
    return result
''')
        
        config = AutoOptimizationConfig(
            mode=AutoOptimizationMode.ON_DEMAND,
            check_interval_seconds=60,
            optimization_interval_seconds=300,
            max_optimizations_per_cycle=3
        )
        
        self.optimizer = AutoOptimizer(self.temp_dir, config)
    
    def test_run_optimization_cycle(self):
        report = self.optimizer.run_optimization_cycle()
        
        self.assertIsNotNone(report)
        self.assertEqual(report['state'], AutoOptimizationState.COMPLETED.value)
    
    def test_start_stop(self):
        self.optimizer.start()
        self.assertEqual(self.optimizer.get_current_state(), AutoOptimizationState.MONITORING)
        
        self.optimizer.stop()
        self.assertEqual(self.optimizer.get_current_state(), AutoOptimizationState.PAUSED)
    
    def test_get_optimization_history(self):
        self.optimizer.run_optimization_cycle()
        self.optimizer.run_optimization_cycle()
        
        history = self.optimizer.get_optimization_history()
        self.assertEqual(len(history), 2)
    
    def test_export_report(self):
        report = self.optimizer.run_optimization_cycle()
        
        output_path = self.temp_dir / "auto_opt_report.json"
        self.optimizer.export_report(report, output_path)
        
        self.assertTrue(output_path.exists())
    
    def tearDown(self):
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)


if __name__ == '__main__':
    unittest.main()
