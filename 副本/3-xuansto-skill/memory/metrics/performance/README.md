# 性能指标记录

本目录用于存储系统性能相关指标的采集记录，包括响应时间、吞吐量、并发能力、资源利用率等。

## 记录格式

```json
{
  "id": "MET-PF-YYYYMMDD-NNN",
  "timestamp": "ISO8601时间戳",
  "metricCategory": "响应时间|吞吐量|并发|资源利用率",
  "metricName": "指标名称",
  "value": "指标值",
  "unit": "单位",
  "percentile": "P50|P90|P95|P99|P999",
  "benchmark": "基准值",
  "threshold": "阈值",
  "environment": "采集环境",
  "serviceName": "服务名称",
  "dataSource": "数据来源",
  "tags": ["标签列表"],
  "status": "normal|warning|critical"
}
```

## 示例记录

```json
{
  "id": "MET-PF-20260428-001",
  "timestamp": "2026-04-28T12:00:00.000Z",
  "metricCategory": "响应时间",
  "metricName": "API网关请求延迟",
  "value": 156,
  "unit": "ms",
  "percentile": "P99",
  "benchmark": "200ms",
  "threshold": "500ms",
  "environment": "production",
  "serviceName": "api-gateway",
  "dataSource": "Prometheus + Grafana",
  "tags": ["latency", "gateway", "p99"],
  "status": "normal"
}
```
