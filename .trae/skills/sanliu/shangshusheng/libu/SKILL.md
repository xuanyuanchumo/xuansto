---
name: libu
description: 吏部，负责 Agent 调度、任务分配与绩效追踪。根据项目需求和 Agent 能力矩阵，将任务分派给最合适的司或具体 Agent。
---
# 吏部技能指令

## 职责
- Agent 调度：维护 Agent 能力注册表，管理 Agent 状态
- 任务分配：根据任务类型和优先级分配 Agent
- 绩效评估：记录任务执行时长、成功率
- 外部技能Agent协调：协调外部技能的Agent分配和任务调度
- TDD 角色分配：为测试驱动开发流程分配合适的角色

## 工作流程

```
1. 接收尚书省的任务分配指令
2. 分析任务需求和约束条件
3. 评估Agent能力与任务匹配度
4. 制定任务分配方案
5. 记录分配决策推理过程
6. 执行任务分配
7. 监控任务执行状态
8. 处理任务异常和重分配
9. 生成任务执行报告
10. 任务完成确认与归档
```

---

## 协同效果评估能力

### Agent调度协同评估指标

吏部作为Agent调度机构，负责评估Agent调度在三省六部协同中的效果。

| 评估维度 | 指标 | 目标值 | 度量方法 |
|----------|------|--------|----------|
| 分配效率 | 任务分配平均时间 | ≤5分钟 | 时间戳差值统计 |
| 匹配准确率 | Agent能力匹配成功率 | ≥90% | 匹配结果统计 |
| 负载均衡度 | Agent负载分布标准差 | ≤0.2 | 负载数据统计 |
| 任务完成率 | 按时完成任务比例 | ≥95% | 任务完成统计 |
| Agent利用率 | Agent工作时间占比 | 70-85% | 工作时间统计 |

### Agent调度协同评估流程

```
[1] 收集调度数据
    ↓
[2] 计算调度效率指标
    ↓
[3] 分析Agent利用率
    ↓
[4] 评估匹配准确性
    ↓
[5] 生成优化建议
    ↓
输出《Agent调度协同评估报告》
```

### Agent调度协同评估报告格式

```json
{
  "evaluation_id": "EVAL-LIBU-001",
  "timestamp": "2024-01-01T00:00:00Z",
  "period": {
    "start": "2024-01-01T00:00:00Z",
    "end": "2024-01-07T23:59:59Z"
  },
  "allocation_metrics": {
    "total_allocations": 100,
    "successful_allocations": 95,
    "failed_allocations": 5,
    "avg_allocation_time_seconds": 180,
    "reallocation_count": 8
  },
  "agent_metrics": {
    "total_agents": 20,
    "active_agents": 18,
    "avg_utilization": 0.78,
    "load_balance_score": 0.85,
    "top_performers": ["agent-001", "agent-005", "agent-012"]
  },
  "matching_metrics": {
    "capability_match_rate": 0.92,
    "skill_match_rate": 0.88,
    "preference_match_rate": 0.75,
    "overall_match_score": 0.85
  },
  "tdd_metrics": {
    "red_phase_allocations": 30,
    "green_phase_allocations": 30,
    "refactor_phase_allocations": 25,
    "role_switch_count": 15,
    "role_compatibility_rate": 0.90
  },
  "recommendations": [
    {
      "category": "load_balancing",
      "priority": "medium",
      "description": "优化Agent负载分配，减少负载不均",
      "expected_impact": "预计负载均衡度提升至0.90"
    }
  ]
}
```

---

## 流水线协调能力

### 流水线Agent调度节点

吏部在白盒化7阶段流水线中负责Agent调度和任务分配。

| 阶段 | 吏部角色 | 调度内容 | Agent需求 |
|------|----------|----------|----------|
| 需求分析 | 协调 | 分配需求分析Agent | 需求分析专家 |
| SDD规范定义 | 协调 | 分配规范制定Agent | 规范制定专家 |
| 审议批准 | 支持 | 提供审议支持Agent | 审议专家 |
| 测试先行 | 主导 | 分配测试编写Agent | 测试专家 |
| 代码实现 | 主导 | 分配开发Agent | 开发专家 |
| 持续重构 | 主导 | 分配重构Agent | 重构专家 |
| 部署发布 | 支持 | 提供部署支持Agent | 运维专家 |

### 流水线Agent调度配置

```yaml
pipeline_agent_scheduling:
  scheduling_strategy:
    mode: "dynamic"
    preemptive: true
    load_aware: true
    
  agent_pool:
    requirement_analysts: 3
    specification_writers: 2
    reviewers: 2
    test_writers: 5
    developers: 8
    refactoring_experts: 3
    devops_engineers: 2
    
  scheduling_rules:
    - stage: "test_first"
      agent_type: "test_writer"
      min_count: 1
      max_count: 3
      skill_requirements: ["test_design", "boundary_testing"]
      
    - stage: "implementation"
      agent_type: "developer"
      min_count: 1
      max_count: 5
      skill_requirements: ["code_implementation", "feature_development"]
      
    - stage: "refactoring"
      agent_type: "refactoring_expert"
      min_count: 1
      max_count: 2
      skill_requirements: ["code_refactoring", "quality_optimization"]
```

### 流水线Agent调度流程

```
流水线阶段启动
    ↓
[1] 接收阶段Agent需求
    ↓
[2] 评估Agent池状态
    ↓
[3] 匹配Agent能力与需求
    ↓
[4] 执行Agent分配
    ↓
[5] 监控Agent执行状态
    ↓
[6] 处理Agent异常
    ↓
阶段完成，释放Agent
```

### 流水线Agent调度报告

