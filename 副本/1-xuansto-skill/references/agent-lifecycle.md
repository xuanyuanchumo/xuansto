# Agent生命周期管理

## 1. Agent状态模型

Agent在生命周期中经历以下5种核心状态和1种降级状态：

| 状态 | 标识 | 说明 |
|------|------|------|
| 未激活 | Inactive | Agent定义已加载但未初始化，仅存在定义信息，无工作记忆 |
| 就绪 | Ready | Agent已初始化工作记忆，等待任务分配，已注册到可用Agent池 |
| 活跃 | Active | Agent正在执行任务，占用Token预算和计算资源 |
| 空闲 | Idle | Agent任务完成，等待新任务，保持工作记忆但不占用执行资源 |
| 已销毁 | Destroyed | Agent已销毁，释放所有资源（工作记忆、上下文、注册信息） |
| 降级 | Degraded | Agent因资源不足降级运行，仅保留核心功能，非核心能力暂停 |

### 状态转换图

```
                    ┌─────────────┐
                    │  Inactive   │
                    └──────┬──────┘
                           │ 实例化
                           ▼
                    ┌─────────────┐
              ┌────▶│    Ready    │◀────┐
              │     └──────┬──────┘     │
              │            │ 任务分配    │ 任务完成/释放工作记忆
              │            ▼            │
              │     ┌─────────────┐     │
              │     │   Active    │─────┘
              │     └──────┬──────┘
              │            │ 任务完成（保持工作记忆）
              │            ▼
              │     ┌─────────────┐
              │     │    Idle     │─────┘
              │     └──────┬──────┘     │
              │            │            │
              │  超时30min │ 新任务分配  │ 资源不足
              │            ▼            │
              │     ┌─────────────┐     │
              └─────│    Ready    │     │
                    └──────┬──────┘     │
                           │            │
              ┌────────────┤            │
              │            │            ▼
              │            │     ┌─────────────┐
              │            │     │  Degraded   │
              │            │     └──────┬──────┘
              │            │            │ 连续3次健康检查通过
              │            │            ▼
              │            │     ┌─────────────┐
              │            └────▶│    Ready    │
              │                  └──────┬──────┘
              │                         │
              │  显式销毁                │ 显式销毁
              ▼                         ▼
       ┌─────────────┐          ┌─────────────┐
       │  Destroyed  │          │  Destroyed  │
       └─────────────┘          └─────────────┘
```

### 合法状态转换矩阵

| 从\到 | Inactive | Ready | Active | Idle | Destroyed | Degraded |
|-------|----------|-------|--------|------|-----------|----------|
| Inactive | - | ✓ | ✗ | ✗ | ✓ | ✗ |
| Ready | ✗ | - | ✓ | ✗ | ✓ | ✗ |
| Active | ✗ | ✓ | - | ✓ | ✓ | ✓ |
| Idle | ✗ | ✓ | ✓ | - | ✓ | ✗ |
| Destroyed | ✗ | ✗ | ✗ | ✗ | - | ✗ |
| Degraded | ✗ | ✓ | ✗ | ✗ | ✓ | - |

## 2. Agent实例化流程

Agent实例化遵循4步流程，确保每个Agent在进入就绪状态前完成所有必要的初始化工作：

### 步骤1：加载定义

从 `agents/` 目录读取Agent定义文件，解析以下核心信息：

- **Identity**：Agent唯一标识符、名称、所属层级、协作角色
- **Mission**：Agent的核心使命与职责范围
- **Guidelines**：行为准则、约束条件、质量标准

定义文件结构示例：

```json
{
  "identity": {
    "agent_id": "arch-001",
    "name": "架构设计Agent",
    "layer": 2,
    "role": "architect"
  },
  "mission": "负责系统架构设计与技术选型决策",
  "guidelines": [
    "遵循SDD原则，规格先行",
    "输出必须通过质量门禁",
    "与开发Agent保持契约一致性"
  ]
}
```

### 步骤2：初始化工作记忆

