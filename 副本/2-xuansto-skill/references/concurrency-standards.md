# 并发任务执行规范

## Token预算分配策略

### 1. 均分策略（Equal Distribution）
- 公式：`budget_per_agent = total_budget / active_agent_count`
- 适用场景：Agent优先级相同、任务复杂度相近
- 优点：简单公平
- 缺点：不考虑Agent实际需求差异

### 2. 优先级加权策略（Priority-Weighted）
- 公式：`budget_i = total_budget × (priority_i / Σpriority_j)`
- 优先级定义：P0=4, P1=3, P2=2, P3=1
- 适用场景：任务优先级明确、核心Agent需要更多Token
- 优点：关键任务获得更多资源

### 3. 主从策略（Master-Worker）
- 主Agent获得70%预算，从Agent均分剩余30%
- 适用场景：存在明确的编排Agent（如Orchestrator）
- 优点：编排层有足够上下文管理能力

### 4. 动态调整策略（Dynamic Adjustment）
- 基于实时消耗率动态调整：`adjustment = (consumed_rate - expected_rate) × factor`
- 每5分钟重新评估一次
- 适用场景：任务复杂度不确定、Agent消耗差异大
- 优点：自适应资源分配

## 上下文隔离规则

### 1. 会话上下文隔离
- 每个Agent拥有独立的会话上下文空间
- 禁止跨Agent读取其他Agent的会话历史
- 共享信息通过Orchestrator中转

### 2. 文件访问隔离
- Agent仅可写入分配的工作目录
- 读取范围：项目源码（只读）+ 分配的工作目录（读写）
- 冲突文件通过文件锁机制协调

### 3. 知识库读取隔离
- 所有Agent可读取知识库（只读）
- 写入操作通过知识库服务API，自动去重和版本管理
- 并发写入同一条目时使用乐观锁

### 4. Spec引用隔离
- 每个Agent仅引用当前Phase相关的Spec文档
- 跨Phase引用需通过Orchestrator授权
- Spec变更通知通过事件总线广播

### 5. 环境变量隔离
- Agent间不共享环境变量
- 敏感信息（API Key等）通过Orchestrator按需注入
- 环境变量命名规范：`AGENT_<ROLE>_<VAR_NAME>`

## 知识库写入乐观锁

### 机制
- 每个知识条目包含`version`字段，每次写入递增
- 写入时检查：`WHERE id = ? AND version = ?`
- 冲突处理：版本不匹配时返回409 Conflict，Agent需重新读取后合并

### 冲突解决规则

1. **最后写入胜出**（Last Write Wins）：低优先级条目（如注释更新）
2. **字段级合并**（Field-Level Merge）：不同字段修改可自动合并
3. **人工裁决**（Manual Arbitration）：核心Spec文档冲突，升级至Orchestrator
4. **版本分支**（Version Branch）：并行开发场景，创建分支版本
5. **自动去重**（Auto Dedup）：余弦相似度>0.85的条目自动合并，保留更高置信度版本
