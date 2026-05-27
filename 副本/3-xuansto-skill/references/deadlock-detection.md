# 死锁检测与恢复机制

## 概述

多Agent并行执行时，Agent间可能因资源依赖形成循环等待，导致死锁。本规范定义死锁检测算法、恢复策略和事件记录机制。

## 依赖图构建

### 数据结构
Orchestrator维护Agent间依赖关系有向图（Directed Graph）：
- 节点：活跃Agent实例
- 边：Agent A等待Agent B的输出（A → B）
- 权重：等待的Token消耗量

### 依赖关系来源
1. 文件依赖：Agent A需要Agent B生成的文件
2. 数据依赖：Agent A需要Agent B的API输出
3. 知识库依赖：Agent A需要Agent B写入的知识条目
4. Spec依赖：Agent A需要Agent B完成的Spec章节

### 图更新时机
- Agent启动时：添加节点
- Agent请求其他Agent输出时：添加边
- Agent完成输出时：移除对应边
- Agent终止时：移除节点及关联边

## DFS环检测算法

### 检测频率
Runtime Supervisor每60秒执行一次依赖图环检测。

### 算法步骤
1. 从每个活跃节点出发执行深度优先搜索（DFS）
2. 维护访问状态：WHITE（未访问）、GRAY（访问中）、BLACK（已完成）
3. 遇到GRAY节点时，检测到环
4. 记录环路径和涉及的Agent

### 伪代码
```
function detectCycle(graph):
    for node in graph.nodes:
        if node.color == WHITE:
            if dfs(node):
                return cycle_path
    return null

function dfs(node):
    node.color = GRAY
    for neighbor in node.neighbors:
        if neighbor.color == GRAY:
            return extractCyclePath(node, neighbor)
        if neighbor.color == WHITE:
            if dfs(neighbor):
                return true
    node.color = BLACK
    return false
```

## 死锁恢复策略

### 恢复步骤
1. **识别让步Agent**：选择环中Token消耗最低的Agent作为让步方
2. **检查点输出**：让步Agent将当前中间结果保存至检查点
3. **释放资源**：让步Agent释放所有持有的资源锁
4. **延迟重试**：让步Agent等待依赖解除后重新执行（指数退避，初始30秒）
5. **恢复执行**：其他Agent从让步Agent的检查点输出继续

### 让步Agent选择标准
- 优先选择Token消耗最低的Agent（减少重试成本）
- 次优先选择非关键路径上的Agent
- 最后选择：若所有Agent等权，选择最先进入等待的Agent

## 死锁事件记录

### 记录格式
死锁事件记录至 `.skill-logs/deadlock-events.jsonl`，每行一条JSON记录：

```json
{
    "timestamp": "2026-05-02T10:30:00Z",
    "cycle_agents": ["AgentA", "AgentB", "AgentC"],
    "cycle_path": "AgentA→AgentB→AgentC→AgentA",
    "yielding_agent": "AgentA",
    "yield_reason": "lowest_token_consumption",
    "token_consumption": {"AgentA": 5000, "AgentB": 12000, "AgentC": 8000},
    "recovery_action": "checkpoint_and_retry",
    "retry_delay_seconds": 30,
    "resolved": true
}
```

### 升级规则
- 连续3次死锁事件涉及相同Agent组合 → 升级至人工介入
- 人工介入方式：Orchestrator暂停相关Agent，通知用户调整任务分解策略
- 升级事件记录：在deadlock-events.jsonl中添加`"escalated": true`字段

## 与Runtime Supervisor的协作

- Runtime Supervisor负责执行环检测算法
- 检测到死锁后通知Orchestrator执行恢复策略
- Orchestrator负责选择让步Agent和协调恢复
- Runtime Supervisor监控恢复过程，确认死锁解除