```json
{
  "scheduling_id": "SCHED-PL-001",
  "timestamp": "2024-01-01T00:00:00Z",
  "pipeline_id": "PIPE-001",
  "stage": "implementation",
  "agent_allocations": [
    {
      "agent_id": "AGENT-001",
      "role": "lead_developer",
      "skills_matched": ["code_implementation", "architecture"],
      "allocation_time": "2024-01-01T10:00:00Z",
      "estimated_duration_minutes": 120
    },
    {
      "agent_id": "AGENT-005",
      "role": "developer",
      "skills_matched": ["code_implementation", "unit_testing"],
      "allocation_time": "2024-01-01T10:00:00Z",
      "estimated_duration_minutes": 120
    }
  ],
  "scheduling_metrics": {
    "matching_score": 0.92,
    "load_balance_score": 0.88,
    "allocation_time_seconds": 45
  },
  "issues": []
}
```

---

## 智能调度支持

### 智能匹配算法

```python
def calculate_agent_match_score(agent, task):
    weights = {
        "capability_match": 0.35,
        "skill_match": 0.25,
        "load_factor": 0.20,
        "historical_performance": 0.15,
        "preference_match": 0.05
    }
    
    scores = {
        "capability_match": evaluate_capability_match(agent, task),
        "skill_match": evaluate_skill_match(agent, task),
        "load_factor": 1.0 - agent.current_load,
        "historical_performance": agent.performance_score,
        "preference_match": evaluate_preference(agent, task)
    }
    
    return sum(scores[k] * weights[k] for k in weights)
```

### Agent能力矩阵

```json
{
  "capability_matrix": {
    "AGENT-001": {
      "primary_skills": ["code_implementation", "architecture", "code_review"],
      "secondary_skills": ["testing", "documentation"],
      "tdd_roles": ["developer", "refactoring_expert"],
      "experience_level": "expert",
      "availability": 0.85,
      "current_load": 0.3
    },
    "AGENT-002": {
      "primary_skills": ["test_design", "test_automation", "boundary_testing"],
      "secondary_skills": ["code_implementation"],
      "tdd_roles": ["test_writer"],
      "experience_level": "senior",
      "availability": 0.90,
      "current_load": 0.2
    }
  }
}
```

---

## 增强功能集成

### 与provincial_coordinator集成

吏部通过provincial_coordinator.py实现Agent调度的自动化和协同：

```python
from scripts.provincial_coordinator import (
    SmartDispatcher,
    TaskRequirement,
    TaskPriority
)

dispatcher = SmartDispatcher()

def allocate_agent_for_task(task_id: str, required_capabilities: dict):
    requirement = TaskRequirement(
        task_id=task_id,
        required_capabilities=required_capabilities,
        preferred_specializations=["development"],
        priority=TaskPriority.HIGH
    )
    
    decision = dispatcher.find_best_match(requirement, "ministry")
    
    return {
        "assigned_agent": decision.assigned_entity,
        "match_score": decision.overall_score,
        "reasoning": decision.reasoning
    }
```

---

## 调度质量保障

### 调度质量检查清单

```
□ Agent能力与任务需求匹配
□ Agent负载在合理范围内
□ 分配决策有充分依据
□ TDD角色分配合理
□ 调度过程记录完整
□ 异常处理机制有效
□ 绩效追踪持续进行
□ 优化建议及时实施
```

### 调度质量评分

| 评分项 | 权重 | 评分标准 |
|--------|------|----------|
| 匹配准确性 | 30% | Agent能力与任务需求高度匹配 |
| 负载均衡度 | 25% | Agent负载分布合理 |
| 分配效率 | 20% | 分配时间在合理范围内 |
| 任务完成率 | 15% | 任务按时完成比例高 |
| 持续优化 | 10% | 持续改进调度策略 |
1. 接收尚书省的任务分配指令
2. 分析任务需求和约束条件
3. 评估Agent能力与任务匹配度
4. 制定任务分配方案
5. 记录分配决策推理过程
6. 执行任务分配
7. 监控任务执行状态
8. 处理任务异常和重分配
9. 生成任务执行报告
10. 任务完成确认与归档
```

## 任务分配决策流程（增强版）

### 任务分析阶段

```
任务分析步骤:
  1. 任务类型识别
     - 功能开发任务
     - Bug修复任务
     - 重构任务
     - 测试任务
     - 文档任务
  
  2. 任务复杂度评估
     - 简单任务: 单一模块，工作量<4小时
     - 中等任务: 多模块协作，工作量4-16小时
     - 复杂任务: 跨系统，工作量>16小时
  
  3. 任务依赖分析
     - 前置任务识别
     - 并行任务识别
     - 依赖图构建
  
  4. 技能需求分析
     - 所需技能列表
     - 技能级别要求
     - 特殊技能需求
