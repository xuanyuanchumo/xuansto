---
id: tdd-practices
type: knowledge
category: testing
tags: [TDD, 测试驱动开发, 红绿重构, Mock, Stub, 单元测试]
version: 1.0.0
created: 2026-04-28
updated: 2026-04-28
confidence: high
---

# TDD 实践指南

## 红-绿-重构循环

TDD 的核心工作流是严格的三步循环：

1. **红 (Red)**：编写一个失败的测试，描述期望行为
2. **绿 (Green)**：编写最少代码使测试通过，不过度设计
3. **重构 (Refactor)**：在测试保护下优化代码结构，消除重复

关键纪律：未写测试不写产品代码，每次只写一个失败的测试。

## 测试先行原则

- 测试描述行为而非实现：`should_return_empty_list_when_no_items` 而非 `test_array`
- 测试命名使用 Given-When-Then 或 Should-When 模式
- 每个测试只验证一个行为，避免断言堆叠
- 测试之间无依赖，可任意顺序执行
- FIRST 原则：Fast / Independent / Repeatable / Self-validating / Timely

## Mock 与 Stub 策略

| 类型 | 用途 | 特征 |
|------|------|------|
| **Stub** | 提供预设返回值 | `when(repo.findById(1)).thenReturn(user)` |
| **Mock** | 验证交互行为 | `verify(mailService).send(any())` |
| **Spy** | 部分模拟，保留真实逻辑 | 包装真实对象，选择性覆盖 |
| **Fake** | 简化实现（如内存数据库） | 可用于集成测试 |

使用原则：
- 外部依赖（网络/数据库/时间）使用 Mock/Stub 隔离
- 不 Mock 被测系统本身的方法
- 优先使用 Fake 而非 Mock，减少脆弱性
- Mock 数量过多说明设计耦合过重，考虑重构

## 测试金字塔

```
     /  E2E  \        少量，慢，高成本
    / 集成测试 \      适量，验证模块协作
   /  单元测试   \    大量，快，低成本
```

单元测试覆盖率目标 ≥ 80%，关键业务路径 100%。测试代码与产品代码同等质量要求。
