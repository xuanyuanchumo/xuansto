---
name: xuansto-skill
version: 5.0.0
description: |
  Multi-Agent Autonomous Development Orchestrator | SDD+TDD Fusion | 57 Agents | 9-Phase Workflow | 54 Quality Gates | 27 Commands
  Proactively trigger for ANY structured, multi-step software development task that requires planning, testing, implementation, and verification across multiple files or modules. This includes: building features from scratch, TDD/SDD workflows, code reviews with security analysis, refactoring with test safety nets, sprint planning, architecture design, desktop app builds (Electron/Tauri/Flutter), penetration testing, design system generation, and any task requiring multi-agent coordination across 2+ phases.
  Do NOT trigger for: single-file edits (renames, typo fixes, one-line changes), pure UI/UX design without code (use ui-ux-pro-max instead), pure infrastructure/DevOps config without code changes, documentation-only tasks, simple Q&A or code explanations, simple config changes (env vars, flags), trivial patches under 5 lines.
agents_summary: "13 layers / 57 agents"
triggers:
  phrases: ["build this properly", "write tests first", "plan my sprint", "review architecture", "implement properly", "build a full feature", "start a new project", "refactor this module", "set up a project", "create a new app", "build from scratch", "develop a feature end-to-end", "plan development", "write specs first", "帮我搭建项目", "先写测试再写代码", "做个代码审查", "安全审计一下", "重构这段代码", "帮我规划一下", "完整开发一个功能", "从需求到部署", "多agent协作", "TDD开发", "SDD驱动", "桌面打包", "渗透测试", "规格驱动开发", "搭建项目", "从零开发", "端到端开发", "开发一个功能", "先写规格", "做需求分析", "test-first", "spec-first", "full-stack feature", "multi-step task", "structured workflow", "全流程开发", "规格驱动", "测试先行", "brainstorm", "design system", "simplify code", "loop task", "security review", "vulnerability scan", "penetration test", "桌面应用", "desktop build", "app packaging", "pentest"]
  keywords: [xuansto, SDD, TDD, spec-driven, test-driven, quality-gates, multi-agent, agent-orchestration, autonomous-development, self-evolving-code, desktop-development, desktop-app, cross-platform, Electron, Tauri, Flutter, OWASP, TrinityGuard, penetration-testing, pentest, security-audit, vulnerability-scan, IPC-contracts, token-optimization, spec-drift, 9-phase-workflow, 54-quality-gates, 57-agents, 27-commands, project-setup, build-from-scratch, end-to-end-development, 冲刺规划, 需求澄清, 架构规划, 代码审查, 安全审计, 桌面构建, 桌面开发, 桌面应用, 全生命周期, 质量门禁, 自动化开发, 编排器, agent协作, 规格优先, 测试先行, 重构安全网, 全流程开发, 规格驱动, 多agent协作, 桌面打包, 渗透测试, brainstorm, design-system, simplify, loop, 搭建项目, 从零开发, 端到端开发, 先写规格, 需求分析]
  commands: [/sprint, /clarify, /plan, /spec, /design, /implement, /test, /review, /fix, /accept, /deploy, /build-desktop, /release-desktop, /refactor, /audit, /agent-status, /learn, /brainstorm, /execute-plan, /design-system, /simplify, /loop, /cancel-loop, /build, /init, /status, /rollback]
  not_for: ["simple single-file edits (add comment, fix typo)", "pure infrastructure/DevOps without code changes", "documentation-only tasks without code", "simple Q&A or explanations", "pure UI/UX design without code development (use ui-ux-pro-max)", "pure data analysis or reporting", "simple config changes (env vars, flags)", "one-line fixes or trivial patches", "simple security scans without code remediation", "documentation-only security reports", "desktop app UI design only without code", "quick hotfixes under 5 lines"]
author: skiller-team
tags: [xuansto, multi-agent, sdd, tdd, orchestration, autonomous-development, quality-gates, cross-platform, desktop, electron, tauri, flutter, trinityguard, pentest, security-audit, brainstorm, design-system, simplify, loop, hooks, model-routing, parallelization, evaluation]
min_version: 1.0.0
license: MIT
---

# Xuansto Skill v5.0.0

> 57 Agents/13层 | 54 Gates | 27 Cmds | 9 Phase | 15 WF | 49 Scripts | 72+ Refs

## 核心约束

