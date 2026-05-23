# Xuansto Skill 整合重构迭代方案

> 版本: 8.0.0 | 日期: 2026-05-23 | 状态: 实施中
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

五份分析文档共发现 63 个问题（ARCH-12 + DB-12 + MCP-15 + SKILL-12 + API-12），经去重合并后为 **42 个独立问题**。v8.0.0 代码审查又发现 **4 个新问题**（U-43~U-46），合计 **46 个独立问题**。合并规则：

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
| U-17 | DB-06 | YAML配置无Schema校验，错误仅运行时暴露 | 数据, 架构 | 中 | ✅ RESOLVED: config_manage Tool + Pydantic校验(SkillConfigModel/FallbackConfigModel/ConstraintsModel) |
| U-18 | DB-11 | 多个SQLite数据库分散，连接管理复杂 | 数据 | 中 | ✅ RESOLVED: 统一xuansto.db(8表) |
| U-19 | MCP-02 | Resource与Tool功能重叠（loading/status） | MCP | 中 | ✅ RESOLVED: 明确分工-Resource只读快照/Tool交互操作 |
| U-20 | MCP-04 | Hook引擎缺少类型安全（字符串代替枚举） | MCP | 中 | ✅ RESOLVED: HookType枚举 |
| U-21 | MCP-06 | 通知系统未与MCP协议集成 | MCP | 中 | ✅ RESOLVED: MCPNotificationCallback |
| U-22 | MCP-07 | 配置热重载缺少MCP入口 | MCP | 中 | ✅ RESOLVED: config_manage Tool |
| U-23 | MCP-09 | Resource缺少分页和过滤能力 | MCP | 中 | ✅ RESOLVED: sessions/{id}+agents/{layer}/{name}参数化Resource |
| U-24 | MCP-14 | context_compress Token估算精度不足 | MCP | 中 | ✅ RESOLVED: tiktoken可选(_HAS_TIKTOKEN)+compression verification(target_deviation字段) |
| U-25 | SKILL-10 | Hook系统与MCP工具集成不完整 | Skill, MCP | 中 | ✅ RESOLVED: HookType枚举+安全阻断+失败计数 |
| U-26 | SKILL-11 | Agent合并策略未在运行时执行 | Skill | 中 | ✅ RESOLVED: agent_status(action="merge")实现+_merge_agents()+YAML规则加载 |
| U-27 | API-01 | 命令路由为静态YAML，缺乏运行时能力协商 | API, Skill | 中 | ✅ RESOLVED: server_health(action="capabilities")返回可用Tool+降级状态+API版本 |
| U-28 | API-02 | DisclosureTransition Schema已定义但未使用 | API, 特效 | 中 | ✅ RESOLVED: DisclosureTransition状态机已实现 |
| U-29 | API-06 | FALLBACK_MAP静态构建，热更新后不刷新 | API, MCP | 中 | ✅ RESOLVED: config_manage reload + fallback_config.yaml热监控(watchfiles/polling) |
| U-30 | API-08 | 错误码code与error_code并存，语义混淆 | API | 中 | ✅ RESOLVED: 统一error_code, deprecated code字段 |
| U-31 | API-12 | 降级恢复退避缺少抖动，可能雪崩 | API, MCP | 中 | ✅ RESOLVED: backoff jitter(random.uniform(0, 0.5)) |
| U-32 | SKILL-06 | v2缺少评估配置文件 | Skill | 低 | ✅ RESOLVED: evals/目录已存在(mcp_evaluation.xml+trigger_eval.json) |
| U-33 | SKILL-07 | v2缺少CHANGELOG.md | Skill | 低 | ✅ RESOLVED: CHANGELOG.md已存在 |
| U-34 | SKILL-08 | v1与v2存在大量重复文件 | Skill, 架构 | 低 | ✅ RESOLVED: v1标记ARCHIVED |
| U-35 | SKILL-09 | v2 SKILL.md行数可能超过500行上限 | Skill | 低 | ✅ RESOLVED: SKILL.md精简至<200行 |
| U-36 | SKILL-12 | 工作流YAML与MD存在同步风险 | Skill | 低 | ✅ RESOLVED: YAML为权威源(_yaml/目录15个YAML文件) |
| U-37 | DB-07 | ErrorPattern缺乏分类体系 | 数据 | 低 | ✅ RESOLVED: error_type字段+database.py |
| U-38 | DB-08 | WorkflowInstance与Decision无显式关联 | 数据 | 低 | ✅ RESOLVED: workflow_id关联字段 |
| U-39 | DB-09 | knowledge_entries无软删除 | 数据 | 低 | ✅ RESOLVED: deleted_at字段+knowledge_inject(delete) |
| U-40 | DB-10 | 资源缓存无LRU淘汰策略 | 数据 | 低 | ✅ RESOLVED: cache.py LRU缓存 |
| U-41 | DB-12 | 快照文件无加密 | 数据 | 低 | ✅ RESOLVED: crypto.py AES-256-GCM |
| U-42 | MCP-12, API-09, API-11 | 缺少速率限制/模板参数白名单/action默认值不一致 | MCP, API | 低 | ✅ RESOLVED: rate_limiter.py令牌桶+名称白名单+action必填 |
| U-43 | 代码审查 | FALLBACK_MAP缺少3个新Tool降级定义(metrics_report/config_manage/agent_manage) | MCP, 降级 | 中 | ✅ RESOLVED: degradation.py补全3个fallback函数+映射 |
| U-44 | SKILL-15 | mcp_evaluation.xml引用不存在的Tool(knowledge_auto_retrieve/knowledge_progressive_search/knowledge_deep_load/knowledge_stats) | Skill, 评估 | 中 | ✅ RESOLVED: mcp_evaluation.xml重写为knowledge_search/metrics_report |
| U-45 | SKILL-14 | SKILL.md未使用Phase标记实现渐进式加载提示 | Skill, 特效 | 低 | 🔲 待实施 (Trae平台侧未实现Phase裁剪，标记暂无实际效果) |
| U-46 | 代码审查 | DegradationManager健康检查间隔硬编码30s，不可配置 | MCP, 架构 | 低 | ✅ RESOLVED: config_models.py DegradationConfigModel.health_check_interval可配置 |

