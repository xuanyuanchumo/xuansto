---
name: anquan_ceshi
description: 进行安全测试，包括漏洞扫描、渗透测试、安全审计。
---
# 安全测试流程

## 测试内容
1. **漏洞扫描**：使用工具扫描已知漏洞
2. **渗透测试**：模拟攻击测试系统安全
3. **安全审计**：审查安全配置和策略
4. **代码审计**：检查代码安全问题

## 测试流程
1. 确定测试范围
2. 信息收集
3. 漏洞发现
4. 漏洞验证
5. 风险评估
6. 报告编写

## 详细测试方法

### 1. 漏洞扫描
- **工具选择**：OWASP ZAP、Nessus、OpenVAS
- **扫描类型**：
  - 静态应用安全测试 (SAST)
  - 动态应用安全测试 (DAST)
  - 交互式应用安全测试 (IAST)
- **扫描频率**：每次代码提交、每日构建、发布前

### 2. 渗透测试
- **测试阶段**：
  - 信息收集：端口扫描、服务识别
  - 漏洞发现：Web漏洞、系统漏洞
  - 漏洞利用：验证漏洞可利用性
  - 后渗透测试：权限提升、横向移动
- **测试范围**：
  - Web应用安全 (OWASP Top 10)
  - API安全测试
  - 认证授权测试
  - 会话管理测试

### 3. 安全审计
- **配置审计**：
  - 服务器安全配置
  - 数据库安全配置
  - 网络安全配置
- **权限审计**：
  - 用户权限检查
  - 角色权限检查
  - 敏感数据访问权限
- **日志审计**：
  - 访问日志分析
  - 异常行为检测
  - 安全事件追踪

### 4. 代码安全审计
- **常见漏洞检查**：
  - SQL注入
  - XSS跨站脚本
  - CSRF跨站请求伪造
  - 命令注入
  - 敏感数据泄露
  - 不安全的反序列化
- **安全编码规范**：
  - 输入验证
  - 输出编码
  - 参数化查询
  - 安全的密码存储

## 风险等级定义

| 等级 | 描述 | 处理优先级 |
|------|------|------------|
| 严重 | 可导致系统完全被控制 | 立即修复 |
| 高危 | 可导致敏感数据泄露 | 24小时内修复 |
| 中危 | 可导致部分功能受损 | 一周内修复 |
| 低危 | 轻微安全问题 | 下个版本修复 |

## 输出物
- 安全测试报告
- 漏洞列表（含风险等级）
- 修复建议
- 复测报告

---

# OWASP Top 10 检测指南

## A01:2021 - 访问控制失效 (Broken Access Control)

### 检测方法

#### 1. 越权访问测试
```bash
# 水平越权测试
# 尝试访问其他用户的资源
GET /api/users/{user_id}/profile
# 修改 user_id 为其他用户ID

# 垂直越权测试
# 普通用户尝试访问管理员功能
GET /admin/users
GET /api/admin/settings
```

## 2. IDOR (不安全的直接对象引用) 测试
```bash
# 测试可预测的资源ID
GET /api/documents/1
GET /api/documents/2
GET /api/documents/3
# 观察是否可以访问不属于自己的资源
```

## 3. 元数据操作测试
```bash
# 修改请求中的权限参数
POST /api/users/update
{
  "user_id": "123",
  "role": "admin"  # 尝试提升权限
}
```

## 4. 目录遍历测试
```bash
# 测试路径遍历
GET /api/files?path=../../../etc/passwd
GET /api/download?file=....//....//etc/passwd
```

## 检测工具
- **Burp Suite**: 使用 Intruder 进行自动化越权测试
- **OWASP ZAP**: 访问控制扫描插件
- **Autorize (Burp插件)**: 自动检测越权漏洞

### 代码检测模式
```python
# 危险模式：仅有登录检查，无权限验证
@login_required
def get_user_data(user_id):
    return User.query.get(user_id)

# 安全模式：验证用户权限
@login_required
def get_user_data(user_id):
    if current_user.id != user_id and not current_user.is_admin:
        abort(403)
    return User.query.get(user_id)
```

---

## A02:2021 - 加密失败 (Cryptographic Failures)

### 检测方法

#### 1. 传输层加密检测
```bash
# 检查 SSL/TLS 配置
nmap --script ssl-enum-ciphers -p 443 target.com

# 检查证书有效性
openssl s_client -connect target.com:443

# 检查是否支持弱协议
openssl s_client -connect target.com:443 -tls1
openssl s_client -connect target.com:443 -tls1_1
```

## 2. 敏感数据存储检测
```bash
# 检查数据库中的密码存储方式
# 查看是否使用明文或弱哈希

# 检查日志中是否记录敏感信息
grep -r "password" /var/log/
grep -r "token" /var/log/

# 检查配置文件中的敏感信息
grep -r "secret" config/
grep -r "api_key" config/
```

