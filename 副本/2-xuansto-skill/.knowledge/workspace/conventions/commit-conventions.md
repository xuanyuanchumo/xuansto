---
id: "KP-WS-CONV-001"
type: "conventions"
project: "sample-project"
version: "1.0.0"
created: "2026-04-28T10:00:00Z"
updated: "2026-04-28T10:00:00Z"
source: "manual"
confidence: 0.96
tags: ["提交规范", "Conventional Commits", "分支策略", "代码规范", "Git约定"]
---

# 提交约定

## Conventional Commits 格式

本项目遵循 [Conventional Commits](https://www.conventionalcommits.org/) 规范，提交信息格式如下：

```
<type>(<scope>): <subject>

[body]

[footer(s)]
```

### 格式规则

- **subject**：简短描述，不超过 50 字符，使用祈使句（如 `add` 而非 `added`）
- **body**：详细描述变更原因和内容，每行不超过 72 字符
- **footer**：关联 Issue、Breaking Change 等
- **中文项目**：subject 使用简体中文，技术术语保留英文

## 类型定义

| 类型 | 说明 | SemVer 影响 | 示例 |
|------|------|-------------|------|
| feat | 新功能 | MINOR | `feat(order): 添加订单退款功能` |
| fix | 修复缺陷 | PATCH | `fix(auth): 修复 Token 过期后未跳转登录页` |
| docs | 文档变更 | 无 | `docs(api): 更新支付接口错误码说明` |
| style | 代码格式（不影响逻辑） | 无 | `style(product): 格式化商品列表组件` |
| refactor | 重构（不新增功能/修复缺陷） | 无 | `refactor(user): 拆分用户服务为独立模块` |
| perf | 性能优化 | PATCH | `perf(search): 优化商品搜索查询索引` |
| test | 测试相关 | 无 | `test(order): 补充订单状态机单元测试` |
| build | 构建系统或外部依赖 | 可能 | `build(deps): 升级 FastAPI 至 0.115` |
| ci | CI/CD 配置变更 | 无 | `ci: 添加 staging 环境自动部署流程` |
| chore | 其他不修改 src/test 的变更 | 无 | `chore: 更新 .gitignore 规则` |
| revert | 回退提交 | 视情况 | `revert: 回退 feat(order): 添加退款功能` |

## Scope 定义

| Scope | 模块 | 说明 |
|-------|------|------|
| auth | 认证授权 | 登录、注册、Token、权限 |
| user | 用户管理 | 用户信息、角色、商家入驻 |
| product | 商品管理 | 商品、分类、库存 |
| order | 订单管理 | 下单、支付、发货、退款 |
| payment | 支付模块 | 支付渠道、对账、结算 |
| search | 搜索服务 | 全文检索、筛选、排序 |
| api | API 层 | 接口定义、中间件、错误码 |
| db | 数据库 | 迁移、索引、模型 |
| infra | 基础设施 | Docker、K8s、监控、日志 |
| deps | 依赖管理 | 第三方库升级、安全补丁 |

## 提交示例

### 新功能

```
feat(order): 添加订单自动取消功能

- 支付超时 30 分钟自动取消订单
- 取消时释放预扣库存
- 通过 RabbitMQ 延迟队列实现定时触发

Closes #1234
```

### 缺陷修复

```
fix(product): 修复并发下单时库存超卖问题

使用 Redis 分布式锁替代数据库行锁，避免高并发场景下
库存扣减不一致导致超卖。

Fixes #5678
```

### 破坏性变更

```
feat(api)!: 重构用户接口响应格式

将 snake_case 字段统一改为 camelCase，
与前端约定保持一致。

BREAKING CHANGE: 用户相关 API 响应字段命名变更
- user_id → userId
- created_at → createdAt
- 前端需同步更新字段映射

Migration-Guide: 见 docs/migration/v2.md
Ref: #9012
```

### 重构

```
refactor(payment): 抽象支付渠道为策略模式

将支付宝/微信/银联的支付逻辑从 PaymentService
拆分为独立策略类，便于后续新增支付渠道。
```

## 分支命名约定

| 分支类型 | 格式 | 示例 | 生命周期 |
|----------|------|------|----------|
| 主分支 | `main` | main | 永久 |
| 开发分支 | `develop` | develop | 永久 |
| 功能分支 | `feat/<scope>-<description>` | `feat/order-refund` | 合并后删除 |
| 修复分支 | `fix/<scope>-<description>` | `fix/auth-token-expire` | 合并后删除 |
| 热修复 | `hotfix/<version>-<description>` | `hotfix/v1.2.1-payment-crash` | 合并后删除 |
| 发布分支 | `release/<version>` | `release/v1.3.0` | 合并后删除 |
| 实验分支 | `exp/<description>` | `exp/new-search-engine` | 评估后删除 |

### 分支规则

1. `main` 分支始终可部署，所有合并必须通过 PR 和 Code Review
2. `develop` 为日常开发集成分支，功能分支从此拉出
3. 功能分支命名不超过 40 字符，使用小写字母和连字符
4. 禁止直接向 `main` 推送，必须通过 PR 合并
5. PR 合并前必须通过 CI 检查（lint、test、build）
6. 合并策略：功能分支使用 squash merge，热修复使用 merge commit

## 相关知识

- [KP-WS-ARCH-001] 系统架构概览 — CI/CD 流水线配置
- [KP-WS-TERM-001] 术语表 — 技术缩写与命名约定
- [KP-WS-ENV-001] 环境变量配置 — 密钥管理规范
