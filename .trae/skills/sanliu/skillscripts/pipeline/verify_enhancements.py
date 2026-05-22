#!/usr/bin/env python3
"""
SDD+TDD增强功能验证脚本

验证新增的功能：
1. SDD规范解析器增强 - 规范验证、错误提示、多格式支持
2. TDD循环执行器优化 - 阶段切换、进度跟踪、执行报告
3. SDD-TDD集成增强 - 自动映射、反馈机制、覆盖率追踪
"""

import sys
import json
from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from enum import Enum

print("=" * 60)
print("SDD+TDD增强功能验证")
print("=" * 60)

test_results = {
    "timestamp": datetime.now().isoformat(),
    "tests": [],
    "passed": 0,
    "failed": 0,
    "total": 0
}

def run_test(name: str, test_func) -> bool:
    """运行单个测试"""
    test_results["total"] += 1
    try:
        test_func()
        test_results["passed"] += 1
        test_results["tests"].append({"name": name, "status": "passed"})
        print(f"  [PASS] {name}")
        return True
    except Exception as e:
        test_results["failed"] += 1
        test_results["tests"].append({"name": name, "status": "failed", "error": str(e)})
        print(f"  [FAIL] {name}: {e}")
        return False

print("\n[1] SDD规范解析器增强测试")
print("-" * 40)

def test_spec_format_validator():
    """测试规范格式验证器"""
    from sdd_spec_parser_enhanced import SpecFormatValidator
    
    validator = SpecFormatValidator()
    
    openapi_content = '{"openapi": "3.0.0", "info": {}, "paths": {}}'
    detected, confidence = validator.detect_format(openapi_content, "json")
    assert detected == "openapi", f"Expected openapi, got {detected}"
    assert confidence > 0.5, f"Confidence too low: {confidence}"
    
    sdd_content = '{"apiVersion": "v1", "kind": "EntitySpec", "metadata": {}, "spec": {}}'
    detected, confidence = validator.detect_format(sdd_content, "json")
    assert detected == "sdd", f"Expected sdd, got {detected}"
    
    print("    - 格式检测功能正常")

run_test("SpecFormatValidator", test_spec_format_validator)

def test_enhanced_validation():
    """测试增强的验证功能"""
    from sdd_spec_parser_enhanced import ValidationResult, ValidationSeverity
    
    result = ValidationResult(is_valid=True)
    
    result.add_error("test.path", "测试错误", "测试建议")
    assert not result.is_valid, "添加错误后应该无效"
    assert len(result.errors) == 1, "应该有一个错误"
    
    result.add_warning("test.path2", "测试警告")
    assert len(result.warnings) == 1, "应该有一个警告"
    
    summary = result.get_summary()
    assert "errors" in summary, "摘要应包含错误数"
    assert summary["errors"] == 1, "错误数应为1"
    
    print("    - 验证结果功能正常")

run_test("EnhancedValidation", test_enhanced_validation)

print("\n[2] TDD循环执行器优化测试")
print("-" * 40)

def test_cycle_phase_enum():
    """测试循环阶段枚举"""
    from tdd_blue_refactoring_pipeline import CyclePhase, PhaseStatus
    
    assert CyclePhase.RED.value == "red"
    assert CyclePhase.GREEN.value == "green"
    assert CyclePhase.BLUE.value == "blue"
    
    assert PhaseStatus.PENDING.value == "pending"
    assert PhaseStatus.COMPLETED.value == "completed"
    assert PhaseStatus.FAILED.value == "failed"
    
    print("    - 阶段枚举定义正确")

run_test("CyclePhaseEnum", test_cycle_phase_enum)

def test_phase_execution_record():
    """测试阶段执行记录"""
    from tdd_blue_refactoring_pipeline import PhaseExecutionRecord, CyclePhase, PhaseStatus
    
    record = PhaseExecutionRecord(
        phase=CyclePhase.RED,
        status=PhaseStatus.IN_PROGRESS,
        started_at=datetime.now().isoformat()
    )
    
    assert record.phase == CyclePhase.RED
    assert record.status == PhaseStatus.IN_PROGRESS
    assert record.test_passed == 0
    assert record.test_failed == 0
    
    record.test_passed = 5
    record.test_failed = 2
    assert record.test_passed == 5
    
    print("    - 阶段执行记录功能正常")

run_test("PhaseExecutionRecord", test_phase_execution_record)

def test_cycle_progress():
    """测试循环进度跟踪"""
    from tdd_blue_refactoring_pipeline import CycleProgress, CyclePhase
    
    progress = CycleProgress(
        current_phase=CyclePhase.RED,
        current_iteration=1,
        total_iterations=5,
        phase_progress=0.5,
        overall_progress=0.1
    )
    
    assert progress.current_phase == CyclePhase.RED
    assert progress.current_iteration == 1
    assert progress.total_iterations == 5
    assert progress.health_status == "healthy"
    
    print("    - 循环进度跟踪功能正常")

run_test("CycleProgress", test_cycle_progress)

