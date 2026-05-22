<!--
  模板说明: Run Log (运行日志)
  用途: 记录一次自动化任务/脚本/构建/部署等操作的完整执行过程
  变量列表:
    {{run_id}}                - 运行唯一标识
    {{run_type}}              - 运行类型 (build/deploy/migrate/test/cron等)
    {{trigger_command}}       - 触发命令
    {{executor}}              - 执行者
    {{start_time}}            - 开始时间
    {{end_time}}              - 结束时间
    {{duration}}              - 总耗时
    {{status}}                - 最终状态 (SUCCESS/FAILURE/PARTIAL/TIMEOUT/CANCELLED)
    {{stages}}                - 各阶段记录
    {{errors}}                - 错误与异常记录
    {{outputs}}               - 输出物清单
    {{resource_usage}}        - 资源使用统计
    {{next_actions}}          - 下一步行动建议
  使用方式: 每次CI/CD流水线运行、手动脚本执行、定时任务完成后自动/手动生成此日志
-->

# 📋 运行日志 #{{run_id | default('RUN-20240321-001')}}

> **类型**: {{run_type | default('Deployment')}} | **状态**: {{status_emoji | default('✅')}} **{{status | default('SUCCESS')}}**
> **触发时间**: {{start_time | default('2024-03-21 02:00:15 UTC+8')}}
> **执行人**: {{executor | default('DevOps Bot (CI Pipeline)')}}
> **触发命令**: `{{trigger_command | default('./deploy.sh --env=production --version=v1.0.0')}}`

---

## 执行概览

| 属性 | 值 |
|------|-----|
| **Run ID** | `{{run_id | default('RUN-20240321-001')}}` |
| **运行类型** | {{run_type | default('Production Deployment')}} |
| **目标环境** | {{environment | default('PRODUCTION')}} |
| **目标版本** | {{target_version | default('v1.0.0 (build.20240320.1)')}} |
| **开始时间** | {{start_time | default('2024-03-21 02:00:15')}} |
| **结束时间** | {{end_time | default('2024-03-21 02:18:42')}} |
| **总耗时** | **{{duration | default('18分27秒')}}** |
| **最终状态** | **{{status | default('✅ SUCCESS')}}** |
| **执行节点** | {{runner_node | default('ci-runner-prod-03')}} |
| **Git Commit** | `{{git_commit | default('a1b2c3d')}}` — {{commit_message | default('feat: release v1.0.0 - MVP正式版')}} |
| **Git Branch** | `{{git_branch | default('release/v1.0.0')}}` |

---

## 阶段执行详情

### Phase 1: 准备阶段 (Preparation)

```
┌─────────────────────────────────────────────┐
│ Phase 1: 准备                               │
│ 开始: 02:00:15  │ 结束: 02:01:02  │ 耗时: 47s │
│ 状态: ✅ SUCCESS                            │
└─────────────────────────────────────────────┘
```

| 步骤 | 操作 | 状态 | 耗时 | 输出摘要 |
|------|------|------|------|----------|
| 1.1 | 拉取最新代码 (`git fetch && git checkout`) | ✅ 成功 | 12s | commit a1b2c3d checked out |
| 1.2 | 加载环境变量 (`.env.production`) | ✅ 成功 | 2s | 28个变量已加载 |
| 1.3 | 验证前置条件 (磁盘/内存/Docker/K8s) | ✅ 成功 | 18s | 所有12项检查通过 |
| 1.4 | 检查当前版本运行状态 | ✅ 成功 | 8s | v0.9.2 运行正常, 3/3 Pod Ready |
| 1.5 | 创建备份快照 | ✅ 成功 | 7s | 备份至 `/backup/deploy-snap-20240321-0200.tar.gz` |

### Phase 2: 构建阶段 (Build)

```
┌─────────────────────────────────────────────┐
│ Phase 2: 构建                               │
│ 开始: 02:01:02  │ 结束: 02:05:45  │ 耗时: 4m43s │
│ 状态: ✅ SUCCESS                            │
└─────────────────────────────────────────────┘
```

| 步骤 | 操作 | 状态 | 耗时 | 输出摘要 |
|------|------|------|------|----------|
| 2.1 | 安装依赖 (`npm ci` / `mvn dependency:resolve`) | ✅ 成功 | 58s | 前端 1247 deps, 后端 89 deps |
| 2.2 | 前端构建 (`npm run build`) | ✅ 成功 | 2m15s | 产物大小: 1.2MB (gzip: 380KB) |
| 2.3 | 后端编译 (`mvn package -DskipTests`) | ✅ 成功 | 1m48s | JAR: skiller-backend-1.0.0.jar (52MB) |
| 2.4 | 单元测试 (`npm test / mvn test`) | ✅ 成功 | 1m32s | UT: 1247 passed, 15 failed(已知), 0 skipped |
| 2.5 | Docker镜像构建 (`docker build`) | ✅ 成功 | 2m08s | Image: registry/skiller-backend:v1.0.0 (156MB) |
| 2.6 | 镜像安全扫描 (`trivy image scan`) | ✅ 成功 | 22s | 0 Critical, 0 High, 3 Low |

