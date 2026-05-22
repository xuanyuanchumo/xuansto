---
id: "KP-GEN-TST-001"
type: "testing"
category: "test-strategy"
tags: ["test-pyramid", "tdd", "testing", "单元测试", "集成测试", "E2E测试", "mock", "桌面测试"]
version: "1.0.0"
confidence: 0.95
---

## 测试金字塔指南 (版本: 1.0 | 适用: Web/桌面应用)

### 核心规则
- 单元测试 60-70%：毫秒级，高稳定，覆盖单个函数/类
- 集成测试 15-25%：秒级，验证模块交互，优先使用真实数据库
- E2E 测试 5-10%：分钟级，仅覆盖核心用户流程
- 桌面应用扩展：IPC 通信集成测试 + 平台特定手动探索
- AAA 模式：Arrange → Act → Assert
- Mock 最小化：只 Mock 直接依赖，不 Mock 间接依赖
- 核心业务逻辑覆盖率 ≥ 90%，工具函数 100%

### 代码示例

```python
class TestPriceCalculator:
    def test_calculate_with_vip_discount(self):
        calculator = PriceCalculator(VIPPricing())
        assert calculator.calculate(100.0) == 80.0
```

```typescript
describe("PriceCalculator", () => {
  it("should reject negative price", () => {
    expect(() => new PriceCalculator(new RegularPricing()).calculate(-10))
      .toThrow("价格不能为负数");
  });
});
```

### 反模式
- ❌ E2E 测试占比过高 — 维护成本爆炸
- ❌ 单元测试 Mock 过多 — 测试与实现强耦合
- ❌ 集成测试使用 Mock 数据库 — 无法发现真实交互问题