### 1.3 按影响域统计

| 影响域 | 问题数 | 紧急 | 高 | 中 | 低 |
|--------|--------|------|---|---|---|
| Skill | 10 | 2 | 2 | 2 | 4 |
| MCP | 15 | 2 | 3 | 7 | 3 |
| 数据 | 11 | 1 | 1 | 4 | 5 |
| API | 10 | 1 | 2 | 5 | 2 |
| 架构 | 5 | 1 | 0 | 3 | 1 |
| 特效 | 1 | 0 | 0 | 1 | 0 |
| 降级 | 1 | 0 | 0 | 1 | 0 |
| 评估 | 1 | 0 | 0 | 1 | 0 |

### 1.4 解决进度

```
已解决 (42/46)  ██████████████████████████████████████████████████████████████████████████████░░  91.3%
待实施 (4/46)   ████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  8.7%
```

---

## 2. 影响链分析

### 2.1 核心影响链：降级机制断裂（已修复）

```
U-01 降级机制不完整 ✅
  ├── 影响: degradation.py → scripts/ 调用链断裂
  ├── 连锁: U-09 (同步阻塞) → 事件循环卡死 ✅
  ├── 连锁: U-29 (FALLBACK_MAP静态) → 热更新失效 ✅
  ├── 连锁: U-25 (Hook降级不完整) → 安全检查被跳过 ✅
  └── 连锁: U-08 (ChromaDB降级) → 知识检索完全失效 ✅
      └── 连锁: U-14 (会话状态分散) → 降级后无法恢复上下文 ✅

遗留: U-43 FALLBACK_MAP缺少新Tool降级 → 新增3个Tool无降级路径
```

### 2.2 核心影响链：状态持久化不可靠（已修复）

```
U-03 状态持久化无原子保障 ✅
  ├── 影响: resource_state.json / degradation_state.json / workflow实例
  ├── 连锁: U-16 (内存缓存无持久化) → 进程重启后全部丢失 ✅
  ├── 连锁: U-18 (SQLite分散) → 跨库事务无法保证 ✅
  ├── 连锁: U-15 (指标文件膨胀) → 磁盘空间耗尽 ✅
  └── 连锁: U-31 (退避无抖动) → 多组件同时恢复雪崩 ✅
```

### 2.3 核心影响链：Tool接口设计缺陷（已修复）

