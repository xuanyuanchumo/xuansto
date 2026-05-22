# 渐进式加载披露规范

> 版本: 1.0.0 | 更新日期: 2026-05-22 | 编码: UTF-8 | 行尾: LF

本文档定义了 xuansto-skill-v2 的渐进式加载披露（Progressive Loading Disclosure）完整规范，包括加载阶段、状态机、触发矩阵、降级策略和性能目标。**披露（Disclosure）**强调在渐进式加载过程中，系统透明地向用户和Agent公开当前加载状态、功能可用性及资源就绪情况，确保加载过程可观测、可审计。

---

## 1. 加载阶段定义

### 1.1 四级加载层次

| 加载阶段 | 名称 | 加载内容 | 对应工作流Phase | 预估Token |
|----------|------|----------|-----------------|-----------|
| Phase 0 | 骨架 (Skeleton) | 核心约束 + 命令概要 + Agent索引表 | Phase 0 | ~2K |
| Phase 1 | 功能 (Functional) | 命令详细步骤 + 工作流Phase定义 + MCP工具参数 | Phase 0-8 | ~3K |
| Phase 2 | 增强 (Enhanced) | 参考文档 + 模板文件 + 知识库索引 | Phase 0-8 | ~5K |
| Phase 3 | 完整 (Full) | 全部资源 + 脚本集 + 披露资源 | All | ~10K |

### 1.2 各阶段详细内容

#### Phase 0: 骨架 (Skeleton)

加载内容：
- SKILL.md 核心约束（5条）
- 命令路由概要（27命令 → MCP Tool映射）
- Agent索引表（57 Agent按层级分组）
- MCP Server依赖声明
- 降级模式入口

不加载：
- 命令详细步骤
- Agent完整定义
- 参考文档
- 模板文件

#### Phase 1: 功能 (Functional)

加载内容：
- Phase 0 全部内容
- 当前命令的详细步骤（commands/[command].md）
- 当前工作流Phase定义
- MCP工具参数Schema
- Hook系统配置

不加载：
- 参考文档（quality-gates.md等）
- Agent详细定义
- 知识库索引

#### Phase 2: 增强 (Enhanced)

加载内容：
- Phase 1 全部内容
- 参考文档（quality-gates.md, agent-registry.md, knowledge-workflow-details.md等）
- 模板文件（PRD模板、ADR模板等）
- 知识库索引（ChromaDB/FTS5元数据）
- Agent详细定义（按需加载）

不加载：
- 完整脚本集
- 披露资源
- 评估配置

#### Phase 3: 完整 (Full)

加载内容：
- Phase 2 全部内容
- 完整脚本集（scripts/目录）
- 披露资源（加载状态、功能可用性）
- 评估配置（evals/）
- 全部Agent定义
- 全部参考文档

---

## 2. 状态机设计

### 2.1 LoadPhase枚举

```python
class LoadPhase(str, Enum):
    SKELETON = "skeleton"
    FUNCTIONAL = "functional"
    ENHANCED = "enhanced"
    FULL = "full"
```

### 2.2 状态转换规则

```
SKELETON ──[命令执行]──→ FUNCTIONAL
FUNCTIONAL ──[参考文档请求]──→ ENHANCED
ENHANCED ──[深度分析/桌面构建]──→ FULL

FULL ──[Token>80%]──→ ENHANCED
ENHANCED ──[Token>95%]──→ FUNCTIONAL
FUNCTIONAL ──[Token>95%且无活动]──→ SKELETON

任意Phase ──[Phase回退/recover]──→ 上一Phase的FUNCTIONAL
```

### 2.3 转换条件

| 转换 | 触发条件 | 动作 |
|------|----------|------|
| SKELETON→FUNCTIONAL | 用户执行命令 或 Phase进入 | preload当前Phase资源 |
| FUNCTIONAL→ENHANCED | agent_status(detail) 或 参考文档请求 | 加载Agent定义+参考文档 |
| ENHANCED→FULL | /build-desktop 或 /loop 命令 | 加载全部资源 |
| FULL→ENHANCED | Token使用率>80% | context_compress压缩 |
| ENHANCED→FUNCTIONAL | Token使用率>95% | 释放参考文档缓存 |
| FUNCTIONAL→SKELETON | Token使用率>95%且当前Phase无活动 | 仅保留核心约束 |

