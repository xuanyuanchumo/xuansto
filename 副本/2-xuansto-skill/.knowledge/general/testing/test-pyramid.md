---
id: "KP-GEN-TST-001"
type: "testing"
category: "test-strategy"
tags: ["test-pyramid", "tdd", "testing", "单元测试", "集成测试", "E2E测试", "mock", "桌面测试"]
version: "1.0.0"
created: "2026-04-28T10:00:00Z"
updated: "2026-04-28T10:00:00Z"
source: "Martin Fowler - Testing Pyramid / Kent Beck - TDD / 社区实践总结"
confidence: 0.95
last_validated: "2026-04-28T10:00:00Z"
success_count: 0
failure_count: 0
references:
  - id: "KP-GEN-STD-001"
    relation: "validates"
  - id: "KP-GEN-001"
    relation: "supports"
  - id: "KP-GEN-030"
    relation: "extends"
---

# 测试金字塔指南

## 概述

测试金字塔是指导测试策略的经典模型，由 Mike Cohn 提出，核心思想是：底层测试数量多、速度快、成本低；顶层测试数量少、速度慢、成本高。合理的测试分层确保以最小成本获得最大信心。本文涵盖 Web 和桌面应用的测试策略、最佳实践和 Mock 方案。

---

## 测试金字塔模型

```
        /  E2E  \          5-10% — 慢、脆弱、高成本
       / 集成测试 \        15-25% — 中速、中等稳定
      /  单元测试   \      60-70% — 快速、稳定、低成本
     /_______________\
```

| 层级 | 占比 | 执行速度 | 稳定性 | 维护成本 | 覆盖范围 |
|------|------|---------|--------|---------|---------|
| 单元测试 | 60-70% | 毫秒级 | 高 | 低 | 单个函数/类 |
| 集成测试 | 15-25% | 秒级 | 中 | 中 | 模块交互 |
| E2E 测试 | 5-10% | 分钟级 | 低 | 高 | 完整用户流程 |

---

## 单元测试最佳实践 (60-70%)

### 核心原则

1. **FIRST 原则**：Fast（快速）、Independent（独立）、Repeatable（可重复）、Self-validating（自验证）、Timely（及时）
2. **单一断言**：每个测试方法验证一个行为，避免断言堆叠
3. **AAA 模式**：Arrange（准备）→ Act（执行）→ Assert（断言）

### Python 示例 (pytest)

```python
import pytest
from calculator import PriceCalculator, PricingStrategy

class TestPriceCalculator:
    def test_calculate_with_vip_discount(self):
        calculator = PriceCalculator(VIPPricing())
        result = calculator.calculate(100.0)
        assert result == 80.0

    def test_calculate_with_zero_price(self):
        calculator = PriceCalculator(RegularPricing())
        result = calculator.calculate(0.0)
        assert result == 0.0

    def test_calculate_with_negative_price_raises(self):
        calculator = PriceCalculator(RegularPricing())
        with pytest.raises(ValueError, match="价格不能为负数"):
            calculator.calculate(-10.0)
```

### TypeScript 示例 (Vitest)

```typescript
import { describe, it, expect } from "vitest";
import { PriceCalculator, VIPPricing, RegularPricing } from "./calculator";

describe("PriceCalculator", () => {
  it("should apply VIP discount", () => {
    const calculator = new PriceCalculator(new VIPPricing());
    expect(calculator.calculate(100)).toBe(80);
  });

  it("should handle zero price", () => {
    const calculator = new PriceCalculator(new RegularPricing());
    expect(calculator.calculate(0)).toBe(0);
  });

  it("should reject negative price", () => {
    const calculator = new PriceCalculator(new RegularPricing());
    expect(() => calculator.calculate(-10)).toThrow("价格不能为负数");
  });
});
```

### 单元测试覆盖要求

| 代码类型 | 最低覆盖率 | 推荐覆盖率 |
|---------|-----------|-----------|
| 核心业务逻辑 | 90% | 95%+ |
| 工具函数 | 90% | 100% |
| 数据模型 | 70% | 85% |
| 控制器/处理函数 | 70% | 80% |
| UI 组件 | 50% | 70% |

---

## 集成测试最佳实践 (15-25%)

### 核心原则

1. **验证模块交互**：测试模块之间的数据流和契约
2. **使用真实依赖**：优先使用真实数据库（测试实例）而非 Mock
3. **测试边界条件**：API 契约、数据库事务、消息格式

### API 集成测试

```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_create_user_and_retrieve():
    async with AsyncClient(app=app, base_url="http://test") as client:
        create_response = await client.post("/api/users", json={
            "name": "张三",
            "email": "zhangsan@example.com",
        })
        assert create_response.status_code == 201
        user_id = create_response.json()["id"]

        get_response = await client.get(f"/api/users/{user_id}")
        assert get_response.status_code == 200
        assert get_response.json()["email"] == "zhangsan@example.com"
```

### 数据库集成测试

