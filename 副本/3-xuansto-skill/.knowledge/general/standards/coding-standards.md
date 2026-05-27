---
id: "KP-GEN-STD-001"
type: "standards"
category: "coding"
tags: ["coding-standards", "best-practices", "DRY", "KISS", "YAGNI", "命名规范", "代码审查"]
version: "1.0.0"
confidence: 0.95
---

## 编码标准概览 (版本: 1.0 | 适用: Python/TypeScript)

### 核心规则
- DRY：系统中每项知识有单一权威表示，消除重复
- KISS：最简单的方案通常最好，嵌套不超过 3 层，函数不超过 50 行
- YAGNI：只实现当前需要的功能，不为假想需求编码
- 命名：Python snake_case，TypeScript camelCase，类 PascalCase，常量 UPPER_SNAKE
- 布尔变量用 is/has/can/should 前缀，函数用动词开头
- 函数参数不超过 3 个，超过时使用配置对象
- 错误处理：使用异常而非错误码，永远不吞掉异常

### 代码示例

```python
@dataclass
class SearchParams:
    query: str
    page: int = 1
    size: int = 20
    sort_by: str = "relevance"

def search(params: SearchParams) -> list[dict]: ...
```

```typescript
interface SearchParams { query: string; page?: number; size?: number; sortBy?: string; }
function search(params: SearchParams): Record<string, unknown>[] { return []; }
```

### 反模式
- ❌ 单字母变量（循环 i/j/k 除外）— 可读性差
- ❌ 魔法数硬编码 — 应使用命名常量
- ❌ 空 catch 块吞掉异常 — 隐藏错误
