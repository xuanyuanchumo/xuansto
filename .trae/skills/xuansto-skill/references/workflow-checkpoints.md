# 工作流检查点与恢复

## 1. 子任务粒度检查点规范

### 保存时机

- 每个子任务开始前
- 每个子任务完成后
- 关键决策点（架构选型、技术方案变更、依赖升级等）

### 保存内容

```json
{
  "task_id": "string",
  "phase": "number",
  "subtask_index": "number",
  "status": "pending | in_progress | completed | failed | skipped",
  "artifacts": ["string"],
  "decisions": [
    {
      "decision_id": "string",
      "description": "string",
      "rationale": "string",
      "alternatives_considered": ["string"],
      "made_by": "string",
      "timestamp": "ISO8601"
    }
  ],
  "timestamp": "ISO8601",
  "agent_id": "string",
  "parent_task_id": "string | null",
  "retry_count": "number",
  "dependencies": ["string"],
  "quality_gate_results": [
    {
      "gate_id": "string",
      "passed": "boolean",
      "score": "number",
      "details": "string"
    }
  ]
}
```

### 存储路径

```
.knowledge/checkpoints/{task_id}/{phase}_{subtask_index}.json
```

路径示例：

```
.knowledge/checkpoints/TASK-001/phase2_subtask3.json
.knowledge/checkpoints/TASK-001/phase0_subtask1.json
```

### 检查点大小限制

| 条件 | 处理方式 |
|------|----------|
| 单文件 ≤ 100KB | 完整保存所有内容 |
| 单文件 > 100KB | 仅保存引用路径，实际内容存储至 `.knowledge/artifacts/{task_id}/` |

引用路径格式：

```json
{
  "ref_type": "artifact_reference",
  "artifact_path": ".knowledge/artifacts/{task_id}/{filename}",
  "checksum": "sha256:..."
}
```

## 2. 中断标记与恢复续传流程

### 五步恢复流程

#### 步骤一：中断检测

Orchestrator 通过以下方式检测中断：

| 检测方式 | 触发条件 | 超时阈值 |
|----------|----------|----------|
| 心跳超时 | Agent 无响应 | 60秒 |
| 显式中断信号 | 用户发送中断指令 | 即时 |
| 异常捕获 | Agent 执行抛出未处理异常 | 即时 |
| 资源耗尽 | 内存/CPU超出安全阈值 | 持续5秒 |

心跳机制细节：

- Agent 每 15 秒发送一次心跳
- Orchestrator 连续 4 次未收到心跳（60秒）判定为中断
- 心跳内容：`{agent_id, current_subtask, progress_pct, memory_usage, timestamp}`

#### 步骤二：状态快照

立即保存当前所有 Active Agent 的状态快照：

```
.knowledge/checkpoints/{task_id}/interrupt_snapshot_{timestamp}.json
```

快照内容：

```json
{
  "snapshot_id": "string",
  "task_id": "string",
  "timestamp": "ISO8601",
  "active_agents": [
    {
      "agent_id": "string",
      "agent_type": "string",
      "current_phase": "number",
      "current_subtask": "number",
      "status": "string",
      "partial_artifacts": ["string"],
      "context_window_usage": "number",
      "pending_actions": ["string"]
    }
  ],
  "shared_state": {
    "global_variables": {},
    "accumulated_decisions": [],
    "quality_gate_history": []
  }
}
```

#### 步骤三：中断标记

在任务元数据中标记中断点：

```json
{
  "task_id": "string",
  "interrupted_at": "ISO8601",
  "interrupt_reason": "heartbeat_timeout | user_signal | exception | resource_exhaustion",
  "interrupt_phase": "number",
  "interrupt_subtask": "number",
  "recoverable": "boolean",
  "affected_agents": ["string"],
  "data_integrity_verified": "boolean"
}
```

`recoverable` 判定规则：

- 心跳超时 → `true`（可恢复）
- 用户中断信号 → 由用户决定
- 未处理异常 → 根据异常类型判断
- 资源耗尽 → `true`（释放资源后可恢复）

#### 步骤四：恢复准备

1. 重新初始化中断 Agent
2. 加载状态快照
3. 验证上下文完整性

上下文完整性验证清单：

| 验证项 | 验证方式 | 失败处理 |
|--------|----------|----------|
| 文件完整性 | 对比快照中的 checksum | 重新生成或回退 |
| 依赖状态 | 检查上游子任务是否已完成 | 等待或重新执行 |
| Agent 可用性 | 心跳确认 | 重新初始化 |
| 共享状态一致性 | 版本号比对 | 以最新版本为准 |

