# MCP审查文档

> 版本: 8.0.0 | 更新日期: 2026-05-25 | 编码: UTF-8 | 行尾: LF
> Skill目录: `.trae/skills/xuansto-skill-v2/`

本文档对 xuansto-skill-v2 的 MCP（Model Context Protocol）调用能力进行全面审查，涵盖现有工具盘点、可MCP化能力识别、目标MCP Server设计、渐进式加载关联以及Skill→MCP交互协议。

---

## 1. 现有MCP调用盘点

### 1.1 知识管理工具（11个）

定义位置：[mcp_server.py](../../.trae/skills/xuansto-skill-v2/scripts/knowledge_server/mcp_server.py) 的 `list_tools()` 函数。

| # | 工具名称 | 功能概述 | 权限标注 |
|---|---------|----------|----------|
| 1 | `knowledge_search` | 三层知识库检索（hybrid/semantic_only/keyword_only），支持FTS5全文检索和ChromaDB向量检索 | readOnlyHint=True, idempotentHint=True |
| 2 | `knowledge_add` | 添加知识条目，支持自动去重检测（auto_dedup），相似条目可合并或拒绝 | readOnlyHint=False, destructiveHint=False |
| 3 | `knowledge_update` | 更新知识条目内容和元数据，乐观锁版本控制，并发修改返回VERSION_CONFLICT | readOnlyHint=False, destructiveHint=False |
| 4 | `knowledge_delete` | 删除知识条目，不可逆操作，同时删除版本历史 | readOnlyHint=False, destructiveHint=True |
| 5 | `knowledge_stats` | 知识库统计：条目数/嵌入状态/引擎健康/变更检测 | readOnlyHint=True, idempotentHint=True |
| 6 | `knowledge_rollback` | 版本回滚到指定版本，当前版本保存到历史 | readOnlyHint=False, destructiveHint=True, idempotentHint=True |
| 7 | `knowledge_auto_retrieve` | 自动检索：任务类型+技术栈感知，自动检测项目技术栈并生成检索上下文 | readOnlyHint=True, idempotentHint=True |
| 8 | `knowledge_progressive_search` | 渐进式多轮检索：Token预算控制、按scope优先级搜索、结果截断与裁剪 | readOnlyHint=True, idempotentHint=True |
| 9 | `knowledge_deep_load` | 深度加载完整条目，绕过Token预算限制返回未截断内容 | readOnlyHint=True, idempotentHint=True |
| 10 | `knowledge_web_update` | Web文档搜索更新：搜索官方文档并更新/创建知识条目 | readOnlyHint=False, openWorldHint=True |
| 11 | `resource_load_status` | 渐进式加载状态查询与控制：status/preload/cache/clear_cache/loading_progress | readOnlyHint=False |

#### 知识管理工具参数与返回值详情

**knowledge_search**

```json
{
  "input": {
    "query": "string (required) - 检索文本",
    "top_k": "integer (default=5, range 1-50) - 最大返回数",
    "search_type": "enum [hybrid|semantic_only|keyword_only] (default=hybrid) - 检索策略",
    "filters": {
      "type": "array[string] - 按类型过滤",
      "category": "array[string] - 按分类过滤",
      "tags": "array[string] - 按标签过滤",
      "min_confidence": "number (0-1, default=0.0) - 最低置信度"
    }
  },
  "output": {
    "results": [{"id": "", "type": "", "category": "", "title": "", "content": "", "confidence": 0, "scope": "", "tags": []}],
    "total": 0,
    "search_strategy": "",
    "degradation_level": 0,
    "degradation_name": ""
  }
}
```

**knowledge_add**

```json
{
  "input": {
    "content": "string (required) - 知识内容文本",
    "metadata": {
      "id": "string (optional) - 自定义ID",
      "type": "string (default=unknown) - 条目类型",
      "category": "string (default=uncategorized) - 分类",
      "tags": "array[string] - 标签",
      "confidence": "number (0-1, default=0.6) - 置信度",
      "source": "string - 来源路径"
    },
    "auto_dedup": "boolean (default=true) - 自动去重"
  },
  "output": {
    "id": "",
    "status": "created|merged",
    "dedup_status": "new|duplicate_merged|duplicate_rejected",
    "similarity_score": 0
  }
}
```

**knowledge_update**

```json
{
  "input": {
    "id": "string (required) - 条目ID",
    "content": "string (optional) - 新内容",
    "metadata": {
      "type": "string",
      "category": "string",
      "tags": "array[string]",
      "confidence": "number (0-1)"
    }
  },
  "output": {
    "id": "",
    "status": "updated"
  }
}
```

**knowledge_delete**

```json
{
  "input": {
    "id": "string (required) - 条目ID"
  },
  "output": {
    "id": "",
    "status": "deleted"
  }
}
```

**knowledge_stats**

```json
{
  "input": {
    "detailed": "boolean (default=false) - 包含详细分类统计",
    "since": "string (ISO 8601) - 变更检测时间戳"
  },
  "output": {
    "total_entries": 0,
    "by_scope": {},
    "embedding": {"pending": 0, "ready": 0},
    "chroma_available": false,
    "chroma_vector_count": 0,
    "degradation_level": 0,
    "degradation_name": "",
    "embedding_level": 0,
    "embedding_level_name": "",
    "last_change_timestamp": "",
    "status_changed_since_last_check": false,
    "by_type": {},
    "by_category": {}
  }
}
```

**knowledge_rollback**

```json
{
  "input": {
    "id": "string (required) - 条目ID",
    "target_version": "integer (required, min=1) - 目标版本号"
  },
  "output": {
    "id": "",
    "status": "rolled_back",
    "target_version": 0,
    "current_version": 0
  }
}
```

**knowledge_auto_retrieve**

```json
{
  "input": {
    "task_type": "enum [bug_fix|feature|refactor|review|deploy|security] (default=feature) - 任务类型",
    "project_path": "string (required) - 项目根目录绝对路径",
    "query": "string (optional) - 覆盖自动生成的检索查询",
    "token_budget": "integer (256-8192, default=2048) - Token预算"
  },
  "output": {
    "context": "",
    "tech_stack": {},
    "task_type": "",
    "query_used": "",
    "results_count": 0,
    "degradation_level": 0,
    "degradation_name": ""
  }
}
```

