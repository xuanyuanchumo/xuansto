---
name: /review
aliases:
  - r
category: workflow
phase: "5"
description: 代码审查与规范检查
trigger: 需要审查代码质量或合规性时
workflow: subagent-driven-workflow
---

# /review 命令

## 命令描述

`/review` 命令用于执行代码审查与质量检查，是质量保障体系的核心命令。该命令触发多维度代码审查流程，包括静态分析、安全扫描、架构合规检查等，确保代码质量符合项目标准。

## 触发条件

| 触发方式 | 说明 |
|----------|------|
| 命令输入 | 用户输入 `/review` |
| 关键词触发 | 用户提及"代码审查"、"Code Review"、"质量检查" |
| 自动触发 | `/implement` 完成后自动触发代码审查 |
| 流程触发 | `/fix` 修复完成后自动触发审查验证 |

## 命令名称与语法

```
/review [target] [options]
```

## 参数定义

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| target | string | 否 | 当前工作目录 | 审查目标路径或文件 |
| --scope | string | 否 | full | 审查范围：full/quick/security/performance/staged/file/dir/pr |
| --depth | string | 否 | standard | 审查深度：shallow/standard/deep |
| --format | string | 否 | markdown | 输出格式：markdown/json/html |
| --output | string | 否 | console | 输出目标：console/file/both |
| --strict | boolean | 否 | false | 严格模式，任何警告都视为错误 |
| --fix | boolean | 否 | false | 自动修复可修复的问题 |
| --baseline | string | 否 | null | 对比基线版本或提交 |
| --exclude | string[] | 否 | [] | 排除的文件或目录模式 |
| --confidence-threshold | int | 否 | 80 | Multi-Perspective Review置信度过滤阈值（0-100） |
| --focus-areas | string[] | 否 | [] | 专注审查领域：security/performance/accessibility/compliance/bug/history/comments |
| --multi-perspective | boolean | 否 | false | 启用Multi-Perspective Review模式，调度5个子代理并行审查 |

## 执行流程

> 标准五步框架：1. 输入验证 → 2. Agent调度 → 3. 任务执行 → 4. 结果验证 → 5. 输出交付

### 执行步骤

1. **输入验证**：校验target路径存在、`--scope`和`--depth`参数合法、`--baseline`版本可访问；加载项目配置和规则集
2. **Agent调度**：code-reviewer主导审查流程，security-auditor负责安全扫描，`--multi-perspective`模式调度5个子代理(compliance-reviewer/bug-scanner/history-analyzer/comment-verifier/specification-keeper)并行审查
3. **任务执行**：执行静态分析→安全扫描→架构合规检查→测试覆盖分析→文档完整性检查的完整审查流程
4. **结果验证**：执行GATE-009/SPEC-CONSISTENCY/REVIEW-CONFIDENCE门禁检查，验证审查通过、无高危问题、置信度达标
5. **输出交付**：生成review-report.md、gate-status.json、issues.json，保存到.sprint/artifacts/review/

```
┌─────────────────────────────────────────────────────────────┐
│                    /review 执行流程                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. 初始化阶段                                               │
│     ├── 解析命令参数                                         │
│     ├── 确定审查范围和目标                                    │
│     ├── 加载项目配置和规则集                                  │
│     └── 初始化审查上下文                                      │
│                                                             │
│  2. 静态分析阶段                                             │
│     ├── 代码规范检查 (Lint)                                  │
│     ├── 复杂度分析 (Cyclomatic Complexity)                  │
│     ├── 重复代码检测 (Duplication)                          │
│     ├── 代码异味检测 (Code Smells)                           │
│     └── 依赖分析 (Dependency Analysis)                       │
│                                                             │
│  3. 安全扫描阶段                                             │
│     ├── 漏洞扫描 (Vulnerability Scan)                       │
│     ├── 敏感信息检测 (Secret Detection)                     │
│     ├── 依赖安全检查 (Supply Chain Security)                │
│     └── 权限配置审计 (Permission Audit)                      │
│                                                             │
│  4. 架构合规检查                                             │
│     ├── 设计模式遵循检查                                      │
│     ├── 模块边界验证                                         │
│     ├── 接口契约验证                                         │
│     └── 分层架构合规性                                       │
│                                                             │
│  5. 测试覆盖分析                                             │
│     ├── 单元测试覆盖率                                       │
│     ├── 集成测试覆盖率                                       │
│     ├── 边界条件覆盖                                         │
│     └── 测试质量评估                                         │
│                                                             │
│  6. 文档完整性检查                                           │
│     ├── API文档完整性                                        │
│     ├── 注释覆盖率                                           │
│     ├── README更新检查                                       │
│     └── 变更日志检查                                         │
│                                                             │
│  7. 汇总与报告                                               │
│     ├── 问题分类与优先级排序                                  │
│     ├── 生成审查报告                                         │
│     ├── 提供修复建议                                         │
│     ├── 简化机会检测：若审查发现 simplification-flag，建议执行 `/simplify` 命令 │
│     └── 更新质量门禁状态                                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 涉及Agent

| Agent | 角色 | 职责 |
|-------|------|------|
| code-reviewer | 主导 | 协调审查流程、代码质量审查 |
| security-auditor | 辅助 | 安全漏洞和风险分析 |
| doc-reviewer | 辅助 | 文档完整性和质量检查 |
| test-architect | 辅助 | 测试覆盖率和质量评估 |
| system-architect | 辅助 | 架构合规性验证 |
| compliance-officer | 辅助 | 规范遵循和合规检查 |

### Multi-Perspective Review子代理

启用`--multi-perspective`时，额外调度5个子代理：

| 子代理 | 审查视角 |
|--------|----------|
| compliance-reviewer | 合规性审查 |
| bug-scanner | 缺陷扫描 |
| history-analyzer | 历史上下文分析 |
| comment-verifier | 注释准确性验证 |
| specification-keeper | 规格一致性检查 |

## 输出格式

### 1. 审查报告 (review-report.md)

```markdown
# 代码审查报告

