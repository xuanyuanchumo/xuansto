---
name: shujuku_sheji
description: 数据库设计指导，包含ER图设计、表结构设计和性能优化指南。
---
# 数据库设计指导

## ER图设计方法

### 什么是ER图

实体关系图（Entity-Relationship Diagram）是描述现实世界概念模型的有效工具，用于数据库概念设计阶段。

### 基本元素

| 元素 | 符号 | 说明 |
|------|------|------|
| 实体 | 矩形 | 表示现实世界中可区分的事物 |
| 属性 | 椭圆 | 表示实体的特征或性质 |
| 关系 | 菱形 | 表示实体之间的联系 |
| 连线 | 直线 | 连接实体与属性、实体与关系 |

### 实体设计原则

1. **实体识别**
   - 识别业务中的核心对象
   - 每个实体应有唯一标识符（主键）
   - 实体名称使用名词，如：用户、订单、商品

2. **属性设计**
   - 属性应为原子值，不可再分
   - 避免冗余属性
   - 合理选择数据类型

3. **关系设计**
   - 一对一关系（1:1）：如用户-用户详情
   - 一对多关系（1:N）：如用户-订单
   - 多对多关系（M:N）：如学生-课程，需引入中间表

### ER图绘制步骤

```
1. 需求分析 → 确定系统边界和功能需求
2. 识别实体 → 找出所有需要存储的对象
3. 确定属性 → 为每个实体确定属性
4. 建立关系 → 分析实体间的联系
5. 确定基数 → 明确关系的数量约束
6. 绘制图形 → 使用工具绘制ER图
7. 优化调整 → 消除冗余，规范化处理
```

### 常用ER图工具

- MySQL Workbench
- draw.io
- Lucidchart
- PDMan
- PowerDesigner

---

## 表结构设计规范

### 命名规范

#### 表命名

| 规则 | 示例 | 说明 |
|------|------|------|
| 使用小写字母 | `user_order` | 避免大小写问题 |
| 使用下划线分隔 | `order_item` | 提高可读性 |
| 使用单数形式 | `user` 而非 `users` | 表示一个实体 |
| 添加业务前缀 | `sys_user`, `biz_order` | 区分业务模块 |
| 关联表命名 | `user_role` | 两个表名组合 |

#### 字段命名

| 规则 | 示例 | 说明 |
|------|------|------|
| 主键命名 | `id` 或 `表名_id` | 统一规范 |
| 外键命名 | `user_id` | 关联表名+_id |
| 布尔字段 | `is_deleted`, `has_permission` | 使用is/has前缀 |
| 时间字段 | `created_at`, `updated_at` | 使用_at后缀 |
| 金额字段 | `total_amount` | 避免使用price等模糊词 |

### 字段设计规范

#### 主键设计

```sql
-- 推荐使用自增ID或雪花ID
CREATE TABLE `user` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

-- 或使用UUID（分布式场景）
CREATE TABLE `order` (
  `id` VARCHAR(32) NOT NULL COMMENT '订单ID',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='订单表';
```

#### 必备字段

