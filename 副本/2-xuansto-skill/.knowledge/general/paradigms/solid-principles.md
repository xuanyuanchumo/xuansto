---
id: "KP-GEN-001"
type: "paradigm"
category: "object-oriented"
tags: ["SOLID", "面向对象", "设计原则", "单一职责", "开闭原则", "依赖倒置", "接口隔离", "里氏替换"]
version: "1.0.0"
created: "2026-04-28T10:00:00Z"
updated: "2026-04-28T10:00:00Z"
source: "Robert C. Martin - Clean Architecture / 社区实践总结"
confidence: 0.95
last_validated: "2026-04-28T10:00:00Z"
success_count: 0
failure_count: 0
references:
  - id: "KP-GEN-002"
    relation: "complements"
  - id: "KP-GEN-010"
    relation: "implements"
---

# SOLID 设计原则

## 概述

SOLID 是面向对象设计的五大基本原则的首字母缩写，由 Robert C. Martin 提出。这些原则旨在提高软件的可维护性、可扩展性和可测试性，是构建健壮软件架构的基石。

| 原则 | 名称 | 核心思想 |
|------|------|---------|
| **S** | 单一职责原则 (SRP) | 一个类应该只有一个引起变化的原因 |
| **O** | 开闭原则 (OCP) | 对扩展开放，对修改关闭 |
| **L** | 里氏替换原则 (LSP) | 子类型必须能够替换其基类型 |
| **I** | 接口隔离原则 (ISP) | 客户端不应被迫依赖它不使用的接口 |
| **D** | 依赖倒置原则 (DIP) | 高层模块不应依赖低层模块，两者都应依赖抽象 |

---

## S - 单一职责原则 (Single Responsibility Principle)

一个类或模块应该只有一个引起它变化的原因。当需求变化时，只影响一个职责域。

### Python 示例

```python
class User:
    def __init__(self, name: str, email: str):
        self.name = name
        self.email = email

class UserRepository:
    def save(self, user: User) -> None:
        pass

    def find_by_email(self, email: str) -> User | None:
        pass

class UserNotifier:
    def send_welcome(self, user: User) -> None:
        print(f"欢迎 {user.name}，邮件已发送至 {user.email}")
```

### TypeScript 示例

```typescript
class User {
  constructor(
    public name: string,
    public email: string,
  ) {}
}

class UserRepository {
  async save(user: User): Promise<void> {}

  async findByEmail(email: string): Promise<User | null> {
    return null;
  }
}

class UserNotifier {
  sendWelcome(user: User): void {
    console.log(`欢迎 ${user.name}，邮件已发送至 ${user.email}`);
  }
}
```

---

## O - 开闭原则 (Open/Closed Principle)

软件实体应该对扩展开放，对修改关闭。通过抽象和多态实现行为扩展，而不修改已有代码。

### Python 示例

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class Discount:
    customer_type: str
    amount: float

class PricingStrategy(ABC):
    @abstractmethod
    def calculate(self, base_price: float) -> float:
        pass

class RegularPricing(PricingStrategy):
    def calculate(self, base_price: float) -> float:
        return base_price

class VIPPricing(PricingStrategy):
    def calculate(self, base_price: float) -> float:
        return base_price * 0.8

class PremiumPricing(PricingStrategy):
    def calculate(self, base_price: float) -> float:
        return base_price * 0.7

class PriceCalculator:
    def __init__(self, strategy: PricingStrategy):
        self.strategy = strategy

    def calculate(self, base_price: float) -> float:
        return self.strategy.calculate(base_price)
```

### TypeScript 示例

```typescript
interface PricingStrategy {
  calculate(basePrice: number): number;
}

class RegularPricing implements PricingStrategy {
  calculate(basePrice: number): number {
    return basePrice;
  }
}

class VIPPricing implements PricingStrategy {
  calculate(basePrice: number): number {
    return basePrice * 0.8;
  }
}

class PremiumPricing implements PricingStrategy {
  calculate(basePrice: number): number {
    return basePrice * 0.7;
  }
}

class PriceCalculator {
  constructor(private strategy: PricingStrategy) {}

  calculate(basePrice: number): number {
    return this.strategy.calculate(basePrice);
  }
}
```

---

## L - 里氏替换原则 (Liskov Substitution Principle)

子类型必须能够替换其基类型而不影响程序正确性。继承必须保证超类所拥有的性质在子类中仍然成立。

### Python 示例

```python
from abc import ABC, abstractmethod

