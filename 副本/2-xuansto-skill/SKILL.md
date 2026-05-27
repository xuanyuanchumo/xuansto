---
name: xuansto-skill
version: 2.0.0
agents_summary: "11 layers / 41 agents / 编排+产品+设计+工程+跨平台+数据+测试+安全+运维+质量+文档"
description: |
  Xuansto Skill - Multi-Agent Autonomous Development Orchestrator | SDD+TDD Fusion | 41 Agents | 9-Phase Workflow | 37 Quality Gates | Web+Desktop(Electron/Tauri/Flutter)
  Proactively trigger for ANY structured, multi-step software development task — even if users don't explicitly ask for spec-driven or test-driven workflows. Trigger when users describe multi-step coding tasks, want proper implementation, or mention any structured development need. Covers: full-lifecycle from requirements→architecture→specs→TDD implementation→testing→security→review→deployment→release. Multi-agent coordination, 37 quality gates, code reviews, refactoring with safety nets, security audits (OWASP/penetration testing), desktop builds (Electron/Tauri/Flutter), cross-platform, code signing, auto-update, IPC contracts, knowledge base, token optimization, spec drift detection, autonomous development.
  Trigger on phrases: "build this properly", "write tests first", "plan my sprint", "review architecture", "implement properly", "build a full feature", "start a new project", "refactor this module", "帮我搭建项目", "先写测试再写代码", "做个代码审查", "安全审计一下", "重构这段代码", "帮我规划一下", "完整开发一个功能", "从需求到部署", "多agent协作", "TDD开发", "SDD驱动", "桌面打包", "渗透测试", "规格驱动开发", "test-first", "spec-first", "full-stack feature", "multi-step task", "structured workflow", "全流程开发", "规格驱动", "测试先行".
  Trigger on keywords: xuansto, SDD, TDD, spec-driven, test-driven, quality gates, multi-agent, agent orchestration, autonomous development, self-evolving code, desktop development, cross-platform, Electron, Tauri, Flutter, OWASP, penetration testing, IPC contracts, token optimization, spec drift, 9-phase workflow, 37 quality gates, 冲刺规划, 需求澄清, 架构规划, 代码审查, 安全审计, 桌面构建, 全生命周期, 质量门禁, 自动化开发, 编排器, agent协作, 规格优先, 测试先行, 重构安全网, 全流程开发, 规格驱动, 多agent协作, 桌面打包, 渗透测试.
  Commands: /sprint /clarify /plan /spec /design /implement /test /review /fix /accept /deploy /build-desktop /release-desktop /refactor /audit /agent-status /learn
  Do NOT trigger for: simple single-file edits (e.g., "add a comment", "fix a typo"), pure infrastructure/DevOps without code, documentation-only without code, simple Q&A, pure UI/UX design without code development (use ui-ux-pro-max instead), pure data analysis, simple config changes, one-line fixes.
author: skiller-team
tags:
  - xuansto
  - multi-agent
  - sdd
  - tdd
  - orchestration
  - autonomous-development
  - quality-gates
  - cross-platform
  - desktop
  - electron
  - tauri
min_version: 1.0.0
license: MIT
---

# Xuansto Skill - 多Agent SDD+TDD 编排器

> 41 Agents | 9-Phase (Phase 0-8) | 37 Quality Gates | Web + Desktop 全生命周期编排

## 不可妥协原则
1. **Spec > Test > Code**：无规格不开发 | 无测试不合并 | 规格变更重审测试 | 测试失败禁提交 | 覆盖率≥80%
2. **Karpathy行为准则**：Think Before Coding | Simplicity First | Surgical Changes | Goal-Driven Execution
3. **增量约束**：分解→实现→测试→重复；连续3次失败→停止→记录反模式→从头重启
4. **脚本规范**：所有文件修改遵循 [script-standards.md](references/script-standards.md) | Python优先 | UTF-8无BOM | 验证后删除脚本 [强制]
5. **跨平台声明**：Web+Desktop(Electron/Tauri/Flutter)全平台支持，平台差异通过UI Adapter和Native Module Agent自动适配

## 九阶段工作流
> 详情：[sdd-tdd-full.md](workflows/sdd-tdd-full.md) | [sdd-tdd-fast.md](workflows/sdd-tdd-fast.md)