```

### Agent能力评估

```json
{
  "agent_capability_assessment": {
    "agent_id": "agent-001",
    "capabilities": {
      "skills": [
        {"name": "python", "level": "expert", "score": 0.95},
        {"name": "javascript", "level": "intermediate", "score": 0.75},
        {"name": "database", "level": "expert", "score": 0.90}
      ],
      "experience": {
        "total_tasks": 150,
        "success_rate": 0.95,
        "avg_completion_time_ratio": 0.85
      },
      "availability": {
        "current_load": 0.3,
        "max_capacity": 1.0,
        "available_slots": 3
      },
      "specializations": ["backend", "api", "database"]
    },
    "overall_score": 0.88
  }
}
```

### 任务分配策略

| 策略类型 | 适用场景 | 分配规则 |
|----------|----------|----------|
| 技能匹配优先 | 技术难度高的任务 | 选择技能匹配度最高的Agent |
| 负载均衡优先 | 大量并行任务 | 选择当前负载最低的Agent |
| 经验优先 | 复杂任务 | 选择相关经验最丰富的Agent |
| 混合策略 | 一般任务 | 综合评估技能、负载、经验 |

### 任务分配决策输出

```json
{
  "allocation_decision_id": "AD-001",
  "timestamp": "2024-01-01T00:00:00Z",
  "task_id": "TASK-001",
  "decision": {
    "selected_agent": "agent-001",
    "allocation_score": 0.92,
    "decision_factors": {
      "skill_match": 0.95,
      "load_balance": 0.90,
      "experience_match": 0.92
    },
    "estimated_completion_time": "4 hours",
    "confidence_level": "high"
  },
  "alternatives": [
    {"agent_id": "agent-002", "score": 0.85, "reason": "技能匹配度稍低"},
    {"agent_id": "agent-003", "score": 0.78, "reason": "当前负载较高"}
  ],
  "risk_assessment": {
    "risk_level": "low",
    "mitigation_plan": "无需特殊缓解措施"
  }
}
```

## 任务监控与调度（增强版）

### 任务状态监控

```json
{
  "task_monitoring": {
    "monitor_id": "MON-001",
    "timestamp": "2024-01-01T00:00:00Z",
    "active_tasks": [
      {
        "task_id": "TASK-001",
        "assigned_agent": "agent-001",
        "status": "in_progress",
        "progress": 0.65,
        "started_at": "2024-01-01T08:00:00Z",
        "estimated_completion": "2024-01-01T12:00:00Z",
        "health_status": "healthy",
        "blockers": []
      }
    ],
    "summary": {
      "total_active": 5,
      "on_track": 4,
      "at_risk": 1,
      "blocked": 0
    }
  }
}
```

### 异常处理机制

| 异常类型 | 检测条件 | 处理策略 |
|----------|----------|----------|
| 超时风险 | 预计完成时间超过截止时间 | 资源调配或任务拆分 |
| Agent不可用 | Agent状态异常 | 任务重分配 |
| 依赖阻塞 | 前置任务未完成 | 优先级调整或并行处理 |
| 技能不匹配 | 执行中发现技能差距 | 协作支持或重新分配 |

### 任务重分配流程

```
重分配触发条件:
  - Agent不可用
  - 任务优先级变更
  - 执行失败需要重试
  - 资源重新调配

重分配步骤:
  1. 评估当前任务状态
  2. 识别可用替代Agent
  3. 计算重分配成本
  4. 执行重分配决策
  5. 通知相关方
  6. 更新任务状态
  7. 记录重分配日志
```

## Agent分配流程

### 1. 任务接收与分析
```
输入: 任务描述、优先级、截止时间、技能要求
处理:
  - 解析任务类型（开发/测试/重构/部署）
  - 提取技能要求清单
  - 评估任务复杂度（简单/中等/复杂）
  - 确定优先级（P0紧急/P1高/P2中/P3低）
输出: 任务分析报告
```

### 2. Agent能力匹配
```
步骤:
  1. 查询Agent能力注册表
  2. 按技能要求筛选候选Agent
  3. 检查Agent当前负载状态
  4. 计算匹配度得分
     匹配度 = 技能匹配分 × 0.4 + 负载可用分 × 0.3 + 历史绩效分 × 0.3
  5. 生成候选Agent排序列表
输出: 候选Agent列表（按匹配度降序）
```

### 3. 分配决策
```
决策规则:
  - 单Agent任务: 选择匹配度最高的Agent
  - 多Agent任务: 按技能互补原则组建团队
  - 冲突处理: 高优先级任务优先分配
  - 备选机制: 保留2-3个备选Agent
```

### 4. 分配执行与确认
```
执行步骤:
  1. 发送任务分配通知
  2. 等待Agent确认（超时: 5分钟）
  3. 确认成功: 更新Agent状态为"忙碌"
  4. 确认失败: 选择备选Agent重新分配
  5. 记录分配日志
```

### 5. 执行监控
```
监控内容:
  - 任务进度跟踪
  - 超时预警（超过预估时间50%）
  - 异常状态处理
  - 绩效数据收集
```

## TDD 角色分配

### TDD 流程角色定义

| 角色 | 职责 | 技能要求 | 适用场景 |
|------|------|----------|----------|
| 测试编写者 | 编写单元测试、集成测试用例 | 测试框架、用例设计、边界分析 | 兵部测试先行阶段 |
| 红阶段开发者 | 分析失败测试，理解需求 | 需求分析、测试解读、代码阅读 | TDD 红阶段 |
| 绿阶段开发者 | 编写最小代码使测试通过 | 编码能力、快速实现、简单设计 | TDD 绿阶段 |
| 重构专家 | 优化代码结构，保持测试通过 | 重构模式、代码异味识别、设计模式 | TDD 重构阶段 |
| 规范验证者 | 验证代码是否符合规范 | 规范理解、代码审查、一致性检查 | SDD 规范验证 |

### TDD 角色分配策略

#### 按 TDD 阶段分配
```
红阶段（测试编写）:
  - 分配给: 测试编写者
  - 技能要求: 精通测试框架，擅长边界值分析
  - 输出: 失败的测试用例

绿阶段（代码实现）:
  - 分配给: 绿阶段开发者
  - 技能要求: 快速编码能力，理解简单设计
  - 输出: 通过测试的最小代码

重构阶段（代码优化）:
  - 分配给: 重构专家
  - 技能要求: 精通重构技术，识别代码异味
  - 输出: 优化后的代码（保持测试通过）
