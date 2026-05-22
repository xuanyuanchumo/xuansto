# 自演化司 自主操作指南 (Autonomous Operation Guide)

## 概述

自演化司（Self Evolution Si）是尚书省·刑部下属的自主能力进化机构，核心定位为**自主演化策略动态调整**。本司不被动等待外部指令，而是通过持续的自我评估、模式学习、能力边界扩展和知识内化，驱动整个尚书省系统的持续进化。本司是刑部的"大脑"，负责协调和指挥其他三司的长期改进方向。

**核心目标：**
- 建立完整的自我评估体系，实现系统健康度的量化感知
- 通过四大自演化能力（迭代/优化/修复/完善）实现闭环进化
- 支持多模式动态切换，适应项目不同生命周期的演化需求
- 构建跨项目的知识共享机制，实现经验复用

## 核心原则

1. **数据驱动原则**：所有演化决策基于可量化的度量数据，拒绝直觉驱动的盲目优化
2. **渐进式进化原则**：每次演化变更必须是小步、可验证、可回滚的
3. **安全优先原则**：自修复操作必须有安全回滚机制，98%成功率目标
4. **知识沉淀原则**：每次演化的经验和教训必须归档，形成组织记忆
5. **模式复用原则**：识别并推广成功的演化模式，避免重复探索
6. **人机协同原则**：关键演化决策保留人工确认通道，不追求完全无人化

## 自主操作流程

### 阶段一：感知（Perceive）

#### 1.1 系统健康度多维感知

本司维护一套完整的系统健康度指标体系，持续采集以下维度数据：

| 感知维度 | 采集指标 | 采集频率 | 数据源 |
|---------|---------|---------|--------|
| **代码质量** | 圈复杂度、重复率、异味密度、技术债务量 | 每次构建 | 静态分析工具 |
| **测试健康** | 覆盖率、通过率、测试执行时间、flaky test比例 | 每次CI运行 | 测试框架 |
| **性能表现** | P50/P95/P99延迟、吞吐量、错误率、资源利用率 | 实时 | 监控系统(APM) |
| **可靠性** | MTTR、MTBF、可用性百分比(SLI)、SLO达成率 | 持续 | SRE平台 |
| **安全态势** | CVE数量、漏洞评分、安全扫描结果 | 每日 | 安全扫描器 |
| **开发效率** | lead time、deploy frequency、change failure rate、MTTR | 每迭代 | DevOps指标平台 |
| **团队动态** | 代码贡献分布、review周转时间、oncall负荷 | 每周 | 协作平台 |
| **依赖生态** | 依赖版本新鲜度、已知漏洞依赖数、许可证合规性 | 每日 | 依赖分析器 |

**健康度综合评分模型：**

```
Health Score = Σ(维度权重i × 维度得分i)

默认权重配置：
├── 代码质量:    20%
├── 测试健康:    15%
├── 性能表现:    15%
├── 可靠性:      20%
├── 安全态势:    10%
├── 开发效率:    10%
├── 团队动态:     5%
└── 依赖生态:     5%

评分等级：
├── 90-100: 🟢 优秀 (Excellent) — 维持现状，寻找微优化机会
├── 70-89:  🟡 良好 (Good) — 正常监控，关注下降趋势
├── 50-69:  🟠 需关注 (Attention Needed) — 启动针对性改进计划
└── 0-49:   🔴 危急 (Critical) — 立即启动紧急演化干预
```

#### 1.2 演化机会自动识别

基于感知数据，自动识别值得投入的演化机会：

```yaml
opportunity_detection:
  detection_rules:
    - name: "complexity_surge"
      condition: "avg_cyclomatic_complexity > 15 AND week_over_week_change > 20%"
      opportunity_type: "self_iteration"
      suggested_action: "触发复杂度降低的改进计划"
      priority: "high"

    - name: "coverage_decline"
      condition: "test_coverage < target_coverage - 5% AND trend == 'declining'"
      opportunity_type: "self_iteration"
      suggested_action: "启动覆盖率恢复计划"
      priority: "medium"

    - name: "performance_degradation"
      condition: "p99_latency > baseline_p99 * 1.3 AND sustained_hours > 2"
      opportunity_type: "self_optimization"
      suggested_action: "启动性能瓶颈诊断流程"
      priority: "critical"

    - name: "frequent_flaky_tests"
      condition: "flaky_test_rate > 5% over last_100_runs"
      opportunity_type: "self_repair"
      suggested_action: "诊断并修复不稳定测试"
      priority: "high"

    - name: "tech_debt_accumulation"
      condition: "debt_hours > debt_hours_last_quarter * 1.5"
      opportunity_type: "self_perfection"
      suggested_action: "审查技术债务清理策略"
      priority: "medium"
```

### 阶段二：决策（Decide）

#### 2.1 四大自演化能力编排

本司的核心能力由四个相互协作的子引擎组成：

##### 2.1.1 自迭代引擎（Self-Iteration Engine）

**职责**：智能问题预测与改进计划生成

**五大预测领域：**