**knowledge_progressive_search**

```json
{
  "input": {
    "query": "string (required) - 检索文本",
    "task_type": "enum [bug_fix|feature|refactor|review|deploy|security] (default=feature)",
    "tech_stack": {
      "languages": "array[string]",
      "frameworks": "array[string]",
      "runtimes": "array[string]"
    },
    "token_budget": "integer (256-8192, default=2048) - Token预算"
  },
  "output": {
    "results": [{"id": "", "title": "", "content": "", "scope": "", "confidence": 0, "tags": [], "_truncated": false}],
    "total": 0,
    "task_type": "",
    "search_config": {},
    "token_budget": 0,
    "pruned_entry_ids": [],
    "degradation_level": 0,
    "degradation_name": ""
  }
}
```

**knowledge_deep_load**

```json
{
  "input": {
    "entry_id": "string (required) - 条目ID"
  },
  "output": {
    "id": "",
    "title": "",
    "content": "",
    "scope": "",
    "confidence": 0,
    "tags": [],
    "type": "",
    "category": ""
  }
}
```

**knowledge_web_update**

```json
{
  "input": {
    "entry_id": "string (optional) - 已有条目ID",
    "category": "string (optional) - 技术分类",
    "tags": "array[string] (optional) - 标签"
  },
  "output": {
    "id": "",
    "status": "updated|created_pending_review|no_change|no_results|extraction_failed",
    "sources_found": 0,
    "best_source_rating": 0,
    "updated_fields": []
  }
}
```

**resource_load_status**

```json
{
  "input": {
    "action": "enum [status|preload|cache|clear_cache|loading_progress] (required)",
    "target_phase": "enum [skeleton|functional|enhanced|full] - preload目标阶段",
    "resource_ids": "array[string] - 指定资源ID"
  },
  "output": {
    "action": "",
    "current_phase": "",
    "phase_index": 0,
    "loaded_resources": [],
    "loaded_count": 0,
    "available_resources": [],
    "available_commands": [],
    "disclosure_note": "",
    "upgrade_hint": "",
    "progress": {},
    "timestamp": ""
  }
}
```

---

### 1.2 Skill工具（15个）

定义位置：[skill_tools.py](../../.trae/skills/xuansto-skill-v2/scripts/knowledge_server/skill_tools.py) 的 `get_skill_tool_definitions()` 函数。

| # | 工具名称 | 功能概述 | 权限标注 |
|---|---------|----------|----------|
| 1 | `skill_analyze` | 项目结构分析：YAML元数据、目录结构、Agent注册表、脚本依赖、问题检测 | readOnlyHint=True, idempotentHint=True |
| 2 | `quality_gate_check` | 54项质量门禁检查：按gate_ids/phase过滤，BLOCK/WARN分级 | readOnlyHint=True, idempotentHint=True |
| 3 | `spec_drift_detect` | 规格偏差检测：扫描spec目录与源码目录的匹配度，报告覆盖率和偏差 | readOnlyHint=True, idempotentHint=True |
| 4 | `security_scan` | OWASP Agentic Top 10 + 依赖漏洞扫描，支持严重度过滤 | readOnlyHint=True, idempotentHint=True, openWorldHint=True |
| 5 | `code_simplify` | 代码简化分析：死代码/重复/复杂度/命名问题，安全等级评估 | readOnlyHint=True, idempotentHint=True |
| 6 | `session_manage` | 会话状态管理：save/load/list/detect/verify/track/restore | readOnlyHint=False |
| 7 | `workflow_dispatch` | 工作流调度：start/status/abort/phase/recover/snapshots | readOnlyHint=False |
| 8 | `agent_status` | Agent状态查询：list/by_phase/detail/create/match/assign/release/instance_status/destroy/schedule | readOnlyHint=False |
| 9 | `hook_manage` | Hook管理：list/execute，支持minimal/standard/strict配置 | readOnlyHint=False |
| 10 | `context_compress` | 上下文压缩：semantic/selective/lossless三种策略 | readOnlyHint=True, idempotentHint=True |
| 11 | `server_health` | 服务器健康检查：check/version/status，版本兼容性验证 | readOnlyHint=True, idempotentHint=True |
| 12 | `decision_log` | 决策日志管理：log/query/export，支持ADR格式 | readOnlyHint=False |
| 13 | `token_budget` | Token预算管理：status/set_budget/recommend/report | readOnlyHint=False |
| 14 | `knowledge_inject` | 知识注入：inject/preview/clear，session/workflow/global三级作用域 | readOnlyHint=False |
| 15 | `project_init` | 项目初始化：create/validate/detect_stack | readOnlyHint=False |

#### Skill工具参数与返回值详情

**skill_analyze**

```json
{
  "input": {
    "skill_path": "string (required) - Skill根目录绝对路径",
    "include_scripts": "boolean (default=true) - 是否分析scripts目录",
    "include_agents": "boolean (default=true) - 是否分析agents目录",
    "depth": "enum [basic|full] (default=basic) - 分析深度"
  },
  "output": {
    "metadata": {"name": "", "version": "", "agents_summary": "", "tags": []},
    "structure": {"root": "", "directories": [], "file_count": 0, "total_lines": 0},
    "agents": {"total": 0, "layers": 0, "by_layer": {}},
    "dependencies": {"mcp_server": "", "scripts": [], "python_version": ""},
    "issues": [{"severity": "", "code": "", "message": "", "path": ""}]
  }
}
```

**quality_gate_check**

```json
{
  "input": {
    "gate_ids": "array[string] - 指定门禁ID",
    "phase": "string - 阶段编号(0-8)",
    "project_path": "string (default=.) - 项目根目录",
    "severity_filter": "enum [all|BLOCK|WARN] (default=all)",
    "force_refresh": "boolean (default=false) - 强制刷新"
  },
  "output": {
    "gates_checked": 0,
    "gates_passed": 0,
    "gates_failed": 0,
    "results": [{"gate_id": "", "status": "", "severity": "", "message": "", "details": {}}],
    "phase": "",
    "can_proceed": false
  }
}
```

