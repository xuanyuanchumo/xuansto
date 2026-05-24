# Changelog

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
