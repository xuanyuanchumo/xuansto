# Xuansto Skill v2 (MCP Edition) 问题清单

> 版本：9.0.0
> 更新日期：2026-05-27
> 分析范围：SKILL.md、57个Agent定义、32个命令、20个MCP工具、降级脚本、渐进式加载、模块化重构

---

## P0 - 阻塞性问题

### P0-01: v2降级模式不可用 ✅ 已修复
- **需求来源**: SKILL.md声明"MCP工具优先→脚本降级→文件系统兜底"
- **当前状态**: ✅ 已修复 — degradation.py已实现MCPToolFallback类，包含14个MCP工具的脚本调用链
- **修复内容**:
  - 新增MCPToolFallback类，实现subprocess.run调用scripts/目录下Python脚本
  - 三级降级策略：脚本执行→内联降级→错误响应
  - 14个MCP工具映射到对应降级脚本
  - 内联降级实现：spec_drift_detect、security_scan、code_simplify、agent_status、hook_manage、resource_load_status、server_health、workflow_dispatch
  - 超时控制（默认120秒）和线程安全日志
- **影响**: MCP Server不可用时，系统可通过脚本降级继续运行

### P0-02: v2缺少references/完整参考文档 ✅ 已修复
- **需求来源**: v1有72+参考文件，v2仅2个
- **当前状态**: ✅ 已修复 — v2 references/现已包含79+参考文件，SKILL.md外部参考表已更新为18个条目（4个配置+14个参考文档）
- **修复内容**:
  - 从v1迁移并创建全部关键参考文档（quality-gates.md、agent-registry.md、knowledge-workflow-details.md等）
  - 扩展mcp-integration-strategy.md（38行→367行）和parallelization-strategy.md（45行→414行）
  - SKILL.md外部参考表按优先级分组：P0核心工作流(5)、P1集成与质量(11)、P2并行优化(2)
- **影响**: Agent和命令执行时可获取完整参考文档

## P1 - 高优先级问题

### P1-01: MCP Server版本与Skill版本不一致 ✅ 已修复
- **当前状态**: ✅ 已修复 — SKILL.md YAML frontmatter新增compatible_mcp_server: ">=4.0.0"，API版本声明更新为3.0.0
- **修复内容**:
  - SKILL.md新增compatible_mcp_server字段声明最低兼容MCP Server版本
  - MCP依赖声明更新为xuansto-mcp-server >= 4.0.0 | API版本: 3.0.0
- **影响**: 用户可明确判断版本兼容性

### P1-02: server_health工具未在v2 mcp-tools.md中列出 ✅ 已修复
- **当前状态**: ✅ 已修复 — references/mcp-tools.md已补充server_health完整文档
- **修复内容**:
  - 补充server_health工具参数（action: check|version|status, include_details: bool）
  - 补充返回值JSON Schema（status, version, api_version, uptime_seconds, tools_available, degradation_level等）
  - 补充错误码和降级脚本路径
- **影响**: 用户可了解server_health工具的完整参数和返回值

### P1-03: knowledge_search缺少inject/precipitate action文档 ✅ 已修复
- **当前状态**: ✅ 已修复 — references/mcp-tools.md已补充inject和precipitate action完整文档
- **修复内容**:
  - 补充inject action参数（content, scope, metadata）和返回值Schema
  - 补充precipitate action参数（experience_type, min_confidence, scope, pattern_ids）和返回值Schema
  - 补充inject/precipitate专用错误码（INJECT_FAILED, PRECIPITATE_NO_PATTERNS, DUPLICATE_CONTENT）
  - 补充降级脚本路径和调用示例
- **影响**: 知识注入和经验沉淀功能可正常使用

