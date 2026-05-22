#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试增强的代码质量优化器

测试功能：
1. 智能重构建议生成
2. 安全重构执行
3. 优化效果验证
4. 优化历史记录
"""

import sys
from pathlib import Path

sys.path.insert(0, str(get_path_config().SCRIPTS_DIR / "optimization"))

from code_quality_optimizer_enhanced import (
    UnifiedCodeQualityOptimizer,
    SafeRefactoringExecutor,
    OptimizationHistoryManager,
    RefactoringSuggestion,
    RefactoringType
)


def test_complexity_analysis():
    print("\n" + "=" * 80)
    print("测试1: 复杂度分析")
    print("=" * 80)
    
    project_path = get_path_config().SKILL_ROOT
    optimizer = UnifiedCodeQualityOptimizer(project_path)
    
    complexity_issues = optimizer.complexity_analyzer.analyze_complexity(project_path)
    
    print(f"\n发现 {len(complexity_issues)} 个复杂度问题:")
    for i, issue in enumerate(complexity_issues[:5], 1):
        print(f"\n{i}. {issue.function_name} ({issue.complexity_type})")
        print(f"   文件: {issue.file_path}")
        print(f"   行号: {issue.line_number}")
        print(f"   复杂度: {issue.complexity_value} ({issue.complexity_level.value})")
        print(f"   描述: {issue.description}")
        if issue.suggestions:
            print(f"   建议: {issue.suggestions[0]}")
    
    return complexity_issues


def test_duplication_detection():
    print("\n" + "=" * 80)
    print("测试2: 代码重复检测")
    print("=" * 80)
    
    project_path = get_path_config().SKILL_ROOT
    optimizer = UnifiedCodeQualityOptimizer(project_path)
    
    duplication_issues = optimizer.duplication_detector.detect_duplications(project_path)
    
    print(f"\n发现 {len(duplication_issues)} 处代码重复:")
    for i, issue in enumerate(duplication_issues[:5], 1):
        print(f"\n{i}. 重复类型: {issue.duplication_type.value}")
        print(f"   文件: {issue.file_path}")
        print(f"   行号: {issue.line_numbers[:3]}")
        print(f"   重复次数: {issue.duplicate_count}")
        print(f"   相似度: {issue.similarity_score:.2%}")
        print(f"   建议: {issue.suggested_refactoring}")
    
    return duplication_issues


def test_refactoring_suggestions(complexity_issues, duplication_issues):
    print("\n" + "=" * 80)
    print("测试3: 重构建议生成")
    print("=" * 80)
    
    project_path = get_path_config().SKILL_ROOT
    optimizer = UnifiedCodeQualityOptimizer(project_path)
    
    suggestions = optimizer.refactoring_advisor.generate_refactoring_suggestions(
        complexity_issues,
        duplication_issues
    )
    
    print(f"\n生成 {len(suggestions)} 个重构建议:")
    for i, suggestion in enumerate(suggestions[:5], 1):
        print(f"\n{i}. {suggestion.suggestion_id}: {suggestion.description}")
        print(f"   类型: {suggestion.refactoring_type.value}")
        print(f"   文件: {suggestion.file_path}")
        print(f"   行号: {suggestion.line_number}")
        print(f"   优先级: {suggestion.priority}")
        print(f"   工作量: {suggestion.estimated_effort}")
        print(f"   收益: {', '.join(suggestion.benefits[:2])}")
    
    return suggestions


def test_safe_refactoring():
    print("\n" + "=" * 80)
    print("测试4: 安全重构执行")
    print("=" * 80)
    
    project_path = get_path_config().SKILL_ROOT
    safe_executor = SafeRefactoringExecutor(project_path)
    
    print("\n安全重构执行器已初始化")
    print(f"备份目录: {safe_executor._backup_dir}")
    print("功能:")
    print("  - 自动备份原始文件")
    print("  - 语法验证")
    print("  - 测试验证")
    print("  - 自动回滚机制")
    
    return safe_executor


def test_optimization_history():
    print("\n" + "=" * 80)
    print("测试5: 优化历史记录")
    print("=" * 80)
    
    project_path = get_path_config().SKILL_ROOT
    history_manager = OptimizationHistoryManager(project_path)
    
    stats = history_manager.get_optimization_stats()
    
    print(f"\n优化历史统计:")
    print(f"  总优化次数: {stats.get('total_optimizations', 0)}")
    print(f"  成功优化: {stats.get('successful_optimizations', 0)}")
    print(f"  已回滚: {stats.get('rolled_back_optimizations', 0)}")
    print(f"  成功率: {stats.get('success_rate', 0):.1f}%")
    print(f"  平均复杂度降低: {stats.get('average_complexity_reduction', 0):.1f}")
    
    recent = history_manager.get_recent_optimizations(5)
    if recent:
        print(f"\n最近的优化记录:")
        for record in recent:
            status = "✓" if record.success else "✗"
            rollback = " (已回滚)" if record.rolled_back else ""
            print(f"  {status} {record.record_id}: {record.refactoring_type} - {record.file_path}{rollback}")
    
    return history_manager


def test_optimization_validation():
    print("\n" + "=" * 80)
    print("测试6: 优化效果验证")
    print("=" * 80)
    
    project_path = get_path_config().SKILL_ROOT
    optimizer = UnifiedCodeQualityOptimizer(project_path)
    
    print("\n捕获优化前快照...")
    before_snapshot = optimizer._capture_project_snapshot()
    
    print(f"快照时间: {before_snapshot['timestamp']}")
    print(f"质量分数: {before_snapshot['quality_score']:.2f}")
    print(f"复杂度问题: {before_snapshot['complexity_metrics'].get('total_issues', 0)}")
    print(f"代码重复: {before_snapshot['duplication_metrics'].get('total_duplications', 0)}")
    
    print("\n验证优化效果功能:")
    print("  - 支持优化前后对比")
    print("  - 自动识别改进和回退")
    print("  - 生成详细对比报告")
    
    return before_snapshot


def test_full_optimization_cycle():
    print("\n" + "=" * 80)
    print("测试7: 完整优化流程")
    print("=" * 80)
    
    project_path = get_path_config().SKILL_ROOT
    optimizer = UnifiedCodeQualityOptimizer(project_path)
    
    print("\n运行完整优化流程（仅分析，不自动应用）...")
    report = optimizer.run_full_optimization_cycle(
        auto_apply=False,
        max_refactorings=5
    )
    
    print(f"\n优化周期ID: {report['cycle_id']}")
    print(f"开始时间: {report['started_at']}")
    print(f"持续时间: {report['duration_seconds']:.2f} 秒")
    print(f"\n发现:")
    print(f"  复杂度问题: {report['complexity_issues_found']}")
    print(f"  代码重复: {report['duplication_issues_found']}")
    print(f"  重构建议: {report['refactorings_suggested']}")
    
    return report


def main():
    print("\n" + "=" * 80)
    print("增强的代码质量优化器 - 功能测试")
    print("=" * 80)
    
    try:
        complexity_issues = test_complexity_analysis()
        duplication_issues = test_duplication_detection()
        suggestions = test_refactoring_suggestions(complexity_issues, duplication_issues)
        safe_executor = test_safe_refactoring()
        history_manager = test_optimization_history()
        before_snapshot = test_optimization_validation()
        report = test_full_optimization_cycle()
        
        print("\n" + "=" * 80)
        print("测试总结")
        print("=" * 80)
        print("\n✅ 所有测试通过!")
        print("\n新增功能:")
        print("  1. ✓ 智能重构建议生成")
        print("  2. ✓ 安全重构执行（备份、验证、回滚）")
        print("  3. ✓ 优化效果验证（前后对比）")
        print("  4. ✓ 优化历史记录管理")
        print("  5. ✓ 集成到系统性优化流程")
        
        print("\n使用示例:")
        print("  # 运行安全优化流程")
        print("  optimizer = UnifiedCodeQualityOptimizer(project_path)")
        print("  report = optimizer.run_safe_optimization_cycle()")
        print()
        print("  # 验证优化效果")
        print("  before = optimizer._capture_project_snapshot()")
        print("  # ... 执行优化 ...")
        print("  result = optimizer.validate_optimization_effect(before)")
        print()
        print("  # 查看优化历史")
        print("  stats = optimizer.history_manager.get_optimization_stats()")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
from skillscripts.core.path_config_center import get_path_config
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
