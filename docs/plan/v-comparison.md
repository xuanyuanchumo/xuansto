# Xuansto Skill + MCP Server 双维度版本对比文档

> 文档版本：3.0.0
> 生成日期：2026-05-22
> 基于 REFACTOR_PLAN.md / ARCHITECTURE.md / SKILL_REVIEW.md / MCP_REVIEW.md / SKILL.md(v1+v2) / pyproject.toml 源码事实编写
> 对比范围：
> - Skill层：v5.0.0 (v1前驱大版本) / v7.0.0 (v2当前) / v7.1.0 (v2下一小版本) / v8.0.0 (下一大版本)
> - MCP Server层：v3.0.0 (前驱) / v3.5.0 (当前) / v3.6.0 (下一小版本) / v4.0.0 (下一大版本)
> 术语规范：渐进式加载披露（Progressive Loading Disclosure），使用"披露"而非"特效"

---

## 1. 版本概览表

### 1.1 Skill版本概览

| 维度 | v5.0.0 (Skill v1) | v7.0.0 (Skill v2当前) | v7.1.0 (Skill v2下一小版本) | v8.0.0 (Skill下一大版本) |
|------|-------------------|----------------------|---------------------------|------------------------|
| 发布状态 | 已废弃(deprecated) | 当前版本 | 规划中 | 规划中 |
| 架构模式 | 文件系统驱动 | MCP工具驱动+渐进式加载披露(基础) | MCP+渐进式加载披露(增强) | MCP+渐进式加载披露+生产级 |
| Agent数量 | 57/13层 | 57/13层 | 57/13层 | 57/13层 |
| Command数量 | 27 | 27 | 27 | 27 |
| Workflow数量 | 15 | 15 | 15 | 15 |
| MCP Tool数量 | 0 | 13 | 13 | 16 |
| MCP Resource数量 | 0 | 7 | 8 | 11 |
| Quality Gate数量 | 54 | 54 | 54 | 54 |
| 脚本数量 | 49+ | 89+ | 89+ | 92+ |
| 参考文档数量 | 72+ | 6(本地)+100+(MCP) | 15+(本地)+100+(MCP) | 30+(本地)+100+(MCP) |
| 模板数量 | 19 | 19 | 19 | 19 |
| 渐进式加载披露 | ✗ | ✓(基础) | ✓(增强) | ✓(完整) |
| 降级链 | 脚本直接调用 | MCP→脚本→内嵌逻辑(三级) | MCP→脚本→内嵌+降级统计 | MCP→脚本→内嵌+状态追踪+配置化 |
| SKILL.md行数 | ~360行 | ~416行 | ~120行 | ~50行(元数据)+4个YAML |
| Token消耗(触发时) | ~8K | ~10K(全量)/~2K(骨架) | ~2K | ~2K |
| 测试覆盖率 | 0% | 0% | 20% | 80%+ |
| 持久化 | 无(纯文件) | 5个JSON文件 | 5个JSON文件 | SQLite+JSON降级 |

### 1.2 MCP Server版本概览

| 维度 | v3.0.0 (MCP前驱) | v3.5.0 (MCP当前) | v3.6.0 (MCP下一小版本) | v4.0.0 (MCP下一大版本) |
|------|------------------|-----------------|----------------------|---------------------|
| 发布状态 | 已废弃 | 当前版本 | 规划中 | 规划中 |
| Tool数量 | 8 | 13 | 13(增强) | 16 |
| Resource数量 | 0 | 7 | 8 | 11 |
| API版本 | 0.5.0 | 1.0.0 | 1.1.0 | 2.0.0 |
| 降级策略 | 无 | 脚本实际调用(run_script_fallback) | 脚本实际调用+降级统计 | 脚本调用+状态追踪+YAML配置化 |
| 渐进式加载披露 | ✗ | ✓(基础) | ✓(增强) | ✓(完整) |
| Hook系统 | 无(仅hooks.json结构定义) | 包装拦截(_with_hook_interception) | 包装拦截 | 独立引擎+插件式注册 |
| 配置热重载 | 无 | 线程轮询(5s) | 线程轮询(5s) | 事件驱动(watchdog) |
| 错误处理 | 英文消息 | 英文消息 | 英文消息 | 结构化错误码(XST-XXXX)+i18n |
| Python要求 | ≥3.8 | ≥3.10 | ≥3.10 | ≥3.10 |
| MCP协议版本 | 2024-11-05 | 2025-03-26 | 2025-03-26 | 2025-03-26 |
| CLI子命令数 | 4 | 9 | 9 | 12 |
| Pydantic校验 | 无 | 13个模型(extra="forbid") | 13个模型(extra="forbid") | 16个模型(extra="forbid") |
| 知识检索引擎 | 无 | ChromaDB+FTS5+关键词 | ChromaDB+FTS5+关键词 | 统一接口+可插拔引擎 |
| 持久化 | 无 | 5个JSON+threading.Lock | 5个JSON+threading.Lock | SQLite WAL+JSON降级 |
| 内嵌降级逻辑 | 无 | ~800行(分布在8个tool文件) | ~800行(分布在8个tool文件) | 独立模块(core/inline_fallbacks.py) |

---

## 2. Skill版本对比 (v5.0.0 / v7.0.0 / v7.1.0 / v8.0.0)

### 2.1 v5.0.0 功能矩阵（前驱大版本基线）

#### 2.1.1 完整功能列表

| 功能域 | 数量 | 详情 |
|--------|------|------|
| Agent定义 | 57个/13层 | 编排3 + 产品4 + 设计4 + 工程6 + 跨平台5 + 数据3 + 测试10 + 安全3 + DevOps4 + 质量7 + 文档2 + 知识3 + 监控3 |
| 命令 | 27个 | /sprint, /clarify, /plan, /spec, /design, /implement, /test, /review, /fix, /accept, /deploy, /build-desktop, /release-desktop, /refactor, /audit, /agent-status, /learn, /brainstorm, /execute-plan, /design-system, /simplify, /loop, /cancel-loop, /build, /init, /status, /rollback |
| 工作流 | 15个 | brainstorming, sdd-tdd-full/medium/fast, security-audit, bug-fix, desktop-build, flutter-desktop, cross-platform, ui-ux, webapp-testing, subagent-driven, acceptance, ai-pentest, performance-test |
| 质量门禁 | 54项 | Phase 0-8门禁 + 跨阶段门禁（TOKEN-BUDGET, SESSION-RECOVERY, ITERATION-BUDGET等） |
| 脚本 | 49+个 | Python/JS/PS1，覆盖知识服务(30)、安全扫描(3)、质量门禁(4)、代码简化(3)、会话管理(4)、规格检测(3)、桌面构建(4)、上下文压缩(3)、验证工具(4)、工作流工具(5) |
| 参考文档 | 72+个 | 编码规范(7)、安全框架(7)、设计指南(7)、协议(2)、集成(6)、桌面(5)、测试(2)、Agent(2)、验收(4)、数据库(1)、Git(2)、文档(2)、知识库(5)、其他(8)、脚本(49+)、新增(6) |
| 模板 | 19个 | PRD/ADR/RFC/RCA/用户故事/测试计划/设计系统/设计令牌/安全清单/无障碍清单/可用性测试/部署计划/用户手册/API契约/CI-CD/桌面构建/Flutter构建/自动更新/IPC契约 |
| 知识库 | 三层 | experience(经验沉淀) + general(通用知识) + workspace(工作区知识) |
| 命令路由表 | 27条 | 含MCP工具调用链和降级策略的完整映射 |
| Hook系统 | 6个核心Hook | PhaseEnter/PhaseExit/GatePass/GateFail/SessionStart/SessionStop |
| 模型路由 | 三级声明 | fast(搜索/简单编辑) / standard(多文件实现) / deep(架构设计/安全分析) |
| 并行化策略 | 声明 | Phase内独立子任务自动并行分发，Agent级+文件级并行 |
| 验证评估 | 声明 | 功能正确性+性能基准+安全合规+代码质量+用户体验 |
| MCP集成 | 声明 | MCP Tool优先→REST API降级→文件系统兜底三级调用链 |
| 协作模式 | 8种 | Auto/串行/并行/Review/Challenge/迭代/层级/Consult/Hivecoding |
| 多语言规范 | 5种 | Python/Go/Java/Rust/TypeScript |

#### 2.1.2 架构特点

| 特点 | 说明 |
|------|------|
| **文件系统驱动** | 所有数据（Agent定义、命令、工作流、脚本、参考文档、模板、知识库）以本地文件形式存储在Skill目录下，直接通过文件系统读取 |
| **脚本直接调用** | 降级和辅助功能通过直接执行scripts/目录下的Python/JS脚本实现，无需中间层 |
| **单文件编排** | SKILL.md承载全部编排逻辑（~360行）：触发条件+命令路由+Agent索引+核心约束+MCP工具映射+27命令详细步骤 |
| **全量加载** | Skill触发时加载全部资源（72+参考文档、57 Agent定义、27命令路由），Token消耗~8K |
| **知识库服务层** | 本地knowledge-server.py提供SQLite+ChromaDB双引擎知识检索，含REST API(7端点)和MCP Tool接口(5工具) |
| **数据完整性** | 完整的文件体系（~250+文件），包含agents/、commands/、workflows/、scripts/、templates/、references/、configs/、hooks/、knowledge/、memory/、examples/、evals/ |

#### 2.1.3 已知问题

| 编号 | 描述 | 严重级别 |
|------|------|----------|
| V5-01 | Hook系统仅有结构定义(hooks.json)，无实际Hook执行引擎 | 中 |
| V5-02 | 模型路由仅为文档描述(references/model-routing.md)，无实际路由代码 | 中 |
| V5-03 | 并行化策略仅为文档描述(references/parallelization-strategy.md)，无实际并行调度引擎 | 中 |
| V5-04 | 验证评估框架仅为文档描述(references/evaluation-framework.md)，无实际评估引擎 | 中 |
| V5-05 | 安全沙箱约束与现有脚本(coverage-check.py使用subprocess)存在冲突 | 中 |
| V5-06 | SKILL.md参考索引未覆盖全部参考文件 | 低 |
| V5-07 | 部分声明功能（Hook/模型路由/并行化/验证评估）仅有references/文档，无实际运行时代码 | 中 |
| V5-08 | 全量加载导致Token浪费（~8K触发+~84K全流程） | 高 |
| V5-09 | knowledge-server.py存在import yaml缺少try/except的问题（v1.9.1已修复） | 低 |
| V5-10 | 声明MCP集成但实际无MCP工具，与MCP Server的协作关系不清晰 | 高 |

#### 2.1.4 废弃原因

| 原因 | 说明 |
|------|------|
| **架构范式过时** | 文件系统驱动架构无法适应MCP协议标准化趋势，所有数据需通过MCP Tool/Resource统一暴露 |
| **Token效率低下** | 全量加载模式导致Token消耗过高（~8K触发），无法支持渐进式加载披露 |
| **降级链不完整** | 脚本直接调用缺乏统一降级框架，降级策略分散在各命令中，无内嵌逻辑兜底 |
| **数据镜像冗余** | v1与MCP Server data/存在~200+文件双份存储（agents/、scripts/、hooks/、templates/） |
| **MCP Server依赖声明虚假** | v1 SKILL.md声明MCP集成但实际无MCP工具调用，命令路由表中的MCP工具调用链仅为占位描述 |
| **维护成本高** | ~250+文件体系维护困难，Agent定义/命令/工作流分散在多个目录 |
| **缺乏状态管理** | 无会话持久化、无工作流状态追踪、无Agent实例管理 |

