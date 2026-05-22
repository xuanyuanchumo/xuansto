# 持续演化系统说明文档

> 🧬 **持续演化，自我优化** - 通过智能监控和自动化机制实现系统的持续改进和演化

---

## 概述

持续演化系统是 sanliu 技能的高级能力，它在自迭代机制的基础上，提供更智能、更自动化的系统演化能力。该系统通过实时监控、智能分析、自动触发和渐进式优化，实现技能和系统的持续改进。

### 核心特征

- **智能监控**：实时监控系统状态和性能指标
- **自动触发**：基于阈值和模式自动触发演化过程
- **渐进优化**：采用渐进式策略降低风险
- **可追溯性**：完整记录演化历史和决策过程
- **可回滚性**：支持快速回滚到稳定状态

---

## 系统架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          持续演化系统架构                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                         监控层 (Monitoring Layer)                    │   │
│   │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│   │  │ 性能监控器   │  │ 质量监控器   │  │ 安全监控器   │              │   │
│   │  │ Performance  │  │   Quality    │  │  Security    │              │   │
│   │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                         分析层 (Analysis Layer)                      │   │
│   │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│   │  │ 趋势分析器   │  │ 异常检测器   │  │ 影响评估器   │              │   │
│   │  │   Trend      │  │  Anomaly     │  │   Impact     │              │   │
│   │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                         决策层 (Decision Layer)                      │   │
│   │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│   │  │ 策略选择器   │  │ 优先级排序   │  │ 风险评估器   │              │   │
│   │  │  Strategy    │  │  Priority    │  │    Risk      │              │   │
│   │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                         执行层 (Execution Layer)                     │   │
│   │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│   │  │ 演化执行器   │  │ 变更管理器   │  │ 回滚管理器   │              │   │
│   │  │  Executor    │  │   Change     │  │  Rollback    │              │   │
│   │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                         存储层 (Storage Layer)                       │   │
│   │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│   │  │ 演化历史库   │  │ 状态快照库   │  │ 决策日志库   │              │   │
│   │  │   History    │  │   Snapshot   │  │ DecisionLog  │              │   │
│   │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 核心组件

### 1. 演化类型 (EvolutionType)

| 类型 | 说明 | 触发场景 | 执行频率 |
|------|------|----------|----------|
| `skill_optimization` | 技能优化 | 技能性能下降、错误率上升 | 按需触发 |
| `workflow_adaptation` | 工作流适应 | 流程效率降低、瓶颈出现 | 按需触发 |
| `resource_rebalance` | 资源重平衡 | 资源利用率不均、负载过高 | 定期检查 |
| `knowledge_update` | 知识库更新 | 新知识积累、规则过时 | 定期更新 |
| `performance_tuning` | 性能调优 | 性能指标下降、响应变慢 | 持续监控 |

### 2. 演化阶段 (EvolutionStage)

```
演化阶段流程:

分析 (Analysis) ──▶ 规划 (Planning) ──▶ 执行 (Execution) ──▶ 验证 (Validation) ──▶ 部署 (Deployment)
     │                  │                   │                    │                    │
     ▼                  ▼                   ▼                    ▼                    ▼
  收集指标          制定变更计划        执行变更操作         验证变更效果         发布变更结果
  分析趋势          评估影响范围        监控执行过程         运行测试用例         更新系统状态
  识别问题          确定执行顺序        处理异常情况         对比前后指标         记录演化历史
```

### 3. 触发类型 (EvolutionTriggerType)

| 触发类型 | 说明 | 使用场景 |
|----------|------|----------|
| `automatic` | 自动触发 | 系统自动检测到问题并触发 |
| `manual` | 手动触发 | 用户主动发起演化请求 |
| `scheduled` | 定时触发 | 按预定计划执行演化 |
| `threshold_based` | 阈值触发 | 指标超过阈值时触发 |

---

## 使用方法

### API 接口

#### 获取演化状态

```bash
GET /api/evolution/status
```

**响应示例：**
```json
{
  "status": "idle",
  "current_stage": null,
  "evolution_type": null,
  "progress": 0.0,
  "started_at": null,
  "estimated_completion": null,
  "current_metrics": {
    "skill_success_rate": 94.5,
    "avg_response_time": 1.2,
    "active_agents": 5,
    "pending_tasks": 12
  },
  "active_changes": [],
  "last_evolution": "2024-03-29T10:30:00",
  "next_scheduled": "2024-03-30T04:00:00"
}
```

#### 触发演化

```bash
POST /api/evolution/trigger
```

**请求体：**
```json
{
  "evolution_type": "skill_optimization",
  "reason": "技能成功率下降至85%",
  "parameters": {
    "target_skill": "zhongshusheng",
    "optimization_scope": "performance"
  },
  "force": false,
  "dry_run": false,
  "priority": "high",
  "scheduled_at": null
}
```

**响应示例：**
```json
{
  "trigger_id": 1711705800000,
  "evolution_type": "skill_optimization",
  "status": "running",
  "message": "演化已触发，正在后台执行",
  "estimated_duration": 600,
  "queued_position": 1
}
```

#### 查询演化历史

```bash
GET /api/evolution/history?skip=0&limit=20&evolution_type=skill_optimization
```

**响应示例：**
```json
{
  "total": 100,
  "items": [
    {
      "id": 1,
      "evolution_type": "skill_optimization",
      "trigger_type": "automatic",
      "status": "completed",
      "started_at": "2024-03-29T10:00:00",
      "completed_at": "2024-03-29T11:00:00",
      "duration_seconds": 3600,
      "changes_count": 5,
      "success_rate": 0.95,
      "metrics_before": {"performance": 80, "efficiency": 75},
      "metrics_after": {"performance": 85, "efficiency": 80},
      "summary": "技能优化完成，性能提升6.25%"
    }
  ],
  "page": 1,
  "page_size": 20,
  "total_pages": 5
}
```

#### 获取演化趋势

```bash
GET /api/evolution/trends?metric=performance&period=7d
```