class Bird(ABC):
    @abstractmethod
    def get_name(self) -> str:
        pass

class FlyingBird(Bird):
    @abstractmethod
    def fly(self) -> str:
        pass

class Sparrow(FlyingBird):
    def get_name(self) -> str:
        return "麻雀"

    def fly(self) -> str:
        return "飞翔中"

class Penguin(Bird):
    def get_name(self) -> str:
        return "企鹅"

def make_bird_fly(bird: FlyingBird) -> str:
    return bird.fly()
```

### TypeScript 示例

```typescript
abstract class Bird {
  abstract getName(): string;
}

abstract class FlyingBird extends Bird {
  abstract fly(): string;
}

class Sparrow extends FlyingBird {
  getName(): string {
    return "麻雀";
  }

  fly(): string {
    return "飞翔中";
  }
}

class Penguin extends Bird {
  getName(): string {
    return "企鹅";
  }
}

function makeBirdFly(bird: FlyingBird): string {
  return bird.fly();
}
```

---

## I - 接口隔离原则 (Interface Segregation Principle)

客户端不应被迫依赖它不使用的接口。将臃肿的接口拆分为更小、更具体的接口。

### Python 示例

```python
from abc import ABC, abstractmethod

class Readable(ABC):
    @abstractmethod
    def read(self) -> str:
        pass

class Writable(ABC):
    @abstractmethod
    def write(self, data: str) -> None:
        pass

class Deletable(ABC):
    @abstractmethod
    def delete(self) -> None:
        pass

class ReadOnlyStorage(Readable):
    def read(self) -> str:
        return "data"

class FullStorage(Readable, Writable, Deletable):
    def read(self) -> str:
        return "data"

    def write(self, data: str) -> None:
        pass

    def delete(self) -> None:
        pass
```

### TypeScript 示例

```typescript
interface Readable {
  read(): string;
}

interface Writable {
  write(data: string): void;
}

interface Deletable {
  delete(): void;
}

class ReadOnlyStorage implements Readable {
  read(): string {
    return "data";
  }
}

class FullStorage implements Readable, Writable, Deletable {
  read(): string {
    return "data";
  }

  write(data: string): void {}

  delete(): void {}
}
```

---

## D - 依赖倒置原则 (Dependency Inversion Principle)

高层模块不应依赖低层模块，两者都应依赖抽象。抽象不应依赖细节，细节应依赖抽象。

### Python 示例

```python
from abc import ABC, abstractmethod

class MessageSender(ABC):
    @abstractmethod
    def send(self, recipient: str, message: str) -> None:
        pass

class EmailSender(MessageSender):
    def send(self, recipient: str, message: str) -> None:
        print(f"发送邮件至 {recipient}: {message}")

class SmsSender(MessageSender):
    def send(self, recipient: str, message: str) -> None:
        print(f"发送短信至 {recipient}: {message}")

class NotificationService:
    def __init__(self, sender: MessageSender):
        self.sender = sender

    def notify(self, recipient: str, message: str) -> None:
        self.sender.send(recipient, message)
```

### TypeScript 示例

```typescript
interface MessageSender {
  send(recipient: string, message: string): void;
}

class EmailSender implements MessageSender {
  send(recipient: string, message: string): void {
    console.log(`发送邮件至 ${recipient}: ${message}`);
  }
}

class SmsSender implements MessageSender {
  send(recipient: string, message: string): void {
    console.log(`发送短信至 ${recipient}: ${message}`);
  }
}

class NotificationService {
  constructor(private sender: MessageSender) {}

  notify(recipient: string, message: string): void {
    this.sender.send(recipient, message);
  }
}
```

---

## 应用注意事项

- **SRP** 不意味着每个类只能有一个方法，而是强调职责的内聚性
- **OCP** 需要合理预判变化点，过度抽象反而增加复杂度
- **LSP** 违反通常表现为子类抛出基类没有的异常或改变方法语义
- **ISP** 接口粒度不宜过细，需平衡接口数量与使用便利性
- **DIP** 依赖注入是实现依赖倒置的常用手段，但需避免过度使用 IoC 容器

## 相关知识

- [KP-GEN-002] 函数式编程原则 — 与 SOLID 互补的编程范式
- [KP-GEN-010] 观察者模式 — SOLID 原则在设计模式中的体现
- [KP-EXP-PAT-001] 仓储模式 — 依赖倒置原则的典型应用
