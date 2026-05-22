---
id: "KP-GEN-001"
type: "paradigm"
category: "object-oriented"
tags: ["SOLID", "面向对象", "设计原则", "单一职责", "开闭原则", "依赖倒置", "接口隔离", "里氏替换"]
version: "1.0.0"
confidence: 0.95
---

## SOLID 设计原则 (版本: 1.0 | 适用: OOP/Python/TypeScript)

### 核心规则
- **S** 单一职责：一个类只有一个引起变化的原因，职责内聚
- **O** 开闭原则：对扩展开放，对修改关闭，通过抽象和多态实现
- **L** 里氏替换：子类必须能替换基类，继承保证超类性质在子类成立
- **I** 接口隔离：客户端不应被迫依赖不使用的接口，拆分臃肿接口
- **D** 依赖倒置：高层不依赖低层，两者都依赖抽象；抽象不依赖细节

### 代码示例

```typescript
interface PricingStrategy { calculate(base: number): number; }
class VIPPricing implements PricingStrategy {
  calculate(base: number): number { return base * 0.8; }
}
class PriceCalculator {
  constructor(private strategy: PricingStrategy) {}
  calculate(base: number): number { return this.strategy.calculate(base); }
}
```

```python
class MessageSender(ABC):
    @abstractmethod
    def send(self, recipient: str, message: str) -> None: ...

class NotificationService:
    def __init__(self, sender: MessageSender):
        self.sender = sender
    def notify(self, recipient: str, message: str) -> None:
        self.sender.send(recipient, message)
```

### 反模式
- ❌ 类承担多职责（如 User 同时处理持久化和通知）— 违反 SRP
- ❌ 继承层次超过 3 层 — 应优先使用组合
- ❌ 子类抛出基类没有的异常 — 违反 LSP
- ❌ 胖接口包含客户端不需要的方法 — 违反 ISP
