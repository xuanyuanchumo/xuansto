# MCP 审查文档

> 版本: 8.0.0 | 更新日期: 2026-05-25 | 编码: UTF-8 | 行尾: LF
> MCP Server 目录: `xuansto-mcp-server/src/xuansto_mcp/`
> Skill 目录: `.trae/skills/xuansto-skill-v2/`

本文档对 xuansto-skill-v2 的 MCP（Model Context Protocol）能力进行全面审查，基于 `xuansto-mcp-server` 实际代码，涵盖现有工具/资源/提示盘点、可 MCP 化能力识别、目标 MCP Server 设计、渐进式加载关联以及 Skill→MCP 交互协议。

---

## 1. 现有 MCP 调用盘点

### 1.1 MCP Tools（20 个）

定义位置：[server.py](../../xuansto-mcp-server/src/xuansto_mcp/server.py) 通过 `tool_module.register(mcp)` 注册，每个工具经由 `_with_hook_interception` 装饰器包装（pre-hook → 安全检查 → 速率限制 → 重试 → Token 追踪 → post-hook）。

| # | 工具名称 | 功能概述 | 源文件 | ToolAnnotations |
|---|---------|----------|--------|-----------------|
| 1 | `skill_analyze` | 项目结构分析：YAML 元数据、目录结构、Agent 注册表、脚本依赖、问题检测 | [skill_analyze.py](../../xuansto-mcp-server/src/xuansto_mcp/tools/skill_analyze.py) | readOnly, idempotent |
| 2 | `knowledge_search` | 三层知识库检索（ChromaDB→SQLite FTS5→关键词），自动降级 | [knowledge_search.py](../../xuansto-mcp-server/src/xuansto_mcp/tools/knowledge_search.py) | readOnly, idempotent |
| 3 | `knowledge_inject` | 知识注入/添加/更新/沉淀/列出可用知识 | [knowledge_inject.py](../../xuansto-mcp-server/src/xuansto_mcp/tools/knowledge_inject.py) | openWorld |
| 4 | `quality_gate_check` | 54 项质量门禁检查，按 gate_ids/phase 过滤，含缓存和硬门禁 | [quality_gate_check.py](../../xuansto-mcp-server/src/xuansto_mcp/tools/quality_gate_check.py) | readOnly, idempotent |
| 5 | `spec_drift_detect` | 规格-代码偏差检测，AST 级别匹配 | [spec_drift_detect.py](../../xuansto-mcp-server/src/xuansto_mcp/tools/spec_drift_detect.py) | readOnly, idempotent |
| 6 | `security_scan` | OWASP Agentic Top 10 + 依赖漏洞扫描 | [security_scan.py](../../xuansto-mcp-server/src/xuansto_mcp/tools/security_scan.py) | readOnly, openWorld |
| 7 | `code_simplify` | 代码简化分析：死代码/深层嵌套/过长函数/重复代码 | [code_simplify.py](../../xuansto-mcp-server/src/xuansto_mcp/tools/code_simplify.py) | readOnly, idempotent |
| 8 | `session_manage` | 会话状态管理：save/load/list/detect/verify/track/restore | [session_manage.py](../../xuansto-mcp-server/src/xuansto_mcp/tools/session_manage.py) | — |
| 9 | `workflow_dispatch` | 工作流调度：start/status/abort/phase/recover/snapshots | [workflow_dispatch.py](../../xuansto-mcp-server/src/xuansto_mcp/tools/workflow_dispatch.py) | — |
| 10 | `agent_status` | Agent 状态查询：list/by_phase/detail/match/merge | [agent_status.py](../../xuansto-mcp-server/src/xuansto_mcp/tools/agent_status.py) | — |
| 11 | `agent_manage` | Agent 实例管理：create/assign/release/destroy/instance_status/schedule | [agent_manage.py](../../xuansto-mcp-server/src/xuansto_mcp/tools/agent_manage.py) | destructive |
| 12 | `hook_manage` | Hook 管理：list/execute，16 个内嵌 Hook，3 种 profile | [hook_manage.py](../../xuansto-mcp-server/src/xuansto_mcp/tools/hook_manage.py) | — |
| 13 | `resource_load_status` | 渐进式加载状态管理：status/preload/cache/clear_cache/loading_progress/token_report/disclosure_transition | [resource_load_status.py](../../xuansto-mcp-server/src/xuansto_mcp/tools/resource_load_status.py) | — |
| 14 | `context_compress` | 上下文压缩：semantic/selective/lossless 三种策略 | [context_compress.py](../../xuansto-mcp-server/src/xuansto_mcp/tools/context_compress.py) | readOnly, idempotent |
| 15 | `server_health` | 服务器健康检查：check/negotiate_version/capabilities | [server_health.py](../../xuansto-mcp-server/src/xuansto_mcp/tools/server_health.py) | readOnly, idempotent |
| 16 | `decision_log` | 决策日志管理：log/list/query/update/export/stats，SQLite+FTS5 | [decision_log.py](../../xuansto-mcp-server/src/xuansto_mcp/tools/decision_log.py) | — |
| 17 | `token_budget` | Token 预算管理：status/set_budget/recommend/report/enforce | [token_budget.py](../../xuansto-mcp-server/src/xuansto_mcp/tools/token_budget.py) | — |
| 18 | `project_init` | 项目初始化：create/validate/detect_stack/configure | [project_init.py](../../xuansto-mcp-server/src/xuansto_mcp/tools/project_init.py) | — |
| 19 | `metrics_report` | 指标报告：query/summary/evaluate | [metrics_report.py](../../xuansto-mcp-server/src/xuansto_mcp/tools/metrics_report.py) | — |
| 20 | `config_manage` | 配置管理：reload/status/validate | [config_manage.py](../../xuansto-mcp-server/src/xuansto_mcp/tools/config_manage.py) | — |

#### 1.1.1 各工具完整 JSON Schema

**skill_analyze**

```json
{
  "input": {
    "type": "object",
    "properties": {
      "skill_path": { "type": "string", "description": "Skill 根目录绝对路径" },
      "include_scripts": { "type": "boolean", "default": true, "description": "是否分析 scripts 目录" },
      "include_agents": { "type": "boolean", "default": true, "description": "是否分析 agents 目录" },
      "depth": { "type": "string", "enum": ["basic", "detailed", "full", "comprehensive"], "default": "basic", "description": "分析深度" }
    },
    "required": ["skill_path"]
  },
  "output": {
    "type": "object",
    "properties": {
      "metadata": { "type": "object", "description": "YAML frontmatter 元数据" },
      "structure": { "type": "object", "description": "目录结构" },
      "depth_level": { "type": "integer", "description": "实际分析深度(1-3)" },
      "agents": { "type": "array", "description": "Agent 注册表(depth≥2)" },
      "dependencies": { "type": "object", "description": "脚本依赖(depth≥2)" },
      "issues": { "type": "array", "description": "验证问题(depth≥3)" },
      "project_scale": { "type": "string", "description": "项目规模(depth≥3)" },
      "recommended_workflow": { "type": "string", "description": "推荐工作流(depth≥3)" }
    }
  }
}
```

**knowledge_search**

