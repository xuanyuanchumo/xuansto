---
name: /accept
aliases:
  - a
category: workflow
phase: "6"
description: 验收确认与交付
trigger: 需要确认功能验收或交付时
workflow: acceptance
---

# /accept 命令

## 命令描述

`/accept` 命令用于验收测试与确认，是交付流程的把关命令。该命令执行全面的验收测试，验证功能完整性、质量达标性和需求符合度，确保交付物满足验收标准后方可进入下一阶段。

---

## 触发条件

| 触发方式 | 说明 |
|----------|------|
| 命令输入 | 用户输入 `/accept` |
| 关键词触发 | 用户提及"验收"、"验收确认"、"验收测试" |
| 自动触发 | `/test` 全部测试通过后自动建议验收 |
| 流程触发 | `/fix` 修复验证通过后自动建议验收 |

---

## 命令名称与语法

```
/accept [feature|task-id] [options]
```

---

## 参数定义

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| feature | string | 否 | 当前任务 | 验收的功能名称或任务ID |
| --criteria | string | 否 | default | 验收标准集：default、strict、custom |
| --scope | string | 否 | full | 验收范围：full(全面)、smoke(冒烟)、regression(回归) |
| --report | boolean | 否 | true | 生成验收报告 |
| --sign-off | boolean | 否 | false | 验收通过后自动签核 |
| --stakeholder | string | 否 | - | 指定验收干系人 |
| --environment | string | 否 | staging | 验收环境：staging、production、local |
| --rollback | boolean | 否 | true | 验收失败自动回滚 |

---

## 执行流程

> 标准四步框架：1. 输入验证 → 2. Agent调度 → 3. 任务执行 → 4. 结果验证

```
┌─────────────────────────────────────────────────────────────┐
│                    /accept 执行流程                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. 准备阶段                                                 │
│     ├── 加载验收标准和检查清单                                │
│     ├── 确认验收环境和配置                                    │
│     ├── 准备验收测试数据                                      │
│     ├── 通知相关干系人                                        │
│     └── 创建验收快照                                         │
│                                                             │
│  2. 功能验收测试                                             │
│     ├── 用户故事验证                                         │
│     ├── 验收标准逐项检查                                      │
│     ├── 边界条件测试                                         │
│     ├── 异常场景测试                                         │
│     └── 用户流程端到端测试                                    │
│                                                             │
│  3. 质量验收检查                                             │
│     ├── 代码覆盖率验证                                       │
│     ├── 静态分析结果检查                                      │
│     ├── 安全扫描结果确认                                      │
│     ├── 性能基准验证                                         │
│     └── 技术债务评估                                         │
│                                                             │
│  4. 需求符合度验证                                           │
│     ├── 需求追溯矩阵检查                                      │
│     ├── 规格文档一致性验证                                    │
│     ├── 用户期望确认                                         │
│     └── 业务价值交付评估                                      │
│                                                             │
│  5. 集成验收测试                                             │
│     ├── 接口契约验证                                         │
│     ├── 数据一致性检查                                       │
│     ├── 第三方集成验证                                       │
│     └── 跨系统流程验证                                       │
│                                                             │
│  6. 非功能性验收                                             │
│     ├── 性能指标验证                                         │
│     ├── 安全合规检查                                         │
│     ├── 可访问性验证                                         │
│     ├── 兼容性测试                                           │
│     └── 可维护性评估                                         │
│                                                             │
│  7. 文档验收                                                 │
│     ├── API文档完整性                                        │
│     ├── 用户文档更新                                         │
│     ├── 运维文档准备                                         │
│     └── 变更日志确认                                         │
│                                                             │
│  7.5 Definition of Done检查                                  │
│     ├── 代码审查通过（code_review_passed）                    │
│     ├── 测试覆盖率达标（test_coverage_met）                   │
│     ├── 安全扫描清洁（security_scan_clean）                   │
│     ├── 文档完整（docs_complete）                             │
│     ├── 性能未退化（performance_not_degraded）                │
│     └── 设计一致性≥95%（design_consistency_gte_95）          │
│                                                             │
│  8. 决策与签核                                               │
│     ├── 汇总验收结果                                         │
│     ├── 生成验收报告                                         │
│     ├── 执行签核流程                                         │
│     └── 更新项目状态                                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 涉及Agent

| Agent | 角色 | 职责 |
|-------|------|------|
| product-manager | 主导 | 验收标准确认、业务价值评估 |
| qa-engineer | 辅助 | 质量聚合与验收汇总 |
| test-architect | 辅助 | 验收测试设计与执行 |
| e2e-tester | 辅助 | 端到端验收测试 |
| performance-tester | 辅助 | 性能验收测试 |
| security-auditor | 辅助 | 安全合规验收 |
| doc-reviewer | 辅助 | 文档完整性验收 |
| compliance-officer | 辅助 | 合规性检查 |

---

## 输出格式

### 1. 验收报告 (acceptance-report.md)

```markdown
# 验收测试报告

## 基本信息
- 验收时间: 2026-04-17 14:00:00
- 验收功能: 用户认证模块
- 验收环境: staging
- 验收人: Product Manager, QA Lead

## 验收结果概览

