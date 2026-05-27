---
id: "KP-EXP-ERR-002"
type: "error-solution"
severity: "medium"
category: "coding"
tags: ["空指针", "NullPointerException", "None", "undefined", "可选类型", "防御性编程"]
version: "1.0.0"
confidence: 0.95
occurrences: 3
---

## 空指针异常 (置信度: 0.95 | 技术栈: Python/TypeScript/Java)

### 现象
运行时访问 null/undefined/None 的属性：`Cannot read properties of undefined (reading 'name')`、`AttributeError: 'NoneType' object has no attribute`。

### 根因
链式属性访问未做空值检查、集合操作返回空结果未处理、异步操作未处理 null 返回、对象解构时字段缺失。

### 解决方案

```typescript
function getCity(user: User | undefined): string {
  return user?.address?.city ?? "未知";
}
```

```python
def get_city(user: dict | None) -> str:
    return (user or {}).get("address", {}).get("city", "未知")
```

```typescript
type Result<T, E> = { ok: true; value: T } | { ok: false; error: E };
function findUser(id: string): Result<User, string> {
  const user = db.getUser(id);
  return user ? { ok: true, value: user } : { ok: false, error: "用户不存在" };
}
```

### 验证
启用 TypeScript strictNullChecks，Python 使用 Optional 类型注解。
