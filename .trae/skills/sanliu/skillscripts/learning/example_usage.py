#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动学习系统使用示例

演示如何使用自动学习系统的各个组件。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(get_path_config().SKILL_ROOT))

from learning import (
from skillscripts.core.path_config_center import get_path_config
    AutoLearner,
    PatternRecognizer,
    PatternType,
    PatternConfidence,
    BestPracticeExtractor,
    KnowledgeUpdater,
    KnowledgeCategory,
    UpdateStrategy,
    KnowledgeApplicationEngine,
    ApplicationContext,
    LearningMode,
    FeedbackType
)


def example_pattern_recognition():
    """模式识别示例"""
    print("\n" + "="*60)
    print("模式识别示例")
    print("="*60)
    
    recognizer = PatternRecognizer()
    
    success_data = {
        "status": "success",
        "success_rate": 0.95,
        "quality_score": 0.88,
        "performance_score": 0.92,
        "code": "def example_function():\n    return True",
        "file_path": "example.py",
        "execution_time": 0.5,
        "metrics": {
            "success_count": 95,
            "total_count": 100
        }
    }
    
    context = {
        "project": "example_project",
        "environment": "production"
    }
    
    pattern = recognizer.recognize_success_pattern(success_data, context)
    
    if pattern:
        print(f"\n识别到成功模式:")
        print(f"  - 模式ID: {pattern.pattern_id}")
        print(f"  - 名称: {pattern.name}")
        print(f"  - 置信度: {pattern.confidence.value}")
        print(f"  - 置信度分数: {pattern.confidence_score:.2f}")
        print(f"  - 出现次数: {pattern.occurrences}")
    
    failure_data = {
        "status": "failed",
        "errors": [
            {"type": "ValueError", "message": "Invalid input"}
        ]
    }
    
    error_info = {
        "type": "ValueError",
        "message": "Invalid input: expected int but got str",
        "severity": "medium"
    }
    
    failure_pattern = recognizer.recognize_failure_pattern(
        failure_data,
        error_info,
        context
    )
    
    if failure_pattern:
        print(f"\n识别到失败模式:")
        print(f"  - 模式ID: {failure_pattern.pattern_id}")
        print(f"  - 名称: {failure_pattern.name}")
        print(f"  - 描述: {failure_pattern.description}")
    
    before_data = {
        "performance": 100,
        "quality_score": 0.7,
        "execution_time": 2.5
    }
    
    after_data = {
        "performance": 150,
        "quality_score": 0.85,
        "execution_time": 1.8
    }
    
    opt_pattern = recognizer.recognize_optimization_pattern(
        before_data,
        after_data,
        "performance"
    )
    
    if opt_pattern:
        print(f"\n识别到优化模式:")
        print(f"  - 模式ID: {opt_pattern.pattern_id}")
        print(f"  - 名称: {opt_pattern.name}")
        print(f"  - 描述: {opt_pattern.description}")
    
    stats = recognizer.get_statistics()
    print(f"\n模式识别统计:")
    print(f"  - 总模式数: {stats['total_patterns']}")
    print(f"  - 按类型: {stats['by_type']}")
    print(f"  - 按置信度: {stats['by_confidence']}")


def example_best_practice_extraction():
    """最佳实践提取示例"""
    print("\n" + "="*60)
    print("最佳实践提取示例")
    print("="*60)
    
    recognizer = PatternRecognizer()
    extractor = BestPracticeExtractor(pattern_recognizer=recognizer)
    
    for i in range(5):
        success_data = {
            "status": "success",
            "success_rate": 0.9 + i * 0.02,
            "quality_score": 0.85,
            "code": f"def function_{i}():\n    return True",
            "file_path": f"module_{i}.py"
        }
        
        recognizer.recognize_success_pattern(success_data)
    
    patterns = recognizer.get_patterns_by_type(
        PatternType.SUCCESS,
        min_confidence=PatternConfidence.HIGH
    )
    
    if patterns:
        pattern = patterns[0]
        
        code_analysis = {
            "complexity": 8,
            "test_coverage": 85,
            "documentation": 0.9
        }
        
        practice = extractor.extract_code_practice(pattern, code_analysis)
        
        if practice:
            print(f"\n提取的代码最佳实践:")
            print(f"  - 实践ID: {practice.practice_id}")
            print(f"  - 标题: {practice.title}")
            print(f"  - 类别: {practice.category.value}")
            print(f"  - 质量: {practice.quality.value}")
            print(f"  - 质量分数: {practice.quality_score:.2f}")
            print(f"  - 收益: {', '.join(practice.benefits)}")
            print(f"  - 实施步骤数: {len(practice.implementation_steps)}")
    
    stats = extractor.get_statistics()
    print(f"\n最佳实践提取统计:")
    print(f"  - 总实践数: {stats['total_practices']}")
    print(f"  - 按类别: {stats['by_category']}")
    print(f"  - 已验证数: {stats['verified_count']}")


