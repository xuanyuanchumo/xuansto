# Xuansto Skill Wiki

> Multi-Agent Autonomous Development Orchestrator | SDD+TDD Fusion
> 版本: v4.1.0 | 文档日期: 2026-05-08 | 基于 skill-creator 方法论系统性分析

---

## 目录

- [1. 项目概述](#1-项目概述)
- [2. 整体架构](#2-整体架构)
- [3. 目录结构](#3-目录结构)
- [4. 核心模块详解](#4-核心模块详解)
- [5. Agent 角色体系（13层/57个）](#5-agent-角色体系13层57个)
- [6. 命令系统（27个）](#6-命令系统27个)
- [7. 工作流体系（15个）](#7-工作流体系15个)
- [8. 质量门禁体系（54个）](#8-质量门禁体系54个)
- [9. 知识库服务层](#9-知识库服务层)
- [10. 脚本体系（49个）](#10-脚本体系49个)
- [11. 模板体系（19个）](#11-模板体系19个)
- [12. 参考文档体系（66+个）](#12-参考文档体系66个)
- [13. 配置体系](#13-配置体系)
- [14. 依赖关系](#14-依赖关系)
- [15. 功能业务与调用链](#15-功能业务与调用链)
- [16. 逻辑链全景](#16-逻辑链全景)
- [17. 项目运行方式](#17-项目运行方式)
- [18. 版本演进](#18-版本演进)
- [19. 完整性审查](#19-完整性审查)

---

## 1. 项目概述

### 1.1 基本信息

| 属性 | 值 |
|------|-----|
| **项目名称** | Xuansto Skill |
| **版本** | v4.1.0 |
| **作者** | skiller-team |
| **许可** | MIT License |
| **定位** | 多Agent自主开发编排器 \| SDD+TDD融合系统 |
| **技能路径** | `.trae/skills/xuansto-skill/` |
| **核心范式** | Spec > Test > Code（规格驱动 > 测试先行 > 代码实现） |

### 1.2 核心能力矩阵

| 能力 | 数量 | 说明 |
|------|------|------|
| Agent架构 | 13层/57个 | 编排→产品→设计→工程→跨平台→数据→测试→安全→运维→质量→文档→知识→监控 |
| 工作流Phase | 9个(0-8) | 初始化→需求→架构→测试先行→实现→验证→验收→重构→部署 |
| 质量门禁 | 54个 | 覆盖全阶段，含跨阶段门禁 |
| 命令 | 27个 | /sprint /clarify /plan ... /rollback |
| 工作流 | 15个 | SDD-TDD(3级)/安全/测试/桌面/跨平台等 |
| 工具脚本 | 49个 | Python/JS/PS1三类运行时 |
| 参考文档 | 66+个 | 15类覆盖（设计/安全/规范/协议/集成/编码/桌面/测试等） |
| 模板 | 19个 | PRD/ADR/API契约/CI-CD/设计系统/测试计划等 |
| 集成模块 | 7个 | Superpowers/Planning/UIUXProMax/CodeReview/CodeSimplifier/WebappTesting/RalphLoop |

### 1.3 核心约束

1. **Spec > Test > Code**：无规格不开发 | 无测试不合并 | 覆盖率≥80%
2. **Karpathy准则**：Think Before Coding | Simplicity First | Surgical Changes
3. **增量约束**：分解→实现→测试→重复；3次失败→停止→反模式→重启；知识库强制工作流
4. **脚本规范**：遵循script-standards.md | Python优先 | UTF-8无BOM+无U+FFFD | 验证后删除
5. **跨平台**：Web+Desktop(Electron/Tauri/Flutter)全平台支持

---

## 2. 整体架构

### 2.1 分层架构图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         用户命令层 (27 Commands)                         │
│  /sprint /clarify /plan /spec /design /implement /test /review /fix    │
│  /accept /deploy /build-desktop /release-desktop /refactor /audit ...  │
├─────────────────────────────────────────────────────────────────────────┤
│                       编排调度层 (Orchestrator Layer)                    │
│  ┌──────────────┐  ┌──────────────────┐  ┌──────────────────┐         │
│  │ Orchestrator │  │ Subagent         │  │ Task             │         │
│  │ (全局编排)   │  │ Dispatcher       │  │ Coordinator      │         │
│  └──────────────┘  │ (子代理调度)     │  │ (任务协调)       │         │
│                    └──────────────────┘  └──────────────────┘         │
├─────────────────────────────────────────────────────────────────────────┤
│                      工作流引擎层 (15 Workflows)                         │
│  SDD-TDD Full/Medium/Fast | Brainstorming | Subagent-Driven |         │
│  UI-UX | Security-Audit | AI-Pentest | Webapp-Testing | Desktop |     │
│  Cross-Platform | Flutter | Bug-Fix | Acceptance | Performance        │
├─────────────────────────────────────────────────────────────────────────┤
│                     Agent执行层 (13 Layers / 57 Agents)                 │
│  产品(4) | 设计(4) | 工程(6) | 跨平台(5) | 数据(3) | 测试(10) |      │
│  安全(3) | 运维(4) | 质量(7) | 文档(2) | 知识(3) | 监控(3)           │
├─────────────────────────────────────────────────────────────────────────┤
│                     质量门禁层 (54 Quality Gates)                        │
│  Phase 0(6) | Phase 1(3) | Phase 2(4) | Phase 3(1) | Phase 4(11) |   │
│  Phase 5(10) | Phase 6(4) | Phase 7(4) | Phase 8(5) | 跨阶段(6)      │
├─────────────────────────────────────────────────────────────────────────┤
│                     基础设施层                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                 │
│  │ 知识库服务   │  │ 脚本引擎     │  │ 配置管理     │                 │
│  │ SQLite+Chroma│  │ Py/JS/PS1    │  │ YAML/JSON    │                 │
│  └──────────────┘  └──────────────┘  └──────────────┘                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                 │
│  │ 模板系统     │  │ 参考文档库   │  │ 通信协议     │                 │
│  │ 19 Templates │  │ 66+ Refs     │  │ A2A/MCP      │                 │
│  └──────────────┘  └──────────────┘  └──────────────┘                 │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 九阶段工作流Phase

| Phase | 名称 | 核心目标 | 关键门禁 |
|-------|------|----------|----------|
| 0 | 初始化/设计 | UX/UI设计、设计系统、反模式检查 | DESIGN-SYSTEM-COMPLETE, ANTI-PATTERN-CHECK, DESIGN-REVIEW/* |
| 1 | 需求分析 | 需求澄清、用户故事、验收标准 | BRAINSTORM-COMPLETE, GATE-001~002 |
| 2 | 架构设计 | 技术选型、模块划分、接口契约 | PLAN-ATOMIC, GATE-003~004 |
| 3 | 测试先行 | TDD红灯阶段、测试用例编写 | TEST-FIRST, GATE-005~006 |
| 4 | 代码实现 | TDD绿灯+重构、子代理审查 | SUBAGENT-REVIEW, REVIEW-CONFIDENCE, GATE-007~009, TDD-RED/GREEN/REFACTOR, SCRIPT-* |
| 5 | 测试验证 | E2E/安全/性能/渗透测试 | PLAYWRIGHT-E2E-PASS, GATE-011~012, AI-PENTEST, SPEC-CONSISTENCY, RENDER-CHECK |
| 6 | 验收确认 | 部署就绪、生产验证、UX验收 | GATE-013~014, INFRA-HEALTH, UX-ACCEPTANCE, DOD-CHECK |
| 7 | 持续重构 | 代码简化、行为等价验证 | SIMPLIFICATION-BEHAVIOR, CHESTERTON-FENCE, GATE-015 |
| 8 | 部署交付 | 桌面构建/签名/更新/跨平台 | DESKTOP-BUILD/SIGN/UPDATE/CROSS, IPC-CONTRACT |

### 2.3 三级渐进式加载

| 层级 | 内容 | 加载时机 |
|------|------|----------|
| L1 元数据 | name + description (~100词) | 始终在上下文中 |
| L2 SKILL.md | 核心规则+索引 (<150行) | 技能触发时加载 |
| L3 引用资源 | references/ + scripts/ + templates/ | 按需加载 |

---

## 3. 目录结构

```
xuansto-skill/
├── SKILL.md                          # 技能主定义文件（YAML frontmatter + Markdown指令）
├── .skill-config.yaml                # 技能运行时配置（Token预算/降级/日志/循环/规划）
├── CHANGELOG.md                      # 版本变更日志
├── configs/
│   └── default.yaml                  # 默认配置文件（编排器/门禁/通信/桌面/日志/知识库/安全/可观测性/成本优化/平台检测/人机协作/知识层/监控层/Karpathy/脚本/编码/Token/循环/规划/审查/简化/测试/按需加载/知识服务/降级）
├── agents/                           # Agent定义文件（13层57个）
│   ├── orchestrator/                 # 编排层（3个）
│   │   ├── orchestrator.md
│   │   ├── subagent-dispatcher.md
│   │   └── task-coordinator.md
│   ├── product/                      # 产品层（4个）
│   │   ├── product-manager.md
│   │   ├── system-architect.md
│   │   ├── technical-writer.md
│   │   └── brainstorming-facilitator.md
│   ├── design/                       # 设计层（4个）
│   │   ├── ui-designer.md
│   │   ├── ux-designer.md
│   │   ├── frontend-stylist.md
│   │   └── design-system-generator.md
│   ├── engineering/                  # 工程层（6个）
│   │   ├── frontend-developer.md
│   │   ├── backend-developer.md
│   │   ├── fullstack-engineer.md
│   │   ├── database-engineer.md
│   │   ├── mobile-developer.md
│   │   └── devops-engineer.md
│   ├── cross-platform/               # 跨平台层（5个）
│   │   ├── desktop-developer.md
│   │   ├── desktop-ui-adapter.md
│   │   ├── native-module-developer.md
│   │   ├── ipc-specialist.md
│   │   └── auto-update-engineer.md
│   ├── database/                     # 数据层（3个）
│   │   ├── data-modeler.md
│   │   ├── dba.md
│   │   └── data-seeder.md
│   ├── testing/                      # 测试层（10个）
│   │   ├── test-architect.md
│   │   ├── unit-tester.md
│   │   ├── integration-tester.md
│   │   ├── e2e-tester.md
│   │   ├── desktop-tester.md
│   │   ├── performance-tester.md
│   │   ├── security-tester.md
│   │   ├── ai-penetration-tester.md
│   │   ├── test-maintainer.md
│   │   └── qa-engineer.md
│   ├── security/                     # 安全层（3个）
│   │   ├── security-auditor.md
│   │   ├── penetration-tester.md
│   │   └── compliance-officer.md
│   ├── devops/                       # 运维层（4个）
│   │   ├── cicd-specialist.md
│   │   ├── build-release-engineer.md
│   │   ├── monitor-specialist.md
│   │   └── runtime-supervisor.md
│   ├── quality/                      # 质量层（7个）
│   │   ├── code-reviewer.md
│   │   ├── refactoring-specialist.md
│   │   ├── doc-reviewer.md
│   │   ├── compliance-reviewer.md
│   │   ├── bug-scanner.md
│   │   ├── history-analyzer.md
│   │   └── comment-verifier.md
│   ├── documentation/                # 文档层（2个）
│   │   ├── documentation-engineer.md
│   │   └── specification-keeper.md
│   ├── knowledge/                    # 知识层（3个）
│   │   ├── knowledge-manager.md
│   │   ├── learning-specialist.md
│   │   └── token-optimizer.md
│   └── monitoring/                   # 监控层（3个）
│       ├── quality-monitor.md
│       ├── progress-tracker.md
│       └── decision-logger.md
├── commands/                         # 命令定义文件（27个）
│   ├── sprint.md / clarify.md / plan.md / spec.md
│   ├── design.md / implement.md / test.md / review.md
│   ├── fix.md / accept.md / deploy.md / build-desktop.md
│   ├── release-desktop.md / refactor.md / audit.md / agent-status.md
│   ├── learn.md / brainstorm.md / execute-plan.md / design-system.md
│   ├── simplify.md / loop.md / cancel-loop.md / build.md
│   ├── init.md / status.md / rollback.md
├── workflows/                        # 工作流定义文件（15个.md + 15个.yaml）
│   ├── sdd-tdd-full.md / sdd-tdd-medium.md / sdd-tdd-fast.md
│   ├── brainstorming-workflow.md / subagent-driven-workflow.md
│   ├── ui-ux-workflow.md / webapp-testing-workflow.md
│   ├── security-audit.md / ai-pentest.md
│   ├── desktop-build-workflow.md / cross-platform-workflow.md
│   ├── flutter-desktop-workflow.md / bug-fix.md
│   ├── acceptance.md / performance-test.md
│   └── _yaml/                        # YAML格式工作流定义
│       ├── sdd-tdd-full.yaml / sdd-tdd-medium.yaml / sdd-tdd-fast.yaml
│       ├── brainstorming-workflow.yaml / subagent-driven-workflow.yaml
│       ├── ui-ux-workflow.yaml / webapp-testing-workflow.yaml
│       ├── security-audit.yaml / ai-pentest.yaml
│       ├── desktop-build-workflow.yaml / cross-platform-workflow.yaml
│       ├── flutter-desktop-workflow.yaml / bug-fix.yaml
│       ├── acceptance.yaml / performance-test.yaml
├── scripts/                          # 工具脚本（49个）
│   ├── knowledge_server/             # 知识库服务模块化包（22个.py）
│   │   ├── __init__.py / main.py / server.py / config.py
│   │   ├── api.py / api_models.py / api_routes.py
│   │   ├── auth.py / security.py / backup.py
│   │   ├── db_engine.py / vector_engine.py / embedding.py
│   │   ├── hybrid_search.py / dedup.py / degradation.py
│   │   ├── distillation.py / exporter.py / importer.py
│   │   ├── lifecycle.py / sync.py / mcp_server.py
│   │   └── websocket_manager.py
│   ├── verification/                 # 验证工具（4个）
│   │   ├── agent-structure-check.py / cmd-agent-check.py
│   │   ├── skill-token-check.py / wf-gate-check.py
│   ├── workflow-tools/               # 工作流工具（5个）
│   │   ├── check-current.py / check-frontmatter.py
│   │   ├── extract-phases.py / fix-frontmatter.py / validate-workflow.py
│   ├── [核心脚本 18个Python]         # token-budget-guard / context-compressor / ...
│   ├── [核心脚本 5个JS]              # accessibility-test / visual-regression / ...
│   └── [核心脚本 3个PS1]             # build-desktop / sign-desktop / verify-auto-update
├── references/                       # 参考文档（66+个）
│   ├── [设计类 7个]                  # design-database / color-palettes / font-pairings / ...
│   ├── [安全类 7个]                  # security-guidelines / owasp-top10-2026 / ...
│   ├── [规范类 6个]                  # quality-gates / agent-registry / coding-standards / ...
│   ├── [协议类 2个]                  # a2a-protocol / mcp-protocol
│   ├── [集成类 6个]                  # agent-forge / cangjie / claude-code-collective / ...
│   ├── [编码规范 7个]                # python / go / java / rust / flutter / typescript / concurrency
│   ├── [桌面类 5个]                  # desktop-dev / flutter-desktop / tauri-dev / ipc / electron-security
│   ├── [测试类 2个]                  # accessibility-testing / component-testing
│   ├── [Agent类 2个]                 # agent-lifecycle / open-source-agent-frameworks
│   ├── [验收类 4个]                  # acceptance-criteria / ci-cd / iteration-scheduling / human-collaboration
│   ├── [数据库 1个]                  # database-guidelines
│   ├── [Git类 2个]                   # git-workflow / git-worktree-parallel
│   ├── [文档类 2个]                  # documentation-standards / documentation-generation
│   ├── [知识库 5个]                  # knowledge-base-architecture / kb-api-reference / token-optimization / karpathy-guidelines / spec-drift-handling
│   └── [其他 8个]                    # deadlock-detection / non-functional-requirements / ...
├── templates/                        # 模板文件（19个）
│   ├── prd-template.md / adr-template.md / rfc-template.md
│   ├── api-contract-template.yaml / ci-cd-pipeline-template.yaml
│   ├── design-system-template.md / design-tokens.json
│   ├── test-plan-template.md / usability-test-plan.md
│   ├── security-checklist.md / accessibility-checklist.md
│   ├── deployment-plan-template.md / rca-template.md
│   ├── user-story-template.md / user-manual-template.md
│   ├── ipc-contract-template.md
│   ├── desktop-build-config-template.yaml / flutter-build-config-template.yaml
│   └── auto-update-config-template.yaml
├── docs/
│   └── knowledge-service-design.md   # 知识库服务层技术设计文档
└── .knowledge/                       # 知识库数据目录
    └── workspace/
        ├── README.md
        ├── architecture/             # 项目架构设计
        ├── domain/                   # 领域知识
        ├── glossary/                 # 术语表（naming-conventions / abbreviations / terms）
        ├── api/                      # API文档与契约
        ├── environment/              # 环境配置（dev-setup / deployment / env-variables）
        ├── desktop/                  # 桌面端项目知识
        └── conventions/              # 项目约定
```

---

## 4. 核心模块详解

### 4.1 七大集成模块

| 模块 | 命令 | 核心Agent | 关键门禁 | 职责 |
|------|------|----------|---------|------|
| **Superpowers** | /brainstorm | Brainstorming Facilitator | BRAINSTORM-COMPLETE | 苏格拉底式6阶段需求探索 |
| **Planning Files** | /loop, /cancel-loop | Orchestrator | LOOP-COMPLETION, ITERATION-BUDGET | 自主迭代循环控制 |
| **UIUXProMax** | /design-system | Design System Generator | DESIGN-SYSTEM-COMPLETE, ANTI-PATTERN-CHECK | 5域并行搜索+推理引擎生成设计系统 |
| **Code Review** | /review | Code Reviewer+5子代理 | REVIEW-CONFIDENCE, MULTI-PERSPECTIVE-COVERAGE | 多视角代码审查（合规/Bug/历史/注释/规格） |
| **Code Simplifier** | /simplify | Refactoring Specialist | SIMPLIFICATION-BEHAVIOR, CHESTERTON-FENCE | 行为等价简化+Chesterton栅栏保护 |
| **WebappTesting** | /test --playwright | E2E Tester | PLAYWRIGHT-E2E-PASS, VISUAL-REGRESSION-PASS | Playwright自动化E2E+视觉回归 |
| **Ralph Loop** | /loop, /sprint --autonomous | Orchestrator | LOOP-COMPLETION | 自主迭代循环执行 |

### 4.2 编排器核心逻辑

Orchestrator作为全局编排核心，负责：

- **任务分解**：将用户需求分解为可执行的子任务
- **Agent调度**：根据任务类型选择合适的Agent，支持串行/并行/混合模式
- **冲突仲裁**：三级仲裁机制（L1技术→L2策略ADR→L3安全人工）
- **平台检测**：自动检测项目类型（Web/Desktop/Flutter）
- **精简模式**：文件<50自动启用精简模式，减少Agent数量
- **死循环检测**：增量实施死循环检测与自动恢复
- **Loop Enforcement**：强制循环执行直到完成承诺"DONE"
- **2-Action Rule**：每轮最多2个研究动作
- **3-Strike Protocol**：3次失败自动升级

### 4.3 Agent合并策略

当项目规模较小时，自动合并功能相近的Agent：

| 合并组 | 条件 | 说明 |
|--------|------|------|
| security-tester + ai-penetration-tester | project_scale < medium | 安全测试与AI渗透测试合并 |
| integration-tester + e2e-tester | project_scale < medium | 集成测试与E2E测试合并 |
| documentation-engineer + specification-keeper | project_scale < medium | 文档工程师与规格管理员合并 |
| cicd-specialist + devops-engineer | project_scale < small | CI/CD专员与DevOps工程师合并 |
| desktop-developer + frontend-developer | desktop_framework == electron | Electron项目桌面与前端合并 |
| desktop-tester + e2e-tester | desktop_test_complexity < medium | 桌面测试简单时与E2E测试合并 |
| build-release-engineer + cicd-specialist | project_scale < small | 小型项目构建发布与CI/CD合并 |
| knowledge-manager + learning-specialist | project_scale < medium | 知识管理器与学习专员合并 |
| quality-monitor + progress-tracker | project_scale < medium | 质量监控与进度追踪合并 |

---

## 5. Agent角色体系（13层/57个）

### 5.1 编排层（Orchestrator）- 3个

| Agent | 职责 | 优先级 | 技能标签 |
|-------|------|--------|----------|
| **Orchestrator** | 全局编排协调、任务分解、Agent调度、冲突仲裁、平台检测、增量实施死循环检测 | P0 | orchestration, coordination, platform-detection |
| **Subagent Dispatcher** | 子代理调度分发、两阶段审查协调(计划合规+代码质量)、子代理结果聚合、返工流程管理 | P1 | subagent-creation, two-stage-review, rework-management |
| **Task Coordinator** | 任务协调与依赖管理、跨Agent任务编排、并行任务调度、任务状态跟踪、冲突检测与解决 | P1 | task-coordination, dependency-management, progress-tracking |

### 5.2 产品层（Product）- 4个

| Agent | 职责 | 优先级 | 技能标签 |
|-------|------|--------|----------|
| **Product Manager** | 需求澄清、功能分解、用户故事编写、验收标准定义、产品方向决策 | P1 | requirements, user-stories, acceptance-criteria |
| **System Architect** | 系统架构设计、技术选型、模块划分、接口契约定义、ADR编写、策略性分歧裁决 | P1 | architecture, adr, tech-selection |
| **Technical Writer** | 技术文档编写、API文档生成、README维护、变更日志编写 | P1 | documentation, api-docs, readme |
| **Brainstorming Facilitator** | 苏格拉底式需求探索、6阶段引导(Discovery→Option→Design→Reflect→Commit→Transition)、结构化设计文档生成 | P1 | brainstorming, socratic-dialogue, design-document |

### 5.3 设计层（Design）- 4个

| Agent | 职责 | 优先级 | 技能标签 |
|-------|------|--------|----------|
| **UI Designer** | 界面设计与原型、设计系统建立、Design Token定义、组件库规划 | P1 | visual-design, design-system, design-tokens |
| **UX Designer** | 用户体验设计、用户旅程地图、可用性测试、交互设计、可访问性规划 | P1 | user-research, interaction-design, accessibility |
| **Frontend Stylist** | 前端样式实现、CSS架构、响应式设计、主题系统、动画效果 | P2 | css, responsive, animation |
| **Design System Generator** | 设计系统自动生成、风格/配色/字体推理选择、反模式检查、WCAG AA对比度验证 | P1 | design-system-generation, style-reasoning, anti-pattern-filtering |

### 5.4 工程层（Engineering）- 6个

| Agent | 职责 | 优先级 | 技能标签 |
|-------|------|--------|----------|
| **Frontend Developer** | 前端代码实现、组件开发、状态管理、API集成 | P1 | react, vue, angular, components |
| **Backend Developer** | 后端代码实现、API开发、业务逻辑、中间件配置 | P1 | api, middleware, business-logic |
| **Fullstack Engineer** | 全栈开发、前后端集成、端到端功能实现 | P1 | integration, contract-testing, e2e |
| **Database Engineer** | 数据库设计优化、查询性能调优、数据迁移、索引策略 | P1 | schema, indexing, sql-review |
| **Mobile Developer** | 移动端开发、跨平台移动适配、原生桥接 | P2 | react-native, flutter, responsive |
| **DevOps Engineer** | 基础设施配置、CI/CD流水线、容器化部署、环境管理 | P1 | docker, k8s, github-actions |

### 5.5 跨平台层（Cross-Platform）- 5个

| Agent | 职责 | 优先级 | 技能标签 |
|-------|------|--------|----------|
| **Desktop Developer** | 桌面端开发、Electron/Tauri应用开发、IPC通信实现 | P1 | electron, tauri, ipc |
| **Desktop UI Adapter** | 桌面端UI适配、原生控件集成、窗口管理、平台特定样式 | P2 | window-management, native-menu, system-theme |
| **Native Module Developer** | 原生模块开发、C++/Rust FFI绑定、性能关键路径实现 | P2 | n-api, rust-ffi, native-dialogs |
| **IPC Specialist** | IPC通信架构设计、进程间消息协议定义、序列化优化、IPC安全审计 | P1 | ipc-contract-design, secure-channel-management |
| **Auto-Update Engineer** | 自动更新机制设计、增量更新策略、版本回滚、更新签名验证 | P1 | auto-update-design, incremental-update, rollback-mechanism |

### 5.6 数据层（Database）- 3个

| Agent | 职责 | 优先级 | 技能标签 |
|-------|------|--------|----------|
| **Data Modeler** | 数据模型设计、ER图绘制、范式优化、数据字典维护 | P1 | er-diagram, normalization, relations |
| **DBA** | 数据库管理、性能监控、备份恢复、安全审计 | P1 | slow-query, execution-plan, backup |
| **Data Seeder** | 测试数据生成、数据脱敏、数据迁移脚本、种子数据管理 | P2 | seed-scripts, data-factory, anonymization |

### 5.7 测试层（Testing）- 10个

| Agent | 职责 | 优先级 | 技能标签 |
|-------|------|--------|----------|
| **Test Architect** | 测试架构设计、测试策略制定、测试工具选型、回归测试自动生成 | P1 | test-strategy, coverage, framework-selection |
| **Unit Tester** | 单元测试编写、边界条件覆盖、Mock/Stub配置 | P1 | unit-tests, mocking, boundary-testing |
| **Integration Tester** | 集成测试设计、接口契约验证、模块间交互测试 | P1 | api-tests, database-tests, contract-tests |
| **E2E Tester** | 端到端测试执行、用户旅程验证、跨浏览器测试、Playwright自动化 | P1 | playwright, cypress, visual-regression |
| **Desktop Tester** | 桌面端专项测试、窗口生命周期、安装包测试、IPC通信测试 | P2 | window-testing, ipc-testing, offline-testing |
| **Performance Tester** | 性能基准测试、负载测试、压力测试、性能回归检测 | P1 | k6, jmeter, load-testing |
| **Security Tester** | 安全扫描、漏洞检测、依赖审计、安全合规验证 | P1 | owasp, sqli, xss, csrf |
| **AI Penetration Tester** | AI驱动的渗透测试、Agentic安全测试、OWASP ASI验证、安全修复闭环 | P1 | ai-pentest, multi-agent-recon, exploit-chain |
| **Test Maintainer** | 测试代码维护、测试数据更新、测试环境管理、测试报告生成 | P2 | test-dedup, flaky-detection, optimization |
| **QA Engineer** | 质量保证、合规审计、验收测试聚合、质量指标跟踪 | P2 | quality-gates, compliance, uat |

### 5.8 安全层（Security）- 3个

| Agent | 职责 | 优先级 | 技能标签 |
|-------|------|--------|----------|
| **Security Auditor** | 安全审计、合规检查、安全策略制定、OWASP Top 10验证 | P1 | sast, cve, secure-coding |
| **Penetration Tester** | 渗透测试、漏洞利用验证、安全评估报告 | P1 | auth-bypass, privilege-escalation, injection |
| **Compliance Officer** | 合规管理、法规遵循、数据保护、审计跟踪 | P2 | gdpr, pci-dss, audit-trail |

### 5.9 运维层（DevOps）- 4个

| Agent | 职责 | 优先级 | 技能标签 |
|-------|------|--------|----------|
| **CI/CD Specialist** | CI/CD流水线设计、自动化构建、部署策略、环境管理 | P1 | github-actions, gitlab-ci, multi-env |
| **Build-Release Engineer** | 多平台构建、代码签名、安装包生成、发布管理 | P1 | electron-builder, tauri-bundler, code-signing |
| **Monitor Specialist** | 监控系统配置、告警规则、可观测性基线、日志管理 | P1 | prometheus, sentry, elk |
| **Runtime Supervisor** | 运行时监控、熔断机制、工作流检查点恢复、级联故障防护 | P1 | health-check, checkpoint-recovery, scaling |

### 5.10 质量层（Quality）- 7个

| Agent | 职责 | 优先级 | 技能标签 |
|-------|------|--------|----------|
| **Code Reviewer** | 代码审查、编码规范检查、最佳实践验证、安全代码审查 | P1 | code-standards, design-patterns, complexity |
| **Refactoring Specialist** | 代码重构、技术债务管理、设计模式应用、性能优化 | P2 | code-smells, refactoring-patterns, simplification |
| **Doc Reviewer** | 文档质量审查、一致性检查、完整性验证 | P2 | doc-coverage, openapi-consistency, style-check |
| **Compliance Reviewer** | 合规性审查、编码规范验证、最佳实践合规检查 | P2 | coding-standards, project-conventions |
| **Bug Scanner** | Bug模式扫描、常见缺陷检测、边界条件分析、异常路径识别 | P2 | bug-detection, logic-analysis, edge-case-check |
| **History Analyzer** | 变更历史分析、回归风险评估、修改影响范围识别 | P2 | git-blame, change-history, context-correlation |
| **Comment Verifier** | 注释准确性验证、注释与代码同步检查、过时注释检测 | P2 | comment-accuracy, doc-code-sync |

### 5.11 文档层（Documentation）- 2个

| Agent | 职责 | 优先级 | 技能标签 |
|-------|------|--------|----------|
| **Documentation Engineer** | 文档工程、API文档自动生成、文档站点构建、知识库维护 | P1 | user-manual, dev-guide, troubleshooting |
| **Specification Keeper** | 规格文档维护、规格漂移审核、知识沉淀、跨分支经验同步、ADR归档 | P1 | cross-reference, version-tracking, backup-scheduling |

### 5.12 知识层（Knowledge）- 3个

| Agent | 职责 | 优先级 | 技能标签 |
|-------|------|--------|----------|
| **Knowledge Manager** | 知识库架构管理、知识条目CRUD、知识检索与推荐、SQLite+Chroma双引擎管理 | P1 | knowledge-base-management, knowledge-indexing, knowledge-retrieval |
| **Learning Specialist** | 知识学习与提取、经验模式识别、反模式沉淀、跨项目知识迁移 | P2 | experience-extraction, pattern-learning, knowledge-dedup |
| **Token Optimizer** | Token预算管理、上下文压缩、信息密度优化、冗余检测与消除 | P1 | token-budget-management, context-compression, tes-scoring |

### 5.13 监控层（Monitoring）- 3个

| Agent | 职责 | 优先级 | 技能标签 |
|-------|------|--------|----------|
| **Quality Monitor** | 六维质量监控、质量指标聚合、质量趋势分析、质量门禁状态追踪、异常预警 | P1 | quality-gate-monitoring, degradation-detection |
| **Progress Tracker** | 项目进度跟踪、里程碑管理、迭代预算监控、交付物状态追踪 | P1 | phase-progress-tracking, milestone-management, blocker-detection |
| **Decision Logger** | 透明决策记录、Decision Log维护、决策追溯、ADR关联、决策影响评估 | P2 | decision-logging, adr-index-maintenance, audit-trail |

---

## 6. 命令系统（27个）

### 6.1 命令总览

| 命令 | 说明 | 核心Agent | 关键门禁 | 工作流引用 |
|------|------|----------|---------|-----------|
| `/sprint` | 冲刺规划 | Orchestrator | LOOP-COMPLETION | sdd-tdd-* |
| `/clarify` | 需求澄清 | Product Manager | GATE-001 | brainstorming-workflow |
| `/plan` | 架构规划 | System Architect | GATE-003, PLAN-ATOMIC | sdd-tdd-* |
| `/spec` | 规格编写 | Product Manager, System Architect | GATE-002, SPEC-ATOMIC | sdd-tdd-* |
| `/design` | UI/UX设计 | UI Designer, UX Designer | DESIGN-SYSTEM-COMPLETE | ui-ux-workflow |
| `/implement` | TDD实现 | Frontend/Backend Developer | TDD-RED/GREEN/REFACTOR, GATE-007~009 | sdd-tdd-*, subagent-driven |
| `/test` | 测试执行 | Unit/E2E/Integration Tester | TEST-PASS, GATE-011 | webapp-testing-workflow |
| `/review` | 代码审查 | Code Reviewer + 5子代理 | REVIEW-CONFIDENCE, MULTI-PERSPECTIVE-COVERAGE | subagent-driven-workflow |
| `/fix` | Bug修复 | Frontend/Backend Developer | TEST-PASS | bug-fix |
| `/accept` | 验收确认 | QA Engineer | GATE-013~014, UX-ACCEPTANCE | acceptance |
| `/deploy` | 部署发布 | CI/CD Specialist | GATE-013~014 | — |
| `/build-desktop` | 桌面构建 | Build-Release Engineer | DESKTOP-BUILD/SIGN/UPDATE/CROSS | desktop-build-workflow |
| `/release-desktop` | 桌面发布 | Build-Release Engineer | DESKTOP-BUILD, IPC-CONTRACT | desktop-build-workflow |
| `/refactor` | 代码重构 | Refactoring Specialist | SIMPLIFICATION-BEHAVIOR, CHESTERTON-FENCE | — |
| `/audit` | 安全审计 | Security Auditor + Penetration Tester | GATE-012, AI-PENTEST | security-audit, ai-pentest |
| `/agent-status` | 状态监控 | Quality Monitor | STATUS-HEALTHY | — |
| `/learn` | 知识学习 | Learning Specialist | — | — |
| `/brainstorm` | 需求探索 | Brainstorming Facilitator | BRAINSTORM-COMPLETE | brainstorming-workflow |
| `/execute-plan` | 执行计划 | Subagent Dispatcher | SUBAGENT-REVIEW | subagent-driven-workflow |
| `/design-system` | 设计系统 | Design System Generator | DESIGN-SYSTEM-COMPLETE, ANTI-PATTERN-CHECK | ui-ux-workflow |
| `/simplify` | 代码简化 | Refactoring Specialist | SIMPLIFICATION-BEHAVIOR, CHESTERTON-FENCE | — |
| `/loop` | 循环执行 | Orchestrator | LOOP-COMPLETION, ITERATION-BUDGET | — |
| `/cancel-loop` | 取消循环 | Orchestrator | — | — |
| `/build` | 项目构建 | Build-Release Engineer | BUILD-SUCCESS | — |
| `/init` | 初始化项目 | Orchestrator | INIT-COMPLETE | — |
| `/status` | 状态检查 | Quality Monitor | STATUS-HEALTHY | — |
| `/rollback` | 回滚版本 | CI/CD Specialist | ROLLBACK-SAFETY | — |

### 6.2 命令增强选项

| 命令 | 增强选项 |
|------|----------|
| `/review` | --confidence-threshold, --focus-areas, --scope |
| `/refactor` | --simplify, --scope, --aggressive |
| `/test` | --playwright, --screenshot, --visual-regression, --browsers, --server, --port |
| `/sprint` | --autonomous |

---

## 7. 工作流体系（15个）

### 7.1 SDD-TDD核心工作流（3级）

| 工作流 | 阶段数 | 适用场景 | 说明 |
|--------|--------|----------|------|
| **sdd-tdd-full** | 9阶段 | 大型项目 | 完整SDD+TDD流程，所有门禁启用 |
| **sdd-tdd-medium** | 精简 | 中型项目 | 合并部分阶段，减少Agent数量 |
| **sdd-tdd-fast** | 极简 | 小型项目/快速迭代 | 最少阶段，核心门禁 |

### 7.2 专项工作流

| 工作流 | 阶段 | 核心Agent | 关键门禁 | 触发条件 |
|--------|------|----------|---------|----------|
| **brainstorming-workflow** | 6阶段 | Brainstorming Facilitator | BRAINSTORM-COMPLETE | /brainstorm, /clarify |
| **subagent-driven-workflow** | 多阶段 | Subagent Dispatcher | SUBAGENT-REVIEW, REVIEW-CONFIDENCE | /review, /execute-plan |
| **ui-ux-workflow** | 多阶段 | Design System Generator | DESIGN-SYSTEM-COMPLETE, ANTI-PATTERN-CHECK | /design, /design-system |
| **webapp-testing-workflow** | 多阶段 | E2E Tester | PLAYWRIGHT-E2E-PASS, VISUAL-REGRESSION-PASS | /test --playwright |
| **security-audit** | 多阶段 | Security Auditor | GATE-012 | /audit |
| **ai-pentest** | 多阶段 | AI Penetration Tester | AI-PENTEST, AGENTIC-SECURITY | /audit (深度) |
| **desktop-build-workflow** | 多阶段 | Build-Release Engineer | DESKTOP-BUILD/SIGN/UPDATE | /build-desktop |
| **cross-platform-workflow** | 多阶段 | Desktop Developer | DESKTOP-CROSS, IPC-CONTRACT | 跨平台开发 |
| **flutter-desktop-workflow** | 5阶段 | Desktop Developer | 5个Flutter专用门禁 | Flutter桌面开发 |
| **bug-fix** | 多阶段 | Frontend/Backend Developer | TEST-PASS | /fix |
| **acceptance** | 多阶段 | QA Engineer | GATE-013~014, UX-ACCEPTANCE | /accept |
| **performance-test** | 多阶段 | Performance Tester | PERFORMANCE | 性能测试 |

### 7.3 Phase→工作流映射

| Phase | 核心工作流 | 关键参考 |
|-------|-----------|----------|
| 0 | brainstorming-workflow | design-database.md, design-guidelines.md |
| 1 | brainstorming-workflow | collaboration-modes.md |
| 2 | sdd-tdd-full/medium | coding-standards.md, script-standards.md |
| 3 | sdd-tdd-full/medium | test-guidelines.md |
| 4 | sdd-tdd-full/medium, subagent-driven-workflow | script-standards.md, coding-standards.md |
| 5 | webapp-testing-workflow | security-*.md, performance-test.md |
| 6 | acceptance | quality-gates.md |
| 7 | — | collaboration-modes.md |
| 8 | desktop-build-workflow | cross-platform-workflow.md |

---

## 8. 质量门禁体系（54个）

### 8.1 门禁按Phase分布

| Phase | 门禁数 | 门禁列表 |
|-------|--------|----------|
| **Phase 0** | 6 | DESIGN-REVIEW-PRODUCT, DESIGN-REVIEW-TECH, DESIGN-REVIEW-DESIGN, DESIGN-TOKENS, DESIGN-SYSTEM-COMPLETE, ANTI-PATTERN-CHECK |
| **Phase 1** | 3 | GATE-001(需求完整性), GATE-002(规格一致性), BRAINSTORM-COMPLETE |
| **Phase 2** | 4 | GATE-003(架构合理性), GATE-004(接口契约), PLAN-ATOMIC, SPEC-ATOMIC |
| **Phase 3** | 1 | TEST-FIRST(含覆盖率+测试数据) |
| **Phase 4** | 11 | GATE-007(代码质量), TEST-PASS, GATE-009(代码审查), MULTI-PERSPECTIVE-COVERAGE, TDD-RED, TDD-GREEN, TDD-REFACTOR, EXECUTION-VERIFY, SCRIPT-SECURITY, SCRIPT-CLEANUP, TOKEN-BUDGET |
| **Phase 5** | 10 | GATE-011(E2E), GATE-012(安全), SPEC-CONSISTENCY, AGENTIC-SECURITY, AI-PENTEST, VISUAL-REGRESSION, RENDER-CHECK, ACCESSIBILITY, PERFORMANCE, SECURITY-FIX-CLOSED |
| **Phase 6** | 4 | GATE-013(部署就绪), GATE-014(生产验证), UX-ACCEPTANCE, DOD-CHECK |
| **Phase 7** | 4 | GATE-015(演化闭环), DOC-COMPLETENESS, SIMPLIFICATION-BEHAVIOR, CHESTERTON-FENCE |
| **Phase 8** | 5 | DESKTOP-BUILD, DESKTOP-SIGN, DESKTOP-UPDATE, DESKTOP-CROSS, IPC-CONTRACT |
| **跨阶段** | 6 | ITERATION-BUDGET, SESSION-RECOVERY, BUILD-SUCCESS, ROLLBACK-SAFETY, INIT-COMPLETE, STATUS-HEALTHY |

### 8.2 门禁阻塞级别

| 级别 | 说明 |
|------|------|
| **BLOCK** | 阻断后续流程，必须修复 |
| **WARN** | 警告，可继续但需记录 |
| **INFO** | 信息性提示 |

### 8.3 门禁别名映射

SKILL.md及命令文件使用语义化别名，quality-gates.md使用结构化ID。关键映射：

| 别名 | 对应ID | 说明 |
|------|--------|------|
| REQ-COMPLETENESS | GATE-001 | 需求完整性 |
| SPEC-DOC-CONSISTENCY | GATE-002 | 规格文档一致性 |
| ARCH-REVIEW | GATE-003 | 架构合理性 |
| CONTRACT | GATE-004 | 接口契约 |
| LINT | GATE-007 | 代码规范检查 |
| CODE-REVIEW | GATE-009 | 代码审查 |
| E2E-TEST | GATE-011 | 端到端测试 |
| SECURITY | GATE-012 | 安全扫描 |
| DEPLOY-READY | GATE-013 | 部署就绪 |
| PROD-VERIFY | GATE-014 | 生产环境验证 |
| ITERATION-CLOSE | GATE-015 | 迭代闭环 |

---

## 9. 知识库服务层

### 9.1 架构定位

知识库服务层是v1.7.0引入的核心基础设施，将纯文件存储升级为服务化架构，提供统一数据访问和混合检索能力。

### 9.2 双引擎架构

```
┌─────────────────────────────────────────────────────────────┐
│                  知识库数据库服务层架构                        │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ FastAPI HTTP │  │ MCP Tool     │  │ WebSocket    │     │
│  │ REST API     │  │ Interface    │  │ 实时通知      │     │
│  │ :8765/v1/*   │  │ knowledge_*  │  │ /ws/notify   │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         └─────────────────┼─────────────────┘              │
│                    ┌──────▼──────┐                          │
│                    │ 服务编排层  │                          │
│                    └──────┬──────┘                          │
│         ┌─────────────────┼─────────────────┐              │
│  ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐       │
│  │ SQLite      │  │ Chroma      │  │ 文件存储    │       │
│  │ 结构化存储  │  │ 向量语义    │  │ (Fallback)  │       │
│  │ knowledge.db│  │ Collection  │  │ v1.6兼容    │       │
│  └─────────────┘  └─────────────┘  └─────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

| 引擎 | 职责 | 检索能力 |
|------|------|----------|
| **SQLite** | 知识条目CRUD、元数据管理、全文检索、版本追踪 | FTS5全文搜索、结构化查询、事务支持 |
| **Chroma** | 语义相似度检索、向量嵌入管理 | 余弦相似度、语义匹配、模糊概念检索 |

### 9.3 三大接口通道

| 通道 | 协议 | 用途 | 消费者 |
|------|------|------|--------|
| FastAPI HTTP REST | HTTP/1.1 | 标准CRUD、混合检索、健康检查 | 外部工具、CI/CD |
| MCP Tool Interface | MCP Protocol (stdio) | Agent直接调用知识检索与写入 | 多Agent系统 |
| WebSocket 实时通知 | WebSocket | 知识变更推送、冲突预警 | 订阅Agent、监控面板 |

### 9.4 三层知识库

| 层级 | 路径 | 用途 |
|------|------|------|
| **通用知识** | .knowledge/general/ | 跨项目通用知识、最佳实践 |
| **工作知识** | .knowledge/workspace/ | 项目级知识（架构/领域/API/环境/术语） |
| **经验知识** | .knowledge/experience/ | 项目经验沉淀、决策记录、模式学习 |

### 9.5 数据流

**写入流**：
```
Agent → MCP Tool / REST API → 服务编排层
    → SQLite (结构化存储 + FTS索引更新)
    → Chroma (向量嵌入计算 + Collection更新)
    → WebSocket (变更通知 → 订阅Agent)
```

**读取流**：
```
查询请求 → 服务编排层 → 混合检索引擎
    → SQLite FTS5 (关键词检索 → 排名列表)
    → Chroma (语义检索 → 排名列表)
    → RRF融合 → 排序结果 → 返回
```

### 9.6 三级降级策略

| 级别 | 名称 | 触发条件 | 搜索策略 |
|------|------|----------|----------|
| L1 | Normal | Token使用率<80% | hybrid（BM25+语义） |
| L2 | Local Semantic | Token使用率80%~95% | hybrid（本地语义） |
| L3 | BM25-only | Token使用率≥95% | keyword_only（仅关键词） |

### 9.7 知识库服务模块

knowledge_server/ 包含22个Python模块：

| 模块 | 职责 |
|------|------|
| `main.py` | 入口，启动FastAPI服务 |
| `server.py` | 服务核心，路由注册 |
| `config.py` | 配置加载 |
| `api.py` | API业务逻辑 |
| `api_models.py` | Pydantic数据模型 |
| `api_routes.py` | 路由定义 |
| `auth.py` | API Key认证与权限分级 |
| `security.py` | 敏感内容过滤、输入验证 |
| `backup.py` | 备份与恢复管理 |
| `db_engine.py` | SQLite引擎封装 |
| `vector_engine.py` | Chroma向量引擎封装 |
| `embedding.py` | 向量嵌入计算 |
| `hybrid_search.py` | RRF混合检索引擎 |
| `dedup.py` | 去重引擎（精确+语义） |
| `degradation.py` | 三级降级策略 |
| `distillation.py` | 知识蒸馏 |
| `exporter.py` | DB→Markdown双向同步 |
| `importer.py` | 首次运行自动导入 |
| `lifecycle.py` | 知识条目生命周期管理 |
| `sync.py` | 增量同步模块 |
| `mcp_server.py` | MCP Tool接口 |
| `websocket_manager.py` | WebSocket实时通知 |

---

## 10. 脚本体系（49个）

### 10.1 按功能分类

#### 知识库服务（22个 - knowledge_server/包）

见 [9.7 知识库服务模块](#97-知识库服务模块)

#### Token优化（4个）

| 脚本 | 语言 | 职责 |
|------|------|------|
| `token-budget-guard.py` | Python | Token预算门禁，80%WARN/100%BLOCK |
| `context-compressor.py` | Python | 上下文压缩（无损/语义/选择性三级） |
| `token-dashboard.py` | Python | Token使用仪表盘 |
| `pattern-learner.py` | Python | 模式学习与经验提取 |

#### 代码质量（8个）

| 脚本 | 语言 | 职责 |
|------|------|------|
| `check-encoding.py` | Python | UTF-8无BOM+无U+FFFD编码检查 |
| `check-comment-lang.py` | Python | 注释语言合规性检查（zh-business策略） |
| `coverage-check.py` | Python | 测试覆盖率检查（coverage API） |
| `code-simplifier.py` | Python | 代码简化分析 |
| `deduplication-detector.py` | Python | 重复代码检测 |
| `documentation-coverage.py` | Python | 文档覆盖率检查 |
| `confidence-scorer.py` | Python | 审查置信度评分 |
| `check-complete.py` | Python | 任务完成度验证 |

#### 安全审计（5个）

| 脚本 | 语言 | 职责 |
|------|------|------|
| `script-security-scanner.py` | Python | 脚本安全约束扫描 |
| `agentic-security-scanner.py` | Python | Agentic安全扫描 |
| `ai-pentest-runner.py` | Python | AI渗透测试执行器 |
| `dependency-scan.py` | Python | 依赖漏洞扫描 |
| `api-contract-validator.py` | Python | API契约验证 |

#### 审查与评审（3个）

| 脚本 | 语言 | 职责 |
|------|------|------|
| `review-aggregator.py` | Python | 多视角审查结果聚合 |
| `review-eligibility-check.py` | Python | 审查资格检查 |
| `skill-md-validator.py` | Python | SKILL.md结构验证 |

#### 规划与循环（5个）

| 脚本 | 语言 | 职责 |
|------|------|------|
| `init-session.py` | Python | 会话初始化 |
| `session-catchup.py` | Python | 会话恢复与上下文补全 |
| `plan-sync.py` | Python | 规划文件同步 |
| `loop-guard.py` | Python | 循环执行保护 |
| `completion-verifier.py` | Python | 完成承诺验证 |

#### 知识库工具（4个）

| 脚本 | 语言 | 职责 |
|------|------|------|
| `knowledge-server.py` | Python | 知识库服务入口（独立运行） |
| `kb-migrate.py` | Python | 知识库迁移工具 |
| `knowledge-index-builder.py` | Python | 知识索引构建 |
| `knowledge-server-tests.py` | Python | 知识库服务测试 |

#### 基础设施（3个）

| 脚本 | 语言 | 职责 |
|------|------|------|
| `infra-health-check.py` | Python | 基础设施健康检查 |
| `health-checker.py` | Python | 通用健康检查 |
| `build-optimizer.py` | Python | 构建优化 |

#### Webapp测试（5个JS）

| 脚本 | 语言 | 职责 |
|------|------|------|
| `accessibility-test.js` | JS | WCAG 2.1 AA可访问性测试(@axe-core/playwright) |
| `visual-regression.js` | JS | 视觉回归测试(Playwright+pixelmatch) |
| `performance-benchmark.js` | JS | 性能基准测试 |
| `design-tokens-sync.js` | JS | Design Tokens同步验证 |
| `ipc-contract-validator.js` | JS | IPC契约验证 |

#### 桌面构建（3个PS1）

| 脚本 | 语言 | 职责 |
|------|------|------|
| `build-desktop.ps1` | PowerShell | 桌面应用构建 |
| `sign-desktop.ps1` | PowerShell | 代码签名 |
| `verify-auto-update.ps1` | PowerShell | 自动更新验证 |

#### 验证工具（4个 - verification/）

| 脚本 | 语言 | 职责 |
|------|------|------|
| `agent-structure-check.py` | Python | Agent结构完整性验证 |
| `cmd-agent-check.py` | Python | 命令-Agent映射验证 |
| `skill-token-check.py` | Python | 技能Token预算验证 |
| `wf-gate-check.py` | Python | 工作流门禁一致性验证 |

#### 工作流工具（5个 - workflow-tools/）

| 脚本 | 语言 | 职责 |
|------|------|------|
| `check-current.py` | Python | 当前工作流状态检查 |
| `check-frontmatter.py` | Python | Frontmatter元数据验证 |
| `extract-phases.py` | Python | 阶段提取工具 |
| `fix-frontmatter.py` | Python | Frontmatter修复工具 |
| `validate-workflow.py` | Python | 工作流有效性验证 |

#### 其他工具（5个）

| 脚本 | 语言 | 职责 |
|------|------|------|
| `spec-drift-detector.py` | Python | 规格漂移检测 |
| `db-migration-validator.py` | Python | 数据库迁移验证 |
| `script-cleanup-checker.py` | Python | 临时脚本清理检查 |
| `agent-frontmatter-validator.py` | Python | Agent Frontmatter验证 |
| `skill-test.py` | Python | 技能集成测试 |

---

## 11. 模板体系（19个）

| 模板 | 类型 | 用途 |
|------|------|------|
| `prd-template.md` | Markdown | 产品需求文档模板 |
| `adr-template.md` | Markdown | 架构决策记录模板 |
| `rfc-template.md` | Markdown | 请求评论文档模板 |
| `api-contract-template.yaml` | YAML | API契约定义模板 |
| `ci-cd-pipeline-template.yaml` | YAML | CI/CD流水线配置模板 |
| `design-system-template.md` | Markdown | 设计系统文档模板 |
| `design-tokens.json` | JSON | Design Tokens定义模板 |
| `test-plan-template.md` | Markdown | 测试计划模板 |
| `usability-test-plan.md` | Markdown | 可用性测试计划模板 |
| `security-checklist.md` | Markdown | 安全检查清单模板 |
| `accessibility-checklist.md` | Markdown | 可访问性检查清单模板 |
| `deployment-plan-template.md` | Markdown | 部署计划模板 |
| `rca-template.md` | Markdown | 根因分析模板 |
| `user-story-template.md` | Markdown | 用户故事模板 |
| `user-manual-template.md` | Markdown | 用户手册模板 |
| `ipc-contract-template.md` | Markdown | IPC契约定义模板 |
| `desktop-build-config-template.yaml` | YAML | 桌面构建配置模板 |
| `flutter-build-config-template.yaml` | YAML | Flutter桌面构建配置模板 |
| `auto-update-config-template.yaml` | YAML | 自动更新配置模板 |

---

## 12. 参考文档体系（66+个）

### 按类别索引

| 类别 | 数量 | 文件列表 |
|------|------|----------|
| **设计** | 7 | design-database, color-palettes, font-pairings, product-reasoning-rules, chart-recommendations, design-guidelines, design-token-system |
| **安全** | 7 | security-frontier-frameworks, ai-pentest-frameworks, agentic-security-frameworks, owasp-agentic-top10-2026, owasp-top10-2026, owasp-mcp-top10, security-guidelines |
| **规范** | 6 | quality-gates, agent-registry, collaboration-modes, coding-standards, script-standards, test-guidelines |
| **协议** | 2 | a2a-protocol, mcp-protocol |
| **集成** | 6 | agent-forge-integration, cangjie-skills-integration, claude-code-collective-integration, hivehub-rulebook-integration, open-source-integration, sddwcc-integration |
| **编码规范** | 7 | python-standards, go-standards, java-standards, rust-standards, flutter-standards, typescript-standards, concurrency-standards |
| **桌面** | 5 | desktop-dev-guidelines, flutter-desktop-guidelines, tauri-dev-guidelines, ipc-contracts, electron-security |
| **测试** | 2 | accessibility-testing, component-testing |
| **Agent** | 2 | agent-lifecycle, open-source-agent-frameworks |
| **验收** | 4 | acceptance-criteria, ci-cd-integration, iteration-scheduling, human-collaboration |
| **数据库** | 1 | database-guidelines |
| **Git** | 2 | git-workflow, git-worktree-parallel |
| **文档** | 2 | documentation-standards, documentation-generation |
| **知识库** | 5 | knowledge-base-architecture, kb-api-reference, token-optimization, karpathy-guidelines, spec-drift-handling |
| **其他** | 8 | deadlock-detection, non-functional-requirements, workflow-checkpoints, frontend-developer-details, runtime-supervisor-details, specification-keeper-details, ai-penetration-tester-details, ai-code-review-patterns |

---

## 13. 配置体系

### 13.1 配置文件层级

| 文件 | 职责 | 优先级 |
|------|------|--------|
| `SKILL.md` (frontmatter) | 技能元数据、触发条件、命令列表 | 最高 |
| `.skill-config.yaml` | 运行时配置（Token/降级/日志/循环/规划） | 高 |
| `configs/default.yaml` | 默认配置（编排器/门禁/通信/桌面/安全/...） | 中 |

### 13.2 .skill-config.yaml 关键配置

| 配置段 | 关键参数 |
|--------|----------|
| `token_budget` | default: 100000, warning: 0.8, compression: 0.8, block: 1.0 |
| `on_demand_loading` | enabled: true, strategy: lazy, preload: [karpathy, quality-gates, agent-registry] |
| `knowledge_service` | host: 127.0.0.1, port: 8765, auth_mode: optional |
| `logging` | level: INFO, dir: .skill-logs |
| `degradation` | L1(0.8), L2(0.95), L3(1.0), recovery: 0.6 |
| `planning_files` | two_action_rule: enabled, three_strike_protocol: enabled |
| `loop` | max_iterations: 50, max_stagnation: 3, completion_promise: "DONE" |

### 13.3 configs/default.yaml 关键配置

| 配置段 | 关键参数 |
|--------|----------|
| `orchestrator` | max_concurrent_agents: 3, lean_mode: false, agent_merge_policy: enabled |
| `quality_gates` | enforcement: strict, coverage: unit 80%, integration 70%, high_risk 90% |
| `communication` | protocol: A2A/v1.1, mcp_compatible: true, encryption: tls1.3 |
| `desktop` | frameworks: [electron, tauri, flutter], code_signing: required |
| `security` | owasp_top10: true, penetration_test: true, sast: true, vulnerability_threshold: P2 |
| `cost_optimization` | model_selection: complexity_based, token_budget: 50000, context_pruning: true |
| `human_collaboration` | loop_mode: autonomous, auto_pass_review_on_confidence: 0.85, security_hard_gates: [production_deploy, secret_key_rotation, db_schema_destructive] |
| `karpathy_guidelines` | compliance_threshold: 0.9, think_before_coding: true, simplicity_first: true |
| `script_execution` | python3/node/pwsh, sandbox: true, shell_script_allowed: false |
| `encoding` | UTF-8, no_bom: true, line_ending: LF, python_coding_declaration: forbidden |
| `token_optimization` | budget: 100000, warn: 0.8, block: 1.0, compression: semantic |
| `review` | confidence_threshold: 80, multi_perspective: true |
| `simplification` | chesterton_fence: true, behavior_equivalence: true |
| `webapp_testing` | browser: chromium, visual_regression_threshold: 0.001 |

---

## 14. 依赖关系

### 14.1 Agent间严格依赖

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
| Compliance/Bug/History/Comment Reviewer | Subagent Dispatcher | 审查任务分配 |
| Design System Generator | UI Designer + Product Manager | 设计需求 + 产品类型 |
| Knowledge Manager | All Agents | 知识条目输入 |
| Learning Specialist | Knowledge Manager | 知识库就绪 |
| Token Optimizer | Orchestrator | Token预算约束 |
| Quality Monitor | Quality Layer Agents | 质量指标数据 |
| Progress Tracker | Task Coordinator | 任务状态数据 |
| Decision Logger | Orchestrator + System Architect | 决策事件 |

### 14.2 可并行Agent组

| Agent组 | 说明 |
|---------|------|
| Product Manager + Technical Writer | 需求分析可与文档模板准备并行 |
| UI Designer + UX Designer | 设计可并行迭代，通过设计令牌同步 |
| Frontend Developer + Backend Developer | 基于契约开发，可并行 |
| Unit Tester (前端) + Unit Tester (后端) | 不同模块的单元测试可并行 |
| Security Auditor + Compliance Officer | 安全审计与合规检查可并行 |
| Compliance/Bug/History/Comment Reviewer | 子代理审查可并行执行 |
| IPC Specialist + Auto-Update Engineer | 跨平台专项可并行开发 |
| Knowledge/Learning/Token Optimizer | 知识层Agent可并行运作 |
| Quality Monitor + Progress Tracker + Decision Logger | 监控层Agent可并行运作 |

### 14.3 外部依赖

| 依赖 | 用途 | 必需性 |
|------|------|--------|
| Python 3.10+ | 脚本运行时 | 必需 |
| Node.js | JS脚本运行时 | 可选 |
| PowerShell 7+ | PS1脚本运行时 | 可选(桌面构建) |
| FastAPI | 知识库服务HTTP层 | 可选(知识库服务) |
| SQLite | 知识库结构化存储 | 可选(知识库服务) |
| Chroma | 知识库向量检索 | 可选(知识库服务) |
| PyYAML | YAML配置解析 | 必需 |
| Playwright | E2E测试 | 可选(测试) |
| @axe-core/playwright | 可访问性测试 | 可选(测试) |
| pixelmatch | 视觉回归测试 | 可选(测试) |

---

## 15. 功能业务与调用链

### 15.1 全生命周期开发调用链

```
用户输入 → SKILL.md触发匹配 → 命令解析 → 工作流选择 → Agent调度 → 质量门禁 → 产出交付
```

详细调用链：

```
1. 用户触发（命令/自然语言）
   ↓
2. SKILL.md frontmatter 匹配触发条件
   ↓
3. 命令文件加载（commands/xxx.md）
   ↓
4. 工作流选择（根据项目规模: full/medium/fast）
   ↓
5. Orchestrator 接管
   ├── 平台检测（Web/Desktop/Flutter）
   ├── 精简模式判断（文件<50?）
   ├── Agent合并策略应用
   └── 任务分解与调度
   ↓
6. Phase 0-8 顺序执行
   ├── 每个Phase: 加载参考文档 → Agent执行 → 质量门禁检查
   ├── 门禁通过 → 下一Phase
   ├── 门禁失败 → 修复 → 重试（最多3次）
   └── 3次失败 → 3-Strike Protocol → 升级/重启
   ↓
7. 知识库交互
   ├── 任务开始: 检索知识库 → 注入上下文
   ├── 任务执行: 经验模式匹配
   └── 任务完成: 沉淀经验 → 知识库更新
   ↓
8. 产出交付 + 完成承诺"DONE"
```

### 15.2 核心业务场景调用链

#### 场景1：新项目从零开发

```
/init → Orchestrator → 平台检测 → 项目初始化
  → /brainstorm → Brainstorming Facilitator → 6阶段需求探索
  → /plan → System Architect → 架构设计
  → /spec → Product Manager → 规格编写
  → /design → UI/UX Designer → 设计系统
  → /implement → Developer Agents → TDD实现
  → /test → Tester Agents → 测试验证
  → /review → Code Reviewer + 5子代理 → 代码审查
  → /accept → QA Engineer → 验收确认
  → /deploy → CI/CD Specialist → 部署发布
```

#### 场景2：代码审查

```
/review → Code Reviewer
  ├── Subagent Dispatcher 调度5个子代理
  │   ├── Compliance Reviewer → 编码规范合规性
  │   ├── Bug Scanner → Bug模式扫描
  │   ├── History Analyzer → 变更历史分析
  │   ├── Comment Verifier → 注释准确性验证
  │   └── Specification Keeper → 规格一致性
  ├── confidence-scorer.py → 置信度评分
  ├── review-aggregator.py → 结果聚合
  └── MULTI-PERSPECTIVE-COVERAGE 门禁检查
```

#### 场景3：安全审计

```
/audit → Security Auditor + Penetration Tester
  ├── Security Auditor → OWASP Top 10 检查
  │   ├── script-security-scanner.py → 脚本安全扫描
  │   ├── dependency-scan.py → 依赖漏洞扫描
  │   └── agentic-security-scanner.py → Agentic安全扫描
  ├── AI Penetration Tester → 6-Agent协作渗透测试
  │   ├── Security Auditor → 攻击面分析
  │   ├── Penetration Tester → 漏洞利用验证
  │   ├── Compliance Officer → 合规检查
  │   ├── AI Pentest → AI驱动测试
  │   ├── Bug Scanner → 缺陷扫描
  │   └── QA Engineer → 质量验证
  └── GATE-012 + AI-PENTEST + AGENTIC-SECURITY 门禁
```

#### 场景4：桌面应用构建

```
/build-desktop → Build-Release Engineer
  ├── Desktop Developer → 桌面端代码
  ├── IPC Specialist → IPC契约验证
  ├── Auto-Update Engineer → 自动更新机制
  ├── build-desktop.ps1 → 构建执行
  ├── sign-desktop.ps1 → 代码签名
  ├── verify-auto-update.ps1 → 更新验证
  └── DESKTOP-BUILD/SIGN/UPDATE/CROSS + IPC-CONTRACT 门禁
```

#### 场景5：自主迭代循环

```
/loop → Orchestrator
  ├── Loop Enforcement 启动
  ├── 循环执行:
  │   ├── 任务分解 → Agent调度 → 执行 → 门禁检查
  │   ├── 完成承诺检查 → "DONE"?
  │   ├── 停滞检测 → max_stagnation: 3
  │   └── Token预算检查 → loop-guard.py
  ├── loop-guard.py → 循环保护
  ├── completion-verifier.py → 完成验证
  └── LOOP-COMPLETION + ITERATION-BUDGET 门禁
```

### 15.3 通信协议调用链

```
Agent A → A2A/v1.1 Protocol → Agent B
  ├── 消息格式: JSON
  ├── 加密: TLS 1.3
  ├── 超时: 30秒
  └── MCP兼容: true (MCP spec 2025-03-26)
```

---

## 16. 逻辑链全景

### 16.1 核心决策逻辑链

```
用户输入
  │
  ├── 是否匹配触发条件？ ──否──→ 不触发技能
  │   ├── 匹配phrases/keywords？
  │   └── 不在not_for排除列表？
  │
  ├── 是 → 加载SKILL.md
  │   │
  │   ├── 解析命令
  │   │   ├── 已知命令 → 加载commands/xxx.md
  │   │   └── 自然语言 → Orchestrator推断意图
  │   │
  │   ├── 选择工作流
  │   │   ├── 项目规模大 → sdd-tdd-full
  │   │   ├── 项目规模中 → sdd-tdd-medium
  │   │   └── 项目规模小 → sdd-tdd-fast
  │   │
  │   └── 平台检测
  │       ├── explicit_declaration → 使用显式声明
  │       ├── dependency_analysis → 依赖分析
  │       ├── structure_analysis → 结构分析
  │       └── default_web → 默认Web
  │
  └── 执行Phase 0-8
      │
      ├── 每Phase:
      │   ├── 加载参考文档（按需）
      │   ├── 检索知识库 → 注入上下文
      │   ├── Agent调度执行
      │   ├── 质量门禁检查
      │   │   ├── 通过 → 下一Phase
      │   │   ├── 失败 → 修复 → 重试（≤3次）
      │   │   └── 3次失败 → 3-Strike Protocol
      │   │       ├── L1技术仲裁
      │   │       ├── L2策略ADR
      │   │       └── L3安全人工
      │   └── Token预算检查
      │       ├── <80% → 正常执行
      │       ├── 80%-95% → L1降级（压缩上下文）
      │       ├── 95%-100% → L2降级（减少Agent）
      │       └── 100% → L3降级（最小Agent集）
      │
      └── 完成承诺"DONE"
          ├── 沉淀经验 → 知识库
          ├── 归档规划文件
          └── 清理临时脚本
```

### 16.2 Token优化逻辑链

```
任务开始
  │
  ├── Token预算分配
  │   ├── Phase 0: 10000
  │   ├── Phase 1: 15000
  │   ├── Phase 2: 20000
  │   ├── Phase 3: 10000
  │   ├── Phase 4: 30000
  │   ├── Phase 5: 15000
  │   ├── Phase 6: 8000
  │   ├── Phase 7: 12000
  │   └── Phase 8: 10000
  │
  ├── Token使用监控
  │   ├── token-budget-guard.py 实时监控
  │   └── token-dashboard.py 可视化
  │
  ├── 压缩策略
  │   ├── Level 1 (60%): lossless（无损压缩）
  │   ├── Level 2 (80%): semantic（语义压缩）
  │   └── Level 3 (95%): selective_discard（选择性丢弃）
  │
  └── 按需加载
      ├── 预加载: karpathy-guidelines, quality-gates, agent-registry
      ├── Phase转换: 加载对应参考文档
      └── LRU缓存: cache_size=5, max_lines=300
```

### 16.3 质量门禁执行逻辑链

```
Phase执行完成
  │
  ├── 收集门禁检查项
  │   ├── 自动化门禁 → 运行对应脚本
  │   └── 人工门禁 → 请求人工确认
  │
  ├── 门禁结果判定
  │   ├── BLOCK → 阻断，必须修复
  │   ├── WARN → 警告，可继续
  │   └── INFO → 记录
  │
  ├── BLOCK门禁处理
  │   ├── 自动修复尝试（≤3次）
  │   ├── 修复成功 → 重新检查
  │   └── 修复失败 → 3-Strike Protocol
  │
  └── 门禁绕过
      ├── bypass_requires_approval: true
      └── 需人工审批
```

### 16.4 知识库交互逻辑链

```
任务开始
  │
  ├── 知识检索
  │   ├── 混合检索引擎
  │   │   ├── SQLite FTS5 → 关键词检索
  │   │   ├── Chroma → 语义检索
  │   │   └── RRF融合 → 排序结果
  │   ├── Top-K: 5
  │   └── 注入上下文
  │
  ├── 知识写入
  │   ├── Agent产出 → MCP Tool / REST API
  │   ├── 服务编排层 → 同步更新
  │   │   ├── SQLite (结构化+FTS)
  │   │   └── Chroma (向量嵌入)
  │   ├── WebSocket → 变更通知
  │   └── 去重引擎 → 精确+语义去重
  │
  └── 经验沉淀
      ├── Learning Specialist → 模式识别
      ├── min_confidence: 0.8
      ├── review_required: true
      └── 知识库更新
```

---

## 17. 项目运行方式

### 17.1 技能触发方式

Xuansto Skill作为Trae IDE的技能自动运行，触发方式：

1. **命令触发**：用户输入 `/sprint`, `/plan`, `/implement` 等命令
2. **自然语言触发**：用户输入包含触发短语/关键词的自然语言
3. **自动触发**：系统根据上下文自动匹配技能描述

### 17.2 知识库服务启动

```bash
# 启动知识库服务（可选）
python scripts/knowledge-server.py --port 8765

# 或使用模块化入口
python -m scripts.knowledge_server.main --port 8765
```

### 17.3 脚本执行

```bash
# Python脚本
python3 scripts/token-budget-guard.py
python3 scripts/check-encoding.py --path ./src
python3 scripts/coverage-check.py --test-dir ./tests

# Node.js脚本
node scripts/accessibility-test.js --url http://localhost:3000
node scripts/visual-regression.js --baseline ./screenshots

# PowerShell脚本（桌面构建）
pwsh scripts/build-desktop.ps1 -Platform win -Framework electron
pwsh scripts/sign-desktop.ps1 -Config ./desktop-build-config.yaml
```

### 17.4 验证工具

```bash
# Agent结构验证
python3 scripts/verification/agent-structure-check.py

# 命令-Agent映射验证
python3 scripts/verification/cmd-agent-check.py

# 工作流门禁一致性验证
python3 scripts/verification/wf-gate-check.py

# SKILL.md结构验证
python3 scripts/skill-md-validator.py

# 技能集成测试
python3 scripts/skill-test.py
```

### 17.5 知识库管理

```bash
# 知识库迁移
python3 scripts/kb-migrate.py --source ./old-kb --target .knowledge

# 知识索引构建
python3 scripts/knowledge-index-builder.py --dir .knowledge

# 知识库服务测试
python3 scripts/knowledge-server-tests.py
```

---

## 18. 版本演进

| 版本 | 日期 | 核心变更 |
|------|------|----------|
| **v1.0.0** | 2026-04-17 | 初始版本：41 Agent/11层/9 Phase/35门禁/17命令 |
| **v1.6.0** | 2026-04-28 | 跨平台桌面支持：+6桌面Agent/+5桌面门禁/Phase 0+8 |
| **v1.7.0** | 2026-04-29 | 知识库服务化：SQLite+Chroma双引擎/REST API/MCP Tool |
| **v1.8.0** | 2026-05-01 | Token优化体系：超精简SKILL.md/按需加载/Token预算门禁 |
| **v1.9.0** | 2026-05-02 | 知识库增强：WebSocket/版本回滚/三级降级/安全过滤/限流 |
| **v1.9.1** | 2026-05-03 | Bug修复：YAML导入/Token阈值/Agent格式统一 |
| **v1.9.2** | 2026-05-03 | 安全合规：沙箱合规/三级降级/故障恢复 |
| **v1.9.3** | 2026-05-03 | Flutter桌面：+Flutter工作流/指南/模板 |
| **v1.10.0** | 2026-05-04 | 模块化重构：knowledge_server包/脚本修复 |
| **v2.0.0** | 2026-05-04 | 数据完整性：增量同步/双向同步/生命周期管理 |
| **v3.0.0** | 2026-05-05 | 七大开源Skill整合：+7 Agent/+6命令/+16门禁/+3工作流 |
| **v3.1.0** | 2026-05-05 | 知识+监控层：+9 Agent(知识3/监控3/跨平台2/编排1) |
| **v3.2.0** | 2026-05-06 | 整合优化：版本统一/废弃脚本替换/参考文档补全 |
| **v4.0.0** | 2026-05-06 | 命令扩展：+4命令(/build/init/status/rollback)/+4门禁 |
| **v4.1.0** | 当前 | 持续优化：门禁数54/参考索引完善 |

---

## 19. 完整性审查

### 19.1 组件完整性矩阵

| 组件 | 声明数量 | 实际数量 | 状态 |
|------|----------|----------|------|
| Agent | 57 | 57 | ✅ 完整 |
| 命令 | 27 | 27 | ✅ 完整 |
| 工作流(.md) | 15 | 15 | ✅ 完整 |
| 工作流(.yaml) | 15 | 15 | ✅ 完整 |
| 质量门禁 | 54 | 54 | ✅ 完整 |
| 脚本 | 49 | 49 | ✅ 完整 |
| 参考文档 | 66+ | 66+ | ✅ 完整 |
| 模板 | 19 | 19 | ✅ 完整 |

### 19.2 Agent层完整性

| 层级 | 声明 | 实际目录 | 状态 |
|------|------|----------|------|
| 编排层 | 3 | orchestrator/(3) | ✅ |
| 产品层 | 4 | product/(4) | ✅ |
| 设计层 | 4 | design/(4) | ✅ |
| 工程层 | 6 | engineering/(6) | ✅ |
| 跨平台层 | 5 | cross-platform/(5) | ✅ |
| 数据层 | 3 | database/(3) | ✅ |
| 测试层 | 10 | testing/(10) | ✅ |
| 安全层 | 3 | security/(3) | ✅ |
| 运维层 | 4 | devops/(4) | ✅ |
| 质量层 | 7 | quality/(7) | ✅ |
| 文档层 | 2 | documentation/(2) | ✅ |
| 知识层 | 3 | knowledge/(3) | ✅ |
| 监控层 | 3 | monitoring/(3) | ✅ |

### 19.3 关键规则合规

| 规则 | 实现 | 状态 |
|------|------|------|
| 2-Action Research | .skill-config.yaml + planning_files.two_action_rule | ✅ |
| 3-Strike Error | .skill-config.yaml + planning_files.three_strike_protocol | ✅ |
| Chesterton's Fence | configs/default.yaml + simplification.chesterton_fence | ✅ |
| Loop Enforcement | .skill-config.yaml + loop.* 配置 | ✅ |
| Confidence≥80 | configs/default.yaml + review.confidence_threshold | ✅ |
| 三级仲裁 | SKILL.md声明 + Orchestrator定义 | ✅ |
| UTF-8无BOM+LF | configs/default.yaml + encoding.* + check-encoding.py | ✅ |
| Python优先 | configs/default.yaml + script_execution.python_runtime | ✅ |
| 禁止Shell(.sh) | configs/default.yaml + script_execution.shell_script_allowed: false | ✅ |
| 五步闭环 | script-standards.md + Agent定义10.5节 | ✅ |
| 知识库强制工作流 | knowledge_layer.* 配置 + knowledge_server/ | ✅ |
| Token预算门禁 | token_budget.* + token-budget-guard.py | ✅ |
| 按需加载 | on_demand_loading.* 配置 | ✅ |
| 精简模式 | orchestrator.lean_mode + agent_merge_policy | ✅ |

---

> 本文档基于 xuansto-skill v4.1.0 源码分析生成，涵盖项目整体架构、模块职责、Agent体系、命令系统、工作流、质量门禁、知识库服务、脚本体系、配置体系、依赖关系、功能业务调用链及逻辑链全景。
