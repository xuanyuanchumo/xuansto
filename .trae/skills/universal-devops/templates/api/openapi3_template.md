<!--
  模板说明: OpenAPI 3.0 API Documentation (OpenAPI 3.0 规范的API文档)
  用途: 定义RESTful API接口规范，可作为Swagger UI展示、代码生成、Mock服务的源文件
  变量列表:
    {{api_title}}              - API标题
    {{api_description}}        - API描述
    {{api_version}}            - API版本号
    {{contact_name}}           - 联系人姓名
    {{contact_email}}          - 联系邮箱
    {{server_urls}}            - 服务器环境URL列表
    {{api_paths}}              - API端点定义
    {{data_models}}            - 数据模型(Schema)定义
    {{security_schemes}}       - 认证方式定义
  使用方式: 此文件同时是有效的YAML和Markdown格式，可导入Swagger Editor验证。
         推荐使用 .yaml 后缀保存为纯YAML文件用于工具消费，此.md版本供人类阅读。
-->

# {{api_title | default('[项目名称]')}} RESTful API 文档

> **规范版本**: OpenAPI 3.0.3 | **API版本**: {{api_version | default('v1.0')}}
> **基础URL**: `{{base_url | default('https://api.example.com/v1')}}`
> **联系方式**: {{contact_email | default('api@example.com')}}

---

## 📖 目录