```json
{
  "input": {
    "type": "object",
    "properties": {
      "action": { "type": "string", "enum": ["retrieve"], "description": "仅支持 retrieve 操作" },
      "query": { "type": "string", "description": "检索文本" },
      "top_k": { "type": "integer", "default": 5, "minimum": 1, "maximum": 50, "description": "最大返回数" },
      "search_type": { "type": "string", "enum": ["hybrid", "semantic_only", "keyword_only"], "default": "hybrid", "description": "检索策略" },
      "scope": { "type": "string", "enum": ["general", "workspace", "experience"], "description": "知识库范围" },
      "min_confidence": { "type": "number", "default": 0.0, "minimum": 0, "maximum": 1, "description": "最低置信度" }
    },
    "required": ["action", "query"]
  },
  "output": {
    "type": "object",
    "properties": {
      "results": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "source": { "type": "string" },
            "content": { "type": "string" },
            "match_type": { "type": "string", "enum": ["semantic", "fts5", "keyword"] },
            "relevance": { "type": "number" }
          }
        }
      },
      "total": { "type": "integer" },
      "strategy": { "type": "string", "enum": ["chromadb_semantic", "sqlite_fts5_bm25", "keyword_tfidf"] }
    }
  }
}
```

**knowledge_inject**

```json
{
  "input": {
    "type": "object",
    "properties": {
      "action": { "type": "string", "enum": ["inject", "list_available", "precipitate", "add", "update"], "description": "操作类型" },
      "topics": { "type": "array", "items": { "type": "string" }, "description": "注入主题列表(inject)" },
      "scope": { "type": "string", "enum": ["general", "workspace", "experience"], "default": "general", "description": "知识范围" },
      "max_tokens": { "type": "integer", "default": 5000, "description": "注入最大 Token 数" },
      "relevance_threshold": { "type": "number", "default": 0.5, "description": "相关性阈值" },
      "category": { "type": "string", "description": "沉淀分类(precipitate)" },
      "title": { "type": "string", "description": "条目标题(precipitate/add)" },
      "content": { "type": "string", "description": "条目内容(precipitate/add)" },
      "tags": { "type": "array", "items": { "type": "string" }, "description": "标签" },
      "confidence": { "type": "number", "default": 0.8, "description": "置信度(precipitate)" },
      "entry_id": { "type": "string", "description": "条目 ID(update)" }
    },
    "required": ["action"]
  },
  "output": {
    "type": "object",
    "properties": {
      "injected_count": { "type": "integer" },
      "total_estimated_tokens": { "type": "integer" },
      "precipitated_id": { "type": "string" },
      "added_id": { "type": "string" },
      "updated": { "type": "boolean" }
    }
  }
}
```

**quality_gate_check**

```json
{
  "input": {
    "type": "object",
    "properties": {
      "gate_ids": { "type": "array", "items": { "type": "string" }, "description": "指定门禁 ID" },
      "phase": { "type": "string", "description": "阶段编号(0-8)" },
      "project_path": { "type": "string", "default": ".", "description": "项目根目录" },
      "severity_filter": { "type": "string", "enum": ["all", "BLOCK", "WARN"], "default": "all" },
      "force_refresh": { "type": "boolean", "default": false, "description": "强制刷新缓存" }
    }
  },
  "output": {
    "type": "object",
    "properties": {
      "checks": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "gate_id": { "type": "string" },
            "status": { "type": "string", "enum": ["PASS", "FAIL", "SKIP", "ERROR", "BLOCKED"] },
            "source": { "type": "string", "enum": ["script", "inline", "cache", "hard_gate", "no_inline_check"] },
            "details": { "type": "object" },
            "suggestion": { "type": "string" }
          }
        }
      },
      "summary": {
        "type": "object",
        "properties": {
          "total": { "type": "integer" },
          "passed": { "type": "integer" },
          "failed": { "type": "integer" },
          "skipped": { "type": "integer" },
          "blocked": { "type": "boolean" },
          "hard_gate_blocked": { "type": "integer" }
        }
      },
      "cache_info": { "type": "object" }
    }
  }
}
```

**spec_drift_detect**

```json
{
  "input": {
    "type": "object",
    "properties": {
      "spec_dir": { "type": "string", "default": ".trae/specs", "description": "规格文档目录" },
      "src_dir": { "type": "string", "default": ".", "description": "源码目录" }
    }
  },
  "output": {
    "type": "object",
    "properties": {
      "total_specs": { "type": "integer" },
      "total_pending_tasks": { "type": "integer" },
      "drifts": { "type": "array", "items": { "type": "object" } },
      "implementation_rate": { "type": "number" },
      "analysis_level": { "type": "string", "enum": ["ast", "keyword_match", "none"] },
      "interface_coverage": { "type": "number" }
    }
  }
}
```

**security_scan**

```json
{
  "input": {
    "type": "object",
    "properties": {
      "target": { "type": "string", "default": ".", "description": "扫描目标目录" },
      "severity_threshold": { "type": "string", "enum": ["critical", "high", "medium", "low"], "default": "medium" },
      "include_agentic": { "type": "boolean", "default": true, "description": "包含 OWASP Agentic Top 10" },
      "include_dependency": { "type": "boolean", "default": true, "description": "包含依赖漏洞扫描" }
    }
  },
  "output": {
    "type": "object",
    "properties": {
      "agentic_scan": {
        "type": "object",
        "properties": {
          "vulnerabilities": { "type": "array" },
          "total": { "type": "integer" },
          "by_severity": { "type": "object" },
          "security_score": { "type": "integer", "minimum": 0, "maximum": 100 }
        }
      },
      "dependency_scan": {
        "type": "object",
        "properties": {
          "dependencies": { "type": "array" },
          "total": { "type": "integer" },
          "vulnerable_count": { "type": "integer" }
        }
      }
    }
  }
}
```

**code_simplify**

```json
{
  "input": {
    "type": "object",
    "properties": {
      "target": { "type": "string", "description": "目标文件或目录" },
      "scope": { "type": "string", "enum": ["file", "dir", "recent"], "default": "recent", "description": "扫描范围" },
      "include_dedup": { "type": "boolean", "default": true, "description": "包含重复代码检测" }
    },
    "required": ["target"]
  },
  "output": {
    "type": "object",
    "properties": {
      "simplification": {
        "type": "object",
        "properties": {
          "suggestions": { "type": "array" },
          "total": { "type": "integer" },
          "by_type": { "type": "object" },
          "quality_score": { "type": "integer" },
          "analysis_level": { "type": "string", "enum": ["ast", "text_level"] }
        }
      },
      "deduplication": {
        "type": "object",
        "properties": {
          "duplicates": { "type": "array" },
          "total_groups": { "type": "integer" },
          "total_duplicate_lines": { "type": "integer" }
        }
      }
    }
  }
}
```

**session_manage**

```json
{
  "input": {
    "type": "object",
    "properties": {
      "action": { "type": "string", "enum": ["save", "load", "list", "detect", "verify", "track", "restore"], "description": "操作类型" },
      "completed_tasks": { "type": "array", "items": { "type": "string" }, "description": "已完成任务(save)" },
      "pending_tasks": { "type": "array", "items": { "type": "string" }, "description": "待办任务(save/track)" },
      "decisions": { "type": "array", "items": { "type": "string" }, "description": "决策列表(save)" },
      "experience": { "type": "array", "items": { "type": "string" }, "description": "经验沉淀(save)" },
      "error_log": { "type": "array", "items": { "type": "string" }, "description": "错误日志(detect)" },
      "pattern_path": { "type": "string", "description": "模式文件路径(verify)" },
      "success": { "type": "boolean", "default": true, "description": "验证结果(verify)" },
      "current_phase": { "type": "integer", "description": "当前阶段(track)" },
      "current_task": { "type": "string", "description": "当前任务(track)" }
    },
    "required": ["action"]
  },
  "output": {
    "type": "object",
    "properties": {
      "action": { "type": "string" },
      "session_id": { "type": "string" },
      "saved_at": { "type": "string" },
      "state": { "type": "object" }
    }
  }
}
```

