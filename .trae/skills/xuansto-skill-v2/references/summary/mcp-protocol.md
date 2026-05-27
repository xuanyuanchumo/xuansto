# MCP协议参考文档

## Core Points
- MCP(Model Context Protocol)是LLM与外部工具交互的标准协议，定义服务器实现、工具注册、资源管理和提示模板
- 协议架构：客户端-服务器模型，支持HTTP/SSE传输，JSON-RPC 2.0消息格式
- 核心概念：Tools(可调用函数)、Resources(只读数据)、Prompts(提示模板)、Sampling(模型采样)
- 服务器实现：FastMCP(Python)/MCP SDK(TypeScript)，支持工具注册和资源暴露
- 与xuansto集成：xuansto-mcp-server提供20个MCP原子工具驱动9阶段开发流程

## Applicable Scenarios
- 理解MCP协议规范和核心概念
- 开发和集成MCP服务器和工具
- 设计MCP资源管理和提示模板
