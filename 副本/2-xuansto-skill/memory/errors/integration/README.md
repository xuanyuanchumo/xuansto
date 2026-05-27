# 集成错误记录

本目录用于存储系统集成过程中产生的错误记录，包括接口不兼容、数据格式不匹配、第三方服务异常、消息队列故障等。

## 记录格式

```json
{
  "id": "ERR-IG-YYYYMMDD-NNN",
  "timestamp": "ISO8601时间戳",
  "severity": "critical|high|medium|low",
  "errorType": "接口不兼容|数据格式错误|第三方异常|协议错误|超时",
  "message": "错误消息",
  "sourceService": "调用方服务",
  "targetService": "被调用方服务",
  "endpoint": "接口路径",
  "requestPayload": "请求负载摘要",
  "responseCode": "响应状态码",
  "responseMessage": "响应消息",
  "contractVersion": "契约版本",
  "resolution": "解决方式",
  "status": "open|investigating|resolved"
}
```

## 示例记录

```json
{
  "id": "ERR-IG-20260428-001",
  "timestamp": "2026-04-28T16:45:10.000Z",
  "severity": "high",
  "errorType": "数据格式错误",
  "message": "支付服务返回的金额字段为字符串，期望数值类型",
  "sourceService": "order-service",
  "targetService": "payment-service",
  "endpoint": "/api/v2/payments/refund",
  "requestPayload": "{\"orderId\":\"ORD-20260428-001\",\"amount\":99.9}",
  "responseCode": "200",
  "responseMessage": "refundAmount字段返回\"99.90\"而非99.90",
  "contractVersion": "v2.1.0",
  "resolution": "在order-service中添加字段类型转换适配层，同步更新契约至v2.1.1",
  "status": "resolved"
}
```
