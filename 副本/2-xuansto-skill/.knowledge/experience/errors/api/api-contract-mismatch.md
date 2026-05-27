---
id: "KP-EXP-ERR-003"
type: "error-solution"
severity: "high"
category: "api"
tags: ["API契约", "接口不匹配", "字段缺失", "类型不一致", "版本兼容", "契约测试"]
version: "1.0.0"
created: "2026-04-28T10:00:00Z"
updated: "2026-04-28T10:00:00Z"
source: "auto_precipitation"
confidence: 0.92
last_validated: "2026-04-28T10:00:00Z"
success_count: 0
failure_count: 0
occurrences: 3
trigger: "bug_fix_completed"
references:
  - id: "KP-EXP-PAT-001"
    relation: "complies"
  - id: "KP-EXP-PAT-002"
    relation: "extends"
  - id: "KP-GEN-020"
    relation: "complies"
---

# API 契约不匹配错误

## 错误现象

前后端或微服务间 API 调用失败，表现为数据解析错误、字段缺失或类型不一致：

```
# 前端错误
TypeError: Cannot read properties of undefined (reading 'userId')
Error: Request failed with status code 422

# 后端错误
JsonDecodingError: Key 'user_id' not found
ValidationError: Expected string, got number for field 'age'

# 微服务间错误
gRPC error: 12 UNIMPLEMENTED: method not found
StatusRuntimeException: INVALID_ARGUMENT: field 'order_id' is required
```

### 典型特征

- 一方更新接口后另一方未同步
- 字段名不一致（如 `userId` vs `user_id`）
- 字段类型变更（如 `string` → `number`）
- 必填/可选字段变更
- API 版本未对齐

---

## 根因分析

### 1. 字段命名风格不一致

前端使用 `camelCase`，后端使用 `snake_case`，缺少统一转换层。

```typescript
interface FrontendUser {
  userId: string;
  firstName: string;
  lastName: string;
}

interface BackendUser {
  user_id: string;
  first_name: string;
  last_name: string;
}
```

### 2. 接口变更未同步

后端新增必填字段或修改字段类型，前端未更新。

```python
class UserResponse(BaseModel):
    user_id: str
    name: str
    email: str
    phone: str  # 新增必填字段，前端未适配
```

### 3. 缺少契约定义

API 接口仅靠口头约定或文档描述，无机器可读的契约文件。

### 4. 版本管理缺失

API 变更无版本控制，破坏性变更直接影响所有消费方。

---

## 解决方案

### 1. 定义 API 契约（OpenAPI / Swagger）

```yaml
openapi: "3.1.0"
info:
  title: 用户服务 API
  version: "2.0.0"
paths:
  /api/v2/users/{userId}:
    get:
      summary: 获取用户信息
      parameters:
        - name: userId
          in: path
          required: true
          schema:
            type: string
            pattern: "^usr_[a-zA-Z0-9]+$"
      responses:
        "200":
          description: 成功
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/UserResponse"
        "404":
          description: 用户不存在
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/ErrorResponse"

components:
  schemas:
    UserResponse:
      type: object
      required:
        - userId
        - name
        - email
      properties:
        userId:
          type: string
          example: "usr_abc123"
        name:
          type: string
          example: "张三"
        email:
          type: string
          format: email
          example: "zhangsan@example.com"
        phone:
          type: string
          nullable: true
          example: "13800138000"
    ErrorResponse:
      type: object
      required:
        - code
        - message
      properties:
        code:
          type: string
        message:
          type: string
```

### 2. 自动生成类型定义

#### 从 OpenAPI 生成 TypeScript 类型

```bash
npx openapi-typescript openapi.yaml -o src/types/api.d.ts
```

#### 从 OpenAPI 生成 Python 模型

```bash
datamodel-codegen --input openapi.yaml --output models.py
```

### 3. 契约测试（Pact）

```typescript
import { Pact } from "@pact-foundation/pact";

const provider = new Pact({
  consumer: "FrontendApp",
  provider: "UserService",
});

await provider.addInteraction({
  state: "用户 usr_001 存在",
  uponReceiving: "获取用户请求",
  withRequest: {
    method: "GET",
    path: "/api/v2/users/usr_001",
  },
  willRespondWith: {
    status: 200,
    headers: { "Content-Type": "application/json" },
    body: {
      userId: like("usr_001"),
      name: like("张三"),
      email: like("zhangsan@example.com"),
      phone: like("13800138000"),
    },
  },
});
```

### 4. 命名风格统一转换

#### Python 响应模型

```python
from pydantic import BaseModel, ConfigDict

class UserResponse(BaseModel):
    model_config = ConfigDict(
        alias_generator=lambda field_name: field_name,
        populate_by_name=True,
    )

    user_id: str
    name: str
    email: str
    phone: str | None = None

    def to_camel(self) -> dict:
        def snake_to_camel(name: str) -> str:
            parts = name.split("_")
            return parts[0] + "".join(p.capitalize() for p in parts[1:])

        return {
            snake_to_camel(k): v for k, v in self.model_dump().items()
        }
```

#### TypeScript 命名转换工具

```typescript
function snakeToCamel(str: string): string {
  return str.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase());
}

function camelToSnake(str: string): string {
  return str.replace(/[A-Z]/g, (letter) => `_${letter.toLowerCase()}`);
}

function transformKeys<T extends Record<string, unknown>>(
  obj: T,
  transformer: (key: string) => string,
): Record<string, unknown> {
  const result: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(obj)) {
    result[transformer(key)] = value;
  }
  return result;
}
```

### 5. API 版本管理策略

```python
from fastapi import FastAPI, APIRouter

app = FastAPI()

v1_router = APIRouter(prefix="/api/v1")
v2_router = APIRouter(prefix="/api/v2")

@v1_router.get("/users/{user_id}")
async def get_user_v1(user_id: str):
    return {"user_id": user_id, "name": "张三"}

@v2_router.get("/users/{userId}")
async def get_user_v2(userId: str):
    return {"userId": userId, "name": "张三", "email": "zhangsan@example.com"}

app.include_router(v1_router)
app.include_router(v2_router)
```

---

## 预防措施

| 措施 | 说明 |
|------|------|
| OpenAPI 契约优先 | 先定义 API 契约，再实现代码 |
| 自动生成类型 | 从契约文件自动生成前后端类型定义 |
| 契约测试 | 使用 Pact 等工具验证消费方与提供方契约一致 |
| 命名风格统一 | 约定 API 层统一使用 `camelCase` 或 `snake_case` |
| API 版本管理 | 破坏性变更必须升级 API 版本 |
| 变更通知机制 | API 变更自动通知所有消费方 |
| CI 集成 | 在 CI 中运行契约测试，防止不兼容变更合入 |

## 相关知识

- [KP-EXP-PAT-001] 仓储模式 — API 层与数据访问层的解耦
- [KP-EXP-PAT-002] 错误处理中间件 — 统一 API 错误响应格式
- [KP-GEN-020] 安全编码基础 — API 输入验证
