# 运行时错误记录

本目录用于存储应用运行期间发生的错误记录，包括未捕获异常、内存溢出、线程死锁等运行时问题。

## 记录格式

```json
{
  "id": "ERR-RT-YYYYMMDD-NNN",
  "timestamp": "ISO8601时间戳",
  "severity": "critical|high|medium|low",
  "errorType": "异常类型",
  "message": "错误消息",
  "stackTrace": "堆栈跟踪",
  "context": {
    "module": "所属模块",
    "function": "所属函数",
    "inputData": "触发输入数据"
  },
  "environment": {
    "os": "操作系统",
    "runtime": "运行时版本",
    "memoryUsage": "内存使用量"
  },
  "resolution": "解决方式",
  "status": "open|investigating|resolved"
}
```

## 示例记录

```json
{
  "id": "ERR-RT-20260428-001",
  "timestamp": "2026-04-28T10:23:45.000Z",
  "severity": "critical",
  "errorType": "OutOfMemoryError",
  "message": "堆内存溢出：处理批量数据时超出4GB限制",
  "stackTrace": "at DataProcessor.batchProcess(DataProcessor.js:142)\nat Pipeline.run(Pipeline.js:87)",
  "context": {
    "module": "data-processor",
    "function": "batchProcess",
    "inputData": "batchSize=100000"
  },
  "environment": {
    "os": "Windows Server 2022",
    "runtime": "Node.js 20.11.0",
    "memoryUsage": "4096MB"
  },
  "resolution": "实现流式处理替代批量加载",
  "status": "resolved"
}
```