**构建产物清单**:

| 产物 | 路径/Tag | 大小 | SHA256 |
|------|----------|------|--------|
| 前端静态资源 | `dist/build-20240320-abc1234/` | 1.2MB | `e8f3a2b1...` |
| 后端JAR包 | `target/skiller-backend-1.0.0.jar` | 52MB | `c9d4e5f6...` |
| Docker镜像 | `registry/skiller-backend:v1.0.0` | 156MB | `a1b2c3d4...` |

### Phase 3: 数据库迁移 (Database Migration)

```
┌─────────────────────────────────────────────┐
│ Phase 3: DB迁移                             │
│ 开始: 02:05:45  │ 结束: 02:07:12  │ 耗时: 1m27s │
│ 状态: ✅ SUCCESS                            │
└─────────────────────────────────────────────┘
```

| 步骤 | 操作 | 状态 | 耗时 | 输出摘要 |
|------|------|------|------|----------|
| 3.1 | 连接数据库验证 | ✅ 成功 | 3s | PostgreSQL 15.2, 连接正常 |
| 3.2 | 检查待执行迁移 | ✅ 成功 | 2s | 发现 3 个待执行迁移脚本 |
| 3.3 | 执行 V1.0.0__add_user_roles_table.sql | ✅ 成功 | 8s | 创建表 user_roles (0 rows affected) |
| 3.4 | 执行 V1.0.0__alter_orders_add_payment_method.sql | ✅ 成功 | 15s | ALTER TABLE orders ADD COLUMN payment_method |
| 3.5 | 执行 V1.0.0__create_operation_logs_table.sql | ✅ 成功 | 12s | CREATE TABLE operation_logs |
| 3.6 | 更新Flyway schema_history | ✅ 成功 | 2s | 版本更新至 1.0.0 |
| 3.7 | 数据校验 (抽样检查) | ✅ 成功 | 25s | 表结构正确，外键约束有效 |

**迁移SQL详情**:

```sql
-- V1.0.0__add_user_roles_table.sql
CREATE TABLE user_roles (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id),
    role_id BIGINT NOT NULL REFERENCES roles(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, role_id)
);

-- V1.0.0__alter_orders_add_payment_method.sql
ALTER TABLE orders ADD COLUMN IF NOT EXISTS payment_method
    VARCHAR(20) DEFAULT NULL;
COMMENT ON orders.payment_method IS '支付方式';

-- V1.0.0__create_operation_logs_table.sql
CREATE TABLE operation_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT,
    action VARCHAR(50) NOT NULL,
    target_type VARCHAR(30),
    target_id VARCHAR(64),
    detail JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_oplogs_user ON operation_logs(user_id);
CREATE INDEX idx_oplogs_action ON operation_logs(action);
CREATE INDEX idx_oplogs_created ON operation_logs(created_at);
```

### Phase 4: 部署阶段 (Deployment)

```
┌─────────────────────────────────────────────┐
│ Phase 4: 部署                               │
│ 开始: 02:07:12  │ 结束: 02:16:33  │ 耗时: 9m21s │
│ 状态: ✅ SUCCESS                            │
└─────────────────────────────────────────────┘
```

| 步骤 | 操作 | 状态 | 耗时 | 输出摘要 |
|------|------|------|------|----------|
| 4.1 | 推送Docker镜像至Registry | ✅ 成功 | 45s | Pushed 3 layers (156MB total) |
| 4.2 | Helm渲染模板 | ✅ 成功 | 8s | 渲染 12 个K8s资源模板 |
| 4.3 | 应用ConfigMap更新 | ✅ 成功 | 3s | configmap/skiller-backend-config updated |
| 4.4 | 应用Secret更新(如有变更) | ⏭️ 跳过 | 0s | 无Secret变更 |
| 4.5 | 执行滚动更新(RollingUpdate) | ✅ 成功 | 6m42s | 3个Pod逐个替换完成 |
| 4.6 | Pod健康检查等待 | ✅ 成功 | 2m10s | 所有Pod ReadinessProbe通过 |
| 4.7 | Service Endpoints验证 | ✅ 成功 | 5s | 3个Endpoint就绪 |

