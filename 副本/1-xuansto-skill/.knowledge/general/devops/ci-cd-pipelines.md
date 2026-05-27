---
id: ci-cd-pipelines
type: knowledge
category: devops
tags: [CI/CD, 流水线, 持续集成, 持续部署, GitHub Actions, 质量门禁, 桌面应用]
version: 1.6.0
confidence: high
---

## CI/CD 流水线知识 (版本: 1.6 | 适用: GitHub Actions/通用)

### 核心规则
- 三阶段：Build（编译打包）→ Test（质量验证）→ Deploy（部署发布）
- 依赖缓存锁定 lockfile 确保可复现构建，构建产物版本化
- 单元测试优先执行快速反馈，安全扫描与测试并行
- 分支触发：feature 仅 CI，develop CI+CD 到开发环境，main 到生产
- PR 必须通过所有 CI 检查才允许合并，main 分支保护要求审批
- 桌面应用：多平台 matrix 构建，签名证书通过 CI Secrets 注入
- 质量门禁：BLOCK 级别终止流水线，WARN 级别标记需人工确认

### 代码示例

```yaml
jobs:
  build:
    strategy:
      matrix:
        os: [windows-latest, macos-latest]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - run: npm test
      - run: npm run build
```

### 反模式
- ❌ 未锁定依赖版本 — 构建不可复现
- ❌ 跳过安全扫描的 hotfix — 安全漏洞可绕过 CI
- ❌ 桌面应用未在对应平台构建 — 交叉编译不可靠
