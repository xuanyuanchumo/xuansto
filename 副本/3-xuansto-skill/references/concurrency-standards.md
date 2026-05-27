# 并发任务执行规范

<!-- version: 2.0.0 | 编码: UTF-8 -->

> 本文档定义了 Xuansto Skill 多Agent自主开发编排器中并发任务执行的完整规范，
> 涵盖并发度控制、Token预算分配、上下文隔离和知识库写入冲突解决。

---

## 1. 并发度控制

### 1.1 任务级并发

| 参数 | 值 | 说明 |
|------|-----|------|
| `max_concurrent_agents` | 3 | 同一任务内最大并发Agent数 |
| 调度策略 | 优先级加权 | 按Agent优先级分配并发槽位 |
| 抢占机制 | 支持 | 高优先级Agent可抢占低优先级Agent的并发槽位 |

**并发槽位分配规则**：

1. 每个任务最多同时运行3个Agent
2. 优先级排序：Orchestrator > System Architect > Code Implementer > 其他
3. 当3个槽位已满且有更高优先级Agent需要执行时：
   - 最低优先级的运行中Agent被暂停（保存检查点）
   - 高优先级Agent获得槽位并开始执行
   - 被暂停Agent在槽位释放后从检查点恢复

**槽位状态流转**：

```
空闲(IDLE) → 分配中(ALLOCATING) → 运行中(RUNNING) → 释放中(RELEASING) → 空闲(IDLE)
                                    ↓
                              被抢占(PREEMPTED) → 等待恢复(WAITING) → 运行中(RUNNING)
```

### 1.2 系统级并行度

| 参数 | 值 | 说明 |
|------|-----|------|
| `system_parallel_capacity` | 10 | 系统最大并行任务数 |
| 任务调度策略 | FIFO + 优先级 | 先进先出，高优先级任务可插队 |
| 资源隔离 | 任务级 | 每个任务独立资源池，任务间互不影响 |

**系统级并行度分配**：

- 系统总并行容量为10个任务槽位
- 每个任务占用1个系统槽位 + 最多3个Agent并发槽位
- 系统级槽位分配优先级：
  1. 阻塞性任务（BLOCKING_GATE_FAILURE修复）
  2. 高优先级任务（P0/P1）
  3. 标准优先级任务（P2）
  4. 低优先级任务（P3）

**资源争用处理**：

| 场景 | 处理策略 |
|------|----------|
| 系统槽位已满 | 新任务进入等待队列，按优先级排序 |
| Agent并发槽位已满 | 新Agent等待当前Agent完成或被抢占 |
| Token预算不足 | 暂停低优先级Agent，释放Token给高优先级Agent |
| 上下文窗口不足 | 触发上下文压缩或Agent切换 |

### 1.3 并发度配置

```json
{
  "concurrency": {
    "max_concurrent_agents": 3,
    "system_parallel_capacity": 10,
    "preemption_enabled": true,
    "preemption_cooldown_seconds": 30,
    "agent_priority": {
      "orchestrator": 100,
      "system_architect": 90,
      "code_implementer": 70,
      "test_architect": 60,
      "code_reviewer": 50,
      "security_auditor": 50,
      "specification_keeper": 40
    }
  }
}
```

---

## 2. Token预算分配策略

### 2.1 均分策略（Equal Distribution）

- 公式：`budget_per_agent = total_budget / active_agent_count`
- 适用场景：Agent优先级相同、任务复杂度相近
- 优点：简单公平
- 缺点：不考虑Agent实际需求差异

**示例**：总预算120K tokens，3个活跃Agent → 每个Agent 40K tokens

### 2.2 优先级加权策略（Priority-Weighted）

- 公式：`budget_i = total_budget × (priority_i / Σpriority_j)`
- 优先级定义：P0=4, P1=3, P2=2, P3=1
- 适用场景：任务优先级明确、核心Agent需要更多Token
- 优点：关键任务获得更多资源

