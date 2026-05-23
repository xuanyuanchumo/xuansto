# xuansto-skill 数据库设计文档

> 基于 xuansto-mcp-server 源码与 `.xuansto/` 运行时状态文件的实际代码分析
> 生成日期: 2026-05-22

---

## 1. 当前数据存储分析

xuansto-skill 是一个 MCP Server + Skill 混合项目，当前数据存储采用**纯文件系统**方案，无传统数据库（除知识库使用 SQLite/ChromaDB）。数据分散在 JSON 文件、Markdown 文件、YAML 配置、环境变量和内存状态中。

### 1.1 存储介质分类

| 介质类型 | 用途 | 典型路径 |
|---------|------|---------|
| JSON 文件 | 运行时状态持久化 | `.xuansto/*.json` |
| Markdown 文件 | 会话记录/知识文档 | `.xuansto/sessions/session-*.md` |
| YAML 配置 | Skill 全局配置 | `.xuansto-config.yaml` |
| SQLite (FTS5) | 知识库全文检索 | `knowledge/index/knowledge.db` |
| ChromaDB | 知识库语义检索 | `knowledge/index/chroma_db/` |
| 环境变量 | 路径配置 | `XUANSTO_SKILL_ROOT`, `XUANSTO_WORK_DIR` |
| 内存状态 | 高频读写缓存 | `_ACTIVE_WORKFLOWS`, `_AGENT_INSTANCES` 等 |

### 1.2 环境变量

| 变量名 | 默认值 | 说明 | 来源 |
|--------|-------|------|------|
| `XUANSTO_SKILL_ROOT` | `DATA_DIR`（包内 data 目录） | Skill 资源根目录 | `config.py:L27` |
| `XUANSTO_WORK_DIR` | `{project_root}/.xuansto` | 运行时工作目录 | `config.py:L197` |

### 1.3 持久化/缓存数据实体详解

#### 1.3.1 resource_state.json — 资源加载状态

**路径**: `{WORK_DIR}/resource_state.json`
**写入方**: `resource_load_status.py` → `_save_resource_state()`
**读取方**: `resource_load_status.py` → `_load_resource_state()`, `_get_loading_disclosure()`

当前存在**双格式兼容**：旧格式为纯列表，新格式为带版本号的对象。

```json
// 旧格式（列表）
["test-dir-1", "test-hash-1", "test-res-1"]

// 新格式（对象，v1）
{
  "version": 1,
  "updated_at": "2026-05-22T08:30:00+00:00",
  "loaded": ["skill-config", "agent-registry", "quality-gates"],
  "phase": "enhanced"
}
```

**字段说明**:

| 字段 | 类型 | 说明 |
|------|------|------|
| `version` | int | 格式版本号，当前为 1 |
| `updated_at` | string(ISO8601) | 最后更新时间 |
| `loaded` | string[] | 已加载资源 ID 列表 |
| `phase` | string | 当前加载阶段（skeleton/functional/enhanced/full） |

#### 1.3.2 workflow_states.json — 活跃工作流状态汇总

**路径**: `{WORK_DIR}/workflow_states.json`
**写入方**: `workflow_dispatch.py` → `_persist_active_workflows()`
**读取方**: `workflow_dispatch.py` → `_load_active_workflows()`, `load_on_startup()`

```json
{
  "wf-337aba39": {
    "workflow_id": "wf-337aba39",
    "workflow": "sdd-tdd-fast",
    "project_path": "C:\\Users\\...\\test_project",
    "status": "running",
    "current_phase": 0,
    "started_at": "2026-05-21T15:45:40.702986+00:00",
    "completed_phases": [],
    "phase_definitions": [
      {
        "id": 0,
        "name": "设计+测试",
        "gates": ["DESIGN-SYSTEM-COMPLETE", "TEST-FIRST"],
        "agents": ["design-reviewer", "tdd-agent"]
      }
    ]
  }
}
```

**字段说明**:

| 字段 | 类型 | 说明 |
|------|------|------|
| `workflow_id` | string | 工作流实例 ID，格式 `wf-{uuid[:8]}` |
| `workflow` | string | 工作流定义名称（如 `sdd-tdd-full`） |
| `project_path` | string | 关联项目路径 |
| `status` | string | 状态：`running` / `completed` / `aborted` |
| `current_phase` | int | 当前阶段编号（0-8） |
| `started_at` | string(ISO8601) | 启动时间 |
| `completed_at` | string(ISO8601)? | 完成时间（仅 completed 状态） |
| `aborted_at` | string(ISO8601)? | 中止时间（仅 aborted 状态） |
| `completed_phases` | int[] | 已完成阶段列表 |
| `phase_definitions` | object[]? | 阶段定义（含 gates/agents） |

#### 1.3.3 单个工作流实例文件

**路径**: `{WORK_DIR}/workflows/{workflow_id}.json`
**写入方**: `workflow_dispatch.py` → `_persist_workflow()`

数据结构与 `workflow_states.json` 中单个条目相同，但作为独立文件存储，用于单实例持久化和恢复。

#### 1.3.4 工作流快照文件

**路径**: `{project_path}/.xuansto/workflow_snapshots/{workflow_id}_phase{N}_{timestamp}.json.gz`
**写入方**: `workflow_dispatch.py` → `_save_snapshot()`
**读取方**: `workflow_dispatch.py` → `_load_latest_snapshot()`, `_list_snapshots()`

```json
{
  "workflow_id": "wf-ac896d47",
  "phase": 1,
  "timestamp": 1779320289.020507,
  "time_iso": "2026-05-21T07:38:09",
  "state": {
    "workflow_id": "wf-ac896d47",
    "workflow": "sdd-tdd-full",
    "project_path": ".",
    "status": "running",
    "current_phase": 1,
    "started_at": "2026-05-21T07:38:08.977936",
    "completed_phases": [0],
    "phase_definitions": [...]
  }
}
```

