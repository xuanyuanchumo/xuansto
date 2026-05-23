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
min_version: 1.0.0
license: MIT
---

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

## 执行入口

1. **平台检测** → 检查项目依赖和结构
2. **规模评估** → 统计文件数判断规模
3. **工作流选择** → full/medium/fast
4. **MCP+知识检索** → skill_analyze → knowledge_search → 注入Agent上下文
5. **执行Phase 0** → 按Phase顺序推进

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

## 外部参考文件

| 文件 | 内容 |
|------|------|
| {{include:triggers.yaml}} | 触发条件完整定义 |
| {{include:constraints.yaml}} | 核心约束与降级规则 |
| {{include:commands/routes.yaml}} | 完整命令路由表(含降级策略) |
| {{include:agents/registry.yaml}} | 完整Agent角色索引(13层57个) |
| references/mcp-tools.md | 17个MCP工具完整参数与返回值 |
| references/workflow-phases.md | 9阶段工作流目标、步骤、门禁和命令路由详情 |

## 关键规则

2-Action Research | 3-Strike Error | Chesterton's Fence | Loop Enforcement | Confidence≥80 | 三级仲裁(L1技术→L2策略ADR→L3安全人工)
UTF-8无BOM+LF | Python优先 | 业务注释中文 | Git:`<类型>(<范围>): <中文描述>` | 禁止Shell(.sh) | 五步闭环
