#!/usr/bin/env python3
"""
集成测试和使用示例
演示自动迭代与自完善机制的完整功能
"""

import json
import os
import sys
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(get_path_config().SKILL_ROOT))

from enhanced_version_iterator import (
    EnhancedVersionIterator,
    VersionBumpType,
    ChangeType,
    ChangeEntry
)

from self_improvement_cycle import (
    SelfImprovementCycle,
    IssueType
)

from iteration_trigger_system import (
    IterationTriggerSystem,
    TriggerType
)

from iteration_effect_evaluator import (
    IterationEffectEvaluator,
    IterationHistoryAnalyzer
)


def create_test_project() -> Path:
    test_dir = Path(tempfile.mkdtemp(prefix="iteration_test_"))
    
    (test_dir / "src").mkdir(parents=True, exist_ok=True)
    (test_dir / "tests").mkdir(parents=True, exist_ok=True)
    
    main_py = test_dir / "src" / "main.py"
    main_py.write_text("""
def main():
    print("Hello, World!")
    x = 1 + 2
    return x

if __name__ == "__main__":
    main()
""")
    
    test_py = test_dir / "tests" / "test_main.py"
    test_py.write_text("""
import sys
sys.path.insert(0, '../src')
from main import main

def test_main():
    result = main()
    assert result == 3
""")
    
    requirements = test_dir / "requirements.txt"
    requirements.write_text("pytest>=7.0.0\n")
    
    return test_dir


