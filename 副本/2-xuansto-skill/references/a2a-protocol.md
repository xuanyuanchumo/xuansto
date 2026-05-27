# A2A协议参考文档
> 版本: 1.9.0 | 更新日期: 2026-04-28 | 编码: UTF-8 | 行尾: LF

## 目录

- [协议概述](#协议概述)
  - [什么是A2A协议](#什么是a2a协议)
  - [核心设计原则](#核心设计原则)
  - [协议版本](#协议版本)
  - [协议栈层次](#协议栈层次)
- [消息格式](#消息格式)
  - [基础消息结构](#基础消息结构)
  - [消息类型定义](#消息类型定义)
  - [流式消息格式](#流式消息格式)
  - [消息验证规则](#消息验证规则)
- [发现机制](#发现机制)
  - [智能体注册](#智能体注册)
  - [智能体发现流程](#智能体发现流程)
  - [能力匹配查询](#能力匹配查询)
  - [心跳机制](#心跳机制)
  - [服务网格集成](#服务网格集成)
- [安全考虑](#安全考虑)
  - [身份验证](#身份验证)
  - [授权模型](#授权模型)
  - [加密通信](#加密通信)
  - [审计日志](#审计日志)
  - [安全最佳实践](#安全最佳实践)
- [错误处理](#错误处理)
  - [错误代码体系](#错误代码体系)
  - [错误恢复策略](#错误恢复策略)
- [性能优化](#性能优化)
  - [消息压缩](#消息压缩)
  - [批量处理](#批量处理)
  - [连接池管理](#连接池管理)
- [版本兼容性](#版本兼容性)
  - [版本协商](#版本协商)
  - [向后兼容策略](#向后兼容策略)
- [Xuansto Skill Agent 集成映射](#xuansto-skill-agent-集成映射)
  - [层级-A2A类型总览](#层级-a2a类型总览)
  - [A2A消息映射示例](#a2a消息映射示例)
- [参考资源](#参考资源)

## 协议概述

### 什么是A2A协议

A2A（Agent-to-Agent）协议是一种标准化的智能体间通信协议，用于实现不同AI智能体之间的互操作性和协作能力。该协议定义了智能体发现、消息传递、任务协调和安全通信的规范。

### 核心设计原则

1. **互操作性**：支持异构智能体系统间的无缝通信
2. **可扩展性**：协议设计支持未来功能扩展
3. **安全性**：内置身份验证和授权机制
4. **异步通信**：支持同步和异步消息传递模式
5. **语义互操作**：基于共享本体和语义模型

### 协议版本

| 版本 | 发布日期 | 主要特性 |
|------|----------|----------|
| v1.0 | 2024-Q1 | 基础消息传递、发现机制 |
| v1.1 | 2024-Q2 | 增强安全模型、流式传输 |
| v2.0 | 2024-Q4 | 多模态支持、联邦学习集成 |

### 协议栈层次

```
┌─────────────────────────────────────┐
│         应用层 (Application)         │
│    任务协调、工作流编排、知识共享      │
├─────────────────────────────────────┤
│         会话层 (Session)             │
│    连接管理、状态维护、会话恢复        │
├─────────────────────────────────────┤
│         传输层 (Transport)           │
│    消息路由、可靠性保证、流量控制      │
├─────────────────────────────────────┤
│         安全层 (Security)            │
│    身份验证、授权、加密通信           │
├─────────────────────────────────────┤
│         网络层 (Network)             │
│    HTTP/WebSocket/gRPC、服务发现     │
└─────────────────────────────────────┘
```

## 消息格式

### 基础消息结构

```json
{
  "version": "2.0",
  "messageId": "msg-uuid-v4",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "source": {
    "agentId": "agent-001",
    "agentType": "orchestrator",
    "capabilities": ["task-planning", "resource-allocation"]
  },
  "destination": {
    "agentId": "agent-002",
    "agentType": "executor",
    "address": "https://agent-002.a2a.local/a2a"
  },
  "type": "TASK_ASSIGN|STATUS|GATE_CHECK|GATE_RESULT|KNOWLEDGE_SHARE|ERROR_REPORT|HELP_REQUEST|HANDOFF|request|response|broadcast|error",
  "protocol": "internal|a2a|mcp",
  "signature": "agent-signature",
  "contentType": "application/json",
  "payload": {
    "platform": "web|desktop|cross-platform"
  },
  "metadata": {
    "correlationId": "corr-uuid",
    "ttl": 30000,
    "priority": "normal|high|critical",
    "traceContext": {}
  }
}
```

### 消息类型定义

#### 请求消息 (Request)

```json
{
  "type": "TASK_ASSIGN",
  "protocol": "a2a",
  "signature": "agent-signature",
  "payload": {
    "platform": "cross-platform",
    "action": "execute-task",
    "parameters": {
      "taskId": "task-001",
      "taskType": "code-generation",
      "input": {
        "specification": "创建用户认证模块",
        "constraints": {
          "language": "TypeScript",
          "framework": "Express"
        }
      },
      "deadline": "2024-01-15T12:00:00.000Z"
    }
  }
}
```

#### 响应消息 (Response)

```json
{
  "type": "STATUS",
  "protocol": "a2a",
  "signature": "agent-signature",
  "payload": {
    "platform": "web",
    "status": "success|partial|failed",
    "result": {
      "taskId": "task-001",
      "artifacts": [
        {
          "type": "file",
          "path": "src/auth/user-auth.ts",
          "content": "..."
        }
      ],
      "metrics": {
        "executionTime": 45000,
        "tokensUsed": 2500
      }
    },
    "errors": []
  }
}
```

#### 通知消息 (Notification)

```json
{
  "type": "broadcast",
  "protocol": "a2a",
  "signature": "agent-signature",
  "payload": {
    "platform": "desktop",
    "event": "task-progress",
    "data": {
      "taskId": "task-001",
      "progress": 0.65,
      "currentStep": "生成单元测试",
      "estimatedRemaining": 15000
    }
  }
}
```

#### 错误消息 (Error)

```json
{
  "type": "ERROR_REPORT",
  "protocol": "a2a",
  "signature": "agent-signature",
  "payload": {
    "platform": "web",
    "errorCode": "TASK_EXECUTION_FAILED",
    "errorMessage": "任务执行失败：依赖解析错误",
    "errorDetails": {
      "type": "DependencyError",
      "cause": "缺少必需的npm包",
      "suggestions": [
        "运行 npm install 安装依赖",
        "检查 package.json 配置"
      ]
    },
    "recoverable": true,
    "retryAfter": 5000
  }
}
```

### 流式消息格式

用于大文件传输或长时间任务的状态更新：

```json
{
  "type": "GATE_CHECK",
  "protocol": "internal",
  "signature": "agent-signature",
  "payload": {
    "platform": "web",
    "streamId": "stream-001",
    "sequence": 1,
    "total": 100,
    "chunk": {
      "data": "...",
      "encoding": "base64"
    },
    "isLast": false
  }
}
```

### 消息验证规则

#### 消息类型枚举定义

| 消息类型 | 说明 | 典型场景 |
|----------|------|---------|
| TASK_ASSIGN | 任务分配 | 编排器向执行Agent分配任务 |
| STATUS | 状态报告 | 执行Agent向编排器报告任务状态 |
| GATE_CHECK | 门禁检查请求 | Agent请求执行质量门禁检查 |
| GATE_RESULT | 门禁检查结果 | 返回门禁检查通过/未通过结果 |
| KNOWLEDGE_SHARE | 知识共享 | Agent间共享知识库条目或经验 |
| ERROR_REPORT | 错误报告 | Agent报告执行错误或异常 |
| HELP_REQUEST | 帮助请求 | Agent请求其他Agent协助 |
| HANDOFF | 任务移交 | Agent间移交任务所有权 |
| request | 通用请求 | 兼容旧版通用请求消息 |
| response | 通用响应 | 兼容旧版通用响应消息 |
| broadcast | 广播通知 | 向多个Agent广播事件通知 |
| error | 通用错误 | 兼容旧版通用错误消息 |

| 字段 | 类型 | 必填 | 验证规则 |
|------|------|------|----------|
| version | string | 是 | 语义版本格式 |
| messageId | string | 是 | UUID v4格式 |
| timestamp | string | 是 | ISO 8601格式 |
| source | object | 是 | 包含agentId |
| destination | object | 是 | 包含agentId或address |
| type | string | 是 | 枚举值: TASK_ASSIGN, STATUS, GATE_CHECK, GATE_RESULT, KNOWLEDGE_SHARE, ERROR_REPORT, HELP_REQUEST, HANDOFF, request, response, broadcast, error |
| payload | object | 是 | 非空对象 |

## 发现机制

### 智能体注册

智能体启动时向注册中心发送注册请求：

```json
{
  "action": "register",
  "agent": {
    "agentId": "agent-001",
    "agentType": "code-generator",
    "version": "1.0.0",
    "endpoint": "https://agent-001.a2a.local/a2a",
    "capabilities": [
      {
        "name": "code-generation",
        "version": "1.0",
        "inputSchema": {},
        "outputSchema": {}
      },
      {
        "name": "code-review",
        "version": "1.0",
        "inputSchema": {},
        "outputSchema": {}
      }
    ],
    "metadata": {
      "maxConcurrentTasks": 5,
      "avgResponseTime": 2000,
      "supportedLanguages": ["TypeScript", "Python", "Go"]
    }
  },
  "ttl": 3600
}
```

### 智能体发现流程

```
┌─────────┐     ┌─────────────┐     ┌─────────────┐
│ Agent A │     │ Registry    │     │ Agent B     │
└────┬────┘     └──────┬──────┘     └──────┬──────┘
     │                 │                   │
     │  1. Register    │                   │
     │────────────────>│                   │
     │                 │                   │
     │                 │  2. Register      │
     │                 │<──────────────────│
     │                 │                   │
     │  3. Discover    │                   │
     │  (capability)   │                   │
     │────────────────>│                   │
     │                 │                   │
     │  4. Agent List  │                   │
     │<────────────────│                   │
     │                 │                   │
     │  5. Connect     │                   │
     │─────────────────────────────────────>│
     │                 │                   │
     │  6. Handshake   │                   │
     │<─────────────────────────────────────│
     │                 │                   │
```

### 能力匹配查询

```json
{
  "query": {
    "capabilities": {
      "must": ["code-generation"],
      "should": ["code-review", "testing"],
      "mustNot": ["deployment"]
    },
    "filters": {
      "supportedLanguages": ["TypeScript"],
      "maxResponseTime": 5000,
      "availability": "online"
    },
    "sortBy": "responseTime",
    "limit": 10
  }
}
```

### 心跳机制

智能体定期发送心跳以维持注册状态：

```json
{
  "action": "heartbeat",
  "agentId": "agent-001",
  "status": {
    "state": "healthy",
    "activeTasks": 2,
    "queueLength": 5,
    "cpuUsage": 0.45,
    "memoryUsage": 0.62
  },
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

心跳配置参数：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| interval | 30秒 | 心跳发送间隔 |
| timeout | 10秒 | 心跳响应超时 |
| maxMissed | 3 | 最大丢失心跳数 |
| gracePeriod | 60秒 | 注销宽限期 |

### 服务网格集成

支持与主流服务网格集成：

- **Istio**：通过Envoy Sidecar代理
- **Linkerd**：轻量级服务网格
- **Consul Connect**：服务发现与配置

## 安全考虑

### 身份验证

#### 令牌认证

```json
{
  "auth": {
    "type": "bearer",
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expiresAt": "2024-01-15T11:30:00.000Z"
  }
}
```

#### mTLS认证

双向TLS认证配置：

```yaml
tls:
  enabled: true
  certFile: /etc/certs/agent.crt
  keyFile: /etc/certs/agent.key
  caFile: /etc/certs/ca.crt
  verifyClient: true
  minVersion: TLS1.3
```

#### API Key认证

```json
{
  "auth": {
    "type": "api-key",
    "keyId": "key-001",
    "signature": "sha256-hmac-signature"
  }
}
```

### 授权模型

#### 基于角色的访问控制 (RBAC)

```json
{
  "roles": [
    {
      "name": "task-executor",
      "permissions": [
        "task:read",
        "task:execute",
        "result:submit"
      ]
    },
    {
      "name": "orchestrator",
      "permissions": [
        "task:*",
        "agent:discover",
        "workflow:*"
      ]
    }
  ],
  "bindings": [
    {
      "agentId": "agent-001",
      "roles": ["task-executor"]
    }
  ]
}
```

#### 基于属性的访问控制 (ABAC)

```json
{
  "policy": {
    "effect": "allow",
    "subject": {
      "agentType": "executor",
      "clearance": "confidential"
    },
    "resource": {
      "type": "task",
      "sensitivity": ["public", "internal", "confidential"]
    },
    "action": ["execute", "report"],
    "condition": {
      "timeWindow": "business-hours",
      "location": "trusted-network"
    }
  }
}
```

### 加密通信

#### 传输层加密

- 强制使用TLS 1.3
- 禁用弱密码套件
- 启用证书固定

#### 消息层加密

对于敏感数据，支持端到端加密：

```json
{
  "encryption": {
    "algorithm": "AES-256-GCM",
    "keyId": "key-2024-001",
    "iv": "base64-encoded-iv",
    "tag": "base64-encoded-tag"
  },
  "payload": "base64-encrypted-payload"
}
```

### 审计日志

记录所有关键操作：

```json
{
  "audit": {
    "eventId": "audit-001",
    "timestamp": "2024-01-15T10:30:00.000Z",
    "actor": {
      "agentId": "agent-001",
      "ipAddress": "192.168.1.100"
    },
    "action": "task.execute",
    "resource": {
      "type": "task",
      "id": "task-001"
    },
    "result": "success",
    "details": {}
  }
}
```

### 安全最佳实践

1. **最小权限原则**
   - 仅授予必要的权限
   - 定期审查权限分配
   - 实施权限过期机制

2. **零信任架构**
   - 每次请求都进行验证
   - 不信任网络位置
   - 持续监控和评估

3. **密钥管理**
   - 使用密钥管理系统 (KMS)
   - 定期轮换密钥
   - 安全存储凭证

4. **入侵检测**
   - 监控异常行为模式
   - 设置速率限制
   - 实施熔断机制

5. **安全更新**
   - 及时更新协议版本
   - 修补已知漏洞
   - 订阅安全公告

## 错误处理

### 错误代码体系

| 错误代码范围 | 类别 | 示例 |
|--------------|------|------|
| 1xxx | 协议错误 | 1001: 无效消息格式 |
| 2xxx | 认证错误 | 2001: 认证失败 |
| 3xxx | 授权错误 | 3001: 权限不足 |
| 4xxx | 资源错误 | 4001: 资源不存在 |
| 5xxx | 执行错误 | 5001: 任务执行失败 |
| 6xxx | 超时错误 | 6001: 请求超时 |
| 7xxx | 系统错误 | 7001: 内部服务错误 |

### 错误恢复策略

```json
{
  "recovery": {
    "strategy": "retry|fallback|compensate",
    "maxRetries": 3,
    "backoff": {
      "type": "exponential",
      "initialDelay": 1000,
      "maxDelay": 30000,
      "multiplier": 2
    },
    "fallback": {
      "action": "notify-admin",
      "message": "任务执行失败，已通知管理员"
    }
  }
}
```

## 性能优化

### 消息压缩

对于大型消息，支持压缩传输：

```json
{
  "contentEncoding": "gzip",
  "payload": "compressed-base64-data"
}
```

### 批量处理

支持批量消息减少网络开销：

```json
{
  "type": "KNOWLEDGE_SHARE",
  "protocol": "a2a",
  "signature": "agent-signature",
  "payload": {
    "platform": "cross-platform",
    "messages": [
      { "messageId": "msg-001", "payload": {} },
      { "messageId": "msg-002", "payload": {} }
    ]
  }
}
```

### 连接池管理

| 参数 | 推荐值 | 说明 |
|------|--------|------|
| maxConnections | 100 | 最大连接数 |
| idleTimeout | 300秒 | 空闲连接超时 |
| keepAlive | true | 启用保活 |
| connectionTimeout | 30秒 | 连接建立超时 |

## 版本兼容性

### 版本协商

```json
{
  "handshake": {
    "supportedVersions": ["2.0", "1.1", "1.0"],
    "selectedVersion": "2.0",
    "features": {
      "streaming": true,
      "compression": true,
      "encryption": true
    }
  }
}
```

### 向后兼容策略

1. **添加新字段**：使用可选字段，不影响旧版本
2. **弃用字段**：标记为deprecated，保留兼容期
3. **破坏性变更**：升级主版本号，提供迁移指南

## 集成示例

### Python A2A客户端完整集成

```python
import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any, Optional
import httpx

class A2AClient:
    def __init__(self, agent_id: str, agent_type: str, registry_url: str):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.registry_url = registry_url
        self._client = httpx.AsyncClient(timeout=30.0)

    def _build_message(
        self, message_type: str, payload: dict,
        destination: Optional[dict] = None,
    ) -> dict:
        return {
            "version": "2.0",
            "messageId": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": {"agentId": self.agent_id, "agentType": self.agent_type},
            "destination": destination or {},
            "type": message_type,
            "protocol": "a2a",
            "signature": "agent-signature",
            "contentType": "application/json",
            "payload": payload,
            "metadata": {"correlationId": str(uuid.uuid4()), "priority": "normal"},
        }

    async def register(self, capabilities: list[dict]) -> dict:
        msg = self._build_message("request", {
            "action": "register",
            "agent": {
                "agentId": self.agent_id,
                "agentType": self.agent_type,
                "capabilities": capabilities,
                "endpoint": f"https://{self.agent_id}.a2a.local/a2a",
            },
            "ttl": 3600,
        })
        resp = await self._client.post(
            f"{self.registry_url}/register", json=msg
        )
        resp.raise_for_status()
        return resp.json()

    async def discover(self, capability: str) -> list[dict]:
        msg = self._build_message("request", {
            "action": "discover",
            "query": {"capabilities": {"must": [capability]}},
        })
        resp = await self._client.post(
            f"{self.registry_url}/discover", json=msg
        )
        resp.raise_for_status()
        return resp.json().get("agents", [])

    async def send_task(
        self, target_endpoint: str, task_type: str, task_input: dict
    ) -> dict:
        msg = self._build_message("request", {
            "action": "execute-task",
            "parameters": {"taskType": task_type, "input": task_input},
        })
        resp = await self._client.post(target_endpoint, json=msg)
        resp.raise_for_status()
        return resp.json()

    async def close(self) -> None:
        await self._client.aclose()

async def main():
    client = A2AClient("agent-001", "orchestrator", "https://registry.a2a.local")
    await client.register([{"name": "task-planning", "version": "1.0"}])
    agents = await client.discover("code-generation")
    if agents:
        result = await client.send_task(
            agents[0]["endpoint"], "code-generation",
            {"specification": "创建REST API模块", "language": "TypeScript"},
        )
        print(f"任务结果: {result}")
    await client.close()

asyncio.run(main())
```

## 最佳实践

1. **消息幂等性**：为每个请求消息生成唯一messageId，接收方应做幂等校验，避免重复执行同一任务
2. **超时与重试**：所有A2A调用必须设置合理超时（建议30秒），重试采用指数退避策略，最大重试3次
3. **能力声明精确化**：注册时capabilities应包含inputSchema/outputSchema，便于调用方自动校验参数格式
4. **安全通信优先**：生产环境强制使用mTLS认证，敏感payload启用端到端加密（AES-256-GCM）
5. **心跳保活**：智能体应按30秒间隔发送心跳，连续3次丢失后注册中心应标记为离线并触发重连
6. **版本协商前置**：建立连接时先完成版本协商，选择双方支持的最高协议版本，避免运行时兼容性问题
7. **审计日志完整**：记录所有消息的发送/接收事件，包含messageId、时间戳、操作类型，便于问题追踪
8. **流量控制**：对高频消息使用批量处理减少网络开销，大payload启用gzip压缩，连接池最大连接数建议100

## Xuansto Skill Agent 集成映射

> **能力子角色澄清说明**：以下各层分项表中列出的子角色（如 Master Orchestrator、Sprint Planner 等）为**能力子角色（Capability Sub-Roles）**，代表该层实际 Agent 的内部能力维度，**并非独立的 Agent 实体**。实际的 Agent 定义以 `agent-registry.md` 为准，子角色与 Agent 注册表条目的对应关系见各表"对应Agent注册表ID"列。当多个子角色映射到同一个 Agent 注册表ID 时，映射类型标记为"一对多"；当子角色与 Agent 一一对应时，映射类型标记为"一对一"。

### 层级-A2A类型总览

| Xuansto Agent Layer | A2A agentType | A2A 能力描述 | Agent注册表数量 |
|---------------------|---------------|-------------|----------------|
| 编排层 | `orchestrator` | 任务编排、工作流调度、资源分配、Agent间协调 | 1 |
| 产品层 | `analyst` | 需求分析、用户故事编写、验收标准定义、优先级排序 | 3 |
| 设计层 | `designer` | 架构设计、UI/UX设计、API契约设计、数据模型设计 | 3 |
| 工程层 | `developer` | 代码实现、功能开发、重构优化、技术债务清理 | 6 |
| 跨平台层 | `desktop-developer` | Electron/Tauri开发、原生模块构建、IPC契约管理、跨平台打包 | 3 |
| 数据层 | `data-engineer` | 数据建模、迁移管理、缓存策略、外部API集成 | 3 |
| 测试层 | `tester` | 单元测试、集成测试、E2E测试、性能测试、回归测试 | 10 |
| 安全层 | `security-auditor` | 安全审计、漏洞扫描、OWASP合规检查、密钥安全审查 | 3 |
| 运维层 | `devops` | CI/CD流水线、基础设施管理、监控告警、发布部署 | 4 |
| 质量层 | `reviewer` | 代码审查、质量门禁、指标度量、四维防线检查 | 3 |
| 文档层 | `documenter` | API文档生成、知识库管理、变更日志、Decision Log维护 | 2 |

### 编排层 → `orchestrator`

| Agent | A2A capability | 说明 | 对应Agent注册表ID | 映射类型 |
|-------|----------------|------|-------------------|----------|
| Master Orchestrator | `task-orchestration` | 主编排器，统筹9阶段工作流 | orchestrator | 一对多 |
| Sprint Planner | `sprint-planning` | 冲刺规划，任务分解与排期 | orchestrator | 一对多 |
| Task Dispatcher | `task-dispatch` | 任务调度，Agent间任务分配 | orchestrator | 一对多 |
| Workflow Coordinator | `workflow-coordination` | 工作流协调，阶段间衔接与状态流转 | orchestrator | 一对多 |

### 产品层 → `analyst`

| Agent | A2A capability | 说明 | 对应Agent注册表ID | 映射类型 |
|-------|----------------|------|-------------------|----------|
| Requirements Analyst | `requirement-analysis` | 需求分析，功能/非功能需求提取 | product-manager | 一对多 |
| Product Owner | `product-ownership` | 产品决策，优先级与范围管理 | product-manager | 一对多 |
| User Story Writer | `user-story-writing` | 用户故事编写，验收标准定义 | technical-writer | 一对一 |
| Acceptance Validator | `acceptance-validation` | 验收确认，需求满足度验证 | system-architect | 一对一 |

### 设计层 → `designer`

| Agent | A2A capability | 说明 | 对应Agent注册表ID | 映射类型 |
|-------|----------------|------|-------------------|----------|
| Architecture Designer | `architecture-design` | 架构设计，技术选型与模块划分 | ui-designer | 一对多 |
| UI/UX Designer | `ui-ux-design` | 界面设计，交互模式与设计令牌 | ux-designer | 一对一 |
| API Designer | `api-contract-design` | API契约设计，接口规范定义 | ui-designer | 一对多 |
| Database Designer | `data-model-design` | 数据模型设计，Schema与关系定义 | ui-stylist | 一对一 |

### 工程层 → `developer`

| Agent | A2A capability | 说明 | 对应Agent注册表ID | 映射类型 |
|-------|----------------|------|-------------------|----------|
| Frontend Developer | `frontend-development` | 前端开发，React/Vue/Svelte实现 | frontend-developer | 一对一 |
| Backend Developer | `backend-development` | 后端开发，API与服务逻辑实现 | backend-developer | 一对一 |
| Full-Stack Developer | `fullstack-development` | 全栈开发，端到端功能交付 | fullstack-developer | 一对一 |
| Code Generator | `code-generation` | 代码生成，模板驱动与自动化产出 | devops-engineer | 一对一 |

### 跨平台层 → `desktop-developer`

| Agent | A2A capability | 说明 | 对应Agent注册表ID | 映射类型 |
|-------|----------------|------|-------------------|----------|
| Electron Developer | `electron-development` | Electron桌面应用开发 | desktop-developer | 一对多 |
| Tauri Developer | `tauri-development` | Tauri桌面应用开发 | desktop-developer | 一对多 |
| Native Module Builder | `native-module-build` | 原生模块构建与Rust/C++集成 | native-module-developer | 一对一 |
| IPC Contract Manager | `ipc-contract-management` | IPC契约管理，主进程与渲染进程通信 | desktop-ui-adapter | 一对一 |

### 数据层 → `data-engineer`

| Agent | A2A capability | 说明 | 对应Agent注册表ID | 映射类型 |
|-------|----------------|------|-------------------|----------|
| Data Modeler | `data-modeling` | 数据建模，实体关系与Schema设计 | database-modeler | 一对多 |
| Migration Specialist | `migration-management` | 数据库迁移，版本演进管理 | data-seeder | 一对一 |
| Cache Strategist | `cache-strategy` | 缓存策略，Redis/内存缓存优化 | database-admin | 一对一 |
| API Integrator | `api-integration` | 外部API集成，第三方服务对接 | database-modeler | 一对多 |

### 测试层 → `tester`

| Agent | A2A capability | 说明 | 对应Agent注册表ID | 映射类型 |
|-------|----------------|------|-------------------|----------|
| Unit Tester | `unit-testing` | 单元测试，TDD驱动函数级验证 | unit-tester | 一对一 |
| Integration Tester | `integration-testing` | 集成测试，模块间交互验证 | integration-tester | 一对一 |
| E2E Tester | `e2e-testing` | 端到端测试，用户场景全链路验证 | e2e-tester | 一对一 |
| Performance Tester | `performance-testing` | 性能测试，负载与基准测试 | performance-tester | 一对一 |

### 安全层 → `security-auditor`

| Agent | A2A capability | 说明 | 对应Agent注册表ID | 映射类型 |
|-------|----------------|------|-------------------|----------|
| Security Auditor | `security-audit` | 安全审计，OWASP Top 10合规检查 | security-auditor | 一对一 |
| Vulnerability Scanner | `vulnerability-scanning` | 漏洞扫描，依赖与代码安全检测 | ai-penetration-tester | 一对一 |
| Compliance Checker | `compliance-checking` | 合规检查，密钥安全与硬编码检测 | compliance-officer | 一对一 |

### 运维层 → `devops`

| Agent | A2A capability | 说明 | 对应Agent注册表ID | 映射类型 |
|-------|----------------|------|-------------------|----------|
| CI/CD Pipeline Agent | `cicd-pipeline` | CI/CD流水线，自动化构建与部署 | cicd-specialist | 一对一 |
| Infrastructure Manager | `infrastructure-management` | 基础设施管理，环境配置与容器编排 | runtime-supervisor | 一对一 |
| Monitoring Agent | `monitoring-alerting` | 监控告警，运行时指标采集与异常通知 | monitor-analyst | 一对一 |
| Release Manager | `release-management` | 发布管理，版本发布与回滚策略 | build-release-engineer | 一对一 |

### 质量层 → `reviewer`

| Agent | A2A capability | 说明 | 对应Agent注册表ID | 映射类型 |
|-------|----------------|------|-------------------|----------|
| Code Reviewer | `code-review` | 代码审查，编码规范与最佳实践检查 | code-reviewer | 一对多 |
| Quality Gate Keeper | `quality-gate` | 质量门禁，33质量门禁检查点执行 | code-reviewer | 一对多 |
| Metrics Collector | `metrics-collection` | 指标收集，六维质量监控与趋势分析 | refactoring-specialist | 一对一 |

### 文档层 → `documenter`

| Agent | A2A capability | 说明 | 对应Agent注册表ID | 映射类型 |
|-------|----------------|------|-------------------|----------|
| API Documenter | `api-documentation` | API文档生成，OpenAPI/接口说明维护 | documentation-engineer | 一对多 |
| Knowledge Base Manager | `knowledge-management` | 知识库管理，经验沉淀与知识学习 | specification-keeper | 一对一 |
| Changelog Generator | `changelog-generation` | 变更日志，Decision Log与版本记录 | documentation-engineer | 一对多 |

### A2A消息映射示例

Xuansto Agent间协作通过A2A协议消息实现，以下为典型协作场景的消息映射：

```
编排层(Master Orchestrator)
  │  TASK_ASSIGN → 工程层(Frontend Developer)
  │                     │  STATUS → 编排层
  │                     │  GATE_CHECK → 质量层(Code Reviewer)
  │                     │                     │  GATE_RESULT → 工程层
  │  HANDOFF → 测试层(Unit Tester)
  │                │  STATUS → 编排层
  │  KNOWLEDGE_SHARE → 文档层(API Documenter)
```

对应的A2A消息中 `source.agentType` 与 `destination.agentType` 应使用上表定义的 agentType 值，确保Agent发现与能力匹配的准确性。

## 参考资源

- A2A协议规范: https://github.com/google/A2A
- A2A开发文档: https://google.github.io/A2A/
- 安全最佳实践: https://owasp.org/www-project-top-ten/