创建Agent的短期记忆缓冲区，加载项目相关上下文：

- 分配短期记忆缓冲区（默认容量：4,000 tokens）
- 加载项目基础配置信息
- 初始化任务执行上下文容器
- 设置Token预算计数器（初始值：50,000）

### 步骤3：注入项目上下文

读取 `.knowledge/` 目录下的项目知识，注入到Agent上下文：

- 加载项目架构文档（`.knowledge/architecture/`）
- 加载编码规范（`.knowledge/standards/`）
- 加载历史决策记录（`.knowledge/decisions/`）
- 加载依赖关系图谱（`.knowledge/dependencies/`）

上下文注入优先级：架构文档 > 编码规范 > 决策记录 > 依赖图谱

### 步骤4：进入就绪

状态转为Ready，注册到Orchestrator的可用Agent池：

- 将Agent状态更新为Ready
- 向Orchestrator发送注册请求
- **注册A2A Agent Card**（见第7节）
- 记录实例化时间戳到健康指标
- 等待任务分配

## 3. Agent状态持久化

### 存储路径

```
.knowledge/agent-states/
├── arch-001.json
├── dev-001.json
├── test-001.json
└── ...
```

### 文件格式

```json
{
  "agent_id": "arch-001",
  "state": "Active",
  "last_active": "2026-05-02T14:30:00Z",
  "task_history": [
    {
      "task_id": "task-20260502-001",
      "started_at": "2026-05-02T14:00:00Z",
      "completed_at": "2026-05-02T14:25:00Z",
      "status": "completed",
      "quality_score": 0.92
    }
  ],
  "memory_snapshot": {
    "short_term": "...",
    "context_keys": ["architecture", "tech-stack"],
    "buffer_usage": 2800
  },
  "health_metrics": {
    "avg_response_latency_ms": 1200,
    "token_consumption_rate": 3200,
    "quality_score": 0.92,
    "error_rate": 0.02,
    "last_health_check": "2026-05-02T14:30:00Z"
  }
}
```

### 恢复流程

系统启动时执行以下恢复流程：

1. **扫描目录**：遍历 `.knowledge/agent-states/` 目录，读取所有Agent状态文件
2. **按优先级恢复**：按以下优先级恢复Agent
   - 优先级1：Active状态Agent（正在执行任务的Agent）
   - 优先级2：Idle状态Agent（保持工作记忆的Agent）
   - 优先级3：Ready状态Agent（等待任务分配的Agent）
   - 优先级4：Degraded状态Agent（降级运行的Agent）
3. **验证上下文完整性**：检查每个Agent的工作记忆和项目上下文是否完整
   - 验证短期记忆缓冲区数据完整性
   - 验证项目上下文引用有效性
   - 验证任务历史记录一致性
4. **标记不完整Agent**：上下文不完整的Agent标记为Degraded状态
   - 记录缺失的上下文项
   - 触发上下文重建流程
   - 降级运行直到上下文恢复完整

## 4. Agent健康监控

### 监控指标

#### 4.1 响应延迟

Agent从接收任务到开始执行的时间。

| 级别 | 阈值 | 说明 |
|------|------|------|
| 正常 | < 30s | Agent响应迅速，资源充足 |
| 警告 | 30s - 60s | Agent响应偏慢，可能存在资源竞争 |
| 异常 | > 60s | Agent响应严重延迟，需要排查原因 |

#### 4.2 Token消耗率

每分钟Token消耗量。

| 级别 | 阈值 | 说明 |
|------|------|------|
| 正常 | < 5,000/min | Token使用效率合理 |
| 警告 | 5,000 - 10,000/min | Token消耗偏高，可能存在冗余输出 |
| 异常 | > 10,000/min | Token消耗过高，需要优化或中断 |

#### 4.3 输出质量分数

基于质量门禁通过率的0-1评分。

