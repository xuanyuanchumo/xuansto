---
name: /refactor
aliases:
  - ref
category: workflow
phase: "6"
description: 代码重构与结构优化
trigger: 需要重构代码或优化结构时
workflow: sdd-tdd-full
---

# /refactor 命令

## 命令用途

执行代码重构与结构优化，通过代码简化和上下文压缩，改善代码结构而不改变功能行为。

## MCP工具调用链

| 顺序 | MCP工具 | 参数 | 说明 |
|------|---------|------|------|
| 1 | code_simplify | - | 分析代码复杂度并生成简化建议 |
| 2 | context_compress | - | 压缩冗余上下文和重复代码 |

## 降级策略

| MCP工具 | 降级方式 | 降级脚本/操作 |
|---------|----------|---------------|
| code_simplify | 脚本调用 | python scripts/code-simplifier.py |
| context_compress | 脚本调用 | python scripts/context-compressor.py |

## 涉及Agent

| Agent | 角色 | 职责 |
|-------|------|------|
| code-reviewer | 主导 | 重构分析、结构优化建议 |
| fullstack-engineer | 辅助 | 重构实现 |
| test-architect | 辅助 | 重构验证测试 |

## 命令描述

执行代码重构与结构优化，通过代码简化和上下文压缩，改善代码结构而不改变功能行为。该命令专注于结构性改进，包括提取方法、消除重复、改善命名等。

## 触发条件

| 触发方式 | 说明 |
|----------|------|
| 命令输入 | 用户输入 `/refactor` |
| 关键词触发 | 用户提及"代码重构"、"结构优化"、"refactor" |
| 自动触发 | `/review` 发现结构性问题时自动建议 |
| 条件触发 | 代码重复率超过阈值时 |

## 命令名称与语法

```
/refactor [--type=<类型>] [--scope=<范围>] [--safe-only]
```

## 参数定义

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--type` | enum | 否 | all | 重构类型：all/extract/rename/inline/move/simplify |
| `--scope` | enum | 否 | changed | 重构范围：changed/all/module |
| `--safe-only` | flag | 否 | true | 仅执行安全重构（有测试覆盖的） |
| `--dry-run` | flag | 否 | false | 仅生成重构计划不执行 |
| `--preserve-api` | flag | 否 | true | 保留公共API不变 |

## 执行流程

> 标准五步框架：1. 输入验证 → 2. Agent调度 → 3. 任务执行 → 4. 结果验证 → 5. 输出交付

1. **输入验证**：校验`--type`和`--scope`参数合法、确定重构文件范围
2. **Agent调度**：code-reviewer主导重构分析，fullstack-engineer辅助实现
3. **任务执行**：执行代码分析→重构计划→用户确认→重构实现→测试验证
4. **结果验证**：验证重构后功能不变、测试通过、代码结构改善
5. **输出交付**：生成重构报告、变更摘要

## 质量门禁

| 门禁标识 | 阻塞级别(BLOCK/WARN) | 通过标准 |
|----------|----------------------|----------|
| REFACTOR-BEHAVIOR | BLOCK | 重构后功能行为不变、所有测试通过 |
| REFACTOR-STRUCTURE | BLOCK | 代码结构改善、重复代码减少 |

## 使用示例

### 示例1：重构变更代码

```
/refactor
```

### 示例2：提取方法

```
/refactor --type=extract
```

### 示例3：重构所有代码

```
/refactor --scope=all
```

### 示例4：试运行

```
/refactor --dry-run
```

### 示例5：仅安全重构

```
/refactor --safe-only
```

## 相关脚本

- `scripts/code-simplifier.py` - 代码简化器，分析代码复杂度并生成简化建议
- `scripts/context-compressor.py` - 上下文压缩器，压缩冗余上下文和重复代码

---

## 相关命令

- `/simplify` - 代码简化
- `/review` - 代码审查
- `/sprint` - 启动完整冲刺
