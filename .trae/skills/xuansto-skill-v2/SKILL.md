---
name: xuansto-skill-v2
version: 8.0.0
description: |
  多Agent自主开发编排引擎，通过xuansto-mcp-server的17个MCP原子工具驱动9阶段全生命周期开发流程。务必在以下场景使用本技能：用户要求从零搭建项目、端到端开发功能、TDD/SDD驱动开发、多步骤结构化任务、代码审查+安全审计、规格驱动开发、桌面应用构建，即使用户没有明确说出"多Agent"或"全流程"。支持57个Agent/13层编排、54项质量门禁、31个命令，MCP工具优先不可用时自动降级到脚本调用。
agents_summary: "13 layers / 57 agents (via MCP v2)"
triggers:
  phrases: ["build this properly", "write tests first", "plan my sprint", "review architecture", "implement properly", "build a full feature", "start a new project", "refactor this module", "set up a project", "create a new app", "build from scratch", "develop a feature end-to-end", "plan development", "write specs first", "develop feature", "create project", "add feature", "build app", "code quality", "quality check", "write code", "develop app", "帮我搭建项目", "先写测试再写代码", "做个代码审查", "安全审计一下", "重构这段代码", "帮我规划一下", "完整开发一个功能", "从需求到部署", "多agent协作", "TDD开发", "SDD驱动", "桌面打包", "渗透测试", "规格驱动开发", "搭建项目", "从零开发", "端到端开发", "开发一个功能", "先写规格", "做需求分析", "帮我开发", "写个功能", "添加功能", "新建项目", "创建项目", "代码质量", "质量检查", "写代码", "开发应用", "test-first", "spec-first", "full-stack feature", "multi-step task", "structured workflow", "全流程开发", "规格驱动", "测试先行", "brainstorm", "design system", "simplify code", "loop task", "security review", "vulnerability scan", "penetration test", "桌面应用", "desktop build", "app packaging", "pentest"]
  keywords: [xuansto, SDD, TDD, spec-driven, test-driven, quality-gates, multi-agent, agent-orchestration, autonomous-development, self-evolving-code, desktop-development, desktop-app, cross-platform, Electron, Tauri, Flutter, OWASP, TrinityGuard, penetration-testing, pentest, security-audit, vulnerability-scan, IPC-contracts, token-optimization, spec-drift, 9-phase-workflow, 54-quality-gates, 57-agents, 31-commands, project-setup, build-from-scratch, end-to-end-development, develop-feature, create-project, add-feature, build-app, code-quality, quality-check, write-code, develop-app, 冲刺规划, 需求澄清, 架构规划, 代码审查, 安全审计, 桌面构建, 桌面开发, 桌面应用, 全生命周期, 质量门禁, 自动化开发, 编排器, agent协作, 规格优先, 测试先行, 重构安全网, 全流程开发, 规格驱动, 多agent协作, 桌面打包, 渗透测试, brainstorm, design-system, simplify, loop, 搭建项目, 从零开发, 端到端开发, 先写规格, 需求分析, 帮我开发, 写个功能, 添加功能, 新建项目, 创建项目, 代码质量, 质量检查, 写代码, 开发应用]
  commands: [/sprint, /clarify, /plan, /spec, /design, /implement, /test, /review, /fix, /accept, /deploy, /build-desktop, /release-desktop, /refactor, /audit, /agent-status, /learn, /brainstorm, /execute-plan, /design-system, /simplify, /loop, /cancel-loop, /build, /init, /status, /rollback, /sdd-tdd-medium, /sdd-tdd-fast, /decision, /budget]
  not_for: ["simple single-file edits (add comment, fix typo)", "pure infrastructure/DevOps without code changes", "documentation-only tasks without code", "simple Q&A or explanations", "pure UI/UX design without code development (use ui-ux-pro-max)", "pure data analysis or reporting", "simple config changes (env vars, flags)", "one-line fixes or trivial patches", "simple security scans without code remediation", "documentation-only security reports", "desktop app UI design only without code", "quick hotfixes under 5 lines"]
author: skiller-team
tags: [xuansto, multi-agent, sdd, tdd, orchestration, autonomous-development, quality-gates, cross-platform, desktop, electron, tauri, flutter, trinityguard, pentest, security-audit, brainstorm, design-system, simplify, loop, hooks, model-routing, parallelization, evaluation, mcp]
compatible_mcp_server: ">=4.0.0"
min_version: 1.0.0
license: MIT
---

<!-- PHASE_0_START -->

# Xuansto Skill v8.0.0 (MCP Edition)

