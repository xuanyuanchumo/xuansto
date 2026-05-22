#!/usr/bin/env python3
"""
测试增强版版本迭代器功能
"""

import sys
import os
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(get_path_config().SCRIPTS_DIR))

from version_iterator import (
    VersionIterator,
    QualityMetrics,
    ImprovementTaskPriority,
    IterationStatus,
    IterationPhase,
    IterationTriggerType
)


def test_quality_metrics():
    """测试质量指标"""
    print("\n=== 测试质量指标 ===")
    
    metrics = QualityMetrics(
        code_quality_score=0.65,
        test_coverage=55.0,
        error_rate=0.08,
        performance_score=0.75,
        security_score=0.85,
        health_score=0.70
    )
    
    print(f"代码质量分数: {metrics.code_quality_score}")
    print(f"测试覆盖率: {metrics.test_coverage}%")
    print(f"错误率: {metrics.error_rate:.2%}")
    print(f"综合分数: {metrics.calculate_overall_score():.3f}")
    
    assert metrics.code_quality_score == 0.65
    assert metrics.test_coverage == 55.0
    print("✅ 质量指标测试通过")


def test_quality_driven_iteration():
    """测试质量驱动迭代"""
    print("\n=== 测试质量驱动迭代 ===")
    
    test_dir = Path(__file__).parent / "test_version_iteration"
    test_dir.mkdir(exist_ok=True)
    
    vi = VersionIterator(str(test_dir))
    
    metrics = QualityMetrics(
        code_quality_score=0.65,
        test_coverage=55.0,
        error_rate=0.08,
        performance_score=0.75,
        security_score=0.85,
        health_score=0.70
    )
    
    result = vi.quality_driven_iteration(metrics, auto_create_tasks=True)
    
    print(f"触发迭代: {result['triggered']}")
    print(f"触发条件数量: {len(result['triggers'])}")
    print(f"创建任务数量: {len(result['tasks_created'])}")
    print(f"迭代已开始: {result['iteration_started']}")
    
    if result['triggers']:
        print("\n触发的条件:")
        for trigger in result['triggers']:
            print(f"  - {trigger.trigger_type.value}: {trigger.details.get('message', '')}")
    
    if result['tasks_created']:
        print("\n创建的任务:")
        for task in result['tasks_created']:
            print(f"  - {task.task_id}: {task.title} (优先级: {task.priority.value})")
    
    assert result['triggered'] == True
    assert len(result['triggers']) > 0
    assert len(result['tasks_created']) > 0
    print("✅ 质量驱动迭代测试通过")
    
    import shutil
    if test_dir.exists():
        shutil.rmtree(test_dir)


def test_improvement_tasks():
    """测试改进任务管理"""
    print("\n=== 测试改进任务管理 ===")
    
    test_dir = Path(__file__).parent / "test_version_tasks"
    test_dir.mkdir(exist_ok=True)
    
    vi = VersionIterator(str(test_dir))
    
    task = vi.create_improvement_task(
        title="测试任务",
        description="这是一个测试任务",
        priority=ImprovementTaskPriority.HIGH,
        category="testing",
        affected_components=["module1", "module2"],
        tags=["test", "quality"]
    )
    
    print(f"任务ID: {task.task_id}")
    print(f"任务标题: {task.title}")
    print(f"任务优先级: {task.priority.value}")
    print(f"任务状态: {task.status}")
    
    pending_tasks = vi.get_pending_improvement_tasks()
    print(f"待处理任务数量: {len(pending_tasks)}")
    
    assert task.task_id.startswith("TASK-")
    assert task.status == "pending"
    assert len(pending_tasks) == 1
    print("✅ 改进任务管理测试通过")
    
    import shutil
    if test_dir.exists():
        shutil.rmtree(test_dir)


def test_iteration_progress():
    """测试迭代进度跟踪"""
    print("\n=== 测试迭代进度跟踪 ===")
    
    test_dir = Path(__file__).parent / "test_version_progress"
    test_dir.mkdir(exist_ok=True)
    
    vi = VersionIterator(str(test_dir))
    
    from version_iterator import IterationTrigger
    
    triggers = [
        IterationTrigger(
            trigger_type=IterationTriggerType.CODE_QUALITY,
            threshold=0.7,
            current_value=0.65,
            triggered=True
        )
    ]
    
    progress = vi.start_iteration_with_progress(triggers)
    
    print(f"迭代ID: {progress.iteration_id}")
    print(f"目标版本: {progress.version}")
    print(f"当前阶段: {progress.current_phase.value}")
    print(f"状态: {progress.status.value}")
    print(f"进度: {progress.progress_percentage:.1f}%")
    
    assert progress.status == IterationStatus.IN_PROGRESS
    assert progress.current_phase == IterationPhase.TRIGGER_DETECTION
    
    progress = vi.complete_iteration_phase(IterationPhase.TRIGGER_DETECTION)
    print(f"完成阶段后的新阶段: {progress.current_phase.value}")
    
    assert progress.current_phase == IterationPhase.QUALITY_ASSESSMENT
    print("✅ 迭代进度跟踪测试通过")
    
    import shutil
    if test_dir.exists():
        shutil.rmtree(test_dir)


def test_sanliu_integration():
    """测试三省六部集成"""
    print("\n=== 测试三省六部集成 ===")
    
    test_dir = Path(__file__).parent / "test_version_sanliu"
    test_dir.mkdir(exist_ok=True)
    
    vi = VersionIterator(str(test_dir))
    
    metrics = QualityMetrics(
        code_quality_score=0.65,
        test_coverage=55.0,
        error_rate=0.08
    )
    
    result = vi.integrate_with_sanliu_workflow(
        province="menxiasheng",
        action="quality_gate_check",
        data={"metrics": metrics}
    )
    
    print(f"省份: {result['province']}")
    print(f"动作: {result['action']}")
    print(f"成功: {result['success']}")
    print(f"质量门禁通过: {result['data'].get('passed', False)}")
    
    assert result['success'] == True
    assert result['data']['passed'] == False
    print("✅ 三省六部集成测试通过")
    
    import shutil
    if test_dir.exists():
        shutil.rmtree(test_dir)


def main():
    """运行所有测试"""
    print("=" * 60)
    print("开始测试增强版版本迭代器")
    print("=" * 60)
    
    try:
        test_quality_metrics()
        test_improvement_tasks()
        test_iteration_progress()
        test_quality_driven_iteration()
        test_sanliu_integration()
        
        print("\n" + "=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
from skillscripts.core.path_config_center import get_path_config
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
