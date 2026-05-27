# 三层知识库架构详细定义

> 版本: 1.9.0 | 更新日期: 2026-05-02 | 编码: UTF-8 | 行尾: LF

## 目录

1. [架构概述](#1-架构概述)
2. [通用知识库（General KB）](#2-通用知识库general-kb)
3. [工作知识库（Working KB）](#3-工作知识库working-kb)
4. [经验知识库（Experience KB）](#4-经验知识库experience-kb)
5. [存储格式规范](#5-存储格式规范)
6. [索引机制](#6-索引机制)
7. [并发写入冲突处理机制](#7-并发写入冲突处理机制)
8. [灾难恢复策略](#8-灾难恢复策略)
9. [检索策略](#9-检索策略)
10. [Agent知识检索机制与注入流程](#10-agent知识检索机制与注入流程)
11. [知识自动沉淀](#11-知识自动沉淀)
12. [版本管理与增量更新](#12-版本管理与增量更新)
13. [主动学习机制](#13-主动学习机制)
14. [知识生命周期管理](#14-知识生命周期管理)
15. [跨项目知识泛化](#15-跨项目知识泛化)
16. [目录结构](#16-目录结构)
17. [知识库数据库服务层架构](#17-知识库数据库服务层架构)
18. [SQLite结构化存储设计](#18-sqlite结构化存储设计)
19. [混合检索引擎](#19-混合检索引擎)
20. [REST API接口契约](#20-rest-api接口契约)
21. [MCP Tool接口契约](#21-mcp-tool接口契约)
22. [知识去重与智能更新](#22-知识去重与智能更新)
23. [服务管理要点](#23-服务管理要点)

---

## 1. 架构概述

### 1.1 三层架构图

```
┌─────────────────────────────────────────────────────────┐
│                   经验知识库 (Experience KB)              │
│   实时沉淀 · 错误方案 · 成功模式 · 优化记录 · 裁决日志    │
│   存储: ~/.xuansto/knowledge/experience/                 │
│   更新: 实时自动  |  共享: 可配置全局/项目隔离             │
├─────────────────────────────────────────────────────────┤
│                   工作知识库 (Working KB)                 │
│   项目架构 · 业务领域 · API规范 · 环境配置 · 团队约定     │
│   存储: .knowledge/workspace/                            │
│   更新: 项目生命周期同步  |  共享: 项目内共享              │
├─────────────────────────────────────────────────────────┤
│                   通用知识库 (General KB)                 │
│   编程范式 · 开发规范 · 设计模式 · 安全规范 · DevOps      │
│   存储: ~/.xuansto/knowledge/general/                    │
│   更新: 季度/年度  |  共享: 全局共享，多项目复用           │
└─────────────────────────────────────────────────────────┘
         ▲ 知识流向：自底向上支撑，自顶向下沉淀
```

### 1.2 设计目标

| 目标 | 说明 |
|------|------|
| **知识复用** | 通用知识跨项目共享，避免重复建设；经验知识从具体项目提炼后可泛化复用 |
| **上下文增强** | 工作知识库为当前项目提供精准上下文，减少Agent理解偏差 |
| **自主进化** | 经验知识库实时自动沉淀，知识置信度动态调整，形成自演化闭环 |
| **版本可控** | 知识库与代码库同步版本管理，支持分支探索、回滚和增量更新 |
| **跨平台知识** | 支持Web端与桌面端（Electron/Tauri）开发知识的统一管理与差异化检索 |

### 1.3 层级关系

- **通用知识库**是最底层的基础设施，提供跨项目、跨技术栈的通用知识支撑
- **工作知识库**是中间层，绑定具体项目，提供项目级上下文
- **经验知识库**是最上层的动态层，从实践中实时沉淀，可向下反哺通用知识库
- 知识流动方向：通用→工作（提供基础支撑），经验→通用（提炼泛化），经验→工作（直接应用）

---

## 2. 通用知识库（General KB）

### 2.1 基本属性

| 属性 | 值 |
|------|-----|
| 存储位置 | `~/.xuansto/knowledge/general/`（全局）或 `.knowledge/general/`（项目级覆盖） |
| 更新频率 | 低（季度/年度），由Specification Keeper审核后批量更新 |
| 共享范围 | 全局共享，多项目复用 |
| 生命周期 | 长期稳定，版本化演进 |
| 权威性 | 高，经过充分验证的通用知识 |

### 2.2 内容分类

| 分类 | 说明 | 示例 |
|------|------|------|
| 编程范式 | 函数式/面向对象/响应式等编程范式核心概念 | 纯函数原则、不可变数据模式、Monad模式 |
| 开发规范 | 通用编码规范与最佳实践 | Clean Code原则、SOLID原则、DRY原则 |
| 设计模式 | 经典与新兴设计模式 | 工厂模式、观察者模式、策略模式、CQRS |
| 安全规范 | 通用安全编码与防护规范 | OWASP Top 10、输入验证、认证授权 |
| 测试规范 | 通用测试策略与方法论 | TDD流程、测试金字塔、Mock策略 |
| DevOps规范 | CI/CD、容器化、监控等规范 | Git Flow、Docker最佳实践、蓝绿部署 |
| 桌面开发规范 | 跨平台桌面应用通用规范 | 进程模型、窗口管理、原生API调用模式 |

### 2.3 知识条目格式

```yaml
---
id: "gkb-design-pattern-observer-001"
type: "design_pattern"
category: "设计模式"
tags: ["观察者模式", "发布订阅", "事件驱动", "行为型模式"]
version: "1.2.0"
created: "2025-01-15T10:00:00Z"
updated: "2026-03-20T14:30:00Z"
source: "GoF Design Patterns / 社区实践总结"
confidence: 0.95
last_validated: "2026-03-20T14:30:00Z"
success_count: 42
failure_count: 1
---

# 观察者模式 (Observer Pattern)

## 定义
定义对象间一对多的依赖关系，当一个对象状态改变时，所有依赖它的对象
都会收到通知并自动更新。

## 适用场景
- 事件系统实现
- 消息总线
- 数据绑定
- 状态变更通知

## 代码示例
（语言无关的伪代码或特定语言实现）

## 注意事项
- 注意内存泄漏（未取消订阅）
- 避免通知循环
- 考虑异步通知的性能影响
```

### 2.4 元数据字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | string | 是 | 全局唯一标识，格式：`gkb-{category}-{name}-{seq}` |
| `type` | string | 是 | 知识类型枚举值 |
| `category` | string | 是 | 所属分类 |
| `tags` | string[] | 是 | 标签列表，用于检索和关联 |
| `version` | string | 是 | 语义化版本号 |
| `created` | datetime | 是 | 创建时间（ISO 8601） |
| `updated` | datetime | 是 | 最后更新时间（ISO 8601） |
| `source` | string | 是 | 知识来源说明 |
| `confidence` | float | 是 | 置信度，范围 [0, 1]，通用知识库初始值 ≥ 0.8 |
| `last_validated` | datetime | 否 | 最后验证时间 |
| `success_count` | int | 否 | 成功应用次数 |
| `failure_count` | int | 否 | 失败应用次数 |

---

## 3. 工作知识库（Working KB）

### 3.1 基本属性

| 属性 | 值 |
|------|-----|
| 存储位置 | `.knowledge/workspace/` |
| 更新频率 | 与项目生命周期同步，需求变更/架构调整时即时更新 |
| 共享范围 | 项目内共享，项目间隔离 |
| 生命周期 | 与项目绑定，项目结束后可选择性归档 |
| 权威性 | 中，项目特定上下文 |

### 3.2 内容分类

| 分类 | 说明 | 示例 |
|------|------|------|
| 项目架构 | 系统架构、模块划分、依赖关系 | 微服务拓扑图、模块依赖矩阵、数据流图 |
| 业务领域 | 业务概念、业务规则、领域模型 | 订单生命周期、支付状态机、用户权限模型 |
| 术语规范 | 项目专用术语与定义 | 业务实体命名、缩写对照表、领域词汇表 |
| API规范 | 内部/外部API接口规范 | RESTful API设计规范、GraphQL Schema、gRPC定义 |
| 环境配置 | 开发/测试/生产环境配置 | 环境变量清单、服务地址映射、特性开关 |
| 团队约定 | 编码风格、分支策略、Review规则 | 提交信息格式、PR模板、代码审查清单 |
| 桌面端架构 | 桌面应用特有架构决策 | 主进程/渲染进程通信方案、自动更新策略、打包配置 |

### 3.3 知识条目格式

```yaml
---
id: "wkb-{project}-arch-microservice-001"
type: "architecture"
category: "项目架构"
tags: ["微服务", "服务拆分", "API网关", "事件总线"]
version: "2.1.0"
created: "2025-06-01T09:00:00Z"
updated: "2026-04-10T16:00:00Z"
source: "架构设计文档 ADR-2025-003"
confidence: 0.90
project: "{project_name}"
scope: "project"
---

# 微服务架构设计

## 服务划分
（项目特定的服务划分方案）

## 通信方式
（服务间通信协议与规范）

## 部署拓扑
（当前部署架构图）
```

### 3.4 与通用知识库的关联

工作知识库中的条目可通过 `references` 字段引用通用知识库中的条目：

```yaml
references:
  - id: "gkb-design-pattern-observer-001"
    relation: "implements"
  - id: "gkb-security-owasp-top10-001"
    relation: "complies"
```

---

## 4. 经验知识库（Experience KB）

### 4.1 基本属性

| 属性 | 值 |
|------|-----|
| 存储位置 | `~/.xuansto/knowledge/experience/`（全局）或 `.knowledge/experience/`（项目级） |
| 更新频率 | 实时自动沉淀 |
| 共享范围 | 可配置为全局共享或项目隔离 |
| 生命周期 | 动态演进，置信度驱动的生命周期管理 |
| 权威性 | 动态，由置信度字段衡量 |

### 4.2 内容分类

| 分类 | 说明 | 示例 |
|------|------|------|
| 错误解决方案 | Bug修复记录、故障排查经验 | OOM排查流程、死锁诊断方法、依赖冲突解决 |
| 成功模式 | 验证有效的开发模式与实践 | 高并发处理方案、缓存策略、批量导入优化 |
| 性能优化 | 性能调优记录与基准数据 | SQL查询优化、内存泄漏修复、渲染性能提升 |
| 安全漏洞 | 安全问题发现与修复记录 | XSS防护方案、CSRF令牌实现、依赖漏洞修复 |
| 集成经验 | 第三方服务/工具集成经验 | OAuth2集成、消息队列接入、支付SDK对接 |
| 重构记录 | 代码重构决策与结果 | 模块拆分重构、数据模型迁移、API版本升级 |
| 桌面端经验 | 桌面平台特定问题与方案 | macOS签名问题、Windows UAC兼容、Linux打包适配 |
| 裁决审计日志 | Agent间分歧的裁决记录与理由 | 技术选型裁决、架构分歧仲裁、优先级冲突解决 |

### 4.3 知识条目格式

```yaml
---
id: "ekb-bugfix-oom-handler-001"
type: "bug_fix"
category: "错误解决方案"
tags: ["OOM", "内存泄漏", "Node.js", "堆内存", "性能"]
version: "1.0.0"
created: "2026-04-15T11:30:00Z"
updated: "2026-04-15T11:30:00Z"
source: "auto_precipitation"
confidence: 0.75
project: "data-pipeline-service"
trigger: "bug_fix_completed"
last_validated: "2026-04-15T11:30:00Z"
success_count: 0
failure_count: 0
---

# Node.js OOM 处理方案

## 错误现象
处理大文件时进程因 OOM 被系统终止，错误码 137。

## 根因分析
1. 文件内容一次性加载到内存
2. 未使用流式处理
3. 默认堆内存限制不足

## 解决方案
1. 使用 stream.Readable 替代 fs.readFileSync
2. 实现背压控制
3. 调整 --max-old-space-size 参数

## 验证结果
处理 2GB 文件内存峰值从 1.8GB 降至 200MB。
```

### 4.4 裁决审计日志格式

```yaml
---
id: "ekb-arbiter-tech-choice-001"
type: "arbiter_log"
category: "裁决审计日志"
tags: ["技术选型", "状态管理", "Zustand", "Redux"]
version: "1.0.0"
created: "2026-04-20T09:00:00Z"
updated: "2026-04-20T09:00:00Z"
source: "arbiter_decision"
confidence: 0.85
project: "admin-dashboard"
---

# 状态管理方案裁决

## 分歧描述
- Backend Developer 建议: Redux Toolkit（生态成熟、中间件丰富）
- Frontend Developer 建议: Zustand（轻量、API简洁）

## 裁决依据
1. 项目规模：中型管理后台，状态复杂度中等
2. 团队熟悉度：Zustand 学习曲线更低
3. Bundle 体积：Zustand ~1KB vs Redux Toolkit ~11KB
4. 中间件需求：仅需日志和持久化，Zustand 中间件可满足

## 裁决结果
采用 Zustand + immer 中间件方案。

## 后续评估
3个月后评估是否需要迁移至 Redux Toolkit。
```

---

## 5. 存储格式规范

### 5.1 格式对照表

| 格式 | 用途 | 文件扩展名 | 编码 | 说明 |
|------|------|-----------|------|------|
| Markdown | 知识条目主体 | `.md` | UTF-8 | 人类可读的知识内容，支持代码块、表格、图表 |
| YAML Frontmatter | 结构化元数据 | 嵌入 `.md` 文件头部 | UTF-8 | 机器可解析的元数据，用于索引和检索 |
| JSON | 向量嵌入索引 | `.json` | UTF-8 | 存储文本向量嵌入，用于语义检索 |
| SQLite | 本地索引数据库 | `.db` | - | FTS5全文索引、元数据索引、检索缓存 |

### 5.2 Markdown规范

- 文件头使用YAML Frontmatter包裹元数据（`---` 分隔）
- 主体使用标准Markdown语法
- 代码块必须标注语言类型
- 图片使用相对路径，存放于同目录的 `assets/` 子目录
- 表格使用标准GitHub Flavored Markdown格式
- 换行使用LF（`\n`），不使用CRLF

### 5.3 YAML Frontmatter规范

```yaml
---
id: string           # 全局唯一标识
type: string         # 知识类型枚举
category: string     # 所属分类
tags: string[]       # 标签列表
version: string      # 语义化版本号 (semver)
created: datetime    # ISO 8601 创建时间
updated: datetime    # ISO 8601 更新时间
source: string       # 知识来源
confidence: float    # 置信度 [0, 1]
# 以下为可选字段
last_validated: datetime   # 最后验证时间
success_count: int         # 成功应用次数
failure_count: int         # 失败应用次数
project: string            # 关联项目（工作/经验知识库）
scope: string              # 作用域: global | project
references:                # 关联知识条目
  - id: string
    relation: string       # implements | complies | extends | refines | contradicts
trigger: string            # 沉淀触发条件（经验知识库）
source_rating: int         # 信源权威性评级 1-5（主动学习）
status: string             # active | pending_review | archived
---
```

### 5.4 JSON向量嵌入格式

```json
{
  "entry_id": "gkb-design-pattern-observer-001",
  "model": "text-embedding-3-small",
  "dimension": 1536,
  "embedding": [0.0123, -0.0456, ...],
  "chunk_text": "观察者模式定义对象间一对多的依赖关系...",
  "chunk_index": 0,
  "created": "2026-03-20T14:30:00Z"
}
```

### 5.5 SQLite索引数据库Schema

```sql
CREATE TABLE entries (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    category TEXT NOT NULL,
    tags TEXT NOT NULL,        -- JSON array
    version TEXT NOT NULL,
    confidence REAL NOT NULL,
    project TEXT,
    scope TEXT DEFAULT 'global',
    status TEXT DEFAULT 'active',
    created TEXT NOT NULL,
    updated TEXT NOT NULL,
    file_path TEXT NOT NULL
);

CREATE VIRTUAL TABLE entries_fts USING fts5(
    id,
    title,
    content,
    tags,
    category,
    tokenize='unicode61'
);

CREATE TABLE cross_references (
    source_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    relation TEXT NOT NULL,
    PRIMARY KEY (source_id, target_id, relation)
);

CREATE TABLE usage_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id TEXT NOT NULL,
    agent TEXT NOT NULL,
    task_type TEXT,
    was_helpful BOOLEAN,
    timestamp TEXT NOT NULL
);

CREATE INDEX idx_entries_type ON entries(type);
CREATE INDEX idx_entries_category ON entries(category);
CREATE INDEX idx_entries_confidence ON entries(confidence);
CREATE INDEX idx_entries_status ON entries(status);
CREATE INDEX idx_entries_project ON entries(project);
CREATE INDEX idx_usage_logs_entry ON usage_logs(entry_id);
CREATE INDEX idx_usage_logs_timestamp ON usage_logs(timestamp);
```

---

## 6. 索引机制

### 6.1 索引类型总览

| 索引类型 | 存储后端 | 检索方式 | 适用场景 |
|----------|---------|---------|---------|
| 关键词索引 | SQLite + FTS5 | BM25排序 | 精确关键词匹配、术语检索 |
| 向量索引 | FAISS / Chroma | 余弦相似度 | 语义相似度检索、模糊概念匹配 |
| 元数据索引 | SQLite | 结构化查询 | 按类型/标签/时间/置信度筛选 |
| 交叉引用 | JSON | 图遍历 | 知识条目间关联与追溯 |

### 6.2 关键词索引（SQLite + FTS5）

- 使用SQLite的FTS5全文搜索引擎
- 支持Unicode分词（`unicode61` tokenizer）
- BM25算法排序，支持短语匹配和前缀匹配
- 索引字段：`id`、`title`、`content`、`tags`、`category`
- 增量更新：知识条目变更时实时更新FTS索引

```sql
-- 关键词检索示例
SELECT e.id, e.category, e.confidence,
       bm25(entries_fts) AS rank
FROM entries_fts f
JOIN entries e ON f.id = e.id
WHERE entries_fts MATCH '观察者模式 事件驱动'
ORDER BY rank
LIMIT 10;
```

### 6.3 向量索引（FAISS / Chroma）

- 文本嵌入模型：`text-embedding-3-small`（1536维）或项目配置的嵌入模型
- 索引构建：知识条目按段落分块（chunk），每块生成向量嵌入
- 存储格式：FAISS IndexFlatIP（内积索引）或 Chroma Collection
- 相似度度量：余弦距离（cosine distance）
- 增量更新：新增/修改条目时追加向量，删除条目时标记为无效

```
向量索引配置:
  model: text-embedding-3-small
  dimension: 1536
  chunk_size: 512 tokens
  chunk_overlap: 64 tokens
  metric: cosine
  index_type: IndexFlatIP
```

### 6.4 元数据索引（SQLite）

- 基于entries表的索引字段进行结构化查询
- 支持多维度组合筛选：类型 + 标签 + 时间范围 + 置信度阈值
- 用于检索前的预过滤，缩小向量检索范围

```sql
-- 元数据筛选示例
SELECT id, category, confidence, updated
FROM entries
WHERE type = 'design_pattern'
  AND confidence >= 0.7
  AND status = 'active'
  AND updated > '2026-01-01'
ORDER BY confidence DESC;
```

### 6.5 交叉引用索引（JSON）

- 存储知识条目间的关联关系
- 支持的关系类型：`implements`、`complies`、`extends`、`refines`、`contradicts`
- 用于知识追溯和影响分析

```json
{
  "source_id": "ekb-bugfix-oom-handler-001",
  "relations": [
    {
      "target_id": "gkb-devops-nodejs-memory-001",
      "relation": "extends",
      "description": "基于通用Node.js内存管理规范的具体实践"
    },
    {
      "target_id": "wkb-data-pipeline-arch-001",
      "relation": "complies",
      "description": "符合项目数据管道架构设计"
    }
  ]
}
```

---

## 7. 并发写入冲突处理机制

### 7.1 乐观锁机制

当多个 Agent 同时写入同一条目时，采用乐观锁 + 三级冲突解决策略。

每个知识条目包含 `_version` 和 `_last_modified` 字段：

```yaml
metadata:
  _version: 3
  _last_modified: "2026-04-29T10:30:00Z"
  _last_modified_by: "security-auditor"
```

写入时检查版本号：如果读取后版本号已被其他 Agent 修改，触发冲突解决流程。

### 7.2 三级冲突解决策略

| 级别 | 条件 | 策略 | 说明 |
|------|------|------|------|
| L1 自动合并 | 变更不重叠 | 自动合并 | 不同字段的修改可直接合并 |
| L2 基于优先级 | 变更重叠但优先级明确 | 高优先级覆盖 | 安全相关 Agent 优先级最高 |
| L3 人工裁决 | 变更重叠且优先级冲突 | 创建裁决请求 | Orchestrator 介入或请求人类决策 |

### 7.3 Agent 优先级排序（写入冲突时）

1. Security Auditor / Compliance Officer（安全优先）
2. System Architect（架构一致性）
3. Product Manager（需求权威性）
4. 其他 Agent（按任务阶段顺序）

### 7.4 冲突检测流程

```
Agent A 读取条目 (version=3)
Agent B 读取条目 (version=3)
Agent A 写入 (version=3 → 4) ✓ 成功
Agent B 写入 (version=3 → 4) ✗ 版本冲突
  → 检查变更重叠
    → 不重叠 → L1 自动合并 (version=5)
    → 重叠 → 检查优先级
      → Agent B 优先级更高 → L2 覆盖 (version=5)
      → 优先级冲突 → L3 裁决请求
```

---

## 8. 灾难恢复策略

### 8.1 备份策略

| 备份类型 | 频率 | 保留期限 | 存储位置 |
|----------|------|---------|---------|
| 完整备份 | 每日 | 30 天 | `.knowledge/backup/full/` |
| 增量备份 | 每小时 | 7 天 | `.knowledge/backup/incremental/` |
| 快照备份 | 每次重大变更 | 永久 | `.knowledge/backup/snapshot/` |

> **备份目录自动创建**：备份目录（`.knowledge/backup/full/`、`.knowledge/backup/incremental/`、`.knowledge/backup/snapshot/`）SHALL 在知识服务首次运行初始化时由 `first_run_import()` 函数自动创建，确保备份机制在知识库创建之初即可用，无需人工干预。

### 8.2 恢复流程

1. **条目级恢复**：从备份中恢复单个知识条目
   - 定位条目在最近备份中的版本
   - 验证条目完整性（元数据、内容、索引）
   - 恢复条目并更新索引

2. **索引级恢复**：重建损坏的索引文件
   - 从条目文件重新生成 keyword_index.db
   - 从条目文件重新生成 metadata_index.json
   - 从条目文件重新生成 cross_reference.json
   - vector_index.json 需要重新计算嵌入向量

3. **全量恢复**：从备份恢复整个知识库
   - 停止所有 Agent 写入操作
   - 从最近完整备份恢复
   - 按时间顺序应用增量备份
   - 重建所有索引
   - 验证知识库完整性

### 8.3 损坏检测

| 检测项 | 方法 | 频率 |
|--------|------|------|
| 文件完整性 | SHA256 校验和 | 每次读取 |
| 索引一致性 | 条目数 vs 索引记录数 | 每日 |
| 元数据完整性 | 必填字段检查 | 每次写入 |
| 交叉引用有效性 | 引用目标存在性检查 | 每日 |

### 8.4 版本回退

- 每次知识库变更都记录在 CHANGELOG.md 中
- 通过 Git 可回退到任意历史版本
- 回退操作需要 Orchestrator 审批
- 回退后需重建索引

---

## 9. 检索策略

### 9.1 语义检索

- **算法**：向量相似度（余弦距离）
- **流程**：查询文本 → 嵌入向量化 → 向量索引检索 → Top-K结果
- **参数**：
  - `top_k`: 返回结果数，默认10
  - `similarity_threshold`: 相似度阈值，默认0.7
  - `rerank`: 是否启用重排序，默认true

```
语义检索流程:
  Query → Embedding Model → Vector Index → Top-K Candidates → Reranker → Results
```

### 9.2 关键词检索

- **算法**：BM25排序
- **流程**：查询关键词 → FTS5匹配 → BM25排序 → Top-K结果
- **参数**：
  - `top_k`: 返回结果数，默认10
  - `match_mode`: 匹配模式（AND/OR/PHRASE），默认OR

### 9.3 混合检索

- **算法**：语义检索 + 关键词检索加权融合
- **权重**：语义 0.7 + 关键词 0.3
- **融合方式**：Reciprocal Rank Fusion (RRF)

```
混合检索流程:
  Query ──┬──→ 语义检索 → 语义排名列表
          │
          └──→ 关键词检索 → 关键词排名列表
                    │
                    ▼
          RRF 融合 (语义×0.7 + 关键词×0.3)
                    │
                    ▼
               融合排序结果
```

**RRF融合公式**：

```
score(d) = 0.7 × (1 / (k + rank_semantic(d))) + 0.3 × (1 / (k + rank_keyword(d)))
```

其中 `k = 60`（标准RRF参数）

### 9.4 上下文检索

- **触发条件**：Agent执行特定任务时，基于任务类型和当前上下文自动筛选
- **筛选维度**：
  - 任务类型（bug_fix / feature / refactor / review / deploy）
  - 技术栈（语言/框架/运行时）
  - 项目上下文（工作知识库中的架构和约定）
  - 置信度阈值（默认 ≥ 0.5）

```
上下文检索流程:
  Task Context → 确定检索范围 → 元数据预过滤 → 混合检索 → 上下文排序 → 结果
```

### 9.5 检索策略选择

| 场景 | 推荐策略 | 原因 |
|------|---------|------|
| 精确术语查找 | 关键词检索 | 术语需要精确匹配 |
| 概念性查询 | 语义检索 | 自然语言描述需语义理解 |
| 综合知识查询 | 混合检索 | 兼顾语义理解和关键词精确性 |
| 任务驱动检索 | 上下文检索 | 基于任务上下文精准筛选 |

---

## 10. Agent知识检索机制与注入流程

### 10.1 各Agent知识检索策略

| Agent | 优先检索层 | 关键检索类别 | 检索策略 |
|-------|-----------|-------------|---------|
| Code Reviewer | 工作知识库 > 通用知识库 > 经验知识库 | 错误解决方案、编码规范、重构记录 | 混合检索，关键词权重0.6 |
| Backend Developer | 工作→经验→通用 | 项目架构、API规范、性能优化 | 上下文检索 + 语义检索 |
| Security Auditor | 通用知识库 > 经验知识库 > 工作知识库 | 安全漏洞、安全规范、裁决日志 | 关键词检索 + 语义检索 |
| Test Architect | 通用→经验→工作 | 测试规范、错误解决方案、成功模式 | 语义检索，相似度阈值0.75 |
| Desktop Developer | 工作→经验→通用 | 桌面端架构、桌面端经验、桌面开发规范 | 上下文检索 + 混合检索 |
| Build & Release Engineer | 经验→通用→工作 | DevOps规范、集成经验、环境配置 | 关键词检索，精确匹配 |

### 10.2 知识注入流程

```
┌──────────────────────────────────────────────────────────────────┐
│                      Agent 知识注入流程                           │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ① 接收任务                                                      │
│     │                                                            │
│     ▼                                                            │
│  ② 分析知识需求                                                  │
│     │  - 确定任务类型 (bug_fix/feature/refactor/...)              │
│     │  - 提取关键概念和术语                                       │
│     │  - 确定检索范围和策略                                       │
│     ▼                                                            │
│  ③ 检索知识库                                                    │
│     │  - 按Agent优先级检索三层知识库                               │
│     │  - 执行混合检索（语义+关键词+上下文）                        │
│     │  - 过滤低置信度条目 (confidence < 0.5)                      │
│     │  - 去重与排序                                               │
│     ▼                                                            │
│  ④ 注入上下文                                                    │
│     │  - 将检索结果格式化为结构化上下文                             │
│     │  - 按相关性排序插入Agent提示词                               │
│     │  - 标注知识来源和置信度                                      │
│     │  - 控制注入量（token上限：2048）                             │
│     ▼                                                            │
│  ⑤ 执行任务                                                      │
│     │  - Agent基于注入知识执行任务                                 │
│     │  - 记录知识使用情况                                          │
│     ▼                                                            │
│  ⑥ 记录使用日志                                                  │
│     │  - 写入 usage_logs 表                                       │
│     │  - 记录 entry_id / agent / task_type / was_helpful          │
│     ▼                                                            │
│  ⑦ 沉淀新知识                                                    │
│     │  - 根据任务结果自动触发沉淀规则                              │
│     │  - 生成新知识条目或更新现有条目                               │
│     ▼                                                            │
│  ⑧ 更新知识库                                                    │
│     - 写入新条目或更新现有条目                                     │
│     - 更新索引（FTS5 + 向量索引）                                  │
│     - 调整置信度                                                  │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 10.3 知识注入格式

注入到Agent上下文的知识采用以下结构化格式：

```
## 📚 知识库参考 (Knowledge Base References)

### [经验] Node.js OOM 处理方案 (置信度: 0.75)
> 来源: 经验知识库 | 更新: 2026-04-15 | 引用: ekb-bugfix-oom-handler-001

使用 stream.Readable 替代 fs.readFileSync，实现背压控制...
[详见: ekb-bugfix-oom-handler-001]

### [通用] 观察者模式 (置信度: 0.95)
> 来源: 通用知识库 | 更新: 2026-03-20 | 引用: gkb-design-pattern-observer-001

定义对象间一对多的依赖关系...
[详见: gkb-design-pattern-observer-001]

---
⚠️ 以上知识仅供参考，请结合项目实际情况判断适用性。
```

---

## 11. 知识自动沉淀

### 11.1 触发条件与沉淀内容对照表

| 触发条件 | 沉淀内容 | 目标知识库 | 置信度初始值 |
|----------|---------|-----------|-------------|
| Bug修复完成 | 错误现象 + 根因 + 解决方案 | 经验知识库 | 0.70 |
| 新模式验证成功 | 模式描述 + 代码示例 + 适用场景 | 经验知识库 | 0.75 |
| 架构决策确定 | ADR文档（决策背景+方案对比+结论） | 工作知识库 | 0.85 |
| 安全漏洞修复 | 漏洞详情 + 修复方案 + 影响范围 | 经验知识库 | 0.80 |
| 性能优化完成 | 优化前基准 + 优化方案 + 优化后基准 | 经验知识库 | 0.70 |
| 集成完成 | 集成方案 + 踩坑记录 + 配置要点 | 经验知识库 | 0.65 |
| 重构完成 | 重构原因 + 重构策略 + 影响评估 | 经验知识库 | 0.70 |
| 桌面平台经验 | 平台特定问题 + 兼容方案 + 签名配置 | 经验知识库 | 0.70 |
| Agent裁决完成 | 分歧描述 + 裁决依据 + 裁决结果 | 经验知识库 | 0.80 |
| 测试用例发现边界条件 | 边界条件描述 + 测试策略 + 覆盖建议 | 经验知识库 | 0.60 |

### 11.2 沉淀流程

```
触发事件 → 提取关键信息 → 生成知识条目草稿 → Specification Keeper审核
    │                                              │
    │                                    ┌─────────┴─────────┐
    │                                    ▼                   ▼
    │                               审核通过              审核驳回
    │                                    │                   │
    │                                    ▼                   ▼
    │                           写入知识库              修改后重新提交
    │                           更新索引                或丢弃
    │                                    │
    ▼                                    ▼
记录沉淀日志 ←────────────────────── 完成
```

### 11.3 沉淀质量保障

- **去重检查**：新条目与现有条目的余弦相似度 > 0.85 时，触发合并而非新建
- **格式校验**：YAML Frontmatter字段完整性检查，缺失必填字段则拒绝写入
- **置信度初始化**：根据触发条件和来源设定初始置信度，自动沉淀的条目初始值 ≤ 0.80
- **审核机制**：Specification Keeper对自动沉淀的条目进行质量审核

---

## 12. 版本管理与增量更新

### 12.1 Git集成

- 知识库与代码库存储于同一Git仓库（`.knowledge/` 目录）
- 通用知识库（`~/.xuansto/knowledge/general/`）独立Git仓库管理
- 知识条目变更遵循与代码相同的提交规范
- 提交信息格式：`kb({scope}): {type} {entry_id} - {description}`

```
提交信息示例:
  kb(workspace): add wkb-admin-arch-001 - 添加管理后台架构知识
  kb(experience): update ekb-bugfix-oom-001 - 补充流式处理方案
  kb(general): refactor gkb-design-pattern-* - 重构设计模式分类体系
```

### 12.2 语义化版本

知识库变更遵循语义化版本规范（SemVer）：

| 版本类型 | 触发条件 | 示例 |
|---------|---------|------|
| MAJOR | 知识体系重大重构，不兼容旧版 | 1.x → 2.0 |
| MINOR | 新增知识分类或大量新条目 | 1.5 → 1.6 |
| PATCH | 单个条目修正或少量更新 | 1.6.0 → 1.6.1 |

每个知识条目独立版本号，知识库整体版本号记录于 `.knowledge/VERSION` 文件。

### 12.3 变更日志

- 变更日志存放于 `.knowledge/CHANGELOG.md`
- 格式遵循 [Keep a Changelog](https://keepachangelog.com/) 规范
- 每次知识更新自动追加变更记录

```markdown
## [1.6.0] - 2026-04-28

### Added
- 新增桌面端架构知识分类 (wkb-desktop-arch-*)
- 新增裁决审计日志经验分类 (ekb-arbiter-*)

### Changed
- 更新观察者模式条目，补充异步通知注意事项 (gkb-design-pattern-observer-001)

### Fixed
- 修正Node.js OOM方案中的背压控制代码示例 (ekb-bugfix-oom-handler-001)
```

### 12.4 分支管理

- 支持知识库的分支探索和合并
- `kb/experiment/*` 分支：实验性知识探索
- `kb/hotfix/*` 分支：紧急知识修正
- 合并策略：知识条目冲突时，保留更高置信度的版本

### 12.5 多环境同步

| 环境 | 同步策略 | 版本策略 |
|------|---------|---------|
| 开发环境 | 实时同步，文件变更即时反映 | 跟踪最新版本 |
| 测试环境 | 按需同步，CI触发时拉取 | 锁定到指定版本 |
| 生产环境 | 版本锁定，仅通过CI/CD更新 | 严格版本控制，需审批 |

---

## 13. 主动学习机制

### 13.1 外部知识摄入

Technical Writer扩展为Research Agent，负责外部知识摄入：

```
外部知识摄入流程:
  识别知识缺口 → 搜索外部信源 → 提取关键信息 → 生成结构化条目
       │                                          │
       ▼                                          ▼
  分析当前知识库覆盖度                    标记 confidence: 0.6（待验证）
  识别薄弱领域                            标记 source_rating（信源评级）
```

**搜索范围**：
- 官方技术文档（MDN、docs.rs、docs.python.org等）
- 社区FAQ（Stack Overflow、GitHub Discussions）
- GitHub Issues与Pull Requests
- 技术博客与会议论文
- 安全公告（CVE、NVD）

### 13.2 信源权威性评级

| 评级 | 信源类型 | 示例 | 自动沉淀权限 |
|------|---------|------|-------------|
| 5 | 官方文档 | MDN、docs.rs、React官方文档 | 可自动沉淀 |
| 4 | 官方仓库 | GitHub官方Repo的Issue/PR | 需验证沙箱通过 |
| 3 | 权威社区 | Stack Overflow高票回答、RFC文档 | 需验证沙箱通过 |
| 2 | 一般社区 | 技术博客、Medium文章 | 需人工审核 |
| 1 | 无法确认来源 | 匿名论坛、无引用文章 | 不可沉淀 |

**规则**：仅 `source_rating ≥ 3` 的知识条目可进入自动沉淀流程；`source_rating ≤ 4` 的条目需通过验证沙箱。

### 13.3 外部知识验证沙箱

```
验证沙箱流程:
  source_rating ≤ 4 的知识条目
       │
       ▼
  进入隔离验证沙箱
       │
       ├─→ Test Architect 生成针对性测试
       │       │
       │       ▼
       │   执行测试验证
       │       │
       │   ┌───┴───┐
       │   ▼       ▼
       │ 通过    失败
       │   │       │
       │   ▼       ▼
       │ 提升     降低
       │ confidence  confidence
       │ 至0.7     至0.3
       │   │       │
       │   ▼       ▼
       │ 正式    标记
       │ 写入    "待审查"
       │
       └─→ source_rating = 5 的条目可直接写入
           （confidence 初始值 0.6）
```

### 13.4 代码库考古

Orchestrator触发"项目理解"子流程，深入分析代码库：

| 分析维度 | 方法 | 产出 |
|---------|------|------|
| Git历史 | 分析提交频率、变更热点、贡献者模式 | 变更热点图、技术债务识别 |
| 目录结构 | 分析模块划分、依赖关系、分层架构 | 架构知识条目 |
| 隐含约定 | 分析命名模式、代码风格、注释习惯 | 团队约定知识条目 |
| 依赖图谱 | 分析package.json/Cargo.toml/go.mod | 技术栈知识条目 |
| 测试覆盖 | 分析测试目录结构、覆盖率报告 | 测试策略知识条目 |

### 13.5 社区知识消化

- 支持订阅技术栈更新源（RSS、GitHub Release、npm registry）
- 主动生成技术更新摘要
- 评估对当前项目的影响

```
社区知识消化流程:
  订阅源轮询 → 检测更新 → 生成摘要 → 影响评估 → 通知相关Agent
                                    │
                                    ▼
                              评估影响范围:
                              - 是否影响当前项目依赖？
                              - 是否引入Breaking Change？
                              - 是否修复已知安全问题？
                              - 是否提供性能改进？
```

---

## 14. 知识生命周期管理

### 14.1 置信度动态调整

置信度是知识条目可信度的核心指标，基于实际使用效果动态调整：

**调整规则**：

| 事件 | 调整幅度 | 说明 |
|------|---------|------|
| 成功应用 | +0.02 | `success_count` +1，置信度提升 |
| 应用失败 | -0.05 | `failure_count` +1，置信度下降 |
| 通过验证沙箱 | +0.10 | 外部知识验证通过 |
| 验证沙箱失败 | -0.15 | 外部知识验证失败 |
| 人工确认 | +0.10 | Specification Keeper审核确认 |
| 人工驳回 | -0.20 | Specification Keeper审核驳回 |
| 长期未使用（30天） | -0.01 | 每30天衰减一次 |

**状态转换**：

```
           confidence ≥ 0.8          0.3 ≤ confidence < 0.8         confidence < 0.3
          ┌──────────────┐         ┌────────────────────┐        ┌──────────────┐
          │   ✅ 可信     │         │   ⚠️ 待验证        │        │   🔴 待审查   │
          │   active     │◄───────►│   active           │◄──────►│   pending_   │
          │              │  提升/   │                    │  提升/  │   review     │
          │              │  下降    │                    │  下降   │              │
          └──────────────┘         └────────────────────┘        └──────┬───────┘
                                                                            │
                                                                    90天未使用
                                                                    且 < 0.5
                                                                            │
                                                                            ▼
                                                                  ┌──────────────┐
                                                                  │   📦 已归档   │
                                                                  │   archived   │
                                                                  └──────────────┘
```

### 14.2 知识去重与合并

**去重检测**：
- 新条目写入前，与现有条目进行语义相似度计算
- 余弦相似度 > 0.85 时触发合并流程

**合并策略**：

| 场景 | 策略 |
|------|------|
| 两个条目置信度差异 > 0.2 | 保留高置信度条目，将低置信度条目的独特内容合并为补充段落 |
| 两个条目置信度接近 | 合并为新条目，置信度取加权平均，版本号递增 |
| 一个条目是另一个的细化 | 保留细化条目，建立 `refines` 交叉引用 |

**合并后处理**：
- 更新所有引用旧条目的交叉引用
- 保留合并历史记录于条目的 `merge_history` 字段
- 更新FTS索引和向量索引

### 14.3 定期归档

**归档条件**（同时满足）：
- 连续90天未使用（`usage_logs` 无记录）
- 置信度 < 0.5

**归档流程**：

```
定期扫描（每周） → 识别满足归档条件的条目 → 标记 status: "archived"
    → 移动到 archive/ 目录 → 更新索引 → 记录变更日志
```

**归档恢复**：
- 归档条目仍可通过显式查询检索
- 被引用时自动恢复为 `pending_review` 状态
- 人工审核后可恢复为 `active` 状态

---

## 15. 跨项目知识泛化

### 15.1 泛化筛选

Specification Keeper定期扫描经验知识库，识别可泛化的成功模式：

**筛选条件**：
- 被3个以上项目验证的成功模式
- 置信度 ≥ 0.85
- 不包含项目特定的业务逻辑

**泛化流程**：

```
定期扫描经验知识库
    │
    ▼
识别多项目验证的成功模式 (≥3个项目, confidence ≥ 0.85)
    │
    ▼
提取通用部分，去除项目特定细节
    │
    ▼
技术栈适配校验
    │
    ├─→ 技术栈匹配 → 生成通用知识条目 → 写入通用知识库
    │
    └─→ 技术栈不匹配 → 降低推荐权重 → 标记"需手动适配"
```

### 15.2 技术栈适配校验

泛化知识条目前，强制检查技术栈差异：

| 校验维度 | 校验方式 | 不匹配处理 |
|---------|---------|-----------|
| 编程语言 | 比对源项目与目标项目的语言 | 降低推荐权重0.2，标记"需手动适配" |
| 框架版本 | 比对主要框架版本差异 | 标注版本兼容性说明 |
| 运行时环境 | 比对运行时（Node/Bun/Deno等） | 标注运行时特定注意事项 |
| 桌面框架 | 比对Electron/Tauri/WPF等 | 降低推荐权重0.3，标记"需手动适配" |
| 数据库 | 比对数据库类型和版本 | 标注数据库特定语法差异 |

### 15.3 迁移学习标记

泛化后的知识条目保留源项目引用，便于追溯：

```yaml
---
id: "gkb-pattern-circuit-breaker-001"
type: "design_pattern"
category: "设计模式"
tags: ["熔断器", "容错", "微服务", "弹性设计"]
version: "1.0.0"
created: "2026-04-20T10:00:00Z"
updated: "2026-04-20T10:00:00Z"
source: "cross_project_generalization"
confidence: 0.88
generalized_from:
  - project: "order-service"
    entry_id: "ekb-pattern-circuit-breaker-001"
    validated_at: "2026-03-15"
  - project: "payment-gateway"
    entry_id: "ekb-pattern-circuit-breaker-002"
    validated_at: "2026-03-20"
  - project: "notification-service"
    entry_id: "ekb-pattern-circuit-breaker-003"
    validated_at: "2026-04-10"
tech_stack_compatibility:
  languages: ["TypeScript", "Python", "Go"]
  frameworks: ["Express", "FastAPI", "Gin"]
  runtime: ["Node.js >= 18", "Python >= 3.10", "Go >= 1.21"]
---
```

---

## 16. 目录结构

```
.knowledge/
├── VERSION                              # 知识库整体版本号
├── CHANGELOG.md                         # 变更日志
├── config.yaml                          # 知识库配置（嵌入模型、检索参数等）
│
├── general/                             # 通用知识库
│   ├── paradigms/                       # 编程范式
│   │   ├── functional-programming.md
│   │   ├── oop-principles.md
│   │   ├── reactive-patterns.md
│   │   └── solid-principles.md
│   ├── standards/                       # 开发规范
│   │   ├── coding-standards.md
│   │   ├── documentation-standards.md
│   │   └── naming-conventions.md
│   ├── patterns/                        # 设计模式
│   │   ├── anti-patterns/               # 反模式
│   │   ├── architectural-patterns/      # 架构模式
│   │   ├── gof-patterns/                # GoF设计模式
│   │   └── observer-pattern.md
│   ├── security/                        # 安全规范
│   │   ├── authentication.md
│   │   ├── owasp-top10.md
│   │   └── secure-coding.md
│   ├── testing/                         # 测试规范
│   │   ├── e2e-testing.md
│   │   ├── tdd-practices.md
│   │   └── test-pyramid.md
│   └── desktop/                         # 桌面开发规范
│       ├── cross-platform-desktop-patterns.md
│       ├── desktop-security-guidelines.md
│       ├── electron-best-practices.md
│       └── tauri-guidelines.md
│
├── workspace/                           # 工作知识库
│   ├── architecture/                    # 项目架构
│   │   ├── system-overview.md
│   │   ├── module-diagram.md
│   │   └── dependency-graph.md
│   ├── domain/                          # 业务领域
│   │   ├── business-concepts.md
│   │   ├── business-rules.md
│   │   └── user-journeys.md
│   ├── api/                             # API规范
│   │   ├── data-models.md
│   │   └── error-codes.md
│   ├── environment/                     # 环境配置
│   │   ├── env-variables.md
│   │   ├── dev-setup.md
│   │   └── deployment.md
│   ├── conventions/                     # 团队约定
│   │   ├── commit-conventions.md
│   │   ├── code-review.md
│   │   └── branch-strategy.md
│   ├── desktop/                         # 桌面端架构
│   │   ├── ipc-architecture.md
│   │   ├── build-config.md
│   │   ├── platform-matrix.md
│   │   └── signing-setup.md
│   └── glossary/                        # 术语表
│       ├── terms.md
│       ├── abbreviations.md
│       └── naming-conventions.md
│
├── experience/                          # 经验知识库
│   ├── errors/                          # 错误解决方案
│   │   ├── general/
│   │   ├── api/
│   │   ├── database/
│   │   ├── desktop/
│   │   ├── authentication/
│   │   ├── network/
│   │   └── performance/
│   ├── patterns/                        # 成功模式
│   │   ├── code-patterns/
│   │   ├── architecture-patterns/
│   │   └── integration-patterns/
│   ├── performance/                     # 性能优化
│   │   ├── database-optimization/
│   │   └── caching-strategies/
│   ├── security/                        # 安全漏洞
│   │   ├── vulnerabilities/
│   │   ├── fixes/
│   │   └── prevention/
│   ├── integration/                     # 集成经验
│   │   ├── apis/
│   │   └── tools/
│   ├── desktop/                         # 桌面端经验
│   │   ├── signing-issues/
│   │   ├── build-fixes/
│   │   └── platform-compatibility/
│   └── decisions/                       # 裁决审计日志
│       └── arbitration-log.md
│
├── backup/                              # 知识库备份（自动创建）
│   ├── full/                            # 全量备份
│   ├── incremental/                     # 增量备份
│   └── snapshot/                        # 快照备份
│
└── index/                               # 索引目录（集中管理）
    ├── keyword_index.db                 # SQLite关键词索引
    ├── metadata_index.json              # 元数据索引
    └── cross_reference.json             # 交叉引用索引
```

---

## 17. 知识库数据库服务层架构

### 17.1 服务层架构概述

知识库数据库服务层作为v1.8.0新增的核心基础设施，将原有的纯文件存储模式升级为服务化架构，提供统一的数据访问接口和混合检索能力。

```
┌─────────────────────────────────────────────────────────────────────┐
│                     知识库数据库服务层架构                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────────┐    │
│  │  FastAPI HTTP   │  │  MCP Tool       │  │  WebSocket       │    │
│  │  REST API       │  │  Interface      │  │  实时通知         │    │
│  │  :8900/v1/*    │  │  knowledge_*    │  │  /ws/notify      │    │
│  └────────┬────────┘  └────────┬────────┘  └────────┬─────────┘    │
│           │                    │                     │              │
│           └────────────────────┼─────────────────────┘              │
│                                │                                    │
│                     ┌──────────▼──────────┐                         │
│                     │   服务编排层         │                         │
│                     │   (Service Layer)   │                         │
│                     └──────────┬──────────┘                         │
│                                │                                    │
│              ┌─────────────────┼─────────────────┐                  │
│              │                 │                  │                  │
│     ┌────────▼────────┐ ┌─────▼──────┐ ┌────────▼────────┐        │
│     │ SQLite 结构化   │ │ Chroma     │ │ 文件存储        │        │
│     │ 存储引擎        │ │ 向量语义   │ │ (Fallback)      │        │
│     │ knowledge.db    │ │ Collection │ │ v1.6兼容模式    │        │
│     └─────────────────┘ └────────────┘ └─────────────────┘        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**三大接口通道**：

| 通道 | 协议 | 用途 | 消费者 |
|------|------|------|--------|
| FastAPI HTTP REST | HTTP/1.1 | 标准CRUD操作、混合检索、健康检查 | 外部工具、CI/CD、管理界面 |
| MCP Tool Interface | MCP Protocol | Agent直接调用知识检索与写入 | Xuansto多Agent系统 |
| WebSocket实时通知 | WebSocket | 知识变更推送、冲突预警 | 订阅Agent、监控面板 |

### 17.2 双引擎设计理念

| 引擎 | 职责 | 存储格式 | 检索能力 |
|------|------|---------|---------|
| **SQLite结构化存储** | 知识条目CRUD、元数据管理、全文检索、版本追踪 | `knowledge.db` (WAL模式) | FTS5全文搜索、结构化查询、事务支持 |
| **Chroma向量语义检索** | 语义相似度检索、向量嵌入管理 | Chroma Collection | 余弦相似度、语义匹配、模糊概念检索 |

**双引擎协同**：写入时同步更新SQLite和Chroma，读取时通过混合检索引擎融合两路结果。

### 17.3 数据流全景

```
写入流:
  Agent → MCP Tool / REST API → 服务编排层
      → SQLite (结构化存储 + FTS索引更新)
      → Chroma (向量嵌入计算 + Collection更新)
      → WebSocket (变更通知 → 订阅Agent)

读取流:
  查询请求 → 服务编排层 → 混合检索引擎
      → SQLite FTS5 (关键词检索 → 排名列表)
      → Chroma (语义检索 → 排名列表)
      → RRF融合 → 排序结果 → 返回

通知流:
  知识变更 → WebSocket Hub
      → 推送变更事件 (create/update/delete)
      → 订阅Agent接收通知
      → 触发上下文更新或冲突检测
```

### 17.4 向后兼容策略

v1.6.0文件存储模式作为fallback，服务层不可用时自动降级：

| 场景 | 行为 |
|------|------|
| 服务层正常启动 | 所有操作走服务层（SQLite + Chroma） |
| 服务层启动失败 | 自动降级为v1.6文件存储模式，日志记录降级事件 |
| 服务层运行中崩溃 | 已有请求返回错误，新请求降级为文件存储模式 |
| 服务层恢复 | 自动从文件存储模式切回服务层，同步期间变更 |

```
降级检测流程:
  服务启动 → 检测SQLite/Chroma可用性
      → 可用 → 正常模式
      → 不可用 → 记录降级日志 → 切换文件存储模式 → 定时重试连接
          → 重连成功 → 同步降级期间变更 → 切回正常模式
```

---

## 18. SQLite结构化存储设计

### 18.1 数据表DDL

```sql
CREATE TABLE knowledge_entries (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL DEFAULT 'unknown',
    category TEXT NOT NULL DEFAULT 'uncategorized',
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    summary TEXT,
    content_path TEXT,
    scope TEXT NOT NULL CHECK(scope IN ('general','workspace','experience')),
    tags TEXT DEFAULT '[]',
    confidence REAL DEFAULT 0.6 CHECK(confidence BETWEEN 0 AND 1),
    source TEXT,
    source_rating INTEGER DEFAULT 3 CHECK(source_rating BETWEEN 1 AND 5),
    occurrences INTEGER DEFAULT 1,
    content_hash TEXT,
    last_validated TEXT,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    version INTEGER DEFAULT 1,
    embedding_status TEXT DEFAULT 'pending' CHECK(embedding_status IN ('pending','ready')),
    embedding_retry_count INTEGER DEFAULT 0,
    created TEXT DEFAULT (datetime('now')),
    updated TEXT DEFAULT (datetime('now'))
);

CREATE TABLE knowledge_tags (
    entry_id TEXT NOT NULL,
    tag TEXT NOT NULL,
    PRIMARY KEY (entry_id, tag),
    FOREIGN KEY (entry_id) REFERENCES knowledge_entries(id) ON DELETE CASCADE
);

CREATE TABLE version_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id TEXT NOT NULL,
    version INTEGER NOT NULL,
    title TEXT,
    content TEXT,
    scope TEXT,
    tags TEXT,
    confidence REAL,
    source_path TEXT,
    source_rating INTEGER,
    content_hash TEXT,
    change_type TEXT DEFAULT 'update',
    content_snapshot TEXT,
    saved_at TEXT NOT NULL,
    FOREIGN KEY (entry_id) REFERENCES knowledge_entries(id) ON DELETE CASCADE
);

CREATE TABLE dedup_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    new_entry_id TEXT NOT NULL,
    existing_entry_id TEXT NOT NULL,
    similarity_score REAL NOT NULL,
    action TEXT NOT NULL CHECK(action IN ('skip', 'merge', 'keep_both')),
    merged_at TEXT,
    FOREIGN KEY (new_entry_id) REFERENCES knowledge_entries(id),
    FOREIGN KEY (existing_entry_id) REFERENCES knowledge_entries(id)
);

CREATE TABLE reconciliation_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    check_time TEXT NOT NULL,
    sqlite_ready_count INTEGER,
    chroma_vector_count INTEGER,
    missing_in_chroma INTEGER DEFAULT 0,
    orphan_in_chroma INTEGER DEFAULT 0,
    fixed_count INTEGER DEFAULT 0,
    details TEXT
);

CREATE TABLE backup_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    backup_path TEXT NOT NULL,
    backup_size INTEGER,
    entry_count INTEGER,
    created_at TEXT NOT NULL,
    status TEXT DEFAULT 'completed'
);

CREATE VIRTUAL TABLE knowledge_fts USING fts5(
    id UNINDEXED,
    summary,
    type,
    category,
    content='knowledge_entries',
    content_rowid='rowid',
    tokenize='unicode61'
);

CREATE TRIGGER IF NOT EXISTS knowledge_entries_ai AFTER INSERT ON knowledge_entries BEGIN
    INSERT INTO knowledge_fts(rowid, id, summary, type, category)
    VALUES (new.rowid, new.id, new.summary, new.type, new.category);
END;

CREATE TRIGGER IF NOT EXISTS knowledge_entries_ad AFTER DELETE ON knowledge_entries BEGIN
    INSERT INTO knowledge_fts(knowledge_fts, rowid, id, summary, type, category)
    VALUES ('delete', old.rowid, old.id, old.summary, old.type, old.category);
END;

CREATE TRIGGER IF NOT EXISTS knowledge_entries_au AFTER UPDATE ON knowledge_entries BEGIN
    INSERT INTO knowledge_fts(knowledge_fts, rowid, id, summary, type, category)
    VALUES ('delete', old.rowid, old.id, old.summary, old.type, old.category);
    INSERT INTO knowledge_fts(rowid, id, summary, type, category)
    VALUES (new.rowid, new.id, new.summary, new.type, new.category);
END;

CREATE TABLE schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL,
    description TEXT
);
```

### 18.2 索引定义

```sql
CREATE INDEX idx_entries_type ON knowledge_entries(type);
CREATE INDEX idx_entries_category ON knowledge_entries(category);
CREATE INDEX idx_entries_confidence ON knowledge_entries(confidence);
CREATE INDEX idx_entries_scope ON knowledge_entries(scope);
CREATE INDEX idx_entries_created ON knowledge_entries(created);
CREATE INDEX idx_entries_updated ON knowledge_entries(updated);
CREATE INDEX idx_entries_hash ON knowledge_entries(content_hash);
CREATE INDEX idx_entries_source_rating ON knowledge_entries(source_rating);
CREATE INDEX idx_entries_embedding_status ON knowledge_entries(embedding_status);

CREATE INDEX idx_tags_tag ON knowledge_tags(tag);

CREATE INDEX idx_version_entry ON version_history(entry_id, version);

CREATE INDEX idx_dedup_new ON dedup_log(new_entry_id);
CREATE INDEX idx_dedup_existing ON dedup_log(existing_entry_id);
CREATE INDEX idx_dedup_similarity ON dedup_log(similarity_score);
```

### 18.3 表职责说明

| 表名 | 职责 | 关键特性 |
|------|------|---------|
| `knowledge_entries` | 知识条目主表，存储完整条目数据 | 乐观锁字段 `_version`，支持级联删除 |
| `knowledge_tags` | 标签规范化表，拆分tags为独立行 | UNIQUE约束防止重复标签，支持高效标签检索 |
| `version_history` | 版本变更历史，记录每次变更快照 | `snapshot`字段存储变更前完整JSON快照 |
| `dedup_log` | 去重决策日志，审计去重行为 | 记录相似度分数和采取的动作 |
| `knowledge_fts` | FTS5全文检索虚拟表 | Unicode分词，支持中英文混合检索 |
| `schema_version` | 数据库Schema版本管理 | 支持增量迁移，记录每次DDL变更 |

---

## 19. 混合检索引擎

### 19.1 RRF融合算法

混合检索引擎采用Reciprocal Rank Fusion (RRF)算法融合语义检索和关键词检索结果：

```
score(d) = w_semantic × (1 / (k + rank_semantic(d))) + w_keyword × (1 / (k + rank_keyword(d)))
```

**默认参数**：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `w_semantic` | 0.7 | 语义检索权重 |
| `w_keyword` | 0.3 | 关键词检索权重 |
| `k` | 60 | RRF平滑常数，防止排名靠前的结果权重过大 |

**融合流程**：

```
查询请求
    │
    ├─→ Chroma语义检索 → Top-K语义排名列表 (rank_semantic)
    │
    ├─→ SQLite FTS5关键词检索 → Top-K关键词排名列表 (rank_keyword)
    │
    └─→ RRF融合计算
            │
            ├─ 对每个文档d计算: score(d) = 0.7/(60+rank_sem) + 0.3/(60+rank_kw)
            │
            ├─ 按融合分数降序排列
            │
            └─ 返回Top-N结果
```

### 19.2 检索策略配置

| 检索模式 | 语义权重 | 关键词权重 | Top-K | 相似度阈值 | 适用场景 |
|----------|---------|-----------|-------|-----------|---------|
| `hybrid` (默认) | 0.7 | 0.3 | 10 | 0.5 | 综合知识查询 |
| `semantic` | 1.0 | 0.0 | 10 | 0.7 | 概念性查询、模糊描述 |
| `keyword` | 0.0 | 1.0 | 10 | - | 精确术语查找 |
| `context` | 0.5 | 0.5 | 15 | 0.5 | 任务驱动检索 |
| `precise` | 0.3 | 0.7 | 5 | 0.8 | 高精度需求场景 |

### 19.3 上下文感知检索

基于任务类型和Agent角色的智能检索，自动调整检索参数和范围：

**任务类型映射**：

| 任务类型 | 推荐检索模式 | 置信度阈值 | 优先知识库 | 关键词权重提升 |
|----------|-------------|-----------|-----------|--------------|
| `bug_fix` | `hybrid` | 0.6 | 经验→工作→通用 | +0.1 |
| `feature` | `semantic` | 0.5 | 工作→通用→经验 | - |
| `refactor` | `context` | 0.6 | 工作→经验→通用 | +0.05 |
| `review` | `keyword` | 0.7 | 通用→经验→工作 | +0.2 |
| `deploy` | `precise` | 0.8 | 经验→通用→工作 | +0.15 |
| `security` | `precise` | 0.8 | 通用→经验→工作 | +0.2 |

**Agent角色感知**：

```
上下文感知检索流程:
  Agent请求 → 解析Agent角色 + 任务类型
      → 查询检索策略映射表
      → 确定检索模式、权重、阈值、优先知识库
      → 执行混合检索
      → 结果按上下文相关性重排序
      → 返回
```

---

## 20. REST API接口契约

### 20.1 标准响应信封

所有API响应遵循统一信封格式：

```json
{
  "status": "success|error",
  "data": {},
  "meta": {
    "total": 0,
    "page": 1,
    "per_page": 20
  },
  "errors": []
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `status` | string | 请求状态：`success` 或 `error` |
| `data` | object/array | 响应数据，错误时为空对象 |
| `meta` | object | 分页元数据，仅列表接口返回 |
| `errors` | array | 错误详情列表，成功时为空数组 |

### 20.2 端点定义

#### 20.2.1 GET /v1/knowledge - 检索知识条目

**请求参数**：

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `type` | string | 否 | - | 按类型筛选 |
| `category` | string | 否 | - | 按分类筛选 |
| `tags` | string | 否 | - | 按标签筛选，逗号分隔 |
| `scope` | string | 否 | - | 按作用域筛选: global/project |
| `project` | string | 否 | - | 按项目筛选 |
| `status` | string | 否 | active | 按状态筛选 |
| `confidence_min` | float | 否 | 0.0 | 最低置信度阈值 |
| `page` | int | 否 | 1 | 页码 |
| `per_page` | int | 否 | 20 | 每页条数（最大100） |

**响应格式**：

```json
{
  "status": "success",
  "data": [
    {
      "id": "gkb-design-pattern-observer-001",
      "type": "design_pattern",
      "category": "设计模式",
      "title": "观察者模式",
      "tags": ["观察者模式", "发布订阅"],
      "version": "1.2.0",
      "confidence": 0.95,
      "scope": "global",
      "status": "active",
      "created": "2025-01-15T10:00:00Z",
      "updated": "2026-03-20T14:30:00Z"
    }
  ],
  "meta": {
    "total": 42,
    "page": 1,
    "per_page": 20
  },
  "errors": []
}
```

**错误码**：`400`（参数无效）、`500`（服务内部错误）

#### 20.2.2 GET /v1/knowledge/{entry_id} - 获取单个条目

**路径参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| `entry_id` | string | 知识条目唯一标识 |

**响应格式**：

```json
{
  "status": "success",
  "data": {
    "id": "gkb-design-pattern-observer-001",
    "type": "design_pattern",
    "category": "设计模式",
    "title": "观察者模式",
    "content": "定义对象间一对多的依赖关系...",
    "tags": ["观察者模式", "发布订阅"],
    "version": "1.2.0",
    "confidence": 0.95,
    "project": null,
    "scope": "global",
    "status": "active",
    "source": "GoF Design Patterns",
    "source_rating": 5,
    "file_path": "general/patterns/observer-pattern.md",
    "created": "2025-01-15T10:00:00Z",
    "updated": "2026-03-20T14:30:00Z",
    "_version": 3,
    "_last_modified": "2026-03-20T14:30:00Z",
    "_last_modified_by": "specification-keeper"
  },
  "meta": {},
  "errors": []
}
```

**错误码**：`404`（条目不存在）、`500`（服务内部错误）

#### 20.2.3 POST /v1/knowledge - 创建知识条目

**请求体**：

```json
{
  "id": "ekb-bugfix-new-001",
  "type": "bug_fix",
  "category": "错误解决方案",
  "title": "新Bug修复方案",
  "content": "修复方案详细内容...",
  "tags": ["Bug", "修复"],
  "source": "auto_precipitation",
  "source_rating": 3,
  "project": "my-project",
  "scope": "project",
  "confidence": 0.70
}
```

**响应格式**：

```json
{
  "status": "success",
  "data": {
    "id": "ekb-bugfix-new-001",
    "type": "bug_fix",
    "category": "错误解决方案",
    "title": "新Bug修复方案",
    "version": "1.0.0",
    "confidence": 0.70,
    "status": "active",
    "created": "2026-05-01T10:00:00Z",
    "updated": "2026-05-01T10:00:00Z",
    "_version": 1,
    "_last_modified": "2026-05-01T10:00:00Z",
    "_last_modified_by": "backend-developer"
  },
  "meta": {},
  "errors": []
}
```

**错误码**：`400`（请求体无效）、`409`（ID已存在）、`422`（字段校验失败）、`500`（服务内部错误）

#### 20.2.4 PUT /v1/knowledge/{entry_id} - 更新知识条目

**路径参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| `entry_id` | string | 知识条目唯一标识 |

**请求体**：

```json
{
  "title": "更新后的标题",
  "content": "更新后的内容...",
  "tags": ["Bug", "修复", "更新"],
  "confidence": 0.80,
  "_version": 1
}
```

**响应格式**：

```json
{
  "status": "success",
  "data": {
    "id": "ekb-bugfix-new-001",
    "version": "1.1.0",
    "_version": 2,
    "_last_modified": "2026-05-01T11:00:00Z",
    "_last_modified_by": "backend-developer"
  },
  "meta": {},
  "errors": []
}
```

**错误码**：`400`（请求体无效）、`404`（条目不存在）、`409`（版本冲突）、`422`（字段校验失败）、`500`（服务内部错误）

#### 20.2.5 DELETE /v1/knowledge/{entry_id} - 删除知识条目

**路径参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| `entry_id` | string | 知识条目唯一标识 |

**响应格式**：

```json
{
  "status": "success",
  "data": {
    "id": "ekb-bugfix-new-001",
    "deleted": true
  },
  "meta": {},
  "errors": []
}
```

**错误码**：`404`（条目不存在）、`500`（服务内部错误）

#### 20.2.6 POST /v1/knowledge/search - 混合检索

**请求体**：

```json
{
  "query": "观察者模式事件驱动",
  "mode": "hybrid",
  "w_semantic": 0.6,
  "w_keyword": 0.4,
  "top_k": 10,
  "similarity_threshold": 0.5,
  "filters": {
    "type": "design_pattern",
    "scope": "global",
    "confidence_min": 0.7
  },
  "context": {
    "task_type": "feature",
    "agent_role": "backend-developer"
  }
}
```

**响应格式**：

```json
{
  "status": "success",
  "data": [
    {
      "id": "gkb-design-pattern-observer-001",
      "title": "观察者模式",
      "content": "定义对象间一对多的依赖关系...",
      "category": "设计模式",
      "tags": ["观察者模式", "发布订阅"],
      "confidence": 0.95,
      "score": 0.0321,
      "rank_semantic": 1,
      "rank_keyword": 2
    }
  ],
  "meta": {
    "total": 5,
    "page": 1,
    "per_page": 10
  },
  "errors": []
}
```

**错误码**：`400`（查询参数无效）、`500`（服务内部错误）

#### 20.2.7 GET /v1/knowledge/{entry_id}/versions - 获取版本历史

**路径参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| `entry_id` | string | 知识条目唯一标识 |

**查询参数**：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `page` | int | 1 | 页码 |
| `per_page` | int | 20 | 每页条数 |

**响应格式**：

```json
{
  "status": "success",
  "data": [
    {
      "id": 42,
      "entry_id": "gkb-design-pattern-observer-001",
      "version": "1.2.0",
      "change_type": "update",
      "change_description": "补充异步通知注意事项",
      "changed_by": "specification-keeper",
      "changed_at": "2026-03-20T14:30:00Z"
    }
  ],
  "meta": {
    "total": 3,
    "page": 1,
    "per_page": 20
  },
  "errors": []
}
```

**错误码**：`404`（条目不存在）、`500`（服务内部错误）

#### 20.2.8 GET /v1/health - 健康检查

**响应格式**：

```json
{
  "status": "success",
  "data": {
    "service": "knowledge-db-service",
    "version": "1.8.0",
    "uptime_seconds": 86400,
    "components": {
      "sqlite": "healthy",
      "chroma": "healthy",
      "fts_index": "healthy"
    },
    "stats": {
      "total_entries": 1250,
      "active_entries": 1180,
      "index_size_mb": 45.2
    }
  },
  "meta": {},
  "errors": []
}
```

**错误码**：`503`（服务不可用，组件异常）

---

## 21. MCP Tool接口契约

### 21.1 knowledge_search - 知识检索

| 属性 | 值 |
|------|-----|
| **name** | `knowledge_search` |
| **description** | 混合检索知识库，支持语义检索、关键词检索和上下文感知检索，返回按RRF融合排序的知识条目列表 |

**inputSchema**：

```json
{
  "type": "object",
  "properties": {
    "query": {
      "type": "string",
      "description": "检索查询文本"
    },
    "mode": {
      "type": "string",
      "enum": ["hybrid", "semantic", "keyword", "context", "precise"],
      "default": "hybrid",
      "description": "检索模式"
    },
    "top_k": {
      "type": "integer",
      "default": 10,
      "description": "返回结果数量"
    },
    "similarity_threshold": {
      "type": "number",
      "default": 0.5,
      "description": "语义相似度阈值"
    },
    "filters": {
      "type": "object",
      "properties": {
        "type": { "type": "string" },
        "category": { "type": "string" },
        "tags": { "type": "array", "items": { "type": "string" } },
        "scope": { "type": "string" },
        "project": { "type": "string" },
        "confidence_min": { "type": "number" }
      },
      "description": "筛选条件"
    },
    "context": {
      "type": "object",
      "properties": {
        "task_type": { "type": "string" },
        "agent_role": { "type": "string" }
      },
      "description": "上下文信息，用于上下文感知检索"
    }
  },
  "required": ["query"]
}
```

**outputFormat**：

```json
{
  "results": [
    {
      "id": "string",
      "title": "string",
      "content": "string",
      "category": "string",
      "tags": ["string"],
      "confidence": 0.95,
      "score": 0.0321,
      "source": "string"
    }
  ],
  "total": 5,
  "mode": "hybrid"
}
```

### 21.2 knowledge_rollback - 回滚知识条目

| 属性 | 值 |
|------|-----|
| **name** | `knowledge_rollback` |
| **description** | 将知识条目回滚至指定版本，从version_history中恢复目标版本的内容快照，自动递增版本号并记录回滚历史 |

**inputSchema**：

```json
{
  "type": "object",
  "properties": {
    "id": {
      "type": "string",
      "description": "知识条目唯一标识"
    },
    "target_version": {
      "type": "integer",
      "description": "目标版本号，回滚到该版本的内容快照"
    }
  },
  "required": ["id", "target_version"]
}
```

**outputFormat**：

```json
{
  "id": "string",
  "title": "string",
  "content": "string",
  "scope": "general|workspace|experience",
  "tags": ["string"],
  "confidence": 0.6,
  "source_path": "string",
  "source_rating": 3,
  "occurrences": 1,
  "content_hash": "string",
  "version": 3,
  "rollback_from_version": 2,
  "created_at": "ISO8601",
  "updated_at": "ISO8601"
}
```

### 21.3 knowledge_add - 添加知识条目

| 属性 | 值 |
|------|-----|
| **name** | `knowledge_add` |
| **description** | 创建新的知识条目，自动执行去重检查、向量嵌入计算、FTS索引更新，支持自动沉淀和手动创建两种模式 |

**inputSchema**：

```json
{
  "type": "object",
  "properties": {
    "id": {
      "type": "string",
      "description": "知识条目唯一标识，格式：{kb_prefix}-{category}-{name}-{seq}"
    },
    "type": {
      "type": "string",
      "description": "知识类型枚举值"
    },
    "category": {
      "type": "string",
      "description": "所属分类"
    },
    "title": {
      "type": "string",
      "description": "知识条目标题"
    },
    "content": {
      "type": "string",
      "description": "知识条目内容（Markdown格式）"
    },
    "tags": {
      "type": "array",
      "items": { "type": "string" },
      "default": [],
      "description": "标签列表"
    },
    "source": {
      "type": "string",
      "default": "manual",
      "description": "知识来源"
    },
    "source_rating": {
      "type": "integer",
      "default": 3,
      "minimum": 1,
      "maximum": 5,
      "description": "信源权威性评级"
    },
    "project": {
      "type": "string",
      "description": "关联项目（工作/经验知识库必填）"
    },
    "scope": {
      "type": "string",
      "enum": ["global", "project"],
      "default": "global",
      "description": "作用域"
    },
    "confidence": {
      "type": "number",
      "default": 0.5,
      "minimum": 0.0,
      "maximum": 1.0,
      "description": "初始置信度"
    }
  },
  "required": ["id", "type", "category", "title", "content"]
}
```

**outputFormat**：

```json
{
  "id": "string",
  "version": "1.0.0",
  "status": "active",
  "created": "ISO8601",
  "dedup_check": {
    "is_duplicate": false,
    "similar_entries": []
  }
}
```

### 21.4 knowledge_update - 更新知识条目

| 属性 | 值 |
|------|-----|
| **name** | `knowledge_update` |
| **description** | 更新现有知识条目，支持乐观锁冲突检测，自动记录版本历史和更新向量索引 |

**inputSchema**：

```json
{
  "type": "object",
  "properties": {
    "entry_id": {
      "type": "string",
      "description": "知识条目唯一标识"
    },
    "updates": {
      "type": "object",
      "properties": {
        "title": { "type": "string" },
        "content": { "type": "string" },
        "tags": { "type": "array", "items": { "type": "string" } },
        "confidence": { "type": "number" },
        "category": { "type": "string" },
        "status": { "type": "string" },
        "source_rating": { "type": "integer" }
      },
      "description": "需要更新的字段"
    },
    "change_description": {
      "type": "string",
      "description": "变更说明，记录到版本历史"
    },
    "_version": {
      "type": "integer",
      "description": "当前版本号，用于乐观锁冲突检测"
    }
  },
  "required": ["entry_id", "updates", "_version"]
}
```

**outputFormat**：

```json
{
  "id": "string",
  "version": "1.1.0",
  "_version": 2,
  "_last_modified": "ISO8601",
  "_last_modified_by": "string",
  "conflict": null
}
```

**冲突响应**：

```json
{
  "id": "string",
  "conflict": {
    "type": "version_mismatch",
    "current_version": 3,
    "provided_version": 2,
    "resolution_options": ["force_overwrite", "merge", "abort"]
  }
}
```

### 21.5 knowledge_delete - 删除知识条目

| 属性 | 值 |
|------|-----|
| **name** | `knowledge_delete` |
| **description** | 删除知识条目，级联删除关联标签、版本历史快照保留，同步清理FTS索引和Chroma向量 |

**inputSchema**：

```json
{
  "type": "object",
  "properties": {
    "entry_id": {
      "type": "string",
      "description": "知识条目唯一标识"
    },
    "reason": {
      "type": "string",
      "description": "删除原因，记录到变更日志"
    },
    "archive_first": {
      "type": "boolean",
      "default": true,
      "description": "是否先归档再删除（推荐）"
    }
  },
  "required": ["entry_id"]
}
```

**outputFormat**：

```json
{
  "id": "string",
  "deleted": true,
  "archived": true,
  "version_history_preserved": true
}
```

---

## 22. 知识去重与智能更新

### 22.1 双重去重机制

```
新条目写入
    │
    ├─→ 第一层：精确去重（ID匹配）
    │       │
    │       ├─ ID完全匹配 → 拒绝创建，返回已有条目信息
    │       └─ ID不匹配 → 进入第二层
    │
    └─→ 第二层：语义去重（余弦相似度）
            │
            ├─ 相似度 > 0.85 → 触发合并流程
            ├─ 0.70 < 相似度 ≤ 0.85 → 标记为"相关条目"，建立交叉引用
            └─ 相似度 ≤ 0.70 → 允许独立创建
```

| 去重层级 | 方法 | 阈值 | 动作 |
|----------|------|------|------|
| 精确去重 | ID字符串匹配 | 完全相等 | 拒绝创建，返回409 |
| 语义去重 | Chroma余弦相似度 | > 0.85 | 触发合并流程 |
| 相关检测 | Chroma余弦相似度 | 0.70 ~ 0.85 | 建立交叉引用 |
| 独立条目 | Chroma余弦相似度 | ≤ 0.70 | 允许独立创建 |

### 22.2 合并策略

当语义去重触发合并时，根据置信度差异选择合并策略：

| 场景 | 条件 | 策略 | 处理方式 |
|------|------|------|---------|
| 高置信度保留 | 置信度差异 > 0.2 | 保留高置信度条目 | 低置信度条目的独特内容合并为补充段落，原条目标记为`merged` |
| 加权平均合并 | 置信度差异 ≤ 0.2 | 合并为新条目 | 置信度取加权平均，内容取并集，版本号递增 |
| 细化条目保留 | 一个条目是另一个的细化 | 保留细化条目 | 建立`refines`交叉引用，通用条目保留为父条目 |

**合并后处理**：

- 更新所有引用旧条目的交叉引用指向合并后条目
- 在`dedup_log`表记录合并决策和相似度分数
- 保留合并历史，合并后条目的`merge_history`字段记录来源
- 同步更新FTS索引和Chroma向量

### 22.3 版本追踪

`version_history`表记录完整变更历史，支持回溯和审计：

| 字段 | 说明 |
|------|------|
| `entry_id` | 关联的知识条目ID |
| `version` | 变更后的语义化版本号 |
| `change_type` | 变更类型：`create`/`update`/`merge`/`archive`/`restore` |
| `change_description` | 变更描述 |
| `changed_by` | 变更发起者（Agent名称或用户） |
| `changed_at` | 变更时间（ISO 8601） |
| `snapshot` | 变更前的完整条目JSON快照，用于回滚 |

**版本追踪流程**：

```
条目变更请求
    → 读取当前条目快照
    → 写入version_history (snapshot=当前快照)
    → 执行变更
    → 递增_version
    → 更新_last_modified和_last_modified_by
    → 返回变更结果
```

---

## 23. 服务管理要点

### 23.1 启动流程

```
服务启动
    │
    ├─→ 1. 环境检测
    │       检查Python版本 ≥ 3.10
    │       检查依赖包完整性
    │       检查端口8900可用性
    │
    ├─→ 2. 数据库初始化
    │       检查knowledge.db是否存在
    │       不存在 → 执行DDL创建表和索引
    │       已存在 → 检查schema_version，执行增量迁移
    │
    ├─→ 3. Chroma连接
    │       初始化Chroma Client
    │       检查/创建knowledge Collection
    │       验证向量维度一致性
    │
    ├─→ 4. 索引加载
    │       加载FTS5索引
    │       验证索引与数据一致性
    │       不一致 → 触发索引重建
    │
    ├─→ 5. 健康检查
    │       SQLite读写测试
    │       Chroma读写测试
    │       FTS5检索测试
    │
    └─→ 6. 就绪
            启动FastAPI服务
            启动WebSocket Hub
            注册MCP Tools
            输出就绪日志
```

### 23.2 备份策略

备份策略遵循第8章已定义的灾难恢复策略，服务层额外保障：

| 保障项 | 说明 |
|--------|------|
| SQLite文件备份 | 在完整备份和增量备份中包含`knowledge.db`文件 |
| Chroma数据备份 | Chroma Collection数据目录纳入备份范围 |
| 备份前检查 | 执行`PRAGMA integrity_check`确保SQLite文件一致性 |
| WAL检查点 | 备份前执行`PRAGMA wal_checkpoint(TRUNCATE)`刷新WAL日志 |

### 23.3 并发控制

| 机制 | 说明 |
|------|------|
| **SQLite WAL模式** | 启用Write-Ahead Logging，允许读写并发，读操作不阻塞写操作 |
| **写入队列** | 所有写操作通过异步队列串行化执行，避免并发写入冲突 |
| **乐观锁** | 基于`_version`字段检测冲突，写入时校验版本号，冲突时返回错误而非阻塞等待 |

```sql
PRAGMA journal_mode=WAL;
PRAGMA wal_autocheckpoint=1000;
PRAGMA busy_timeout=5000;
```

**写入队列处理流程**：

```
写请求 → 入队列 → 异步串行执行
    │
    ├─ 成功 → 返回结果 + WebSocket通知
    └─ 冲突 → 返回冲突信息（含当前版本号和解决选项）
```

### 23.4 优雅关闭

```
收到关闭信号 (SIGTERM/SIGINT)
    │
    ├─→ 1. 停止接收新请求
    │       设置健康检查为unhealthy
    │       负载均衡器摘除节点
    │
    ├─→ 2. 完成进行中请求
    │       等待所有进行中的请求完成（超时30秒）
    │       写入队列排空
    │
    ├─→ 3. 刷新WAL
    │       执行 PRAGMA wal_checkpoint(TRUNCATE)
    │       确保所有WAL日志写入主数据库文件
    │
    ├─→ 4. 关闭Chroma连接
    │       持久化Collection数据
    │       释放Chroma Client资源
    │
    └─→ 5. 记录状态
            写入关闭时间戳到schema_version表
            输出关闭日志
            退出进程
```

---

> **文档维护说明**：本文档随知识库架构演进同步更新。任何架构变更需经Specification Keeper审核后更新本文档，并递增版本号。

---

## 8. 主动学习机制

### 8.1 外部知识摄入
- 支持从外部文档（Markdown、PDF、代码文件）摄入知识
- 摄入流程：文件解析→内容分段→语义嵌入→质量评估→入库
- 信源评级：官方文档(0.9) > 技术博客(0.7) > 社区回答(0.5) > 个人笔记(0.3)

### 8.2 验证沙箱
- 新摄入知识先进入沙箱环境验证
- 验证维度：语法正确性、语义一致性、与现有知识的兼容性
- 验证通过后自动提升置信度，失败则标记为待审核

### 8.3 代码库考古
- 自动扫描项目代码库，提取编码模式、架构决策、性能优化经验
- 提取规则：高频代码模式→模式知识、错误处理模式→防御知识、性能优化→优化知识
- 扫描频率：每次Phase 0（需求分析）时自动触发

### 8.4 社区知识消化
- 从开源项目、技术文章中提取通用最佳实践
- 消化流程：信息采集→去噪→结构化→验证→入库
- 置信度初始值：0.5，经过项目验证后逐步提升

---

## 9. 知识生命周期管理

### 9.1 置信度动态调整
- 初始置信度：根据知识来源确定（见8.1信源评级）
- 提升条件：知识被成功应用于3个以上项目，每次+0.1
- 降低条件：知识导致错误或质量门禁失败，每次-0.2
- 归档阈值：置信度<0.2，标记为archived

### 9.2 知识去重与合并
- 双重去重机制：
  1. 余弦相似度>0.92：语义高度相似
  2. 元数据哈希匹配：来源和结构相同
- 合并策略：保留置信度更高的版本，合并互补信息
- 版本追踪：每次合并创建新版本，保留历史版本

### 9.3 定期归档
- 归档频率：每月1次
- 归档条件：置信度<0.2 或 超过90天未被引用
- 归档操作：移动到.knowledge/archive/目录，不删除
- 恢复机制：通过knowledge-server的restore端点恢复

---

## 10. 跨项目知识泛化

### 10.1 泛化筛选
- 筛选条件：置信度>0.7 且 被至少2个项目引用
- 排除条件：项目特定配置、硬编码路径、环境变量
- 泛化标记：添加 generalized=true 标签

### 10.2 技术栈适配校验
- 校验流程：读取目标项目技术栈→匹配知识标签→标记兼容/不兼容
- 兼容性等级：完全兼容(1.0) > 部分兼容(0.6) > 需适配(0.3) > 不兼容(0)
- 适配建议：对"需适配"等级的知识生成修改建议

### 10.3 迁移学习标记
- 标记维度：源项目、目标项目、迁移时间、适配修改、验证结果
- 迁移成功率追踪：记录每次迁移的成功/失败，用于调整置信度

---

## 11. 知识去重与智能更新

### 11.1 双重去重机制
- 第一层：余弦相似度>0.92 → 语义高度相似，触发合并评估
- 第二层：元数据哈希匹配 → 来源和结构相同，自动合并
- 去重范围：同类别知识（general/experience/workspace）

### 11.2 合并策略
- 保留策略：保留置信度更高的版本作为主版本
- 互补合并：将低置信度版本中的独有信息合并到主版本
- 冲突处理：内容冲突时保留两个版本，标记为待人工审核

### 11.3 版本追踪
- 版本号格式：v{major}.{minor}（合并+1 major，修改+1 minor）
- 版本历史：存储在version_history表中
- 回滚支持：通过knowledge_rollback端点恢复到任意历史版本

## 知识生命周期管理自动化

### 置信度动态调整

每条知识条目包含以下置信度相关字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| confidence | FLOAT | 当前置信度（0.0-1.0），初始值0.6 |
| last_validated | DATETIME | 最后验证时间 |
| success_count | INTEGER | 被成功引用的次数 |
| failure_count | INTEGER | 被引用但未解决问题的次数 |

#### 调整规则

1. **成功引用**：confidence += 0.02（上限1.0），success_count += 1
2. **失败引用**：confidence -= 0.05，failure_count += 1
3. **定期验证**：每30天自动验证，confidence -= 0.01（未验证衰减）
4. **待审查标记**：confidence < 0.3 时标记为"待审查"，需人工确认
5. **自动删除**：confidence < 0.1 且 failure_count > 5 时自动删除

### 知识去重与合并

#### 去重检测
- 新条目写入前，计算与现有条目的余弦相似度
- 使用ChromaDB的向量检索功能，相似度阈值0.85

#### 合并规则
- 余弦相似度 > 0.85 时触发自动合并
- 保留更高置信度的条目作为主条目
- 合并内容：取两个条目的并集，冲突字段保留主条目的值
- 合并后confidence = max(conf_a, conf_b) + 0.01
- 合并事件记录至知识库的merge_log

### 定期归档

#### 归档条件
- 90天未被引用（last_validated > 90天前）
- 且置信度 < 0.5

#### 归档动作
1. 将条目从活跃表移动到archive/目录
2. 保留条目的完整内容和元数据
3. 在原位置保留索引指针（指向归档位置）
4. 归档事件记录至知识库的archive_log

#### 归档恢复
- 被引用时自动检测归档状态
- 若归档条目被成功引用，自动恢复到活跃表
- 恢复后confidence重置为0.5
