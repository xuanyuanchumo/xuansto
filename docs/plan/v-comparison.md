# Xuansto Skill 版本功能对比文档

> 版本: 4.0.0 | 日期: 2026-05-24 | 状态: 已更新
> 仓库: https://github.com/xuanyuanchumo/xuansto
> 覆盖范围: v1.0.0 (V_PREVIOUS_MAJOR, 已移除) → v8.0.0 (V_CURRENT) → v8.1.0 (下一小版本) → v9.0.0 (下一大版本)

---

## 目录

1. [版本概览](#1-版本概览)
2. [架构形态对比](#2-架构形态对比)
3. [核心功能对比](#3-核心功能对比)
4. [性能对比](#4-性能对比)
5. [特效加载方式对比](#5-特效加载方式对比)
6. [API契约对比](#6-api契约对比)
7. [数据模型对比](#7-数据模型对比)
8. [已知限制对比](#8-已知限制对比)
9. [版本演进路线图](#9-版本演进路线图)

---

## 1. 版本概览

| 属性 | V_PREVIOUS_MAJOR | V_CURRENT | v8.1.0 | v9.0.0 |
|------|-------------------|-----------|--------|--------|
| **Skill版本** | xuansto-skill v1.0.0 | xuansto-skill-v2 v8.0.0 | xuansto-skill-v2 v8.1.0 | xuansto-skill-v2 v9.0.0 |
| **MCP Server版本** | 无 | xuansto-mcp-server v8.0.0 | xuansto-mcp-server v8.1.0 | xuansto-mcp-server v9.0.0 |
| **仓库状态** | ⚠️ 已移除，不在仓库中 | ✅ 当前版本 | 计划中 | 计划中 |
| **原始名称** | multi-agent-sdd-tdd-orchestrator | xuansto-skill-v2 | xuansto-skill-v2 | xuansto-skill-v2 |
| **Agent数量** | 35 | 57 ⬆️ | 57 ➡️ | 57+ ⬆️ |
| **编排层数** | 8 | 13 ⬆️ | 13 ➡️ | 13 ➡️ |
| **工作流数** | 8 | 15 ⬆️ | 15 ➡️ | 15+ ⬆️ |
| **命令数** | 13 | 31 ⬆️ | 31 ➡️ | 31+ ⬆️ |
| **MCP Tool数** | 0 | 20 🆕 | 20 ➡️ | 22+ ⬆️ |
| **MCP Resource数** | 0 | 8 🆕 | 8 ➡️ | 10+ ⬆️ |
| **质量门禁** | 15 | 54 ⬆️ | 54 ➡️ | 54+ ⬆️ |
| **降级脚本** | 12 | 60+ ⬆️ | 60+ ➡️ | 60+ ➡️ |
| **模板数** | 12 | 19 ⬆️ | 19 ➡️ | 19+ ⬆️ |
| **参考文档** | 14 | 75+ ⬆️ | 75+ ➡️ | 80+ ⬆️ |
| **SKILL.md行数** | ~765 | <200 ⬆️ | <200 ➡️ | <200 ➡️ |
| **统一数据库** | 无 | xuansto.db(8表) 🆕 | xuansto.db(8表) ➡️ | xuansto.db(10+表) ⬆️ |
| **问题修复率** | N/A | 97.8% (45/46) | 97.8% (45/46) ➡️ | 100% ⬆️ |
| **已知限制** | N/A | U-45(Skill.md Phase标记) | U-45(可选改进) ➡️ | 无 🆕 |

> **说明**: V_PREVIOUS_MAJOR (xuansto-skill v1.0.0) 已从仓库彻底移除，仅作历史参照。当前仓库仅含 `xuansto-mcp-server/` + `.trae/skills/xuansto-skill-v2/` + `README.md` + `.gitignore` + `.editorconfig`。

---

## 2. 架构形态对比

### 2.1 整体架构

| 维度 | V_PREVIOUS_MAJOR | V_CURRENT | v8.1.0 | v9.0.0 |
|------|-------------------|-----------|--------|--------|
| **架构模式** | 单体Skill ⚠️已移除 | Skill层 + MCP Server双层 ⬆️ | Skill层 + MCP Server双层 ➡️ | Skill层 + MCP Server双层 + 数据层统一 ⬆️ |
| **Skill层职责** | 全部(触发+路由+执行+降级) | 触发+路由+声明+约束 ⬆️ | 触发+路由+声明+约束 ➡️ | 触发+路由+声明+约束 ➡️ |
| **执行层** | 内嵌脚本直接调用 | + MCP Server独立进程 🆕 | + MCP Server独立进程 ➡️ | + MCP Server独立进程 ➡️ |
| **通信协议** | 无(文件系统直读) | + MCP协议(stdio) 🆕 | + MCP协议(stdio) ➡️ | + MCP协议(stdio+SSE可选) ⬆️ |
| **进程模型** | 单进程 | 双进程(Skill + MCP Server) 🆕 | 双进程 ➡️ | 双进程 ➡️ |
| **配置管理** | 内嵌SKILL.md | + 外部化YAML+热重载MCP入口 ⬆️ | + 外部化YAML+Schema校验 ⬆️ | + 外部化YAML+Schema校验+热重载MCP入口 ➡️ |
| **降级架构** | 无统一降级 | 统一降级框架(异步+完整链+20/20覆盖) 🆕 | 统一降级框架(20/20覆盖) ➡️ | + 完整降级+恢复+抖动 ➡️ |
| **项目支持** | 单项目 | 单项目 ➡️ | 单项目 ➡️ | 多项目并行 🆕 |
| **扩展机制** | 无 | 无 | 无 | 插件系统 🆕 |

### 2.2 架构分层

| 分层 | V_PREVIOUS_MAJOR | V_CURRENT | v8.1.0 | v9.0.0 |
|------|-------------------|-----------|--------|--------|
| **Skill层** | SKILL.md(765行，全内嵌) ⚠️已移除 | SKILL.md(<200行)+外部YAML ⬆️ | SKILL.md(<200行)+Phase标记+外部YAML ⬆️ | SKILL.md(<200行)+Phase标记+外部YAML ➡️ |
| **执行层** | 无 | 20 MCP Tool + 8 Resource 🆕 | 20 MCP Tool + 8 Resource ➡️ | 22+ MCP Tool + 10+ Resource ⬆️ |
| **资源层** | agents/commands/scripts | + references/templates/workflows ⬆️ | + references补全+evals修正 ⬆️ | + 统一数据层+插件资源 ⬆️ |
| **依赖层** | Python脚本 | + mcp[cli]+pydantic+pyyaml ⬆️ | + mcp[cli]+pydantic+pyyaml ➡️ | + mcp[cli]+pydantic+pyyaml+watchfiles ⬆️ |

### 2.3 架构关键差异

| 差异点 | V_PREVIOUS_MAJOR → V_CURRENT | V_CURRENT → v8.1.0 | v8.1.0 → v9.0.0 |
|--------|------------------------------|---------------------|-------------------|
| **核心变革** | 单体→双层解耦(v1已移除) | Phase标记补全Skill侧 | 双层→三层(数据层统一) |
| **执行路径** | 脚本直调→MCP优先+脚本降级 | Skill侧Phase标记增强 | MCP+脚本+插件三路径 |
| **状态管理** | 文件分散→统一SQLite | 无变化 | SQLite→分布式状态协调 |
| **加载模型** | 全量→渐进式4阶段 | Phase标记补全Skill侧 | 渐进式+运行时协商 |

---

## 3. 核心功能对比

### 3.1 Agent体系

| 维度 | V_PREVIOUS_MAJOR | V_CURRENT | v8.1.0 | v9.0.0 |
|------|-------------------|-----------|--------|--------|
| **Agent数量** | 35 | 57 ⬆️ | 57 ➡️ | 57+ ⬆️ |
| **编排层数** | 8 | 13 ⬆️ | 13 ➡️ | 13 ➡️ |
| **Agent注册方式** | SKILL.md内嵌索引 | + 外部registry.yaml ⬆️ | + 外部registry.yaml ➡️ | + 外部registry.yaml+插件注册 🆕 |
| **模型路由** | 无 | + fast/standard/deep三级 🆕 | + fast/standard/deep三级 ➡️ | + fast/standard/deep三级 ➡️ |
| **Agent合并策略** | 无 | + 声明但未执行 | + 运行时合并执行 ⬆️ | + 运行时合并执行 ➡️ |
| **Agent动态创建** | 无 | + agent_status(create) 🆕 | + agent_status(create) ➡️ | + agent_manage(create) ⬆️ |
| **Agent调度** | 静态分配 | + Phase感知调度 ⬆️ | + Phase感知调度 ➡️ | + Phase感知+规模自适应调度 ⬆️ |
| **跨项目Agent** | 无 | 无 | 无 | + 分布式Agent协调 🆕 |

### 3.2 工作流

| 维度 | V_PREVIOUS_MAJOR | V_CURRENT | v8.1.0 | v9.0.0 |
|------|-------------------|-----------|--------|--------|
| **工作流数** | 8 | 15 ⬆️ | 15 ➡️ | 15+ ⬆️ |
| **Phase数** | 8 | 9 ⬆️ (含Phase 0初始化) | 9 ➡️ | 9 ➡️ |
| **工作流定义** | SKILL.md内描述 | + 独立YAML+MD文件 ⬆️ | + 独立YAML+MD文件 ➡️ | YAML为权威源，MD由YAML生成 ⬆️ |
| **工作流调度** | 手动Phase推进 | + MCP workflow_dispatch ⬆️ | + MCP workflow_dispatch ➡️ | + MCP workflow_dispatch ➡️ |
| **工作流快照** | 无 | + gzip压缩快照 🆕 | + gzip压缩快照 ➡️ | + gzip压缩快照+AES-256-GCM加密 ⬆️ |
| **工作流恢复** | 无 | + recover action 🆕 | + recover action ➡️ | + recover action ➡️ |
| **SDD+TDD融合** | 基础 | + full/medium/fast三档 ⬆️ | + full/medium/fast三档 ➡️ | + full/medium/fast三档 ➡️ |
| **跨项目工作流** | 无 | 无 | 无 | + 多项目编排 🆕 |

### 3.3 质量门禁

| 维度 | V_PREVIOUS_MAJOR | V_CURRENT | v8.1.0 | v9.0.0 |
|------|-------------------|-----------|--------|--------|
| **门禁数量** | 15 | 54 ⬆️ | 54 ➡️ | 54+ ⬆️ |
| **门禁检查方式** | 脚本检查 | + MCP quality_gate_check ⬆️ | + MCP quality_gate_check ➡️ | + MCP quality_gate_check ➡️ |
| **3-Strike协议** | 无 | + 自动修复→换策略→升级 🆕 | + 自动修复→换策略→升级 ➡️ | + 自动修复→换策略→升级 ➡️ |
| **容差规则** | 无 | + 数值±0.5%/比率2%/布尔无/安全无 🆕 | + 数值±0.5%/比率2%/布尔无/安全无 ➡️ | + 数值±0.5%/比率2%/布尔无/安全无 ➡️ |
| **门禁异常** | 无 | + PASS_WITH_NOTE+WARN+BLOCK 🆕 | + PASS_WITH_NOTE+WARN+BLOCK ➡️ | + PASS_WITH_NOTE+WARN+BLOCK ➡️ |
| **自定义门禁** | 无 | 无 | 无 | + 插件门禁注册 🆕 |

### 3.4 知识管理

| 维度 | V_PREVIOUS_MAJOR | V_CURRENT | v8.1.0 | v9.0.0 |
|------|-------------------|-----------|--------|--------|
| **知识检索** | 无 | + knowledge_search(retrieve) 🆕 | + knowledge_search(retrieve) ➡️ | + knowledge_search(retrieve) ➡️ |
| **知识注入** | 无 | + knowledge_inject(inject) 🆕 | + knowledge_inject(inject) ➡️ | + knowledge_inject(inject) ➡️ |
| **经验沉淀** | 无 | + knowledge_inject(precipitate) 🆕 | + knowledge_inject(precipitate) ➡️ | + knowledge_inject(precipitate) ➡️ |
| **搜索降级链** | 无 | HybridSearchEngine: ChromaDB(可选)→SQLite FTS→关键词 🆕 | ChromaDB(可选)→SQLite FTS→关键词 ➡️ | + SQLite FTS5+BM25为主，ChromaDB可选增强 ⬆️ |
| **ChromaDB依赖** | 无 | 可选增强(默认BM25) ⬆️ | 可选增强(默认BM25) ➡️ | 可选增强(默认BM25) ➡️ |
| **知识闭环** | 无 | Retrieve→Inject→Precipitate完整闭环 🆕 | Retrieve→Inject→Precipitate完整闭环 ➡️ | Retrieve→Inject→Precipitate完整闭环 ➡️ |
| **职责边界** | 无 | knowledge_search只读，knowledge_inject只写 ⬆️ | knowledge_search只读，knowledge_inject只写 ➡️ | knowledge_search只读，knowledge_inject只写 ➡️ |
| **跨项目知识** | 无 | 无 | 无 | + 知识共享与隔离 🆕 |

### 3.5 安全能力

| 维度 | V_PREVIOUS_MAJOR | V_CURRENT | v8.1.0 | v9.0.0 |
|------|-------------------|-----------|--------|--------|
| **安全扫描** | OWASP Top 10 | + OWASP Agentic Top 10 ⬆️ | + OWASP Agentic Top 10 ➡️ | + OWASP Agentic Top 10 ➡️ |
| **依赖扫描** | 无 | + dependency漏洞扫描 🆕 | + dependency漏洞扫描 ➡️ | + dependency漏洞扫描 ➡️ |
| **路径安全** | 无 | + validator.py防遍历 🆕 | + validator.py防遍历 ➡️ | + validator.py防遍历 ➡️ |
| **Hook安全阻断** | 无 | + security-block Hook 🆕 | + security-block Hook ➡️ | + security-block Hook(失败默认阻塞) ➡️ |
| **编码安全** | UTF-8检查 | + UTF-8无BOM+无U+FFFD ⬆️ | + UTF-8无BOM+无U+FFFD ➡️ | + UTF-8无BOM+无U+FFFD ➡️ |
| **速率限制** | 无 | + 令牌桶速率限制 🆕 | + 令牌桶速率限制 ➡️ | + 令牌桶速率限制 ➡️ |
| **模板参数白名单** | 无 | + name参数正则白名单 🆕 | + name参数正则白名单 ➡️ | + name参数正则白名单 ➡️ |
| **快照加密** | 无 | + AES-256-GCM可选加密 🆕 | + AES-256-GCM可选加密 ➡️ | + AES-256-GCM可选加密 ➡️ |
| **零信任模式** | 无 | 无 | 无 | + 零信任Agent通信 🆕 |

### 3.6 会话与决策

| 维度 | V_PREVIOUS_MAJOR | V_CURRENT | v8.1.0 | v9.0.0 |
|------|-------------------|-----------|--------|--------|
| **会话管理** | 无 | + session_manage(7种action) 🆕 | + session_manage(7种action) ➡️ | + session_manage(7种action) ➡️ |
| **会话持久化** | 无 | + save/load/track/restore 🆕 | + save/load/track/restore ➡️ | + save/load/track/restore ➡️ |
| **决策日志** | 无 | + decision_log(6种action) 🆕 | + decision_log(6种action) ➡️ | + decision_log(6种action) ➡️ |
| **决策透明化** | 无 | + ADR集成 🆕 | + ADR集成 ➡️ | + ADR集成+Workflow关联 ⬆️ |
| **会话状态存储** | 无 | + 统一SQLite+MD双写 🆕 | + 统一SQLite+MD双写 ➡️ | + 统一SQLite+MD双写 ➡️ |
| **跨会话恢复** | 无 | + atexit+hash验证 🆕 | + atexit+hash验证 ➡️ | + atexit+hash验证+分布式快照 ⬆️ |

---

## 4. 性能对比

### 4.1 启动与加载

| 维度 | V_PREVIOUS_MAJOR | V_CURRENT | v8.1.0 | v9.0.0 |
|------|-------------------|-----------|--------|--------|
| **SKILL.md体积** | ~765行(全量加载) | <200行 ⬆️(骨架加载) | <200行 ➡️ | <200行 ➡️ |
| **初始Token占用** | 全量(估计50K+) | ≤2K ⬆️(Phase 0骨架) | ≤2K ➡️ | ≤2K ➡️ |
| **加载方式** | 一次性全量 | + 渐进式4阶段 🆕 | + 渐进式4阶段+Phase标记 ⬆️ | + 渐进式4阶段+运行时协商 ⬆️ |
| **Phase 0→1推进延迟** | N/A | ≤500ms(目标) | ≤500ms ➡️ | ≤500ms ➡️ |
| **Phase 1→2推进延迟** | N/A | ≤2000ms(目标) | ≤2000ms ➡️ | ≤2000ms ➡️ |
| **Phase 2→3推进延迟** | N/A | ≤5000ms(目标) | ≤5000ms ➡️ | ≤5000ms ➡️ |
| **降级切换延迟** | N/A | ≤100ms(目标) | ≤100ms ➡️ | ≤100ms ➡️ |

### 4.2 运行时性能

| 维度 | V_PREVIOUS_MAJOR | V_CURRENT | v8.1.0 | v9.0.0 |
|------|-------------------|-----------|--------|--------|
| **MCP调用延迟** | N/A | 依赖MCP Server | 依赖MCP Server ➡️ | 依赖MCP Server ➡️ |
| **降级脚本调用** | 同步subprocess.run | 同步subprocess.run(阻塞事件循环) ⬇️ | + asyncio异步调用 ⬆️ | + asyncio异步调用 ➡️ |
| **知识检索** | 无 | ChromaDB优先(降级频繁) ⬇️ | + BM25为主(稳定) ⬆️ | + BM25为主(稳定) ➡️ |
| **Token预算控制** | 无 | + 三级降级(L1/L2/L3) 🆕 | + 三级降级(L1/L2/L3) ➡️ | + 三级降级(L1/L2/L3)+动态调整 ⬆️ |
| **上下文压缩** | 无 | + semantic/selective/lossless 🆕 | + semantic/selective/lossless ➡️ | + semantic/selective/lossless+精确Token估算 ⬆️ |
| **资源缓存命中率** | N/A | ≥80%(目标) | ≥80%(目标) ➡️ | ≥80%(目标) ➡️ |
| **最大并发MCP调用** | N/A | 10 | 10 ➡️ | 10 ➡️ |
| **健康检查间隔** | N/A | 可配置(5s~300s) ✅ | 可配置(5s~300s) ➡️ | 可配置(5s~300s) ➡️ |

### 4.3 Token预算分配

| Phase | V_PREVIOUS_MAJOR | V_CURRENT | v8.1.0 | v9.0.0 |
|-------|-------------------|-----------|--------|--------|
| Phase 0 骨架 | N/A | ≤2K | ≤2K ➡️ | ≤2K ➡️ |
| Phase 1 功能 | N/A | ≤5K | ≤5K ➡️ | ≤5K ➡️ |
| Phase 2 增强 | N/A | ≤10K | ≤10K ➡️ | ≤10K ➡️ |
| Phase 3 完整 | N/A | ≤20K | ≤20K ➡️ | ≤20K ➡️ |
| Token降级L1 | N/A | ≥80%→减少并行+MCP降级 | ≥80%→减少并行+MCP降级 ➡️ | ≥80%→减少并行+MCP降级 ➡️ |
| Token降级L2 | N/A | ≥95%→精简模式(≤15 Agent) | ≥95%→精简模式(≤15 Agent) ➡️ | ≥95%→精简模式(≤15 Agent) ➡️ |
| Token降级L3 | N/A | 100%→最小串行(3 Agent) | 100%→最小串行(3 Agent) ➡️ | 100%→最小串行(3 Agent) ➡️ |

---

## 5. 特效加载方式对比

### 5.1 渐进式加载

| 维度 | V_PREVIOUS_MAJOR | V_CURRENT | v8.1.0 | v9.0.0 |
|------|-------------------|-----------|--------|--------|
| **加载模型** | 无(全量) | + 4阶段加载 🆕 | + 4阶段加载 ➡️ | + 4阶段加载 ➡️ |
| **触发机制** | 无 | + 自动+显式+披露触发 🆕 | + 自动+显式+披露触发 ➡️ | + 自动+显式+披露触发+运行时协商 ⬆️ |
| **状态机** | 无 | + 单向推进+Token降级 🆕 | + 单向推进+Token降级 ➡️ | + 单向推进+Token降级+DisclosureTransition ⬆️ |
| **DisclosureTransition** | 无 | Schema已定义但未使用 ⬇️ | + 启用 ⬆️ | + 完整实现 ➡️ |
| **Phase标记(Skill侧)** | 无 | 无 ⚠️ U-45已知限制 | + SKILL.md Phase标记 🆕 | + SKILL.md Phase标记 ➡️ |
| **Phase转换通知** | 无 | 无 | + MCP Notification 🆕 | + MCP Notification ➡️ |
| **进度反馈** | 无 | + loading_progress action 🆕 | + loading_progress action ➡️ | + loading_progress action ➡️ |
| **资源优先级** | 无 | + P0-P3四级 🆕 | + P0-P3四级 ➡️ | + P0-P3四级 ➡️ |
| **按需加载策略** | 无 | + lazy加载 🆕 | + lazy加载 ➡️ | + lazy加载 ➡️ |
| **Phase感知卸载** | 无 | + phase_transition_rules 🆕 | + phase_transition_rules ➡️ | + phase_transition_rules ➡️ |

### 5.2 披露规则

| 维度 | V_PREVIOUS_MAJOR | V_CURRENT | v8.1.0 | v9.0.0 |
|------|-------------------|-----------|--------|--------|
| **功能不可用提示** | 无 | + xuansto://loading/status 🆕 | + xuansto://loading/status ➡️ | + xuansto://loading/status ➡️ |
| **推进提示** | 无 | + resource_load_status(preload) 🆕 | + resource_load_status(preload) ➡️ | + resource_load_status(preload) ➡️ |
| **降级到可用范围** | 无 | + on_unavailable 3步披露 🆕 | + on_unavailable 3步披露 ➡️ | + on_unavailable 3步披露 ➡️ |
| **Token降级自动回退** | 无 | + 自动降级(不可逆) 🆕 | + 自动降级(不可逆) ➡️ | + 自动降级(不可逆)+显式恢复 ⬆️ |

### 5.3 Hook系统

| 维度 | V_PREVIOUS_MAJOR | V_CURRENT | v8.1.0 | v9.0.0 |
|------|-------------------|-----------|--------|--------|
| **Hook引擎** | 无 | + hook_engine.py 🆕 | + hook_engine.py ➡️ | + hook_engine.py ➡️ |
| **Hook配置** | 无 | + hooks.json(3级profile) 🆕 | + hooks.json(3级profile) ➡️ | + hooks.json(3级profile) ➡️ |
| **Hook类型安全** | 无 | 字符串(易拼写错误) ⬇️ | + HookType枚举 ⬆️ | + HookType枚举 ➡️ |
| **Hook生命周期** | 无 | + PreToolUse/PostToolUse/SessionStart/Stop/PreCompact 🆕 | + 5种生命周期 ➡️ | + 5种生命周期 ➡️ |
| **Hook失败处理** | 无 | 不阻塞主流程(安全检查可能被跳过) ⬇️ | + 安全类Hook失败默认阻塞 ⬆️ | + 安全类Hook失败默认阻塞 ➡️ |
| **Hook降级覆盖** | 无 | 部分(encoding-check/token-budget-check/session-save) ⬇️ | + 每个Hook独立降级脚本 ⬆️ | + 每个Hook独立降级脚本 ➡️ |
| **Hook失败告警** | 无 | 无 | + 失败计数+告警阈值 🆕 | + 失败计数+告警阈值 ➡️ |
| **自定义Hook** | 无 | 无 | 无 | + 插件Hook注册 🆕 |

---

## 6. API契约对比

### 6.1 MCP Tool接口

| 维度 | V_PREVIOUS_MAJOR | V_CURRENT | v8.1.0 | v9.0.0 |
|------|-------------------|-----------|--------|--------|
| **Tool数量** | 0 | 20 🆕 | 20 ➡️ | 22+ ⬆️ |
| **API版本** | N/A | 3.0.0(最低兼容1.0.0) | 3.0.0(最低兼容1.0.0) ➡️ | 4.0.0(最低兼容3.0.0) ⬆️ |
| **传输方式** | N/A | stdio | stdio ➡️ | stdio+SSE可选 ⬆️ |
| **输入校验** | N/A | + Pydantic BaseModel(extra="forbid") 🆕 | + Pydantic BaseModel(extra="forbid") ➡️ | + Pydantic BaseModel(extra="forbid") ➡️ |
| **Tool注册方式** | N/A | FastMCP装饰器+内部API ⬇️ | + 本地Tool注册映射表 ⬆️ | + 本地Tool注册映射表+插件注册 ⬆️ |
| **版本协商** | N/A | negotiate_version(不完整) ⬇️ | + 完整版本协商+功能列表 ⬆️ | + 完整版本协商+功能列表 ➡️ |
| **FALLBACK_MAP覆盖** | N/A | 20/20(完整覆盖) ✅ | 20/20(完整覆盖) ➡️ | 20/20(完整覆盖) ➡️ |

### 6.2 Tool职责演变

| Tool | V_PREVIOUS_MAJOR | V_CURRENT | v8.1.0 | v9.0.0 |
|------|-------------------|-----------|--------|--------|
| skill_analyze | 无 | + analyze 🆕 | + analyze ➡️ | + analyze ➡️ |
| knowledge_search | 无 | + retrieve(只读) 🆕 | + retrieve(只读) ➡️ | + retrieve(只读) ➡️ |
| knowledge_inject | 无 | + inject/precipitate(统一写入) 🆕 | + inject/precipitate(统一写入) ➡️ | + inject/precipitate(统一写入) ➡️ |
| quality_gate_check | 无 | + check(54门禁) 🆕 | + check(54门禁) ➡️ | + check(54门禁) ➡️ |
| spec_drift_detect | 无 | + detect 🆕 | + detect ➡️ | + detect ➡️ |
| security_scan | 无 | + scan 🆕 | + scan ➡️ | + scan ➡️ |
| code_simplify | 无 | + simplify 🆕 | + simplify ➡️ | + simplify ➡️ |
| session_manage | 无 | + 7种action 🆕 | + 7种action ➡️ | + 7种action ➡️ |
| workflow_dispatch | 无 | + 6种action 🆕 | + 6种action ➡️ | + 6种action ➡️ |
| agent_status | 无 | + 查询类(5种action) 🆕 | + 查询类(5种action) ➡️ | + 查询类(5种action) ➡️ |
| agent_manage | 无 | + 变更类(5种action) 🆕 | + 变更类(5种action)+降级 ⬆️ | + 变更类(5种action) ➡️ |
| hook_manage | 无 | + list/execute 🆕 | + list/execute ➡️ | + list/execute ➡️ |
| resource_load_status | 无 | + 6种action 🆕 | + 6种action+disclosure_transition ⬆️ | + 6种action+disclosure_transition ➡️ |
| context_compress | 无 | + compress 🆕 | + compress ➡️ | + compress+精确Token估算 ⬆️ |
| server_health | 无 | + check/negotiate_version 🆕 | + check/negotiate_version/capabilities ⬆️ | + check/negotiate_version/capabilities ➡️ |
| decision_log | 无 | + 6种action 🆕 | + 6种action ➡️ | + 6种action ➡️ |
| token_budget | 无 | + 4种action 🆕 | + 4种action ➡️ | + 4种action ➡️ |
| project_init | 无 | + 3种action 🆕 | + 3种action ➡️ | + 3种action ➡️ |
| metrics_report | 无 | + 按Tool/时间/类型查询 🆕 | + 按Tool/时间/类型查询+降级 ⬆️ | + 按Tool/时间/类型查询 ➡️ |
| config_manage | 无 | + reload/status/validate 🆕 | + reload/status/validate+降级 ⬆️ | + reload/status/validate ➡️ |
| plugin_manage | 无 | 无 | 无 | + install/list/unload 🆕 |
| project_switch | 无 | 无 | 无 | + switch/status 🆕 |

### 6.3 MCP Resource接口

| Resource | V_PREVIOUS_MAJOR | V_CURRENT | v8.1.0 | v9.0.0 |
|----------|-------------------|-----------|--------|--------|
| xuansto://config/skill | 无 | + 静态 🆕 | + 静态 ➡️ | + 静态 ➡️ |
| xuansto://references/quality-gates | 无 | + 静态 🆕 | + 静态 ➡️ | + 静态 ➡️ |
| xuansto://references/agent-registry | 无 | + 静态 🆕 | + 静态 ➡️ | + 静态 ➡️ |
| xuansto://references/workflow-phases | 无 | + 静态 🆕 | + 静态 ➡️ | + 静态 ➡️ |
| xuansto://templates/{name} | 无 | + 参数化 🆕 | + 参数化 ➡️ | + 参数化 ➡️ |
| xuansto://sessions/latest | 无 | + 静态 🆕 | + 参数化sessions/{id} ⬆️ | + 参数化sessions/{id} ➡️ |
| xuansto://loading/status | 无 | + 静态(JSON) 🆕 | + 静态(JSON) ➡️ | + 静态(JSON) ➡️ |
| xuansto://degradation/status | 无 | + JSON 🆕 | + JSON ➡️ | + JSON ➡️ |
| xuansto://metrics/summary | 无 | + JSON 🆕 | + JSON ➡️ | + JSON ➡️ |
| xuansto://agents/{layer}/{name} | 无 | 无 | + 参数化 🆕 | + 参数化 ➡️ |
| xuansto://plugins/registry | 无 | 无 | 无 | + 参数化 🆕 |

### 6.4 响应格式

| 维度 | V_PREVIOUS_MAJOR | V_CURRENT | v8.1.0 | v9.0.0 |
|------|-------------------|-----------|--------|--------|
| **统一响应格式** | 无 | + JSON(status/data/metadata) 🆕 | + JSON(status/data/metadata) ➡️ | + JSON(status/data/metadata) ➡️ |
| **错误码体系** | 无 | code+error_code并存(语义混淆) ⬇️ | + 统一error_code ⬆️ | + 统一error_code ➡️ |
| **降级标识** | 无 | + degraded字段 🆕 | + degraded字段+source:"fallback" ⬆️ | + degraded字段+source:"fallback" ➡️ |
| **重试策略** | 无 | + 指数退避(瞬态3次/永久0次) 🆕 | + 指数退避(瞬态3次/永久0次) ➡️ | + 指数退避+抖动(瞬态3次/永久0次) ⬆️ |
| **退避抖动** | 无 | 无(可能雪崩) ⬇️ | + 随机抖动 ⬆️ | + 随机抖动 ➡️ |

---

## 7. 数据模型对比

### 7.1 存储介质

| 维度 | V_PREVIOUS_MAJOR | V_CURRENT | v8.1.0 | v9.0.0 |
|------|-------------------|-----------|--------|--------|
| **SQLite** | 无 | 1个(xuansto.db统一8表) 🆕 | 1个(xuansto.db统一8表) ➡️ | 1个(xuansto.db统一10+表) ⬆️ |
| **ChromaDB** | 无 | 1个(可选增强) 🆕 | 1个(可选增强) ➡️ | 1个(可选增强) ➡️ |
| **JSON文件** | 无 | ~3类(已迁移到SQLite) ⬆️ | ~3类(已迁移到SQLite) ➡️ | ↓ 迁移到SQLite ⬆️ |
| **YAML文件** | 无 | ~4类(+Pydantic Schema校验) 🆕 | ~4类(+Pydantic Schema校验) ➡️ | ~4类(+Pydantic Schema校验) ➡️ |
| **Markdown文件** | 无 | ~3类(双写) 🆕 | ~3类(双写) ➡️ | + 双写(人类可读快照) ➡️ |
| **内存缓存** | 无 | + LRU缓存(cache.py)+持久化 🆕 | + LRU缓存(cache.py)+持久化 ➡️ | + 持久化到SQLite ➡️ |
| **gzip快照** | 无 | 1个(+AES-256-GCM加密) 🆕 | 1个(+AES-256-GCM加密) ➡️ | 1个(+AES-256-GCM加密) ➡️ |

### 7.2 关键数据实体

| 实体 | V_PREVIOUS_MAJOR | V_CURRENT | v8.1.0 | v9.0.0 |
|------|-------------------|-----------|--------|--------|
| **knowledge_entries** | 无 | + 统一SQLite+软删除 🆕 | + 统一SQLite+软删除 ➡️ | + 统一SQLite+软删除 ➡️ |
| **WorkflowInstance** | 无 | + SQLite+Decision关联 🆕 | + SQLite+Decision关联 ➡️ | + SQLite+Decision关联 ➡️ |
| **SessionState** | 无 | + 统一SQLite 🆕 | + 统一SQLite ➡️ | + 统一SQLite ➡️ |
| **DecisionRecord** | 无 | + 统一SQLite 🆕 | + 统一SQLite ➡️ | + 统一SQLite ➡️ |
| **ResourceLoadState** | 无 | + SQLite 🆕 | + SQLite ➡️ | + SQLite ➡️ |
| **DegradationState** | 无 | + SQLite 🆕 | + SQLite ➡️ | + SQLite ➡️ |
| **ErrorPattern** | 无 | + SQLite+error_type分类 🆕 | + SQLite+error_type分类 ➡️ | + SQLite+error_type分类 ➡️ |
| **MetricsSnapshot** | 无 | + SQLite+TTL自动清理 🆕 | + SQLite+TTL自动清理 ➡️ | + SQLite+TTL自动清理 ➡️ |
| **PluginRegistry** | 无 | 无 | 无 | + SQLite 🆕 |
| **ProjectState** | 无 | 无 | 无 | + SQLite 🆕 |

### 7.3 数据一致性

| 维度 | V_PREVIOUS_MAJOR | V_CURRENT | v8.1.0 | v9.0.0 |
|------|-------------------|-----------|--------|--------|
| **原子写入** | 无 | + atomic_write(tmpfile+os.replace) 🆕 | + atomic_write ➡️ | + atomic_write ➡️ |
| **竞态保护** | 无 | + 写入锁+hash验证 🆕 | + 写入锁+hash验证 ➡️ | + 写入锁+完整性校验 ➡️ |
| **崩溃恢复** | 无 | + atexit注册+hash验证 🆕 | + atexit注册+hash验证 ➡️ | + atexit注册+校验和 ➡️ |
| **跨库事务** | N/A | + 统一SQLite 🆕 | + 统一SQLite ➡️ | + 统一SQLite ➡️ |
| **缓存淘汰** | 无 | + LRU淘汰策略(cache.py) 🆕 | + LRU淘汰策略 ➡️ | + LRU淘汰策略 ➡️ |
| **指标清理** | 无 | + TTL自动清理(30天) 🆕 | + TTL自动清理(30天) ➡️ | + TTL自动清理(30天) ➡️ |
| **分布式一致性** | 无 | 无 | 无 | + 最终一致性协调 🆕 |

---

## 8. 已知限制对比

### 8.1 限制清单

| 限制 | V_PREVIOUS_MAJOR | V_CURRENT | v8.1.0 | v9.0.0 |
|------|-------------------|-----------|--------|--------|
| **降级机制不完整** | 无降级 ❌ | ✅ 统一降级框架(异步+20/20覆盖) | ➡️ 统一降级框架(20/20覆盖) | ➡️ 完整降级+恢复 |
| **参考文档不足** | 14个(完整) | ✅ 75+文件(完整) | ➡️ 75+文件 | ⬆️ 80+文件 |
| **状态持久化竞态** | N/A | ✅ 统一SQLite+写入锁+hash验证 | ➡️ 统一SQLite+写入锁 | ➡️ 统一SQLite |
| **Tool注册依赖内部API** | N/A | ✅ 本地_TOOL_FUNCTIONS注册表 | ⬆️ 本地注册映射表 | ⬆️ 本地注册映射表+插件注册 |
| **版本协商不完整** | N/A | ✅ MCP v8.0.0完整协商 | ⬆️ 完整版本协商+功能列表 | ➡️ 完整协商 |
| **knowledge职责模糊** | N/A | ✅ search只读/inject只写 | ➡️ search只读/inject只写 | ➡️ search只读/inject只写 |
| **ChromaDB降级频繁** | N/A | ✅ 可选增强(HybridSearchEngine) | ⬆️ BM25为主(稳定) | ➡️ BM25为主 |
| **降级脚本同步阻塞** | N/A | ⬇️ 同步阻塞事件循环 | ⬆️ asyncio异步调用 | ➡️ asyncio异步调用 |
| **Tool职责过载** | N/A | ✅ 拆分为agent_status+agent_manage | ➡️ 拆分完成 | ➡️ 拆分完成 |
| **Hook类型不安全** | N/A | ⬇️ 字符串代替枚举 | ⬆️ HookType枚举+安全阻断 | ➡️ HookType枚举 |
| **通知系统空实现** | N/A | ✅ MCPNotificationCallback | ⬆️ MCP Notification启用 | ➡️ MCPNotificationCallback |
| **错误码混淆** | N/A | ⬇️ code+error_code并存 | ⬆️ 统一error_code, deprecated code | ➡️ 统一error_code |
| **退避无抖动** | N/A | ⬇️ 可能雪崩 | ⬆️ backoff jitter | ➡️ 随机抖动 |
| **YAML无Schema校验** | N/A | 待实施 | ⬆️ Pydantic校验 | ➡️ Pydantic校验 |
| **SKILL.md行数** | ❌ 765行(超限) | ✅ <200行 | ⬆️ <200行+Phase标记 | ➡️ <200行 |
| **v1/v2文件重复** | N/A | ✅ v1标记ARCHIVED | ➡️ v1归档，v2唯一维护 | ➡️ v1归档 |
| **缺少CHANGELOG** | ❌ 无 | ✅ CHANGELOG.md已存在 | ➡️ CHANGELOG.md | ➡️ CHANGELOG.md |
| **缺少评估配置** | ❌ 无 | ✅ evals/目录已存在+Tool引用有效 | ➡️ evals修正(Tool引用有效) | ➡️ evals完整 |
| **缺少速率限制** | N/A | ✅ 令牌桶限流 | ➡️ 令牌桶限流 | ➡️ 令牌桶限流 |
| **快照无加密** | N/A | ✅ AES-256-GCM可选 | ➡️ AES-256-GCM可选 | ➡️ AES-256-GCM可选 |
| **缓存无LRU** | N/A | ✅ LRU淘汰(cache.py) | ➡️ LRU淘汰 | ➡️ LRU淘汰 |
| **指标无清理** | N/A | ✅ TTL自动清理(30天) | ➡️ TTL自动清理 | ➡️ TTL自动清理 |
| **知识无软删除** | N/A | ✅ deleted_at软删除 | ➡️ deleted_at软删除 | ➡️ deleted_at软删除 |
| **FALLBACK_MAP缺3个Tool** | N/A | ✅ 20/20完整覆盖(U-43已解决) | ➡️ 20/20完整覆盖 | ➡️ 完整覆盖 |
| **评估配置引用不存在Tool** | N/A | ✅ 全部Tool引用有效(U-44已解决) | ➡️ 全部Tool引用有效 | ➡️ 全部有效 |
| **SKILL.md无Phase标记** | N/A | ⚠️ U-45已知限制(Skill侧无Phase感知) | ⬆️ Phase标记添加(可选改进) | ➡️ Phase标记 |
| **健康检查间隔硬编码** | N/A | ✅ 可配置(5s~300s)(U-46已解决) | ➡️ 可配置 | ➡️ 可配置 |

### 8.2 限制统计

| 版本 | ❌ 废弃/未解决 | ⬇️ 削弱/部分解决 | ✅ 已修复/改善 | ⚠️ 已知限制 | 修复率 |
|------|--------------|-----------------|---------------|-------------|--------|
| V_PREVIOUS_MAJOR | 3 | 0 | 0 | 0 | 0% |
| V_CURRENT | 0 | 5 | 18 | 1(U-45) | 97.8% (45/46) |
| v8.1.0 | 0 | 0 | 25 | 1(U-45可选改进) | 97.8% (45/46) |
| v9.0.0 | 0 | 0 | 26 | 0 | 100% |

### 8.3 U-45 已知限制详情

| 编号 | 问题 | 严重度 | 当前状态 | v8.1.0方案 | v9.0.0方案 |
|------|------|--------|---------|------------|------------|
| U-45 | SKILL.md未使用Phase标记 | 低 | ⚠️ 已知限制 | 添加phase标注+Phase推进提示文本模板(可选改进) | Phase标记完整实现 |

### 8.4 已解决问题确认

| 编号 | 问题 | 解决版本 | 解决方案 |
|------|------|---------|---------|
| U-43 | FALLBACK_MAP缺3个新Tool降级(metrics_report/config_manage/agent_manage) | v8.0.0 | 新增3个fallback函数+FALLBACK_MAP+INLINE_FALLBACK_MAP补全，20/20完整覆盖 |
| U-44 | mcp_evaluation.xml引用不存在的Tool | v8.0.0 | 替换为knowledge_search/knowledge_inject实际action，全部Tool引用有效 |
| U-46 | DegradationManager健康检查间隔硬编码30s | v8.0.0 | .xuansto-config.yaml添加health_check_interval_sec字段，可配置(5s~300s) |

---

## 9. 版本演进路线图

### 9.1 里程碑时间线

```
V_PREVIOUS_MAJOR          V_CURRENT               v8.1.0                   v9.0.0
xuansto-skill v1.0.0      xuansto-skill-v2 v8.0.0  xuansto-skill-v2 v8.1.0  xuansto-skill-v2 v9.0.0
35 Agents / 8 Workflows   57 Agents / 20 Tools     57 Agents / 20 Tools     57+ Agents / 22+ Tools
⚠️ 已移除，不在仓库中     MCP Server v8.0.0        MCP Server v8.1.0        MCP Server v9.0.0
                          API v3.0.0               API v3.0.0               API v4.0.0

    │                         │                         │                         │
    │    重命名为xuansto       │    P0紧急修复            │    P4收尾修复            │    架构升级
    │    扩展到57 Agent        │    降级机制修复          │    Phase标记(可选)        │    多项目并行
    │    新增MCP Server        │    参考文档补充          │    评估配置已修正          │    插件系统
    │    渐进式加载            │    状态持久化修复        │    健康检查已可配置        │    分布式编排
    │                         │                         │                         │    零信任安全
    │    P1接口治理            │                         │                         │    SSE传输
    │    Tool注册解耦          │                         │                         │    自定义门禁
    │    版本协商完善          │                         │                         │    跨项目知识
    │    knowledge接口治理     │                         │                         │
    │    降级脚本异步化        │                         │                         │
    │    Tool职责拆分          │                         │                         │
    │    ChromaDB可选化        │                         │                         │
    │    工具文档补全          │                         │                         │
    │                         │                         │                         │
    │    P2架构加固            │                         │                         │
    │    数据层统一            │                         │                         │
    │    配置校验层            │                         │                         │
    │    Hook系统加固          │                         │                         │
    │    渐进式加载完善        │                         │                         │
    │    通知与错误治理        │                         │                         │
    │    Resource增强          │                         │                         │
    │    Agent与工作流治理     │                         │                         │
    │                         │                         │                         │
    │    P3优化收尾            │                         │                         │
    │    文档与版本治理        │                         │                         │
    │    数据模型增强          │                         │                         │
    │    安全与一致性          │                         │                         │
    │                         │                         │                         │
    │    U-43/U-44/U-46已解决  │                         │                         │
    │    U-45已知限制(低)      │                         │                         │
    │                         │                         │                         │
    ▼                         ▼                         ▼                         ▼
  ⚠️ 已移除                 骨架加载+降级完整         Phase标记补全(可选)        多项目+插件+分布式
  无降级机制                45/46问题修复(97.8%)      45/46问题修复(97.8%)      架构成熟+生态开放
```

### 9.2 关键演进指标

| 指标 | V_PREVIOUS_MAJOR → V_CURRENT | V_CURRENT → v8.1.0 | v8.1.0 → v9.0.0 |
|------|------------------------------|---------------------|-------------------|
| **Agent扩展** | 35→57 (+63%) | 不变 | 57→57+ |
| **MCP Tool** | 0→20 (+∞) | 不变 | 20→22+ (+10%) |
| **质量门禁** | 15→54 (+260%) | 不变 | 54→54+ |
| **SKILL.md精简** | 765→<200行 (-74%) | 不变 | 不变 |
| **初始Token** | ~50K→≤2K (-96%) | 不变 | 不变 |
| **降级可用性** | 0%→100%(20/20) ✅ | 100%→100% | 100%→100%+加密 |
| **已知问题修复率** | N/A | 97.8%→97.8% | 97.8%→100% |
| **数据存储统一** | 分散 | 统一SQLite(8表) | 统一SQLite(10+表) |
| **FALLBACK_MAP覆盖** | N/A | 20/20→20/20 | 20/20→20/20 |
| **评估配置有效性** | N/A | 全部有效→全部有效 | 全部有效→全部有效 |
| **Phase标记(Skill侧)** | 无 | 无→有(可选改进) | 有→有 |
| **健康检查可配置** | 否→是(5s~300s) ✅ | 是→是 | 是→是 |

### 9.3 破坏性变更摘要

| 版本跃迁 | 破坏性变更 | 迁移建议 |
|---------|-----------|---------|
| V_PREVIOUS_MAJOR → V_CURRENT | SKILL.md结构完全重写；新增MCP Server依赖；触发条件外部化；Agent从35扩展到57；命令从13扩展到31；v1已从仓库移除 | 需要安装xuansto-mcp-server；更新IDE Skill配置；迁移到xuansto-skill-v2目录；v1代码不再可用 |
| V_CURRENT → v8.1.0 | knowledge_search移除inject/precipitate action(已由knowledge_inject替代)；agent_status拆分为agent_status+agent_manage；错误响应deprecated code字段 | 更新调用knowledge_search的代码，使用knowledge_inject替代inject；更新agent变更类调用为agent_manage；更新错误处理代码移除code字段依赖 |
| v8.1.0 → v9.0.0 | API版本从3.0.0升级到4.0.0；新增plugin_manage/project_switch Tool；传输方式新增SSE可选；数据存储新增2+表 | 更新版本协商代码；适配新Tool；SSE传输需额外配置；运行数据迁移脚本 |

### 9.4 v9.0.0前瞻特性

| 特性 | 描述 | 优先级 |
|------|------|--------|
| **多项目并行** | 支持同时编排多个项目，独立会话+共享知识库 | 高 |
| **插件系统** | 自定义Tool/Agent/Hook/Gate注册，plugin_manage管理生命周期 | 高 |
| **SSE传输** | MCP协议支持SSE传输方式，适配远程部署场景 | 高 |
| **API v4.0.0** | API版本升级到4.0.0，最低兼容3.0.0 | 高 |
| **分布式编排** | 跨进程Agent协调，最终一致性状态管理 | 中 |
| **零信任安全** | Agent间通信零信任验证，敏感操作二次确认 | 中 |
| **自定义门禁** | 插件注册自定义质量门禁，扩展质量保障体系 | 低 |
| **跨项目知识** | 项目间知识共享与隔离，支持组织级知识沉淀 | 低 |
| **运行时协商** | 渐进式加载支持运行时能力协商，动态调整加载策略 | 低 |