**响应示例：**
```json
{
  "metric_name": "performance",
  "period": "7d",
  "data_points": [
    {"timestamp": "2024-03-23T00:00:00", "value": 80.5, "label": "Day 1"},
    {"timestamp": "2024-03-24T00:00:00", "value": 81.2, "label": "Day 2"},
    {"timestamp": "2024-03-25T00:00:00", "value": 82.0, "label": "Day 3"}
  ],
  "trend_direction": "upward",
  "change_percentage": 5.5,
  "prediction": 86.5,
  "confidence": 0.85
}
```

### WebSocket 实时监控

```javascript
const ws = new WebSocket('ws://localhost:8000/api/evolution/ws');

ws.onopen = () => {
  ws.send(JSON.stringify({ type: 'get_status' }));
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  
  switch (message.type) {
    case 'initial_state':
      console.log('初始状态:', message.data);
      break;
    case 'evolution_started':
      console.log('演化开始:', message.data);
      break;
    case 'evolution_progress':
      console.log('演化进度:', message.data);
      break;
    case 'evolution_completed':
      console.log('演化完成:', message.data);
      break;
    case 'evolution_paused':
      console.log('演化暂停:', message.data);
      break;
    case 'evolution_cancelled':
      console.log('演化取消:', message.data);
      break;
  }
};

setInterval(() => {
  ws.send(JSON.stringify({ type: 'heartbeat' }));
}, 30000);
```

### 命令行工具

#### 查看演化状态

```bash
python scripts/evolution_manager.py status
```

#### 手动触发演化

```bash
python scripts/evolution_manager.py trigger \
  --type skill_optimization \
  --reason "手动触发技能优化" \
  --priority high
```

#### 查看演化历史

```bash
python scripts/evolution_manager.py history \
  --limit 10 \
  --type skill_optimization
```

#### 暂停/恢复/取消演化

```bash
python scripts/evolution_manager.py pause
python scripts/evolution_manager.py resume
python scripts/evolution_manager.py cancel
```

---

## 演化策略

### 1. 技能优化策略

```yaml
skill_optimization:
  触发条件:
    - 成功率 < 90%
    - 平均响应时间 > 基线 * 1.5
    - 错误率 > 5%
  
  优化措施:
    - 参数调优: 调整技能参数配置
    - 缓存优化: 优化缓存策略和命中率
    - 并发调整: 调整并发处理能力
    - 资源重分配: 重新分配计算资源
  
  验证标准:
    - 成功率提升 >= 5%
    - 响应时间降低 >= 10%
    - 错误率降低 >= 50%
```

### 2. 工作流适应策略

```yaml
workflow_adaptation:
  触发条件:
    - 流程执行时间 > 预期 * 1.5
    - 瓶颈阶段识别
    - 资源利用率不均
  
  适应措施:
    - 并行化: 将串行步骤改为并行
    - 缓存复用: 增加中间结果缓存
    - 负载均衡: 重新分配任务负载
    - 流程简化: 移除冗余步骤
  
  验证标准:
    - 执行时间降低 >= 20%
    - 资源利用率均衡度 >= 0.8
    - 瓶颈消除或缓解
```

### 3. 资源重平衡策略

```yaml
resource_rebalance:
  触发条件:
    - CPU利用率 > 80% 持续5分钟
    - 内存使用率 > 85%
    - 磁盘IO等待时间 > 100ms
  
  重平衡措施:
    - 负载迁移: 迁移部分负载到其他节点
    - 资源扩容: 动态增加资源配额
    - 任务调度: 调整任务执行优先级
    - 缓存清理: 清理过期缓存释放资源
  
  验证标准:
    - CPU利用率 <= 70%
    - 内存使用率 <= 75%
    - IO等待时间 <= 50ms
```

---

## 与自迭代机制的集成

持续演化系统与自迭代机制紧密集成，形成完整的自我改进闭环：

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    持续演化与自迭代集成架构                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────┐                        ┌─────────────────┐          │
│   │  持续演化系统    │                        │  自迭代机制      │          │
│   │                 │                        │                 │          │
│   │  ┌───────────┐  │    触发自迭代          │  ┌───────────┐  │          │
│   │  │ 监控分析  │──┼───────────────────────▶│  │ 问题检测  │  │          │
│   │  └───────────┘  │                        │  └───────────┘  │          │
│   │         │       │                        │         │       │          │
│   │         ▼       │                        │         ▼       │          │
│   │  ┌───────────┐  │    提供演化方向          │  ┌───────────┐  │          │
│   │  │ 策略决策  │◀─┼────────────────────────│  │ 修复执行  │  │          │
│   │  └───────────┘  │                        │  └───────────┘  │          │
│   │         │       │                        │         │       │          │
│   │         ▼       │                        │         ▼       │          │
│   │  ┌───────────┐  │    反馈演化效果          │  ┌───────────┐  │          │
│   │  │ 效果验证  │──┼───────────────────────▶│  │ 版本迭代  │  │          │
│   │  └───────────┘  │                        │  └───────────┘  │          │
│   │                 │                        │                 │          │
│   └─────────────────┘                        └─────────────────┘          │
│                                                                             │
│   集成点:                                                                    │
│   1. 演化系统监控到问题 → 触发自迭代流程                                      │
│   2. 自迭代修复完成 → 反馈到演化系统验证效果                                   │
│   3. 演化系统评估效果 → 决定是否继续演化或回滚                                 │
│   4. 自迭代记录版本 → 演化系统更新历史和指标                                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 集成配置示例

```yaml
integration:
  evolution_to_iteration:
    enabled: true
    auto_trigger: true
    trigger_conditions:
      - type: performance_degradation
        threshold: 0.15
        action: trigger_skill_optimization
      - type: error_rate_spike
        threshold: 0.05
        action: trigger_self_iteration
  
  iteration_to_evolution:
    enabled: true
    feedback_enabled: true
    validation_required: true
    rollback_on_failure: true
  
  shared_components:
    - problem_detector
    - version_manager
    - rollback_manager
    - metrics_collector
```

