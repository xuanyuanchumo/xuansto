# Xuansto Skill v2 版本对比文档

> **文档版本**: 1.0 | **生成日期**: 2026-05-26
> **对比范围**: v7.0.0 → v8.4.0 → v8.5.0 → v9.0.0
> **变更标注**: 增强(↑) / 削弱(↓) / 废弃(✗) / 新增(+) / 不变(=)

---

## 目录

1. [版本概览](#1-版本概览)
2. [架构形态对比](#2-架构形态对比)
3. [核心功能对比](#3-核心功能对比)
4. [性能对比](#4-性能对比)
5. [渐进式加载方式对比](#5-渐进式加载方式对比)
6. [API契约对比](#6-api契约对比)
7. [数据模型对比](#7-数据模型对比)
8. [已知限制对比](#8-已知限制对比)
9. [版本过渡变更统计](#9-版本过渡变更统计)

---

## 1. 版本概览

| 属性 | v7.0.0 (V_PREVIOUS_MAJOR) | v8.4.0 (V_CURRENT) | v8.5.0 (next minor) | v9.0.0 (next major) |
|------|--------------------------|---------------------|----------------------|----------------------|
| 发布状态 | 已发布 | 当前稳定版 | 规划中 | 规划中 |
| 架构形态 | 纯Skill + 脚本 | MCP Server + Skill 混合 | MCP Server + Skill 混合（增强） | MCP Server + Skill 混合（完整） |
| MCP工具数 | 0 | 20 | 22 | 22+ |
| MCP Resource数 | 0 | 25+ | 28+ | 28+ |
| Agent数量 | 57 | 57 | 57 | 57 |
| 质量门禁 | 13（内嵌） | 54（声明）+13（内嵌降级） | 54（声明+内嵌一致） | 54（声明+内嵌一致） |
| 命令数 | 27 | 31 | 31 | 31 |
| 降级级数 | 0 | 3级 | 3级（对齐） | 3级（对齐） |
| 渐进式加载 | 无 | 4阶段 | 4阶段（完整映射） | 4阶段（完整映射+Token联动） |
| 数据库 | SQLite单实例 | 双SQLite实例 | 统一SQLite实例 | 统一SQLite实例 |
| API版本 | 无 | MCP API v3.0.0 | MCP API v3.1.0 | MCP API v4.0.0 |
| 未修复问题 | — | 22项 | 8项 | 0项 |

---

## 2. 架构形态对比

### 2.1 整体架构

| 对比维度 | v7.0.0 | v8.4.0 | v8.5.0 | v9.0.0 |
|----------|--------|--------|--------|--------|
| 架构模式 | 纯Skill内嵌 (+) | MCP Server + Skill 双层架构 (↑) | MCP Server + Skill 双层架构 (=) | MCP Server + Skill 双层架构 (=) |
| 执行层 | 内嵌脚本/内联逻辑 (=) | Python FastMCP 服务器 (↑) | Python FastMCP 服务器 (=) | Python FastMCP 服务器 (=) |
| 通信协议 | 无外部协议 (=) | MCP stdio + streamable-http (↑) | MCP stdio + streamable-http (=) | MCP stdio + streamable-http (=) |
| 状态管理 | 无状态（纯声明） (=) | 有状态（SQLite + ChromaDB + 内存） (↑) | 有状态（统一SQLite + ChromaDB + 内存） (↑) | 有状态（统一SQLite + ChromaDB + 内存） (=) |
| Skill层职责 | 全部（定义+执行） (=) | 纯声明式（定义What） (↑) | 纯声明式（定义What） (=) | 纯声明式（定义What） (=) |
| MCP层职责 | 无 (=) | 执行式（实现How） (+) | 执行式（实现How） (=) | 执行式（实现How） (=) |
| 降级脚本层 | 无 (=) | scripts/ 独立脚本后备 (+) | scripts/ 独立脚本后备 (=) | scripts/ 独立脚本后备（精简） (↑) |
| 知识库HTTP服务 | 无 (=) | FastAPI独立服务（与MCP重叠） (+) | FastAPI独立服务（与MCP重叠） (=) | 合并到MCP Server内部 (↑) |

### 2.2 分层职责划分

| 层次 | v7.0.0 | v8.4.0 | v8.5.0 | v9.0.0 |
|------|--------|--------|--------|--------|
| Skill层 | 定义+执行+降级（一体式） (=) | 纯声明（Agent/命令/约束/参考文档） (↑) | 纯声明（+降级映射权威源） (↑) | 纯声明（完整权威源） (=) |
| 执行层 | 内嵌在SKILL.md中 (=) | MCP Server 20工具+25+资源 (↑) | MCP Server 22工具+28+资源 (↑) | MCP Server 22+工具+28+资源 (=) |
| 资源层 | 脚本直接执行 (=) | 降级脚本+知识库数据+参考文档 (↑) | 降级脚本+知识库数据+参考文档 (=) | 降级脚本+知识库数据+参考文档（精简） (↑) |
| 数据层 | 无 (=) | 双SQLite（xuansto.db + knowledge.db） (+) | 统一SQLite（xuansto.db） (↑) | 统一SQLite（xuansto.db） (=) |

---

## 3. 核心功能对比

### 3.1 Agent编排

| 对比维度 | v7.0.0 | v8.4.0 | v8.5.0 | v9.0.0 |
|----------|--------|--------|--------|--------|
| Agent数量 | 57 | 57 (=) | 57 (=) | 57 (=) |
| 编排层数 | 13层 | 13层 (=) | 13层 (=) | 13层 (=) |
| Agent加载方式 | 全量加载 (=) | 按Phase渐进加载 (↑) | 按Phase渐进加载 (=) | 按Phase渐进加载 (=) |
| Agent持久化 | 无 (=) | agent_states表+load_on_startup (+) | 验证恢复完整性 (↑) | 完全持久化+跨会话连续 (↑) |
| Agent管理工具 | 无 (=) | agent_status + agent_manage (+) | agent_status + agent_manage (=) | agent_status + agent_manage (=) |
| Agent注册表 | registry.yaml静态声明 (=) | registry.yaml + MCP Resource (+) | registry.yaml + MCP Resource (=) | registry.yaml + MCP Resource (=) |

### 3.2 工作流

| 对比维度 | v7.0.0 | v8.4.0 | v8.5.0 | v9.0.0 |
|----------|--------|--------|--------|--------|
| 工作流阶段 | 9阶段（0-8） | 9阶段全生命周期 (=) | 9阶段全生命周期 (=) | 9阶段全生命周期 (=) |
| 工作流调度 | 无独立调度 (=) | workflow_dispatch工具 (+) | workflow_dispatch工具 (=) | workflow_dispatch工具 (=) |
| 工作流持久化 | 无 (=) | workflow_states表+load_on_startup (+) | 验证Phase推进恢复 (↑) | 完全持久化+重启自动恢复 (↑) |
| 循环模式 | 无 (=) | /loop命令+max_iterations=50 (+) | /loop命令+max_iterations=50 (=) | /loop命令+max_iterations=50 (=) |
| 停滞检测 | 无 (=) | stagnation_threshold=3 (+) | stagnation_threshold=3 (=) | stagnation_threshold=3 (=) |

### 3.3 质量门禁

| 对比维度 | v7.0.0 | v8.4.0 | v8.5.0 | v9.0.0 |
|----------|--------|--------|--------|--------|
| 门禁总数 | 13（内嵌） | 54（声明）+13（内嵌降级） (↑) | 54（声明+内嵌一致） (↑) | 54（声明+内嵌一致） (=) |
| 门禁级别 | 单级 | BLOCK/WARN两级 (↑) | BLOCK/WARN两级 (=) | BLOCK/WARN两级 (=) |
| 门禁工具 | 无 (=) | quality_gate_check (+) | quality_gate_check (=) | quality_gate_check (=) |
| 降级门禁 | 无 (=) | _QUALITY_GATES内嵌13项（与54项不一致） (↓) | 补全至54项内嵌 (↑) | 54项内嵌 (=) |
| 规格偏差检测 | 无 (=) | spec_drift_detect工具 (+) | spec_drift_detect工具 (=) | spec_drift_detect工具 (=) |

### 3.4 知识检索

| 对比维度 | v7.0.0 | v8.4.0 | v8.5.0 | v9.0.0 |
|----------|--------|--------|--------|--------|
| 检索方式 | ChromaDB/SQLite/关键词（简单） (=) | 可插拔搜索引擎架构（4后端） (↑) | 可插拔搜索引擎架构（4后端） (=) | 可插拔搜索引擎架构（4后端） (=) |
| 搜索后端 | ChromaDB + SQLite + 关键词 | ChromaDB/SQLiteFTS5/Simple/Hybrid (↑) | ChromaDB/SQLiteFTS5/Simple/Hybrid (=) | ChromaDB/SQLiteFTS5/Simple/Hybrid (=) |
| 混合检索 | 无 (=) | Hybrid（ChromaDB 0.6 + BM25 0.4） (+) | Hybrid（ChromaDB 0.6 + BM25 0.4） (=) | Hybrid（ChromaDB 0.6 + BM25 0.4） (=) |
| 自动降级 | 无 (=) | Hybrid→SQLiteFTS→Simple三级 (+) | Hybrid→SQLiteFTS→Simple三级 (=) | Hybrid→SQLiteFTS→Simple三级 (=) |
| 知识注入 | 无 (=) | knowledge_inject工具 (+) | knowledge_inject工具 (=) | knowledge_inject工具 (=) |
| 双写一致性 | 无 (=) | 先写SQLite(pending)→再写ChromaDB(+对账) (+) | 自动重试3次+failed可追踪 (↑) | 事务保证+自动对账 (↑) |

### 3.5 降级容错

| 对比维度 | v7.0.0 | v8.4.0 | v8.5.0 | v9.0.0 |
|----------|--------|--------|--------|--------|
| 降级级数 | 0（无统一降级） (=) | 3级（MCP→脚本→内联→错误） (+) | 3级（MCP→脚本→内联→错误） (=) | 3级（MCP→脚本→内联→错误） (=) |
| 降级函数 | 无 (=) | FALLBACK_MAP 20个 (+) | FALLBACK_MAP 20个 (=) | FALLBACK_MAP 20个 (=) |
| 降级声明 | 无 (=) | constraints.yaml 14个映射（与20不一致） (↓) | constraints.yaml 20个映射（对齐） (↑) | constraints.yaml 20个映射（单一权威源） (↑) |
| 降级管理器 | 无 (=) | DegradationManager+DegradationExecutor (+) | DegradationManager+DegradationExecutor (=) | DegradationManager+DegradationExecutor (=) |
| 健康监控 | 无 (=) | 4组件健康监控+自动恢复 (+) | 4组件健康监控+自动恢复 (=) | 4组件健康监控+自动恢复 (=) |
| 恢复退避 | 无 (=) | 指数退避5s~300s+抖动 (+) | 指数退避5s~300s+抖动 (=) | 指数退避5s~300s+抖动 (=) |
| 降级脚本 | 无 (=) | ~30个Python脚本 (+) | ~30个Python脚本 (=) | 精简脚本集 (↑) |

### 3.6 安全与审计

| 对比维度 | v7.0.0 | v8.4.0 | v8.5.0 | v9.0.0 |
|----------|--------|--------|--------|--------|
| 安全扫描 | 无 (=) | security_scan（OWASP+依赖扫描） (+) | security_scan（OWASP+依赖扫描） (=) | security_scan（OWASP+依赖扫描） (=) |
| 审计日志 | 无 (=) | AuditLogger（JSONL持久化+线程安全） (+) | AuditLogger+查询Tool接口 (↑) | AuditLogger+查询Tool接口 (=) |
| 审计查询 | 无 (=) | 仅Resource暴露最近50条 (↓) | audit_query Tool（按条件查询） (↑) | audit_query Tool（按条件查询） (=) |
| 速率限制 | 无 (=) | rate_limiter (+) | rate_limiter (=) | rate_limiter (=) |
| 路径验证 | 无 (=) | validator路径安全验证 (+) | validator路径安全验证 (=) | validator路径安全验证 (=) |

### 3.7 Hook系统

| 对比维度 | v7.0.0 | v8.4.0 | v8.5.0 | v9.0.0 |
|----------|--------|--------|--------|--------|
| Hook类型 | 无 (=) | 8种Hook类型 (+) | 8种Hook类型 (=) | 8种Hook类型 (=) |
| Hook配置 | 静态配置 (=) | minimal/standard/strict三级 (↑) | minimal/standard/strict三级 (=) | minimal/standard/strict三级 (=) |
| Hook数量 | 0 | 14个Hook事件处理器 (+) | 14个Hook事件处理器 (=) | 14个Hook事件处理器 (=) |
| 超时保护 | 无 (=) | DEFAULT_HOOK_TIMEOUT_SECONDS=30.0 (+) | 验证超时保护完整性 (↑) | 完整超时保护+优雅降级 (↑) |
| 动态注册 | 无 (=) | 动态注册/注销+配置文件加载 (+) | 动态注册/注销+配置文件加载 (=) | 动态注册/注销+配置文件加载 (=) |

---

## 4. 性能对比

### 4.1 Token消耗

| 对比维度 | v7.0.0 | v8.4.0 | v8.5.0 | v9.0.0 |
|----------|--------|--------|--------|--------|
| 初始Token消耗 | 全量加载（无预算控制） (=) | Phase 0 ≤2K Token (↑) | Phase 0 ≤2K Token (=) | Phase 0 ≤2K Token (=) |
| 功能阶段Token | 全量加载 (=) | Phase 1 ≤5K Token (↑) | Phase 1 ≤5K Token (=) | Phase 1 ≤5K Token (=) |
| 增强阶段Token | 全量加载 (=) | Phase 2 ≤10K Token (↑) | Phase 2 ≤10K Token (=) | Phase 2 ≤10K Token (=) |
| 完整阶段Token | 全量加载（≈50K+） (=) | Phase 3 ≤20K Token (↑) | Phase 3 ≤20K Token (=) | Phase 3 ≤20K Token (=) |
| Token预算管理 | 无 (=) | token_budget工具 (+) | token_budget+阶段关联 (↑) | token_budget+阶段自动调整 (↑) |
| Token超限降级 | 无 (=) | 降级到低阶段 (+) | 降级到低阶段 (=) | 降级到低阶段+自动恢复 (↑) |

### 4.2 响应时间

| 对比维度 | v7.0.0 | v8.4.0 | v8.5.0 | v9.0.0 |
|----------|--------|--------|--------|--------|
| Phase 0加载 | — | ≤500ms (+) | ≤500ms (=) | ≤500ms (=) |
| Phase 0→1推进 | — | ≤2s (+) | ≤2s (=) | ≤2s (=) |
| Phase 1→2推进 | — | ≤3s (+) | ≤3s (=) | ≤3s (=) |
| Phase 2→3推进 | — | ≤5s (+) | ≤5s (=) | ≤5s (=) |
| 降级恢复延迟 | — | ≤30s (+) | ≤30s (=) | ≤30s (=) |
| 阶段转换通知 | — | 无 (↓) | ≤1s (↑) | ≤1s (=) |
| Hook超时 | 无限制 (=) | 30s超时保护 (↑) | 30s超时保护 (=) | 30s超时保护+优雅降级 (↑) |

### 4.3 并发与可靠性

| 对比维度 | v7.0.0 | v8.4.0 | v8.5.0 | v9.0.0 |
|----------|--------|--------|--------|--------|
| SQLite并发 | 单线程 (=) | WAL模式+busy_timeout=5000+_db_lock (↑) | WAL模式+busy_timeout=5000+_db_lock (=) | WAL模式+busy_timeout=5000+_db_lock (=) |
| 配置热更新 | 需重启 (=) | watchfiles/SIGHUP/轮询三种机制 (↑) | 验证热更新完整性 (↑) | 配置变更实时生效 (=) |
| 双写一致性 | 无 (=) | 最终一致性+对账 (↑) | 自动重试+failed可追踪 (↑) | 事务保证+自动对账 (↑) |
| 知识版本清理 | 无 (=) | cleanup_knowledge_versions(keep_last_n=10) (+) | cleanup_knowledge_versions(keep_last_n=10) (=) | cleanup_knowledge_versions(keep_last_n=10) (=) |

---

## 5. 渐进式加载方式对比

### 5.1 加载策略

| 对比维度 | v7.0.0 | v8.4.0 | v8.5.0 | v9.0.0 |
|----------|--------|--------|--------|--------|
| 加载模式 | 全量加载（无阶段） (=) | 4阶段渐进式加载 (↑) | 4阶段渐进式加载 (=) | 4阶段渐进式加载 (=) |
| 阶段定义 | 无 (=) | SKELETON→FUNCTIONAL→ENHANCED→FULL (+) | SKELETON→FUNCTIONAL→ENHANCED→FULL (=) | SKELETON→FUNCTIONAL→ENHANCED→FULL (=) |
| SKILL.md分段 | 无 (=) | PHASE_0~3标记（4段） (+) | PHASE_0~3标记（4段） (=) | PHASE_0~3标记（4段） (=) |
| 加载工具 | 无 (=) | resource_load_status（status+preload） (+) | resource_load_status（status+preload+transition_check） (↑) | resource_load_status（status+preload+transition_check） (=) |
| 命令驱动推进 | 无 (=) | 仅6个命令有映射 (↓) | 全部31个命令有映射 (↑) | 全部31个命令有映射 (=) |
| 自动降级 | 无 (=) | degrade_phase()已实现 (+) | degrade_phase()+Token超限触发 (↑) | degrade_phase()+Token超限+自动恢复 (↑) |
| 披露机制 | 无 (=) | disclosure_note+upgrade_hint (+) | disclosure_note+upgrade_hint+过渡提示 (↑) | disclosure_note+upgrade_hint+过渡提示 (=) |
| 阶段变更通知 | 无 (=) | 无 (↓) | MCP通知推送 (↑) | MCP通知推送 (=) |

### 5.2 各阶段可用功能

| 功能 | v7.0.0 | v8.4.0 Phase 0 | v8.4.0 Phase 1 | v8.4.0 Phase 2 | v8.4.0 Phase 3 | v8.5.0+ Phase 0 |
|------|--------|----------------|----------------|----------------|----------------|-----------------|
| 命令路由 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 命令执行 | ✅ | ❌ | ✅ | ✅ | ✅ | ✅（/status, /help, /budget） |
| 质量门禁 | ✅ | ❌ | ✅ | ✅ | ✅ | ✅（基础3项） |
| 知识检索 | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ |
| 参考文档 | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ |
| Agent详情 | ✅（全量） | ❌ | 核心13个 | 全部57个 | ✅ | 核心3个 |
| Hook系统 | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| 模型路由 | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |

### 5.3 COMMAND_PHASE_MAP覆盖

| 对比维度 | v7.0.0 | v8.4.0 | v8.5.0 | v9.0.0 |
|----------|--------|--------|--------|--------|
| 有映射的命令数 | — | 6个（/init, /sprint, /implement, /audit, /refactor, /loop） (↓) | 31个（全覆盖） (↑) | 31个（全覆盖） (=) |
| 无映射的命令数 | — | 25个 (↓) | 0 (↑) | 0 (=) |
| 查询类命令 | — | 不触发推进 (=) | 不触发推进（/status, /agent-status, /budget, /decision） (=) | 不触发推进 (=) |
| 设计类命令 | — | 无映射 (↓) | 推进到ENHANCED（/plan, /spec, /design, /design-system, /brainstorm, /clarify） (↑) | 推进到ENHANCED (=) |
| 构建类命令 | — | 无映射 (↓) | 推进到FULL（/build, /build-desktop, /release-desktop） (↑) | 推进到FULL (=) |

---

## 6. API契约对比

### 6.1 API版本与协商

| 对比维度 | v7.0.0 | v8.4.0 | v8.5.0 | v9.0.0 |
|----------|--------|--------|--------|--------|
| MCP API版本 | 无 (=) | 3.0.0 (+) | 3.1.0 (↑) | 4.0.0 (↑) |
| 最低兼容版本 | 无 (=) | 2.0.0 (+) | 2.0.0 (=) | 3.0.0 (↑) |
| Skill最低版本 | 无 (=) | 8.0.0 (+) | 8.0.0 (=) | 8.5.0 (↑) |
| 版本协商 | 无 (=) | 声明已有，协商逻辑不完整 (↓) | 完整协商逻辑+优雅降级 (↑) | 客户端自动适配 (↑) |
| KB HTTP API版本 | 无 (=) | 2.0.0（与MCP不一致） (↓) | 2.0.0（与MCP不一致） (=) | 统一为4.0.0 (↑) |

### 6.2 响应格式

| 对比维度 | v7.0.0 | v8.4.0 | v8.5.0 | v9.0.0 |
|----------|--------|--------|--------|--------|
| MCP响应格式 | 脚本输出（非标准） (=) | make_response统一格式（大部分） (↑) | 全部Tool返回{status, data, metadata} (↑) | 全部Tool返回{status, data, metadata} (=) |
| HTTP API响应格式 | 无 (=) | {status:"ok", ...}（与MCP不一致） (↓) | 与MCP格式对齐{status, data, error, metadata} (↑) | 与MCP格式统一 (=) |
| 错误码体系 | 无 (=) | MCP:ERR_*与HTTP:BAD_REQUEST不统一 (↓) | 合并错误码枚举+映射明确 (↑) | 统一错误码体系 (=) |
| 降级响应格式 | 无 (=) | degraded=True标记（部分不一致） (↓) | 降级响应格式与MCP统一 (↑) | 降级响应格式与MCP统一 (=) |

### 6.3 接口统一

| 对比维度 | v7.0.0 | v8.4.0 | v8.5.0 | v9.0.0 |
|----------|--------|--------|--------|--------|
| MCP Tool接口 | 无 (=) | 20个Tool (+) | 22个Tool（+audit_query+resource_subscribe） (↑) | 22+个Tool (=) |
| MCP Resource接口 | 无 (=) | 25+个Resource（xuansto://协议） (+) | 28+个Resource (↑) | 28+个Resource (=) |
| HTTP API接口 | 无 (=) | FastAPI独立服务（与MCP重叠） (↓) | FastAPI独立服务（响应格式对齐） (↑) | 合并到MCP Server内部 (↑) |
| Resource订阅 | 无 (=) | 内部实现，未暴露为Tool (↓) | resource_subscribe Tool暴露 (↑) | resource_subscribe Tool暴露 (=) |
| spec-locks校验 | 无 (=) | 3个JSON Schema锁文件存在但CI未校验 (↓) | CI步骤强制校验 (↑) | CI步骤强制校验 (=) |

---

## 7. 数据模型对比

### 7.1 数据库架构

| 对比维度 | v7.0.0 | v8.4.0 | v8.5.0 | v9.0.0 |
|----------|--------|--------|--------|--------|
| 数据库实例 | SQLite单实例 | 双SQLite实例（xuansto.db + knowledge.db） (↓) | 统一SQLite实例（xuansto.db） (↑) | 统一SQLite实例（xuansto.db） (=) |
| xuansto.db表数 | — | 14张表 (+) | 22+张表（合并后） (↑) | 22+张表 (=) |
| knowledge.db表数 | — | 9张表 (+) | 废弃（合并到xuansto.db） (✗) | 废弃 (=) |
| knowledge_entries | — | 两个实例重复定义 (↓) | 统一Schema，FTS5触发器正确 (↑) | 统一Schema (=) |
| FTS5全文索引 | — | xuansto.db有FTS5 (+) | 统一FTS5索引 (↑) | 统一FTS5索引 (=) |
| ChromaDB向量库 | 可选 | 可选（Hybrid搜索） (=) | 可选（Hybrid搜索） (=) | 可选（Hybrid搜索） (=) |

### 7.2 数据一致性

| 对比维度 | v7.0.0 | v8.4.0 | v8.5.0 | v9.0.0 |
|----------|--------|--------|--------|--------|
| 决策记录持久化 | 无 (=) | decision_records仅存于MCP Server数据库 (+) | SQLite持久化+文件系统备份可选 (↑) | SQLite持久化+文件系统备份 (=) |
| 决策双写一致性 | 无 (=) | SQLite+文件系统双写，文件失败回滚SQLite (+) | 验证双写完整性 (↑) | 完全双写保证 (=) |
| ChromaDB/SQLite双写 | 无 (=) | 先写SQLite(pending)→再写ChromaDB→成功标记ready (+) | 自动重试3次+failed可追踪 (↑) | 事务保证+自动对账 (↑) |
| 对账机制 | 无 (=) | reconcile_knowledge_stores+reconciliation_log (+) | reconcile_knowledge_stores+reconciliation_log (=) | reconcile_knowledge_stores+reconciliation_log (=) |
| 过期清理 | 无 (=) | cleanup_stale_pending_entries(24h) (+) | cleanup_stale_pending_entries(24h) (=) | cleanup_stale_pending_entries(24h) (=) |
| 知识版本清理 | 无 (=) | cleanup_knowledge_versions(keep_last_n=10) (+) | cleanup_knowledge_versions(keep_last_n=10) (=) | cleanup_knowledge_versions(keep_last_n=10) (=) |

### 7.3 数据迁移

| 对比维度 | v7.0.0 | v8.4.0 | v8.5.0 | v9.0.0 |
|----------|--------|--------|--------|--------|
| 迁移机制 | 无 (=) | 无统一迁移 (=) | migration_v13.py统一Schema迁移 (+) | 迁移完成，保留迁移脚本 (=) |
| 旧表处理 | — | — | 保留为_legacy前缀 (↑) | _legacy表可选清理 (↑) |
| 迁移验证 | — | — | 条目数一致性+FTS5搜索验证 (↑) | 全量验证通过 (=) |
| 回滚能力 | — | — | Schema回滚+数据回滚 (↑) | 迁移脚本保留 (=) |

---

## 8. 已知限制对比

### 8.1 问题清单

| 问题编号 | 描述 | v7.0.0 | v8.4.0 | v8.5.0 | v9.0.0 |
|----------|------|--------|--------|--------|--------|
| NEW-11 | PROBLEM.md状态与代码不同步 | — | 存在（6个误标） (↓) | 修复 (↑) | 不适用 (=) |
| NEW-07 | 双SQLite实例 | — | 存在（knowledge_entries重复定义） (↓) | 合并为单实例 (↑) | 不适用 (=) |
| DB-02 | ChromaDB/SQLite双写无事务保证 | — | 存在（最终一致性） (↓) | 自动重试+failed追踪 (↑) | 事务保证 (↑) |
| DB-01 | 决策记录双写一致性风险 | — | 存在 (↓) | 验证+修复 (↑) | 不适用 (=) |
| NEW-01 | 降级映射数量不一致(20 vs 14) | — | 存在 (↓) | 对齐为20 (↑) | 不适用 (=) |
| ARCH-11 | 错误处理不统一 | — | 大部分统一，边缘情况 (↓) | 全部统一 (↑) | 不适用 (=) |
| API-01 | HTTP API与MCP两套接口无统一Schema | — | 存在（status:success vs ok） (↓) | Schema对齐 (↑) | 合并为单一接口 (↑) |
| ARCH-05/MCP-02 | Resource变更通知不可达 | — | Resource已注册但Host未订阅 (↓) | 暴露订阅Tool (↑) | 不适用 (=) |
| NEW-08 | Resource订阅管理未暴露为Tool | — | 存在 (↓) | resource_subscribe Tool (↑) | 不适用 (=) |
| MCP-03/NEW-09 | 审计日志缺少Tool查询接口 | — | 仅Resource暴露 (↓) | audit_query Tool (↑) | 不适用 (=) |
| NEW-05 | COMMAND_PHASE_MAP仅覆盖6个命令 | — | 存在 (↓) | 覆盖全部31个命令 (↑) | 不适用 (=) |
| NEW-06 | 内嵌门禁13项vs声明54项 | — | 存在 (↓) | 补全至54项 (↑) | 不适用 (=) |
| NEW-02 | 知识库HTTP服务与MCP Server功能重叠 | — | 存在 (↓) | 存在（响应格式对齐） (=) | 合并到MCP Server (↑) |
| SKILL-02 | SKELETON阶段无可用命令 | — | 存在 (↓) | /status, /help, /budget可用 (↑) | 不适用 (=) |
| ARCH-08 | Token预算与加载阶段未关联 | — | 存在 (↓) | 关联逻辑实现 (↑) | 自动调整 (↑) |
| ARCH-12 | API版本协商机制不完整 | — | 声明已有，逻辑不完整 (↓) | 声明已有，逻辑不完整 (=) | 完整协商逻辑 (↑) |
| NEW-03 | spec-locks未在CI中强制校验 | — | 存在 (↓) | CI步骤强制校验 (↑) | 不适用 (=) |
| NEW-04 | 部分工具缺少专项测试 | — | 存在 (↓) | 存在 (=) | 测试覆盖完整 (↑) |
| NEW-10 | MCP与KB版本号不一致 | — | 存在（3.0.0 vs 2.0.0） (↓) | 存在 (=) | 统一版本号 (↑) |
| P3-01 | v1与v2存在重复文件 | — | 存在 (↓) | 存在 (=) | v1归档 (↑) |
| ARCH-06 | Agent持久化（待验证） | — | 代码已实现，需验证 (⚠️) | 验证完成 (↑) | 不适用 (=) |
| ARCH-07 | 工作流持久化（待验证） | — | 代码已实现，需验证 (⚠️) | 验证完成 (↑) | 不适用 (=) |
| ARCH-09 | Hook超时保护（待验证） | — | 代码已实现，需验证 (⚠️) | 验证完成 (↑) | 不适用 (=) |
| ARCH-10 | 配置热更新（待验证） | — | 代码已实现，需验证 (⚠️) | 验证完成 (↑) | 不适用 (=) |
| DB-03 | 版本历史清理（待验证） | — | 代码已实现，需验证 (⚠️) | 验证完成 (↑) | 不适用 (=) |
| MCP-03 | 审计日志（待验证） | — | 代码已实现，需验证 (⚠️) | 验证完成 (↑) | 不适用 (=) |

### 8.2 问题统计

| 版本 | 总问题数 | 紧急 | 高 | 中 | 低 | 待验证 |
|------|----------|------|---|---|---|--------|
| v7.0.0 | — | — | — | — | — | — |
| v8.4.0 | 22 | 1 | 5 | 9 | 7 | 7 |
| v8.5.0 | 8 | 0 | 0 | 3 | 5 | 0 |
| v9.0.0 | 0 | 0 | 0 | 0 | 0 | 0 |

---

## 9. 版本过渡变更统计

### 9.1 v7.0.0 → v8.4.0 变更统计

| 变更类型 | 数量 | 占比 | 典型变更 |
|----------|------|------|----------|
| 新增(+) | 28 | 53.8% | MCP Server架构、20工具、25+资源、渐进式加载、3级降级、Hook系统、审计日志 |
| 增强(↑) | 17 | 32.7% | Agent按Phase加载、知识检索升级为4后端、Token预算管理、配置热更新 |
| 削弱(↓) | 5 | 9.6% | 降级映射不一致(20 vs 14)、双SQLite实例、API格式不统一、COMMAND_PHASE_MAP仅6个 |
| 废弃(✗) | 1 | 1.9% | v1纯Skill内嵌执行模式 |
| 不变(=) | 1 | 1.9% | Agent数量57个/13层 |
| **合计** | **52** | **100%** | — |

### 9.2 v8.4.0 → v8.5.0 变更统计

| 变更类型 | 数量 | 占比 | 典型变更 |
|----------|------|------|----------|
| 新增(+) | 3 | 10.7% | audit_query Tool、resource_subscribe Tool、migration_v13.py |
| 增强(↑) | 18 | 64.3% | 双SQLite合并、降级映射对齐、响应格式统一、COMMAND_PHASE_MAP全覆盖、内嵌门禁补全、Token-Phase关联 |
| 削弱(↓) | 0 | 0% | — |
| 废弃(✗) | 1 | 3.6% | knowledge.db独立实例 |
| 不变(=) | 6 | 21.4% | Agent数量、工作流阶段、搜索后端、Hook类型、降级级数 |
| **合计** | **28** | **100%** | — |

### 9.3 v8.5.0 → v9.0.0 变更统计

| 变更类型 | 数量 | 占比 | 典型变更 |
|----------|------|------|----------|
| 新增(+) | 0 | 0% | — |
| 增强(↑) | 8 | 47.1% | 知识库HTTP服务合并到MCP、API版本协商完善、v1文件归档、版本号统一、测试覆盖完整 |
| 削弱(↓) | 0 | 0% | — |
| 废弃(✗) | 2 | 11.8% | v1重复文件归档、_legacy表可选清理 |
| 不变(=) | 7 | 41.2% | MCP工具数、Agent数量、渐进式加载阶段、搜索后端、降级级数 |
| **合计** | **17** | **100%** | — |

### 9.4 全版本变更趋势总览

| 变更类型 | v7→v8.4 | v8.4→v8.5 | v8.5→v9.0 | 累计 |
|----------|---------|-----------|-----------|------|
| 新增(+) | 28 | 3 | 0 | 31 |
| 增强(↑) | 17 | 18 | 8 | 43 |
| 削弱(↓) | 5 | 0 | 0 | 5 |
| 废弃(✗) | 1 | 1 | 2 | 4 |
| 不变(=) | 1 | 6 | 7 | 14 |
| **合计** | **52** | **28** | **17** | **97** |

### 9.5 版本成熟度评估

| 维度 | v7.0.0 | v8.4.0 | v8.5.0 | v9.0.0 |
|------|--------|--------|--------|--------|
| 架构完整性 | ★★☆☆☆ | ★★★★☆ | ★★★★☆ | ★★★★★ |
| 数据一致性 | ★☆☆☆☆ | ★★★☆☆ | ★★★★☆ | ★★★★★ |
| API统一性 | ★☆☆☆☆ | ★★☆☆☆ | ★★★★☆ | ★★★★★ |
| 降级可靠性 | ★☆☆☆☆ | ★★★☆☆ | ★★★★☆ | ★★★★★ |
| 测试覆盖 | ★☆☆☆☆ | ★★★☆☆ | ★★★☆☆ | ★★★★★ |
| 文档准确性 | ★★☆☆☆ | ★★☆☆☆ | ★★★★☆ | ★★★★★ |
| **综合评分** | **★☆☆☆☆** | **★★★☆☆** | **★★★★☆** | **★★★★★** |

---

> **文档说明**：本对比文档基于 ARCHITECTURE.md、REFACTOR_PLAN.md、MIGRATION.md、CHANGELOG.md 四份源文档综合生成。v8.5.0 和 v9.0.0 的数据基于当前重构规划，实际实现可能存在调整。