### P1-04: skill_tools.py单文件过大 ✅ 已修复（8.1.0-dev）
- **需求来源**: skill_tools.py 2300+行，所有15个Skill工具处理器耦合在单一文件中
- **当前状态**: ✅ 已修复 — 拆分为 tools/ 子包，15个独立模块 + __init__.py + _shared.py
- **修复内容**:
  - 创建 scripts/knowledge_server/tools/ 目录
  - 每个工具模块包含 get_tool_definition() 和 handle_tool() 函数
  - tools/__init__.py 导出 TOOL_REGISTRY 字典实现动态注册
  - tools/_shared.py 集中共享常量和辅助函数
  - skill_tools.py 精简为74行，SkillToolHandler 委托给 TOOL_REGISTRY
  - mcp_server.py 导入路径更新为从 .tools 导入
- **影响**: 每个工具可独立开发、测试和维护

### P1-05: 降级映射硬编码 ✅ 已修复（8.1.0-dev）
- **需求来源**: degradation.py 的 MCPToolFallback 硬编码14个工具映射，与 constraints.yaml 可能不一致
- **当前状态**: ✅ 已修复 — MCPToolFallback 从 constraints.yaml 读取映射，失败时回退到硬编码
- **修复内容**:
  - 新增 _load_fallbacks_from_yaml() 方法从 constraints.yaml 读取 degradation.tool_fallbacks
  - constraints.yaml 的 tool_fallbacks 升级为结构化格式（script/args/inline）
  - 降级结果格式统一为 JSON（degraded/inline_degraded/error 三种状态）
  - 向后兼容：YAML读取失败自动回退到硬编码映射
- **影响**: 降级策略单一权威源为 constraints.yaml

### P1-06: Skill层与MCP层加载状态缺乏双向同步 ✅ 已修复（8.1.0-dev）
- **需求来源**: SKILL.md PHASE标记与 progressive_loader.py LoadPhase 枚举无对应关系
- **当前状态**: ✅ 已修复 — 建立了命令驱动推进 + PHASE标记同步 + 降级通知的双向机制
- **修复内容**:
  - progressive_loader.py 新增 COMMAND_PHASE_MAP（命令→阶段映射）和 PHASE_SKILL_MAP（PHASE→LoadPhase映射）
  - SkillToolHandler.handle() 工具成功执行后自动调用 _try_advance_phase() 推进加载阶段
  - progressive_loader.py 新增 degrade_phase() 方法，降级时设置 degraded=True 和 degraded_from
  - resource_load_status 工具响应新增 degraded 和 degraded_from 字段
  - LoadingState 数据类扩展 degraded 和 degraded_from 字段
- **影响**: 命令执行时自动推进加载阶段，降级时Skill层可感知

## P2 - 中等优先级问题

### P2-01: v2缺少评估配置文件 ✅ 已修复（8.1.0-dev）
- **当前状态**: ✅ 已修复 — evals/ 目录已创建，包含 mcp_evaluation.xml 和 trigger_eval.json
- **修复内容**:
  - 创建 evals/mcp_evaluation.xml（5个QA对，覆盖5个核心MCP工具）
  - 创建 evals/trigger_eval.json（3条触发评估配置）
- **影响**: 可进行技能评估

### P2-02: v2缺少CHANGELOG.md ✅ 已修复（8.1.0-dev）
- **当前状态**: ✅ 已修复 — CHANGELOG.md 已创建
- **修复内容**:
  - 创建 CHANGELOG.md，记录 v8.0.0 版本变更（Added/Changed/Fixed）
  - 遵循 Keep a Changelog 格式和语义化版本规范
- **影响**: 可追踪v2的版本变更

## P3 - 低优先级问题

### P3-01: v1与v2存在重复文件 ✅ 已缓解
- **当前状态**: ✅ 已缓解 — v1技能目录已不存在于.trae/skills/下，SKILL.md frontmatter已设置v1_archived: true（line 17），v2为唯一维护版本
- **影响**: 无实际重复文件，v1已归档标记
- **缓解措施**:
  - .trae/skills/下仅存在xuansto-skill-v2目录，无v1目录
  - SKILL.md YAML frontmatter v1_archived: true 明确标识v1已归档
  - v2为唯一维护版本，无重复文件维护负担

