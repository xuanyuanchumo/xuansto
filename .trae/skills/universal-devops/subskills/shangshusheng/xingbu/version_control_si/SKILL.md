---
name: version-control-si
parent: universal-devops
department: xingbu
province: shangshusheng
description: |
  版本控制司 - 刑部·夏官司

  【职责】Git工作流、分支策略、发布管理、变更日志

  【触发条件】
  - Git工作流规范和管理
  - 分支策略制定和执行
  - 版本发布和变更日志

  【能力】
  - Git Flow/GitHub Flow支持
  - 分支策略模板
  - Semantic Versioning
  - Changelog自动生成
---

# 版本控制司 (Version Control Si)

> 尚书省 · 刑部 · Universal DevOps v4.0

**状态**: 占位符 - 具体内容由后续任务填充

## 🤖 自主化操作指南 (v7.0)

### 推荐操作模式
| 操作场景 | 推荐模式 | 置信度 | 说明 |
|---------|---------|--------|------|
| Git工作流执行 | SCRIPTED_BATCH | 96% | CLI命令高度标准化，可脚本化 |
| 分支策略管理 | SCRIPTED_BATCH | 94% | Git Flow/GitHub Flow模板化 |
| Semantic Versioning | SCRIPTED_BATCH | 97% | 版本号规则明确，可自动计算 |
| 变更日志生成 | SCRIPTED_BATCH | 98% | 基于commit message自动生成Changelog |

### 常用工具组合
- **读操作**: Read, SearchCodebase, Grep（读取Git log、分支状态、tag信息）
- **写操作**: Write, SearchReplace（创建branch/tag、编写release notes）
- **批量操作**: Git Hook脚本、CI/CD pipeline集成、版本发布自动化工具
- **验证操作**: 分支合规性检查、commit message规范校验、版本一致性验证

### 注意事项
- ⚠️ Commit message必须有意义：禁止`update`、`fix bug`等模糊信息，采用Conventional Commits规范
- ⚠️ 主分支(main/master)必须保持可部署状态：任何合入都必须通过CI且可成功部署
- ✅ 采用"小步快跑"策略：频繁提交小的变更，而非堆积大量改动的一次性大PR
- ✅ 建立分支生命周期管理：完成合并的分支及时清理，避免分支泛滥

## 🔗 资源协调要点 (v7.0)

### 常访问资源
| 资源类型 | 典型路径 | 锁策略建议 |
|---------|---------|-----------|
| REPOSITORY | Git仓库 | DISTRIBUTED (分布式版本控制) |
| BRANCH | 功能分支/发布分支 | SHORT_LIVED (及时清理) |
| TAG | 版本标签(v1.0.0) | IMMUTABLE (不可修改) |
| HOOK | Git Hooks(pre-commit/commit-msg) | ENFORCED (强制执行) |
| RELEASE | 发布说明和Changelog | VERSIONED (按版本归档) |

### 竞争规避策略
1. **分支命名约定**: 统一使用`feature/JIRA-123-description`格式，避免名称冲突
2. **Pull Request模板**: 标准化PR描述模板，包含checklist、测试说明、截图等必填项
3. **合并顺序规则**: 先合并低风险的依赖分支，再合入高风险的功能分支，减少冲突概率

## 💡 开源哲学应用 (v7.0)

### OpenCode 透明化
- 完整的变更历史公开：任何人都可通过Git log查看完整的代码演进历程
- Code Review过程透明：PR的所有讨论、review意见、决策理由都永久保存可追溯
- 发布节奏和计划可视：版本发布日历、当前版本状态、已知issues对全员透明

### OpenClaude 编排
- 智能Commit消息生成：基于代码变更内容自动生成符合规范的commit message
- 冲突预测和预防：分析分支间的差异程度，提前预警可能的合并冲突
- 自动化Release流程：从打tag到生成Changelog到触发CI/CD全流程自动化编排

### Claw-Code 契约驱动
- Commit规范强制门禁：pre-commit hook检查message格式，不符合则拒绝提交
- 分支保护规则(Rulesets): 主分支禁止force push、要求PR review、必须CI通过
- Semantic Versioning自动化：基于commit type(feat/fix/breaking)自动计算下一个版本号
