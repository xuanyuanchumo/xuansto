# 热修复记录

本目录用于存储生产环境紧急热修复记录，包括故障现象、应急方案、修复时间线及后续跟进措施。

## 记录格式

```json
{
  "id": "FIX-HF-YYYYMMDD-NNN",
  "timestamp": "ISO8601时间戳",
  "incidentId": "关联事件编号",
  "severity": "critical|high",
  "summary": "热修复摘要",
  "symptom": "故障现象描述",
  "impactScope": "影响范围",
  "affectedUsers": "受影响用户数估算",
  "hotfixDescription": "热修复方案",
  "changedFiles": ["变更文件列表"],
  "deployTime": "热修复部署时间",
  "recoveryTime": "服务恢复时间",
  "followUpAction": "后续跟进措施",
  "permanentFix": "永久修复计划",
  "status": "deployed|permanent-fixed|monitoring"
}
```

## 示例记录

```json
{
  "id": "FIX-HF-20260428-001",
  "timestamp": "2026-04-28T03:15:00.000Z",
  "incidentId": "INC-20260428-007",
  "severity": "critical",
  "summary": "支付接口SSL证书过期导致交易全部失败",
  "symptom": "所有支付请求返回SSL握手失败错误",
  "impactScope": "全站支付功能不可用",
  "affectedUsers": "约12000",
  "hotfixDescription": "紧急更新SSL证书配置并重启支付网关服务",
  "changedFiles": ["config/ssl/cert-config.json"],
  "deployTime": "2026-04-28T03:45:00.000Z",
  "recoveryTime": "2026-04-28T03:52:00.000Z",
  "followUpAction": "配置证书自动续期监控告警",
  "permanentFix": "集成Let's Encrypt自动续期，添加证书过期提前7天告警",
  "status": "permanent-fixed"
}
```
