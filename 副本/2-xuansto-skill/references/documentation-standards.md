# 文档规范参考文档
> 版本: 1.9.0 | 更新日期: 2026-04-28 | 编码: UTF-8 | 行尾: LF

## 目录

- [文档类型](#文档类型)
- [格式规范](#格式规范)
- [维护策略](#维护策略)
- [版本控制](#版本控制)
- [自动化工具](#自动化工具)
- [参考资源](#参考资源)

## 文档类型

### 文档分类体系

```
┌─────────────────────────────────────────────────────────────┐
│                      文档分类体系                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                   产品文档                          │   │
│  │   需求文档 │ PRD │ 用户手册 │ FAQ                  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                   技术文档                          │   │
│  │   架构设计 │ API文档 │ 数据库设计 │ 技术方案       │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                   开发文档                          │   │
│  │   代码规范 │ 开发指南 │ 提交规范 │ 分支策略        │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                   运维文档                          │   │
│  │   部署指南 │ 监控配置 │ 故障处理 │ 运维手册        │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                   测试文档                          │   │
│  │   测试计划 │ 测试用例 │ 测试报告 │ 自动化指南      │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 文档类型定义

| 类型 | 文件名 | 目标读者 | 内容要点 |
|------|--------|----------|----------|
| README | README.md | 所有用户 | 项目概述、快速开始 |
| 架构设计 | ARCHITECTURE.md | 技术团队 | 系统架构、技术选型 |
| API文档 | API.md | 开发者 | 接口定义、使用示例 |
| 开发指南 | CONTRIBUTING.md | 贡献者 | 开发规范、提交流程 |
| 变更日志 | CHANGELOG.md | 所有用户 | 版本变更记录 |
| 许可证 | LICENSE | 所有用户 | 使用许可条款 |
| 行为准则 | CODE_OF_CONDUCT.md | 社区成员 | 社区行为规范 |
| 安全政策 | SECURITY.md | 安全研究员 | 安全报告流程 |

### 产品需求文档 (PRD)

```markdown
# 产品需求文档 - 用户认证模块

## 文档信息
| 项目 | 内容 |
|------|------|
| 文档版本 | v1.0.0 |
| 创建日期 | 2024-01-15 |
| 最后更新 | 2024-01-20 |
| 作者 | 产品团队 |
| 状态 | 已评审 |

## 1. 概述

### 1.1 背景
当前系统缺乏统一的用户认证机制，导致用户体验不一致，存在安全隐患。

### 1.2 目标
- 提供安全可靠的用户认证服务
- 支持多种认证方式
- 提升用户体验

### 1.3 范围
- 用户注册/登录
- 密码找回
- 第三方登录
- 会话管理

## 2. 用户故事

### US-001: 用户注册
作为新用户，我希望能够注册账号，以便使用系统功能。

**验收标准：**
- [ ] 支持邮箱注册
- [ ] 支持手机号注册
- [ ] 密码强度验证
- [ ] 邮箱/手机验证

### US-002: 用户登录
作为已注册用户，我希望能够登录系统，以便访问我的账户。

**验收标准：**
- [ ] 支持账号密码登录
- [ ] 支持验证码登录
- [ ] 支持记住登录状态
- [ ] 登录失败提示

## 3. 功能需求

### 3.1 注册功能
| 功能点 | 优先级 | 描述 |
|--------|--------|------|
| 邮箱注册 | P0 | 使用邮箱地址注册 |
| 手机注册 | P0 | 使用手机号注册 |
| 密码设置 | P0 | 设置登录密码 |
| 验证码 | P0 | 邮箱/手机验证码 |

### 3.2 登录功能
| 功能点 | 优先级 | 描述 |
|--------|--------|------|
| 账号登录 | P0 | 账号密码登录 |
| 验证码登录 | P1 | 短信/邮箱验证码登录 |
| 第三方登录 | P1 | 微信/Google登录 |
| 多因素认证 | P2 | MFA支持 |

## 4. 非功能需求

### 4.1 安全性
- 密码加密存储（bcrypt）
- 会话超时机制
- 防暴力破解
- HTTPS传输

### 4.2 性能
- 登录响应时间 < 500ms
- 支持1000并发登录
- 可用性 > 99.9%

## 5. 里程碑

| 阶段 | 日期 | 交付物 |
|------|------|--------|
| 设计 | 2024-01-25 | 设计稿、技术方案 |
| 开发 | 2024-02-15 | 功能代码 |
| 测试 | 2024-02-25 | 测试报告 |
| 上线 | 2024-03-01 | 生产环境部署 |

## 6. 附录

### 6.1 参考资料
- [OAuth 2.0 规范](https://oauth.net/2/)
- [OWASP 认证指南](https://owasp.org/)

### 6.2 术语表
| 术语 | 定义 |
|------|------|
| MFA | 多因素认证 |
| JWT | JSON Web Token |
```

### 技术设计文档

```markdown
# 技术设计文档 - 用户认证服务

## 1. 概述

### 1.1 背景
本文档描述用户认证服务的技术实现方案。

### 1.2 目标
- 高可用认证服务
- 安全的数据存储
- 可扩展的架构设计

## 2. 系统架构

### 2.1 架构图

```
┌─────────────────────────────────────────────────────┐
│                    客户端层                          │
│   Web App │ Mobile App │ Third-party App           │
└─────────────────────┬───────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────┐
│                    API Gateway                       │
│   认证 │ 限流 │ 路由 │ 日志                         │
└─────────────────────┬───────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────┐
│                    认证服务                          │
│   登录 │ 注册 │ Token管理 │ 会话管理               │
└─────────────────────┬───────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────┐
│                    数据层                            │
│   PostgreSQL │ Redis │ Message Queue               │
└─────────────────────────────────────────────────────┘
```

### 2.2 技术选型

| 组件 | 技术选择 | 理由 |
|------|----------|------|
| 后端框架 | NestJS | 模块化、TypeScript支持 |
| 数据库 | PostgreSQL | ACID、扩展性 |
| 缓存 | Redis | 高性能、会话存储 |
| 消息队列 | RabbitMQ | 可靠性、延迟队列 |

## 3. 数据模型

### 3.1 用户表

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_phone ON users(phone);
```

### 3.2 会话表

```sql
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    token_hash VARCHAR(255) NOT NULL,
    device_info JSONB,
    ip_address INET,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_sessions_token_hash ON sessions(token_hash);
```

## 4. API设计

### 4.1 登录接口

```yaml
POST /api/v1/auth/login
Request:
  body:
    email: string (required)
    password: string (required)
    remember_me: boolean (optional)

Response:
  200:
    data:
      access_token: string
      refresh_token: string
      expires_in: number
      user:
        id: string
        email: string
  401:
    error:
      code: INVALID_CREDENTIALS
      message: 邮箱或密码错误
```

### 4.2 注册接口

```yaml
POST /api/v1/auth/register
Request:
  body:
    email: string (required)
    password: string (required)
    verification_code: string (required)

Response:
  201:
    data:
      user:
        id: string
        email: string
      access_token: string
  400:
    error:
      code: VALIDATION_ERROR
      message: 参数验证失败
```

## 5. 安全设计

### 5.1 密码安全
- 使用bcrypt加密，cost factor = 12
- 密码强度要求：至少8位，包含大小写字母和数字
- 密码历史检查，禁止重复使用最近5次密码

### 5.2 Token安全
- JWT有效期：access_token 15分钟，refresh_token 7天
- Token签名算法：RS256
- Token撤销机制：黑名单 + 短有效期

### 5.3 防护措施
- 登录失败次数限制：5次/15分钟
- IP黑名单机制
- 敏感操作二次验证

## 6. 部署方案

### 6.1 容器化

```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY dist ./dist
EXPOSE 3000
CMD ["node", "dist/main.js"]
```

### 6.2 Kubernetes配置

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: auth-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: auth-service
  template:
    spec:
      containers:
        - name: auth-service
          image: auth-service:latest
          ports:
            - containerPort: 3000
          resources:
            requests:
              memory: "256Mi"
              cpu: "250m"
            limits:
              memory: "512Mi"
              cpu: "500m"
```
```

## 格式规范

### Markdown规范

#### 标题层级

```markdown
# 一级标题 - 文档标题
## 二级标题 - 主要章节
### 三级标题 - 子章节
#### 四级标题 - 小节
##### 五级标题 - 细节说明
```

#### 代码块

```markdown
行内代码使用反引号：`const x = 1;`

代码块使用三个反引号并指定语言：

```typescript
const greeting: string = "Hello, World!";
console.log(greeting);
```
```

#### 列表格式

```markdown
无序列表：
- 项目一
- 项目二
  - 子项目一
  - 子项目二

有序列表：
1. 第一步
2. 第二步
   1. 子步骤一
   2. 子步骤二

任务列表：
- [x] 已完成
- [ ] 未完成
```

#### 表格格式

```markdown
| 列1 | 列2 | 列3 |
|-----|-----|-----|
| 内容 | 内容 | 内容 |
| 内容 | 内容 | 内容 |
```

#### 链接和图片

```markdown
[链接文本](https://example.com)

[带标题的链接](https://example.com "链接标题")

![图片替代文本](https://example.com/image.png)

![带标题的图片](https://example.com/image.png "图片标题")
```

### 文档模板

#### README模板

```markdown
# 项目名称

简短的项目描述，说明项目的主要功能和用途。

## 功能特性

- 特性一：描述
- 特性二：描述
- 特性三：描述

## 快速开始

### 环境要求

- Node.js >= 18
- npm >= 9

### 安装

```bash
npm install my-project
```

### 使用

```javascript
import { MyProject } from 'my-project';

const instance = new MyProject();
instance.start();
```

## 文档

详细文档请参阅 [docs](./docs) 目录。

## 贡献指南

请参阅 [CONTRIBUTING.md](./CONTRIBUTING.md)。

## 许可证

[MIT](./LICENSE)
```

#### CHANGELOG模板

```markdown
# 变更日志

本项目的所有重要变更都将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/)，
版本号遵循 [语义化版本](https://semver.org/)。

## [Unreleased]

### 新增
- 待发布的新功能

### 变更
- 待发布的变更

### 修复
- 待发布的修复

## [1.2.0] - 2024-01-15

### 新增
- 添加用户认证模块
- 支持第三方登录

### 变更
- 优化数据库查询性能
- 更新API响应格式

### 修复
- 修复登录超时问题 (#123)
- 修复文件上传漏洞

### 安全
- 升级依赖包修复安全漏洞

## [1.1.0] - 2024-01-01

### 新增
- 初始版本发布
```

## 维护策略

### 文档生命周期

```
┌─────────────────────────────────────────────────────────────┐
│                      文档生命周期                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐ │
│  │  创建   │───>│  评审   │───>│  发布   │───>│  维护   │ │
│  └─────────┘    └─────────┘    └─────────┘    └────┬────┘ │
│                                                     │       │
│                                                     ▼       │
│                                               ┌─────────┐  │
│                                               │  归档   │  │
│                                               └─────────┘  │
│                                                             │
│  状态说明：                                                 │
│  - 草稿 (Draft)：正在编写中                                 │
│  - 评审 (Review)：等待评审                                  │
│  - 发布 (Published)：正式发布                               │
│  - 维护 (Maintenance)：持续更新                             │
│  - 归档 (Archived)：不再维护                                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 更新频率

| 文档类型 | 更新频率 | 责任人 |
|----------|----------|--------|
| README | 版本发布时 | 项目负责人 |
| API文档 | 接口变更时 | 后端开发 |
| 架构文档 | 架构调整时 | 架构师 |
| 运维文档 | 部署变更时 | 运维团队 |
| 用户手册 | 功能变更时 | 产品团队 |

### 文档审查

```yaml
文档审查清单:
  内容完整性:
    - 标题和描述清晰
    - 内容完整无遗漏
    - 示例代码可运行
    - 链接有效可访问

  格式规范性:
    - Markdown格式正确
    - 标题层级合理
    - 代码块指定语言
    - 表格格式整齐

  技术准确性:
    - 技术描述准确
    - 代码示例正确
    - 版本信息最新
    - 配置参数有效

  可读性:
    - 语言简洁明了
    - 结构清晰有序
    - 图表辅助说明
    - 术语使用一致
```

## 版本控制

### 文档版本号

遵循语义化版本规范：`MAJOR.MINOR.PATCH`

- **MAJOR**：重大变更，内容结构重组
- **MINOR**：新增内容，功能扩展
- **PATCH**：错误修正，小幅更新

### 版本记录

```markdown
## 版本历史

| 版本 | 日期 | 作者 | 变更说明 |
|------|------|------|----------|
| v2.0.0 | 2024-01-15 | 张三 | 重构文档结构 |
| v1.1.0 | 2024-01-10 | 李四 | 新增API文档 |
| v1.0.1 | 2024-01-05 | 王五 | 修复链接错误 |
| v1.0.0 | 2024-01-01 | 张三 | 初始版本 |
```

### Git管理

```bash
docs/
├── README.md
├── CHANGELOG.md
├── architecture/
│   ├── system-design.md
│   └── database-design.md
├── api/
│   ├── rest-api.md
│   └── graphql-api.md
├── guides/
│   ├── development.md
│   └── deployment.md
└── templates/
    ├── prd-template.md
    └── tech-design-template.md
```

### 文档分支策略

```
main (已发布文档)
  │
  ├── develop (文档开发)
  │     │
  │     ├── docs/feature-new-api
  │     └── docs/update-readme
  │
  └── archive (归档文档)
        │
        └── v1.x
```

## 自动化工具

### 文档生成

```yaml
name: Generate Docs

on:
  push:
    branches: [main]
    paths:
      - 'docs/**'
      - 'src/**'

jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: 生成API文档
        run: npm run docs:api
      
      - name: 生成类型文档
        run: npm run docs:types
      
      - name: 部署文档
        run: npm run docs:deploy
```

### 链接检查

```yaml
name: Check Links

on:
  schedule:
    - cron: '0 0 * * *'

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: 检查Markdown链接
        uses: gaurav-nelson/github-action-markdown-link-check@v1
        with:
          use-quiet-mode: 'yes'
          config-file: '.mlc_config.json'
```

### 拼写检查

```json
{
  "version": "0.2",
  "language": "en",
  "words": [
    "nestjs",
    "typescript",
    "postgresql"
  ],
  "ignorePaths": [
    "node_modules/**",
    "dist/**"
  ]
}
```

## 参考资源

- Write the Docs: https://www.writethedocs.org
- Divio文档系统: https://documentation.divio.com
- 语义化版本: https://semver.org
- Keep a Changelog: https://keepachangelog.com
- Markdown指南: https://www.markdownguide.org
