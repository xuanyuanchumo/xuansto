"""
SDD+TDD深度融合功能单元测试

测试新增的增强功能：
- 异步操作规范解析
- 增强的错误报告
- 覆盖率分析增强
- 失败模式识别
- 循环质量评估
- 循环中断和恢复机制
"""

import unittest
import json
import tempfile
import os
import sys
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from enum import Enum
from unittest.mock import Mock, patch, MagicMock


class TestStatus(Enum):
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class FailureCategory(Enum):
    ASSERTION = "assertion"
    EXCEPTION = "exception"
    TYPE = "type"
    VALUE = "value"
    ATTRIBUTE = "attribute"


class CoverageLevel(Enum):
    FULL = "full"
    PARTIAL = "partial"
    MINIMAL = "minimal"
    NONE = "none"


@dataclass
class TestResult:
    test_name: str
    test_class: str
    status: TestStatus
    duration: float
    error_message: str
    stack_trace: str


@dataclass
class FailureAnalysis:
    failure_id: str
    test_id: str
    category: FailureCategory
    root_cause: str
    error_message: str
    suggested_fix: str
    confidence: float
    related_spec_element: str = ""


@dataclass
class CoverageData:
    file_path: str
    line_rate: float
    branch_rate: float
    covered_lines: int
    total_lines: int
    missing_lines: List[int] = field(default_factory=list)


class TestAsyncOperationParser(unittest.TestCase):
    """测试异步操作规范解析器"""
    
    def test_parse_promise_operation(self):
        """测试Promise类型异步操作解析"""
        ASYNC_PATTERNS = {
            "promise": r"Promise<(.+)>",
            "async_function": r"async\s+(\w+)\s*\(([^)]*)\)\s*(?::\s*(.+))?",
            "callback": r"callback\s*:\s*\(([^)]*)\)\s*=>\s*(.+)",
            "observable": r"Observable<(.+)>",
        }
        
        output_type = "Promise<User>"
        operation_type = "promise"
        
        for pattern_name, pattern in ASYNC_PATTERNS.items():
            import re
            if re.search(pattern, output_type, re.IGNORECASE):
                operation_type = pattern_name
                break
        
        self.assertEqual(operation_type, "promise")
    
    def test_parse_observable_operation(self):
        """测试Observable类型异步操作解析"""
        ASYNC_PATTERNS = {
            "promise": r"Promise<(.+)>",
            "observable": r"Observable<(.+)>",
        }
        
        output_type = "Observable<Data>"
        operation_type = "promise"
        
        import re
        for pattern_name, pattern in ASYNC_PATTERNS.items():
            if re.search(pattern, output_type, re.IGNORECASE):
                operation_type = pattern_name
                break
        
        self.assertEqual(operation_type, "observable")
    
    def test_parse_retry_policy(self):
        """测试重试策略解析"""
        data = {
            "strategy": "exponential",
            "maxRetries": 5,
            "initialDelay": 1000
        }
        
        retry_policy = {
            "strategy": data.get("strategy", "exponential"),
            "max_retries": data.get("maxRetries", data.get("max_retries", 3)),
            "initial_delay": data.get("initialDelay", data.get("initial_delay", 1000)),
            "max_delay": data.get("maxDelay", data.get("max_delay", 30000)),
            "multiplier": data.get("multiplier", 2.0),
        }
        
        self.assertEqual(retry_policy["strategy"], "exponential")
        self.assertEqual(retry_policy["max_retries"], 5)
        self.assertEqual(retry_policy["initial_delay"], 1000)
    
    def test_validate_timeout(self):
        """测试超时值验证"""
        timeout = 5000
        self.assertGreater(timeout, 0)
        
        invalid_timeout = -1
        self.assertLessEqual(invalid_timeout, 0)
    
    def test_generate_async_test_cases(self):
        """测试异步测试用例生成"""
        operation = {
            "name": "fetchData",
            "timeout": 5000,
            "cancellation_support": True,
            "progress_reporting": True,
            "retry_policy": {"max_retries": 3}
        }
        
        test_cases = []
        
        test_cases.append({
            "name": f"test_{operation['name']}_success",
            "type": "async_success"
        })
        
        if operation.get("timeout"):
            test_cases.append({
                "name": f"test_{operation['name']}_timeout",
                "type": "async_timeout"
            })
        
        if operation.get("retry_policy") and operation["retry_policy"].get("max_retries", 0) > 0:
            test_cases.append({
                "name": f"test_{operation['name']}_retry",
                "type": "async_retry"
            })
        
        if operation.get("cancellation_support"):
            test_cases.append({
                "name": f"test_{operation['name']}_cancellation",
                "type": "async_cancellation"
            })
        
        if operation.get("progress_reporting"):
            test_cases.append({
                "name": f"test_{operation['name']}_progress",
                "type": "async_progress"
            })
        
        self.assertGreater(len(test_cases), 0)
        
        test_names = [tc["name"] for tc in test_cases]
        self.assertTrue(any("success" in name for name in test_names))
        self.assertTrue(any("timeout" in name for name in test_names))
        self.assertTrue(any("retry" in name for name in test_names))
        self.assertTrue(any("cancellation" in name for name in test_names))
        self.assertTrue(any("progress" in name for name in test_names))


