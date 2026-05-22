"""
优化器功能测试示例

演示如何使用增强的性能优化器、代码质量优化器和架构优化器
"""

from pathlib import Path
from optimization.performance_optimizer_enhanced import UnifiedPerformanceOptimizer
from optimization.code_quality_optimizer_enhanced import UnifiedCodeQualityOptimizer
from optimization.architecture_optimizer_enhanced import UnifiedArchitectureOptimizer
from skillscripts.core.path_config_center import get_path_config


def test_performance_optimizer():
    print("=" * 60)
    print("测试性能优化器")
    print("=" * 60)

    project_path = get_path_config().SKILL_ROOT

    optimizer = UnifiedPerformanceOptimizer(project_path)

    report = optimizer.run_full_optimization(auto_apply=False, max_optimizations=5)

    print(f"\n优化周期 ID: {report['cycle_id']}")
    print(f"发现瓶颈数: {report['bottlenecks_found']}")
    print(f"生成建议数: {report['suggestions_generated']}")
    print(f"执行优化数: {report['optimizations_executed']}")
    print(f"成功优化数: {report['successful_optimizations']}")

    if report['bottlenecks']:
        print("\n前 3 个性能瓶颈:")
        for i, bottleneck in enumerate(report['bottlenecks'][:3], 1):
            print(f"  {i}. {bottleneck['description']}")
            print(f"     类型: {bottleneck['type']}")
            print(f"     影响分数: {bottleneck['impact_score']}")

    print("\n性能优化器测试完成！\n")


def test_code_quality_optimizer():
    print("=" * 60)
    print("测试代码质量优化器")
    print("=" * 60)

    project_path = get_path_config().SKILL_ROOT

    optimizer = UnifiedCodeQualityOptimizer(project_path)

    report = optimizer.run_full_optimization_cycle(auto_apply=False, max_refactorings=5)

    print(f"\n优化周期 ID: {report['cycle_id']}")
    print(f"发现复杂度问题数: {report['complexity_issues_found']}")
    print(f"发现重复问题数: {report['duplication_issues_found']}")
    print(f"生成重构建议数: {report['refactorings_suggested']}")
    print(f"执行重构数: {report['refactorings_executed']}")
    print(f"成功重构数: {report['successful_refactorings']}")

    if report['complexity_issues']:
        print("\n前 3 个复杂度问题:")
        for i, issue in enumerate(report['complexity_issues'][:3], 1):
            print(f"  {i}. {issue['function']} - {issue['type']}")
            print(f"     复杂度值: {issue['value']}")
            print(f"     级别: {issue['level']}")

    complexity_metrics = optimizer.complexity_analyzer.get_complexity_metrics()
    print(f"\n复杂度指标统计: {len(complexity_metrics)} 个文件")

    duplication_stats = optimizer.duplication_detector.get_duplication_stats()
    print(f"重复代码统计: {duplication_stats}")

    print("\n代码质量优化器测试完成！\n")


def test_architecture_optimizer():
    print("=" * 60)
    print("测试架构优化器")
    print("=" * 60)

    project_path = get_path_config().SKILL_ROOT

    optimizer = UnifiedArchitectureOptimizer(project_path)

    report = optimizer.run_full_optimization_cycle(auto_apply=False, max_optimizations=5)

    print(f"\n优化周期 ID: {report['cycle_id']}")
    print(f"分析依赖数: {report['dependencies_analyzed']}")
    print(f"发现问题数: {report['issues_found']}")
    print(f"生成建议数: {report['suggestions_generated']}")
    print(f"执行优化数: {report['optimizations_executed']}")
    print(f"成功优化数: {report['successful_optimizations']}")

    if report['issues']:
        print("\n前 3 个架构问题:")
        for i, issue in enumerate(report['issues'][:3], 1):
            print(f"  {i}. {issue['description']}")
            print(f"     类型: {issue['type']}")
            print(f"     严重性: {issue['severity']}")

    dependency_metrics = report.get('dependency_metrics', {})
    print(f"\n依赖指标统计: {len(dependency_metrics)} 个模块")

    critical_modules = report.get('critical_modules', [])
    if critical_modules:
        print(f"\n关键模块 (前 3 个):")
        for module, metrics in critical_modules[:3]:
            print(f"  - {module}: 总耦合度 {metrics['total_coupling']}")

    dependency_graph = report.get('dependency_graph', {})
    print(f"\n依赖图统计:")
    print(f"  模块数: {dependency_graph.get('total_modules', 0)}")
    print(f"  依赖数: {dependency_graph.get('total_dependencies', 0)}")

    print("\n架构优化器测试完成！\n")


def test_all_optimizers():
    print("\n" + "=" * 60)
    print("开始测试所有优化器")
    print("=" * 60 + "\n")

    test_performance_optimizer()
    test_code_quality_optimizer()
    test_architecture_optimizer()

    print("=" * 60)
    print("所有优化器测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    test_all_optimizers()