**滚动更新详情**:

| Pod | 操作 | 开始时间 | 完成时间 | 耗时 | 结果 |
|-----|------|----------|----------|------|------|
| skiller-backend-7c8d9f0k1-old | Terminating (优雅停止) | 02:09:15 | 02:09:45 | 30s | ✅ 正常终止 |
| skiller-backend-7c8d9f0k1-new | Starting → Ready | 02:09:20 | 02:11:35 | 135s | ✅ 就绪 |
| skiller-backend-8a1b2c3m2-old | Terminating (优雅停止) | 02:11:40 | 02:12:10 | 30s | ✅ 正常终止 |
| skiller-backend-8a1b2c3m2-new | Starting → Ready | 02:11:45 | 02:13:55 | 130s | ✅ 就绪 |
| skiller-backend-9d3e4f5n3-old | Terminating (优雅停止) | 02:14:00 | 02:14:30 | 30s | ✅ 正常终止 |
| skiller-backend-9d3e4f5n3-new | Starting → Ready | 02:14:05 | 02:16:33 | 148s | ✅ 就绪 |

### Phase 5: 验证阶段 (Verification)

```
┌─────────────────────────────────────────────┐
│ Phase 5: 验证                               │
│ 开始: 02:16:33  │ 结束: 02:18:22  │ 耗时: 1m49s │
│ 状态: ✅ SUCCESS                            │
└─────────────────────────────────────────────┘
```

| 步骤 | 操作 | 状态 | 耗时 | 输出摘要 |
|------|------|------|------|----------|
| 5.1 | 健康检查 (`/actuator/health`) | ✅ 成功 | 2s | status=UP, components={db:"UP", redis:"UP", disk:"UP"} |
| 5.2 | API连通性测试 (核心接口冒烟) | ✅ 成功 | 35s | 15/15 接口返回200 |
| 5.3 | 登录功能验证 | ✅ 成功 | 5s | Token正常签发 |
| 5.4 | 静态资源CDN刷新验证 | ✅ 成功 | 12s | CDN已缓存新版本资源 |
| 5.5 | 监控数据上报验证 | ✅ 成功 | 18s | Prometheus收到新metrics |
| 5.6 | 错误日志扫描 | ✅ 成功 | 25s | 启动期间无ERROR级别日志 |
| 5.7 | 性能基线快速检测 | ✅ 成功 | 12s | P99=298ms (<500ms目标) ✅ |

**冒烟测试结果**:

| 接口 | 方法 | HTTP状态 | 耗时(ms) | 结果 |
|------|------|----------|----------|------|
| GET /actuator/health | Health Check | 200 | 12 | ✅ |
| GET /api/v1/public/config | 公开配置 | 200 | 45 | ✅ |
| POST /api/v1/auth/login | 用户登录 | 201 | 189 | ✅ |
| GET /api/v1/users/me | 当前用户 | 200 | 95 | ✅ |
| POST /api/v1/orders | 创建订单 | 201 | 312 | ✅ |
| GET /api/v1/orders | 订单列表 | 200 | 178 | ✅ |
| POST /api/v1/files/upload | 文件上传 | 201 | 456 | ✅ |
| GET /api/v1/admin/statistics/overview | 统计概览 | 200 | 567 | ✅ |
| ... (共15个接口全部通过) | | | | |

---

## ❌ 错误与异常记录

<!-- COMMENT: 记录本次运行中出现的所有非预期情况 -->

| # | 时间 | 级别 | 错误信息 | 来源 | 处理结果 | 影响 |
|---|------|------|----------|------|----------|------|
| ERR-01 | 02:04:23 | WARN | npm warn deprecated `core-js@2` | 前端构建 | 已知警告，忽略 | 无影响 |
| ERR-02 | 02:06:45 | INFO | Flyway: table "flyway_schema_history" already exists | DB迁移 | 首次初始化提示，自动处理 | 无影响 |
| ERR-03 | 02:12:18 | WARN | Pod startup probe failed on first attempt | K8s滚动更新 | 重试后成功（应用冷启动需~60s） | 无影响 |

**错误详情 (ERR-03)**:

```
[WARN] 02:12:18 kubernetes Liveness probe failed: HTTP probe failed with statuscode: 503
[INFO] 02:12:28 kubernetes Liveness probe succeeded: HTTP probe succeeded with statuscode: 200
[说明]: 新Pod启动时Spring Boot尚未完全初始化完成，Liveness Probe首次探测失败属正常现象。
      Readiness Probe配置了 initialDelaySeconds=60，确保服务就绪后才接收流量。
```

---

## 📦 输出物清单

<!-- COMMENT: 列出本次运行产生的所有文件和制品 -->

