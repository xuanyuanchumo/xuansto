---
id: "KP-GEN-021"
type: "security"
category: "owasp"
tags: ["OWASP", "Top10", "Web安全", "注入", "XSS", "CSRF", "SSRF", "认证失败", "安全配置"]
version: "1.0.0"
confidence: 0.93
---

## OWASP Top 10 概述 (版本: 1.0 | 适用: Web安全)

### 核心规则
- A01 失效访问控制：默认拒绝 + 显式授权，防 IDOR
- A02 加密失败：分类数据敏感度 + TLS 1.2+ + 强加密算法
- A03 注入：参数化查询 + 输入验证，禁止拼接 SQL
- A04 不安全设计：威胁建模 + 安全设计模式
- A05 安全配置错误：最小化安装 + 自动化配置审查 + 安全头
- A06 过时组件：持续监控 CVE + 自动化依赖扫描
- A07 认证失败：MFA + 密码复杂度 + 登录限流
- A08 完整性失败：数字签名 + 安全 CI/CD
- A09 日志监控失败：全面日志 + 实时告警
- A10 SSRF：URL 白名单 + 禁止内网访问

### 代码示例

```python
cursor.execute("SELECT * FROM users WHERE email = %s", (email,))  # 参数化查询
```

```typescript
app.get("/api/orders/:id", async (req, res) => {
  const order = await OrderModel.findById(req.params.id);
  if (order.userId !== req.user.id) return res.status(403).json({ error: "无权访问" });
  res.json(order);
});
```

### 反模式
- ❌ SQL 拼接 `f"WHERE name = '{name}'"` — SQL 注入
- ❌ 无权限检查的 API 端点 — IDOR 越权访问
- ❌ 明文传输敏感数据 — 中间人攻击
