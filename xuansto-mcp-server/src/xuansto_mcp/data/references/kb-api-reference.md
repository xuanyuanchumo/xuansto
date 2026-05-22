# 知识库API接口文档

> 版本: 1.9.0 | 更新日期: 2026-05-02 | 编码: UTF-8 | 行尾: LF

本文件定义Xuansto Skill知识库服务的REST API和MCP Tool接口规范，供Agent和外部工具通过标准化接口访问知识库。

## 目录

1. [REST API端点](#rest-api端点)
2. [MCP Tool接口](#mcp-tool接口)
3. [错误码定义](#错误码定义)
4. [认证与限流](#认证与限流)

---

## REST API端点

基础路径：`/v1/knowledge`

### 标准响应信封

所有API响应遵循统一信封格式：

```json
{
  "status": "ok|error|conflict",
  "data": {},
  "meta": {
    "elapsed_ms": 123
  }
}
```

### 搜索知识条目

**端点**：`POST /v1/knowledge/search`

**MCP Tool对应**：`knowledge_search` — 参数映射见[下方对照表](#rest-api与mcp-tool参数对照表)

**请求体**：
```json
{
  "query": "React组件设计模式",
  "scope": "general",
  "top_k": 5,
  "search_type": "hybrid",
  "agent_role": "code_reviewer",
  "filters": {
    "type": ["standard", "pattern"],
    "category": ["security"],
    "tags": ["react", "design-pattern"],
    "min_confidence": 0.7
  }
}
```

**响应**：
```json
{
  "status": "ok",
  "data": {
    "results": [
      {
        "id": "kb-20260429-001",
        "type": "pattern",
        "category": "design-pattern",
        "title": "React组件设计模式最佳实践",
        "content": "复合组件模式允许...",
        "summary": "React组件设计模式包括复合组件、HOC、Render Props等",
        "scope": "general",
        "tags": ["react", "design-pattern"],
        "confidence": 0.92,
        "source_rating": 4,
        "version": 1,
        "embedding_status": "ready",
        "created": "2026-04-29T10:00:00Z",
        "updated": "2026-04-29T10:00:00Z"
      }
    ],
    "total": 1,
    "search_strategy": "hybrid"
  },
  "meta": {
    "elapsed_ms": 45
  }
}
```

### 获取知识条目

**端点**：`GET /v1/knowledge/get/{id}`（兼容旧路径 `GET /v1/knowledge/{id}`）

**MCP Tool对应**：无直接对应（MCP通过`knowledge_search`按ID检索，或通过Resource URI `knowledge://{category}/{id}` 访问）

**响应**：
```json
{
  "status": "ok",
  "data": {
    "id": "kb-20260429-001",
    "type": "pattern",
    "category": "design-pattern",
    "title": "React组件设计模式最佳实践",
    "content": "复合组件模式允许...",
    "summary": "React组件设计模式包括复合组件、HOC、Render Props等",
    "content_path": ".knowledge/general/patterns/react-patterns.md",
    "scope": "general",
    "tags": ["react", "design-pattern"],
    "confidence": 0.92,
    "source_rating": 4,
    "source": ".knowledge/general/patterns/react-patterns.md",
    "occurrences": 5,
    "success_count": 4,
    "failure_count": 0,
    "version": 2,
    "embedding_status": "ready",
    "last_validated": "2026-04-30T10:00:00Z",
    "created": "2026-04-29T10:00:00Z",
    "updated": "2026-04-29T15:00:00Z"
  },
  "meta": {}
}
```

### 新增知识条目

**端点**：`POST /v1/knowledge/add`

**MCP Tool对应**：`knowledge_add` — 参数映射见[下方对照表](#rest-api与mcp-tool参数对照表)

**请求体**：
```json
{
  "title": "新知识条目标题",
  "content": "知识内容...",
  "type": "error-solution",
  "category": "database",
  "summary": "简要摘要用于向量嵌入和FTS索引",
  "content_path": ".knowledge/workspace/custom.md",
  "scope": "workspace",
  "tags": ["tag1", "tag2"],
  "source": ".knowledge/workspace/custom.md",
  "source_rating": 3
}
```

**响应**：
```json
{
  "status": "ok",
  "data": {
    "id": "kb-20260501-042",
    "status": "created",
    "dedup_status": "new",
    "message": "知识条目已创建"
  },
  "meta": {}
}
```

### 更新知识条目

**端点**：`PUT /v1/knowledge/update/{id}`（兼容旧路径 `PUT /v1/knowledge/{id}`）

**MCP Tool对应**：`knowledge_update` — 参数映射见[下方对照表](#rest-api与mcp-tool参数对照表)

**请求体**：
```json
{
  "title": "更新后的标题",
  "content": "更新后的内容...",
  "type": "error-solution",
  "category": "database",
  "tags": ["updated-tag"],
  "confidence": 0.85,
  "version": 1
}
```

**响应**：
```json
{
  "status": "ok",
  "data": {
    "id": "kb-20260429-001",
    "status": "updated",
    "previous_version": 1,
    "current_version": 2,
    "message": "知识条目已更新"
  },
  "meta": {}
}
```

**版本冲突响应**（409）：
```json
{
  "status": "conflict",
  "data": null,
  "meta": {
    "error": {
      "code": "VERSION_CONFLICT",
      "message": "版本冲突：当前版本为2，期望版本为1",
      "details": {
        "current_version": 2,
        "expected_version": 1
      },
      "retryable": true
    }
  }
}
```

### 删除知识条目

**端点**：`DELETE /v1/knowledge/delete/{id}`（兼容旧路径 `DELETE /v1/knowledge/{id}`）

**MCP Tool对应**：`knowledge_delete` — 参数映射见[下方对照表](#rest-api与mcp-tool参数对照表)

**响应**：
```json
{
  "status": "ok",
  "data": {
    "id": "kb-20260429-001",
    "status": "deleted",
    "message": "知识条目已删除"
  },
  "meta": {}
}
```

### 健康检查

**端点**：`GET /v1/knowledge/health`

**MCP Tool对应**：`knowledge_stats`（MCP通过stats工具获取健康状态，包含degradation和embedding级别信息）

**响应**：
```json
{
  "status": "ok",
  "data": {
    "status": "healthy",
    "version": "1.9.0",
    "engines": {
      "sqlite": "connected",
      "chroma": "connected"
    },
    "embedding": {
      "degraded": false,
      "level": 0,
      "level_name": "api",
      "dimension": 1536
    },
    "stats": {
      "total_entries": 156,
      "general_entries": 42,
      "workspace_entries": 89,
      "experience_entries": 25,
      "pending_embeddings": 3,
      "ready_embeddings": 153
    }
  },
  "meta": {}
}
```

### 一致性校验

**端点**：`GET /v1/health/consistency`

**响应**：
```json
{
  "status": "ok",
  "data": {
    "sqlite_ready_count": 153,
    "chroma_vector_count": 150,
    "missing_in_chroma": 3,
    "orphan_in_chroma": 0,
    "fixed_count": 3,
    "details": "3 entries missing in Chroma have been queued for re-embedding"
  },
  "meta": {}
}
```

### 备份知识库

**端点**：`POST /v1/knowledge/backup`

**请求体**：
```json
{
  "type": "full",
  "destination": ".knowledge/backup/full/"
}
```

**响应**：
```json
{
  "status": "ok",
  "data": {
    "status": "completed",
    "type": "full",
    "backup_path": ".knowledge/backup/full/kb-backup-20260501.tar.gz",
    "entries_count": 156,
    "size_bytes": 2048576,
    "timestamp": "2026-05-01T12:00:00Z"
  },
  "meta": {}
}
```

### 版本回滚

**端点**：`POST /v1/knowledge/rollback`

**MCP Tool对应**：`knowledge_rollback` — 参数映射见[下方对照表](#rest-api与mcp-tool参数对照表)

**请求体**：
```json
{
  "id": "kb-20260429-001",
  "target_version": 1
}
```

**响应**：
```json
{
  "status": "ok",
  "data": {
    "id": "kb-20260429-001",
    "status": "rolled_back",
    "target_version": 1,
    "current_version": 3,
    "message": "知识条目已回滚到版本1"
  },
  "meta": {}
}
```

### POST /v1/knowledge/auto_retrieve

自动检索知识库，根据任务类型和项目技术栈自动执行检索和格式化。

**请求体**：
```json
{
  "task_type": "bug_fix | feature | refactor | review | deploy | security",
  "project_path": "/path/to/project",
  "query": "optional search query",
  "token_budget": 2048
}
```

**响应**：
```json
{
  "context": "格式化后的结构化上下文字符串",
  "tech_stack": {"languages": [...], "frameworks": [...], "runtimes": [...], "platform": "..."},
  "degraded": false,
  "entries_used": 5,
  "token_used": 1847
}
```

### POST /v1/knowledge/web_update

从网络搜索官方文档并更新知识库。

**请求体**：
```json
{
  "entry_id": "optional entry ID to update",
  "category": "optional category to search",
  "tags": ["optional", "tags"]
}
```

**响应**：
```json
{
  "status": "updated | created | no_results",
  "entry_id": "...",
  "source_rating": 5,
  "changes_summary": "..."
}
```

### POST /v1/knowledge/progressive_search

渐进式知识检索，按 scope 优先级多轮检索。

**请求体**：
```json
{
  "query": "search query",
  "task_type": "bug_fix | feature | refactor | review | deploy | security",
  "tech_stack": {"languages": [...], "frameworks": [...], "runtimes": [...]},
  "token_budget": 2048
}
```

**响应**：
```json
{
  "results": [...],
  "total_entries": 8,
  "token_used": 1920,
  "pruned_entry_ids": ["id1", "id2"],
  "rounds_completed": 3
}
```

### POST /v1/knowledge/deep_load

按需深度加载特定知识条目的完整内容，不受日常 token 预算限制。

**请求体**：
```json
{
  "entry_id": "entry ID to load"
}
```

**响应**：
```json
{
  "entry": {完整知识条目对象},
  "loaded_at": "2026-05-12T10:00:00Z"
}
```

---

## MCP Tool接口

MCP（Model Context Protocol）Tool接口供Agent通过MCP协议直接调用知识库功能。使用stdio传输协议。完整MCP协议规范见 [mcp-protocol.md](mcp-protocol.md)。

### knowledge_search

搜索知识库条目。

**REST API对应**：`POST /v1/knowledge/search` — 参数映射见[REST API与MCP Tool参数对照表](#rest-api与mcp-tool参数对照表)

**参数**：
| 名称 | 类型 | 必需 | 说明 |
|------|------|------|------|
| query | string | 是 | 搜索查询文本 |
| top_k | integer | 否 | 返回结果数量，默认5 |
| search_type | string | 否 | 检索策略（hybrid/semantic_only/keyword_only），默认hybrid |
| filters | object | 否 | 过滤条件 |
| filters.type | array | 否 | 按类型筛选（paradigm/standard/pattern/error-solution/glossary） |
| filters.category | array | 否 | 按分类筛选 |
| filters.tags | array | 否 | 按标签筛选 |
| filters.min_confidence | number | 否 | 最低置信度阈值 |
| agent_role | string | 否 | Agent角色（code_reviewer/backend_developer/security_auditor/test_architect/desktop_developer） |

**返回值**：
```json
{
  "results": [
    {
      "id": "kb-20260429-001",
      "type": "pattern",
      "category": "design-pattern",
      "title": "条目标题",
      "content": "条目内容摘要...",
      "confidence": 0.92,
      "scope": "general"
    }
  ],
  "total": 1
}
```

### knowledge_add

新增知识条目。

**REST API对应**：`POST /v1/knowledge/add` — 参数映射见[REST API与MCP Tool参数对照表](#rest-api与mcp-tool参数对照表)

**参数**：
| 名称 | 类型 | 必需 | 说明 |
|------|------|------|------|
| content | string | 是 | 条目内容 |
| metadata | object | 否 | 条目元数据 |
| metadata.id | string | 否 | 自定义ID |
| metadata.type | string | 否 | 知识类型，默认unknown |
| metadata.category | string | 否 | 知识分类，默认uncategorized |
| metadata.tags | array | 否 | 标签列表 |
| metadata.confidence | number | 否 | 置信度，默认0.6 |
| metadata.source | string | 否 | 知识来源 |
| auto_dedup | boolean | 否 | 是否自动去重，默认true |

**返回值**：
```json
{
  "id": "kb-20260501-042",
  "status": "created",
  "dedup_status": "new"
}
```

### knowledge_update

更新知识条目。

**REST API对应**：`PUT /v1/knowledge/update/{id}` — 参数映射见[REST API与MCP Tool参数对照表](#rest-api与mcp-tool参数对照表)

**参数**：
| 名称 | 类型 | 必需 | 说明 |
|------|------|------|------|
| id | string | 是 | 条目ID |
| content | string | 否 | 更新内容 |
| metadata | object | 否 | 更新元数据 |
| metadata.type | string | 否 | 知识类型 |
| metadata.category | string | 否 | 知识分类 |
| metadata.tags | array | 否 | 标签列表 |
| metadata.confidence | number | 否 | 置信度 |
| metadata._version | integer | 否 | 乐观锁版本号 |

**返回值**：
```json
{
  "id": "kb-20260429-001",
  "status": "updated",
  "current_version": 2
}
```

**版本冲突返回**：
```json
{
  "status": "version_conflict",
  "current_version": 2,
  "expected_version": 1,
  "retryable": true
}
```

### knowledge_delete

删除知识条目。

**REST API对应**：`DELETE /v1/knowledge/delete/{id}` — 参数映射见[REST API与MCP Tool参数对照表](#rest-api与mcp-tool参数对照表)

**参数**：
| 名称 | 类型 | 必需 | 说明 |
|------|------|------|------|
| id | string | 是 | 条目ID |

**返回值**：
```json
{
  "id": "kb-20260429-001",
  "status": "deleted"
}
```

### knowledge_rollback

回滚知识条目到指定版本。

**REST API对应**：`POST /v1/knowledge/rollback` — 参数映射见[REST API与MCP Tool参数对照表](#rest-api与mcp-tool参数对照表)

**参数**：
| 名称 | 类型 | 必需 | 说明 |
|------|------|------|------|
| id | string | 是 | 条目ID |
| target_version | integer | 是 | 目标版本号 |

**返回值**：
```json
{
  "id": "kb-20260429-001",
  "status": "rolled_back",
  "target_version": 1,
  "current_version": 3
}
```

---

## REST API与MCP Tool参数对照表

以下对照表定义REST API端点与MCP Tool函数之间的参数映射关系，确保两种接口的输入输出保持一致。

### knowledge_search 对照

| REST API (`POST /v1/knowledge/search`) | MCP Tool (`knowledge_search`) | 映射说明 |
|---------------------------------------|-------------------------------|---------|
| query | query | 直接映射 |
| top_k | top_k | 直接映射 |
| search_type | search_type | 直接映射，枚举值一致 |
| filters.type | filters.type | 直接映射 |
| filters.category | filters.category | 直接映射 |
| filters.tags | filters.tags | 直接映射 |
| filters.min_confidence | filters.min_confidence | 直接映射 |
| scope | — | REST独有，MCP默认workspace |
| agent_role | — | REST独有，MCP通过AGENT_RETRIEVAL_PROFILES隐式处理 |

### knowledge_add 对照

| REST API (`POST /v1/knowledge/add`) | MCP Tool (`knowledge_add`) | 映射说明 |
|-------------------------------------|----------------------------|---------|
| content | content | 直接映射 |
| title | metadata.id | REST的title映射到MCP的metadata.id（用于去重标识） |
| type | metadata.type | 直接映射 |
| category | metadata.category | 直接映射 |
| tags | metadata.tags | 直接映射 |
| confidence | metadata.confidence | 直接映射 |
| source | metadata.source | 直接映射 |
| scope | — | REST独有，MCP默认workspace |
| summary | — | REST独有，MCP自动从content提取 |
| source_rating | — | REST独有，MCP默认3 |
| content_path | — | REST独有 |
| — | auto_dedup | MCP独有，默认true，REST始终启用去重 |

### knowledge_update 对照

| REST API (`PUT /v1/knowledge/update/{id}`) | MCP Tool (`knowledge_update`) | 映射说明 |
|---------------------------------------------|-------------------------------|---------|
| {id} (路径参数) | id | REST路径参数映射到MCP参数 |
| content | content | 直接映射 |
| type | metadata.type | 直接映射 |
| category | metadata.category | 直接映射 |
| tags | metadata.tags | 直接映射 |
| confidence | metadata.confidence | 直接映射 |
| title | — | REST独有，MCP不支持更新title |
| version | — | REST独有（乐观锁），MCP内部处理版本控制 |

### knowledge_delete 对照

| REST API (`DELETE /v1/knowledge/delete/{id}`) | MCP Tool (`knowledge_delete`) | 映射说明 |
|-----------------------------------------------|-------------------------------|---------|
| {id} (路径参数) | id | REST路径参数映射到MCP参数 |

### knowledge_rollback 对照

| REST API (`POST /v1/knowledge/rollback`) | MCP Tool (`knowledge_rollback`) | 映射说明 |
|------------------------------------------|---------------------------------|---------|
| id | id | 直接映射 |
| target_version | target_version | 直接映射 |

### knowledge_stats 对照

| REST API (`GET /v1/knowledge/health`) | MCP Tool (`knowledge_stats`) | 映射说明 |
|---------------------------------------|-------------------------------|---------|
| — | detailed | MCP独有，控制是否返回详细分类统计 |
| stats.total_entries | total_entries | 直接映射 |
| stats.general_entries | by_scope.general | REST扁平结构，MCP使用by_scope对象 |
| stats.workspace_entries | by_scope.workspace | 同上 |
| stats.experience_entries | by_scope.experience | 同上 |
| stats.pending_embeddings | embedding.pending | 直接映射 |
| stats.ready_embeddings | embedding.ready | 直接映射 |
| engines.chroma | chroma_available | REST返回状态字符串，MCP返回布尔值 |
| — | degradation_level | MCP独有，返回降级级别 |
| — | embedding_level | MCP独有，返回嵌入级别 |

### 错误码对照

| REST API错误码 | MCP Tool错误码 | MCP标准错误代码 | 说明 |
|---------------|---------------|----------------|------|
| BAD_REQUEST (400) | BAD_REQUEST | -32101 | 请求参数无效 |
| UNAUTHORIZED (401) | — | — | MCP通过传输层认证处理 |
| NOT_FOUND (404) | NOT_FOUND | -32102 | 知识条目不存在 |
| DUPLICATE_DETECTED (409) | — | -32104 | REST返回重复检测，MCP通过dedup_status字段返回 |
| VERSION_CONFLICT (409) | VERSION_CONFLICT | -32103 | 版本冲突（乐观锁） |
| VALIDATION_ERROR (422) | SENSITIVE_CONTENT | -32106 | MCP区分敏感内容错误 |
| RATE_LIMITED (429) | — | — | MCP通过传输层限流处理 |
| INTERNAL_ERROR (500) | — | -32603 | MCP标准InternalError |
| SERVICE_DEGRADED (503) | — | — | MCP通过degradation_level字段反映 |
| — | UNKNOWN_TOOL | -32601 | MCP独有，工具名不存在 |

---

## 错误码定义

| 错误码 | HTTP状态码 | 说明 | 处理建议 |
|--------|-----------|------|---------|
| BAD_REQUEST | 400 | 请求参数无效 | 检查请求体格式和必填字段 |
| UNAUTHORIZED | 401 | 未授权（远程模式需要API Key） | 提供有效的X-API-Key请求头 |
| NOT_FOUND | 404 | 知识条目不存在 | 检查entry_id是否正确 |
| DUPLICATE_DETECTED | 409 | 知识条目重复（相似度>阈值） | 使用knowledge_update更新已有条目 |
| VERSION_CONFLICT | 409 | 版本冲突（乐观锁） | 重新读取最新版本后重试 |
| VALIDATION_ERROR | 422 | 字段校验失败 | 检查字段值范围和格式 |
| RATE_LIMITED | 429 | 请求频率超限 | 等待retry_after秒后重试 |
| INTERNAL_ERROR | 500 | 内部服务器错误 | 检查日志，重启知识库服务 |
| SERVICE_DEGRADED | 503 | 服务降级（双引擎不可用） | 系统自动降级到SQLite+FTS5 |

**错误响应格式**：
```json
{
  "status": "error",
  "data": null,
  "meta": {
    "error": {
      "code": "DUPLICATE_DETECTED",
      "message": "知识条目重复",
      "details": {
        "similarity_score": 0.95,
        "existing_id": "kb-20260429-001"
      },
      "retryable": false
    }
  }
}
```

---

## 认证与限流

### 认证规范

知识库服务支持基于API Key的认证机制：

| 环境 | 认证方式 | 说明 |
|------|---------|------|
| 本地开发 (127.0.0.1) | 无认证 | 默认跳过认证 |
| 远程部署 (0.0.0.0) | API Key（强制） | 请求头 `X-API-Key` |

**API Key格式**：`xks-` 前缀 + 32字节随机十六进制字符串

**权限分级**：
| 权限级别 | 允许操作 |
|---------|---------|
| read-only | GET和POST /search端点 |
| read-write | 所有CRUD端点 |
| admin | 所有端点 + backup + config |

**API Key来源**：
- 环境变量 `KNOWLEDGE_API_KEY`
- 配置文件 `.knowledge/.api_keys.json`

### API限流

| 限流维度 | 默认值 | 说明 |
|---------|-------|------|
| 每分钟请求数 | 60 | 单IP滑动窗口限制 |
| 算法 | sliding_window | 滑动窗口算法 |

限流响应HTTP状态码：429 Too Many Requests，响应包含`retry_after`字段。
