# API设计司 自主操作指南 (Autonomous Operation Guide)

> 尚书省 · 工部 · 工部司 · Universal DevOps v5.0
> 自主 API 版本管理与接口契约引擎

## 概述

API设计司（工部司）负责**RESTful API 设计规范制定、OpenAPI 契约文档生成、版本管理策略执行与网关路由配置**。本司是前后端协作的契约中心，确保 API 的稳定性、一致性和可演化性。

### 定位

- **RESTful 规范守护者**：确保所有 API 遵循统一的命名、语义和状态码约定
- **OpenAPI 契约工厂**：自动生成机器可读的 API 规格文档，驱动代码生成和测试
- **版本管理架构师**：制定并执行 API 演化策略，平衡新功能与向后兼容
- **网关路由编排者**：生成 Kong/Apisix/Nginx 网关路由配置

### 目标

1. 所有 API 设计遵循 RESTful 最佳实践，产出 OpenAPI 3.0 标准规范
2. 版本变更平滑过渡，不破坏现有消费者
3. 接口文档始终与实现同步（Doc-as-Code）

## 核心原则

### 原则一：资源导向（Resource-Oriented）
API 围绕名词（资源）设计，而非动词（操作）。URL 表示资源，HTTP 方法表示对资源的操作。

### 原则二：无状态性（Statelessness）
每个请求包含处理所需的所有信息。服务端不在会话间保存客户端上下文。

### 原则三：统一响应格式（Uniform Response）
所有 API 使用一致的响应信封结构，便于客户端统一解析和处理错误。

### 原则四：向后兼容优先（Backward Compatibility First）
新增字段默认可选，废弃字段设置过渡期，破坏性变更必须升级主版本号。

### 原则五：契约即文档（Contract as Documentation）
OpenAPI Spec 是唯一权威的 API 文档，代码实现必须与 Spec 保持一致。

## 自主操作流程

### 阶段一：感知（Perceive）

#### 1.1 需求分析与资源识别

```
输入: 业务需求 / 用户故事 / 数据模型 / 现有API清单
输出: 资源清单 + 操作矩阵 + URL 路由表
```

**操作步骤**：

1. **从业务需求中提取资源**
   - 名词提取法：需求中的每个名词都是候选资源
   - 动词→操作映射：需求中的动词对应 HTTP 方法
   - 关系识别：资源之间的归属/关联关系反映在 URL 嵌套中

2. **资源识别模板**

| 业务描述 | 提取的资源 | CRUD 操作 | 关联资源 |
|----------|-----------|-----------|---------|
| "用户可以创建订单" | Order (订单) | POST /orders | → User (通过 customer_id) |
| "查看订单详情" | Order (订单) | GET /orders/{id} | → OrderItem (嵌套) |
| "修改收货地址" | Address (地址) | PUT /addresses/{id} | → User (所属) |
| "搜索商品" | Product (商品) | GET /products (带查询参数) | → Category (筛选) |
| "取消订单" | Order (订单) | PATCH /orders/{id}/cancel (自定义动作) | — |

3. **现有 API 审计**
   - 扫描现有路由定义文件
   - 识别已注册的所有端点
   - 检测命名不一致、方法误用、状态码不规范等问题

#### 1.2 技术栈感知

```yaml
api_tech_stack_detection:
  framework_detection:
    fastapi:
      files: ["main.py", "routers/", "*.py"]
      router_pattern: "APIRouter"
      dependency_injection: "Depends()"
    express:
      files: ["app.js", "routes/", "*.js"]
      router_pattern: "express.Router()"
      middleware: "app.use()"
    spring_boot:
      files: ["*Controller.java", "*Application.java"]
      annotation_pattern: "@RestController @RequestMapping"
    django_rest:
      files: ["views.py", "urls.py", "serializers.py"]
      pattern: "viewsets.ModelViewSet / APIView"
    gin_echo:
      files: ["*.go", "router.go"]
      pattern: "r.GET / r.POST / r.Group"

  auth_detection:
    jwt: "Authorization: Bearer <token>"
    oauth2: "/oauth/token /authorize"
    api_key: "X-API-Key header"
    session: "Cookie-based session"

  existing_docs:
    swagger_ui: "访问 /docs 或 /swagger"
    openapi_json: "访问 /openapi.json 或 /api-docs"
    postman_collection: "项目根目录或 docs/ 中的 .json 文件"
```

### 阶段二：决策（Decide）

#### 2.1 RESTful 设计规范

##### 2.1.1 资源命名规则

```yaml
naming_conventions:
  url_rules:
    - rule: "使用名词复数"
      good: "/users /orders /products /categories"
      bad: "/getUser /order-list /ProductInfo /get-all-items"
      rationale: "复数表示集合，单数通过 ID 访问具体实例"

    - rule: "使用 kebab-case（短横线分隔）"
      good: "/user-profiles /order-items /shipping-addresses"
      bad: "/userProfiles /order_items /ShippingAddresses"
      rationale: "kebab-case 在 URL 中最易读，RFC 3986 安全字符"

    - rule: "避免动词（除特殊情况）"
      good: "POST /orders (创建) / DELETE /orders/{id} (删除)"
      bad: "/createOrder /deleteOrder?id=1 /getOrdersList"
      exception: "当标准方法无法表达时，可使用 /resource/{id}/actions/action-name"

    - rule: "URL 层级不超过 4 层"
      good: "/orders/{id}/items" (2层资源 + 2层ID)
      bad: "/shops/{shopId}/categories/{catId}/products/{prodId}/reviews/{reviewId}"
      mitigation: "深层关系改用查询参数: /reviews?product_id={prodId}"

    - rule: "避免查询动词作为路径段"
      good: "/users?role=admin (过滤) /users?sort=created_at:desc (排序)"
      bad: "/users/search /users/list /users/filter"

  http_method_semantics:
    GET:
      description: "读取资源（安全、幂等）"
      idempotent: true
      safe: true
      body_allowed: false
      success_response: "200 OK + 资源表示 / 304 Not Modified"
      common_use: "获取列表、获取详情、条件过滤"
    POST:
      description: "创建子资源（非幂等）"
      idempotent: false
      safe: false
      body_allowed: true
      success_response: "201 Created + Location header + 创建的资源"
      common_use: "新建记录、提交表单、触发异步任务"
    PUT:
      description: "全量替换资源（幂等）"
      idempotent: true
      safe: false
      body_allowed: true
      success_response: "200 OK + 更新后的资源 / 204 No Content"
      common_use: "完整更新用户资料、替换配置"
    PATCH:
      description: "部分更新资源（通常幂等，取决于语义）"
      idempotent: "context-dependent"
      safe: false
      body_allowed: true
      success_response: "200 OK + 更新后的资源"
      common_use: "修改密码、更新状态字段、部分字段修改"
    DELETE:
      description: "删除资源（幂等）"
      idempotent: true
      safe: false
      body_allowed: false
      success_response: "204 No Content / 200 OK + 删除确认"
      common_use: "删除记录、取消订阅、移除关联"
```

##### 2.1.2 HTTP 状态码正确使用指南