**示例**：总预算120K tokens，3个Agent（P0+P1+P2）
- P0 Agent: 120K × (4/7) = 68.6K tokens
- P1 Agent: 120K × (3/7) = 51.4K tokens
- P2 Agent: 120K × (2/7) = 34.3K tokens

### 2.3 主从策略（Master-Worker）

- 主Agent获得70%预算，从Agent均分剩余30%
- 适用场景：存在明确的编排Agent（如Orchestrator）
- 优点：编排层有足够上下文管理能力

**示例**：总预算120K tokens，1主+2从
- 主Agent(Orchestrator): 120K × 70% = 84K tokens
- 从Agent A: (120K × 30%) / 2 = 18K tokens
- 从Agent B: (120K × 30%) / 2 = 18K tokens

### 2.4 动态调整策略（Dynamic Adjustment）

- 基于实时消耗率动态调整：`adjustment = (consumed_rate - expected_rate) × factor`
- 每5分钟重新评估一次
- 适用场景：任务复杂度不确定、Agent消耗差异大
- 优点：自适应资源分配

**动态调整规则**：

| 消耗状态 | 调整方向 | 调整幅度 |
|----------|----------|----------|
| 消耗率 > 预期率 × 1.5 | 减少预算 | -10% per cycle |
| 消耗率 > 预期率 × 1.2 | 轻微减少 | -5% per cycle |
| 消耗率在预期率 ± 20% | 保持不变 | 0 |
| 消耗率 < 预期率 × 0.8 | 轻微增加 | +5% per cycle |
| 消耗率 < 预期率 × 0.5 | 增加预算 | +10% per cycle |

**最低保障**：每个Agent最低Token预算不低于总预算的10%，防止Agent因预算不足无法完成基本操作。

### 2.5 策略选择决策树

```
任务类型判定
    │
    ├── 编排型任务(Orchestrator主导) → 主从策略
    │
    ├── 优先级明确的并行任务 → 优先级加权策略
    │
    ├── 复杂度不确定的探索性任务 → 动态调整策略
    │
    └── 同等优先级的常规任务 → 均分策略
```

---

## 3. 上下文隔离规则

### 3.1 会话上下文隔离

- 每个Agent拥有独立的会话上下文空间（per-task context window）
- 禁止跨Agent读取其他Agent的会话历史
- 共享信息通过Orchestrator中转

**上下文窗口分配**：

| Agent角色 | 默认窗口大小 | 最大窗口大小 | 说明 |
|-----------|-------------|-------------|------|
| Orchestrator | 8K tokens | 16K tokens | 需要维护全局上下文 |
| System Architect | 6K tokens | 12K tokens | 需要理解系统架构 |
| Code Implementer | 4K tokens | 8K tokens | 聚焦当前实现任务 |
| Test Architect | 4K tokens | 8K tokens | 聚焦测试设计 |
| Code Reviewer | 4K tokens | 8K tokens | 聚焦代码审查 |
| Security Auditor | 4K tokens | 8K tokens | 聚焦安全审计 |

**上下文压缩策略**：

当Agent上下文接近窗口上限时：
1. 优先保留：当前任务指令、最近3轮交互、关键约束条件
2. 可压缩：历史交互摘要、中间推理过程、已完成的子任务细节
3. 可丢弃：调试信息、重复内容、过期状态

### 3.2 文件访问隔离

- Agent仅可写入分配的工作目录
- 读取范围：项目源码（只读）+ 分配的工作目录（读写）
- 冲突文件通过文件锁机制协调

**文件锁机制**：

| 锁类型 | 适用场景 | 行为 |
|--------|----------|------|
| 共享锁(S锁) | 读取文件 | 多个Agent可同时持有 |
| 排他锁(X锁) | 写入文件 | 仅一个Agent可持有，阻塞其他S/X锁 |
| 意向锁(IS/IX) | 目录级操作 | 表示意图获取下层S/X锁 |

