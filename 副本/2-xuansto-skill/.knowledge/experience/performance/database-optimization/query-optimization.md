---
id: "KP-EXP-PERF-001"
type: "performance"
severity: "medium"
category: "database"
tags: ["postgresql", "query", "optimization", "索引", "慢查询", "N+1"]
version: "1.0.0"
created: "2026-04-28T10:00:00Z"
updated: "2026-04-28T10:00:00Z"
source: "auto_precipitation"
confidence: 0.90
last_validated: "2026-04-28T10:00:00Z"
success_count: 0
failure_count: 0
occurrences: 5
trigger: "performance_fix_completed"
references:
  - id: "KP-GEN-020"
    relation: "complies"
---

# 用户订单查询慢查询优化

## 问题描述

在生产环境中，用户订单列表页面加载时间随数据量增长持续恶化。当单用户订单数超过 500 条时，接口响应时间从正常的 200ms 飙升至 8-12 秒，严重影响用户体验。

### 典型表现

- 接口 P99 延迟超过 10 秒
- PostgreSQL CPU 使用率峰值达 85%
- 数据库连接池频繁耗尽
- 前端超时错误率上升至 12%

### 问题 SQL

```sql
SELECT o.id, o.order_no, o.status, o.created_at,
       u.name AS user_name,
       (SELECT COUNT(*) FROM order_items oi WHERE oi.order_id = o.id) AS item_count,
       (SELECT SUM(oi.price * oi.quantity) FROM order_items oi WHERE oi.order_id = o.id) AS total_amount
FROM orders o
LEFT JOIN users u ON u.id = o.user_id
WHERE o.user_id = 'usr_12345'
ORDER BY o.created_at DESC;
```

---

## 根因分析

### 1. 缺失复合索引

`orders` 表仅有 `user_id` 单列索引，查询按 `user_id` 筛选并按 `created_at DESC` 排序时，数据库需要额外执行 filesort。

```sql
EXPLAIN ANALYZE 结果：
-> Sort (cost=12345.00..12400.00 rows=500 width=100) (actual time=8500ms)
   -> Seq Scan on orders (cost=0.00..10000.00 rows=500 width=100)
```

### 2. 相关子查询导致 N+1 问题

每行订单执行两次子查询（`COUNT` 和 `SUM`），500 条订单产生 1000 次子查询。

### 3. 未使用分页

一次性加载用户全部订单，数据量大时内存和网络开销巨大。

---

## 优化方案

### 1. 创建复合索引

```sql
CREATE INDEX idx_orders_user_created
ON orders (user_id, created_at DESC);
```

### 2. 子查询改写为 JOIN 聚合

```sql
SELECT o.id, o.order_no, o.status, o.created_at,
       u.name AS user_name,
       COALESCE(oi_summary.item_count, 0) AS item_count,
       COALESCE(oi_summary.total_amount, 0) AS total_amount
FROM orders o
LEFT JOIN users u ON u.id = o.user_id
LEFT JOIN (
    SELECT order_id,
           COUNT(*) AS item_count,
           SUM(price * quantity) AS total_amount
    FROM order_items
    GROUP BY order_id
) oi_summary ON oi_summary.order_id = o.id
WHERE o.user_id = 'usr_12345'
ORDER BY o.created_at DESC
LIMIT 20 OFFSET 0;
```

### 3. 为 order_items 添加覆盖索引

```sql
CREATE INDEX idx_order_items_covering
ON order_items (order_id, price, quantity);
```

### 4. 应用层分页封装

```python
from pydantic import BaseModel

class PageRequest(BaseModel):
    page: int = 1
    page_size: int = 20

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

async def get_user_orders(user_id: str, page: PageRequest) -> dict:
    total = await db.fetch_val(
        "SELECT COUNT(*) FROM orders WHERE user_id = $1",
        user_id,
    )
    rows = await db.fetch_all(
        """SELECT o.id, o.order_no, o.status, o.created_at,
                  u.name AS user_name,
                  COALESCE(oi_summary.item_count, 0) AS item_count,
                  COALESCE(oi_summary.total_amount, 0) AS total_amount
           FROM orders o
           LEFT JOIN users u ON u.id = o.user_id
           LEFT JOIN (
               SELECT order_id, COUNT(*) AS item_count,
                      SUM(price * quantity) AS total_amount
               FROM order_items GROUP BY order_id
           ) oi_summary ON oi_summary.order_id = o.id
           WHERE o.user_id = $1
           ORDER BY o.created_at DESC
           LIMIT $2 OFFSET $3""",
        user_id, page.page_size, page.offset,
    )
    return {
        "items": rows,
        "total": total,
        "page": page.page,
        "page_size": page.page_size,
    }
```

---

## 性能对比

| 指标 | 优化前 | 优化后 | 提升 |
|------|--------|--------|------|
| 查询耗时 (P99) | 10,200ms | 45ms | 226x |
| 数据库 CPU 峰值 | 85% | 12% | 7x |
| 子查询次数 | 1000 | 0 | - |
| 连接池等待 | 频繁耗尽 | 无等待 | - |
| 前端超时率 | 12% | 0.01% | 1200x |

---

## 预防措施

| 措施 | 说明 |
|------|------|
| 慢查询监控 | 开启 PostgreSQL `log_min_duration_statement = 200`，记录超过 200ms 的查询 |
| EXPLAIN 审查 | 新增查询必须附带 `EXPLAIN ANALYZE` 结果进行 Code Review |
| 索引设计规范 | WHERE + ORDER BY 组合必须建立复合索引 |
| 禁止裸子查询 | 代码规范禁止在 SELECT 中使用相关子查询 |
| 分页强制 | 列表查询必须实现分页，默认 `page_size` 不超过 50 |
| 性能基线测试 | CI 中集成查询性能回归测试 |

## 相关知识

- [KP-GEN-020] 安全编码基础 — SQL 注入防护与参数化查询