#### 步骤五：续传执行

从中断点继续执行，跳过已完成的子任务：

```
恢复执行流程：
1. 读取中断标记 → 确定中断位置
2. 扫描检查点 → 确认已完成子任务列表
3. 跳过已完成 → 从中断子任务开始
4. 继承上下文 → 加载中断前的决策和状态
5. 恢复执行 → 正常推进工作流
```

续传时的特殊处理：

- 中断时正在执行的子任务：从头重新执行（不保留部分结果）
- 中断时已完成的子任务：直接跳过
- 中断时排队等待的子任务：正常执行
- 中断时被阻塞的子任务：检查阻塞条件是否仍然存在

## 3. Phase间回退策略

### 四步回退流程

#### 步骤一：创建回退分支

```bash
git switch -c rollback/phase-{N}-{reason}
```

分支命名规范：

| 组成部分 | 说明 | 示例 |
|----------|------|------|
| phase-{N} | 回退目标Phase编号 | phase-2 |
| reason | 回退原因缩写 | arch-change, perf-fail, req-update |

示例：

```bash
git switch -c rollback/phase-2-arch-change
git switch -c rollback/phase-3-perf-fail
```

回退分支创建后自动操作：

- 保留当前分支的所有提交记录
- 在回退分支上标记回退起点：`ROLLBACK_START: phase {N} → phase {M}`
- 通知所有 Active Agent 切换到回退分支

#### 步骤二：标记需修订

在 `.knowledge/checkpoints/` 中标记需要重新执行的子任务：

```json
{
  "rollback_id": "string",
  "target_phase": "number",
  "rollback_reason": "string",
  "subtasks_to_rerun": [
    {
      "subtask_index": "number",
      "rerun_reason": "string",
      "preserve_outputs": "boolean"
    }
  ],
  "subtasks_to_preserve": [
    {
      "subtask_index": "number",
      "preserve_reason": "string"
    }
  ],
  "created_at": "ISO8601"
}
```

标记规则：

- 回退目标 Phase 的所有子任务标记为需重新执行
- 已通过门禁且不受回退影响的子任务标记为保留
- 下游 Phase 中依赖回退 Phase 输出的子任务标记为需重新执行

#### 步骤三：重新执行

从回退 Phase 的开始点重新执行，保留已通过门禁的子任务结果：

```
重新执行策略：
┌─────────────────────────────────────────────┐
│  Phase N（回退目标）                          │
│  ├── Subtask 1 → 重新执行                    │
│  ├── Subtask 2 → 保留（门禁已通过且无依赖）    │
│  ├── Subtask 3 → 重新执行                    │
│  └── Subtask 4 → 重新执行                    │
├─────────────────────────────────────────────┤
│  Phase N+1（下游）                           │
│  ├── Subtask 1 → 重新执行（依赖Phase N输出）  │
│  └── Subtask 2 → 保留（无依赖关系）           │
└─────────────────────────────────────────────┘
```

重新执行时的注意事项：

- 保留的子任务结果不得被覆盖
- 重新执行的子任务可引用保留子任务的输出
- 每个重新执行的子任务完成后立即创建新检查点
- 新检查点覆盖同位置的旧检查点

#### 步骤四：门禁检查

重新执行完成后，必须通过该 Phase 的所有质量门禁：

| 门禁类型 | 检查内容 | 通过标准 |
|----------|----------|----------|
| 代码质量门禁 | Lint、类型检查、复杂度 | 零错误，警告数低于阈值 |
| 测试门禁 | 单元测试、集成测试覆盖率 | 覆盖率 ≥ 80%，全部通过 |
| 安全门禁 | 依赖漏洞、敏感信息泄露 | 零高危漏洞 |
| 架构门禁 | 依赖方向、模块耦合度 | 无循环依赖，耦合度达标 |
| 性能门禁 | 响应时间、内存占用 | 满足非功能性需求指标 |

门禁检查失败处理：

- 单个门禁失败：修复后重新执行该门禁
- 多个门禁失败：评估是否需要进一步回退到更早的 Phase
- 修复超过 3 次仍失败：升级为人工决策点

## 4. 检查点清理策略

### 清理规则

