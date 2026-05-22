"""
优化系统使用示例

演示如何使用三省六部技能的自动优化能力
"""

from pathlib import Path
import json
from datetime import datetime

from .unified_optimization_manager import (
    UnifiedOptimizationManager,
    OptimizationConfig,
    OptimizationType,
    create_optimization_manager
)
from .performance_optimizer_enhanced import UnifiedPerformanceOptimizer
from .code_quality_optimizer_enhanced import UnifiedCodeQualityOptimizer
from .architecture_optimizer_enhanced import UnifiedArchitectureOptimizer
from .optimization_evaluation_system import UnifiedOptimizationEvaluator


def example_basic_usage():
    """基本使用示例"""
    print("=" * 80)
    print("基本使用示例")
    print("=" * 80)

    project_path = get_path_config().SKILL_ROOT

    manager = create_optimization_manager(
        project_path=project_path,
        auto_apply=False,
        max_optimizations=5,
        output_dir=project_path / "reports" / "optimization"
    )

    print("\n执行完整优化...")
    result = manager.run_optimization(OptimizationType.FULL)

    print(f"\n优化 ID: {result.optimization_id}")
    print(f"总体得分: {result.overall_score:.2f}")
    print(f"摘要: {result.summary}")

    print("\n建议:")
    for i, rec in enumerate(result.recommendations, 1):
        print(f"  {i}. {rec}")


def example_performance_optimization():
    """性能优化示例"""
    print("\n" + "=" * 80)
    print("性能优化示例")
    print("=" * 80)

    project_path = get_path_config().SKILL_ROOT

    optimizer = UnifiedPerformanceOptimizer(project_path)

    print("\n运行性能优化周期...")
    report = optimizer.run_full_optimization_cycle(
        auto_apply=False,
        max_optimizations=10
    )

    print(f"\n发现的瓶颈数: {report['bottlenecks_found']}")
    print(f"生成的建议数: {report['suggestions_generated']}")
    print(f"执行的优化数: {report['optimizations_executed']}")
    print(f"成功的优化数: {report['successful_optimizations']}")

    if report['bottlenecks']:
        print("\n前 5 个瓶颈:")
        for i, bottleneck in enumerate(report['bottlenecks'][:5], 1):
            print(f"  {i}. {bottleneck['type']}: {bottleneck['description']}")

    output_path = project_path / "reports" / "performance_optimization_report.json"
    optimizer.export_report(report, output_path)
    print(f"\n报告已导出到: {output_path}")


def example_code_quality_optimization():
    """代码质量优化示例"""
    print("\n" + "=" * 80)
    print("代码质量优化示例")
    print("=" * 80)

    project_path = get_path_config().SKILL_ROOT

    optimizer = UnifiedCodeQualityOptimizer(project_path)

    print("\n运行代码质量优化周期...")
    report = optimizer.run_full_optimization_cycle(
        auto_apply=False,
        max_refactorings=10
    )

    print(f"\n发现的复杂度问题数: {report['complexity_issues_found']}")
    print(f"发现的重复代码数: {report['duplication_issues_found']}")
    print(f"生成的重构建议数: {report['refactorings_suggested']}")
    print(f"执行的重构数: {report['refactorings_executed']}")
    print(f"成功的重构数: {report['successful_refactorings']}")

    if report['complexity_issues']:
        print("\n前 5 个复杂度问题:")
        for i, issue in enumerate(report['complexity_issues'][:5], 1):
            print(f"  {i}. {issue['type']}: {issue['function']} (值: {issue['value']})")

    output_path = project_path / "reports" / "code_quality_optimization_report.json"
    optimizer.export_report(report, output_path)
    print(f"\n报告已导出到: {output_path}")


def example_architecture_optimization():
    """架构优化示例"""
    print("\n" + "=" * 80)
    print("架构优化示例")
    print("=" * 80)

    project_path = get_path_config().SKILL_ROOT

    optimizer = UnifiedArchitectureOptimizer(project_path)

    print("\n运行架构优化周期...")
    report = optimizer.run_full_optimization_cycle(
        auto_apply=False,
        max_optimizations=10
    )

    print(f"\n分析的依赖数: {report['dependencies_analyzed']}")
    print(f"发现的问题数: {report['issues_found']}")
    print(f"生成的建议数: {report['suggestions_generated']}")
    print(f"执行的优化数: {report['optimizations_executed']}")
    print(f"成功的优化数: {report['successful_optimizations']}")

    if report['issues']:
        print("\n前 5 个架构问题:")
        for i, issue in enumerate(report['issues'][:5], 1):
            print(f"  {i}. {issue['type']}: {issue['description']}")

    output_path = project_path / "reports" / "architecture_optimization_report.json"
    optimizer.export_report(report, output_path)
    print(f"\n报告已导出到: {output_path}")


