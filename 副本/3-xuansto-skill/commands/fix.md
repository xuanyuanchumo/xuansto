---
name: /fix
aliases:
  - f
category: workflow
phase: "6"
description: Bug修复与问题解决
trigger: 需要修复Bug或解决问题时
workflow: bug-fix
---

# /fix 命令

## 命令描述

`/fix` 命令用于问题修复与迭代改进，是质量闭环的关键命令。该命令接收审查报告或问题清单，自动分析问题根因，制定修复方案，执行修复并验证结果，确保问题得到彻底解决。

---

## 触发条件

| 触发方式 | 说明 |
|----------|------|
| 命令输入 | 用户输入 `/fix` |
| 关键词触发 | 用户提及"Bug修复"、"问题修复"、"hotfix" |
| 自动触发 | `/review` 审查发现高危问题时自动建议 |
| 流程触发 | `/audit` 安全审计发现漏洞时自动建议 |

---

## 命令名称与语法

```
/fix [issue-id|issue-file] [options]
```

---

## 参数定义

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| issue-id | string | 否 | - | 单个问题ID，如 ISSUE-001 |
| issue-file | string | 否 | - | 问题清单文件路径 |
| --all | boolean | 否 | false | 修复所有可修复的问题 |
| --severity | string | 否 | high | 修复的问题级别：critical、high、medium、low、all |
| --auto | boolean | 否 | false | 全自动修复模式，无需确认 |
| --dry-run | boolean | 否 | false | 模拟运行，只显示修复计划 |
| --verify | boolean | 否 | true | 修复后自动验证 |
| --max-iterations | number | 否 | 3 | 最大迭代修复次数 |
| --strategy | string | 否 | conservative | 修复策略：conservative(保守)、aggressive(激进)、balanced(平衡) |
| --backup | boolean | 否 | true | 修复前自动备份 |
| --security | boolean | 否 | false | 安全修复闭环模式，触发完整6步闭环流程 |

---

## 执行流程

> 标准四步框架：1. 输入验证 → 2. Agent调度 → 3. 任务执行 → 4. 结果验证

```
┌─────────────────────────────────────────────────────────────┐
│                    /fix 执行流程                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. 问题分析阶段                                             │
│     ├── 加载问题清单或审查报告                                │
│     ├── 解析问题详情和上下文                                  │
│     ├── 问题分类与优先级排序                                  │
│     ├── 依赖关系分析                                         │
│     └── 生成问题影响范围图                                    │
│                                                             │
│  2. 根因分析阶段                                             │
│     ├── 代码上下文分析                                       │
│     ├── 历史变更追溯                                         │
│     ├── 相关问题关联分析                                      │
│     ├── 确定根本原因                                         │
│     └── 记录分析过程到 Decision Log                          │
│                                                             │
│  3. 修复方案设计                                             │
│     ├── 生成多个候选修复方案                                  │
│     ├── 评估方案风险和影响                                    │
│     ├── 选择最优修复方案                                     │
│     ├── 制定详细修复步骤                                      │
│     └── 预估修复时间和资源                                    │
│                                                             │
│  4. 执行修复阶段                                             │
│     ├── 创建备份点                                           │
│     ├── 应用代码变更                                         │
│     ├── 更新相关文档                                         │
│     ├── 调整测试用例（如需要）                                │
│     └── 记录变更日志                                         │
│                                                             │
│  5. 验证阶段                                                 │
│     ├── 运行相关单元测试                                      │
│     ├── 执行集成测试                                         │
│     ├── 静态分析验证                                         │
│     ├── 回归测试（如需要）                                    │
│     └── 验证问题是否解决                                      │
│                                                             │
│  6. 迭代优化阶段                                             │
│     ├── 检查是否引入新问题                                    │
│     ├── 评估修复质量                                         │
│     ├── 如有问题则迭代修复                                    │
│     └── 达到最大迭代次数或修复成功                            │
│                                                             │
│  7. 完成阶段                                                 │
│     ├── 生成修复报告                                         │
│     ├── 更新问题状态                                         │
│     ├── 提交变更（如配置）                                    │
│     └── 触发后续流程（如需要）                                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 涉及Agent

| Agent | 角色 | 职责 |
|-------|------|------|
| backend-developer | 主导 | 后端代码修复 |
| frontend-developer | 辅助 | 前端代码修复 |
| refactoring-specialist | 辅助 | 代码重构优化 |
| unit-tester | 辅助 | 测试用例调整 |
| code-reviewer | 辅助 | 修复质量验证 |
| security-auditor | 辅助 | 安全问题修复 |

---

## 输出格式

### 1. 修复报告 (fix-report.md)

```markdown
# 问题修复报告

