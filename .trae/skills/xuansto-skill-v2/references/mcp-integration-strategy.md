# MCP集成策略

> 版本: 3.0.0 | 更新日期: 2026-05-24 | 编码: UTF-8 | 行尾: LF

本文档定义 Xuansto Skill v2 与 xuansto-mcp-server 的完整集成策略，涵盖上下文预算管理、懒加载机制、降级策略、CLI替代方案、健康检查及工具-脚本映射关系。

## 目录

- [1. 集成架构概述](#1-集成架构概述)
- [2. 上下文窗口预算管理](#2-上下文窗口预算管理)
- [3. MCP工具懒加载策略](#3-mcp工具懒加载策略)
- [4. 三级降级策略](#4-三级降级策略)
- [5. CLI替代方案](#5-cli替代方案)
- [6. MCP健康检查机制](#6-mcp健康检查机制)
- [7. 工具-脚本完整映射表](#7-工具-脚本完整映射表)
- [8. MCP与知识服务集成](#8-mcp与知识服务集成)
- [9. MCP Resource集成](#9-mcp-resource集成)
- [10. 版本兼容性管理](#10-版本兼容性管理)

---

## 1. 集成架构概述

Xuansto Skill v2 通过 MCP（Model Context Protocol）协议与 xuansto-mcp-server 交互，提供17个原子工具驱动9阶段全生命周期开发流程。

### 1.1 集成层级

```
┌─────────────────────────────────────────────┐
│              SKILL.md (入口)                  │
│  渐进式加载: Phase 0→1→2→3                   │
├─────────────────────────────────────────────┤
│         MCP Tool Layer (优先)                │
│  17个原子工具 → xuansto-mcp-server           │
├─────────────────────────────────────────────┤
│         Script Layer (降级)                   │
│  Python/Node脚本 → scripts/ 目录             │
├─────────────────────────────────────────────┤
│         File System Layer (兜底)             │
│  本地文件读取 → references/ 知识库            │
└─────────────────────────────────────────────┘
```

### 1.2 调用优先级

| 优先级 | 调用方式 | 延迟 | 功能完整度 | 可靠性 |
|--------|----------|------|-----------|--------|
| 1 | MCP Tool | <100ms | 100% | 依赖MCP Server |
| 2 | REST API | <500ms | 90% | 依赖HTTP服务 |
| 3 | Python脚本 | 1-5s | 80% | 本地执行 |
| 4 | 文件系统 | <50ms | 50% | 始终可用 |

---

## 2. 上下文窗口预算管理

### 2.1 预算分配原则

每个MCP工具占用约5-10%上下文窗口，同时启用不超过10个工具，确保核心推理空间不被挤占。

### 2.2 上下文预算分配

| 资源类别 | 预算占比 | 说明 |
|----------|----------|------|
| 核心推理 | 40-50% | Agent推理、决策、代码生成 |
| MCP工具定义 | 15-20% | 当前活跃工具的Schema和描述 |
| 参考文档 | 15-20% | 按需加载的references/文档 |
| 知识检索结果 | 10-15% | knowledge_search返回的知识条目 |
| 会话状态 | 5-10% | 决策日志、进度追踪、工作流状态 |

### 2.3 工具启用上限

| 上下文窗口大小 | 最大同时启用工具数 | 最大活跃工具数 |
|---------------|-------------------|---------------|
| 200K+ | 10 | 80 |
| 128K | 7 | 50 |
| 64K | 4 | 30 |

### 2.4 预算超支处理

| Token使用率 | 处理策略 |
|-------------|----------|
| < 60% | 正常运行，所有MCP工具可用 |
| 60-80% | 释放P3资源，禁用非关键MCP工具 |
| 80-95% | 释放P2资源，仅保留核心MCP工具（skill_analyze, quality_gate_check, session_manage） |
| ≥ 95% | 释放P1资源，仅保留P0工具，降级为脚本调用 |

---

## 3. MCP工具懒加载策略

### 3.1 按Phase加载

MCP工具按工作流Phase按需加载，避免全量加载占用上下文：

| Phase | 可加载MCP工具 | 说明 |
|-------|-------------|------|
| Phase 0 | skill_analyze, workflow_dispatch, agent_status, resource_load_status, project_init | 项目初始化与分析 |
| Phase 1 | knowledge_search, resource_load_status | 需求检索与探索 |
| Phase 2 | knowledge_search, resource_load_status, decision_log, token_budget | 架构设计与决策 |
| Phase 3 | — | 测试设计阶段无MCP需求 |
| Phase 4 | quality_gate_check, agent_status, hook_manage | 代码实现与质量检查 |
| Phase 5 | security_scan, spec_drift_detect, agent_status | 测试验证与安全扫描 |
| Phase 6 | quality_gate_check | 验收确认 |
| Phase 7 | code_simplify, context_compress | 持续重构与压缩 |
| Phase 8 | — | 部署交付阶段使用CLI为主 |

### 3.2 按命令加载

| 命令 | 加载的MCP工具 |
|------|-------------|
| /init | skill_analyze, knowledge_search, workflow_dispatch, project_init, decision_log |
| /brainstorm | knowledge_search, workflow_dispatch |
| /clarify | knowledge_search, workflow_dispatch, quality_gate_check |
| /plan | skill_analyze, knowledge_search, agent_status, workflow_dispatch, decision_log, token_budget |
| /spec | workflow_dispatch, quality_gate_check, spec_drift_detect |
| /design | quality_gate_check, knowledge_search, workflow_dispatch |
| /implement | workflow_dispatch, quality_gate_check, hook_manage |
| /test | quality_gate_check, workflow_dispatch |
| /review | quality_gate_check, security_scan, code_simplify |
| /audit | security_scan, quality_gate_check, spec_drift_detect |
| /fix | session_manage, quality_gate_check, hook_manage |
| /accept | quality_gate_check, workflow_dispatch |
| /deploy | quality_gate_check, server_health, workflow_dispatch |
| /simplify | code_simplify, quality_gate_check, context_compress |
| /refactor | code_simplify, quality_gate_check, context_compress |
| /loop | workflow_dispatch, session_manage, resource_load_status, token_budget, decision_log |
| /learn | knowledge_search, knowledge_inject, session_manage |
| /sprint | workflow_dispatch, session_manage, resource_load_status, token_budget, project_init |

### 3.3 卸载策略

Phase切换时自动卸载上一Phase的MCP工具：

1. Phase开始：加载当前Phase所需MCP工具
2. Phase执行：仅保留当前Phase工具在上下文中
3. Phase结束：卸载当前Phase工具，保留核心决策摘要
4. 跨Phase共享工具（如session_manage）常驻上下文

---

## 4. 三级降级策略

### 4.1 降级判定流程

```
尝试 MCP Tool 调用
  ↓ 失败/超时(>5s)
尝试 REST API 调用
  ↓ 失败/超时(>10s)
降级为 Python 脚本调用
  ↓ 失败
降级为文件系统读取
```

### 4.2 降级级别定义

| 降级级别 | 名称 | 触发条件 | 可用功能 |
|----------|------|----------|----------|
| Level 0 | 正常 | MCP Server健康 | 全部17个MCP工具 |
| Level 1 | MCP降级 | MCP Server不可用/超时 | Python脚本替代 |
| Level 2 | 脚本降级 | 脚本执行失败 | 内嵌逻辑替代 |
| Level 3 | 最小可用 | 所有外部服务不可用 | 仅文件系统读取 |

### 4.3 降级结果格式统一

降级模式下结果包装为与MCP工具相同的JSON结构，确保上层调用方无需感知降级：

```json
{
  "status": "success|degraded|error",
  "data": { ... },
  "metadata": {
    "tool": "tool_name",
    "latency_ms": 0,
    "degraded": true,
    "fallback_method": "script|inline|filesystem"
  }
}
```

### 4.4 自动恢复

| 恢复条件 | 检查间隔 | 恢复动作 |
|----------|----------|----------|
| MCP Server心跳恢复 | 30秒 | 从Level 1恢复到Level 0 |
| 脚本执行成功 | 每次调用 | 保持Level 1，下次尝试MCP |
| 文件系统读取成功 | 每次调用 | 保持Level 2，下次尝试脚本 |

---

## 5. CLI替代方案

CLI功能完善的平台优先使用CLI+Skill组合，减少MCP上下文占用：

### 5.1 CLI优先级矩阵

| 平台/服务 | CLI工具 | 优先级 | 替代MCP工具 |
|-----------|---------|--------|-------------|
| GitHub | gh CLI | CLI优先 | workflow_dispatch(部分) |
| Supabase | supabase CLI | CLI优先 | — |
| Vercel | vercel CLI | CLI优先 | workflow_dispatch(部署) |
| Cloudflare | wrangler CLI | CLI优先 | — |
| Docker | docker CLI | CLI优先 | — |
| Kubernetes | kubectl CLI | CLI优先 | — |
| AWS | aws CLI | CLI优先 | — |

### 5.2 CLI降级策略

当CLI不可用时，回退到MCP工具或脚本：

```
CLI调用 → 失败 → MCP Tool调用 → 失败 → 脚本调用 → 失败 → 内嵌逻辑
```

---

## 6. MCP健康检查机制

### 6.1 SessionStart Hook检查

会话启动时自动检查MCP Server可用性：

```python
async def check_mcp_health():
    try:
        result = await server_health(action="check")
        if result["status"] == "HEALTHY":
            return "mcp_available"
        else:
            return "mcp_degraded"
    except Exception:
        return "mcp_unavailable"
```

### 6.2 健康检查频率

| 场景 | 检查频率 | 超时阈值 |
|------|----------|----------|
| 会话启动 | 1次 | 5秒 |
| MCP工具调用前 | 每次调用 | 工具超时 |
| 长时间运行任务 | 每5分钟 | 5秒 |
| 降级模式恢复检测 | 每30秒 | 5秒 |

### 6.3 健康状态与降级联动

| server_health状态 | 降级行为 |
|-------------------|----------|
| HEALTHY | 正常模式，全部MCP工具可用 |
| DEGRADED | 部分工具降级，非关键工具使用脚本替代 |
| UNAVAILABLE | 全量降级，所有工具使用脚本或内嵌逻辑 |

---

## 7. 工具-脚本完整映射表

### 7.1 MCP工具到脚本的降级映射

| MCP工具 | 降级脚本 | 降级结果格式 |
|---------|----------|-------------|
| skill_analyze | scripts/skill-test.py --analyze | 统一JSON |
| knowledge_search | scripts/knowledge-server.py --search | 统一JSON |
| knowledge_inject | scripts/knowledge_server/main.py --inject | 统一JSON |
| quality_gate_check | scripts/skill-test.py --gate | 统一JSON |
| spec_drift_detect | scripts/spec-drift-detector.py → 内联漂移检测 | 统一JSON |
| security_scan | scripts/agentic-security-scanner.py → 内嵌agentic+dependency扫描 | 统一JSON |
| code_simplify | scripts/code-simplifier.py → 内嵌simplify+dedup | 统一JSON |
| session_manage | scripts/init-session.py / session-catchup.py / session-persist.py | 统一JSON |
| workflow_dispatch | scripts/project-initializer.py (start) / 内联Phase推进 | 统一JSON |
| agent_status | 静态注册表查询(agents/) / scripts/skill-test.py --agents | 统一JSON |
| hook_manage | scripts/check-encoding.py / token-budget-guard.py / session-persist.py / 内联Hook | 统一JSON |
| resource_load_status | 内联状态检查(resource_state.json) | 统一JSON |
| context_compress | scripts/context-compressor.py | 统一JSON |
| server_health | scripts/health-checker.py → 降级状态返回 | 统一JSON |
| decision_log | 内联JSON记录 | 统一JSON |
| token_budget | scripts/token-budget-guard.py / 内联估算 | 统一JSON |
| project_init | scripts/project-initializer.py / 内联模板生成 | 统一JSON |

### 7.2 知识检索降级链

```
ChromaDB语义检索 → SQLite FTS5全文检索 → 关键词匹配 → 内嵌模板
```

| 降级级别 | 检索方式 | 精度 | 延迟 |
|----------|----------|------|------|
| Level 0 | ChromaDB + FTS5 混合检索 | 高 | <3s |
| Level 1 | SQLite FTS5 全文检索 | 中 | <1s |
| Level 2 | 关键词匹配 | 低 | <500ms |
| Level 3 | 内嵌知识模板 | 固定 | <100ms |

---

## 8. MCP与知识服务集成

### 8.1 知识服务MCP接口

| MCP工具 | 知识服务操作 | 降级方式 |
|---------|-------------|----------|
| knowledge_search(action="retrieve") | 三层知识库检索 | ChromaDB→FTS5→关键词 |
| knowledge_search(action="inject") | 知识注入到上下文 | 内联格式化注入 |
| knowledge_search(action="precipitate") | 经验沉淀到知识库 | 本地文件写入 |
| knowledge_inject | 知识注入到会话上下文 | 内联注入 |

### 8.2 知识服务降级与MCP降级联动

| MCP状态 | 知识服务状态 | 可用操作 |
|---------|-------------|----------|
| 可用 | 可用 | 全部：retrieve/inject/precipitate |
| 不可用 | 可用 | 脚本调用：retrieve/inject/precipitate |
| 不可用 | 不可用 | 文件系统：仅retrieve(关键词) |

---

## 9. MCP Resource集成

### 9.1 资源URI定义

| URI | 内容 | 加载Phase |
|-----|------|-----------|
| xuansto://loading/status | 加载状态JSON | Phase 0+ |
| xuansto://references/agent-registry | Agent注册表 | Phase 2+ |
| xuansto://references/quality-gates | 质量门禁定义 | Phase 2+ |
| xuansto://references/workflow-phases | 工作流阶段定义 | Phase 1+ |

### 9.2 resource_load_status工具

| Action | 描述 | 加载Phase |
|--------|------|-----------|
| status | 查询当前加载状态 | 不变 |
| preload | 预加载指定Phase资源 | 推进到目标Phase |
| cache | 查询缓存状态 | 不变 |
| clear_cache | 清理缓存 | 降级到SKELETON |
| loading_progress | 查询加载进度 | 不变 |

---

## 10. 版本兼容性管理

### 10.1 版本兼容矩阵

| Skill版本 | 最低MCP Server版本 | API版本 | 兼容说明 |
|-----------|-------------------|---------|----------|
| 8.0.0 | 4.0.0 | 3.0.0 | 17工具+metrics_report |
| 7.0.0 | 3.5.0 | 2.0.0 | 15工具 |
| 6.0.0 | 3.0.0 | 1.0.0 | 13工具 |

### 10.2 版本不兼容处理

当MCP Server版本低于最低兼容版本时：

1. server_health(action="version") 返回版本信息
2. 比对版本号，低于最低兼容版本
3. 输出版本不兼容警告
4. 自动降级到脚本模式执行
5. 记录版本不兼容事件到 `.skill-logs/`

### 10.3 API版本协商

| API版本 | 支持的工具集 | 新增工具 |
|---------|-------------|----------|
| 3.0.0 | 全部17个 | metrics_report, knowledge_inject, project_init |
| 2.0.0 | 15个 | server_health, decision_log, token_budget |
| 1.0.0 | 13个 | 基础工具集 |

当API版本不匹配时，仅使用该API版本支持的工具子集，其余工具降级到脚本调用。
