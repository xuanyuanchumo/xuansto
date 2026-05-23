# Xuansto Skill MCP 详细分析文档

> 版本: v4.1.0 | 日期: 2026-05-23 | 问题编号前缀: MCP-

---

## 目录

1. [现有MCP调用盘点](#1-现有mcp调用盘点)
2. [可MCP化能力识别](#2-可mcp化能力识别)
3. [目标MCP Server设计](#3-目标mcp-server设计)
4. [mcpServers配置JSON示例](#4-mcpservers配置json示例)
5. [渐进式加载与MCP的关联](#5-渐进式加载与mcp的关联)
6. [Skill→MCP交互协议](#6-skillmcp交互协议)
7. [问题清单](#7-问题清单)

---

## 1. 现有MCP调用盘点

### 1.1 Tool清单（17个）

| # | Tool名称 | 功能描述 | 核心action | 降级策略 |
|---|---------|---------|-----------|---------|
| 1 | `skill_analyze` | 分析技能项目结构、YAML元数据、Agent注册表、脚本依赖 | 单一调用 | `scripts/skill-test.py --analyze` |
| 2 | `knowledge_search` | 三层知识库混合检索（retrieve/inject/precipitate） | retrieve, inject, precipitate | ChromaDB→SQLite FTS5→keyword |
| 3 | `knowledge_inject` | 知识注入与经验沉淀 | inject, list_available, precipitate | `scripts/knowledge_server/main.py --inject` |
| 4 | `quality_gate_check` | 54项质量门禁检查 | 单一调用 | `scripts/skill-test.py --gate` → 逐门禁脚本 |
| 5 | `spec_drift_detect` | 规格文档与代码实现偏差检测 | 单一调用 | `scripts/spec-drift-detector.py` → 内联漂移检测 |
| 6 | `security_scan` | OWASP Agentic Top 10 + 依赖漏洞扫描 | 单一调用 | `scripts/agentic-security-scanner.py` → 内联agentic+dependency |
| 7 | `code_simplify` | 代码简化分析（死代码/重复/复杂度/命名） | 单一调用 | `scripts/code-simplifier.py` → 内联simplify+dedup |
| 8 | `session_manage` | 会话状态管理（save/load/list/detect/verify/track/restore） | 7种action | `scripts/init-session.py` / `session-catchup.py` / `session-persist.py` |
| 9 | `workflow_dispatch` | 工作流调度（start/status/abort/phase/recover/snapshots） | 6种action | `scripts/project-initializer.py` → 内联Phase推进 |
| 10 | `agent_status` | Agent状态查询（list/by_phase/detail/create/match/assign/release/instance_status/destroy/schedule） | 10种action | 静态注册表查询 → `scripts/skill-test.py --agents` |
| 11 | `hook_manage` | Hook管理（list/execute） | 2种action | 内联Hook执行 |
| 12 | `resource_load_status` | 渐进式加载状态管理（status/preload/cache/clear_cache/loading_progress/token_report） | 6种action | 内联状态检查 |
| 13 | `context_compress` | 上下文压缩（semantic/selective/lossless） | 单一调用 | `scripts/context-compressor.py` |
| 14 | `server_health` | 服务器健康检查与版本协商 | check, negotiate_version | `scripts/health-checker.py` → 降级状态返回 |
| 15 | `decision_log` | 决策日志管理（log/list/query/update/export/stats） | 6种action | `scripts/decision-log.py` → 内联JSON记录 |
| 16 | `token_budget` | Token预算管理（status/set_budget/recommend/report） | 4种action | `scripts/token-budget-guard.py` → 内联估算 |
| 17 | `project_init` | 项目初始化（create/validate/detect_stack） | 3种action | `scripts/project-initializer.py` → 内联模板生成 |

### 1.2 Resource清单（6个）

| # | URI | 类型 | 功能描述 | 内容类型 |
|---|-----|------|---------|---------|
| 1 | `xuansto://config/skill` | 静态 | 技能配置文件(.skill-config.yaml) | YAML文本 |
| 2 | `xuansto://references/quality-gates` | 静态 | 质量门禁参考文档 | Markdown文本 |
| 3 | `xuansto://references/agent-registry` | 静态 | Agent注册表 | Markdown文本 |
| 4 | `xuansto://references/workflow-phases` | 静态 | 工作流阶段定义 | Markdown文本 |
| 5 | `xuansto://templates/{name}` | 模板 | 模板文件（动态参数name） | Markdown文本 |
| 6 | `xuansto://sessions/latest` | 静态 | 最新会话记录 | Markdown文本 |
| 7 | `xuansto://loading/status` | 静态 | 渐进式加载状态（含当前Phase、可用功能、资源映射） | JSON |

> **注意**: `xuansto://loading/status` 虽然注册为Resource，但其返回的是JSON结构化数据，包含`current_phase`、`available_functions`、`loaded_resources`等关键状态信息，是渐进式加载机制的核心状态暴露点。

### 1.3 核心基础设施

| 模块 | 文件 | 职责 |
|------|------|------|
| Hook引擎 | `core/hook_engine.py` | Pre/Post Hook拦截、动态注册、配置文件加载 |
| 降级管理 | `core/degradation.py` | 三级降级(L1_NORMAL/L2_LOCAL_SEMANTIC/L3_BM25_ONLY)、健康监控、自动恢复 |
| 通知系统 | `core/notifications.py` | 可插拔通知回调(NotificationCallback Protocol) |
| 指标收集 | `core/metrics.py` | 工具调用延迟/成功率、降级事件、质量门禁结果、Phase转换、Token用量 |
| 验证器 | `core/validator.py` | 路径安全验证(防遍历/防绝对路径)、Pydantic输入校验 |
| 错误处理 | `core/errors.py` | 统一错误响应、重试机制(瞬态/永久错误分类)、i18n消息 |
| 配置管理 | `core/config.py` | 路径解析、YAML配置热重载(watchfiles/polling)、API版本管理 |

---

## 2. 可MCP化能力识别

### 2.1 适合封装为Tool的功能单元

以下能力目前以脚本或内联代码形式存在，具备明确的输入/输出契约，适合封装为独立MCP Tool：

| 候选Tool | 当前实现方式 | 封装理由 | 优先级 |
|----------|------------|---------|--------|
| `config_reload` | `core/config.py` 中的 `reload_config()` | 配置热重载是运维高频操作，当前无MCP入口 | 高 |
| `metrics_report` | `core/metrics.py` 中的 `MetricsCollector` | 指标查询当前仅在 `server_health` 中部分暴露，缺少独立查询接口 | 高 |
| `degradation_status` | `core/degradation.py` 中的 `DegradationManager.get_status()` | 降级状态查询当前无独立Tool入口，对可观测性至关重要 | 高 |
| `pattern_manage` | `scripts/pattern-learner.py` | 模式学习/检测/验证是经验沉淀核心，当前仅通过Hook间接调用 | 中 |
| `test_run` | `scripts/coverage-check.py` 等 | 测试执行与覆盖率检查当前散落在多个门禁脚本中 | 中 |
| `git_operation` | 多个脚本中的git操作 | Git状态检查、提交规范化当前分散在Hook和脚本中 | 低 |
| `dependency_audit` | `security_scan` 的子集 | 依赖漏洞审计可独立于安全扫描使用 | 低 |

### 2.2 适合封装为Resource的数据

| 候选Resource | URI | 数据来源 | 内容类型 | 优先级 |
|-------------|-----|---------|---------|--------|
| 降级状态 | `xuansto://degradation/status` | `DegradationManager.get_status()` | JSON | 高 |
| 指标摘要 | `xuansto://metrics/summary` | `MetricsCollector.get_system_summary()` | JSON | 高 |
| 工具注册表 | `xuansto://tools/registry` | `mcp._tool_manager._tools` | JSON | 中 |
| 决策日志 | `xuansto://decisions/latest` | `decision_log` 工具的持久化数据 | Markdown | 中 |
| Hook配置 | `xuansto://hooks/config` | `hooks/hooks.json` | JSON | 低 |
| Agent定义 | `xuansto://agents/{name}` | `agents/` 目录下的Agent定义文件 | Markdown | 低 |

### 2.3 不适合MCP化的能力

| 能力 | 原因 |
|------|------|
| 文件系统直接操作（创建/删除/移动文件） | 应由IDE/Agent直接执行，MCP仅提供检查和验证 |
| 实时代码编辑 | 需要低延迟交互，MCP的stdio传输增加不必要的开销 |
| UI渲染 | MCP协议不支持图形输出 |

---

## 3. 目标MCP Server设计

### 3.1 Server基本信息

| 属性 | 值 |
|------|-----|
| Server名称 | `xuansto-mcp-server` |
| 版本 | v4.1.0 |
| 协议 | MCP (Model Context Protocol) |
| 传输方式 | stdio |
| 入口函数 | `xuansto_mcp.server:main` |
| CLI入口 | `xuansto-cli` |
| Python版本 | >=3.10 |
| 核心依赖 | `mcp[cli]>=1.0.0`, `pydantic>=2.0.0`, `pyyaml>=6.0` |
| 可选依赖 | `chromadb>=0.4.0`, `fastapi>=0.100.0`, `sentence-transformers>=2.0.0` |
| API版本 | 2.0.0 (最低兼容 1.0.0) |

### 3.2 Tool详细设计

#### 3.2.1 skill_analyze

**描述**: 分析技能项目结构，提取YAML元数据、目录结构、Agent注册表、脚本依赖和验证问题。

**参数JSON Schema**:
```json
{
  "type": "object",
  "properties": {
    "skill_path": {
      "type": "string",
      "description": "技能根目录路径"
    },
    "include_scripts": {
      "type": "boolean",
      "default": true,
      "description": "是否分析scripts目录"
    },
    "include_agents": {
      "type": "boolean",
      "default": true,
      "description": "是否分析agents目录"
    },
    "depth": {
      "type": "string",
      "enum": ["basic", "full"],
      "default": "basic",
      "description": "分析深度"
    }
  },
  "required": ["skill_path"]
}
```

**返回值**:
```json
{
  "error": false,
  "api_version": "2.0.0",
  "data": {
    "metadata": { "name": "", "version": "", "agents_summary": "", "tags": [] },
    "structure": { "root": "", "directories": [], "file_count": 0, "total_lines": 0 },
    "agents": { "total": 0, "layers": 0, "by_layer": {} },
    "dependencies": { "mcp_server": "", "scripts": [], "python_version": "" },
    "issues": [{ "severity": "", "code": "", "message": "", "path": "" }]
  }
}
```

#### 3.2.2 knowledge_search

**描述**: 三层知识库混合检索引擎，支持retrieve/inject/precipitate三种操作。

**参数JSON Schema**:
```json
{
  "type": "object",
  "properties": {
    "action": { "type": "string", "enum": ["retrieve", "inject", "precipitate"], "default": "retrieve" },
    "query": { "type": ["string", "null"], "description": "搜索查询文本" },
    "top_k": { "type": "integer", "minimum": 1, "maximum": 50, "default": 5 },
    "search_type": { "type": "string", "enum": ["hybrid", "semantic_only", "keyword_only"], "default": "hybrid" },
    "scope": { "type": ["string", "null"], "enum": ["general", "workspace", "experience", null] },
    "min_confidence": { "type": "number", "minimum": 0.0, "maximum": 1.0, "default": 0.0 },
    "content": { "type": ["string", "null"], "description": "注入的知识内容(inject时使用)" },
    "knowledge_type": { "type": "string", "enum": ["general", "workspace", "experience"], "default": "general" },
    "metadata": { "type": ["object", "null"], "description": "附加元数据(inject时使用)" },
    "pattern_ids": { "type": ["array", "null"], "items": { "type": "string" }, "description": "模式ID列表(precipitate时使用)" }
  }
}
```

**返回值**:
```json
{
  "error": false,
  "api_version": "2.0.0",
  "data": {
    "results": [{ "id": "", "content": "", "source": "", "confidence": 0.0, "metadata": {} }],
    "total_matches": 0,
    "search_type_used": "",
    "degraded": false
  }
}
```

#### 3.2.3 knowledge_inject

**描述**: 知识注入与经验沉淀，支持inject/list_available/precipitate三种操作。

**参数JSON Schema**:
```json
{
  "type": "object",
  "properties": {
    "action": { "type": "string", "enum": ["inject", "list_available", "precipitate"], "default": "inject" },
    "topics": { "type": ["array", "null"], "items": { "type": "string" }, "description": "知识主题列表(inject时使用)" },
    "scope": { "type": "string", "enum": ["general", "workspace", "experience"], "default": "general" },
    "max_tokens": { "type": "integer", "minimum": 100, "maximum": 50000, "default": 5000 },
    "relevance_threshold": { "type": "number", "minimum": 0.0, "maximum": 1.0, "default": 0.5 },
    "category": { "type": ["string", "null"], "description": "经验分类(precipitate时使用)" },
    "title": { "type": ["string", "null"], "description": "经验标题(precipitate时使用)" },
    "content": { "type": ["string", "null"], "description": "经验内容(precipitate时使用)" },
    "tags": { "type": ["array", "null"], "items": { "type": "string" }, "description": "标签列表(precipitate时使用)" },
    "confidence": { "type": "number", "minimum": 0.0, "maximum": 1.0, "default": 0.8 }
  },
  "required": ["action"]
}
```

**返回值**: 与knowledge_search类似结构，action字段标识操作类型。

#### 3.2.4 quality_gate_check

**描述**: 54项质量门禁检查，支持按阶段过滤、按ID指定、按严重级别过滤。

**参数JSON Schema**:
```json
{
  "type": "object",
  "properties": {
    "gate_ids": { "type": ["array", "null"], "items": { "type": "string" }, "description": "要检查的门禁ID列表，为空则检查全部" },
    "phase": { "type": ["string", "null"], "description": "按阶段过滤门禁(0-8)" },
    "project_path": { "type": "string", "default": "." },
    "severity_filter": { "type": "string", "enum": ["all", "BLOCK", "WARN"], "default": "all" },
    "force_refresh": { "type": "boolean", "default": false }
  }
}
```

**返回值**:
```json
{
  "error": false,
  "api_version": "2.0.0",
  "data": {
    "gates_checked": 0,
    "gates_passed": 0,
    "gates_failed": 0,
    "results": [{ "gate_id": "", "status": "PASS|FAIL", "severity": "BLOCK|WARN", "message": "", "details": {} }],
    "phase": "",
    "can_proceed": true
  }
}
```

#### 3.2.5 spec_drift_detect

**描述**: 规格文档与代码实现偏差检测。

**参数JSON Schema**:
```json
{
  "type": "object",
  "properties": {
    "spec_dir": { "type": "string", "default": ".trae/specs" },
    "src_dir": { "type": "string", "default": "." }
  }
}
```

**返回值**:
```json
{
  "error": false,
  "api_version": "2.0.0",
  "data": {
    "total_specs": 0,
    "drifts_detected": 0,
    "drifts": [{ "spec_file": "", "spec_requirement": "", "implementation": "", "drift_type": "", "severity": "", "description": "", "suggestion": "" }],
    "coverage_pct": 0.0
  }
}
```

#### 3.2.6 security_scan

**描述**: OWASP Agentic Top 10 + 依赖漏洞扫描。

**参数JSON Schema**:
```json
{
  "type": "object",
  "properties": {
    "target": { "type": "string", "default": "." },
    "severity_threshold": { "type": "string", "enum": ["critical", "high", "medium", "low"], "default": "medium" },
    "include_agentic": { "type": "boolean", "default": true },
    "include_dependency": { "type": "boolean", "default": true }
  }
}
```

**返回值**:
```json
{
  "error": false,
  "api_version": "2.0.0",
  "data": {
    "total_findings": 0,
    "by_severity": { "critical": 0, "high": 0, "medium": 0, "low": 0 },
    "findings": [{ "id": "", "title": "", "severity": "", "category": "", "file": "", "line": 0, "description": "", "remediation": "", "references": [] }],
    "agentic_findings": 0,
    "dependency_findings": 0,
    "scan_duration_ms": 0
  }
}
```

#### 3.2.7 code_simplify

**描述**: 代码简化分析，检测死代码、重复代码、复杂度和命名问题。

**参数JSON Schema**:
```json
{
  "type": "object",
  "properties": {
    "target": { "type": "string", "description": "目标文件或目录路径" },
    "scope": { "type": "string", "enum": ["file", "dir", "recent"], "default": "recent" },
    "include_dedup": { "type": "boolean", "default": true }
  },
  "required": ["target"]
}
```

**返回值**:
```json
{
  "error": false,
  "api_version": "2.0.0",
  "data": {
    "total_suggestions": 0,
    "by_type": { "dead_code": 0, "duplication": 0, "complexity": 0, "naming": 0 },
    "suggestions": [{ "id": "", "type": "", "file": "", "line_start": 0, "line_end": 0, "description": "", "safety": "SAFE|CAUTION", "action": "", "estimated_reduction": 0 }],
    "total_lines_reducible": 0,
    "safe_count": 0,
    "caution_count": 0
  }
}
```

#### 3.2.8 session_manage

**描述**: 会话状态管理，支持7种操作。

**参数JSON Schema**:
```json
{
  "type": "object",
  "properties": {
    "action": { "type": "string", "enum": ["save", "load", "list", "detect", "verify", "track", "restore"] },
    "completed_tasks": { "type": ["array", "null"], "items": { "type": "string" } },
    "pending_tasks": { "type": ["array", "null"], "items": { "type": "string" } },
    "decisions": { "type": ["array", "null"], "items": { "type": "string" } },
    "experience": { "type": ["array", "null"], "items": { "type": "string" } },
    "error_log": { "type": ["array", "null"], "items": { "type": "string" } },
    "pattern_path": { "type": ["string", "null"] },
    "success": { "type": "boolean", "default": true },
    "current_phase": { "type": ["integer", "null"], "minimum": 0 },
    "current_task": { "type": ["string", "null"] }
  },
  "required": ["action"]
}
```

**返回值**: 根据action不同返回不同结构，均包含`action`、`session_id`、`state`等字段。

#### 3.2.9 workflow_dispatch

**描述**: 工作流调度，支持6种操作。

**参数JSON Schema**:
```json
{
  "type": "object",
  "properties": {
    "action": { "type": "string", "enum": ["start", "status", "abort", "phase", "recover", "snapshots"] },
    "workflow": { "type": ["string", "null"], "description": "工作流名称: sdd-tdd-full, sdd-tdd-medium, sdd-tdd-fast等" },
    "project_path": { "type": "string", "default": "." },
    "workflow_id": { "type": ["string", "null"] },
    "phase_action": { "type": ["string", "null"], "enum": ["advance", "current", null] },
    "snapshot_phase": { "type": ["integer", "null"] }
  },
  "required": ["action"]
}
```

**返回值**: 包含`workflow_id`、`current_phase`、`phases`数组等。

#### 3.2.10 agent_status

**描述**: Agent状态查询，支持10种操作。

**参数JSON Schema**:
```json
{
  "type": "object",
  "properties": {
    "action": { "type": "string", "enum": ["list", "by_phase", "detail", "create", "match", "assign", "release", "instance_status", "destroy", "schedule"] },
    "phase": { "type": ["integer", "null"], "minimum": 0, "maximum": 8 },
    "agent_name": { "type": ["string", "null"] },
    "agent_type": { "type": ["string", "null"] },
    "capabilities": { "type": ["array", "null"], "items": { "type": "string" } },
    "agent_id": { "type": ["string", "null"] },
    "task": { "type": ["string", "null"] }
  },
  "required": ["action"]
}
```

**返回值**: 包含`agents`数组、`total_agents`、`available_count`等。

#### 3.2.11 hook_manage

**描述**: Hook管理，支持list和execute两种操作。

**参数JSON Schema**:
```json
{
  "type": "object",
  "properties": {
    "action": { "type": "string", "enum": ["list", "execute"] },
    "profile": { "type": "string", "enum": ["minimal", "standard", "strict"], "default": "standard" },
    "hook_name": { "type": ["string", "null"] },
    "context": { "type": ["object", "null"] }
  },
  "required": ["action"]
}
```

**返回值**: list返回`hooks`数组和`total_hooks`；execute返回`result`和回调执行结果。

#### 3.2.12 resource_load_status

**描述**: 渐进式加载状态管理，支持6种操作。

**参数JSON Schema**:
```json
{
  "type": "object",
  "properties": {
    "action": { "type": "string", "enum": ["status", "preload", "cache", "clear_cache", "loading_progress", "token_report"] },
    "phase": { "type": ["integer", "null"], "minimum": 0, "maximum": 3, "description": "0=骨架, 1=功能, 2=增强, 3=完整" },
    "resource_ids": { "type": ["array", "null"], "items": { "type": "string" } },
    "resource_uris": { "type": ["array", "null"], "items": { "type": "string" } },
    "priority": { "type": "string", "enum": ["critical", "normal", "background"], "default": "normal" },
    "batch_mode": { "type": "boolean", "default": false },
    "auto_upgrade": { "type": "boolean", "default": false }
  },
  "required": ["action"]
}
```

**返回值**: 包含`resources`数组、`token_budget_used`、`token_budget_remaining`等。

#### 3.2.13 context_compress

**描述**: 上下文压缩，支持semantic/selective/lossless三种策略。

**参数JSON Schema**:
```json
{
  "type": "object",
  "properties": {
    "content": { "type": "string", "description": "待压缩的文本内容" },
    "strategy": { "type": "string", "enum": ["semantic", "selective", "lossless"], "default": "semantic" },
    "target_tokens": { "type": "integer", "minimum": 100, "maximum": 50000, "default": 2000 },
    "preserve_sections": { "type": ["array", "null"], "items": { "type": "string" } }
  },
  "required": ["content"]
}
```

**返回值**:
```json
{
  "error": false,
  "api_version": "2.0.0",
  "data": {
    "original_tokens": 0,
    "compressed_tokens": 0,
    "compression_ratio": 0.0,
    "strategy_used": "",
    "compressed_content": "",
    "preserved_sections": [],
    "quality_score": 0.0
  }
}
```

#### 3.2.14 server_health

**描述**: 服务器健康检查与版本协商。

**参数JSON Schema**:
```json
{
  "type": "object",
  "properties": {
    "action": { "type": "string", "enum": ["check", "negotiate_version"], "default": "check" },
    "client_version": { "type": ["string", "null"] }
  }
}
```

**返回值**:
```json
{
  "error": false,
  "api_version": "2.0.0",
  "data": {
    "server_status": "HEALTHY|DEGRADED|UNAVAILABLE",
    "version": "4.1.0",
    "uptime_seconds": 0,
    "tools_available": 17,
    "tools_status": {},
    "memory_usage_mb": 0.0,
    "active_workflows": 0,
    "active_sessions": 0,
    "degradation_level": "L1_NORMAL",
    "metrics_summary": {}
  }
}
```

#### 3.2.15 decision_log

**描述**: 决策日志管理，支持6种操作。

**参数JSON Schema**:
```json
{
  "type": "object",
  "properties": {
    "action": { "type": "string", "enum": ["log", "list", "query", "update", "export", "stats"] },
    "title": { "type": ["string", "null"] },
    "description": { "type": ["string", "null"] },
    "context": { "type": ["string", "null"] },
    "alternatives": { "type": ["array", "null"], "items": { "type": "string" } },
    "decision": { "type": ["string", "null"] },
    "rationale": { "type": ["string", "null"] },
    "impact": { "type": ["string", "null"] },
    "decided_by": { "type": ["string", "null"] },
    "keyword": { "type": ["string", "null"] },
    "tag": { "type": ["string", "null"] },
    "date_from": { "type": ["string", "null"] },
    "date_to": { "type": ["string", "null"] },
    "limit": { "type": "integer", "minimum": 1, "maximum": 100, "default": 20 },
    "offset": { "type": "integer", "minimum": 0, "maximum": 10000, "default": 0 },
    "format": { "type": "string", "enum": ["json", "markdown"], "default": "json" },
    "decision_id": { "type": ["string", "null"] },
    "status": { "type": ["string", "null"], "enum": ["proposed", "accepted", "deprecated", "superseded", null] }
  },
  "required": ["action"]
}
```

**返回值**: log返回`id`和`entry`；query返回`results`数组；export返回`content`。

#### 3.2.16 token_budget

**描述**: Token预算管理，支持4种操作。

**参数JSON Schema**:
```json
{
  "type": "object",
  "properties": {
    "action": { "type": "string", "enum": ["status", "set_budget", "recommend", "report"] },
    "total_budget": { "type": ["integer", "null"], "minimum": 1000 },
    "phase_allocations": { "type": ["object", "null"], "additionalProperties": { "type": "integer" } },
    "project_size": { "type": ["string", "null"], "enum": ["small", "medium", "large", null] },
    "complexity": { "type": ["string", "null"], "enum": ["low", "medium", "high", null] },
    "team_size": { "type": ["integer", "null"], "minimum": 1, "maximum": 50 },
    "period": { "type": "string", "enum": ["daily", "weekly", "session"], "default": "session" }
  },
  "required": ["action"]
}
```

**返回值**: 包含`total_budget`、`used`、`remaining`、`phase_allocations`、`usage_by_phase`等。

#### 3.2.17 project_init

**描述**: 项目初始化管理，支持3种操作。

**参数JSON Schema**:
```json
{
  "type": "object",
  "properties": {
    "action": { "type": "string", "enum": ["create", "validate", "detect_stack"] },
    "name": { "type": ["string", "null"] },
    "description": { "type": ["string", "null"] },
    "stack": { "type": ["array", "null"], "items": { "type": "string" } },
    "template": { "type": ["string", "null"] },
    "directory": { "type": ["string", "null"] },
    "project_path": { "type": ["string", "null"] }
  },
  "required": ["action"]
}
```

**返回值**: create返回`name`、`directory`、`config_path`、`stack`；validate返回`valid`、`issues`；detect_stack返回`detected_stacks`。

### 3.3 Resource详细设计

| URI | 类型 | 描述 | 内容类型 | 安全约束 |
|-----|------|------|---------|---------|
| `xuansto://config/skill` | 静态Resource | 技能配置文件内容 | `text/yaml` | 仅读取SKILL_ROOT下的配置文件 |
| `xuansto://references/quality-gates` | 静态Resource | 质量门禁参考文档 | `text/markdown` | 仅读取REFERENCES_DIR |
| `xuansto://references/agent-registry` | 静态Resource | Agent注册表 | `text/markdown` | 仅读取REFERENCES_DIR |
| `xuansto://references/workflow-phases` | 静态Resource | 工作流阶段定义 | `text/markdown` | 仅读取REFERENCES_DIR |
| `xuansto://templates/{name}` | 模板Resource | 模板文件（按名称动态获取） | `text/markdown` | 路径安全验证（防遍历/防绝对路径），限制在TEMPLATES_DIR内 |
| `xuansto://sessions/latest` | 静态Resource | 最新会话记录 | `text/markdown` | 仅读取SESSION_DIR |
| `xuansto://loading/status` | 静态Resource | 渐进式加载状态 | `application/json` | 仅读取WORK_DIR下状态文件 |

### 3.4 权限与安全边界

| 安全机制 | 实现位置 | 描述 |
|---------|---------|------|
| 路径安全验证 | `core/validator.py` | 防止路径遍历(`..`)、绝对路径、null字节注入 |
| 目录白名单 | `skill_resources.py` | Resource读取限制在SKILL_ROOT子目录内 |
| Pydantic输入校验 | `models/schemas.py` | 所有Tool输入通过Pydantic BaseModel严格校验，`extra="forbid"`拒绝未知字段 |
| Hook拦截 | `server.py` → `_with_hook_interception` | Pre-Hook可阻止危险操作（`status: "block"`） |
| 降级隔离 | `core/degradation.py` | 降级模式下不暴露完整功能，限制在安全子集内 |
| Token预算 | `token_budget` Tool | 防止资源过度消耗 |
| 脚本执行超时 | `degradation.py` → `run_script_fallback` | 默认60秒超时，安全脚本30秒 |

---

## 4. mcpServers配置JSON示例

### 4.1 uvx方式（推荐）

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

### 4.2 uvx + 本地路径方式

```json
{
  "mcpServers": {
    "xuansto-mcp-server": {
      "command": "uvx",
      "args": [
        "--from",
        "/path/to/xuansto-mcp-server",
        "xuansto-mcp"
      ]
    }
  }
}
```

### 4.3 Python直接运行方式

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
        "SKILL_ROOT": "/path/to/.trae/skills/xuansto-skill-v2",
        "XUANSTO_WORK_DIR": "/path/to/.xuansto"
      }
    }
  }
}
```

### 4.4 环境变量说明

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `SKILL_ROOT` / `XUANSTO_SKILL_ROOT` | 自动检测 `.trae/skills/xuansto-skill-v2` | 技能根目录 |
| `XUANSTO_WORK_DIR` | `{project_root}/.xuansto` | 工作目录（会话/模式/指标持久化） |

---

## 5. 渐进式加载与MCP的关联

### 5.1 四阶段加载模型

| Phase | 名称 | Token预算 | 可用功能 | 触发条件 |
|-------|------|----------|---------|---------|
| 0 | 骨架(skeleton) | ≤2K | 命令路由、核心元数据 | Skill触发时 |
| 1 | 功能(functional) | ≤5K | +命令执行、工作流推进、门禁检查、核心Agent | 用户执行命令时 |
| 2 | 增强(enhanced) | ≤10K | +知识检索、参考文档、Agent完整注册表 | 需要参考文档时 |
| 3 | 完整(full) | ≤20K | +完整脚本集、模板库、全部Agent定义 | 深度分析时 |

### 5.2 Tool在渐进式加载中的角色

| Tool | Phase 0 | Phase 1 | Phase 2 | Phase 3 |
|------|---------|---------|---------|---------|
| `skill_analyze` | ✅(basic) | ✅(basic) | ✅(full) | ✅(full) |
| `knowledge_search` | ❌ | ❌ | ✅ | ✅ |
| `knowledge_inject` | ❌ | ❌ | ✅ | ✅ |
| `quality_gate_check` | ❌ | ✅ | ✅ | ✅ |
| `spec_drift_detect` | ❌ | ❌ | ✅ | ✅ |
| `security_scan` | ❌ | ❌ | ✅ | ✅ |
| `code_simplify` | ❌ | ❌ | ❌ | ✅ |
| `session_manage` | ❌ | ✅(save/load) | ✅ | ✅ |
| `workflow_dispatch` | ❌ | ✅ | ✅ | ✅ |
| `agent_status` | ❌ | ✅(核心Agent) | ✅(完整) | ✅ |
| `hook_manage` | ❌ | ✅ | ✅ | ✅ |
| `resource_load_status` | ✅(status) | ✅ | ✅ | ✅ |
| `context_compress` | ❌ | ❌ | ✅ | ✅ |
| `server_health` | ✅ | ✅ | ✅ | ✅ |
| `decision_log` | ❌ | ✅(log) | ✅ | ✅ |
| `token_budget` | ✅(status) | ✅ | ✅ | ✅ |
| `project_init` | ❌ | ✅ | ✅ | ✅ |

### 5.3 Resource在渐进式加载中的角色

| Resource | Phase 0 | Phase 1 | Phase 2 | Phase 3 |
|----------|---------|---------|---------|---------|
| `xuansto://config/skill` | ✅ | ✅ | ✅ | ✅ |
| `xuansto://references/quality-gates` | ❌ | ✅(摘要) | ✅ | ✅ |
| `xuansto://references/agent-registry` | ❌ | ✅(核心) | ✅ | ✅ |
| `xuansto://references/workflow-phases` | ❌ | ✅ | ✅ | ✅ |
| `xuansto://templates/{name}` | ❌ | ❌ | ✅ | ✅ |
| `xuansto://sessions/latest` | ❌ | ✅ | ✅ | ✅ |
| `xuansto://loading/status` | ✅ | ✅ | ✅ | ✅ |

### 5.4 渐进式加载的MCP交互流程

```
1. Skill触发 → 调用 resource_load_status(action="status")
   ← 返回 { current_phase: "skeleton", available_functions: {...} }

2. 用户执行命令 → 调用 resource_load_status(action="preload", phase=1)
   ← 触发Phase 0→1转换，加载命令执行相关资源
   ← xuansto://loading/status 更新为 { current_phase: "functional" }

3. 需要参考文档 → 调用 resource_load_status(action="preload", phase=2)
   ← 触发Phase 1→2转换，加载知识检索和参考文档
   ← 调用 knowledge_search 检索相关知识

4. 深度分析 → 调用 resource_load_status(action="preload", phase=3)
   ← 触发Phase 2→3转换，加载完整脚本集和模板库
   ← 调用 code_simplify / security_scan 等深度分析工具
```

### 5.5 状态暴露与通知

- **状态暴露**: `xuansto://loading/status` Resource 实时反映当前Phase、已加载资源列表、可用功能映射
- **Token预算通知**: `token_budget` Tool 在预算接近上限时通过通知系统发出警告
- **降级通知**: `DegradationManager` 在组件降级时通过 `notify()` 发出通知
- **Phase转换通知**: `MetricsCollector.record_phase_transition()` 记录Phase转换事件

---

## 6. Skill→MCP交互协议

### 6.1 调用方式

Skill通过MCP协议与xuansto-mcp-server交互，遵循以下流程：

```
Skill (LLM Agent)
    │
    ├── 1. 发现工具: 列出可用Tool和Resource
    │
    ├── 2. 健康检查: server_health(action="check")
    │
    ├── 3. 状态查询: resource_load_status(action="status")
    │   └── 确定当前Phase和可用功能
    │
    ├── 4. 按需加载: resource_load_status(action="preload", phase=N)
    │   └── 推进到所需Phase
    │
    ├── 5. 调用工具: 根据任务需求调用具体Tool
    │
    └── 6. 读取资源: 通过Resource URI获取参考数据
```

### 6.2 参数传递规范

| 规则 | 说明 |
|------|------|
| 输入校验 | 所有参数通过Pydantic BaseModel校验，`extra="forbid"`拒绝多余字段 |
| 必填参数 | `action`字段为多数Tool的必填参数，`skill_path`/`target`/`content`为特定Tool必填 |
| 默认值 | 所有可选参数均有合理默认值，Skill可仅传递必要参数 |
| 类型约束 | 枚举值严格限定（如action、strategy、severity等），数值有范围约束 |
| 路径安全 | 所有路径参数经过`validate_path_safety`验证，防止遍历和绝对路径 |

### 6.3 结果处理规范

#### 成功响应

```json
{
  "error": false,
  "api_version": "2.0.0",
  "data": { ... },
  "degradation_level": "L1_NORMAL | L2_LOCAL_SEMANTIC | L3_BM25_ONLY"
}
```

#### 错误响应

```json
{
  "error": true,
  "code": "VALIDATION_ERROR | PATH_NOT_FOUND | TIMEOUT | ...",
  "message": "中文错误描述",
  "details": { ... },
  "error_code": "ERR_VALIDATION | ERR_NOT_FOUND | ERR_TIMEOUT | ...",
  "language": "zh"
}
```

#### 降级响应

```json
{
  "error": false,
  "api_version": "2.0.0",
  "data": { ..., "source": "fallback", "status": "degraded", "note": "主工具不可用，使用降级响应" },
  "degradation_level": "L2_LOCAL_SEMANTIC"
}
```

### 6.4 重试策略

| 错误类型 | 重试策略 | 最大重试次数 |
|---------|---------|------------|
| 瞬态错误(TIMEOUT/CONNECTION_ERROR/DEGRADATION/RATE_LIMITED) | 指数退避重试 | 3次 |
| 永久错误(VALIDATION_ERROR/PATH_NOT_FOUND/PERMISSION_DENIED) | 不重试，立即返回 | 0次 |
| 未知错误 | 不重试 | 0次 |

退避公式: `delay = base_delay * (2 ^ attempt)`，base_delay=1.0s

### 6.5 Hook拦截协议

```
Skill调用Tool
    │
    ├── Pre-Hook执行
    │   ├── 返回 { status: "pass" } → 继续执行
    │   ├── 返回 { status: "block", reason: "..." } → 阻止执行，返回blocked响应
    │   └── 抛出异常 → 记录hook_errors，继续执行
    │
    ├── Tool执行（含重试）
    │
    ├── Post-Hook执行
    │   └── 记录hook_errors到响应中
    │
    └── 返回最终响应（含hook_errors如有）
```

### 6.6 典型交互序列

#### 场景1: 新项目启动

```
1. server_health(action="check")
   ← { server_status: "HEALTHY", tools_available: 17 }

2. project_init(action="create", name="my-app", stack=["python", "react"])
   ← { name: "my-app", directory: "...", config_path: "..." }

3. workflow_dispatch(action="start", workflow="sdd-tdd-full", project_path=".")
   ← { workflow_id: "wf-001", current_phase: 0, phases: [...] }

4. token_budget(action="recommend", project_size="medium", complexity="high")
   ← { recommended_total: 200000, recommended_allocations: {...} }

5. token_budget(action="set_budget", total_budget=200000, phase_allocations={...})
   ← { total_budget: 200000, updated_at: "..." }
```

#### 场景2: 质量门禁检查

```
1. quality_gate_check(gate_ids=["TEST-PASS", "FILE-ENCODING"], project_path=".")
   ← { gates_checked: 2, gates_passed: 1, gates_failed: 1, can_proceed: false }

2. (修复FILE-ENCODING问题)

3. quality_gate_check(gate_ids=["FILE-ENCODING"], force_refresh=true)
   ← { gates_checked: 1, gates_passed: 1, gates_failed: 0, can_proceed: true }

4. decision_log(action="log", title="修复文件编码问题", decision="移除BOM标记", rationale="UTF-8无BOM规范要求")
   ← { id: "ADR-001", entry: {...} }
```

#### 场景3: 降级模式处理

```
1. knowledge_search(query="React最佳实践")
   ← (ChromaDB不可用，自动降级)
   ← { results: [...], search_type_used: "keyword", degraded: true, degradation_level: "L3_BM25_ONLY" }

2. server_health(action="check")
   ← { server_status: "DEGRADED", degradation_level: "L2_LOCAL_SEMANTIC", tools_status: { knowledge_search: "DEGRADED" } }

3. (等待自动恢复或手动修复ChromaDB)

4. knowledge_search(query="React最佳实践")
   ← { results: [...], search_type_used: "hybrid", degraded: false }
```

---

## 7. 问题清单

### MCP-01: Tool职责过载

**问题**: `knowledge_search` 同时承担 retrieve/inject/precipitate 三种语义不同的操作，违反单一职责原则。`agent_status` 承担10种action，包含查询(list/by_phase/detail)和变更(create/assign/release/destroy)两类截然不同的操作。

**影响**: 参数校验复杂度高，调用者容易误用，文档理解成本大。

**建议**: 考虑将变更类操作（create/assign/release/destroy）从 `agent_status` 拆分为独立的 `agent_manage` Tool；将 `knowledge_search` 的inject/precipitate拆分为独立Tool（已有 `knowledge_inject`，但 `knowledge_search` 仍保留inject/precipitate参数）。

### MCP-02: Resource与Tool功能重叠

**问题**: `xuansto://loading/status` Resource 返回的加载状态信息与 `resource_load_status(action="status")` Tool 返回的信息存在重叠。两者数据源相同（`resource_state.json`），但Resource返回简化视图，Tool返回完整视图。

**影响**: 调用者可能困惑于使用Resource还是Tool获取状态。

**建议**: 明确分工——Resource用于只读状态快照（轻量、被动读取），Tool用于交互式操作（preload/cache/token_report）。在文档中明确说明两者区别。

### MCP-03: 降级策略不统一

**问题**: 17个Tool的降级策略实现方式不一致：
- 部分Tool优先尝试脚本降级，再尝试内联实现（如 `security_scan`）
- 部分Tool仅支持脚本降级（如 `skill_analyze`）
- 部分Tool仅支持内联降级（如 `hook_manage`）
- 降级脚本路径硬编码在 `degradation.py` 中

**影响**: 维护成本高，新增Tool需要手动添加降级函数；降级脚本可能不存在导致二次失败。

**建议**: 建立统一的降级框架：MCP调用 → 脚本降级 → 内联降级 → 最小响应。降级脚本路径应从配置文件读取而非硬编码。

### MCP-04: Hook引擎缺少类型安全

**问题**: `HookEngine` 的 `register_hook` 方法接受 `hook_type: str` 参数，仅支持 "pre" 和 "post" 两种值，但使用字符串而非枚举。Hook handler的返回类型也不统一（同步返回tuple，异步返回Awaitable）。

**影响**: 容易因拼写错误导致Hook注册失败，且难以在编译期发现类型错误。

**建议**: 将 `hook_type` 改为枚举类型 `HookType`；统一Hook handler的返回类型协议。

### MCP-05: 指标系统缺少MCP暴露

**问题**: `MetricsCollector` 收集了丰富的运行时指标（工具调用延迟/成功率、降级事件、质量门禁结果、Phase转换、Token用量），但这些指标目前仅通过 `server_health` 部分暴露，缺少独立的查询接口。

**影响**: 无法按时间范围查询指标、无法获取特定Tool的详细性能数据、无法导出指标用于外部监控。

**建议**: 新增 `metrics_report` Tool，支持按Tool/时间范围/指标类型查询，支持导出为JSON/Markdown格式。同时新增 `xuansto://metrics/summary` Resource 暴露系统级指标摘要。

### MCP-06: 通知系统未与MCP协议集成

**问题**: `notifications.py` 实现了可插拔的通知回调机制，但当前仅使用 `_NullNotificationCallback`（空实现）。MCP协议支持Notification消息，但未被利用。

**影响**: 降级事件、Phase转换、Token预算超限等关键事件无法实时通知客户端。

**建议**: 实现 `MCPNotificationCallback`，通过MCP协议的Notification机制向客户端推送关键事件。需在 `server.py` 的 `main()` 中注册此回调。

### MCP-07: 配置热重载缺少MCP入口

**问题**: `core/config.py` 实现了配置热重载功能（watchfiles/polling/SIGHUP），但没有MCP Tool入口让客户端主动触发重载或查询当前配置状态。

**影响**: 运维人员无法通过MCP协议主动触发配置重载，只能依赖文件变更检测或信号。

**建议**: 新增 `config_manage` Tool，支持 `reload`（触发重载）、`status`（查询当前配置）、`validate`（验证配置文件）三种action。

### MCP-08: 版本协商机制不完整

**问题**: `server_health` 支持 `negotiate_version` action，但 `MCP_API_VERSION` 和 `MCP_MIN_SUPPORTED_VERSION` 定义在 `config.py` 中，版本兼容性检查逻辑不够健壮。`API_CHANGELOG` 仅记录了2.0.0的变更。

**影响**: 客户端可能使用不兼容的API版本，导致调用失败。

**建议**: 实现语义化版本比较逻辑，在 `negotiate_version` 中返回兼容的功能列表和降级建议。维护完整的API CHANGELOG。

### MCP-09: Resource缺少分页和过滤

**问题**: `xuansto://sessions/latest` 仅返回最新一条会话记录，无法查看历史会话。`xuansto://references/agent-registry` 返回完整注册表，无法按条件过滤。

**影响**: 大型项目中会话记录和Agent注册表可能很大，一次性加载浪费Token。

**建议**: 为Resource引入查询参数支持（MCP协议的Template Resource），如 `xuansto://sessions/{id}` 和 `xuansto://agents/{layer}/{name}`。

### MCP-10: 降级状态持久化与恢复竞态

**问题**: `DegradationManager` 在 `_persist_state` 和 `load_state` 之间可能存在竞态条件。健康监控线程在后台持续检查和降级，同时 `_persist_state` 使用 `atomic_write`，但如果Server在写入过程中崩溃，可能留下不完整的降级状态。

**影响**: Server重启后可能恢复到错误的降级级别。

**建议**: 在 `load_state` 中增加状态完整性校验（如校验和或时间戳验证），确保只加载完整的持久化状态。

### MCP-11: Tool注册依赖内部API

**问题**: `server.py` 中通过 `mcp._tool_manager._tools` 访问已注册的Tool列表和Tool Entry对象，这是FastMCP的内部API，可能在版本升级时变更。

**影响**: MCP SDK升级可能导致Tool注册和Hook拦截机制失效。

**建议**: 向FastMCP贡献公开的Tool注册表API，或在本地维护一份Tool注册映射表，避免依赖内部属性。

### MCP-12: 缺少速率限制

**问题**: 当前MCP Server没有实现速率限制机制。虽然错误码中定义了 `ERR_RATE_LIMIT`，但没有实际的限流逻辑。

**影响**: 恶意或异常客户端可能通过高频调用耗尽Server资源。

**建议**: 实现基于令牌桶或滑动窗口的速率限制，可通过配置文件设置不同Tool的调用频率上限。

### MCP-13: knowledge_search与knowledge_inject职责边界模糊

**问题**: `knowledge_search` 的Schema中包含 `action` 参数支持 `inject` 和 `precipitate`，而 `knowledge_inject` Tool专门处理这些操作。两个Tool的 `precipitate` 功能存在重叠。

**影响**: 调用者不确定应该使用哪个Tool进行知识注入和经验沉淀。

**建议**: 从 `knowledge_search` 中移除 `inject` 和 `precipitate` action，仅保留 `retrieve`。所有写入操作统一通过 `knowledge_inject` 处理。保持单一职责。

### MCP-14: context_compress的Token估算精度

**问题**: `context_compress` 的 `target_tokens` 参数期望精确的Token数量控制，但压缩后的实际Token数取决于分词器实现，当前可能使用近似估算。

**影响**: 压缩结果可能超出或远低于目标Token数，影响上下文管理精度。

**建议**: 引入可配置的分词器（tiktoken/transformers），在压缩后验证实际Token数并提供调整建议。

### MCP-15: 安全扫描缺少白名单机制

**问题**: `security_scan` 没有提供忽略特定发现的白名单机制。在大型遗留项目中，已知的安全问题可能被反复报告。

**影响**: 产生大量噪音，降低安全扫描的实用性。

**建议**: 新增 `ignore_rules` 参数或在项目配置中支持 `.xuansto-security-ignore.yaml` 文件，允许按规则ID/文件路径/严重级别忽略特定发现。
