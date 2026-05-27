---
id: ci-cd-pipelines
type: knowledge
category: devops
tags: [CI/CD, 流水线, 持续集成, 持续部署, GitHub Actions, 质量门禁, 桌面应用]
version: 1.6.0
created: 2026-04-29
updated: 2026-04-29
confidence: high
---

# CI/CD 流水线知识

## 流水线阶段

标准 CI/CD 流水线包含以下核心阶段：

| 阶段 | 职责 | 关键活动 |
|------|------|----------|
| **Build** | 编译与构建 | 依赖安装、编译打包、制品生成 |
| **Test** | 质量验证 | 单元测试、集成测试、安全扫描 |
| **Deploy** | 部署发布 | 环境部署、冒烟测试、回滚准备 |

### Build 阶段

- 依赖缓存策略：锁定 `package-lock.json` / `yarn.lock` / `pnpm-lock.yaml` 确保可复现构建
- 构建产物版本化：使用语义化版本（SemVer）标记制品
- 构建环境隔离：使用容器或虚拟环境避免环境差异

### Test 阶段

- 单元测试优先执行，快速反馈
- 集成测试在单元测试通过后触发
- 安全扫描（SAST/DAST）与测试并行执行
- 测试覆盖率报告自动生成并上传

### Deploy 阶段

- 部署前执行冒烟测试验证基本功能
- 支持蓝绿部署、金丝雀发布、滚动更新等策略
- 部署后自动触发健康检查
- 回滚方案预先验证，确保可快速回退

## 基于分支的流水线触发

| 分支模式 | 触发策略 | 部署目标 |
|----------|----------|----------|
| `feature/*` | PR 创建/更新时触发 CI | 无部署，仅构建+测试 |
| `develop` | 合并时触发 CI + CD | 开发环境 |
| `release/*` | 创建时触发 CI + CD | 预发布环境 |
| `main` / `master` | 合并时触发 CI + CD | 生产环境 |
| `hotfix/*` | 创建时触发 CI + CD（紧急） | 生产环境（快速通道） |

### 触发规则

- PR 必须通过所有 CI 检查才允许合并
- `main` 分支保护：要求至少1个审批审查
- `hotfix/*` 分支可跳过部分非关键检查，但安全扫描不可跳过
- 定时构建（Nightly Build）：每日凌晨对 `develop` 分支执行完整测试套件

## 质量门禁集成

CI/CD 流水线与质量门禁体系深度集成，确保每次变更都经过充分验证：

### 门禁嵌入策略

```yaml
build_stage:
  gates:
    - FILE-ENCODING
    - COMMENT-LANGUAGE

test_stage:
  gates:
    - GATE-007
    - GATE-008
    - GATE-010
    - GATE-012

deploy_stage:
  gates:
    - GATE-013
    - GATE-014
    - GATE-015
```

### 门控失败处理

- **BLOCK 级别**：流水线立即终止，阻止合并/部署
- **WARN 级别**：流水线继续执行，但标记警告，需人工确认
- 门禁结果记录到决策日志（Decision Log），确保可追溯

## 桌面应用 CI 考虑

桌面应用的 CI/CD 流水线需要额外关注以下方面：

### 多平台构建

- 需要在对应平台上构建：Windows（NSIS/MSI）、macOS（dmg）、Linux（AppImage/deb/rpm）
- 使用 GitHub Actions 的 `matrix` 策略并行构建多平台
- macOS 构建需要签名证书和公证配置

### 代码签名 CI 集成

- 签名证书通过 CI 密钥管理注入（GitHub Secrets / Vault）
- Windows 使用 Authenticode 签名，macOS 使用 `codesign` + `notarytool`
- 签名失败应阻塞发布流程

### 自动更新流水线

- 发布后自动生成更新清单（`latest.yml` / `latest-mac.yml`）
- 更新包上传到 CDN 或 GitHub Releases
- 端到端验证自动更新流程（检测→下载→安装→重启）

### 桌面应用 CI 检查清单

- [ ] 三平台构建成功
- [ ] 安装包签名验证通过
- [ ] 安装包体积在预期范围内
- [ ] 自动更新清单生成正确
- [ ] 安装/卸载流程测试通过
- [ ] 无原生模块编译错误
