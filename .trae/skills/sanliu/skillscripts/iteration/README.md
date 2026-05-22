# 自动迭代与自完善机制

## 概述

本模块实现了三省六部技能的自动迭代与自完善机制，提供完整的版本管理、问题发现与修复、迭代触发和效果评估功能。

## 功能特性

### 1. 增强版版本迭代器 (`enhanced_version_iterator.py`)

#### 核心功能
- **语义化版本自动升级**：支持 Major、Minor、Patch、预发布版本等多种升级类型
- **变更日志自动生成**：遵循 Keep a Changelog 规范，支持 Markdown 和 JSON 格式
- **版本快照自动创建**：在每次迭代时自动创建代码快照
- **版本回滚机制**：支持快速回滚到任意历史版本

#### 使用示例

```python
from iteration import EnhancedVersionIterator, VersionBumpType, ChangeType, ChangeEntry

# 初始化迭代器
iterator = EnhancedVersionIterator("/path/to/project")

# 执行版本迭代
changes = [
    ChangeEntry(change_type=ChangeType.FEATURE, description="添加新功能"),
    ChangeEntry(change_type=ChangeType.FIX, description="修复bug")
]
entry = iterator.iterate(
    bump_type=VersionBumpType.MINOR,
    changes=changes,
    author="开发者",
    notes="版本更新说明"
)

print(f"新版本: {entry.version}")
print(f"快照ID: {entry.snapshot_id}")

# 查看快照列表
snapshots = iterator.list_snapshots()

# 回滚版本
iterator.rollback_version("1.0.0")

# 生成变更日志
changelog = iterator.changelog_generator.generate()
```

#### 命令行使用

```bash
# 执行版本迭代
python enhanced_version_iterator.py iterate --type minor --change "feat:新功能" --author "开发者"

# 查看状态
python enhanced_version_iterator.py status

# 回滚版本
python enhanced_version_iterator.py rollback --to 1.0.0

# 管理快照
python enhanced_version_iterator.py snapshot list
python enhanced_version_iterator.py snapshot create --description "手动快照"
python enhanced_version_iterator.py snapshot restore --id SNAP-xxx

# 生成变更日志
python enhanced_version_iterator.py changelog -o CHANGELOG.md
```

### 2. 自完善循环系统 (`self_improvement_cycle.py`)

#### 核心功能
- **问题发现引擎**：自动扫描代码库发现 Bug、性能问题、安全问题等
- **问题分析器**：深度分析问题根因和影响范围
- **修复执行器**：自动执行修复操作
- **验证引擎**：验证修复效果
- **学习引擎**：从修复过程中学习和积累经验
- **优化应用器**：将学习到的经验应用到其他场景

#### 使用示例

```python
from iteration import SelfImprovementCycle, IssueType

# 初始化循环系统
cycle = SelfImprovementCycle("/path/to/project")

# 运行自完善循环
result = cycle.run_cycle(scan_types=[IssueType.BUG, IssueType.CODE_QUALITY])

print(f"发现问题: {len(result.issues_discovered)}")
print(f"修复问题: {len(result.issues_fixed)}")
print(f"验证问题: {len(result.issues_verified)}")
print(f"学习记录: {len(result.learnings)}")

# 查看循环历史
history = cycle.get_cycle_history(limit=10)

# 生成报告
report = cycle.generate_report("improvement_report.md")
```

#### 命令行使用

```bash
# 运行自完善循环
python self_improvement_cycle.py --project-root /path/to/project

# 指定扫描类型
python self_improvement_cycle.py --scan-types bug performance security

# 生成报告
python self_improvement_cycle.py --report --output report.md
```

### 3. 迭代触发器系统 (`iteration_trigger_system.py`)

#### 核心功能
- **定时触发**：支持间隔、每日、每周等多种定时策略
- **事件触发**：监听文件变更、测试失败、构建失败等事件
- **阈值触发**：监控错误率、性能指标等，超过阈值自动触发
- **手动触发**：支持手动触发迭代

#### 使用示例

```python
from iteration import IterationTriggerSystem, TriggerType

# 初始化触发器系统
system = IterationTriggerSystem("/path/to/project")

# 设置迭代回调
def on_iteration():
    print("迭代被触发！")
    # 执行迭代逻辑...

system.set_iteration_callback(on_iteration)

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
        "thresholds": {
            "error_rate": {"operator": ">", "value": 5.0}
        }
    }
)

# 启动所有触发器
system.start_all()

# 手动触发
system.manual_trigger("TRIGGER-xxx")

# 查看状态
status = system.get_all_status()
```

#### 命令行使用

```bash
# 注册触发器
python iteration_trigger_system.py register --type scheduled --config '{"type":"interval","interval_seconds":3600}'

# 查看状态
python iteration_trigger_system.py status

# 手动触发
python iteration_trigger_system.py trigger --trigger-id TRIGGER-xxx

# 生成报告
python iteration_trigger_system.py report --output trigger_report.md
```

### 4. 迭代效果评估系统 (`iteration_effect_evaluator.py`)

#### 核心功能
- **指标定义**：定义代码覆盖率、测试通过率、性能指标等多种指标
- **前后对比**：对比迭代前后的指标变化
- **报告生成**：生成详细的效果评估报告
- **历史分析**：分析迭代历史趋势和模式

#### 使用示例

