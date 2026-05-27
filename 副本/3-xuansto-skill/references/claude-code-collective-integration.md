# Claude Code Collective 集成参考文档

> 版本: 3.2.0 | 更新日期: 2026-05-06 | 编码: UTF-8 without BOM | 行尾: LF

---

## 概述

Claude Code Collective 是一套基于Claude Code的AI辅助开发集成框架，核心特性包括TDD强制执行（RED→GREEN→REFACTOR）、Context7实时文档集成和智能任务路由。本文档描述其关键机制及与xuansto-skill的对接模式。

---

## TDD强制执行

### RED→GREEN→REFACTOR循环

Claude Code Collective严格遵循TDD三阶段循环，确保代码质量从设计阶段就得到保障。

**RED阶段（编写失败测试）：**

```yaml
tdd_red:
  rules:
    - 必须先编写测试，再编写实现
    - 测试必须失败（验证测试本身有效）
    - 测试应覆盖所有acceptance criteria
    - 禁止在RED阶段编写任何实现代码
  validation:
    - test_runs: true
    - all_tests_fail: true
    - coverage_target_set: true
```

**GREEN阶段（最小实现通过测试）：**

```yaml
tdd_green:
  rules:
    - 只编写使测试通过的最少代码
    - 禁止过度设计或添加未测试的功能
    - 禁止修改测试以适应实现
    - 优先选择最简单的实现路径
  validation:
    - all_tests_pass: true
    - no_test_modifications: true
    - minimum_implementation: true
```

**REFACTOR阶段（优化代码结构）：**

```yaml
tdd_refactor:
  rules:
    - 重构不改变外部行为
    - 所有测试必须持续通过
    - 每次重构后立即运行测试
    - 遵循小步重构原则
  validation:
    - all_tests_still_pass: true
    - no_behavior_change: true
    - code_quality_improved: true
```

### 强制执行机制

```python
class TDDStateMachine:
    STATES = ["RED", "GREEN", "REFACTOR"]

    def transition(self, current: str, test_results: dict) -> str:
        if current == "RED":
            if test_results["all_fail"]:
                return "GREEN"
            raise TDDViolation("RED阶段测试未全部失败")

        if current == "GREEN":
            if test_results["all_pass"]:
                return "REFACTOR"
            raise TDDViolation("GREEN阶段测试未全部通过")

        if current == "REFACTOR":
            if test_results["all_pass"]:
                return "RED"
            raise TDDViolation("REFACTOR阶段测试失败，回退到GREEN")

        raise InvalidState(current)
```

---

## TDD强制执行模式

### 概述

Claude Code Collective的TDD强制执行模式通过状态机严格约束开发流程，确保RED→GREEN→REFACTOR三阶段循环不可跳过、不可逆序。本节定义强制执行的详细规则和验证机制。

### RED阶段强制执行

**强制规则**：
1. 必须先编写测试代码，禁止编写任何实现代码
2. 测试必须失败（验证测试本身有效），若测试意外通过则拒绝进入GREEN
3. 测试必须覆盖当前任务的所有acceptance criteria
4. 禁止在RED阶段编写`pass`桩实现使测试"通过"

**验证检查**：
```yaml
red_verification:
  - test_file_exists: true
  - test_runs_without_error: true
  - all_tests_fail: true
  - no_implementation_code: true
  - coverage_target_set: true
```

### GREEN阶段强制执行

**强制规则**：
1. 只编写使测试通过的最少代码，禁止过度设计
2. 禁止修改测试代码以适应实现
3. 禁止添加未测试的功能
4. 实现代码必须是最简方案

**验证检查**：
```yaml
green_verification:
  - all_tests_pass: true
  - no_test_modifications: true
  - minimum_implementation: true
  - no_extra_features: true
```

### REFACTOR阶段强制执行

**强制规则**：
1. 重构不改变外部行为（行为等价性）
2. 所有测试必须持续通过
3. 每次重构后立即运行测试
4. 遵循小步重构原则，每次只做一个重构操作

**验证检查**：
```yaml
refactor_verification:
  - all_tests_still_pass: true
  - no_behavior_change: true
  - code_quality_improved: true
  - single_refactor_per_step: true
```

### 强制执行状态机

