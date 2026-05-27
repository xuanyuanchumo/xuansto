---
id: "KP-EXP-PAT-REPO-001"
type: "pattern"
category: "architecture"
tags: ["Repository模式", "数据访问", "ORM", "抽象层", "TypeORM", "SQLAlchemy"]
version: "1.0.0"
confidence: 0.90
---

## Repository 模式实践 (置信度: 0.90 | 技术栈: TypeORM/SQLAlchemy)

### 现象
业务逻辑直接操作 ORM 模型，切换数据库需改动大量业务代码，测试时无法 Mock 数据层。

### 根因
业务层与数据访问层耦合，缺少抽象隔离，ORM 查询散布在 Service 中。

### 解决方案

```typescript
interface UserRepository {
  findById(id: string): Promise<User | null>;
  save(user: User): Promise<void>;
}
class TypeOrmUserRepository implements UserRepository {
  constructor(private repo: Repository<UserEntity>) {}
  async findById(id: string) { return this.repo.findOne({ where: { id } }); }
  async save(user: User) { await this.repo.save(this.toEntity(user)); }
}
```

```python
class UserRepository(ABC):
    @abstractmethod
    async def find_by_id(self, user_id: str) -> User | None: ...

class SqlAlchemyUserRepository(UserRepository):
    async def find_by_id(self, user_id: str) -> User | None:
        row = await self.session.execute(select(UserModel).where(UserModel.id == user_id))
        return row.scalar_one_or_none()
```

### 验证
业务层测试使用 Mock Repository，无需真实数据库即可验证逻辑。
