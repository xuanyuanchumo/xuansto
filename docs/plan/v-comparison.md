# Xuansto Skill v2 版本对比文档

> **文档版本**: 2.0 | **生成日期**: 2026-05-26
> **对比范围**: v7.0.0 → v8.5.0 → v8.6.0 → v9.0.0
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

| 属性 | v7.0.0 (V_PREVIOUS_MAJOR) | v8.5.0 (V_CURRENT) | v8.6.0 (next minor) | v9.0.0 (next major) |
|------|--------------------------|---------------------|----------------------|----------------------|
| 发布状态 | 已发布 | 当前稳定版 | 规划中 | 规划中 |
| 架构形态 | 纯Skill + 脚本 | MCP Server + Skill 混合 | MCP Server + Skill 混合（增强） | MCP Server + Skill 混合（完整） |
| MCP工具数 | 0 | 22 | 22 | 22+ |
| MCP Resource数 | 0 | 27 | 27（URI去重） | 27（URI去重） |
| Agent数量 | 57 | 57 | 57 | 57 |
| 质量门禁 | 13（内嵌） | 54（声明+内嵌一致） | 54（声明+内嵌一致） | 54（声明+内嵌一致） |
| 命令数 | 27 | 32 | 32 | 32 |
| 降级级数 | 0 | 3级（对齐20/20） | 3级（对齐） | 3级（对齐） |
| 渐进式加载 | 无 | 4阶段（完整映射32命令） | 4阶段（完整映射+Token联动） | 4阶段（完整映射+Token联动+自动推进） |
| 数据库 | SQLite单实例 | 统一SQLite实例 | 统一SQLite实例（decisions合并） | 统一SQLite实例 |
| API版本 | 无 | MCP API v3.0.0 ⚠️不一致 | MCP API v3.0.0（统一） | MCP API v4.0.0 |
| 未修复问题 | — | 30项 | 15项 | 0项 |

---

## 2. 架构形态对比

### 2.1 整体架构

| 对比维度 | v7.0.0 | v8.5.0 | v8.6.0 | v9.0.0 |
|----------|--------|--------|--------|--------|
| 架构模式 | 纯Skill内嵌 (+) | MCP Server + Skill 双层架构 (↑) | MCP Server + Skill 双层架构 (=) | MCP Server + Skill 双层架构 (=) |
| 执行层 | 内嵌脚本/内联逻辑 (=) | Python FastMCP 服务器 (↑) | Python FastMCP 服务器 (=) | Python FastMCP 服务器 (=) |
| 通信协议 | 无外部协议 (=) | MCP stdio + streamable-http (↑) | MCP stdio + streamable-http (=) | MCP stdio + streamable-http (=) |
| 状态管理 | 无状态（纯声明） (=) | 有状态（统一SQLite + ChromaDB + 内存） (↑) | 有状态（统一SQLite + ChromaDB + 内存） (=) | 有状态（统一SQLite + ChromaDB + 内存） (=) |
| Skill层职责 | 全部（定义+执行） (=) | 纯声明式（定义What） (↑) | 纯声明式（瘦身） (↑) | 纯声明式（完整权威源） (=) |
| MCP层职责 | 无 (=) | 执行式（实现How） (+) | 执行式（实现How） (=) | 执行式（实现How） (=) |
| 降级脚本层 | 无 (=) | scripts/ 独立脚本后备 (+) | scripts/ 独立脚本后备 (=) | scripts/ 独立脚本后备（精简） (↑) |
| 知识库HTTP服务 | 无 (=) | FastAPI独立服务（与MCP重叠） (+) | FastAPI独立服务（与MCP重叠） (=) | 合并到MCP Server内部 (↑) |

### 2.2 分层职责划分

| 层次 | v7.0.0 | v8.5.0 | v8.6.0 | v9.0.0 |
|------|--------|--------|--------|--------|
| Skill层 | 定义+执行+降级（一体式） (=) | 纯声明+降级映射权威源 (↑) | 纯声明（SKILL.md外置+去重） (↑) | 纯声明（完整权威源） (=) |
| 执行层 | 内嵌在SKILL.md中 (=) | MCP Server 22工具+27资源 (↑) | MCP Server 22工具+27资源 (=) | MCP Server 22+工具+27资源 (=) |
| 资源层 | 脚本直接执行 (=) | 降级脚本+知识库数据+参考文档 (↑) | 降级脚本+知识库数据+参考文档（两级加载） (↑) | 降级脚本+知识库数据+参考文档（精简） (↑) |
| 数据层 | 无 (=) | 统一SQLite（xuansto.db） (↑) | 统一SQLite（xuansto.db含decisions） (↑) | 统一SQLite（xuansto.db） (=) |

