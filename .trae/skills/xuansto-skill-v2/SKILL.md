---
name: xuansto-skill-v2
version: 9.0.0
description: |
  多Agent自主开发编排引擎，通过xuansto-mcp-server的22个MCP原子工具驱动9阶段全生命周期开发流程。务必在以下场景使用本技能：用户要求从零搭建项目、端到端开发功能、TDD/SDD驱动开发、多步骤结构化任务、代码审查+安全审计、规格驱动开发、桌面应用构建，即使用户没有明确说出"多Agent"或"全流程"。支持57个Agent/13层编排、54项质量门禁、32个命令，MCP工具优先不可用时自动降级到脚本调用。
agents_summary: "13 layers / 57 agents (via MCP v2)"
triggers:
  phrases: ["build this properly", "write tests first", "plan my sprint", "review architecture", "implement properly", "build a full feature", "start a new project", "refactor this module", "set up a project", "create a new app", "build from scratch", "develop a feature end-to-end", "plan development", "write specs first", "develop feature", "create project", "add feature", "build app", "code quality", "quality check", "write code", "develop app", "帮我搭建项目", "先写测试再写代码", "做个代码审查", "安全审计一下", "重构这段代码", "帮我规划一下", "完整开发一个功能", "从需求到部署", "多agent协作", "TDD开发", "SDD驱动", "桌面打包", "渗透测试", "规格驱动开发", "搭建项目", "从零开发", "端到端开发", "开发一个功能", "先写规格", "做需求分析", "帮我开发", "写个功能", "添加功能", "新建项目", "创建项目", "代码质量", "质量检查", "写代码", "开发应用", "test-first", "spec-first", "full-stack feature", "multi-step task", "structured workflow", "全流程开发", "规格驱动", "测试先行", "brainstorm", "design system", "simplify code", "loop task", "security review", "vulnerability scan", "penetration test", "桌面应用", "desktop build", "app packaging", "pentest"]
  keywords: [xuansto, SDD, TDD, spec-driven, test-driven, quality-gates, multi-agent, agent-orchestration, autonomous-development, self-evolving-code, desktop-development, desktop-app, cross-platform, Electron, Tauri, Flutter, OWASP, TrinityGuard, penetration-testing, pentest, security-audit, vulnerability-scan, IPC-contracts, token-optimization, spec-drift, 9-phase-workflow, 54-quality-gates, 57-agents, 32-commands, project-setup, build-from-scratch, end-to-end-development, develop-feature, create-project, add-feature, build-app, code-quality, quality-check, write-code, develop-app, 冲刺规划, 需求澄清, 架构规划, 代码审查, 安全审计, 桌面构建, 桌面开发, 桌面应用, 全生命周期, 质量门禁, 自动化开发, 编排器, agent协作, 规格优先, 测试先行, 重构安全网, 全流程开发, 规格驱动, 多agent协作, 桌面打包, 渗透测试, brainstorm, design-system, simplify, loop, 搭建项目, 从零开发, 端到端开发, 先写规格, 需求分析, 帮我开发, 写个功能, 添加功能, 新建项目, 创建项目, 代码质量, 质量检查, 写代码, 开发应用]
  commands: [/sprint, /clarify, /plan, /spec, /design, /implement, /test, /review, /fix, /accept, /deploy, /build-desktop, /release-desktop, /refactor, /audit, /agent-status, /learn, /brainstorm, /execute-plan, /design-system, /simplify, /loop, /cancel-loop, /build, /init, /status, /help, /rollback, /sdd-tdd-medium, /sdd-tdd-fast, /decision, /budget]
  not_for: ["simple single-file edits (add comment, fix typo)", "pure infrastructure/DevOps without code changes", "documentation-only tasks without code", "simple Q&A or explanations", "pure UI/UX design without code development (use ui-ux-pro-max)", "pure data analysis or reporting", "simple config changes (env vars, flags)", "one-line fixes or trivial patches", "simple security scans without code remediation", "documentation-only security reports", "desktop app UI design only without code", "quick hotfixes under 5 lines"]
author: skiller-team
tags: [xuansto, multi-agent, sdd, tdd, orchestration, autonomous-development, quality-gates, cross-platform, desktop, electron, tauri, flutter, trinityguard, pentest, security-audit, brainstorm, design-system, simplify, loop, hooks, model-routing, parallelization, evaluation, mcp]
compatible_mcp_server: ">=4.0.0"
mcp_server_min_version: "4.0.0"
min_version: 1.0.0
v1_archived: true
license: MIT
---

<!-- PHASE_0_START -->

# Xuansto Skill v8.7.0-dev (MCP Edition)

> 57 Agents/13层 | 54 Gates | 32 Cmds | 9 Phase | 22 MCP工具驱动

## 命令列表