### 集成使用示例

```python
from scripts.self_iteration_intelligent import SelfIterationOrchestrator
from scripts.evolution_manager import EvolutionManager

iteration_orchestrator = SelfIterationOrchestrator(project_root='./')
evolution_manager = EvolutionManager(project_root='./')

problems = iteration_orchestrator.detector.detect_problems('./src')

should_evolve, evolution_type = evolution_manager.analyze_evolution_need(problems)

if should_evolve:
    result = evolution_manager.trigger_evolution(
        evolution_type=evolution_type,
        reason="检测到需要演化的模式",
        auto_trigger_iteration=True
    )
    
    print(f"演化已触发: {result['trigger_id']}")
    print(f"关联的自迭代计划: {result['iteration_plan_id']}")
```

---

## 最佳实践

### 1. 演化策略配置

```yaml
evolution_config:
  safety_first:
    enable_dry_run: true
    require_approval_for_major_changes: true
    max_concurrent_changes: 3
    rollback_threshold: 0.8
  
  monitoring:
    metrics_collection_interval: 60
    trend_analysis_window: 7d
    anomaly_detection_sensitivity: medium
  
  execution:
    stage_timeout: 3600
    max_retry_attempts: 3
    parallel_execution: true
    checkpoint_interval: 300
```

### 2. 风险控制

```yaml
risk_control:
  pre_evolution:
    - backup_current_state: true
    - create_snapshot: true
    - validate_preconditions: true
  
  during_evolution:
    - monitor_progress: true
    - detect_anomalies: true
    - auto_pause_on_issues: true
  
  post_evolution:
    - validate_results: true
    - compare_metrics: true
    - update_baselines: true
```

### 3. 回滚策略

```yaml
rollback_strategy:
  automatic_rollback:
    enabled: true
    conditions:
      - success_rate_drop > 20%
      - error_rate_increase > 10%
      - performance_degradation > 30%
  
  manual_rollback:
    enabled: true
    require_approval: false
    preserve_evolution_history: true
  
  partial_rollback:
    enabled: true
    granularity: component
    max_components: 3
```

---

## 监控与告警

### 关键指标

| 指标类别 | 指标名称 | 说明 | 告警阈值 |
|----------|----------|------|----------|
| 性能 | evolution_duration | 演化执行时长 | > 2小时 |
| 性能 | success_rate | 演化成功率 | < 90% |
| 质量 | changes_success_rate | 变更成功率 | < 85% |
| 质量 | rollback_rate | 回滚率 | > 10% |
| 可用性 | evolution_availability | 演化系统可用性 | < 99% |

### 告警配置

```yaml
alerts:
  evolution_failed:
    condition: status == 'failed'
    severity: critical
    notification: [email, slack]
  
  evolution_timeout:
    condition: duration > max_duration
    severity: high
    notification: [email]
  
  frequent_rollback:
    condition: rollback_count > 3 in 24h
    severity: high
    notification: [email, slack]
```

---

## 故障排除

### 常见问题

**Q: 演化过程卡在某个阶段？**

```bash
python scripts/evolution_manager.py status --detailed

python scripts/evolution_manager.py resume --force

python scripts/evolution_manager.py cancel
```

**Q: 演化效果不明显？**

```bash
python scripts/evolution_manager.py trends --metric performance --period 30d

python scripts/evolution_manager.py validate --evolution-id <id>

python scripts/evolution_manager.py rollback --evolution-id <id>
```

**Q: 演化触发过于频繁？**

```yaml
evolution_config:
  trigger_cooldown: 3600
  min_interval_between_evolutions: 7200
  max_evolutions_per_day: 5
```

---

## 总结

持续演化系统通过以下能力实现系统的自我改进：

1. **智能监控** - 实时监控系统状态和性能
2. **自动触发** - 基于阈值和模式自动启动演化
3. **渐进优化** - 采用渐进式策略降低风险
4. **完整追溯** - 记录所有演化历史和决策
5. **快速回滚** - 支持一键回滚到稳定状态

通过与自迭代机制的深度集成，持续演化系统形成了完整的自我改进闭环，确保系统始终保持最佳状态。

---

## 永久演化模式

永久演化模式是持续演化系统的高级运行模式，支持在后台持续运行演化循环，实现真正的"持续"演化能力。

### 模式概述

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          永久演化模式架构                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                      永久演化控制器                                   │   │
│   │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│   │  │ 状态管理器   │  │ 周期调度器   │  │ 优雅停止器   │              │   │
│   │  │   State      │  │  Scheduler   │  │   Stopper    │              │   │
│   │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                      演化循环执行器                                   │   │
│   │                                                                      │   │
│   │   ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐     │   │
│   │   │ 问题检测 │───▶│ 自动修复 │───▶│ 优化学习 │───▶│ 验证反馈 │     │   │
│   │   │  Detect  │    │   Fix    │    │  Learn   │    │ Validate │     │   │
│   │   └──────────┘    └──────────┘    └──────────┘    └──────────┘     │   │
│   │         ▲                                              │           │   │
│   │         └──────────────────────────────────────────────┘           │   │
│   │                         持续循环                                    │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                      状态持久化层                                     │   │
│   │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│   │  │ 演化状态库   │  │ 历史记录库   │  │ 配置存储库   │              │   │
│   │  │   State DB   │  │  History DB  │  │ Config Store │              │   │
│   │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 启动永久演化模式

#### 命令行启动

```bash
python scripts/continuous_evolution_controller.py start --mode perpetual \
  --project-root ./ \
  --cycle-interval 3600 \
  --max-cycles 0
```

**参数说明：**

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--mode` | 运行模式：`single`（单次）、`perpetual`（永久） | `single` |
| `--project-root` | 项目根目录 | 当前目录 |
| `--cycle-interval` | 演化周期间隔（秒） | 3600 |
| `--max-cycles` | 最大演化周期数（0表示无限制） | 0 |
| `--config` | 配置文件路径 | `config/evolution.yaml` |
| `--daemon` | 以守护进程模式运行 | False |

#### API 启动

```bash
POST /api/evolution/perpetual/start
Content-Type: application/json

