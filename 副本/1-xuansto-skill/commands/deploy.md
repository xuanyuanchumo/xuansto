# /deploy 命令

## 命令描述

`/deploy` 命令用于部署与发布管理，是交付流程的最终执行命令。该命令管理从构建到生产的完整部署流程，支持多环境部署、蓝绿发布、金丝雀发布等策略，确保安全、可控、可回滚的发布过程。

---

## 使用语法

```
/deploy [environment] [options]
```

---

## 参数说明

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| environment | string | 否 | staging | 目标环境：local、dev、staging、production |
| --strategy | string | 否 | rolling | 部署策略：rolling、blue-green、canary、recreate |
| --version | string | 否 | latest | 部署版本号或标签 |
| --dry-run | boolean | 否 | false | 模拟部署，不执行实际变更 |
| --skip-tests | boolean | 否 | false | 跳过部署前测试 |
| --skip-backup | boolean | 否 | false | 跳过部署前备份 |
| --rollback-on-fail | boolean | 否 | true | 部署失败自动回滚 |
| --health-check | boolean | 否 | true | 部署后健康检查 |
| --notify | string | 否 | all | 通知对象：all、team、stakeholders、none |
| --timeout | number | 否 | 600 | 部署超时时间（秒） |
| --canary-percent | number | 否 | 10 | 金丝雀发布流量百分比 |

---

## 执行流程

```
┌─────────────────────────────────────────────────────────────┐
│                    /deploy 执行流程                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. 预部署检查                                               │
│     ├── 验证部署权限                                         │
│     ├── 检查环境状态                                         │
│     ├── 验证版本完整性                                       │
│     ├── 运行部署前测试                                       │
│     └── 生成部署清单                                         │
│                                                             │
│  2. 备份与准备                                               │
│     ├── 创建当前状态快照                                     │
│     ├── 备份数据库（如需要）                                  │
│     ├── 记录回滚点                                          │
│     └── 准备部署资源                                         │
│                                                             │
│  3. 构建阶段                                                 │
│     ├── 拉取代码/镜像                                       │
│     ├── 执行构建脚本                                         │
│     ├── 运行单元测试                                         │
│     ├── 安全扫描                                            │
│     └── 生成构建产物                                         │
│                                                             │
│  4. 部署执行阶段                                             │
│     ├── 根据策略执行部署                                     │
│     │   ├── Rolling: 滚动更新实例                           │
│     │   ├── Blue-Green: 创建新环境切换                      │
│     │   ├── Canary: 逐步增加流量                            │
│     │   └── Recreate: 停止旧版本部署新版本                   │
│     ├── 更新负载均衡配置                                     │
│     ├── 执行数据库迁移                                       │
│     └── 应用配置变更                                         │
│                                                             │
│  5. 验证阶段                                                 │
│     ├── 健康检查                                            │
│     ├── 冒烟测试                                            │
│     ├── 性能基线验证                                         │
│     ├── 监控指标检查                                         │
│     └── 日志错误检测                                         │
│                                                             │
│  6. 流量切换（如适用）                                        │
│     ├── 逐步切换流量                                         │
│     ├── 监控错误率                                          │
│     ├── 验证用户体验                                         │
│     └── 完成流量迁移                                         │
│                                                             │
│  7. 后部署处理                                               │
│     ├── 清理旧版本资源                                       │
│     ├── 更新DNS/CDN配置                                     │
│     ├── 发送部署通知                                         │
│     ├── 更新发布文档                                         │
│     └── 归档部署记录                                         │
│                                                             │
│  8. 监控与告警                                               │
│     ├── 配置监控告警                                         │
│     ├── 设置错误率阈值                                       │
│     ├── 启用自动回滚触发器                                   │
│     └── 持续监控窗口期                                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 涉及的Agent

| Agent角色 | 职责 | 参与阶段 |
|-----------|------|----------|
| cicd-specialist | CI/CD流水线执行 | 构建阶段、部署执行 |
| runtime-supervisor | 运行时监控 | 验证阶段、监控告警 |
| monitor-specialist | 监控配置与告警 | 后部署处理、监控告警 |
| dba | 数据库迁移 | 部署执行阶段 |
| security-auditor | 安全配置验证 | 预部署检查、验证阶段 |
| technical-writer | 发布文档更新 | 后部署处理 |

---

## 输出产物

### 1. 部署报告 (deployment-report.md)

```markdown
# 部署报告

## 部署概要
- 部署时间: 2026-04-17 16:00:00
- 部署环境: production
- 部署策略: blue-green
- 部署版本: v1.2.0
- 部署状态: ✅ 成功

## 部署清单
| 组件 | 旧版本 | 新版本 | 状态 |
|------|--------|--------|------|
| api-server | v1.1.5 | v1.2.0 | ✅ 已更新 |
| web-client | v1.1.5 | v1.2.0 | ✅ 已更新 |
| worker-service | v1.1.5 | v1.2.0 | ✅ 已更新 |
| database | schema-v5 | schema-v6 | ✅ 已迁移 |

