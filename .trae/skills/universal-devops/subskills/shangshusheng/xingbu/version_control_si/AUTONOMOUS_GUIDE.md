# 版本管理司 自主操作指南 (Autonomous Operation Guide)

## 概述

版本管理司（Version Control Si）是尚书省·刑部下属的自主发布治理机构，核心定位为**自主发布决策与版本全生命周期管理**。本司负责从代码提交到生产发布的完整链路管控，通过标准化的分支策略、语义化版本管理、自动化变更日志生成和发布就绪度评估，确保每次发布都是可控、可追溯、可回滚的。

**核心目标：**
- 实现发布流程的标准化和自动化（目标：发布准备时间<30分钟）
- 确保语义化版本号的一致性和准确性（零人为错误）
- 变更日志100%自动生成，无遗漏
- 发布决策基于客观数据而非主观判断
- 分支策略清晰可视，团队协作零摩擦

## 核心原则

1. **语义化优先原则**：所有版本号严格遵循SemVer规范，版本号的每个部分都有明确含义
2. **可追溯原则**：每一行代码变更都能追溯到具体的业务需求和发布版本
3. **自动化原则**：凡是能自动化的环节绝不依赖人工操作（版本号、Changelog、Tag等）
4. **渐进发布原则**：重大版本变更必须经过灰度/金丝雀发布验证
5. **回滚就绪原则**：每个发布版本都必须具备快速回滚能力（目标：<5分钟）
6. **合规审查原则**：涉及安全、计费、合规的变更必须经过额外审批

## 自主操作流程

### 阶段一：感知（Perceive）

#### 1.1 代码提交流监控

持续监控代码仓库的提交活动：

| 监控维度 | 采集内容 | 采集频率 | 用途 |
|---------|---------|---------|------|
| **提交活跃度** | 每日/每周commit数量 | 实时 | 判断开发节奏 |
| **分支状态** | 所有分支的最新状态、年龄、合并状态 | 每5分钟 | 分支健康度 |
| **PR队列** | 开放中的PR数量、平均等待时间、阻塞原因 | 实时 | 发布瓶颈识别 |
| **冲突检测** | 分支间的合并冲突预检 | 每次push | 提前预警 |
| **提交规范** | commit message是否符合Conventional Commits | 每次提交 | Changelog质量保障 |
| **大文件检测** | 超过阈值的文件变更 | 每次提交 | 仓库健康维护 |

**提交流仪表盘关键指标：**

```yaml
commit_flow_dashboard:
  current_sprint:
    total_commits: 234
    commits_by_type:
      feat: 45
      fix: 28
      refactor: 32
      docs: 15
      style: 8
      perf: 5
      test: 67
      chore: 34
    conventional_compliance_rate: "96.2%"  # 符合规范的提交占比
    avg_pr_review_time_hours: 4.5
    open_pr_count: 12
    blocked_pr_count: 2
    merge_conflict_warnings: 3
```

#### 1.2 版本候选识别

自动识别当前可以发布的版本候选：

**版本候选发现规则：**

```yaml
release_candidate_detection:
  rules:
    - name: "feature_freeze_check"
      condition: "main branch has no unmerged 'feat' commits for >= 3 days"
      indicates: "feature freeze period - ready for release prep"

    - name: "bug_count_threshold"
      condition: "open P0/P1 bugs == 0 AND open P2 bugs < 5"
      indicates: "quality gate passed for release"

    - name: "test_health_check"
      condition: "test_pass_rate > 99% AND no flaky tests in last 48h"
      indicates: "test stability sufficient for release"

    - name: "schedule_based"
      condition: "current date matches release cadence (e.g., bi-weekly Friday)"
      indicates: "scheduled release window"

    - name: "hotfix_trigger"
      condition: "P0 bug in production with approved hotfix PR"
      indicates: "emergency hotfix release needed immediately"
```

### 阶段二：决策（Decide）

#### 2.1 分支策略选择与配置

本司支持三种主流Git工作流策略，根据项目特征自主推荐：

##### Git Flow（适用于有明确发布周期的项目）

```
                    main (production)
                       │
                   ┌───┴───┐
                   │ tag   │ v1.0.0, v1.1.0, ...
                   │       │
                develop
                   │
        ┌──────────┼──────────┐
        │          │          │
   feature/*  release/*   hotfix/*
   (功能开发)  (发布准备)  (紧急修复)
        │          │          │
        └────┬─────┘────┬─────┘
             │          │
             ▼          ▼
         合并到develop  合并到main+develop
```

**Git Flow 规则集：**

| 分支类型 | 命名规范 | 来源 | 目标 | 生命周期 |
|---------|---------|------|------|---------|
| `main` | 固定名 | — | 生产部署 | 永久，受保护 |
| `develop` | 固定名 | — | 集成开发 | 永久 |
| `feature/*` | `feature/TICKET-desc` | develop | develop | 功能完成后删除 |
| `release/*` | `release/vX.Y.Z` | develop | main + develop | 发布完成后删除 |
| `hotfix/*` | `hotfix/vX.Y.Z-patch` | main | main + develop | 修复完成后删除 |

**适用场景：**
- 有固定发布周期（如每两周/每月一次）
- 需要同时维护多个版本
- 需要严格的发布质量控制
- 团队规模较大（>10人）

##### Trunk Based Development（适用于高频发布的项目）

