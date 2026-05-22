---
id: oop-principles
type: knowledge
category: paradigms
tags: [OOP, SOLID, 封装, 继承, 多态, 设计原则]
version: 1.0.0
confidence: high
---

## 面向对象编程原则 (版本: 1.0 | 适用: OOP/通用)

### 核心规则
- 封装：将数据和操作绑定，通过访问修饰符控制可见性，隐藏实现细节
- 继承：子类复用父类，建立 is-a 关系；优先组合而非继承，避免深层继承链
- 多态：同一接口不同实现；编译时多态（重载）+ 运行时多态（重写）
- DRY：消除重复逻辑，提取公共抽象
- KISS：优先选择最简单的可行方案
- Law of Demeter：最少知识原则，对象应少了解其他对象内部结构

### 代码示例

```typescript
class UserRepository {
  constructor(private db: Database) {}
  async findById(id: string): Promise<User | null> {
    return this.db.query("SELECT * FROM users WHERE id = $1", [id]);
  }
}
```

### 反模式
- ❌ 继承层次超过 3 层 — 应改用组合模式
- ❌ 在类内部 new 具体实现 — 应通过构造函数注入依赖
- ❌ Tell Don't Ask 违反：询问对象状态后做决策 — 应告诉对象做什么
