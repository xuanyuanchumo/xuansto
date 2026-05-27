# 并行化策略

## Core Points
- 完整并行化策略涵盖Git Worktree并行、子代理上下文协商、Fork对话、并行调度规则、冲突解决和资源隔离
- Git Worktree并行：多Agent在不同worktree上并行开发，减少分支切换开销
- 子代理上下文协商：并行Agent间共享只读上下文，写入需协调
- Fork对话：从当前对话分叉出新线程，独立执行后合并结果
- 并行调度算法：基于依赖图分析，无依赖任务并行执行，有依赖任务串行排队

## Applicable Scenarios
- Orchestrator设计多Agent并行执行策略
- 实现Git Worktree并行开发和冲突解决
- 配置并行调度规则和资源隔离机制
