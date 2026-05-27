# xuansto-skill

> 多Agent自主开发编排器 | SDD+TDD Fusion System

**版本**：4.1.0
**许可**：MIT License

---

## 项目概述

xuansto-skill 是一个多Agent自主开发编排器，采用 SDD（Spec-Driven Development）+ TDD（Test-Driven Development）融合系统，实现从需求到发布的全生命周期自动化编排。

**核心能力**：

- **57 Agents**：13层架构，覆盖产品、设计、工程、测试、安全、运维、质量、文档、知识、监控等全角色
- **9-Phase Workflow**（Phase 0-8）：从初始化与设计到桌面构建发布的完整工作流
- **54 Quality Gates**：跨阶段质量门禁，严格保障交付质量
- **27 Commands**：完整命令集，覆盖全生命周期
- **Token Optimization**：语义压缩、预算管控、并行降级，优化 Token 消耗
- **Autonomous Iteration & Self-Evolution**：自主迭代与自演化闭环
- **Full-lifecycle Orchestration**：Web + Desktop（Electron/Tauri/Flutter）全平台全生命周期编排

**核心原则**：

| 原则 | 说明 |
|------|------|
| **Spec > Test > Code（STC规则）** | 无规格不开发 \| 无测试不合并 \| 规格变更重审测试 \| 测试失败禁提交 \| 覆盖率≥80% |
| **Karpathy Guidelines** | Think Before Coding \| Simplicity First \| Surgical Changes \| Goal-Driven Execution |
| **双动作规则** | 每次迭代必须完成两个动作 |
| **三击协议** | 3次失败→停止→反模式分析→重启 |
| **知识库强制工作流** | 检索→注入→沉淀 |
| **Chesterton栅栏** | 移除代码前必须理解其用途 |
| **跨平台支持** | Web + Desktop（Electron/Tauri/Flutter），平台差异通过 UI Adapter 和 Native Module Agent 自动适配 |
| **[强制] 规则** | 标记 `[强制]` 的规则为不可妥协约束，违反即阻断流程 |

---

## 架构概览

### 13层Agent架构

```
编排层 → 产品层 → 设计层 → 工程层 → 跨平台层 → 数据层 → 测试层 → 安全层 → 运维层 → 质量层 → 文档层 → 知识层 → 监控层
```

| 层级 | Agent角色 |
|------|-----------|
| 编排层 | Orchestrator, Subagent Dispatcher, Task Coordinator |
| 产品层 | Product Manager, Brainstorming Facilitator, System Architect, Technical Writer |
| 设计层 | Design System Generator, Frontend Stylist, UI Designer, UX Designer |
| 工程层 | Frontend/Backend/Full-Stack/Database/Mobile/DevOps Developer |
| 跨平台层 | Desktop Developer, Desktop UI Adapter, Native Module Developer |
| 数据层 | Data Modeler, DBA, Data Seeder |
| 测试层 | Test Architect, Unit/Integration/E2E/Performance/Security/Desktop/AI-Pentest Tester, QA Engineer, Test Maintainer |
| 安全层 | Security Auditor, Penetration Tester, Compliance Officer |
| 运维层 | CI/CD Specialist, Build & Release Engineer, Monitor Specialist, Runtime Supervisor |
| 质量层 | Bug Scanner, Code Reviewer, Comment Verifier, Compliance Reviewer, Doc Reviewer, History Analyzer, Refactoring Specialist |
| 文档层 | Documentation Engineer, Specification Keeper |
| 知识层 | Knowledge Manager, Learning Specialist, Token Optimizer |
| 监控层 | Quality Monitor, Progress Tracker, Decision Logger |

**精简模式**：文件 < 50 自动启用，仅激活编排 + 产品 + 核心工程 + 测试 + 安全。

### 9-Phase SDD+TDD工作流

