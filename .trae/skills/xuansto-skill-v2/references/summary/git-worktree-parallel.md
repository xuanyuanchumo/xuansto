# Git Worktree 并行开发参考文档

## Core Points
- Git worktree允许同一仓库同时检出多个分支到不同目录，支持AI Agent并行开发
- 工具链：git-stint(轻量worktree管理)、worktrunk(结构化并行开发)、wt(快速切换)
- 跨分支经验同步：高置信度(>0.8)条目自动广播、低置信度需人工确认
- 与xuansto集成：Parallelization Strategy Agent使用worktree实现多任务并行开发

## Applicable Scenarios
- 多Agent并行开发多个功能分支
- 跨分支知识共享和经验同步
- 配置Git worktree工作流和冲突解决策略
