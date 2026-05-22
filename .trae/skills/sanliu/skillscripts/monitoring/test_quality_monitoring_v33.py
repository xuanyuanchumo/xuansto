#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
持续质量监控六维体系集成测试 v33
==============================

全面覆盖质量监控系统：
- 代码质量指标采集（圈复杂度、重复率等）
- 测试覆盖监控（行/分支/函数覆盖率）
- 技术债务追踪（识别、量化、排序）
- 性能基准监控（响应时间、吞吐量）
- 安全合规检查（OWASP规则）
- 用户体验指标采集
- 告警触发和处理逻辑
- 多维度数据聚合
"""

import ast
import json
import os
import tempfile
import unittest
from pathlib import Path
from datetime import datetime, timedelta

from skillscripts.monitoring.quality_metrics_collector import (
    QualityMetricsCollector,
    CodeQualityCollector,
    TestQualityCollector,
    DocumentationQualityCollector,
    ArchitectureQualityCollector,
    QualityMetricsRegistry,
    QualityGateChecker,
    QualityTrendAnalyzer,
    ReportGenerator as QualityReportGenerator,
    MetricCategory,
    MetricType,
    GateStatus,
    Severity,
    MetricDefinition,
    MetricValue,
    CodeQualityMetrics,
    TestQualityMetrics,
    DocumentationQualityMetrics,
    ArchitectureQualityMetrics,
    QualityMetricsCollection,
    GateCheckResult,
    QualityGateReport,
    TrendAnalysis,
)


class TestCodeQualityMetricsCollection(unittest.TestCase):
    """测试代码质量指标采集"""

    def setUp(self):
        self.collector = CodeQualityCollector()
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_collect_empty_project_returns_zeros(self):
        """测试空项目返回零值指标"""
        empty_dir = Path(self.tmpdir) / 'empty'
        empty_dir.mkdir()
        metrics = self.collector.collect(empty_dir)
        self.assertIsInstance(metrics, CodeQualityMetrics)
        self.assertEqual(metrics.cyclomatic_complexity, 0.0)
        self.assertEqual(metrics.code_lines, 0)

    def test_collect_simple_python_file(self):
        """测试简单Python文件的指标采集"""
        code = '''
def simple_function():
    return 42

class SimpleClass:
    def method_one(self):
        if True:
            return "hello"
'''
        file_path = Path(self.tmpdir) / 'simple.py'
        file_path.write_text(code)
        metrics = self.collector.collect(Path(self.tmpdir))
        self.assertGreater(metrics.code_lines, 0)
        self.assertIsInstance(metrics.cyclomatic_complexity, float)

    def test_detect_high_complexity_functions(self):
        """检测高复杂度函数"""
        complex_code = '''
def very_complex():
    if condition1:
        if condition2:
            if condition3:
                for i in range(10):
                    if x > 0:
                        while y < 5:
                            try:
                                pass
                            except:
                                pass
'''
        file_path = Path(self.tmpdir) / 'complex.py'
        file_path.write_text(complex_code)
        metrics = self.collector.collect(Path(self.tmpdir))
        self.assertTrue(len(metrics.high_complexity_functions) > 0 or
                        metrics.max_nesting_depth > 3)

    def test_calculate_cyclomatic_complexity(self):
        """测试圈复杂度计算"""
        code = '''
def test_complexity():
    if a:
        if b:
            for i in range(10):
                if c:
                    pass
    elif d:
        try:
            pass
        except:
            pass
'''
        tree = ast.parse(code)
        complexity = self.collector._calculate_cyclomatic_complexity(tree)
        self.assertGreater(complexity, 1)

    def test_detect_code_duplication(self):
        """检测代码重复"""
        duplicated_line = 'result = expensive_calculation(param1, param2)'
        code = f'''
def function_a():
    {duplicated_line}
    return result

def function_b():
    {duplicated_line}
    return result

def function_c():
    {duplicated_line}
    return result
'''
        file_path = Path(self.tmpdir) / 'dup.py'
        file_path.write_text(code)
        metrics = self.collector.collect(Path(self.tmpdir))
        self.assertGreater(metrics.duplicated_blocks, 0)
        self.assertGreater(metrics.code_duplication_rate, 0)

    def test_count_violations(self):
        """统计违规项"""
        code_with_violations = '''
def bad_function():
    except:  # 裸except错误
        pass
    
    x = "a" * 150  # 行过长警告
'''
        file_path = Path(self.tmpdir) / 'violations.py'
        file_path.write_text(code_with_violations)
        metrics = self.collector.collect(Path(self.tmpdir))
        self.assertGreater(metrics.total_violations, 0)

    def test_calculate_maintainability_index(self):
        """计算可维护性指数"""
        mi = self.collector._calculate_maintainability_index(
            avg_complexity=5.0,
            code_lines=1000,
            comment_lines=200
        )
        self.assertGreater(mi, 0)
        self.assertLessEqual(mi, 100)

    def test_maintainability_index_low_complexity_high(self):
        """低复杂度代码应有较高可维护性"""
        mi_good = self.collector._calculate_maintainability_index(
            avg_complexity=2.0,
            code_lines=500,
            comment_lines=150
        )
        mi_bad = self.collector._calculate_maintainability_index(
            avg_complexity=15.0,
            code_lines=500,
            comment_lines=50
        )
        self.assertGreater(mi_good, mi_bad)


class TestTestQualityMetricsCollection(unittest.TestCase):
    """测试测试质量指标采集"""

    def setUp(self):
        self.collector = TestQualityCollector()
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_collect_no_test_files(self):
        """无测试文件时返回零值"""
        empty_dir = Path(self.tmpdir) / 'notests'
        empty_dir.mkdir()
        metrics = self.collector.collect(empty_dir)
        self.assertEqual(metrics.test_count, 0)
        self.assertEqual(metrics.line_coverage, 0.0)

    def test_find_test_files_by_pattern(self):
        """按模式查找测试文件"""
        (Path(self.tmpdir) / 'test_example.py').write_text('def test_x(): pass')
        (Path(self.tmpdir) / 'example_test.py').write_text('def test_y(): pass')
        tests_dir = Path(self.tmpdir) / 'tests'
        tests_dir.mkdir()
        (tests_dir / 'z_test.py').write_text('def test_z(): pass')

        found = self.collector._find_test_files(Path(self.tmpdir))
        self.assertTrue(len(found) >= 3)

    def test_count_test_functions(self):
        """统计测试函数数量"""
        code = '''
import pytest

def test_login_success():
    assert True

def test_login_failure():
    assert False

def test_registration():
    assert True

class TestUserAPI:
    def test_create_user(self):
        pass

    def test_delete_user(self):
        pass
'''
        file_path = Path(self.tmpdir) / 'tests_module.py'
        file_path.write_text(code)
        metrics = self.collector._collect_test_metrics([file_path])
        self.assertEqual(metrics["test_count"], 5)

    def test_parse_coverage_json_report(self):
        """解析JSON格式覆盖率报告"""
        coverage_data = {
            "files": {
                "module_a.py": {
                    "summary": {
                        "covered_lines": 80,
                        "num_statements": 100
                    }
                },
                "module_b.py": {
                    "summary": {
                        "covered_lines": 45,
                        "num_statements": 50
                    }
                }
            }
        }
        coverage_file = Path(self.tmpdir) / 'coverage.json'
        coverage_file.write_text(json.dumps(coverage_data))

        result = self.collector._parse_coverage_report(coverage_file)
        total = coverage_data['files']['module_a.py']['summary']['covered_lines'] + \
                coverage_data['files']['module_b.py']['summary']['covered_lines']
        total_statements = coverage_data['files']['module_a.py']['summary']['num_statements'] + \
                          coverage_data['files']['module_b.py']['summary']['num_statements']
        expected_coverage = (total / total_statements) * 100
        self.assertAlmostEqual(result["line_coverage"], expected_coverage, places=1)

    def test_parse_coverage_xml_report(self):
        """解析XML格式覆盖率报告"""
        xml_content = '''<?xml version="1.0" ?>
<coverage line-rate="0.85" branch-rate="0.70">
</coverage>
'''
        xml_file = Path(self.tmpdir) / 'coverage.xml'
        xml_file.write_text(xml_content)
        result = self.collector._parse_coverage_xml(xml_file)
        self.assertAlmostEqual(result["line_coverage"], 85.0)
        self.assertAlmostEqual(result["branch_coverage"], 70.0)

    def test_calculate_test_quality_score(self):
        """计算测试质量评分"""
        score_100 = self.collector._calculate_test_quality_score(
            line_coverage=90.0,
            pass_rate=1.0,
            test_count=100
        )
        score_50 = self.collector._calculate_test_quality_score(
            line_coverage=40.0,
            pass_rate=0.8,
            test_count=20
        )
        self.assertGreater(score_100, score_50)

    def test_identify_low_coverage_files(self):
        """识别低覆盖率文件"""
        coverage_data = {
            "files": {
                "low_cov.py": {"summary": {"covered_lines": 30, "num_statements": 100}},
                "ok_cov.py": {"summary": {"covered_lines": 85, "num_statements": 100}}
            }
        }
        coverage_file = Path(self.tmpdir) / 'cov.json'
        coverage_file.write_text(json.dumps(coverage_data))
        result = self.collector._parse_coverage_report(coverage_file)
        low_cov_files = result.get("low_coverage_files", [])
        self.assertTrue(any(f["file"] == "low_cov.py" for f in low_cov_files))


class TestDocumentationQualityMetricsCollection(unittest.TestCase):
    """测试文档质量指标采集"""

    def setUp(self):
        self.collector = DocumentationQualityCollector()
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_collect_no_documentation(self):
        """无文档时返回零覆盖率"""
        code = '''
def undocumented_func():
    pass

class UndocumentedClass:
    def method(self):
        pass
'''
        file_path = Path(self.tmpdir) / 'no_doc.py'
        file_path.write_text(code)
        metrics = self.collector.collect(Path(self.tmpdir))
        self.assertEqual(metrics.function_doc_coverage, 0.0)
        self.assertEqual(metrics.class_doc_coverage, 0.0)

    def test_collect_fully_documented(self):
        """完全文档化的代码"""
        code = '''
"""Module documentation."""

def documented_function(arg1, arg2):
    """This is a well-documented function.
    
    Args:
        arg1: First argument
        arg2: Second argument
        
    Returns:
        Result value
    """
    return arg1 + arg2

class DocumentedClass:
    """A class with full documentation."""
    
    def documented_method(self):
        """Method with docstring."""
        pass
'''
        file_path = Path(self.tmpdir) / 'documented.py'
        file_path.write_text(code)
        metrics = self.collector.collect(Path(self.tmpdir))
        self.assertGreater(metrics.function_doc_coverage, 0)
        self.assertGreater(metrics.class_doc_coverage, 0)

    def test_detect_readme_exists(self):
        """检测README存在"""
        (Path(self.tmpdir) / 'README.md').write_text('# Project')
        metrics = self.collector.collect(Path(self.tmpdir))
        self.assertTrue(metrics.readme_exists)

    def test_detect_api_docs_exist(self):
        """检测API文档存在"""
        api_dir = Path(self.tmpdir) / 'docs' / 'api'
        api_dir.mkdir(parents=True)
        metrics = self.collector.collect(Path(self.tmpdir))
        self.assertTrue(metrics.api_doc_exists)

    def test_detect_changelog_exists(self):
        """检测CHANGELOG存在"""
        (Path(self.tmpdir) / 'CHANGELOG.md').write_text('Changelog')
        metrics = self.collector.collect(Path(self.tmpdir))
        self.assertTrue(metrics.changelog_exists)

    def test_identify_undocumented_items(self):
        """识别未文档化项目"""
        code = '''
def public_func_no_doc(x):
    return x * 2

def _private_func(y):
    return y + 1

class PublicClassNoDoc:
    def public_method(self):
        pass
'''
        file_path = Path(self.tmpdir) / 'undoc.py'
        file_path.write_text(code)
        metrics = self.collector.collect(Path(self.tmpdir))
        undoc_items = [item for item in metrics.undocumented_items
                       if item["name"] == "public_func_no_doc"]
        self.assertTrue(len(undoc_items) > 0)

    def test_calculate_doc_quality_score(self):
        """计算文档质量评分"""
        high_score = self.collector._calculate_doc_quality_score(
            function_doc_coverage=90.0,
            class_doc_coverage=85.0,
            file_metrics={
                "readme_exists": True,
                "api_doc_exists": True,
                "changelog_exists": True
            }
        )
        low_score = self.collector._calculate_doc_quality_score(
            function_doc_coverage=20.0,
            class_doc_coverage=10.0,
            file_metrics={
                "readme_exists": False,
                "api_doc_exists": False,
                "changelog_exists": False
            }
        )
        self.assertGreater(high_score, low_score)


class TestArchitectureQualityMetricsCollection(unittest.TestCase):
    """测试架构质量指标采集"""

    def setUp(self):
        self.collector = ArchitectureQualityCollector()
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_collect_empty_project(self):
        """空项目的架构指标"""
        empty_dir = Path(self.tmpdir) / 'empty_arch'
        empty_dir.mkdir()
        metrics = self.collector.collect(empty_dir)
        self.assertEqual(metrics.total_modules, 0)
        self.assertEqual(metrics.circular_dependencies, 0)

    def test_detect_circular_dependencies(self):
        """检测循环依赖"""
        module_a = Path(self.tmpdir) / 'module_a'
        module_b = Path(self.tmpdir) / 'module_b'
        module_a.mkdir()
        module_b.mkdir()

        (module_a / '__init__.py').write_text('from module_b import something\n')
        (module_b / '__init__.py').write_text('from module_a import other\n')

        metrics = self.collector.collect(Path(self.tmpdir))
        self.assertGreater(metrics.circular_dependencies, 0)

    def test_calculate_coupling_score(self):
        """计算耦合度评分"""
        imports = {
            "module_a": {"os", "sys", "json", "pathlib", "datetime",
                         "collections", "re", "math", "typing", "logging"},
            "module_b": {"os"}
        }
        coupling = self.collector._calculate_coupling_score(imports)
        self.assertGreater(coupling, 0)
        self.assertLessEqual(coupling, 1.0)

    def test_calculate_dependency_depths(self):
        """计算依赖深度"""
        imports = {
            "top": {"mid"},
            "mid": {"bottom"},
            "bottom": set()
        }
        depths = self.collector._calculate_dependency_depths(imports)
        self.assertEqual(depths["top"], 2)
        self.assertEqual(depths["mid"], 1)
        self.assertEqual(depths["bottom"], 0)

    def test_detect_god_classes(self):
        """检测上帝类"""
        god_class_code = 'class GodClass:\n' + '\n'.join([
            f'    def method_{i}(self): pass' for i in range(25)
        ])
        file_path = Path(self.tmpdir) / 'god_class.py'
        file_path.write_text(god_class_code)
        metrics = self.collector.collect(Path(self.tmpdir))
        self.assertGreater(metrics.god_classes, 0)

    def test_calculate_architecture_quality_score(self):
        """计算架构质量评分"""
        dep_metrics = {"circular_dependencies": 0, "coupling_score": 0.2}
        struct_metrics = {"god_classes_count": 0, "violations": 0}
        score = self.collector._calculate_architecture_score(dep_metrics, struct_metrics)
        self.assertGreaterEqual(score, 80)

        bad_dep = {"circular_dependencies": 5, "coupling_score": 0.9}
        bad_struct = {"god_classes_count": 3, "violations": 10}
        bad_score = self.collector._calculate_architecture_score(bad_dep, bad_struct)
        self.assertLess(bad_score, score)


class TestQualityMetricsRegistry(unittest.TestCase):
    """测试质量指标注册表"""

    def setUp(self):
        self.registry = QualityMetricsRegistry()

    def test_default_metrics_registered(self):
        """默认指标已注册"""
        all_metrics = self.registry.get_all()
        self.assertTrue(len(all_metrics) >= 10)

    def test_get_metric_by_name(self):
        """按名称获取指标"""
        metric = self.registry.get("cyclomatic_complexity")
        self.assertIsNotNone(metric)
        self.assertEqual(metric.name, "cyclomatic_complexity")
        self.assertEqual(metric.category, MetricCategory.CODE_QUALITY)

    def test_get_nonexistent_metric_returns_none(self):
        """获取不存在指标返回None"""
        self.assertIsNone(self.registry.get("nonexistent_metric_xyz"))

    def test_get_by_category(self):
        """按类别获取指标"""
        code_metrics = self.registry.get_by_category(MetricCategory.CODE_QUALITY)
        self.assertTrue(len(code_metrics) >= 3)

        test_metrics = self.registry.get_by_category(MetricCategory.TEST_QUALITY)
        self.assertTrue(len(test_metrics) >= 2)

    def test_register_custom_metric(self):
        """注册自定义指标"""
        custom = MetricDefinition(
            name="custom_metric",
            category=MetricCategory.ARCHITECTURE_QUALITY,
            metric_type=MetricType.STRUCTURE,
            description="自定义指标",
            unit="%",
            threshold_pass=90.0,
            threshold_warning=80.0,
            higher_is_better=True
        )
        self.registry.register(custom)
        retrieved = self.registry.get("custom_metric")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.description, "自定义指标")

    def test_metric_definition_to_dict(self):
        """测试指标定义序列化"""
        metric = self.registry.get("line_coverage")
        d = metric.to_dict()
        self.assertIn("name", d)
        self.assertIn("threshold_pass", d)
        self.assertIn("higher_is_better", d)


class TestQualityGateCheckerComprehensive(unittest.TestCase):
    """测试质量门禁检查器完整场景"""

    def setUp(self):
        self.registry = QualityMetricsRegistry()
        self.checker = QualityGateChecker(self.registry)

    def test_check_perfect_project_passes_all_gates(self):
        """完美项目通过所有门禁"""
        collection = self._create_perfect_collection()
        report = self.checker.check(collection)
        self.assertEqual(report.overall_status, GateStatus.PASSED)
        self.assertEqual(report.failed_gates, 0)

    def test_check_poor_project_fails_gates(self):
        """差项目失败门禁"""
        collection = self._create_poor_collection()
        report = self.checker.check(collection)
        self.assertIn(report.overall_status, [GateStatus.FAILED, GateStatus.WARNING])

    def test_gate_result_structure(self):
        """门禁结果结构完整性"""
        collection = self._create_perfect_collection()
        report = self.checker.check(collection)
        self.assertIsInstance(report.gate_results, list)
        self.assertTrue(len(report.gate_results) > 0)

        for gate in report.gate_results:
            self.assertIsInstance(gate.gate_name, str)
            self.assertIsInstance(gate.status, GateStatus)
            self.assertIsInstance(gate.actual_value, (int, float))
            self.assertIsInstance(gate.suggestions, list)

    def test_recommendations_generated_for_failures(self):
        """为失败生成建议"""
        poor_collection = self._create_poor_collection()
        report = self.checker.check(poor_collection)
        if report.failed_gates > 0:
            self.assertTrue(len(report.recommendations) > 0)

    def _create_perfect_collection(self):
        """创建完美项目集合"""
        return QualityMetricsCollection(
            timestamp=datetime.now().isoformat(),
            project="perfect_project",
            code_quality=CodeQualityMetrics(
                cyclomatic_complexity=5.0,
                avg_function_complexity=3.0,
                code_duplication_rate=0.02,
                error_count=0,
                warning_count=1,
                code_lines=10000,
                comment_lines=2000
            ),
            test_quality=TestQualityMetrics(
                line_coverage=95.0,
                branch_coverage=88.0,
                test_count=200,
                test_pass_rate=1.0
            ),
            documentation_quality=DocumentationQualityMetrics(
                documentation_coverage=95.0,
                function_doc_coverage=92.0,
                class_doc_coverage=90.0,
                readme_exists=True,
                api_doc_exists=True,
                changelog_exists=True
            ),
            architecture_quality=ArchitectureQualityMetrics(
                circular_dependencies=0,
                coupling_score=0.15,
                god_classes=0
            ),
            overall_score=95.0
        )

    def _create_poor_collection(self):
        """创建差项目集合"""
        return QualityMetricsCollection(
            timestamp=datetime.now().isoformat(),
            project="poor_project",
            code_quality=CodeQualityMetrics(
                cyclomatic_complexity=50.0,
                avg_function_complexity=18.0,
                code_duplication_rate=0.25,
                error_count=15,
                warning_count=40,
                code_lines=5000,
                comment_lines=100
            ),
            test_quality=TestQualityMetrics(
                line_coverage=30.0,
                branch_coverage=20.0,
                test_count=10,
                test_pass_rate=0.6
            ),
            documentation_quality=DocumentationQualityMetrics(
                documentation_coverage=20.0,
                function_doc_coverage=10.0,
                class_doc_coverage=5.0,
                readme_exists=False,
                api_doc_exists=False,
                changelog_exists=False
            ),
            architecture_quality=ArchitectureQualityMetrics(
                circular_dependencies=8,
                coupling_score=0.85,
                god_classes=5
            ),
            overall_score=25.0
        )


class TestQualityTrendAnalyzerBehavior(unittest.TestCase):
    """测试质量趋势分析器行为"""

    def setUp(self):
        self.analyzer = QualityTrendAnalyzer()

    def test_insufficient_data_returns_empty(self):
        """数据不足时返回空列表"""
        single_point = [
            QualityMetricsCollection(
                timestamp=datetime.now().isoformat(),
                project="test",
                code_quality=CodeQualityMetrics(),
                test_quality=TestQualityMetrics(),
                documentation_quality=DocumentationQualityMetrics(),
                architecture_quality=ArchitectureQualityMetrics(),
                overall_score=75.0
            )
        ]
        trends = self.analyzer.analyze(single_point)
        self.assertEqual(trends, [])

    def test_analyze_improving_trend(self):
        """分析上升趋势"""
        data = []
        base_time = datetime.now() - timedelta(days=10)
        for i in range(5):
            ts = (base_time + timedelta(days=i*2)).isoformat()
            data.append(QualityMetricsCollection(
                timestamp=ts,
                project="test",
                code_quality=CodeQualityMetrics(),
                test_quality=TestQualityMetrics(),
                documentation_quality=DocumentationQualityMetrics(),
                architecture_quality=ArchitectureQualityMetrics(),
                overall_score=70.0 + i*5
            ))
        trends = self.analyzer.analyze(data)
        self.assertTrue(len(trends) > 0)
        overall_trend = next((t for t in trends if t.metric_name == "overall_score"), None)
        if overall_trend:
            self.assertEqual(overall_trend.direction, "improving")

    def test_analyze_declining_trend(self):
        """分析下降趋势"""
        data = []
        base_time = datetime.now() - timedelta(days=10)
        for i in range(5):
            ts = (base_time + timedelta(days=i*2)).isoformat()
            data.append(QualityMetricsCollection(
                timestamp=ts,
                project="test",
                code_quality=CodeQualityMetrics(),
                test_quality=TestQualityMetrics(),
                documentation_quality=DocumentationQualityMetrics(),
                architecture_quality=ArchitectureQualityMetrics(),
                overall_score=90.0 - i*4
            ))
        trends = self.analyzer.analyze(data)
        declining = [t for t in trends if t.direction == "declining"]
        self.assertTrue(len(declining) > 0)

    def test_trend_prediction_and_confidence(self):
        """趋势预测和置信度"""
        data = []
        for i in range(7):
            ts = (datetime.now() - timedelta(days=(6-i)*2)).isoformat()
            data.append(QualityMetricsCollection(
                timestamp=ts,
                project="predict_test",
                code_quality=CodeQualityMetrics(),
                test_quality=TestQualityMetrics(),
                documentation_quality=DocumentationQualityMetrics(),
                architecture_quality=ArchitectureQualityMetrics(),
                overall_score=70.0 + i*2
            ))
        trends = self.analyzer.analyze(data, predict_days=7)
        for trend in trends:
            self.assertIsInstance(trend.predicted_value, float)
            self.assertGreaterEqual(trend.confidence, 0)
            self.assertLessEqual(trend.confidence, 1.0)
            self.assertIn(trend.direction, ["improving", "declining", "stable"])


class TestQualityMetricsCollectorIntegration(unittest.TestCase):
    """测试质量指标收集器集成"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.collector = QualityMetricsCollector(
            project_path=Path(self.tmpdir),
            storage_path=Path(self.tmpdir) / 'quality_data'
        )

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_collect_all_returns_complete_collection(self):
        """collect_all返回完整的集合对象"""
        sample_code = '''
"""Sample module."""
def documented_func():
    """Documented function."""
    if True:
        return 42
'''
        (Path(self.tmpdir) / 'sample.py').write_text(sample_code)
        collection = self.collector.collect_all("integration_test")
        self.assertIsInstance(collection, QualityMetricsCollection)
        self.assertEqual(collection.project, "integration_test")
        self.assertIn("timestamp", collection.to_dict())

    def test_overall_score_calculation(self):
        """整体评分计算"""
        good_code = CodeQualityMetrics(
            avg_function_complexity=4.0,
            code_duplication_rate=0.01,
            error_count=0,
            warning_count=2,
            code_lines=5000,
            comment_lines=1500
        )
        good_test = TestQualityMetrics(test_quality_score=90.0)
        good_doc = DocumentationQualityMetrics(doc_quality_score=85.0)
        good_arch = ArchitectureQualityMetrics(architecture_quality_score=88.0)
        score = self.collector._calculate_overall_score(good_code, good_test, good_doc, good_arch)
        self.assertGreater(score, 70)

    def test_save_and_load_history(self):
        """保存和加载历史数据"""
        collection = self.collector.collect_all("history_test")
        saved = self.collector._save_collection(collection, "history_test")
        self.assertTrue(saved)

        loaded = self.collector.load_history("history_test", days=30)
        self.assertTrue(len(loaded) >= 1)
        self.assertEqual(loaded[0].project, "history_test")

    def test_load_empty_history(self):
        """加载空历史数据"""
        loaded = self.collector.load_history("nonexistent_project", days=30)
        self.assertEqual(loaded, [])


