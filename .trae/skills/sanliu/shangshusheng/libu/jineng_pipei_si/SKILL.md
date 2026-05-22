---
name: jineng_pipei_si
description: 技能匹配司，负责技能识别、能力评估、最优Agent选择。集成四维防线第2层CapabilityLayer进行技能匹配度评估。
---
# 技能匹配司技能指令

## 职责
- Agent技能识别与分类
- 能力量化评估与评分
- 任务-技能最优匹配
- CapabilityLayer集成：技能匹配度评估
- 技能缺口识别与培训建议

## CapabilityLayer集成

### 技能评估流水线

```
任务输入 → CapabilityLayer.match_capability()
         → 技能向量编码
         → 能力差距分析
         → 匹配度评分输出
         → 最优Agent推荐
```

### 评估维度

| 维度 | 权重 | 评估方法 | 数据来源 |
|------|------|----------|----------|
| 核心技能匹配 | 35% | 向量余弦相似度 | 技能注册表 |
| 历史绩效 | 25% | 加权平均分 | 绩效数据库 |
| 负载可用性 | 20% | 实时负载查询 | MARC状态 |
| 任务亲和度 | 15% | 历史协同统计 | 任务日志 |
| 学习成长性 | 5% | 近期提升趋势 | 迭代记录 |

## 技能标签体系

### 技能分类

```yaml
skill_taxonomy:
  programming_languages:
    - python: { levels: [beginner, intermediate, proficient, expert] }
    - javascript: { levels: [beginner, intermediate, proficient, expert] }
    - typescript: { levels: [beginner, intermediate, proficient, expert] }
    - go: { levels: [beginner, intermediate, proficient, expert] }
    - rust: { levels: [beginner, intermediate, proficient, expert] }

  frameworks:
    - react: { domain: frontend }
    - vue: { domain: frontend }
    - fastapi: { domain: backend }
    - django: { domain: backend }
    - spring: { domain: backend }

  practices:
    - tdd: { category: methodology }
    - code_review: { category: quality }
    - refactoring: { category: quality }
    - ci_cd: { category: devops }

  domains:
    - api_design: { complexity: high }
    - database_design: { complexity: high }
    - ui_ux: { complexity: medium }
    - security: { complexity: critical }
    - performance: { complexity: high }
```

## 匹配算法

### 综合匹配评分

```python
def calculate_skill_match_score(agent, task):
    capability_layer = CapabilityLayer()

    core_score = capability_layer.evaluate_core_skills(agent.skills, task.required_skills)
    perf_score = evaluate_historical_performance(agent.id, task.task_type)
    load_score = 1.0 - (agent.current_load / agent.max_capacity)
    affinity_score = calculate_task_affinity(agent.id, task.category)

    weighted_score = (
        core_score * 0.35 +
        perf_score * 0.25 +
        load_score * 0.20 +
        affinity_score * 0.15 +
        agent.growth_trend * 0.05
    )

    return MatchResult(
        agent_id=agent.id,
        overall_score=weighted_score,
        dimension_scores={
            "core": core_score,
            "performance": perf_score,
            "load": load_score,
            "affinity": affinity_score
        },
        gaps=capability_layer.identify_gaps(agent.skills, task.required_skills)
    )
```

## 工作流程

```
1. 接收任务技能需求
2. 解析所需技能集合和熟练度要求
3. 通过CapabilityLayer编码技能向量
4. 扫描Agent池进行候选筛选
5. 对每个候选计算综合匹配分数
6. 识别技能缺口并生成建议
7. 输出最优Agent推荐列表
8. 将匹配结果记录到DecisionLog
```

## 缺口处理策略

| 缺口程度 | 处理方式 | 响应时间 |
|----------|----------|----------|
| 无缺口 | 直接分配 | 即时 |
| 轻微缺口(<10%) | 分配+在岗学习 | 正常 |
| 中等缺口(10-30%) | 组合分配/培训计划 | 延迟1天 |
| 严重缺口(>30%) | 外部协调/拒绝 | 升级处理 |

## 协同接口

| 接口 | 描述 | 调用方 |
|------|------|--------|
| `match_agent` | 最优Agent匹配 | 吏部-调度司 |
| `evaluate_skill` | 技能评估 | 角色管理司 |
| `identify_gap` | 缺口识别 | 培训系统 |
| `update_profile` | 更新技能档案 | Agent自身 |