**死锁预防**：
- 所有Agent按固定顺序（文件路径字典序）请求文件锁
- 锁等待超时(默认30秒)，超时后释放已持有的锁并重试
- Orchestrator检测死锁循环，强制释放低优先级Agent的锁

### 3.3 知识库读取隔离

- 所有Agent可读取知识库（只读）
- 写入操作通过知识库服务API，自动去重和版本管理
- 并发写入同一条目时使用乐观锁

**共享知识库架构**：

```
┌─────────────────────────────────────────┐
│              共享知识库                    │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐   │
│  │ Markdown │ │ SQLite  │ │ Chroma  │   │
│  │  知识源  │ │ 结构化  │ │ 向量库  │   │
│  └────┬────┘ └────┬────┘ └────┬────┘   │
│       │           │           │         │
│  ┌────┴───────────┴───────────┴────┐   │
│  │       乐观锁 + 版本管理          │   │
│  └────────────────┬────────────────┘   │
│                   │                     │
└───────────────────┼─────────────────────┘
                    │
        ┌───────────┼───────────┐
        │           │           │
   Agent A      Agent B     Agent C
   (只读+       (只读+       (只读+
    乐观写)      乐观写)      乐观写)
```

### 3.4 Spec引用隔离

- 每个Agent仅引用当前Phase相关的Spec文档
- 跨Phase引用需通过Orchestrator授权
- Spec变更通知通过事件总线广播

**事件总线消息格式**：

```json
{
  "event_type": "SPEC_UPDATED",
  "source_agent": "specification_keeper",
  "spec_id": "user-auth-spec",
  "change_type": "MODIFIED",
  "affected_sections": ["4.2", "4.3"],
  "timestamp": "2026-05-06T14:30:00Z",
  "subscribers": ["code_implementer", "test_architect"]
}
```

### 3.5 环境变量隔离

- Agent间不共享环境变量
- 敏感信息（API Key等）通过Orchestrator按需注入
- 环境变量命名规范：`AGENT_<ROLE>_<VAR_NAME>`

**环境变量注入流程**：

1. Agent启动时向Orchestrator声明所需环境变量
2. Orchestrator验证Agent角色是否有权访问该变量
3. 验证通过后，Orchestrator将环境变量注入Agent的执行环境
4. Agent终止时，注入的环境变量自动清除
5. 环境变量不写入Agent上下文或长期记忆

---

## 4. 知识库写入冲突解决

### 4.1 乐观锁机制

- 每个知识条目包含`version`字段，每次写入递增
- 写入时检查：`WHERE id = ? AND version = ?`
- 冲突处理：版本不匹配时返回409 Conflict，Agent需重新读取后合并

**乐观锁工作流程**：

```
Agent A: 读取条目(version=5) ──────────────────────────
                                                        │
Agent B: 读取条目(version=5) ────────────────────────── │
                                                        │ │
Agent A: 写入条目(version=5→6) ─── 成功 ─────────────── │
                                                        │ │
Agent B: 写入条目(version=5→6) ─── 冲突(当前version=6) │
                    │                                   │
                    ▼                                   │
            冲突解决流程 ─────────────────────────────── │
                    │                                   │
                    ▼                                   │
            重新读取(version=6) → 合并 → 写入(6→7) ─── 成功
```

### 4.2 冲突解决规则

| 规则 | 适用场景 | 冲突解决方式 | 冲突日志 |
|------|----------|-------------|----------|
| 最后写入胜出(Last Write Wins) | 低优先级条目(注释更新、日志记录) | 时间戳较新的版本覆盖较旧版本 | 记录被覆盖版本摘要 |
| 字段级合并(Field-Level Merge) | 不同Agent修改同一条目的不同字段 | 自动合并各字段修改，保留全部变更 | 记录合并字段列表 |
| 人工裁决(Manual Arbitration) | 核心Spec文档冲突 | 升级至Orchestrator，人工选择保留版本 | 记录裁决人和裁决理由 |
| 版本分支(Version Branch) | 并行开发场景 | 创建分支版本，后续合并 | 记录分支关系 |
| 自动去重(Auto Dedup) | 余弦相似度>0.85的条目 | 自动合并，保留更高置信度版本 | 记录去重详情和相似度 |