> 57 Agents/13层 | 54 Gates | 31 Cmds | 9 Phase | 17 MCP工具驱动

## 命令列表

/sprint /clarify /plan /spec /design /implement /test /review /fix /accept /deploy /build-desktop /release-desktop /refactor /audit /agent-status /learn /brainstorm /execute-plan /design-system /simplify /loop /cancel-loop /build /init /status /rollback /sdd-tdd-medium /sdd-tdd-fast /decision /budget

## MCP依赖

最低兼容: xuansto-mcp-server >= 4.0.0 | API版本: 3.0.0
MCP不可用时自动降级到 scripts/ 目录Python脚本，详见 {{include:constraints.yaml}}

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

| 意图 | 命令 | MCP工具链 | Phase |
|------|------|-----------|-------|
| 从零开始新项目 | /init | skill_analyze, knowledge_search, workflow_dispatch, project_init, decision_log | 0 |
| 头脑风暴/需求探索 | /brainstorm | knowledge_search, workflow_dispatch | 1 |
| 澄清需求 | /clarify | knowledge_search, workflow_dispatch, quality_gate_check | 1 |
| 规划架构 | /plan | skill_analyze, knowledge_search, agent_status, workflow_dispatch, decision_log, token_budget | 2 |
| 写规格文档 | /spec | workflow_dispatch, quality_gate_check, spec_drift_detect | 2 |
| 设计 | /design | quality_gate_check, knowledge_search, workflow_dispatch | 2 |
| 设计系统 | /design-system | quality_gate_check, knowledge_search, workflow_dispatch | 2 |
| 写代码 | /implement | workflow_dispatch, quality_gate_check, hook_manage | 4 |
| 跑测试 | /test | quality_gate_check, workflow_dispatch | 5 |
| 代码审查 | /review | quality_gate_check, security_scan, code_simplify | 5 |
| 安全审计 | /audit | security_scan, quality_gate_check, spec_drift_detect | 5 |
| 修复Bug | /fix | session_manage, quality_gate_check, hook_manage | 4 |
| 验收确认 | /accept | quality_gate_check, workflow_dispatch | 6 |
| 代码简化 | /simplify | code_simplify, quality_gate_check, context_compress | 7 |
| 代码重构 | /refactor | code_simplify, quality_gate_check, context_compress | 7 |
| 部署交付 | /deploy | quality_gate_check, server_health, workflow_dispatch | 8 |
| 构建项目 | /build | skill_analyze, quality_gate_check, server_health | 8 |
| 桌面构建 | /build-desktop | quality_gate_check, skill_analyze, workflow_dispatch | 8 |
| 桌面发布 | /release-desktop | quality_gate_check, workflow_dispatch | 8 |
| 冲刺 | /sprint | workflow_dispatch, session_manage, resource_load_status, token_budget, project_init | 0 |
| 知识学习 | /learn | knowledge_search, knowledge_inject, session_manage | — |
| 执行计划 | /execute-plan | workflow_dispatch, session_manage | — |
| 自主循环 | /loop | workflow_dispatch, session_manage, resource_load_status, token_budget, decision_log | — |
| 取消循环 | /cancel-loop | workflow_dispatch, session_manage | — |
| 查询Agent | /agent-status | agent_status | — |
| 查询进度 | /status | workflow_dispatch, session_manage, server_health | — |
| 回滚 | /rollback | session_manage, workflow_dispatch | — |
| 中等SDD+TDD | /sdd-tdd-medium | skill_analyze, workflow_dispatch, resource_load_status | 0 |
| 快速SDD+TDD | /sdd-tdd-fast | workflow_dispatch, resource_load_status | 1 |
| 决策记录 | /decision | decision_log | — |
| Token预算 | /budget | token_budget, resource_load_status | — |

## 核心Agent索引（编排+产品+工程层）

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

## 完整命令路由表

{{include:commands/routes.yaml}}

## 完整Agent注册表

{{include:agents/registry.yaml}}

## 外部参考文件

### 配置文件（{{include:}}内联加载）

| 文件 | 内容 |
|------|------|
| {{include:triggers.yaml}} | 触发条件完整定义 |
| {{include:constraints.yaml}} | 核心约束与降级规则 |
| {{include:commands/routes.yaml}} | 完整命令路由表(含降级策略) |
| {{include:agents/registry.yaml}} | 完整Agent角色索引(13层57个) |

### 核心工作流参考（P0 — Phase 0+加载）

