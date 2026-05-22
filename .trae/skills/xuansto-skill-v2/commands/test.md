---
name: /test
aliases:
  - t
category: workflow
phase: "5"
description: 测试执行与质量验证
trigger: 需要执行测试或验证质量时
workflow: sdd-tdd-full
---

# /test 命令

## 命令用途

执行测试流程，包括单元测试、集成测试和端到端测试，确保代码质量通过质量门禁验证。

## MCP工具调用链

| 顺序 | MCP工具 | 参数 | 说明 |
|------|---------|------|------|
| 1 | quality_gate_check | phase=5 | 检查测试阶段质量门禁 |

## 降级策略

| MCP工具 | 降级方式 | 降级脚本/操作 |
|---------|----------|---------------|
| quality_gate_check | 脚本调用 | python scripts/skill-test.py --gate [gate_id] |

## 涉及Agent

| Agent | 角色 | 职责 |
|-------|------|------|
| test-architect | 主导 | 测试策略、测试架构 |
| qa-engineer | 主导 | 测试执行、缺陷报告 |
| fullstack-engineer | 辅助 | 修复测试发现的问题 |

## 命令描述

执行测试流程，包括单元测试、集成测试和端到端测试，确保代码质量通过质量门禁验证。该命令是SDD流程中质量保障的核心环节。

## 触发条件

| 触发方式 | 说明 |
|----------|------|
| 命令输入 | 用户输入 `/test` |
| 关键词触发 | 用户提及"测试执行"、"运行测试"、"质量验证" |
| 自动触发 | `/sprint` 命令执行时自动调用Test阶段 |
| 流程触发 | `/implement` 完成后自动进入Test阶段 |

## 命令名称与语法

```
/test [--type=<类型>] [--coverage=<阈值>] [--watch=<监视>]
```

## 参数定义

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--type` | enum | 否 | all | 测试类型：all/unit/integration/e2e/performance |
| `--coverage` | int | 否 | 80 | 最低覆盖率阈值（百分比） |
| `--watch` | flag | 否 | false | 监视模式，文件变更时自动重跑 |
| `--bail` | flag | 否 | false | 首个测试失败时停止 |
| `--update-snapshots` | flag | 否 | false | 更新快照测试 |
| `--verbose` | flag | 否 | false | 详细输出模式 |

## 执行流程

> 标准五步框架：1. 输入验证 → 2. Agent调度 → 3. 任务执行 → 4. 结果验证 → 5. 输出交付

1. **输入验证**：校验测试文件存在、`--type`参数合法、`--coverage`阈值合理
2. **Agent调度**：test-architect主导测试策略，qa-engineer主导测试执行
3. **任务执行**：执行测试发现→测试执行→覆盖率分析→缺陷报告的完整测试流程
4. **结果验证**：执行GATE-006门禁检查
5. **输出交付**：生成测试报告、覆盖率报告、缺陷列表

## 质量门禁

| 门禁标识 | 阻塞级别(BLOCK/WARN) | 通过标准 |
|----------|----------------------|----------|
| GATE-006 | BLOCK | 所有测试通过、覆盖率≥阈值、无严重缺陷 |
| TEST-COVERAGE | BLOCK | 行覆盖率≥80%、分支覆盖率≥70% |
| TEST-NO-FLAKY | WARN | 无不稳定测试（连续3次运行结果一致） |

## 使用示例

### 示例1：执行所有测试

```
/test
```

### 示例2：仅执行单元测试

```
/test --type=unit
```

### 示例3：高覆盖率要求

```
/test --coverage=95
```

### 示例4：监视模式

```
/test --watch
```

### 示例5：详细输出

```
/test --verbose --type=integration
```

## 相关脚本

- `scripts/skill-test.py` - 技能测试器，执行质量门禁检查和测试验证

---

## 相关命令

- `/implement` - 代码实现
- `/review` - 代码审查
- `/fix` - 修复缺陷
- `/sprint` - 启动完整冲刺