### 4.3 冲突日志规范

所有写入冲突必须记录到冲突日志，确保冲突可追溯、可审计。

**日志存储路径**：`.knowledge/conflicts/`

**日志格式**：

```json
{
  "conflict_id": "cf-20260506-001",
  "timestamp": "2026-05-06T14:35:00Z",
  "entry_id": "kb-user-auth-design",
  "conflict_type": "VERSION_MISMATCH",
  "resolution_strategy": "FIELD_LEVEL_MERGE",
  "agents_involved": ["code_implementer_a", "code_implementer_b"],
  "base_version": 5,
  "conflicting_versions": [6, 7],
  "resolved_version": 8,
  "merged_fields": ["description", "constraints"],
  "overwritten_fields": [],
  "auto_resolved": true,
  "reviewer": null
}
```

**冲突日志保留策略**：

| 冲突类型 | 保留时长 | 说明 |
|----------|----------|------|
| 自动解决(低优先级) | 30天 | Last Write Wins、Auto Dedup |
| 自动解决(中优先级) | 90天 | Field-Level Merge |
| 人工裁决 | 永久 | Manual Arbitration |
| 版本分支 | 至分支合并 | Version Branch |

### 4.4 冲突预防策略

1. **任务分区**：Orchestrator在分配任务时，尽量将不同Agent的工作范围分配到不同的知识条目
2. **写入预约**：Agent在写入前向Orchestrator预约写入意图，Orchestrator协调写入顺序
3. **批量写入**：Agent将多个相关变更合并为一次写入，减少冲突概率
4. **写入窗口**：为高冲突率的知识条目设置写入窗口，同一时间仅允许一个Agent写入

---

## 5. 并发安全检查清单

### 5.1 任务启动前检查

- [ ] 并发槽位可用（当前活跃Agent < max_concurrent_agents）
- [ ] Token预算充足（剩余预算 > Agent最低需求）
- [ ] 上下文窗口可用（当前上下文 < 最大窗口 × 80%）
- [ ] 工作目录无冲突（无其他Agent写入同一目录）
- [ ] 所需知识条目无写锁（或已预约写入窗口）

### 5.2 运行时监控

- [ ] Agent上下文使用率 < 80%（超过时触发压缩）
- [ ] Token消耗率在预期范围内（偏差 < 20%）
- [ ] 文件锁等待时间 < 30秒（超过时触发死锁检测）
- [ ] 知识库写入冲突率 < 5%（超过时触发分区优化）
- [ ] 系统并行度 < system_parallel_capacity（超过时排队等待）

### 5.3 任务完成时检查

- [ ] 所有文件锁已释放
- [ ] 知识库写入冲突已解决
- [ ] 环境变量已清除
- [ ] 上下文资源已释放
- [ ] 并发槽位已归还

---

## 6. 并发度量指标

| 指标名称 | 计算方式 | 目标值 | 说明 |
|----------|----------|--------|------|
| Agent并发利用率 | 活跃Agent数 / max_concurrent_agents | 60-90% | 衡量并发资源利用效率 |
| 系统并行利用率 | 活跃任务数 / system_parallel_capacity | 50-80% | 衡量系统资源利用效率 |
| Token预算利用率 | 已消耗Token / 分配Token | 70-95% | 衡量Token分配准确性 |
| 知识库写入冲突率 | 冲突次数 / 总写入次数 | ≤ 5% | 衡量分区策略有效性 |
| 上下文压缩频率 | 压缩次数 / Agent运行时长 | ≤ 2次/小时 | 衡量上下文窗口充足性 |
| 抢占频率 | 抢占次数 / 总调度次数 | ≤ 10% | 衡量优先级分配合理性 |
| 死锁检测频率 | 死锁检测次数 / 总运行时长 | 0 | 死锁应完全避免 |
