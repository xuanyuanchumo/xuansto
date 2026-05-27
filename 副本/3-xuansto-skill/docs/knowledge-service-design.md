# 知识库服务层技术设计文档

> 版本: 2.0.0 | 更新日期: 2026-05-03 | 编码: UTF-8 | 行尾: LF
>
> 本文档为 xuansto-skill 需求文档 7.4-7.9 节引用的知识库服务层技术设计文档，定义双引擎架构、SQL Schema、MCP Tool 接口、错误处理、认证规范、WebSocket 推送、并发控制、备份灾备、配置文件及测试用例的完整技术方案。

---

## 目录

1. [概述](#1-概述)
2. [SQL Schema 设计](#2-sql-schema-设计)
3. [API 接口设计](#3-api-接口设计)
4. [错误处理与重试策略](#4-错误处理与重试策略)
5. [认证规范](#5-认证规范)
6. [WebSocket 接口](#6-websocket-接口)
7. [并发控制](#7-并发控制)
8. [备份灾备](#8-备份灾备)
9. [配置文件](#9-配置文件)
10. [测试用例](#10-测试用例)

---

## 1. 概述

### 1.1 架构定位

知识库服务层作为 xuansto-skill v1.8.0 新增的核心基础设施，将原有的纯文件存储模式升级为服务化架构，提供统一的数据访问接口和混合检索能力。服务层位于三层知识库（通用/工作/经验）与消费方（Agent、外部工具、CI/CD）之间，屏蔽底层存储细节，对外暴露标准化接口。

### 1.2 双引擎架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                     知识库数据库服务层架构                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────────┐    │
│  │  FastAPI HTTP   │  │  MCP Tool       │  │  WebSocket       │    │
│  │  REST API       │  │  Interface      │  │  实时通知         │    │
│  │  :8765/v1/*    │  │  knowledge_*    │  │  /ws/notify      │    │
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

| 引擎 | 职责 | 存储格式 | 检索能力 |
|------|------|---------|---------|
| **SQLite 结构化存储** | 知识条目 CRUD、元数据管理、全文检索、版本追踪 | `knowledge.db` (WAL 模式) | FTS5 全文搜索、结构化查询、事务支持 |
| **Chroma 向量语义检索** | 语义相似度检索、向量嵌入管理 | Chroma Collection | 余弦相似度、语义匹配、模糊概念检索 |

**双引擎协同**：写入时同步更新 SQLite 和 Chroma，读取时通过混合检索引擎融合两路结果。

### 1.3 三大接口通道

| 通道 | 协议 | 用途 | 消费者 |
|------|------|------|--------|
| FastAPI HTTP REST | HTTP/1.1 | 标准 CRUD 操作、混合检索、健康检查 | 外部工具、CI/CD、管理界面 |
| MCP Tool Interface | MCP Protocol (stdio) | Agent 直接调用知识检索与写入 | Xuansto 多 Agent 系统 |
| WebSocket 实时通知 | WebSocket | 知识变更推送、冲突预警 | 订阅 Agent、监控面板 |

### 1.4 数据流全景

**写入流**：

```
Agent → MCP Tool / REST API → 服务编排层
    → SQLite (结构化存储 + FTS 索引更新)
    → Chroma (向量嵌入计算 + Collection 更新)
    → WebSocket (变更通知 → 订阅 Agent)
```

**读取流**：

```
查询请求 → 服务编排层 → 混合检索引擎
    → SQLite FTS5 (关键词检索 → 排名列表)
    → Chroma (语义检索 → 排名列表)
    → RRF 融合 → 排序结果 → 返回
```

**通知流**：

```
知识变更 → WebSocket Hub
    → 推送变更事件 (create/update/delete)
    → 订阅 Agent 接收通知
    → 触发上下文更新或冲突检测
```

### 1.5 服务启动流程

```
服务启动
    │
    ├─→ 1. 环境检测
    │       检查 Python 版本 ≥ 3.10
    │       检查依赖包完整性 (fastapi, chromadb, openai, uvicorn)
    │       检查端口 8765 可用性
    │
    ├─→ 2. 数据库初始化
    │       检查 knowledge.db 是否存在
    │       不存在 → 执行 DDL 创建表和索引
    │       已存在 → 检查 schema_version，执行增量迁移
    │
    ├─→ 3. Chroma 连接
    │       初始化 Chroma Client
    │       检查/创建 knowledge Collection
    │       验证向量维度一致性 (默认 1536 维)
    │
    ├─→ 4. 索引加载
    │       加载 FTS5 索引
    │       验证索引与数据一致性
    │       不一致 → 触发索引重建
    │
    ├─→ 5. 健康检查
    │       SQLite 读写测试
    │       Chroma 读写测试
    │       FTS5 检索测试
    │
    └─→ 6. 就绪
            启动 FastAPI 服务
            启动 WebSocket Hub
            注册 MCP Tools
            输出就绪日志
```

### 1.6 服务关闭流程

```
收到关闭信号 (SIGTERM/SIGINT)
    │
    ├─→ 1. 停止接收新请求
    │       设置健康检查为 unhealthy
    │       负载均衡器摘除节点
    │
    ├─→ 2. 完成进行中请求
    │       等待所有进行中的请求完成（超时 30 秒）
    │       写入队列排空
    │
    ├─→ 3. 刷新 WAL
    │       执行 PRAGMA wal_checkpoint(TRUNCATE)
    │       确保所有 WAL 日志写入主数据库文件
    │
    ├─→ 4. 关闭 Chroma 连接
    │       持久化 Collection 数据
    │       释放 Chroma Client 资源
    │
    └─→ 5. 记录状态
            写入关闭时间戳到 schema_version 表
            输出关闭日志
            退出进程
```

### 1.7 降级容错

v1.6.0 文件存储模式作为 fallback，服务层不可用时自动降级：

| 场景 | 行为 |
|------|------|
| 服务层正常启动 | 所有操作走服务层（SQLite + Chroma） |
| 服务层启动失败 | 自动降级为 v1.6 文件存储模式，日志记录降级事件 |
| 服务层运行中崩溃 | 已有请求返回错误，新请求降级为文件存储模式 |
| 服务层恢复 | 自动从文件存储模式切回服务层，同步期间变更 |

```
降级检测流程:
  服务启动 → 检测 SQLite/Chroma 可用性
      → 可用 → 正常模式
      → 不可用 → 记录降级日志 → 切换文件存储模式 → 定时重试连接
          → 重连成功 → 同步降级期间变更 → 切回正常模式
```

---

## 2. SQL Schema 设计

### 2.1 schema_version 表

版本追踪表，记录每次 Schema 变更，支持增量迁移。

```sql
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT DEFAULT (datetime('now')),
    description TEXT
);
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `version` | INTEGER | Schema 版本号，主键，单调递增 |
| `applied_at` | TEXT | 迁移应用时间（ISO 8601） |
| `description` | TEXT | 迁移描述说明 |

**迁移机制**：服务启动时读取当前 `MAX(version)`，与代码中 `SCHEMA_VERSION` 常量对比，依次执行缺失版本的迁移脚本。

### 2.2 knowledge_entries 表

知识条目主表，存储完整的知识条目数据。

```sql
CREATE TABLE IF NOT EXISTS knowledge_entries (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    scope TEXT NOT NULL CHECK(scope IN ('general','workspace','experience')),
    tags TEXT DEFAULT '[]',
    confidence REAL DEFAULT 0.6 CHECK(confidence BETWEEN 0 AND 1),
    source_path TEXT,
    source_rating INTEGER DEFAULT 3 CHECK(source_rating BETWEEN 1 AND 5),
    occurrences INTEGER DEFAULT 1,
    content_hash TEXT,
    type TEXT NOT NULL DEFAULT 'unknown',
    category TEXT NOT NULL DEFAULT 'uncategorized',
    summary TEXT,
    content_path TEXT,
    source TEXT,
    last_validated TEXT,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    version INTEGER DEFAULT 1,
    embedding_status TEXT DEFAULT 'pending' CHECK(embedding_status IN ('pending','ready')),
    embedding_retry_count INTEGER DEFAULT 0,
    created TEXT DEFAULT (datetime('now')),
    updated TEXT DEFAULT (datetime('now'))
);
```

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | TEXT | PK | 全局唯一标识，格式：`{kb_prefix}-{category}-{name}-{seq}` |
| `title` | TEXT | NOT NULL | 知识条目标题 |
| `content` | TEXT | NOT NULL | 知识条目内容（Markdown 格式） |
| `scope` | TEXT | NOT NULL, CHECK | 作用域：`general` / `workspace` / `experience` |
| `tags` | TEXT | DEFAULT '[]' | 标签 JSON 数组，如 `["观察者模式","事件驱动"]` |
| `confidence` | REAL | DEFAULT 0.6, CHECK [0,1] | 置信度，动态调整 |
| `source_path` | TEXT | - | 原始文件路径 |
| `source_rating` | INTEGER | DEFAULT 3, CHECK [1,5] | 信源权威性评级 |
| `occurrences` | INTEGER | DEFAULT 1 | 出现次数（去重合并时累加） |
| `content_hash` | TEXT | - | 内容 SHA256 哈希，用于变更检测 |
| `type` | TEXT | NOT NULL, DEFAULT 'unknown' | 知识类型枚举 |
| `category` | TEXT | NOT NULL, DEFAULT 'uncategorized' | 所属分类 |
| `summary` | TEXT | - | 摘要，用于 FTS 索引和向量嵌入 |
| `content_path` | TEXT | - | 内容文件路径（外部 Markdown 文件） |
| `source` | TEXT | - | 知识来源说明 |
| `last_validated` | TEXT | - | 最后验证时间（ISO 8601） |
| `success_count` | INTEGER | DEFAULT 0 | 成功应用次数 |
| `failure_count` | INTEGER | DEFAULT 0 | 失败应用次数 |
| `version` | INTEGER | DEFAULT 1 | 乐观锁版本号 |
| `embedding_status` | TEXT | DEFAULT 'pending', CHECK | 向量嵌入状态：`pending` / `ready` |
| `embedding_retry_count` | INTEGER | DEFAULT 0 | 嵌入计算重试次数 |
| `created` | TEXT | DEFAULT now | 创建时间（ISO 8601） |
| `updated` | TEXT | DEFAULT now | 最后更新时间（ISO 8601） |

### 2.3 knowledge_embeddings 表

向量嵌入表，存储知识条目的向量嵌入数据。当 Chroma 不可用时作为本地向量存储的备选方案。

```sql
CREATE TABLE IF NOT EXISTS knowledge_embeddings (
    entry_id TEXT NOT NULL,
    embedding BLOB NOT NULL,
    model_name TEXT NOT NULL,
    dimension INTEGER NOT NULL,
    chunk_text TEXT,
    chunk_index INTEGER DEFAULT 0,
    created TEXT DEFAULT (datetime('now')),
    PRIMARY KEY (entry_id, model_name, chunk_index),
    FOREIGN KEY (entry_id) REFERENCES knowledge_entries(id) ON DELETE CASCADE
);
```

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `entry_id` | TEXT | FK, NOT NULL | 关联知识条目 ID |
| `embedding` | BLOB | NOT NULL | 向量嵌入二进制数据（float32 序列化） |
| `model_name` | TEXT | NOT NULL | 嵌入模型名称，如 `text-embedding-3-small` |
| `dimension` | INTEGER | NOT NULL | 向量维度，如 1536 |
| `chunk_text` | TEXT | - | 分块文本内容 |
| `chunk_index` | INTEGER | DEFAULT 0 | 分块索引序号 |
| `created` | TEXT | DEFAULT now | 嵌入计算时间 |

### 2.4 knowledge_relations 表

知识关联表，存储知识条目间的语义关联关系。

```sql
CREATE TABLE IF NOT EXISTS knowledge_relations (
    source_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    relation_type TEXT NOT NULL CHECK(relation_type IN (
        'implements', 'complies', 'extends', 'refines', 'contradicts',
        'related_to', 'derived_from', 'generalizes'
    )),
    description TEXT,
    created TEXT DEFAULT (datetime('now')),
    PRIMARY KEY (source_id, target_id, relation_type),
    FOREIGN KEY (source_id) REFERENCES knowledge_entries(id) ON DELETE CASCADE,
    FOREIGN KEY (target_id) REFERENCES knowledge_entries(id) ON DELETE CASCADE
);
```

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `source_id` | TEXT | FK, NOT NULL | 源知识条目 ID |
| `target_id` | TEXT | FK, NOT NULL | 目标知识条目 ID |
| `relation_type` | TEXT | NOT NULL, CHECK | 关系类型枚举 |
| `description` | TEXT | - | 关系描述说明 |
| `created` | TEXT | DEFAULT now | 关系创建时间 |

**关系类型枚举**：

| 类型 | 说明 | 示例 |
|------|------|------|
| `implements` | 实现 | 工作条目实现了通用模式 |
| `complies` | 遵循 | 工作条目遵循通用规范 |
| `extends` | 扩展 | 经验条目扩展了通用知识 |
| `refines` | 细化 | 细化条目是通用条目的具体化 |
| `contradicts` | 矛盾 | 经验条目与通用知识矛盾 |
| `related_to` | 相关 | 通用关联关系 |
| `derived_from` | 派生 | 泛化条目的来源项目条目 |
| `generalizes` | 泛化 | 通用条目由经验条目泛化而来 |

### 2.5 sync_log 表

同步日志表，记录跨分支/跨环境同步操作。

```sql
CREATE TABLE IF NOT EXISTS sync_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sync_type TEXT NOT NULL CHECK(sync_type IN ('full', 'incremental', 'branch_merge', 'reconciliation')),
    source_branch TEXT,
    target_branch TEXT,
    entries_synced INTEGER DEFAULT 0,
    entries_conflicted INTEGER DEFAULT 0,
    entries_skipped INTEGER DEFAULT 0,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    status TEXT DEFAULT 'in_progress' CHECK(status IN ('in_progress', 'completed', 'failed', 'rolled_back')),
    error_message TEXT,
    details TEXT
);
```

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | INTEGER | PK, AUTO | 自增主键 |
| `sync_type` | TEXT | NOT NULL, CHECK | 同步类型 |
| `source_branch` | TEXT | - | 源分支名称 |
| `target_branch` | TEXT | - | 目标分支名称 |
| `entries_synced` | INTEGER | DEFAULT 0 | 成功同步条目数 |
| `entries_conflicted` | INTEGER | DEFAULT 0 | 冲突条目数 |
| `entries_skipped` | INTEGER | DEFAULT 0 | 跳过条目数 |
| `started_at` | TEXT | NOT NULL | 同步开始时间 |
| `completed_at` | TEXT | - | 同步完成时间 |
| `status` | TEXT | DEFAULT 'in_progress', CHECK | 同步状态 |
| `error_message` | TEXT | - | 错误信息 |
| `details` | TEXT | - | 详细信息（JSON 格式） |

### 2.6 辅助表

#### knowledge_tags 表

标签规范化表，拆分 tags 为独立行，支持高效标签检索。

```sql
CREATE TABLE IF NOT EXISTS knowledge_tags (
    entry_id TEXT NOT NULL,
    tag TEXT NOT NULL,
    PRIMARY KEY (entry_id, tag),
    FOREIGN KEY (entry_id) REFERENCES knowledge_entries(id) ON DELETE CASCADE
);
```

#### version_history 表

版本变更历史表，记录每次变更快照，支持回滚。

```sql
CREATE TABLE IF NOT EXISTS version_history (
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
    saved_at TEXT DEFAULT (datetime('now')),
    UNIQUE(entry_id, version),
    FOREIGN KEY (entry_id) REFERENCES knowledge_entries(id) ON DELETE CASCADE
);
```

#### dedup_log 表

去重决策日志表，审计去重行为。

```sql
CREATE TABLE IF NOT EXISTS dedup_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    new_entry_id TEXT NOT NULL,
    existing_entry_id TEXT NOT NULL,
    similarity_score REAL NOT NULL,
    action TEXT NOT NULL CHECK(action IN ('skip', 'merge', 'keep_both')),
    merged_at TEXT,
    FOREIGN KEY (new_entry_id) REFERENCES knowledge_entries(id),
    FOREIGN KEY (existing_entry_id) REFERENCES knowledge_entries(id)
);
```

#### reconciliation_log 表

一致性校验日志表，记录 SQLite 与 Chroma 数据对账结果。

```sql
CREATE TABLE IF NOT EXISTS reconciliation_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    check_time TEXT NOT NULL,
    sqlite_ready_count INTEGER,
    chroma_vector_count INTEGER,
    missing_in_chroma INTEGER DEFAULT 0,
    orphan_in_chroma INTEGER DEFAULT 0,
    fixed_count INTEGER DEFAULT 0,
    details TEXT
);
```

#### usage_logs 表

使用日志表，记录知识条目的检索和使用情况。

```sql
CREATE TABLE IF NOT EXISTS usage_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id TEXT,
    agent_role TEXT,
    query_text TEXT,
    result_count INTEGER DEFAULT 0,
    elapsed_ms REAL DEFAULT 0.0,
    timestamp TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (entry_id) REFERENCES knowledge_entries(id) ON DELETE SET NULL
);
```

#### backup_history 表

备份历史表，记录备份操作。

```sql
CREATE TABLE IF NOT EXISTS backup_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    backup_path TEXT NOT NULL,
    backup_size INTEGER,
    entry_count INTEGER,
    created_at TEXT NOT NULL,
    status TEXT DEFAULT 'completed'
);
```

### 2.7 FTS5 全文检索虚拟表

```sql
CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts USING fts5(
    id UNINDEXED,
    summary,
    type,
    category,
    content='knowledge_entries',
    content_rowid='rowid',
    tokenize='unicode61'
);
```

**FTS 触发器**：自动同步 `knowledge_entries` 表变更到 FTS 索引。

```sql
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
```

### 2.8 索引定义

```sql
CREATE INDEX IF NOT EXISTS idx_entries_scope ON knowledge_entries(scope);
CREATE INDEX IF NOT EXISTS idx_entries_hash ON knowledge_entries(content_hash);
CREATE INDEX IF NOT EXISTS idx_entries_confidence ON knowledge_entries(confidence);
CREATE INDEX IF NOT EXISTS idx_entries_type ON knowledge_entries(type);
CREATE INDEX IF NOT EXISTS idx_entries_category ON knowledge_entries(category);
CREATE INDEX IF NOT EXISTS idx_entries_created ON knowledge_entries(created);
CREATE INDEX IF NOT EXISTS idx_entries_updated ON knowledge_entries(updated);
CREATE INDEX IF NOT EXISTS idx_entries_source_rating ON knowledge_entries(source_rating);
CREATE INDEX IF NOT EXISTS idx_entries_embedding_status ON knowledge_entries(embedding_status);

CREATE INDEX IF NOT EXISTS idx_tags_tag ON knowledge_tags(tag);

CREATE INDEX IF NOT EXISTS idx_version_entry ON version_history(entry_id, version);

CREATE INDEX IF NOT EXISTS idx_dedup_new ON dedup_log(new_entry_id);
CREATE INDEX IF NOT EXISTS idx_dedup_existing ON dedup_log(existing_entry_id);
CREATE INDEX IF NOT EXISTS idx_dedup_similarity ON dedup_log(similarity_score);

CREATE INDEX IF NOT EXISTS idx_relations_source ON knowledge_relations(source_id);
CREATE INDEX IF NOT EXISTS idx_relations_target ON knowledge_relations(target_id);
CREATE INDEX IF NOT EXISTS idx_relations_type ON knowledge_relations(relation_type);

CREATE INDEX IF NOT EXISTS idx_sync_status ON sync_log(status);
CREATE INDEX IF NOT EXISTS idx_sync_started ON sync_log(started_at);

CREATE INDEX IF NOT EXISTS idx_usage_entry ON usage_logs(entry_id);
CREATE INDEX IF NOT EXISTS idx_usage_agent ON usage_logs(agent_role);
CREATE INDEX IF NOT EXISTS idx_usage_timestamp ON usage_logs(timestamp);

CREATE INDEX IF NOT EXISTS idx_embeddings_model ON knowledge_embeddings(model_name);
CREATE INDEX IF NOT EXISTS idx_embeddings_status ON knowledge_entries(embedding_status);
```

### 2.9 外键约束汇总

| 子表 | 外键字段 | 父表 | 父字段 | 删除行为 |
|------|---------|------|--------|---------|
| `knowledge_tags` | `entry_id` | `knowledge_entries` | `id` | CASCADE |
| `knowledge_embeddings` | `entry_id` | `knowledge_entries` | `id` | CASCADE |
| `knowledge_relations` | `source_id` | `knowledge_entries` | `id` | CASCADE |
| `knowledge_relations` | `target_id` | `knowledge_entries` | `id` | CASCADE |
| `version_history` | `entry_id` | `knowledge_entries` | `id` | CASCADE |
| `dedup_log` | `new_entry_id` | `knowledge_entries` | `id` | RESTRICT |
| `dedup_log` | `existing_entry_id` | `knowledge_entries` | `id` | RESTRICT |
| `usage_logs` | `entry_id` | `knowledge_entries` | `id` | SET NULL |

> **注意**：SQLite 默认不启用外键约束，服务启动时须执行 `PRAGMA foreign_keys=ON`。

---

## 3. API 接口设计

### 3.1 MCP Tool 接口总览

MCP Tool 接口供 Agent 通过 MCP 协议（stdio 传输）直接调用知识库功能。

| Tool 名称 | 功能 | 必需参数 |
|-----------|------|---------|
| `knowledge_search` | 混合检索知识库 | `query` |
| `knowledge_add` | 添加知识条目 | `id`, `type`, `category`, `title`, `content` |
| `knowledge_update` | 更新知识条目 | `entry_id`, `updates`, `_version` |
| `knowledge_delete` | 删除知识条目 | `entry_id` |
| `knowledge_sync` | 跨分支同步 | `source_branch`, `target_branch` |

### 3.2 knowledge_search - 混合检索

混合检索知识库，支持语义检索、关键词检索和上下文感知检索，返回按 RRF 融合排序的知识条目列表。

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
      "description": "检索模式：hybrid=混合(默认), semantic=语义, keyword=关键词, context=上下文感知, precise=高精度"
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
        "type": { "type": "string", "description": "按类型筛选" },
        "category": { "type": "string", "description": "按分类筛选" },
        "tags": { "type": "array", "items": { "type": "string" }, "description": "按标签筛选" },
        "scope": { "type": "string", "description": "按作用域筛选: general/workspace/experience" },
        "project": { "type": "string", "description": "按项目筛选" },
        "confidence_min": { "type": "number", "description": "最低置信度阈值" }
      },
      "description": "筛选条件"
    },
    "context": {
      "type": "object",
      "properties": {
        "task_type": { "type": "string", "description": "任务类型: bug_fix/feature/refactor/review/deploy/security" },
        "agent_role": { "type": "string", "description": "Agent角色" }
      },
      "description": "上下文信息，用于上下文感知检索"
    }
  },
  "required": ["query"]
}
```

**请求示例**：

```json
{
  "query": "观察者模式事件驱动",
  "mode": "hybrid",
  "top_k": 5,
  "similarity_threshold": 0.5,
  "filters": {
    "type": "design_pattern",
    "scope": "general",
    "confidence_min": 0.7
  },
  "context": {
    "task_type": "feature",
    "agent_role": "backend-developer"
  }
}
```

**响应示例**：

```json
{
  "results": [
    {
      "id": "gkb-design-pattern-observer-001",
      "title": "观察者模式",
      "content": "定义对象间一对多的依赖关系，当一个对象状态改变时，所有依赖它的对象都会收到通知并自动更新。",
      "category": "设计模式",
      "tags": ["观察者模式", "发布订阅", "事件驱动"],
      "confidence": 0.95,
      "score": 0.0321,
      "rank_semantic": 1,
      "rank_keyword": 2,
      "source": "GoF Design Patterns"
    },
    {
      "id": "gkb-pattern-event-driven-001",
      "title": "事件驱动架构",
      "content": "事件驱动架构通过事件的产生、检测和消费实现组件间解耦...",
      "category": "架构模式",
      "tags": ["事件驱动", "发布订阅", "异步"],
      "confidence": 0.88,
      "score": 0.0287,
      "rank_semantic": 2,
      "rank_keyword": 1,
      "source": "社区实践总结"
    }
  ],
  "total": 2,
  "mode": "hybrid"
}
```

### 3.3 knowledge_add - 添加知识条目

创建新的知识条目，自动执行去重检查、向量嵌入计算、FTS 索引更新。

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
      "enum": ["general", "workspace", "experience"],
      "default": "general",
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

**请求示例**：

```json
{
  "id": "ekb-bugfix-oom-handler-001",
  "type": "bug_fix",
  "category": "错误解决方案",
  "title": "Node.js OOM 处理方案",
  "content": "## 错误现象\n处理大文件时进程因 OOM 被系统终止，错误码 137。\n\n## 根因分析\n1. 文件内容一次性加载到内存\n2. 未使用流式处理\n\n## 解决方案\n1. 使用 stream.Readable 替代 fs.readFileSync\n2. 实现背压控制",
  "tags": ["OOM", "内存泄漏", "Node.js"],
  "source": "auto_precipitation",
  "source_rating": 3,
  "project": "data-pipeline-service",
  "scope": "experience",
  "confidence": 0.70
}
```

**响应示例**：

```json
{
  "id": "ekb-bugfix-oom-handler-001",
  "version": "1.0.0",
  "status": "active",
  "created": "2026-05-03T10:00:00Z",
  "dedup_check": {
    "is_duplicate": false,
    "similar_entries": []
  }
}
```

**去重检测响应示例**（相似度 > 0.85）：

```json
{
  "id": null,
  "status": "duplicate_detected",
  "dedup_check": {
    "is_duplicate": true,
    "similar_entries": [
      {
        "id": "ekb-bugfix-oom-001",
        "similarity_score": 0.92,
        "action": "merge_suggested"
      }
    ]
  }
}
```

### 3.4 knowledge_update - 更新知识条目

更新现有知识条目，支持乐观锁冲突检测，自动记录版本历史和更新向量索引。

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

**请求示例**：

```json
{
  "entry_id": "ekb-bugfix-oom-handler-001",
  "updates": {
    "title": "Node.js OOM 处理方案（已验证）",
    "content": "## 错误现象\n处理大文件时进程因 OOM 被系统终止...\n\n## 解决方案\n1. 使用 stream.Readable 替代 fs.readFileSync\n2. 实现背压控制\n3. 调整 --max-old-space-size 参数",
    "confidence": 0.80,
    "tags": ["OOM", "内存泄漏", "Node.js", "流式处理"]
  },
  "change_description": "补充 --max-old-space-size 参数调整方案，提升置信度",
  "_version": 1
}
```

**响应示例**：

```json
{
  "id": "ekb-bugfix-oom-handler-001",
  "version": "1.1.0",
  "_version": 2,
  "_last_modified": "2026-05-03T11:00:00Z",
  "_last_modified_by": "backend-developer",
  "conflict": null
}
```

**版本冲突响应示例**：

```json
{
  "id": "ekb-bugfix-oom-handler-001",
  "conflict": {
    "type": "version_mismatch",
    "current_version": 3,
    "provided_version": 1,
    "resolution_options": ["force_overwrite", "merge", "abort"]
  }
}
```

### 3.5 knowledge_delete - 删除知识条目

删除知识条目，级联删除关联标签，版本历史快照保留，同步清理 FTS 索引和 Chroma 向量。

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

**请求示例**：

```json
{
  "entry_id": "ekb-bugfix-oom-handler-001",
  "reason": "知识已过时，Node.js 22 已内置流式处理优化",
  "archive_first": true
}
```

**响应示例**：

```json
{
  "id": "ekb-bugfix-oom-handler-001",
  "deleted": true,
  "archived": true,
  "version_history_preserved": true
}
```

### 3.6 knowledge_sync - 跨分支同步

跨分支同步知识条目，支持全量同步和增量同步。

**inputSchema**：

```json
{
  "type": "object",
  "properties": {
    "source_branch": {
      "type": "string",
      "description": "源分支名称"
    },
    "target_branch": {
      "type": "string",
      "description": "目标分支名称"
    },
    "sync_type": {
      "type": "string",
      "enum": ["full", "incremental"],
      "default": "incremental",
      "description": "同步类型：full=全量同步, incremental=增量同步"
    },
    "conflict_resolution": {
      "type": "string",
      "enum": ["source_wins", "target_wins", "higher_confidence", "manual"],
      "default": "higher_confidence",
      "description": "冲突解决策略"
    },
    "dry_run": {
      "type": "boolean",
      "default": false,
      "description": "是否为试运行模式（不实际写入）"
    }
  },
  "required": ["source_branch", "target_branch"]
}
```

**请求示例**：

```json
{
  "source_branch": "kb/experiment/new-patterns",
  "target_branch": "main",
  "sync_type": "incremental",
  "conflict_resolution": "higher_confidence",
  "dry_run": false
}
```

**响应示例**：

```json
{
  "sync_id": 42,
  "source_branch": "kb/experiment/new-patterns",
  "target_branch": "main",
  "sync_type": "incremental",
  "entries_synced": 15,
  "entries_conflicted": 2,
  "entries_skipped": 1,
  "conflicts": [
    {
      "entry_id": "gkb-design-pattern-observer-001",
      "source_confidence": 0.90,
      "target_confidence": 0.95,
      "resolution": "target_wins (higher_confidence)"
    }
  ],
  "started_at": "2026-05-03T10:00:00Z",
  "completed_at": "2026-05-03T10:00:05Z",
  "status": "completed"
}
```

**试运行响应示例**：

```json
{
  "sync_id": null,
  "dry_run": true,
  "source_branch": "kb/experiment/new-patterns",
  "target_branch": "main",
  "entries_to_sync": 15,
  "entries_to_conflict": 2,
  "entries_to_skip": 1,
  "status": "dry_run_completed"
}
```

---

## 4. 错误处理与重试策略

### 4.1 错误码定义

| 错误码 | HTTP 状态码 | 说明 | 处理建议 |
|--------|-----------|------|---------|
| `BAD_REQUEST` | 400 | 请求参数无效 | 检查请求体格式和必填字段 |
| `UNAUTHORIZED` | 401 | 未授权（远程模式需要 API Key） | 提供有效的 X-API-Key 请求头 |
| `NOT_FOUND` | 404 | 知识条目不存在 | 检查 entry_id 是否正确 |
| `DUPLICATE_DETECTED` | 409 | 知识条目重复（相似度 > 阈值） | 使用 knowledge_update 更新已有条目 |
| `VERSION_CONFLICT` | 409 | 版本冲突（乐观锁） | 重新读取最新版本后重试 |
| `VALIDATION_ERROR` | 422 | 字段校验失败 | 检查字段值范围和格式 |
| `RATE_LIMITED` | 429 | 请求频率超限 | 等待 retry_after 秒后重试 |
| `INTERNAL_ERROR` | 500 | 内部服务器错误 | 检查日志，重启知识库服务 |
| `CHROMA_UNAVAILABLE` | 503 | Chroma 向量引擎不可用 | 自动降级为 SQLite + FTS5 |
| `EMBEDDING_FAILED` | 503 | 向量嵌入计算失败 | 排入重试队列，条目标记为 pending |
| `SERVICE_DEGRADED` | 503 | 服务降级（双引擎不可用） | 系统自动降级到 SQLite+FTS5 |

**错误响应格式**：

```json
{
  "status": "error",
  "data": null,
  "meta": {
    "error": {
      "code": "DUPLICATE_DETECTED",
      "message": "知识条目重复",
      "details": {
        "similarity_score": 0.95,
        "existing_id": "kb-20260429-001"
      },
      "retryable": false
    }
  }
}
```

### 4.2 重试策略

#### 指数退避算法

对于可重试错误（`VERSION_CONFLICT`、`RATE_LIMITED`、`EMBEDDING_FAILED`、`CHROMA_UNAVAILABLE`），采用指数退避重试：

```
重试间隔 = base_delay × 2^(attempt - 1) + jitter

base_delay = 1 秒
max_delay = 60 秒
max_retries = 5
jitter = random(0, 0.5) 秒
```

| 重试次数 | 基础延迟 | 实际延迟范围 |
|---------|---------|------------|
| 1 | 1s | 1.0s ~ 1.5s |
| 2 | 2s | 2.0s ~ 2.5s |
| 3 | 4s | 4.0s ~ 4.5s |
| 4 | 8s | 8.0s ~ 8.5s |
| 5 | 16s | 16.0s ~ 16.5s |

#### 各错误类型的重试策略

| 错误码 | 可重试 | 最大重试次数 | 退避策略 | 特殊处理 |
|--------|-------|------------|---------|---------|
| `VERSION_CONFLICT` | 是 | 3 | 指数退避 | 重试前需重新读取最新版本 |
| `RATE_LIMITED` | 是 | 5 | 固定间隔 | 使用响应中的 `retry_after` |
| `EMBEDDING_FAILED` | 是 | 3 | 指数退避 | 条目先以 `pending` 状态入库，后台异步重试 |
| `CHROMA_UNAVAILABLE` | 是 | 5 | 指数退避 | 降级为纯 SQLite 模式，后台持续重连 |
| `INTERNAL_ERROR` | 否 | 0 | - | 记录错误日志，需人工排查 |
| `DUPLICATE_DETECTED` | 否 | 0 | - | 返回已有条目信息，由调用方决定合并策略 |
| `VALIDATION_ERROR` | 否 | 0 | - | 修正请求参数后重新提交 |

#### 嵌入计算异步重试

向量嵌入计算失败时采用异步重试机制：

```
条目写入 → embedding_status = 'pending'
    │
    ├─→ 首次嵌入计算
    │       │
    │       ├─ 成功 → embedding_status = 'ready'
    │       │
    │       └─ 失败 → embedding_retry_count += 1
    │               │
    │               ├─ retry_count < 3 → 排入重试队列（指数退避）
    │               │
    │               └─ retry_count ≥ 3 → embedding_status 保持 'pending'
    │                                    记录错误日志
    │                                    降级为纯关键词检索
```

### 4.3 降级容错

#### SQLite 降级模式

当 Chroma 向量引擎不可用时，自动降级为纯 SQLite + FTS5 模式：

```
正常模式 (SQLite + Chroma)
    │
    ├─ Chroma 连接失败
    │       │
    │       ▼
    ├─ 降级模式 (SQLite + FTS5 only)
    │       │
    │       ├─ 写入操作：仅更新 SQLite，embedding_status = 'pending'
    │       ├─ 读取操作：仅使用 FTS5 关键词检索
    │       ├─ 后台持续尝试重连 Chroma
    │       │
    │       ├─ 重连成功 → 同步 pending 条目的嵌入 → 恢复正常模式
    │       └─ 重连失败 → 继续降级模式
    │
    └─ SQLite 也不可用
            │
            ▼
        文件存储 Fallback (v1.6 兼容模式)
```

#### 降级行为矩阵

| 组件状态 | 检索行为 | 写入行为 | 通知行为 |
|---------|---------|---------|---------|
| SQLite ✓ + Chroma ✓ | 混合检索（RRF 融合） | 双写 + 双索引 | 正常推送 |
| SQLite ✓ + Chroma ✗ | 纯关键词检索（FTS5） | SQLite 单写，嵌入标记 pending | 正常推送 |
| SQLite ✗ + Chroma ✓ | 纯语义检索 | Chroma 单写（降级模式） | 降级推送 |
| SQLite ✗ + Chroma ✗ | 文件存储 Fallback | 文件读写 | 无推送 |

---

## 5. 认证规范

### 5.1 API Key 管理

| 环境 | 认证方式 | 说明 |
|------|---------|------|
| 本地开发 (127.0.0.1) | 无认证 | 默认跳过认证 |
| 远程部署 (0.0.0.0) | API Key（强制） | 请求头 `X-API-Key` |

**API Key 格式**：`xks-` 前缀 + 32 字节随机十六进制字符串

```
xks-a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6
```

**API Key 来源**（按优先级）：

1. 环境变量 `KNOWLEDGE_API_KEY`
2. 配置文件 `.knowledge/.api_keys.json`

**API Key 存储格式**（`.knowledge/.api_keys.json`）：

```json
{
  "keys": [
    {
      "key_hash": "sha256:abc123...",
      "scope": "read_write",
      "description": "Backend Developer Agent",
      "created_at": "2026-05-01T10:00:00Z",
      "expires_at": null
    },
    {
      "key_hash": "sha256:def456...",
      "scope": "read_only",
      "description": "CI/CD Pipeline",
      "created_at": "2026-05-01T10:00:00Z",
      "expires_at": "2026-06-01T00:00:00Z"
    }
  ]
}
```

> **安全要求**：API Key 文件权限设置为 600（仅所有者可读写），存储时仅保留 SHA256 哈希值，不存储明文。

### 5.2 权限范围

| 权限级别 | 允许操作 | 对应端点 |
|---------|---------|---------|
| `read_only` | 检索和查询 | `knowledge_search`、`GET /v1/knowledge/*` |
| `read_write` | 所有 CRUD 操作 | `read_only` + `knowledge_add`、`knowledge_update`、`knowledge_delete` |
| `admin` | 所有端点 + 管理 | `read_write` + `knowledge_sync`、`backup`、`config` |

**权限检查流程**：

```
请求到达 → 检查认证模式
    │
    ├─ 本地模式 (127.0.0.1) → 跳过认证，授予 admin 权限
    │
    └─ 远程模式 → 检查 X-API-Key 请求头
            │
            ├─ 无 Key → 返回 401 UNAUTHORIZED
            ├─ Key 无效 → 返回 401 UNAUTHORIZED
            ├─ Key 过期 → 返回 401 UNAUTHORIZED
            └─ Key 有效 → 检查权限范围
                    │
                    ├─ 权限不足 → 返回 403 FORBIDDEN
                    └─ 权限充足 → 执行请求
```

### 5.3 API 限流

| 限流维度 | 默认值 | 说明 |
|---------|-------|------|
| 每分钟请求数 | 60 | 单 IP 滑动窗口限制 |
| 算法 | sliding_window | 滑动窗口算法 |

限流响应 HTTP 状态码：429 Too Many Requests，响应包含 `retry_after` 字段。

```json
{
  "status": "error",
  "data": null,
  "meta": {
    "error": {
      "code": "RATE_LIMITED",
      "message": "请求频率超限",
      "details": {
        "retry_after": 12,
        "limit": 60,
        "remaining": 0
      },
      "retryable": true
    }
  }
}
```

---

## 6. WebSocket 接口

### 6.1 实时知识更新推送

WebSocket 端点：`ws://127.0.0.1:8765/ws/notify`

**连接建立**：

```
客户端 → ws://127.0.0.1:8765/ws/notify
服务端 → 连接确认 + 当前服务状态
```

**消息格式**：

```json
{
  "event": "knowledge_created",
  "timestamp": "2026-05-03T10:00:00Z",
  "data": {
    "id": "ekb-bugfix-oom-handler-001",
    "title": "Node.js OOM 处理方案",
    "scope": "experience",
    "category": "错误解决方案",
    "confidence": 0.70,
    "tags": ["OOM", "内存泄漏", "Node.js"]
  }
}
```

**事件类型**：

| 事件 | 触发条件 | 推送内容 |
|------|---------|---------|
| `knowledge_created` | 新增知识条目 | 条目 ID、标题、作用域、分类 |
| `knowledge_updated` | 更新知识条目 | 条目 ID、变更字段、新版本号 |
| `knowledge_deleted` | 删除知识条目 | 条目 ID、删除原因 |
| `knowledge_merged` | 知识条目合并 | 源 ID、目标 ID、合并策略 |
| `version_conflict` | 乐观锁冲突 | 条目 ID、当前版本、冲突版本 |
| `embedding_ready` | 向量嵌入计算完成 | 条目 ID、嵌入状态 |
| `sync_completed` | 同步操作完成 | 同步 ID、同步统计 |
| `service_degraded` | 服务降级 | 降级组件、降级模式 |

**订阅过滤**：

客户端可在连接时指定订阅过滤条件：

```json
{
  "subscribe": {
    "scopes": ["experience"],
    "categories": ["错误解决方案", "安全漏洞"],
    "events": ["knowledge_created", "knowledge_updated"]
  }
}
```

### 6.2 连接管理

**心跳机制**：

- 服务端每 30 秒发送 `ping` 帧
- 客户端需在 10 秒内回复 `pong` 帧
- 连续 3 次未收到 `pong` 则断开连接

**重连策略**：

客户端断开后采用指数退避重连：

| 重试次数 | 延迟 |
|---------|------|
| 1 | 1s |
| 2 | 2s |
| 3 | 4s |
| 4 | 8s |
| 5+ | 30s（上限） |

**连接数限制**：

| 参数 | 默认值 | 说明 |
|------|-------|------|
| `max_connections` | 20 | 最大同时连接数 |
| `idle_timeout` | 300s | 空闲连接超时时间 |
| `message_size_limit` | 1MB | 单条消息大小限制 |

**连接生命周期**：

```
客户端发起连接
    │
    ├─→ 认证检查（远程模式需 API Key）
    │       │
    │       ├─ 认证失败 → 关闭连接 (4001)
    │       └─ 认证成功 → 进入已连接状态
    │
    ├─→ 已连接状态
    │       │
    │       ├─ 接收订阅过滤条件
    │       ├─ 按过滤条件推送事件
    │       ├─ 心跳维持
    │       │
    │       ├─ 客户端主动断开 → 关闭连接 (1000)
    │       ├─ 心跳超时 → 关闭连接 (4002)
    │       ├─ 服务端关闭 → 关闭连接 (1001)
    │       └─ 连接数超限 → 关闭连接 (4003)
```

**关闭码定义**：

| 关闭码 | 说明 |
|--------|------|
| 1000 | 正常关闭 |
| 1001 | 服务端关闭 |
| 4001 | 认证失败 |
| 4002 | 心跳超时 |
| 4003 | 连接数超限 |
| 4004 | 订阅过滤条件无效 |

---

## 7. 并发控制

### 7.1 读写锁策略

#### SQLite WAL 模式

启用 Write-Ahead Logging，允许读写并发，读操作不阻塞写操作：

```sql
PRAGMA journal_mode=WAL;
PRAGMA wal_autocheckpoint=1000;
PRAGMA busy_timeout=5000;
```

| PRAGMA | 值 | 说明 |
|--------|-----|------|
| `journal_mode` | WAL | 写前日志模式，读写并发 |
| `wal_autocheckpoint` | 1000 | 每 1000 页自动检查点 |
| `busy_timeout` | 5000ms | 写锁等待超时 |
| `foreign_keys` | ON | 启用外键约束 |
| `synchronous` | NORMAL | 平衡性能与安全性 |

#### 写入队列

所有写操作通过异步队列串行化执行，避免并发写入冲突：

```
写请求 → 入队列 → 异步串行执行
    │
    ├─ 成功 → 返回结果 + WebSocket 通知
    └─ 冲突 → 返回冲突信息（含当前版本号和解决选项）
```

**写入队列参数**：

| 参数 | 默认值 | 说明 |
|------|-------|------|
| `max_queue_size` | 1000 | 队列最大容量 |
| `queue_timeout` | 30s | 队列等待超时 |
| `batch_size` | 1 | 批量写入大小（当前为单条） |

#### 乐观锁机制

基于 `version` 字段检测冲突，写入时校验版本号，冲突时返回错误而非阻塞等待：

```sql
UPDATE knowledge_entries
SET title = ?, content = ?, version = version + 1, updated = datetime('now')
WHERE id = ? AND version = ?;
```

若 `affected_rows = 0`，说明版本冲突，返回 `VERSION_CONFLICT` 错误。

### 7.2 事务隔离级别

SQLite 默认隔离级别为 `SERIALIZABLE`，但 WAL 模式下读取不阻塞写入：

| 操作类型 | 事务范围 | 隔离级别 | 说明 |
|---------|---------|---------|------|
| 单条目写入 | 单事务 | SERIALIZABLE | 包含 entries + tags + FTS + version_history |
| 批量写入 | 单事务 | SERIALIZABLE | 批量 INSERT/UPDATE 在同一事务中 |
| 检索操作 | 无事务 | READ UNCOMMITTED | WAL 模式下读取最新已提交数据 |
| 同步操作 | 单事务 | SERIALIZABLE | 跨分支同步在独立事务中执行 |
| 备份操作 | 读取事务 | REPEATABLE READ | 备份期间数据快照一致性 |

**典型写入事务流程**：

```sql
BEGIN IMMEDIATE;

INSERT INTO version_history (entry_id, version, title, content, scope, tags,
    confidence, source_path, source_rating, content_hash, change_type, content_snapshot, saved_at)
SELECT id, version, title, content, scope, tags,
    confidence, source_path, source_rating, content_hash, 'update',
    json_object('title', title, 'content', content, 'tags', tags),
    datetime('now')
FROM knowledge_entries
WHERE id = ? AND version = ?;

UPDATE knowledge_entries
SET title = ?, content = ?, version = version + 1, updated = datetime('now'),
    embedding_status = 'pending'
WHERE id = ? AND version = ?;

DELETE FROM knowledge_tags WHERE entry_id = ?;
INSERT INTO knowledge_tags (entry_id, tag) VALUES (?, ?), (?, ?), ...;

COMMIT;
```

### 7.3 并发场景处理

| 场景 | 处理策略 |
|------|---------|
| 多 Agent 同时读取 | WAL 模式天然支持，无冲突 |
| 多 Agent 同时写入不同条目 | 写入队列串行化，无冲突 |
| 多 Agent 同时写入同一条目 | 乐观锁检测，版本冲突时返回冲突信息 |
| 读取与写入并发 | WAL 模式下读取不阻塞写入 |
| 批量导入与检索并发 | 批量导入在独立事务中，检索读取旧快照 |
| 同步操作与写入并发 | 同步操作加 IMMEDIATE 锁，写入排队等待 |

---

## 8. 备份灾备

### 8.1 自动备份策略

| 备份类型 | 频率 | 保留期限 | 存储位置 | 内容 |
|----------|------|---------|---------|------|
| 完整备份 | 每 6 小时 | 10 份 | `.knowledge/backup/full/` | knowledge.db + Chroma 数据 + 配置文件 |
| 增量备份 | 每小时 | 7 天 | `.knowledge/backup/incremental/` | 自上次备份后的变更条目 |
| 快照备份 | 每次重大变更 | 永久 | `.knowledge/backup/snapshot/` | 完整知识库快照 |

**备份文件命名**：

```
完整备份: kb-backup-full-20260503T100000.tar.gz
增量备份: kb-backup-inc-20260503T110000.json
快照备份: kb-snapshot-v2.0.0-20260503T100000.tar.gz
```

**备份前检查**：

```sql
PRAGMA integrity_check;
PRAGMA wal_checkpoint(TRUNCATE);
```

### 8.2 恢复流程

#### 条目级恢复

从备份中恢复单个知识条目：

```
1. 定位条目在最近备份中的版本
   → 查询 version_history 表获取历史版本快照

2. 验证条目完整性
   → 检查元数据字段完整性
   → 校验 content_hash

3. 恢复条目
   → 从 version_history.content_snapshot 读取快照
   → 写入 knowledge_entries 表
   → 更新 FTS 索引
   → 重新计算向量嵌入
```

#### 索引级恢复

重建损坏的索引文件：

```
1. 从 knowledge_entries 表重建 FTS5 索引
   → INSERT INTO knowledge_fts ... SELECT ... FROM knowledge_entries

2. 从 knowledge_entries 表重建 Chroma Collection
   → 重新计算所有 pending 条目的向量嵌入
   → 批量写入 Chroma

3. 一致性校验
   → 对比 SQLite ready_count 与 Chroma vector_count
   → 修复不一致条目
```

#### 全量恢复

从备份恢复整个知识库：

```
1. 停止所有 Agent 写入操作
   → 设置服务为 maintenance 模式
   → 关闭 WebSocket 连接

2. 从最近完整备份恢复
   → 解压备份文件
   → 替换 knowledge.db 文件
   → 替换 Chroma 数据目录

3. 按时间顺序应用增量备份
   → 读取增量备份 JSON 文件
   → 逐条应用变更

4. 重建所有索引
   → 执行 FTS5 重建
   → 执行 Chroma Collection 重建

5. 验证知识库完整性
   → PRAGMA integrity_check
   → 一致性校验
   → 条目数统计

6. 恢复服务
   → 退出 maintenance 模式
   → 重新接受请求
```

### 8.3 损坏检测

| 检测项 | 方法 | 频率 | 自动修复 |
|--------|------|------|---------|
| SQLite 文件完整性 | `PRAGMA integrity_check` | 每次启动 + 每 6 小时 | 从备份恢复 |
| 索引一致性 | 条目数 vs FTS 记录数 | 每日 | 重建 FTS 索引 |
| Chroma 一致性 | SQLite ready_count vs Chroma vector_count | 每日 | 重新嵌入缺失条目 |
| 元数据完整性 | 必填字段检查 | 每次写入 | 拒绝写入 |
| 交叉引用有效性 | 引用目标存在性检查 | 每日 | 标记为孤儿引用 |
| 内容哈希校验 | SHA256 校验和 | 每次读取 | 从备份恢复 |

### 8.4 版本回退

- 每次知识库变更都记录在 `version_history` 表中
- 通过 `knowledge_rollback` 端点可回退到任意历史版本
- 回退操作需要 `admin` 权限
- 回退后需重建 FTS 索引和 Chroma 向量

---

## 9. 配置文件

### 9.1 完整 YAML 配置示例

```yaml
knowledge_base:
  version: "2.0.0"
  last_sync: "2026-05-03T00:00:00Z"

  general:
    path: "~/.xuansto/knowledge/general"
    auto_sync: true
    sync_interval: "weekly"
    upstream: ""

  workspace:
    path: ".knowledge/workspace"
    auto_update: true
    track_changes: true

  experience:
    path: ".knowledge/experience"
    auto_extract: true
    review_required: true
    min_confidence: 0.8

  indexing:
    vector_enabled: true
    vector_index_path: ".knowledge/index/vector_index.json"
    embedding_model: "text-embedding-3-small"
    reindex_on_change: true
    keyword_engine: "sqlite-fts5"
    keyword_index_path: ".knowledge/index/keyword_index.db"
    metadata_engine: "sqlite"
    metadata_index_path: ".knowledge/index/metadata_index.json"
    cross_reference_path: ".knowledge/index/cross_reference.json"

  lifecycle:
    confidence_threshold_archive: 0.5
    archive_after_days: 90
    archive_path: ".knowledge/archive"
    dedup_similarity_threshold: 0.85
    generalization_min_projects: 3
    tech_stack_check_enabled: true

  active_learning:
    enabled: true
    min_source_rating: 3
    sandbox_verification: true
    verification_sandbox:
      enabled: true
      timeout_seconds: 300
      test_generation: true
      auto_promote_on_pass: true
    default_confidence_new: 0.6
    default_confidence_verified: 0.8
    community_digest_enabled: false

  server:
    host: "127.0.0.1"
    port: 8765
    transport: "stdio"
    log_level: "INFO"

  database:
    sqlite_path: ".knowledge/index/knowledge.db"
    chroma_path: ".knowledge/index/chroma_db"

  embedding:
    primary: "text-embedding-3-small"
    fallback: "sentence-transformers/all-MiniLM-L6-v2"
    dimension: 1536
    strategy: "primary_with_fallback"
    batch_size: 100
    cache_enabled: true

  retrieval:
    default_strategy: "hybrid"
    semantic_weight: 0.7
    keyword_weight: 0.3
    top_k: 5
    rerank_enabled: false
    hybrid:
      rrf_k: 60
      candidate_multiplier: 2
    semantic_only:
      min_similarity: 0.3
    keyword_only:
      bm25_weights:
        summary: 10.0
        type: 1.0
        category: 2.0

  dedup:
    similarity_threshold: 0.92
    action: "merge"
    metadata_hash_fields:
      - "title"
      - "scope"
      - "source"
      - "type"
      - "category"
      - "tags"
    auto_merge: false

  sync:
    watch_enabled: true
    delta_sync_interval: 300
    full_sync_interval: 86400
    file_patterns:
      - "*.md"
      - "*.yaml"
      - "*.json"
    watch_interval_seconds: 30
    full_sync_on_startup: false

  rate_limit:
    enabled: true
    max_requests_per_minute: 60
    algorithm: "sliding_window"

  resource_limits:
    max_memory_mb: 512
    max_db_size_mb: 1024
    max_connections: 20

  logging:
    level: "INFO"
    file_path: ".knowledge/logs/knowledge-server.log"
    max_size_mb: 10
    backup_count: 5
    format: "json"

  backup:
    sqlite_interval_hours: 6
    chroma_interval_hours: 24
    sqlite_retention_count: 10
    chroma_retention_count: 7
    encryption_enabled: false

  auth:
    enabled: false
    remote_enforced: true
    key_prefix: "xks-"

  websocket:
    enabled: true
    max_connections: 20
    idle_timeout_seconds: 300
    heartbeat_interval_seconds: 30
    message_size_limit_bytes: 1048576

  concurrency:
    write_queue_size: 1000
    write_queue_timeout_seconds: 30
    wal_autocheckpoint: 1000
    busy_timeout_ms: 5000
```

### 9.2 配置项说明

| 配置段 | 关键配置项 | 默认值 | 说明 |
|--------|-----------|-------|------|
| `server` | `host` | 127.0.0.1 | 服务监听地址 |
| `server` | `port` | 8765 | 服务监听端口 |
| `server` | `transport` | stdio | 传输协议：stdio / http |
| `database` | `sqlite_path` | .knowledge/index/knowledge.db | SQLite 数据库路径 |
| `database` | `chroma_path` | .knowledge/index/chroma_db | Chroma 数据目录 |
| `embedding` | `primary` | text-embedding-3-small | 主嵌入模型 |
| `embedding` | `fallback` | all-MiniLM-L6-v2 | 备选嵌入模型 |
| `embedding` | `strategy` | primary_with_fallback | 嵌入策略 |
| `retrieval` | `default_strategy` | hybrid | 默认检索策略 |
| `retrieval` | `semantic_weight` | 0.7 | 语义检索权重 |
| `retrieval` | `keyword_weight` | 0.3 | 关键词检索权重 |
| `dedup` | `similarity_threshold` | 0.92 | 去重相似度阈值 |
| `backup` | `sqlite_interval_hours` | 6 | SQLite 备份间隔 |
| `auth` | `enabled` | false | 是否启用认证 |
| `websocket` | `max_connections` | 20 | WebSocket 最大连接数 |
| `concurrency` | `write_queue_size` | 1000 | 写入队列容量 |

---

## 10. 测试用例

### 10.1 知识检索测试

| 用例 ID | 场景 | 前置条件 | 操作 | 预期结果 |
|---------|------|---------|------|---------|
| TC-SEARCH-001 | 混合检索 - 精确关键词 | 存在包含"观察者模式"的条目 | `knowledge_search(query="观察者模式", mode="hybrid")` | 返回匹配条目，rank_keyword 靠前 |
| TC-SEARCH-002 | 混合检索 - 语义模糊查询 | 存在事件驱动相关条目 | `knowledge_search(query="如何实现组件间通信", mode="hybrid")` | 返回观察者模式等语义相关条目 |
| TC-SEARCH-003 | 纯语义检索 | 存在多条语义相关条目 | `knowledge_search(query="内存不够用怎么办", mode="semantic")` | 返回 OOM 相关条目，rank_keyword 为 null |
| TC-SEARCH-004 | 纯关键词检索 | 存在精确匹配条目 | `knowledge_search(query="Node.js OOM", mode="keyword")` | 返回精确匹配条目，rank_semantic 为 null |
| TC-SEARCH-005 | 上下文感知检索 | 配置了 Agent 检索策略 | `knowledge_search(query="安全漏洞", context={task_type: "security", agent_role: "security-auditor"})` | 自动选择 precise 模式，置信度阈值 0.8 |
| TC-SEARCH-006 | 空结果查询 | 无匹配条目 | `knowledge_search(query="量子计算量子纠缠")` | 返回空结果列表，total=0 |
| TC-SEARCH-007 | 筛选条件组合 | 存在多类型条目 | `knowledge_search(query="模式", filters={type: "design_pattern", scope: "general", confidence_min: 0.8})` | 仅返回符合筛选条件的条目 |

### 10.2 知识写入测试

| 用例 ID | 场景 | 前置条件 | 操作 | 预期结果 |
|---------|------|---------|------|---------|
| TC-ADD-001 | 正常添加条目 | 无同名条目 | `knowledge_add(id="test-001", ...)` | 创建成功，status=active，embedding_status=pending |
| TC-ADD-002 | ID 重复 | 已存在同名条目 | `knowledge_add(id="test-001", ...)` | 返回 DUPLICATE_DETECTED 错误 |
| TC-ADD-003 | 语义去重触发 | 已存在相似度 > 0.85 的条目 | `knowledge_add(id="test-002", content=相似内容)` | 返回去重检测结果，建议合并 |
| TC-ADD-004 | 必填字段缺失 | - | `knowledge_add(title="无ID条目")` | 返回 VALIDATION_ERROR 错误 |
| TC-ADD-005 | 置信度超范围 | - | `knowledge_add(..., confidence=1.5)` | 返回 VALIDATION_ERROR 错误 |
| TC-ADD-006 | scope 枚举校验 | - | `knowledge_add(..., scope="invalid")` | 返回 VALIDATION_ERROR 错误 |

### 10.3 知识更新测试

| 用例 ID | 场景 | 前置条件 | 操作 | 预期结果 |
|---------|------|---------|------|---------|
| TC-UPD-001 | 正常更新 | 条目存在，版本号匹配 | `knowledge_update(entry_id="test-001", updates={...}, _version=1)` | 更新成功，_version 递增为 2 |
| TC-UPD-002 | 版本冲突 | 条目已被其他 Agent 更新 | `knowledge_update(entry_id="test-001", updates={...}, _version=1)` (当前版本已为 2) | 返回 VERSION_CONFLICT 错误 |
| TC-UPD-003 | 条目不存在 | - | `knowledge_update(entry_id="nonexistent", ...)` | 返回 NOT_FOUND 错误 |
| TC-UPD-004 | 部分字段更新 | 条目存在 | `knowledge_update(entry_id="test-001", updates={confidence: 0.85}, _version=2)` | 仅更新 confidence 字段，其他字段不变 |
| TC-UPD-005 | 版本历史记录 | 条目更新成功 | 查询 version_history 表 | 存在变更前快照记录 |

### 10.4 知识删除测试

| 用例 ID | 场景 | 前置条件 | 操作 | 预期结果 |
|---------|------|---------|------|---------|
| TC-DEL-001 | 正常删除（先归档） | 条目存在 | `knowledge_delete(entry_id="test-001", archive_first=true)` | 删除成功，archived=true，版本历史保留 |
| TC-DEL-002 | 直接删除 | 条目存在 | `knowledge_delete(entry_id="test-001", archive_first=false)` | 删除成功，archived=false |
| TC-DEL-003 | 删除不存在条目 | - | `knowledge_delete(entry_id="nonexistent")` | 返回 NOT_FOUND 错误 |
| TC-DEL-004 | 级联删除验证 | 条目存在且有关联标签 | 删除条目后查询 knowledge_tags | 关联标签记录已删除 |
| TC-DEL-005 | FTS 索引清理 | 条目已索引 | 删除后 FTS 检索 | 不再返回已删除条目 |

### 10.5 同步测试

| 用例 ID | 场景 | 前置条件 | 操作 | 预期结果 |
|---------|------|---------|------|---------|
| TC-SYNC-001 | 增量同步 - 无冲突 | 源分支有新条目 | `knowledge_sync(source="dev", target="main")` | 新条目同步到目标分支 |
| TC-SYNC-002 | 增量同步 - 有冲突 | 两分支修改了同一条目 | `knowledge_sync(..., conflict_resolution="higher_confidence")` | 高置信度版本胜出 |
| TC-SYNC-003 | 全量同步 | 源分支条目更多 | `knowledge_sync(..., sync_type="full")` | 目标分支与源分支一致 |
| TC-SYNC-004 | 试运行 | - | `knowledge_sync(..., dry_run=true)` | 返回预计变更，不实际写入 |
| TC-SYNC-005 | 同步日志记录 | 同步完成 | 查询 sync_log 表 | 存在同步记录，统计信息正确 |

### 10.6 错误处理与降级测试

| 用例 ID | 场景 | 前置条件 | 操作 | 预期结果 |
|---------|------|---------|------|---------|
| TC-ERR-001 | Chroma 不可用降级 | Chroma 服务停止 | 执行检索请求 | 自动降级为 FTS5 检索，返回结果 |
| TC-ERR-002 | Chroma 恢复后同步 | Chroma 重新启动 | 等待重连成功 | pending 条目自动重新嵌入 |
| TC-ERR-003 | 限流触发 | 超过 60 次/分钟 | 连续发送请求 | 第 61 次返回 429 RATE_LIMITED |
| TC-ERR-004 | 嵌入计算失败 | 嵌入服务不可用 | 添加新条目 | 条目以 pending 状态入库，后台重试 |
| TC-ERR-005 | SQLite 完整性损坏 | 数据库文件损坏 | 启动服务 | 检测到损坏，从备份恢复 |

### 10.7 并发测试

| 用例 ID | 场景 | 前置条件 | 操作 | 预期结果 |
|---------|------|---------|------|---------|
| TC-CONC-001 | 多 Agent 同时读取 | 10 个 Agent 同时检索 | 并发发送检索请求 | 所有请求成功返回，无阻塞 |
| TC-CONC-002 | 多 Agent 同时写入不同条目 | 5 个 Agent 写入不同条目 | 并发发送写入请求 | 所有请求成功，写入队列串行化执行 |
| TC-CONC-003 | 多 Agent 同时写入同一条目 | 2 个 Agent 更新同一条目 | 并发发送更新请求（相同版本号） | 第一个成功，第二个返回 VERSION_CONFLICT |
| TC-CONC-004 | 读写并发 | 1 个 Agent 写入，10 个 Agent 读取 | 同时执行读写 | 读取不阻塞，写入成功 |

### 10.8 认证测试

| 用例 ID | 场景 | 前置条件 | 操作 | 预期结果 |
|---------|------|---------|------|---------|
| TC-AUTH-001 | 本地模式无认证 | host=127.0.0.1 | 不带 API Key 发送请求 | 请求成功 |
| TC-AUTH-002 | 远程模式需认证 | host=0.0.0.0 | 不带 API Key 发送请求 | 返回 401 UNAUTHORIZED |
| TC-AUTH-003 | 有效 API Key | 远程模式 | 带有效 API Key 发送请求 | 请求成功 |
| TC-AUTH-004 | 无效 API Key | 远程模式 | 带无效 API Key 发送请求 | 返回 401 UNAUTHORIZED |
| TC-AUTH-005 | 权限不足 | read_only Key | 调用 knowledge_add | 返回 403 FORBIDDEN |
| TC-AUTH-006 | 过期 API Key | 远程模式 | 带过期 API Key 发送请求 | 返回 401 UNAUTHORIZED |

### 10.9 WebSocket 测试

| 用例 ID | 场景 | 前置条件 | 操作 | 预期结果 |
|---------|------|---------|------|---------|
| TC-WS-001 | 连接建立 | 服务运行中 | 建立 WebSocket 连接 | 连接成功，收到服务状态 |
| TC-WS-002 | 知识创建通知 | 已订阅 | 添加新知识条目 | 收到 knowledge_created 事件 |
| TC-WS-003 | 知识更新通知 | 已订阅 | 更新知识条目 | 收到 knowledge_updated 事件 |
| TC-WS-004 | 订阅过滤 | 指定 scope=experience | 添加 general 条目 | 不收到通知 |
| TC-WS-005 | 心跳超时 | 连接建立 | 不回复 pong | 3 次后连接断开 (4002) |
| TC-WS-006 | 连接数超限 | 已达最大连接数 | 新建连接 | 连接被拒 (4003) |

### 10.10 备份恢复测试

| 用例 ID | 场景 | 前置条件 | 操作 | 预期结果 |
|---------|------|---------|------|---------|
| TC-BKP-001 | 完整备份 | 服务运行中 | 触发完整备份 | 备份文件生成，条目数一致 |
| TC-BKP-002 | 增量备份 | 已有完整备份 | 触发增量备份 | 仅包含变更条目 |
| TC-BKP-003 | 条目级恢复 | 条目被误修改 | 从 version_history 恢复 | 条目恢复到指定版本 |
| TC-BKP-004 | 全量恢复 | 数据库损坏 | 从备份恢复 | 知识库完整恢复，索引重建 |
| TC-BKP-005 | 备份前完整性检查 | 数据库正常 | 执行 PRAGMA integrity_check | 检查通过，备份继续 |

---

## 11. 增量同步与双向同步设计

### 11.1 增量同步 (Incremental Sync)

增量同步模块由 `FileSyncDetector` 和 `IncrementalSync` 两个核心类组成，负责检测知识库 Markdown 文件的变更并执行增量同步操作。

**FileSyncDetector** 负责文件变更检测：

- 通过比较文件的 `mtime`（修改时间戳）快速识别可能变更的文件
- 对 mtime 发生变化的文件进一步计算 SHA256 哈希值，确认内容是否真正变更
- 维护 `file_mtime` 表记录每个文件的最近同步时间戳，用于增量比对
- 检测三种变更类型：新增（新文件出现）、修改（mtime + hash 均变化）、删除（文件消失）

**IncrementalSync** 负责执行增量同步：

- 接收 FileSyncDetector 的变更检测结果，按变更类型分别处理
- **新增 (add)**：解析 Markdown frontmatter，写入 `knowledge_entries` 表，更新 FTS5 索引，触发向量嵌入计算
- **修改 (modify)**：对比 content_hash 判断是否需要更新，执行乐观锁更新，记录版本历史，刷新 FTS 索引和向量嵌入
- **删除 (delete)**：从 `knowledge_entries` 表移除条目，级联清理 `knowledge_tags`、FTS 索引和 Chroma 向量，保留 `version_history` 快照
- 同步完成后写入 `sync_log` 表，记录同步类型为 `incremental`，包含同步统计信息

增量同步由配置文件 `sync.delta_sync_interval`（默认 300 秒）控制执行间隔，支持文件模式匹配（`*.md`、`*.yaml`、`*.json`）。

### 11.2 双向同步 (Bidirectional Sync)

双向同步模块由 `KnowledgeExporter` 类实现，负责将数据库中的变更写回 Markdown 文件，确保 DB 与文件系统的一致性。

**KnowledgeExporter** 工作流程：

1. 监听 `knowledge_entries` 表的变更事件（通过 WebSocket 通知或轮询 `updated` 字段）
2. 对发生变更的条目，读取最新数据并序列化为 Markdown 格式
3. 写入对应的 Markdown 文件，更新文件的 mtime 时间戳
4. 记录导出日志，防止循环同步（DB→文件→DB 的无限循环）

**Frontmatter 格式**：

导出的 Markdown 文件使用 YAML frontmatter 存储元数据：

```yaml
---
id: gkb-design-pattern-observer-001
title: 观察者模式
type: design_pattern
category: 设计模式
scope: general
tags:
  - 观察者模式
  - 发布订阅
  - 事件驱动
confidence: 0.95
source_rating: 3
source: GoF Design Patterns
version: 3
updated: "2026-05-03T11:00:00Z"
---

## 正文内容
定义对象间一对多的依赖关系...
```

**循环同步防护**：

- 导出写入文件后，FileSyncDetector 检测到 mtime 变化
- 通过比较 content_hash 判断文件内容是否真正变更（排除仅 mtime 变化的情况）
- 若 content_hash 未变化，跳过该文件的增量同步，避免 DB→文件→DB 循环

### 11.3 知识生命周期管理 (Lifecycle Management)

知识生命周期管理模块由 `LifecycleManager` 类实现，负责自动归档过时或低价值的知识条目，保持知识库的活跃度和检索质量。

**归档标准**：

条目满足以下**全部条件**时触发自动归档：

| 条件 | 阈值 | 说明 |
|------|------|------|
| 最后更新时间 | ≥ 90 天 | 长期未更新的条目可能已过时 |
| 置信度 | < 0.5 | 低置信度表明知识未经充分验证 |

归档标准对应配置文件中的 `lifecycle.archive_after_days`（默认 90）和 `lifecycle.confidence_threshold_archive`（默认 0.5）。

**LifecycleManager 工作流程**：

1. 定期扫描 `knowledge_entries` 表，筛选满足归档条件的条目
2. 将条目标记为 `archived` 状态（在 `scope` 或 `status` 字段中记录）
3. 将归档条目移至 `lifecycle.archive_path`（默认 `.knowledge/archive/`）目录
4. 记录归档操作日志，保留 `version_history` 快照以支持恢复

**搜索排除机制**：

归档条目通过三层过滤从搜索结果中排除：

1. **SQL 查询层**：`knowledge_search` 的 SQL 查询自动添加 `WHERE status != 'archived'` 条件，从数据源排除归档条目
2. **FTS5 索引层**：归档条目从 `knowledge_fts` 虚拟表中移除，关键词检索不再命中
3. **Chroma 向量层**：归档条目的向量嵌入从 Chroma Collection 中删除，语义检索不再返回

三层过滤确保归档条目不会出现在任何检索模式的结果中，同时保留归档数据以支持手动恢复。

## 新增模块设计

### tech_stack_detector.py — 技术栈自动检测

职责：从项目配置文件自动提取技术栈和版本信息。

支持检测的配置文件：
- package.json → Node.js/React/Vue/Angular/Svelte/Next.js + 版本
- Cargo.toml → Rust + 依赖框架
- go.mod → Go + 版本 + 依赖
- pyproject.toml / requirements.txt → Python + FastAPI/Flask/Django + 版本
- pubspec.yaml → Flutter/Dart

输出格式：`{"languages": [...], "frameworks": [...], "runtimes": [...], "platform": "web|desktop|mobile"}`

### context_formatter.py — 知识注入格式化

职责：将检索结果格式化为结构化上下文，注入 Agent 提示词。

核心逻辑：
- 优先级排序：高置信度(≥0.8) +2.0分，技术栈匹配 +1.5分
- Token 预算控制：按 4 字符/token 估算，优先保留高分条目
- 智能截断：超长条目自动降级为 summary 模式

### kb_client.py — 知识库客户端适配层

职责：提供统一的知识库调用接口，支持三级降级。

降级策略：MCP Tool → REST API → 文件系统

### web_search.py — 网络搜索知识更新

职责：从网络搜索官方技术规范，自动总结并更新知识库。

核心功能：
- 官方文档源搜索（8个技术栈）
- 信源权威性自动评级（5级）
- 搜索结果摘要提取与结构化
- 新技术栈依赖检测与自动知识摄入

### experience_precipitator.py — 修复经验自动沉淀

职责：在项目 bug 修复过程中自动提取错误处理经验。

核心功能：
- Bug 修复经验沉淀（confidence=0.70）
- 3-Strike 失败经验沉淀（confidence=0.40）
- 成功模式沉淀（confidence=0.75）
- 性能优化经验沉淀（confidence=0.70）
- 错误信息提取（支持6种语言错误格式）
- 修复经验去重与合并（Jaccard + SHA256 双重校验）

### progressive_search.py — 渐进式知识检索

职责：根据项目技术栈版本和任务场景，智能调整知识检索范围和深度。

核心功能：
- 多轮渐进式检索（工作→经验→通用）
- 基于技术栈版本的检索过滤
- 基于任务场景的检索策略自动调整（6种任务类型）
- Token 预算控制下的知识裁剪
- 按需深度加载（不受日常 token 预算限制）

---

> **文档维护说明**：本文档随知识库架构演进同步更新。任何架构变更需经 Specification Keeper 审核后更新本文档，并递增版本号。
