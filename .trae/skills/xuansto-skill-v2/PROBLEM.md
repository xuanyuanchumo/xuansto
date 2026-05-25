# Xuansto Skill v2 (MCP Edition) 问题清单

> 版本：8.1.0-dev
> 更新日期：2026-05-25
> 分析范围：SKILL.md、57个Agent定义、31个命令、26个MCP工具、降级脚本、渐进式加载、模块化重构

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

### P3-01: v1与v2存在重复文件
- **当前状态**: agents/、commands/、workflows/等目录在v1和v2中同时存在
- **影响**: 维护成本增加，可能出现不一致
- **修复方案**: 确立v2为唯一维护版本，v1标记为archived（计划在v8.5.0执行）

### P3-02: v2 SKILL.md行数可能超过500行
- **当前状态**: 增强后的SKILL.md已添加PHASE标记实现渐进式加载，实际Token消耗由Phase控制
- **影响**: 通过渐进式加载机制已缓解，Phase 0仅加载≤2K Token
- **修复方案**: 已通过PHASE标记实现渐进式加载，SKILL.md按Phase分段加载

## 新增问题（来自8.1.0-dev重构分析）

### ARCH-05: MCP Server未暴露Resource（优先级：中）
- **当前状态**: 26个MCP工具全部为Tool，无Resource暴露
- **影响**: Agent无法通过URI模式订阅状态变更
- **修复方案**: 新增3个Resource（xuansto://agents/{name}、xuansto://knowledge/stats、xuansto://loading/status），计划在v8.2.0实现

### ARCH-06: 缺少Agent持久化机制（优先级：低）
- **当前状态**: Agent实例仅内存存储，重启丢失
- **影响**: 长时间工作流中断后无法恢复Agent状态
- **修复方案**: 将Agent状态持久化到SQLite，计划在v8.4.0实现

### ARCH-07: 工作流状态仅内存存储（优先级：低）
- **当前状态**: 工作流状态存储在SkillToolHandler._workflows字典中
- **影响**: MCP Server重启后工作流状态丢失
- **修复方案**: 工作流状态持久化到SQLite，计划在v8.4.0实现

### ARCH-08: Token预算与加载阶段未关联（优先级：低）
- **当前状态**: Token预算独立于加载阶段管理
- **影响**: 无法根据加载阶段自动调整Token分配
- **修复方案**: 建立Token预算与LoadPhase的关联，计划在v8.4.0实现

### ARCH-09: Hook执行无超时保护（优先级：低）
- **当前状态**: Hook执行无超时限制
- **影响**: 恶意或错误Hook可能无限阻塞
- **修复方案**: 为Hook执行添加超时控制，计划在v8.4.0实现

### ARCH-10: 配置变更需重启MCP Server（优先级：低）
- **当前状态**: constraints.yaml和.skill-config.yaml变更需重启生效
- **影响**: 无法热更新配置
- **修复方案**: 实现配置热更新机制，计划在v8.4.0实现

### ARCH-11: 错误处理不统一（优先级：中）
- **当前状态**: 部分工具返回字符串而非JSON
- **影响**: 调用方需处理多种返回格式
- **修复方案**: 统一所有工具返回JSON格式，计划在v8.3.0实现

### ARCH-12: 缺少API版本协商机制（优先级：低）
- **当前状态**: 无API版本协商
- **影响**: 客户端与服务端版本不匹配时无法优雅降级
- **修复方案**: 实现API版本协商，计划在v8.4.0实现

### DB-01: 决策记录双写一致性风险（优先级：中）
- **当前状态**: 决策同时写入SQLite和文件系统
- **影响**: 双写无事务保证，可能出现不一致
- **修复方案**: 实现双写事务保证，计划在v8.3.0实现

### DB-02: ChromaDB与SQLite双写无事务保证（优先级：中）
- **当前状态**: 先写SQLite标记pending，再写ChromaDB，成功后标记ready
- **影响**: ChromaDB写入失败时SQLite标记仍为pending
- **修复方案**: 实现对账机制和自动重试，计划在v8.3.0实现

### DB-03: 知识条目版本历史无清理策略（优先级：低）
- **当前状态**: 版本历史无限增长
- **影响**: 数据库膨胀
- **修复方案**: 添加版本历史清理策略，计划在v8.5.0实现

### MCP-02: 缺少Resource暴露（优先级：中）
- **当前状态**: 同ARCH-05
- **修复方案**: 同ARCH-05

### MCP-03: 工具调用无审计日志（优先级：中）
- **当前状态**: MCP工具调用无审计记录
- **影响**: 无法追踪工具调用历史
- **修复方案**: 添加审计日志，计划在v8.3.0实现

### SKILL-01: PHASE标记与LoadPhase枚举值不对应 ✅ 已修复（8.1.0-dev）
- **当前状态**: ✅ 已修复 — PHASE_SKILL_MAP 建立了 PHASE_0→SKELETON、PHASE_1→FUNCTIONAL、PHASE_2→ENHANCED、PHASE_3→FULL 的映射
- **修复内容**: progressive_loader.py 新增 PHASE_SKILL_MAP 和 sync_from_skill_phase() 方法
- **影响**: Skill层PHASE标记与MCP层LoadPhase可正确对应

### SKILL-02: SKELETON阶段无可用命令（优先级：低）
- **当前状态**: SKELETON阶段仅加载骨架信息，无可用命令
- **影响**: 用户在SKELETON阶段无法执行任何操作
- **修复方案**: 为SKELETON阶段添加基础命令（/status、/help），计划在v8.2.0实现

### SKILL-03: 降级时Skill层不感知MCP层状态 ✅ 已修复（8.1.0-dev）
- **当前状态**: ✅ 已修复 — degrade_phase() 设置 degraded=True，resource_load_status 返回降级信息
- **修复内容**: progressive_loader.py 新增 degrade_phase() 方法，SkillToolHandler 可通过 resource_load_status 感知降级
- **影响**: 降级时Skill层可感知并调整行为

### API-01: HTTP API与MCP stdio两套接口无统一Schema（优先级：中）
- **当前状态**: HTTP API和MCP stdio接口返回格式不同
- **影响**: 调用方需适配两套接口
- **修复方案**: 统一Schema，计划在v8.3.0实现

### API-02: 降级脚本返回格式与MCP工具不一致 ✅ 已修复（8.1.0-dev）
- **当前状态**: ✅ 已修复 — 降级结果统一包装为JSON格式（degraded/inline_degraded/error）
- **修复内容**: degradation.py 新增 _wrap_degraded()、_wrap_inline_degraded()、_wrap_error() 方法
- **影响**: 降级脚本返回格式与MCP工具一致

---

## 统计摘要

| 优先级 | 总数 | 已修复 | 未修复 |
|--------|------|--------|--------|
| P0 | 2 | 2 | 0 |
| P1 | 6 | 6 | 0 |
| P2 | 2 | 2 | 0 |
| P3 | 2 | 0 | 2 |
| 新增(ARCH) | 8 | 0 | 8 |
| 新增(DB) | 3 | 0 | 3 |
| 新增(MCP) | 2 | 0 | 2 |
| 新增(SKILL) | 3 | 2 | 1 |
| 新增(API) | 2 | 1 | 1 |
| **总计** | **30** | **13** | **17** |