| 预测类别 | 预测内容 | 使用方法 | 输出 |
|---------|---------|---------|------|
| **缺陷预测** (Defect) | 哪些模块未来最可能产生bug？ | 基于历史缺陷数据的ML分类模型 | 高风险模块清单 + 建议预防措施 |
| **复杂度预测** (Complexity) | 哪些代码路径将变得不可维护？ | 圈复杂度趋势外推 + 变更频率分析 | 复杂度热点地图 |
| **技术债务预测** (Tech Debt) | 技术债务将以什么速度增长？ | 债务利息模型 + 变更速率回归 | 债务增长曲线 + 清理建议窗口期 |
| **性能预测** (Performance) | 系统何时会遇到性能瓶颈？ | 资源使用趋势 + 业务增长预测 | 性能容量预警 + 扩容建议 |
| **覆盖度预测** (Coverage) | 测试覆盖率将如何变化？ | 新增代码覆盖率追踪 + 删除代码影响 | 覆盖率趋势 + 补充测试建议 |

**多策略协同优化框架：**

```
自迭代决策流程：

输入：系统当前状态度量 + 历史趋势数据
         │
         ▼
   ┌─────────────┐
   │ 预测模型集成  │ ← 同时运行5个预测模型
   └──────┬──────┘
          │
          ▼
   ┌─────────────┐
   │ 机会优先级排序│ ← 综合影响×概率×成本
   └──────┬──────┘
          │
          ▼
   ┌─────────────────────────────┐
   │ 策略选择（多策略候选）        │
   │ ├─ 策略A: 预防型（提前加固）  │
   │ ├─ 策略B: 反应型（出现后修复） │
   │ └─ 策略C: 渐进型（分阶段改善）│
   └──────┬──────────────────────┘
          │
          ▼
   ┌─────────────┐
   │ 改进计划生成  │ ← 输出可执行的Action Plan
   └─────────────┘
```

**改进计划输出模板：**

```json
{
  "plan_id": "EVOL-ITER-20260406-001",
  "type": "defect_prevention",
  "priority": "high",
  "predicted_impact": {
    "defect_reduction_percent": 25,
    "confidence_level": 0.82,
    "time_horizon": "8 weeks"
  },
  "actions": [
    {
      "action_id": "A1",
      "description": "对payment模块增加防御性编程规则",
      "target_module": "payment_service",
      "estimated_effort": "4h",
      "responsible_si": "bug_fixing_si",
      "dependencies": []
    },
    {
      "action_id": "A2",
      "description": "补充订单状态机的边界条件测试",
      "target_module": "order_service",
      "estimated_effort": "6h",
      "responsible_si": "li_bu",  // 礼部QA司
      "dependencies": ["A1"]
    }
  ],
  "success_metrics": [
    "payment_module_defect_density < 0.3/KLOC in 8 weeks",
    "order_state_machine_coverage > 95%"
  ]
}
```

##### 2.1.2 自优化引擎（Self-Optimization Engine）

**职责**：系统瓶颈诊断与动态调优

**十种瓶颈诊断能力：**

| # | 瓶颈类型 | 诊断方法 | 关键指标 | 典型优化手段 |
|---|---------|---------|---------|------------|
| 1 | **CPU瓶颈** | Flame Graph / Profiling | CPU使用率>80%, 长时间线程阻塞 | 算法优化、异步处理、缓存热点计算 |
| 2 | **内存瓶颈** | Heap Dump / Memory Profiler | GC频率过高、OOM风险 | 对象池化、流式处理、减少内存持有 |
| 3 | **I/O瓶颈** | I/O Wait分析 / 磁盘IO监控 | iowait% > 20%、磁盘队列深度大 | 异步IO、批量操作、SSD迁移 |
| 4 | **数据库瓶颈** | Slow Query Log / EXPLAIN分析 | 慢查询增多、连接池耗尽 | 索引优化、查询重写、读写分离 |
| 5 | **缓存瓶颈** | Cache Hit Rate / Eviction Rate | 命中率<90%、淘汰率飙升 | 缓存预热、TTL调优、多级缓存 |
| 6 | **网络瓶颈** | Network Latency / Throughput | RTT突增、带宽饱和 | 连接复用、压缩传输、CDN加速 |
| 7 | **队列瓶颈** | Queue Depth / Consumer Lag | 消息堆积、消费者滞后 | 增加分区、水平扩展消费者 |
| 8 | **锁竞争瓶颈** | Thread Dump / Lock Contention | 锁等待时间长、线程阻塞 | 无锁数据结构、细粒度锁、乐观锁 |
| 9 | **GC瓶颈** | GC日志分析 | Full GC频繁、STW时间长 | 堆大小调优、减少对象分配、GC算法选择 |
| 10 | **连接池瓶颈** | Pool Utilization / Timeout | 连接获取超时、池满拒绝 | 池大小调整、连接泄漏检测、超时优化 |

**动态调优工作流：**

```
检测到性能异常
     │
     ▼
┌──────────────┐
│ 自动诊断引擎   │ ← 并行运行多种诊断探测器
│              │
│ 探测器列表:   │
│ ├─ CPU探针    │
│ ├─ 内存探针   │
│ ├─ DB探针     │
│ ├─ 缓存探针   │
│ └─ ...       │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ 根因定位      │ ← 综合各探针证据，确定主要瓶颈
│              │
│ 输出:        │
│ ├─ 瓶颈类型   │
│ ├─ 严重程度   │
│ ├─ 影响范围   │
│ └─ 证据链     │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ 优化方案生成  │ ← 基于知识库匹配历史成功方案
│              │
│ 方案候选:    │
│ ├─ 方案A(推荐): xxx  [置信度: 0.89]
│ ├─ 方案B(备选): xxx  [置信度: 0.72]
│ └─ 方案C(保守): xxx  [置信度: 0.65]
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ 安全应用      │ ← 灰度发布 → 观察效果 → 全量或回滚
└──────────────┘
```

