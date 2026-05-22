# MCP 服务器项目模板

本文档提供 MCP (Model Context Protocol) 服务器项目的标准模板，包含项目结构、工具定义和配置文件模板。

## 一、MCP 服务器项目结构

### 1.1 Python MCP 服务器项目结构

```
mcp-server/
├── src/
│   ├── mcp_server/
│   │   ├── __init__.py
│   │   ├── server.py              # 服务器主入口
│   │   ├── tools/                 # 工具定义
│   │   │   ├── __init__.py
│   │   │   ├── base.py            # 工具基类
│   │   │   ├── file_tools.py      # 文件操作工具
│   │   │   ├── search_tools.py    # 搜索工具
│   │   │   └── data_tools.py      # 数据处理工具
│   │   ├── resources/             # 资源定义
│   │   │   ├── __init__.py
│   │   │   ├── base.py            # 资源基类
│   │   │   └── file_resources.py  # 文件资源
│   │   ├── prompts/               # 提示词模板
│   │   │   ├── __init__.py
│   │   │   └── templates.py
│   │   ├── handlers/              # 请求处理器
│   │   │   ├── __init__.py
│   │   │   └── message_handler.py
│   │   ├── utils/                 # 工具函数
│   │   │   ├── __init__.py
│   │   │   ├── logger.py
│   │   │   └── validators.py
│   │   └── config.py              # 配置管理
│   └── main.py                    # 启动入口
├── tests/                         # 测试
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_tools/
│   └── test_server.py
├── config/                        # 配置文件
│   ├── server.json                # 服务器配置
│   └── tools.json                 # 工具配置
├── pyproject.toml
├── requirements.txt
├── .env.example
├── Dockerfile
└── README.md
```

### 1.2 TypeScript MCP 服务器项目结构

```
mcp-server/
├── src/
│   ├── index.ts                   # 入口文件
│   ├── server.ts                  # 服务器核心
│   ├── tools/                     # 工具定义
│   │   ├── index.ts
│   │   ├── base.ts                # 工具基类
│   │   ├── fileTools.ts           # 文件操作工具
│   │   ├── searchTools.ts         # 搜索工具
│   │   └── dataTools.ts           # 数据处理工具
│   ├── resources/                 # 资源定义
│   │   ├── index.ts
│   │   ├── base.ts
│   │   └── fileResources.ts
│   ├── prompts/                   # 提示词模板
│   │   ├── index.ts
│   │   └── templates.ts
│   ├── handlers/                  # 请求处理器
│   │   └── messageHandler.ts
│   ├── types/                     # 类型定义
│   │   ├── tools.ts
│   │   ├── resources.ts
│   │   └── messages.ts
│   ├── utils/                     # 工具函数
│   │   ├── logger.ts
│   │   └── validators.ts
│   └── config.ts                  # 配置管理
├── tests/                         # 测试
│   ├── tools/
│   └── server.test.ts
├── config/                        # 配置文件
│   ├── server.json
│   └── tools.json
├── package.json
├── tsconfig.json
├── .env.example
├── Dockerfile
└── README.md
```

## 二、工具定义模板

### 2.1 Python 工具定义

**tools/base.py**
```python
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class ToolParameter(BaseModel):
    name: str
    type: str
    description: str
    required: bool = True
    default: Optional[Any] = None


class ToolResult(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None


class BaseTool(ABC):
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    @property
    @abstractmethod
    def parameters(self) -> List[ToolParameter]:
        pass
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        pass
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    p.name: {
                        "type": p.type,
                        "description": p.description
                    }
                    for p in self.parameters
                },
                "required": [p.name for p in self.parameters if p.required]
            }
        }
```

