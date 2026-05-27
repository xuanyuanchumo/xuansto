---
id: "KP-GEN-020"
type: "security"
category: "secure-coding"
tags: ["安全编码", "输入验证", "输出编码", "认证", "授权", "SQL注入", "XSS", "CSRF"]
version: "1.0.0"
created: "2026-04-28T10:00:00Z"
updated: "2026-04-28T10:00:00Z"
source: "OWASP Secure Coding Practices / CWE/SANS Top 25"
confidence: 0.95
last_validated: "2026-04-28T10:00:00Z"
success_count: 0
failure_count: 0
references:
  - id: "KP-GEN-021"
    relation: "complies"
---

# 安全编码基础

## 概述

安全编码是在软件设计和开发过程中主动防御安全漏洞的实践。核心原则是"永不信任用户输入"，所有外部数据在进入系统时必须经过验证，在输出时必须经过编码。本文涵盖输入验证、输出编码、认证授权三大基础领域。

---

## 输入验证

所有来自外部的数据（用户输入、API 请求、文件内容等）必须被视为不可信，在处理前进行严格验证。

### 验证原则

1. **白名单优先**：优先使用允许列表（白名单）而非拒绝列表（黑名单）
2. **尽早验证**：在数据进入系统的最前端进行验证
3. **服务端验证**：客户端验证仅用于用户体验，服务端验证是安全保障
4. **统一验证**：使用统一的验证框架，避免分散的验证逻辑

### Python 示例

```python
import re
from dataclasses import dataclass
from typing import Optional

@dataclass
class ValidationResult:
    is_valid: bool
    error: Optional[str] = None

def validate_username(username: str) -> ValidationResult:
    if not username or len(username) < 3 or len(username) > 50:
        return ValidationResult(False, "用户名长度须在3-50之间")
    if not re.match(r"^[a-zA-Z0-9_]+$", username):
        return ValidationResult(False, "用户名仅允许字母、数字和下划线")
    return ValidationResult(True)

def validate_email(email: str) -> ValidationResult:
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(pattern, email):
        return ValidationResult(False, "邮箱格式不正确")
    return ValidationResult(True)

def validate_page_params(page: int, size: int) -> ValidationResult:
    if page < 1 or page > 10000:
        return ValidationResult(False, "页码超出范围")
    if size < 1 or size > 100:
        return ValidationResult(False, "每页数量须在1-100之间")
    return ValidationResult(True)
```

### TypeScript 示例

```typescript
import { z } from "zod";

const UsernameSchema = z
  .string()
  .min(3, "用户名长度须在3-50之间")
  .max(50, "用户名长度须在3-50之间")
  .regex(/^[a-zA-Z0-9_]+$/, "用户名仅允许字母、数字和下划线");

const EmailSchema = z.string().email("邮箱格式不正确");

const PaginationSchema = z.object({
  page: z.number().int().min(1).max(10000),
  size: z.number().int().min(1).max(100),
});

type Pagination = z.infer<typeof PaginationSchema>;
```

---

## SQL 注入防护

### 错误模式

```python
username = request.get("username")
cursor.execute(f"SELECT * FROM users WHERE username = '{username}'")
```

```typescript
const username = req.query.username;
await pool.query(`SELECT * FROM users WHERE username = '${username}'`);
```

### 正确模式

```python
cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
```

```typescript
await pool.query("SELECT * FROM users WHERE username = $1", [username]);
```

---

## 输出编码

输出编码确保数据在嵌入到不同上下文（HTML、JavaScript、URL、CSS）时被正确转义，防止 XSS 攻击。

### HTML 上下文编码

```python
import html

def render_user_input(user_input: str) -> str:
    return html.escape(user_input)
```

```typescript
function escapeHtml(input: string): string {
  return input
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#x27;");
}
```

### JavaScript 上下文编码

```typescript
function encodeForJs(input: string): string {
  return JSON.stringify(input);
}
```

### URL 上下文编码

```python
from urllib.parse import quote

def build_url(base: str, user_param: str) -> str:
    return f"{base}?q={quote(user_param, safe='')}"
```

```typescript
function buildUrl(base: string, userParam: string): string {
  return `${base}?q=${encodeURIComponent(userParam)}`;
}
```