### P3-02: v2 SKILL.md行数可能超过500行
- **当前状态**: 增强后的SKILL.md已添加PHASE标记实现渐进式加载，实际Token消耗由Phase控制
- **影响**: 通过渐进式加载机制已缓解，Phase 0仅加载≤2K Token
- **修复方案**: 已通过PHASE标记实现渐进式加载，SKILL.md按Phase分段加载

## 新增问题（来自8.1.0-dev重构分析）

### ARCH-01: Skill-MCP通信同步/异步混合 ✅ 已修复（v8.5.0）
- **当前状态**: ✅ 已修复 — 所有22个Tool handler统一为 async def，subprocess.run 包装为 asyncio.to_thread，degradation.py 降级回退转换为 async
- **修复内容**:
  - 所有22个MCP Tool handler 统一为 async def
  - subprocess.run 调用包装为 asyncio.to_thread，避免阻塞事件循环
  - degradation.py 降级回退函数转换为 async
- **文件路径**: xuansto-mcp-server/src/xuansto_mcp/tools/, xuansto-mcp-server/src/xuansto_mcp/scripts/degradation.py
- **影响**: Skill-MCP通信全链路异步，消除同步/异步混合导致的潜在死锁和性能问题

### ARCH-05: MCP Resource变更通知不可达 ✅ 已修复（v8.5.0）
- **当前状态**: ✅ 已修复 — 阶段变更通知已添加到 resource_load_status.py，resource_subscribe 已注册
- **修复内容**:
  - resource_load_status.py 新增 degrade_phase 和 preload 阶段变更通知
  - resource_subscribe 工具已注册，支持订阅 Resource URI 变更通知
  - Agent 可通过订阅机制感知 Resource 状态变更
- **文件路径**: xuansto-mcp-server/src/xuansto_mcp/tools/resource_load_status.py
- **影响**: Resource 变更通知可达，Agent 可实时感知状态变更

### ARCH-06: 缺少Agent持久化机制 ✅ 已修复（v8.4.0）
- **当前状态**: ✅ 已修复 — database.py 已创建 agent_states 表，实现 save/load/delete_agent_state 函数
- **修复内容**:
  - 新增 agent_states 表存储Agent状态
  - 实现 save_agent_state、load_agent_state、delete_agent_state 函数
  - Agent重启后可从SQLite恢复状态
- **文件路径**: xuansto-mcp-server/src/xuansto_mcp/core/database.py
- **影响**: 长时间工作流中断后可恢复Agent状态

### ARCH-07: 工作流状态仅内存存储 ✅ 已修复（v8.4.0）
- **当前状态**: ✅ 已修复 — database.py 已创建 workflow_states 表，实现 save/load/delete/list_workflow_state 函数
- **修复内容**:
  - 新增 workflow_states 表存储工作流状态
  - 实现 save_workflow_state、load_workflow_state、delete_workflow_state、list_workflow_states 函数
  - MCP Server重启后工作流状态可从SQLite恢复
- **文件路径**: xuansto-mcp-server/src/xuansto_mcp/core/database.py
- **影响**: MCP Server重启后工作流状态不再丢失

### ARCH-08: Token预算与加载阶段未关联 ✅ 已修复（v8.4.0）
- **当前状态**: ✅ 已修复 — token_budget.py 已实现 PHASE_TOKEN_BUDGET_MAP 和 set_from_phase 操作
- **修复内容**:
  - 新增 PHASE_TOKEN_BUDGET_MAP 建立LoadPhase与Token预算的映射关系
  - 实现 set_from_phase 操作，根据加载阶段自动调整Token分配
  - Token预算与渐进式加载阶段联动
- **文件路径**: xuansto-mcp-server/src/xuansto_mcp/tools/token_budget.py
- **影响**: 可根据加载阶段自动调整Token分配