**workflow_dispatch**

```json
{
  "input": {
    "type": "object",
    "properties": {
      "action": { "type": "string", "enum": ["start", "status", "abort", "phase", "recover", "snapshots"], "description": "操作类型" },
      "workflow": { "type": "string", "description": "工作流名称(start): sdd-tdd-full/medium/fast 等" },
      "project_path": { "type": "string", "default": ".", "description": "项目根目录(start)" },
      "workflow_id": { "type": "string", "description": "工作流实例 ID" },
      "phase_action": { "type": "string", "enum": ["advance", "current"], "description": "阶段操作(phase)" },
      "snapshot_phase": { "type": "integer", "description": "恢复目标阶段(recover)" }
    },
    "required": ["action"]
  },
  "output": {
    "type": "object",
    "properties": {
      "action": { "type": "string" },
      "workflow_id": { "type": "string" },
      "workflow_name": { "type": "string" },
      "current_phase": { "type": "integer" },
      "phases": { "type": "array", "items": { "type": "object" } },
      "started_at": { "type": "string" },
      "aborted_at": { "type": "string" }
    }
  }
}
```

**agent_status**

```json
{
  "input": {
    "type": "object",
    "properties": {
      "action": { "type": "string", "enum": ["list", "by_phase", "detail", "match", "merge"], "description": "操作类型" },
      "phase": { "type": "integer", "description": "阶段编号(by_phase, 0-8)" },
      "agent_name": { "type": "string", "description": "Agent 名称(detail)" },
      "capabilities": { "type": "array", "items": { "type": "string" }, "description": "能力列表(match)" },
      "project_file_count": { "type": "integer", "description": "项目文件数(merge 自动合并)" }
    },
    "required": ["action"]
  },
  "output": {
    "type": "object",
    "properties": {
      "action": { "type": "string" },
      "agents": { "type": "array", "items": { "type": "object" } },
      "total_agents": { "type": "integer" },
      "available_count": { "type": "integer" }
    }
  }
}
```

**agent_manage**

```json
{
  "input": {
    "type": "object",
    "properties": {
      "action": { "type": "string", "enum": ["create", "assign", "release", "instance_status", "destroy", "schedule"], "description": "操作类型" },
      "agent_type": { "type": "string", "description": "Agent 类型(create)" },
      "capabilities": { "type": "array", "items": { "type": "string" }, "description": "能力列表(create)" },
      "agent_id": { "type": "string", "description": "实例 ID(assign/release/instance_status/destroy)" },
      "task": { "type": "string", "description": "任务描述(assign)" }
    },
    "required": ["action"]
  },
  "output": {
    "type": "object",
    "properties": {
      "action": { "type": "string" },
      "agent_id": { "type": "string" },
      "status": { "type": "string" },
      "agent_type": { "type": "string" },
      "capabilities": { "type": "array" }
    }
  }
}
```

**hook_manage**

```json
{
  "input": {
    "type": "object",
    "properties": {
      "action": { "type": "string", "enum": ["list", "execute"], "description": "操作类型" },
      "profile": { "type": "string", "enum": ["minimal", "standard", "strict"], "default": "standard", "description": "Hook 配置级别" },
      "hook_name": { "type": "string", "description": "Hook 名称(execute)" },
      "context": { "type": "object", "description": "执行上下文(execute)" }
    },
    "required": ["action"]
  },
  "output": {
    "type": "object",
    "properties": {
      "action": { "type": "string" },
      "profile": { "type": "string" },
      "hooks": { "type": "array", "items": { "type": "object" } },
      "total_hooks": { "type": "integer" },
      "enabled_count": { "type": "integer" }
    }
  }
}
```

**resource_load_status**

```json
{
  "input": {
    "type": "object",
    "properties": {
      "action": { "type": "string", "enum": ["status", "preload", "cache", "clear_cache", "loading_progress", "token_report", "disclosure_transition"], "description": "操作类型" },
      "phase": { "type": "integer", "description": "指定阶段编号(0-3)" },
      "resource_ids": { "type": "array", "items": { "type": "string" }, "description": "指定资源 ID" },
      "resource_uris": { "type": "array", "items": { "type": "string" }, "description": "指定资源 URI" },
      "priority": { "type": "string", "enum": ["critical", "normal", "background"], "default": "normal", "description": "预加载优先级" },
      "batch_mode": { "type": "boolean", "default": false, "description": "批量并发加载" },
      "auto_upgrade": { "type": "boolean", "default": false, "description": "Token 预算超限时自动升级阶段" },
      "target_phase": { "type": "string", "enum": ["skeleton", "functional", "enhanced", "full"], "description": "目标阶段(preload)" }
    },
    "required": ["action"]
  },
  "output": {
    "type": "object",
    "properties": {
      "action": { "type": "string" },
      "current_phase": { "type": "string" },
      "phase_index": { "type": "integer" },
      "loaded_resources": { "type": "array" },
      "loaded_count": { "type": "integer" },
      "available_resources": { "type": "array" },
      "available_commands": { "type": "array" },
      "disclosure_note": { "type": "string" },
      "upgrade_hint": { "type": "string" },
      "progress": { "type": "object" },
      "token_budget": { "type": "object" },
      "timestamp": { "type": "string" }
    }
  }
}
```

**context_compress**

```json
{
  "input": {
    "type": "object",
    "properties": {
      "content": { "type": "string", "description": "待压缩文本" },
      "strategy": { "type": "string", "enum": ["semantic", "selective", "lossless"], "default": "semantic", "description": "压缩策略" },
      "target_tokens": { "type": "integer", "default": 2000, "minimum": 100, "maximum": 50000, "description": "目标 Token 数" },
      "preserve_sections": { "type": "array", "items": { "type": "string" }, "description": "保留章节标题" }
    },
    "required": ["content"]
  },
  "output": {
    "type": "object",
    "properties": {
      "original_tokens": { "type": "integer" },
      "compressed_tokens": { "type": "integer" },
      "compression_ratio": { "type": "number" },
      "strategy_used": { "type": "string" },
      "compressed_content": { "type": "string" },
      "preserved_sections": { "type": "array" },
      "quality_score": { "type": "number" }
    }
  }
}
```

**server_health**

```json
{
  "input": {
    "type": "object",
    "properties": {
      "action": { "type": "string", "enum": ["check", "negotiate_version", "capabilities"], "default": "check", "description": "操作类型" },
      "client_version": { "type": "string", "description": "客户端 API 版本(negotiate_version)" }
    }
  },
  "output": {
    "type": "object",
    "properties": {
      "status": { "type": "string", "enum": ["HEALTHY", "DEGRADED", "UNAVAILABLE"] },
      "version": { "type": "string" },
      "api_version": { "type": "string" },
      "uptime_seconds": { "type": "number" },
      "tools_available": { "type": "integer" },
      "degradation_level": { "type": "string" },
      "last_check_timestamp": { "type": "string" },
      "tools_status": { "type": "object" },
      "memory_usage_mb": { "type": "number" },
      "active_workflows": { "type": "integer" },
      "active_sessions": { "type": "integer" }
    }
  }
}
```

**decision_log**

