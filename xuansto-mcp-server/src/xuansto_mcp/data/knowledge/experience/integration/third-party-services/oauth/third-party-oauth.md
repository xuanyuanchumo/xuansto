---
id: "KP-EXP-INT-OAUTH-001"
type: "error-solution"
severity: "medium"
category: "integration"
tags: ["OAuth2", "第三方服务", "token管理", "刷新策略", "安全"]
version: "1.0.0"
confidence: 0.87
occurrences: 2
---

## 第三方 OAuth 服务集成 (置信度: 0.87 | 技术栈: OAuth2/后端)

### 现象
第三方 OAuth 服务 token 过期后请求失败、并发刷新导致 token 失效、回调 URL 配置错误。

### 根因
Token 过期未自动刷新、多请求并发刷新同一 refresh token（仅首次有效）、回调 URL 与注册不一致。

### 解决方案

```python
class TokenManager:
    def __init__(self):
        self._lock = asyncio.Lock()
        self._token: dict | None = None

    async def get_valid_token(self) -> str:
        if self._token and time.time() < self._token["expires_at"] - 60:
            return self._token["access_token"]
        async with self._lock:
            if self._token and time.time() < self._token["expires_at"] - 60:
                return self._token["access_token"]
            self._token = await self._refresh_token()
            return self._token["access_token"]
```

### 验证
模拟 token 过期场景，验证自动刷新和并发请求仅触发一次刷新。
