# 错误处理模式记录

本目录用于存储错误处理设计模式的记录，包括异常层次结构、错误传播、重试策略、熔断模式、降级策略等。

## 记录格式

```json
{
  "id": "PAT-EH-YYYYMMDD-NNN",
  "timestamp": "ISO8601时间戳",
  "patternName": "模式名称",
  "patternType": "异常层次|错误传播|重试|熔断|降级|补偿|兜底",
  "description": "模式描述",
  "problem": "解决的问题",
  "solution": "解决方案",
  "applicableScenario": "适用场景",
  "implementation": "实现要点",
  "examples": ["代码示例或伪代码"],
  "advantages": ["优势列表"],
  "disadvantages": ["劣势列表"],
  "relatedPatterns": ["关联模式"],
  "references": ["参考来源"]
}
```

## 示例记录

```json
{
  "id": "PAT-EH-20260428-001",
  "timestamp": "2026-04-28T15:30:00.000Z",
  "patternName": "熔断器模式(Circuit Breaker)",
  "patternType": "熔断",
  "description": "当下游服务故障率超过阈值时自动切断请求，避免故障蔓延，定期探测恢复",
  "problem": "下游服务不可用时请求持续堆积，导致线程池耗尽和级联故障",
  "solution": "统计失败率，超过阈值进入Open状态拒绝请求，定时探测后进入Half-Open状态试探恢复",
  "applicableScenario": "微服务间远程调用、第三方API集成、数据库连接等可能故障的外部依赖",
  "implementation": "使用状态机管理Closed/Open/Half-Open三种状态，滑动窗口统计失败率",
  "examples": ["circuitBreaker.execute(() => paymentService.charge(order))"],
  "advantages": ["防止级联故障", "自动恢复探测", "保护系统稳定性"],
  "disadvantages": ["需要合理配置阈值", "探测期间部分请求可能被拒绝"],
  "relatedPatterns": ["重试模式", "限流模式", "降级模式"],
  "references": ["Michael Nygard - Release It!"]
}
```