```
U-04 Tool注册依赖内部API ✅
  ├── 影响: server.py → mcp._tool_manager._tools
  ├── 连锁: U-10 (Tool职责过载) → 参数校验复杂 ✅
  ├── 连锁: U-06 (knowledge职责模糊) → 调用者困惑 ✅
  ├── 连锁: U-19 (Resource/Tool重叠) → loading/status歧义 ✅
  └── 连锁: U-30 (错误码混淆) → 错误处理不一致 ✅
```

### 2.4 核心影响链：版本与文档不一致（已修复）

```
U-05 版本协商不完整 ✅
  ├── 影响: Skill v8.0.0 vs MCP Server v3.5.0
  ├── 连锁: U-07 (工具文档缺失) → 用户无法使用完整功能 ✅
  ├── 连锁: U-02 (参考文档不足) → Agent执行缺乏指引 ✅
  └── 连锁: U-27 (静态路由无协商) → 降级时命令路由失效 ✅

遗留: U-44 评估配置引用不存在的Tool → 评估无法执行
```

### 2.5 新增影响链：降级覆盖不完整

```
U-43 FALLBACK_MAP缺少新Tool降级
  ├── 根因: U-10拆分后新增agent_manage，U-07补全后新增metrics_report/config_manage
  ├── 影响: MCP不可用时3个新Tool直接失败，无降级响应
  ├── 连锁: metrics_report降级缺失 → 运维无法获取指标
  ├── 连锁: config_manage降级缺失 → 配置变更无法执行
  └── 连锁: agent_manage降级缺失 → Agent实例管理不可用

涉及文件:
  xuansto-mcp-server/src/xuansto_mcp/core/degradation.py (FALLBACK_MAP)
  xuansto-mcp-server/src/xuansto_mcp/tools/metrics_report.py
  xuansto-mcp-server/src/xuansto_mcp/tools/config_manage.py
  xuansto-mcp-server/src/xuansto_mcp/tools/agent_manage.py
```

### 2.6 模块依赖热力图

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
  evals/          │ ■■□□□□□ │    │              │   │          │
                  └─────────┘    └──────────────┘   └──────────┘

  ■ = 影响深度 (1-7级)   □ = 无直接影响
  高影响模块: server.py, degradation.py, search_engine.py
  新增关注: evals/ (U-44), FALLBACK_MAP (U-43)
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
| U-43 | FALLBACK_MAP缺少新Tool降级 | 中 | 新增3个Tool无降级路径 | 1层 | 低 |
| U-44 | 评估配置引用不存在的Tool | 中 | 评估无法执行 | 1层 | 中 |
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
| U-45 | SKILL.md未使用Phase标记 | 低 | 渐进式加载Skill侧未实现 | 0层 | 低 |
| U-46 | 健康检查间隔硬编码 | 低 | 不同环境无法调整频率 | 0层 | 低 |

### 3.3 优先级分布

```
紧急 (3)  ████████  6.5%   ← 全部已解决 ✅
高   (7)  ██████████████████  15.2%  ← 全部已解决 ✅
中   (23) ████████████████████████████████████████████████████████  50.0%  ← 21已解决, 2待实施
低   (13) ████████████████████████████  28.3%  ← 11已解决, 2待实施
```

---

## 4. 模块化重构步骤

### 4.1 阶段总览

| 阶段 | 名称 | 周期 | 解决问题 | 状态 |
|------|------|------|---------|------|
| P0 | 紧急修复 | 第1周 | U-01, U-02, U-03 | ✅ 已完成 |
| P1 | 接口治理 | 第2-3周 | U-04, U-05, U-06, U-07, U-08, U-09, U-10 | ✅ 已完成 |
| P2 | 架构加固 | 第4-5周 | U-11~U-31 | ✅ 已完成 |
| P3 | 优化收尾 | 第6周+ | U-32~U-42 | ✅ 已完成 |
| P4 | v8.0.0收尾 | 第7周 | U-43, U-44, U-45, U-46 | 🔲 进行中 |

### 4.2 P0: 紧急修复 ✅ 已完成

#### P0-A: 降级机制修复 (U-01) ✅

| 项目 | 内容 |
|------|------|
| **实施结果** | subprocess_utils异步降级链完整实现：MCP调用 → 脚本降级 → 内联降级 → 最小响应 |
| **验收** | 17个Tool全部有降级路径；降级响应含source:"fallback"标识；脚本超时60s后回退内联降级 |

#### P0-B: 参考文档补充 (U-02) ✅