**tools/file_tools.py**
```python
from typing import List, Optional
from pathlib import Path
from .base import BaseTool, ToolParameter, ToolResult


class ReadFileTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="read_file",
            description="读取指定路径的文件内容"
        )
    
    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="path",
                type="string",
                description="文件路径",
                required=True
            ),
            ToolParameter(
                name="encoding",
                type="string",
                description="文件编码",
                required=False,
                default="utf-8"
            )
        ]
    
    async def execute(self, path: str, encoding: str = "utf-8") -> ToolResult:
        try:
            file_path = Path(path)
            if not file_path.exists():
                return ToolResult(success=False, error=f"文件不存在: {path}")
            
            content = file_path.read_text(encoding=encoding)
            return ToolResult(success=True, data=content)
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class WriteFileTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="write_file",
            description="将内容写入指定文件"
        )
    
    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="path",
                type="string",
                description="文件路径",
                required=True
            ),
            ToolParameter(
                name="content",
                type="string",
                description="文件内容",
                required=True
            ),
            ToolParameter(
                name="mode",
                type="string",
                description="写入模式: write 或 append",
                required=False,
                default="write"
            )
        ]
    
    async def execute(
        self, 
        path: str, 
        content: str, 
        mode: str = "write"
    ) -> ToolResult:
        try:
            file_path = Path(path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            write_mode = "a" if mode == "append" else "w"
            file_path.write_text(content, encoding="utf-8")
            
            return ToolResult(
                success=True, 
                data={"path": str(file_path), "bytes_written": len(content)}
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class ListDirectoryTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="list_directory",
            description="列出目录内容"
        )
    
    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="path",
                type="string",
                description="目录路径",
                required=True
            ),
            ToolParameter(
                name="recursive",
                type="boolean",
                description="是否递归列出",
                required=False,
                default=False
            )
        ]
    
    async def execute(self, path: str, recursive: bool = False) -> ToolResult:
        try:
            dir_path = Path(path)
            if not dir_path.is_dir():
                return ToolResult(success=False, error=f"不是有效目录: {path}")
            
            if recursive:
                items = [
                    str(p.relative_to(dir_path)) 
                    for p in dir_path.rglob("*")
                ]
            else:
                items = [p.name for p in dir_path.iterdir()]
            
            return ToolResult(success=True, data=sorted(items))
        except Exception as e:
            return ToolResult(success=False, error=str(e))
```

### 2.2 TypeScript 工具定义

**tools/base.ts**
```typescript
export interface ToolParameter {
    name: string;
    type: 'string' | 'number' | 'boolean' | 'object' | 'array';
    description: string;
    required: boolean;
    default?: unknown;
}

export interface ToolResult {
    success: boolean;
    data?: unknown;
    error?: string;
}

export interface ToolSchema {
    name: string;
    description: string;
    parameters: {
        type: 'object';
        properties: Record<string, {
            type: string;
            description: string;
        }>;
        required: string[];
    };
}

export abstract class BaseTool {
    constructor(
        public readonly name: string,
        public readonly description: string
    ) {}
    
    abstract get parameters(): ToolParameter[];
    abstract execute(params: Record<string, unknown>): Promise<ToolResult>;
    
    getSchema(): ToolSchema {
        return {
            name: this.name,
            description: this.description,
            parameters: {
                type: 'object',
                properties: Object.fromEntries(
                    this.parameters.map(p => [
                        p.name,
                        { type: p.type, description: p.description }
                    ])
                ),
                required: this.parameters
                    .filter(p => p.required)
                    .map(p => p.name)
            }
        };
    }
}
```

