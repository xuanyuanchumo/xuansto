# xuansto-skill

> 多Agent自主开发编排器 | SDD+TDD Fusion System

**版本**：2.0.0  
**许可**：MIT License

---

## 项目概述

xuansto-skill 是一个多Agent自主开发编排器，采用 SDD（Spec-Driven Development）+ TDD（Test-Driven Development）融合系统，实现从需求到发布的全生命周期自动化编排。

**核心能力**：

- **41 Agents**：11层架构，覆盖产品、设计、工程、测试、安全、运维等全角色
- **9-Phase Workflow**（Phase 0-8）：从 UX/UI 设计到桌面构建发布的完整工作流
- **37 Quality Gates**：跨阶段质量门禁，严格保障交付质量
- **Token Optimization**：语义压缩、预算管控、并行降级，优化 Token 消耗
- **Autonomous Iteration & Self-Evolution**：自主迭代与自演化闭环
- **Full-lifecycle Orchestration**：Web + Desktop（Electron/Tauri/Flutter）全平台全生命周期编排

**核心原则**：

| 原则 | 说明 |
|------|------|
| **Spec > Test > Code（STC规则）** | 无规格不开发 \| 无测试不合并 \| 规格变更重审测试 \| 测试失败禁提交 \| 覆盖率≥80% |
| **Karpathy Guidelines** | Think Before Coding \| Simplicity First \| Surgical Changes \| Goal-Driven Execution |
| **跨平台支持** | Web + Desktop（Electron/Tauri/Flutter），平台差异通过 UI Adapter 和 Native Module Agent 自动适配 |
| **[强制] 规则** | 标记 `[强制]` 的规则为不可妥协约束，违反即阻断流程 |

---

## 架构概览

### 11层Agent架构

```
编排层 → 产品层 → 设计层 → 工程层 → 跨平台层 → 数据层 → 测试层 → 安全层 → 运维层 → 质量层 → 文档层
```

| 层级 | Agent角色 |
|------|-----------|
| 编排层 | Orchestrator |
| 产品层 | Product Manager, System Architect, Technical Writer |
| 设计层 | UI Designer, UX Designer, Frontend Stylist |
| 工程层 | Frontend/Backend/Full-Stack/Database/Mobile/DevOps Developer |
| 跨平台层 | Desktop Developer, Desktop UI Adapter, Native Module Developer |
| 数据层 | Data Modeler, DBA, Data Seeder |
| 测试层 | Test Architect, Unit/Integration/E2E/Performance/Security/Desktop/AI-Pentest Tester, QA Engineer, Test Maintainer |
| 安全层 | Security Auditor, Penetration Tester, Compliance Officer |
| 运维层 | CI/CD Specialist, Build & Release Engineer, Monitor Specialist, Runtime Supervisor |
| 质量层 | Code Reviewer, Refactoring Specialist, Doc Reviewer |
| 文档层 | Documentation Engineer, Specification Keeper |

**精简模式**：文件 < 50 自动启用，仅激活编排 + 产品 + 核心工程 + 测试 + 安全。

### 9-Phase SDD+TDD工作流

| Phase | 名称 | 负责Agent | 质量门禁 |
|-------|------|-----------|----------|
| 0 | UX/UI Design | UX/UI Designer | DESIGN-REVIEW, DESIGN-TOKENS |
| 1 | 需求澄清 | Product Manager | GATE-001~002 |
| 2 | 架构与规格 | System Architect | GATE-003~004 |
| 3 | 测试设计 | Test Architect | GATE-005~006 |
| 4 | TDD实现 | FE/BE/Desktop Dev + Code Reviewer | GATE-007~009, FILE-ENCODING, COMMENT-LANGUAGE, SCRIPT-SECURITY, SCRIPT-CLEANUP |
| 5 | 全量验证 | QA Engineer + Security + Perf | GATE-010~012, AGENTIC-SECURITY, AI-PENTEST, PERFORMANCE, SPEC-CONSISTENCY 等 |
| 6 | 验收 | Product Manager | GATE-013~014, INFRA-HEALTH, UX-ACCEPTANCE |
| 7 | 迭代优化 | Orchestrator + Refactoring | GATE-015, DOC-COMPLETENESS |
| 8 | 构建发布(桌面) | Build & Release Engineer | DESKTOP-BUILD, DESKTOP-SIGN, DESKTOP-UPDATE, DESKTOP-CROSS, IPC-CONTRACT |

### 37 Quality Gates

核心分布：Phase 0（设计4项）→ Phase 1-3（GATE-001~006）→ Phase 4（代码5项 + 安全 + 清理）→ Phase 5（测试 + 安全 + 性能 + 视觉10项）→ Phase 6-7（验收 + 迭代5项）→ Phase 8（桌面4项）+ TOKEN-BUDGET（跨阶段）

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
| `/learn` | 知识学习 | | |

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
| `desktop.frameworks` | electron, tauri, flutter | 支持的桌面框架 |
| `desktop.target_platforms` | win, macos, linux | 目标平台 |
| `desktop.code_signing` | required | 代码签名要求 |
| `communication.protocol` | A2A/v1.1 | Agent间通信协议 |
| `communication.mcp_compatible` | true | MCP协议兼容 |
| `security.owasp_top10_enabled` | true | OWASP Top 10 检查 |
| `security.owasp_agentic_top10_enabled` | true | OWASP Agentic Top 10 检查 |
| `token_optimization.budget` | 100000 | Token预算上限 |
| `token_optimization.compression_level` | semantic | 压缩级别（lossless/semantic/selective） |
| `karpathy_guidelines.compliance_threshold` | 0.9 | Karpathy准则合规率阈值 |

---

## 目录结构

```
xuansto-skill/
├── agents/                     # Agent角色定义（11层41个Agent）
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
│   └── documentation/          # 文档层
├── commands/                   # 17个命令定义
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
├── templates/                  # 模板文件
├── workflows/                  # 工作流定义
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

1. **Level 0（完整）**：ChromaDB 向量检索 + SQLite FTS5 关键词检索（混合模式）
2. **Level 1（降级）**：仅 SQLite FTS5 关键词检索
3. **Level 2（最小）**：仅 SQLite 基础检索

---

## 版本历史

详见 [CHANGELOG.md](.knowledge/CHANGELOG.md)

### 废弃脚本说明

以下脚本已标记为废弃，将在后续版本中移除：

| 脚本 | 原因 | 替代方案 |
|------|------|----------|
| `accessibility-test.js` | 使用Math.random模拟结果（假实现） | 使用axe-core + Playwright集成 |
| `visual-regression.js` | 使用Math.random模拟像素对比（假实现） | 使用Playwright截图对比 |
| `performance-benchmark.js` | 与desktop-perf-benchmark.js功能重叠 | 使用desktop-perf-benchmark.js |

---

## 许可证

MIT License