/sprint /clarify /plan /spec /design /implement /test /review /fix /accept /deploy /build-desktop /release-desktop /refactor /audit /agent-status /learn /brainstorm /execute-plan /design-system /simplify /loop /cancel-loop /build /init /status /help /rollback /sdd-tdd-medium /sdd-tdd-fast /decision /budget

## SKELETON阶段可用命令

在SKELETON阶段（PHASE_0），以下基本命令始终可用：

| 命令 | 用途 | 说明 |
|------|------|------|
| /status | 查询进度 | 查看项目当前状态、工作流进度和资源负载 |
| /help | 帮助信息 | 显示当前阶段可用命令列表和使用说明 |
| /budget | Token预算 | 查看和管理Token预算使用情况 |

执行任意非SKELETON命令（如 /init, /sprint）可推进到FUNCTIONAL阶段。

## MCP依赖

最低兼容: xuansto-mcp-server >= 4.0.0 | API版本: 3.0.0
MCP不可用时自动降级到 scripts/ 目录Python脚本，核心约束见 xuansto://config/constraints

## 核心约束

1. **Spec > Test > Code**：先规格再测试最后代码，覆盖率≥80%
2. **Karpathy准则**：Think Before Coding | Simplicity First | Surgical Changes
3. **增量约束**：分解→实现→测试→重复；3-Strike Protocol
4. **脚本规范**：Python优先 | UTF-8无BOM+无U+FFFD | 验证后删除临时脚本
5. **跨平台**：Web+Desktop(Electron/Tauri/Flutter)，桌面端需IPC安全+代码签名

<!-- PHASE_0_END -->

<!-- PHASE_1_START -->

## 执行入口

1. **平台检测** → 检查项目依赖和结构
2. **规模评估** → 统计文件数判断规模
3. **工作流选择** → full/medium/fast
4. **MCP+知识检索** → skill_analyze → knowledge_search → 注入Agent上下文
5. **执行Phase 0** → 按Phase顺序推进

## 工作流Phase概览

| Phase | 名称 | MCP工具 | 关键门禁 |
|-------|------|---------|----------|
| 0 | 初始化 | skill_analyze, workflow_dispatch, agent_status, resource_load_status | DESIGN-SYSTEM-COMPLETE, ANTI-PATTERN-CHECK |
| 1 | 需求分析 | knowledge_search, resource_load_status | BRAINSTORM-COMPLETE, GATE-001~002 |
| 2 | 架构设计 | knowledge_search, resource_load_status | PLAN-ATOMIC, GATE-003~004 |
| 3 | 测试先行 | — | TEST-FIRST |
| 4 | 代码实现 | quality_gate_check, agent_status | GATE-007, TEST-PASS, FILE-ENCODING |
| 5 | 测试验证 | security_scan, spec_drift_detect, agent_status | AI-PENTEST, SPEC-CONSISTENCY |
| 6 | 验收确认 | quality_gate_check | GATE-013~014, UX-ACCEPTANCE |
| 7 | 持续重构 | code_simplify, context_compress | SIMPLIFICATION-BEHAVIOR, GATE-015 |
| 8 | 部署交付 | — | DESKTOP-BUILD/SIGN/UPDATE/CROSS |

## 命令路由表（精简）