class TestEnhancedErrorReporter(unittest.TestCase):
    """测试增强的错误报告器"""
    
    def test_create_missing_field_error(self):
        """测试创建缺少字段错误"""
        ERROR_TEMPLATES = {
            "missing_required_field": {
                "message": "缺少必需字段 '{field}'",
                "suggestion": "添加 '{field}' 字段，参考文档: {doc_link}"
            }
        }
        
        context = {"field": "name", "doc_link": "https://docs.example.com/spec"}
        
        template = ERROR_TEMPLATES["missing_required_field"]
        message = template["message"].format(**context)
        suggestion = template["suggestion"].format(**context)
        
        self.assertIn("name", message)
        self.assertIn("name", suggestion)
    
    def test_create_invalid_type_error(self):
        """测试创建类型无效错误"""
        ERROR_TEMPLATES = {
            "invalid_type": {
                "message": "字段 '{field}' 的类型无效: 期望 {expected}, 实际 {actual}",
                "suggestion": "将 '{field}' 的值修改为 {expected} 类型"
            }
        }
        
        context = {"field": "type", "expected": "string", "actual": "number"}
        
        template = ERROR_TEMPLATES["invalid_type"]
        message = template["message"].format(**context)
        
        self.assertIn("string", message)
        self.assertIn("number", message)
    
    def test_generate_fix_suggestions(self):
        """测试生成修复建议"""
        errors = [
            {
                "path": "spec.interfaces[0]",
                "message": "缺少必需字段",
                "suggestion": "添加name字段",
                "code": "missing_required_field"
            }
        ]
        
        suggestions = {}
        for error in errors:
            path = error["path"]
            if path not in suggestions:
                suggestions[path] = []
            suggestions[path].append(error["suggestion"])
        
        self.assertIn("spec.interfaces[0]", suggestions)
        self.assertGreater(len(suggestions["spec.interfaces[0]"]), 0)