**优化跟踪机制：**

| 跟踪项 | 记录内容 | 更新频率 |
|-------|---------|---------|
| 优化前基线 | 各项性能指标的快照 | 优化开始时 |
| 优化措施详情 | 具体做了什么改动 | 每次变更 |
| 效果对比数据 | 优化前后指标差值 | 优化完成后 |
| 副作用记录 | 是否引入新问题 | 持续观察 |
| ROI评估 | 收益/成本比 | 优化稳定后 |

##### 2.1.3 自修复引擎（Self-Repair Engine）

**职责**：自动问题检测-修复-验证循环

**12条内置修复规则：**

| 规则ID | 触发条件 | 修复动作 | 成功率目标 | 风险等级 |
|--------|---------|---------|-----------|---------|
| SR-001 | NPE堆栈出现在日志中 | 添加null guard / Optional包装 | 98% | LOW |
| SR-002 | 未关闭的资源(File/Stream/Connection) | 添加try-with-resources / finally块 | 97% | LOW |
| SR-003 | SQL拼接（非参数化查询） | 替换为PreparedStatement/ORM参数化 | 99% | MEDIUM |
| SR-004 | 硬编码密钥/密码 | 提取到配置/密钥管理服务 | 96% | HIGH |
| SR-005 | 同步阻塞调用在异步上下文中 | 包装为CompletableFuture / async-await | 92% | MEDIUM |
| SR-006 | 缺少超时设置的网络调用 | 添加合理的timeout配置 | 98% | LOW |
| SR-007 | 日志中打印敏感信息(PII) | 脱敏处理 / 移除敏感字段 | 99% | LOW |
| SR-008 | 未处理的Promise rejection / Future exception | 添加.catch() / 异常处理链 | 95% | LOW |
| SR-009 | 循环中的数据库N+1查询 | 批量查询替代循环查询 | 94% | MEDIUM |
| SR-010 | 过大的HTTP响应体未分页 | 添加分页参数 / 流式响应 | 93% | MEDIUM |
| SR-011 | 缺少CORS安全头配置 | 添加严格的CORS白名单 | 97% | HIGH |
| SR-012 | 弱加密算法使用(MD5/SHA1 for passwords) | 替换为BCrypt/Argon2/PBKDF2 | 99% | HIGH |

**自动修复-验证循环：**

```
┌─────────────────────────────────────────────────┐
│            自修复闭环 (Auto-Repair Loop)           │
│                                                  │
│  ① DETECT (检测)                                 │
│     ├── 静态扫描发现违规                          │
│     ├── 运行时异常捕获                            │
│     └── 日志模式匹配                              │
│     ↓                                            │
│  ② MATCH (匹配)                                  │
│     ├── 匹配到修复规则 SR-XXX                     │
│     ├── 评估置信度 (confidence ≥ 0.85 才执行)      │
│     └── 检查是否在允许的自修复范围内               │
│     ↓                                            │
│  ③ REPAIR (修复)                                │
│     ├── 应用修复变换                              │
│     ├── 生成修复diff                              │
│     └── 创建auto-repair分支                       │
│     ↓                                            │
│  ④ VERIFY (验证)                                │
│     ├── 运行相关单元测试                           │
│     ├── 运行受影响的集成测试                       │
│     └── 确认无回归                                │
│     ↓                                            │
│  ⑤ APPLY / ROLLBACK (应用或回滚)                 │
│     ├── 验证通过 → 合并修复                        │
│     └── 验证失败 → 自动回滚 + 上报人工             │
│     ↓                                            │
│  ⑥ LEARN (学习)                                 │
│     ├── 记录修复结果                              │
│     ├── 更新规则成功率统计                         │
│     └── 如失败 → 分析原因 → 改进规则               │
│     ↓                                            │
│  回到 ① (持续循环)                               │
└─────────────────────────────────────────────────┘
```

**成功率保障机制：**
- 每条规则的独立成功率跟踪（目标≥98%）
- 低成功率规则自动降级为"仅报告不修复"模式
- 所有修复操作保留完整审计日志
- 回滚脚本预生成，确保可在30秒内回滚

##### 2.1.4 自完善引擎（Self-Perfection Engine）

**职责**：从成功案例中学习，归纳最佳实践，识别反模式

**六大反模式类型识别：**

| 反模式类型 | 识别信号 | 典型表现 | 改进方向 |
|-----------|---------|---------|---------|
| **架构反模式** | 循环依赖、上帝类、 spaghetti code | 单点修改牵动全局 | 模块化解耦、分层重构 |
| **设计反模式** | God Object、Golden Hammer、Premature Optimization | 用错工具解决所有问题 | 设计评审、模式培训 |
| **编码反模式** | Magic Number、Copy-Paste Programming、Hard Code | 可读性差、维护困难 | 编码规范强制、Code Review加强 |
| **测试反模式** | The Inspector、Local Hero、Mockery | 测试形同虚设或过度Mock | 测试策略重新设计 |
| **DevOps反模式 | Deployment Roulette、Bypass Gateway | 发布混乱、环境不一致 | CI/CD标准化 |
| **管理反模式** | Bus Factor=1、Hero Culture、Analysis Paralysis | 知识孤岛、决策瘫痪 | 文档化、知识共享 |

