---
id: authentication
type: knowledge
category: security
tags: [认证, 授权, JWT, OAuth2, Session, MFA, 密码安全]
version: 1.0.0
created: 2026-04-28
updated: 2026-04-28
confidence: high
---

# 认证与授权规范

## 认证 (Authentication) vs 授权 (Authorization)

- **认证**：验证用户身份（你是谁？）
- **授权**：验证用户权限（你能做什么？）

## JWT (JSON Web Token)

结构：Header.Payload.Signature

```
Header:  { "alg": "RS256", "typ": "JWT" }
Payload: { "sub": "user_id", "iat": 1745800000, "exp": 1745803600 }
```

安全要点：
- 使用 RS256/ES256 非对称算法，避免 HS256 对称算法
- Payload 不存放敏感信息（仅 Base64 编码，非加密）
- 设置合理过期时间（Access Token 15min，Refresh Token 7d）
- Refresh Token 单次使用，轮换后旧 Token 失效
- Token 撤销需维护黑名单或短过期 + Refresh 机制

## OAuth 2.0 授权流程

| 流程 | 适用场景 |
|------|----------|
| Authorization Code | 服务端 Web 应用（最安全） |
| Authorization Code + PKCE | SPA / 移动端 |
| Client Credentials | 服务间通信（M2M） |
| Device Code | IoT / 无浏览器设备 |

禁止使用 Implicit Grant 和 Resource Owner Password Credentials。

## Session 管理

- Session ID 使用加密安全随机数（至少 128 位）
- Cookie 设置：`HttpOnly` + `Secure` + `SameSite=Strict/Lax`
- 登录后重新生成 Session ID，防止 Session Fixation
- 设置空闲超时（30min）和绝对超时（8h）

## 密码存储

- 使用 Argon2id / bcrypt / scrypt 等自适应哈希算法
- 禁止使用 MD5/SHA 系列直接哈希
- bcrypt cost factor ≥ 12，Argon2id 内存 ≥ 64MB
- 密码加盐（salt）长度 ≥ 16 字节，每用户独立盐值

## MFA (多因素认证)

三因素类型：知识（密码）、持有（手机/Token）、固有（生物特征）。推荐 TOTP（Time-based OTP）作为第二因素，备份 Recovery Code 单次使用。