**清理策略**: 每工作流最多保留 20 个快照，TTL 30 天（可通过 `.xuansto-config.yaml` 配置）。

#### 1.3.5 agent_instances.json — Agent 实例状态

**路径**: `{WORK_DIR}/agent_instances.json`
**写入方**: `agent_status.py` → `_persist_agent_instances()`
**读取方**: `agent_status.py` → `_load_agent_instances()`, `load_on_startup()`

```json
{
  "agent-2c932163": {
    "agent_id": "agent-2c932163",
    "agent_type": "Backend",
    "capabilities": ["python"],
    "status": "idle",
    "task": "",
    "created_at": 1779378152.874071,
    "history": [],
    "last_active_at": "2026-05-21T15:42:32.874070+00:00",
    "task_count": 0,
    "total_duration_ms": 0
  }
}
```

**字段说明**:

| 字段 | 类型 | 说明 |
|------|------|------|
| `agent_id` | string | 实例 ID，格式 `agent-{uuid[:8]}` |
| `agent_type` | string | Agent 类型（如 Backend/Frontend） |
| `capabilities` | string[] | 能力标签列表 |
| `status` | string | 状态：`idle` / `busy` |
| `task` | string | 当前任务描述（busy 时非空） |
| `created_at` | float(unix) | 创建时间戳 |
| `history` | object[] | 操作历史记录 |
| `last_active_at` | string(ISO8601) | 最后活跃时间 |
| `task_count` | int | 累计执行任务数 |
| `total_duration_ms` | int | 累计执行时长（毫秒） |

**限制**: 最多 20 个实例（`_MAX_AGENT_INSTANCES = 20`）。

#### 1.3.6 gate_cache.json — 质量门禁缓存

**路径**: `{project_path}/.xuansto/gate_cache.json`
**写入方**: `quality_gate_check.py` → `_save_gate_cache()`
**读取方**: `quality_gate_check.py` → `_load_gate_cache()`

```json
{
  "file_hashes": {
    ".editorconfig": "250889e4c3e28e1965...",
    "README.md": "39ca728fb1ee45fcf9..."
  },
  "checks": [
    {
      "gate_id": "TEST-PASS",
      "status": "PASS",
      "source": "inline",
      "details": { "message": "Tests collectible: 42 tests found" }
    }
  ],
  "timestamp": 1779320289.020507
}
```

**字段说明**:

| 字段 | 类型 | 说明 |
|------|------|------|
| `file_hashes` | dict | 项目文件 SHA256 哈希映射（用于缓存失效检测） |
| `checks` | object[] | 门禁检查结果列表 |
| `timestamp` | float | 缓存写入时间戳 |

**缓存失效逻辑**: 当 `file_hashes` 的 key 集合或 value 与当前计算结果不一致时，缓存失效。

#### 1.3.7 file_hashes.json — 持久化文件哈希缓存

**路径**: `{DATA_DIR}/.xuansto/file_hashes.json`
**写入方**: `quality_gate_check.py` → `_save_persistent_hash_cache()`
**读取方**: `quality_gate_check.py` → `_load_persistent_hash_cache()`

```json
{
  "D:\\Projects\\MyProject": {
    "src/main.py": {
      "hash": "abc123...",
      "mtime": 1779320289.0
    }
  }
}
```

按项目路径分组，每个文件记录哈希值和 mtime，用于增量哈希计算（mtime 未变则跳过哈希计算）。

#### 1.3.8 tool_metrics.json — 工具调用指标

**路径**: `{WORK_DIR}/tool_metrics.json`
**写入方**: `server_health.py` → `_persist_metrics()`
**读取方**: `server_health.py` → `metrics_load_on_startup()`

```json
{
  "mixed_tool": {
    "call_count": 304,
    "error_count": 102,
    "latencies": [1.0, 2.0, 3.0, 4.0, 5.0]
  }
}
```

**字段说明**:

| 字段 | 类型 | 说明 |
|------|------|------|
| `call_count` | int | 总调用次数 |
| `error_count` | int | 错误次数 |
| `latencies` | float[] | 最近 1000 次延迟记录（ms），持久化时截断到最近 100 条 |

**持久化策略**: 调用计数 ≥100 次或距上次持久化 ≥60 秒时触发。

#### 1.3.9 degradation_stats.json — 降级统计

**路径**: `{WORK_DIR}/degradation_stats.json`
**写入方**: `server_health.py` → `_persist_metrics()`
**读取方**: `server_health.py` → `degradation_load_on_startup()`

```json
{
  "chromadb_unavailable": 3,
  "mixed_degr": 300
}
```

键为降级原因（如 `chromadb_unavailable`），值为累计降级次数。ChromaDB 恢复后对应计数归零。

#### 1.3.10 Session 文件

**路径**: `{WORK_DIR}/sessions/session-{timestamp}.md`
**写入方**: `session_manage.py` → `_save_session()`

```markdown
# Session 20260522-083000

## 已完成任务
- 实现用户认证模块
- 编写单元测试

## 未完成任务
- 集成测试编写

## 关键决策
- 选择 JWT 作为认证方案

## 经验沉淀
- pytest fixture 复用可减少测试代码量
```

**清理策略**: 最多保留 10 个会话文件（`_cleanup_old_sessions(max_sessions=10)`）。

#### 1.3.11 current.json — 会话追踪状态

