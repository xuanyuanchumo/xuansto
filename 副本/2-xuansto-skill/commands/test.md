---
name: /test
aliases:
  - t
category: workflow
description: 测试执行与验证
trigger: 需要运行测试或验证功能时
---

# /test 命令

## 命令描述

执行测试验证阶段，运行多层测试套件并生成测试报告。该命令确保代码质量符合标准，是SDD+TDD流程的质量保障环节。

## 触发条件

| 触发方式 | 说明 |
|----------|------|
| 命令输入 | 用户输入 `/test` |
| 关键词触发 | 用户提及"测试执行"、"运行测试"、"测试验证" |
| 自动触发 | `/sprint` 命令执行时自动调用Test阶段 |
| 流程触发 | `/implement` 完成后自动进入Test阶段 |

## 命令名称与语法

```
/test [--type=<类型>] [--scope=<范围>] [--report=<报告格式>]
```

## 参数定义

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--type` | enum | 否 | all | 测试类型：all/unit/integration/e2e/performance/security |
| `--scope` | enum | 否 | changed | 测试范围：all/changed/affected |
| `--report` | enum | 否 | html | 报告格式：html/json/junit/console |
| `--coverage` | flag | 否 | true | 生成覆盖率报告 |
| `--parallel` | flag | 否 | true | 并行执行测试 |
| `--fail-fast` | flag | 否 | false | 首次失败即停止 |
| `--retry` | int | 否 | 2 | 失败重试次数 |
| `--timeout` | int | 否 | 30000 | 单个测试超时时间（毫秒） |
| `--update-snapshot` | flag | 否 | false | 更新快照 |

## 执行流程

> 标准四步框架：1. 输入验证 → 2. Agent调度 → 3. 任务执行 → 4. 结果验证

```
┌─────────────────────────────────────────────────────────────┐
│                    测试执行流程                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐                                          │
│  │  环境准备     │                                          │
│  └──────┬───────┘                                          │
│         │                                                   │
│         ▼                                                   │
│  ┌──────────────────────────────────────────────┐          │
│  │              测试执行矩阵                     │          │
│  │                                              │          │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐     │          │
│  │  │ 单元测试 │  │集成测试  │  │E2E测试  │     │          │
│  │  │  ⚡快    │  │  🔄中    │  │  🐢慢   │     │          │
│  │  └────┬────┘  └────┬────┘  └────┬────┘     │          │
│  │       │            │            │           │          │
│  │       └────────────┼────────────┘           │          │
│  │                    │                        │          │
│  │  ┌─────────┐  ┌────▼────┐  ┌─────────┐     │          │
│  │  │性能测试  │  │安全测试  │  │快照测试  │     │          │
│  │  └────┬────┘  └────┬────┘  └────┬────┘     │          │
│  │       │            │            │           │          │
│  │       └────────────┴────────────┘           │          │
│  │                    │                        │          │
│  └────────────────────┼────────────────────────┘          │
│                       │                                     │
│                       ▼                                     │
│  ┌──────────────┐    ┌──────────────┐                      │
│  │  结果汇总     │───▶│  报告生成     │                      │
│  └──────────────┘    └──────┬───────┘                      │
│                             │                               │
│                             ▼                               │
│  ┌──────────────┐    ┌──────────────┐                      │
│  │  质量门禁     │───▶│  输出产物     │                      │
│  └──────────────┘    └──────────────┘                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 测试类型详情

1. **单元测试**
   - 测试单个函数/方法
   - 隔离依赖，使用Mock
   - 执行速度快
   - 覆盖边界条件

2. **集成测试**
   - 测试模块间交互
   - 使用真实依赖或容器
   - 验证数据流
   - 测试API契约

3. **E2E测试**
   - 测试完整用户流程
   - 模拟真实用户操作
   - 验证业务场景
   - 跨系统测试

4. **性能测试**
   - 负载测试
   - 压力测试
   - 基准测试
   - 资源监控

5. **安全测试**
   - 漏洞扫描
   - 渗透测试
   - 依赖检查
   - 合规验证

## 涉及Agent

| Agent | 角色 | 职责 |
|-------|------|------|
| test-architect | 主导 | 测试策略制定 |
| unit-tester | 辅助 | 单元测试 |
| integration-tester | 辅助 | 集成测试 |
| e2e-tester | 辅助 | E2E测试 |
| performance-tester | 辅助 | 性能测试 |
| security-tester | 辅助 | 安全测试 |
| test-maintainer | 辅助 | 测试维护 |
| desktop-tester | 辅助 | 桌面应用测试 |
| ai-penetration-tester | 辅助 | AI渗透测试 |
| qa-engineer | 辅助 | 质量汇总与聚合 |