```sql
-- 每个表建议包含以下字段
`id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键',
`created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
`updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
`created_by` BIGINT UNSIGNED COMMENT '创建人',
`updated_by` BIGINT UNSIGNED COMMENT '更新人',
`is_deleted` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否删除：0-否，1-是',
`version` INT NOT NULL DEFAULT 0 COMMENT '乐观锁版本号'
```

#### 数据类型选择

| 数据类型 | 使用场景 | 示例 |
|----------|----------|------|
| TINYINT | 状态、标志位 | `status` TINYINT COMMENT '状态：0-禁用，1-启用' |
| SMALLINT | 小范围数值 | `age` SMALLINT COMMENT '年龄' |
| INT | 普通整数 | `count` INT COMMENT '数量' |
| BIGINT | 大整数、ID | `id` BIGINT COMMENT '主键' |
| DECIMAL | 精确小数、金额 | `amount` DECIMAL(18,2) COMMENT '金额' |
| VARCHAR | 可变长字符串 | `name` VARCHAR(50) COMMENT '姓名' |
| CHAR | 定长字符串 | `phone` CHAR(11) COMMENT '手机号' |
| TEXT | 大文本 | `content` TEXT COMMENT '内容' |
| DATETIME | 日期时间 | `created_at` DATETIME COMMENT '创建时间' |
| DATE | 日期 | `birth_date` DATE COMMENT '出生日期' |
| JSON | JSON数据 | `extra` JSON COMMENT '扩展信息' |

#### 字段约束

```sql
CREATE TABLE `product` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(100) NOT NULL COMMENT '商品名称',
  `sku` VARCHAR(50) NOT NULL COMMENT 'SKU编码',
  `price` DECIMAL(10,2) NOT NULL COMMENT '价格',
  `stock` INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '库存',
  `status` TINYINT NOT NULL DEFAULT 1 COMMENT '状态',
  
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_sku` (`sku`),
  CONSTRAINT `chk_price` CHECK (`price` >= 0),
  CONSTRAINT `chk_stock` CHECK (`stock` >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='商品表';
```

### 表设计原则

1. **第三范式（3NF）**
   - 消除非主键对主键的部分依赖
   - 消除非主键对主键的传递依赖

2. **适度反范式**
   - 高频查询场景可适当冗余
   - 减少JOIN操作提升性能

3. **字段数量控制**
   - 单表字段数建议不超过50个
   - 大字段考虑拆分到扩展表

4. **避免保留字**
   - 不要使用数据库保留字作为表名或字段名
   - 如必须使用，请用反引号包裹

---

## 索引设计

### 索引类型

| 类型 | 说明 | 使用场景 |
|------|------|----------|
| 主键索引 | 唯一标识记录 | 每个表必须有 |
| 唯一索引 | 字段值唯一 | 身份证、邮箱等 |
| 普通索引 | 加速查询 | WHERE条件字段 |
| 复合索引 | 多字段组合 | 多条件查询 |
| 全文索引 | 文本搜索 | 文章内容搜索 |
| 空间索引 | 地理位置查询 | 经纬度查询 |

### 索引设计原则

#### 最左前缀原则

```sql
-- 创建复合索引
CREATE INDEX idx_user_status_time ON `order` (user_id, status, created_at);

-- 可以命中索引的查询
WHERE user_id = 1
WHERE user_id = 1 AND status = 1
WHERE user_id = 1 AND status = 1 AND created_at > '2024-01-01'

-- 无法命中索引的查询
WHERE status = 1
WHERE created_at > '2024-01-01'
WHERE status = 1 AND created_at > '2024-01-01'
```

#### 选择性原则

```sql
-- 选择性高的字段适合建索引
-- 选择性 = DISTINCT值数量 / 总记录数

-- 高选择性（适合建索引）
SELECT COUNT(DISTINCT user_id) / COUNT(*) FROM `order`;  -- 0.8

-- 低选择性（不适合建索引）
SELECT COUNT(DISTINCT status) / COUNT(*) FROM `order`;   -- 0.001
```

#### 覆盖索引

```sql
-- 创建覆盖索引，避免回表
CREATE INDEX idx_user_order ON `order` (user_id, order_no, total_amount);

-- 查询只使用索引字段，无需回表
SELECT order_no, total_amount FROM `order` WHERE user_id = 1;
```

### 索引创建规范

```sql
-- 命名规范
-- 主键索引：PRIMARY
-- 唯一索引：uk_字段名
-- 普通索引：idx_字段名
-- 复合索引：idx_字段名1_字段名2

-- 创建索引示例
ALTER TABLE `user` ADD UNIQUE KEY `uk_email` (`email`);
ALTER TABLE `user` ADD INDEX `idx_name_phone` (`name`, `phone`);
ALTER TABLE `order` ADD INDEX `idx_user_status` (`user_id`, `status`);

-- 查看索引
SHOW INDEX FROM `user`;

-- 分析索引使用情况
EXPLAIN SELECT * FROM `user` WHERE email = 'test@example.com';
```