**路径**: `{WORK_DIR}/sessions/current.json`
**写入方**: `session_manage.py` → `_track_session()`
**读取方**: `session_manage.py` → `_restore_session()`, `restore_on_startup()`

```json
{
  "current_phase": 4,
  "current_task": "实现用户认证",
  "decisions": ["选择 JWT 认证方案", "使用 bcrypt 哈希"],
  "pending_tasks": ["集成测试", "API 文档"],
  "completed_phases": [0, 1, 2, 3],
  "timestamp": "2026-05-22T08:00:00+00:00",
  "updated_at": "2026-05-22T08:30:00+00:00"
}
```

#### 1.3.12 模式文件（Pattern）

**路径**: `{WORK_DIR}/patterns/pattern-{timestamp}.json`
**写入方**: `session_manage.py` → `_detect_patterns()`
**读取方**: `session_manage.py` → `_verify_pattern()`, `knowledge_search.py` → `_precipitate_experience()`

```json
{
  "error": "ImportError: No module named 'xyz'",
  "count": 3,
  "confidence": 0.45,
  "status": "draft",
  "created_at": "2026-05-22T08:30:00",
  "verified": false
}
```

#### 1.3.13 知识库（SQLite + ChromaDB）

**SQLite 路径**: `{KNOWLEDGE_DIR}/index/knowledge.db`
**ChromaDB 路径**: `{KNOWLEDGE_DIR}/index/chroma_db/`

SQLite 表结构：

```sql
CREATE TABLE knowledge_entries (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    type TEXT NOT NULL DEFAULT 'general',
    metadata_json TEXT DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- FTS5 全文索引（unicode61 分词器）
CREATE VIRTUAL TABLE knowledge_fts
    USING fts5(content, title, type,
        content=knowledge_entries,
        content_rowid=rowid,
        tokenize='unicode61');

-- 自动同步触发器
CREATE TRIGGER knowledge_ai AFTER INSERT ON knowledge_entries BEGIN
    INSERT INTO knowledge_fts(rowid, content, title, type)
        VALUES (new.rowid, new.content, new.title, new.type);
END;
-- knowledge_ad, knowledge_au 触发器类似
```

ChromaDB 集合名: `knowledge`，存储文档向量用于语义检索。

**三层降级检索策略**: ChromaDB 语义搜索 → SQLite FTS5 BM25 → 文件系统关键词搜索。

#### 1.3.14 YAML 配置文件

**路径**: `{SKILL_ROOT}/.xuansto-config.yaml`

```yaml
gate_scripts:
  GATE-007: check-encoding.py
  TEST-PASS: coverage-check.py
gates_by_phase:
  "0": ["DESIGN-SYSTEM-COMPLETE", "ANTI-PATTERN-CHECK"]
  "1": ["BRAINSTORM-COMPLETE", "GATE-001"]
hook_scripts:
  token-budget-check: token-budget-guard.py
  encoding-check: check-encoding.py
max_snapshots_per_workflow: 20
snapshot_ttl_days: 30
```

#### 1.3.15 内存状态汇总

| 变量名 | 模块 | 类型 | 说明 |
|--------|------|------|------|
| `_ACTIVE_WORKFLOWS` | workflow_dispatch | `dict[str, dict]` | 活跃工作流实例映射 |
| `_AGENT_INSTANCES` | agent_status | `dict[str, _AgentInstance]` | Agent 实例映射 |
| `_RESOURCE_CACHE` | resource_load_status | `dict[str, dict]` | 资源内容缓存（TTL 3600s，上限 100 条） |
| `_LOADED_PROGRESS` | resource_load_status | `dict` | 加载进度追踪 |
| `_TOOL_METRICS` | server_health | `dict[str, dict]` | 工具调用指标 |
| `_DEGRADATION_COUNTS` | server_health | `dict[str, int]` | 降级计数 |
| `_file_hash_cache` | quality_gate_check | `dict[str, dict]` | 文件哈希缓存 |
| `_file_mtime_cache` | quality_gate_check | `dict[str, dict]` | 文件 mtime 缓存 |
| `_RESTORED_STATE` | session_manage | `dict \| None` | 启动恢复的会话状态 |
| `_chromadb_client` | server_health | `PersistentClient \| None` | ChromaDB 客户端实例 |

---

## 2. 数据生命周期

### 2.1 生命周期总览

```
启动 → 加载持久化状态到内存 → 运行时读写（内存优先）→ 定期/触发式持久化 → 关闭
```

### 2.2 各实体生命周期详情

#### resource_state.json

| 阶段 | 触发条件 | 操作 |
|------|---------|------|
| **创建** | 首次 `preload` 操作 | `_save_resource_state()` 写入新格式 |
| **读取** | `status` 操作 / `_get_loading_disclosure()` | `_load_resource_state()` 兼容旧列表格式和新对象格式 |
| **更新** | `preload` 操作完成 | `_set_loaded_resources()` 更新 loaded 列表并持久化 |
| **销毁** | 手动删除 / `clear_cache` | 仅清内存缓存，不删除文件 |

#### workflow_states.json

| 阶段 | 触发条件 | 操作 |
|------|---------|------|
| **创建** | `start` 操作 | `_start_workflow()` → `_persist_active_workflows()` |
| **读取** | 启动恢复 / `status` 操作 | `load_on_startup()` 从 `workflows/*.json` 恢复到内存 |
| **更新** | `phase advance` / `abort` | 修改内存 `_ACTIVE_WORKFLOWS` → `_persist_active_workflows()` |
| **销毁** | `abort` 操作 | 从 `_ACTIVE_WORKFLOWS` 移除，文件标记 `status=aborted` |