{
  "project_root": "./",
  "cycle_interval": 3600,
  "max_cycles": 0,
  "config": {
    "auto_fix_enabled": true,
    "learning_enabled": true,
    "notification_enabled": true
  }
}
```

**响应示例：**
```json
{
  "status": "started",
  "perpetual_id": "PERP-20240329120000",
  "started_at": "2024-03-29T12:00:00",
  "config": {
    "cycle_interval": 3600,
    "max_cycles": 0,
    "auto_fix_enabled": true
  },
  "message": "永久演化模式已启动"
}
```

### 停止永久演化模式

#### 优雅停止

```bash
python scripts/continuous_evolution_controller.py stop --graceful
```

优雅停止会等待当前演化周期完成后停止。

#### 强制停止

```bash
python scripts/continuous_evolution_controller.py stop --force
```

强制停止会立即中断当前演化周期。

#### API 停止

```bash
POST /api/evolution/perpetual/stop
Content-Type: application/json

{
  "mode": "graceful",
  "timeout": 300
}
```

### 状态监控

#### 查看永久演化状态

```bash
python scripts/continuous_evolution_controller.py status --perpetual
```

**输出示例：**
```
=== 永久演化模式状态 ===

状态: running
启动时间: 2024-03-29T12:00:00
运行时长: 24小时 30分钟
已完成周期: 24
当前周期: 25
  阶段: optimization
  进度: 65%
  开始时间: 2024-03-30T12:00:00

统计信息:
  问题检测: 156 个
  自动修复: 142 个
  优化应用: 38 个
  学习记录: 25 条

下次周期: 2024-03-30T13:00:00
```

#### WebSocket 实时监控

```javascript
const ws = new WebSocket('ws://localhost:8000/api/evolution/perpetual/ws');

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  
  switch (message.type) {
    case 'cycle_started':
      console.log(`周期 ${message.cycle_number} 开始`);
      break;
    case 'cycle_completed':
      console.log(`周期 ${message.cycle_number} 完成`);
      console.log(`修复问题: ${message.fixes_applied}`);
      console.log(`学习记录: ${message.learnings_recorded}`);
      break;
    case 'perpetual_stopped':
      console.log('永久演化已停止');
      break;
  }
};
```

---

## 演化循环执行器

演化循环执行器是永久演化模式的核心组件，负责执行完整的演化循环。

### 循环阶段

```
演化循环四阶段:

┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   阶段1: 问题检测 (Detection)                                               │
│   ├─ 扫描项目代码                                                           │
│   ├─ 分析日志文件                                                           │
│   ├─ 检测性能指标                                                           │
│   └─ 生成问题列表                                                           │
│                                                                             │
│   阶段2: 自动修复 (Fixing)                                                  │
│   ├─ 问题优先级排序                                                         │
│   ├─ 选择修复策略                                                           │
│   ├─ 执行修复操作                                                           │
│   └─ 验证修复效果                                                           │
│                                                                             │
│   阶段3: 优化学习 (Learning)                                                │
│   ├─ 分析修复模式                                                           │
│   ├─ 提取最佳实践                                                           │
│   ├─ 更新知识库                                                             │
│   └─ 生成优化建议                                                           │
│                                                                             │
│   阶段4: 验证反馈 (Validation)                                              │
│   ├─ 运行测试套件                                                           │
│   ├─ 对比性能指标                                                           │
│   ├─ 生成演化报告                                                           │
│   └─ 决定下一步行动                                                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 执行器配置

```yaml
evolution_cycle:
  detection:
    enabled: true
    scan_patterns:
      - "**/*.py"
      - "**/*.js"
      - "**/*.ts"
    log_dirs:
      - "./logs"
      - "./var/log"
    metrics_sources:
      - type: prometheus
        endpoint: "http://localhost:9090"
      - type: custom
        script: "./scripts/collect_metrics.py"
  
  fixing:
    enabled: true
    max_fixes_per_cycle: 50
    strategies:
      - syntax_fix
      - import_fix
      - security_fix
      - performance_fix
    auto_rollback_on_failure: true
  
  learning:
    enabled: true
    pattern_extraction: true
    best_practice_learning: true
    knowledge_sharing: true
  
  validation:
    enabled: true
    test_command: "pytest tests/"
    performance_benchmark: true
    coverage_threshold: 0.8
```

### 执行器使用示例

#### 编程接口

```python
from scripts.evolution_cycle_executor import EvolutionCycleExecutor

executor = EvolutionCycleExecutor(
    project_root='./',
    config_path='./config/evolution.yaml'
)

result = executor.execute_cycle()

print(f"检测问题: {result['detection']['issues_found']}")
print(f"修复问题: {result['fixing']['issues_fixed']}")
print(f"学习记录: {result['learning']['patterns_learned']}")
print(f"验证结果: {result['validation']['status']}")
```

#### 执行单个阶段

```python
from scripts.evolution_cycle_executor import EvolutionCycleExecutor

executor = EvolutionCycleExecutor(project_root='./')

detection_result = executor.execute_stage('detection')
print(f"检测到 {len(detection_result['issues'])} 个问题")

fixing_result = executor.execute_stage('fixing', issues=detection_result['issues'])
print(f"修复了 {fixing_result['fixed_count']} 个问题")

learning_result = executor.execute_stage('learning', fixes=fixing_result['fixes'])
print(f"学习了 {len(learning_result['patterns'])} 个模式")

validation_result = executor.execute_stage('validation')
print(f"验证状态: {validation_result['status']}")
```

#### 自定义执行流程

