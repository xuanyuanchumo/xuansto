---
id: "KP-GEN-002"
type: "paradigm"
category: "functional"
tags: ["函数式编程", "纯函数", "不可变性", "高阶函数", "组合", "柯里化"]
version: "1.0.0"
confidence: 0.92
---

## 函数式编程原则 (版本: 1.0 | 适用: Python/TypeScript)

### 核心规则
- 纯函数：相同输入始终返回相同输出，无副作用
- 不可变性：数据创建后不可修改，变更通过创建新副本
- 高阶函数：接受函数作为参数或返回函数（map/filter/reduce）
- 函数组合：将简单函数串联为复杂功能（pipe/compose）
- 柯里化：多参数函数转换为一系列单参数函数，便于部分应用

### 代码示例

```typescript
const pipe = <T>(...fns: Array<(x: T) => T>) => (x: T): T =>
  fns.reduce((v, f) => f(v), x);

const trim = (s: string) => s.trim();
const lower = (s: string) => s.toLowerCase();
const prefix = (s: string) => `user_${s}`;

const normalizeUsername = pipe(trim, lower, prefix);
```

```python
from dataclasses import dataclass, replace
from functools import partial

@dataclass(frozen=True)
class Cart:
    items: frozenset = frozenset()
    def add(self, item: str) -> "Cart":
        return replace(self, items=self.items | {item})

double = partial(lambda a, b: a * b, 2)
```

### 反模式
- ❌ 纯函数中包含 I/O 副作用 — 应将副作用推至程序边界
- ❌ 频繁更新不可变数据导致性能问题 — 考虑结构共享（Immer）
- ❌ 过度使用高阶函数降低可读性 — 需平衡简洁与清晰
