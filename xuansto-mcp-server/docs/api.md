# Xuansto MCP Server API 文档

> 版本: 2.5.0 | 工具数量: 13 | 资源数量: 27

本文档详细描述 xuansto-mcp-server 提供的全部 13 个 MCP 工具，包括参数说明、返回值结构、降级行为和使用示例。

---

## 目录

1. [skill_analyze](#1-skill_analyze)
2. [knowledge_search](#2-knowledge_search)
3. [quality_gate_check](#3-quality_gate_check)
4. [spec_drift_detect](#4-spec_drift_detect)
5. [security_scan](#5-security_scan)
6. [code_simplify](#6-code_simplify)
7. [session_manage](#7-session_manage)
8. [workflow_dispatch](#8-workflow_dispatch)
9. [agent_status](#9-agent_status)
10. [hook_manage](#10-hook_manage)
11. [resource_load_status](#11-resource_load_status)
12. [context_compress](#12-context_compress)
13. [server_health](#13-server_health)

---

## 通用响应结构

所有工具返回统一的响应格式：

**成功响应：**
```json
{
  "error": false,
  "data": { ... }
}
```

**降级响应：**
```json
{
  "error": false,
  "data": { ... },
  "degradation_level": "inline"
}
```

**错误响应：**
```json
{
  "error": true,
  "code": "PATH_NOT_FOUND",
  "message": "路径不存在: /xxx",
  "details": { ... }
}
```

---

## 1. skill_analyze

分析技能项目结构，提取 YAML 元数据、目录结构、Agent 注册表、脚本依赖和验证问题。

### 参数

| 名称 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| skill_path | string | 是 | — | 技能根目录路径 |
| include_scripts | boolean | 否 | true | 是否分析 scripts 目录 |
| include_agents | boolean | 否 | true | 是否分析 agents 目录 |
| depth | string | 否 | "basic" | 分析深度: `basic` 或 `full` |

### 返回值结构

```json
{
  "error": false,
  "data": {
    "metadata": {
      "name": "...",
      "version": "..."
    },
    "structure": {
      "root": "/path/to/skill",
      "exists": true,
      "directories": [
        { "name": "scripts", "files_count": 25 }
      ],
      "files_count": 5
    },
    "agents": [
      { "name": "Orchestrator", "layer": "编排层" }
    ],
    "dependencies": {
      "total_scripts": 25,
      "by_type": { "root": 10, "knowledge_server": 12 }
    },
    "issues": [
      { "type": "missing_file", "file": "SKILL.md", "severity": "critical" }
    ],
    "project_scale": "medium",
    "recommended_workflow": "sdd-tdd-medium",
    "scale_details": {
      "file_count": 50,
      "loc_count": 8000,
      "scale": "medium",
      "recommended_workflow": "sdd-tdd-medium",
      "workflow_phases": 6
    }
  }
}
```

### 降级行为

无降级链。路径不存在时返回 `PATH_NOT_FOUND` 错误。

### 使用示例

```json
{
  "skill_path": "/path/to/project",
  "include_scripts": true,
  "include_agents": true,
  "depth": "full"
}
```

---

## 2. knowledge_search

三层知识库（通用/工作区/经验）混合检索引擎。支持语义搜索(ChromaDB)、关键词搜索(SQLite FTS5)和混合模式，自动降级。同时支持 inject 注入知识和 precipitate 经验沉淀。

### 参数

| 名称 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| action | string | 否 | "retrieve" | 操作类型: `retrieve`, `inject`, `precipitate` |
| query | string \| null | 否 | null | 搜索查询文本（retrieve 时必填） |
| top_k | integer | 否 | 5 | 返回结果数量上限（1-50） |
| search_type | string | 否 | "hybrid" | 搜索策略: `hybrid`, `semantic_only`, `keyword_only` |
| scope | string \| null | 否 | null | 限定搜索范围: `general`, `workspace`, `experience` |
| min_confidence | float | 否 | 0.0 | 最低置信度阈值（0.0-1.0） |
| content | string \| null | 否 | null | 注入的知识内容（inject 时必填） |
| knowledge_type | string | 否 | "general" | 知识类型（inject 时使用）: `general`, `workspace`, `experience` |
| metadata | object \| null | 否 | null | 附加元数据（inject 时使用） |
| pattern_ids | array\<string\> \| null | 否 | null | 模式 ID 列表（precipitate 时必填） |

### 返回值结构

**retrieve 操作：**
```json
{
  "error": false,
  "data": {
    "results": [
      {
        "source": "general/patterns/observer-pattern.md",
        "content": "...",
        "match_type": "semantic",
        "relevance": 0.85
      }
    ],
    "total": 3,
    "strategy": "chromadb_semantic"
  },
  "degradation_level": "chromadb"
}
```

**inject 操作：**
```json
{
  "error": false,
  "data": {
    "injected_id": "injected-20260520T120000Z.md",
    "path": "/path/to/knowledge/general/injected-20260520T120000Z.md",
    "knowledge_type": "general",
    "indexed": true
  }
}
```

**precipitate 操作：**
```json
{
  "error": false,
  "data": {
    "precipitated_id": "precipitated-20260520T120000Z.md",
    "path": "/path/to/knowledge/experience/precipitated-20260520T120000Z.md",
    "patterns_analyzed": 5,
    "themes_found": 3
  }
}
```

### 降级行为

检索操作降级链：`ChromaDB 语义搜索` → `SQLite FTS5 全文搜索` → `关键词文件扫描(keyword_fallback)`

- `degradation_level: "chromadb"` — ChromaDB 语义搜索成功
- `degradation_level: "sqlite_fts5"` — ChromaDB 不可用，降级到 SQLite
- `degradation_level: "keyword_fallback"` — 全部数据库不可用，降级到文件关键词扫描

### 使用示例

```json
{
  "action": "retrieve",
  "query": "如何处理数据库连接超时",
  "top_k": 10,
  "search_type": "hybrid",
  "min_confidence": 0.3
}
```

```json
{
  "action": "inject",
  "content": "# 数据库连接池最佳实践\n使用连接池管理数据库连接...",
  "knowledge_type": "experience",
  "metadata": { "source": "project-x", "confidence": 0.9 }
}
```

```json
{
  "action": "precipitate",
  "pattern_ids": ["pattern-20260501-120000", "pattern-20260502-140000"]
}
```

---

## 3. quality_gate_check

执行 54 项质量门禁检查，支持按门禁 ID 或开发阶段(0-8)过滤。自动映射门禁到检查脚本，返回 PASS/FAIL/SKIP 状态和详细结果。

### 参数

| 名称 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| gate_ids | array\<string\> \| null | 否 | null | 要检查的门禁 ID 列表，为空则检查全部 |
| phase | string \| null | 否 | null | 按阶段过滤门禁（0-8） |
| project_path | string | 否 | "." | 项目根目录路径 |
| severity_filter | string | 否 | "all" | 严重级别过滤: `all`, `BLOCK`, `WARN` |
| force_refresh | boolean | 否 | false | 强制刷新缓存，忽略文件哈希缓存 |

### 返回值结构

```json
{
  "error": false,
  "data": {
    "checks": [
      {
        "gate_id": "TEST-PASS",
        "status": "PASS",
        "details": {
          "message": "发现5个测试文件",
          "test_files_found": 5,
          "pytest_available": true
        }
      },
      {
        "gate_id": "FILE-ENCODING",
        "status": "FAIL",
        "details": {
          "message": "发现2个编码不合规文件"
        },
        "suggestion": "修复文件编码：将以下文件转换为 UTF-8 编码"
      }
    ],
    "summary": {
      "total": 10,
      "passed": 7,
      "failed": 2,
      "skipped": 1,
      "blocked": true
    },
    "cache_info": {
      "hit": false,
      "hit_count": 0,
      "miss_count": 10,
      "cache_age_seconds": 0.0
    }
  }
}
```

### 降级行为

- 脚本存在时：执行检查脚本，超时 30 秒
- 脚本不存在时：降级到内嵌检查逻辑（INLINE_CHECKS）
- 脚本和内嵌检查均不可用：返回 `SKIP` 状态
- 增量缓存：基于文件哈希缓存，文件未变更时直接返回缓存结果

### 使用示例

```json
{
  "gate_ids": ["TEST-PASS", "FILE-ENCODING", "COMMENT-LANGUAGE"],
  "project_path": "/path/to/project",
  "force_refresh": true
}
```

```json
{
  "phase": "4",
  "project_path": ".",
  "severity_filter": "BLOCK"
}
```

---

## 4. spec_drift_detect

检测规格文档(spec)与代码实现(src)之间的偏差。扫描规格目录中的任务定义，对比源代码中的实际实现，报告缺失、过期或不一致的规格项。

### 参数

| 名称 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| spec_dir | string | 否 | ".trae/specs" | 规格文档目录 |
| src_dir | string | 否 | "." | 源代码目录 |

### 返回值结构

```json
{
  "error": false,
  "data": {
    "total_specs": 3,
    "total_pending_tasks": 12,
    "drifts": [
      {
        "task": "实现用户认证模块",
        "spec_file": ".trae/specs/tasks.md",
        "has_implementation": true,
        "potential_files": ["src/auth/user_auth.py"]
      },
      {
        "task": "添加日志中间件",
        "spec_file": ".trae/specs/tasks.md",
        "has_implementation": false,
        "potential_files": []
      }
    ],
    "implementation_rate": 0.58
  },
  "degradation_level": "script"
}
```

### 降级行为

降级链：`检查脚本(spec-drift-detector.py)` → `内嵌偏差检测逻辑`

- `degradation_level: "script"` — 脚本执行成功
- `degradation_level: "inline"` — 脚本不存在或执行失败，降级到内嵌逻辑

### 使用示例

```json
{
  "spec_dir": ".trae/specs",
  "src_dir": "src"
}
```

---

## 5. security_scan

安全扫描引擎：OWASP Agentic Top 10 检查 + 依赖漏洞扫描。支持严重级别过滤(critical/high/medium/low)，返回分类漏洞列表和修复建议。

### 参数

| 名称 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| target | string | 否 | "." | 目标扫描目录 |
| severity_threshold | string | 否 | "medium" | 最低报告严重级别: `critical`, `high`, `medium`, `low` |
| include_agentic | boolean | 否 | true | 是否包含 OWASP Agentic Top 10 检查 |
| include_dependency | boolean | 否 | true | 是否包含依赖漏洞扫描 |

### 返回值结构

```json
{
  "error": false,
  "data": {
    "agentic_scan": {
      "vulnerabilities": [
        {
          "type": "hardcoded_secret",
          "severity": "critical",
          "file": "src/config.py",
          "line": 42,
          "pattern": "api_key=\"sk-xxx\"",
          "description": "Hardcoded secret detected: credentials should not be embedded in source code"
        }
      ],
      "total": 3,
      "by_severity": {
        "critical": 1,
        "high": 1,
        "medium": 1,
        "low": 0
      }
    },
    "dependency_scan": {
      "dependencies": [
        {
          "name": "Flask",
          "version": "1.1.0",
          "status": "potentially_vulnerable",
          "reason": "Flask < 2.0 has known security vulnerabilities"
        }
      ],
      "total": 15,
      "vulnerable_count": 1
    }
  },
  "degradation_level": "inline"
}
```

### 降级行为

降级链：`安全扫描脚本(agentic-security-scanner.py)` → `内嵌安全扫描逻辑`

- Agentic 扫描和依赖扫描各自独立降级
- 脚本不可用时自动使用内嵌的正则匹配扫描
- `degradation_level: "inline"` — 至少一项扫描降级到内嵌逻辑

### 使用示例

```json
{
  "target": "src",
  "severity_threshold": "high",
  "include_agentic": true,
  "include_dependency": true
}
```

---

## 6. code_simplify

代码简化分析：检测死代码、深层嵌套、过长函数和重复代码。支持文件/目录/最近修改三种扫描范围，返回简化建议和重复代码报告。

### 参数

| 名称 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| target | string | 是 | — | 目标文件或目录路径 |
| scope | string | 否 | "recent" | 扫描范围: `file`, `dir`, `recent` |
| include_dedup | boolean | 否 | true | 是否包含重复代码检测 |

### 返回值结构

```json
{
  "error": false,
  "data": {
    "simplification": {
      "suggestions": [
        {
          "type": "long_function",
          "file": "src/service.py",
          "line": 45,
          "description": "函数长度 72 行，超过 50 行阈值",
          "severity": "medium"
        },
        {
          "type": "deep_nesting",
          "file": "src/handler.py",
          "line": 120,
          "description": "嵌套层级 5，超过 4 层阈值",
          "severity": "high"
        },
        {
          "type": "unused_import",
          "file": "src/utils.py",
          "line": 3,
          "description": "未使用的导入: os",
          "severity": "low"
        },
        {
          "type": "dead_code",
          "file": "src/main.py",
          "line": 89,
          "description": "return 语句后的不可达代码",
          "severity": "high"
        }
      ],
      "total": 8,
      "by_type": {
        "long_function": 2,
        "deep_nesting": 1,
        "unused_import": 3,
        "dead_code": 2
      }
    },
    "deduplication": {
      "duplicates": [
        {
          "hash": "a1b2c3d4",
          "count": 3,
          "files": ["src/a.py", "src/b.py", "src/c.py"],
          "preview": "def process(data):\n    result = []\n    for item in data:"
        }
      ],
      "total_groups": 2,
      "total_duplicate_lines": 18
    }
  },
  "degradation_level": "full"
}
```

### 降级行为

降级链：`代码简化脚本(code-simplifier.py)` → `内嵌简化检测逻辑`

- `degradation_level: "full"` — 脚本执行成功
- `degradation_level: "inline"` — 脚本不可用，降级到内嵌逻辑
- `degradation_level: "partial"` — 简化脚本成功但去重脚本降级

### 使用示例

```json
{
  "target": "src",
  "scope": "dir",
  "include_dedup": true
}
```

---

## 7. session_manage

会话状态管理：保存/加载/列出会话记录，检测重复错误模式，验证经验模式，追踪/恢复会话状态。

### 参数

| 名称 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| action | string | 是 | — | 操作类型: `save`, `load`, `list`, `detect`, `verify`, `track`, `restore` |
| completed_tasks | array\<string\> \| null | 否 | null | 已完成任务列表（save 时使用） |
| pending_tasks | array\<string\> \| null | 否 | null | 未完成任务列表（save/track 时使用） |
| decisions | array\<string\> \| null | 否 | null | 关键决策列表（save/track 时使用） |
| experience | array\<string\> \| null | 否 | null | 经验沉淀列表（save 时使用） |
| error_log | array\<string\> \| null | 否 | null | 错误日志（detect 时使用） |
| pattern_path | string \| null | 否 | null | 模式文件路径（verify 时使用） |
| success | boolean | 否 | true | 验证是否成功（verify 时使用） |
| current_phase | integer \| null | 否 | null | 当前阶段编号（track 时使用） |
| current_task | string \| null | 否 | null | 当前任务描述（track 时使用） |

### 返回值结构

**save 操作：**
```json
{
  "error": false,
  "data": {
    "path": "/path/to/.xuansto/sessions/session-20260520-120000.md",
    "filename": "session-20260520-120000.md"
  }
}
```

**load 操作：**
```json
{
  "error": false,
  "data": {
    "content": "# Session 20260520-120000\n\n## 已完成任务\n- 实现用户认证\n\n## 未完成任务\n- 添加日志中间件",
    "filename": "session-20260520-120000.md"
  }
}
```

**list 操作：**
```json
{
  "error": false,
  "data": {
    "sessions": ["session-20260520-120000.md", "session-20260519-180000.md"],
    "total": 2
  }
}
```

**detect 操作：**
```json
{
  "error": false,
  "data": {
    "patterns": [
      {
        "error": "ConnectionError: database timeout",
        "count": 5,
        "confidence": 0.40,
        "status": "draft",
        "verified": false
      }
    ],
    "total_detected": 1
  }
}
```

**verify 操作：**
```json
{
  "error": false,
  "data": {
    "verified": true,
    "updated_confidence": 0.85,
    "status": "verified"
  }
}
```

**track 操作：**
```json
{
  "error": false,
  "data": {
    "current_phase": 4,
    "current_task": "实现用户认证模块",
    "decisions": ["使用JWT认证方案"],
    "pending_tasks": ["添加日志中间件"],
    "completed_phases": [0, 1, 2, 3],
    "timestamp": "2026-05-20T10:00:00",
    "updated_at": "2026-05-20T12:00:00"
  }
}
```

**restore 操作：**
```json
{
  "error": false,
  "data": {
    "current_phase": 4,
    "current_task": "实现用户认证模块",
    "decisions": ["使用JWT认证方案"],
    "pending_tasks": ["添加日志中间件"],
    "completed_phases": [0, 1, 2, 3],
    "last_session": "# Session 20260520-120000\n..."
  }
}
```

### 降级行为

无降级链。所有操作均为纯文件系统操作，不依赖外部脚本。

### 使用示例

```json
{
  "action": "save",
  "completed_tasks": ["实现用户认证", "配置数据库连接"],
  "pending_tasks": ["添加日志中间件"],
  "decisions": ["使用JWT认证方案", "选择PostgreSQL数据库"],
  "experience": ["数据库连接超时需要设置pool_size参数"]
}
```

```json
{
  "action": "detect",
  "error_log": [
    "ConnectionError: database timeout",
    "ConnectionError: database timeout",
    "ConnectionError: database timeout",
    "ImportError: module not found",
    "ConnectionError: database timeout"
  ]
}
```

```json
{
  "action": "track",
  "current_phase": 4,
  "current_task": "实现用户认证模块",
  "decisions": ["使用JWT认证方案"],
  "pending_tasks": ["添加日志中间件"]
}
```

---

## 8. workflow_dispatch

工作流调度：启动/查询/中止/阶段推进工作流执行。支持 sdd-tdd-full/medium/fast 等工作流，返回工作流实例 ID 和当前状态。

### 参数

| 名称 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| action | string | 是 | — | 操作类型: `start`, `status`, `abort`, `phase` |
| workflow | string \| null | 否 | null | 工作流名称（start 时必填）: `sdd-tdd-full`, `sdd-tdd-medium`, `sdd-tdd-fast` 等 |
| project_path | string | 否 | "." | 项目根目录路径（start 时使用） |
| workflow_id | string \| null | 否 | null | 工作流实例 ID（status/abort/phase 时使用） |
| phase_action | string \| null | 否 | null | 阶段操作（phase 时使用）: `advance`, `current` |

### 阶段名称映射

| 阶段 | 名称 |
|------|------|
| 0 | 初始化 |
| 1 | 需求分析 |
| 2 | 架构设计 |
| 3 | 测试先行 |
| 4 | 代码实现 |
| 5 | 测试验证 |
| 6 | 验收确认 |
| 7 | 持续重构 |
| 8 | 部署交付 |

### 返回值结构

**start 操作：**
```json
{
  "error": false,
  "data": {
    "workflow_id": "wf-a1b2c3d4",
    "workflow": "sdd-tdd-full",
    "project_path": "/path/to/project",
    "status": "running",
    "current_phase": 0,
    "started_at": "2026-05-20T12:00:00",
    "completed_phases": []
  }
}
```

**status 操作（指定 workflow_id）：**
```json
{
  "error": false,
  "data": {
    "workflow_id": "wf-a1b2c3d4",
    "workflow": "sdd-tdd-full",
    "status": "running",
    "current_phase": 4,
    "completed_phases": [0, 1, 2, 3]
  }
}
```

**phase advance 操作：**
```json
{
  "error": false,
  "data": {
    "workflow_id": "wf-a1b2c3d4",
    "previous_phase": 3,
    "new_phase": 4,
    "advanced": true,
    "gates_passed": true,
    "gates_checked": [
      { "gate_id": "TEST-FIRST", "status": "PASS", "message": "...", "source": "inline" }
    ],
    "message": "阶段推进: 测试先行 -> 代码实现"
  }
}
```

**phase advance 失败：**
```json
{
  "error": false,
  "data": {
    "workflow_id": "wf-a1b2c3d4",
    "current_phase": 3,
    "phase_name": "测试先行",
    "advanced": false,
    "gates_passed": false,
    "gates_checked": [...],
    "failed_gates": [
      { "gate_id": "TEST-PASS", "status": "FAIL", "message": "未发现测试文件" }
    ],
    "message": "阶段 测试先行 门禁未通过，1 个失败"
  }
}
```

### 降级行为

无降级链。所有操作均为内存/文件系统操作。工作流状态持久化到 `.xuansto/workflows/` 目录。

### 使用示例

```json
{
  "action": "start",
  "workflow": "sdd-tdd-full",
  "project_path": "/path/to/project"
}
```

```json
{
  "action": "phase",
  "workflow_id": "wf-a1b2c3d4",
  "phase_action": "advance"
}
```

```json
{
  "action": "abort",
  "workflow_id": "wf-a1b2c3d4"
}
```

---

## 9. agent_status

Agent 状态查询：列出全部 57 个 Agent、按 Phase 查询活跃 Agent、查询单个 Agent 详情。返回 Agent 名称、层级和分配状态。

### 参数

| 名称 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| action | string | 是 | — | 操作类型: `list`, `by_phase`, `detail` |
| phase | integer \| null | 否 | null | 按阶段查询 Agent（by_phase 时使用，0-8） |
| agent_name | string \| null | 否 | null | Agent 名称（detail 时使用） |

### 阶段-Agent 映射

| 阶段 | Agent 列表 |
|------|-----------|
| 0 初始化 | Orchestrator, Design System Generator, UI Designer |
| 1 需求分析 | Product Manager, Brainstorming Facilitator, Knowledge Manager |
| 2 架构设计 | System Architect, Technical Writer, Knowledge Manager |
| 3 测试先行 | Test Architect, Unit Tester |
| 4 代码实现 | Backend Developer, Frontend Developer, Fullstack Developer, Subagent Dispatcher, Task Coordinator |
| 5 测试验证 | Security Auditor, AI Penetration Tester, E2E Tester, Integration Tester |
| 6 验收确认 | QA Engineer, UX Designer, Compliance Officer |
| 7 持续重构 | Refactoring Specialist, Code Reviewer, History Analyzer |
| 8 部署交付 | Build-Release Engineer, CI/CD Specialist, Runtime Supervisor |

### 返回值结构

**list 操作：**
```json
{
  "error": false,
  "data": {
    "agents": [
      { "name": "Orchestrator", "layer": "编排层" },
      { "name": "Product Manager", "layer": "产品层" }
    ],
    "total": 57
  }
}
```

**by_phase 操作：**
```json
{
  "error": false,
  "data": {
    "phase": 4,
    "agents": ["Backend Developer", "Frontend Developer", "Fullstack Developer", "Subagent Dispatcher", "Task Coordinator"],
    "total": 5
  }
}
```

**detail 操作：**
```json
{
  "error": false,
  "data": {
    "name": "Backend Developer",
    "file": "/path/to/agents/engineering/backend-developer.md",
    "content_length": 2048
  }
}
```

### 降级行为

无降级链。Agent 注册表从 `references/agent-registry.md` 解析，详情从 `agents/` 目录读取。

### 使用示例

```json
{
  "action": "list"
}
```

```json
{
  "action": "by_phase",
  "phase": 4
}
```

```json
{
  "action": "detail",
  "agent_name": "Backend Developer"
}
```

---

## 10. hook_manage

Hook 管理：列出指定 profile 的 Hook 配置，执行指定 Hook。支持 minimal/standard/strict 三种配置级别，16 个 Hook。

### 参数

| 名称 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| action | string | 是 | — | 操作类型: `list`, `execute` |
| profile | string | 否 | "standard" | Hook 配置级别: `minimal`, `standard`, `strict` |
| hook_name | string \| null | 否 | null | Hook 名称（execute 时必填） |
| context | object \| null | 否 | null | 执行上下文（execute 时使用） |

### Hook Profile 说明

| Profile | Hook 数量 | 说明 |
|---------|-----------|------|
| minimal | 2 | security-block, session-save |
| standard | 10 | 包含安全检查、格式检查、编码检查、会话保存等 |
| strict | 16 | 全部 Hook |

### 返回值结构

**list 操作：**
```json
{
  "error": false,
  "data": {
    "profile": "standard",
    "hooks": [
      {
        "name": "security-block",
        "has_script": false,
        "script": null,
        "has_inline_logic": true
      },
      {
        "name": "token-budget-check",
        "has_script": true,
        "script": "token-budget-guard.py",
        "has_inline_logic": false
      }
    ],
    "total": 10
  }
}
```

**execute 操作：**
```json
{
  "error": false,
  "data": {
    "hook": "security-block",
    "status": "block",
    "message": "检测到危险命令模式: rm -rf",
    "details": {
      "matched_patterns": ["rm -rf"],
      "command": "rm -rf /tmp/old"
    },
    "source": "inline"
  }
}
```

### 降级行为

降级链：`Hook 脚本` → `内嵌 Hook 逻辑(INLINE_HOOK_LOGIC)` → `跳过(skipped)`

- `source: "inline"` — 脚本不存在，使用内嵌逻辑
- `source: "inline_fallback"` — 脚本执行失败，降级到内嵌逻辑
- `status: "skipped"` — 无脚本也无内嵌逻辑

### 使用示例

```json
{
  "action": "list",
  "profile": "strict"
}
```

```json
{
  "action": "execute",
  "hook_name": "security-block",
  "context": {
    "command": "rm -rf /tmp/old",
    "project_path": "."
  }
}
```

---

## 11. resource_load_status

渐进式加载状态管理：查询指定 Phase 的资源加载状态，预加载指定 Phase 的资源。返回资源 ID、状态(loaded/available/missing)和路径。

### 参数

| 名称 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| action | string | 是 | — | 操作类型: `status`, `preload` |
| phase | integer \| null | 否 | null | 目标阶段（0-8） |
| resource_ids | array\<string\> \| null | 否 | null | 指定资源 ID 列表 |

### 阶段-资源映射

| 阶段 | 资源 |
|------|------|
| 0 | skill-config, agent-registry, quality-gates |
| 1 | knowledge-general, brainstorm-workflow |
| 2 | knowledge-patterns, sdd-tdd-full |
| 3 | test-guidelines |
| 4 | coding-standards, karpathy-guidelines |
| 5 | security-guidelines, owasp-top10 |
| 6 | acceptance-criteria |
| 7 | simplification-rules |
| 8 | desktop-guidelines, ipc-contracts |

### 返回值结构

**status 操作：**
```json
{
  "error": false,
  "data": {
    "resources": [
      { "id": "skill-config", "type": "config", "path": ".skill-config.yaml", "status": "loaded" },
      { "id": "agent-registry", "type": "reference", "path": "references/agent-registry.md", "status": "available" },
      { "id": "quality-gates", "type": "reference", "path": "references/quality-gates.md", "status": "missing" }
    ],
    "total": 3,
    "loaded": 1
  }
}
```

**preload 操作：**
```json
{
  "error": false,
  "data": {
    "phase": 4,
    "preloaded": [
      { "id": "coding-standards", "status": "loaded" },
      { "id": "karpathy-guidelines", "status": "loaded" }
    ],
    "total": 2
  }
}
```

### 降级行为

无降级链。资源状态持久化到 `.xuansto/resource_state.json`。

### 使用示例

```json
{
  "action": "status",
  "phase": 4
}
```

```json
{
  "action": "preload",
  "phase": 5
}
```

```json
{
  "action": "status",
  "resource_ids": ["skill-config", "agent-registry"]
}
```

---

## 12. context_compress

上下文压缩：支持 semantic(语义保留)/selective(选择性采样)/lossless(无损截断)三种策略。保留指定章节，压缩其余内容至目标 Token 数。

### 参数

| 名称 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| content | string | 是 | — | 待压缩的文本内容 |
| strategy | string | 否 | "semantic" | 压缩策略: `semantic`, `selective`, `lossless` |
| target_tokens | integer | 否 | 2000 | 目标 Token 数量（100-50000） |
| preserve_sections | array\<string\> \| null | 否 | null | 必须保留的章节标题列表 |

### 策略说明

| 策略 | 说明 |
|------|------|
| semantic | 按语义分块，保留高重要性块，低重要性块用摘要替代 |
| selective | 保留包含指定关键词的块，其余压缩为摘要 |
| lossless | 无损截断，按行保留直到达到目标 Token 数 |

### 返回值结构

```json
{
  "error": false,
  "data": {
    "compressed": "# 项目概述\n[...标题: ## 技术架构...]\n核心实现逻辑...\n[...段落: 详细配置说明...]",
    "original_tokens": 5000,
    "compressed_tokens": 1800,
    "compression_ratio": 0.36,
    "strategy": "semantic"
  }
}
```

**selective 策略额外字段：**
```json
{
  "preserved_chunks": 5,
  "total_chunks": 12
}
```

### 降级行为

无降级链。所有压缩策略均为纯 Python 内嵌实现，不依赖外部脚本。

### 使用示例

```json
{
  "content": "# 项目文档\n\n## 概述\n这是一个...\n\n## 技术架构\n采用微服务架构...\n\n## 部署指南\n详细步骤...",
  "strategy": "semantic",
  "target_tokens": 1000
}
```

```json
{
  "content": "...",
  "strategy": "selective",
  "target_tokens": 1500,
  "preserve_sections": ["技术架构", "核心接口"]
}
```

```json
{
  "content": "...",
  "strategy": "lossless",
  "target_tokens": 3000
}
```

---

## 13. server_health

MCP Server 健康检查：返回服务器状态、版本、运行时间、配置路径和工具统计。

### 参数

无参数。

### 返回值结构

```json
{
  "error": false,
  "data": {
    "status": "healthy",
    "version": "2.5.0",
    "uptime_seconds": 3600.5,
    "tools_count": 13,
    "resources_count": 6,
    "active_workflows": 2,
    "degradation_stats": {
      "security_scan": 1,
      "spec_drift_detect": 1
    },
    "performance_metrics": {
      "quality_gate_check": {
        "call_count": 15,
        "error_count": 0,
        "error_rate": 0.0,
        "latency_p50_ms": 120.5,
        "latency_p95_ms": 350.2,
        "latency_p99_ms": 500.1
      }
    },
    "config": {
      "data_dir": "/path/to/data",
      "skill_root": "/path/to/skill",
      "work_dir": "/path/to/.xuansto",
      "data_dir_exists": true,
      "skill_root_exists": true
    }
  }
}
```

### 降级行为

无降级链。始终返回当前服务器状态。

### 使用示例

```json
{}
```

---

## 错误码参考

| 错误码 | 说明 |
|--------|------|
| PATH_NOT_FOUND | 指定路径不存在 |
| SCRIPT_NOT_FOUND | 脚本文件不存在 |
| SCRIPT_EXECUTION_ERROR | 脚本执行失败 |
| DEGRADATION | 服务降级 |
| VALIDATION_ERROR | 参数校验失败 |
| INTERNAL_ERROR | 内部错误 |
| TIMEOUT | 脚本执行超时 |
| WORKFLOW_NOT_FOUND | 工作流实例不存在 |

## 降级级别说明

| 级别 | 说明 |
|------|------|
| chromadb | ChromaDB 语义搜索成功 |
| sqlite_fts5 | 降级到 SQLite FTS5 全文搜索 |
| keyword_fallback | 降级到关键词文件扫描 |
| script | 脚本执行成功 |
| inline | 降级到内嵌逻辑 |
| partial | 部分功能降级 |
| full | 全部功能正常 |