## 概要信息
- 审查时间: 2026-04-17 10:30:00
- 审查范围: src/
- 审查深度: standard
- 总体评分: 85/100

## 问题统计
| 级别 | 数量 | 占比 |
|------|------|------|
| 严重 | 0 | 0% |
| 高危 | 2 | 5% |
| 中等 | 8 | 20% |
| 低危 | 15 | 37.5% |
| 建议 | 20 | 37.5% |

## 详细问题列表
### 高危问题
1. [SEC-001] SQL注入风险 - src/db/queries.py:45
2. [ARCH-001] 循环依赖 - src/models/user.py

### 中等问题
...

## 修复建议
...
```

### 2. 质量门禁状态 (gate-status.json)

```json
{
  "gate_id": "GATE-007",
  "gate_name": "代码质量门禁",
  "status": "passed",
  "score": 85,
  "threshold": 80,
  "checks": {
    "lint": "passed",
    "security": "failed",
    "coverage": "passed",
    "complexity": "passed"
  },
  "blocking_issues": 0,
  "warnings": 8
}
```

### 3. 问题清单 (issues.json)

```json
{
  "issues": [
    {
      "id": "ISSUE-001",
      "type": "security",
      "severity": "high",
      "file": "src/db/queries.py",
      "line": 45,
      "message": "SQL注入风险：使用字符串拼接构建SQL查询",
      "suggestion": "使用参数化查询替代字符串拼接",
      "auto_fixable": true
    }
  ]
}
```

## 示例用法

### 示例1: 基础审查

```bash
/review
```

对当前工作目录执行标准代码审查。

### 示例2: 指定目标审查

```bash
/review src/auth --scope=security --depth=deep
```

对 `src/auth` 目录执行深度安全审查。

### 示例3: 快速审查并自动修复

```bash
/review --scope=quick --fix
```

执行快速审查并自动修复可修复的问题。

### 示例4: 与基线对比审查

```bash
/review --baseline=main --format=html --output=file
```

与 main 分支对比，生成 HTML 格式的审查报告并保存到文件。

### 示例5: 严格模式审查

```bash
/review --strict --exclude="**/*.test.js,**/vendor/**"
```

执行严格模式审查，排除测试文件和第三方库。

### 示例6: Multi-Perspective Review多视角审查

```bash
/review --multi-perspective --confidence-threshold 80
```

启用Multi-Perspective Review模式，调度5个子代理并行审查，仅保留置信度>=80的发现。

### 示例7: 专注安全与性能审查

```bash
/review --multi-perspective --focus-areas security,performance --scope pr
```

启用多视角审查，专注安全和性能领域，审查PR范围内的变更。

### 示例8: 暂存区快速审查

```bash
/review --scope staged --depth shallow
```

对暂存区变更执行浅层快速审查。

## 质量门禁

| 门禁标识 | 阻塞级别(BLOCK/WARN) | 通过标准 |
|----------|----------------------|----------|
| GATE-009 | BLOCK | 审查通过、无高危问题、代码规范合规 |
| SPEC-CONSISTENCY | WARN | 代码实现与规格文档一致、API契约验证通过 |
| REVIEW-CONFIDENCE | BLOCK | `--multi-perspective`模式：所有审查发现置信度≥`--confidence-threshold`阈值 |
| MULTI-PERSPECTIVE-COVERAGE | WARN | `--multi-perspective`模式：5个子代理全部完成审查 |
| SUBAGENT-REVIEW | BLOCK | 两阶段审查通过(计划合规+代码质量)、无返工任务 |

## 注意事项

1. **审查范围**: 确保审查范围覆盖所有变更文件
2. **基线对比**: 使用基线对比可减少噪音，聚焦实际变更
3. **自动修复**: `--fix` 选项仅修复安全且无歧义的问题
4. **严格模式**: 在 CI/CD 流水线中建议使用严格模式
5. **排除规则**: 合理使用排除规则避免误报

## 相关脚本

- `scripts/confidence-scorer.py` - 置信度评分器，为Multi-Perspective Review审查发现计算置信度分数
- `scripts/review-aggregator.py` - 审查聚合器，汇总多视角审查结果并生成综合报告
- `scripts/review-eligibility-check.py` - 审查资格检查器，验证代码变更是否符合审查条件

---

## 相关命令

- `/fix` - 修复审查发现的问题
- `/simplify` - 当审查发现 simplification-flag 时，执行代码简化
- `/test` - 运行测试验证修复
- `/accept` - 验收审查通过的代码
