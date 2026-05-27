# MCP工具详细参考

## Core Points
- 20个MCP原子工具驱动9阶段开发流程，按需加载不预占用上下文
- 核心工具：skill_analyze(项目分析)、knowledge_search(知识检索)、quality_gate_check(门禁检查)、security_scan(安全扫描)
- 工作流工具：workflow_dispatch(工作流调度)、session_manage(会话管理)、agent_status(Agent状态)
- 辅助工具：spec_drift_detect(规格漂移检测)、code_simplify(代码简化)、resource_load_status(资源加载状态)

## Applicable Scenarios
- Agent通过MCP工具执行开发任务
- 配置MCP工具注册和懒加载策略
- 实现工具调用的降级和替代方案
