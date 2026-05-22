---
id: "KP-EXP-INT-001"
type: "error-solution"
severity: "medium"
category: "integration"
tags: ["OAuth2", "第三方登录", "token", "refresh-token", "PKCE", "CSRF"]
version: "1.0.0"
confidence: 0.88
occurrences: 3
---

## 第三方 OAuth 集成问题 (置信度: 0.88 | 技术栈: OAuth2/SPA)

### 现象
OAuth 回调后获取不到 token、state 校验失败、refresh token 失效、CORS 阻止 token 交换。

### 根因
SPA 使用 Implicit Grant（已废弃）、redirect_uri 不匹配、state 未生成/未校验、refresh token 未轮换、后端未配置 CORS 允许 token 端点。

### 解决方案

```typescript
const state = crypto.randomUUID();
sessionStorage.setItem("oauth_state", state);
const authUrl = `https://auth.example.com/authorize?` +
  `response_type=code&client_id=${CLIENT_ID}&redirect_uri=${REDIRECT_URI}` +
  `&scope=openid profile email&state=${state}&code_challenge=${challenge}&code_challenge_method=S256`;
```

```typescript
const tokenResponse = await fetch("/api/auth/token", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ code, code_verifier: verifier, redirect_uri: REDIRECT_URI }),
});
```

### 验证
测试完整 OAuth 流程：授权→回调→token 交换→刷新→过期重授权。