**tools/fileTools.ts**
```typescript
import * as fs from 'fs/promises';
import * as path from 'path';
import { BaseTool, ToolParameter, ToolResult } from './base';

export class ReadFileTool extends BaseTool {
    constructor() {
        super('read_file', '读取指定路径的文件内容');
    }
    
    get parameters(): ToolParameter[] {
        return [
            {
                name: 'path',
                type: 'string',
                description: '文件路径',
                required: true
            },
            {
                name: 'encoding',
                type: 'string',
                description: '文件编码',
                required: false,
                default: 'utf-8'
            }
        ];
    }
    
    async execute(params: Record<string, unknown>): Promise<ToolResult> {
        try {
            const filePath = params.path as string;
            const encoding = (params.encoding as BufferEncoding) || 'utf-8';
            
            const content = await fs.readFile(filePath, encoding);
            return { success: true, data: content };
        } catch (error) {
            return { success: false, error: String(error) };
        }
    }
}

export class WriteFileTool extends BaseTool {
    constructor() {
        super('write_file', '将内容写入指定文件');
    }
    
    get parameters(): ToolParameter[] {
        return [
            {
                name: 'path',
                type: 'string',
                description: '文件路径',
                required: true
            },
            {
                name: 'content',
                type: 'string',
                description: '文件内容',
                required: true
            }
        ];
    }
    
    async execute(params: Record<string, unknown>): Promise<ToolResult> {
        try {
            const filePath = params.path as string;
            const content = params.content as string;
            
            await fs.mkdir(path.dirname(filePath), { recursive: true });
            await fs.writeFile(filePath, content, 'utf-8');
            
            return { 
                success: true, 
                data: { path: filePath, bytesWritten: content.length }
            };
        } catch (error) {
            return { success: false, error: String(error) };
        }
    }
}
```

## 三、服务器核心代码模板

### 3.1 Python 服务器实现

**server.py**
```python
import asyncio
import json
from typing import Dict, List, Optional
from .tools.base import BaseTool, ToolResult
from .utils.logger import get_logger

logger = get_logger(__name__)


class MCPServer:
    def __init__(self, name: str, version: str = "1.0.0"):
        self.name = name
        self.version = version
        self.tools: Dict[str, BaseTool] = {}
        self.resources: Dict[str, any] = {}
        self.prompts: Dict[str, any] = {}
    
    def register_tool(self, tool: BaseTool):
        self.tools[tool.name] = tool
        logger.info(f"注册工具: {tool.name}")
    
    def register_resource(self, name: str, resource: any):
        self.resources[name] = resource
        logger.info(f"注册资源: {name}")
    
    def register_prompt(self, name: str, prompt: any):
        self.prompts[name] = prompt
        logger.info(f"注册提示词: {name}")
    
    def get_server_info(self) -> Dict:
        return {
            "name": self.name,
            "version": self.version,
            "capabilities": {
                "tools": len(self.tools) > 0,
                "resources": len(self.resources) > 0,
                "prompts": len(self.prompts) > 0
            }
        }
    
    def list_tools(self) -> List[Dict]:
        return [tool.get_schema() for tool in self.tools.values()]
    
    async def call_tool(self, name: str, arguments: Dict) -> ToolResult:
        if name not in self.tools:
            return ToolResult(
                success=False, 
                error=f"工具不存在: {name}"
            )
        
        tool = self.tools[name]
        logger.info(f"调用工具: {name}, 参数: {arguments}")
        
        try:
            result = await tool.execute(**arguments)
            return result
        except Exception as e:
            logger.error(f"工具执行失败: {name}, 错误: {e}")
            return ToolResult(success=False, error=str(e))
    
    async def handle_message(self, message: Dict) -> Dict:
        method = message.get("method")
        params = message.get("params", {})
        
        handlers = {
            "initialize": self._handle_initialize,
            "tools/list": self._handle_tools_list,
            "tools/call": self._handle_tools_call,
            "resources/list": self._handle_resources_list,
            "prompts/list": self._handle_prompts_list,
        }
        
        handler = handlers.get(method)
        if not handler:
            return {"error": f"未知方法: {method}"}
        
        return await handler(params)
    
    async def _handle_initialize(self, params: Dict) -> Dict:
        return {
            "result": {
                "serverInfo": self.get_server_info(),
                "protocolVersion": "2024-11-05"
            }
        }
    
    async def _handle_tools_list(self, params: Dict) -> Dict:
        return {"result": {"tools": self.list_tools()}}
    
    async def _handle_tools_call(self, params: Dict) -> Dict:
        name = params.get("name")
        arguments = params.get("arguments", {})
        result = await self.call_tool(name, arguments)
        return {"result": result.model_dump()}
    
    async def _handle_resources_list(self, params: Dict) -> Dict:
        return {"result": {"resources": list(self.resources.keys())}}
    
    async def _handle_prompts_list(self, params: Dict) -> Dict:
        return {"result": {"prompts": list(self.prompts.keys())}}
```

