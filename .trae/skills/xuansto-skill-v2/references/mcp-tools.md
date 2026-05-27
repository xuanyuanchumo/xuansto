# MCP工具详细参考

> 本文件由SKILL.md按需加载，不需要时不会占用上下文

## 目录

1. [skill_analyze](#skill_analyze)
2. [knowledge_search](#knowledge_search)
3. [quality_gate_check](#quality_gate_check)
4. [spec_drift_detect](#spec_drift_detect)
5. [security_scan](#security_scan)
6. [code_simplify](#code_simplify)
7. [session_manage](#session_manage)
8. [workflow_dispatch](#workflow_dispatch)
9. [agent_status](#agent_status)
10. [agent_manage](#agent_manage)
11. [hook_manage](#hook_manage)
12. [resource_load_status](#resource_load_status)
13. [context_compress](#context_compress)
14. [server_health](#server_health)
15. [decision_log](#decision_log)
16. [token_budget](#token_budget)
17. [knowledge_inject](#knowledge_inject)
18. [project_init](#project_init)
19. [metrics_report](#metrics_report)
20. [audit_query](#audit_query)
21. [resource_subscribe](#resource_subscribe)

---

## skill_analyze

分析技能项目结构，提取YAML元数据、目录结构、Agent注册表、脚本依赖和验证问题。

**参数：**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| skill_path | str | 必填 | 技能根目录路径 |
| include_scripts | bool | True | 是否分析scripts目录 |
| include_agents | bool | True | 是否分析agents目录 |
| depth | str | "basic" | 分析深度: basic 或 full |

**完整返回值JSON Schema：**
```json
{
  "status": "success",
  "data": {
    "metadata": {
      "name": "xuansto-skill-v2",
      "version": "7.0.0",
      "agents_summary": "13 layers / 57 agents (via MCP v2)",
      "tags": ["xuansto", "multi-agent", "sdd", "tdd"]
    },
    "structure": {
      "root": "/path/to/skill",
      "directories": ["references", "scripts", "agents"],
      "file_count": 72,
      "total_lines": 15420
    },
    "agents": {
      "total": 57,
      "layers": 13,
      "by_layer": {
        "orchestration": 3,
        "product": 4,
        "design": 4,
        "engineering": 6
      }
    },
    "dependencies": {
      "mcp_server": "xuansto-mcp-server>=4.0.0",
      "scripts": ["knowledge-server.py", "skill-test.py", "agentic-security-scanner.py"],
      "python_version": ">=3.10"
    },
    "issues": [
      {
        "severity": "WARN",
        "code": "MISSING_SCRIPT",
        "message": "Script not found: scripts/context-compressor.py",
        "path": "scripts/context-compressor.py"
      }
    ]
  },
  "metadata": {
    "tool": "skill_analyze",
    "latency_ms": 234,
    "degraded": false
  }
}
```

**错误码定义：**
| 错误码 | 说明 | 处理建议 |
|--------|------|----------|
| INVALID_INPUT | skill_path为空或不存在 | 检查路径是否正确 |
| NOT_FOUND | 技能目录不存在 | 确认skill_path指向有效目录 |
| PARSE_ERROR | YAML元数据解析失败 | 检查SKILL.md的frontmatter格式 |
| DEGRADED | 降级模式执行 | 检查MCP Server连接 |
| TIMEOUT | 分析超时(depth=full时可能) | 改用depth="basic"或缩小分析范围 |

**降级脚本路径：** `scripts/skill-test.py --analyze`

**调用示例：**
```
调用: skill_analyze(skill_path="/path/to/project", depth="full", include_agents=True)
响应: {status: "success", data: {metadata: {...}, structure: {file_count: 72, ...}, agents: {total: 57}, issues: []}, ...}
```

## knowledge_search

三层知识库混合检索引擎。支持retrieve/inject/precipitate三种操作。

**参数：**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| action | str | "retrieve" | 操作类型: retrieve, inject, precipitate |
| query | str\|None | None | 搜索查询文本 |
| top_k | int | 5 | 返回结果数量上限(1-50) |
| search_type | str | "hybrid" | 搜索策略: hybrid, semantic_only, keyword_only |
| scope | str\|None | None | 限定搜索范围: general, workspace, experience |
| min_confidence | float | 0.0 | 最低置信度阈值(0.0-1.0) |
| content | str\|None | None | 注入的知识内容(inject时使用) |
| knowledge_type | str | "general" | 知识类型(inject时使用): general, workspace, experience |
| metadata | dict\|None | None | 附加元数据(inject时使用) |
| pattern_ids | list\|None | None | 模式ID列表(precipitate时使用) |

**降级链：** ChromaDB → SQLite FTS5 → keyword_fallback

**action说明：**
- `retrieve`: 三层知识库混合检索，返回匹配结果列表
- `inject`: 将知识内容注入知识库，底层通过knowledge_add实现
- `precipitate`: 从已有经验中沉淀模式，底层通过experience_precipitator.py实现

**retrieve返回值JSON Schema：**
```json
{
  "status": "success",
  "data": {
    "results": [
      {
        "id": "kb-001",
        "content": "React项目初始化最佳实践：使用Vite...",
        "source": "experience/react-init.md",
        "confidence": 0.92,
        "metadata": {
          "category": "project-init",
          "tags": ["react", "vite", "typescript"],
          "created_at": "2025-01-15"
        }
      }
    ],
    "total_matches": 12,
    "search_type_used": "hybrid",
    "degraded": false
  },
  "metadata": {
    "tool": "knowledge_search",
    "latency_ms": 89,
    "degraded": false
  }
}
```

**inject返回值JSON Schema：**
```json
{
  "status": "success",
  "data": {
    "action": "inject",
    "id": "kb-inj-20250122-001",
    "knowledge_type": "experience",
    "scope": "workspace",
    "content_preview": "Vite+React+TS组合初始化效率高...",
    "metadata_saved": {
      "category": "project-init",
      "tags": ["react", "vite"],
      "injected_at": "2025-01-22T14:30:00Z"
    },
    "indexed": true
  },
  "metadata": {
    "tool": "knowledge_search",
    "latency_ms": 45,
    "degraded": false
  }
}
```

**precipitate返回值JSON Schema：**
```json
{
  "status": "success",
  "data": {
    "action": "precipitate",
    "patterns": [
      {
        "id": "pat-001",
        "experience_type": "project-init",
        "pattern": "Vite+React+TS组合在中小型项目中初始化效率最高",
        "confidence": 0.88,
        "occurrence_count": 5,
        "scope": "workspace",
        "first_seen": "2025-01-10T08:00:00Z",
        "last_seen": "2025-01-22T14:30:00Z"
      },
      {
        "id": "pat-002",
        "experience_type": "error-recovery",
        "pattern": "TypeScript严格模式应在项目初期启用，后期启用成本高",
        "confidence": 0.82,
        "occurrence_count": 3,
        "scope": "general",
        "first_seen": "2025-01-12T10:00:00Z",
        "last_seen": "2025-01-20T16:00:00Z"
      }
    ],
    "total_patterns": 2,
    "min_confidence_used": 0.7,
    "scope_filtered": "workspace"
  },
  "metadata": {
    "tool": "knowledge_search",
    "latency_ms": 120,
    "degraded": false
  }
}
```

**错误码定义：**
| 错误码 | 说明 | 处理建议 |
|--------|------|----------|
| INVALID_INPUT | query为空或top_k超出范围 | 检查参数类型和范围 |
| NO_RESULTS | 无匹配结果 | 扩大搜索范围或降低min_confidence |
| DB_UNAVAILABLE | ChromaDB不可用 | 自动降级到SQLite FTS5 |
| DEGRADED | 降级模式执行(关键词检索) | 检查ChromaDB服务状态 |
| TIMEOUT | 检索超时 | 减少top_k或简化query |
| INJECT_FAILED | 知识注入失败(inject) | 检查content和knowledge_type参数 |
| PRECIPITATE_NO_PATTERNS | 无可沉淀的模式(precipitate) | 降低min_confidence或扩大scope |
| DUPLICATE_CONTENT | 注入内容已存在(inject) | 检查是否重复注入相同内容 |

**降级脚本路径：** `scripts/knowledge-server.py --search` (retrieve) / `scripts/knowledge_server/kb_client.py` (inject) / `scripts/knowledge_server/experience_precipitator.py` (precipitate)

**调用示例：**
```
调用: knowledge_search(action="retrieve", query="React项目初始化最佳实践", top_k=5, search_type="hybrid", scope="experience")
响应: {status: "success", data: {results: [{id: "kb-001", content: "...", confidence: 0.92}], total_matches: 12, search_type_used: "hybrid"}, ...}

调用: knowledge_search(action="inject", content="Vite+React+TS组合初始化效率高", knowledge_type="experience", scope="workspace", metadata={"category": "project-init", "tags": ["react", "vite"]})
响应: {status: "success", data: {action: "inject", id: "kb-inj-20250122-001", knowledge_type: "experience", scope: "workspace", content_preview: "Vite+React+TS组合初始化效率高...", indexed: true}, ...}

调用: knowledge_search(action="precipitate", min_confidence=0.7, scope="workspace")
响应: {status: "success", data: {action: "precipitate", patterns: [{id: "pat-001", experience_type: "project-init", pattern: "Vite+React+TS组合...", confidence: 0.88, occurrence_count: 5}], total_patterns: 2, min_confidence_used: 0.7}, ...}
```

## quality_gate_check

54项质量门禁检查。

**参数：**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| gate_ids | list\|None | None | 要检查的门禁ID列表，为空则检查全部 |
| phase | str\|None | None | 按阶段过滤门禁(0-8) |
| project_path | str | "." | 项目根目录路径 |
| severity_filter | str | "all" | 严重级别过滤: all, BLOCK, WARN |
| force_refresh | bool | False | 强制刷新缓存，忽略文件哈希缓存 |

**阶段映射：**
- Phase 0: DESIGN-SYSTEM-COMPLETE, ANTI-PATTERN-CHECK
- Phase 4: GATE-007, TEST-PASS, FILE-ENCODING
- Phase 5: AI-PENTEST, SPEC-CONSISTENCY
- Phase 7: SIMPLIFICATION-BEHAVIOR, GATE-015

**完整返回值JSON Schema：**
```json
{
  "status": "success",
  "data": {
    "gates_checked": 6,
    "gates_passed": 5,
    "gates_failed": 1,
    "results": [
      {
        "gate_id": "TEST-PASS",
        "status": "PASS",
        "severity": "BLOCK",
        "message": "All 42 tests passed. Coverage: 87.3%",
        "details": {
          "total_tests": 42,
          "passed": 42,
          "failed": 0,
          "coverage_pct": 87.3
        }
      },
      {
        "gate_id": "FILE-ENCODING",
        "status": "FAIL",
        "severity": "BLOCK",
        "message": "2 files have BOM markers",
        "details": {
          "offending_files": ["src/utils.ts", "src/config.ts"],
          "issue": "UTF-8 BOM detected"
        }
      }
    ],
    "phase": "4",
    "can_proceed": false
  },
  "metadata": {
    "tool": "quality_gate_check",
    "latency_ms": 156,
    "degraded": false
  }
}
```

**错误码定义：**
| 错误码 | 说明 | 处理建议 |
|--------|------|----------|
| INVALID_INPUT | gate_ids格式错误或phase超出范围 | 检查参数类型和范围 |
| NOT_FOUND | 指定的gate_id不存在 | 检查门禁ID拼写 |
| GATE_BLOCKED | 存在BLOCK级别门禁失败 | 根据失败详情修复后重新检查 |
| DEGRADED | 降级模式执行 | 检查MCP Server连接 |
| PROJECT_NOT_FOUND | project_path无效 | 确认项目路径正确 |

**降级脚本路径：** `scripts/skill-test.py --gate`

**调用示例：**
```
调用: quality_gate_check(gate_ids=["TEST-PASS", "FILE-ENCODING"], project_path="/path/to/project")
响应: {status: "success", data: {gates_checked: 2, gates_passed: 1, gates_failed: 1, results: [{gate_id: "TEST-PASS", status: "PASS", ...}, {gate_id: "FILE-ENCODING", status: "FAIL", ...}], can_proceed: false}, ...}
```

## spec_drift_detect

规格文档与代码实现偏差检测。

**参数：**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| spec_dir | str | ".trae/specs" | 规格文档目录 |
| src_dir | str | "." | 源代码目录 |

**完整返回值JSON Schema：**
```json
{
  "status": "success",
  "data": {
    "total_specs": 8,
    "drifts_detected": 2,
    "drifts": [
      {
        "spec_file": "user-auth.md",
        "spec_requirement": "密码必须包含大小写字母+数字+特殊字符",
        "implementation": "src/auth/validator.ts",
        "drift_type": "MISMATCH",
        "severity": "HIGH",
        "description": "实现中缺少特殊字符验证",
        "suggestion": "在validator.ts中添加特殊字符正则检查"
      }
    ],
    "coverage_pct": 75.0
  },
  "metadata": {
    "tool": "spec_drift_detect",
    "latency_ms": 312,
    "degraded": false
  }
}
```

**错误码定义：**
| 错误码 | 说明 | 处理建议 |
|--------|------|----------|
| INVALID_INPUT | spec_dir或src_dir不存在 | 检查目录路径 |
| NO_SPECS | 规格目录为空 | 确认规格文档已编写 |
| PARSE_ERROR | 规格文档解析失败 | 检查规格文档格式 |
| DEGRADED | 降级模式执行 | 检查MCP Server连接 |
| TIMEOUT | 检测超时(大型项目) | 缩小src_dir范围 |

**降级脚本路径：** `scripts/spec-drift-detector.py`

**调用示例：**
```
调用: spec_drift_detect(spec_dir=".trae/specs", src_dir="src")
响应: {status: "success", data: {total_specs: 8, drifts_detected: 2, drifts: [{spec_file: "user-auth.md", drift_type: "MISMATCH", severity: "HIGH", ...}], coverage_pct: 75.0}, ...}
```

## security_scan

OWASP Agentic Top 10 + 依赖漏洞扫描。

**参数：**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| target | str | "." | 目标扫描目录 |
| severity_threshold | str | "medium" | 最低报告严重级别: critical, high, medium, low |
| include_agentic | bool | True | 是否包含OWASP Agentic Top 10检查 |
| include_dependency | bool | True | 是否包含依赖漏洞扫描 |

**完整返回值JSON Schema：**
```json
{
  "status": "success",
  "data": {
    "total_findings": 5,
    "by_severity": {
      "critical": 0,
      "high": 1,
      "medium": 3,
      "low": 1
    },
    "findings": [
      {
        "id": "SEC-001",
        "title": "SQL注入风险",
        "severity": "high",
        "category": "OWASP-A03",
        "file": "src/db/query.ts",
        "line": 42,
        "description": "使用字符串拼接构建SQL查询",
        "remediation": "使用参数化查询替代字符串拼接",
        "references": ["https://owasp.org/Top10/A03_2021-Injection/"]
      }
    ],
    "agentic_findings": 1,
    "dependency_findings": 2,
    "scan_duration_ms": 1847
  },
  "metadata": {
    "tool": "security_scan",
    "latency_ms": 1847,
    "degraded": false
  }
}
```

**错误码定义：**
| 错误码 | 说明 | 处理建议 |
|--------|------|----------|
| INVALID_INPUT | target路径无效或severity_threshold错误 | 检查参数类型和范围 |
| NOT_FOUND | 扫描目标不存在 | 确认target路径正确 |
| SCAN_ERROR | 扫描引擎内部错误 | 重试或检查目标文件完整性 |
| DEGRADED | 降级模式执行(内嵌扫描) | 检查MCP Server连接 |
| TIMEOUT | 扫描超时(大型项目) | 缩小target范围或提高severity_threshold |

**降级脚本路径：** `scripts/agentic-security-scanner.py`

**调用示例：**
```
调用: security_scan(target="src", severity_threshold="medium", include_agentic=True, include_dependency=True)
响应: {status: "success", data: {total_findings: 5, by_severity: {critical: 0, high: 1, medium: 3, low: 1}, findings: [{id: "SEC-001", title: "SQL注入风险", severity: "high", ...}], ...}, ...}
```

## code_simplify

代码简化分析。

**参数：**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| target | str | 必填 | 目标文件或目录路径 |
| scope | str | "recent" | 扫描范围: file, dir, recent |
| include_dedup | bool | True | 是否包含重复代码检测 |

**完整返回值JSON Schema：**
```json
{
  "status": "success",
  "data": {
    "total_suggestions": 8,
    "by_type": {
      "dead_code": 3,
      "duplication": 2,
      "complexity": 2,
      "naming": 1
    },
    "suggestions": [
      {
        "id": "SIMP-001",
        "type": "dead_code",
        "file": "src/utils/helpers.ts",
        "line_start": 45,
        "line_end": 52,
        "description": "未使用的函数 processLegacyData",
        "safety": "SAFE",
        "action": "删除整个函数",
        "estimated_reduction": 8
      },
      {
        "id": "SIMP-002",
        "type": "duplication",
        "files": ["src/auth/validator.ts", "src/user/validator.ts"],
        "description": "重复的邮箱验证逻辑",
        "safety": "SAFE",
        "action": "提取为共享工具函数",
        "estimated_reduction": 15
      }
    ],
    "total_lines_reducible": 42,
    "safe_count": 6,
    "caution_count": 2
  },
  "metadata": {
    "tool": "code_simplify",
    "latency_ms": 567,
    "degraded": false
  }
}
```

**错误码定义：**
| 错误码 | 说明 | 处理建议 |
|--------|------|----------|
| INVALID_INPUT | target路径无效或scope错误 | 检查参数类型和范围 |
| NOT_FOUND | 目标文件/目录不存在 | 确认target路径正确 |
| PARSE_ERROR | 代码解析失败 | 检查文件语法是否正确 |
| DEGRADED | 降级模式执行(内嵌simplify+dedup) | 检查MCP Server连接 |
| TIMEOUT | 分析超时(大型目录) | 改用scope="file"或缩小target |

**降级脚本路径：** `scripts/code-simplifier.py`

**调用示例：**
```
调用: code_simplify(target="src/utils", scope="dir", include_dedup=True)
响应: {status: "success", data: {total_suggestions: 8, by_type: {dead_code: 3, duplication: 2, ...}, suggestions: [{id: "SIMP-001", type: "dead_code", safety: "SAFE", ...}], ...}, ...}
```

## session_manage

会话状态管理。

**参数：**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| action | str | 必填 | 操作类型: save, load, list, detect, verify, track, restore |
| completed_tasks | list\|None | None | 已完成任务列表(save时使用) |
| pending_tasks | list\|None | None | 未完成任务列表(save/track时使用) |
| decisions | list\|None | None | 关键决策列表(save/track时使用) |
| experience | list\|None | None | 经验沉淀列表(save时使用) |
| error_log | list\|None | None | 错误日志(detect时使用) |
| pattern_path | str\|None | None | 模式文件路径(verify时使用) |
| success | bool | True | 验证是否成功(verify时使用) |
| current_phase | int\|None | None | 当前阶段编号(track时使用) |
| current_task | str\|None | None | 当前任务描述(track时使用) |

**完整返回值JSON Schema：**
```json
{
  "status": "success",
  "data": {
    "action": "save",
    "session_id": "sess-20250122-001",
    "saved_at": "2025-01-22T14:30:00Z",
    "state": {
      "current_phase": 4,
      "workflow_id": "wf-001",
      "completed_tasks": ["task-1", "task-2"],
      "pending_tasks": ["task-3", "task-4"],
      "decisions": [
        {
          "id": "ADR-001",
          "title": "选择React作为前端框架",
          "rationale": "团队经验+生态成熟",
          "timestamp": "2025-01-22T10:00:00Z"
        }
      ],
      "experience": [
        {
          "category": "project-init",
          "content": "Vite+React+TS组合初始化效率高",
          "confidence": 0.85
        }
      ]
    }
  },
  "metadata": {
    "tool": "session_manage",
    "latency_ms": 45,
    "degraded": false
  }
}
```

**错误码定义：**
| 错误码 | 说明 | 处理建议 |
|--------|------|----------|
| INVALID_INPUT | action不在允许列表中 | 使用save/load/list/detect/verify |
| NOT_FOUND | 会话不存在(load) | 确认session_id正确 |
| SAVE_ERROR | 会话保存失败 | 检查磁盘空间和权限 |
| VERIFY_FAILED | 模式验证失败 | 检查pattern_path和success参数 |
| DEGRADED | 降级模式执行(内存临时状态) | 检查MCP Server连接 |

**降级脚本路径：** `scripts/init-session.py` (save/init) / `scripts/session-catchup.py` (load/detect/restore) / `scripts/session-persist.py` (save/load/list 兜底)

**调用示例：**
```
调用: session_manage(action="save", completed_tasks=["task-1", "task-2"], pending_tasks=["task-3"], decisions=[{"id": "ADR-001", "title": "选择React"}])
响应: {status: "success", data: {action: "save", session_id: "sess-20250122-001", state: {current_phase: 4, completed_tasks: ["task-1", "task-2"], ...}}, ...}

调用: session_manage(action="load")
响应: {status: "success", data: {action: "load", session_id: "sess-20250122-001", state: {current_phase: 4, workflow_id: "wf-001", ...}}, ...}
```

## workflow_dispatch

工作流调度：启动/查询/中止工作流执行。

**参数：**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| action | str | 必填 | 操作类型: start, status, abort, phase, recover, snapshots |
| workflow | str\|None | None | 工作流名称(start时使用): sdd-tdd-full, sdd-tdd-medium, sdd-tdd-fast等 |
| project_path | str | "." | 项目根目录路径(start时使用) |
| workflow_id | str\|None | None | 工作流实例ID(status/abort/phase/recover/snapshots时使用) |
| phase_action | str\|None | None | 阶段操作(phase时使用): advance, current |
| snapshot_phase | int\|None | None | 恢复到指定阶段的快照(recover时使用) |

**完整返回值JSON Schema：**
```json
{
  "status": "success",
  "data": {
    "action": "start",
    "workflow_id": "wf-20250122-001",
    "workflow_name": "sdd-tdd-full",
    "current_phase": 0,
    "phases": [
      {"phase": 0, "name": "初始化", "status": "IN_PROGRESS"},
      {"phase": 1, "name": "需求分析", "status": "PENDING"},
      {"phase": 2, "name": "架构设计", "status": "PENDING"},
      {"phase": 3, "name": "测试先行", "status": "PENDING"},
      {"phase": 4, "name": "代码实现", "status": "PENDING"},
      {"phase": 5, "name": "测试验证", "status": "PENDING"},
      {"phase": 6, "name": "验收确认", "status": "PENDING"},
      {"phase": 7, "name": "持续重构", "status": "PENDING"},
      {"phase": 8, "name": "部署交付", "status": "PENDING"}
    ],
    "started_at": "2025-01-22T14:00:00Z"
  },
  "metadata": {
    "tool": "workflow_dispatch",
    "latency_ms": 78,
    "degraded": false
  }
}
```

**错误码定义：**
| 错误码 | 说明 | 处理建议 |
|--------|------|----------|
| INVALID_INPUT | action不在允许列表中或workflow名称无效 | 使用start/status/abort |
| NOT_FOUND | workflow_id不存在(status/abort) | 确认workflow_id正确 |
| ALREADY_RUNNING | 已有工作流在运行(start) | 先abort当前工作流或使用status查询 |
| ABORT_FAILED | 工作流中止失败 | 检查工作流状态后重试 |
| DEGRADED | 降级模式执行(内联Phase推进) | 检查MCP Server连接 |

**降级脚本路径：** `scripts/project-initializer.py` (start) / 内联Phase推进（status/abort，无独立脚本）

**调用示例：**
```
调用: workflow_dispatch(action="start", workflow="sdd-tdd-full", project_path="/path/to/project")
响应: {status: "success", data: {action: "start", workflow_id: "wf-20250122-001", current_phase: 0, phases: [...], ...}, ...}

调用: workflow_dispatch(action="status", workflow_id="wf-20250122-001")
响应: {status: "success", data: {action: "status", workflow_id: "wf-20250122-001", current_phase: 4, ...}, ...}

调用: workflow_dispatch(action="abort", workflow_id="wf-20250122-001")
响应: {status: "success", data: {action: "abort", workflow_id: "wf-20250122-001", aborted_at: "2025-01-22T15:00:00Z"}, ...}
```

## agent_status

Agent状态查询：列出全部Agent、按Phase查询、查询单个Agent详情。

**参数：**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| action | str | 必填 | 操作类型: list, by_phase, detail, create, match, assign, release, instance_status, destroy, schedule |
| phase | int\|None | None | 按阶段查询Agent(by_phase时使用, 0-8) |
| agent_name | str\|None | None | Agent名称(detail时使用) |
| agent_type | str\|None | None | Agent类型(create) |
| capabilities | list\|None | None | 能力列表(create/match) |
| agent_id | str\|None | None | Agent实例ID(assign/release/instance_status/destroy) |
| task | str\|None | None | 任务描述(assign) |

**完整返回值JSON Schema：**
```json
{
  "status": "success",
  "data": {
    "action": "by_phase",
    "phase": 4,
    "agents": [
      {
        "name": "Backend Developer",
        "layer": "engineering",
        "status": "AVAILABLE",
        "capabilities": ["API开发", "数据库操作", "业务逻辑实现"],
        "assigned_tasks": 2,
        "completed_tasks": 1,
        "definition_file": "agents/backend-developer.md"
      },
      {
        "name": "Frontend Developer",
        "layer": "engineering",
        "status": "BUSY",
        "capabilities": ["UI组件开发", "状态管理", "样式实现"],
        "assigned_tasks": 3,
        "completed_tasks": 0,
        "definition_file": "agents/frontend-developer.md"
      }
    ],
    "total_agents": 7,
    "available_count": 5
  },
  "metadata": {
    "tool": "agent_status",
    "latency_ms": 23,
    "degraded": false
  }
}
```

**错误码定义：**
| 错误码 | 说明 | 处理建议 |
|--------|------|----------|
| INVALID_INPUT | action不在允许列表中或phase超出范围 | 使用list/by_phase/detail，phase范围0-8 |
| NOT_FOUND | agent_name不存在 | 检查Agent名称拼写 |
| DEGRADED | 降级模式执行(静态注册表查询) | 检查MCP Server连接 |

**降级脚本路径：** 静态注册表查询 / `scripts/skill-test.py --agents` (兜底)

**调用示例：**
```
调用: agent_status(action="list")
响应: {status: "success", data: {action: "list", agents: [{name: "Orchestrator", layer: "orchestration", ...}, ...], total_agents: 57}, ...}

调用: agent_status(action="by_phase", phase=4)
响应: {status: "success", data: {action: "by_phase", phase: 4, agents: [{name: "Backend Developer", status: "AVAILABLE", ...}], total_agents: 7}, ...}

调用: agent_status(action="detail", agent_name="Security Auditor")
响应: {status: "success", data: {action: "detail", agent: {name: "Security Auditor", layer: "security", capabilities: [...], definition_file: "agents/security-auditor.md"}}, ...}
```

## agent_manage

Agent实例管理：创建/分配/释放/销毁Agent实例，查询实例状态，调度规划。从agent_status拆分出的独立工具，专注于实例生命周期管理。

**参数：**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| action | str | 必填 | 操作类型: create, assign, release, instance_status, destroy, schedule |
| agent_type | str\|None | None | Agent类型(create时使用)，如: developer, reviewer, tester |
| capabilities | list\|None | None | Agent能力列表(create时使用)，如: ['code_review', 'testing'] |
| agent_id | str\|None | None | Agent实例ID(assign/release/instance_status/destroy时使用) |
| task | str\|None | None | 分配的任务描述(assign时使用) |

**完整返回值JSON Schema：**
```json
{
  "status": "success",
  "data": {
    "action": "create",
    "agent_id": "agent-a1b2c3d4",
    "agent_type": "developer",
    "capabilities": ["code_review", "testing"],
    "status": "idle",
    "created_at": "2025-01-22T14:30:00+00:00",
    "last_active_at": "2025-01-22T14:30:00+00:00",
    "task_count": 0,
    "total_duration_ms": 0
  },
  "metadata": {
    "tool": "agent_manage",
    "latency_ms": 15,
    "degraded": false
  }
}
```

**错误码定义：**
| 错误码 | 说明 | 处理建议 |
|--------|------|----------|
| INVALID_INPUT | action不在允许列表中或缺少必要参数 | 使用create/assign/release/instance_status/destroy/schedule |
| NOT_FOUND | agent_id对应的实例不存在 | 确认agent_id正确 |
| RATE_LIMIT | Agent实例数量已达上限(20) | 释放或销毁不用的Agent实例 |
| PERMISSION | Agent正忙无法分配新任务 | 先release当前任务再assign |

**降级脚本路径：** 静态注册表查询 / `scripts/skill-test.py --agents` (兜底)

**调用示例：**
```
调用: agent_manage(action="create", agent_type="developer", capabilities=["code_review", "testing"])
响应: {status: "success", data: {action: "create", agent_id: "agent-a1b2c3d4", agent_type: "developer", capabilities: ["code_review", "testing"], status: "idle", ...}, ...}

调用: agent_manage(action="assign", agent_id="agent-a1b2c3d4", task="实现用户认证模块")
响应: {status: "success", data: {action: "assign", agent_id: "agent-a1b2c3d4", task: "实现用户认证模块", status: "busy", task_count: 1, ...}, ...}

调用: agent_manage(action="release", agent_id="agent-a1b2c3d4")
响应: {status: "success", data: {action: "release", agent_id: "agent-a1b2c3d4", status: "idle", completed_task: "实现用户认证模块", duration_ms: 15000, ...}, ...}

调用: agent_manage(action="instance_status", agent_id="agent-a1b2c3d4")
响应: {status: "success", data: {action: "instance_status", agent_id: "agent-a1b2c3d4", agent_type: "developer", status: "idle", task_count: 1, total_duration_ms: 15000, ...}, ...}

调用: agent_manage(action="destroy", agent_id="agent-a1b2c3d4")
响应: {status: "success", data: {action: "destroy", agent_id: "agent-a1b2c3d4", status: "destroyed", task_count: 1, total_duration_ms: 15000, ...}, ...}
```

## hook_manage

Hook管理：列出Hook配置、执行指定Hook。

**参数：**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| action | str | 必填 | 操作类型: list, execute |
| profile | str | "standard" | Hook配置级别: minimal, standard, strict |
| hook_name | str\|None | None | Hook名称(execute时使用) |
| context | dict\|None | None | 执行上下文(execute时使用) |

**完整返回值JSON Schema：**
```json
{
  "status": "success",
  "data": {
    "action": "list",
    "profile": "standard",
    "hooks": [
      {
        "name": "PhaseEnter",
        "trigger": "phase_transition",
        "pre_callbacks": ["validate_phase_prerequisites"],
        "post_callbacks": ["notify_agents", "preload_resources"],
        "enabled": true
      },
      {
        "name": "GatePass",
        "trigger": "gate_check_pass",
        "pre_callbacks": [],
        "post_callbacks": ["quality_gate_check"],
        "enabled": true
      },
      {
        "name": "GateFail",
        "trigger": "gate_check_fail",
        "pre_callbacks": [],
        "post_callbacks": ["log_failure", "suggest_fix"],
        "enabled": true
      },
      {
        "name": "SessionStart",
        "trigger": "session_init",
        "pre_callbacks": [],
        "post_callbacks": ["session_manage(load)"],
        "enabled": true
      },
      {
        "name": "SessionStop",
        "trigger": "session_end",
        "pre_callbacks": [],
        "post_callbacks": ["session_manage(save)"],
        "enabled": true
      }
    ],
    "total_hooks": 6,
    "enabled_count": 6
  },
  "metadata": {
    "tool": "hook_manage",
    "latency_ms": 12,
    "degraded": false
  }
}
```

**错误码定义：**
| 错误码 | 说明 | 处理建议 |
|--------|------|----------|
| INVALID_INPUT | action不在允许列表中或profile无效 | 使用list/execute，profile: minimal/standard/strict |
| NOT_FOUND | hook_name不存在 | 检查Hook名称拼写 |
| EXECUTION_ERROR | Hook执行失败 | 检查context参数；Hook失败不阻塞主流程 |
| DEGRADED | 降级模式执行(内联Hook执行) | 检查MCP Server连接 |

**降级脚本路径：** `scripts/check-encoding.py` (encoding-check) / `scripts/token-budget-guard.py` (token-budget-check) / `scripts/session-persist.py` (session-save) / 内联Hook执行（list，无独立脚本）

**调用示例：**
```
调用: hook_manage(action="list", profile="standard")
响应: {status: "success", data: {action: "list", profile: "standard", hooks: [{name: "PhaseEnter", trigger: "phase_transition", enabled: true, ...}, ...], total_hooks: 6}, ...}

调用: hook_manage(action="execute", hook_name="PhaseEnter", context={"from_phase": 3, "to_phase": 4})
响应: {status: "success", data: {action: "execute", hook_name: "PhaseEnter", result: "completed", pre_callbacks_result: ["prerequisites_ok"], post_callbacks_result: ["agents_notified", "resources_preloaded"]}, ...}
```

## resource_load_status

渐进式加载状态管理：查询资源加载状态、预加载指定Phase资源。

**参数：**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| action | str | 必填 | 操作类型: status, preload, cache, clear_cache, loading_progress |
| phase | int\|None | None | 目标阶段(0-8) |
| resource_ids | list\|None | None | 指定资源ID列表 |
| resource_uris | list\|None | None | 资源URI列表(preload时使用) |
| priority | str | "normal" | 预加载优先级(preload时使用): critical, normal, background |
| batch_mode | bool | False | 是否批量预加载模式(preload时使用)，批量模式并发加载多个资源 |

**完整返回值JSON Schema：**
```json
{
  "status": "success",
  "data": {
    "action": "preload",
    "phase": 4,
    "resources": [
      {
        "id": "ref-mcp-tools",
        "type": "reference",
        "path": "references/mcp-tools.md",
        "status": "LOADED",
        "size_kb": 12.5
      },
      {
        "id": "ref-workflow-phases",
        "type": "reference",
        "path": "references/workflow-phases.md",
        "status": "LOADED",
        "size_kb": 8.3
      },
      {
        "id": "agent-registry",
        "type": "agent",
        "path": "xuansto://references/agent-registry",
        "status": "LOADED",
        "size_kb": 45.2
      }
    ],
    "total_resources": 3,
    "loaded_count": 3,
    "total_size_kb": 66.0,
    "token_budget_used": 3200,
    "token_budget_remaining": 76800
  },
  "metadata": {
    "tool": "resource_load_status",
    "latency_ms": 34,
    "degraded": false
  }
}
```

**错误码定义：**
| 错误码 | 说明 | 处理建议 |
|--------|------|----------|
| INVALID_INPUT | action不在允许列表中或phase超出范围 | 使用status/preload，phase范围0-8 |
| NOT_FOUND | resource_ids中包含不存在的资源 | 检查资源ID拼写 |
| LOAD_ERROR | 资源加载失败 | 检查资源文件是否存在 |
| TOKEN_BUDGET_EXCEEDED | Token预算不足 | 使用context_compress压缩或减少加载量 |
| DEGRADED | 降级模式执行(内联状态检查) | 检查MCP Server连接 |

**降级脚本路径：** 内联状态检查（无独立脚本，直接读取文件系统）

**调用示例：**
```
调用: resource_load_status(action="status")
响应: {status: "success", data: {action: "status", resources: [{id: "ref-mcp-tools", status: "LOADED", ...}], token_budget_used: 3200, ...}, ...}

调用: resource_load_status(action="preload", phase=4, resource_ids=["ref-mcp-tools", "agent-registry"])
响应: {status: "success", data: {action: "preload", phase: 4, resources: [{id: "ref-mcp-tools", status: "LOADED", ...}], total_resources: 2, ...}, ...}
```

## context_compress

上下文压缩：支持semantic/selective/lossless三种策略。

**参数：**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| content | str | 必填 | 待压缩的文本内容 |
| strategy | str | "semantic" | 压缩策略: semantic, selective, lossless |
| target_tokens | int | 2000 | 目标Token数量(100-50000) |
| preserve_sections | list\|None | None | 必须保留的章节标题列表 |

**完整返回值JSON Schema：**
```json
{
  "status": "success",
  "data": {
    "original_tokens": 8500,
    "compressed_tokens": 1950,
    "compression_ratio": 0.23,
    "strategy_used": "semantic",
    "compressed_content": "## 项目摘要\n\n技术栈: React+TypeScript+Vite\n当前Phase: 4(代码实现)\n已完成: 初始化→需求→架构→测试先行\n关键决策: ADR-001(React选型), ADR-002(Monorepo)\n待完成: 用户认证模块, 数据看板模块\n...",
    "preserved_sections": ["关键决策", "待完成任务"],
    "quality_score": 0.91
  },
  "metadata": {
    "tool": "context_compress",
    "latency_ms": 234,
    "degraded": false
  }
}
```

**错误码定义：**
| 错误码 | 说明 | 处理建议 |
|--------|------|----------|
| INVALID_INPUT | content为空或strategy无效 | 检查参数类型和范围 |
| TARGET_TOO_SMALL | target_tokens过小无法保留关键信息 | 增大target_tokens或使用preserve_sections |
| COMPRESSION_FAILED | 压缩过程失败 | 改用lossless策略 |
| DEGRADED | 降级模式执行 | 检查MCP Server连接 |
| TIMEOUT | 压缩超时(内容过长) | 减少content长度或使用selective策略 |

**降级脚本路径：** `scripts/context-compressor.py`

**调用示例：**
```
调用: context_compress(content="...(8500 tokens of session summary)...", strategy="semantic", target_tokens=2000, preserve_sections=["关键决策", "待完成任务"])
响应: {status: "success", data: {original_tokens: 8500, compressed_tokens: 1950, compression_ratio: 0.23, strategy_used: "semantic", compressed_content: "## 项目摘要\n...", quality_score: 0.91}, ...}
```

## server_health

服务器健康检查与版本兼容性验证。

**参数：**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| action | str | "check" | 操作类型: check, version, status |
| include_details | bool | False | 是否返回详细工具状态信息 |

**完整返回值JSON Schema：**
```json
{
  "status": "success",
  "data": {
    "status": "HEALTHY",
    "version": "4.0.0",
    "api_version": "3.0.0",
    "uptime_seconds": 86400,
    "tools_available": 17,
    "degradation_level": "none",
    "last_check_timestamp": "2025-01-22T14:30:00Z"
  },
  "metadata": {
    "tool": "server_health",
    "latency_ms": 5,
    "degraded": false
  }
}
```

**action说明：**
- `check`: 执行完整健康检查，返回status/version/api_version/uptime_seconds/tools_available/degradation_level/last_check_timestamp
- `version`: 仅返回版本兼容性信息，返回version/api_version
- `status`: 返回服务运行状态概要，返回status/uptime_seconds/degradation_level

**include_details=True时额外返回：**
```json
{
  "tools_status": {
    "skill_analyze": "OK",
    "knowledge_search": "OK",
    "quality_gate_check": "OK",
    "spec_drift_detect": "OK",
    "security_scan": "OK",
    "code_simplify": "OK",
    "session_manage": "OK",
    "workflow_dispatch": "OK",
    "agent_status": "OK",
    "hook_manage": "OK",
    "resource_load_status": "OK",
    "context_compress": "OK",
    "server_health": "OK",
    "decision_log": "OK",
    "token_budget": "OK",
    "knowledge_inject": "OK",
    "project_init": "OK"
  },
  "memory_usage_mb": 128.5,
  "active_workflows": 1,
  "active_sessions": 2
}
```

**错误码定义：**
| 错误码 | 说明 | 处理建议 |
|--------|------|----------|
| UNAVAILABLE | MCP Server不可用 | 检查xuansto-mcp-server进程和配置 |
| TIMEOUT | 健康检查超时 | 检查Server负载和网络连接 |
| PARTIAL_DEGRADATION | 部分工具不可用 | 查看tools_status确认哪些工具降级 |
| VERSION_MISMATCH | Server版本不兼容 | 更新xuansto-mcp-server到>=4.0.0 |

**降级脚本路径：** `scripts/health-checker.py`

**调用示例：**
```
调用: server_health(action="check", include_details=True)
响应: {status: "success", data: {status: "HEALTHY", version: "4.0.0", api_version: "3.0.0", uptime_seconds: 86400, tools_available: 17, degradation_level: "none", last_check_timestamp: "2025-01-22T14:30:00Z", tools_status: {skill_analyze: "OK", ...}, memory_usage_mb: 128.5, ...}, ...}

调用: server_health(action="version")
响应: {status: "success", data: {version: "4.0.0", api_version: "3.0.0"}, ...}

调用: server_health(action="status")
响应: {status: "success", data: {status: "HEALTHY", uptime_seconds: 86400, degradation_level: "none"}, ...}
```

## decision_log

决策日志管理：记录决策条目、搜索决策、导出决策记录。

**参数：**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| action | str | 必填 | 操作类型: log, query, export |
| title | str\|None | None | 决策标题(log时使用) |
| description | str\|None | None | 决策描述(log时使用) |
| context | str\|None | None | 决策上下文(log时使用) |
| alternatives | list\|None | None | 备选方案列表(log时使用) |
| decision | str\|None | None | 最终决策(log时使用) |
| rationale | str\|None | None | 决策理由(log时使用) |
| impact | str\|None | None | 影响范围(log时使用) |
| decided_by | str\|None | None | 决策者(log时使用) |
| keyword | str\|None | None | 搜索关键词(query时使用) |
| tag | str\|None | None | 标签过滤(query时使用) |
| date_from | str\|None | None | 起始日期(ISO8601, query/export时使用) |
| date_to | str\|None | None | 截止日期(ISO8601, query/export时使用) |
| limit | int | 20 | 返回数量上限(query时使用, 1-100) |
| format | str | "json" | 导出格式(export时使用): json, markdown |

**完整返回值JSON Schema：**
```json
{
  "status": "success",
  "data": {
    "action": "log",
    "id": "ADR-20250122-001",
    "entry": {
      "id": "ADR-20250122-001",
      "title": "选择React作为前端框架",
      "description": "前端框架选型决策",
      "context": "新项目需要选择前端框架",
      "alternatives": ["Vue", "Angular", "Svelte"],
      "decision": "React + TypeScript",
      "rationale": "团队经验丰富，生态成熟",
      "impact": "影响前端架构和组件库选择",
      "decided_by": "Tech Lead",
      "tags": [],
      "created_at": "2025-01-22T14:30:00"
    },
    "total_decisions": 1
  },
  "metadata": {
    "tool": "decision_log",
    "latency_ms": 12,
    "degraded": false
  }
}
```

**错误码定义：**
| 错误码 | 说明 | 处理建议 |
|--------|------|----------|
| INVALID_INPUT | action不在允许列表中或log缺少title | 使用log/query/export，log需提供title |
| NOT_FOUND | 查询无结果 | 扩大搜索范围或调整关键词 |
| EXPORT_ERROR | 导出失败 | 检查format参数 |
| DEGRADED | 降级模式执行(内联JSON记录) | 检查MCP Server连接 |

**降级脚本路径：** `scripts/decision-log.py` / 内联JSON记录（兜底）

**调用示例：**
```
调用: decision_log(action="log", title="选择React作为前端框架", alternatives=["Vue", "Angular"], decision="React", rationale="团队经验丰富")
响应: {status: "success", data: {action: "log", id: "ADR-20250122-001", entry: {title: "选择React作为前端框架", decision: "React", ...}, total_decisions: 1}, ...}

调用: decision_log(action="query", keyword="React", limit=10)
响应: {status: "success", data: {results: [{id: "ADR-20250122-001", title: "选择React作为前端框架", ...}], total: 1, limit: 10}, ...}

调用: decision_log(action="export", format="markdown")
响应: {status: "success", data: {format: "markdown", content: "# Decision Log\n\n## ADR-20250122-001: 选择React作为前端框架\n...", total: 1}, ...}
```

## token_budget

Token预算管理：查询预算状态、设置预算、获取推荐、生成使用报告。

**参数：**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| action | str | 必填 | 操作类型: status, set_budget, recommend, report |
| total_budget | int\|None | None | 总Token预算(set_budget时使用, >=1000) |
| phase_allocations | dict\|None | None | 阶段分配(set_budget时使用) |
| project_size | str\|None | None | 项目规模(recommend时使用): small, medium, large |
| complexity | str\|None | None | 复杂度(recommend时使用): low, medium, high |
| team_size | int\|None | None | 团队人数(recommend时使用, 1-50) |
| period | str | "session" | 报告周期(report时使用): daily, weekly, session |

**完整返回值JSON Schema：**
```json
{
  "status": "success",
  "data": {
    "action": "status",
    "total_budget": 150000,
    "used": 45000,
    "remaining": 105000,
    "phase_allocations": {
      "0": 8000,
      "1": 15000,
      "2": 22000,
      "3": 12000,
      "4": 45000,
      "5": 18000,
      "6": 10000,
      "7": 12000,
      "8": 8000
    },
    "usage_by_phase": {
      "0": 5000,
      "1": 12000,
      "2": 18000,
      "4": 10000
    }
  },
  "metadata": {
    "tool": "token_budget",
    "latency_ms": 8,
    "degraded": false
  }
}
```

**错误码定义：**
| 错误码 | 说明 | 处理建议 |
|--------|------|----------|
| INVALID_INPUT | action不在允许列表中或set_budget缺少参数 | 使用status/set_budget/recommend/report |
| BUDGET_EXCEEDED | Token预算已耗尽 | 调整预算或压缩上下文 |
| DEGRADED | 降级模式执行(内联估算) | 检查MCP Server连接 |

**降级脚本路径：** `scripts/token-budget-guard.py` / 内联估算（兜底）

**调用示例：**
```
调用: token_budget(action="status")
响应: {status: "success", data: {total_budget: 150000, used: 45000, remaining: 105000, phase_allocations: {...}, ...}, ...}

调用: token_budget(action="set_budget", total_budget=200000, phase_allocations={"0": 10000, "1": 20000, "4": 60000})
响应: {status: "success", data: {total_budget: 200000, phase_allocations: {"0": 10000, "1": 20000, "4": 60000}, updated_at: "2025-01-22T14:30:00"}, ...}

调用: token_budget(action="recommend", project_size="medium", complexity="high", team_size=3)
响应: {status: "success", data: {recommended_total: 200000, recommended_allocations: {...}, project_size: "medium", complexity: "high", team_size: 3, adjusted_total: 240000, ...}, ...}

调用: token_budget(action="report", period="session")
响应: {status: "success", data: {period: "session", total_budget: 150000, total_used: 45000, remaining: 105000, usage_pct: 30.0, ...}, ...}
```

## knowledge_inject

将检索到的知识内容注入到当前会话上下文中，供Agent在执行任务时参考。

**参数：**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| action | str | 必填 | 操作类型: inject, preview, clear |
| content | str\|None | None | 注入内容(inject时使用) |
| scope | str\|None | "session" | 注入范围: session, workflow, global |
| source | str\|None | None | 知识来源标识(如knowledge_search结果ID) |
| priority | str\|None | "normal" | 优先级: low, normal, high |

**完整返回值JSON Schema：**
```json
{
  "status": "success",
  "data": {
    "action": "inject",
    "scope": "session",
    "injected_tokens": 1500,
    "source": "kb-result-abc123",
    "priority": "normal",
    "context_window_usage_pct": 35.0
  },
  "metadata": {
    "tool": "knowledge_inject",
    "latency_ms": 5,
    "degraded": false
  }
}
```

**错误码定义：**
| 错误码 | 说明 | 处理建议 |
|--------|------|----------|
| INVALID_INPUT | action不在允许列表中或inject缺少content | 使用inject/preview/clear，inject需提供content |
| CONTEXT_OVERFLOW | 注入内容超出上下文窗口 | 减少content长度或使用context_compress先压缩 |
| DEGRADED | 降级模式执行(内联注入) | 检查MCP Server连接 |

## project_init

项目初始化管理：创建项目、验证项目配置、检测技术栈。

**参数：**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| action | str | 必填 | 操作类型: create, validate, detect_stack |
| name | str\|None | None | 项目名称(create时使用) |
| description | str\|None | None | 项目描述(create时使用) |
| stack | list\|None | None | 技术栈列表(create时使用) |
| template | str\|None | None | 项目模板(create时使用) |
| directory | str\|None | None | 项目目录(create时使用) |
| project_path | str\|None | None | 项目路径(validate/detect_stack时使用) |

**完整返回值JSON Schema：**
```json
{
  "status": "success",
  "data": {
    "action": "create",
    "name": "my-project",
    "directory": "/path/to/my-project",
    "config_path": "/path/to/my-project/.xuansto-config.yaml",
    "stack": ["python", "react"],
    "template": "default"
  },
  "metadata": {
    "tool": "project_init",
    "latency_ms": 15,
    "degraded": false
  }
}
```

**错误码定义：**
| 错误码 | 说明 | 处理建议 |
|--------|------|----------|
| INVALID_INPUT | action不在允许列表中或create缺少name | 使用create/validate/detect_stack，create需提供name |
| NOT_FOUND | 项目路径不存在(validate/detect_stack) | 确认project_path正确 |
| CONFIG_EXISTS | 项目配置已存在(create) | 删除已有配置或选择其他目录 |
| DEGRADED | 降级模式执行(内联模板生成) | 检查MCP Server连接 |

**降级脚本路径：** `scripts/project-initializer.py` / 内联模板生成（兜底）

**调用示例：**
```
调用: project_init(action="create", name="my-project", stack=["python", "react"], template="default")
响应: {status: "success", data: {name: "my-project", directory: "/path/to/my-project", config_path: "/path/to/my-project/.xuansto-config.yaml", stack: ["python", "react"], template: "default"}, ...}

调用: project_init(action="validate", project_path="/path/to/my-project")
响应: {status: "success", data: {project_path: "/path/to/my-project", valid: true, issues: [], total_issues: 0, block_count: 0, warn_count: 0}, ...}

调用: project_init(action="detect_stack", project_path="/path/to/my-project")
响应: {status: "success", data: {project_path: "/path/to/my-project", detected_stacks: [{stack: "python", confidence: 0.75, markers_found: ["pyproject.toml"]}, {stack: "node", confidence: 1.0, markers_found: ["package.json"]}], primary_stack: "node", total_detected: 2}, ...}
```

## metrics_report

指标报告：查询工具调用指标(按工具名/时间/类型)，汇总统计(总调用/错误率/延迟分布/降级计数)。

**参数：**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| action | str | 必填 | 操作类型: query, summary |
| tool_name | str\|None | None | 工具名称(query时使用)，为空则查询全部工具 |
| time_range | str | "all" | 时间范围: 1h, 6h, 24h, 7d, all |
| metric_type | str | "all" | 指标类型: calls, errors, latency, all |

**完整返回值JSON Schema：**
```json
{
  "status": "success",
  "data": {
    "action": "query",
    "tools": {
      "skill_analyze": {
        "call_count": 42,
        "error_count": 1,
        "error_rate": 0.0238,
        "latency_p50_ms": 234.0,
        "latency_p95_ms": 567.0,
        "latency_p99_ms": 890.0,
        "latency_avg_ms": 280.5
      },
      "context_compress": {
        "call_count": 18,
        "error_count": 0,
        "error_rate": 0.0,
        "latency_p50_ms": 180.0,
        "latency_p95_ms": 320.0,
        "latency_p99_ms": 450.0,
        "latency_avg_ms": 195.2
      }
    },
    "total_tools": 2,
    "time_range": "all",
    "metric_type": "all"
  },
  "metadata": {
    "tool": "metrics_report",
    "latency_ms": 12,
    "degraded": false
  }
}
```

**错误码定义：**
| 错误码 | 说明 | 处理建议 |
|--------|------|----------|
| INVALID_INPUT | action不在允许列表中或参数无效 | 使用query/summary |
| DEGRADED | 降级模式执行(从持久化文件读取) | 检查MCP Server连接 |

**降级脚本路径：** 内联指标读取（从tool_metrics.json持久化文件读取）

**调用示例：**
```
调用: metrics_report(action="query", tool_name="skill_analyze", metric_type="all")
响应: {status: "success", data: {tools: {skill_analyze: {call_count: 42, error_count: 1, error_rate: 0.0238, latency_p50_ms: 234.0, ...}}, total_tools: 1, time_range: "all", metric_type: "all"}, ...}

调用: metrics_report(action="summary", time_range="24h")
响应: {status: "success", data: {total_calls: 256, total_errors: 3, overall_error_rate: 0.0117, latency_p50_ms: 195.0, latency_p95_ms: 450.0, latency_p99_ms: 780.0, latency_avg_ms: 230.5, total_tools: 15, top_tools: [{tool_name: "skill_analyze", call_count: 42, ...}, ...], degradation_counts: {level_1: 2, level_2: 0}, time_range: "24h"}, ...}
```

## audit_query

审计日志查询：查询MCP工具调用审计记录，支持按工具名和日期范围过滤。

**参数：**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| tool_name | str\|None | None | 按工具名称过滤，为空则查询全部工具 |
| date_range | str\|None | None | 日期范围过滤，格式: YYYY-MM-DD:YYYY-MM-DD |
| limit | int | 50 | 返回结果数量上限(1-500) |

**完整返回值JSON Schema：**
```json
{
  "status": "success",
  "data": {
    "entries": [
      {
        "timestamp": 1737548400.123,
        "tool": "skill_analyze",
        "params_summary": {"skill_path": "/path/to/project", "depth": "basic"},
        "success": true,
        "latency_ms": 234.56,
        "result_summary": {"error": false, "keys": ["metadata", "structure", "agents"]}
      },
      {
        "timestamp": 1737548395.456,
        "tool": "security_scan",
        "params_summary": {"target": "src", "severity_threshold": "medium"},
        "success": false,
        "latency_ms": 1847.23,
        "result_summary": {"error": true, "keys": ["error", "message"]}
      }
    ],
    "total_returned": 2,
    "filters": {
      "tool_name": null,
      "date_range": null,
      "limit": 50
    },
    "summary": {
      "success_count": 1,
      "error_count": 1,
      "unique_tools": 2,
      "tool_names": ["security_scan", "skill_analyze"]
    }
  },
  "metadata": {
    "tool": "audit_query",
    "latency_ms": 15,
    "degraded": false
  }
}
```

**错误码定义：**
| 错误码 | 说明 | 处理建议 |
|--------|------|----------|
| INVALID_INPUT | date_range格式错误或limit超出范围 | date_range格式应为YYYY-MM-DD:YYYY-MM-DD，limit范围1-500 |
| DEGRADED | 降级模式执行 | 检查MCP Server连接 |
| INTERNAL_ERROR | 审计日志读取失败 | 检查audit_log.jsonl文件完整性 |

**降级脚本路径：** 内联审计日志读取（直接读取audit_log.jsonl文件）

**调用示例：**
```
调用: audit_query(tool_name="skill_analyze", limit=10)
响应: {status: "success", data: {entries: [{timestamp: 1737548400.123, tool: "skill_analyze", success: true, latency_ms: 234.56, ...}], total_returned: 1, filters: {tool_name: "skill_analyze", date_range: null, limit: 10}, summary: {success_count: 1, error_count: 0, unique_tools: 1, tool_names: ["skill_analyze"]}}, ...}

调用: audit_query(date_range="2025-01-20:2025-01-22", limit=100)
响应: {status: "success", data: {entries: [{timestamp: ..., tool: "skill_analyze", ...}, {timestamp: ..., tool: "security_scan", ...}], total_returned: 15, filters: {tool_name: null, date_range: "2025-01-20:2025-01-22", limit: 100}, summary: {success_count: 12, error_count: 3, unique_tools: 5, tool_names: ["agent_status", "context_compress", "security_scan", "skill_analyze", "workflow_dispatch"]}}, ...}

调用: audit_query()
响应: {status: "success", data: {entries: [...], total_returned: 50, filters: {tool_name: null, date_range: null, limit: 50}, summary: {success_count: 45, error_count: 5, unique_tools: 8, tool_names: [...]}}, ...}
```

## resource_subscribe

资源订阅管理：订阅/取消订阅/列出资源变更通知。当订阅的资源(如xuansto://loading/status)发生变化时，服务器会通过MCP通知推送更新。

**参数：**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| action | str | 必填 | 操作类型: subscribe, unsubscribe, list |
| uri | str\|None | None | 资源URI(subscribe/unsubscribe时使用)，如: xuansto://loading/status |
| client_id | str\|None | None | 客户端标识(subscribe/unsubscribe时使用)，用于区分不同订阅者 |

**action说明：**
- `subscribe`: 订阅指定URI的资源变更通知。若未提供client_id，服务器自动生成唯一标识。订阅后，当该资源发生变化(如phase变更)时，服务器通过MCP `resource_updated` 通知推送更新
- `unsubscribe`: 取消订阅指定URI的资源变更通知。需要提供uri和client_id
- `list`: 列出当前所有订阅信息。若提供uri则返回该URI的订阅者列表，否则返回全部订阅

**subscribe返回值JSON Schema：**
```json
{
  "status": "success",
  "data": {
    "action": "subscribe",
    "uri": "xuansto://loading/status",
    "client_id": "client-a1b2c3d4",
    "subscribed": true
  },
  "metadata": {
    "api_version": "3.0.0"
  }
}
```

**unsubscribe返回值JSON Schema：**
```json
{
  "status": "success",
  "data": {
    "action": "unsubscribe",
    "uri": "xuansto://loading/status",
    "client_id": "client-a1b2c3d4",
    "unsubscribed": true
  },
  "metadata": {
    "api_version": "3.0.0"
  }
}
```

**list返回值JSON Schema：**
```json
{
  "status": "success",
  "data": {
    "action": "list",
    "subscriptions": {
      "xuansto://loading/status": ["client-a1b2c3d4", "client-e5f6g7h8"]
    },
    "total_uris": 1
  },
  "metadata": {
    "api_version": "3.0.0"
  }
}
```

**MCP通知事件：**
当资源发生变化时，服务器发送 `resource_updated` 类型的MCP通知：
```json
{
  "event_type": "resource_updated",
  "data": {
    "uri": "xuansto://loading/status",
    "subscribers": ["client-a1b2c3d4"],
    "event_data": {
      "event": "phase_transition",
      "from_phase": "skeleton",
      "to_phase": "functional",
      "loaded_resources": ["commands_detail", "workflow_phases", "quality_gates_summary", "core_agents"]
    }
  }
}
```

**支持的资源URI：**
| URI | 变更触发条件 |
|-----|-------------|
| xuansto://loading/status | 加载阶段(phase)变更时通知(skeleton→functional→enhanced→full) |

**错误码定义：**
| 错误码 | 说明 | 处理建议 |
|--------|------|----------|
| INVALID_INPUT | action不在允许列表中或缺少必要参数 | 使用subscribe/unsubscribe/list |
| ERR_VALIDATION | subscribe缺少uri或uri格式无效 | 确保uri以xuansto://开头 |

**调用示例：**
```
调用: resource_subscribe(action="subscribe", uri="xuansto://loading/status")
响应: {status: "success", data: {action: "subscribe", uri: "xuansto://loading/status", client_id: "client-a1b2c3d4", subscribed: true}, ...}

调用: resource_subscribe(action="subscribe", uri="xuansto://loading/status", client_id="my-client")
响应: {status: "success", data: {action: "subscribe", uri: "xuansto://loading/status", client_id: "my-client", subscribed: true}, ...}

调用: resource_subscribe(action="unsubscribe", uri="xuansto://loading/status", client_id="my-client")
响应: {status: "success", data: {action: "unsubscribe", uri: "xuansto://loading/status", client_id: "my-client", unsubscribed: true}, ...}

调用: resource_subscribe(action="list")
响应: {status: "success", data: {action: "list", subscriptions: {"xuansto://loading/status": ["client-a1b2c3d4"]}, total_uris: 1}, ...}

调用: resource_subscribe(action="list", uri="xuansto://loading/status")
响应: {status: "success", data: {action: "list", uri: "xuansto://loading/status", subscribers: ["client-a1b2c3d4"], count: 1}, ...}
```
