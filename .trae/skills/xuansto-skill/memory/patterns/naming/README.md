# 命名模式记录

本目录用于存储项目命名约定与模式的记录，包括变量命名、函数命名、类命名、文件命名、常量命名等规范。

## 记录格式

```json
{
  "id": "PAT-NM-YYYYMMDD-NNN",
  "timestamp": "ISO8601时间戳",
  "category": "变量|函数|类|文件|常量|接口|枚举|模块",
  "language": "编程语言",
  "patternName": "模式名称",
  "convention": "命名约定描述",
  "format": "命名格式",
  "examples": ["示例列表"],
  "antiPatterns": ["反模式列表"],
  "rationale": "设计理由",
  "applicableScope": "适用范围",
  "references": ["参考来源"]
}
```

## 示例记录

```json
{
  "id": "PAT-NM-20260428-001",
  "timestamp": "2026-04-28T10:00:00.000Z",
  "category": "函数",
  "language": "TypeScript",
  "patternName": "动词前缀函数命名",
  "convention": "函数名以动词开头，清晰表达行为意图",
  "format": "动词+名词(可选修饰词)，camelCase",
  "examples": ["getUserById", "calculateTotalPrice", "validateEmail", "hasPermission"],
  "antiPatterns": ["userData", "price", "emailCheck"],
  "rationale": "动词前缀使函数意图一目了然，提高代码可读性和可维护性",
  "applicableScope": "所有TypeScript项目中的函数声明",
  "references": ["Clean Code - Robert C. Martin"]
}
```