| 意图 | 命令 | MCP工具链 | 工作流Phase | 加载阶段 |
|------|------|-----------|-------------|----------|
| 从零开始新项目 | /init | skill_analyze, knowledge_search, workflow_dispatch, project_init, decision_log | 0 | FUNCTIONAL |
| 头脑风暴/需求探索 | /brainstorm | knowledge_search, workflow_dispatch | 1 | FUNCTIONAL |
| 澄清需求 | /clarify | knowledge_search, workflow_dispatch, quality_gate_check | 1 | FUNCTIONAL |
| 规划架构 | /plan | skill_analyze, knowledge_search, agent_status, workflow_dispatch, decision_log, token_budget | 2 | FUNCTIONAL |
| 写规格文档 | /spec | workflow_dispatch, quality_gate_check, spec_drift_detect | 2 | FUNCTIONAL |
| 设计 | /design | quality_gate_check, knowledge_search, workflow_dispatch | 2 | FUNCTIONAL |
| 设计系统 | /design-system | quality_gate_check, knowledge_search, workflow_dispatch | 2 | ENHANCED |
| 写代码 | /implement | workflow_dispatch, quality_gate_check, hook_manage | 4 | ENHANCED |
| 跑测试 | /test | quality_gate_check, workflow_dispatch | 5 | ENHANCED |
| 代码审查 | /review | quality_gate_check, security_scan, code_simplify | 5 | ENHANCED |
| 安全审计 | /audit | security_scan, quality_gate_check, spec_drift_detect | 5 | FULL |
| 修复Bug | /fix | session_manage, quality_gate_check, hook_manage | 4 | ENHANCED |
| 验收确认 | /accept | quality_gate_check, workflow_dispatch | 6 | ENHANCED |
| 代码简化 | /simplify | code_simplify, quality_gate_check, context_compress | 7 | ENHANCED |
| 代码重构 | /refactor | code_simplify, quality_gate_check, context_compress | 7 | ENHANCED |
| 部署交付 | /deploy | quality_gate_check, server_health, workflow_dispatch | 8 | FULL |
| 构建项目 | /build | skill_analyze, quality_gate_check, server_health | 8 | ENHANCED |
| 桌面构建 | /build-desktop | quality_gate_check, skill_analyze, workflow_dispatch | 8 | FULL |
| 桌面发布 | /release-desktop | quality_gate_check, workflow_dispatch | 8 | FULL |
| 冲刺 | /sprint | workflow_dispatch, session_manage, resource_load_status, token_budget, project_init | 0 | FUNCTIONAL |
| 知识学习 | /learn | knowledge_search, knowledge_inject, session_manage | — | FUNCTIONAL |
| 执行计划 | /execute-plan | workflow_dispatch, session_manage | — | FUNCTIONAL |
| 自主循环 | /loop | workflow_dispatch, session_manage, resource_load_status, token_budget, decision_log | — | FULL |
| 取消循环 | /cancel-loop | workflow_dispatch, session_manage | — | FULL |
| 查询Agent | /agent-status | agent_status | — | FUNCTIONAL |
| 查询进度 | /status | workflow_dispatch, session_manage, server_health | 0 | SKELETON |
| 帮助信息 | /help | resource_load_status | 0 | SKELETON |
| 回滚 | /rollback | session_manage, workflow_dispatch | — | FULL |
| 中等SDD+TDD | /sdd-tdd-medium | skill_analyze, workflow_dispatch, resource_load_status | 0 | ENHANCED |
| 快速SDD+TDD | /sdd-tdd-fast | workflow_dispatch, resource_load_status | 1 | ENHANCED |
| 决策记录 | /decision | decision_log | — | ENHANCED |
| Token预算 | /budget | token_budget, resource_load_status | — | SKELETON |

## 核心Agent索引（编排+产品+工程层）

> ⚠️ **DEPRECATED**: Inline agent definitions in SKILL.md are deprecated. Use MCP Resource `xuansto://agents/list` and `xuansto://agents/{name}` for agent discovery and details. The inline table below is kept for backward compatibility only.

| 层级 | Agent | Phase | 模型路由 |
|------|-------|-------|----------|
| 编排 | Orchestrator | 0,1,2 | deep |
| 编排 | Subagent Dispatcher | 0,4,5 | standard |
| 编排 | Task Coordinator | 0,4,5 | standard |
| 产品 | Product Manager | 1,6 | standard |
| 产品 | Brainstorming Facilitator | 1 | standard |
| 产品 | System Architect | 2 | deep |
| 产品 | Technical Writer | 1,6 | standard |
| 工程 | Backend Developer | 4 | standard |
| 工程 | Database Engineer | 4 | standard |
| 工程 | DevOps Engineer | 4,8 | standard |
| 工程 | Frontend Developer | 4 | standard |
| 工程 | Fullstack Engineer | 4 | standard |
| 工程 | Mobile Developer | 4 | standard |

<!-- PHASE_1_END -->

<!-- PHASE_2_START -->

## MCP Resource URI 索引

| 数据 | MCP Resource URI | 加载阶段 |
|------|-----------------|----------|
| 命令路由表 | xuansto://commands/routes | Phase 2+ |
| Agent注册表 | xuansto://agents/registry | Phase 2+ |
| 技能配置 | xuansto://config/skill | Phase 1+ |
| 质量门禁定义 | xuansto://gates/definitions | Phase 2+ |
| 工作流定义 | xuansto://workflows/definitions | Phase 2+ |
| Hook定义 | xuansto://hooks/definitions | Phase 3+ |
| 加载状态 | xuansto://loading/status | Phase 1+ |
| 知识库统计 | xuansto://knowledge/stats | Phase 2+ |
| 核心约束 | xuansto://config/constraints | Phase 0+ |

完整命令路由见 xuansto://commands/routes | 完整Agent注册表(57个/13层)见 xuansto://agents/registry | 核心约束见 xuansto://config/constraints | 质量门禁完整列表见 xuansto://gates/definitions | 工作流阶段定义见 xuansto://workflows/definitions | MCP工具完整参数见 xuansto://config/skill

<!-- PHASE_2_END -->

<!-- PHASE_3_START -->

Hook系统定义见 xuansto://hooks/definitions | 模型路由规则见 xuansto://config/skill | 并行化策略见 xuansto://workflows/definitions

关键规则: 2-Action Research | 3-Strike Error | Chesterton's Fence | Loop Enforcement | Confidence≥80 | 三级仲裁(L1技术→L2策略ADR→L3安全人工) | UTF-8无BOM+LF | Python优先 | 业务注释中文 | Git:`<类型>(<范围>): <中文描述>` | 禁止Shell(.sh) | 五步闭环

<!-- PHASE_3_END -->