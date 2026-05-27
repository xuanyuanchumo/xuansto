# MCP集成策略

## Core Points
- 定义xuansto-skill v2与xuansto-mcp-server的完整集成策略
- 上下文窗口预算管理：按阶段分配Token预算，骨架2K→功能5K→增强10K→完整20K
- MCP工具懒加载策略：按需加载工具定义，未使用工具不占用上下文
- 三级降级策略：L1(MCP可用)→L2(CLI替代)→L3(脚本降级)
- 工具-脚本完整映射表：每个MCP工具有对应的CLI命令和Python脚本替代方案

## Applicable Scenarios
- 配置MCP服务器集成和工具加载策略
- 实现MCP工具降级和CLI替代方案
- 管理上下文窗口Token预算
