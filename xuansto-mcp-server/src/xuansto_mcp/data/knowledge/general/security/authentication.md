---
id: authentication
type: knowledge
category: security
tags: [认证, 授权, JWT, OAuth2, Session, MFA, 密码安全]
version: 1.0.0
confidence: high
---

## 认证与授权规范 (版本: 1.0 | 适用: Web/API)

### 核心规则
- 认证（你是谁）vs 授权（你能做什么）必须分离
- JWT 使用 RS256/ES256 非对称算法，Payload 不存放敏感信息
- Access Token 15min + Refresh Token 7d，Refresh 单次使用轮换
- OAuth 2.0：Web 用 Authorization Code + PKCE，M2M 用 Client Credentials
- 禁止 Implicit Grant 和 Resource Owner Password Credentials
- Session Cookie：HttpOnly + Secure + SameSite=Strict/Lax
- 密码存储：Argon2id/bcrypt/scrypt，禁止 MD5/SHA，盐值 ≥16 字节
- MFA 推荐 TOTP 作为第二因素

### 代码示例

```typescript
const token = jwt.sign({ sub: userId }, JWT_SECRET, { expiresIn: "15m", algorithm: "RS256" });
```

```python
response.set_cookie("session_id", token, httponly=True, secure=True, samesite="strict", max_age=3600)
```

### 反模式
- ❌ JWT 使用 HS256 对称算法 — 密钥泄露后任何人可签发
- ❌ Session ID 未轮换 — Session Fixation 攻击
- ❌ 密码用 MD5 哈希无盐值 — 彩虹表秒破
