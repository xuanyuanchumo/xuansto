---
id: "KP-WS-TERM-001"
type: "glossary"
project: "sample-project"
version: "1.0.0"
created: "2026-04-28T10:00:00Z"
updated: "2026-04-28T10:00:00Z"
source: "manual"
confidence: 0.98
tags: ["术语表", "缩写", "业务术语", "技术术语", "项目词汇"]
---

# 项目术语表

## 项目专用术语

| 术语 | 英文 | 定义 | 使用场景 |
|------|------|------|----------|
| 预扣库存 | Stock Pre-lock | 下单时临时锁定库存，支付后确认扣减 | 订单创建流程 |
| 锁定库存 | Locked Stock | 已被未支付订单占用的库存数量 | 库存管理 |
| 可售库存 | Available Stock | 实际可售数量 = 总库存 - 锁定库存 | 商品列表展示 |
| 退款审核 | Refund Audit | 商家或系统对退款申请的审批流程 | 退款流程 |
| 自动收货 | Auto-confirm | 发货后超时未操作自动确认收货 | 订单完成 |
| 对账 | Reconciliation | 支付渠道流水与系统订单的核对 | 财务结算 |
| 商家入驻 | Merchant Onboarding | 商家注册并完成资质审核的流程 | 用户管理 |

## 业务领域术语

| 术语 | 英文 | 定义 | 所属领域 |
|------|------|------|----------|
| SKU | Stock Keeping Unit | 最小库存单位，对应具体规格的商品 | 商品域 |
| SPU | Standard Product Unit | 标准产品单元，同款商品的不同规格集合 | 商品域 |
| GMV | Gross Merchandise Volume | 成交总额，包含未支付和已退款订单 | 交易域 |
| 净收入 | Net Revenue | 实际到账金额 = GMV - 退款 - 手续费 | 交易域 |
| 转化率 | Conversion Rate | 下单用户数 / 访问用户数 × 100% | 运营域 |
| 客单价 | Average Order Value | GMV / 有效订单数 | 运营域 |
| 复购率 | Repurchase Rate | 二次及以上购买用户占比 | 运营域 |
| DSR | Detail Seller Rating | 商家动态评分，含描述/服务/物流三项 | 评价域 |
| 账期 | Settlement Cycle | 商家可提现的结算周期 | 支付域 |
| 保证金 | Security Deposit | 商家入驻时缴纳的担保金额 | 支付域 |

## 技术缩写

| 缩写 | 全称 | 中文含义 | 使用场景 |
|------|------|----------|----------|
| ADR | Architecture Decision Record | 架构决策记录 | 架构设计 |
| API | Application Programming Interface | 应用编程接口 | 接口开发 |
| BFF | Backend For Frontend | 面向前端的后端 | 服务架构 |
| CQRS | Command Query Responsibility Segregation | 命令查询职责分离 | 数据架构 |
| DDD | Domain-Driven Design | 领域驱动设计 | 业务建模 |
| DTO | Data Transfer Object | 数据传输对象 | 接口层 |
| E2E | End-to-End | 端到端 | 测试 |
| FTS | Full-Text Search | 全文检索 | 搜索功能 |
| GRPC | gRPC Remote Procedure Call | gRPC 远程过程调用 | 微服务通信 |
| HPA | Horizontal Pod Autoscaler | 水平 Pod 自动扩缩容 | K8s 运维 |
| IAM | Identity and Access Management | 身份与访问管理 | 安全认证 |
| JWT | JSON Web Token | JSON 网络令牌 | 身份认证 |
| K8s | Kubernetes | 容器编排平台 | 部署运维 |
| MQ | Message Queue | 消息队列 | 异步通信 |
| ORM | Object-Relational Mapping | 对象关系映射 | 数据访问 |
| QPS | Queries Per Second | 每秒查询数 | 性能指标 |
| RPS | Requests Per Second | 每秒请求数 | 性能指标 |
| SLA | Service Level Agreement | 服务等级协议 | 运维保障 |
| TPS | Transactions Per Second | 每秒事务数 | 性能指标 |
| VO | Value Object | 值对象 | 领域建模 |

## 命名约定术语

| 约定 | 格式 | 示例 |
|------|------|------|
| 实体 ID 前缀 | `{类型缩写}_` | `usr_abc123`, `ord_20260428` |
| 数据库表名 | `snake_case` 复数 | `users`, `order_items` |
| API 路径 | `kebab-case` 复数 | `/api/v1/order-items` |
| JSON 字段 | `camelCase` | `userId`, `totalAmount` |
| 环境变量 | `UPPER_SNAKE_CASE` | `DATABASE_URL`, `REDIS_HOST` |
| 枚举值 | `snake_case` | `pending_payment`, `on_sale` |

## 相关知识

- [KP-WS-ARCH-001] 系统架构概览 — 架构组件与术语
- [KP-WS-DOM-001] 业务领域概念 — 领域实体详解
- [KP-WS-CONV-001] 提交约定 — 命名与编码规范
