---
name: /loop
aliases:
  - lp
category: workflow
phase: "cross-phase"
description: 自主迭代循环，持续执行直到任务完成
trigger: 需要自主迭代执行任务直到完成时
execution_mode: autonomous_loop
---

# /loop 命令

## 命令描述

启动自主迭代循环（Ralph Loop），持续执行开发任务直到完成标准满足或达到迭代上限。该命令是 Module 7 的核心入口，Orchestrator 在循环中自动协调各 Agent 执行 Brainstorming→Design→Architecture→TDD→Review→Verify→Simplify 流程，无需人工干预。

---

## 触发条件

| 触发方式 | 说明 |
|----------|------|
| 命令输入 | 用户输入 `/loop` |
| 关键词触发 | 用户提及"自主迭代"、"Ralph Loop"、"循环执行"、"自动循环" |
| 参数触发 | `/sprint --autonomous` 内部调用 |

---

## 命令名称与语法

```
/loop <prompt> [--max-iterations 50] [--completion-promise "DONE"]
```

---

## 参数定义

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `<prompt>` | string | 是 | - | 任务描述或需求提示 |
| `--max-iterations` | number | 否 | 50 | 最大迭代次数 |
| `--completion-promise` | string | 否 | "DONE" | 完成承诺字符串，输出此字符串视为完成信号 |

---

## 执行流程

> 8步循环框架：初始化→头脑风暴→设计→架构+测试→TDD+审查→验证→简化→完成检查

```
┌─────────────────────────────────────────────────────────────┐
│                  /loop 自主迭代循环                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Step 1: 初始化 Loop + Planning Files                  │   │
│  │   ├── 执行 init-session.py --task-name <name>        │   │
│  │   ├── 执行 loop-guard.py --action init               │   │
│  │   ├── 创建 loop-state.md (YAML frontmatter + MD)     │   │
│  │   └── 记录原始提示、完成标准、最大迭代数               │   │
│  └──────────────────────────────────────────────────────┘   │
│                          │                                  │
│                          ▼                                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Step 2: Brainstorming（头脑风暴）                      │   │
│  │   ├── 分析需求，生成多个候选方案                        │   │
│  │   ├── 评估方案可行性                                   │   │
│  │   └── 选择最优方案                                     │   │
│  └──────────────────────────────────────────────────────┘   │
│                          │                                  │
│                          ▼                                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Step 3: Design（设计）                                 │   │
│  │   ├── UI/UX 设计                                      │   │
│  │   ├── 数据模型设计                                     │   │
│  │   └── 接口设计                                         │   │
│  └──────────────────────────────────────────────────────┘   │
│                          │                                  │
│                          ▼                                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Step 4: Architecture + Test Design（架构+测试）        │   │
│  │   ├── 系统架构设计                                     │   │
│  │   ├── 测试策略制定                                     │   │
│  │   └── 测试用例编写                                     │   │
│  └──────────────────────────────────────────────────────┘   │
│                          │                                  │
│                          ▼                                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Step 5: TDD + Review（TDD实现+审查）                   │   │
│  │   ├── 红灯：编写失败测试                                │   │
│  │   ├── 绿灯：编写最小实现                                │   │
│  │   ├── 重构：优化代码                                    │   │
│  │   └── 代码审查                                         │   │
│  └──────────────────────────────────────────────────────┘   │
│                          │                                  │
│                          ▼                                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Step 6: Verify（验证）                                 │   │
│  │   ├── 运行测试套件                                     │   │
│  │   ├── 安全扫描                                         │   │
│  │   └── 性能基准测试                                     │   │
│  └──────────────────────────────────────────────────────┘   │
│                          │                                  │
│                          ▼                                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Step 7: Simplify（简化）                               │   │
│  │   ├── 代码简化与重构                                   │   │
│  │   ├── 删除冗余代码                                     │   │
│  │   └── 优化实现                                         │   │
│  └──────────────────────────────────────────────────────┘   │
│                          │                                  │
│                          ▼                                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Step 8: Completion Check（完成检查）                   │   │
│  │   ├── 执行 completion-verifier.py                     │   │
│  │   ├── 检查 completion promise 是否输出                 │   │
│  │   ├── 检查完成标准是否满足                              │   │
│  │   ├── 检查质量门禁通过状态                              │   │
│  │   ├── 更新 loop-guard.py --action update              │   │
│  │   └── complete → 退出 / incomplete → 回到 Step 2     │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                             │
│  安全机制:                                                   │
│  ├── 最大迭代数 (默认50)                                    │
│  ├── 连续3次无进展 → 标记stagnant并暂停                     │
│  ├── Token预算耗尽前优雅退出                                │
│  └── /cancel-loop 随时取消                                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 涉及Agent

| Agent | 角色 | 职责 |
|-------|------|------|
| Orchestrator | 主导 | Loop Enforcement，循环控制，迭代调度，停滞检测 |
| Brainstorming Facilitator | 协同 | Phase 1: 需求探索，生成候选方案，评估可行性 |
| System Architect | 协同 | Phase 2: 架构规划，系统架构设计，技术选型 |
| Fullstack Engineer | 协同 | Phase 4: TDD实现，红灯-绿灯-重构循环 |
| Code Reviewer | 协同 | Phase 4: 代码审查，协调子Agent执行审查 |
| Test Architect | 协同 | Phase 3/5: 测试策略制定，测试用例编写与验证 |
| Refactoring Specialist | 协同 | Phase 7: 代码简化与优化，消除冗余 |

---

## 输出格式

### 1. Loop State (loop-state.md)

```yaml
---
task_name: "my-feature"
status: "active"
original_prompt: "实现用户登录功能"
completion_promise: "DONE"
completion_criteria: "所有测试通过;无安全漏洞"
max_iterations: 50
current_iteration: 5
stagnation_count: 0
stagnant: false
started_at: "2026-05-05T10:00:00Z"
last_updated_at: "2026-05-05T10:30:00Z"
---

