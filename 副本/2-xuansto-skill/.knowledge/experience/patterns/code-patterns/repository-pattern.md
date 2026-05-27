---
id: "KP-EXP-PAT-001"
type: "success-pattern"
category: "architecture"
tags: ["仓储模式", "Repository", "数据访问层", "解耦", "依赖倒置", "DDD", "领域驱动设计"]
version: "1.0.0"
created: "2026-04-28T10:00:00Z"
updated: "2026-04-28T10:00:00Z"
source: "auto_precipitation"
confidence: 0.90
last_validated: "2026-04-28T10:00:00Z"
success_count: 0
failure_count: 0
trigger: "pattern_validated"
references:
  - id: "KP-GEN-001"
    relation: "implements"
  - id: "KP-EXP-ERR-001"
    relation: "prevents"
---

# 仓储模式 (Repository Pattern)

## 模式描述

仓储模式在领域层和数据访问层之间引入抽象层，将数据持久化细节封装在仓储接口背后。领域层通过仓储接口操作数据，无需关心底层是关系数据库、文档数据库还是内存存储。这是依赖倒置原则（DIP）的典型应用。

### 核心价值

| 价值 | 说明 |
|------|------|
| **解耦** | 领域逻辑与数据访问实现分离 |
| **可测试** | 可用内存仓储替代真实数据库进行单元测试 |
| **可替换** | 切换数据库只需实现新的仓储类 |
| **统一接口** | 不同实体的数据访问遵循一致的接口约定 |

### 架构位置

```
┌─────────────────────────────────────────────┐
│              领域层 (Domain)                  │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐     │
│  │ Entity  │  │ Service │  │  Repo   │     │
│  │         │  │         │  │Interface│     │
│  └─────────┘  └────┬────┘  └────┬────┘     │
│                    │             │           │
├────────────────────┼─────────────┼───────────┤
│              基础设施层 (Infrastructure)      │
│                    │             │           │
│                    ▼             ▼           │
│             ┌──────────────────────┐         │
│             │  Repository Impl     │         │
│             │  (PostgreSQL/Mongo)  │         │
│             └──────────────────────┘         │
└─────────────────────────────────────────────┘
```

---

## Python 实现

### 领域实体

```python
from dataclasses import dataclass
from datetime import datetime

@dataclass
class User:
    id: str
    name: str
    email: str
    created_at: datetime
    is_active: bool = True
```

### 仓储接口

```python
from abc import ABC, abstractmethod
from typing import Optional

class UserRepository(ABC):
    @abstractmethod
    async def find_by_id(self, user_id: str) -> Optional[User]:
        pass

    @abstractmethod
    async def find_by_email(self, email: str) -> Optional[User]:
        pass

    @abstractmethod
    async def save(self, user: User) -> User:
        pass

    @abstractmethod
    async def delete(self, user_id: str) -> bool:
        pass

    @abstractmethod
    async def find_active_users(self, limit: int = 20, offset: int = 0) -> list[User]:
        pass
```

### PostgreSQL 实现

```python
import asyncpg
from typing import Optional

class PostgresUserRepository(UserRepository):
    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    async def find_by_id(self, user_id: str) -> Optional[User]:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id, name, email, created_at, is_active "
                "FROM users WHERE id = $1",
                user_id,
            )
        if row is None:
            return None
        return User(
            id=row["id"],
            name=row["name"],
            email=row["email"],
            created_at=row["created_at"],
            is_active=row["is_active"],
        )

    async def find_by_email(self, email: str) -> Optional[User]:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id, name, email, created_at, is_active "
                "FROM users WHERE email = $1",
                email,
            )
        if row is None:
            return None
        return User(
            id=row["id"],
            name=row["name"],
            email=row["email"],
            created_at=row["created_at"],
            is_active=row["is_active"],
        )

    async def save(self, user: User) -> User:
        async with self._pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO users (id, name, email, created_at, is_active) "
                "VALUES ($1, $2, $3, $4, $5) "
                "ON CONFLICT (id) DO UPDATE SET name=$2, email=$3, is_active=$5",
                user.id, user.name, user.email, user.created_at, user.is_active,
            )
        return user

    async def delete(self, user_id: str) -> bool:
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM users WHERE id = $1", user_id
            )
        return result == "DELETE 1"

    async def find_active_users(self, limit: int = 20, offset: int = 0) -> list[User]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT id, name, email, created_at, is_active "
                "FROM users WHERE is_active = true "
                "ORDER BY created_at DESC LIMIT $1 OFFSET $2",
                limit, offset,
            )
        return [
            User(
                id=r["id"], name=r["name"], email=r["email"],
                created_at=r["created_at"], is_active=r["is_active"],
            )
            for r in rows
        ]
```