### ARCH-09: Hook执行无超时保护 ✅ 已修复（v8.4.0）
- **当前状态**: ✅ 已修复 — hook_engine.py 已实现 DEFAULT_HOOK_TIMEOUT_SECONDS 和 asyncio.wait_for 超时控制
- **修复内容**:
  - 新增 DEFAULT_HOOK_TIMEOUT_SECONDS 常量定义默认超时时间
  - 使用 asyncio.wait_for 为Hook执行添加超时控制
  - 超时后自动取消Hook执行并返回超时错误
- **文件路径**: xuansto-mcp-server/src/xuansto_mcp/core/hook_engine.py
- **影响**: 恶意或错误Hook不再无限阻塞

### ARCH-10: 配置变更需重启MCP Server ✅ 已修复（v8.4.0）
- **当前状态**: ✅ 已修复 — config.py 已实现 start_config_watcher 和 watchfiles 热更新机制
- **修复内容**:
  - 新增 start_config_watcher 函数启动配置文件监听
  - 使用 watchfiles 库实现配置文件变更检测
  - 配置变更后自动热更新，无需重启MCP Server
- **文件路径**: xuansto-mcp-server/src/xuansto_mcp/core/config.py
- **影响**: 配置变更后无需重启即可生效

### ARCH-11: 错误处理不统一 ✅ 已修复（v8.4.0）
- **当前状态**: ✅ 已修复 — 所有20个MCP工具统一使用 make_success_response/make_error_response 返回JSON格式
- **修复内容**:
  - errors.py 新增 make_success_response 和 make_error_response 统一响应函数
  - 所有20个MCP工具统一使用JSON格式返回结果
  - 错误码和错误信息标准化
- **文件路径**: xuansto-mcp-server/src/xuansto_mcp/core/errors.py
- **影响**: 调用方只需处理统一的JSON返回格式

### ARCH-12: 缺少API版本协商机制 ✅ 已修复（v8.4.0）
- **当前状态**: ✅ 已修复 — server_health.py 已实现 _negotiate_api_version 函数和 negotiate_version 操作
- **修复内容**:
  - 新增 _negotiate_api_version 函数实现API版本协商逻辑
  - server_health 工具新增 negotiate_version 操作
  - 客户端与服务端版本不匹配时可优雅降级
- **文件路径**: xuansto-mcp-server/src/xuansto_mcp/tools/server_health.py
- **影响**: 客户端与服务端版本不匹配时可优雅降级

### DB-01: 决策记录双写一致性风险 ✅ 已修复（v8.5.0）
- **当前状态**: ✅ 已修复 — decision_log.py SQLite 主存储策略，文件备份可选（configure action），_reconcile_decisions 增强
- **修复内容**:
  - v8.4.0: decision_log.py 新增 _reconcile_decisions 对账函数和 reconcile 操作
  - v8.5.0: SQLite 主存储策略（决策记录以 SQLite 为权威源，文件备份可选）
  - v8.5.0: decision_log 新增 configure action（file_backup: true/false）
  - v8.5.0: _reconcile_decisions 增强（SQLite→文件单向同步，文件写入失败不影响主存储）
- **文件路径**: xuansto-mcp-server/src/xuansto_mcp/tools/decision_log.py
- **影响**: 决策记录双写有一致性保证和对账机制，SQLite 为权威源

### DB-02: ChromaDB与SQLite双写无事务保证 ✅ 已修复（v8.5.0）
- **当前状态**: ✅ 已修复 — database.py ChromaDB 3次指数退避重试，sync_status='failed' 追踪，reconcile 增强对账
- **修复内容**:
  - v8.4.0: persist_knowledge_dual_write 函数实现双写事务保证，reconcile_knowledge_stores 对账函数
  - v8.5.0: ChromaDB 双写重试机制（3次指数退避重试，1s/2s/4s间隔）
  - v8.5.0: sync_status='failed' 状态追踪（ChromaDB写入失败时标记，reconcile可修复）
  - v8.5.0: reconcile 增强对账（自动检测 failed 条目并重试同步，reconciliation_log 审计追踪）
- **文件路径**: xuansto-mcp-server/src/xuansto_mcp/core/database.py
- **影响**: ChromaDB与SQLite双写有事务保证、重试机制和自动对账

