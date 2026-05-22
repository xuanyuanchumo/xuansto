# 编译错误记录

本目录用于存储编译阶段产生的错误记录，包括语法错误、类型不匹配、依赖缺失、构建配置问题等。

## 记录格式

```json
{
  "id": "ERR-CP-YYYYMMDD-NNN",
  "timestamp": "ISO8601时间戳",
  "severity": "critical|high|medium|low",
  "errorType": "语法错误|类型错误|依赖错误|配置错误",
  "message": "编译器错误消息",
  "file": "源文件路径",
  "line": "行号",
  "column": "列号",
  "compiler": "编译器名称及版本",
  "buildTarget": "构建目标",
  "suggestion": "修复建议",
  "resolution": "解决方式",
  "status": "open|investigating|resolved"
}
```

## 示例记录

```json
{
  "id": "ERR-CP-20260428-001",
  "timestamp": "2026-04-28T09:15:30.000Z",
  "severity": "high",
  "errorType": "类型错误",
  "message": "Type 'string' is not assignable to parameter of type 'number'",
  "file": "src/services/calculation.ts",
  "line": 47,
  "column": 23,
  "compiler": "TypeScript 5.4.2",
  "buildTarget": "es2022",
  "suggestion": "检查函数参数类型，添加类型转换或修正调用方传参",
  "resolution": "在调用处添加Number()类型转换",
  "status": "resolved"
}
```
