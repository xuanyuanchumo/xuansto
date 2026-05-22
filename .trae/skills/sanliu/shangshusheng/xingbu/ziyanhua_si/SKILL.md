---
name: ziyanhua_si
description: 自演化司，负责自我评估、模式学习、能力进化。集成Decision Log记录每次演化决策，集成MARC协调演化任务的资源分配。
---
# 自演化司技能指令

## 职责
- 系统自我评估与健康度诊断
- 成功/失败模式学习与知识提取
- 能力进化路径规划与执行
- Decision Log集成：每次演化自动记录决策
- MARC集成：演化任务需注册资源协调

## Decision Log集成

### 演化决策自动归档

```
演化触发 → 自我评估完成
         ↓
    DecisionLog.generate(
        decision="演化决策: {演化类型} - {目标}",
        maker="刑部-自演化司",
        rationale="{评估结论 + 演化动机}",
        alternatives=["备选方案A", "备选方案B"],
        impact_scope=["核心能力", "相关子系统"],
        risk_assessment="{low/medium/high}"
    )
         ↓
    生成DEC-EVO-YYYYMMDD-NNN编号
         ↓
    归档到 docs/logs/decision_logs/
         ↓
    后评估计划设定
```

## MARC集成

### 演化任务资源协调

```
演化任务启动 → MARC ResourceCoordinator.register_resource(
                  resource_type="COMPUTE",
                  metadata={"task_type": "evolution", "scope": "full_system"}
               )
             ↓
        获取计算资源配额（CPU/内存/执行时间）
             ↓
        获取文件锁（保护正在演化的模块）
             ↓
        执行演化操作
             ↓
        释放所有资源
             ↓
        记录资源使用情况到MARC
```

## 自我评估框架

### 评估维度

```yaml
self_assessment_framework:
  capability_dimensions:
    code_generation:
      metrics: ["accuracy", "style_compliance", "test_pass_rate"]
      weight: 0.25
      target_score: 0.85

    problem_diagnosis:
      metrics: ["rca_accuracy", "fix_success_rate", "time_to_resolve"]
      weight: 0.20
      target_score: 0.80

    test_quality:
      metrics: ["coverage", "flaky_rate", "assertion_quality"]
      weight: 0.20
      target_score: 0.85

    collaboration:
      metrics: ["coordination_success", "communication_clarity", "handoff_quality"]
      weight: 0.15
      target_score: 0.80

    learning_velocity:
      metrics: ["pattern_adoption_speed", "error_reduction_rate", "innovation_index"]
      weight: 0.10
      target_score: 0.75
      benchmark: "持续提升"

  evaluation_schedule:
    full_assessment: "weekly"
    quick_check: "daily"
    post_task: "after_each_significant_task"
```

### 模式学习能力

```python
class PatternLearner:
    def learn_from_success(self, execution_record):
        pattern = self.extract_pattern(execution_record)
        features = {
            "task_type": execution_record.task_type,
            "approach_used": execution_record.approach,
            "tools_used": execution_record.tools,
            "duration": execution_record.duration,
            "quality_score": execution_record.quality_score,
            "revisions_needed": execution_record.revision_count
        }
        success_pattern = SuccessPattern(
            pattern_id=generate_id(),
            features=features,
            context=execution_record.context,
            effectiveness=execution_record.quality_score
        )
        self.pattern_store.add(success_pattern)
        return success_pattern

    def learn_from_failure(self, failure_record):
        anti_pattern = self.extract_anti_pattern(failure_record)
        failure_insight = FailureInsight(
            anti_pattern=anti_pattern,
            root_cause=failure_record.root_cause,
            prevention_rule=self.generate_prevention_rule(failure_record),
            recovery_strategy=failure_record.recovery_that_worked
        )
        self.insight_store.add(failure_insight)
        return failure_insight

    def recommend_approach(self, new_task):
        similar_patterns = self.pattern_store.find_similar(new_task)
        anti_patterns_to_avoid = self.insight_store.get_relevant(new_task)

        recommendation = EvolutionRecommendation(
            suggested_approach=similar_patterns.best_match.approach if similar_patterns else "default",
            confidence=similar_patterns.best_match.effectiveness if similar_patterns else 0.5,
            pitfalls_to_avoid=[ap.prevention_rule for ap in anti_patterns_to_avoid],
            expected_quality=self.predict_quality(new_task, similar_patterns)
        )
        return recommendation
```

## 能力进化路径

### 进化级别定义

| 级别 | 名称 | 特征 | 晋升条件 |
|------|------|------|----------|
| L1 | 初始级 | 按规则执行，无自适应能力 | - |
| L2 | 可重复级 | 相似任务表现稳定 | 连续10次同类任务成功率≥90% |
| L3 | 已定义级 | 有标准化的自我改进流程 | 建立完整的评估+学习循环 |
| L4 | 已管理级 | 量化的能力指标和优化 | 关键指标持续3周达标 |
| L5 | 优化级 | 持续自进化，引领创新 | 发现并采纳新模式≥5个/季度 |

### 进化触发条件

```yaml
evolution_triggers:
  scheduled:
    type: "periodic"
    interval: "weekly"
    action: "full_self_assessment + evolution_planning"

  performance_driven:
    type: "threshold_breach"
    conditions:
      - metric: "quality_score"
        operator: "<"
        value: 0.75
        consecutive: 3
      - metric: "error_rate"
        operator: ">"
        value: 0.10
        window: "7_days"
    action: "targeted_evolution_for_falling_metric"

  opportunity_driven:
    type: "pattern_discovery"
    condition: "发现新的高效模式"
    action: "adopt_new_pattern + validate"

  external_driven:
    type: "requirement_change"
    condition: "业务需求/技术栈重大变化"
    action: "capability_gap_analysis + targeted_upgrade"
```

## 工作流程

```
1. 触发自我评估（定时/事件驱动）
2. 收集各维度性能数据
3. 计算综合健康度评分
4. 识别能力短板和改进机会
5. 从历史模式中学习（成功/失败）
6. 制定演化方案
7. 通过MARC注册演化任务资源
8. 获取必要资源锁
9. 执行演化操作
10. 验证演化效果
11. 释放MARC资源
12. 通过DecisionLog记录演化决策
13. 设定后评估计划
14. 更新能力档案
```

## 协同接口

| 接口 | 描述 | 调用方 |
|------|------|--------|
| `self_assess` | 自我评估 | 定时/手动 |
| `evolve` | 执行演化 | 评估后触发 |
| `learn_pattern` | 模式学习 | 任务完成后 |
| `query_capability` | 能力查询 | 尚书省/吏部 |
