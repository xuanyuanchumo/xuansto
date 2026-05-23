---
name: xuansto-skill
version: 5.0.0
deprecated: true
migrate_to: xuansto-skill-v2
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

> ⛔ **ARCHIVED — No longer maintained**: This skill (xuansto-skill v5) is archived. All development has moved to `xuansto-skill-v2` (v8.0.0) + `xuansto-mcp-server` (v5.0.0).
>
> **Migration Path**: Replace `xuansto-skill` with `xuansto-skill-v2` in `.trae/skills/`. The v2 skill provides full backward compatibility via its 31-command routing table and 57-agent registry. See migration guide in `docs/plan/v-comparison.md`.

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

| 用户意图 | 命令 | 工作流 | MCP工具调用链 | 降级策略 |
|---------|------|--------|-------------|---------|
| 从零开始新项目 | /init → /brainstorm | brainstorming-workflow | skill_analyze → knowledge_search(retrieve) → workflow_dispatch(start) | 知识检索: ChromaDB→SQLite FTS→关键词 |
| 澄清需求/做需求分析 | /clarify | brainstorming-workflow | knowledge_search(retrieve) → workflow_dispatch(start) → quality_gate_check(BRAINSTORM-COMPLETE) | 知识检索→降级链；门禁→内嵌检查 |
| 规划架构/技术选型 | /plan | sdd-tdd-full | skill_analyze → knowledge_search(retrieve) → workflow_dispatch(start) | 项目分析→基础扫描；知识检索→降级链 |
| 写规格文档 | /spec | sdd-tdd-full | workflow_dispatch(start) → quality_gate_check(phase=2) → knowledge_search(retrieve) | 门禁失败→返回修复建议；知识检索→默认模板 |
| 设计UI/设计系统 | /design, /design-system | ui-ux-workflow | quality_gate_check(DESIGN-SYSTEM-COMPLETE, DESIGN-REVIEW) → knowledge_search(retrieve) → workflow_dispatch(start) | 设计门禁→内嵌检查；知识检索→降级链 |
| 写代码/实现功能 | /implement | sdd-tdd-full | workflow_dispatch(phase=current) → quality_gate_check(phase=3) → hook_manage(list) → knowledge_search(retrieve) | 门禁失败→阻止实现+修复建议；Hook拦截→security-block |
| 跑测试 | /test | webapp-testing-workflow | quality_gate_check(TEST-PASS) → workflow_dispatch(phase=advance) | 测试门禁FAIL→返回具体失败文件和建议 |
| 代码审查 | /review | subagent-driven-workflow | quality_gate_check(SUBAGENT-REVIEW, REVIEW-CONFIDENCE) → security_scan(medium) → code_simplify(recent) | 安全扫描→内嵌扫描降级；代码简化→内嵌简化降级 |
| 修Bug | /fix | bug-fix | session_manage(track) → quality_gate_check(TEST-PASS) → hook_manage(list) | 会话追踪失败→内存临时状态；门禁→增量缓存 |
| 安全审计/渗透测试 | /audit | security-audit | security_scan(full, low) → quality_gate_check(AI-PENTEST) → spec_drift_detect() | 安全扫描→内嵌agentic_scan+dependency_scan；渗透测试→内嵌检查 |
| 验收/确认交付 | /accept | acceptance | quality_gate_check(phase=6) → workflow_dispatch(phase=advance) | 门禁检查→增量缓存；Phase推进→门禁校验后推进 |
| 部署上线 | /deploy | inline | quality_gate_check(phase=6) → server_health() → workflow_dispatch(phase=advance) | 健康检查→基础状态返回 |
| 桌面应用构建 | /build-desktop | desktop-build-workflow | quality_gate_check(DESKTOP-BUILD, DESKTOP-SIGN, DESKTOP-CROSS) → workflow_dispatch(start) | 桌面门禁→文件存在性检查 |
| 代码简化/重构 | /simplify, /refactor | sdd-tdd-fast/medium | code_simplify(recent) → quality_gate_check(SIMPLIFICATION-BEHAVIOR, CHESTERTON-FENCE) → session_manage(track) | 代码简化→内嵌simplify+dedup；门禁→内嵌检查 |
| 自主循环执行 | /loop | autonomous_loop | workflow_dispatch(start) → session_manage(track) → resource_load_status(status) | 工作流启动→手动Phase推进；资源检查→基础状态 |
| 知识学习 | /learn | — | knowledge_search(retrieve) → knowledge_search(inject) → knowledge_search(precipitate) | ChromaDB→SQLite FTS→关键词检索 |
| 查询Agent | /agent-status | — | agent_status(list) / agent_status(query) | 静态注册表查询 |
| 查询进度 | /status | — | workflow_dispatch(status) → session_manage(restore) → server_health() | 工作流状态→持久化文件读取；会话恢复→最近会话 |
| 回滚 | /rollback | — | session_manage(restore) → workflow_dispatch(abort) | 会话恢复→最近保存点；工作流中止→状态持久化 |
| 冲刺 | /sprint | sdd-tdd-fast | workflow_dispatch(start) → session_manage(track) → resource_load_status(status) | 快速工作流→精简Phase；资源监控→基础状态 |
| 构建项目 | /build | — | quality_gate_check(BUILD-SUCCESS) → server_health() | 构建门禁→内嵌检查；健康检查→基础状态 |