**启动恢复流程** (`load_on_startup()`):
1. 扫描 `workflows/*.json`
2. 跳过 `status=aborted` 和损坏文件
3. 恢复到 `_ACTIVE_WORKFLOWS` 内存
4. 重新写入 `workflow_states.json`

#### 单工作流文件 (workflows/{id}.json)

| 阶段 | 触发条件 | 操作 |
|------|---------|------|
| **创建** | `start` 操作 | `_persist_workflow()` |
| **读取** | `status` / `phase advance` / `recover` | `_load_workflow()` |
| **更新** | `phase advance` 成功 | 更新 `current_phase`/`completed_phases` |
| **销毁** | 不主动删除，由快照清理策略间接管理 | |

#### 工作流快照 (workflow_snapshots/)

| 阶段 | 触发条件 | 操作 |
|------|---------|------|
| **创建** | `phase advance` 成功 | `_save_snapshot()` 写入 gzip 压缩文件 |
| **读取** | `recover` / `snapshots` 操作 | `_load_latest_snapshot()` / `_list_snapshots()` |
| **清理** | 每次快照创建后 / `server_health` 调用时 | `_cleanup_snapshots()` 按 TTL 和数量限制清理 |

#### agent_instances.json

| 阶段 | 触发条件 | 操作 |
|------|---------|------|
| **创建** | `create` 操作 | 新建 `_AgentInstance` → `_persist_agent_instances()` |
| **读取** | 启动恢复 / `instance_status` / `match` | `_load_agent_instances()` |
| **更新** | `assign` / `release` 操作 | 修改内存 dataclass → `_persist_agent_instances()` |
| **销毁** | `destroy` 操作 | 从 `_AGENT_INSTANCES` 移除 → `_persist_agent_instances()` |

#### gate_cache.json

| 阶段 | 触发条件 | 操作 |
|------|---------|------|
| **创建** | 首次 `quality_gate_check` 调用 | `_save_gate_cache()` |
| **读取** | 每次 `quality_gate_check` 调用 | `_load_gate_cache()` → 比对 `file_hashes` 判定缓存有效性 |
| **更新** | 缓存失效时重新检查 | 计算新哈希 → 执行检查 → `_save_gate_cache()` |
| **销毁** | `force_refresh=True` | 跳过缓存读取，强制重新检查 |

#### tool_metrics.json / degradation_stats.json

| 阶段 | 触发条件 | 操作 |
|------|---------|------|
| **创建** | 首次工具调用 | `record_tool_call()` 初始化内存条目 |
| **读取** | 启动时 | `metrics_load_on_startup()` / `degradation_load_on_startup()` |
| **更新** | 每次工具调用 | 内存更新 → 满足阈值时 `_persist_metrics()` |
| **销毁** | 不主动删除 | |

**持久化触发条件**（二选一）:
- 调用计数 ≥ `_PERSIST_CALL_THRESHOLD`（100 次）
- 距上次持久化 ≥ `_PERSIST_INTERVAL_SEC`（60 秒）

#### Session 文件

| 阶段 | 触发条件 | 操作 |
|------|---------|------|
| **创建** | `save` 操作 | `_save_session()` 写入 Markdown 文件 |
| **读取** | `load` / `restore` 操作 | `_load_last_session()` / `_restore_session()` |
| **清理** | 每次 `save` 后 | `_cleanup_old_sessions()` 保留最近 10 个 |

#### current.json

| 阶段 | 触发条件 | 操作 |
|------|---------|------|
| **创建** | `track` 操作 | `_track_session()` |
| **读取** | `restore` 操作 / 启动时 | `_restore_session()` / `restore_on_startup()` |
| **更新** | `track` 操作 | 合并 decisions/completed_phases 后覆写 |

#### 知识库 (SQLite + ChromaDB)

| 阶段 | 触发条件 | 操作 |
|------|---------|------|
| **创建** | 首次 `retrieve` / `inject` 调用 | `_ensure_knowledge_index()` 建表 + FTS5 |
| **读取** | `retrieve` 操作 | 三层降级：ChromaDB → SQLite FTS5 → 文件搜索 |
| **写入** | `inject` 操作 | 同时写入 Markdown 文件 + SQLite + ChromaDB |
| **迁移** | FTS5 tokenizer 升级 | `_migrate_fts5_to_unicode61()` 自动迁移 |

---

## 3. 重构后数据模型设计

### 3.1 MCP Server 状态模型

基于当前代码分析，将分散的 JSON 文件整合为结构化的状态模型。

#### 3.1.1 ServerState — 服务器全局状态

```python
@dataclass
class ServerState:
    version: str
    started_at: str
    uptime_seconds: float
    config: ServerConfig
    services: ServicesStatus
    performance: PerformanceMetrics

@dataclass
class ServerConfig:
    data_dir: str
    skill_root: str
    work_dir: str

@dataclass
class ServicesStatus:
    chromadb: ChromaDBStatus

@dataclass
class ChromaDBStatus:
    available: bool
    latency_ms: float
    reason: str | None

@dataclass
class PerformanceMetrics:
    tools: dict[str, ToolMetrics]
    degradation_counts: dict[str, int]

@dataclass
class ToolMetrics:
    call_count: int
    error_count: int
    error_rate: float
    latency_p50_ms: float
    latency_p95_ms: float
    latency_p99_ms: float
```

### 3.2 资源存储模型

#### 3.2.1 ResourceState — 渐进式加载状态