def example_optimization_evaluation():
    """优化效果评估示例"""
    print("\n" + "=" * 80)
    print("优化效果评估示例")
    print("=" * 80)

    project_path = get_path_config().SKILL_ROOT

    evaluator = UnifiedOptimizationEvaluator(
        history_file=project_path / "optimization_history.json"
    )

    before_metrics = {
        'execution_time': 150.0,
        'memory_usage': 80.0,
        'cpu_usage': 45.0,
        'cyclomatic_complexity': 20.0,
        'code_duplication': 15.0,
        'function_length': 60.0,
        'coupling_score': 0.6,
        'cohesion_score': 0.4,
        'dependency_cycles': 5.0,
        'test_coverage': 60.0,
    }

    after_metrics = {
        'execution_time': 100.0,
        'memory_usage': 50.0,
        'cpu_usage': 30.0,
        'cyclomatic_complexity': 12.0,
        'code_duplication': 5.0,
        'function_length': 30.0,
        'coupling_score': 0.3,
        'cohesion_score': 0.7,
        'dependency_cycles': 0.0,
        'test_coverage': 85.0,
    }

    print("\n评估优化效果...")
    evaluation = evaluator.evaluate_optimization(
        optimization_id="EXAMPLE-OPT-001",
        optimization_type="full",
        before_metrics=before_metrics,
        after_metrics=after_metrics,
        details={'example': True}
    )

    print(f"\n总体得分: {evaluation['score']['overall']:.2f}")
    print(f"改进等级: {evaluation['score']['level']}")
    print(f"摘要: {evaluation['score']['summary']}")

    print("\n各项指标改进:")
    for measurement in evaluation['measurements']:
        print(f"  - {measurement['metric']}: {measurement['before']:.1f} -> {measurement['after']:.1f} ({measurement['improvement']})")

    print("\n建议:")
    for i, rec in enumerate(evaluation['recommendations'], 1):
        print(f"  {i}. {rec}")

    trend = evaluator.get_trend_report()
    print(f"\n趋势分析: {trend}")

    output_path = project_path / "reports" / "optimization_evaluation_report.json"
    evaluator.export_evaluation_report(evaluation, output_path)
    print(f"\n评估报告已导出到: {output_path}")


def example_comprehensive_report():
    """综合报告示例"""
    print("\n" + "=" * 80)
    print("综合报告示例")
    print("=" * 80)

    project_path = get_path_config().SKILL_ROOT

    manager = create_optimization_manager(
        project_path=project_path,
        auto_apply=False,
        max_optimizations=5
    )

    print("\n执行多次优化...")
    manager.run_optimization(OptimizationType.PERFORMANCE)
    manager.run_optimization(OptimizationType.CODE_QUALITY)
    manager.run_optimization(OptimizationType.ARCHITECTURE)
    manager.run_optimization(OptimizationType.FULL)

    print("\n生成综合报告...")
    report = manager.generate_comprehensive_report()

    print(f"\n报告 ID: {report['report_id']}")
    print(f"生成时间: {report['generated_at']}")
    print(f"总优化次数: {report['total_optimizations']}")
    print(f"性能优化次数: {report['performance_optimizations']}")
    print(f"代码质量优化次数: {report['quality_optimizations']}")
    print(f"架构优化次数: {report['architecture_optimizations']}")

    print("\n趋势分析:")
    trend = report['trend_analysis']
    print(f"  平均得分: {trend.get('average_score', 0):.2f}")
    print(f"  最高得分: {trend.get('best_score', 0):.2f}")
    print(f"  最低得分: {trend.get('worst_score', 0):.2f}")
    print(f"  趋势: {trend.get('trend', 'unknown')}")

    print("\n全局建议:")
    for i, rec in enumerate(report['recommendations'], 1):
        print(f"  {i}. {rec}")

    output_path = project_path / "reports" / "comprehensive_optimization_report.json"
    manager.export_comprehensive_report(output_path)
    print(f"\n综合报告已导出到: {output_path}")


def example_custom_configuration():
    """自定义配置示例"""
    print("\n" + "=" * 80)
    print("自定义配置示例")
    print("=" * 80)

    project_path = get_path_config().SKILL_ROOT

    config = OptimizationConfig(
        auto_apply=False,
        max_optimizations_per_type=15,
        enable_performance_optimization=True,
        enable_code_quality_optimization=True,
        enable_architecture_optimization=True,
        output_dir=project_path / "reports" / "custom_optimization",
        verbose=True
    )

    manager = UnifiedOptimizationManager(project_path, config)

    print("\n使用自定义配置执行优化...")
    result = manager.run_optimization(OptimizationType.FULL)

    print(f"\n优化完成!")
    print(f"优化 ID: {result.optimization_id}")
    print(f"总体得分: {result.overall_score:.2f}")
    print(f"摘要: {result.summary}")

    print("\n详细结果:")
    if result.performance_report:
        print(f"  性能优化: {result.performance_report.get('optimizations_executed', 0)} 个")
    if result.quality_report:
        print(f"  代码质量优化: {result.quality_report.get('refactorings_executed', 0)} 个")
    if result.architecture_report:
        print(f"  架构优化: {result.architecture_report.get('optimizations_executed', 0)} 个")


def run_all_examples():
    """运行所有示例"""
    print("\n" + "=" * 80)
    print("三省六部技能 - 自动优化能力演示")
    print("=" * 80)
    print(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    try:
        example_basic_usage()
        example_performance_optimization()
        example_code_quality_optimization()
        example_architecture_optimization()
        example_optimization_evaluation()
        example_comprehensive_report()
        example_custom_configuration()

        print("\n" + "=" * 80)
        print("所有示例运行完成!")
        print("=" * 80)

    except Exception as e:
        print(f"\n运行示例时出错: {e}")
        import traceback
from skillscripts.core.path_config_center import get_path_config
        traceback.print_exc()


if __name__ == "__main__":
    run_all_examples()
