<!--
  模板说明: Deployment Guide (部署手册)
  用途: 完整的部署操作指南，包含环境要求、逐步操作命令、配置管理、回滚方案和运维手册
  变量列表:
    {{project_name}}           - 项目名称
    {{version}}                - 部署版本
    {{environment}}            - 目标环境(DEV/TEST/STAGE/PROD)
    {{domain}}                 - 域名
    {{deployment_server}}      - 部署目标服务器
    {{docker_registry}}        - Docker镜像仓库
    {{k8s_cluster}}            - Kubernetes集群信息
    {{database_host}}          - 数据库地址
    {{redis_host}}             - Redis地址
    {{oss_bucket}}             - OSS存储桶
  使用方式: 部署前仔细阅读，按步骤执行。生产环境部署需至少2人复核
-->

# {{project_name | default('[项目名称]')}} — 部署手册

> **版本**: {{version | default('v1.0.0')}} | **目标环境**: {{environment | default('PRODUCTION')}}
> **编写人**: {{author | default('[DevOps工程师]')}} | **更新日期**: {{date | default('YYYY-MM-DD')}}

---

## ⚠️ 部署前必读

> **🔴 生产环境部署注意事项**:
> 1. 必须在业务低峰期执行（建议凌晨2:00-5:00）
> 2. 至少2人在线：一人操作、一人复核
> 3. 提前通知所有相关方（产品/运营/客服）
> 4. 准备好回滚预案并确认回滚脚本可用
> 5. 部署全程保留操作日志

---

## 📋 目录