| 级别 | 阈值 | 说明 |
|------|------|------|
| 正常 | > 0.8 | 输出质量优秀，稳定通过质量门禁 |
| 警告 | 0.6 - 0.8 | 输出质量下降，需要关注 |
| 异常 | < 0.6 | 输出质量不达标，需要干预 |

#### 4.4 错误率

任务执行失败比例。

| 级别 | 阈值 | 说明 |
|------|------|------|
| 正常 | < 5% | 错误率在可接受范围内 |
| 警告 | 5% - 15% | 错误率偏高，需要分析失败原因 |
| 异常 | > 15% | 错误率过高，Agent可能需要重置或升级 |

### 健康检查机制

- **检查间隔**：Active任务执行期间每5分钟执行一次健康检查
- **检查流程**：
  1. 采集4项监控指标当前值
  2. 对照阈值表判定各项指标级别
  3. 综合评估Agent健康状态
  4. 触发相应处理策略

### 健康状态综合判定规则

| 综合状态 | 判定条件 |
|----------|----------|
| 健康 | 全部指标正常 |
| 亚健康 | 1-2项指标警告，无异常 |
| 不健康 | 任意1项指标异常，或3项以上警告 |
| 危险 | 2项以上指标异常 |

### 处理策略

| 健康状态 | 处理策略 |
|----------|----------|
| 健康 | 继续正常运行 |
| 亚健康 | 记录日志，降低任务分配优先级 |
| 不健康 | 暂停新任务分配，触发自检流程 |
| 危险 | 立即暂停Agent，转为Degraded状态，启动诊断 |

## 5. Agent版本升级策略

### 步骤1：定义对比

比较新旧Agent定义文件差异，识别行为变更：

- 对比Identity字段变更（agent_id不变，名称/层级/角色可能变更）
- 对比Mission声明变更（职责范围扩大或缩小）
- 对比Guidelines规则变更（新增约束、修改行为准则）
- 生成差异报告，标注影响范围

### 步骤2：迁移说明

生成状态迁移指南，覆盖以下内容：

- **工作记忆格式变更**：新版本是否改变了工作记忆的数据结构
- **新增必填字段**：新版本是否要求提供额外的上下文信息
- **废弃字段处理**：旧版本中存在但新版本已移除的字段
- **向后兼容性**：旧版本状态数据是否可直接迁移到新版本

迁移指南示例：

```json
{
  "from_version": "1.2.0",
  "to_version": "1.3.0",
  "breaking_changes": [
    {
      "field": "memory_snapshot.short_term",
      "change": "格式从纯文本变更为结构化JSON",
      "migration": "自动解析旧格式并转换"
    }
  ],
  "new_required_fields": [
    {
      "field": "health_metrics.token_consumption_rate",
      "default": 0
    }
  ],
  "deprecated_fields": [
    {
      "field": "legacy_context",
      "action": "移除，数据已迁移至memory_snapshot"
    }
  ],
  "backward_compatible": true
}
```

### 步骤3：进行中任务标记

处理当前正在执行的任务：

- 扫描所有Active状态的Agent
- 标记当前Active任务
- 等待任务完成或到达安全中断点
- 安全中断点定义：
  - 当前子任务执行完成
  - 数据已持久化
  - 无部分写入状态

### 步骤4：渐进式升级

按优先级逐个升级Agent，确保系统稳定性：

1. 按层级从低到高排序待升级Agent（Layer 0 → Layer 10）
2. 每次仅升级1个Agent
3. 升级后执行健康检查，验证以下指标：
   - 响应延迟恢复正常
   - Token消耗率恢复正常
   - 输出质量分数 > 0.8
   - 错误率 < 5%
4. 健康检查通过后继续升级下一个Agent
5. 健康检查未通过则回滚该Agent到旧版本

## 6. Agent资源限制

### 资源配额

| 资源项 | 限制值 | 说明 |
|--------|--------|------|
| 单Agent最大Token预算 | 50,000 tokens/task | 每个Agent每个任务的最大Token消耗量 |
| 最大并发Active Agent数 | 5 | 同时处于Active状态的Agent数量上限 |
| Idle状态保持时间 | 30分钟 | 超时自动转为Ready，释放工作记忆 |
| Degraded状态恢复条件 | 连续3次健康检查通过 | 每次检查间隔5分钟，需连续通过 |