```python
@dataclass
class ResourceState:
    version: int = 1
    updated_at: str = ""
    loaded: list[str] = field(default_factory=list)
    phase: LoadPhase = LoadPhase.SKELETON

class LoadPhase(str, Enum):
    SKELETON = "skeleton"
    FUNCTIONAL = "functional"
    ENHANCED = "enhanced"
    FULL = "full"

@dataclass
class ProgressiveLoadState:
    total_resources: int = 0
    loaded_resources: int = 0
    current_phase: int | None = None
    loading: bool = False
    started_at: str | None = None
    completed_at: str | None = None

    @property
    def progress_percent(self) -> float:
        if self.total_resources == 0:
            return 0.0
        return round(self.loaded_resources / self.total_resources * 100, 2)

@dataclass
class DisclosureTransition:
    from_phase: LoadPhase
    to_phase: LoadPhase
    available_functions: dict[str, bool]
    disclosure_note: str

@dataclass
class ResourceEntry:
    id: str
    type: str
    path: str
    status: ResourceStatus
    inherits_from: str | None = None

class ResourceStatus(str, Enum):
    LOADED = "loaded"
    AVAILABLE = "available"
    MISSING = "missing"
    STALE = "stale"
    EXPIRED = "expired"

@dataclass
class ResourceCacheEntry:
    content: str
    cached_at: float
    access_count: int
    content_hash: str
    ttl_seconds: int = 3600
    source_path: str | None = None
```

**LoadPhase 与功能披露映射**:

| LoadPhase | command_routing | command_execution | quality_gates | knowledge_search | reference_docs | agent_details | full_scripts |
|-----------|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| skeleton | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| functional | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| enhanced | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| full | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

**DisclosureTransition 定义**:

```python
DISCLOSURE_TRANSITIONS: list[DisclosureTransition] = [
    DisclosureTransition(
        from_phase=LoadPhase.SKELETON,
        to_phase=LoadPhase.FUNCTIONAL,
        available_functions={
            "command_routing": True, "command_execution": True,
            "quality_gates": True, "knowledge_search": False,
            "reference_docs": False, "agent_details": False,
            "full_scripts": False,
        },
        disclosure_note="功能阶段，知识检索需推进到增强阶段",
    ),
    DisclosureTransition(
        from_phase=LoadPhase.FUNCTIONAL,
        to_phase=LoadPhase.ENHANCED,
        available_functions={
            "command_routing": True, "command_execution": True,
            "quality_gates": True, "knowledge_search": True,
            "reference_docs": True, "agent_details": True,
            "full_scripts": False,
        },
        disclosure_note="增强阶段，完整脚本集需推进到完整阶段",
    ),
    DisclosureTransition(
        from_phase=LoadPhase.ENHANCED,
        to_phase=LoadPhase.FULL,
        available_functions={
            "command_routing": True, "command_execution": True,
            "quality_gates": True, "knowledge_search": True,
            "reference_docs": True, "agent_details": True,
            "full_scripts": True,
        },
        disclosure_note="完整阶段，全部功能可用",
    ),
]
```

### 3.3 工作流模型

```python
@dataclass
class WorkflowInstance:
    workflow_id: str
    workflow: str
    project_path: str
    status: WorkflowStatus
    current_phase: int
    started_at: str
    completed_at: str | None = None
    aborted_at: str | None = None
    completed_phases: list[int] = field(default_factory=list)
    phase_definitions: list[PhaseDefinition] = field(default_factory=list)

class WorkflowStatus(str, Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    ABORTED = "aborted"

@dataclass
class PhaseDefinition:
    id: int
    name: str
    gates: list[str] = field(default_factory=list)
    agents: list[str] = field(default_factory=list)

@dataclass
class WorkflowSnapshot:
    workflow_id: str
    phase: int
    timestamp: float
    time_iso: str
    state: WorkflowInstance
```

### 3.4 Agent 模型

```python
@dataclass
class AgentInstance:
    agent_id: str
    agent_type: str
    capabilities: list[str]
    status: AgentStatus = AgentStatus.IDLE
    task: str = ""
    created_at: float = 0.0
    history: list[AgentHistoryEntry] = field(default_factory=list)
    last_active_at: str = ""
    task_count: int = 0
    total_duration_ms: int = 0

class AgentStatus(str, Enum):
    IDLE = "idle"
    BUSY = "busy"
    DESTROYED = "destroyed"

@dataclass
class AgentHistoryEntry:
    action: str
    task: str
    timestamp: float
    duration_ms: int | None = None
```

### 3.5 质量门禁模型

```python
@dataclass
class GateCache:
    file_hashes: dict[str, str]
    checks: list[GateCheckResult]
    timestamp: float

@dataclass
class GateCheckResult:
    gate_id: str
    status: GateStatus
    source: str
    details: dict = field(default_factory=dict)
    suggestion: str | None = None

class GateStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    SKIP = "SKIP"
    ERROR = "ERROR"

@dataclass
class FileHashCache:
    project_path: str
    file_hashes: dict[str, str]
    file_mtimes: dict[str, float]
```

### 3.6 会话模型

```python
@dataclass
class SessionTrackState:
    current_phase: int | None
    current_task: str | None
    decisions: list[str]
    pending_tasks: list[str]
    completed_phases: list[int]
    timestamp: str
    updated_at: str

@dataclass
class PatternEntry:
    error: str
    count: int
    confidence: float
    status: str
    created_at: str
    verified: bool
```

### 3.7 知识库模型

```python
@dataclass
class KnowledgeEntry:
    id: str
    title: str
    content: str
    type: str = "general"
    metadata_json: str = "{}"
    created_at: str = ""
    updated_at: str = ""

@dataclass
class KnowledgeSearchResult:
    source: str
    content: str
    match_type: str  # "semantic" | "fts5" | "keyword"
    relevance: float
```

### 3.8 实体关系描述

