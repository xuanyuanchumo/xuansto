---
id: "KP-EXP-SEC-XSS-001"
type: "error-solution"
severity: "high"
category: "security"
tags: ["XSS", "跨站脚本", "CSP", "输出编码", "DOMPurify", "安全"]
version: "1.0.0"
confidence: 0.95
occurrences: 3
---

## XSS 跨站脚本攻击防护 (置信度: 0.95 | 技术栈: Web/React/Vue)

### 现象
用户输入被渲染为 HTML 执行恶意脚本：Cookie 窃取、页面篡改、钓鱼表单注入。

### 根因
未对用户输入进行输出编码、使用 dangerouslySetInnerHTML/v-html 渲染原始 HTML、CSP 未配置或过于宽松。

### 解决方案

```typescript
import DOMPurify from "dompurify";
const safe = DOMPurify.sanitize(userInput);
```

```html
<meta http-equiv="Content-Security-Policy"
  content="default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:">
```

```python
import html
safe_output = html.escape(user_input, quote=True)
```

### 验证
自动化 XSS 扫描（OWASP ZAP），CSP 违规报告监控，输入包含 `<script>` 标签时确认被转义。
