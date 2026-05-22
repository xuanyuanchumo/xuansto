---
name: /simplify
aliases:
  - simp
category: workflow
phase: "6"
description: 代码简化与复杂度降低
trigger: 需要简化代码或降低复杂度时
workflow: sdd-tdd-full
---

# /simplify 命令

## 命令用途

执行代码简化与复杂度降低，分析代码结构并生成简化建议，使代码更易理解和维护。

## MCP工具调用链

| 顺序 | MCP工具 | 参数 | 说明 |
|------|---------|------|------|
| 1 | code_simplify | - | 分析代码复杂度并生成简化建议 |

## 降级策略

| MCP工具 | 降级方式 | 降级脚本/操作 |
|---------|----------|---------------|
| code_simplify | 脚本调用 | python scripts/code-simplifier.py |

## 涉及Agent

| Agent | 角色 | 职责 |
|-------|------|------|
| code-reviewer | 主导 | 代码简化分析、重构建议 |
| fullstack-engineer | 辅助 | 简化实现 |
| performance-optimizer | 辅助 | 性能影响评估 |

## 命令描述

执行代码简化与复杂度降低，分析代码结构并生成简化建议，使代码更易理解和维护。该命令专注于降低代码复杂度而不改变功能行为。

## 触发条件

| 触发方式 | 说明 |
|----------|------|
| 命令输入 | 用户输入 `/simplify` |
| 关键词触发 | 用户提及"代码简化"、"降低复杂度"、"simplify" |
| 自动触发 | `/review` 发现复杂度问题时自动建议 |
| 条件触发 | 代码圈复杂度超过阈值时 |

## 命令名称与语法

```
/simplify [--scope=<范围>] [--threshold=<阈值>] [--auto-apply]
```

## 参数定义

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--scope` | enum | 否 | changed | 简化范围：changed/all/targeted |
| `--threshold` | int | 否 | 10 | 圈复杂度阈值 |
| `--auto-apply` | flag | 否 | false | 自动应用简化建议 |
| `--preserve-api` | flag | 否 | true | 保留公共API不变 |
| `--max-lines` | int | 否 | 50 | 函数最大行数 |

## 执行流程

> 标准四步框架：1. 输入验证 → 2. Agent调度 → 3. 任务执行 → 4. 结果验证

1. **输入验证**：校验`--scope`参数合法、确定简化文件范围
2. **Agent调度**：code-reviewer主导简化分析，fullstack-engineer辅助实现
3. **任务执行**：执行复杂度分析→简化建议生成→用户确认→简化实现的完整流程
4. **结果验证**：验证简化后功能不变、测试通过、复杂度降低

## 质量门禁

| 门禁标识 | 阻塞级别(BLOCK/WARN) | 通过标准 |
|----------|----------------------|----------|
| SIMPLIFY-BEHAVIOR | BLOCK | 简化后功能行为不变、所有测试通过 |
| SIMPLIFY-COMPLEXITY | BLOCK | 圈复杂度降低、函数长度减少 |

## 使用示例

### 示例1：简化变更代码

```
/simplify
```

### 示例2：简化所有代码

```
/simplify --scope=all
```

### 示例3：自动应用

```
/simplify --auto-apply
```

### 示例4：设置复杂度阈值

```
/simplify --threshold=5
```

## 相关脚本

- `scripts/code-simplifier.py` - 代码简化器，分析代码复杂度并生成简化建议

---

## 相关命令

- `/review` - 代码审查
- `/refactor` - 代码重构
- `/sprint` - 启动完整冲刺
