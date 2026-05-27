# Changelog

## [9.0.0] - 2026-05-27

### Added
- CI流水线：Lint(ruff)+类型检查(mypy)+Schema校验+MCP定义验证+测试+构建
- API契约锁定：spec-locks/tool-parameter-schemas.json覆盖全部22个Tool
- Schema校验脚本：scripts/validate_schemas.py
- 全量回归测试：298个测试覆盖Tool完整性、Resource可访问性、降级链路、数据库统一
- 知识库废弃标记：scripts/knowledge_server/DEPRECATED.md
- Hook配置废弃标记：hooks.json添加_deprecated字段

### Changed
- 9份docs/plan文档基于v8.9.0-dev代码事实完全重写
- Resource返回类型优化：14个Resource从str改为dict结构化返回
- 模型路由统一：model-routing.md与registry.yaml对齐
- default.yaml空段清理：移除已迁移至constraints.yaml的token_optimization段
- Tool参数Schema对齐：修复5处Schema漂移

### Deprecated
- hooks.json：Hook配置已迁移至MCP Server hook_manage工具
- scripts/knowledge_server/：知识库存储已统一至xuansto-mcp-server

### Fixed
- decision_log.py两处IndentationError修复

## [8.0.0] - 2025-05-24

### Added
- 20 MCP tools with full parameter validation
- DegradationExecutor for automatic fallback
- Token budget runtime enforcement (80% compress, 95% degrade)
- Agent on-demand loading by phase
- Progressive loading interface (5 core actions)
- Dual-write confirmation for SQLite/ChromaDB
- AES-256 backup encryption with auto-generated key
- Version alignment between Skill and MCP Server
- Unified response format with retryable field
- SkillToolCall protocol definition
- DegradationCoordinator for unified exception handling
- 12 MCP Resource URIs
- Reconciliation log for data consistency

### Changed
- Tool count updated from 26 to 20
- SKILL.md PHASE markers for progressive loading
- ChromaDB single collection with embedding_tier metadata
- Agent registry with phase field for on-demand loading

### Deprecated
- triggers.yaml (use SKILL.md triggers instead)
