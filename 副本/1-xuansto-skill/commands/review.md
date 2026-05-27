# /review 命令

## 命令描述

`/review` 命令用于执行代码审查与质量检查，是质量保障体系的核心命令。该命令触发多维度代码审查流程，包括静态分析、安全扫描、架构合规检查等，确保代码质量符合项目标准。

---

## 使用语法

```
/review [target] [options]
```

---

## 参数说明

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| target | string | 否 | 当前工作目录 | 审查目标路径或文件 |
| --scope | string | 否 | full | 审查范围：full(全面)、quick(快速)、security(安全)、performance(性能) |
| --depth | string | 否 | standard | 审查深度：shallow(浅层)、standard(标准)、deep(深度) |
| --format | string | 否 | markdown | 输出格式：markdown、json、html |
| --output | string | 否 | console | 输出目标：console、file、both |
| --strict | boolean | 否 | false | 严格模式，任何警告都视为错误 |
| --fix | boolean | 否 | false | 自动修复可修复的问题 |
| --baseline | string | 否 | null | 对比基线版本或提交 |
| --exclude | string[] | 否 | [] | 排除的文件或目录模式 |

---

## 执行流程

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
│     └── 更新质量门禁状态                                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 涉及的Agent

| Agent角色 | 职责 | 参与阶段 |
|-----------|------|----------|
| code-reviewer | 主审查员，协调审查流程 | 全流程 |
| security-auditor | 安全漏洞和风险分析 | 安全扫描阶段 |
| doc-reviewer | 文档完整性和质量检查 | 文档检查阶段 |
| test-architect | 测试覆盖率和质量评估 | 测试分析阶段 |
| system-architect | 架构合规性验证 | 架构检查阶段 |
| compliance-officer | 规范遵循和合规检查 | 静态分析阶段 |

---

## 输出产物

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

---

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

---

## 质量门禁关联

| 门禁ID | 门禁名称 | 触发条件 |
|--------|----------|----------|
| GATE-007 | 代码质量门禁 | 静态分析检查 |
| GATE-009 | 代码审查门禁 | 审查完成验证 |
| GATE-012 | 安全扫描门禁 | 安全扫描检查 |

---

## 注意事项

1. **审查范围**: 确保审查范围覆盖所有变更文件
2. **基线对比**: 使用基线对比可减少噪音，聚焦实际变更
3. **自动修复**: `--fix` 选项仅修复安全且无歧义的问题
4. **严格模式**: 在 CI/CD 流水线中建议使用严格模式
5. **排除规则**: 合理使用排除规则避免误报

---

## 相关命令

- `/fix` - 修复审查发现的问题
- `/test` - 运行测试验证修复
- `/accept` - 验收审查通过的代码
