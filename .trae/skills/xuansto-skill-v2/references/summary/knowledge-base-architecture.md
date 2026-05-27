# 三层知识库架构详细定义

## Core Points
- 三层架构：通用知识库(General KB/长期)、工作知识库(Working KB/短期)、经验知识库(Experience KB/中期)
- 通用知识库：项目架构、编码规范、技术选型决策，SQLite+Chroma双引擎
- 工作知识库：当前会话上下文、临时变量、任务状态，内存+文件混合存储
- 经验知识库：历史经验、反模式、跨项目知识，Chroma向量检索
- 并发写入冲突处理：乐观锁+版本号，灾难恢复：检查点+增量备份

## Applicable Scenarios
- Knowledge Manager Agent管理三层知识库
- Token Optimizer Agent优化知识库检索和加载
- 设计知识库存储和检索策略
