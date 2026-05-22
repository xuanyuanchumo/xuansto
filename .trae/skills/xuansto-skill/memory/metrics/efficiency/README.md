# 效率指标记录

本目录用于存储开发效率相关指标的采集记录，包括交付周期、部署频率、变更前置时间、变更失败率等。

## 记录格式

```json
{
  "id": "MET-EF-YYYYMMDD-NNN",
  "timestamp": "ISO8601时间戳",
  "metricCategory": "交付周期|部署频率|变更前置时间|变更失败率|恢复时间|开发速率",
  "metricName": "指标名称",
  "value": "指标值",
  "unit": "单位",
  "benchmark": "基准值",
  "threshold": "阈值",
  "team": "团队名称",
  "sprint": "迭代周期",
  "period": "统计周期",
  "dataSource": "数据来源工具",
  "trend": "improving|stable|declining",
  "tags": ["标签列表"],
  "status": "normal|warning|critical"
}
```

## 示例记录

```json
{
  "id": "MET-EF-20260428-001",
  "timestamp": "2026-04-28T08:00:00.000Z",
  "metricCategory": "部署频率",
  "metricName": "生产环境日均部署次数",
  "value": 4.2,
  "unit": "次/天",
  "benchmark": "3次/天",
  "threshold": "1次/天",
  "team": "平台工程组",
  "sprint": "Sprint 2026-17",
  "period": "周平均",
  "dataSource": "Jenkins + ArgoCD",
  "trend": "improving",
  "tags": ["dora", "deploy-frequency", "ci-cd"],
  "status": "normal"
}
```