### 资源限制执行规则

#### Token预算管理

- Agent接收任务时分配Token预算
- 执行过程中实时监控Token消耗
- Token消耗达到80%时发出警告
- Token消耗达到100%时强制结束任务，标记为Token超限

#### 并发控制

- 新任务分配前检查当前Active Agent数量
- 达到上限时新任务进入等待队列
- 等待队列按任务优先级排序
- Active Agent完成任务后自动从队列中分配下一个任务

#### Idle超时处理

- Agent进入Idle状态时启动30分钟倒计时
- 倒计时结束前收到新任务则重置计时器
- 倒计时结束后：
  1. 保存工作记忆快照到持久化存储
  2. 释放短期记忆缓冲区
  3. 状态转为Ready
  4. 通知Orchestrator更新Agent池状态

#### Degraded恢复流程

- Degraded状态Agent每5分钟执行一次健康检查
- 检查4项健康指标是否全部达到正常级别
- 连续3次检查全部通过后：
  1. 恢复完整功能
  2. 重新加载工作记忆
  3. 状态转为Ready
  4. 通知Orchestrator更新Agent池状态
- 任意一次检查未通过则重新计数

## 7. A2A协议Agent Card注册

### 概述

当Agent从Inactive状态转换到Ready状态时，必须注册A2A Agent Card。Agent Card遵循Google A2A Protocol v0.3.0标准格式（详见 [a2a-protocol.md](a2a-protocol.md)），使跨框架Agent能够通过Agent Card发现和调用本系统Agent的能力。

### Agent Card注册时机

Agent Card注册发生在以下状态转换中：

| 状态转换 | 是否注册Agent Card | 说明 |
|----------|-------------------|------|
| Inactive → Ready | ✅ 首次注册 | Agent实例化完成，注册Agent Card到发现服务 |
| Active → Ready | ✅ 更新注册 | 任务完成后更新Agent Card中的可用状态和技能标签 |
| Idle → Ready | ✅ 更新注册 | 超时回归时更新Agent Card中的状态信息 |
| Degraded → Ready | ✅ 更新注册 | 恢复后更新Agent Card，标记全部能力可用 |
| Ready → Destroyed | ❌ 注销 | 销毁时从发现服务移除Agent Card |
| Active → Degraded | ✅ 更新注册 | 降级时更新Agent Card，标记仅核心能力可用 |

### Agent Card标准格式

Agent Card遵循A2A协议标准格式，包含以下核心字段：

```json
{
  "schemaVersion": "0.3.0",
  "name": "架构设计Agent",
  "description": "负责系统架构设计与技术选型决策，支持SDD驱动和契约设计",
  "url": "https://xuansto-agent.local/a2a/arch-001",
  "preferredTransport": "jsonrpc",
  "provider": {
    "organization": "Xuansto Skill",
    "url": "https://xuansto.example.com"
  },
  "version": "3.0.0",
  "capabilities": {
    "streaming": true,
    "pushNotifications": true,
    "stateTransitionHistory": false
  },
  "securitySchemes": {
    "bearer": {
      "type": "http",
      "scheme": "bearer",
      "bearerFormat": "JWT"
    }
  },
  "security": [
    { "bearer": [] }
  ],
  "defaultInputModes": ["text", "data"],
  "defaultOutputModes": ["text", "data", "file"],
  "skills": [
    {
      "id": "architecture-design",
      "name": "架构设计",
      "description": "系统架构设计与技术选型，输出ADR和架构文档",
      "tags": ["architecture", "design", "sdd"],
      "examples": ["设计微服务架构", "技术选型决策"]
    }
  ]
}
```

### Agent Card字段映射

Agent Card中的字段从Agent定义文件和运行时状态中提取：