1. **Spec > Test > Code**：先规格再测试最后代码，覆盖率≥80%
2. **Karpathy准则**：Think Before Coding | Simplicity First | Surgical Changes
3. **增量约束**：分解→实现→测试→重复；3-Strike Protocol: 自动修复→换策略→升级处理 → [gate-recovery-details.md](references/gate-recovery-details.md)；知识库强制工作流(Retrieve→Inject→Precipitate+持续学习闭环) → [knowledge-workflow-details.md](references/knowledge-workflow-details.md)
4. **脚本规范**：script-standards.md | Python优先 | UTF-8无BOM+无U+FFFD | 验证后删除临时脚本
5. **跨平台**：Web+Desktop(Electron/Tauri/Flutter)，桌面端需IPC安全+代码签名

## 执行入口

1. **平台检测** — 检查项目依赖和结构，判断 Web/Desktop/Flutter
2. **规模评估** — 统计项目文件数，判断项目规模（大/中/小）
3. **工作流选择** — 根据规模选择 full/medium/fast（见下方）
4. **加载命令+知识检索** — 读取commands/对应.md → 解析任务类型+技术栈 → knowledge_search检索 → 注入Agent上下文(token≤2048) → 完成后沉淀经验
5. **执行Phase 0** — 从初始化/设计阶段开始，按Phase顺序推进

## 工作流Phase概览

