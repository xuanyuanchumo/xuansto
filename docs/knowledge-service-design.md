# 知识库数据库服务层 - 技术设计文档

> **来源**：本文档从《多Agent自主开发指导Skill - 需求分析说明书 v1.7.0》第七章拆分而来，包含知识库服务层的详细技术设计。需求定义见需求文档第七章。

**版本**：v1.7.0
**最后更新**：2026-04-30

---

## 目录

- [7.1 服务层架构概述](#71-服务层架构概述)
- [7.2 SQLite结构化存储设计](#72-sqlite结构化存储设计)
- [7.3 Chroma向量语义检索设计](#73-chroma向量语义检索设计)
- [7.4 混合检索引擎](#74-混合检索引擎-hybrid-retrieval-engine)
- [7.5 知识库API接口定义](#75-知识库api接口定义)
- [7.6 知识库服务管理](#76-知识库服务管理)
- [7.7 知识去重与智能更新](#77-知识去重与智能更新)
- [7.8 知识库安全规范](#78-知识库安全规范)
- [7.9 服务测试规范](#79-服务测试规范)

---

### 7.1 服务层架构概述

#### 7.1.1 架构全景图

```text
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        知识库数据库服务层架构 (v1.7.0)                               │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                        数据源层 (Source Layer)                           │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                 │   │
│  │  │ .knowledge/  │  │ Agent 沉淀    │  │ 外部知识摄入  │                 │   │
│  │  │ Markdown文件 │  │ 实时写入      │  │ API/爬虫导入  │                 │   │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘                 │   │
│  └─────────┼─────────────────┼─────────────────┼──────────────────────────┘   │
│            │                 │                 │                               │
│            ▼                 ▼                 ▼                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                      导入服务层 (Import Service)                         │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                 │   │
│  │  │ Frontmatter  │  │ 去重检测      │  │ 增量同步      │                 │   │
│  │  │ 解析器       │──▶│ (Dedup Check)│──▶│ (Delta Sync) │                 │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘                 │   │
│  └────────────────────────────┬────────────────────────────────────────────┘   │
│                               │                                                │
│              ┌────────────────┼────────────────┐                               │
│              ▼                                 ▼                               │
│  ┌──────────────────────┐          ┌──────────────────────┐                    │
│  │  SQLite 结构化引擎    │          │  Chroma 向量引擎      │                    │
│  │  ┌────────────────┐  │          │  ┌────────────────┐  │                    │
│  │  │ knowledge_     │  │          │  │ xuansto_       │  │                    │
│  │  │ entries        │  │          │  │ knowledge      │  │                    │
│  │  ├────────────────┤  │          │  │ (Collection)   │  │                    │
│  │  │ knowledge_tags │  │          │  ├────────────────┤  │                    │
│  │  ├────────────────┤  │          │  │ Embedding:     │  │                    │
│  │  │ version_       │  │          │  │ text-embedding │  │                    │
│  │  │ history        │  │          │  │ -3-small /     │  │                    │
│  │  ├────────────────┤  │          │  │ all-MiniLM-    │  │                    │
│  │  │ dedup_log      │  │          │  │ L6-v2          │  │                    │
│  │  ├────────────────┤  │          │  └────────────────┘  │                    │
│  │  │ knowledge_fts  │  │          │  Distance: cosine    │                    │
│  │  │ (FTS5虚拟表)   │  │          └──────────┬───────────┘                    │
│  │  └────────────────┘  │                     │                                │
│  │  索引: type/category/ │                     │                                │
│  │  confidence/created   │                     │                                │
│  └──────────┬───────────┘                     │                                │
│             │                                 │                                │
│             ▼                                 ▼                                │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                     混合检索引擎 (Hybrid Retrieval Engine)                │   │
│  │  ┌──────────────────────────────────────────────────────────────────┐  │   │
│  │  │  SQLite FTS5 BM25 ──┐                                          │  │   │
│  │  │                     ├──▶ RRF (Reciprocal Rank Fusion) ──▶ Top-K │  │   │
│  │  │  Chroma Cosine Sim ─┘                                          │  │   │
│  │  └──────────────────────────────────────────────────────────────────┘  │   │
│  └────────────────────────────┬────────────────────────────────────────────┘   │
│                               │                                                │
│                               ▼                                                │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                        API 服务层 (API Layer)                            │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                 │   │
│  │  │ REST API     │  │ MCP Tool     │  │ WebSocket    │                 │   │
│  │  │ (FastAPI)    │  │ Interface    │  │ (实时通知)   │                 │   │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘                 │   │
│  └─────────┼─────────────────┼─────────────────┼──────────────────────────┘   │
│            │                 │                 │                               │
│            ▼                 ▼                 ▼                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                        │
│  │ AI Models    │  │ Skill Agent  │  │ 外部工具     │                        │
│  │ (LLM/Embed)  │  │ (41 Agents)  │  │ (IDE插件等)  │                        │
│  └──────────────┘  └──────────────┘  └──────────────┘                        │
│                                                                               │
└───────────────────────────────────────────────────────────────────────────────┘
```

#### 7.1.2 双引擎设计理念

| 维度       | SQLite 引擎          | Chroma 引擎         | 协同价值                   |
| :------- | :----------------- | :---------------- | :--------------------- |
| **核心能力** | 结构化查询 + FTS5全文检索   | 语义向量相似度检索         | 互补覆盖精确与模糊查询            |
| **检索范式** | BM25关键词匹配（词频/文档频率） | 余弦相似度（语义空间距离）     | RRF融合消除单一范式偏差          |
| **适用场景** | 精确术语搜索、分类筛选、范围查询   | 概念搜索、跨语言检索、模糊意图匹配 | 混合策略覆盖90%+检索需求         |
| **数据规模** | 单机百万级条目无压力         | 万级条目性能最优，十万级需调优   | 分层存储，按规模弹性选择           |
| **部署依赖** | Python内置，零外部依赖     | 需安装chromadb包      | 本地优先，渐进增强              |
| **持久化**  | 单文件数据库，Git友好       | 目录级存储，需备份策略       | SQLite为主存储，Chroma为索引缓存 |

> **设计意图**：双引擎不是简单的功能叠加，而是基于检索范式的互补性设计。BM25擅长精确匹配（如搜索"PostgreSQL连接超时"），语义检索擅长概念关联（如搜索"数据库连不上"也能命中PostgreSQL相关条目）。RRF融合算法将两种排序结果归一化合并，使检索结果既精确又全面。

#### 7.1.3 数据流全景

```text
知识条目生命周期数据流：

  ┌─────────────┐
  │ 知识条目写入 │ ──── Markdown文件 / Agent实时写入 / 外部导入
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐     ┌─────────────────────────────────────────────────┐
  │ 去重检测     │────▶│ Chroma语义相似度(>0.92) → 元数据哈希比对(type+   │
  │ (Dedup Check)│     │ category+tags) → 确认重复/新增/合并              │
  └──────┬──────┘     └─────────────────────────────────────────────────┘
         │
    ┌────┴────┐
    │ 新条目  │ 合并条目
    ▼         ▼
  ┌─────────────┐  ┌─────────────┐
  │ 结构化存储   │  │ 版本记录     │
  │ → SQLite    │  │ → version_  │
  │   entries   │  │   history   │
  │   tags      │  │ → dedup_log │
  │   fts       │  │   (合并日志) │
  └──────┬──────┘  └──────┬──────┘
         │                │
         ▼                │
  ┌─────────────┐         │
  │ 向量嵌入     │         │
  │ → Chroma    │         │
  │   embedding │         │
  └──────┬──────┘         │
         │                │
         ▼                ▼
  ┌─────────────────────────────────────────────────────────────────┐
  │                     混合检索就绪                                  │
  │  查询 → SQLite FTS5 BM25 + Chroma Cosine → RRF融合 → Top-K结果  │
  └─────────────────────────────────────────────────────────────────┘
```

#### 7.1.4 向后兼容策略

| 兼容维度                | 策略                       | 说明                                                   |
| :------------------ | :----------------------- | :--------------------------------------------------- |
| **Source of Truth** | `.knowledge/` Markdown文件 | 数据库层为索引和缓存，Markdown文件仍为唯一权威数据源                       |
| **首次运行**            | 自动扫描导入                   | 检测到 `.knowledge/` 目录时，自动解析所有Markdown文件并导入数据库         |
| **增量同步**            | 文件变更检测                   | 监控Markdown文件的修改时间戳，仅同步变更部分                           |
| **降级回退**            | 数据库不可用时回退文件检索            | 当SQLite或Chroma不可用时，自动降级为第六章定义的文件检索模式                 |
| **数据导出**            | 数据库→Markdown双向同步         | 数据库中的变更可回写到Markdown文件，保持文件与数据库一致                     |
| **Git集成**           | SQLite文件纳入版本管理           | `knowledge.db` 纳入Git跟踪（v1.7索引缓存），`keyword_index.db` 标记待废弃（v1.8移除），Chroma数据目录加入 `.gitignore` |

**多项目知识隔离**：

知识库服务支持多项目并行运行，确保项目间知识完全隔离：

| 隔离维度 | 实现方式 | 说明 |
| :--- | :--- | :--- |
| **项目数据库隔离** | 每个项目绑定不同端口或不同SQLite数据库文件 | 项目A使用 `project-a.db`，项目B使用 `project-b.db`，数据互不可见 |
| **通用知识库** | 项目根目录 `.knowledge/general/`（优先）或 `~/.xuansto/knowledge/general/`（回退） | 共享只读资源，所有项目可读取但不允许写入，存放跨项目通用知识。存储位置优先级见6.2.1节 |
| **项目间隔离** | 独立服务实例或独立数据库文件 | 项目间知识完全隔离，一个项目的知识条目不会出现在另一个项目的检索结果中 |

> **设计意图**：多项目隔离确保不同项目的知识库互不干扰，同时通过通用知识库实现跨项目知识共享。项目级知识为可读写私有资源，通用知识库为只读共享资源，二者在检索时合并结果但写入时严格区分。

### 7.2 SQLite结构化存储设计

#### 7.2.1 核心表结构

**knowledge\_entries — 知识条目主表**

**knowledge_entries表字段清单**：

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | TEXT | PRIMARY KEY | 知识条目唯一标识，如 "KP-GEN-001" |
| type | TEXT | NOT NULL | 条目类型: paradigm/standard/pattern/error-solution/glossary/... |
| category | TEXT | NOT NULL | 分类: object-oriented/database/security/... |
| tags | TEXT | - | 标签JSON数组: '["SOLID","oop","design"]' |
| confidence | REAL | NOT NULL, DEFAULT 0.5 | 置信度 [0.0, 1.0] |
| source | TEXT | - | 来源URL或文件路径 |
| content_path | TEXT | - | Markdown文件相对路径 |
| summary | TEXT | - | 条目摘要（用于向量嵌入和FTS索引） |
| created | TEXT | NOT NULL | ISO8601创建时间 |
| updated | TEXT | NOT NULL | ISO8601更新时间 |
| last_validated | TEXT | - | ISO8601最后验证时间 |
| success_count | INTEGER | DEFAULT 0 | 成功应用次数 |
| failure_count | INTEGER | DEFAULT 0 | 失败应用次数 |
| occurrences | INTEGER | DEFAULT 1 | 出现/合并次数 |
| version | INTEGER | DEFAULT 1 | 当前版本号 |

> **参考实现**：以下SQL DDL为参考实现，需求定义见上文字段清单。

```sql
CREATE TABLE knowledge_entries (
    id              TEXT PRIMARY KEY,          -- 知识条目唯一标识，如 "KP-GEN-001"
    type            TEXT NOT NULL,             -- 条目类型: paradigm/standard/pattern/error-solution/glossary/...
    category        TEXT NOT NULL,             -- 分类: object-oriented/database/security/...
    tags            TEXT,                      -- 标签JSON数组: '["SOLID","oop","design"]'
    confidence      REAL NOT NULL DEFAULT 0.5, -- 置信度 [0.0, 1.0]
    source          TEXT,                      -- 来源URL或文件路径
    content_path    TEXT,                      -- Markdown文件相对路径
    summary         TEXT,                      -- 条目摘要（用于向量嵌入和FTS索引）
    created         TEXT NOT NULL,             -- ISO8601创建时间
    updated         TEXT NOT NULL,             -- ISO8601更新时间
    last_validated  TEXT,                      -- ISO8601最后验证时间
    success_count   INTEGER DEFAULT 0,         -- 成功应用次数
    failure_count   INTEGER DEFAULT 0,         -- 失败应用次数
    occurrences     INTEGER DEFAULT 1,         -- 出现/合并次数
    version         INTEGER DEFAULT 1          -- 当前版本号
);
```

**knowledge\_tags — 标签归一化表**

**knowledge_tags表字段清单**：

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| entry_id | TEXT | NOT NULL, FK→knowledge_entries(id) | 关联知识条目ID |
| tag | TEXT | NOT NULL | 归一化标签（小写，去空格） |
| *(entry_id, tag)* | - | PRIMARY KEY | 复合主键 |

> **参考实现**：以下SQL DDL为参考实现，需求定义见上文字段清单。

```sql
CREATE TABLE knowledge_tags (
    entry_id  TEXT NOT NULL,                   -- 关联 knowledge_entries.id
    tag       TEXT NOT NULL,                   -- 归一化标签（小写，去空格）
    PRIMARY KEY (entry_id, tag),
    FOREIGN KEY (entry_id) REFERENCES knowledge_entries(id) ON DELETE CASCADE
);
```

**version\_history — 版本历史表**

**version_history表字段清单**：

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | 自增主键 |
| entry_id | TEXT | NOT NULL, FK→knowledge_entries(id) | 关联知识条目ID |
| version | INTEGER | NOT NULL | 版本号 |
| content_snapshot | TEXT | - | 该版本内容快照（Markdown原文） |
| changed_at | TEXT | NOT NULL | ISO8601变更时间 |
| change_type | TEXT | NOT NULL | 变更类型: create/update/merge/rollback |

> **参考实现**：以下SQL DDL为参考实现，需求定义见上文字段清单。

```sql
CREATE TABLE version_history (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id         TEXT NOT NULL,            -- 关联 knowledge_entries.id
    version          INTEGER NOT NULL,         -- 版本号
    content_snapshot TEXT,                     -- 该版本内容快照（Markdown原文）
    changed_at       TEXT NOT NULL,            -- ISO8601变更时间
    change_type      TEXT NOT NULL,            -- 变更类型: create/update/merge/rollback
    FOREIGN KEY (entry_id) REFERENCES knowledge_entries(id) ON DELETE CASCADE
);
```

**dedup\_log — 去重日志表**

**dedup_log表字段清单**：

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | 自增主键 |
| new_entry_id | TEXT | NOT NULL | 新写入条目ID |
| existing_entry_id | TEXT | NOT NULL | 已存在条目ID |
| similarity_score | REAL | NOT NULL | 语义相似度分数 |
| action | TEXT | NOT NULL, CHECK IN ('skip','merge','keep_both') | 执行动作 |
| merged_at | TEXT | - | ISO8601合并时间（仅merge时） |

> **参考实现**：以下SQL DDL为参考实现，需求定义见上文字段清单。

```sql
CREATE TABLE dedup_log (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    new_entry_id      TEXT NOT NULL,           -- 新写入条目ID
    existing_entry_id TEXT NOT NULL,           -- 已存在条目ID
    similarity_score  REAL NOT NULL,           -- 语义相似度分数
    action            TEXT NOT NULL,           -- 执行动作: skip/merge/keep_both
    merged_at         TEXT,                    -- ISO8601合并时间（仅merge时）
    CHECK (action IN ('skip', 'merge', 'keep_both'))
);
```

#### 7.2.2 FTS5全文检索虚拟表

> **参考实现**：以下SQL DDL为参考实现，需求定义见上文字段清单。

```sql
CREATE VIRTUAL TABLE knowledge_fts USING fts5(
    id UNINDEXED,
    summary,
    type,
    category,
    content='knowledge_entries',
    content_rowid='rowid',
    tokenize='unicode61'                       -- 支持Unicode分词（含中文）
);

-- 触发器：自动同步 knowledge_entries → knowledge_fts
CREATE TRIGGER knowledge_entries_ai AFTER INSERT ON knowledge_entries BEGIN
    INSERT INTO knowledge_fts(rowid, id, summary, type, category)
    VALUES (new.rowid, new.id, new.summary, new.type, new.category);
END;

CREATE TRIGGER knowledge_entries_ad AFTER DELETE ON knowledge_entries BEGIN
    INSERT INTO knowledge_fts(knowledge_fts, rowid, id, summary, type, category)
    VALUES ('delete', old.rowid, old.id, old.summary, old.type, old.category);
END;

CREATE TRIGGER knowledge_entries_au AFTER UPDATE ON knowledge_entries BEGIN
    INSERT INTO knowledge_fts(knowledge_fts, rowid, id, summary, type, category)
    VALUES ('delete', old.rowid, old.id, old.summary, old.type, old.category);
    INSERT INTO knowledge_fts(rowid, id, summary, type, category)
    VALUES (new.rowid, new.id, new.summary, new.type, new.category);
END;
```

#### 7.2.3 索引设计

> **参考实现**：以下SQL DDL为参考实现，需求定义见上文字段清单。

```sql
CREATE INDEX idx_entries_type       ON knowledge_entries(type);
CREATE INDEX idx_entries_category   ON knowledge_entries(category);
CREATE INDEX idx_entries_confidence ON knowledge_entries(confidence);
CREATE INDEX idx_entries_created    ON knowledge_entries(created);
CREATE INDEX idx_entries_updated    ON knowledge_entries(updated);
CREATE INDEX idx_tags_tag           ON knowledge_tags(tag);
CREATE INDEX idx_version_entry      ON version_history(entry_id, version);
CREATE INDEX idx_dedup_new          ON dedup_log(new_entry_id);
```

| 索引名称                     | 覆盖查询场景                   | 预期选择性        |
| :----------------------- | :----------------------- | :----------- |
| `idx_entries_type`       | 按类型筛选（如仅查error-solution） | 中等，约10-20种类型 |
| `idx_entries_category`   | 按分类筛选（如仅查database类）      | 中等，约30-50种分类 |
| `idx_entries_confidence` | 置信度阈值过滤（如 ≥0.8）          | 低，值域连续       |
| `idx_entries_created`    | 按创建时间排序/范围查询             | 高，近乎唯一       |
| `idx_entries_updated`    | 增量同步时查找最近更新              | 高，近乎唯一       |
| `idx_tags_tag`           | 按标签检索关联条目                | 中等，热门标签命中多条  |
| `idx_version_entry`      | 查询某条目的版本历史               | 高，复合索引精确匹配   |
| `idx_dedup_new`          | 去重日志回查                   | 高，精确匹配       |

#### 7.2.4 ER关系图

```text
┌──────────────────────┐       ┌──────────────────────┐
│  knowledge_entries   │       │   knowledge_tags     │
├──────────────────────┤       ├──────────────────────┤
│ *id TEXT PK          │◀──────│ *entry_id TEXT FK     │
│  type TEXT           │       │ *tag TEXT             │
│  category TEXT       │       └──────────────────────┘
│  tags TEXT           │
│  confidence REAL     │       ┌──────────────────────┐
│  source TEXT         │       │  version_history     │
│  content_path TEXT   │       ├──────────────────────┤
│  summary TEXT        │◀──────│  id INTEGER PK AUTO  │
│  created TEXT        │       │ *entry_id TEXT FK     │
│  updated TEXT        │       │  version INTEGER      │
│  last_validated TEXT │       │  content_snapshot TEXT│
│  success_count INT   │       │  changed_at TEXT      │
│  failure_count INT   │       │  change_type TEXT     │
│  occurrences INT     │       └──────────────────────┘
│  version INT         │
└──────────────────────┘       ┌──────────────────────┐
         ▲                     │  dedup_log            │
         │                     ├──────────────────────┤
         │                     │  id INTEGER PK AUTO  │
         └─────────────────────│ *new_entry_id TEXT   │
                               │ *existing_entry_id   │
                               │  similarity_score    │
                               │  action TEXT         │
                               │  merged_at TEXT      │
                               └──────────────────────┘

         ┌──────────────────────┐
         │  knowledge_fts (FTS5)│  ← 虚拟表，由触发器自动同步
         ├──────────────────────┤
         │  id UNINDEXED        │
         │  summary             │
         │  type                │
         │  category            │
         └──────────────────────┘
```

#### 7.2.5 Schema版本管理

**schema_version元数据表**：

**schema_version表字段清单**：

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| version | INTEGER | PRIMARY KEY | Schema版本号，如 1、2、3 |
| applied_at | TEXT | NOT NULL | ISO8601迁移应用时间 |
| description | TEXT | NOT NULL | 迁移描述，如 "新增dedup_log表" |

> **参考实现**：以下SQL DDL为参考实现，需求定义见上文字段清单。

```sql
CREATE TABLE schema_version (
    version     INTEGER PRIMARY KEY,    -- Schema版本号，如 1、2、3
    applied_at  TEXT NOT NULL,          -- ISO8601迁移应用时间
    description TEXT NOT NULL           -- 迁移描述，如 "新增dedup_log表"
);
```

> **设计意图**：通过独立的 `schema_version` 表追踪数据库Schema演进历史，确保多环境部署时Schema状态可审计、迁移可回滚。

**增量迁移脚本命名规范**：

```text
migrations/
├── v1_to_v2.sql          -- 从Schema v1迁移到v2
├── v2_to_v3.sql          -- 从Schema v2迁移到v3
└── v3_to_v4.sql          -- 从Schema v3迁移到v4
```

命名规则：`migrations/v{N}_to_v{N+1}.sql`，其中 `N` 为当前Schema版本号。每个迁移脚本必须为幂等设计，重复执行不产生副作用。

**迁移执行流程**：

```text
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ 版本检测     │────▶│ 按序执行     │────▶│ 数据完整性   │────▶│ 完成/回滚    │
│ 读取当前版本 │     │ 逐个执行     │     │ 验证         │     │              │
│ 确定待迁移   │     │ 迁移脚本     │     │ PRAGMA检查   │     │              │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

| 步骤 | 操作 | 说明 |
| :--- | :--- | :--- |
| **1. 版本检测** | 查询 `schema_version` 表获取当前版本号 | 若表不存在，视为v0，从v0_to_v1开始执行 |
| **2. 按序执行** | 按版本号顺序依次执行待执行的迁移脚本 | 每个脚本在独立事务中执行 |
| **3. 数据完整性验证** | 执行 `PRAGMA integrity_check` 和 `PRAGMA foreign_key_check` | 验证迁移后数据库结构和引用完整性 |
| **4. 完成/回滚** | 验证通过则写入 `schema_version` 记录；失败则回滚当前事务 | 回滚后数据库保持迁移前状态 |

**迁移失败回滚策略**：

| 失败场景 | 回滚策略 |
| :--- | :--- |
| **单步迁移脚本执行失败** | 回滚当前迁移事务，数据库保持该步迁移前状态，记录失败日志 |
| **完整性验证失败** | 回滚当前迁移事务，恢复到迁移前一致性状态 |
| **部分迁移已执行** | 已成功执行的迁移步骤不回滚（已写入 `schema_version`），仅回滚当前失败步骤 |
| **无法自动恢复** | 记录详细错误信息，通过健康检查端点暴露 `sqlite_integrity: corrupted`，等待人工介入 |

### 7.3 Chroma向量语义检索设计

#### 7.3.1 Collection定义

| 配置项              | 值                                            | 说明            |
| :--------------- | :------------------------------------------- | :------------ |
| **Collection名称** | `xuansto_knowledge`                          | 全局唯一命名空间      |
| **文档格式**         | `summary + "\n---\n" + key_content_excerpts` | 摘要+关键内容摘录拼接   |
| **距离函数**         | `cosine`                                     | 余弦相似度，适合语义检索  |
| **分块策略**         | 按知识条目粒度                                      | 每个条目为一个文档，不拆分 |

#### 7.3.2 元数据Schema

> **参考实现**：以下Python代码为参考实现，需求定义见上文元数据Schema规范。

```python
metadata_schema = {
    "id": str,              # 知识条目ID，如 "KP-GEN-001"
    "type": str,            # 条目类型
    "category": str,        # 分类
    "confidence": float,    # 置信度
    "source": str,          # 来源标识
}
```

#### 7.3.3 嵌入模型配置

```yaml
embedding:
  primary:
    model: "text-embedding-3-small"     # OpenAI API，1536维
    provider: "openai"
    dimension: 1536
    cost_per_1k_tokens: 0.02           # USD

  fallback:
    model: "all-MiniLM-L6-v2"          # 本地模型，384维
    provider: "sentence-transformers"
    dimension: 384
    cost_per_1k_tokens: 0              # 本地免费

  strategy: "primary_with_fallback"     # 优先API，失败回退本地
  batch_size: 100                       # 批量嵌入大小
  cache_enabled: true                   # 启用嵌入缓存
```

| 模型                         | 维度   | 适用场景         | 优势          | 劣势             |
| :------------------------- | :--- | :----------- | :---------- | :------------- |
| **text-embedding-3-small** | 1536 | 在线环境、高质量语义检索 | 精度高、多语言支持好  | 需API Key、有调用成本 |
| **all-MiniLM-L6-v2**       | 384  | 离线环境、快速原型    | 免费、本地运行、零延迟 | 精度略低、中文支持一般    |

> **降级策略**：当API调用失败（网络超时、Key过期、额度耗尽）时，自动切换到本地 `all-MiniLM-L6-v2` 模型。切换过程对上层检索透明，但会在健康检查接口中标记 `embedding_degraded: true`。

**嵌入模型降级链**：

```text
嵌入模型可用性降级链：

  ┌──────────────────────┐
  │ text-embedding-3-small│  ← 首选：OpenAI API，1536维，质量最优
  │ (OpenAI API)         │
  └──────────┬───────────┘
             │ API不可用
             ▼
  ┌──────────────────────┐
  │ all-MiniLM-L6-v2     │  ← 降级：本地模型，384维，零外部依赖
  │ (sentence-transformers)│
  └──────────┬───────────┘
             │ 本地模型加载失败
             ▼
  ┌──────────────────────┐
  │ 仅FTS5关键词检索       │  ← 最终降级：禁用语义检索，仅BM25
  │ (SQLite FTS5)        │
  └──────────────────────┘
```

| 降级级别 | 触发条件 | 检索能力 | 性能影响 | 自动恢复 |
| :--- | :--- | :--- | :--- | :--- |
| **Level 0（正常）** | text-embedding-3-small可用 | 混合检索（BM25+语义） | 基线 | — |
| **Level 1（降级）** | API不可用或超时>5秒 | 混合检索（BM25+本地语义） | 语义质量略降 | 每5分钟探测API可用性 |
| **Level 2（最终降级）** | 本地模型加载失败 | 仅BM25关键词检索 | 概念搜索能力丧失 | 每次服务启动时尝试加载 |

**模型切换期间数据一致性**：

- 当从Level 1降级到Level 0恢复时，Chroma中由all-MiniLM-L6-v2生成的向量与text-embedding-3-small向量维度不同（384 vs 1536），系统SHALL：
  1. 标记所有现有向量条目为`embedding_model_stale=true`
  2. 在后台异步执行重新嵌入（每次处理10条，避免阻塞服务）
  3. 重新嵌入完成前，混合检索仅使用BM25部分，语义部分权重降低
  4. 全部重新嵌入完成后，清除`embedding_model_stale`标记，恢复正常混合检索

#### 7.3.4 查询接口

**函数契约**：`query_chroma(collection: Collection, query_text: str, n_results: int, where_filter: dict | None) -> list[dict]`
- 输入：Chroma Collection对象、查询文本、返回数量、过滤条件
- 输出：匹配的知识条目列表，每项包含id、document、metadata、distance、similarity

> **参考实现**：以下Python代码为参考实现，需求定义见上文接口契约。

```python
from chromadb import Collection

def query_chroma(
    collection: Collection,
    query_text: str,
    n_results: int = 10,
    where_filter: dict | None = None,
) -> list[dict]:
    results = collection.query(
        query_texts=[query_text],
        n_results=n_results,
        where=where_filter,
        include=["documents", "metadatas", "distances"]
    )
    return [
        {
            "id": meta["id"],
            "document": doc,
            "metadata": meta,
            "distance": dist,
            "similarity": 1 - dist,
        }
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        )
    ]
```

**过滤查询示例**：

> **参考实现**：以下Python代码为参考实现，需求定义见上文过滤查询规范。

```python
where_filter = {
    "$and": [
        {"type": {"$eq": "error-solution"}},
        {"confidence": {"$gte": 0.8}},
        {"category": {"$eq": "database"}},
    ]
}
```

### 7.4 混合检索引擎 (Hybrid Retrieval Engine)

#### 7.4.1 RRF融合算法

Reciprocal Rank Fusion（RRF）是一种无需归一化的排序融合算法，将多个检索系统的排名结果合并为统一排序。相比简单加权融合，RRF对评分尺度差异不敏感，更适合BM25分数与余弦相似度的融合。

**函数契约**：`reciprocal_rank_fusion(ranked_lists: list[list[str]], k: int) -> list[tuple[str, float]]`
- 输入：多个检索系统的排名结果列表、RRF平滑常数k（默认60）
- 输出：融合后的排序结果列表，每项为(文档ID, RRF分数)元组，按分数降序排列

> **参考实现**：以下Python代码为参考实现，需求定义见上文算法步骤。

```python
def reciprocal_rank_fusion(
    ranked_lists: list[list[str]],
    k: int = 60,
) -> list[tuple[str, float]]:
    rrf_scores: dict[str, float] = {}
    for ranked_list in ranked_lists:
        for rank, doc_id in enumerate(ranked_list, start=1):
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + 1.0 / (k + rank)
    sorted_results = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
    return sorted_results
```

**RRF公式**：

```text
RRF_score(d) = Σ_{r∈R} 1 / (k + rank_r(d))

其中：
  d    = 文档ID
  R    = 检索系统集合 {BM25, Cosine}
  k    = 平滑常数（默认60，经验最优值）
  rank_r(d) = 文档d在检索系统r中的排名位置
```

> **设计意图**：选择RRF而非简单加权融合的原因——BM25分数范围不固定（依赖语料库大小和词频分布），余弦相似度范围为\[0,1]，两者尺度不一致。RRF仅使用排名位置，天然消除尺度差异，且对异常值（如BM25极端高分）鲁棒。

#### 7.4.2 检索策略配置

| 策略        | 标识              | 适用场景      | 说明                        |
| :-------- | :-------------- | :-------- | :------------------------ |
| **混合检索**  | `hybrid`（默认）    | 通用场景      | BM25+Cosine RRF融合，兼顾精确与语义 |
| **语义检索**  | `semantic_only` | 概念搜索、跨语言  | 仅使用Chroma余弦相似度            |
| **关键词检索** | `keyword_only`  | 精确匹配、术语搜索 | 仅使用SQLite FTS5 BM25       |

```yaml
retrieval:
  default_strategy: "hybrid"
  hybrid:
    semantic_weight: 0.6          # 语义检索权重（RRF中通过k值间接影响）
    keyword_weight: 0.4           # 关键词检索权重
    rrf_k: 60                     # RRF平滑常数
    top_k: 5                      # 最终返回条目数
    candidate_multiplier: 2       # 候选集倍数（各引擎先取 top_k * multiplier 再融合）
  semantic_only:
    top_k: 5
    min_similarity: 0.3           # 最低相似度阈值
  keyword_only:
    top_k: 5
    bm25_weights:                 # FTS5列权重
      summary: 10.0
      type: 1.0
      category: 2.0
```

#### 7.4.3 上下文感知检索

不同Agent角色对知识的需求不同，混合检索引擎支持基于Agent角色的上下文过滤：

| Agent角色               | 默认过滤策略                                                                                           | 优先知识层                 | 置信度阈值 |
| :-------------------- | :----------------------------------------------------------------------------------------------- | :-------------------- | :---- |
| **Code Reviewer**     | `type IN ('standard','pattern','error-solution')`                                                | 工作知识库 > 通用知识库 > 经验知识库 | ≥0.7  |
| **Backend Developer** | `type IN ('pattern','error-solution','glossary') AND category='database'`                        | 工作知识库 > 经验知识库 > 通用知识库 | ≥0.6  |
| **Security Auditor**  | `type IN ('standard','error-solution') AND category='security'`                                  | 通用知识库 > 经验知识库 > 工作知识库 | ≥0.8  |
| **Test Architect**    | `type IN ('standard','pattern') AND category='testing'`                                          | 工作知识库 > 通用知识库         | ≥0.7  |
| **Desktop Developer** | `type IN ('standard','pattern','error-solution') AND category IN ('desktop','electron','tauri')` | 通用知识库 > 经验知识库 > 工作知识库 | ≥0.6  |

> **参考实现**：以下Python代码为参考实现，需求定义见上文上下文感知检索规范。

```python
def context_aware_search(
    query: str,
    agent_role: str,
    top_k: int = 5,
) -> list[KnowledgeEntry]:
    role_config = AGENT_RETRIEVAL_PROFILES.get(agent_role, {})
    filters = role_config.get("filters", {})
    min_confidence = role_config.get("min_confidence", 0.5)
    filters["confidence"] = {"$gte": min_confidence}
    return hybrid_search(
        query=query,
        top_k=top_k,
        search_type="hybrid",
        filters=filters,
    )
```

#### 7.4.4 混合检索完整流程

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                        混合检索执行流程                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐                                                            │
│  │ 用户查询     │  query="数据库连不上怎么办"                                   │
│  └──────┬──────┘                                                            │
│         │                                                                   │
│         ▼                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 策略路由                                                             │   │
│  │  search_type="hybrid" → 并行执行双引擎检索                           │   │
│  │  search_type="semantic_only" → 仅Chroma                              │   │
│  │  search_type="keyword_only" → 仅SQLite FTS5                         │   │
│  └──────────┬──────────────────────────────────────────────────────────┘   │
│             │                                                               │
│      ┌──────┴──────┐                                                        │
│      ▼             ▼                                                        │
│  ┌─────────┐  ┌─────────┐                                                   │
│  │ SQLite  │  │ Chroma  │   并行检索，各取 top_k * candidate_multiplier 条   │
│  │ FTS5    │  │ Vector  │   (默认各取10条候选)                                │
│  │ BM25    │  │ Cosine  │                                                    │
│  └────┬────┘  └────┬────┘                                                    │
│       │            │                                                         │
│       ▼            ▼                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ RRF 融合                                                             │   │
│  │  BM25排名: [A:1, B:2, C:3, D:4, E:5, ...]                          │   │
│  │  Cosine排名: [C:1, A:2, F:3, B:4, G:5, ...]                        │   │
│  │  RRF_score(A) = 1/(60+1) + 1/(60+2) = 0.0328                       │   │
│  │  RRF_score(C) = 1/(60+3) + 1/(60+1) = 0.0323                       │   │
│  │  → 融合排序: [A, C, B, F, D, ...]                                   │   │
│  └──────────┬──────────────────────────────────────────────────────────┘   │
│             │                                                               │
│             ▼                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 上下文过滤                                                           │   │
│  │  应用Agent角色过滤策略 + 置信度阈值 + 分类/标签筛选                    │   │
│  └──────────┬──────────────────────────────────────────────────────────┘   │
│             │                                                               │
│             ▼                                                               │
│  ┌─────────────┐                                                            │
│  │ Top-K 结果  │  返回最终 top_k 条 KnowledgeEntry                          │
│  └─────────────┘                                                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 7.5 知识库API接口定义

#### 7.5.1 REST API端点

| 方法       | 路径                       | 说明         | 认证      |
| :------- | :----------------------- | :--------- | :------ |
| `POST`   | `/v1/knowledge/search`      | 混合检索       | 无（本地服务） |
| `GET`    | `/v1/knowledge/get/{id}`    | 获取指定条目     | 无       |
| `POST`   | `/v1/knowledge/add`         | 新增条目（自动去重） | 无       |
| `PUT`    | `/v1/knowledge/update/{id}` | 更新条目       | 无       |
| `DELETE` | `/v1/knowledge/delete/{id}` | 删除条目       | 无       |
| `GET`    | `/v1/knowledge/health`      | 健康检查       | 无       |
| `GET`  | `/v1/health/consistency` | 一致性校验 | 触发SQLite与Chroma数据一致性校验，返回校验报告 |

#### 7.5.2 接口详细定义

**POST /v1/knowledge/search — 混合检索**

```json
{
  "query": "PostgreSQL连接超时",
  "top_k": 5,
  "search_type": "hybrid",
  "filters": {
    "type": "error-solution",
    "category": "database",
    "min_confidence": 0.7,
    "tags": ["postgresql", "timeout"]
  }
}
```

响应：

```json
{
  "status": "ok",
  "data": [
    {
      "id": "KP-EXP-ERR-001",
      "type": "error-solution",
      "category": "database",
      "tags": ["postgresql", "connection", "timeout"],
      "confidence": 0.98,
      "summary": "PostgreSQL连接超时问题，根因为防火墙未开放端口和连接池配置不当",
      "content_path": "experience/errors/database/pg-connection-timeout.md",
      "rrf_score": 0.0328,
      "source_rank": {
        "bm25_rank": 1,
        "semantic_rank": 2
      },
      "created": "2026-04-15T10:30:00Z",
      "updated": "2026-04-20T14:22:00Z"
    }
  ],
  "meta": {
    "total": 1,
    "search_type": "hybrid",
    "elapsed_ms": 45
  }
}
```

**POST /v1/knowledge/add — 新增条目**

```json
{
  "content": "## Redis连接池耗尽\n\n连接池耗尽导致服务不可用...",
  "metadata": {
    "id": "KP-EXP-ERR-002",
    "type": "error-solution",
    "category": "database",
    "tags": ["redis", "connection-pool"],
    "confidence": 0.85,
    "source": "experience/errors/database/redis-pool-exhaustion.md"
  },
  "auto_dedup": true
}
```

响应（新增成功）：

```json
{
  "status": "ok",
  "data": {
    "id": "KP-EXP-ERR-002",
    "type": "error-solution",
    "category": "database",
    "confidence": 0.85,
    "version": 1,
    "created": "2026-04-29T08:15:00Z"
  },
  "meta": {
    "dedup_checked": true,
    "dedup_result": "no_duplicate"
  }
}
```

响应（检测到重复）：

```json
{
  "status": "conflict",
  "data": {
    "existing_id": "KP-EXP-ERR-001",
    "similarity_score": 0.94,
    "action": "merge_suggested"
  },
  "meta": {
    "dedup_checked": true,
    "dedup_result": "duplicate_detected"
  }
}
```

**PUT /v1/knowledge/update/{id} — 更新条目**

```json
{
  "summary": "PostgreSQL连接超时问题，新增连接池预热方案",
  "confidence": 0.99,
  "tags": ["postgresql", "connection", "timeout", "pool-warmup"]
}
```

**DELETE /v1/knowledge/delete/{id} — 删除条目**

响应：

```json
{
  "status": "ok",
  "data": {
    "id": "KP-EXP-ERR-001",
    "deleted_at": "2026-04-29T10:00:00Z",
    "version_history_preserved": true
  },
  "meta": {}
}
```

**GET /v1/knowledge/health — 健康检查**

响应：

```json
{
  "status": "ok",
  "data": {
    "sqlite_ok": true,
    "chroma_ok": true,
    "embedding_degraded": false,
    "entry_count": 156,
    "last_sync": "2026-04-29T08:00:00Z",
    "chroma_collection_count": 156,
    "uptime_seconds": 3600
  },
  "meta": {}
}
```

#### 7.5.3 MCP Tool接口

MCP Tool接口为Agent提供原生调用能力，无需通过HTTP层：

| Tool名称             | 参数                                                                        | 返回值                    | 说明   |
| :----------------- | :------------------------------------------------------------------------ | :--------------------- | :--- |
| `knowledge_search` | `query: str, top_k: int=5, search_type: str="hybrid", filters: dict=None` | `List[KnowledgeEntry]` | 混合检索 |
| `knowledge_add`    | `content: str, metadata: dict, auto_dedup: bool=True`                     | `KnowledgeEntry`       | 新增条目 |
| `knowledge_update` | `id: str, content: str=None, metadata: dict=None`                         | `KnowledgeEntry`       | 更新条目 |
| `knowledge_delete` | `id: str`                                                                 | `dict`                 | 删除条目 |
| `knowledge_rollback` | `id: str, target_version: int`                                          | `KnowledgeEntry`       | 回滚条目至指定版本 |

**MCP Tool定义示例**：

**函数契约**：
- `knowledge_search(query: str, top_k: int, search_type: str, filters: dict | None) -> list[dict]` — 混合检索，返回匹配的知识条目列表
- `knowledge_add(content: str, metadata: dict, auto_dedup: bool) -> dict` — 新增条目，返回创建的知识条目
- `knowledge_update(id: str, content: str | None, metadata: dict | None) -> dict` — 更新条目，返回更新后的知识条目
- `knowledge_delete(id: str) -> dict` — 删除条目，返回操作结果
- `knowledge_rollback(id: str, target_version: int) -> dict` — 回滚条目至指定版本，返回回滚后的知识条目

> **参考实现**：以下Python代码为参考实现，需求定义见上文MCP Tool接口契约。

```python
from mcp.server import Server

server = Server("xuansto-knowledge")

@server.tool()
async def knowledge_search(
    query: str,
    top_k: int = 5,
    search_type: str = "hybrid",
    filters: dict | None = None,
) -> list[dict]:
    results = await hybrid_search_engine.search(
        query=query,
        top_k=top_k,
        search_type=search_type,
        filters=filters,
    )
    return [entry.to_dict() for entry in results]

@server.tool()
async def knowledge_add(
    content: str,
    metadata: dict,
    auto_dedup: bool = True,
) -> dict:
    entry = await knowledge_service.add_entry(
        content=content,
        metadata=metadata,
        auto_dedup=auto_dedup,
    )
    return entry.to_dict()

@server.tool()
async def knowledge_update(
    id: str,
    content: str | None = None,
    metadata: dict | None = None,
) -> dict:
    entry = await knowledge_service.update_entry(
        entry_id=id,
        content=content,
        metadata=metadata,
    )
    return entry.to_dict()

@server.tool()
async def knowledge_delete(
    id: str,
) -> dict:
    result = await knowledge_service.delete_entry(
        entry_id=id,
    )
    return result

@server.tool()
async def knowledge_rollback(
    id: str,
    target_version: int,
) -> dict:
    entry = await knowledge_service.rollback_entry(
        entry_id=id,
        target_version=target_version,
    )
    return entry.to_dict()
```

#### 7.5.4 标准响应信封

所有API响应遵循统一信封格式：

```json
{
  "status": "ok | error | conflict",
  "data": {},
  "meta": {
    "elapsed_ms": 45,
    "dedup_checked": true,
    "dedup_result": "no_duplicate"
  }
}
```

#### 7.5.5 错误码定义

**客户端错误（4xx）**：

| HTTP状态码 | 错误标识                 | 说明       | 触发场景                                    |
| :------ | :------------------- | :------- | :-------------------------------------- |
| `400`   | `BAD_REQUEST`        | 请求格式错误   | JSON解析失败、请求体为空                          |
| `401`   | `UNAUTHORIZED`       | 未认证      | 远程模式下未提供有效API Key                       |
| `404`   | `NOT_FOUND`          | 条目不存在    | GET/PUT/DELETE操作指定ID不存在                 |
| `409`   | `DUPLICATE_DETECTED` | 检测到重复条目  | POST /add 且 auto\_dedup=true 时检测到高相似度条目 |
| `409`   | `VERSION_CONFLICT`   | 版本冲突     | PUT /update 时version不匹配                  |
| `422`   | `VALIDATION_ERROR`   | 请求参数校验失败 | 缺少必填字段、类型不匹配等                           |
| `429`   | `RATE_LIMITED`       | 请求限流     | 超出API限流阈值（见7.5.10节）                     |

**服务端错误（5xx）**：

| HTTP状态码 | 错误标识                 | 说明       | 触发场景                                    |
| :------ | :------------------- | :------- | :-------------------------------------- |
| `500`   | `INTERNAL_ERROR`     | 服务内部错误   | 数据库异常、嵌入服务不可用等                          |
| `503`   | `SERVICE_DEGRADED`   | 服务降级     | Chroma不可用但SQLite正常，或嵌入模型降级              |
| `503`   | `SERVICE_SHUTTING_DOWN` | 服务关闭中  | 优雅关闭期间拒绝新请求                             |

#### 7.5.6 错误处理与重试策略

| 策略 | 适用场景 | 实现方式 |
| :--- | :--- | :--- |
| **自动重试** | 网络超时、临时服务不可用 | 指数退避重试（1s→2s→4s），最多3次，仅对5xx和超时错误重试 |
| **熔断机制** | 下游服务持续故障 | 连续5次失败后熔断30s，半开状态允许1次试探请求，成功则恢复 |
| **优雅降级** | Chroma不可用 | 自动降级为SQLite FTS5关键词检索，响应中标注`degraded: true` |
| **错误传播** | 客户端错误（4xx） | 直接返回错误响应，不重试，附带详细错误信息和建议操作 |

标准错误响应格式：

```json
{
  "error": {
    "code": "DUPLICATE_DETECTED",
    "message": "检测到高相似度条目 (similarity=0.95)",
    "details": {
      "existing_id": "kbid-20260429-abc123",
      "similarity_score": 0.95,
      "suggestion": "使用 PUT /v1/knowledge/update/{existing_id} 更新已有条目"
    },
    "retryable": false
  }
}
```

#### 7.5.7 认证规范

| 场景 | 认证方式 | 说明 |
| :--- | :--- | :--- |
| **本地开发（默认）** | 免认证 | 服务绑定`localhost:8765`，仅本机可访问，无需API Key |
| **本地开发（可选增强）** | API Key | 环境变量`KNOWLEDGE_API_KEY`设置后启用，请求头`X-API-Key`传递 |
| **远程/团队共享** | 强制API Key | 服务绑定`0.0.0.0`时强制启用API Key认证，无Key请求返回`401` |
| **MCP Tool调用** | 免认证 | MCP通过stdio传输，仅限本机Agent调用，无需额外认证 |

**API Key管理规范**：

| 管理项 | 规范 | 说明 |
| :--- | :--- | :--- |
| **Key生成** | `xks-`前缀 + 32字节随机十六进制 | 格式示例：`xks-a1b2c3d4e5f6...`，通过`xuansto-knowledge-server keygen`命令生成 |
| **Key存储** | 环境变量或`.env`文件 | 禁止硬编码到源代码或配置文件中，`.env`文件纳入`.gitignore` |
| **Key轮换** | 建议周期90天 | 通过`keygen`生成新Key后替换环境变量，旧Key保留7天过渡期 |
| **Key验证** | 常量时间比较（防时序攻击） | 使用`hmac.compare_digest()`而非`==`比较Key |

**权限范围**：

| 权限级别 | 可访问端点 | 适用场景 |
| :--- | :--- | :--- |
| **read-only** | `GET /v1/knowledge/*`, `POST /v1/knowledge/search` | CI/CD流水线、外部监控 |
| **read-write** | 所有端点 | 开发Agent、知识库管理工具 |
| **admin** | 所有端点 + `/v1/knowledge/admin/*` | 服务配置、备份管理、Key管理 |

> **安全建议**：生产环境中，API Key应通过环境变量或密钥管理服务注入，禁止硬编码。Key轮换周期建议为90天。远程部署时建议配合HTTPS和IP白名单使用。

#### 7.5.8 WebSocket实时通知接口

知识库服务通过WebSocket协议推送知识条目变更事件，供Agent和外部工具实时感知知识库状态变化。

**连接端点**：`ws://localhost:{port}/v1/knowledge/ws`

**事件类型**：

| 事件类型 | 触发条件 | 推送内容 |
| :--- | :--- | :--- |
| `knowledge.created` | 新增知识条目 | 条目ID、类型、分类、摘要 |
| `knowledge.updated` | 更新知识条目 | 条目ID、变更字段、新值摘要 |
| `knowledge.deleted` | 删除知识条目 | 条目ID、删除时间 |
| `knowledge.merged` | 知识条目合并 | 主条目ID、被合并条目ID、合并摘要 |
| `backup.completed` | 备份完成 | 备份类型、备份大小、耗时 |
| `service.degraded` | 服务降级 | 降级级别、降级原因 |

**消息格式**：

```json
{
  "event": "knowledge.created",
  "timestamp": "2026-04-29T10:30:00Z",
  "data": {
    "id": "KP-EXP-ERR-002",
    "type": "error-solution",
    "category": "database",
    "summary": "Redis连接池耗尽导致服务不可用"
  }
}
```

**重连策略**：

| 参数 | 值 | 说明 |
| :--- | :--- | :--- |
| 初始重连延迟 | 1秒 | 首次断连后等待时间 |
| 最大重连延迟 | 30秒 | 指数退避上限 |
| 退避因子 | 2 | 每次重连延迟翻倍 |
| 最大重连次数 | 10 | 超过后转为轮询健康检查 |

**订阅过滤**：客户端可在连接时通过查询参数指定订阅的事件类型和知识分类过滤：

```text
ws://localhost:{port}/v1/knowledge/ws?events=knowledge.created,knowledge.merged&category=database
```

#### 7.5.9 降级与容错

**ChromaDB不可用降级策略**：

当ChromaDB服务不可用（启动失败、连接超时、运行时崩溃）时，知识库服务自动降级为仅SQLite模式：

| 降级行为 | 说明 |
| :--- | :--- |
| **自动降级** | 检测到ChromaDB不可用时，立即切换为仅SQLite+FTS5检索模式 |
| **健康检查标记** | `/v1/knowledge/health` 响应中 `chroma_available: false`，标识当前处于降级状态 |
| **功能影响** | 语义向量检索不可用，仅支持BM25关键词检索；混合检索退化为纯FTS5检索 |
| **自动恢复** | 后台每30秒探测ChromaDB可用性，恢复后自动重新连接并重建索引 |
| **事件通知** | 通过WebSocket推送 `service.degraded` 事件，携带降级级别和原因 |

**SQLite损坏检测与恢复**：

| 检测机制 | 处理策略 |
| :--- | :--- |
| **启动时完整性检查** | 执行 `PRAGMA integrity_check`，若返回非 `ok` 则判定数据库损坏 |
| **备份恢复** | 从最近一次有效备份（`.knowledge/backup/`）恢复数据库文件 |
| **全量重新导入** | 若无可用备份，清空损坏数据库，从 `.knowledge/` Markdown文件全量重新导入 |
| **恢复后验证** | 恢复完成后重新执行完整性检查，确认数据库状态正常 |

**健康检查端点** `/v1/knowledge/health` 完整响应格式：

```json
{
  "status": "healthy",
  "chroma_available": true,
  "sqlite_integrity": "ok",
  "disk_usage": {
    "sqlite_bytes": 1048576,
    "chroma_bytes": 5242880
  },
  "active_connections": 3,
  "uptime_seconds": 86400
}
```

| 字段 | 类型 | 说明 |
| :--- | :--- | :--- |
| `status` | string | 服务状态：`healthy` / `degraded` / `unhealthy` |
| `chroma_available` | boolean | ChromaDB是否可用，`false` 表示处于降级模式 |
| `sqlite_integrity` | string | SQLite完整性检查结果：`ok` / `corrupted` |
| `disk_usage` | object | 磁盘使用情况，含 `sqlite_bytes` 和 `chroma_bytes` |
| `active_connections` | integer | 当前活跃连接数 |
| `uptime_seconds` | integer | 服务运行时长（秒） |

#### 7.5.10 API限流

**默认限流策略**：

| 参数 | 默认值 | 说明 |
| :--- | :--- | :--- |
| **限流维度** | 每IP | 按客户端IP地址限流 |
| **请求配额** | 60次/分钟 | 每IP每分钟允许的最大请求数 |
| **限流算法** | 滑动窗口 | 基于滑动时间窗口计数，避免固定窗口边界突发 |

**配置文件调整**：

限流参数可通过知识库服务配置文件（7.6.4节定义）的 `rate_limit` 段调整：

```yaml
rate_limit:
  enabled: true
  max_requests_per_minute: 60
  algorithm: "sliding_window"
```

**429 Too Many Requests响应格式**：

当请求超过限流配额时，返回HTTP 429状态码：

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "请求频率超过限制，请稍后重试",
    "retry_after": 30
  }
}
```

| 字段 | 类型 | 说明 |
| :--- | :--- | :--- |
| `error.code` | string | 错误码，固定为 `RATE_LIMIT_EXCEEDED` |
| `error.message` | string | 人类可读的错误描述 |
| `error.retry_after` | integer | 建议客户端等待的秒数后再重试 |

#### 7.5.11 双引擎数据一致性保障

知识库服务采用SQLite（结构化数据+全文检索）与Chroma（向量嵌入+语义检索）双引擎架构，需确保两引擎间数据一致性。

**写入事务边界**：
1. 写入操作遵循"SQLite先写→Chroma后写→失败补偿"策略
2. SQLite写入成功后，Chroma嵌入生成/写入若失败，条目标记为`embedding_status=pending`
3. 后台重试任务（间隔60秒，最多5次）在Chroma恢复后自动补齐pending状态的嵌入
4. 检索时对`embedding_status=pending`的条目降级为仅关键词检索（FTS5），不参与语义排序

**一致性校验流程**（服务启动时自动执行）：
1. 统计SQLite中`embedding_status=ready`的记录数，与Chroma向量数对比
2. 差异条目记录至`reconciliation_log`表
3. 自动修复：SQLite有记录但Chroma缺向量→补齐嵌入；Chroma有向量但SQLite无记录→标记为孤儿向量待清理
4. 校验结果写入`consistency_report`，可通过API查询

**故障恢复策略**：
| 故障场景 | 恢复策略 |
| :--- | :--- |
| SQLite写入成功，Chroma嵌入失败 | 条目标记pending，后台重试补齐 |
| SQLite写入失败 | 整个写入事务回滚，不触发Chroma操作 |
| Chroma服务不可用 | 所有新写入条目标记pending，检索降级为纯FTS5 |
| SQLite与Chroma数据不一致 | 启动时自动校验修复，无法自动修复的记录至reconciliation_log |

### 7.6 知识库服务管理

#### 7.6.1 服务实现方案

| 方案                 | 技术栈                        | 适用场景            | 优势               | 劣势        |
| :----------------- | :------------------------- | :-------------- | :--------------- | :-------- |
| **FastAPI HTTP服务** | Python + FastAPI + uvicorn | 多客户端、跨进程访问      | REST标准、调试方便、生态丰富 | 需额外进程管理   |
| **MCP Server**     | Python + mcp-sdk           | Agent原生调用、IDE集成 | 零HTTP开销、原生Tool接口 | 仅MCP客户端可用 |

> **推荐方案**：默认使用FastAPI HTTP服务，同时暴露MCP Tool接口。两者共享同一服务实例，FastAPI处理外部HTTP请求，MCP Server处理Agent内部调用。

#### 7.6.2 服务启动流程

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                        知识库服务启动流程                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐                                                            │
│  │ 服务启动     │  xuansto-knowledge-server start                            │
│  └──────┬──────┘                                                            │
│         │                                                                   │
│         ▼                                                                   │
│  ┌─────────────┐     ┌─────────────────────────────────────────────────┐   │
│  │ 检测配置     │────▶│ 读取 .knowledge/config.yaml                      │   │
│  │             │     │ 获取: port, embedding_model, dedup_threshold等   │   │
│  └──────┬──────┘     └─────────────────────────────────────────────────┘   │
│         │                                                                   │
│         ▼                                                                   │
│  ┌─────────────┐     ┌─────────────────────────────────────────────────┐   │
│  │ 初始化SQLite │────▶│ 检查 .knowledge/index/knowledge.db              │   │
│  │             │     │ 不存在 → 创建表结构 + 索引 + FTS5 + 触发器        │   │
│  └──────┬──────┘     └─────────────────────────────────────────────────┘   │
│         │                                                                   │
│         ▼                                                                   │
│  ┌─────────────┐     ┌─────────────────────────────────────────────────┐   │
│  │ 初始化Chroma │────▶│ 检查 .knowledge/index/chroma_data/              │   │
│  │             │     │ 不存在 → 创建 xuansto_knowledge Collection       │   │
│  └──────┬──────┘     └─────────────────────────────────────────────────┘   │
│         │                                                                   │
│         ▼                                                                   │
│  ┌─────────────┐     ┌─────────────────────────────────────────────────┐   │
│  │ 首次运行检测 │────▶│ SQLite entry_count == 0?                        │   │
│  │             │     │ 是 → 触发首次导入（First-Run Import）            │   │
│  └──────┬──────┘     └─────────────────────────────────────────────────┘   │
│         │                                                                   │
│         ▼                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 首次导入 (First-Run Import)                                          │   │
│  │  1. 扫描 .knowledge/ 下所有 *.md 文件                                │   │
│  │  2. 解析 YAML Frontmatter → 提取元数据                               │   │
│  │  3. 提取 Markdown正文 → 生成summary                                  │   │
│  │  4. 写入 SQLite (knowledge_entries + knowledge_tags + knowledge_fts) │   │
│  │  5. 生成向量嵌入 → 写入 Chroma Collection                            │   │
│  │  6. 记录导入日志 → .knowledge/sync-log.md                            │   │
│  └──────────┬──────────────────────────────────────────────────────────┘   │
│             │                                                               │
│             ▼                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 双引擎数据一致性校验                                                 │   │
│  │  7. 执行双引擎数据一致性校验（见7.5.11节），自动修复差异条目          │   │
│  └──────────┬──────────────────────────────────────────────────────────┘   │
│             │                                                               │
│             ▼                                                               │
│  ┌─────────────┐                                                            │
│  │ 启动监听     │  FastAPI: http://localhost:8765                            │
│  │             │  MCP: stdio transport                                       │
│  └─────────────┘                                                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 7.6.3 首次导入实现

**函数契约**：`first_run_import(knowledge_dir: Path, db: KnowledgeDB, chroma: ChromaClient) -> None`
- 输入：知识库Markdown目录路径、SQLite数据库实例、Chroma客户端实例
- 输出：无返回值（副作用：将Markdown文件解析后写入SQLite和Chroma，记录版本历史）

> **参考实现**：以下Python代码为参考实现，需求定义见上文首次导入流程。

```python
import frontmatter
from pathlib import Path

async def first_run_import(knowledge_dir: Path, db: KnowledgeDB, chroma: ChromaClient):
    md_files = list(knowledge_dir.rglob("*.md"))
    imported, skipped, errors = 0, 0, 0

    for md_file in md_files:
        try:
            post = frontmatter.load(str(md_file))
            metadata = post.metadata
            content = post.content

            summary = generate_summary(content, max_length=500)
            relative_path = md_file.relative_to(knowledge_dir)

            entry_id = metadata.get("id", generate_id_from_path(relative_path))

            db.insert_entry(
                id=entry_id,
                type=metadata.get("type", "unknown"),
                category=metadata.get("category", "uncategorized"),
                tags=metadata.get("tags", []),
                confidence=metadata.get("confidence", 0.5),
                source=metadata.get("source", ""),
                content_path=str(relative_path),
                summary=summary,
                created=metadata.get("created", ""),
                updated=metadata.get("updated", ""),
                last_validated=metadata.get("last_validated"),
                success_count=metadata.get("success_count", 0),
                failure_count=metadata.get("failure_count", 0),
                occurrences=metadata.get("occurrences", 1),
                version=1,
            )

            chroma.add_document(
                doc_id=entry_id,
                document=summary,
                metadata={
                    "id": entry_id,
                    "type": metadata.get("type", "unknown"),
                    "category": metadata.get("category", "uncategorized"),
                    "confidence": metadata.get("confidence", 0.5),
                    "source": metadata.get("source", ""),
                },
            )

            db.add_version_history(
                entry_id=entry_id,
                version=1,
                content_snapshot=content,
                change_type="create",
            )

            imported += 1
        except Exception as e:
            errors += 1
            log_import_error(md_file, str(e))

    log_sync(f"首次导入完成: 导入{imported}, 跳过{skipped}, 错误{errors}")
```

#### 7.6.4 配置文件定义

```yaml
# .knowledge/config.yaml — 知识库服务配置（在8.7.2基础上扩展）
knowledge_base:
  version: "1.7.0"
  last_sync: "2026-04-29T08:00:00Z"

  server:
    enabled: true
    host: "127.0.0.1"
    port: 8765
    transport: "http+mcp"              # http | mcp | http+mcp
    log_level: "INFO"

  database:
    sqlite_path: ".knowledge/index/knowledge.db"
    chroma_path: ".knowledge/index/chroma_data"

  embedding:
    primary_model: "text-embedding-3-small"
    fallback_model: "all-MiniLM-L6-v2"
    strategy: "primary_with_fallback"
    batch_size: 100
    cache_enabled: true

  retrieval:
    default_strategy: "hybrid"
    hybrid:
      semantic_weight: 0.6
      keyword_weight: 0.4
      rrf_k: 60
      top_k: 5
      candidate_multiplier: 2
    semantic_only:
      top_k: 5
      min_similarity: 0.3
    keyword_only:
      top_k: 5

  dedup:
    enabled: true
    similarity_threshold: 0.92          # 语义相似度阈值
    metadata_hash_fields:               # 元数据哈希比对字段
      - type
      - category
      - tags
    auto_merge: false                   # 自动合并（需人工确认）

  sync:
    watch_enabled: true                 # 监控文件变更
    watch_interval_seconds: 30
    full_sync_on_startup: false         # 启动时全量同步（首次导入后关闭）
```

#### 7.6.5 服务生命周期

| 阶段         | 触发条件               | 执行动作                                         |
| :--------- | :----------------- | :------------------------------------------- |
| **启动**     | 项目会话开始 / 手动启动      | 初始化数据库→首次导入检测→启动HTTP/MCP监听                   |
| **运行**     | Agent调用 / 外部请求     | 处理检索/增删改请求→文件变更监控→增量同步                       |
| **降级**     | Chroma不可用 / 嵌入模型失败 | 标记`embedding_degraded`→回退SQLite FTS5检索       |
| **停止**     | 项目会话结束 / 手动停止      | 写入同步日志→关闭数据库连接→持久化Chroma数据                   |
| **跨会话持久化** | 会话间                | SQLite文件和Chroma数据目录持久保存在 `.knowledge/index/` |

#### 7.6.6 备份与灾备

| 备份对象 | 备份策略 | 备份频率 | 恢复RTO | 存储位置 |
| :--- | :--- | :--- | :--- | :--- |
| **SQLite数据库** | 自动定时备份（`sqlite3 .backup` API） | 每6小时一次 | < 5分钟 | `.knowledge/backups/sqlite/` |
| **Chroma数据目录** | 目录级压缩备份（tar.gz） | 每日一次 | < 15分钟 | `.knowledge/backups/chroma/` |
| **Markdown源文件** | Git版本控制（已有机制） | 每次提交 | < 1分钟 | Git仓库 |

**手动备份触发**：通过API端点 `POST /v1/knowledge/backup` 或命令 `xuansto-knowledge-server backup` 可手动触发全量备份。

**灾备恢复流程**：

```text
1. 停止知识库服务
2. 从备份目录复制SQLite数据库文件覆盖当前文件
3. 从备份目录解压Chroma数据目录覆盖当前目录
4. 执行一致性校验（entry_count比对）
5. 重启服务并验证健康检查端点
```

**备份保留策略**：SQLite备份保留最近10份，Chroma备份保留最近7份，超期自动清理。

#### 7.6.7 并发访问控制

| 场景 | 策略 | 冲突处理 |
| :--- | :--- | :--- |
| **多Agent同时写入不同条目** | 无锁并行写入 | 无冲突 |
| **多Agent同时写入同一条目** | 乐观锁（基于version字段） | 后写入者检测version不匹配，返回409 Conflict，需重新读取后重试 |
| **写入与检索并发** | 读写不阻塞（SQLite WAL模式） | 检索可能返回稍旧数据 |
| **批量导入与单条写入并发** | 批量导入使用事务锁 | 单条写入等待事务完成 |

**冲突日志**：所有写入冲突记录到 `dedup_log` 表的 `conflict_type='write_conflict'` 条目中，包含冲突双方的Agent ID和时间戳。

**最后写入胜出规则**：当乐观锁重试3次仍失败时，采用最后写入胜出（Last Write Wins）策略，但保留被覆盖条目的版本快照到 `version_history` 表。

#### 7.6.8 优雅关闭流程

```text
知识库服务优雅关闭流程：

1. 接收SIGTERM/SIGINT信号或用户执行 stop 命令
2. 停止接受新请求（返回503 Service Unavailable）
3. 等待当前进行中的请求完成（超时阈值：30秒）
4. 将内存中未持久化的变更刷写到SQLite数据库
5. 执行Chroma数据目录的最终同步
6. 关闭SQLite数据库连接
7. 关闭Chroma客户端连接
8. 关闭HTTP服务器
9. 输出关闭日志并退出进程（exit code 0）
```

**超时强制关闭**：若步骤3等待超过30秒，记录未完成请求日志后强制关闭（exit code 1）。

#### 7.6.9 API版本化策略

| 版本 | 路径前缀 | 状态 | 兼容承诺 |
| :--- | :--- | :--- | :--- |
| **v1** | `/v1/knowledge/*` | 当前稳定版 | 至少维护到v1.9.0发布 |
| **v2** | `/v2/knowledge/*` | 规划中 | 引入批量操作和流式响应 |

**版本化规则**：
- 所有API端点默认包含版本前缀（如 `/v1/knowledge/search`）
- 不兼容变更必须递增主版本号，在新版本路径下提供
- 旧版本API至少维护2个次版本周期
- 健康检查端点（`/health`）不纳入版本化，始终可用

**7.5.1节REST API端点更新**：所有端点路径应加上`/v1`前缀，即：

| 方法 | 路径 | 说明 | 认证 |
| :--- | :--- | :--- | :--- |
| `POST` | `/v1/knowledge/search` | 混合检索 | 无（本地服务） |
| `GET` | `/v1/knowledge/get/{id}` | 获取指定条目 | 无 |
| `POST` | `/v1/knowledge/add` | 新增条目（自动去重） | 无 |
| `PUT` | `/v1/knowledge/update/{id}` | 更新条目 | 无 |
| `DELETE` | `/v1/knowledge/delete/{id}` | 删除条目 | 无 |
| `GET` | `/v1/knowledge/health` | 健康检查 | 无 |
| `POST` | `/v1/knowledge/backup` | 手动触发备份 | 无 |

#### 7.6.10 资源限制配置

知识库服务支持配置资源使用上限，防止单个服务实例占用过多系统资源：

| 资源维度 | 默认值 | 配置键 | 说明 |
| :--- | :--- | :--- | :--- |
| **内存限制** | 512MB | `resource_limits.max_memory_mb` | 服务进程最大内存占用，超出时触发告警并拒绝新请求 |
| **数据库大小限制** | 1GB | `resource_limits.max_db_size_mb` | SQLite数据库文件最大大小，超出时拒绝写入操作 |
| **并发连接数限制** | 20 | `resource_limits.max_connections` | 最大同时活跃连接数，超出返回503 Service Unavailable |

**配置示例**：

```yaml
resource_limits:
  max_memory_mb: 512
  max_db_size_mb: 1024
  max_connections: 20
```

**Runtime Supervisor监控集成**：

资源使用指标通过 `/v1/knowledge/health` 健康检查端点暴露，供Runtime Supervisor定期采集：

| 监控指标 | 采集方式 | 告警阈值 |
| :--- | :--- | :--- |
| 内存使用率 | 进程RSS / `max_memory_mb` | >80% 告警，>95% 拒绝新请求 |
| 数据库大小 | SQLite文件大小 / `max_db_size_mb` | >80% 告警，>95% 拒绝写入 |
| 活跃连接数 | 当前连接数 / `max_connections` | >80% 告警，100% 返回503 |

#### 7.6.11 日志配置

**日志格式**：结构化JSON，每条日志包含以下字段：

```json
{
  "timestamp": "2026-04-29T10:30:00.123Z",
  "level": "INFO",
  "module": "knowledge.search",
  "message": "混合检索完成，返回12条结果"
}
```

| 字段 | 类型 | 说明 |
| :--- | :--- | :--- |
| `timestamp` | string | ISO8601格式时间戳，精确到毫秒 |
| `level` | string | 日志级别：`DEBUG` / `INFO` / `WARN` / `ERROR` |
| `module` | string | 产生日志的模块标识，如 `knowledge.search`、`knowledge.import`、`knowledge.health` |
| `message` | string | 日志消息内容 |

**日志级别**：

| 级别 | 用途 | 示例 |
| :--- | :--- | :--- |
| **DEBUG** | 详细调试信息，仅开发环境启用 | SQL查询语句、嵌入向量维度 |
| **INFO** | 常规运行信息（默认级别） | 服务启动、检索完成、导入成功 |
| **WARN** | 警告信息，不影响运行但需关注 | 接近资源限制、降级模式切换 |
| **ERROR** | 错误信息，影响功能正常运行 | 数据库写入失败、ChromaDB连接超时 |

默认日志级别为 `INFO`，可通过配置文件 `logging.level` 调整。

**存储路径**：`.knowledge/logs/knowledge-server.log`

**轮转策略**：

| 参数 | 值 | 说明 |
| :--- | :--- | :--- |
| **大小轮转** | 10MB | 单个日志文件达到10MB时触发轮转 |
| **保留文件数** | 5 | 保留最近5个轮转日志文件，超出自动删除最旧文件 |
| **命名规则** | `knowledge-server.log.1`、`knowledge-server.log.2`... | 轮转后文件按序号递增命名 |

### 7.7 知识去重与智能更新

#### 7.7.1 去重检测流程

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                        知识去重检测流程                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐                                                            │
│  │ 新知识条目   │  content + metadata                                        │
│  └──────┬──────┘                                                            │
│         │                                                                   │
│         ▼                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Step 1: Chroma语义相似度检索                                         │   │
│  │  query = new_entry.summary                                          │   │
│  │  n_results = 3                                                      │   │
│  │  → 获取最相似的3条已有条目                                            │   │
│  └──────────┬──────────────────────────────────────────────────────────┘   │
│             │                                                               │
│             ▼                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Step 2: 相似度阈值判断                                               │   │
│  │  max_similarity < 0.92?                                             │   │
│  │  → 是: 判定为新条目，直接写入（跳过去重）                              │   │
│  │  → 否: 进入Step 3                                                   │   │
│  └──────────┬──────────────────────────────────────────────────────────┘   │
│             │                                                               │
│             ▼                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Step 3: 元数据哈希比对                                               │   │
│  │  hash = hash(type + category + sorted(tags))                        │   │
│  │  new_hash == existing_hash?                                         │   │
│  │  → 是: 确认重复，执行 skip 或 merge                                  │   │
│  │  → 否: 相似但不同维度，执行 keep_both                                │   │
│  └──────────┬──────────────────────────────────────────────────────────┘   │
│             │                                                               │
│      ┌──────┼──────┐                                                        │
│      ▼      ▼      ▼                                                        │
│  ┌──────┐┌──────┐┌──────────┐                                               │
│  │ skip ││merge ││keep_both │                                               │
│  │跳过  ││合并  ││两者保留  │                                                │
│  └──────┘└──┬───┘└──────────┘                                               │
│             │                                                               │
│             ▼                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 合并策略 (Merge)                                                    │   │
│  │  1. 保留更高confidence的条目作为主条目                                │   │
│  │  2. 合并增量信息（新案例、新发现）到主条目                             │   │
│  │  3. 更新 timestamps 和 counters                                     │   │
│  │  4. 记录 version_history (change_type="merge")                      │   │
│  │  5. 写入 dedup_log                                                  │   │
│  │  6. 写入 sync-log.md                                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 7.7.2 合并策略详细规则

| 规则        | 说明                                               | 示例                                                               |
| :-------- | :----------------------------------------------- | :--------------------------------------------------------------- |
| **主条目选择** | 保留 `confidence` 更高的条目为主                          | 0.98 > 0.85 → 保留0.98条目                                           |
| **摘要合并**  | 主条目摘要保留，补充新条目的独有信息                               | 主条目+"新增预热方案"                                                     |
| **标签合并**  | 取并集，去重                                           | `["pg","timeout"]` ∪ `["pg","pool"]` = `["pg","timeout","pool"]` |
| **计数器合并** | `success_count`、`failure_count`、`occurrences` 累加 | 3+2=5                                                            |
| **置信度更新** | 取加权平均，权重为各自occurrences                           | (0.98×5 + 0.85×2) / 7 = 0.94                                     |
| **时间戳**   | `created` 取较早者，`updated` 取当前时间                   | —                                                                |

#### 7.7.3 版本追踪与回滚

每次知识条目更新（包括merge操作）都会在 `version_history` 表中创建一条记录：

**函数契约**：`update_with_version(entry_id: str, updates: dict, change_type: str) -> None`
- 输入：条目ID、更新字段字典、变更类型（"update" | "merge" | "rollback"）
- 输出：无返回值（副作用：记录版本历史并更新条目版本号）

> **参考实现**：以下Python代码为参考实现，需求定义见上文版本追踪与回滚流程。

```python
async def update_with_version(
    entry_id: str,
    updates: dict,
    change_type: str,  # "update" | "merge" | "rollback"
):
    current = db.get_entry(entry_id)
    new_version = current.version + 1

    db.add_version_history(
        entry_id=entry_id,
        version=current.version,
        content_snapshot=current.summary,
        change_type=change_type,
    )

    db.update_entry(entry_id, {
        **updates,
        "version": new_version,
        "updated": datetime.utcnow().isoformat(),
    })
```

**回滚操作**：

**函数契约**：`rollback_entry(entry_id: str, target_version: int) -> KnowledgeEntry`
- 输入：条目ID、目标版本号
- 输出：回滚后的知识条目对象（版本号递增，内容恢复为目标版本快照）

> **参考实现**：以下Python代码为参考实现，需求定义见上文版本追踪与回滚流程。

```python
async def rollback_entry(entry_id: str, target_version: int) -> KnowledgeEntry:
    history = db.get_version_history(entry_id, target_version)
    if not history:
        raise ValueError(f"Version {target_version} not found for {entry_id}")

    current = db.get_entry(entry_id)

    db.add_version_history(
        entry_id=entry_id,
        version=current.version,
        content_snapshot=current.summary,
        change_type="rollback",
    )

    restored = db.update_entry(entry_id, {
        "summary": history.content_snapshot,
        "version": current.version + 1,
        "updated": datetime.utcnow().isoformat(),
    })

    await reindex_chroma(entry_id, history.content_snapshot)

    return restored
```

#### 7.7.4 同步日志

所有去重/合并操作均记录到 `.knowledge/sync-log.md`，确保操作可审计：

```markdown
# 知识库同步日志

## 2026-04-29

### 10:30:00 — 首次导入
- 扫描文件: 42个Markdown文件
- 导入成功: 40条
- 跳过(格式错误): 2条
- 生成嵌入: 40条 (text-embedding-3-small)

### 14:22:00 — 去重检测
- 新条目: KP-EXP-ERR-003 "Redis连接池耗尽"
- 匹配已有: KP-EXP-ERR-001 (相似度: 0.72)
- 判定: keep_both (元数据哈希不同: database/redis vs database/postgresql)
- 操作: 两者保留

### 15:10:00 — 合并操作
- 新条目: KP-EXP-ERR-004 "PG连接超时(补充案例)"
- 匹配已有: KP-EXP-ERR-001 (相似度: 0.95)
- 元数据哈希匹配: type=error-solution, category=database, tags匹配
- 判定: merge
- 主条目: KP-EXP-ERR-001 (confidence: 0.98 > 0.85)
- 合并内容: 新增"连接池预热方案"案例
- 版本: v1 → v2
```

#### 7.7.5 去重与更新流程总览

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                    知识去重与智能更新总流程                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐                  │
│  │ 新知识写入   │────▶│ 去重检测     │────▶│ 判定结果     │                  │
│  └─────────────┘     │ Chroma>0.92?│     │ skip/merge/ │                  │
│                      │ 元数据哈希?  │     │ keep_both   │                  │
│                      └─────────────┘     └──────┬──────┘                  │
│                                                 │                          │
│                    ┌────────────────────────────┼───────────────────┐     │
│                    │                            │                   │     │
│                    ▼                            ▼                   ▼     │
│             ┌───────────┐              ┌──────────────┐    ┌──────────┐  │
│             │ skip      │              │ merge        │    │keep_both │  │
│             │ 不写入    │              │ 智能合并      │    │ 两者保留 │  │
│             │ 记录日志  │              │ 版本追踪      │    │ 各自独立 │  │
│             └───────────┘              │ 计数器累加    │    └──────────┘  │
│                                        │ 置信度重算    │                   │
│                                        └──────┬───────┘                   │
│                                               │                           │
│                                               ▼                           │
│                                        ┌──────────────┐                   │
│                                        │ 双引擎同步    │                   │
│                                        │ SQLite更新    │                   │
│                                        │ Chroma重嵌入  │                   │
│                                        │ FTS5重建索引  │                   │
│                                        │ sync-log记录  │                   │
│                                        └──────┬───────┘                   │
│                                               │                           │
│                                               ▼                           │
│                                        ┌──────────────┐                   │
│                                        │ 版本历史      │                   │
│                                        │ 可回滚任意版本│                   │
│                                        └──────────────┘                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 7.8 知识库安全规范

#### 7.8.1 数据安全

| 安全维度 | 规范 | 说明 |
| :--- | :--- | :--- |
| **本地存储加密** | SQLite数据库文件权限设为0600 | 仅服务进程可读写，防止其他用户直接访问 |
| **敏感内容过滤** | 写入前执行敏感信息检测 | 检测API Key、密码、Token等模式，匹配则拒绝写入并告警 |
| **备份加密** | 备份文件使用AES-256加密 | 防止备份文件泄露导致知识库内容暴露 |
| **日志脱敏** | 日志中不记录条目完整内容 | 仅记录条目ID、操作类型、时间戳，不记录正文 |

#### 7.8.2 访问控制

| 控制维度 | 规范 | 说明 |
| :--- | :--- | :--- |
| **服务绑定** | 默认绑定 `127.0.0.1:8765` | 仅本地访问，不暴露到网络 |
| **CORS策略** | 禁止跨域请求 | 本地服务无需CORS，默认拒绝所有Origin |
| **输入校验** | 所有API端点执行参数校验 | 防止SQL注入、路径遍历、XSS等攻击 |

### 7.9 服务测试规范

> **设计意图**：知识库服务作为Skill运行时的核心基础设施，其可靠性直接影响多Agent协作的成败。本节定义四类测试规范，确保API端点正确性、双引擎一致性、降级容错有效性和并发安全性。

#### 7.9.1 API端点单元测试

| 测试类别 | 测试用例 | 预期结果 |
| :--- | :--- | :--- |
| **检索接口** | `POST /v1/knowledge/search` 正常混合检索 | 返回status=ok，结果按rrf_score降序排列 |
| **检索接口** | `POST /v1/knowledge/search` 仅BM25模式（search_type=keyword） | 不调用Chroma，仅返回FTS5结果 |
| **检索接口** | `POST /v1/knowledge/search` 空查询字符串 | 返回422 Validation Error |
| **检索接口** | `POST /v1/knowledge/search` top_k超出范围（>100或<1） | 返回422 Validation Error |
| **获取接口** | `GET /v1/knowledge/get/{id}` 存在的条目 | 返回完整条目数据 |
| **获取接口** | `GET /v1/knowledge/get/{id}` 不存在的条目 | 返回404 Not Found |
| **新增接口** | `POST /v1/knowledge/add` 正常新增 | 返回201 Created，SQLite和Chroma均写入 |
| **新增接口** | `POST /v1/knowledge/add` 重复条目（相似度>阈值） | 触发去重，返回200 + merge/skip决策 |
| **更新接口** | `PUT /v1/knowledge/update/{id}` 正常更新 | 版本号递增，version_history记录快照 |
| **更新接口** | `PUT /v1/knowledge/update/{id}` version冲突 | 返回409 Conflict |
| **删除接口** | `DELETE /v1/knowledge/delete/{id}` 正常删除 | SQLite和Chroma均删除，级联删除tags |
| **健康检查** | `GET /v1/knowledge/health` 正常状态 | 返回status=healthy，chroma_available=true |
| **健康检查** | `GET /v1/knowledge/health` Chroma不可用 | 返回status=degraded，chroma_available=false |

> **参考实现**：完整代码见 `knowledge_server/tests/test_api_endpoints.py`，以下为关键测试接口与逻辑摘要。

```python
# 测试接口定义
@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as c:
        yield c

# 关键测试逻辑摘要
async def test_search_hybrid(client):
    # 验证混合检索返回200，结果按rrf_score降序

async def test_search_empty_query(client):
    # 验证空查询返回422

async def test_add_and_dedup(client):
    # 验证新增返回201，重复新增触发去重(200 + skip/merge)

async def test_update_version_conflict(client):
    # 验证版本冲突返回409

async def test_health_check(client):
    # 验证健康检查返回healthy或degraded，包含chroma_available和sqlite_integrity
```

#### 7.9.2 SQLite+Chroma双引擎集成测试

| 测试类别 | 测试用例 | 预期结果 |
| :--- | :--- | :--- |
| **写入一致性** | 新增条目后，SQLite和Chroma均可检索到 | 两个引擎返回相同条目ID |
| **删除一致性** | 删除条目后，SQLite和Chroma均无该条目 | 两个引擎检索结果均不包含已删除条目 |
| **更新一致性** | 更新条目后，SQLite和Chroma的summary同步更新 | 两个引擎检索返回更新后的summary |
| **首次导入** | 首次启动服务，扫描Markdown文件导入 | 导入条目数与Markdown文件数一致，SQLite和Chroma条目数相同 |
| **FTS5与语义检索对比** | 对同一查询分别执行keyword和semantic检索 | keyword检索匹配关键词，semantic检索匹配语义相似内容 |
| **混合检索融合** | 执行hybrid检索，验证RRF融合排序 | 结果包含BM25和语义检索的融合排序，rrf_score计算正确 |

> **参考实现**：完整代码见 `knowledge_server/tests/test_dual_engine.py`，以下为关键测试接口与逻辑摘要。

```python
# 测试接口定义
@pytest.fixture
def stores(tmp_path):
    sqlite = SQLiteStore(str(tmp_path / "test.db"))
    chroma = ChromaStore(persist_dir=str(tmp_path / "chroma"))
    return sqlite, chroma

# 关键测试逻辑摘要
def test_write_consistency(stores):
    # 验证upsert后SQLite和Chroma均可检索到相同条目ID

def test_delete_consistency(stores):
    # 验证delete后SQLite和Chroma均无该条目

def test_update_consistency(stores):
    # 验证upsert更新后SQLite和Chroma的summary同步更新
```

#### 7.9.3 降级场景测试

| 测试类别 | 测试用例 | 预期结果 |
| :--- | :--- | :--- |
| **ChromaDB启动失败** | 启动时ChromaDB不可用 | 服务正常启动，健康检查返回degraded，检索降级为FTS5 |
| **ChromaDB运行时崩溃** | 运行中模拟ChromaDB进程终止 | 自动降级为FTS5，WebSocket推送service.degraded事件 |
| **ChromaDB自动恢复** | 降级后模拟ChromaDB恢复 | 30秒内自动重连，健康检查恢复healthy |
| **SQLite损坏恢复** | 模拟SQLite数据库文件损坏 | 从备份恢复，无备份则全量重新导入 |
| **SQLite无备份恢复** | 损坏且无可用备份 | 清空数据库，从Markdown文件全量重新导入 |
| **双重故障** | SQLite和Chroma同时不可用 | 返回503 Service Unavailable，记录错误日志 |

> **参考实现**：完整代码见 `knowledge_server/tests/test_degradation.py`，以下为关键测试接口与逻辑摘要。

```python
# 关键测试逻辑摘要
async def test_chroma_unavailable_on_startup(client):
    # patch ChromaStore.initialize抛出ConnectionError，验证health返回degraded

async def test_degraded_search_fallback(client):
    # patch ChromaStore.query抛出ConnectionError，验证检索降级为keyword模式

async def test_chroma_auto_recovery(client):
    # 模拟ChromaDB前2次调用失败第3次成功，验证自动恢复为hybrid模式

async def test_sqlite_corruption_recovery(client, tmp_path):
    # 模拟SQLite文件损坏，验证健康检查返回corrupted状态
```

#### 7.9.4 并发写入测试

| 测试类别 | 测试用例 | 预期结果 |
| :--- | :--- | :--- |
| **多Agent并行写入不同条目** | 10个并发请求写入不同ID条目 | 全部成功（201），无数据丢失 |
| **多Agent并行写入同一条目** | 5个并发请求更新同一条目 | 仅1个成功，其余返回409 Conflict |
| **读写并发** | 写入同时执行检索 | 检索不阻塞，返回一致快照 |
| **乐观锁重试** | version冲突后自动重试 | 重试最多3次，仍失败则Last Write Wins |
| **批量导入与单条写入并发** | 批量导入进行时执行单条写入 | 单条写入等待事务完成后成功 |

> **参考实现**：完整代码见 `knowledge_server/tests/test_concurrency.py`，以下为关键测试接口与逻辑摘要。

```python
# 关键测试逻辑摘要
async def test_concurrent_write_different_entries(client):
    # 10个并发POST /add不同ID，验证全部返回201

async def test_concurrent_write_same_entry(client):
    # 5个并发PUT /update同一条目，验证仅1个成功(200)，其余409 Conflict

async def test_read_write_concurrency(client):
    # 并发执行PUT更新和GET读取，验证读取不阻塞且返回一致快照

async def test_optimistic_lock_retry(client):
    # 验证version冲突返回409，重试机制最多3次
```