def example_knowledge_management():
    """知识管理示例"""
    print("\n" + "="*60)
    print("知识管理示例")
    print("="*60)
    
    updater = KnowledgeUpdater()
    
    knowledge_data = {
        "title": "Python代码优化最佳实践",
        "description": "使用列表推导式代替循环可以提高代码性能",
        "content": {
            "pattern": "list_comprehension",
            "example": "[x*2 for x in range(10)]",
            "benefits": ["性能提升", "代码简洁"],
            "use_cases": ["数据处理", "转换操作"]
        },
        "tags": ["python", "optimization", "performance"],
        "quality_score": 0.85,
        "application_count": 5,
        "success_rate": 0.9
    }
    
    entry = updater.add_knowledge(knowledge_data, auto_classify=True)
    
    print(f"\n添加的知识条目:")
    print(f"  - 条目ID: {entry.entry_id}")
    print(f"  - 标题: {entry.title}")
    print(f"  - 类别: {entry.category.value}")
    print(f"  - 质量: {entry.quality.value}")
    print(f"  - 版本: {entry.version}")
    
    similar_data = {
        "title": "Python代码优化最佳实践",
        "content": {
            "pattern": "list_comprehension",
            "example": "[x*2 for x in range(10)]"
        }
    }
    
    is_duplicate, duplicate_id = updater.deduplicate_knowledge(similar_data)
    print(f"\n去重检测: {'重复' if is_duplicate else '不重复'}")
    if is_duplicate:
        print(f"  - 重复条目ID: {duplicate_id}")
    
    updates = {
        "content": {
            "additional_tip": "避免在列表推导式中使用复杂表达式"
        },
        "tags": ["python", "optimization", "performance", "best-practice"]
    }
    
    updated_entry = updater.update_knowledge(
        entry.entry_id,
        updates,
        UpdateStrategy.VERSION
    )
    
    print(f"\n更新后的知识条目:")
    print(f"  - 版本: {updated_entry.version}")
    print(f"  - 标签数: {len(updated_entry.tags)}")
    
    search_results = updater.search_knowledge("Python", limit=5)
    print(f"\n搜索结果 (查询: 'Python'):")
    for entry, score in search_results:
        print(f"  - {entry.title} (相关度: {score:.2f})")
    
    stats = updater.get_statistics()
    print(f"\n知识管理统计:")
    print(f"  - 总条目数: {stats['total_entries']}")
    print(f"  - 按类别: {stats['by_category']}")
    print(f"  - 平均质量分数: {stats['avg_quality_score']:.2f}")


def example_knowledge_application():
    """知识应用示例"""
    print("\n" + "="*60)
    print("知识应用示例")
    print("="*60)
    
    updater = KnowledgeUpdater()
    
    for i in range(3):
        updater.add_knowledge({
            "title": f"最佳实践 {i+1}",
            "description": f"示例最佳实践 {i+1}",
            "content": {
                "pattern": f"pattern_{i}",
                "benefits": [f"benefit_{i}"]
            },
            "tags": ["python", "testing"],
            "quality_score": 0.8 + i * 0.05,
            "success_rate": 0.85
        })
    
    engine = KnowledgeApplicationEngine(knowledge_updater=updater)
    
    context = ApplicationContext(
        context_id="ctx-001",
        project_type="web_application",
        technology_stack=["python", "django", "postgresql"],
        current_state={
            "performance": 75,
            "quality_score": 0.7
        },
        objectives=["improve_performance", "increase_quality"],
        constraints=["maintain_backward_compatibility"]
    )
    
    suggestions = engine.generate_suggestions(context, max_suggestions=3)
    
    print(f"\n生成的应用建议:")
    for suggestion in suggestions:
        print(f"\n  建议 {suggestion.priority}:")
        print(f"    - ID: {suggestion.suggestion_id}")
        print(f"    - 标题: {suggestion.title}")
        print(f"    - 相关性分数: {suggestion.relevance_score:.2f}")
        print(f"    - 适用性分数: {suggestion.applicability_score:.2f}")
        print(f"    - 预期收益: {', '.join(suggestion.expected_benefits[:2])}")
        print(f"    - 潜在风险: {', '.join(suggestion.potential_risks[:2])}")
    
    if suggestions:
        suggestion = suggestions[0]
        
        metrics_before = {
            "performance": 75,
            "quality_score": 0.7,
            "test_coverage": 70
        }
        
        metrics_after = {
            "performance": 85,
            "quality_score": 0.82,
            "test_coverage": 85
        }
        
        result = engine.track_application_effect(
            suggestion.suggestion_id,
            metrics_before,
            metrics_after
        )
        
        print(f"\n应用结果:")
        print(f"  - 结果ID: {result.result_id}")
        print(f"  - 状态: {result.status.value}")
        print(f"  - 有效性分数: {result.effectiveness_score:.2f}")
        print(f"  - 改进: {result.improvements}")
        
        feedback = engine.collect_feedback(
            knowledge_id=suggestion.knowledge_id,
            result_id=result.result_id,
            feedback_type=FeedbackType.POSITIVE,
            rating=4,
            comment="应用效果良好，性能显著提升",
            suggested_improvements=["可以添加更多示例"]
        )
        
        print(f"\n反馈收集:")
        print(f"  - 反馈ID: {feedback.feedback_id}")
        print(f"  - 类型: {feedback.feedback_type.value}")
        print(f"  - 评分: {feedback.rating}/5")
    
    stats = engine.get_statistics()
    print(f"\n知识应用统计:")
    print(f"  - 总建议数: {stats['total_suggestions']}")
    print(f"  - 总结果数: {stats['total_results']}")
    print(f"  - 成功应用数: {stats['successful_applications']}")
    print(f"  - 平均有效性: {stats['avg_effectiveness']:.2f}")