---

## 3. 核心功能对比

### 3.1 Agent编排

| 对比维度 | v7.0.0 | v8.5.0 | v8.6.0 | v9.0.0 |
|----------|--------|--------|--------|--------|
| Agent数量 | 57 | 57 (=) | 57 (=) | 57 (=) |
| 编排层数 | 13层 | 13层 (=) | 13层 (=) | 13层 (=) |
| Agent加载方式 | 全量加载 (=) | 按Phase渐进加载 (↑) | 按Phase渐进加载 (=) | 按Phase渐进加载+单Agent按需 (↑) |
| Agent持久化 | 无 (=) | agent_states表+load_on_startup (+) | 完全持久化+SQLite权威源 (↑) | 完全持久化+跨会话连续 (↑) |
| Agent管理工具 | 无 (=) | agent_status + agent_manage (+) | agent_status + agent_manage (=) | agent_status + agent_manage (=) |
| Agent注册表 | registry.yaml静态声明 (=) | registry.yaml + MCP Resource (+) | registry.yaml + MCP Resource (=) | registry.yaml + MCP Resource (=) |

### 3.2 工作流

| 对比维度 | v7.0.0 | v8.5.0 | v8.6.0 | v9.0.0 |
|----------|--------|--------|--------|--------|
| 工作流阶段 | 9阶段（0-8） | 9阶段全生命周期 (=) | 9阶段全生命周期 (=) | 9阶段全生命周期 (=) |
| 工作流调度 | 无独立调度 (=) | workflow_dispatch工具 (+) | workflow_dispatch工具 (=) | workflow_dispatch工具 (=) |
| 工作流持久化 | 无 (=) | workflow_states表+load_on_startup (+) | SQLite权威源+重启自动恢复 (↑) | 完全持久化+重启自动恢复 (=) |
| 循环模式 | 无 (=) | /loop命令+max_iterations=50 (+) | /loop命令+max_iterations=50 (=) | /loop命令+max_iterations=50 (=) |
| 停滞检测 | 无 (=) | stagnation_threshold=3 (+) | stagnation_threshold=3 (=) | stagnation_threshold=3 (=) |

### 3.3 质量门禁

| 对比维度 | v7.0.0 | v8.5.0 | v8.6.0 | v9.0.0 |
|----------|--------|--------|--------|--------|
| 门禁总数 | 13（内嵌） | 54（声明+内嵌一致） (↑) | 54（声明+内嵌一致） (=) | 54（声明+内嵌一致） (=) |
| 门禁级别 | 单级 | BLOCK/WARN两级 (↑) | BLOCK/WARN两级 (=) | BLOCK/WARN两级 (=) |
| 门禁工具 | 无 (=) | quality_gate_check (+) | quality_gate_check (=) | quality_gate_check (=) |
| 降级门禁 | 无 (=) | 54项内嵌与声明一致 (↑) | 54项内嵌 (=) | 54项内嵌 (=) |
| 规格偏差检测 | 无 (=) | spec_drift_detect工具 (+) | spec_drift_detect工具 (=) | spec_drift_detect工具 (=) |

### 3.4 知识检索

| 对比维度 | v7.0.0 | v8.5.0 | v8.6.0 | v9.0.0 |
|----------|--------|--------|--------|--------|
| 检索方式 | ChromaDB/SQLite/关键词（简单） (=) | 可插拔搜索引擎架构（4后端） (↑) | 可插拔搜索引擎架构（4后端） (=) | 可插拔搜索引擎架构（4后端） (=) |
| 搜索后端 | ChromaDB + SQLite + 关键词 | ChromaDB/SQLiteFTS5/Simple/Hybrid (↑) | ChromaDB/SQLiteFTS5/Simple/Hybrid (=) | ChromaDB/SQLiteFTS5/Simple/Hybrid (=) |
| 混合检索 | 无 (=) | Hybrid（ChromaDB 0.6 + BM25 0.4） (+) | Hybrid（ChromaDB 0.6 + BM25 0.4） (=) | Hybrid（ChromaDB 0.6 + BM25 0.4） (=) |
| 自动降级 | 无 (=) | Hybrid→SQLiteFTS→Simple三级 (+) | Hybrid→SQLiteFTS→Simple三级 (=) | Hybrid→SQLiteFTS→Simple三级 (=) |
| 知识注入 | 无 (=) | knowledge_inject工具 (+) | knowledge_inject工具 (=) | knowledge_inject工具 (=) |
| 双写一致性 | 无 (=) | 自动重试3次+failed可追踪 (↑) | 事务保证+自动对账 (↑) | 事务保证+自动对账 (=) |