| Agent Card字段 | 数据来源 | 映射规则 |
|---------------|---------|---------|
| name | identity.name | Agent定义中的名称 |
| description | mission | Agent定义中的核心使命描述 |
| url | 运行时配置 | Agent的A2A服务端点，格式：`{base_url}/a2a/{agent_id}` |
| capabilities | 运行时状态 | 根据Agent当前状态和配置确定streaming/pushNotifications等能力 |
| skills | guidelines + identity.role | 从Agent行为准则和角色中提取技能列表 |
| securitySchemes | 系统配置 | 从A2A安全层配置中获取认证方案 |
| defaultInputModes | 固定值 | 默认 `["text", "data"]` |
| defaultOutputModes | 固定值 | 默认 `["text", "data", "file"]` |

### Agent Card注册流程

```
Agent实例化完成
       │
       ▼
构建Agent Card ──── 从Agent定义和运行时配置提取字段
       │
       ▼
验证Agent Card ──── 校验必填字段（name, description, url, skills）
       │              校验skills非空
       │              校验url格式合法
       ▼
注册到发现服务 ──── POST /register 发送Agent Card
       │              设置TTL（默认3600秒）
       │              获取注册确认
       ▼
启动心跳保活 ────── 每30秒发送心跳维持注册状态
                      连续3次心跳丢失则标记为离线
```

### Degraded状态下的Agent Card

当Agent进入Degraded状态时，Agent Card需要更新以反映降级后的能力：

- 仅保留核心skills（与Degraded状态保留的核心功能一致）
- `capabilities.streaming` 设为 `false`（降级模式下不支持流式传输）
- `capabilities.pushNotifications` 设为 `false`
- skills中移除非核心技能，仅保留与核心功能对应的技能项

### 跨框架Agent发现与调用

注册Agent Card后，跨框架Agent可通过以下方式发现和调用本系统Agent：

1. **Well-Known URI发现**：外部Agent通过 `GET /.well-known/agent.json` 获取Agent Card
2. **注册中心查询**：通过A2A注册中心按能力查询匹配的Agent
3. **能力匹配调用**：外部Agent根据Agent Card中的skills匹配需求，通过 `message/send` 发起任务

Agent Card确保了Xuansto Skill中的Agent能够被其他框架（如Microsoft Agent Framework、LangGraph等）发现和调用，实现真正的跨框架互操作。

### Agent Card注销

Agent销毁（状态转为Destroyed）时，必须执行Agent Card注销：

1. 向发现服务发送注销请求 `DELETE /agents/{agent_id}`
2. 清除本地Agent Card缓存
3. 通知已连接的跨框架Agent该Agent已下线

## 8. 故障转移与恢复规范

### 概述

当Orchestrator发生故障时，系统通过Runtime Supervisor、Specification Keeper和Orchestrator三者的协同，实现故障检测→降级接管→恢复自检的完整闭环，确保工作流不中断且状态一致。

