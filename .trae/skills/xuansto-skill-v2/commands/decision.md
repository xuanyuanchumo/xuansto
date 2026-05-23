---
name: /decision
aliases:
  - adr
  - decide
category: system
phase: "any"
description: 决策记录与管理
trigger: 需要记录、查询或回顾架构决策时
workflow: none
---

# /decision 命令

## 命令用途

记录、查询和管理项目中的架构决策(ADR)，确保关键决策可追溯、可回顾。

## MCP工具调用链

| 顺序 | MCP工具 | 参数 | 说明 |
|------|---------|------|------|
| 1 | decision_log | action, title, decision | 记录或查询决策 |

## 降级策略

| MCP工具 | 降级方式 | 降级脚本/操作 |
|---------|----------|---------------|
| decision_log | 内联JSON记录 | 写入本地decision-log.json |

## 涉及Agent

| Agent | 角色 | 职责 |
|-------|------|------|
| Decision Logger | 主导 | 决策记录持久化与检索 |

## 命令描述

记录、查询和管理项目中的架构决策。使用ADR(Architecture Decision Record)格式记录决策上下文、决策内容和后果，确保团队对关键设计选择有共识且可追溯。

## 触发条件

| 触发方式 | 说明 |
|----------|------|
| 命令输入 | 用户输入 `/decision` |
| 别名触发 | `/adr`, `/decide` |
| 关键词触发 | 用户提及"决策记录"、"ADR"、"架构决策" |
| 条件触发 | 架构设计阶段或冲突仲裁后 |

## 命令名称与语法

```
/decision <action> [--title=<标题>] [--decision=<决策内容>]
```

## 参数定义

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `action` | enum | 是 | — | 操作类型：record/query/list |
| `--title` | str | record时必填 | — | 决策标题 |
| `--decision` | str | record时必填 | — | 决策内容描述 |
| `--context` | str | 否 | — | 决策背景上下文 |
| `--consequences` | str | 否 | — | 决策预期后果 |
| `--format` | enum | 否 | table | 输出格式：table/json/markdown |

## 执行流程

> 标准三步框架：1. 决策收集 → 2. 持久化记录 → 3. 确认反馈

1. **决策收集**：收集决策标题、内容、上下文和后果
2. **持久化记录**：通过decision_log工具记录决策到持久化存储
3. **确认反馈**：返回决策记录ID和摘要

## 质量门禁

无特定质量门禁。该命令为记录类命令。

## 使用示例

### 示例1：记录决策

```
/decision record --title="数据库选型" --decision="选用PostgreSQL" --context="需要支持复杂查询和JSON类型"
```

### 示例2：查询决策

```
/decision query --title="数据库选型"
```

### 示例3：列出所有决策

```
/decision list
```

## 相关脚本

- 降级时使用内联JSON文件记录

---

## 相关命令

- `/plan` - 架构规划
- `/spec` - 规格文档
- `/status` - 项目状态查询