### 3.2 TypeScript 服务器实现

**server.ts**
```typescript
import { BaseTool, ToolResult } from './tools/base';

interface ServerInfo {
    name: string;
    version: string;
    capabilities: {
        tools: boolean;
        resources: boolean;
        prompts: boolean;
    };
}

interface Message {
    method: string;
    params?: Record<string, unknown>;
}

export class MCPServer {
    private tools: Map<string, BaseTool> = new Map();
    private resources: Map<string, unknown> = new Map();
    private prompts: Map<string, unknown> = new Map();
    
    constructor(
        private readonly name: string,
        private readonly version: string = '1.0.0'
    ) {}
    
    registerTool(tool: BaseTool): void {
        this.tools.set(tool.name, tool);
        console.log(`注册工具: ${tool.name}`);
    }
    
    registerResource(name: string, resource: unknown): void {
        this.resources.set(name, resource);
        console.log(`注册资源: ${name}`);
    }
    
    registerPrompt(name: string, prompt: unknown): void {
        this.prompts.set(name, prompt);
        console.log(`注册提示词: ${name}`);
    }
    
    getServerInfo(): ServerInfo {
        return {
            name: this.name,
            version: this.version,
            capabilities: {
                tools: this.tools.size > 0,
                resources: this.resources.size > 0,
                prompts: this.prompts.size > 0
            }
        };
    }
    
    listTools(): unknown[] {
        return Array.from(this.tools.values()).map(t => t.getSchema());
    }
    
    async callTool(name: string, args: Record<string, unknown>): Promise<ToolResult> {
        const tool = this.tools.get(name);
        if (!tool) {
            return { success: false, error: `工具不存在: ${name}` };
        }
        
        console.log(`调用工具: ${name}, 参数:`, args);
        
        try {
            return await tool.execute(args);
        } catch (error) {
            console.error(`工具执行失败: ${name}`, error);
            return { success: false, error: String(error) };
        }
    }
    
    async handleMessage(message: Message): Promise<unknown> {
        const { method, params = {} } = message;
        
        switch (method) {
            case 'initialize':
                return {
                    result: {
                        serverInfo: this.getServerInfo(),
                        protocolVersion: '2024-11-05'
                    }
                };
            
            case 'tools/list':
                return { result: { tools: this.listTools() } };
            
            case 'tools/call':
                const result = await this.callTool(
                    params.name as string,
                    params.arguments as Record<string, unknown>
                );
                return { result };
            
            case 'resources/list':
                return { result: { resources: Array.from(this.resources.keys()) } };
            
            case 'prompts/list':
                return { result: { prompts: Array.from(this.prompts.keys()) } };
            
            default:
                return { error: `未知方法: ${method}` };
        }
    }
}
```

## 四、配置文件模板

### 4.1 服务器配置

**config/server.json**
```json
{
    "server": {
        "name": "my-mcp-server",
        "version": "1.0.0",
        "description": "自定义 MCP 服务器",
        "transport": {
            "type": "stdio",
            "options": {}
        }
    },
    "logging": {
        "level": "info",
        "format": "json",
        "output": "stderr"
    },
    "security": {
        "allowedPaths": ["./workspace"],
        "maxFileSize": 10485760,
        "timeout": 30000
    }
}
```

### 4.2 工具配置

**config/tools.json**
```json
{
    "tools": [
        {
            "name": "read_file",
            "enabled": true,
            "permissions": ["read"],
            "rateLimit": {
                "requests": 100,
                "window": 60
            }
        },
        {
            "name": "write_file",
            "enabled": true,
            "permissions": ["write"],
            "rateLimit": {
                "requests": 50,
                "window": 60
            }
        },
        {
            "name": "list_directory",
            "enabled": true,
            "permissions": ["read"],
            "rateLimit": {
                "requests": 100,
                "window": 60
            }
        }
    ]
}
```

### 4.3 项目配置文件