```yaml
status_code_guide:

  # === 2xx 成功 ===
  success_codes:
    "200 OK":
      usage: "标准成功响应（GET/PATCH/PUT 成功时返回数据）"
      example: "GET /users/123 → { user data }"
    "201 Created":
      usage: "资源创建成功（POST 创建后返回新资源和 Location）"
      headers: "Location: /users/456"
      example: "POST /users → 201 + { new user } + Location: /users/456"
    "202 Accepted":
      usage: "异步处理已接受（任务已入队，尚未完成）"
      body: "{ task_id, status: 'pending', estimated_completion }"
      example: "POST /reports/generate → 202 + task info"
    "204 No Content":
      usage: "成功但无返回体（DELETE/PUT 无需返回数据时）"
      example: "DELETE /users/123 → 204 (空 body)"
    "206 Partial Content":
      usage: "范围请求成功（分页/断点续传）"
      headers: "Content-Range: bytes 0-1023/5000"

  # === 3xx 重定向 ===
  redirect_codes:
    "301 Moved Permanently":
      usage: "永久重定向（旧URL永远迁移到新URL）"
      note: "搜索引擎会更新索引"
    "302 Found":
      usage: "临时重定向（POST 后的重定向慎用，见 303/307）"
    "303 See Other":
      usage: "POST 处理后重定向到 GET 页面（PRG 模式）"
    "304 Not Modified":
      usage: "条件请求未变更（缓存命中，配合 ETag/Last-Modified）"
    "307 Temporary Redirect":
      usage: "临时重定向（保持原始方法和 body）"
    "308 Permanent Redirect":
      usage: "永久重定向（保持原始方法和 body）"

  # === 4xx 客户端错误 ===
  client_error_codes:
    "400 Bad Request":
      usage: "请求语法错误、参数校验失败、语义无法理解"
      response_body: |
        {
          "code": "VALIDATION_ERROR",
          "message": "请求参数验证失败",
          "details": [
            {"field": "email", "message": "邮箱格式无效"},
            {"field": "age", "message": "年龄必须在0-150之间"}
          ],
          "request_id": "req_abc123"
        }
    "401 Unauthorized":
      usage: "未认证（缺少或无效的凭证）"
      response_body: |
        {
          "code": "UNAUTHORIZED",
          "message": "认证信息缺失或无效",
          "details": "请提供有效的 Bearer Token"
        }
      www_authenticate: 'Bearer realm="API", error="invalid_token"'
    "403 Forbidden":
      usage: "已认证但权限不足"
      response_body: |
        {
          "code": "FORBIDDEN",
          "message": "没有权限执行此操作",
          "details": "需要 role:admin 权限"
        }
    "404 Not Found":
      usage: "资源不存在"
      response_body: |
        {
          "code": "NOT_FOUND",
          "message": "请求的资源不存在",
          "details": "User(id=999) not found"
        }
    "405 Method Not Allowed":
      usage: "HTTP 方法不允许（该资源不支持此方法）"
      allow_header: "Allow: GET, POST, DELETE"
    "409 Conflict":
      usage: "资源冲突（唯一约束违反、并发编辑冲突）"
      response_body: |
        {
          "code": "CONFLICT",
          "message": "资源冲突",
          "details": "邮箱 address@example.com 已被注册"
        }
    "422 Unprocessable Entity":
      usage: "语法正确但语义错误（业务逻辑校验失败）"
      difference_from_400: "400是格式问题，422是业务规则问题"
    "429 Too Many Requests":
      usage: "超过速率限制"
      headers: "Retry-After: 60, X-RateLimit-Limit: 100, X-RateLimit-Remaining: 0"

  # === 5xx 服务端错误 ===
  server_error_codes:
    "500 Internal Server Error":
      usage: "服务器内部未知错误"
      action: "记录完整堆栈，返回通用消息给客户端"
      never_expose: "绝不暴露堆栈信息、数据库错误、内部路径"
    "501 Not Implemented":
      usage: "服务器不支持该功能"
    "502 Bad Gateway":
      usage: "上游服务不可用（网关/代理场景）"
    "503 Service Unavailable":
      usage: "服务暂时过载或维护中"
      headers: "Retry-After: 300"
    "504 Gateway Timeout":
      usage: "上游服务响应超时"
```

##### 2.1.3 统一响应信封格式

```yaml
response_envelope:
  # 成功响应
  success_envelope:
    single_resource:
      get_detail: |
        HTTP/1.1 200 OK
        Content-Type: application/json

        {
          "code": "SUCCESS",
          "data": {
            "id": "usr_abc123",
            "email": "user@example.com",
            "nickname": "张三",
            "created_at": "2024-01-15T08:30:00Z"
          },
          "meta": {
            "request_id": "req_xyz789",
            "timestamp": "2024-01-15T10:00:00Z"
          }
        }

    collection_with_pagination: |
      HTTP/1.1 200 OK
      Content-Type: application/json

      {
        "code": "SUCCESS",
        "data": [
          { "id": "usr_001", "email": "a@example.com", ... },
          { "id": "usr_002", "email": "b@example.com", ... }
        ],
        "pagination": {
          "page": 1,
          "size": 20,
          "total": 150,
          "total_pages": 8,
          "has_next": true,
          "has_prev": false
        },
        "meta": {
          "request_id": "req_xyz789",
          "timestamp": "2024-01-15T10:00:00Z"
        }
      }

  # 错误响应
  error_envelope: |
    HTTP/1.1 400 Bad Request
    Content-Type: application/json

    {
      "code": "VALIDATION_ERROR",
      "message": "请求参数验证失败",
      "details": [
        {
          "field": "email",
          "message": "邮箱格式无效",
          "rejected_value": "not-an-email"
        },
        {
          "field": "age",
          "message": "必须在 0-150 之间",
          "rejected_value": -5,
          "constraints": { "min": 0, "max": 150 }
        }
      ],
      "meta": {
        "request_id": "req_xyz789",
        "timestamp": "2024-01-15T10:00:00Z",
        "trace_id": "trace_abc123"
      }
    }

  # 创建成功响应（特殊：返回 Location header）
  created_response: |
    HTTP/1.1 201 Created
    Content-Type: application/json
    Location: /api/v1/users/usr_new456

    {
      "code": "CREATED",
      "data": {
        "id": "usr_new456",
        "email": "new@example.com",
        ...
      },
      "meta": { "request_id": "req_xyz789" }
    }
```

##### 2.1.4 分页/过滤/排序/字段选择标准化

```yaml
query_parameter_conventions:

  pagination:
    style: "cursor-based for infinite scroll, offset-based for admin"
    offset_based:
      page: { type: integer, default: 1, min: 1, description: "页码" }
      size: { type: integer, default: 20, min: 1, max: 100, description: "每页数量" }
      example: "GET /users?page=2&size=50"
    cursor_based:
      cursor: { type: string, description: "上一页最后一条的游标" }
      limit: { type: integer, default: 20, min: 1, max: 100 }
      example: "GET /messages?cursor=eyJpZCI6MTIzfQ&limit=20"
    response_headers:
      link: '<https://api.example.com/users?page=3&size=20>; rel="next", <...>; rel="last"'

  filtering:
    style: "query parameter filters"
    exact_match: "GET /users?status=active&role=admin"
    range_filter: "GET /orders?created_at_gte=2024-01-01&created_at_lt=2024-02-01"
    list_filter: "GET /products?category=electronics,books&status=published"
    search: "GET /users?q=zhangsan&search_fields=email,nickname"
    nested_filter: "GET /orders?customer.address.city=Beijing"

  sorting:
    style: "sort 参数，支持多字段排序"
    single_field: "GET /users?sort=created_at:desc"
    multi_field: "GET /users?sort=status:asc,created_at:desc"
    default_sort: "按 created_at DESC（最新优先）"

  field_selection:
    style: "fields 参数，逗号分隔"
    syntax: "GET /users?fields=id,email,nickname"
    nested: "GET /users/123?fields=id,email,profile.avatar"
    note: "减少传输体积，适用于移动端和网络受限环境"

  include_expansion:
    style: "include 参数，展开关联资源"
    syntax: "GET /orders/456?include=items,customer,address"
    response: "主资源 + include 中指定的关联资源内联返回"
```