---

## 3. 加载触发矩阵

| 触发事件 | 加载动作 | 目标Phase |
|----------|----------|-----------|
| Skill首次触发 | 加载Phase 0骨架 | SKELETON |
| 命令路由匹配成功 | 加载当前命令的Phase 1详情 | FUNCTIONAL |
| Phase转换(advance) | resource_load_status(preload, phase=N) | FUNCTIONAL |
| Agent调度(detail) | 加载目标Agent的Phase 2定义 | ENHANCED |
| 知识检索(retrieve) | 按需检索，不预加载 | ENHANCED |
| Token使用率>80% | context_compress(strategy=semantic) | 降级到ENHANCED |
| Token使用率>95% | 仅保留Phase 0 + 当前命令 | 降级到SKELETON |
| 桌面构建命令 | 加载Phase 3桌面资源 | FULL |

---

## 4. 资源优先级定义

### 4.1 优先级分类

| 优先级 | 名称 | 资源 | Token紧张时处理 |
|--------|------|------|-----------------|
| P0 | 必须 | SKILL.md核心约束、命令路由表、Agent索引表 | 始终保留 |
| P1 | 重要 | 命令详细步骤、工作流Phase定义、MCP工具参数 | Token>95%时释放 |
| P2 | 增强 | 参考文档、模板文件、知识库 | Token>80%时释放 |
| P3 | 可选 | 示例文档、评估配置、披露资源 | Token>60%时释放 |

### 4.2 资源释放顺序

当Token预算紧张时，按以下顺序释放资源：

1. 释放P3资源（披露、评估、示例）
2. 释放P2资源（参考文档、模板、知识库）
3. 释放P1资源（命令步骤、工作流定义）— 仅保留当前命令
4. P0资源始终保留

---

## 5. MCP Resource集成

### 5.1 xuansto://loading/status

URI: `xuansto://loading/status`

返回当前加载状态的JSON：

```json
{
  "current_phase": "functional",
  "phase_index": 1,
  "loaded_resources": ["skill-config", "quality-gates", "agent-registry"],
  "loaded_count": 3,
  "available_references": ["quality-gates.md", "agent-registry.md", "mcp-tools.md"],
  "loading_progress": {
    "quality-gates": 1.0,
    "agent-registry": 1.0,
    "knowledge-workflow-details": 0.5
  },
  "timestamp": 1716360000.0
}
```

### 5.2 resource_load_status工具集成

`resource_load_status` MCP工具支持以下action：

| Action | 描述 | 加载Phase |
|--------|------|-----------|
| status | 查询当前加载状态 | 不变 |
| preload | 预加载指定Phase资源 | 推进到目标Phase |
| cache | 查询缓存状态 | 不变 |
| clear_cache | 清理缓存 | 降级到SKELETON |
| loading_progress | 查询加载进度 | 不变 |

---

## 6. 降级加载策略

### 6.1 MCP不可用时的降级

当MCP Server不可用时，渐进式加载降级为本地文件系统读取：

| 加载方式 | 优先级 | 实现路径 |
|----------|--------|----------|
| MCP Resource | 1 | xuansto://loading/status |
| MCP Tool | 2 | resource_load_status(action=status) |
| 本地文件 | 3 | 直接读取 references/ 目录 |

### 6.2 低精度→高精度加载

参考文档支持两级加载：

| 精度 | 内容 | Token消耗 |
|------|------|-----------|
| 摘要 | 文档标题+章节列表+关键指标 | ~200 |
| 完整 | 文档全部内容 | ~2000-5000 |

默认加载摘要，当Agent执行需要详细信息时再加载完整内容。

---

## 7. 性能目标

### 7.1 Token消耗目标

