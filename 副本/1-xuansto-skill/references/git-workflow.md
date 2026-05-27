# Git工作流参考文档

## 分支模型

### Git Flow模型

Git Flow是一种经典的分支模型，适用于有明确发布周期的项目。

```
                    ┌─────────────────────────────────────┐
                    │             main (生产)              │
                    └─────────────┬───────────────────────┘
                                  │
                    ┌─────────────┴───────────────────────┐
                    │             develop (开发)           │
                    └─────────────┬───────────────────────┘
                                  │
            ┌─────────────────────┼─────────────────────┐
            │                     │                     │
    ┌───────┴───────┐     ┌───────┴───────┐     ┌───────┴───────┐
    │ feature/login │     │ feature/api   │     │ feature/ui    │
    └───────────────┘     └───────────────┘     └───────────────┘
```

#### 分支类型

| 分支类型 | 命名规范 | 说明 | 生命周期 |
|----------|----------|------|----------|
| main | main/master | 生产环境代码，只接受合并 | 永久 |
| develop | develop | 开发集成分支 | 永久 |
| feature | feature/* | 新功能开发 | 临时 |
| release | release/* | 发布准备 | 临时 |
| hotfix | hotfix/* | 紧急修复 | 临时 |

#### 工作流程

```bash
git checkout develop
git checkout -b feature/user-authentication

git add .
git commit -m "feat(auth): 添加用户认证功能"

git checkout develop
git merge --no-ff feature/user-authentication
git branch -d feature/user-authentication

git checkout -b release/v1.0.0
git commit -m "chore(release): 准备v1.0.0发布"

git checkout main
git merge --no-ff release/v1.0.0
git tag -a v1.0.0 -m "Release v1.0.0"

git checkout develop
git merge --no-ff release/v1.0.0
git branch -d release/v1.0.0
```

### GitHub Flow模型

GitHub Flow是一种简化的工作流，适用于持续部署的项目。

```
┌─────────────────────────────────────────────────────┐
│                    main (生产)                       │
├─────────────────────────────────────────────────────┤
│  commit 1 │ commit 2 │ commit 3 │ commit 4          │
└───────────┴──────────┴──────────┴───────────────────┘
       │          │          │
       ▼          ▼          ▼
   ┌───────┐  ┌───────┐  ┌───────┐
   │ PR #1 │  │ PR #2 │  │ PR #3 │
   └───────┘  └───────┘  └───────┘
```

#### 工作流程

```bash
git checkout main
git pull origin main
git checkout -b feature/new-feature

git add .
git commit -m "feat: 添加新功能"

git push origin feature/new-feature

gh pr create --title "添加新功能" --body "功能描述"

gh pr merge --squash
```

### GitLab Flow模型

GitLab Flow结合了Git Flow和GitHub Flow的优点，增加了环境分支。

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│    main     │────>│   staging   │────>│ production  │
└─────────────┘     └─────────────┘     └─────────────┘
       │
       ▼
┌─────────────┐
│  feature/*  │
└─────────────┘
```

#### 环境分支

| 环境 | 分支 | 说明 |
|------|------|------|
| 开发环境 | main | 最新开发代码 |
| 测试环境 | staging | 预发布测试 |
| 生产环境 | production | 生产部署 |

### Trunk Based Development

主干开发模式，适用于CI/CD成熟度高的团队。

```
┌─────────────────────────────────────────────────────┐
│                    trunk/main                        │
│  ──●──●──●──●──●──●──●──●──●──●──●──●──●──●──●──●── │
│     │     │     │     │     │     │                 │
│     └──┐  └──┐  └──┐  └──┐  └──┐  └──┐              │
│        │     │     │     │     │     │              │
│     short-lived branches (< 1 day)                  │
└─────────────────────────────────────────────────────┘
```

#### 核心原则

1. 所有开发在主干进行
2. 短生命周期分支（< 1天）
3. 使用Feature Flag控制发布
4. 持续集成和测试

## 提交规范

### Conventional Commits

#### 格式规范

```
<type>(<scope>): <subject>

<body>

<footer>
```

#### 类型定义

| 类型 | 说明 | 示例 |
|------|------|------|
| feat | 新功能 | feat(auth): 添加OAuth2认证 |
| fix | Bug修复 | fix(api): 修复请求超时问题 |
| docs | 文档更新 | docs(readme): 更新安装说明 |
| style | 代码格式 | style: 格式化代码 |
| refactor | 重构 | refactor(utils): 优化工具函数 |
| perf | 性能优化 | perf(query): 优化数据库查询 |
| test | 测试 | test(auth): 添加认证单元测试 |
| build | 构建系统 | build(docker): 更新Docker配置 |
| ci | CI配置 | ci(github): 添加自动部署流程 |
| chore | 其他 | chore: 更新依赖版本 |
| revert | 回滚 | revert: 回滚提交abc123 |

#### Scope范围

```
feat(api): 添加用户API
feat(ui): 添加登录页面
feat(db): 添加用户表
feat(auth): 添加权限验证
```

#### Subject主题

- 使用祈使句，现在时态
- 首字母小写
- 不以句号结尾
- 限制在50字符内

#### Body正文

```bash
git commit -m "feat(api): 添加用户管理API" -m "
- 添加用户CRUD接口
- 实现分页查询
- 添加权限验证

BREAKING CHANGE: 用户API路径从 /user 改为 /api/v1/users"
```

#### Footer页脚

```bash
git commit -m "fix(api): 修复请求超时问题" -m "
Closes #123
Reviewed-by: 张三
Co-authored-by: 李四 <lisi@example.com>"
```

### 提交模板

#### 配置模板

```bash
git config commit.template .git/commit-template
```

#### 模板文件

```
# <type>(<scope>): <subject>
# 
# type: feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert
# scope: api, ui, db, auth, config, etc.
# subject: 简短描述，不超过50字符
#
# <body>
# 详细描述本次修改的内容
#
# <footer>
# 关联的Issue: Closes #xxx
# 破坏性变更: BREAKING CHANGE: xxx
```

### Commitlint配置

```javascript
module.exports = {
  extends: ['@commitlint/config-conventional'],
  rules: {
    'type-enum': [
      2,
      'always',
      ['feat', 'fix', 'docs', 'style', 'refactor', 'perf', 'test', 'build', 'ci', 'chore', 'revert']
    ],
    'subject-case': [2, 'always', 'lower-case'],
    'subject-max-length': [2, 'always', 50],
    'body-max-line-length': [2, 'always', 72]
  }
};
```

## PR流程

### PR创建规范

#### 标题格式

```
[类型] 简短描述

示例:
[feat] 添加用户认证功能
[fix] 修复登录页面样式问题
[refactor] 重构API响应处理
```

#### PR模板

```markdown
## 变更类型
- [ ] 新功能 (feat)
- [ ] Bug修复 (fix)
- [ ] 重构 (refactor)
- [ ] 文档更新 (docs)
- [ ] 其他

## 变更描述
<!-- 详细描述本次变更的内容 -->

## 关联Issue
<!-- 关联的Issue编号，如 Closes #123 -->

## 变更影响
- [ ] 无破坏性变更
- [ ] 有破坏性变更（请在下方说明）

## 测试情况
- [ ] 已添加单元测试
- [ ] 已添加集成测试
- [ ] 已手动测试

## 检查清单
- [ ] 代码符合项目规范
- [ ] 已更新相关文档
- [ ] 已通过所有测试
- [ ] 已进行代码自审
```

### Code Review规范

#### Review要点

| 类别 | 检查项 |
|------|--------|
| 功能性 | 是否满足需求、边界条件处理 |
| 代码质量 | 可读性、可维护性、性能 |
| 安全性 | 输入验证、权限检查、敏感信息 |
| 测试 | 测试覆盖率、测试质量 |
| 文档 | 注释完整性、文档更新 |

#### Review流程

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   创建PR    │────>│   代码审查   │────>│   合并代码   │
└─────────────┘     └──────┬──────┘     └─────────────┘
                           │
                    ┌──────┴──────┐
                    │             │
              ┌─────┴─────┐ ┌─────┴─────┐
              │  通过     │ │  需修改   │
              └───────────┘ └─────┬─────┘
                                  │
                          ┌───────┴───────┐
                          │  修改后重新提交 │
                          └───────────────┘
```

#### Review评论规范

```markdown
<!-- 必须修改 -->
**[必须]** 这里存在潜在的空指针异常，请添加null检查。

<!-- 建议修改 -->
**[建议]** 考虑使用更高效的算法，可以将时间复杂度从O(n²)降低到O(n)。

<!-- 问题讨论 -->
**[问题]** 这里为什么选择使用单例模式？是否有并发问题？

<!-- 赞赏 -->
**[赞赏]** 这个抽象做得很好，大大提高了代码的可读性。
```

### 合并策略

#### Merge Commit

```bash
git merge --no-ff feature/branch
```

保留完整的分支历史，适合长期分支。

#### Squash Merge

```bash
git merge --squash feature/branch
git commit -m "feat: 添加用户认证功能"
```

将多个提交压缩为一个，保持历史整洁。

#### Rebase Merge

```bash
git rebase main
git checkout main
git merge feature/branch
```

保持线性历史，适合短期分支。

#### 策略选择

| 场景 | 推荐策略 | 原因 |
|------|----------|------|
| 功能分支 | Squash | 保持主分支整洁 |
| 发布分支 | Merge Commit | 保留发布历史 |
| 热修复 | Merge Commit | 便于追踪 |
| 个人开发分支 | Rebase | 保持线性历史 |

## 回滚策略

### 场景分析

```
┌─────────────────────────────────────────────────────┐
│                    回滚决策树                        │
├─────────────────────────────────────────────────────┤
│                                                     │
│  问题发生                                           │
│      │                                              │
│      ▼                                              │
│  是否已推送? ───否──> git reset/commit --amend      │
│      │                                              │
│     是                                              │
│      │                                              │
│      ▼                                              │
│  是否已合并? ───否──> git push --force (谨慎使用)   │
│      │                                              │
│     是                                              │
│      │                                              │
│      ▼                                              │
│  是否紧急? ───是──> git revert                      │
│      │                                              │
│     否                                              │
│      │                                              │
│      ▼                                              │
│  创建修复分支                                       │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### 本地回滚

#### 撤销最近提交（保留修改）

```bash
git reset --soft HEAD~1
```

#### 撤销最近提交（丢弃修改）

```bash
git reset --hard HEAD~1
```

#### 修改最近提交

```bash
git commit --amend -m "新的提交信息"
```

### 远程回滚

#### Revert方式（推荐）

```bash
git revert <commit-hash>
git push origin main
```

创建新的回滚提交，不修改历史。

#### 多个提交回滚

```bash
git revert <oldest-commit>..<newest-commit>
```

#### 回滚合并提交

```bash
git revert -m 1 <merge-commit-hash>
```

`-m 1` 表示保留第一个父提交的变更。

### 紧急回滚流程

```bash
git checkout main
git pull origin main

git revert HEAD --no-edit
git push origin main

git checkout -b hotfix/rollback-$(date +%Y%m%d)
git push origin hotfix/rollback-$(date +%Y%m%d)
```

### 回滚检查清单

- [ ] 确认回滚范围和影响
- [ ] 通知相关团队成员
- [ ] 备份当前代码状态
- [ ] 执行回滚操作
- [ ] 验证回滚结果
- [ ] 更新问题追踪系统
- [ ] 编写事故报告

## 分支保护规则

### GitHub配置

```yaml
branches:
  - name: main
    protection:
      required_pull_request_reviews:
        dismiss_stale_reviews: true
        require_code_owner_reviews: true
        required_approving_review_count: 2
      required_status_checks:
        strict: true
        contexts:
          - ci/tests
          - ci/lint
          - ci/build
      enforce_admins: true
      restrictions:
        users: []
        teams: ["core-team"]
```

### GitLab配置

```yaml
protected_branches:
  - name: main
    push_access_level: maintainer
    merge_access_level: maintainer
    unprotect_access_level: admin
    allowed_to_merge:
      - access_level: maintainer
    allowed_to_push:
      - access_level: no_one
    code_owner_approval_required: true
```

## 最佳实践

### 分支命名规范

```
feature/ISSUE-123-user-authentication
bugfix/ISSUE-456-login-error
hotfix/ISSUE-789-security-patch
release/v1.2.0
experiment/new-architecture
```

### 提交频率

- 小步提交，频繁推送
- 每个提交应该是原子性的
- 避免大批量提交

### 冲突解决

```bash
git fetch origin
git rebase origin/main

# 解决冲突
git add <resolved-files>
git rebase --continue

# 或放弃rebase
git rebase --abort
```

### 敏感信息处理

```bash
# 从历史中删除敏感文件
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch path/to/sensitive-file" \
  --prune-empty --tag-name-filter cat -- --all

# 强制推送（谨慎使用）
git push origin --force --all
```

## 参考资源

- Pro Git: https://git-scm.com/book
- GitHub Flow: https://docs.github.com/en/get-started/quickstart/github-flow
- GitLab Flow: https://docs.gitlab.com/ee/topics/gitlab_flow.html
- Conventional Commits: https://www.conventionalcommits.org
