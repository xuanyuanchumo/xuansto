---
id: oop-principles
type: knowledge
category: paradigms
tags: [OOP, SOLID, 封装, 继承, 多态, 设计原则]
version: 1.0.0
created: 2026-04-28
updated: 2026-04-28
confidence: high
---

# 面向对象编程原则

## 三大核心特性

- **封装 (Encapsulation)**：将数据和操作数据的方法绑定在一起，通过访问修饰符控制外部可见性。隐藏实现细节，暴露最小接口，降低耦合度。
- **继承 (Inheritance)**：子类复用父类的属性和方法，建立 is-a 关系。优先使用组合而非继承（Composition over Inheritance），避免深层继承链。
- **多态 (Polymorphism)**：同一接口不同实现，运行时动态绑定。分为编译时多态（方法重载 Overloading）和运行时多态（方法重写 Overriding）。

## SOLID 原则

| 原则 | 名称 | 核心要求 |
|------|------|----------|
| S | Single Responsibility | 一个类只有一个引起变化的原因 |
| O | Open/Closed | 对扩展开放，对修改关闭 |
| L | Liskov Substitution | 子类必须能替换其父类而不破坏正确性 |
| I | Interface Segregation | 客户端不应被迫依赖它不使用的接口 |
| D | Dependency Inversion | 高层模块不依赖低层模块，两者都依赖抽象 |

## 补充设计原则

- **DRY (Don't Repeat Yourself)**：消除重复逻辑，提取公共抽象
- **KISS (Keep It Simple, Stupid)**：优先选择最简单的可行方案
- **Law of Demeter**：一个对象应尽可能少地了解其他对象的内部结构，最少知识原则
- **Tell, Don't Ask**：告诉对象做什么，而非询问状态后做决策

## 实践要点

- 构造函数注入依赖，避免在类内部 new 具体实现
- 使用 Interface 或 Abstract Class 定义契约，面向接口编程
- 优先使用组合模式实现代码复用，继承层次控制在 3 层以内
- 保持类的内聚性（High Cohesion），每个类职责单一明确
