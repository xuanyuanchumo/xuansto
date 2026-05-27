# 智能迭代调度

## Core Points
- 修复优先级矩阵从高到低：阻塞性门禁失败→安全漏洞→编译错误→测试失败→性能问题→代码规范→文档缺失
- 阻塞性门禁失败(BLOCKING_GATE_FAILURE)为最高优先级，必须立即修复
- 迭代策略：每轮迭代按优先级处理缺陷，直到所有阻塞性问题解决
- 迭代预算：每轮迭代有Token预算限制，超出则进入降级模式

## Applicable Scenarios
- Orchestrator设计迭代修复的优先级调度
- Task Coordinator Agent管理缺陷修复顺序
- 质量门禁失败后的迭代恢复流程