```
┌─────────────────────────────────────────────────────────────────┐
│                        ServerState                               │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────┐ │
│  │ ServerConfig │  │ ServicesStat │  │ PerformanceMetrics    │ │
│  │  data_dir    │  │  chromadb    │  │  tools: ToolMetrics[] │ │
│  │  skill_root  │  │  available   │  │  degradation_counts   │ │
│  │  work_dir    │  │  latency_ms  │  │                       │ │
│  └──────────────┘  └──────────────┘  └───────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    WorkflowInstance (1:N)                        │
│  workflow_id ──────────┐                                        │
│  workflow              │  ┌─ PhaseDefinition[]                  │
│  project_path          │  │   id, name, gates[], agents[]       │
│  status                │  └────────────────────────────────     │
│  current_phase ────────┼──→ PhaseDefinition.id                  │
│  completed_phases[]    │                                        │
│                        │  ┌─ WorkflowSnapshot[] (per phase)     │
│                        │  │   phase, timestamp, state           │
│                        │  └────────────────────────────────     │
│  └─────────────────────┘                                        │
│                                                                  │
│  PhaseDefinition.gates[] ──→ GateCheckResult[] (via gate_cache) │
│  PhaseDefinition.agents[] ─→ AgentInstance (by capability match)│
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    AgentInstance (max 20)                        │
│  agent_id ──────→ history: AgentHistoryEntry[]                  │
│  agent_type     capabilities[] ──→ match with PhaseDefinition   │
│  status: idle|busy                                              │
│  task (when busy)                                               │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    ResourceState                                 │
│  phase: LoadPhase ──→ DisclosureTransition                      │
│  loaded[] ──→ ResourceEntry.status                               │
│  ResourceCacheEntry (in-memory, TTL 3600s, max 100)             │
│  ProgressiveLoadState (loading progress tracker)                │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    GateCache (per project)                       │
│  file_hashes{} ──→ cache validity check                         │
│  checks[] ──→ GateCheckResult                                   │
│  FileHashCache (persistent, per project)                        │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    SessionTrackState                             │
│  current_phase ──→ WorkflowInstance.current_phase               │
│  decisions[], pending_tasks[], completed_phases[]               │
│  PatternEntry[] ──→ KnowledgeEntry (via precipitate)            │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    KnowledgeDB (SQLite + ChromaDB)               │
│  KnowledgeEntry ──→ knowledge_fts (FTS5, auto-sync triggers)   │
│  KnowledgeEntry ──→ ChromaDB collection "knowledge" (vectors)  │
│  三层降级: semantic → fts5_bm25 → keyword_tfidf                │
└─────────────────────────────────────────────────────────────────┘
```

**核心关系**:

1. **WorkflowInstance ↔ PhaseDefinition**: 一个工作流包含多个阶段定义，`current_phase` 指向当前阶段
2. **PhaseDefinition → GateCheckResult**: 阶段的 `gates[]` 通过 `quality_gate_check` 产生检查结果
3. **PhaseDefinition → AgentInstance**: 阶段的 `agents[]` 通过 `agent_status.match` 匹配可用实例
4. **WorkflowInstance → WorkflowSnapshot**: 每次阶段推进产生一个快照，用于恢复
5. **SessionTrackState ↔ WorkflowInstance**: 会话追踪的 `current_phase` 与工作流阶段同步
6. **ResourceState → LoadPhase → DisclosureTransition**: 加载阶段决定功能可用性
7. **KnowledgeEntry → FTS5 + ChromaDB**: 双索引同步写入，三层降级检索
8. **PatternEntry → KnowledgeEntry**: `precipitate` 操作将模式沉淀为经验知识

---

## 4. 迁移策略

### 4.1 resource_state.json 双格式迁移

**现状**: `_load_resource_state()` 已实现双格式兼容（`resource_load_status.py:L277-284`）:

```python
def _load_resource_state() -> set[str]:
    data = json.loads(state_file.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return set(data)          # 旧格式：纯列表
    if isinstance(data, dict):
        return set(data.get("loaded", []))  # 新格式：带版本号的对象
```

**迁移方案**:

| 步骤 | 操作 | 兼容性 |
|------|------|--------|
| 1 | 读取时兼容两种格式（已实现） | ✅ 向后兼容 |
| 2 | 写入时始终使用新格式（已实现 `_save_resource_state`） | ✅ 自动升级 |
| 3 | 添加 `phase` 字段到新格式 | ✅ 新增字段，默认 `skeleton` |
| 4 | 旧格式文件在首次写入时自动升级为新格式 | ✅ 透明迁移 |

**无需数据迁移脚本**，读写代码已内置格式兼容逻辑。

### 4.2 ChromaDB 路径迁移

**现状**: `config.py:L215-243` 已实现 `_migrate_chroma_path()`:

```python
def _migrate_chroma_path() -> None:
    legacy = KNOWLEDGE_DIR / "index" / "chroma"      # 旧路径
    current = KNOWLEDGE_DIR / "index" / "chroma_db"   # 新路径
    # 自动 shutil.move
```

**迁移规则**:
- 旧路径有数据 + 新路径无数据 → 自动 `shutil.move`
- 两边都有数据 → 保留新路径，日志警告
- 旧路径为空 → 跳过

### 4.3 FTS5 Tokenizer 迁移

**现状**: `knowledge_search.py:L52-89` 已实现 `_migrate_fts5_to_unicode61()`:

```python
def _migrate_fts5_to_unicode61(conn) -> None:
    # 检查现有 FTS5 表是否使用 unicode61
    # 若否：删除旧触发器 → 删除旧 FTS5 表 → 创建新 FTS5 表 → rebuild
```

**迁移规则**:
- 自动检测 tokenizer 类型
- 非 unicode61 → 自动重建 FTS5 索引
- 保留原 `knowledge_entries` 表数据不变