```python
from iteration import IterationEffectEvaluator, IterationHistoryAnalyzer

# 初始化评估器
evaluator = IterationEffectEvaluator("/path/to/project")
analyzer = IterationHistoryAnalyzer("/path/to/project")

# 收集指标
metrics = evaluator.collect_metrics("iteration-1")
print(f"代码覆盖率: {metrics.get('code_coverage', 0):.2f}%")
print(f"测试通过率: {metrics.get('test_pass_rate', 0):.2f}%")

# 对比迭代前后
before = {"code_coverage": 70.0, "test_pass_rate": 85.0}
after = {"code_coverage": 85.0, "test_pass_rate": 95.0}
effect = evaluator.compare_iterations("iteration-1", before, after)

print(f"改善的指标: {len(effect.improvements)}")
print(f"下降的指标: {len(effect.degradations)}")

# 生成对比报告
report = evaluator.generate_comparison_report(effect)

# 记录迭代历史
analyzer.record_iteration(
    iteration_id="iteration-1",
    trigger_type="manual",
    duration_seconds=45.5,
    issues_found=5,
    issues_fixed=4,
    metrics_snapshot=after
)

# 分析趋势
trends = analyzer.analyze_trends(days=30)
print(f"迭代频率: {trends['iteration_frequency']} 次/天")
print(f"平均成功率: {trends['average_success_rate']:.2f}%")

# 生成历史分析报告
report = analyzer.generate_analysis_report("history_report.md")
```

#### 命令行使用

```bash
# 收集指标
python iteration_effect_evaluator.py collect --iteration-id iter-1

# 对比迭代
python iteration_effect_evaluator.py compare --iteration-id iter-1

# 生成报告
python iteration_effect_evaluator.py report --output evaluation_report.md

# 查看趋势
python iteration_effect_evaluator.py trend --metric-id code_coverage --days 30

# 历史分析
python iteration_effect_evaluator.py history --output history_report.md
```

## 完整集成示例

```python
from iteration import (
    EnhancedVersionIterator,
    SelfImprovementCycle,
    IterationTriggerSystem,
    IterationEffectEvaluator,
    IterationHistoryAnalyzer,
    TriggerType,
    VersionBumpType,
    ChangeType,
    ChangeEntry
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
    print("迭代触发！")
    
    # 收集迭代前指标
    metrics_before = evaluator.collect_metrics("auto-iteration")
    
    # 运行自完善循环
    result = cycle.run_cycle()
    
    # 收集迭代后指标
    metrics_after = evaluator.collect_metrics("auto-iteration")
    
    # 对比效果
    effect = evaluator.compare_iterations("auto-iteration", metrics_before, metrics_after)
    
    # 如果有改善，执行版本迭代
    if effect.improvements:
        changes = [
            ChangeEntry(
                change_type=ChangeType.FIX,
                description=f"自动修复 {len(result.issues_fixed)} 个问题"
            )
        ]
        iterator.iterate(VersionBumpType.PATCH, changes)
    
    # 记录迭代历史
    analyzer.record_iteration(
        iteration_id="auto-iteration",
        trigger_type="scheduled",
        duration_seconds=result.duration,
        issues_found=len(result.issues_discovered),
        issues_fixed=len(result.issues_fixed),
        metrics_snapshot=metrics_after
    )

# 设置回调
trigger_system.set_iteration_callback(on_trigger)

# 注册触发器
trigger_system.register_trigger(
    TriggerType.SCHEDULED,
    {"type": "interval", "interval_seconds": 3600}
)

trigger_system.register_trigger(
    TriggerType.THRESHOLD,
    {
        "monitor_error_rate": True,
        "thresholds": {"error_rate": {"operator": ">", "value": 5.0}}
    }
)

# 启动所有触发器
trigger_system.start_all()

print("自动迭代与自完善机制已启动！")
```

## 文件结构

```
iteration/
├── __init__.py                      # 模块初始化
├── enhanced_version_iterator.py     # 增强版版本迭代器
├── self_improvement_cycle.py        # 自完善循环系统
├── iteration_trigger_system.py      # 迭代触发器系统
├── iteration_effect_evaluator.py    # 迭代效果评估系统
├── test_integration.py              # 集成测试
└── README.md                        # 本文档
```

## 测试

运行集成测试：

```bash
python test_integration.py
```

测试将验证以下功能：
1. 版本迭代器的版本升级、快照创建、回滚功能
2. 自完善循环的问题发现、分析、修复、验证流程
3. 触发器系统的定时、事件、阈值触发机制
4. 效果评估系统的指标收集、对比、报告生成功能
5. 完整的集成工作流

## 配置文件

系统会在项目根目录下创建以下配置文件：

- `version.json` - 版本历史记录
- `CHANGELOG.md` - 变更日志
- `.version_snapshots/` - 版本快照目录
- `.improvement_knowledge.json` - 学习知识库
- `.improvement_cycles.json` - 改进循环历史
- `.trigger_configs.json` - 触发器配置
- `.trigger_results.json` - 触发器结果
- `.metrics_history.json` - 指标历史
- `.effect_metrics.json` - 效果指标
- `.iteration_history.json` - 迭代历史

## 最佳实践

1. **定期触发迭代**：建议设置定时触发器，每小时或每天执行一次迭代检查
2. **监控关键指标**：设置阈值触发器监控错误率、性能等关键指标
3. **保留历史数据**：定期备份配置文件和历史记录
4. **审查学习结果**：定期查看学习引擎的知识库，确保学习质量
5. **验证修复效果**：每次迭代后都要验证修复效果，避免引入新问题

## 注意事项

1. 首次运行会在项目根目录创建配置文件
2. 版本快照会占用磁盘空间，建议定期清理旧快照
3. 触发器系统使用后台线程，确保在程序退出前正确停止
4. 自动修复可能不完美，建议在关键项目上人工审查修复结果
5. 学习引擎的知识库会不断积累，建议定期整理和优化

## 版本历史

- **v1.0.0** (2026-04-01)
  - 初始版本发布
  - 实现完整的自动迭代与自完善机制
  - 包含版本迭代器、自完善循环、触发器系统、效果评估四大核心模块

## 作者

三省六部技能开发团队

## 许可证

内部使用
