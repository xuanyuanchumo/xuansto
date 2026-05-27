# 部署错误记录

本目录用于存储部署过程中产生的错误记录，包括环境配置错误、容器启动失败、服务发现异常、资源不足等。

## 记录格式

```json
{
  "id": "ERR-DP-YYYYMMDD-NNN",
  "timestamp": "ISO8601时间戳",
  "severity": "critical|high|medium|low",
  "errorType": "配置错误|启动失败|资源不足|权限错误|网络错误",
  "message": "错误消息",
  "environment": "部署环境",
  "platform": "部署平台",
  "version": "部署版本",
  "logs": "关键日志片段",
  "rollbackNeeded": true,
  "affectedServices": ["受影响服务列表"],
  "resolution": "解决方式",
  "status": "open|investigating|resolved"
}
```

## 示例记录

```json
{
  "id": "ERR-DP-20260428-001",
  "timestamp": "2026-04-28T14:30:00.000Z",
  "severity": "critical",
  "errorType": "启动失败",
  "message": "容器健康检查失败：端口8080未在60秒内响应",
  "environment": "production",
  "platform": "Kubernetes 1.29",
  "version": "v2.3.1",
  "logs": "Liveness probe failed: Get http://10.0.1.5:8080/health: dial tcp 10.0.1.5:8080: connect: connection refused",
  "rollbackNeeded": true,
  "affectedServices": ["api-gateway", "user-service"],
  "resolution": "回滚至v2.3.0，修复数据库迁移脚本后重新部署",
  "status": "resolved"
}
```