```

#### 按任务复杂度分配 TDD 角色
```
简单任务（<2小时）:
  - 单角色: 全栈开发者（兼顾测试和实现）
  - 流程: 快速红-绿-重构循环

中等任务（2-8小时）:
  - 双角色: 测试编写者 + 开发者
  - 流程: 先写测试，再实现，最后重构

复杂任务（>8小时）:
  - 多角色团队:
    - 测试架构师: 设计测试策略
    - 测试编写者: 编写具体用例
    - 开发者: 实现功能
    - 重构专家: 持续优化
  - 流程: 分模块迭代，每个模块完成红-绿-重构
```

### TDD 团队协作模式

#### 配对编程模式
```
角色配对:
  - 测试员-开发者配对: 测试员写测试，开发者实现
  - 开发者-重构者配对: 开发者实现，重构者优化
  - 新手-专家配对: 新手学习，专家指导

协作流程:
  1. 测试员编写测试（红）
  2. 开发者编写代码（绿）
  3. 重构者优化代码（重构）
  4. 循环往复，角色可轮换
```

#### 并行开发模式
```
适用场景: 大型项目，多个独立模块

分工策略:
  - 测试团队: 并行编写各模块测试
  - 开发团队: 并行实现各模块功能
  - 集成团队: 负责模块集成测试

协调机制:
  - 每日同步会议
  - 测试用例评审
  - 集成点协调
```

## 角色定义模板

### Agent角色定义规范
```yaml
agent_definition:
  id: "agent-xxx"
  name: "Agent名称"
  type: "specialist|generalist|coordinator"
  
  capabilities:
    primary_skills:
      - skill_name: "技能名称"
        proficiency: "expert|proficient|intermediate|beginner"
        experience_years: 数字
    secondary_skills:
      - skill_name: "技能名称"
        proficiency: "熟练度"
  
  tdd_capabilities:
    test_writing: "expert|proficient|intermediate|beginner"
    red_phase: "expert|proficient|intermediate|beginner"
    green_phase: "expert|proficient|intermediate|beginner"
    refactoring: "expert|proficient|intermediate|beginner"
    test_frameworks: ["jest", "pytest", "junit", "nunit"]
    
  constraints:
    max_concurrent_tasks: 数字
    preferred_task_types: ["类型列表"]
    excluded_task_types: ["排除类型"]
    working_hours: "时区/时间段"
    preferred_tdd_phase: ["red", "green", "refactor"]
  
  performance_metrics:
    total_tasks_completed: 数字
    success_rate: 百分比
    average_completion_time: "平均耗时"
    customer_satisfaction: 评分
    tdd_metrics:
      tests_written: 数字
      test_coverage_avg: 百分比
      refactoring_count: 数字
  
  metadata:
    created_at: "创建时间"
    last_updated: "更新时间"
    version: "版本号"
```

### 角色类型说明

| 类型 | 职责 | 适用场景 |
|------|------|----------|
| specialist | 专精某一领域 | 复杂技术问题、深度开发 |
| generalist | 多领域通用 | 简单任务、快速响应 |
| coordinator | 协调多个Agent | 大型项目、跨团队协作 |

### 能力等级定义

| 等级 | 描述 | 任务复杂度 |
|------|------|------------|
| expert | 深度专家，可独立解决复杂问题 | 复杂 |
| proficient | 熟练掌握，可独立完成任务 | 中等 |
| intermediate | 基本掌握，需适度指导 | 简单 |
| beginner | 入门级别，需全程指导 | 学习任务 |

## 任务分配指南

### 任务类型与Agent匹配矩阵

| 任务类型 | 推荐Agent类型 | 必备技能 | 优先级权重 |
|----------|---------------|----------|------------|
| 新功能开发 | specialist | 编码、架构设计 | 1.0 |
| Bug修复 | generalist | 调试、代码分析 | 1.2 |
| 代码重构 | specialist | 重构模式、测试 | 0.8 |
| 测试编写 | generalist | 测试框架、用例设计 | 0.9 |
| 文档编写 | generalist | 技术写作 | 0.7 |
| 部署运维 | specialist | CI/CD、运维 | 1.1 |
| 安全审计 | specialist | 安全测试、渗透 | 1.3 |
| TDD测试编写 | specialist | 测试框架、边界分析 | 1.0 |
| TDD代码实现 | generalist | 快速编码、简单设计 | 1.0 |
| TDD重构优化 | specialist | 重构模式、代码异味 | 0.9 |

### 分配策略

#### 按优先级分配
```
P0紧急任务:
  - 立即分配，不考虑负载均衡
  - 选择最匹配的可用Agent
  - 必要时中断低优先级任务

P1高优先级:
  - 优先分配，考虑负载
  - 选择匹配度前3的Agent
  - 设置加急监控

P2中优先级:
  - 正常分配流程
  - 考虑负载均衡
  - 常规监控

P3低优先级:
  - 填充式分配
  - 可用于Agent培训
  - 最低监控频率
```

#### 按复杂度分配
```
简单任务（<2小时）:
  - 分配给intermediate级别Agent
  - 可作为学习任务

中等任务（2-8小时）:
  - 分配给proficient级别Agent
  - 常规流程执行

复杂任务（>8小时）:
  - 分配给expert级别Agent
  - 或组建多Agent团队
  - 需要详细规划