**spec_drift_detect**

```json
{
  "input": {
    "spec_dir": "string (default=.trae/specs) - 规格文档目录",
    "src_dir": "string (default=.) - 源码目录"
  },
  "output": {
    "total_specs": 0,
    "drifts_detected": 0,
    "drifts": [{"spec_file": "", "spec_requirement": "", "implementation": "", "drift_type": "", "severity": "", "description": "", "suggestion": ""}],
    "coverage_pct": 0
  }
}
```

**security_scan**

```json
{
  "input": {
    "target": "string (default=.) - 扫描目标目录",
    "severity_threshold": "enum [critical|high|medium|low] (default=medium)",
    "include_agentic": "boolean (default=true) - 包含OWASP Agentic Top 10",
    "include_dependency": "boolean (default=true) - 包含依赖漏洞扫描"
  },
  "output": {
    "total_findings": 0,
    "by_severity": {"critical": 0, "high": 0, "medium": 0, "low": 0},
    "findings": [{"id": "", "title": "", "severity": "", "category": "", "file": "", "line": 0, "description": "", "remediation": "", "references": []}],
    "agentic_findings": 0,
    "dependency_findings": 0,
    "scan_duration_ms": 0
  }
}
```

**code_simplify**

```json
{
  "input": {
    "target": "string (required) - 目标文件或目录",
    "scope": "enum [file|dir|recent] (default=recent) - 扫描范围",
    "include_dedup": "boolean (default=true) - 包含重复代码检测"
  },
  "output": {
    "total_suggestions": 0,
    "by_type": {"dead_code": 0, "duplication": 0, "complexity": 0, "naming": 0},
    "suggestions": [{"id": "", "type": "", "file": "", "line_start": 0, "line_end": 0, "description": "", "safety": "", "action": "", "estimated_reduction": 0}],
    "total_lines_reducible": 0,
    "safe_count": 0,
    "caution_count": 0
  }
}
```

**session_manage**

```json
{
  "input": {
    "action": "enum [save|load|list|detect|verify|track|restore] (required)",
    "completed_tasks": "array[string] - 已完成任务(save)",
    "pending_tasks": "array[string] - 待办任务(save/track)",
    "decisions": "array[object] - 决策列表(save/track)",
    "experience": "array[object] - 经验沉淀(save)",
    "error_log": "array[string] - 错误日志(detect)",
    "pattern_path": "string - 模式文件路径(verify)",
    "success": "boolean (default=true) - 验证结果(verify)",
    "current_phase": "integer - 当前阶段(track)",
    "current_task": "string - 当前任务(track)"
  },
  "output": {
    "action": "",
    "session_id": "",
    "saved_at": "",
    "state": {}
  }
}
```

**workflow_dispatch**

```json
{
  "input": {
    "action": "enum [start|status|abort|phase|recover|snapshots] (required)",
    "workflow": "string - 工作流名称(start): sdd-tdd-full/medium/fast",
    "project_path": "string (default=.) - 项目根目录(start)",
    "workflow_id": "string - 工作流实例ID",
    "phase_action": "enum [advance|current] - 阶段操作(phase)",
    "snapshot_phase": "integer - 恢复目标阶段(recover)"
  },
  "output": {
    "action": "",
    "workflow_id": "",
    "workflow_name": "",
    "current_phase": 0,
    "phases": [{"phase": 0, "name": "", "status": ""}],
    "started_at": "",
    "aborted_at": ""
  }
}
```

**agent_status**

```json
{
  "input": {
    "action": "enum [list|by_phase|detail|create|match|assign|release|instance_status|destroy|schedule] (required)",
    "phase": "integer - 阶段编号(by_phase, 0-8)",
    "agent_name": "string - Agent名称(detail)",
    "agent_type": "string - Agent类型(create)",
    "capabilities": "array[string] - 能力列表(create/match)",
    "agent_id": "string - 实例ID(assign/release/instance_status/destroy)",
    "task": "string - 任务描述(assign)"
  },
  "output": {
    "action": "",
    "agents": [{"name": "", "layer": "", "status": "", "capabilities": [], "assigned_tasks": 0, "completed_tasks": 0, "definition_file": ""}],
    "total_agents": 0,
    "available_count": 0
  }
}
```

**hook_manage**

```json
{
  "input": {
    "action": "enum [list|execute] (required)",
    "profile": "enum [minimal|standard|strict] (default=standard)",
    "hook_name": "string - Hook名称(execute)",
    "context": "object - 执行上下文(execute)"
  },
  "output": {
    "action": "",
    "profile": "",
    "hooks": [{"name": "", "trigger": "", "pre_callbacks": [], "post_callbacks": [], "enabled": false}],
    "total_hooks": 0,
    "enabled_count": 0
  }
}
```

**context_compress**

```json
{
  "input": {
    "content": "string (required) - 待压缩文本",
    "strategy": "enum [semantic|selective|lossless] (default=semantic)",
    "target_tokens": "integer (100-50000, default=2000) - 目标Token数",
    "preserve_sections": "array[string] - 保留章节标题"
  },
  "output": {
    "original_tokens": 0,
    "compressed_tokens": 0,
    "compression_ratio": 0,
    "strategy_used": "",
    "compressed_content": "",
    "preserved_sections": [],
    "quality_score": 0
  }
}
```

**server_health**

```json
{
  "input": {
    "action": "enum [check|version|status] (default=check)",
    "include_details": "boolean (default=false) - 包含详细工具状态"
  },
  "output": {
    "status": "HEALTHY|DEGRADED|UNAVAILABLE",
    "version": "",
    "api_version": "",
    "uptime_seconds": 0,
    "tools_available": 0,
    "degradation_level": "",
    "last_check_timestamp": "",
    "tools_status": {},
    "memory_usage_mb": 0,
    "active_workflows": 0,
    "active_sessions": 0
  }
}
```

**decision_log**

