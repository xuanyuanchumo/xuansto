# Git Worktree 并行开发参考文档

> 版本: 3.2.0 | 更新日期: 2026-05-06 | 编码: UTF-8 without BOM | 行尾: LF

---

## 概述

Git worktree 允许在同一仓库中同时检出多个分支到不同目录，使AI Agent能够并行开发多个功能而无需频繁切换分支。本文档介绍git-stint、worktrunk、wt等工具的使用模式，以及跨分支经验同步策略。

---

## Git Worktree 基础

### 核心概念

Git worktree是Git 2.5+引入的功能，允许一个仓库同时拥有多个工作目录，每个目录检出不同分支。

```bash
# 创建worktree
git worktree add ../feature-auth feature/auth
git worktree add ../feature-api feature/api

# 查看所有worktree
git worktree list

# 删除worktree
git worktree remove ../feature-auth
```

### Agent并行开发模型

```
主仓库 (main)
  ├── worktree/feature-auth    → Agent A: 认证模块
  ├── worktree/feature-api     → Agent B: API模块
  ├── worktree/bugfix-123      → Agent C: Bug修复
  └── worktree/refactor-core   → Agent D: 核心重构
```

---

## 工具集成

### git-stint

git-stint 是面向AI Agent的worktree生命周期管理工具，自动化创建、同步和清理。

```yaml
git_stint:
  version: "2.1.0"
  commands:
    create:
      description: "创建worktree并配置Agent工作环境"
      usage: "git stint create <branch> <agent_id>"
      options:
        --base: 基于哪个分支创建（默认main）
        --sync: 是否自动同步主分支变更
        --cleanup: 完成后是否自动清理

    sync:
      description: "同步主分支变更到所有worktree"
      usage: "git stint sync [--rebase|--merge]"

    status:
      description: "查看所有worktree状态"
      usage: "git stint status"

    cleanup:
      description: "清理已完成或过期的worktree"
      usage: "git stint cleanup [--force] [--older-than 7d]"
```

### worktrunk

worktrunk 提供worktree的分支管理策略和合并协调。

```yaml
worktrunk:
  version: "1.3.0"
  features:
    - 分支依赖图管理
    - 冲突预检测
    - 合并队列编排
    - 变更影响分析
  config:
    merge_strategy: rebase
    conflict_resolution: manual_with_suggestion
    auto_rebase_interval: 300
```

**分支依赖图：**

```
main ← feature/auth ← feature/auth-oauth
  ↑                      ↑
  ├── feature/api ───────┘
  └── feature/ui
```

### wt（Worktree Tools）

wt 是轻量级worktree快捷操作工具集。

```yaml
wt:
  version: "0.8.0"
  commands:
    wt new <name>:     创建新worktree
    wt cd <name>:      切换到指定worktree
    wt list:           列出所有worktree
    wt rm <name>:      删除worktree
    wt push <name>:    推送指定worktree的变更
    wt diff <n1> <n2>: 比较两个worktree的差异
```

---

## 分支管理策略

### 功能分支策略

```yaml
branch_strategy:
  naming_convention:
    feature: "feature/<agent-id>/<short-desc>"
    bugfix: "bugfix/<issue-id>"
    refactor: "refactor/<module-name>"
    experiment: "exp/<agent-id>/<desc>"

  lifecycle:
    create: "git stint create feature/agent-a/auth-module agent-a"
    develop: "Agent在worktree中独立开发"
    sync: "定期从main同步变更"
    review: "创建PR进行代码审查"
    merge: "审查通过后合并到main"
    cleanup: "git stint cleanup feature/agent-a/auth-module"
```

### 冲突预防

```yaml
conflict_prevention:
  strategies:
    - file_ownership: 每个Agent拥有专属文件区域
    - interface_contracts: 通过接口契约减少交叉修改
    - change_notification: 变更时通知相关Agent
    - periodic_sync: 定期从main同步最新代码

  file_ownership_example:
    agent_a:
      owns: ["src/auth/**", "src/middleware/auth*"]
    agent_b:
      owns: ["src/api/**", "src/routes/api*"]
    shared:
      files: ["src/types/**", "src/config/**"]
      strategy: "先到先得+通知机制"
```

---

## 跨分支经验同步

### 知识共享机制

```yaml
experience_sync:
  mechanisms:
    anti_pattern_broadcast:
      description: "Agent发现反模式时广播到所有worktree"
      channel: "knowledge_bus"
      format:
        pattern_name: string
        description: string
        affected_files: list
        resolution: string

    solution_sharing:
      description: "通用解决方案跨分支共享"
      trigger: "Agent解决通用问题时"
      target: "所有活跃worktree的知识库"

    test_pattern_sync:
      description: "测试模式和工具函数同步"
      scope: "test-utils, fixtures, mocks"
      direction: "bidirectional"
```

### 经验同步流程

```
Agent A 发现反模式
    │
    ├── 记录到本地知识库
    ├── 广播到知识总线
    │
    ▼
Agent B 收到广播
    │
    ├── 检查自身worktree是否受影响
    ├── 如受影响，应用解决方案
    └── 确认同步完成
```

---

## 与xuansto-skill的集成

| xuansto模块 | Worktree功能 | 集成方式 |
|------------|-------------|---------|
| Agent Registry | Agent-Worktree绑定 | Agent分配到专属worktree |
| Knowledge Base | 经验同步 | 跨worktree知识共享 |
| Quality Gates | 分支质量检查 | 合并前门禁验证 |
| CI/CD | 并行构建 | 每个worktree独立CI流水线 |

---

> 本文档由 Multi-Agent SDD/TDD Orchestrator 维护 | 最后更新: 2026-05-06