优先级：精确匹配 > 语义匹配 > 更具体命令优先 > 默认/sprint兜底

### 命令详细步骤

#### /init → /brainstorm（从零开始新项目）
1. `skill_analyze(skill_path, depth="full")` → 项目结构分析
2. `knowledge_search(query="项目初始化最佳实践", action="retrieve")` → 检索相关知识
3. `workflow_dispatch(action="start", workflow="brainstorming-workflow")` → 启动工作流
4. 按Phase推进，门禁检查通过后进入下一阶段
- **降级**: 知识检索失败→使用内嵌知识；工作流启动失败→手动Phase推进
- **示例**: 用户说"帮我搭建一个React项目" → 自动检测技术栈 → 启动brainstorming-workflow

#### /clarify（澄清需求/做需求分析）
1. `knowledge_search(query="需求分析模板", action="retrieve")` → 检索需求模板
2. `workflow_dispatch(action="start", workflow="brainstorming-workflow")` → 启动头脑风暴
3. `quality_gate_check(gate_ids=["BRAINSTORM-COMPLETE"])` → 检查需求完成度
- **降级**: 知识检索→降级链；门禁→内嵌检查
- **示例**: 用户说"澄清需求" → 检索模板 → 头脑风暴 → 检查完成度

#### /plan（规划架构/技术选型）
1. `skill_analyze(skill_path, depth="full")` → 项目分析
2. `knowledge_search(query="架构模式", action="retrieve")` → 检索架构参考
3. `workflow_dispatch(action="start", workflow="sdd-tdd-full")` → 启动SDD工作流
- **降级**: 项目分析→基础扫描；知识检索→降级链
- **示例**: 用户说"规划架构" → 分析项目 → 检索参考 → 启动规划

#### /spec（写规格文档）
1. `workflow_dispatch(action="start", workflow="sdd-tdd-full")` → 启动SDD工作流
2. `quality_gate_check(phase="2")` → 检查架构设计门禁
3. `knowledge_search(query="规格文档模板", action="retrieve")` → 检索规格模板
- **降级**: 门禁检查失败→返回修复建议；知识检索失败→使用默认模板
- **示例**: 用户说"先写规格" → 启动sdd-tdd-full → Phase 2规格编写

#### /design, /design-system（设计/设计系统）
1. `quality_gate_check(gate_ids=["DESIGN-SYSTEM-COMPLETE", "DESIGN-REVIEW"])` → 设计门禁
2. `knowledge_search(query="设计系统模板", action="retrieve")` → 检索设计参考
3. `workflow_dispatch(action="start", workflow="ui-ux-workflow")` → 启动设计工作流
- **降级**: 设计门禁→内嵌检查；知识检索→降级链
- **示例**: 用户说"设计系统" → 检查设计完整性 → 检索模板 → 启动工作流

#### /implement（写代码/实现功能）
1. `workflow_dispatch(action="phase", phase_action="current")` → 查询当前Phase
2. `quality_gate_check(phase="3")` → 检查测试先行门禁
3. `hook_manage(action="list")` → 获取当前Hook配置
4. `knowledge_search(query="实现模式", action="retrieve")` → 检索实现参考
- **降级**: 门禁检查失败→阻止实现，返回修复建议；Hook拦截→security-block检查
- **示例**: 用户说"实现用户认证" → 检查测试门禁 → security-block检查 → 实现

#### /test（跑测试）
1. `quality_gate_check(gate_ids=["TEST-PASS"])` → 检查测试门禁
2. `workflow_dispatch(action="phase", phase_action="advance")` → 推进到测试Phase
- **降级**: 测试门禁FAIL→返回具体失败文件和建议
- **示例**: 用户说"跑测试" → 执行TEST-PASS门禁 → 返回覆盖率结果

#### /review（代码审查）
1. `quality_gate_check(gate_ids=["SUBAGENT-REVIEW", "REVIEW-CONFIDENCE"])` → 审查门禁
2. `security_scan(severity_threshold="medium")` → 安全扫描
3. `code_simplify(target, scope="recent")` → 代码简化建议
- **降级**: 安全扫描→内嵌扫描降级；代码简化→内嵌简化降级
- **示例**: 用户说"做个代码审查" → 多门禁并行检查 → 汇总结果

#### /fix（修Bug）
1. `session_manage(action="track", ...)` → 追踪修复状态
2. `quality_gate_check(gate_ids=["TEST-PASS"])` → 确认测试通过
3. `hook_manage(action="list")` → 检查Hook配置
- **降级**: 会话追踪失败→内存临时状态；门禁检查→增量缓存
- **示例**: 用户说"修复登录Bug" → 追踪状态 → 修复 → 验证测试