### 3.5 降级容错

| 对比维度 | v7.0.0 | v8.5.0 | v8.6.0 | v9.0.0 |
|----------|--------|--------|--------|--------|
| 降级级数 | 0（无统一降级） (=) | 3级（MCP→脚本→内联→错误） (+) | 3级（MCP→脚本→内联→错误） (=) | 3级（MCP→脚本→内联→错误） (=) |
| 降级函数 | 无 (=) | FALLBACK_MAP 20个 (+) | FALLBACK_MAP 20个 (=) | FALLBACK_MAP 20个 (=) |
| 降级声明 | 无 (=) | constraints.yaml 20个映射（对齐） (↑) | constraints.yaml 20个映射（单一权威源） (=) | constraints.yaml 20个映射（单一权威源） (=) |
| 降级管理器 | 无 (=) | DegradationManager+DegradationExecutor (+) | DegradationManager+DegradationExecutor (=) | DegradationManager+DegradationExecutor (=) |
| 健康监控 | 无 (=) | 4组件健康监控+自动恢复 (+) | 4组件健康监控+自动恢复 (=) | 4组件健康监控+自动恢复 (=) |
| 恢复退避 | 无 (=) | 指数退避5s~300s+抖动 (+) | 指数退避5s~300s+抖动 (=) | 指数退避5s~300s+抖动 (=) |
| 降级脚本 | 无 (=) | ~30个Python脚本 (+) | ~30个Python脚本 (=) | 精简脚本集 (↑) |

### 3.6 安全与审计

| 对比维度 | v7.0.0 | v8.5.0 | v8.6.0 | v9.0.0 |
|----------|--------|--------|--------|--------|
| 安全扫描 | 无 (=) | security_scan（OWASP+依赖扫描） (+) | security_scan（OWASP+依赖扫描） (=) | security_scan（OWASP+依赖扫描） (=) |
| 审计日志 | 无 (=) | AuditLogger+audit_query Tool (+) | AuditLogger+audit_query Tool (=) | AuditLogger+audit_query Tool（增强查询） (↑) |
| 审计查询 | 无 (=) | audit_query Tool（按条件查询） (+) | audit_query Tool（按条件查询） (=) | audit_query Tool（复杂过滤） (↑) |
| 速率限制 | 无 (=) | rate_limiter (+) | rate_limiter (=) | rate_limiter (=) |
| 路径验证 | 无 (=) | validator路径安全验证 (+) | validator路径安全验证 (=) | validator路径安全验证 (=) |

### 3.7 Hook系统

| 对比维度 | v7.0.0 | v8.5.0 | v8.6.0 | v9.0.0 |
|----------|--------|--------|--------|--------|
| Hook类型 | 无 (=) | 8种Hook类型 (+) | 8种Hook类型 (=) | 8种Hook类型 (=) |
| Hook配置 | 静态配置 (=) | minimal/standard/strict三级 (↑) | minimal/standard/strict三级 (=) | minimal/standard/strict三级（Phase联动） (↑) |
| Hook数量 | 0 | 14个Hook事件处理器 (+) | 14个Hook事件处理器 (=) | 14个Hook事件处理器 (=) |
| 超时保护 | 无 (=) | DEFAULT_HOOK_TIMEOUT_SECONDS=30.0 (+) | 30s超时保护 (=) | 30s超时保护+优雅降级 (↑) |
| 动态注册 | 无 (=) | 动态注册/注销+配置文件加载 (+) | 动态注册/注销+配置文件加载 (=) | 动态注册/注销+配置文件加载 (=) |

---

## 4. 性能对比

### 4.1 Token消耗

| 对比维度 | v7.0.0 | v8.5.0 | v8.6.0 | v9.0.0 |
|----------|--------|--------|--------|--------|
| 初始Token消耗 | 全量加载（无预算控制） (=) | Phase 0 ≤2K Token (↑) | Phase 0 ≤2K Token (=) | Phase 0 ≤2K Token (=) |
| 功能阶段Token | 全量加载 (=) | Phase 1 ≤5K Token (↑) | Phase 1 ≤5K Token (=) | Phase 1 ≤5K Token (=) |
| 增强阶段Token | 全量加载 (=) | Phase 2 ≤10K Token ⚠️含include可能超限 | Phase 2 ≤10K Token（外置后达标） (↑) | Phase 2 ≤10K Token (=) |
| 完整阶段Token | 全量加载（≈50K+） (=) | Phase 3 ≤20K Token ⚠️含完整参考文档可能超限 | Phase 3 ≤20K Token（两级加载后达标） (↑) | Phase 3 ≤20K Token (=) |
| Token预算管理 | 无 (=) | token_budget+阶段关联 (↑) | token_budget+阶段关联 (=) | token_budget+阶段自动调整 (↑) |
| Token超限降级 | 无 (=) | 降级到低阶段 (↑) | 降级到低阶段 (=) | 降级到低阶段+自动恢复 (↑) |