```

### 团队组建规则

```yaml
team_formation:
  minimum_size: 2
  maximum_size: 5
  
  roles:
    - role: "技术负责人"
      requirement: "expert级别"
      count: 1
    - role: "核心开发者"
      requirement: "proficient及以上"
      count: "2-3"
    - role: "辅助开发者"
      requirement: "intermediate及以上"
      count: "0-1"
  
  tdd_team_roles:
    - role: "测试架构师"
      requirement: "expert级别"
      responsibility: "设计测试策略和框架"
    - role: "测试编写者"
      requirement: "proficient及以上"
      responsibility: "编写单元测试和集成测试"
    - role: "功能开发者"
      requirement: "proficient及以上"
      responsibility: "实现功能使测试通过"
    - role: "重构专家"
      requirement: "expert级别"
      responsibility: "优化代码结构"
  
  principles:
    - "技能互补原则: 团队成员技能覆盖任务需求"
    - "经验搭配原则: 高级带中级"
    - "负载均衡原则: 避免过度集中"
    - "TDD角色完整原则: 红绿重构角色齐全"
```

### 分配冲突处理

```
冲突场景处理流程:

1. 多任务竞争同一Agent:
   - 比较任务优先级
   - 高优先级优先
   - 同优先级按到达时间排序
   - 考虑任务预估时间，短任务优先

2. Agent不可用:
   - 检查预计恢复时间
   - 短时间等待（<30分钟）: 排队
   - 长时间等待（>30分钟）: 重新分配

3. 技能匹配不足:
   - 放宽匹配条件
   - 考虑培训机会
   - 申请外部技能支持

4. TDD角色冲突:
   - 优先保证测试编写者
   - 红绿阶段可合并角色
   - 重构阶段必须独立
```

## TDD 任务分配最佳实践

### 测试驱动任务拆分
```
任务拆分原则:
  - 按功能点拆分: 每个功能点一个测试用例
  - 按边界条件拆分: 正常/异常/边界各一个用例
  - 按集成点拆分: 单元测试 → 集成测试 → E2E测试

分配策略:
  - 独立功能点: 分配给单个Agent
  - 关联功能点: 分配给同一团队
  - 跨模块功能: 分配给协调者统筹
```

### 动态角色调整
```
调整时机:
  - 测试编写阶段: 需要测试专家
  - 代码实现阶段: 需要开发专家
  - 重构优化阶段: 需要重构专家

调整策略:
  - 同一Agent可承担多个角色
  - 角色切换时进行知识传递
  - 保持上下文连续性
```

## 透明度记录要求
### Agent分配决策记录
- 记录Agent选择依据：包括Agent能力匹配度、当前负载状态、历史绩效数据
- 记录任务分配推理过程：包括任务需求分析、候选Agent评估、最终选择理由
- 记录TDD角色分配依据：包括角色需求分析、Agent TDD能力评估、角色匹配度

### 记录内容规范
- 决策时间戳
- 任务特征描述
- 候选Agent列表及评估分数
- TDD角色分配方案
- 选择理由详细说明
- 预期执行效果

## 下属四司
- xuansi（选司）：Agent 选择和任务分配
- kaosi（考司）：绩效评估和考核
- xunsi（勋司）：奖励机制
- juesi（爵司）：权限管理

## 协同调用接口

### 接口定义

吏部作为Agent调度机构，提供以下协同调用接口供其他技能调用：

| 接口名称 | 接口描述 | 调用方 |
|----------|----------|--------|
| `assign_agent` | Agent分配接口 | 尚书省、外部技能 |
| `get_agent_status` | Agent状态查询接口 | 尚书省 |
| `assign_tdd_role` | TDD角色分配接口 | 兵部、工部、刑部 |
| `coordinate_external_agent` | 外部Agent协调接口 | 尚书省 |

### 输入参数规范

#### Agent分配接口参数

```json
{
  "interface": "assign_agent",
  "version": "1.0.0",
  "timestamp": "2024-01-01T00:00:00Z",
  "caller": "调用方标识",
  "parameters": {
    "task": {
      "task_id": "任务ID",
      "task_type": "development|testing|refactoring|deployment",
      "description": "任务描述",
      "priority": "P0|P1|P2|P3",
      "required_skills": ["技能列表"],
      "estimated_duration": "预估时长"
    },
    "constraints": {
      "max_agents": 3,
      "preferred_agents": ["偏好Agent列表"],
      "excluded_agents": ["排除Agent列表"]
    }
  }
}
```

#### TDD角色分配接口参数

```json
{
  "interface": "assign_tdd_role",
  "version": "1.0.0",
  "timestamp": "2024-01-01T00:00:00Z",
  "caller": "调用方标识",
  "parameters": {
    "tdd_phase": "red|green|refactor",
    "feature_id": "功能点ID",
    "required_capabilities": {
      "test_writing": "expert|proficient|intermediate",
      "coding": "expert|proficient|intermediate",
      "refactoring": "expert|proficient|intermediate"
    },
    "team_mode": "solo|pair|team"
  }
}
```

### 输出格式规范

```json
{
  "interface": "assign_agent",
  "call_id": "ASSIGN-001",
  "timestamp": "2024-01-01T00:00:00Z",
  "status": "success|failure|partial",
  "result": {
    "assigned_agents": [
      {
        "agent_id": "AGENT-001",
        "agent_name": "Agent名称",
        "role": "primary|secondary|support",
        "match_score": 0.95
      }
    ],
    "assignment_reason": "分配理由",
    "estimated_start": "预计开始时间"
  }
}
```

### 调用示例

```bash
# 调用Agent分配接口
调用 ./SKILL.md --interface=assign_agent \
  --task='{"task_id":"TASK-001","task_type":"development","priority":"P1"}' \
  --constraints='{"max_agents":2}'

# 调用TDD角色分配接口
调用 ./SKILL.md --interface=assign_tdd_role \
  --tdd-phase="red" \
  --feature-id="F-001" \
  --team-mode="pair"
