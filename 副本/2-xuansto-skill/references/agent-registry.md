# Agent注册表（41 Agents）

> 版本: 1.9.0 | 更新日期: 2026-04-28 | 编码: UTF-8 | 行尾: LF

本注册表包含Xuansto Skill全部41个Agent的完整注册信息，供Orchestrator进行任务路由和Agent调度时参考。

## 目录

1. [编排层（Orchestrator）- 1个](#编排层orchestrator---1个)
2. [产品层（Product）- 3个](#产品层product---3个)
3. [设计层（Design）- 3个](#设计层design---3个)
4. [工程层（Engineering）- 6个](#工程层engineering---6个)
5. [跨平台层（Cross-Platform）- 3个](#跨平台层cross-platform---3个)
6. [数据层（Database）- 3个](#数据层database---3个)
7. [测试层（Testing）- 10个](#测试层testing---10个)
8. [安全层（Security）- 3个](#安全层security---3个)
9. [运维层（DevOps）- 4个](#运维层devops---4个)
10. [质量层（Quality）- 3个](#质量层quality---3个)
11. [文档层（Documentation）- 2个](#文档层documentation---2个)

---

## 编排层（Orchestrator）- 1个

| 名称 | 职责 | 技能标签 | 优先级 | 定义文件 |
|------|------|----------|--------|----------|
| Orchestrator | 全局编排协调、任务分解、Agent调度、冲突仲裁、平台检测、增量实施死循环检测 | orchestration, coordination, platform-detection, conflict-resolution | P0 | agents/orchestrator/orchestrator.md |

## 产品层（Product）- 3个

| 名称 | 职责 | 技能标签 | 优先级 | 定义文件 |
|------|------|----------|--------|----------|
| Product Manager | 需求澄清、功能分解、用户故事编写、验收标准定义、产品方向决策 | requirements, user-stories, prd, acceptance-criteria | P1 | agents/product/product-manager.md |
| System Architect | 系统架构设计、技术选型、模块划分、接口契约定义、ADR编写、策略性分歧裁决 | architecture, adr, tech-selection, interface-design | P1 | agents/product/system-architect.md |
| Technical Writer | 技术文档编写、API文档生成、README维护、变更日志编写 | documentation, openapi, readme, changelog | P1 | agents/product/technical-writer.md |

## 设计层（Design）- 3个

| 名称 | 职责 | 技能标签 | 优先级 | 定义文件 |
|------|------|----------|--------|----------|
| UI Designer | 界面设计与原型、设计系统建立、Design Token定义、组件库规划 | ui, design-system, tokens, figma, component-library | P1 | agents/design/ui-designer.md |
| UX Designer | 用户体验设计、用户旅程地图、可用性测试、交互设计、可访问性规划 | ux, research, journey-map, usability, accessibility | P1 | agents/design/ux-designer.md |
| Frontend Stylist | 前端样式实现、CSS架构、响应式设计、主题系统、动画效果 | css, responsive, theme, animation, tailwind | P2 | agents/design/frontend-stylist.md |

## 工程层（Engineering）- 6个

| 名称 | 职责 | 技能标签 | 优先级 | 定义文件 |
|------|------|----------|--------|----------|
| Frontend Developer | 前端代码实现、组件开发、状态管理、API集成 | react, vue, css, state-management, api-integration | P1 | agents/engineering/frontend-developer.md |
| Backend Developer | 后端代码实现、API开发、业务逻辑、中间件配置 | api, database, server, middleware, business-logic | P1 | agents/engineering/backend-developer.md |
| Full-Stack Engineer | 全栈开发、前后端集成、端到端功能实现 | fullstack, integration, e2e, deployment | P1 | agents/engineering/fullstack-engineer.md |
| Database Engineer | 数据库设计优化、查询性能调优、数据迁移、索引策略 | database, sql, nosql, query-optimization, migration | P1 | agents/engineering/database-engineer.md |
| Mobile Developer | 移动端开发、跨平台移动适配、原生桥接 | mobile, react-native, flutter, native-bridge | P2 | agents/engineering/mobile-developer.md |
| DevOps Engineer | 基础设施配置、CI/CD流水线、容器化部署、环境管理 | deployment, monitoring, docker, kubernetes, ci-cd | P1 | agents/engineering/devops-engineer.md |

## 跨平台层（Cross-Platform）- 3个

| 名称 | 职责 | 技能标签 | 优先级 | 定义文件 |
|------|------|----------|--------|----------|
| Desktop Developer | 桌面端开发、Electron/Tauri应用开发、IPC通信实现 | electron, tauri, native, ipc, desktop | P1 | agents/cross-platform/desktop-developer.md |
| Desktop UI Adapter | 桌面端UI适配、原生控件集成、窗口管理、平台特定样式 | desktop-ui, responsive, native-controls, window-management | P2 | agents/cross-platform/desktop-ui-adapter.md |
| Native Module Developer | 原生模块开发、C++/Rust FFI绑定、性能关键路径实现 | native, c++, rust, ffi, performance-critical | P2 | agents/cross-platform/native-module-developer.md |

## 数据层（Database）- 3个

| 名称 | 职责 | 技能标签 | 优先级 | 定义文件 |
|------|------|----------|--------|----------|
| Data Modeler | 数据模型设计、ER图绘制、范式优化、数据字典维护 | data-modeling, er-diagram, normalization, schema | P1 | agents/database/data-modeler.md |
| DBA | 数据库管理、性能监控、备份恢复、安全审计 | dba, performance, backup, security, audit | P1 | agents/database/dba.md |
| Data Seeder | 测试数据生成、数据脱敏、数据迁移脚本、种子数据管理 | test-data, seeding, migration, anonymization | P2 | agents/database/data-seeder.md |

## 测试层（Testing）- 10个

| 名称 | 职责 | 技能标签 | 优先级 | 定义文件 |
|------|------|----------|--------|----------|
| Test Architect | 测试架构设计、测试策略制定、测试工具选型、回归测试自动生成 | test-strategy, automation, regression, coverage | P1 | agents/testing/test-architect.md |
| Unit Tester | 单元测试编写、边界条件覆盖、Mock/Stub配置 | unit-test, mocking, boundary, coverage | P1 | agents/testing/unit-tester.md |
| Integration Tester | 集成测试设计、接口契约验证、模块间交互测试 | integration, contract-testing, api-test | P1 | agents/testing/integration-tester.md |
| E2E Tester | 端到端测试执行、用户旅程验证、跨浏览器测试 | e2e, user-journey, cross-browser, playwright | P1 | agents/testing/e2e-tester.md |
| Desktop Tester | 桌面端专项测试、窗口生命周期、安装包测试、IPC通信测试 | desktop-testing, installer-test, ipc-test, window-lifecycle | P2 | agents/testing/desktop-tester.md |
| Performance Tester | 性能基准测试、负载测试、压力测试、性能回归检测 | performance, load-test, stress-test, benchmark | P1 | agents/testing/performance-tester.md |
| Security Tester | 安全扫描、漏洞检测、依赖审计、安全合规验证 | security, vulnerability, dependency-audit, compliance | P1 | agents/testing/security-tester.md |
| AI Penetration Tester | AI驱动的渗透测试、Agentic安全测试、OWASP ASI验证、安全修复闭环 | ai-pentest, owasp-asi, agentic-security, exploit | P1 | agents/testing/ai-penetration-tester.md |
| Test Maintainer | 测试代码维护、测试数据更新、测试环境管理、测试报告生成 | test-maintenance, test-data, test-environment, reporting | P2 | agents/testing/test-maintainer.md |
| QA Engineer | 质量保证、合规审计、验收测试聚合、质量指标跟踪 | qa, compliance, audit, acceptance, metrics | P2 | agents/testing/qa-engineer.md |

## 安全层（Security）- 3个

| 名称 | 职责 | 技能标签 | 优先级 | 定义文件 |
|------|------|----------|--------|----------|
| Security Auditor | 安全审计、合规检查、安全策略制定、OWASP Top 10验证 | security-audit, compliance, owasp, policy | P1 | agents/security/security-auditor.md |
| Penetration Tester | 渗透测试、漏洞利用验证、安全评估报告 | pentest, exploit, vulnerability-assessment | P1 | agents/security/penetration-tester.md |
| Compliance Officer | 合规管理、法规遵循、数据保护、审计跟踪 | compliance, gdpr, data-protection, audit-trail | P2 | agents/security/compliance-officer.md |

## 运维层（DevOps）- 4个

| 名称 | 职责 | 技能标签 | 优先级 | 定义文件 |
|------|------|----------|--------|----------|
| CI/CD Specialist | CI/CD流水线设计、自动化构建、部署策略、环境管理 | ci-cd, automation, pipeline, deployment-strategy | P1 | agents/devops/cicd-specialist.md |
| Build & Release Engineer | 多平台构建、代码签名、安装包生成、发布管理 | build, signing, release, installer, multi-platform | P1 | agents/devops/build-release-engineer.md |
| Monitor Specialist | 监控系统配置、告警规则、可观测性基线、日志管理 | monitoring, alerting, observability, logging | P1 | agents/devops/monitor-specialist.md |
| Runtime Supervisor | 运行时监控、熔断机制、工作流检查点恢复、级联故障防护 | runtime, circuit-breaker, checkpoint, cascading-failure | P1 | agents/devops/runtime-supervisor.md |

## 质量层（Quality）- 3个

| 名称 | 职责 | 技能标签 | 优先级 | 定义文件 |
|------|------|----------|--------|----------|
| Code Reviewer | 代码审查、编码规范检查、最佳实践验证、安全代码审查 | code-review, standards, best-practices, secure-coding | P1 | agents/quality/code-reviewer.md |
| Refactoring Specialist | 代码重构、技术债务管理、设计模式应用、性能优化 | refactoring, tech-debt, design-patterns, optimization | P2 | agents/quality/refactoring-specialist.md |
| Documentation Reviewer | 文档质量审查、一致性检查、完整性验证 | doc-review, consistency, completeness | P2 | agents/quality/doc-reviewer.md |

## 文档层（Documentation）- 2个

| 名称 | 职责 | 技能标签 | 优先级 | 定义文件 |
|------|------|----------|--------|----------|
| Documentation Engineer | 文档工程、API文档自动生成、文档站点构建、知识库维护 | doc-engineering, openapi, docusaurus, knowledge-base | P1 | agents/documentation/documentation-engineer.md |
| Specification Keeper | 规格文档维护、规格漂移审核、知识沉淀、跨分支经验同步、ADR归档 | specification, spec-drift, knowledge-curation, adr, cross-branch-sync | P1 | agents/documentation/specification-keeper.md |

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
| Unit Tester | Frontend/Backend Developer | 代码实现 |
| Integration Tester | Unit Tester | 单元测试通过 |
| E2E Tester | Integration Tester | 集成测试通过 |
| Security Tester | Integration Tester | 集成构建 |
| Performance Tester | Integration Tester | 集成构建 |
| Code Reviewer | Frontend/Backend Developer | 代码实现 |
| Documentation Engineer | All Development Agents | 完整实现 |

### 可并行（无严格依赖）

| Agent组 | 说明 |
|---------|------|
| Product Manager + Technical Writer | 需求分析可与文档模板准备并行 |
| UI Designer + UX Designer | 设计可并行迭代，通过设计令牌同步 |
| Frontend Developer + Backend Developer | 基于契约开发，可并行 |
| Unit Tester (前端) + Unit Tester (后端) | 不同模块的单元测试可并行 |
| Security Auditor + Compliance Officer | 安全审计与合规检查可并行 |

---

## 统计

| 层级 | 数量 | 优先级P0 | 优先级P1 | 优先级P2 |
|------|------|----------|----------|----------|
| 编排层 | 1 | 1 | 0 | 0 |
| 产品层 | 3 | 0 | 3 | 0 |
| 设计层 | 3 | 0 | 2 | 1 |
| 工程层 | 6 | 0 | 5 | 1 |
| 跨平台层 | 3 | 0 | 1 | 2 |
| 数据层 | 3 | 0 | 2 | 1 |
| 测试层 | 10 | 0 | 6 | 4 |
| 安全层 | 3 | 0 | 2 | 1 |
| 运维层 | 4 | 0 | 4 | 0 |
| 质量层 | 3 | 0 | 1 | 2 |
| 文档层 | 2 | 0 | 2 | 0 |
| **合计** | **41** | **1** | **28** | **12** |