---

## 认证最佳实践

### 密码存储

```python
import hashlib
import os
import base64

def hash_password(password: str) -> str:
    salt = os.urandom(16)
    iterations = 600000
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations)
    return f"{iterations}:{base64.b64encode(salt).decode()}:{base64.b64encode(dk).decode()}"

def verify_password(password: str, stored_hash: str) -> bool:
    iterations, salt_b64, dk_b64 = stored_hash.split(":")
    salt = base64.b64decode(salt_b64)
    dk = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt, int(iterations)
    )
    return base64.b64encode(dk).decode() == dk_b64
```

### JWT 安全实践

```typescript
import jwt from "jsonwebtoken";

const JWT_SECRET = process.env.JWT_SECRET;
const TOKEN_EXPIRY = "15m";

function generateToken(userId: string): string {
  return jwt.sign({ sub: userId }, JWT_SECRET, {
    expiresIn: TOKEN_EXPIRY,
    algorithm: "HS256",
  });
}

function verifyToken(token: string): { sub: string } | null {
  try {
    const payload = jwt.verify(token, JWT_SECRET, {
      algorithms: ["HS256"],
    }) as { sub: string };
    return payload;
  } catch {
    return null;
  }
}
```

### 认证安全清单

| 实践 | 说明 |
|------|------|
| 使用强哈希算法 | PBKDF2 / bcrypt / scrypt / Argon2 |
| 盐值唯一 | 每个密码使用独立随机盐 |
| 令牌短有效期 | Access Token 15分钟，Refresh Token 7天 |
| HTTPS 强制 | 所有认证请求必须走 HTTPS |
| 登录限流 | 防止暴力破解，5次失败后锁定15分钟 |
| 多因素认证 | 敏感操作要求 MFA |

---

## 授权最佳实践

### 错误模式：隐式授权

```python
@app.route("/api/users/<user_id>/profile")
def get_profile(user_id):
    return get_user_profile(user_id)
```

### 正确模式：显式授权检查

```python
from functools import wraps

def require_owner(resource_param: str):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            current_user = get_current_user()
            resource_id = kwargs.get(resource_param)
            if not has_permission(current_user, resource_id, "read"):
                return {"error": "权限不足"}, 403
            return f(*args, **kwargs)
        return wrapper
    return decorator

@app.route("/api/users/<user_id>/profile")
@require_owner("user_id")
def get_profile(user_id):
    return get_user_profile(user_id)
```

### TypeScript RBAC 实现

```typescript
type Permission = "read" | "write" | "delete" | "admin";

const ROLE_PERMISSIONS: Record<string, Permission[]> = {
  viewer: ["read"],
  editor: ["read", "write"],
  admin: ["read", "write", "delete", "admin"],
};

function hasPermission(
  userRole: string,
  requiredPermission: Permission,
): boolean {
  const permissions = ROLE_PERMISSIONS[userRole] ?? [];
  return permissions.includes(requiredPermission);
}

function requirePermission(permission: Permission) {
  return (req: any, res: any, next: any) => {
    const userRole = req.user?.role;
    if (!hasPermission(userRole, permission)) {
      return res.status(403).json({ error: "权限不足" });
    }
    next();
  };
}
```

---

## 安全编码检查清单

| 类别 | 检查项 |
|------|--------|
| 输入验证 | 所有外部输入已验证、使用白名单、服务端验证完整 |
| 输出编码 | HTML/JS/URL/CSS 上下文正确编码、模板引擎自动转义 |
| SQL 注入 | 使用参数化查询、ORM 防注入 |
| 认证 | 强密码哈希、令牌安全管理、MFA 支持 |
| 授权 | 最小权限原则、显式权限检查、RBAC/ABAC |
| 敏感数据 | 不记录密码/令牌、日志脱敏、传输加密 |

## 相关知识

- [KP-GEN-021] OWASP Top 10 概述 — 最常见的 Web 安全风险
- [KP-GEN-030] Electron 最佳实践 — 桌面应用安全编码
- [KP-EXP-DSK-001] Electron 上下文隔离经验 — 桌面端安全实践
