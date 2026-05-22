---
name: xuansto-skill-v2
version: 7.0.0
description: |
  多Agent自主开发编排引擎，通过xuansto-mcp-server的13个MCP原子工具驱动9阶段全生命周期开发流程。务必在以下场景使用本技能：用户要求从零搭建项目、端到端开发功能、TDD/SDD驱动开发、多步骤结构化任务、代码审查+安全审计、规格驱动开发、桌面应用构建，即使用户没有明确说出"多Agent"或"全流程"。支持57个Agent/13层编排、54项质量门禁、27个命令，MCP工具优先不可用时自动降级到脚本调用。
agents_summary: "13 layers / 57 agents (via MCP v2)"
triggers:
  phrases: ["build this properly", "write tests first", "plan my sprint", "review architecture", "implement properly", "build a full feature", "start a new project", "refactor this module", "set up a project", "create a new app", "build from scratch", "develop a feature end-to-end", "plan development", "write specs first", "帮我搭建项目", "先写测试再写代码", "做个代码审查", "安全审计一下", "重构这段代码", "帮我规划一下", "完整开发一个功能", "从需求到部署", "多agent协作", "TDD开发", "SDD驱动", "桌面打包", "渗透测试", "规格驱动开发", "搭建项目", "从零开发", "端到端开发", "开发一个功能", "先写规格", "做需求分析", "test-first", "spec-first", "full-stack feature", "multi-step task", "structured workflow", "全流程开发", "规格驱动", "测试先行", "brainstorm", "design system", "simplify code", "loop task", "security review", "vulnerability scan", "penetration test", "桌面应用", "desktop build", "app packaging", "pentest"]
  keywords: [xuansto, SDD, TDD, spec-driven, test-driven, quality-gates, multi-agent, agent-orchestration, autonomous-development, self-evolving-code, desktop-development, desktop-app, cross-platform, Electron, Tauri, Flutter, OWASP, TrinityGuard, penetration-testing, pentest, security-audit, vulnerability-scan, IPC-contracts, token-optimization, spec-drift, 9-phase-workflow, 54-quality-gates, 57-agents, 27-commands, project-setup, build-from-scratch, end-to-end-development, 冲刺规划, 需求澄清, 架构规划, 代码审查, 安全审计, 桌面构建, 桌面开发, 桌面应用, 全生命周期, 质量门禁, 自动化开发, 编排器, agent协作, 规格优先, 测试先行, 重构安全网, 全流程开发, 规格驱动, 多agent协作, 桌面打包, 渗透测试, brainstorm, design-system, simplify, loop, 搭建项目, 从零开发, 端到端开发, 先写规格, 需求分析]
  commands: [/sprint, /clarify, /plan, /spec, /design, /implement, /test, /review, /fix, /accept, /deploy, /build-desktop, /release-desktop, /refactor, /audit, /agent-status, /learn, /brainstorm, /execute-plan, /design-system, /simplify, /loop, /cancel-loop, /build, /init, /status, /rollback]
  not_for: ["simple single-file edits (add comment, fix typo)", "pure infrastructure/DevOps without code changes", "documentation-only tasks without code", "simple Q&A or explanations", "pure UI/UX design without code development (use ui-ux-pro-max)", "pure data analysis or reporting", "simple config changes (env vars, flags)", "one-line fixes or trivial patches", "simple security scans without code remediation", "documentation-only security reports", "desktop app UI design only without code", "quick hotfixes under 5 lines"]
author: skiller-team
tags: [xuansto, multi-agent, sdd, tdd, orchestration, autonomous-development, quality-gates, cross-platform, desktop, electron, tauri, flutter, trinityguard, pentest, security-audit, brainstorm, design-system, simplify, loop, hooks, model-routing, parallelization, evaluation, mcp]
min_version: 1.0.0
license: MIT
---

# Xuansto Skill v7.0.0 (MCP Edition)

> 57 Agents/13层 | 54 Gates | 27 Cmds | 9 Phase | 13 MCP工具驱动

## 参考文档（按需加载）