## 3. 加密算法检测
```python
# 危险模式
import hashlib
hashlib.md5(password.encode()).hexdigest()  # 不安全
hashlib.sha1(password.encode()).hexdigest()  # 不安全

from Crypto.Cipher import DES  # 不安全

# 安全模式
import hashlib
hashlib.sha256(password.encode()).hexdigest()

import bcrypt
bcrypt.hashpw(password.encode(), bcrypt.gensalt())
```

## 检测工具
- **testssl.sh**: SSL/TLS 配置检测
- **SSL Labs**: 在线 SSL 配置分析
- **hashcat**: 密码哈希强度测试

---

## A03:2021 - 注入攻击 (Injection)

### 检测方法

#### 1. SQL 注入检测
```bash
# 基于错误的注入测试
' OR 1=1--
' OR '1'='1
1 OR 1=1

# 时间盲注测试
' AND SLEEP(5)--
' AND (SELECT * FROM (SELECT(SLEEP(5)))a)--

# UNION 注入测试
' UNION SELECT NULL--
' UNION SELECT NULL,NULL--
' UNION SELECT username,password FROM users--
```

## 2. 命令注入检测
```bash
# Unix/Linux 命令注入
; ls -la
| cat /etc/passwd
`whoami`
$(id)

# Windows 命令注入
& dir
| type C:\Windows\win.ini
```

## 3. LDAP 注入检测
```bash
# LDAP 注入测试
*)(uid=*))(|(uid=*
)(cn=))|(cn=
```

## 4. NoSQL 注入检测
```javascript
// MongoDB 注入
{ "$ne": "" }
{ "$gt": "" }
{ "$where": "this.password == this.confirmPassword" }
```

### 检测工具
- **sqlmap**: 自动化 SQL 注入检测
- **Burp Suite**: 手动和自动化注入测试
- **Commix**: 命令注入检测工具

### 代码检测模式
```python
# 危险模式：字符串拼接
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
cursor.execute("SELECT * FROM users WHERE id = " + user_id)

# 安全模式：参数化查询
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))

# ORM 安全使用
User.objects.filter(id=user_id)  # Django ORM 安全
```

---

## A04:2021 - 不安全设计 (Insecure Design)

### 检测方法

#### 1. 业务逻辑漏洞检测
```bash
# 支付流程测试
# 尝试修改金额、数量、折扣参数
POST /api/checkout
{
  "items": [{"id": 1, "price": -100}],  # 负数价格
  "quantity": -1,  # 负数数量
  "discount": 999  # 异常折扣
}

# 工作流绕过测试
# 跳过必要的审批步骤
POST /api/order/complete  # 直接完成，跳过支付
```

## 2. 速率限制检测
```bash
# 测试是否有速率限制
for i in {1..100}; do
  curl -X POST https://api.target.com/login \
    -d "username=admin&password=test$i"
done

# 测试验证码绕过
# 重放验证码请求
```

## 3. 会话管理测试
```bash
# 测试会话固定攻击
# 登录前后 Session ID 是否变化

# 测试会话超时
# 长时间不活动后会话是否失效
```

## 检测工具
- **Burp Suite**: 业务逻辑测试
- **OWASP ZAP**: 自动化扫描
- **自定义脚本**: 针对性业务逻辑测试

---

## A05:2021 - 安全配置错误 (Security Misconfiguration)

### 检测方法

#### 1. 默认配置检测
```bash
# 检查默认账户
admin:admin
admin:password
root:root

# 检查默认页面
/admin/
/phpmyadmin/
/manager/html
/.git/config
/.env
```

## 2. 目录枚举
```bash
# 使用 dirb 枚举目录
dirb https://target.com /usr/share/wordlists/dirb/common.txt

# 使用 gobuster
gobuster dir -u https://target.com -w common.txt
```

## 3. 错误信息泄露
```bash
# 触发错误查看详细堆栈信息
?id=1'
?id[]=1
?id[0]=1&id[1]=2
```

## 4. HTTP 安全头检测
```bash
# 检查安全响应头
curl -I https://target.com

# 应包含以下头
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
Content-Security-Policy: default-src 'self'
Strict-Transport-Security: max-age=31536000
```

## 检测工具
- **Nikto**: Web 服务器配置扫描
- **Wapiti**: Web 应用漏洞扫描
- **SecurityHeaders.com**: HTTP 安全头检测

---

## A06:2021 - 脆弱和过时的组件 (Vulnerable Components)

### 检测方法

#### 1. 依赖版本检测
```bash
# Python 依赖检查
pip list --outdated
safety check -r requirements.txt

# Node.js 依赖检查
npm audit
npm outdated
yarn audit

# Java 依赖检查
mvn dependency:check
gradle dependencyCheckAnalyze
```

## 2. 已知漏洞数据库查询
```bash
# 使用 CVE 数据库
# https://cve.mitre.org/
# https://nvd.nist.gov/

# 使用 Snyk 漏洞数据库
# https://snyk.io/vuln/
```

## 3. 组件指纹识别
```bash
# 识别 Web 框架版本
whatweb https://target.com

# 识别 CMS 版本
wpscan --url https://target.com  # WordPress
joomscan -u https://target.com   # Joomla
```