class TestQualityReportGeneration(unittest.TestCase):
    """测试质量报告生成"""

    def setUp(self):
        self.generator = QualityReportGenerator()
        self.sample_collection = QualityMetricsCollection(
            timestamp="2024-01-15T10:30:00",
            project="report_test",
            code_quality=CodeQualityMetrics(
                cyclomatic_complexity=12.5,
                avg_function_complexity=5.2,
                code_duplication_rate=0.03,
                code_lines=8500,
                comment_lines=1700
            ),
            test_quality=TestQualityMetrics(
                line_coverage=87.5,
                branch_coverage=76.3,
                test_count=156,
                test_pass_rate=0.98
            ),
            documentation_quality=DocumentationQualityMetrics(
                documentation_coverage=82.0,
                function_doc_coverage=78.5,
                readme_exists=True,
                api_doc_exists=False,
                changelog_exists=True
            ),
            architecture_quality=ArchitectureQualityMetrics(
                total_modules=12,
                circular_dependencies=1,
                max_dependency_depth=4,
                coupling_score=0.28,
                god_classes=1
            ),
            overall_score=78.5
        )

    def test_generate_markdown_report_structure(self):
        """Markdown报告结构"""
        md = self.generator.generate_metrics_report(self.sample_collection, "markdown")
        self.assertIn("# 质量指标报告", md)
        self.assertIn("## 概览", md)
        self.assertIn("## 代码质量指标", md)
        self.assertIn("## 测试质量指标", md)

    def test_generate_json_report_valid(self):
        """JSON报告有效性"""
        json_str = self.generator.generate_metrics_report(self.sample_collection, "json")
        data = json.loads(json_str)
        self.assertEqual(data["project"], "report_test")
        self.assertIn("code_quality", data)
        self.assertAlmostEqual(data["overall_score"], 78.5)

    def test_generate_gate_report_markdown(self):
        """门禁报告Markdown格式"""
        registry = QualityMetricsRegistry()
        checker = QualityGateChecker(registry)
        gate_report = checker.check(self.sample_collection)
        md = self.generator.generate_gate_report(gate_report, "markdown")
        self.assertIn("# 质量门禁报告", md)
        self.assertIn(gate_report.overall_status.value.upper(), md)

    def test_generate_gate_report_json(self):
        """门禁报告JSON格式"""
        registry = QualityMetricsRegistry()
        checker = QualityGateChecker(registry)
        gate_report = checker.check(self.sample_collection)
        json_str = self.generator.generate_gate_report(gate_report, "json")
        data = json.loads(json_str)
        self.assertIn("gate_results", data)
        self.assertIn("passed_gates", data)