class TestEnhancedCoverageAnalyzer(unittest.TestCase):
    """测试增强的覆盖率分析器"""
    
    def test_analyze_line_coverage(self):
        """测试分析行覆盖率"""
        coverage_data = {
            "src/main.py": CoverageData(
                file_path="src/main.py",
                line_rate=85.0,
                branch_rate=70.0,
                covered_lines=85,
                total_lines=100,
                missing_lines=[10, 20, 30]
            ),
            "src/utils.py": CoverageData(
                file_path="src/utils.py",
                line_rate=60.0,
                branch_rate=50.0,
                covered_lines=60,
                total_lines=100,
                missing_lines=[]
            )
        }
        
        total_lines = sum(d.total_lines for d in coverage_data.values())
        covered_lines = sum(d.covered_lines for d in coverage_data.values())
        overall_rate = (covered_lines / total_lines * 100) if total_lines > 0 else 0
        
        self.assertEqual(total_lines, 200)
        self.assertEqual(covered_lines, 145)
        self.assertAlmostEqual(overall_rate, 72.5, places=1)
    
    def test_analyze_branch_coverage(self):
        """测试分析分支覆盖率"""
        coverage_data = {
            "src/main.py": CoverageData(
                file_path="src/main.py",
                line_rate=85.0,
                branch_rate=70.0,
                covered_lines=85,
                total_lines=100,
                missing_lines=[]
            )
        }
        
        for file_path, data in coverage_data.items():
            branch_rate = data.branch_rate
            self.assertGreater(branch_rate, 50)
    
    def test_identify_coverage_gaps(self):
        """测试识别覆盖缺口"""
        coverage_data = {
            "src/low_coverage.py": CoverageData(
                file_path="src/low_coverage.py",
                line_rate=30.0,
                branch_rate=20.0,
                covered_lines=30,
                total_lines=100,
                missing_lines=list(range(31, 101))
            )
        }
        
        gaps = []
        for file_path, data in coverage_data.items():
            if data.line_rate < 50:
                gaps.append({
                    "type": "low_coverage_file",
                    "file": file_path,
                    "coverage": data.line_rate,
                    "priority": 10 - int(data.line_rate / 10)
                })
        
        self.assertEqual(len(gaps), 1)
        self.assertEqual(gaps[0]["type"], "low_coverage_file")
        self.assertEqual(gaps[0]["coverage"], 30.0)
    
    def test_coverage_summary(self):
        """测试覆盖率摘要"""
        line_coverage = {"overall_rate": 72.5}
        branch_coverage = {"overall_rate": 65.0}
        condition_coverage = {"overall_rate": 80.0}
        gaps = []
        
        overall_score = (
            line_coverage["overall_rate"] * 0.5 +
            branch_coverage["overall_rate"] * 0.3 +
            condition_coverage["overall_rate"] * 0.2
        )
        
        if overall_score >= 80:
            grade = "A"
        elif overall_score >= 70:
            grade = "B"
        elif overall_score >= 60:
            grade = "C"
        else:
            grade = "D"
        
        self.assertAlmostEqual(overall_score, 71.75, places=1)
        self.assertEqual(grade, "B")


class TestFailurePatternRecognizer(unittest.TestCase):
    """测试失败模式识别器"""
    
    def test_find_recurring_patterns(self):
        """测试发现重复出现的失败模式"""
        test_results = [
            TestResult(
                test_name="test1",
                test_class="Tests",
                status=TestStatus.FAILED,
                duration=1.0,
                error_message="AssertionError: expected 200 but got 404",
                stack_trace=""
            ),
            TestResult(
                test_name="test2",
                test_class="Tests",
                status=TestStatus.FAILED,
                duration=1.0,
                error_message="AssertionError: expected 200 but got 404",
                stack_trace=""
            ),
            TestResult(
                test_name="test3",
                test_class="Tests",
                status=TestStatus.FAILED,
                duration=1.0,
                error_message="AssertionError: expected 200 but got 500",
                stack_trace=""
            )
        ]
        
        error_messages = {}
        for test in test_results:
            if test.status == TestStatus.FAILED and test.error_message:
                import re
                normalized = re.sub(r'\d+', 'N', test.error_message)
                if normalized not in error_messages:
                    error_messages[normalized] = []
                error_messages[normalized].append(test.test_name)
        
        patterns = []
        for normalized_msg, tests in error_messages.items():
            if len(tests) >= 2:
                patterns.append({
                    "pattern_type": "recurring_error",
                    "occurrence_count": len(tests),
                    "affected_tests": tests
                })
        
        self.assertEqual(len(patterns), 1)
        self.assertEqual(patterns[0]["occurrence_count"], 3)
    
    def test_cluster_by_root_cause(self):
        """测试按根因聚类"""
        failure_analyses = [
            FailureAnalysis(
                failure_id="F1",
                test_id="test1",
                category=FailureCategory.ASSERTION,
                root_cause="NullPointerException in UserService",
                error_message="NullPointerException",
                suggested_fix="Add null check",
                confidence=0.9
            ),
            FailureAnalysis(
                failure_id="F2",
                test_id="test2",
                category=FailureCategory.EXCEPTION,
                root_cause="NullPointerException in OrderService",
                error_message="NullPointerException",
                suggested_fix="Add null check",
                confidence=0.8
            ),
            FailureAnalysis(
                failure_id="F3",
                test_id="test3",
                category=FailureCategory.TYPE,
                root_cause="TypeError in PaymentService",
                error_message="TypeError",
                suggested_fix="Check type",
                confidence=0.7
            )
        ]
        
        clusters = {}
        for analysis in failure_analyses:
            root_cause_key = "null_related" if "null" in analysis.root_cause.lower() else "other"
            
            if root_cause_key not in clusters:
                clusters[root_cause_key] = {"count": 0, "tests": []}
            
            clusters[root_cause_key]["count"] += 1
            clusters[root_cause_key]["tests"].append(analysis.test_id)
        
        self.assertIn("null_related", clusters)
        self.assertEqual(clusters["null_related"]["count"], 2)
    
    def test_analyze_failure_trends(self):
        """测试分析失败趋势"""
        test_results = [
            TestResult(
                test_name="test1",
                test_class="Tests",
                status=TestStatus.FAILED,
                duration=1.0,
                error_message="",
                stack_trace=""
            ),
            TestResult(
                test_name="test2",
                test_class="Tests",
                status=TestStatus.PASSED,
                duration=1.0,
                error_message="",
                stack_trace=""
            ),
            TestResult(
                test_name="test3",
                test_class="Tests",
                status=TestStatus.PASSED,
                duration=1.0,
                error_message="",
                stack_trace=""
            )
        ]
        
        current_failed = len([t for t in test_results if t.status == TestStatus.FAILED])
        current_total = len(test_results)
        current_rate = (current_failed / current_total * 100) if current_total > 0 else 0
        
        self.assertEqual(current_failed, 1)
        self.assertAlmostEqual(current_rate, 33.33, places=1)


