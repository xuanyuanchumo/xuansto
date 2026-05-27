---
name: xuansto-skill
version: 1.0.0
description: |
  Xuansto Skill - 多Agent自主开发编排器
  基于SDD+TDD融合的智能开发协调系统，支持多Agent协作、质量门禁、自主迭代与持续演化
  触发词：xuansto、多Agent开发、SDD、TDD、测试驱动开发、规格驱动开发、自主开发、质量门禁、Agent协作、multi-agent、orchestration
author: skiller-team
tags:
  - xuansto
  - multi-agent
  - sdd
  - tdd
  - orchestration
  - autonomous-development
  - quality-gates
min_version: 1.0.0
license: MIT
---

# Xuansto Skill - Multi-Agent SDD+TDD Orchestrator

## 概述

Xuansto Skill 是一个功能完善的多Agent自主开发编排器，融合规格驱动开发(SDD)与测试驱动开发(TDD)，
通过智能编排实现高质量、自主化的软件开发过程。

---

## Karpathy Guidelines 行为准则

> 详细内容请参阅 [karpathy-guidelines.md](references/karpathy-guidelines.md)

### 核心原则概要

| 原则 | 核心思想 |
|------|----------|
| **Think Before Coding** | 编写代码前完成完整思考，记录决策过程 |
| **Simplicity First** | 选择最简单有效的解决方案，避免过度工程 |
| **Surgical Changes** | 每次变更精准、最小化、可追溯 |
| **Goal-Driven Execution** | 所有行动服务于明确的业务目标 |

---

## 核心原则：Spec > Test > Code

### 优先级层次

```
┌─────────────────────────────────────────┐
│           SPEC（规格说明）               │  ← 最高优先级
│    定义"做什么"和"为什么做"              │
├─────────────────────────────────────────┤
│           TEST（测试用例）               │  ← 中间优先级
│    定义"如何验证"和"验收标准"            │
├─────────────────────────────────────────┤
│           CODE（实现代码）               │  ← 最低优先级
│    定义"如何实现"和"技术细节"            │
└─────────────────────────────────────────┘
```

### 执行规则

| 规则ID | 规则描述 | 强制性 |
|--------|----------|--------|
| STC-001 | 无规格不开发 | 强制 |
| STC-002 | 无测试不合并 | 强制 |
| STC-003 | 规格变更需重新评审测试 | 强制 |
| STC-004 | 测试失败禁止代码提交 | 强制 |
| STC-005 | 代码覆盖率不低于80% | 推荐 |

---

## 七阶段SDD+TDD工作流

### Phase 0: 环境初始化

```
目标：建立开发环境和基础设施
任务：检测环境、初始化版本控制、配置依赖管理、设置CI/CD、初始化质量门禁
输出：环境就绪报告、配置文件
质量门禁：GATE-000
```

### Phase 1: 需求分析与规格定义

```
目标：将业务需求转化为可执行的规格说明
任务：收集需求、编写用户故事、创建SDD规格文档、评审规格、建立追溯矩阵
输出：SDD规格文档、用户故事、追溯矩阵
质量门禁：GATE-001, GATE-002
Agent角色：需求分析师、产品经理
```

### Phase 2: 架构设计与技术方案

```
目标：设计系统架构和技术实现方案
任务：分析非功能性需求、设计系统架构、选择技术栈、定义接口契约、创建ADR
输出：架构设计文档、ADR、接口定义
质量门禁：GATE-003, GATE-004
Agent角色：架构师、技术负责人
```

### Phase 3: 测试用例设计

```
目标：基于规格设计完整的测试用例
任务：编写单元测试规格、设计集成测试场景、创建E2E测试用例、定义性能基准
输出：测试用例库、测试数据、测试计划
质量门禁：GATE-005, GATE-006
Agent角色：测试工程师、QA负责人
```

### Phase 4: 测试先行实现

```
目标：按照TDD原则实现功能代码
任务：编写失败的测试用例、实现最小可行代码、重构优化、确保测试通过、代码审查
输出：功能代码、测试代码、审查报告
质量门禁：GATE-007, GATE-008, GATE-009
Agent角色：开发工程师、代码审查员
```

### Phase 5: 集成与验证

```
目标：集成各模块并进行全面验证
任务：模块集成测试、接口契约验证、E2E测试执行、性能基准测试、安全扫描
输出：集成报告、测试报告、安全报告
质量门禁：GATE-010, GATE-011, GATE-012
Agent角色：集成工程师、安全工程师
```