```python
from scripts.evolution_cycle_executor import EvolutionCycleExecutor, CycleConfig

config = CycleConfig(
    detection_enabled=True,
    fixing_enabled=True,
    learning_enabled=True,
    validation_enabled=True,
    max_fixes_per_cycle=20,
    auto_rollback=True
)

executor = EvolutionCycleExecutor(project_root='./', config=config)

for cycle_result in executor.run_cycles(max_cycles=10):
    print(f"周期 {cycle_result['cycle_number']} 完成")
    if cycle_result['should_stop']:
        print("检测到停止条件，终止演化")
        break
```

### 执行器事件回调

```python
from scripts.evolution_cycle_executor import EvolutionCycleExecutor

def on_cycle_start(cycle_number):
    print(f"周期 {cycle_number} 开始")

def on_issue_detected(issue):
    print(f"检测到问题: {issue['type']} - {issue['description']}")

def on_fix_applied(fix):
    print(f"应用修复: {fix['strategy']} - {fix['file']}")

def on_learning_recorded(learning):
    print(f"记录学习: {learning['pattern_type']}")

def on_cycle_complete(result):
    print(f"周期完成: 修复 {result['fixes']} 个问题")

executor = EvolutionCycleExecutor(project_root='./')
executor.on_cycle_start = on_cycle_start
executor.on_issue_detected = on_issue_detected
executor.on_fix_applied = on_fix_applied
executor.on_learning_recorded = on_learning_recorded
executor.on_cycle_complete = on_cycle_complete

executor.run_perpetual()
```

---

## 配置选项说明

### 完整配置文件

```yaml
# config/evolution.yaml

evolution:
  mode: perpetual
  project_root: ./
  
  cycle:
    interval: 3600
    max_cycles: 0
    timeout: 7200
  
  detection:
    enabled: true
    sources:
      code_scan:
        enabled: true
        patterns:
          - "**/*.py"
          - "**/*.js"
          - "**/*.ts"
        exclude_patterns:
          - "**/node_modules/**"
          - "**/venv/**"
          - "**/.git/**"
      
      log_analysis:
        enabled: true
        log_dirs:
          - "./logs"
        patterns:
          error: "ERROR|Error|error"
          warning: "WARN|Warning|warning"
          critical: "CRITICAL|Critical|critical"
      
      metrics_monitoring:
        enabled: true
        endpoints:
          - type: prometheus
            url: "http://localhost:9090"
          - type: custom
            script: "./scripts/collect_metrics.py"
    
    thresholds:
      error_rate: 0.05
      warning_rate: 0.10
      performance_degradation: 0.20
  
  fixing:
    enabled: true
    max_fixes_per_cycle: 50
    strategies:
      syntax_fix:
        enabled: true
        priority: high
      import_fix:
        enabled: true
        priority: high
      security_fix:
        enabled: true
        priority: critical
      performance_fix:
        enabled: true
        priority: medium
      style_fix:
        enabled: false
        priority: low
    
    auto_rollback:
      enabled: true
      conditions:
        - test_failure
        - performance_regression
        - new_errors
    
    backup:
      enabled: true
      directory: "./.evolution/backups"
      retention_days: 30
  
  learning:
    enabled: true
    pattern_extraction:
      enabled: true
      min_occurrences: 3
      confidence_threshold: 0.8
    
    best_practice_learning:
      enabled: true
      sources:
        - successful_fixes
        - performance_improvements
        - code_reviews
    
    knowledge_sharing:
      enabled: true
      cross_project: true
      knowledge_base_path: "./.evolution/knowledge"
  
  validation:
    enabled: true
    test_command: "pytest tests/ -v"
    coverage_threshold: 0.8
    performance_benchmark:
      enabled: true
      baseline_file: "./.evolution/baseline.json"
    
    rollback_conditions:
      - condition: test_failure_rate > 0.1
        action: rollback
      - condition: performance_regression > 0.2
        action: rollback
      - condition: new_errors > 5
        action: pause_and_notify
  
  notification:
    enabled: true
    channels:
      - type: email
        recipients:
          - dev-team@example.com
        events:
          - cycle_completed
          - critical_issue
          - evolution_stopped
      
      - type: slack
        webhook_url: "https://hooks.slack.com/services/xxx"
        events:
          - critical_issue
          - evolution_stopped
      
      - type: webhook
        url: "http://localhost:8080/webhook/evolution"
        events:
          - cycle_completed
  
  persistence:
    state_file: "./.evolution/state.json"
    history_file: "./.evolution/history.json"
    knowledge_base: "./.evolution/knowledge"
  
  logging:
    level: INFO
    file: "./.evolution/evolution.log"
    rotation:
      max_size: 10MB
      backup_count: 5
```

## 配置项详解

#### 核心配置

| 配置项 | 类型 | 说明 | 默认值 |
|--------|------|------|--------|
| `evolution.mode` | string | 运行模式：`single`、`perpetual` | `single` |
| `evolution.project_root` | string | 项目根目录 | `./` |
| `cycle.interval` | int | 演化周期间隔（秒） | 3600 |
| `cycle.max_cycles` | int | 最大周期数（0=无限制） | 0 |
| `cycle.timeout` | int | 单周期超时时间（秒） | 7200 |

#### 检测配置

| 配置项 | 类型 | 说明 | 默认值 |
|--------|------|------|--------|
| `detection.enabled` | bool | 是否启用检测 | true |
| `detection.sources.code_scan.enabled` | bool | 是否启用代码扫描 | true |
| `detection.sources.log_analysis.enabled` | bool | 是否启用日志分析 | true |
| `detection.sources.metrics_monitoring.enabled` | bool | 是否启用指标监控 | true |
| `detection.thresholds.error_rate` | float | 错误率阈值 | 0.05 |
| `detection.thresholds.performance_degradation` | float | 性能下降阈值 | 0.20 |

#### 修复配置

| 配置项 | 类型 | 说明 | 默认值 |
|--------|------|------|--------|
| `fixing.enabled` | bool | 是否启用修复 | true |
| `fixing.max_fixes_per_cycle` | int | 每周期最大修复数 | 50 |
| `fixing.strategies.*.enabled` | bool | 是否启用该策略 | true |
| `fixing.strategies.*.priority` | string | 策略优先级 | - |
| `fixing.auto_rollback.enabled` | bool | 是否启用自动回滚 | true |
| `fixing.backup.enabled` | bool | 是否启用备份 | true |

