# Xuansto Skill 版本演进路线

> 版本: 3.0.0 | 日期: 2026-05-23 | 状态: v8.0.0 已发布
> 关联文档: [REFACTOR_PLAN.md](./REFACTOR_PLAN.md)

---

## 目录

1. [版本号定义规则](#1-版本号定义规则)
2. [双组件版本规则](#2-双组件版本规则)
3. [版本里程碑总览](#3-版本里程碑总览)
4. [v8.0.0 — 当前发布版](#4-v800--当前发布版)
5. [v8.1.0 — P4 收尾修复](#5-v810--p4-收尾修复)
6. [v9.0.0 — 下一大版本](#6-v900--下一大版本)
7. [版本兼容性矩阵](#7-版本兼容性矩阵)
8. [升级与回退策略](#8-升级与回退策略)

---

## 1. 版本号定义规则

### 1.1 语义化版本（SemVer）

本项目严格遵循 [语义化版本 2.0.0](https://semver.org/lang/zh-CN/) 规范，版本号格式为 **MAJOR.MINOR.PATCH**：

| 字段 | 含义 | 递增条件 | 示例 |
|------|------|---------|------|
| **MAJOR** | 主版本号 | 存在不兼容的 API 变更 | 8 → 9 |
| **MINOR** | 次版本号 | 新增向后兼容的功能 | 8.0 → 8.1 |
| **PATCH** | 修订号 | 向后兼容的问题修复 | 8.0.0 → 8.0.1 |

### 1.2 版本号变更判定标准

| 变更类型 | Skill 版本影响 | MCP Server 版本影响 | 示例 |
|---------|--------------|-------------------|------|
| 新增 Tool / Resource | — | MINOR | 新增 `metrics_report` Tool → v8.0.0 → v8.1.0 |
| 新增 Skill 命令 | MINOR | — | 新增 `/audit` 命令 → v8.0.0 → v8.1.0 |
| Tool 参数变更（向后兼容） | — | MINOR | `agent_status` 新增 action → v8.1.0 |
| Tool 参数变更（不兼容） | — | MAJOR | 移除 `knowledge_search.inject` → v9.0.0 |
| 降级机制变更 | MINOR | MINOR | 统一降级框架 → 双方 MINOR |
| 数据模型变更（需迁移） | — | MINOR | 新增 `error_type` 字段 → v8.1.0 |
| API 协议变更 | MAJOR | MAJOR | API v2 → v3 → v9.0.0 |
| Bug 修复 | PATCH | PATCH | 修复竞态条件 → v8.0.1 |

### 1.3 预发布版本标识

| 标识 | 含义 | 示例 |
|------|------|------|
| `-alpha.N` | 内部测试，API 可能频繁变更 | `v8.1.0-alpha.1` |
| `-beta.N` | 功能冻结，仅修复缺陷 | `v8.1.0-beta.1` |
| `-rc.N` | 发布候选，预期即为正式版 | `v8.1.0-rc.1` |

---

## 2. 双组件版本规则

### 2.1 组件定义

xuansto 项目由两个协同发布的组件构成：

| 组件 | 当前版本 | 位置 | 职责 |
|------|---------|------|------|
| **xuansto-skill-v2** | v8.0.0 | `.trae/skills/xuansto-skill-v2/` | Skill 层：SKILL.md、约束、路由、参考文档、评估配置 |
| **xuansto-mcp-server** | v8.0.0 | `xuansto-mcp-server/` | MCP Server 层：Tool、Resource、Hook、数据层、降级引擎 |
| ~~xuansto-skill (v1)~~ | v4.0.0 (ARCHIVED) | `.trae/skills/xuansto-skill/` | 已归档，不再维护 |

### 2.2 版本同步规则

自 v8.0.0 起，双组件采用 **版本号对齐** 策略：

| 规则 | 说明 |
|------|------|
| MAJOR 同步 | 双组件 MAJOR 版本必须同步递增（v8 → v9 同时发布） |
| MINOR 独立 | MINOR 版本可独立递增，但跨组件依赖的变更需同步发布 |
| PATCH 独立 | PATCH 版本完全独立递增，不要求同步 |
| 最低兼容声明 | SKILL.md 中声明 `min_version`，MCP Server 通过 `negotiate_version` 校验 |

### 2.3 版本协商机制

```
Skill 启动 → 读取 SKILL.md min_version
           → 调用 server_health(negotiate_version, client_version="8.0.0")
           → MCP Server 返回:
              { server_version: "8.0.0",
                api_version: "3.0.0",
                compatible: true,
                deprecated_features: [...],
                new_features: [...] }
           → 不兼容时返回错误 + 升级建议
```

### 2.4 版本不对齐时的行为

| 场景 | Skill 版本 | MCP Server 版本 | 行为 |
|------|-----------|----------------|------|
| Skill > Server | v8.1.0 | v8.0.0 | 降级运行，v8.1.0 新功能不可用 |
| Skill < Server | v8.0.0 | v8.1.0 | 正常运行，Server 新功能未暴露 |
| MAJOR 不匹配 | v9.0.0 | v8.0.0 | 拒绝连接，返回明确升级指引 |
| Server 不可用 | v8.0.0 | — | 全量降级到脚本/内联模式 |

---

## 3. 版本里程碑总览

### 3.1 版本谱系图

```
  V_ARCHIVED                 V_CURRENT                    V_PATCH                V_NEXT_MAJOR
  ──────────                 ─────────                    ───────                ────────────
  xuansto-skill v1.0.0       xuansto-skill-v2 v8.0.0      v8.1.0 (P4收尾)        xuansto-skill-v2 v9.0.0
  (原始 multi-agent-         xuansto-mcp-server v8.0.0    xuansto-mcp-server      xuansto-mcp-server v9.0.0
   sdd-tdd-orchestrator)    ┌──────────────────┐         v8.1.0                 ┌──────────────────┐
  ┌──────────────────┐      │  v8.0.0 重构整合  │                                │  v9.0.0 下一大版  │
  │ v1.0.0 → v4.0.0  │      │                  │               ┌──────────┐     │                  │
  │ 原始单文件Skill   │      │ P0 紧急修复 ✅    │               │ v8.1.0   │     │ API v3 强制      │
  │ 72+参考文件       │      │ P1 接口治理 ✅    │──────────────▶│ P4收尾   │     │ Phase自动推进    │
  │ 脚本驱动         │      │ P2 架构加固 ✅    │               │ U-43~46  │     │ v1彻底清除       │
  │ v4.0.0 ARCHIVED  │      │ P3 优化收尾 ✅    │               └────┬─────┘     │ 架构升级         │
  └──────────────────┘      │ 42/42 问题已解决  │                    │           └──────────────────┘
                            │ 20 Tool + 6 Res  │                    │
                            │ 统一xuansto.db    │◀───────────────────┘
                            └──────────────────┘    v8.1.0 完成后
                                                    46/46 问题全部解决
```

### 3.2 里程碑时间线

| 版本 | 阶段 | 周期 | 解决问题数 | 累计解决 | 状态 |
|------|------|------|-----------|---------|------|
| v8.0.0 | P0 紧急修复 | 第 1 周 | 3 (U-01~U-03) | 3/46 | ✅ 已完成 |
| v8.0.0 | P1 接口治理 | 第 2-3 周 | 7 (U-04~U-10) | 10/46 | ✅ 已完成 |
| v8.0.0 | P2 架构加固 | 第 4-5 周 | 21 (U-11~U-31) | 31/46 | ✅ 已完成 |
| v8.0.0 | P3 优化收尾 | 第 6 周+ | 11 (U-32~U-42) | 42/46 | ✅ 已完成 |
| v8.1.0 | P4 收尾修复 | 第 7 周 | 4 (U-43~U-46) | 46/46 | 🔲 进行中 |
| v9.0.0 | 下一大版本 | 第 8 周+ | 新特性 + 破坏性变更 | — | 📋 待规划 |

### 3.3 问题分布与版本映射

```
紧急 (3)  U-01 U-02 U-03                                    → v8.0.0 P0 ✅
高   (7)  U-04 U-05 U-06 U-07 U-08 U-09 U-10               → v8.0.0 P1 ✅
中   (23) U-11~U-31, U-43, U-44                             → v8.0.0 P2 ✅ (21) + v8.1.0 P4 🔲 (2)
低   (13) U-32~U-42, U-45, U-46                             → v8.0.0 P3 ✅ (11) + v8.1.0 P4 🔲 (2)

v8.0.0 已解决: 42/46  ██████████████████████████████████████████████████████████████████████████░░  91.3%
v8.1.0 待解决:  4/46  ████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   8.7%
```

---

## 4. v8.0.0 — 当前发布版

### 4.1 版本目标

从原始脚本驱动架构全面重构为 MCP-first 架构，解决五份分析文档（ARCHITECTURE / DATABASE_DESIGN / MCP_REVIEW / SKILL_REVIEW / API_SPECIFICATION）中发现的全部 42 个独立问题。实现生产级降级机制、统一数据存储、完整 Tool 体系、渐进式加载框架和安全加固。

### 4.2 主要变更

#### 4.2.1 P0 紧急修复（U-01, U-02, U-03）

| 问题 | 变更内容 | 影响文件 |
|------|---------|---------|
| U-01 降级机制不完整且不统一 | 实现 `subprocess_utils.py` 异步降级链：MCP 调用 → 脚本降级 → 内联降级 → 最小响应；17 个 Tool 全部有降级路径；降级响应含 `source:"fallback"` 标识 | `degradation.py`, `subprocess_utils.py`, `server.py` |
| U-02 v2 参考文档严重不足 | references/ 从 6 个文件扩展到 75+ 参考文件，覆盖编码规范、安全指南、桌面开发、Hook 系统等 | `references/*.md`, `mcp-tools.md` |
| U-03 状态持久化无原子保障 | xuansto.db 统一存储（8 表 + 11 索引）；atexit 注册 `_persist_state()`；hash 完整性校验；写入锁 + backoff jitter | `database.py`, `degradation.py` |

#### 4.2.2 P1 接口治理（U-04 ~ U-10）

| 问题 | 变更内容 | 影响文件 |
|------|---------|---------|
| U-04 Tool 注册依赖 FastMCP 内部 API | 本地 `_TOOL_REGISTRY` 注册表；Hook 拦截从映射表获取 Tool 函数；`_tool_manager._tools` 零引用 | `server.py`, `hook_engine.py` |
| U-05 版本协商机制不完整 | MCP Server 升级到 v8.0.0；`negotiate_version` 响应含 `deprecated_features` / `new_features`；semver 比较逻辑 | `server_health.py`, `config.py` |
| U-06 knowledge_search/inject 职责边界模糊 | `knowledge_search` Schema 仅保留 `action="retrieve"`；写入操作统一通过 `knowledge_inject` | `knowledge_search.py`, `knowledge_inject.py` |
| U-07 工具文档与 MCP 暴露缺失 | 新增 `metrics_report` + `config_manage` Tool；`mcp-tools.md` 覆盖全部 20 个 Tool | `metrics_report.py`, `config_manage.py` |
| U-08 ChromaDB 降级频繁 | ChromaDB 从必需降级为可选增强；默认 SQLite FTS5 + BM25；`HybridSearchEngine` 三级降级 | `search_engine.py`, `pyproject.toml` |
| U-09 降级脚本同步阻塞 | `run_script_fallback_async` 使用 `asyncio.create_subprocess_exec`；`wait_for` 超时控制；保留同步版本 | `subprocess_utils.py` |
| U-10 Tool 职责过载 | `agent_status` 保留查询类；`agent_manage` 负责变更类（create/assign/release/destroy/schedule） | `agent_status.py`, `agent_manage.py` |

#### 4.2.3 P2 架构加固（U-11 ~ U-31）

| 问题 | 变更内容 | 影响文件 |
|------|---------|---------|
| U-11 Phase 定义重复 | SKILL.md 精简至 <200 行 | `SKILL.md` |
| U-12 路径解析静默降级 | MCPNotificationCallback 通知 + WARNING 日志 | `config.py`, `notification.py` |
| U-13 Hook 拦截失败不阻塞 | 安全 Hook 失败默认阻塞 + 失败计数 `_HOOK_FAILURE_THRESHOLD=5` | `hook_engine.py` |
| U-14 会话状态分散 | xuansto.db `session_states` 表 | `database.py` |
| U-15 指标文件无清理 | xuansto.db `tool_metrics` 表 + TTL 清理 | `metrics.py` |
| U-16 内存缓存无持久化 | xuansto.db 持久化 + atexit handler | `cache.py` |
| U-17 YAML 配置无 Schema 校验 | `SkillConfigModel` / `FallbackConfigModel` / `ConstraintsModel` Pydantic 校验 | `config_models.py`, `config_manage.py` |
| U-18 SQLite 数据库分散 | 统一 xuansto.db（8 表） | `database.py` |
| U-19 Resource 与 Tool 重叠 | 明确分工：Resource 只读快照 / Tool 交互操作 | `skill_resources.py` |
| U-20 Hook 引擎缺少类型安全 | `HookType` 枚举（8 种类型） | `hook_engine.py`, `schemas.py` |
| U-21 通知系统未与 MCP 集成 | `MCPNotificationCallback` 推送关键事件 | `notification.py` |
| U-22 配置热重载缺少 MCP 入口 | `config_manage` Tool | `config_manage.py` |
| U-23 Resource 缺少分页过滤 | `sessions/{id}` + `agents/{layer}/{name}` 参数化 Resource | `skill_resources.py` |
| U-24 Token 估算精度不足 | tiktoken 可选（`_HAS_TIKTOKEN`）+ `target_deviation` 字段 | `context_compress.py` |
| U-25 Hook 与 MCP 集成不完整 | HookType 枚举 + 安全阻断 + 失败计数 | `hook_engine.py` |
| U-26 Agent 合并策略未执行 | `agent_status(action="merge")` + `_merge_agents()` + YAML 规则加载 | `agent_status.py` |
| U-27 命令路由静态无协商 | `server_health(action="capabilities")` 返回可用 Tool + 降级状态 + API 版本 | `server_health.py` |
| U-28 DisclosureTransition 未使用 | DisclosureTransition 状态机已实现 | `resource_load_status.py` |
| U-29 FALLBACK_MAP 静态构建 | `config_manage reload` + `fallback_config.yaml` 热监控（watchfiles/polling） | `degradation.py` |
| U-30 错误码语义混淆 | 统一 `error_code`，deprecated `code` 字段 | `errors.py` |
| U-31 退避缺少抖动 | `backoff jitter`（`random.uniform(0, 0.5)`） | `degradation.py` |

#### 4.2.4 P3 优化收尾（U-32 ~ U-42）

| 问题 | 变更内容 | 影响文件 |
|------|---------|---------|
| U-32 缺少评估配置 | evals/ 目录（`mcp_evaluation.xml` + `trigger_eval.json`） | `evals/` |
| U-33 缺少 CHANGELOG | `CHANGELOG.md` 已创建 | `CHANGELOG.md` |
| U-34 v1/v2 文件重复 | v1 标记 ARCHIVED | `xuansto-skill/` |
| U-35 SKILL.md 行数超限 | SKILL.md 精简至 <200 行 | `SKILL.md` |
| U-36 工作流 YAML/MD 同步 | YAML 为权威源（`_yaml/` 目录 15 个 YAML 文件） | `workflows/_yaml/` |
| U-37 ErrorPattern 无分类 | `error_type` 字段 | `database.py` |
| U-38 Workflow/Decision 无关联 | `workflow_id` 关联字段 | `database.py` |
| U-39 knowledge_entries 无软删除 | `deleted_at` 字段 + `knowledge_inject(delete)` | `database.py`, `knowledge_inject.py` |
| U-40 缓存无 LRU 淘汰 | `cache.py` LRU 缓存 | `cache.py` |
| U-41 快照文件无加密 | `crypto.py` AES-256-GCM | `crypto.py` |
| U-42 速率限制/白名单/默认值 | `rate_limiter.py` 令牌桶 + 名称白名单 + action 必填 | `rate_limiter.py`, `validator.py` |

### 4.3 关联问题编号

| 阶段 | 问题编号 | 数量 | 状态 |
|------|---------|------|------|
| P0 紧急修复 | U-01, U-02, U-03 | 3 | ✅ 全部已解决 |
| P1 接口治理 | U-04 ~ U-10 | 7 | ✅ 全部已解决 |
| P2 架构加固 | U-11 ~ U-31 | 21 | ✅ 全部已解决 |
| P3 优化收尾 | U-32 ~ U-42 | 11 | ✅ 全部已解决 |
| **合计** | **U-01 ~ U-42** | **42** | **✅ 全部已解决** |

### 4.4 验收标准

| 编号 | 验收标准 | 状态 |
|------|---------|------|
| AC-01 | 杀死 MCP Server 进程后，17 个 Tool 仍可通过降级返回结果 | ✅ |
| AC-02 | 降级响应结构与正常响应一致（含 `source:"fallback"` 标识） | ✅ |
| AC-03 | 降级脚本调用超时（60s）后回退到内联降级 | ✅ |
| AC-04 | 每个 Phase 的 Agent 执行时可获取对应参考文档 | ✅ |
| AC-05 | `mcp-tools.md` 覆盖全部 20 个 Tool | ✅ |
| AC-06 | 模拟进程崩溃后重启，状态可正确恢复 | ✅ |
| AC-07 | 并发读写测试无数据损坏 | ✅ |
| AC-08 | `_tool_manager._tools` 在代码中零引用 | ✅ |
| AC-09 | `knowledge_search(action="inject")` 返回参数校验错误 | ✅ |
| AC-10 | 卸载 chromadb 后知识检索仍可用（BM25 模式） | ✅ |
| AC-11 | `agent_status` action 枚举仅含查询类 | ✅ |
| AC-12 | 所有状态实体可通过 SQL 查询 | ✅ |
| AC-13 | `config_manage(action="validate")` 可检测配置问题 | ✅ |
| AC-14 | security-block Hook 失败时工具调用被阻止 | ✅ |
| AC-15 | Phase 转换时客户端收到 DisclosureTransition 通知 | ✅ |
| AC-16 | 修改 `fallback_config.yaml` 后降级路径自动更新 | ✅ |
| AC-17 | 错误响应仅含 `error_code` 字段（`code` 已 deprecated） | ✅ |
| AC-18 | SKILL.md < 200 行 | ✅ |
| AC-19 | YAML 为工作流权威源（15 个 YAML 文件） | ✅ |
| AC-20 | 高频调用被限流（令牌桶 60 req/min） | ✅ |
| AC-21 | 所有 Tool 的 action 参数为必填 | ✅ |

### 4.5 核心成果指标

| 指标 | v8.0.0 值 |
|------|----------|
| MCP Tool 数量 | 20 |
| MCP Resource 数量 | 6 |
| Agent 数量 | 57 / 13 层 |
| 命令数量 | 31 |
| 质量门禁 | 54 项 |
| 工作流阶段 | 9 Phase |
| 降级路径覆盖 | 17/20 Tool（3 个新 Tool 降级待补全 → U-43） |
| 数据库表 | 8 表 + 11 索引 |
| 参考文档 | 75+ 文件 |
| 问题解决率 | 42/46（91.3%） |

---

## 5. v8.1.0 — P4 收尾修复

### 5.1 版本目标

修复 v8.0.0 代码审查中发现的 4 个遗留问题（U-43 ~ U-46），实现 46/46 问题全部解决。此版本为 v8.x 系列的最终稳定版，为 v9.0.0 大版本升级提供完整基线。

### 5.2 主要变更

#### 5.2.1 FALLBACK_MAP 补全（U-43）

| 项目 | 说明 |
|------|------|
| **问题** | FALLBACK_MAP 当前 17 个条目，缺少 `metrics_report` / `config_manage` / `agent_manage` 的降级函数 |
| **根因** | P1-E 拆分后新增 `agent_manage`，P1-G 补全后新增 `metrics_report` / `config_manage`，但未同步 FALLBACK_MAP |
| **影响** | MCP 不可用时 3 个新 Tool 直接失败，无降级响应 |
| **变更** | 1. 新增 `metrics_report_fallback`：从 xuansto.db 读取最近指标<br>2. 新增 `config_manage_fallback`：返回当前配置快照（只读）<br>3. 新增 `agent_manage_fallback`：从静态 registry 读取 Agent 信息<br>4. 将 3 个 fallback 函数加入 FALLBACK_MAP 和 _INLINE_FALLBACK_MAP<br>5. 更新 `fallback_config.yaml` 添加新条目 |
| **影响文件** | `degradation.py`, `metrics_report.py`, `config_manage.py`, `agent_manage.py`, `fallback_config.yaml` |
| **修复复杂度** | 低 |

#### 5.2.2 评估配置修正（U-44）

| 项目 | 说明 |
|------|------|
| **问题** | `mcp_evaluation.xml` 引用 4 个不存在的 Tool：`knowledge_auto_retrieve` / `knowledge_progressive_search` / `knowledge_deep_load` / `knowledge_stats` |
| **根因** | mcp_evaluation.xml 基于旧 API 编写，未随 U-06 knowledge 接口治理更新 |
| **影响** | 10 个 qa_pair 中 6 个引用不存在的 Tool，评估无法执行 |
| **变更** | 1. `knowledge_auto_retrieve` → `knowledge_search(action="retrieve")` + `knowledge_inject(action="list_available")`<br>2. `knowledge_progressive_search` → `knowledge_search(action="retrieve", search_type="hybrid")`<br>3. `knowledge_deep_load` → `knowledge_search(action="retrieve", query=entry_id)`<br>4. `knowledge_stats` → `knowledge_inject(action="list_available")`<br>5. 更新 verification 断言以匹配新响应结构<br>6. 确保全部 10 个 qa_pair 的 tool_calls 指向实际存在的 Tool |
| **影响文件** | `evals/mcp_evaluation.xml` |
| **修复复杂度** | 中 |

#### 5.2.3 SKILL.md Phase 标记（U-45）

| 项目 | 说明 |
|------|------|
| **问题** | SKILL.md 未使用 Phase 标记，渐进式加载状态机仅在 MCP Server 侧实现 |
| **根因** | 渐进式加载框架在 P2-D 阶段仅实现了 Server 侧，Skill 侧未同步 |
| **影响** | Skill 无法在加载时告知平台自身属于哪个 Phase；平台无法根据 Skill 的 Phase 声明决定加载策略 |
| **变更** | 1. 在 SKILL.md 的 triggers 段添加 phase 标注：`phase: 0`（骨架阶段加载）<br>2. 在 commands/ 段标注各命令所需最低 Phase<br>3. 在 references/ 段标注各参考文档的 Phase 归属<br>4. 添加 Phase 推进提示文本模板 |
| **影响文件** | `SKILL.md` |
| **修复复杂度** | 低 |

#### 5.2.4 健康检查间隔可配置（U-46）

| 项目 | 说明 |
|------|------|
| **问题** | `DegradationManager._DEFAULT_HEALTH_INTERVAL` 硬编码为 30.0s，不可配置 |
| **根因** | 初始实现时使用字面量，未考虑不同部署环境的差异化需求 |
| **影响** | 高频环境检查间隔过长，低频环境浪费资源 |
| **变更** | 1. 在 `.xuansto-config.yaml` 添加 `health_check_interval_sec` 字段<br>2. 在 `SkillConfigModel` 添加 `health_check_interval_sec: int = Field(default=30, ge=5, le=300)`<br>3. `DegradationManager.__init__` 从配置读取间隔值<br>4. `config_manage(action="status")` 显示当前间隔 |
| **影响文件** | `degradation.py`, `config_models.py`, `.xuansto-config.yaml` |
| **修复复杂度** | 低 |
| **依赖** | P2-B（config_manage 已实现） |

### 5.3 关联问题编号

| 问题编号 | 标题 | 严重度 | 影响域 |
|---------|------|--------|--------|
| U-43 | FALLBACK_MAP 缺少 3 个新 Tool 降级定义 | 中 | MCP, 降级 |
| U-44 | mcp_evaluation.xml 引用 4 个不存在的 Tool | 中 | Skill, 评估 |
| U-45 | SKILL.md 未使用 Phase 标记实现渐进式加载提示 | 低 | Skill, 特效 |
| U-46 | DegradationManager 健康检查间隔硬编码 30s | 低 | MCP, 架构 |

### 5.4 验收标准

| 编号 | 验收标准 |
|------|---------|
| AC-22 | `server_health(check)` 返回 `tools_count=20` |
| AC-23 | MCP 不可用时 20/20 Tool 返回降级响应 |
| AC-24 | 降级链集成测试通过（含 3 个新 Tool） |
| AC-25 | `mcp_evaluation.xml` 中每个 qa_pair 引用的 Tool 名称在 `schemas.py` 中有对应 Input 定义 |
| AC-26 | `mcp_evaluation.xml` 中参数结构与 Schema 一致 |
| AC-27 | `trigger_eval.json` 无需修改 |
| AC-28 | SKILL.md 行数仍 <200 行 |
| AC-29 | Phase 标记与 `resource_load_status` 的 4 阶段模型一致 |
| AC-30 | 修改 `.xuansto-config.yaml` 后 `config_manage(reload)` 生效 |
| AC-31 | 健康检查间隔范围 5s ~ 300s |
| AC-32 | 默认间隔仍为 30s |

### 5.5 预计周期

第 7 周，4 个问题均为低/中复杂度，可并行实施。

---

## 6. v9.0.0 — 下一大版本

### 6.1 版本目标

基于 v8.1.0 的完整稳定基线（46/46 问题全部解决），引入不兼容的 API 变更和重大架构升级。主要实现 API v3.0.0 协议强制执行、渐进式加载 Phase 2-3 自动推进、v1 遗留代码彻底清除、MCP Server 内部架构升级。

### 6.2 主要变更

#### 6.2.1 API v3.0.0 协议升级

| 项目 | 说明 |
|------|------|
| **目标** | 统一 API 响应格式，移除历史兼容层 |
| **变更** | 移除 `code` 字段，仅保留 `error_code`（v8.0.0 已 deprecated，v9.0.0 强制执行）；统一所有 Tool 响应为 `{status, data, error_code, metadata}` 结构；移除 v1 兼容的降级响应格式；API 版本号从 v2 升级到 v3.0.0 |
| **破坏性** | 不兼容 v8.x 客户端，需配合 Skill 层升级 |

#### 6.2.2 渐进式加载完整实现

| 项目 | 说明 |
|------|------|
| **目标** | 实现 Phase 2-3 自动推进，无需显式调用 `resource_load_status(preload, phase=N)` |
| **变更** | Phase 1→2 推进由"需要参考文档/知识检索"自动触发（v8.0.0 已实现 DisclosureTransition 提示，v9.0.0 改为自动推进）；Phase 2→3 推进由"深度分析/安全扫描"自动触发；Token 预算监控与自动降级闭环；完整 Phase 转换通知体系 |
| **性能目标** | Phase 0→1 推进延迟 ≤500ms；Phase 1→2 推进延迟 ≤2000ms；Phase 2→3 推进延迟 ≤5000ms |

#### 6.2.3 v1 遗留彻底清除

| 项目 | 说明 |
|------|------|
| **目标** | 移除所有 v1 兼容代码和文件 |
| **变更** | 删除 `xuansto-skill/` 目录（v1）；移除 `constraints.yaml` 中 v1 兼容的 Phase 定义；统一 Skill 命名空间为 `xuansto-skill-v2`；清理 `scripts/` 中仅 v1 使用的脚本 |
| **破坏性** | v1 Skill 完全不可用 |

#### 6.2.4 MCP Server 架构升级

| 项目 | 说明 |
|------|------|
| **目标** | MCP Server 内部架构升级，提升可维护性 |
| **变更** | Tool 注册完全基于公开 API（v8.0.0 已解耦，v9.0.0 移除内部 API 兼容层）；搜索引擎默认 BM25 + 可选向量搜索（v8.0.0 已实现，v9.0.0 移除 ChromaDB 必需依赖声明）；统一 SQLite 存储引擎（v8.0.0 已迁移，v9.0.0 移除 JSON 状态文件兼容读取）；移除同步降级兼容代码 |

#### 6.2.5 降级覆盖完整化

| 项目 | 说明 |
|------|------|
| **目标** | 基于v8.1.0补全的20/20降级覆盖，进一步优化降级质量 |
| **变更** | 降级响应从"最小可用"升级为"功能等价"（尽可能保留核心语义）；降级脚本支持增量更新（无需全量替换）；降级状态持久化到 xuansto.db 支持跨重启恢复 |

### 6.3 关联问题编号

v9.0.0 不直接关联 U-01~U-46 中的未解决问题（v8.1.0 已全部解决），但以下问题的治理成果在此版本中成为强制要求：

| 问题编号 | 关联说明 |
|---------|---------|
| U-01 | 降级机制在 v9.0.0 中移除 v1 兼容降级路径 |
| U-04 | Tool 注册在 v9.0.0 中完全移除内部 API 兼容层 |
| U-05 | API v3.0.0 强制版本协商，不支持 v2 客户端 |
| U-06 | `knowledge_search` 在 v9.0.0 中移除 inject/precipitate 兼容处理 |
| U-08 | ChromaDB 在 v9.0.0 中从必需依赖声明中移除 |
| U-30 | `code` 字段在 v9.0.0 中彻底移除 |
| U-34 | v1 目录在 v9.0.0 中彻底删除 |
| U-43 | v8.1.0 补全的 20/20 降级覆盖在 v9.0.0 中升级为"功能等价"降级 |
| U-45 | v8.1.0 添加的 Phase 标记在 v9.0.0 中支持自动推进 |

### 6.4 验收标准

| 编号 | 验收标准 |
|------|---------|
| AC-33 | API v3.0.0 客户端可正常调用全部 Tool |
| AC-34 | API v2.x 客户端调用返回明确的不兼容错误 |
| AC-35 | Phase 0→1→2 自动推进，无需显式 preload |
| AC-36 | Token 预算超限时自动降级并通知客户端 |
| AC-37 | `xuansto-skill/` 目录不存在 |
| AC-38 | `_tool_manager._tools` 引用不存在 |
| AC-39 | `chromadb` 不在 `pyproject.toml` 必需依赖中 |
| AC-40 | JSON 状态文件兼容读取代码不存在 |
| AC-41 | `code` 字段在错误响应中不存在 |
| AC-42 | `subprocess.run` 同步降级代码不存在 |
| AC-43 | 全部 46 个 U-01~U-46 问题的回归测试通过 |

---

## 7. 版本兼容性矩阵

### 7.1 Skill 与 MCP Server 版本对应关系

| Skill 版本 | MCP Server 版本 | API 版本 | 降级覆盖 | 兼容说明 |
|-----------|----------------|---------|---------|---------|
| v8.0.0 | v8.0.0 | v2.0.0 | 17/20 Tool | 当前发布版，42/46 问题已解决 |
| v8.1.0 | v8.1.0 | v2.1.0 | 20/20 Tool | P4 收尾，46/46 问题全部解决 |
| v9.0.0 | v9.0.0 | v3.0.0 | 20/20 Tool | 不兼容 v8.x；需同时升级 Skill 和 MCP Server |

### 7.2 渐进式加载版本演进

| 版本 | Phase 0→1 | Phase 1→2 | Phase 2→3 | Token 降级 | Skill 侧 Phase 标记 |
|------|-----------|-----------|-----------|-----------|-------------------|
| v8.0.0 | 自动 | DisclosureTransition 提示 | DisclosureTransition 提示 | 手动触发 | ✗ |
| v8.1.0 | 自动 | DisclosureTransition 提示 | DisclosureTransition 提示 | 手动触发 | ✓ |
| v9.0.0 | 自动 | **自动推进** | **自动推进** | **自动降级** | ✓ |

### 7.3 降级机制版本演进

| 版本 | MCP 调用 | 脚本降级 | 内联降级 | 最小响应 | 异步化 | 覆盖率 |
|------|---------|---------|---------|---------|--------|--------|
| v8.0.0 | ✓ | ✓ | ✓ | ✓ | ✓ | 17/20 (85%) |
| v8.1.0 | ✓ | ✓ | ✓ | ✓ | ✓ | 20/20 (100%) |
| v9.0.0 | ✓ | ✓（功能等价） | ✓（功能等价） | ✓ | ✓（移除同步兼容） | 20/20 (100%) |

### 7.4 数据存储版本演进

| 版本 | 主存储 | 状态文件 | 缓存 | 加密 |
|------|--------|---------|------|------|
| v8.0.0 | xuansto.db (8 表) | JSON 兼容读取 | SQLite 持久化 + LRU | AES-256-GCM 可选 |
| v8.1.0 | xuansto.db (8 表) | JSON 兼容读取 | SQLite 持久化 + LRU | AES-256-GCM 可选 |
| v9.0.0 | xuansto.db (8 表) | **仅 SQLite** | SQLite 持久化 + LRU | AES-256-GCM 可选 |

### 7.5 跨版本兼容性

| 客户端 \ 服务端 | MCP v8.0.0 | MCP v8.1.0 | MCP v9.0.0 |
|---------------|-----------|-----------|-----------|
| Skill v8.0.0 | ✓ 完全兼容 | ✓ 降级运行 | ✗ 不兼容 |
| Skill v8.1.0 | ✓ 降级运行 | ✓ 完全兼容 | ✗ 不兼容 |
| Skill v9.0.0 | ✗ 不兼容 | ✗ 不兼容 | ✓ 完全兼容 |

---

## 8. 升级与回退策略

### 8.1 升级路径

```
v8.0.0/v8.0.0 ──────▶ v8.1.0/v8.1.0 ──────▶ v9.0.0/v9.0.0
  当前发布版             P4 收尾修复           下一大版本
  42/46 已解决           46/46 全部解决        API v3 + 自动Phase
  17/20 降级覆盖         20/20 降级覆盖        功能等价降级
```

### 8.2 各版本升级注意事项

| 版本升级 | 数据迁移 | 配置变更 | 破坏性变更 |
|---------|---------|---------|-----------|
| v8.0.0 → v8.1.0 | 无 | `.xuansto-config.yaml` 新增 `health_check_interval_sec`（可选，默认 30） | 无 |
| v8.1.0 → v9.0.0 | 无（v8.0.0 已完成迁移） | API 版本协商强制 v3 | `knowledge_search.inject` 移除；`code` 字段移除；v1 删除；JSON 状态文件读取移除 |

### 8.3 回退策略

| 场景 | 回退方案 | 数据影响 |
|------|---------|---------|
| v8.1.0 → v8.0.0 | 直接替换文件 | 无影响（v8.1.0 新增配置有默认值） |
| v9.0.0 → v8.1.0 | 替换文件 + API 降级 | 不支持自动回退，需手动调整客户端 |

### 8.4 Deprecated 功能时间线

| 功能 | Deprecated 版本 | 移除版本 | 替代方案 |
|------|----------------|---------|---------|
| `knowledge_search(action="inject")` | v8.0.0 | v9.0.0 | `knowledge_inject` |
| `knowledge_search(action="precipitate")` | v8.0.0 | v9.0.0 | `knowledge_inject(action="precipitate")` |
| 错误响应 `code` 字段 | v8.0.0 | v9.0.0 | `error_code` 字段 |
| JSON 状态文件读取 | v8.0.0 | v9.0.0 | SQLite 统一存储 |
| v1 Skill 目录 | v8.0.0 | v9.0.0 | v2 Skill |
| `subprocess.run` 同步降级 | v8.0.0 | v9.0.0 | `asyncio.create_subprocess_exec` |
| `_tool_manager._tools` 内部 API | v8.0.0 | v9.0.0 | `_TOOL_REGISTRY` 映射表 |
| ChromaDB 必需依赖 | v8.0.0 | v9.0.0 | 可选增强依赖 |

### 8.5 升级检查清单

#### v8.0.0 → v8.1.0

- [ ] 更新 xuansto-mcp-server 到 v8.1.0
- [ ] 更新 xuansto-skill-v2 到 v8.1.0
- [ ] （可选）在 `.xuansto-config.yaml` 中配置 `health_check_interval_sec`
- [ ] 验证 `server_health(check)` 返回 `tools_count=20`
- [ ] 验证 `mcp_evaluation.xml` 全部 qa_pair 可执行
- [ ] 运行降级链集成测试

#### v8.1.0 → v9.0.0

- [ ] 更新 xuansto-mcp-server 到 v9.0.0
- [ ] 更新 xuansto-skill-v2 到 v9.0.0
- [ ] 更新客户端 API 版本协商为 v3
- [ ] 移除所有 `knowledge_search(action="inject")` 调用
- [ ] 移除所有错误响应中 `code` 字段的读取
- [ ] 删除 `xuansto-skill/` 目录（v1）
- [ ] 验证 API v2.x 客户端收到不兼容错误
- [ ] 运行全量回归测试（46 个问题）