### 4.4 knowledge_entries Schema 迁移

**现状**: `knowledge_search.py:L109-134` 已实现列缺失检测:

```python
cursor.execute("PRAGMA table_info(knowledge_entries)")
existing_cols = {row[1] for row in cursor.fetchall()}
missing = _MCP_STANDARD_COLUMNS - existing_cols
for col in sorted(missing):
    conn.execute(f"ALTER TABLE knowledge_entries ADD COLUMN {col} ...")
```

**迁移规则**:
- 启动时自动检测缺失列
- 逐列 `ALTER TABLE ADD COLUMN` 添加
- 带默认值，无需数据回填

### 4.5 未来迁移建议

| 迁移项 | 当前状态 | 建议方案 |
|--------|---------|---------|
| workflow_states.json → SQLite | 分散 JSON 文件 | 保留 JSON 作为备份，新增 SQLite `workflows` 表 |
| agent_instances.json → SQLite | 单 JSON 文件 | 迁移到 SQLite `agent_instances` 表，保留 JSON 降级读取 |
| gate_cache.json → SQLite | 按 project 分散 | 迁移到 SQLite `gate_cache` 表，以 `project_path` 为分区键 |
| tool_metrics.json → SQLite | 单 JSON 文件 | 迁移到 SQLite `tool_metrics` 表，支持时序查询 |
| session current.json → SQLite | 单 JSON 文件 | 迁移到 SQLite `sessions` 表 |

**通用迁移模式**:

```python
def migrate_json_to_sqlite(json_path: Path, table_name: str, conn: sqlite3.Connection):
    backup_path = json_path.with_suffix(".json.bak")
    if not json_path.exists():
        return
    data = json.loads(json_path.read_text(encoding="utf-8"))
    # 1. 写入 SQLite
    _upsert_to_table(conn, table_name, data)
    # 2. 备份旧文件
    shutil.copy2(json_path, backup_path)
    # 3. 验证数据完整性
    if _verify_migration(conn, table_name, data):
        json_path.unlink()
    else:
        logger.error("Migration verification failed, keeping JSON backup")
```

---

## 5. 存储技术选型建议

### 5.1 当前架构评估

| 维度 | 当前方案 | 评分 | 问题 |
|------|---------|------|------|
| 数据一致性 | JSON 原子写入 (`atomic_write`) | ⭐⭐⭐ | 无事务保证，并发写入可能丢失 |
| 查询能力 | 全量加载到内存后过滤 | ⭐⭐ | 无法索引查询，O(n) 复杂度 |
| 并发安全 | `threading.Lock` | ⭐⭐⭐ | 进程级锁，多进程不安全 |
| 存储效率 | JSON 文本 + gzip 快照 | ⭐⭐⭐ | 重复数据多（workflow_states vs 单文件） |
| 可观测性 | 手动日志 | ⭐⭐ | 无结构化查询，难以聚合分析 |
| 扩展性 | 文件系统 | ⭐⭐ | 大量工作流文件时 I/O 瓶颈 |

### 5.2 推荐方案：SQLite 为主 + ChromaDB 为辅

#### 5.2.1 为什么选择 SQLite

| 考量 | SQLite 优势 |
|------|-----------|
| 零部署 | 无需额外服务，Python 内置支持 |
| 事务安全 | WAL 模式支持并发读、串行写 |
| 查询能力 | SQL 全功能，支持 FTS5/窗口函数/CTE |
| 单文件 | 便于备份和迁移 |
| 性能 | 适合本项目读写量级（非高并发 Web 场景） |
| 已有基础 | 知识库已使用 SQLite，团队熟悉 |

#### 5.2.2 建议的 SQLite Schema