```

---

## Agent集成配置

详细内容请参考 [Agency-Agents集成配置](../../subskills/daili_jicheng.md)

---

## Agent池管理（增强版）

### Agent池状态监控

```json
{
  "pool_status": {
    "timestamp": "2024-01-01T00:00:00Z",
    "total_agents": 20,
    "agents_by_status": {
      "available": 12,
      "busy": 6,
      "offline": 2
    },
    "agents_by_type": {
      "specialist": 8,
      "generalist": 10,
      "coordinator": 2
    },
    "agents_by_tdd_phase": {
      "red_phase_capable": 15,
      "green_phase_capable": 18,
      "refactor_phase_capable": 10
    },
    "load_metrics": {
      "average_load": 0.45,
      "peak_load": 0.85,
      "load_trend": "increasing|stable|decreasing"
    }
  }
}
```

### 动态负载均衡策略

```yaml
load_balancing:
  strategy: "weighted_round_robin"
  
  weights:
    agent_capability: 0.35
    current_load: 0.25
    historical_performance: 0.20
    task_affinity: 0.20
    
  rebalancing:
    trigger_threshold: 0.80
    check_interval_seconds: 60
    min_rebalance_interval_seconds: 300
    
  rules:
    - name: "prevent_overload"
      condition: "agent_load > 0.9"
      action: "exclude_from_assignment"
      
    - name: "prefer_low_load"
      condition: "multiple_candidates_available"
      action: "prefer_lower_load_agent"
      
    - name: "task_affinity"
      condition: "agent_has_history_with_task_type"
      action: "increase_weight_by_10%"
```

### Agent健康检查

```yaml
health_check:
  heartbeat_interval_seconds: 30
  timeout_seconds: 60
  retry_count: 3
  
  checks:
    - name: "responsiveness"
      type: "ping"
      timeout_ms: 5000
      
    - name: "task_progress"
      type: "status_query"
      timeout_ms: 10000
      
    - name: "resource_usage"
      type: "metrics_query"
      timeout_ms: 5000
      
  actions_on_failure:
    - step: "mark_unhealthy"
      after_retries: 3
    - step: "reassign_tasks"
      condition: "tasks_in_progress"
    - step: "notify_admin"
      condition: "critical_agent"
```

---

## 绩效追踪增强

### 绩效指标体系

```json
{
  "performance_framework": {
    "dimensions": {
      "task_completion": {
        "metrics": [
          "completion_rate",
          "on_time_rate",
          "quality_score"
        ],
        "weight": 0.30
      },
      "tdd_compliance": {
        "metrics": [
          "test_first_rate",
          "red_green_cycle_time",
          "refactor_frequency"
        ],
        "weight": 0.25
      },
      "code_quality": {
        "metrics": [
          "defect_rate",
          "code_review_pass_rate",
          "technical_debt_ratio"
        ],
        "weight": 0.25
      },
      "collaboration": {
        "metrics": [
          "handoff_success_rate",
          "communication_score",
          "knowledge_sharing"
        ],
        "weight": 0.20
      }
    },
    "scoring": {
      "excellent": ">= 0.90",
      "good": ">= 0.75",
      "satisfactory": ">= 0.60",
      "needs_improvement": "< 0.60"
    }
  }
}
```

### 绩效报告模板

```json
{
  "performance_report": {
    "report_id": "PERF-001",
    "period": {
      "start": "2024-01-01T00:00:00Z",
      "end": "2024-01-31T23:59:59Z"
    },
    "agent_id": "AGENT-001",
    "summary": {
      "overall_score": 0.85,
      "rating": "good",
      "tasks_completed": 25,
      "total_hours": 120
    },
    "dimension_scores": {
      "task_completion": {
        "score": 0.88,
        "details": {
          "completion_rate": 0.96,
          "on_time_rate": 0.84,
          "quality_score": 0.85
        }
      },
      "tdd_compliance": {
        "score": 0.82,
        "details": {
          "test_first_rate": 0.92,
          "red_green_cycle_time_minutes": 22,
          "refactor_frequency": 0.68
        }
      },
      "code_quality": {
        "score": 0.86,
        "details": {
          "defect_rate": 0.04,
          "code_review_pass_rate": 0.92,
          "technical_debt_ratio": 0.12
        }
      },
      "collaboration": {
        "score": 0.83,
        "details": {
          "handoff_success_rate": 0.88,
          "communication_score": 0.85,
          "knowledge_sharing_count": 5
        }
      }
    },
    "improvement_areas": [
      {
        "area": "refactor_frequency",
        "current": 0.68,
        "target": 0.80,
        "suggestion": "增加重构阶段的投入时间"
      }
    ],
    "recognition": [
      "测试先行执行率优秀",
      "代码审查通过率高"
    ]
  }
}
```

---

## 智能调度算法

### 任务优先级计算

```python
def calculate_task_priority(task, context):
    score = 0.0
    
    score += task.business_value * 0.30
    score += (1 - task.dependency_depth / max_depth) * 0.20
    score += task.deadline_urgency * 0.20
    score += task.risk_score * 0.15
    score += context.resource_availability * 0.15
    
    return score
```

### Agent匹配算法

```python
def calculate_agent_match_score(agent, task):
    score = 0.0
    
    skill_match = calculate_skill_match(agent.skills, task.required_skills)
    score += skill_match * 0.40
    
    load_score = 1 - (agent.current_load / agent.max_capacity)
    score += load_score * 0.30
    
    performance_score = agent.historical_performance_score
    score += performance_score * 0.20
    
    affinity_score = calculate_task_affinity(agent, task)
    score += affinity_score * 0.10
    
    return score