#### /audit（安全审计/渗透测试）
1. `security_scan(scan_type="full", severity_threshold="low")` → 全面安全扫描
2. `quality_gate_check(gate_ids=["AI-PENTEST"])` → AI渗透测试门禁
3. `spec_drift_detect()` → 规格漂移检测
- **降级**: 安全扫描→内嵌agentic_scan+dependency_scan；渗透测试→内嵌检查
- **示例**: 用户说"安全审计" → full扫描+渗透测试 → 汇总漏洞报告

#### /accept（验收确认）
1. `quality_gate_check(phase="6")` → 验收门禁
2. `workflow_dispatch(action="phase", phase_action="advance")` → 推进Phase
- **降级**: 门禁检查→增量缓存；Phase推进→门禁校验后推进
- **示例**: 用户说"验收通过" → 检查验收门禁 → 推进到部署阶段

#### /deploy（部署上线）
1. `quality_gate_check(phase="6")` → 验收门禁检查
2. `server_health()` → 服务器健康检查
3. `workflow_dispatch(action="phase", phase_action="advance")` → 推进到部署Phase
- **降级**: 健康检查→基础状态返回
- **示例**: 用户说"部署上线" → 验收门禁 → 健康检查 → 部署

#### /build-desktop（桌面应用构建）
1. `quality_gate_check(gate_ids=["DESKTOP-BUILD", "DESKTOP-SIGN", "DESKTOP-CROSS"])` → 桌面构建门禁
2. `workflow_dispatch(action="start", workflow="desktop-build-workflow")` → 启动桌面构建工作流
- **降级**: 桌面门禁→文件存在性检查
- **示例**: 用户说"打包桌面应用" → 检查构建配置 → 启动构建流程

#### /simplify, /refactor（代码简化/重构）
1. `code_simplify(target, scope="recent")` → 代码简化分析
2. `quality_gate_check(gate_ids=["SIMPLIFICATION-BEHAVIOR", "CHESTERTON-FENCE"])` → 重构门禁
3. `session_manage(action="track", ...)` → 追踪重构进度
- **降级**: 代码简化→内嵌simplify+dedup；门禁→内嵌检查
- **示例**: 用户说"重构这段代码" → 简化分析 → 门禁检查 → 安全重构

#### /loop（自主循环执行）
1. `workflow_dispatch(action="start", workflow="autonomous_loop")` → 启动自主循环
2. `session_manage(action="track", ...)` → 追踪循环状态
3. `resource_load_status(action="status")` → 检查资源负载
- **降级**: 工作流启动→手动Phase推进；资源检查→基础状态
- **示例**: 用户说"自主循环执行" → 启动循环 → 持续追踪 → 资源监控

#### /learn（知识学习）
1. `knowledge_search(query, action="retrieve")` → 知识检索
2. `knowledge_search(..., action="inject")` → 知识注入
3. `knowledge_search(..., action="precipitate")` → 经验沉淀
- **降级**: ChromaDB→SQLite FTS→关键词检索
- **示例**: 用户说"学习React最佳实践" → 检索→注入→沉淀

#### /agent-status（查询Agent）
1. `agent_status(action="list")` → 列出所有Agent
2. `agent_status(action="query", agent_name="...")` → 查询特定Agent
- **降级**: 静态注册表查询
- **示例**: 用户说"查看Agent状态" → 返回57个Agent列表

#### /status（查询进度）
1. `workflow_dispatch(action="status")` → 工作流状态
2. `session_manage(action="restore")` → 恢复会话状态
3. `server_health()` → 服务器健康
- **降级**: 工作流状态→持久化文件读取；会话恢复→最近会话
- **示例**: 用户说"查看进度" → 返回当前Phase+任务+决策

#### /rollback（回滚）
1. `session_manage(action="restore")` → 恢复上一个会话状态
2. `workflow_dispatch(action="abort")` → 中止当前工作流
- **降级**: 会话恢复→最近保存点；工作流中止→状态持久化
- **示例**: 用户说"回滚" → 恢复上一状态 → 中止当前工作流

#### /sprint（冲刺）
1. `workflow_dispatch(action="start", workflow="sdd-tdd-fast")` → 启动快速工作流
2. `session_manage(action="track", ...)` → 追踪冲刺进度
3. `resource_load_status(action="status")` → 资源监控
- **降级**: 快速工作流→精简Phase；资源监控→基础状态
- **示例**: 用户说"冲刺开发" → 快速工作流 → 追踪进度 → 资源监控

#### /build（构建项目）
1. `quality_gate_check(gate_ids=["BUILD-SUCCESS"])` → 构建门禁
2. `server_health()` → 健康检查
- **降级**: 构建门禁→内嵌检查；健康检查→基础状态
- **示例**: 用户说"构建项目" → 检查构建门禁 → 执行构建

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