**知识内化流程：**

```
成功案例收集
    │
    ▼
模式提取（什么是导致成功的关键因素？）
    │
    ▼
抽象归纳（提炼为可复用的方法论/ Checklist/模板）
    │
    ▼
验证检验（在小范围内试点验证有效性）
    │
    ▼
推广固化（写入规范/自动化工具/培训材料）
    │
    ▼
跨项目共享（同步到组织级知识库）
```

**跨项目知识共享格式：**

```yaml
knowledge_entry:
  id: "KNOW-20260406-001"
  title: "支付模块高并发场景下的幂等性设计模式"
  source_project: "skiller-payment-service"
  source_context: "解决双11期间重复扣款问题"
  pattern_category: "architecture"
  problem_statement: "在高并发场景下，网络超时导致的重复请求造成重复扣款"
  solution_summary: "采用分布式IDempotency Key + 状态机保证幂等"
  key_insights:
    - "Idempotency Key必须在业务逻辑之前生成和校验"
    - "状态机转换必须是原子的（DB事务或分布式锁）"
    - "客户端重试需要携带相同的Idempotency Key"
  applicable_scenarios:
    - "涉及资金操作的API"
    - "可能发生网络超时的长耗时操作"
    - "需要至少一次语义的消息处理"
  anti_patterns_to_avoid:
    - "不要在应用层做去重（存在竞态条件）"
    - "不要用数据库唯一约束作为唯一的幂等手段（不够灵活）"
  evidence:
    success_rate: "99.997%（100万次请求中仅3次需要人工介入）"
    performance_overhead: "< 1ms per request"
  adoption_projects: ["ecommerce-platform", "subscription-service"]
  created_at: "2026-04-06"
  tags: ["idempotency", "high-concurrency", "payment", "distributed-system"]
```

#### 2.2 三种演化模式动态切换

根据项目所处生命周期阶段和环境特征，自动选择最适合的演化模式：

| 模式 | 适用场景 | 变更频率 | 审批要求 | 风险容忍度 | 典型特征 |
|------|---------|---------|---------|-----------|---------|
| **aggressive（激进模式）** | 早期项目/MVP阶段/快速验证期 | 高（每日多次变更） | 仅自动化检查 | 高 | 快速试错、大量实验性变更、接受适度回滚 |
| **conservative（保守模式）** | 稳定生产系统/金融系统/监管严格行业 | 低（每周少量变更） | 多层审批+灰度 | 低 | 小步谨慎、充分验证、渐进推进 |
| **manual（手动模式）** | 关键基础设施/合规审计期/重大变更窗口 | 按需 | 人工逐一确认 | 极低 | 所有变更需人确认、详细记录、完整追溯 |

**模式切换判定规则：**

```yaml
mode_selection_rules:
  - condition: "project_age < 3 months AND team_size < 5"
    recommended_mode: "aggressive"
    reasoning: "早期项目应快速迭代，快速学习和调整"

  - condition: "slo_compliance_rate > 99.9% AND audit_mode = active"
    recommended_mode: "manual"
    reasoning: "高合规要求时期需要完全可控的变更流程"

  - condition: "production_incidents_last_month > 3 OR critical_bug_open > 0"
    recommended_mode: "conservative"
    reasoning: "近期不稳定时应采取保守策略，优先稳定"

  - condition: "default"
    recommended_mode: "conservative"
    reasoning: "默认采用保守模式以确保稳定性"
```

**模式切换流程：**

```
检测到模式切换条件
    │
    ▼
生成模式切换提案
    ├── 当前模式: conservative
    ├── 目标模式: aggressive
    ├── 切换理由: 项目进入MVP快速迭代期
    ├── 影响评估: 变更频率将从每周2次提升至每日5+次
    └── 风险评估: 回滚率可能从0.5%升至3%
    │
    ▼
[如 auto_switch_enabled = true]
    → 自动切换 + 记录切换事件
    │
    ↓ [否则]
通知负责人审批
    → 人工确认后切换
    │
    ▼
执行模式切换
    ├── 更新演化配置
    ├── 通知所有相关司
    └─ 进入新模式下的首次演化周期
```

### 阶段三：执行（Execute）

#### 3.1 DAG任务编排支持

复杂的演化任务通常包含多个有依赖关系的步骤，本司支持DAG（有向无环图）编排：

**DAG定义示例：**

```yaml
evolution_dag:
  dag_id: "monthly_evolution_cycle_2026_04"
  schedule: "0 2 1 * *"  # 每月1日凌晨2点
  tasks:
    - task_id: "health_assessment"
      type: "perceive"
      action: "run_full_health_check"
      timeout_minutes: 30

    - task_id: "opportunity_analysis"
      type: "decide"
      action: "analyze_opportunities"
      depends_on: ["health_assessment"]
      timeout_minutes: 20

    - task_id: "defect_prediction"
      type: "self_iteration"
      action: "predict_defect_hotspots"
      depends_on: ["health_assessment"]
      timeout_minutes: 15

    - task_id: "bottleneck_diagnosis"
      type: "self_optimization"
      action: "diagnose_performance_bottlenecks"
      depends_on: ["health_assessment"]
      timeout_minutes: 25

    - task_id: "auto_repair_scan"
      type: "self_repair"
      action: "scan_and_repair_safe_issues"
      depends_on: ["health_assessment"]
      timeout_minutes: 45

    - task_id: "plan_generation"
      type: "decide"
      action: "generate_improvement_plan"
      depends_on: ["opportunity_analysis", "defect_prediction", "bottleneck_diagnosis"]
      timeout_minutes: 15

    - task_id: "knowledge_sync"
      type: "self_perfection"
      action: "sync_knowledge_across_projects"
      depends_on: ["auto_repair_scan"]
      timeout_minutes: 20

    - task_id: "report_generation"
      type: "record"
      action: "generate_evolution_report"
      depends_on: ["plan_generation", "knowledge_sync"]
      timeout_minutes: 10
```

