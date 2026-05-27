# 测试失败记录

本目录用于存储测试执行过程中的失败记录，包括单元测试失败、集成测试失败、断言错误、测试超时等。

## 记录格式

```json
{
  "id": "ERR-TS-YYYYMMDD-NNN",
  "timestamp": "ISO8601时间戳",
  "severity": "critical|high|medium|low",
  "testSuite": "测试套件名称",
  "testCase": "测试用例名称",
  "errorType": "断言失败|超时|异常|跳过",
  "message": "失败消息",
  "expected": "期望值",
  "actual": "实际值",
  "stackTrace": "堆栈跟踪",
  "testFramework": "测试框架及版本",
  "relatedCode": "关联源代码路径",
  "resolution": "解决方式",
  "status": "open|investigating|resolved"
}
```

## 示例记录

```json
{
  "id": "ERR-TS-20260428-001",
  "timestamp": "2026-04-28T11:05:22.000Z",
  "severity": "high",
  "testSuite": "UserService.test.ts",
  "testCase": "should create user with valid data",
  "errorType": "断言失败",
  "message": "Expected status 201 but received 500",
  "expected": "201",
  "actual": "500",
  "stackTrace": "at Object.<anonymous> (UserService.test.ts:34:18)",
  "testFramework": "Jest 29.7.0",
  "relatedCode": "src/services/UserService.ts",
  "resolution": "修复数据库连接池配置，确保测试环境数据库可用",
  "status": "resolved"
}
```
