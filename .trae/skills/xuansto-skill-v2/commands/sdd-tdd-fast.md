---
name: /sdd-tdd-fast
aliases:
  - fast
  - dev-fast
category: workflow
phase: "1-4"
description: 启动SDD+TDD快速开发工作流
trigger: 需要启动快速SDD+TDD开发流程时
workflow: sdd-tdd-fast
---

# /sdd-tdd-fast 命令

## 命令用途

启动SDD+TDD快速开发工作流（4阶段），适用于小型任务、Bug修复、功能增强等快速迭代场景，保留核心质量保障机制同时精简流程步骤。

## MCP工具调用链

| 顺序 | MCP工具 | 参数 | 说明 |
|------|---------|------|------|
| 1 | workflow_dispatch | action=start, workflow=sdd-tdd-fast | 启动快速工作流 |
| 2 | resource_load_status | action=preload, phase=1 | 预加载核心资源 |

## 降级策略

| MCP工具 | 降级方式 | 降级脚本/操作 |
|---------|----------|---------------|
| workflow_dispatch | 内联执行 | 内联阶段推进（SDD+TDD快速流程） |
| resource_load_status | 内联执行 | 内联状态检查 |

## 涉及Agent

| Agent | 角色 | 职责 |
|-------|------|------|
| fullstack-engineer | 主导(阶段1-4) | 需求理解+实现+验证 |
| unit-tester | 主导(阶段2) | TDD测试编写 |
| code-reviewer | 主导(阶段3) | 快速代码审查 |

## 命令描述

启动SDD+TDD快速开发工作流，精简为4阶段（快速需求→TDD快速开发→快速审查→快速验证），适用于小型任务和快速迭代场景。保留核心TDD循环（Red-Green-Refactor-Verify）和强制门禁（FILE-ENCODING、COMMENT-LANGUAGE），同时省略独立的设计阶段、架构规格阶段和完整的安全审计。

## 触发条件

| 触发方式 | 说明 |
|----------|------|
| 命令输入 | 用户输入 `/sdd-tdd-fast` |
| 别名触发 | `/fast`, `/dev-fast` |
| 关键词触发 | 用户提及"快速开发"、"fast"、"简化流程" |
| 条件触发 | 项目规模为小型（<20文件、1-3模块） |

## 命令名称与语法

```
/sdd-tdd-fast [--scope=<范围>] [--skip-review] [--desktop-quick]
```

## 参数定义

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--scope` | enum | 否 | feature | 开发范围：feature/bugfix/refactor |
| `--skip-review` | flag | 否 | false | 跳过独立审查阶段（合并到验证阶段） |
| `--coverage-threshold` | int | 否 | 60 | 代码覆盖率阈值(%) |
| `--desktop-quick` | flag | 否 | false | 启用桌面快速验证通道 |

## 执行流程

```
┌─────────────────────────────────────────────────────────────┐
│              /sdd-tdd-fast 执行流程                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │ 阶段1    │───▶│ 阶段2    │───▶│ 阶段3    │              │
│  │ 快速需求 │    │ TDD开发  │    │ 快速审查 │              │
│  └──────────┘    └──────────┘    └──────────┘              │
│                                       │                     │
│                                       ▼                     │
│  ┌──────────┐                                              │
│  │ 阶段4    │                                              │
│  │ 快速验证 │───▶ 交付                                     │
│  └──────────┘                                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 质量门禁

| 门禁标识 | 阶段 | 阻塞级别 | 通过标准 |
|----------|------|----------|----------|
| GATE-001 | 1 | BLOCK | 核心功能点明确 |
| GATE-002 | 1 | BLOCK | 实现方案可行 |
| TEST-PASS | 2 | BLOCK | 核心测试用例通过 |
| GATE-007 | 2 | BLOCK | 代码覆盖率>=60% |
| FILE-ENCODING | 2 | BLOCK(强制) | 所有源代码文件为UTF-8 without BOM |
| COMMENT-LANGUAGE | 2 | BLOCK(强制) | 业务注释包含中文说明 |
| GATE-009 | 3 | BLOCK | 无严重问题且核心逻辑正确 |
| GATE-011 | 4 | BLOCK | 功能符合预期 |
| GATE-015 | 4 | BLOCK | 演化闭环完成 |

## 使用示例

### 示例1：快速功能开发

```
/sdd-tdd-fast
```

### 示例2：Bug修复

```
/sdd-tdd-fast --scope=bugfix
```

### 示例3：桌面快速修复

```
/sdd-tdd-fast --desktop-quick --scope=bugfix
```

### 示例4：跳过独立审查

```
/sdd-tdd-fast --skip-review
```

## 相关脚本

- `scripts/session-catchup.py` - 会话恢复器

---

## 相关命令

- `/sdd-tdd-medium` - 中等规模开发工作流（6阶段）
- `/sdd-tdd-full` - 完整开发工作流（9阶段）
- `/sprint` - 快速冲刺（本工作流的别名入口）
- `/fix` - Bug修复快捷命令
- `/status` - 查看工作流状态