## 检测工具
- **OWASP Dependency-Check**: 依赖漏洞扫描
- **Snyk**: 开源漏洞检测
- **Retire.js**: JavaScript 库漏洞检测
- **Trivy**: 容器镜像漏洞扫描

---

## A07:2021 - 身份识别和身份验证失败 (Identification and Authentication Failures)

### 检测方法

#### 1. 弱密码检测
```bash
# 暴力破解测试
hydra -l admin -P /usr/share/wordlists/rockyou.txt target.com http-post-form "/login:username=^USER^&password=^PASS^:Invalid"

# 使用 Burp Suite Intruder
# 配置常见用户名和密码字典
```

## 2. 密码策略测试
```bash
# 测试密码复杂度要求
# 尝试设置弱密码
123456
password
qwerty

# 测试密码长度限制
# 尝试超长密码导致缓冲区溢出
```

## 3. 多因素认证测试
```bash
# 测试 MFA 绕过
# 直接访问受保护资源
GET /api/profile

# 重放 MFA 令牌
# 使用过期的 MFA 代码
```

## 4. 会话管理测试
```bash
# 测试会令牌强度
# 分析 Session ID 的随机性

# 测试会话固定
# 登录后 Session ID 是否更新
```

## 检测工具
- **Hydra**: 暴力破解工具
- **Medusa**: 并行暴力破解
- **Hashcat**: 密码哈希破解

---

## A08:2021 - 软件和数据完整性失败 (Software and Data Integrity Failures)

### 检测方法

#### 1. 不安全的反序列化检测
```python
# Python pickle 反序列化测试
import pickle
import base64

# 构造恶意 payload
class Exploit:
    def __reduce__(self):
        import os
        return (os.system, ('id',))

payload = base64.b64encode(pickle.dumps(Exploit()))
# 发送 payload 到目标应用
```

## 2. CI/CD 管道安全检测
```bash
# 检查 CI/CD 配置文件
# .gitlab-ci.yml
# .github/workflows/
# Jenkinsfile

# 检查是否有未授权的代码执行
# 检查是否有敏感信息泄露
```

## 3. 第三方资源完整性检测
```html
<!-- 检查 CDN 资源是否有 SRI -->
<!-- 不安全 -->
<script src="https://cdn.example.com/jquery.js"></script>

<!-- 安全 -->
<script src="https://cdn.example.com/jquery.js"
        integrity="sha384-..."
        crossorigin="anonymous"></script>
```

### 检测工具
- **ysoserial**: Java 反序列化漏洞利用
- **pickle-tools**: Python pickle 分析
- **Gitness**: CI/CD 安全检测

---

## A09:2021 - 安全日志和监控失败 (Security Logging and Monitoring Failures)

### 检测方法

#### 1. 日志记录检测
```bash
# 检查是否记录关键事件
# - 登录成功/失败
# - 权限变更
# - 敏感操作
# - 错误和异常

# 检查日志存储位置
/var/log/
/var/log/nginx/
/var/log/apache2/
```

## 2. 日志内容检测
```bash
# 检查日志是否包含敏感信息
grep -r "password" /var/log/
grep -r "token" /var/log/
grep -r "credit_card" /var/log/

# 检查日志格式是否统一
# 是否包含时间戳、用户ID、IP地址等
```

## 3. 监控告警检测
```bash
# 检查是否有实时监控
# 检查是否有异常告警机制
# 检查告警响应流程
```

## 检测工具
- **ELK Stack**: 日志分析平台
- **Splunk**: 安全信息和事件管理
- **Graylog**: 日志管理

---

## A10:2021 - 服务器端请求伪造 (SSRF)

### 检测方法

#### 1. 基本 SSRF 测试
```bash
# 测试 URL 参数
GET /api/fetch?url=http://localhost
GET /api/fetch?url=http://127.0.0.1
GET /api/fetch?url=http://[::1]

# 访问内部服务
GET /api/fetch?url=http://localhost:22
GET /api/fetch?url=http://localhost:3306
GET /api/fetch?url=http://169.254.169.254/latest/meta-data/
```

## 2. 绕过技术
```bash
# DNS 绑定绕过
# 使用指向 127.0.0.1 的域名

# URL 编码绕过
http://%31%32%37%2e%30%2e%30%2e%31

# 重定向绕过
# 使用 HTTP 重定向到内部地址

# IPv6 绕过
http://[0:0:0:0:0:ffff:127.0.0.1]
```

## 3. 云环境 SSRF
```bash
# AWS 元数据
http://169.254.169.254/latest/meta-data/
http://169.254.169.254/latest/user-data/

# GCP 元数据
http://metadata.google.internal/computeMetadata/v1/

# Azure 元数据
http://169.254.169.254/metadata/instance
```

## 检测工具
- **SSRFmap**: SSRF 漏洞利用工具
- **Gopherus**: SSRF 利用 payload 生成
- **Burp Suite**: 手动 SSRF 测试

---

# 安全扫描脚本使用说明

## skillscripts/test/security_scanner.py 概述