### DB-03: 知识条目版本历史无清理策略 ✅ 已修复（v8.4.0）
- **当前状态**: ✅ 已修复 — 已实现 cleanup_knowledge_versions 函数和 KNOWLEDGE_VERSION_CLEANUP_KEEP_LAST_N 环境变量
- **修复内容**:
  - 新增 cleanup_knowledge_versions 函数自动清理过期版本历史
  - 新增 KNOWLEDGE_VERSION_CLEANUP_KEEP_LAST_N 环境变量控制保留版本数
  - 防止版本历史无限增长导致数据库膨胀
- **文件路径**: xuansto-mcp-server/src/xuansto_mcp/core/database.py
- **影响**: 版本历史有清理策略，数据库不再膨胀

### MCP-01: Server指令版本(8.4.0)与pyproject.toml(8.5.0)不一致 ✅ 已修复（v8.5.0）
- **当前状态**: ✅ 已修复 — server.py 和 __init__.py 版本号已更新为 8.5.0，与 pyproject.toml 一致
- **修复内容**:
  - server.py 版本号从 8.4.0 更新为 8.5.0
  - __init__.py 版本号从 8.4.0 更新为 8.5.0
  - 三源版本号（server.py / __init__.py / pyproject.toml）现已统一为 8.5.0
- **文件路径**: xuansto-mcp-server/src/xuansto_mcp/server.py, xuansto-mcp-server/src/xuansto_mcp/__init__.py
- **影响**: Server指令版本与项目版本一致，消除版本不一致导致的兼容性问题

### MCP-02: Resource URI重复 ✅ 已修复（v8.5.0）
- **当前状态**: ✅ 已修复 — 5个重复URI已移除（27→22），测试文件已更新
- **修复内容**:
  - 移除5个重复的Resource URI定义
  - Resource URI数量从27个精简为22个（无重复）
  - 测试文件同步更新以反映URI变更
- **文件路径**: xuansto-mcp-server/src/xuansto_mcp/resources/skill_resources.py
- **影响**: Resource URI无重复，避免订阅和查询歧义

### MCP-03: 工具调用无审计日志 ✅ 已修复（v8.4.0）
- **当前状态**: ✅ 已修复 — 已实现 AuditLogger 类和 audit_logger 模块
- **修复内容**:
  - 新增 AuditLogger 类实现MCP工具调用审计记录
  - 新增 audit_logger 模块提供统一的审计日志接口
  - 可追踪所有工具调用历史
- **文件路径**: xuansto-mcp-server/src/xuansto_mcp/core/audit_logger.py
- **影响**: MCP工具调用有完整审计记录

### SKILL-01: PHASE标记与LoadPhase枚举值不对应 ✅ 已修复（8.1.0-dev）
- **当前状态**: ✅ 已修复 — PHASE_SKILL_MAP 建立了 PHASE_0→SKELETON、PHASE_1→FUNCTIONAL、PHASE_2→ENHANCED、PHASE_3→FULL 的映射
- **修复内容**: progressive_loader.py 新增 PHASE_SKILL_MAP 和 sync_from_skill_phase() 方法
- **影响**: Skill层PHASE标记与MCP层LoadPhase可正确对应

### SKILL-02: SKELETON阶段无可用命令 ✅ 已修复（v8.5.0）
- **当前状态**: ✅ 已修复 — SKELETON阶段已支持 /status、/help、/budget 基础命令
- **修复内容**:
  - COMMAND_PHASE_MAP 新增 /status、/help、/budget → SKELETON 映射
  - routes.yaml /status phase null→0，新增 /help 命令路由（phase:0）
  - SKILL.md PHASE_0 新增 SKELETON 阶段可用命令表格
- **影响**: 用户在SKELETON阶段可执行基础命令

