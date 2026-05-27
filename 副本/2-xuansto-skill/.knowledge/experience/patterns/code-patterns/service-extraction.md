---
id: "KP-EXP-REF-001"
type: "refactoring"
severity: "medium"
category: "architecture"
tags: ["service-extraction", "clean-architecture", "God Class", "领域驱动", "渐进式重构"]
version: "1.0.0"
created: "2026-04-28T10:00:00Z"
updated: "2026-04-28T10:00:00Z"
source: "auto_precipitation"
confidence: 0.87
last_validated: "2026-04-28T10:00:00Z"
success_count: 0
failure_count: 0
occurrences: 2
trigger: "refactoring_completed"
references:
  - id: "KP-GEN-030"
    relation: "complies"
  - id: "KP-EXP-PAT-001"
    relation: "extends"
---

# 订单服务从 God Class 中提取重构

## 重构动机

项目中的 `OrderService` 类承担了订单生命周期的所有职责，包括创建、支付、发货、退款、库存扣减、通知发送等，代码量超过 2500 行，严重违反单一职责原则（SRP）。

### God Class 问题表现

- 修改支付逻辑可能影响库存扣减
- 新增退款渠道需要改动 800 行的方法
- 单元测试需要 mock 15+ 个依赖
- 代码审查无法在合理时间内完成
- 新成员理解成本极高

### 重构前架构

```
OrderService (2500+ 行)
├── createOrder()          — 订单创建 + 库存扣减 + 优惠券核销
├── payOrder()             — 支付处理 + 状态流转 + 通知
├── shipOrder()            — 物流创建 + 状态流转 + 通知
├── refundOrder()          — 退款处理 + 库存归还 + 优惠券归还 + 通知
├── cancelOrder()          — 取消处理 + 库存归还 + 优惠券归还 + 通知
├── getOrderDetail()       — 查询 + 权限校验
├── listOrders()           — 列表查询 + 过滤 + 排序 + 分页
└── 15+ 个 private 辅助方法
```

---

## 重构后架构

```
OrderDomainService (协调者, 200 行)
├── OrderCreationService     — 订单创建
├── OrderPaymentService      — 支付处理
├── OrderFulfillmentService  — 履约发货
├── OrderRefundService       — 退款处理
├── OrderQueryService        — 查询服务
├── InventoryService         — 库存管理
├── CouponService            — 优惠券管理
└── NotificationService      — 通知服务
```

---

## 渐进式提取步骤

### 第一步：提取查询服务（风险最低）

```python
class OrderQueryService:
    def __init__(self, order_repo: OrderRepository):
        self._order_repo = order_repo

    async def get_detail(self, order_id: str, user_id: str) -> OrderDetail:
        order = await self._order_repo.get_by_id(order_id)
        if order.user_id != user_id:
            raise PermissionError("无权访问此订单")
        return OrderDetail.from_entity(order)

    async def list_orders(self, user_id: str, page: PageRequest) -> PageResult:
        return await self._order_repo.list_by_user(user_id, page)
```

### 第二步：提取通知服务

```python
class NotificationService:
    def __init__(self, email_sender, sms_sender, push_sender):
        self._email = email_sender
        self._sms = sms_sender
        self._push = push_sender

    async def notify_order_created(self, order: Order) -> None:
        await self._email.send(order.user_email, "order_created", {"order": order})

    async def notify_order_paid(self, order: Order) -> None:
        await self._email.send(order.user_email, "order_paid", {"order": order})
        await self._push.send(order.user_id, "支付成功", f"订单 {order.order_no} 已支付")

    async def notify_order_shipped(self, order: Order) -> None:
        await self._sms.send(order.user_phone, f"订单 {order.order_no} 已发货")
```

### 第三步：提取库存服务

```python
class InventoryService:
    def __init__(self, inventory_repo: InventoryRepository):
        self._repo = inventory_repo

    async def reserve(self, items: list[OrderItem]) -> None:
        for item in items:
            stock = await self._repo.get_stock(item.sku_id)
            if stock.available < item.quantity:
                raise InsufficientStockError(item.sku_id)
            await self._repo.decrease(item.sku_id, item.quantity)

    async def release(self, items: list[OrderItem]) -> None:
        for item in items:
            await self._repo.increase(item.sku_id, item.quantity)
```

### 第四步：提取核心业务服务

```python
class OrderCreationService:
    def __init__(self, order_repo, inventory: InventoryService,
                 coupon: CouponService, notification: NotificationService):
        self._order_repo = order_repo
        self._inventory = inventory
        self._coupon = coupon
        self._notification = notification

    async def create(self, cmd: CreateOrderCommand) -> Order:
        await self._inventory.reserve(cmd.items)
        if cmd.coupon_id:
            await self._coupon.validate_and_lock(cmd.coupon_id, cmd.user_id)
        order = Order.create(cmd)
        await self._order_repo.save(order)
        await self._notification.notify_order_created(order)
        return order
```

### 第五步：建立领域协调者

```python
class OrderDomainService:
    def __init__(self, creation: OrderCreationService,
                 payment: OrderPaymentService,
                 fulfillment: OrderFulfillmentService,
                 refund: OrderRefundService):
        self._creation = creation
        self._payment = payment
        self._fulfillment = fulfillment
        self._refund = refund

    async def create_order(self, cmd: CreateOrderCommand) -> Order:
        return await self._creation.create(cmd)

    async def pay_order(self, order_id: str, payment: PaymentInfo) -> Order:
        return await self._payment.pay(order_id, payment)
```

---

## 重构期间测试策略

| 策略 | 说明 |
|------|------|
| 继承委托 | 新服务从旧类继承，逐步将方法委托到新服务 |
| 特征测试 | 为旧方法编写 characterization test 锁定行为 |
| 并行运行 | 新旧实现并行运行，比对结果一致性 |
| 金丝雀发布 | 先对 5% 流量使用新实现，逐步扩大 |
| 回滚预案 | 每步保留 Feature Flag 可即时回退 |

---

## 经验教训

| 教训 | 说明 |
|------|------|
| 先测试后重构 | 没有测试覆盖的重构是赌博，先补齐特征测试 |
| 小步提交 | 每次只提取一个服务，确保每步可独立回滚 |
| 依赖注入是前提 | 没有依赖注入，提取后仍是硬编码耦合 |
| 查询优先提取 | 查询服务无副作用，提取风险最低，适合练手 |
| 通知最后提取 | 通知是横切关注点，提取后用事件驱动更自然 |
| 避免 Big Bang | 一次性重写风险极高，渐进式迁移更安全 |

## 相关知识

- [KP-GEN-030] 软件设计最佳实践 — 单一职责与领域驱动
- [KP-EXP-PAT-001] 仓储模式 — 数据访问层解耦