#### 2.2 API 版本管理策略

##### 三种版本策略对比与选择

```yaml
versioning_strategies:

  strategy_a_url_path:
    name: "URL Path Versioning"
    pattern: "/api/v{major}/resources"
    examples:
      - "GET /api/v1/users"
      - "GET /api/v2/users"
      - "POST /api/v1/orders"
    pros:
      - "直观明确，URL 即可见版本"
      - "易于在网关层做路由分发"
      - "不同版本可独立部署"
      - "缓存友好（不同URL = 不同缓存键）"
    cons:
      - "URL 变长"
      - "需要维护多套路由代码"
    best_for: "公开 API、需要长期共存多版本的场景"
    recommendation_weight: "★★★★★ (首选)"

  strategy_b_header:
    name: "Header-Based Versioning (Accept / Custom Header)"
    pattern: "Accept: application/vnd.api.v+json;version=2"
    alternatives:
      - "X-API-Version: 2"
      - "Accept-Version: 2"
    pros:
      - "URL 保持简洁干净"
      - "同一资源 URL 不变"
    cons:
      - "不易发现（隐藏在 header 中）"
      - "调试不便（浏览器直接访问看不到版本）"
      - "缓存复杂化（同 URL 不同版本）"
      - "某些 CDN/代理可能不传递自定义头"
    best_for: "内部 API、强工具链支持的团队"
    recommendation_weight: "★★★☆☆"

  strategy_c_backward_compatible:
    name: "No-Breaking Change (向后兼容式演化)"
    pattern: "不显式版本号，所有变更保持向后兼容"
    evolution_rules:
      add_field: "新字段必须可选且有默认值"
      deprecate_field: "标记 deprecated 但不立即移除"
      breaking_change: "升级主版本号（v1 → v2）"
    pros:
      - "最简洁，无需版本管理开销"
      - "客户端零感知平滑升级"
    cons:
      - "难以判断当前 API 版本"
      - "长期累积技术债务"
      - "破坏性变更仍需某种形式的版本标识"
    best_for: "快速迭代的产品初期、内部微服务"
    recommendation_weight: "★★☆☆☆ (仅限早期)"

  # 推荐：混合策略
  recommended_hybrid:
    name: "Path Versioning + 向后兼容原则"
    approach: |
      主版本号放 URL path (/api/v1/, /api/v2/)
      同主版本内遵循向后兼容原则
      小功能增强不升版（新字段可选、新端点增量添加）
    lifecycle:
      v1_active: "当前稳定版，接收 bug fix"
      v2_candidate: "下一版候选，新功能在此开发"
      v1_deprecated: "公告废弃期（建议 6 个月过渡）"
      v1_retired: "停止服务，返回 410 Gone"
```

##### 版本生命周期管理

```yaml
version_lifecycle:

  phases:
    - phase: "Active（活跃）"
      status: "正常服务，推荐新消费者使用"
      support_level: "全量支持（bug fix + security patch）"
      communication: "文档标记为 Current / Latest"

    - phase: "Maintenance（维护）"
      status: "不再接受新功能，仅修复严重 bug 和安全漏洞"
      trigger: "发布新版后自动进入此阶段"
      duration: "建议 12 个月"
      communication: "文档标记为 Deprecated，引导迁移到新版本"

    - phase: "Deprecated（废弃）"
      status: "公告即将退役，强烈建议迁移"
      duration: "建议 6 个月"
      actions:
        - "所有响应增加 Deprecation 警告头"
        - "Sunset header: Sunset: Sat, 31 Dec 2025 23:59:59 GMT"
        - "Link header 指向迁移指南"
      headers:
        Warning: '299 - "Deprecated API Version"'
        Deprecation: "true"
        Sunset: "Sat, 31 Dec 2025 23:59:59 GMT"
        Link: '</api/docs/migration-v1-to-v2>; rel="deprecation"'

    - phase: "Retired（退役）"
      status: "停止服务"
      response: "410 Gone + 迁移指引"
      response_body: |
        {
          "code": "VERSION_RETIRED",
          "message": "API v1 已于 2025-12-31 退役",
          "migration_guide": "https://docs.example.com/api/migration-v1-to-v2",
          "supported_versions": ["/api/v2", "/api/v3"]
        }
```

#### 2.3 OpenAPI 3.0 规范自主生成

##### 完整 OpenAPI 3.0 规范示例

