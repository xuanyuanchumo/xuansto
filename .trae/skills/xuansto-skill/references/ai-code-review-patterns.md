# AI代码审查模式参考文档

> 版本: 3.2.0 | 更新日期: 2026-05-06 | 编码: UTF-8 without BOM | 行尾: LF

---

## 概述

AI代码审查（AI Code Review）利用大语言模型辅助代码审查过程，通过结构化审查模式、自动化检查规则和审查质量度量，提升代码审查的效率和一致性。本文档描述AI驱动的代码审查模式、审查清单和与xuansto-skill的集成方式。

---

## 审查模式分类

### 模式一：安全优先审查（Security-First Review）

优先检查安全漏洞，适用于涉及认证、授权、数据处理的代码变更。

```yaml
security_first_review:
  priority_order:
    - 注入漏洞（SQL/NoSQL/Command/XSS）
    - 认证与授权缺陷
    - 敏感数据泄露
    - 加密实现错误
    - 输入验证缺失
  checks:
    - rule: "所有用户输入必须经过验证和清理"
      severity: critical
    - rule: "密码和密钥不得硬编码"
      severity: critical
    - rule: "SQL查询必须使用参数化语句"
      severity: critical
    - rule: "文件操作必须验证路径（防路径遍历）"
      severity: high
```

### 模式二：性能审查（Performance Review）

聚焦性能瓶颈和资源使用效率，适用于高频调用路径和大数据量场景。

```yaml
performance_review:
  focus_areas:
    - 算法复杂度（时间/空间）
    - 数据库查询效率（N+1问题、缺失索引）
    - 内存泄漏风险
    - 不必要的同步操作
    - 缓存策略合理性
  checks:
    - rule: "循环内禁止数据库查询"
      severity: high
    - rule: "大列表必须使用虚拟滚动或分页"
      severity: medium
    - rule: "异步操作不得阻塞主线程"
      severity: high
    - rule: "资源（连接/文件/流）必须确保释放"
      severity: critical
```

### 模式三：架构一致性审查（Architecture Consistency Review）

检查代码变更是否符合项目架构规范和设计模式。

```yaml
architecture_review:
  focus_areas:
    - 分层架构遵守（表示层/业务层/数据层）
    - 依赖方向正确性
    - 接口契约一致性
    - 模块边界清晰性
    - 设计模式正确应用
  checks:
    - rule: "表示层不得直接访问数据层"
      severity: high
    - rule: "跨模块调用必须通过公开接口"
      severity: high
    - rule: "新依赖必须经过审批"
      severity: medium
    - rule: "公共API必须有版本管理"
      severity: medium
```

### 模式四：可维护性审查（Maintainability Review）

评估代码的可读性、可测试性和长期维护成本。

```yaml
maintainability_review:
  focus_areas:
    - 命名清晰度
    - 函数长度和复杂度
    - 代码重复度
    - 注释质量
    - 测试覆盖率
  checks:
    - rule: "函数长度不超过50行"
      severity: medium
    - rule: "圈复杂度不超过10"
      severity: medium
    - rule: "重复代码块超过6行需提取"
      severity: low
    - rule: "公共方法必须有文档注释"
      severity: medium
```

---

## 审查流程

### 自动化审查流水线

```
代码提交 → 静态分析 → AI审查 → 人工审查 → 合并
    │          │          │          │        │
    ├─ 格式检查 ├─ Lint规则  ├─ 模式匹配  ├─ 最终决策 ├─ 代码入库
    ├─ 类型检查 ├─ 安全扫描  ├─ 上下文理解 ├─ 业务逻辑 ├─ 文档更新
    └─ 构建验证 └─ 依赖检查  └─ 建议生成  └─ 风险评估 └─ 变更通知
```

### AI审查触发条件

```yaml
ai_review_trigger:
  auto_trigger:
    - PR创建或更新
    - 涉及安全敏感文件
    - 变更行数超过阈值（>200行）
  manual_trigger:
    - 开发者主动请求
    - 审查者需要AI辅助
  skip_conditions:
    - 仅文档变更
    - 仅配置格式调整
    - 自动生成的代码
```

---

## 审查输出格式

```yaml
review_output:
  summary: "审查摘要：发现2个高优先级问题，3个建议"
  findings:
    - id: "CR-001"
      severity: critical
      category: security
      file: "src/auth/login.ts"
      line: 42
      message: "SQL注入风险：使用字符串拼接构建查询"
      suggestion: "使用参数化查询替代字符串拼接"
      reference: "OWASP-A1"
    - id: "CR-002"
      severity: high
      category: performance
      file: "src/api/users.ts"
      line: 78
      message: "N+1查询：循环内执行数据库查询"
      suggestion: "使用批量查询或JOIN优化"
      reference: "PERF-003"
  metrics:
    files_reviewed: 5
    lines_reviewed: 342
    issues_found: 5
    critical: 1
    high: 1
    medium: 2
    low: 1
```

---

## 审查质量度量

| 指标 | 目标值 | 计算方式 |
|------|--------|---------|
| 误报率 | <15% | 误报数/总报告数 |
| 漏报率 | <5% | 遗漏缺陷数/实际缺陷数 |
| 审查覆盖率 | ≥90% | 已审查文件数/变更文件数 |
| 平均审查时间 | <5min | 总审查时间/审查次数 |
| 建议采纳率 | ≥60% | 被采纳建议数/总建议数 |

---

## 与xuansto-skill的集成

| xuansto模块 | AI代码审查 | 集成方式 |
|------------|-----------|---------|
| Code Reviewer Agent | 审查模式执行 | Agent使用审查清单 |
| Quality Gates | 审查门禁 | 严重问题阻断合并 |
| Security Auditor | 安全优先审查 | 安全检查规则同步 |
| Knowledge Base | 审查经验积累 | 常见问题模式入库 |

---

> 本文档由 Multi-Agent SDD/TDD Orchestrator 维护 | 最后更新: 2026-05-06
