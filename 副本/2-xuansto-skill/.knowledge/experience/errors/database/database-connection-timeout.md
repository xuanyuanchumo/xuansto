---
id: "KP-EXP-ERR-001"
type: "error-solution"
severity: "high"
category: "database"
tags: ["数据库", "连接超时", "连接池", "PostgreSQL", "MySQL", "重试", "超时配置"]
version: "1.0.0"
created: "2026-04-28T10:00:00Z"
updated: "2026-04-28T10:00:00Z"
source: "auto_precipitation"
confidence: 0.98
last_validated: "2026-04-28T10:00:00Z"
success_count: 0
failure_count: 0
occurrences: 3
trigger: "bug_fix_completed"
references:
  - id: "KP-EXP-PAT-001"
    relation: "complies"
  - id: "KP-EXP-PAT-002"
    relation: "extends"
---

# 数据库连接超时错误

## 错误现象

应用在运行一段时间后，数据库操作开始超时，日志中出现以下错误：

```
# PostgreSQL
psycopg2.OperationalError: server closed the connection unexpectedly
FATAL: sorry, too many clients already
connection timeout expired

# MySQL
Error: ER_CON_COUNT_ERROR: Too many connections
Error: connect ETIMEDOUT

# TypeORM
QueryFailedError: connection timeout
```

### 典型特征

- 应用启动时正常，运行一段时间后开始出现超时
- 高并发场景下更容易触发
- 重启应用后暂时恢复，但问题会再次出现
- 数据库服务端连接数达到上限

---

## 根因分析

### 1. 连接泄漏

应用获取数据库连接后未正确释放，导致连接池耗尽。

```python
async def get_user_bad(user_id: str):
    conn = await pool.acquire()
    result = await conn.fetchrow(
        "SELECT * FROM users WHERE id = $1", user_id
    )
    return result
```

问题：如果 `fetchrow` 抛出异常，连接永远不会归还连接池。

### 2. 连接池配置不当

连接池大小、超时时间、空闲回收等参数未根据实际负载调优。

### 3. 长事务占用连接

事务执行时间过长，占用连接不释放。

### 4. 数据库服务端限制

`max_connections`（PostgreSQL）或 `max_connections`（MySQL）设置过低。

---

## 解决方案

### 1. 确保连接正确释放

#### Python (asyncpg)

```python
async def get_user(user_id: str):
    async with pool.acquire() as conn:
        result = await conn.fetchrow(
            "SELECT * FROM users WHERE id = $1", user_id
        )
        return result
```

#### TypeScript (TypeORM)

```typescript
async function getUser(userId: string): Promise<User | null> {
  const repository = dataSource.getRepository(User);
  return repository.findOne({ where: { id: userId } });
}
```

#### 手动连接管理（需确保释放）

```python
async def get_user_manual(user_id: str):
    conn = None
    try:
        conn = await pool.acquire()
        return await conn.fetchrow(
            "SELECT * FROM users WHERE id = $1", user_id
        )
    finally:
        if conn:
            await pool.release(conn)
```

### 2. 合理配置连接池

#### Python (asyncpg)

```python
import asyncpg

pool = await asyncpg.create_pool(
    dsn="postgresql://user:pass@localhost/db",
    min_size=5,
    max_size=20,
    max_inactive_connection_lifetime=300,
    command_timeout=60,
    acquire_timeout=30,
)
```

#### TypeScript (TypeORM)

```typescript
import { DataSource } from "typeorm";

const dataSource = new DataSource({
  type: "postgres",
  host: process.env.DB_HOST,
  port: 5432,
  username: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
  database: process.env.DB_NAME,
  poolSize: 20,
  extra: {
    max: 20,
    min: 5,
    idleTimeoutMillis: 30000,
    connectionTimeoutMillis: 5000,
  },
});
```

### 3. 实现重试机制

```python
import asyncio
from typing import TypeVar, Callable

T = TypeVar("T")

async def with_retry(
    operation: Callable[[], T],
    max_retries: int = 3,
    base_delay: float = 1.0,
    retryable_exceptions: tuple = (asyncpg.PostgresConnectionError,),
) -> T:
    last_error = None
    for attempt in range(max_retries):
        try:
            return await operation()
        except retryable_exceptions as e:
            last_error = e
            delay = base_delay * (2 ** attempt)
            await asyncio.sleep(delay)
    raise last_error
```

```typescript
async function withRetry<T>(
  operation: () => Promise<T>,
  maxRetries: number = 3,
  baseDelay: number = 1000,
): Promise<T> {
  let lastError: Error | null = null;
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await operation();
    } catch (error) {
      lastError = error as Error;
      const delay = baseDelay * Math.pow(2, attempt);
      await new Promise((resolve) => setTimeout(resolve, delay));
    }
  }
  throw lastError;
}
```

### 4. 监控连接池状态

```python
async def monitor_pool(pool: asyncpg.Pool):
    print(f"连接池状态:")
    print(f"  空闲连接: {pool.get_idle_size()}")
    print(f"  使用中连接: {pool.get_size() - pool.get_idle_size()}")
    print(f"  最大连接数: {pool.get_max_size()}")
```

---

## 预防措施

| 措施 | 说明 |
|------|------|
| 使用上下文管理器 | 确保连接在 `finally` 块中释放 |
| 合理配置连接池 | 根据并发量设置 `min_size`、`max_size`、`acquire_timeout` |
| 避免长事务 | 事务中不执行耗时操作（网络请求、文件 I/O） |
| 设置连接超时 | `command_timeout` 防止查询无限等待 |
| 实现重试机制 | 对瞬时故障自动重试，使用指数退避 |
| 监控连接池 | 定期检查连接池使用率，设置告警阈值 |
| 健康检查 | 实现数据库健康检查端点，及时发现连接问题 |

## 相关知识

- [KP-EXP-PAT-001] 仓储模式 — 数据库访问层的标准封装
- [KP-EXP-PAT-002] 错误处理中间件 — 统一的错误处理与重试策略