```yaml
openapi: 3.0.3
info:
  title: E-Commerce API
  description: |
    电商系统 RESTful API
    ## 认证方式
    - **Bearer Token**: 通过 `Authorization: Bearer <token>` 头传递
    ## 速率限制
    - 默认: 100 requests/min
    - 认证用户: 1000 requests/min
  version: 1.0.0
  contact:
    name: API Support
    email: api-support@example.com
  license:
    name: MIT
    url: https://opensource.org/licenses/MIT

servers:
  - url: https://api.example.com/v1
    description: Production
  - url: https://staging-api.example.com/v1
    description: Staging
  - url: http://localhost:8000/v1
    description: Local Development

tags:
  - name: Users
    description: 用户管理
  - name: Orders
    description: 订单管理
  - name: Products
    description: 商品管理
  - name: Auth
    description: 认证授权

paths:
  /users:
    get:
      tags: [Users]
      summary: 获取用户列表
      description: 分页获取用户列表，支持按状态和角色过滤
      operationId: listUsers
      parameters:
        - name: page
          in: query
          schema:
            type: integer
            minimum: 1
            default: 1
        - name: size
          in: query
          schema:
            type: integer
            minimum: 1
            maximum: 100
            default: 20
        - name: status
          in: query
          description: 按状态过滤
          schema:
            $ref: '#/components/schemas/UserStatus'
        - name: sort
          in: query
          description: 排序字段
          schema:
            type: string
            enum: [created_at, nickname]
            default: created_at
        - name: fields
          in: query
          description: 选择返回字段
          schema:
            type: string
            example: "id,email,nickname"
      responses:
        '200':
          description: 用户列表
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaginatedUserResponse'
              examples:
                normal:
                  summary: 正常响应
                  value:
                    code: SUCCESS
                    data:
                      - id: usr_001
                        email: alice@example.com
                        nickname: Alice
                        status: active
                        created_at: '2024-01-01T00:00:00Z'
                      - id: usr_002
                        email: bob@example.com
                        nickname: Bob
                        status: active
                        created_at: '2024-01-02T00:00:00Z'
                    pagination:
                      page: 1
                      size: 20
                      total: 150
                      total_pages: 8
                      has_next: true
                      has_prev: false
                    meta:
                      request_id: req_abc123
        '401':
          $ref: '#/components/responses/Unauthorized'
        '429':
          $ref: '#/components/responses/RateLimited'
      security:
        - bearerAuth: []

    post:
      tags: [Users]
      summary: 创建用户
      operationId: createUser
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateUserRequest'
            examples:
              normal:
                summary: 创建普通用户
                value:
                  email: "newuser@example.com"
                  password: "SecurePass123!"
                  nickname: "NewUser"
      responses:
        '201':
          description: 用户创建成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UserResponse'
          headers:
            Location:
              description: 新建用户的 URI
              schema:
                type: string
                format: uri
                example: /v1/users/usr_new001
        '400':
          $ref: '#/components/responses/BadRequest'
        '409':
          description: 邮箱已被注册
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
              example:
                code: CONFLICT
                message: 资源冲突
                details: "邮箱 newuser@example.com 已被注册"

  /users/{userId}:
    get:
      tags: [Users]
      summary: 获取用户详情
      operationId: getUserById
      parameters:
        - name: userId
          in: path
          required: true
          schema:
            type: string
            format: uuid
            example: usr_abc123
      responses:
        '200':
          description: 用户详情
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UserResponse'
        '404':
          $ref: '#/components/responses/NotFound'

    put:
      tags: [Users]
      summary: 全量更新用户信息
      operationId: updateUser
      parameters:
        - name: userId
          in: path
          required: true
          schema:
            type: string
            format: uuid
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/UpdateUserRequest'
      responses:
        '200':
          description: 更新成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UserResponse'
        '404':
          $ref: '#/components/responses/NotFound'

    delete:
      tags: [Users]
      summary: 删除用户
      operationId: deleteUser
      parameters:
        - name: userId
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '204':
          description: 删除成功
        '404':
          $ref: '#/components/responses/NotFound'

  /orders:
    get:
      tags: [Orders]
      summary: 获取订单列表
      operationId: listOrders
      parameters:
        - name: page
          in: query
          schema: { type: integer, default: 1, minimum: 1 }
        - name: size
          in: query
          schema: { type: integer, default: 20, maximum: 100 }
        - name: status
          in: query
          schema:
            $ref: '#/components/schemas/OrderStatus'
        - name: customer_id
          in: query
          description: 按客户ID过滤
          schema:
            type: string
            format: uuid
        - name: created_at_gte
          in: query
          schema:
            type: string
            format: date-time
        - name: sort
          in: query
          schema:
            type: string
            enum: [created_at, total_amount]
            default: created_at
        - name: include
          in: query
          description: 展开关联资源
          schema:
            type: array
            items:
              type: string
              enum: [items, customer, shipping_address]
      responses:
        '200':
          description: 订单列表
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaginatedOrderResponse'

    post:
      tags: [Orders]
      summary: 创建订单
      operationId: createOrder
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateOrderRequest'
      responses:
        '201':
          description: 订单创建成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/OrderResponse'
          headers:
            Location:
              schema:
                type: string
                format: uri

  /orders/{orderId}:
    parameters:
      - name: orderId
        in: path
        required: true
        schema:
          type: string
          format: uuid
    get:
      tags: [Orders]
      summary: 获取订单详情
      operationId: getOrderById
      parameters:
        - $ref: '#/components/parameters/OrderId'
      responses:
        '200':
          description: 订单详情
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/OrderDetailResponse'
    patch:
      tags: [Orders]
      summary: 部分更新订单（如取消订单）
      operationId: updateOrderStatus
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                status:
                  $ref: '#/components/schemas/OrderStatus'
                cancel_reason:
                  type: string
                  maxLength: 500
              required: [status]
      responses:
        '200':
          description: 更新成功
        '409':
          description: 状态转换非法
        '422':
          description: 业务规则校验失败

  /auth/login:
    post:
      tags: [Auth]
      summary: 用户登录
      operationId: login
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [email, password]
              properties:
                email:
                  type: string
                  format: email
                password:
                  type: string
                  format: password
                  writeOnly: true
      responses:
        '200':
          description: 登录成功
          content:
            application/json:
              schema:
                type: object
                properties:
                  access_token:
                    type: string
                    description: JWT access token
                  token_type:
                    type: string
                    default: Bearer
                  expires_in:
                    type: integer
                    description: Token 有效期（秒）
                  refresh_token:
                    type: string
        '401':
          description: 邮箱或密码错误

components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
      description: JWT Bearer Token 认证

  schemas:
    User:
      type: object
      properties:
        id:
          type: string
          format: uuid
          example: usr_abc123
        email:
          type: string
          format: email
        nickname:
          type: string
          maxLength: 100
        status:
          $ref: '#/components/schemas/UserStatus'
        avatar_url:
          type: string
          format: uri
          nullable: true
        created_at:
          type: string
          format: date-time
        updated_at:
          type: string
          format: date-time
      required: [id, email, status, created_at]

    UserStatus:
      type: string
      enum: [active, suspended, banned]
      description: 用户账户状态

    CreateUserRequest:
      type: object
      required: [email, password]
      properties:
        email:
          type: string
          format: email
        password:
          type: string
          format: password
          minLength: 8
          maxLength: 128
          description: 密码至少包含大小写字母和数字
        nickname:
          type: string
          maxLength: 100

    UpdateUserRequest:
      type: object
      properties:
        nickname:
          type: string
          maxLength: 100
        avatar_url:
          type: string
          format: uri
          nullable: true

    OrderStatus:
      type: string
      enum: [pending, processing, shipped, delivered, cancelled]

    CreateOrderRequest:
      type: object
      required: [items, shipping_address_id]
      properties:
        items:
          type: array
          minItems: 1
          items:
            type: object
            required: [product_id, quantity]
            properties:
              product_id:
                type: string
                format: uuid
              quantity:
                type: integer
                minimum: 1
        shipping_address_id:
          type: string
          format: uuid
        coupon_code:
          type: string
          nullable: true

    ErrorResponse:
      type: object
      required: [code, message]
      properties:
        code:
          type: string
          enum: [VALIDATION_ERROR, UNAUTHORIZED, FORBIDDEN, NOT_FOUND,
                 CONFLICT, RATE_LIMITED, INTERNAL_ERROR]
        message:
          type: string
        details:
          oneOf:
            - type: string
            - type: array
              items:
                type: object
                properties:
                  field:
                    type: string
                  message:
                    type: string
                  rejected_value: true
        meta:
          $ref: '#/components/schemas/ResponseMeta'

    ResponseMeta:
      type: object
      properties:
        request_id:
          type: string
          description: 请求追踪ID，用于排查问题
        timestamp:
          type: string
          format: date-time
        trace_id:
          type: string

    PaginatedUserResponse:
      allOf:
        - $ref: '#/components/schemas/SuccessEnvelope'
        - type: object
          properties:
            data:
              type: array
              items:
                $ref: '#/components/schemas/User'
            pagination:
              $ref: '#/components/schemas/Pagination'

    SuccessEnvelope:
      type: object
      required: [code, data, meta]
      properties:
        code:
          type: string
          enum: [SUCCESS, CREATED]
        meta:
          $ref: '#/components/schemas/ResponseMeta'

    Pagination:
      type: object
      required: [page, size, total, total_pages, has_next, has_prev]
      properties:
        page:
          type: integer
          example: 1
        size:
          type: integer
          example: 20
        total:
          type: integer
          example: 150
        total_pages:
          type: integer
          example: 8
        has_next:
          type: boolean
        has_prev:
          type: boolean

  responses:
    BadRequest:
      description: 请求参数错误
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'
    Unauthorized:
      description: 未认证
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'
    Forbidden:
      description: 权限不足
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'
    NotFound:
      description: 资源不存在
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'
    RateLimited:
      description: 超过速率限制
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'
      headers:
        Retry-After:
          schema:
            type: integer
            example: 60
        X-RateLimit-Limit:
          schema:
            type: integer
        X-RateLimit-Remaining:
          schema:
            type: integer

  parameters:
    OrderId:
      name: orderId
      in: path
      required: true
      description: 订单UUID
      schema:
        type: string
        format: uuid
```