```json
{
  "input": {
    "type": "object",
    "properties": {
      "action": { "type": "string", "enum": ["log", "list", "query", "update", "export", "stats"], "description": "操作类型" },
      "title": { "type": "string", "description": "决策标题(log)" },
      "description": { "type": "string", "description": "决策描述(log)" },
      "context": { "type": "string", "description": "决策上下文(log)" },
      "alternatives": { "type": "array", "items": { "type": "string" }, "description": "备选方案(log)" },
      "decision": { "type": "string", "description": "最终决策(log)" },
      "rationale": { "type": "string", "description": "决策理由(log)" },
      "impact": { "type": "string", "description": "影响范围(log)" },
      "decided_by": { "type": "string", "description": "决策者(log)" },
      "keyword": { "type": "string", "description": "搜索关键词(query)" },
      "tag": { "type": "string", "description": "标签过滤(query)" },
      "date_from": { "type": "string", "format": "date-time", "description": "起始日期(query/export)" },
      "date_to": { "type": "string", "format": "date-time", "description": "结束日期(query/export)" },
      "limit": { "type": "integer", "default": 20, "minimum": 1, "maximum": 100, "description": "结果限制" },
      "offset": { "type": "integer", "default": 0, "description": "偏移量" },
      "format": { "type": "string", "enum": ["json", "markdown"], "default": "json", "description": "导出格式(export)" }
    },
    "required": ["action"]
  },
  "output": {
    "type": "object",
    "properties": {
      "action": { "type": "string" },
      "id": { "type": "string", "description": "ADR 格式: ADR-YYYYMMDD-NNN" },
      "entry": { "type": "object" },
      "results": { "type": "array" },
      "total_decisions": { "type": "integer" },
      "format": { "type": "string" },
      "content": { "type": "string" }
    }
  }
}
```

**token_budget**

```json
{
  "input": {
    "type": "object",
    "properties": {
      "action": { "type": "string", "enum": ["status", "set_budget", "recommend", "report", "enforce"], "description": "操作类型" },
      "total_budget": { "type": "integer", "minimum": 1000, "description": "总预算(set_budget)" },
      "phase_allocations": { "type": "object", "description": "阶段分配(set_budget)" },
      "project_size": { "type": "string", "enum": ["small", "medium", "large"], "description": "项目规模(recommend)" },
      "complexity": { "type": "string", "enum": ["low", "medium", "high"], "description": "复杂度(recommend)" },
      "team_size": { "type": "integer", "minimum": 1, "maximum": 50, "description": "团队规模(recommend)" },
      "period": { "type": "string", "enum": ["daily", "weekly", "session"], "default": "session", "description": "报告周期(report)" }
    },
    "required": ["action"]
  },
  "output": {
    "type": "object",
    "properties": {
      "action": { "type": "string" },
      "total_budget": { "type": "integer" },
      "used": { "type": "integer" },
      "remaining": { "type": "integer" },
      "phase_allocations": { "type": "object" },
      "usage_by_phase": { "type": "object" }
    }
  }
}
```

**project_init**

```json
{
  "input": {
    "type": "object",
    "properties": {
      "action": { "type": "string", "enum": ["create", "init", "validate", "detect_stack", "detect", "configure"], "description": "操作类型" },
      "name": { "type": "string", "description": "项目名称(create)" },
      "description": { "type": "string", "description": "项目描述(create)" },
      "stack": { "type": "array", "items": { "type": "string" }, "description": "技术栈(create)" },
      "template": { "type": "string", "description": "项目模板(create)" },
      "directory": { "type": "string", "description": "项目目录(create)" },
      "project_path": { "type": "string", "description": "项目路径(validate/detect_stack)" }
    },
    "required": ["action"]
  },
  "output": {
    "type": "object",
    "properties": {
      "action": { "type": "string" },
      "name": { "type": "string" },
      "directory": { "type": "string" },
      "config_path": { "type": "string" },
      "stack": { "type": "array" },
      "template": { "type": "string" },
      "valid": { "type": "boolean" },
      "issues": { "type": "array" },
      "detected_stacks": { "type": "array" }
    }
  }
}
```

**metrics_report**

```json
{
  "input": {
    "type": "object",
    "properties": {
      "action": { "type": "string", "enum": ["query", "summary", "evaluate"], "description": "操作类型" },
      "tool_name": { "type": "string", "description": "工具名称(query)" },
      "time_range": { "type": "string", "default": "all", "description": "时间范围(query)" },
      "metric_type": { "type": "string", "default": "all", "description": "指标类型(query)" },
      "criterion": { "type": "string", "default": "all", "description": "评估标准(evaluate)" }
    },
    "required": ["action"]
  },
  "output": {
    "type": "object",
    "properties": {
      "action": { "type": "string" },
      "metrics": { "type": "object" },
      "summary": { "type": "object" },
      "evaluation": { "type": "object" }
    }
  }
}
```

**config_manage**

```json
{
  "input": {
    "type": "object",
    "properties": {
      "action": { "type": "string", "enum": ["reload", "status", "validate"], "description": "操作类型" }
    },
    "required": ["action"]
  },
  "output": {
    "type": "object",
    "properties": {
      "action": { "type": "string" },
      "gate_scripts_count": { "type": "integer" },
      "gates_by_phase_count": { "type": "integer" },
      "hook_scripts_count": { "type": "integer" },
      "validation_warnings": { "type": "array" },
      "validation_results": { "type": "object" }
    }
  }
}
```

### 1.2 MCP Resources（22 个）

定义位置：[skill_resources.py](../../xuansto-mcp-server/src/xuansto_mcp/resources/skill_resources.py)，通过 `skill_resources.register(mcp)` 注册。所有 Resource 均支持降级响应（`_degraded_resource` 返回 `status: "degraded"` JSON）。

| # | URI 模式 | 描述 | 内容类型 | 参数 |
|---|---------|------|----------|------|
| 1 | `xuansto://config/skill` | Skill 配置文件 (.skill-config.yaml) | text/markdown | — |
| 2 | `xuansto://references/quality-gates` | 质量门禁参考文档 | text/markdown | — |
| 3 | `xuansto://references/agent-registry` | Agent 注册表参考文档 | text/markdown | — |
| 4 | `xuansto://references/workflow-phases` | 工作流阶段参考文档 | text/markdown | — |
| 5 | `xuansto://templates/{name}` | 模板文件（按名称） | text/markdown | name: 模板名 |
| 6 | `xuansto://sessions/latest` | 最新会话记录 | text/markdown | — |
| 7 | `xuansto://sessions/{session_id}` | 指定 ID 的会话记录 | text/markdown | session_id: 会话 ID |
| 8 | `xuansto://agents/{layer}/{name}` | 指定层级和名称的 Agent 定义 | text/markdown | layer: 层级, name: 名称 |
| 9 | `xuansto://loading/status` | 渐进式加载状态 | application/json | — |
| 10 | `xuansto://metrics/summary` | 工具指标汇总 | application/json | — |
| 11 | `xuansto://degradation/status` | 降级状态 | application/json | — |
| 12 | `xuansto://skill/config` | Skill 配置（统一入口） | text/markdown | — |
| 13 | `xuansto://skill/constraints` | Skill 约束配置 | text/markdown | — |
| 14 | `xuansto://agents/registry` | Agent 注册表（JSON 格式） | application/json | — |
| 15 | `xuansto://gates/definitions` | 质量门禁定义 | text/markdown | — |
| 16 | `xuansto://workflows/definitions` | 工作流定义 | text/markdown | — |
| 17 | `xuansto://hooks/definitions` | Hook 定义 | text/markdown | — |
| 18 | `xuansto://knowledge/status` | 知识库状态 | application/json | — |
| 19 | `xuansto://templates/index` | 模板索引 | application/json | — |
| 20 | `xuansto://commands/routes` | 命令路由索引 | application/json | — |
| 21 | `xuansto://session/state` | 当前会话状态 | application/json | — |
| 22 | `xuansto://health/status` | 健康状态 | application/json | — |

