---
name: /agent-status
aliases:
  - ags
  - as
category: system
phase: "cross-phase"
description: Agent状态监控与查询
trigger: 需要查看Agent运行状态时
execution_mode: inline
---

# /agent-status 命令

## 命令描述

`/agent-status` 命令用于查看和管理多Agent系统的运行状态。该命令提供Agent健康检查、任务负载、资源使用、协作状态等全面的状态信息，帮助监控和诊断Agent系统的运行情况。

---

## 触发条件

| 触发方式 | 说明 |
|----------|------|
| 命令输入 | 用户输入 `/agent-status` |
| 关键词触发 | 用户提及"Agent状态"、"状态监控"、"系统状态" |
| 自动触发 | 冲刺执行过程中定期自动检查Agent状态 |
| 条件触发 | Agent异常或超时时自动触发状态检查 |

---

## 命令名称与语法

```
/agent-status [agent-id] [options]
```

---

## 参数定义

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| agent-id | string | 否 | all | 指定Agent ID，默认查看所有 |
| --detail | boolean | 否 | false | 显示详细信息 |
| --tasks | boolean | 否 | false | 显示任务队列详情 |
| --health | boolean | 否 | true | 执行健康检查 |
| --metrics | boolean | 否 | false | 显示性能指标 |
| --history | boolean | 否 | false | 显示历史执行记录 |
| --format | string | 否 | table | 输出格式：table、json、yaml |
| --watch | boolean | 否 | false | 持续监控模式 |
| --interval | number | 否 | 5 | 监控刷新间隔（秒） |

---

## 执行流程

> 标准四步框架：1. 输入验证 → 2. Agent调度 → 3. 任务执行 → 4. 结果验证

