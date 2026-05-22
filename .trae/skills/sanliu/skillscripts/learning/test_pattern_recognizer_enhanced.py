#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强模式识别器测试 - Enhanced Pattern Recognizer Test

测试增强的模式识别功能。
"""

import sys
import tempfile
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(get_path_config().SKILL_ROOT))

from pattern_recognizer import (
    PatternRecognizer,
    PatternType,
    PatternConfidence
)


def test_success_pattern_correlations():
    """测试成功模式关联分析"""
    print("\n=== 测试成功模式关联分析 ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        recognizer = PatternRecognizer(storage_path=str(Path(tmpdir) / "patterns.json"))
        
        execution_data1 = {
            "status": "success",
            "success_rate": 0.95,
            "quality_score": 0.9,
            "performance_score": 0.85,
            "code": "def test_function():\n    return True",
            "file_path": "test1.py",
            "execution_time": 0.5
        }
        
        execution_data2 = {
            "status": "success",
            "success_rate": 0.92,
            "quality_score": 0.88,
            "performance_score": 0.82,
            "code": "def another_function():\n    return False",
            "file_path": "test2.py",
            "execution_time": 0.6
        }
        
        pattern1 = recognizer.recognize_success_pattern(execution_data1)
        pattern2 = recognizer.recognize_success_pattern(execution_data2)
        
        if pattern1 and pattern2:
            correlations = recognizer.analyze_success_pattern_correlations(pattern1.pattern_id)
            print(f"✓ 模式关联分析完成")
            print(f"  - 总关联数: {correlations.get('total_correlations', 0)}")
            print(f"  - 关联强度: {correlations.get('correlation_strength', 'none')}")
        else:
            print("✗ 模式识别失败")


def test_success_probability_prediction():
    """测试成功概率预测"""
    print("\n=== 测试成功概率预测 ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        recognizer = PatternRecognizer(storage_path=str(Path(tmpdir) / "patterns.json"))
        
        for i in range(3):
            execution_data = {
                "status": "success",
                "success_rate": 0.9 + i * 0.02,
                "quality_score": 0.85 + i * 0.03,
                "code": f"def function_{i}():\n    return {i}",
                "file_path": f"test_{i}.py",
                "execution_time": 0.5 + i * 0.1
            }
            recognizer.recognize_success_pattern(execution_data)
        
        context = {
            "code": "def new_function():\n    return True",
            "file_path": "new_test.py",
            "execution_time": 0.55
        }
        
        prediction = recognizer.predict_success_probability(context)
        
        print(f"✓ 成功概率预测完成")
        print(f"  - 成功概率: {prediction['success_probability']:.2%}")
        print(f"  - 置信度: {prediction['confidence']:.2%}")
        print(f"  - 适用模式数: {len(prediction['applicable_patterns'])}")
        if prediction['recommendations']:
            print(f"  - 建议: {prediction['recommendations'][0]}")


def test_failure_root_cause_analysis():
    """测试失败根因分析"""
    print("\n=== 测试失败根因分析 ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        recognizer = PatternRecognizer(storage_path=str(Path(tmpdir) / "patterns.json"))
        
        execution_data = {
            "status": "failed",
            "failure_rate": 0.95,
            "error_info": {
                "type": "ValueError",
                "message": "Invalid value provided",
                "severity": "high"
            },
            "code": "def failing_function():\n    raise ValueError('Invalid value')",
            "file_path": "failing_test.py"
        }
        
        error_info = execution_data["error_info"]
        
        pattern = recognizer.recognize_failure_pattern(execution_data, error_info)
        
        if pattern:
            root_cause = recognizer.analyze_failure_root_cause(pattern.pattern_id)
            
            print(f"✓ 根因分析完成")
            print(f"  - 根本原因数: {len(root_cause.get('root_causes', []))}")
            if root_cause.get('primary_cause'):
                print(f"  - 主要原因: {root_cause['primary_cause'].get('description', 'N/A')}")
            if root_cause.get('remediation_suggestions'):
                print(f"  - 修复建议: {root_cause['remediation_suggestions'][0]}")
        else:
            print("✗ 失败模式识别失败")


def test_failure_warning():
    """测试失败预警"""
    print("\n=== 测试失败预警 ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        recognizer = PatternRecognizer(storage_path=str(Path(tmpdir) / "patterns.json"))
        
        for i in range(2):
            execution_data = {
                "status": "failed",
                "failure_rate": 0.9,
                "error_info": {
                    "type": "ConnectionError",
                    "message": f"Connection timeout {i}",
                    "severity": "high"
                },
                "code": f"def network_call_{i}():\n    pass",
                "file_path": f"network_{i}.py"
            }
            recognizer.recognize_failure_pattern(execution_data, execution_data["error_info"])
        
        context = {
            "code": "def new_network_call():\n    pass",
            "file_path": "new_network.py",
            "environment": "production"
        }
        
        warning = recognizer.generate_failure_warning(context, warning_threshold=0.5)
        
        print(f"✓ 失败预警完成")
        print(f"  - 是否有预警: {warning['has_warnings']}")
        print(f"  - 预警数量: {warning['warning_count']}")
        print(f"  - 整体风险: {warning['overall_risk']}")
        if warning['recommended_actions']:
            print(f"  - 推荐行动: {warning['recommended_actions'][0]}")


def test_optimization_effect_evaluation():
    """测试优化效果评估"""
    print("\n=== 测试优化效果评估 ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        recognizer = PatternRecognizer(storage_path=str(Path(tmpdir) / "patterns.json"))
        
        before_data = {
            "execution_time": 3.0,
            "memory_usage": 200.0,
            "quality_score": 0.5,
            "code_coverage": 0.4
        }
        
        after_data = {
            "execution_time": 1.0,
            "memory_usage": 100.0,
            "quality_score": 0.9,
            "code_coverage": 0.85
        }
        
        pattern = recognizer.recognize_optimization_pattern(before_data, after_data, "performance")
        
        if pattern:
            evaluation = recognizer.evaluate_optimization_effect(
                pattern.pattern_id, before_data, after_data
            )
            
            print(f"✓ 优化效果评估完成")
            print(f"  - 整体改进: {evaluation['overall_improvement']:.2%}")
            print(f"  - 有效性分数: {evaluation['effectiveness_score']:.2f}")
            print(f"  - 适用性分数: {evaluation['applicability_score']:.2f}")
            
            if evaluation['metrics']:
                metric_name = list(evaluation['metrics'].keys())[0]
                metric_data = evaluation['metrics'][metric_name]
                print(f"  - {metric_name} 改进: {metric_data.get('improvement_percentage', 'N/A')}")
        else:
            print("✗ 优化模式识别失败")


def test_optimization_scenario_analysis():
    """测试优化场景分析"""
    print("\n=== 测试优化场景分析 ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        recognizer = PatternRecognizer(storage_path=str(Path(tmpdir) / "patterns.json"))
        
        before_data = {
            "execution_time": 4.0,
            "performance": 40.0
        }
        
        after_data = {
            "execution_time": 1.5,
            "performance": 90.0
        }
        
        pattern = recognizer.recognize_optimization_pattern(before_data, after_data, "performance")
        
        if pattern:
            context = {
                "project_type": "web_application",
                "technology_stack": ["python", "flask", "postgresql"]
            }
            
            scenario = recognizer.analyze_optimization_scenarios(pattern.pattern_id, context)
            
            print(f"✓ 场景分析完成")
            print(f"  - 场景匹配分数: {scenario['scenario_match_score']:.2f}")
            print(f"  - 适用场景数: {len(scenario['applicable_scenarios'])}")
            print(f"  - 实施复杂度: {scenario['implementation_complexity']}")
            print(f"  - 整体风险: {scenario['risk_assessment']['overall_risk']}")
        else:
            print("✗ 优化模式识别失败")


def test_confidence_with_decay():
    """测试带衰减的置信度评估"""
    print("\n=== 测试带衰减的置信度评估 ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        recognizer = PatternRecognizer(storage_path=str(Path(tmpdir) / "patterns.json"))
        
        execution_data = {
            "status": "success",
            "success_rate": 0.9,
            "quality_score": 0.85,
            "code": "def test():\n    pass",
            "file_path": "test.py"
        }
        
        pattern = recognizer.recognize_success_pattern(execution_data)
        
        if pattern:
            confidence_eval = recognizer.evaluate_confidence_with_decay(
                pattern.pattern_id, decay_rate=0.1, time_horizon_days=30
            )
            
            print(f"✓ 置信度衰减评估完成")
            print(f"  - 基础置信度: {confidence_eval['base_confidence']:.2f}")
            print(f"  - 衰减后置信度: {confidence_eval['decayed_confidence']:.2f}")
            print(f"  - 调整后置信度: {confidence_eval['adjusted_confidence']:.2f}")
            print(f"  - 模式年龄: {confidence_eval['age_days']} 天")
            print(f"  - 建议: {confidence_eval['recommendation']}")
        else:
            print("✗ 模式识别失败")


def test_dynamic_confidence_adjustment():
    """测试动态置信度调整"""
    print("\n=== 测试动态置信度调整 ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        recognizer = PatternRecognizer(storage_path=str(Path(tmpdir) / "patterns.json"))
        
        execution_data = {
            "status": "success",
            "success_rate": 0.85,
            "quality_score": 0.8,
            "code": "def test():\n    pass",
            "file_path": "test.py"
        }
        
        pattern = recognizer.recognize_success_pattern(execution_data)
        
        if pattern:
            initial_confidence = pattern.confidence_score
            
            positive_feedback = {
                "type": "positive",
                "score": 0.9,
                "weight": 1.0
            }
            
            result = recognizer.dynamic_confidence_adjustment(pattern.pattern_id, positive_feedback)
            
            print(f"✓ 动态置信度调整完成")
            print(f"  - 初始置信度: {initial_confidence:.2f}")
            print(f"  - 调整后置信度: {result['new_confidence']:.2f}")
            print(f"  - 调整幅度: {result['adjustment']:+.3f}")
            print(f"  - 调整方向: {result['adjustment_direction']}")
            print(f"  - 置信度级别: {result['confidence_level']}")
        else:
            print("✗ 模式识别失败")


def test_all_basic_functions():
    """测试所有基础功能"""
    print("\n=== 测试所有基础功能 ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        recognizer = PatternRecognizer(storage_path=str(Path(tmpdir) / "patterns.json"))
        
        success_data = {
            "status": "success",
            "success_rate": 0.95,
            "code": "def success():\n    return True",
            "file_path": "success.py"
        }
        success_pattern = recognizer.recognize_success_pattern(success_data)
        print(f"✓ 成功模式识别: {success_pattern is not None}")
        
        failure_data = {
            "status": "failed",
            "failure_rate": 0.9,
            "error_info": {"type": "Error", "message": "Test error"},
            "code": "def failure():\n    raise Error()",
            "file_path": "failure.py"
        }
        failure_pattern = recognizer.recognize_failure_pattern(
            failure_data, failure_data["error_info"]
        )
        print(f"✓ 失败模式识别: {failure_pattern is not None}")
        
        before = {"execution_time": 3.0, "quality_score": 0.5}
        after = {"execution_time": 1.0, "quality_score": 0.9}
        opt_pattern = recognizer.recognize_optimization_pattern(before, after, "general")
        print(f"✓ 优化模式识别: {opt_pattern is not None}")
        
        if success_pattern:
            confidence, score = recognizer.evaluate_pattern_confidence(success_pattern.pattern_id)
            print(f"✓ 置信度评估: {confidence.value}, 分数: {score:.2f}")
        
        stats = recognizer.get_statistics()
        print(f"✓ 统计信息: 总模式数 {stats['total_patterns']}")


def main():
    """主测试函数"""
    print("=" * 60)
    print("增强模式识别器功能测试")
    print("=" * 60)
    
    try:
        test_all_basic_functions()
        test_success_pattern_correlations()
        test_success_probability_prediction()
        test_failure_root_cause_analysis()
        test_failure_warning()
        test_optimization_effect_evaluation()
        test_optimization_scenario_analysis()
        test_confidence_with_decay()
        test_dynamic_confidence_adjustment()
        
        print("\n" + "=" * 60)
        print("✓ 所有测试完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
from skillscripts.core.path_config_center import get_path_config
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