| 指标 | 当前值 | 目标值 | 降低比例 |
|------|--------|--------|----------|
| Skill触发时Token | ~8,000 | ≤2,000 | 75% |
| 单命令执行Token | ~15,000 | ≤5,000 | 67% |
| 全流程Token(9 Phase) | ~84,000 | ≤30,000 | 64% |
| Agent调度Token(单次) | ~500/Agent | ≤150/Agent | 70% |

### 7.2 加载时间目标

| 指标 | 当前值 | 目标值 |
|------|--------|--------|
| 骨架加载 | N/A(全量) | ≤500ms |
| Phase资源预加载 | N/A(全量) | ≤2s/Phase |
| Agent定义按需加载 | N/A(全量) | ≤300ms/Agent |
| 知识检索响应 | 1-5s(ChromaDB) | ≤3s(hybrid) |

---

## 8. LoadingProgress数据结构

```python
@dataclass
class LoadingProgress:
    resource_uri: str
    phase: LoadPhase
    progress: float  # [0.0, 1.0]
    loaded_at: float | None  # timestamp
    content_hash: str | None  # for cache validation
    ttl: int | None  # seconds, None = no expiry
```

### 8.1 resource_state.json格式

升级后的格式（向后兼容纯字符串列表）：

```json
{
  "phase": "functional",
  "loaded": ["quality-gates", "agent-registry", "workflow-phases"],
  "progress": {
    "quality-gates": {"progress": 1.0, "loaded_at": 1716360000.0},
    "agent-registry": {"progress": 1.0, "loaded_at": 1716360001.0}
  },
  "last_updated": 1716360001.0
}
```

旧格式（纯字符串列表）仍可读取，自动升级为新格式。

---

## 9. 披露策略

### 9.1 披露原则

渐进式加载披露遵循以下原则：

1. **透明性**：始终向用户/Host披露当前加载状态和可用功能范围
2. **可操作性**：当功能不可用时，提供明确的推进加载路径
3. **降级友好**：不可用功能应提供降级替代方案
4. **渐进式**：功能可用性随加载阶段递增，不跳跃

### 9.2 披露触发点

| 触发事件 | 披露动作 | 披露内容 |
|----------|----------|----------|
| Skill首次触发 | 返回骨架阶段可用功能 | 可用：命令路由、Agent索引；不可用：命令步骤、知识检索 |
| 命令路由匹配 | 返回功能阶段可用功能 | 可用：命令执行、门禁检查；不可用：知识检索、参考文档 |
| Phase转换 | 返回新阶段可用功能 | 根据目标阶段披露可用功能范围 |
| resource_load_status(status) | 返回当前完整状态 | 全部加载状态+可用功能+披露说明 |
| Token预算紧张 | 披露降级信息 | 哪些功能将被释放、降级替代方案 |

### 9.3 状态转换披露规则

| 转换 | 披露内容 | 用户通知 |
|------|----------|----------|
| SKELETON→FUNCTIONAL | "命令详细步骤已加载，可执行命令" | 自动通知 |
| FUNCTIONAL→ENHANCED | "参考文档和知识检索已可用" | 按需通知 |
| ENHANCED→FULL | "全部功能已可用" | 自动通知 |
| FULL→ENHANCED | "Token预算紧张，已释放完整脚本集" | 必须通知 |
| ENHANCED→FUNCTIONAL | "Token预算紧张，已释放参考文档" | 必须通知 |
| FUNCTIONAL→SKELETON | "Token预算紧张，仅保留核心功能" | 必须通知 |

### 9.4 降级披露

当功能因加载阶段限制不可用时，系统应披露降级方案：

| 不可用功能 | 降级方案 | 披露说明 |
|-----------|----------|----------|
| 知识检索(ChromaDB) | SQLite FTS5关键词检索 | "语义检索不可用，已降级为关键词检索" |
| 知识检索(FTS5) | 内嵌知识模板 | "知识库不可用，使用内嵌模板" |
| 参考文档 | 命令内嵌摘要 | "参考文档未加载，使用命令内嵌信息" |
| Agent详细定义 | Agent索引摘要 | "Agent详情未加载，使用索引摘要" |
| 完整脚本集 | 内嵌降级逻辑 | "脚本集不可用，使用内嵌降级逻辑" |