```
┌─────────────────────────────────────────────────────────────┐
│                 /agent-status 执行流程                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. 参数解析阶段                                             │
│     ├── 解析命令参数                                         │
│     ├── 确定查询范围                                         │
│     ├── 验证Agent ID有效性                                   │
│     └── 设置输出格式                                         │
│                                                             │
│  2. Agent发现阶段                                            │
│     ├── 扫描已注册Agent                                      │
│     ├── 获取Agent元数据                                      │
│     ├── 确定Agent类型和角色                                   │
│     └── 构建Agent列表                                        │
│                                                             │
│  3. 状态收集阶段                                             │
│     ├── 查询Agent运行状态                                     │
│     ├── 收集任务队列信息                                      │
│     ├── 获取资源使用数据                                      │
│     ├── 检查连接状态                                         │
│     └── 收集错误和警告                                       │
│                                                             │
│  4. 健康检查阶段                                             │
│     ├── 发送健康检查请求                                      │
│     ├── 验证响应时间                                         │
│     ├── 检查依赖服务                                         │
│     ├── 评估健康分数                                         │
│     └── 标记异常Agent                                        │
│                                                             │
│  5. 指标聚合阶段                                             │
│     ├── 计算总体统计                                         │
│     ├── 聚合性能指标                                         │
│     ├── 分析负载分布                                         │
│     └── 生成趋势数据                                         │
│                                                             │
│  6. 报告生成阶段                                             │
│     ├── 格式化状态信息                                       │
│     ├── 生成可视化图表                                       │
│     ├── 标注问题和建议                                       │
│     └── 输出结果                                             │
│                                                             │
│  7. 监控模式（可选）                                          │
│     ├── 持续收集状态                                         │
│     ├── 检测状态变化                                         │
│     ├── 触发告警（如需要）                                    │
│     └── 刷新显示                                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 涉及Agent

| Agent | 角色 | 职责 |
|-------|------|------|
| Orchestrator | 主导 | 状态汇总和报告生成 |
| 所有Agent | 辅助 | 响应状态查询和健康检查 |

---

## 输出格式

### 1. 状态概览表

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Agent 状态概览                                    │
├─────────────────────────────────────────────────────────────────────────┤
│ ID              │ 角色          │ 状态   │ 任务数 │ CPU   │ 内存   │ 健康 │
├─────────────────┼───────────────┼────────┼────────┼───────┼────────┼──────┤
│ orchestrator-01 │ Orchestrator  │ 运行中 │ 3      │ 15%   │ 256MB  │ 100% │
│ architect-01    │ Architect     │ 运行中 │ 1      │ 8%    │ 128MB  │ 100% │
│ developer-01    │ Developer     │ 运行中 │ 2      │ 45%   │ 512MB  │ 95%  │
│ developer-02    │ Developer     │ 空闲   │ 0      │ 2%    │ 64MB   │ 100% │
│ tester-01       │ Tester        │ 运行中 │ 1      │ 30%   │ 384MB  │ 100% │
│ reviewer-01     │ Reviewer      │ 空闲   │ 0      │ 1%    │ 32MB   │ 100% │
│ devops-01       │ DevOps        │ 运行中 │ 1      │ 12%   │ 192MB  │ 100% │
│ security-01     │ Security      │ 空闲   │ 0      │ 3%    │ 48MB   │ 100% │
├─────────────────┴───────────────┴────────┴────────┴───────┴────────┴──────┤
│ 总计: 8个Agent │ 运行中: 5 │ 空闲: 3 │ 平均健康: 99.4%                    │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2. 详细状态报告 (agent-status.json)

```json
{
  "timestamp": "2026-04-17T15:30:00Z",
  "summary": {
    "total_agents": 8,
    "running": 5,
    "idle": 3,
    "error": 0,
    "average_health": 99.4
  },
  "agents": [
    {
      "id": "orchestrator-01",
      "role": "Orchestrator",
      "status": "running",
      "health_score": 100,
      "current_tasks": [
        {
          "task_id": "TASK-001",
          "type": "coordination",
          "started_at": "2026-04-17T15:00:00Z",
          "progress": 75
        }
      ],
      "metrics": {
        "cpu_usage": 15,
        "memory_usage": 256,
        "response_time_ms": 45,
        "tasks_completed_today": 12,
        "success_rate": 99.2
      },
      "last_heartbeat": "2026-04-17T15:29:55Z",
      "uptime_seconds": 86400
    },
    {
      "id": "developer-01",
      "role": "Developer",
      "status": "running",
      "health_score": 95,
      "current_tasks": [
        {
          "task_id": "TASK-002",
          "type": "implementation",
          "started_at": "2026-04-17T14:30:00Z",
          "progress": 60
        },
        {
          "task_id": "TASK-003",
          "type": "refactoring",
          "started_at": "2026-04-17T15:00:00Z",
          "progress": 30
        }
      ],
      "metrics": {
        "cpu_usage": 45,
        "memory_usage": 512,
        "response_time_ms": 120,
        "tasks_completed_today": 5,
        "success_rate": 97.5
      },
      "warnings": [
        {
          "type": "high_memory",
          "message": "内存使用接近阈值",
          "threshold": 512,
          "current": 512
        }
      ],
      "last_heartbeat": "2026-04-17T15:29:58Z",
      "uptime_seconds": 72000
    }
  ]
}
```

### 3. 任务队列状态 (task-queue.json)

```json
{
  "queues": {
    "high_priority": {
      "pending": 2,
      "processing": 1,
      "completed_today": 15
    },
    "normal_priority": {
      "pending": 5,
      "processing": 3,
      "completed_today": 42
    },
    "low_priority": {
      "pending": 3,
      "processing": 0,
      "completed_today": 8
    }
  },
  "task_distribution": {
    "orchestrator-01": ["TASK-001"],
    "developer-01": ["TASK-002", "TASK-003"],
    "tester-01": ["TASK-004"],
    "devops-01": ["TASK-005"]
  },
  "blocked_tasks": [],
  "estimated_completion": "2026-04-17T17:00:00Z"
}
```

### 4. 健康检查报告 (health-check.md)

```markdown
# Agent 健康检查报告

## 检查时间
2026-04-17 15:30:00

## 总体状态
✅ 系统健康 - 所有Agent运行正常

