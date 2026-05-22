---
name: /audit
aliases:
  - au
category: workflow
phase: "6"
description: 安全审计与合规检查
trigger: 需要安全审计或合规检查时
workflow: sdd-tdd-full
---

# /audit 命令

## 命令用途

执行安全审计与合规检查，扫描代码中的安全漏洞并验证合规性，确保代码满足安全标准。

## MCP工具调用链

| 顺序 | MCP工具 | 参数 | 说明 |
|------|---------|------|------|
| 1 | security_scan | - | 扫描代码中的安全漏洞 |
| 2 | quality_gate_check | phase=audit | 检查审计阶段质量门禁 |

## 降级策略

| MCP工具 | 降级方式 | 降级脚本/操作 |
|---------|----------|---------------|
| security_scan | 脚本调用 | python scripts/agentic-security-scanner.py |
| quality_gate_check | 脚本调用 | python scripts/skill-test.py --gate [gate_id] |

## 涉及Agent

| Agent | 角色 | 职责 |
|-------|------|------|
| security-auditor | 主导 | 安全漏洞扫描、合规检查、安全建议 |
| code-reviewer | 辅助 | 代码安全审查 |
| devops-engineer | 辅助 | 基础设施安全检查 |

## 命令描述

执行安全审计与合规检查，扫描代码中的安全漏洞并验证合规性，确保代码满足安全标准。该命令覆盖OWASP Top 10、SANS Top 25等常见安全标准。

## 触发条件

| 触发方式 | 说明 |
|----------|------|
| 命令输入 | 用户输入 `/audit` |
| 别名触发 | `/au` |
| 关键词触发 | 用户提及"安全审计"、"合规检查"、"security audit" |
| 自动触发 | `/sprint` 命令执行时自动调用Audit阶段 |
| 条件触发 | 代码变更涉及认证/授权/数据处理时 |

## 命令名称与语法

```
/audit [--standard=<标准>] [--scope=<范围>] [--severity=<严重级别>]
```

## 参数定义

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--standard` | enum | 否 | owasp | 审计标准：owasp/sans/pci/hipaa/gdpr/custom |
| `--scope` | enum | 否 | all | 审计范围：all/code/infra/dependencies |
| `--severity` | enum | 否 | medium | 最低报告严重级别：low/medium/high/critical |
| `--fix` | flag | 否 | false | 自动修复可修复的安全问题 |
| `--report` | enum | 否 | markdown | 报告格式：markdown/html/pdf/sarif |
| `--compliance-only` | flag | 否 | false | 仅执行合规检查 |

## 执行流程

> 标准五步框架：1. 输入验证 → 2. Agent调度 → 3. 任务执行 → 4. 结果验证 → 5. 输出交付

1. **输入验证**：校验`--standard`和`--scope`参数合法、确定审计文件范围
2. **Agent调度**：security-auditor主导安全扫描，code-reviewer辅助代码审查
3. **任务执行**：执行安全扫描→漏洞检测→合规检查→风险评估→修复建议的完整审计流程
4. **结果验证**：执行quality_gate_check(phase=audit)
5. **输出交付**：生成安全审计报告、合规报告、修复建议

## 质量门禁

| 门禁标识 | 阻塞级别(BLOCK/WARN) | 通过标准 |
|----------|----------------------|----------|
| AUDIT-NO-CRITICAL | BLOCK | 无严重安全漏洞、无硬编码密钥 |
| AUDIT-NO-HIGH | BLOCK | 无高危安全漏洞 |
| AUDIT-COMPLIANCE | WARN | 合规检查通过、无合规风险 |

## 使用示例

### 示例1：OWASP审计

```
/audit
```

### 示例2：PCI合规审计

```
/audit --standard=pci
```

### 示例3：仅依赖审计

```
/audit --scope=dependencies
```

### 示例4：自动修复

```
/audit --fix
```

### 示例5：SARIF报告

```
/audit --report=sarif
```

## 相关脚本

- `scripts/agentic-security-scanner.py` - 安全扫描器，扫描代码中的安全漏洞
- `scripts/skill-test.py` - 技能测试器，执行质量门禁检查

---

## 相关命令

- `/review` - 代码审查
- `/fix` - 修复缺陷
- `/deploy` - 部署交付
- `/sprint` - 启动完整冲刺