**DAG执行引擎特性：**
- 并行执行无依赖关系的任务以缩短总时长
- 任务级别的超时控制和失败重试
- 失败任务的隔离（不影响其他独立任务）
- 执行过程的可视化展示
- 支持手动触发和暂停/恢复

#### 3.2 演化行动执行规范

每项演化行动遵循统一执行协议：

```bash
# 执行单次演化行动
autonomous-evolve execute \
  --plan-id="EVOL-ITER-20260406-001" \
  --action-id="A1" \
  --mode="conservative" \
  --dry-run=false \
  --rollback-script="auto"

# 执行完整DAG
autonomous-evolve run-dag \
  --dag-id="monthly_evolution_cycle_2026_04" \
  --async=true \
  --notification="slack:#evolution-updates"
```

**执行过程状态机：**

```
pending → scheduled → running → verifying → completed
                  ↘                ↗
                   → failed → retrying → ...
                                     ↘
                                      → rolled_back
                                     ↗
                    → cancelled (manual)
```

### 阶段四：Verify

#### 4.1 演化效果验证

| 验证维度 | 验证方法 | 通过标准 |
|---------|---------|---------|
| **健康度改善** | 重跑健康度评估 | 综合评分提升 ≥ 预设目标 |
| **预测准确率** | 对比预测与实际结果 | 准确率 ≥ 80% |
| **优化效果** | 性能基准对比 | 关键指标达到预期改善幅度 |
| **修复成功率** | 自修复统计数据 | 成功率 ≥ 98% |
| **知识产出质量** | 知识条目被引用次数 | 月均引用 ≥ 3次 |
| **副作用检测** | 全面回归测试 | 0个新引入问题 |
| **资源消耗合理性** | CPU/内存/时间开销 | 在预算范围内 |

#### 4.2 模式有效性验证

定期（每季度）评估已固化的模式和最佳实践是否仍然有效：

| 评估项 | 方法 | 决策 |
|-------|------|------|
| 模式是否仍适用 | 检查最近3个月的应用案例 | 如无新应用→标记为待复审 |
| 模式是否有更好替代 | 搜索新的技术方案 | 发现更优方案→更新或替换 |
| 模式是否被滥用 | 检查误用案例 | 滥用率高→加强培训和约束 |
| 模式文档是否过时 | 对照最新实践更新 | 内容陈旧→刷新文档 |

### 阶段五：Record

#### 5.1 演化日志与状态持久化

所有演化活动记录到持久化存储中：

**日志存储结构：**

```
.evolution/
├── logs/
│   ├── 2026/
│   │   ├── 04/
│   │   │   ├── daily/
│   │   │   │   ├── 2026-04-01.json
│   │   │   │   ├── 2026-04-02.json
│   │   │   │   └── ...
│   │   │   └── weekly/
│   │   │       ├── 2026-W14.json
│   │   │       └── ...
│   │   └── ...
├── state/
│   ├── current_mode.json          # 当前演化模式
│   ├── health_baseline.json       # 健康度基线
│   ├── active_plans.json          # 进行中的计划
│   └── metrics_history.json       # 历史指标数据
├── knowledge/
│   ├── patterns/                  # 已验证的模式库
│   ├── anti_patterns/             # 反模式库
│   ├── lessons_learned/           # 经验教训
│   └── cross_project/             # 跨项目共享知识
└── reports/
    ├── monthly/
    │   └── 2026-04.md
    └── quarterly/
        └── 2026-Q1.md
```

**单日日志示例：**

```json
{
  "date": "2026-04-06",
  "mode": "conservative",
  "summary": {
    "total_actions_initiated": 12,
    "actions_completed": 11,
    "actions_failed": 1,
    "actions_rolled_back": 0,
    "total_time_spent_minutes": 145
  },
  "by_engine": {
    "self_iteration": {"initiated": 3, "completed": 3},
    "self_optimization": {"initiated": 2, "completed": 2},
    "self_repair": {"initiated": 5, "completed": 4, "failed": 1},
    "self_perfection": {"initiated": 2, "completed": 2}
  },
  "health_score_change": {
    "before": 76.5,
    "after": 78.2,
    "delta": "+1.7"
  },
  "notable_events": [
    {
      "type": "repair_failed",
      "rule": "SR-005",
      "reason": "async context detection false positive",
      "action_taken": "rolled back and escalated to human review"
    }
  ]
}
```

#### 5.2 存储持久化要求

- 所有演化状态数据必须持久化到版本控制系统中（而非仅本地文件）
- 状态文件的变更遵循常规Git流程
- 关键状态变更需要有commit message说明原因
- 支持从任意历史时间点恢复状态（用于调试和审计）

