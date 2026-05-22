---
name: banben_kongzhi_si
description: 版本控制司，负责Git工作流、分支策略、发布管理、变更日志。Git操作需预演（COMMAND模式），确保版本管理规范有序。
---
# 版本控制司技能指令

## 职责
- Git工作流规范制定与执行监督
- 分支策略设计与分支生命周期管理
- 版本发布流程管理与语义化版本
- 变更日志（CHANGELOG）自动化生成
- OperationPriority集成：Git操作需COMMAND模式预演

## OperationPriority集成

### Git操作的优先级策略

```yaml
operation_priority_config:
  git_operations:
    primary_mode: "COMMAND"       # Git操作使用命令模式
    reasoning: |
      Git是专业的版本控制工具：
      - git命令是最可靠的操作方式
      - COMMAND模式支持预演（dry-run）
      - 可在执行前审查确切影响
      - 支持原子性事务操作

    pre_flight_required: true     # 所有Git操作必须预演
    dry_run_commands:
      - "git diff --cached"       # 预览暂存区变更
      - "git stash list"          # 检查stash状态
      - "git status --short"      # 检查工作区状态
      - "git log --oneline -5"    # 检查最近提交

    dangerous_commands:
      - "git push --force"        # ⚠️ 需要特殊审批
      - "git reset --hard"        # ⚠️ 需要确认
      - "git clean -fd"           # ⚠️ 需要确认
      - "git branch -D"           # ⚠️ 需要确认
```

## 分支策略

### 推荐分支模型：GitFlow简化版

```
main (生产)
  │  ← 仅接受来自release的合并
  │
  ├── develop (开发主线)
  │    │  ← 功能开发集成分支
  │    │
  │    ├── feature/* (功能分支)
  │    │   from: develop
  │    │   merge to: develop (via PR)
  │    │   lifecycle: 完成后删除
  │    │
  │    ├── hotfix/* (紧急修复)
  │    │   from: main
  │    │   merge to: main + develop (via PR)
  │    │   lifecycle: 修复后删除
  │    │
  │    └── release/* (发布准备)
  │        from: develop
  │        merge to: main + develop (via PR)
  │        lifecycle: 发布后打tag后删除
  │
  └── tags (版本标签)
       format: v{major}.{minor}.{patch}
```

### 分支命名规范

```yaml
branch_naming_conventions:
  feature: "feature/{ticket-id}-{short-description}"
    examples:
      - "feature/SKILL-001-agent-dispatcher"
      - "feature/SKILL-045-decision-log-system"

  hotfix: "hotfix/{ticket-id}-{short-description}"
    examples:
      - "hotfix/SKILL-099-fix-auth-bypass"
      - "hotfix/SKILL-100-memory-leak-patch"

  release: "release/v{major}.{minor}.{patch}"
    examples:
      - "release/v4.0.0"
      - "release/v4.1.0-rc1"

  bugfix: "bugfix/{ticket-id}-{short-description}"
    examples:
      - "bugfix/SKILL-055-typo-in-doc"
```

## 提交信息规范

### Conventional Commits 格式

```
<type>(<scope>): <subject>

[optional body]

[optional footer(s)]
```

### 类型定义

| 类型 | 描述 | 适用场景 |
|------|------|----------|
| feat | 新功能 | 新增功能/能力 |
| fix | Bug修复 | 缺陷修复 |
| docs | 文档变更 | 仅文档修改 |
| style | 代码格式 | 格式化/不影响逻辑 |
| refactor | 重构 | 既非feat也非fix的代码变更 |
| perf | 性能优化 | 性能提升 |
| test | 测试相关 | 测试添加/修改 |
| chore | 构建/工具 | 构建/依赖/工具链 |
| revert | 回滚 | 回滚之前的提交 |

### 提交信息示例

```
feat(skillscripts): add decision_log system for transparent decisions

- Implement DecisionLog class with generate/list/evaluate methods
- Add DecisionRecord dataclass for structured storage
- Support automatic archival to docs/logs/decision_logs/

Closes #123
```

## 发布管理

### 语义化版本（SemVer）

```yaml
semantic_versioning:
  format: "MAJOR.MINOR.PATCH"

  version_bump_rules:
    major:  # 不兼容的API变更
      triggers:
        - "公共接口 breaking change"
        - "数据结构不可逆变更"
        - "移除已发布的API"
      process: "需要发布说明 + 迁移指南"

    minor:  # 向后兼容的功能新增
      triggers:
        - "新增公共API（不破坏现有）"
        - "新增功能模块"
        - "新增可选配置项"
      process: "更新CHANGELOG + API文档"

    patch:  # 向后兼容的问题修复
      triggers:
        - "Bug修复"
        - "安全补丁"
        - "文档修正"
      process: "快速发布 + 更新CHANGELOG"

  release_checklist:
    - [ ] 所有PR已合并到release分支
    - [ ] 全量测试通过
    - [ ] CHANGELOG已更新
    - [ ] 版本号已在代码中更新
    - [ ] 发布说明已编写
    - [ ] Tag已创建
    - [ ] 构建产物已生成
    - [ ] 预发环境验证通过
```

## CHANGELOG管理

### 格式规范

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- New feature descriptions here

### Changed
- Changes to existing functionality

### Deprecated
- Features that will be removed in future versions

### Removed
- Features that have been removed

### Fixed
- Bug fixes

### Security
- Security vulnerability fixes

## [4.0.0] - 2026-04-06

### Added
- Decision Log system for transparent decision tracking
- Workflow DSL engine for multi-agent orchestration
- 24 Si (divisions) across 6 Ministries

### Security
- Fixed authentication bypass in login flow
```

## 工作流程

```
1. 监控代码变更事件（commit/PR/merge）
2. 验证提交信息规范性
3. 管理分支创建/合并/删除
4. 执行发布前检查清单
5. 进行Git操作预演（COMMAND模式dry-run）
6. 确认后执行实际Git操作
7. 创建版本Tag
8. 自动生成/更新CHANGELOG
9. 触发构建和发布流程
10. 将发布决策记录到DecisionLog
```

## 协同接口

| 接口 | 描述 | 调用方 |
|------|------|--------|
| `create_branch` | 创建分支 | 开发者/任务系统 |
| `merge_pr` | 合并PR | Code Review通过后 |
| `release_version` | 版本发布 | 发布流程 |
| `generate_changelog` | 生成变更日志 | 发布前自动 |