### 阶段三：Execute

#### 3.1 API 网关路由配置生成

##### Kong 网关配置

```yaml
# kong-declarative-config.yaml
_format_version: "3.0"

services:
  # 用户服务
  - name: user-service
    url: http://user-service:8000
    routes:
      - name: users-route
        paths:
          - /v1/users
        methods:
          - GET
          - POST
        strip_path: false
        plugins:
          - name: rate-limiting
            config:
              minute: 100
              policy: local
          - name: key-auth
          - name: cors
            config:
              origins:
                - "*"
              methods:
                - GET
                - POST
                - PUT
                - PATCH
                - DELETE
              headers:
                - Accept
                - Authorization
                - Content-Type
              exposed_headers:
                - X-Request-ID
                - X-RateLimit-Remaining
              credentials: true
              max_age: 3600

      - name: user-by-id-route
        paths:
          - /v1/users/~$
        regex_priority: 1
        methods:
          - GET
          - PUT
          - DELETE
        strip_path: false

  # 订单服务
  - name: order-service
    url: http://order-service:8000
    routes:
      - name: orders-route
        paths:
          - /v1/orders
        strip_path: false
        plugins:
          - name: rate-limiting
            config:
              minute: 200
              policy: local
          - name: key-auth
          - name: request-transformer
            config:
              add:
                headers:
                  - X-Source:kong-gateway

consumers:
  - username: app-frontend
    keyauth_credentials:
      - key: frontend-key-xxx
    plugins:
      - name: rate-limiting
        config:
          minute: 1000
          policy: local
  - username: third-party-integration
    keyauth_credentials:
      - key: partner-key-yyy
    plugins:
      - name: rate-limiting
        config:
          minute: 50
          policy: local
      - name: ip-restriction
        config:
          allow:
            - 203.0.113.0/24
```

##### APISix 网关配置

```json
{
  "routes": [
    {
      "id": "route-users-list",
      "uri": "/v1/users",
      "methods": ["GET", "POST"],
      "plugins": {
        "limit-count": {
          "count": 100,
          "time_window": 60,
          "rejected_code": 429,
          "key_type": "var",
          "key": "consumer_name"
        },
        "key-auth": {},
        "cors": {
          "allow_origins": ["*"],
          "allow_methods": ["GET", "POST", "PUT", "PATCH", "DELETE"],
          "allow_headers": ["Authorization", "Content-Type"],
          "expose_headers": ["X-Request-ID"],
          "max_age": 3600
        }
      },
      "upstream": {
        "type": "roundrobin",
        "nodes": {
          "user-service:8000": 1
        }
      }
    },
    {
      "id": "route-orders",
      "uri": "/v1/orders/*",
      "methods": ["GET", "POST", "PATCH"],
      "plugins": {
        "limit-count": {
          "count": 200,
          "time_window": 60
        },
        "key-auth": {},
        "proxy-rewrite": {
          "regex_uri": ["^/v1/orders/(.*)", "/$1"]
        }
      },
      "upstream": {
        "type": "roundrobin",
        "nodes": {
          "order-service:8000": 1
        }
      }
    }
  ],
  "consumers": [
    {
      "username": "app-frontend",
      "plugins": {
        "key-auth": {
          "key": "frontend-key-xxx"
        }
      }
    }
  ]
}
```

##### Nginx 反向代理配置

```nginx
# /etc/nginx/conf.d/api-gateway.conf

# 定义上游服务
upstream user_service {
    server user-service:8000;
    keepalive 32;
}

upstream order_service {
    server order-service:8000;
    keepalive 32;
}

# 速率限制区域
limit_req_zone $binary_remote_addr zone=general_limit:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=auth_limit:10m rate=5r/s;

# API 网关入口
server {
    listen 80;
    server_name api.example.com;

    # 通用安全头
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # CORS
    add_header Access-Control-Allow-Origin * always;
    add_header Access-Control-Allow-Methods "GET, POST, PUT, PATCH, DELETE, OPTIONS" always;
    add_header Access-Control-Allow-Headers "Authorization, Content-Type, X-Request-ID" always;
    add_header Access-Control-Max-Age 3600 always;

    if ($request_method = OPTIONS) {
        return 204;
    }

    # === 用户服务路由 ===
    location ~ ^/v1/users/?$ {
        limit_req zone=general_limit burst=20 nodelay;
        proxy_pass http://user_service/v1/users;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Request-ID $request_id;
        proxy_connect_timeout 5s;
        proxy_read_timeout 30s;
    }

    location ~ ^/v1/users/(?<user_id>[^/]+) {
        limit_req zone=general_limit burst=20 nodelay;
        proxy_pass http://user_service/v1/users/$user_id;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Request-ID $request_id;
    }

    # === 订单服务路由 ===
    location ~ ^/v1/orders {
        limit_req zone=general_limit burst=30 nodelay;
        proxy_pass http://order_service;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Request-ID $request_id;
        proxy_connect_timeout 5s;
        proxy_read_timeout 60s;
    }

    # === 认证路由（更高频率限制）===
    location ~ ^/v1/auth {
        limit_req zone=auth_limit burst=10 nodelay;
        proxy_pass http://user_service/v1/auth;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # === 默认拒绝 ===
    location / {
        return 404 '{"code":"NOT_FOUND","message":"Endpoint not found"}';
        default_type application/json;
    }

    # 错误页面自定义
    error_page 429 = @rate_limited;
    error_page 500 502 503 504 = @server_error;

    location @rate_limited {
        default_type application/json;
        return 429 '{"code":"RATE_LIMITED","message":"Too many requests","meta":{"retry_after":60}}';
    }

    location @server_error {
        default_type application/json;
        return 500 '{"code":"INTERNAL_ERROR","message":"Internal server error"}';
    }
}
```

#### 3.2 限流策略

