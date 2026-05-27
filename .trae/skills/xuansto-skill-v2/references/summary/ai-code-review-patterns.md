# AI代码审查模式参考文档

## Core Points
- 四种审查模式：安全优先(注入/认证/数据泄露)、性能(算法/查询/内存)、架构一致性(分层/依赖/契约)、可维护性(命名/复杂度/重复)
- 自动化审查流水线：代码提交→静态分析→AI审查→人工审查→合并
- AI审查触发条件：PR创建/更新、安全敏感文件变更、变更>200行；跳过条件：仅文档/配置变更
- 审查输出格式包含findings(id/severity/category/file/line/message/suggestion)和metrics统计
- 质量度量目标：误报率<15%、漏报率<5%、覆盖率≥90%、平均时间<5min、建议采纳率≥60%

## Applicable Scenarios
- 配置Code Reviewer Agent的审查模式和检查清单
- 设计AI代码审查流水线和触发规则
- 度量审查质量和优化审查效率