```python
class TDDStateMachine:
    STATES = ["RED", "GREEN", "REFACTOR"]

    def transition(self, current: str, test_results: dict) -> str:
        if current == "RED":
            if not test_results.get("test_file_exists"):
                raise TDDViolation("RED阶段：测试文件不存在")
            if not test_results.get("all_tests_fail"):
                raise TDDViolation("RED阶段：测试未全部失败，请确认测试有效性")
            return "GREEN"

        if current == "GREEN":
            if not test_results.get("all_tests_pass"):
                raise TDDViolation("GREEN阶段：测试未全部通过，继续实现最小代码")
            if test_results.get("test_modified"):
                raise TDDViolation("GREEN阶段：禁止修改测试以适应实现")
            return "REFACTOR"

        if current == "REFACTOR":
            if not test_results.get("all_tests_still_pass"):
                raise TDDViolation("REFACTOR阶段：测试失败，回退到GREEN阶段")
            return "RED"

        raise InvalidState(current)
```

---

## Context7实时文档集成

### 概述

Context7机制在Agent编码时实时检索最新技术文档，确保代码基于准确的API规范而非过时记忆。

### 工作流程

```
Agent编码 → 遇到API调用 → Context7查询 → 获取最新文档 → 验证API签名 → 继续编码
```

### 配置

```yaml
context7:
  enabled: true
  sources:
    - type: npm_registry
      packages: ["react", "next", "typescript"]
    - type: github_docs
      repos: ["facebook/react", "vercel/next.js"]
    - type: mdn
      categories: ["web-api", "css", "javascript"]
  cache:
    ttl: 3600
    max_entries: 500
  fallback:
    - local_knowledge_base
    - cached_documentation
```

### 查询策略

| 场景 | 查询时机 | 查询内容 |
|------|---------|---------|
| API调用 | 编写前 | 函数签名、参数类型、返回值 |
| 依赖引入 | import时 | 版本兼容性、导出成员 |
| 配置项 | 使用时 | 配置键名、值类型、默认值 |
| 错误处理 | catch时 | 错误码、异常类型、恢复策略 |

---

## 智能任务路由

### 路由策略

根据任务特征自动分配给最合适的Agent，优化执行效率和资源利用。

```yaml
task_routing:
  strategy: multi_factor_decision
  factors:
    - weight: 0.4
      name: task_complexity
      calculation: cyclomatic_complexity + dependency_count
    - weight: 0.3
      name: agent_capability_match
      calculation: cosine_similarity(task_embedding, agent_profile)
    - weight: 0.2
      name: agent_availability
      calculation: 1 / (current_load + 1)
    - weight: 0.1
      name: historical_performance
      calculation: success_rate * speed_factor
```

### 路由决策矩阵

| 任务类型 | 优先Agent | 备选Agent | 路由条件 |
|---------|----------|----------|---------|
| Bug修复 | Bug-Fixer | TDD Writer | 有明确复现步骤 |
| 新功能 | Feature Developer | TDD Writer | 有完整规格 |
| 重构 | Refactoring Specialist | Code Reviewer | 测试覆盖率≥80% |
| 安全审计 | Security Auditor | AI Penetration Tester | 涉及敏感数据 |
| 性能优化 | Performance Tester | Refactoring Specialist | 有性能基准 |

### 负载均衡

```yaml
load_balancing:
  strategy: weighted_round_robin
  max_concurrent_per_agent: 3
  queue_timeout: 300
  retry_on_failure: true
  max_retries: 2
```

---

## 与xuansto-skill的集成

| xuansto模块 | Claude Code Collective | 集成方式 |
|------------|----------------------|---------|
| TDD Workflow | TDD Enforcement | 共享RED→GREEN→REFACTOR状态机 |
| Agent Registry | Task Router | Agent能力注册与路由决策 |
| Knowledge Base | Context7 | 文档检索与缓存共享 |
| Quality Gates | TDD Validation | 门禁条件对齐 |

### Context7实时文档集成详细机制

Context7在Agent编码时实时检索最新技术文档，确保代码基于准确的API规范而非过时记忆。与xuansto-skill知识库的集成方式：

1. **知识库优先查询**: Context7查询首先命中xuansto本地知识库（`.knowledge/`），若未找到则回退到远程文档源
2. **缓存共享**: Context7缓存与知识库向量引擎共享，避免重复嵌入计算
3. **文档版本追踪**: Context7检索的文档版本信息写入知识库，支持版本过期检测
4. **Agent检索配置**: 不同Agent角色使用不同的Context7检索策略（参考AGENT_RETRIEVAL_PROFILES）

---

> 本文档由 Multi-Agent SDD/TDD Orchestrator 维护 | 最后更新: 2026-05-06