| 验收类别 | 通过项 | 失败项 | 通过率 |
|----------|--------|--------|--------|
| 功能验收 | 15 | 0 | 100% |
| 质量验收 | 8 | 0 | 100% |
| 需求符合 | 10 | 0 | 100% |
| 集成验收 | 5 | 0 | 100% |
| 非功能验收 | 6 | 1 | 85.7% |
| 文档验收 | 4 | 0 | 100% |
| **总计** | **48** | **1** | **98%** |

## 验收标准检查清单

### US-001: 用户登录
- [x] 用户可以使用邮箱和密码登录
- [x] 登录失败显示正确错误信息
- [x] 连续失败5次锁定账户
- [x] 支持记住我功能

### US-002: 密码重置
- [x] 用户可以请求密码重置邮件
- [x] 重置链接24小时内有效
- [x] 新密码符合安全策略

## 未通过项详情

### PERF-001: 响应时间超标
- 预期: < 200ms
- 实际: 350ms
- 影响: 用户体验
- 建议: 优化数据库查询

## 验收结论
- 状态: ⚠️ 有条件通过
- 条件: PERF-001需在发布前修复
- 签核人: [待签核]
```

### 2. 验收检查清单 (checklist.json)

```json
{
  "checklist_id": "ACC-20260417-001",
  "feature": "用户认证模块",
  "items": [
    {
      "id": "AC-001",
      "category": "functional",
      "description": "用户可以使用邮箱登录",
      "status": "passed",
      "evidence": "test_login_email.py::test_valid_login"
    },
    {
      "id": "AC-002",
      "category": "functional",
      "description": "登录失败显示错误信息",
      "status": "passed",
      "evidence": "test_login_email.py::test_invalid_login"
    }
  ],
  "summary": {
    "total": 49,
    "passed": 48,
    "failed": 1,
    "blocked": 0
  }
}
```

### 3. 签核记录 (sign-off.json)

```json
{
  "sign_off_id": "SO-20260417-001",
  "feature": "用户认证模块",
  "status": "conditional_pass",
  "conditions": [
    {
      "id": "COND-001",
      "description": "修复PERF-001性能问题",
      "deadline": "2026-04-18",
      "responsible": "backend-developer"
    }
  ],
  "approvers": [
    {
      "role": "product-manager",
      "status": "approved",
      "timestamp": "2026-04-17T14:30:00Z"
    },
    {
      "role": "qa-lead",
      "status": "approved",
      "timestamp": "2026-04-17T14:35:00Z"
    }
  ]
}
```

---

## 示例用法

### 示例1: 基础验收

```bash
/accept
```

对当前任务执行标准验收测试。

### 示例2: 指定功能验收

```bash
/accept user-auth --criteria=strict
```

对用户认证模块执行严格验收标准。

### 示例3: 冒烟测试验收

```bash
/accept --scope=smoke --environment=production
```

在生产环境执行冒烟测试验收。

### 示例4: 自动签核验收

```bash
/accept --sign-off --stakeholder="PM,QA"
```

验收通过后自动执行签核流程。

### 示例5: 回归验收

```bash
/accept --scope=regression --report
```

执行回归测试验收并生成报告。

---

## 验收标准集说明

### Default（默认标准）

```
功能验收:
  - 所有用户故事验收标准通过
  - 核心功能流程验证通过
  - 无阻塞性缺陷

质量验收:
  - 代码覆盖率 >= 80%
  - 无高危安全问题
  - 静态分析无严重问题

文档验收:
  - API文档更新
  - 变更日志记录
```

### Strict（严格标准）

```
功能验收:
  - 所有验收标准100%通过
  - 边界条件全覆盖
  - 异常场景全覆盖

质量验收:
  - 代码覆盖率 >= 90%
  - 无任何安全问题
  - 性能基准达标
  - 技术债务清零

文档验收:
  - 完整用户文档
  - 运维手册更新
  - API文档完整
```

### Custom（自定义标准）

```
从配置文件加载自定义验收标准:
  - .trae/acceptance-criteria.yaml
  - 项目根目录 acceptance-criteria.json
```

---

## 质量门禁

| 门禁标识 | 阻塞级别(BLOCK/WARN) | 通过标准 |
|----------|----------------------|----------|
| GATE-013 | BLOCK | 功能验收100%通过、质量验收达标、文档完整 |
| GATE-014 | BLOCK | 性能指标达标、安全合规通过、用户体验验证 |
| UX-ACCEPTANCE | WARN | UI/UX设计符合度验证、交互体验达标、无障碍合规 |
---

## 注意事项

1. **环境隔离**: 验收应在独立环境进行，避免影响生产
2. **数据准备**: 确保验收测试数据完整且符合场景
3. **回滚机制**: 验收失败时自动回滚，保护环境稳定
4. **自主模式签核**: 当 `human_collaboration.loop_mode: autonomous` 时，验收通过后自动签核（等效 `--sign-off`），验收失败时自动重试修复（最多 `acceptance_auto_retry_max` 次）
5. **条件通过**: 有条件通过时，自主模式下自动修复条件项后重新验收
6. **安全硬门禁**: 生产环境部署验收仍需人工确认（security_hard_gates: production_deploy）

---

## 相关脚本

- `scripts/uat-runner.py` - UAT测试运行器，执行用户验收测试并生成验收报告

---

## 相关命令

- `/review` - 验收前的代码审查
- `/fix` - 修复验收发现的问题
- `/deploy` - 验收通过后部署发布