def test_version_iterator():
    print("\n" + "="*60)
    print("测试1: 增强版版本迭代器")
    print("="*60)
    
    test_dir = create_test_project()
    print(f"测试项目目录: {test_dir}")
    
    try:
        iterator = EnhancedVersionIterator(str(test_dir))
        
        print("\n1.1 查看初始状态")
        status = iterator.get_status()
        print(f"项目名称: {status['project_name']}")
        print(f"当前版本: {status['current_version']}")
        
        print("\n1.2 执行版本迭代")
        changes = [
            ChangeEntry(
                change_type=ChangeType.FEATURE,
                description="添加新功能",
                scope="core"
            ),
            ChangeEntry(
                change_type=ChangeType.FIX,
                description="修复bug",
                scope="ui"
            )
        ]
        
        entry = iterator.iterate(
            bump_type=VersionBumpType.MINOR,
            changes=changes,
            author="测试用户",
            notes="测试版本迭代"
        )
        
        print(f"新版本: {entry.version}")
        print(f"上一版本: {entry.previous_version}")
        print(f"变更数: {len(entry.changes)}")
        print(f"快照ID: {entry.snapshot_id}")
        
        print("\n1.3 查看快照列表")
        snapshots = iterator.list_snapshots()
        for snap in snapshots:
            print(f"快照ID: {snap['snapshot_id']}, 版本: {snap['version']}")
        
        print("\n1.4 生成变更日志")
        changelog = iterator.changelog_generator.generate()
        print("变更日志已生成")
        
        print("\n1.5 测试版本回滚")
        rollback_success = iterator.rollback_version("0.0.0")
        print(f"回滚成功: {rollback_success}")
        print(f"当前版本: {iterator.history.current_version}")
        
        print("\n✅ 版本迭代器测试完成")
        
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def test_self_improvement_cycle():
    print("\n" + "="*60)
    print("测试2: 自完善循环系统")
    print("="*60)
    
    test_dir = create_test_project()
    print(f"测试项目目录: {test_dir}")
    
    try:
        cycle = SelfImprovementCycle(str(test_dir))
        
        print("\n2.1 运行自完善循环")
        result = cycle.run_cycle(scan_types=[IssueType.CODE_QUALITY])
        
        print(f"循环ID: {result.cycle_id}")
        print(f"发现问题: {len(result.issues_discovered)}")
        print(f"分析问题: {len(result.issues_analyzed)}")
        print(f"修复问题: {len(result.issues_fixed)}")
        print(f"验证问题: {len(result.issues_verified)}")
        print(f"学习记录: {len(result.learnings)}")
        print(f"成功: {result.success}")
        
        if result.issues_discovered:
            print("\n发现的问题:")
            for issue in result.issues_discovered[:3]:
                print(f"  - {issue.title} ({issue.severity.value})")
        
        print("\n2.2 生成循环报告")
        report = cycle.generate_report()
        print("报告已生成")
        
        print("\n✅ 自完善循环测试完成")
        
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def test_iteration_trigger():
    print("\n" + "="*60)
    print("测试3: 迭代触发器系统")
    print("="*60)
    
    test_dir = create_test_project()
    print(f"测试项目目录: {test_dir}")
    
    try:
        system = IterationTriggerSystem(str(test_dir))
        
        print("\n3.1 注册手动触发器")
        trigger_id = system.register_trigger(
            TriggerType.MANUAL,
            {"description": "手动测试触发器"}
        )
        print(f"触发器ID: {trigger_id}")
        
        print("\n3.2 注册定时触发器")
        scheduled_id = system.register_trigger(
            TriggerType.SCHEDULED,
            {"type": "interval", "interval_seconds": 3600}
        )
        print(f"触发器ID: {scheduled_id}")
        
        print("\n3.3 注册阈值触发器")
        threshold_id = system.register_trigger(
            TriggerType.THRESHOLD,
            {
                "monitor_error_rate": True,
                "thresholds": {
                    "error_rate": {
                        "operator": ">",
                        "value": 5.0
                    }
                }
            }
        )
        print(f"触发器ID: {threshold_id}")
        
        print("\n3.4 查看触发器状态")
        statuses = system.get_all_status()
        for status in statuses:
            print(f"触发器: {status['trigger_id']}, 类型: {status['type']}, 状态: {'运行中' if status['running'] else '已停止'}")
        
        print("\n3.5 手动触发")
        trigger_count_before = system.trigger_configs[trigger_id].trigger_count
        success = system.manual_trigger(trigger_id)
        trigger_count_after = system.trigger_configs[trigger_id].trigger_count
        print(f"触发成功: {success}")
        print(f"触发次数: {trigger_count_before} -> {trigger_count_after}")
        
        print("\n3.6 生成触发器报告")
        report = system.generate_report()
        print("报告已生成")
        
        print("\n✅ 迭代触发器测试完成")
        
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def test_effect_evaluator():
    print("\n" + "="*60)
    print("测试4: 迭代效果评估系统")
    print("="*60)
    
    test_dir = create_test_project()
    print(f"测试项目目录: {test_dir}")
    
    try:
        evaluator = IterationEffectEvaluator(str(test_dir))
        analyzer = IterationHistoryAnalyzer(str(test_dir))
        
        print("\n4.1 收集指标")
        metrics = evaluator.collect_metrics("test-iteration-1")
        print("收集的指标:")
        for metric_id, value in metrics.items():
            print(f"  - {metric_id}: {value}")
        
        print("\n4.2 模拟迭代前后对比")
        before_metrics = {
            "code_coverage": 65.0,
            "test_pass_rate": 85.0,
            "code_quality_score": 70.0,
            "error_rate": 8.0
        }
        
        after_metrics = {
            "code_coverage": 75.0,
            "test_pass_rate": 90.0,
            "code_quality_score": 80.0,
            "error_rate": 3.0
        }
        
        effect = evaluator.compare_iterations("test-iteration-1", before_metrics, after_metrics)
        
        print(f"改善的指标: {len(effect.improvements)}")
        print(f"下降的指标: {len(effect.degradations)}")
        
        if effect.improvements:
            print("\n改善详情:")
            for metric_id, change in effect.improvements.items():
                print(f"  - {metric_id}: {change:+.2f}")
        
        print("\n4.3 生成对比报告")
        report = evaluator.generate_comparison_report(effect)
        print(f"整体评分: {report.overall_score:.2f}")
        print(f"摘要: {report.summary}")
        
        print("\n4.4 记录迭代历史")
        analyzer.record_iteration(
            iteration_id="test-iteration-1",
            trigger_type="manual",
            duration_seconds=45.5,
            issues_found=5,
            issues_fixed=4,
            metrics_snapshot=after_metrics
        )
        
        print("\n4.5 分析迭代趋势")
        stats = analyzer.get_iteration_stats()
        print(f"总迭代次数: {stats.get('total_iterations', 0)}")
        
        print("\n4.6 生成历史分析报告")
        report = analyzer.generate_analysis_report()
        print("报告已生成")
        
        print("\n✅ 效果评估测试完成")
        
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def test_integrated_workflow():
    print("\n" + "="*60)
    print("测试5: 集成工作流")
    print("="*60)
    
    test_dir = create_test_project()
    print(f"测试项目目录: {test_dir}")
    
    try:
        print("\n5.1 初始化所有组件")
        iterator = EnhancedVersionIterator(str(test_dir))
        cycle = SelfImprovementCycle(str(test_dir))
        trigger_system = IterationTriggerSystem(str(test_dir))
        evaluator = IterationEffectEvaluator(str(test_dir))
        analyzer = IterationHistoryAnalyzer(str(test_dir))
        
        print("\n5.2 设置触发器回调")
        def on_iteration_trigger():
            print("触发迭代回调...")
            
            metrics_before = evaluator.collect_metrics("integrated-test")
            
            result = cycle.run_cycle()
            
            metrics_after = evaluator.collect_metrics("integrated-test")
            
            effect = evaluator.compare_iterations("integrated-test", metrics_before, metrics_after)
            
            if effect.improvements:
                changes = [
                    ChangeEntry(
                        change_type=ChangeType.FIX,
                        description=f"修复问题: {issue.title}",
                        scope="auto"
                    )
                    for issue in result.issues_fixed[:3]
                ]
                
                if changes:
                    iterator.iterate(
                        bump_type=VersionBumpType.PATCH,
                        changes=changes,
                        author="自动迭代系统"
                    )
            
            analyzer.record_iteration(
                iteration_id="integrated-test",
                trigger_type="manual",
                duration_seconds=30.0,
                issues_found=len(result.issues_discovered),
                issues_fixed=len(result.issues_fixed),
                metrics_snapshot=metrics_after
            )
            
            return result
        
        trigger_system.set_iteration_callback(on_iteration_trigger)
        
        print("\n5.3 注册并触发手动触发器")
        trigger_id = trigger_system.register_trigger(
            TriggerType.MANUAL,
            {"description": "集成测试触发器"}
        )
        
        success = trigger_system.manual_trigger(trigger_id)
        print(f"集成工作流执行: {'成功' if success else '失败'}")
        
        print("\n5.4 查看最终状态")
        version_status = iterator.get_status()
        print(f"当前版本: {version_status['current_version']}")
        print(f"迭代次数: {version_status['iteration_count']}")
        
        stats = analyzer.get_iteration_stats()
        print(f"总迭代次数: {stats.get('total_iterations', 0)}")
        
        print("\n✅ 集成工作流测试完成")
        
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def generate_usage_examples():
    print("\n" + "="*60)
    print("使用示例")
    print("="*60)
    
    examples = """
## 1. 版本迭代器使用示例

```python
from iteration import EnhancedVersionIterator, VersionBumpType, ChangeType, ChangeEntry

# 初始化迭代器
iterator = EnhancedVersionIterator("/path/to/project")

# 执行版本迭代
changes = [
    ChangeEntry(change_type=ChangeType.FEATURE, description="添加新功能"),
    ChangeEntry(change_type=ChangeType.FIX, description="修复bug")
]
entry = iterator.iterate(VersionBumpType.MINOR, changes, author="开发者")

# 查看状态
status = iterator.get_status()
print(f"当前版本: {status['current_version']}")

# 回滚版本
iterator.rollback_version("1.0.0")
```

## 2. 自完善循环使用示例

```python
from iteration import SelfImprovementCycle, IssueType

# 初始化循环系统
cycle = SelfImprovementCycle("/path/to/project")

# 运行自完善循环
result = cycle.run_cycle(scan_types=[IssueType.BUG, IssueType.CODE_QUALITY])

print(f"发现问题: {len(result.issues_discovered)}")
print(f"修复问题: {len(result.issues_fixed)}")
print(f"学习记录: {len(result.learnings)}")
```

## 3. 迭代触发器使用示例

```python
from iteration import IterationTriggerSystem, TriggerType

# 初始化触发器系统
system = IterationTriggerSystem("/path/to/project")

# 注册定时触发器（每小时）
system.register_trigger(
    TriggerType.SCHEDULED,
    {"type": "interval", "interval_seconds": 3600}
)

# 注册阈值触发器（错误率超过5%）
system.register_trigger(
    TriggerType.THRESHOLD,
    {
        "monitor_error_rate": True,
        "thresholds": {"error_rate": {"operator": ">", "value": 5.0}}
    }
)

# 手动触发
system.manual_trigger("TRIGGER-xxx")
```

## 4. 效果评估使用示例

```python
from iteration import IterationEffectEvaluator, IterationHistoryAnalyzer

# 初始化评估器
evaluator = IterationEffectEvaluator("/path/to/project")
analyzer = IterationHistoryAnalyzer("/path/to/project")

# 收集指标
metrics = evaluator.collect_metrics("iteration-1")

# 对比迭代前后
effect = evaluator.compare_iterations(
    "iteration-1",
    before_metrics={"code_coverage": 70.0},
    after_metrics={"code_coverage": 85.0}
)

# 分析历史趋势
trends = analyzer.analyze_trends(days=30)
print(f"迭代频率: {trends['iteration_frequency']} 次/天")
```

## 5. 完整集成示例

```python
from iteration import (
    EnhancedVersionIterator,
    SelfImprovementCycle,
    IterationTriggerSystem,
    IterationEffectEvaluator,
    IterationHistoryAnalyzer,
    TriggerType
)

# 初始化所有组件
project_root = "/path/to/project"
iterator = EnhancedVersionIterator(project_root)
cycle = SelfImprovementCycle(project_root)
trigger_system = IterationTriggerSystem(project_root)
evaluator = IterationEffectEvaluator(project_root)
analyzer = IterationHistoryAnalyzer(project_root)

# 设置触发器回调
def on_trigger():
    metrics_before = evaluator.collect_metrics("auto-iteration")
    result = cycle.run_cycle()
    metrics_after = evaluator.collect_metrics("auto-iteration")
    
    effect = evaluator.compare_iterations("auto-iteration", metrics_before, metrics_after)
    
    if effect.improvements:
        iterator.iterate(VersionBumpType.PATCH, [...])
    
    analyzer.record_iteration(...)

trigger_system.set_iteration_callback(on_trigger)

# 启动触发器
trigger_system.register_trigger(TriggerType.SCHEDULED, {"type": "interval", "interval_seconds": 3600})
trigger_system.start_all()
```
"""
    
    print(examples)


def main():
    print("="*60)
    print("自动迭代与自完善机制 - 集成测试")
    print("="*60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        test_version_iterator()
        test_self_improvement_cycle()
        test_iteration_trigger()
        test_effect_evaluator()
        test_integrated_workflow()
        
        generate_usage_examples()
        
        print("\n" + "="*60)
        print("所有测试完成！")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
from skillscripts.core.path_config_center import get_path_config
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
