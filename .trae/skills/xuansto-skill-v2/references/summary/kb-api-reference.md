# 知识库API接口文档

## Core Points
- 定义Xuansto Skill知识库服务的REST API和MCP Tool接口规范
- REST API端点：知识条目CRUD、语义检索、知识推荐、批量操作
- MCP Tool接口：knowledge_search、knowledge_add、knowledge_update、knowledge_delete
- 错误码定义：4xx客户端错误、5xx服务端错误、详细错误消息
- 认证与限流：Bearer Token认证、API限流(100次/分钟)

## Applicable Scenarios
- Knowledge Manager Agent通过API管理知识库
- Agent通过MCP Tool接口检索和推荐知识
- 外部工具集成知识库服务
