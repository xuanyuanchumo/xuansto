---
id: tdd-practices
type: knowledge
category: testing
tags: [TDD, 测试驱动开发, 红绿重构, Mock, Stub, 单元测试]
version: 1.0.0
confidence: high
---

## TDD 实践指南 (版本: 1.0 | 适用: 通用)

### 核心规则
- 红-绿-重构：先写失败测试 → 最少代码通过 → 测试保护下重构
- 测试描述行为而非实现：`should_return_empty_list_when_no_items`
- 每个测试只验证一个行为，测试之间无依赖
- FIRST 原则：Fast/Independent/Repeatable/Self-validating/Timely
- Stub 提供预设返回值，Mock 验证交互行为，优先使用 Fake 减少脆弱性
- Mock 数量过多说明设计耦合过重，考虑重构
- 单元测试覆盖率 ≥ 80%，关键业务路径 100%

### 代码示例

```typescript
describe("PriceCalculator", () => {
  it("should apply VIP discount", () => {
    const calculator = new PriceCalculator(new VIPPricing());
    expect(calculator.calculate(100)).toBe(80);
  });
});
```

### 反模式
- ❌ 先写实现再补测试 — 失去 TDD 设计驱动价值
- ❌ 一个测试多个断言 — 测试失败难以定位原因
- ❌ 过度 Mock 被测系统自身方法 — 测试与实现强耦合