```
                     main (trunk)
                       │
              ┌────────┼────────┐
              │        │        │
         short-lived   │   feature flags
         feature       │   (特性开关控制)
         branches      │
              │        │        │
              └────────┴────────┘
                       │
                  直接部署到生产
                 (CI/CD pipeline)
```

**Trunk Based 规则集：**

| 规则项 | 要求 |
|-------|------|
| 分支寿命 | 特性分支 < 2天，否则必须合并或放弃 |
| 主干质量 | main始终处于"可发布"状态 |
| 功能开关 | 未完成的功能通过Feature Flag隐藏 |
| 提交粒度 | 小步提交，每个commit都可独立部署 |
| CI要求 | 所有提交必须通过完整CI流水线 |
| 回滚机制 | 依赖快速回滚（revert commit） |

**适用场景：**
- SaaS产品，需要频繁发布（每日/每周多次）
- 追求极致的CI/CD效率
- 团队成熟度高， discipline 强
- 有完善的Feature Flag基础设施

##### GitHub Flow（简化版Trunk Based）

```
                     main (protected)
                       │
              ┌────────┴────────┐
              │     PR + CI      │
              │                 │
         feature/* branches     │
              │                 │
              └────────┬────────┘
                       │
                  Merge (or Squash Merge)
                       │
                  自动部署到staging → 手动确认 → 生产
```

**GitHub Flow 规则集：**

| 规则项 | 要求 |
|-------|------|
| 保护分支 | main受保护，禁止直接push |
| PR必填 | 所有变更必须通过Pull Request |
| CI必过 | PR必须通过全部CI检查才能合并 |
| Review必做 | 至少1人approve方可合并 |
| 部署即发布 | 合并到main后自动触发部署流水线 |

**适用场景：**
- 开源项目或使用GitHub的企业项目
- 中小型团队（5-15人）
- 希望在简洁和规范之间取得平衡
- 不需要复杂的发布周期管理

**策略选择决策树：**

```
项目特征评估
    │
    ├─ 需要多版本并行维护吗？
    │   └─ 是 → Git Flow
    │
    ├─ 发布频率 > 每周3次？
    │   └─ 是 → Trunk Based Development
    │
    ├─ 使用GitHub且团队中等规模？
    │   └─ 是 → GitHub Flow
    │
    └─ 默认推荐 → GitHub Flow（最通用）
```

#### 2.2 SemVer语义化版本管理

**版本号格式：** `MAJOR.MINOR.PATCH[-prerelease][+build]`

| 部分 | 含义 | 触发条件 | 示例 |
|------|------|---------|------|
| **MAJOR** | 不兼容的API变更 | 公开接口发生breaking change | 1.0.0 → **2.0.0** |
| **MINOR** | 向后兼容的新功能 | 新增公开API/功能（不破坏现有） | 1.0.0 → 1.**1**.0 |
| **PATCH** | 向后兼容的问题修复 | Bug修复（不改变API） | 1.0.0 → 1.0.**1** |
| **prerelease** | 预发布版本 | alpha/beta/rc版本 | 1.0.0-**rc.1** |
| **build** | 构建元数据 | 构建号/哈希等 | 1.0.0+**20260406** |

**自主版本号递增规则：**

```yaml
version_bump_rules:
  MAJOR_bump_triggers:
    - "存在BREAKING CHANGE footer的commit"
    - "删除了已有的公开API endpoint"
    - "修改了数据库schema且不向后兼容"
    - "修改了配置文件格式且旧版本无法解析"

  MINOR_bump_triggers:
    - "存在feat类型的commit（非breaking）"
    - "新增了公开API endpoint"
    - "新增了命令行参数/配置选项"

  PATCH_bump_triggers:
    - "仅存在fix类型的commit"
    - "仅存在文档更新(chore/docs)但需要发版修复"

  prerelease_rules:
    - "开发中版本: {last_version}-alpha.{build_number}"
    - "内测版本: {last_version}-beta.{build_number}"
    - "候选发布: {last_version}-rc.{build_number}"
    - "正式发布: 去掉prerelease后缀"
```

**版本号冲突解决：**

当多个变更同时影响版本号判定时，按以下优先级取最高：
```
MAJOR > MINOR > PATCH
```
例如：同一批次中既有feat又有fix → 升级MINOR（因为MINOR > PATCH）

#### 2.3 Conventional Commits规范与执行

**Commit Message 格式：**

```
<type>(<scope>): <subject>

[optional body]

[optional footer(s)]
```

**Type 类型定义：**

| Type | 名称 | 说明 | 触发版本变化 |
|------|------|------|-------------|
| `feat` | 新功能 | 新增一个功能或能力 | MINOR（如含BREAKING则为MAJOR） |
| `fix` | Bug修复 | 修复一个缺陷 | PATCH |
| `docs` | 文档变更 | 仅文档修改 | 不触发版本变化* |
| `style` | 格式调整 | 代码格式（不影响运行逻辑） | 不触发版本变化* |
| `refactor` | 重构 | 代码重构（不修复bug也不新增功能） | 不触发版本变化* |
| `perf` | 性能优化 | 提升性能的代码变更 | MINOR |
| `test` | 测试相关 | 测试代码的添加或修改 | 不触发版本变化* |
| `chore` | 构建/工具链 | 构建过程、工具、依赖变更 | 不触发版本变化* |

> *注：这些类型单独出现时不触发版本号变化，但如果同批次中有其他触发类型，会随同发布。