```json
{
  "input": {
    "action": "enum [log|query|export] (required)",
    "title": "string - 决策标题(log)",
    "description": "string - 决策描述(log)",
    "context": "string - 决策上下文(log)",
    "alternatives": "array[string] - 备选方案(log)",
    "decision": "string - 最终决策(log)",
    "rationale": "string - 决策理由(log)",
    "impact": "string - 影响范围(log)",
    "decided_by": "string - 决策者(log)",
    "keyword": "string - 搜索关键词(query)",
    "tag": "string - 标签过滤(query)",
    "date_from": "string (ISO8601) - 起始日期(query/export)",
    "date_to": "string (ISO8601) - 结束日期(query/export)",
    "limit": "integer (1-100, default=20) - 结果限制(query)",
    "format": "enum [json|markdown] (default=json) - 导出格式(export)"
  },
  "output": {
    "action": "",
    "id": "",
    "entry": {},
    "results": [],
    "total_decisions": 0,
    "format": "",
    "content": ""
  }
}
```

**token_budget**

```json
{
  "input": {
    "action": "enum [status|set_budget|recommend|report] (required)",
    "total_budget": "integer (>=1000) - 总预算(set_budget)",
    "phase_allocations": "object - 阶段分配(set_budget)",
    "project_size": "enum [small|medium|large] - 项目规模(recommend)",
    "complexity": "enum [low|medium|high] - 复杂度(recommend)",
    "team_size": "integer (1-50) - 团队规模(recommend)",
    "period": "enum [daily|weekly|session] (default=session) - 报告周期(report)"
  },
  "output": {
    "action": "",
    "total_budget": 0,
    "used": 0,
    "remaining": 0,
    "phase_allocations": {},
    "usage_by_phase": {}
  }
}
```

**knowledge_inject**

```json
{
  "input": {
    "action": "enum [inject|preview|clear] (required)",
    "content": "string - 注入内容(inject)",
    "scope": "enum [session|workflow|global] (default=session) - 作用域",
    "source": "string - 知识来源标识",
    "priority": "enum [low|normal|high] (default=normal) - 优先级"
  },
  "output": {
    "action": "",
    "scope": "",
    "injected_tokens": 0,
    "source": "",
    "priority": "",
    "context_window_usage_pct": 0
  }
}
```

**project_init**

```json
{
  "input": {
    "action": "enum [create|validate|detect_stack] (required)",
    "name": "string - 项目名称(create)",
    "description": "string - 项目描述(create)",
    "stack": "array[string] - 技术栈(create)",
    "template": "string - 项目模板(create)",
    "directory": "string - 项目目录(create)",
    "project_path": "string - 项目路径(validate/detect_stack)"
  },
  "output": {
    "action": "",
    "name": "",
    "directory": "",
    "config_path": "",
    "stack": [],
    "template": "",
    "valid": false,
    "issues": [],
    "detected_stacks": []
  }
}
```

---

## 2. 可MCP化能力识别

### 2.1 适合封装为Tool的功能单元

以下功能已通过 `mcp_server.py` 和 `skill_tools.py` 完整封装为MCP Tool，共计26个。所有工具均具备完整的 `inputSchema`、`outputSchema` 和 `ToolAnnotations`。

| 分类 | 工具 | 输入 | 输出 | 封装状态 |
|------|------|------|------|----------|
| 知识检索 | knowledge_search | query, top_k, search_type, filters | results, total, search_strategy, degradation | ✅ 已封装 |
| 知识检索 | knowledge_auto_retrieve | task_type, project_path, query, token_budget | context, tech_stack, results_count | ✅ 已封装 |
| 知识检索 | knowledge_progressive_search | query, task_type, tech_stack, token_budget | results, total, pruned_entry_ids | ✅ 已封装 |
| 知识检索 | knowledge_deep_load | entry_id | id, title, content, scope, confidence | ✅ 已封装 |
| 知识写入 | knowledge_add | content, metadata, auto_dedup | id, status, dedup_status | ✅ 已封装 |
| 知识写入 | knowledge_update | id, content, metadata | id, status | ✅ 已封装 |
| 知识写入 | knowledge_delete | id | id, status | ✅ 已封装 |
| 知识写入 | knowledge_rollback | id, target_version | id, status, target_version, current_version | ✅ 已封装 |
| 知识写入 | knowledge_web_update | entry_id, category, tags | id, status, sources_found | ✅ 已封装 |
| 知识元数据 | knowledge_stats | detailed, since | total_entries, by_scope, embedding, degradation | ✅ 已封装 |
| 知识注入 | knowledge_inject | action, content, scope, source, priority | injected_tokens, context_window_usage_pct | ✅ 已封装 |
| 加载控制 | resource_load_status | action, target_phase, resource_ids | current_phase, loaded_resources, disclosure_note | ✅ 已封装 |
| 项目分析 | skill_analyze | skill_path, include_scripts, include_agents, depth | metadata, structure, agents, dependencies, issues | ✅ 已封装 |
| 质量保障 | quality_gate_check | gate_ids, phase, project_path, severity_filter | gates_checked, gates_passed, can_proceed | ✅ 已封装 |
| 质量保障 | spec_drift_detect | spec_dir, src_dir | total_specs, drifts, coverage_pct | ✅ 已封装 |
| 安全扫描 | security_scan | target, severity_threshold, include_agentic, include_dependency | total_findings, by_severity, findings | ✅ 已封装 |
| 代码优化 | code_simplify | target, scope, include_dedup | total_suggestions, by_type, suggestions | ✅ 已封装 |
| 会话管理 | session_manage | action, completed_tasks, pending_tasks, decisions | session_id, saved_at, state | ✅ 已封装 |
| 工作流 | workflow_dispatch | action, workflow, project_path, workflow_id | workflow_id, current_phase, phases | ✅ 已封装 |
| Agent管理 | agent_status | action, phase, agent_name, capabilities | agents, total_agents, available_count | ✅ 已封装 |
| Hook管理 | hook_manage | action, profile, hook_name, context | hooks, total_hooks, enabled_count | ✅ 已封装 |
| 上下文 | context_compress | content, strategy, target_tokens, preserve_sections | compressed_content, compression_ratio, quality_score | ✅ 已封装 |
| 健康检查 | server_health | action, include_details | status, version, tools_available | ✅ 已封装 |
| 决策日志 | decision_log | action, title, alternatives, decision, rationale | id, entry, results, total_decisions | ✅ 已封装 |
| Token预算 | token_budget | action, total_budget, phase_allocations, project_size | total_budget, used, remaining, phase_allocations | ✅ 已封装 |
| 项目初始化 | project_init | action, name, stack, template, directory | name, directory, config_path, stack | ✅ 已封装 |

