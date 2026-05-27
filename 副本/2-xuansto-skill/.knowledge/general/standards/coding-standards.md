---
id: "KP-GEN-STD-001"
type: "standards"
category: "coding"
tags: ["coding-standards", "best-practices", "DRY", "KISS", "YAGNI", "命名规范", "代码审查"]
version: "1.0.0"
created: "2026-04-28T10:00:00Z"
updated: "2026-04-28T10:00:00Z"
source: "Clean Code / The Pragmatic Programmer / 社区实践总结"
confidence: 0.95
last_validated: "2026-04-28T10:00:00Z"
success_count: 0
failure_count: 0
references:
  - id: "KP-GEN-001"
    relation: "complements"
  - id: "KP-GEN-002"
    relation: "complements"
  - id: "KP-GEN-020"
    relation: "complies"
---

# 编码标准概览

## 概述

编码标准是团队协作的基石，确保代码库具备一致性、可读性和可维护性。本文涵盖通用编码原则、命名规范、代码组织、文档标准和代码审查清单，适用于 Python、TypeScript 等主流语言的跨平台项目开发。

---

## 通用编码原则

### DRY — Don't Repeat Yourself

不要重复自己。系统中每一项知识都必须有单一、明确、权威的表示。重复代码是维护噩梦的根源。

```python
def calculate_discount(price: float, customer_type: str) -> float:
    rates = {"regular": 1.0, "vip": 0.8, "premium": 0.7}
    return price * rates.get(customer_type, 1.0)
```

```typescript
function calculateDiscount(price: number, customerType: string): number {
  const rates: Record<string, number> = {
    regular: 1.0,
    vip: 0.8,
    premium: 0.7,
  };
  return price * (rates[customerType] ?? 1.0);
}
```

### KISS — Keep It Simple, Stupid

保持简单。最简单的解决方案通常是最好的。过度设计增加理解和维护成本。

| 反模式 | 推荐做法 |
|--------|---------|
| 为未来可能的需求预先抽象 | 在需求出现时再重构 |
| 嵌套超过3层的条件逻辑 | 提前返回或使用策略模式 |
| 一个函数超过50行 | 拆分为职责单一的子函数 |
| 过度使用设计模式 | 选择最简单的可行方案 |

### YAGNI — You Aren't Gonna Need It

你不会需要它。只实现当前确实需要的功能，不要为假想的未来需求编写代码。

---

## 命名规范

### 通用原则

1. **名副其实**：名称应解释其存在的目的和用途
2. **避免缩写**：除非是广泛认知的缩写（如 URL、ID、HTTP）
3. **避免魔法数**：用命名常量替代硬编码数值
4. **上下文一致**：同一领域中相同概念使用相同术语

### 各语言命名约定

| 元素类型 | Python | TypeScript |
|---------|--------|------------|
| 模块/文件 | `snake_case` | `kebab-case` |
| 类 | `PascalCase` | `PascalCase` |
| 函数/方法 | `snake_case` | `camelCase` |
| 变量 | `snake_case` | `camelCase` |
| 常量 | `UPPER_SNAKE_CASE` | `UPPER_SNAKE_CASE` |
| 私有成员 | `_leading_underscore` | `#private` 或 `_leadingUnderscore` |
| 接口/协议 | `PascalCase` (Protocol) | `PascalCase` (I前缀可选) |
| 类型别名 | `PascalCase` | `PascalCase` |
| 枚举值 | `UPPER_SNAKE_CASE` | `PascalCase` |

### 布尔命名

```python
is_active: bool
has_permission: bool
can_edit: bool
should_retry: bool
```

```typescript
isActive: boolean;
hasPermission: boolean;
canEdit: boolean;
shouldRetry: boolean;
```

---

## 代码组织最佳实践

### 文件结构

- 单一职责：每个文件围绕一个核心概念组织
- 文件长度：建议不超过 300 行，超过时考虑拆分
- 导入顺序：标准库 → 第三方库 → 项目内部模块，各组之间空一行

### 函数设计

- 函数长度：建议不超过 20 行，最长不超过 50 行
- 参数数量：不超过 3 个，超过时使用配置对象/数据类
- 纯函数优先：相同输入始终产生相同输出，无副作用

```python
from dataclasses import dataclass

@dataclass
class SearchParams:
    query: str
    page: int = 1
    size: int = 20
    sort_by: str = "relevance"

def search(params: SearchParams) -> list[dict]:
    pass
```

```typescript
interface SearchParams {
  query: string;
  page?: number;
  size?: number;
  sortBy?: string;
}

function search(params: SearchParams): Record<string, unknown>[] {
  return [];
}
```

### 错误处理

- 使用异常而非返回错误码
- 在合适的层级捕获和处理异常
- 自定义异常类型携带上下文信息
- 永远不要吞掉异常（空 catch 块）

---

## 文档标准

### 模块级文档

```python
"""用户认证服务模块。

提供 JWT 令牌签发、验证和刷新功能。
依赖 UserRepository 进行用户查询。
"""
```

### 函数级文档

```python
def generate_token(user_id: str, expires_in: int = 900) -> str:
    """生成 JWT 访问令牌。

    Args:
        user_id: 用户唯一标识符
        expires_in: 令牌有效期（秒），默认15分钟

    Returns:
        签名后的 JWT 字符串

    Raises:
        ValueError: 当 user_id 为空时
    """
```

```typescript
/**
 * 生成 JWT 访问令牌
 * @param userId - 用户唯一标识符
 * @param expiresIn - 令牌有效期（秒），默认15分钟
 * @returns 签名后的 JWT 字符串
 * @throws {Error} 当 userId 为空时
 */
function generateToken(userId: string, expiresIn: number = 900): string {
  return "";
}
```

### 文档覆盖要求

| 代码元素 | 最低文档要求 |
|---------|-------------|
| 公共模块 | 模块用途和主要导出 |
| 公共类 | 职责描述和主要方法概览 |
| 公共函数/方法 | 参数、返回值、异常说明 |
| 私有函数 | 复杂逻辑需行内注释 |
| 配置项 | 类型、默认值、影响范围 |

---

## 代码审查清单

### 正确性

- [ ] 代码逻辑是否正确实现了需求
- [ ] 边界条件和异常场景是否处理
- [ ] 是否存在空指针/未定义访问风险

### 可读性

- [ ] 命名是否清晰、一致、无歧义
- [ ] 函数长度和复杂度是否合理
- [ ] 是否存在可以简化的条件逻辑

### 安全性

- [ ] 外部输入是否经过验证和编码
- [ ] 是否存在 SQL 注入、XSS 等漏洞
- [ ] 敏感数据是否正确处理（不记录、不暴露）

### 性能

- [ ] 是否存在不必要的循环或重复计算
- [ ] 数据库查询是否合理（N+1 问题）
- [ ] 资源是否正确释放（连接、文件句柄）

### 可维护性

- [ ] 是否遵循 DRY、KISS、YAGNI 原则
- [ ] 新增代码是否易于扩展和修改
- [ ] 是否有足够的文档和注释

## 相关知识

- [KP-GEN-001] SOLID 设计原则 — 编码标准的设计原则基础
- [KP-GEN-002] 函数式编程原则 — 与面向对象互补的编程范式
- [KP-GEN-020] 安全编码基础 — 编码标准中的安全实践
- [KP-GEN-TST-001] 测试金字塔指南 — 编码标准的质量验证策略
