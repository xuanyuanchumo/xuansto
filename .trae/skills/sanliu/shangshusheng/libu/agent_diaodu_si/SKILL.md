---
name: agent_diaodu_si
description: Agent调度司，负责AI Agent任务分配、负载均衡、优先级调度。所有Agent调度通过ResourceCoordinator进行资源注册和锁获取，集成MARC资源协调体系。
---
# Agent调度司技能指令

## 职责
- AI Agent任务分配与调度
- Agent负载均衡管理
- 任务优先级排序与调度
- MARC资源协调集成：资源注册与锁获取
- 调度队列管理与死锁预防

## MARC集成规范

### 资源注册流程

```
Agent调度前必须完成资源注册：
  1. 调用 ResourceCoordinator.register_resource() 注册任务资源
  2. 调用 ResourceCoordinator.acquire_lock() 获取资源锁
  3. 执行调度决策
  4. 完成后调用 ResourceCoordinator.release_lock() 释放锁
```

### 锁获取策略

| 资源类型 | 锁类型 | 超时时间 | 重试策略 |
|----------|--------|----------|----------|
| FILE | EXCLUSIVE | 30s | 指数退避 |
| API | SHARED | 10s | 线性重试 |
| COMPUTE | EXCLUSIVE | 60s | 固定间隔 |
| TERMINAL | EXCLUSIVE | 120s | 单次尝试 |

## 工作流程

```
1. 接收任务调度请求
2. 分析任务特征（类型/优先级/复杂度/依赖）
3. 通过MARC注册任务资源
4. 获取所需资源锁
5. 评估Agent能力矩阵匹配度
6. 计算负载均衡分配方案
7. 执行调度决策
8. 释放资源锁
9. 监控执行状态
10. 记录调度日志到DecisionLog
```

## 负载均衡算法

### 权重计算公式

```python
def calculate_dispatch_weight(agent, task):
    weights = {
        "capability_match": 0.30,
        "current_load": 0.25,
        "historical_performance": 0.20,
        "task_affinity": 0.15,
        "resource_availability": 0.10
    }
    score = sum(
        evaluate_dimension(agent, task, dim) * w
        for dim, w in weights.items()
    )
    return score
```

### 调度优先级规则

| 优先级 | 触发条件 | 调度策略 |
|--------|----------|----------|
| P0 紧急 | 阻塞性Bug/安全漏洞 | 立即抢占式调度 |
| P1 高优 | 核心功能/截止临近 | 优先队列头部插入 |
| P2 中等 | 常规功能开发 | 正常FIFO调度 |
| P3 低优 | 优化/文档 | 填充式调度 |

## 调度质量指标

| 指标 | 目标值 | 度量方式 |
|------|--------|----------|
| 分配响应时间 | ≤3秒 | 时间戳差值 |
| 匹配准确率 | ≥90% | 后验统计 |
| 负载标准差 | ≤0.15 | 分布统计 |
| 锁竞争率 | ≤5% | MARC统计 |

## 协同接口

| 接口 | 描述 | 调用方 |
|------|------|--------|
| `dispatch_agent` | Agent分发 | 尚书省/各部 |
| `query_load` | 负载查询 | 尚书省 |
| `rebalance` | 负载再平衡 | 自动触发 |