- [1. 部署架构概览](#1-部署架构概览)
- [2. 前置条件](#2-前置条件)
- [3. 环境变量与配置](#3-环境变量与配置)
- [4. 部署步骤](#4-部署步骤)
- [5. 健康检查](#5-健康检查)
- [6. 回滚步骤](#6-回滚步骤)
- [7. 运维手册](#7-运维手册)
- [8. 故障排查指南](#8-故障排查指南)

---

## 1. 部署架构概览

### 1.1 环境拓扑图

```mermaid
graph TB
    subgraph Internet["🌐 互联网"]
        Users["用户"]
    end

    subgraph CDN["☁️ CDN Layer"]
        CDNNode["阿里云CDN<br/>静态资源加速<br/>domain: cdn.{{domain | default('example.com')}}"]
    end

    subgraph LB["⚖️ 负载均衡层"]
        SLB["SLB 负载均衡<br/>阿里云SLB / Nginx<br/>HTTPS终止<br/>端口: 443"]
    end

    subgraph K8s["🏗️ Kubernetes Cluster<br/>{{k8s_cluster | default('prod-cluster')}}"]
        subgraph Ingress["Ingress Controller"]
            IngressCtrl["Nginx Ingress<br/>路由规则/限流"]
        end

        subgraph Backend["应用节点 (3副本)"]
            Pod1["Pod: backend-v{{version | default('1.0')}}-xxx1<br/>:8080"]
            Pod2["Pod: backend-v{{version | default('1.0')}}-xxx2<br/>:8080"]
            Pod3["Pod: backend-v{{version | default('1.0')}}-xxx3<br/>:8080"]
        end
    end

    subgraph Data["💾 数据层"]
        PG[(PostgreSQL<br/>主: pg-master<br/>从: pg-slave)]
        Redis[(Redis Cluster<br/>6节点)]
        OSS[(OSS<br/>bucket: {{oss_bucket | default('skiller-prod')}}")]
    end

    subgraph MQ["📨 消息队列"]
        Kafka[(Kafka Cluster<br/>3 Broker)]
    end

    Users -->|"HTTPS"| SLB
    SLB --> IngressCtrl
    IngressCtrl --> Pod1 & Pod2 & Pod3
    Users -.->|静态资源| CDNNode
    Pod1 & Pod2 & Pod3 --> PG & Redis & OSS & Kafka
```

### 1.2 基础设施清单

| 组件 | 规格/配置 | 数量 | 提供商 | 内网IP |
|------|-----------|------|--------|--------|
| K8s Master | 4C8G | 3 | 阿里云ACK | 10.0.1.10~12 |
| K8s Worker | 8C16G | 3 | 阿里云ECS | 10.0.2.10~12 |
| PostgreSQL | 4C16G SSD云盘 | 1主+1从 | 云数据库RDS | 10.0.3.10 |
| Redis Cluster | 2G内存×6节点 | 6 | 云数据库Redis | 10.0.4.10~15 |
| Kafka | 4C8G | 3 | 自建K8s部署 | 10.0.5.10~12 |
| OSS | 标准型 | 1 Bucket | 阿里云OSS | - |
| SLB | 性能共享型 | 1 | 阿里云SLB | 公网IP |

---

## 2. 前置条件

### 2.1 硬件要求

| 资源 | 最低配置 | 推荐配置 | 当前环境 |
|------|----------|----------|----------|
| **CPU** | 4核 | 8核+ | ✅ 8核 |
| **内存** | 8GB | 16GB+ | ✅ 16GB |
| **磁盘** | 100GB SSD | 200GB SSD+ | ✅ 200GB SSD |
| **网络带宽** | 10Mbps | 50Mbps+ | ✅ 50Mbps |
| **操作系统** | Ubuntu 22.04 / CentOS 8+ | Ubuntu 22.04 LTS | ✅ Ubuntu 22.04 |

### 2.2 软件依赖

| 软件 | 版本要求 | 安装方式 | 验证命令 |
|------|----------|----------|----------|
| Docker | ≥ 24.0 | 包管理器安装 | `docker --version` |
| Kubernetes kubectl | ≥ 1.28 | 二进制下载 | `kubectl version --client` |
| Helm | ≥ 3.12 | 二进制下载 | `helm version` |
| Git | ≥ 2.40 | 包管理器 | `git --version` |
| OpenSSL | ≥ 3.0 | 系统自带 | `openssl version` |

### 2.3 权限要求

| 权限项 | 说明 | 验证方式 |
|--------|------|----------|
| K8s集群访问权限 | kubeconfig已配置且有效 | `kubectl get nodes` |
| Docker镜像仓库推送权限 | 已登录registry | `docker pull {{docker_registry | default('registry.example.com')}}/backend:latest` |
| 数据库迁移权限 | Flyway/Liquibase有DDL权限 | 连接数据库执行 `SELECT 1` |
| DNS解析权限 | 可修改域名DNS记录 | 登录域名控制台确认 |
| SSL证书 | 证书未过期且已部署到LB | `openssl s_client -connect api.{{domain | default('example.com')}}:443` |

### 2.4 部署前置检查清单

<!-- COMMENT: 部署前逐项确认 -->

| # | 检查项 | 命令/方式 | 预期结果 | 状态 |
|---|--------|-----------|----------|:----:|
| PC-01 | K8s集群健康 | `kubectl get nodes` | 所有节点Ready | ☐ |
| PC-02 | 磁盘空间充足 | `df -h /` | 可用空间 > 20GB | ☐ |
| PC-03 | 内存充足 | `free -h` | 可用 > 4GB | ☐ |
| PC-04 | 数据库可连接 | `pg_isready -h {{db_host}} -p 5432` | 返回OK | ☐ |
| PC-05 | Redis可连接 | `redis-cli -h {{redis_host}} ping` | 返回PONG | ☐ |
| PC-06 | 镜像仓库可访问 | `docker pull registry/skiller-backend:latest` | 成功拉取 | ☐ |
| PC-07 | 当前版本运行正常 | `curl -sf https://api.{{domain}}/health` | 返回200 | ☐ |
| PC-08 | CI流水线构建成功 | GitHub Actions绿色 | Build + Test通过 | ☐ |
| PC-09 | 测试报告已审批 | 测试报告签字 | UAT通过 | ☐ |
| PC-10 | 回滚镜像可用 | `docker pull registry/skiller-backend:v{{prev_version}}` | 成功拉取 | ☐ |
| PC-11 | 备份已完成 | 自动备份任务日志 | 最新备份时间<24h | ☐ |
| PC-12 | 相关方已通知 | 邮件/钉钉通知记录 | 收到确认回复 | ☐ |

> ⚠️ 以上全部为 ☑ 后方可开始部署！

---

## 3. 环境变量与配置

### 3.1 配置文件结构

```
config/
├── .env.production          # 生产环境变量 (加密存储于K8s Secret)
├── application-prod.yml     # Spring Boot 生产配置
├── nginx.conf               # Nginx/Ingress 配置
└── kubernetes/
    ├── namespace.yaml
    ├── configmap.yaml       # 非敏感配置
    ├── secret.yaml          # 敏感配置(加密)
    ├── deployment.yaml
    ├── service.yaml
    ├── ingress.yaml
    └── hpa.yaml             # 自动扩缩容
```

### 3.2 核心环境变量

```bash
# ============================================
# 应用配置 (Application Config)
# ============================================

# 服务端口号
SERVER_PORT=8080
# Spring Profile
SPRING_PROFILES_ACTIVE=prod

# ============================================
# 数据库配置 (Database)
# ============================================
SPRING_DATASOURCE_URL=jdbc:postgresql://{{db_host | default('pg-master.prod.internal')}}:5432/{{db_name | default('skiller_db')}}
SPRING_DATASOURCE_USERNAME=${DB_USERNAME}
SPRING_DATASOURCE_PASSWORD=${DB_PASSWORD}
SPRING_DATASOURCE_HIKARI_MAXIMUM_POOL_SIZE=20
SPRING_DATASOURCE_HIKARI_MINIMUM_IDLE=5

# ============================================
# Redis配置 (Cache)
# ============================================
SPRING_DATA_REDIS_HOST={{redis_host | default('redis-cluster.prod.internal')}}
SPRING_DATA_REDIS_PORT=6379
SPRING_DATA_REDIS_PASSWORD=${REDIS_PASSWORD}
SPRING_DATA_REDIS_DATABASE=0
SPRING_DATA_REDIS_TIMEOUT=3000ms

# ============================================
# JWT配置 (Security)
# ============================================
JWT_SECRET=${JWT_SECRET_KEY}
JWT_ACCESS_TOKEN_EXPIRATION_MS=900000        # 15分钟
JWT_REFRESH_TOKEN_EXPIRATION_MS=604800000   # 7天
JWT_ISSUER={{project_name | default('skiller')}}

# ============================================
# 文件存储 (OSS)
# ============================================
OSS_ENDPOINT=https://oss-cn-hangzhou.aliyuncs.com
OSS_ACCESS_KEY_ID=${OSS_AK}
OSS_ACCESS_KEY_SECRET=${OSS_SK}
OSS_BUCKET_NAME={{oss_bucket | default('skiller-prod')}}

# ============================================
# 第三方服务 (Third-party Services)
# ============================================
# 短信服务
ALIYUN_SMS_ACCESS_KEY_ID=${SMS_AK}
ALIYUN_SMS_ACCESS_KEY_SECRET=${SMS_SK}
ALIYUN_SMS_SIGN_NAME=【{{project_name | default('公司名')}}】
ALIYUN_SMS_TEMPLATE_CODE_REGISTER=SMS_123456789

# 支付宝
ALIPAY_APP_ID=${ALIPAY_APP_ID}
ALIPAY_PRIVATE_KEY=${ALIPAY_PRIVATE_KEY}
ALIPAY_PUBLIC_KEY=${ALIPAY_PUBLIC_KEY}
ALIPAY_NOTIFY_URL=https://api.{{domain | default('example.com')}}/api/v1/payments/callback/alipay

# 微信支付
WXPAY_MCH_ID=${WX_MCH_ID}
WXPAY_API_KEY=${WX_API_KEY}
WXPAY_NOTIFY_URL=https://api.{{domain | default('example.com')}}/api/v1/payments/callback/wechat

# ============================================
# 日志配置 (Logging)
# ============================================
LOGGING_LEVEL_ROOT=INFO
LOGGING_LEVEL_COM_EXAMPLE=DEBUG
LOGBACK_FILE_PATH=/var/log/{{project_name | lower | default('skiller')}}

# ============================================
# 监控配置 (Observability)
# ============================================
MANAGEMENT_ENDPOINTS_WEB_EXPOSURE_INCLUDE=health,info,metrics,prometheus
MANAGEMENT_METRICS_EXPORT_PROMETHEUS_ENABLED=true
APPLICATION_INSIGHTS_CONNECTION_STRING=${APPINSIGHTS_KEY}

# ============================================
# Kafka配置 (Message Queue)
# ============================================
SPRING_KAFKA_BOOTSTRAP_SERVERS=kafka-0.prod.internal:9092,kafka-1.prod.internal:9092,kafka-2.prod.internal:9092
SPRING_KAFKA_CONSUMER_GROUP_ID={{project_name | lower | default('skiller')}}-prod
```

### 3.3 密钥管理规范

| 密钥类型 | 存储位置 | 轮换周期 | 访问权限 |
|----------|----------|----------|----------|
| 数据库密码 | K8s Secret (Sealed Secrets) | 每90天 | DBA + K8s Admin |
| Redis密码 | K8s Secret | 每90天 | DevOps |
| JWT密钥 | K8s Secret | 每180天 | Security Team |
| API密钥(支付宝等) | K8s Secret + AWS Parameter Store | 按需 | DevOps + Payment Owner |
| SSL证书 | K8s Secret (tls类型) | Let's Encrypt自动续期 | K8s Admin |
| OSS AK/SK | RAM子账号密钥 | 每180天 | DevOps |

---

## 4. 部署步骤

### 4.1 部署总流程

```
Step 0: 准备工作 (备份/通知)
    ↓
Step 1: 构建镜像 (CI Pipeline 或手动)
    ↓
Step 2: 推送镜像至Registry
    ↓
Step 3: 执行数据库迁移
    ↓
Step 4: 更新K8s部署 (滚动更新)
    ↓
Step 5: 验证部署成功 (健康检查)
    ↓
Step 6: 清理旧资源
    ↓
Step 7: 通知完成
```

### 4.2 Step 0: 准备工作

```bash
# ========================================
# Step 0: 部署前准备
# ========================================

# 0.1 设置环境变量
export ENVIRONMENT="production"
export VERSION="{{version | default('v1.0.0')}}"
export NAMESPACE="skiller-prod"
export REGISTRY="{{docker_registry | default('registry.example.com')}}"
export RELEASE_NAME="skiller-backend"

echo "=== 部署准备 ==="
echo "环境: $ENVIRONMENT"
echo "版本: $VERSION"
echo "命名空间: $NAMESPACE"

# 0.2 创建当前版本快照（用于回滚）
kubectl get deployment $RELEASE_NAME -n $NAMESPACE -o yaml > /backup/deployment-backup-$(date +%Y%m%d-%H%M%S).yaml

# 0.3 备份当前数据库
pg_dump -h {{db_host}} -U backup_user -d {{db_name | default('skiller_db')}} \
  --no-owner --no-privileges \
  > /backup/db-backup-pre-deploy-$(date +%Y%m%d).sql.gz

echo "✅ 准备工作完成"
```

### 4.3 Step 1~2: 构建和推送镜像

```bash
# ========================================
# Step 1-2: 构建并推送Docker镜像
# ========================================

# 方式A: 使用CI Pipeline自动构建 (推荐)
# GitHub Actions会自动触发: push tag → build → push → deploy
# 手动触发:
# gh workflow run deploy.yml -f version=$VERSION -f environment=production

# 方式B: 手动构建推送 (CI不可用时)
IMAGE_TAG="${REGISTRY}/${PROJECT_NAME}-backend:${VERSION}"

# 构建镜像 (多阶段构建)
docker build \
  -t ${IMAGE_TAG} \
  --build-arg VERSION=${VERSION} \
  --build-arg GIT_COMMIT=$(git rev-parse HEAD) \
  -f docker/Dockerfile .

# 推送至私有镜像仓库
docker push ${IMAGE_TAG}

echo "✅ 镜像已推送: ${IMAGE_TAG}"
```

### 4.4 Step 3: 数据库迁移

```bash
# ========================================
# Step 3: 执行数据库迁移
# ========================================

# 使用Flyway执行SQL迁移 (推荐)
# 或者使用Helm chart中的job自动执行

# 3.1 检查待执行的迁移脚本
kubectl exec -it $(kubectl get pod -l app=flyway -n $NAMESPACE -o jsonpath='{.items[0].metadata.name}') \
  -- flyway -url=jdbc:postgresql://${DB_HOST}:5432/${DB_NAME} \
         -user=${DB_USER} \
         -password=${DB_PASSWORD} \
         -locations=filesystem:/flyway/sql \
         info

# 3.2 执行迁移 (dry-run先验证)
kubectl exec -it $(kubectl get pod -l app=flyway -n $NAMESPACE -o jsonpath='{.items[0].metadata.name}') \
  -- flyway -url=jdbc:postgresql://${DB_HOST}:5432/${DB_NAME} \
         -user=${DB_USER} \
         -password=${DB_PASSWORD} \
         -locations=filesystem:/flyway/sql \
         -connectRetries=10 \
         migrate

# 3.3 验证迁移结果
echo "✅ 数据库迁移完成"
```

### 4.5 Step 4: Kubernetes滚动更新

```bash
# ========================================
# Step 4: 执行K8s滚动更新
# ========================================

# 4.1 使用Helm升级 (推荐方式)
helm upgrade --install ${RELEASE_NAME} ./helm/skiller-backend \
  --namespace ${NAMESPACE} \
  --set image.tag=${VERSION} \
  --set image.repository=${REGISTRY}/${PROJECT_NAME}-backend \
  --set replicaCount=3 \
  --set resources.requests.cpu="500m" \
  --set resources.requests.memory="1Gi" \
  --set resources.limits.cpu="2000m" \
  --set resources.limits.memory="2Gi" \
  --wait \
  --timeout 300s \
  --atomic

# 4.2 如果不用Helm，使用kubectl直接更新
# kubectl set image deployment/${RELEASE_NAME} \
#   backend=${REGISTRY}/${PROJECT_NAME}-backend:${VERSION} \
#   -n ${NAMESPACE}

# 4.3 观察滚动更新状态
kubectl rollout status deployment/${RELEASE_NAME} -n ${NAMESPACE} --timeout=300s

# 4.4 查看Pod状态
kubectl get pods -l app=${RELEASE_NAME} -n ${NAMESPACE} -w

echo "✅ K8s更新完成"
```

### 4.6 Step 5: 验证部署

```bash
# ========================================
# Step 5: 验证部署成功
# ========================================

# 5.1 检查所有Pod是否Running
kubectl get pods -l app=${RELEASE_NAME} -n ${NAMESPACE}

# 预期输出: 3/3 Running, 0/0 ContainerCreating, 0/0 CrashLoopBackOff

# 5.2 健康检查
curl -sf https://api.{{domain | default('example.com')}}/actuator/health | jq .
# 预期: {"status":"UP",...}

# 5.3 检查Service Endpoints
kubectl get endpoints ${RELEASE_NAME} -n ${NAMESPACE}

# 5.4 验证关键API接口
echo "=== API验证 ==="
curl -sf https://api.{{domain | default('example.com')}}/api/v1/health | jq .
curl -sf -o /dev/null -w "%{http_code}" https://api.{{domain | default('example.com')}}/api/v1/public/config
# 预期: 200

# 5.5 检查日志无ERROR级别
kubectl logs -l app=${RELEASE_NAME} -n ${NAMESPACE} --tail=100 | grep -i "error\|exception" || echo "✅ 无错误日志"

echo "✅ 部署验证通过"
```

### 4.7 Step 6~7: 清理与通知

```bash
# ========================================
# Step 6-7: 清理与通知
# ========================================

# 6.1 清理旧版本的ReplicaSet (保留最近2个版本用于回滚)
kubectl delete rs -l app=${RELEASE_NAME} -n ${NAMESPACE} \
  --field-selector=status.replicas==0 2>/dev/null || true

# 6.2 清理旧镜像 (可选，节省磁盘空间)
# docker image prune -a --filter "until=72h"

# 7.1 发送部署成功通知 (钉钉/Slack/Email)
curl -X POST '{{webhook_url | default("https://oapi.dingtalk.com/robot/send?access_token=xxx")}}' \
  -H 'Content-Type: application/json' \
  -d '{
    "msgtype": "markdown",
    "markdown": {
      "title": "✅ 部署成功",
      "text": "## 🚀 {{project_name | default("Skiller")}} 部署成功\n\n\
- **环境**: Production\n\
- **版本**: '${VERSION}'\n\
- **时间**: '$(date '+%Y-%m-%d %H:%M:%S')'\n\
- **操作人**: '$(whoami)'\n\
- **Pod状态**: 3/3 Running\n\n\
请关注系统监控指标。"
    }
  }'

echo "🎉 部署全部完成！"
```

---

## 5. 健康检查

### 5.1 健康检查端点

| 端点 | 用途 | 预期响应 | 检查频率 |
|------|------|----------|----------|
| `/actuator/health` | 应用存活检查 | `{"status":"UP"}` | 每10s (Liveness Probe) |
| `/actuator/health/readiness` | 就绪检查 | `{"status":"UP"}` | 每10s (Readiness Probe) |
| `/api/v1/health` | 业务健康检查 | 含DB/Redis连接状态 | 每30s |
| `/actuator/info` | 版本信息 | Git commit + Build time | 手动查询 |
| `/actuator/metrics` | Prometheus指标 | 各项监控指标 | Prometheus抓取 |

### 5.2 部署后检查清单

| # | 检查项 | 命令/方法 | 预期结果 | 状态 |
|---|--------|-----------|----------|:----:|
| HC-01 | Pod全部正常运行 | `kubectl get pods -n skiller-prod` | 3/3 Running | ☐ |
| HC-02 | 应用启动无报错 | `kubectl logs <pod> --tail=50` | 无Exception/Error | ☐ |
| HC-03 | Health UP | `curl /actuator/health` | status=UP | ☐ |
| HC-04 | 数据库连接正常 | 日志中含"DataSource initialized" | 连接池就绪 | ☐ |
| HC-05 | Redis连接正常 | 日志中含"Redis connected" | 缓存可用 | ☐ |
| HC-06 | 用户登录接口正常 | POST /auth/login | 返回Token | ☐ |
| HC-07 | HTTPS证书有效 | 浏览器访问 | 🔒安全，无警告 | ☐ |
| HC-08 | 静态资源加载(CDN) | 页面打开速度 | FCP < 2s | ☐ |
| HC-09 | 监控数据上报 | Grafana面板 | 有新数据点 | ☐ |
| HC-10 | 告警通道正常 | 触发测试告警 | 钉钉/邮件收到 | ☐ |

---

## 6. 回滚步骤

### 6.1 回滚决策条件

出现以下任一情况应立即回滚：

| # | 回滚触发条件 | 判断标准 |
|---|-------------|----------|
| R-1 | 错误率飙升 | HTTP 5xx错误率 > 5% 且持续 > 5min |
| R-2 | P99延迟恶化 | P99延迟 > 3倍基线值 |
| R-3 | 核心功能不可用 | 登录/下单/支付任一失败 |
| R-4 | 数据异常 | 数据丢失/损坏/不一致 |
| R-5 | 安全事件 | 异常访问/入侵迹象 |

### 6.2 回滚操作步骤

```bash
# ========================================
# 紧急回滚操作 (预计耗时 < 5分钟)
# ========================================

# 方法一: Helm回滚 (推荐，最快)
# 查看历史版本
helm history ${RELEASE_NAME} -n ${NAMESPACE}

# 回滚到上一个版本
helm rollback ${RELEASE_NAME} 1 -n ${NAMESPACE} --wait --timeout=120s

# 方法二: kubectl回滚
# 查看 rollout 历史
kubectl rollout history deployment/${RELEASE_NAME} -n ${NAMESPACE}

# 回滚到指定版本 (REVISION编号)
kubectl rollout undo deployment/${RELEASE_NAME} -n ${NAMESPACE} --to-revision=<PREV_REVISION>

# 等待回滚完成
kubectl rollout status deployment/${RELEASE_NAME} -n ${NAMESPACE} --timeout=120s

# 验证回滚成功
curl -sf https://api.{{domain | default('example.com')}}/actuator/health | jq '.status'
# 预期: "UP"

# 如需同时回滚数据库 (谨慎!)
# pg_restore -h ${DB_HOST} -U backup_user -d ${DB_NAME} /backup/db-backup-pre-deploy-YYYYMMDD.sql.gz

echo "⚠️ 回滚完成！请立即排查问题根因！"
```

### 6.3 回滚后行动

- [ ] 立即发送回滚通知给全团队
- [ ] 收集故障期间的日志和监控数据
- [ ] 召开Post-mortem会议分析根因
- [ ] 修复问题后重新走完整发布流程
- [ ] 更新Runbook和文档

---

## 7. 运维手册

### 7.1 日常运维操作

#### 查看日志

```bash
# 实时查看所有Pod日志
kubectl logs -f -l app=skiller-backend -n skiller-prod --all-containers

# 查看特定Pod最近100行日志
kubectl logs <pod-name> -n skiller-prod --tail=100

# 查看特定时间的日志
kubectl logs <pod-name> -n skiller-prod --since-time='2024-03-20T14:00:00Z' --until-time='2024-03-20T15:00:00Z'

# 查看含ERROR的日志
kubectl logs -l app=skiller-backend -n skiller-prod --since=1h | grep -i "error\|exception\|fatal"
```

#### Pod重启

```bash
# 重启单个Pod (不推荐，优先用rollout restart)
kubectl delete pod <pod-name> -n skiller-prod

# 重启全部Pod (优雅的滚动重启)
kubectl rollout restart deployment/skiller-backend -n skiller-prod
```

#### 扩缩容

```bash
# 手动扩容到5个副本
kubectl scale deployment/skiller-backend --replicas=5 -n skiller-prod

# 恢复默认3个副本
kubectl scale deployment/skiller-backend --replicas=3 -n skiller-prod

# 查看HPA状态
kubectl get hpa -n skiller-prod
```

#### 进入容器调试

```bash
# 进入运行中容器Shell
kubectl exec -it <pod-name> -n skiller-prod -- /bin/sh

# 在容器内执行诊断命令
# top, jstack, curl localhost:8080/actuator/health 等
```

### 7.2 监控与告警

#### 关键监控指标

| 指标 | PromQL查询 | 告警阈值 | 严重度 |
|------|-----------|----------|--------|
| HTTP错误率 | `rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])` | > 5% | 🔴 Critical |
| P99延迟 | `histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))` | > 1s | 🟠 Warning |
| JVM堆使用 | `jvm_memory_used_bytes{area="heap"} / jvm_memory_max_bytes{area="heap"}` | > 85% | 🟠 Warning |
| Pod重启次数 | `changes(kube_pod_container_status_restarts_total[1h])` | > 3次/h | 🟠 Warning |
| 数据库连接池活跃 | `hikaricp_active_connections` | > 最大值*80% | 🟡 Info |
| Redis连接失败 | `rate(redis_connection_errors_total[5m])` | > 0 | 🟠 Warning |

#### 告警通知渠道

| 级别 | 通知渠道 | 响应时效 | 升级策略 |
|------|----------|----------|----------|
| 🔴 P1-Critical | 电话 + 钉钉 + Slack | 5分钟内 | 10分钟无人响应→升级给TL |
| 🟠 P2-Warning | 钉钉 + 邮件 | 30分钟内 | 1小时无人响应→升级 |
| 🟡 P3-Info | 邮件 | 工作时间内 | 每日汇总 |

### 7.3 定时任务维护

| 任务 | Cron表达式 | 功能 | 维护注意 |
|------|-----------|------|----------|
| order-expire-job | `0 */5 * * * ?` | 扫描超时未支付订单并关闭 | 关注执行耗时 |
| data-cleanup-job | `0 0 3 * * ?` | 清理过期临时数据(验证码/缓存) | 低峰期执行 |
| report-generate-job | `0 0 2 * * ?` | 生成每日运营报表 | 确保数据完整 |
| db-backup-job | `0 0 4 * * ?` | 全量数据库备份 | 验证备份完整性 |

### 7.4 备份策略

| 备份对象 | 频率 | 保留期 | 存储位置 | 恢复方式 |
|----------|------|--------|----------|----------|
| PostgreSQL全量 | 每天02:00 | 30天 | OSS冷存储 | pg_restore |
| PostgreSQL WAL | 实时 | 7天 | 本地+OSS | PITR恢复 |
| Redis RDB | 每小时 | 7天 | OSS | redis-cli --rdb |
| K8s资源定义 | 每次变更 | 永久 | Git仓库 | kubectl apply |
| SSL证书 | 自动(Let's Encrypt) | - | K8s Secret | certbot renew |
| 应用配置(ConfigMap) | 每次变更 | 永久 | Git仓库 | kubectl apply |

---

## 8. 故障排查指南

### 8.1 常见问题速查表

| 问题现象 | 可能原因 | 排查命令 | 解决方案 |
|----------|----------|----------|----------|
| **Pod CrashLoopBackOff** | 启动失败/OOM/配置错误 | `kubectl describe pod <name>` `kubectl logs <name> --previous` | 检查资源配置/日志/配置文件 |
| **502 Bad Gateway** | 后端服务未就绪/端口不通 | `kubectl get endpoints` `kubectl logs ingress-controller` | 检查ReadinessProbe/Service selector |
| **504 Gateway Timeout** | 后端处理超时 | 检查慢查询日志/Prometheus P99 | 优化慢SQL/增加超时时间/扩容 |
| **数据库连接拒绝** | 连接池满/DB过载 | `SHOW processlist;` 检查max_connections | 增大连接池/优化长事务 |
| **Redis连接超时** | Redis过载/网络抖动 | `redis-cli info stats` 检查connected_clients | 检查Redis内存/CPU/网络 |
| **高CPU使用率** | GC频繁/死循环/密集计算 | `kubectl top pods` `jstat -gcutil <pid>` | 分析线程dump/调优JVM参数 |
| **OOM Killed** | 内存泄漏/配置不足 | `kubectl describe pod` 中显示 OOMKilled | 增大memory limit/排查泄漏 |
| **SSL证书错误** | 证书过期/域名不匹配 | `openssl s_client -connect domain:443` | 续期Let's Encrypt证书 |
| **文件上传失败** | OSS权限/大小限制/超时 | 检查OSS bucket policy/Nginx client_max_body_size | 调整限制/检查AKSK权限 |
| **短信发送失败** | 签名/模板审核未通过/余额不足 | 查看阿里云短信控制台 | 联系运营审核签名/充值 |

### 8.2 故障排查流程图

```
用户报告异常
    │
    ▼
┌─────────────────┐
│ 1. 确认影响范围  │ ← 是单用户还是全局？
│ who/what/when   │
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
 全局问题   单用户问题
    │         │
    ▼         ▼
┌────────┐ ┌────────┐
│检查CDN │ │检查用户│
│/SLB    │ │Session │
│/DNS    │ │/权限   │
└───┬────┘ └───┬────┘
    │         │
    ▼         ▼
┌─────────────────┐
│ 2. 检查基础设施  │
│ K8s Pod状态     │
│ Service/Ingress │
│ 资源使用率       │
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
 基础设施正常  基础设施异常
    │         │
    ▼         ▼
┌────────┐ ┌────────────┐
│3.检查  │ │修复/重启/  │
│应用日志│ │扩容/回滚   │
│DB状态  │ │            │
│Redis   │ └────────────┘
└───┬────┘
    │
    ▼
┌─────────────────┐
│ 4. 定位根因      │
│ 修复并验证       │
│ 记录到知识库     │
└─────────────────┘
```

### 8.3 应急联系人与Escalation

| 角色 | 姓名 | 电话 | 职责 | 可处理时间段 |
|------|------|------|------|-------------|
| 一线值班 | On-Call轮值 | 📞 DUTY-PHONE | 初步判断和快速恢复 | 7×24 |
| DevOps工程师 | {{ops_primary | default('___')}} | 📞 ___ | 基础设施层面处理 | 工作时间+紧急 |
| 后端负责人 | {{dev_lead | default('___')}} | 📞 ___ | 应用层面深度排查 | 工作时间+紧急 |
| DBA | {{dba | default('___')}} | 📞 ___ | 数据库相关问题 | 工作时间+紧急 |
| 技术总监 | {{cto | default('___')}} | 📞 ___ | 重大决策/对外协调 | 紧急 |

---

## 附录: 部署Checklist (最终确认)

在点击"发布"按钮前，**逐项确认**以下内容：

### 发布前 (T-30min)

- [ ] 代码已合并至Release分支
- [ ] CI流水线全绿 (Build + Test + Scan)
- [ ] 测试报告已签字批准
- [ ] 数据库迁移脚本已review
- [ ] 配置文件已review (特别是密钥和环境差异)
- [ ] 回滚方案已准备并可执行
- [ ] 备份已完成且可恢复
- [ ] 相关方已收到通知
- [ ] 监控Dashboard已准备好观察

### 发布中 (T-0)

- [ ] 滚动更新开始
- [ ] 旧Pod逐个停止，新Pod逐个启动
- [ ] 观察日志无ERROR
- [ ] 健康检查持续UP
- [ ] 错误率无明显上升

### 发布后 (T+30min)

- [ ] 全部Pod Running (3/3)
- [ ] 核心API返回正常
- [ ] 监控指标在正常范围
- [ ] 发送部署成功通知
- [ ] 更新部署记录

---

*本文档由 DevOps 团队维护，每次部署后如有变更需及时更新。*
