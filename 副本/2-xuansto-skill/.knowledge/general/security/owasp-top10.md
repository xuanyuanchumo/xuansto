---
id: "KP-GEN-021"
type: "security"
category: "owasp"
tags: ["OWASP", "Top10", "Web安全", "注入", "XSS", "CSRF", "SSRF", "认证失败", "安全配置"]
version: "1.0.0"
created: "2026-04-28T10:00:00Z"
updated: "2026-04-28T10:00:00Z"
source: "OWASP Top 10:2025 / OWASP Foundation"
confidence: 0.93
last_validated: "2026-04-28T10:00:00Z"
success_count: 0
failure_count: 0
references:
  - id: "KP-GEN-020"
    relation: "complies"
---

# OWASP Top 10 概述

## 概述

OWASP Top 10 是开放 Web 应用安全项目（OWASP）发布的十大最关键 Web 应用安全风险清单，每3-4年更新一次。以下基于 OWASP Top 10:2025 版本，概述每项风险及其预防措施。

---

## A01:2021 - 失效的访问控制 (Broken Access Control)

| 项目 | 说明 |
|------|------|
| **风险描述** | 用户可以越权访问超出其权限范围的资源或执行未授权操作 |
| **常见表现** | URL 强制浏览、IDOR（不安全的直接对象引用）、CORS 配置错误、API 端点未做权限校验 |
| **预防措施** | 默认拒绝、最小权限原则、显式权限检查、服务端强制访问控制、禁用目录列表 |

### IDOR 示例

```typescript
app.get("/api/orders/:id", async (req, res) => {
  const order = await OrderModel.findById(req.params.id);
  if (!order) return res.status(404).json({ error: "订单不存在" });
  if (order.userId !== req.user.id) {
    return res.status(403).json({ error: "无权访问此订单" });
  }
  res.json(order);
});
```

---

## A02:2021 - 加密机制失败 (Cryptographic Failures)

| 项目 | 说明 |
|------|------|
| **风险描述** | 敏感数据未加密或使用了弱加密算法，导致数据泄露 |
| **常见表现** | 明文传输敏感数据、使用 MD5/SHA1 哈希、硬编码密钥、弱随机数生成器 |
| **预防措施** | 分类数据敏感度、传输层强制 TLS 1.2+、存储层使用强加密算法、密钥安全管理 |

### 正确的加密实践

```python
from cryptography.fernet import Fernet

key = Fernet.generate_key()
cipher = Fernet(key)

def encrypt_data(plaintext: str) -> bytes:
    return cipher.encrypt(plaintext.encode())

def decrypt_data(ciphertext: bytes) -> str:
    return cipher.decrypt(ciphertext).decode()
```

---

## A03:2021 - 注入 (Injection)

| 项目 | 说明 |
|------|------|
| **风险描述** | 不受信任的数据作为命令或查询的一部分发送给解释器，导致非预期执行 |
| **常见表现** | SQL 注入、NoSQL 注入、OS 命令注入、LDAP 注入 |
| **预防措施** | 参数化查询、输入验证、ORM 使用、最小权限数据库账户 |

### 参数化查询

```python
cursor.execute(
    "SELECT id, name FROM users WHERE email = %s AND status = %s",
    (email, "active"),
)
```

```typescript
await pool.query(
  "SELECT id, name FROM users WHERE email = $1 AND status = $2",
  [email, "active"],
);
```

---

## A04:2021 - 不安全设计 (Insecure Design)

| 项目 | 说明 |
|------|------|
| **风险描述** | 缺乏安全控制的设计缺陷，无法通过更好的实现来弥补 |
| **常见表现** | 缺少威胁建模、业务流程未考虑滥用场景、缺少安全设计模式 |
| **预防措施** | 安全设计模式、威胁建模、安全用户故事、架构风险分析 |

---

## A05:2021 - 安全配置错误 (Security Misconfiguration)

| 项目 | 说明 |
|------|------|
| **风险描述** | 应用、服务器或框架的安全配置不当或缺失 |
| **常见表现** | 默认账户未改、不必要的功能启用、错误信息泄露堆栈、缺少安全头 |
| **预防措施** | 最小化安装、自动化配置审查、安全头配置、环境隔离 |

### 安全头配置

```typescript
app.use((req, res, next) => {
  res.setHeader("X-Content-Type-Options", "nosniff");
  res.setHeader("X-Frame-Options", "DENY");
  res.setHeader("X-XSS-Protection", "0");
  res.setHeader(
    "Strict-Transport-Security",
    "max-age=31536000; includeSubDomains",
  );
  res.setHeader(
    "Content-Security-Policy",
    "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'",
  );
  next();
});
```

