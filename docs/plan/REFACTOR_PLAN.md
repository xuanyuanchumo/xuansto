# Xuansto Skill 整合重构迭代方案

> 版本: 2.0.0 | 日期: 2026-05-23 | 状态: 已实施
> 来源文档: ARCHITECTURE.md / DATABASE_DESIGN.md / MCP_REVIEW.md / SKILL_REVIEW.md / API_SPECIFICATION.md

---

## 目录

1. [统一问题清单](#1-统一问题清单)
2. [影响链分析](#2-影响链分析)
3. [优先级矩阵](#3-优先级矩阵)
4. [模块化重构步骤](#4-模块化重构步骤)
5. [渐进式加载披露实现方案](#5-渐进式加载披露实现方案)
6. [测试策略](#6-测试策略)
7. [持续集成建议](#7-持续集成建议)

---

## 1. 统一问题清单

### 1.1 去重合并说明

五份分析文档共发现 63 个问题（ARCH-12 + DB-12 + MCP-15 + SKILL-12 + API-12），经去重合并后为 **42 个独立问题**。合并规则：

- 语义相同、来源不同的问题合并为一条，保留所有原始编号
- 子问题（如 ARCH-06-1~4）拆分为独立条目
- 信息性问题（如 ARCH-01 元数据声明）不纳入重构清单

### 1.2 合并后问题清单

| 统一编号 | 原始编号 | 问题标题 | 影响域 | 严重度 | 状态 |
|---------|---------|---------|--------|--------|------|
| U-01 | SKILL-01, MCP-03, ARCH-06-2 | 降级机制不完整且不统一 | Skill, MCP, 架构 | 紧急 | ✅ RESOLVED: subprocess_utils异步降级 |
| U-02 | SKILL-02 | v2参考文档严重不足 | Skill | 紧急 | ✅ RESOLVED: v2已有75+参考文件 |
| U-03 | DB-01, MCP-10, API-10 | 状态持久化无原子保障且存在竞态 | 数据, MCP, API | 紧急 | ✅ RESOLVED: xuansto.db统一存储+写入锁+hash验证 |
| U-04 | MCP-11, API-04 | Tool注册依赖FastMCP内部API | MCP, API | 高 | ✅ RESOLVED: 本地_TOOL_FUNCTIONS注册表 |
| U-05 | SKILL-03, MCP-08, API-03 | 版本协商机制不完整，Skill与MCP版本不一致 | Skill, MCP, API | 高 | ✅ RESOLVED: MCP Server升级到v8.0.0 |
| U-06 | SKILL-04, MCP-13, API-07 | knowledge_search/inject职责边界模糊 | Skill, MCP, API | 高 | ✅ RESOLVED: knowledge_search改为retrieve only |
| U-07 | SKILL-05, MCP-05 | 工具文档与MCP暴露缺失 | Skill, MCP | 高 | ✅ RESOLVED: metrics_report+config_manage Tool |
| U-08 | DB-02 | ChromaDB降级频繁，语义搜索不可靠 | 数据, MCP | 高 | ✅ RESOLVED: ChromaDB可选化+HybridSearchEngine |
| U-09 | API-05 | 降级脚本调用为同步阻塞，可能阻塞事件循环 | API, MCP | 高 | ✅ RESOLVED: subprocess_utils异步调用 |
| U-10 | MCP-01 | Tool职责过载（agent_status 10种action） | MCP | 高 | ✅ RESOLVED: 拆分为agent_status+agent_manage |
| U-11 | ARCH-06-1 | SKILL.md与constraints.yaml Phase定义重复 | Skill, 架构 | 中 | ✅ RESOLVED: SKILL.md精简至<200行 |
| U-12 | ARCH-06-3 | MCP路径解析失败时静默降级，缺乏告警 | MCP, 架构 | 中 | ✅ RESOLVED: MCPNotificationCallback通知 |
| U-13 | ARCH-06-4 | Hook拦截失败不阻塞主流程，安全检查可能被跳过 | MCP, 架构 | 中 | ✅ RESOLVED: 安全Hook失败默认阻塞+失败计数 |
| U-14 | DB-03 | 会话状态分散在MD和JSON中，关联查询困难 | 数据 | 中 | ✅ RESOLVED: xuansto.db session_states表 |
| U-15 | DB-04 | 指标文件无自动清理，长期运行文件膨胀 | 数据 | 中 | ✅ RESOLVED: xuansto.db tool_metrics表+TTL清理 |
| U-16 | DB-05 | 内存缓存无持久化，进程重启后丢失 | 数据 | 中 | ✅ RESOLVED: xuansto.db持久化+atexit handler |
| U-17 | DB-06 | YAML配置无Schema校验，错误仅运行时暴露 | 数据, 架构 | 中 | 待实施 |
| U-18 | DB-11 | 多个SQLite数据库分散，连接管理复杂 | 数据 | 中 | ✅ RESOLVED: 统一xuansto.db(8表) |
| U-19 | MCP-02 | Resource与Tool功能重叠（loading/status） | MCP | 中 | ✅ RESOLVED: 明确分工-Resource只读快照/Tool交互操作 |
| U-20 | MCP-04 | Hook引擎缺少类型安全（字符串代替枚举） | MCP | 中 | ✅ RESOLVED: HookType枚举 |
| U-21 | MCP-06 | 通知系统未与MCP协议集成 | MCP | 中 | ✅ RESOLVED: MCPNotificationCallback |
| U-22 | MCP-07 | 配置热重载缺少MCP入口 | MCP | 中 | ✅ RESOLVED: config_manage Tool |
| U-23 | MCP-09 | Resource缺少分页和过滤能力 | MCP | 中 | ✅ RESOLVED: sessions/{id}+agents/{layer}/{name}参数化Resource |
| U-24 | MCP-14 | context_compress Token估算精度不足 | MCP | 中 | 待实施 |
| U-25 | SKILL-10 | Hook系统与MCP工具集成不完整 | Skill, MCP | 中 | ✅ RESOLVED: HookType枚举+安全阻断+失败计数 |
| U-26 | SKILL-11 | Agent合并策略未在运行时执行 | Skill | 中 | 待实施 |
| U-27 | API-01 | 命令路由为静态YAML，缺乏运行时能力协商 | API, Skill | 中 | 待实施 |
| U-28 | API-02 | DisclosureTransition Schema已定义但未使用 | API, 特效 | 中 | ✅ RESOLVED: DisclosureTransition状态机已实现 |
| U-29 | API-06 | FALLBACK_MAP静态构建，热更新后不刷新 | API, MCP | 中 | ✅ RESOLVED: config_manage reload |
| U-30 | API-08 | 错误码code与error_code并存，语义混淆 | API | 中 | ✅ RESOLVED: 统一error_code, deprecated code字段 |
| U-31 | API-12 | 降级恢复退避缺少抖动，可能雪崩 | API, MCP | 中 | ✅ RESOLVED: backoff jitter |
| U-32 | SKILL-06 | v2缺少评估配置文件 | Skill | 低 | 待实施 |
| U-33 | SKILL-07 | v2缺少CHANGELOG.md | Skill | 低 | 待实施 |
| U-34 | SKILL-08 | v1与v2存在大量重复文件 | Skill, 架构 | 低 | ✅ RESOLVED: v1标记ARCHIVED |
| U-35 | SKILL-09 | v2 SKILL.md行数可能超过500行上限 | Skill | 低 | ✅ RESOLVED: SKILL.md精简至<200行 |
| U-36 | SKILL-12 | 工作流YAML与MD存在同步风险 | Skill | 低 | 待实施 |
| U-37 | DB-07 | ErrorPattern缺乏分类体系 | 数据 | 低 | ✅ RESOLVED: error_type字段+database.py |
| U-38 | DB-08 | WorkflowInstance与Decision无显式关联 | 数据 | 低 | ✅ RESOLVED: workflow_id关联字段 |
| U-39 | DB-09 | knowledge_entries无软删除 | 数据 | 低 | ✅ RESOLVED: deleted_at字段+knowledge_inject(delete) |
| U-40 | DB-10 | 资源缓存无LRU淘汰策略 | 数据 | 低 | ✅ RESOLVED: cache.py LRU缓存 |
| U-41 | DB-12 | 快照文件无加密 | 数据 | 低 | ✅ RESOLVED: crypto.py AES-256-GCM |
| U-42 | MCP-12, API-09, API-11 | 缺少速率限制/模板参数白名单/action默认值不一致 | MCP, API | 低 | ✅ RESOLVED: rate_limiter.py令牌桶+名称白名单+action必填 |

### 1.3 按影响域统计

| 影响域 | 问题数 | 紧急 | 高 | 中 | 低 |
|--------|--------|------|---|---|---|
| Skill | 10 | 2 | 2 | 2 | 4 |
| MCP | 14 | 2 | 3 | 6 | 3 |
| 数据 | 11 | 1 | 1 | 4 | 5 |
| API | 10 | 1 | 2 | 5 | 2 |
| 架构 | 5 | 1 | 0 | 3 | 1 |
| 特效 | 1 | 0 | 0 | 1 | 0 |

---

## 2. 影响链分析

### 2.1 核心影响链：降级机制断裂

```
U-01 降级机制不完整
  ├── 影响: degradation.py → scripts/ 调用链断裂
  ├── 连锁: U-09 (同步阻塞) → 事件循环卡死
  ├── 连锁: U-29 (FALLBACK_MAP静态) → 热更新失效
  ├── 连锁: U-25 (Hook降级不完整) → 安全检查被跳过
  └── 连锁: U-08 (ChromaDB降级) → 知识检索完全失效
      └── 连锁: U-14 (会话状态分散) → 降级后无法恢复上下文

涉及文件:
  xuansto-mcp-server/src/xuansto_mcp/core/degradation.py
  xuansto-mcp-server/src/xuansto_mcp/core/subprocess_utils.py
  xuansto-mcp-server/src/xuansto_mcp/server.py (_with_hook_interception)
  .trae/skills/xuansto-skill-v2/constraints.yaml
  .trae/skills/xuansto-skill-v2/scripts/*.py (60+脚本)

外部依赖:
  FastMCP (mcp[cli]>=1.0.0)
  Python subprocess 模块
  ChromaDB (可选)
```

### 2.2 核心影响链：状态持久化不可靠

```
U-03 状态持久化无原子保障
  ├── 影响: resource_state.json / degradation_state.json / workflow实例
  ├── 连锁: U-16 (内存缓存无持久化) → 进程重启后全部丢失
  ├── 连锁: U-18 (SQLite分散) → 跨库事务无法保证
  ├── 连锁: U-15 (指标文件膨胀) → 磁盘空间耗尽
  └── 连锁: U-31 (退避无抖动) → 多组件同时恢复雪崩

涉及文件:
  xuansto-mcp-server/src/xuansto_mcp/core/degradation.py (_persist_state)
  xuansto-mcp-server/src/xuansto_mcp/tools/resource_load_status.py
  xuansto-mcp-server/src/xuansto_mcp/tools/workflow_dispatch.py
  xuansto-mcp-server/src/xuansto_mcp/core/metrics.py
  .xuansto/ 目录下所有JSON文件

外部依赖:
  SQLite (WAL模式)
  os.replace / tempfile (atomic_write)
```

### 2.3 核心影响链：Tool接口设计缺陷

```
U-04 Tool注册依赖内部API
  ├── 影响: server.py → mcp._tool_manager._tools
  ├── 连锁: U-10 (Tool职责过载) → 参数校验复杂
  ├── 连锁: U-06 (knowledge职责模糊) → 调用者困惑
  ├── 连锁: U-19 (Resource/Tool重叠) → loading/status歧义
  └── 连锁: U-30 (错误码混淆) → 错误处理不一致

涉及文件:
  xuansto-mcp-server/src/xuansto_mcp/server.py
  xuansto-mcp-server/src/xuansto_mcp/tools/knowledge_search.py
  xuansto-mcp-server/src/xuansto_mcp/tools/knowledge_inject.py
  xuansto-mcp-server/src/xuansto_mcp/tools/agent_status.py
  xuansto-mcp-server/src/xuansto_mcp/tools/resource_load_status.py
  xuansto-mcp-server/src/xuansto_mcp/resources/skill_resources.py
  xuansto-mcp-server/src/xuansto_mcp/core/errors.py
  xuansto-mcp-server/src/xuansto_mcp/models/schemas.py

外部依赖:
  FastMCP SDK (内部API可能变更)
```

### 2.4 核心影响链：版本与文档不一致

```
U-05 版本协商不完整
  ├── 影响: Skill v8.0.0 vs MCP Server v3.5.0
  ├── 连锁: U-07 (工具文档缺失) → 用户无法使用完整功能
  ├── 连锁: U-02 (参考文档不足) → Agent执行缺乏指引
  └── 连锁: U-27 (静态路由无协商) → 降级时命令路由失效

涉及文件:
  .trae/skills/xuansto-skill-v2/SKILL.md
  .trae/skills/xuansto-skill-v2/references/mcp-tools.md
  .trae/skills/xuansto-skill-v2/commands/routes.yaml
  xuansto-mcp-server/src/xuansto_mcp/tools/server_health.py
  xuansto-mcp-server/src/xuansto_mcp/core/config.py

外部依赖:
  MCP API版本约定
  Skill平台版本约束
```

### 2.5 模块依赖热力图

```
                    Skill层          MCP Server        数据层
                  ┌─────────┐    ┌──────────────┐   ┌──────────┐
  SKILL.md        │ ■■■■■■■ │    │              │   │          │
  constraints.yaml│ ■■■■■□□ │───▶│ ■■■□□□□     │   │          │
  routes.yaml     │ ■■■■□□□ │───▶│ ■■■■■□□     │   │          │
  registry.yaml   │ ■■■□□□□ │───▶│ ■■□□□□□     │   │          │
  server.py       │          │    │ ■■■■■■■     │──▶│ ■■■■□□□  │
  degradation.py  │          │    │ ■■■■■□□     │──▶│ ■■■■■■■  │
  hook_engine.py  │          │    │ ■■■□□□□     │   │ ■□□□□□□  │
  search_engine.py│          │    │ ■■■■□□□     │──▶│ ■■■■■■□  │
  metrics.py      │          │    │ ■■□□□□□     │──▶│ ■■■□□□□  │
  schemas.py      │          │    │ ■■■■■□□     │   │          │
                  └─────────┘    └──────────────┘   └──────────┘

  ■ = 影响深度 (1-7级)   □ = 无直接影响
  高影响模块: server.py, degradation.py, search_engine.py
```

---

## 3. 优先级矩阵

### 3.1 优先级定义

| 级别 | 定义 | 修复时限 | 依据 |
|------|------|---------|------|
| **紧急** | 系统核心功能不可用，阻塞正常使用 | 1周内 | P0问题 + 影响链根节点 |
| **高** | 重要功能受损或存在兼容性风险 | 2周内 | P1问题 + 影响链关键节点 |
| **中** | 功能可用但体验/可维护性受损 | 1个迭代内 | P2问题 + 影响链传播节点 |
| **低** | 优化改进项，不影响核心功能 | 后续迭代 | P3问题 + 影响链末端 |

### 3.2 优先级矩阵

| 统一编号 | 问题标题 | 优先级 | 依据 | 影响链深度 | 修复复杂度 |
|---------|---------|--------|------|-----------|-----------|
| U-01 | 降级机制不完整且不统一 | 紧急 | 系统完全不可用的根因 | 4层 | 高 |
| U-02 | v2参考文档严重不足 | 紧急 | Agent执行缺乏必要指引 | 2层 | 低 |
| U-03 | 状态持久化无原子保障且存在竞态 | 紧急 | 数据丢失风险 | 4层 | 高 |
| U-04 | Tool注册依赖FastMCP内部API | 高 | SDK升级可能导致全面失效 | 3层 | 中 |
| U-05 | 版本协商机制不完整 | 高 | 版本不匹配导致调用失败 | 3层 | 中 |
| U-06 | knowledge_search/inject职责边界模糊 | 高 | 接口误用风险 | 2层 | 中 |
| U-07 | 工具文档与MCP暴露缺失 | 高 | 功能不可发现不可用 | 2层 | 低 |
| U-08 | ChromaDB降级频繁 | 高 | 知识检索核心能力受损 | 2层 | 中 |
| U-09 | 降级脚本同步阻塞 | 高 | 事件循环卡死风险 | 2层 | 中 |
| U-10 | Tool职责过载 | 高 | 参数校验复杂，易误用 | 2层 | 中 |
| U-11 | Phase定义重复 | 中 | 维护不一致风险 | 1层 | 低 |
| U-12 | 路径解析静默降级 | 中 | 问题难以发现 | 1层 | 低 |
| U-13 | Hook拦截失败不阻塞 | 中 | 安全检查可能被跳过 | 2层 | 中 |
| U-14 | 会话状态分散 | 中 | 关联查询困难 | 2层 | 中 |
| U-15 | 指标文件无清理 | 中 | 磁盘膨胀 | 1层 | 低 |
| U-16 | 内存缓存无持久化 | 中 | 重启后状态丢失 | 2层 | 中 |
| U-17 | YAML配置无Schema校验 | 中 | 配置错误运行时才暴露 | 1层 | 中 |
| U-18 | SQLite数据库分散 | 中 | 跨库事务困难 | 2层 | 高 |
| U-19 | Resource与Tool功能重叠 | 中 | 调用者困惑 | 1层 | 低 |
| U-20 | Hook引擎缺少类型安全 | 中 | 拼写错误导致注册失败 | 1层 | 低 |
| U-21 | 通知系统未与MCP集成 | 中 | 关键事件无法实时通知 | 1层 | 中 |
| U-22 | 配置热重载缺少MCP入口 | 中 | 运维无法主动触发 | 1层 | 低 |
| U-23 | Resource缺少分页过滤 | 中 | 大数据集Token浪费 | 1层 | 中 |
| U-24 | Token估算精度不足 | 中 | 上下文管理不精确 | 1层 | 中 |
| U-25 | Hook与MCP集成不完整 | 中 | 降级模式Hook覆盖不全 | 2层 | 中 |
| U-26 | Agent合并策略未执行 | 中 | 小项目Token浪费 | 1层 | 中 |
| U-27 | 命令路由静态无协商 | 中 | 降级时路由失效 | 2层 | 中 |
| U-28 | DisclosureTransition未使用 | 中 | 渐进式加载转换通知缺失 | 1层 | 中 |
| U-29 | FALLBACK_MAP静态构建 | 中 | 热更新后降级配置失效 | 2层 | 中 |
| U-30 | 错误码语义混淆 | 中 | 错误处理不一致 | 1层 | 低 |
| U-31 | 退避缺少抖动 | 中 | 恢复雪崩风险 | 1层 | 低 |
| U-32 | 缺少评估配置 | 低 | 无法评估技能质量 | 0层 | 低 |
| U-33 | 缺少CHANGELOG | 低 | 版本变更不可追踪 | 0层 | 低 |
| U-34 | v1/v2文件重复 | 低 | 维护成本增加 | 0层 | 低 |
| U-35 | SKILL.md行数可能超限 | 低 | Token消耗增加 | 0层 | 低 |
| U-36 | 工作流YAML/MD同步风险 | 低 | 执行歧义 | 0层 | 低 |
| U-37 | ErrorPattern无分类 | 低 | 模式匹配效率低 | 0层 | 低 |
| U-38 | Workflow/Decision无关联 | 低 | 决策来源不可追溯 | 0层 | 低 |
| U-39 | knowledge_entries无软删除 | 低 | 注入知识无法撤销 | 0层 | 低 |
| U-40 | 缓存无LRU淘汰 | 低 | 内存占用不可控 | 0层 | 低 |
| U-41 | 快照文件无加密 | 低 | 敏感信息泄露风险 | 0层 | 低 |
| U-42 | 速率限制/白名单/默认值 | 低 | 安全与一致性 | 0层 | 低 |

### 3.3 优先级分布

```
紧急 (3)  ████████  7.1%
高   (7)  ██████████████████  16.7%
中   (21) ████████████████████████████████████████████████████████  50.0%
低   (11) ████████████████████████████  26.2%
```

---

## 4. 模块化重构步骤

### 4.1 阶段总览

| 阶段 | 名称 | 周期 | 解决问题 | 前置依赖 |
|------|------|------|---------|---------|
| P0 | 紧急修复 | 第1周 | U-01, U-02, U-03 | 无 |
| P1 | 接口治理 | 第2-3周 | U-04, U-05, U-06, U-07, U-08, U-09, U-10 | P0 |
| P2 | 架构加固 | 第4-5周 | U-11~U-31 | P1 |
| P3 | 优化收尾 | 第6周+ | U-32~U-42 | P2 |

### 4.2 P0: 紧急修复

#### P0-A: 降级机制修复 (U-01)

| 项目 | 内容 |
|------|------|
| **输入** | 当前 degradation.py 仅返回 fallback 响应；constraints.yaml 声明了降级路径 |
| **步骤** | 1. 实现 `subprocess_utils.py` 到 `scripts/` 目录的实际调用链<br>2. 统一降级框架：MCP调用 → 脚本降级 → 内联降级 → 最小响应<br>3. 降级脚本路径从 `fallback_config.yaml` 读取而非硬编码<br>4. 为每个内联降级提取为独立脚本或统一内联框架 |
| **输出** | MCP Server 不可用时系统仍可通过脚本降级运行 |
| **验收标准** | 1. 杀死 MCP Server 进程后，所有 17 个 Tool 仍可通过降级返回结果<br>2. 降级响应结构与正常响应一致（含 `source: "fallback"` 标识）<br>3. 降级脚本调用超时（60s）后回退到内联降级 |
| **依赖** | 无 |

#### P0-B: 参考文档补充 (U-02)

| 项目 | 内容 |
|------|------|
| **输入** | v2 references/ 仅 6 个文件；v1 有 72+ 参考文件 |
| **步骤** | 1. 盘点 v1 参考文件，识别 v2 必需的参考文档<br>2. 迁移关键参考文件（编码规范、安全指南、桌面开发指南、Hook系统、模型路由、并行化策略）<br>3. 补充 server_health 工具文档到 mcp-tools.md<br>4. 补充 knowledge_search inject/precipitate 文档 |
| **输出** | v2 references/ 包含所有必要参考文档 |
| **验收标准** | 1. 每个 Phase 的 Agent 执行时可获取对应参考文档<br>2. mcp-tools.md 覆盖全部 17 个 Tool<br>3. knowledge_search 三种 action 均有文档 |
| **依赖** | 无 |

#### P0-C: 状态持久化修复 (U-03)

| 项目 | 内容 |
|------|------|
| **输入** | JSON 状态文件使用 atomic_write 但存在竞态；daemon 线程退出时可能丢失状态 |
| **步骤** | 1. 在 `atexit` 注册 `_persist_state()` 确保状态落盘<br>2. 在 `load_state` 中增加完整性校验（时间戳 + 内容哈希）<br>3. 为关键状态文件添加写入锁（`threading.Lock` + 文件锁）<br>4. 降级恢复退避引入随机抖动（`jitter = random.uniform(0, 0.5) * delay`） |
| **输出** | 状态持久化具备原子性和完整性保障 |
| **验收标准** | 1. 模拟进程崩溃后重启，状态可正确恢复<br>2. 并发读写测试无数据损坏<br>3. 多组件同时恢复不会雪崩 |
| **依赖** | 无 |

### 4.3 P1: 接口治理

#### P1-A: Tool注册解耦 (U-04)

| 项目 | 内容 |
|------|------|
| **输入** | server.py 通过 `mcp._tool_manager._tools` 访问内部属性 |
| **步骤** | 1. 在 server.py 中维护本地 Tool 注册映射表 `_TOOL_REGISTRY: dict[str, Callable]`<br>2. 使用 FastMCP 装饰器 `@mcp.tool()` 注册时同步写入映射表<br>3. Hook 拦截从映射表获取 Tool 函数，不再访问 `_tool_manager`<br>4. 向 FastMCP 贡献公开 Tool 注册表 API 的 Issue |
| **输出** | Tool 注册不再依赖 FastMCP 内部 API |
| **验收标准** | 1. FastMCP 升级到最新版本后 Hook 拦截仍正常工作<br>2. `_tool_manager._tools` 在代码中零引用 |
| **依赖** | P0-A |

#### P1-B: 版本协商完善 (U-05)

| 项目 | 内容 |
|------|------|
| **输入** | Skill v8.0.0 声明需要 MCP >= 4.0.0，实际 MCP 为 3.5.0；版本协商响应缺少功能信息 |
| **步骤** | 1. 升级 MCP Server 版本到 4.1.0+ 与 Skill 声明一致<br>2. 在 `negotiate_version` 响应中增加 `deprecated_features` 和 `new_features`<br>3. SKILL.md 和 MCP Server README 互相声明兼容版本<br>4. 实现语义化版本比较逻辑（semver） |
| **输出** | 版本协商机制完整，客户端可获知功能差异 |
| **验收标准** | 1. `server_health(negotiate_version, client_version="2.0.0")` 返回功能列表<br>2. 不兼容版本返回明确错误和升级建议 |
| **依赖** | P0-B |

#### P1-C: knowledge接口治理 (U-06)

| 项目 | 内容 |
|------|------|
| **输入** | knowledge_search 包含 inject/precipitate action，与 knowledge_inject 职责重叠 |
| **步骤** | 1. 从 `knowledge_search` Schema 中移除 `inject` 和 `precipitate` action，仅保留 `retrieve`<br>2. 所有写入操作统一通过 `knowledge_inject` 处理<br>3. 更新 mcp-tools.md 文档<br>4. 更新 routes.yaml 中引用 knowledge_search inject 的命令路由 |
| **输出** | knowledge_search 只读，knowledge_inject 只写，职责清晰 |
| **验收标准** | 1. `knowledge_search(action="inject")` 返回参数校验错误<br>2. 所有知识写入通过 `knowledge_inject` 完成 |
| **依赖** | P0-B |

#### P1-D: 降级脚本异步化 (U-09)

| 项目 | 内容 |
|------|------|
| **输入** | `run_script_fallback` 使用 `subprocess.run` 同步调用 |
| **步骤** | 1. 将 `subprocess.run` 替换为 `asyncio.create_subprocess_exec`<br>2. 添加超时控制（`asyncio.wait_for`，默认 60s）<br>3. 保留同步版本 `run_script_fallback_sync` 供非 async 上下文使用 |
| **输出** | 降级脚本调用不再阻塞事件循环 |
| **验收标准** | 1. 降级脚本执行期间其他 MCP 调用不受影响<br>2. 超时后正确回退到内联降级 |
| **依赖** | P0-A |

#### P1-E: Tool职责拆分 (U-10)

| 项目 | 内容 |
|------|------|
| **输入** | agent_status 承担 10 种 action（查询 + 变更混合） |
| **步骤** | 1. 将变更类操作（create/assign/release/instance_status/destroy/schedule）拆分为 `agent_manage` Tool<br>2. `agent_status` 仅保留查询类操作（list/by_phase/detail/match）<br>3. 更新 schemas.py、routes.yaml、mcp-tools.md |
| **输出** | Tool 职责单一，参数校验简化 |
| **验收标准** | 1. `agent_status` action 枚举仅含查询类<br>2. `agent_manage` action 枚举仅含变更类<br>3. 降级路径完整 |
| **依赖** | P0-A |

#### P1-F: ChromaDB可选化 (U-08)

| 项目 | 内容 |
|------|------|
| **输入** | ChromaDB 降级频繁，影响语义搜索 |
| **步骤** | 1. 将 ChromaDB 从必需依赖降级为可选增强<br>2. 默认使用 SQLite FTS5 + BM25 作为主搜索引擎<br>3. 添加本地嵌入模型支持（sentence-transformers 可选）<br>4. 搜索引擎注册表机制保持不变 |
| **输出** | 无 ChromaDB 时系统仍可正常搜索 |
| **验收标准** | 1. 卸载 chromadb 后知识检索仍可用（BM25 模式）<br>2. 安装 chromadb 后自动升级为混合搜索 |
| **依赖** | P0-A |

#### P1-G: 工具文档与暴露补全 (U-07)

| 项目 | 内容 |
|------|------|
| **输入** | server_health 未在 mcp-tools.md 列出；指标系统无独立查询接口 |
| **步骤** | 1. 补充 server_health 完整文档到 mcp-tools.md<br>2. 新增 `metrics_report` Tool（按 Tool/时间/类型查询）<br>3. 新增 `xuansto://metrics/summary` Resource<br>4. 新增 `xuansto://degradation/status` Resource |
| **输出** | 所有 Tool 有完整文档；指标和降级状态可查询 |
| **验收标准** | 1. mcp-tools.md 覆盖全部 17+2 个 Tool<br>2. `metrics_report` 可按时间范围查询指标 |
| **依赖** | P0-B |

### 4.4 P2: 架构加固

#### P2-A: 数据层统一 (U-14, U-15, U-16, U-18)

| 项目 | 内容 |
|------|------|
| **输入** | 分散的 JSON/MD/SQLite 存储 |
| **步骤** | 1. 创建统一 `xuansto.db`，合并 knowledge.db + decisions.db<br>2. 将 WorkflowInstance、SessionState、ResourceLoadState、DegradationState、ErrorPattern 迁移到 SQLite<br>3. 保留 Markdown 快照用于人类审阅（双写）<br>4. 指标存储迁移到 SQLite，支持 TTL 自动清理<br>5. 关键缓存持久化到 SQLite |
| **输出** | 统一 SQLite 存储 + Markdown 人类可读快照 |
| **验收标准** | 1. 所有状态实体可通过 SQL 查询<br>2. 指标自动清理超过 30 天的数据<br>3. 进程重启后缓存从 SQLite 恢复 |
| **依赖** | P0-C |

#### P2-B: 配置校验层 (U-17)

| 项目 | 内容 |
|------|------|
| **输入** | YAML 配置无 Schema 校验 |
| **步骤** | 1. 定义 `SkillConfigModel`、`FallbackConfigModel`、`ConstraintsModel` Pydantic 模型<br>2. 在 `_load_yaml_config()` 后执行校验<br>3. 校验失败使用默认值并记录警告<br>4. 新增 `config_manage` Tool（reload/status/validate） |
| **输出** | 配置错误在加载时即被发现 |
| **验收标准** | 1. 错误的 YAML 配置不会导致运行时崩溃<br>2. `config_manage(action="validate")` 可检测配置问题 |
| **依赖** | P1-G |

#### P2-C: Hook系统加固 (U-13, U-20, U-25)

| 项目 | 内容 |
|------|------|
| **输入** | Hook 类型为字符串；拦截失败不阻塞；降级 Hook 覆盖不全 |
| **步骤** | 1. 将 `hook_type` 改为 `HookType` 枚举<br>2. 统一 Hook handler 返回类型协议<br>3. 安全类 Hook（security-block）失败时默认阻塞<br>4. 为每个 Hook 实现独立降级脚本<br>5. 增加 Hook 失败计数和告警阈值 |
| **输出** | Hook 系统类型安全且降级覆盖完整 |
| **验收标准** | 1. `hook_type` 拼写错误在类型检查时发现<br>2. security-block Hook 失败时工具调用被阻止 |
| **依赖** | P0-A |

#### P2-D: 渐进式加载完善 (U-11, U-27, U-28, U-29)

| 项目 | 内容 |
|------|------|
| **输入** | Phase 定义重复；路由静态无协商；DisclosureTransition 未使用；FALLBACK_MAP 静态 |
| **步骤** | 1. 将 SKILL.md Phase 概览表移至 references/，SKILL.md 仅保留引用<br>2. 新增 `server_health(action="capabilities")` 返回当前可用 Tool<br>3. 实现 `resource_load_status(action="disclosure_transition")` 使用 DisclosureTransition<br>4. 监听 fallback_config.yaml 变更，触发 `_resolve_fallback_map()` 重建 |
| **输出** | 渐进式加载具备运行时协商和动态配置能力 |
| **验收标准** | 1. Skill 启动时可动态获取可用 Tool 列表<br>2. Phase 转换时客户端收到 DisclosureTransition 通知<br>3. 修改 fallback_config.yaml 后降级路径自动更新 |
| **依赖** | P1-A, P1-G |

#### P2-E: 通知与错误治理 (U-21, U-30, U-31)

| 项目 | 内容 |
|------|------|
| **输入** | 通知系统空实现；错误码混淆；退避无抖动 |
| **步骤** | 1. 实现 `MCPNotificationCallback`，通过 MCP Notification 推送关键事件<br>2. 统一错误码：移除 `code` 字段，仅保留 `error_code`（标准化）<br>3. 退避计算引入抖动：`delay = base * 2^attempt * (1 + random.uniform(0, 0.5))` |
| **输出** | 关键事件实时通知；错误码语义清晰；恢复退避避免雪崩 |
| **验收标准** | 1. 降级事件、Phase 转换、Token 超限触发 MCP Notification<br>2. 错误响应仅含 `error_code` 字段 |
| **依赖** | P1-A |

#### P2-F: Resource增强 (U-19, U-22, U-23)

| 项目 | 内容 |
|------|------|
| **输入** | Resource/Tool 重叠；配置热重载无入口；Resource 无分页 |
| **步骤** | 1. 明确分工：Resource 只读快照，Tool 交互操作<br>2. 新增 `config_manage` Tool<br>3. 引入 Template Resource：`xuansto://sessions/{id}`、`xuansto://agents/{layer}/{name}` |
| **输出** | Resource 层职责清晰，支持参数化查询 |
| **验收标准** | 1. 文档明确 Resource vs Tool 使用场景<br>2. `xuansto://sessions/{id}` 可查询指定会话 |
| **依赖** | P1-G |

#### P2-G: Agent与工作流治理 (U-12, U-26, U-24)

| 项目 | 内容 |
|------|------|
| **输入** | 路径解析静默降级；Agent 合并策略未执行；Token 估算不精确 |
| **步骤** | 1. 路径解析失败时记录 WARNING 日志并在 health check 中告警<br>2. 在 Orchestrator 中实现 Agent 合并执行逻辑（读取 default.yaml 合并规则）<br>3. 引入可配置分词器（tiktoken 可选），压缩后验证实际 Token 数 |
| **输出** | 路径问题可发现；小项目 Agent 自动精简；Token 估算精确 |
| **验收标准** | 1. 路径解析失败时 `server_health` 返回告警<br>2. 小项目自动从 57 Agent 合并为 20 以内<br>3. 压缩后 Token 数与目标偏差 < 10% |
| **依赖** | P1-A |

### 4.5 P3: 优化收尾

#### P3-A: 文档与版本治理 (U-32, U-33, U-34, U-35, U-36)

| 项目 | 内容 |
|------|------|
| **步骤** | 1. 从 v1 迁移 evals/ 目录到 v2<br>2. 创建 v2 CHANGELOG.md<br>3. 确立 v2 为唯一维护版本，v1 标记 archived<br>4. 将 SKILL.md 详细步骤外移到 references/<br>5. 确定工作流 YAML 为权威源，MD 由 YAML 生成 |
| **验收标准** | v1 目录可安全删除；CHANGELOG 追踪所有变更；SKILL.md < 200 行 |
| **依赖** | P2 全部完成 |

#### P3-B: 数据模型增强 (U-37, U-38, U-39, U-40, U-41)

| 项目 | 内容 |
|------|------|
| **步骤** | 1. ErrorPattern 添加 error_type 分类字段<br>2. WorkflowInstance 添加 workflow_id 关联到 DecisionRecord<br>3. knowledge_entries 添加 deleted_at 软删除字段<br>4. 资源缓存实现 LRU 淘汰（`functools.lru_cache` 或 `cachetools.TTLCache`）<br>5. 快照文件可选加密（AES-256-GCM，密钥从环境变量读取） |
| **验收标准** | 数据模型字段完整；缓存内存占用可控 |
| **依赖** | P2-A |

#### P3-C: 安全与一致性 (U-42)

| 项目 | 内容 |
|------|------|
| **步骤** | 1. 实现基于令牌桶的速率限制<br>2. 模板参数 name 增加白名单正则校验<br>3. 统一所有 Tool 的 action 参数为必填 |
| **验收标准** | 高频调用被限流；模板路径遍历被阻止 |
| **依赖** | P1-A |

---

## 5. 渐进式加载披露实现方案

### 5.1 阶段设计

#### 5.1.1 四阶段加载模型（已有框架，需完善）

| 阶段 | 名称 | Token预算 | 加载资源 | 可用功能 | 不可用功能 |
|------|------|----------|---------|---------|-----------|
| Phase 0 | 骨架 | ≤2K | SKILL.md核心约束、triggers.yaml、routes.yaml(路由)、registry.yaml(索引) | 触发匹配、命令路由、命令列表(无详情) | 命令执行、Agent详情、参考文档、知识检索 |
| Phase 1 | 功能 | ≤5K | +commands/*.md(27命令详情)、workflow-phases.md、quality-gates摘要、核心3 Agent | 命令执行、工作流推进、门禁检查、核心Agent | 知识检索、参考文档、Agent完整注册表 |
| Phase 2 | 增强 | ≤10K | +agent-registry.md(完整)、knowledge检索、mcp-tools.md、工作流YAML | 知识检索、参考文档、Agent完整注册表 | 完整脚本集、模板库、全部Agent定义 |
| Phase 3 | 完整 | ≤20K | +全部Agent定义、templates/、scripts/索引、完整参考文档 | 全部功能 | 无 |

#### 5.1.2 阶段推进触发条件

| 转换 | 触发条件 | 推进方式 | 披露行为 |
|------|---------|---------|---------|
| 0→1 | 用户执行命令 | 自动推进 | 提示"加载命令执行能力" |
| 1→2 | 需要参考文档/知识检索 | 显式调用 `resource_load_status(preload, phase=2)` | 提示"加载知识检索和参考文档" |
| 2→3 | 深度分析/安全扫描 | 显式调用 `resource_load_status(preload, phase=3)` | 提示"加载完整功能" |
| N→N-1 | Token预算超限 | 自动降级 | 披露"功能受限，当前可用范围" |

### 5.2 状态机

```
                    ┌──────────────────────────────────────────┐
                    │                                          │
                    ▼                                          │
  ┌──────────┐  命令执行  ┌──────────┐  需要参考  ┌──────────┐  深度分析  ┌──────────┐
  │ Phase 0  │──────────▶│ Phase 1  │──────────▶│ Phase 2  │──────────▶│ Phase 3  │
  │  骨架    │           │  功能    │           │  增强    │           │  完整    │
  │  ≤2K     │           │  ≤5K     │           │  ≤10K    │           │  ≤20K    │
  └──────────┘           └──────────┘           └──────────┘           └──────────┘
       ▲                       ▲                       ▲                       │
       │         Token超限     │         Token超限     │         Token超限     │
       │  ┌───────────────────┘  ┌────────────────────┘  ┌────────────────────┘
       │  │                      │                       │
       └──┘──────────────────────┘───────────────────────┘
                    自动降级（Token预算回收）
```

**状态机规则：**

| 规则 | 说明 |
|------|------|
| 单向推进 | 正常流程只允许 Phase N → Phase N+1 |
| Token降级 | Token使用率 ≥ 80% 时触发 Phase N → Phase N-1 评估 |
| 降级不可逆 | 当次会话内降级后不自动恢复，需显式 preload |
| 披露触发 | 访问不可用功能时返回 DisclosureTransition 结构 |

### 5.3 DisclosureTransition 结构

```python
class DisclosureTransition:
    current_phase: str          # "skeleton" | "functional" | "enhanced" | "full"
    target_phase: str           # 需要推进到的阶段
    required_resources: list    # 需要加载的资源ID列表
    estimated_tokens: int       # 预估Token增量
    available_alternatives: list # 当前阶段可用的替代方案
    transition_hint: str        # 推进提示文本
```

**使用场景：**

```
用户在 Phase 1 调用 knowledge_search
  → 检测到 knowledge_search 需要 Phase 2
  → 返回 DisclosureTransition:
      current_phase: "functional"
      target_phase: "enhanced"
      required_resources: ["knowledge-general", "agent-registry-full"]
      estimated_tokens: 5000
      available_alternatives: ["使用内置知识（有限）", "跳过知识检索"]
      transition_hint: "知识检索需要增强阶段，调用 resource_load_status(preload, phase=2) 推进"
```

### 5.4 过渡动画（CLI/IDE集成）

#### 5.4.1 阶段转换通知

| 事件 | 通知方式 | 内容 |
|------|---------|------|
| Phase 推进开始 | MCP Notification | `{"type": "phase_transition", "from": 1, "to": 2, "status": "loading"}` |
| Phase 推进完成 | MCP Notification | `{"type": "phase_transition", "from": 1, "to": 2, "status": "complete", "loaded": [...]}` |
| Phase 降级 | MCP Notification | `{"type": "phase_degradation", "from": 2, "to": 1, "reason": "token_budget"}` |
| 功能不可用 | Tool 响应附加 | `DisclosureTransition` 结构嵌入响应 |

#### 5.4.2 进度反馈

```
resource_load_status(action="loading_progress")
  → 返回:
    {
      "current_phase": 1,
      "target_phase": 2,
      "progress": 0.6,
      "loaded_resources": ["agent-registry", "quality-gates"],
      "pending_resources": ["knowledge-general", "mcp-tools"],
      "estimated_time_remaining_ms": 1200
    }
```

### 5.5 性能指标

| 指标 | 目标值 | 测量方式 |
|------|--------|---------|
| Phase 0→1 推进延迟 | ≤500ms | `resource_load_status(preload, phase=1)` 调用耗时 |
| Phase 1→2 推进延迟 | ≤2000ms | 同上 |
| Phase 2→3 推进延迟 | ≤5000ms | 同上 |
| Phase 0 Token占用 | ≤2K | `token_budget(action="report")` 统计 |
| Phase 1 Token占用 | ≤5K | 同上 |
| Phase 2 Token占用 | ≤10K | 同上 |
| Phase 3 Token占用 | ≤20K | 同上 |
| 降级切换延迟 | ≤100ms | 从检测到MCP不可用到降级响应返回 |
| 披露通知延迟 | ≤50ms | DisclosureTransition 构建和返回耗时 |
| 资源缓存命中率 | ≥80% | `resource_load_status(action="cache")` 统计 |

---

## 6. 测试策略

### 6.1 测试分层

```
┌─────────────────────────────────────────┐
│           端到端测试 (E2E)               │  ← 完整工作流验证
├─────────────────────────────────────────┤
│           集成测试 (Integration)         │  ← MCP Tool 交互验证
├─────────────────────────────────────────┤
│           单元测试 (Unit)                │  ← 函数/类级别验证
└─────────────────────────────────────────┘
```

### 6.2 单元测试

| 模块 | 测试文件 | 覆盖目标 | 关键测试用例 |
|------|---------|---------|------------|
| degradation.py | test_degradation.py | ≥90% | 降级链切换、恢复退避、状态持久化、竞态条件 |
| hook_engine.py | test_hook_engine.py | ≥85% | Pre/Post Hook执行、类型枚举、阻塞逻辑、失败处理 |
| search_engine.py | test_search_engine.py | ≥85% | ChromaDB/SQLite/Keyword三级切换、查询结果格式 |
| config.py | test_config.py | ≥80% | 路径解析、热重载、Schema校验、默认值回退 |
| errors.py | test_errors.py | ≥90% | 错误分类、重试策略、统一响应格式 |
| validator.py | test_validator.py | ≥95% | 路径遍历防护、绝对路径拒绝、null字节检测 |
| metrics.py | test_metrics.py | ≥80% | 指标收集、聚合统计、持久化、TTL清理 |
| schemas.py | test_schemas.py | ≥90% | Pydantic校验、extra="forbid"、枚举约束 |

**单元测试框架：** pytest + pytest-asyncio + pytest-cov

**覆盖率目标：** 核心模块 ≥ 85%，总体 ≥ 80%

### 6.3 集成测试

| 测试场景 | 测试文件 | 验证内容 |
|---------|---------|---------|
| MCP Tool 完整调用链 | test_mcp_tool_integration.py | 17个Tool通过MCP协议调用，返回正确结构 |
| 降级链端到端 | test_fallback_integration.py | MCP Server停止后脚本降级→内联降级→最小响应 |
| 渐进式加载推进 | test_progressive_loading.py | Phase 0→1→2→3 推进，Token预算控制 |
| Hook拦截链 | test_hook_integration.py | Pre-Hook阻塞、Post-Hook处理、Hook失败处理 |
| 知识检索降级 | test_knowledge_degradation.py | ChromaDB→SQLite→Keyword三级降级 |
| 会话持久化与恢复 | test_session_integration.py | 会话保存→进程重启→会话恢复 |
| 工作流调度 | test_workflow_integration.py | start→phase推进→abort→recover→snapshots |
| 版本协商 | test_version_negotiation.py | 兼容版本协商、不兼容版本拒绝 |
| 配置热重载 | test_config_reload.py | 修改YAML→自动重载→Tool行为变更 |

**集成测试环境：** 使用 `FastMCP` 的测试工具启动真实 MCP Server 进程

### 6.4 端到端测试

| 测试场景 | 验证内容 | 执行方式 |
|---------|---------|---------|
| 新项目全流程 | /init → /brainstorm → /plan → /implement → /test → /review → /deploy | 手动 + 自动化脚本 |
| 降级模式全流程 | 杀死MCP Server → 脚本降级执行 → 功能验证 | 自动化脚本 |
| Token预算控制 | 大项目Token消耗 → L1/L2/L3降级 → 恢复 | 自动化脚本 |
| 安全审计流程 | /audit → 安全扫描 → 门禁检查 → 修复 → 重新验证 | 手动 |
| 桌面构建流程 | /build-desktop → 构建 → 签名 → 更新检查 | 手动 |

### 6.5 回归验证方案

#### 6.5.1 回归测试矩阵

| 变更类型 | 必须通过的测试 | 验证方法 |
|---------|--------------|---------|
| MCP Tool 变更 | 对应Tool单元测试 + 集成测试 | `pytest tests/test_{tool_name}.py -v` |
| 降级逻辑变更 | 降级链集成测试 + E2E降级测试 | `pytest tests/test_fallback_integration.py -v` |
| 数据模型变更 | Schema校验测试 + 迁移测试 | `pytest tests/test_schemas.py tests/test_migrations.py -v` |
| 配置变更 | 配置校验测试 + 热重载测试 | `pytest tests/test_config.py -v` |
| 渐进式加载变更 | 加载推进测试 + Token预算测试 | `pytest tests/test_progressive_loading.py -v` |

#### 6.5.2 回归保护规则

1. **任何PR必须通过全量单元测试** — `pytest tests/ -x --cov=xuansto_mcp --cov-fail-under=80`
2. **降级相关PR必须通过集成测试** — `pytest tests/test_fallback_integration.py -v`
3. **API变更必须通过版本兼容性测试** — `pytest tests/test_version_negotiation.py -v`
4. **数据迁移必须通过双向验证** — 迁移前数据 → 迁移 → 迁移后数据 → 回滚 → 验证一致性

---

## 7. 持续集成建议

### 7.1 CI流水线设计

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  Lint    │───▶│  Schema  │───▶│  Unit    │───▶│  Integ   │───▶│  Build   │
│  检查    │    │  校验    │    │  测试    │    │  测试    │    │  发布    │
└──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
     │               │               │               │               │
     ▼               ▼               ▼               ▼               ▼
  ruff/mypy      Pydantic        pytest          pytest          uv build
  yaml-lint      YAML校验        单元测试        集成测试        发布检查
  encoding       MCP定义         覆盖率≥80%      降级链验证      版本号校验
```

### 7.2 Lint检查

| 检查项 | 工具 | 配置 | 触发条件 |
|--------|------|------|---------|
| Python代码风格 | ruff | `pyproject.toml [tool.ruff]` | 每次提交 |
| Python类型检查 | mypy | `pyproject.toml [tool.mypy]` | 每次提交 |
| YAML格式 | yamllint | `.yamllint` | 每次提交 |
| 编码检查 | 自定义脚本 | UTF-8无BOM + 无U+FFFD | 每次提交 |
| Markdown格式 | markdownlint | `.markdownlint.json` | 每次提交 |

**执行命令：**
```bash
ruff check src/ tests/
mypy src/xuansto_mcp/
yamllint .trae/skills/xuansto-skill-v2/*.yaml .trae/skills/xuansto-skill-v2/configs/*.yaml
python scripts/check-encoding.py --check
```

### 7.3 Schema校验

| 校验对象 | 校验方式 | 校验内容 |
|---------|---------|---------|
| YAML配置文件 | Pydantic Model | `.skill-config.yaml`、`constraints.yaml`、`fallback_config.yaml` 结构校验 |
| MCP Tool Schema | Pydantic Model | 17个Tool的Input Schema 校验（`extra="forbid"`） |
| MCP Resource URI | 正则匹配 | `xuansto://` 前缀 + 路径安全校验 |
| Agent注册表 | 结构校验 | `registry.yaml` 中57个Agent的层级/Phase/模型路由字段完整性 |
| 命令路由表 | 结构校验 | `routes.yaml` 中27个命令的意图/MCP工具链/降级路径完整性 |

**执行命令：**
```bash
python -m xuansto_mcp.tools.schema_validator --all
python -c "from xuansto_mcp.models.schemas import *; print('Schema validation passed')"
```

### 7.4 MCP定义验证

| 验证项 | 验证方式 | 预期结果 |
|--------|---------|---------|
| Tool注册完整性 | `server_health(check)` | tools_available == 17（重构后为19） |
| Tool参数校验 | 每个Tool传入非法参数 | 返回 `ERR_VALIDATION` |
| Resource可达性 | 读取6个Resource URI | 全部返回有效内容 |
| 降级链可达性 | 停止MCP Server后调用Tool | 降级响应结构正确 |
| 版本协商 | `server_health(negotiate_version)` | 兼容版本正确返回 |
| Hook拦截 | 调用被security-block的Tool | 返回blocked响应 |

**执行命令：**
```bash
pytest tests/test_mcp_definition.py -v
```

### 7.5 构建流水线

```yaml
# .github/workflows/ci.yml 示例
name: Xuansto CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - run: uv sync --dev
      - run: uv run ruff check src/ tests/
      - run: uv run mypy src/xuansto_mcp/

  schema-validation:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - run: uv sync --dev
      - run: uv run python -m xuansto_mcp.tools.schema_validator --all

  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - run: uv sync --dev
      - run: uv run pytest tests/unit/ -x --cov=xuansto_mcp --cov-fail-under=80 -v

  integration-tests:
    runs-on: ubuntu-latest
    needs: [lint, unit-tests]
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - run: uv sync --dev
      - run: uv run pytest tests/integration/ -v --timeout=120

  build:
    runs-on: ubuntu-latest
    needs: [integration-tests]
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - run: uv build
      - run: uv run python -c "import xuansto_mcp; print(xuansto_mcp.__version__)"
```

### 7.6 质量门禁

| 门禁 | 阈值 | 阻断级别 |
|------|------|---------|
| 单元测试覆盖率 | ≥80% | BLOCK |
| Lint错误数 | 0 | BLOCK |
| 类型检查错误数 | 0 | BLOCK |
| Schema校验失败数 | 0 | BLOCK |
| 集成测试通过率 | 100% | BLOCK |
| MCP定义验证 | 全部通过 | BLOCK |
| 降级链可达性 | 17/17 Tool | BLOCK |
| 文档覆盖率 | 100% Tool有文档 | WARN |

---

## 附录A: 问题编号映射表

| 统一编号 | 原始编号 |
|---------|---------|
| U-01 | SKILL-01, MCP-03, ARCH-06-2 |
| U-02 | SKILL-02 |
| U-03 | DB-01, MCP-10, API-10 |
| U-04 | MCP-11, API-04 |
| U-05 | SKILL-03, MCP-08, API-03 |
| U-06 | SKILL-04, MCP-13, API-07 |
| U-07 | SKILL-05, MCP-05 |
| U-08 | DB-02 |
| U-09 | API-05 |
| U-10 | MCP-01 |
| U-11 | ARCH-06-1 |
| U-12 | ARCH-06-3 |
| U-13 | ARCH-06-4 |
| U-14 | DB-03 |
| U-15 | DB-04 |
| U-16 | DB-05 |
| U-17 | DB-06 |
| U-18 | DB-11 |
| U-19 | MCP-02 |
| U-20 | MCP-04 |
| U-21 | MCP-06 |
| U-22 | MCP-07 |
| U-23 | MCP-09 |
| U-24 | MCP-14 |
| U-25 | SKILL-10 |
| U-26 | SKILL-11 |
| U-27 | API-01 |
| U-28 | API-02 |
| U-29 | API-06 |
| U-30 | API-08 |
| U-31 | API-12 |
| U-32 | SKILL-06 |
| U-33 | SKILL-07 |
| U-34 | SKILL-08 |
| U-35 | SKILL-09 |
| U-36 | SKILL-12 |
| U-37 | DB-07 |
| U-38 | DB-08 |
| U-39 | DB-09 |
| U-40 | DB-10 |
| U-41 | DB-12 |
| U-42 | MCP-12, API-09, API-11 |

## 附录B: 里程碑时间线

```
第1周    P0-A 降级机制修复 ─────────┐
         P0-B 参考文档补充 ─────────┤ P0 紧急修复
         P0-C 状态持久化修复 ────────┘
第2周    P1-A Tool注册解耦 ─────────┐
         P1-B 版本协商完善 ─────────┤
         P1-C knowledge接口治理 ────┤ P1 接口治理
         P1-D 降级脚本异步化 ────────┤
第3周    P1-E Tool职责拆分 ─────────┤
         P1-F ChromaDB可选化 ────────┤
         P1-G 工具文档与暴露补全 ────┘
第4周    P2-A 数据层统一 ───────────┐
         P2-B 配置校验层 ───────────┤
         P2-C Hook系统加固 ──────────┤ P2 架构加固
         P2-D 渐进式加载完善 ────────┤
第5周    P2-E 通知与错误治理 ────────┤
         P2-F Resource增强 ──────────┤
         P2-G Agent与工作流治理 ─────┘
第6周+   P3-A 文档与版本治理 ───────┐
         P3-B 数据模型增强 ──────────┤ P3 优化收尾
         P3-C 安全与一致性 ──────────┘
```
