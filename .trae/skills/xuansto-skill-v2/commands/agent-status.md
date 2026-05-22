---
name: /agent-status
aliases:
  - agents
  - as
category: system
phase: "any"
description: Agent状态查询与管理
trigger: 需要查看Agent状态或管理Agent时
workflow: none
---

# /agent-status 命令

## 命令用途

查询Agent状态与负载信息，查看可用Agent列表、当前任务分配和资源使用情况。

## MCP工具调用链

| 顺序 | MCP工具 | 参数 | 说明 |
|------|---------|------|------|
| 1 | agent_status | - | 查询所有Agent状态和负载 |

## 降级策略

| MCP工具 | 降级方式 | 降级脚本/操作 |
|---------|----------|---------------|
| agent_status | 静态查询 | 静态注册表查找 |

## 涉及Agent

| Agent | 角色 | 职责 |
|-------|------|------|
| orchestrator | 主导 | Agent状态汇总、资源管理 |

## 命令描述

查询Agent状态与负载信息，查看可用Agent列表、当前任务分配和资源使用情况。该命令是系统管理类命令，用于监控和调试Agent系统。

## 触发条件

| 触发方式 | 说明 |
|----------|------|
| 命令输入 | 用户输入 `/agent-status` |
| 别名触发 | `/agents`, `/as` |
| 关键词触发 | 用户提及"Agent状态"、"查看Agent"、"agent status" |
| 条件触发 | 任务分配失败或Agent不可用时 |

## 命令名称与语法

```
/agent-status [--filter=<过滤>] [--format=<格式>]
```

## 参数定义

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--filter` | enum | 否 | all | 过滤条件：all/available/busy/offline |
| `--format` | enum | 否 | table | 输出格式：table/json/detailed |
| `--watch` | flag | 否 | false | 持续监控模式 |

## 执行流程

> 标准三步框架：1. 状态收集 → 2. 信息汇总 → 3. 结果展示

1. **状态收集**：通过agent_status工具收集所有Agent状态
2. **信息汇总**：汇总Agent可用性、负载、任务分配信息
3. **结果展示**：格式化输出Agent状态表

## 质量门禁

无特定质量门禁。该命令为查询类命令。

## 使用示例

### 示例1：查看所有Agent

```
/agent-status
```

### 示例2：仅查看可用Agent

```
/agent-status --filter=available
```

### 示例3：JSON格式输出

```
/agent-status --format=json
```

### 示例4：持续监控

```
/agent-status --watch
```

### 示例5：详细模式

```
/agent-status --format=detailed
```

## 相关脚本

- 无特定脚本（使用静态注册表查找作为降级方式）

---

## 相关命令

- `/status` - 项目状态查询
- `/sprint` - 启动冲刺
- `/learn` - 知识学习
