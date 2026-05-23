---
name: /sdd-tdd-medium
aliases:
  - medium
  - dev-medium
category: workflow
phase: "0-5"
description: 启动SDD+TDD中等规模开发工作流
trigger: 需要启动中等规模SDD+TDD开发流程时
workflow: sdd-tdd-medium
---

# /sdd-tdd-medium 命令

## 命令用途

启动SDD+TDD中等规模开发工作流（6阶段），适用于中型项目（20-100文件、5-20模块），在保留核心质量保障机制的同时提升开发效率。

## MCP工具调用链

| 顺序 | MCP工具 | 参数 | 说明 |
|------|---------|------|------|
| 1 | skill_analyze | scope=project | 分析项目规模和技术栈 |
| 2 | workflow_dispatch | action=start, workflow=sdd-tdd-medium | 启动中等规模工作流 |
| 3 | resource_load_status | action=preload, phase=1 | 预加载阶段资源 |

## 降级策略

| MCP工具 | 降级方式 | 降级脚本/操作 |
|---------|----------|---------------|
| skill_analyze | 脚本调用 | python scripts/skill-test.py --analyze |
| workflow_dispatch | 内联执行 | 内联阶段推进（SDD+TDD中等流程） |
| resource_load_status | 内联执行 | 内联状态检查 |

## 涉及Agent

| Agent | 角色 | 职责 |
|-------|------|------|
| product-manager | 主导(阶段A/E) | 需求分析、验收确认 |
| ux-designer | 主导(阶段A) | 用户研究、交互设计 |
| ui-designer | 主导(阶段A) | 视觉设计、设计系统 |
| system-architect | 主导(阶段B) | 架构设计、技术选型 |
| test-architect | 主导(阶段C) | 测试策略设计 |
| fullstack-engineer | 主导(阶段D) | 代码实现 |
| unit-tester | 主导(阶段C/D) | TDD测试编写 |
| code-reviewer | 主导(阶段D) | 代码质量把关 |
| qa-engineer | 主导(阶段E) | 全量测试执行 |
| security-auditor | 主导(阶段E) | 安全扫描与审计 |
| refactoring-specialist | 主导(阶段F) | 代码优化与重构 |
| build-release-engineer | 主导(阶段F) | 构建、打包、发布 |

## 命令描述

启动SDD+TDD中等规模开发工作流，将完整9阶段流程合并为6阶段（需求与设计→架构与规格→测试设计→TDD实现→验证与验收→迭代与交付），在保留核心质量保障机制的同时提升开发效率。相比快速工作流，增加了独立的设计阶段、架构规格阶段和测试策略阶段；相比完整工作流，合并了需求与设计、验证与验收、迭代与交付等阶段，减少流程开销。

## 触发条件

| 触发方式 | 说明 |
|----------|------|
| 命令输入 | 用户输入 `/sdd-tdd-medium` |
| 别名触发 | `/medium`, `/dev-medium` |
| 关键词触发 | 用户提及"中等开发"、"medium"、"标准流程" |
| 条件触发 | 项目规模为中型（20-100文件、5-20模块） |

## 命令名称与语法

```
/sdd-tdd-medium [--scope=<范围>] [--skip-design] [--skip-security]
```

## 参数定义

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--scope` | enum | 否 | feature | 开发范围：feature/refactor/full |
| `--skip-design` | flag | 否 | false | 跳过独立设计阶段（需求与设计合并为快速需求） |
| `--skip-security` | flag | 否 | false | 跳过安全审计阶段 |
| `--coverage-threshold` | int | 否 | 70 | 代码覆盖率阈值(%) |
| `--desktop` | flag | 否 | false | 启用桌面开发通道 |

## 执行流程

```
┌─────────────────────────────────────────────────────────────┐
│              /sdd-tdd-medium 执行流程                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │  阶段A       │───▶│  阶段B       │───▶│  阶段C       │  │
│  │  需求与设计  │    │  架构与规格  │    │  测试设计    │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│                                               │             │
│                                               ▼             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │  阶段F       │◀───│  阶段E       │◀───│  阶段D       │  │
│  │  迭代与交付  │    │  验证与验收  │    │  TDD实现     │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│       │                                                     │
│       ▼                                                     │
│  ┌──────────┐                                              │
│  │  交付    │                                              │
│  └──────────┘                                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 质量门禁

| 门禁标识 | 阶段 | 阻塞级别 | 通过标准 |
|----------|------|----------|----------|
| DESIGN-SYSTEM-COMPLETE | A | BLOCK | 设计系统完整且设计令牌与技术栈兼容 |
| GATE-001 | A | BLOCK | 需求完整性检查通过 |
| GATE-003 | B | BLOCK | 架构设计符合SOLID原则 |
| PLAN-ATOMIC | B | BLOCK | 实现计划已原子化拆分 |
| GATE-005 | C | BLOCK | 测试覆盖所有用户故事 |
| TEST-PASS | D | BLOCK | 所有测试用例通过 |
| GATE-007 | D | BLOCK | 代码质量门禁通过 |
| FILE-ENCODING | D | BLOCK(强制) | 所有源代码文件为UTF-8 without BOM |
| COMMENT-LANGUAGE | D | BLOCK(强制) | 业务注释包含中文说明 |
| SCRIPT-SECURITY | D | BLOCK(强制) | 无安全风险脚本 |
| GATE-012 | E | BLOCK | 安全扫描门禁通过 |
| PLAYWRIGHT-E2E-PASS | E | BLOCK | Playwright E2E测试通过 |
| SIMPLIFICATION-BEHAVIOR | F | BLOCK | 简化行为等价验证通过 |
| CHESTERTON-FENCE | F | BLOCK | Chesterton's Fence检查通过 |

## 使用示例

### 示例1：标准中等开发

```
/sdd-tdd-medium
```

### 示例2：功能增强

```
/sdd-tdd-medium --scope=feature
```

### 示例3：跳过设计阶段

```
/sdd-tdd-medium --skip-design
```

### 示例4：桌面应用开发

```
/sdd-tdd-medium --desktop
```

### 示例5：自定义覆盖率阈值

```
/sdd-tdd-medium --coverage-threshold=80
```

## 相关脚本

- `scripts/project-initializer.py` - 项目初始化器
- `scripts/session-catchup.py` - 会话恢复器

---

## 相关命令

- `/sdd-tdd-fast` - 快速开发工作流（4阶段）
- `/sprint` - 快速冲刺（sdd-tdd-fast的别名入口）
- `/sdd-tdd-full` - 完整开发工作流（9阶段）
- `/status` - 查看工作流状态
- `/cancel-loop` - 取消工作流
