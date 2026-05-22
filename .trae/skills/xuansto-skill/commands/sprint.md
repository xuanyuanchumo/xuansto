---
name: /sprint
aliases:
  - s
category: workflow
phase: "cross-phase"
description: 冲刺规划与任务分解
trigger: 需要规划开发冲刺或分解任务时
workflow: sdd-tdd-full
---

# /sprint 命令

## 命令描述

启动完整的SDD+TDD冲刺周期，执行从需求分析到代码交付的全流程开发。该命令是核心入口点，协调所有Agent按照三省六部二十四司机制协同工作。

## 触发条件

| 触发方式 | 说明 |
|----------|------|
| 命令输入 | 用户输入 `/sprint` |
| 关键词触发 | 用户提及"冲刺规划"、"Sprint规划"、"迭代规划" |
| 流程触发 | 由其他命令自动调用启动完整开发周期 |

## 命令名称与语法

```
/sprint <需求描述> [--phase=<阶段>] [--agents=<Agent列表>] [--dry-run]
```

## 参数定义

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `<需求描述>` | string | 是 | - | 功能需求或用户故事描述 |
| `--phase` | enum | 否 | all | 指定起始阶段：all/clarify/plan/spec/design/implement/test/deploy |
| `--agents` | list | 否 | auto | 手动指定参与的Agent，用逗号分隔 |
| `--dry-run` | flag | 否 | false | 模拟运行，不执行实际操作 |
| `--skip-tests` | flag | 否 | false | 跳过测试阶段（仅用于紧急修复） |
| `--parallel` | flag | 否 | true | 启用并行Agent执行 |
| `--autonomous` | flag | 否 | false | 启用Ralph Loop模式，自主迭代直到完成 |

## 执行流程

> 标准五步框架：1. 输入验证 → 2. Agent调度 → 3. 任务执行 → 4. 结果验证 → 5. 输出交付

### 执行步骤

1. **输入验证**：校验需求描述非空、`--phase`参数合法、Agent列表有效；检查.sprint目录状态
2. **Agent调度**：orchestrator根据`--phase`和`--agents`参数分配Agent，建立Agent协作拓扑
3. **任务执行**：按Clarify→Plan→Spec→Design→Implement→Test→Deploy顺序执行各阶段，每阶段调用对应子命令
4. **结果验证**：每阶段完成后执行对应质量门禁检查，失败则回滚到上一阶段
5. **输出交付**：生成sprint-summary.md和metrics.json，归档所有产物到.sprint/目录

```
┌─────────────────────────────────────────────────────────────┐
│                    SDD+TDD 冲刺周期                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │ Clarify  │───▶│   Plan   │───▶│   Spec   │              │
│  │ 需求澄清  │    │ 计划制定  │    │ 规格编写  │              │
│  └──────────┘    └──────────┘    └──────────┘              │
│                                        │                    │
│                                        ▼                    │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │   Test   │◀───│ Implement│◀───│  Design  │              │
│  │ 测试验证  │    │ TDD实现   │    │ UI/UX设计 │              │
│  └──────────┘    └──────────┘    └──────────┘              │
│       │                                                    │
│       ▼                                                    │
│  ┌──────────┐                                              │
│  │  Deploy  │                                              │
│  │ 部署交付  │                                              │
│  └──────────┘                                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 阶段详情

1. **Clarify（需求澄清）**
   - 调用 `/clarify` 命令
   - 检测需求歧义
   - 生成澄清问题列表

2. **Plan（计划制定）**
   - 调用 `/plan` 命令
   - 分解任务
   - 分配Agent

3. **Spec（规格编写）**
   - 调用 `/spec` 命令
   - 编写技术规格
   - 定义API契约

4. **Design（设计阶段）**
   - 调用 `/design` 命令
   - UI/UX设计
   - 架构设计

5. **Implement（实现阶段）**
   - 调用 `/implement` 命令
   - TDD开发流程
   - 代码实现

6. **Test（测试阶段）**
   - 调用 `/test` 命令
   - 多层测试验证
   - 质量门禁

7. **Deploy（部署阶段）**
   - CI/CD流水线
   - 环境部署
   - 监控配置

## 涉及Agent

| Agent | 角色 | 职责 |
|-------|------|------|
| product-manager | 主导 | 需求管理、优先级排序 |
| orchestrator | 主导 | 冲刺流程协调、Agent调度、资源分配 |
| system-architect | 主导 | 架构设计、技术选型 |
| fullstack-engineer | 主导 | 核心开发实现 |
| test-architect | 主导 | 测试策略制定 |
| ui-designer | 辅助 | 前端界面设计 |
| backend-developer | 辅助 | 后端逻辑开发 |
| database-engineer | 辅助 | 数据存储设计 |
| devops-engineer | 辅助 | 部署配置管理 |
| security-auditor | 辅助 | 安全需求审计 |
| performance-tester | 辅助 | 性能测试验证 |

## 输出格式

```
.sprint/
├── artifacts/
│   ├── requirements/
│   │   ├── clarified-requirements.md
│   │   └── acceptance-criteria.md
│   ├── design/
│   │   ├── architecture.md
│   │   ├── api-spec.yaml
│   │   └── ui-mockups/
│   ├── implementation/
│   │   ├── source-code/
│   │   └── configuration/
│   └── testing/
│       ├── test-plans.md
│       ├── test-results.md
│       └── coverage-report.html
├── decisions/
│   └── decision-log.md
└── reports/
    ├── sprint-summary.md
    └── metrics.json
