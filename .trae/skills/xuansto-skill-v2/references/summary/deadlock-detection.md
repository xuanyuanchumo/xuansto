# 死锁检测与恢复机制

## Core Points
- Orchestrator维护Agent间依赖关系有向图，节点为活跃Agent，边为等待关系，权重为Token消耗量
- 死锁检测算法：周期性(30秒)检测有向图中的环，发现环即判定死锁
- 恢复策略：选择环中Token消耗最低的Agent终止，释放资源解除死锁
- 事件记录：死锁事件写入审计日志，包含参与Agent、等待链、恢复动作

## Applicable Scenarios
- Orchestrator实现多Agent并行执行的死锁检测
- 设计死锁恢复和资源释放策略
- 分析和调试Agent间循环依赖问题