```typescript
import { describe, it, expect, beforeAll, afterAll } from "vitest";
import { UserRepository } from "./user-repository";
import { testPool, migrateUp, migrateDown } from "../test-helpers/db";

describe("UserRepository Integration", () => {
  let repo: UserRepository;

  beforeAll(async () => {
    await migrateUp(testPool);
    repo = new UserRepository(testPool);
  });

  afterAll(async () => {
    await migrateDown(testPool);
    await testPool.end();
  });

  it("should persist and retrieve user", async () => {
    const created = await repo.create({
      name: "李四",
      email: "lisi@example.com",
    });
    const found = await repo.findById(created.id);
    expect(found?.email).toBe("lisi@example.com");
  });
});
```

---

## E2E 测试最佳实践 (5-10%)

### 核心原则

1. **覆盖关键路径**：只测试最核心的用户流程
2. **独立测试环境**：使用专用测试数据库和服务
3. **避免实现耦合**：通过用户视角操作，不依赖内部实现

### Web E2E 测试 (Playwright)

```typescript
import { test, expect } from "@playwright/test";

test("用户注册并登录流程", async ({ page }) => {
  await page.goto("/register");
  await page.fill('[data-testid="username"]', "新用户");
  await page.fill('[data-testid="email"]', "newuser@example.com");
  await page.fill('[data-testid="password"]', "SecurePass123!");
  await page.click('[data-testid="submit"]');

  await expect(page.locator('[data-testid="welcome"]')).toBeVisible();

  await page.goto("/login");
  await page.fill('[data-testid="email"]', "newuser@example.com");
  await page.fill('[data-testid="password"]', "SecurePass123!");
  await page.click('[data-testid="login"]');

  await expect(page.locator('[data-testid="dashboard"]')).toBeVisible();
});
```

---

## 桌面测试金字塔扩展

桌面应用（Electron/Tauri）在传统金字塔基础上需增加平台相关测试层：

```
       /  手动探索  \        1-3% — 平台特有交互
      /  E2E 自动化  \       5-8% — Spectron/Playwright
     /  集成测试       \     15-20% — IPC/原生API
    /  单元测试          \   65-75% — 纯逻辑
   /_______________________\
```

### 桌面特有测试场景

| 场景 | 测试层级 | 工具 |
|------|---------|------|
| 主进程逻辑 | 单元测试 | Vitest/Jest |
| IPC 通信 | 集成测试 | Electron IPC Mock |
| 原生模块调用 | 集成测试 | 依赖注入 + Mock |
| 窗口管理 | E2E 测试 | Playwright Electron |
| 自动更新 | E2E 测试 | 模拟更新服务器 |
| 跨平台兼容 | 手动探索 | 多 OS 虚拟机 |

---

## 测试命名规范

### 统一命名模式

```
test_{单元}_{场景}_{预期结果}
```

| 语言 | 示例 |
|------|------|
| Python | `test_calculate_with_vip_discount_returns_80_percent` |
| TypeScript | `should return 80% when calculating with VIP discount` |

### describe/it 组织模式

```typescript
describe("PriceCalculator", () => {
  describe("calculate", () => {
    it("should apply VIP discount", () => {});
    it("should reject negative price", () => {});
    it("should handle zero price", () => {});
  });
});
```

---

## Mock/Stub 策略

### 何时使用 Mock

| 场景 | 策略 | 原因 |
|------|------|------|
| 外部 API 调用 | Mock | 避免网络依赖、控制响应 |
| 数据库操作（单元测试） | Mock | 隔离逻辑、加速执行 |
| 时间相关逻辑 | Mock | 确保可重复性 |
| 文件系统操作 | Mock/临时目录 | 避免副作用 |
| 内部模块交互 | Stub | 简化依赖、聚焦被测逻辑 |

### Python Mock 示例

```python
from unittest.mock import AsyncMock, patch
import pytest

@pytest.mark.asyncio
async def test_send_notification_calls_email_service():
    mock_sender = AsyncMock()
    service = NotificationService(mock_sender)

    await service.notify("user@example.com", "测试消息")

    mock_sender.send.assert_called_once_with(
        "user@example.com", "测试消息"
    )
```

### TypeScript Mock 示例

```typescript
import { describe, it, expect, vi } from "vitest";

it("should call email service when notifying", async () => {
  const mockSender = { send: vi.fn().mockResolvedValue(undefined) };
  const service = new NotificationService(mockSender);

  await service.notify("user@example.com", "测试消息");

  expect(mockSender.send).toHaveBeenCalledWith(
    "user@example.com",
    "测试消息"
  );
});
```

### Mock 使用原则

1. **最小化 Mock 范围**：只 Mock 直接依赖，不 Mock 间接依赖
2. **验证交互而非实现**：断言行为结果而非调用顺序
3. **避免过度 Mock**：Mock 过多意味着设计可能存在问题
4. **清理 Mock 状态**：每个测试前后确保 Mock 状态重置

## 相关知识

- [KP-GEN-STD-001] 编码标准概览 — 测试验证的编码标准
- [KP-GEN-001] SOLID 设计原则 — 可测试性的设计基础
- [KP-GEN-030] Electron 最佳实践 — 桌面应用测试策略
- [KP-EXP-DSK-001] Electron 上下文隔离经验 — 桌面端 IPC 测试实践
