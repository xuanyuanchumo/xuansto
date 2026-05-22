---
name: /loop
aliases:
  - lp
category: system
phase: "0-8"
description: 全生命周期自动循环
trigger: 需要全自动执行完整开发周期时
workflow: sdd-tdd-full
---

# /loop 命令

## 命令用途

启动全生命周期自动循环，从需求探索到部署交付的完整自动化执行，调用全部13个MCP工具实现端到端开发。

## MCP工具调用链

| 顺序 | MCP工具 | 参数 | 说明 |
|------|---------|------|------|
| 1 | skill_analyze | scope=full-lifecycle | 全生命周期技能分析 |
| 2 | knowledge_search | query=<需求关键词> | 知识库搜索 |
| 3 | quality_gate_check | phase=auto | 自动阶段质量门禁 |
| 4 | spec_drift_detect | - | 规格偏移检测 |
| 5 | security_scan | - | 安全扫描 |
| 6 | code_simplify | - | 代码简化 |
| 7 | session_manage | action=auto | 会话管理 |
| 8 | workflow_dispatch | action=auto | 工作流调度 |
| 9 | agent_status | - | Agent状态查询 |
| 10 | hook_manage | action=auto | 钩子管理 |
| 11 | resource_load_status | - | 资源负载状态 |
| 12 | context_compress | - | 上下文压缩 |
| 13 | server_health | - | 服务器健康检查 |

## 降级策略

| MCP工具 | 降级方式 | 降级脚本/操作 |
|---------|----------|---------------|
| skill_analyze | 脚本调用 | python scripts/skill-test.py --analyze |
| knowledge_search | 脚本调用 | python scripts/knowledge-server.py --search [query] |
| quality_gate_check | 脚本调用 | python scripts/skill-test.py --gate [gate_id] |
| spec_drift_detect | 脚本调用 | python scripts/spec-drift-detector.py |
| security_scan | 脚本调用 | python scripts/agentic-security-scanner.py |
| code_simplify | 脚本调用 | python scripts/code-simplifier.py |
| session_manage | 脚本调用 | python scripts/init-session.py / session-catchup.py |
| workflow_dispatch | 内联执行 | 内联阶段推进 |
| agent_status | 静态查询 | 静态注册表查找 |
| hook_manage | 内联执行 | 内联钩子执行 |
| resource_load_status | 内联执行 | 内联状态检查 |
| context_compress | 脚本调用 | python scripts/context-compressor.py |
| server_health | 脚本调用 | python scripts/health-checker.py |

## 涉及Agent

| Agent | 角色 | 职责 |
|-------|------|------|
| orchestrator | 主导 | 全流程编排、阶段调度 |
| product-manager | 辅助 | 需求管理 |
| system-architect | 辅助 | 架构决策 |
| fullstack-engineer | 辅助 | 代码实现 |
| test-architect | 辅助 | 测试策略 |
| code-reviewer | 辅助 | 代码审查 |
| security-auditor | 辅助 | 安全审计 |
| devops-engineer | 辅助 | 部署交付 |

## 命令描述

启动全生命周期自动循环，从需求探索到部署交付的完整自动化执行。该命令调用全部13个MCP工具，实现端到端的自动开发，是最高级别的自动化命令。

## 触发条件

| 触发方式 | 说明 |
|----------|------|
| 命令输入 | 用户输入 `/loop` |
| 关键词触发 | 用户提及"全自动"、"完整循环"、"auto loop" |
| 条件触发 | 用户希望一次性完成从需求到部署的全流程 |

## 命令名称与语法

```
/loop [--from=<起始阶段>] [--to=<结束阶段>] [--interactive]
```

## 参数定义

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--from` | enum | 否 | clarify | 起始阶段：clarify/plan/spec/design/implement/test/review/deploy |
| `--to` | enum | 否 | deploy | 结束阶段 |
| `--interactive` | flag | 否 | false | 交互模式（每阶段确认） |
| `--skip-phases` | list | 否 | [] | 跳过的阶段 |
| `--max-iterations` | int | 否 | 3 | 最大迭代次数 |
| `--stop-on-failure` | flag | 否 | true | 失败时停止 |

## 执行流程

> 全生命周期9阶段循环：Clarify → Plan → Spec → Design → Implement → Test → Review → Accept → Deploy

```
┌─────────────────────────────────────────────────────────────┐
│                    /loop 执行流程                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │ Clarify  │───▶│  Plan    │───▶│  Spec    │              │
│  └──────────┘    └──────────┘    └──────────┘              │
│       │               │               │                     │
│       ▼               ▼               ▼                     │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │ Design   │───▶│Implement │───▶│  Test    │              │
│  └──────────┘    └──────────┘    └──────────┘              │
│       │               │               │                     │
│       ▼               ▼               ▼                     │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │ Review   │───▶│  Accept  │───▶│  Deploy  │              │
│  └──────────┘    └──────────┘    └──────────┘              │
│                                             │               │
│                    ┌────────────────────────┘               │
│                    ▼                                        │
│             ┌──────────────┐                                │
│             │  完成/迭代    │                                │
│             └──────────────┘                                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 质量门禁

| 门禁标识 | 阻塞级别(BLOCK/WARN) | 通过标准 |
|----------|----------------------|----------|
| LOOP-ALL-GATES | BLOCK | 所有阶段质量门禁通过 |
| LOOP-NO-REGRESSION | BLOCK | 无回归问题 |

## 使用示例

### 示例1：完整自动循环

```
/loop
```

### 示例2：从计划阶段开始

```
/loop --from=plan
```

### 示例3：交互模式

```
/loop --interactive
```

### 示例4：跳过设计阶段

```
/loop --skip-phases=design
```

### 示例5：仅到测试阶段

```
/loop --to=test
```

## 相关脚本

- `scripts/skill-test.py` - 技能测试器，执行质量门禁检查
- `scripts/knowledge-server.py` - 知识服务器，知识库搜索
- `scripts/spec-drift-detector.py` - 规格偏移检测器
- `scripts/agentic-security-scanner.py` - 安全扫描器
- `scripts/code-simplifier.py` - 代码简化器
- `scripts/context-compressor.py` - 上下文压缩器
- `scripts/health-checker.py` - 健康检查器

---

## 相关命令

- `/cancel-loop` - 取消自动循环
- `/status` - 查看循环状态
- `/sprint` - 启动冲刺