## 修复概要
- 修复时间: 2026-04-17 11:00:00
- 问题总数: 10
- 已修复: 8
- 需人工处理: 2
- 修复成功率: 80%

## 修复详情

### ISSUE-001: SQL注入风险
- 状态: ✅ 已修复
- 文件: src/db/queries.py
- 修复方案: 使用参数化查询替代字符串拼接
- 验证结果: 测试通过，安全扫描通过

### ISSUE-002: 循环依赖
- 状态: ✅ 已修复
- 文件: src/models/user.py
- 修复方案: 引入依赖注入模式
- 验证结果: 导入检查通过

### ISSUE-003: 复杂度过高
- 状态: ⚠️ 需人工处理
- 原因: 需要业务逻辑重构，超出自动修复范围
- 建议: 将方法拆分为多个职责单一的函数

## 变更统计
- 文件修改: 5
- 代码行变更: +45/-23
- 测试用例调整: 2
```

### 2. 变更记录 (changes.json)

```json
{
  "changes": [
    {
      "issue_id": "ISSUE-001",
      "file": "src/db/queries.py",
      "change_type": "modification",
      "lines_added": 5,
      "lines_removed": 3,
      "backup_path": ".backup/queries.py.20260417-110000"
    }
  ],
  "total_files": 5,
  "total_lines_added": 45,
  "total_lines_removed": 23
}
```

### 3. 验证结果 (verification.json)

```json
{
  "verification_time": "2026-04-17T11:15:00Z",
  "tests_run": 45,
  "tests_passed": 45,
  "tests_failed": 0,
  "lint_status": "passed",
  "security_scan": "passed",
  "issues_introduced": 0
}
```

---

## 示例用法

### 示例1: 修复单个问题

```bash
/fix ISSUE-001
```

修复指定ID的问题。

### 示例2: 从文件批量修复

```bash
/fix issues.json --severity=high --auto
```

从问题清单文件修复所有高危问题，无需确认。

### 示例3: 修复所有问题

```bash
/fix --all --verify
```

修复所有可自动修复的问题并验证。

### 示例4: 模拟修复

```bash
/fix --all --dry-run
```

显示修复计划但不实际执行。

### 示例5: 激进策略修复

```bash
/fix --all --strategy=aggressive --max-iterations=5
```

使用激进策略修复，最多迭代5次。

### 示例6: 安全修复闭环模式

```bash
/fix ISSUE-001 --security
```

对安全漏洞执行完整的6步闭环流程：Discovery → Verification → Fix → Regression Test → Re-test → Closure Confirmation。

---

## 安全修复闭环模式 (`--security`)

当使用 `--security` 标志时，`/fix` 命令进入安全修复闭环模式，执行完整的6步安全修复闭环流程：

### 闭环流程

```
┌─────────────────────────────────────────────────────────────┐
│              /fix --security 安全修复闭环流程                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Step 1: Discovery（漏洞发现）                               │
│     ├── 负责Agent: ai-penetration-tester / penetration-tester│
│     ├── 验证标准: 漏洞已记录，含PoC和CVSS评分                  │
│     └── 输出: 漏洞报告                                       │
│                                                             │
│  Step 2: Verification（漏洞验证）                             │
│     ├── 负责Agent: security-auditor                          │
│     ├── 验证标准: 漏洞真实性确认，排除误报                      │
│     └── 输出: 漏洞验证报告                                    │
│                                                             │
│  Step 3: Fix（修复实施）                                      │
│     ├── 负责Agent: backend-developer / frontend-developer    │
│     ├── 验证标准: 修复代码通过代码审查，无新增安全问题            │
│     └── 输出: 修复代码 + 修复说明文档                          │
│                                                             │
│  Step 4: Regression Test（回归测试）                          │
│     ├── 负责Agent: unit-tester / test-architect              │
│     ├── 验证标准: 回归测试全部通过，修复未引入新缺陷             │
│     └── 输出: 回归测试报告                                    │
│                                                             │
│  Step 5: Re-test（复测确认）                                  │
│     ├── 负责Agent: penetration-tester / ai-penetration-tester│
│     ├── 验证标准: 原漏洞不可复现，无残留风险                    │
│     └── 输出: 复测报告                                       │
│                                                             │
│  Step 6: Closure Confirmation（闭环确认）                     │
│     ├── 负责Agent: security-auditor                          │
│     ├── 验证标准: SECURITY-FIX-CLOSED门禁通过                  │
│     └── 输出: 安全修复闭环确认书                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 门禁要求