### 2.2 适合封装为Resource的数据

当前MCP Server **未暴露任何Resource**，仅通过Tool提供数据访问。以下为建议新增的Resource：

| URI模式 | 描述 | 内容类型 | 加载阶段 | 数据来源 |
|---------|------|----------|----------|----------|
| `xuansto://agents/{name}` | 单个Agent的完整定义（Markdown内容） | `text/markdown` | Phase 2+ | `agents/{layer}/{name}.md` |
| `xuansto://knowledge/stats` | 知识库实时统计快照 | `application/json` | Phase 1+ | `knowledge_stats` 工具返回值 |
| `xuansto://loading/status` | 渐进式加载当前状态 | `application/json` | Phase 0+ | `ProgressiveLoader._state` |

#### Resource详细设计

**xuansto://agents/{name}**

- 描述：按Agent名称获取完整Agent定义文件内容
- URI参数：`{name}` 为Agent文件名（不含扩展名），如 `backend-developer`、`qa-engineer`
- 内容类型：`text/markdown`
- 可用阶段：Phase 2 (Enhanced) 及以上
- 实现方式：读取 `agents/{layer}/{name}.md` 文件内容
- 示例：`xuansto://agents/backend-developer` → 返回 `agents/engineering/backend-developer.md` 的完整内容

**xuansto://knowledge/stats**

- 描述：知识库实时统计信息，包含条目数、嵌入状态、引擎健康度
- 内容类型：`application/json`
- 可用阶段：Phase 1 (Functional) 及以上
- 实现方式：调用 `knowledge_stats(detailed=false)` 并返回结果
- 示例返回值：

```json
{
  "total_entries": 42,
  "by_scope": {"general": 15, "workspace": 20, "experience": 7},
  "embedding": {"pending": 3, "ready": 39},
  "chroma_available": true,
  "degradation_level": 0,
  "degradation_name": "full",
  "last_change_timestamp": "2026-05-25T08:30:00+00:00"
}
```

**xuansto://loading/status**

- 描述：渐进式加载状态，包含当前阶段、已加载资源、可用命令
- 内容类型：`application/json`
- 可用阶段：Phase 0 (Skeleton) 及以上
- 实现方式：读取 `ProgressiveLoader._state` 并格式化
- 示例返回值：

```json
{
  "current_phase": "functional",
  "phase_index": 1,
  "loaded_resources": ["skill-config", "command-list", "mcp-dependency", "core-constraints", "execution-entry"],
  "loaded_count": 5,
  "available_commands": ["/init", "/brainstorm", "/plan", "/implement"],
  "disclosure_note": "当前处于功能阶段，命令执行和工作流概览可用。",
  "upgrade_hint": "请求参考文档或查询Agent详情可推进到增强阶段。"
}
```

---

## 3. 目标MCP Server设计

### 3.1 Server基本信息

| 属性 | 值 |
|------|-----|
| Server名称 | `xuansto-mcp-server` |
| 描述 | 多Agent自主开发编排引擎的MCP工具集 |
| 版本 | 8.0.0 (Skill) / 4.0.0 (MCP Server) / 3.0.0 (API) |
| 协议 | Model Context Protocol (MCP) |
| 传输方式 | stdio |
| 依赖 | Python >=3.10, mcp SDK |

### 3.2 Tool列表（26个）

| # | 名称 | 描述 | readOnlyHint | destructiveHint | idempotentHint | openWorldHint |
|---|------|------|:---:|:---:|:---:|:---:|
| 1 | knowledge_search | 三层知识库检索 | ✅ | ❌ | ✅ | ❌ |
| 2 | knowledge_add | 添加知识条目（自动去重） | ❌ | ❌ | ❌ | ❌ |
| 3 | knowledge_update | 更新知识条目（乐观锁版本控制） | ❌ | ❌ | ❌ | ❌ |
| 4 | knowledge_delete | 删除知识条目（不可逆） | ❌ | ✅ | ❌ | ❌ |
| 5 | knowledge_stats | 知识库统计 | ✅ | ❌ | ✅ | ❌ |
| 6 | knowledge_rollback | 版本回滚 | ❌ | ✅ | ✅ | ❌ |
| 7 | knowledge_auto_retrieve | 自动检索（任务类型+技术栈感知） | ✅ | ❌ | ✅ | ❌ |
| 8 | knowledge_progressive_search | 渐进式多轮检索（Token预算控制） | ✅ | ❌ | ✅ | ❌ |
| 9 | knowledge_deep_load | 深度加载完整条目 | ✅ | ❌ | ✅ | ❌ |
| 10 | knowledge_web_update | Web文档搜索更新 | ❌ | ❌ | ❌ | ✅ |
| 11 | resource_load_status | 渐进式加载状态查询与控制 | ❌ | ❌ | ❌ | ❌ |
| 12 | skill_analyze | 项目结构分析 | ✅ | ❌ | ✅ | ❌ |
| 13 | quality_gate_check | 54项质量门禁检查 | ✅ | ❌ | ✅ | ❌ |
| 14 | spec_drift_detect | 规格偏差检测 | ✅ | ❌ | ✅ | ❌ |
| 15 | security_scan | OWASP+依赖扫描 | ✅ | ❌ | ✅ | ✅ |
| 16 | code_simplify | 代码简化分析 | ✅ | ❌ | ✅ | ❌ |
| 17 | session_manage | 会话状态管理 | ❌ | ❌ | ❌ | ❌ |
| 18 | workflow_dispatch | 工作流调度 | ❌ | ❌ | ❌ | ❌ |
| 19 | agent_status | Agent状态查询 | ❌ | ❌ | ❌ | ❌ |
| 20 | hook_manage | Hook管理 | ❌ | ❌ | ❌ | ❌ |
| 21 | context_compress | 上下文压缩 | ✅ | ❌ | ✅ | ❌ |
| 22 | server_health | 服务器健康检查 | ✅ | ❌ | ✅ | ❌ |
| 23 | decision_log | 决策日志管理 | ❌ | ❌ | ❌ | ❌ |
| 24 | token_budget | Token预算管理 | ❌ | ❌ | ❌ | ❌ |
| 25 | knowledge_inject | 知识注入 | ❌ | ❌ | ❌ | ❌ |
| 26 | project_init | 项目初始化 | ❌ | ❌ | ❌ | ❌ |

