# AgentForge 执行验证多Agent框架参考文档

> 版本: 3.2.0 | 更新日期: 2026-05-06 | 编码: UTF-8 without BOM | 行尾: LF

---

## 概述

AgentForge 是一套执行验证型多Agent框架，核心特征是所有Agent输出必须通过Docker沙箱验证后才能被接受。在SWE-bench Lite基准测试中达到40.0%的问题解决率。框架包含5个专业化角色，通过结构化协作流程实现高质量代码生成。

---

## 五大核心角色

### 1. Planner（规划者）

**职责：** 分析问题、制定执行计划、分配子任务

```yaml
planner:
  responsibilities:
    - 问题分析与理解
    - 执行计划制定
    - 子任务分解与分配
    - 依赖关系梳理
  input: issue_description
  output: execution_plan
  constraints:
    - 计划必须包含验证检查点
    - 每个子任务必须有明确的完成条件
    - 依赖关系必须显式声明
```

**计划结构：**

```yaml
execution_plan:
  issue_id: "SWE-12345"
  steps:
    - id: step-1
      task: "定位bug根因"
      assigned_to: Coder
      depends_on: []
      validation: "根因分析报告包含堆栈跟踪和代码位置"
    - id: step-2
      task: "编写修复代码"
      assigned_to: Coder
      depends_on: [step-1]
      validation: "修复代码通过单元测试"
    - id: step-3
      task: "验证修复"
      assigned_to: Tester
      depends_on: [step-2]
      validation: "所有测试通过，无回归"
```

### 2. Coder（编码者）

**职责：** 根据计划编写代码实现

```yaml
coder:
  responsibilities:
    - 代码实现
    - 单元测试编写
    - 代码自检
  input: execution_plan_step
  output: code_changes
  constraints:
    - 必须先编写测试再编写实现
    - 代码变更必须最小化
    - 必须遵循项目代码规范
```

### 3. Tester（测试者）

**职责：** 验证代码正确性、执行测试套件

```yaml
tester:
  responsibilities:
    - 测试执行与验证
    - 回归测试
    - 边界条件测试
  input: code_changes
  output: test_report
  constraints:
    - 必须在Docker沙箱中执行
    - 测试结果必须可复现
    - 失败测试必须提供详细错误信息
```

### 4. Debugger（调试者）

**职责：** 分析失败原因、定位问题、提出修复方案

```yaml
debugger:
  responsibilities:
    - 失败根因分析
    - 问题定位
    - 修复方案建议
  input: test_report (failed)
  output: debug_analysis
  constraints:
    - 必须提供最小复现步骤
    - 修复方案必须经过验证
    - 不得直接修改代码（交由Coder执行）
```

### 5. Critic（评审者）

**职责：** 代码质量评审、最终决策

```yaml
critic:
  responsibilities:
    - 代码质量评审
    - 方案可行性评估
    - 最终接受/拒绝决策
  input: code_changes + test_report + debug_analysis
  output: review_decision
  constraints:
    - 必须基于客观标准评审
    - 拒绝必须提供具体改进建议
    - 最多允许3轮修改循环
```

---

## Docker沙箱验证

### 验证流程

```
代码提交 → Docker容器创建 → 依赖安装 → 测试执行 → 结果收集 → 容器销毁
    │            │               │           │           │            │
    └─ 隔离 ────┘── 可复现 ────┘── 安全 ───┘── 可信 ───┘── 清理 ────┘
```

### 沙箱配置

```yaml
docker_sandbox:
  base_image: "python:3.12-slim"
  resource_limits:
    cpu: 2
    memory: "4g"
    disk: "10g"
    timeout: 300
  network: none
  security:
    read_only_root: true
    no_new_privileges: true
    drop_capabilities: ALL
  verification:
    run_tests: true
    check_linting: true
    verify_types: true
    security_scan: true
```

### 验证结果格式