### 1.3 MCP Prompts（2 个）

定义位置：[server.py](../../xuansto-mcp-server/src/xuansto_mcp/server.py) L196-L202。

| # | 名称 | 参数 | 返回 |
|---|------|------|------|
| 1 | `xuansto_workflow` | `task_description: str` | `"Execute xuansto workflow for: {task_description}"` |
| 2 | `xuansto_analysis` | `skill_path: str` | `"Analyze skill at: {skill_path}"` |

---

## 2. 可 MCP 化能力识别

### 2.1 适合封装为 Tool 的功能单元

以下 20 个功能已完整封装为 MCP Tool，均具备 `inputSchema`、`outputSchema` 和 `ToolAnnotations`：

| 分类 | 工具 | 输入 | 输出 | 封装状态 |
|------|------|------|------|----------|
| 知识检索 | knowledge_search | action, query, top_k, search_type, scope, min_confidence | results, total, strategy | ✅ 已封装 |
| 知识写入 | knowledge_inject | action, topics, scope, max_tokens, title, content, tags, entry_id | injected_count, precipitated_id, added_id | ✅ 已封装 |
| 项目分析 | skill_analyze | skill_path, include_scripts, include_agents, depth | metadata, structure, agents, dependencies, issues | ✅ 已封装 |
| 质量保障 | quality_gate_check | gate_ids, phase, project_path, severity_filter, force_refresh | checks, summary, cache_info | ✅ 已封装 |
| 质量保障 | spec_drift_detect | spec_dir, src_dir | total_specs, drifts, implementation_rate | ✅ 已封装 |
| 安全扫描 | security_scan | target, severity_threshold, include_agentic, include_dependency | agentic_scan, dependency_scan | ✅ 已封装 |
| 代码优化 | code_simplify | target, scope, include_dedup | simplification, deduplication | ✅ 已封装 |
| 会话管理 | session_manage | action, completed_tasks, pending_tasks, decisions, experience | session_id, saved_at, state | ✅ 已封装 |
| 工作流 | workflow_dispatch | action, workflow, project_path, workflow_id, phase_action | workflow_id, current_phase, phases | ✅ 已封装 |
| Agent 查询 | agent_status | action, phase, agent_name, capabilities | agents, total_agents | ✅ 已封装 |
| Agent 管理 | agent_manage | action, agent_type, capabilities, agent_id, task | agent_id, status, agent_type | ✅ 已封装 |
| Hook 管理 | hook_manage | action, profile, hook_name, context | hooks, total_hooks, enabled_count | ✅ 已封装 |
| 加载控制 | resource_load_status | action, phase, resource_ids, priority, batch_mode, auto_upgrade | current_phase, loaded_resources, disclosure_note | ✅ 已封装 |
| 上下文 | context_compress | content, strategy, target_tokens, preserve_sections | compressed_content, compression_ratio, quality_score | ✅ 已封装 |
| 健康检查 | server_health | action, client_version | status, version, tools_available | ✅ 已封装 |
| 决策日志 | decision_log | action, title, alternatives, decision, rationale, keyword, tag | id, entry, results, total_decisions | ✅ 已封装 |
| Token 预算 | token_budget | action, total_budget, phase_allocations, project_size | total_budget, used, remaining, phase_allocations | ✅ 已封装 |
| 项目初始化 | project_init | action, name, stack, template, directory, project_path | name, directory, config_path, stack | ✅ 已封装 |
| 指标报告 | metrics_report | action, tool_name, time_range, metric_type, criterion | metrics, summary, evaluation | ✅ 已封装 |
| 配置管理 | config_manage | action | gate_scripts_count, validation_warnings | ✅ 已封装 |

### 2.2 适合封装为 Resource 的数据

当前 MCP Server 已暴露 22 个 Resource。以下为建议新增的 Resource：

| URI 模式 | 描述 | 内容类型 | 建议阶段 | 数据来源 |
|---------|------|----------|----------|----------|
| `xuansto://agents/{name}` | 单个 Agent 的完整定义（无需指定 layer） | text/markdown | Phase 2+ | `AGENTS_DIR` 递归搜索 `{name}.md` |
| `xuansto://knowledge/stats` | 知识库实时统计（含 ChromaDB 向量数、SQLite 条目数） | application/json | Phase 1+ | `knowledge_stats` 工具返回值 |
| `xuansto://decisions/latest` | 最近 10 条决策记录 | application/json | Phase 2+ | `decision_log` SQLite 查询 |
| `xuansto://workflows/active` | 当前活跃工作流列表 | application/json | Phase 1+ | `workflow_dispatch` 内存状态 |

#### 新增 Resource 详细设计

**xuansto://agents/{name}**

- 描述：按 Agent 名称获取完整 Agent 定义文件内容（无需指定层级，自动递归搜索）
- URI 参数：`{name}` 为 Agent 文件名（不含扩展名），如 `backend-developer`、`qa-engineer`
- 内容类型：`text/markdown`
- 可用阶段：Phase 2 (Enhanced) 及以上
- 实现方式：在 `AGENTS_DIR` 下递归搜索 `{name}.md`
- 与现有 `xuansto://agents/{layer}/{name}` 的区别：无需预知 layer，更易用

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

**xuansto://decisions/latest**

- 描述：最近 10 条决策记录，按时间倒序
- 内容类型：`application/json`
- 可用阶段：Phase 2 (Enhanced) 及以上
- 实现方式：查询 `decision_log` SQLite 表 `ORDER BY created_at DESC LIMIT 10`

**xuansto://workflows/active**

- 描述：当前活跃的工作流实例列表
- 内容类型：`application/json`
- 可用阶段：Phase 1 (Functional) 及以上
- 实现方式：读取 `workflow_dispatch` 内存中的活跃工作流状态

---

## 3. 目标 MCP Server 设计

### 3.1 Server 基本信息

| 属性 | 值 |
|------|-----|
| Server 名称 | `xuansto-mcp-server` |
| 描述 | 多 Agent 自主开发编排引擎的 MCP 工具集 |
| Skill 版本 | 8.0.0 |
| API 版本 | 3.0.0（最低兼容 2.0.0） |
| 协议 | Model Context Protocol (MCP) |
| 传输方式 | stdio |
| 框架 | FastMCP (Python) |
| 依赖 | Python ≥3.10, mcp SDK, chromadb(可选), watchfiles(可选) |
| 注册工具数 | 20 |
| 注册资源数 | 22 |
| 注册提示数 | 2 |

### 3.2 完整 Tool 列表

