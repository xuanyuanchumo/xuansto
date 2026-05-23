# MCP Review - xuansto-mcp-server 全面审查报告

> 基于 xuansto-mcp-server v3.5.0 源码事实分析
> 审查日期: 2026-05-22
> 项目类型: MCP + Skill 混合架构

---

## 目录

1. [现有MCP相关调用盘点](#1-现有mcp相关调用盘点)
2. [可MCP化能力识别](#2-可mcp化能力识别)
3. [目标MCP Server设计](#3-目标mcp-server设计)
4. [渐进式加载披露与MCP关联](#4-渐进式加载披露与mcp关联)
5. [与Skill层的交互协议](#5-与skill层的交互协议)

---

## 1. 现有MCP相关调用盘点

### 1.1 Server 概况

| 属性 | 值 |
|------|------|
| Server名称 | `xuansto-mcp-server` |
| 版本 | v3.5.0 |
| 传输协议 | stdio |
| 框架 | FastMCP (`mcp[cli]>=1.0.0`) |
| Python要求 | >=3.10 |
| 核心依赖 | mcp[cli]>=1.0.0, pydantic>=2.0.0, pyyaml>=6.0 |
| 可选依赖 | chromadb>=0.4.0, fastapi, uvicorn, openai, sentence-transformers |
| 入口函数 | `xuansto_mcp.server:main` |
| CLI入口 | `xuansto_mcp.cli:main` |
| API版本 | 1.0.0 |

### 1.2 13个Tool完整分析

#### Tool 1: skill_analyze

| 维度 | 详情 |
|------|------|
| **名称** | `skill_analyze` |
| **功能** | 分析技能项目结构，提取YAML元数据、目录结构、Agent注册表、脚本依赖和验证问题，评估项目规模并推荐工作流 |
| **参数Schema** | `SkillAnalyzeInput` - `skill_path: str`(必填), `include_scripts: bool=True`, `include_agents: bool=True`, `depth: str="basic"` |
| **返回值** | `{error, api_version, data: {metadata, structure, agents, dependencies, issues, project_scale, recommended_workflow, scale_details}}` |
| **ToolAnnotations** | readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False |
| **错误处理** | PathNotFoundError(路径不存在), INVALID_INPUT(参数校验失败), PARSE_ERROR(YAML解析失败) |
| **降级策略** | 脚本降级: `scripts/skill-test.py --analyze` → `scripts/skill-test.py --path` (二级降级) |
| **核心逻辑** | `_parse_yaml_frontmatter()` 解析SKILL.md, `_scan_directory()` 扫描目录, `_parse_agent_registry()` 解析Agent注册表, `_assess_project_scale()` 评估项目规模(small/medium/large → sdd-tdd-fast/medium/full) |

#### Tool 2: knowledge_search

| 维度 | 详情 |
|------|------|
| **名称** | `knowledge_search` |
| **功能** | 三层知识库(通用/工作区/经验)混合检索引擎，支持retrieve/inject/precipitate三种操作 |
| **参数Schema** | `KnowledgeSearchInput` - `action: str="retrieve"`, `query: str\|None`, `top_k: int=5(1-50)`, `search_type: str="hybrid"`, `scope: str\|None`, `min_confidence: float=0.0(0-1)`, `content: str\|None`(inject), `knowledge_type: str="general"`, `metadata: dict\|None`(inject), `pattern_ids: list\|None`(precipitate) |
| **返回值** | `{error, api_version, data: {results: [{source, content, match_type, relevance}], total, strategy}, degradation_level}` |
| **ToolAnnotations** | readOnlyHint=False, destructiveHint=False, idempotentHint=False, openWorldHint=True |
| **错误处理** | INVALID_INPUT(参数校验), NO_RESULTS(无匹配), DB_UNAVAILABLE(数据库不可用自动降级) |
| **降级策略** | 三级降级链: ChromaDB语义搜索 → SQLite FTS5 BM25 → keyword_fallback关键词搜索; 脚本降级: `scripts/knowledge-server.py --search` |
| **核心逻辑** | `_chromadb_search()` 向量语义检索, `_sqlite_search()` FTS5全文检索, `_keyword_fallback_search()` 关键词TF-IDF检索, `_inject_knowledge()` 知识注入(写文件+索引), `_precipitate_experience()` 经验沉淀(模式分析+文档生成) |

#### Tool 3: quality_gate_check

| 维度 | 详情 |
|------|------|
| **名称** | `quality_gate_check` |
| **功能** | 执行54项质量门禁检查，支持按门禁ID或开发阶段(0-8)过滤，自动映射门禁到检查脚本 |
| **参数Schema** | `QualityGateCheckInput` - `gate_ids: list\|None`, `phase: str\|None`, `project_path: str="."`, `severity_filter: str="all"`, `force_refresh: bool=False` |
| **返回值** | `{error, api_version, data: {checks: [{gate_id, status, source, details, suggestion}], summary: {total, passed, failed, skipped, blocked}, cache_info: {hit, hit_count, miss_count, cache_age_seconds}}}` |
| **ToolAnnotations** | readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False |
| **错误处理** | INVALID_INPUT, NOT_FOUND(门禁ID不存在), GATE_BLOCKED(存在BLOCK级别失败) |
| **降级策略** | 脚本降级: `scripts/skill-test.py --gate` → 逐门禁脚本降级(`GATE_SCRIPTS_MAP`映射) → 内嵌检查(`INLINE_CHECKS`36项内嵌实现) |
| **核心逻辑** | `_resolve_gates()` 解析门禁列表, `_compute_file_hashes()` SHA256哈希缓存(含持久化), `_load_gate_cache()`/`_save_gate_cache()` 门禁结果缓存, 36个内嵌检查函数覆盖Phase 0-8 |

#### Tool 4: spec_drift_detect

| 维度 | 详情 |
|------|------|
| **名称** | `spec_drift_detect` |
| **功能** | 检测规格文档(spec)与代码实现(src)之间的偏差，支持AST级别分析 |
| **参数Schema** | `SpecDriftDetectInput` - `spec_dir: str=".trae/specs"`, `src_dir: str="."` |
| **返回值** | `{error, api_version, data: {total_specs, total_pending_tasks, drifts: [{task, spec_file, has_implementation, potential_files, best_match, match_coverage}], implementation_rate, analysis_level, interface_coverage}}` |
| **ToolAnnotations** | readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False |
| **错误处理** | INVALID_INPUT, NO_SPECS(规格目录为空), PARSE_ERROR |
| **降级策略** | 脚本降级: `scripts/spec-drift-detector.py` → 内嵌AST分析 `_inline_spec_drift()` (degradation_level="inline") |
| **核心逻辑** | `_parse_python_ast()` Python AST解析提取符号表, `_match_spec_to_ast()` 规格任务与AST符号匹配, 支持AST级别和关键词匹配两种分析级别 |

#### Tool 5: security_scan

| 维度 | 详情 |
|------|------|
| **名称** | `security_scan` |
| **功能** | OWASP Agentic Top 10检查 + 依赖漏洞扫描，支持严重级别过滤 |
| **参数Schema** | `SecurityScanInput` - `target: str="."`, `severity_threshold: str="medium"`, `include_agentic: bool=True`, `include_dependency: bool=True` |
| **返回值** | `{error, api_version, data: {agentic_scan: {vulnerabilities, total, by_severity, security_score}, dependency_scan: {dependencies, total, vulnerable_count}}, degradation_level}` |
| **ToolAnnotations** | readOnlyHint=True, destructiveHint=False, idempotentHint=False, openWorldHint=True |
| **错误处理** | INVALID_INPUT, NOT_FOUND, SCAN_ERROR |
| **降级策略** | 脚本降级: `scripts/agentic-security-scanner.py` → 内嵌扫描 `_inline_agentic_scan()`; `scripts/dependency-scan.py` → 内嵌扫描 `_inline_dependency_scan()` |
| **核心逻辑** | 6种漏洞模式正则检测(hardcoded_secret/eval_exec/sql_injection/unsafe_deserialization/xss/unsafe_shell), `_is_likely_false_positive()` 误报过滤, `_calculate_security_score()` 安全评分(0-100), 依赖版本比对 |

#### Tool 6: code_simplify

| 维度 | 详情 |
|------|------|
| **名称** | `code_simplify` |
| **功能** | 代码简化分析：检测死代码、深层嵌套、过长函数、重复代码和圈复杂度 |
| **参数Schema** | `CodeSimplifyInput` - `target: str`(必填), `scope: str="recent"`, `include_dedup: bool=True` |
| **返回值** | `{error, api_version, data: {simplification: {suggestions, total, by_type, quality_score, analysis_level}, deduplication: {duplicates, total_groups, total_duplicate_lines}}, degradation_level}` |
| **ToolAnnotations** | readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False |
| **错误处理** | INVALID_INPUT, NOT_FOUND, PARSE_ERROR |
| **降级策略** | 脚本降级: `scripts/code-simplifier.py` → 内嵌分析 `_inline_simplify()`; `scripts/deduplication-detector.py` → 内嵌去重 `_inline_dedup()` |
| **核心逻辑** | `_calculate_cyclomatic_complexity()` 圈复杂度计算, `_detect_long_functions()` 长函数检测(>50行), `_detect_deep_nesting()` 深层嵌套检测(>4层), `_detect_unused_imports()` 未使用导入, `_detect_dead_code()` 死代码检测, `_inline_dedup()` MD5块级重复检测 |

#### Tool 7: session_manage

| 维度 | 详情 |
|------|------|
| **名称** | `session_manage` |
| **功能** | 会话状态管理：保存/加载/列出会话记录，检测重复错误模式，验证经验模式，追踪/恢复会话状态 |
| **参数Schema** | `SessionManageInput` - `action: str`(必填: save/load/list/detect/verify/track/restore), `completed_tasks: list\|None`, `pending_tasks: list\|None`, `decisions: list\|None`, `experience: list\|None`, `error_log: list\|None`, `pattern_path: str\|None`, `success: bool=True`, `current_phase: int\|None`, `current_task: str\|None` |
| **返回值** | `{error, api_version, data: {action, path/filename/content/patterns/state...}}` |
| **ToolAnnotations** | readOnlyHint=False, destructiveHint=False, idempotentHint=False, openWorldHint=False |
| **错误处理** | INVALID_INPUT, NOT_FOUND(会话不存在), SAVE_ERROR, VERIFY_FAILED |
| **降级策略** | 脚本降级: `scripts/init-session.py`(save/init) → `scripts/session-catchup.py`(load/detect/restore) → `scripts/session-persist.py`(兜底) |
| **核心逻辑** | `_save_session()` 生成Markdown会话文件, `_detect_patterns()` 错误模式检测(频次>=2自动生成模式文件), `_verify_pattern()` 模式置信度递增验证(0.40→0.80→verified), `_track_session()` 实时状态追踪(current.json), `_restore_session()` 启动时恢复, 最多保留10个历史会话 |

#### Tool 8: workflow_dispatch

| 维度 | 详情 |
|------|------|
| **名称** | `workflow_dispatch` |
| **功能** | 工作流调度：启动/查询/中止/阶段推进/快照恢复工作流执行，9阶段SDD+TDD工作流 |
| **参数Schema** | `WorkflowDispatchInput` - `action: str`(必填: start/status/abort/phase/recover/snapshots), `workflow: str\|None`, `project_path: str="."`, `workflow_id: str\|None`, `phase_action: str\|None`(advance/current), `snapshot_phase: int\|None` |
| **返回值** | `{error, api_version, data: {workflow_id, workflow, status, current_phase, completed_phases, phase_definitions/advanced/gates_checked/...}}` |
| **ToolAnnotations** | readOnlyHint=False, destructiveHint=False, idempotentHint=False, openWorldHint=False |
| **错误处理** | INVALID_INPUT, WORKFLOW_NOT_FOUND, ALREADY_RUNNING, ABORT_FAILED |
| **降级策略** | 脚本降级: `scripts/project-initializer.py`(start) → 内联Phase推进(status/abort/recover) |
| **核心逻辑** | `_start_workflow()` 解析工作流定义(YAML frontmatter)并创建实例, `_advance_phase()` 阶段推进含门禁检查, `_save_snapshot()` gzip压缩快照持久化, `_load_latest_snapshot()` 快照恢复, `_cleanup_snapshots()` TTL+数量双重清理策略, 9阶段名称映射(初始化→需求分析→架构设计→测试先行→代码实现→测试验证→验收确认→持续重构→部署交付) |

#### Tool 9: agent_status

| 维度 | 详情 |
|------|------|
| **名称** | `agent_status` |
| **功能** | Agent状态查询与管理：列出Agent、按Phase查询、查询详情、创建/匹配/分配/释放/销毁实例 |
| **参数Schema** | `AgentStatusInput` - `action: str`(必填: list/by_phase/detail/create/match/assign/release/instance_status/destroy/schedule), `phase: int\|None(0-8)`, `agent_name: str\|None`, `agent_type: str\|None`, `capabilities: list\|None`, `agent_id: str\|None`, `task: str\|None` |
| **返回值** | `{error, api_version, data: {agents, total, phase/agent_id/status/...}}` |
| **ToolAnnotations** | readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False |
| **错误处理** | INVALID_INPUT, NOT_FOUND(Agent不存在), AGENT_BUSY, VALIDATION_ERROR |
| **降级策略** | 静态注册表查询(AGENTS_DIR) → `scripts/skill-test.py --agents` |
| **核心逻辑** | `PHASE_AGENT_MAP` 9阶段Agent映射(57个Agent), `_AgentInstance` dataclass实例管理(idle/busy状态机), `_persist_agent_instances()` 持久化, `_parse_agent_registry()` Markdown注册表解析, 能力匹配(match)按覆盖率排序, 最大实例数20 |

#### Tool 10: hook_manage

| 维度 | 详情 |
|------|------|
| **名称** | `hook_manage` |
| **功能** | Hook管理：列出指定profile的Hook配置，执行指定Hook，含7种内嵌Hook逻辑 |
| **参数Schema** | `HookManageInput` - `action: str`(必填: list/execute), `profile: str="standard"`, `hook_name: str\|None`, `context: dict\|None` |
| **返回值** | `{error, api_version, data: {profile, hooks: [{name, has_script, script, has_inline_logic}], hook, status, message, details, source}}` |
| **ToolAnnotations** | readOnlyHint=False, destructiveHint=False, idempotentHint=False, openWorldHint=False |
| **错误处理** | INVALID_INPUT, NOT_FOUND(Hook不存在), EXECUTION_ERROR |
| **降级策略** | 脚本降级: `HOOK_SCRIPTS_MAP`映射(16个Hook脚本) → `INLINE_HOOK_LOGIC`内嵌逻辑(7种) |
| **核心逻辑** | 3种profile(minimal=2/standard=10/strict=16), 7种内嵌Hook: security-block(危险命令拦截), dangerous-cmd-confirm(中等危险确认), auto-format(格式检查), console-log-detect(调试输出检测), type-check(TypeScript环境检查), git-status-check(Git状态检查), decision-log-persist(决策日志持久化); `_HOOK_TOOL_MAP` 定义Hook与Tool的绑定关系; Pre-hook可block执行, Post-hook不阻塞 |

#### Tool 11: resource_load_status

| 维度 | 详情 |
|------|------|
| **名称** | `resource_load_status` |
| **功能** | 渐进式加载状态管理：查询资源加载状态、预加载指定Phase资源、缓存管理、加载进度追踪 |
| **参数Schema** | `ResourceLoadStatusInput` - `action: str`(必填: status/preload/cache/clear_cache/loading_progress), `phase: int\|None(0-8)`, `resource_ids: list\|None`, `resource_uris: list\|None`, `priority: str="normal"`, `batch_mode: bool=False` |
| **返回值** | `{error, api_version, data: {resources: [{id, type, path, status}], total, loaded, stale, expired, available_functions, disclosure_note / preloaded / cache / progress...}}` |
| **ToolAnnotations** | readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False |
| **错误处理** | INVALID_INPUT, NOT_FOUND, LOAD_ERROR, TOKEN_BUDGET_EXCEEDED |
| **降级策略** | 内联状态检查(直接读取文件系统)，无独立降级脚本 |
| **核心逻辑** | `PHASE_RESOURCE_MAP` 9阶段资源映射(18个资源), `_RESOURCE_CACHE` 内存缓存(TTL=3600s, 最大100条), `_LOADED_PROGRESS` 加载进度追踪, `_compute_path_hash()` SHA256内容哈希变更检测, `_URI_DIR_MAP` URI到目录映射, 4级加载阶段(skeleton/functional/enhanced/full), Phase继承机制(Phase 7继承Phase 4) |

#### Tool 12: context_compress

| 维度 | 详情 |
|------|------|
| **名称** | `context_compress` |
| **功能** | 上下文压缩：支持semantic(语义保留)/selective(选择性采样)/lossless(无损截断)三种策略 |
| **参数Schema** | `ContextCompressInput` - `content: str`(必填), `strategy: str="semantic"`, `target_tokens: int=2000(100-50000)`, `preserve_sections: list\|None` |
| **返回值** | `{error, api_version, data: {compressed, original_tokens, compressed_tokens, compression_ratio, strategy, preserved_chunks, total_chunks}}` |
| **ToolAnnotations** | readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False |
| **错误处理** | INVALID_INPUT, TARGET_TOO_SMALL, COMPRESSION_FAILED |
| **降级策略** | 脚本降级: `scripts/context-compressor.py` |
| **核心逻辑** | `_split_into_semantic_chunks()` 语义分块(heading/import/class/function/prose), `_score_chunk_importance()` 重要性评分, `_semantic_compress()` 按重要性排序保留, `_selective_compress()` 按关键词选择性保留, `_compress_lossless()` 无损截断, `_estimate_tokens()` Token估算(len/4) |

#### Tool 13: server_health

| 维度 | 详情 |
|------|------|
| **名称** | `server_health` |
| **功能** | MCP Server健康检查：返回服务器状态、版本、运行时间、工具统计、ChromaDB健康、降级统计、性能指标 |
| **参数Schema** | 无参数 |
| **返回值** | `{error, api_version, data: {status, version, uptime_seconds, tools_count, resources_count, active_workflows, snapshot_cleanup, degradation_stats, performance_metrics: {call_count, error_count, error_rate, latency_p50/p95/p99}, services: {chromadb: {available, latency_ms, reason}}, config: {data_dir, skill_root, work_dir}}}` |
| **ToolAnnotations** | readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False |
| **错误处理** | UNAVAILABLE, TIMEOUT, PARTIAL_DEGRADATION, VERSION_MISMATCH |
| **降级策略** | 脚本降级: `scripts/health-checker.py` → 返回 `{status: "degraded", mcp_available: False}` |
| **核心逻辑** | `_check_chromadb_health()` ChromaDB可用性检测, `_TOOL_METRICS` 工具调用指标(调用次数/错误率/P50/P95/P99延迟), `_DEGRADATION_COUNTS` 降级计数追踪, `_persist_metrics()` 指标持久化(60s间隔或100次调用阈值), `_cleanup_all_snapshots()` 快照清理(300s间隔) |

### 1.3 7个Resource完整分析

#### Resource 1: xuansto://config/skill

| 维度 | 详情 |
|------|------|
| **URI** | `xuansto://config/skill` |
| **数据源** | `SKILL_ROOT / ".skill-config.yaml"` |
| **内容类型** | YAML文本 |
| **说明** | 技能配置文件，包含gate_scripts、gates_by_phase、hook_scripts等配置映射。文件不存在时返回 `# 配置文件不存在` |

#### Resource 2: xuansto://references/quality-gates

| 维度 | 详情 |
|------|------|
| **URI** | `xuansto://references/quality-gates` |
| **数据源** | `REFERENCES_DIR / "quality-gates.md"` |
| **内容类型** | Markdown文本 |
| **说明** | 54项质量门禁定义文档，包含门禁ID、描述、严重级别和检查逻辑说明。文件不存在时返回 `# 质量门禁文档不存在` |

#### Resource 3: xuansto://references/agent-registry

| 维度 | 详情 |
|------|------|
| **URI** | `xuansto://references/agent-registry` |
| **数据源** | `REFERENCES_DIR / "agent-registry.md"` |
| **内容类型** | Markdown文本 |
| **说明** | Agent注册表文档，按层级列出57个Agent的名称、能力和定义。文件不存在时返回 `# Agent注册表不存在` |

#### Resource 4: xuansto://references/workflow-phases

| 维度 | 详情 |
|------|------|
| **URI** | `xuansto://references/workflow-phases` |
| **数据源** | `REFERENCES_DIR / "workflow-phases.md"` |
| **内容类型** | Markdown文本 |
| **说明** | 工作流阶段定义文档，描述9阶段(0-8)的名称、目标、门禁和产出。文件不存在时返回 `# 工作流定义不存在` |

#### Resource 5: xuansto://templates/{name}

| 维度 | 详情 |
|------|------|
| **URI** | `xuansto://templates/{name}` (模板Resource) |
| **数据源** | `TEMPLATES_DIR / "{name}.md"` |
| **内容类型** | Markdown文本 |
| **说明** | 动态模板Resource，按名称加载模板文件。含路径遍历防护(禁止`/`、`\\`、`..`)和resolve安全检查(确保在TEMPLATES_DIR内)。模板不存在时返回 `Template '{name}' not found` |

#### Resource 6: xuansto://sessions/latest

| 维度 | 详情 |
|------|------|
| **URI** | `xuansto://sessions/latest` |
| **数据源** | `SESSION_DIR` 下最新的 `session-*.md` 文件 |
| **内容类型** | Markdown文本 |
| **说明** | 最近一次会话记录，按文件名倒序排列取第一个。SESSION_DIR不存在时自动创建。无会话时返回 `# 无会话记录` |

#### Resource 7: xuansto://loading/status

| 维度 | 详情 |
|------|------|
| **URI** | `xuansto://loading/status` |
| **数据源** | `WORK_DIR / "resource_state.json"` + 运行时计算 |
| **内容类型** | JSON文本 |
| **说明** | 渐进式加载状态，包含current_phase、loaded_resources、available_functions、loading_progress、disclosure_note。4级加载阶段(skeleton/functional/enhanced/full)，每阶段披露可用功能集合。文件不存在时默认skeleton阶段 |

### 1.4 降级体系总览

```
FALLBACK_MAP (13个Tool → 13个降级函数)
├── skill_analyze       → skill-test.py --analyze → skill-test.py --path
├── knowledge_search    → knowledge-server.py --search → knowledge-server.py search
├── quality_gate_check  → skill-test.py --gate → 逐门禁脚本(GATE_SCRIPTS_MAP) → INLINE_CHECKS(36项)
├── spec_drift_detect   → spec-drift-detector.py → _inline_spec_drift()
├── security_scan       → agentic-security-scanner.py → _inline_agentic_scan(); dependency-scan.py → _inline_dependency_scan()
├── code_simplify       → code-simplifier.py → _inline_simplify(); deduplication-detector.py → _inline_dedup()
├── session_manage      → init-session.py → session-catchup.py → session-persist.py
├── workflow_dispatch   → project-initializer.py(start) → 内联Phase推进
├── agent_status        → AGENTS_DIR静态注册表 → skill-test.py --agents
├── hook_manage         → HOOK_SCRIPTS_MAP脚本 → INLINE_HOOK_LOGIC(7种内嵌)
├── resource_load_status → 内联状态检查(直接读文件系统)
├── context_compress    → context-compressor.py
└── server_health       → health-checker.py → {status: "degraded"}
```

降级级别标记:
- `"script"`: 使用外部脚本降级
- `"inline"`: 使用内嵌逻辑降级
- `"keyword_fallback"`: 知识检索最低级降级
- `"sqlite_fts5"`: 知识检索中级降级
- `"chromadb"`: 知识检索最高级(正常)
- `"partial"`: 部分降级(code_simplify的dedup降级但simplify正常)

### 1.5 Hook拦截体系

Server层通过 `_with_hook_interception()` 包装所有Tool调用:

```
Tool调用流程:
1. Pre-hook执行 → 如果status="block"则直接返回blocked响应
2. 执行Tool主逻辑 → 记录latency和成功/失败
3. Post-hook执行 → 不阻塞，错误附加到hook_errors
4. 返回结果(含hook_errors如有)
```

Hook-Tool绑定关系:
- security-block → code_simplify, security_scan, spec_drift_detect
- dangerous-cmd-confirm → workflow_dispatch
- auto-format → code_simplify
- console-log-detect → code_simplify
- type-check → quality_gate_check
- git-status-check → workflow_dispatch
- decision-log-persist → workflow_dispatch, session_manage (Post-hook)

### 1.6 错误处理体系

```
XuanstoMCPError (基类)
├── PathNotFoundError     → code="PATH_NOT_FOUND"
├── ScriptExecutionError  → code="SCRIPT_EXECUTION_ERROR"
├── DegradationError      → code="DEGRADATION"
└── ValidationError       → code="VALIDATION_ERROR"

统一响应格式:
- 成功: {error: False, api_version: "1.0.0", data: {...}, degradation_level?: str}
- 失败: {error: True, code: str, message: str, details: {...}}
- Pydantic校验失败自动转换为: {error: True, code: "VALIDATION_ERROR", message: "参数校验失败: N个错误", details: {errors: [{field, message}]}}
- 未知异常: {error: True, code: "INTERNAL_ERROR", message: str(e), details: {}}
```

---

## 2. 可MCP化能力识别

### 2.1 核心逻辑拆分为独立功能单元

基于源码分析，将现有能力拆分为以下功能单元，并标记MCP封装适配度:

#### 适合Tool封装的能力 (输入输出明确/无状态或状态可管理)

| 功能单元 | 当前归属 | 输入 | 输出 | 状态 | 适配度 | 说明 |
|----------|----------|------|------|------|--------|------|
| 项目规模评估 | skill_analyze | project_path | scale/recommended_workflow | 无状态 | ★★★★★ | 纯计算逻辑，输入输出明确 |
| YAML Frontmatter解析 | skill_analyze | file_path | metadata dict | 无状态 | ★★★★☆ | 通用解析能力，可独立暴露 |
| 知识注入 | knowledge_search | content/type/metadata | injected_id/indexed | 有状态(DB) | ★★★★★ | 已独立为action=inject |
| 经验沉淀 | knowledge_search | pattern_ids | precipitated_id/themes | 有状态(文件) | ★★★★★ | 已独立为action=precipitate |
| 门禁检查(单门禁) | quality_gate_check | gate_id/project_path | pass/fail/details | 无状态(有缓存) | ★★★★★ | 可拆分为原子Tool |
| 规格偏差检测 | spec_drift_detect | spec_dir/src_dir | drifts/implementation_rate | 无状态 | ★★★★★ | 已独立 |
| 安全漏洞扫描 | security_scan | target/threshold | vulnerabilities/score | 无状态 | ★★★★★ | 已独立 |
| 依赖漏洞扫描 | security_scan | target | dependencies/vulnerable | 无状态 | ★★★★★ | 可从security_scan拆分 |
| 代码简化分析 | code_simplify | target/scope | suggestions/quality_score | 无状态 | ★★★★★ | 已独立 |
| 重复代码检测 | code_simplify | target | duplicates/groups | 无状态 | ★★★★★ | 可从code_simplify拆分 |
| 会话保存 | session_manage | tasks/decisions/experience | path/filename | 有状态(文件) | ★★★★★ | 已独立为action=save |
| 会话恢复 | session_manage | 无 | state/content | 有状态(文件) | ★★★★★ | 已独立为action=restore |
| 工作流启动 | workflow_dispatch | workflow/project_path | workflow_id/status | 有状态(内存+文件) | ★★★★★ | 已独立为action=start |
| 阶段推进 | workflow_dispatch | workflow_id | advanced/gates_checked | 有状态 | ★★★★★ | 已独立为action=phase/advance |
| 快照恢复 | workflow_dispatch | workflow_id/snapshot_phase | recovered_phase/state | 有状态 | ★★★★☆ | 已独立为action=recover |
| Agent实例管理 | agent_status | agent_type/capabilities/task | agent_id/status | 有状态(内存+文件) | ★★★★★ | 已独立 |
| Hook执行 | hook_manage | hook_name/context | status/message/details | 无状态 | ★★★★☆ | 已独立 |
| 资源预加载 | resource_load_status | phase/uris/priority | loaded_count/progress | 有状态(缓存) | ★★★★★ | 已独立 |
| 上下文压缩 | context_compress | content/strategy/target_tokens | compressed/ratio | 无状态 | ★★★★★ | 已独立 |
| 健康检查 | server_health | 无 | status/metrics/services | 有状态(指标) | ★★★★★ | 已独立 |

#### 适合Resource封装的数据 (模板/配置/静态定义)

| 数据单元 | 当前归属 | URI候选 | 内容类型 | 更新频率 | 说明 |
|----------|----------|---------|----------|----------|------|
| 技能配置 | Resource | xuansto://config/skill | YAML | 低(手动) | 已实现 |
| 质量门禁定义 | Resource | xuansto://references/quality-gates | Markdown | 低(版本更新) | 已实现 |
| Agent注册表 | Resource | xuansto://references/agent-registry | Markdown | 低(版本更新) | 已实现 |
| 工作流阶段定义 | Resource | xuansto://references/workflow-phases | Markdown | 低(版本更新) | 已实现 |
| 模板库 | Resource | xuansto://templates/{name} | Markdown | 低(手动) | 已实现 |
| 最新会话 | Resource | xuansto://sessions/latest | Markdown | 高(每次save) | 已实现 |
| 加载状态 | Resource | xuansto://loading/status | JSON | 高(运行时) | 已实现 |
| 门禁脚本映射 | config.py | xuansto://config/gate-scripts | JSON | 低(配置更新) | **新增候选** |
| Hook脚本映射 | config.py | xuansto://config/hook-scripts | JSON | 低(配置更新) | **新增候选** |
| 阶段-门禁映射 | config.py | xuansto://config/phase-gates | JSON | 低(配置更新) | **新增候选** |
| 阶段-资源映射 | resource_load_status | xuansto://config/phase-resources | JSON | 低(版本更新) | **新增候选** |

### 2.2 不适合MCP化的能力

| 功能单元 | 原因 | 替代方案 |
|----------|------|----------|
| Hook拦截包装 | 属于Server内部中间件逻辑，非外部调用接口 | 保持在Server内部 |
| 配置热重载 | 内部守护线程，非外部触发 | 通过Resource暴露配置，修改后自动重载 |
| 指标持久化 | 内部定时任务，非外部调用 | 通过server_health暴露结果 |
| 快照清理 | 内部定时任务，非外部调用 | 通过server_health触发 |

---

## 3. 目标MCP Server设计

### 3.1 Server基本信息

| 属性 | 值 |
|------|------|
| Server名称 | `xuansto-mcp-server` |
| 描述 | Xuansto Skill MCP服务器 - 16原子工具 + 11资源，驱动SDD+TDD全生命周期自主开发编排 |
| 版本 | v4.0.0 (目标) |
| 传输协议 | stdio |
| 框架 | FastMCP |

### 3.2 Tool列表 (16个 = 现有13 + 新增3)

#### 现有13个Tool (保持不变)

| # | 名称 | 描述 | 参数Schema | 返回值描述 |
|---|------|------|-----------|-----------|
| 1 | skill_analyze | 分析技能项目结构 | 见1.2节Tool 1 | metadata/structure/agents/dependencies/issues/project_scale |
| 2 | knowledge_search | 三层知识库混合检索 | 见1.2节Tool 2 | results/total/strategy + inject/precipitate结果 |
| 3 | quality_gate_check | 54项质量门禁检查 | 见1.2节Tool 3 | checks/summary/cache_info |
| 4 | spec_drift_detect | 规格偏差检测 | 见1.2节Tool 4 | drifts/implementation_rate/analysis_level |
| 5 | security_scan | 安全扫描 | 见1.2节Tool 5 | agentic_scan/dependency_scan/security_score |
| 6 | code_simplify | 代码简化分析 | 见1.2节Tool 6 | simplification/deduplication/quality_score |
| 7 | session_manage | 会话状态管理 | 见1.2节Tool 7 | action对应结果 |
| 8 | workflow_dispatch | 工作流调度 | 见1.2节Tool 8 | workflow_id/status/phase信息 |
| 9 | agent_status | Agent状态管理 | 见1.2节Tool 9 | agents/agent_id/status |
| 10 | hook_manage | Hook管理 | 见1.2节Tool 10 | hooks/hook执行结果 |
| 11 | resource_load_status | 渐进式加载管理 | 见1.2节Tool 11 | resources/preloaded/cache/progress |
| 12 | context_compress | 上下文压缩 | 见1.2节Tool 12 | compressed/ratio/strategy |
| 13 | server_health | 健康检查 | 见1.2节Tool 13 | status/metrics/services/config |

#### 新增3个Tool

##### Tool 14: decision_log

```json
{
  "name": "decision_log",
  "description": "决策日志管理：记录/查询/导出开发过程中的架构决策记录(ADR)。支持按阶段、时间范围过滤，自动关联工作流和会话上下文。",
  "parameters": {
    "type": "object",
    "properties": {
      "action": {
        "type": "string",
        "enum": ["record", "list", "export", "query"],
        "description": "操作类型: record(记录决策), list(列出决策), export(导出决策日志), query(按条件查询)"
      },
      "title": {
        "type": "string",
        "description": "决策标题(record时使用)，格式: ADR-NNN 简述"
      },
      "context": {
        "type": "string",
        "description": "决策背景和原因(record时使用)"
      },
      "decision": {
        "type": "string",
        "description": "决策内容(record时使用)"
      },
      "alternatives": {
        "type": "array",
        "items": {"type": "string"},
        "description": "被考虑的替代方案(record时使用)"
      },
      "consequences": {
        "type": "string",
        "description": "决策后果和影响(record时使用)"
      },
      "phase": {
        "type": "integer",
        "minimum": 0,
        "maximum": 8,
        "description": "关联的开发阶段(0-8)"
      },
      "workflow_id": {
        "type": "string",
        "description": "关联的工作流实例ID"
      },
      "query_text": {
        "type": "string",
        "description": "搜索查询文本(query时使用)"
      },
      "format": {
        "type": "string",
        "enum": ["markdown", "json"],
        "default": "markdown",
        "description": "导出格式(export时使用)"
      },
      "since": {
        "type": "string",
        "description": "起始时间ISO格式(query/export时使用)"
      },
      "until": {
        "type": "string",
        "description": "截止时间ISO格式(query/export时使用)"
      }
    },
    "required": ["action"]
  },
  "returns": {
    "record": "ADR记录ID和文件路径",
    "list": "决策列表[{id, title, phase, timestamp, workflow_id}]",
    "export": "完整决策日志内容(markdown或json格式)",
    "query": "匹配的决策记录列表"
  }
}
```

##### Tool 15: token_budget

```json
{
  "name": "token_budget",
  "description": "Token预算管理：查询/设置/监控上下文窗口的Token使用预算。跟踪各Tool的Token消耗，在预算不足时自动触发压缩建议，防止上下文溢出。",
  "parameters": {
    "type": "object",
    "properties": {
      "action": {
        "type": "string",
        "enum": ["status", "set_budget", "track", "recommend", "history"],
        "description": "操作类型: status(查询预算状态), set_budget(设置预算), track(记录消耗), recommend(获取压缩建议), history(查看消耗历史)"
      },
      "total_budget": {
        "type": "integer",
        "minimum": 1000,
        "maximum": 500000,
        "description": "总Token预算(set_budget时使用)"
      },
      "tool_name": {
        "type": "string",
        "description": "Tool名称(track时使用)"
      },
      "tokens_used": {
        "type": "integer",
        "minimum": 0,
        "description": "消耗的Token数(track时使用)"
      },
      "tokens_returned": {
        "type": "integer",
        "minimum": 0,
        "description": "返回的Token数(track时使用)"
      },
      "phase": {
        "type": "integer",
        "minimum": 0,
        "maximum": 8,
        "description": "当前阶段(recommend时使用，影响压缩策略)"
      },
      "window_type": {
        "type": "string",
        "enum": ["input", "output", "total"],
        "default": "total",
        "description": "预算窗口类型(set_budget时使用)"
      }
    },
    "required": ["action"]
  },
  "returns": {
    "status": "预算状态{total_budget, used, remaining, usage_percent, by_tool, warnings}",
    "set_budget": "设置确认{budget, window_type}",
    "track": "追踪确认{tracked, running_total}",
    "recommend": "压缩建议{should_compress, strategy, target_tokens, savings_estimate, tools_to_compress}",
    "history": "消耗历史[{timestamp, tool_name, tokens_used, running_total}]"
  }
}
```

##### Tool 16: project_init

```json
{
  "name": "project_init",
  "description": "项目初始化：创建项目骨架、生成配置文件、初始化工作目录结构。支持多种项目模板(React/Vue/Svelte/Electron/Tauri/Python)，自动检测技术栈并推荐工作流。",
  "parameters": {
    "type": "object",
    "properties": {
      "action": {
        "type": "string",
        "enum": ["init", "detect", "scaffold", "validate"],
        "description": "操作类型: init(完整初始化), detect(检测技术栈), scaffold(生成骨架), validate(验证项目结构)"
      },
      "project_path": {
        "type": "string",
        "description": "项目根目录路径"
      },
      "template": {
        "type": "string",
        "enum": ["react-vite-ts", "vue-vite-ts", "svelte-kit", "next-js", "electron-react", "tauri-react", "python-fastapi", "python-cli", "auto"],
        "default": "auto",
        "description": "项目模板(init/scaffold时使用)，auto自动检测"
      },
      "project_name": {
        "type": "string",
        "description": "项目名称(init时使用)"
      },
      "features": {
        "type": "array",
        "items": {"type": "string"},
        "description": "启用特性列表(init时使用): testing, ci-cd, docker, linting, formatting"
      },
      "workflow": {
        "type": "string",
        "enum": ["sdd-tdd-full", "sdd-tdd-medium", "sdd-tdd-fast", "auto"],
        "default": "auto",
        "description": "关联工作流(init时使用)，auto根据项目规模自动选择"
      }
    },
    "required": ["action"]
  },
  "returns": {
    "init": "初始化结果{project_path, template, workflow_id, created_files, directories, config_files}",
    "detect": "检测结果{detected_stack, framework, language, package_manager, suggested_template, suggested_workflow}",
    "scaffold": "骨架生成结果{created_files, directories, template_used}",
    "validate": "验证结果{valid, missing_files, missing_dirs, suggestions}"
  }
}
```

### 3.3 Resource列表 (11个 = 现有7 + 新增4)

#### 现有7个Resource (保持不变)

| # | URI | 内容类型 | 描述 |
|---|-----|----------|------|
| 1 | `xuansto://config/skill` | YAML | 技能配置文件 |
| 2 | `xuansto://references/quality-gates` | Markdown | 质量门禁定义 |
| 3 | `xuansto://references/agent-registry` | Markdown | Agent注册表 |
| 4 | `xuansto://references/workflow-phases` | Markdown | 工作流阶段定义 |
| 5 | `xuansto://templates/{name}` | Markdown | 动态模板 |
| 6 | `xuansto://sessions/latest` | Markdown | 最新会话记录 |
| 7 | `xuansto://loading/status` | JSON | 渐进式加载状态 |

#### 新增4个Resource

| # | URI模式 | 内容类型 | 描述 | 数据源 |
|---|---------|----------|------|--------|
| 8 | `xuansto://config/gate-scripts` | JSON | 门禁-脚本映射配置 | `GATE_SCRIPTS_MAP` (config.py) |
| 9 | `xuansto://config/hook-scripts` | JSON | Hook-脚本映射配置 | `HOOK_SCRIPTS_MAP` (config.py) |
| 10 | `xuansto://config/phase-gates` | JSON | 阶段-门禁映射配置 | `QUALITY_GATES_PHASE_MAP` (config.py) |
| 11 | `xuansto://decisions/latest` | Markdown | 最新决策日志 | `WORK_DIR/decisions/` 下最新ADR文件 |

### 3.4 权限与安全边界

#### Tool权限分级

| 权限级别 | Tool | 说明 |
|----------|------|------|
| **只读** | skill_analyze, quality_gate_check, spec_drift_detect, security_scan, code_simplify, agent_status(list/by_phase/detail), resource_load_status(status/cache/loading_progress), context_compress, server_health | 仅读取和分析，不修改文件系统 |
| **写入** | knowledge_search(inject/precipitate), session_manage(save/track), workflow_dispatch(start/phase/abort), hook_manage(execute), resource_load_status(preload/clear_cache) | 创建或修改文件，但在受控目录内 |
| **管理** | agent_status(create/assign/release/destroy), project_init, decision_log(record) | 创建/修改实例和项目结构 |

#### 安全边界

1. **路径遍历防护**: Resource `xuansto://templates/{name}` 禁止 `/`、`\\`、`..`，且resolve后必须在TEMPLATES_DIR内
2. **命令注入防护**: hook_manage的security-block Hook拦截危险命令(rm -rf, DROP TABLE, sudo等)
3. **密钥泄露防护**: security_scan检测硬编码密钥，hook_manage的security-block Hook拦截
4. **Token预算防护**: token_budget Tool监控上下文窗口，防止溢出
5. **文件大小限制**: resource_load_status单文件最大1MB，总资源最大10MB
6. **实例数量限制**: agent_status最大20个Agent实例
7. **会话数量限制**: session_manage最多保留10个历史会话
8. **快照数量限制**: workflow_dispatch每个工作流最多20个快照，TTL 30天

### 3.5 MCP Servers配置JSON

#### UVX配置格式 (当前)

```json
{
  "mcpServers": {
    "xuansto-mcp-server": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/skiller-team/xuansto-mcp-server",
        "xuansto-mcp"
      ]
    }
  }
}
```

#### 目标配置格式 (v4.0.0)

```json
{
  "mcpServers": {
    "xuansto-mcp-server": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/skiller-team/xuansto-mcp-server@v4.0.0",
        "xuansto-mcp"
      ],
      "env": {
        "XUANSTO_SKILL_ROOT": "",
        "XUANSTO_WORK_DIR": ""
      }
    }
  }
}
```

#### 本地开发配置

```json
{
  "mcpServers": {
    "xuansto-mcp-server": {
      "command": "python",
      "args": [
        "-m",
        "xuansto_mcp.server"
      ],
      "cwd": "/path/to/xuansto-mcp-server",
      "env": {
        "XUANSTO_SKILL_ROOT": "/path/to/skill/data",
        "XUANSTO_WORK_DIR": "/path/to/project/.xuansto",
        "PYTHONPATH": "/path/to/xuansto-mcp-server/src"
      }
    }
  }
}
```

---

## 4. 渐进式加载披露与MCP关联

### 4.1 加载阶段体系

当前系统实现了4级渐进式加载阶段，由 `resource_load_status` Tool 和 `xuansto://loading/status` Resource 共同管理:

```
skeleton (阶段0) ──→ functional (阶段1) ──→ enhanced (阶段2) ──→ full (阶段3)
```

| 加载阶段 | 可用功能 | 不可用功能 | 披露说明 |
|----------|----------|------------|----------|
| **skeleton** | command_routing | command_execution, quality_gates, knowledge_search, reference_docs, agent_details, full_scripts | 骨架阶段，仅命令路由可用 |
| **functional** | command_routing, command_execution, quality_gates | knowledge_search, reference_docs, agent_details, full_scripts | 功能阶段，知识检索需推进到增强阶段 |
| **enhanced** | command_routing, command_execution, quality_gates, knowledge_search, reference_docs, agent_details | full_scripts | 增强阶段，完整脚本集需推进到完整阶段 |
| **full** | 全部功能 | 无 | 完整阶段，全部功能可用 |

### 4.2 负责加载特效资源的工具

`resource_load_status` Tool 是唯一负责加载特效资源的MCP工具，其5种action与加载的关系:

| Action | 加载职责 | 说明 |
|--------|----------|------|
| `status` | 查询加载状态 | 不触发加载，仅报告当前各资源状态(loaded/available/missing/stale/expired) |
| `preload` | **核心加载动作** | 按Phase或URI列表预加载资源到内存缓存，支持priority(critical/normal/background)和batch_mode |
| `cache` | 查询缓存状态 | 报告缓存条目、大小、过期/陈旧条目数 |
| `clear_cache` | 清除缓存 | 清除所有缓存条目，释放内存 |
| `loading_progress` | 查询加载进度 | 报告当前加载任务的进度百分比、已加载数/总数 |

### 4.3 Phase-Resource映射

9个开发阶段对应的资源映射 (`PHASE_RESOURCE_MAP`):

| Phase | 阶段名称 | 资源ID | 资源类型 | 资源路径 |
|-------|----------|--------|----------|----------|
| 0 | 初始化 | skill-config | config | .skill-config.yaml |
| 0 | 初始化 | agent-registry | reference | references/agent-registry.md |
| 0 | 初始化 | quality-gates | reference | references/quality-gates.md |
| 1 | 需求分析 | knowledge-general | knowledge | .knowledge/general/ |
| 1 | 需求分析 | brainstorm-workflow | workflow | workflows/brainstorming-workflow.md |
| 2 | 架构设计 | knowledge-patterns | knowledge | .knowledge/general/patterns/ |
| 2 | 架构设计 | sdd-tdd-full | workflow | workflows/sdd-tdd-full.md |
| 3 | 测试先行 | test-guidelines | reference | references/test-guidelines.md |
| 4 | 代码实现 | coding-standards | reference | references/coding-standards.md |
| 4 | 代码实现 | karpathy-guidelines | reference | references/karpathy-guidelines.md |
| 5 | 测试验证 | security-guidelines | reference | references/security-guidelines.md |
| 5 | 测试验证 | owasp-top10 | reference | references/owasp-top10-2026.md |
| 6 | 验收确认 | acceptance-criteria | reference | references/acceptance-criteria.md |
| 7 | 持续重构 | simplification-rules | reference | references/karpathy-guidelines.md (继承Phase 4) |
| 8 | 部署交付 | desktop-guidelines | reference | references/desktop-dev-guidelines.md |
| 8 | 部署交付 | ipc-contracts | reference | references/ipc-contracts.md |

Phase继承机制: Phase 7 继承 Phase 4 的资源(避免重复加载)。

### 4.4 加载状态暴露方式

当前系统通过两种方式暴露加载状态:

1. **Tool方式**: `resource_load_status(action="status"|"loading_progress")` - 主动查询
2. **Resource方式**: `xuansto://loading/status` - 被动读取

两种方式的数据源相同(`WORK_DIR/resource_state.json` + 运行时计算)，但Resource方式返回JSON字符串，Tool方式返回结构化dict。

### 4.5 MCP推送加载进度通知

**当前状态**: 不支持MCP推送通知。加载进度只能通过Tool主动查询(`loading_progress` action)。

**MCP协议支持**: MCP协议支持Server-to-Client通知(通过notifications机制)，但FastMCP框架当前未封装进度通知API。

**建议方案**:

```
方案A: 轮询模式(当前)
  Client → resource_load_status(action="loading_progress") → Server
  适用于: 短时加载(秒级)

方案B: MCP Notification模式(建议)
  Server在preload执行过程中，通过MCP Notification推送进度:
  - 通知类型: notifications/progress
  - 通知内容: {progressToken, progress, total}
  - 触发时机: 每个资源加载完成时
  适用于: 长时加载(分钟级)或batch_mode批量加载

方案C: 混合模式(推荐)
  - 短时加载: 轮询loading_progress
  - 长时加载(batch_mode): 注册progressToken，接收MCP Notification
  - 加载完成: 发送notifications/tools/complete
```

---

## 5. 与Skill层的交互协议

### 5.1 Skill调用MCP工具的架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Skill层 (.trae/skills/)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ SKILL.md     │  │ commands/    │  │ references/  │      │
│  │ (入口+路由)  │  │ (命令定义)   │  │ (参考文档)   │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                 │                  │              │
│         └─────────────────┼──────────────────┘              │
│                           │                                 │
│              MCP Tool Call (stdio)                           │
│                           │                                 │
└───────────────────────────┼─────────────────────────────────┘
                            │
┌───────────────────────────┼─────────────────────────────────┐
│              xuansto-mcp-server                              │
│  ┌────────────────────────┴────────────────────────┐        │
│  │           FastMCP (Tool Registry)                │        │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐        │        │
│  │  │Tool 1-13 │ │Tool 14-16│ │Resource  │        │        │
│  │  │(现有)    │ │(新增)    │ │1-11      │        │        │
│  │  └────┬─────┘ └────┬─────┘ └────┬─────┘        │        │
│  └───────┼────────────┼────────────┼───────────────┘        │
│          │            │            │                        │
│  ┌───────┴────────────┴────────────┴───────────────┐        │
│  │         Hook Interception Layer                  │        │
│  │  Pre-hooks → Tool执行 → Post-hooks              │        │
│  └───────┬─────────────────────────────────────────┘        │
│          │                                                   │
│  ┌───────┴─────────────────────────────────────────┐        │
│  │         Degradation Layer                        │        │
│  │  主逻辑 → 脚本降级 → 内嵌降级                    │        │
│  └───────┬─────────────────────────────────────────┘        │
│          │                                                   │
│  ┌───────┴─────────────────────────────────────────┐        │
│  │         Data Layer                               │        │
│  │  文件系统 / SQLite / ChromaDB / 内存缓存         │        │
│  └──────────────────────────────────────────────────┘        │
└──────────────────────────────────────────────────────────────┘
```

### 5.2 参数传递规范

#### 5.2.1 Skill → MCP Tool 调用格式

Skill层通过MCP协议调用Tool时，参数传递遵循以下规范:

```
调用格式:
  tool_name(param1=value1, param2=value2, ...)

参数类型映射:
  Skill层类型    →  MCP JSON Schema类型
  string         →  {"type": "string"}
  integer        →  {"type": "integer"}
  boolean        →  {"type": "boolean"}
  list<string>   →  {"type": "array", "items": {"type": "string"}}
  dict           →  {"type": "object"}
  enum           →  {"type": "string", "enum": [...]}
  Optional[T]    →  不加入required列表，提供default
```

#### 5.2.2 参数校验流程

```
1. Pydantic Schema校验 (SkillAnalyzeInput等13+3个Model)
   ├── 类型校验 (str/int/bool/list/dict)
   ├── 范围校验 (top_k: 1-50, target_tokens: 100-50000, phase: 0-8)
   ├── 枚举校验 (action枚举值, strategy枚举值)
   └── 额外字段拒绝 (extra="forbid")

2. 业务逻辑校验 (Tool内部)
   ├── 路径存在性检查 (PathNotFoundError)
   ├── 参数依赖检查 (inject需要content, verify需要pattern_path)
   └── 状态前置检查 (abort需要workflow_id, assign需要agent_id+task)

3. Hook前置检查 (Pre-hook)
   ├── security-block: 拦截危险命令
   ├── dangerous-cmd-confirm: 警告中等危险命令
   └── 其他Hook: 格式检查、类型检查等
```

### 5.3 结果处理规范

#### 5.3.1 统一响应格式

```json
{
  "error": false,
  "api_version": "1.0.0",
  "data": { ... },
  "degradation_level": "chromadb|sqlite_fts5|keyword_fallback|script|inline|partial|full",
  "hook_errors": [ ... ]
}
```

#### 5.3.2 Skill层结果处理流程

```
1. 检查error字段
   ├── error=true  → 提取code/message/details，执行错误处理
   └── error=false → 继续

2. 检查degradation_level
   ├── 无/undefined → 正常处理
   ├── "script"/"inline" → 记录降级，结果可能精度降低
   └── "keyword_fallback" → 记录降级，结果可能遗漏

3. 检查hook_errors
   ├── 无 → 正常处理
   └── 有 → 记录Hook错误，不影响主结果

4. 提取data字段，按Tool特定Schema处理
```

### 5.4 典型交互场景

#### 场景1: 新项目启动

```
Skill层                           MCP Server
  │                                  │
  │── project_init(init) ──────────→ │ 检测技术栈、生成骨架
  │←─ {template, workflow_id} ──────│
  │                                  │
  │── workflow_dispatch(start) ────→ │ 启动sdd-tdd-full工作流
  │←─ {workflow_id, phase:0} ──────│
  │                                  │
  │── resource_load_status(preload)→ │ 预加载Phase 0资源
  │←─ {loaded_count, progress} ────│
  │                                  │
  │── decision_log(record) ────────→ │ 记录技术选型决策
  │←─ {adr_id, path} ──────────────│
```

#### 场景2: 代码实现阶段

```
Skill层                           MCP Server
  │                                  │
  │── workflow_dispatch(phase, ────→ │ 推进到Phase 4
  │   phase_action="advance")       │ 自动检查Phase 3门禁
  │←─ {advanced, gates_checked} ───│
  │                                  │
  │── resource_load_status(preload)→ │ 预加载Phase 4资源
  │←─ {coding-standards, ...} ────│
  │                                  │
  │── code_simplify(target) ──────→ │ 分析代码简化机会
  │←─ {suggestions, quality_score}─│
  │                                  │
  │── security_scan(target) ──────→ │ 安全扫描
  │←─ {vulnerabilities, score} ───│
  │                                  │
  │── token_budget(track) ────────→ │ 记录Token消耗
  │←─ {running_total} ────────────│
```

#### 场景3: 会话恢复

```
Skill层                           MCP Server
  │                                  │
  │── session_manage(restore) ────→ │ 恢复上次追踪状态
  │←─ {current_phase, decisions} ──│
  │                                  │
  │── workflow_dispatch(status) ──→ │ 查询工作流状态
  │←─ {workflow_id, phase:4} ─────│
  │                                  │
  │── resource_load_status(status)→ │ 查询资源加载状态
  │←─ {loaded, stale, expired} ───│
  │                                  │
  │── context_compress(content) ──→ │ 压缩历史上下文
  │←─ {compressed, ratio} ────────│
```

### 5.5 Skill-MCP交互约束

| 约束 | 说明 |
|------|------|
| **串行调用** | 同一workflow_id的phase/advance操作必须串行，避免并发推进 |
| **状态一致性** | session_manage(track)和workflow_dispatch(phase/advance)应同步调用，确保阶段状态一致 |
| **降级感知** | Skill层必须处理degradation_level，在降级模式下降低对结果精度的期望 |
| **Token预算** | 长会话中应定期调用token_budget(status)，在预算不足时主动压缩 |
| **资源预加载** | 阶段推进前应先preload目标Phase资源，避免运行时延迟 |
| **错误恢复** | Tool调用失败时，Skill层应检查error.code并采取对应恢复策略(重试/降级/跳过) |
| **Hook阻塞** | Pre-hook返回block时，Skill层不应重试，应提示用户修改操作 |
| **缓存尊重** | quality_gate_check的缓存结果应被尊重，除非force_refresh=True |

---

> 本文档基于 xuansto-mcp-server v3.5.0 源码事实生成，所有数据均来自实际代码分析。
> 目标设计为v4.0.0规划，新增3个Tool和4个Resource需在后续迭代中实现。