## 部署时间线
- 16:00:00 - 开始预部署检查
- 16:02:30 - 创建备份快照
- 16:05:00 - 开始构建
- 16:15:00 - 构建完成
- 16:16:00 - 开始蓝环境部署
- 16:25:00 - 蓝环境健康检查通过
- 16:26:00 - 流量切换到蓝环境
- 16:30:00 - 部署完成

## 验证结果
- 健康检查: ✅ 通过
- 冒烟测试: ✅ 通过 (12/12)
- 性能验证: ✅ 响应时间 < 200ms
- 错误率: ✅ 0.01% (< 0.1% 阈值)

## 回滚信息
- 回滚点: rollback-20260417-160000
- 回滚命令: /deploy production --rollback=rollback-20260417-160000

## 监控配置
- 告警规则: 已更新
- 仪表板: 已刷新
- 日志收集: 正常
```

### 2. 部署清单 (deployment-manifest.json)

```json
{
  "deployment_id": "DEPLOY-20260417-001",
  "environment": "production",
  "strategy": "blue-green",
  "version": "v1.2.0",
  "previous_version": "v1.1.5",
  "status": "success",
  "components": [
    {
      "name": "api-server",
      "image": "registry.example.com/api-server:v1.2.0",
      "replicas": 3,
      "health_check": "/health"
    },
    {
      "name": "web-client",
      "image": "registry.example.com/web-client:v1.2.0",
      "replicas": 2,
      "health_check": "/"
    }
  ],
  "migrations": [
    {
      "name": "add_user_preferences_table",
      "status": "applied",
      "rollback_sql": "DROP TABLE user_preferences;"
    }
  ],
  "rollback_point": "rollback-20260417-160000"
}
```

### 3. 发布说明 (release-notes.md)

```markdown
# Release v1.2.0

## 新功能
- 用户偏好设置功能
- 多主题支持
- 导出数据功能

## 改进
- 登录性能优化 50%
- 数据库查询优化
- 前端资源压缩

## 修复
- 修复会话超时问题
- 修复文件上传大小限制

## 已知问题
- 无

## 升级说明
- 需要执行数据库迁移
- 建议清理浏览器缓存
```

---

## 示例用法

### 示例1: 标准部署

```bash
/deploy staging
```

部署到 staging 环境，使用默认滚动更新策略。

### 示例2: 生产环境蓝绿部署

```bash
/deploy production --strategy=blue-green --notify=all
```

使用蓝绿策略部署到生产环境，通知所有干系人。

### 示例3: 金丝雀发布

```bash
/deploy production --strategy=canary --canary-percent=20
```

使用金丝雀策略部署，初始20%流量到新版本。

### 示例4: 模拟部署

```bash
/deploy production --dry-run
```

模拟生产环境部署，验证部署流程。

### 示例5: 指定版本部署

```bash
/deploy staging --version=v1.1.0 --skip-tests
```

部署指定版本到 staging 环境，跳过测试。

### 示例6: 回滚部署

```bash
/deploy production --rollback=rollback-20260417-160000
```

回滚到指定的回滚点。

---

## 部署策略说明

### Rolling Update（滚动更新）

```
特点:
  - 逐步替换旧实例
  - 零停机时间
  - 资源利用率高
  - 回滚较慢

流程:
  [v1][v1][v1][v1] → [v2][v1][v1][v1] → [v2][v2][v1][v1] → [v2][v2][v2][v2]

适用场景:
  - 常规版本更新
  - 无重大架构变更
  - 兼容性良好的更新
```

### Blue-Green（蓝绿部署）

```
特点:
  - 完整并行环境
  - 即时切换
  - 快速回滚
  - 资源消耗高

流程:
  Green(v1): [active] ← 流量
  Blue(v2):  [idle]   → 部署新版本
  ↓
  Green(v1): [idle]
  Blue(v2):  [active] ← 流量切换

适用场景:
  - 重大版本更新
  - 需要快速回滚
  - 有充足资源
```

### Canary（金丝雀发布）

```
特点:
  - 逐步放量
  - 风险可控
  - 实时验证
  - 可精细控制

流程:
  [v1: 100%] → [v1: 90%, v2: 10%] → [v1: 50%, v2: 50%] → [v2: 100%]

适用场景:
  - 高风险变更
  - 需要验证新版本
  - 用户影响敏感
```

### Recreate（重建部署）

```
特点:
  - 停止旧版本后部署新版本
  - 有停机时间
  - 简单直接
  - 无兼容性问题

流程:
  [v1][v1][v1] → [停止] → [v2][v2][v2]

适用场景:
  - 允许短暂停机
  - 不兼容的更新
  - 开发/测试环境
```

---

## 质量门禁关联

| 门禁ID | 门禁名称 | 触发条件 |
|--------|----------|----------|
| GATE-013 | 部署就绪门禁 | 预部署检查 |
| GATE-014 | 生产验证门禁 | 部署后验证 |

---

## 注意事项

1. **权限验证**: 确保有目标环境的部署权限
2. **备份重要**: 生产部署前必须创建备份
3. **监控窗口**: 部署后持续监控至少30分钟
4. **回滚准备**: 确保回滚方案和脚本就绪
5. **通知机制**: 重要部署需通知相关干系人

---

## 相关命令

- `/accept` - 部署前的验收确认
- `/agent-status` - 查看部署Agent状态
- `/learn` - 部署经验沉淀
