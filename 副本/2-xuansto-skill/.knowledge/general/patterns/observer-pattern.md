---
id: "KP-GEN-010"
type: "pattern"
category: "behavioral"
tags: ["观察者模式", "发布订阅", "事件驱动", "行为型模式", "EventEmitter", "事件总线"]
version: "1.0.0"
created: "2026-04-28T10:00:00Z"
updated: "2026-04-28T10:00:00Z"
source: "GoF Design Patterns / 社区实践总结"
confidence: 0.90
last_validated: "2026-04-28T10:00:00Z"
success_count: 0
failure_count: 0
references:
  - id: "KP-GEN-001"
    relation: "implements"
  - id: "KP-GEN-002"
    relation: "extends"
---

# 观察者模式 (Observer Pattern)

## 定义

观察者模式定义对象间一对多的依赖关系，当一个对象（主题/被观察者）状态发生改变时，所有依赖于它的对象（观察者）都会收到通知并自动更新。该模式是事件驱动架构和响应式编程的基础。

## 适用场景

- 事件系统实现（DOM 事件、自定义事件）
- 消息总线与发布/订阅通信
- 数据绑定与状态变更通知
- 日志与审计系统
- 跨组件/跨模块通信
- Electron 主进程与渲染进程通信

## 结构

```
┌──────────────┐        ┌──────────────┐
│   Subject    │        │   Observer   │
│──────────────│        │──────────────│
│ +attach()    │◄───────│ +update()    │
│ +detach()    │        └──────────────┘
│ +notify()    │              ▲
│──────────────│              │
│ observers[]  │──────────────┘
└──────────────┘
```

---

## Python 实现

```python
from abc import ABC, abstractmethod
from typing import List
from dataclasses import dataclass, field
from datetime import datetime

class Observer(ABC):
    @abstractmethod
    def update(self, event_type: str, data: dict) -> None:
        pass

class Subject:
    def __init__(self):
        self._observers: List[Observer] = []

    def attach(self, observer: Observer) -> None:
        if observer not in self._observers:
            self._observers.append(observer)

    def detach(self, observer: Observer) -> None:
        self._observers.remove(observer)

    def notify(self, event_type: str, data: dict) -> None:
        for observer in self._observers:
            observer.update(event_type, data)

@dataclass
class OrderEvent:
    order_id: str
    status: str
    timestamp: datetime = field(default_factory=datetime.now)

class EmailNotifier(Observer):
    def update(self, event_type: str, data: dict) -> None:
        if event_type == "order_created":
            print(f"[邮件] 新订单: {data['order_id']}")

class InventoryUpdater(Observer):
    def update(self, event_type: str, data: dict) -> None:
        if event_type == "order_created":
            print(f"[库存] 扣减库存，订单: {data['order_id']}")

class AnalyticsTracker(Observer):
    def update(self, event_type: str, data: dict) -> None:
        print(f"[分析] 记录事件: {event_type}, 数据: {data}")

order_subject = Subject()
order_subject.attach(EmailNotifier())
order_subject.attach(InventoryUpdater())
order_subject.attach(AnalyticsTracker())

order_subject.notify("order_created", {"order_id": "ORD-001"})
```

---

## TypeScript 实现

```typescript
interface Observer {
  update(eventType: string, data: Record<string, unknown>): void;
}

class Subject {
  private observers: Set<Observer> = new Set();

  attach(observer: Observer): void {
    this.observers.add(observer);
  }

  detach(observer: Observer): void {
    this.observers.delete(observer);
  }

  notify(eventType: string, data: Record<string, unknown>): void {
    for (const observer of this.observers) {
      observer.update(eventType, data);
    }
  }
}

class EmailNotifier implements Observer {
  update(eventType: string, data: Record<string, unknown>): void {
    if (eventType === "order_created") {
      console.log(`[邮件] 新订单: ${data.orderId}`);
    }
  }
}

class InventoryUpdater implements Observer {
  update(eventType: string, data: Record<string, unknown>): void {
    if (eventType === "order_created") {
      console.log(`[库存] 扣减库存，订单: ${data.orderId}`);
    }
  }
}

class AnalyticsTracker implements Observer {
  update(eventType: string, data: Record<string, unknown>): void {
    console.log(`[分析] 记录事件: ${eventType}`, data);
  }
}

const orderSubject = new Subject();
orderSubject.attach(new EmailNotifier());
orderSubject.attach(new InventoryUpdater());
orderSubject.attach(new AnalyticsTracker());

orderSubject.notify("order_created", { orderId: "ORD-001" });
```

---

## 变体：发布/订阅模式

观察者模式的常见变体是发布/订阅（Pub/Sub）模式，通过事件总线解耦发布者和订阅者。

### TypeScript 事件总线实现

```typescript
type EventHandler = (data: unknown) => void;

class EventBus {
  private handlers: Map<string, Set<EventHandler>> = new Map();

  subscribe(event: string, handler: EventHandler): () => void {
    if (!this.handlers.has(event)) {
      this.handlers.set(event, new Set());
    }
    this.handlers.get(event)!.add(handler);

    return () => {
      this.handlers.get(event)?.delete(handler);
    };
  }

  publish(event: string, data: unknown): void {
    this.handlers.get(event)?.forEach((handler) => handler(data));
  }
}

const bus = new EventBus();

const unsubscribe = bus.subscribe("user:login", (data) => {
  console.log("用户登录:", data);
});

bus.publish("user:login", { userId: "u-001", timestamp: Date.now() });

unsubscribe();
```

---

## 注意事项

- **内存泄漏**：观察者未取消订阅会导致主题持有观察者引用，阻止垃圾回收。务必在组件销毁时调用 `detach` 或 `unsubscribe`
- **通知循环**：观察者在 `update` 方法中修改主题状态可能触发无限递归，需设置防护标志
- **异步通知**：异步通知可能导致观察者执行顺序不可预测，如需顺序保证应使用同步通知或消息队列
- **性能影响**：观察者数量过多时，通知开销显著。考虑使用异步批量通知或按需通知
- **错误隔离**：单个观察者的异常不应影响其他观察者接收通知，需在 `notify` 中添加 try-catch

## 相关知识

- [KP-GEN-001] SOLID 设计原则 — 开闭原则在观察者模式中的体现
- [KP-GEN-002] 函数式编程原则 — 函数式响应式编程（FRP）的基础
- [KP-GEN-030] Electron 最佳实践 — IPC 通信中的事件驱动模式
