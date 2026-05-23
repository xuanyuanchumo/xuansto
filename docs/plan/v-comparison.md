# Xuansto Skill 版本功能对比文档

> 版本: 2.0.0 | 日期: 2026-05-23 | 状态: 已实施

---

## 目录

1. [版本概览](#1-版本概览)
2. [架构形态对比](#2-架构形态对比)
3. [核心功能对比](#3-核心功能对比)
4. [性能对比](#4-性能对比)
5. [特效加载方式对比](#5-特效加载方式对比)
6. [API契约对比](#6-api契约对比)
7. [数据模型对比](#7-数据模型对比)
8. [已知限制对比](#8-已知限制对比)
9. [版本演进路线图](#9-版本演进路线图)

---

## 1. 版本概览

| 属性 | V_PREVIOUS_MAJOR | V_CURRENT | v8.2.0 / v4.3.0 | v9.0.0 / v9.0.0 |
|------|-------------------|-----------|-------------------|-------------------|
| **Skill版本** | xuansto-skill v1.0.0 | xuansto-skill-v2 v8.0.0 | xuansto-skill-v2 v8.2.0 | xuansto-skill-v2 v9.0.0 |
| **MCP Server版本** | 无 | xuansto-mcp-server v8.0.0 | xuansto-mcp-server v4.3.0 | xuansto-mcp-server v9.0.0 |
| **原始名称** | multi-agent-sdd-tdd-orchestrator | xuansto-skill-v2 | xuansto-skill-v2 | xuansto-skill-v2 |
| **Agent数量** | 35 | 57 | 57 | 57+ |
| **编排层数** | 8 | 13 | 13 | 13 |
| **工作流数** | 8 | 15 | 15 | 15+ |
| **命令数** | 13 | 27 | 27 | 27+ |
| **MCP Tool数** | 0 | 19+ | 19 | 21+ |
| **MCP Resource数** | 0 | 8+ | 8 | 10+ |
| **质量门禁** | 15 | 54 | 54 | 54+ |
| **降级脚本** | 12 | 60+ | 60+ | 60+ |
| **模板数** | 12 | 19 | 19 | 19+ |
| **参考文档** | 14 | 75+ | 10+ | 15+ |
| **SKILL.md行数** | ~765 | <200 | ~71 | <200 |

---

## 2. 架构形态对比

### 2.1 整体架构

| 维度 | V_PREVIOUS_MAJOR | V_CURRENT | v8.2.0 / v4.3.0 | v9.0.0 / v9.0.0 |
|------|-------------------|-----------|-------------------|-------------------|
| **架构模式** | 单体Skill | Skill层 + MCP Server双层 | Skill层 + MCP Server双层 | Skill层 + MCP Server双层 + 数据层统一 |
| **Skill层职责** | 全部（触发+路由+执行+降级） | 触发+路由+声明+约束 | 触发+路由+声明+约束 | 触发+路由+声明+约束 |
| **执行层** | 内嵌脚本直接调用 | + MCP Server独立进程 | + MCP Server独立进程 | + MCP Server独立进程 |
| **通信协议** | 无（文件系统直读） | + MCP协议(stdio) | + MCP协议(stdio) | + MCP协议(stdio) |
| **进程模型** | 单进程 | 双进程(Skill + MCP Server) | 双进程(Skill + MCP Server) | 双进程(Skill + MCP Server) |
| **配置管理** | 内嵌SKILL.md | + 外部化YAML+热重载MCP入口 | + 外部化YAML + Schema校验 | + 外部化YAML + Schema校验 + 热重载MCP入口 |
| **降级架构** | 无统一降级 | 统一降级框架(异步+完整链) | + 统一降级框架 | + 完整降级+恢复+抖动 |

### 2.2 架构分层

| 分层 | V_PREVIOUS_MAJOR | V_CURRENT | v8.2.0 / v4.3.0 | v9.0.0 / v9.0.0 |
|------|-------------------|-----------|-------------------|-------------------|
| **Skill层** | SKILL.md(765行，全内嵌) | SKILL.md(<200行)+外部YAML | SKILL.md(71行)+外部YAML | SKILL.md(<200行)+外部YAML |
| **执行层** | 无 | 19+ MCP Tool + 8+ Resource | + 19 MCP Tool + 8 Resource | + 21 MCP Tool + 10 Resource |
| **资源层** | agents/commands/scripts | + references/templates/workflows | + references补全 | + 统一数据层 |
| **依赖层** | Python脚本 | + mcp[cli]+pydantic+pyyaml | + mcp[cli]+pydantic+pyyaml | + mcp[cli]+pydantic+pyyaml |

---

## 3. 核心功能对比

### 3.1 Agent体系

| 维度 | V_PREVIOUS_MAJOR | V_CURRENT | v8.2.0 / v4.3.0 | v9.0.0 / v5.0.0 |
|------|-------------------|-----------|-------------------|-------------------|
| **Agent数量** | 35 | 57 ↑ | 57 | 57+ |
| **编排层数** | 8 | 13 ↑ | 13 | 13 |
| **Agent注册方式** | SKILL.md内嵌索引 | + 外部registry.yaml | + 外部registry.yaml | + 外部registry.yaml |
| **模型路由** | 无 | + fast/standard/deep三级 | + fast/standard/deep三级 | + fast/standard/deep三级 |
| **Agent合并策略** | 无 | 声明但未执行 | + 运行时合并执行 | + 运行时合并执行 |
| **Agent动态创建** | 无 | + agent_status(create) | + agent_status(create) | + agent_manage(create) |
| **Agent调度** | 静态分配 | + Phase感知调度 | + Phase感知调度 | + Phase感知+规模自适应调度 |

### 3.2 工作流

| 维度 | V_PREVIOUS_MAJOR | V_CURRENT | v8.2.0 / v4.3.0 | v9.0.0 / v5.0.0 |
|------|-------------------|-----------|-------------------|-------------------|
| **工作流数** | 8 | 15 ↑ | 15 | 15+ |
| **Phase数** | 8 | 9 ↑ (含Phase 0初始化) | 9 | 9 |
| **工作流定义** | SKILL.md内描述 | + 独立YAML+MD文件 | + 独立YAML+MD文件 | YAML为权威源，MD由YAML生成 |
| **工作流调度** | 手动Phase推进 | + MCP workflow_dispatch | + MCP workflow_dispatch | + MCP workflow_dispatch |
| **工作流快照** | 无 | + gzip压缩快照 | + gzip压缩快照 | + gzip压缩快照+加密 |
| **工作流恢复** | 无 | + recover action | + recover action | + recover action |
| **SDD+TDD融合** | 基础 | + full/medium/fast三档 | + full/medium/fast三档 | + full/medium/fast三档 |

### 3.3 质量门禁

| 维度 | V_PREVIOUS_MAJOR | V_CURRENT | v8.2.0 / v4.3.0 | v9.0.0 / v5.0.0 |
|------|-------------------|-----------|-------------------|-------------------|
| **门禁数量** | 15 | 54 ↑ | 54 | 54+ |
| **门禁检查方式** | 脚本检查 | + MCP quality_gate_check | + MCP quality_gate_check | + MCP quality_gate_check |
| **3-Strike协议** | 无 | + 自动修复→换策略→升级 | + 自动修复→换策略→升级 | + 自动修复→换策略→升级 |
| **容差规则** | 无 | + 数值±0.5%/比率2%/布尔无/安全无 | + 数值±0.5%/比率2%/布尔无/安全无 | + 数值±0.5%/比率2%/布尔无/安全无 |
| **门禁异常** | 无 | + PASS_WITH_NOTE+WARN+BLOCK | + PASS_WITH_NOTE+WARN+BLOCK | + PASS_WITH_NOTE+WARN+BLOCK |

### 3.4 知识管理

| 维度 | V_PREVIOUS_MAJOR | V_CURRENT | v8.2.0 / v4.3.0 | v9.0.0 / v5.0.0 |
|------|-------------------|-----------|-------------------|-------------------|
| **知识检索** | 无 | + knowledge_search(retrieve) | + knowledge_search(retrieve) | + knowledge_search(retrieve) |
| **知识注入** | 无 | + knowledge_inject(inject) | + knowledge_inject(inject) | + knowledge_inject(inject) |
| **经验沉淀** | 无 | + knowledge_inject(precipitate) | + knowledge_inject(precipitate) | + knowledge_inject(precipitate) |
| **搜索降级链** | 无 | HybridSearchEngine: ChromaDB(可选)→SQLite FTS→关键词 | ChromaDB→SQLite FTS→关键词 | + SQLite FTS5+BM25为主，ChromaDB可选增强 |
| **ChromaDB依赖** | 无 | 可选增强(默认BM25) | 必需(降级频繁) | ↓ 可选增强(默认BM25) |
| **知识闭环** | 无 | Retrieve→Inject→Precipitate完整闭环 | Retrieve→Inject→Precipitate | Retrieve→Inject→Precipitate完整闭环 |
| **职责边界** | 无 | knowledge_search只读，knowledge_inject只写 | + knowledge_search只读，knowledge_inject只写 | + knowledge_search只读，knowledge_inject只写 |

### 3.5 安全能力

| 维度 | V_PREVIOUS_MAJOR | V_CURRENT | v8.2.0 / v4.3.0 | v9.0.0 / v5.0.0 |
|------|-------------------|-----------|-------------------|-------------------|
| **安全扫描** | OWASP Top 10 | + OWASP Agentic Top 10 ↑ | + OWASP Agentic Top 10 | + OWASP Agentic Top 10 |
| **依赖扫描** | 无 | + dependency漏洞扫描 | + dependency漏洞扫描 | + dependency漏洞扫描 |
| **路径安全** | 无 | + validator.py防遍历 | + validator.py防遍历 | + validator.py防遍历 |
| **Hook安全阻断** | 无 | + security-block Hook | + security-block Hook | + security-block Hook(失败默认阻塞) |
| **编码安全** | UTF-8检查 | + UTF-8无BOM+无U+FFFD | + UTF-8无BOM+无U+FFFD | + UTF-8无BOM+无U+FFFD |
| **速率限制** | 无 | + 令牌桶速率限制 | 无 | + 令牌桶速率限制 |
| **模板参数白名单** | 无 | + name参数正则白名单 | 无 | + name参数正则白名单 |
| **快照加密** | 无 | + AES-256-GCM可选加密 | 无 | + AES-256-GCM可选加密 |

### 3.6 会话与决策

| 维度 | V_PREVIOUS_MAJOR | V_CURRENT | v8.2.0 / v4.3.0 | v9.0.0 / v5.0.0 |
|------|-------------------|-----------|-------------------|-------------------|
| **会话管理** | 无 | + session_manage(7种action) | + session_manage(7种action) | + session_manage(7种action) |
| **会话持久化** | 无 | + save/load/track/restore | + save/load/track/restore | + save/load/track/restore |
| **决策日志** | 无 | + decision_log(6种action) | + decision_log(6种action) | + decision_log(6种action) |
| **决策透明化** | 无 | + ADR集成 | + ADR集成 | + ADR集成+Workflow关联 |
| **会话状态存储** | 无 | + 统一SQLite+MD双写 | JSON+MD分散 | + 统一SQLite+MD双写 |

---

## 4. 性能对比

### 4.1 启动与加载

| 维度 | V_PREVIOUS_MAJOR | V_CURRENT | v8.2.0 / v4.3.0 | v9.0.0 / v5.0.0 |
|------|-------------------|-----------|-------------------|-------------------|
| **SKILL.md体积** | ~765行(全量加载) | ~71行 ↓(骨架加载) | ~71行 | <200行 |
| **初始Token占用** | 全量(估计50K+) | ≤2K ↓(Phase 0骨架) | ≤2K | ≤2K |
| **加载方式** | 一次性全量 | + 渐进式4阶段 | + 渐进式4阶段 | + 渐进式4阶段+运行时协商 |
| **Phase 0→1推进延迟** | N/A | ≤500ms(目标) | ≤500ms | ≤500ms |
| **Phase 1→2推进延迟** | N/A | ≤2000ms(目标) | ≤2000ms | ≤2000ms |
| **Phase 2→3推进延迟** | N/A | ≤5000ms(目标) | ≤5000ms | ≤5000ms |
| **降级切换延迟** | N/A | ≤100ms(目标) | ≤100ms | ≤100ms |

### 4.2 运行时性能

| 维度 | V_PREVIOUS_MAJOR | V_CURRENT | v8.2.0 / v4.3.0 | v9.0.0 / v5.0.0 |
|------|-------------------|-----------|-------------------|-------------------|
| **MCP调用延迟** | N/A | 依赖MCP Server | 依赖MCP Server | 依赖MCP Server |
| **降级脚本调用** | 同步subprocess.run | 同步subprocess.run(阻塞事件循环) | + asyncio异步调用 ↑ | + asyncio异步调用 |
| **知识检索** | 无 | ChromaDB优先(降级频繁) | ChromaDB优先(降级频繁) | + BM25为主(稳定) ↑ |
| **Token预算控制** | 无 | + 三级降级(L1/L2/L3) | + 三级降级(L1/L2/L3) | + 三级降级(L1/L2/L3)+动态调整 |
| **上下文压缩** | 无 | + semantic/selective/lossless | + semantic/selective/lossless | + semantic/selective/lossless+精确Token估算 |
| **资源缓存命中率** | N/A | ≥80%(目标) | ≥80%(目标) | ≥80% |
| **最大并发MCP调用** | N/A | 10 | 10 | 10 |

### 4.3 Token预算分配

| Phase | V_PREVIOUS_MAJOR | V_CURRENT | v8.2.0 / v4.3.0 | v9.0.0 / v5.0.0 |
|-------|-------------------|-----------|-------------------|-------------------|
| Phase 0 骨架 | N/A | ≤2K | ≤2K | ≤2K |
| Phase 1 功能 | N/A | ≤5K | ≤5K | ≤5K |
| Phase 2 增强 | N/A | ≤10K | ≤10K | ≤10K |
| Phase 3 完整 | N/A | ≤20K | ≤20K | ≤20K |
| Token降级L1 | N/A | ≥80%→减少并行+MCP降级 | ≥80%→减少并行+MCP降级 | ≥80%→减少并行+MCP降级 |
| Token降级L2 | N/A | ≥95%→精简模式(≤15 Agent) | ≥95%→精简模式(≤15 Agent) | ≥95%→精简模式(≤15 Agent) |
| Token降级L3 | N/A | 100%→最小串行(3 Agent) | 100%→最小串行(3 Agent) | 100%→最小串行(3 Agent) |

---

## 5. 特效加载方式对比

### 5.1 渐进式加载

| 维度 | V_PREVIOUS_MAJOR | V_CURRENT | v8.2.0 / v4.3.0 | v9.0.0 / v5.0.0 |
|------|-------------------|-----------|-------------------|-------------------|
| **加载模型** | 无(全量) | + 4阶段加载 | + 4阶段加载 | + 4阶段加载 |
| **触发机制** | 无 | + 自动+显式+披露触发 | + 自动+显式+披露触发 | + 自动+显式+披露触发+运行时协商 |
| **状态机** | 无 | + 单向推进+Token降级 | + 单向推进+Token降级 | + 单向推进+Token降级+DisclosureTransition |
| **DisclosureTransition** | 无 | Schema已定义但未使用 ↓ | + 启用 ↑ | + 完整实现 |
| **Phase转换通知** | 无 | 无 | + MCP Notification ↑ | + MCP Notification |
| **进度反馈** | 无 | + loading_progress action | + loading_progress action | + loading_progress action |
| **资源优先级** | 无 | + P0-P3四级 | + P0-P3四级 | + P0-P3四级 |
| **按需加载策略** | 无 | + lazy加载 | + lazy加载 | + lazy加载 |
| **Phase感知卸载** | 无 | + phase_transition_rules | + phase_transition_rules | + phase_transition_rules |

### 5.2 披露规则

| 维度 | V_PREVIOUS_MAJOR | V_CURRENT | v8.2.0 / v4.3.0 | v9.0.0 / v5.0.0 |
|------|-------------------|-----------|-------------------|-------------------|
| **功能不可用提示** | 无 | + xuansto://loading/status | + xuansto://loading/status | + xuansto://loading/status |
| **推进提示** | 无 | + resource_load_status(preload) | + resource_load_status(preload) | + resource_load_status(preload) |
| **降级到可用范围** | 无 | + on_unavailable 3步披露 | + on_unavailable 3步披露 | + on_unavailable 3步披露 |
| **Token降级自动回退** | 无 | + 自动降级(不可逆) | + 自动降级(不可逆) | + 自动降级(不可逆)+显式恢复 |

### 5.3 Hook系统

| 维度 | V_PREVIOUS_MAJOR | V_CURRENT | v8.2.0 / v4.3.0 | v9.0.0 / v5.0.0 |
|------|-------------------|-----------|-------------------|-------------------|
| **Hook引擎** | 无 | + hook_engine.py | + hook_engine.py | + hook_engine.py |
| **Hook配置** | 无 | + hooks.json(3级profile) | + hooks.json(3级profile) | + hooks.json(3级profile) |
| **Hook类型安全** | 无 | 字符串(易拼写错误) ↓ | + HookType枚举 ↑ | + HookType枚举 |
| **Hook生命周期** | 无 | + PreToolUse/PostToolUse/SessionStart/Stop/PreCompact | + 5种生命周期 | + 5种生命周期 |
| **Hook失败处理** | 无 | 不阻塞主流程(安全检查可能被跳过) ↓ | + 安全类Hook失败默认阻塞 ↑ | + 安全类Hook失败默认阻塞 |
| **Hook降级覆盖** | 无 | 部分(encoding-check/token-budget-check/session-save) ↓ | + 每个Hook独立降级脚本 ↑ | + 每个Hook独立降级脚本 |
| **Hook失败告警** | 无 | 无 | + 失败计数+告警阈值 ↑ | + 失败计数+告警阈值 |

---

## 6. API契约对比

### 6.1 MCP Tool接口

| 维度 | V_PREVIOUS_MAJOR | V_CURRENT | v8.2.0 / v4.3.0 | v9.0.0 / v5.0.0 |
|------|-------------------|-----------|-------------------|-------------------|
| **Tool数量** | 0 | 17 | 19 ↑ | 21+ ↑ |
| **API版本** | N/A | 2.0.0(最低兼容1.0.0) | 2.0.0(最低兼容1.0.0) | 3.0.0(最低兼容2.0.0) |
| **传输方式** | N/A | stdio | stdio | stdio |
| **输入校验** | N/A | + Pydantic BaseModel(extra="forbid") | + Pydantic BaseModel(extra="forbid") | + Pydantic BaseModel(extra="forbid") |
| **Tool注册方式** | N/A | FastMCP装饰器+内部API ↓ | + 本地Tool注册映射表 ↑ | + 本地Tool注册映射表 |
| **版本协商** | N/A | negotiate_version(不完整) ↓ | + 完整版本协商+功能列表 ↑ | + 完整版本协商+功能列表 |

### 6.2 Tool职责演变

| Tool | V_PREVIOUS_MAJOR | V_CURRENT | v8.2.0 / v4.3.0 | v9.0.0 / v5.0.0 |
|------|-------------------|-----------|-------------------|-------------------|
| skill_analyze | 无 | + analyze | + analyze | + analyze |
| knowledge_search | 无 | + retrieve/inject/precipitate(职责模糊) ↓ | + retrieve(只读) ↑ | + retrieve(只读) |
| knowledge_inject | 无 | + inject/list_available/precipitate | + inject/precipitate(统一写入) ↑ | + inject/precipitate(统一写入) |
| quality_gate_check | 无 | + check(54门禁) | + check(54门禁) | + check(54门禁) |
| spec_drift_detect | 无 | + detect | + detect | + detect |
| security_scan | 无 | + scan | + scan | + scan |
| code_simplify | 无 | + simplify | + simplify | + simplify |
| session_manage | 无 | + 7种action | + 7种action | + 7种action |
| workflow_dispatch | 无 | + 6种action | + 6种action | + 6种action |
| agent_status | 无 | + 10种action(查询+变更混合) ↓ | + 查询类(5种) ↑ | + 查询类(5种) |
| agent_manage | 无 | 无 | + 新增(变更类5种action) ↑ | + 变更类(5种action) |
| hook_manage | 无 | + list/execute | + list/execute | + list/execute |
| resource_load_status | 无 | + 6种action | + 6种action+disclosure_transition ↑ | + 6种action+disclosure_transition |
| context_compress | 无 | + compress | + compress | + compress+精确Token估算 |
| server_health | 无 | + check/negotiate_version | + check/negotiate_version/capabilities ↑ | + check/negotiate_version/capabilities |
| decision_log | 无 | + 6种action | + 6种action | + 6种action |
| token_budget | 无 | + 4种action | + 4种action | + 4种action |
| project_init | 无 | + 3种action | + 3种action | + 3种action |
| metrics_report | 无 | 无 | + 新增(按Tool/时间/类型查询) ↑ | + 按Tool/时间/类型查询 |
| config_manage | 无 | 无 | + 新增(reload/status/validate) ↑ | + reload/status/validate |

### 6.3 MCP Resource接口

| Resource | V_PREVIOUS_MAJOR | V_CURRENT | v8.2.0 / v4.3.0 | v9.0.0 / v5.0.0 |
|----------|-------------------|-----------|-------------------|-------------------|
| xuansto://config/skill | 无 | + 静态 | + 静态 | + 静态 |
| xuansto://references/quality-gates | 无 | + 静态 | + 静态 | + 静态 |
| xuansto://references/agent-registry | 无 | + 静态 | + 静态 | + 静态 |
| xuansto://references/workflow-phases | 无 | + 静态 | + 静态 | + 静态 |
| xuansto://templates/{name} | 无 | + 参数化 | + 参数化 | + 参数化 |
| xuansto://sessions/latest | 无 | + 静态 | + 静态 | + 参数化sessions/{id} ↑ |
| xuansto://loading/status | 无 | + 静态(JSON) | + 静态(JSON) | + 静态(JSON) |
| xuansto://degradation/status | 无 | 无 | + 新增(JSON) ↑ | + JSON |
| xuansto://metrics/summary | 无 | 无 | + 新增(JSON) ↑ | + JSON |
| xuansto://agents/{layer}/{name} | 无 | 无 | 无 | + 参数化 ↑ |

### 6.4 响应格式

| 维度 | V_PREVIOUS_MAJOR | V_CURRENT | v8.2.0 / v4.3.0 | v9.0.0 / v5.0.0 |
|------|-------------------|-----------|-------------------|-------------------|
| **统一响应格式** | 无 | + JSON(status/data/metadata) | + JSON(status/data/metadata) | + JSON(status/data/metadata) |
| **错误码体系** | 无 | code+error_code并存(语义混淆) ↓ | + 统一error_code ↑ | + 统一error_code |
| **降级标识** | 无 | + degraded字段 | + degraded字段+source:"fallback" | + degraded字段+source:"fallback" |
| **重试策略** | 无 | + 指数退避(瞬态3次/永久0次) | + 指数退避(瞬态3次/永久0次) | + 指数退避+抖动(瞬态3次/永久0次) |
| **退避抖动** | 无 | 无(可能雪崩) ↓ | + 随机抖动 ↑ | + 随机抖动 |

---

## 7. 数据模型对比

### 7.1 存储介质

| 维度 | V_PREVIOUS_MAJOR | V_CURRENT | v8.2.0 / v4.3.0 | v9.0.0 / v9.0.0 |
|------|-------------------|-----------|-------------------|-------------------|
| **SQLite** | 无 | 1个(xuansto.db统一8表) | 2个 | + 统一xuansto.db ↑ |
| **ChromaDB** | 无 | 1个(可选增强) | 1个(向量搜索) | ↓ 可选增强 |
| **JSON文件** | 无 | ~3类(已迁移到SQLite) | ~8类 | ↓ 迁移到SQLite |
| **YAML文件** | 无 | ~4类(+Pydantic Schema校验) | + Pydantic Schema校验 | + Pydantic Schema校验 |
| **Markdown文件** | 无 | ~3类(双写) | ~3类 | + 双写(人类可读快照) |
| **内存缓存** | 无 | + LRU缓存(cache.py)+持久化 | ~8类(无持久化) | + 持久化到SQLite ↑ |
| **gzip快照** | 无 | 1个(+AES-256-GCM加密) | 1个(无加密) | + AES-256-GCM可选加密 ↑ |

### 7.2 关键数据实体

| 实体 | V_PREVIOUS_MAJOR | V_CURRENT | v8.2.0 / v4.3.0 | v9.0.0 / v9.0.0 |
|------|-------------------|-----------|-------------------|-------------------|
| **knowledge_entries** | 无 | + 统一SQLite+软删除 ↑ | + SQLite+ChromaDB+MD | + 统一SQLite+软删除 ↑ |
| **WorkflowInstance** | 无 | + SQLite+Decision关联 ↑ | + JSON文件 | + SQLite+Decision关联 ↑ |
| **SessionState** | 无 | + 统一SQLite ↑ | + JSON+MD分散 | + 统一SQLite ↑ |
| **DecisionRecord** | 无 | + 统一SQLite ↑ | + SQLite(decisions.db) | + 统一SQLite ↑ |
| **ResourceLoadState** | 无 | + SQLite ↑ | + JSON(resource_state.json) | + SQLite ↑ |
| **DegradationState** | 无 | + SQLite ↑ | + JSON(degradation_state.json) | + SQLite ↑ |
| **ErrorPattern** | 无 | + SQLite+error_type分类 ↑ | + JSON(pattern-*.json) | + SQLite+error_type分类 ↑ |
| **MetricsSnapshot** | 无 | + SQLite+TTL自动清理 ↑ | + JSON(metrics_*.json) | + SQLite+TTL自动清理 ↑ |

### 7.3 数据一致性

| 维度 | V_PREVIOUS_MAJOR | V_CURRENT | v8.2.0 / v4.3.0 | v9.0.0 / v9.0.0 |
|------|-------------------|-----------|-------------------|-------------------|
| **原子写入** | 无 | + atomic_write(tmpfile+os.replace) | + atomic_write | + atomic_write |
| **竞态保护** | 无 | + 写入锁+hash验证 ↑ | + 写入锁+完整性校验 | + 写入锁+完整性校验 |
| **崩溃恢复** | 无 | + atexit注册+hash验证 ↑ | + atexit注册+校验和 | + atexit注册+校验和 |
| **跨库事务** | N/A | + 统一SQLite ↑ | 无(SQLite分散) | + 统一SQLite ↑ |
| **缓存淘汰** | 无 | + LRU淘汰策略(cache.py) ↑ | 无LRU | + LRU淘汰策略 ↑ |
| **指标清理** | 无 | + TTL自动清理(30天) ↑ | 无(文件膨胀) | + TTL自动清理(30天) ↑ |

---

## 8. 已知限制对比

### 8.1 限制清单

| 限制 | V_PREVIOUS_MAJOR | V_CURRENT | v8.2.0 / v4.3.0 | v9.0.0 / v9.0.0 |
|------|-------------------|-----------|-------------------|-------------------|
| **降级机制不完整** | 无降级 | ↑ 统一降级框架(异步) | ↑ 统一降级框架 | ↑ 完整降级+恢复 |
| **参考文档不足** | 14个(完整) | ↑ 75+文件(完整) | ↑ 补全到10+ | ↑ 补全到15+ |
| **状态持久化竞态** | N/A | ↑ 统一SQLite+写入锁+hash验证 | ↑ 写入锁+校验 | ↑ 统一SQLite |
| **Tool注册依赖内部API** | N/A | ↑ 本地_TOOL_FUNCTIONS注册表 | ↑ 本地注册映射表 | ↑ 本地注册映射表 |
| **版本协商不完整** | N/A | ↑ MCP v8.0.0完整协商 | ↑ MCP升级到4.3.0+ | ↑ 完整协商 |
| **knowledge职责模糊** | N/A | ↑ search只读/inject只写 | ↑ search只读/inject只写 | ↑ search只读/inject只写 |
| **ChromaDB降级频繁** | N/A | ↑ 可选增强(HybridSearchEngine) | ✗ 必需依赖 | ↑ 可选增强(BM25为主) |
| **降级脚本同步阻塞** | N/A | ↑ asyncio异步调用 | ↑ asyncio异步调用 | ↑ asyncio异步调用 |
| **Tool职责过载** | N/A | ↑ 拆分为agent_status+agent_manage | ↑ 拆分为agent_status+agent_manage | ↑ 拆分完成 |
| **Hook类型不安全** | N/A | ↑ HookType枚举+安全阻断 | ↑ HookType枚举 | ↑ HookType枚举 |
| **通知系统空实现** | N/A | ↑ MCPNotificationCallback | ↑ MCPNotificationCallback | ↑ MCPNotificationCallback |
| **错误码混淆** | N/A | ↑ 统一error_code, deprecated code | ↑ 统一error_code | ↑ 统一error_code |
| **退避无抖动** | N/A | ↑ backoff jitter | ↑ 随机抖动 | ↑ 随机抖动 |
| **YAML无Schema校验** | N/A | 待实施 | ↑ Pydantic校验 | ↑ Pydantic校验 |
| **SKILL.md行数** | ✗ 765行(超限) | ↑ <200行 | ↑ 71行 | ↑ <200行 |
| **v1/v2文件重复** | N/A | ↑ v1标记ARCHIVED | ✗ 两版本并存 | ↑ v1归档，v2唯一维护 |
| **缺少CHANGELOG** | ✗ 无 | 待实施 | ↑ v2 CHANGELOG | ↑ v2 CHANGELOG |
| **缺少评估配置** | ✗ 无 | 待实施 | ↑ 从v1迁移 | ↑ 从v1迁移 |
| **缺少速率限制** | N/A | ↑ 令牌桶限流 | ✗ 无 | ↑ 令牌桶限流 |
| **快照无加密** | N/A | ↑ AES-256-GCM可选 | ✗ 无 | ↑ AES-256-GCM可选 |
| **缓存无LRU** | N/A | ↑ LRU淘汰(cache.py) | ✗ 内存不可控 | ↑ LRU淘汰 |
| **指标无清理** | N/A | ↑ TTL自动清理(30天) | ✗ 磁盘膨胀 | ↑ TTL自动清理 |
| **知识无软删除** | N/A | ↑ deleted_at软删除 | ✗ 注入知识不可撤销 | ↑ deleted_at软删除 |

### 8.2 限制统计

| 版本 | ✗ 废弃/未解决 | ↑ 已修复/改善 | 待实施 | 修复率 |
|------|--------------|-------------|--------|--------|
| V_PREVIOUS_MAJOR | 3 | 0 | 0 | 0% |
| V_CURRENT | 0 | 19 | 4 | 83% |
| v8.2.0 / v4.3.0 | 7 | 16 | 0 | 70% |
| v9.0.0 / v9.0.0 | 0 | 23 | 0 | 100% |

---

## 9. 版本演进路线图

### 9.1 里程碑时间线

```
V_PREVIOUS_MAJOR          V_CURRENT               v8.2.0/v4.3.0           v9.0.0/v5.0.0
xuansto-skill v1.0.0      xuansto-skill-v2 v8.0.0  xuansto-skill-v2 v8.2.0  xuansto-skill-v2 v9.0.0
35 Agents / 8 Workflows   57 Agents / 17 Tools     57 Agents / 19 Tools     57+ Agents / 21+ Tools
                          MCP Server v4.1.0         MCP Server v4.3.0        MCP Server v5.0.0

    │                         │                         │                         │
    │    重命名为xuansto       │    P0紧急修复            │    P1接口治理            │    P2架构加固
    │    扩展到57 Agent        │    降级机制修复          │    Tool注册解耦          │    数据层统一
    │    新增MCP Server        │    参考文档补充          │    版本协商完善          │    配置校验层
    │    渐进式加载            │    状态持久化修复        │    knowledge接口治理     │    Hook系统加固
    │                         │                         │    降级脚本异步化        │    渐进式加载完善
    │                         │                         │    Tool职责拆分          │    通知与错误治理
    │                         │                         │    ChromaDB可选化        │    Resource增强
    │                         │                         │    工具文档补全          │    Agent与工作流治理
    │                         │                         │                         │
    ▼                         ▼                         ▼                         ▼
  全量加载                  骨架加载+降级可用         接口清晰+异步降级         数据统一+完整闭环
  无降级机制                降级链修复               职责拆分+版本对齐         架构成熟+安全加固
```

### 9.2 关键演进指标

| 指标 | V_PREVIOUS_MAJOR → V_CURRENT | V_CURRENT → v8.2.0 | v8.2.0 → v9.0.0 |
|------|------------------------------|---------------------|-------------------|
| **Agent扩展** | 35→57 (+63%) | 不变 | 57→57+ |
| **MCP Tool** | 0→17 (+∞) | 17→19 (+12%) | 19→21+ (+11%) |
| **质量门禁** | 15→54 (+260%) | 不变 | 54→54+ |
| **SKILL.md精简** | 765→71行 (-91%) | 不变 | 71→<200行 |
| **初始Token** | ~50K→≤2K (-96%) | 不变 | 不变 |
| **降级可用性** | 0%→部分 | 部分→100% | 100%→100%+加密 |
| **已知问题修复率** | N/A | 22%→70% | 70%→100% |
| **数据存储统一** | 分散 | 分散 | 分散→统一SQLite |

### 9.3 破坏性变更摘要

| 版本跃迁 | 破坏性变更 | 迁移建议 |
|---------|-----------|---------|
| V_PREVIOUS_MAJOR → V_CURRENT | SKILL.md结构完全重写；新增MCP Server依赖；触发条件外部化 | 需要安装xuansto-mcp-server；更新IDE Skill配置 |
| V_CURRENT → v8.2.0 | knowledge_search移除inject/precipitate action；agent_status拆分为agent_status+agent_manage | 更新调用knowledge_search的代码，使用knowledge_inject替代inject；更新agent变更类调用为agent_manage |
| v8.2.0 → v9.0.0 | 错误响应移除code字段，仅保留error_code；数据存储迁移到统一SQLite | 更新错误处理代码；运行数据迁移脚本 |