- [概述](#概述)
- [认证方式](#认证方式)
- [通用约定](#通用约定)
- [错误码规范](#错误码规范)
- [API端点](#api端点)
  - [用户模块 (Users)](#用户模块-users)
  - [认证模块 (Auth)](#认证模块-auth)
  - [订单模块 (Orders)](#订单模块-orders)
  - [支付模块 (Payment)](#支付模块-payment)
  - [文件模块 (Files)](#文件模块-files)
  - [管理后台 (Admin)](#管理后台-admin)
- [数据模型](#数据模型)
- [变更日志](#变更日志)

---

## 概述

<!-- COMMENT: 描述API的整体设计理念和主要能力 -->

{{api_description | default('{{api_title | default("本系统")}} 提供完整的RESTful API接口，支持用户管理、业务操作、支付集成等核心功能。所有接口均返回JSON格式数据，遵循RESTful设计规范。')}}

### 设计原则

| 原则 | 说明 |
|------|------|
| **RESTful** | 使用标准HTTP方法(GET/POST/PUT/DELETE)，资源以名词URI表示 |
| **版本化** | URL中包含版本前缀 `/v1/`，保证向后兼容 |
| **JSON优先** | 请求和响应体统一使用JSON格式 |
| **统一响应** | 所有响应使用统一的包装结构 `{code, message, data}` |
| **分页支持** | 列表接口支持统一的分页参数 |
| **幂等性** | PUT/DELETE操作保证幂等 |
| **HATEOAS** | 响应包含相关资源的链接（可选） |

---

## 认证方式

### JWT Bearer Token

所有需要认证的接口（除公开接口外）必须在请求头中携带JWT Token：

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Token获取**: 通过 `POST /api/v1/auth/login` 登录接口获取。

**Token有效期**: Access Token = 15分钟, Refresh Token = 7天。

### 认证流程图

```mermaid
sequenceDiagram
    participant C as 客户端
    participant S as API Server
    participant Auth as 认证服务

    C->>S: POST /auth/login {phone, password}
    S->>Auth: 验证凭据
    Auth-->>S: 验证通过
    S-->>C: 200 {accessToken, refreshToken}

    Note over C,S: 后续请求携带Token

    C->>S: GET /api/v1/users/me<br/>Authorization: Bearer {accessToken}
    S->>Auth: 解析并验证Token
    Auth-->>S: Token有效 + 用户信息
    S-->>C: 200 {用户数据}

    Note over C,S: Token过期时

    C->>S: GET /api/v1/users/me<br/>(Token已过期)
    S-->>C: 401 Unauthorized

    C->>S: POST /auth/refresh {refreshToken}
    S-->>C: 200 {新accessToken, 新refreshToken}
```

---

## 通用约定

### 请求头

| Header | 必填 | 说明 | 示例 |
|--------|------|------|------|
| `Content-Type` | 是(POST/PUT) | 请求体格式 | `application/json` |
| `Accept` | 否 | 响应格式 | `application/json` |
| `Authorization` | 是*(需认证)* | Bearer Token | `Bearer eyJ...` |
| `X-Request-ID` | 否 | 请求追踪ID（客户端生成） | `uuid-v4` |
| `X-Lang` | 否 | 语言偏好 | `zh-CN`, `en-US` |

### 统一响应格式

#### 成功响应

```json
{
  "code": 0,
  "message": "success",
  "data": {
    <!-- 具体数据 -->
  },
  "requestId": "req_abc123",
  "timestamp": 1700000000000
}
```

#### 错误响应

```json
{
  "code": 40001,
  "message": "参数校验失败: 手机号格式不正确",
  "data": null,
  "errors": [
    {
      "field": "phone",
      "message": "请输入正确的11位手机号码"
    }
  ],
  "requestId": "req_def456",
  "timestamp": 1700000000000
}
```

#### 分页响应

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [...],
    "pagination": {
      "page": 1,
      "pageSize": 20,
      "totalItems": 150,
      "totalPages": 8,
      "hasNext": true,
      "hasPrev": false
    }
  }
}
```

### 分页参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `page` | integer | 否 | 1 | 页码，从1开始 |
| `pageSize` | integer | 否 | 20 | 每页条数，最大100 |

---

## 错误码规范

<!-- COMMENT: 统一的错误码体系，方便客户端处理 -->

| 错误码范围 | 类别 | HTTP状态码 | 说明 |
|------------|------|-----------|------|
| 0 | 成功 | 200 | 请求成功 |
| 10001-10099 | 参数错误 | 400 | 请求参数不合法 |
| 20001-20099 | 认证错误 | 401 | 未登录或Token无效 |
| 30001-30099 | 权限错误 | 403 | 无权限访问该资源 |
| 40001-40099 | 资源不存在 | 404 | 请求的资源不存在 |
| 50001-50099 | 业务逻辑错误 | 422 | 业务规则校验失败 |
| 90001-90099 | 系统内部错误 | 500 | 服务器内部错误 |
| 99001-99099 | 第三方服务错误 | 502 | 外部服务调用失败 |

### 常用错误码明细

| 错误码 | HTTP状态码 | 含义 | 处理建议 |
|--------|-----------|------|----------|
| 0 | 200 | 成功 | - |
| 10001 | 400 | 缺少必填参数 | 检查请求体完整性 |
| 10002 | 400 | 参数格式错误 | 参考 errors 字段定位具体字段 |
| 20001 | 401 | 未提供Token | 引导用户登录 |
| 20002 | 401 | Token已过期 | 使用RefreshToken刷新 |
| 20003 | 401 | Token无效 | 重新登录 |
| 30001 | 403 | 权限不足 | 提示用户无权操作 |
| 40001 | 404 | 资源不存在 | 检查资源ID是否正确 |
| 50001 | 422 | 业务规则违反 | 展示message给用户 |
| 90001 | 500 | 服务器内部错误 | 稍后重试，联系客服 |
| 99001 | 502 | 短信发送失败 | 稍后重试 |

---

## API端点

### 🔐 认证模块 (Auth)

#### POST 用户注册

注册新用户账号。

```
POST /api/v1/auth/register
```

**请求体**:

```json
{
  "phone": "13800138000",
  "code": "123456",
  "password": "MyPassw0rd!",
  "confirmPassword": "MyPassw0rd!"
}
```

| 字段 | 类型 | 必填 | 约束 | 说明 |
|------|------|------|------|------|
| phone | string | ✅ | 11位手机号 | 注册手机号 |
| code | string | ✅ | 6位数字 | 短信验证码 |
| password | string | ✅ | 8-20位，含字母+数字 | 登录密码 |
| confirmPassword | string | ✅ | 与password一致 | 确认密码 |

**响应** (201 Created):

```json
{
  "code": 0,
  "message": "注册成功",
  "data": {
    "userId": 10086,
    "phone": "138****8000",
    "token": {
      "accessToken": "eyJ...",
      "refreshToken": "eyJ...",
      "expiresIn": 900
    }
  }
}
```

**错误响应**:

| 场景 | HTTP状态码 | 错误码 | message |
|------|-----------|--------|---------|
| 该手机号已注册 | 409 | 50002 | 该手机号已被注册 |
| 验证码错误 | 400 | 50003 | 验证码错误或已过期 |
| 密码不符合规则 | 400 | 10002 | 密码需8-20位且包含字母和数字 |

---

#### POST 用户登录

通过手机号+密码登录。

```
POST /api/v1/auth/login
```

**请求体**:

```json
{
  "phone": "13800138000",
  "password": "MyPassw0rd!"
}
```

**响应** (200 OK):

```json
{
  "code": 0,
  "message": "登录成功",
  "data": {
    "userId": 10086,
    "token": {
      "accessToken": "eyJ...",
      "refreshToken": "eyJ...",
      "expiresIn": 900
    },
    "userInfo": {
      "nickname": "用户10086",
      "avatarUrl": "https://cdn.example.com/avatar/default.png"
    }
  }
}
```

---

#### POST 刷新Token

使用RefreshToken获取新的Access Token。

```
POST /api/v1/auth/refresh
```

**请求体**:

```json
{
  "refreshToken": "eyJ..."
}
```

**响应** (200 OK):

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "accessToken": "eyJ...(new)",
    "refreshToken": "eyJ...(new)",
    "expiresIn": 900
  }
}
```

---

#### POST 发送短信验证码

向指定手机号发送短信验证码。

```
POST /api/v1/auth/sms/send
```

**请求体**:

```json
{
  "phone": "13800138000",
  "scene": "REGISTER"
}
```

| scene枚举值 | 用途 |
|-------------|------|
| REGISTER | 注册验证码 |
| LOGIN | 登录验证码 |
| RESET_PASSWORD | 重置密码验证码 |
| CHANGE_PHONE | 更换手机号验证码 |
| BIND_ACCOUNT | 绑定账号验证码 |

**响应** (200 OK):

```json
{
  "code": 0,
  "message": "验证码已发送",
  "data": null
}
```

**频率限制**: 同一IP每分钟最多3次，同一手机号每天最多10次。

---

#### POST 忘记密码 / 重置密码

通过验证码重置密码。

```
POST /api/v1/auth/password/reset
```

**请求体**:

```json
{
  "phone": "13800138000",
  "code": "123456",
  "newPassword": "NewPassw0rd!",
  "confirmPassword": "NewPassw0rd!"
}
```

**响应** (200 OK):

```json
{
  "code": 0,
  "message": "密码重置成功",
  "data": null
}
```

---

### 👤 用户模块 (Users)

> ⚠️ 以下接口需认证: `Authorization: Bearer {token}`

#### GET 获取当前用户信息

获取当前登录用户的详细信息。

```
GET /api/v1/users/me
```

**响应** (200 OK):

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 10086,
    "phone": "138****8000",
    "email": "user@example.com",
    "nickname": "张三",
    "avatarUrl": "https://cdn.example.com/avatar/u10086.jpg",
    "bio": "这是我的个人简介",
    "gender": "MALE",
    "status": "ACTIVE",
    "createdAt": "2024-01-15T08:30:00Z",
    "lastLoginAt": "2024-03-20T14:22:00Z"
  }
}
```

---

#### PUT 更新用户资料

修改当前用户的个人信息。

```
PUT /api/v1/users/me/profile
```

**请求体**:

```json
{
  "nickname": "新昵称",
  "bio": "更新后的简介",
  "gender": "MALE"
}
```

**响应** (200 OK):

```json
{
  "code": 0,
  "message": "更新成功",
  "data": {
    "id": 10086,
    "nickname": "新昵称",
    "bio": "更新后的简介",
    "gender": "MALE"
  }
}
```

---

#### POST 上传头像

上传用户头像图片。

```
POST /api/v1/users/me/avatar
Content-Type: multipart/form-data
```

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | file | ✅ | 图片文件(JPG/PNG/GIF, ≤2MB) |

**响应** (200 OK):

```json
{
  "code": 0,
  "message": "头像上传成功",
  "data": {
    "avatarUrl": "https://cdn.example.com/avatar/u10086_1700000000.jpg",
    "thumbnailUrl": "https://cdn.example.com/avatar/thumb_u10086.jpg"
  }
}
```

---

#### PUT 修改密码

修改当前用户密码（需验证旧密码）。

```
PUT /api/v1/users/me/password
```

**请求体**:

```json
{
  "oldPassword": "OldPassw0rd!",
  "newPassword": "NewSecure1!",
  "confirmPassword": "NewSecure1!"
}
```

**响应** (200 OK):

```json
{
  "code": 0,
  "message": "密码修改成功",
  "data": null
}
```

---

### 📦 订单模块 (Orders)

> ⚠️ 需认证

#### POST 创建订单

创建一个新的订单。

```
POST /api/v1/orders
```

**请求体**:

```json
{
  "items": [
    {
      "productId": "P001",
      "quantity": 2,
      "skuId": "SKU001"
    },
    {
      "productId": "P002",
      "quantity": 1,
      "skuId": "SKU002"
    }
  ],
  "remark": "请尽快发货",
  "couponCode": "SAVE20"
}
```

**响应** (201 Created):

```json
{
  "code": 0,
  "message": "订单创建成功",
  "data": {
    "orderId": "ORD202403200001",
    "orderNo": "ORD-20240320-ABC123",
    "status": "PENDING_PAYMENT",
    "totalAmount": 299.00,
    "discountAmount": 20.00,
    "payableAmount": 279.00,
    "expireTime": "2024-03-20T15:30:00Z",
    "items": [
      {
        "itemId": "I001",
        "productName": "商品A",
        "quantity": 2,
        "unitPrice": 129.50,
        "subtotal": 259.00
      }
    ]
  }
}
```

---

#### GET 订单列表 (分页)

查询当前用户的订单列表，支持多维度筛选。

```
GET /api/v1/orders?page=1&pageSize=20&status=PAID&startDate=2024-01-01&endDate=2024-03-31
```

**查询参数**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| page | integer | 否 | 1 | 页码 |
| pageSize | integer | 否 | 20 | 每页条数(≤100) |
| status | string | 否 | 全部 | 订单状态筛选 |
| startDate | date | 否 | - | 创建时间起始 |
| endDate | date | 否 | - | 创建时间截止 |
| keyword | string | 否 | - | 关键词搜索(订单号/商品名) |

**status枚举值**: `PENDING_PAYMENT`, `PAID`, `SHIPPED`, `DELIVERED`, `COMPLETED`, `CANCELLED`, `REFUNDING`

**响应** (200 OK):

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "orderId": "ORD202403200001",
        "orderNo": "ORD-20240320-ABC123",
        "status": "PAID",
        "statusText": "已付款",
        "totalAmount": 279.00,
        "itemCount": 2,
        "createdAt": "2024-03-20T14:30:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "pageSize": 20,
      "totalItems": 45,
      "totalPages": 3,
      "hasNext": true,
      "hasPrev": false
    }
  }
}
```

---

#### GET 订单详情

获取单个订单的完整信息。

```
GET /api/v1/orders/{orderId}
```

**路径参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| orderId | string | 订单ID |

**响应** (200 OK):

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "orderId": "ORD202403200001",
    "orderNo": "ORD-20240320-ABC123",
    "status": "PAID",
    "statusText": "已付款",
    "totalAmount": 279.00,
    "payableAmount": 279.00,
    "paymentMethod": "ALIPAY",
    "paidAt": "2024-03-20T14:35:00Z",
    "shippingAddress": {
      "recipient": "张三",
      "phone": "138****8000",
      "province": "北京市",
      "city": "北京市",
      "district": "朝阳区",
      "detailAddress": "建国路88号",
      "fullAddress": "北京市北京市朝阳区建国路88号"
    },
    "items": [
      {
        "productId": "P001",
        "productName": "优质商品A",
        "productImage": "https://cdn.example.com/products/P001.jpg",
        "skuName": "红色/L码",
        "quantity": 2,
        "unitPrice": 129.50,
        "subtotal": 259.00
      }
    ],
    "timeline": [
      {"time": "2024-03-20T14:30:00Z", "event": "订单创建", "desc": "您提交了订单"},
      {"time": "2024-03-20T14:33:00Z", "event": "支付完成", "desc": "支付宝支付¥279.00"},
      {"time": "2024-03-20T16:00:00Z", "event": "商家发货", "desc": "顺丰快递 SF1234567890"}
    ],
    "createdAt": "2024-03-20T14:30:00Z",
    "updatedAt": "2024-03-20T16:00:00Z"
  }
}
```

---

#### POST 取消订单

取消未支付的订单。

```
POST /api/v1/orders/{orderId}/cancel
```

**请求体**:

```json
{
  "reason": "不想买了"
}
```

**响应** (200 OK):

```json
{
  "code": 0,
  "message": "订单已取消",
  "data": {
    "orderId": "ORD202403200001",
    "status": "CANCELLED",
    "refundAmount": 0,
    "cancelledAt": "2024-03-20T15:00:00Z"
  }
}
```

---

### 💳 支付模块 (Payment)

> ⚠️ 需认证

#### POST 发起支付

为指定订单发起支付请求。

```
POST /api/v1/payments/create
```

**请求体**:

```json
{
  "orderId": "ORD202403200001",
  "paymentMethod": "ALIPAY",
  "returnUrl": "https://app.example.com/payment/result"
}
```

| paymentMethod 枚举 | 说明 |
|-------------------|------|
| ALIPAY | 支付宝 |
| WECHAT_PAY | 微信支付 |
| BALANCE | 余额支付 |

**响应** (200 OK):

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "paymentId": "PAY202403200001",
    "payUrl": "https://openapi.alipay.com/gateway.do?...",   // ALIPAY/WECHAT_PAY时返回
    "qrCodeUrl": "data:image/png;base64,...",                  // 微信支付扫码链接
    "prepayId": "wx2024032000012345abcdef",                    // 微信支付预付单号
    "expireTime": "2024-03-20T15:30:00Z"
  }
}
```

---

#### GET 支付结果查询

查询订单的支付状态。

```
GET /api/v1/payments/{paymentId}/status
```

**响应** (200 OK):

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "paymentId": "PAY202403200001",
    "orderId": "ORD202403200001",
    "status": "PAID",
    "paidAmount": 279.00,
    "paymentMethod": "ALIPAY",
    "transactionNo": "2024032022001001234567",
    "paidAt": "2024-03-20T14:35:12Z"
  }
}
```

---

#### POST 支付回调通知

> ⚠️ 此接口由支付平台主动调用，不需要客户端认证

支付平台在支付完成后回调通知服务器。

```
POST /api/v1/payments/callback/alipay
Content-Type: application/x-www-form-urlencoded
```

**响应** (需原样返回给支付平台):

```
success
```

---

### 📁 文件模块 (Files)

> ⚠️ 需认证

#### POST 通用文件上传

上传任意类型的文件。

```
POST /api/v1/files/upload
Content-Type: multipart/form-data
```

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | file | ✅ | 文件(≤50MB) |
| category | string | 否 | 文件分类: avatar/document/export/other |

**响应** (200 OK):

```json
{
  "code": 0,
  "message": "上传成功",
  "data": {
    "fileId": "F202403200001",
    "fileName": "report.xlsx",
    "fileSize": 2048576,
    "mimeType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "url": "https://cdn.example.com/uploads/F202403200001.xlsx",
    "thumbnailUrl": null
  }
}
```

---

### 🔧 管理后台 (Admin)

> ⚠️ 需管理员权限 (`role: ADMIN`)

#### GET 用户管理 - 用户列表

```
GET /api/v1/admin/users?page=1&pageSize=20&status=ACTIVE&keyword=
```

**响应** (200 OK):

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 10086,
        "phone": "138****8000",
        "email": "user@example.com",
        "nickname": "张三",
        "status": "ACTIVE",
        "registeredAt": "2024-01-15T08:30:00Z",
        "lastLoginAt": "2024-03-20T14:22:00Z",
        "orderCount": 15,
        "totalSpent": 4580.00
      }
    ],
    "pagination": {
      "page": 1,
      "pageSize": 20,
      "totalItems": 1024,
      "totalPages": 52,
      "hasNext": true,
      "hasPrev": false
    }
  }
}
```

---

#### PUT 用户管理 - 封禁/解封用户

```
PUT /api/v1/admin/users/{userId}/status
```

**请求体**:

```json
{
  "status": "DISABLED",
  "reason": "违反社区规定"
}
```

---

#### GET 数据统计 - 运营概览

```
GET /api/v1/admin/statistics/overview?startDate=2024-03-01&endDate=2024-03-31
```

**响应** (200 OK):

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "period": {
      "start": "2024-03-01",
      "end": "2024-03-31"
    },
    "summary": {
      "newUsers": 1520,
      "activeUsers": 8500,
      "totalOrders": 12580,
      "totalRevenue": 528600.00,
      "conversionRate": 0.128,
      "avgOrderValue": 42.03
    },
    "trend": {
      "dailyNewUsers": [[{"date":"03-01","value":45}, ...]],
      "dailyRevenue": [[{"date":"03-01","value":15800}, ...]]
    }
  }
}
```

---

## 数据模型

### UserDTO (用户信息)

```typescript
interface UserDTO {
  id: number;                    // 用户唯一标识
  phone: string;                 // 手机号(脱敏显示)
  email: string | null;          // 邮箱地址
  nickname: string;              // 昵称
  avatarUrl: string;             // 头像URL
  bio: string | null;            // 个人简介
  gender: 'MALE' | 'FEMALE' | 'UNKNOWN';  // 性别
  status: 'ACTIVE' | 'DISABLED' | 'PENDING_VERIFICATION';  // 状态
  createdAt: string;             // ISO 8601 格式
  lastLoginAt: string | null;    // 最后登录时间
}
```

### OrderDTO (订单信息)

```typescript
interface OrderDTO {
  orderId: string;
  orderNo: string;
  status: OrderStatus;
  statusText: string;
  totalAmount: number;
  discountAmount: number;
  payableAmount: number;
  paymentMethod?: PaymentMethod;
  items: OrderItemDTO[];
  shippingAddress?: AddressDTO;
  timeline: TimelineEventDTO[];
  createdAt: string;
  updatedAt: string;
}

type OrderStatus =
  | 'PENDING_PAYMENT'
  | 'PAID'
  | 'SHIPPED'
  | 'DELIVERED'
  | 'COMPLETED'
  | 'CANCELLED'
  | 'REFUNDING';

type PaymentMethod = 'ALIPAY' | 'WECHAT_PAY' | 'BALANCE';
```

### PaginatedResponse<T> (分页响应)

```typescript
interface PaginatedResponse<T> {
  items: T[];
  pagination: {
    page: number;
    pageSize: number;
    totalItems: number;
    totalPages: number;
    hasNext: boolean;
    hasPrev: boolean;
  };
}
```

### ApiResponse<T> (统一响应)

```typescript
interface ApiResponse<T> {
  code: number;           // 0=成功, 非0=错误码
  message: string;        // 可读消息
  data: T | null;         // 业务数据
  errors?: Array<{        // 仅错误时有值
    field: string;
    message: string;
  }>;
  requestId: string;      // 请求追踪ID
  timestamp: number;      // 服务端时间戳(ms)
}
```

---

## 安全注意事项

| 安全项 | 要求 | 实现 |
|--------|------|------|
| HTTPS强制 | 生产环境必须HTTPS | Nginx SSL配置 + HSTS头 |
| CORS策略 | 仅允许信任的域名 | Access-Control-Allow-Origin白名单 |
| 输入校验 | 所有输入严格校验 | DTO注解 + 白名单过滤 |
| SQL注入防护 | 参数化查询 | MyBatis #{} 占位符 |
| XSS防护 | 输出编码 | JSON序列化自动转义 |
| CSRF保护 | SameSite Cookie | Cookie属性配置 |
| 速率限制 | 防止暴力攻击 | Redis滑动窗口限流 |
| 敏感数据脱敏 | 手机号/身份证等 | 后端脱敏后返回 |
| 日志脱敏 | 不记录敏感字段 | Logback Masking规则 |

---

## 变更日志

| 版本 | 日期 | 作者 | 变更内容 |
|------|------|------|----------|
| v1.0.0 | {{date | default('YYYY-MM-DD')}} | {{author | default('API Team')}} | 初始版本，包含Auth/Users/Orders/Payment/Files/Admin六大模块 |
| v1.1.0 | <!-- COMMENT: 未来变更 --> | | <!-- COMMENT: --> |

---

*本文档基于 OpenAPI 3.0.3 规范编写。可通过 Swagger UI 在线浏览: `https://api.example.com/swagger-ui.html`*