## 典型自主场景

### 场景1：月度自主演化周期

**触发条件**：每月定时触发的全量演化周期

**自主执行流程（DAG编排）：**

```
T+00min  [感知] 全量健康度检查启动
         → 采集8大维度的最新数据
         → 与上月基线对比

T+30min  [决策] 机会分析 + 预测 + 诊断 并行执行
         → 自迭代引擎：预测下月高风险模块（Top 5）
         → 自优化引擎：诊断当前性能瓶颈（发现DB慢查询问题）
         → 自修复引擎：扫描并修复安全问题（修复3处硬编码密码）

T+55min  [决策] 生成综合改进计划
         → 整合各引擎输出
         → 排定优先级和排期
         → 分配给对应的责任司

T+70min  [完善] 跨项目知识同步
         → 将本月新发现的模式推送到组织知识库
         → 拉取其他项目的有用知识

T+80min  [记录] 生成月度演化报告
         → 健康度趋势图表
         → 各引擎KPI汇总
         → 下月重点建议

总耗时：约80分钟（全自动执行）
```

**输出物：**
- 月度健康度报告（含趋势图）
- 下月改进计划（含具体Action Items）
- 知识库更新记录
- 各引擎运行效率统计

### 场景2：激进模式下的大量快速实验

**触发条件**：新项目启动初期，设置为aggressive模式

**自主执行流程：**

1. **感知**：高频扫描（每2小时一次），快速发现问题
2. **决策**：低门槛启动优化尝试，允许较高失败率（目标回滚率<5%）
3. **执行**：并行执行多个小型实验性变更
4. **验证**：每个变更独立验证，失败的立即回滚
5. **记录**：大量积累实验数据，快速收敛有效方案

**典型一天的活动：**
```
09:00  实验1: 引入新的缓存策略 → ✅ 成功，P95延迟降15%
10:00  实验2: 尝试新的日志聚合方案 → ❌ 失败，回滚（内存占用过高）
11:00  实验3: API网关路由优化 → ✅ 成功，吞吐量升20%
14:00  实验4: 数据库连接池调参 → ⚠️ 部分成功，需进一步微调
15:00  实验5: 引入新的监控仪表盘 → ✅ 成功
16:00  汇总当日实验结果 → 4成功/1失败 → 成功率80%
```

### 场景3：自修复引擎的日常值守

**触发条件**：持续运行的修复守护进程

**自主执行流程（24小时不间断）：**

```
每30分钟循环：
  ① 扫描代码仓库的最新变更
  ② 匹配12条修复规则
  ③ 发现可自动修复的问题？
     ├─ 是 → 进入修复循环
     │   ├─ 生成修复方案
     │   ├─ 自动验证（测试）
     │   ├─ 验证通过 → 自动合并
     │   └─ 验证失败 → 回滚 + 告警
     └─ 否 → 等待下一轮

典型一天的修复成果：
  - 修复SR-001(NPE防护): 5处
  - 修复SR-006(超时设置): 3处
  - 修复SR-007(日志脱敏): 2处
  - 修复SR-003(SQL参数化): 1处
  总计: 11处自动修复，全部成功，0回滚
```

## 决策框架

### 演化行动准入判断

```
是否启动某项演化行动？
    │
    ├─ 有明确的度量依据吗？（不是凭感觉）
    │   └─ 否 → 补充数据采集
    │
    ├─ 预期收益可量化吗？
    │   └─ 否 → 先定义成功标准
    │
    ├─ 在当前演化模式下允许吗？
    │   └─ 否 → 申请模式切换或升级审批
    │
    ├─ 有足够的回滚预案吗？
    │   └─ 否 → 先准备回滚方案
    │
    └─ 全部通过 → 🟢 准许执行
```

### 演化中止条件

| 中止条件 | 触发动作 |
|---------|---------|
| 系统健康度连续下降超过10% | 暂停所有主动演化，转为观察模式 |
| 自修复成功率低于90%（24h滑动窗口） | 暂停自修复，转人工审查所有修复建议 |
| 生产环境发生P0级事故 | 立即冻结所有演化活动 |
| 演化预算（时间/资源）耗尽 | 暂停非关键演化行动 |
| 人工发出停止指令 | 立即停止 |

### 自主权限边界

| 操作类型 | aggressive模式 | conservative模式 | manual模式 |
|---------|---------------|-----------------|-----------|
| LOW风险自修复 | ✅ 自主执行 | ✅ 自主执行 | 需确认 |
| MEDIUM风险自修复 | ✅ 自动执行 | 需确认 | 需确认 |
| HIGH风险自修复 | 需确认 | 需确认 | 需确认 |
| 性能参数调优 | ✅ 自主（灰度） | 需审批 | 需确认 |
| 模式切换 | ✅ 自主 | 需审批 | 需确认 |
| 知识库写入 | ✅ 自主 | ✅ 自主 | 需确认 |
| 跨项目知识推送 | 需确认 | 需确认 | 需确认 |
| 删除生产数据 | 🚫 禁止 | 🚫 禁止 | 🚫 禁止 |
| 修改安全策略 | 需Security Team | 需Security Team | 需Security Team |

## 安全与治理

### 演化安全红线

