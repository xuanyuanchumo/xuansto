---
name: /accept
aliases:
  - acc
category: workflow
phase: "6"
description: 验收确认与交付准备
trigger: 需要确认功能验收或准备交付时
workflow: sdd-tdd-full
---

# /accept 命令

## 命令用途

执行验收确认与交付准备，通过Phase 6质量门禁检查，确保功能满足验收标准并可以交付。

## MCP工具调用链

| 顺序 | MCP工具 | 参数 | 说明 |
|------|---------|------|------|
| 1 | quality_gate_check | phase=6 | 检查验收阶段质量门禁 |

## 降级策略

| MCP工具 | 降级方式 | 降级脚本/操作 |
|---------|----------|---------------|
| quality_gate_check | 脚本调用 | python scripts/skill-test.py --gate [gate_id] |

## 涉及Agent

| Agent | 角色 | 职责 |
|-------|------|------|
| product-manager | 主导 | 验收标准确认、功能验收 |
| qa-engineer | 辅助 | 验收测试执行 |
| technical-writer | 辅助 | 验收文档整理 |

## 命令描述

执行验收确认与交付准备，通过Phase 6质量门禁检查，确保功能满足验收标准并可以交付。该命令是SDD流程中交付前的最终确认环节。

## 触发条件

| 触发方式 | 说明 |
|----------|------|
| 命令输入 | 用户输入 `/accept` |
| 关键词触发 | 用户提及"验收确认"、"功能验收"、"交付准备" |
| 自动触发 | `/sprint` 命令执行时自动调用Accept阶段 |
| 流程触发 | `/review` 和 `/fix` 完成后自动进入Accept阶段 |

## 命令名称与语法

```
/accept [--criteria=<验收标准>] [--skip-tests] [--auto]
```

## 参数定义

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--criteria` | path | 否 | .sprint/artifacts/acceptance/ | 验收标准文件路径 |
| `--skip-tests` | flag | 否 | false | 跳过验收测试（不推荐） |
| `--auto` | flag | 否 | false | 自动验收模式 |
| `--report` | enum | 否 | markdown | 报告格式：markdown/html/pdf |

## 执行流程

> 标准五步框架：1. 输入验证 → 2. Agent调度 → 3. 任务执行 → 4. 结果验证 → 5. 输出交付

1. **输入验证**：校验验收标准文件存在、所有前置阶段已完成
2. **Agent调度**：product-manager主导验收确认，qa-engineer执行验收测试
3. **任务执行**：执行验收标准检查→验收测试→用户确认→验收报告生成
4. **结果验证**：执行quality_gate_check(phase=6)
5. **输出交付**：生成验收报告、交付清单

## 质量门禁

| 门禁标识 | 阻塞级别(BLOCK/WARN) | 通过标准 |
|----------|----------------------|----------|
| ACCEPT-ALL-CRITERIA | BLOCK | 所有验收标准已满足、验收测试全部通过 |
| ACCEPT-NO-OPEN-ISSUES | BLOCK | 无未解决的严重/高危问题 |

## 使用示例

### 示例1：标准验收

```
/accept
```

### 示例2：指定验收标准

```
/accept --criteria=./docs/acceptance-criteria.md
```

### 示例3：自动验收

```
/accept --auto
```

### 示例4：生成HTML报告

```
/accept --report=html
```

## 相关脚本

- `scripts/skill-test.py` - 技能测试器，执行质量门禁检查

---

## 相关命令

- `/review` - 代码审查
- `/fix` - 修复缺陷
- `/deploy` - 部署交付
- `/sprint` - 启动完整冲刺