---

## A06:2021 - 易受攻击和过时的组件 (Vulnerable and Outdated Components)

| 项目 | 说明 |
|------|------|
| **风险描述** | 使用了已知存在安全漏洞的组件或过时的依赖 |
| **常见表现** | 未及时更新依赖、使用已废弃的库版本、未监控 CVE 公告 |
| **预防措施** | 持续监控依赖漏洞、自动化依赖扫描、移除未使用依赖、仅从可信源获取组件 |

### 依赖扫描

```bash
npm audit
pip audit
safety check --full-report
```

---

## A07:2021 - 身份识别和认证失败 (Identification and Authentication Failures)

| 项目 | 说明 |
|------|------|
| **风险描述** | 认证机制实现不当，允许攻击者冒充合法用户 |
| **常见表现** | 允许弱密码、暴力破解无防护、会话管理不当、凭证恢复流程不安全 |
| **预防措施** | 多因素认证、密码复杂度策略、登录限流、安全会话管理 |

---

## A08:2021 - 软件和数据完整性失败 (Software and Data Integrity Failures)

| 项目 | 说明 |
|------|------|
| **风险描述** | 在不验证完整性的情况下使用来自不受信任来源的软件或数据 |
| **常见表现** | 不安全的 CI/CD 管道、自动更新未签名验证、反序列化不受信任数据 |
| **预防措施** | 数字签名验证、安全 CI/CD 管道、完整性校验、避免不安全的反序列化 |

---

## A09:2021 - 安全日志和监控失败 (Security Logging and Monitoring Failures)

| 项目 | 说明 |
|------|------|
| **风险描述** | 缺乏足够的日志记录和监控，无法检测和响应安全事件 |
| **常见表现** | 登录失败未记录、敏感操作无审计、无入侵检测、日志未集中管理 |
| **预防措施** | 记录所有认证事件、集中日志管理、实时告警、定期安全审计 |

### 安全日志实践

```python
import logging
import structlog

logger = structlog.get_logger()

def handle_login(username: str, success: bool, ip_address: str):
    event = "login_success" if success else "login_failure"
    logger.info(
        event,
        username=username,
        ip_address=ip_address,
        success=success,
        timestamp=datetime.utcnow().isoformat(),
    )
    if not success:
        failed_count = get_recent_failed_attempts(username, minutes=15)
        if failed_count >= 5:
            logger.warning(
                "brute_force_detected",
                username=username,
                ip_address=ip_address,
                failed_count=failed_count,
            )
```

---

## A10:2021 - 服务器端请求伪造 (Server-Side Request Forgery, SSRF)

| 项目 | 说明 |
|------|------|
| **风险描述** | 应用在获取远程资源时未验证用户提供的 URL，导致向非预期目标发送请求 |
| **常见表现** | URL 获取功能未限制目标、可访问内网服务、云元数据 API 可达 |
| **预防措施** | URL 白名单、禁止内网地址访问、网络分段、禁用 HTTP 重定向 |

### SSRF 防护

```python
import ipaddress
from urllib.parse import urlparse

BLOCKED_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
]

def is_url_allowed(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return False
    try:
        host_ip = ipaddress.ip_address(parsed.hostname)
        for network in BLOCKED_NETWORKS:
            if host_ip in network:
                return False
    except ValueError:
        pass
    return True
```

---

## 预防措施总览

| 风险 | 核心预防策略 |
|------|-------------|
| 失效的访问控制 | 默认拒绝 + 显式授权 |
| 加密机制失败 | 分类数据 + 强加密 + TLS |
| 注入 | 参数化查询 + 输入验证 |
| 不安全设计 | 威胁建模 + 安全设计模式 |
| 安全配置错误 | 最小化 + 自动化审查 |
| 过时组件 | 持续监控 + 自动化扫描 |
| 认证失败 | MFA + 限流 + 安全会话 |
| 完整性失败 | 数字签名 + 安全 CI/CD |
| 日志监控失败 | 全面日志 + 实时告警 |
| SSRF | URL 白名单 + 网络分段 |

## 相关知识

- [KP-GEN-020] 安全编码基础 — 输入验证、输出编码、认证最佳实践
- [KP-GEN-030] Electron 最佳实践 — 桌面应用安全配置
- [KP-EXP-DSK-001] Electron 上下文隔离经验 — 桌面端安全防护