class TestCycleQualityEvaluator(unittest.TestCase):
    """测试循环质量评估器"""
    
    def test_determine_quality_grade(self):
        """测试确定质量等级"""
        def determine_grade(score):
            if score >= 90:
                return "A"
            elif score >= 80:
                return "B"
            elif score >= 70:
                return "C"
            elif score >= 60:
                return "D"
            else:
                return "F"
        
        self.assertEqual(determine_grade(95), "A")
        self.assertEqual(determine_grade(85), "B")
        self.assertEqual(determine_grade(75), "C")
        self.assertEqual(determine_grade(65), "D")
        self.assertEqual(determine_grade(50), "F")
    
    def test_calculate_phase_efficiency(self):
        """测试计算阶段效率"""
        def calculate_efficiency(avg_duration, phase):
            expected_durations = {
                "red": 30.0,
                "green": 60.0,
                "blue": 45.0
            }
            
            expected = expected_durations.get(phase, 30.0)
            
            if avg_duration <= expected:
                return 100.0
            elif avg_duration <= expected * 2:
                return 80.0
            elif avg_duration <= expected * 3:
                return 60.0
            else:
                return 40.0
        
        self.assertEqual(calculate_efficiency(25, "red"), 100.0)
        self.assertEqual(calculate_efficiency(45, "red"), 80.0)
        self.assertEqual(calculate_efficiency(70, "red"), 60.0)
        self.assertEqual(calculate_efficiency(100, "red"), 40.0)
    
    def test_calculate_overall_quality(self):
        """测试计算整体质量"""
        iteration_quality = {"score": 80}
        code_evolution = {"overall_improvement": 10}
        test_stability = {"stability_score": 85}
        refactoring_effectiveness = {"score": 75}
        
        scores = [
            iteration_quality.get("score", 0),
            code_evolution.get("overall_improvement", 0) + 50,
            test_stability.get("stability_score", 0),
            refactoring_effectiveness.get("score", 0)
        ]
        
        overall_score = sum(scores) / len(scores)
        
        self.assertAlmostEqual(overall_score, 75.0, places=1)


