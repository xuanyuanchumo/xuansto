---
name: /review
aliases:
  - r
  - rv
category: workflow
phase: "6"
description: 代码审查与质量评估
trigger: 需要代码审查或质量评估时
workflow: sdd-tdd-full
---

# /review 命令

## 命令用途

执行代码审查与质量评估，包括代码简化建议和安全漏洞扫描，确保代码符合质量标准。

## MCP工具调用链

| 顺序 | MCP工具 | 参数 | 说明 |
|------|---------|------|------|
| 1 | code_simplify | - | 分析代码复杂度并生成简化建议 |
| 2 | security_scan | - | 扫描代码中的安全漏洞 |

## 降级策略

| MCP工具 | 降级方式 | 降级脚本/操作 |
|---------|----------|---------------|
| code_simplify | 脚本调用 | python scripts/code-simplifier.py |
| security_scan | 脚本调用 | python scripts/agentic-security-scanner.py |

## 涉及Agent

| Agent | 角色 | 职责 |
|-------|------|------|
| code-reviewer | 主导 | 代码质量审查、最佳实践检查 |
| security-auditor | 辅助 | 安全漏洞扫描、安全建议 |
| performance-optimizer | 辅助 | 性能问题识别 |

## 命令描述

执行代码审查与质量评估，包括代码简化建议和安全漏洞扫描，确保代码符合质量标准。该命令是SDD流程中质量保障的重要环节。

## 触发条件

| 触发方式 | 说明 |
|----------|------|
| 命令输入 | 用户输入 `/review` |
| 关键词触发 | 用户提及"代码审查"、"质量评估"、"code review" |
| 自动触发 | `/sprint` 命令执行时自动调用Review阶段 |
| 流程触发 | `/test` 完成后自动进入Review阶段 |

## 命令名称与语法

```
/review [--scope=<范围>] [--severity=<严重级别>] [--auto-fix]
```

## 参数定义

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--scope` | enum | 否 | changed | 审查范围：changed/all/staged |
| `--severity` | enum | 否 | medium | 最低报告严重级别：low/medium/high/critical |
| `--auto-fix` | flag | 否 | false | 自动修复可修复的问题 |
| `--security-only` | flag | 否 | false | 仅执行安全审查 |
| `--quality-only` | flag | 否 | false | 仅执行质量审查 |
| `--output` | enum | 否 | markdown | 输出格式：markdown/json/sarif |

## 执行流程

> 标准五步框架：1. 输入验证 → 2. Agent调度 → 3. 任务执行 → 4. 结果验证 → 5. 输出交付

1. **输入验证**：校验`--scope`参数合法、确定审查文件范围
2. **Agent调度**：code-reviewer主导代码质量审查，security-auditor主导安全扫描
3. **任务执行**：执行代码质量审查→安全漏洞扫描→性能问题识别→审查报告生成
4. **结果验证**：执行GATE-007门禁检查
5. **输出交付**：生成审查报告、安全报告、改进建议

## 质量门禁

| 门禁标识 | 阻塞级别(BLOCK/WARN) | 通过标准 |
|----------|----------------------|----------|
| GATE-007 | BLOCK | 无严重/高危问题、代码复杂度在阈值内、安全扫描无高危漏洞 |
| REVIEW-NO-SECRETS | BLOCK | 代码中无硬编码密钥/密码/Token |
| REVIEW-COMPLEXITY | WARN | 圈复杂度≤10、函数长度≤50行 |

## 使用示例

### 示例1：审查变更代码

```
/review
```

### 示例2：审查所有代码

```
/review --scope=all
```

### 示例3：仅安全审查

```
/review --security-only
```

### 示例4：自动修复

```
/review --auto-fix
```

### 示例5：JSON输出

```
/review --output=json
```

## 相关脚本

- `scripts/code-simplifier.py` - 代码简化器，分析代码复杂度并生成简化建议
- `scripts/agentic-security-scanner.py` - 安全扫描器，扫描代码中的安全漏洞

---

## 相关命令

- `/test` - 测试执行
- `/fix` - 修复缺陷
- `/simplify` - 代码简化
- `/sprint` - 启动完整冲刺
