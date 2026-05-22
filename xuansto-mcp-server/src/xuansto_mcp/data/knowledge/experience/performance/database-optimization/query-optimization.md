---
id: "KP-EXP-PERF-DB-001"
type: "performance"
category: "database"
tags: ["查询优化", "慢查询", "索引", "N+1", "EXPLAIN", "PostgreSQL"]
version: "1.0.0"
confidence: 0.92
---

## 数据库查询优化 (置信度: 0.92 | 技术栈: PostgreSQL/MySQL)

### 现象
API 响应慢（>1s），数据库 CPU 飙升，慢查询日志大量记录。

### 根因
缺失索引、N+1 查询、SELECT * 返回冗余列、大表全表扫描、连接池耗尽。

### 解决方案

```sql
EXPLAIN (ANALYZE, BUFFERS) SELECT * FROM orders WHERE user_id = 123;
CREATE INDEX idx_orders_user_id ON orders(user_id);
```

```python
orders = await session.execute(
    select(OrderModel).options(selectinload(OrderModel.items)).where(OrderModel.user_id == user_id)
)
```

```typescript
const orders = await this.repo.find({
    where: { userId },
    relations: ["items"],
    select: ["id", "total", "createdAt"],
});
```

### 验证
慢查询阈值 200ms，EXPLAIN 确认使用索引扫描而非顺序扫描。