### 4.2 响应时间

| 对比维度 | v7.0.0 | v8.5.0 | v8.6.0 | v9.0.0 |
|----------|--------|--------|--------|--------|
| Phase 0加载 | — | ≤500ms（未实测） (↓) | ≤500ms（实测确认） (↑) | ≤500ms (=) |
| Phase 0→1推进 | — | ≤2s（未实测） (↓) | ≤2s（实测确认） (↑) | ≤2s (=) |
| Phase 1→2推进 | — | ≤3s（未实测） (↓) | ≤3s（实测确认） (↑) | ≤3s (=) |
| Phase 2→3推进 | — | ≤5s（未实测） (↓) | ≤5s（实测确认） (↑) | ≤5s (=) |
| 降级恢复延迟 | — | ≤30s（未实测） (↓) | ≤30s（实测确认） (↑) | ≤30s (=) |
| 阶段转换通知 | — | 无 (↓) | ≤1s (↑) | ≤1s (=) |
| Hook超时 | 无限制 (=) | 30s超时保护 (↑) | 30s超时保护 (=) | 30s超时保护+优雅降级 (↑) |

### 4.3 并发与可靠性

| 对比维度 | v7.0.0 | v8.5.0 | v8.6.0 | v9.0.0 |
|----------|--------|--------|--------|--------|
| SQLite并发 | 单线程 (=) | WAL模式+busy_timeout=5000+_db_lock (↑) | WAL模式+busy_timeout=5000+_db_lock (=) | WAL模式+busy_timeout=5000+_db_lock (=) |
| 配置热更新 | 需重启 (=) | watchfiles/SIGHUP/轮询三种机制 (↑) | watchfiles/SIGHUP/轮询三种机制 (=) | 配置变更实时生效+Windows稳定性增强 (↑) |
| 双写一致性 | 无 (=) | 自动重试+failed可追踪 (↑) | 事务保证+自动对账 (↑) | 事务保证+自动对账 (=) |
| 知识版本清理 | 无 (=) | cleanup_knowledge_versions(keep_last_n=10) (+) | cleanup_knowledge_versions(keep_last_n=10) (=) | cleanup_knowledge_versions(keep_last_n=10) (=) |

---

## 5. 渐进式加载方式对比

### 5.1 加载策略

| 对比维度 | v7.0.0 | v8.5.0 | v8.6.0 | v9.0.0 |
|----------|--------|--------|--------|--------|
| 加载模式 | 全量加载（无阶段） (=) | 4阶段渐进式加载 (↑) | 4阶段渐进式加载 (=) | 4阶段渐进式加载 (=) |
| 阶段定义 | 无 (=) | SKELETON→FUNCTIONAL→ENHANCED→FULL (+) | SKELETON→FUNCTIONAL→ENHANCED→FULL (=) | SKELETON→FUNCTIONAL→ENHANCED→FULL (=) |
| SKILL.md分段 | 无 (=) | PHASE_0~3标记（4段） (+) | PHASE_0~3标记（4段，PHASE_2/3外置） (↑) | PHASE_0~3标记（4段，PHASE_2/3外置） (=) |
| 加载工具 | 无 (=) | resource_load_status（status+preload+transition_check） (+) | resource_load_status（status+preload+transition_check） (=) | resource_load_status（status+preload+transition_check） (=) |
| 命令驱动推进 | 无 (=) | 全部32个命令有映射 (↑) | 全部32个命令有映射 (=) | 全部32个命令有映射 (=) |
| 自动Phase推进 | 无 (=) | 需手动preload (↓) | 需手动preload (=) | 基于Token消耗自动推进 (↑) |
| 参考文档加载 | 全量 (=) | 全量加载 (↓) | 两级加载（摘要→完整） (↑) | 两级加载（摘要→完整） (=) |
| 自动降级 | 无 (=) | degrade_phase()+Token超限触发 (↑) | degrade_phase()+Token超限触发 (=) | degrade_phase()+Token超限+自动恢复 (↑) |
| 披露机制 | 无 (=) | disclosure_note+upgrade_hint+过渡提示 (↑) | disclosure_note+upgrade_hint+过渡提示 (=) | disclosure_note+upgrade_hint+过渡提示 (=) |
| 阶段变更通知 | 无 (=) | resource_subscribe已实现但Host端未消费 (⚠️) | Host端可订阅变更 (↑) | Host端可订阅变更 (=) |