| 文件 | 内容 |
|------|------|
| references/mcp-tools.md | 17个MCP工具完整参数与返回值 |
| references/workflow-phases.md | 9阶段工作流目标、步骤、门禁和命令路由详情 |
| references/quality-gates.md | 54项质量门禁详细定义与判定标准 |
| references/agent-registry.md | 完整Agent注册表(57个Agent/13层)与角色详情 |
| references/progressive-loading.md | 渐进式加载策略、Phase映射与资源预算 |

### 集成与基础设施参考（P1 — Phase 2+加载）

| 文件 | 内容 |
|------|------|
| references/mcp-integration-strategy.md | MCP集成策略：上下文预算、懒加载、降级链、健康检查 |
| references/session-persistence.md | 会话持久化、状态恢复与跨会话连续性 |
| references/token-optimization.md | Token优化策略、上下文压缩与预算管理 |
| references/hook-system.md | Hook系统完整定义：三级配置与事件触发 |
| references/model-routing.md | 模型路由规则：fast/standard/deep分配策略 |

### 工作流与质量参考（P1 — Phase 2+加载）

| 文件 | 内容 |
|------|------|
| references/workflow-checkpoints.md | 工作流检查点、Phase转换规则与回退策略 |
| references/spec-drift-handling.md | 规格偏差检测、处理策略与对齐流程 |
| references/agent-lifecycle.md | Agent生命周期管理：激活、协作、降级与回收 |
| references/knowledge-workflow-details.md | 知识工作流：检索、注入、沉淀与跨分支同步 |
| references/collaboration-modes.md | 协作模式定义：人机协作断点与决策仲裁 |
| references/iteration-scheduling.md | 智能迭代调度：优先级矩阵、增量验证与收敛判定 |

### 并行与优化参考（P2 — Phase 3+加载）

| 文件 | 内容 |
|------|------|
| references/parallelization-strategy.md | 并行化策略：Git Worktree、Fork对话与冲突解决 |
| references/concurrency-standards.md | 并发编码标准：线程安全、锁策略与竞态防护 |

## MCP工具摘要

| 工具 | 功能 | 关键参数 |
|------|------|----------|
| skill_analyze | 项目结构分析 | skill_path, depth |
| knowledge_search | 三层知识库检索 | action, query, top_k, search_type |
| quality_gate_check | 54项质量门禁 | gate_ids, phase, project_path |
| spec_drift_detect | 规格偏差检测 | spec_dir, src_dir |
| security_scan | OWASP+依赖扫描 | target, severity_threshold |
| code_simplify | 代码简化分析 | target, scope, include_dedup |
| session_manage | 会话状态管理 | action, completed_tasks, decisions |
| workflow_dispatch | 工作流调度 | action, workflow, project_path |
| agent_status | Agent状态查询 | action, phase, agent_name |
| hook_manage | Hook管理 | action, profile, hook_name |
| resource_load_status | 渐进式加载状态 | action, phase, resource_ids |
| context_compress | 上下文压缩 | content, strategy, target_tokens |
| server_health | 服务器健康检查 | — |
| decision_log | 决策日志管理 | action, title, decision |
| token_budget | Token预算管理 | action, total_budget |
| knowledge_inject | 知识注入到上下文 | action, content, scope |
| project_init | 项目初始化 | action, name, stack |

<!-- PHASE_2_END -->

<!-- PHASE_3_START -->

## Hook系统说明

三级配置: minimal(仅security-block) → standard(+encoding-check, token-guard) → full(+session-persist, spec-drift-guard, quality-enforce)

关键Hook:
- **PhaseEnter**: Phase转换时触发，执行门禁预检
- **PreCommit**: Git提交前触发，执行编码检查和格式验证
- **PostTest**: 测试完成后触发，执行覆盖率检查和规格偏差检测
- **SecurityBlock**: 安全阻断，检测敏感信息和危险操作

## 模型路由说明

| 路由 | 模型 | 适用场景 |
|------|------|----------|
| fast | 轻量模型 | 简单查询、格式化、快速响应 |
| standard | 标准模型 | 常规开发任务、代码生成、测试编写 |
| deep | 深度模型 | 架构设计、复杂分析、安全审计、决策仲裁 |

路由规则: Orchestrator/System Architect → deep; 编排/产品层核心 → standard; 简单查询 → fast

## 关键规则

2-Action Research | 3-Strike Error | Chesterton's Fence | Loop Enforcement | Confidence≥80 | 三级仲裁(L1技术→L2策略ADR→L3安全人工)
UTF-8无BOM+LF | Python优先 | 业务注释中文 | Git:`<类型>(<范围>): <中文描述>` | 禁止Shell(.sh) | 五步闭环

<!-- PHASE_3_END -->