| Phase | 名称 | 主导Agent | 参考文件 | 质量门禁 |
|-------|------|-----------|----------|----------|
| 0 | UX/UI Design | UX/UI Designer | [ui-ux-workflow.md](workflows/ui-ux-workflow.md) | DESIGN-REVIEW, DESIGN-TOKENS, DESIGN-VISUAL-REGRESSION, DESIGN-ACCESSIBILITY |
| 1 | 需求澄清 | Product Manager | [sdd-tdd-full.md](workflows/sdd-tdd-full.md) | GATE-001~002 |
| 2 | 架构与规格 | System Architect | [sdd-tdd-full.md](workflows/sdd-tdd-full.md) | GATE-003~004 |
| 3 | 测试设计 | Test Architect | [sdd-tdd-full.md](workflows/sdd-tdd-full.md) | GATE-005~006 |
| 4 | TDD实现 | FE/BE/Desktop Dev + Code Reviewer | [sdd-tdd-full.md](workflows/sdd-tdd-full.md) | GATE-007~009, FILE-ENCODING, COMMENT-LANGUAGE, SCRIPT-SECURITY, SCRIPT-CLEANUP |
| 5 | 全量验证 | QA Engineer + Security + Perf | [sdd-tdd-full.md](workflows/sdd-tdd-full.md) | GATE-010~012, AGENTIC-SECURITY, AI-PENTEST, PERFORMANCE, SPEC-CONSISTENCY, TEST-PASS, VISUAL-REGRESSION, ACCESSIBILITY, TOKEN-BUDGET |
| 6 | 验收 | Product Manager | [acceptance.md](workflows/acceptance.md) | GATE-013~014, INFRA-HEALTH, UX-ACCEPTANCE |
| 7 | 迭代优化 | Orchestrator + Refactoring | [sdd-tdd-full.md](workflows/sdd-tdd-full.md) | GATE-015, DOC-COMPLETENESS |
| 8 | 构建发布(桌面) | Build & Release Engineer | [desktop-build-workflow.md](workflows/desktop-build-workflow.md) | DESKTOP-BUILD, DESKTOP-SIGN, DESKTOP-UPDATE, DESKTOP-CROSS, IPC-CONTRACT |

专项工作流：[UI/UX](workflows/ui-ux-workflow.md) | [跨平台](workflows/cross-platform-workflow.md) | [桌面构建](workflows/desktop-build-workflow.md) | [Flutter桌面](workflows/flutter-desktop-workflow.md) | [安全审计](workflows/security-audit.md) | [AI渗透](workflows/ai-pentest.md) | [性能](workflows/performance-test.md) | [验收](workflows/acceptance.md) | [Bug修复](workflows/bug-fix.md)

## 质量门禁（共37项）
> 完整定义：[quality-gates.md](references/quality-gates.md)

| 级别 | Phase | 门禁数 |
|------|-------|--------|
| 设计 | Phase 0 | 4项 |
| 需求+架构 | Phase 1-3 | 6项 |
| 代码 | Phase 4 | 5项+安全+清理 |
| 测试+安全+性能 | Phase 5 | 10项 |
| 验收+迭代 | Phase 6-7 | 5项 |
| 桌面 | Phase 8 | 4项 |
| Token | 跨阶段 | 1项 |

## Agent角色（41个/11层架构）
> 完整注册：[agent-registry.md](references/agent-registry.md)

编排层→产品(PM/Architect/Writer)→设计(UI/UX/Stylist)→工程(FE/BE/Full-Stack/DB/Mobile/DevOps)→跨平台(Desktop Dev/UI Adapter/Native Module)→数据(Modeler/DBA/Seeder)→测试(Architect+7Tester+QA)→安全(Auditor/Pentester/Compliance)→运维(CI-CD/Build-Release/Monitor/Runtime)→质量(Reviewer/Refactor/Doc Reviewer)→文档(Doc Engineer/Spec Keeper) | **精简模式**：文件<50自动启用，仅激活编排+产品+核心工程+测试+安全

## 协作模式
| 模式 | 场景 | 模式 | 场景 |
|------|------|------|------|
| Auto | 默认智能路由 | 跨平台 | Web+Desktop协同 |
| 串行/并行 | 依赖/独立任务 | Review/Challenge | 审查/对抗决策 |
| 迭代/层级 | 反馈优化/复杂分解 | Consult/Hivecoding | 专家咨询/并行编码 |

**三级仲裁**：Level1(技术→Orchestrator裁决) → Level2(策略→+Architect ADR) → Level3(安全/产品→人工断点)。详情见 [Orchestrator](agents/orchestrator/orchestrator.md)

## 命令一览
| 命令 | 说明 | 命令 | 说明 |
|------|------|------|------|
| `/sprint` | 冲刺规划 | `/clarify` | 需求澄清 |
| `/plan` | 架构规划 | `/spec` | 规格编写 |
| `/design` | UI/UX设计 | `/implement` | TDD实现 |
| `/test` | 测试执行 | `/review` | 代码审查 |
| `/fix` | Bug修复 | `/accept` | 验收确认 |
| `/deploy` | 部署发布 | `/build-desktop` | 桌面构建 |
| `/release-desktop` | 桌面发布 | `/refactor` | 代码重构 |
| `/audit` | 安全审计 | `/agent-status` | 状态监控 |
| `/learn` | 知识学习 | | |