### 5.2 各阶段可用功能

| 功能 | v7.0.0 | v8.5.0 Phase 0 | v8.5.0 Phase 1 | v8.5.0 Phase 2 | v8.5.0 Phase 3 |
|------|--------|----------------|----------------|----------------|----------------|
| 命令路由 | ✅ | ✅ | ✅ | ✅ | ✅ |
| 命令执行 | ✅ | ✅（/status, /help, /budget） | ✅ | ✅ | ✅ |
| 质量门禁 | ✅ | ✅（基础3项） | ✅ | ✅ | ✅ |
| 知识检索 | ✅ | ❌ | ❌ | ✅ | ✅ |
| 参考文档 | ✅ | ❌ | ❌ | ✅（全量） | ✅（全量） |
| Agent详情 | ✅（全量） | 核心3个 | 核心13个 | 全部57个 | ✅ |
| Hook系统 | ❌ | ❌ | ❌ | ❌ | ✅ |
| 模型路由 | ❌ | ❌ | ❌ | ❌ | ✅ |

### 5.3 COMMAND_PHASE_MAP覆盖

| 对比维度 | v7.0.0 | v8.5.0 | v8.6.0 | v9.0.0 |
|----------|--------|--------|--------|--------|
| 有映射的命令数 | — | 32个（全覆盖） (↑) | 32个（全覆盖） (=) | 32个（全覆盖） (=) |
| 无映射的命令数 | — | 0 (=) | 0 (=) | 0 (=) |
| 查询类命令 | — | 不触发推进（/status, /agent-status, /budget, /decision） (=) | 不触发推进 (=) | 不触发推进 (=) |
| 设计类命令 | — | 推进到ENHANCED（/plan, /spec, /design等） (↑) | 推进到ENHANCED (=) | 推进到ENHANCED (=) |
| 构建类命令 | — | 推进到FULL（/build, /build-desktop, /release-desktop） (↑) | 推进到FULL (=) | 推进到FULL (=) |

---

## 6. API契约对比

### 6.1 API版本与协商

| 对比维度 | v7.0.0 | v8.5.0 | v8.6.0 | v9.0.0 |
|----------|--------|--------|--------|--------|
| MCP API版本 | 无 (=) | 3.0.0 ⚠️不一致 (+) | 3.0.0（统一） (↑) | 4.0.0 (↑) |
| Server指令版本 | 无 (=) | 8.4.0 ⚠️与pyproject.toml(8.5.0)不一致 (↓) | 8.5.0（统一） (↑) | 9.0.0 (↑) |
| 最低兼容版本 | 无 (=) | 2.0.0 (+) | 2.0.0 (=) | 3.0.0 (↑) |
| Skill最低版本 | 无 (=) | 8.0.0 (+) | 8.0.0 (=) | 8.5.0 (↑) |
| 版本协商 | 无 (=) | 声明已有，协商逻辑不完整 (↓) | 完整协商逻辑+优雅降级 (↑) | 客户端自动适配 (↑) |
| KB HTTP API版本 | 无 (=) | 2.0.0（与MCP不一致） (↓) | 2.0.0（与MCP不一致） (=) | 统一为4.0.0 (↑) |

### 6.2 响应格式

| 对比维度 | v7.0.0 | v8.5.0 | v8.6.0 | v9.0.0 |
|----------|--------|--------|--------|--------|
| MCP响应格式 | 脚本输出（非标准） (=) | make_response统一格式（大部分） (↑) | 全部Tool返回{status, data, metadata} (↑) | 全部Tool返回{status, data, metadata} (=) |
| HTTP API响应格式 | 无 (=) | {status:"ok", ...}（与MCP不一致） (↓) | 与MCP格式对齐{status, data, error, metadata} (↑) | 与MCP格式统一 (=) |
| 错误码体系 | 无 (=) | MCP:ERR_*与HTTP:BAD_REQUEST不统一 (↓) | 合并错误码枚举+映射明确 (↑) | 统一错误码体系 (=) |
| 降级响应格式 | 无 (=) | degraded=True标记（部分不一致） (↓) | 降级响应格式与MCP统一 (↑) | 降级响应格式与MCP统一 (=) |

### 6.3 接口统一