## 输出格式

### 测试报告结构

```
.sprint/artifacts/testing/
├── reports/
│   ├── test-report.html
│   ├── test-report.json
│   ├── junit.xml
│   └── coverage/
│       ├── index.html
│       ├── lcov.info
│       └── clover.xml
├── screenshots/
│   └── e2e/
│       ├── login-success.png
│       └── login-failure.png
├── videos/
│   └── e2e/
│       └── user-flow.mp4
└── logs/
    └── test-execution.log
```

### test-report.html

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <title>测试报告</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f5f5f5; padding: 20px; }
    .container { max-width: 1200px; margin: 0 auto; }
    .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 12px; margin-bottom: 20px; }
    .header h1 { font-size: 28px; margin-bottom: 10px; }
    .stats { display: grid; grid-template-columns: repeat(5, 1fr); gap: 15px; margin-bottom: 20px; }
    .stat-card { background: white; padding: 20px; border-radius: 8px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .stat-card.passed { border-left: 4px solid #10b981; }
    .stat-card.failed { border-left: 4px solid #ef4444; }
    .stat-card.skipped { border-left: 4px solid #f59e0b; }
    .stat-value { font-size: 36px; font-weight: bold; margin-bottom: 5px; }
    .stat-label { color: #666; font-size: 14px; }
    .section { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .section h2 { font-size: 20px; margin-bottom: 15px; padding-bottom: 10px; border-bottom: 1px solid #eee; }
    .test-suite { margin-bottom: 15px; }
    .suite-header { display: flex; align-items: center; gap: 10px; padding: 10px; background: #f9fafb; border-radius: 6px; cursor: pointer; }
    .suite-header:hover { background: #f3f4f6; }
    .suite-icon { width: 20px; height: 20px; }
    .suite-icon.passed { color: #10b981; }
    .suite-icon.failed { color: #ef4444; }
    .test-case { padding: 10px 10px 10px 40px; border-bottom: 1px solid #f3f4f6; display: flex; justify-content: space-between; align-items: center; }
    .test-case:last-child { border-bottom: none; }
    .test-name { flex: 1; }
    .test-duration { color: #666; font-size: 12px; }
    .coverage-bar { height: 20px; background: #e5e7eb; border-radius: 10px; overflow: hidden; margin-top: 10px; }
    .coverage-fill { height: 100%; background: linear-gradient(90deg, #10b981, #34d399); }
    .badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: 500; }
    .badge.pass { background: #d1fae5; color: #065f46; }
    .badge.fail { background: #fee2e2; color: #991b1b; }
    .badge.skip { background: #fef3c7; color: #92400e; }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>测试报告</h1>
      <p>生成时间: 2024-01-15 14:30:00 | 执行时间: 45.2s</p>
    </div>

    <div class="stats">
      <div class="stat-card passed">
        <div class="stat-value">156</div>
        <div class="stat-label">通过</div>
      </div>
      <div class="stat-card failed">
        <div class="stat-value">3</div>
        <div class="stat-label">失败</div>
      </div>
      <div class="stat-card skipped">
        <div class="stat-value">5</div>
        <div class="stat-label">跳过</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">164</div>
        <div class="stat-label">总计</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">95.1%</div>
        <div class="stat-label">通过率</div>
      </div>
    </div>

    <div class="section">
      <h2>覆盖率统计</h2>
      <div style="margin-bottom: 15px;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
          <span>语句覆盖率</span>
          <span>87.5%</span>
        </div>
        <div class="coverage-bar">
          <div class="coverage-fill" style="width: 87.5%"></div>
        </div>
      </div>
      <div style="margin-bottom: 15px;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
          <span>分支覆盖率</span>
          <span>82.3%</span>
        </div>
        <div class="coverage-bar">
          <div class="coverage-fill" style="width: 82.3%"></div>
        </div>
      </div>
      <div style="margin-bottom: 15px;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
          <span>函数覆盖率</span>
          <span>91.2%</span>
        </div>
        <div class="coverage-bar">
          <div class="coverage-fill" style="width: 91.2%"></div>
        </div>
      </div>
      <div>
        <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
          <span>行覆盖率</span>
          <span>88.7%</span>
        </div>
        <div class="coverage-bar">
          <div class="coverage-fill" style="width: 88.7%"></div>
        </div>
      </div>
    </div>

    <div class="section">
      <h2>测试套件详情</h2>
      <div class="test-suite">
        <div class="suite-header">
          <span class="suite-icon passed">✓</span>
          <span>UserService (12 tests)</span>
          <span class="badge pass">全部通过</span>
        </div>
        <div class="test-case">
          <span class="test-name">应该成功创建用户</span>
          <span class="test-duration">45ms</span>
        </div>
        <div class="test-case">
          <span class="test-name">邮箱已存在时应该抛出错误</span>
          <span class="test-duration">32ms</span>
        </div>
      </div>
      <div class="test-suite">
        <div class="suite-header">
          <span class="suite-icon failed">✗</span>
          <span>AuthService (8 tests)</span>
          <span class="badge fail">2 失败</span>
        </div>
        <div class="test-case">
          <span class="test-name">应该验证有效Token</span>
          <span class="badge fail">失败</span>
          <span class="test-duration">Timeout</span>
        </div>
      </div>
    </div>
  </div>
</body>
</html>
```

### test-report.json

```json
{
  "summary": {
    "total": 164,
    "passed": 156,
    "failed": 3,
    "skipped": 5,
    "duration": 45234,
    "passRate": 95.1
  },
  "coverage": {
    "lines": 88.7,
    "statements": 87.5,
    "branches": 82.3,
    "functions": 91.2
  },
  "suites": [
    {
      "name": "UserService",
      "file": "src/modules/user/__tests__/user.service.spec.ts",
      "tests": [
        {
          "name": "应该成功创建用户",
          "status": "passed",
          "duration": 45
        },
        {
          "name": "邮箱已存在时应该抛出错误",
          "status": "passed",
          "duration": 32
        }
      ],
      "status": "passed",
      "duration": 234
    }
  ],
  "failures": [
    {
      "suite": "AuthService",
      "test": "应该验证有效Token",
      "error": "Timeout: Async callback was not invoked within 30000ms timeout",
      "stack": "at Timeout._onTimeout (node:internal/timers:568:17)"
    }
  ]
}
```

## 测试执行矩阵

| 测试类型 | 触发时机 | 执行环境 | 超时时间 |
|----------|----------|----------|----------|
| 单元测试 | 每次提交 | 本地/CI | 30s |
| 集成测试 | PR合并前 | CI容器 | 5min |
| E2E测试 | 部署前 | 测试环境 | 15min |
| 性能测试 | 发布前 | 预发布环境 | 30min |
| 安全测试 | 每日/发布前 | CI/专用环境 | 1h |

## 示例用法

### 示例1：运行所有测试

```
/test
```

### 示例2：仅运行单元测试

```
/test --type=unit
```

### 示例3：运行变更相关测试

```
/test --scope=changed
```

### 示例4：生成JSON报告

```
/test --report=json
```

### 示例5：失败重试

```
/test --retry=3 --fail-fast
```

### 示例6：性能测试

```
/test --type=performance --timeout=60000
```

## 质量门禁

| 门禁标识 | 阻塞级别(BLOCK/WARN) | 通过标准 |
|----------|----------------------|----------|
| GATE-005 | BLOCK | 单元测试通过率100%、核心业务逻辑覆盖率 ≥ 90% |
| GATE-006 | BLOCK | 集成测试通过率100%、API契约验证通过 |
| TEST-PASS | BLOCK | 测试通过率100%、无安全漏洞、E2E通过100% |
| GATE-011 | BLOCK | E2E测试通过率100%、用户流程验证通过 |
测试完成后自动检查：

| 门禁项 | 要求 | 状态 |
|--------|------|------|
| 测试通过率 | 100% | 必须 |
| 代码覆盖率 | ≥ 设定值 | 必须 |
| 无安全漏洞 | 0高危 | 必须 |
| 性能基准 | 无退化 | 必须 |
| E2E通过 | 100% | 必须 |

### 覆盖率要求

| 模块类型 | 最低覆盖率 |
|----------|------------|
| 核心业务逻辑 | 90% |
| API控制器 | 80% |
| 工具函数 | 85% |
| 数据访问层 | 75% |
| 配置文件 | 50% |

## 测试失败处理

```
❌ 测试失败处理流程：

1. 分析失败原因
   ├── 断言失败 → 检查预期值
   ├── 超时失败 → 优化性能或调整超时
   ├── 环境问题 → 检查依赖服务
   └── 代码缺陷 → 修复并重新测试

2. 自动重试
   └── 失败测试自动重试指定次数

3. 生成修复建议
   └── AI分析失败原因，提供修复建议

4. 阻断后续流程
   └── 测试未通过时禁止部署
```

## 性能基准

| 指标 | 基准值 | 警告阈值 |
|------|--------|----------|
| 单元测试总时间 | < 30s | > 60s |
| 集成测试总时间 | < 5min | > 10min |
| E2E测试总时间 | < 15min | > 30min |
| 单个测试时间 | < 5s | > 10s |

## 相关命令

- `/implement` - TDD实施
- `/sprint` - 启动完整冲刺
- `/plan` - 计划制定
