# xuansto-skill 重构总计划

> 版本: 1.0.0 | 生成日期: 2026-05-22
> 基于 ARCHITECTURE.md / DATABASE_DESIGN.md / MCP_REVIEW.md / SKILL_REVIEW.md / API_SPECIFICATION.md 五份分析文档及源码事实编写
> 当前版本: Skill v7.0.0 | MCP Server v3.5.0 | API v1.0.0
> 目标版本: Skill v8.0.0 | MCP Server v4.0.0 | API v2.0.0

---

## 目录

1. [问题统一清单](#1-问题统一清单)
2. [影响链分析](#2-影响链分析)
3. [优先级划分](#3-优先级划分)
4. [模块化重构步骤](#4-模块化重构步骤)
5. [渐进式加载披露实现方案](#5-渐进式加载披露实现方案)
6. [测试策略](#6-测试策略)
7. [持续集成建议](#7-持续集成建议)

---

## 1. 问题统一清单

从前五份分析文档提取所有发现的问题、技术债和不兼容项，去重后形成统一清单。每项标注所属端：**Skill**(Skill定义层) / **MCP**(MCP Server执行层) / **数据**(持久化与存储) / **API**(接口协议) / **披露**(渐进式加载披露) / **架构**(全局架构)。

### 1.1 P1 — 阻塞级问题（3项）

| 编号 | 问题 | 所属端 | 来源文档 | 详细描述 |
|------|------|--------|----------|----------|
| **A-01** | SKILL.md膨胀至~416行 | Skill | ARCHITECTURE.md §7.1, SKILL_REVIEW.md §5.2 | SKILL.md同时承载触发条件、命令路由表、27命令详细步骤、降级策略、Agent索引、加载阶段定义等6类职责，Token消耗~10K，严重拖慢Skill触发速度。命令详细步骤与commands/*.md内容完全重复，内嵌步骤占~2500 Token |
| **A-02** | 数据镜像冗余 | 数据 | DATABASE_DESIGN.md §1.3, ARCHITECTURE.md §7.1 | workflow_states.json与单工作流文件workflows/{id}.json存储相同数据；Skill层agents/与MCP层data/agents/目录完全镜像；Skill层scripts/与MCP层data/scripts/目录完全镜像。5个JSON持久化文件分散存储，无事务保证 |
| **A-03** | 命令步骤重复 | Skill | SKILL_REVIEW.md §5.2 | SKILL.md中27命令的详细步骤（L213-L378）与commands/*.md文件内容完全重复，导致维护时需同步修改两处，且SKILL.md内嵌步骤无法按需加载，违背渐进式加载设计初衷 |

### 1.2 P2 — 高优先级问题（9项）

| 编号 | 问题 | 所属端 | 来源文档 | 详细描述 |
|------|------|--------|----------|----------|
| **D-01** | 并发写入无事务保证 | 数据 | DATABASE_DESIGN.md §5.1, ARCHITECTURE.md §8.4 | 5个JSON文件使用threading.Lock+atomic_write，但仅进程级锁有效，多进程场景下数据可能丢失。gate_cache.json与file_hashes.json按project_path分散，缺乏统一管理 |
| **D-02** | 持久化文件分散无索引 | 数据 | DATABASE_DESIGN.md §5.1 | 5个JSON文件(workflow_states/agent_instances/gate_cache/tool_metrics/degradation_stats)全量加载到内存后O(n)过滤，无索引查询能力。工作流快照gzip压缩文件无限增长风险(虽有TTL+数量限制但依赖server_health调用触发清理) |
| **D-05** | 降级策略双源定义 | Skill/MCP | ARCHITECTURE.md §7.1, SKILL_REVIEW.md §5.2 | 降级策略同时定义在SKILL.md降级表(L141-L148)和degradation.py FALLBACK_MAP中，两处映射关系需手动同步。SKILL.md中session_manage降级脚本描述与mcp-tools.md中不一致 |
| **M-07** | MCP Resource URI降级路径缺失 | MCP/API | SKILL_REVIEW.md §5.2 | xuansto://协议URI依赖MCP Server实现，降级模式下无法访问7个Resource。需为每个Resource URI提供文件系统降级路径，当前仅resource_load_status有降级(读resource_state.json) |
| **M-09** | Hook拦截与降级脚本映射不一致 | MCP | API_SPECIFICATION.md §1.1.10, MCP_REVIEW.md §1.5 | config.py DEFAULT_HOOK_SCRIPTS_MAP定义16个Hook脚本映射，但degradation.py hook_manage_fallback仅硬编码3个Hook脚本(encoding-check/token-budget-check/session-save)，其余13个Hook降级时直接返回空列表 |
| **S-07** | 门禁别名映射冗余 | Skill | SKILL_REVIEW.md §5.2 | quality-gates.md中存在大量"已合并至"的别名映射，增加理解成本和维护负担。54项门禁中部分ID已废弃但仍保留别名 |
| **S-10** | 工作流命名不完整 | Skill | SKILL_REVIEW.md §5.2 | 存在sdd-tdd-full/medium/fast三种工作流，但SKILL.md仅详细描述了full工作流的Phase定义，medium/fast工作流缺乏详细步骤说明 |
| **E-02** | API响应格式不统一 | API | MCP_REVIEW.md §1.6, API_SPECIFICATION.md §4.1 | quality_gate_check返回`{gates_checked, gates_passed, results}`但API_SPECIFICATION定义`{checks, summary}`；部分Tool返回裸dict而非标准`{error, api_version, data}`结构；degradation_level字段位置不一致(有时在data内，有时在顶层) |
| **E-03** | 缺乏API版本协商机制 | API | API_SPECIFICATION.md §4.2 | 当前MCP_API_VERSION="1.0.0"仅作为响应字段返回，无客户端版本声明和服务器版本校验。Skill与MCP Server版本不匹配时无预警机制 |

### 1.3 P3 — 中低优先级问题（11项）

| 编号 | 问题 | 所属端 | 来源文档 | 详细描述 |
|------|------|--------|----------|----------|
| **D-03** | resource_state.json双格式兼容 | 数据 | DATABASE_DESIGN.md §4.1 | _load_resource_state()需同时兼容旧格式(纯列表)和新格式(带版本号对象)，增加维护成本。旧格式在首次写入时自动升级但无迁移完成标记 |
| **D-04** | 缓存失效检测粒度粗 | 数据 | DATABASE_DESIGN.md §1.3.6 | gate_cache.json通过文件SHA256哈希校验缓存有效性，但任何文件变更都导致整个缓存失效，无法增量更新。file_hashes.json按mtime跳过哈希计算，但mtime不可靠(如git checkout) |
| **M-02** | 内嵌逻辑代码分散 | MCP | ARCHITECTURE.md §7.1 | ~800行内嵌降级逻辑(_inline_*函数)分布在8个tool文件中，与主逻辑耦合。degradation.py通过`from ..tools.xxx import _inline_xxx`反向引用tool模块，形成循环依赖风险 |
| **M-05** | 配置热重载平台差异 | MCP | ARCHITECTURE.md §8.2 | Windows使用5秒轮询检测配置变更，Unix使用SIGHUP信号。两种机制行为不一致：轮询有延迟，SIGHUP即时但Windows不可用 |
| **M-06** | server_health无参数校验Schema | MCP | API_SPECIFICATION.md §1.1.13 | server_health是唯一无Pydantic Schema的Tool，直接调用无参数校验。与其他12个Tool的参数校验模式不一致 |
| **M-08** | 降级脚本路径不一致 | MCP/Skill | SKILL_REVIEW.md §5.2 | 部分MCP工具的降级脚本路径在不同位置描述不一致：SKILL.md中session_manage降级为init-session.py/session-catchup.py，mcp-tools.md中还包含session-persist.py |
| **S-06** | Agent frontmatter字段不一致 | Skill | SKILL_REVIEW.md §5.2 | 57个Agent定义文件(.md)中frontmatter字段不统一，部分缺少必要字段(如capabilities/priority)，虽有agent-frontmatter-validator.py但未强制执行 |
| **S-08** | Token预算目标缺乏实测数据 | 披露 | SKILL_REVIEW.md §5.2 | progressive-loading.md中性能目标"当前值"仍为全量加载的估算值(~8K触发/~15K单命令/~84K全流程)，缺乏渐进式加载后的实际测量数据 |
| **S-09** | /loop命令降级策略过长 | Skill | SKILL_REVIEW.md §5.2 | /loop调用全部13个MCP工具，降级脚本列表过长，实际执行时可能无法全部降级。应按Phase分批降级而非一次性列出所有降级脚本 |
| **E-04** | 缺乏重试机制 | API | API_SPECIFICATION.md §5.3 | 当前无显式重试机制，降级即视为最终策略。INTERNAL_ERROR等可恢复错误应支持指数退避重试 |
| **I-01** | stdio传输限制远程调用 | 架构 | ARCHITECTURE.md §8.2 | MCP Server仅支持stdio传输，不支持HTTP/SSE，限制远程调用和分布式部署场景 |
| **I-02** | 文件系统依赖不支持分布式 | 架构 | ARCHITECTURE.md §8.2 | 知识库、会话、工作流状态均依赖本地文件系统，不支持多进程/多机器部署 |

---

## 2. 影响链分析

### 2.1 A-01 SKILL.md膨胀 — 影响链

```
SKILL.md (~416行)
├── 触发条件定义 (L1-L16) → Host匹配引擎 → Skill触发延迟
├── 命令路由表 (L180-L211) → Skill路由决策 → 27命令分发
├── 命令详细步骤 (L213-L378) → 与commands/*.md重复 → 维护双源
├── Agent索引表 (L379-L397) → 与xuansto://references/agent-registry重复
├── 降级策略表 (L141-L148) → 与degradation.py FALLBACK_MAP重复
└── 渐进式加载定义 (L66-L108) → 与resource_load_status实现重复

修改影响:
  SKILL.md瘦身 → commands/*.md成为唯一步骤源 → 需验证27个命令文件完整性
  SKILL.md瘦身 → 降级策略统一到degradation.py → 需更新SKILL.md降级表引用
  SKILL.md瘦身 → Agent索引改用MCP Resource → 需确保xuansto://references/agent-registry可用
  Token消耗: ~10K → ~3K (-70%)
```

### 2.2 A-02 数据镜像冗余 — 影响链

```
Skill层 .trae/skills/xuansto-skill-v2/
├── agents/ (57个.md) ←──镜像──→ MCP层 data/agents/ (57个.md)
├── scripts/ (89+脚本) ←──镜像──→ MCP层 data/scripts/ (89+脚本)
├── hooks/hooks.json ←──镜像──→ MCP层 data/hooks/hooks.json
└── templates/ (19个) ←──镜像──→ MCP层 data/templates/ (19个)

持久化冗余:
├── workflow_states.json ←→ workflows/{id}.json (同数据双文件)
├── gate_cache.json + file_hashes.json (分散存储)
└── tool_metrics.json + degradation_stats.json (分散存储)

修改影响:
  消除镜像 → 需建立单一数据源(Skill层或MCP层) → 另一层通过MCP Resource/文件引用访问
  合并持久化 → 引入SQLite xuansto_state.db → 需迁移5个JSON文件 → 需保留JSON降级读取
  风险: 数据源切换期间可能存在读写不一致窗口
```

### 2.3 A-03 命令步骤重复 — 影响链

```
SKILL.md 命令详细步骤 (L213-L378)
  ↓ 完全重复
commands/*.md (27个文件)

修改影响:
  删除SKILL.md内嵌步骤 → commands/*.md成为唯一权威源
  → 渐进式加载Phase 1按需读取commands/{cmd}.md → 需确保文件路径映射正确
  → 27个命令文件需逐一验证内容完整性
  → SKILL.md命令路由表保留概要，详细步骤引用commands/
  风险: commands/目录缺失文件时命令步骤不可用
```

### 2.4 D-01 并发写入无事务保证 — 影响链

```
当前: JSON文件 + threading.Lock + atomic_write
  ├── workflow_dispatch → _persist_active_workflows() → workflow_states.json
  ├── agent_status → _persist_agent_instances() → agent_instances.json
  ├── quality_gate_check → _save_gate_cache() → gate_cache.json
  ├── server_health → _persist_metrics() → tool_metrics.json + degradation_stats.json
  └── session_manage → _track_session() → current.json

修改影响:
  引入SQLite WAL模式 → 5个JSON文件迁移到xuansto_state.db
  → 需修改5个tool模块的读写逻辑
  → 需保留JSON降级读取(启动时SQLite不可用回退到JSON)
  → threading.Lock替换为SQLite内置锁
  风险: SQLite WAL在NFS上不可靠(但当前仅本地文件系统)
```

### 2.5 D-05 降级策略双源定义 — 影响链

```
SKILL.md 降级表 (L141-L148)
  ↓ 定义
  13个Tool的降级脚本路径和降级模式功能范围

degradation.py FALLBACK_MAP (L363-L377)
  ↓ 定义
  13个Tool的降级函数映射

不一致点:
  SKILL.md: session_manage → init-session.py / session-catchup.py
  degradation.py: session_manage → init-session.py / session-catchup.py / session-persist.py (三级)

修改影响:
  统一到degradation.py + 配置文件 → SKILL.md仅引用降级模式说明
  → 需在.xuansto-config.yaml中定义降级脚本映射(当前仅在config.py硬编码)
  → 需同步更新SKILL.md降级模式功能范围表
  风险: 降级路径变更需同时更新3处(degradation.py + config.py + SKILL.md)
```

### 2.6 M-07 MCP Resource URI降级路径缺失 — 影响链

```
7个MCP Resource:
  xuansto://config/skill → .skill-config.yaml (降级: 直接读文件 ✓)
  xuansto://references/quality-gates → references/quality-gates.md (降级: 无 ✗)
  xuansto://references/agent-registry → references/agent-registry.md (降级: 无 ✗)
  xuansto://references/workflow-phases → references/workflow-phases.md (降级: 无 ✗)
  xuansto://templates/{name} → templates/{name}.md (降级: 无 ✗)
  xuansto://sessions/latest → sessions/session-*.md (降级: 无 ✗)
  xuansto://loading/status → resource_state.json (降级: 内联读取 ✓)

修改影响:
  为5个Resource添加文件系统降级路径 → 需在Skill层定义URI→文件映射
  → 需在SKILL.md或routing.yaml中声明降级路径
  → 渐进式加载降级模式下仍可访问参考文档
  风险: 降级路径与MCP Server实际文件路径不同步
```

### 2.7 E-02 API响应格式不统一 — 影响链

```
当前不一致:
  quality_gate_check: 返回 {gates_checked, gates_passed, gates_failed, results, phase, can_proceed}
  API_SPECIFICATION定义: {checks, summary: {total, passed, failed, skipped, blocked}, cache_info}
  degradation_level: 有时在data内，有时在顶层

修改影响:
  统一响应格式 → 需修改13个Tool的返回值结构
  → 需更新SKILL.md命令路由表中的降级策略描述
  → 需更新API_SPECIFICATION.md
  → Skill层需适配新响应格式
  风险: 破坏性变更，需API版本升级(MAJOR: 1.0.0 → 2.0.0)
```

### 2.8 其他问题影响链摘要

| 编号 | 核心影响文件 | 连锁影响模块 | 风险扩散范围 |
|------|-------------|-------------|-------------|
| D-02 | 5个JSON持久化文件 | workflow_dispatch, agent_status, quality_gate_check, server_health, session_manage | 引入SQLite需修改5个tool模块 |
| D-03 | resource_load_status.py | resource_load_status, skill_resources.py | 格式兼容逻辑增加维护负担 |
| D-04 | quality_gate_check.py | quality_gate_check, 所有依赖门禁的命令 | 缓存策略变更影响门禁检查性能 |
| M-02 | 8个tool文件的_inline_*函数 | degradation.py, 所有tool模块 | 提取到独立模块需修改import路径 |
| M-05 | config.py | server.py, 所有依赖配置的tool | 配置热重载机制变更影响运行时行为 |
| M-06 | server_health | server.py, schemas.py | 新增Schema需版本兼容 |
| M-08 | degradation.py, SKILL.md | 所有降级路径引用 | 路径统一需同步3处定义 |
| M-09 | hook_manage.py, degradation.py | hook_manage, 所有Pre/Post Hook | Hook降级覆盖从3/16提升到16/16 |
| S-06 | agents/*.md (57个文件) | agent_status, agent-frontmatter-validator.py | 统一frontmatter需修改57个文件 |
| S-07 | references/quality-gates.md | quality_gate_check, 所有门禁引用 | 清理别名需更新门禁ID引用 |
| S-08 | progressive-loading.md, SKILL.md | resource_load_status | 实测数据影响加载阶段Token预算设定 |
| S-09 | commands/loop.md, SKILL.md | /loop命令降级链 | 分批降级需修改loop命令定义 |
| S-10 | workflows/*.md, SKILL.md | workflow_dispatch | 补充工作流定义需修改YAML frontmatter |
| E-03 | config.py, server.py | 所有MCP Tool响应 | 版本协商需修改请求/响应协议 |
| E-04 | degradation.py, 所有tool | 所有MCP Tool调用链 | 重试机制需修改server.py Hook拦截层 |
| I-01 | server.py | MCP传输层 | 传输协议变更影响所有客户端 |
| I-02 | 5个tool模块 | 所有持久化操作 | 存储抽象层需修改5个tool模块 |

---

## 3. 优先级划分

### 3.1 划分依据

| 维度 | 权重 | 说明 |
|------|------|------|
| 用户感知 | 30% | 直接影响用户体验(延迟/错误/功能缺失) |
| 功能正确性 | 30% | 影响核心功能(SDD/TDD流程/门禁/降级) |
| 安全性 | 20% | 数据丢失/并发冲突/注入风险 |
| 依赖解耦 | 20% | 模块间耦合度/可维护性/可测试性 |

### 3.2 紧急级（阻塞重构）

必须首先解决，否则后续重构无法安全推进。

| 编号 | 问题 | 紧急原因 | 前置依赖 |
|------|------|----------|----------|
| A-01 | SKILL.md膨胀 | Token消耗~10K阻塞渐进式加载优化，所有Skill层重构依赖SKILL.md瘦身 | 无 |
| A-03 | 命令步骤重复 | SKILL.md瘦身必须先消除重复，否则删除内嵌步骤后需验证commands/完整性 | A-01 |
| A-02 | 数据镜像冗余 | 持久化层重构必须先消除镜像，否则SQLite迁移时双源数据不一致 | 无 |

### 3.3 高优先级（核心功能缺失/正确性风险）

| 编号 | 问题 | 高优先原因 | 前置依赖 |
|------|------|-----------|----------|
| D-01 | 并发写入无事务保证 | 数据丢失风险，多进程场景下workflow/agent状态可能损坏 | A-02 |
| D-02 | 持久化文件分散无索引 | O(n)查询性能，大量工作流时I/O瓶颈 | A-02 |
| D-05 | 降级策略双源定义 | 维护不同步导致降级失败，影响Skill-MCP协议正确性 | A-01 |
| M-07 | Resource URI降级路径缺失 | MCP不可用时5个Resource无法访问，影响降级模式功能完整性 | A-01 |
| M-09 | Hook降级映射不一致 | 13/16个Hook降级时直接返回空列表，Hook拦截形同虚设 | D-05 |
| S-07 | 门禁别名映射冗余 | 增加门禁检查理解成本，可能引用已废弃ID | 无 |
| S-10 | 工作流命名不完整 | medium/fast工作流缺乏详细定义，用户选择后步骤不明确 | 无 |
| E-02 | API响应格式不统一 | Skill层无法统一处理响应，增加适配代码复杂度 | A-01 |
| E-03 | 缺乏API版本协商 | 版本不匹配时无预警，可能导致静默错误 | E-02 |

### 3.4 中优先级（优化项）

| 编号 | 问题 | 中优先原因 | 前置依赖 |
|------|------|-----------|----------|
| D-03 | resource_state.json双格式 | 兼容逻辑增加维护成本但不影响功能 | D-01 |
| D-04 | 缓存失效检测粒度粗 | 影响门禁检查性能但不影响正确性 | D-01 |
| M-02 | 内嵌逻辑代码分散 | 代码组织问题，不影响运行时行为 | D-05 |
| M-05 | 配置热重载平台差异 | Windows延迟5秒可接受 | 无 |
| M-06 | server_health无Schema | 不影响功能，仅代码一致性 | E-02 |
| M-08 | 降级脚本路径不一致 | 文档描述问题，degradation.py实际行为正确 | D-05 |
| S-06 | Agent frontmatter不一致 | 有validator但未强制，不影响运行时 | 无 |
| S-08 | Token预算缺乏实测 | 影响优化目标设定但不影响功能 | A-01 |
| S-09 | /loop降级策略过长 | 降级可能不完整但主流程正常 | D-05 |

### 3.5 低优先级（锦上添花）

| 编号 | 问题 | 低优先原因 | 前置依赖 |
|------|------|-----------|----------|
| E-04 | 缺乏重试机制 | 降级链已提供容错，重试为增强项 | E-02 |
| I-01 | stdio传输限制 | 当前单机场景足够，远程调用为远期需求 | 无 |
| I-02 | 文件系统依赖 | 当前单机场景足够，分布式为远期需求 | D-01 |

---

## 4. 模块化重构步骤

重构拆分为4个独立可测试的阶段，每阶段有明确的输入/输出/验收标准/依赖关系。

### 阶段1: Skill定义瘦身与数据源统一

**目标**: SKILL.md从~416行瘦身至~120行，消除命令步骤重复，建立单一数据源。

**前置依赖**: 无

**输入**:
- 当前SKILL.md (~416行)
- commands/ 目录 (27个.md文件)
- degradation.py FALLBACK_MAP
- references/ 目录 (6个参考文档)

**步骤**:

| 步骤 | 操作 | 涉及文件 | 产出 |
|------|------|----------|------|
| 1.1 | 创建commands/routing.yaml，将SKILL.md命令路由表(L180-L211)提取为YAML格式 | 新建: commands/routing.yaml | 27命令的MCP工具调用链+降级策略YAML定义 |
| 1.2 | 删除SKILL.md中27命令详细步骤(L213-L378)，替换为"详见commands/{cmd}.md"引用 | 修改: SKILL.md | SKILL.md减少~165行 |
| 1.3 | 验证27个commands/*.md文件完整性，补全缺失内容 | 验证: commands/*.md | 27个命令文件内容完整且与原SKILL.md一致 |
| 1.4 | 将SKILL.md降级模式功能范围表(L47-L65)替换为引用degradation.py | 修改: SKILL.md | 降级策略单一来源: degradation.py |
| 1.5 | 将SKILL.md Agent索引表(L379-L397)替换为MCP Resource引用 | 修改: SKILL.md | Agent索引单一来源: xuansto://references/agent-registry |
| 1.6 | 消除Skill层与MCP层数据镜像，MCP层data/目录为唯一数据源 | 修改: Skill层agents/scripts/hooks/templates引用路径 | Skill层通过MCP Resource或相对路径引用MCP层数据 |
| 1.7 | 为5个MCP Resource添加文件系统降级路径声明 | 修改: SKILL.md或routing.yaml | 7个Resource均有降级路径 |

**输出**:
- SKILL.md ~120行 (触发条件+核心约束+加载阶段+命令概要+引用)
- commands/routing.yaml (命令路由独立定义)
- 27个commands/*.md (唯一命令步骤权威源)
- 数据镜像消除 (单一数据源: MCP层data/)

**验收标准**:
- [ ] SKILL.md行数 ≤ 150行
- [ ] SKILL.md Token消耗 ≤ 3K (实测)
- [ ] 27个commands/*.md文件均存在且内容完整
- [ ] commands/routing.yaml可被YAML解析器正确解析
- [ ] 所有MCP Resource有降级路径声明
- [ ] Skill层无独立agents/scripts/hooks/templates副本(或为符号链接)

### 阶段2: MCP Server持久化层重构

**目标**: 引入SQLite状态库，消除5个JSON文件分散存储，提供事务安全和索引查询。

**前置依赖**: 阶段1 (数据镜像消除后，仅需迁移MCP层数据)

**输入**:
- 5个JSON持久化文件 (workflow_states/agent_instances/gate_cache/tool_metrics/degradation_stats)
- 当前各tool模块的读写逻辑
- DATABASE_DESIGN.md §5.2 建议的SQLite Schema

**步骤**:

| 步骤 | 操作 | 涉及文件 | 产出 |
|------|------|----------|------|
| 2.1 | 创建core/persistence.py，封装SQLite连接管理(WAL模式+busy_timeout) | 新建: core/persistence.py | SQLite连接池+事务上下文管理器 |
| 2.2 | 创建xuansto_state.db Schema (9张表) | 新建: core/schema.sql | workflow_instances/agent_instances/gate_cache/tool_metrics/degradation_stats/session_states/resource_states/patterns/workflow_snapshots |
| 2.3 | 迁移workflow_dispatch持久化: JSON → SQLite workflow_instances表 | 修改: tools/workflow_dispatch.py | _persist_active_workflows/_load_active_workflows改用SQLite |
| 2.4 | 迁移agent_status持久化: JSON → SQLite agent_instances表 | 修改: tools/agent_status.py | _persist_agent_instances/_load_agent_instances改用SQLite |
| 2.5 | 迁移quality_gate_check缓存: JSON → SQLite gate_cache表 | 修改: tools/quality_gate_check.py | _save_gate_cache/_load_gate_cache改用SQLite |
| 2.6 | 迁移server_health指标: JSON → SQLite tool_metrics+degradation_stats表 | 修改: tools/server_health.py | _persist_metrics/metrics_load_on_startup改用SQLite |
| 2.7 | 迁移session_manage状态: JSON → SQLite session_states表 | 修改: tools/session_manage.py | _track_session/_restore_session改用SQLite |
| 2.8 | 添加启动迁移逻辑: 检测JSON文件→导入SQLite→备份JSON→删除原文件 | 修改: server.py main() | 启动时自动迁移，保留.json.bak备份 |
| 2.9 | 添加JSON降级读取: SQLite不可用时回退到JSON文件 | 修改: core/persistence.py | 降级读取逻辑，确保向前兼容 |

**输出**:
- xuansto_state.db (SQLite WAL模式状态库)
- core/persistence.py (统一持久化层)
- 5个tool模块改用SQLite读写
- .json.bak备份文件(迁移后保留)

**验收标准**:
- [ ] xuansto_state.db包含9张表且Schema正确
- [ ] 启动时自动检测并迁移JSON数据到SQLite
- [ ] 迁移后原JSON文件备份为.json.bak
- [ ] SQLite不可用时自动降级到JSON读取
- [ ] 并发写入测试: 10个线程同时写入workflow_instances无数据丢失
- [ ] 查询性能: workflow_instances按status索引查询 < 1ms

### 阶段3: 降级链统一与API规范化

**目标**: 降级策略单一来源，API响应格式统一，Hook降级覆盖完整。

**前置依赖**: 阶段1 (SKILL.md瘦身) + 阶段2 (持久化层稳定)

**输入**:
- degradation.py FALLBACK_MAP (13个降级函数)
- config.py DEFAULT_GATE_SCRIPTS_MAP / DEFAULT_HOOK_SCRIPTS_MAP
- 13个Tool的当前返回值结构
- API_SPECIFICATION.md定义的目标响应格式

**步骤**:

| 步骤 | 操作 | 涉及文件 | 产出 |
|------|------|----------|------|
| 3.1 | 提取8个tool文件中的_inline_*函数到core/inline_fallbacks.py | 新建: core/inline_fallbacks.py; 修改: 8个tool文件 | 内嵌降级逻辑独立模块，消除循环依赖 |
| 3.2 | 将降级脚本映射从config.py硬编码迁移到.xuansto-config.yaml | 修改: config.py, .xuansto-config.yaml | 降级脚本映射配置化，SKILL.md/degradation.py均从配置读取 |
| 3.3 | 补全hook_manage降级: 16个Hook全部有降级路径 | 修改: degradation.py hook_manage_fallback | Hook降级覆盖率从3/16提升到16/16 |
| 3.4 | 统一13个Tool的响应格式为`{error, api_version, data, degradation_level}` | 修改: 13个tool模块 | 所有Tool返回标准结构，degradation_level始终在顶层 |
| 3.5 | 修复quality_gate_check响应格式: results→checks, 添加summary和cache_info | 修改: tools/quality_gate_check.py | 响应格式与API_SPECIFICATION一致 |
| 3.6 | 添加API版本协商: 请求携带api_version，响应校验版本兼容性 | 修改: server.py, core/config.py | API_VERSION从1.0.0升级到2.0.0，支持版本协商 |
| 3.7 | 为server_health添加Pydantic Schema (ServerHealthInput) | 新增: schemas.py ServerHealthInput | 13个Tool全部有Pydantic Schema |
| 3.8 | 清理quality-gates.md中已废弃的门禁别名 | 修改: references/quality-gates.md | 仅保留当前有效的54项门禁ID |
| 3.9 | 补充sdd-tdd-medium/fast工作流详细定义 | 修改: workflows/sdd-tdd-medium.md, sdd-tdd-fast.md | 3种工作流均有完整Phase定义 |

**输出**:
- core/inline_fallbacks.py (独立内嵌降级模块)
- 统一的API响应格式 (v2.0.0)
- 完整的Hook降级覆盖 (16/16)
- 配置化的降级脚本映射
- 清理后的门禁定义
- 完整的工作流定义

**验收标准**:
- [ ] 13个Tool返回值均为`{error, api_version, data, degradation_level}`标准结构
- [ ] degradation_level字段始终在响应顶层
- [ ] quality_gate_check返回checks+summary+cache_info
- [ ] 16个Hook均有降级路径(脚本或内嵌逻辑)
- [ ] 降级脚本映射从.xuansto-config.yaml读取
- [ ] API版本协商: 客户端发送api_version="2.0.0"，服务端校验兼容性
- [ ] server_health有Pydantic Schema
- [ ] quality-gates.md无已废弃别名
- [ ] sdd-tdd-medium/fast工作流有完整Phase定义

### 阶段4: 渐进式加载披露增强与集成

**目标**: 完善渐进式加载披露的状态机、过渡动画、性能指标，实现真正的按需加载。

**前置依赖**: 阶段1 (SKILL.md瘦身) + 阶段3 (API规范化)

**输入**:
- 当前resource_load_status工具 (5个action)
- 当前xuansto://loading/status Resource
- SKILL_REVIEW.md §4 加载披露逻辑分析
- progressive-loading.md规范

**步骤**:

| 步骤 | 操作 | 涉及文件 | 产出 |
|------|------|----------|------|
| 4.1 | 实现LoadPhase状态机: 严格的状态转换规则+转换条件校验 | 修改: tools/resource_load_status.py | LoadPhaseStateMachine类，禁止非法转换(如skeleton→full跳跃) |
| 4.2 | 实现DisclosureTransition过渡披露: 每次Phase转换返回新旧功能对比 | 修改: tools/resource_load_status.py, resources/skill_resources.py | 过渡披露包含from_phase/to_phase/added_functions/removed_functions/disclosure_note |
| 4.3 | 添加Token预算追踪: loading/status增加estimated_total_tokens和token_budget_remaining | 修改: tools/resource_load_status.py | Token估算基于已加载资源大小，预算剩余=总预算-已消耗 |
| 4.4 | 添加加载错误上报: loading_progress增加errors和estimated_remaining_ms | 修改: tools/resource_load_status.py | 加载失败时上报错误信息，预估剩余时间 |
| 4.5 | 实现MCP Notification进度推送(混合模式) | 修改: tools/resource_load_status.py, server.py | batch_mode下注册progressToken，每资源加载完成推送notifications/progress |
| 4.6 | 实测渐进式加载Token消耗: skeleton/functional/enhanced/full四阶段 | 新增: tests/test_token_budget.py | 实测数据替换progressive-loading.md中的估算值 |
| 4.7 | 添加资源依赖声明: 资源清单增加depends_on和priority字段 | 修改: tools/resource_load_status.py PHASE_RESOURCE_MAP | 资源加载按依赖拓扑排序，depends_on资源先加载 |
| 4.8 | 添加缓存命中率统计: cache操作增加hit_rate字段 | 修改: tools/resource_load_status.py | 缓存命中率=命中次数/(命中+未命中) |

**输出**:
- LoadPhaseStateMachine (严格状态转换)
- DisclosureTransition (过渡披露)
- Token预算追踪
- MCP Notification进度推送
- 实测Token消耗数据
- 资源依赖拓扑
- 缓存命中率

**验收标准**:
- [ ] LoadPhase状态机拒绝非法转换(如skeleton→full)
- [ ] 每次Phase转换返回DisclosureTransition(新旧功能对比)
- [ ] loading/status包含estimated_total_tokens和token_budget_remaining
- [ ] loading_progress包含errors和estimated_remaining_ms
- [ ] batch_mode下MCP Notification推送进度
- [ ] 实测Token消耗: skeleton≤2K, functional≤5K, enhanced≤8K, full≤12K
- [ ] 资源按depends_on拓扑排序加载
- [ ] cache操作返回hit_rate

---

## 5. 渐进式加载披露实现方案

### 5.1 分阶段加载策略

#### 5.1.1 四级加载层次详细设计

| 层次 | 名称 | 触发条件 | 加载内容 | Token预估 | 对应LoadPhase |
|------|------|----------|----------|-----------|---------------|
| Level 0 | 骨架(Skeleton) | Skill触发时自动 | SKILL.md核心约束(5条) + 命令概要(27命令→MCP Tool映射) + Agent索引(57 Agent按层级) + MCP Server依赖声明 + 降级模式入口 | ~2K | SKELETON |
| Level 1 | 功能(Functional) | 用户执行命令时 | 当前命令详细步骤(commands/{cmd}.md) + 当前工作流Phase定义 + MCP工具参数Schema + Hook系统配置 | ~3K | FUNCTIONAL |
| Level 2 | 增强(Enhanced) | 需要参考文档时 | 参考文档(quality-gates.md等) + 模板文件 + 知识库索引(ChromaDB/FTS5元数据) + Agent详细定义(按需) | ~5K | ENHANCED |
| Level 3 | 完整(Full) | 深度分析时 | 完整脚本集(scripts/) + 披露资源(加载状态/功能可用性) + 评估配置 + 全部Agent定义 + 全部参考文档 | ~10K | FULL |

#### 5.1.2 骨架屏/占位符设计

在SKELETON阶段，未加载的功能以"占位符"形式呈现，用户可感知功能存在但尚未可用：

```
┌─────────────────────────────────────────┐
│  Xuansto Skill v8.0.0 (已激活)          │
│  ─────────────────────────────────────  │
│  ✓ 命令路由 (27命令可用)                │
│  ✓ Agent索引 (57 Agent可查询)           │
│  ✓ 核心约束 (Spec>Test>Code)            │
│  ─────────────────────────────────────  │
│  ○ 命令详细步骤 → 执行命令时加载        │
│  ○ 参考文档 → 需要时加载                │
│  ○ 知识检索 → 增强阶段可用              │
│  ○ 完整脚本集 → 深度分析时加载          │
│  ─────────────────────────────────────  │
│  当前阶段: SKELETON | 已加载: 2K Token  │
│  推进加载: resource_load_status(preload) │
└─────────────────────────────────────────┘
```

#### 5.1.3 低精度资源→高精度资源过渡

| 过渡 | 低精度(占位) | 高精度(实际) | 过渡条件 |
|------|-------------|-------------|----------|
| 命令步骤 | 命令名+MCP工具概要(1行) | 完整分步执行流程(commands/{cmd}.md) | 用户执行该命令 |
| Agent定义 | 名称+层级+状态(1行) | 完整角色定义(agents/{layer}/{name}.md) | agent_status(detail)调用 |
| 参考文档 | 文件名+大小(1行) | 完整文档内容(references/{name}.md) | 知识检索或显式请求 |
| 门禁定义 | 门禁ID+严重级别(1行) | 完整检查逻辑+通过条件(quality-gates.md) | quality_gate_check调用 |
| 模板文件 | 模板名+描述(1行) | 完整模板内容(templates/{name}.md) | 工作流需要模板时 |

#### 5.1.4 交互动效设计

| 交互 | 动效 | 实现 |
|------|------|------|
| Phase推进 | 从旧Phase到新Phase的功能解锁动画 | DisclosureTransition返回added_functions列表，Skill层逐项展示解锁功能 |
| 资源预加载 | 进度条(0%→100%) | resource_load_status(loading_progress)返回progress_percent，Skill层展示进度 |
| Token预算紧张 | 降级预警 | Token使用率>60%时P3资源释放，>80%时P2释放，>95%时P1释放(仅保留当前命令) |
| 功能不可用 | 灰色占位+提示 | 不可用功能显示为"○ 功能名 → 推进到X阶段可用" |
| 加载失败 | 错误提示+降级方案 | 加载失败时显示"✗ 资源加载失败，使用降级方案: [降级描述]" |

### 5.2 状态机设计

#### 5.2.1 LoadPhase状态机

```python
class LoadPhaseStateMachine:
    TRANSITIONS = {
        (LoadPhase.SKELETON, LoadPhase.FUNCTIONAL): {
            "trigger": "command_execution",
            "condition": "用户执行命令 或 Phase进入",
            "action": "preload当前Phase资源",
        },
        (LoadPhase.FUNCTIONAL, LoadPhase.ENHANCED): {
            "trigger": "reference_request",
            "condition": "agent_status(detail) 或 参考文档请求",
            "action": "加载Agent定义+参考文档",
        },
        (LoadPhase.ENHANCED, LoadPhase.FULL): {
            "trigger": "deep_analysis",
            "condition": "/build-desktop 或 /loop 命令",
            "action": "加载全部资源",
        },
        (LoadPhase.FULL, LoadPhase.ENHANCED): {
            "trigger": "token_pressure_80",
            "condition": "Token使用率>80%",
            "action": "context_compress + 释放P3资源",
        },
        (LoadPhase.ENHANCED, LoadPhase.FUNCTIONAL): {
            "trigger": "token_pressure_95",
            "condition": "Token使用率>95%",
            "action": "释放P2资源(参考文档+模板+知识库缓存)",
        },
        (LoadPhase.FUNCTIONAL, LoadPhase.SKELETON): {
            "trigger": "token_pressure_95_idle",
            "condition": "Token使用率>95% 且 当前Phase无活动",
            "action": "仅保留P0资源(核心约束+命令概要+Agent索引)",
        },
    }

    def can_transition(self, from_phase: LoadPhase, to_phase: LoadPhase) -> bool:
        return (from_phase, to_phase) in self.TRANSITIONS

    def transition(self, from_phase: LoadPhase, to_phase: LoadPhase, context: dict) -> DisclosureTransition:
        if not self.can_transition(from_phase, to_phase):
            raise InvalidTransitionError(f"不允许从{from_phase}转换到{to_phase}")
        transition_def = self.TRANSITIONS[(from_phase, to_phase)]
        return DisclosureTransition(
            from_phase=from_phase,
            to_phase=to_phase,
            available_functions=self._compute_functions(to_phase),
            disclosure_note=self._generate_disclosure_note(from_phase, to_phase),
            trigger=transition_def["trigger"],
            action=transition_def["action"],
        )
```

#### 5.2.2 状态转换矩阵

```
                 ┌──────────────────────────────────────────┐
                 │              正向推进                      │
                 │                                          │
  SKELETON ──────→ FUNCTIONAL ──────→ ENHANCED ──────→ FULL
     ↑                  ↑                   ↑               │
     │                  │                   │               │
     │  Token>95%+idle  │  Token>95%        │  Token>80%    │
     │                  │                   │               │
     └──────────────────┴───────────────────┴───────────────┘
                         反向降级 (Token压力)
```

**禁止的转换**:
- SKELETON → ENHANCED (跳跃，必须经过FUNCTIONAL)
- SKELETON → FULL (跳跃，必须逐级推进)
- FUNCTIONAL → FULL (跳跃，必须经过ENHANCED)
- 任意Phase → 自身 (无意义)

### 5.3 过渡动画方案

#### 5.3.1 DisclosureTransition数据结构

```python
@dataclass
class DisclosureTransition:
    from_phase: LoadPhase
    to_phase: LoadPhase
    trigger: str
    action: str
    available_functions: dict[str, bool]
    added_functions: dict[str, bool]
    removed_functions: dict[str, bool]
    disclosure_note: str
    estimated_token_delta: int
    timestamp: float
```

#### 5.3.2 过渡披露模板

| 过渡 | 披露模板 |
|------|----------|
| SKELETON→FUNCTIONAL | "🎯 功能阶段已激活！新增: 命令执行、工作流推进、门禁检查。Token增量: +{delta}" |
| FUNCTIONAL→ENHANCED | "📚 增强阶段已激活！新增: 知识检索、参考文档、Agent详情。Token增量: +{delta}" |
| ENHANCED→FULL | "⚡ 完整阶段已激活！全部功能可用。Token增量: +{delta}" |
| FULL→ENHANCED | "⚠️ Token预算紧张(>80%)，已释放完整脚本集。保留: 知识检索、参考文档" |
| ENHANCED→FUNCTIONAL | "🔴 Token预算紧张(>95%)，已释放参考文档和知识库。保留: 命令执行、门禁检查" |
| FUNCTIONAL→SKELETON | "🔴 Token预算严重不足(>95%+空闲)，仅保留核心约束。建议: context_compress" |

### 5.4 性能指标

| 指标 | 当前值(全量) | 目标值(渐进式) | 测量方法 |
|------|-------------|---------------|----------|
| Skill触发时Token | ~10K | ≤2K | SKILL.md字数/4 |
| 单命令执行Token | ~15K | ≤5K | (SKILL.md+commands/{cmd}.md)字数/4 |
| 全流程Token(9 Phase) | ~84K | ≤30K | 各Phase累计Token |
| Agent调度Token(单次) | ~500/Agent | ≤150/Agent | agents/{name}.md字数/4 |
| 骨架加载延迟 | N/A | ≤500ms | resource_load_status(status)响应时间 |
| Phase资源预加载 | N/A | ≤2s/Phase | resource_load_status(preload)响应时间 |
| Agent定义按需加载 | N/A | ≤300ms/Agent | agent_status(detail)响应时间 |
| 知识检索响应 | 1-5s(ChromaDB) | ≤3s(hybrid) | knowledge_search(retrieve)响应时间 |
| 缓存命中率 | N/A | ≥70% | cache操作hit_rate字段 |

---

## 6. 测试策略

### 6.1 测试体系优化

当前测试目录: `xuansto-mcp-server/tests/`

**测试分层**:

```
tests/
├── unit/                    # 单元测试 (无外部依赖)
│   ├── test_schemas.py      # Pydantic Schema校验
│   ├── test_degradation.py  # 降级链逻辑
│   ├── test_persistence.py  # SQLite持久化层
│   ├── test_state_machine.py # LoadPhase状态机
│   ├── test_inline_fallbacks.py # 内嵌降级函数
│   └── test_config.py       # 配置管理
├── integration/             # 集成测试 (MCP协议联动)
│   ├── test_skill_mcp_protocol.py  # Skill-MCP协议联动
│   ├── test_loading_disclosure.py  # 渐进式加载流程
│   ├── test_workflow_lifecycle.py   # 工作流生命周期
│   └── test_hook_interception.py   # Hook拦截链
├── e2e/                     # 端到端测试 (用户输入到输出)
│   ├── test_command_execution.py    # 27命令执行
│   ├── test_sdd_tdd_workflow.py     # SDD+TDD完整流程
│   └── test_degradation_e2e.py      # 降级模式端到端
└── regression/              # 回归验证
    ├── test_api_compatibility.py    # API向后兼容
    ├── test_migration.py            # JSON→SQLite迁移
    └── test_skill_md_token.py       # SKILL.md Token消耗
```

### 6.2 单元测试

#### 6.2.1 MCP Tool逻辑测试

| 测试模块 | 测试用例数 | 覆盖重点 |
|----------|-----------|----------|
| test_schemas.py | 13×5=65 | 13个Pydantic Schema的字段类型/默认值/范围校验/extra="forbid" |
| test_degradation.py | 13×3=39 | 13个降级函数的脚本降级/内嵌降级/错误处理 |
| test_persistence.py | 9×4=36 | 9张SQLite表的CRUD/事务/WAL并发/迁移 |
| test_state_machine.py | 8+3=11 | 6个合法转换+2个非法转换+3个Token压力降级 |
| test_inline_fallbacks.py | 8×2=16 | 8个内嵌降级函数的正常/异常路径 |
| test_config.py | 5 | 配置加载/热重载/降级映射/路径解析 |

**关键测试用例示例**:

```python
# test_state_machine.py
def test_skeleton_to_functional_valid():
    sm = LoadPhaseStateMachine()
    transition = sm.transition(LoadPhase.SKELETON, LoadPhase.FUNCTIONAL, {"trigger": "command_execution"})
    assert transition.added_functions == {
        "command_execution": True, "quality_gates": True,
    }
    assert transition.removed_functions == {}

def test_skeleton_to_enhanced_invalid():
    sm = LoadPhaseStateMachine()
    with pytest.raises(InvalidTransitionError):
        sm.transition(LoadPhase.SKELETON, LoadPhase.ENHANCED, {})

def test_token_pressure_causes_downgrade():
    sm = LoadPhaseStateMachine()
    transition = sm.transition(LoadPhase.FULL, LoadPhase.ENHANCED, {"token_usage": 0.85})
    assert "full_scripts" in transition.removed_functions
```

#### 6.2.2 状态管理测试

| 测试场景 | 验证点 |
|----------|--------|
| 工作流状态CRUD | start→status→phase advance→abort，SQLite写入后可读取 |
| Agent实例CRUD | create→assign→release→destroy，实例数≤20限制 |
| 门禁缓存 | 首次检查→缓存命中→文件变更→缓存失效→重新检查 |
| 会话追踪 | track→restore→track更新→重启恢复 |
| 资源加载状态 | preload→status→cache→clear_cache→loading_progress |

### 6.3 集成测试

#### 6.3.1 Skill-MCP协议联动测试

| 测试场景 | 步骤 | 验证点 |
|----------|------|--------|
| 命令路由→MCP调用 | 用户输入"/review" → Skill路由 → quality_gate_check+security_scan+code_simplify | 3个Tool按序调用，响应格式统一 |
| 降级链联动 | 断开MCP Server → 执行"/review" → degradation.py降级 | 降级响应包含degradation_level，功能范围与SKILL.md降级表一致 |
| Hook拦截联动 | 执行"/implement" → Pre-hook(security-block) → Tool执行 → Post-hook(decision-log-persist) | Pre-hook可阻断，Post-hook不阻断 |
| Resource访问联动 | 读取xuansto://loading/status → 解析available_functions → 按需preload | Resource返回JSON可解析，available_functions与当前Phase一致 |

#### 6.3.2 渐进式加载流程测试

| 测试场景 | 步骤 | 验证点 |
|----------|------|--------|
| 完整加载流程 | SKELETON→FUNCTIONAL→ENHANCED→FULL | 每次转换返回DisclosureTransition，功能逐级解锁 |
| Token压力降级 | FULL→Token>80%→ENHANCED→Token>95%→FUNCTIONAL | 降级转换合法，功能按P3→P2→P1顺序释放 |
| 预加载+缓存 | preload Phase 4 → cache命中 → 再次preload → 缓存有效 | 缓存TTL=3600s，命中时返回cache="valid" |
| batch_mode | preload多个URI(batch_mode=True) → 进度推送 | 每个资源加载完成推送notifications/progress |

### 6.4 端到端测试

| 测试场景 | 用户输入 | 预期输出 | 验证点 |
|----------|----------|----------|--------|
| 新项目初始化 | "帮我搭建React项目" | 初始化报告+brainstorm工作流启动 | /init→/brainstorm自动路由，工作流ID非空 |
| 代码审查 | "/review" | 审查报告+安全扫描+简化建议 | 3个Tool结果汇总，门禁PASS/FAIL明确 |
| 安全审计 | "/audit" | 漏洞报告+渗透测试结果 | security_scan+AI-PENTEST门禁 |
| 降级模式 | 断开MCP + "/sprint" | 降级执行结果 | degradation_level非null，功能范围受限 |
| 自主循环 | "/loop" | 9阶段完整执行 | 每阶段门禁检查，Phase推进成功 |
| 桌面构建 | "/build-desktop" | 构建门禁检查结果 | DESKTOP-BUILD/SIGN/CROSS门禁 |

### 6.5 回归验证方案

| 回归项 | 验证方法 | 频率 |
|--------|----------|------|
| API向后兼容 | 发送api_version="1.0.0"请求，验证响应格式不变 | 每次API变更 |
| JSON→SQLite迁移 | 准备JSON测试数据，执行迁移，验证SQLite数据一致 | 每次持久化层变更 |
| SKILL.md Token消耗 | 统计SKILL.md字数/4，验证≤3K | 每次SKILL.md修改 |
| 降级链完整性 | 逐个Tool模拟MCP不可用，验证降级响应 | 每次降级逻辑变更 |
| 门禁检查结果 | 对比重构前后54项门禁检查结果 | 每次门禁逻辑变更 |
| 渐进式加载性能 | 测量4个Phase的Token消耗和响应时间 | 每次加载逻辑变更 |

---

## 7. 持续集成建议

### 7.1 自动化检查

#### 7.1.1 Lint检查

```yaml
# .github/workflows/ci.yml
lint:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - name: Python Lint
      run: |
        pip install ruff
        ruff check xuansto-mcp-server/src/
        ruff format --check xuansto-mcp-server/src/
    - name: YAML Lint
      run: |
        pip install yamllint
        yamllint .trae/skills/xuansto-skill-v2/configs/
        yamllint .trae/skills/xuansto-skill-v2/workflows/_yaml/
```

#### 7.1.2 Schema校验

```yaml
schema-validate:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - name: Pydantic Schema校验
      run: |
        pip install -e xuansto-mcp-server/
        python -c "
          from xuansto_mcp.models.schemas import *
          import json
          # 验证13个Schema均可实例化
          for cls in [SkillAnalyzeInput, KnowledgeSearchInput, QualityGateCheckInput,
                      SpecDriftDetectInput, SecurityScanInput, CodeSimplifyInput,
                      SessionManageInput, WorkflowDispatchInput, AgentStatusInput,
                      HookManageInput, ResourceLoadStatusInput, ContextCompressInput]:
              cls.model_json_schema()  # 验证Schema可生成
          print('All 12+1 Schemas validated')
        "
    - name: YAML Frontmatter校验
      run: |
        python -c "
          import yaml, glob
          for f in glob.glob('.trae/skills/xuansto-skill-v2/workflows/*.md'):
              with open(f) as fh:
                  content = fh.read()
                  if content.startswith('---'):
                      fm = yaml.safe_load(content.split('---')[1])
                      assert 'name' in fm, f'{f}: missing name in frontmatter'
          print('All workflow frontmatter validated')
        "
```

#### 7.1.3 MCP工具定义验证

```yaml
mcp-tool-validate:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - name: MCP工具注册验证
      run: |
        pip install -e xuansto-mcp-server/
        python -c "
          from xuansto_mcp.server import mcp, _REGISTERED_TOOL_NAMES, _REGISTERED_RESOURCE_NAMES
          # 验证13个Tool已注册
          expected_tools = ['skill_analyze', 'knowledge_search', 'quality_gate_check',
                           'spec_drift_detect', 'security_scan', 'code_simplify',
                           'session_manage', 'workflow_dispatch', 'agent_status',
                           'hook_manage', 'resource_load_status', 'context_compress',
                           'server_health']
          for t in expected_tools:
              assert t in _REGISTERED_TOOL_NAMES, f'Tool {t} not registered'
          print(f'All {len(expected_tools)} tools registered')
          # 验证7个Resource已注册
          expected_resources = ['xuansto://config/skill', 'xuansto://references/quality-gates',
                               'xuansto://references/agent-registry', 'xuansto://references/workflow-phases',
                               'xuansto://templates/{name}', 'xuansto://sessions/latest',
                               'xuansto://loading/status']
          for r in expected_resources:
              assert r in _REGISTERED_RESOURCE_NAMES, f'Resource {r} not registered'
          print(f'All {len(expected_resources)} resources registered')
        "
    - name: 降级链完整性验证
      run: |
        python -c "
          from xuansto_mcp.core.degradation import FALLBACK_MAP
          expected_tools = ['skill_analyze', 'knowledge_search', 'quality_gate_check',
                           'spec_drift_detect', 'security_scan', 'code_simplify',
                           'session_manage', 'workflow_dispatch', 'agent_status',
                           'hook_manage', 'resource_load_status', 'context_compress',
                           'server_health']
          for t in expected_tools:
              assert t in FALLBACK_MAP, f'No fallback for tool {t}'
          print(f'All {len(expected_tools)} tools have fallback functions')
        "
```

### 7.2 规范锁

#### 7.2.1 锁定Skill定义格式

```yaml
# .trae/rules/skill-format-lock.yaml
skill_definition:
  version: "8.0.0"
  max_lines: 150
  max_tokens: 3000
  required_sections:
    - name: "核心约束"
      max_lines: 10
    - name: "MCP Server 依赖"
      max_lines: 30
    - name: "渐进式加载披露"
      max_lines: 40
    - name: "命令路由表"
      max_lines: 35
    - name: "MCP工具调用"
      max_lines: 20
    - name: "MCP Resource访问"
      max_lines: 15
  forbidden_sections:
    - "命令详细步骤"  # 必须在commands/*.md中
    - "Agent角色索引表"  # 必须通过MCP Resource访问
    - "降级模式功能范围"  # 必须引用degradation.py
```

#### 7.2.2 锁定API契约版本

```yaml
# .trae/rules/api-contract-lock.yaml
api_contract:
  version: "2.0.0"
  response_format:
    success:
      required_fields: ["error", "api_version", "data"]
      optional_fields: ["degradation_level", "hook_errors"]
      error_must_be: false
    error:
      required_fields: ["error", "code", "message"]
      optional_fields: ["details"]
      error_must_be: true
  tool_schemas:
    - name: "quality_gate_check"
      response_fields: ["checks", "summary", "cache_info"]
      forbidden_fields: ["gates_checked", "gates_passed", "results"]  # 旧格式
  degradation_level:
    position: "top_level"  # 必须在响应顶层，不在data内
    allowed_values: ["chromadb", "sqlite_fts5", "keyword_fallback", "inline", "partial", "script", null]
```

### 7.3 构建与部署验证流水线

```yaml
# .github/workflows/build-deploy.yml
name: Build & Deploy Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: ["3.10", "3.11", "3.12"]
    steps:
      - uses: actions/checkout@v4
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - name: Install dependencies
        run: |
          pip install -e "xuansto-mcp-server/[full]"
          pip install pytest pytest-asyncio pytest-cov
      - name: Unit tests
        run: pytest tests/unit/ -v --cov=xuansto_mcp --cov-report=xml
      - name: Integration tests
        run: pytest tests/integration/ -v
      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: coverage.xml

  e2e:
    runs-on: ubuntu-latest
    needs: test
    steps:
      - uses: actions/checkout@v4
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install dependencies
        run: pip install -e "xuansto-mcp-server/[full]" pytest pytest-asyncio
      - name: E2E tests
        run: pytest tests/e2e/ -v --timeout=300

  regression:
    runs-on: ubuntu-latest
    needs: test
    steps:
      - uses: actions/checkout@v4
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install dependencies
        run: pip install -e "xuansto-mcp-server/[full]" pytest
      - name: API compatibility
        run: pytest tests/regression/test_api_compatibility.py -v
      - name: Migration test
        run: pytest tests/regression/test_migration.py -v
      - name: Token budget test
        run: pytest tests/regression/test_skill_md_token.py -v

  deploy:
    runs-on: ubuntu-latest
    needs: [test, e2e, regression]
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - name: Build package
        run: |
          cd xuansto-mcp-server
          pip install build
          python -m build
      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        with:
          password: ${{ secrets.PYPI_API_TOKEN }}
          packages-dir: xuansto-mcp-server/dist/
```

### 7.4 检查清单汇总

| 检查项 | 触发条件 | 工具 | 阻断级别 |
|--------|----------|------|----------|
| Python Lint (ruff) | 每次push | ruff check + ruff format --check | 阻断 |
| YAML Lint | 每次push | yamllint | 阻断 |
| Pydantic Schema校验 | 每次push | model_json_schema() | 阻断 |
| MCP工具注册验证 | 每次push | _REGISTERED_TOOL_NAMES检查 | 阻断 |
| 降级链完整性 | 每次push | FALLBACK_MAP检查 | 阻断 |
| SKILL.md行数≤150 | 每次修改SKILL.md | wc -l | 阻断 |
| SKILL.md Token≤3K | 每次修改SKILL.md | 字数/4 | 阻断 |
| API响应格式一致性 | 每次修改tool模块 | JSON Schema校验 | 阻断 |
| 单元测试覆盖率≥80% | 每次push | pytest --cov | 警告 |
| 集成测试通过 | 每次push | pytest tests/integration/ | 阻断 |
| E2E测试通过 | 每次PR到main | pytest tests/e2e/ | 阻断 |
| 回归测试通过 | 每次PR到main | pytest tests/regression/ | 阻断 |

---

## 附录A: 问题编号与来源文档映射

| 编号 | ARCHITECTURE | DATABASE_DESIGN | MCP_REVIEW | SKILL_REVIEW | API_SPECIFICATION |
|------|:-:|:-:|:-:|:-:|:-:|
| A-01 | §7.1 | - | - | §5.2 | - |
| A-02 | §7.1 | §1.3, §5.1 | - | - | - |
| A-03 | - | - | - | §5.2 | - |
| D-01 | §8.4 | §5.1 | - | - | - |
| D-02 | - | §5.1 | - | - | - |
| D-03 | - | §4.1 | - | - | - |
| D-04 | - | §1.3.6 | - | - | - |
| D-05 | §7.1 | - | - | §5.2 | - |
| M-02 | §7.1 | - | - | - | - |
| M-05 | §8.2 | - | - | - | - |
| M-06 | - | - | - | - | §1.1.13 |
| M-07 | - | - | - | §5.2 | - |
| M-08 | - | - | - | §5.2 | - |
| M-09 | - | - | §1.5 | - | §1.1.10 |
| S-06 | - | - | - | §5.2 | - |
| S-07 | - | - | - | §5.2 | - |
| S-08 | - | - | - | §5.2 | - |
| S-09 | - | - | - | §5.2 | - |
| S-10 | - | - | - | §5.2 | - |
| E-02 | - | - | §1.6 | - | §4.1 |
| E-03 | - | - | - | - | §4.2 |
| E-04 | - | - | - | - | §5.3 |
| I-01 | §8.2 | - | - | - | - |
| I-02 | §8.2 | - | - | - | - |

## 附录B: 重构里程碑时间线

```
Week 1-2: 阶段1 — Skill定义瘦身与数据源统一
  ├── Day 1-3:  A-03 命令步骤提取到commands/*.md
  ├── Day 4-5:  A-01 SKILL.md瘦身(删除内嵌步骤+降级表+Agent索引)
  ├── Day 6-7:  A-02 数据镜像消除(符号链接或引用路径)
  └── Day 8-10: M-07 Resource降级路径 + 验收测试

Week 3-5: 阶段2 — MCP Server持久化层重构
  ├── Day 1-3:  D-01/D-02 SQLite Schema设计 + core/persistence.py
  ├── Day 4-8:  5个tool模块迁移到SQLite
  ├── Day 9-10: 启动迁移逻辑 + JSON降级读取
  └── Day 11-15: 并发测试 + 性能测试 + 验收

Week 6-8: 阶段3 — 降级链统一与API规范化
  ├── Day 1-2:  M-02 内嵌逻辑提取到core/inline_fallbacks.py
  ├── Day 3-4:  D-05 降级策略配置化 + M-09 Hook降级补全
  ├── Day 5-7:  E-02 API响应格式统一 + E-03 版本协商
  ├── Day 8:    M-06 server_health Schema
  ├── Day 9:    S-07 门禁别名清理 + S-10 工作流补充
  └── Day 10-15: 集成测试 + 回归测试 + 验收

Week 9-11: 阶段4 — 渐进式加载披露增强
  ├── Day 1-3:  LoadPhase状态机 + DisclosureTransition
  ├── Day 4-5:  Token预算追踪 + 加载错误上报
  ├── Day 6-7:  MCP Notification进度推送
  ├── Day 8:    资源依赖声明 + 缓存命中率
  ├── Day 9-10: S-08 Token实测
  └── Day 11-15: E2E测试 + 性能基准 + 验收

Week 12: CI/CD流水线搭建 + 全量回归 + 文档更新
```

## 附录C: 版本升级影响矩阵

| 组件 | 当前版本 | 目标版本 | 破坏性变更 | 兼容策略 |
|------|---------|---------|-----------|----------|
| SKILL.md | v7.0.0 | v8.0.0 | 删除内嵌命令步骤/Agent索引/降级表 | 渐进式加载按需读取commands/ |
| MCP Server | v3.5.0 | v4.0.0 | API响应格式统一(quality_gate_check等) | API版本协商: v1.0.0→v2.0.0 |
| MCP API | v1.0.0 | v2.0.0 | degradation_level移到顶层; quality_gate_check响应结构变更 | 客户端声明api_version，服务端按版本返回 |
| 持久化 | JSON | SQLite+JSON降级 | 5个JSON文件迁移到SQLite | 启动自动迁移，保留.json.bak |
| 新增Tool | - | decision_log, token_budget, project_init | 3个新Tool | 非破坏性，MINOR版本变更 |
| 新增Resource | 7个 | 11个 | 4个新Resource | 非破坏性，MINOR版本变更 |