| 对比维度 | v7.0.0 | v8.5.0 | v8.6.0 | v9.0.0 |
|----------|--------|--------|--------|--------|
| MCP Tool接口 | 无 (=) | 22个Tool (+) | 22个Tool (=) | 22+个Tool (=) |
| MCP Resource接口 | 无 (=) | 27个Resource（含重复URI） (+) | 27个Resource（URI去重） (↑) | 27个Resource（URI去重） (=) |
| HTTP API接口 | 无 (=) | FastAPI独立服务（与MCP重叠） (↓) | FastAPI独立服务（响应格式对齐） (↑) | 合并到MCP Server内部 (↑) |
| Resource订阅 | 无 (=) | resource_subscribe Tool已暴露但Host端未消费 (⚠️) | Host端可订阅变更 (↑) | Host端可订阅变更 (=) |
| spec-locks校验 | 无 (=) | 3个JSON Schema锁文件存在但CI未校验 (↓) | CI步骤强制校验 (↑) | CI步骤强制校验 (=) |

---

## 7. 数据模型对比

### 7.1 数据库架构

| 对比维度 | v7.0.0 | v8.5.0 | v8.6.0 | v9.0.0 |
|----------|--------|--------|--------|--------|
| 数据库实例 | SQLite单实例 | 统一SQLite实例（xuansto.db）+独立decisions.db (↑) | 统一SQLite实例（xuansto.db含decisions） (↑) | 统一SQLite实例（xuansto.db） (=) |
| xuansto.db表数 | — | 22+张表 (+) | 22+张表（+decisions相关表） (↑) | 22+张表 (=) |
| decisions.db | — | 独立1表+FTS5 (↓) | 合并到xuansto.db (↑) | 不适用 (=) |
| workflow双表 | — | workflow_instances + workflow_states重叠 (↓) | 统一为workflow_states (↑) | 统一为workflow_states (=) |
| FTS5全文索引 | — | xuansto.db有FTS5 (+) | 统一FTS5索引（含decisions_fts） (↑) | 统一FTS5索引 (=) |
| ChromaDB向量库 | 可选 | 可选（Hybrid搜索） (=) | 可选（Hybrid搜索） (=) | 可选（Hybrid搜索） (=) |

### 7.2 数据一致性

| 对比维度 | v7.0.0 | v8.5.0 | v8.6.0 | v9.0.0 |
|----------|--------|--------|--------|--------|
| 决策记录持久化 | 无 (=) | decision_records在独立decisions.db (↓) | 合并到xuansto.db+文件系统备份可选 (↑) | SQLite持久化+文件系统备份 (=) |
| 决策双写一致性 | 无 (=) | SQLite+文件系统双写，文件失败回滚SQLite (+) | 验证双写完整性 (↑) | 完全双写保证 (=) |
| ChromaDB/SQLite双写 | 无 (=) | 自动重试3次+failed可追踪 (↑) | 事务保证+自动对账 (↑) | 事务保证+自动对账 (=) |
| 对账机制 | 无 (=) | reconcile_knowledge_stores（手动触发） (↓) | 自动定时对账（默认每小时） (↑) | 自动定时对账 (=) |
| 过期清理 | 无 (=) | cleanup_stale_pending_entries(24h) (+) | cleanup_stale_pending_entries(24h) (=) | cleanup_stale_pending_entries(24h) (=) |
| 知识版本清理 | 无 (=) | cleanup_knowledge_versions(keep_last_n=10) (+) | cleanup_knowledge_versions(keep_last_n=10) (=) | cleanup_knowledge_versions(keep_last_n=10) (=) |

### 7.3 状态存储

| 对比维度 | v7.0.0 | v8.5.0 | v8.6.0 | v9.0.0 |
|----------|--------|--------|--------|--------|
| Agent状态 | 无 (=) | 内存dict+JSON文件+SQLite三源 (↓) | SQLite为唯一权威源，JSON仅备份 (↑) | SQLite为唯一权威源 (=) |
| Workflow状态 | 无 (=) | 内存dict+JSON文件+SQLite三源 (↓) | SQLite为唯一权威源，JSON仅备份 (↑) | SQLite为唯一权威源 (=) |
| Session状态 | 无 (=) | 内存+JSON文件 (↓) | SQLite为唯一权威源 (↑) | SQLite为唯一权威源 (=) |
| JSON状态文件 | 无 (=) | 10+个，无事务保证 (↓) | 可选备份，非权威源 (↑) | 可选备份 (=) |

---

## 8. 已知限制对比

### 8.1 问题清单（基于 REFACTOR_PLAN.md v2.0）

