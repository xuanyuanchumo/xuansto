# 3-Strike Protocol 门禁恢复详细文档

## Core Points
- 3-Strike Protocol是门禁检查失败后的渐进式恢复机制，三次递进式尝试解决阻塞
- Strike 1(自动修复)：分析失败原因→自动修正代码/配置→重新运行门禁，适用于编码错误/配置缺失
- Strike 2(策略调整)：更换修复策略→调整参数/方法→重新运行，适用于Strike 1无效的情况
- Strike 3(人工介入)：标记为需人工处理→记录完整上下文→暂停当前流程，避免无限循环
- 每次Strike有超时限制和回退机制，确保不会卡在恢复流程中

## Applicable Scenarios
- 质量门禁失败时的自动恢复流程
- Runtime Supervisor实现渐进式故障恢复
- 设计门禁检查的容错和重试策略
