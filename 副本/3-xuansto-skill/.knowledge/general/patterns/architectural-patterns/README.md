---
id: architectural-patterns
type: knowledge
category: patterns
tags: [架构模式, MVC, MVVM, 微服务, CQRS, 事件驱动]
version: 1.0.0
created: 2026-04-28
updated: 2026-04-28
confidence: high
---

# 架构模式索引

## UI 架构模式

| 模式 | 核心思想 | 适用场景 |
|------|----------|----------|
| **MVC** | Model-View-Controller，控制器协调模型与视图 | 传统 Web 应用 |
| **MVP** | Model-View-Presenter，Presenter 完全控制视图 | Android 早期、WinForms |
| **MVVM** | Model-View-ViewModel，双向数据绑定驱动 | WPF/Vue/Angular |
| **Flux** | 单向数据流：Action → Dispatcher → Store → View | React 生态 |

## 分布式架构模式

| 模式 | 核心思想 | 关键优势 | 注意事项 |
|------|----------|----------|----------|
| **Microservices** | 按业务域拆分独立服务 | 独立部署/技术异构 | 分布式复杂度、数据一致性 |
| **Event-Driven** | 事件异步通信，松耦合 | 解耦/可扩展/可追溯 | 最终一致性、事件顺序 |
| **CQRS** | 读写模型分离 | 读写独立优化 | 模型同步复杂度 |
| **Saga** | 长事务拆分为本地事务链 | 避免分布式锁 | 补偿逻辑复杂 |
| **Sidecar** | 辅助进程处理横切关注点 | 与业务逻辑解耦 | 资源开销 |

## 系统架构模式

| 模式 | 核心思想 | 适用场景 |
|------|----------|----------|
| **Layered** | 分层架构（表现/业务/持久化） | 传统企业应用 |
| **Hexagonal** | 端口与适配器，核心逻辑不依赖外部 | 领域驱动设计 |
| **Plugin** | 核心系统 + 插件扩展 | IDE/编辑器/工具链 |
| **Pipeline** | 数据流经一系列处理阶段 | 编译器/ETL/中间件 |

## 选型原则

- 团队规模小 → Monolith 优先，模块化设计预留拆分能力
- 高并发读 → CQRS + 缓存层
- 复杂业务流程 → Event-Driven + Saga
- 多端共享逻辑 → Hexagonal + 领域层隔离