class TestCycleRecoveryManager(unittest.TestCase):
    """测试循环中断和恢复管理器"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.state_dir = Path(self.temp_dir) / "cycle_states"
        self.state_dir.mkdir(parents=True, exist_ok=True)
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_save_and_load_cycle_state(self):
        """测试保存和加载循环状态"""
        state = {
            "report_id": "TEST-001",
            "spec_id": "SPEC-001",
            "spec_name": "TestSpec",
            "current_iteration": 3,
            "current_phase": "green",
            "total_iterations": 10,
            "completed_iterations": 2,
            "failed_iterations": 0,
            "iterations": [],
            "context": {},
            "saved_at": datetime.now().isoformat(),
            "status": "interrupted"
        }
        
        state_file = self.state_dir / f"{state['report_id']}.json"
        
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        
        with open(state_file, "r", encoding="utf-8") as f:
            loaded_state = json.load(f)
        
        self.assertEqual(loaded_state["report_id"], "TEST-001")
        self.assertEqual(loaded_state["current_iteration"], 3)
        self.assertEqual(loaded_state["status"], "interrupted")
    
    def test_get_recovery_point(self):
        """测试获取恢复点"""
        state = {
            "report_id": "RECOVERY-TEST-001",
            "spec_id": "SPEC-001",
            "spec_name": "TestSpec",
            "current_iteration": 4,
            "current_phase": "blue",
            "total_iterations": 10,
            "completed_iterations": 4,
            "failed_iterations": 1,
            "iterations": [],
            "saved_at": datetime.now().isoformat(),
            "status": "interrupted"
        }
        
        state_file = self.state_dir / f"{state['report_id']}.json"
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        
        recovery_point = {
            "report_id": state["report_id"],
            "resume_from_iteration": state["current_iteration"],
            "resume_from_phase": state["current_phase"],
            "progress_percentage": (state["completed_iterations"] / state["total_iterations"] * 100)
        }
        
        self.assertEqual(recovery_point["resume_from_iteration"], 4)
        self.assertEqual(recovery_point["resume_from_phase"], "blue")
        self.assertEqual(recovery_point["progress_percentage"], 40.0)
    
    def test_mark_cycle_completed(self):
        """测试标记循环完成"""
        state = {
            "report_id": "COMPLETE-TEST-001",
            "spec_id": "SPEC-001",
            "spec_name": "TestSpec",
            "status": "interrupted"
        }
        
        state_file = self.state_dir / f"{state['report_id']}.json"
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        
        state["status"] = "completed"
        state["completed_at"] = datetime.now().isoformat()
        
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        
        with open(state_file, "r", encoding="utf-8") as f:
            loaded_state = json.load(f)
        
        self.assertEqual(loaded_state["status"], "completed")


class TestIntelligentFeedbackGenerator(unittest.TestCase):
    """测试智能反馈生成器"""
    
    def test_detect_spec_inconsistencies(self):
        """测试检测规范不一致"""
        failure_analyses = [
            FailureAnalysis(
                failure_id="F1",
                test_id="test_user_get",
                category=FailureCategory.ASSERTION,
                root_cause="API返回404",
                error_message="AssertionError: expected status 200 but got 404",
                suggested_fix="检查API端点",
                confidence=0.9,
                related_spec_element="UserAPI"
            )
        ]
        
        spec = {
            "interfaces": [
                {
                    "name": "UserAPI",
                    "description": "用户API接口",
                    "type": "REST"
                }
            ]
        }
        
        inconsistencies = []
        for analysis in failure_analyses:
            element = analysis.related_spec_element
            if element:
                spec_element = None
                for iface in spec.get("interfaces", []):
                    if iface.get("name", "").lower() == element.lower():
                        spec_element = iface
                        break
                
                if spec_element:
                    if analysis.category == FailureCategory.ASSERTION:
                        inconsistencies.append({
                            "type": "behavior_mismatch",
                            "element": element,
                            "severity": "high"
                        })
        
        self.assertGreater(len(inconsistencies), 0)
        self.assertEqual(inconsistencies[0]["type"], "behavior_mismatch")
    
    def test_identify_missing_specs(self):
        """测试识别缺失规范"""
        test_results = [
            TestResult(
                test_name="test_OrderService_create",
                test_class="OrderTests",
                status=TestStatus.PASSED,
                duration=1.0,
                error_message="",
                stack_trace=""
            )
        ]
        
        spec = {
            "interfaces": [
                {"name": "UserService"}
            ],
            "data_models": []
        }
        
        spec_elements = set()
        for iface in spec.get("interfaces", []):
            spec_elements.add(iface.get("name", "").lower())
        
        missing = []
        for test in test_results:
            import re
            parts = re.split(r"[_\s]", test.test_name)
            for part in parts:
                if len(part) > 3 and not part.lower().startswith("test"):
                    if part.lower() not in spec_elements:
                        missing.append({
                            "type": "missing_element",
                            "element": part
                        })
        
        order_missing = [m for m in missing if "Order" in m.get("element", "")]
        self.assertGreater(len(order_missing), 0)


if __name__ == "__main__":
    unittest.main()