## 详细检查结果

### orchestrator-01
- 状态: ✅ 健康
- 响应时间: 45ms (正常)
- 内存: 256MB/1GB (25%)
- 心跳: 正常 (最后: 5秒前)
- 依赖服务: 全部可用

### developer-01
- 状态: ⚠️ 警告
- 响应时间: 120ms (偏高)
- 内存: 512MB/512MB (100%) ⚠️
- 心跳: 正常 (最后: 2秒前)
- 建议: 考虑增加内存限制或优化任务

### 其他Agent
- architect-01: ✅ 健康
- developer-02: ✅ 健康
- tester-01: ✅ 健康
- reviewer-01: ✅ 健康
- devops-01: ✅ 健康
- security-01: ✅ 健康

## 建议操作
1. developer-01 内存使用接近阈值，建议监控
2. 考虑为高负载Agent增加资源
```

---

## 示例用法

### 示例1: 查看所有Agent状态

```bash
/agent-status
```

显示所有Agent的状态概览。

### 示例2: 查看指定Agent详情

```bash
/agent-status developer-01 --detail
```

显示 developer-01 的详细状态信息。

### 示例3: 查看任务队列

```bash
/agent-status --tasks
```

显示所有Agent的任务队列详情。

### 示例4: 查看性能指标

```bash
/agent-status --metrics --format=json
```

以JSON格式输出性能指标。

### 示例5: 持续监控模式

```bash
/agent-status --watch --interval=10
```

每10秒刷新一次状态，持续监控。

### 示例6: 查看历史记录

```bash
/agent-status orchestrator-01 --history
```

查看 orchestrator-01 的历史执行记录。

---

## 状态说明

### Agent状态类型

| 状态 | 说明 | 图标 |
|------|------|------|
| running | 正在执行任务 | 🟢 |
| idle | 空闲，等待任务 | 🔵 |
| busy | 高负载运行中 | 🟡 |
| error | 错误状态 | 🔴 |
| offline | 离线 | ⚫ |
| maintenance | 维护模式 | 🟣 |

### 健康分数说明

| 分数范围 | 状态 | 说明 |
|----------|------|------|
| 90-100 | 优秀 | Agent运行状态极佳 |
| 70-89 | 良好 | Agent运行正常，可优化 |
| 50-69 | 一般 | Agent有轻微问题 |
| 30-49 | 较差 | Agent需要关注 |
| 0-29 | 危险 | Agent需要立即处理 |

---

## 告警规则

```yaml
alerts:
  - name: agent_offline
    condition: agent.status == "offline"
    severity: critical
    action: notify_admin
    
  - name: high_memory_usage
    condition: agent.memory_usage > 90%
    severity: warning
    action: log_and_notify
    
  - name: slow_response
    condition: agent.response_time > 5000ms
    severity: warning
    action: log_and_notify
    
  - name: task_timeout
    condition: task.duration > task.timeout
    severity: error
    action: kill_and_restart
```

---

## 注意事项

1. **权限要求**: 查看状态需要相应的监控权限
2. **性能影响**: 详细查询可能对系统有轻微影响
3. **监控模式**: 持续监控会占用终端会话
4. **历史数据**: 历史记录保留时间取决于配置
5. **敏感信息**: 某些详细信息可能需要额外授权

---

## 质量门禁

| 门禁标识 | 阻塞级别(BLOCK/WARN) | 通过标准 |
|----------|----------------------|----------|
| TOKEN-BUDGET | WARN | Token消耗在预算范围内、无Agent超出Token限制、剩余Token充足 |
---

## 相关脚本

- `scripts/skill-test.py` - 技能测试器，验证Agent技能可用性和执行状态

---

## 相关工作流

- `workflows/sdd-tdd-full.md` (monitoring) - SDD+TDD全生命周期工作流的监控阶段

---

## 相关命令

- `/review` - 审查Agent执行结果
- `/deploy` - 部署时查看Agent状态
- `/learn` - 学习Agent协作模式