```

## 示例用法

### 示例1：启动完整冲刺

```
/sprint 实现用户登录功能，支持邮箱和手机号登录，包含OAuth2.0第三方登录
```

### 示例2：从特定阶段开始

```
/sprint 实现购物车功能 --phase=design
```

### 示例3：模拟运行

```
/sprint 实现支付系统 --dry-run
```

### 示例4：指定Agent

```
/sprint 实现数据报表 --agents=backend-developer,database-engineer,test-architect
```

### 示例5：自主迭代模式

```
/sprint 实现用户认证系统 --autonomous
```

启用Ralph Loop模式，orchestrator将自主迭代执行直到任务完成。与 `/loop` 命令等效，适合需要完全自主执行的场景。循环受最大迭代数（默认50）、停滞检测（连续3次无进展暂停）和Token预算约束，可随时通过 `/cancel-loop` 取消。

## 质量门禁

| 门禁标识 | 阻塞级别(BLOCK/WARN) | 通过标准 |
|----------|----------------------|----------|
| GATE-001 | BLOCK | 需求无歧义、验收标准可测试 |
| GATE-002 | BLOCK | API契约完整、类型定义清晰 |
| LOOP-COMPLETION | BLOCK | `--autonomous`模式：所有迭代任务完成、目标达成 |
| ITERATION-BUDGET | WARN | `--autonomous`模式：迭代次数未超预算(默认50)、Token消耗在预算内 |
| TOKEN-BUDGET | WARN/BLOCK | Token使用率<80%正常，80%-100%触发压缩，≥100%强制串行 |

每个阶段完成后自动执行质量检查：

| 阶段 | 质量门禁 |
|------|----------|
| Clarify | GATE-001：无歧义、有验收标准 |
| Plan | GATE-003：任务完整、依赖明确 |
| Spec | GATE-002/GATE-004：API契约完整、类型定义清晰 |
| Design | DESIGN-REVIEW：设计评审通过 |
| Implement | GATE-007/TEST-PASS：代码审查通过、静态分析通过 |
| Test | GATE-005/GATE-011：测试覆盖率≥80%、所有测试通过 |
| Deploy | GATE-013：部署验证通过、监控正常 |

## 错误处理

- **阶段失败**：自动回滚到上一阶段，记录失败原因
- **Agent超时**：触发备用Agent接管
- **依赖阻塞**：自动调整执行顺序或并行化

## 相关脚本

- `scripts/init-session.py` - 会话初始化器，创建冲刺会话和工作目录结构
- `scripts/session-catchup.py` - 会话恢复器，从上次中断处恢复冲刺进度
- `scripts/check-complete.py` - 完成检查器，验证冲刺任务是否全部完成

---

## 相关命令

- `/clarify` - 需求澄清
- `/plan` - 计划制定
- `/spec` - 规格编写
- `/design` - 设计流程
- `/implement` - TDD实现
- `/test` - 测试验证
- `/loop` - 自主迭代循环（--autonomous模式的独立命令入口）
- `/cancel-loop` - 取消当前运行的循环
