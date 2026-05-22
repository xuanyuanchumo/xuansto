---
name: /status
aliases:
  - st
  - info
category: system
phase: "any"
description: 项目状态查询
trigger: 需要查看项目状态或进度时
workflow: none
---

# /status 命令

## 命令用途

查询项目当前状态，包括工作流进度、资源负载和阶段完成情况。

## MCP工具调用链

| 顺序 | MCP工具 | 参数 | 说明 |
|------|---------|------|------|
| 1 | workflow_dispatch | action=status | 查询当前工作流状态 |
| 2 | resource_load_status | - | 查询资源负载状态 |

## 降级策略

| MCP工具 | 降级方式 | 降级脚本/操作 |
|---------|----------|---------------|
| workflow_dispatch | 内联执行 | 内联状态检查 |
| resource_load_status | 内联执行 | 内联状态检查 |

## 涉及Agent

| Agent | 角色 | 职责 |
|-------|------|------|
| orchestrator | 主导 | 状态汇总、进度报告 |

## 命令描述

查询项目当前状态，包括工作流进度、资源负载和阶段完成情况。该命令是系统管理类命令，用于了解项目整体进展。

## 触发条件

| 触发方式 | 说明 |
|----------|------|
| 命令输入 | 用户输入 `/status` |
| 别名触发 | `/st`, `/info` |
| 关键词触发 | 用户提及"项目状态"、"查看进度"、"status" |
| 条件触发 | 需要了解项目整体进展时 |

## 命令名称与语法

```
/status [--detail=<详细程度>] [--phase=<阶段>]
```

## 参数定义

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--detail` | enum | 否 | summary | 详细程度：summary/detailed/full |
| `--phase` | enum | 否 | current | 查询阶段：current/all/specific |
| `--format` | enum | 否 | table | 输出格式：table/json/markdown |

## 执行流程

> 标准三步框架：1. 状态收集 → 2. 信息汇总 → 3. 结果展示

1. **状态收集**：通过workflow_dispatch和resource_load_status收集项目状态
2. **信息汇总**：汇总工作流进度、资源使用、阶段完成情况
3. **结果展示**：格式化输出项目状态报告

## 质量门禁

无特定质量门禁。该命令为查询类命令。

## 使用示例

### 示例1：查看当前状态

```
/status
```

### 示例2：详细状态

```
/status --detail=detailed
```

### 示例3：所有阶段状态

```
/status --phase=all
```

### 示例4：JSON格式

```
/status --format=json
```

### 示例5：完整报告

```
/status --detail=full
```

## 相关脚本

- 无特定脚本（使用内联状态检查作为降级方式）

---

## 相关命令

- `/agent-status` - Agent状态查询
- `/sprint` - 启动冲刺
- `/loop` - 启动自动循环
