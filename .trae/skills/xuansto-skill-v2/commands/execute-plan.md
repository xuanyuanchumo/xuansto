---
name: /execute-plan
aliases:
  - ep
  - exec
category: workflow
phase: "4"
description: 执行实施计划
trigger: 需要执行已制定的实施计划时
workflow: sdd-tdd-full
---

# /execute-plan 命令

## 命令用途

执行已制定的实施计划，启动工作流并按计划逐步实施任务。

## MCP工具调用链

| 顺序 | MCP工具 | 参数 | 说明 |
|------|---------|------|------|
| 1 | workflow_dispatch | action=start | 启动实施工作流 |

## 降级策略

| MCP工具 | 降级方式 | 降级脚本/操作 |
|---------|----------|---------------|
| workflow_dispatch | 内联执行 | 内联阶段推进（实施流程） |

## 涉及Agent

| Agent | 角色 | 职责 |
|-------|------|------|
| orchestrator | 主导 | 计划执行编排、任务调度 |
| fullstack-engineer | 辅助 | 代码实现 |
| test-architect | 辅助 | 测试验证 |

## 命令描述

执行已制定的实施计划，启动工作流并按计划逐步实施任务。该命令是连接计划阶段和实施阶段的桥梁。

## 触发条件

| 触发方式 | 说明 |
|----------|------|
| 命令输入 | 用户输入 `/execute-plan` |
| 别名触发 | `/ep`, `/exec` |
| 关键词触发 | 用户提及"执行计划"、"开始实施"、"execute plan" |
| 流程触发 | `/plan` 完成后自动建议执行 |

## 命令名称与语法

```
/execute-plan [--plan=<计划文件>] [--task=<任务ID>] [--parallel=<并行数>]
```

## 参数定义

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--plan` | path | 否 | .sprint/artifacts/plan/ | 实施计划文件路径 |
| `--task` | string | 否 | all | 指定任务ID或all |
| `--parallel` | int | 否 | 3 | 最大并行任务数 |
| `--dry-run` | flag | 否 | false | 仅模拟执行不实际操作 |
| `--continue-on-error` | flag | 否 | false | 任务失败时继续执行后续任务 |

## 执行流程

> 标准五步框架：1. 输入验证 → 2. Agent调度 → 3. 任务执行 → 4. 结果验证 → 5. 输出交付

1. **输入验证**：校验计划文件存在、任务ID有效
2. **Agent调度**：orchestrator主导计划执行，根据任务类型分配Agent
3. **任务执行**：按计划顺序或并行执行任务、每个任务完成后验证
4. **结果验证**：验证所有任务已完成、质量门禁通过
5. **输出交付**：生成执行报告、变更摘要

## 质量门禁

| 门禁标识 | 阻塞级别(BLOCK/WARN) | 通过标准 |
|----------|----------------------|----------|
| EXEC-PLAN-COMPLETE | BLOCK | 计划中所有任务已执行、验证通过 |
| EXEC-NO-FAILED | BLOCK | 无失败任务（除非--continue-on-error） |

## 使用示例

### 示例1：执行所有任务

```
/execute-plan
```

### 示例2：执行指定任务

```
/execute-plan --task=TASK-001
```

### 示例3：指定计划文件

```
/execute-plan --plan=./docs/implementation-plan.md
```

### 示例4：高并行度执行

```
/execute-plan --parallel=5
```

### 示例5：试运行

```
/execute-plan --dry-run
```

## 相关脚本

- `scripts/init-session.py` - 会话初始化器，创建执行会话

---

## 相关命令

- `/plan` - 计划制定
- `/implement` - 代码实现
- `/sprint` - 启动冲刺
- `/status` - 查看执行状态
