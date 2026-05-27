# CI/CD集成参考文档

## Core Points
- CI/CD流水线架构：代码提交→构建→测试→部署四阶段，每阶段含多个子步骤
- 质量门禁集成：构建门禁(编译/类型检查)、测试门禁(单元/集成/E2E)、安全门禁(SAST/DAST)、部署门禁(健康检查)
- 部署策略：蓝绿部署、金丝雀发布、滚动更新，支持自动回滚
- 监控集成：Prometheus指标采集、Grafana仪表盘、Sentry错误追踪、ELK日志聚合

## Applicable Scenarios
- CI/CD Specialist Agent设计流水线配置
- 配置质量门禁和部署策略
- 集成监控和告警系统