| 任务结果 | 保留策略 | 清理时机 |
|----------|----------|----------|
| 成功完成 | 保留最终检查点7天，删除中间检查点 | 任务完成后7天自动清理 |
| 失败任务 | 保留所有检查点30天供分析 | 任务失败后30天自动清理 |
| 回退任务 | 保留回退前后的检查点直到任务成功完成 | 任务成功后按成功策略处理 |

### 清理优先级

```
1. 临时快照（interrupt_snapshot_*）→ 任务完成后立即清理
2. 中间子任务检查点 → 任务完成后7天清理
3. Phase 级检查点 → 保留至最终检查点过期
4. 最终检查点 → 按上述保留策略执行
5. 回退相关检查点 → 任务成功后按成功策略执行
```

### 清理执行方式

```
清理流程：
1. 扫描 .knowledge/checkpoints/ 目录
2. 读取每个检查点的任务状态和创建时间
3. 根据清理规则判断是否过期
4. 生成清理清单，记录待删除文件
5. 执行删除操作
6. 记录清理日志至 .knowledge/logs/checkpoint_cleanup.log
```

清理日志格式：

```json
{
  "cleanup_id": "string",
  "timestamp": "ISO8601",
  "deleted_files": ["string"],
  "freed_space_kb": "number",
  "task_id": "string",
  "task_status": "success | failed | rolled_back"
}
```

### 磁盘空间保护

- 检查点总占用超过 500MB 时触发紧急清理
- 紧急清理优先删除失败任务的中间检查点
- 紧急清理后保留每个任务至少一个检查点

## 5. 检查点与质量门禁联动

### 联动机制

#### 门禁通过后自动创建检查点

每个质量门禁通过后自动创建检查点，作为回退锚点：

```
门禁通过 → 创建检查点
├── 检查点命名：{phase}_gate_{gate_id}_passed.json
├── 检查点内容：包含门禁结果快照
└── 检查点标记：gate_checkpoint = true
```

门禁检查点内容：

```json
{
  "checkpoint_type": "gate_passed",
  "task_id": "string",
  "phase": "number",
  "gate_id": "string",
  "gate_type": "code_quality | test | security | architecture | performance",
  "gate_result": {
    "passed": true,
    "score": "number",
    "details": "string",
    "checked_artifacts": ["string"],
    "violations": []
  },
  "timestamp": "ISO8601",
  "snapshot": {
    "file_hashes": {},
    "dependency_versions": {},
    "config_state": {}
  }
}
```

#### 门禁失败时自动回退

门禁失败时自动回退到上一个通过门禁的检查点：

```
门禁失败 → 自动回退
1. 定位上一个通过门禁的检查点
2. 验证检查点完整性（checksum比对）
3. 恢复文件状态至检查点时刻
4. 记录回退原因和门禁失败详情
5. 通知 Orchestrator 重新调度
```

回退定位算法：

```
查找上一个通过门禁的检查点：
1. 从当前 Phase 开始向前搜索
2. 查找 gate_checkpoint = true 的检查点
3. 优先查找同类型门禁的检查点
4. 若当前 Phase 无可用检查点，扩展到上一个 Phase
5. 若仍无可用检查点，回退到 Phase 0 的初始检查点
```

#### 检查点包含门禁结果快照

检查点包含门禁结果快照，用于恢复时快速验证：

```json
{
  "gate_result_snapshot": {
    "total_gates_passed": "number",
    "total_gates_failed": "number",
    "gate_history": [
      {
        "gate_id": "string",
        "gate_type": "string",
        "passed": "boolean",
        "timestamp": "ISO8601",
        "artifacts_at_gate": ["string"]
      }
    ],
    "cumulative_score": "number"
  }
}
```

恢复时快速验证流程：

```
1. 加载检查点中的门禁结果快照
2. 比对当前文件状态与快照中的 file_hashes
3. 若文件状态一致 → 跳过门禁重新验证，直接继续
4. 若文件状态不一致 → 重新执行门禁验证
5. 验证结果与快照比对，确认无退化
```

### 联动保障规则

| 规则 | 说明 |
|------|------|
| 检查点先于门禁 | 子任务完成后先创建检查点，再执行门禁验证 |
| 门禁检查点不可覆盖 | 门禁通过创建的检查点标记为只读，不可被后续检查点覆盖 |
| 回退必须经过门禁 | 从检查点恢复后，必须重新通过门禁验证才能继续推进 |
| 门禁结果可追溯 | 所有门禁结果保留完整历史，支持任意时间点的状态还原 |
| 跨Phase门禁联动 | 下游Phase的门禁失败时，可追溯至上游Phase的门禁检查点 |
