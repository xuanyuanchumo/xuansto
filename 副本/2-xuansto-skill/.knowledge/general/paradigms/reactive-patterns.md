---
id: reactive-patterns
type: knowledge
category: paradigms
tags: [响应式编程, Observer, 背压, RxJS, RxJava, 响应式流]
version: 1.0.0
created: 2026-04-28
updated: 2026-04-28
confidence: high
---

# 响应式编程模式

## 核心概念

响应式编程 (Reactive Programming) 是一种面向数据流和变化传播的声明式编程范式。核心思想：当数据源发生变化时，依赖该数据的计算自动更新。

## Observer 模式

响应式编程的基础是 Observer 模式：Subject 维护一组 Observer，状态变更时自动通知所有订阅者。

```
Subject ──subscribe──▶ Observer
   │                      │
   └──notify()───────────▶ onUpdate()
```

关键区别：Iterator 是拉模式（消费者主动获取），Observer 是推模式（生产者主动推送）。

## 响应式流规范 (Reactive Streams)

四大核心接口：
- **Publisher**：数据源，产生数据项
- **Subscriber**：消费者，接收并处理数据
- **Subscription**：订阅关系，控制数据流
- **Processor**：同时充当 Publisher 和 Subscriber 的中间处理阶段

## 背压 (Backpressure) 处理

当生产速度超过消费速度时，需要背压机制防止系统崩溃：

| 策略 | 说明 |
|------|------|
| Buffer | 缓冲未处理数据，有 OOM 风险 |
| Drop | 丢弃无法处理的数据 |
| Latest | 只保留最新数据，丢弃旧数据 |
| Error | 超出容量直接报错 |
| OnOverflow | 自定义溢出处理逻辑 |

## RxJS 示例

```typescript
import { fromEvent, debounceTime, map } from 'rxjs';
fromEvent(input, 'input').pipe(
  debounceTime(300),
  map(e => e.target.value)
).subscribe(value => search(value));
```

## RxJava 示例

```kotlin
Observable.just("Hello", "World")
  .map { it.uppercase() }
  .filter { it.length > 3 }
  .subscribe { println(it) }
```

## 适用场景

- UI 事件流处理（搜索框防抖、拖拽）
- 实时数据推送（WebSocket、SSE）
- 异步数据组合（并行请求、级联调用）
- 传感器数据流处理