| # | 名称 | 描述 | readOnly | destructive | idempotent | openWorld |
|---|------|------|:---:|:---:|:---:|:---:|
| 1 | skill_analyze | 项目结构分析 | ✅ | ❌ | ✅ | ❌ |
| 2 | knowledge_search | 三层知识库检索 | ✅ | ❌ | ✅ | ❌ |
| 3 | knowledge_inject | 知识注入/添加/更新/沉淀 | ❌ | ❌ | ❌ | ✅ |
| 4 | quality_gate_check | 54 项质量门禁检查 | ✅ | ❌ | ✅ | ❌ |
| 5 | spec_drift_detect | 规格-代码偏差检测 | ✅ | ❌ | ✅ | ❌ |
| 6 | security_scan | OWASP+依赖扫描 | ✅ | ❌ | ❌ | ✅ |
| 7 | code_simplify | 代码简化分析 | ✅ | ❌ | ✅ | ❌ |
| 8 | session_manage | 会话状态管理 | ❌ | ❌ | ❌ | ❌ |
| 9 | workflow_dispatch | 工作流调度 | ❌ | ❌ | ❌ | ❌ |
| 10 | agent_status | Agent 状态查询 | ❌ | ❌ | ❌ | ❌ |
| 11 | agent_manage | Agent 实例管理 | ❌ | ✅ | ❌ | ❌ |
| 12 | hook_manage | Hook 管理 | ❌ | ❌ | ❌ | ❌ |
| 13 | resource_load_status | 渐进式加载控制 | ❌ | ❌ | ❌ | ❌ |
| 14 | context_compress | 上下文压缩 | ✅ | ❌ | ✅ | ❌ |
| 15 | server_health | 服务器健康检查 | ✅ | ❌ | ✅ | ❌ |
| 16 | decision_log | 决策日志管理 | ❌ | ❌ | ❌ | ❌ |
| 17 | token_budget | Token 预算管理 | ❌ | ❌ | ❌ | ❌ |
| 18 | project_init | 项目初始化 | ❌ | ❌ | ❌ | ❌ |
| 19 | metrics_report | 指标报告 | ❌ | ❌ | ❌ | ❌ |
| 20 | config_manage | 配置管理 | ❌ | ❌ | ❌ | ❌ |

### 3.3 完整 Resource 列表

| # | URI | 描述 | 内容类型 | 可用阶段 |
|---|-----|------|----------|----------|
| 1 | `xuansto://config/skill` | Skill 配置文件 | text/markdown | Phase 0+ |
| 2 | `xuansto://references/quality-gates` | 质量门禁参考 | text/markdown | Phase 1+ |
| 3 | `xuansto://references/agent-registry` | Agent 注册表 | text/markdown | Phase 1+ |
| 4 | `xuansto://references/workflow-phases` | 工作流阶段 | text/markdown | Phase 1+ |
| 5 | `xuansto://templates/{name}` | 模板文件 | text/markdown | Phase 2+ |
| 6 | `xuansto://sessions/latest` | 最新会话 | text/markdown | Phase 1+ |
| 7 | `xuansto://sessions/{session_id}` | 指定会话 | text/markdown | Phase 1+ |
| 8 | `xuansto://agents/{layer}/{name}` | Agent 定义 | text/markdown | Phase 2+ |
| 9 | `xuansto://loading/status` | 加载状态 | application/json | Phase 0+ |
| 10 | `xuansto://metrics/summary` | 指标汇总 | application/json | Phase 2+ |
| 11 | `xuansto://degradation/status` | 降级状态 | application/json | Phase 1+ |
| 12 | `xuansto://skill/config` | Skill 配置（统一） | text/markdown | Phase 0+ |
| 13 | `xuansto://skill/constraints` | 约束配置 | text/markdown | Phase 0+ |
| 14 | `xuansto://agents/registry` | Agent 注册表（JSON） | application/json | Phase 1+ |
| 15 | `xuansto://gates/definitions` | 门禁定义 | text/markdown | Phase 1+ |
| 16 | `xuansto://workflows/definitions` | 工作流定义 | text/markdown | Phase 1+ |
| 17 | `xuansto://hooks/definitions` | Hook 定义 | text/markdown | Phase 1+ |
| 18 | `xuansto://knowledge/status` | 知识库状态 | application/json | Phase 1+ |
| 19 | `xuansto://templates/index` | 模板索引 | application/json | Phase 2+ |
| 20 | `xuansto://commands/routes` | 命令路由 | application/json | Phase 1+ |
| 21 | `xuansto://session/state` | 会话状态 | application/json | Phase 1+ |
| 22 | `xuansto://health/status` | 健康状态 | application/json | Phase 0+ |

### 3.4 权限与安全边界

所有 20 个工具均通过 `ToolAnnotations` 标注了安全边界信息：

| 标注 | 含义 | 工具数量 | 工具列表 |
|------|------|---------|----------|
| `readOnlyHint=True` | 只读操作，不修改任何状态 | 8 | skill_analyze, knowledge_search, quality_gate_check, spec_drift_detect, security_scan, code_simplify, context_compress, server_health |
| `destructiveHint=True` | 破坏性操作，不可逆 | 1 | agent_manage |
| `idempotentHint=True` | 幂等操作，重复调用结果一致 | 8 | skill_analyze, knowledge_search, quality_gate_check, spec_drift_detect, code_simplify, context_compress, server_health |
| `openWorldHint=True` | 访问外部网络资源 | 2 | knowledge_inject, security_scan |

#### 安全措施

1. **Hook 拦截引擎**：`_with_hook_interception` 装饰器为所有工具调用添加 pre-hook 和 post-hook 拦截，安全 Hook 失败时默认阻断执行
2. **速率限制**：`check_rate_limit(tool_name)` 为每个工具实施调用频率限制
3. **路径安全验证**：`validate_path_safety` 防止路径遍历攻击，所有接受路径参数的工具均使用
4. **输入验证**：`validate_input` 使用 Pydantic 模型校验所有工具输入
5. **破坏性操作标记**：`agent_manage` 标记为 `destructiveHint=True`，Host 端可要求用户确认
6. **外部访问标记**：`knowledge_inject` 和 `security_scan` 标记为 `openWorldHint=True`，Host 端可限制网络访问
7. **硬门禁**：`quality_gate_check` 中的 `_SECURITY_HARD_GATES` 集合定义了必须人工确认的安全门禁

### 3.5 mcpServers 配置 JSON

**uvx 方式（推荐）**