安全修复闭环模式下的额外门禁：

| 门禁标识 | 阻塞级别 | 通过标准 |
|----------|---------|---------|
| SECURITY-FIX-CLOSED | BLOCK | 漏洞已验证修复 + 回归测试通过 + 复测确认无残留风险 |
| GATE-009 | BLOCK | 修复代码审查通过 |
| GATE-012 | BLOCK | 安全扫描通过，无新增漏洞 |

### 异常处理

| 异常场景 | 处理方式 |
|----------|---------|
| Verification判定为误报 | 关闭漏洞，记录误报原因 |
| Fix引入新安全问题 | 回滚修复，重新进入Fix步骤 |
| Regression Test失败 | 返回Fix步骤修复新引入的问题 |
| Re-test发现残留风险 | 返回Fix步骤补充修复 |
| 闭环超时（>7天未关闭） | 自动升级为P0，通知Orchestrator介入 |

---

## 修复策略说明

### Conservative（保守策略）

```
特点:
  - 仅修复100%确定安全的问题
  - 保留原有代码风格
  - 最小化变更范围
  - 需要人工确认高风险修复

适用场景:
  - 生产环境代码
  - 关键业务逻辑
  - 首次修复尝试
```

### Balanced（平衡策略）

```
特点:
  - 修复大部分可自动修复的问题
  - 允许适度的代码重构
  - 平衡风险和效率
  - 自动处理中等风险问题

适用场景:
  - 开发环境代码
  - 常规问题修复
  - 推荐默认策略
```

### Aggressive（激进策略）

```
特点:
  - 修复所有检测到的问题
  - 允许较大范围重构
  - 自动处理高风险问题
  - 可能引入较大变更

适用场景:
  - 重构阶段
  - 技术债务清理
  - 需配合充分测试
```

---

## 质量门禁

| 门禁标识 | 阻塞级别(BLOCK/WARN) | 通过标准 |
|----------|----------------------|----------|
| TEST-PASS | BLOCK | 所有相关测试通过、无回归问题 |
| GATE-009 | BLOCK | 修复代码审查通过、无新增问题 |
| SECURITY-FIX-CLOSED | BLOCK | 安全修复闭环验证通过（仅--security模式） |
---

## 注意事项

1. **备份机制**: 默认开启备份，可在 `.backup/` 目录找到备份文件
2. **迭代限制**: 最大迭代次数防止无限循环
3. **人工介入**: 部分复杂问题需人工处理，命令会明确标注
4. **验证重要性**: 建议始终开启验证确保修复正确
5. **策略选择**: 根据代码重要性和风险承受能力选择策略

---

## 相关脚本

- `scripts/context-compressor.py` - 上下文压缩器，压缩问题上下文信息以优化Token使用

---

## 相关命令

- `/review` - 执行代码审查发现问题
- `/test` - 运行测试验证修复
- `/accept` - 验收修复结果
