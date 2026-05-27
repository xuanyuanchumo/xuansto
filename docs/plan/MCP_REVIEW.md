# Xuansto MCP Server 全面审查报告

> 版本: 8.9.0-dev | 审查日期: 2026-05-27 | 编码: UTF-8 | 行尾: LF

## 目录

- [1. 当前 MCP Tool 清单（22 Tools + ToolAnnotations）](#1-当前-mcp-tool-清单22-tools--toolannotations)
- [2. 当前 MCP Resource 清单（29 Resources）](#2-当前-mcp-resource-清单29-resources)
- [3. 当前 MCP Prompt 定义（2 Prompts）](#3-当前-mcp-prompt-定义2-prompts)
- [4. Hook 差异化超时](#4-hook-差异化超时)
- [5. 速率限制差异化配置](#5-速率限制差异化配置)
- [6. 降级链路完整性（22/22）](#6-降级链路完整性2222)
- [7. mcpServers 配置 JSON 示例](#7-mcpservers-配置-json-示例)
- [8. Skill→MCP 交互协议](#8-skillmcp-交互协议)

---

## 1. 当前 MCP Tool 清单（22 Tools + ToolAnnotations）

> 源码位置: `xuansto-mcp-server/src/xuansto_mcp/server.py` L173-L197 (工具注册循环)
> 所有 22 个 Tool 均已声明 `ToolAnnotations`（v8.9.0-dev 新增），客户端可据此做安全决策。

| # | 工具名 | 功能描述 | ToolAnnotations | 核心参数 | 源码文件 |
|---|--------|----------|-----------------|----------|----------|
| 1 | `skill_analyze` | 分析技能项目结构，提取YAML元数据、目录结构、Agent注册表、脚本依赖和验证问题 | R:true D:false I:true O:false | `skill_path`(必填), `include_scripts`(bool), `include_agents`(bool), `depth`("basic"/"detailed"/"full") | `tools/skill_analyze.py` |
| 2 | `knowledge_search` | 三层知识库（通用/工作区/经验）混合检索引擎。仅支持retrieve和cleanup_versions操作 | R:true D:false I:true O:false | `action`("retrieve"/"cleanup_versions"), `query`, `top_k`(1-50), `search_type`("hybrid"/"semantic_only"/"keyword_only"), `scope`, `min_confidence` | `tools/knowledge_search.py` |
| 3 | `knowledge_inject` | 知识注入引擎：按主题检索注入、列出可用知识、经验沉淀保存、直接添加/更新知识条目 | R:false D:false I:false O:false | `action`("inject"/"list_available"/"precipitate"/"add"/"update"), `topics`, `scope`, `max_tokens`, `relevance_threshold`, `category`, `title`, `content`, `tags`, `confidence`, `entry_id` | `tools/knowledge_inject.py` |
| 4 | `quality_gate_check` | 执行54项质量门禁检查，支持按门禁ID或开发阶段(0-8)过滤 | R:false D:false I:true O:false | `gate_ids`(list), `phase`("0"-"8"), `project_path`, `severity_filter`, `force_refresh`(bool) | `tools/quality_gate_check.py` |
| 5 | `spec_drift_detect` | 检测规格文档(spec)与代码实现(src)之间的偏差 | R:true D:false I:true O:false | `spec_dir`, `src_dir` | `tools/spec_drift_detect.py` |
| 6 | `security_scan` | OWASP Agentic Top 10检查 + 依赖漏洞扫描 | R:true D:false I:true O:false | `target`, `severity_threshold`("critical"/"high"/"medium"/"low"), `include_agentic`(bool), `include_dependency`(bool) | `tools/security_scan.py` |
| 7 | `code_simplify` | 代码简化分析：检测死代码、深层嵌套、过长函数和重复代码 | R:false D:true I:false O:true | `target`(必填), `scope`("file"/"dir"/"recent"), `include_dedup`(bool) | `tools/code_simplify.py` |
| 8 | `session_manage` | 会话状态管理：保存/加载/列出/检测/验证/追踪/恢复会话 | R:false D:false I:false O:false | `action`("save"/"load"/"list"/"detect"/"verify"/"track"/"restore"), `completed_tasks`, `pending_tasks`, `decisions`, `experience`, `error_log`, `pattern_path`, `success`, `current_phase`, `current_task` | `tools/session_manage.py` |
| 9 | `workflow_dispatch` | 工作流调度：启动/查询/中止/阶段推进/恢复/快照 | R:false D:false I:false O:false | `action`("start"/"status"/"abort"/"phase"/"recover"/"snapshots"), `workflow`, `project_path`, `workflow_id`, `phase_action`, `snapshot_phase` | `tools/workflow_dispatch.py` |
| 10 | `agent_status` | Agent状态查询：列出全部57个Agent、按Phase查询、查询单个Agent详情、按能力匹配 | R:true D:false I:true O:false | `action`("list"/"by_phase"/"detail"/"match"), `phase`, `agent_name`, `capabilities`, `project_file_count` | `tools/agent_status.py` |
| 11 | `agent_manage` | Agent实例生命周期管理：创建/分配/释放/销毁/状态查询/调度 | R:false D:true I:false O:false | `action`("create"/"assign"/"release"/"instance_status"/"destroy"/"schedule"), `agent_type`, `capabilities`, `agent_id`, `task` | `tools/agent_manage.py` |
| 12 | `hook_manage` | Hook管理：列出指定profile的Hook配置，执行指定Hook，查询Phase对应的活跃Hook Profile | R:false D:false I:false O:false | `action`("list"/"execute"/"phase_profile"), `profile`("minimal"/"standard"/"strict"), `hook_name`, `context`, `phase` | `tools/hook_manage.py` |
| 13 | `resource_load_status` | 渐进式加载状态管理：查询Phase资源加载状态、预加载、阶段转换 | R:true D:false I:true O:false | `action`("status"/"preload"/"cache"/"clear_cache"/"loading_progress"/"disclosure_transition"), `phase`(0-3), `resource_ids`, `resource_uris`, `priority`, `batch_mode`, `auto_upgrade`, `target_phase` | `tools/resource_load_status.py` |
| 14 | `resource_subscribe` | 资源订阅管理：订阅/取消订阅/列出资源变更通知 | R:false D:false I:true O:false | `action`("subscribe"/"unsubscribe"/"list"), `uri`, `client_id` | `tools/resource_subscribe.py` |
| 15 | `context_compress` | 上下文压缩：支持semantic/selective/lossless三种策略 | R:false D:false I:true O:false | `content`(必填), `strategy`("semantic"/"selective"/"lossless"), `target_tokens`(100-50000), `preserve_sections` | `tools/context_compress.py` |
| 16 | `server_health` | MCP Server 健康检查：返回服务器状态、版本、运行时间、配置路径和工具统计 | R:true D:false I:true O:false | `action`("check"/"version"/"status"), `client_version`, `client_api_version` | `tools/server_health.py` |
| 17 | `decision_log` | 决策日志管理：记录/搜索/导出决策记录 | R:false D:false I:false O:false | `action`("log"/"list"/"query"/"update"/"export"/"stats"/"configure"), `title`, `description`, `context`, `alternatives`, `decision`, `rationale`, `impact`, `decided_by`, `keyword`, `tag`, `date_from`, `date_to`, `limit`, `offset`, `format`, `decision_id`, `status`, `file_backup` | `tools/decision_log.py` |
| 18 | `token_budget` | Token预算管理：查询/设置/推荐/报告/强制执行/阶段设置 | R:false D:false I:false O:false | `action`("status"/"set_budget"/"set_from_phase"/"recommend"/"report"/"enforce"), `total_budget`, `phase_allocations`, `project_size`, `complexity`, `team_size`, `period`, `phase` | `tools/token_budget.py` |
| 19 | `project_init` | 项目初始化管理：创建/验证/检测技术栈/配置项目 | R:false D:false I:true O:false | `action`("create"/"init"/"validate"/"detect_stack"/"detect"/"configure"), `name`, `description`, `stack`, `template`, `directory`, `project_path` | `tools/project_init.py` |
| 20 | `metrics_report` | 指标报告：查询/汇总/评估工具调用指标 | R:true D:false I:true O:false | `action`("query"/"summary"/"evaluate"), `tool_name`, `time_range`("1h"/"6h"/"24h"/"7d"/"all"), `metric_type`("calls"/"errors"/"latency"/"all"), `criterion` | `tools/metrics_report.py` |
| 21 | `config_manage` | 配置管理：重载/查询状态/校验/获取YAML配置文件 | R:false D:false I:false O:false | `action`("reload"/"status"/"validate"/"get") | `tools/config_manage.py` |
| 22 | `audit_query` | 审计日志查询：查询MCP工具调用审计记录 | R:true D:false I:true O:false | `tool_name`, `date_range`("YYYY-MM-DD:YYYY-MM-DD"), `limit`(1-500) | `tools/audit_query.py` |

> **ToolAnnotations 图例**: R=readOnlyHint, D=destructiveHint, I=idempotentHint, O=openWorldHint

### 1.1 ToolAnnotations 完整声明表

> 源码: 各 `tools/*.py` 中 `@mcp.tool(annotations=ToolAnnotations(...))` 声明

| Tool | readOnlyHint | destructiveHint | idempotentHint | openWorldHint |
|------|-------------|-----------------|----------------|---------------|
| `skill_analyze` | true | false | true | false |
| `knowledge_search` | true | false | true | false |
| `knowledge_inject` | false | false | false | false |
| `quality_gate_check` | false | false | true | false |
| `spec_drift_detect` | true | false | true | false |
| `security_scan` | true | false | true | false |
| `code_simplify` | false | true | false | true |
| `session_manage` | false | false | false | false |
| `workflow_dispatch` | false | false | false | false |
| `agent_status` | true | false | true | false |
| `agent_manage` | false | true | false | false |
| `hook_manage` | false | false | false | false |
| `resource_load_status` | true | false | true | false |
| `resource_subscribe` | false | false | true | false |
| `context_compress` | false | false | true | false |
| `server_health` | true | false | true | false |
| `decision_log` | false | false | false | false |
| `token_budget` | false | false | false | false |
| `project_init` | false | false | true | false |
| `metrics_report` | true | false | true | false |
| `config_manage` | false | false | false | false |
| `audit_query` | true | false | true | false |

### 1.2 Tool/Resource 职责分离现状

根据 MCP 协议设计原则：**Tool 用于有副作用的操作，Resource 用于只读状态快照**。v8.9.0-dev 已将多个只读查询迁移为 Resource：

| Tool | 保留的写操作 | 已迁移到 Resource 的只读操作 |
|------|-------------|------------------------------|
| `agent_status` | — (纯只读) | `xuansto://agents/list`, `xuansto://agents/{name}`, `xuansto://agents/{layer}/{name}`, `xuansto://agents/registry` |
| `server_health` | — (纯只读) | `xuansto://health/status` |
| `metrics_report` | — (纯只读) | `xuansto://metrics/summary` |
| `audit_query` | — (纯只读) | `xuansto://audit/log`, `xuansto://audit/recent` |
| `decision_log` | log/update/configure | `xuansto://decisions/latest`, `xuansto://decisions/recent` |
| `session_manage` | save/track/restore | `xuansto://sessions/latest`, `xuansto://sessions/{session_id}`, `xuansto://sessions/list`, `xuansto://session/state` |
| `resource_load_status` | preload/clear_cache | `xuansto://loading/status`, `xuansto://loading/requirements` |
| `quality_gate_check` | 执行检查(有副作用) | `xuansto://gates/definitions`, `xuansto://gates/list` |
| `workflow_dispatch` | start/abort/phase/recover | `xuansto://workflows/definitions`, `xuansto://workflows/active`, `xuansto://workflows/list` |

---

## 2. 当前 MCP Resource 清单（29 Resources）

> 源码位置: `xuansto-mcp-server/src/xuansto_mcp/resources/skill_resources.py` L82-L872

| # | URI 模式 | 类型 | 内容描述 | 加载Phase |
|---|----------|------|----------|-----------|
| 1 | `xuansto://config/skill` | 静态 | 技能配置文件(.skill-config.yaml) | Phase 0+ |
| 2 | `xuansto://templates/{name}` | 模板 | 按名称获取模板文件 | Phase 2+ |
| 3 | `xuansto://sessions/latest` | 静态 | 最新会话记录 | Phase 1+ |
| 4 | `xuansto://sessions/{session_id}` | 模板 | 按ID获取会话记录 | Phase 1+ |
| 5 | `xuansto://agents/{name}` | 模板 | 按名称获取Agent定义 | Phase 2+ |
| 6 | `xuansto://agents/{layer}/{name}` | 模板 | 按层级+名称获取Agent定义 | Phase 2+ |
| 7 | `xuansto://loading/status` | 静态 | 渐进式加载状态JSON（含phase_capability_matrix、token_budget_status、transition_validation） | Phase 0+ |
| 8 | `xuansto://loading/requirements` | 静态 | 各Phase资源加载需求详情（含资源列表、Token估算、转换条件） | Phase 0+ |
| 9 | `xuansto://metrics/summary` | 静态 | 工具指标汇总 | Phase 2+ |
| 10 | `xuansto://degradation/status` | 静态 | 降级状态（含组件级别和恢复尝试） | Phase 0+ |
| 11 | `xuansto://skill/constraints` | 静态 | 技能约束配置 | Phase 0+ |
| 12 | `xuansto://agents/registry` | 静态 | Agent注册表 | Phase 2+ |
| 13 | `xuansto://gates/definitions` | 静态 | 质量门禁定义 | Phase 2+ |
| 14 | `xuansto://workflows/definitions` | 静态 | 工作流定义 | Phase 1+ |
| 15 | `xuansto://hooks/definitions` | 静态 | Hook定义 | Phase 3 |
| 16 | `xuansto://knowledge/stats` | 静态 | 知识库统计（含DB和ChromaDB条目数） | Phase 2+ |
| 17 | `xuansto://templates/index` | 静态 | 模板索引 | Phase 2+ |
| 18 | `xuansto://commands/routes` | 静态 | 命令路由表 | Phase 1+ |
| 19 | `xuansto://session/state` | 静态 | 当前会话状态 | Phase 1+ |
| 20 | `xuansto://health/status` | 静态 | 健康状态（含组件健康检查） | Phase 0+ |
| 21 | `xuansto://audit/log` | 静态 | 审计日志(最近50条) | Phase 2+ |
| 22 | `xuansto://decisions/latest` | 静态 | 最近决策记录(10条, Markdown格式) | Phase 2+ |
| 23 | `xuansto://workflows/active` | 静态 | 活跃工作流实例 | Phase 1+ |
| 24 | `xuansto://agents/list` | 静态 | Agent列表（含Phase映射） | Phase 2+ |
| 25 | `xuansto://sessions/list` | 静态 | 会话列表 | Phase 1+ |
| 26 | `xuansto://gates/list` | 静态 | 质量门禁列表（含inline_check和phase映射） | Phase 2+ |
| 27 | `xuansto://workflows/list` | 静态 | 工作流列表 | Phase 1+ |
| 28 | `xuansto://audit/recent` | 静态 | 最近审计记录（含汇总统计） | Phase 2+ |
| 29 | `xuansto://references/summary/{name}` | 模板 | 按名称获取参考文档摘要 | Phase 2+ |

> **降级机制**: 所有 Resource 均实现了 `_degraded_resource()` 降级响应（L71-L79），当资源读取异常时返回 `{"status": "degraded", "uri": ..., "error": ...}` JSON。
> **路径安全**: 模板类 Resource 使用 `validate_path_safety()` 验证路径安全性，防止路径遍历攻击（L67-L68）。
> **v8.9.0-dev 新增 Resource**: #8 `loading/requirements`, #24 `agents/list`, #25 `sessions/list`, #26 `gates/list`, #27 `workflows/list`, #28 `audit/recent`, #29 `references/summary/{name}`。

---

## 3. 当前 MCP Prompt 定义（2 Prompts）

> 源码位置: `xuansto-mcp-server/src/xuansto_mcp/server.py` L218-L231

### 3.1 xuansto_workflow

```python
@mcp.prompt("xuansto_workflow")
def xuansto_workflow_prompt(task_description: str) -> list[dict[str, str]]:
    return [
        {"role": "user", "content": "You are an expert workflow orchestrator for the xuansto development system. Follow the xuansto workflow phases and quality gates to ensure structured, high-quality development output."},
        {"role": "user", "content": f"Execute xuansto workflow for: {task_description}"},
    ]
```

**参数**: `task_description: str`

**返回**: 结构化 `messages` 数组（2条消息），符合 MCP Prompt 规范。

### 3.2 xuansto_analysis

```python
@mcp.prompt("xuansto_analysis")
def xuansto_analysis_prompt(skill_path: str) -> list[dict[str, str]]:
    return [
        {"role": "user", "content": "You are an expert code and architecture analyst. Provide thorough analysis of skill definitions, code quality, and architectural patterns."},
        {"role": "user", "content": f"Analyze skill at: {skill_path}"},
    ]
```

**参数**: `skill_path: str`

**返回**: 结构化 `messages` 数组（2条消息），符合 MCP Prompt 规范。

> **v8.9.0-dev 改进**: Prompt 现在返回 `list[dict[str, str]]` 格式的结构化消息数组（包含 `role` 和 `content` 字段），符合 MCP Prompt 规范的 `messages` 数组格式要求。此前版本仅返回固定格式字符串。

---

## 4. Hook 差异化超时

> 源码位置: `xuansto-mcp-server/src/xuansto_mcp/core/hook_engine.py` L44-L57

### 4.1 超时配置

```python
DEFAULT_HOOK_TIMEOUT_SECONDS = 30.0

HOOK_TIMEOUT_MAP: dict[str, float] = {
    "security-block": 5.0,
    "dangerous-cmd-confirm": 5.0,
    "auto-format": 10.0,
    "encoding-check": 10.0,
    "console-log-detect": 10.0,
    "type-check": 10.0,
}
```

| Hook 类别 | Hook 名称 | 超时时间 | 设计理由 |
|-----------|-----------|----------|----------|
| **安全类** | `security-block` | 5s | 安全检查必须快速响应，延迟意味着风险 |
| **安全类** | `dangerous-cmd-confirm` | 5s | 危险命令确认需要即时反馈 |
| **编码类** | `auto-format` | 10s | 代码格式化涉及文件I/O，需适当放宽 |
| **编码类** | `encoding-check` | 10s | 编码检查需读取文件内容 |
| **编码类** | `console-log-detect` | 10s | 日志检测需扫描源码 |
| **编码类** | `type-check` | 10s | 类型检查可能涉及AST解析 |
| **其他** | 默认 | 30s | 通用超时，兼容复杂Hook逻辑 |

### 4.2 超时执行逻辑

> 源码位置: `hook_engine.py` L163-L198 (`execute_pre_hooks`), L200-L226 (`execute_post_hooks`)

```python
timeout = get_hook_timeout(handler_name)
if asyncio.iscoroutinefunction(handler):
    result = await asyncio.wait_for(handler(tool_name, kwargs), timeout=timeout)
else:
    result = await asyncio.wait_for(asyncio.to_thread(handler, tool_name, kwargs), timeout=timeout)
```

- 每个 Hook 按名称查询 `HOOK_TIMEOUT_MAP` 获取独立超时
- 超时后记录 `{"hook": handler_name, "error": f"timeout after {timeout:.1f}s"}` 并跳过
- 连续失败 5 次触发告警（`_HOOK_FAILURE_THRESHOLD = 5`）

### 4.3 Hook 动态配置与 Phase 联动

> 源码位置: `xuansto-mcp-server/src/xuansto_mcp/tools/hook_manage.py` L35-L46

```python
HOOK_PROFILES = {
    "minimal": ["security-block", "session-save"],
    "standard": ["security-block", "token-budget-check", "auto-format", "encoding-check",
                 "load-context", "kb-health-check", "session-save", "git-status-check",
                 "experience-precipitate", "save-state"],
    "strict": list(HOOK_SCRIPTS_MAP.keys()),
}

PHASE_HOOK_PROFILE_MAP: dict[int, str] = {
    0: "minimal",
    1: "standard",
    2: "standard",
    3: "strict",
}
```

| Phase | Hook Profile | 活跃 Hook 数量 | 说明 |
|-------|-------------|----------------|------|
| Phase 0 (SKELETON) | minimal | 2 | 仅安全阻断和会话保存 |
| Phase 1 (FUNCTIONAL) | standard | 10 | 增加编码检查、Token预算、上下文加载 |
| Phase 2 (ENHANCED) | standard | 10 | 同 FUNCTIONAL |
| Phase 3 (FULL) | strict | 全部 | 全部 Hook 启用，最严格管控 |

---

## 5. 速率限制差异化配置

> 源码位置: `xuansto-mcp-server/src/xuansto_mcp/core/rate_limiter.py` L39-L46

### 5.1 令牌桶配置

```python
_DEFAULT_MAX_TOKENS = 60.0
_DEFAULT_REFILL_RATE = 1.0

_TOOL_RATE_LIMITS: dict[str, tuple[float, float]] = {
    "quality_gate_check": (120.0, 2.0),
    "config_manage": (10.0, 1.0 / 6.0),
    "security_scan": (30.0, 0.5),
}
```

| Tool | 最大令牌数 | 填充速率(令牌/秒) | 等效速率(次/分钟) | 设计理由 |
|------|-----------|-------------------|-------------------|----------|
| `quality_gate_check` | 120.0 | 2.0 | 120/min | 门禁检查高频调用场景，需高吞吐 |
| `security_scan` | 30.0 | 0.5 | 30/min | 扫描计算密集，限制并发避免资源争抢 |
| `config_manage` | 10.0 | 1/6 | 10/min | 配置变更低频但高风险，严格限流 |
| 其他（默认） | 60.0 | 1.0 | 60/min | 通用速率，平衡吞吐与安全 |

### 5.2 速率限制执行逻辑

> 源码位置: `server.py` L112-L124

```python
rate_allowed, rate_info = check_rate_limit(tool_name)
if not rate_allowed:
    result = make_response(
        error=True,
        error_code=ErrorCodes.RATE_LIMITED,
        message=rate_info.get("message", "Rate limit exceeded"),
    )
    result["details"] = rate_info
```

- 每个工具独立令牌桶，互不影响
- 超限时返回 `ERR_RATE_LIMITED` 错误码和 `retry_after_seconds` 信息
- 支持运行时动态调整: `configure_tool_limit(tool_name, max_tokens, refill_rate)`

---

## 6. 降级链路完整性（22/22）

> 源码位置: `xuansto-mcp-server/src/xuansto_mcp/core/degradation.py` L1119-L1142 (`FALLBACK_MAP`)

### 6.1 降级链路架构

```
MCP Tool 调用 → 失败/超时
    ↓
Level 1: Script Fallback (run_script_fallback)
    → 成功: 返回降级结果 (degraded=true)
    → 失败: ↓
Level 2: Inline Fallback (_try_inline_fallback)
    → 成功: 返回内联结果 (degradation_level="inline")
    → 失败: ↓
Level 3: Minimal Response
    → 返回最小可用结果 (degradation_level="minimal")
```

### 6.2 FALLBACK_MAP 完整清单（22/22 工具全覆盖）

| # | Tool 名称 | Fallback 函数 | 脚本降级 | 内联降级 | 最小响应 |
|---|-----------|---------------|----------|----------|----------|
| 1 | `skill_analyze` | `skill_analyze_fallback` | skill-test.py | `_inline_skill_analyze` | ✅ |
| 2 | `knowledge_search` | `knowledge_search_fallback` | knowledge-server.py | `_inline_knowledge_search` | ✅ |
| 3 | `knowledge_inject` | `knowledge_inject_fallback` | knowledge-server.py | `_inline_knowledge_inject` | ✅ |
| 4 | `quality_gate_check` | `quality_gate_fallback` | skill-test.py + GATE_SCRIPTS_MAP | `_inline_quality_gate` | ✅ |
| 5 | `spec_drift_detect` | `spec_drift_fallback` | spec-drift-detector.py | `_inline_spec_drift` | ✅ |
| 6 | `security_scan` | `security_scan_fallback` | agentic-security-scanner.py | `_inline_agentic_scan` | ✅ |
| 7 | `code_simplify` | `code_simplify_fallback` | code-simplifier.py | `_inline_simplify` | ✅ |
| 8 | `session_manage` | `session_manage_fallback` | init-session.py / session-catchup.py / session-persist.py | `_inline_session_manage` | ✅ |
| 9 | `workflow_dispatch` | `workflow_dispatch_fallback` | project-initializer.py | `_load_workflow` | ✅ |
| 10 | `agent_status` | `agent_status_fallback` | skill-test.py + 静态注册表扫描 | `_inline_agent_status` | ✅ |
| 11 | `agent_manage` | `agent_manage_fallback` | — (无脚本) | `_inline_agent_manage` | ✅ |
| 12 | `hook_manage` | `hook_manage_fallback` | hook_scripts映射 | `_inline_hook_manage` | ✅ |
| 13 | `resource_load_status` | `resource_load_status_fallback` | resource_state.json读取 | `_inline_resource_load_status` | ✅ |
| 14 | `resource_subscribe` | `resource_subscribe_fallback` | — (无脚本) | `_inline_resource_subscribe` | ✅ |
| 15 | `context_compress` | `context_compress_fallback` | context-compressor.py | `_inline_context_compress` | ✅ |
| 16 | `server_health` | `server_health_fallback` | health-checker.py | `_inline_server_health` | ✅ |
| 17 | `decision_log` | `fallback_decision_log` | decision-log.py | `_inline_decision_log` | ✅ |
| 18 | `token_budget` | `fallback_token_budget` | token-budget-guard.py | `_inline_token_budget` | ✅ |
| 19 | `project_init` | `fallback_project_init` | project-initializer.py | `_inline_project_init` | ✅ |
| 20 | `metrics_report` | `metrics_report_fallback` | test-reporter.py | `_inline_metrics_report` | ✅ |
| 21 | `config_manage` | `config_manage_fallback` | — (无脚本) | `_inline_config_manage` | ✅ |
| 22 | `audit_query` | `audit_query_fallback` | — (无脚本) | `_inline_audit_query` + 内存审计日志 | ✅ |

### 6.3 DegradationManager 组件降级

> 源码位置: `degradation.py` L531-L561

| 组件 | 正常级别 | 降级级别 | 不可用级别 |
|------|----------|----------|-----------|
| `search_engine` | chromadb | sqlite_fts | keyword |
| `knowledge_base` | full | workspace_only | no_knowledge |
| `hooks` | full_hooks | essential_only | no_hooks |
| `resources` | full_resources | cached_only | minimal |

### 6.4 降级配置热加载

> 源码位置: `degradation.py` L1239-L1374

- 支持 `fallback_config.yaml` 和 `constraints.yaml` 两种配置源
- `constraints.yaml` 中的 `degradation.tool_fallbacks` 优先级更高
- 配置变更自动检测: watchfiles（优先）或 5s 轮询
- `_INLINE_FALLBACK_MAP` 提供内联降级函数名到实际函数的映射（22条）

---

## 7. mcpServers 配置 JSON 示例

> 源码位置: `xuansto-mcp-server/pyproject.toml` (version = "8.9.0-dev")

### 7.1 uvx 方式（推荐）

```json
{
  "mcpServers": {
    "xuansto-mcp-server": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/xuanyuanchumo/xuansto#subdirectory=xuansto-mcp-server",
        "xuansto-mcp"
      ],
      "env": {
        "XUANSTO_SKILL_ROOT": "/path/to/.trae/skills/xuansto-skill-v2",
        "XUANSTO_WORK_DIR": "/path/to/.xuansto"
      }
    }
  }
}
```

### 7.2 streamable-http 方式

```json
{
  "mcpServers": {
    "xuansto-mcp-server-http": {
      "url": "http://127.0.0.1:8000/mcp",
      "transport": "streamable-http",
      "headers": {
        "MCP-Protocol-Version": "2025-11-25"
      }
    }
  }
}
```

启动命令:
```bash
XUANSTO_TRANSPORT=streamable-http XUANSTO_HOST=127.0.0.1 XUANSTO_PORT=8000 xuansto-mcp
```

### 7.3 本地开发方式

```json
{
  "mcpServers": {
    "xuansto-mcp-server-dev": {
      "command": "python",
      "args": [
        "-m",
        "xuansto_mcp.server"
      ],
      "cwd": "/path/to/xuansto-mcp-server",
      "env": {
        "PYTHONPATH": "/path/to/xuansto-mcp-server/src",
        "XUANSTO_SKILL_ROOT": "/path/to/.trae/skills/xuansto-skill-v2",
        "XUANSTO_WORK_DIR": "/path/to/.xuansto"
      }
    }
  }
}
```

### 7.4 环境变量说明

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| `XUANSTO_TRANSPORT` | `stdio` | 传输方式: stdio / streamable-http |
| `XUANSTO_HOST` | `127.0.0.1` | HTTP监听地址(streamable-http时) |
| `XUANSTO_PORT` | `8000` | HTTP监听端口(streamable-http时) |
| `XUANSTO_API_KEY` | (空) | API密钥(设置后启用HTTP认证中间件) |
| `XUANSTO_SKILL_ROOT` | 自动检测 | Skill根目录 |
| `XUANSTO_WORK_DIR` | `{project_root}/.xuansto` | 工作目录 |
| `XUANSTO_KNOWLEDGE_CLEANUP_KEEP_LAST_N` | `10` | 知识版本清理保留数 |

---

## 8. Skill→MCP 交互协议

### 8.1 调用链路

```
Skill → MCP Client → MCP Server → HookEngine(pre) → RateLimiter → Tool → HookEngine(post) → AuditLogger → Response
```

详细时序:

1. Skill 通过 MCP Client 发起 `tools/call` 请求
2. Server 接收请求，执行 `_with_hook_interception` 包装逻辑
3. **Pre-Hook 拦截**: `HookEngine.execute_pre_hooks()` 执行所有前置Hook
   - 安全Hook失败 → 返回 `SECURITY_VIOLATION`
   - Pre-hook block → 返回 `BLOCKED_BY_HOOK`
4. **速率限制**: `check_rate_limit(tool_name)` 检查令牌桶
   - 超限 → 返回 `RATE_LIMITED`（含 `retry_after_seconds`）
5. **工具执行**: `retry_tool_call()` 执行工具逻辑（最多3次重试，指数退避）
6. **Post-Hook 处理**: `HookEngine.execute_post_hooks()` 执行后置Hook
7. **审计记录**: `AuditLogger.log()` 记录调用详情
8. **Token统计**: `record_token_usage()` 记录输入/输出Token消耗
9. 返回统一格式响应

### 8.2 统一响应格式

```json
{
  "status": "success | error",
  "data": { ... },
  "error": {
    "code": "ERROR_CODE",
    "message": "错误描述",
    "details": { ... },
    "retryable": true
  },
  "metadata": {
    "api_version": "3.0.0",
    "degradation_level": "L1_NORMAL",
    "degraded": false
  }
}
```

### 8.3 错误码体系

| 错误码 | 类别 | 可重试 |
|--------|------|--------|
| `ERR_VALIDATION` | client | 否 |
| `ERR_NOT_FOUND` | client | 否 |
| `ERR_TIMEOUT` | transient | 是 |
| `ERR_DEGRADATION` | transient | 是 |
| `ERR_RATE_LIMIT` | transient | 是 |
| `ERR_PERMISSION` | client | 否 |
| `ERR_WORKFLOW_NOT_FOUND` | client | 否 |
| `ERR_DUPLICATE` | client | 否 |
| `ERR_VERSION_CONFLICT` | transient | 是 |
| `ERR_UNAUTHORIZED` | client | 否 |
| `ERR_SERVICE_UNAVAILABLE` | transient | 是 |
| `BLOCKED_BY_HOOK` | server | 否 |
| `SECURITY_VIOLATION` | server | 否 |

### 8.4 重试策略

| 参数 | 值 | 说明 |
|------|-----|------|
| `max_retries` | 3 | 最大重试次数 |
| `base_delay` | 1.0s | 基础延迟 |
| 退避策略 | `1s → 2s → 4s` | 指数退避 |
| 可重试错误 | TIMEOUT, CONNECTION_ERROR, DEGRADATION, RATE_LIMITED | `_TRANSIENT_ERROR_CODES` |
| 不可重试错误 | VALIDATION_ERROR, PATH_NOT_FOUND, PERMISSION_DENIED | `_PERMANENT_ERROR_CODES` |

### 8.5 降级链路交互

当 MCP Tool 调用失败时，`DegradationExecutor` 按以下顺序尝试:

1. **Script Fallback**: 执行对应脚本（如 `skill-test.py`, `knowledge-server.py`），超时30s
2. **Inline Fallback**: 调用工具模块内的 `_inline_*` 函数（纯Python逻辑，无外部依赖）
3. **Minimal Response**: 返回 `{"status": "unavailable", "degraded": true}` 最小可用响应

所有降级结果均标记 `degraded: true`，客户端可据此调整行为。

### 8.6 安全边界

| 边界 | 实现方式 | 源码位置 |
|------|----------|----------|
| 路径安全 | `validate_path_safety()` 防止路径遍历 | `core/validator.py` → `resources/skill_resources.py` L67 |
| 安全Hook拦截 | pre-hook中security hook失败默认阻断 | `server.py` L70-L110 |
| 速率限制 | `check_rate_limit()` 每工具独立令牌桶 | `core/rate_limiter.py` → `server.py` L112-L124 |
| 审计日志 | 所有Tool调用记录到audit_log | `core/audit_logger.py` → `server.py` L130 |
| 降级隔离 | 降级结果标记 `degraded: true` | `core/degradation.py` L630-L645 |
| Token预算 | 超预算时返回 `TOKEN_BUDGET_EXCEEDED` | `tools/resource_load_status.py` |
| 状态完整性 | 降级状态文件SHA256哈希校验 | `core/degradation.py` L282-L287 |
| HTTP认证 | API Key中间件（可选，`XUANSTO_API_KEY`） | `server.py` L239-L273 |
