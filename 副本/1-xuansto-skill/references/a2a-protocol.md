# A2A协议参考文档

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
    "address": "https://agent-002.example.com/a2a"
  },
  "messageType": "request|response|notification|error",
  "contentType": "application/json",
  "payload": {},
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
  "messageType": "request",
  "payload": {
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
  "messageType": "response",
  "payload": {
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
  "messageType": "notification",
  "payload": {
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
  "messageType": "error",
  "payload": {
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
  "messageType": "stream",
  "payload": {
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

| 字段 | 类型 | 必填 | 验证规则 |
|------|------|------|----------|
| version | string | 是 | 语义版本格式 |
| messageId | string | 是 | UUID v4格式 |
| timestamp | string | 是 | ISO 8601格式 |
| source | object | 是 | 包含agentId |
| destination | object | 是 | 包含agentId或address |
| messageType | string | 是 | 枚举值 |
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
    "endpoint": "https://agent-001.example.com/a2a",
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
  "messageType": "batch",
  "payload": {
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

## 参考资源

- A2A协议规范: https://example.com/a2a-spec
- 智能体开发指南: https://example.com/agent-dev-guide
- 安全最佳实践: https://example.com/security-guide
