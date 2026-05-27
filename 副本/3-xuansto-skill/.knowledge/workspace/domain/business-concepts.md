---
id: "KP-WS-DOM-001"
type: "domain"
project: "sample-project"
version: "1.0.0"
created: "2026-04-28T10:00:00Z"
updated: "2026-04-28T10:00:00Z"
source: "manual"
confidence: 0.93
tags: ["业务领域", "领域模型", "业务规则", "实体关系", "核心概念"]
---

# 业务领域概念

## 核心业务实体

### 用户 (User)

系统核心实体，代表平台注册用户。

| 属性 | 类型 | 说明 |
|------|------|------|
| userId | string | 用户唯一标识，格式 `usr_` 前缀 |
| username | string | 用户名，3-20 位字母数字下划线 |
| email | string | 注册邮箱，唯一约束 |
| phone | string | 手机号，可选，E.164 格式 |
| role | enum | 角色：`admin` / `merchant` / `customer` |
| status | enum | 状态：`active` / `suspended` / `deleted` |
| createdAt | datetime | 注册时间 |

### 商品 (Product)

商家发布的可售商品。

| 属性 | 类型 | 说明 |
|------|------|------|
| productId | string | 商品唯一标识，格式 `prd_` 前缀 |
| merchantId | string | 所属商家 userId |
| name | string | 商品名称，2-100 字符 |
| category | string | 分类路径，如 `电子/手机/智能手机` |
| price | decimal | 售价，精确到分，最小 0.01 |
| stock | integer | 库存数量，>= 0 |
| status | enum | 状态：`draft` / `on_sale` / `off_sale` / `removed` |

### 订单 (Order)

用户购买商品产生的交易记录。

| 属性 | 类型 | 说明 |
|------|------|------|
| orderId | string | 订单唯一标识，格式 `ord_` 前缀 |
| customerId | string | 下单用户 userId |
| items | OrderItem[] | 订单明细列表 |
| totalAmount | decimal | 订单总金额 |
| status | enum | 状态：见下方状态机 |
| paymentMethod | enum | 支付方式：`alipay` / `wechat` / `card` |
| createdAt | datetime | 下单时间 |
| paidAt | datetime | 支付时间，可选 |

### 支付 (Payment)

订单关联的支付记录。

| 属性 | 类型 | 说明 |
|------|------|------|
| paymentId | string | 支付唯一标识，格式 `pay_` 前缀 |
| orderId | string | 关联订单 ID |
| amount | decimal | 支付金额 |
| channel | enum | 支付渠道 |
| status | enum | 状态：`pending` / `success` / `failed` / `refunded` |
| paidAt | datetime | 支付完成时间 |

## 业务规则

### BR-001: 订单状态机

```
created → pending_payment → paid → shipping → completed
    │           │              │
    │           ▼              ▼
    │      cancelled      refunding → refunded
    │
    ▼
cancelled
```

- `created`: 订单创建，等待确认
- `pending_payment`: 确认后等待支付，超时 30 分钟自动取消
- `paid`: 支付成功，等待发货
- `shipping`: 已发货，等待收货
- `completed`: 已完成，7 天后自动确认收货
- `cancelled`: 已取消，库存回滚
- `refunding`: 退款中，需审核
- `refunded`: 已退款

### BR-002: 库存扣减规则

- 下单时预扣库存（`stock` 减少但标记为锁定）
- 支付成功后确认扣减
- 订单取消或支付超时后释放锁定库存
- 同一商品并发下单使用 Redis 分布式锁保证一致性
- 库存为 0 时商品自动标记为 `off_sale`

### BR-003: 退款规则

- 仅 `paid` 和 `shipping` 状态可申请退款
- `paid` 状态：全额退款，自动审核
- `shipping` 状态：需商家确认，最多退商品金额的 100%
- 退款审核时限：48 小时，超时自动通过
- 单笔订单最多退款 3 次

### BR-004: 用户权限矩阵

| 操作 | admin | merchant | customer |
|------|-------|----------|----------|
| 管理用户 | ✅ | ❌ | ❌ |
| 发布商品 | ✅ | ✅ | ❌ |
| 购买商品 | ✅ | ❌ | ✅ |
| 处理订单 | ✅ | ✅（自己的） | ❌ |
| 查看统计 | ✅ | ✅（自己的） | ❌ |
| 系统配置 | ✅ | ❌ | ❌ |

## 领域关系

```
User (1) ──────< Order (N)
  │                  │
  │                  ├── OrderItem (N)
  │                  │       │
  │                  │       └── Product (1)
  │                  │
  │                  └── Payment (1)
  │
  └──────< Product (N)   [商家发布商品]
```

- 一个用户（商家）可发布多个商品
- 一个用户（顾客）可创建多个订单
- 一个订单包含多个订单明细（OrderItem）
- 每个订单明细关联一个商品
- 一个订单对应一笔支付记录

## 相关知识

- [KP-WS-ARCH-001] 系统架构概览 — 模块划分与技术选型
- [KP-WS-API-001] API 错误码规范 — 业务错误码定义
- [KP-WS-TERM-001] 术语表 — 领域术语定义
