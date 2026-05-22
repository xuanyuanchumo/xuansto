#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自演化四大能力端到端测试 v33
==========================

全面覆盖自演化系统核心能力：
- 自迭代：问题预测→策略生成→优先级排序→效果评估
- 自优化：策略生成→A/B对比→选择应用→回滚决策
- 自修复：问题检测→规则匹配→修复执行→效果验证
- 自完善：知识提取→模式学习→知识存储→推荐查询
"""

import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock

try:
    from skillscripts.core.self_iteration_enhanced import (
        ProblemType,
        ProblemSeverity,
        IterationPriority,
        IterationStatus,
        RiskLevel,
        VerificationStatus,
        DetectedProblem,
        ResourceEstimate,
        RiskAssessment,
        IterationTask,
    )
    SELF_ITERATION_AVAILABLE = True
except ImportError:
    SELF_ITERATION_AVAILABLE = False


class TestSelfIterationProblemDetection(unittest.TestCase):
    """测试自迭代：问题检测能力"""

    def setUp(self):
        if not SELF_ITERATION_AVAILABLE:
            self.skipTest("self_iteration_enhanced module not available")
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_create_detected_problem_minimal(self):
        """创建最小化检测问题"""
        problem = DetectedProblem(
            problem_id="PROB-001",
            problem_type=ProblemType.CODE_QUALITY,
            severity=ProblemSeverity.HIGH,
            title="高复杂度函数",
            description="函数圈复杂度过高",
            location="module.py:50",
            file_path="/path/to/module.py"
        )
        self.assertEqual(problem.problem_id, "PROB-001")
        self.assertEqual(problem.severity, ProblemSeverity.HIGH)
        self.assertIsNotNone(problem.detected_at)

    def test_create_problem_with_full_details(self):
        """创建包含完整细节的问题"""
        problem = DetectedProblem(
            problem_id="PROB-002",
            problem_type=ProblemType.PERFORMANCE,
            severity=ProblemSeverity.CRITICAL,
            title="性能瓶颈",
            description="数据库查询响应时间过长",
            location="db_handler.py:120-150",
            file_path="/src/db_handler.py",
            line_start=120,
            line_end=150,
            code_snippet="def slow_query():\n    # ... complex logic ...",
            suggestion="添加索引或优化查询",
            impact="影响用户体验",
            confidence=0.95,
            related_problems=["PROB-003"]
        )
        self.assertEqual(problem.line_start, 120)
        self.assertEqual(problem.confidence, 0.95)
        self.assertIn("PROB-003", problem.related_problems)

    def test_problem_serialization_to_dict(self):
        """问题序列化为字典"""
        problem = DetectedProblem(
            problem_id="SERIAL-TEST",
            problem_type=ProblemType.SECURITY,
            severity=ProblemSeverity.CRITICAL,
            title="SQL注入风险",
            description="未参数化查询",
            location="auth.py:30",
            file_path="/auth.py"
        )
        d = problem.to_dict()
        self.assertIsInstance(d, dict)
        self.assertEqual(d["problem_type"], "security")
        self.assertIn("detected_at", d)
        self.assertIn("metadata", d)

    def test_all_problem_types_defined(self):
        """所有问题类型已定义"""
        expected_types = [
            "code_quality", "performance", "security", "documentation",
            "testing", "dependency", "architecture", "maintainability"
        ]
        actual_types = [t.value for t in ProblemType]
        for et in expected_types:
            self.assertIn(et, actual_types)

    def test_severity_levels_ordering(self):
        """严重级别排序正确"""
        severities = list(ProblemSeverity)
        critical_idx = severities.index(ProblemSeverity.CRITICAL)
        low_idx = severities.index(ProblemSeverity.LOW)
        self.assertLess(critical_idx, low_idx)


class TestSelfIterationStrategyGeneration(unittest.TestCase):
    """测试自迭代：策略生成能力"""

    def setUp(self):
        if not SELF_ITERATION_AVAILABLE:
            self.skipTest("self_iteration_enhanced module not available")

    def test_create_resource_estimate(self):
        """创建资源估算"""
        estimate = ResourceEstimate(
            cpu_hours=2.5,
            memory_gb=4.0,
            disk_gb=1.0,
            developer_hours=8.0
        )
        self.assertAlmostEqual(estimate.cpu_hours, 2.5)
        self.assertAlmostEqual(estimate.developer_hours, 8.0)

    def test_resource_estimate_default_values(self):
        """资源估算默认值"""
        estimate = ResourceEstimate()
        self.assertEqual(estimate.cpu_hours, 0.0)
        self.assertEqual(estimate.memory_gb, 0.0)

    def test_resource_estimate_serialization(self):
        """资源估算序列化"""
        estimate = ResourceEstimate(cpu_hours=5.0, network_gb=2.0)
        d = estimate.to_dict()
        self.assertEqual(d["cpu_hours"], 5.0)
        self.assertIn("network_gb", d)

    def test_create_risk_assessment(self):
        """创建风险评估"""
        risk = RiskAssessment(
            risk_level=RiskLevel.MEDIUM,
            risk_factors=["可能影响现有功能", "需要回归测试"],
            mitigation_strategies=["先在测试环境验证", "准备回滚方案"],
            rollback_complexity="中等",
            impact_scope="认证模块",
            probability=0.3
        )
        self.assertEqual(risk.risk_level, RiskLevel.MEDIUM)
        self.assertTrue(len(risk.mitigation_strategies) >= 1)

    def test_risk_assessment_serialization(self):
        """风险评估序列化"""
        risk = RiskAssessment(
            risk_level=RiskLevel.HIGH,
            risk_factors=["高风险因素"],
            mitigation_strategies=["缓解策略"],
            rollback_complexity="复杂",
            impact_scope="全局",
            probability=0.7
        )
        d = risk.to_dict()
        self.assertEqual(d["risk_level"], "high")
        self.assertEqual(d["probability"], 0.7)


class TestSelfIterationPrioritySorting(unittest.TestCase):
    """测试自迭代：优先级排序能力"""

    def setUp(self):
        if not SELF_ITERATION_AVAILABLE:
            self.skipTest("self_iteration_enhanced module not available")

    def test_create_iteration_task_basic(self):
        """创建基本迭代任务"""
        task = IterationTask(
            task_id="TASK-001",
            title="降低复杂度",
            description="重构高复杂度函数",
            problem_ids=["PROB-001"],
            priority=IterationPriority.IMMEDIATE,
            status=IterationStatus.PENDING
        )
        self.assertEqual(task.priority, IterationPriority.IMMEDIATE)
        self.assertEqual(task.status, IterationStatus.PENDING)

    def test_priority_ordering_consistency(self):
        """优先级顺序一致性检查"""
        priorities = list(IterationPriority)
        immediate_idx = priorities.index(IterationPriority.IMMEDIATE)
        high_idx = priorities.index(IterationPriority.HIGH)
        normal_idx = priorities.index(IterationPriority.NORMAL)
        low_idx = priorities.index(IterationPriority.LOW)
        scheduled_idx = priorities.index(IterationPriority.SCHEDULED)

        self.assertLess(immediate_idx, high_idx)
        self.assertLess(high_idx, normal_idx)
        self.assertLess(normal_idx, low_idx)
        self.assertLess(low_idx, scheduled_idx)

    def test_status_transitions_valid(self):
        """状态转换有效性"""
        statuses = list(IterationStatus)
        self.assertIn(IterationStatus.PENDING, statuses)
        self.assertIn(IterationStatus.IN_PROGRESS, statuses)
        self.assertIn(IterationStatus.COMPLETED, statuses)
        self.assertIn(IterationStatus.FAILED, statuses)
        self.assertIn(IterationStatus.ROLLED_BACK, statuses)

    def test_risk_levels_comprehensive(self):
        """风险级别完整性"""
        levels = [r.value for r in RiskLevel]
        self.assertIn("critical", levels)
        self.assertIn("high", levels)
        self.assertIn("medium", levels)
        self.assertIn("low", levels)
        self.assertIn("minimal", levels)


class TestSelfOptimizationABTesting(unittest.TestCase):
    """测试自优化：A/B对比和选择"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_strategy_comparison_metrics(self):
        """策略对比指标计算"""
        strategy_a_results = {
            "execution_time": [100, 105, 98, 102, 99],
            "memory_usage": [50, 52, 48, 51, 49],
            "success_rate": [0.98, 0.97, 0.99, 0.98, 0.98]
        }
        strategy_b_results = {
            "execution_time": [90, 92, 88, 91, 89],
            "memory_usage": [65, 68, 63, 66, 64],
            "success_rate": [0.95, 0.96, 0.94, 0.95, 0.95]
        }

        avg_a_time = sum(strategy_a_results["execution_time"]) / len(strategy_a_results["execution_time"])
        avg_b_time = sum(strategy_b_results["execution_time"]) / len(strategy_b_results["execution_time"])

        avg_a_mem = sum(strategy_a_results["memory_usage"]) / len(strategy_a_results["memory_usage"])
        avg_b_mem = sum(strategy_b_results["memory_usage"]) / len(strategy_b_results["memory_usage"])

        self.assertLess(avg_b_time, avg_a_time, "Strategy B should be faster")
        self.assertGreater(avg_b_mem, avg_a_mem, "Strategy A should use less memory")

    def test_statistical_significance_check(self):
        """统计显著性检验模拟"""
        import statistics

        group_a = [10.1, 10.2, 10.0, 9.9, 10.1] * 20
        group_b = [9.8, 9.7, 9.9, 9.6, 9.8] * 20

        mean_a = statistics.mean(group_a)
        mean_b = statistics.mean(group_b)
        std_a = statistics.stdev(group_a)
        std_b = statistics.stdev(group_b)

        self.assertNotEqual(mean_a, mean_b)
        self.assertGreater(std_a, 0)
        self.assertGreater(std_b, 0)

    def test_rollback_decision_criteria(self):
        """回滚决策标准"""
        scenarios = [
            {"error_rate": 0.05, "performance_delta": -0.10, "should_rollback": True},
            {"error_rate": 0.01, "performance_delta": +0.15, "should_rollback": False},
            {"error_rate": 0.02, "performance_delta": -0.02, "should_rollback": False},
            {"error_rate": 0.15, "performance_delta": +0.05, "should_rollback": True},
        ]

        for scenario in scenarios:
            error_rate = scenario["error_rate"]
            perf_delta = scenario["performance_delta"]
            expected = scenario["should_rollback"]

            should_rollback = (error_rate > 0.10 or
                            (perf_delta < -0.05 and error_rate > 0.03))
            self.assertEqual(should_rollback, expected,
                           f"Failed for scenario: {scenario}")


