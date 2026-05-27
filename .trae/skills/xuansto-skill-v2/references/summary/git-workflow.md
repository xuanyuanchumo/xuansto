# Git工作流参考文档

## Core Points
- 分支模型：main(生产)、develop(开发)、feature/*(功能)、release/*(发布)、hotfix/*(热修复)
- 提交规范：Conventional Commits格式(type(scope): subject)，type含feat/fix/docs/refactor/test等
- PR流程：创建PR→自动检查→Code Review→合并，要求至少1个审批
- 回滚策略：git revert(安全回滚)、git reset(本地回滚)、紧急回滚流程
- 分支保护规则：main/develop分支保护、禁止force push、要求PR审查

## Applicable Scenarios
- DevOps Engineer Agent配置Git工作流和分支保护
- Code Reviewer Agent执行PR审查流程
- 项目Git规范建立和执行