| Phase | 名称 | 负责Agent | 质量门禁 |
|-------|------|-----------|----------|
| 0 | 初始化与设计 | Design System Generator, UX/UI Designer | DESIGN-SYSTEM-COMPLETE, ANTI-PATTERN-CHECK, DESIGN-REVIEW/* |
| 1 | 需求澄清 | Product Manager, Brainstorming Facilitator | BRAINSTORM-COMPLETE, GATE-001~002 |
| 2 | 架构与规格 | System Architect | PLAN-ATOMIC, GATE-003~004 |
| 3 | 测试设计 | Test Architect | GATE-005~006 |
| 4 | TDD实现 | FE/BE/Desktop Dev + Code Reviewer | SUBAGENT-REVIEW, REVIEW-CONFIDENCE, GATE-007(含U+FFFD检测), TEST-PASS, GATE-009, FILE-ENCODING, SCRIPT-* |
| 5 | 全量验证 | QA Engineer + Security + Perf | PLAYWRIGHT-E2E-PASS, GATE-011(含RENDER-CHECK)~012, AI-PENTEST, SPEC-CONSISTENCY, RENDER-CHECK |
| 6 | 验收 | Product Manager | GATE-013~014, INFRA-HEALTH, UX-ACCEPTANCE |
| 7 | 迭代优化 | Orchestrator + Refactoring | SIMPLIFICATION-BEHAVIOR, CHESTERTON-FENCE, GATE-015 |
| 8 | 构建发布(桌面) | Build & Release Engineer | DESKTOP-BUILD, DESKTOP-SIGN, DESKTOP-UPDATE, DESKTOP-CROSS, IPC-CONTRACT |

### 54 Quality Gates

核心分布：Phase 0（设计系统+反模式3项）→ Phase 1（需求2项）→ Phase 2（架构2项）→ Phase 3（测试2项）→ Phase 4（代码+审查+安全+清理10项）→ Phase 5（测试+安全+性能+视觉+渲染12项）→ Phase 6（验收4项）→ Phase 7（迭代3项）→ Phase 8（桌面5项）+ 跨阶段（PLAN-PERSISTENCE, SESSION-RECOVERY, LOOP-COMPLETION, TOKEN-BUDGET 等）

### 三层知识库

```
通用知识（编码规范/设计模式）→ 工作知识（项目架构/ADR/接口契约）→ 经验知识（修复记录/性能调优）
```

- **存储**：`memory/` 目录存储 patterns/errors/fixes/metrics
- **检索引擎**：SQLite + Chroma 双引擎（FTS5 关键词检索 + 向量语义检索）
- **混合检索策略**：语义权重 0.7 + 关键词权重 0.3，支持 hybrid/semantic_only/keyword_only 三种模式
- **增量同步**：FileSyncDetector + IncrementalSync，通过 mtime 和 hash 比较检测文件变更，支持 add/modify/delete 增量操作
- **双向同步**：KnowledgeExporter 将 DB 变更写回 Markdown 文件，YAML frontmatter 格式存储元数据，循环同步防护
- **生命周期管理**：LifecycleManager 自动归档过时条目（90天未更新 + 置信度 < 0.5），归档条目通过三层过滤（SQL/FTS5/Chroma）从搜索结果中排除

---

## 安装说明

### Skill安装

将 `.trae/skills/xuansto-skill/` 目录复制到项目的 `.trae/skills/` 下即可：

```bash
cp -r .trae/skills/xuansto-skill/ <your-project>/.trae/skills/xuansto-skill/
```

### Python依赖

知识库服务需要以下 Python 依赖：

| 依赖包 | 用途 | 必需 |
|--------|------|------|
| `fastapi` | REST API 框架 | 可选 |
| `uvicorn` | ASGI 服务器 | 可选 |
| `chromadb` | 向量数据库引擎 | 可选 |
| `sentence-transformers` | 本地 Embedding 模型 | 可选 |
| `openai` | OpenAI Embedding API | 可选 |
| `pyyaml` | YAML 配置解析 | 必需 |
| `mcp` | MCP 协议集成 | 可选 |

> 所有可选依赖均支持优雅降级：缺失时自动回退到可用引擎，不影响核心功能运行。

安装命令：

```bash
pip install pyyaml
pip install fastapi uvicorn chromadb sentence-transformers openai mcp
```

---

## 快速开始

基本使用流程：

```
/sprint → /clarify → /plan → /spec → /implement → /test → /review → /accept
```

| 步骤 | 命令 | 说明 |
|------|------|------|
| 1 | `/sprint` | 创建冲刺规划，定义迭代目标 |
| 2 | `/clarify` | 需求澄清，消除歧义 |
| 3 | `/plan` | 架构规划，确定技术方案 |
| 4 | `/spec` | 规格编写，输出 SDD 规格文档 |
| 5 | `/implement` | TDD 实现，先测试后编码 |
| 6 | `/test` | 测试执行，全量验证 |
| 7 | `/review` | 代码审查，质量把关 |
| 8 | `/accept` | 验收确认，完成交付 |

**桌面应用开发**：在 `/accept` 之后追加 `/build-desktop` → `/release-desktop`。

---

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
| `/audit` | 安全审计 | `/agent-status` | Agent状态监控 |
| `/learn` | 知识学习 | `/brainstorm` | 需求探索 |
| `/execute-plan` | 执行计划 | `/design-system` | 设计系统 |
| `/simplify` | 代码简化 | `/loop` | 循环执行 |
| `/cancel-loop` | 取消循环 | `/build` | 项目构建 |
| `/init` | 初始化项目 | `/status` | 状态检查 |
| `/rollback` | 回滚版本 | | |

---

## 配置说明

主配置文件：`configs/default.yaml`

### 关键参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `orchestrator.max_concurrent_agents` | 3 | 单任务最大并发Agent数 |
| `orchestrator.system_parallel_capacity` | 10 | 系统级并行容量上限 |
| `orchestrator.task_timeout_minutes` | 60 | 单任务超时时间（分钟） |
| `orchestrator.retry_policy.backoff` | exponential | 退避策略（指数退避） |
| `orchestrator.retry_policy.max_retries` | 3 | 最大重试次数 |
| `quality_gates.enforcement` | strict | 质量门禁执行模式 |
| `quality_gates.coverage_threshold.unit` | 80% | 单元测试覆盖率阈值 |
| `karpathy_guidelines.compliance_threshold` | 0.9 | Karpathy准则合规率阈值 |
| `token_optimization.budget` | 100000 | Token预算上限 |
| `token_optimization.compression_level` | semantic | 压缩级别（lossless/semantic/selective） |
| `desktop.frameworks` | electron, tauri, flutter | 支持的桌面框架 |
| `desktop.target_platforms` | win, macos, linux | 目标平台 |
| `desktop.code_signing` | required | 代码签名要求 |
| `communication.protocol` | A2A/v1.1 | Agent间通信协议 |
| `communication.mcp_compatible` | true | MCP协议兼容 |
| `security.owasp_top10_enabled` | true | OWASP Top 10 检查 |
| `security.owasp_agentic_top10_enabled` | true | OWASP Agentic Top 10 检查 |

---

## 目录结构

```
xuansto-skill/
├── agents/                     # Agent角色定义（13层57个Agent）
│   ├── orchestrator/           # 编排层
│   ├── product/                # 产品层
│   ├── design/                 # 设计层
│   ├── engineering/            # 工程层
│   ├── cross-platform/         # 跨平台层
│   ├── database/               # 数据层
│   ├── testing/                # 测试层
│   ├── security/               # 安全层
│   ├── devops/                 # 运维层
│   ├── quality/                # 质量层
│   ├── documentation/          # 文档层
│   ├── knowledge/              # 知识层
│   └── monitoring/             # 监控层
├── commands/                   # 27个命令定义
├── configs/                    # 配置文件
│   └── default.yaml            # 默认配置
├── examples/                   # 使用示例
│   ├── web-app-development.md
│   └── desktop-app-development.md
├── memory/                     # 经验记忆存储
│   ├── patterns/               # 模式记录
│   ├── errors/                 # 错误记录
│   ├── fixes/                  # 修复记录
│   └── metrics/                # 指标记录
├── references/                 # 参考文档
├── scripts/                    # 工具脚本
│   ├── knowledge_server/       # 知识库服务脚本
│   ├── verification/           # 验证脚本
│   └── workflow-tools/         # 工作流工具脚本
├── templates/                  # 模板文件
├── workflows/                  # 工作流定义
├── .agent_cache/               # Agent缓存
├── .skill-logs/                # 技能日志
└── .knowledge/                 # 知识库数据
    ├── general/                # 通用知识
    ├── workspace/              # 工作知识
    ├── experience/             # 经验知识
    ├── index/                  # 索引数据
    └── backup/                 # 备份数据
```

---

## 知识库服务

### 启动服务

```bash
python scripts/knowledge-server.py --port 8765
```

默认监听 `127.0.0.1:8765`，支持 `--host` 和 `--port` 参数自定义。

### REST API端点

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/v1/knowledge/search` | 搜索知识条目（支持 hybrid/semantic/keyword 策略） |
| GET | `/v1/knowledge/get/{entry_id}` | 获取指定知识条目 |
| POST | `/v1/knowledge/add` | 添加知识条目（支持自动去重） |
| PUT | `/v1/knowledge/update/{entry_id}` | 更新知识条目 |
| DELETE | `/v1/knowledge/delete/{entry_id}` | 删除知识条目 |
| GET | `/v1/knowledge/health` | 服务健康检查 |
| GET | `/v1/knowledge/{entry_id}/versions` | 获取条目版本历史 |
| POST | `/v1/knowledge/rollback` | 回滚知识条目到指定版本 |
| POST | `/v1/knowledge/backup` | 触发知识库备份 |
| GET | `/v1/health/consistency` | 数据一致性检查 |

### MCP Tools

| 工具名 | 说明 |
|--------|------|
| `knowledge_search` | 搜索知识库条目，支持 hybrid/semantic/keyword 策略及过滤条件 |
| `knowledge_add` | 添加知识条目，支持自动去重检测 |
| `knowledge_update` | 更新已有知识条目 |
| `knowledge_delete` | 删除指定知识条目 |
| `knowledge_rollback` | 回滚知识条目到指定版本 |

### WebSocket通知

服务提供 WebSocket 端点 `ws://127.0.0.1:8765/ws`，支持实时知识库变更通知。

### 三级降级策略

当可选依赖缺失时，检索引擎自动降级：

1. **L1（完整）**：ChromaDB 向量检索 + SQLite FTS5 关键词检索（混合模式）
2. **L2（本地语义）**：本地 Embedding + SQLite FTS5（OpenAI 不可用时）
3. **L3（BM25 Only）**：仅 SQLite FTS5 关键词检索（向量引擎不可用时）

> 知识库还包含蒸馏模块，支持经验知识的自动提炼与沉淀。

---

## 版本历史

详见 [CHANGELOG.md](.knowledge/CHANGELOG.md)

### 脚本更新说明

以下脚本已从模拟实现重写为真实Playwright集成：

| 脚本 | 更新内容 | 当前实现 |
|------|----------|----------|
| `accessibility-test.js` | 替换Math.random模拟为真实WCAG审计 | @axe-core/playwright + Playwright |
| `visual-regression.js` | 替换Math.random模拟为真实截图对比 | Playwright + pixelmatch，支持组件级截图和diff图像输出 |
| `performance-benchmark.js` | 与desktop-perf-benchmark.js合并为统一脚本 | Playwright Performance API，支持web/desktop双平台 |

---

## 许可证

MIT License
