---
name: /cancel-loop
aliases:
  - cl
category: workflow
phase: "cross-phase"
description: 取消当前运行的自主迭代循环
trigger: 需要终止正在运行的Ralph Loop时
execution_mode: inline
---

# /cancel-loop 命令

## 命令描述

取消当前正在运行的自主迭代循环（Ralph Loop）。该命令是 `/loop` 的安全终止机制，允许用户在任何时候中断循环执行，Orchestrator 将执行优雅退出流程，保留当前进度状态。

---

## 触发条件

| 触发方式 | 说明 |
|----------|------|
| 命令输入 | 用户输入 `/cancel-loop` |
| 关键词触发 | 用户提及"取消循环"、"停止循环"、"终止循环" |
| 自动触发 | 停滞检测连续3次无进展时自动建议 |

---

## 命令名称与语法

```
/cancel-loop [options]
```

---

## 参数定义

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| --save-progress | boolean | 否 | true | 取消前保存当前进度到 .agent_cache/ |
| --force | boolean | 否 | false | 强制取消，不等待当前迭代完成 |
| --reason | string | 否 | - | 取消原因说明，记录到 Decision Log |

---

## 执行流程

> 标准四步框架：1. 输入验证 → 2. Agent调度 → 3. 任务执行 → 4. 结果验证

```
┌─────────────────────────────────────────────────────────────┐
│                  /cancel-loop 执行流程                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. 输入验证阶段                                             │
│     ├── 读取 .agent_cache/<task>/loop-state.md             │
│     ├── 确认循环状态为 active                               │
│     ├── 若已 cancelled/completed 则提示并退出               │
│     └── 验证 --force 和 --save-progress 参数合法性          │
│                                                             │
│  2. Agent调度阶段                                            │
│     ├── 通知 Orchestrator 执行取消操作                       │
│     ├── 若 --force=false，等待当前迭代步骤完成               │
│     └── 若 --force=true，立即中断当前迭代                    │
│                                                             │
│  3. 任务执行阶段                                             │
│     ├── 调用 loop-guard.py --action cancel                 │
│     ├── 将 loop-state.md 状态标记为 cancelled              │
│     ├── 记录取消时间戳和原因                                 │
│     ├── 更新 progress.md 记录当前迭代进度                   │
│     ├── 保留 loop-state.md 中的迭代历史                     │
│     └── 触发 plan-sync.py 归档当前阶段                      │
│                                                             │
│  4. 结果验证与输出阶段                                       │
│     ├── 验证 loop-state.md 状态已更新为 cancelled           │
│     ├── 验证进度文件已保存（--save-progress=true 时）       │
│     ├── 输出取消摘要                                        │
│     ├── 显示已完成迭代数                                    │
│     └── 显示下次恢复建议                                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 涉及Agent

| Agent | 角色 | 职责 |
|-------|------|------|
| orchestrator | 主导 | 执行取消操作，保存进度，生成退出报告 |

---

## 输出格式

```
==================================================
Loop Cancelled
==================================================

Task: my-feature
Cancelled at: 2026-05-05T10:45:00Z
Iterations completed: 12/50
Last progress: 实现用户登录API

Recovery suggestion:
  Resume with: /loop 继续实现用户登录功能
  Or restart: /sprint my-feature --phase=implement

==================================================
```

---

## 质量门禁

| 门禁标识 | 阻塞级别(BLOCK/WARN) | 通过标准 |
|----------|----------------------|----------|
| LOOP-COMPLETION | WARN | 循环已正常取消+进度已保存+迭代历史已保留 |
| ITERATION-BUDGET | WARN | 取消时迭代数未超预算、Token消耗记录完整 |

---

## 示例用法

### 示例1：取消当前循环

```
/cancel-loop
```

优雅取消当前运行的循环，等待当前迭代步骤完成后保存进度并退出。

### 示例2：强制取消

```
/cancel-loop --force
```

立即中断当前迭代，不等待当前步骤完成。注意：可能导致部分变更未保存。

### 示例3：取消并说明原因

```
/cancel-loop --reason="需求变更，暂停开发"
```

取消循环并记录取消原因到 Decision Log。

### 示例4：取消但不保存进度

```
/cancel-loop --save-progress=false
```

取消循环且不保存当前进度（仅保留已有的迭代历史）。

---

## 相关脚本

- `scripts/loop-guard.py` - 循环守卫，执行循环取消操作并管理循环状态
- `scripts/plan-sync.py` - 计划同步器，归档当前阶段进度

---

## 相关命令

- `/loop` - 启动自主迭代循环
- `/sprint --autonomous` - 以自主迭代模式启动冲刺
