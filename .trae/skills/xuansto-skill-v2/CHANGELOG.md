# Changelog

All notable changes to xuansto-skill-v2 will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