### 索引使用注意事项

1. **避免索引失效**
   - 避免在索引列上使用函数
   - 避免隐式类型转换
   - 避免使用 `!=` 或 `<>`
   - 避免使用 `OR` 连接非索引列

2. **索引数量控制**
   - 单表索引数建议不超过5个
   - 单个索引字段数不超过5个

3. **索引维护**
   - 定期分析索引使用率
   - 删除无用索引
   - 重建碎片化严重的索引

---

## 性能优化

### 查询优化

#### 避免SELECT *

```sql
-- 不推荐
SELECT * FROM `user` WHERE id = 1;

-- 推荐：只查询需要的字段
SELECT id, name, email FROM `user` WHERE id = 1;
```

#### 分页优化

```sql
-- 传统分页（数据量大时性能差）
SELECT * FROM `order` ORDER BY id LIMIT 10000, 20;

-- 优化方案1：使用子查询
SELECT * FROM `order` o 
JOIN (SELECT id FROM `order` ORDER BY id LIMIT 10000, 20) t 
ON o.id = t.id;

-- 优化方案2：使用游标（记住上一页最后一条记录ID）
SELECT * FROM `order` WHERE id > 10000 ORDER BY id LIMIT 20;
```

#### JOIN优化

```sql
-- 小表驱动大表
-- 小表 LEFT JOIN 大表 性能更好
SELECT o.*, u.name 
FROM (SELECT * FROM `order` WHERE user_id = 1) o
LEFT JOIN `user` u ON o.user_id = u.id;

-- JOIN字段建立索引
ALTER TABLE `order` ADD INDEX `idx_user_id` (`user_id`);
```

#### 子查询优化

```sql
-- 不推荐：子查询
SELECT * FROM `user` WHERE id IN (SELECT user_id FROM `order` WHERE status = 1);

-- 推荐：JOIN查询
SELECT DISTINCT u.* FROM `user` u
INNER JOIN `order` o ON u.id = o.user_id
WHERE o.status = 1;
```

### 表结构优化

#### 垂直拆分

```
┌─────────────────────────────────────────────────────────────┐
│                      原始用户表                              │
│  id, name, email, password, phone, avatar, intro, settings │
└─────────────────────────────────────────────────────────────┘
                            ↓ 垂直拆分
┌─────────────────────┐        ┌─────────────────────────────┐
│      用户基础表       │        │        用户详情表           │
│ id, name, email,    │  1:1   │ user_id, avatar, intro,    │
│ password, phone     │◄──────►│ settings                   │
└─────────────────────┘        └─────────────────────────────┘
```

#### 水平拆分

```
┌─────────────────────────────────────────────────────────────┐
│                      原始订单表                              │
│              id, user_id, amount, status, ...               │
└─────────────────────────────────────────────────────────────┘
                            ↓ 水平拆分
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   订单表_2024    │  │   订单表_2025    │  │   订单表_2026    │
│  2024年订单数据   │  │  2025年订单数据   │  │  2026年订单数据   │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

### 数据库配置优化

```sql
-- InnoDB缓冲池大小（建议设为物理内存的70%-80%）
innodb_buffer_pool_size = 4G

-- 日志文件大小
innodb_log_file_size = 512M

-- 连接数
max_connections = 1000

-- 查询缓存（MySQL 8.0已移除）
query_cache_size = 0

-- 慢查询日志
slow_query_log = ON
long_query_time = 2
```

### 性能监控

```sql
-- 查看慢查询
SHOW VARIABLES LIKE 'slow_query%';

-- 查看表状态
SHOW TABLE STATUS LIKE 'user';