### 3.3 Resource列表（3个新增）

| # | URI | 描述 | 内容类型 | 可用阶段 |
|---|-----|------|----------|----------|
| 1 | `xuansto://agents/{name}` | Agent完整定义 | `text/markdown` | Phase 2+ |
| 2 | `xuansto://knowledge/stats` | 知识库统计快照 | `application/json` | Phase 1+ |
| 3 | `xuansto://loading/status` | 加载状态 | `application/json` | Phase 0+ |

### 3.4 权限与安全边界

所有26个工具均通过 `ToolAnnotations` 标注了安全边界信息：

| 标注 | 含义 | 工具数量 | 工具列表 |
|------|------|---------|----------|
| `readOnlyHint=True` | 只读操作，不修改任何状态 | 10 | knowledge_search, knowledge_stats, knowledge_auto_retrieve, knowledge_progressive_search, knowledge_deep_load, skill_analyze, quality_gate_check, spec_drift_detect, security_scan, code_simplify, context_compress, server_health |
| `destructiveHint=True` | 破坏性操作，不可逆 | 2 | knowledge_delete, knowledge_rollback |
| `idempotentHint=True` | 幂等操作，重复调用结果一致 | 12 | knowledge_search, knowledge_stats, knowledge_auto_retrieve, knowledge_progressive_search, knowledge_deep_load, knowledge_rollback, skill_analyze, quality_gate_check, spec_drift_detect, security_scan, code_simplify, context_compress, server_health |
| `openWorldHint=True` | 访问外部网络资源 | 2 | knowledge_web_update, security_scan |

#### 安全措施

1. **敏感内容过滤**：`knowledge_add` 和 `knowledge_update` 调用 `SensitiveContentFilter.check()` 检测API密钥、密码等敏感信息
2. **输入验证**：`knowledge_add` 调用 `InputValidator.validate_all()` 进行输入合法性校验
3. **乐观锁控制**：`knowledge_update` 通过版本号检测并发修改，返回 `VERSION_CONFLICT` 错误
4. **破坏性操作标记**：`knowledge_delete` 和 `knowledge_rollback` 标记为 `destructiveHint=True`，Host端可要求用户确认
5. **外部访问标记**：`knowledge_web_update` 和 `security_scan` 标记为 `openWorldHint=True`，Host端可限制网络访问

### 3.5 mcpServers配置JSON示例

**uvx方式（推荐）**

