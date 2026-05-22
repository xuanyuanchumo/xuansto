---
name: /deploy
aliases:
  - dep
category: workflow
phase: "8"
description: 部署交付与发布管理
trigger: 需要部署或发布时
workflow: sdd-tdd-full
---

# /deploy 命令

## 命令用途

执行部署交付与发布管理，通过Phase 8质量门禁检查后启动部署工作流，确保代码安全发布到目标环境。

## MCP工具调用链

| 顺序 | MCP工具 | 参数 | 说明 |
|------|---------|------|------|
| 1 | quality_gate_check | phase=8 | 检查部署阶段质量门禁 |
| 2 | workflow_dispatch | action=start, workflow=deployment | 启动部署工作流 |

## 降级策略

| MCP工具 | 降级方式 | 降级脚本/操作 |
|---------|----------|---------------|
| quality_gate_check | 脚本调用 | python scripts/skill-test.py --gate [gate_id] |
| workflow_dispatch | 内联执行 | 内联阶段推进（部署流程） |

## 涉及Agent

| Agent | 角色 | 职责 |
|-------|------|------|
| devops-engineer | 主导 | 部署执行、环境管理 |
| security-auditor | 辅助 | 部署安全检查 |
| fullstack-engineer | 辅助 | 部署问题修复 |

## 命令描述

执行部署交付与发布管理，通过Phase 8质量门禁检查后启动部署工作流，确保代码安全发布到目标环境。该命令是SDD流程的最终交付环节。

## 触发条件

| 触发方式 | 说明 |
|----------|------|
| 命令输入 | 用户输入 `/deploy` |
| 关键词触发 | 用户提及"部署"、"发布"、"deploy"、"release" |
| 自动触发 | `/sprint` 命令执行时自动调用Deploy阶段 |
| 流程触发 | `/accept` 完成后自动进入Deploy阶段 |

## 命令名称与语法

```
/deploy [--env=<环境>] [--strategy=<策略>] [--rollback=<回滚策略>]
```

## 参数定义

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--env` | enum | 否 | staging | 目标环境：staging/production/canary |
| `--strategy` | enum | 否 | rolling | 部署策略：rolling/blue-green/canary/recreate |
| `--rollback` | enum | 否 | auto | 回滚策略：auto/manual/disabled |
| `--dry-run` | flag | 否 | false | 仅模拟部署不实际执行 |
| `--skip-tests` | flag | 否 | false | 跳过部署前测试（不推荐） |

## 执行流程

> 标准五步框架：1. 输入验证 → 2. Agent调度 → 3. 任务执行 → 4. 结果验证 → 5. 输出交付

1. **输入验证**：校验验收已完成、`--env`参数合法、部署配置存在
2. **Agent调度**：devops-engineer主导部署执行，security-auditor辅助安全检查
3. **任务执行**：执行部署前检查→环境准备→代码部署→健康检查→流量切换
4. **结果验证**：执行quality_gate_check(phase=8)
5. **输出交付**：生成部署报告、发布说明

## 质量门禁

| 门禁标识 | 阻塞级别(BLOCK/WARN) | 通过标准 |
|----------|----------------------|----------|
| DEPLOY-READY | BLOCK | 验收已通过、部署配置完整、目标环境可达 |
| DEPLOY-HEALTHY | BLOCK | 部署后健康检查通过、无错误日志、性能指标正常 |

## 使用示例

### 示例1：部署到staging

```
/deploy
```

### 示例2：部署到生产环境

```
/deploy --env=production
```

### 示例3：蓝绿部署

```
/deploy --env=production --strategy=blue-green
```

### 示例4：金丝雀部署

```
/deploy --env=production --strategy=canary
```

### 示例5：模拟部署

```
/deploy --dry-run
```

## 相关脚本

- `scripts/skill-test.py` - 技能测试器，执行质量门禁检查

---

## 相关命令

- `/accept` - 验收确认
- `/rollback` - 部署回滚
- `/status` - 查看部署状态
- `/sprint` - 启动完整冲刺