| 类别 | 文件名/路径 | 大小 | 类型 | 存储位置 | 保留期 |
|------|-------------|------|------|----------|--------|
| **Docker镜像** | `registry/skiller-backend:v1.0.0` | 156MB | OCI Image | Harbor Registry | 永久 |
| **Docker镜像** | `registry/skiller-backend:v1.0.0-build.20240320` | 156MB | OCI Image | Harbor Registry | 90天 |
| **前端构建** | `dist/build-20240320-abc1234/` | 1.2MB | Static Files | OSS (cdn bucket) | 永久 |
| **后端JAR** | `target/skiller-backend-1.0.0.jar` | 52MB | Java Artifact | OSS (archive bucket) | 365天 |
| **数据库备份** | `backup/db-pre-deploy-20240321.sql.gz` | 245MB | SQL Dump | OSS (backup bucket) | 30天 |
| **部署快照** | `backup/deploy-snap-20240321-0200.tar.gz` | 12MB | Tar Archive | NFS Backup | 14天 |
| **单元测试报告** | `reports/junit/index.html` | 85KB | HTML Report | CI Artifacts | 30天 |
| **覆盖率报告** | `reports/jacoco/index.html` | 120KB | HTML Report | CI Artifacts | 30天 |
| **构建日志** | `logs/build-20240321-0200.log` | 2.3MB | Text Log | ELK | 90天 |
| **部署报告** | `reports/deployment-20240321.md` | 15KB | Markdown | Git Repo | 永久 |
| **变更记录** | `CHANGELOG.md` (已更新) | 8KB | Markdown | Git Repo | 永久 |

---

## 💻 资源使用统计

### 计算资源

| 资源 | 峰值使用 | 平均使用 | 最大可用 | 使用率峰值 |
|------|----------|----------|----------|-----------|
| **CPU** | 3.8 cores | 1.2 cores | 8 cores | 47.5% |
| **内存** | 5.2 GB | 2.8 GB | 16 GB | 32.5% |
| **磁盘I/O** | 85 MB/s | 12 MB/s | - | - |
| **网络入流量** | 180 Mbps | 45 Mbps | 1 Gbps | 18% |
| **网络出流量** | 95 Mbps | 28 Mbps | 1 Gbps | 9.5% |

### 时间分布饼图

```
总耗时: 18分27秒

  构建 ████████████████████████  26%  (4m43s)
  部署 █████████████████████     51%  (9m21s)
  验证 ████                      10%  (1m49s)
  DB迁移 ██                       8%   (1m27s)
  准备   █                        4%   (47s)
```

---

## 🔜 下一步行动建议

### ✅ 立即执行 (Post-Deploy)

- [ ] 发送部署成功通知到钉钉群 (#devops-alerts)
- [ ] 更新运行状态页面 (Status Page → Operational)
- [ ] 触发E2E冒烟测试套件 (Playwright CI Job)
- [ ] 清理旧版本的ReplicaSet（保留最近2个版本）

### 📊 24小时内监控

- [ ] 关注前2小时的错误率曲线（对比基线）
- [ ] 确认P99延迟在正常范围（<500ms）
- [ ] 观察用户注册转化率是否异常
- [ ] 检查支付成功率（支付宝/微信回调正常接收）

### 📋 本周内跟进

- [ ] 整理本次发布的技术总结文档
- [ ] 安排Post-mortem会议（如有任何异常）
- [ ] 更新运维Runbook中的版本相关信息
- [ ] 标记已解决的Jira Ticket为Done

### 🗓️ 下次发布准备

- [ ] 当前版本稳定运行72小时后开始规划 v1.0.1
- [ ] 收集用户反馈和Bug Report
- [ ] 评估遗留缺陷的修复优先级

---

## 关联信息

| 项目 | 链接/标识 |
|------|-----------|
| CI/CD Pipeline Run | https://github.com/org/repo/actions/runs/{{run_id | default('1234567890')}} |
| Git Commit | [`a1b2c3d`](https://github.com/org/repo/commit/a1b2c3d) |
| Docker Image | `registry.example.com/skiller-backend:v1.0.0` |
| Helm Release | `helm history skiller-backend -n skiller-prod` (REVISION=15) |
| 相关Issue | [#123](https://github.com/org/repo/issues/123) Release v1.0.0 |
| 监控Dashboard | https://grafana.example.com/d/deployment |
| 上一次运行日志 | [RUN-20240314-001](./RUN-20240314-001.md) |

---

*本日志由 {{run_type | default('Deployment Pipeline')}} 自动生成于 {{end_time | default('2024-03-21 02:18:42 UTC+8')}}*
