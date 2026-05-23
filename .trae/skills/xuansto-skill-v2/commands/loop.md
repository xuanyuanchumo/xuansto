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

/loop 采用逐步降级策略，按 Step 1→2→3 顺序尝试，每步失败自动进入下一步：

### 逐步降级链

| Step | 策略 | 说明 | 适用工具 |
|------|------|------|----------|
| 1 | MCP完整调用 | 调用MCP工具完整参数，获取结构化JSON结果 | 全部13个MCP工具 |
| 2 | MCP简化调用 | 调用MCP工具精简参数（省略可选参数、降低depth/top_k等），仅获取核心结果 | skill_analyze(depth=basic), knowledge_search(top_k=3, search_type=keyword_only), quality_gate_check(仅检查BLOCK级别), security_scan(severity_threshold=high), code_simplify(scope=file) |
| 3 | 脚本降级调用 | 使用Python脚本替代，结果包装为与MCP相同的JSON结构 | 全部有降级脚本的工具 |

### 各工具降级详情

| MCP工具 | Step 1: MCP完整 | Step 2: MCP简化 | Step 3: 脚本降级 |
|---------|-----------------|-----------------|------------------|
| skill_analyze | depth=full, include_agents=True | depth=basic, include_agents=False | scripts/skill-test.py --analyze |
| knowledge_search | top_k=5, search_type=hybrid | top_k=3, search_type=keyword_only | scripts/knowledge-server.py --search [query] |
| quality_gate_check | 全部门禁检查 | 仅BLOCK级别门禁 | scripts/skill-test.py --gate [gate_id] |
| spec_drift_detect | 完整漂移检测 | 仅MISMATCH级别漂移 | scripts/spec-drift-detector.py |
| security_scan | severity_threshold=medium, include_agentic=True | severity_threshold=high, include_agentic=False | scripts/agentic-security-scanner.py |
| code_simplify | scope=dir, include_dedup=True | scope=file, include_dedup=False | scripts/code-simplifier.py |
| session_manage | 完整参数save/load | 仅save/load核心字段 | scripts/init-session.py / scripts/session-catchup.py |
| workflow_dispatch | 完整工作流调度 | 仅phase=current+advance | 内联阶段推进 |
| agent_status | action=list, by_phase | action=list(省略by_phase) | 静态注册表查找 |
| hook_manage | action=list+execute | action=list(跳过execute) | 内联钩子执行 |
| resource_load_status | action=preload+status | action=status(跳过preload) | 内联状态检查 |
| context_compress | strategy=semantic | strategy=selective | scripts/context-compressor.py |
| server_health | 完整健康检查 | — | scripts/health-checker.py |

### 降级判定规则

1. Step 1 失败条件：MCP工具返回错误码(DEGRADED/TIMEOUT/UNAVAILABLE)或调用超时(>30秒)
2. Step 2 失败条件：MCP简化调用仍返回错误或超时(>15秒)
3. Step 3 为最终兜底：脚本调用失败则记录错误并跳过该工具，继续执行下一阶段
4. 降级不可逆：一旦进入Step 2/3，同一工具在本轮循环中不再尝试更高级别
5. 降级事件记录：写入 session_manage(action=save) 的 decisions 字段

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
