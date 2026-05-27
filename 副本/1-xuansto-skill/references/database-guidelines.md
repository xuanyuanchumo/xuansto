# 数据库指南参考文档

> 版本: 1.0.0 | 更新日期: 2026-04-17 | 编码: UTF-8 | 行尾: LF

---

## 目录

1. [命名规范](#命名规范)
2. [索引策略](#索引策略)
3. [查询优化](#查询优化)
4. [迁移管理](#迁移管理)

---

## 命名规范

### 表命名

| 规则 | 说明 | 示例 |
|------|------|------|
| 使用小写 | 避免大小写问题 | `users`, `order_items` |
| 使用下划线分隔 | snake_case格式 | `user_profiles`, `payment_methods` |
| 使用复数形式 | 表示数据集合 | `users`, `products`, `orders` |
| 避免保留字 | 不使用SQL关键字 | `user_accounts` 而非 `users` |
| 表达清晰 | 名称应反映内容 | `order_items` 而非 `items` |

### 字段命名

| 规则 | 说明 | 示例 |
|------|------|------|
| 使用小写下划线 | snake_case格式 | `created_at`, `user_id` |
| 主键命名 | id或表名_id | `id`, `user_id` |
| 外键命名 | 关联表名_id | `user_id`, `order_id` |
| 布尔字段 | is/has前缀 | `is_active`, `has_verified` |
| 时间字段 | 动作_at/ed_at | `created_at`, `deleted_at` |
| 金额字段 | 使用分为单位 | `price_cents` |

### 索引命名

| 类型 | 命名规则 | 示例 |
|------|----------|------|
| 普通索引 | `idx_表名_字段名` | `idx_users_email` |
| 唯一索引 | `uq_表名_字段名` | `uq_users_email` |
| 复合索引 | `idx_表名_字段1_字段2` | `idx_orders_user_status` |
| 全文索引 | `ft_表名_字段名` | `ft_products_name` |
| 外键索引 | `fk_表名_关联表名` | `fk_orders_users` |

### 约束命名

| 类型 | 命名规则 | 示例 |
|------|----------|------|
| 主键 | `pk_表名` | `pk_users` |
| 外键 | `fk_表名_关联表名` | `fk_orders_users` |
| 唯一约束 | `uq_表名_字段名` | `uq_users_email` |
| 检查约束 | `ck_表名_字段名` | `ck_users_age` |
| 非空约束 | 默认，无需命名 | - |

### 完整示例

```sql
-- 用户表
CREATE TABLE users (
    id              BIGSERIAL PRIMARY KEY,
    email           VARCHAR(255) NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,
    name            VARCHAR(100),
    is_active       BOOLEAN DEFAULT true,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT uq_users_email UNIQUE (email),
    CONSTRAINT ck_users_email CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_created_at ON users(created_at);

-- 订单表
CREATE TABLE orders (
    id              BIGSERIAL PRIMARY KEY,
    user_id         BIGINT NOT NULL,
    status          VARCHAR(20) NOT NULL DEFAULT 'pending',
    total_cents     BIGINT NOT NULL,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_orders_users FOREIGN KEY (user_id) REFERENCES users(id),
    CONSTRAINT ck_orders_status CHECK (status IN ('pending', 'paid', 'shipped', 'completed', 'cancelled')),
    CONSTRAINT ck_orders_total CHECK (total_cents >= 0)
);

CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_user_status ON orders(user_id, status);
```

---

## 索引策略

### 索引类型

| 类型 | 用途 | 特点 |
|------|------|------|
| B-Tree | 等值、范围、排序查询 | 默认类型，最常用 |
| Hash | 等值查询 | 最快等值查找，不支持范围 |
| GiST | 几何、全文搜索 | 支持复杂查询 |
| GIN | 数组、JSON、全文 | 支持包含查询 |
| BRIN | 大表范围查询 | 占用空间小 |

### 索引设计原则

**1. 选择性原则**

```sql
-- 高选择性字段适合建索引
-- 选择性 = 不同值数量 / 总行数

-- 高选择性 (接近1): 适合索引
CREATE INDEX idx_users_email ON users(email);

-- 低选择性 (接近0): 不适合单独索引
-- 不建议: CREATE INDEX idx_users_gender ON users(gender);
```

**2. 最左前缀原则**

```sql
-- 复合索引 (a, b, c)
CREATE INDEX idx_example ON table(a, b, c);

-- 可以使用索引
WHERE a = 1
WHERE a = 1 AND b = 2
WHERE a = 1 AND b = 2 AND c = 3

-- 不能使用索引
WHERE b = 2
WHERE c = 3
WHERE b = 2 AND c = 3
```

**3. 覆盖索引**

```sql
-- 创建覆盖索引避免回表
CREATE INDEX idx_orders_user_status_total ON orders(user_id, status) INCLUDE (total_cents);

-- 查询可以直接从索引获取所有数据
SELECT status, total_cents 
FROM orders 
WHERE user_id = 123;
```

**4. 部分索引**

```sql
-- 只索引活跃用户
CREATE INDEX idx_users_active_email ON users(email) WHERE is_active = true;

-- 只索引未完成订单
CREATE INDEX idx_orders_pending ON orders(created_at) WHERE status = 'pending';
```

**5. 表达式索引**

```sql
-- 索引函数结果
CREATE INDEX idx_users_lower_email ON users(LOWER(email));

-- 索引日期部分
CREATE INDEX idx_orders_year ON orders(EXTRACT(YEAR FROM created_at));
```

### 索引使用场景

| 场景 | 建议 |
|------|------|
| WHERE条件字段 | 优先考虑索引 |
| JOIN关联字段 | 必须建立索引 |
| ORDER BY排序字段 | 考虑建立索引 |
| GROUP BY分组字段 | 考虑建立索引 |
| DISTINCT去重字段 | 考虑建立索引 |
| 频繁更新的字段 | 谨慎建立索引 |
| 小表 | 不需要索引 |

### 索引维护

```sql
-- 查看索引使用情况
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;

-- 查找未使用的索引
SELECT 
    schemaname || '.' || relname AS table,
    indexrelname AS index,
    pg_size_pretty(pg_relation_size(i.indexrelid)) AS index_size,
    idx_scan AS index_scans
FROM pg_stat_user_indexes ui
JOIN pg_index i ON ui.indexrelid = i.indexrelid
WHERE NOT indisunique 
  AND idx_scan < 50 
  AND pg_relation_size(relid) > 5 * 8192
ORDER BY pg_relation_size(i.indexrelid) DESC;

-- 重建索引
REINDEX INDEX idx_users_email;
REINDEX TABLE users;

-- 更新统计信息
ANALYZE users;
```

---

## 查询优化

### 查询分析

```sql
-- 使用EXPLAIN分析查询计划
EXPLAIN SELECT * FROM users WHERE email = 'test@example.com';

-- 使用EXPLAIN ANALYZE实际执行
EXPLAIN ANALYZE SELECT * FROM users WHERE email = 'test@example.com';

-- 查看详细成本
EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) 
SELECT * FROM users WHERE email = 'test@example.com';
```

### 执行计划解读

| 关键指标 | 说明 | 优化建议 |
|----------|------|----------|
| Seq Scan | 全表扫描 | 添加索引 |
| Index Scan | 索引扫描 | 正常 |
| Bitmap Scan | 位图扫描 | 大量数据时正常 |
| Nested Loop | 嵌套循环连接 | 小数据集正常 |
| Hash Join | 哈希连接 | 大数据集更高效 |
| Merge Join | 合并连接 | 已排序数据高效 |

### 优化技巧

**1. 避免SELECT ***

```sql
-- ❌ 不推荐
SELECT * FROM users WHERE id = 1;

-- ✅ 推荐
SELECT id, name, email FROM users WHERE id = 1;
```

**2. 使用LIMIT**

```sql
-- ✅ 分页查询
SELECT * FROM orders 
WHERE user_id = 123 
ORDER BY created_at DESC 
LIMIT 20 OFFSET 0;

-- ✅ 使用游标分页(更高效)
SELECT * FROM orders 
WHERE user_id = 123 AND id < :last_id
ORDER BY id DESC 
LIMIT 20;
```

**3. 避免函数操作索引列**

```sql
-- ❌ 不使用索引
SELECT * FROM users WHERE LOWER(email) = 'test@example.com';

-- ✅ 使用表达式索引或修改查询
-- 方法1: 创建表达式索引
CREATE INDEX idx_users_lower_email ON users(LOWER(email));

-- 方法2: 修改查询
SELECT * FROM users WHERE email = 'TEST@EXAMPLE.COM' COLLATE "C";
```

**4. 避免隐式类型转换**

```sql
-- ❌ 隐式转换，不使用索引
SELECT * FROM users WHERE id = '123'; -- id是整数

-- ✅ 显式类型
SELECT * FROM users WHERE id = 123;
```

**5. 使用JOIN代替子查询**

```sql
-- ❌ 子查询可能低效
SELECT * FROM orders 
WHERE user_id IN (SELECT id FROM users WHERE is_active = true);

-- ✅ JOIN通常更高效
SELECT o.* FROM orders o
JOIN users u ON o.user_id = u.id
WHERE u.is_active = true;
```

**6. 批量操作**

```sql
-- ❌ 单条插入
INSERT INTO users (name) VALUES ('Alice');
INSERT INTO users (name) VALUES ('Bob');
INSERT INTO users (name) VALUES ('Charlie');

-- ✅ 批量插入
INSERT INTO users (name) VALUES ('Alice'), ('Bob'), ('Charlie');

-- ✅ 使用COPY (PostgreSQL)
COPY users (name, email) FROM '/path/to/data.csv' CSV;
```

**7. 使用UPSERT**

```sql
-- PostgreSQL
INSERT INTO users (id, name, email)
VALUES (1, 'Alice', 'alice@example.com')
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    email = EXCLUDED.email;

-- MySQL
INSERT INTO users (id, name, email)
VALUES (1, 'Alice', 'alice@example.com')
ON DUPLICATE KEY UPDATE
    name = VALUES(name),
    email = VALUES(email);
```

**8. 优化COUNT查询**

```sql
-- ❌ 全表COUNT
SELECT COUNT(*) FROM orders WHERE status = 'pending';

-- ✅ 使用估计值
SELECT reltuples::bigint FROM pg_class WHERE relname = 'orders';

-- ✅ 维护计数表
CREATE TABLE order_counts (
    status VARCHAR(20) PRIMARY KEY,
    count BIGINT
);
```

### 慢查询分析

```sql
-- PostgreSQL慢查询配置
ALTER SYSTEM SET log_min_duration_statement = 1000; -- 记录超过1秒的查询
SELECT pg_reload_conf();

-- 查看慢查询
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    max_time
FROM pg_stat_statements
ORDER BY total_time DESC
LIMIT 10;
```

---

## 迁移管理

### 迁移文件命名

```
migrations/
├── 20260417000001_create_users_table.sql
├── 20260417000002_create_orders_table.sql
├── 20260417000003_add_user_status.sql
└── 20260417000004_create_index_orders_user.sql
```

**命名规则**: `{timestamp}_{description}.sql`

### 迁移文件结构

```sql
-- migrations/20260417000001_create_users_table.sql

-- UP: 应用迁移
-- +migrate Up
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    name VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);

-- DOWN: 回滚迁移
-- +migrate Down
DROP INDEX IF EXISTS idx_users_email;
DROP TABLE IF EXISTS users;
```

### 迁移最佳实践

**1. 可逆性**

```sql
-- ✅ 每个迁移都应该可以回滚
-- UP
ALTER TABLE users ADD COLUMN phone VARCHAR(20);

-- DOWN
ALTER TABLE users DROP COLUMN phone;
```

**2. 原子性**

```sql
-- ✅ 使用事务包装
BEGIN;

ALTER TABLE users ADD COLUMN phone VARCHAR(20);
UPDATE users SET phone = 'N/A' WHERE phone IS NULL;

COMMIT;

-- 如果失败会自动回滚
```

**3. 幂等性**

```sql
-- ✅ 使用IF EXISTS/IF NOT EXISTS
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY
);

DROP TABLE IF EXISTS old_users;

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
```

**4. 小步迁移**

```sql
-- ❌ 大迁移: 一次性做太多
ALTER TABLE users ADD COLUMN phone VARCHAR(20);
ALTER TABLE users ADD COLUMN address TEXT;
ALTER TABLE users ADD COLUMN city VARCHAR(100);
CREATE INDEX idx_users_phone ON users(phone);
CREATE INDEX idx_users_city ON users(city);

-- ✅ 小迁移: 分步执行
-- 迁移1: 添加phone字段
ALTER TABLE users ADD COLUMN phone VARCHAR(20);

-- 迁移2: 添加address字段
ALTER TABLE users ADD COLUMN address TEXT;

-- 迁移3: 创建索引
CREATE INDEX CONCURRENTLY idx_users_phone ON users(phone);
```

**5. 大表迁移**

```sql
-- ✅ 分批更新大表
DO $$
DECLARE
    batch_size INT := 10000;
    updated INT;
BEGIN
    LOOP
        UPDATE users 
        SET status = 'active' 
        WHERE status IS NULL 
          AND id IN (
              SELECT id FROM users 
              WHERE status IS NULL 
              LIMIT batch_size
          );
        
        GET DIAGNOSTICS updated = ROW_COUNT;
        EXIT WHEN updated = 0;
        
        COMMIT;
    END LOOP;
END $$;

-- ✅ 使用CONCURRENTLY创建索引
CREATE INDEX CONCURRENTLY idx_users_email ON users(email);
```

### 数据迁移脚本

```sql
-- 数据迁移示例: 合并重复用户

BEGIN;

-- 1. 创建临时表存储重复数据
CREATE TEMP TABLE duplicate_users AS
SELECT email, array_agg(id) as ids
FROM users
GROUP BY email
HAVING COUNT(*) > 1;

-- 2. 更新关联数据
UPDATE orders o
SET user_id = du.ids[1]
FROM duplicate_users du
WHERE o.user_id = ANY(du.ids[2:]);

-- 3. 删除重复用户
DELETE FROM users u
WHERE id IN (
    SELECT unnest(ids[2:])
    FROM duplicate_users
);

-- 4. 添加唯一约束
ALTER TABLE users ADD CONSTRAINT uq_users_email UNIQUE (email);

COMMIT;
```

### 迁移工具配置

```yaml
# .dbconfig.yml (golang-migrate)
development:
  driver: postgres
  open: host=localhost port=5432 user=dev password=dev dbname=myapp sslmode=disable

production:
  driver: postgres
  open: $DATABASE_URL
```

```javascript
// Knex迁移配置
module.exports = {
  client: 'postgresql',
  connection: {
    host: process.env.DB_HOST,
    database: process.env.DB_NAME,
    user: process.env.DB_USER,
    password: process.env.DB_PASSWORD
  },
  migrations: {
    directory: './migrations',
    tableName: 'migrations'
  }
};
```

---

## 性能监控

### 关键指标

| 指标 | 说明 | 告警阈值 |
|------|------|----------|
| 连接数 | 当前连接数 | >80%最大连接 |
| 查询时间 | 平均查询时间 | >100ms |
| 慢查询 | 慢查询数量 | >10/分钟 |
| 缓存命中率 | Buffer命中率 | <95% |
| 死锁 | 死锁次数 | >0 |
| 表膨胀 | 表空间浪费 | >20% |

### 监控查询

```sql
-- 当前活动连接
SELECT 
    pid,
    usename,
    application_name,
    state,
    query,
    query_start
FROM pg_stat_activity
WHERE state = 'active';

-- 表统计信息
SELECT 
    schemaname,
    tablename,
    seq_scan,
    seq_tup_read,
    idx_scan,
    idx_tup_fetch
FROM pg_stat_user_tables
ORDER BY seq_tup_read DESC;

-- 索引使用率
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
FROM pg_stat_user_indexes
ORDER BY idx_scan ASC;

-- 表大小
SELECT 
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) AS table_size,
    pg_size_pretty(pg_indexes_size(schemaname||'.'||tablename)) AS index_size
FROM pg_tables
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

---

## 参考资料

- [PostgreSQL Documentation](https://www.postgresql.org/docs/current/index.html)
- [Use The Index, Luke](https://use-the-index-luke.com/)
- [PostgreSQL Performance Optimization](https://wiki.postgresql.org/wiki/Performance_Optimization)
- [Database Migration Best Practices](https://github.com/golang-migrate/migrate)

---

> 本文档由 Multi-Agent SDD/TDD Orchestrator 维护 | 最后更新: 2026-04-17
