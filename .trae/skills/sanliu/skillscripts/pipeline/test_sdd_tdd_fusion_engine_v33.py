#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SDD-TDD 融合引擎完整循环测试 v33
==============================

覆盖红绿蓝回归完整循环流程：
- 规范解析→测试骨架生成链路
- 测试失败→代码实现引导链路
- 代码实现→重构优化链路
- 回归验证→规范更新闭环
- 产物追溯完整性
- 异常场景和错误恢复
"""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock, call

from skillscripts.pipeline.sdd_tdd_fusion_engine import (
    SDDTDDFusionEngine,
    SDDSpecParser,
    TestSkeletonGenerator,
    TestRunner,
    FailureAnalyzer,
    ImplementationGuideGenerator,
    RefactoringAnalyzer,
    OptimizationApplier,
    RegressionTester,
    ArtifactTracer,
    SpecDocumentationUpdater,
    ReportGenerator,
    FusionEngineConfig,
    FusionPhase,
    PhaseStatus,
    CycleStatus,
    Requirement,
    AcceptanceCriterion,
    TestCase,
    TestResult,
    FailureInfo,
    FailureAnalysis,
    ImplementationGuide,
    RefactoringSuggestion,
    OptimizationResult,
    RegressionResult,
    ArtifactTrace,
    CycleReport,
)


class TestSDDSpecParserEdgeCases(unittest.TestCase):
    """测试SDD规范解析器边界情况"""

    def setUp(self):
        self.parser = SDDSpecParser()
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_parse_nonexistent_file_raises_error(self):
        """测试解析不存在文件抛出FileNotFoundError"""
        with self.assertRaises(FileNotFoundError):
            self.parser.parse(Path('/nonexistent/spec.md'))

    def test_parse_unsupported_format_raises_error(self):
        """测试不支持的格式抛出ValueError"""
        spec_file = Path(self.tmpdir) / 'test.txt'
        spec_file.write_text('content')
        with self.assertRaises(ValueError) as ctx:
            self.parser.parse(spec_file)
        self.assertIn("不支持", str(ctx.exception))

    def test_parse_empty_markdown_file(self):
        """测试解析空Markdown文件返回默认规范"""
        spec_file = Path(self.tmpdir) / 'empty.md'
        spec_file.write_text('')
        spec = self.parser.parse(spec_file)
        self.assertIsInstance(spec.spec_id, str)
        self.assertTrue(len(spec.spec_id) > 0)
        self.assertEqual(spec.title, "未命名规范")

    def test_parse_markdown_with_only_title(self):
        """测试只有标题的Markdown"""
        content = "# 用户认证规范\n"
        spec_file = Path(self.tmpdir) / 'title_only.md'
        spec_file.write_text(content)
        spec = self.parser.parse(spec_file)
        self.assertEqual(spec.title, "用户认证规范")

    def test_parse_markdown_with_requirements_section(self):
        """测试包含需求列表的Markdown"""
        content = """# 测试规范

## 功能需求
- 用户登录功能：支持用户名密码登录
- 用户注册功能：支持邮箱注册
- 密码重置功能：支持通过邮件重置
"""
        spec_file = Path(self.tmpdir) / 'with_reqs.md'
        spec_file.write_text(content)
        spec = self.parser.parse(spec_file)
        self.assertTrue(len(spec.requirements) >= 2)

    def test_parse_markdown_with_given_when_then(self):
        """测试包含Given-When-Then的Markdown"""
        content = """# 认证测试

### 场景1: 成功登录
Given: 用户已注册且密码正确
When: 提交登录表单
Then: 系统允许登录并跳转首页
"""
        spec_file = Path(self.tmpdir) / 'gwt.md'
        spec_file.write_text(content)
        spec = self.parser.parse(spec_file)
        self.assertTrue(len(spec.acceptance_criteria) >= 1)

    def test_parse_yaml_format_basic(self):
        """测试基本YAML格式解析"""
        try:
            import yaml
            content = """
spec:
  name: YAML测试规范
  version: v2.0.0
requirements:
  - id: REQ-001
    title: 基本功能
    priority: high