```

### 团队组建算法

```yaml
team_formation_algorithm:
  step_1_analyze_requirements:
    - identify_required_skills
    - estimate_complexity
    - determine_team_size_range
    
  step_2_select_lead:
    criteria:
      - expert_level_in_primary_skill
      - leadership_experience
      - availability
      
  step_3_fill_core_roles:
    strategy: "skill_coverage_optimization"
    constraints:
      - minimize_skill_overlap
      - balance_experience_levels
      
  step_4_add_support:
    condition: "team_size > 3"
    criteria:
      - complementary_skills
      - learning_opportunity
      
  step_5_validate:
    checks:
      - all_skills_covered
      - tdd_roles_assigned
      - load_balanced
```

---

## 最佳实践提取器集成

### 概述

吏部集成了最佳实践提取器（Best Practice Extractor），用于从高质量代码中提取可复用模式，并生成最佳实践文档，为Agent调度和任务分配提供决策支持。

### 核心功能

#### 1. 代码模式识别

识别代码中的设计模式、代码结构、命名规范等：

```python
from skillscripts.learning.best_practice_extractor import BestPracticeExtractor

extractor = BestPracticeExtractor()

# 识别代码模式
patterns = extractor.recognize_code_patterns(
    code_content=source_code,
    language="python"
)

# 识别结果包括：
# - 设计模式（单例、工厂、观察者等）
# - 代码结构（类、函数、模块、继承、组合）
# - 命名规范（类命名、函数命名、变量命名、常量命名）
# - 代码质量指标（文档、复杂度、测试、错误处理）
# - 反模式检测（上帝类、长方法、魔法数字等）
```

#### 2. 最佳实践提取

从成功模式中提取最佳实践：

```python
from skillscripts.learning.pattern_recognizer import PatternRecognizer

recognizer = PatternRecognizer()
extractor = BestPracticeExtractor(pattern_recognizer=recognizer)

# 识别成功模式
pattern = recognizer.recognize_success_pattern(
    execution_data={
        "task_type": "code_review",
        "success_rate": 0.95,
        "execution_time": 120
    },
    context={"language": "python"}
)

# 提取最佳实践
practice = extractor.extract_code_practice(
    pattern,
    code_analysis={
        "complexity": 8,
        "test_coverage": 85,
        "documentation": 0.9
    }
)
```

#### 3. 最佳实践文档生成

自动生成最佳实践文档（支持Markdown、HTML、JSON格式）：

```python
# 生成Markdown文档
markdown_doc = extractor.generate_practice_document(
    practice_id=practice.practice_id,
    output_format="markdown",
    include_examples=True
)

# 生成HTML文档
html_doc = extractor.generate_practice_document(
    practice_id=practice.practice_id,
    output_format="html",
    include_examples=True
)

# 生成JSON文档
json_doc = extractor.generate_practice_document(
    practice_id=practice.practice_id,
    output_format="json",
    include_examples=True
)
```

#### 4. 模式适用性分析

分析模式在特定上下文中的适用性：

```python
# 分析模式适用性
analysis = extractor.analyze_pattern_applicability(
    pattern=pattern,
    target_context={
        "language": "python",
        "framework": "django",
        "scale": "large"
    },
    constraints=["avoid singleton", "must be scalable"]
)

# 分析结果包括：
# - 适用性得分
# - 上下文匹配度
# - 约束合规性
# - 风险识别
# - 建议生成
# - 需要的适配
```

#### 5. 导出到礼部规范库

将最佳实践导出到礼部规范库：

```python
# 导出到礼部规范库
exported_files = extractor.export_practices_to_standards(
    output_dir=".trae/skills/sanliu/shangshusheng/libu/best_practices",
    categories=[PracticeCategory.CODE, PracticeCategory.ARCHITECTURE],
    min_quality=PracticeQuality.GOOD
)
```

### 与Agent调度的集成

#### 基于最佳实践的Agent选择

吏部在Agent调度时，可以参考最佳实践提取器的分析结果：

```python
def select_agent_with_best_practices(task, agents):
    """基于最佳实践选择Agent"""
    
    # 1. 分析任务需求
    task_patterns = extractor.recognize_code_patterns(
        task.code_sample,
        language=task.language
    )
    
    # 2. 评估Agent历史实践
    agent_scores = {}
    for agent in agents:
        # 获取Agent的历史最佳实践
        agent_practices = get_agent_practices(agent.id)
        
        # 计算匹配度
        match_score = calculate_pattern_match(
            task_patterns,
            agent_practices
        )
        
        agent_scores[agent.id] = match_score
    
    # 3. 选择最佳匹配的Agent
    best_agent_id = max(agent_scores, key=agent_scores.get)
    
    return {
        "agent_id": best_agent_id,
        "match_score": agent_scores[best_agent_id],
        "reasoning": f"Agent历史实践与任务模式匹配度最高"
    }
```

#### 任务分配决策支持

```python
def allocate_task_with_practice_analysis(task, context):
    """基于实践分析的任务分配"""
    
    # 1. 分析任务模式
    task_patterns = extractor.recognize_code_patterns(
        task.code_content,
        language=context.get("language", "python")
    )
    
    # 2. 查找相关最佳实践
    relevant_practices = extractor.get_top_practices(
        category=PracticeCategory.CODE,
        limit=5
    )
    
    # 3. 分析实践适用性
    practice_recommendations = []
    for practice in relevant_practices:
        analysis = extractor.analyze_pattern_applicability(
            pattern=practice,
            target_context=context
        )
        
        if analysis["applicability_score"] > 0.7:
            practice_recommendations.append({
                "practice": practice,
                "analysis": analysis
            })
    
    # 4. 生成分配建议
    allocation_recommendation = {
        "task_id": task.id,
        "pattern_analysis": task_patterns,
        "recommended_practices": practice_recommendations,
        "agent_requirements": extract_agent_requirements(task_patterns)
    }
    
    return allocation_recommendation