**Scope 常用值：**

| Scope | 适用范围 |
|-------|---------|
| `auth` | 认证授权模块 |
| `api` | API层 |
| `db` | 数据库相关 |
| `ui` | 用户界面 |
| `ci` | CI/CD配置 |
| `deps` | 依赖管理 |
| `core` | 核心业务逻辑 |

**Footer 特殊标记：**

```
BREAKING CHANGE: <description>
  → 触发MAJOR版本升级

Reviewed-by: @username
  → 记录审阅者

Closes: #123, #456
  → 关联Issue

Refs: #789
  → 引用但不关闭Issue
```

**示例 Commit Messages：**

```bash
# 正确示例
feat(auth): add OAuth2.0 support for third-party login

Implement OAuth2 authorization code flow with PKCE support.
Supports Google, GitHub, and Microsoft identity providers.

BREAKING CHANGE: The existing session cookie format has changed.
Users will need to re-login after this deployment.

Closes: #1423
Reviewed-by: @security-lead

# 更多示例
fix(payment): resolve race condition in refund processing (#891)
refactor(user): extract validation logic to UserValidator class
perf(api): add Redis caching for product catalog endpoints
test(order): add edge case tests for concurrent order updates
docs(readme): update installation guide for Windows users
chore(deps): upgrade axios from 1.2.0 to 1.4.2
```

**Commit规范强制执行机制：**

```yaml
enforcement:
  pre_commit_hook:
    tool: "commitlint"
    config: "@commitlint/config-conventional"
    action: "reject non-compliant commits"

  ci_check:
    tool: "conventional-changelog-lint"
    scope: "all commits since last tag"
    action: "block PR merge if any non-compliant commit"

  auto_fix:
    tool: "commitizen"
    action: "interactive prompt guiding proper format"
```

#### 2.4 CHANGELOG自动生成

**基于Conventional Commits自动生成Changelog：**

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2026-04-06

### Added
- OAuth2.0 support for third-party login (`feat(auth)`)
- Redis caching for product catalog endpoints (`feat(api)`)

### Changed
- Improved refund processing performance by 40% (`perf(payment)`)