```yaml
rate_limiting_strategies:

  token_bucket:
    name: "令牌桶算法"
    principle: "以恒定速率填充令牌桶，每次请求消耗一个令牌"
    params:
      bucket_size: "桶容量（突发上限）"
      refill_rate: "令牌填充速率（每秒/每分钟）"
    config_example_kong: |
      plugin: rate-limiting
      config:
        policy: redis       # 分布式限流
        redis_host: redis
        redis_port: 6379
        second: 10          # 每秒10个请求
        burst: 20           # 允许突发20个
        continued: true     # 突发消耗后继续按速率限制
    use_case: "保护下游服务免受突发流量冲击"
    pros: "允许适度突发，平滑处理波动"
    cons: "需要 Redis 存储状态"

  sliding_window:
    name: "滑动窗口算法"
    principle: "统计最近时间窗口内的请求数"
    params:
      window_size: "窗口大小（秒）"
      max_requests: "窗口内最大请求数"
    config_example_apisix: |
      plugin: limit-count
      config:
        count: 100
        time_window: 60     # 60秒窗口内最多100次
        rejected_code: 429
        key_type: "var_combination"
        key: "consumer_name, remote_addr"
    use_case: "精确控制单位时间内的总请求数"
    pros: "精确控制，无突发穿透"
    cons: "不支持突发容忍"

  fixed_window:
    name: "固定窗口算法"
    principle: "将时间划分为固定间隔，每个窗口独立计数"
    params:
      window_interval: "窗口间隔（秒）"
      limit_per_window: "每个窗口的限制数"
    config_example_nginx: |
      limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
      limit_req zone=api_limit burst=20 nodelay;
    use_case: "简单场景的轻量级限流"
    pros: "实现简单，内存占用低"
    cons: "窗口边界处可能出现 2x 流量突刺"

  # 限流层级建议
  tiered_rate_limits:
    global:
      scope: "整个 API 网关"
      limit: "10000 req/s"
      purpose: "防止 DDoS 和系统级过载"
    per_consumer:
      scope: "每个 API Key / Consumer"
      limits:
        anonymous: "60 req/min"
        authenticated_user: "300 req/min"
        premium_user: "1000 req/min"
        internal_service: "5000 req/min"
      purpose: "公平分配资源，防止滥用"
    per_endpoint:
      scope: "单个端点"
      examples:
        "POST /auth/login": "5 req/min"         # 防暴力破解
        "POST /users": "20 req/min"             # 防批量注册
        "GET /orders": "120 req/min"            # 正常业务
        "POST /orders": "30 req/min"            # 写操作更严格
      purpose: "保护敏感和高成本端点"
```

### 阶段四：Verify

#### 4.1 API 合规性检查

```yaml
api_compliance_checklist:

  naming:
    - "所有 URL 使用名词复数 ✅"
    - "URL 使用 kebab-case ✅"
    - "URL 层级 ≤ 4 层 ✅"
    - "无查询动词出现在路径中 ✅"

  http_methods:
    - "GET 用于读取（无副作用）✅"
    - "POST 用于创建（非幂等）✅"
    - "PUT 用于全量替换（幂等）✅"
    - "PATCH 用于部分更新 ✅"
    - "DELETE 用于删除（幂等）✅"
    - "无使用 GET 修改数据的端点 ❌"

  status_codes:
    - "2xx 正确用于成功场景 ✅"
    - "4xx 正确区分各类客户端错误 ✅"
    - "5xx 不暴露内部细节 ✅"
    - "401 vs 403 区分正确（认证 vs 授权）✅"
    - "409 用于冲突场景 ✅"
    - "422 用于业务逻辑校验失败 ✅"

  response_format:
    - "所有响应使用统一信封格式 ✅"
    - "错误响应包含 code + message + details ✅"
    - "列表响应包含分页信息 ✅"
    - "创建响应包含 Location header ✅"

  authentication:
    - "敏感端点需要认证 ✅"
    - "Token 过期返回 401 + 明确提示 ✅"
    - "公共端点正确标注 ✅"

  documentation:
    - "OpenAPI Spec 与实际实现一致 ✅"
    - "每个端点有 summary 和 description ✅"
    - "所有参数有 schema 定义 ✅"
    - "错误响应有示例 ✅"
```

#### 4.2 向后兼容性保障检查

```yaml
backward_compatibility_checklist:

  adding_features:
    new_endpoint:
      impact: "无影响（纯增量）"
      check: "✅ 新端点不影响已有消费者"
    new_optional_field:
      impact: "无影响（旧客户端忽略未知字段）"
      check: "✅ 新字段有默认值且为 optional"
      caution: "确保序列化器不会因未知字段报错"
    new_query_param:
      impact: "无影响（旧请求不含新参数）"
      check: "✅ 新参数有合理默认值"

  changing_existing:
    making_required_field_optional:
      impact: "向后兼容 ✅"
      check: "旧客户端仍然提供该字段，不会出错"
    relaxing_validation:
      impact: "向后兼容 ✅"
      check: "扩大了合法输入范围"
    expanding_enum_values:
      impact: "⚠️ 可能影响（如果客户端硬编码枚举值）"
      check: "通知消费者；考虑新增值而非修改现有值"

  breaking_changes_requiring_version_bump:
    removing_field:
      severity: "🔴 BREAKING"
      mitigation: "先标记 deprecated，保留 ≥ 1 个版本周期"
    making_optional_field_required:
      severity: "🔴 BREAKING"
      mitigation: "新版本端点，旧版本并行运行"
    changing_field_type:
      severity: "🔴 BREAKING"
      mitigation: "新类型用新名称，保留旧字段过渡"
    changing_response_structure:
      severity: "🔴 BREAKING"
      mitigation: "新版本端点"
    removing endpoint:
      severity: "🔴 BREAKING"
      mitigation: "返回 410 Gone + 迁移指引"
    changing authentication_method:
      severity: "🔴 BREAKING"
      mitigation: "充分预告 + 并行运行新旧方案"
```

### 阶段五：Record

#### 5.1 API 变更日志

```markdown
# API Changelog

## [v1.2.0] - 2024-02-01

### Added
- `GET /users/me` — 获取当前登录用户信息 (#142)
- `PATCH /users/{id}/password` — 修改密码 (#145)
- `GET /orders` 新增 `include` 参数支持展开关联资源 (#148)
- `Order` 响应新增 `payment_method` 字段（optional）(#150)

### Changed
- `/orders` 分页默认 size 从 10 改为 20 (#147)
- 错误响应 `details` 字段类型从 string 改为 union[string, array] (#149)

### Deprecated
- `GET /users/profile` 将于 v2.0 移除，请迁移到 `GET /users/me` (#143)
  - Sunset: 2024-06-30
  - Migration Guide: /docs/migration/profile-to-me

### Security
- 修复 `/auth/login` 缺少暴力破解限流的问题 (#146)
- Bearer Token 最小长度要求从 10 增加到 32 (#144)

---

## [v1.1.0] - 2024-01-15

### Added
- 订单管理完整 CRUD (#120-130)
- `POST /orders` 创建订单 (#121)
- `GET /orders/{id}` 获取订单详情 (#122)
- `PATCH /orders/{id}/cancel` 取消订单 (#126)
- OpenAPI 3.0 规范文档 (#135)
```

## 典型自主场景

### 场景1：为新业务模块设计完整 RESTful API

**输入**: "设计库存管理模块的 API"

**自主流程**:

1. **感知**：识别资源（Warehouse/ProductStock/StockMovement/InventoryAlert）→ 分析 CRUD 需求 → 确定关联关系
2. **决策**：
   - URL 设计：`/warehouses`, `/warehouses/{id}/products`, `/stock-movements`, `/inventory-alerts`
   - HTTP 方法映射：标准 CRUD + 特殊动作（如 `POST /stock-movements/adjust` 手动调整库存）
   - 版本策略：纳入 `/api/v1/` 统一前缀
3. **执行**：生成完整的 OpenAPI 3.0 YAML → 生成 Kong 路由配置 → 生成统一响应 DTO
4. **验证**：RESTful 规范检查全部通过 → OpenAPI lint 无错误
5. **记录**：输出 API Changelog 条目 + Swagger UI 可预览

### 场景2：API 版本升级（v1 → v2）

**输入**: "订单 API 需要重大重构，设计 v2 方案"

**自主流程**:

