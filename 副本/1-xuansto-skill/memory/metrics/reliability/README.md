# 可靠性指标记录

本目录用于存储系统可靠性相关指标的采集记录，包括可用性、MTBF、MTTR、错误率、SLA达标率等。

## 记录格式

```json
{
  "id": "MET-RL-YYYYMMDD-NNN",
  "timestamp": "ISO8601时间戳",
  "metricCategory": "可用性|MTBF|MTTR|错误率|SLA达标率|RPO|RTO",
  "metricName": "指标名称",
  "value": "指标值",
  "unit": "单位",
  "benchmark": "基准值",
  "threshold": "阈值",
  "serviceName": "服务名称",
  "environment": "采集环境",
  "measurementPeriod": "测量周期",
  "dataSource": "数据来源工具",
  "trend": "improving|stable|declining",
  "tags": ["标签列表"],
  "status": "normal|warning|critical"
}
```

## 示例记录

```json
{
  "id": "MET-RL-20260428-001",
  "timestamp": "2026-04-28T07:00:00.000Z",
  "metricCategory": "可用性",
  "metricName": "核心服务月度可用性",
  "value": 99.97,
  "unit": "%",
  "benchmark": "99.95%",
  "threshold": "99.9%",
  "serviceName": "user-service",
  "environment": "production",
  "measurementPeriod": "2026年4月",
  "dataSource": "Datadog APM",
  "trend": "stable",
  "tags": ["availability", "sla", "core-service"],
  "status": "normal"
}
```
