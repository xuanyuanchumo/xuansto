---
name: api_sheji_si
description: API设计司，负责RESTful API设计、接口契约定义、版本管理。确保API设计的一致性和可维护性。
---
# API设计司技能指令

## 职责
- RESTful API架构设计与规范制定
- OpenAPI/Swagger接口契约定义
- API版本管理策略
- 请求/响应格式标准化
- API安全性与性能设计

## API设计规范

### RESTful设计原则

```yaml
restful_conventions:
  uri_structure:
    pattern: "/api/v{version}/{resource}/{id}"
    examples:
      collection:   "/api/v1/users"
      resource:     "/api/v1/users/{user_id}"
      sub_resource: "/api/v1/users/{user_id}/orders"
      action:       "/api/v1/users/{user_id}/activate"

  http_methods:
    GET:    "获取资源（幂等/安全）"
    POST:   "创建资源（非幂等）"
    PUT:    "全量替换资源（幂等）"
    PATCH:  "部分更新资源（非幂等）"
    DELETE: "删除资源（幂等）"

  naming_conventions:
    resources: "kebab-case plural (users, order-items)"
    query_params: "snake_case (sort_by, page_size)"
    request_body: "camelCase (for JSON)"
    response_body: "camelCase (for JSON)"

  status_codes:
    success:
      200: "OK - 成功GET/PUT/PATCH"
      201: "Created - 成功POST"
      204: "No Content - 成功DELETE"
    client_error:
      400: "Bad Request - 参数错误"
      401: "Unauthorized - 未认证"
      403: "Forbidden - 无权限"
      404: "Not Found - 资源不存在"
      409: "Conflict - 资源冲突"
      422: "Unprocessable Entity - 校验失败"
    server_error:
      500: "Internal Server Error"
      503: "Service Unavailable"
```

### OpenAPI规范模板

```yaml
openapi: "3.1.0"
info:
  title: "Skiller API"
  version: "1.0.0"
  description: "尚书省六部协同管理系统API"
  contact:
    name: "API Support"

servers:
  - url: http://localhost:8000/api/v1
    description: "Development"

paths:
  /users:
    get:
      summary: "获取用户列表"
      operationId: "listUsers"
      tags: ["Users"]
      parameters:
        - name: page
          in: query
          schema:
            type: integer
            default: 1
            minimum: 1
        - name: page_size
          in: query
          schema:
            type: integer
            default: 20
            maximum: 100
      responses:
        "200":
          description: "成功返回用户列表"
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/PaginatedUserResponse"

components:
  schemas:
    User:
      type: object
      required: [id, name, email]
      properties:
        id:
          type: string
          format: uuid
        name:
          type: string
          maxLength: 100
        email:
          type: string
          format: email
        createdAt:
          type: string
          format: date-time

    PaginatedUserResponse:
      type: object
      properties:
        data:
          type: array
          items:
            $ref: "#/components/schemas/User"
        pagination:
          $ref: "#/components/schemas/PaginationMeta"

    PaginationMeta:
      type: object
      properties:
        page:
          type: integer
        pageSize:
          type: integer
        total:
          type: integer
        totalPages:
          type: integer

    ErrorResponse:
      type: object
      properties:
        code:
          type: string
        message:
          type: string
        details:
          type: array
          items:
            type: object
            properties:
              field:
                type: string
              message:
                type: string

  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
```

## 版本管理策略

### 版本化方案对比

| 方案 | URI路径 | Header | 优缺点 |
|------|---------|--------|--------|
| URI版本 | `/api/v1/users` | - | ✅简单直观 ❌URL变化 |
| Header版本 | `/api/users` | `Accept: v=1` | ✅URI稳定 ❌不易调试 |
| Media Type | `/api/users` | `Accept: application/vnd.api.v1+json` | ✅标准 ❌复杂 |
| **推荐** | **URI版本** | **-** | **平衡简洁性与实用性****

### 版本生命周期

```
v1 (current) ──→ v2 (stable) ──→ v3 (beta)
     │                   │               │
  维护模式           功能冻结         开发中
  仅安全修复         Bug修复          新功能
```

## 工作流程

```
1. 收集API需求（来自功能规格/前端需求）
2. 识别资源和操作
3. 设计RESTful端点和HTTP语义
4. 定义请求/响应Schema
5. 编写OpenAPI规范文档
6. 设计错误响应体系
7. 制定认证授权方案
8. API Review（团队评审）
9. 生成Mock服务供前端联调
10. 实现后验证契约合规性
11. 发布API文档
12. 将设计决策记录到DecisionLog
```

## 协同接口

| 接口 | 描述 | 调用方 |
|------|------|--------|
| `design_api` | API设计 | 新功能开发 |
| `generate_openapi` | 生成OpenAPI规范 | 设计阶段 |
| `validate_contract` | 契约验证 | CI/CD |
| `version_api` | 版本管理 | 发布周期 |