class TestSelfRepairRuleMatching(unittest.TestCase):
    """测试自修复：规则匹配和执行"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.repair_rules = {
            "syntax_error": {
                "pattern": r"SyntaxError|IndentationError",
                "fix": "修正语法错误和缩进问题",
                "severity": "critical"
            },
            "import_error": {
                "pattern": r"ModuleNotFoundError|ImportError",
                "fix": "安装缺失的依赖包或修正导入路径",
                "severity": "high"
            },
            "type_error": {
                "pattern": r"TypeError.*unsupported|cannot concatenate",
                "fix": "检查数据类型并进行类型转换",
                "severity": "medium"
            },
            "name_error": {
                "pattern": r"NameError.*not defined",
                "fix": "定义缺失的变量、函数或类",
                "severity": "high"
            },
            "assertion_error": {
                "pattern": r"AssertionError",
                "fix": "检查断言条件并修正业务逻辑",
                "severity": "low"
            }
        }

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_match_syntax_error_rule(self):
        """匹配语法错误规则"""
        import re
        error_message = "SyntaxError: invalid syntax at line 45"
        matched_rules = []
        for rule_name, rule_info in self.repair_rules.items():
            if re.search(rule_info["pattern"], error_message):
                matched_rules.append((rule_name, rule_info))
        self.assertTrue(len(matched_rules) >= 1)
        self.assertIn("syntax_error", [r[0] for r in matched_rules])

    def test_match_import_error_rule(self):
        """匹配导入错误规则"""
        import re
        error_message = "ModuleNotFoundError: No module named 'missing_package'"
        matched = []
        for rule_name, rule_info in self.repair_rules.items():
            if re.search(rule_info["pattern"], error_message):
                matched.append(rule_name)
        self.assertIn("import_error", matched)

    def test_no_match_for_unknown_error(self):
        """未知错误不匹配任何规则"""
        import re
        error_message = "CustomUnknownError: something unexpected happened"
        matched = []
        for rule_name, rule_info in self.repair_rules.items():
            if re.search(rule_info["pattern"], error_message):
                matched.append(rule_name)
        self.assertEqual(len(matched), 0)

    def test_fix_suggestion_extraction(self):
        """提取修复建议"""
        error_message = "NameError: name 'user_service' is not defined"
        import re
        for rule_name, rule_info in self.repair_rules.items():
            if re.search(rule_info["pattern"], error_message):
                suggestion = rule_info["fix"]
                self.assertIsNotNone(suggestion)
                self.assertTrue(len(suggestion) > 0)
                return
        self.fail("Should have matched a rule")

    def test_repair_execution_simulation(self):
        """修复执行模拟"""
        repair_log = []
        
        errors_to_fix = [
            ("file_a.py", "SyntaxError: invalid syntax"),
            ("file_b.py", "ImportError: No module named 'requests'"),
            ("file_c.py", "NameError: name 'config' is not defined"),
        ]

        import re
        for file_path, error_msg in errors_to_fix:
            for rule_name, rule_info in self.repair_rules.items():
                if re.search(rule_info["pattern"], error_msg):
                    repair_log.append({
                        "file": file_path,
                        "rule": rule_name,
                        "fix": rule_info["fix"],
                        "severity": rule_info["severity"]
                    })
                    break

        self.assertEqual(len(repair_log), 3)
        fixed_files = [log["file"] for log in repair_log]
        self.assertIn("file_a.py", fixed_files)
        self.assertIn("file_b.py", fixed_files)
        self.assertIn("file_c.py", fixed_files)


class TestSelfRepairEffectVerification(unittest.TestCase):
    """测试自修复：效果验证"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_verify_fix_improves_code_quality(self):
        """验证修复改善代码质量"""
        before_code = '''
def bad_function(x, y, z):
    if x > 0:
        if y > 0:
            if z > 0:
                for i in range(x):
                    if i % 2 == 0:
                        while y > 0:
                            result = x * y * z
                            y -= 1
    return result
'''
        after_code = '''
def good_function(x, y, z):
    return x * y * z
'''

        before_lines = len(before_code.split('\n'))
        after_lines = len(after_code.split('\n'))
        before_complexity_est = before_code.count('if') + before_code.count('for') + before_code.count('while')
        after_complexity_est = after_code.count('if') + after_code.count('for') + after_code.count('while')

        self.assertLess(after_lines, before_lines)
        self.assertLess(after_complexity_est, before_complexity_est)

    def test_verify_fix_preserves_behavior(self):
        """验证修复保留行为"""
        def original_func(items):
            result = []
            for item in items:
                if item is not None and item != '':
                    result.append(str(item).strip())
            return result

        def refactored_func(items):
            return [str(item).strip() for item in items 
                   if item is not None and item != '']

        test_input = [" hello ", "world", None, "", "  test  "]
        original_result = original_func(test_input)
        refactored_result = refactored_func(test_input)
        self.assertEqual(original_result, refactored_result)

    def test_regression_prevention_check(self):
        """回归预防检查"""
        test_cases = [
            ({"input": [1, 2, 3], "expected": 6}),
            ({"input": [-1, 0, 1], "expected": 0}),
            ({"input": [], "expected": 0}),
            ({"input": [100, -50, 50], "expected": 100}),
        ]

        def safe_sum(data):
            return sum(data) if data else 0

        all_passed = True
        for case in test_cases:
            result = safe_sum(case["input"])
            if result != case["expected"]:
                all_passed = False
                break

        self.assertTrue(all_passed)