def test_pipeline_result_enhanced():
    """测试增强的管道结果"""
    from tdd_blue_refactoring_pipeline import PipelineResult, CycleProgress, CyclePhase
    
    progress = CycleProgress(current_phase=CyclePhase.GREEN)
    result = PipelineResult(
        timestamp=datetime.now().isoformat(),
        project_root="/test",
        cycle_progress=progress
    )
    
    assert result.cycle_progress is not None
    assert result.cycle_progress.current_phase == CyclePhase.GREEN
    
    result_dict = result.to_dict()
    assert "cycle_progress" in result_dict
    assert result_dict["cycle_progress"]["current_phase"] == "green"
    
    print("    - 管道结果增强功能正常")

run_test("PipelineResultEnhanced", test_pipeline_result_enhanced)

print("\n[3] SDD-TDD集成增强测试")
print("-" * 40)

def test_spec_to_test_auto_mapper():
    """测试规范到测试用例的自动映射"""
    from sdd_tdd_integrator import SpecToTestAutoMapper, SpecElement, SpecElementType, GeneratedTestCase, TestType
    
    mapper = SpecToTestAutoMapper()
    
    element = SpecElement(
        name="UserService",
        element_type=SpecElementType.INTERFACE,
        description="用户服务接口"
    )
    
    test_cases = [
        GeneratedTestCase(
            test_id="TC-001",
            name="test_UserService_create",
            test_type=TestType.UNIT,
            spec_element_id="UserService",
            spec_element_name="UserService",
            arrange="准备用户数据",
            act="调用创建方法",
            assert_="验证创建成功"
        ),
        GeneratedTestCase(
            test_id="TC-002",
            name="test_UserService_delete",
            test_type=TestType.UNIT,
            spec_element_id="UserService",
            spec_element_name="UserService",
            arrange="准备用户ID",
            act="调用删除方法",
            assert_="验证删除成功"
        )
    ]
    
    mappings = mapper.auto_map(
        type('Spec', (), {'elements': [element]})(),
        test_cases
    )
    
    assert "UserService" in mappings
    assert len(mappings["UserService"]) >= 1
    
    print("    - 自动映射功能正常")

run_test("SpecToTestAutoMapper", test_spec_to_test_auto_mapper)

def test_semantic_analyzer():
    """测试语义分析器"""
    from sdd_tdd_integrator import SemanticAnalyzer
    
    analyzer = SemanticAnalyzer()
    
    similarity = analyzer.calculate_similarity(
        "UserService create user",
        "test UserService create"
    )
    
    assert similarity > 0, "相似度应该大于0"
    assert similarity <= 1, "相似度应该小于等于1"
    
    similarity2 = analyzer.calculate_similarity(
        "完全不同的文本内容",
        "totally different content"
    )
    
    assert similarity2 < similarity, "不相关文本相似度应该更低"
    
    print("    - 语义分析功能正常")

run_test("SemanticAnalyzer", test_semantic_analyzer)

def test_test_result_feedback_handler():
    """测试结果反馈处理器"""
    from sdd_tdd_integrator import TestResultFeedbackHandler
    
    handler = TestResultFeedbackHandler()
    
    feedback = handler.process_feedback(
        type('Spec', (), {'spec_id': 'TEST-001', 'elements': []})(),
        {"tests": {"TC-001": {"status": "passed"}, "TC-002": {"status": "failed", "error_message": "Assertion error"}}},
        {"Element1": ["TC-001", "TC-002"]}
    )
    
    assert "timestamp" in feedback
    assert feedback["total_tests"] == 2
    assert feedback["passed_tests"] == 1
    assert feedback["failed_tests"] == 1
    assert len(feedback["recommendations"]) > 0
    
    print("    - 反馈处理功能正常")

run_test("TestResultFeedbackHandler", test_test_result_feedback_handler)

def test_coverage_tracker():
    """测试覆盖率追踪器"""
    from sdd_tdd_integrator import CoverageTracker, SpecElement, SpecElementType
    
    tracker = CoverageTracker()
    
    element = SpecElement(
        name="TestElement",
        element_type=SpecElementType.INTERFACE,
        description="测试元素"
    )
    
    from sdd_tdd_integrator import GeneratedTestCase, TestType
    
    test_cases = [
        GeneratedTestCase(
            test_id="TC-001",
            name="test_TestElement",
            test_type=TestType.UNIT,
            spec_element_id="TestElement",
            spec_element_name="TestElement",
            arrange="准备",
            act="执行",
            assert_="验证"
        )
    ]
    
    coverage_report = tracker.track_coverage(
        type('Spec', (), {'spec_id': 'TEST-001', 'elements': [element]})(),
        test_cases
    )
    
    assert "overall_coverage" in coverage_report
    assert "element_coverage" in coverage_report
    assert "TestElement" in coverage_report["element_coverage"]
    
    print("    - 覆盖率追踪功能正常")

run_test("CoverageTracker", test_coverage_tracker)

print("\n" + "=" * 60)
print("测试结果汇总")
print("=" * 60)
print(f"总计: {test_results['total']}")
print(f"通过: {test_results['passed']}")
print(f"失败: {test_results['failed']}")
print(f"通过率: {test_results['passed'] / test_results['total'] * 100:.1f}%")

if test_results['failed'] == 0:
    print("\n✅ 所有测试通过!")
    sys.exit(0)
else:
    print("\n❌ 存在失败的测试")
    sys.exit(1)
