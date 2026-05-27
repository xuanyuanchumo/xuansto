---
id: "KP-EXP-ERR-002"
type: "error-solution"
severity: "medium"
category: "coding"
tags: ["空指针", "NullPointerException", "None", "undefined", "可选类型", "防御性编程"]
version: "1.0.0"
created: "2026-04-28T10:00:00Z"
updated: "2026-04-28T10:00:00Z"
source: "auto_precipitation"
confidence: 0.95
last_validated: "2026-04-28T10:00:00Z"
success_count: 0
failure_count: 0
occurrences: 3
trigger: "bug_fix_completed"
references:
  - id: "KP-GEN-001"
    relation: "complies"
  - id: "KP-EXP-PAT-002"
    relation: "extends"
---

# 空指针异常模式

## 错误现象

运行时访问 `null` / `undefined` / `None` 值的属性或方法，导致程序崩溃：

```python
# Python
AttributeError: 'NoneType' object has no attribute 'name'

# TypeScript
TypeError: Cannot read properties of undefined (reading 'name')
TypeError: Cannot read properties of null (reading 'name')

# Java
java.lang.NullPointerException
```

### 典型特征

- 错误堆栈指向属性访问或方法调用行
- 涉及链式属性访问（如 `a.b.c.d`）
- 多发生在边界条件：空查询结果、缺失字段、未初始化对象

---

## 根因分析

### 1. 链式属性访问未做空值检查

```python
user = get_user(user_id)
print(user.address.city)
```

当 `user` 为 `None` 或 `user.address` 为 `None` 时崩溃。

### 2. 集合操作返回空结果

```python
first_item = items[0]
```

当 `items` 为空列表时抛出 `IndexError`。

### 3. 异步操作未处理空值

```typescript
const user = await fetchUser(userId);
console.log(user.name);
```

当 API 返回 `null` 时崩溃。

### 4. 对象解构时字段缺失

```typescript
const { name, email } = response.data;
```

当 `response.data` 为 `undefined` 时崩溃。

---

## 解决方案

### 1. 可选链与空值合并

#### Python

```python
from typing import Optional

def get_city(user: Optional[dict]) -> str:
    return (user or {}).get("address", {}).get("city", "未知")

def safe_get(data: dict, *keys, default=None):
    result = data
    for key in keys:
        if isinstance(result, dict):
            result = result.get(key)
        else:
            return default
    return result if result is not None else default

city = safe_get(user_dict, "address", "city", default="未知")
```

#### TypeScript

```typescript
interface User {
  name: string;
  address?: {
    city?: string;
  };
}

function getCity(user: User | undefined | null): string {
  return user?.address?.city ?? "未知";
}
```

### 2. 使用 Result/Maybe 模式

#### Python

```python
from dataclasses import dataclass
from typing import TypeVar, Generic, Optional

T = TypeVar("T")
E = TypeVar("E")

@dataclass
class Result(Generic[T, E]):
    value: Optional[T] = None
    error: Optional[E] = None

    @property
    def is_ok(self) -> bool:
        return self.error is None

    def unwrap(self) -> T:
        if self.error is not None:
            raise ValueError(f"Result 包含错误: {self.error}")
        return self.value

    def unwrap_or(self, default: T) -> T:
        return self.value if self.is_ok else default

def find_user(user_id: str) -> Result[dict, str]:
    user = db.get_user(user_id)
    if user is None:
        return Result(error="用户不存在")
    return Result(value=user)

result = find_user("u-001")
city = result.unwrap_or({}).get("address", {}).get("city", "未知")
```

#### TypeScript

```typescript
type Result<T, E> =
  | { ok: true; value: T }
  | { ok: false; error: E };

function findUser(userId: string): Result<User, string> {
  const user = db.getUser(userId);
  if (!user) {
    return { ok: false, error: "用户不存在" };
  }
  return { ok: true, value: user };
}

const result = findUser("u-001");
if (result.ok) {
  console.log(result.value.name);
} else {
  console.error(result.error);
}
```

### 3. 防御性编程模式

#### Python

```python
from typing import Optional

def process_order(order: Optional[dict]) -> dict:
    if order is None:
        return {"status": "error", "message": "订单不存在"}

    items = order.get("items") or []
    if not items:
        return {"status": "empty", "message": "订单无商品"}

    total = sum(item.get("price", 0) * item.get("quantity", 1) for item in items)
    return {"status": "success", "total": total}
```

#### TypeScript

```typescript
interface Order {
  items?: Array<{ price?: number; quantity?: number }>;
}

function processOrder(order: Order | undefined | null): {
  status: string;
  total?: number;
  message?: string;
} {
  if (!order) {
    return { status: "error", message: "订单不存在" };
  }

  const items = order.items ?? [];
  if (items.length === 0) {
    return { status: "empty", message: "订单无商品" };
  }

  const total = items.reduce(
    (sum, item) => sum + (item.price ?? 0) * (item.quantity ?? 1),
    0,
  );
  return { status: "success", total };
}
```

### 4. 类型系统防护

#### TypeScript 严格模式

```typescript
interface User {
  id: string;
  name: string;
  email: string | null;
}

interface UserWithProfile extends User {
  profile: {
    avatar: string;
    bio: string;
  };
}

function isUserWithProfile(user: User): user is UserWithProfile {
  return "profile" in user && user.profile !== undefined;
}

function displayUser(user: User): string {
  const email = user.email ?? "未设置邮箱";
  if (isUserWithProfile(user)) {
    return `${user.name} (${email}) - ${user.profile.bio}`;
  }
  return `${user.name} (${email})`;
}
```

---

## 预防措施

| 措施 | 说明 |
|------|------|
| 启用严格空值检查 | TypeScript `strictNullChecks`、Python `Optional` 类型注解 |
| 使用可选链 | `?.` 和 `??` 运算符处理链式访问 |
| Result 模式 | 用 `Result<T, E>` 替代异常和空值返回 |
| 防御性编程 | 函数入口处验证参数，提供默认值 |
| 类型收窄 | 使用类型守卫（Type Guard）收窄类型 |
| 代码审查 | 重点关注链式属性访问和隐式空值假设 |

## 相关知识

- [KP-GEN-001] SOLID 设计原则 — 接口隔离原则减少空值依赖
- [KP-EXP-PAT-002] 错误处理中间件 — 统一错误处理模式
