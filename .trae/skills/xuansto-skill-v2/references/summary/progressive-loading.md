# 渐进式加载披露规范

## Core Points
- 四级加载层次：骨架(Skeleton/2K)→功能(Functional/5K)→增强(Enhanced/10K)→完整(Full/20K)
- 每级加载内容递增：骨架(核心约束+命令概要)→功能(+质量门禁+命令执行)→增强(+知识检索+参考文档+Agent详情)→完整(+脚本集)
- 状态机驱动加载阶段转换，触发矩阵定义转换条件
- 披露(Disclosure)强调透明公开当前加载状态、功能可用性和资源就绪情况

## Applicable Scenarios
- 配置xuansto-skill的渐进式加载策略
- Token Optimizer Agent管理上下文预算分配
- 实现加载状态披露和功能可用性检查