### Phase 6: 部署与发布

```
目标：安全部署到生产环境
任务：准备部署清单、执行部署脚本、生产环境验证、监控告警配置、发布文档更新
输出：部署报告、发布说明、监控配置
质量门禁：GATE-013, GATE-014
Agent角色：DevOps工程师、发布经理
```

### Phase 7: 演化与优化

```
目标：持续监控、学习和优化
任务：收集运行时数据、分析性能指标、识别优化机会、执行改进迭代、更新知识库
输出：演化报告、优化建议、知识更新
质量门禁：GATE-015
Agent角色：SRE工程师、优化专家
```

---

## 质量门禁体系

> 详细定义请参阅 [quality-gates.md](references/quality-gates.md)

### 门禁概览表

| 阶段 | 门禁ID | 名称 | 阻塞级别 |
|------|--------|------|----------|
| Phase 0 | GATE-000 | 环境就绪验证 | 阻塞 |
| Phase 1 | GATE-001 | 需求规格完整性验证 | 阻塞 |
| Phase 1 | GATE-002 | 规格文档一致性验证 | 阻塞 |
| Phase 2 | GATE-003 | 架构设计合理性验证 | 阻塞 |
| Phase 2 | GATE-004 | 接口契约完整性验证 | 阻塞 |
| Phase 3 | GATE-005 | 测试用例覆盖率验证 | 阻塞 |
| Phase 3 | GATE-006 | 测试数据准备验证 | 阻塞 |
| Phase 4 | GATE-007 | 代码静态质量验证 | 阻塞 |
| Phase 4 | GATE-008 | 单元测试执行验证 | 阻塞 |
| Phase 4 | GATE-009 | 代码审查完成验证 | 阻塞 |
| Phase 5 | GATE-010 | 集成测试执行验证 | 阻塞 |
| Phase 5 | GATE-011 | 端到端测试验证 | 阻塞 |
| Phase 5 | GATE-012 | 安全合规验证 | 阻塞 |
| Phase 6 | GATE-013 | 部署准备验证 | 阻塞 |
| Phase 6 | GATE-014 | 生产环境验证 | 阻塞 |
| Phase 7 | GATE-015 | 持续演化验证 | 非阻塞 |

---

## 协作模式与任务路由机制

### Agent角色定义

| Agent角色 | 职责范围 | 技能标签 | 优先级 |
|-----------|----------|----------|--------|
| Orchestrator | 全局编排协调 | orchestration, coordination | P0 |
| Architect | 架构设计决策 | architecture, design-patterns | P1 |
| Developer | 代码实现 | coding, refactoring | P1 |
| Tester | 测试设计与执行 | testing, qa | P1 |
| Reviewer | 代码审查 | code-review, quality | P2 |
| DevOps | 部署运维 | deployment, monitoring | P2 |
| Security | 安全审计 | security, compliance | P2 |

### 任务路由规则

```yaml
路由策略:
  默认策略: 能力匹配优先
  规则:
    - architecture → Architect
    - implementation → Developer
    - testing → Tester
    - review → Reviewer
    - deployment → DevOps
    - security → Security
  负载均衡:
    策略: 最少任务优先
    最大并发: 3
    超时重试: 3次
```

### 协作模式

| 模式 | 适用场景 | 流程 |
|------|----------|------|
| 串行协作 | 有严格依赖关系的任务 | Task A → Task B → Task C |
| 并行协作 | 无依赖的独立任务 | 多任务并行 → 合并结果 |
| 迭代协作 | 需要多次反馈优化 | Task ⇄ Review ⇄ Fix → Complete |
| 层级协作 | 复杂任务的分解执行 | Orchestrator 分发子任务 |

---

## Agent通信协议

> 详细协议定义请参阅：
> - [A2A协议](references/a2a-protocol.md)
> - [MCP协议](references/mcp-protocol.md)

### 协议概要

| 协议 | 用途 | 特点 |
|------|------|------|
| A2A | Agent间直接通信 | 支持请求-响应、发布-订阅、流式传输 |
| MCP | 与外部工具集成 | JSON-RPC 2.0 兼容，支持工具调用 |

### 消息类型

