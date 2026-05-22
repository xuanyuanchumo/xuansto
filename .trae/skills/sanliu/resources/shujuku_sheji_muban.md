---
name: shujuku_sheji_muban
description: 数据库设计模板，包含 ER 图设计和表结构设计规范。
---
# 数据库设计模板

## ER 图设计原则

### 实体设计
- 每个实体对应一张表
- 实体属性对应表字段
- 主键唯一标识实体

### 关系设计
- 一对一：外键放在任意一方
- 一对多：外键放在多方
- 多对多：创建关联表

## 表结构设计规范

### 基础字段
- id：主键，自增或 UUID
- created_at：创建时间
- updated_at：更新时间
- deleted_at：软删除时间（可选）

### 字段类型选择
- 整数：INT, BIGINT
- 字符串：VARCHAR(n), TEXT
- 时间：TIMESTAMP, DATETIME
- 布尔：BOOLEAN
- JSON：JSON, JSONB

### 索引设计
- 主键索引：自动创建
- 唯一索引：唯一约束字段
- 普通索引：常用查询字段
- 复合索引：多字段组合查询

## 表结构模板

```sql
CREATE TABLE example (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```