# Loop Iteration History

| # | Iteration | Description | Progress | Stagnant | Timestamp |
|---|-----------|-------------|----------|----------|-----------|
| 1 | 1 | 初始化项目结构 | 10% | no | 2026-05-05T10:05:00Z |
```

### 2. Completion Verification Report

```
==================================================
Completion Verification Report
==================================================

Task: my-feature
Status: COMPLETE

--- Check Results ---
  [PASS] completion_promise: Promise 'DONE' found in output
  [PASS] completion_criteria: All completion criteria met
  [PASS] quality_gates: All blocking quality gates passed

--- Missing Items ---
  (none)

==================================================
```

---

## 质量门禁

| 门禁标识 | 阻塞级别(BLOCK/WARN) | 通过标准 |
|----------|----------------------|----------|
| LOOP-COMPLETION | BLOCK | Completion promise已输出 + 所有完成标准已满足 + 质量门禁通过 |
| ITERATION-BUDGET | WARN+BLOCK | 迭代数<=最大值 + 连续无进展<=3次 + Token预算未耗尽 |

---

## 示例用法

### 示例1：启动自主迭代循环

```
/loop 实现用户登录功能，支持邮箱和手机号登录
```

### 示例2：指定最大迭代数

```
/loop 实现购物车功能 --max-iterations 30
```

### 示例3：自定义完成承诺

```
/loop 重构支付模块 --max-iterations 20 --completion-promise "REFACTORING_COMPLETE"
```

### 示例4：通过sprint自主模式间接调用

```
/sprint 实现数据报表 --autonomous
```

---

## 安全机制

1. **最大迭代数**：默认50次，可通过 `--max-iterations` 调整
2. **停滞检测与自动恢复**：连续3次迭代无进展时，若 `loop.stagnation_auto_recovery: true`（默认）则自动执行恢复策略（replan/fallback/restart），不暂停循环
3. **Token预算**：Token预算耗尽前优雅退出，保留10%预算用于收尾
4. **随时取消**：用户可随时输入 `/cancel-loop` 终止循环
5. **自主模式**：当 `human_collaboration.loop_mode: autonomous`（默认）时，所有断点自动恢复，仅安全硬门禁（production_deploy/secret_key_rotation/database_schema_destructive_change）需人工确认
6. **三击协议自动恢复**：3次失败后自动执行恢复策略（默认 replan），恢复失败才升级到用户

---

## 相关脚本

- `scripts/loop-guard.py` - 循环守卫，管理循环状态初始化、更新和取消
- `scripts/completion-verifier.py` - 完成验证器，检查完成承诺输出和完成标准满足状态

---

## 相关命令

- `/cancel-loop` - 取消当前运行的循环
- `/sprint --autonomous` - 以自主迭代模式启动冲刺
- `/plan` - 手动规划任务
- `/implement` - 手动实现任务
