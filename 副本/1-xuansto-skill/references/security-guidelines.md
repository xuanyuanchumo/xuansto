# 安全指南参考文档

> 版本: 1.0.0 | 更新日期: 2026-04-17 | 编码: UTF-8 | 行尾: LF

---

## 目录

1. [安全编码实践](#安全编码实践)
2. [常见漏洞防护](#常见漏洞防护)
3. [敏感数据处理](#敏感数据处理)

---

## 安全编码实践

### 核心原则

| 原则 | 说明 |
|------|------|
| 最小权限 | 只授予必要的最小权限 |
| 纵深防御 | 多层安全防护机制 |
| 安全默认 | 默认配置应为最安全状态 |
| 失败安全 | 失败时应处于安全状态 |
| 输入验证 | 所有外部输入都不可信 |

### 输入验证

```javascript
// ❌ 不安全: 直接使用用户输入
const query = `SELECT * FROM users WHERE id = '${userId}'`;

// ✅ 安全: 使用参数化查询
const query = 'SELECT * FROM users WHERE id = ?';
db.query(query, [userId]);

// ✅ 安全: 使用验证库
import { z } from 'zod';

const userSchema = z.object({
  email: z.string().email(),
  age: z.number().int().min(0).max(150),
  name: z.string().min(1).max(100).regex(/^[\w\s-]+$/)
});

const validatedData = userSchema.parse(userInput);
```

### 输出编码

```javascript
// ❌ 不安全: 直接输出用户内容
res.send(`<div>${userContent}</div>`);

// ✅ 安全: 使用模板引擎自动转义
res.render('template', { content: userContent });

// ✅ 安全: 手动转义
import { escape } from 'html-escaper';
res.send(`<div>${escape(userContent)}</div>`);

// ✅ 安全: 设置Content-Type
res.setHeader('Content-Type', 'text/html; charset=utf-8');
```

### 认证安全

```javascript
// 密码存储
import bcrypt from 'bcrypt';

// ✅ 安全: 使用bcrypt哈希
const saltRounds = 12;
const hashedPassword = await bcrypt.hash(password, saltRounds);

// ✅ 安全: 验证密码
const isValid = await bcrypt.compare(password, hashedPassword);

// ❌ 不安全: 明文存储或弱哈希
const stored = password; // 永远不要这样做
const stored = md5(password); // MD5已不安全
const stored = sha1(password); // SHA1已不安全

// Session安全
app.use(session({
  secret: process.env.SESSION_SECRET,
  resave: false,
  saveUninitialized: false,
  cookie: {
    httpOnly: true,
    secure: true, // HTTPS
    sameSite: 'strict',
    maxAge: 3600000 // 1小时
  }
}));
```

### 授权检查

```javascript
// ✅ 安全: 每个操作都检查权限
async function deleteUser(userId, requesterId) {
  const requester = await getUser(requesterId);
  
  if (!requester.isAdmin && requester.id !== userId) {
    throw new ForbiddenError('无权执行此操作');
  }
  
  await deleteUserFromDb(userId);
}

// ✅ 安全: 使用RBAC
const permissions = {
  admin: ['read', 'write', 'delete'],
  editor: ['read', 'write'],
  viewer: ['read']
};

function hasPermission(role, action) {
  return permissions[role]?.includes(action) ?? false;
}
```

### 安全头设置

```javascript
// Express安全头配置
import helmet from 'helmet';

app.use(helmet());

// 或手动配置
app.use((req, res, next) => {
  res.setHeader('X-Content-Type-Options', 'nosniff');
  res.setHeader('X-Frame-Options', 'DENY');
  res.setHeader('X-XSS-Protection', '1; mode=block');
  res.setHeader('Strict-Transport-Security', 'max-age=31536000; includeSubDomains');
  res.setHeader('Content-Security-Policy', "default-src 'self'");
  res.setHeader('Referrer-Policy', 'strict-origin-when-cross-origin');
  res.removeHeader('X-Powered-By');
  next();
});
```

---

## 常见漏洞防护

### SQL注入

**漏洞描述**: 攻击者通过输入恶意SQL代码操作数据库

```javascript
// ❌ 漏洞代码
app.get('/users', (req, res) => {
  const query = `SELECT * FROM users WHERE name = '${req.query.name}'`;
  db.query(query, (err, results) => {
    res.json(results);
  });
});

// 攻击: ?name=' OR '1'='1' --

// ✅ 安全代码
app.get('/users', async (req, res) => {
  const query = 'SELECT * FROM users WHERE name = ?';
  const results = await db.query(query, [req.query.name]);
  res.json(results);
});

// ✅ 使用ORM
const users = await User.findAll({
  where: { name: req.query.name }
});
```

### XSS (跨站脚本攻击)

**漏洞描述**: 攻击者注入恶意脚本到网页

```javascript
// ❌ 漏洞代码
app.get('/search', (req, res) => {
  res.send(`<h1>搜索结果: ${req.query.q}</h1>`);
});

// 攻击: ?q=<script>alert('XSS')</script>

// ✅ 安全代码
import { escape } from 'html-escaper';

app.get('/search', (req, res) => {
  res.send(`<h1>搜索结果: ${escape(req.query.q)}</h1>`);
});

// ✅ 使用CSP
res.setHeader(
  'Content-Security-Policy',
  "default-src 'self'; script-src 'self'"
);
```

### CSRF (跨站请求伪造)

**漏洞描述**: 攻击者诱导用户执行非预期操作

```javascript
// ✅ 使用CSRF Token
import csrf from 'csurf';

const csrfProtection = csrf({ cookie: true });

app.get('/form', csrfProtection, (req, res) => {
  res.render('form', { csrfToken: req.csrfToken() });
});

app.post('/submit', csrfProtection, (req, res) => {
  // CSRF Token已验证
  res.send('提交成功');
});

// 前端表单
// <input type="hidden" name="_csrf" value="{{csrfToken}}">

// ✅ 使用SameSite Cookie
app.use(session({
  cookie: {
    sameSite: 'strict'
  }
}));
```

### 命令注入

**漏洞描述**: 攻击者执行系统命令

```javascript
// ❌ 漏洞代码
app.get('/ping', (req, res) => {
  exec(`ping -c 4 ${req.query.host}`, (err, stdout) => {
    res.send(stdout);
  });
});

// 攻击: ?host=google.com; rm -rf /

// ✅ 安全代码: 验证输入
app.get('/ping', (req, res) => {
  const host = req.query.host;
  
  // 白名单验证
  if (!/^[a-zA-Z0-9.-]+$/.test(host)) {
    return res.status(400).send('无效的主机名');
  }
  
  exec(`ping -c 4 ${host}`, (err, stdout) => {
    res.send(stdout);
  });
});

// ✅ 更安全: 使用参数化命令
const { spawn } = require('child_process');
app.get('/ping', (req, res) => {
  const ping = spawn('ping', ['-c', '4', req.query.host]);
  ping.stdout.on('data', data => res.write(data));
  ping.on('close', () => res.end());
});
```

### 路径遍历

**漏洞描述**: 攻击者访问非授权文件

```javascript
// ❌ 漏洞代码
app.get('/files', (req, res) => {
  res.sendFile(`/uploads/${req.query.filename}`);
});

// 攻击: ?filename=../../../etc/passwd

// ✅ 安全代码
import path from 'path';

app.get('/files', (req, res) => {
  const uploadsDir = path.resolve('/uploads');
  const filePath = path.resolve(uploadsDir, req.query.filename);
  
  // 检查路径是否在允许目录内
  if (!filePath.startsWith(uploadsDir)) {
    return res.status(403).send('禁止访问');
  }
  
  res.sendFile(filePath);
});

// ✅ 使用白名单
const allowedFiles = ['report.pdf', 'data.csv'];
if (!allowedFiles.includes(req.query.filename)) {
  return res.status(403).send('文件不存在');
}
```

### 不安全的反序列化

**漏洞描述**: 反序列化恶意数据导致代码执行

```javascript
// ❌ 漏洞代码
const data = JSON.parse(userInput);
const obj = eval(`(${userInput})`); // 极其危险

// ✅ 安全代码
import { z } from 'zod';

const schema = z.object({
  name: z.string(),
  age: z.number()
});

const data = schema.parse(JSON.parse(userInput));

// ✅ 使用安全的序列化库
import { serialize, deserialize } from 'v8';

// 只反序列化可信数据
const obj = deserialize(trustedBuffer);
```

### XXE (XML外部实体)

**漏洞描述**: 通过XML解析器访问外部资源

```javascript
// ❌ 漏洞代码
import { parseString } from 'xml2js';

parseString(xmlInput, (err, result) => {
  // 可能遭受XXE攻击
});

// ✅ 安全代码
import { parseString } from 'xml2js';

parseString(xmlInput, {
  explicitArray: false,
  // 禁用外部实体
  doctype: undefined,
  xmlns: false
}, (err, result) => {
  // 安全处理
});

// ✅ 使用JSON替代XML
const data = JSON.parse(jsonInput);
```

### SSRF (服务器端请求伪造)

**漏洞描述**: 攻击者让服务器访问内部资源

```javascript
// ❌ 漏洞代码
app.get('/fetch', async (req, res) => {
  const response = await fetch(req.query.url);
  res.send(await response.text());
});

// 攻击: ?url=http://localhost:8080/admin

// ✅ 安全代码
const allowedDomains = ['api.example.com', 'cdn.example.com'];

app.get('/fetch', async (req, res) => {
  const url = new URL(req.query.url);
  
  if (!allowedDomains.includes(url.hostname)) {
    return res.status(403).send('禁止访问');
  }
  
  // 禁止访问私有IP
  const ip = await dns.lookup(url.hostname);
  if (isPrivateIP(ip.address)) {
    return res.status(403).send('禁止访问');
  }
  
  const response = await fetch(url.toString());
  res.send(await response.text());
});
```

---

## 敏感数据处理

### 数据分类

| 级别 | 类型 | 示例 | 处理要求 |
|------|------|------|----------|
| 极高敏感 | 身份认证 | 密码、密钥、生物特征 | 加密存储、不记录日志 |
| 高敏感 | 个人隐私 | 身份证、银行卡、地址 | 加密存储、访问控制 |
| 中敏感 | 业务数据 | 交易记录、联系方式 | 访问控制、审计日志 |
| 低敏感 | 公开数据 | 产品信息、公告 | 基本访问控制 |

### 加密存储

```javascript
import crypto from 'crypto';

// 对称加密
const algorithm = 'aes-256-gcm';
const key = crypto.randomBytes(32);

function encrypt(text) {
  const iv = crypto.randomBytes(16);
  const cipher = crypto.createCipheriv(algorithm, key, iv);
  
  let encrypted = cipher.update(text, 'utf8', 'hex');
  encrypted += cipher.final('hex');
  
  const authTag = cipher.getAuthTag();
  
  return {
    iv: iv.toString('hex'),
    encrypted,
    authTag: authTag.toString('hex')
  };
}

function decrypt(encrypted, iv, authTag) {
  const decipher = crypto.createDecipheriv(
    algorithm,
    key,
    Buffer.from(iv, 'hex')
  );
  
  decipher.setAuthTag(Buffer.from(authTag, 'hex'));
  
  let decrypted = decipher.update(encrypted, 'hex', 'utf8');
  decrypted += decipher.final('utf8');
  
  return decrypted;
}
```

### 密钥管理

```javascript
// ❌ 不安全: 硬编码密钥
const apiKey = 'sk-1234567890abcdef';

// ✅ 安全: 使用环境变量
const apiKey = process.env.API_KEY;

// ✅ 更安全: 使用密钥管理服务
import { SecretsManager } from '@aws-sdk/client-secrets-manager';

async function getSecret(secretName) {
  const client = new SecretsManager();
  const response = await client.getSecretValue({ SecretId: secretName });
  return JSON.parse(response.SecretString);
}

// ✅ 密钥轮换
async function rotateKey() {
  const newKey = crypto.randomBytes(32);
  await storeKey('current', newKey);
  await storeKey('previous', currentKey);
}
```

### 日志安全

```javascript
// ❌ 不安全: 记录敏感信息
console.log(`User login: ${email}, password: ${password}`);

// ✅ 安全: 脱敏处理
console.log(`User login: ${maskEmail(email)}`);

function maskEmail(email) {
  const [local, domain] = email.split('@');
  return `${local[0]}***@${domain}`;
}

// ✅ 敏感字段过滤
const sensitiveFields = ['password', 'token', 'ssn', 'creditCard'];

function sanitizeLog(data) {
  const sanitized = { ...data };
  for (const field of sensitiveFields) {
    if (sanitized[field]) {
      sanitized[field] = '[REDACTED]';
    }
  }
  return sanitized;
}

// ✅ 使用安全的日志库
import pino from 'pino';

const logger = pino({
  redact: ['password', 'token', 'ssn', 'creditCard']
});
```

### 数据传输

```javascript
// ✅ 强制HTTPS
app.use((req, res, next) => {
  if (!req.secure && req.get('x-forwarded-proto') !== 'https') {
    return res.redirect(`https://${req.get('host')}${req.url}`);
  }
  next();
});