```json
{
  "mcpServers": {
    "xuansto-mcp-server": {
      "command": "uvx",
      "args": [
        "xuansto-mcp-server@>=8.0.0"
      ],
      "env": {
        "SKILL_ROOT": ".trae/skills/xuansto-skill-v2",
        "XUANSTO_WORK_DIR": ".xuansto",
        "XUANSTO_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

**Python 直接运行方式**

```json
{
  "mcpServers": {
    "xuansto-mcp-server": {
      "command": "python",
      "args": [
        "-m",
        "xuansto_mcp"
      ],
      "cwd": "xuansto-mcp-server",
      "env": {
        "SKILL_ROOT": ".trae/skills/xuansto-skill-v2",
        "XUANSTO_WORK_DIR": ".xuansto",
        "XUANSTO_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

**开发模式（可编辑安装）**

```json
{
  "mcpServers": {
    "xuansto-mcp-server": {
      "command": "python",
      "args": [
        "-m",
        "xuansto_mcp"
      ],
      "cwd": "xuansto-mcp-server/src",
      "env": {
        "SKILL_ROOT": ".trae/skills/xuansto-skill-v2",
        "XUANSTO_WORK_DIR": ".xuansto",
        "XUANSTO_LOG_LEVEL": "DEBUG",
        "PYTHONPATH": "xuansto-mcp-server/src"
      }
    }
  }
}
```

---

## 4. 渐进式加载与 MCP 关联

### 4.1 加载阶段体系

渐进式加载系统定义了四个阶段，由 `resource_load_status` 工具和 `xuansto://loading/status` Resource 共同管理：

| 阶段 | 名称 | Token 预算 | 加载资源 | 对应工具可用性 |
|------|------|----------|----------|---------------|
| Phase 0 | 骨架 (Skeleton) | 2K | skill-config | resource_load_status, server_health, config_manage |
| Phase 1 | 功能 (Functional) | 5K | agent-registry, quality-gates, brainstorm-workflow, 核心 Agent | + knowledge_search, knowledge_inject(list_available), workflow_dispatch, agent_status, session_manage, project_init, decision_log(log) |
| Phase 2 | 增强 (Enhanced) | 10K | knowledge-general, sdd-tdd 工作流, mcp-tools 参考, 完整 Agent 注册表 | + knowledge_inject(inject/precipitate/add/update), quality_gate_check, spec_drift_detect, token_budget, context_compress, hook_manage, metrics_report |
| Phase 3 | 完整 (Full) | 20K | 全部参考文档、模板、完整 Agent 目录、脚本集 | + security_scan, code_simplify, agent_manage, decision_log(query/export/stats) |

### 4.2 PHASE_RESOURCE_MAP 详细映射

定义位置：[resource_load_status.py](../../xuansto-mcp-server/src/xuansto_mcp/tools/resource_load_status.py) L25-L72。

| Phase | 资源 ID | 类型 | 路径 |
|-------|---------|------|------|
| 0 | skill-config | config | .skill-config.yaml |
| 1 | agent-registry | reference | references/agent-registry.md |
| 1 | quality-gates | reference | references/quality-gates.md |
| 1 | brainstorm-workflow | workflow | workflows/brainstorming-workflow.md |
| 1 | agent-product-manager | agent | agents/product/product-manager.md |
| 1 | agent-orchestrator | agent | agents/orchestrator/orchestrator.md |
| 1 | agent-system-architect | agent | agents/product/system-architect.md |
| 2 | knowledge-general | knowledge | .knowledge/general/ |
| 2 | sdd-tdd-full | workflow | workflows/sdd-tdd-full.md |
| 2 | sdd-tdd-medium | workflow | workflows/sdd-tdd-medium.md |
| 2 | sdd-tdd-fast | workflow | workflows/sdd-tdd-fast.md |
| 2 | mcp-tools | reference | references/mcp-tools.md |
| 2 | workflow-phases | reference | references/workflow-phases.md |
| 2 | agent-registry-full | agent | agents/registry.yaml |
| 2 | progressive-loading | reference | references/progressive-loading.md |
| 3 | test-guidelines | reference | references/test-guidelines.md |
| 3 | coding-standards | reference | references/coding-standards.md |
| 3 | karpathy-guidelines | reference | references/karpathy-guidelines.md |
| 3 | security-guidelines | reference | references/security-guidelines.md |
| 3 | owasp-top10 | reference | references/owasp-top10-2026.md |
| 3 | acceptance-criteria | reference | references/acceptance-criteria.md |
| 3 | desktop-guidelines | reference | references/desktop-dev-guidelines.md |
| 3 | ipc-contracts | reference | references/ipc-contracts.md |
| 3 | knowledge-workflow | reference | references/knowledge-workflow-details.md |
| 3 | templates-dir | template | templates/ |
| 3 | agents-*-full (×13) | agent | agents/{layer}/ |

### 4.3 resource_load_status 工具职责

| Action | 职责 | 对加载阶段的影响 |
|--------|------|-----------------|
| `status` | 查询当前加载状态、可用资源、可用命令 | 不变 |
| `preload` | 预加载指定阶段资源（累积式，加载到目标阶段的所有资源） | 推进到目标阶段 |
| `cache` | 查询缓存状态（LRU 缓存，含 TTL 和内容哈希校验） | 不变 |
| `clear_cache` | 清理缓存 | 降级到 SKELETON |
| `loading_progress` | 查询各资源加载进度、功能可用性、Token 预算追踪 | 不变 |
| `token_report` | Token 使用报告 | 不变 |
| `disclosure_transition` | 返回阶段转换所需资源和估算 | 不变 |

### 4.4 工具可用性受加载阶段控制

| 加载阶段 | 可用工具 | 不可用工具的降级行为 |
|----------|---------|---------------------|
| SKELETON | resource_load_status, server_health, config_manage | 其他工具返回"当前阶段不可用"提示，建议执行 preload |
| FUNCTIONAL | + knowledge_search, knowledge_inject(list_available), workflow_dispatch, agent_status, session_manage, project_init, decision_log(log) | 写入/分析类工具不可用 |
| ENHANCED | + knowledge_inject(全部), quality_gate_check, spec_drift_detect, token_budget, context_compress, hook_manage, metrics_report | 安全扫描/代码简化不可用 |
| FULL | 全部 20 个工具 | 无 |

### 4.5 工具调用时自动推进加载阶段

当用户调用某个工具时，系统会自动检测该工具所需的最小加载阶段，并在必要时自动推进：

```
用户调用 knowledge_progressive_search
  → 检测到需要 Phase 2 (Enhanced)
  → 自动调用 resource_load_status(preload, target_phase=enhanced)
  → 加载 Phase 2 资源
  → 执行 knowledge_progressive_search
```

### 4.6 Token 预算与阶段降级

当 Token 使用率超过阈值时，渐进式加载系统自动降级（由 `token_budget.enforce` 触发）：

| Token 使用率 | 降级动作 | 披露通知 |
|------------|----------|----------|
| > 80% | FULL → ENHANCED，释放 P3 资源 | 必须通知用户 |
| > 95% | ENHANCED → FUNCTIONAL，释放 P2 资源 | 必须通知用户 |
| > 95% 且无活动 > 5 分钟 | FUNCTIONAL → SKELETON，释放 P1 资源 | 必须通知用户 |

### 4.7 DegradationManager 组件降级

定义位置：[degradation.py](../../xuansto-mcp-server/src/xuansto_mcp/core/degradation.py) L460-L491。

| 组件 | Level 1 (正常) | Level 2 (降级) | Level 3 (不可用) |
|------|---------------|---------------|-----------------|
| search_engine | chromadb | sqlite_fts | keyword |
| knowledge_base | full | workspace_only | no_knowledge |
| hooks | full_hooks | essential_only | no_hooks |
| resources | full_resources | cached_only | minimal |

整体降级级别取所有组件中最差级别：`L1_NORMAL` → `L2_LOCAL_SEMANTIC` → `L3_BM25_ONLY`。

---

## 5. Skill → MCP 交互协议

### 5.1 调用方式：Skill 命令 → MCP 工具调用链

Skill 命令通过 SKILL.md 中的路由规则映射到 MCP 工具调用链。每个命令可能触发一个或多个 MCP 工具的顺序调用：

| Skill 命令 | MCP 工具调用链 | 说明 |
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
| `/learn` | knowledge_search → knowledge_inject(inject) → session_manage(save) | 知识学习 |
| `/loop` | workflow_dispatch(start) → session_manage(save) → resource_load_status(status) → token_budget(status) → decision_log(log) | 循环开发 |
| `/sprint` | workflow_dispatch(start) → session_manage(save) → resource_load_status(preload) → token_budget(recommend) → project_init(detect_stack) | 冲刺开发 |

### 5.2 参数传递：命令参数 → MCP 工具参数映射

| 映射规则 | 源（Skill 命令参数） | 目标（MCP 工具参数） | 示例 |
|----------|-------------------|-------------------|------|
| 直接映射 | 命令参数名与工具参数名一致 | 直接传递 | `project_path` → `project_path` |
| 语义映射 | 命令参数名与工具参数名不同 | 按语义转换 | `--stack` → `stack` (project_init) |
| 默认值填充 | 命令未提供参数 | 使用工具默认值 | `top_k` 未指定 → 默认 5 |
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
  action: "retrieve"
  query: "python react project setup best practices"  ← 语义映射
  top_k: 5                    ← 默认值
  search_type: "hybrid"       ← 默认值

workflow_dispatch:
  action: "start"             ← 命令固定
  workflow: "sdd-tdd-full"    ← 默认值
  project_path: "."           ← 环境推断
```

### 5.3 结果处理：MCP 工具返回值 → Skill 输出格式化

MCP 工具的返回值统一包装为以下 JSON 结构：

```json
{
  "error": false,
  "data": { ... },
  "degradation_level": "chromadb|sqlite_fts5|keyword_fallback|inline|minimal|none",
  "hook_errors": []
}
```

错误响应：

```json
{
  "error": true,
  "error_code": "ERR_XXX",
  "message": "具体错误描述",
  "details": { ... }
}
```

#### 结果处理流程

```
MCP 工具返回值
  ↓
1. 解包 make_success_response / make_error_response
  ↓
2. 提取 data 字段
  ↓
3. 格式化为 Skill 输出
  ├── 成功：格式化关键信息 + 可操作建议
  ├── 降级：添加降级提示 + 替代方案
  └── 错误：错误码 + 错误描述 + 恢复建议
```

### 5.4 降级回退链

定义位置：[degradation.py](../../xuansto-mcp-server/src/xuansto_mcp/core/degradation.py) L1088-L1109 `FALLBACK_MAP`。

每个工具都有三级降级链：

```
MCP Tool（主路径）
  ↓ 失败
脚本降级（run_script_fallback）
  ↓ 失败
内嵌降级（_inline_* 函数）
  ↓ 失败
最小响应（_minimal_response）
```

| MCP 工具 | 脚本降级 | 内嵌降级函数 |
|---------|----------|-------------|
| skill_analyze | skill-test.py --analyze | _inline_skill_analyze |
| knowledge_search | knowledge-server.py --search | _inline_knowledge_search |
| knowledge_inject | knowledge-server.py --inject | _inline_knowledge_inject |
| quality_gate_check | skill-test.py --gate | _inline_quality_gate |
| spec_drift_detect | spec-drift-detector.py | _inline_spec_drift |
| security_scan | agentic-security-scanner.py | _inline_agentic_scan |
| code_simplify | code-simplifier.py | _inline_simplify |
| session_manage | init-session.py / session-catchup.py / session-persist.py | _inline_session_manage |
| workflow_dispatch | project-initializer.py | _load_workflow |
| agent_status | skill-test.py --agents | _inline_agent_status |
| hook_manage | check-encoding.py / token-budget-guard.py / session-persist.py | _inline_hook_manage |
| resource_load_status | resource_state.json 文件系统 | _inline_resource_load_status |
| context_compress | context-compressor.py | _inline_context_compress |
| server_health | health-checker.py | _inline_server_health |
| decision_log | decision-log.py | _inline_decision_log |
| token_budget | token-budget-guard.py | _inline_token_budget |
| project_init | project-initializer.py | _inline_project_init |
| agent_manage | — | _inline_agent_manage |
| metrics_report | test-reporter.py | _inline_metrics_report |
| config_manage | — | _inline_config_manage |

### 5.5 错误码映射

| MCP 错误码 | 数值 | Skill 输出 | 恢复建议 |
|-----------|------|----------|----------|
| PARSE_ERROR | -32700 | 请求解析失败 | 检查参数格式 |
| INVALID_REQUEST | -32600 | 无效请求 | 检查必填参数 |
| METHOD_NOT_FOUND | -32601 | 未知工具 | 检查工具名称 |
| INVALID_PARAMS | -32602 | 参数无效 | 检查参数类型和范围 |
| INTERNAL_ERROR | -32603 | 内部错误 | 重试或降级为脚本调用 |
| VALIDATION_ERROR | -32100 | 输入验证失败 | 修正输入内容 |
| NOT_FOUND | -32102 | 资源不存在 | 检查 ID 是否正确 |
| VERSION_CONFLICT | -32103 | 版本冲突 | 重新获取最新版本后重试 |
| RATE_LIMITED | -32104 | 速率限制 | 等待后重试 |
| SENSITIVE_CONTENT | -32106 | 包含敏感信息 | 移除 API 密钥/密码等 |

---

## 附录 A：Hook 拦截引擎

### 16 个内嵌 Hook

| Hook 名称 | 触发时机 | 功能 | Profile 包含 |
|-----------|---------|------|-------------|
| security-block | pre | 安全阻断（检测危险命令模式） | minimal, standard, strict |
| dangerous-cmd-confirm | pre | 危险命令确认 | strict |
| auto-format | post | 自动格式化 | standard, strict |
| console-log-detect | pre | 检测 console.log/print | standard, strict |
| type-check | pre | 类型检查 | strict |
| git-status-check | pre | Git 状态检查 | standard, strict |
| decision-log-persist | post | 决策日志持久化 | strict |
| token-budget-check | pre | Token 预算检查 | standard, strict |
| encoding-check | pre | 编码检查 | standard, strict |
| load-context | pre | 加载上下文 | standard, strict |
| kb-health-check | pre | 知识库健康检查 | standard, strict |
| platform-detect | pre | 平台检测 | standard, strict |
| session-save | post | 会话保存 | minimal, standard, strict |
| experience-precipitate | post | 经验沉淀 | standard, strict |
| pattern-detect | pre | 模式检测 | strict |
| save-state | post | 状态保存 | strict |

### Profile 配置

| Profile | Hook 数量 | 包含 |
|---------|----------|------|
| minimal | 2 | security-block, session-save |
| standard | 10 | security-block, token-budget-check, auto-format, encoding-check, load-context, kb-health-check, session-save, git-status-check, experience-precipitate, save-state |
| strict | 16 | 全部 Hook |

## 附录 B：版本兼容矩阵

| Skill 版本 | 最低 MCP Server 版本 | API 版本 | 工具数量 | Resource 数量 |
|-----------|-------------------|---------|---------|-------------|
| 8.0.0 | 8.0.0 | 3.0.0 | 20 | 22 |
| 7.0.0 | 7.0.0 | 2.0.0 | 15 | 3 |
| 6.0.0 | 6.0.0 | 1.0.0 | 13 | 0 |

## 附录 C：配置热更新

MCP Server 支持配置文件热更新，无需重启：

| 配置文件 | 热更新方式 | 检测间隔 |
|---------|----------|---------|
| .xuansto-config.yaml | watchfiles（优先）或轮询 | 5 秒 |
| fallback_config.yaml | watchfiles（优先）或轮询 | 5 秒 |
| hooks.json | 随配置重载 | — |

## 附录 D：启动恢复流程

MCP Server 启动时自动恢复以下状态：

1. `init_db()` — 初始化 SQLite 数据库
2. `restore_on_startup()` — 恢复会话状态
3. `workflow_load_on_startup()` — 恢复工作流状态
4. `agent_load_on_startup()` — 恢复 Agent 实例状态
5. `health_load_on_startup()` — 恢复健康检查状态
6. `metrics_load_on_startup()` — 恢复工具指标
7. `degradation_load_on_startup()` — 恢复降级状态
8. `start_fallback_watcher()` — 启动降级配置监听
9. `start_config_watcher()` — 启动配置热更新监听
