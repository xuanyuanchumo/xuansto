---
id: "KP-GEN-020"
type: "security"
category: "secure-coding"
tags: ["安全编码", "输入验证", "输出编码", "认证", "授权", "SQL注入", "XSS", "CSRF"]
version: "1.0.0"
confidence: 0.95
---

## 安全编码基础 (版本: 1.0 | 适用: Python/TypeScript)

### 核心规则
- 永不信任用户输入，所有外部数据进入系统前必须验证
- 白名单优先，服务端验证是安全保障，客户端仅改善体验
- 输出编码：HTML/JS/URL/CSS 各上下文正确转义，防 XSS
- SQL 注入防护：必须使用参数化查询，禁止字符串拼接
- 密码存储：使用 Argon2id/bcrypt/scrypt，禁止 MD5/SHA 直接哈希
- JWT：短有效期（Access 15min）+ Refresh Token 轮换
- 授权：最小权限原则 + 显式权限检查 + RBAC

### 代码示例

```python
cursor.execute("SELECT * FROM users WHERE email = %s", (email,))  # 参数化查询
html.escape(user_input, quote=True)  # HTML 输出编码
```

```typescript
import { z } from "zod";
const EmailSchema = z.string().email();

function hasPermission(role: string, perm: Permission): boolean {
  return (ROLE_PERMISSIONS[role] ?? []).includes(perm);
}
```

### 反模式
- ❌ `f"SELECT * FROM users WHERE name = '{name}'"` — SQL 注入
- ❌ 直接渲染用户输入到 HTML — XSS 攻击
- ❌ 密码用 MD5 哈希 — 易被彩虹表破解