### SKILL-03: 降级时Skill层不感知MCP层状态 ✅ 已修复（8.1.0-dev）
- **当前状态**: ✅ 已修复 — degrade_phase() 设置 degraded=True，resource_load_status 返回降级信息
- **修复内容**: progressive_loader.py 新增 degrade_phase() 方法，SkillToolHandler 可通过 resource_load_status 感知降级
- **影响**: 降级时Skill层可感知并调整行为

### API-01: API版本号三源不一致 ✅ 已修复（v8.5.0）
- **当前状态**: ✅ 已修复 — __version__ 统一为 8.5.0，MCP_API_VERSION 作为独立协议版本
- **修复内容**:
  - server.py 和 __init__.py 中 __version__ 统一更新为 8.5.0
  - MCP_API_VERSION 作为独立协议版本（与包版本解耦）
  - 三源版本号（server.py / __init__.py / pyproject.toml）现已一致
- **影响**: API版本号三源一致，消除版本混淆

### API-02: 降级脚本返回格式与MCP工具不一致 ✅ 已修复（8.1.0-dev）
- **当前状态**: ✅ 已修复 — 降级结果统一包装为JSON格式（degraded/inline_degraded/error）
- **修复内容**: degradation.py 新增 _wrap_degraded()、_wrap_inline_degraded()、_wrap_error() 方法
- **影响**: 降级脚本返回格式与MCP工具一致

### NEW-01: 降级映射不完整（14/20） ✅ 已修复（v8.5.0）
- **需求来源**: degradation.py MCPToolFallback 仅映射14个工具，constraints.yaml 声明20个MCP工具
- **当前状态**: ✅ 已修复 — 降级映射补全6个缺失项，20/20完整覆盖所有MCP工具
- **修复内容**:
  - 补全6个缺失降级映射（knowledge_inject、knowledge_precipitate、resource_subscribe、audit_query、decision_log configure、server_health negotiate_version）
  - constraints.yaml 作为降级映射权威源（tool_fallbacks 结构化配置）
  - degradation.py 从 constraints.yaml 动态加载映射，YAML读取失败回退硬编码
- **影响**: 所有20个MCP工具均有降级路径

### NEW-03: Schema验证缺失 ✅ 已修复（v8.5.0）
- **需求来源**: MCP工具定义与实际代码可能存在Schema不一致，缺乏自动化验证
- **当前状态**: ✅ 已修复 — validate_schemas.py 验证脚本已实现，5处不一致已修复
- **修复内容**:
  - 新增 validate_schemas.py 验证脚本
  - 检查 MCP 工具定义与实际代码的 Schema 一致性
  - 检查 SKILL.md 声明与实际实现的匹配度
  - 修复 5 个 Schema-代码不一致问题
  - CI 集成：schema 验证可作为 pre-commit hook 运行
- **影响**: Schema不一致可自动检测和修复

### NEW-05: COMMAND_PHASE_MAP不完整（6/32） ✅ 已修复（v8.5.0）
- **需求来源**: progressive_loader.py COMMAND_PHASE_MAP 仅映射6个命令，32个命令中26个无阶段映射
- **当前状态**: ✅ 已修复 — COMMAND_PHASE_MAP 从6个命令扩展到32个命令完整映射
- **修复内容**:
  - COMMAND_PHASE_MAP 扩展到32个命令完整映射
  - 阶段转换披露模板：phase_transition_templates 定义阶段推进时的通知格式
  - 新增 get_commands_for_phase() 和 get_phase_for_command() 查询函数
- **影响**: 所有32个命令均有明确的阶段归属

### NEW-06: 质量门禁不完整（13/54） ✅ 已修复（v8.5.0）
- **需求来源**: _shared.py QUALITY_GATES 仅定义13项，SKILL.md 声明54项质量门禁
- **当前状态**: ✅ 已修复 — 质量门禁从13项扩展到54项（_shared.py QUALITY_GATES 完整定义）
- **修复内容**:
  - QUALITY_GATES 扩展到54项完整定义
  - 新增跨阶段门禁：cross_phase_gates 检查阶段间一致性
  - 门禁分类：BLOCK（阻塞）/ WARN（警告）/ INFO（信息）三级
  - 门禁覆盖全部9个阶段 + 跨阶段检查