| 项目 | 内容 |
|------|------|
| **实施结果** | v2 references/从6个文件扩展到75+参考文件，覆盖编码规范、安全指南、桌面开发、Hook系统等 |
| **验收** | 每个Phase的Agent可获取对应参考文档；mcp-tools.md覆盖全部20个Tool |

#### P0-C: 状态持久化修复 (U-03) ✅

| 项目 | 内容 |
|------|------|
| **实施结果** | xuansto.db统一存储(8表)；atexit注册_persist_state()；hash完整性校验；写入锁+backoff jitter |
| **验收** | 进程崩溃后重启状态可恢复；并发读写无数据损坏；多组件恢复不雪崩 |

### 4.3 P1: 接口治理 ✅ 已完成

#### P1-A: Tool注册解耦 (U-04) ✅

| 项目 | 内容 |
|------|------|
| **实施结果** | 本地_TOOL_REGISTRY注册表；Hook拦截从映射表获取Tool函数；_tool_manager._tools零引用 |

#### P1-B: 版本协商完善 (U-05) ✅

| 项目 | 内容 |
|------|------|
| **实施结果** | MCP Server升级到v8.0.0；negotiate_version响应含deprecated_features/new_features；semver比较逻辑 |

#### P1-C: knowledge接口治理 (U-06) ✅

| 项目 | 内容 |
|------|------|
| **实施结果** | knowledge_search Schema仅保留action="retrieve"；写入操作统一通过knowledge_inject |

#### P1-D: 降级脚本异步化 (U-09) ✅

| 项目 | 内容 |
|------|------|
| **实施结果** | run_script_fallback_async使用asyncio.create_subprocess_exec；wait_for超时控制；保留同步版本 |

#### P1-E: Tool职责拆分 (U-10) ✅

| 项目 | 内容 |
|------|------|
| **实施结果** | agent_status保留查询类(list/by_phase/detail/match/merge)；agent_manage负责变更类(create/assign/release/instance_status/destroy/schedule) |

#### P1-F: ChromaDB可选化 (U-08) ✅

| 项目 | 内容 |
|------|------|
| **实施结果** | ChromaDB从必需降级为可选增强；默认SQLite FTS5+BM25；HybridSearchEngine三级降级 |

#### P1-G: 工具文档与暴露补全 (U-07) ✅

| 项目 | 内容 |
|------|------|
| **实施结果** | 新增metrics_report+config_manage Tool；mcp-tools.md覆盖全部20个Tool |

### 4.4 P2: 架构加固 ✅ 已完成

#### P2-A: 数据层统一 (U-14, U-15, U-16, U-18) ✅

| 项目 | 内容 |
|------|------|
| **实施结果** | 统一xuansto.db(8表+11索引)；Markdown双写人类可读；指标TTL自动清理；缓存SQLite持久化 |

#### P2-B: 配置校验层 (U-17) ✅

| 项目 | 内容 |
|------|------|
| **实施结果** | SkillConfigModel/FallbackConfigModel/ConstraintsModel Pydantic模型；config_manage(action="validate")可检测配置问题；校验失败使用默认值+警告 |

#### P2-C: Hook系统加固 (U-13, U-20, U-25) ✅

| 项目 | 内容 |
|------|------|
| **实施结果** | HookType枚举(8种类型)；HookHandler/AsyncHookHandler Protocol；安全Hook失败默认阻塞；_HOOK_FAILURE_THRESHOLD=5告警 |

#### P2-D: 渐进式加载完善 (U-11, U-27, U-28, U-29) ✅

| 项目 | 内容 |
|------|------|
| **实施结果** | SKILL.md精简至<200行；server_health(action="capabilities")运行时协商；DisclosureTransition状态机；fallback_config.yaml热监控(watchfiles/polling) |

#### P2-E: 通知与错误治理 (U-21, U-30, U-31) ✅

| 项目 | 内容 |
|------|------|
| **实施结果** | MCPNotificationCallback推送关键事件；统一error_code；backoff jitter(random.uniform(0, 0.5)) |

#### P2-F: Resource增强 (U-19, U-22, U-23) ✅

| 项目 | 内容 |
|------|------|
| **实施结果** | Resource只读快照/Tool交互操作分工明确；config_manage Tool；参数化Resource URI |

#### P2-G: Agent与工作流治理 (U-12, U-26, U-24) ✅