### 内存实现（测试用）

```python
class InMemoryUserRepository(UserRepository):
    def __init__(self):
        self._store: dict[str, User] = {}

    async def find_by_id(self, user_id: str) -> Optional[User]:
        return self._store.get(user_id)

    async def find_by_email(self, email: str) -> Optional[User]:
        for user in self._store.values():
            if user.email == email:
                return user
        return None

    async def save(self, user: User) -> User:
        self._store[user.id] = user
        return user

    async def delete(self, user_id: str) -> bool:
        return self._store.pop(user_id, None) is not None

    async def find_active_users(self, limit: int = 20, offset: int = 0) -> list[User]:
        active = [u for u in self._store.values() if u.is_active]
        return active[offset : offset + limit]
```

---

## TypeScript 实现

### 仓储接口

```typescript
interface User {
  id: string;
  name: string;
  email: string;
  createdAt: Date;
  isActive: boolean;
}

interface UserRepository {
  findById(userId: string): Promise<User | null>;
  findByEmail(email: string): Promise<User | null>;
  save(user: User): Promise<User>;
  delete(userId: string): Promise<boolean>;
  findActiveUsers(limit?: number, offset?: number): Promise<User[]>;
}
```

### TypeORM 实现

```typescript
import { DataSource, Repository } from "typeorm";
import { UserEntity } from "./entities/user.entity";

class TypeOrmUserRepository implements UserRepository {
  private readonly repo: Repository<UserEntity>;

  constructor(dataSource: DataSource) {
    this.repo = dataSource.getRepository(UserEntity);
  }

  async findById(userId: string): Promise<User | null> {
    const entity = await this.repo.findOne({ where: { id: userId } });
    return entity ? this.toDomain(entity) : null;
  }

  async findByEmail(email: string): Promise<User | null> {
    const entity = await this.repo.findOne({ where: { email } });
    return entity ? this.toDomain(entity) : null;
  }

  async save(user: User): Promise<User> {
    await this.repo.save(this.toEntity(user));
    return user;
  }

  async delete(userId: string): Promise<boolean> {
    const result = await this.repo.delete(userId);
    return (result.affected ?? 0) > 0;
  }

  async findActiveUsers(limit = 20, offset = 0): Promise<User[]> {
    const entities = await this.repo.find({
      where: { isActive: true },
      order: { createdAt: "DESC" },
      take: limit,
      skip: offset,
    });
    return entities.map(this.toDomain);
  }

  private toDomain(entity: UserEntity): User {
    return {
      id: entity.id,
      name: entity.name,
      email: entity.email,
      createdAt: entity.createdAt,
      isActive: entity.isActive,
    };
  }

  private toEntity(user: User): Partial<UserEntity> {
    return {
      id: user.id,
      name: user.name,
      email: user.email,
      createdAt: user.createdAt,
      isActive: user.isActive,
    };
  }
}
```

---

## 适用场景

| 场景 | 说明 |
|------|------|
| 领域驱动设计 | 聚合根需要通过仓储访问，保持领域模型纯净 |
| 单元测试 | 使用内存仓储替代真实数据库，测试速度快且隔离 |
| 多数据源 | 同一接口支持 PostgreSQL、MongoDB、Redis 等不同实现 |
| 数据库迁移 | 从一个数据库迁移到另一个，只需替换仓储实现 |
| CQRS 架构 | 读写分离，命令和查询使用不同仓储 |

## 注意事项

- 仓储接口应属于领域层，实现在基础设施层
- 仓储方法应返回领域对象而非数据传输对象（DTO）
- 避免在仓储接口中暴露查询构建器等 ORM 特定 API
- 复杂查询考虑使用规约模式（Specification Pattern）
- 每个聚合根对应一个仓储，而非每个实体

## 相关知识

- [KP-GEN-001] SOLID 设计原则 — 依赖倒置原则的典型应用
- [KP-EXP-ERR-001] 数据库连接超时 — 仓储模式中的连接管理
- [KP-EXP-PAT-002] 错误处理中间件 — 仓储层错误的统一处理