// ✅ HSTS头
res.setHeader(
  'Strict-Transport-Security',
  'max-age=31536000; includeSubDomains; preload'
);

// ✅ 安全的API响应
app.get('/user/:id', async (req, res) => {
  const user = await getUser(req.params.id);
  
  // 过滤敏感字段
  const safeUser = {
    id: user.id,
    name: user.name,
    email: maskEmail(user.email)
  };
  
  res.json(safeUser);
});
```

### 数据备份安全

```javascript
// ✅ 加密备份
async function createBackup() {
  const data = await exportData();
  const encrypted = encrypt(JSON.stringify(data));
  
  await storage.upload('backup.enc', encrypted, {
    serverSideEncryption: 'AES256'
  });
}

// ✅ 访问控制
const backupPolicy = {
  Version: '2012-10-17',
  Statement: [{
    Effect: 'Allow',
    Principal: { AWS: 'arn:aws:iam::123456789:role/BackupRole' },
    Action: ['s3:GetObject', 's3:PutObject'],
    Resource: 'arn:aws:s3:::backup-bucket/*'
  }]
};
```

---

## 安全检查清单

### 开发阶段

- [ ] 所有用户输入都经过验证
- [ ] 使用参数化查询
- [ ] 密码使用强哈希存储
- [ ] 敏感数据加密存储
- [ ] 不在日志中记录敏感信息
- [ ] 使用安全的依赖版本

### 部署阶段

- [ ] 启用HTTPS
- [ ] 配置安全响应头
- [ ] 禁用不必要的端口
- [ ] 设置适当的文件权限
- [ ] 配置防火墙规则
- [ ] 启用访问日志

### 运维阶段

- [ ] 定期更新依赖
- [ ] 监控异常访问
- [ ] 定期备份数据
- [ ] 定期轮换密钥
- [ ] 进行安全审计
- [ ] 响应安全事件

---

## 参考资料

- [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CWE/SANS Top 25](https://cwe.mitre.org/top25/)
- [Node.js Security Best Practices](https://nodejs.org/en/docs/guides/security/)
- [Web Security Academy](https://portswigger.net/web-security)

---

> 本文档由 Multi-Agent SDD/TDD Orchestrator 维护 | 最后更新: 2026-04-17
