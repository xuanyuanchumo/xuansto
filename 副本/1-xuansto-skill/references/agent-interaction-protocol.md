# Agent 交互协议 (A2A/v1.1)

## 1. A2A 消息格式

### 消息信封结构

```json
{
  "sender": "code-reviewer",
  "recipient": "bug-scanner",
  "message_type": "TASK_ASSIGN",
  "payload": { },
  "timestamp": "2026-05-07T10:00:00Z",
  "correlation_id": "corr-abc123"
}
```

### 消息类型

| 类型 | 用途 | 方向 |
|------|------|------|
| `TASK_ASSIGN` | 分配任务 | Orchestrator → Sub-agent |
| `TASK_RESULT` | 返回结果 | Sub-agent → Orchestrator |
| `QUERY` | 直接查询 | Agent ↔ Agent |
| `RESPONSE` | 查询响应 | Agent ↔ Agent |
| `BROADCAST` | 广播通知 | Agent → 多个 Agent |
| `ERROR` | 错误上报 | 任意 → Runtime Supervisor |
| `HEARTBEAT` | 心跳检测 | Agent → Runtime Supervisor |

### 示例消息

**TASK_ASSIGN**
```json
{ "sender": "orchestrator", "recipient": "compliance-reviewer",
  "message_type": "TASK_ASSIGN", "correlation_id": "t-001",
  "payload": { "task": "review_compliance", "scope": "src/auth/", "phase": 6 } }
```

**TASK_RESULT**
```json
{ "sender": "compliance-reviewer", "recipient": "code-reviewer",
  "message_type": "TASK_RESULT", "correlation_id": "t-001",
  "payload": { "status": "pass", "issues": [], "confidence": 0.95 } }
```

**QUERY / RESPONSE**
```json
{ "sender": "bug-scanner", "recipient": "history-analyzer",
  "message_type": "QUERY", "correlation_id": "q-042",
  "payload": { "question": "recent_fixes_for", "file": "src/auth/login.ts" } }
```

**BROADCAST**
```json
{ "sender": "quality-gate", "recipient": "*",
  "message_type": "BROADCAST", "correlation_id": "b-007",
  "payload": { "event": "gate_failed", "phase": 6, "reason": "security_violation" } }
```

**ERROR**
```json
{ "sender": "penetration-tester", "recipient": "runtime-supervisor",
  "message_type": "ERROR", "correlation_id": "e-103",
  "payload": { "code": "TIMEOUT", "detail": "scan_exceeded_30s" } }
```

**HEARTBEAT**
```json
{ "sender": "code-reviewer", "recipient": "runtime-supervisor",
  "message_type": "HEARTBEAT", "correlation_id": "h-557",
  "payload": { "status": "alive", "active_tasks": 2 } }
```

---

## 2. Agent 间通信协议

### 同步 vs 异步

| 模式 | 适用场景 | 阻塞 |
|------|----------|------|
| 同步 | QUERY/RESPONSE、快速确认 | 是 |
| 异步 | TASK_ASSIGN/TASK_RESULT、长耗时任务 | 否 |

### 请求-响应模式

Agent A → `QUERY` → Agent B → 处理 → `RESPONSE` → Agent A

适用于直接查询，如 Bug Scanner 向 History Analyzer 查询修复历史。

### 发布-订阅模式

发布者 → `BROADCAST` → 所有订阅者

适用于质量门禁失败、阶段切换等全局通知。订阅者按 `payload.event` 过滤。

### 流水线模式

Phase N agents → 质量门禁 → Phase N+1 agents

顺序执行，前一阶段全部 `TASK_RESULT` 为 `pass` 后才进入下一阶段。

---

## 3. 子 Agent 调度协议

### 调度流程

Orchestrator 通过 `TASK_ASSIGN` 派发任务，子 Agent 遵循以下生命周期：

```
DISPATCH → EXECUTE → REPORT → COMPLETE
```

- **DISPATCH**: Orchestrator 分配任务，设置 correlation_id
- **EXECUTE**: 子 Agent 执行任务，可发送 QUERY 获取辅助信息
- **REPORT**: 子 Agent 返回 TASK_RESULT
- **COMPLETE**: Orchestrator 确认结果，释放 Agent 资源

### 并行调度规则

| 约束 | 限制 |
|------|------|
| 单任务最大并发 Agent | 3 |
| 系统全局最大并发 Agent | 10 |

超出限制时进入 FIFO 等待队列。

### 结果聚合（Review-Aggregator 模式）

Code Reviewer 的 5 个子 Agent 并行执行后，结果汇聚至聚合器：

```
5 × TASK_RESULT → review-aggregator → 合并去重 → 置信度评分 → 单一 TASK_RESULT
```

聚合规则：issue 去重（按 file+line+type）、置信度取加权均值。

---

## 4. Agent 协调模式

### 代码审查模式

```
Code Reviewer
  ├── Compliance Reviewer  ──┐
  ├── Bug Scanner           ──┤
  ├── History Analyzer      ──┼→ review-aggregator → confidence_score
  ├── Comment Verifier      ──┤
  └── Specification Keeper  ──┘
```

5 个子 Agent 并行审查 → 聚合 → 输出统一置信度评分（0-1）。

### 安全审计模式

```
Security Auditor → Penetration Tester → Compliance Officer
  → AI Penetration Tester → Bug Scanner → QA Engineer
```

串行流水线，每步结果作为下一步输入，任一环节失败即终止并上报。

### 阶段转换模式

```
当前阶段 Agents → 全部 TASK_RESULT(pass)
  → Quality Gate 检查 → pass → 下一阶段 Agents
                       → fail → BROADCAST(gate_failed) → 修复循环
```

---

## 5. 错误处理

### 故障检测

Runtime Supervisor 通过心跳监控所有 Agent：
- 心跳间隔：**10s**
- 超时阈值：**30s**（3 次未响应判定为故障）

### 故障转移

故障 Agent 的未完成任务转移至 **Specification Keeper**：
- 采用 FIFO 串行队列
- 保证任务不丢失、顺序不变

### 三击协议（Three-Strike）

```
第1次失败 → 重试
第2次失败 → 重试 + 日志告警
第3次失败 → 停止该 Agent → 反模式分析 → 修复后重启
```

连续 3 次失败触发反模式分析，定位根因后重新初始化 Agent。

---

## 6. 通信约束

| 约束项 | 规范 |
|--------|------|
| 协议版本 | A2A/v1.1 |
| 工具调用兼容 | MCP 协议 |
| 敏感数据 | 传输加密（AES-256） |
| 默认超时 | 30s |
| Token 预算 | 消息 payload 含 token_budget 字段，Agent 据此裁剪输出 |
| 消息大小 | 单条消息 ≤ 64KB |
| correlation_id | 全局唯一，格式：`{type}-{alphanum}` |