- **影响**: 质量门禁完整覆盖所有阶段

### NEW-07: 双SQLite数据库分裂 ✅ 已修复（v8.5.0）
- **需求来源**: knowledge.db 与 workflow.db 两个独立SQLite数据库，缺乏事务一致性保证
- **当前状态**: ✅ 已修复 — 双SQLite合并为统一 xuansto.db（22+表合并）
- **修复内容**:
  - 双SQLite数据库合并为统一 xuansto.db（22+表合并，消除 knowledge.db 与 workflow.db 分裂）
  - migration_v13 迁移脚本：合并表结构、数据迁移、索引重建
  - FTS5 全文搜索触发器：decision_fts、knowledge_fts 自动同步全文索引
  - db_engine.py 统一数据库引擎：单连接池管理、事务一致性保证、统一 xuansto.db 路径
- **文件路径**: xuansto-mcp-server/src/xuansto_mcp/core/db_engine.py
- **影响**: 数据库事务一致性保证，消除分裂问题

### NEW-08: 缺少Resource订阅机制 ✅ 已修复（v8.5.0）
- **需求来源**: MCP Resource 变更无通知机制，Agent无法感知Resource状态变更
- **当前状态**: ✅ 已修复 — resource_subscribe 工具已实现（subscribe/unsubscribe/list）
- **修复内容**:
  - 新增 resource_subscribe 工具
  - subscribe：订阅 Resource URI 变更通知
  - unsubscribe：取消订阅
  - list：列出当前所有活跃订阅
- **文件路径**: xuansto-mcp-server/src/xuansto_mcp/tools/resource_subscribe.py
- **影响**: Agent可订阅Resource变更通知

### NEW-09: 缺少审计日志查询 ✅ 已修复（v8.5.0）
- **需求来源**: AuditLogger 仅写入审计日志，无查询接口
- **当前状态**: ✅ 已修复 — audit_query 工具已实现
- **修复内容**:
  - 新增 audit_query 工具（查询审计日志）
  - 支持 tool_name、time_range、success 过滤
  - 支持分页（limit/offset）
  - 返回审计记录详情（tool_name、params_summary、latency_ms、success、timestamp）
- **文件路径**: xuansto-mcp-server/src/xuansto_mcp/tools/audit_query.py
- **影响**: 审计日志可查询和过滤

## 新增问题（来自v9.0.0重构分析）

### ARCH-02: 跨会话 Token 持久化 ✅ 已修复（v9.0.0）
- **当前状态**: ✅ 已修复 — Token 使用历史持久化到 SQLite token_budget_states 表
- **影响**: 跨会话 Token 预算数据不再丢失

### ARCH-03: Agent 定义去重 ✅ 已修复（v9.0.0）
- **当前状态**: ✅ 已修复 — Agent 定义统一为 agents/ 目录唯一源，删除 references/agent-details/ 57 个重复文件
- **影响**: Agent 定义无重复，维护负担减轻

### ARCH-07: 知识库路径统一 ✅ 已修复（v9.0.0）
- **当前状态**: ✅ 已修复 — 知识库路径统一为 MCP Server data/knowledge/，新增 KNOWLEDGE_REFERENCES_DIR
- **影响**: 知识库路径单一权威源

### ARCH-08: 会话持久化统一 ✅ 已修复（v9.0.0）
- **当前状态**: ✅ 已修复 — SQLite session_states 表为唯一权威源，文件导出可选
- **影响**: 会话持久化单一权威源

### ARCH-10: 版本号统一 ✅ 已修复（v9.0.0）
- **当前状态**: ✅ 已修复 — 版本号统一为 9.0.0，CI 版本一致性检查
- **影响**: 版本号跨组件一致

### ARCH-13: 知识库路径统一（与 ARCH-07 合并） ✅ 已修复（v9.0.0）
- **当前状态**: ✅ 已修复 — 与 ARCH-07 合并处理
- **影响**: 知识库路径统一

