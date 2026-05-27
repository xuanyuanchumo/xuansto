# 知识工作流详细文档

## Core Points
- 知识服务三种状态：可用态(完整MCP/REST服务)、不可用态(降级为文件系统模式)、维护态(只读)
- 知识注入流程：检索→排序→注入上下文，按Token预算裁剪，优先注入高置信度条目
- 知识沉淀流程：Agent产出→质量评估→去重→入库，低置信度条目标记待验证
- 跨会话持久化：Stop Hook保存关键状态，SessionStart Hook恢复上下文

## Applicable Scenarios
- Knowledge Manager Agent管理知识服务生命周期
- 实现知识注入和沉淀的自动化流程
- 设计跨会话知识持久化策略