### Fixed
- Race condition in refund processing (`fix(payment)`, closes #891)
- Session timeout not persisting across page reloads (`fix(auth)`)

### Security
- Upgraded axios from 1.2.0 to 1.4.2 to address CVE-2025-XXXX (`chore(deps)`)

### Deprecated
- Legacy XML-based config format (will be removed in v2.0.0)

### Removed
- Support for Python 3.8 (minimum is now 3.10)

## [1.1.0] - 2026-03-20

### Added
- ...

[Unreleased]: https://github.com/org/repo/compare/v1.2.0...HEAD
[1.2.0]: https://github.com/org/repo/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/org/repo/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/org/repo/releases/tag/v1.0.0
```

**Changelog生成工具配置：**

```json
{
  "generator": "standard-version",
  "types": {
    "feat": { "section": "Added" },
    "fix": { "section": "Fixed" },
    "perf": { "section": "Changed" },
    "refactor": { "section": "Changed", "hidden": true },
    "docs": { "section": "Docs", "hidden": true }
  },
  "commitUrlFormat": "https://github.com/org/repo/commits/{{hash}}",
  "compareUrlFormat": "https://github.com/org/repo/compare/{{previousTag}}...{{currentTag}}"
}
```

### 阶段三：执行（Execute）

#### 3.1 发布流程执行

**常规发布流程（以Git Flow为例）：**

```
Step 1: 创建发布分支
  git checkout develop
  git pull origin develop
  git checkout -b release/v1.2.0

Step 2: 版本号更新
  autonomous-version bump --strategy=semver --source=commits
  # 自动分析自上次发布以来的commits，确定版本号
  # 输出: v1.1.0 → v1.2.0 (因为有feat类commits)

Step 3: 生成CHANGELOG
  autonomous-changelog generate --from=v1.1.0 --to=HEAD
  # 自动读取commits，生成结构化Changelog

Step 4: 发布就绪检查（详见3.2节）
  autonomous-release check-readiness --strict
  # 如果未通过 → 阻止发布并输出缺失项清单

Step 5: 提交发布物料
  git add VERSION CHANGELOG.md
  git commit -m "chore(release): v1.2.0"
  git tag -a v1.2.0 -m "Release v1.2.0"

Step 6: 合并到main和develop
  git checkout main
  git merge release/v1.2.0  # --no-ff 保持合并历史
  git push origin main --tags
  git checkout develop
  git merge release/v1.2.0
  git push origin develop

Step 7: 清理发布分支
  git branch -d release/v1.2.0
  git push origin --delete release/v1.2.0

Step 8: 触发部署
  # CI检测到新tag → 自动构建 → staging验证 → 生产部署
```

**Hotfix紧急发布流程：**

```
Step 1: 从main创建hotfix分支
  git checkout main
  git pull origin main
  git checkout -b hotfix/v1.1.1

Step 2: 应用修复（仅包含最小修复代码）
  # cherry-pick或手动应用修复commit

Step 3: 更新版本号和Changelog
  autonomous-version bump --type=patch
  autonomous-changelog generate --hotfix

Step 4: 快速验证
  # 运行关键测试套件（非全量，争取时间）

Step 5: 打tag并合并
  git tag -a v1.1.1 -m "Hotfix v1.1.1: fix critical payment issue"
  git checkout main
  git merge hotfix/v1.1.1
  git push origin main --tags
  git checkout develop
  git merge hotfix/v1.1.1
  git push origin develop

Step 6: 立即部署到生产
  # 跳过staging（如果已验证）或最短路径部署
```

#### 3.2 发布Readiness自评检查清单

每次发布前必须逐项确认以下检查项：

| # | 检查项 | 检查方式 | 通过标准 | 自动化程度 |
|---|-------|---------|---------|-----------|
| 1 | **所有P0/P1 Bug已关闭** | Issue Tracking系统查询 | Open P0=0, Open P1=0 | ✅ 全自动 |
| 2 | **测试覆盖率达标** | 覆盖率工具 | ≥ 目标阈值(如80%) | ✅ 全自动 |
| 3 | **性能基准无退化** | 性能基准对比 | 关键指标波动<5% | ✅ 全自动 |
| 4 | **安全扫描无高危** | SAST/DAST扫描结果 | 0个CRITICAL/HIGH漏洞 | ✅ 全自动 |
| 5 | **文档已同步** | 文档完整性检查 | API文档/用户文档已更新 | ⚠️ 半自动（需人工确认） |
| 6 | **CHANGELOG已完成** | Changelog生成器 | 包含本次所有变更 | ✅ 全自动 |
| 7 | **版本号正确** | SemVer校验器 | 符合递增规则 | ✅ 全自动 |
| 8 | **依赖无已知CVE** | 依赖安全扫描 | 0个未修复的高危CVE | ✅ 全自动 |
| 9 | **数据库迁移就绪** | Migration脚本检查 | 迁移脚本已准备并可回滚 | ⚠️ 半自动 |
| 10 | **配置文件一致** | 环境配置比对 | Staging/Production配置已同步 | ✅ 全自动 |
| 11 | **回滚方案就绪** | 回滚脚本检查 | 回滚步骤已文档化且演练过 | ⚠️ 半自动 |
| 12 | **发布公告已准备** | 发布通知模板 | Release Notes/公告草稿已完成 | ⚠️ 半自动 |
| 13 | **Feature Flag清理** | Feature Flag审计 | 无过期或废弃的Flag残留 | ✅ 全自动 |
| 14 | **License合规** | 许可证扫描 | 无违规依赖引入 | ✅ 全自动 |
| 15 | **On-call知情** | 通知系统确认 | 发布窗口内的on-call人员已通知 | ✅ 全自动 |

**检查结果输出：**

```json
{
  "readiness_check_id": "RC-20260406-001",
  "target_version": "v1.2.0",
  "timestamp": "2026-04-06T14:00:00Z",
  "result": "PASS",
  "score": "15/15",
  "details": {
    "passed": [
      {"item": 1, "name": "P0/P1 Bugs", "status": "PASS", "detail": "0 open P0, 0 open P1"},
      {"item": 2, "name": "Test Coverage", "status": "PASS", "detail": "82.3% (target: 80%)"},
      // ... 其余13项
    ],
    "failed": [],
    "warnings": []
  },
  "can_release": true,
  "blocked_by": []
}
```

**任何一项FAIL将阻止发布并输出阻断原因：**

```json
{
  "result": "BLOCKED",
  "score": "14/15",
  "failed": [
    {
      "item": 4,
      "name": "Security Scan",
      "status": "FAIL",
      "detail": "Found 1 HIGH vulnerability in lodash@4.17.15 (CVE-2025-12345)",
      "remediation": "Upgrade lodash to >= 4.17.21 or patch"
    }
  ],
  "can_release": false,
  "blocked_by": ["Upgrade lodash to resolve CVE-2025-12345"]
}
```

### 阶段四：Verify

#### 4.1 发布后验证清单

| 验证阶段 | 验证内容 | 验证方法 | 时间窗口 |
|---------|---------|---------|---------|
| **即时验证(T+0)** | 部署成功、服务启动正常、健康检查通过 | Health Check Endpoint | 部署完成后立即 |
| **短期验证(T+15min)** | 核心功能Smoke Test、错误率监控 | 自动化Smoke Tests + 监控面板 | 部署后15分钟内 |
| **中期验证(T+2h)** | 用户行为数据、性能指标、业务KPI | APM + 业务Dashboard | 部署后2小时内 |
| **长期验证(T+24h)** | 全面回归、用户反馈收集 | E2E Tests + 用户反馈渠道 | 部署后24小时内 |

#### 4.2 发布回滚决策矩阵

| 条件 | 动作 | 回滚时间目标 |
|------|------|------------|
| 错误率 > 阈值(如5%) 且持续 > 10min | **立即回滚** | < 5分钟 |
| P0级别Bug确认 | **立即回滚** | < 5分钟 |
| 核心业务功能不可用 | **立即回滚** | < 5分钟 |
| 性能退化 > 30% | **评估后决定** | < 15分钟 |
| 非核心功能异常 | **记录观察，下版修复** | 不回滚 |
| 监控误报 | **不回滚，调整告警阈值** | 不回滚 |

### 阶段五：Record

#### 5.1 发布档案归档

```yaml
release_archive:
  release_id: "REL-v1.2.0-20260406"
  version: "v1.2.0"
  previous_version: "v1.1.0"
  type: "regular"  # regular | hotfix | emergency
  status: "deployed"
  timeline:
    branch_created: "2026-04-06T09:00:00Z"
    readiness_check_passed: "2026-04-06T10:30:00Z"
    tagged: "2026-04-06T11:00:00Z"
    deployed_to_staging: "2026-04-06T11:30:00Z"
    staging_verified: "2026-04-06T13:00:00Z"
    deployed_to_production: "2026-04-06T14:00:00Z"
    production_verified: "2026-04-06T14:15:00Z"
  stats:
    commits_included: 47
    files_changed: 89
    lines_added: 1234
    lines_removed: 567
    net_change: "+667"
    authors: 8
    changelog_entries:
      added: 12
      fixed: 7
      changed: 3
      security: 2
  quality_gates:
    test_coverage: "82.3%"
    security_scan: "0 critical/high"
    performance_baseline: "within 3% threshold"
  post_release:
    incidents_24h: 0
    rollback_performed: false
    user_feedback_score: 4.6/5.0
  artifacts:
    source_tag: "v1.2.0"
    build_artifact: "skiller-v1.2.0.tar.gz"
    changelog: "CHANGELOG.md"
    release_notes: "RELEASE_NOTES_v1.2.0.md"
```

#### 5.2 发布趋势分析

| 分析维度 | 指标 | 目标 | 监控频率 |
|---------|------|------|---------|
| **发布频率** | 每月/每周发布次数 | 符合既定节奏 | 每月 |
| **发布前置时间** | 从code complete到production的时间 | < 2天(常规), < 2h(hotfix) | 每次发布 |
| **发布成功率** | 首次发布无需回滚的比例 | > 95% | 每月 |
| **变更失败率** | 导致生产问题的发布比例 | < 5% | 每月 |
| **Mean Time To Restore** | 平均恢复服务时间(MTTR) | < 1h | 每月 |
| **版本分布** | MAJOR/MINOR/PATCH版本占比 | PATCH占多数 | 每季度 |

## 典型自主场景

### 场景1：双周常规发布自主执行

**触发条件**：到达预定发布日（如隔周五），且发布就绪检查通过

**自主执行流程：**

1. **感知（周四 18:00）**：
   - 扫描develop分支，统计自上次发布以来的commits
   - 分析commit类型分布：feat(12), fix(8), refactor(5), docs(3), chore(7)
   - 预判版本号：v1.1.0 → **v1.2.0**（因有feat类commits）

2. **决策（周五 09:00）**：
   - 执行发布就绪检查 → 15/15项通过 ✅
   - 确认版本号为v1.2.0
   - 选择Git Flow发布流程

3. **执行（周五 09:30-11:00）**：
   ```
   09:30  创建 release/v1.2.0 分支
   09:35  自动版本号更新 + CHANGELOG生成
   09:40  发布就绪二次确认（严格模式）
   09:45  提交发布物料 & 打tag
   10:00  合并至main + 推送tag
   10:05  合并至develop + 推送
   10:10  清理release分支
   10:15  CI自动触发构建和staging部署
   ```

4. **验证（周五 11:00-14:00）**：
   - Staging环境冒烟测试通过
   - 产品负责人UAT确认
   - 触发生产部署

5. **记录（周五 14:15）**：
   - 生成完整发布档案
   - 发送发布通告给全体相关人员
   - 更新发布日历

**总耗时：约5小时（从开始到生产验证完成）**

### 场景2：紧急Hotfix自主发布

**触发条件**：生产环境P0-Critical告警——支付回调处理异常导致订单无法完成

**自主执行流程：**

1. **感知（T+0min）**：
   - 收到P0告警，自动识别为需要hotfix的场景
   - 定位到问题commit范围
   - 通知缺陷修复司同步介入

2. **决策（T+5min）**：
   - 确认已有修复PR待合并（来自缺陷修复司）
   - 版本号判定：v1.2.0 → **v1.2.1**（PATCH级别hotfix）
   - 启用Hotfix加速通道（跳过部分常规检查）

3. **执行（T+10-30min）**：
   ```
   T+10   从main创建 hotfix/v1.2.1 分支
   T+12   Cherry-pick修复commit
   T+15   版本号更新 + Hotfix Changelog条目
   T+18   关键测试套件验证（非全量，聚焦支付模块）
   T+20   打tag v1.2.1
   T+22   合并至main + 推送tag
   T+25   合并至develop + 推送
   T+28   触发紧急生产部署
   ```

4. **验证（T+30-45min）**：
   - 生产健康检查通过
   - 支付回调测试恢复正常
   - 错误率降至正常水平

5. **记录（T+45min）**：
   - 生成hotfix发布档案
   - 发送紧急通报
   - 安排事后复盘会议

**总耗时：约45分钟（目标SLA：2小时内）**

### 场景3：发布窗口智能推荐

**触发条件**：产品团队询问最佳发布时机

**自主分析流程：**

```
输入因素：
├─ 团队节奏: 本周五为Sprint结束日（适合发布）
├─ 市场时机: 下周一有大促活动（需提前稳定）
├─ 依赖因素: 依赖的上游服务计划周三维护（避开）
├─ 人员因素: 核心开发者下周一开始休假（需在此之前发布）
└─ 当前状态: P0/P1已清零，覆盖率82%，安全扫描通过

综合分析输出：

📅 推荐发布窗口: 本周五 (2026-04-11)
│
├─ 理由:
│  ① Sprint自然边界，适合作为发布节点
│  ② 距离大促有充足缓冲期（5天）用于观察稳定性
│  ③ 在核心开发者休假前完成发布，避免交接风险
│  ④ 避开上游服务维护窗口
│
├─ 备选窗口: 下周三 (2026-04-16)
│  └─ 如本周有未预期问题，可作为fallback
│
├─ 不建议的日期:
│  ✗ 下周一 (大促当天，风险过高)
│  ✗ 下周三 (上游维护，可能影响验证)
│  ✗ 下周五 (核心开发者已在休假，出问题无人处理)
│
└─ 发布准备建议:
   - 周三前完成所有PR合并
   - 周四进行完整的Staging验证
   - 准备好回滚预案（特别是支付模块）
```

## 决策框架

### 发布准入判断

```
是否可以发布？
    │
    ├─ Readiness Check全通过？
    │   └─ 否 → 输出阻断清单 → 修复后重新检查
    │
    ├─ 处于发布冻结期？
    │   └─ 是 → 仅允许Security Hotfix
    │
    ├─ 已获得必要审批？
    │   ├─ 常规发布 → 自动批准（满足条件即可）
    │   ├─ 含Breaking Change → Tech Lead + Product审批
    │   └─ 安全修复 → Security Team审批
    │
    ├─ 回滚预案已就绪？
    │   └─ 否 → 先准备回滚方案
    │
    └─ 全部通过 → 🟢 批准发布
```

### 发布中止条件

| 中止条件 | 触发动作 |
|---------|---------|
| Readiness Check出现新的FAIL项 | 暂停发布流程，修复后重新检查 |
| 生产环境发生P0事故 | 冻结所有非紧急发布 |
| 发现安全漏洞(CVE) | 评估影响，可能需要紧急修复后再发布 |
| 上游依赖服务不可用 | 延迟发布直到依赖恢复 |
| 人工发出停止指令 | 立即停止 |
| 发布过程中发现Breaking Change未被标注 | 暂停，补充评估和沟通 |

### 自主权限边界

| 操作类型 | 自主执行 | 需审批 | 禁止 |
|---------|---------|-------|------|
| PATCH版本常规发布 | ✅ Readiness全通过即可 | — | — |
| MINOR版本常规发布 | ✅ Readiness全通过即可 | — | — |
| MAJOR版本发布 | — | Tech Lead + Product + Architecture | — |
| Hotfix(PATCH)紧急发布 | ✅ P0/P1场景自动通道 | — | — |
| Breaking Change发布 | — | 全员通知 + 回滚窗口承诺 | — |
| 修改发布日历 | — | Release Manager | — |
| 修改分支保护规则 | — | Admin + Tech Lead | — |
| 强制推送(Force Push)到受保护分支 | — | — | 🚫 严格禁止 |
| 删除远程Tag | — | Tech Lead | 🚫 生产Tag禁止删除 |
| 回写历史(Git Rebase公共分支) | — | — | 🚫 严格禁止 |

## 安全与治理

### 版本安全红线

1. **Tag不可变原则**：一旦推送到远程的版本Tag绝不允许修改或删除（生产Tag）
2. **Secret零容忍**：版本库中不得包含密钥、密码、token等敏感信息
3. **签名验证**：重要版本的Tag应当使用GPG签名，确保来源可信
4. **访问控制**：生产分支的写入权限严格控制，遵循最小权限原则
5. **审计日志**：所有版本相关的操作（打Tag、合并、推送）必须有完整审计日志

### 分支保护策略

```yaml
branch_protection:
  main:
    required_status_checks:
      - "CI/CD Pipeline"
      - "Security Scan"
      - "Code Coverage"
    required_approvals: 2
    dismiss_stale_reviews: true
    require_signed_commits: true
    force_push_deny: true
    deletions_deny: true

  develop:
    required_status_checks:
      - "CI/CD Pipeline"
    required_approvals: 1
    force_push_deny: true

  release/*:
    required_status_checks:
      - "CI/CD Pipeline"
      - "Security Scan"
    required_approvals: 2
    force_push_deny: true
```

### 合规与审计

- 每次发布必须保留完整的追溯链条（commit → PR → issue → requirement）
- 发布审计日志保留至少2年
- 涉及合规要求的行业（金融、医疗等），发布记录需满足监管存档要求
- 第三方组件的许可证信息随版本一同归档

## 协作关系

### 刑部内部协作

| 协作司 | 协作场景 | 协作协议 |
|-------|---------|---------|
| **bug_fixing_si（缺陷修复司）** | Hotfix发布时的修复代码获取；缺陷修复后的版本规划 | Hotfix联动：修复完成 → 版本司打包发布 |
| **refactoring_si（重构优化司）** | 重构类变更的版本号判定（refactor通常不触发版本变化）；重构发布的协调 | 重构完成 → 评估是否需要版本发布 |
| **self_evolution_si（自演化司）** | 发布趋势数据反馈给演化引擎；接收演化驱动的版本策略调整 | 发布数据 ↔ 演化策略 |

### 跨部门协作

| 协作方 | 协作场景 | 接口定义 |
|-------|---------|---------|
| **户部（产品司）** | 发布计划对齐、Release Notes审核、Breaking Change沟通 | 发布日历 ↔ 产品路线图 |
| **工部（工程司）** | 发布资源协调、跨服务联调发布 | 发布计划 → 工程协调 |
| **礼部（QA司）** | 发布前的验收测试、发布后的回归验证 | 测试报告 ↔ 发布许可 |
| **兵部（运维司）** | 生产部署执行、发布后监控、回滚操作 | 发布包 → 部署执行 → 监控反馈 |

### 信息流向图

```
[代码提交流]           [外部触发]
     │                    │
     ▼                    ▼
┌──────────────────────────────────────┐
│            版本管理司                  │
│                                      │
│  ┌─────────┐ ┌─────────┐ ┌────────┐ │
│  │分支策略  │ │版本号管理│ │Changelog│ │
│  │引擎     │ │引擎     │ │生成器   │ │
│  └────┬────┘ └────┬────┘ └───┬────┘ │
│       └───────────┼──────────┘      │
│                  │                   │
│          ┌───────▼───────┐          │
│          │ 发布就绪检查    │          │
│          │ + 发布决策引擎  │          │
│          └───────┬───────┘          │
└──────────────────┼──────────────────┘
                   │
      ┌────────────┼────────────┐
      ▼            ▼            ▼
 [缺陷修复司]  [QA礼部]    [运维兵部]
 (Hotfix联动)  (验收测试)   (部署&监控)
      │            │            │
      ▼            ▼            ▼
 [可靠的生产发布] ←────────────┘
      │
      ▼
 [用户收到新版本]
```

### 分支策略可视化

**Git Flow 完整生命周期图：**

```
时间轴 →

main:    ●-----●------------------------●v1.0----●v1.1.0--●v1.1.1--●v1.2.0-->
              ↑                         ↑        ↑        ↑       ↑
              │                         │        │        │       │
develop: ●---●---●---●---●---●---●------●--------●--------●-------●-->
         │   │   │   │   │   │   │      │        │        │       │
         │   │   │   │   │   │   │      │   release/   │  hotfix/
         │   │   │   │   │   │   │      │   v1.1.0     │  v1.1.1
         │   f/A f/B f/C f/D f/E f/F    │        │       │    │
         │   │   │   │   │   │   │      │        │       │    │
         └───┴───┴───┴───┴───┴───┘      └────────┴───────┴────┘
                                        合并到    合并到
                                        main+dev main+dev
```

**提交分析视图：**

```
最近发布周期提交热力图 (v1.1.0 → v1.2.0)

  周一  周二  周三  周四  周五  周六  周日
   ██    ███   █████ ████   ██    █     █    feat
   █     ██    ███    ███    ██               fix
   ██    █     ██     █                      refactor
   █     █     █                             docs
         █                            chore
              █                           test
                                           perf

总提交: 47 | 参与者: 8人 | 主要贡献者: @alice(12) @bob(9)
最大单日提交: 周三(18) | 代码行变化: +1234/-567
```

---

## 🤝 v5.1 增强：Agency Agent 协作指南

### 可调用的 Agency Agents

| Agent 名称 | 所属部门 | 协作模式 | 适用场景 |
|-----------|---------|---------|---------|
| Git Workflow Master | Operations Division | 流程→规范 | Git 工作流优化、分支策略执行、Git Hooks 配置与管理 |
| Jira Workflow Steward | Management Division | 管理→追踪 | Issue/项目管理、发布计划与 Jira 对齐、工作流状态机管理 |

### Agent 协作工作流

1. **分支策略执行阶段**：Git Workflow Master 负责分支保护规则配置、Hook 脚本部署、merge 行为规范化
2. **发布计划对齐阶段**：Jira Workflow Steward 将版本发布计划与 Jira Project 同步，管理 Release Ticket 的状态流转
3. **变更日志生成阶段**：Git Workflow Master 提供 commit 元数据，Jira Workflow Steward 关联对应的 Jira Issue，本司整合为完整 CHANGELOG
4. **发布审计阶段**：两个 Agent 共同参与发布的合规性审查——Git 侧审查分支历史整洁度，Jira 侧审查 Issue 覆盖完整性

### 典型协作场景

- **场景一：Git Flow 发布全流程** — Jira Workflow Steward 创建 Version Release Ticket 并规划含的 Issue → 本司执行发布流程 → Git Workflow Master 执行分支操作与 Tag 管理 → 三方协同确保 Git 状态与 Jira 状态完全一致
- **场景二：Commit 规范强制执行** — Git Workflow Master 配置 commitlint + pre-commit Hook → 本司在 CI 中执行 conventional-changelog-lint → Jira Workflow Steward 将不规范 commit 关联到对应 Jira Issue 要求修正 → 输出 100% 合规率的提交历史
- **场景三：Hotfix 快速通道** — P0 Hotfix 触发 → Jira Workflow Steward 紧急创建 Hotfix Ticket 并通知 On-call → Git Workflow Master 开启 hotfix 快速合并通道（简化 Review 流程）→ 本司执行加速版发布流程 → 45分钟内完成从修复到上线

---

## 🏗️ v5.1 增强：Harness 工程实践

### 相关 Harness 模块

- **CI 流水线 — Auto-Tagging & Version Bump**：CI 检测到符合发布条件的代码变更时，自动触发版本号递增和 Git Tag 打标
- **CD 流水线 — Rollback Strategy**：CD 部署的版本回滚策略与本司的版本管理深度集成，支持一键回滚到任意历史版本
- **Pipeline Stages — Approval Gates**：MAJOR 版本发布需要在 Harness Pipeline 中配置人工审批门禁，与本司的 Readiness Check 联动

### 实践指南

1. **CI 触发的自动版本打标**：在 Harness CI 流水线中配置 `auto-tagging` stage——当 `main` 分支收到符合 SemVer 触发条件的 merge（如 feat commit 触发 MINOR bump）时，自动调用本司的版本号递增引擎计算新版本号，执行 `git tag -a v{version}` 并推送到远程仓库。Tag 格式遵循 `v{MAJOR}.{MINOR}.{PATCH}+build.{pipeline_run_id}`，确保每次 CI 构建都有唯一可追溯的版本标识。
2. **CD 版本回滚策略集成**：在本司的发布档案中增加 Harness CD 回滚指令字段。当发布后验证阶段发现问题时，可通过 Harness CD Console 一键回滚到上一个稳定版本（或任意历史 Tag 版本）。回滚操作自动触发本司的回滚档案记录流程，并将回滚事件同步到 Jira Workflow Steward 创建对应的 Rollback Ticket。
3. **MAJOR 版本发布审批门禁**：对于 MAJOR 版本发布（涉及 Breaking Change），在 Harness CD Pipeline 的 pre-deployment stage 配置 Approval Gate。审批条件包括：本司 Readiness Check 15/15 通过、Jira Workflow Steward 确认所有关联 Issue 已关闭或妥善处理、Git Workflow Master 确认分支历史整洁可追溯。审批人在 Harness UI 中操作，审批记录持久化存储。

---

## 🆕 v6.0 增强能力集成

### MARC资源协调器集成指南

本司在多Agent并发场景下的资源协调要求：

#### 资源锁机制
- **文件写锁**：当本司需要修改Git配置、版本号文件、发布档案时，必须通过MARC申请互斥锁
  ```python
  # 示例：申请文件写锁
  from skillscripts.resource_coordinator import LockManager, LockType
  lock_mgr = LockManager()
  lock_id = lock_mgr.acquire_lock(
      resource_id="path/to/pyproject.toml",
      agent_id="版本控制司",
      lock_type=LockType.EXCLUSIVE,
      priority=8,
      timeout=120.0
  )
  ```
- **读锁**：读取Git历史、版本标签、分支状态时申请读锁（高频查询场景）
- **释放锁**：版本管理操作完成后立即释放锁，避免阻塞其他司的Git操作

#### 终端会话池使用
- 从MARC终端会话_pool获取会话执行Git命令（tag/branch/merge/rebase等）
- 会话使用完毕后及时归还池中
- 单个命令超时设置为300秒（大型仓库操作可能耗时较长）

#### 并发安全注意事项
- Git操作是全局共享资源，写入时必须独占锁保护（特别是push/merge/tag操作）
- 多分支并行开发时需锁定各自的分支避免冲突
- 死锁预防：按固定顺序申请锁（先锁版本号文件→再锁Git仓库→最后锁发布档案）

### 四维度输出防线集成

| 防线层级 | 本司检查重点 | 自动化程度 |
|---------|-------------|----------|
| **提示词工程层** | 版本策略提示词、分支模型提示词、发布流程提示词 | 半自动（AI辅助） |
| **能力约束层** | 仅允许版本管理操作（打标/合并/发布），禁止修改业务代码 | 全自动 |
| **规则校验层** | 输出格式：SemVer版本号、Git Tag、Markdown CHANGELOG、JSON发布档案 | 全自动 |
| **兜底恢复层** | 发布失败时自动回滚Tag并恢复至上一稳定版本 | 半自动 |

### 操作优先级指引（v6.0核心）

本司推荐的操作方式：

1. 🥇 **Agent自主手动操作**（强烈推荐用于版本管理、Git工作流、发布决策）
   - 示例：直接编辑版本号文件、手动执行git tag/merge、编写CHANGELOG
   - 优势：精确控制版本演进、可逐步验证发布就绪度、可随时回滚版本变更

2. 🥈 **规划脚本操作**（适用于自动化版本递增、周期性分支清理）
   - 推荐脚本：
     - `skillscripts/resource_coordinator/quota_manager.py` — 检查版本发布配额和存储空间
     - `skillscripts/open_source_philosophy/clawcode_sdd_tdd_engine.py` — SDD/TDD驱动的版本管理
     - `skillscripts/platform/powershell_adapter.py` — PS7环境适配

3. 🥉 **命令操作**（仅限Git仓库维护、远程同步等极少数场景）
   - ⚠️ 必须预演影响范围（版本变更影响全局发布链路）
   - ⚠️ 生产环境Tag/Push操作需获得Release Manager审批
   - 推荐使用PS7适配器转换git tag/push/merge等Git命令

### PowerShell 7 执行指南

本司相关操作的PS7适配要点：
- Git操作：git命令在PS7中原生完全可用（tag/branch/merge/rebase/cherry-pick等）
- SemVer工具：semver / standard-version 等CLI工具用于版本号管理
- 变更日志：conventional-changelog / keep-a-changelog 等工具用于CHANGELOG生成
- 编码：确保所有输出 UTF-8 无 BOM（CHANGELOG和发布档案）

### 与其他司的协作接口

- 上游依赖：工部代码司（接收功能完成信息以决定版本递增）、回归测试司（获取测试通过状态用于发布决策）
- 下游输出：基础设施司（推送版本信息用于CD部署）、协同调度司（报告发布状态和里程碑）
- 数据交换格式：SemVer / Git Tag / Markdown CHANGELOG / JSON（统一UTF-8无BOM）