-- 分析表
ANALYZE TABLE `user`;

-- 查看索引使用情况
SELECT * FROM sys.schema_index_statistics 
WHERE table_schema = 'your_database';

-- 查看未使用的索引
SELECT * FROM sys.schema_unused_indexes 
WHERE object_schema = 'your_database';
```

---

## 数据库安全

### 权限管理

```sql
-- 创建用户
CREATE USER 'app_user'@'%' IDENTIFIED BY 'strong_password_123!';

-- 授予权限（最小权限原则）
GRANT SELECT, INSERT, UPDATE ON mydb.* TO 'app_user'@'%';

-- 收回权限
REVOKE DELETE ON mydb.* FROM 'app_user'@'%';

-- 刷新权限
FLUSH PRIVILEGES;

-- 查看用户权限
SHOW GRANTS FOR 'app_user'@'%';
```

### SQL注入防护

```sql
-- 使用参数化查询（以Python为例）
-- 不安全的方式
cursor.execute(f"SELECT * FROM user WHERE name = '{name}'")

-- 安全的方式：参数化查询
cursor.execute("SELECT * FROM user WHERE name = %s", (name,))
```

### 敏感数据保护

```sql
-- 密码加密存储
-- 使用bcrypt、Argon2等安全哈希算法

-- 敏感字段加密
CREATE TABLE `user` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(50) NOT NULL,
  `id_card` VARCHAR(100) COMMENT '身份证号（加密存储）',
  `phone` VARCHAR(100) COMMENT '手机号（加密存储）',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 数据脱敏查询
SELECT 
  id,
  name,
  CONCAT(LEFT(id_card, 6), '********', RIGHT(id_card, 4)) AS id_card_masked,
  CONCAT(LEFT(phone, 3), '****', RIGHT(phone, 4)) AS phone_masked
FROM `user`;
```

### 备份策略

```bash
# 全量备份
mysqldump -u root -p --single-transaction --routines --triggers mydb > backup_full.sql

# 增量备份（开启binlog）
mysqlbinlog --start-datetime="2024-01-01 00:00:00" \
            --stop-datetime="2024-01-02 00:00:00" \
            /var/lib/mysql/mysql-bin.000001 > incremental.sql

# 定时备份脚本示例
# crontab -e
0 2 * * * /usr/bin/mysqldump -u root -p'password' mydb | gzip > /backup/mydb_$(date +\%Y\%m\%d).sql.gz
```

## 审计日志

```sql
-- 开启审计日志（MySQL Enterprise Edition）
-- 或使用开源审计插件

-- 自定义审计表
CREATE TABLE `audit_log` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT UNSIGNED COMMENT '操作用户',
  `action` VARCHAR(50) NOT NULL COMMENT '操作类型',
  `table_name` VARCHAR(50) COMMENT '表名',
  `record_id` BIGINT COMMENT '记录ID',
  `old_value` JSON COMMENT '旧值',
  `new_value` JSON COMMENT '新值',
  `ip_address` VARCHAR(50) COMMENT 'IP地址',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  INDEX `idx_user_time` (`user_id`, `created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='审计日志表';
```

---

## 最佳实践清单

### 设计阶段

- [ ] 完成ER图设计并评审
- [ ] 遵循命名规范
- [ ] 选择合适的数据类型
- [ ] 添加必要的字段注释
- [ ] 设计合理的主键和外键
- [ ] 考虑数据扩展性

### 开发阶段

- [ ] 创建必要的索引
- [ ] 编写高效的SQL语句
- [ ] 使用事务保证数据一致性
- [ ] 实现软删除机制
- [ ] 添加数据校验约束

### 运维阶段

- [ ] 配置数据库监控
- [ ] 定期备份数据
- [ ] 分析慢查询日志
- [ ] 定期优化表
- [ ] 审查用户权限
- [ ] 关注存储空间使用情况