1. **感知**：审计 v1 所有端点 → 识别需要 breaking change 的点 → 收集消费者反馈
2. **决策**：
   - v2 采用全新 URL 前缀 `/api/v2/orders`
   - v1 进入 Maintenance 阶段，标记 Deprecated
   - 关键变更：响应结构扁平化、引入 cursor 分页、新增 HATEOAS links
3. **执行**：
   - 生成 v2 OpenAPI Spec
   - 配置网关同时路由 v1 和 v2
   - v1 端点添加 Deprecation header
4. **验证**：v1 消费者不受影响，v2 新消费者可接入
5. **记录**：完整的 Migration Guide + Sunset 时间线

### 场景3：API 安全加固巡检

**输入**: 定期安全审计模式

**自主流程**:

1. **感知**：扫描所有端点的安全配置 → 发现 3 个问题：
   - `/auth/login` 无频率限制（暴力破解风险）
   - `/users` POST 端点缺少速率限制（批量注册风险）
   - 错误响应偶尔泄露内部堆栈信息
2. **决策**：P0 优先修复安全问题
3. **执行**：
   - 登录端点添加 5/min 限制
   - 注册端点添加 20/min 限制
   - 全局错误处理器改为统一格式，剥离内部细节
4. **验证**：安全扫描通过，限流生效
5. **记录**：Security Advisory 文档

## 决策框架

### API 设计决策树

```
需要设计什么类型的 API?
├── CRUD 资源操作?
│   └── 标准 RESTful: GET/POST/PUT/PATCH/DELETE + /resources/{id}
│
├── 异步长耗时操作?
│   ├── 返回 202 Accepted + task_id
│   └── 提供 GET /tasks/{task_id} 查询进度
│
├── 文件上传?
│   ├── 小文件 (< 5MB)? → multipart/form-data 直接上传
│   ├── 大文件? → 预签名URL / 分片上传 / 断点续传
│   └── 返回文件资源 URL（非 base64 内嵌）
│
├── 批量操作?
│   ├── 批量创建? → POST /resources/batch (body: array)
│   ├── 批量删除? → DELETE /resources?ids=id1,id2,id3
│   └── 批量更新? → PATCH /resources/batch (body: array of {id, changes})
│
├── 搜索/过滤?
│   ├── 简单过滤? → Query parameters (?status=active&type=premium)
│   ├── 全文搜索? → POST /search (body: JSON query DSL)
│   └── 高级搜索? → 独立搜索端点 + Facet/Aggregation 支持
│
├── 实时/流式数据?
│   ├── SSE (Server-Sent Events)? → text/event-stream
│   ├── WebSocket? → 升级协议
│   └── 长轮询? → 不推荐（优先选 SSE/WebSocket）
│
└── Webhook 回调?
    ├── 注册: POST /webhooks (注册回调 URL)
    ├── 验证: 签名验证 + 幂等 key
    └── 重试: 指数退避重试策略
```

### HTTP 方法选择速查表

| 操作意图 | 方法 | URL 示例 | 是否幂等 | 是否安全 |
|---------|------|---------|---------|---------|
| 列出资源 | GET | /users | ✅ | ✅ |
| 获取详情 | GET | /users/123 | ✅ | ✅ |
| 创建资源 | POST | /users | ❌ | ❌ |
| 全量替换 | PUT | /users/123 | ✅ | ❌ |
| 部分更新 | PATCH | /users/123 | ⚠️ | ❌ |
| 删除资源 | DELETE | /users/123 | ✅ | ❌ |
| 取消订单 | PATCH | /orders/456/cancel | ⚠️ | ❌ |
| 发布文章 | PATCH | /articles/789/publish | ⚠️ | ❌ |

## 安全与治理

### API 安全红线

1. **绝不在 URL 中传递敏感信息**：Token、密码、PII 不出现于 URL（会被日志记录）
2. **绝不明文传输敏感数据**：生产环境强制 HTTPS（HSTS + TLS 1.2+）
3. **绝不信任客户端输入**：所有输入必须经过校验和清洗（防注入）
4. **绝不暴露内部细节**：错误响应不包含堆栈、SQL、内部路径、IP
5. **绝不过度授权**：遵循最小权限原则（ Principle of Least Privilege）
6. **忽略认证的端点必须有明确理由**：并记录在安全审计中

### 安全 Checklist

```yaml
security_requirements:
  transport:
    - "HTTPS 强制（生产环境）"
    - "HSTS header: max-age=31536000; includeSubDomains"
    - "TLS 1.2+（推荐 1.3）"

  authentication:
    - "JWT 过期时间 ≤ 15min（access token）"
    - "Refresh token 可撤销"
    - "Token 黑名单机制（登出即时生效）"
    - "密码存储使用 bcrypt/scrypt/argon2（cost factor ≥ 12）"

  authorization:
    - "基于 RBAC 的细粒度权限控制"
    - "资源级权限（用户只能操作自己的数据）"
    - "Admin 操作需要二次验证（MFA）"

  input_validation:
    - "服务端校验是唯一可信的校验（前端校验仅为 UX）"
    - "SQL 参数化查询（杜绝 SQL 注入）"
    - "XSS 防护：输出编码 + CSP header"
    - "CSRF 防护：SameSite Cookie + CSRF Token"
    - "上传文件类型白名单 + 大小限制 + 病毒扫描"

  rate_limiting:
    - "全局、按消费者、按端点三级限流"
    - "认证端点更严格限制（防暴力破解）"
    - "限流超出返回 429 + Retry-After"

  audit_logging:
    - "所有写操作记录审计日志"
    - "日志包含：who, when, what, from_where"
    - "日志保留 ≥ 90 天"
```

### 权限分级

| 操作等级 | 需要审批 | 自主执行范围 |
|----------|---------|-------------|
| 只读分析 | 否 | API 文档生成、合规检查、度量报告 |
| 新增端点 | 建议 | 新增非破坏性端点（含 OpenAPI Spec） |
| 修改响应格式 | 必须 | 任何可能影响消费者的响应结构变更 |
| 废弃端点 | 必须 | 标记废弃 + 设定 Sunset 时间 |
| 删除端点 | 必须 | 必须经过完整的退役流程 |
| 认证/授权变更 | 必须 | 任何安全相关配置变更 |
| 网关配置变更 | 必须 | 生产环境网关路由/插件变更 |

## 协作关系

### 上游依赖

| 上游司 | 协作内容 | 接口方式 |
|--------|---------|---------|
| **数据库设计司** (database_design_si) | 数据模型驱动 API 资源和字段设计 | 接收 ER 图 / Schema |
| **UI/UX设计司** (uiux_design_si) | 前端交互需求驱动 API 响应结构 | 接收组件规格 / 交互说明 |
| **产品规划司** | 业务需求和用户故事 | 接收 PRD / User Stories |

### 下游输出

| 下游消费者 | 输出物 | 格式 |
|------------|--------|------|
| 前端团队 | API Client SDK / TypeScript Types | OpenAPI Codegen |
| 后端开发 | Router + Controller + DTO 骨架代码 | 框架特定代码 |
| 测试司 | API 测试用例（基于 OpenAPI） | Postman Collection / Jest |
| DevOps司 | 网关配置 + CI/CD Pipeline | Kong/YAML / Nginx/Conf |
| 文档司 | API Reference Documentation | Markdown / Swagger UI |

---

