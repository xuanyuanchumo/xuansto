# Changelog

All notable changes to xuansto-skill-v2 will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [8.5.1] - 2026-05-26

### Added

#### Phase变更通知
- ARCH-05: degrade_phase和preload操作成功后发送subscriber通知

### Changed

#### 版本与接口统一
- MCP-01: 统一版本号——server.py指令版本和__init__.__version__从8.4.0更新为8.5.0
- ARCH-01: Skill-MCP异步统一——run_script改为async，subprocess.run用asyncio.to_thread包装
- ARCH-01: 降级脚本异步化——degradation.py全部20个fallback函数改为async def，使用asyncio.create_subprocess_exec
- MCP-02: Resource URI去重——移除5个重复URI（27→22），保留规范URI模式

### Fixed
- MCP-01: Server指令版本与pyproject.toml不一致
- API-01: API版本号三源不一致
- ARCH-01: Skill-MCP通信同步/异步混合
- ARCH-05: MCP Resource变更通知不可达
- MCP-02: Resource URI重复

## [8.5.0] - 2026-05-26

### Added

#### 数据层：双SQLite合并
- NEW-07: 双SQLite数据库合并为统一 xuansto.db（22+表合并，消除 knowledge.db 与 workflow.db 分裂）
- migration_v13 迁移脚本：合并表结构、数据迁移、索引重建
- FTS5 全文搜索触发器：decision_fts、knowledge_fts 自动同步全文索引
- db_engine.py 统一数据库引擎：单连接池管理、事务一致性保证、统一 xuansto.db 路径

#### 双写增强
- DB-02: ChromaDB 双写重试机制（3次指数退避重试，1s/2s/4s间隔）
- sync_status='failed' 状态追踪：ChromaDB写入失败时标记，reconcile可修复
- reconcile 增强对账：自动检测 failed 条目并重试同步，reconciliation_log 审计追踪

#### 决策日志增强
- DB-01: SQLite 主存储策略（决策记录以 SQLite 为权威源，文件备份可选）
- decision_log 新增 configure action：可配置文件备份开关（file_backup: true/false）
- _reconcile_decisions 增强：SQLite→文件单向同步，文件写入失败不影响主存储

#### 降级映射完善
- NEW-01: 降级映射补全 6 个缺失项（14→20，20/20 完整覆盖所有MCP工具）
- constraints.yaml 作为降级映射权威源（tool_fallbacks 结构化配置）
- degradation.py 从 constraints.yaml 动态加载映射，YAML读取失败回退硬编码

#### 统一响应格式
- 响应格式统一为 {status, data, error, metadata} 结构
- MCP 工具和 HTTP API 共享统一响应 Schema
- metadata 包含 request_id、timestamp、version 等标准字段

#### 统一错误码
- UNIFIED_ERROR_CODE_MAPPING：MCP↔HTTP 错误码双向映射
- 错误码分类：CLIENT_ERROR(4xx)、SERVER_ERROR(5xx)、MCP_SPECIFIC(6xxx)
- errors.py 新增 error_code_to_http_status() 和 http_status_to_error_code() 映射函数

#### 新增MCP工具
- NEW-08: resource_subscribe 工具（subscribe/unsubscribe/list 三种操作）
  - subscribe：订阅 Resource URI 变更通知
  - unsubscribe：取消订阅
  - list：列出当前所有活跃订阅
- NEW-09: audit_query 工具（查询审计日志）
  - 支持 tool_name、time_range、success 过滤
  - 支持分页（limit/offset）
  - 返回审计记录详情（tool_name、params_summary、latency_ms、success、timestamp）

#### 命令-阶段映射完善
- NEW-05: COMMAND_PHASE_MAP 从 6 个命令扩展到 32 个命令完整映射
- 阶段转换披露模板：phase_transition_templates 定义阶段推进时的通知格式
- progressive_loader.py 新增 get_commands_for_phase() 和 get_phase_for_command() 查询函数

