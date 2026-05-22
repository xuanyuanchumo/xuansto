---
name: /plan
aliases:
  - p
category: workflow
phase: "2"
description: 架构规划与技术选型
trigger: 需要架构设计或技术决策时
workflow: sdd-tdd-full
---

# /plan 命令

## 命令用途

基于澄清后的需求制定详细的实施计划，包括任务分解、Agent分配、依赖分析和时间估算。

## MCP工具调用链

| 顺序 | MCP工具 | 参数 | 说明 |
|------|---------|------|------|
| 1 | skill_analyze | scope=planning | 分析项目技能需求和Agent匹配 |
| 2 | knowledge_search | query=<需求关键词> | 搜索知识库中相关架构模式 |
| 3 | agent_status | - | 查询可用Agent状态和负载 |

## 降级策略

| MCP工具 | 降级方式 | 降级脚本/操作 |
|---------|----------|---------------|
| skill_analyze | 脚本调用 | python scripts/skill-test.py --analyze |
| knowledge_search | 脚本调用 | python scripts/knowledge-server.py --search [query] |
| agent_status | 静态查询 | 静态注册表查找 |

## 涉及Agent

| Agent | 角色 | 职责 |
|-------|------|------|
| product-manager | 主导 | 任务优先级、里程碑定义 |
| system-architect | 辅助 | 技术依赖、架构决策 |
| fullstack-engineer | 辅助 | 工作量估算 |
| test-architect | 辅助 | 测试策略、测试任务 |
| devops-engineer | 辅助 | 部署任务、环境准备 |

## 命令描述

基于澄清后的需求制定详细的实施计划，包括任务分解、Agent分配、依赖分析和时间估算。该命令是SDD流程的核心规划环节。

## 触发条件

| 触发方式 | 说明 |
|----------|------|
| 命令输入 | 用户输入 `/plan` |
| 关键词触发 | 用户提及"架构规划"、"计划制定"、"任务分解" |
| 自动触发 | `/sprint` 命令执行时自动调用Plan阶段 |
| 流程触发 | `/clarify` 完成后自动进入Plan阶段 |

## 命令名称与语法

```
/plan [--input=<需求文件>] [--method=<方法>] [--constraints=<约束>]
```

## 参数定义

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--input` | path | 否 | .sprint/artifacts/requirements/ | 澄清后的需求文件路径 |
| `--method` | enum | 否 | auto | 规划方法：auto/agile/waterfall/kanban |
| `--constraints` | json | 否 | {} | 约束条件（时间、资源、技术） |
| `--parallelism` | int | 否 | 3 | 最大并行任务数 |
| `--granularity` | enum | 否 | medium | 任务粒度：coarse/medium/fine |
| `--save` | flag | 否 | true | 保存计划到文件 |

## 执行流程

> 标准五步框架：1. 输入验证 → 2. Agent调度 → 3. 任务执行 → 4. 结果验证 → 5. 输出交付

1. **输入验证**：校验`--input`路径存在且包含有效需求文件、`--method`参数合法
2. **Agent调度**：product-manager主导任务优先级，system-architect负责技术依赖分析
3. **任务执行**：执行任务分解→依赖分析→Agent分配→时间估算→风险评估→计划优化
4. **结果验证**：执行GATE-003和PLAN-ATOMIC门禁检查
5. **输出交付**：生成implementation-plan.md和task-graph.json

## 质量门禁

| 门禁标识 | 阻塞级别(BLOCK/WARN) | 通过标准 |
|----------|----------------------|----------|
| GATE-003 | BLOCK | 任务分解完整、依赖关系无循环、关键路径已识别 |
| GATE-004 | BLOCK | 技术选型合理、风险评估完成、备选方案已评估 |
| PLAN-ATOMIC | BLOCK | 每个任务≤5分钟+含文件路径+含验证步骤+任务不可再分 |
| PLAN-PERSISTENCE | WARN | 重大决策前已重新读取计划文件、2-Action Rule执行 |

## 使用示例

### 示例1：自动规划

```
/plan
```

### 示例2：指定输入文件

```
/plan --input=./docs/requirements.md
```

### 示例3：带约束条件

```
/plan --constraints='{"deadline":"2024-02-01","max_agents":5}'
```

### 示例4：细粒度任务

```
/plan --granularity=fine --parallelism=5
```

## 相关脚本

- `scripts/init-session.py` - 会话初始化器，创建规划会话和工作目录结构

---

## 相关命令

- `/clarify` - 需求澄清
- `/spec` - 规格编写
- `/implement` - 开始实施
- `/sprint` - 启动完整冲刺
