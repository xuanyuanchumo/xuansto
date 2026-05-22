---
name: api_sheji
description: API设计指导，包含RESTful设计原则、接口设计规范和版本管理指南。
---
# API设计指导

## RESTful设计原则

### 核心概念

REST（Representational State Transfer）是一种软件架构风格，用于设计网络应用程序。RESTful API遵循以下核心原则：

### 1. 资源导向

- **资源（Resource）**：API的核心概念，代表业务实体
- **统一资源标识符（URI）**：每个资源通过唯一的URI标识
- **资源命名规范**：
  - 使用名词而非动词
  - 使用复数形式表示资源集合
  - 使用小写字母和连字符
  - 避免深层嵌套（建议不超过3层）

```
✅ 正确示例：
GET    /users              # 获取用户列表
GET    /users/{id}         # 获取指定用户
GET    /users/{id}/orders  # 获取指定用户的订单列表

❌ 错误示例：
GET    /getUsers           # 不应使用动词
GET    /user               # 应使用复数形式
GET    /users/{id}/orders/{orderId}/items/{itemId}/details  # 嵌套过深
```

### 2. HTTP方法语义

| HTTP方法 | 操作 | 幂等性 | 安全性 | 说明 |
|---------|------|--------|--------|------|
| GET | 查询 | 是 | 是 | 获取资源，不应修改服务器状态 |
| POST | 创建 | 否 | 否 | 创建新资源 |
| PUT | 更新 | 是 | 否 | 完整更新资源（替换） |
| PATCH | 部分更新 | 否 | 否 | 部分更新资源 |
| DELETE | 删除 | 是 | 否 | 删除资源 |

### 3. 状态码规范

#### 成功响应（2xx）

| 状态码 | 说明 | 使用场景 |
|--------|------|----------|
| 200 OK | 请求成功 | GET、PUT、PATCH成功 |
| 201 Created | 创建成功 | POST创建资源成功 |
| 202 Accepted | 已接受 | 异步任务已接收 |
| 204 No Content | 无内容 | DELETE成功或PUT无返回内容 |

#### 客户端错误（4xx）

| 状态码 | 说明 | 使用场景 |
|--------|------|----------|
| 400 Bad Request | 请求格式错误 | 参数校验失败 |
| 401 Unauthorized | 未认证 | 缺少或无效的身份认证 |
| 403 Forbidden | 禁止访问 | 无权限访问资源 |
| 404 Not Found | 资源不存在 | 请求的资源不存在 |
| 405 Method Not Allowed | 方法不允许 | 不支持的HTTP方法 |
| 409 Conflict | 冲突 | 资源状态冲突 |
| 422 Unprocessable Entity | 无法处理 | 语义错误 |
| 429 Too Many Requests | 请求过多 | 触发限流 |

#### 服务端错误（5xx）

| 状态码 | 说明 | 使用场景 |
|--------|------|----------|
| 500 Internal Server Error | 服务器错误 | 未知的服务器错误 |
| 502 Bad Gateway | 网关错误 | 上游服务不可用 |
| 503 Service Unavailable | 服务不可用 | 服务暂时不可用 |
| 504 Gateway Timeout | 网关超时 | 上游服务超时 |

### 4. 无状态性

- 每个请求必须包含所有必要信息
- 服务器不保存客户端会话状态
- 便于水平扩展和负载均衡

### 5. 统一接口

- 使用标准的HTTP方法和状态码
- 资源标识符统一规范
- 响应格式统一（JSON）
- 错误信息结构统一

---

## 接口设计规范

### 请求规范

#### URL设计

```
基础URL格式：
https://api.example.com/v1/resource-name

示例：
https://api.example.com/v1/users
https://api.example.com/v1/orders/12345
https://api.example.com/v1/products?category=electronics&page=1&size=20
```

#### 查询参数

| 参数类型 | 说明 | 示例 |
|---------|------|------|
| 分页 | page, size/limit, offset | ?page=1&size=20 |
| 排序 | sort, order | ?sort=created_at&order=desc |
| 过滤 | 字段名=值 | ?status=active&category=book |
| 字段选择 | fields | ?fields=id,name,email |
| 搜索 | q, search, keyword | ?q=keyword |

#### 请求头

```http
Content-Type: application/json
Accept: application/json
Authorization: Bearer {token}
X-Request-ID: {uuid}          # 请求追踪ID
X-API-Version: 1              # API版本（可选）
```

#### 请求体

```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "age": 25
}
```

### 响应规范

#### 成功响应格式

**单资源响应**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": "12345",
    "username": "john_doe",
    "email": "john@example.com",
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

