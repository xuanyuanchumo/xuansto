---
id: naming-conventions
type: knowledge
category: standards
tags: [命名规范, camelCase, snake_case, PascalCase, 代码风格]
version: 1.0.0
created: 2026-04-28
updated: 2026-04-28
confidence: high
---

# 命名约定规范

## 命名风格

| 风格 | 格式 | 示例 | 典型用途 |
|------|------|------|----------|
| camelCase | 首词小写后续大写 | `userName` | JS/TS 变量、函数 |
| PascalCase | 每词首字母大写 | `UserService` | 类名、组件名、类型 |
| snake_case | 下划线分隔小写 | `user_name` | Python 变量、数据库列 |
| SCREAMING_SNAKE | 下划线分隔大写 | `MAX_RETRY` | 常量 |
| kebab-case | 短横线分隔小写 | `user-profile` | URL、CSS 类名、文件名 |

## 各语言惯例

- **JavaScript/TypeScript**：变量/函数 camelCase，类/接口/类型 PascalCase，常量 SCREAMING_SNAKE，文件 kebab-case 或 camelCase
- **Python**：变量/函数 snake_case，类 PascalCase，常量 SCREAMING_SNAKE，模块 snake_case
- **Java**：变量/方法 camelCase，类 PascalCase，常量 SCREAMING_SNAKE，包名全小写
- **Rust**：变量/函数 snake_case，类型/ trait PascalCase，常量 SCREAMING_SNAKE
- **Go**：导出标识符 PascalCase，未导出 camelCase，接口名加 -er 后缀（Reader, Writer）

## 通用原则

- **意图明确**：名称应表达用途而非实现，`fetchUsers` 优于 `getData`
- **避免缩写**：使用 `configuration` 而非 `cfg`，通用缩写除外（`id`, `url`, `http`）
- **布尔变量**：使用 is/has/can/should 前缀，如 `isValid`, `hasPermission`
- **函数命名**：动词开头，`get/set/create/delete/update/find/handle/on`
- **类命名**：名词，体现职责，如 `UserRepository`, `PaymentService`
- **接口命名**：行为描述加 able/ible 后缀或 I 前缀，如 `Serializable`, `IComparable`

## 反模式

- 单字母变量（循环变量 i/j/k 除外）
- 无意义前缀（`m_`, `str`, `arr` 等匈牙利标记法）
- 名不副实（`temp`, `data`, `info`, `result` 等过于泛化的名称）
- 同义词混用（get/fetch/retrieve 随意切换）
