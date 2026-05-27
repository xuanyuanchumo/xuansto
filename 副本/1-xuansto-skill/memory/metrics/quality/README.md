# 质量指标记录

本目录用于存储代码质量相关指标的采集记录，包括代码覆盖率、缺陷密度、代码复杂度、技术债务等。

## 记录格式

```json
{
  "id": "MET-QA-YYYYMMDD-NNN",
  "timestamp": "ISO8601时间戳",
  "metricCategory": "测试覆盖率|缺陷密度|代码复杂度|技术债务|代码重复率",
  "metricName": "指标名称",
  "value": "指标值",
  "unit": "单位",
  "benchmark": "基准值",
  "threshold": "阈值",
  "scope": "指标范围(module|service|system)",
  "targetModule": "目标模块",
  "dataSource": "数据来源工具",
  "trend": "improving|stable|declining",
  "tags": ["标签列表"],
  "status": "normal|warning|critical"
}
```

## 示例记录

```json
{
  "id": "MET-QA-20260428-001",
  "timestamp": "2026-04-28T09:00:00.000Z",
  "metricCategory": "测试覆盖率",
  "metricName": "行覆盖率",
  "value": 87.3,
  "unit": "%",
  "benchmark": "80%",
  "threshold": "70%",
  "scope": "service",
  "targetModule": "order-service",
  "dataSource": "SonarQube 10.3",
  "trend": "improving",
  "tags": ["coverage", "unit-test", "order"],
  "status": "normal"
}
```