1. **生产安全第一**：任何演化行动不得降低生产环境的可用性和安全性
2. **数据保护**：演化过程中不得访问、修改或泄露用户数据和敏感信息
3. **变更可追溯**：每一次演化操作都必须有完整的审计轨迹
4. **预算控制**：演化活动的资源消耗（计算时间、API调用等）必须在预设限额内
5. **隔离执行**：演化操作应在隔离环境中先验证，再应用到生产相关环境

### 隐私与伦理

- 演化分析过程中收集的代码度量数据不包含个人身份信息
- 知识共享时注意去除项目特定的敏感信息
- 不利用演化能力进行未经授权的代码修改
- AI辅助决策的过程保持透明，可解释

### 合规要求

- 演化活动符合组织的变更管理政策
- 自动生成的代码变更符合编码规范和安全标准
- 跨项目知识共享遵守知识产权和数据保密协议

## 协作关系

### 刑部内部协作

| 协作司 | 协作场景 | 协作协议 |
|-------|---------|---------|
| **bug_fixing_si（缺陷修复司）** | 提供缺陷趋势数据作为自迭代引擎的输入；接收缺陷预测结果指导预防工作 | 双向数据流：缺陷数据 ↔ 预防建议 |
| **refactoring_si（重构优化司）** | 提供代码质量度量；接收架构优化指令；共享技术债务数据 | 质量 ↔ 优化指令 |
| **version_control_si（版本管理司）** | 演化变更的版本管理和发布协调；提供提交分析数据 | 版本管理服务 |

### 跨部门协作

| 协作方 | 协作场景 | 接口定义 |
|-------|---------|---------|
| **户部（产品司）** | 演化方向的业务价值对齐；产品路线图影响评估 | 定期演化汇报 |
| **工部（工程司）** | 大规模演化行动的资源协调；工程能力建设 | 演化计划 ↔ 工程资源 |
| **礼部（QA司）** | 测试策略协同；质量门禁共建 | 质量数据互通 |
| **兵部（运维司）** | 性能优化实施配合；监控指标对接 | 运维 ↔ 演化联动 |

### 信息流向图

```
┌──────────────────────────────────────────────────────┐
│                    自演化司 (中枢大脑)                  │
│                                                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌─────────┐ │
│  │ 自迭代    │ │ 自优化    │ │ 自修复    │ │ 自完善   │ │
│  │ Engine   │ │ Engine   │ │ Engine   │ │ Engine  │ │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬────┘ │
│       │           │           │           │        │
│       └───────────┴─────┬─────┴───────────┘        │
│                         │                           │
│              ┌──────────▼──────────┐                │
│              │  DAG编排 & 模式切换   │                │
│              └──────────┬──────────┘                │
│                         │                           │
└─────────────────────────┼───────────────────────────┘
                          │
            ┌─────────────┼─────────────┐
            ▼             ▼             ▼
      [缺陷修复司]   [重构优化司]   [版本管理司]
            │             │             │
            ▼             ▼             ▼
      [更好的代码质量] ←────────────────┘
            │
            ▼
      [持续进化的系统]
```

---

## 🤝 v5.1 增强：Agency Agent 协作指南

### 可调用的 Agency Agents

| Agent 名称 | 所属部门 | 协作模式 | 适用场景 |
|-----------|---------|---------|---------|
| Autonomous Optimization Architect | Strategy Division | 策略→执行 | 全局优化策略制定、多目标优化权衡、演化路线图规划 |
| Automation Governance Architect | Governance Division | 治理→合规 | 自动化操作治理框架、权限边界定义、审计合规保障 |

### Agent 协作工作流

1. **策略制定阶段**：Autonomous Optimization Architect 基于本司的健康度数据制定全局优化策略，平衡代码质量/性能/安全性/成本等多维目标
2. **治理框架阶段**：Automation Governance Architect 定义自演化的操作边界和安全护栏，确保自主操作不越界
3. **执行监控阶段**：两个 Agent 持续监控演化活动的合规性和效果，实时调整策略参数
4. **复盘迭代阶段**：每个演化周期结束后，三方共同评审产出效果并调整下一周期策略

### 典型协作场景

- **场景一：系统级优化策略制定** — 本司输出月度健康度报告 → Autonomous Optimization Architect 制定多目标优化策略（如：牺牲3%性能换取20%代码复杂度下降）→ Automation Governance Architect 评估策略风险并设置执行护栏 → 三方共同签署执行计划
- **场景二：自动化操作治理框架建立** — Automation Governance Architect 设计自主操作的权限矩阵和审批流程 → 本司将治理规则嵌入自修复引擎的置信度判断逻辑 → Autonomous Optimization Architect 确保治理约束不影响优化效果
- **场景三：SLO 驱动的演化方向校准** — 本司检测到 SLO 趋势恶化 → Autonomous Optimization Architect 重新分配四大引擎的资源配比 → Automation Governance Architect 审核调整后的操作风险 → 输出修正后的演化策略

---

## 🏗️ v5.1 增强：Harness 工程实践

### 相关 Harness 模块

- **Service Reliability Engineering (SRE) — SLO-Driven Evolution**：SLO 达成率数据作为自演化引擎的核心输入，驱动优化方向的动态调整
- **Chaos Engineering — Adaptive Chaos**：Chaos 实验结果反馈给自演化引擎，自适应地调整系统的韧性策略
- **Service Reliability — Error Budget Consumption Tracking**：Error Budget 消耗速率影响演化模式的激进程度选择

### 实践指南

