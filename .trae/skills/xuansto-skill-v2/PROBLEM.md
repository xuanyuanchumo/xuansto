# Xuansto Skill v2 (MCP Edition) 问题清单

> 版本：8.0.0
> 更新日期：2026-05-24
> 分析范围：SKILL.md、57个Agent定义、31个命令、17个MCP工具、降级脚本、渐进式加载

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

## P2 - 中等优先级问题

### P2-01: v2缺少评估配置文件
- **当前状态**: v1有evals/目录，v2无
- **影响**: 无法进行技能评估
- **修复方案**: 从v1迁移evals/目录

### P2-02: v2缺少CHANGELOG.md
- **当前状态**: v1有完整CHANGELOG，v2无
- **影响**: 无法追踪v2的版本变更
- **修复方案**: 创建v2专用CHANGELOG.md

## P3 - 低优先级问题

### P3-01: v1与v2存在重复文件
- **当前状态**: agents/、commands/、workflows/等目录在v1和v2中同时存在
- **影响**: 维护成本增加，可能出现不一致
- **修复方案**: 确立v2为唯一维护版本，v1标记为archived

### P3-02: v2 SKILL.md行数可能超过500行
- **当前状态**: 增强后的SKILL.md已添加PHASE标记实现渐进式加载，实际Token消耗由Phase控制
- **影响**: 通过渐进式加载机制已缓解，Phase 0仅加载≤2K Token
- **修复方案**: 已通过PHASE标记实现渐进式加载，SKILL.md按Phase分段加载

---

## 统计摘要

| 优先级 | 总数 | 已修复 | 未修复 |
|--------|------|--------|--------|
| P0 | 2 | 2 | 0 |
| P1 | 3 | 3 | 0 |
| P2 | 2 | 0 | 2 |
| P3 | 2 | 0 | 2 |
| **总计** | **9** | **5** | **4** |
