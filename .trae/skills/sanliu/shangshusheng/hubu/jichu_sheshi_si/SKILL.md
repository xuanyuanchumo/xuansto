---
name: jichu_sheshi_si
description: 基础设施司，负责CI/CD流水线、容器化部署、云资源管理。构建稳定高效的工程基础设施。
---
# 基础设施司技能指令

## 职责
- CI/CD流水线设计、搭建与维护
- 容器化（Docker/K8s）配置与管理
- 云资源（计算/存储/网络）规划与运维
- 基础设施即代码（IaC）管理
- 环境可用性与灾难恢复

## CI/CD流水线架构

### 流水线阶段

```
代码提交 → Lint → 单元测试 → 构建 → 安全扫描 → 集成测试
                                                    ↓
                                              E2E测试 ← 部署(staging)
                                                    ↓
                                              验收测试 → 部署(prod)
                                                    ↓
                                              监控 & 回滚准备
```

### 流水线配置示例

```yaml
pipeline_stages:
  - name: "code_quality"
    steps: [lint, format_check, complexity_check]
    fail_fast: true

  - name: "unit_test"
    steps: [pytest, coverage_report]
    threshold:
      coverage_min: 80%

  - name: "security_scan"
    steps: [dependency_audit, secret_scan, sast]
    block_on: ["critical", "high"]

  - name: "build"
    steps: [docker_build, image_push]
    cache_strategy: "layered"

  - name: "deploy_staging"
    environment: "staging"
    strategy: "blue_green"
    health_check: "/health"
    rollback_on_failure: true

  - name: "e2e_test"
    environment: "staging"
    parallel: true
    suites: [smoke, regression, performance]

  - name: "deploy_prod"
    environment: "production"
    approval_required: true
    strategy: "canary"
    canary_percent: 10
    increment_percent: 20
    monitor_duration_minutes: 15
```

## 容器化规范

### Dockerfile最佳实践

```dockerfile
FROM python:3.12-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.12-slim AS runtime
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY . .
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s CMD curl -f http://localhost:8000/health || exit 1
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### K8s资源配置

```yaml
resources:
  requests:
    cpu: "250m"
    memory: "256Mi"
  limits:
    cpu: "500m"
    memory: "512Mi"

livenessProbe:
  httpGet:
    path: /health/live
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /health/ready
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5
```

## 工作流程

```
1. 接收基础设施需求（新服务/扩容/迁移）
2. 设计基础设施架构方案
3. 编写IaC配置（Terraform/Helm/Kustomize）
4. Code Review基础设施代码
5. 在预发环境验证
6. 执行部署
7. 配置监控和告警
8. 编写运维手册
9. 记录架构决策到DecisionLog
```

## 可靠性目标

| 指标 | 目标值 | 度量方式 |
|------|--------|----------|
| 可用性(SLA) | ≥99.9% | 月度统计 |
| 平均恢复时间(MTTR) | ≤30分钟 | 故障记录 |
| 部署成功率 | ≥98% | 流水线统计 |
| 回滚成功率 | 100% | 回滚演练 |

## 协同接口

| 接口 | 描述 | 调用方 |
|------|------|--------|
| `create_pipeline` | 创建流水线 | 新项目启动 |
| `deploy_service` | 服务部署 | 发布流程 |
| `scale_resource` | 资源伸缩 | 资源优化司 |
| `disaster_recovery` | 灾难恢复 | 应急响应 |
