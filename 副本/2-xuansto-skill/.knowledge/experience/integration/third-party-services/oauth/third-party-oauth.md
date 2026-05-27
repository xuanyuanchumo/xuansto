---
id: "KP-EXP-INT-001"
type: "integration"
severity: "medium"
category: "authentication"
tags: ["oauth", "google", "authentication", "第三方登录", "OIDC", "token"]
version: "1.0.0"
created: "2026-04-28T10:00:00Z"
updated: "2026-04-28T10:00:00Z"
source: "auto_precipitation"
confidence: 0.88
last_validated: "2026-04-28T10:00:00Z"
success_count: 0
failure_count: 0
occurrences: 3
trigger: "integration_completed"
references:
  - id: "KP-GEN-020"
    relation: "complies"
  - id: "KP-GEN-021"
    relation: "complies"
---

# Google OAuth 2.0 第三方登录集成

## 集成挑战

在系统中集成 Google OAuth 2.0 第三方登录时，面临以下核心挑战：

- OAuth 2.0 流程状态管理复杂，CSRF 防护要求严格
- Token 安全存储与刷新机制设计
- 已有账号与第三方身份的关联策略
- 多环境（开发/预发/生产）回调 URL 配置
- Google API 变更导致接口不兼容

---

## 解决方案

### 1. OAuth 2.0 授权码流程

```
用户 → 点击"Google登录" → 重定向至 Google 授权页
                              ↓
                         用户授权
                              ↓
Google → 回调 redirect_uri + code → 后端换取 token
                                        ↓
                                   获取用户信息
                                        ↓
                                   创建/关联账号 → 签发 JWT
```

### 2. 后端核心实现

```python
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config

config = Config(".env")

oauth = OAuth(config)
oauth.register(
    name="google",
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

async def google_login(request):
    redirect_uri = request.url_for("google_callback")
    return await oauth.google.authorize_redirect(request, redirect_uri)

async def google_callback(request):
    token = await oauth.google.authorize_access_token(request)
    userinfo = token.get("userinfo")

    if not userinfo:
        userinfo = await oauth.google.userinfo(token=token)

    user = await find_or_create_user(
        provider="google",
        provider_id=userinfo["sub"],
        email=userinfo.get("email"),
        name=userinfo.get("name"),
        avatar=userinfo.get("picture"),
    )

    jwt_token = create_jwt({"user_id": user.id, "email": user.email})
    response = RedirectResponse(url="/dashboard")
    response.set_cookie(
        key="access_token",
        value=jwt_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=3600,
    )
    return response
```

### 3. 账号关联策略

```python
from datetime import datetime

async def find_or_create_user(provider: str, provider_id: str, email: str, name: str, avatar: str):
    identity = await db.fetch_one(
        "SELECT user_id FROM user_identities WHERE provider = $1 AND provider_id = $2",
        provider, provider_id,
    )

    if identity:
        await db.execute(
            "UPDATE user_identities SET last_used_at = $1 WHERE provider = $2 AND provider_id = $3",
            datetime.utcnow(), provider, provider_id,
        )
        return await db.fetch_one("SELECT * FROM users WHERE id = $1", identity.user_id)

    existing_user = await db.fetch_one("SELECT * FROM users WHERE email = $1", email)

    if existing_user:
        await db.execute(
            """INSERT INTO user_identities (user_id, provider, provider_id, created_at, last_used_at)
               VALUES ($1, $2, $3, $4, $4)""",
            existing_user.id, provider, provider_id, datetime.utcnow(),
        )
        return existing_user

    new_user = await db.fetch_one(
        """INSERT INTO users (email, name, avatar, created_at)
           VALUES ($1, $2, $3, $4) RETURNING *""",
        email, name, avatar, datetime.utcnow(),
    )
    await db.execute(
        """INSERT INTO user_identities (user_id, provider, provider_id, created_at, last_used_at)
           VALUES ($1, $2, $3, $4, $4)""",
        new_user.id, provider, provider_id, datetime.utcnow(),
    )
    return new_user
```

### 4. 数据库设计

```sql
CREATE TABLE user_identities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider VARCHAR(32) NOT NULL,
    provider_id VARCHAR(256) NOT NULL,
    email VARCHAR(256),
    display_name VARCHAR(128),
    avatar_url TEXT,
    access_token TEXT,
    refresh_token TEXT,
    token_expires_at TIMESTAMPTZ,
    last_used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(provider, provider_id)
);

CREATE INDEX idx_user_identities_user ON user_identities(user_id);
```

---

## 常见陷阱与解决方案

| 陷阱 | 现象 | 解决方案 |
|------|------|---------|
| state 参数缺失 | CSRF 攻击风险 | `authlib` 自动处理，手动实现须生成随机 state 并验证 |
| 回调 URL 不匹配 | Google 返回 `redirect_uri_mismatch` | 各环境在 Google Console 分别注册回调 URL |
| Token 过期未刷新 | 用户频繁掉线 | 存储 refresh_token，access_token 过期前自动刷新 |
| 邮箱冲突 | 同一邮箱不同 provider 登录创建重复账号 | 以邮箱为主键关联，首次自动绑定 |
| HTTPS 要求 | 本地开发无法回调 | 使用 `ngrok` 或 `localhost` 特殊配置 |
| ID Token 验证缺失 | 伪造用户信息 | 始终验证 ID Token 的签名和 `aud` 声明 |

---

## 测试策略

### 单元测试

```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_find_or_create_existing_identity():
    with patch("module.db") as mock_db:
        mock_db.fetch_one = AsyncMock(side_effect=[
            {"user_id": "usr_001"},
            {"id": "usr_001", "email": "test@example.com"},
        ])
        user = await find_or_create_user("google", "123", "test@example.com", "Test", None)
        assert user.id == "usr_001"

@pytest.mark.asyncio
async def test_find_or_create_new_user():
    with patch("module.db") as mock_db:
        mock_db.fetch_one = AsyncMock(side_effect=[None, None, {"id": "usr_new", "email": "new@example.com"}])
        user = await find_or_create_user("google", "456", "new@example.com", "New", None)
        assert user.id == "usr_new"
```

### 集成测试

| 测试场景 | 验证点 |
|---------|--------|
| 完整授权流程 | 从登录到获取 JWT 全链路 |
| 已有账号关联 | Google 登录关联到已有邮箱账号 |
| 新用户注册 | 自动创建用户和身份记录 |
| Token 过期刷新 | refresh_token 正确获取新 access_token |
| 无效 Token 处理 | 过期/伪造 Token 返回 401 |
| 重复绑定防护 | 同一 provider_id 不创建重复记录 |

## 相关知识

- [KP-GEN-020] 安全编码基础 — Token 安全存储
- [KP-GEN-021] OWASP Top 10 概述 — 身份认证安全