### ARCH-21: Token 预算动态调整 ✅ 已修复（v9.0.0）
- **当前状态**: ✅ 已修复 — 根据项目规模(small/medium/large)动态计算 Token 预算
- **影响**: Token 预算可根据项目规模自适应

### ARCH-22: 会话恢复增强 ✅ 已修复（v9.0.0）
- **当前状态**: ✅ 已修复 — 进程重启后自动恢复活跃工作流和 Token 预算
- **影响**: 进程重启后工作流和预算可自动恢复

### SKILL-01: 版本号统一 ✅ 已修复（v9.0.0）
- **当前状态**: ✅ 已修复 — 版本号统一为 9.0.0
- **影响**: Skill 版本号与 MCP Server 一致

### SKILL-03: 模型路由对齐 ✅ 已修复（v9.0.0）
- **当前状态**: ✅ 已修复 — registry.yaml 为唯一源，更新 model-routing.md
- **影响**: 模型路由配置单一权威源

### SKILL-08: SKILL.md 工具数修正 ✅ 已修复（v9.0.0）
- **当前状态**: ✅ 已修复 — SKILL.md 工具数从 20 修正为 22
- **影响**: SKILL.md 声明与实际一致

### SKILL-10: default.yaml 空段清理 ✅ 已修复（v9.0.0）
- **当前状态**: ✅ 已修复 — 清理 default.yaml 中已迁移到 constraints.yaml 的空段引用
- **影响**: 配置文件无冗余空段

### SKILL-11: 跨会话 Token 持久化 ✅ 已修复（v9.0.0）
- **当前状态**: ✅ 已修复 — Token 使用历史持久化到 SQLite token_budget_states 表
- **影响**: 跨会话 Token 预算数据不再丢失

### SKILL-14: SKILL.md 工具数修正 ✅ 已修复（v9.0.0）
- **当前状态**: ✅ 已修复 — SKILL.md 工具数从 20 修正为 22
- **影响**: SKILL.md 声明与实际一致

### DATA-10: 指标系统合并 ✅ 已修复（v9.0.0）
- **当前状态**: ✅ 已修复 — MetricsCollector 为唯一来源，移除 _TOOL_METRICS 独立字典
- **影响**: 指标数据单一权威源

### API-14: 版本协商去重 ✅ 已修复（v9.0.0）
- **当前状态**: ✅ 已修复 — 统一到 server_health.py
- **影响**: 版本协商逻辑无重复

---

## 统计摘要

| 优先级 | 总数 | 已修复 | 未修复 | 缓解 |
|--------|------|--------|--------|------|
| P0 | 2 | 2 | 0 | 0 |
| P1 | 6 | 6 | 0 | 0 |
| P2 | 2 | 2 | 0 | 0 |
| P3 | 2 | 0 | 0 | 2 |
| 新增(ARCH) | 9 | 9 | 0 | 0 |
| 新增(DB) | 3 | 3 | 0 | 0 |
| 新增(MCP) | 3 | 3 | 0 | 0 |
| 新增(SKILL) | 3 | 3 | 0 | 0 |
| 新增(API) | 2 | 2 | 0 | 0 |
| 新增(NEW-v8.5.0) | 7 | 7 | 0 | 0 |
| 新增(v9.0.0) | 16 | 16 | 0 | 0 |
| **总计** | **55** | **53** | **0** | **2** |

> 缓解项：P3-01（v1与v2重复文件，v1已归档标记）、P3-02（SKILL.md行数超限，已通过PHASE标记渐进式加载缓解）
> v8.5.0 新修复：NEW-01/03/05/06/07/08/09、DB-01(增强)、DB-02(增强)、SKILL-02、MCP-01、API-01(更新)、ARCH-01、ARCH-05(更新)、MCP-02(更新)
> v9.0.0 新修复：ARCH-02/03/07/08/10/13/21/22、SKILL-01/03/08/10/11/14、DATA-10、API-14