```sql
-- 核心状态表
CREATE TABLE workflow_instances (
    workflow_id TEXT PRIMARY KEY,
    workflow TEXT NOT NULL,
    project_path TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'running'
        CHECK(status IN ('running', 'completed', 'aborted')),
    current_phase INTEGER NOT NULL DEFAULT 0,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    aborted_at TEXT,
    completed_phases TEXT NOT NULL DEFAULT '[]',  -- JSON array
    phase_definitions TEXT NOT NULL DEFAULT '[]', -- JSON array
    updated_at TEXT NOT NULL
);

CREATE INDEX idx_workflow_status ON workflow_instances(status);
CREATE INDEX idx_workflow_project ON workflow_instances(project_path);

-- 工作流快照
CREATE TABLE workflow_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workflow_id TEXT NOT NULL,
    phase INTEGER NOT NULL,
    timestamp REAL NOT NULL,
    time_iso TEXT NOT NULL,
    state_json TEXT NOT NULL,       -- 完整状态 JSON
    FOREIGN KEY (workflow_id) REFERENCES workflow_instances(workflow_id)
);

CREATE INDEX idx_snapshot_workflow ON workflow_snapshots(workflow_id);
CREATE INDEX idx_snapshot_phase ON workflow_snapshots(workflow_id, phase);

-- Agent 实例
CREATE TABLE agent_instances (
    agent_id TEXT PRIMARY KEY,
    agent_type TEXT NOT NULL,
    capabilities TEXT NOT NULL DEFAULT '[]',  -- JSON array
    status TEXT NOT NULL DEFAULT 'idle'
        CHECK(status IN ('idle', 'busy', 'destroyed')),
    task TEXT NOT NULL DEFAULT '',
    created_at REAL NOT NULL,
    last_active_at TEXT NOT NULL,
    task_count INTEGER NOT NULL DEFAULT 0,
    total_duration_ms INTEGER NOT NULL DEFAULT 0,
    history TEXT NOT NULL DEFAULT '[]'  -- JSON array
);

-- 门禁缓存（按项目分区）
CREATE TABLE gate_cache (
    project_path TEXT NOT NULL,
    gate_id TEXT NOT NULL,
    status TEXT NOT NULL,
    source TEXT NOT NULL,
    details TEXT DEFAULT '{}',
    suggestion TEXT,
    file_hashes TEXT NOT NULL DEFAULT '{}',
    cached_at REAL NOT NULL,
    PRIMARY KEY (project_path, gate_id)
);

-- 工具指标（时序数据）
CREATE TABLE tool_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tool_name TEXT NOT NULL,
    call_count INTEGER NOT NULL DEFAULT 0,
    error_count INTEGER NOT NULL DEFAULT 0,
    latency_p50_ms REAL,
    latency_p95_ms REAL,
    latency_p99_ms REAL,
    recorded_at TEXT NOT NULL
);

CREATE INDEX idx_metrics_tool ON tool_metrics(tool_name);
CREATE INDEX idx_metrics_time ON tool_metrics(recorded_at);

-- 降级统计
CREATE TABLE degradation_stats (
    reason TEXT PRIMARY KEY,
    count INTEGER NOT NULL DEFAULT 0,
    last_occurred_at TEXT
);

-- 会话追踪
CREATE TABLE session_states (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    current_phase INTEGER,
    current_task TEXT,
    decisions TEXT NOT NULL DEFAULT '[]',
    pending_tasks TEXT NOT NULL DEFAULT '[]',
    completed_phases TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- 资源加载状态
CREATE TABLE resource_states (
    id INTEGER PRIMARY KEY CHECK(id = 1),  -- 单行表
    version INTEGER NOT NULL DEFAULT 1,
    phase TEXT NOT NULL DEFAULT 'skeleton',
    loaded TEXT NOT NULL DEFAULT '[]',      -- JSON array
    updated_at TEXT NOT NULL
);

-- 模式记录
CREATE TABLE patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    error_text TEXT NOT NULL,
    count INTEGER NOT NULL DEFAULT 1,
    confidence REAL NOT NULL DEFAULT 0.4,
    status TEXT NOT NULL DEFAULT 'draft',
    verified INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    file_path TEXT
);

CREATE INDEX idx_patterns_status ON patterns(status);
```

#### 5.2.3 ChromaDB 保留场景

| 场景 | 说明 |
|------|------|
| 知识库语义搜索 | 向量相似度检索，SQLite 无法替代 |
| 降级兼容 | ChromaDB 不可用时自动降级到 SQLite FTS5 |

#### 5.2.4 文件系统保留场景

| 场景 | 说明 |
|------|------|
| 工作流定义文件 | `.md` 格式，含 YAML frontmatter，适合人类编辑 |
| Agent 注册表 | `agent-registry.md`，Markdown 格式 |
| 会话记录 | `session-*.md`，人类可读 |
| 知识文档 | `knowledge/general/*.md`，Markdown 格式 |
| 配置文件 | `.xuansto-config.yaml` |
| 快照文件 | 大体积 gzip 压缩文件，SQLite BLOB 不合适 |

### 5.3 迁移路线图

```
Phase 0 (当前) ─── 纯文件系统 + SQLite(知识库) + ChromaDB
    │
Phase 1 ─── 引入 SQLite 状态库
    │  - 新增 xuansto_state.db
    │  - 迁移 workflow_instances / agent_instances
    │  - 保留 JSON 作为降级备份
    │
Phase 2 ─── 迁移缓存和指标
    │  - 迁移 gate_cache / tool_metrics / degradation_stats
    │  - 迁移 session_states / resource_states / patterns
    │  - 删除 JSON 降级读取代码
    │
Phase 3 ─── 优化与增强
    │  - 添加 SQLite 时序聚合视图
    │  - 添加数据清理 cron（VACUUM + 过期数据删除）
    │  - 考虑 SQLite → PostgreSQL 远期方案（多用户场景）
    │
Phase 4 ─── 可选：分布式场景
       - SQLite → PostgreSQL（多进程/多用户）
       - ChromaDB → Milvus/Qdrant（大规模向量检索）
```

### 5.4 技术选型对比

| 方案 | 优点 | 缺点 | 适用场景 |
|------|------|------|---------|
| **JSON 文件（当前）** | 零依赖、人类可读、调试简单 | 无事务、无索引、并发不安全 | 原型/单用户/低频写入 |
| **SQLite（推荐）** | 零部署、事务安全、SQL 全功能、FTS5 | 单写者限制、无内置复制 | 单机/中等并发/结构化查询 |
| **PostgreSQL** | 企业级、高并发、丰富扩展 | 需部署服务、运维成本 | 多用户/高并发/分布式 |
| **ChromaDB** | 向量检索、语义搜索 | 仅向量场景、无事务 | 知识库语义检索 |
| **Redis** | 高性能缓存、TTL 原生支持 | 内存成本、数据持久化弱 | 高频缓存/短期状态 |

### 5.5 最终建议

1. **短期（Phase 1）**: 引入 `xuansto_state.db`，迁移 `workflow_instances` 和 `agent_instances` 两张高频读写表，保留 JSON 文件作为降级备份
2. **中期（Phase 2）**: 完成所有状态数据迁移到 SQLite，删除 JSON 降级代码，统一使用 SQLite WAL 模式
3. **长期（Phase 3-4）**: 根据实际并发需求评估是否需要升级到 PostgreSQL；ChromaDB 在当前规模下足够，无需更换
4. **文件系统**: 始终保留用于人类可读的 Markdown 文档（会话记录、知识文档、工作流定义）