`skillscripts/test/skillscripts/test/security_scanner.py` 是三省六部项目的安全扫描脚本，用于自动化检测代码中的安全漏洞。

### 功能特性

- **OWASP Top 10 检测**: 覆盖所有 OWASP Top 10 类别
- **代码安全扫描**: SQL注入、XSS、CSRF等漏洞检测
- **敏感信息检测**: 硬编码密码、API密钥、私钥等
- **依赖安全检查**: 已知漏洞依赖检测
- **配置安全检查**: 安全配置错误检测

## 命令行参数

### 基本用法

```bash
# 基本扫描
python skillscripts/test/skillscripts/test/security_scanner.py

# 严格模式（任何警告都视为失败）
python skillscripts/test/skillscripts/test/security_scanner.py --strict

# 详细输出模式
python skillscripts/test/skillscripts/test/security_scanner.py --verbose

# JSON 格式输出
python skillscripts/test/skillscripts/test/security_scanner.py --output json

# 保存 JSON 到文件
python skillscripts/test/skillscripts/test/security_scanner.py --output json --output-file result.json
```

## 参数详解

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--strict` | 严格模式，任何警告都视为失败 | False |
| `--output` | 输出格式：console 或 json | console |
| `--output-file` | 输出文件路径（JSON格式时使用） | 无 |
| `--verbose` | 启用详细日志输出 | False |

## 检查项目

### 1. SQL 注入检测 (`check_sql_injection`)
检测以下危险模式：
- f-string SQL 查询
- 字符串格式化 SQL 查询
- 字符串拼接 SQL 查询
- Django extra where 子句
- SQLAlchemy f-string

### 2. XSS 漏洞检测 (`check_xss_vulnerabilities`)
检测以下危险模式：
- innerHTML 赋值
- document.write 调用
- React dangerouslySetInnerHTML
- jQuery .html() 非变量
- Vue v-html 指令
- Angular innerHTML 绑定

### 3. CSRF 漏洞检测 (`check_csrf_vulnerabilities`)
检测以下危险模式：
- Django CSRF 豁免装饰器
- CSRF 保护禁用
- Flask POST 路由无 CSRF

### 4. 敏感数据泄露检测 (`check_sensitive_data_exposure`)
检测以下危险模式：
- 日志记录密码
- 日志记录令牌
- 日志记录密钥

### 5. 硬编码密钥检测 (`check_hardcoded_secrets`)
检测以下敏感信息：
- 硬编码密码
- 硬编码 API Key
- 硬编码密钥
- 硬编码访问令牌
- 硬编码私钥
- 硬编码 AWS 凭证
- 硬编码数据库连接
- PEM 格式私钥
- Bearer 令牌
- Basic 认证凭证

### 6. 访问控制检测 (`check_access_control`)
检测以下问题：
- 仅有登录检查，无权限验证
- Django REST framework 允许任何用户
- 仅检查认证，无权限验证
- 空权限类列表

### 7. 加密失败检测 (`check_cryptographic_failures`)
检测以下问题：
- MD5 哈希（不安全）
- SHA1 哈希（不安全）
- DES 加密（不安全）
- 不安全的随机数生成
- 过时的 TLS 协议

### 8. SSRF 漏洞检测 (`check_ssrf_vulnerabilities`)
检测以下危险模式：
- URL 拼接请求
- f-string URL 请求

### 9. 身份验证失败检测 (`check_auth_failures`)
检测以下问题：
- 明文密码比较
- 弱密码验证
- 硬编码密码检查
- 不安全的会话设置
- 硬编码 JWT 密钥

### 10. 日志问题检测 (`check_logging_issues`)
检测以下问题：
- 静默异常处理
- 缺少日志记录机制

### 11. 依赖漏洞检测 (`check_dependency_vulnerabilities`)
检测以下内容：
- Python 依赖已知漏洞
- JavaScript 依赖已知漏洞

### 12. 安全配置错误检测 (`check_security_misconfiguration`)
检测以下问题：
- DEBUG 模式启用
- SECRET_KEY 硬编码
- ALLOWED_HOSTS 配置不安全
- 容器以特权模式运行

## 输出格式

### 控制台输出

```
================================================================================
安全扫描报告
================================================================================
项目根目录: /path/to/project
扫描时间: 2024-01-15T10:30:00
总体状态: ❌ 未通过

--------------------------------------------------------------------------------
摘要
--------------------------------------------------------------------------------
  total_checks: 12
  passed_checks: 8
  failed_checks: 2
  warning_checks: 2
  total_issues: 5
  critical_issues: 1
  high_issues: 2
  medium_issues: 2
  files_scanned: 50

--------------------------------------------------------------------------------
OWASP Top 10 摘要
--------------------------------------------------------------------------------
  A03:2021 - 注入攻击: 2 个问题
  A02:2021 - 加密失败: 1 个问题
  A01:2021 - 访问控制失效: 2 个问题

--------------------------------------------------------------------------------
检查: sql_injection
--------------------------------------------------------------------------------
状态: ❌ fail

