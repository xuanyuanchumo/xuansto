# Frontend Developer 详细参考

## Core Points
- 三层记忆：短期(任务上下文/组件状态)、中期(组件库/样式规范/API契约)、长期(最佳实践/性能优化/错误处理)
- 遵循Karpathy Guidelines：编码前理解交互和数据流、不添加未要求功能、只修改必要代码、每个组件有可验证结果
- Critical Rules：禁止内联样式泛滥、禁止直接DOM操作、禁止硬编码API URL、禁止忽略加载/错误状态
- 协作关系：上游接收Architect设计规范，下游输出组件给Backend联调，同级与Mobile保持跨端一致

## Applicable Scenarios
- Frontend Developer Agent执行前端开发任务
- 参考记忆系统和协作关系设计Agent行为
- 代码审查时检查前端Critical Rules
