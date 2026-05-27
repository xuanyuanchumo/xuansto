---
id: ws-conv-branch-strategy
type: conventions
project: [待填写]
version: 0.1.0
---

# 分支策略

## 概述

[待填写：项目分支管理策略的整体说明]

## 分支类型

| 分支类型 | 命名规则 | 生命周期 | 用途 | 保护规则 |
|---------|---------|---------|------|---------|
| main | `main` | 永久 | 生产发布分支 | 禁止直接推送，需PR合并 |
| develop | `develop` | 永久 | 开发集成分支 | [待填写] |
| feature | `feature/<ticket>-<描述>` | 临时 | 功能开发 | [待填写] |
| bugfix | `bugfix/<ticket>-<描述>` | 临时 | 缺陷修复 | [待填写] |
| hotfix | `hotfix/<ticket>-<描述>` | 临时 | 紧急修复 | [待填写] |
| release | `release/<版本号>` | 临时 | 发布准备 | [待填写] |

## 命名规则

- 分支名使用小写英文，单词间以 `-` 连接
- 必须包含对应的 ticket/issue 编号
- 描述部分简明扼要，不超过 [待填写] 个字符
- 示例：`feature/PROJ-123-add-user-auth`

## 合并策略

| 源分支 | 目标分支 | 合并方式 | 审查要求 | CI要求 |
|--------|---------|---------|---------|--------|
| feature | develop | Squash / Merge | [待填写] | [待填写] |
| bugfix | develop | Squash / Merge | [待填写] | [待填写] |
| hotfix | main + develop | Merge | [待填写] | [待填写] |
| release | main | Merge | [待填写] | [待填写] |
| develop | release | Cherry-pick / Merge | [待填写] | [待填写] |

## 版本号规范

- 遵循语义化版本：`MAJOR.MINOR.PATCH`
- [待填写：版本号递增规则]

## 分支清理

- 已合并的 feature/bugfix 分支在合并后 [待填写] 小时内删除
- release 分支在发布完成后保留 [待填写] 天

## 变更记录

| 日期 | 变更内容 | 变更人 |
|------|---------|--------|
| [待填写] | [待填写] | [待填写] |