```yaml
verification_result:
  status: pass | fail | error
  test_results:
    total: 42
    passed: 42
    failed: 0
    skipped: 0
  lint_result:
    errors: 0
    warnings: 2
  type_check:
    errors: 0
  security_scan:
    vulnerabilities: 0
  execution_time: 12.5s
```

---

## SWE-bench Lite 40.0%解决率

### 性能指标

| 指标 | 值 | 说明 |
|------|-----|------|
| 解决率 | 40.0% | SWE-bench Lite基准 |
| 平均解决时间 | 8.5min | 从问题输入到验证通过 |
| 代码变更准确率 | 72% | 变更位置和内容正确 |
| 首轮通过率 | 55% | 无需Debugger介入 |
| 最大迭代次数 | 3 | Critic拒绝后最大重试 |

### 关键成功因素

1. **执行验证闭环：** 所有输出必须通过沙箱验证
2. **角色分离：** 编码与评审独立，避免自我确认偏差
3. **Docker隔离：** 确保测试环境一致性和安全性
4. **有限迭代：** 3轮上限防止无限循环
5. **结构化计划：** Planner确保执行路径清晰

---

## 执行验证型框架

### 概述

AgentForge的核心特征是执行验证型框架——所有Agent输出必须通过Docker沙箱验证后才能被接受。本节详细定义5角色映射、Docker沙箱验证流程和执行验证门禁。

### 5角色映射到xuansto-skill

| AgentForge角色 | xuansto-skill Agent | 职责映射 |
|---------------|---------------------|---------|
| Planner | system-architect / product-manager | 问题分析、执行计划制定、子任务分解 |
| Coder | fullstack-engineer / backend-developer / frontend-developer | 代码实现、单元测试编写、代码自检 |
| Tester | unit-tester / test-architect / qa-engineer | 测试执行与验证、回归测试、边界条件测试 |
| Debugger | bug-scanner / refactoring-specialist | 失败根因分析、问题定位、修复方案建议 |
| Critic | code-reviewer / security-auditor | 代码质量评审、方案可行性评估、最终接受/拒绝决策 |

### Docker沙箱验证流程

```
代码提交 → Docker容器创建 → 依赖安装 → 编译验证 → 测试执行 → 结果收集 → 容器销毁
    │            │               │           │           │           │            │
    └─ 隔离 ────┘── 可复现 ────┘── 编译通过 ─┘── 测试通过 ─┘── 可信 ────┘── 清理 ────┘
```

**验证步骤**：
1. **编译验证**: 代码在沙箱中编译通过，无语法错误和类型错误
2. **依赖安装验证**: 所有依赖在隔离环境中成功安装，无缺失依赖
3. **测试套件执行**: 完整测试套件在沙箱中执行，所有测试通过
4. **结果收集**: 收集测试报告、覆盖率报告、lint结果
5. **容器清理**: 验证完成后销毁容器，释放资源

### 执行验证门禁

```yaml
execution_verification_gate:
  gate_id: EXEC-VERIFY
  blocking: true
  checks:
    - compile_success: true
      description: "代码在Docker沙箱中编译通过"
    - deps_install_success: true
      description: "所有依赖在隔离环境中成功安装"
    - test_suite_pass: true
      description: "完整测试套件在沙箱中执行通过"
    - no_resource_leak: true
      description: "沙箱资源使用在限制范围内"
  docker_config:
    base_image: "python:3.12-slim"
    resource_limits:
      cpu: 2
      memory: "4g"
      timeout: 300
    network: none
    security:
      read_only_root: true
      no_new_privileges: true
```

---

## 与xuansto-skill的集成

| xuansto模块 | AgentForge对应 | 集成方式 |
|------------|---------------|---------|
| 57 Agents | 5 Roles | 角色映射与能力对齐 |
| Quality Gates | Docker Verification | 验证标准同步 |
| TDD Workflow | RED→GREEN→REFACTOR | TDD流程共享 |
| Code Review | Critic Role | 评审标准对齐 |

---

> 本文档由 Multi-Agent SDD/TDD Orchestrator 维护 | 最后更新: 2026-05-06