发现 2 个安全问题:

  🟠 [HIGH] sql_injection
     文件: backend/api/views.py
     行号: 45
     描述: 潜在 SQL 注入风险: f-string SQL 查询
     OWASP: A03:2021 - 注入攻击
     CWE: CWE-89
     建议: 使用参数化查询或 ORM，避免直接拼接 SQL 字符串
```

### JSON 输出格式

```json
{
  "timestamp": "2024-01-15T10:30:00",
  "project_root": "/path/to/project",
  "overall_passed": false,
  "summary": {
    "total_checks": 12,
    "passed_checks": 8,
    "failed_checks": 2,
    "warning_checks": 2,
    "total_issues": 5,
    "critical_issues": 1,
    "high_issues": 2,
    "medium_issues": 2,
    "files_scanned": 50
  },
  "owasp_summary": {
    "A01:2021 - 访问控制失效": {
      "count": 2,
      "severity_breakdown": {
        "critical": 0,
        "high": 1,
        "medium": 1,
        "low": 0
      }
    }
  },
  "results": [
    {
      "check_name": "sql_injection",
      "status": "fail",
      "issues": [
        {
          "file_path": "backend/api/views.py",
          "issue_type": "sql_injection",
          "description": "潜在 SQL 注入风险: f-string SQL 查询",
          "severity": "high",
          "owasp_category": "A03:2021 - 注入攻击",
          "line_number": 45,
          "code_snippet": "...",
          "suggestion": "使用参数化查询或 ORM，避免直接拼接 SQL 字符串",
          "cwe_id": "CWE-89"
        }
      ],
      "details": {
        "files_scanned": 25,
        "owasp": "A03:2021 - 注入攻击"
      }
    }
  ]
}
```

## 报告存储

扫描报告自动保存到 `reports/` 目录：
- `security_scan_YYYYMMDD_HHMMSS.json` - 带时间戳的报告
- `security_scan_latest.json` - 最新报告

---

# 安全修复策略

## 修复优先级矩阵

| 严重程度 | 影响范围 | 利用难度 | 修复时限 |
|----------|----------|----------|----------|
| Critical | 系统完全被控制 | 容易 | 立即修复 |
| High | 敏感数据泄露 | 中等 | 24小时内 |
| Medium | 部分功能受损 | 较难 | 一周内 |
| Low | 轻微安全问题 | 困难 | 下版本 |

## 常见安全问题修复方法

### 1. SQL 注入修复

#### 问题代码
```python
# 危险：字符串拼接
query = f"SELECT * FROM users WHERE id = {user_id}"
cursor.execute(query)

# 危险：字符串格式化
query = "SELECT * FROM users WHERE name = '%s'" % name
cursor.execute(query)
```

## 修复方案
```python
# 方案1：参数化查询
query = "SELECT * FROM users WHERE id = %s"
cursor.execute(query, (user_id,))

# 方案2：使用 ORM
user = User.query.filter_by(id=user_id).first()  # SQLAlchemy
user = User.objects.get(id=user_id)  # Django ORM

# 方案3：存储过程
cursor.callproc('get_user_by_id', (user_id,))
```

## 2. XSS 修复

#### 问题代码
```javascript
// 危险：直接插入 HTML
element.innerHTML = userInput;

// 危险：React dangerouslySetInnerHTML
<div dangerouslySetInnerHTML={{__html: userInput}} />

// 危险：Vue v-html
<div v-html="userInput"></div>
```

#### 修复方案
```javascript
// 方案1：使用 textContent
element.textContent = userInput;

// 方案2：React 默认转义
<div>{userInput}</div>

// 方案3：Vue 默认转义
<div>{{ userInput }}</div>

// 方案4：使用 DOMPurify 库
import DOMPurify from 'dompurify';
element.innerHTML = DOMPurify.sanitize(userInput);
```

### 3. CSRF 修复

#### 问题代码
```python
# Django 危险配置
@csrf_exempt
def update_profile(request):
    ...

# Flask 危险配置
@app.route('/update', methods=['POST'])
def update():
    ...
```

## 修复方案
```python
# Django：启用 CSRF 保护
from django.views.decorators.csrf import csrf_protect

@csrf_protect
def update_profile(request):
    ...

# Flask：使用 Flask-WTF
from flask_wtf.csrf import CSRFProtect
csrf = CSRFProtect(app)

# 前端：包含 CSRF Token
fetch('/api/update', {
    method: 'POST',
    headers: {
        'X-CSRFToken': getCookie('csrftoken')
    },
    body: JSON.stringify(data)
});
```

## 4. 硬编码密钥修复

#### 问题代码
```python
# 危险：硬编码密钥
SECRET_KEY = 'django-insecure-123456'
API_KEY = 'sk-1234567890abcdef'
DATABASE_PASSWORD = 'password123'
```

## 修复方案
```python
# 方案1：环境变量
import os
SECRET_KEY = os.environ.get('SECRET_KEY')
API_KEY = os.environ.get('API_KEY')

# 方案2：配置文件（不提交到版本控制）
from config import SECRET_KEY, API_KEY