## 编码与脚本规范 [强制]
> 完整：[coding-standards.md](references/coding-standards.md) | [script-standards.md](references/script-standards.md)
**编码**：所有文件 UTF-8 without BOM + LF行尾 | Python禁止 `# -*- coding:` 声明 | 业务注释简体中文 | Git提交 `<类型>(<范围>): <中文描述>`
**脚本**：通用操作用Python(.py) | Web前端用Node.js(.js) | 系统/构建少量使用PowerShell(.ps1) | **禁止Agent本地创建Shell(.sh)脚本** [强制] | 五步闭环：创建→审查→执行→验证→清理 | 验证后必须删除临时脚本

## 知识库（三层+双引擎）
> 架构：[knowledge-base-architecture.md](references/knowledge-base-architecture.md)
通用知识→工作知识→经验知识 | SQLite+Chroma双引擎检索 | 服务：[knowledge-server.py](scripts/knowledge-server.py)（REST API + MCP Tool）

## 参考资源索引
**核心**：[Karpathy Guidelines](references/karpathy-guidelines.md) | [质量门禁](references/quality-gates.md) | [Agent注册](references/agent-registry.md) | [Agent生命周期](references/agent-lifecycle.md) | [非功能需求](references/non-functional-requirements.md) | [脚本规范](references/script-standards.md) | [Token优化](references/token-optimization.md) | [AI渗透测试详情](references/ai-penetration-tester-details.md) | [前端开发详情](references/frontend-developer-details.md) | [运行时监控详情](references/runtime-supervisor-details.md) | [规格守护详情](references/specification-keeper-details.md)
**工程**：[编码规范](references/coding-standards.md) | [测试指南](references/test-guidelines.md) | [数据库](references/database-guidelines.md) | [设计规范](references/design-guidelines.md) | [CI/CD](references/ci-cd-integration.md) | [Git工作流](references/git-workflow.md) | [文档标准](references/documentation-standards.md) | [验收标准](references/acceptance-criteria.md) | [知识库](references/knowledge-base-architecture.md)
**流程**：[工作流检查点](references/workflow-checkpoints.md) | [人机协作](references/human-collaboration.md) | [规格漂移](references/spec-drift-handling.md) | [迭代调度](references/iteration-scheduling.md) | [并发规范](references/concurrency-standards.md) | [死锁检测](references/deadlock-detection.md) | [协作模式](references/collaboration-modes.md)
**安全**：[安全编码](references/security-guidelines.md) | [OWASP Agentic Top10](references/owasp-agentic-top10-2026.md) | [OWASP Top10](references/owasp-top10-2026.md) | [Electron安全](references/electron-security.md)
**桌面**：[桌面开发](references/desktop-dev-guidelines.md) | [Tauri](references/tauri-dev-guidelines.md) | [Flutter桌面](references/flutter-desktop-guidelines.md) | [Flutter规范](references/flutter-standards.md) | [IPC](references/ipc-contracts.md) | [通信](references/a2a-protocol.md) | [MCP](references/mcp-protocol.md)
**知识库**：[API参考](references/kb-api-reference.md)
**工具**：[Token预算门禁](scripts/token-budget-guard.py) | [上下文压缩](scripts/context-compressor.py) | [脚本安全扫描](scripts/script-security-scanner.py) | [基础设施检查](scripts/infra-health-check.py) | [脚本清理检查](scripts/script-cleanup-checker.py) | [覆盖率检查](scripts/coverage-check.py) | [编码检查](scripts/check-encoding.py) | [注释语言检查](scripts/check-comment-lang.py) | [API契约验证](scripts/api-contract-validator.py) | [设计令牌同步](scripts/design-tokens-sync.js) | [视觉回归](scripts/visual-regression.js) | [可访问性测试](scripts/accessibility-test.js) | [性能基准](scripts/performance-benchmark.js) | [IPC契约验证](scripts/ipc-contract-validator.js) | [规格漂移检测](scripts/spec-drift-detector.py) | [Agentic安全扫描](scripts/agentic-security-scanner.py) | [AI渗透测试](scripts/ai-pentest-runner.py) | [文档覆盖率](scripts/documentation-coverage.py) | [UAT执行器](scripts/uat-runner.py) | [桌面构建](scripts/build-desktop.ps1) | [桌面签名](scripts/sign-desktop.ps1) | [自动更新验证](scripts/verify-auto-update.ps1) | [知识库服务](scripts/knowledge-server.py) | [知识库迁移](scripts/kb-migrate.py) | [Skill自检](scripts/skill-test.py) | [依赖扫描](scripts/dependency-scan.py) | [RCA模板](templates/rca-template.md)
**语言**：[Python](references/python-standards.md) | [Go](references/go-standards.md) | [Java](references/java-standards.md) | [Rust](references/rust-standards.md) | [TypeScript/JS](references/typescript-standards.md) | 优先级：项目自定义 > 语言专用 > 通用编码规范