```

### 最佳实践库管理

#### 实践质量评估

```python
def evaluate_practice_quality(practice_id):
    """评估实践质量"""
    
    quality, score = extractor.evaluate_practice_quality(
        practice_id,
        additional_evidence={
            "success": True,
            "metrics": {
                "execution_time": 120,
                "success_rate": 0.95
            }
        }
    )
    
    return {
        "practice_id": practice_id,
        "quality": quality.value,
        "score": score,
        "recommendation": "推荐使用" if score > 0.8 else "谨慎使用"
    }
```

#### 实践验证

```python
def verify_practice(practice_id, verification_result):
    """验证实践"""
    
    success = extractor.verify_practice(
        practice_id,
        verification_data={
            "success": verification_result.success,
            "metrics": verification_result.metrics,
            "feedback": verification_result.feedback
        }
    )
    
    return {
        "practice_id": practice_id,
        "verified": success,
        "status": "验证成功" if success else "验证失败"
    }
```

### 最佳实践推荐引擎

#### 基于上下文的实践推荐

```python
def recommend_practices_for_context(context, objectives):
    """基于上下文推荐最佳实践"""
    
    recommendations = extractor.recommend_practices(
        context=context,
        objectives=objectives,
        constraints=["avoid anti-patterns"],
        limit=5
    )
    
    return {
        "context": context,
        "objectives": objectives,
        "recommendations": [
            {
                "practice_id": rec["practice_id"],
                "title": rec["title"],
                "relevance_score": rec["relevance_score"],
                "reasons": rec["reasons"],
                "warnings": rec["warnings"]
            }
            for rec in recommendations
        ]
    }
```

### 集成配置

#### 配置文件

```yaml
best_practice_extractor:
  enabled: true
  
  storage:
    path: ".trae/skills/sanliu/shangshusheng/libu/best_practices"
    auto_save: true
    backup_enabled: true
    
  extraction:
    min_confidence: "high"
    min_occurrences: 3
    quality_threshold: 0.7
    
  pattern_recognition:
    languages: ["python", "javascript", "typescript"]
    design_patterns: true
    code_structures: true
    naming_conventions: true
    anti_patterns: true
    
  document_generation:
    default_format: "markdown"
    include_examples: true
    auto_export: true
    
  integration:
    agent_selection: true
    task_allocation: true
    performance_tracking: true
```

### 使用示例

#### 完整工作流程

```python
# 1. 初始化提取器
from skillscripts.learning.best_practice_extractor import BestPracticeExtractor
from skillscripts.learning.pattern_recognizer import PatternRecognizer

recognizer = PatternRecognizer()
extractor = BestPracticeExtractor(
    pattern_recognizer=recognizer,
    storage_path=".trae/skills/sanliu/shangshusheng/libu/best_practices/practices.json"
)

# 2. 识别代码模式
code_sample = open("example.py").read()
patterns = extractor.recognize_code_patterns(code_sample, "python")

# 3. 提取最佳实践
if patterns["overall_score"] > 0.7:
    pattern = recognizer.recognize_success_pattern(
        {"code": code_sample, "quality": patterns["overall_score"]},
        context={"language": "python"}
    )
    
    if pattern:
        practice = extractor.extract_code_practice(pattern)

# 4. 生成文档
doc = extractor.generate_practice_document(
    practice.practice_id,
    output_format="markdown"
)

# 5. 导出到规范库
exported = extractor.export_practices_to_standards(
    output_dir=".trae/skills/sanliu/shangshusheng/libu/best_practices",
    min_quality=PracticeQuality.GOOD
)

# 6. 分析适用性
analysis = extractor.analyze_pattern_applicability(
    pattern,
    target_context={"language": "python", "scale": "large"},
    constraints=["must be scalable"]
)

# 7. 推荐实践
recommendations = extractor.recommend_practices(
    context={"language": "python", "project_type": "web"},
    objectives=["maintainability", "testability"],
    limit=5
)
```

### 性能指标

| 指标 | 目标值 | 说明 |
|------|--------|------|
| 模式识别准确率 | ≥85% | 正确识别设计模式的比率 |
| 实践提取质量 | ≥0.8 | 提取的最佳实践平均质量分数 |
| 文档生成速度 | ≤1秒 | 生成单个实践文档的时间 |
| 适用性分析准确率 | ≥80% | 正确评估模式适用性的比率 |
| 推荐相关性 | ≥0.75 | 推荐实践与上下文的相关性得分 |

### 维护与更新

#### 定期更新最佳实践库

```python
def update_best_practices():
    """定期更新最佳实践库"""
    
    # 1. 收集新的实践数据
    new_patterns = collect_recent_patterns()
    
    # 2. 提取新的最佳实践
    for pattern in new_patterns:
        practice = extractor.extract_code_practice(pattern)
        
        # 3. 验证实践质量
        if practice and practice.quality_score > 0.7:
            # 4. 添加到实践库
            extractor.verify_practice(
                practice.practice_id,
                {"success": True, "metrics": pattern.metrics}
            )
    
    # 5. 导出更新后的实践库
    extractor.export_practices_to_standards(
        output_dir=".trae/skills/sanliu/shangshusheng/libu/best_practices",
        min_quality=PracticeQuality.GOOD
    )
```

---

## 相关文档

- [代码规范](../../resources/daima_guifan.md)
- [TDD规范](../../resources/tdd_guifan.md)
- [最佳实践模板](../../resources/best_practices/)
