# 并行化策略

## 并行化策略概述

参照ECC的并行化模式，通过多Agent协同和资源隔离实现高效并行执行。

## Git Worktree并行

多Agent并行修改不同文件时使用git worktree隔离工作区：

```bash
git worktree add ../agent-a-worktree feature-branch-a
git worktree add ../agent-b-worktree feature-branch-b
```

完成后合并：

```bash
git worktree remove ../agent-a-worktree
git merge feature-branch-a
```

## 子代理上下文协商

Orchestrator评估子代理返回结果，必要时发起追问（最多3轮）。传递目标上下文而非仅查询，确保子代理理解完整意图。

## 迭代检索模式

子代理返回不足时，Orchestrator提供更多上下文后重新检索，逐步逼近目标结果。

## Fork对话

独立任务使用Fork并行执行，避免串行等待。每个Fork拥有独立上下文，完成后由Orchestrator合并结果。

## 并行执行规则

- 每个Agent获得一个清晰输入，产生一个清晰输出
- 输出成为下一阶段的输入
- 不跳过阶段
- 独立任务间使用Fork并行
- 重叠任务间使用git worktree隔离

## 最小并行原则

以最少并行量完成最多工作。新增终端应出于真正需要，而非为了并行而并行。