| 消息类型 | 用途 |
|----------|------|
| TASK_ASSIGN | 任务分配 |
| TASK_STATUS | 状态更新 |
| GATE_CHECK | 门禁检查请求 |
| GATE_RESULT | 门禁检查结果 |
| KNOWLEDGE_SHARE | 知识共享 |
| ERROR_REPORT | 错误报告 |
| HELP_REQUEST | 协助请求 |
| HANDOFF | 任务移交 |

---

## 使用示例

### 触发方式

```
关键词触发:
  - "多Agent开发"
  - "SDD+TDD流程"
  - "自主开发编排"
  - "质量门禁检查"
  - "Agent协作"

显式调用:
  @xuansto-skill
```

### 典型工作流

```
1. 用户: "使用多Agent开发模式实现用户认证功能"

2. 系统响应:
   - 启动Orchestrator
   - 创建任务分解计划
   - 分配Phase 0-7任务
   - 执行质量门禁检查
   - 协调Agent协作
   - 生成最终交付物

3. 输出:
   - 完整的实现代码
   - 测试用例和测试报告
   - 质量门禁通过报告
   - 部署文档
```

---

## 配置选项

```yaml
orchestrator:
  max_concurrent_agents: 5
  task_timeout_minutes: 60
  retry_policy:
    max_retries: 3
    backoff: exponential
    
quality_gates:
  enforcement: strict
  bypass_requires_approval: true
  
communication:
  protocol: A2A
  mcp_compatible: true
  encryption: tls1.3
  
logging:
  level: info
  format: json
  retention_days: 30
```

---

## 版本历史

| 版本 | 日期 | 变更说明 |
|------|------|----------|
| 1.0.0 | 2026-04-17 | 初始版本，包含完整SDD+TDD工作流 |

---

## 多语言开发规范索引

### 语言规范对照表

| 语言 | 规范文件 | 主要技术栈覆盖 |
|------|----------|----------------|
| **Python** | [python-standards.md](references/python-standards.md) | PEP 8、Type Hints、pytest、FastAPI、Django、Flask |
| **Go** | [go-standards.md](references/go-standards.md) | Effective Go、go mod、testify、Gin、Echo、Fiber |
| **Java** | [java-standards.md](references/java-standards.md) | Java命名约定、JUnit 5、Spring Boot、Quarkus、Maven/Gradle |
| **Rust** | [rust-standards.md](references/rust-standards.md) | Rust API指南、Cargo、proptest、thiserror、unsafe准则 |
| **TypeScript/JS** | [typescript-standards.md](references/typescript-standards.md) | ESLint、React、Vue、Angular、NestJS、Express、Fastify |

### 规范使用指南

```
Agent在处理项目时，应根据项目语言自动加载对应的开发规范：

1. 项目语言检测
   - 检查项目根目录的配置文件（pyproject.toml、go.mod、pom.xml、Cargo.toml、package.json）
   - 识别主要编程语言和技术栈

2. 规范加载策略
   - Code Reviewer: 根据被审查代码的语言加载对应规范
   - Backend Developer: 根据后端技术栈加载对应规范
   - Frontend Developer: 加载 TypeScript/JavaScript 规范
   - Test Architect: 根据项目语言加载测试规范章节

3. 规范应用优先级
   - 项目自定义规范 > 语言专用规范 > 通用编码规范（coding-standards.md）

4. 多语言项目处理
   - 微服务架构：每个服务独立应用对应语言规范
   - Monorepo：根据子项目目录分别应用规范
   - FFI/跨语言调用：遵循接口契约规范
```

---

## 参考资源

### 核心配置
- SDD Specification Parser: `skillscripts/core/sdd_parser.py`
- Quality Gate Config: `configs/quality_gate_config.yaml`
- Agent Registry: `skillscripts/core/agent_selector.py`
- Decision Log System: `subskills/decision_log_system.md`

### 详细文档
- [质量门禁详细定义](references/quality-gates.md)
- [Karpathy Guidelines](references/karpathy-guidelines.md)
- [A2A通信协议](references/a2a-protocol.md)
- [MCP协议兼容层](references/mcp-protocol.md)

### 语言规范
- [Python开发规范](references/python-standards.md)
- [Go开发规范](references/go-standards.md)
- [Java开发规范](references/java-standards.md)
- [Rust开发规范](references/rust-standards.md)
- [TypeScript/JavaScript开发规范](references/typescript-standards.md)
