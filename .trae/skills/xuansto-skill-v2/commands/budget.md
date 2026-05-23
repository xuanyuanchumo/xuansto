---
name: /budget
aliases:
  - token-budget
  - tokens
category: system
phase: "any"
description: Token预算管理与监控
trigger: 需要查看或调整Token预算时
workflow: none
---

# /budget 命令

## 命令用途

查看、调整和监控当前会话的Token预算使用情况，防止上下文溢出。

## MCP工具调用链

| 顺序 | MCP工具 | 参数 | 说明 |
|------|---------|------|------|
| 1 | token_budget | action, total_budget | 查询或调整Token预算 |
| 2 | resource_load_status | action, phase | 查看资源加载状态 |

## 降级策略

| MCP工具 | 降级方式 | 降级脚本/操作 |
|---------|----------|---------------|
| token_budget | 内联估算 | 基于消息长度估算Token使用 |
| resource_load_status | 内联状态检查 | 读取resource_state.json |

## 涉及Agent

| Agent | 角色 | 职责 |
|-------|------|------|
| Token Optimizer | 主导 | Token预算分配与优化建议 |

## 命令描述

管理当前会话的Token预算，查看使用率、调整分配、获取优化建议。Token预算控制是渐进式加载的核心机制，确保上下文窗口不被过度消耗。

## 触发条件

| 触发方式 | 说明 |
|----------|------|
| 命令输入 | 用户输入 `/budget` |
| 别名触发 | `/token-budget`, `/tokens` |
| 关键词触发 | 用户提及"Token预算"、"预算管理"、"token usage" |
| 条件触发 | Token使用率超过80%时自动提醒 |

## 命令名称与语法

```
/budget <action> [--total=<总预算>]
```

## 参数定义

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `action` | enum | 是 | — | 操作类型：status/set/recommend/report |
| `--total` | int | set时必填 | — | 设置总Token预算 |
| `--period` | enum | 否 | session | 报告周期：session/workflow |
| `--format` | enum | 否 | table | 输出格式：table/json |

## 执行流程

> 标准三步框架：1. 状态查询 → 2. 预算操作 → 3. 结果反馈

1. **状态查询**：通过token_budget工具查询当前预算使用情况
2. **预算操作**：根据action执行设置、推荐或报告操作
3. **结果反馈**：返回预算状态和优化建议

## 质量门禁

无特定质量门禁。该命令为管理类命令。

## 使用示例

### 示例1：查看预算状态

```
/budget status
```

### 示例2：设置总预算

```
/budget set --total=200000
```

### 示例3：获取推荐预算

```
/budget recommend
```

### 示例4：生成使用报告

```
/budget report --period=session
```

## 相关脚本

- scripts/token-budget-guard.py - Token预算守卫Hook
- scripts/token-dashboard.py - Token使用仪表盘

---

## 相关命令

- `/status` - 项目状态查询
- `/agent-status` - Agent状态查询
- `/decision` - 决策记录
