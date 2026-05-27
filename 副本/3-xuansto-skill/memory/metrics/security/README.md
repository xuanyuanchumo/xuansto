# 安全指标记录

本目录用于存储安全相关指标的采集记录，包括漏洞数量、漏洞修复时间、安全扫描通过率、合规达标率等。

## 记录格式

```json
{
  "id": "MET-SC-YYYYMMDD-NNN",
  "timestamp": "ISO8601时间戳",
  "metricCategory": "漏洞统计|修复时效|扫描通过率|合规达标率|安全事件",
  "metricName": "指标名称",
  "value": "指标值",
  "unit": "单位",
  "benchmark": "基准值",
  "threshold": "阈值",
  "severity": "critical|high|medium|low",
  "scanType": "SAST|DAST|SCA|容器扫描|基础设施扫描",
  "serviceName": "服务名称",
  "dataSource": "数据来源工具",
  "trend": "improving|stable|declining",
  "tags": ["标签列表"],
  "status": "normal|warning|critical"
}
```

## 示例记录

```json
{
  "id": "MET-SC-20260428-001",
  "timestamp": "2026-04-28T06:00:00.000Z",
  "metricCategory": "漏洞统计",
  "metricName": "高危漏洞数量",
  "value": 2,
  "unit": "个",
  "benchmark": "0个",
  "threshold": "3个",
  "severity": "high",
  "scanType": "SCA",
  "serviceName": "payment-service",
  "dataSource": "Snyk + Trivy",
  "trend": "declining",
  "tags": ["vulnerability", "sca", "high-severity", "payment"],
  "status": "warning"
}
```
