---
id: reactive-patterns
type: knowledge
category: paradigms
tags: [响应式编程, Observer, 背压, RxJS, RxJava, 响应式流]
version: 1.0.0
confidence: high
---

## 响应式编程模式 (版本: 1.0 | 适用: RxJS/RxJava/响应式流)

### 核心规则
- 核心思想：数据源变化时，依赖该数据的计算自动更新（推模式）
- 响应式流四大接口：Publisher → Subscriber，Subscription 控制流，Processor 中间处理
- 背压策略：Buffer（有 OOM 风险）/ Drop / Latest / Error / 自定义
- Observer 是推模式，Iterator 是拉模式

### 代码示例

```typescript
import { fromEvent, debounceTime, map } from 'rxjs';
fromEvent(input, 'input').pipe(
  debounceTime(300),
  map(e => e.target.value)
).subscribe(value => search(value));
```

### 反模式
- ❌ 观察者未取消订阅 — 主题持有引用阻止 GC，导致内存泄漏
- ❌ 观察者在 update 中修改主题状态 — 可能触发无限递归
- ❌ 无背压处理的生产者 — 消费速度跟不上时系统崩溃