#### 学习配置

| 配置项 | 类型 | 说明 | 默认值 |
|--------|------|------|--------|
| `learning.enabled` | bool | 是否启用学习 | true |
| `learning.pattern_extraction.enabled` | bool | 是否启用模式提取 | true |
| `learning.pattern_extraction.min_occurrences` | int | 最小出现次数 | 3 |
| `learning.pattern_extraction.confidence_threshold` | float | 置信度阈值 | 0.8 |
| `learning.knowledge_sharing.enabled` | bool | 是否启用知识共享 | true |
| `learning.knowledge_sharing.cross_project` | bool | 是否跨项目共享 | true |

#### 验证配置

| 配置项 | 类型 | 说明 | 默认值 |
|--------|------|------|--------|
| `validation.enabled` | bool | 是否启用验证 | true |
| `validation.test_command` | string | 测试命令 | - |
| `validation.coverage_threshold` | float | 覆盖率阈值 | 0.8 |
| `validation.performance_benchmark.enabled` | bool | 是否启用性能基准 | true |

#### 通知配置

| 配置项 | 类型 | 说明 | 默认值 |
|--------|------|------|--------|
| `notification.enabled` | bool | 是否启用通知 | true |
| `notification.channels[].type` | string | 通知类型 | - |
| `notification.channels[].events` | list | 触发事件列表 | - |

### 环境变量覆盖

配置项可通过环境变量覆盖：

```bash
export EVOLUTION_MODE=perpetual
export EVOLUTION_CYCLE_INTERVAL=1800
export EVOLUTION_DETECTION_ENABLED=true
export EVOLUTION_FIXING_MAX_FIXES=100
export EVOLUTION_LEARNING_ENABLED=true
export EVOLUTION_NOTIFICATION_ENABLED=false
```

### 配置验证

```bash
python scripts/continuous_evolution_controller.py validate-config --config config/evolution.yaml
```

**输出示例：**
```
=== 配置验证结果 ===

配置文件: config/evolution.yaml
状态: 有效

警告:
  - [WARNING] fixing.max_fixes_per_cycle=50 可能过高，建议不超过 30
  - [WARNING] notification.channels 中没有配置 critical_issue 事件的通知

建议:
  - 建议启用 validation.performance_benchmark 以监控性能变化
  - 建议配置 backup.retention_days 以自动清理旧备份
```

---

## 技能自身演化

技能自身演化是持续演化系统的高级应用，允许技能系统自我更新和优化，实现真正的"自我进化"能力。

### 演化能力架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          技能自身演化架构                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                      演化感知层                                       │   │
│   │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│   │  │ 技能状态监控 │  │ 性能指标采集 │  │ 用户反馈收集 │              │   │
│   │  │   Status     │  │   Metrics    │  │   Feedback   │              │   │
│   │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                      演化决策层                                       │   │
│   │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│   │  │ 演化需求分析 │  │ 演化策略选择 │  │ 风险评估器   │              │   │
│   │  │   Analysis   │  │   Strategy   │  │    Risk      │              │   │
│   │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                      演化执行层                                       │   │
│   │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│   │  │ 技能内容更新 │  │ 配置参数优化 │  │ 知识库扩充   │              │   │
│   │  │   Content    │  │   Config     │  │  Knowledge   │              │   │
│   │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                      演化验证层                                       │   │
│   │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│   │  │ 功能正确性   │  │ 性能回归测试 │  │ 兼容性验证   │              │   │
│   │  │ Correctness  │  │ Regression   │  │ Compatibility│              │   │
│   │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 演化类型

| 演化类型 | 说明 | 触发条件 | 执行频率 |
|----------|------|----------|----------|
| `skill_content_evolution` | 技能内容演化 | 内容过时、用户反馈 | 按需触发 |
| `skill_config_evolution` | 技能配置演化 | 性能下降、参数不当 | 定期检查 |
| `skill_knowledge_evolution` | 知识库演化 | 新知识积累、规则更新 | 持续进行 |
| `skill_structure_evolution` | 结构演化 | 架构优化、模块重组 | 谨慎触发 |

### 技能内容演化

#### 自动更新机制

```python
from scripts.skill_evolution_manager import SkillEvolutionManager

manager = SkillEvolutionManager(project_root='./')

result = manager.evolve_skill_content(
    skill_id='sanliu',
    evolution_type='skill_content_evolution',
    trigger_reason='用户反馈表明技能描述不够清晰',
    auto_apply=False
)

print(f"演化计划: {result['plan_id']}")
print(f"建议变更: {len(result['suggested_changes'])} 项")
for change in result['suggested_changes']:
    print(f"  - {change['type']}: {change['description']}")
```

#### 演化审批流程

```bash
python scripts/skill_evolution_manager.py propose \
  --skill sanliu \
  --type skill_content_evolution \
  --reason "优化技能描述和示例"

python scripts/skill_evolution_manager.py review \
  --plan-id PLAN-20240329120000

python scripts/skill_evolution_manager.py apply \
  --plan-id PLAN-20240329120000 \
  --approve
```

### 技能配置演化

#### 配置优化流程

```python
from scripts.skill_evolution_manager import SkillConfigEvolver

evolver = SkillConfigEvolver(skill_root='./')

analysis = evolver.analyze_config_performance(
    config_file='config/skill.yaml',
    metrics_source='./logs/performance.json'
)

print(f"配置健康分数: {analysis['health_score']}")
print(f"优化建议: {len(analysis['suggestions'])} 项")

if analysis['needs_optimization']:
    result = evolver.optimize_config(
        suggestions=analysis['suggestions'],
        auto_apply=False,
        create_backup=True
    )
    print(f"优化计划: {result['plan_id']}")
```

#### 配置演化命令