# 方案3：密钥管理服务
import boto3
client = boto3.client('secretsmanager')
secret = client.get_secret_value(SecretId='my-secret')
```

## 5. 访问控制修复

#### 问题代码
```python
# 危险：仅有登录检查
@login_required
def delete_user(request, user_id):
    User.objects.get(id=user_id).delete()
```

## 修复方案
```python
# 方案1：检查资源所有权
@login_required
def delete_user(request, user_id):
    user = User.objects.get(id=user_id)
    if request.user != user and not request.user.is_admin:
        return HttpResponseForbidden()
    user.delete()

# 方案2：使用权限装饰器
from django.contrib.auth.decorators import permission_required

@permission_required('app.delete_user')
def delete_user(request, user_id):
    User.objects.get(id=user_id).delete()

# 方案3：Django REST Framework 权限类
from rest_framework import permissions

class IsOwnerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user or request.user.is_admin
```

## 6. 加密失败修复

#### 问题代码
```python
# 危险：弱哈希算法
import hashlib
password_hash = hashlib.md5(password.encode()).hexdigest()

# 危险：不安全的随机数
import random
token = random.randint(100000, 999999)
```

## 修复方案
```python
# 方案1：使用 bcrypt
import bcrypt
password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

# 方案2：使用 Argon2
from argon2 import PasswordHasher
ph = PasswordHasher()
password_hash = ph.hash(password)

# 方案3：安全的随机数
import secrets
token = secrets.token_hex(32)
token = secrets.randbelow(1000000)
```

## 7. SSRF 修复

#### 问题代码
```python
# 危险：用户可控的 URL
url = request.GET.get('url')
response = requests.get(url)
```

## 修复方案
```python
# 方案1：URL 白名单
ALLOWED_DOMAINS = ['api.example.com', 'cdn.example.com']

def is_allowed_url(url):
    from urllib.parse import urlparse
    domain = urlparse(url).netloc
    return domain in ALLOWED_DOMAINS

url = request.GET.get('url')
if not is_allowed_url(url):
    return HttpResponseBadRequest('Invalid URL')

# 方案2：禁止内部 IP
import ipaddress
import socket

def is_internal_ip(url):
    from urllib.parse import urlparse
    domain = urlparse(url).netloc.split(':')[0]
    ip = socket.gethostbyname(domain)
    return ipaddress.ip_address(ip).is_private

# 方案3：使用代理服务
# 通过专门的代理服务请求外部资源
```

## 8. 身份验证修复

#### 问题代码
```python
# 危险：明文密码比较
if user.password == password:
    login(user)

# 危险：弱密码策略
# 无密码复杂度要求
```

## 修复方案
```python
# 方案1：使用密码哈希验证
from django.contrib.auth import authenticate
user = authenticate(username=username, password=password)

# 方案2：强密码策略
import re

def validate_password(password):
    if len(password) < 12:
        return False, "密码长度至少12位"
    if not re.search(r'[A-Z]', password):
        return False, "密码必须包含大写字母"
    if not re.search(r'[a-z]', password):
        return False, "密码必须包含小写字母"
    if not re.search(r'\d', password):
        return False, "密码必须包含数字"
    if not re.search(r'[!@#$%^&*]', password):
        return False, "密码必须包含特殊字符"
    return True, "密码强度符合要求"

# 方案3：多因素认证
# 使用 pyotp 实现 TOTP
import pyotp
totp = pyotp.TOTP(user.totp_secret)
if totp.verify(code):
    # 验证成功
```

## 9. 安全配置修复

#### 问题代码
```python
# settings.py 危险配置
DEBUG = True
SECRET_KEY = 'hardcoded-secret-key'
ALLOWED_HOSTS = []
```

## 修复方案
```python
# settings.py 安全配置
import os
from pathlib import Path

DEBUG = os.environ.get('DEBUG', 'False') == 'True'
SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError('SECRET_KEY environment variable not set')

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')
if not ALLOWED_HOSTS or ALLOWED_HOSTS == ['']:
    ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# 安全响应头
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

## 10. 日志安全修复

#### 问题代码
```python
# 危险：记录敏感信息
logger.info(f"User login: {username}, password: {password}")

# 危险：静默异常
try:
    process_data()
except:
    pass
```

## 修复方案
```python
# 方案1：脱敏处理
def sanitize_for_log(data):
    sensitive_fields = ['password', 'token', 'secret', 'key']
    for field in sensitive_fields:
        if field in data:
            data[field] = '***'
    return data

logger.info(f"User login: {username}")

# 方案2：记录异常信息
import logging
logger = logging.getLogger(__name__)

try:
    process_data()
except Exception as e:
    logger.error(f"Error processing data: {e}", exc_info=True)
    raise

# 方案3：结构化日志
import structlog
logger = structlog.get_logger()

logger.info("user_login", user_id=user.id, ip=request.META['REMOTE_ADDR'])
```

---

# 安全测试最佳实践

## 安全测试流程

### 1. 测试准备阶段