def example_auto_learner():
    """自动学习主控制器示例"""
    print("\n" + "="*60)
    print("自动学习主控制器示例")
    print("="*60)
    
    learner = AutoLearner(learning_mode=LearningMode.ACTIVE)
    
    print(f"\n初始状态:")
    status = learner.get_status()
    print(f"  - 学习模式: {status['learning_mode']}")
    print(f"  - 状态: {status['status']}")
    
    execution_data = {
        "status": "success",
        "success_rate": 0.92,
        "quality_score": 0.88,
        "code": "def optimized_function():\n    return [x*2 for x in range(100)]",
        "file_path": "optimized.py",
        "execution_time": 0.3,
        "code_analysis": {
            "complexity": 5,
            "test_coverage": 90
        }
    }
    
    result = learner.learn_from_execution(execution_data)
    
    print(f"\n学习结果:")
    print(f"  - 状态: {result['status']}")
    print(f"  - 识别的模式数: {len(result['patterns'])}")
    print(f"  - 提取的实践数: {len(result['practices'])}")
    print(f"  - 更新的知识数: {len(result['knowledge'])}")
    
    before_data = {
        "performance": 100,
        "quality_score": 0.75,
        "execution_time": 2.0
    }
    
    after_data = {
        "performance": 180,
        "quality_score": 0.92,
        "execution_time": 1.2
    }
    
    opt_result = learner.learn_from_optimization(
        before_data,
        after_data,
        "performance_optimization"
    )
    
    print(f"\n优化学习结果:")
    print(f"  - 状态: {opt_result['status']}")
    print(f"  - 识别的模式数: {len(opt_result['patterns'])}")
    
    context = ApplicationContext(
        context_id="ctx-002",
        project_type="api_service",
        technology_stack=["python", "fastapi", "redis"],
        current_state={
            "response_time": 200,
            "throughput": 1000
        },
        objectives=["reduce_response_time", "increase_throughput"],
        constraints=["no_downtime"]
    )
    
    app_result = learner.apply_knowledge(context)
    
    print(f"\n知识应用结果:")
    print(f"  - 状态: {app_result['status']}")
    print(f"  - 建议数: {len(app_result['suggestions'])}")
    
    report = learner.generate_learning_report(period_days=7)
    
    print(f"\n学习报告:")
    print(f"  - 报告ID: {report.report_id}")
    print(f"  - 周期: {report.period_start.date()} 至 {report.period_end.date()}")
    print(f"  - 识别的模式数: {report.patterns_recognized}")
    print(f"  - 提取的实践数: {report.practices_extracted}")
    print(f"  - 更新的知识数: {report.knowledge_updated}")
    print(f"  - 有效性分数: {report.effectiveness_score:.2f}")
    print(f"\n  建议:")
    for i, rec in enumerate(report.recommendations, 1):
        print(f"    {i}. {rec}")
    
    learner.set_learning_mode(LearningMode.AGGRESSIVE)
    print(f"\n学习模式已切换为: {learner._learning_mode.value}")


def main():
    """主函数"""
    print("\n" + "="*60)
    print("三省六部技能 - 自动学习系统示例")
    print("="*60)
    
    example_pattern_recognition()
    example_best_practice_extraction()
    example_knowledge_management()
    example_knowledge_application()
    example_auto_learner()
    
    print("\n" + "="*60)
    print("示例运行完成")
    print("="*60)


if __name__ == "__main__":
    main()