| 项目 | 内容 |
|------|------|
| **实施结果** | 路径解析失败WARNING日志+health check告警；agent_status(action="merge")运行时合并；tiktoken可选+target_deviation验证 |

### 4.5 P3: 优化收尾 ✅ 已完成

#### P3-A: 文档与版本治理 (U-32, U-33, U-34, U-35, U-36) ✅

| 项目 | 内容 |
|------|------|
| **实施结果** | evals/目录(mcp_evaluation.xml+trigger_eval.json)；CHANGELOG.md；v1标记ARCHIVED；SKILL.md<200行；YAML为权威源(_yaml/目录15个文件) |

#### P3-B: 数据模型增强 (U-37, U-38, U-39, U-40, U-41) ✅

| 项目 | 内容 |
|------|------|
| **实施结果** | error_type分类字段；workflow_id关联；deleted_at软删除；LRU缓存；AES-256-GCM加密 |

#### P3-C: 安全与一致性 (U-42) ✅

| 项目 | 内容 |
|------|------|
| **实施结果** | 令牌桶速率限制；name白名单正则校验；action参数必填 |

### 4.6 P4: v8.0.0收尾 🔲 进行中

#### P4-A: FALLBACK_MAP补全 (U-43)

| 项目 | 内容 |
|------|------|
| **输入** | FALLBACK_MAP当前17个条目，缺少metrics_report/config_manage/agent_manage的降级函数 |
| **步骤** | 1. 在degradation.py中新增`metrics_report_fallback`：从xuansto.db读取最近指标<br>2. 新增`config_manage_fallback`：返回当前配置快照(只读)<br>3. 新增`agent_manage_fallback`：从静态registry读取Agent信息<br>4. 将3个fallback函数加入FALLBACK_MAP和_INLINE_FALLBACK_MAP<br>5. 更新fallback_config.yaml添加新条目 |
| **输出** | 全部20个Tool均有降级路径 |
| **验收标准** | 1. `server_health(check)` 返回tools_count=20<br>2. MCP不可用时20/20 Tool返回降级响应<br>3. 降级链测试通过 |
| **依赖** | 无 |
| **修复复杂度** | 低 |

#### P4-B: 评估配置修正 (U-44)

| 项目 | 内容 |
|------|------|
| **输入** | mcp_evaluation.xml引用4个不存在的Tool：knowledge_auto_retrieve、knowledge_progressive_search、knowledge_deep_load、knowledge_stats |
| **步骤** | 1. 将knowledge_auto_retrieve替换为knowledge_search(action="retrieve")+knowledge_inject(action="list_available")组合<br>2. 将knowledge_progressive_search替换为knowledge_search(action="retrieve", search_type="hybrid")<br>3. 将knowledge_deep_load替换为knowledge_search(action="retrieve", query=entry_id)<br>4. 将knowledge_stats替换为knowledge_inject(action="list_available")<br>5. 更新verification断言以匹配新响应结构<br>6. 确保所有10个qa_pair的tool_calls指向实际存在的Tool |
| **输出** | mcp_evaluation.xml全部Tool调用可执行 |
| **验收标准** | 1. 每个qa_pair引用的Tool名称在schemas.py中有对应Input定义<br>2. 参数结构与Schema一致<br>3. trigger_eval.json无需修改(仅测试触发准确率) |
| **依赖** | 无 |
| **修复复杂度** | 中 |

#### P4-C: SKILL.md Phase标记 (U-45)

| 项目 | 内容 |
|------|------|
| **输入** | SKILL.md未使用Phase标记，渐进式加载状态机仅在MCP Server侧实现 |
| **步骤** | 1. 在SKILL.md的triggers段添加phase标注：`phase: 0`（骨架阶段加载）<br>2. 在commands/段标注各命令所需最低Phase<br>3. 在references/段标注各参考文档的Phase归属<br>4. 添加Phase推进提示文本模板 |
| **输出** | SKILL.md具备Phase感知能力 |
| **验收标准** | 1. SKILL.md行数仍<200行<br>2. Phase标记与resource_load_status的4阶段模型一致 |
| **依赖** | 无 |
| **修复复杂度** | 低 |

#### P4-D: 健康检查间隔可配置 (U-46)