#### 质量门禁完善
- NEW-06: 质量门禁从 13 项扩展到 54 项（_shared.py QUALITY_GATES 完整定义）
- 新增跨阶段门禁：cross_phase_gates 检查阶段间一致性
- 门禁分类：BLOCK（阻塞）/ WARN（警告）/ INFO（信息）三级
- 门禁覆盖全部 9 个阶段 + 跨阶段检查

#### Schema 验证
- NEW-03: validate_schemas.py 验证脚本
  - 检查 MCP 工具定义与实际代码的 Schema 一致性
  - 检查 SKILL.md 声明与实际实现的匹配度
  - 修复 5 个 Schema-代码不一致问题
  - CI 集成：schema 验证可作为 pre-commit hook 运行

#### SKELETON 阶段命令
- SKILL-02: SKELETON 阶段基础命令支持（/status、/help、/budget 可用）
- COMMAND_PHASE_MAP 新增 /status、/help、/budget → SKELETON 映射
- routes.yaml /status phase null→0，新增 /help 命令路由（phase:0）

#### 文档
- docs/plan/ARCHITECTURE.md 总体架构文档
- docs/plan/DATABASE_DESIGN.md 数据存储设计文档
- docs/plan/MCP_REVIEW.md MCP 详细分析文档
- docs/plan/SKILL_REVIEW.md Skill 详细分析文档
- docs/plan/API_SPECIFICATION.md API 接口分析文档
- docs/plan/REFACTOR_PLAN.md 整合重构迭代方案
- docs/plan/v-l.md 版本演进文档
- docs/plan/v-comparison.md 功能对比文档
- docs/plan/v-git.md Git/GitHub 管理文档

### Changed
- PROBLEM.md 更新：9 个问题标记为 ✅已修复(v8.5.0)，新增 NEW-01/03/05/06/07/08/09 问题条目
- SKILL.md PHASE_0 新增 SKELETON 阶段可用命令表格，命令数 31→32
- routes.yaml /status phase null→0，新增 /help 命令路由（phase:0）
- progressive_loader.py COMMAND_PHASE_MAP 新增 /status、/help、/budget → SKELETON 映射
- pyproject.toml MCP Server 版本 8.4.0 → 8.5.0
- DB-01/DB-02 修复版本标注从 v8.4.0 更新为 v8.5.0（含本轮增强修复）

### Fixed
- NEW-07: 双 SQLite 数据库分裂 → ✅已修复(v8.5.0，db_engine.py 统一 xuansto.db)
- DB-01: 决策记录双写一致性风险 → ✅已修复(v8.5.0，SQLite 主存储+文件备份可选)
- DB-02: ChromaDB 与 SQLite 双写无事务保证 → ✅已修复(v8.5.0，3次指数退避重试+failed状态追踪)
- NEW-01: 降级映射不完整(14/20) → ✅已修复(v8.5.0，20/20 完整覆盖)
- NEW-08: 缺少 Resource 订阅机制 → ✅已修复(v8.5.0，resource_subscribe 工具)
- NEW-09: 缺少审计日志查询 → ✅已修复(v8.5.0，audit_query 工具)
- NEW-05: COMMAND_PHASE_MAP 不完整(6/32) → ✅已修复(v8.5.0，32/32 完整映射)
- NEW-06: 质量门禁不完整(13/54) → ✅已修复(v8.5.0，54/54 完整定义)
- NEW-03: Schema 验证缺失 → ✅已修复(v8.5.0，validate_schemas.py+5处不一致修复)
- SKILL-02: SKELETON 阶段无可用命令 → ✅已修复(v8.5.0，/status 和 /help 可用)

## [8.4.0] - 2026-05-26

### Added
- TRANS-01: Streamable HTTP传输支持（XUANSTO_TRANSPORT/XUANSTO_HOST/XUANSTO_PORT环境变量，mcp.run(transport="streamable-http")，mcp-config.json新增HTTP配置）
- DB-03: 知识条目版本历史清理配置项（KNOWLEDGE_VERSION_CLEANUP_KEEP_LAST_N环境变量，cleanup_knowledge_versions集成配置默认值）