1. **SLO 驱动的演化方向指引**：将 Harness SRE 中的 SLO 数据（Availability/Latency/Quality）接入本司的自迭代引擎作为核心输入维度。当 SLO 达成率 > 99.9% 时，演化模式倾向 `aggressive`（大胆尝试新方案）；当 SLO 达成率 < 99% 时，自动切换至 `conservative` 模式（聚焦稳定性恢复）。SLO 趋势变化是模式切换的首要触发信号。
2. **Chaos 实验反馈自适应**：每次 Harness Chaos Engineering 实验结束后，实验结果（故障检测时间MTTD、平均恢复时间MTTR、cascading failure 发生率）自动回传给本司的自优化引擎。如果某类混沌实验反复暴露相同弱点（如 DB 连接池耗尽），自优化引擎自动调高该方向的优化优先级，并在下一个演化周期中针对性加强。
3. **Error Budget 驱动的模式选择**：Harness SRE 的 Error Budget 剩余量直接映射为本司的演化模式选择依据。Budget 充裕（>70%）→ `aggressive` 模式，鼓励探索性优化；Budget 中等（30%-70%）→ `conservative` 模式，聚焦债务清理；Budget 紧张（<30%）→ `manual` 模式，仅允许安全修复。此映射关系写入模式切换判定规则的最高优先级。

---

## 🆕 v6.0 增强能力集成

### MARC资源协调器集成指南

本司在多Agent并发场景下的资源协调要求：

#### 资源锁机制
- **文件写锁**：当本司需要修改优化配置、演化策略、安全规则时，必须通过MARC申请互斥锁
  ```python
  # 示例：申请文件写锁
  from skillscripts.resource_coordinator import LockManager, LockType
  lock_mgr = LockManager()
  lock_id = lock_mgr.acquire_lock(
      resource_id="path/to/config/security-rules.yaml",
      agent_id="安全加固司",
      lock_type=LockType.EXCLUSIVE,
      priority=10,
      timeout=180.0
  )
  ```
- **读锁**：读取SLO指标、Chaos实验结果、安全扫描报告时申请读锁（高频监控场景）
- **释放锁**：优化和安全加固操作完成后立即释放锁，避免阻塞其他司的状态查询

#### 终端会话池使用
- 从MARC终端会话_pool获取会话执行安全扫描命令、性能基准测试、Chaos实验触发
- 会话使用完毕后及时归还池中
- 单个命令超时设置为300秒（安全扫描和Chaos实验可能耗时较长）

#### 并发安全注意事项
- 安全规则和优化策略是全局共享资产，写入时必须独占锁保护
- 自适应演化引擎的状态变更需原子性操作，避免出现不一致的中间状态
- 死锁预防：按固定顺序申请锁（先锁安全规则→再锁优化配置→最后锁演化策略）

### 四维度输出防线集成

| 防线层级 | 本司检查重点 | 自动化程度 |
|---------|-------------|----------|
| **提示词工程层** | 安全加固提示词、性能优化提示词、自适应策略提示词 | 半自动（AI辅助） |
| **能力约束层** | 仅允许优化和安全操作（加固/调优/演化），禁止修改业务逻辑 | 全自动 |
| **规则校验层** | 输出格式：YAML安全规则、JSON优化参数、Markdown演化报告 | 全自动 |
| **兜底恢复层** | 优化导致SLO退化时自动回滚至上一个稳定配置 | 半自动 |

### 操作优先级指引（v6.0核心）

本司推荐的操作方式：

1. 🥇 **Agent自主手动操作**（强烈推荐用于安全加固、性能调优、策略制定）
   - 示例：直接编辑安全规则YAML、手动调整优化参数、编写加固方案
   - 优势：精确控制安全和性能细节、可逐步验证有效性、可随时回滚策略变更

2. 🥈 **规划脚本操作**（适用于自动化安全扫描、周期性性能基准对比）
   - 推荐脚本：
     - `skillscripts/resource_coordinator/quota_manager.py` — 检查安全和优化资源配额
     - `skillscripts/open_source_philosophy/clawcode_sdd_tdd_engine.py` — SDD/TDD驱动的安全实践
     - `skillscripts/platform/powershell_adapter.py` — PS7环境适配

3. 🥉 **命令操作**（仅限安全漏洞紧急修补、生产环境性能调优等极少数场景）
   - ⚠️ 必须预演影响范围（安全和性能变更直接影响系统稳定性）
   - ⚠️ 生产环境操作需获得Security/SRE团队审批
   - 推荐使用PS7适配器转换trivy/snyk/bandit等安全扫描工具命令

### PowerShell 7 执行指南

本司相关操作的PS7适配要点:
- 安全扫描：trivy / snyk test / bandit -r / npm audit 等命令原生可用
- 性能分析：自定义Python/Go脚本用于性能基准采集和分析
- Chaos实验：通过Harness CLI或API触发混沌实验
- 编码：确保所有输出 UTF-8 无 BOM（安全报告和优化建议）

### 与其他司的协作接口

- 上游依赖：Bug修复司（接收漏洞信息用于安全加固）、基础设施司（获取部署拓扑用于韧性优化）
- 下游输出：依赖管理司（推送安全版本升级要求）、协同调度司（报告系统健康度和风险预警）
- 数据交换格式：YAML / JSON / Markdown / CSV（统一UTF-8无BOM）