| 项目 | 内容 |
|------|------|
| **输入** | DegradationManager._DEFAULT_HEALTH_INTERVAL硬编码为30.0s |
| **步骤** | 1. 在.xuansto-config.yaml添加health_check_interval_sec字段<br>2. 在SkillConfigModel添加health_check_interval_sec: int = Field(default=30, ge=5, le=300)<br>3. DegradationManager.__init__从配置读取间隔值<br>4. config_manage(action="status")显示当前间隔 |
| **输出** | 健康检查间隔可通过YAML配置调整 |
| **验收标准** | 1. 修改.xuansto-config.yaml后config_manage(reload)生效<br>2. 间隔范围5s~300s<br>3. 默认值仍为30s |
| **依赖** | P2-B (config_manage已实现) |
| **修复复杂度** | 低 |

---

## 5. 渐进式加载披露实现方案

### 5.1 阶段设计

#### 5.1.1 四阶段加载模型

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
class DisclosureTransition(BaseModel):
    current_phase: str          # "skeleton" | "functional" | "enhanced" | "full"
    target_phase: str           # 需要推进到的阶段
    required_resources: list    # 需要加载的资源ID列表
    estimated_tokens: int       # 预估Token增量
    available_alternatives: list # 当前阶段可用的替代方案
    transition_hint: str        # 推进提示文本
    status: Literal["pending", "in_progress", "completed", "failed"]
    from_phase: str             # 源阶段名称
    to_phase: str               # 目标阶段名称
    started_at: str | None      # 转换开始时间(ISO8601)
    completed_at: str | None    # 转换完成时间(ISO8601)
    resources_affected: list    # 受影响的资源ID列表
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
      status: "pending"
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

### 5.6 v8.0.0遗留：Skill侧Phase标记

当前渐进式加载状态机仅在MCP Server侧实现（resource_load_status Tool + DisclosureTransition Schema）。Skill侧（SKILL.md）尚未使用Phase标记，导致：

- Skill无法在加载时告知平台自身属于哪个Phase
- 平台无法根据Skill的Phase声明决定加载策略
- Phase推进依赖MCP Tool调用而非Skill元数据

**P4-C (U-45)** 将解决此问题，在SKILL.md中添加Phase元数据标记。

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
| degradation.py | test_degradation.py | ≥90% | 降级链切换、恢复退避(含jitter)、状态持久化、竞态条件、FALLBACK_MAP完整性 |
| hook_engine.py | test_hook_engine.py | ≥85% | Pre/Post Hook执行、HookType枚举、阻塞逻辑、失败处理、失败计数阈值 |
| search_engine.py | test_search_engine.py | ≥85% | ChromaDB/SQLite/Keyword三级切换、查询结果格式 |
| config.py | test_config.py | ≥80% | 路径解析、热重载、Schema校验、默认值回退 |
| errors.py | test_errors.py | ≥90% | 错误分类、重试策略、统一响应格式(error_code) |
| validator.py | test_validator.py | ≥95% | 路径遍历防护、绝对路径拒绝、null字节检测 |
| metrics.py | test_metrics.py | ≥80% | 指标收集、聚合统计、持久化、TTL清理 |
| schemas.py | test_schemas.py | ≥90% | Pydantic校验、extra="forbid"、枚举约束 |
| database.py | test_database.py | ≥85% | 8表CRUD、索引查询、JSON字段序列化、TTL清理 |
| config_models.py | test_config_models.py | ≥90% | SkillConfigModel/FallbackConfigModel/ConstraintsModel校验 |

**单元测试框架：** pytest + pytest-asyncio + pytest-cov

**覆盖率目标：** 核心模块 ≥ 85%，总体 ≥ 80%

### 6.3 集成测试

| 测试场景 | 测试文件 | 验证内容 |
|---------|---------|---------|
| MCP Tool 完整调用链 | test_mcp_tool_integration.py | 20个Tool通过MCP协议调用，返回正确结构 |
| 降级链端到端 | test_fallback_integration.py | MCP Server停止后脚本降级→内联降级→最小响应(含3个新Tool) |
| 渐进式加载推进 | test_progressive_loading.py | Phase 0→1→2→3 推进，Token预算控制 |
| Hook拦截链 | test_hook_integration.py | Pre-Hook阻塞、Post-Hook处理、Hook失败处理、失败计数 |
| 知识检索降级 | test_knowledge_degradation.py | ChromaDB→SQLite→Keyword三级降级 |
| 会话持久化与恢复 | test_session_integration.py | 会话保存→进程重启→会话恢复 |
| 工作流调度 | test_workflow_integration.py | start→phase推进→abort→recover→snapshots |
| 版本协商 | test_version_negotiation.py | 兼容版本协商、不兼容版本拒绝、deprecated_features |
| 配置热重载 | test_config_reload.py | 修改YAML→自动重载→Tool行为变更 |
| Agent合并 | test_agent_merge.py | merge action→57→~20 Agent、YAML规则加载、builtin回退 |