#### 确定测试范围
```markdown
- 测试目标系统
- 测试功能模块
- 测试接口列表
- 测试数据范围
- 禁止测试的项目
```

#### 获取授权
```markdown
- 书面授权文件
- 测试时间窗口
- 紧急联系人
- 测试IP白名单
```

#### 环境准备
```markdown
- 测试环境搭建
- 测试工具配置
- 测试账号准备
- 测试数据准备
```

### 2. 信息收集阶段

#### 被动信息收集
```bash
# WHOIS 查询
whois target.com

# DNS 枚举
dnsenum target.com
dnsrecon -d target.com

# 搜索引擎信息
# Google Dorks
site:target.com filetype:pdf
site:target.com inurl:admin

# 证书透明度日志
# https://crt.sh/
# https://censys.io/
```

## 主动信息收集
```bash
# 端口扫描
nmap -sV -sC target.com
nmap -p- target.com

# 服务识别
nmap -sV --script=banner target.com

# Web 应用指纹
whatweb https://target.com
wappalyzer -u https://target.com

# 目录枚举
gobuster dir -u https://target.com -w /usr/share/wordlists/dirb/common.txt
```

## 3. 漏洞发现阶段

#### 自动化扫描
```bash
# 运行安全扫描脚本
python skillscripts/test/skillscripts/test/security_scanner.py --verbose

# 运行 OWASP ZAP 扫描
zap-cli quick-scan https://target.com

# 运行 Nikto 扫描
nikto -h https://target.com

# 运行 Nuclei 扫描
nuclei -u https://target.com -t /path/to/templates
```

## 手动测试
```markdown
1. 认证测试
   - 登录功能测试
   - 密码重置测试
   - 会话管理测试
   - 多因素认证测试

2. 授权测试
   - 水平越权测试
   - 垂直越权测试
   - IDOR 测试

3. 输入验证测试
   - SQL 注入测试
   - XSS 测试
   - 命令注入测试
   - 路径遍历测试

4. 业务逻辑测试
   - 支付流程测试
   - 权限变更测试
   - 数据篡改测试
```

### 4. 漏洞验证阶段

#### 漏洞复现
```markdown
1. 记录漏洞触发步骤
2. 保存漏洞证明材料
   - 截图
   - 请求/响应数据
   - 日志记录
3. 评估漏洞影响
   - 数据泄露范围
   - 系统控制程度
   - 业务影响
```

#### 漏洞利用（仅限授权测试）
```markdown
1. 验证漏洞可利用性
2. 评估利用难度
3. 记录利用过程
4. 清理测试痕迹
```

### 5. 风险评估阶段

#### 风险计算
```
风险 = 影响 × 可能性

影响评估：
- Critical: 系统完全被控制，敏感数据大规模泄露
- High: 敏感数据泄露，重要功能受损
- Medium: 部分数据泄露，部分功能受损
- Low: 轻微信息泄露，影响有限

可能性评估：
- High: 无需认证，容易发现和利用
- Medium: 需要认证，需要一定技能
- Low: 需要特殊条件，利用困难
```

### 6. 报告编写阶段

## 安全测试报告格式

### 报告结构

```markdown
# 安全测试报告

## 1. 执行摘要
### 1.1 测试概述
- 测试时间：YYYY-MM-DD 至 YYYY-MM-DD
- 测试范围：[系统名称/模块]
- 测试方法：[黑盒/白盒/灰盒]

### 1.2 主要发现
- 发现漏洞总数：XX 个
- 严重漏洞：XX 个
- 高危漏洞：XX 个
- 中危漏洞：XX 个
- 低危漏洞：XX 个

### 1.3 风险评估
- 整体风险等级：[Critical/High/Medium/Low]
- 主要风险点：[描述]

## 2. 测试范围
### 2.1 测试目标
- 目标系统：[系统名称]
- 目标地址：[URL/IP]
- 测试账号：[账号类型]

### 2.2 测试限制
- 禁止测试项目
- 测试时间限制
- 其他限制条件

## 3. 测试方法
### 3.1 测试工具
| 工具名称 | 版本 | 用途 |
|---------|------|------|
| skillscripts/test/security_scanner.py | 1.0 | 代码安全扫描 |
| OWASP ZAP | 2.12 | Web漏洞扫描 |
| Burp Suite | 2023.1 | 渗透测试 |

### 3.2 测试类型
- 静态代码分析
- 动态应用测试
- 渗透测试
- 配置审计

## 4. 漏洞详情
### 4.1 严重漏洞

#### 漏洞 #1: [漏洞名称]
**基本信息**
- 漏洞类型：[SQL注入/XSS/...]
- 风险等级：Critical
- OWASP分类：A03:2021 - 注入攻击
- CWE编号：CWE-89

**漏洞描述**
[详细描述漏洞原理和影响]

**漏洞位置**
- 文件：[文件路径]
- 行号：[行号]
- URL：[接口地址]

**复现步骤**
1. 步骤一
2. 步骤二
3. 步骤三

**漏洞证明**
[截图或代码片段]

**修复建议**
[详细的修复方案和代码示例]

**参考资料**
- CWE-89: https://cwe.mitre.org/data/definitions/89.html
- OWASP SQL Injection: https://owasp.org/www-community/attacks/SQL_Injection

### 4.2 高危漏洞
[同上格式]

### 4.3 中危漏洞
[同上格式]

### 4.4 低危漏洞
[同上格式]

## 5. 安全建议
### 5.1 紧急修复项
1. [建议1]
2. [建议2]

### 5.2 短期改进项
1. [建议1]
2. [建议2]

### 5.3 长期改进项
1. [建议1]
2. [建议2]

## 6. 附录
### 6.1 扫描报告
[附上自动化扫描工具的报告]

### 6.2 测试数据
[测试过程中使用的测试数据]

### 6.3 参考资料
[相关安全标准和最佳实践]
```

