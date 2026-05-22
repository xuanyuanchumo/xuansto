# Skiller 项目 Code Wiki

> 版本: 3.2.0 | 许可: MIT License | 最后更新: 2026-05-07

---

## 目录

- [1. 项目概述](#1-项目概述)
- [2. 整体架构](#2-整体架构)
- [3. 技术栈与依赖](#3-技术栈与依赖)
- [4. 模块详解](#4-模块详解)
  - [4.1 xuansto-skill — 多Agent自主开发编排器](#41-xuansto-skill--多agent自主开发编排器)
  - [4.2 sanliu — 三省六部软件开发全流程管理技能](#42-sanliu--三省六部软件开发全流程管理技能)
  - [4.3 skill-creator — 技能创建与评估工具](#43-skill-creator--技能创建与评估工具)
  - [4.4 mcp-builder — MCP服务器构建指南](#44-mcp-builder--mcp服务器构建指南)
  - [4.5 ui-ux-pro-max — UI/UX设计智能](#45-ui-ux-pro-max--uiux设计智能)
  - [4.6 universal-devops — 通用AI全生命周期开发技能](#46-universal-devops--通用ai全生命周期开发技能)
  - [4.7 global-chinese — 通用中文响应技能](#47-global-chinese--通用中文响应技能)
  - [4.8 agency-agents — Agency Agent桥接](#48-agency-agents--agency-agent桥接)
  - [4.9 skills-main — 官方技能集合](#49-skills-main--官方技能集合)
- [5. 知识库服务器架构](#5-知识库服务器架构)
- [6. 关键脚本索引](#6-关键脚本索引)
- [7. 工作流与质量门禁体系](#7-工作流与质量门禁体系)
- [8. Agent角色体系](#8-agent角色体系)
- [9. 命令系统](#9-命令系统)
- [10. 配置体系](#10-配置体系)
- [11. 模块间依赖关系](#11-模块间依赖关系)
- [12. 项目运行方式](#12-项目运行方式)

---

## 1. 项目概述

Skiller 是一个 **Trae IDE 技能集合项目**，包含多个独立的技能模块（Skill），每个技能模块为 AI 编码助手提供特定领域的增强能力。项目核心目标是实现 **SDD（Spec-Driven Development）+ TDD（Test-Driven Development）融合驱动的全生命周期自动化开发编排**。

### 核心能力矩阵

| 能力维度 | 说明 |
|----------|------|
| 多Agent编排 | 57个Agent / 13层架构，覆盖产品→设计→工程→测试→安全→运维全角色 |
| 全生命周期工作流 | 9-Phase Workflow（Phase 0-8），从需求到部署的完整流程 |
| 质量门禁 | 53 Quality Gates，跨阶段严格质量保障 |
| 知识库系统 | SQLite + Chroma 双引擎，FTS5 + 向量语义混合检索 |
| 安全合规 | TrinityGuard框架 + OWASP Top 10 2026 + Agentic安全扫描 |
| 跨平台支持 | Web + Desktop（Electron/Tauri/Flutter）全平台 |
| Token优化 | 语义压缩、预算管控、并行降级 |

### 核心原则

| 原则 | 说明 |
|------|------|
| **Spec > Test > Code** | 无规格不开发 / 无测试不合并 / 覆盖率≥80% |
| **Karpathy准则** | Think Before Coding / Simplicity First / Surgical Changes |
| **增量约束** | 分解→实现→测试→重复；3次失败→停止→反模式→重启 |
| **知识库强制工作流** | 每次任务必须检索知识库→注入上下文→沉淀经验 |

---

## 2. 整体架构

```
skiller/
├── .trae/
│   └── skills/                          # 技能模块集合
│       ├── xuansto-skill/               # [核心] 多Agent自主开发编排器
│       │   ├── SKILL.md                 # 技能定义与核心规则
│       │   ├── .skill-config.yaml       # 技能元数据配置
│       │   ├── configs/default.yaml     # 默认运行配置
│       │   ├── agents/                  # 57个Agent角色定义（13层）
│       │   ├── commands/                # 23个命令定义
│       │   ├── workflows/               # 15个工作流定义
│       │   ├── scripts/                 # 49个工具脚本
│       │   │   ├── knowledge_server/    # 知识库服务器（21个模块）
│       │   │   ├── verification/        # 验证脚本集
│       │   │   └── workflow-tools/      # 工作流工具脚本
│       │   ├── references/              # 66+参考文档
│       │   ├── templates/               # 模板文件集
│       │   ├── memory/                  # 知识记忆存储
│       │   ├── .knowledge/              # 知识库数据目录
│       │   ├── migrations/              # 数据库迁移
│       │   └── examples/                # 使用示例
│       │
│       ├── sanliu/                      # 三省六部全流程管理技能
│       │   ├── SKILL.md                 # 技能定义
│       │   ├── backend/                 # FastAPI后端
│       │   │   └── app/
│       │   │       ├── main.py          # 应用入口
│       │   │       ├── api/             # API端点
│       │   │       ├── models/          # 数据模型
│       │   │       └── services/        # 业务服务
│       │   ├── frontend/                # Vue 3前端
│       │   │   └── src/
│       │   │       ├── components/      # UI组件
│       │   │       ├── views/           # 页面视图
│       │   │       ├── stores/          # Pinia状态管理
│       │   │       ├── router/          # 路由配置
│       │   │       ├── composables/     # 组合式函数
│       │   │       ├── api/             # API调用层
│       │   │       └── utils/           # 工具函数
│       │   └── tests/                   # 测试文件
│       │
│       ├── skill-creator/               # 技能创建与评估
│       ├── mcp-builder/                 # MCP服务器构建
│       ├── ui-ux-pro-max/               # UI/UX设计智能
│       ├── ui-ux-pro-max-skill/         # UI/UX Pro Max CLI版
│       ├── universal-devops/            # 通用DevOps技能
│       ├── global-chinese/              # 中文响应技能
│       ├── agency-agents/               # Agency Agent桥接
│       └── skills-main/                 # 官方技能集合
│           └── skills-main/
│               └── skills/
│                   ├── xlsx/            # Excel处理
│                   ├── docx/            # Word处理
│                   ├── pptx/            # PowerPoint处理
│                   ├── webapp-testing/  # Web应用测试
│                   ├── skill-creator/   # 技能创建（副本）
│                   └── slack-gif-creator/ # Slack GIF创建
│
├── .claude/                             # Claude IDE配置
├── .cursor/                             # Cursor IDE配置
├── .editorconfig                        # 编辑器配置
└── .gitignore                           # Git忽略规则
```

---

## 3. 技术栈与依赖

### 后端技术栈

| 技术 | 用途 | 所属模块 |
|------|------|----------|
| **Python 3.10+** | 主要脚本语言 | 全局 |
| **FastAPI** | REST API框架 | sanliu, knowledge_server |
| **Uvicorn** | ASGI服务器 | sanliu, knowledge_server |
| **SQLAlchemy** | ORM框架 | sanliu |
| **PostgreSQL** | 关系型数据库 | sanliu |
| **Redis** | 缓存 | sanliu |
| **SQLite + FTS5** | 关键词检索引擎 | knowledge_server |
| **ChromaDB** | 向量数据库引擎 | knowledge_server |
| **Sentence-Transformers** | 本地Embedding模型 | knowledge_server |
| **OpenAI API** | 远程Embedding API | knowledge_server |
| **PyYAML** | YAML配置解析 | 全局 |
| **MCP SDK** | MCP协议集成 | knowledge_server |

### 前端技术栈

| 技术 | 用途 | 所属模块 |
|------|------|----------|
| **Vue 3** | 前端框架 | sanliu |
| **TypeScript** | 类型安全 | sanliu |
| **Vite** | 构建工具 | sanliu |
| **Pinia** | 状态管理 | sanliu |
| **Element Plus** | UI组件库 | sanliu |
| **Vue Router** | 路由管理 | sanliu |
| **Axios** | HTTP客户端 | sanliu |
| **ECharts/ZRender** | 图表可视化 | sanliu |

### 脚本运行时

| 运行时 | 用途 |
|--------|------|
| **Python 3** | 主要脚本执行 |
| **Node.js** | JS脚本执行（视觉回归/性能基准等） |
| **PowerShell 7+** | 桌面构建/签名/更新验证 |

---

## 4. 模块详解

### 4.1 xuansto-skill — 多Agent自主开发编排器

**版本**: 3.2.0 | **定位**: 项目核心技能，SDD+TDD融合驱动的全生命周期编排器

#### 目录结构

```
xuansto-skill/
├── SKILL.md                     # 技能定义（Layer 2核心规则 + Layer 3引用索引）
├── .skill-config.yaml           # 技能元数据（触发词/命令/标签）
├── configs/default.yaml         # 默认运行配置（400+行）
├── agents/                      # Agent角色定义
│   ├── orchestrator/            # 编排层（3个Agent）
│   ├── product/                 # 产品层（4个Agent）
│   ├── design/                  # 设计层（4个Agent）
│   ├── engineering/             # 工程层（6个Agent）
│   ├── cross-platform/          # 跨平台层（5个Agent）
│   ├── database/                # 数据层（3个Agent）
│   ├── testing/                 # 测试层（10个Agent）
│   ├── security/                # 安全层（3个Agent）
│   ├── devops/                  # 运维层（4个Agent）
│   ├── quality/                 # 质量层（7个Agent）
│   ├── documentation/           # 文档层（2个Agent）
│   ├── knowledge/               # 知识层（3个Agent）
│   └── monitoring/              # 监控层（3个Agent）
├── commands/                    # 23个命令定义
├── workflows/                   # 15个工作流定义
│   ├── _yaml/                   # YAML格式工作流
│   ├── sdd-tdd-full.md          # 完整SDD-TDD工作流
│   ├── sdd-tdd-medium.md        # 中等SDD-TDD工作流
│   ├── sdd-tdd-fast.md          # 快速SDD-TDD工作流
│   ├── brainstorming-workflow.md # 头脑风暴工作流
│   ├── acceptance.md            # 验收工作流
│   ├── bug-fix.md               # Bug修复工作流
│   ├── security-audit.md        # 安全审计工作流
│   ├── ai-pentest.md            # AI渗透测试工作流
│   ├── desktop-build-workflow.md # 桌面构建工作流
│   ├── cross-platform-workflow.md # 跨平台工作流
│   ├── flutter-desktop-workflow.md # Flutter桌面工作流
│   ├── performance-test.md      # 性能测试工作流
│   ├── ui-ux-workflow.md        # UI/UX工作流
│   ├── webapp-testing-workflow.md # Web应用测试工作流
│   └── subagent-driven-workflow.md # 子Agent驱动工作流
├── scripts/                     # 49个工具脚本
│   ├── knowledge_server/        # 知识库服务器（21个模块）
│   ├── verification/            # 验证脚本（4个）
│   ├── workflow-tools/          # 工作流工具（5个）
│   └── [40个独立脚本]
├── references/                  # 66+参考文档
├── templates/                   # 19个模板文件
├── memory/                      # 知识记忆存储
├── .knowledge/                  # 知识库数据
├── migrations/                  # 数据库迁移
└── examples/                    # 使用示例
```

#### 核心模块调用路径

| 模块 | 命令 | 核心Agent | 关键门禁 |
|------|------|----------|---------|
| Superpowers | `/brainstorm` | Brainstorming Facilitator | BRAINSTORM-COMPLETE |
| Planning Files | `/loop`, `/cancel-loop` | Orchestrator | LOOP-COMPLETION, ITERATION-BUDGET |
| UIUXProMax | `/design-system` | Design System Generator | DESIGN-SYSTEM-COMPLETE, ANTI-PATTERN-CHECK |
| Code Review | `/review` | Code Reviewer+5子代理 | REVIEW-CONFIDENCE, MULTI-PERSPECTIVE-COVERAGE |
| Code Simplifier | `/simplify` | Refactoring Specialist | SIMPLIFICATION-BEHAVIOR, CHESTERTON-FENCE |
| WebappTesting | `/test --playwright` | E2E Tester | PLAYWRIGHT-E2E-PASS, VISUAL-REGRESSION-PASS |
| Ralph Loop | `/loop`, `/sprint --autonomous` | Orchestrator | LOOP-COMPLETION |

---

### 4.2 sanliu — 三省六部软件开发全流程管理技能

**定位**: TDD/SDD驱动的软件开发全流程管理，三省六部二十四司协同机制

#### 后端架构（FastAPI）

```
backend/
├── app/
│   ├── main.py                  # 应用入口，路由注册
│   ├── api/                     # API端点层
│   │   ├── projects.py          # 项目管理API
│   │   ├── tasks.py             # 任务管理API
│   │   ├── agents.py            # Agent管理API
│   │   ├── decision_logs.py     # 决策日志API
│   │   ├── quality_monitor.py   # 质量监控API
│   │   └── four_d_defense.py    # 四维防线API
│   ├── models/                  # 数据模型层
│   │   ├── project.py           # 项目模型
│   │   ├── task.py              # 任务模型
│   │   ├── agent.py             # Agent模型
│   │   └── decision_log.py      # 决策日志模型
│   └── services/                # 业务服务层
│       ├── resource_coordination.py  # MARC资源协调器
│       ├── workflow/
│       │   └── executor.py      # 工作流执行器
│       ├── performance/         # 性能监控服务
│       └── reports/             # 报告生成服务
├── requirements.txt             # Python依赖
└── tests/                       # 测试文件
```

#### 前端架构（Vue 3 + TypeScript）

```
frontend/
├── src/
│   ├── main.ts                  # 应用入口
│   ├── App.vue                  # 根组件
│   ├── router/index.ts          # 路由配置
│   ├── api/index.ts             # API调用层
│   ├── stores/                  # Pinia状态管理
│   │   ├── projects.ts          # 项目状态
│   │   ├── tasks.ts             # 任务状态
│   │   ├── agents.ts            # Agent状态
│   │   ├── dashboard.ts         # 仪表盘状态
│   │   ├── notifications.ts     # 通知状态
│   │   └── skillCalls.ts        # 技能调用状态
│   ├── views/                   # 页面视图
│   │   ├── Dashboard.vue        # 仪表盘
│   │   ├── ProjectList.vue      # 项目列表
│   │   ├── ProjectDetail.vue    # 项目详情
│   │   ├── ProjectCreate.vue    # 项目创建
│   │   ├── TaskManagement.vue   # 任务管理
│   │   ├── Agents.vue           # Agent管理
│   │   ├── PipelineMonitor.vue  # 流水线监控
│   │   ├── PipelineVisualizer.vue # 流水线可视化
│   │   ├── ApprovalCenter.vue   # 审批中心
│   │   ├── Statistics.vue       # 统计分析
│   │   ├── SkillCalls.vue       # 技能调用
│   │   └── TransparencyReport.vue # 透明度报告
│   ├── components/              # UI组件
│   │   └── evolution/           # 进化相关组件
│   ├── composables/             # 组合式函数
│   │   ├── useWebSocket.ts      # WebSocket通信
│   │   ├── useEnhancedWebSocket.ts # 增强WebSocket
│   │   └── useListFilter.ts     # 列表过滤
│   └── utils/                   # 工具函数
│       ├── formatters.ts        # 格式化工具
│       ├── apiHelpers.ts        # API辅助
│       ├── performance.ts       # 性能工具
│       └── prefetch.ts          # 预取工具
├── package.json                 # 前端依赖
├── vite.config.ts               # Vite配置
├── vitest.config.ts             # 测试配置
└── playwright.config.ts         # E2E测试配置
```

#### 核心API端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/projects` | GET/POST | 项目列表/创建 |
| `/api/projects/{id}` | GET/PUT/DELETE | 项目详情/更新/删除 |
| `/api/tasks` | GET/POST | 任务列表/创建 |
| `/api/tasks/{id}` | GET/PUT/DELETE | 任务详情/更新/删除 |
| `/api/agents` | GET/POST | Agent列表/注册 |
| `/api/agents/{id}` | GET/PUT | Agent详情/更新 |
| `/api/decision-logs` | GET/POST | 决策日志查询/记录 |
| `/api/quality-monitor` | GET | 质量监控数据 |
| `/api/four-d-defense` | GET/POST | 四维防线检查 |

#### 核心数据模型

| 模型 | 关键属性 | 说明 |
|------|----------|------|
| **Project** | name, description, status | 项目实体 |
| **Task** | description, assignee, status, dependencies | 任务实体 |
| **Agent** | name, role, configuration | AI代理实体 |
| **DecisionLog** | decision, context, outcome | 决策记录 |

---

### 4.3 skill-creator — 技能创建与评估工具

**定位**: 创建新技能、改进现有技能、衡量技能表现

#### 目录结构

```
skill-creator/
├── SKILL.md                     # 技能定义
├── scripts/                     # 工具脚本
│   ├── __init__.py
│   ├── utils.py                 # 通用工具函数
│   ├── run_loop.py              # 评估循环运行器
│   ├── run_eval.py              # 评估执行器
│   ├── quick_validate.py        # 快速验证
│   ├── package_skill.py         # 技能打包
│   ├── improve_description.py   # 描述优化
│   ├── generate_report.py       # 报告生成
│   └── aggregate_benchmark.py   # 基准聚合
├── agents/                      # Agent定义
│   ├── grader.md                # 评分Agent
│   ├── comparator.md            # 比较Agent
│   └── analyzer.md              # 分析Agent
├── references/schemas.md        # 技能Schema参考
├── eval-viewer/                 # 评估结果查看器
│   ├── viewer.html              # HTML查看器
│   └── generate_review.py       # 评审生成
└── LICENSE.txt                  # MIT许可证
```

#### 关键脚本功能

| 脚本 | 功能 |
|------|------|
| `run_eval.py` | 执行技能评估，运行测试用例并收集结果 |
| `run_loop.py` | 评估循环运行器，支持多次迭代评估 |
| `quick_validate.py` | 快速验证技能结构完整性 |
| `package_skill.py` | 将技能打包为可分发格式 |
| `improve_description.py` | 优化技能描述以提升触发准确率 |
| `generate_report.py` | 生成评估报告 |
| `aggregate_benchmark.py` | 聚合多次基准测试结果 |

---

### 4.4 mcp-builder — MCP服务器构建指南

**定位**: 指导创建高质量的MCP（Model Context Protocol）服务器

#### 目录结构

```
mcp-builder/
├── SKILL.md                     # 技能定义
├── scripts/
│   ├── evaluation.py            # MCP服务器评估脚本
│   └── connections.py           # MCP连接测试脚本
├── reference/                   # 参考文档
│   ├── python_mcp_server.md     # Python MCP服务器指南
│   ├── node_mcp_server.md       # Node.js MCP服务器指南
│   ├── mcp_best_practices.md    # MCP最佳实践
│   └── evaluation.md            # 评估标准
└── LICENSE.txt
```

#### 四阶段开发流程

| 阶段 | 说明 |
|------|------|
| 1. 研究与规划 | 深入理解需求，设计MCP工具接口 |
| 2. 实施 | 使用Python FastMCP或Node MCP SDK实现 |
| 3. 审查与测试 | 代码质量检查、功能测试 |
| 4. 创建评估 | 构建评估用例验证工具质量 |

---

### 4.5 ui-ux-pro-max — UI/UX设计智能

**定位**: Web和移动应用的UI/UX设计智能引擎

#### 核心能力

| 维度 | 数量 | 说明 |
|------|------|------|
| 样式 | 50+ | glassmorphism, claymorphism, minimalism等 |
| 配色方案 | 161种 | 预定义配色方案 |
| 字体配对 | 57种 | 字体组合推荐 |
| 产品类型 | 161种 | 覆盖各类产品场景 |
| UX准则 | 99条 | 用户体验最佳实践 |
| 图表类型 | 25种 | 数据可视化图表 |
| 技术栈 | 10种 | React, Next.js, Vue, Svelte, SwiftUI等 |

#### 脚本

| 脚本 | 功能 |
|------|------|
| `core.py` | 核心设计数据和配置 |
| `search.py` | 设计领域搜索 |
| `design_system.py` | 设计系统生成 |

---

### 4.6 universal-devops — 通用AI全生命周期开发技能

**定位**: 集成各种工具和技能，提供从开发到生产的全面DevOps能力

**版本**: v7.0

#### 核心特性

- 开源融合引擎（OpenCode/OpenClaude/Claw-Code）
- 哲学融合引擎
- 全生命周期 21 阶段技能矩阵
- CI/CD 自动化流水线
- 六维质量监控
- 自演化闭环
- MARC-Lite 多 Agent 资源协调器

---

### 4.7 global-chinese — 通用中文响应技能

**定位**: 确保无论用户使用何种语言提问，系统都能正确理解并触发对应语言的技能，最终所有输出内容都用简体中文回答

#### 核心能力

| 能力 | 说明 |
|------|------|
| **语言无关性接收** | 可接收任何语言的用户输入 |
| **智能技能触发** | 根据输入语义正确触发对应技能 |
| **强制简体中文输出** | 所有输出统一转换为简体中文 |

---

### 4.8 agency-agents — Agency Agent 桥接

**定位**: 提供 Agency Agent 相关的桥接功能

#### 目录结构

```
agency-agents/
├── testing/                  # 测试相关模块
│   ├── testing-workflow-optimizer.md
│   ├── testing-tool-evaluator.md
│   ├── testing-test-results-analyzer.md
│   ├── testing-reality-checker.md
│   ├── testing-performance-benchmarker.md
│   ├── testing-evidence-collector.md
│   ├── testing-api-tester.md
│   └── testing-accessibility-auditor.md
├── support/                  # 支持相关模块
│   ├── support-support-responder.md
│   ├── support-legal-compliance-checker.md
│   ├── support-infrastructure-maintainer.md
│   ├── support-finance-tracker.md
│   ├── support-executive-summary-generator.md
│   └── support-analytics-reporter.md
└── CONTRIBUTING.md
```

---

### 4.9 skills-main — 官方技能集合

**定位**: Claude Code Collective 官方技能集合

#### 包含的子技能

| 技能 | 功能 |
|------|------|
| **xlsx** | Excel 文件处理，支持 redline 标注 |
| **docx** | Word 文档处理，批注/接受变更 |
| **pptx** | PowerPoint 文档处理，缩略图生成 |
| **webapp-testing** | Web 应用自动化测试，Playwright 集成 |
| **skill-creator** | 技能创建工具（副本） |
| **slack-gif-creator** | Slack GIF 创建工具 |

---

## 5. 知识库服务器架构

### 5.1 核心架构图

```
┌────────────────────────────────────────────────────────────┐
│                      knowledge_server                      │
├────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────┐ │
│  │  main.py - 入口与启动                                │ │
│  │  server.py - 服务器核心类                           │ │
│  └──────────────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  API 层                                              │ │
│  │  ├── api.py - API 封装                               │ │
│  │  ├── api_routes.py - 路由定义                        │ │
│  │  ├── api_models.py - 数据模型                        │ │
│  │  ├── auth.py - 认证                                  │ │
│  │  ├── security.py - 安全检查                          │ │
│  │  └── mcp_server.py - MCP 协议                        │ │
│  └──────────────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  检索层                                              │ │
│  │  ├── hybrid_search.py - 混合检索                     │ │
│  │  ├── db_engine.py - SQLite 引擎                      │ │
│  │  ├── vector_engine.py - Chroma 向量引擎              │ │
│  │  └── embedding.py - Embedding 生成                   │ │
│  └──────────────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  管理层                                              │ │
│  │  ├── dedup.py - 去重                                 │ │
│  │  ├── lifecycle.py - 生命周期管理                      │ │
│  │  ├── sync.py - 文件同步                              │ │
│  │  ├── backup.py - 备份恢复                            │ │
│  │  ├── exporter.py - 知识导出                          │ │
│  │  └── importer.py - 知识导入                          │ │
│  └──────────────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  工具层                                              │ │
│  │  ├── config.py - 配置管理                            │ │
│  │  ├── degradation.py - 降级策略                       │ │
│  │  └── websocket_manager.py - WebSocket 管理          │ │
│  └──────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────┘
```

### 5.2 核心模块说明

| 模块 | 文件 | 职责 |
|------|------|------|
| **入口模块** | [main.py](file:///D:/Projects/TraeProjects/skiller/.trae/skills/xuansto-skill/scripts/knowledge_server/main.py) | 命令行参数处理、配置加载、服务启动 |
| **服务器核心** | [server.py](file:///D:/Projects/TraeProjects/skiller/.trae/skills/xuansto-skill/scripts/knowledge_server/server.py) | KnowledgeServer 核心类，组件初始化与协调 |
| **API 路由** | [api_routes.py](file:///D:/Projects/TraeProjects/skiller/.trae/skills/xuansto-skill/scripts/knowledge_server/api_routes.py) | REST API 端点定义 |
| **数据模型** | [api_models.py](file:///D:/Projects/TraeProjects/skiller/.trae/skills/xuansto-skill/scripts/knowledge_server/api_models.py) | API 请求/响应模型 |
| **SQL 引擎** | [db_engine.py](file:///D:/Projects/TraeProjects/skiller/.trae/skills/xuansto-skill/scripts/knowledge_server/db_engine.py) | SQLite + FTS5 关键词检索引擎 |
| **向量引擎** | [vector_engine.py](file:///D:/Projects/TraeProjects/skiller/.trae/skills/xuansto-skill/scripts/knowledge_server/vector_engine.py) | ChromaDB 向量存储与检索 |
| **混合检索** | [hybrid_search.py](file:///D:/Projects/TraeProjects/skiller/.trae/skills/xuansto-skill/scripts/knowledge_server/hybrid_search.py) | 语义权重 0.7 + 关键词权重 0.3 融合 |
| **Embedding** | [embedding.py](file:///D:/Projects/TraeProjects/skiller/.trae/skills/xuansto-skill/scripts/knowledge_server/embedding.py) | Sentence-Transformers / OpenAI API 二选一 |
| **配置管理** | [config.py](file:///D:/Projects/TraeProjects/skiller/.trae/skills/xuansto-skill/scripts/knowledge_server/config.py) | 服务器配置项 |
| **认证** | [auth.py](file:///D:/Projects/TraeProjects/skiller/.trae/skills/xuansto-skill/scripts/knowledge_server/auth.py) | API 密钥认证 |
| **安全** | [security.py](file:///D:/Projects/TraeProjects/skiller/.trae/skills/xuansto-skill/scripts/knowledge_server/security.py) | 输入验证、敏感内容过滤 |
| **备份** | [backup.py](file:///D:/Projects/TraeProjects/skiller/.trae/skills/xuansto-skill/scripts/knowledge_server/backup.py) | 定期备份与恢复 |
| **去重** | [dedup.py](file:///D:/Projects/TraeProjects/skiller/.trae/skills/xuansto-skill/scripts/knowledge_server/dedup.py) | 知识条目去重 |
| **降级** | [degradation.py](file:///D:/Projects/TraeProjects/skiller/.trae/skills/xuansto-skill/scripts/knowledge_server/degradation.py) | 动态调整检索策略 |
| **导出** | [exporter.py](file:///D:/Projects/TraeProjects/skiller/.trae/skills/xuansto-skill/scripts/knowledge_server/exporter.py) | 知识导出为 Markdown |
| **导入** | [importer.py](file:///D:/Projects/TraeProjects/skiller/.trae/skills/xuansto-skill/scripts/knowledge_server/importer.py) | 初始知识库导入 |
| **生命周期** | [lifecycle.py](file:///D:/Projects/TraeProjects/skiller/.trae/skills/xuansto-skill/scripts/knowledge_server/lifecycle.py) | 自动归档、清理过时条目 |
| **同步** | [sync.py](file:///D:/Projects/TraeProjects/skiller/.trae/skills/xuansto-skill/scripts/knowledge_server/sync.py) | 文件监控、增量同步 |
| **WebSocket** | [websocket_manager.py](file:///D:/Projects/TraeProjects/skiller/.trae/skills/xuansto-skill/scripts/knowledge_server/websocket_manager.py) | 实时通信与状态推送 |
| **MCP 协议** | [mcp_server.py](file:///D:/Projects/TraeProjects/skiller/.trae/skills/xuansto-skill/scripts/knowledge_server/mcp_server.py) | MCP 协议支持 |

### 5.3 三层知识库结构

```
通用知识层 (general/)
    ├── coding-standards.md
    ├── design-patterns.md
    └── ...

工作知识层 (workspace/)
    ├── architecture.md
    ├── api-contracts.md
    └── adr/

经验知识层 (experience/)
    ├── fixes/
    ├── errors/
    └── patterns/
```

### 5.4 API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/knowledge/search` | POST | 知识检索（支持 hybrid/semantic/keyword） |
| `/knowledge` | GET/POST | 查询/添加知识条目 |
| `/knowledge/{id}` | GET/PUT/DELETE | 知识条目 CRUD |
| `/sync` | POST | 触发文件同步 |
| `/backup` | POST | 触发备份 |
| `/ws` | WebSocket | 实时通信 |

---

## 6. 关键脚本索引

### 6.1 知识库相关脚本（10个）

| 脚本 | 功能 | 所属阶段 |
|------|------|----------|
| [knowledge-server.py](file:///D:/Projects/TraeProjects/skiller/.trae/skills/xuansto-skill/scripts/knowledge-server.py) | 知识服务器启动入口 | 全阶段 |
| [knowledge-index-builder.py](file:///D:/Projects/TraeProjects/skiller/.trae/skills/xuansto-skill/scripts/knowledge-index-builder.py) | 构建 FTS5/元数据/交叉引用索引 | 初始化 |
| [knowledge-server-tests.py](file:///D:/Projects/TraeProjects/skiller/.trae/skills/xuansto-skill/scripts/knowledge-server-tests.py) | 知识服务器单元测试 | 测试 |
| [kb-migrate.py](file:///D:/Projects/TraeProjects/skiller/.trae/skills/xuansto-skill/scripts/kb-migrate.py) | 知识库版本迁移 | 升级 |
| [kb-branch-sync.py](file:///D:/Projects/TraeProjects/skiller/.trae/skills/xuansto-skill/scripts/kb-branch-sync.py) | 多分支知识库同步 | 协作 |
| [pattern-learner.py](file:///D:/Projects/TraeProjects/skiller/.trae/skills/xuansto-skill/scripts/pattern-learner.py) | 从数据中提取通用模式 | 学习 |

### 6.2 Token 优化脚本（3个）

| 脚本 | 功能 | 所属阶段 |
|------|------|----------|
| [token-budget-guard.py](file:///D:/Projects/TraeProjects/skiller/.trae/skills/xuansto-skill/scripts/token-budget-guard.py) | Token 预算守护、限流策略 | 全阶段 |
| [context-compressor.py](file:///D:/Projects/TraeProjects/skiller/.trae/skills/xuansto-skill/scripts/context-compressor.py) | 上下文语义压缩 | 全阶段 |
| [token-dashboard.py](file:///D:/Projects/TraeProjects/skiller/.trae/skills/xuansto-skill/scripts/token-dashboard.py) | Token 使用统计仪表盘 | 监控 |

### 6.3 质量门禁脚本（14个）

| 脚本 | 功能 | 所属阶段 |
|------|------|----------|
| [loop-guard.py](file:///D:/Projects/TraeProjects/skiller/.trae/skills/xuansto-skill/scripts/loop-guard.py) | 防止无限循环 | 实现 |
| [completion-verifier.py](file:///D:/Projects/TraeProjects/skiller/.trae/skills/xuansto-skill/scripts/completion-verifier.py) | 补全结果验证 | 实现 |
| [confidence-scorer.py](file:///D:/Projects/TraeProjects/skiller/.trae/skills/xuansto-skill/scripts/confidence-scorer.py) | 置信度评分 | 审查 |
| [review-aggregator.py](file:///D:/Projects/TraeProjects/skiller/.trae/skills/xuansto-skill/scripts/review-aggregator.py) | 评审意见聚合 | 审查 |
| [review-eligibility-check.py](file:///D:/Projects/TraeProjects/skiller/.trae/skills/xuansto-skill/scripts/review-eligibility-check.py) | 评审资格验证 | 审查 |
| [code-simplifier.py](file:///D:/Projects/TraeProjects/skiller/.trae/skills/xuansto-skill/scripts/code-simplifier.py) | 代码简化（AST） | 重构 |
| [deduplication-detector.py](file:///D:/Projects/TraeProjects/skiller/.trae/skills/xuansto-skill/scripts/deduplication-detector.py) | 重复内容检测 | 重构 |
| [spec-drift-detector.py](file:///D:/Projects/TraeProjects/skiller/.trae/skills/xuansto-skill/scripts/spec-drift-detector.py) | 规格漂移检测 | 审查 |
| [coverage-check.py](file:///D:/Projects/TraeProjects/skiller/.trae/skills/xuansto-skill/scripts/coverage-check.py) | 测试覆盖率检查 | 测试 |
| [api-contract-validator.py](file:///D:/Projects/TraeProjects/skiller/.trae/skills/xuansto-skill/scripts/api-contract-validator.py) | API 合约验证 | 测试 |
| [db-migration-validator.py](file:///D:/Projects/TraeProjects/skiller/.trae/skills/xuansto-skill/scripts/db-migration-validator.py) | 数据库迁移验证 | 部署 |
| [check-encoding.py](file:///D:/Projects/TraeProjects/skiller/.trae/skills/xuansto-skill/scripts/check-encoding.py) | 文件编码检查（UTF-8无BOM） | 实现 |
| [check-comment-lang.py](file:///D:/Projects/TraeProjects/skiller/.trae/skills/xuansto-skill/scripts/check-comment-lang.py) | 注释语言检查 | 实现 |
| [check-complete.py](file:///D:/Projects/TraeProjects/skiller/.trae/skills/xuansto-skill/scripts/check-complete.py) | 文件完整性验证 | 全阶段 |

### 6.4 安全脚本（4个）

| 脚本 | 功能 | 所属阶段 |
|------|------|----------|
| [agentic-security-scanner.py](file:///D:/Projects/TraeProjects/skiller/.trae/skills/xuansto-skill/scripts/agentic-security-scanner.py) | Agent 安全扫描 | 测试 |
| [ai-pentest-runner.py](file:///D:/Projects/TraeProjects/skiller/.trae/skills/xuansto-skill/scripts/ai-pentest-runner.py) | AI 渗透测试 | 测试 |
| [script-security-scanner.py](file:///D:/Projects/TraeProjects/skiller/.trae/skills/xuansto-skill/scripts/script-security-scanner.py) | 脚本安全扫描 | 审查 |
| [dependency-scan.py](file:///D:/Projects/TraeProjects/skiller/.trae/skills/xuansto-skill/scripts/dependency-scan.py) | 依赖漏洞扫描 | 测试 |

### 6.5 测试与报告脚本（5个）

| 脚本 | 功能 | 所属阶段 |
|------|------|----------|
| [uat-runner.py](file:///D:/Projects/TraeProjects/skiller/.trae/skills/xuansto-skill/scripts/uat-runner.py) | UAT 验收测试执行 | 验收 |
| [test-reporter.py](file:///D:/Projects/TraeProjects/skiller/.trae/skills/xuansto-skill/scripts/test-reporter.py) | 测试报告生成 | 测试 |
| [documentation-coverage.py](file:///D:/Projects/TraeProjects/skiller/.trae/skills/xuansto-skill/scripts/documentation-coverage.py) | 文档覆盖率检查 | 审查 |
| [skill-test.py](file:///D:/Projects/TraeProjects/skiller/.trae/skills/xuansto-skill/scripts/skill-test.py) | 技能功能测试 | 测试 |
| [skill-md-validator.py](file:///D:/Projects/TraeProjects/skiller/.trae/skills/xuansto-skill/scripts/skill-md-validator.py) | 技能 Markdown 验证 | 验证 |
| [agent-frontmatter-validator.py](file:///D:/Projects/TraeProjects/skiller/.trae/skills/xuansto-skill/scripts/agent-frontmatter-validator.py) | Agent 元数据验证 | 验证 |

### 6.6 会话与计划脚本（4个）

| 脚本 | 功能 | 所属阶段 |
|------|------|----------|
| [init-session.py](file:///D:/Projects/TraeProjects/skiller/.trae/skills/xuansto-skill/scripts/init-session.py) | 会话初始化 | 启动 |
| [session-catchup.py](file:///D:/Projects/TraeProjects/skiller/.trae/skills/xuansto-skill/scripts/session-catchup.py) | 会话状态恢复 | 恢复 |
| [plan-sync.py](file:///D:/Projects/TraeProjects/skiller/.trae/skills/xuansto-skill/scripts/plan-sync.py) | 计划同步 | 全阶段 |
| [with_server.py](file:///D:/Projects/TraeProjects/skiller/.trae/skills/xuansto-skill/scripts/with_server.py) | 服务启动包装器 | 启动 |

### 6.7 Web 测试脚本（5个）

| 脚本 | 功能 | 所属阶段 |
|------|------|----------|
| [visual-capture.py](file:///D:/Projects/TraeProjects/skiller/.trae/skills/xuansto-skill/scripts/visual-capture.py) | 可视化捕获 | 测试 |
| [console_monitor.py](file:///D:/Projects/TraeProjects/skiller/.trae/skills/xuansto-skill/scripts/console_monitor.py) | 控制台日志监控 | 测试 |
| [element_discovery.py](file:///D:/Projects/TraeProjects/skiller/.trae/skills/xuansto-skill/scripts/element_discovery.py) | UI 元素自动发现 | 测试 |
| [visual-regression.js](file:///D:/Projects/TraeProjects/skiller/.trae/skills/xuansto-skill/scripts/visual-regression.js) | 视觉回归测试 | 测试 |
| [performance-benchmark.js](file:///D:/Projects/TraeProjects/skiller/.trae/skills/xuansto-skill/scripts/performance-benchmark.js) | 性能基准测试 | 测试 |
| [accessibility-test.js](file:///D:/Projects/TraeProjects/skiller/.trae/skills/xuansto-skill/scripts/accessibility-test.js) | 无障碍测试 | 测试 |

### 6.8 桌面构建脚本（3个 PowerShell）

| 脚本 | 功能 | 所属阶段 |
|------|------|----------|
| [build-desktop.ps1](file:///D:/Projects/TraeProjects/skiller/.trae/skills/xuansto-skill/scripts/build-desktop.ps1) | 桌面应用构建 | 部署 |
| [sign-desktop.ps1](file:///D:/Projects/TraeProjects/skiller/.trae/skills/xuansto-skill/scripts/sign-desktop.ps1) | 应用签名 | 部署 |
| [verify-auto-update.ps1](file:///D:/Projects/TraeProjects/skiller/.trae/skills/xuansto-skill/scripts/verify-auto-update.ps1) | 自动更新验证 | 部署 |

### 6.9 其他脚本（3个）

| 脚本 | 功能 | 所属阶段 |
|------|------|----------|
| [ipc-contract-validator.js](file:///D:/Projects/TraeProjects/skiller/.trae/skills/xuansto-skill/scripts/ipc-contract-validator.js) | IPC 合约验证 | 跨平台 |
| [design-tokens-sync.js](file:///D:/Projects/TraeProjects/skiller/.trae/skills/xuansto-skill/scripts/design-tokens-sync.js) | 设计令牌同步 | 设计 |
| [infra-health-check.py](file:///D:/Projects/TraeProjects/skiller/.trae/skills/xuansto-skill/scripts/infra-health-check.py) | 基础设施健康检查 | 运维 |
| [script-cleanup-checker.py](file:///D:/Projects/TraeProjects/skiller/.trae/skills/xuansto-skill/scripts/script-cleanup-checker.py) | 废弃脚本清理 | 运维 |

---

## 7. 工作流与质量门禁体系

### 7.1 9-Phase SDD-TDD 工作流

| Phase | 名称 | 负责 Agent | 关键门禁 | 交付物 |
|-------|------|------------|----------|--------|
| **0** | 初始化与设计 | Design System Generator | DESIGN-SYSTEM-COMPLETE, ANTI-PATTERN-CHECK | 设计系统、UI 规范 |
| **1** | 需求分析 | Product Manager, Brainstorming Facilitator | BRAINSTORM-COMPLETE, GATE-001~002 | 需求文档、用户故事 |
| **2** | 架构设计 | System Architect | PLAN-ATOMIC, GATE-003~004 | 架构设计、接口定义 |
| **3** | 测试先行 | Test Architect | GATE-005~006 | 测试用例、测试计划 |
| **4** | 代码实现 | Engineering Agents | SUBAGENT-REVIEW, REVIEW-CONFIDENCE, GATE-007~009, FILE-ENCODING, SCRIPT-* | 实现代码 |
| **5** | 测试验证 | Testing Agents | PLAYWRIGHT-E2E-PASS, GATE-011~012, AI-PENTEST, SPEC-CONSISTENCY | 测试报告、漏洞报告 |
| **6** | 验收确认 | Product Manager | GATE-013~014, INFRA-HEALTH, UX-ACCEPTANCE | 验收报告 |
| **7** | 持续重构 | Refactoring Specialist | SIMPLIFICATION-BEHAVIOR, CHESTERTON-FENCE, GATE-015 | 重构后的代码 |
| **8** | 部署交付 | DevOps Agents | DESKTOP-BUILD/SIGN/UPDATE/CROSS, IPC-CONTRACT | 可交付产品 |

### 7.2 质量门禁（53个）

| 类别 | 门禁名称 | 说明 |
|------|----------|------|
| **需求门禁** | GATE-001, GATE-002 | 需求完整性、歧义检查 |
| **架构门禁** | GATE-003, GATE-004 | 架构可行性、可扩展性 |
| **测试门禁** | GATE-005, GATE-006 | 测试覆盖率 ≥80% |
| **实现门禁** | GATE-007~009 | 代码规范、编码标准 |
| **验证门禁** | GATE-011~012 | E2E 测试通过、性能达标 |
| **验收门禁** | GATE-013~014 | 功能验收、用户验收 |
| **重构门禁** | GATE-015 | 重构验证、无功能变更 |
| **设计门禁** | DESIGN-SYSTEM-COMPLETE, ANTI-PATTERN-CHECK | 设计完整性、反模式检查 |
| **评审门禁** | REVIEW-CONFIDENCE, MULTI-PERSPECTIVE-COVERAGE | 置信度 ≥80% |
| **安全门禁** | AI-PENTEST, SPEC-CONSISTENCY | 渗透测试通过 |
| **文件门禁** | FILE-ENCODING, SCRIPT-* | UTF-8无BOM，脚本规范 |
| **Token门禁** | TOKEN-BUDGET | 预算管控 |

### 7.3 核心约束规则

| 规则 | 说明 |
|------|------|
| **Spec > Test > Code** | 无规格不开发 / 无测试不合并 |
| **Karpathy 准则** | Think Before Coding / Simplicity First / Surgical Changes |
| **双动作规则** | 每次迭代必须完成两个动作 |
| **三击协议** | 3次失败 → 停止 → 反模式分析 → 重启 |
| **Chesterton 栅栏** | 移除代码前必须理解其用途 |
| **知识库强制工作流** | 每次任务必须检索→注入→沉淀 |

---

## 8. Agent 角色体系

### 8.1 13层架构总览

```
┌─────────────────────────────────────────────────────────┐
│  13. 监控层 (3)   │ Quality Monitor, Progress Tracker, Decision Logger │
├─────────────────────────────────────────────────────────┤
│  12. 知识层 (3)   │ Knowledge Manager, Learning Specialist, Token Optimizer │
├─────────────────────────────────────────────────────────┤
│  11. 文档层 (2)   │ Documentation Engineer, Specification Keeper │
├─────────────────────────────────────────────────────────┤
│  10. 质量层 (7)   │ Bug Scanner, Code Reviewer, Comment Verifier, Compliance Reviewer, Doc Reviewer, History Analyzer, Refactoring Specialist │
├─────────────────────────────────────────────────────────┤
│   9. 运维层 (4)   │ Build-Release Engineer, CI/CD Specialist, Monitor Specialist, Runtime Supervisor │
├─────────────────────────────────────────────────────────┤
│   8. 安全层 (3)   │ Security Auditor, Penetration Tester, Compliance Officer │
├─────────────────────────────────────────────────────────┤
│   7. 测试层 (10)  │ AI Penetration Tester, Desktop Tester, E2E Tester, Integration Tester, Performance Tester, QA Engineer, Security Tester, Test Architect, Test Maintainer, Unit Tester │
├─────────────────────────────────────────────────────────┤
│   6. 数据层 (3)   │ Data Modeler, Data Seeder, DBA │
├─────────────────────────────────────────────────────────┤
│   5. 跨平台层 (5) │ Auto-Update Engineer, Desktop Developer, Desktop UI Adapter, IPC Specialist, Native Module Developer │
├─────────────────────────────────────────────────────────┤
│   4. 工程层 (6)   │ Backend Developer, Database Engineer, DevOps Engineer, Frontend Developer, Fullstack Engineer, Mobile Developer │
├─────────────────────────────────────────────────────────┤
│   3. 设计层 (4)   │ Design System Generator, Frontend Stylist, UI Designer, UX Designer │
├─────────────────────────────────────────────────────────┤
│   2. 产品层 (4)   │ Brainstorming Facilitator, Product Manager, System Architect, Technical Writer │
├─────────────────────────────────────────────────────────┤
│   1. 编排层 (3)   │ Orchestrator, Subagent Dispatcher, Task Coordinator │
└─────────────────────────────────────────────────────────┘
```

### 8.2 关键 Agent 说明

#### 编排层 (Orchestration)

| Agent | 职责 |
|-------|------|
| **Orchestrator** | 整体工作流编排、任务分配、冲突解决 |
| **Subagent Dispatcher** | 子 Agent 调度、并行协调 |
| **Task Coordinator** | 任务状态跟踪、依赖管理 |

#### 代码审查子代理

Code Reviewer 调用 5 个子代理进行多视角审查：

| 子代理 | 审查视角 |
|--------|----------|
| **Compliance Reviewer** | 规范合规性 |
| **Bug Scanner** | 潜在 Bug |
| **History Analyzer** | 历史上下文 |
| **Comment Verifier** | 注释质量 |
| **Specification Keeper** | 规格一致性 |

#### 安全测试 6 代理协作

| Agent | 职责 |
|-------|------|
| **Security Auditor** | 安全审计规划 |
| **Penetration Tester** | 手动渗透测试 |
| **Compliance Officer** | 合规检查（OWASP） |
| **AI Penetration Tester** | AI 驱动的自动渗透 |
| **Bug Scanner** | 漏洞扫描 |
| **QA Engineer** | 安全功能测试 |

---

## 9. 命令系统

### 9.1 23个命令索引

| 命令 | 说明 | 相关 Phase |
|------|------|------------|
| `/sprint` | 冲刺规划，定义迭代目标 | 0-1 |
| `/clarify` | 需求澄清，消除歧义 | 1 |
| `/plan` | 架构规划，确定技术方案 | 2 |
| `/spec` | 规格编写，输出 SDD 规格文档 | 2 |
| `/design` | UI/UX 设计 | 0 |
| `/implement` | TDD 实现，先测试后编码 | 3-4 |
| `/test` | 测试执行，全量验证 | 5 |
| `/review` | 代码审查，质量把关 | 4-6 |
| `/fix` | Bug 修复 | 4-7 |
| `/accept` | 验收确认，完成交付 | 6 |
| `/deploy` | 部署发布 | 8 |
| `/build-desktop` | 桌面应用构建 | 8 |
| `/release-desktop` | 桌面应用发布 | 8 |
| `/refactor` | 代码重构 | 7 |
| `/audit` | 安全审计 | 5 |
| `/agent-status` | Agent 状态监控 | 全阶段 |
| `/learn` | 知识学习 | 全阶段 |
| `/brainstorm` | 需求探索，头脑风暴 | 1 |
| `/execute-plan` | 执行计划 | 2-8 |
| `/design-system` | 生成设计系统 | 0 |
| `/simplify` | 代码简化 | 7 |
| `/loop` | 循环执行（Ralph Loop） | 全阶段 |
| `/cancel-loop` | 取消循环 | 全阶段 |

---

## 10. 配置体系

### 10.1 主要配置文件

| 文件 | 位置 | 说明 |
|------|------|------|
| **.skill-config.yaml** | [xuansto-skill/.skill-config.yaml](file:///D:/Projects/TraeProjects/skiller/.trae/skills/xuansto-skill/.skill-config.yaml) | 技能元数据（触发词、命令、标签） |
| **default.yaml** | [xuansto-skill/configs/default.yaml](file:///D:/Projects/TraeProjects/skiller/.trae/skills/xuansto-skill/configs/default.yaml) | 400+ 行运行配置 |

### 10.2 default.yaml 配置分区

| 分区 | 说明 |
|------|------|
| **orchestrator** | 最大并发 Agent、系统并行容量、超时、重试策略、Agent 合并规则 |
| **quality_gates** | 执行模式（strict）、覆盖率阈值（unit 80%）、绕过审批 |
| **communication** | A2A/v1.1 协议、MCP 兼容、加密、消息超时 |
| **desktop** | Electron/Tauri/Flutter 支持、目标平台（win/mac/linux）、代码签名要求、安装包格式 |
| **logging** | 级别（info）、格式（json）、保留天数（30）、链路追踪 |
| **knowledge_base** | 通用知识自动同步、工作区知识自动更新、经验自动提取 |
| **security** | OWASP Top 10、OWASP Agentic Top 10、渗透测试、SAST、依赖扫描、漏洞阈值（P2）、扫描频率 |
| **observability** | 指标采集间隔、告警通道、监控端点、链路追踪、保留天数 |
| **cost_optimization** | 模型选择策略、Token 预算、上下文裁剪、知识检索 Top-K、并行转串行阈值 |
| **platform_detection** | 自动检测、检测优先级、Web/桌面指示器、默认平台 |
| **human_collaboration** | 验收失败断点、规格漂移断点、安全关键断点、迭代卡住断点、审批超时、自动继续 |
| **knowledge_layer** | 知识管理器自动同步、学习专家自动提取、Token 优化器预算执行 |
| **monitoring_layer** | 质量监控门禁检查间隔、进度跟踪里程碑跟踪、决策日志自动记录 |
| **karpathy_guidelines** | 合规阈值（0.9）、思考检查、简洁优先、外科手术式变更检查、目标驱动执行检查 |
| **script_execution** | Python 运行时、Node 运行时、PowerShell 运行时、超时、沙箱、临时目录、错误日志目录、完成清理、Shell 禁止 |
| **encoding** | 默认（UTF-8）、无 BOM、行尾（LF）、Python 编码声明禁止、提交检查 |
| **token_optimization** | 预算（100000）、警告阈值（0.8）、阻断阈值（1.0）、压缩级别（semantic）、日志启用 |
| **loop** | 最大迭代（50）、最大停滞（3）、完成承诺、完成自动归档、Token 预算保留（0.1） |
| **planning_files** | 缓存目录、自动归档、归档目标、双动作规则启用、三击协议启用 |
| **review** | 置信度阈值（80）、多视角、子代理列表 |
| **simplification** | Chesterton 栅栏、行为等价、最大嵌套深度（3）、最小重复出现（3） |
| **webapp_testing** | 默认浏览器（chromium）、服务器超时（30）、视觉回归阈值（0.001）、控制台错误级别（error） |
| **on_demand_loading** | 启用、策略（lazy）、预加载、缓存大小、卸载启用、策略（phase-aware）、始终保留、阶段转换规则 |
| **knowledge_service** | 主机（127.0.0.1）、端口（8765）、认证模式（local）、备份目录 |
| **degradation** | L1/L2/L3 降级策略、恢复检查间隔、自动恢复 |

### 10.3 Token 预算配置

```yaml
token_budget:
  default: 100000
  warning_threshold: 0.8          # 80% 触发压缩
  compression_threshold: 0.8
  compression_triggers:
    level_1_threshold: 0.6        # 无损压缩
    level_2_threshold: 0.8        # 语义压缩
    level_3_threshold: 0.95       # 选择性丢弃
  block_threshold: 1.0            # 100% 阻断
  per_phase:
    phase_0: 10000
    phase_1: 15000
    phase_2: 20000
    phase_3: 10000
    phase_4: 30000
    phase_5: 15000
    phase_6: 8000
    phase_7: 12000
    phase_8: 10000
```

---

## 11. 模块间依赖关系

### 11.1 依赖图

```
                    ┌───────────────┐
                    │  Trae IDE    │
                    └───────┬───────┘
                            │
            ┌───────────────┴───────────────┐
            │                               │
     ┌──────▼──────┐                  ┌─────▼─────┐
     │ xuansto-    │                  │  sanliu   │
     │ skill       │◄────────────────►│           │
     └──────┬──────┘                  └─────┬─────┘
            │                               │
    ┌───────┼───────────────────────────────┼───────┐
    │       │                               │       │
    ▼       ▼                               ▼       ▼
┌──────────┐ ┌─────────────┐         ┌──────────┐ ┌──────────┐
│ skill-   │ │  mcp-       │         │ ui-ux-   │ │universal │
│ creator  │ │  builder    │         │ pro-max  │ │ devops   │
└──────────┘ └─────────────┘         └──────────┘ └──────────┘
                                      │
                                      ▼
                              ┌──────────────┐
                              │ global-      │
                              │ chinese      │
                              └──────────────┘

┌───────────────────────────────────────────────────────────┐
│                    skills-main（独立）                     │
│  xlsx / docx / pptx / webapp-testing / slack-gif-creator  │
└───────────────────────────────────────────────────────────┘
```

### 11.2 依赖说明

| 依赖方向 | 说明 |
|----------|------|
| **xuansto-skill ↔ sanliu** | 双向集成，sanliu 提供完整流程管理 UI，xuansto-skill 提供底层编排 |
| **xuansto-skill → 其他技能** | xuansto-skill 可调用 ui-ux-pro-max、skill-creator、mcp-builder 等作为子模块 |
| **skills-main 技能** | 独立技能，可被任何其他技能或 Trae IDE 直接调用 |
| **global-chinese** | 作为语言层包装器，可与任何技能组合使用 |

---

## 12. 项目运行方式

### 12.1 快速开始（Web 项目）

```bash
# 1. 创建冲刺规划
/sprint

# 2. 需求澄清
/clarify

# 3. 架构规划
/plan

# 4. 规格编写
/spec

# 5. TDD 实现
/implement

# 6. 测试执行
/test

# 7. 代码审查
/review

# 8. 验收确认
/accept
```

### 12.2 桌面应用开发

```bash
# 在 /accept 之后追加
/build-desktop
/release-desktop
```

### 12.3 知识服务器启动

```python
# 方式 1：直接启动
python .trae/skills/xuansto-skill/scripts/knowledge-server.py

# 方式 2：使用知识服务器模块
cd .trae/skills/xuansto-skill/scripts/knowledge_server
python main.py --host 127.0.0.1 --port 8765
```

### 12.4 知识库初始化

```python
# 构建索引
python .trae/skills/xuansto-skill/scripts/knowledge-index-builder.py

# 执行迁移
python .trae/skills/xuansto-skill/scripts/kb-migrate.py
```

### 12.5 sanliu 前后端启动

#### 后端

```bash
cd .trae/skills/sanliu/backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 前端

```bash
cd .trae/skills/sanliu/frontend
npm install
npm run dev
```

---

## 附录

### A. 参考文档索引（66+）

| 类别 | 文档 |
|------|------|
| **架构** | system-overview.md, module-diagram.md, dependency-graph.md |
| **API** | openapi.yaml, data-models.md, error-codes.md |
| **规范** | coding-standards.md, commit-conventions.md, documentation-standards.md |
| **安全** | security-guidelines.md, owasp-top10-2026.md, owasp-agentic-top10-2026.md, security-frontier-frameworks.md, ai-pentest-frameworks.md, agentic-security-frameworks.md |
| **设计** | design-guidelines.md, color-palettes.md, font-pairings.md, product-reasoning-rules.md, chart-recommendations.md |
| **测试** | test-guidelines.md, e2e-testing.md |
| **桌面** | desktop-dev-guidelines.md, electron-security.md, ipc-contracts.md, platform-matrix.md, build-config.md, signing-setup.md |
| **协议** | a2a-protocol.md, mcp-protocol.md |
| **协作** | collaboration-modes.md, human-collaboration.md |
| **知识库** | knowledge-base-architecture.md, kb-api-reference.md |
| **领域** | business-concepts.md, business-rules.md, user-journeys.md |
| **环境** | dev-setup.md, deployment.md, env-variables.md |
| **术语** | terms.md, abbreviations.md, naming-conventions.md |
| **质量** | quality-gates.md, acceptance-criteria.md |
| **Agent** | agent-registry.md, agent-lifecycle.md |
| **工作流** | workflow-checkpoints.md, iteration-scheduling.md, spec-drift-handling.md |
| **模板** | 19个模板（adr-template.md, api-contract-template.yaml, accessibility-checklist.md 等） |

### B. 模板文件（19个）

| 模板 | 用途 |
|------|------|
| `adr-template.md` | 架构决策记录 |
| `api-contract-template.yaml` | API 合约定义 |
| `accessibility-checklist.md` | 无障碍检查清单 |
| `security-checklist.md` | 安全检查清单 |
| `prd-template.md` | 产品需求文档 |
| `user-story-template.md` | 用户故事模板 |
| `test-plan-template.md` | 测试计划模板 |
| `usability-test-plan.md` | 可用性测试计划 |
| `design-system-template.md` | 设计系统模板 |
| `desktop-build-config-template.yaml` | 桌面构建配置 |
| `flutter-build-config-template.yaml` | Flutter 构建配置 |
| `auto-update-config-template.yaml` | 自动更新配置 |
| `ci-cd-pipeline-template.yaml` | CI/CD 流水线模板 |
| `deployment-plan-template.md` | 部署计划模板 |
| `user-manual-template.md` | 用户手册模板 |
| `rca-template.md` | 根因分析模板 |
| `rfc-template.md` | 请求变更模板 |
| `ipc-contract-template.md` | IPC 合约模板 |
| `design-tokens.json` | 设计令牌 |

---

**文档版本**: 3.2.0 | **最后更新**: 2026-05-07 | **维护者**: skiller-team