```json
{
  "mcpServers": {
    "xuansto-mcp-server": {
      "command": "uvx",
      "args": [
        "xuansto-mcp-server@>=4.0.0",
        "--skill-root",
        ".trae/skills/xuansto-skill-v2"
      ],
      "env": {
        "XUANSTO_KB_PATH": ".trae/skills/xuansto-skill-v2/.knowledge",
        "XUANSTO_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

**npx方式**

```json
{
  "mcpServers": {
    "xuansto-mcp-server": {
      "command": "npx",
      "args": [
        "-y",
        "xuansto-mcp-server@>=4.0.0",
        "--skill-root",
        ".trae/skills/xuansto-skill-v2"
      ],
      "env": {
        "XUANSTO_KB_PATH": ".trae/skills/xuansto-skill-v2/.knowledge",
        "XUANSTO_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

**Python直接运行方式**

```json
{
  "mcpServers": {
    "xuansto-mcp-server": {
      "command": "python",
      "args": [
        "-m",
        "knowledge_server",
        "--skill-root",
        ".trae/skills/xuansto-skill-v2"
      ],
      "cwd": ".trae/skills/xuansto-skill-v2/scripts",
      "env": {
        "XUANSTO_KB_PATH": ".trae/skills/xuansto-skill-v2/.knowledge",
        "XUANSTO_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

---

## 4. 渐进式加载与MCP的关联

### 4.1 加载阶段体系

渐进式加载系统定义了四个阶段，由 `resource_load_status` 工具负责管理：

| 阶段 | 名称 | Token预算 | 加载内容 | 对应工具可用性 |
|------|------|----------|----------|---------------|
| Phase 0 | 骨架 (Skeleton) | ~2K | 核心约束 + 命令概要 + Agent索引 | resource_load_status, server_health |
| Phase 1 | 功能 (Functional) | ~5K | 命令详细步骤 + 工作流Phase + MCP工具参数 | + knowledge_search, knowledge_stats, workflow_dispatch, agent_status(list), session_manage, project_init |
| Phase 2 | 增强 (Enhanced) | ~10K | 参考文档 + 模板 + 知识库索引 | + knowledge_auto_retrieve, knowledge_progressive_search, knowledge_deep_load, quality_gate_check, spec_drift_detect, decision_log, token_budget, knowledge_inject |
| Phase 3 | 完整 (Full) | ~20K | 全部资源 + 脚本集 + 披露资源 | + knowledge_add, knowledge_update, knowledge_delete, knowledge_rollback, knowledge_web_update, security_scan, code_simplify, hook_manage, context_compress, skill_analyze |

### 4.2 resource_load_status工具职责

`resource_load_status` 是渐进式加载的核心控制工具，负责：

| Action | 职责 | 对加载阶段的影响 |
|--------|------|-----------------|
| `status` | 查询当前加载状态、可用资源、可用命令 | 不变 |
| `preload` | 预加载指定阶段资源 | 推进到目标阶段 |
| `cache` | 查询缓存状态 | 不变 |
| `clear_cache` | 清理缓存 | 降级到SKELETON |
| `loading_progress` | 查询各资源加载进度 | 不变 |

### 4.3 工具可用性受加载阶段控制

每个MCP工具的可用性受当前加载阶段控制。当工具在当前阶段不可用时，调用将返回降级结果或错误提示：

| 加载阶段 | 可用工具 | 不可用工具的降级行为 |
|----------|---------|---------------------|
| SKELETON | resource_load_status, server_health | 其他工具返回"当前阶段不可用"提示，建议执行preload |
| FUNCTIONAL | + 知识检索类(只读)、工作流、会话、Agent查询 | 写入类工具不可用 |
| ENHANCED | + 质量门禁、偏差检测、决策日志、Token预算、知识注入 | 破坏性操作不可用 |
| FULL | 全部26个工具 | 无 |

### 4.4 工具调用时自动推进加载阶段

当用户调用某个工具时，系统会自动检测该工具所需的最小加载阶段，并在必要时自动推进：

```
用户调用 knowledge_progressive_search
  → 检测到需要 Phase 2 (Enhanced)
  → 自动调用 resource_load_status(preload, target_phase=enhanced)
  → 加载 Phase 2 资源
  → 执行 knowledge_progressive_search
```

自动推进规则：

| 触发工具 | 自动推进到 | 条件 |
|----------|-----------|------|
| 任意命令路由匹配 | FUNCTIONAL | 当前为SKELETON |
| knowledge_auto_retrieve | ENHANCED | 当前为FUNCTIONAL |
| knowledge_progressive_search | ENHANCED | 当前为FUNCTIONAL |
| quality_gate_check | ENHANCED | 当前为FUNCTIONAL |
| security_scan | FULL | 当前为ENHANCED |
| knowledge_delete | FULL | 当前为ENHANCED |
| code_simplify | FULL | 当前为ENHANCED |

### 4.5 Token预算与阶段降级

当Token使用率超过阈值时，渐进式加载系统自动降级：

| Token使用率 | 降级动作 | 披露通知 |
|------------|----------|----------|
| > 80% | FULL → ENHANCED，释放P3资源 | 必须通知用户 |
| > 95% | ENHANCED → FUNCTIONAL，释放P2资源 | 必须通知用户 |
| > 95% 且无活动 > 5分钟 | FUNCTIONAL → SKELETON，释放P1资源 | 必须通知用户 |

---

## 5. Skill→MCP交互协议

### 5.1 调用方式：Skill命令→MCP工具调用链

Skill命令通过SKILL.md中的路由规则映射到MCP工具调用链。每个命令可能触发一个或多个MCP工具的顺序调用：

| Skill命令 | MCP工具调用链 | 说明 |
|-----------|-------------|------|
| `/init` | project_init(create) → skill_analyze → knowledge_search → workflow_dispatch(start) | 项目初始化全流程 |
| `/brainstorm` | knowledge_search → workflow_dispatch(start) | 头脑风暴启动 |
| `/plan` | skill_analyze → knowledge_search → agent_status(list) → workflow_dispatch(start) → decision_log(log) → token_budget(recommend) | 规划阶段 |
| `/spec` | workflow_dispatch(phase) → quality_gate_check → spec_drift_detect | 规格编写 |
| `/design` | quality_gate_check → knowledge_search → workflow_dispatch(phase) | 架构设计 |
| `/implement` | workflow_dispatch(phase) → quality_gate_check → hook_manage(list) | 代码实现 |
| `/test` | quality_gate_check → workflow_dispatch(phase) | 测试验证 |
| `/review` | quality_gate_check → security_scan → code_simplify | 代码审查 |
| `/audit` | security_scan → quality_gate_check → spec_drift_detect | 安全审计 |
| `/fix` | session_manage(load) → quality_gate_check → hook_manage(list) | 问题修复 |
| `/simplify` | code_simplify → quality_gate_check → context_compress | 代码简化 |
| `/refactor` | code_simplify → quality_gate_check → context_compress | 代码重构 |
| `/deploy` | quality_gate_check → server_health(check) → workflow_dispatch(phase) | 部署交付 |
| `/learn` | knowledge_search → knowledge_inject → session_manage(save) | 知识学习 |
| `/loop` | workflow_dispatch(start) → session_manage(save) → resource_load_status(status) → token_budget(status) → decision_log(log) | 循环开发 |
| `/sprint` | workflow_dispatch(start) → session_manage(save) → resource_load_status(preload) → token_budget(recommend) → project_init(detect_stack) | 冲刺开发 |

### 5.2 参数传递：命令参数→MCP工具参数映射

Skill命令的参数通过以下规则映射到MCP工具参数：

| 映射规则 | 源（Skill命令参数） | 目标（MCP工具参数） | 示例 |
|----------|-------------------|-------------------|------|
| 直接映射 | 命令参数名与工具参数名一致 | 直接传递 | `project_path` → `project_path` |
| 语义映射 | 命令参数名与工具参数名不同 | 按语义转换 | `--stack` → `stack` (project_init) |
| 默认值填充 | 命令未提供参数 | 使用工具默认值 | `top_k` 未指定 → 默认5 |
| 上下文注入 | 从会话状态获取 | 自动注入 | `workflow_id` 从当前会话获取 |
| 环境推断 | 从项目环境推断 | 自动检测 | `project_path` → 当前工作目录 |

#### 参数映射示例

**`/init --name my-project --stack python,react`**

```
project_init:
  action: "create"
  name: "my-project"          ← 直接映射
  stack: ["python", "react"]  ← 逗号分隔→数组
  directory: "my-project"     ← 默认值=name

skill_analyze:
  skill_path: ".trae/skills/xuansto-skill-v2"  ← 环境推断
  depth: "basic"              ← 默认值

knowledge_search:
  query: "python react project setup best practices"  ← 语义映射
  top_k: 5                    ← 默认值
  search_type: "hybrid"       ← 默认值

workflow_dispatch:
  action: "start"             ← 命令固定
  workflow: "sdd-tdd-full"    ← 默认值
  project_path: "."           ← 环境推断
```

### 5.3 结果处理：MCP工具返回值→Skill输出格式化

MCP工具的返回值统一包装为以下JSON结构：

```json
{
  "status": "ok|conflict|error",
  "data": { ... },
  "metadata": {
    "tool": "tool_name",
    "latency_ms": 0,
    "degraded": false,
    "fallback_method": null
  }
}
```

#### 结果处理流程

```
MCP工具返回值
  ↓
1. 解包 make_response/make_error_response
  ↓
2. 提取 data 字段
  ↓
3. 格式化为Skill输出
  ├── 成功：格式化关键信息 + 可操作建议
  ├── 降级：添加降级提示 + 替代方案
  └── 错误：错误码 + 错误描述 + 恢复建议
```

#### 结果格式化示例

**knowledge_search 返回值 → Skill输出**

```
MCP返回:
{
  "status": "ok",
  "data": {
    "results": [
      {"id": "entry-1", "title": "React Hooks", "content": "...", "confidence": 0.92}
    ],
    "total": 1,
    "search_strategy": "hybrid",
    "degradation_level": 0
  }
}

Skill输出:
🔍 知识检索完成 (策略: hybrid, 引擎: 完整)
  找到 1 条匹配结果:
  1. [0.92] React Hooks - ...
  💡 使用 knowledge_deep_load(entry_id="entry-1") 查看完整内容
```

**quality_gate_check 返回值 → Skill输出**

```
MCP返回:
{
  "status": "ok",
  "data": {
    "gates_checked": 5,
    "gates_passed": 4,
    "gates_failed": 1,
    "can_proceed": false,
    "results": [
      {"gate_id": "TEST-PASS", "status": "FAIL", "severity": "BLOCK", "message": "测试未通过"}
    ]
  }
}

Skill输出:
🚧 质量门禁检查: 4/5 通过 (❌ 不可继续)
  ❌ BLOCK: TEST-PASS - 测试未通过
  ⚠️ 请修复BLOCK门禁后再继续
```

#### 错误码映射

| MCP错误码 | 数值 | Skill输出 | 恢复建议 |
|-----------|------|----------|----------|
| PARSE_ERROR | -32700 | 请求解析失败 | 检查参数格式 |
| INVALID_REQUEST | -32600 | 无效请求 | 检查必填参数 |
| METHOD_NOT_FOUND | -32601 | 未知工具 | 检查工具名称 |
| INVALID_PARAMS | -32602 | 参数无效 | 检查参数类型和范围 |
| INTERNAL_ERROR | -32603 | 内部错误 | 重试或降级为脚本调用 |
| VALIDATION_ERROR | -32100 | 输入验证失败 | 修正输入内容 |
| NOT_FOUND | -32102 | 资源不存在 | 检查ID是否正确 |
| VERSION_CONFLICT | -32103 | 版本冲突 | 重新获取最新版本后重试 |
| SENSITIVE_CONTENT | -32106 | 包含敏感信息 | 移除API密钥/密码等 |

---

## 附录A：工具-脚本降级映射表

当MCP Server不可用时，工具自动降级为脚本或内嵌逻辑：

| MCP工具 | 降级脚本 | 降级方式 |
|---------|----------|----------|
| knowledge_search | scripts/knowledge-server.py --search | Python脚本 |
| knowledge_add | scripts/knowledge-server.py --add | Python脚本 |
| knowledge_update | scripts/knowledge-server.py --update | Python脚本 |
| knowledge_delete | scripts/knowledge-server.py --delete | Python脚本 |
| skill_analyze | scripts/skill-test.py --analyze | Python脚本 |
| quality_gate_check | scripts/skill-test.py --gate | Python脚本 |
| spec_drift_detect | 内联漂移检测逻辑 | 内嵌逻辑 |
| security_scan | scripts/agentic-security-scanner.py | Python脚本 |
| code_simplify | scripts/code-simplifier.py | Python脚本 |
| session_manage | scripts/init-session.py | Python脚本 |
| workflow_dispatch | 内联Phase推进逻辑 | 内嵌逻辑 |
| agent_status | 静态注册表查询(agents/) | 文件系统 |
| hook_manage | 内联Hook配置读取 | 内嵌逻辑 |
| resource_load_status | 内联状态检查(resource_state.json) | 文件系统 |
| context_compress | scripts/context-compressor.py | Python脚本 |
| server_health | scripts/health-checker.py | Python脚本 |
| decision_log | 内联JSON记录 | 内嵌逻辑 |
| token_budget | 内联估算逻辑 | 内嵌逻辑 |
| knowledge_inject | 内联注入逻辑 | 内嵌逻辑 |
| project_init | scripts/project-initializer.py | Python脚本 |

## 附录B：版本兼容矩阵

| Skill版本 | 最低MCP Server版本 | API版本 | 工具数量 | 新增工具 |
|-----------|-------------------|---------|---------|----------|
| 8.0.0 | 4.0.0 | 3.0.0 | 26 | knowledge_inject, project_init, knowledge_progressive_search, knowledge_deep_load, knowledge_web_update, resource_load_status, skill_analyze, quality_gate_check, spec_drift_detect, security_scan, code_simplify, session_manage, workflow_dispatch, agent_status, hook_manage, context_compress, server_health, decision_log, token_budget |
| 7.0.0 | 3.5.0 | 2.0.0 | 15 | server_health, decision_log, token_budget |
| 6.0.0 | 3.0.0 | 1.0.0 | 13 | 基础工具集 |

## 附录C：错误码完整列表

### MCP标准错误码

| 错误码 | 数值 | 描述 |
|--------|------|------|
| PARSE_ERROR | -32700 | JSON解析失败 |
| INVALID_REQUEST | -32600 | 请求对象无效 |
| METHOD_NOT_FOUND | -32601 | 方法/工具不存在 |
| INVALID_PARAMS | -32602 | 参数无效 |
| INTERNAL_ERROR | -32603 | 服务器内部错误 |

### 应用错误码

| 错误码 | 数值 | 描述 |
|--------|------|------|
| VALIDATION_ERROR | -32100 | 输入验证失败 |
| BAD_REQUEST | -32101 | 请求格式错误 |
| NOT_FOUND | -32102 | 资源不存在 |
| VERSION_CONFLICT | -32103 | 乐观锁版本冲突 |
| DUPLICATE_DETECTED | -32104 | 重复条目检测 |
| UNKNOWN_TOOL | -32105 | 未知工具名称 |
| SENSITIVE_CONTENT | -32106 | 内容包含敏感信息 |