---

### 2.2 v7.0.0 功能矩阵（当前版本）

#### 2.2.1 完整功能列表

| 功能域 | 数量 | 详情 |
|--------|------|------|
| Agent定义 | 57个/13层 | 与v5.0.0相同的57个Agent，通过MCP Resource(xuansto://references/agent-registry)或agents/目录访问 |
| 命令 | 27个 | 与v5.0.0相同的27个命令，路由表简化为MCP工具映射 |
| 工作流 | 15个 | 与v5.0.0相同的15个工作流，通过MCP Resource(xuansto://references/workflow-phases)访问合并版 |
| 质量门禁 | 54项 | 通过MCP quality_gate_check工具统一检查，含36项INLINE_CHECKS内嵌实现 |
| MCP Tools | 13个 | skill_analyze, knowledge_search, quality_gate_check, spec_drift_detect, security_scan, code_simplify, session_manage, workflow_dispatch, agent_status, hook_manage, resource_load_status, context_compress, server_health |
| MCP Resources | 7个 | xuansto://config/skill, xuansto://references/quality-gates, xuansto://references/agent-registry, xuansto://references/workflow-phases, xuansto://templates/{name}, xuansto://sessions/latest, xuansto://loading/status |
| 脚本 | 89+个 | 由MCP Server data/scripts/提供，Skill层scripts/为镜像 |
| 参考文档 | 6个(本地) | mcp-tools.md + workflow-phases.md + quality-gates.md + agent-registry.md + knowledge-workflow-details.md + progressive-loading.md |
| 模板 | 19个 | 通过MCP Resource(xuansto://templates/{name})访问，含路径遍历防护 |
| 知识库 | 三层 | 通过MCP knowledge_search工具访问，支持retrieve/inject/precipitate，ChromaDB+FTS5+关键词三级降级 |
| 命令路由表 | 27条 | 简化为"命令→MCP Tool调用链"映射，含降级策略 |
| Hook系统 | 拦截框架 | server.py的_with_hook_interception包装所有Tool调用，3个profile(minimal/standard/strict)，7种内嵌Hook逻辑 |
| 模型路由 | 三级声明 | fast/standard/deep三级说明，无实际路由引擎 |
| 会话持久化 | MCP驱动 | SessionStart→session_manage(load), SessionStop→session_manage(save)，current.json实时追踪 |
| 降级链 | 三级实际调用 | MCP Tool优先→脚本降级(run_script_fallback)→内嵌逻辑降级，13个Tool均有FALLBACK_MAP映射 |
| 渐进式加载披露 | 基础实现 | 4级加载策略(skeleton→functional→enhanced→full)+LoadPhase枚举+available_functions+disclosure_note+priority(P0-P3)/batch_mode |
| 工作流调度 | MCP驱动 | workflow_dispatch支持start/status/abort/phase/recover/snapshots，9阶段SDD+TDD |
| Agent实例管理 | MCP驱动 | agent_status支持list/by_phase/detail/create/match/assign/release/instance_status/destroy/schedule，最大20实例 |
| 上下文压缩 | MCP驱动 | context_compress支持semantic/selective/lossless三种策略 |
| 性能追踪 | MCP驱动 | server_health记录调用次数/错误率/P50/P95/P99延迟，降级计数追踪 |

#### 2.2.2 架构特点

| 特点 | 说明 |
|------|------|
| **MCP工具驱动** | 所有核心功能通过13个MCP原子工具驱动，Skill层仅负责编排策略和命令路由 |
| **Skill-MCP分离** | Skill层是"大脑"（编排策略、Agent调度、命令路由），MCP Server是"手脚"（原子化工具执行、资源读取、降级兜底） |
| **Hook拦截框架** | 所有MCP工具调用自动包装pre/post Hook拦截，Pre-hook可block执行，Post-hook不阻塞 |
| **配置热重载** | config.py的_config_watcher线程轮询(5s间隔)实现配置热更新，Windows使用轮询，Unix使用SIGHUP |
| **CLI工具** | xuansto-cli支持health/invoke/gate/version/config/reload/workflow/session/agent子命令 |
| **Pydantic校验** | 13个Tool的输入参数通过Pydantic Model严格校验(extra="forbid")，server_health无Schema |
| **渐进式加载披露(基础)** | SKILL.md含4级加载指令+资源优先级(P0-P3)+加载状态查询机制，MCP Server提供loading/status Resource+available_functions+disclosure_note |
| **降级链实际调用** | degradation.py的FALLBACK_MAP 13个Tool均有run_script_fallback实际脚本调用，非占位响应 |
| **数据镜像** | Skill层agents/scripts/hooks/templates与MCP层data/目录完全镜像，~200+文件双份存储 |
| **持久化分散** | 5个JSON文件(workflow_states/agent_instances/gate_cache/tool_metrics/degradation_stats)分散存储，使用threading.Lock+atomic_write |

#### 2.2.3 相对v5.0.0的增量

| 增量项 | v5.0.0 | v7.0.0 | 说明 |
|--------|--------|--------|------|
| MCP Tools | 0 | 13 | 新增13个原子化MCP工具，统一功能入口 |
| MCP Resources | 0 | 7 | 新增7个只读Resource URI，统一数据访问 |
| Hook拦截框架 | 无(仅结构定义) | 有(包装拦截) | server.py的_with_hook_interception包装所有Tool调用，7种内嵌Hook逻辑 |
| 工具调用性能追踪 | 无 | 有 | record_tool_call记录每次调用的延迟和成功/失败状态 |
| 配置热重载 | 无 | 有 | start_config_watcher监听配置文件变更 |
| 工具动态注册 | 无 | 有 | 每个工具模块通过register(mcp)函数动态注册 |
| Pydantic输入校验 | 无 | 有 | 13个Pydantic Input模型定义(schemas.py) |
| CLI工具 | 无 | 有 | xuansto-cli命令行工具(9个子命令) |
| 降级链 | 分散声明 | 统一三级 | degradation.py统一管理13个Tool的降级策略，MCP→脚本→内嵌逻辑 |
| 内嵌降级逻辑 | 无 | ~800行 | 8个tool文件含_inline_*函数，提供MCP和脚本均不可用时的兜底 |
| 命令路由表 | 详细步骤 | 精简映射 | 从v1的详细步骤简化为MCP工具映射 |
| 渐进式加载披露 | 无 | 基础实现 | 4级加载+LoadPhase+available_functions+disclosure_note+priority/batch_mode |
| loading/status Resource | 无 | 有 | xuansto://loading/status返回实时加载状态+available_functions |
| 会话持久化 | 无 | MCP驱动 | session_manage支持save/load/list/detect/verify/track/restore |
| 工作流调度 | 无 | MCP驱动 | workflow_dispatch支持start/status/abort/phase/recover/snapshots |
| Agent实例管理 | 无 | MCP驱动 | agent_status支持create/match/assign/release/destroy |
| 上下文压缩 | 无 | MCP驱动 | context_compress支持semantic/selective/lossless |
| 门禁缓存 | 无 | 有 | quality_gate_check含SHA256文件哈希缓存+gate_cache.json持久化 |
| 工作流快照 | 无 | 有 | gzip压缩快照+TTL+数量双重清理策略 |
| 知识注入/沉淀 | 无 | 有 | knowledge_search支持inject(知识注入)和precipitate(经验沉淀) |

#### 2.2.4 已知问题

**来自REFACTOR_PLAN.md的问题统一清单**：

| 编号 | 描述 | 所属端 | 严重级别 | 状态 |
|------|------|--------|----------|------|
| A-01 | SKILL.md膨胀至~416行，Token消耗~10K | Skill | P1阻塞 | 规划v7.1.0 |
| A-02 | 数据镜像冗余(Skill层与MCP层~200+文件双份) | 数据 | P1阻塞 | 规划v8.0.0 |
| A-03 | 命令步骤重复(SKILL.md L213-L378与commands/*.md完全重复) | Skill | P1阻塞 | 规划v7.1.0 |
| D-01 | 并发写入无事务保证(5个JSON文件仅进程级锁) | 数据 | P2高 | 规划v8.0.0 |
| D-02 | 持久化文件分散无索引(O(n)过滤) | 数据 | P2高 | 规划v8.0.0 |
| D-05 | 降级策略双源定义(SKILL.md降级表+degradation.py FALLBACK_MAP) | Skill/MCP | P2高 | 规划v7.1.0 |
| M-07 | MCP Resource URI降级路径缺失(5/7个Resource无降级路径) | MCP/API | P2高 | 规划v7.1.0 |
| M-09 | Hook拦截与降级脚本映射不一致(3/16个Hook有降级脚本) | MCP | P2高 | 规划v8.0.0 |
| E-02 | API响应格式不统一(degradation_level位置不一致) | API | P2高 | 规划v8.0.0 |
| E-03 | 缺乏API版本协商机制 | API | P2高 | 规划v8.0.0 |
| S-07 | 门禁别名映射冗余 | Skill | P2高 | 规划v7.1.0 |
| S-10 | 工作流命名不完整(medium/fast缺乏详细步骤) | Skill | P2高 | 规划v7.1.0 |

**来自SKILL_REVIEW.md的补充问题**：

| 编号 | 描述 | 严重级别 | 状态 |
|------|------|----------|------|
| V7-01 | 渐进式加载缺少独立状态管理器，完全依赖LLM上下文记忆 | 高 | 规划v7.1.0 |
| V7-02 | 缺少优先级调度器，Token预算检查依赖LLM推理 | 高 | 规划v8.0.0 |
| V7-03 | 缺少占位符机制，不可用功能不会在输出中预留位置 | 中 | 规划v7.1.0 |
| V7-04 | 缺少加载进度UI呈现，loading_progress仅返回浮点数 | 中 | 规划v7.1.0 |
| V7-05 | 缺少缓存失效和TTL管理实现 | 中 | 规划v7.1.0 |
| V7-06 | phrases(47个)和keywords(83个)存在约30%语义重叠 | 低 | 规划v7.1.0 |

#### 2.2.5 迁移路径（v5→v7）

| 迁移步骤 | 操作 | 验证方法 |
|----------|------|----------|
| 1 | 安装xuansto-mcp-server: `pip install xuansto-mcp-server>=3.5.0` | `xuansto-cli health` 返回OK |
| 2 | 配置IDE的MCP连接(stdio) | MCP Server启动日志无错误 |
| 3 | 替换Skill目录: xuansto-skill → xuansto-skill-v2 | SKILL.md frontmatter version=7.0.0 |
| 4 | 验证MCP工具注册: `server_health()` | tools_count=13, resources_count=7 |
| 5 | 验证MCP Resource可访问: 逐个读取7个URI | 每个URI返回非空内容 |
| 6 | 验证降级链: 模拟MCP Server不可用 | 脚本降级实际执行(degradation_level="script"或"inline") |
| 7 | 迁移自定义配置: .skill-config.yaml → MCP Server data/ | 配置项在新位置可读取 |
| 8 | 迁移自定义Hook: hooks.json → MCP Server data/hooks/ | Hook定义在新位置可读取 |
| 9 | 标记v1为deprecated | v1 SKILL.md `deprecated: true`, `migrate_to: xuansto-skill-v2` |

**迁移注意事项**：

| 注意项 | v5.0.0 | v7.0.0 | 说明 |
|--------|--------|--------|------|
| 数据目录 | 本地agents/commands/workflows/ | MCP Server data/ | 数据由MCP Server统一提供 |
| 命令路由 | 详细步骤(3-4步/命令) | MCP工具映射(1-3步/命令) | 部分命令调用链简化 |
| 降级模式 | 脚本直接调用 | MCP→脚本→内嵌逻辑 | 降级链统一管理，实际脚本调用 |
| 参考文档 | 72+本地文件 | 6本地+100+MCP Server | 本地参考大幅减少 |
| Hook系统 | hooks.json结构定义 | _with_hook_interception拦截框架 | Hook可实际执行和阻断 |
| 渐进式加载披露 | 无 | 基础实现 | 4级加载+LoadPhase+available_functions |
| 会话持久化 | 无 | MCP驱动 | session_manage支持7种action |
| 工作流调度 | 无 | MCP驱动 | workflow_dispatch支持6种action |

---

### 2.3 v7.1.0 功能矩阵（后继相邻小版本）

#### 2.3.1 核心增量：SKILL.md精简 + 渐进式加载披露增强

v7.1.0聚焦于解决v7.0.0的P1阻塞级问题(A-01/A-03)和P2高优先级问题(D-05/M-07/S-07/S-10)，精简SKILL.md并增强渐进式加载披露。

| 增量项 | v7.0.0 | v7.1.0 | 说明 |
|--------|--------|--------|------|
| SKILL.md行数 | ~416行 | ~120行 | 提取命令详细步骤到commands/*.md、降级表引用degradation.py、Agent索引引用MCP Resource |
| Token消耗(触发时) | ~10K(全量)/~2K(骨架) | ~2K | 确认降低，commands/*.md按需加载 |
| 渐进式加载披露 | ✓(基础) | ✓(增强) | 新增DisclosureTransition过渡披露、LoadPhaseStateMachine状态机、Token预算追踪 |
| MCP Resource | 7 | 8 | 新增xuansto://stats/degradation |
| 参考文档(本地) | 6 | 15+ | 从v1迁移quality-gates.md、agent-registry.md、coding-standards.md等关键参考 |
| 命令路由 | 内嵌SKILL.md | 独立routing.yaml | commands/routing.yaml独立定义27命令的MCP工具调用链+降级策略 |
| DisclosureTransition | 无 | 有 | 阶段切换时的过渡披露(from_phase/to_phase/added_functions/removed_functions/disclosure_note) |
| LoadPhaseStateMachine | 无 | 有 | 严格状态转换规则，禁止非法转换(如skeleton→full跳跃) |
| Token预算追踪 | 无 | 有 | loading/status增加estimated_total_tokens和token_budget_remaining |
| MCP Resource降级路径 | 2/7有降级 | 7/7有降级 | 为5个Resource URI补充文件系统降级路径 |
| 门禁别名清理 | 有冗余别名 | 清理后 | quality-gates.md仅保留当前有效的54项门禁ID |
| 工作流定义补全 | medium/fast不完整 | 完整 | sdd-tdd-medium.md和sdd-tdd-fast.md补充完整Phase定义 |

#### 2.3.2 相对v7.0.0的变更

##### 2.3.2.1 SKILL.md瘦身重构（解决A-01/A-03）

| 变更项 | 说明 |
|--------|------|
| 删除命令详细步骤 | SKILL.md L213-L378命令详细步骤改为引用commands/{cmd}.md，减少~165行 |
| 创建commands/routing.yaml | 将SKILL.md命令路由表(L180-L211)提取为YAML格式 |
| 降级表引用degradation.py | SKILL.md降级模式功能范围表(L47-L65)替换为引用degradation.py |
| Agent索引引用MCP Resource | SKILL.md Agent索引表(L379-L397)替换为xuansto://references/agent-registry引用 |
| 渐进式加载定义简化 | SKILL.md加载阶段定义引用resource_load_status工具管理 |

##### 2.3.2.2 渐进式加载披露增强（解决M-07/V7-01/V7-03）

| 变更项 | 说明 |
|--------|------|
| LoadPhaseStateMachine实现 | 严格状态转换规则：skeleton→functional→enhanced→full正向推进，Token压力反向降级，禁止跳跃转换 |
| DisclosureTransition实现 | 每次Phase转换返回新旧功能对比(from_phase/to_phase/added_functions/removed_functions/disclosure_note) |
| Token预算追踪 | loading/status增加estimated_total_tokens和token_budget_remaining字段 |
| 加载错误上报 | loading_progress增加errors和estimated_remaining_ms字段 |
| MCP Resource降级路径 | 为7个Resource URI提供文件系统降级路径声明 |
| 骨架屏/占位符设计 | SKELETON阶段未加载功能以占位符形式呈现，用户可感知功能存在但尚未可用 |

##### 2.3.2.3 降级策略统一（解决D-05）

| 变更项 | 说明 |
|--------|------|
| 降级策略单一来源 | 统一到degradation.py + 配置文件，SKILL.md仅引用降级模式说明 |
| 降级脚本映射配置化 | 从config.py硬编码迁移到.xuansto-config.yaml |

##### 2.3.2.4 其他修复

| 变更项 | 说明 |
|--------|------|
| 门禁别名清理 | quality-gates.md清理已废弃的门禁ID别名 |
| 工作流定义补全 | sdd-tdd-medium.md和sdd-tdd-fast.md补充完整Phase定义 |
| 参考文档补齐 | 从v1迁移15+核心参考文档到v2 references/目录 |

#### 2.3.3 解决的v7.0.0问题

| 问题编号 | 描述 | 解决方式 |
|----------|------|----------|
| A-01 | SKILL.md膨胀至~416行 | 瘦身至~120行，提取命令步骤/降级表/Agent索引到独立文件 |
| A-03 | 命令步骤重复 | 删除SKILL.md内嵌步骤，commands/*.md成为唯一权威源 |
| D-05 | 降级策略双源定义 | 统一到degradation.py + 配置文件 |
| M-07 | MCP Resource URI降级路径缺失 | 为7个Resource补充文件系统降级路径 |
| S-07 | 门禁别名映射冗余 | 清理已废弃别名 |
| S-10 | 工作流命名不完整 | 补充medium/fast工作流详细定义 |
| V7-01 | 渐进式加载缺少状态管理器 | LoadPhaseStateMachine实现 |
| V7-03 | 缺少占位符机制 | 骨架屏/占位符设计 |

#### 2.3.4 迁移路径（v7→v7.1）

| 迁移步骤 | 操作 | 验证方法 |
|----------|------|----------|
| 1 | 升级MCP Server到v3.6.0(推荐) | `xuansto-cli health` 返回version=3.6.0 |
| 2 | 替换SKILL.md为Phase-aware摘要版 | SKILL.md行数≤150行，Token消耗≤3K |
| 3 | 创建commands/routing.yaml | YAML解析器可正确解析27命令路由 |
| 4 | 更新references/目录(6→15+文件) | 关键参考文件可访问 |
| 5 | 验证渐进式加载披露增强 | 确认DisclosureTransition过渡披露返回 |
| 6 | 验证MCP Resource降级路径 | 模拟MCP Server不可用，确认Resource文件系统降级路径可用 |
| 7 | 回归测试27命令 | 所有命令触发和路由正确 |

**兼容性说明**：v7.1.0 Skill + MCP Server v3.5.0可运行，渐进式加载披露保持基础模式（无DisclosureTransition、无stats/degradation Resource）。推荐搭配MCP Server v3.6.0。

---

### 2.4 v8.0.0 功能矩阵（后继相邻大版本）

#### 2.4.1 核心增量：生产级发布

v8.0.0在v7.1.0渐进式加载披露增强基础上，实现完整的生产级发布：SKILL.md拆分为多配置文件、数据镜像消除、SQLite持久化、完整测试体系、MCP Server v4.0.0升级。

| 增量项 | v7.1.0 | v8.0.0 | 说明 |
|--------|--------|--------|------|
| SKILL.md结构 | 单文件(~120行) | 多文件(~50行元数据) | 拆分为SKILL.md + triggers.yaml + routes.yaml + registry.yaml + constraints.yaml |
| MCP Tools | 13 | 16 | 新增decision_log, token_budget, project_init |
| MCP Resources | 8 | 11 | 新增xuansto://config/gate-scripts, xuansto://config/hook-scripts, xuansto://config/phase-gates |
| 渐进式加载披露 | ✓(增强) | ✓(完整) | 完整四级加载披露+Token预算驱动动态加载+MCP Notification进度推送 |
| 降级链 | 脚本实际调用+降级统计 | 脚本调用+状态追踪+配置化 | FALLBACK_MAP从degradation.py迁移到YAML配置，内嵌逻辑提取到core/inline_fallbacks.py |
| 参考文档(本地) | 15+ | 30+ | 全面迁移v1参考文档+新增MCP化文档 |
| 脚本数量 | 89+ | 92+ | 新增3个脚本(token-budget-guard增强、config-validator、workflow-snapshot-manager) |
| 测试覆盖率 | 20% | 80%+ | 完整测试体系：单元/集成/端到端/回归 |
| 数据镜像 | 双份存储 | 统一管理 | 消除data/与.trae/skills/之间的数据镜像，MCP Server通过SKILL_ROOT引用 |
| 持久化 | 5个JSON文件 | SQLite WAL+JSON降级 | xuansto_state.db(9张表)+启动自动迁移+JSON降级读取 |
| Hook系统 | 包装在server.py | 独立引擎 | 独立Hook引擎，16/16 Hook有降级路径，支持插件式注册 |
| 知识检索 | ChromaDB+FTS5+关键词 | 统一接口+可插拔引擎 | SearchEngine抽象基类，支持引擎切换 |
| 配置热重载 | 线程轮询(5s) | 事件驱动 | watchdog事件驱动，即时响应，watchdog不可用时降级为轮询 |
| 错误处理 | 英文消息 | 结构化错误码+i18n | XST-XXXX格式错误码+中文/英文消息 |
| API版本 | 1.1.0 | 2.0.0 | SemVer MAJOR升级，含BREAKING变更 |
| API响应格式 | 不统一 | 统一 | 所有Tool返回{error, api_version, data, degradation_level}标准结构 |
| MCP Server版本 | v3.6.0 | v4.0.0 | 大版本升级，API不兼容 |

#### 2.4.2 相对v7.x的变更

##### 2.4.2.1 SKILL.md拆分为多配置文件

| 文件 | 职责 | 说明 |
|------|------|------|
| SKILL.md | 元数据+核心约束 | 仅保留frontmatter和核心约束引用（~50行） |
| triggers.yaml | 触发条件 | phrases/keywords/commands/not_for四类触发定义 |
| routes.yaml | 命令路由 | 27命令→MCP Tool调用链映射 |
| registry.yaml | Agent注册表 | 57 Agent的13层分类索引 |
| constraints.yaml | 核心约束 | Spec>Test>Code、Karpathy准则、3-Strike Protocol等 |

##### 2.4.2.2 数据镜像消除

| 变更项 | 说明 |
|--------|------|
| 统一数据管理 | Agent定义、知识库、脚本统一由Skill层管理 |
| SKILL_ROOT引用 | MCP Server通过SKILL_ROOT环境变量动态定位资源 |
| data/目录降级 | MCP Server的data/仅作为无Skill时的默认数据源 |
| 消除~200+文件双份存储 | 从双份镜像变为单份+引用 |

##### 2.4.2.3 SQLite持久化层重构

| 变更项 | 说明 |
|--------|------|
| xuansto_state.db | SQLite WAL模式状态库，9张表(workflow_instances/agent_instances/gate_cache/tool_metrics/degradation_stats/session_states/resource_states/patterns/workflow_snapshots) |
| core/persistence.py | 统一持久化层，SQLite连接池+事务上下文管理器 |
| 启动自动迁移 | 检测JSON文件→导入SQLite→备份为.json.bak→删除原文件 |
| JSON降级读取 | SQLite不可用时自动降级到JSON文件读取 |

##### 2.4.2.4 完整渐进式加载披露

| 加载层次 | 名称 | 加载内容 | Token预估 |
|----------|------|----------|-----------|
| Level 0 | 骨架(Skeleton) | 核心约束+命令概要+Agent索引+MCP依赖声明+降级入口 | ~2K |
| Level 1 | 功能(Functional) | 命令详细步骤+当前Phase工作流+MCP工具参数+Hook配置 | ~3K |
| Level 2 | 增强(Enhanced) | 参考文档+模板+知识库索引+Agent详细定义(按需) | ~5K |
| Level 3 | 完整(Full) | 全部资源+脚本集+披露资源+评估配置 | ~10K |

**Token预算驱动动态加载**：

| Token使用率 | 动作 |
|-------------|------|
| >60% | 释放P3资源(示例文档、评估配置) |
| >80% | context_compress(strategy=semantic)压缩+释放P2资源(参考文档、模板、知识库) |
| >95% | 仅保留P0(核心约束+命令概要+Agent索引)+当前命令 |

##### 2.4.2.5 API响应格式统一

| 变更项 | v7.x | v8.0.0 |
|--------|------|--------|
| 成功响应 | 格式不统一 | `{error: false, api_version: "2.0.0", data: {...}, degradation_level?: string}` |
| 错误响应 | 英文消息 | `{error: true, code: "XST-XXXX", message: str, message_i18n: {zh: str, en: str}, details: {...}}` |
| degradation_level位置 | 有时在data内，有时在顶层 | 始终在响应顶层 |
| quality_gate_check | `{gates_checked, gates_passed, results}` | `{checks, summary: {total, passed, failed, skipped, blocked}, cache_info}` |

#### 2.4.3 BREAKING变更

| 变更项 | v7.x行为 | v8.0.0行为 | 影响范围 | 迁移建议 |
|--------|----------|-----------|----------|----------|
| SKILL.md结构 | 单文件包含全部编排逻辑 | 拆分为5个文件(SKILL.md + 4个YAML) | 所有依赖SKILL.md的工具和脚本 | 更新SKILL.md解析逻辑，支持多文件引用 |
| MCP Server API版本 | 1.x | 2.0.0 | 所有MCP Tool调用 | 检查API版本兼容性，更新响应格式处理 |
| MCP Server最低版本 | v3.5.0 | v4.0.0 | MCP Server依赖 | 升级MCP Server到v4.0.0 |
| API响应格式 | 不统一 | 统一标准结构 | 所有Tool响应解析 | 更新响应解析逻辑，适配{error, api_version, data, degradation_level} |
| quality_gate_check响应 | {gates_checked, gates_passed, results} | {checks, summary, cache_info} | 门禁检查结果处理 | 更新字段名映射 |
| 降级策略格式 | 硬编码FALLBACK_MAP | YAML配置文件 | degradation.py调用 | 迁移自定义降级策略到YAML配置 |
| 错误响应格式 | 英文消息 | 结构化错误码+国际化 | 错误处理逻辑 | 更新错误解析逻辑，支持error_code映射 |
| data/目录定位 | 内嵌data/ | SKILL_ROOT环境变量引用 | MCP Server部署 | 设置SKILL_ROOT环境变量指向Skill目录 |
| 持久化 | 5个JSON文件 | SQLite+JSON降级 | 持久化读写 | 启动时自动迁移，无需手动操作 |

#### 2.4.4 迁移路径（v7.x→v8.0）

| 迁移步骤 | 操作 | 验证方法 |
|----------|------|----------|
| 1 | 升级MCP Server到v4.0.0 | `xuansto-cli health` 返回version=4.0.0 |
| 2 | 设置SKILL_ROOT环境变量 | MCP Server可读取Skill目录资源 |
| 3 | 替换SKILL.md为多文件体系 | SKILL.md + triggers.yaml + routes.yaml + registry.yaml + constraints.yaml |
| 4 | 迁移降级策略到YAML配置 | degradation.yaml可被MCP Server读取 |
| 5 | 更新错误处理逻辑 | 结构化错误码可被正确解析 |
| 6 | 验证SQLite自动迁移 | 启动时JSON→SQLite迁移成功，.json.bak备份存在 |
| 7 | 运行完整测试套件 | 覆盖率≥80% |
| 8 | 验证四级渐进式加载披露 | Level 0→1→2→3加载正确 |
| 9 | 验证Token预算驱动 | Token>80%自动压缩，>95%降级到Level 0 |
| 10 | 回归测试27命令 | 所有命令在新架构下行为一致 |
| 11 | 性能基线验证 | Token消耗≤2K(触发)，≤5K(单命令) |

**不兼容警告**：v8.0.0 Skill + MCP Server v3.5.0/v3.6.0 **不兼容**，必须升级MCP Server到v4.0.0。

---

## 3. MCP Server版本对比 (v3.0.0 / v3.5.0 / v3.6.0 / v4.0.0)

### 3.1 v3.0.0 功能矩阵（前驱大版本基线）

#### 3.1.1 完整功能列表

| 功能域 | 数量 | 详情 |
|--------|------|------|
| MCP Tools | 8个 | skill_analyze, knowledge_search, quality_gate_check, session_manage, workflow_dispatch, agent_status, hook_manage, server_health |
| MCP Resources | 0个 | 无Resource暴露，所有数据通过Tool返回 |
| API版本 | 0.5.0 | 初始API，无版本协商机制 |
| CLI子命令 | 4个 | health, invoke, gate, version |
| 脚本 | 30+个 | 基础脚本集，覆盖知识服务、安全扫描、质量门禁 |
| Pydantic校验 | 无 | 参数校验依赖手动检查 |
| 降级策略 | 无 | MCP不可用时直接报错，无降级链 |
| Hook系统 | 无 | hooks.json仅结构定义，无执行引擎 |
| 配置热重载 | 无 | 配置变更需重启MCP Server |
| MCP协议版本 | 2024-11-05 | 早期协议版本 |
| 知识检索 | 基础 | SQLite FTS5 + 关键词匹配，无ChromaDB |

#### 3.1.2 架构特点

| 特点 | 说明 |
|------|------|
| **最小工具集** | 仅8个核心MCP Tool，覆盖分析、搜索、门禁、会话、工作流、Agent状态、Hook管理、健康检查 |
| **无Resource层** | 所有数据通过Tool响应返回，无MCP Resource URI暴露 |
| **基础CLI** | 仅4个子命令，功能有限 |
| **无降级机制** | MCP Server不可用时直接失败，无fallback策略 |
| **手动参数校验** | 无Pydantic模型，参数校验依赖if/else逻辑 |
| **MCP协议早期版本** | 使用2024-11-05协议版本，功能受限 |

#### 3.1.3 已知问题

| 编号 | 描述 | 严重级别 |
|------|------|----------|
| M3-01 | 无降级机制：MCP Server不可用时所有功能失效 | 高 |
| M3-02 | 无Resource层：数据只能通过Tool返回，无法订阅和缓存 | 中 |
| M3-03 | API v0.5.0无版本协商：客户端无法判断兼容性 | 中 |
| M3-04 | 无Pydantic校验：参数错误在运行时才暴露 | 中 |
| M3-05 | CLI功能不足：仅4个子命令，无法执行工作流或管理会话 | 低 |
| M3-06 | Hook系统仅有结构定义，无执行引擎 | 中 |
| M3-07 | 配置变更需重启，无法热更新 | 低 |
| M3-08 | 缺少安全扫描、代码简化、规格漂移检测等关键工具 | 高 |

#### 3.1.4 废弃原因

| 原因 | 说明 |
|------|------|
| **工具集不足** | 8个Tool无法覆盖完整开发流程，缺少安全扫描、代码简化、规格漂移检测、上下文压缩、资源加载状态等关键工具 |
| **无Resource层** | 不符合MCP协议最佳实践，数据访问效率低，无法利用Resource的订阅和缓存机制 |
| **API版本过时** | v0.5.0无版本协商，与Skill层兼容性无法保证 |
| **降级机制缺失** | 生产环境不可接受单点故障，MCP不可用时所有功能失效 |
| **MCP协议版本过旧** | 2024-11-05版本缺少notifications等关键特性 |

---

### 3.2 v3.5.0 功能矩阵（当前版本）

#### 3.2.1 完整功能列表

| 功能域 | 数量 | 详情 |
|--------|------|------|
| MCP Tools | 13个 | skill_analyze, knowledge_search, quality_gate_check, spec_drift_detect, security_scan, code_simplify, session_manage, workflow_dispatch, agent_status, hook_manage, resource_load_status, context_compress, server_health |
| MCP Resources | 7个 | xuansto://config/skill, xuansto://references/quality-gates, xuansto://references/agent-registry, xuansto://references/workflow-phases, xuansto://templates/{name}, xuansto://sessions/latest, xuansto://loading/status |
| API版本 | 1.0.0 | 正式API版本，含api_version字段 |
| CLI子命令 | 9个 | health, invoke, gate, version, config, reload, workflow, session, agent |
| 脚本 | 89+个 | 完整脚本集，覆盖知识服务(30+)、安全扫描(3)、质量门禁(4)、代码简化(3)、会话管理(4)、规格检测(3)、桌面构建(4)、上下文压缩(3)、验证工具(4)、工作流工具(5) |
| Pydantic校验 | 13个模型 | 13个Tool的Input模型，extra="forbid"严格校验(server_health无Schema) |
| 降级策略 | 脚本实际调用 | degradation.py统一管理13个Tool的降级策略，FALLBACK_MAP 13个Tool均有run_script_fallback实际脚本调用+内嵌逻辑兜底 |
| Hook系统 | 包装拦截 | server.py的_with_hook_interception包装所有Tool调用，3个profile(minimal=2/standard=10/strict=16)，7种内嵌Hook逻辑 |
| 配置热重载 | 线程轮询 | config.py的_config_watcher线程轮询(5s间隔)，Windows轮询/Unix SIGHUP |
| MCP协议版本 | 2025-03-26 | 最新协议版本 |
| 工具动态注册 | 有 | 每个工具模块通过register(mcp)函数动态注册 |
| 性能追踪 | 有 | record_tool_call记录每次调用的延迟和成功/失败状态，P50/P95/P99延迟 |
| 渐进式加载披露 | 基础实现 | xuansto://loading/status Resource + available_functions + disclosure_note + priority(P0-P3)/batch_mode参数 + LoadPhase枚举 |
| 知识检索 | 三层降级 | ChromaDB语义搜索 → SQLite FTS5 BM25 → 关键词TF-IDF匹配 |
| 门禁检查 | 54项 | 36项INLINE_CHECKS内嵌实现 + 脚本检查 + SHA256缓存 |
| 工作流调度 | 9阶段 | start/status/abort/phase/recover/snapshots，gzip快照+TTL清理 |
| Agent实例管理 | 10种action | list/by_phase/detail/create/match/assign/release/instance_status/destroy/schedule，最大20实例 |
| 会话管理 | 7种action | save/load/list/detect/verify/track/restore，current.json实时追踪 |
| 上下文压缩 | 3种策略 | semantic(语义保留)/selective(选择性采样)/lossless(无损截断) |
| 持久化 | 5个JSON | workflow_states/agent_instances/gate_cache/tool_metrics/degradation_stats，threading.Lock+atomic_write |

#### 3.2.2 架构特点

| 特点 | 说明 |
|------|------|
| **13个原子化MCP Tool** | 覆盖分析、搜索、门禁、规格漂移、安全扫描、代码简化、会话、工作流、Agent状态、Hook管理、资源加载状态、上下文压缩、健康检查 |
| **7个只读Resource URI** | 配置、门禁、Agent注册表、工作流、模板、会话、加载状态的统一只读访问 |
| **API v1.0.0** | 正式版本化API，含api_version字段 |
| **Hook拦截框架** | _with_hook_interception装饰器包装所有Tool调用，Pre-hook可block，Post-hook不阻塞 |
| **Pydantic严格校验** | 13个Input模型定义(schemas.py)，extra="forbid"防止未知参数 |
| **配置热重载** | _config_watcher线程轮询(5s)监听配置文件变更 |
| **工具动态注册** | 每个工具模块独立register(mcp)函数，支持按需加载 |
| **统一降级框架** | degradation.py统一管理13个Tool的降级策略，FALLBACK_MAP 13个Tool均有实际脚本调用+内嵌逻辑 |
| **渐进式加载披露(基础)** | xuansto://loading/status Resource返回实时加载状态+available_functions+disclosure_note，resource_load_status支持priority/batch_mode参数 |
| **知识检索三层降级** | ChromaDB语义搜索 → SQLite FTS5 BM25 → 关键词TF-IDF，自动降级计数追踪 |
| **门禁缓存** | SHA256文件哈希校验+gate_cache.json持久化+force_refresh参数 |
| **工作流快照** | gzip压缩+TTL(30天)+数量限制(20/工作流)+自动清理 |

#### 3.2.3 相对v3.0.0的增量

| 增量项 | v3.0.0 | v3.5.0 | 说明 |
|--------|--------|--------|------|
| MCP Tools | 8 | 13 | 新增spec_drift_detect, security_scan, code_simplify, resource_load_status, context_compress |
| MCP Resources | 0 | 7 | 新增7个只读Resource URI，统一数据访问 |
| API版本 | 0.5.0 | 1.0.0 | 正式版本化API，含api_version字段 |
| CLI子命令 | 4 | 9 | 新增config, reload, workflow, session, agent |
| Pydantic校验 | 无 | 13个模型 | 严格参数校验，extra="forbid" |
| 降级策略 | 无 | 脚本实际调用+内嵌逻辑 | degradation.py统一降级框架，13个Tool均有FALLBACK_MAP |
| Hook拦截 | 无 | 包装拦截 | _with_hook_interception装饰器，7种内嵌Hook |
| 配置热重载 | 无 | 线程轮询 | _config_watcher(5s间隔) |
| 工具动态注册 | 无 | 有 | register(mcp)函数模式 |
| 性能追踪 | 无 | 有 | record_tool_call记录延迟和成功率 |
| MCP协议版本 | 2024-11-05 | 2025-03-26 | 协议升级 |
| 渐进式加载披露 | 无 | 基础实现 | loading/status Resource + available_functions + disclosure_note + priority/batch_mode |
| 知识检索 | FTS5+关键词 | ChromaDB+FTS5+关键词 | 三层降级检索引擎 |
| 门禁缓存 | 无 | SHA256哈希缓存 | gate_cache.json持久化 |
| 工作流快照 | 无 | gzip压缩快照 | TTL+数量双重清理 |
| Agent实例管理 | 基础查询 | 10种action | create/match/assign/release/destroy等 |
| 会话管理 | 基础 | 7种action | save/load/list/detect/verify/track/restore |
| 上下文压缩 | 无 | 3种策略 | semantic/selective/lossless |
| 持久化 | 无 | 5个JSON文件 | threading.Lock+atomic_write |

#### 3.2.4 已知问题

**来自REFACTOR_PLAN.md的问题统一清单（MCP端）**：

| 编号 | 描述 | 所属端 | 严重级别 | 状态 |
|------|------|--------|----------|------|
| D-01 | 并发写入无事务保证(5个JSON文件仅进程级锁，多进程场景数据可能丢失) | 数据 | P2高 | 规划v4.0.0 |
| D-02 | 持久化文件分散无索引(5个JSON全量加载O(n)过滤) | 数据 | P2高 | 规划v4.0.0 |
| D-03 | resource_state.json双格式兼容(旧格式纯列表/新格式带版本号对象) | 数据 | P3中 | 规划v3.6.0 |
| D-04 | 缓存失效检测粒度粗(文件SHA256哈希任何变更导致整个缓存失效) | 数据 | P3中 | 规划v4.0.0 |
| M-02 | 内嵌逻辑代码分散(~800行_inline_*函数分布在8个tool文件，循环依赖风险) | MCP | P3中 | 规划v4.0.0 |
| M-05 | 配置热重载平台差异(Windows轮询5s延迟/Unix SIGHUP即时) | MCP | P3中 | 规划v4.0.0 |
| M-06 | server_health无参数校验Schema(唯一无Pydantic Schema的Tool) | MCP | P3中 | 规划v8.0.0 |
| M-07 | MCP Resource URI降级路径缺失(5/7个Resource无降级路径) | MCP/API | P2高 | 规划v3.6.0 |
| M-08 | 降级脚本路径不一致(SKILL.md与degradation.py描述不一致) | MCP/Skill | P3中 | 规划v3.6.0 |
| M-09 | Hook拦截与降级脚本映射不一致(3/16个Hook有降级脚本，其余13个返回空列表) | MCP | P2高 | 规划v4.0.0 |
| E-02 | API响应格式不统一(degradation_level位置不一致，quality_gate_check响应结构不一致) | API | P2高 | 规划v4.0.0 |
| E-03 | 缺乏API版本协商机制(MCP_API_VERSION仅作为响应字段返回) | API | P2高 | 规划v4.0.0 |
| E-04 | 缺乏重试机制(降级即视为最终策略，可恢复错误应支持重试) | API | P3低 | 规划v4.0.0 |
| I-01 | stdio传输限制远程调用(不支持HTTP/SSE) | 架构 | P3低 | 远期 |
| I-02 | 文件系统依赖不支持分布式(知识库/会话/工作流均依赖本地文件系统) | 架构 | P3低 | 远期 |

---

### 3.3 v3.6.0 功能矩阵（后继相邻小版本）

#### 3.3.1 核心增量：渐进式加载披露增强 + 降级路径补全

v3.6.0聚焦于增强MCP Server的渐进式加载披露能力和降级路径补全，配合Skill v7.1.0实现DisclosureTransition过渡披露、Resource降级路径和格式统一。

| 增量项 | v3.5.0 | v3.6.0 | 说明 |
|--------|--------|--------|------|
| MCP Tools | 13 | 13(增强) | resource_load_status增强DisclosureTransition+LoadPhaseStateMachine+Token预算追踪 |
| MCP Resources | 7 | 8 | 新增xuansto://stats/degradation |
| API版本 | 1.0.0 | 1.1.0 | 向后兼容扩展 |
| DisclosureTransition | 无 | 有 | 阶段切换时的过渡披露(from_phase/to_phase/added_functions/removed_functions/disclosure_note) |
| LoadPhaseStateMachine | 无 | 有 | 严格状态转换规则，禁止非法转换 |
| Token预算追踪 | 无 | 有 | loading/status增加estimated_total_tokens和token_budget_remaining |
| 加载错误上报 | 无 | 有 | loading_progress增加errors和estimated_remaining_ms |
| resource_state.json格式 | 双格式 | 统一字典格式 | 写入与读取格式统一，含version/loaded_resources/progressive_state |
| ProgressiveLoadState持久化 | 无 | 有 | 持久化到.xuansto/progressive_load_state.json |
| MCP Resource降级路径 | 2/7有降级 | 7/7有降级 | 为5个Resource URI提供文件系统降级路径 |
| 降级统计Resource | 无 | 有 | xuansto://stats/degradation返回降级次数/降级率/最近降级时间 |
| 降级脚本路径 | 不一致 | 统一 | 修复SKILL.md与degradation.py路径不一致问题 |

#### 3.3.2 相对v3.5.0的变更

##### 3.3.2.1 渐进式加载披露增强

| 变更项 | 说明 |
|--------|------|
| LoadPhaseStateMachine | 严格状态转换：skeleton→functional→enhanced→full正向推进，Token压力(>80%/>95%/>95%+idle)反向降级，禁止跳跃转换 |
| DisclosureTransition | 每次Phase转换返回from_phase/to_phase/trigger/action/available_functions/added_functions/removed_functions/disclosure_note/estimated_token_delta |
| Token预算追踪 | loading/status增加estimated_total_tokens和token_budget_remaining字段 |
| 加载错误上报 | loading_progress增加errors和estimated_remaining_ms字段 |
| MCP Notification进度推送(batch_mode) | batch_mode下注册progressToken，每资源加载完成推送notifications/progress |

##### 3.3.2.2 Resource降级路径补全

| Resource URI | v3.5.0降级路径 | v3.6.0降级路径 |
|-------------|---------------|---------------|
| xuansto://config/skill | ✓ 直接读文件 | ✓ 直接读文件 |
| xuansto://references/quality-gates | ✗ 无 | ✓ references/quality-gates.md |
| xuansto://references/agent-registry | ✗ 无 | ✓ references/agent-registry.md |
| xuansto://references/workflow-phases | ✗ 无 | ✓ references/workflow-phases.md |
| xuansto://templates/{name} | ✗ 无 | ✓ templates/{name}.md |
| xuansto://sessions/latest | ✗ 无 | ✓ sessions/session-*.md |
| xuansto://loading/status | ✓ 内联读取 | ✓ resource_state.json |

##### 3.3.2.3 降级统计与格式统一

| 变更项 | 说明 |
|--------|------|
| xuansto://stats/degradation | 返回降级统计(降级次数/各Tool降级率/最近降级时间) |
| resource_state.json格式统一 | 统一写入为字典格式(含version/loaded_resources/progressive_state)，读取兼容旧格式 |
| 降级脚本路径统一 | 修复SKILL.md与degradation.py路径不一致问题 |

##### 3.3.2.4 API v1.1.0扩展

| 变更项 | 说明 |
|--------|------|
| api_version字段 | 所有Tool响应添加api_version: "1.1.0" |
| 向后兼容 | v1.1.0完全向后兼容v1.0.0，新增字段为可选 |
| 新增Resource注册 | stats/degradation通过register_resources注册 |

#### 3.3.3 解决的v3.5.0问题

| 问题编号 | 描述 | 解决方式 |
|----------|------|----------|
| D-03 | resource_state.json双格式 | 统一写入为字典格式，读取兼容旧格式 |
| M-07 | MCP Resource URI降级路径缺失 | 为5个Resource补充文件系统降级路径 |
| M-08 | 降级脚本路径不一致 | 统一SKILL.md与degradation.py路径描述 |

#### 3.3.4 迁移路径（v3.5.0→v3.6.0）

| 迁移步骤 | 操作 | 验证方法 |
|----------|------|----------|
| 1 | 升级MCP Server: `pip install xuansto-mcp-server>=3.6.0` | `xuansto-cli health` 返回version=3.6.0 |
| 2 | 验证新增Resource | 读取xuansto://stats/degradation返回降级统计 |
| 3 | 验证DisclosureTransition | 触发Phase切换，确认过渡披露信息返回 |
| 4 | 验证resource_state.json格式统一 | 确认新格式写入正确，旧格式可兼容读取 |
| 5 | 验证Resource降级路径 | 模拟MCP不可用，确认7个Resource文件系统降级路径可用 |
| 6 | 回归测试13个Tool | 所有Tool原有功能不受影响 |

**兼容性说明**：v3.6.0完全向后兼容v3.5.0，API v1.1.0兼容v1.0.0客户端。Skill v7.0.0可无缝升级MCP Server到v3.6.0。

---

### 3.4 v4.0.0 功能矩阵（后继相邻大版本）

#### 3.4.1 核心增量：生产级MCP Server

v4.0.0在v3.6.0渐进式加载披露增强基础上，实现完整的生产级MCP Server：SQLite持久化、独立Hook引擎、可插拔搜索引擎、事件驱动配置、结构化错误码、SKILL_ROOT环境变量支持、3个新Tool、4个新Resource。

| 增量项 | v3.6.0 | v4.0.0 | 说明 |
|--------|--------|--------|------|
| MCP Tools | 13 | 16 | 新增decision_log, token_budget, project_init |
| MCP Resources | 8 | 11 | 新增xuansto://config/gate-scripts, xuansto://config/hook-scripts, xuansto://config/phase-gates |
| API版本 | 1.1.0 | 2.0.0 | **BREAKING** - SemVer MAJOR升级 |
| 降级策略 | 硬编码FALLBACK_MAP | YAML配置化 | FALLBACK_MAP迁移到YAML配置，支持动态注册 |
| 内嵌降级逻辑 | ~800行分布在8个tool文件 | 独立模块 | 提取到core/inline_fallbacks.py，消除循环依赖 |
| 渐进式加载披露 | ✓(增强) | ✓(完整) | 完整四级加载披露+Token预算驱动动态加载+MCP Notification |
| Hook系统 | 包装拦截 | 独立引擎 | 独立Hook引擎，16/16 Hook有降级路径，支持插件式注册 |
| 知识检索 | ChromaDB+FTS5+关键词 | 统一接口+可插拔引擎 | SearchEngine抽象基类，支持引擎切换 |
| 配置热重载 | 线程轮询(5s) | 事件驱动 | watchdog事件驱动，即时响应，降级为轮询 |
| 错误处理 | 英文消息 | 结构化错误码+i18n | XST-XXXX格式错误码+中文/英文消息 |
| 持久化 | 5个JSON文件 | SQLite WAL+JSON降级 | xuansto_state.db(9张表)+启动自动迁移 |
| SKILL_ROOT | 无 | 有 | 环境变量动态定位Skill资源，消除数据镜像 |
| CLI子命令 | 9 | 12 | 新增hook, decision, budget子命令 |
| Pydantic校验 | 13个模型 | 16个模型 | 新增3个Tool的Input模型+server_health Schema |
| API响应格式 | 不统一 | 统一标准结构 | 所有Tool返回{error, api_version, data, degradation_level} |
| API版本协商 | 无 | 有 | 客户端发送api_version，服务端校验兼容性 |

#### 3.4.2 相对v3.6.0的变更

##### 3.4.2.1 新增3个MCP Tool

| Tool名称 | 功能 | 参数Schema |
|----------|------|-----------|
| decision_log | 决策日志管理：记录/查询/导出ADR | DecisionLogInput: action(record/list/export/query), title, context, decision, alternatives, consequences, phase, workflow_id |
| token_budget | Token预算管理：查询/设置/监控Token使用 | TokenBudgetInput: action(status/set_budget/track/recommend/history), total_budget, tool_name, tokens_used, phase |
| project_init | 项目初始化：创建骨架/检测技术栈/验证结构 | ProjectInitInput: action(init/detect/scaffold/validate), project_path, template, project_name, features, workflow |

##### 3.4.2.2 新增4个MCP Resource

| Resource URI | 功能 | 数据源 |
|-------------|------|--------|
| xuansto://config/gate-scripts | 门禁-脚本映射配置 | GATE_SCRIPTS_MAP (config.py) |
| xuansto://config/hook-scripts | Hook-脚本映射配置 | HOOK_SCRIPTS_MAP (config.py) |
| xuansto://config/phase-gates | 阶段-门禁映射配置 | QUALITY_GATES_PHASE_MAP (config.py) |
| xuansto://decisions/latest | 最新决策日志 | WORK_DIR/decisions/下最新ADR文件 |

##### 3.4.2.3 SQLite持久化层重构

| 变更项 | 说明 |
|--------|------|
| xuansto_state.db | SQLite WAL模式状态库，9张表 |
| core/persistence.py | 统一持久化层，SQLite连接池+事务上下文管理器+busy_timeout |
| 启动自动迁移 | 检测JSON文件→导入SQLite→备份为.json.bak→删除原文件 |
| JSON降级读取 | SQLite不可用时自动降级到JSON文件读取 |
| 并发安全 | SQLite WAL模式+内置锁替代threading.Lock |

##### 3.4.2.4 独立Hook引擎

| 变更项 | 说明 |
|--------|------|
| 从server.py解耦 | Hook引擎从_with_hook_interception装饰器迁移为独立模块 |
| 插件式注册 | 支持通过YAML配置动态注册Hook，无需修改代码 |
| Hook链执行 | 支持多个Hook按优先级链式执行 |
| 16/16 Hook降级 | 补全Hook降级路径，从3/16提升到16/16 |

##### 3.4.2.5 可插拔搜索引擎

| 变更项 | 说明 |
|--------|------|
| SearchEngine抽象基类 | 定义retrieve/inject/precipitate接口 |
| ChromaDB引擎 | 默认搜索引擎，保持现有行为 |
| FTS5引擎 | 纯SQLite FTS5搜索引擎，无需ChromaDB依赖 |
| 关键词引擎 | 简单关键词匹配搜索引擎，零外部依赖 |
| 引擎切换 | 通过配置文件指定搜索引擎，运行时动态加载 |

##### 3.4.2.6 结构化错误码+i18n

| 变更项 | 说明 |
|--------|------|
| 错误码体系 | XST-XXXX格式：XST-1xxx(Tool错误), XST-2xxx(Resource错误), XST-3xxx(配置错误), XST-4xxx(降级错误) |
| 多语言消息 | 错误消息支持中文/英文，通过Accept-Language或配置指定 |
| 错误响应格式 | {error_code, message, message_i18n, details, api_version} |
| 向后兼容层 | v1.x客户端仍可解析，error_code和message_i18n为新增字段 |

##### 3.4.2.7 API响应格式统一

| 变更项 | v3.6.0 | v4.0.0 |
|--------|--------|--------|
| 成功响应 | 格式不统一 | `{error: false, api_version: "2.0.0", data: {...}, degradation_level?: string}` |
| 错误响应 | `{error: true, code: str, message: str}` | `{error: true, code: "XST-XXXX", message: str, message_i18n: {zh, en}, details: {...}}` |
| degradation_level位置 | 有时在data内，有时在顶层 | 始终在响应顶层 |
| quality_gate_check | `{gates_checked, gates_passed, results}` | `{checks, summary: {total, passed, failed, skipped, blocked}, cache_info}` |
| API版本协商 | 无 | 客户端发送api_version，服务端校验兼容性 |

#### 3.4.3 BREAKING变更

| 变更项 | v3.6.0行为 | v4.0.0行为 | 影响范围 | 迁移建议 |
|--------|-----------|-----------|----------|----------|
| API版本 | 1.1.0 | 2.0.0 | 所有MCP Tool调用 | 检查api_version字段，适配新响应格式 |
| 错误响应格式 | {error, code, message} | {error_code, message, message_i18n, details, api_version} | 错误处理逻辑 | 更新错误解析逻辑，支持error_code映射 |
| 降级策略格式 | 硬编码FALLBACK_MAP | YAML配置文件 | degradation.py调用 | 迁移自定义降级策略到YAML配置 |
| Hook注册方式 | _with_hook_interception装饰器 | 独立Hook引擎+YAML配置 | Hook定义和管理 | 迁移Hook定义到YAML配置文件 |
| data/目录定位 | 内嵌data/ | SKILL_ROOT环境变量引用 | MCP Server部署 | 设置SKILL_ROOT环境变量指向Skill目录 |
| quality_gate_check响应 | {gates_checked, gates_passed, results} | {checks, summary, cache_info} | 门禁检查结果处理 | 更新字段名映射 |
| Resource URI扩展 | 8个 | 11个 | Resource订阅逻辑 | 新增Resource URI不影响现有，但需更新订阅列表 |
| 持久化 | 5个JSON文件 | SQLite+JSON降级 | 持久化读写 | 启动时自动迁移，无需手动操作 |

#### 3.4.4 迁移路径（v3.6.0→v4.0.0）

| 迁移步骤 | 操作 | 验证方法 |
|----------|------|----------|
| 1 | 设置SKILL_ROOT环境变量 | 指向Skill目录根路径 |
| 2 | 升级MCP Server: `pip install xuansto-mcp-server>=4.0.0` | `xuansto-cli health` 返回version=4.0.0 |
| 3 | 验证SQLite自动迁移 | 启动时JSON→SQLite迁移成功，.json.bak备份存在 |
| 4 | 迁移降级策略到YAML | degradation.yaml可被MCP Server读取 |
| 5 | 迁移Hook定义到YAML | hooks.yaml可被独立Hook引擎读取 |
| 6 | 更新错误处理逻辑 | 结构化错误码可被正确解析 |
| 7 | 验证新增3个Tool | decision_log, token_budget, project_init功能正常 |
| 8 | 验证新增4个Resource | 逐个读取确认数据可访问 |
| 9 | 验证独立Hook引擎 | Hook插件式注册和16/16降级路径 |
| 10 | 验证可插拔搜索引擎 | 不同搜索引擎切换正常 |
| 11 | 验证事件驱动配置重载 | 修改配置文件，确认即时重载 |
| 12 | 验证API响应格式统一 | 13+3个Tool返回标准结构 |
| 13 | 回归测试16个Tool | 所有Tool在新API下行为一致 |

**不兼容警告**：v4.0.0 MCP Server API v2.0.0与v3.x客户端**不兼容**，必须同时升级Skill层到v8.0.0。

---

## 4. MCP+Skill兼容性矩阵

### 4.1 组合兼容性总览

| Skill版本 | MCP Server版本 | API版本 | 渐进式加载披露 | 降级链 | 兼容性 |
|-----------|---------------|---------|--------------|--------|--------|
| v5.0.0 | 无(不依赖) | N/A | ✗ | 脚本直接调用 | ✓ 独立运行 |
| v5.0.0 | v3.0.0 | 0.5.0 | ✗ | 无 | ⚠️ 声明MCP但无实际调用 |
| v7.0.0 | ≥3.5.0 | 1.0.0 | ✓(基础) | MCP→脚本→内嵌 | ✓ 推荐 |
| v7.0.0 | v3.6.0 | 1.1.0 | ✓(基础) | MCP→脚本→内嵌 | ✓ 向后兼容 |
| v7.1.0 | ≥3.5.0 | 1.0.0 | ✓(基础) | MCP→脚本→内嵌 | ✓ 降级运行 |
| v7.1.0 | ≥3.6.0 | 1.1.0 | ✓(增强) | MCP→脚本→内嵌+统计 | ✓ 推荐 |
| v8.0.0 | ≥4.0.0 | 2.0.0 | ✓(完整) | MCP→脚本→内嵌+追踪 | ✓ 必须 |
| v8.0.0 | v3.x | - | - | - | ✗ 不兼容 |

### 4.2 兼容性详细说明

| Skill版本 | MCP Server版本 | API版本 | 渐进式加载披露 | 降级链 | 持久化 | 测试覆盖 | 状态 |
|-----------|---------------|---------|--------------|--------|--------|---------|------|
| v5.0.0 | 无(不依赖) | N/A | ✗ | 脚本直接调用 | 无 | 0% | 已废弃 |
| v7.0.0 | ≥3.5.0 | 1.0.0 | ✓(基础) | MCP→脚本→内嵌 | 5个JSON | 0% | 当前 |
| v7.1.0 | ≥3.5.0 | 1.0.0 | ✓(基础) | MCP→脚本→内嵌 | 5个JSON | 20% | 规划中 |
| v7.1.0 | ≥3.6.0 | 1.1.0 | ✓(增强) | MCP→脚本→内嵌+统计 | 5个JSON | 20% | 规划中(推荐) |
| v8.0.0 | ≥4.0.0 | 2.0.0 | ✓(完整) | MCP→脚本→内嵌+追踪+配置化 | SQLite+JSON降级 | 80%+ | 规划中 |

### 4.3 渐进式加载披露兼容性矩阵

| Skill版本 | MCP Server版本 | LoadPhase | LoadingProgress | available_functions | disclosure_note | loading/status Resource | priority/batch_mode | DisclosureTransition | LoadPhaseStateMachine | 披露模式 |
|-----------|---------------|-----------|-----------------|---------------------|----------------|----------------------|---------------------|---------------------|----------------------|---------|
| v5.0.0 | 无 | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | 全量加载 |
| v7.0.0 | v3.5.0 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ | 渐进式加载披露(基础) |
| v7.0.0 | v3.6.0 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ | 渐进式加载披露(基础) |
| v7.1.0 | v3.5.0 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ | 渐进式加载披露(基础，无DisclosureTransition) |
| v7.1.0 | v3.6.0 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 渐进式加载披露(增强，含DisclosureTransition) |
| v8.0.0 | v4.0.0 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 完整渐进式加载披露+Token预算驱动 |

### 4.4 降级链兼容性矩阵

| Skill版本 | MCP Server版本 | 降级策略 | 降级可用性 | 降级追踪 | Hook降级覆盖 |
|-----------|---------------|---------|-----------|---------|-------------|
| v5.0.0 | 无 | 脚本直接调用 | ✓ | ✗ | N/A |
| v7.0.0 | v3.5.0 | MCP→脚本→内嵌 | ✓ | ✗ | 3/16 |
| v7.0.0 | v3.6.0 | MCP→脚本→内嵌 | ✓ | ✗ | 3/16 |
| v7.1.0 | v3.5.0 | MCP→脚本→内嵌 | ✓ | ✗ | 3/16 |
| v7.1.0 | v3.6.0 | MCP→脚本→内嵌+统计 | ✓ | ✓(stats/degradation) | 3/16 |
| v8.0.0 | v4.0.0 | MCP→脚本→内嵌+追踪+配置化 | ✓ | ✓(完整) | 16/16 |

---

## 5. 版本间迁移路径

### 5.1 Skill层迁移

#### 5.1.1 v5.0.0 → v7.0.0：完整迁移指南

**前置条件**：

| 条件 | 说明 |
|------|------|
| Python ≥ 3.10 | MCP Server运行时要求 |
| xuansto-mcp-server ≥ 3.5.0 | MCP工具提供方 |
| MCP协议支持 | IDE需支持MCP协议(stdio传输) |

**迁移步骤**：

| 步骤 | 操作 | 验证方法 |
|------|------|----------|
| 1 | 安装xuansto-mcp-server: `pip install xuansto-mcp-server>=3.5.0` | `xuansto-cli health` 返回OK |
| 2 | 配置IDE的MCP连接(stdio) | MCP Server启动日志无错误 |
| 3 | 替换Skill目录: xuansto-skill → xuansto-skill-v2 | SKILL.md frontmatter version=7.0.0 |
| 4 | 验证MCP工具注册: `server_health()` | tools_count=13, resources_count=7 |
| 5 | 验证MCP Resource可访问: 逐个读取7个URI | 每个URI返回非空内容 |
| 6 | 验证降级链: 模拟MCP Server不可用 | 脚本降级实际执行 |
| 7 | 迁移自定义配置: .skill-config.yaml → MCP Server data/ | 配置项在新位置可读取 |
| 8 | 迁移自定义Hook: hooks.json → MCP Server data/hooks/ | Hook定义在新位置可读取 |
| 9 | 标记v1为deprecated | v1 SKILL.md `deprecated: true` |

**数据映射**：

| v5.0.0位置 | v7.0.0位置 | 访问方式变化 |
|-----------|-----------|-------------|
| agents/*.md(57个) | MCP Server data/agents/(57个) | 本地文件读取 → MCP Resource/agents/目录 |
| commands/*.md(27个) | 嵌入SKILL.md(L213-L378) | 独立文件 → 内嵌路由表+独立文件双源 |
| workflows/*.md + *.yaml | MCP Server合并版 | 15个独立文件 → 1个合并Resource |
| scripts/*.py/*.js | MCP Server data/scripts/ | 本地直接调用 → MCP Tool降级 |
| templates/* | MCP Resource | 本地文件读取 → xuansto://templates/{name} |
| references/*.md | MCP Server data/references/ | 本地文件读取 → MCP Resource(6本地+100+MCP) |
| configs/default.yaml | MCP Server data/.skill-config.yaml | 本地文件读取 → MCP Resource |
| hooks/hooks.json | MCP Server data/hooks/ | 本地文件读取 → MCP hook_manage工具 |
| knowledge/* | MCP Server data/knowledge/ | 本地knowledge-server.py → MCP knowledge_search |

**功能差异**：

| 功能 | v5.0.0 | v7.0.0 | 差异说明 |
|------|--------|--------|----------|
| 命令调用链 | 完整3-4步 | 简化1-3步 | 部分命令调用链不完整 |
| 降级模式 | 脚本直接调用 | MCP→脚本→内嵌逻辑 | 降级链统一管理，三级实际调用 |
| 参考文档 | 72+本地文件 | 6本地+100+MCP Server | 本地参考减少但MCP Server提供完整集 |
| Agent定义访问 | 57个独立.md文件 | MCP Resource摘要+agents/目录 | MCP Resource返回摘要，完整定义在agents/目录 |
| 工作流YAML | 10个独立.yaml | 0(合并为1个.md) | YAML工作流定义缺失 |
| 评估配置 | evals/目录 | 无 | 评估功能不可用 |
| 渐进式加载披露 | 无 | 基础实现 | 4级加载+LoadPhase+available_functions |
| 会话持久化 | 无 | MCP驱动 | session_manage支持7种action |
| 工作流调度 | 无 | MCP驱动 | workflow_dispatch支持6种action |

#### 5.1.2 v7.0.0 → v7.1.0：渐进式升级

**前置条件**：

| 条件 | 说明 |
|------|------|
| xuansto-mcp-server ≥ 3.5.0 | 最低兼容（渐进式加载披露保持基础模式） |
| xuansto-mcp-server ≥ 3.6.0(推荐) | 渐进式加载披露增强（DisclosureTransition+降级统计） |

**升级步骤**：

| 步骤 | 操作 | 验证方法 |
|------|------|----------|
| 1 | 升级MCP Server到v3.6.0(推荐) | `xuansto-cli health` 返回version=3.6.0 |
| 2 | 替换SKILL.md为Phase-aware摘要版 | SKILL.md行数≤150行，Token消耗≤3K |
| 3 | 创建commands/routing.yaml | YAML解析器可正确解析27命令路由 |
| 4 | 更新references/目录(6→15+文件) | 关键参考文件可访问 |
| 5 | 验证渐进式加载披露增强 | 确认DisclosureTransition过渡披露返回 |
| 6 | 验证stats/degradation Resource | xuansto://stats/degradation返回降级统计 |
| 7 | 验证MCP Resource降级路径 | 模拟MCP不可用，确认7个Resource降级路径可用 |
| 8 | 回归测试27命令 | 所有命令触发和路由正确 |

**兼容性降级**：

| MCP Server版本 | 渐进式加载披露 | 说明 |
|---------------|--------------|------|
| v3.5.0 | ✓(基础) | 无DisclosureTransition、无stats/degradation Resource，保持当前基础模式 |
| v3.6.0 | ✓(增强) | DisclosureTransition过渡披露+stats/degradation+格式统一 |

#### 5.1.3 v7.x → v8.0.0：大版本升级

**前置条件**：

| 条件 | 说明 |
|------|------|
| xuansto-mcp-server ≥ 4.0.0 | **必须**，v3.x不兼容 |
| SKILL_ROOT环境变量 | MCP Server通过此变量定位Skill资源 |
| 测试覆盖率 ≥ 80% | 生产级发布要求 |

**升级步骤**：

| 步骤 | 操作 | 验证方法 |
|------|------|----------|
| 1 | 升级MCP Server到v4.0.0 | `xuansto-cli health` 返回version=4.0.0 |
| 2 | 设置SKILL_ROOT环境变量 | MCP Server可读取Skill目录资源 |
| 3 | 替换SKILL.md为多文件体系 | SKILL.md + triggers.yaml + routes.yaml + registry.yaml + constraints.yaml |
| 4 | 迁移降级策略到YAML配置 | degradation.yaml可被MCP Server读取 |
| 5 | 更新错误处理逻辑 | 结构化错误码可被正确解析 |
| 6 | 验证SQLite自动迁移 | 启动时JSON→SQLite迁移成功 |
| 7 | 运行完整测试套件 | 覆盖率≥80% |
| 8 | 验证四级渐进式加载披露 | Level 0→1→2→3加载正确 |
| 9 | 验证Token预算驱动 | Token>80%自动压缩，>95%降级到Level 0 |
| 10 | 回归测试27命令 | 所有命令在新架构下行为一致 |
| 11 | 性能基线验证 | Token消耗≤2K(触发)，≤5K(单命令) |

**BREAKING变更处理**：

| BREAKING变更 | 处理方式 |
|-------------|----------|
| SKILL.md拆分 | 更新所有依赖SKILL.md的解析逻辑，支持多文件引用 |
| API v2.0.0 | 更新MCP Tool调用代码，适配新响应格式{error, api_version, data, degradation_level} |
| MCP Server v4.0.0 | 必须升级，v3.x不兼容 |
| quality_gate_check响应 | 更新字段名映射(gates_checked→checks, results→summary) |
| 降级策略YAML化 | 迁移自定义降级策略到YAML |
| 错误码国际化 | 更新错误处理逻辑，支持XST-XXXX错误码 |
| 持久化迁移 | 启动时自动JSON→SQLite迁移，无需手动操作 |

### 5.2 MCP Server层迁移

#### 5.2.1 v3.0.0 → v3.5.0：功能扩展迁移

| 步骤 | 操作 | 验证方法 |
|------|------|----------|
| 1 | 升级MCP Server: `pip install xuansto-mcp-server>=3.5.0` | `xuansto-cli health` 返回version=3.5.0 |
| 2 | 配置MCP连接(stdio) | MCP Server启动日志无错误 |
| 3 | 验证新增5个Tool | spec_drift_detect, security_scan, code_simplify, resource_load_status, context_compress |
| 4 | 验证7个Resource URI | 逐个读取确认数据可访问(含loading/status) |
| 5 | 验证Hook拦截 | 确认_with_hook_interception包装生效 |
| 6 | 验证配置热重载 | 修改配置文件，确认5s内自动重载 |
| 7 | 验证CLI扩展 | 测试新增config, reload, workflow, session, agent子命令 |
| 8 | 验证降级链 | 模拟MCP部分不可用→脚本降级成功 |
| 9 | 验证渐进式加载披露 | 调用resource_load_status(status)确认loading/status可用 |

**迁移注意事项**：

| 注意项 | 说明 |
|--------|------|
| MCP协议版本升级 | 从2024-11-05升级到2025-03-26，需确认Host支持 |
| API版本变化 | 从v0.5.0升级到v1.0.0，响应格式有变化 |
| Python版本要求 | 从≥3.8升级到≥3.10 |
| 新增Pydantic校验 | 参数校验更严格，可能暴露之前未发现的参数问题 |
| 降级链变化 | v3.5.0降级链已实现实际脚本调用(非占位响应) |
| 新增渐进式加载披露 | v3.5.0已实现基础渐进式加载披露 |

#### 5.2.2 v3.5.0 → v3.6.0：渐进式加载披露增强迁移

| 步骤 | 操作 | 验证方法 |
|------|------|----------|
| 1 | 升级MCP Server: `pip install xuansto-mcp-server>=3.6.0` | `xuansto-cli health` 返回version=3.6.0 |
| 2 | 验证新增Resource | 读取xuansto://stats/degradation |
| 3 | 验证DisclosureTransition | 触发Phase切换，确认过渡披露信息返回 |
| 4 | 验证resource_state.json格式统一 | 确认新格式写入正确，旧格式可兼容读取 |
| 5 | 验证Resource降级路径 | 模拟MCP不可用，确认7个Resource降级路径可用 |
| 6 | 回归测试13个Tool | 所有Tool原有功能不受影响 |

**兼容性说明**：v3.6.0完全向后兼容v3.5.0，API v1.1.0兼容v1.0.0客户端。可无缝升级。

#### 5.2.3 v3.6.0 → v4.0.0：BREAKING大版本迁移

| 步骤 | 操作 | 验证方法 |
|------|------|----------|
| 1 | 设置SKILL_ROOT环境变量 | 指向Skill目录根路径 |
| 2 | 升级MCP Server: `pip install xuansto-mcp-server>=4.0.0` | `xuansto-cli health` 返回version=4.0.0 |
| 3 | 验证SQLite自动迁移 | 启动时JSON→SQLite迁移成功，.json.bak备份存在 |
| 4 | 迁移降级策略到YAML | degradation.yaml可被MCP Server读取 |
| 5 | 迁移Hook定义到YAML | hooks.yaml可被独立Hook引擎读取 |
| 6 | 更新错误处理逻辑 | 结构化错误码可被正确解析 |
| 7 | 验证新增3个Tool | decision_log, token_budget, project_init |
| 8 | 验证新增4个Resource | 逐个读取确认数据可访问 |
| 9 | 验证独立Hook引擎 | Hook插件式注册和16/16降级路径 |
| 10 | 验证可插拔搜索引擎 | 不同搜索引擎切换正常 |
| 11 | 验证事件驱动配置重载 | 修改配置文件，确认即时重载 |
| 12 | 验证API响应格式统一 | 16个Tool返回标准结构 |
| 13 | 回归测试16个Tool | 所有Tool在新API下行为一致 |

**BREAKING变更处理**：

| BREAKING变更 | 处理方式 |
|-------------|----------|
| API v2.0.0 | 更新所有MCP Tool调用代码，适配新响应格式 |
| 错误响应格式 | 更新错误解析逻辑，支持XST-XXXX错误码映射 |
| quality_gate_check响应 | 更新字段名映射(gates_checked→checks, results→summary) |
| 降级策略YAML化 | 迁移自定义降级策略到YAML配置 |
| Hook独立引擎 | 迁移Hook定义到YAML，更新Hook管理逻辑 |
| SKILL_ROOT | 设置环境变量，更新部署脚本 |
| 持久化迁移 | 启动时自动JSON→SQLite迁移，无需手动操作 |

**不兼容警告**：v4.0.0 API v2.0.0与v3.x客户端**不兼容**，必须同时升级Skill层到v8.0.0。

---

## 6. 版本号对应关系

### 6.1 Skill与MCP Server版本对应

| Skill版本 | MCP Server版本 | API版本 | 发布时间(预估) | 关键特性 |
|-----------|---------------|---------|---------------|---------|
| v5.0.0 | 无(不依赖) | N/A | 2026-05-06(已发布) | 文件系统驱动，全量加载，脚本直接调用 |
| v7.0.0 | v3.5.0 | 1.0.0 | 2026-05-22(已发布) | MCP工具驱动，13 Tool + 7 Resource，渐进式加载披露(基础)，三级降级链 |
| v7.1.0 | v3.6.0 | 1.1.0 | 阶段1-2完成后 | SKILL.md精简(~120行)，渐进式加载披露(增强)，DisclosureTransition，降级统计 |
| v8.0.0 | v4.0.0 | 2.0.0 | 全部4阶段完成后 | 生产级发布，SKILL.md拆分(5文件)，SQLite持久化，独立Hook引擎，16 Tool + 11 Resource |

### 6.2 MCP Server版本演进

| MCP Server版本 | API版本 | 发布时间(预估) | Tool数 | Resource数 | 关键特性 |
|---------------|---------|---------------|--------|-----------|---------|
| v3.0.0 | 0.5.0 | 2026-04(已发布) | 8 | 0 | 最小工具集，无Resource层，无降级链 |
| v3.5.0 | 1.0.0 | 2026-05-22(已发布) | 13 | 7 | 完整工具集，Hook拦截，Pydantic校验，渐进式加载披露(基础)，三级降级链(实际脚本调用) |
| v3.6.0 | 1.1.0 | 阶段1-2完成后 | 13 | 8 | 渐进式加载披露(增强)，DisclosureTransition，LoadPhaseStateMachine，降级统计，Resource降级路径 |
| v4.0.0 | 2.0.0 | 全部4阶段完成后 | 16 | 11 | SQLite持久化，独立Hook引擎，可插拔搜索引擎，SKILL_ROOT，结构化错误码+i18n，API响应格式统一 |

### 6.3 版本发布里程碑

| 里程碑 | Skill版本 | MCP Server版本 | API版本 | 依赖关系 | 发布条件 | 对应重构阶段 |
|--------|-----------|---------------|---------|---------|---------|-------------|
| M1: 基线发布 | v5.0.0 | 无 | N/A | 无 | 文件体系完整 | - |
| M2: MCP化发布 | v7.0.0 | v3.5.0 | 1.0.0 | Skill依赖MCP Server ≥3.5.0 | 13 Tool + 7 Resource可用，渐进式加载披露(基础)，三级降级链 | - |
| M3: 瘦身+披露增强 | v7.1.0 | v3.6.0 | 1.1.0 | Skill依赖MCP Server ≥3.5.0(推荐≥3.6.0) | SKILL.md≤150行 + DisclosureTransition + 降级统计 + Resource降级路径 | 阶段1+阶段4部分 |
| M4: 持久化+降级统一 | - | v3.6.1(可选) | 1.1.0 | 向后兼容v3.6.0 | SQLite持久化 + 降级链统一 + API响应格式统一 | 阶段2+阶段3 |
| M5: 生产级发布 | v8.0.0 | v4.0.0 | 2.0.0 | Skill **必须** MCP Server ≥4.0.0 | 测试覆盖率≥80% + 独立Hook引擎 + SKILL_ROOT + 16 Tool + 11 Resource | 全部4阶段 |

### 6.4 版本号命名规则

| 组件 | 版本号位置 | 命名规则 | 示例 |
|------|----------|---------|------|
| Skill | SKILL.md frontmatter `version` | SemVer MAJOR.MINOR.PATCH | `version: 7.0.0` |
| MCP Server | pyproject.toml `version` + server.py `instructions` | SemVer MAJOR.MINOR.PATCH | `version = "3.5.0"` |
| MCP API | config.py `MCP_API_VERSION` | SemVer MAJOR.MINOR.PATCH | `MCP_API_VERSION = "1.0.0"` |
| Skill最低兼容 | SKILL.md `xuansto-mcp-server >= X.Y.Z` | 最低MCP Server版本 | `xuansto-mcp-server >= 3.5.0` |

**版本号同步规则**：

| 场景 | Skill版本 | MCP Server版本 | API版本 | 说明 |
|------|-----------|---------------|---------|------|
| Skill MINOR升级 | +0.1.0 | 不变或+0.1.0 | 不变 | Skill功能增强，MCP Server可选升级 |
| Skill MAJOR升级 | +1.0.0 | +1.0.0 | +1.0.0 | 破坏性变更，Skill和MCP Server必须同步升级 |
| MCP Server MINOR升级 | 不变 | +0.1.0 | +0.1.0 | MCP Server功能增强，Skill向后兼容 |
| MCP Server PATCH升级 | 不变 | +0.0.1 | 不变 | Bug修复，完全兼容 |
