# Changelog

All notable changes to xuansto-skill-v2 will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
