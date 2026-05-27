---
id: "KP-GEN-002"
type: "paradigm"
category: "functional"
tags: ["函数式编程", "纯函数", "不可变性", "高阶函数", "组合", "柯里化", "Monad"]
version: "1.0.0"
created: "2026-04-28T10:00:00Z"
updated: "2026-04-28T10:00:00Z"
source: "Structure and Interpretation of Computer Programs / 社区实践总结"
confidence: 0.92
last_validated: "2026-04-28T10:00:00Z"
success_count: 0
failure_count: 0
references:
  - id: "KP-GEN-001"
    relation: "complements"
  - id: "KP-GEN-010"
    relation: "extends"
---

# 函数式编程原则

## 概述

函数式编程（Functional Programming, FP）是一种以数学函数为构建块的编程范式。其核心思想是将计算视为函数求值，避免状态变化和可变数据。FP 与面向对象编程互补，在现代软件开发中广泛应用。

| 核心概念 | 说明 |
|---------|------|
| 纯函数 | 相同输入始终产生相同输出，无副作用 |
| 不可变性 | 数据创建后不可修改，变更通过创建新副本实现 |
| 高阶函数 | 接受函数作为参数或返回函数的函数 |
| 函数组合 | 将简单函数组合为复杂功能 |
| 柯里化 | 将多参数函数转换为一系列单参数函数 |

---

## 纯函数 (Pure Functions)

纯函数是函数式编程的基石。它满足两个条件：1) 相同输入始终返回相同输出；2) 不产生可观察的副作用。

### Python 示例

```python
def calculate_discount(price: float, rate: float) -> float:
    return price * (1 - rate)

def format_currency(amount: float) -> str:
    return f"¥{amount:.2f}"

discounted = calculate_discount(100.0, 0.2)
result = format_currency(discounted)
```

### TypeScript 示例

```typescript
const calculateDiscount = (price: number, rate: number): number =>
  price * (1 - rate);

const formatCurrency = (amount: number): string =>
  `¥${amount.toFixed(2)}`;

const discounted = calculateDiscount(100, 0.2);
const result = formatCurrency(discounted);
```

---

## 不可变性 (Immutability)

不可变数据一旦创建就不能被修改。所有变更操作都返回新的数据结构，而非修改原始数据。

### Python 示例

```python
from dataclasses import dataclass, replace
from typing import FrozenSet

@dataclass(frozen=True)
class ShoppingCart:
    items: FrozenSet[str] = frozenset()

    def add_item(self, item: str) -> "ShoppingCart":
        return replace(self, items=self.items | {item})

    def remove_item(self, item: str) -> "ShoppingCart":
        return replace(self, items=self.items - {item})

cart = ShoppingCart()
cart_with_apple = cart.add_item("苹果")
cart_with_banana = cart_with_apple.add_item("香蕉")
```

### TypeScript 示例

```typescript
interface ReadonlyCart {
  readonly items: ReadonlySet<string>;
}

const createCart = (): ReadonlyCart => ({
  items: new Set<string>(),
});

const addItem = (cart: ReadonlyCart, item: string): ReadonlyCart => ({
  items: new Set([...cart.items, item]),
});

const removeItem = (cart: ReadonlyCart, item: string): ReadonlyCart => ({
  items: new Set([...cart.items].filter((i) => i !== item)),
});

const cart = createCart();
const cartWithApple = addItem(cart, "苹果");
const cartWithBanana = addItem(cartWithApple, "香蕉");
```

---

## 高阶函数 (Higher-Order Functions)

高阶函数接受函数作为参数或返回函数，是函数式编程的核心组合工具。

### Python 示例

```python
from typing import Callable, TypeVar

T = TypeVar("T")
R = TypeVar("R")

def map_list(fn: Callable[[T], R], items: list[T]) -> list[R]:
    return [fn(item) for item in items]

def filter_list(fn: Callable[[T], bool], items: list[T]) -> list[T]:
    return [item for item in items if fn(item)]

def compose(f: Callable, g: Callable) -> Callable:
    return lambda x: f(g(x))

double = lambda x: x * 2
increment = lambda x: x + 1
double_then_increment = compose(increment, double)

numbers = [1, 2, 3, 4, 5]
doubled = map_list(double, numbers)
evens = filter_list(lambda x: x % 2 == 0, numbers)
result = double_then_increment(5)
```

### TypeScript 示例

```typescript
const mapArray = <T, R>(fn: (x: T) => R, items: T[]): R[] =>
  items.map(fn);

const filterArray = <T>(fn: (x: T) => boolean, items: T[]): T[] =>
  items.filter(fn);

const compose = <A, B, C>(f: (x: B) => C, g: (x: A) => B) =>
  (x: A): C => f(g(x));

const double = (x: number): number => x * 2;
const increment = (x: number): number => x + 1;
const doubleThenIncrement = compose(increment, double);

const numbers = [1, 2, 3, 4, 5];
const doubled = mapArray(double, numbers);
const evens = filterArray((x) => x % 2 === 0, numbers);
const result = doubleThenIncrement(5);
```

---

## 函数组合 (Function Composition)

函数组合是将多个简单函数串联成复杂功能的技术，数据像管道一样流经各函数。

### Python 示例

```python
from functools import reduce
from typing import Callable, TypeVar

T = TypeVar("T")

def pipe(*functions: Callable[[T], T]) -> Callable[[T], T]:
    return reduce(lambda f, g: lambda x: g(f(x)), functions)

trim = lambda s: s.strip()
lower = lambda s: s.lower()
prefix = lambda s: f"user_{s}"

normalize_username = pipe(trim, lower, prefix)

print(normalize_username("  Alice  "))
```

### TypeScript 示例

```typescript
const pipe =
  <T>(...fns: Array<(x: T) => T>) =>
  (x: T): T =>
    fns.reduce((v, f) => f(v), x);

const trim = (s: string): string => s.trim();
const lower = (s: string): string => s.toLowerCase();
const prefix = (s: string): string => `user_${s}`;

const normalizeUsername = pipe(trim, lower, prefix);

console.log(normalizeUsername("  Alice  "));
```

---

## 柯里化 (Currying)

柯里化将接受多个参数的函数转换为一系列接受单一参数的函数，便于部分应用和函数复用。

### Python 示例

```python
from functools import partial

def multiply(a: float, b: float) -> float:
    return a * b

double = partial(multiply, 2)
triple = partial(multiply, 3)

print(double(5))
print(triple(5))
```

### TypeScript 示例

```typescript
const multiply = (a: number) => (b: number): number => a * b;

const double = multiply(2);
const triple = multiply(3);

console.log(double(5));
console.log(triple(5));
```

---

## 应用注意事项

- 纯函数虽好，但现实中的 I/O 操作必然有副作用，应将副作用推至程序边界
- 不可变性在频繁更新场景下可能产生性能开销，可考虑结构共享（如 Immer）
- 过度使用高阶函数和组合可能降低代码可读性，需平衡简洁与清晰
- 柯里化在 TypeScript 中天然支持，在 Python 中可通过 `functools.partial` 实现
- 函数式编程与面向对象并非对立，混合使用往往效果最佳

## 相关知识

- [KP-GEN-001] SOLID 设计原则 — 与函数式编程互补的面向对象原则
- [KP-GEN-010] 观察者模式 — 函数式响应式编程的基础
- [KP-EXP-PAT-002] 错误处理中间件 — 函数组合在中间件中的应用