```bash
python scripts/skill_evolution_manager.py config-analyze \
  --config config/skill.yaml \
  --metrics logs/performance.json

python scripts/skill_evolution_manager.py config-optimize \
  --config config/skill.yaml \
  --auto-apply \
  --backup
```

### 知识库演化

#### 知识自动更新

```python
from scripts.skill_evolution_manager import KnowledgeEvolver

evolver = KnowledgeEvolver(skill_root='./')

result = evolver.evolve_knowledge(
    knowledge_dir='./resources/knowledge',
    sources=[
        './logs/interactions.json',
        './reports/feedback.json'
    ],
    evolution_mode='incremental'
)

print(f"新增知识: {result['added_count']}")
print(f"更新知识: {result['updated_count']}")
print(f"废弃知识: {result['deprecated_count']}")
```

#### 知识演化命令

```bash
python scripts/skill_evolution_manager.py knowledge-evolve \
  --knowledge-dir ./resources/knowledge \
  --sources ./logs/interactions.json \
  --mode incremental

python scripts/skill_evolution_manager.py knowledge-validate \
  --knowledge-dir ./resources/knowledge
```

### 演化安全控制

#### 安全配置

```yaml
skill_evolution:
  safety:
    enabled: true
    
    approval_required:
      - skill_content_evolution
      - skill_structure_evolution
    
    auto_apply_allowed:
      - skill_knowledge_evolution
    
    max_changes_per_evolution: 10
    
    backup_before_evolution: true
    
    rollback_enabled: true
    
    validation_after_evolution: true
  
  constraints:
    preserve_core_functionality: true
    maintain_backward_compatibility: true
    require_test_coverage: 0.8
```

#### 演化风险评估

```python
from scripts.skill_evolution_manager import EvolutionRiskAssessor

assessor = EvolutionRiskAssessor(skill_root='./')

risk_report = assessor.assess_evolution_risk(
    evolution_plan={
        'type': 'skill_content_evolution',
        'changes': [
            {'file': 'SKILL.md', 'operation': 'update'},
            {'file': 'subskills/test.md', 'operation': 'create'}
        ]
    }
)

print(f"风险等级: {risk_report['risk_level']}")
print(f"风险分数: {risk_report['risk_score']}")
print(f"影响范围: {risk_report['impact_scope']}")
print(f"建议: {risk_report['recommendations']}")
```

---

## 演化监控API使用说明

演化监控API提供完整的演化过程监控能力，支持实时状态查询、历史记录检索和告警配置。

