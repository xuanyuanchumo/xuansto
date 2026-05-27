---
id: "KP-GEN-010"
type: "pattern"
category: "behavioral"
tags: ["观察者模式", "发布订阅", "事件驱动", "行为型模式", "EventEmitter", "事件总线"]
version: "1.0.0"
confidence: 0.90
---

## 观察者模式 (版本: 1.0 | 适用: 事件驱动架构)

### 核心规则
- 定义对象间一对多依赖，主题状态变更时自动通知所有观察者
- 主题维护观察者列表：attach / detach / notify
- 发布/订阅变体通过事件总线解耦发布者和订阅者
- 组件销毁时必须取消订阅，防止内存泄漏
- notify 中添加 try-catch，单个观察者异常不影响其他观察者

### 代码示例

```typescript
class Subject {
  private observers: Set<Observer> = new Set();
  attach(o: Observer) { this.observers.add(o); }
  detach(o: Observer) { this.observers.delete(o); }
  notify(event: string, data: unknown) {
    for (const o of this.observers) {
      try { o.update(event, data); } catch { /* 隔离错误 */ }
    }
  }
}

class EventBus {
  private handlers = new Map<string, Set<Function>>();
  subscribe(event: string, handler: Function): () => void {
    if (!this.handlers.has(event)) this.handlers.set(event, new Set());
    this.handlers.get(event)!.add(handler);
    return () => this.handlers.get(event)?.delete(handler);
  }
  publish(event: string, data: unknown) {
    this.handlers.get(event)?.forEach(h => h(data));
  }
}
```

### 反模式
- ❌ 观察者未取消订阅 — 主题持有引用阻止 GC
- ❌ 观察者在 update 中修改主题 — 触发无限递归
- ❌ 同步通知观察者数量过多 — 性能瓶颈，应考虑异步批量通知