## 🤝 v5.1 增强：Agency Agent 协作指南

### 可调用的 Agency Agents

| Agent 名称 | 所属部门 | 协作模式 | 适用场景 |
|-----------|---------|---------|---------|
| Backend Architect | Development Division | 架构→实现 | API 分层架构设计、微服务边界划分、接口契约定义 |
| Data Engineer | Data Division | 数据→管线 | API 响应数据结构设计、数据聚合接口、实时数据推送 |

### Agent 协作工作流

1. **资源识别阶段**：本司完成 RESTful 资源识别和 URL 设计后，Backend Architect 审核分层架构合理性（Controller → Service → Repository）
2. **Schema 定义阶段**：Data Engineer 参与 API 响应结构设计，确保数据字段与下游数据仓库/BI系统的兼容性
3. **版本管理阶段**：Backend Architect 评估 Breaking Change 影响范围，制定向后兼容策略
4. **网关配置阶段**：两个 Agent 共同审核网关路由配置的正确性和安全性

### 典型协作场景

- **场景一：新业务模块 API 全套设计** — 本司设计资源模型和 OpenAPI Spec → Backend Architect 审核分层架构并补充内部服务间接口 → Data Engineer 设计聚合数据API → 输出完整的 API 设计文档 + 网关配置 + 版本策略
- **场景二：API v2 重构** — 本司审计 v1 所有端点 → Backend Architect 设计新的服务边界（按 DDD 划分 Bounded Context）→ Data Engineer 重新设计响应结构以支持更灵活的数据消费 → 输出 v2 OpenAPI Spec + Migration Guide

---

## 🏗️ v5.1 增强：Harness 工程实践

### 相关 Harness 模块

- **CD 流水线 — API Version Management**：API 版本发布纳入 CD 流水线管理，支持多版本并行运行和渐进式流量切换
- **Security Testing Orchestration (STO)**：API 安全扫描自动化——包括 OWASP Top 10 检测、Auth/NZ 权限验证、Payload Fuzzing 测试
- **Feature Flags**：用于 API 新字段的灰度发布，控制新响应字段对不同消费者的可见性

### 实践指南

1. **CD 驱动的 API 版本发布**：每次 API 版本升级（尤其是 breaking change）通过 Harness CD 流水线的 `api-version-publish` stage 执行。流程：(1) 新版本 API 部署到独立环境 → (2) 自动运行 Regression Test Suite（基于 OpenAPI Spec 生成）→ (3) 网关层面逐步切量（1% → 10% → 50% → 100%）→ (4) 全量后标记旧版本 Deprecated。
2. **STO API 安全扫描门禁**：在 Harness STO 中配置 API 安全扫描流水线，每次 OpenAPI Spec 变更后自动执行：(1) SAST — 扫描 API Handler 代码的安全漏洞 → (2) DAST — 对 staging 环境的 API 端点进行模糊测试 → (3) SCA — 检测依赖库已知 CVE → (4) API Specific — SQL Injection/XSS/Broken Authentication 等 OWASP Top 10 专项检测。任何 HIGH/CRITICAL 级别发现阻断发布。
3. **Feature Flags 控制的 API 字段灰度**：新增的 API 响应字段或端点通过 Harness Feature Flag 控制启用。Flag 命名规范：`api.v{version}.{resource}.{field_name}`。新字段默认对所有消费者不可见，按 consumer 级别逐步开放（Internal Partner → Trusted Customer → Public）。

---

## 🆕 v6.0 增强能力集成

### MARC资源协调器集成指南

本司在多Agent并发场景下的资源协调要求：

#### 资源锁机制
- **文件写锁**：当本司需要修改API定义文件（OpenAPI/GraphQL Schema）、路由配置、接口文档时，必须通过MARC申请互斥锁
  ```python
  # 示例：申请文件写锁
  from skillscripts.resource_coordinator import LockManager, LockType
  lock_mgr = LockManager()
  lock_id = lock_mgr.acquire_lock(
      resource_id="path/to/api/openapi.yaml",
      agent_id="API设计司",
      lock_type=LockType.EXCLUSIVE,
      priority=9,
      timeout=120.0
  )
  ```
- **读锁**：读取API定义、Schema文件、接口文档时申请读锁（高频查询场景）
- **释放锁**：API设计和文档更新完成后立即释放锁，避免阻塞其他司的接口查询

#### 终端会话池使用
- 从MARC终端会话池获取会话运行API验证命令（swagger-codegen/graphql-codegen等）
- 会话使用完毕后及时归还池中
- 单个命令超时设置为300秒（API代码生成和验证可能耗时较长）

#### 并发安全注意事项
- OpenAPI/GraphQL Schema是核心共享资产，写入时必须独占锁保护
- 多版本API并行开发时需锁定各自版本的Schema文件
- 死锁预防：按固定顺序申请锁（先锁API Schema→再锁路由配置→最后锁接口文档）

### 四维度输出防线集成

| 防线层级 | 本司检查重点 | 自动化程度 |
|---------|-------------|----------|
| **提示词工程层** | API设计提示词、Schema生成提示词、版本策略提示词 | 半自动（AI辅助） |
| **能力约束层** | 仅允许API设计操作（定义/文档/验证），禁止修改业务逻辑或数据访问层 | 全自动 |
| **规则校验层** | 输出格式：OpenAPI YAML/JSON、GraphQL Schema、Markdown API文档 | 全自动 |
| **兜底恢复层** | API设计不合规时自动回滚至上一版本并通知相关方 | 半自动 |

### 操作优先级指引（v6.0核心）

本司推荐的操作方式：

1. 🥇 **Agent自主手动操作**（强烈推荐用于API设计、Schema编写、接口文档撰写）
   - 示例：直接编辑OpenAPI YAML、手动编写GraphQL Schema、逐项审核API规范
   - 优势：精确控制API细节、可逐步验证正确性、可随时回滚设计变更

2. 🥈 **规划脚本操作**（适用于API代码生成、自动化文档发布）
   - 推荐脚本：
     - `skillscripts/resource_coordinator/quota_manager.py` — 检查API版本管理配额
     - `skillscripts/open_source_philosophy/clawcode_sdd_tdd_engine.py` — SDD/TDD驱动的API设计
     - `skillscripts/platform/powershell_adapter.py` — PS7环境适配

3. 🥉 **命令操作**（仅限API代码生成、Swagger验证等极少数场景）
   - ⚠️ 必须预演影响范围（API变更影响所有消费者）
   - ⚠️ Breaking Change需通过完整的兼容性测试
   - 推荐使用PS7适配器转换swagger-codegen/graphql-codegen等工具命令

### PowerShell 7 执行指南

本司相关操作的PS7适配要点:
- API验证：swagger-cli validate / graphql-inspector 等命令原生可用
- 代码生成：openapi-generator / graphql-codegen 等工具直接执行
- 文档发布：redocly / spectacle 等工具用于文档站点构建
- 编码：确保所有输出 UTF-8 无 BOM（API定义和文档文件）

### 与其他司的协作接口

- 上游依赖：工部代码司（接收业务需求以设计API）、数据库设计司（获取数据模型用于Schema设计）
- 下游输出：TDD执行司（提供API契约用于测试编写）、回归测试司（推送API变更用于集成测试）
- 数据交换格式：OpenAPI YAML/JSON / GraphQL SDL / Markdown（统一UTF-8无BOM）
