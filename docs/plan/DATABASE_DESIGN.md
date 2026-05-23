# xuansto-skill 数据存储设计文档

> 版本: 2.0.0 | 更新日期: 2026-05-23 | 状态: 已实施

---

## 目录

1. [当前数据存储盘点](#1-当前数据存储盘点)
2. [持久化/缓存数据实体清单](#2-持久化缓存数据实体清单)
3. [数据生命周期](#3-数据生命周期)
4. [重构后数据模型](#4-重构后数据模型)
5. [数据迁移策略](#5-数据迁移策略)
6. [存储技术选型建议](#6-存储技术选型建议)
7. [问题清单](#7-问题清单)

---

## 1. 当前数据存储盘点

### 1.1 存储介质总览

| 介质 | 数量 | 用途 | 一致性保障 |
|------|------|------|-----------|
| SQLite (WAL) | 1 | 统一存储(xuansto.db, 8表) | PRAGMA journal_mode=WAL + busy_timeout=5000 + 写入锁 |
| ChromaDB (PersistentClient) | 1 (可选) | 向量语义搜索(可选增强) | PersistentClient 本地持久化, HybridSearchEngine自动检测 |
| JSON 文件 | ~8类 | 会话状态、工作流状态、资源加载状态、降级状态、指标快照、模式文件 | atomic_write (tmpfile+os.replace) |
| YAML 文件 | ~4类 | 技能配置、降级配置、Hook配置、工作流定义 | 直接读写 |
| Markdown 文件 | ~3类 | 会话记录、知识文档、参考文档 | 直接读写 |
| 内存缓存 | ~8类 | 资源缓存、Token指标、降级组件状态、工作流活跃实例、决策缓存 | threading.Lock / RLock |
| 环境变量 | 3 | SKILL_ROOT、XUANSTO_WORK_DIR、ECC_HOOK_PROFILE | OS 级别 |
| gzip 压缩文件 | 1 | 工作流快照 | tempfile+os.replace |

### 1.2 目录结构映射

```
项目根目录/
├── .trae/skills/xuansto-skill-v2/          # SKILL_ROOT (技能根目录)
│   ├── .skill-config.yaml                   # 技能配置
│   ├── .xuansto-config.yaml                 # 自定义配置覆盖
│   ├── constraints.yaml                     # Token预算/降级/Disclosure配置
│   ├── hooks/hooks.json                     # Hook定义
│   ├── references/*.md                      # 参考文档
│   ├── agents/**/*.md                       # Agent定义
│   ├── workflows/*.md                       # 工作流定义(YAML frontmatter)
│   ├── templates/*.md                       # 模板文件
│   └── scripts/*.py                         # 降级脚本
│
├── .xuansto/                                # WORK_DIR (运行时工作目录)
│   ├── xuansto.db                           # 统一SQLite存储(8表, WAL模式)
│   ├── sessions/                            # 会话持久化
│   │   ├── session-{timestamp}.md           # 会话快照
│   │   └── current.json                     # 当前追踪状态
│   ├── patterns/                            # 错误模式
│   │   └── pattern-{timestamp}.json
│   ├── workflows/                           # 工作流实例
│   │   └── {workflow_id}.json
│   ├── workflow_snapshots/                  # 工作流快照(项目级)
│   └── metrics_{timestamp}.json             # 指标快照(旧格式,已迁移到xuansto.db)
│
├── .xuansto/workflow_snapshots/             # 工作流快照(项目级)
│   └── {workflow_id}_phase{N}_{ts}.json.gz
│
└── xuansto-mcp-server/src/xuansto_mcp/data/ # MCP Server 数据目录
    ├── fallback_config.yaml                 # 降级配置
    └── knowledge/                           # 知识库
        ├── general/                         # 通用知识
        ├── workspace/                       # 工作区知识
        ├── experience/                      # 经验沉淀
        └── index/                           # 索引
            └── chroma_db/                   # ChromaDB向量索引(可选)
```

### 1.3 关键路径解析逻辑

路径解析采用多级回退策略 (参见 [config.py](../../xuansto-mcp-server/src/xuansto_mcp/core/config.py)):

1. **SKILL_ROOT**: 环境变量 `SKILL_ROOT` / `XUANSTO_SKILL_ROOT` → `.trae/skills/xuansto-skill-v2/` → `DATA_DIR`
2. **WORK_DIR**: 环境变量 `XUANSTO_WORK_DIR` → `{project_root}/.xuansto/`
3. **配置文件**: `_resolve_skill_file()` 先查 SKILL_ROOT，再回退 DATA_DIR

---

## 2. 持久化/缓存数据实体清单

### 2.1 知识库条目 (knowledge_entries)

**存储**: xuansto.db (统一SQLite) + ChromaDB (可选, `chroma_db/`) + Markdown 文件

```json
{
  "id": "injected-20260523T120000Z",
  "title": "injected-20260523T120000Z",
  "content": "知识内容文本...",
  "type": "general | workspace | experience",
  "metadata_json": "{\"source\": \"mcp_inject\"}",
  "created_at": "2026-05-23T12:00:00+00:00",
  "updated_at": "2026-05-23T12:00:00+00:00",
  "deleted_at": null
}
```

**FTS5 虚拟表**: `knowledge_fts` (content, title, type, tokenize='unicode61') — 位于 xuansto.db

**ChromaDB 集合**: `knowledge` (ids, documents, metadatas) — 可选，HybridSearchEngine自动检测

**Markdown 文件** (注入时生成):
```yaml
---
type: injected
knowledge_type: general
injected_at: 20260523T120000Z
metadata: {"source": "mcp_inject"}
---
知识内容文本...
```

### 2.2 决策日志 (decisions)

**存储**: xuansto.db (统一SQLite) + 内存缓存

```json
{
  "id": "ADR-20260523-001",
  "title": "选择前端框架",
  "context": "需要支持SSR和静态导出",
  "decision": "采用Next.js",
  "rationale": "生态成熟，SSR支持完善",
  "alternatives": ["Nuxt", "SvelteKit"],
  "status": "proposed | accepted | deprecated | superseded",
  "created_at": "2026-05-23T12:00:00",
  "updated_at": "2026-05-23T12:00:00"
}
```

**FTS5 虚拟表**: `decisions_fts` (id UNINDEXED, title, context, decision)

**索引**: `idx_decisions_status`, `idx_decisions_created_at`

### 2.3 会话状态 (Session)

**存储**: Markdown 文件 + JSON 文件

**会话快照** (`session-{timestamp}.md`):
```markdown
# Session 20260523-120000

## 已完成任务
- 完成需求分析
- 完成架构设计

## 未完成任务
- 编写单元测试

## 关键决策
- ADR-20260523-001: 采用Next.js

## 经验沉淀
- SSR配置需注意hydration问题
```

**当前追踪状态** (`current.json`):
```json
{
  "current_phase": 3,
  "current_task": "编写单元测试",
  "decisions": ["ADR-20260523-001"],
  "pending_tasks": ["编写单元测试"],
  "completed_phases": [0, 1, 2],
  "timestamp": "2026-05-23T10:00:00",
  "updated_at": "2026-05-23T12:00:00"
}
```

### 2.4 工作流实例 (Workflow)

**存储**: JSON 文件 + 内存 + gzip 快照

**工作流实例** (`{workflow_id}.json`):
```json
{
  "workflow_id": "wf-a1b2c3d4",
  "workflow": "sdd-tdd-full",
  "project_path": "/path/to/project",
  "status": "running",
  "current_phase": 3,
  "started_at": "2026-05-23T10:00:00+00:00",
  "completed_phases": [0, 1, 2],
  "phase_definitions": [
    {"id": 0, "name": "初始化", "gates": ["DESIGN-SYSTEM-COMPLETE"]}
  ]
}
```

**工作流快照** (`{workflow_id}_phase{N}_{ts}.json.gz`):
```json
{
  "workflow_id": "wf-a1b2c3d4",
  "phase": 3,
  "timestamp": 1716451200.0,
  "time_iso": "2026-05-23T12:00:00Z",
  "state": { "/* 同工作流实例结构 */" }
}
```

### 2.5 资源加载状态 (Resource State)

**存储**: JSON 文件 (`resource_state.json`)

```json
{
  "version": 3,
  "updated_at": "2026-05-23T12:00:00+00:00",
  "phase": "enhanced",
  "loaded": ["skill-config", "agent-registry", "quality-gates"],
  "resources": {
    "skill-config": {"status": "loaded", "phase": 0, "type": "config", "path": ".skill-config.yaml"},
    "agent-registry": {"status": "loaded", "phase": 1, "type": "reference", "path": "references/agent-registry.md"}
  }
}
```

### 2.6 降级管理器状态 (Degradation State)

**存储**: JSON 文件 (`degradation_state.json`)

```json
{
  "overall_level": "L1_NORMAL",
  "components": {
    "search_engine": {
      "name": "search_engine",
      "level": "chromadb",
      "last_check_time": 1716451200.0,
      "last_check_healthy": true,
      "recovery_attempts": 0,
      "next_recovery_time": 0.0,
      "degraded_since": null
    },
    "knowledge_base": {
      "name": "knowledge_base",
      "level": "full",
      "last_check_time": 1716451200.0,
      "last_check_healthy": true,
      "recovery_attempts": 0,
      "next_recovery_time": 0.0,
      "degraded_since": null
    }
  },
  "health_interval": 30.0,
  "started": true
}
```

### 2.7 错误模式 (Pattern)

**存储**: JSON 文件 (`pattern-{timestamp}.json`)

```json
{
  "error": "TypeError: Cannot read property 'x' of undefined",
  "count": 3,
  "confidence": 0.45,
  "status": "draft | verified",
  "created_at": "2026-05-23T12:00:00",
  "verified": false
}
```

### 2.8 指标快照 (Metrics)

**存储**: JSON 文件 (`metrics_{timestamp}.json`)

```json
{
  "persisted_at": "2026-05-23T12:00:00+00:00",
  "tool_metrics": {
    "knowledge_search": {
      "call_count": 42,
      "success_count": 40,
      "failure_count": 2,
      "total_latency_ms": 3500.0,
      "min_latency_ms": 15.0,
      "max_latency_ms": 500.0,
      "latency_samples": [15.0, 20.0],
      "total_input_tokens": 5000,
      "total_output_tokens": 12000
    }
  },
  "degradation_events": [
    {"timestamp": "...", "component": "search_engine", "from_level": "chromadb", "to_level": "sqlite_fts", "reason": "ChromaDB timeout"}
  ],
  "quality_gate_results": [
    {"gate_id": "TEST-PASS", "passed": true, "phase": 4, "timestamp": "..."}
  ],
  "phase_transitions": [
    {"from_phase": "skeleton", "to_phase": "functional", "resources_affected": ["agent-registry"], "timestamp": "..."}
  ]
}
```

### 2.9 技能配置 (Skill Config)

**存储**: YAML 文件 (`.skill-config.yaml`)

```yaml
token_budget:
  default: 100000
  warning_threshold: 0.8
  compression_threshold: 0.8
  per_phase:
    phase_0: 10000
    phase_1: 15000

knowledge_service:
  host: 127.0.0.1
  port: 8765
  auth_mode: optional

session_persistence:
  enabled: true
  save_dir: .skill-logs
  file_pattern: "session-{timestamp}.md"
  max_sessions: 10

continuous_learning:
  enabled: true
  pattern_threshold: 2
  initial_confidence: 0.40
  verified_confidence: 0.80
```

### 2.10 降级配置 (Fallback Config)

**存储**: YAML 文件 (`fallback_config.yaml`)

```yaml
fallback_map:
  knowledge_search:
    scripts:
      - script: knowledge-server.py
        args: ["--search", "--query", "{query}", "--format", "json"]
        timeout: 30
    inline: knowledge_search_fallback
  session_manage:
    scripts:
      - script: init-session.py
        args: ["--action", "{action}", "--format", "json"]
        timeout: 15
        actions: ["save", "init"]
```

---

## 3. 数据生命周期

### 3.1 CRUD 时序总览

| 实体 | Create | Read | Update | Delete | 触发条件 |
|------|--------|------|--------|--------|---------|
| knowledge_entries | knowledge_inject(inject) | knowledge_search(retrieve,只读) | 无(仅insert) | knowledge_inject(delete,软删除deleted_at) | 用户注入知识 |
| decisions | decision_log(log) | decision_log(list/query) | decision_log(update) | 无 | 决策记录/状态变更 |
| session快照 | session_manage(save) | session_manage(load) | 无(追加式) | _cleanup_old_sessions (max=10) | 会话保存/自动清理 |
| session追踪 | session_manage(track) | session_manage(restore) | session_manage(track) | 无 | 阶段推进/任务变更 |
| workflow实例 | workflow_dispatch(start) | workflow_dispatch(status) | workflow_dispatch(phase/abort) | 无(标记aborted) | 工作流启动/推进 |
| workflow快照 | _save_snapshot | _load_latest_snapshot | 无(追加式) | _cleanup_snapshots (TTL+max) | 阶段推进时自动保存 |
| resource_state | resource_load_status(preload) | resource_load_status(status) | resource_load_status(preload) | clear_cache | 资源预加载/状态查询 |
| degradation_state | DegradationManager初始化 | load_state | check_and_degrade/recover | 无 | 健康检查/恢复 |
| pattern | session_manage(detect) | session_manage(verify) | session_manage(verify) | 无 | 错误模式检测(≥2次) |
| metrics | MetricsCollector.record_* | get_*_summary | record_* | reset | 工具调用/自动持久化 |

### 3.2 关键生命周期流程

#### 知识检索降级链

```
HybridSearchEngine自动检测 → ChromaDB语义搜索(可选) → SQLite FTS5 BM25 → 关键词匹配(TF-IDF)
     ↓ 失败                        ↓ 失败              ↓ 失败            ↓ 最终兜底
   返回空                       返回空              返回空            返回关键词结果
```

触发条件: `knowledge_search(action="retrieve")` 时按 `search_type` 参数选择策略:
- `hybrid`: HybridSearchEngine自动检测，依次尝试 ChromaDB(可选) → SQLite → 关键词
- `semantic_only`: 仅 ChromaDB(可选)，失败回退 SQLite → 关键词
- `keyword_only`: 仅 SQLite → 关键词

#### 渐进式资源加载

```
Phase 0 (骨架, ≤2K tokens)
  └── skill-config
Phase 1 (功能, ≤5K tokens)
  └── agent-registry, quality-gates, brainstorm-workflow, 核心3个Agent
Phase 2 (增强, ≤10K tokens)
  └── knowledge-general, sdd-tdd工作流, mcp-tools, agent-registry-full
Phase 3 (完整, ≤20K tokens)
  └── 全部参考文档, 模板, 全部Agent目录
```

触发条件: `resource_load_status(action="preload", phase=N)` 或 `auto_upgrade=true`

#### 决策日志迁移

```
decisions.json (旧格式, JSON数组) → decisions.db (SQLite)
```

触发条件: `decision_log.py` 模块加载时自动执行 `_migrate_json_to_sqlite()`

#### ChromaDB 路径迁移

```
knowledge/index/chroma/ (旧路径) → knowledge/index/chroma_db/ (新路径)
```

触发条件: `config.py` 模块加载时自动执行 `_migrate_chroma_path()`

### 3.3 清理策略

| 实体 | 清理策略 | 触发时机 | 保留策略 |
|------|---------|---------|---------|
| session快照 | `_cleanup_old_sessions` | 每次save后 | 保留最近10个 |
| workflow快照 | `_cleanup_snapshots` | 每次save_snapshot后 | max=20/workflow, TTL=30天 |
| metrics快照 | TTL自动清理 | xuansto.db写入后 | TTL=30天, database.py自动清理 |
| 资源缓存 | `_cleanup_cache` | preload时 | TTL=3600s, max=100条 |
| 内存降级事件 | 列表截断 | record时 | max=200条 |
| 内存质量门禁记录 | 列表截断 | record时 | max=500条 |
| 内存阶段转换记录 | 列表截断 | record时 | max=100条 |

---

## 4. 重构后数据模型

### 4.1 核心实体定义

#### KnowledgeEntry — 知识条目

```python
class KnowledgeEntry:
    id: str                          # 主键, 格式: injected-{timestamp} 或自定义
    title: str                       # 标题
    content: str                     # 内容正文
    type: str                        # 分类: general | workspace | experience
    metadata_json: str               # JSON序列化元数据
    created_at: str                  # ISO8601创建时间
    updated_at: str                  # ISO8601更新时间
    # --- 渐进式加载扩展字段 ---
    scope: str | None                # 搜索范围限定
    source: str                      # 来源: mcp_inject | script | manual
    confidence: float                # 置信度 [0.0, 1.0]
    token_count: int                 # 估算Token数(用于预算控制)
    embedding_status: str            # embedding状态: pending | indexed | failed
    file_path: str | None            # 关联Markdown文件路径
    deleted_at: str | None           # 软删除时间(ISO8601), null=未删除
```

#### DecisionRecord — 决策记录

```python
class DecisionRecord:
    id: str                          # 主键, 格式: ADR-{date}-{seq}
    title: str                       # 决策标题
    context: str                     # 决策上下文
    decision: str                    # 最终决策
    rationale: str                   # 决策理由
    alternatives: list[str]          # 备选方案列表
    status: str                      # proposed | accepted | deprecated | superseded
    impact: str                      # 影响范围
    decided_by: str                  # 决策者
    created_at: str                  # ISO8601
    updated_at: str                  # ISO8601
    # --- 渐进式加载扩展字段 ---
    tags: list[str]                  # 标签(当前仅内存过滤)
    related_phase: int | None        # 关联工作流阶段
    workflow_id: str | None          # 关联工作流实例
```

#### SessionState — 会话状态

```python
class SessionState:
    # --- 追踪状态(current.json) ---
    current_phase: int | None        # 当前阶段
    current_task: str | None         # 当前任务
    decisions: list[str]             # 关联决策ID列表
    pending_tasks: list[str]         # 未完成任务
    completed_phases: list[int]      # 已完成阶段
    timestamp: str                   # 首次创建时间
    updated_at: str                  # 最后更新时间
    # --- 快照扩展(session-{ts}.md) ---
    completed_tasks: list[str]       # 已完成任务
    experience: list[str]            # 经验沉淀
    # --- 重构扩展 ---
    session_id: str                  # 唯一标识(UUID)
    project_path: str                # 项目路径
    workflow_id: str | None          # 关联工作流
    token_usage: dict[str, int]      # Token使用统计
```

#### WorkflowInstance — 工作流实例

```python
class WorkflowInstance:
    workflow_id: str                 # 主键, 格式: wf-{hex8}
    workflow: str                    # 工作流模板名
    project_path: str                # 项目路径
    status: str                      # running | completed | aborted
    current_phase: int               # 当前阶段(0-8)
    started_at: str                  # ISO8601启动时间
    completed_at: str | None         # ISO8601完成时间
    aborted_at: str | None           # ISO8601中止时间
    completed_phases: list[int]      # 已完成阶段列表
    phase_definitions: list[dict]    # 阶段定义(含gates)
    # --- 重构扩展 ---
    phase_snapshots: list[str]       # 快照文件路径列表
    gate_results: dict[int, list]    # 按阶段存储门禁结果
    last_gate_check: str | None      # 最后门禁检查时间
```

#### ResourceLoadState — 资源加载状态

```python
class ResourceLoadState:
    version: int                     # 状态格式版本(当前=3)
    updated_at: str                  # ISO8601
    phase: str                       # skeleton | functional | enhanced | full
    loaded: list[str]                # 已加载资源ID列表
    resources: dict[str, ResourceEntry]  # 资源详情映射

class ResourceEntry:
    status: str                      # loaded | available | missing | stale | expired
    phase: int                       # 所属加载阶段
    type: str                        # config | reference | workflow | agent | knowledge | template
    path: str                        # 相对路径
    # --- 重构扩展 ---
    token_estimate: int              # 估算Token占用
    content_hash: str                # SHA256内容哈希
    last_loaded_at: str              # 最后加载时间
    cache_ttl: int                   # 缓存TTL(秒)
```

#### DegradationState — 降级状态

```python
class DegradationState:
    overall_level: str               # L1_NORMAL | L2_LOCAL_SEMANTIC | L3_BM25_ONLY
    components: dict[str, ComponentState]
    health_interval: float           # 健康检查间隔(秒)
    started: bool                    # 监控是否启动

class ComponentState:
    name: str                        # search_engine | knowledge_base | hooks | resources
    level: str                       # 组件当前降级级别
    last_check_time: float           # 最后检查时间戳
    last_check_healthy: bool         # 最后检查是否健康
    recovery_attempts: int           # 恢复尝试次数
    next_recovery_time: float        # 下次恢复尝试时间
    degraded_since: float | None     # 降级开始时间
```

#### ErrorPattern — 错误模式

```python
class ErrorPattern:
    error: str                       # 错误信息
    count: int                       # 出现次数
    confidence: float                # 置信度 [0.40, 1.00]
    status: str                      # draft | verified
    created_at: str                  # ISO8601
    verified: bool                   # 是否已验证
    # --- 重构扩展 ---
    pattern_id: str                  # 唯一标识
    error_type: str                  # 错误分类
    resolution: str | None           # 解决方案
    related_decisions: list[str]     # 关联决策ID
```

#### MetricsSnapshot — 指标快照

```python
class MetricsSnapshot:
    persisted_at: str                # ISO8601
    tool_metrics: dict[str, ToolMetric]
    degradation_events: list[DegradationEvent]
    quality_gate_results: list[GateResult]
    phase_transitions: list[PhaseTransition]

class ToolMetric:
    call_count: int
    success_count: int
    failure_count: int
    total_latency_ms: float
    min_latency_ms: float
    max_latency_ms: float
    latency_samples: list[float]     # 最近1000个样本
    total_input_tokens: int
    total_output_tokens: int
```

### 4.2 实体关系描述

```
┌─────────────────┐       ┌──────────────────────┐
│ WorkflowInstance │──1:N──│ WorkflowSnapshot      │
│ (wf-{hex8})     │       │ (phase+timestamp)     │
└────────┬────────┘       └──────────────────────┘
         │
         │ 1:N
         ▼
┌─────────────────┐       ┌──────────────────────┐
│ DecisionRecord  │◄──N:1─│ SessionState          │
│ (ADR-{date}-{n})│       │ (session_id)          │
└─────────────────┘       └──────────┬───────────┘
                                     │
         ┌───────────────────────────┤
         │ N:N                       │ N:1
         ▼                           ▼
┌─────────────────┐       ┌──────────────────────┐
│ ErrorPattern    │       │ WorkflowInstance      │
│ (pattern_id)    │       │ (workflow_id)         │
└────────┬────────┘       └──────────────────────┘
         │
         │ N:N (precipitate)
         ▼
┌─────────────────┐
│ KnowledgeEntry  │◄─── 知识检索(ChromaDB/SQLite/Keyword)
│ (id)            │───→ 知识注入(inject)
└─────────────────┘

┌─────────────────┐       ┌──────────────────────┐
│ResourceLoadState│──1:N──│ ResourceEntry         │
│ (phase)         │       │ (resource_id)         │
└─────────────────┘       └──────────────────────┘

┌─────────────────┐       ┌──────────────────────┐
│DegradationState │──1:N──│ ComponentState        │
│ (overall_level) │       │ (component_name)      │
└─────────────────┘       └──────────────────────┘

┌─────────────────┐
│MetricsSnapshot  │──1:N── ToolMetric / DegradationEvent / GateResult / PhaseTransition
│ (persisted_at)  │
└─────────────────┘
```

**核心关系说明**:

- **WorkflowInstance → WorkflowSnapshot**: 一个工作流实例在每个阶段推进时产生一个快照，1:N关系，通过 `workflow_id` 关联
- **SessionState → DecisionRecord**: 会话中产生的决策通过 `decisions` 列表关联，N:N关系
- **SessionState → WorkflowInstance**: 会话可关联一个活跃工作流，N:1关系
- **ErrorPattern → KnowledgeEntry**: 经验沉淀(precipitate)将多个模式聚合为经验知识，N:N关系
- **ResourceLoadState → ResourceEntry**: 渐进式加载状态包含多个资源条目，1:N关系
- **DegradationState → ComponentState**: 降级管理器管理多个组件状态，1:N关系

### 4.3 渐进式加载相关字段

渐进式加载是 xuansto-skill 的核心设计，以下字段专门服务于该机制:

| 字段 | 所属实体 | 用途 |
|------|---------|------|
| `phase` | ResourceLoadState | 当前加载阶段(0-3) |
| `phase` | ResourceEntry | 资源所属阶段 |
| `type` | ResourceEntry | 资源类型(决定加载优先级) |
| `token_estimate` | ResourceEntry | 估算Token占用(预算控制) |
| `content_hash` | ResourceEntry | 内容哈希(缓存有效性) |
| `cache_ttl` | ResourceEntry | 缓存TTL |
| `embedding_status` | KnowledgeEntry | 向量索引状态 |
| `token_count` | KnowledgeEntry | Token估算(预算控制) |
| `confidence` | KnowledgeEntry | 置信度(搜索过滤) |

**Phase → Resource 映射** (参见 [resource_load_status.py](../../xuansto-mcp-server/src/xuansto_mcp/tools/resource_load_status.py)):

| Phase | Token预算 | 资源数 | 核心资源 |
|-------|----------|--------|---------|
| 0 (骨架) | 2K | 1 | skill-config |
| 1 (功能) | 5K | 6 | agent-registry, quality-gates, 核心3Agent |
| 2 (增强) | 10K | 8 | knowledge, 工作流定义, 完整Agent注册表 |
| 3 (完整) | 20K | 22 | 全部参考文档, 模板, 全部Agent目录 |

---

## 5. 数据迁移策略

### 5.1 已有迁移

| 迁移ID | 源格式 | 目标格式 | 状态 | 实现 |
|--------|--------|---------|------|------|
| MIG-01 | `decisions.json` (JSON数组) | `decisions.db` (SQLite) | ✅ 已完成 | `_migrate_json_to_sqlite()` |
| MIG-02 | `knowledge/index/chroma/` | `knowledge/index/chroma_db/` | ✅ 已完成 | `_migrate_chroma_path()` |
| MIG-03 | FTS5 默认tokenizer | FTS5 unicode61 tokenizer | ✅ 已完成 | `_migrate_fts5_to_unicode61()` |
| MIG-04 | knowledge_entries 缺失列 | MCP标准列 | ✅ 已完成 | schema migration in `_ensure_knowledge_index()` |
| MIG-05 | resource_state.json v1(list) | v3(dict) | ✅ 已完成 | `_load_resource_state()` |
| MIG-06 | SessionState 分散存储 | xuansto.db session_states表 | ✅ 已完成 | `database.py` 统一管理 |
| MIG-07 | ErrorPattern 缺乏分类 | 增强字段(pattern_id/error_type/resolution) | ✅ 已完成 | `database.py` error_patterns表 |
| MIG-08 | WorkflowInstance 关联缺失 | gate_results/phase_snapshots关联 | ✅ 已完成 | `database.py` workflow_instances表 |
| MIG-09 | Metrics 分散JSON文件 | xuansto.db tool_metrics表+TTL清理 | ✅ 已完成 | `database.py` 统一存储+TTL |
| MIG-10 | knowledge.db + decisions.db 分散 | 统一xuansto.db (8表) | ✅ 已完成 | `database.py` 合并为单一数据库 |
| MIG-11 | knowledge_entries 无软删除 | 添加deleted_at字段 | ✅ 已完成 | `knowledge_inject(delete)` 软删除 |

### 5.2 重构迁移计划

#### MIG-06: SessionState 结构化迁移

**问题**: 当前会话状态分散在 Markdown 快照和 JSON 追踪文件中，缺乏统一ID和关联

**迁移步骤**:
1. 读取现有 `current.json` 和 `session-*.md` 文件
2. 为每个会话生成 `session_id` (UUID)
3. 将 Markdown 快照中的结构化数据提取为 JSON
4. 建立 Session → Decision/Workflow 关联
5. 写入新格式到 `.xuansto/sessions/v2/` 目录
6. 保留旧文件作为备份

```python
def migrate_session_v1_to_v2():
    sessions_dir = SESSION_DIR
    v2_dir = sessions_dir / "v2"
    v2_dir.mkdir(exist_ok=True)

    for session_file in sessions_dir.glob("session-*.md"):
        session_id = str(uuid.uuid4())
        content = session_file.read_text(encoding="utf-8")
        parsed = parse_session_markdown(content)
        new_state = {
            "session_id": session_id,
            "version": 2,
            **parsed,
            "project_path": str(_find_project_root()),
        }
        (v2_dir / f"{session_id}.json").write_text(
            json.dumps(new_state, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
```

#### MIG-07: ErrorPattern 增强

**问题**: 当前模式文件仅包含 error/count/confidence，缺乏分类和解决方案

**迁移步骤**:
1. 读取 `patterns/pattern-*.json`
2. 添加 `pattern_id` (从文件名提取)
3. 推断 `error_type` (从错误消息分类)
4. 初始化 `resolution` 和 `related_decisions` 为空
5. 写回增强格式

#### MIG-08: WorkflowInstance 关联增强

**问题**: 工作流实例与决策日志、会话状态之间缺乏显式关联

**迁移步骤**:
1. 读取 `workflows/{workflow_id}.json`
2. 扫描 `decisions.db` 中时间范围匹配的决策
3. 建立 `gate_results` 字段(从快照中提取)
4. 添加 `phase_snapshots` 路径列表
5. 写回增强格式

#### MIG-09: Metrics 统一存储

**问题**: 当前指标以时间戳命名文件存储，无自动清理，查询不便

**迁移步骤**:
1. 创建 `metrics.db` (SQLite)
2. 定义 `tool_metrics`、`degradation_events`、`gate_results`、`phase_transitions` 表
3. 批量导入现有 `metrics_*.json` 文件
4. 切换 MetricsCollector 持久化到 SQLite
5. 保留旧 JSON 文件作为备份(30天后手动清理)

### 5.3 迁移安全原则

1. **向后兼容**: 新格式必须能读取旧数据，旧代码不应因新字段崩溃
2. **原子写入**: 所有文件写入使用 `atomic_write()` (tmpfile + os.replace)
3. **备份优先**: 迁移前保留原始文件，迁移后验证再清理
4. **渐进式**: 每次迁移只处理一个实体，不批量跨实体迁移
5. **可回滚**: 每个迁移步骤都应有回滚路径

---

## 6. 存储技术选型建议

### 6.1 当前选型评估

| 技术 | 当前用途 | 优势 | 问题 | 编号 |
|------|---------|------|------|------|
| SQLite (WAL) | 知识库、决策日志 | 零配置、ACID、FTS5 | 并发写入瓶颈、无向量搜索 | DB-01 |
| ChromaDB | 向量语义搜索 | 开箱即用、Python原生 | 额外依赖、嵌入模型依赖、降级频繁 | DB-02 |
| JSON 文件 | 状态持久化 | 简单直观、人类可读 | 无原子性(需atomic_write)、无查询能力、无压缩 | DB-03 |
| Markdown 文件 | 会话快照 | 人类可读、版本控制友好 | 结构化查询困难、解析脆弱 | DB-04 |
| YAML 文件 | 配置 | 层级清晰、注释支持 | 解析性能差、无schema校验 | DB-05 |
| 内存缓存 | 运行时状态 | 零延迟 | 进程重启丢失、无持久化 | DB-06 |

### 6.2 推荐改进方案

#### DB-01: SQLite 统一状态存储 ✅ 已实施

**建议**: 将分散的 JSON 状态文件统一迁移到 SQLite

**实施结果**: 已创建 `database.py` 统一管理 `xuansto.db` (8表)，替代分散的 knowledge.db、decisions.db 和 JSON 文件

**Schema (已实施)**:
```sql
-- xuansto.db 8表:
-- 1. knowledge_entries (含FTS5虚拟表knowledge_fts, 含deleted_at软删除)
-- 2. decisions (含FTS5虚拟表decisions_fts)
-- 3. session_states
-- 4. workflow_instances
-- 5. resource_states
-- 6. error_patterns
-- 7. degradation_states
-- 8. tool_metrics (含TTL自动清理)
```

#### DB-02: ChromaDB 可选化 + 嵌入模型解耦 ✅ 已实施

**建议**: 将 ChromaDB 从必需依赖降级为可选增强

**实施结果**: ChromaDB已改为可选依赖，HybridSearchEngine自动检测可用性；默认使用 SQLite FTS5 + BM25

#### DB-03: 指标存储迁移到 SQLite ✅ 已实施

**建议**: 创建 `xuansto.db` tool_metrics 表替代时间戳命名的 JSON 文件

**实施结果**: tool_metrics表已创建，支持时间范围查询、TTL自动清理(30天)、聚合统计

#### DB-04: 会话快照双格式存储

**建议**: 保留 Markdown 人类可读格式，同时维护 SQLite 结构化索引

**方案**:
- Markdown 快照继续用于版本控制和人工审阅
- SQLite `session_states` 表维护结构化索引和关联关系
- 两者通过 `session_id` 关联

#### DB-05: 配置 Schema 校验

**建议**: 为 YAML 配置文件添加 Pydantic schema 校验

**方案**:
- 定义 `SkillConfigModel`、`FallbackConfigModel` 等 Pydantic 模型
- 在 `_load_yaml_config()` 后执行校验
- 校验失败时使用默认值并记录警告

### 6.3 技术选型矩阵

| 需求 | SQLite | JSON文件 | YAML文件 | ChromaDB | 内存 |
|------|--------|---------|---------|----------|------|
| 结构化查询 | ✅ 优秀 | ❌ 差 | ❌ 差 | ⚠️ 有限 | ✅ 优秀 |
| 全文搜索 | ✅ FTS5 | ❌ 无 | ❌ 无 | ❌ 无 | ❌ 无 |
| 向量搜索 | ❌ 无 | ❌ 无 | ❌ 无 | ✅ 优秀 | ❌ 无 |
| 事务保障 | ✅ ACID | ⚠️ atomic_write | ❌ 无 | ⚠️ 有限 | ❌ 无 |
| 并发安全 | ✅ WAL | ⚠️ 文件锁 | ❌ 无 | ⚠️ 有限 | ✅ Lock |
| 人类可读 | ❌ 差 | ✅ 好 | ✅ 优秀 | ❌ 差 | ❌ 差 |
| 版本控制 | ❌ 差 | ✅ 好 | ✅ 优秀 | ❌ 差 | ❌ 无 |
| 零依赖 | ✅ 内置 | ✅ 内置 | ⚠️ PyYAML | ❌ 额外 | ✅ 内置 |
| 压缩支持 | ❌ 无 | ❌ 无 | ❌ 无 | ❌ 无 | ❌ 无 |

### 6.4 推荐存储分配

| 实体 | 当前存储 | 推荐存储 | 理由 |
|------|---------|---------|------|
| KnowledgeEntry | xuansto.db + ChromaDB(可选) + MD | xuansto.db + ChromaDB(可选) + MD | ✅ 已实施，ChromaDB降为可选，含软删除 |
| DecisionRecord | xuansto.db + 内存缓存 | xuansto.db | ✅ 已实施，减少内存缓存依赖 |
| SessionState | xuansto.db + MD(双写) | xuansto.db + MD(双写) | ✅ 已实施，SQLite索引+MD人类可读 |
| WorkflowInstance | xuansto.db + gzip快照 | xuansto.db + gzip快照 | ✅ 已实施，SQLite主存储，gzip快照保留 |
| ResourceLoadState | xuansto.db | xuansto.db | ✅ 已实施，查询频繁，需事务保障 |
| DegradationState | xuansto.db + 内存 | xuansto.db + 内存 | ✅ 已实施，SQLite持久化+内存热路径 |
| ErrorPattern | xuansto.db | xuansto.db | ✅ 已实施，结构化查询需求 |
| MetricsSnapshot | xuansto.db (tool_metrics表) | xuansto.db | ✅ 已实施，时间范围查询+TTL自动清理 |
| SkillConfig | YAML | YAML + Pydantic校验 | 保持人类可读，增加校验 |
| FallbackConfig | YAML | YAML + Pydantic校验 | 同上 |

---

## 7. 问题清单

| 编号 | 严重度 | 描述 | 影响 | 建议 | 状态 |
|------|--------|------|------|------|------|
| DB-01 | 高 | JSON状态文件无原子性保障 | 并发写入可能导致数据损坏 | 统一迁移到SQLite | ✅ 已解决 |
| DB-02 | 高 | ChromaDB降级频繁，影响语义搜索 | 知识检索经常回退到BM25 | ChromaDB可选化+HybridSearchEngine | ✅ 已解决 |
| DB-03 | 中 | 会话状态分散在MD和JSON中 | 关联查询困难，数据不一致 | SessionState双格式存储 | ✅ 已解决 |
| DB-04 | 中 | 指标文件无自动清理 | 长期运行后文件系统膨胀 | 迁移到SQLite+TTL清理 | ✅ 已解决 |
| DB-05 | 中 | 内存缓存无持久化 | 进程重启后缓存全部丢失 | 关键缓存持久化到SQLite | ✅ 已解决 |
| DB-06 | 中 | YAML配置无Schema校验 | 配置错误仅在运行时暴露 | 添加Pydantic校验层 | 待实施 |
| DB-07 | 低 | ErrorPattern缺乏分类体系 | 模式匹配效率低 | 添加error_type分类字段 | ✅ 已解决 |
| DB-08 | 低 | WorkflowInstance与Decision无显式关联 | 无法追溯决策来源 | 添加workflow_id关联字段 | ✅ 已解决 |
| DB-09 | 低 | knowledge_entries无软删除 | 注入的知识无法撤销 | 添加deleted_at字段实现软删除 | ✅ 已解决 |
| DB-10 | 低 | 资源缓存无LRU淘汰策略 | 缓存可能占用过多内存 | 实现LRU缓存淘汰 | ✅ 已解决(cache.py) |
| DB-11 | 中 | 多个SQLite数据库分散 | 连接管理复杂，事务跨库困难 | 合并为单一数据库 | ✅ 已解决(xuansto.db) |
| DB-12 | 低 | 快照文件无加密 | 敏感项目信息可能泄露 | 可选加密快照存储 | ✅ 已解决(crypto.py AES-256-GCM) |