**集成测试环境：** 使用 `FastMCP` 的测试工具启动真实 MCP Server 进程

### 6.4 端到端测试

| 测试场景 | 验证内容 | 执行方式 |
|---------|---------|---------|
| 新项目全流程 | /init → /brainstorm → /plan → /implement → /test → /review → /deploy | 手动 + 自动化脚本 |
| 降级模式全流程 | 杀死MCP Server → 脚本降级执行 → 功能验证(20/20 Tool) | 自动化脚本 |
| Token预算控制 | 大项目Token消耗 → L1/L2/L3降级 → 恢复 | 自动化脚本 |
| 安全审计流程 | /audit → 安全扫描 → 门禁检查 → 修复 → 重新验证 | 手动 |
| 桌面构建流程 | /build-desktop → 构建 → 签名 → 更新检查 | 手动 |
| 评估配置验证 | mcp_evaluation.xml中10个qa_pair全部可执行 | 自动化脚本 |

### 6.5 回归验证方案

#### 6.5.1 回归测试矩阵

| 变更类型 | 必须通过的测试 | 验证方法 |
|---------|--------------|---------|
| MCP Tool 变更 | 对应Tool单元测试 + 集成测试 | `pytest tests/test_{tool_name}.py -v` |
| 降级逻辑变更 | 降级链集成测试 + E2E降级测试 | `pytest tests/test_fallback_integration.py -v` |
| 数据模型变更 | Schema校验测试 + 迁移测试 | `pytest tests/test_schemas.py tests/test_migrations.py -v` |
| 配置变更 | 配置校验测试 + 热重载测试 | `pytest tests/test_config.py -v` |
| 渐进式加载变更 | 加载推进测试 + Token预算测试 | `pytest tests/test_progressive_loading.py -v` |
| FALLBACK_MAP变更 | 降级链集成测试 + Tool数量验证 | `pytest tests/test_fallback_integration.py -v` |

#### 6.5.2 回归保护规则

1. **任何PR必须通过全量单元测试** — `pytest tests/ -x --cov=xuansto_mcp --cov-fail-under=80`
2. **降级相关PR必须通过集成测试** — `pytest tests/test_fallback_integration.py -v`
3. **API变更必须通过版本兼容性测试** — `pytest tests/test_version_negotiation.py -v`
4. **数据迁移必须通过双向验证** — 迁移前数据 → 迁移 → 迁移后数据 → 回滚 → 验证一致性
5. **FALLBACK_MAP变更必须验证Tool数量** — `server_health(check)` 返回 tools_count == 20

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
  markdownlint   评估配置        FALLBACK_MAP    20/20 Tool
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
| YAML配置文件 | Pydantic Model | `.xuansto-config.yaml`、`constraints.yaml`、`fallback_config.yaml` 结构校验 |
| MCP Tool Schema | Pydantic Model | 20个Tool的Input Schema 校验（`extra="forbid"`） |
| MCP Resource URI | 正则匹配 | `xuansto://` 前缀 + 路径安全校验 |
| Agent注册表 | 结构校验 | `registry.yaml` 中57个Agent的层级/Phase/模型路由字段完整性 |
| 命令路由表 | 结构校验 | `routes.yaml` 中27个命令的意图/MCP工具链/降级路径完整性 |
| 评估配置 | 结构校验 | `mcp_evaluation.xml` 中引用的Tool名称必须存在于schemas.py |

**执行命令：**
```bash
python -m xuansto_mcp.tools.schema_validator --all
python -c "from xuansto_mcp.models.schemas import *; print('Schema validation passed')"
```

### 7.4 MCP定义验证