| 问题编号 | 描述 | v7.0.0 | v8.5.0 | v8.6.0 | v9.0.0 |
|----------|------|--------|--------|--------|--------|
| MCP-01 | Server指令版本与pyproject.toml不一致 | — | 存在(8.4.0 vs 8.5.0) (↓) | 修复 (↑) | 不适用 (=) |
| API-01 | API版本号三源不一致 | — | 存在(2.5.0/8.5.0/3.0.0) (↓) | 修复 (↑) | 不适用 (=) |
| ARCH-01 | Skill-MCP通信同步/异步混合 | — | 存在 (↓) | 修复 (↑) | 不适用 (=) |
| ARCH-02 | 渐进式加载缺少自动Phase推进 | — | 存在（需手动preload） (↓) | 存在 (=) | 修复 (↑) |
| ARCH-05 | MCP Resource变更通知不可达 | — | 存在（Host端未消费） (↓) | 修复 (↑) | 不适用 (=) |
| ARCH-03 | Hook系统同步+异步混合 | — | 存在 (↓) | 存在 (=) | 修复 (↑) |
| ARCH-04 | Agent管理缺少自动扩缩容 | — | 存在（20实例硬上限） (↓) | 存在 (=) | 修复 (↑) |
| ARCH-13 | 桌面构建仅Windows PowerShell | — | 存在 (↓) | 存在 (=) | 修复 (↑) |
| ARCH-14 | API版本协商缺版本特定行为分支 | — | 存在 (↓) | 存在 (=) | 修复 (↑) |
| ARCH-15 | watchfiles在Windows下可能不稳定 | — | 存在（已有轮询降级） (⚠️) | 存在 (=) | 修复 (↑) |
| DB-04 | workflow_instances与workflow_states表结构重叠 | — | 存在 (↓) | 合并 (↑) | 不适用 (=) |
| DB-05 | decisions.db仍独立于xuansto.db | — | 存在 (↓) | 合并 (↑) | 不适用 (=) |
| DB-06 | Agent/Workflow状态三源分散 | — | 存在 (↓) | 统一为SQLite权威源 (↑) | 不适用 (=) |
| DB-07 | JSON状态文件无事务保证 | — | 存在 (↓) | JSON仅备份 (↑) | 不适用 (=) |
| DB-08 | 知识库缺少自动定时对账 | — | 存在（手动reconcile） (↓) | 自动对账 (↑) | 不适用 (=) |
| MCP-02 | Resource URI重复 | — | 存在 (↓) | 去重 (↑) | 不适用 (=) |
| MCP-03 | Token预算快照未暴露为Resource | — | 存在 (↓) | 存在 (=) | 修复 (↑) |
| MCP-04 | Agent实例池未暴露为Resource | — | 存在 (↓) | 存在 (=) | 修复 (↑) |
| SKILL-01 | v1与v2存在重复文件 | — | 存在 (↓) | 存在 (=) | v1归档 (↑) |
| SKILL-02 | SKILL.md行数可能超限 | — | 已缓解（PHASE标记） (⚠️) | 已缓解 (=) | 外置后解决 (↑) |
| SKILL-03 | SKILL.md PHASE_2/3内容应外置 | — | 存在 (↓) | 外置 (↑) | 不适用 (=) |
| SKILL-04 | routes.yaml与SKILL.md路由表重复 | — | 存在 (↓) | 去重 (↑) | 不适用 (=) |
| SKILL-05 | registry.yaml与SKILL.md Agent索引重复 | — | 存在 (↓) | 去重 (↑) | 不适用 (=) |
| SKILL-06 | 参考文档全量加载，缺两级加载 | — | 存在 (↓) | 两级加载 (↑) | 不适用 (=) |
| SKILL-07 | commands/*.md参数与MCP工具参数冗余 | — | 存在 (↓) | 去重 (↑) | 不适用 (=) |
| SKILL-08 | hooks.json静态配置无法根据Phase调整 | — | 存在 (↓) | 存在 (=) | 修复 (↑) |
| API-02 | 审计日志查询能力有限 | — | 存在 (↓) | 存在 (=) | 增强 (↑) |
| PERF-01 | 性能指标未实测 | — | 存在 (↓) | 存在 (=) | 实测确认 (↑) |
| PERF-02 | Agent按需加载粒度不足 | — | 存在 (↓) | 存在 (=) | 单Agent按需加载 (↑) |
| PERF-03 | Token自动降级缺乏端到端验证 | — | 存在 (↓) | 存在 (=) | 端到端验证 (↑) |

### 8.2 问题统计

| 版本 | 总问题数 | 紧急 | 高 | 中 | 低 |
|------|----------|------|---|---|---|
| v7.0.0 | — | — | — | — | — |
| v8.5.0 | 30 | 2 | 9 | 16 | 3 |
| v8.6.0 | 15 | 0 | 0 | 10 | 5 |
| v9.0.0 | 0 | 0 | 0 | 0 | 0 |

---

## 9. 版本过渡变更统计

### 9.1 v7.0.0 → v8.5.0 变更统计

| 变更类型 | 数量 | 占比 | 典型变更 |
|----------|------|------|----------|
| 新增(+) | 31 | 56.4% | MCP Server架构、22工具、27资源、渐进式加载、3级降级、Hook系统、审计日志、audit_query、resource_subscribe |
| 增强(↑) | 18 | 32.7% | Agent按Phase加载、知识检索升级为4后端、Token预算管理、配置热更新、双SQLite合并、降级映射对齐、门禁补全 |
| 削弱(↓) | 4 | 7.3% | 版本号不一致(MCP-01/API-01)、decisions.db独立、workflow双表重叠、状态三源分散 |
| 废弃(✗) | 1 | 1.8% | knowledge.db独立实例 |
| 不变(=) | 1 | 1.8% | Agent数量57个/13层 |
| **合计** | **55** | **100%** | — |

### 9.2 v8.5.0 → v8.6.0 变更统计

| 变更类型 | 数量 | 占比 | 典型变更 |
|----------|------|------|----------|
| 新增(+) | 2 | 8.0% | 参考文档摘要目录(references/summary/)、自动对账机制 |
| 增强(↑) | 16 | 64.0% | 版本号统一、异步统一、Resource通知可达、URI去重、workflow双表合并、decisions.db合并、状态存储统一、SKILL.md外置、路由/注册表去重、两级加载、命令参数去重 |
| 削弱(↓) | 0 | 0% | — |
| 废弃(✗) | 2 | 8.0% | decisions.db独立实例、workflow_instances旧表 |
| 不变(=) | 5 | 20.0% | Agent数量、工作流阶段、搜索后端、Hook类型、降级级数 |
| **合计** | **25** | **100%** | — |

### 9.3 v8.6.0 → v9.0.0 变更统计

| 变更类型 | 数量 | 占比 | 典型变更 |
|----------|------|------|----------|
| 新增(+) | 1 | 5.9% | 跨平台构建脚本(build-desktop.sh) |
| 增强(↑) | 10 | 58.8% | 知识库HTTP服务合并到MCP、API版本协商完善、v1文件归档、版本号统一、测试覆盖完整、自动Phase推进、Token降级验证、Agent粒度加载、Hook动态配置、性能基准测试 |
| 削弱(↓) | 0 | 0% | — |
| 废弃(✗) | 2 | 11.8% | v1重复文件归档、_legacy表可选清理 |
| 不变(=) | 4 | 23.5% | MCP工具数、Agent数量、渐进式加载阶段、搜索后端 |
| **合计** | **17** | **100%** | — |

### 9.4 全版本变更趋势总览

| 变更类型 | v7→v8.5 | v8.5→v8.6 | v8.6→v9.0 | 累计 |
|----------|---------|-----------|-----------|------|
| 新增(+) | 31 | 2 | 1 | 34 |
| 增强(↑) | 18 | 16 | 10 | 44 |
| 削弱(↓) | 4 | 0 | 0 | 4 |
| 废弃(✗) | 1 | 2 | 2 | 5 |
| 不变(=) | 1 | 5 | 4 | 10 |
| **合计** | **55** | **25** | **17** | **97** |

### 9.5 版本成熟度评估

| 维度 | v7.0.0 | v8.5.0 | v8.6.0 | v9.0.0 |
|------|--------|--------|--------|--------|
| 架构完整性 | ★★☆☆☆ | ★★★★☆ | ★★★★☆ | ★★★★★ |
| 数据一致性 | ★☆☆☆☆ | ★★★☆☆ | ★★★★☆ | ★★★★★ |
| API统一性 | ★☆☆☆☆ | ★★☆☆☆ | ★★★★☆ | ★★★★★ |
| 降级可靠性 | ★☆☆☆☆ | ★★★★☆ | ★★★★☆ | ★★★★★ |
| 测试覆盖 | ★☆☆☆☆ | ★★★☆☆ | ★★★☆☆ | ★★★★★ |
| 文档准确性 | ★★☆☆☆ | ★★★☆☆ | ★★★★☆ | ★★★★★ |
| 性能验证 | ★☆☆☆☆ | ★★☆☆☆ | ★★★☆☆ | ★★★★★ |
| **综合评分** | **★☆☆☆☆** | **★★★☆☆** | **★★★★☆** | **★★★★★** |

---

> **文档说明**：本对比文档基于 REFACTOR_PLAN.md v2.0、ARCHITECTURE.md、DATABASE_DESIGN.md、MCP_REVIEW.md、SKILL_REVIEW.md、API_SPECIFICATION.md 综合生成。v8.6.0 和 v9.0.0 的数据基于当前重构规划，实际实现可能存在调整。
