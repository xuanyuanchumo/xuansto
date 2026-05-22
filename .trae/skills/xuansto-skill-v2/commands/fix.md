---
name: /fix
aliases:
  - f
category: workflow
phase: "6"
description: 缺陷修复与问题解决
trigger: 需要修复缺陷或解决问题时
workflow: sdd-tdd-full
---

# /fix 命令

## 命令用途

执行缺陷修复与问题解决，包括质量门禁检查和安全漏洞修复，确保代码恢复到健康状态。

## MCP工具调用链

| 顺序 | MCP工具 | 参数 | 说明 |
|------|---------|------|------|
| 1 | quality_gate_check | phase=6 | 检查修复后质量门禁状态 |
| 2 | security_scan | - | 扫描修复后的安全状态 |

## 降级策略

| MCP工具 | 降级方式 | 降级脚本/操作 |
|---------|----------|---------------|
| quality_gate_check | 脚本调用 | python scripts/skill-test.py --gate [gate_id] |
| security_scan | 脚本调用 | python scripts/agentic-security-scanner.py |

## 涉及Agent

| Agent | 角色 | 职责 |
|-------|------|------|
| fullstack-engineer | 主导 | 缺陷修复、代码修正 |
| security-auditor | 辅助 | 安全漏洞修复 |
| test-architect | 辅助 | 修复验证测试 |

## 命令描述

执行缺陷修复与问题解决，包括质量门禁检查和安全漏洞修复，确保代码恢复到健康状态。该命令支持自动修复和手动修复两种模式。

## 触发条件

| 触发方式 | 说明 |
|----------|------|
| 命令输入 | 用户输入 `/fix` |
| 关键词触发 | 用户提及"修复缺陷"、"解决问题"、"fix bug" |
| 自动触发 | `/review` 发现问题时自动建议 |
| 流程触发 | 测试失败时自动建议修复 |

## 命令名称与语法

```
/fix [--issue=<问题ID>] [--auto] [--verify]
```

## 参数定义

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--issue` | string | 否 | latest | 指定问题ID或latest/all |
| `--auto` | flag | 否 | false | 自动修复模式 |
| `--verify` | flag | 否 | true | 修复后自动验证 |
| `--security-only` | flag | 否 | false | 仅修复安全问题 |
| `--no-commit` | flag | 否 | false | 修复后不自动提交 |

## 执行流程

> 标准五步框架：1. 输入验证 → 2. Agent调度 → 3. 任务执行 → 4. 结果验证 → 5. 输出交付

1. **输入验证**：校验问题ID有效、确定修复范围
2. **Agent调度**：fullstack-engineer主导缺陷修复，security-auditor辅助安全修复
3. **任务执行**：执行问题定位→根因分析→修复实现→验证测试的完整修复流程
4. **结果验证**：执行quality_gate_check和security_scan
5. **输出交付**：生成修复报告、验证结果

## 质量门禁

| 门禁标识 | 阻塞级别(BLOCK/WARN) | 通过标准 |
|----------|----------------------|----------|
| FIX-VERIFIED | BLOCK | 修复后测试通过、原问题不再复现、无回归问题 |
| FIX-NO-REGRESSION | BLOCK | 修复未引入新缺陷、所有原有测试仍通过 |

## 使用示例

### 示例1：修复最新问题

```
/fix
```

### 示例2：修复指定问题

```
/fix --issue=BUG-001
```

### 示例3：自动修复

```
/fix --auto
```

### 示例4：仅修复安全问题

```
/fix --security-only
```

### 示例5：修复并验证

```
/fix --issue=BUG-003 --verify
```

## 相关脚本

- `scripts/skill-test.py` - 技能测试器，执行质量门禁检查
- `scripts/agentic-security-scanner.py` - 安全扫描器，验证修复后安全状态

---

## 相关命令

- `/review` - 代码审查
- `/test` - 测试执行
- `/simplify` - 代码简化
- `/sprint` - 启动完整冲刺