| 验证项 | 验证方式 | 预期结果 |
|--------|---------|---------|
| Tool注册完整性 | `server_health(check)` | tools_available == 20 |
| Tool参数校验 | 每个Tool传入非法参数 | 返回 `ERR_VALIDATION` |
| Resource可达性 | 读取6个Resource URI | 全部返回有效内容 |
| 降级链可达性 | 停止MCP Server后调用Tool | 20/20 Tool降级响应结构正确 |
| 版本协商 | `server_health(negotiate_version)` | 兼容版本正确返回 |
| Hook拦截 | 调用被security-block的Tool | 返回blocked响应 |
| 能力协商 | `server_health(capabilities)` | 返回20个Tool+降级状态 |

**执行命令：**
```bash
pytest tests/test_mcp_definition.py -v
```

### 7.5 构建流水线

```yaml
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
| 降级链可达性 | 20/20 Tool | BLOCK |
| FALLBACK_MAP完整性 | 20/20 条目 | BLOCK |
| 评估配置Tool引用 | 全部存在 | WARN |
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
| U-43 | 代码审查 (v8.0.0新增) |
| U-44 | SKILL-15 (v8.0.0新增) |
| U-45 | SKILL-14 (v8.0.0新增) |
| U-46 | 代码审查 (v8.0.0新增) |

## 附录B: 里程碑时间线

```
第1周    P0-A 降级机制修复 ─────────┐
         P0-B 参考文档补充 ─────────┤ P0 紧急修复 ✅
         P0-C 状态持久化修复 ────────┘
第2周    P1-A Tool注册解耦 ─────────┐
         P1-B 版本协商完善 ─────────┤
         P1-C knowledge接口治理 ────┤ P1 接口治理 ✅
         P1-D 降级脚本异步化 ────────┤
第3周    P1-E Tool职责拆分 ─────────┤
         P1-F ChromaDB可选化 ────────┤
         P1-G 工具文档与暴露补全 ────┘
第4周    P2-A 数据层统一 ───────────┐
         P2-B 配置校验层 ───────────┤
         P2-C Hook系统加固 ──────────┤ P2 架构加固 ✅
         P2-D 渐进式加载完善 ────────┤
第5周    P2-E 通知与错误治理 ────────┤
         P2-F Resource增强 ──────────┤
         P2-G Agent与工作流治理 ─────┘
第6周+   P3-A 文档与版本治理 ───────┐
         P3-B 数据模型增强 ──────────┤ P3 优化收尾 ✅
         P3-C 安全与一致性 ──────────┘
第7周    P4-A FALLBACK_MAP补全 ─────┐
         P4-B 评估配置修正 ──────────┤ P4 v8.0.0收尾 🔲
         P4-C SKILL.md Phase标记 ────┤
         P4-D 健康检查间隔可配置 ────┘
```

## 附录C: v8.0.0变更验证清单

### C.1 原42项验证结果

| 验证项 | 验证方式 | 结果 |
|--------|---------|------|
| U-17 YAML Schema校验 | 读取config_manage.py + config_models.py | ✅ SkillConfigModel/FallbackConfigModel/ConstraintsModel + validate action |
| U-24 Token估算精度 | 读取context_compress.py | ✅ tiktoken可选(_HAS_TIKTOKEN) + target_deviation字段 + token_method字段 |
| U-26 Agent合并执行 | 读取agent_status.py | ✅ action="merge" + _merge_agents() + YAML规则加载 + builtin回退 |
| U-27 运行时能力协商 | 读取server_health.py | ✅ action="capabilities" + Tool列表+降级状态+API版本 |
| U-32 评估配置文件 | 检查evals/目录 | ✅ mcp_evaluation.xml + trigger_eval.json |
| U-33 CHANGELOG.md | 检查文件存在 | ✅ CHANGELOG.md已存在 |
| U-36 YAML权威源 | 检查workflows/_yaml/ | ✅ 15个YAML文件 |

### C.2 新增4项详情

| 编号 | 问题 | 根因 | 影响 |
|------|------|------|------|
| U-43 | FALLBACK_MAP缺3个新Tool | P1-E拆分+P1-G补全后未同步FALLBACK_MAP | MCP不可用时3个Tool直接失败 |
| U-44 | 评估配置引用不存在Tool | mcp_evaluation.xml基于旧API编写，未随U-06治理更新 | 10个qa_pair中6个引用不存在的Tool |
| U-45 | SKILL.md无Phase标记 | 渐进式加载仅在MCP Server侧实现 | Skill无法告知平台自身Phase归属 |
| U-46 | 健康检查间隔硬编码 | _DEFAULT_HEALTH_INTERVAL=30.0为字面量 | 不同部署环境无法调整检查频率 |