**pyproject.toml**
```toml
[project]
name = "mcp-server"
version = "1.0.0"
description = "MCP Server Implementation"
requires-python = ">=3.10"
dependencies = [
    "mcp>=1.0.0",
    "pydantic>=2.5.0",
    "asyncio-throttle>=1.0.0"
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "black>=23.0.0",
    "mypy>=1.0.0"
]

[project.scripts]
mcp-server = "mcp_server.main:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

**package.json**
```json
{
    "name": "mcp-server",
    "version": "1.0.0",
    "description": "MCP Server Implementation",
    "type": "module",
    "main": "dist/index.js",
    "types": "dist/index.d.ts",
    "scripts": {
        "build": "tsc",
        "start": "node dist/index.js",
        "dev": "tsx watch src/index.ts",
        "test": "vitest",
        "lint": "eslint src/"
    },
    "dependencies": {
        "@modelcontextprotocol/sdk": "^1.0.0"
    },
    "devDependencies": {
        "@types/node": "^20.0.0",
        "typescript": "^5.3.0",
        "tsx": "^4.0.0",
        "vitest": "^1.0.0"
    }
}
```

**tsconfig.json**
```json
{
    "compilerOptions": {
        "target": "ES2022",
        "module": "NodeNext",
        "moduleResolution": "NodeNext",
        "outDir": "dist",
        "rootDir": "src",
        "strict": true,
        "esModuleInterop": true,
        "skipLibCheck": true,
        "declaration": true,
        "declarationMap": true,
        "sourceMap": true
    },
    "include": ["src/**/*"],
    "exclude": ["node_modules", "dist"]
}
```

### 4.4 环境变量

**.env.example**
```env
SERVER_NAME=mcp-server
SERVER_VERSION=1.0.0

LOG_LEVEL=info
LOG_FORMAT=json

ALLOWED_PATHS=./workspace
MAX_FILE_SIZE=10485760
REQUEST_TIMEOUT=30000

RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60
```

## 五、Docker 配置

**Dockerfile (Python)**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY src/ ./src/
COPY config/ ./config/

ENV PYTHONUNBUFFERED=1
ENV LOG_LEVEL=info

CMD ["mcp-server"]
```

**Dockerfile (TypeScript)**
```dockerfile
FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY dist/ ./dist/
COPY config/ ./config/

ENV NODE_ENV=production
ENV LOG_LEVEL=info

CMD ["node", "dist/index.js"]
```

## 六、开发流程说明

### 6.1 项目初始化

1. **创建项目**
   ```bash
   # Python
   mkdir mcp-server && cd mcp-server
   python -m venv .venv
   source .venv/bin/activate
   
   # TypeScript
   mkdir mcp-server && cd mcp-server
   npm init -y
   npm install @modelcontextprotocol/sdk
   ```

2. **配置开发环境**
   - 配置代码格式化工具
   - 配置类型检查
   - 配置测试框架

3. **实现核心功能**
   - 定义工具接口
   - 实现服务器核心
   - 添加配置管理

### 6.2 工具开发规范

1. **工具命名规范**
   - 使用 snake_case 命名
   - 名称应清晰描述功能
   - 避免使用保留字

2. **参数设计原则**
   - 参数数量适中（建议 3-5 个）
   - 提供合理的默认值
   - 完善的参数描述

3. **错误处理**
   - 捕获所有异常
   - 返回有意义的错误信息
   - 记录错误日志

### 6.3 测试规范

1. **单元测试**
   - 测试每个工具的独立功能
   - 测试边界条件
   - 测试错误处理

2. **集成测试**
   - 测试服务器启动
   - 测试消息处理流程
   - 测试工具调用链

3. **性能测试**
   - 测试并发处理能力
   - 测试内存使用
   - 测试响应时间

### 6.4 部署流程

1. **本地测试**
   ```bash
   # Python
   pytest
   
   # TypeScript
   npm test
   ```

2. **构建发布**
   ```bash
   # Python
   python -m build
   twine upload dist/*
   
   # TypeScript
   npm run build
   npm publish
   ```

3. **Docker 部署**
   ```bash
   docker build -t mcp-server .
   docker run -d mcp-server
   ```
