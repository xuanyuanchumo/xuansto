---
name: /sprint
aliases:
  - sp
  - sprint-start
category: system
phase: "0-8"
description: 启动SDD+TDD快速冲刺
trigger: 需要启动快速开发冲刺时
workflow: sdd-tdd-fast
---

# /sprint 命令

## 命令用途

启动SDD+TDD快速冲刺周期，预加载资源并启动sdd-tdd-fast工作流，实现从需求到交付的快速迭代。

## MCP工具调用链

| 顺序 | MCP工具 | 参数 | 说明 |
|------|---------|------|------|
| 1 | workflow_dispatch | action=start, workflow=sdd-tdd-fast | 启动SDD+TDD快速冲刺工作流 |
| 2 | resource_load_status | action=preload | 预加载资源状态检查 |

## 降级策略

| MCP工具 | 降级方式 | 降级脚本/操作 |
|---------|----------|---------------|
| workflow_dispatch | 内联执行 | 内联阶段推进（SDD+TDD快速流程） |
| resource_load_status | 内联执行 | 内联状态检查 |

## 涉及Agent

| Agent | 角色 | 职责 |
|-------|------|------|
| orchestrator | 主导 | 冲刺编排、阶段调度 |
| product-manager | 辅助 | 需求管理 |
| fullstack-engineer | 辅助 | 代码实现 |
| test-architect | 辅助 | 测试策略 |
| devops-engineer | 辅助 | 部署交付 |

## 命令描述

启动SDD+TDD快速冲刺周期，预加载资源并启动sdd-tdd-fast工作流，实现从需求到交付的快速迭代。该命令是快速开发模式的核心入口。

## 触发条件

| 触发方式 | 说明 |
|----------|------|
| 命令输入 | 用户输入 `/sprint` |
| 别名触发 | `/sp`, `/sprint-start` |
| 关键词触发 | 用户提及"冲刺"、"快速开发"、"sprint" |
| 条件触发 | 需要快速完成一个功能开发时 |

## 命令名称与语法

```
/sprint [--mode=<模式>] [--duration=<时长>] [--scope=<范围>]
```

## 参数定义

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--mode` | enum | 否 | fast | 冲刺模式：fast/standard/thorough |
| `--duration` | enum | 否 | 1h | 冲刺时长：30m/1h/2h/4h/1d |
| `--scope` | enum | 否 | feature | 冲刺范围：feature/bugfix/refactor/full |
| `--skip-clarify` | flag | 否 | false | 跳过需求澄清（需求已明确时） |
| `--skip-design` | flag | 否 | false | 跳过设计阶段 |
| `--auto-deploy` | flag | 否 | false | 验收后自动部署 |

## 执行流程

> SDD+TDD快速冲刺：Clarify → Plan → Implement → Test → Review → Accept

```
┌─────────────────────────────────────────────────────────────┐
│                    /sprint 执行流程                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │ Clarify  │───▶│  Plan    │───▶│Implement │              │
│  └──────────┘    └──────────┘    └──────────┘              │
│                                       │                     │
│                                       ▼                     │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │  Accept  │◀───│  Review  │◀───│  Test    │              │
│  └──────────┘    └──────────┘    └──────────┘              │
│       │                                                     │
│       ▼                                                     │
│  ┌──────────┐                                              │
│  │  Deploy  │  (可选，--auto-deploy)                        │
│  └──────────┘                                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 质量门禁

| 门禁标识 | 阻塞级别(BLOCK/WARN) | 通过标准 |
|----------|----------------------|----------|
| SPRINT-COMPLETE | BLOCK | 冲刺所有阶段完成、验收通过 |
| SPRINT-QUALITY | BLOCK | 代码质量达标、测试通过、无严重问题 |

## 使用示例

### 示例1：快速冲刺

```
/sprint
```

### 示例2：标准冲刺

```
/sprint --mode=standard
```

### 示例3：Bug修复冲刺

```
/sprint --scope=bugfix --skip-clarify
```

### 示例4：自动部署冲刺

```
/sprint --auto-deploy
```

### 示例5：2小时冲刺

```
/sprint --duration=2h
```

## 相关脚本

- `scripts/init-session.py` - 会话初始化器，创建冲刺会话
- `scripts/session-catchup.py` - 会话恢复器，恢复冲刺上下文

---

## 相关命令

- `/loop` - 全生命周期自动循环
- `/status` - 查看冲刺状态
- `/cancel-loop` - 取消冲刺