### 报告示例

```markdown
# 安全测试报告

## 1. 执行摘要

### 1.1 测试概述
- 测试时间：2024-01-15 至 2024-01-17
- 测试范围：三省六部项目后端 API
- 测试方法：白盒测试 + 灰盒测试

### 1.2 主要发现
- 发现漏洞总数：5 个
- 严重漏洞：1 个
- 高危漏洞：2 个
- 中危漏洞：2 个
- 低危漏洞：0 个

### 1.3 风险评估
- 整体风险等级：High
- 主要风险点：存在 SQL 注入漏洞，可能导致数据库被完全控制

## 4. 漏洞详情

### 4.1 严重漏洞

#### 漏洞 #1: SQL 注入漏洞

**基本信息**
- 漏洞类型：SQL 注入
- 风险等级：Critical
- OWASP分类：A03:2021 - 注入攻击
- CWE编号：CWE-89

**漏洞描述**
在用户查询接口中，使用 f-string 直接拼接用户输入到 SQL 查询语句中，
攻击者可以通过构造恶意输入来执行任意 SQL 命令，可能导致：
- 数据库数据泄露
- 数据篡改或删除
- 数据库服务器被控制

**漏洞位置**
- 文件：backend/api/views.py
- 行号：45
- URL：/api/users/search

**复现步骤**
1. 发送 GET 请求：/api/users/search?name=test' OR '1'='1
2. 观察返回结果包含所有用户数据
3. 进一步利用可获取数据库敏感信息

**漏洞证明**
```python
# backend/api/views.py:45
def search_users(request):
    name = request.GET.get('name')
    query = f"SELECT * FROM users WHERE name LIKE '%{name}%'"
    cursor.execute(query)  # SQL 注入点
```

**修复建议**
```python
# 使用参数化查询
def search_users(request):
    name = request.GET.get('name')
    query = "SELECT * FROM users WHERE name LIKE %s"
    cursor.execute(query, (f'%{name}%',))

# 或使用 ORM
def search_users(request):
    name = request.GET.get('name')
    users = User.objects.filter(name__icontains=name)
```
```

## 安全测试检查清单

### 认证测试
- [ ] 弱密码测试
- [ ] 暴力破解测试
- [ ] 密码重置流程测试
- [ ] 会话管理测试
- [ ] 记住我功能测试
- [ ] 多因素认证测试

### 授权测试
- [ ] 水平越权测试
- [ ] 垂直越权测试
- [ ] IDOR 测试
- [ ] 目录遍历测试
- [ ] 功能权限测试

### 输入验证测试
- [ ] SQL 注入测试
- [ ] XSS 测试（反射型、存储型、DOM型）
- [ ] 命令注入测试
- [ ] LDAP 注入测试
- [ ] XML 注入测试
- [ ] 路径遍历测试
- [ ] 文件上传测试

### 业务逻辑测试
- [ ] 支付流程测试
- [ ] 订单流程测试
- [ ] 权限变更测试
- [ ] 数据篡改测试
- [ ] 竞态条件测试

### 配置安全测试
- [ ] 默认账户测试
- [ ] 默认配置测试
- [ ] 敏感信息泄露测试
- [ ] HTTP 安全头测试
- [ ] SSL/TLS 配置测试
- [ ] 错误处理测试

### API 安全测试
- [ ] 认证机制测试
- [ ] 速率限制测试
- [ ] 参数篡改测试
- [ ] 批量请求测试
- [ ] API 版本测试

---

## 最佳实践总结

1. **建立安全测试基线，定期执行**
   - 每次代码提交运行自动化安全扫描
   - 每周进行一次全面安全测试
   - 每季度进行一次渗透测试

2. **将安全测试集成到 CI/CD 流程**
   - 代码提交时运行 SAST
   - 部署前运行 DAST
   - 依赖更新时检查漏洞

3. **保持测试工具和漏洞库更新**
   - 定期更新扫描工具
   - 关注最新漏洞公告
   - 更新漏洞检测规则

4. **培训开发人员安全编码意识**
   - 定期安全培训
   - 安全编码规范
   - 代码审查机制

5. **建立漏洞响应机制**
   - 漏洞报告流程
   - 漏洞修复时限
   - 复测验证流程
