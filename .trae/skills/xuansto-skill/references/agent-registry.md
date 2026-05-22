# Agent注册表（57 Agents）

> 版本: 4.0.0 | 更新日期: 2026-05-06 | 编码: UTF-8 | 行尾: LF

本注册表包含Xuansto Skill全部57个Agent的完整注册信息，供Orchestrator进行任务路由和Agent调度时参考。

## 目录

1. [编排层（Orchestrator）- 3个](#编排层orchestrator---3个)
2. [产品层（Product）- 4个](#产品层product---4个)
3. [设计层（Design）- 4个](#设计层design---4个)
4. [工程层（Engineering）- 6个](#工程层engineering---6个)
5. [跨平台层（Cross-Platform）- 5个](#跨平台层cross-platform---5个)
6. [数据层（Database）- 3个](#数据层database---3个)
7. [测试层（Testing）- 10个](#测试层testing---10个)
8. [安全层（Security）- 3个](#安全层security---3个)
9. [运维层（DevOps）- 4个](#运维层devops---4个)
10. [质量层（Quality）- 7个](#质量层quality---7个)
11. [文档层（Documentation）- 2个](#文档层documentation---2个)
12. [知识层（Knowledge）- 3个](#知识层knowledge---3个)
13. [监控层（Monitoring）- 3个](#监控层monitoring---3个)

---

## 编排层（Orchestrator）- 3个

| 名称 | 职责 | 技能标签 | 优先级 | 定义文件 |
|------|------|----------|--------|----------|
| Orchestrator | 全局编排协调、任务分解、Agent调度、冲突仲裁、平台检测、增量实施死循环检测 | orchestration, coordination, platform-detection, conflict-resolution | P0 | agents/orchestrator/orchestrator.md |
| Subagent Dispatcher | 子代理调度分发、两阶段审查协调(计划合规+代码质量)、子代理结果聚合、返工流程管理 | subagent-creation, task-dispatching, parallel-serial-identification, two-stage-review, rework-management | P1 | agents/orchestrator/subagent-dispatcher.md |
| Task Coordinator | 任务协调与依赖管理、跨Agent任务编排、并行任务调度、任务状态跟踪、冲突检测与解决 | task-coordination, dependency-management, progress-tracking, task-dispatching | P1 | agents/orchestrator/task-coordinator.md |

## 产品层（Product）- 4个

| 名称 | 职责 | 技能标签 | 优先级 | 定义文件 |
|------|------|----------|--------|----------|
| Product Manager | 需求澄清、功能分解、用户故事编写、验收标准定义、产品方向决策 | requirements, user-stories, acceptance-criteria | P1 | agents/product/product-manager.md |
| System Architect | 系统架构设计、技术选型、模块划分、接口契约定义、ADR编写、策略性分歧裁决 | architecture, adr, tech-selection | P1 | agents/product/system-architect.md |
| Technical Writer | 技术文档编写、API文档生成、README维护、变更日志编写 | documentation, api-docs, readme | P1 | agents/product/technical-writer.md |
| Brainstorming Facilitator | 苏格拉底式需求探索、6阶段引导(Discovery→Option→Design→Reflect→Commit→Transition)、结构化设计文档生成、信息缺口识别 | brainstorming, socratic-dialogue, design-document, trade-off-analysis, requirement-discovery | P1 | agents/product/brainstorming-facilitator.md |

## 设计层（Design）- 4个

| 名称 | 职责 | 技能标签 | 优先级 | 定义文件 |
|------|------|----------|--------|----------|
| UI Designer | 界面设计与原型、设计系统建立、Design Token定义、组件库规划 | visual-design, design-system, design-tokens | P1 | agents/design/ui-designer.md |
| UX Designer | 用户体验设计、用户旅程地图、可用性测试、交互设计、可访问性规划 | user-research, interaction-design, accessibility | P1 | agents/design/ux-designer.md |
| Frontend Stylist | 前端样式实现、CSS架构、响应式设计、主题系统、动画效果 | css, responsive, animation | P2 | agents/design/frontend-stylist.md |
| Design System Generator | 设计系统自动生成、风格/配色/字体推理选择、反模式检查、WCAG AA对比度验证、设计令牌输出 | design-system-generation, style-reasoning, anti-pattern-filtering, design-tokens-output | P1 | agents/design/design-system-generator.md |

## 工程层（Engineering）- 6个

| 名称 | 职责 | 技能标签 | 优先级 | 定义文件 |
|------|------|----------|--------|----------|
| Frontend Developer | 前端代码实现、组件开发、状态管理、API集成 | react, vue, angular, components | P1 | agents/engineering/frontend-developer.md |
| Backend Developer | 后端代码实现、API开发、业务逻辑、中间件配置 | api, middleware, business-logic | P1 | agents/engineering/backend-developer.md |
| Fullstack Engineer | 全栈开发、前后端集成、端到端功能实现 | integration, contract-testing, e2e | P1 | agents/engineering/fullstack-engineer.md |
| Database Engineer | 数据库设计优化、查询性能调优、数据迁移、索引策略 | schema, indexing, sql-review | P1 | agents/engineering/database-engineer.md |
| Mobile Developer | 移动端开发、跨平台移动适配、原生桥接 | react-native, flutter, responsive | P2 | agents/engineering/mobile-developer.md |
| DevOps Engineer | 基础设施配置、CI/CD流水线、容器化部署、环境管理 | docker, k8s, github-actions | P1 | agents/engineering/devops-engineer.md |

## 跨平台层（Cross-Platform）- 5个

| 名称 | 职责 | 技能标签 | 优先级 | 定义文件 |
|------|------|----------|--------|----------|
| Desktop Developer | 桌面端开发、Electron/Tauri应用开发、IPC通信实现 | electron, tauri, ipc | P1 | agents/cross-platform/desktop-developer.md |
| Desktop UI Adapter | 桌面端UI适配、原生控件集成、窗口管理、平台特定样式 | window-management, native-menu, system-theme | P2 | agents/cross-platform/desktop-ui-adapter.md |
| Native Module Developer | 原生模块开发、C++/Rust FFI绑定、性能关键路径实现 | n-api, rust-ffi, native-dialogs | P2 | agents/cross-platform/native-module-developer.md |
| IPC Specialist | IPC通信架构设计、进程间消息协议定义、序列化优化、IPC安全审计、跨进程数据一致性保障 | ipc-contract-design, main-renderer-communication, secure-channel-management, cross-platform-ipc | P1 | agents/cross-platform/ipc-specialist.md |
| Auto-Update Engineer | 自动更新机制设计、增量更新策略、版本回滚、更新签名验证、多平台分发 | auto-update-design, incremental-update, rollback-mechanism, update-verification | P1 | agents/cross-platform/auto-update-engineer.md |

## 数据层（Database）- 3个

| 名称 | 职责 | 技能标签 | 优先级 | 定义文件 |
|------|------|----------|--------|----------|
| Data Modeler | 数据模型设计、ER图绘制、范式优化、数据字典维护 | er-diagram, normalization, relations | P1 | agents/database/data-modeler.md |
| DBA | 数据库管理、性能监控、备份恢复、安全审计 | slow-query, execution-plan, backup | P1 | agents/database/dba.md |
| Data Seeder | 测试数据生成、数据脱敏、数据迁移脚本、种子数据管理 | seed-scripts, data-factory, anonymization | P2 | agents/database/data-seeder.md |

## 测试层（Testing）- 10个

| 名称 | 职责 | 技能标签 | 优先级 | 定义文件 |
|------|------|----------|--------|----------|
| Test Architect | 测试架构设计、测试策略制定、测试工具选型、回归测试自动生成 | test-strategy, coverage, framework-selection | P1 | agents/testing/test-architect.md |
| Unit Tester | 单元测试编写、边界条件覆盖、Mock/Stub配置 | unit-tests, mocking, boundary-testing | P1 | agents/testing/unit-tester.md |
| Integration Tester | 集成测试设计、接口契约验证、模块间交互测试 | api-tests, database-tests, contract-tests | P1 | agents/testing/integration-tester.md |
| E2E Tester | 端到端测试执行、用户旅程验证、跨浏览器测试 | playwright, cypress, visual-regression | P1 | agents/testing/e2e-tester.md |
| Desktop Tester | 桌面端专项测试、窗口生命周期、安装包测试、IPC通信测试 | window-testing, ipc-testing, offline-testing | P2 | agents/testing/desktop-tester.md |
| Performance Tester | 性能基准测试、负载测试、压力测试、性能回归检测 | k6, jmeter, load-testing | P1 | agents/testing/performance-tester.md |
| Security Tester | 安全扫描、漏洞检测、依赖审计、安全合规验证 | owasp, sqli, xss, csrf | P1 | agents/testing/security-tester.md |
| AI Penetration Tester | AI驱动的渗透测试、Agentic安全测试、OWASP ASI验证、安全修复闭环 | ai-pentest, multi-agent-recon, exploit-chain | P1 | agents/testing/ai-penetration-tester.md |
| Test Maintainer | 测试代码维护、测试数据更新、测试环境管理、测试报告生成 | test-dedup, flaky-detection, optimization | P2 | agents/testing/test-maintainer.md |
| QA Engineer | 质量保证、合规审计、验收测试聚合、质量指标跟踪 | quality-gates, compliance, uat | P2 | agents/testing/qa-engineer.md |

## 安全层（Security）- 3个

| 名称 | 职责 | 技能标签 | 优先级 | 定义文件 |
|------|------|----------|--------|----------|
| Security Auditor | 安全审计、合规检查、安全策略制定、OWASP Top 10验证 | sast, cve, secure-coding | P1 | agents/security/security-auditor.md |
| Penetration Tester | 渗透测试、漏洞利用验证、安全评估报告 | auth-bypass, privilege-escalation, injection | P1 | agents/security/penetration-tester.md |
| Compliance Officer | 合规管理、法规遵循、数据保护、审计跟踪 | gdpr, pci-dss, audit-trail | P2 | agents/security/compliance-officer.md |

## 运维层（DevOps）- 4个

| 名称 | 职责 | 技能标签 | 优先级 | 定义文件 |
|------|------|----------|--------|----------|
| CI/CD Specialist | CI/CD流水线设计、自动化构建、部署策略、环境管理 | github-actions, gitlab-ci, multi-env | P1 | agents/devops/cicd-specialist.md |
| Build-Release Engineer | 多平台构建、代码签名、安装包生成、发布管理 | electron-builder, tauri-bundler, code-signing | P1 | agents/devops/build-release-engineer.md |
| Monitor Specialist | 监控系统配置、告警规则、可观测性基线、日志管理 | prometheus, sentry, elk | P1 | agents/devops/monitor-specialist.md |
| Runtime Supervisor | 运行时监控、熔断机制、工作流检查点恢复、级联故障防护 | health-check, checkpoint-recovery, scaling | P1 | agents/devops/runtime-supervisor.md |

## 质量层（Quality）- 7个

| 名称 | 职责 | 技能标签 | 优先级 | 定义文件 |
|------|------|----------|--------|----------|
| Code Reviewer | 代码审查、编码规范检查、最佳实践验证、安全代码审查 | code-standards, design-patterns, complexity | P1 | agents/quality/code-reviewer.md |
| Refactoring Specialist | 代码重构、技术债务管理、设计模式应用、性能优化 | code-smells, refactoring-patterns, simplification | P2 | agents/quality/refactoring-specialist.md |
| Doc Reviewer | 文档质量审查、一致性检查、完整性验证 | doc-coverage, openapi-consistency, style-check | P2 | agents/quality/doc-reviewer.md |
| Compliance Reviewer | 合规性审查、编码规范验证、最佳实践合规检查、安全编码标准审查 | coding-standards, project-conventions, claude-md-compliance | P2 | agents/quality/compliance-reviewer.md |
| Bug Scanner | Bug模式扫描、常见缺陷检测、边界条件分析、异常路径识别 | bug-detection, logic-analysis, edge-case-check | P2 | agents/quality/bug-scanner.md |
| History Analyzer | 变更历史分析、回归风险评估、修改影响范围识别、历史Bug模式关联 | git-blame, change-history, context-correlation | P2 | agents/quality/history-analyzer.md |
| Comment Verifier | 注释准确性验证、注释与代码同步检查、公共API文档注释完整性验证、过时注释检测 | comment-accuracy, pr-review-check, doc-code-sync | P2 | agents/quality/comment-verifier.md |

## 文档层（Documentation）- 2个

| 名称 | 职责 | 技能标签 | 优先级 | 定义文件 |
|------|------|----------|--------|----------|
| Documentation Engineer | 文档工程、API文档自动生成、文档站点构建、知识库维护 | user-manual, dev-guide, troubleshooting | P1 | agents/documentation/documentation-engineer.md |
| Specification Keeper | 规格文档维护、规格漂移审核、知识沉淀、跨分支经验同步、ADR归档 | cross-reference, version-tracking, backup-scheduling | P1 | agents/documentation/specification-keeper.md |

## 知识层（Knowledge）- 3个

| 名称 | 职责 | 技能标签 | 优先级 | 定义文件 |
|------|------|----------|--------|----------|
| Knowledge Manager | 知识库架构管理、知识条目CRUD、知识检索与推荐、跨会话知识持久化、SQLite+Chroma双引擎管理 | knowledge-base-management, knowledge-indexing, knowledge-lifecycle, knowledge-retrieval | P1 | agents/knowledge/knowledge-manager.md |
| Learning Specialist | 知识学习与提取、经验模式识别、反模式沉淀、跨项目知识迁移、/learn命令处理 | experience-extraction, pattern-learning, knowledge-dedup, auto-induction | P2 | agents/knowledge/learning-specialist.md |
| Token Optimizer | Token预算管理、上下文压缩、信息密度优化、冗余检测与消除、token-budget-guard集成 | token-budget-management, context-compression, tes-scoring, on-demand-loading | P1 | agents/knowledge/token-optimizer.md |

## 监控层（Monitoring）- 3个

| 名称 | 职责 | 技能标签 | 优先级 | 定义文件 |
|------|------|----------|--------|----------|
| Quality Monitor | 六维质量监控、质量指标聚合、质量趋势分析、质量门禁状态追踪、异常预警 | quality-gate-monitoring, degradation-detection, quality-trend-analysis, gate-compliance-tracking | P1 | agents/monitoring/quality-monitor.md |
| Progress Tracker | 项目进度跟踪、里程碑管理、迭代预算监控、交付物状态追踪、LOOP-COMPLETION验证 | phase-progress-tracking, milestone-management, blocker-detection, escalation-management | P1 | agents/monitoring/progress-tracker.md |
| Decision Logger | 透明决策记录、Decision Log维护、决策追溯、ADR关联、决策影响评估 | decision-logging, adr-index-maintenance, audit-trail, decision-retrieval | P2 | agents/monitoring/decision-logger.md |

---

## Agent 间核心依赖关系

### 严格依赖（必须等待上游产出）

| 下游Agent | 依赖上游Agent | 依赖产出 |
|-----------|-------------|---------|
| System Architect | Product Manager | PRD、用户故事 |
| UI Designer | Product Manager | PRD、用户故事 |
| UX Designer | UI Designer | 设计系统、设计令牌 |
| Frontend Developer | UI Designer + System Architect | 设计稿 + 架构设计 |
| Backend Developer | System Architect | 架构设计、API契约 |
| Database Engineer | System Architect | 数据架构设计 |
| Desktop Developer | System Architect + Frontend Developer | 架构设计 + 前端组件 |
| Native Module Developer | Desktop Developer | 桌面应用框架 |
| IPC Specialist | Desktop Developer + System Architect | 桌面应用框架 + 架构设计 |
| Auto-Update Engineer | Desktop Developer + DevOps Engineer | 桌面应用框架 + CI/CD流水线 |
| Unit Tester | Frontend/Backend Developer | 代码实现 |
| Integration Tester | Unit Tester | 单元测试通过 |
| E2E Tester | Integration Tester | 集成测试通过 |
| Security Tester | Integration Tester | 集成构建 |
| Performance Tester | Integration Tester | 集成构建 |
| Code Reviewer | Frontend/Backend Developer | 代码实现 |
| Documentation Engineer | All Development Agents | 完整实现 |
| Subagent Dispatcher | Code Reviewer | 审查触发信号 |
| Task Coordinator | Orchestrator | 编排指令 |
| Compliance Reviewer | Subagent Dispatcher | 审查任务分配 |
| Bug Scanner | Subagent Dispatcher | 审查任务分配 |
| History Analyzer | Subagent Dispatcher | 审查任务分配 |
| Comment Verifier | Subagent Dispatcher | 审查任务分配 |
| Design System Generator | UI Designer + Product Manager | 设计需求 + 产品类型 |
| Knowledge Manager | All Agents | 知识条目输入 |
| Learning Specialist | Knowledge Manager | 知识库就绪 |
| Token Optimizer | Orchestrator | Token预算约束 |
| Quality Monitor | Quality Layer Agents | 质量指标数据 |
| Progress Tracker | Task Coordinator | 任务状态数据 |
| Decision Logger | Orchestrator + System Architect | 决策事件 |

### 可并行（无严格依赖）

| Agent组 | 说明 |
|---------|------|
| Product Manager + Technical Writer | 需求分析可与文档模板准备并行 |
| UI Designer + UX Designer | 设计可并行迭代，通过设计令牌同步 |
| Frontend Developer + Backend Developer | 基于契约开发，可并行 |
| Unit Tester (前端) + Unit Tester (后端) | 不同模块的单元测试可并行 |
| Security Auditor + Compliance Officer | 安全审计与合规检查可并行 |
| Compliance Reviewer + Bug Scanner + History Analyzer + Comment Verifier | 子代理审查可并行执行 |
| IPC Specialist + Auto-Update Engineer | 跨平台专项可并行开发 |
| Knowledge Manager + Learning Specialist + Token Optimizer | 知识层Agent可并行运作 |
| Quality Monitor + Progress Tracker + Decision Logger | 监控层Agent可并行运作 |

---

## 新增Agent注册详情（v3.2.0）

### AGENT-042: Brainstorming Facilitator

```yaml
id: AGENT-042
name: Brainstorming Facilitator
layer: 产品层（Product）
priority: P1
triggers:
  - /brainstorm
  - /clarify
  - 需求探索
  - 苏格拉底式引导
  - brainstorming
description: |
  苏格拉底式需求探索引导Agent，执行6阶段需求探索流程：
  Discovery→Option Analysis→Design→Reflect→Commit→Transition。
  负责识别信息缺口、生成结构化设计文档、引导用户完成需求确认。
dependencies:
  - Product Manager（需求输入）
  - System Architect（技术可行性反馈）
output:
  - 结构化设计文档（8章节）
  - 信息缺口清单
  - 方案Trade-off分析
  - 用户确认记录
services:
  - brainstorming
  - socratic-dialogue
  - design-document
  - trade-off-analysis
  - requirement-discovery
```

### AGENT-043: Subagent Dispatcher

```yaml
id: AGENT-043
name: Subagent Dispatcher
layer: 编排层（Orchestrator）
priority: P1
triggers:
  - /review
  - 子代理调度
  - 多视角审查
  - subagent-dispatch
description: |
  子代理调度分发Agent，负责协调Multi-Perspective Review流程。
  执行两阶段审查：Stage 1计划合规性审查 + Stage 2代码质量审查。
  管理子代理结果聚合、返工流程和审查置信度评分。
dependencies:
  - Code Reviewer（审查触发）
  - Compliance Reviewer（合规视角）
  - Bug Scanner（缺陷视角）
  - History Analyzer（历史视角）
  - Comment Verifier（注释视角）
output:
  - 审查结果聚合报告
  - 置信度评分
  - 返工指令（如需）
  - 视角覆盖状态
services:
  - subagent-creation
  - task-dispatching
  - parallel-serial-identification
  - two-stage-review
  - rework-management
```

### AGENT-044: Design System Generator

```yaml
id: AGENT-044
name: Design System Generator
layer: 设计层（Design）
priority: P1
triggers:
  - /design
  - 设计系统生成
  - design-system
  - 配色方案
  - 字体配对
description: |
  设计系统自动生成Agent，基于产品类型和行业特征推理选择：
  风格、配色方案、字体配对。执行行业反模式检查和WCAG AA对比度验证，
  输出完整设计系统文档和设计令牌。
dependencies:
  - UI Designer（设计需求输入）
  - Product Manager（产品类型和行业信息）
output:
  - 设计系统文档（design-system.md）
  - 设计令牌（design-tokens.json）
  - 反模式检查报告
  - WCAG AA对比度验证结果
services:
  - design-system-generation
  - style-reasoning
  - anti-pattern-filtering
  - design-tokens-output
```

### AGENT-045: Compliance Reviewer

```yaml
id: AGENT-045
name: Compliance Reviewer
layer: 质量层（Quality）
priority: P2
triggers:
  - 合规审查
  - compliance-review
  - 编码规范验证
description: |
  合规性审查子代理，在Multi-Perspective Review模式下提供合规视角。
  检查编码规范合规性、最佳实践遵循情况、安全编码标准合规性。
  由Subagent Dispatcher调度执行。
dependencies:
  - Subagent Dispatcher（调度触发）
output:
  - 合规性审查发现列表
  - 置信度评分
  - 合规违规项（含位置和修复建议）
services:
  - coding-standards
  - project-conventions
  - claude-md-compliance
```

### AGENT-046: Bug Scanner

```yaml
id: AGENT-046
name: Bug Scanner
layer: 质量层（Quality）
priority: P2
triggers:
  - Bug扫描
  - bug-scan
  - 缺陷检测
description: |
  Bug模式扫描子代理，在Multi-Perspective Review模式下提供缺陷检测视角。
  扫描常见Bug模式、边界条件缺陷、异常路径遗漏、空指针/类型错误等。
  由Subagent Dispatcher调度执行。
dependencies:
  - Subagent Dispatcher（调度触发）
output:
  - Bug扫描发现列表
  - 置信度评分
  - 缺陷分类（Critical/High/Medium/Low）
services:
  - bug-detection
  - logic-analysis
  - edge-case-check
```

### AGENT-047: History Analyzer

```yaml
id: AGENT-047
name: History Analyzer
layer: 质量层（Quality）
priority: P2
triggers:
  - 变更历史分析
  - history-analysis
  - 回归风险评估
description: |
  变更历史分析子代理，在Multi-Perspective Review模式下提供历史视角。
  分析变更历史中的回归风险、修改影响范围、历史Bug模式关联。
  由Subagent Dispatcher调度执行。
dependencies:
  - Subagent Dispatcher（调度触发）
output:
  - 变更影响分析报告
  - 回归风险评估
  - 历史Bug模式关联
  - 置信度评分
services:
  - git-blame
  - change-history
  - context-correlation
```

### AGENT-048: Comment Verifier

```yaml
id: AGENT-048
name: Comment Verifier
layer: 质量层（Quality）
priority: P2
triggers:
  - 注释验证
  - comment-verify
  - 文档注释检查
description: |
  注释准确性验证子代理，在Multi-Perspective Review模式下提供注释视角。
  验证注释与代码同步性、公共API文档注释完整性、检测过时注释。
  由Subagent Dispatcher调度执行。
dependencies:
  - Subagent Dispatcher（调度触发）
output:
  - 注释验证发现列表
  - 过时注释标记
  - API文档注释覆盖率
  - 置信度评分
services:
  - comment-accuracy
  - pr-review-check
  - doc-code-sync
```

### AGENT-049: Task Coordinator

```yaml
id: AGENT-049
name: Task Coordinator
layer: 编排层（Orchestrator）
priority: P1
triggers:
  - 任务协调
  - 依赖管理
  - 并行调度
  - task-coordination
description: |
  任务协调Agent，负责跨Agent任务编排与依赖管理。
  管理并行任务调度、任务状态跟踪、冲突检测与解决。
  与Orchestrator协同工作，处理细粒度任务依赖关系和执行顺序。
dependencies:
  - Orchestrator（编排指令输入）
  - Subagent Dispatcher（子任务协调）
output:
  - 任务依赖图
  - 并行执行计划
  - 任务状态追踪报告
  - 冲突检测结果
services:
  - task-coordination
  - dependency-management
  - progress-tracking
  - task-dispatching
```

### AGENT-050: IPC Specialist

```yaml
id: AGENT-050
name: IPC Specialist
layer: 跨平台层（Cross-Platform）
priority: P1
triggers:
  - IPC通信
  - 进程间通信
  - ipc-design
  - ipc-security
description: |
  IPC通信架构设计Agent，负责桌面应用进程间通信的完整生命周期管理。
  定义消息协议、优化序列化策略、执行IPC安全审计、保障跨进程数据一致性。
  支持Electron IPC、Tauri Command、Flutter MethodChannel等多种IPC机制。
dependencies:
  - Desktop Developer（桌面应用框架）
  - System Architect（架构设计）
output:
  - IPC通信架构文档
  - 消息协议定义
  - IPC安全审计报告
  - 序列化优化方案
services:
  - ipc-contract-design
  - main-renderer-communication
  - secure-channel-management
  - cross-platform-ipc
```

### AGENT-051: Auto-Update Engineer

```yaml
id: AGENT-051
name: Auto-Update Engineer
layer: 跨平台层（Cross-Platform）
priority: P1
triggers:
  - 自动更新
  - 增量更新
  - 版本回滚
  - auto-update
description: |
  自动更新机制设计Agent，负责桌面应用自动更新的完整方案设计。
  包括增量更新策略、版本回滚机制、更新签名验证、多平台分发。
  与CI/CD流水线集成，确保更新包的安全分发和可靠安装。
dependencies:
  - Desktop Developer（桌面应用框架）
  - DevOps Engineer（CI/CD流水线）
output:
  - 自动更新架构文档
  - 增量更新策略
  - 版本回滚方案
  - 更新签名验证配置
services:
  - auto-update-design
  - incremental-update
  - rollback-mechanism
  - update-verification
```

### AGENT-052: Knowledge Manager

```yaml
id: AGENT-052
name: Knowledge Manager
layer: 知识层（Knowledge）
priority: P1
triggers:
  - 知识管理
  - 知识库
  - knowledge-base
  - /learn
description: |
  知识库架构管理Agent，负责SQLite+Chroma双引擎知识库的完整生命周期管理。
  管理知识条目CRUD、知识检索与推荐、跨会话知识持久化。
  通过knowledge-server.py提供REST API和MCP Tool接口。
dependencies:
  - All Agents（知识条目输入）
output:
  - 知识库架构文档
  - 知识条目索引
  - 知识检索结果
  - 跨会话持久化状态
services:
  - knowledge-base-management
  - knowledge-indexing
  - knowledge-lifecycle
  - knowledge-retrieval
```

### AGENT-053: Learning Specialist

```yaml
id: AGENT-053
name: Learning Specialist
layer: 知识层（Knowledge）
priority: P2
triggers:
  - 知识学习
  - 经验提取
  - 模式识别
  - /learn
description: |
  知识学习与提取Agent，负责从开发过程中提取可复用经验和模式。
  识别经验模式、沉淀反模式、跨项目知识迁移。
  处理/learn命令，将隐性知识转化为显性知识条目。
dependencies:
  - Knowledge Manager（知识库就绪）
output:
  - 经验模式文档
  - 反模式记录
  - 知识迁移方案
  - 学习报告
services:
  - experience-extraction
  - pattern-learning
  - knowledge-dedup
  - auto-induction
```

### AGENT-054: Token Optimizer

```yaml
id: AGENT-054
name: Token Optimizer
layer: 知识层（Knowledge）
priority: P1
triggers:
  - Token优化
  - 上下文压缩
  - token-budget
  - 上下文管理
description: |
  Token预算管理Agent，负责优化Token使用效率和上下文信息密度。
  管理Token预算分配、上下文压缩、冗余检测与消除。
  集成token-budget-guard.py，确保会话在Token预算约束内高效运行。
dependencies:
  - Orchestrator（Token预算约束）
output:
  - Token预算分配方案
  - 上下文压缩结果
  - 冗余检测报告
  - Token使用效率报告
services:
  - token-budget-management
  - context-compression
  - tes-scoring
  - on-demand-loading
```

### AGENT-055: Quality Monitor

```yaml
id: AGENT-055
name: Quality Monitor
layer: 监控层（Monitoring）
priority: P1
triggers:
  - 质量监控
  - 质量指标
  - quality-monitoring
  - 质量门禁
description: |
  六维质量监控Agent，负责质量指标的聚合、趋势分析和异常预警。
  追踪质量门禁状态、监控质量趋势、触发质量异常预警。
  覆盖代码质量、测试质量、安全质量、文档质量、性能质量、合规质量六个维度。
dependencies:
  - Quality Layer Agents（质量指标数据）
  - Testing Layer Agents（测试指标数据）
output:
  - 六维质量报告
  - 质量趋势分析
  - 质量门禁状态
  - 质量异常预警
services:
  - quality-gate-monitoring
  - degradation-detection
  - quality-trend-analysis
  - gate-compliance-tracking
```

### AGENT-056: Progress Tracker

```yaml
id: AGENT-056
name: Progress Tracker
layer: 监控层（Monitoring）
priority: P1
triggers:
  - 进度跟踪
  - 里程碑
  - progress-tracking
  - 迭代预算
description: |
  项目进度跟踪Agent，负责里程碑管理、迭代预算监控和交付物状态追踪。
  验证LOOP-COMPLETION条件、监控迭代预算消耗、追踪交付物完成状态。
  与Task Coordinator协同，提供实时进度可视化和偏差预警。
dependencies:
  - Task Coordinator（任务状态数据）
  - Orchestrator（迭代预算约束）
output:
  - 项目进度报告
  - 里程碑状态
  - 迭代预算消耗报告
  - LOOP-COMPLETION验证结果
services:
  - phase-progress-tracking
  - milestone-management
  - blocker-detection
  - escalation-management
```

### AGENT-057: Decision Logger

```yaml
id: AGENT-057
name: Decision Logger
layer: 监控层（Monitoring）
priority: P2
triggers:
  - 决策记录
  - Decision Log
  - decision-logging
  - 决策追溯
description: |
  透明决策记录Agent，负责维护Decision Log和决策追溯。
  记录关键决策、关联ADR、评估决策影响、提供决策追溯能力。
  确保所有重要决策可追溯、可审计、可回溯。
dependencies:
  - Orchestrator（决策事件）
  - System Architect（ADR关联）
output:
  - Decision Log条目
  - 决策追溯链
  - 决策影响评估
  - ADR关联记录
services:
  - decision-logging
  - adr-index-maintenance
  - audit-trail
  - decision-retrieval
```

---

## 统计

| 层级 | 数量 | 优先级P0 | 优先级P1 | 优先级P2 |
|------|------|----------|----------|----------|
| 编排层 | 3 | 1 | 2 | 0 |
| 产品层 | 4 | 0 | 4 | 0 |
| 设计层 | 4 | 0 | 3 | 1 |
| 工程层 | 6 | 0 | 5 | 1 |
| 跨平台层 | 5 | 0 | 3 | 2 |
| 数据层 | 3 | 0 | 2 | 1 |
| 测试层 | 10 | 0 | 6 | 4 |
| 安全层 | 3 | 0 | 2 | 1 |
| 运维层 | 4 | 0 | 4 | 0 |
| 质量层 | 7 | 0 | 1 | 6 |
| 文档层 | 2 | 0 | 2 | 0 |
| 知识层 | 3 | 0 | 2 | 1 |
| 监控层 | 3 | 0 | 2 | 1 |
| **合计** | **57** | **1** | **38** | **18** |