"""
            spec_file = Path(self.tmpdir) / 'test.yaml'
            spec_file.write_text(content)
            spec = self.parser.parse(spec_file)
            self.assertEqual(spec.title, "YAML测试规范")
        except ImportError:
            self.skipTest("PyYAML not installed")

    def test_parse_json_format(self):
        """测试JSON格式解析"""
        content = json.dumps({
            "spec": {
                "name": "JSON规范",
                "version": "v1.5.0",
                "requirements": [
                    {"id": "REQ-001", "title": "功能A", "priority": "critical"}
                ]
            }
        })
        spec_file = Path(self.tmpdir) / 'test.json'
        spec_file.write_text(content)
        spec = self.parser.parse(spec_file)
        self.assertEqual(spec.title, "JSON规范")

    def test_priority_inference_from_keywords(self):
        """测试从关键词推断优先级"""
        parser = SDDSpecParser()
        critical_text = parser._infer_priority("这是核心功能，必须实现")
        self.assertEqual(critical_text, "critical")

        high_text = parser._infer_priority("这是重要的主要功能")
        self.assertEqual(high_text, "high")

        low_text = parser._infer_priority("这是可选的次要功能")
        self.assertEqual(low_text, "low")


class TestTestSkeletonGeneratorComprehensive(unittest.TestCase):
    """测试测试骨架生成器完整场景"""

    def setUp(self):
        self.generator = TestSkeletonGenerator()

    def test_generate_from_spec_with_multiple_requirements(self):
        """测试从多需求规范生成测试骨架"""
        spec = SDDSpec(
            spec_id="SPC-TEST",
            title="多需求测试",
            requirements=[
                Requirement(req_id="REQ-001", title="功能A", priority="critical"),
                Requirement(req_id="REQ-002", title="功能B", priority="high"),
                Requirement(req_id="REQ-003", title="功能C", priority="medium"),
            ]
        )
        tests = self.generator.generate(spec)
        self.assertTrue(len(tests) >= 6)

    def test_generate_includes_happy_path_test(self):
        """测试生成包含正常路径测试"""
        req = Requirement(req_id="REQ-001", title="用户登录", priority="high")
        spec = SDDSpec(spec_id="SPC-01", title="测试", requirements=[req])
        tests = self.generator.generate(spec)
        happy_path_tests = [t for t in tests if "happy_path" in t.name]
        self.assertTrue(len(happy_path_tests) > 0)

    def test_generate_critical_requirement_includes_boundary_test(self):
        """测试关键需求生成边界条件测试"""
        req = Requirement(req_id="REQ-001", title="核心功能", priority="critical")
        spec = SDDSpec(spec_id="SPC-01", title="测试", requirements=[req])
        tests = self.generator.generate(spec)
        boundary_tests = [t for t in tests if "boundary" in t.name]
        self.assertTrue(len(boundary_tests) > 0)

    def test_generate_always_includes_error_handling_test(self):
        """测试总是生成异常处理测试"""
        req = Requirement(req_id="REQ-001", title="任意功能", priority="low")
        spec = SDDSpec(spec_id="SPC-01", title="测试", requirements=[req])
        tests = self.generator.generate(spec)
        error_tests = [t for t in tests if "error_handling" in t.name]
        self.assertTrue(len(error_tests) > 0)

    def test_generate_from_acceptance_criteria(self):
        """测试从验收标准生成测试"""
        ac = AcceptanceCriterion(
            criterion_id="AC-001",
            description="登录成功",
            given="有效用户名和密码",
            when="提交登录表单",
            then="系统认证成功"
        )
        spec = SDDSpec(spec_id="SPC-01", title="测试", acceptance_criteria=[ac])
        tests = self.generator.generate(spec)
        acceptance_tests = [t for t in tests if t.tags and "acceptance" in t.tags]
        self.assertTrue(len(acceptance_tests) > 0)

    def test_generated_tests_have_code(self):
        """测试生成的测试用例包含代码"""
        req = Requirement(req_id="REQ-001", title="测试功能")
        spec = SDDSpec(spec_id="SPC-01", title="测试", requirements=[req])
        tests = self.generator.generate(spec)
        for tc in tests:
            self.assertIsInstance(tc.code, str)
            self.assertTrue(len(tc.code) > 0)
            self.assertIn("def ", tc.code)

    def test_sanitize_name_handles_special_chars(self):
        """测试名称清理处理特殊字符"""
        result = self.generator._sanitize_name("功能 A-B_C!@#")
        self.assertNotIn('!', result)
        self.assertNotIn('@', result)
        self.assertNotIn('#', result)
        self.assertIn('_', result)

    def test_generate_preserves_source_requirement_link(self):
        """测试生成保留需求来源链接"""
        req = Requirement(req_id="REQ-099", title="追踪测试")
        spec = SDDSpec(spec_id="SPC-01", title="测试", requirements=[req])
        tests = self.generator.generate(spec)
        for tc in tests:
            if tc.source_requirement:
                self.assertEqual(tc.source_requirement, "REQ-099")


class TestFailureAnalyzerDetailed(unittest.TestCase):
    """测试失败分析器详细场景"""

    def setUp(self):
        self.analyzer = FailureAnalyzer()

    def test_analyze_all_passed_returns_no_failures(self):
        """测试全通过时无失败信息"""
        result = TestResult(
            total_tests=10,
            passed=10,
            failed=0,
            success=True,
            test_results=[
                {"name": "test_1", "status": "passed"},
                {"name": "test_2", "status": "passed"}
            ]
        )
        analysis = self.analyzer.analyze(result)
        self.assertEqual(len(analysis.failures), 0)
        self.assertEqual(analysis.severity, "low")

    def test_analyze_assertion_errors(self):
        """测试断言错误分析"""
        result = TestResult(
            total_tests=5,
            passed=3,
            failed=2,
            test_results=[
                {"name": "test_assert", "status": "failed",
                 "message": "AssertionError: Expected 5 but got 3"},
                {"name": "test_another", "status": "failed",
                 "message": "AssertionError: Values do not match"}
            ]
        )
        analysis = self.analyzer.analyze(result)
        self.assertEqual(len(analysis.failures), 2)
        self.assertIn("AssertionError", analysis.failure_patterns)

    def test_analyze_not_implemented_errors(self):
        """测试NotImplementedError分析（红阶段正常现象）"""
        result = TestResult(
            total_tests=3,
            passed=0,
            failed=3,
            test_results=[
                {"name": "test_new_feature", "status": "failed",
                 "message": "NotImplementedError: 测试尚未实现 (红阶段)"}
            ]
        )
        analysis = self.analyzer.analyze(result)
        self.assertIn("NotImplementedError", analysis.failure_patterns)
        self.assertIn("红阶段", analysis.root_cause_summary)

    def test_analyze_import_errors_as_critical(self):
        """测试导入错误标记为严重"""
        result = TestResult(
            total_tests=2,
            passed=0,
            failed=2,
            test_results=[
                {"name": "test_import", "status": "failed",
                 "message": "ImportError: No module named 'missing_module'"}
            ]
        )
        analysis = self.analyzer.analyze(result)
        self.assertEqual(analysis.severity, "high")

    def test_analyze_mixed_failure_types(self):
        """测试混合失败类型分析"""
        result = TestResult(
            total_tests=6,
            passed=2,
            failed=4,
            test_results=[
                {"name": "test_a", "status": "failed",
                 "message": "NotImplementedError: 未实现"},
                {"name": "test_b", "status": "failed",
                 "message": "AssertionError: 断言失败"},
                {"name": "test_c", "status": "failed",
                 "message": "ImportError: 缺少模块"},
                {"name": "test_d", "status": "failed",
                 "message": "NameError: 变量未定义"}
            ]
        )
        analysis = self.analyzer.analyze(result)
        self.assertTrue(len(analysis.failure_patterns) >= 3)
        self.assertTrue(len(analysis.fix_suggestions) > 0)

    def test_analyze_generates_fix_suggestions(self):
        """测试生成修复建议"""
        result = TestResult(
            total_tests=2,
            passed=0,
            failed=2,
            test_results=[
                {"name": "test_x", "status": "failed",
                 "message": "NotImplementedError: 功能未实现"}
            ]
        )
        analysis = self.analyzer.analyze(result)
        self.assertTrue(len(analysis.fix_suggestions) >= 1)
        self.assertTrue(any("实现" in s for s in analysis.fix_suggestions))


class TestImplementationGuideGeneration(unittest.TestCase):
    """测试代码实现引导生成"""

    def setUp(self):
        self.guide_gen = ImplementationGuideGenerator()

    def test_guide_contains_target_tests(self):
        """测试引导包含目标测试列表"""
        analysis = FailureAnalysis(
            failures=[FailureInfo(test_name="test_login_failed",
                                   error_type="NotImplementedError")]
        )
        guide = self.guide_gen.generate(analysis, [])
        self.assertIn("test_login_failed", guide.target_tests)

    def test_guide_has_implementation_steps(self):
        """测试引导包含实施步骤"""
        analysis = FailureAnalysis(
            failures=[
                FailureInfo(test_name="test_1", error_type="NotImplementedError"),
                FailureInfo(test_name="test_2", error_type="AssertionError")
            ]
        )
        guide = self.guide_gen.generate(analysis, [])
        self.assertTrue(len(guide.implementation_steps) >= 3)

    def test_guide_estimates_effort_correctly(self):
        """测试工作量估算准确性"""
        few_failures = FailureAnalysis(
            failures=[FailureInfo(test_name=f"test_{i}", error_type="Error")
                      for i in range(2)]
        )
        guide_small = self.guide_gen.generate(few_failures, [])
        self.assertEqual(guide_small.estimated_effort, "small")

        many_failures = FailureAnalysis(
            failures=[FailureInfo(test_name=f"test_{i}", error_type="Error")
                      for i in range(12)]
        )
        guide_large = self.guide_gen.generate(many_failures, [])
        self.assertIn(guide_large.estimated_effort, ["large", "very_large"])

    def test_guide_suggests_function_signatures(self):
        """测试建议函数签名"""
        tests = [
            TestCase(test_id="TC-001", name="test_user_login",
                     description="测试用户登录", given="", when="", then="")
        ]
        analysis = FailureAnalysis(failures=[])
        guide = self.guide_gen.generate(analysis, tests)
        if guide.suggested_signatures:
            sig = guide.suggested_signatures[0]
            self.assertIn("function", sig)
            self.assertIn("signature", sig)


class TestRefactoringAnalyzerScenarios(unittest.TestCase):
    """测试重构分析器各种场景"""

    def setUp(self):
        self.analyzer = RefactoringAnalyzer()
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_analyze_nonexistent_file_returns_empty(self):
        """测试分析不存在文件返回空列表"""
        suggestions = self.analyzer.suggest(Path('/nonexistent/file.py'))
        self.assertEqual(suggestions, [])

    def test_detect_long_method(self):
        """测试检测过长方法"""
        code = '\n'.join([f'    pass' for _ in range(30)])
        code = f'def very_long_function():\n{code}\n'
        file_path = Path(self.tmpdir) / 'long_method.py'
        file_path.write_text(code)
        suggestions = self.analyzer.suggest(file_path)
        long_method_refs = [s for s in suggestions
                            if s.refactoring_type == "extract_method"]
        self.assertTrue(len(long_method_refs) > 0)

    def test_detect_duplicate_code(self):
        """测试检测重复代码"""
        unique_line = 'result = complex_calculation(param1, param2, param3)'
        code = f'''
def function_a():
    {unique_line}
    return result

def function_b():
    {unique_line}
    return result
'''
        file_path = Path(self.tmpdir) / 'duplicate.py'
        file_path.write_text(code)
        suggestions = self.analyzer.suggest(file_path)
        dup_refs = [s for s in suggestions
                    if s.refactoring_type == "remove_duplication"]
        self.assertTrue(len(dup_refs) > 0)

    def test_detect_long_line(self):
        """检测超长行"""
        long_line = 'x' * 150
        code = f'def func():\n    result = "{long_line}"\n    return result\n'
        file_path = Path(self.tmpdir) / 'long_line.py'
        file_path.write_text(code)
        suggestions = self.analyzer.suggest(file_path)
        style_refs = [s for s in suggestions
                      if s.refactoring_type == "simplify"]
        self.assertTrue(len(style_refs) > 0)


class TestOptimizationApplierBehavior(unittest.TestCase):
    """测试优化应用器行为"""

    def setUp(self):
        self.applier = OptimizationApplier()
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_apply_empty_suggestions(self):
        """测试应用空建议列表"""
        result = self.applier.apply([])
        self.assertEqual(result.successful_count, 0)
        self.assertEqual(result.failed_count, 0)

    def test_apply_nonexistent_file_skipped(self):
        """测试跳过不存在文件的建议"""
        suggestion = RefactoringSuggestion(
            suggestion_id="REF-TEST",
            refactoring_type="simplify",
            target_file="/nonexistent/file.py",
            target_location="line_1",
            description="Test suggestion"
        )
        result = self.applier.apply([suggestion])
        self.assertEqual(result.failed_count, 1)

    def test_apply_creates_backup_before_modification(self):
        """测试修改前创建备份"""
        code = 'x' * 150 + '\n'
        file_path = Path(self.tmpdir) / 'backup_test.py'
        file_path.write_text(code)

        suggestion = RefactoringSuggestion(
            suggestion_id="REF-BACKUP",
            refactoring_type="simplify",
            target_file=str(file_path),
            target_location="line_1",
            description="Long line"
        )
        result = self.applier.apply([suggestion])
        self.assertIn("REF-BACKUP", result.rollback_data)


class TestRegressionTesterFunctionality(unittest.TestCase):
    """测试回归测试器功能"""

    def setUp(self):
        config = FusionEngineConfig(test_timeout=5)
        self.tester = RegressionTester(config)

    def test_run_regression_on_empty_list(self):
        """测试空测试列表的回归"""
        result = self.tester.run([])
        self.assertEqual(result.total_tests, 0)
        self.assertTrue(result.stable)

    def test_regression_result_structure(self):
        """测试回归结果结构完整性"""
        result = RegressionResult(
            regression_id="REG-TEST",
            test_paths=["test_a.py"],
            total_tests=10,
            passed=10,
            failed=0
        )
        self.assertTrue(result.stable)
        self.assertEqual(len(result.new_failures), 0)


class TestArtifactTracerCompleteness(unittest.TestCase):
    """测试产物追溯完整性"""

    def setUp(self):
        self.tracer = ArtifactTracer()

    def test_initial_state_empty(self):
        """测试初始状态为空"""
        trace = self.tracer.trace("CYCLE-001")
        self.assertEqual(trace.completeness_score, 0.0)
        self.assertEqual(len(trace.artifacts), 0)

    def test_register_and_trace_single_category(self):
        """测试注册并追溯单个类别"""
        artifact = Path("/tmp/test_artifact.py")
        self.tracer.register("test_skeleton", artifact)
        trace = self.tracer.trace("CYCLE-002")
        self.assertIn("test_skeleton", trace.artifacts)
        self.assertGreater(trace.completeness_score, 0)

    def test_register_duplicate_avoids_duplication(self):
        """测试重复注册避免重复"""
        artifact = Path("/tmp/duplicate.py")
        self.tracer.register("tests", artifact)
        self.tracer.register("tests", artifact)
        trace = self.tracer.trace("CYCLE-003")
        self.assertEqual(len(trace.artifacts.get("tests", [])), 1)

    def test_trace_matrix_population(self):
        """测试追溯矩阵填充"""
        self.tracer.register("test_skeleton", Path("/tmp/test.py"))
        self.tracer.register("code_implementation", Path("/tmp/impl.py"))
        self.tracer.register("reports", Path("/tmp/report.md"))
        trace = self.tracer.trace("CYCLE-004")
        self.assertIn("spec_to_tests", trace.trace_matrix)
        self.assertIn("tests_to_code", trace.trace_matrix)
        self.assertIn("code_to_report", trace.trace_matrix)

    def test_completeness_score_calculation(self):
        """测试完整性得分计算"""
        self.tracer.register("category1", Path("/tmp/a.py"))
        score = self.tracer.trace("CYCLE-005").completeness_score
        expected = 1 / 3 * 100
        self.assertAlmostEqual(score, expected, places=1)


class TestReportGenerationFormats(unittest.TestCase):
    """测试报告生成格式"""

    def setUp(self):
        self.generator = ReportGenerator()
        self.sample_report = CycleReport(
            cycle_id="CYCLE-TEST-001",
            start_time=__import__('datetime').datetime.now(),
            end_time=__import__('datetime').datetime.now(),
            phase_results={
                "red": {"status": "passed", "duration": 1.5,
                        "metrics": {"test_cases_generated": 10}},
                "green": {"status": "passed", "duration": 2.0,
                           "metrics": {"failures_analyzed": 3}},
                "blue": {"status": "passed", "duration": 1.0,
                          "metrics": {"refactoring_suggestions": 5}},
                "regression": {"status": "passed", "stable": True, "duration": 0.5}
            },
            artifacts=[Path("/tmp/artifact1.md")],
            quality_metrics={"overall_quality": 85.0},
            status="success",
            summary="所有阶段成功完成"
        )

    def test_markdown_report_contains_cycle_id(self):
        """测试Markdown报告包含循环ID"""
        md = self.generator.generate_markdown(self.sample_report)
        self.assertIn("CYCLE-TEST-001", md)

    def test_markdown_report_contains_phase_info(self):
        """测试Markdown报告包含各阶段信息"""
        md = self.generator.generate_markdown(self.sample_report)
        self.assertIn("RED", md.upper() or "red".upper())
        self.assertIn("GREEN", md.upper() or "green".upper())

    def test_json_report_valid_json(self):
        """测试JSON报告是有效JSON"""
        json_str = self.generator.generate_json(self.sample_report)
        data = json.loads(json_str)
        self.assertEqual(data["cycle_id"], "CYCLE-TEST-001")
        self.assertIn("phase_results", data)

    def test_json_report_contains_quality_metrics(self):
        """测试JSON报告包含质量指标"""
        json_str = self.generator.generate_json(self.sample_report)
        data = json.loads(json_str)
        self.assertIn("quality_metrics", data)
        self.assertEqual(data["quality_metrics"]["overall_quality"], 85.0)


class TestFusionEngineConfiguration(unittest.TestCase):
    """测试融合引擎配置"""

    def test_default_config_values(self):
        """测试默认配置值"""
        config = FusionEngineConfig()
        self.assertEqual(config.max_iterations, 10)
        self.assertEqual(config.coverage_threshold, 80.0)
        self.assertTrue(config.enable_refactoring)
        self.assertTrue(config.enable_regression)
        self.assertFalse(config.auto_generate_implementation)

    def test_custom_config_override(self):
        """测试自定义配置覆盖"""
        config = FusionEngineConfig(
            max_iterations=20,
            coverage_threshold=90.0,
            fail_fast=True,
            enable_refactoring=False
        )
        self.assertEqual(config.max_iterations, 20)
        self.assertEqual(config.coverage_threshold, 90.0)
        self.assertTrue(config.fail_fast)
        self.assertFalse(config.enable_refactoring)


class TestEngineIntegrationAdapters(unittest.TestCase):
    """测试引擎集成适配器"""

    def setUp(self):
        self.engine = SDDTDDFusionEngine()

    def test_provincial_coordinator_adapter_submit(self):
        """测试省级协调器适配器提交接口"""
        adapter = self.engine.integrate_with_provincial_coordinator()
        report = CycleReport(
            cycle_id="TEST",
            start_time=__import__('datetime').datetime.now(),
            end_time=__import__('datetime').datetime.now(),
            phase_results={},
            artifacts=[],
            quality_metrics={},
            status="success"
        )
        result = adapter.submit_cycle_report(report)
        self.assertEqual(result["status"], "submitted")

    def test_version_iterator_adapter_increment(self):
        """测试版本迭代器适配器递增版本"""
        adapter = self.engine.integrate_with_version_iterator()
        new_ver = adapter.increment_version("patch")
        self.assertTrue(new_ver.startswith("v"))

    def test_evolution_controller_adapter_trigger(self):
        """测试演化控制器适配器触发下一阶段"""
        adapter = self.engine.integrate_with_evolution_controller()
        result = adapter.trigger_next_phase("red")
        self.assertTrue(result["triggered"])
        self.assertEqual(result["next_phase"], "green")


class TestDataClassValidation(unittest.TestCase):
    """测试数据类验证"""

    def test_requirement_data_class(self):
        """测试Requirement数据类"""
        req = Requirement(
            req_id="REQ-001",
            title="测试需求",
            description="详细描述",
            priority="critical",
            acceptance_criteria=["AC1", "AC2"],
            tags=["auth", "security"]
        )
        self.assertEqual(req.req_id, "REQ-001")
        self.assertEqual(req.priority, "critical")
        self.assertTrue(len(req.acceptance_criteria) == 2)

    def test_test_case_data_class(self):
        """测试TestCase数据类"""
        tc = TestCase(
            test_id="TC-001",
            name="test_example",
            description="示例测试",
            given="前置条件",
            when="执行操作",
            then="预期结果",
            priority="high",
            tags=["unit", "smoke"],
            source_requirement="REQ-001"
        )
        self.assertEqual(tc.priority, "high")
        self.assertIn("unit", tc.tags)

    def test_cycle_report_data_class(self):
        """测试CycleReport数据类"""
        now = __import__('datetime').datetime.now()
        report = CycleReport(
            cycle_id="CYCLE-001",
            start_time=now,
            end_time=now,
            phase_results={},
            artifacts=[],
            quality_metrics={"score": 90},
            status="success"
        )
        self.assertEqual(report.status, "success")
        self.assertEqual(report.quality_metrics["score"], 90)


if __name__ == '__main__':
    unittest.main(verbosity=2)