| Phase | 名称 | 关键门禁 |
|-------|------|----------|
| 0 | 初始化 | DESIGN-SYSTEM-COMPLETE, ANTI-PATTERN-CHECK, DESIGN-REVIEW/* |
| 1 | 需求分析 | BRAINSTORM-COMPLETE, GATE-001~002 |
| 2 | 架构设计 | PLAN-ATOMIC, GATE-003~004 |
| 3 | 测试先行 | TEST-FIRST |
| 4 | 代码实现 | SUBAGENT-REVIEW, REVIEW-CONFIDENCE, GATE-007(含U+FFFD检测), TEST-PASS, GATE-009, FILE-ENCODING, SCRIPT-* |
| 5 | 测试验证 | PLAYWRIGHT-E2E-PASS, GATE-011(含RENDER-CHECK)~012, AI-PENTEST, SPEC-CONSISTENCY, RENDER-CHECK |
| 6 | 验收确认 | GATE-013~014, INFRA-HEALTH, UX-ACCEPTANCE |
| 7 | 持续重构 | SIMPLIFICATION-BEHAVIOR, CHESTERTON-FENCE, GATE-015 |
| 8 | 部署交付 | DESKTOP-BUILD/SIGN/UPDATE/CROSS, IPC-CONTRACT |
| 跨阶段 | — | ITERATION-BUDGET(含LOOP-COMPLETION), SESSION-RECOVERY(含PLAN-PERSISTENCE), TOKEN-BUDGET, BUILD-SUCCESS, ROLLBACK-SAFETY, INIT-COMPLETE, STATUS-HEALTHY |

## 工作流选择逻辑

| 条件 | 工作流级别 | 说明 |
|------|-----------|------|
| 项目文件>50 或 用户要求完整流程 或 安全关键项目 | **full** | 9阶段完整流程，所有门禁启用，全部Agent参与 |
| 项目文件20-50 或 中等复杂度需求 | **medium** | 合并部分阶段，减少Agent数量，核心门禁保留 |
| 项目文件<20 或 快速迭代/热修复 | **fast** | 最少阶段，仅核心门禁，精简Agent集 |

判断优先级：用户显式指定 > 项目特征自动判断 > 默认 medium

## 命令路由表

| 用户意图 | 命令 | 工作流 |
|---------|------|--------|
| 从零开始新项目 | /init → /brainstorm | brainstorming-workflow |
| 澄清需求/做需求分析 | /clarify | brainstorming-workflow |
| 规划架构/技术选型 | /plan | sdd-tdd-full |
| 写规格文档 | /spec | sdd-tdd-full |
| 设计UI/设计系统 | /design, /design-system | ui-ux-workflow |
| 写代码/实现功能 | /implement | sdd-tdd-full |
| 跑测试 | /test | webapp-testing-workflow |
| 代码审查 | /review | subagent-driven-workflow |
| 修Bug | /fix | bug-fix |
| 安全审计/渗透测试 | /audit | security-audit |
| 验收/确认交付 | /accept | acceptance |
| 部署上线 | /deploy | inline |
| 桌面应用构建 | /build-desktop | desktop-build-workflow |
| 代码简化/重构 | /simplify, /refactor | sdd-tdd-fast/medium |
| 自主循环执行 | /loop | autonomous_loop |

优先级：精确匹配 > 语义匹配 > 更具体命令优先 > 默认/sprint兜底

## Agent角色索引表

| 层级 | # | Agent列表 |
|------|---|-----------|
| 编排 | 3 | Orchestrator, Subagent Dispatcher, Task Coordinator |
| 产品 | 4 | Product Manager, Brainstorming Facilitator, System Architect, Technical Writer |
| 设计 | 4 | Design System Generator, UX Designer, Frontend Stylist, UI Designer |
| 工程 | 6 | Backend/Database/DevOps/Frontend/Fullstack/Mobile Developer |
| 跨平台 | 5 | Desktop Developer, Desktop UI Adapter, Native Module Developer, IPC Specialist, Auto-Update Engineer |
| 数据 | 3 | Data Modeler, Data Seeder, DBA |
| 测试 | 10 | AI Penetration/Desktop/E2E/Integration/Performance/QA/Security/Test Architect/Test Maintainer/Unit Tester |
| 安全 | 3 | Security Auditor, Compliance Officer, Penetration Tester |
| DevOps | 4 | Build-Release Engineer, CI/CD Specialist, Monitor Specialist, Runtime Supervisor |
| 质量 | 7 | Bug Scanner, Code Reviewer, Comment Verifier, Compliance/Doc Reviewer, History Analyzer, Refactoring Specialist |
| 文档 | 2 | Documentation Engineer, Specification Keeper |
| 知识 | 3 | Knowledge Manager, Learning Specialist, Token Optimizer |
| 监控 | 3 | Quality Monitor, Progress Tracker, Decision Logger |

> 完整注册：[agent-registry.md](references/agent-registry.md) | 精简模式：文件<50自动启用

## 外部化详情

- **门禁失败恢复**：3-Strike Protocol: 自动修复→换策略→升级处理 → [gate-recovery-details.md](references/gate-recovery-details.md)
- **知识工作流**：三阶段知识工作流(Retrieve→Inject→Precipitate+持续学习闭环) → [knowledge-workflow-details.md](references/knowledge-workflow-details.md)
- **Token降级**：三级降级(L1减少并行+MCP降级/L2精简模式/L3最小串行) → [token-degradation-details.md](references/token-degradation-details.md)
- **会话持久化**：Stop Hook保存摘要/SessionStart Hook加载上下文 → [session-persistence.md](references/session-persistence.md)

## Hook系统

生命周期Hook在Phase转换、门禁检查、会话边界自动触发，支持pre/post回调链和条件跳过。
核心Hook：PhaseEnter/PhaseExit/GatePass/GateFail/SessionStart/SessionStop。
Hook执行失败不阻塞主流程，记录警告并继续。
支持自定义Hook注册和优先级排序。
→ [hook-system.md](references/hook-system.md)

## 模型路由

根据任务复杂度、Token预算、延迟要求自动选择最优模型。
简单任务→轻量模型，复杂推理→旗舰模型，批量操作→并行轻量。
→ [model-routing.md](references/model-routing.md)

## 并行化策略

Phase内独立子任务自动并行分发，依赖任务串行编排。
支持Agent级并行(多子代理同时执行)和文件级并行(无冲突文件并发写入)。
→ [parallelization-strategy.md](references/parallelization-strategy.md)

## 验证评估

多维度评估框架：功能正确性+性能基准+安全合规+代码质量+用户体验。
每Phase结束生成评估报告，验收Phase汇总决策。
→ [evaluation-framework.md](references/evaluation-framework.md)

## MCP集成

MCP Tool优先→REST API降级→文件系统兜底，三级调用链。
支持knowledge_search/add/update、外部服务集成、工具动态注册。
→ [mcp-integration-strategy.md](references/mcp-integration-strategy.md)

## 引用索引

**设计**(7) **安全**(7) **规范**(6) **协议**(2) **集成**(6) **编码规范**(7) **桌面**(5) **测试**(2) **Agent**(2) **验收**(4) **数据库**(1) **Git**(2) **文档**(2) **知识库**(5) **其他**(8) **脚本**(49) **新增**(6): hook-system.md, model-routing.md, parallelization-strategy.md, evaluation-framework.md, mcp-integration-strategy.md, session-persistence.md

## 关键规则

2-Action Research | 3-Strike Error | Chesterton's Fence | Loop Enforcement | Confidence≥80 | 三级仲裁(L1技术→L2策略ADR→L3安全人工)
UTF-8无BOM+LF | Python优先 | 业务注释中文 | Git:`<类型>(<范围>): <中文描述>` | 禁止Shell(.sh) | 五步闭环
