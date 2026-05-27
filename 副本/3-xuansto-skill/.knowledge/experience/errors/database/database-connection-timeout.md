---
id: "KP-EXP-ERR-001"
type: "error-solution"
severity: "high"
category: "database"
tags: ["数据库", "连接超时", "连接池", "PostgreSQL", "MySQL", "重试", "超时配置"]
version: "1.0.0"
confidence: 0.98
occurrences: 3
---

## 数据库连接超时 (置信度: 0.98 | 技术栈: PostgreSQL/MySQL)

### 现象
应用运行一段时间后数据库操作超时：`too many clients already`、`connection timeout expired`，重启后暂时恢复。

### 根因
连接泄漏（获取连接后未释放）、连接池配置不当、长事务占用连接、数据库 max_connections 过低。

### 解决方案

```python
async def get_user(user_id: str):
    async with pool.acquire() as conn:
        return await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
```

```python
pool = await asyncpg.create_pool(
    dsn="postgresql://user:pass@localhost/db",
    min_size=5, max_size=20,
    command_timeout=60, acquire_timeout=30,
)
```

```typescript
const dataSource = new DataSource({
  type: "postgres", poolSize: 20,
  extra: { max: 20, min: 5, idleTimeoutMillis: 30000, connectionTimeoutMillis: 5000 },
});
```

### 验证
监控连接池使用率，设置告警阈值 > 80%。
