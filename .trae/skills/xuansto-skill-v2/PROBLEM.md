# Xuansto Skill v2 (MCP Edition) 问题清单

> 版本：7.0.0
> 更新日期：2026-05-22
> 分析范围：SKILL.md、57个Agent定义、27个命令、15个工作流、13个MCP工具、降级脚本

---

## P0 - 阻塞性问题

### P0-01: v2降级模式不可用
- **需求来源**: SKILL.md声明"MCP工具优先→脚本降级→文件系统兜底"
- **当前状态**: MCP Server的degradation.py仅返回fallback响应，未实际调用scripts/目录下的Python脚本
- **影响**: MCP Server不可用时，所有MCP工具调用将失败，系统完全无法运行
- **修复方案**: 实现degradation.py到scripts/目录下Python脚本的实际调用链

### P0-02: v2缺少references/完整参考文档
- **需求来源**: v1有72+参考文件，v2仅2个
- **当前状态**: v2 references/仅包含mcp-tools.md和workflow-phases.md
- **影响**: Agent和命令执行时无法获取详细参考（如quality-gates.md、agent-registry.md、knowledge-workflow-details.md等）
- **修复方案**: 从v1迁移关键参考文件到v2 references/，或通过MCP Resource提供

## P1 - 高优先级问题

### P1-01: MCP Server版本与Skill版本不一致
- **当前状态**: MCP Server v3.5.0 vs Skill v7.0.0
- **影响**: 用户难以判断版本兼容性
- **修复方案**: 在SKILL.md和MCP Server README中互相声明兼容版本

### P1-02: server_health工具未在v2 mcp-tools.md中列出
- **当前状态**: MCP Server实现了server_health工具，但v2 references/mcp-tools.md未包含
- **影响**: 用户无法了解server_health工具的参数和返回值
- **修复方案**: 在mcp-tools.md中补充server_health工具文档

### P1-03: knowledge_search缺少inject/precipitate action文档
- **当前状态**: v1 SKILL.md声明knowledge_search支持retrieve/inject/precipitate三个action，v2 mcp-tools.md仅文档了retrieve
- **影响**: 知识注入和经验沉淀功能无法使用
- **修复方案**: 补充inject和precipitate action的参数和返回值文档

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
- **当前状态**: 增强后的SKILL.md可能接近或超过skill-creator建议的500行上限
- **影响**: Token消耗增加
- **修复方案**: 将详细步骤外移到references/，SKILL.md保留概要和索引

---

## 统计摘要

| 优先级 | 总数 | 已修复 | 未修复 |
|--------|------|--------|--------|
| P0 | 2 | 0 | 2 |
| P1 | 3 | 0 | 3 |
| P2 | 2 | 0 | 2 |
| P3 | 2 | 0 | 2 |
| **总计** | **9** | **0** | **9** |
