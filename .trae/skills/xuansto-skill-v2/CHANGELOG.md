# Changelog

All notable changes to xuansto-skill-v2 will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [8.0.0] - 2025-05-23

### Added

- MCP-first architecture with 17 atomic tools via xuansto-mcp-server
- Progressive resource loading with 4-phase disclosure (skeleton/functional/enhanced/full)
- Token budget management with per-phase allocation
- Decision logging with ADR support
- Context compression (semantic/selective/lossless strategies)
- Project initialization with stack detection
- Knowledge injection and precipitation workflow
- Metrics reporting with time-range queries
- Config hot-reload via watchfiles or polling
- Hook engine with pre/post plugin system
- Degradation fallback watcher
- Rate limiting with token bucket algorithm
- LRU cache for resource caching
- Optional AES-256-GCM snapshot encryption
- Name parameter whitelist validation against path traversal
- `error_type` column in error_patterns table
- `workflow_id` column in decision_records table
- `deleted_at` column in knowledge_entries table (soft delete)
- Evals directory with trigger accuracy and MCP evaluation suites
- Workflow YAML files as authoritative source definitions

### Changed

- Migrated from script-based toolchain to MCP server architecture
- Command count expanded from 27 to 31 (added /sdd-tdd-medium, /sdd-tdd-fast, /decision, /budget)
- Agent registry now loaded from YAML (agents/registry.yaml)
- Command routing table now loaded from YAML (commands/routes.yaml)
- SKILL.md slimmed down with detailed content moved to references/
- Action parameter made required on all tool input models
- Resource caching uses LRU eviction policy

### Fixed

- UTF-8 BOM detection in file encoding checks
- Session persistence integrity with hash verification
- ChromaDB path migration from legacy location

### Deprecated

- xuansto-skill (v5) — archived, no longer maintained
- Direct script invocation — use MCP tools instead

### Removed

- Shell script (.sh) support — Python-only for scripts
- Legacy knowledge_auto_retrieve and knowledge_progressive_search tools

### Security

- Rate limiting to prevent tool abuse (60 req/min per tool by default)
- Name parameter whitelist regex validation
- Path traversal prevention in validator
- Optional snapshot encryption with AES-256-GCM
- Security hook blocks dangerous commands (rm -rf, force push, DROP TABLE)
