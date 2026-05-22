#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
闭环机制集成测试 - Closed-Loop Integration Test

验证三省六部技能项目的完整闭环机制功能。
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(get_path_config().SKILL_ROOT))

from pipeline.closed_loop_verifier import (
    ClosedLoopVerifier,
    LoopStage,
    LoopStatus,
    RequirementTracer,
    QualityGateValidator,
    DeliverableChecker
)
from test.failure_pattern_learner import FailurePatternLearner
from utils.version_manager import (
from skillscripts.core.path_config_center import get_path_config
    VersionManager,
    VersionConfig,
    VersionPart,
    ReleaseType
)


def test_requirement_tracer():
    """测试需求追溯功能"""
    print("\n=== 测试需求追溯功能 ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        base_path = Path(tmpdir)
        
        tracer = RequirementTracer(base_path)
        
        trace = tracer.add_requirement("REQ-001", "用户登录功能")
        print("  ✓ 添加需求: REQ-001")
        
        tracer.link_design("REQ-001", "docs/design/login.md")
        tracer.link_code("REQ-001", "src/auth/login.py")
        tracer.link_test("REQ-001", "tests/test_login.py")
        tracer.link_deployment("REQ-001", "deploy-v1.0.0")
        print("  ✓ 链接设计、代码、测试、部署成功")
        
        matrix = tracer.get_trace_matrix()
        assert matrix.total_requirements == 1
        assert matrix.traced_requirements == 1
        assert matrix.coverage_score == 1.0
        print(f"  ✓ 追溯矩阵: 覆盖率 {matrix.coverage_score:.0%}")
        
        passed, issues = tracer.validate_traceability()
        assert passed
        print("  ✓ 追溯验证通过")
        
    return True


def test_quality_gate_validator():
    """测试质量门禁验证功能"""
    print("\n=== 测试质量门禁验证功能 ===")
    
    validator = QualityGateValidator()
    
    gates = validator.get_all_gates_report()
    assert gates["total_gates"] > 0
    print(f"  ✓ 初始化了 {gates['total_gates']} 个质量门禁")
    
    gate = validator.evaluate_gate("GATE-development-code_coverage", 0.85)
    assert gate.passed
    assert gate.actual_value == 0.0
    print(f"  ✓ 代码覆盖率门禁通过 (85% >= 80%)")
    
    gate = validator.evaluate_gate("GATE-testing-test_pass_rate", 0.95)
    assert not gate.passed
    print(f"  ✓ 测试通过率门禁未通过 (95% < 100%)")
    
    stage_status = validator.get_stage_gate_status(LoopStage.DEVELOPMENT)
    assert "status" in stage_status
    print(f"  ✓ 开发阶段门禁状态: {stage_status['status']}")
    
    return True


def test_deliverable_checker():
    """测试交付物完整性检查功能"""
    print("\n=== 测试交付物完整性检查功能 ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        base_path = Path(tmpdir)
        
        src_dir = base_path / "src"
        src_dir.mkdir()
        (src_dir / "main.py").write_text("def main(): pass\n")
        
        test_dir = base_path / "tests"
        test_dir.mkdir()
        (test_dir / "test_main.py").write_text("def test_main(): pass\n")
        
        checker = DeliverableChecker(base_path)
        
        status = checker.get_deliverable_status(LoopStage.DEVELOPMENT)
        print(f"  ✓ 开发阶段交付物检查完成")
        print(f"    - 必需交付物: {status['required_total']}")
        print(f"    - 存在的交付物: {status['required_exists']}")
        
        report = checker.get_all_deliverables_report()
        print(f"  ✓ 总交付物: {report['total_deliverables']}")
        print(f"  ✓ 存在的交付物: {report['existing_deliverables']}")
        
    return True


def test_closed_loop_verifier():
    """测试完整闭环验证功能"""
    print("\n=== 测试完整闭环验证功能 ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        base_path = Path(tmpdir)
        
        docs_dir = base_path / "docs" / "reports"
        docs_dir.mkdir(parents=True)
        
        src_dir = base_path / "backend" / "app"
        src_dir.mkdir(parents=True)
        (src_dir / "main.py").write_text("def main(): pass\n")
        
        test_dir = base_path / "backend" / "tests"
        test_dir.mkdir(parents=True)
        (test_dir / "test_main.py").write_text("def test_main(): pass\n")
        
        verifier = ClosedLoopVerifier(str(base_path))
        
        context = {
            "requirement": {
                "title": "测试需求",
                "description": "这是一个测试需求",
                "acceptance_criteria": ["功能正常", "性能达标"]
            },
            "design": {
                "架构设计": "微服务架构",
                "数据模型": "关系型数据库",
                "接口设计": "RESTful API",
                "安全设计": "JWT认证"
            },
            "test_results": {
                "total": 10,
                "passed": 10,
                "failed": 0
            },
            "development_metrics": {
                "code_coverage": 0.85,
                "static_analysis": 1.0,
                "code_review": 1.0
            },
            "test_metrics": {
                "test_pass_rate": 1.0,
                "defect_fix_rate": 1.0,
                "performance": 0.95
            }
        }
        
        report = verifier.run_full_loop(context)
        
        assert report.report_id.startswith("CLR-")
        print(f"  ✓ 闭环验证报告ID: {report.report_id}")
        
        print(f"  ✓ 质量评分: {report.quality_score:.1%}")
        print(f"  ✓ 状态: {report.iteration.status.value}")
        print(f"  ✓ 检查点: {report.summary['passed_checkpoints']}/{report.summary['total_checkpoints']}")
        print(f"  ✓ 问题: {report.summary['total_issues']} (自动修复: {report.summary['auto_fixed_issues']})")
        
    return True


def test_failure_pattern_learner():
    """测试失败模式学习功能"""
    print("\n=== 测试失败模式学习功能 ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_dir = Path(tmpdir) / "failure_history"
        knowledge_dir = Path(tmpdir) / "failure_knowledge"
        
        learner = FailurePatternLearner(storage_dir, knowledge_dir)
        
        record_id = learner.collector.collect(
            test_name="test_user_login",
            failure_type="failure",
            error_message="AssertionError: Expected True, got False",
            exception_type="AssertionError",
            source="test"
        )
        assert record_id is not None
        print("  ✓ 收集失败记录成功")
        
        result = learner.learn_from_history()
        print(f"  ✓ 学习完成: 分析 {result.get('records_analyzed', 0)} 条记录")
        
        diagnosis = learner.apply_to_diagnosis(
            "TypeError: unsupported operand type(s) for +: 'int' and 'str'"
        )
        print(f"  ✓ 诊断结果: {diagnosis.get('status', 'unknown')}")
        
        best_practices = learner.get_best_practices()
        print(f"  ✓ 最佳实践数量: {len(best_practices)}")
        
        fix_result = learner.learn_fix_patterns()
        print(f"  ✓ 修复模式学习: {fix_result.get('learned_patterns_count', 0)} 个模式")
        
    return True


def test_version_manager():
    """测试版本管理功能"""
    print("\n=== 测试版本管理功能 ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        base_path = Path(tmpdir)
        version_file = base_path / "version.json"
        changelog_file = base_path / "CHANGELOG.md"
        
        config = VersionConfig(
            version_file=version_file,
            changelog_file=changelog_file
        )
        
        manager = VersionManager(config)
        
        current = manager.get_current_version()
        print(f"  ✓ 当前版本: {current}")
        
        new_version = manager.bump_version(VersionPart.MINOR, "添加新功能")
        print(f"  ✓ 版本更新: {current} -> {new_version}")
        
        plan = manager.create_release_plan(
            version="1.1.0",
            release_type=ReleaseType.MINOR,
            target_date=datetime.now(),
            features=["新功能A", "新功能B"]
        )
        print(f"  ✓ 创建发布计划: {plan.version}")
        
        lifecycle = manager.start_lifecycle("1.1.0")
        print(f"  ✓ 开始生命周期: {lifecycle.version}")
        
        health = manager.check_version_health()
        print(f"  ✓ 版本健康检查: {len(health['active_versions'])} 个活跃版本")
        
        upcoming = manager.get_upcoming_releases(30)
        print(f"  ✓ 即将发布: {len(upcoming)} 个版本")
        
    return True


def test_integration():
    """测试完整集成流程"""
    print("\n=== 测试完整集成流程 ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        base_path = Path(tmpdir)
        
        docs_dir = base_path / "docs" / "reports"
        docs_dir.mkdir(parents=True)
        
        src_dir = base_path / "backend" / "app"
        src_dir.mkdir(parents=True)
        (src_dir / "main.py").write_text("# REQ-001: 主程序\ndef main(): pass\n")
        
        test_dir = base_path / "backend" / "tests"
        test_dir.mkdir(parents=True)
        (test_dir / "test_main.py").write_text("def test_main(): pass\n")
        
        print("  1. 初始化组件...")
        verifier = ClosedLoopVerifier(str(base_path))
        
        storage_dir = base_path / "failure_history"
        knowledge_dir = base_path / "failure_knowledge"
        learner = FailurePatternLearner(storage_dir, knowledge_dir)
        
        version_file = base_path / "version.json"
        changelog_file = base_path / "CHANGELOG.md"
        config = VersionConfig(version_file=version_file, changelog_file=changelog_file)
        version_manager = VersionManager(config)
        
        print("  2. 添加需求追溯...")
        verifier.add_requirement_trace("REQ-001", "主程序功能")
        verifier.link_requirement_to_code("REQ-001", "backend/app/main.py")
        verifier.link_requirement_to_test("REQ-001", "backend/tests/test_main.py")
        
        print("  3. 评估质量门禁...")
        verifier.evaluate_quality_gate("GATE-development-code_coverage", 0.85)
        verifier.evaluate_quality_gate("GATE-testing-test_pass_rate", 1.0)
        
        print("  4. 检查交付物...")
        deliverables = verifier.check_deliverables(LoopStage.DEVELOPMENT)
        print(f"     开发阶段交付物完整性: {deliverables['completeness']:.0%}")
        
        print("  5. 运行闭环验证...")
        context = {
            "requirement": {"title": "测试", "description": "测试", "acceptance_criteria": ["通过"]},
            "design": {"架构设计": "测试", "数据模型": "测试", "接口设计": "测试", "安全设计": "测试"},
            "test_results": {"total": 5, "passed": 5, "failed": 0},
            "development_metrics": {"code_coverage": 0.85, "static_analysis": 1.0, "code_review": 1.0},
            "test_metrics": {"test_pass_rate": 1.0, "defect_fix_rate": 1.0, "performance": 0.95}
        }
        report = verifier.run_full_loop_with_trace(context)
        print(f"     质量评分: {report.quality_score:.1%}")
        
        print("  6. 学习失败模式...")
        learner.collector.collect(
            test_name="test_integration",
            failure_type="failure",
            error_message="Integration test failed",
            source="integration_test"
        )
        learner.learn_from_history()
        best_practices = learner.get_best_practices()
        print(f"     最佳实践: {len(best_practices)} 个")
        
        print("  7. 版本管理...")
        current = version_manager.get_current_version()
        print(f"     当前版本: {current}")
        
        print("\n  ✓ 完整集成流程测试通过")
        
    return True


def main():
    """运行所有测试"""
    print("=" * 60)
    print("三省六部技能项目 - 闭环机制集成测试")
    print("=" * 60)
    
    tests = [
        ("需求追溯功能", test_requirement_tracer),
        ("质量门禁验证功能", test_quality_gate_validator),
        ("交付物完整性检查功能", test_deliverable_checker),
        ("完整闭环验证功能", test_closed_loop_verifier),
        ("失败模式学习功能", test_failure_pattern_learner),
        ("版本管理功能", test_version_manager),
        ("完整集成流程", test_integration),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success, None))
        except Exception as e:
            results.append((name, False, str(e)))
            print(f"  ✗ 测试失败: {e}")
    
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    for name, success, error in results:
        status = "✓ 通过" if success else "✗ 失败"
        print(f"  {status}: {name}")
        if error:
            print(f"         错误: {error}")
    
    print(f"\n总计: {passed}/{total} 通过")
    print("=" * 60)
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