### Changed
- server.py main()函数支持通过环境变量选择stdio/streamable-http传输
- knowledge_search cleanup_versions操作使用配置默认值
- mcp-config.json新增xuansto-mcp-server-http配置项

## [8.2.0] - 2026-05-26

### Added
- MCP-03: AuditLogger审计日志（工具调用审计：tool_name/params_summary/latency_ms/success/result_summary，JSONL持久化，线程安全，集成server.py工具调用链）
- API-01: 统一响应模式（make_response/make_success_response/make_error_response统一MCP stdio和HTTP API响应格式，ErrorCodes常量类，i18n错误消息）
- DB-01: Decision双写一致性（SQLite+文件系统双写+文件写入失败回滚SQLite+_reconcile_decisions对账函数+reconcile action）
- DB-02: ChromaDB/SQLite双写（persist_knowledge_dual_write+reconcile_knowledge_stores对账+cleanup_stale_pending_entries过期清理+reconciliation_log审计表）

### Changed
- DecisionLogInput新增reconcile action支持
- decision_log工具支持reconcile操作

## [8.3.0] - 2026-05-26

### Added
- ARCH-06: Agent状态持久化（agent_states表+save/load/delete_agent_state函数+SQLite UPSERT+重启恢复）
- ARCH-07: Workflow状态持久化（workflow_states表+save/load/delete_workflow_state函数+快照恢复）
- ARCH-08: Token-Phase链接（PHASE_TOKEN_BUDGET_MAP映射+set_from_phase action+阶段驱动预算调整）
- ARCH-09: Hook超时保护（DEFAULT_HOOK_TIMEOUT_SECONDS+asyncio.wait_for超时+超时不阻塞主流程）
- ARCH-10: 配置热重载（start_config_watcher+watchfiles事件驱动/轮询降级+reload_config+SIGHUP信号）
- ARCH-12: API版本协商（_negotiate_api_version+优雅降级+API_CHANGELOG+negotiate_version action）

### Changed
- Phase C (v8.3.0) 架构韧性特性全部实现并测试通过

## [8.1.0] - 2026-05-26

### Added
- MCP Resource xuansto://decisions/latest（最近决策记录）
- MCP Resource xuansto://workflows/active（活跃工作流实例）
- SKELETON 阶段基础命令支持（/status、/help、/budget）

### Changed
- MCP Resource 总数从 22 增至 27
- pyproject.toml 描述更新为 25+ resources

## [8.0.0] - 2026-05-24

### Added
- MCP Server + Skill 混合架构（26个MCP工具：11个知识管理+15个Skill工具）
- 57个Agent定义（13层编排架构）
- 54项质量门禁（BLOCK/WARN两级）
- 31个命令（/init到/budget）
- 渐进式加载4阶段（SKELETON→FUNCTIONAL→ENHANCED→FULL）
- 3级降级策略（MCP工具→脚本降级→内联降级→错误响应）
- 79+参考文档
- Token预算管理
- 决策日志（SQLite持久化）
- 工作流调度（9阶段全生命周期）
- Hook系统（minimal/standard/strict三级配置）
- 模型路由（fast/standard/deep）

### Changed
- 从v1纯Skill+脚本架构迁移到MCP+Skill混合架构
- 知识检索从简单关键词匹配升级为三层检索（hybrid/semantic_only/keyword_only）
- 降级策略从无到3级降级链

### Fixed
- P0-01: v2降级模式不可用（已实现MCPToolFallback类）
- P0-02: v2缺少references/完整参考文档（已补充79+参考文件）
- P1-01: MCP Server版本与Skill版本不一致（新增compatible_mcp_server字段）
- P1-02: server_health工具未在v2 mcp-tools.md中列出（已补充）
- P1-03: knowledge_search缺少inject/precipitate action文档（已补充）
