---
id: "KP-EXP-ERR-003"
type: "error-solution"
severity: "high"
category: "api"
tags: ["API契约", "接口不匹配", "字段缺失", "类型不一致", "版本兼容", "契约测试"]
version: "1.0.0"
confidence: 0.92
occurrences: 3
---

## API 契约不匹配 (置信度: 0.92 | 技术栈: API/REST/gRPC)

### 现象
前后端或微服务间调用失败：TypeError 读取 undefined 属性、422 状态码、字段名/类型不一致。

### 根因
字段命名风格不一致（camelCase vs snake_case）、接口变更未同步、缺少机器可读契约定义、API 版本管理缺失。

### 解决方案

```yaml
openapi: "3.1.0"
paths:
  /api/v2/users/{userId}:
    get:
      parameters:
        - name: userId
          in: path
          required: true
          schema:
            type: string
```

```bash
npx openapi-typescript openapi.yaml -o src/types/api.d.ts
```

```python
class UserResponse(BaseModel):
    model_config = ConfigDict(alias_generator=lambda f: f, populate_by_name=True)
    user_id: str
    phone: str | None = None
    def to_camel(self) -> dict: ...
```

### 验证
CI 中运行契约测试（Pact），确保消费方与提供方契约一致。
