---
id: naming-conventions
type: knowledge
category: standards
tags: [命名规范, camelCase, snake_case, PascalCase, 代码风格]
version: 1.0.0
confidence: high
---

## 命名约定规范 (版本: 1.0 | 适用: 多语言)

### 核心规则
- JS/TS：变量/函数 camelCase，类/接口 PascalCase，常量 SCREAMING_SNAKE，文件 kebab-case
- Python：变量/函数 snake_case，类 PascalCase，常量 SCREAMING_SNAKE，模块 snake_case
- Rust：变量/函数 snake_case，类型/trait PascalCase，常量 SCREAMING_SNAKE
- 名称表达用途而非实现：`fetchUsers` 优于 `getData`
- 避免缩写（通用缩写除外：id, url, http）
- 布尔变量：is/has/can/should 前缀
- 函数命名：动词开头 get/set/create/delete/update/find/handle/on
- 类命名：名词体现职责 UserRepository, PaymentService

### 代码示例

```typescript
const isActive: boolean = true;
const hasPermission: boolean = false;
async function fetchUsers(): Promise<User[]> { ... }
class UserRepository { ... }
const MAX_RETRY_COUNT = 3;
```

### 反模式
- ❌ 单字母变量（循环 i/j/k 除外）— 可读性差
- ❌ 无意义前缀 `m_`, `str`, `arr` — 匈牙利标记法已过时
- ❌ 泛化名称 `temp`, `data`, `info`, `result` — 名不副实