### API 端点总览

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/evolution/status` | GET | 获取当前演化状态 |
| `/api/evolution/trigger` | POST | 触发演化 |
| `/api/evolution/history` | GET | 查询演化历史 |
| `/api/evolution/trends` | GET | 获取演化趋势 |
| `/api/evolution/metrics` | GET | 获取演化指标 |
| `/api/evolution/alerts` | GET | 获取演化告警 |
| `/api/evolution/perpetual/start` | POST | 启动永久演化 |
| `/api/evolution/perpetual/stop` | POST | 停止永久演化 |
| `/api/evolution/perpetual/status` | GET | 永久演化状态 |
| `/api/evolution/ws` | WebSocket | 实时监控连接 |

### 状态查询API

#### 获取详细状态

```bash
GET /api/evolution/status?detailed=true
```

**响应示例：**
```json
{
  "status": "running",
  "current_stage": "execution",
  "evolution_type": "skill_optimization",
  "progress": 0.65,
  "started_at": "2024-03-29T10:00:00",
  "estimated_completion": "2024-03-29T11:00:00",
  "current_metrics": {
    "skill_success_rate": 94.5,
    "avg_response_time": 1.2,
    "active_agents": 5,
    "pending_tasks": 12,
    "memory_usage": "256MB",
    "cpu_usage": "45%"
  },
  "active_changes": [
    {
      "change_id": "CHG-001",
      "type": "config_update",
      "target": "config/skill.yaml",
      "status": "applying",
      "progress": 0.8
    }
  ],
  "last_evolution": {
    "id": "EVO-20240328-001",
    "completed_at": "2024-03-28T18:00:00",
    "success_rate": 0.95
  },
  "next_scheduled": "2024-03-30T04:00:00",
  "health_indicators": {
    "system_health": "healthy",
    "evolution_health": "optimal",
    "performance_trend": "improving"
  }
}
```

#### 获取演化指标

```bash
GET /api/evolution/metrics?period=7d&granularity=1h
```

**响应示例：**
```json
{
  "period": "7d",
  "granularity": "1h",
  "metrics": {
    "evolution_count": 42,
    "success_rate": 0.92,
    "avg_duration_seconds": 1800,
    "total_changes_applied": 156,
    "rollback_count": 3,
    "performance_improvement": 0.15
  },
  "time_series": [
    {
      "timestamp": "2024-03-23T00:00:00",
      "evolutions": 6,
      "success_rate": 0.90,
      "avg_duration": 1750
    }
  ],
  "distribution": {
    "by_type": {
      "skill_optimization": 20,
      "workflow_adaptation": 12,
      "resource_rebalance": 10
    },
    "by_trigger": {
      "automatic": 30,
      "manual": 8,
      "scheduled": 4
    }
  }
}
```

### 告警管理API

#### 获取告警列表

```bash
GET /api/evolution/alerts?status=active&severity=high
```

**响应示例：**
```json
{
  "total": 5,
  "alerts": [
    {
      "alert_id": "ALT-20240329-001",
      "type": "evolution_timeout",
      "severity": "high",
      "message": "演化执行超时，已超过2小时",
      "evolution_id": "EVO-20240329-015",
      "triggered_at": "2024-03-29T12:00:00",
      "status": "active",
      "acknowledged": false,
      "actions": [
        {
          "action": "cancel_evolution",
          "available": true
        },
        {
          "action": "extend_timeout",
          "available": true
        }
      ]
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_pages": 1
  }
}
```

#### 确认告警

```bash
POST /api/evolution/alerts/ALT-20240329-001/acknowledge
Content-Type: application/json

{
  "acknowledged_by": "admin",
  "notes": "已知晓，正在处理"
}
```

#### 配置告警规则

```bash
POST /api/evolution/alerts/rules
Content-Type: application/json

{
  "rule_name": "high_rollback_rate",
  "condition": {
    "metric": "rollback_rate",
    "operator": ">",
    "threshold": 0.1,
    "period": "24h"
  },
  "severity": "high",
  "notification": {
    "channels": ["email", "slack"],
    "recipients": ["dev-team@example.com"]
  },
  "enabled": true
}
```

### WebSocket 实时监控

#### 连接建立

```javascript
const ws = new WebSocket('ws://localhost:8000/api/evolution/ws');

ws.onopen = () => {
  ws.send(JSON.stringify({
    type: 'subscribe',
    channels: ['status', 'progress', 'alerts', 'metrics']
  }));
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  handleEvolutionMessage(message);
};

function handleEvolutionMessage(message) {
  switch (message.type) {
    case 'status_update':
      updateStatusDisplay(message.data);
      break;
    case 'progress_update':
      updateProgressBar(message.data);
      break;
    case 'alert_triggered':
      showAlert(message.data);
      break;
    case 'metrics_update':
      updateMetricsChart(message.data);
      break;
    case 'evolution_started':
      onEvolutionStarted(message.data);
      break;
    case 'evolution_completed':
      onEvolutionCompleted(message.data);
      break;
    case 'evolution_failed':
      onEvolutionFailed(message.data);
      break;
  }
}

setInterval(() => {
  ws.send(JSON.stringify({ type: 'heartbeat' }));
}, 30000);
```

#### 消息类型

| 消息类型 | 说明 | 数据字段 |
|----------|------|----------|
| `status_update` | 状态更新 | status, stage, progress |
| `progress_update` | 进度更新 | progress, eta, current_step |
| `alert_triggered` | 告警触发 | alert_id, severity, message |
| `metrics_update` | 指标更新 | metrics, timestamp |
| `evolution_started` | 演化开始 | evolution_id, type, config |
| `evolution_completed` | 演化完成 | evolution_id, summary, duration |
| `evolution_failed` | 演化失败 | evolution_id, error, rollback_status |

### 批量操作API

#### 批量查询演化状态

```bash
POST /api/evolution/batch/status
Content-Type: application/json

{
  "evolution_ids": [
    "EVO-20240329-001",
    "EVO-20240329-002",
    "EVO-20240329-003"
  ]
}
```

**响应示例：**
```json
{
  "results": [
    {
      "evolution_id": "EVO-20240329-001",
      "status": "completed",
      "success": true
    },
    {
      "evolution_id": "EVO-20240329-002",
      "status": "running",
      "progress": 0.45
    },
    {
      "evolution_id": "EVO-20240329-003",
      "status": "failed",
      "error": "Timeout exceeded"
    }
  ]
}
```

#### 批量取消演化

```bash
POST /api/evolution/batch/cancel
Content-Type: application/json

{
  "evolution_ids": [
    "EVO-20240329-002",
    "EVO-20240329-004"
  ],
  "force": false
}
```

### API 错误处理

#### 错误响应格式

```json
{
  "error": {
    "code": "EVOLUTION_IN_PROGRESS",
    "message": "已有演化正在进行，请等待完成或取消当前演化",
    "details": {
      "current_evolution_id": "EVO-20240329-001",
      "started_at": "2024-03-29T10:00:00",
      "estimated_completion": "2024-03-29T11:00:00"
    },
    "suggested_actions": [
      "等待当前演化完成",
      "取消当前演化: POST /api/evolution/EVO-20240329-001/cancel"
    ]
  }
}
```

#### 错误码列表

| 错误码 | HTTP状态码 | 说明 |
|--------|-----------|------|
| `EVOLUTION_IN_PROGRESS` | 409 | 已有演化正在进行 |
| `EVOLUTION_NOT_FOUND` | 404 | 演化记录不存在 |
| `INVALID_EVOLUTION_TYPE` | 400 | 无效的演化类型 |
| `EVOLUTION_TIMEOUT` | 504 | 演化执行超时 |
| `ROLLBACK_FAILED` | 500 | 回滚失败 |
| `PERMISSION_DENIED` | 403 | 权限不足 |
| `CONFIGURATION_ERROR` | 500 | 配置错误 |

### API 使用最佳实践

#### 1. 轮询间隔建议

```javascript
const POLLING_INTERVALS = {
  idle: 60000,       // 空闲状态：60秒
  running: 5000,     // 运行中：5秒
  completing: 2000   // 即将完成：2秒
};

function getPollingInterval(status) {
  return POLLING_INTERVALS[status] || 30000;
}
```

#### 2. 错误重试策略

```javascript
async function fetchEvolutionStatus(retries = 3) {
  for (let i = 0; i < retries; i++) {
    try {
      const response = await fetch('/api/evolution/status');
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();
    } catch (error) {
      if (i === retries - 1) throw error;
      await sleep(1000 * Math.pow(2, i));
    }
  }
}
```

#### 3. WebSocket 重连机制

```javascript
class EvolutionMonitor {
  constructor(url) {
    this.url = url;
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 1000;
  }

  connect() {
    this.ws = new WebSocket(this.url);
    
    this.ws.onclose = () => {
      if (this.reconnectAttempts < this.maxReconnectAttempts) {
        setTimeout(() => {
          this.reconnectAttempts++;
          this.connect();
        }, this.reconnectDelay * Math.pow(2, this.reconnectAttempts));
      }
    };
    
    this.ws.onopen = () => {
      this.reconnectAttempts = 0;
    };
  }
}
```

---

## 相关文档

- [自迭代机制](self_iteration.md)
- [知识库管理](knowledge_base.md)
- [白盒化流水线](baihehua_liushuixian.md)
- [路径配置管理](skill_path_management.md)
- [脚本协同调用](skill_script_coordination.md)
