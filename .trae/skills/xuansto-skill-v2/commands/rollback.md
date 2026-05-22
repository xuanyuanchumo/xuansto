---
name: /rollback
aliases:
  - rb
  - revert
category: system
phase: "any"
description: 回滚到之前状态
trigger: 需要回滚或恢复到之前状态时
workflow: none
---

# /rollback 命令

## 命令用途

回滚到之前的状态，中止当前工作流并加载之前的会话状态，恢复到安全检查点。

## MCP工具调用链

| 顺序 | MCP工具 | 参数 | 说明 |
|------|---------|------|------|
| 1 | workflow_dispatch | action=abort | 中止当前工作流 |
| 2 | session_manage | action=load | 加载之前的会话状态 |

## 降级策略

| MCP工具 | 降级方式 | 降级脚本/操作 |
|---------|----------|---------------|
| workflow_dispatch | 内联执行 | 内联阶段推进（中止流程） |
| session_manage | 脚本调用 | python scripts/init-session.py / session-catchup.py |

## 涉及Agent

| Agent | 角色 | 职责 |
|-------|------|------|
| orchestrator | 主导 | 回滚协调、状态恢复 |

## 命令描述

回滚到之前的状态，中止当前工作流并加载之前的会话状态，恢复到安全检查点。该命令确保回滚操作安全可靠，不会丢失已完成的有效工作。

## 触发条件

| 触发方式 | 说明 |
|----------|------|
| 命令输入 | 用户输入 `/rollback` |
| 别名触发 | `/rb`, `/revert` |
| 关键词触发 | 用户提及"回滚"、"恢复"、"rollback"、"revert" |
| 条件触发 | 部署失败或发现严重问题时 |

## 命令名称与语法

```
/rollback [--to=<检查点>] [--scope=<范围>] [--dry-run]
```

## 参数定义

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--to` | string | 否 | last-stable | 回滚目标：last-stable/last-commit/<checkpoint-id> |
| `--scope` | enum | 否 | full | 回滚范围：full/code/config/database |
| `--dry-run` | flag | 否 | false | 仅模拟回滚不实际执行 |
| `--force` | flag | 否 | false | 强制回滚（跳过确认） |

## 执行流程

> 标准四步框架：1. 状态检查 → 2. 中止工作流 → 3. 加载会话 → 4. 验证恢复

1. **状态检查**：确认当前状态、确定回滚目标检查点
2. **中止工作流**：通过workflow_dispatch(action=abort)中止当前工作流
3. **加载会话**：通过session_manage(action=load)加载之前的会话状态
4. **验证恢复**：验证回滚后状态正确、系统可用

## 质量门禁

| 门禁标识 | 阻塞级别(BLOCK/WARN) | 通过标准 |
|----------|----------------------|----------|
| ROLLBACK-CLEAN | BLOCK | 回滚完成、系统状态一致、无残留变更 |

## 使用示例

### 示例1：回滚到上一个稳定状态

```
/rollback
```

### 示例2：回滚到指定检查点

```
/rollback --to=checkpoint-003
```

### 示例3：仅回滚代码

```
/rollback --scope=code
```

### 示例4：模拟回滚

```
/rollback --dry-run
```

### 示例5：强制回滚

```
/rollback --force
```

## 相关脚本

- `scripts/init-session.py` - 会话初始化器，加载之前的会话状态
- `scripts/session-catchup.py` - 会话恢复器，恢复会话上下文

---

## 相关命令

- `/deploy` - 部署交付
- `/cancel-loop` - 取消自动循环
- `/status` - 查看项目状态
