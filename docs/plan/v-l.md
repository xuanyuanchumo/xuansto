# Xuansto Skill 版本演进路线

> 版本: 1.0.0 | 日期: 2026-05-23 | 状态: 草案
> 关联文档: [REFACTOR_PLAN.md](./REFACTOR_PLAN.md)

---

## 目录

1. [版本号定义规则](#1-版本号定义规则)
2. [版本里程碑总览](#2-版本里程碑总览)
3. [v8.1.0 / v4.2.0 — P0 紧急修复](#3-v810--v420--p0-紧急修复)
4. [v8.2.0 / v4.3.0 — P1 接口治理](#4-v820--v430--p1-接口治理)
5. [v8.3.0 / v4.4.0 — P2 架构加固](#5-v830--v440--p2-架构加固)
6. [v8.4.0 / v4.5.0 — P3 优化收尾](#6-v840--v450--p3-优化收尾)
7. [v9.0.0 / v5.0.0 — 下一大版本](#7-v900--v500--下一大版本)
8. [版本兼容性矩阵](#8-版本兼容性矩阵)
9. [升级与回退策略](#9-升级与回退策略)

---

## 1. 版本号定义规则

### 1.1 语义化版本（SemVer）

本项目严格遵循 [语义化版本 2.0.0](https://semver.org/lang/zh-CN/) 规范，版本号格式为 **MAJOR.MINOR.PATCH**：

| 字段 | 含义 | 递增条件 | 示例 |
|------|------|---------|------|
| **MAJOR** | 主版本号 | 存在不兼容的 API 变更 | 8 → 9 |
| **MINOR** | 次版本号 | 新增向后兼容的功能 | 8.0 → 8.1 |
| **PATCH** | 修订号 | 向后兼容的问题修复 | 8.0.0 → 8.0.1 |

### 1.2 双组件版本号规则

xuansto-skill-v2 与 xuansto-mcp-server 为协同发布的双组件体系，版本号独立递增但保持发布同步：

| 组件 | 版本号格式 | 说明 |
|------|----------|------|
| xuansto-skill-v2 | `v{MAJOR}.{MINOR}.{PATCH}` | Skill 层（SKILL.md、约束、路由、参考文档） |
| xuansto-mcp-server | `v{MAJOR}.{MINOR}.{PATCH}` | MCP Server 层（Tool、Resource、Hook、数据层） |

**同步规则：**

- MINOR 版本同步递增：Skill v8.N.0 对应 MCP Server v4.N+1.0
- MAJOR 版本同步递增：Skill v9.0.0 对应 MCP Server v5.0.0
- PATCH 版本独立递增，不要求同步

### 1.3 版本号变更判定标准

| 变更类型 | Skill 版本影响 | MCP Server 版本影响 | 示例 |
|---------|--------------|-------------------|------|
| 新增 Tool / Resource | — | MINOR | 新增 `metrics_report` Tool → v4.2.0 → v4.3.0 |
| 新增 Skill 命令 | MINOR | — | 新增 `/audit` 命令 → v8.0.0 → v8.1.0 |
| Tool 参数变更（向后兼容） | — | MINOR | `agent_status` 新增 action → v4.2.0 → v4.3.0 |
| Tool 参数变更（不兼容） | — | MAJOR | 移除 `knowledge_search.inject` → v5.0.0 |
| 降级机制变更 | MINOR | MINOR | 统一降级框架 → v8.1.0 / v4.2.0 |
| 数据模型变更（需迁移） | — | MINOR | 新增 `error_type` 字段 → v4.5.0 |
| API 协议变更 | MAJOR | MAJOR | API v2 → v3 → v9.0.0 / v5.0.0 |
| Bug 修复 | PATCH | PATCH | 修复竞态条件 → v8.0.1 / v4.1.1 |

### 1.4 预发布版本标识

| 标识 | 含义 | 示例 |
|------|------|------|
| `-alpha.N` | 内部测试，API 可能频繁变更 | `v8.1.0-alpha.1` |
| `-beta.N` | 功能冻结，仅修复缺陷 | `v8.1.0-beta.1` |
| `-rc.N` | 发布候选，预期即为正式版 | `v8.1.0-rc.1` |

---

## 2. 版本里程碑总览

### 2.1 版本谱系

```
V_PREVIOUS_MAJOR          V_CURRENT                           V_NEXT_MAJOR
xuansto-skill v1.0.0      xuansto-skill-v2 v8.0.0             xuansto-skill-v2 v9.0.0
(原始 multi-agent-         + xuansto-mcp-server v4.1.0         + xuansto-mcp-server v5.0.0
 sdd-tdd-orchestrator)
                                    │
                                    ▼
                           ┌────────────────────┐
                           │  v8.1.0 / v4.2.0   │  P0 紧急修复
                           │  降级·文档·持久化    │
                           └─────────┬──────────┘
                                     │
                                     ▼
                           ┌────────────────────┐
                           │  v8.2.0 / v4.3.0   │  P1 接口治理
                           │  版本协商·接口治理   │
                           └─────────┬──────────┘
                                     │
                                     ▼
                           ┌────────────────────┐
                           │  v8.3.0 / v4.4.0   │  P2 架构加固
                           │  Hook·知识·Token    │
                           └─────────┬──────────┘
                                     │
                                     ▼
                           ┌────────────────────┐
                           │  v8.4.0 / v4.5.0   │  P3 优化收尾
                           │  性能·文档·v5清理   │
                           └─────────┬──────────┘
                                     │
                                     ▼
                           ┌────────────────────┐
                           │  v9.0.0 / v5.0.0   │  下一大版本
                           │  API v3·渐进完整    │
                           └────────────────────┘
```

### 2.2 里程碑时间线

| 版本 | 阶段 | 预计周期 | 解决问题数 | 累计解决 |
|------|------|---------|-----------|---------|
| v8.1.0 / v4.2.0 | P0 紧急修复 | 第 1 周 | 3 (U-01~U-03) | 3/42 |
| v8.2.0 / v4.3.0 | P1 接口治理 | 第 2-3 周 | 7 (U-04~U-10) | 10/42 |
| v8.3.0 / v4.4.0 | P2 架构加固 | 第 4-5 周 | 21 (U-11~U-31) | 31/42 |
| v8.4.0 / v4.5.0 | P3 优化收尾 | 第 6 周+ | 11 (U-32~U-42) | 42/42 |
| v9.0.0 / v5.0.0 | 下一大版本 | 第 8 周+ | 新特性 + 破坏性变更 | — |

### 2.3 问题分布与版本映射

```
紧急 (3)  U-01 U-02 U-03                                    → v8.1.0 / v4.2.0
高   (7)  U-04 U-05 U-06 U-07 U-08 U-09 U-10               → v8.2.0 / v4.3.0
中   (21) U-11~U-31                                         → v8.3.0 / v4.4.0
低   (11) U-32~U-42                                         → v8.4.0 / v4.5.0
```

---

## 3. v8.1.0 / v4.2.0 — P0 紧急修复

### 3.1 版本目标

修复系统核心功能不可用的紧急问题，确保降级链路完整、参考文档充足、状态持久化可靠。此版本为最低可用基线，所有后续版本均依赖此基线。

### 3.2 主要变更

#### 3.2.1 降级机制修复（U-01）

| 项目 | 说明 |
|------|------|
| 问题 | 降级机制不完整且不统一，MCP Server 不可用时系统完全失效 |
| 变更 | 实现 `subprocess_utils.py` → `scripts/` 实际调用链；统一四级降级框架：MCP 调用 → 脚本降级 → 内联降级 → 最小响应；降级脚本路径从 `fallback_config.yaml` 读取 |
| 影响文件 | `degradation.py`、`subprocess_utils.py`、`server.py`、`constraints.yaml`、`scripts/*.py` |
| 影响链 | U-01 → U-09 → U-29 → U-25 → U-08 → U-14 |

#### 3.2.2 参考文档补充（U-02）

| 项目 | 说明 |
|------|------|
| 问题 | v2 参考文档严重不足（仅 6 个文件，v1 有 72+） |
| 变更 | 迁移关键参考文件（编码规范、安全指南、桌面开发指南、Hook 系统、模型路由、并行化策略）；补充 `server_health` 工具文档到 `mcp-tools.md`；补充 `knowledge_search` inject/precipitate 文档 |
| 影响文件 | `references/*.md`、`mcp-tools.md` |
| 影响链 | U-02 → U-07 → U-05 |

#### 3.2.3 状态持久化修复（U-03）

| 项目 | 说明 |
|------|------|
| 问题 | 状态持久化无原子保障，存在竞态条件；daemon 线程退出时可能丢失状态 |
| 变更 | `atexit` 注册 `_persist_state()` 确保状态落盘；`load_state` 增加完整性校验（时间戳 + 内容哈希）；关键状态文件添加写入锁；降级恢复退避引入随机抖动 |
| 影响文件 | `degradation.py`、`resource_state.json`、`degradation_state.json` |
| 影响链 | U-03 → U-16 → U-18 → U-15 → U-31 |

### 3.3 关联问题编号

| 问题编号 | 标题 | 严重度 |
|---------|------|--------|
| U-01 | 降级机制不完整且不统一 | 紧急 |
| U-02 | v2 参考文档严重不足 | 紧急 |
| U-03 | 状态持久化无原子保障且存在竞态 | 紧急 |

### 3.4 验收标准

| 编号 | 验收标准 |
|------|---------|
| AC-01 | 杀死 MCP Server 进程后，全部 17 个 Tool 仍可通过降级返回结果 |
| AC-02 | 降级响应结构与正常响应一致（含 `source: "fallback"` 标识） |
| AC-03 | 降级脚本调用超时（60s）后回退到内联降级 |
| AC-04 | 每个 Phase 的 Agent 执行时可获取对应参考文档 |
| AC-05 | `mcp-tools.md` 覆盖全部 17 个 Tool |
| AC-06 | `knowledge_search` 三种 action 均有文档 |
| AC-07 | 模拟进程崩溃后重启，状态可正确恢复 |
| AC-08 | 并发读写测试无数据损坏 |
| AC-09 | 多组件同时恢复不会雪崩 |

---

## 4. v8.2.0 / v4.3.0 — P1 接口治理

### 4.1 版本目标

治理 Tool 接口设计缺陷，完善版本协商机制，解耦内部 API 依赖，使系统具备生产级接口质量。此版本依赖 v8.1.0 的降级机制修复完成。

### 4.2 主要变更

#### 4.2.1 Tool 注册解耦（U-04）

| 项目 | 说明 |
|------|------|
| 问题 | Tool 注册依赖 FastMCP 内部 API `mcp._tool_manager._tools` |
| 变更 | 维护本地 Tool 注册映射表 `_TOOL_REGISTRY`；Hook 拦截从映射表获取 Tool 函数 |
| 影响文件 | `server.py`、`hook_engine.py` |

#### 4.2.2 版本协商完善（U-05）

| 项目 | 说明 |
|------|------|
| 问题 | Skill v8.0.0 声明需要 MCP >= 4.0.0，实际 MCP 为 3.5.0；版本协商响应缺少功能信息 |
| 变更 | 升级 MCP Server 版本到 4.1.0+ 与 Skill 声明一致；`negotiate_version` 响应增加 `deprecated_features` 和 `new_features`；实现语义化版本比较逻辑 |
| 影响文件 | `server_health.py`、`config.py`、`SKILL.md` |

#### 4.2.3 knowledge 接口治理（U-06）

| 项目 | 说明 |
|------|------|
| 问题 | `knowledge_search` 包含 inject/precipitate action，与 `knowledge_inject` 职责重叠 |
| 变更 | `knowledge_search` Schema 移除 `inject` 和 `precipitate` action，仅保留 `retrieve`；所有写入操作统一通过 `knowledge_inject` 处理 |
| 影响文件 | `knowledge_search.py`、`knowledge_inject.py`、`mcp-tools.md`、`routes.yaml` |

#### 4.2.4 工具文档与暴露补全（U-07）

| 项目 | 说明 |
|------|------|
| 问题 | `server_health` 未在 `mcp-tools.md` 列出；指标系统无独立查询接口 |
| 变更 | 补充 `server_health` 完整文档；新增 `metrics_report` Tool；新增 `xuansto://metrics/summary` Resource；新增 `xuansto://degradation/status` Resource |
| 影响文件 | `mcp-tools.md`、`metrics_report.py`（新增）、`skill_resources.py` |

#### 4.2.5 ChromaDB 可选化（U-08）

| 项目 | 说明 |
|------|------|
| 问题 | ChromaDB 降级频繁，语义搜索不可靠 |
| 变更 | ChromaDB 从必需依赖降级为可选增强；默认使用 SQLite FTS5 + BM25 作为主搜索引擎；添加本地嵌入模型支持（sentence-transformers 可选） |
| 影响文件 | `search_engine.py`、`pyproject.toml` |

#### 4.2.6 降级脚本异步化（U-09）

| 项目 | 说明 |
|------|------|
| 问题 | `run_script_fallback` 使用 `subprocess.run` 同步调用，可能阻塞事件循环 |
| 变更 | 替换为 `asyncio.create_subprocess_exec`；添加超时控制（`asyncio.wait_for`，默认 60s）；保留同步版本供非 async 上下文使用 |
| 影响文件 | `subprocess_utils.py`、`degradation.py` |

#### 4.2.7 Tool 职责拆分（U-10）

| 项目 | 说明 |
|------|------|
| 问题 | `agent_status` 承担 10 种 action（查询 + 变更混合） |
| 变更 | 变更类操作拆分为 `agent_manage` Tool；`agent_status` 仅保留查询类操作 |
| 影响文件 | `agent_status.py`、`agent_manage.py`（新增）、`schemas.py`、`routes.yaml`、`mcp-tools.md` |

### 4.3 关联问题编号

| 问题编号 | 标题 | 严重度 |
|---------|------|--------|
| U-04 | Tool 注册依赖 FastMCP 内部 API | 高 |
| U-05 | 版本协商机制不完整 | 高 |
| U-06 | knowledge_search/inject 职责边界模糊 | 高 |
| U-07 | 工具文档与 MCP 暴露缺失 | 高 |
| U-08 | ChromaDB 降级频繁，语义搜索不可靠 | 高 |
| U-09 | 降级脚本调用为同步阻塞 | 高 |
| U-10 | Tool 职责过载（agent_status 10 种 action） | 高 |

### 4.4 验收标准

| 编号 | 验收标准 |
|------|---------|
| AC-10 | FastMCP 升级到最新版本后 Hook 拦截仍正常工作 |
| AC-11 | `_tool_manager._tools` 在代码中零引用 |
| AC-12 | `server_health(negotiate_version, client_version="2.0.0")` 返回功能列表 |
| AC-13 | 不兼容版本返回明确错误和升级建议 |
| AC-14 | `knowledge_search(action="inject")` 返回参数校验错误 |
| AC-15 | 所有知识写入通过 `knowledge_inject` 完成 |
| AC-16 | `mcp-tools.md` 覆盖全部 19 个 Tool（17 + `metrics_report` + `agent_manage`） |
| AC-17 | 卸载 chromadb 后知识检索仍可用（BM25 模式） |
| AC-18 | 安装 chromadb 后自动升级为混合搜索 |
| AC-19 | 降级脚本执行期间其他 MCP 调用不受影响 |
| AC-20 | `agent_status` action 枚举仅含查询类 |
| AC-21 | `agent_manage` action 枚举仅含变更类，降级路径完整 |

---

## 5. v8.3.0 / v4.4.0 — P2 架构加固

### 5.1 版本目标

加固系统架构，统一数据层存储，完善 Hook 系统类型安全，实现渐进式加载运行时协商，治理通知与错误体系。此版本解决数量最多的问题（21 个），是架构质量的关键跃升。

### 5.2 主要变更

#### 5.2.1 数据层统一（U-14, U-15, U-16, U-18）

| 项目 | 说明 |
|------|------|
| 问题 | 会话状态分散在 MD 和 JSON 中；指标文件无自动清理；内存缓存无持久化；多个 SQLite 数据库分散 |
| 变更 | 创建统一 `xuansto.db`，合并 knowledge.db + decisions.db；将 WorkflowInstance、SessionState、ResourceLoadState、DegradationState、ErrorPattern 迁移到 SQLite；保留 Markdown 快照用于人类审阅（双写）；指标存储迁移到 SQLite 支持 TTL 自动清理；关键缓存持久化到 SQLite |
| 影响文件 | `xuansto.db`（新增）、`metrics.py`、`degradation.py`、所有状态文件读写模块 |

#### 5.2.2 配置校验层（U-17）

| 项目 | 说明 |
|------|------|
| 问题 | YAML 配置无 Schema 校验，错误仅运行时暴露 |
| 变更 | 定义 `SkillConfigModel`、`FallbackConfigModel`、`ConstraintsModel` Pydantic 模型；`_load_yaml_config()` 后执行校验；校验失败使用默认值并记录警告；新增 `config_manage` Tool |
| 影响文件 | `config.py`、`schemas.py`、`config_manage.py`（新增） |

#### 5.2.3 Hook 系统加固（U-13, U-20, U-25）

| 项目 | 说明 |
|------|------|
| 问题 | Hook 拦截失败不阻塞主流程（安全检查可能被跳过）；Hook 引擎缺少类型安全；Hook 系统与 MCP 工具集成不完整 |
| 变更 | `hook_type` 改为 `HookType` 枚举；统一 Hook handler 返回类型协议；安全类 Hook（security-block）失败时默认阻塞；为每个 Hook 实现独立降级脚本；增加 Hook 失败计数和告警阈值 |
| 影响文件 | `hook_engine.py`、`server.py`、`schemas.py` |

#### 5.2.4 渐进式加载完善（U-11, U-27, U-28, U-29）

| 项目 | 说明 |
|------|------|
| 问题 | Phase 定义重复；命令路由静态无协商；DisclosureTransition Schema 已定义但未使用；FALLBACK_MAP 静态构建 |
| 变更 | SKILL.md Phase 概览表移至 references/；新增 `server_health(action="capabilities")` 返回当前可用 Tool；实现 `resource_load_status(action="disclosure_transition")` 使用 DisclosureTransition；监听 `fallback_config.yaml` 变更触发 `_resolve_fallback_map()` 重建 |
| 影响文件 | `SKILL.md`、`server_health.py`、`resource_load_status.py`、`degradation.py` |

#### 5.2.5 通知与错误治理（U-21, U-30, U-31）

| 项目 | 说明 |
|------|------|
| 问题 | 通知系统未与 MCP 协议集成；错误码 code 与 error_code 并存语义混淆；降级恢复退避缺少抖动可能雪崩 |
| 变更 | 实现 `MCPNotificationCallback`，通过 MCP Notification 推送关键事件；统一错误码：移除 `code` 字段，仅保留 `error_code`；退避计算引入抖动 |
| 影响文件 | `notification.py`（新增）、`errors.py`、`degradation.py` |

#### 5.2.6 Resource 增强（U-19, U-22, U-23）

| 项目 | 说明 |
|------|------|
| 问题 | Resource 与 Tool 功能重叠；配置热重载缺少 MCP 入口；Resource 缺少分页和过滤能力 |
| 变更 | 明确分工：Resource 只读快照，Tool 交互操作；新增 `config_manage` Tool；引入 Template Resource：`xuansto://sessions/{id}`、`xuansto://agents/{layer}/{name}` |
| 影响文件 | `skill_resources.py`、`config_manage.py` |

#### 5.2.7 Agent 与工作流治理（U-12, U-24, U-26）

| 项目 | 说明 |
|------|------|
| 问题 | MCP 路径解析失败时静默降级缺乏告警；Agent 合并策略未在运行时执行；context_compress Token 估算精度不足 |
| 变更 | 路径解析失败时记录 WARNING 日志并在 health check 中告警；在 Orchestrator 中实现 Agent 合并执行逻辑；引入可配置分词器（tiktoken 可选），压缩后验证实际 Token 数 |
| 影响文件 | `config.py`、`orchestrator.py`、`context_compress.py` |

### 5.3 关联问题编号

| 问题编号 | 标题 | 严重度 |
|---------|------|--------|
| U-11 | SKILL.md 与 constraints.yaml Phase 定义重复 | 中 |
| U-12 | MCP 路径解析失败时静默降级，缺乏告警 | 中 |
| U-13 | Hook 拦截失败不阻塞主流程，安全检查可能被跳过 | 中 |
| U-14 | 会话状态分散在 MD 和 JSON 中，关联查询困难 | 中 |
| U-15 | 指标文件无自动清理，长期运行文件膨胀 | 中 |
| U-16 | 内存缓存无持久化，进程重启后丢失 | 中 |
| U-17 | YAML 配置无 Schema 校验，错误仅运行时暴露 | 中 |
| U-18 | 多个 SQLite 数据库分散，连接管理复杂 | 中 |
| U-19 | Resource 与 Tool 功能重叠（loading/status） | 中 |
| U-20 | Hook 引擎缺少类型安全（字符串代替枚举） | 中 |
| U-21 | 通知系统未与 MCP 协议集成 | 中 |
| U-22 | 配置热重载缺少 MCP 入口 | 中 |
| U-23 | Resource 缺少分页和过滤能力 | 中 |
| U-24 | context_compress Token 估算精度不足 | 中 |
| U-25 | Hook 系统与 MCP 工具集成不完整 | 中 |
| U-26 | Agent 合并策略未在运行时执行 | 中 |
| U-27 | 命令路由为静态 YAML，缺乏运行时能力协商 | 中 |
| U-28 | DisclosureTransition Schema 已定义但未使用 | 中 |
| U-29 | FALLBACK_MAP 静态构建，热更新后不刷新 | 中 |
| U-30 | 错误码 code 与 error_code 并存，语义混淆 | 中 |
| U-31 | 降级恢复退避缺少抖动，可能雪崩 | 中 |

### 5.4 验收标准

| 编号 | 验收标准 |
|------|---------|
| AC-22 | 所有状态实体可通过 SQL 查询 |
| AC-23 | 指标自动清理超过 30 天的数据 |
| AC-24 | 进程重启后缓存从 SQLite 恢复 |
| AC-25 | 错误的 YAML 配置不会导致运行时崩溃 |
| AC-26 | `config_manage(action="validate")` 可检测配置问题 |
| AC-27 | `hook_type` 拼写错误在类型检查时发现 |
| AC-28 | security-block Hook 失败时工具调用被阻止 |
| AC-29 | Skill 启动时可动态获取可用 Tool 列表 |
| AC-30 | Phase 转换时客户端收到 DisclosureTransition 通知 |
| AC-31 | 修改 `fallback_config.yaml` 后降级路径自动更新 |
| AC-32 | 降级事件、Phase 转换、Token 超限触发 MCP Notification |
| AC-33 | 错误响应仅含 `error_code` 字段 |
| AC-34 | 文档明确 Resource vs Tool 使用场景 |
| AC-35 | `xuansto://sessions/{id}` 可查询指定会话 |
| AC-36 | 路径解析失败时 `server_health` 返回告警 |
| AC-37 | 小项目自动从 57 Agent 合并为 20 以内 |
| AC-38 | 压缩后 Token 数与目标偏差 < 10% |

---

## 6. v8.4.0 / v4.5.0 — P3 优化收尾

### 6.1 版本目标

完成低优先级优化项，完善文档体系与数据模型，清理 v1 遗留，为 v9.0.0 大版本升级做最后准备。此版本完成后，REFACTOR_PLAN.md 中全部 42 个问题均得到解决。

### 6.2 主要变更

#### 6.2.1 文档与版本治理（U-32, U-33, U-34, U-35, U-36）

| 项目 | 说明 |
|------|------|
| 问题 | 缺少评估配置、缺少 CHANGELOG、v1/v2 文件重复、SKILL.md 可能超限、工作流 YAML/MD 同步风险 |
| 变更 | 从 v1 迁移 evals/ 目录到 v2；创建 v2 CHANGELOG.md；确立 v2 为唯一维护版本，v1 标记 archived；将 SKILL.md 详细步骤外移到 references/；确定工作流 YAML 为权威源，MD 由 YAML 生成 |
| 影响文件 | `evals/`（迁移）、`CHANGELOG.md`（新增）、`SKILL.md`、`references/` |

#### 6.2.2 数据模型增强（U-37, U-38, U-39, U-40, U-41）

| 项目 | 说明 |
|------|------|
| 问题 | ErrorPattern 缺乏分类体系；WorkflowInstance 与 Decision 无显式关联；knowledge_entries 无软删除；资源缓存无 LRU 淘汰策略；快照文件无加密 |
| 变更 | ErrorPattern 添加 `error_type` 分类字段；WorkflowInstance 添加 `workflow_id` 关联到 DecisionRecord；knowledge_entries 添加 `deleted_at` 软删除字段；资源缓存实现 LRU 淘汰；快照文件可选加密（AES-256-GCM，密钥从环境变量读取） |
| 影响文件 | `schemas.py`、`xuansto.db` 迁移脚本、缓存模块 |

#### 6.2.3 安全与一致性（U-42）

| 项目 | 说明 |
|------|------|
| 问题 | 缺少速率限制；模板参数无白名单校验；Tool action 默认值不一致 |
| 变更 | 实现基于令牌桶的速率限制；模板参数 name 增加白名单正则校验；统一所有 Tool 的 action 参数为必填 |
| 影响文件 | `server.py`、`validator.py`、所有 Tool Schema |

### 6.3 关联问题编号

| 问题编号 | 标题 | 严重度 |
|---------|------|--------|
| U-32 | v2 缺少评估配置文件 | 低 |
| U-33 | v2 缺少 CHANGELOG.md | 低 |
| U-34 | v1 与 v2 存在大量重复文件 | 低 |
| U-35 | v2 SKILL.md 行数可能超过 500 行上限 | 低 |
| U-36 | 工作流 YAML 与 MD 存在同步风险 | 低 |
| U-37 | ErrorPattern 缺乏分类体系 | 低 |
| U-38 | WorkflowInstance 与 Decision 无显式关联 | 低 |
| U-39 | knowledge_entries 无软删除 | 低 |
| U-40 | 资源缓存无 LRU 淘汰策略 | 低 |
| U-41 | 快照文件无加密 | 低 |
| U-42 | 缺少速率限制/模板参数白名单/action 默认值不一致 | 低 |

### 6.4 验收标准

| 编号 | 验收标准 |
|------|---------|
| AC-39 | v1 目录可安全删除 |
| AC-40 | CHANGELOG 追踪所有变更 |
| AC-41 | SKILL.md < 200 行 |
| AC-42 | 数据模型字段完整，ErrorPattern 可按 `error_type` 分类查询 |
| AC-43 | WorkflowInstance 可关联到 DecisionRecord |
| AC-44 | knowledge_entries 软删除后不再出现在搜索结果中 |
| AC-45 | 缓存内存占用可控，LRU 淘汰正常工作 |
| AC-46 | 高频调用被限流 |
| AC-47 | 模板路径遍历被阻止 |
| AC-48 | 所有 Tool 的 action 参数为必填 |

---

## 7. v9.0.0 / v5.0.0 — 下一大版本

### 7.1 版本目标

基于 v8.4.0 / v4.5.0 的稳定基线，引入不兼容的 API 变更和重大架构升级。主要实现 API v3.0.0 协议、渐进式加载完整实现（Phase 2-3 自动推进），以及 v1 遗留代码的彻底清除。

### 7.2 主要变更

#### 7.2.1 API v3.0.0 协议升级

| 项目 | 说明 |
|------|------|
| 目标 | 统一 API 响应格式，移除历史兼容层 |
| 变更 | 移除 `code` 字段，仅保留 `error_code`（v8.3.0 已治理，v9.0.0 强制执行）；统一所有 Tool 响应为 `{status, data, error_code, metadata}` 结构；移除 v1 兼容的降级响应格式；API 版本号从 v2 升级到 v3.0.0 |
| 破坏性 | 不兼容 v8.x 客户端，需配合 Skill 层升级 |

#### 7.2.2 渐进式加载完整实现

| 项目 | 说明 |
|------|------|
| 目标 | 实现 Phase 2-3 自动推进，无需显式调用 `resource_load_status(preload, phase=N)` |
| 变更 | Phase 1→2 推进由"需要参考文档/知识检索"自动触发（v8.3.0 已实现 DisclosureTransition，v9.0.0 改为自动推进）；Phase 2→3 推进由"深度分析/安全扫描"自动触发；Token 预算监控与自动降级闭环；完整 Phase 转换通知体系 |
| 性能目标 | Phase 0→1 推进延迟 ≤500ms；Phase 1→2 推进延迟 ≤2000ms；Phase 2→3 推进延迟 ≤5000ms |

#### 7.2.3 v1 遗留彻底清除

| 项目 | 说明 |
|------|------|
| 目标 | 移除所有 v1 兼容代码和文件 |
| 变更 | 删除 `xuansto-skill/` 目录（v1）；移除 `constraints.yaml` 中 v1 兼容的 Phase 定义；统一 Skill 命名空间为 `xuansto-skill-v2`；清理 `scripts/` 中仅 v1 使用的脚本 |
| 破坏性 | v1 Skill 完全不可用 |

#### 7.2.4 MCP Server 架构升级

| 项目 | 说明 |
|------|------|
| 目标 | MCP Server 内部架构升级，提升可维护性 |
| 变更 | Tool 注册完全基于公开 API（v8.2.0 已解耦，v5.0.0 移除内部 API 兼容层）；搜索引擎默认 BM25 + 可选向量搜索（v8.2.0 已实现，v5.0.0 移除 ChromaDB 必需依赖声明）；统一 SQLite 存储引擎（v8.3.0 已迁移，v5.0.0 移除 JSON 状态文件兼容读取） |

### 7.3 关联问题编号

v9.0.0 / v5.0.0 不直接关联 U-01~U-42 中的未解决问题（v8.4.0 已全部解决），但以下问题的治理成果在此版本中成为强制要求：

| 问题编号 | 关联说明 |
|---------|---------|
| U-01 | 降级机制在 v9.0.0 中移除 v1 兼容降级路径 |
| U-04 | Tool 注册在 v5.0.0 中完全移除内部 API 兼容层 |
| U-05 | API v3.0.0 强制版本协商，不支持 v2 客户端 |
| U-06 | `knowledge_search` 在 v5.0.0 中移除 inject/precipitate 兼容处理 |
| U-08 | ChromaDB 在 v5.0.0 中从必需依赖声明中移除 |
| U-34 | v1 目录在 v9.0.0 中彻底删除 |

### 7.4 验收标准

| 编号 | 验收标准 |
|------|---------|
| AC-49 | API v3.0.0 客户端可正常调用全部 Tool |
| AC-50 | API v2.x 客户端调用返回明确的不兼容错误 |
| AC-51 | Phase 0→1→2 自动推进，无需显式 preload |
| AC-52 | Token 预算超限时自动降级并通知客户端 |
| AC-53 | `xuansto-skill/` 目录不存在 |
| AC-54 | `_tool_manager._tools` 引用不存在 |
| AC-55 | `chromadb` 不在 `pyproject.toml` 必需依赖中 |
| AC-56 | JSON 状态文件兼容读取代码不存在 |
| AC-57 | 全部 42 个 U-01~U-42 问题的回归测试通过 |

---

## 8. 版本兼容性矩阵

### 8.1 Skill 与 MCP Server 版本对应关系

| Skill 版本 | MCP Server 版本 | API 版本 | 兼容范围 |
|-----------|----------------|---------|---------|
| v8.0.0 | v4.1.0 | v2.0.0 | 当前发布版 |
| v8.1.0 | v4.2.0 | v2.0.0 | 向后兼容 v8.0.0 / v4.1.0 |
| v8.2.0 | v4.3.0 | v2.1.0 | 向后兼容 v8.1.0 / v4.2.0；`knowledge_search.inject` 标记 deprecated |
| v8.3.0 | v4.4.0 | v2.2.0 | 向后兼容 v8.2.0 / v4.3.0；`code` 字段标记 deprecated |
| v8.4.0 | v4.5.0 | v2.3.0 | 向后兼容 v8.3.0 / v4.4.0；v1 Skill 标记 archived |
| v9.0.0 | v5.0.0 | v3.0.0 | 不兼容 v8.x；需同时升级 Skill 和 MCP Server |

### 8.2 渐进式加载版本演进

| 版本 | Phase 0→1 | Phase 1→2 | Phase 2→3 | Token 降级 |
|------|-----------|-----------|-----------|-----------|
| v8.0.0 | 自动 | 显式 preload | 显式 preload | 无 |
| v8.1.0 | 自动 | 显式 preload | 显式 preload | 无 |
| v8.2.0 | 自动 | 显式 preload | 显式 preload | 无 |
| v8.3.0 | 自动 | DisclosureTransition 提示 | DisclosureTransition 提示 | 手动触发 |
| v8.4.0 | 自动 | DisclosureTransition 提示 | DisclosureTransition 提示 | 手动触发 |
| v9.0.0 | 自动 | **自动推进** | **自动推进** | **自动降级** |

### 8.3 降级机制版本演进

| 版本 | MCP 调用 | 脚本降级 | 内联降级 | 最小响应 | 异步化 |
|------|---------|---------|---------|---------|--------|
| v8.0.0 | ✓ | ✗（断裂） | 部分 | 部分 | ✗ |
| v8.1.0 | ✓ | ✓ | ✓ | ✓ | ✗ |
| v8.2.0 | ✓ | ✓ | ✓ | ✓ | ✓ |
| v9.0.0 | ✓ | ✓ | ✓ | ✓ | ✓（移除同步兼容） |

---

## 9. 升级与回退策略

### 9.1 升级路径

```
v8.0.0/v4.1.0 ──→ v8.1.0/v4.2.0 ──→ v8.2.0/v4.3.0 ──→ v8.3.0/v4.4.0 ──→ v8.4.0/v4.5.0 ──→ v9.0.0/v5.0.0
     │                  │                  │                  │                  │                  │
     │                  │                  │                  │                  │                  │
     ▼                  ▼                  ▼                  ▼                  ▼                  ▼
  直接升级           直接升级           直接升级           直接升级           直接升级         需同时升级
  无迁移             无迁移             无迁移            数据迁移           数据迁移        Skill+MCP
                    降级链修复        knowledge API      SQLite统一         v1归档          API v3
                                      变更（兼容）       （自动迁移）       （可选）
```

### 9.2 各版本升级注意事项

| 版本升级 | 数据迁移 | 配置变更 | 破坏性变更 |
|---------|---------|---------|-----------|
| v8.0.0 → v8.1.0 | 无 | 无 | 无 |
| v8.1.0 → v8.2.0 | 无 | `knowledge_search` inject/precipitate 标记 deprecated | 无（兼容期） |
| v8.2.0 → v8.3.0 | JSON → SQLite（自动迁移） | `fallback_config.yaml` 支持热重载 | `code` 字段标记 deprecated |
| v8.3.0 → v8.4.0 | SQLite Schema 升级（自动） | 无 | v1 Skill 标记 archived |
| v8.4.0 → v9.0.0 | 无（v8.4.0 已完成迁移） | API 版本协商强制 v3 | `knowledge_search.inject` 移除；`code` 字段移除；v1 删除 |

### 9.3 回退策略

| 场景 | 回退方案 | 数据影响 |
|------|---------|---------|
| v8.1.0 → v8.0.0 | 直接替换文件 | 无影响（v8.1.0 不改变数据格式） |
| v8.2.0 → v8.1.0 | 替换文件 + 恢复 `knowledge_search` inject action | 无影响（v8.2.0 兼容期保留旧 action） |
| v8.3.0 → v8.2.0 | 替换文件 + 从 SQLite 导出 JSON 状态 | 需运行 `migrate_rollback.py` |
| v8.4.0 → v8.3.0 | 替换文件 + SQLite Schema 回退 | 需运行 Schema 降级脚本 |
| v9.0.0 → v8.4.0 | 替换文件 + API 降级 | 不支持自动回退，需手动调整 |

### 9.4 Deprecated 功能时间线

| 功能 | Deprecated 版本 | 移除版本 | 替代方案 |
|------|----------------|---------|---------|
| `knowledge_search(action="inject")` | v8.2.0 / v4.3.0 | v9.0.0 / v5.0.0 | `knowledge_inject` |
| `knowledge_search(action="precipitate")` | v8.2.0 / v4.3.0 | v9.0.0 / v5.0.0 | `knowledge_inject(action="precipitate")` |
| 错误响应 `code` 字段 | v8.3.0 / v4.4.0 | v9.0.0 / v5.0.0 | `error_code` 字段 |
| JSON 状态文件读取 | v8.3.0 / v4.4.0 | v9.0.0 / v5.0.0 | SQLite 统一存储 |
| v1 Skill 目录 | v8.4.0 / v4.5.0 | v9.0.0 / v5.0.0 | v2 Skill |
| `subprocess.run` 同步降级 | v8.2.0 / v4.3.0 | v9.0.0 / v5.0.0 | `asyncio.create_subprocess_exec` |
| `_tool_manager._tools` 内部 API | v8.2.0 / v4.3.0 | v9.0.0 / v5.0.0 | `_TOOL_REGISTRY` 映射表 |
| ChromaDB 必需依赖 | v8.2.0 / v4.3.0 | v9.0.0 / v5.0.0 | 可选增强依赖 |