**列表响应（带分页）**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "id": "1",
        "name": "Item 1"
      },
      {
        "id": "2",
        "name": "Item 2"
      }
    ],
    "pagination": {
      "page": 1,
      "size": 20,
      "total": 100,
      "total_pages": 5
    }
  }
}
```

#### 错误响应格式

```json
{
  "code": 400,
  "message": "参数校验失败",
  "error": {
    "type": "validation_error",
    "details": [
      {
        "field": "email",
        "message": "邮箱格式不正确"
      },
      {
        "field": "age",
        "message": "年龄必须大于0"
      }
    ]
  },
  "request_id": "req_abc123xyz",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 字段命名规范

- 使用小驼峰命名法（camelCase）
- 布尔类型使用is/has前缀
- 时间字段使用_at后缀
- 数量字段使用_count后缀

```json
{
  "userId": "123",
  "userName": "john",
  "isActive": true,
  "hasPermission": false,
  "createdAt": "2024-01-15T10:30:00Z",
  "updatedAt": "2024-01-15T10:30:00Z",
  "orderCount": 10
}
```

### 时间格式

- 统一使用ISO 8601格式
- 使用UTC时间
- 格式：`YYYY-MM-DDTHH:mm:ssZ` 或 `YYYY-MM-DDTHH:mm:ss.SSSZ`

```
示例：
2024-01-15T10:30:00Z
2024-01-15T10:30:00.123Z
```

### 分页设计

#### 基于偏移量分页

```
请求：
GET /users?page=1&size=20

响应：
{
  "data": {
    "items": [...],
    "pagination": {
      "page": 1,
      "size": 20,
      "total": 100,
      "total_pages": 5
    }
  }
}
```

#### 基于游标分页（大数据量推荐）

```
请求：
GET /messages?cursor=eyJpZCI6MTAwfQ&limit=20

响应：
{
  "data": {
    "items": [...],
    "pagination": {
      "next_cursor": "eyJpZCI6MTIwfQ",
      "prev_cursor": "eyJpZCI6ODB9",
      "has_more": true
    }
  }
}
```

### 过滤与排序

```
过滤：
GET /orders?status=pending&created_after=2024-01-01

排序：
GET /products?sort=price&order=asc
GET /products?sort=created_at,price&order=desc,asc  # 多字段排序

字段选择：
GET /users?fields=id,name,email
```

---

## API版本管理

### 版本策略

#### 1. URL路径版本（推荐）

```
https://api.example.com/v1/users
https://api.example.com/v2/users
```

**优点**：
- 简单直观
- 易于路由和代理
- 支持多版本并行

**缺点**：
- URL变化
- 可能影响缓存策略

#### 2. 请求头版本

```http
GET /users HTTP/1.1
Host: api.example.com
Accept: application/vnd.company.v1+json
```

或

```http
X-API-Version: 1
```

**优点**：
- URL保持不变
- 更符合REST原则

**缺点**：
- 不够直观
- 调试较复杂

#### 3. 查询参数版本

```
https://api.example.com/users?version=1
```

**优点**：
- 简单易用

**缺点**：
- 不够正式
- 容易被忽略

### 版本号规范

- 使用语义化版本：`vMAJOR.MINOR.PATCH`
- API版本通常只显示主版本号：`v1`, `v2`
- 主版本号变更：不兼容的API变更
- 次版本号变更：向后兼容的功能新增
- 修订号变更：向后兼容的问题修复

### 版本生命周期

```
┌─────────────┬─────────────┬─────────────┬─────────────┐
│   开发期     │   稳定期     │   弃用期     │   下线期     │
│  (Alpha)    │  (Stable)   │ (Deprecated) │  (Retired)  │
└─────────────┴─────────────┴─────────────┴─────────────┘
      │              │              │              │
   内部测试       生产可用       通知迁移       停止服务
   6个月         24个月        6个月          -
```

### 弃用策略

#### 响应头通知

```http
HTTP/1.1 200 OK
Deprecation: true
Sunset: Sat, 31 Dec 2024 23:59:59 GMT
Link: </v2/users>; rel="successor-version"
```

#### 响应体通知

```json
{
  "code": 200,
  "message": "success",
  "data": {...},
  "deprecation": {
    "deprecated": true,
    "sunset_date": "2024-12-31",
    "migration_guide": "https://docs.example.com/migration/v1-to-v2"
  }
}
```

### 版本兼容性原则

#### 可兼容变更（不需要升级主版本）

- 新增可选字段
- 新增可选参数
- 新增接口
- 新增枚举值（需谨慎）

#### 不兼容变更（需要升级主版本）

- 删除字段
- 重命名字段
- 修改字段类型
- 修改接口行为
- 修改必填字段
- 修改错误码

---

## API安全设计

### 认证机制

#### 1. OAuth 2.0

```
授权流程：
1. 客户端重定向到授权服务器
2. 用户授权
3. 获取授权码
4. 使用授权码换取访问令牌
5. 使用访问令牌访问资源
```

**令牌类型**：

| 令牌类型 | 说明 | 有效期 |
|---------|------|--------|
| Access Token | 访问令牌 | 短期（1-2小时） |
| Refresh Token | 刷新令牌 | 长期（7-30天） |

#### 2. JWT（JSON Web Token）

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**JWT结构**：
```
Header.Payload.Signature
```

**Payload示例**：
```json
{
  "sub": "user_123",
  "iat": 1705315800,
  "exp": 1705319400,
  "role": "admin"
}
```

#### 3. API Key

```http
X-API-Key: your-api-key-here
```

**适用场景**：
- 服务间调用
- 公开API
- 开发测试环境

### 授权机制

#### RBAC（基于角色的访问控制）

```json
{
  "roles": {
    "admin": ["user:read", "user:write", "user:delete"],
    "editor": ["user:read", "user:write"],
    "viewer": ["user:read"]
  }
}
```

#### 权限检查

```json
{
  "code": 403,
  "message": "权限不足",
  "error": {
    "type": "permission_denied",
    "required_permission": "user:delete"
  }
}
```

### 数据安全

#### 敏感数据保护

- 密码：使用bcrypt/argon2加密存储
- 个人信息：传输时加密，存储时脱敏
- 支付信息：符合PCI DSS标准

#### 数据脱敏

```json
{
  "phone": "138****8888",
  "email": "j***@example.com",
  "id_card": "110***********1234"
}
```

### 安全防护

#### 1. HTTPS强制

```http
Strict-Transport-Security: max-age=31536000; includeSubDomains
```

#### 2. CORS配置

```http
Access-Control-Allow-Origin: https://example.com
Access-Control-Allow-Methods: GET, POST, PUT, DELETE
Access-Control-Allow-Headers: Content-Type, Authorization
Access-Control-Max-Age: 86400
```

#### 3. 限流策略

**响应头**：
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1705315800
```

**限流维度**：
- IP限流
- 用户限流
- 接口限流
- 应用限流

**限流算法**：
- 固定窗口
- 滑动窗口
- 令牌桶
- 漏桶

#### 4. 输入验证

- 参数类型验证
- 参数范围验证
- 参数格式验证（正则）
- SQL注入防护
- XSS防护
- CSRF防护

#### 5. 请求签名

```
签名算法：
1. 按字典序排列参数
2. 拼接参数字符串
3. 加入时间戳和密钥
4. 计算HMAC签名

示例：
sign = HMAC_SHA256(secret_key, sorted_params + timestamp)
```

---

## API文档规范

### 文档结构

```markdown
# API名称

## 概述
API的整体描述和用途

## 基础信息
- 基础URL
- 认证方式
- 编码格式

## 接口列表

### 接口名称

#### 基本信息
- 路径：/api/v1/resource
- 方法：GET/POST/PUT/DELETE
- 描述：接口功能描述

#### 请求参数

| 参数名 | 类型 | 必填 | 位置 | 说明 |
|--------|------|------|------|------|
| id | string | 是 | path | 资源ID |
| name | string | 否 | query | 过滤名称 |

#### 请求示例

#### 响应参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| code | integer | 状态码 |
| data | object | 数据对象 |

#### 响应示例

#### 错误码

| 错误码 | 说明 |
|--------|------|
| 40001 | 参数错误 |
| 40004 | 资源不存在 |

## 公共错误码
## 更新日志
```

### OpenAPI规范（Swagger）

```yaml
openapi: 3.0.0
info:
  title: API文档
  version: 1.0.0
  description: API接口文档

servers:
  - url: https://api.example.com/v1
    description: 生产环境
  - url: https://api-dev.example.com/v1
    description: 测试环境

paths:
  /users:
    get:
      summary: 获取用户列表
      tags:
        - 用户管理
      parameters:
        - name: page
          in: query
          schema:
            type: integer
            default: 1
        - name: size
          in: query
          schema:
            type: integer
            default: 20
      responses:
        '200':
          description: 成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UserListResponse'
        '400':
          description: 参数错误
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'

components:
  schemas:
    User:
      type: object
      properties:
        id:
          type: string
        name:
          type: string
        email:
          type: string
          format: email
    UserListResponse:
      type: object
      properties:
        code:
          type: integer
        message:
          type: string
        data:
          type: object
          properties:
            items:
              type: array
              items:
                $ref: '#/components/schemas/User'
            pagination:
              $ref: '#/components/schemas/Pagination'
    ErrorResponse:
      type: object
      properties:
        code:
          type: integer
        message:
          type: string
        error:
          type: object
    Pagination:
      type: object
      properties:
        page:
          type: integer
        size:
          type: integer
        total:
          type: integer
        total_pages:
          type: integer
```

### 文档最佳实践

1. **保持同步**：文档与代码同步更新
2. **示例丰富**：提供完整的请求/响应示例
3. **错误详尽**：列出所有可能的错误码和解决方案
4. **版本清晰**：标注API版本和变更历史
5. **交互友好**：提供在线测试功能（如Swagger UI）
6. **多语言示例**：提供多种编程语言的调用示例

### 文档工具推荐

| 工具 | 说明 |
|------|------|
| Swagger/OpenAPI | 行业标准API文档规范 |
| Postman | API开发和文档一体化 |
| ApiPost | 国产API文档工具 |
| YApi | 接口管理平台 |
| Knife4j | Swagger增强UI |

---

## 参考资源

- [RESTful API设计指南](https://restfulapi.net/)
- [OpenAPI规范](https://swagger.io/specification/)
- [HTTP状态码](https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Status)
- [OAuth 2.0规范](https://oauth.net/2/)
- [JWT标准](https://jwt.io/)