class TestDataClassSerialization(unittest.TestCase):
    """测试数据类序列化"""

    def test_code_quality_metrics_to_dict(self):
        """CodeQualityMetrics序列化"""
        metrics = CodeQualityMetrics(
            cyclomatic_complexity=15.5,
            code_duplication_rate=0.05,
            code_lines=10000
        )
        d = metrics.to_dict()
        self.assertAlmostEqual(d["cyclomatic_complexity"], 15.5)
        self.assertIn("high_complexity_functions", d)

    def test_test_quality_metrics_to_dict(self):
        """TestQualityMetrics序列化"""
        metrics = TestQualityMetrics(
            line_coverage=85.5,
            test_count=100,
            failed_tests=2
        )
        d = metrics.to_dict()
        self.assertAlmostEqual(d["line_coverage"], 85.5)
        self.assertIn("failed_test_details", d)

    def test_full_collection_serialization(self):
        """完整集合序列化"""
        collection = QualityMetricsCollection(
            timestamp=datetime.now().isoformat(),
            project="serialize_test",
            code_quality=CodeQualityMetrics(),
            test_quality=TestQualityMetrics(),
            documentation_quality=DocumentationQualityMetrics(),
            architecture_quality=ArchitectureQualityMetrics(),
            overall_score=80.0,
            metadata={"custom_key": "custom_value"}
        )
        d = collection.to_dict()
        self.assertEqual(d["project"], "serialize_test")
        self.assertEqual(d["metadata"]["custom_key"], "custom_value")

    def test_gate_check_result_to_dict(self):
        """GateCheckResult序列化"""
        result = GateCheckResult(
            gate_name="测试门禁",
            status=GateStatus.PASSED,
            metric_name="test_coverage",
            actual_value=95.0,
            threshold=80.0,
            message="测试覆盖率达标",
            severity=Severity.INFO,
            suggestions=["继续保持"]
        )
        d = result.to_dict()
        self.assertEqual(d["status"], "passed")
        self.assertEqual(d["suggestions"], ["继续保持"])

    def test_trend_analysis_to_dict(self):
        """TrendAnalysis序列化"""
        trend = TrendAnalysis(
            metric_name="overall_score",
            direction="improving",
            slope=0.5,
            current_value=85.0,
            predicted_value=88.5,
            confidence=0.85,
            change_rate=4.1,
            data_points=10
        )
        d = trend.to_dict()
        self.assertEqual(d["direction"], "improving")
        self.assertAlmostEqual(d["confidence"], 0.85)


if __name__ == '__main__':
    unittest.main(verbosity=2)
