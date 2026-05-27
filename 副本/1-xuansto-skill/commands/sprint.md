# /sprint 命令

## 命令描述

启动完整的SDD+TDD冲刺周期，执行从需求分析到代码交付的全流程开发。该命令是核心入口点，协调所有Agent按照三省六部二十四司机制协同工作。

## 使用语法

```
/sprint <需求描述> [--phase=<阶段>] [--agents=<Agent列表>] [--dry-run]
```

## 参数说明

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `<需求描述>` | string | 是 | - | 功能需求或用户故事描述 |
| `--phase` | enum | 否 | all | 指定起始阶段：all/clarify/plan/spec/design/implement/test/deploy |
| `--agents` | list | 否 | auto | 手动指定参与的Agent，用逗号分隔 |
| `--dry-run` | flag | 否 | false | 模拟运行，不执行实际操作 |
| `--skip-tests` | flag | 否 | false | 跳过测试阶段（仅用于紧急修复） |
| `--parallel` | flag | 否 | true | 启用并行Agent执行 |

## 执行流程

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

## 涉及的Agent

### 核心Agent（始终参与）

| Agent | 角色 | 职责 |
|-------|------|------|
| Product Manager | 产品经理 | 需求管理、优先级排序 |
| System Architect | 系统架构师 | 架构设计、技术选型 |
| Fullstack Engineer | 全栈工程师 | 核心开发实现 |
| Test Architect | 测试架构师 | 测试策略制定 |

### 按需调用的Agent

| Agent | 触发条件 |
|-------|----------|
| UI Designer | 涉及前端界面 |
| Backend Developer | 涉及后端逻辑 |
| Database Engineer | 涉及数据存储 |
| DevOps Engineer | 涉及部署配置 |
| Security Auditor | 涉及安全需求 |
| Performance Tester | 涉及性能要求 |

## 输出产物

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

## 质量门禁

每个阶段完成后自动执行质量检查：

| 阶段 | 质量门禁 |
|------|----------|
| Clarify | 无歧义、有验收标准 |
| Plan | 任务完整、依赖明确 |
| Spec | API契约完整、类型定义清晰 |
| Design | 设计评审通过 |
| Implement | 代码审查通过、静态分析通过 |
| Test | 测试覆盖率≥80%、所有测试通过 |
| Deploy | 部署验证通过、监控正常 |

## 错误处理

- **阶段失败**：自动回滚到上一阶段，记录失败原因
- **Agent超时**：触发备用Agent接管
- **依赖阻塞**：自动调整执行顺序或并行化

## 相关命令

- `/clarify` - 需求澄清
- `/plan` - 计划制定
- `/spec` - 规格编写
- `/design` - 设计流程
- `/implement` - TDD实现
- `/test` - 测试验证
