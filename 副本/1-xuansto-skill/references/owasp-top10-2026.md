# OWASP Top 10 2026 参考文档

> 版本: 1.0.0 | 更新日期: 2026-04-17 | 编码: UTF-8 | 行尾: LF

---

## 概述

OWASP Top 10 是Web应用程序最关键安全风险的权威列表，每3-4年更新一次。本文档基于OWASP Top 10最新版本，提供十大安全风险及其防护措施。

---

## 目录

1. [A01:2021 - 访问控制失效](#a012021---访问控制失效)
2. [A02:2021 - 加密失败](#a022021---加密失败)
3. [A03:2021 - 注入](#a032021---注入)
4. [A04:2021 - 不安全设计](#a042021---不安全设计)
5. [A05:2021 - 安全配置错误](#a052021---安全配置错误)
6. [A06:2021 - 脆弱和过时的组件](#a062021---脆弱和过时的组件)
7. [A07:2021 - 身份识别和身份验证失败](#a072021---身份识别和身份验证失败)
8. [A08:2021 - 软件和数据完整性失败](#a082021---软件和数据完整性失败)
9. [A09:2021 - 安全日志和监控失败](#a092021---安全日志和监控失败)
10. [A10:2021 - 服务器端请求伪造(SSRF)](#a102021---服务器端请求伪造ssrf)

---

## A01:2021 - 访问控制失效

### 风险描述

访问控制失效是指系统未能正确实施权限验证，导致用户可以越权访问资源或执行操作。

### 常见场景

- 通过修改URL访问他人账户
- 查看或编辑他人的敏感信息
- 提权操作(普通用户获得管理员权限)
- 元数据操作(修改token、隐藏字段)
- CORS配置错误导致未授权API访问

### 漏洞示例

```javascript
// ❌ 漏洞代码: 未验证资源所有权
app.get('/api/orders/:id', async (req, res) => {
  const order = await Order.findById(req.params.id);
  res.json(order);
});

// 攻击: 用户A可以访问用户B的订单
// GET /api/orders/123 (用户B的订单ID)
```

### 防护措施

```javascript
// ✅ 安全代码: 验证资源所有权
app.get('/api/orders/:id', authenticate, async (req, res) => {
  const order = await Order.findById(req.params.id);
  
  if (order.userId.toString() !== req.user.id) {
    return res.status(403).json({ error: '无权访问' });
  }
  
  res.json(order);
});

// ✅ 使用RBAC
function checkPermission(role, resource, action) {
  const permissions = {
    admin: { orders: ['read', 'write', 'delete'] },
    manager: { orders: ['read', 'write'] },
    user: { orders: ['read'] }
  };
  
  return permissions[role]?.[resource]?.includes(action) ?? false;
}

// ✅ 使用ABAC
function canAccess(user, resource, action) {
  return (
    user.role === 'admin' ||
    resource.ownerId === user.id ||
    (user.department === resource.department && action === 'read')
  );
}
```

### 防护清单

- [ ] 实施默认拒绝策略
- [ ] 验证每个请求的权限
- [ ] 使用RBAC/ABAC模型
- [ ] 禁用目录列表
- [ ] 记录访问控制失败
- [ ] 限制API访问频率
- [ ] JWT令牌设置合理过期时间

---

## A02:2021 - 加密失败

### 风险描述

敏感数据未加密或使用弱加密算法，导致数据泄露风险。

### 常见场景

- 传输中使用HTTP而非HTTPS
- 存储明文密码或使用弱哈希
- 使用过时的加密算法
- 密钥管理不当
- 不验证服务器证书

### 漏洞示例

```javascript
// ❌ 漏洞代码: 明文存储密码
await db.query('INSERT INTO users (email, password) VALUES (?, ?)', 
  [email, password]);

// ❌ 漏洞代码: 使用MD5哈希
const hashedPassword = md5(password);

// ❌ 漏洞代码: 不安全的传输
fetch('http://api.example.com/users', { method: 'POST', body: data });
```

### 防护措施

```javascript
// ✅ 安全代码: 使用bcrypt哈希密码
import bcrypt from 'bcrypt';

const saltRounds = 12;
const hashedPassword = await bcrypt.hash(password, saltRounds);

// ✅ 安全代码: 使用现代加密算法
import crypto from 'crypto';

const algorithm = 'aes-256-gcm';
const key = crypto.scryptSync(masterKey, 'salt', 32);

function encrypt(text) {
  const iv = crypto.randomBytes(16);
  const cipher = crypto.createCipheriv(algorithm, key, iv);
  let encrypted = cipher.update(text, 'utf8', 'hex');
  encrypted += cipher.final('hex');
  const authTag = cipher.getAuthTag();
  return { iv: iv.toString('hex'), encrypted, authTag: authTag.toString('hex') };
}

// ✅ 安全代码: 强制HTTPS
app.use((req, res, next) => {
  if (!req.secure && req.get('x-forwarded-proto') !== 'https') {
    return res.redirect(`https://${req.get('host')}${req.url}`);
  }
  next();
});

// ✅ 安全代码: 安全头设置
res.setHeader('Strict-Transport-Security', 'max-age=31536000; includeSubDomains');
```

### 防护清单

- [ ] 所有传输使用TLS 1.2+
- [ ] 密码使用bcrypt/scrypt/Argon2
- [ ] 敏感数据加密存储
- [ ] 使用强加密算法(AES-256-GCM)
- [ ] 密钥安全存储和轮换
- [ ] 禁用弱密码套件
- [ ] 不在日志中记录敏感数据

---

## A03:2021 - 注入

### 风险描述

用户输入被解释为代码执行，包括SQL注入、命令注入、LDAP注入等。

### 常见场景

- SQL注入
- 命令注入
- LDAP注入
- XPath注入
- NoSQL注入

### 漏洞示例

```javascript
// ❌ SQL注入漏洞
const query = `SELECT * FROM users WHERE id = '${userId}'`;
db.query(query);

// ❌ 命令注入漏洞
exec(`ping ${userInput}`);

// ❌ NoSQL注入漏洞
const query = { $where: `this.name === '${userInput}'` };
```

### 防护措施

```javascript
// ✅ 安全代码: 参数化查询
const query = 'SELECT * FROM users WHERE id = ?';
db.query(query, [userId]);

// ✅ 安全代码: 使用ORM
const user = await User.findByPk(userId);

// ✅ 安全代码: 输入验证
import { z } from 'zod';

const schema = z.object({
  id: z.string().uuid(),
  name: z.string().min(1).max(100).regex(/^[\w\s-]+$/)
});

const validated = schema.parse(userInput);

// ✅ 安全代码: 命令执行白名单
const allowedHosts = ['google.com', 'github.com'];
if (!allowedHosts.includes(userInput)) {
  throw new Error('Invalid host');
}
exec(`ping -c 1 ${userInput}`);
```

### 防护清单

- [ ] 使用参数化查询
- [ ] 验证所有用户输入
- [ ] 使用ORM框架
- [ ] 最小权限数据库账户
- [ ] 输出编码
- [ ] 使用CSP

---

## A04:2021 - 不安全设计

### 风险描述

系统架构和设计阶段未考虑安全因素，导致根本性的安全缺陷。

### 常见场景

- 缺乏安全建模
- 未考虑业务流程安全
- 缺乏速率限制
- 敏感功能缺乏验证

### 漏洞示例

```javascript
// ❌ 设计缺陷: 无速率限制的密码重置
app.post('/api/reset-password', async (req, res) => {
  const user = await User.findByEmail(req.body.email);
  await sendResetEmail(user.email);
  res.json({ message: '邮件已发送' });
});

// 攻击: 可以无限发送邮件，导致邮件轰炸
```

### 防护措施

```javascript
// ✅ 安全设计: 速率限制
import rateLimit from 'express-rate-limit';

const resetLimiter = rateLimit({
  windowMs: 60 * 60 * 1000, // 1小时
  max: 3, // 每IP最多3次
  message: '请求过于频繁，请稍后再试'
});

app.post('/api/reset-password', resetLimiter, async (req, res) => {
  // ...
});

// ✅ 安全设计: 业务流程验证
app.post('/api/transfer', authenticate, async (req, res) => {
  // 1. 验证用户身份
  // 2. 验证交易金额限制
  // 3. 验证收款账户
  // 4. 发送确认通知
  // 5. 记录审计日志
});

// ✅ 安全设计: 威胁建模
/*
 * 威胁建模清单:
 * - 资产识别: 用户数据、交易记录、系统配置
 * - 威胁识别: 数据泄露、未授权访问、拒绝服务
 * - 威胁评估: 可能性 × 影响 = 风险等级
 * - 缓解措施: 针对高/中风险实施控制
 */
```

### 防护清单

- [ ] 进行威胁建模
- [ ] 实施安全开发生命周期
- [ ] 建立安全参考架构
- [ ] 实施速率限制
- [ ] 设计安全的业务流程
- [ ] 进行安全架构审查

---

## A05:2021 - 安全配置错误

### 风险描述

安全配置不当或缺失，导致系统暴露于攻击风险。

### 常见场景

- 使用默认账户和密码
- 目录列表未禁用
- 错误信息泄露敏感数据
- 不必要的功能启用
- 安全头缺失

### 漏洞示例

```javascript
// ❌ 配置错误: 暴露错误堆栈
app.use((err, req, res, next) => {
  res.status(500).json({ error: err.stack });
});

// ❌ 配置错误: 使用默认配置
app.use(session({
  secret: 'keyboard cat', // 默认密钥
  cookie: { secure: false } // 不安全Cookie
}));

// ❌ 配置错误: 暴露服务器信息
app.use((req, res, next) => {
  res.setHeader('X-Powered-By', 'Express 4.18.2');
  next();
});
```

### 防护措施

```javascript
// ✅ 安全配置: 使用Helmet
import helmet from 'helmet';

app.use(helmet());
app.use(helmet.contentSecurityPolicy({
  directives: {
    defaultSrc: ["'self'"],
    scriptSrc: ["'self'"],
    styleSrc: ["'self'", "'unsafe-inline'"],
    imgSrc: ["'self'", 'data:'],
    connectSrc: ["'self'"],
    fontSrc: ["'self'"],
    objectSrc: ["'none'"],
    frameAncestors: ["'none'"]
  }
}));

// ✅ 安全配置: 安全的Session配置
app.use(session({
  secret: process.env.SESSION_SECRET,
  resave: false,
  saveUninitialized: false,
  cookie: {
    httpOnly: true,
    secure: true,
    sameSite: 'strict',
    maxAge: 3600000
  }
}));

// ✅ 安全配置: 生产环境错误处理
app.use((err, req, res, next) => {
  console.error(err);
  res.status(500).json({ 
    error: process.env.NODE_ENV === 'production' 
      ? '服务器错误' 
      : err.message 
  });
});
```

### 防护清单

- [ ] 删除默认账户
- [ ] 禁用不必要的功能
- [ ] 配置安全响应头
- [ ] 禁用目录列表
- [ ] 生产环境关闭调试模式
- [ ] 定期审计配置
- [ ] 使用配置管理工具

---

## A06:2021 - 脆弱和过时的组件

### 风险描述

使用已知漏洞的库、框架或组件。

### 常见场景

- 未更新的依赖包
- 不支持的框架版本
- 已知漏洞的组件

### 防护措施

```bash
# ✅ 定期检查依赖漏洞
npm audit
npm audit fix

# ✅ 使用依赖检查工具
npx better-npm-audit audit

# ✅ 使用OWASP Dependency-Check
dependency-check --scan ./

# ✅ 使用Snyk
npx snyk test
```

```javascript
// ✅ package.json配置
{
  "scripts": {
    "audit": "npm audit --audit-level=moderate",
    "outdated": "npm outdated"
  },
  "engines": {
    "node": ">=18.0.0"
  }
}
```

### 防护清单

- [ ] 定期更新依赖
- [ ] 移除未使用的依赖
- [ ] 订阅安全公告
- [ ] 使用依赖检查工具
- [ ] 锁定依赖版本
- [ ] 监控漏洞数据库

---

## A07:2021 - 身份识别和身份验证失败

### 风险描述

身份验证机制存在缺陷，导致攻击者可以冒充用户。

### 常见场景

- 弱密码策略
- 凭证填充攻击
- 会话ID暴露
- 会话固定攻击
- 多因素认证缺失

### 漏洞示例

```javascript
// ❌ 漏洞代码: 弱密码策略
app.post('/register', async (req, res) => {
  const { email, password } = req.body;
  await User.create({ email, password }); // 无密码强度验证
});

// ❌ 漏洞代码: 会话固定
app.post('/login', (req, res) => {
  // 登录后不重新生成session ID
  req.session.userId = user.id;
});
```

### 防护措施

```javascript
// ✅ 安全代码: 强密码策略
import { z } from 'zod';

const passwordSchema = z.string()
  .min(12, '密码至少12个字符')
  .regex(/[A-Z]/, '需要大写字母')
  .regex(/[a-z]/, '需要小写字母')
  .regex(/[0-9]/, '需要数字')
  .regex(/[^A-Za-z0-9]/, '需要特殊字符');

// ✅ 安全代码: 登录后重新生成session
app.post('/login', async (req, res) => {
  const user = await authenticateUser(req.body);
  
  // 重新生成session ID
  req.session.regenerate(() => {
    req.session.userId = user.id;
    res.json({ success: true });
  });
});

// ✅ 安全代码: 多因素认证
import speakeasy from 'speakeasy';

// 生成MFA密钥
const secret = speakeasy.generateSecret({ length: 20 });

// 验证MFA代码
const isValid = speakeasy.totp.verify({
  secret: user.mfaSecret,
  encoding: 'base32',
  token: userInputToken
});

// ✅ 安全代码: 登录失败限制
const loginAttempts = new Map();

function checkLoginAttempts(email) {
  const attempts = loginAttempts.get(email) || { count: 0, lastAttempt: 0 };
  
  if (attempts.count >= 5 && Date.now() - attempts.lastAttempt < 15 * 60 * 1000) {
    throw new Error('账户已锁定，请15分钟后再试');
  }
  
  return attempts;
}
```

### 防护清单

- [ ] 实施强密码策略
- [ ] 支持多因素认证
- [ ] 限制登录尝试次数
- [ ] 登录后重新生成session
- [ ] 使用安全的密码恢复流程
- [ ] 记录认证失败事件

---

## A08:2021 - 软件和数据完整性失败

### 风险描述

未验证代码或数据的完整性，导致恶意代码或数据注入。

### 常见场景

- 不安全的反序列化
- 自动更新无签名验证
- CI/CD管道不安全
- 依赖包被篡改

### 漏洞示例

```javascript
// ❌ 漏洞代码: 不安全的反序列化
const obj = eval(`(${userInput})`);

// ❌ 漏洞代码: 无签名验证的更新
const update = await fetch('http://update.example.com/latest');
eval(await update.text());
```

### 防护措施

```javascript
// ✅ 安全代码: 使用JSON.parse
const obj = JSON.parse(userInput);

// ✅ 安全代码: 验证签名
import crypto from 'crypto';

function verifySignature(data, signature, publicKey) {
  const verify = crypto.createVerify('RSA-SHA256');
  verify.update(data);
  return verify.verify(publicKey, signature, 'base64');
}

// ✅ 安全代码: 使用锁文件
// package-lock.json, yarn.lock, pnpm-lock.yaml

// ✅ 安全代码: CI/CD安全
// - 使用受保护的分支
// - 要求PR审查
// - 使用签名提交
// - 限制CI/CD权限
```

### 防护清单

- [ ] 使用签名验证
- [ ] 使用安全的反序列化
- [ ] 保护CI/CD管道
- [ ] 使用锁文件
- [ ] 验证依赖完整性
- [ ] 实施代码审查

---

## A09:2021 - 安全日志和监控失败

### 风险描述

缺乏足够的日志记录和监控，无法检测和响应安全事件。

### 常见场景

- 未记录安全事件
- 日志不包含关键信息
- 无告警机制
- 日志可被篡改

### 漏洞示例

```javascript
// ❌ 漏洞代码: 不记录安全事件
app.post('/login', async (req, res) => {
  const user = await authenticate(req.body);
  if (!user) {
    return res.status(401).json({ error: '认证失败' }); // 未记录
  }
  res.json({ token: generateToken(user) });
});
```

### 防护措施

```javascript
// ✅ 安全代码: 记录安全事件
import pino from 'pino';

const logger = pino({
  level: 'info',
  redact: ['password', 'token', 'creditCard']
});

app.post('/login', async (req, res) => {
  const { email } = req.body;
  
  try {
    const user = await authenticate(req.body);
    
    if (!user) {
      logger.warn({
        event: 'LOGIN_FAILED',
        email,
        ip: req.ip,
        userAgent: req.get('user-agent')
      });
      return res.status(401).json({ error: '认证失败' });
    }
    
    logger.info({
      event: 'LOGIN_SUCCESS',
      userId: user.id,
      ip: req.ip
    });
    
    res.json({ token: generateToken(user) });
  } catch (error) {
    logger.error({
      event: 'LOGIN_ERROR',
      email,
      error: error.message
    });
    res.status(500).json({ error: '服务器错误' });
  }
});

// ✅ 安全代码: 告警机制
const alertThreshold = {
  loginFailures: 5,
  timeWindow: 5 * 60 * 1000 // 5分钟
};

async function checkSuspiciousActivity(userId) {
  const failures = await getRecentLoginFailures(userId, alertThreshold.timeWindow);
  
  if (failures >= alertThreshold.loginFailures) {
    await sendSecurityAlert(userId, '检测到可疑登录活动');
    await lockAccount(userId);
  }
}
```

### 防护清单

- [ ] 记录所有安全事件
- [ ] 日志包含足够上下文
- [ ] 保护日志完整性
- [ ] 设置告警阈值
- [ ] 定期审计日志
- [ ] 建立响应流程

---

## A10:2021 - 服务器端请求伪造(SSRF)

### 风险描述

服务器被诱导向非预期目标发起请求。

### 常见场景

- 获取远程资源功能
- Webhook回调
- 文件导入功能

### 漏洞示例

```javascript
// ❌ 漏洞代码: 无验证的URL获取
app.get('/fetch', async (req, res) => {
  const response = await fetch(req.query.url);
  res.send(await response.text());
});

// 攻击: ?url=http://localhost:8080/admin
// 攻击: ?url=http://169.254.169.254/latest/meta-data/
```

### 防护措施

```javascript
// ✅ 安全代码: URL白名单
const allowedDomains = ['api.example.com', 'cdn.example.com'];

app.get('/fetch', async (req, res) => {
  const url = new URL(req.query.url);
  
  if (!allowedDomains.includes(url.hostname)) {
    return res.status(403).json({ error: '禁止访问' });
  }
  
  const response = await fetch(url.toString());
  res.send(await response.text());
});

// ✅ 安全代码: 阻止私有IP
import { isPrivate } from 'ip';

async function isAllowedUrl(urlString) {
  const url = new URL(urlString);
  
  // 检查协议
  if (!['http:', 'https:'].includes(url.protocol)) {
    return false;
  }
  
  // 检查是否为私有IP
  const { address } = await dns.lookup(url.hostname);
  if (isPrivate(address)) {
    return false;
  }
  
  // 检查是否为本地地址
  const blockedIPs = ['127.0.0.1', '0.0.0.0', '::1'];
  if (blockedIPs.includes(address)) {
    return false;
  }
  
  return true;
}

// ✅ 安全代码: 使用代理隔离
// 将URL获取功能部署在隔离的网络环境中
```

### 防护清单

- [ ] 实施URL白名单
- [ ] 阻止私有IP访问
- [ ] 验证协议类型
- [ ] 使用网络隔离
- [ ] 限制响应大小
- [ ] 禁用不必要的重定向

---

## 快速参考表

| 风险 | 关键防护措施 |
|------|-------------|
| A01 访问控制失效 | RBAC/ABAC、默认拒绝、权限验证 |
| A02 加密失败 | TLS、强哈希、密钥管理 |
| A03 注入 | 参数化查询、输入验证、ORM |
| A04 不安全设计 | 威胁建模、安全架构、速率限制 |
| A05 安全配置错误 | 安全头、移除默认配置、错误处理 |
| A06 脆弱组件 | 依赖更新、漏洞扫描、版本锁定 |
| A07 身份验证失败 | MFA、强密码、会话管理 |
| A08 完整性失败 | 签名验证、安全反序列化 |
| A09 日志监控失败 | 安全日志、告警机制、审计 |
| A10 SSRF | URL白名单、私有IP阻止、网络隔离 |

---

## 参考资料

- [OWASP Top 10 官方网站](https://owasp.org/www-project-top-ten/)
- [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/)
- [OWASP Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)
- [OWASP ASVS](https://owasp.org/www-project-application-security-verification-standard/)

---

> 本文档由 Multi-Agent SDD/TDD Orchestrator 维护 | 最后更新: 2026-04-17