- [MCP工具详细参考](references/mcp-tools.md) — 13个MCP工具的完整参数、返回值和降级链
- [9阶段工作流详细参考](references/workflow-phases.md) — 每个Phase的目标、步骤和门禁详情
- [Agent注册表](#mcp-resource-访问) — 通过 `xuansto://references/agent-registry` 访问57个Agent完整定义

## 核心约束

1. **Spec > Test > Code**：先规格再测试最后代码，覆盖率≥80%
2. **Karpathy准则**：Think Before Coding | Simplicity First | Surgical Changes
3. **增量约束**：分解→实现→测试→重复；3-Strike Protocol: 自动修复→换策略→升级处理
4. **脚本规范**：Python优先 | UTF-8无BOM+无U+FFFD | 验证后删除临时脚本
5. **跨平台**：Web+Desktop(Electron/Tauri/Flutter)，桌面端需IPC安全+代码签名

## MCP Server 依赖

本Skill依赖 xuansto-mcp-server 提供运行时工具支持。

**最低兼容版本**: xuansto-mcp-server >= 3.5.0
**推荐版本**: xuansto-mcp-server 3.5.0
**Skill版本**: xuansto-skill-v2 7.0.0
**API版本**: 1.0.0

当MCP Server不可用时，系统自动降级到 scripts/ 目录下的Python脚本执行。

降级模式功能范围：

| 功能 | 降级可用 | 说明 |
|------|---------|------|
| 项目结构分析 | ✓ | skill_analyze → scripts/skill-test.py --analyze |
| 核心门禁检查 | ✓ | quality_gate_check → scripts/skill-test.py --gate |
| 知识检索(关键词) | ✓ | knowledge_search → scripts/knowledge-server.py --search |
| 语义检索 | ✗ | ChromaDB不可用，仅关键词匹配 |
| 规格漂移检测 | ✓ | spec_drift_detect → scripts/spec-drift-detector.py → 内联漂移检测 |
| 安全扫描 | ✓ | security_scan → scripts/agentic-security-scanner.py → 内联agentic+dependency扫描 |
| 代码简化 | ✓ | code_simplify → scripts/code-simplifier.py → 内联simplify+dedup |
| 会话管理 | ✓ | session_manage → scripts/init-session.py / session-catchup.py / session-persist.py |
| 工作流调度(手动) | ✓ | workflow_dispatch → scripts/project-initializer.py (start) / 内联Phase推进 |
| Agent状态查询 | ✓ | agent_status → 静态注册表查询(agents/目录) / scripts/skill-test.py --agents |
| Hook管理 | ✓ | hook_manage → scripts/check-encoding.py / token-budget-guard.py / session-persist.py / 内联Hook执行 |
| 渐进式加载状态 | ✓ | resource_load_status → 内联状态检查(resource_state.json) |
| 上下文压缩 | ✓ | context_compress → scripts/context-compressor.py |
| 服务器健康检查 | ✓ | server_health → scripts/health-checker.py → 降级状态返回 |

## 渐进式加载披露

本Skill支持渐进式加载披露，按需加载资源并透明披露加载状态与功能可用性，以优化Token消耗。

### 加载阶段

| 阶段 | 触发条件 | 加载内容 | 预估Token |
|------|----------|----------|-----------|
| Phase 0: 骨架 | Skill触发时 | 核心约束+命令概要+Agent索引 | ~2K |
| Phase 1: 功能 | 用户执行命令时 | 命令详细步骤+工作流Phase | ~3K |
| Phase 2: 增强 | 需要参考文档时 | 参考文档+模板+知识库 | ~5K |
| Phase 3: 完整 | 深度分析时 | 全部资源+脚本+披露资源 | ~10K |

### 加载指令

- **按需加载**: 当用户执行特定命令时，读取对应的 commands/[command].md 获取详细步骤
- **参考加载**: 当需要参考文档时，读取 references/ 目录下对应文件
- **资源预加载**: 通过MCP Resource xuansto://loading/status 查询当前加载状态
- **降级策略**: MCP不可用时，直接读取本地文件系统

### 资源优先级

1. **P0-必须**: SKILL.md核心约束、命令路由表、Agent索引表
2. **P1-重要**: 命令详细步骤、工作流Phase定义、MCP工具参数
3. **P2-增强**: 参考文档(quality-gates.md等)、模板文件、知识库
4. **P3-可选**: 示例文档、评估配置、披露资源

### 功能可用性披露

在渐进式加载过程中，系统向用户/Host透明披露当前可用功能范围：

| 加载阶段 | 可用功能 | 不可用功能 |
|----------|----------|------------|
| Phase 0: 骨架 | 命令路由、Agent索引、核心约束 | 命令详细步骤、参考文档、知识检索 |
| Phase 1: 功能 | 命令执行、工作流推进、门禁检查 | 参考文档、Agent详细定义、知识检索 |
| Phase 2: 增强 | 知识检索、参考文档、Agent详细定义 | 完整脚本集、评估配置 |
| Phase 3: 完整 | 全部功能可用 | 无 |

当功能因加载阶段限制不可用时，系统应：
1. 通过 xuansto://loading/status 披露当前可用功能范围
2. 提示用户可通过 resource_load_status(preload) 推进加载
3. 降级到可用功能范围内执行（如知识检索不可用时使用内嵌知识）

## MCP工具调用

本Skill依赖xuansto-mcp-server提供以下13个工具：

| 工具 | 用途 | 调用时机 |
|------|------|----------|
| `skill_analyze` | 项目结构分析 | Phase 0 初始化 |
| `knowledge_search` | 知识库检索 | 每Phase开始前 |
| `quality_gate_check` | 质量门禁检查 | Phase转换时 |
| `spec_drift_detect` | 规格漂移检测 | Phase 5/6 |
| `security_scan` | 安全扫描 | Phase 5/审计命令 |
| `code_simplify` | 代码简化分析 | Phase 7 |
| `session_manage` | 会话状态管理 | Hook触发 |
| `workflow_dispatch` | 工作流调度 | Phase 0 启动工作流 |
| `agent_status` | Agent状态查询 | Agent分配时 |
| `hook_manage` | Hook管理 | Hook触发时 |
| `resource_load_status` | 渐进式加载状态 | Phase转换预加载 |
| `context_compress` | 上下文压缩 | Token预算紧张时 |
| `server_health` | 服务器健康检查 | 启动时/定期检查 |

### MCP调用模式

```
优先: MCP工具调用 (xuansto-mcp-server via stdio)
降级: 直接调用 scripts/ 目录下的Python脚本
```

## MCP Resource 访问

本Skill可通过MCP Resource URI直接读取以下只读数据：

| URI | 描述 |
|-----|------|
| `xuansto://config/skill` | 技能运行时配置(.skill-config.yaml) |
| `xuansto://references/quality-gates` | 54项质量门禁定义 |
| `xuansto://references/agent-registry` | 57个Agent注册表 |
| `xuansto://references/workflow-phases` | 9阶段工作流定义 |
| `xuansto://templates/{name}` | 模板文件(如prd-template) |
| `xuansto://sessions/latest` | 最近会话记录 |
| `xuansto://loading/status` | 渐进式加载状态(当前Phase、已加载资源、进度) |

## 降级模式

当xuansto-mcp-server不可用时，回退到直接调用scripts/目录下的Python脚本：

1. **MCP连接检测**：尝试调用`skill_analyze`，失败则进入降级模式
2. **脚本调用回退**：使用`python scripts/xxx.py --format json`调用
3. **结果格式统一**：降级模式下结果包装为与MCP工具相同的JSON结构

## 执行入口

1. **平台检测** — 检查项目依赖和结构，判断 Web/Desktop/Flutter
2. **规模评估** — 统计项目文件数，判断项目规模（大/中/小）
3. **工作流选择** — 根据规模选择 full/medium/fast
4. **MCP工具调用+知识检索** — 调用`skill_analyze`分析项目 → `knowledge_search`检索 → 注入Agent上下文
5. **执行Phase 0** — 从初始化/设计阶段开始，按Phase顺序推进

## 工作流Phase概览

| Phase | 名称 | MCP工具 | 关键门禁 |
|-------|------|---------|----------|
| 0 | 初始化 | `skill_analyze`, `workflow_dispatch`, `agent_status`, `resource_load_status` | DESIGN-SYSTEM-COMPLETE, ANTI-PATTERN-CHECK |
| 1 | 需求分析 | `knowledge_search`, `resource_load_status` | BRAINSTORM-COMPLETE, GATE-001~002 |
| 2 | 架构设计 | `knowledge_search`, `resource_load_status` | PLAN-ATOMIC, GATE-003~004 |
| 3 | 测试先行 | — | TEST-FIRST |
| 4 | 代码实现 | `quality_gate_check`, `agent_status` | GATE-007, TEST-PASS, FILE-ENCODING |
| 5 | 测试验证 | `security_scan`, `spec_drift_detect`, `agent_status` | AI-PENTEST, SPEC-CONSISTENCY |
| 6 | 验收确认 | `quality_gate_check` | GATE-013~014, UX-ACCEPTANCE |
| 7 | 持续重构 | `code_simplify`, `context_compress` | SIMPLIFICATION-BEHAVIOR, GATE-015 |
| 8 | 部署交付 | — | DESKTOP-BUILD/SIGN/UPDATE/CROSS |

## 命令路由表

| 用户意图 | 命令 | MCP工具调用链 | 降级策略 |
|---------|------|-------------|---------|
| 从零开始新项目 | /init → /brainstorm | skill_analyze → knowledge_search → workflow_dispatch(start) | 知识检索: ChromaDB→SQLite FTS→关键词 |
| 澄清需求 | /clarify | knowledge_search → workflow_dispatch(start) → quality_gate_check(BRAINSTORM-COMPLETE) | 知识检索→降级链；门禁→内嵌检查 |
| 规划架构 | /plan | skill_analyze → knowledge_search → agent_status → workflow_dispatch(start) | 项目分析→基础扫描；知识检索→降级链 |
| 写规格文档 | /spec | workflow_dispatch(start) → quality_gate_check(phase=2) → spec_drift_detect | 门禁失败→返回修复建议；知识检索→默认模板 |
| 写代码 | /implement | workflow_dispatch(current) → quality_gate_check(phase=3) → hook_manage(list) | 门禁失败→阻止实现+修复建议 |
| 跑测试 | /test | quality_gate_check(TEST-PASS) → workflow_dispatch(status) | 测试门禁FAIL→返回具体失败文件和建议 |
| 代码审查 | /review | quality_gate_check(SUBAGENT-REVIEW, REVIEW-CONFIDENCE) → security_scan(medium) → code_simplify(recent) | 安全扫描→内嵌降级；代码简化→内嵌降级 |
| 安全审计 | /audit | security_scan(full, low) → quality_gate_check(AI-PENTEST) → spec_drift_detect | 安全扫描→内嵌agentic+dependency扫描 |
| 代码简化 | /simplify | code_simplify(recent) → quality_gate_check(SIMPLIFICATION-BEHAVIOR, CHESTERTON-FENCE) → context_compress | 代码简化→内嵌simplify+dedup；压缩→脚本降级 |
| 代码重构 | /refactor | code_simplify(recent) → quality_gate_check(SIMPLIFICATION-BEHAVIOR, CHESTERTON-FENCE) → context_compress | 门禁→内嵌检查；压缩→脚本降级 |
| 验收确认 | /accept | quality_gate_check(phase=6) → workflow_dispatch(status) | 门禁检查→增量缓存 |
| 知识学习 | /learn | knowledge_search(retrieve) → knowledge_search(inject) → session_manage(save) | ChromaDB→SQLite FTS→关键词检索 |
| 执行计划 | /execute-plan | workflow_dispatch(start) → session_manage(save) | 工作流启动→手动Phase推进 |
| 取消循环 | /cancel-loop | workflow_dispatch(abort) → session_manage(save) | 工作流中止→状态持久化 |
| 自主循环 | /loop | workflow_dispatch(start) → session_manage(save) → resource_load_status(status) | 工作流→手动Phase推进；资源→基础状态 |
| 查询Agent | /agent-status | agent_status(list) / agent_status(detail) | 静态注册表查询 |
| 查询进度 | /status | workflow_dispatch(status) → session_manage(load) → server_health | 工作流状态→持久化文件读取 |
| 修复Bug | /fix | session_manage(save) → quality_gate_check(TEST-PASS) → hook_manage(list) | 会话追踪→内存临时状态 |
| 部署交付 | /deploy | quality_gate_check(phase=6) → server_health → workflow_dispatch(status) | 健康检查→基础状态返回 |
| 构建项目 | /build | skill_analyze(basic) → quality_gate_check(BUILD-SUCCESS) → server_health | 构建门禁→内嵌检查 |
| 桌面构建 | /build-desktop | quality_gate_check(DESKTOP-BUILD, DESKTOP-SIGN, DESKTOP-CROSS) → skill_analyze(full) → workflow_dispatch(start) | 桌面门禁→文件存在性检查 |
| 桌面发布 | /release-desktop | quality_gate_check(DESKTOP-SIGN, DESKTOP-UPDATE) → workflow_dispatch(start) | 桌面门禁→文件存在性检查 |
| 设计 | /design | quality_gate_check(DESIGN-SYSTEM-COMPLETE, DESIGN-REVIEW) → knowledge_search → workflow_dispatch(start) | 设计门禁→内嵌检查 |
| 设计系统 | /design-system | quality_gate_check(DESIGN-SYSTEM-COMPLETE, DESIGN-REVIEW) → knowledge_search(scope=general) → workflow_dispatch(start) | 知识检索→降级链 |
| 回滚 | /rollback | session_manage(load) → workflow_dispatch(abort) | 会话恢复→最近保存点 |
| 冲刺 | /sprint | workflow_dispatch(start, sdd-tdd-fast) → session_manage(save) → resource_load_status(preload) | 快速工作流→精简Phase |

优先级：精确匹配 > 语义匹配 > 更具体命令优先 > 默认/sprint兜底

### 命令详细步骤

#### /init → /brainstorm（从零开始新项目）
1. `skill_analyze(skill_path, depth="full")` → 项目结构分析
2. `knowledge_search(query="项目初始化最佳实践")` → 检索相关知识
3. `workflow_dispatch(action="start", workflow="brainstorming-workflow")` → 启动工作流
4. 按Phase推进，门禁检查通过后进入下一阶段
- **降级**: 知识检索失败→使用内嵌知识；工作流启动失败→手动Phase推进
- **示例**: 用户说"帮我搭建一个React项目" → 自动检测技术栈 → 启动brainstorming-workflow

#### /clarify（澄清需求/做需求分析）
1. `knowledge_search(query="需求分析模板")` → 检索需求模板
2. `workflow_dispatch(action="start", workflow="brainstorming-workflow")` → 启动头脑风暴
3. `quality_gate_check(gate_ids=["BRAINSTORM-COMPLETE"])` → 检查需求完成度
- **降级**: 知识检索→降级链；门禁→内嵌检查
- **示例**: 用户说"澄清需求" → 检索模板 → 头脑风暴 → 检查完成度

#### /plan（规划架构/技术选型）
1. `skill_analyze(skill_path, depth="full")` → 项目分析
2. `knowledge_search(query="架构模式")` → 检索架构参考
3. `agent_status(action="by_phase", phase=2)` → 查询架构阶段Agent
4. `workflow_dispatch(action="start", workflow="sdd-tdd-full")` → 启动SDD工作流
- **降级**: 项目分析→基础扫描；知识检索→降级链
- **示例**: 用户说"规划架构" → 分析项目 → 检索参考 → 启动规划

#### /spec（写规格文档）
1. `workflow_dispatch(action="start", workflow="sdd-tdd-full")` → 启动SDD工作流
2. `quality_gate_check(phase="2")` → 检查架构设计门禁
3. `spec_drift_detect(spec_dir=".trae/specs", src_dir=".")` → 规格漂移检测
- **降级**: 门禁检查失败→返回修复建议；知识检索失败→使用默认模板
- **示例**: 用户说"先写规格" → 启动sdd-tdd-full → Phase 2规格编写

#### /design, /design-system（设计/设计系统）
1. `quality_gate_check(gate_ids=["DESIGN-SYSTEM-COMPLETE", "DESIGN-REVIEW"])` → 设计门禁
2. `knowledge_search(query="设计系统模板", scope="general")` → 检索设计参考
3. `workflow_dispatch(action="start", workflow="ui-ux-workflow")` → 启动设计工作流
- **降级**: 设计门禁→内嵌检查；知识检索→降级链
- **示例**: 用户说"设计系统" → 检查设计完整性 → 检索模板 → 启动工作流

#### /implement（写代码/实现功能）
1. `workflow_dispatch(action="status")` → 查询当前Phase
2. `quality_gate_check(phase="3")` → 检查测试先行门禁
3. `hook_manage(action="list")` → 获取当前Hook配置
4. `agent_status(action="by_phase", phase=4)` → 查询实现阶段Agent
- **降级**: 门禁检查失败→阻止实现，返回修复建议；Hook拦截→security-block检查
- **示例**: 用户说"实现用户认证" → 检查测试门禁 → security-block检查 → 实现

#### /test（跑测试）
1. `quality_gate_check(gate_ids=["TEST-PASS"])` → 检查测试门禁
2. `workflow_dispatch(action="status")` → 确认当前Phase
- **降级**: 测试门禁FAIL→返回具体失败文件和建议
- **示例**: 用户说"跑测试" → 执行TEST-PASS门禁 → 返回覆盖率结果

#### /review（代码审查）
1. `quality_gate_check(gate_ids=["SUBAGENT-REVIEW", "REVIEW-CONFIDENCE"])` → 审查门禁
2. `security_scan(severity_threshold="medium")` → 安全扫描
3. `code_simplify(target, scope="recent")` → 代码简化建议
- **降级**: 安全扫描→内嵌扫描降级；代码简化→内嵌简化降级
- **示例**: 用户说"做个代码审查" → 多门禁并行检查 → 汇总结果

#### /fix（修Bug）
1. `session_manage(action="save", completed_tasks=[], pending_tasks=["fix-bug"])` → 追踪修复状态
2. `quality_gate_check(gate_ids=["TEST-PASS"])` → 确认测试通过
3. `hook_manage(action="list")` → 检查Hook配置
- **降级**: 会话追踪失败→内存临时状态；门禁检查→增量缓存
- **示例**: 用户说"修复登录Bug" → 追踪状态 → 修复 → 验证测试

#### /audit（安全审计/渗透测试）
1. `security_scan(severity_threshold="low", include_agentic=True)` → 全面安全扫描
2. `quality_gate_check(gate_ids=["AI-PENTEST"])` → AI渗透测试门禁
3. `spec_drift_detect()` → 规格漂移检测
- **降级**: 安全扫描→内嵌agentic_scan+dependency_scan；渗透测试→内嵌检查
- **示例**: 用户说"安全审计" → full扫描+渗透测试 → 汇总漏洞报告

#### /accept（验收确认）
1. `quality_gate_check(phase="6")` → 验收门禁
2. `workflow_dispatch(action="status")` → 确认工作流状态
- **降级**: 门禁检查→增量缓存
- **示例**: 用户说"验收通过" → 检查验收门禁 → 推进到部署阶段

#### /deploy（部署上线）
1. `quality_gate_check(phase="6")` → 验收门禁检查
2. `server_health()` → 服务器健康检查
3. `workflow_dispatch(action="status")` → 确认可推进到部署Phase
- **降级**: 健康检查→基础状态返回
- **示例**: 用户说"部署上线" → 验收门禁 → 健康检查 → 部署

#### /build-desktop（桌面应用构建）
1. `quality_gate_check(gate_ids=["DESKTOP-BUILD", "DESKTOP-SIGN", "DESKTOP-CROSS"])` → 桌面构建门禁
2. `skill_analyze(skill_path, depth="full")` → 确认桌面项目结构
3. `workflow_dispatch(action="start", workflow="desktop-build-workflow")` → 启动桌面构建工作流
- **降级**: 桌面门禁→文件存在性检查
- **示例**: 用户说"打包桌面应用" → 检查构建配置 → 启动构建流程

#### /release-desktop（桌面发布）
1. `quality_gate_check(gate_ids=["DESKTOP-SIGN", "DESKTOP-UPDATE"])` → 签名和更新门禁
2. `workflow_dispatch(action="start", workflow="desktop-release-workflow")` → 启动发布工作流
- **降级**: 桌面门禁→文件存在性检查
- **示例**: 用户说"发布桌面应用" → 检查签名配置 → 启动发布流程

#### /simplify, /refactor（代码简化/重构）
1. `code_simplify(target, scope="recent")` → 代码简化分析
2. `quality_gate_check(gate_ids=["SIMPLIFICATION-BEHAVIOR", "CHESTERTON-FENCE"])` → 重构门禁
3. `context_compress(content=summary, strategy="semantic")` → 压缩上下文
- **降级**: 代码简化→内嵌simplify+dedup；门禁→内嵌检查
- **示例**: 用户说"重构这段代码" → 简化分析 → 门禁检查 → 安全重构

#### /loop（自主循环执行）
1. `workflow_dispatch(action="start", workflow="autonomous_loop")` → 启动自主循环
2. `session_manage(action="save", pending_tasks=[...])` → 追踪循环状态
3. `resource_load_status(action="status")` → 检查资源负载
- **降级**: 工作流启动→手动Phase推进；资源检查→基础状态
- **示例**: 用户说"自主循环执行" → 启动循环 → 持续追踪 → 资源监控

#### /cancel-loop（取消循环）
1. `workflow_dispatch(action="abort")` → 中止当前工作流
2. `session_manage(action="save")` → 保存当前状态
- **降级**: 工作流中止→状态持久化
- **示例**: 用户说"停止循环" → 中止工作流 → 保存进度

#### /learn（知识学习）
1. `knowledge_search(query, search_type="hybrid")` → 知识检索
2. `knowledge_search(query, scope="experience")` → 注入经验上下文
3. `session_manage(action="save", experience=[...])` → 经验沉淀
- **降级**: ChromaDB→SQLite FTS→关键词检索
- **示例**: 用户说"学习React最佳实践" → 检索→注入→沉淀

#### /agent-status（查询Agent）
1. `agent_status(action="list")` → 列出所有Agent
2. `agent_status(action="detail", agent_name="...")` → 查询特定Agent详情
- **降级**: 静态注册表查询
- **示例**: 用户说"查看Agent状态" → 返回57个Agent列表

#### /status（查询进度）
1. `workflow_dispatch(action="status")` → 工作流状态
2. `session_manage(action="load")` → 恢复会话状态
3. `server_health()` → 服务器健康
- **降级**: 工作流状态→持久化文件读取；会话恢复→最近会话
- **示例**: 用户说"查看进度" → 返回当前Phase+任务+决策

#### /rollback（回滚）
1. `session_manage(action="load")` → 恢复上一个会话状态
2. `workflow_dispatch(action="abort")` → 中止当前工作流
- **降级**: 会话恢复→最近保存点；工作流中止→状态持久化
- **示例**: 用户说"回滚" → 恢复上一状态 → 中止当前工作流

#### /sprint（冲刺）
1. `workflow_dispatch(action="start", workflow="sdd-tdd-fast")` → 启动快速工作流
2. `session_manage(action="save", pending_tasks=[...])` → 追踪冲刺进度
3. `resource_load_status(action="preload", phase=0)` → 预加载资源
- **降级**: 快速工作流→精简Phase；资源监控→基础状态
- **示例**: 用户说"冲刺开发" → 快速工作流 → 追踪进度 → 资源监控

#### /build（构建项目）
1. `skill_analyze(skill_path, depth="basic")` → 项目结构确认
2. `quality_gate_check(gate_ids=["BUILD-SUCCESS"])` → 构建门禁
3. `server_health()` → 健康检查
- **降级**: 构建门禁→内嵌检查；健康检查→基础状态
- **示例**: 用户说"构建项目" → 检查构建门禁 → 执行构建

#### /execute-plan（执行计划）
1. `workflow_dispatch(action="start", workflow="sdd-tdd-full")` → 启动工作流
2. `session_manage(action="save", pending_tasks=[...])` → 追踪执行状态
- **降级**: 工作流启动→手动Phase推进
- **示例**: 用户说"执行计划" → 启动工作流 → 按计划推进

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

> 完整Agent定义：agents/ 目录（57个.md文件） | MCP Resource：xuansto://references/agent-registry

## Hook系统

核心Hook：PhaseEnter/PhaseExit/GatePass/GateFail/SessionStart/SessionStop。
Hook中调用MCP工具：GatePass → `quality_gate_check`，SessionStop → `session_manage(save)`。

## 模型路由

根据任务复杂度自动选择：fast(搜索/简单编辑) / standard(多文件实现) / deep(架构设计/安全分析)。

## 会话持久化

SessionStart Hook → `session_manage(load)` 加载上下文
SessionStop Hook → `session_manage(save)` 保存摘要

## 关键规则

2-Action Research | 3-Strike Error | Chesterton's Fence | Loop Enforcement | Confidence≥80 | 三级仲裁(L1技术→L2策略ADR→L3安全人工)
UTF-8无BOM+LF | Python优先 | 业务注释中文 | Git:`<类型>(<范围>): <中文描述>` | 禁止Shell(.sh) | 五步闭环