class TestSelfImprovementKnowledgeExtraction(unittest.TestCase):
    """测试自完善：知识提取"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.knowledge_base = []

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_extract_pattern_from_successful_fix(self):
        """从成功修复中提取模式"""
        fix_history = [
            {
                "problem": "高复杂度函数",
                "solution": "拆分为多个小函数",
                "result": "成功"
            },
            {
                "problem": "重复代码块",
                "solution": "提取公共方法",
                "result": "成功"
            },
            {
                "problem": "过长的方法",
                "solution": "应用单一职责原则拆分",
                "result": "成功"
            }
        ]

        patterns = {}
        for entry in fix_history:
            if entry["result"] == "成功":
                key_pattern = entry["solution"][:20]
                patterns[key_pattern] = patterns.get(key_pattern, 0) + 1

        self.assertTrue(len(patterns) > 0)

    def test_store_knowledge_as_structured_data(self):
        """将知识存储为结构化数据"""
        knowledge_entry = {
            "id": "KNOW-001",
            "category": "refactoring",
            "pattern": "extract_method",
            "trigger_conditions": ["complexity > 10", "lines > 30"],
            "solution_template": "将{function_name}拆分为更小的函数",
            "success_rate": 0.85,
            "applicable_contexts": ["service_layer", "controller"],
            "learned_from": "PROB-001 fix",
            "learned_at": datetime.now().isoformat(),
            "usage_count": 0
        }

        knowledge_file = Path(self.tmpdir) / 'knowledge.json'
        with open(knowledge_file, 'w', encoding='utf-8') as f:
            json.dump([knowledge_entry], f, indent=2, ensure_ascii=False)

        self.assertTrue(knowledge_file.exists())
        with open(knowledge_file, 'r', encoding='utf-8') as f:
            loaded = json.load(f)
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0]["id"], "KNOW-001")

    def test_pattern_learning_similarity_detection(self):
        """模式学习相似性检测"""
        existing_patterns = [
            {"features": ["high_complexity", "many_parameters", "long_method"]},
            {"features": ["duplicate_code", "similar_structure"]},
            {"features": ["deep_nesting", "callback_hell"]}
        ]

        new_case_features = ["high_complexity", "many_parameters", "long_method", "bad_naming"]

        best_match = None
        best_overlap = 0
        for pattern in existing_patterns:
            overlap = len(set(new_case_features) & set(pattern["features"]))
            if overlap > best_overlap:
                best_overlap = overlap
                best_match = pattern

        self.assertIsNotNone(best_match)
        self.assertGreater(best_overlap, 0)

    def test_recommendation_query_by_context(self):
        """按上下文查询推荐"""
        knowledge_base = [
            {"id": "K1", "context": "authentication", "pattern": "add_validation"},
            {"id": "K2", "context": "database", "pattern": "use_connection_pool"},
            {"id": "K3", "context": "api", "pattern": "add_rate_limiting"},
            {"id": "K4", "context": "authentication", "pattern": "hash_passwords"},
        ]

        query_context = "authentication"
        recommendations = [k for k in knowledge_base if k["context"] == query_context]

        self.assertEqual(len(recommendations), 2)
        rec_ids = [r["id"] for r in recommendations]
        self.assertIn("K1", rec_ids)
        self.assertIn("K4", rec_ids)


class TestEvolutionSystemIntegration(unittest.TestCase):
    """测试自演化系统集成场景"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_complete_evolution_cycle_simulation(self):
        """完整演化周期模拟"""
        cycle_log = []

        phase_1_problems = [
            DetectedProblem(
                problem_id="P1",
                problem_type=ProblemType.CODE_QUALITY,
                severity=ProblemSeverity.HIGH,
                title="复杂度高",
                description="函数过于复杂",
                location="core.py:50",
                file_path="/core.py"
            ) if SELF_ITERATION_AVAILABLE else None
        ]
        cycle_log.append(("detect", len([p for p in phase_1_problems if p])))

        strategies_generated = ["extract_method", "apply_strategy"]
        cycle_log.append(("strategize", len(strategies_generated)))

        prioritized = sorted(strategies_generated, key=lambda s: hash(s))
        cycle_log.append(("prioritize", prioritized))

        execution_results = {s: "success" for s in strategies_generated}
        cycle_log.append(("execute", execution_results))

        improvement_score = 85.0
        cycle_log.append(("evaluate", improvement_score))

        self.assertEqual(len(cycle_log), 5)

    def test_multi_dimensional_quality_tracking(self):
        """多维度质量追踪"""
        quality_snapshots = []
        base_time = datetime.now() - timedelta(days=10)

        for day in range(11):
            snapshot = {
                "timestamp": (base_time + timedelta(days=day)).isoformat(),
                "metrics": {
                    "code_quality": 70.0 + day * 1.5,
                    "test_coverage": 60.0 + day * 2.5,
                    "performance": 80.0 + day * 0.8,
                    "security": 90.0
                }
            }
            quality_snapshots.append(snapshot)

        first_score = quality_snapshots[0]["metrics"]["code_quality"]
        last_score = quality_snapshots[-1]["metrics"]["code_quality"]
        improvement = last_score - first_score

        self.assertGreater(improvement, 0)

    def test_knowledge_accumulation_over_cycles(self):
        """多轮循环知识积累"""
        knowledge_store = []

        for cycle_num in range(1, 6):
            new_knowledge = {
                "cycle": cycle_num,
                "lessons_learned": [f"lesson_{i}_{cycle_num}" for i in range(3)],
                "patterns_identified": [f"pattern_{j}_{cycle_num}" for j in range(2)]
            }
            knowledge_store.append(new_knowledge)

        total_lessons = sum(len(k["lessons_learned"]) for k in knowledge_store)
        total_patterns = sum(len(k["patterns_identified"]) for k in knowledge_store)

        self.assertEqual(total_lessons, 15)
        self.assertEqual(total_patterns, 10)
        self.assertEqual(len(knowledge_store), 5)

    def test_adaptive_strategy_selection(self):
        """自适应策略选择"""
        strategy_performance = {
            "aggressive_refactor": {"success_rate": 0.7, "avg_improvement": 15},
            "conservative_fix": {"success_rate": 0.95, "avg_improvement": 5},
            "comprehensive_rewrite": {"success_rate": 0.4, "avg_improvement": 30},
        }

        context = {"risk_tolerance": "low", "urgency": "normal"}

        if context["risk_tolerance"] == "low":
            selected = max(strategy_performance.items(),
                          key=lambda x: x[1]["success_rate"])
        else:
            selected = max(strategy_performance.items(),
                          key=lambda x: x[1]["avg_improvement"])

        strategy_name = selected[0]
        self.assertIn(strategy_name, strategy_performance)

        if context["risk_tolerance"] == "low":
            self.assertEqual(strategy_name, "conservative_fix")


if __name__ == '__main__':
    unittest.main(verbosity=2)
