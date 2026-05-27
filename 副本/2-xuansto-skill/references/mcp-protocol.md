# MCP协议参考文档
> 版本: 1.9.0 | 更新日期: 2026-04-28 | 编码: UTF-8 | 行尾: LF

## 目录

- [协议概述](#协议概述)
  - [什么是MCP协议](#什么是mcp协议)
  - [核心设计理念](#核心设计理念)
  - [协议架构](#协议架构)
  - [协议版本](#协议版本)
  - [核心概念](#核心概念)
- [服务器实现](#服务器实现)
  - [基础服务器结构](#基础服务器结构)
  - [工具注册](#工具注册)
  - [资源管理](#资源管理)
  - [提示词模板](#提示词模板)
  - [传输层配置](#传输层配置)
- [客户端集成](#客户端集成)
  - [客户端连接](#客户端连接)
  - [工具调用流程](#工具调用流程)
  - [错误处理](#错误处理)
  - [资源访问](#资源访问)
- [工具定义规范](#工具定义规范)
  - [输入Schema定义](#输入schema定义)
  - [输出格式规范](#输出格式规范)
  - [工具元数据](#工具元数据)
  - [工具权限控制](#工具权限控制)
- [最佳实践](#最佳实践)
  - [工具设计原则](#工具设计原则)
  - [性能优化](#性能优化)
  - [安全考虑](#安全考虑)
- [配置示例](#配置示例)
  - [Claude Desktop配置](#claude-desktop配置)
  - [环境变量配置](#环境变量配置)
- [桌面应用 MCP 集成指南](#桌面应用-mcp-集成指南)
  - [Electron 桌面应用集成](#electron-桌面应用集成)
  - [Tauri 桌面应用集成](#tauri-桌面应用集成)
- [MCP 与 A2A 协同使用场景](#mcp-与-a2a-协同使用场景)
- [参考资源](#参考资源)

## 协议概述

### 什么是MCP协议

MCP（Model Context Protocol）是一种标准化的协议，用于在AI模型与外部工具、数据源之间建立通信桥梁。它定义了一套统一的接口规范，使得AI模型能够安全、可控地访问和操作外部资源。

### 核心设计理念

1. **标准化接口**：提供统一的工具调用规范
2. **安全可控**：内置权限控制和审计机制
3. **可扩展性**：支持自定义工具和资源类型
4. **语言无关**：支持多种编程语言实现
5. **类型安全**：基于JSON Schema的强类型定义

### 协议架构

```
┌─────────────────────────────────────────────────────┐
│                    AI 模型/客户端                     │
└─────────────────────────┬───────────────────────────┘
                          │ MCP Protocol
┌─────────────────────────┴───────────────────────────┐
│                    MCP 客户端层                       │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐    │
│  │ 连接管理    │ │ 消息序列化  │ │ 错误处理    │    │
│  └─────────────┘ └─────────────┘ └─────────────┘    │
└─────────────────────────┬───────────────────────────┘
                          │ Transport Layer
┌─────────────────────────┴───────────────────────────┐
│                    MCP 服务器层                       │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐    │
│  │ 工具注册    │ │ 资源管理    │ │ 提示词模板  │    │
│  └─────────────┘ └─────────────┘ └─────────────┘    │
└─────────────────────────┬───────────────────────────┘
                          │
┌─────────────────────────┴───────────────────────────┐
│                    外部资源/服务                      │
│  文件系统 │ 数据库 │ API服务 │ 命令行工具 │ ...      │
└─────────────────────────────────────────────────────┘
```

### 协议版本

| 版本 | 发布日期 | 主要特性 |
|------|----------|----------|
| 2024-11-05 | 2024-11 | 初始版本，基础工具调用 |
| 2025-03-26 | 2025-03 | 增强资源管理、流式响应 |

### 核心概念

#### 工具 (Tools)

工具是MCP服务器提供的可执行功能，AI模型可以调用这些工具来执行特定操作。

#### 资源 (Resources)

资源是MCP服务器暴露的数据源，AI模型可以读取这些资源的内容。

#### 提示词 (Prompts)

提示词是预定义的模板，可以帮助用户快速构建常用的交互模式。

## 服务器实现

### 基础服务器结构

#### Python实现 (FastMCP)

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("my-server")

@mcp.tool()
def calculate(expression: str) -> float:
    """计算数学表达式
    
    Args:
        expression: 数学表达式字符串
        
    Returns:
        计算结果
    """
    return eval(expression)

@mcp.resource("config://settings")
def get_config() -> str:
    """获取配置信息"""
    return '{"theme": "dark", "language": "zh-CN"}'

if __name__ == "__main__":
    mcp.run()
```

#### TypeScript/Node.js实现

```typescript
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";

const server = new Server(
  { name: "my-server", version: "1.0.0" },
  { capabilities: { tools: {}, resources: {} } }
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "calculate",
      description: "计算数学表达式",
      inputSchema: {
        type: "object",
        properties: {
          expression: {
            type: "string",
            description: "数学表达式字符串"
          }
        },
        required: ["expression"]
      }
    }
  ]
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  if (request.params.name === "calculate") {
    const result = eval(request.params.arguments.expression);
    return { content: [{ type: "text", text: String(result) }] };
  }
  throw new Error("Unknown tool");
});

const transport = new StdioServerTransport();
await server.connect(transport);
```

### 工具注册

#### 工具定义格式

```json
{
  "name": "read_file",
  "description": "读取文件内容",
  "inputSchema": {
    "type": "object",
    "properties": {
      "path": {
        "type": "string",
        "description": "文件路径"
      },
      "encoding": {
        "type": "string",
        "default": "utf-8",
        "description": "文件编码"
      }
    },
    "required": ["path"]
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "content": { "type": "string" },
      "size": { "type": "number" },
      "mimeType": { "type": "string" }
    }
  }
}
```

#### 工具类型

| 类型 | 说明 | 示例 |
|------|------|------|
| 计算型 | 执行计算并返回结果 | 数学运算、数据分析 |
| 操作型 | 执行操作并返回状态 | 文件操作、API调用 |
| 查询型 | 查询数据并返回结果 | 数据库查询、搜索 |
| 流式型 | 返回流式数据 | 日志监控、实时数据 |

#### 工具实现示例

```python
from mcp.server.fastmcp import FastMCP
from typing import Optional, List
import os

mcp = FastMCP("file-server")

@mcp.tool()
def read_file(path: str, encoding: str = "utf-8") -> dict:
    """读取文件内容
    
    Args:
        path: 文件绝对路径
        encoding: 文件编码，默认utf-8
        
    Returns:
        包含文件内容和元数据的字典
        
    Raises:
        FileNotFoundError: 文件不存在
        PermissionError: 无读取权限
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"文件不存在: {path}")
    
    with open(path, 'r', encoding=encoding) as f:
        content = f.read()
    
    return {
        "content": content,
        "size": os.path.getsize(path),
        "mimeType": "text/plain"
    }

@mcp.tool()
def list_directory(path: str, pattern: str = "*") -> List[dict]:
    """列出目录内容
    
    Args:
        path: 目录路径
        pattern: 文件匹配模式，默认匹配所有
        
    Returns:
        文件和目录信息列表
    """
    import glob
    
    items = []
    for item in glob.glob(os.path.join(path, pattern)):
        items.append({
            "name": os.path.basename(item),
            "path": item,
            "type": "directory" if os.path.isdir(item) else "file",
            "size": os.path.getsize(item) if os.path.isfile(item) else None
        })
    
    return items

@mcp.tool()
async def search_files(root: str, query: str) -> List[str]:
    """异步搜索文件
    
    Args:
        root: 搜索根目录
        query: 搜索关键词
        
    Returns:
        匹配的文件路径列表
    """
    import asyncio
    
    results = []
    
    async def search_dir(directory):
        for entry in os.scandir(directory):
            if entry.is_file() and query.lower() in entry.name.lower():
                results.append(entry.path)
            elif entry.is_dir():
                await search_dir(entry.path)
    
    await search_dir(root)
    return results
```

### 资源管理

#### 资源定义

```python
@mcp.resource("file://{path}")
def read_file_resource(path: str) -> str:
    """动态资源：读取任意文件"""
    with open(path, 'r') as f:
        return f.read()

@mcp.resource("config://app")
def get_app_config() -> str:
    """静态资源：应用配置"""
    return json.dumps({
        "version": "1.0.0",
        "environment": "production"
    })

@mcp.resource("database://tables")
def list_tables() -> str:
    """资源列表：数据库表"""
    return json.dumps(["users", "orders", "products"])
```

#### 资源模板

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("resource-server")

@mcp.resource("user://{user_id}/profile")
def get_user_profile(user_id: str) -> str:
    """获取用户资料"""
    return json.dumps({
        "id": user_id,
        "name": f"User {user_id}",
        "email": f"user{user_id}@example.com"
    })

@mcp.resource("logs://{date}")
def get_logs(date: str) -> str:
    """获取指定日期的日志"""
    log_path = f"/var/log/app/{date}.log"
    with open(log_path, 'r') as f:
        return f.read()
```

### 提示词模板

```python
@mcp.prompt()
def code_review_prompt(code: str) -> str:
    """代码审查提示词模板"""
    return f"""请对以下代码进行审查：

```
{code}
```

请从以下方面进行评估：
1. 代码质量和可读性
2. 潜在的bug和问题
3. 性能优化建议
4. 安全性考虑
5. 最佳实践建议
"""

@mcp.prompt()
def explain_code_prompt(code: str, language: str = "python") -> str:
    """代码解释提示词模板"""
    return f"""请解释以下{language}代码的功能：

```{language}
{code}
```

请包括：
1. 整体功能描述
2. 关键逻辑解释
3. 输入输出说明
4. 使用示例
"""
```

### 传输层配置

#### Stdio传输

```python
mcp.run(transport="stdio")
```

#### HTTP传输

```python
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Route

sse = SseServerTransport("/messages")

async def handle_sse(request):
    async with sse.connect_sse(request) as reader, writer:
        await mcp.run(reader, writer)

app = Starlette(routes=[
    Route("/sse", endpoint=handle_sse),
    Route("/messages", endpoint=sse.handle_post_message)
])
```

## 客户端集成

### 客户端连接

#### Python客户端

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    server_params = StdioServerParameters(
        command="python",
        args=["server.py"],
        env=None
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            tools = await session.list_tools()
            print(f"可用工具: {[t.name for t in tools.tools]}")
            
            result = await session.call_tool(
                "read_file",
                arguments={"path": "/etc/hosts"}
            )
            print(f"结果: {result}")
```

#### TypeScript客户端

```typescript
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

const transport = new StdioClientTransport({
  command: "node",
  args: ["server.js"]
});

const client = new Client(
  { name: "my-client", version: "1.0.0" },
  { capabilities: {} }
);

await client.connect(transport);

const tools = await client.listTools();
console.log("可用工具:", tools.tools.map(t => t.name));

const result = await client.callTool({
  name: "read_file",
  arguments: { path: "/etc/hosts" }
});
console.log("结果:", result);
```

### 工具调用流程

```
┌─────────┐     ┌─────────────┐     ┌─────────────┐
│ Client  │     │ MCP Server  │     │ Tool Impl   │
└────┬────┘     └──────┬──────┘     └──────┬──────┘
     │                 │                   │
     │ 1. Initialize   │                   │
     │────────────────>│                   │
     │                 │                   │
     │ 2. List Tools   │                   │
     │────────────────>│                   │
     │                 │                   │
     │ 3. Tool List    │                   │
     │<────────────────│                   │
     │                 │                   │
     │ 4. Call Tool    │                   │
     │────────────────>│                   │
     │                 │ 5. Execute        │
     │                 │──────────────────>│
     │                 │                   │
     │                 │ 6. Result         │
     │                 │<──────────────────│
     │                 │                   │
     │ 7. Tool Result  │                   │
     │<────────────────│                   │
     │                 │                   │
```

### 错误处理

```python
from mcp import McpError

try:
    result = await session.call_tool(
        "read_file",
        arguments={"path": "/nonexistent"}
    )
except McpError as e:
    print(f"错误代码: {e.code}")
    print(f"错误消息: {e.message}")
    print(f"错误数据: {e.data}")
```

### 资源访问

```python
async def access_resources(session):
    resources = await session.list_resources()
    
    for resource in resources.resources:
        print(f"URI: {resource.uri}")
        print(f"名称: {resource.name}")
        print(f"MIME类型: {resource.mimeType}")
    
    content = await session.read_resource("config://app")
    print(f"资源内容: {content}")
```

## 工具定义规范

### 输入Schema定义

```json
{
  "type": "object",
  "properties": {
    "path": {
      "type": "string",
      "description": "文件路径",
      "pattern": "^/[a-zA-Z0-9/_-]+$"
    },
    "options": {
      "type": "object",
      "properties": {
        "encoding": {
          "type": "string",
          "enum": ["utf-8", "gbk", "latin-1"],
          "default": "utf-8"
        },
        "lines": {
          "type": "object",
          "properties": {
            "start": { "type": "integer", "minimum": 1 },
            "end": { "type": "integer" }
          }
        }
      }
    }
  },
  "required": ["path"],
  "additionalProperties": false
}
```

### 输出格式规范

#### 文本输出

```json
{
  "content": [
    {
      "type": "text",
      "text": "文件内容..."
    }
  ]
}
```

#### 图像输出

```json
{
  "content": [
    {
      "type": "image",
      "data": "base64-encoded-image-data",
      "mimeType": "image/png"
    }
  ]
}
```

#### 资源引用

```json
{
  "content": [
    {
      "type": "resource",
      "resource": {
        "uri": "file:///path/to/file.txt",
        "mimeType": "text/plain"
      }
    }
  ]
}
```

#### 嵌入资源

```json
{
  "content": [
    {
      "type": "text",
      "text": "以下是文件内容："
    },
    {
      "type": "resource",
      "resource": {
        "uri": "file:///example.txt",
        "text": "文件的实际内容..."
      }
    }
  ]
}
```

### 工具元数据

```python
@mcp.tool(
    name="advanced_search",
    description="高级文件搜索工具",
    tags=["search", "file", "async"],
    timeout=30000,
    rate_limit={"requests": 100, "window": 60}
)
async def advanced_search(
    query: str,
    paths: List[str],
    options: Optional[dict] = None
) -> dict:
    """执行高级文件搜索"""
    pass
```

### 工具权限控制

```python
from mcp.server.fastmcp import FastMCP
from mcp.types import Tool, ToolAnnotations

mcp = FastMCP("secure-server")

@mcp.tool(
    annotations=ToolAnnotations(
        title="敏感操作",
        read_only_hint=False,
        destructive_hint=True,
        idempotent_hint=False,
        open_world_hint=True
    )
)
def delete_file(path: str) -> dict:
    """删除文件（需要确认）"""
    import os
    os.remove(path)
    return {"status": "deleted", "path": path}
```

## 最佳实践

### 工具设计原则

1. **单一职责**：每个工具只做一件事
2. **明确命名**：使用动词+名词的命名方式
3. **完整文档**：提供详细的描述和参数说明
4. **类型安全**：使用JSON Schema进行类型验证
5. **错误处理**：提供清晰的错误信息

### 性能优化

1. **异步实现**：使用async/await处理IO密集型操作
2. **批量处理**：支持批量操作减少调用次数
3. **缓存机制**：对频繁访问的数据进行缓存
4. **流式响应**：大数据量使用流式传输

### 安全考虑

1. **输入验证**：严格验证所有输入参数
2. **路径限制**：限制文件访问范围
3. **权限检查**：执行操作前检查权限
4. **审计日志**：记录所有工具调用

## 配置示例

### Claude Desktop配置

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/path/to/allowed/dir"
      ]
    },
    "database": {
      "command": "python",
      "args": ["-m", "mcp_server_db"],
      "env": {
        "DATABASE_URL": "postgresql://localhost/mydb"
      }
    }
  }
}
```

### 环境变量配置

```bash
MCP_SERVER_NAME=my-server
MCP_SERVER_VERSION=1.0.0
MCP_LOG_LEVEL=info
MCP_TIMEOUT=30000
```

## 集成示例

### Python FastMCP完整项目集成

```python
import os
import json
import logging
from typing import Optional
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)
mcp = FastMCP("dev-tools-server", log_level="INFO")

@mcp.tool()
def search_code(query: str, directory: str = ".", file_pattern: str = "*.py") -> list[dict]:
    """在指定目录中搜索代码

    Args:
        query: 搜索关键词
        directory: 搜索根目录，默认当前目录
        file_pattern: 文件匹配模式，默认*.py

    Returns:
        匹配结果列表，每项包含文件路径、行号和匹配行内容
    """
    import glob
    results = []
    for filepath in glob.glob(
        os.path.join(directory, "**", file_pattern), recursive=True
    ):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                for lineno, line in enumerate(f, 1):
                    if query.lower() in line.lower():
                        results.append({
                            "file": filepath,
                            "line": lineno,
                            "content": line.strip(),
                        })
        except (UnicodeDecodeError, PermissionError):
            continue
    return results[:50]

@mcp.tool()
async def run_command(cmd: str, cwd: Optional[str] = None, timeout: int = 30) -> dict:
    """执行shell命令并返回结果

    Args:
        cmd: 要执行的命令
        cwd: 工作目录
        timeout: 超时秒数，默认30

    Returns:
        包含exit_code、stdout、stderr的字典
    """
    import asyncio
    try:
        proc = await asyncio.create_subprocess_shell(
            cmd, cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(), timeout=timeout
        )
        return {
            "exit_code": proc.returncode,
            "stdout": stdout.decode("utf-8", errors="replace"),
            "stderr": stderr.decode("utf-8", errors="replace"),
        }
    except asyncio.TimeoutError:
        proc.kill()
        return {"exit_code": -1, "stdout": "", "stderr": f"命令超时({timeout}s)"}

@mcp.resource("project://config")
def get_project_config() -> str:
    """获取项目配置信息"""
    return json.dumps({
        "name": "dev-tools-server",
        "version": "1.0.0",
        "tools": ["search_code", "run_command"],
    })

if __name__ == "__main__":
    mcp.run()
```

## 最佳实践

1. **工具粒度控制**：每个工具只做一件事，避免"瑞士军刀"式设计；复杂操作拆分为多个可组合的原子工具
2. **Schema严格定义**：inputSchema必须声明required字段和类型约束，使用additionalProperties:false防止未知参数注入
3. **错误信息可操作**：工具异常应返回具体错误原因和修复建议，而非笼统的"操作失败"
4. **资源URI规范化**：使用`scheme://category/item`格式，如`file://src/main.py`、`db://tables/users`，保持一致性
5. **传输层选择**：本地集成用stdio（低延迟），远程服务用SSE/StreamableHTTP（支持跨网络），按场景选择
6. **超时与熔断**：所有工具调用设置超时上限，IO密集型操作使用async实现，长时间任务考虑流式响应
7. **安全边界**：文件操作限制在允许目录内，命令执行禁用危险命令，敏感操作使用ToolAnnotations标记destructive_hint
8. **日志与可观测性**：启用log_level记录工具调用链路，生产环境使用INFO级别，调试时使用DEBUG级别

## 桌面应用 MCP 集成指南

### Electron 桌面应用集成

#### Electron 桌面应用 MCP 集成

在 Electron 应用中集成 MCP 服务器，需要考虑主进程/渲染进程隔离和 IPC 通信。

**架构设计**：
- MCP 服务器运行在 Electron 主进程中
- 渲染进程通过 preload 脚本暴露的 API 与 MCP 通信
- 使用 contextIsolation 隔离渲染进程

**实现步骤**：

1. 在主进程中创建 MCP 服务器：
```typescript
// main.ts
import { app, BrowserWindow, ipcMain } from 'electron';
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { ListToolsRequestSchema, CallToolRequestSchema } from '@modelcontextprotocol/sdk/types.js';

const mcpServer = new Server(
  { name: 'electron-mcp-server', version: '1.0.0' },
  { capabilities: { tools: {} } }
);

mcpServer.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: 'get-system-info',
      description: '获取系统信息',
      inputSchema: { type: 'object', properties: {} }
    }
  ]
}));

mcpServer.setRequestHandler(CallToolRequestSchema, async (request) => {
  if (request.params.name === 'get-system-info') {
    return {
      content: [{
        type: 'text',
        text: JSON.stringify({
          platform: process.platform,
          arch: process.arch,
          electronVersion: process.versions.electron,
        })
      }]
    };
  }
  throw new Error('Unknown tool');
});

// 通过 IPC 桥接 MCP 调用
ipcMain.handle('mcp-call', async (_event, toolName: string, args: any) => {
  const result = await mcpServer.callTool({ name: toolName, arguments: args });
  return result;
});
```

2. 在 preload 脚本中暴露 MCP API：
```typescript
// preload.ts
import { contextBridge, ipcRenderer } from 'electron';

contextBridge.exposeInMainWorld('mcp', {
  callTool: (toolName: string, args: any) => ipcRenderer.invoke('mcp-call', toolName, args),
});
```

3. 安全注意事项：
- 启用 contextIsolation 和 sandbox
- 禁用 nodeIntegration
- MCP 工具调用必须通过 IPC 桥接
- 限制可调用的 MCP 工具白名单

### Tauri 桌面应用集成

#### Tauri 桌面应用 MCP 集成

在 Tauri 应用中集成 MCP 服务器，利用 Tauri 的 Rust 后端和命令系统。

**架构设计**：
- MCP 服务器逻辑在 Rust 后端实现
- 前端通过 Tauri invoke 命令调用 MCP 工具
- 使用 Tauri 的权限系统控制 MCP 工具访问

**实现步骤**：

1. 在 Rust 后端实现 MCP 命令：
```rust
// src-tauri/src/mcp.rs
use tauri::command;
use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize)]
struct SystemInfo {
    platform: String,
    arch: String,
    version: String,
}

#[command]
async fn mcp_get_system_info() -> Result<SystemInfo, String> {
    Ok(SystemInfo {
        platform: std::env::consts::OS.to_string(),
        arch: std::env::consts::ARCH.to_string(),
        version: env!("CARGO_PKG_VERSION").to_string(),
    })
}

// 注册命令到 Tauri 应用
// 在 main.rs 中:
// .invoke_handler(tauri::generate_handler![mcp_get_system_info])
```

2. 在前端调用 MCP 工具：
```typescript
// 前端调用
import { invoke } from '@tauri-apps/api/core';

async function callMcpTool(toolName: string, args?: any) {
  return await invoke(`mcp_${toolName}`, args);
}
```

3. 安全注意事项：
- 在 tauri.conf.json 的 allowlist 中限制可调用的命令
- 使用 Tauri 的 scope 系统限制文件系统访问
- MCP 工具调用需通过 Tauri 权限验证

## MCP 与 A2A 协同使用场景

MCP 和 A2A 协议在 Xuansto Skill 中互补使用：

**场景1：工具调用（MCP）+ Agent协作（A2A）**
- Agent 通过 A2A 协议发现并协商任务分工
- 具体工具调用通过 MCP 协议执行（如文件操作、数据库查询、API调用）
- A2A 负责"谁做什么"，MCP 负责"怎么做"

**场景2：桌面应用中的双层通信**
- Electron/Tauri 内部组件间通过 MCP 通信（工具调用）
- 跨应用/跨服务的 Agent 间通过 A2A 通信（任务协调）
- 例如：桌面端 Agent 通过 A2A 请求云端 Agent 分析数据，云端 Agent 通过 MCP 调用数据库工具

**场景3：安全边界**
- MCP 工具调用受沙箱和权限控制（单Agent内部）
- A2A 通信受认证和加密保护（Agent间通信）
- 两者共同构成完整的安全防线

**协议选择决策矩阵**：

| 场景 | 使用MCP | 使用A2A |
|------|---------|---------|
| 单Agent调用工具 | ✅ | ❌ |
| 多Agent任务分工 | ❌ | ✅ |
| 桌面应用内部通信 | ✅ | ❌ |
| 跨应用Agent协作 | ❌ | ✅ |
| 文件/数据库操作 | ✅ | ❌ |
| 任务状态同步 | ❌ | ✅ |
| 安全扫描执行 | ✅ | ❌ |
| 冲突仲裁请求 | ❌ | ✅ |

## 参考资源

- MCP官方文档: https://modelcontextprotocol.io
- FastMCP文档: https://github.com/modelcontextprotocol/python-sdk
- TypeScript SDK: https://github.com/modelcontextprotocol/typescript-sdk
- 示例服务器: https://github.com/modelcontextprotocol/servers