### 完整故障转移与恢复流程

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Orchestrator故障转移与恢复流程                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ① Runtime Supervisor检测故障                                       │
│     │  每10秒心跳探测，连续3次超时（30秒）判定Orchestrator故障        │
│     │  生成故障事件（时间戳、超时次数、最后心跳时间）                  │
│     ▼                                                               │
│  ② Specification Keeper接管（降级模式）                              │
│     │  接收 FAILOVER_NOTIFY 消息                                     │
│     │  启动FIFO串行队列调度（不支持并行编排和动态角色剪枝）           │
│     │  仅激活核心Agent（工程+测试+安全层），非核心Agent停用待命       │
│     │  从 .knowledge/workflow-checkpoints/ 加载工作流状态            │
│     ▼                                                               │
│  ③ Orchestrator重启                                                 │
│     │  Runtime Supervisor检测到Orchestrator心跳恢复                  │
│     │  通知Specification Keeper准备交还调度权                         │
│     ▼                                                               │
│  ④ 加载检查点                                                       │
│     │  从 .knowledge/workflow-checkpoints/ 加载最近检查点快照        │
│     │  恢复工作流上下文（Phase、任务列表、Agent分配、Token预算）      │
│     ▼                                                               │
│  ⑤ 同步Runtime Supervisor记录                                       │
│     │  请求故障期间的Agent调用记录                                    │
│     │  对比检查点与实际执行情况，识别遗漏任务和过期任务                │
│     ▼                                                               │
│  ⑥ 去重检查                                                         │
│     │  比较检查点记录与实际输出，按去重规则处理冲突                    │
│     │  生成去重报告，记录所有冲突决策和依据                            │
│     ▼                                                               │
│  ⑦ 自检                                                             │
│     │  验证所有活跃Agent状态与检查点一致                              │
│     │  确认工作流上下文完整性（Phase进度、依赖图、契约无断裂）        │
│     │  检查Token预算余额，不足则触发性能降级                          │
│     ▼                                                               │
│  ⑧ 恢复正常调度                                                     │
│        自检通过 → 发送 RECOVERY_COMPLETE → Specification Keeper交还  │
│        串行队列任务全部完成 → 恢复并行调度和动态角色剪枝              │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 各阶段详细规范

#### 阶段①：Runtime Supervisor故障检测

| 参数 | 值 | 说明 |
|------|-----|------|
| 心跳探测间隔 | 10秒 | Runtime Supervisor每10秒向Orchestrator发送心跳 |
| 超时判定 | 连续3次 | 连续3次心跳无响应判定故障 |
| 总超时时间 | 30秒 | 从首次超时到故障判定的最长时间 |
| 通知方式 | FAILOVER_NOTIFY | 向Specification Keeper发送故障转移通知消息 |
| 故障事件内容 | 时间戳+超时次数+最后心跳时间 | 用于Specification Keeper决策和Orchestrator恢复时参考 |

#### 阶段②：Specification Keeper降级接管

| 能力 | 降级模式行为 | 正常模式行为 |
|------|-------------|-------------|
| 调度模式 | FIFO串行队列 | 并行编排+动态角色剪枝 |
| Agent范围 | 仅核心Agent（工程+测试+安全层） | 全部Agent按需激活 |
| 工作流状态 | 从检查点加载只读视图 | 实时更新 |
| 跨分支同步 | 高置信度(>0.8)条目自动广播 | 完整知识同步 |

#### 阶段③-⑥：Orchestrator恢复流程

详见 [orchestrator.md](../../agents/orchestrator/orchestrator.md) 的 Checkpoint Recovery Flow 章节。

#### 阶段⑦：自检清单

| 自检项 | 通过条件 | 失败处理 |
|--------|---------|---------|
| 活跃Agent状态 | 所有Agent运行时状态与检查点一致 | 不一致的Agent标记为Degraded，触发上下文重建 |
| 工作流上下文完整性 | Phase进度、任务依赖图、契约定义无断裂引用 | 记录断裂点，从检查点重建受影响部分 |
| Token预算余额 | 剩余预算 > 0 | 触发性能降级策略（L1→L2→L3） |

#### 阶段⑧：交还调度权条件

Specification Keeper交还调度权必须同时满足以下条件：

1. Orchestrator心跳已恢复（Runtime Supervisor确认）
2. Orchestrator状态同步完成（检查点加载+记录同步）
3. 去重检查通过（无未解决的冲突）
4. 自检全部通过（Agent状态+上下文完整性+Token预算）
5. 串行队列中所有任务已完成（避免任务丢失）

### 故障恢复时间目标

| 指标 | 目标值 | 说明 |
|------|--------|------|
| 故障检测延迟 | < 30秒 | 心跳3次超时判定 |
| 降级接管延迟 | < 10秒 | Specification Keeper收到通知到开始调度 |
| 检查点恢复时间 | < 60秒 | 加载+同步+去重+自检 |
| 端到端恢复时间(MTTR) | < 5分钟 | 从故障发生到恢复正常调度 |
