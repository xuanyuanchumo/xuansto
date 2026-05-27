# DevOps知识库

> 分类: 通用知识库 > DevOps规范 | 版本: 1.0.0 | 更新日期: 2026-04-29

## 知识分类

### CI/CD流水线

持续集成与持续部署的最佳实践和规范。

- 流水线设计模式（阶段划分、并行策略、条件执行）
- 构建工具集成（Webpack/Vite/esbuild/Rollup）
- 制品管理与版本发布（语义化版本、变更日志自动生成）
- 部署策略（蓝绿部署、金丝雀发布、滚动更新）
- 回滚机制与故障恢复

### 容器化

容器化部署与编排规范。

- Docker镜像构建最佳实践（多阶段构建、镜像精简、安全基线）
- Docker Compose服务编排
- Kubernetes部署与运维（Pod/Deployment/Service/Ingress）
- 容器安全（镜像扫描、最小权限、网络策略）
- 桌面应用容器化构建环境

### 基础设施即代码（IaC）

基础设施的声明式管理与自动化。

- Terraform/HCL资源配置
- AWS CDK / Pulumi编程式基础设施
- 环境隔离与配置管理（dev/staging/prod）
- 密钥与敏感信息管理（Vault/KMS）
- GitOps工作流（ArgoCD/Flux）

### 监控与可观测性

系统监控、日志和追踪的规范与实践。

- 指标监控（Prometheus/Grafana/Datadog）
- 日志管理（ELK/Loki/结构化日志）
- 分布式追踪（OpenTelemetry/Jaeger）
- 告警策略与升级机制
- SLA/SLO/SLI定义与跟踪
- 桌面应用遥测与崩溃报告
