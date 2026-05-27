---
id: "KP-WS-ENV-001"
type: "environment"
project: "sample-project"
version: "1.0.0"
created: "2026-04-28T10:00:00Z"
updated: "2026-04-28T10:00:00Z"
source: "manual"
confidence: 0.91
tags: ["环境变量", "配置管理", "部署环境", "开发环境", "密钥管理"]
---

# 环境变量配置

## 命名约定

环境变量遵循以下命名规范：

| 规则 | 格式 | 示例 |
|------|------|------|
| 全局变量 | `APP_` 前缀 | `APP_NAME`, `APP_ENV` |
| 数据库相关 | `DB_` 前缀 | `DB_HOST`, `DB_PORT` |
| Redis 相关 | `REDIS_` 前缀 | `REDIS_URL`, `REDIS_TTL` |
| 消息队列 | `MQ_` 前缀 | `MQ_HOST`, `MQ_VHOST` |
| 外部服务 | `EXT_{服务名}_` 前缀 | `EXT_ALIYUN_OSS_KEY` |
| 功能开关 | `FEATURE_` 前缀 | `FEATURE_NEW_CHECKOUT` |
| 密钥类 | `SECRET_` 前缀 | `SECRET_JWT_KEY` |

### 附加规则

- 全部使用 `UPPER_SNAKE_CASE`
- 布尔值使用 `true` / `false` 字符串
- 多值使用逗号分隔，如 `ALLOWED_ORIGINS=http://a.com,http://b.com`
- 连接字符串优先使用 URL 格式，如 `DATABASE_URL=postgresql://user:pass@host:5432/db`
- 敏感变量必须以 `SECRET_` 前缀标识，禁止硬编码或提交至版本控制

## 必需变量

| 变量名 | 类型 | 必需 | 默认值 | 说明 |
|--------|------|------|--------|------|
| APP_NAME | string | 是 | - | 应用名称 |
| APP_ENV | enum | 是 | - | 运行环境：`development` / `staging` / `production` |
| APP_PORT | integer | 否 | 8000 | 服务监听端口 |
| APP_DEBUG | boolean | 否 | false | 调试模式（生产环境必须为 false） |
| DATABASE_URL | string | 是 | - | PostgreSQL 连接字符串 |
| DB_POOL_SIZE | integer | 否 | 10 | 连接池大小 |
| DB_MAX_OVERFLOW | integer | 否 | 20 | 连接池最大溢出 |
| REDIS_URL | string | 是 | - | Redis 连接字符串 |
| REDIS_TTL | integer | 否 | 3600 | 默认缓存过期时间（秒） |
| MQ_URL | string | 是 | - | RabbitMQ 连接字符串 |
| SECRET_JWT_KEY | string | 是 | - | JWT 签名密钥 |
| SECRET_JWT_ALGORITHM | string | 否 | HS256 | JWT 签名算法 |
| JWT_EXPIRE_MINUTES | integer | 否 | 60 | Token 过期时间（分钟） |
| LOG_LEVEL | enum | 否 | INFO | 日志级别：`DEBUG` / `INFO` / `WARNING` / `ERROR` |
| CORS_ALLOWED_ORIGINS | string | 否 | * | 允许的跨域来源，逗号分隔 |

## 环境配置示例

### 开发环境 (development)

```env
APP_NAME=sample-project
APP_ENV=development
APP_PORT=8000
APP_DEBUG=true

DATABASE_URL=postgresql://dev:dev@localhost:5432/sample_dev
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10

REDIS_URL=redis://localhost:6379/0
REDIS_TTL=1800

MQ_URL=amqp://guest:guest@localhost:5672/

SECRET_JWT_KEY=dev-only-secret-key-do-not-use-in-production
SECRET_JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=480

LOG_LEVEL=DEBUG
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173

FEATURE_NEW_CHECKOUT=true
```

### 预发布环境 (staging)

```env
APP_NAME=sample-project
APP_ENV=staging
APP_PORT=8000
APP_DEBUG=false

DATABASE_URL=postgresql://staging_app:${SECRET_DB_PASSWORD}@pg-staging.internal:5432/sample_staging
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20

REDIS_URL=redis://redis-staging.internal:6379/1
REDIS_TTL=3600

MQ_URL=amqp://staging_app:${SECRET_MQ_PASSWORD}@mq-staging.internal:5672/staging

SECRET_JWT_KEY=${SECRET_JWT_KEY}
SECRET_JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=120

LOG_LEVEL=INFO
CORS_ALLOWED_ORIGINS=https://staging.sample-project.com

FEATURE_NEW_CHECKOUT=true
```

### 生产环境 (production)

```env
APP_NAME=sample-project
APP_ENV=production
APP_PORT=8000
APP_DEBUG=false

DATABASE_URL=postgresql://prod_app:${SECRET_DB_PASSWORD}@pg-primary.internal:5432/sample_prod
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40

REDIS_URL=redis://redis-cluster.internal:6379/2
REDIS_TTL=3600

MQ_URL=amqp://prod_app:${SECRET_MQ_PASSWORD}@mq-cluster.internal:5672/production

SECRET_JWT_KEY=${SECRET_JWT_KEY}
SECRET_JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60

LOG_LEVEL=WARNING
CORS_ALLOWED_ORIGINS=https://www.sample-project.com,https://app.sample-project.com

FEATURE_NEW_CHECKOUT=false
```

## 密钥管理规范

1. **所有密钥通过环境变量注入**，禁止硬编码在代码或配置文件中
2. **使用 `${SECRET_XXX}` 引用**，由部署系统在运行时替换
3. **开发环境密钥与生产环境严格隔离**
4. **密钥轮换周期**：JWT 密钥每 90 天轮换，数据库密码每 180 天轮换
5. **密钥存储**：生产环境使用 Vault 或云厂商 KMS 管理
6. **`.env` 文件**：仅用于本地开发，必须加入 `.gitignore`

## 相关知识

- [KP-WS-ARCH-001] 系统架构概览 — 基础设施配置
- [KP-WS-CONV-001] 提交约定 — 禁止提交密钥
- [KP-GEN-020] 安全编码基础 — 密钥管理最佳实践
