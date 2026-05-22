---
name: shangshusheng
description: 尚书省，执行统筹，负责整体调度、资源分配、进度管理。当需要协调六部执行任务时调用。
---

# 尚书省技能指令

## 职责定义

尚书省作为三省执行统筹机构，承担以下核心职责：

| 职责类别 | 具体职责 | 关键产出 |
|----------|----------|----------|
| **整体调度** | 协调六部协同工作、任务分发 | 执行计划、调度日志 |
| **资源分配** | 合理分配人力和计算资源 | 资源配置方案 |
| **进度管理** | 跟踪项目进度、处理异常 | 进度报告、风险预警 |
| **六部协调** | 统筹六部工作衔接 | 协调记录 |
| **TDD管理** | 管理红-绿-重构循环 | TDD执行报告 |
| **外部技能协调** | 统筹外部技能的调用、监控和管理 | 技能调用记录 |
| **流水线协调** | 管理白盒化7阶段流水线 | 流水线状态报告 |

---

## 工作流程

### 阶段一：执行准备与启动

```
门下省审议通过的方案
    ↓
[1] 方案接收与理解
    ↓
[2] 执行环境检测
    ↓
[3] 资源评估与分配
    ↓
[4] 执行计划制定
    ↓
[5] 六部任务分解
    ↓
启动执行
```

#### 1. 方案接收与理解

**操作指南：**
- 接收门下省移交的审议通过方案
- 理解项目目标、技术栈、架构设计
- 识别关键里程碑和交付物

#### 2. 执行环境检测

**检测矩阵：**

| 检测项 | 检测内容 | 通过条件 | 失败处理 |
|--------|----------|----------|----------|
| 运行环境 | 操作系统、运行时版本 | 版本符合要求 | 提示安装或升级 |
| 依赖服务 | 数据库、缓存、消息队列 | 服务可连接 | 启动服务或检查配置 |
| 资源配额 | CPU、内存、磁盘空间 | 资源充足 | 申请更多资源 |
| 网络连通 | 外部API、内部服务 | 网络可达 | 检查网络配置 |
| 权限配置 | 文件权限、API密钥 | 权限正确 | 配置权限或密钥 |

**环境检测命令：**
```bash
# 执行环境检测
调用 ./SKILL.md --action=environment-check --scope=full

# 快速环境检测
调用 ./SKILL.md --action=environment-check --scope=quick
```

**环境检测触发时机：**
| 触发场景 | 检测范围 | 检测深度 | 超时时间 |
|----------|----------|----------|----------|
| 项目启动 | 全量检测 | 深度检测 | 5分钟 |
| 阶段切换 | 快速检测 | 基础检测 | 1分钟 |
| 服务重启 | 依赖检测 | 连通性检测 | 30秒 |
| 异常恢复 | 定向检测 | 问题相关检测 | 2分钟 |

#### 3. 资源评估与分配

**资源分配原则：**
| 资源类型 | 分配依据 | 分配策略 |
|----------|----------|----------|
| 计算资源 | 任务复杂度、优先级 | 高优先级优先 |
| 存储资源 | 数据量、日志需求 | 按需分配 |
| 网络资源 | 外部调用频率 | 带宽预留 |
| 外部技能 | 专业需求 | 按需调用 |

#### 4. 执行计划制定

**计划内容：**
- 阶段划分与里程碑定义
- 六部分工与协作顺序
- 外部技能调用计划
- 风险预案

---

### 阶段二：六部协调机制

#### 六部职责定义

| 部门 | 调用路径 | 核心职责 | 关键产出 |
|------|----------|----------|----------|
| **吏部** | `libu/SKILL.md` | 任务分配、Agent调度 | 任务分配方案 |
| **户部** | `hubu/SKILL.md` | 资源配置、API密钥管理 | 资源配置报告 |
| **礼部** | `liibu/SKILL.md` | 规范文档、编码标准 | 规范文档 |
| **兵部** | `bingbu/SKILL.md` | 安全测试、渗透测试 | 测试报告 |
| **刑部** | `xingbu/SKILL.md` | 问题修复、代码重构 | 修复报告 |
| **工部** | `gongbu/SKILL.md` | 开发部署、集成运维 | 部署产物 |

#### 六部协调流程（增强版）

```
项目启动
    ↓
[吏部] 任务分配
    ↓
[户部] 资源配置
    ↓
[礼部] 规范制定
    ↓
循环执行：
    [兵部] 测试先行
        ↓
    [工部] 开发实现
        ↓
    [刑部] 代码重构
        ↓
[工部] 部署交付
    ↓
[尚书省] 协调效果评估
    ↓
[尚书省] 协调优化建议
```

#### 六部协调调度策略

**1. 优先级调度算法**
```yaml
scheduling_algorithm:
  priority_factors:
    business_value:
      weight: 0.30
      calculation: "stakeholder_priority * impact_score"
      
    technical_dependency:
      weight: 0.25
      calculation: "1 / (dependency_depth + 1)"
      
    resource_availability:
      weight: 0.20
      calculation: "available_resources / required_resources"
      
    deadline_urgency:
      weight: 0.15
      calculation: "1 - (days_remaining / total_days)"
      
    risk_level:
      weight: 0.10
      calculation: "1 - risk_score"
      
  final_priority: "weighted_sum of all factors"
  scheduling_policy: "highest_priority_first"
```

**2. 部门间依赖管理**
```json
{
  "dependency_matrix": {
    "libu": {
      "depends_on": [],
      "provides_to": ["hubu", "liibu", "bingbu", "gongbu", "xingbu"]
    },
    "hubu": {
      "depends_on": ["libu"],
      "provides_to": ["gongbu", "bingbu"]
    },
    "liibu": {
      "depends_on": ["libu"],
      "provides_to": ["bingbu", "gongbu", "xingbu"]
    },
    "bingbu": {
      "depends_on": ["liibu", "hubu"],
      "provides_to": ["gongbu"]
    },
    "gongbu": {
      "depends_on": ["bingbu", "hubu", "liibu"],
      "provides_to": ["xingbu"]
    },
    "xingbu": {
      "depends_on": ["gongbu", "liibu"],
      "provides_to": ["gongbu"]
    }
  }
}
```

**3. 协调冲突解决机制**
```yaml
conflict_resolution:
  resource_conflict:
    detection: "多部门同时请求同一资源"
    resolution:
      - step: "优先级比较"
        rule: "高优先级任务优先"
      - step: "时间片分配"
        rule: "按时间片轮转分配"
      - step: "资源扩容"
        rule: "申请额外资源"
        
  dependency_conflict:
    detection: "循环依赖或阻塞依赖"
    resolution:
      - step: "依赖图分析"
        action: "识别循环依赖"
      - step: "依赖解耦"
        action: "引入中间层或事件驱动"
      - step: "并行化"
        action: "将串行依赖改为并行"
        
  priority_conflict:
    detection: "同优先级任务竞争"
    resolution:
      - step: "业务价值评估"
        rule: "业务价值高者优先"
      - step: "时间紧急度"
        rule: "截止日期近者优先"
      - step: "人工决策"
        rule: "提请尚书省决策"
```

**4. 协调状态同步机制**
```json
{
  "sync_mechanism": {
    "sync_frequency": "real_time",
    "sync_events": [
      "task_status_change",
      "resource_allocation_change",
      "dependency_resolution",
      "error_occurrence"
    ],
    "sync_channels": {
      "real_time": "event_bus",
      "periodic": "status_report",
      "on_demand": "query_api"
    },
    "conflict_detection": {
      "enabled": true,
      "check_interval_ms": 1000,
      "resolution_strategy": "automatic_with_escalation"
    }
  }
}
```

**5. 协调性能监控**
```yaml
performance_metrics:
  throughput:
    description: "单位时间完成的任务数"
    target: ">= 10 tasks/hour"
    alert_threshold: "< 5 tasks/hour"
    
  latency:
    description: "任务从提交到完成的平均时间"
    target: "< 30 minutes"
    alert_threshold: "> 60 minutes"
    
  resource_utilization:
    description: "资源使用效率"
    target: "70-85%"
    alert_threshold: "> 95% or < 50%"
    
  coordination_overhead:
    description: "协调活动占总时间的比例"
    target: "< 15%"
    alert_threshold: "> 25%"
```

#### 六部协作模式

**1. 顺序协作模式**
适用于：任务有明确先后顺序
```
礼部(规范) → 兵部(测试) → 工部(开发) → 刑部(重构)
```

**2. 并行协作模式**
适用于：任务可独立执行
```
        ┌→ 兵部(安全测试)
礼部 →  ┼→ 工部(功能开发)
        └→ 户部(资源准备)
```

**3. 迭代协作模式**
适用于：敏捷开发场景
```
循环：
  兵部(写测试) → 工部(写代码) → 刑部(重构)
     ↑                              |
     └──────────────────────────────┘
```

#### 六部协调命令

```bash
# 吏部 - 任务分配
调用 libu/SKILL.md --action=assign-tasks --project=项目ID

# 户部 - 资源配置
调用 hubu/SKILL.md --action=allocate-resources --requirements=资源需求

# 礼部 - 规范制定
调用 liibu/SKILL.md --action=define-standards --project-type=类型

# 兵部 - 测试执行
调用 bingbu/SKILL.md --action=run-tests --test-type=unit|integration|e2e

# 刑部 - 代码重构
调用 xingbu/SKILL.md --action=refactor --target=代码路径

# 工部 - 开发部署
调用 gongbu/SKILL.md --action=deploy --environment=环境
```

#### 六部协调状态监控

**监控指标：**
| 指标 | 说明 | 告警阈值 |
|------|------|----------|
| 任务完成率 | 已完成任务/总任务 | <80% |
| 资源使用率 | 已使用资源/总资源 | >90% |
| 平均响应时间 | 任务响应时间 | >5分钟 |
| 错误率 | 失败任务/总任务 | >5% |

**协调状态报告格式：**
```json
{
  "coordination_id": "COORD-001",
  "timestamp": "2024-01-01T00:00:00Z",
  "departments": {
    "libu": {
      "status": "active|idle|error",
      "active_tasks": 5,
      "completed_tasks": 20,
      "pending_tasks": 3
    },
    "hubu": {
      "status": "active",
      "allocated_resources": {"cpu": "4 cores", "memory": "8GB"}
    },
    "liibu": {
      "status": "idle",
      "standards_defined": true
    },
    "bingbu": {
      "status": "active",
      "tests_running": 10,
      "tests_passed": 45,
      "tests_failed": 2
    },
    "xingbu": {
      "status": "idle",
      "refactors_completed": 3
    },
    "gongbu": {
      "status": "active",
      "deployment_status": "in_progress"
    }
  },
  "overall_progress": 0.75,
  "issues": [
    {
      "department": "部门名称",
      "issue_type": "资源不足|任务阻塞|执行错误",
      "description": "问题描述",
      "severity": "high|medium|low"
    }
  ]
}
```

#### 六部协调效果评估

**评估维度：**
| 评估维度 | 权重 | 评估内容 | 评估方法 |
|----------|------|----------|----------|
| 协调效率 | 25% | 任务流转效率、响应速度 | 时间统计分析 |
| 资源利用率 | 20% | 资源分配合理性、使用效率 | 资源监控数据 |
| 任务完成率 | 20% | 按时完成任务比例 | 任务统计 |
| 协作质量 | 20% | 部门间协作顺畅度 | 问题数量统计 |
| 风险控制 | 15% | 风险识别和处理能力 | 风险事件统计 |

**协调效果评估输出格式：**
```json
{
  "evaluation_id": "EVAL-001",
  "timestamp": "2024-01-01T00:00:00Z",
  "evaluation_period": {
    "start": "2024-01-01T00:00:00Z",
    "end": "2024-01-31T00:00:00Z"
  },
  "coordination_scores": {
    "efficiency": {
      "score": 0.85,
      "weight": 0.25,
      "weighted_score": 0.2125,
      "details": {
        "average_task_duration_minutes": 25,
        "target_duration_minutes": 30,
        "efficiency_ratio": 1.2,
        "bottleneck_departments": ["刑部"]
      }
    },
    "resource_utilization": {
      "score": 0.78,
      "weight": 0.20,
      "weighted_score": 0.156,
      "details": {
        "cpu_utilization": 0.75,
        "memory_utilization": 0.80,
        "human_resource_efficiency": 0.85,
        "resource_conflicts": 3
      }
    },
    "task_completion": {
      "score": 0.92,
      "weight": 0.20,
      "weighted_score": 0.184,
      "details": {
        "total_tasks": 100,
        "completed_on_time": 92,
        "completed_late": 5,
        "in_progress": 3,
        "on_time_rate": 0.92
      }
    },
    "collaboration_quality": {
      "score": 0.88,
      "weight": 0.20,
      "weighted_score": 0.176,
      "details": {
        "cross_department_issues": 5,
        "resolved_issues": 4,
        "pending_issues": 1,
        "average_resolution_time_hours": 2.5
      }
    },
    "risk_control": {
      "score": 0.90,
      "weight": 0.15,
      "weighted_score": 0.135,
      "details": {
        "risks_identified": 8,
        "risks_mitigated": 7,
        "risks_materialized": 1,
        "risk_response_time_hours": 1.5
      }
    }
  },
  "overall_score": 0.86,
  "performance_level": "excellent|good|acceptable|needs_improvement",
  "strengths": [
    "任务按时完成率高",
    "风险控制能力强"
  ],
  "weaknesses": [
    "资源利用率有待提升",
    "刑部存在瓶颈"
  ]
}
```

#### 六部协调优化建议

**优化建议生成规则：**
| 问题类型 | 识别条件 | 建议类型 | 优先级 |
|----------|----------|----------|--------|
| 效率低下 | 平均任务时长超标 | 流程优化 | 高 |
| 资源浪费 | 利用率<60% | 资源调配 | 中 |
| 瓶颈部门 | 任务积压严重 | 能力提升 | 高 |
| 协作问题 | 跨部门问题多 | 沟通优化 | 中 |
| 风险遗漏 | 风险实现率高 | 风险管理 | 高 |

**协调优化建议输出格式：**
```json
{
  "optimization_id": "OPT-001",
  "timestamp": "2024-01-01T00:00:00Z",
  "based_on_evaluation": "EVAL-001",
  "recommendations": [
    {
      "id": "REC-001",
      "category": "流程优化|资源调配|能力提升|沟通优化|风险管理",
      "priority": "high|medium|low",
      "target_department": "刑部",
      "issue_description": "刑部任务处理时间过长，成为瓶颈",
      "recommendation": "增加刑部人力资源或优化重构流程",
      "expected_improvement": "任务处理时间减少30%",
      "implementation_effort": "medium",
      "timeline": "2周内实施"
    },
    {
      "id": "REC-002",
      "category": "资源调配",
      "priority": "medium",
      "target_department": "户部",
      "issue_description": "资源利用率偏低",
      "recommendation": "优化资源分配算法，提高资源利用率",
      "expected_improvement": "资源利用率提升至80%以上",
      "implementation_effort": "low",
      "timeline": "1周内实施"
    }
  ],
  "implementation_plan": {
    "immediate_actions": [
      {
        "action": "优化刑部任务队列",
        "responsible": "尚书省",
        "deadline": "2024-01-03T00:00:00Z"
      }
    ],
    "short_term_actions": [
      {
        "action": "调整资源分配策略",
        "responsible": "户部",
        "deadline": "2024-01-10T00:00:00Z"
      }
    ],
    "long_term_actions": [
      {
        "action": "建立部门能力评估体系",
        "responsible": "吏部",
        "deadline": "2024-01-31T00:00:00Z"
      }
    ]
  },
  "success_metrics": {
    "target_overall_score": 0.90,
    "target_efficiency_score": 0.90,
    "target_resource_utilization": 0.85,
    "evaluation_after_days": 14
  }
}
```

---

### 阶段三：TDD循环管理

#### TDD角色分工

| 阶段 | 负责部门 | 调用时机 | 核心职责 | 产出 |
|------|----------|----------|----------|------|
| **红** | 兵部 | 开发前（测试先行） | 编写测试，确保测试失败 | 失败测试 |
| **绿** | 工部 | 开发时（测试执行） | 编写最小代码使测试通过 | 通过测试 |
| **重构** | 刑部 | 测试通过后 | 优化代码结构，确保行为不变 | 优化代码 |

#### TDD循环规则

| 规则 | 说明 | 检查点 |
|------|------|--------|
| 循环粒度 | 每个功能点完成一个完整循环 | 功能点粒度 |
| 时间限制 | 建议15-30分钟一个循环 | 时间追踪 |
| 重构时机 | 绿灯时方可重构 | 状态检查 |
| 验证要求 | 重构后必须运行测试验证 | 测试执行 |
| 禁止事项 | 红灯时禁止重构 | 状态检查 |

#### TDD循环管理流程（增强版）

```
新功能点
    ↓
[1] 红阶段 - 兵部编写测试
    ↓
测试是否失败？
    ↓是
[2] 绿阶段 - 工部编写代码
    ↓
测试是否通过？
    ↓是
[3] 重构阶段 - 刑部优化代码
    ↓
测试是否仍通过？
    ↓是
循环完成，进入下一功能点
```

#### TDD循环状态机

```
         ┌─────────────────────────────────────────┐
         │                                         │
         ▼                                         │
    ┌─────────┐                                    │
    │  IDLE   │ ──────────────────────────────────►│
    └────┬────┘                                    │
         │ 开始新功能                               │
         ▼                                         │
    ┌─────────┐                                    │
    │   RED   │ ◄──────────────────────────────┐   │
    └────┬────┘                                 │   │
         │ 测试失败                              │   │
         ▼                                      │   │
    ┌─────────┐                                 │   │
    │  GREEN  │ ──测试失败─────────────────────►│   │
    └────┬────┘                                 │   │
         │ 测试通过                              │   │
         ▼                                      │   │
    ┌──────────┐                                │   │
    │ REFACTOR │ ──测试失败─────────────────────┘   │
    └────┬─────┘                                    │
         │ 测试通过                                  │
         ▼                                         │
    ┌─────────┐                                    │
    │ DONE    │ ───────────────────────────────────┘
    └─────────┘
```

#### TDD循环配置管理

```yaml
tdd_cycle_config:
  time_constraints:
    red_phase_max_minutes: 10
    green_phase_max_minutes: 15
    refactor_phase_max_minutes: 10
    total_cycle_max_minutes: 30
    
  quality_gates:
    red_phase:
      - check: "测试文件存在"
        required: true
      - check: "测试可执行"
        required: true
      - check: "测试失败（预期）"
        required: true
        
    green_phase:
      - check: "代码编译通过"
        required: true
      - check: "所有测试通过"
        required: true
      - check: "无新增lint错误"
        required: false
        
    refactor_phase:
      - check: "测试仍通过"
        required: true
      - check: "代码复杂度降低"
        required: false
      - check: "代码重复度降低"
        required: false
        
  automation:
    auto_run_tests: true
    auto_format_code: true
    auto_update_coverage: true
    auto_commit_on_green: false
```

#### TDD循环度量指标

```json
{
  "metrics_definition": {
    "cycle_time": {
      "description": "单个TDD循环总时间",
      "target": "< 30 minutes",
      "measurement": "end_time - start_time"
    },
    "red_to_green_ratio": {
      "description": "红绿阶段时间比",
      "target": "0.5 - 1.5",
      "measurement": "red_time / green_time"
    },
    "refactor_frequency": {
      "description": "执行重构的循环比例",
      "target": "> 60%",
      "measurement": "cycles_with_refactor / total_cycles"
    },
    "test_first_compliance": {
      "description": "先写测试的循环比例",
      "target": "100%",
      "measurement": "test_first_cycles / total_cycles"
    },
    "cycle_success_rate": {
      "description": "一次通过的循环比例",
      "target": "> 80%",
      "measurement": "first_pass_cycles / total_cycles"
    }
  }
}
```

#### TDD循环异常处理

```yaml
exception_handling:
  red_phase_timeout:
    detection: "红阶段超过10分钟"
    actions:
      - "记录超时事件"
      - "通知开发者"
      - "建议拆分测试用例"
      
  green_phase_timeout:
    detection: "绿阶段超过15分钟"
    actions:
      - "记录超时事件"
      - "通知开发者"
      - "建议简化实现或拆分功能"
      
  refactor_regression:
    detection: "重构后测试失败"
    actions:
      - "自动回滚代码"
      - "记录回归事件"
      - "通知刑部审查"
      
  test_flakiness:
    detection: "测试结果不稳定"
    actions:
      - "标记不稳定测试"
      - "隔离执行"
      - "通知兵部修复"
```

#### TDD循环报告（增强版）

```json
{
  "tdd_cycle_id": "CYCLE-001",
  "feature_id": "F-001",
  "timestamp_start": "2024-01-01T00:00:00Z",
  "timestamp_end": "2024-01-01T00:25:00Z",
  "phases": {
    "red": {
      "department": "bingbu",
      "duration_minutes": 5,
      "test_cases_created": 3,
      "status": "completed",
      "details": {
        "test_files": ["test_user_auth.py"],
        "test_names": ["test_login_success", "test_login_invalid_password", "test_login_locked_account"],
        "initial_run_result": "3 failed"
      }
    },
    "green": {
      "department": "gongbu",
      "duration_minutes": 12,
      "lines_of_code": 45,
      "status": "completed",
      "details": {
        "files_modified": ["auth_service.py", "user_model.py"],
        "implementation_approach": "最小实现",
        "test_run_result": "3 passed"
      }
    },
    "refactor": {
      "department": "xingbu",
      "duration_minutes": 8,
      "refactoring_type": "extract_method",
      "status": "completed",
      "details": {
        "refactorings_applied": [
          {
            "type": "extract_method",
            "target": "validate_credentials",
            "description": "提取凭证验证逻辑"
          },
          {
            "type": "rename_variable",
            "target": "user -> authenticated_user",
            "description": "提高变量命名清晰度"
          }
        ],
        "test_run_result": "3 passed"
      }
    }
  },
  "test_results": {
    "before_refactor": {"passed": 3, "failed": 0},
    "after_refactor": {"passed": 3, "failed": 0}
  },
  "code_metrics": {
    "complexity_before": 8,
    "complexity_after": 5,
    "lines_before": 45,
    "lines_after": 38,
    "duplication_before": 5,
    "duplication_after": 0
  },
  "quality_metrics": {
    "cycle_time_minutes": 25,
    "red_to_green_ratio": 0.42,
    "refactor_performed": true,
    "first_pass_success": true
  },
  "violations": [],
  "improvement_suggestions": []
}
```

---

### 阶段四：外部技能调用管理

#### 外部技能调用流程

```
识别外部技能需求
    ↓
[1] 技能匹配评估
    ↓
[2] 调用参数准备
    ↓
[3] 执行外部技能调用
    ↓
[4] 结果接收与验证
    ↓
[5] 结果集成到项目
    ↓
记录调用日志
```

#### 外部技能调用场景

| 触发条件 | 负责部门 | 外部技能类型 | 优先级 | 调用时机 |
|----------|----------|--------------|--------|----------|
| 需要专业UI/UX设计 | 工部 | UI/UX设计技能 | 高 | 设计阶段 |
| 需要构建MCP服务 | 工部 | MCP构建技能 | 高 | 开发阶段 |
| 需要深度安全测试 | 兵部 | 外部安全测试技能 | 高 | 测试阶段 |
| 需要注册新外部技能 | 礼部 | 外部技能注册管理 | 中 | 规划阶段 |
| 需要协调多个外部Agent | 吏部 | 外部技能Agent协调 | 中 | 执行阶段 |
| 需要专业性能优化 | 刑部 | 性能优化技能 | 中 | 重构阶段 |
| 需要多语言翻译 | 工部 | 翻译技能 | 低 | 按需 |

#### 外部技能调用规范

**调用前检查：**
| 检查项 | 检查内容 | 通过标准 |
|--------|----------|----------|
| 需求明确性 | 调用目的和需求是否明确 | 需求清晰 |
| 参数完整性 | 调用参数是否完整 | 参数齐全 |
| 权限检查 | 是否有权限调用该技能 | 权限有效 |
| 依赖检查 | 是否满足技能依赖条件 | 依赖满足 |

**调用后处理：**
| 处理项 | 说明 |
|--------|------|
| 结果验证 | 验证外部技能返回结果是否符合预期 |
| 结果集成 | 将结果集成到当前项目中 |
| 错误处理 | 处理调用失败或结果异常的情况 |
| 日志记录 | 记录调用过程和结果 |

#### 外部技能调用命令

```bash
# 外部技能调用
调用 ./SKILL.md --action=call-external-skill \
  --skill-id=技能ID \
  --parameters=参数 \
  --timeout=超时时间

# 外部技能调用状态查询
调用 ./SKILL.md --action=query-skill-status --call-id=CALL-001

# 外部技能结果集成
调用 ./SKILL.md --action=integrate-skill-result --call-id=CALL-001
```

#### 外部技能调用记录

```json
{
  "call_id": "CALL-001",
  "skill_id": "skill-name",
  "skill_category": "ui_design|security|performance|translation",
  "timestamp_call": "2024-01-01T00:00:00Z",
  "timestamp_complete": "2024-01-01T00:05:00Z",
  "requesting_department": "gongbu",
  "trigger_condition": "触发条件描述",
  "parameters": {
    "param1": "value1",
    "param2": "value2"
  },
  "result": {
    "status": "success|failure|partial",
    "output": "结果内容",
    "artifacts": ["产出物列表"]
  },
  "integration_status": "integrated|pending|failed",
  "performance_metrics": {
    "response_time_ms": 5000,
    "token_usage": 1500
  }
}
```

---

### 阶段五：白盒化流水线协调

#### 7阶段流水线概览

| 阶段 | 名称 | 负责机构 | 门禁条件 | 输出物 |
|------|------|----------|----------|--------|
| 1 | 需求结构化 | 中书省 | 需求结构化完整性≥90% | 结构化需求文档 |
| 2 | 测试先行 | 兵部 | 测试覆盖率≥80% | 测试用例 |
| 3 | 实现与决策 | 工部 | 测试全部通过 | 功能代码 |
| 4 | 静态分析 | 刑部 | 无严重问题 | 分析报告 |
| 5 | 测试执行 | 兵部+工部 | 覆盖率≥80%，无失败用例 | 测试报告 |
| 6 | 验收报告 | 门下省 | 白盒化评分≥0.85 | 验收报告 |
| 7 | 人工门禁 | 用户确认 | 用户明确确认 | 发布许可 |

#### 流水线协调流程

```
启动流水线
    ↓
阶段1: 中书省 - 需求结构化
    ↓ [门禁检查]
阶段2: 兵部 - 测试先行
    ↓ [门禁检查]
阶段3: 工部 - 实现与决策
    ↓ [门禁检查]
阶段4: 刑部 - 静态分析
    ↓ [门禁检查]
阶段5: 兵部+工部 - 测试执行
    ↓ [门禁检查]
阶段6: 门下省 - 验收报告
    ↓ [门禁检查]
阶段7: 用户 - 人工门禁
    ↓
流水线完成
```

#### 流水线门禁管理

**门禁检查规则：**
| 阶段 | 门禁检查项 | 通过标准 | 失败处理 |
|------|------------|----------|----------|
| 1→2 | 需求结构化完整性 | ≥90% | 退回中书省补充 |
| 2→3 | 测试覆盖率 | ≥80% | 补充测试用例 |
| 3→4 | 测试通过率 | 100% | 修复失败测试 |
| 4→5 | 静态分析严重问题数 | 0 | 修复严重问题 |
| 5→6 | 测试覆盖率+通过率 | ≥80%, 100% | 补充测试或修复代码 |
| 6→7 | 白盒化评分 | ≥0.85 | 改进后重新验收 |
| 7→完成 | 用户确认 | 明确确认 | 按用户意见处理 |

#### 流水线协调命令

```bash
# 启动白盒化流水线
调用 ./SKILL.md --action=start-pipeline --pipeline=whitebox --project=项目ID

# 查询流水线状态
调用 ./SKILL.md --action=query-pipeline --pipeline-id=PL-001

# 触发阶段转换
调用 ./SKILL.md --action=transition-phase --pipeline-id=PL-001 --from=1 --to=2

# 触发人工门禁
调用 ./SKILL.md --action=trigger-gate --pipeline-id=PL-001 --gate-type=manual --stage=7

# 暂停/恢复流水线
调用 ./SKILL.md --action=pause-pipeline --pipeline-id=PL-001
调用 ./SKILL.md --action=resume-pipeline --pipeline-id=PL-001
```

#### 流水线状态报告

```json
{
  "pipeline_id": "PL-001",
  "project_id": "PROJ-001",
  "status": "running|paused|completed|failed",
  "current_stage": 3,
  "stages": [
    {
      "stage_number": 1,
      "name": "需求结构化",
      "responsible": "zhongshusheng",
      "status": "completed",
      "gate_passed": true,
      "score": 0.95,
      "timestamp_start": "2024-01-01T00:00:00Z",
      "timestamp_end": "2024-01-01T02:00:00Z"
    },
    {
      "stage_number": 2,
      "name": "测试先行",
      "responsible": "bingbu",
      "status": "completed",
      "gate_passed": true,
      "coverage": 0.85,
      "timestamp_start": "2024-01-01T02:00:00Z",
      "timestamp_end": "2024-01-01T03:30:00Z"
    },
    {
      "stage_number": 3,
      "name": "实现与决策",
      "responsible": "gongbu",
      "status": "in_progress",
      "progress": 0.6,
      "timestamp_start": "2024-01-01T03:30:00Z"
    }
  ],
  "overall_progress": 0.45,
  "estimated_completion": "2024-01-02T12:00:00Z"
}
```

---

### 阶段六：进度管理与异常处理

#### 进度跟踪机制

**跟踪指标：**
| 指标 | 说明 | 更新频率 |
|------|------|----------|
| 任务完成率 | 已完成任务/总任务 | 实时 |
| 里程碑达成率 | 已达成里程碑/总里程碑 | 里程碑节点 |
| 代码提交频率 | 每日/每周提交次数 | 每日 |
| 测试通过率 | 通过测试/总测试 | 每次测试执行 |
| 缺陷密度 | 缺陷数/代码行数 | 每周 |

#### 异常处理流程

```
发现异常
    ↓
[1] 异常分类与定级
    ↓
[2] 通知相关部门
    ↓
[3] 制定处理方案
    ↓
[4] 执行处理
    ↓
[5] 验证恢复
    ↓
记录异常处理日志
```

**异常分类与处理：**
| 异常类型 | 负责部门 | 处理时限 | 升级条件 |
|----------|----------|----------|----------|
| 资源不足 | 户部 | 30分钟 | 无法解决时升级 |
| 任务阻塞 | 吏部 | 1小时 | 阻塞超过2小时 |
| 测试失败 | 兵部+工部 | 2小时 | 失败率>20% |
| 代码质量问题 | 刑部 | 4小时 | 严重问题数>5 |
| 部署失败 | 工部 | 1小时 | 连续失败3次 |

#### 进度报告

```json
{
  "report_id": "RPT-001",
  "project_id": "PROJ-001",
  "timestamp": "2024-01-01T00:00:00Z",
  "report_type": "daily|weekly|milestone",
  "summary": {
    "overall_progress": 0.65,
    "tasks_completed": 65,
    "tasks_total": 100,
    "milestones_achieved": 2,
    "milestones_total": 5
  },
  "department_status": {
    "libu": {"progress": 0.7, "issues": 1},
    "hubu": {"progress": 0.8, "issues": 0},
    "liibu": {"progress": 1.0, "issues": 0},
    "bingbu": {"progress": 0.6, "issues": 2},
    "xingbu": {"progress": 0.5, "issues": 1},
    "gongbu": {"progress": 0.65, "issues": 0}
  },
  "risks": [
    {
      "risk_id": "RISK-001",
      "description": "风险描述",
      "probability": "high|medium|low",
      "impact": "high|medium|low",
      "mitigation": "缓解措施"
    }
  ],
  "next_actions": ["下一步行动计划"]
}
```

---

## 协作说明

### 与中书省的协作

| 协作点 | 协作内容 | 交付物 |
|--------|----------|--------|
| 方案接收 | 接收审议通过的方案 | 方案文档包 |
| 规范咨询 | 就技术规范进行咨询 | 规范说明 |
| 变更申请 | 执行中发现问题申请变更 | 变更申请 |

### 与门下省的协作

| 协作点 | 协作内容 | 交付物 |
|--------|----------|--------|
| 进度汇报 | 定期汇报执行进度 | 进度报告 |
| 质量报告 | 汇报质量指标 | 质量报告 |
| 问题上报 | 上报需要审议的问题 | 问题报告 |

### 与六部的协作

| 协作点 | 协作内容 |
|--------|----------|
| 任务分发 | 将项目任务分解到各部 |
| 资源协调 | 协调各部资源需求 |
| 进度同步 | 同步各部进度信息 |
| 问题解决 | 协调跨部门问题解决 |

---

## 输出物清单

| 输出物 | 格式 | 移交对象 |
|--------|------|----------|
| 执行计划 | Markdown | 六部 |
| 调度日志 | JSON | 存档 |
| 进度报告 | Markdown/JSON | 门下省 |
| 资源分配方案 | JSON | 户部 |
| TDD执行报告 | JSON | 存档 |
| 外部技能调用记录 | JSON | 存档 |
| 流水线状态报告 | JSON | 门下省 |
| 异常处理日志 | JSON | 存档 |

---

## 协同调用接口

### 接口定义

尚书省作为执行统筹机构，提供以下协同调用接口供其他技能调用：

| 接口名称 | 接口描述 | 调用方 |
|----------|----------|--------|
| `coordinate_execution` | 执行协调接口 | 中书省、门下省 |
| `dispatch_to_department` | 六部分发接口 | 外部技能 |
| `manage_tdd_cycle` | TDD循环管理接口 | 兵部、工部、刑部 |
| `call_external_skill` | 外部技能调用接口 | 六部 |
| `manage_pipeline` | 流水线管理接口 | 门下省 |

### 输入参数规范

#### 执行协调接口参数

```json
{
  "interface": "coordinate_execution",
  "version": "1.0.0",
  "timestamp": "2024-01-01T00:00:00Z",
  "caller": "调用方标识",
  "parameters": {
    "project_id": "项目ID",
    "execution_plan_id": "执行计划ID",
    "departments": ["libu", "hubu", "liibu", "bingbu", "xingbu", "gongbu"],
    "coordination_mode": "sequential|parallel|iterative",
    "milestones": [
      {
        "name": "里程碑名称",
        "deadline": "截止时间",
        "deliverables": ["交付物列表"]
      }
    ]
  }
}
```

#### 六部分发接口参数

```json
{
  "interface": "dispatch_to_department",
  "version": "1.0.0",
  "timestamp": "2024-01-01T00:00:00Z",
  "caller": "调用方标识",
  "parameters": {
    "department": "libu|hubu|liibu|bingbu|xingbu|gongbu",
    "task": {
      "task_id": "任务ID",
      "task_type": "任务类型",
      "description": "任务描述",
      "priority": "P0|P1|P2|P3",
      "dependencies": ["依赖任务ID列表"]
    },
    "context": {
      "project_id": "项目ID",
      "phase": "阶段标识",
      "input_artifacts": ["输入产物列表"]
    }
  }
}
```

#### TDD循环管理接口参数

```json
{
  "interface": "manage_tdd_cycle",
  "version": "1.0.0",
  "timestamp": "2024-01-01T00:00:00Z",
  "caller": "调用方标识",
  "parameters": {
    "cycle_id": "TDD循环ID",
    "feature_id": "功能点ID",
    "phase": "red|green|refactor",
    "test_cases": ["测试用例列表"],
    "code_path": "代码路径",
    "verification_required": true
  }
}
```

#### 外部技能调用接口参数

```json
{
  "interface": "call_external_skill",
  "version": "1.0.0",
  "timestamp": "2024-01-01T00:00:00Z",
  "caller": "调用方标识",
  "parameters": {
    "skill_id": "外部技能ID",
    "skill_category": "ui_design|security|performance|translation",
    "requesting_department": "libu|hubu|liibu|bingbu|xingbu|gongbu",
    "input_data": {
      "context": "调用上下文",
      "requirements": "需求描述",
      "constraints": ["约束条件"]
    },
    "timeout_ms": 30000,
    "retry_count": 3
  }
}
```

### 输出格式规范

#### 协调状态报告格式

```json
{
  "interface": "coordinate_execution",
  "call_id": "COORD-001",
  "timestamp": "2024-01-01T00:00:00Z",
  "status": "running|completed|failed|paused",
  "result": {
    "overall_progress": 0.75,
    "department_status": {
      "libu": {"status": "active", "progress": 0.8},
      "hubu": {"status": "completed", "progress": 1.0},
      "liibu": {"status": "idle", "progress": 1.0},
      "bingbu": {"status": "active", "progress": 0.6},
      "xingbu": {"status": "pending", "progress": 0.0},
      "gongbu": {"status": "active", "progress": 0.7}
    },
    "issues": [
      {
        "department": "bingbu",
        "issue_type": "测试失败",
        "description": "问题描述",
        "severity": "major"
      }
    ],
    "next_actions": ["下一步行动"]
  }
}
```

### 调用示例

#### 示例1：执行协调调用

```bash
# 调用执行协调接口
调用 ./SKILL.md --interface=coordinate_execution \
  --project-id="PROJ-001" \
  --departments='["libu","hubu","gongbu"]' \
  --coordination-mode="sequential" \
  --output-format=json
```

#### 示例2：六部分发调用

```bash
# 分发任务到工部
调用 ./SKILL.md --interface=dispatch_to_department \
  --department="gongbu" \
  --task='{"task_id":"TASK-001","task_type":"development","priority":"P1"}' \
  --context='{"project_id":"PROJ-001"}'
```

#### 示例3：外部技能调用

```bash
# 调用外部UI设计技能
调用 ./SKILL.md --interface=call_external_skill \
  --skill-id="ui-ux-pro-max" \
  --skill-category="ui_design" \
  --requesting-department="gongbu" \
  --input-data='{"requirements":"设计登录页面"}'
```

### 协同回调接口

尚书省在执行过程中，会通过以下回调接口通知相关技能：

| 回调接口 | 触发时机 | 回调目标 |
|----------|----------|----------|
| `on_phase_complete` | 阶段完成时 | 门下省 |
| `on_department_done` | 部门任务完成时 | 相关部门 |
| `on_external_skill_result` | 外部技能返回时 | 调用部门 |
| `on_execution_blocked` | 执行阻塞时 | 门下省、中书省 |

#### 回调数据格式

```json
{
  "callback": "on_phase_complete",
  "call_id": "COORD-001",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "phase": "阶段名称",
    "completed_departments": ["libu", "hubu"],
    "deliverables": ["阶段交付物"],
    "issues_found": ["发现的问题"],
    "next_phase": "下一阶段"
  }
}
```

---

## 子技能引用

| 子技能 | 用途 |
|--------|------|
| [外部技能集成](../subskills/waiji_jicheng.md) | 外部技能协调调用详细说明 |
| [白盒化流水线](../subskills/baihehua_liushuixian.md) | 白盒化流水线协调详细说明 |
| [skill-creator集成](#skill-creator集成) | 技能创建与优化集成流程 |

---

## 外部技能集成

### skill-creator集成

#### 集成概述

skill-creator是用于创建、修改、优化和测试技能的元技能。尚书省在执行过程中需要创建新技能或优化现有技能时，应调用skill-creator技能。

#### 集成流程

```
识别技能创建/优化需求
    ↓
[1] 需求分析与评估
    ↓
[2] 调用skill-creator进行技能创建/优化
    ↓
[3] 技能评估与测试
    ↓
[4] 结果验证与集成
    ↓
[5] 更新技能注册表
    ↓
记录集成日志
```

#### 触发条件

| 触发场景 | 负责部门 | 优先级 | 说明 |
|----------|----------|--------|------|
| 需要创建新技能 | 礼部 | 高 | 项目需要自定义技能支持 |
| 现有技能效果不佳 | 吏部 | 高 | 技能触发率低或输出质量差 |
| 技能描述需要优化 | 礼部 | 中 | 提高技能触发准确性 |
| 需要技能性能测试 | 兵部 | 中 | 评估技能执行效率 |
| 技能需要迭代改进 | 礼部 | 中 | 基于反馈优化技能 |

#### 调用流程

**1. 技能创建流程**

```bash
# 步骤1: 需求分析与准备
调用 skill-creator/SKILL.md --action=analyze-requirements \
  --skill-purpose="技能用途描述" \
  --target-users="目标用户" \
  --expected-output="期望输出"

# 步骤2: 执行技能创建
调用 skill-creator/SKILL.md --action=create-skill \
  --skill-name="技能名称" \
  --skill-category="技能分类" \
  --output-path=".trae/skills/"

# 步骤3: 生成测试用例
调用 skill-creator/SKILL.md --action=generate-tests \
  --skill-path=".trae/skills/新技能/SKILL.md" \
  --test-count=10

# 步骤4: 执行技能评估
调用 skill-creator/SKILL.md --action=evaluate \
  --skill-path=".trae/skills/新技能/SKILL.md" \
  --test-suite="tests/新技能/"
```

**2. 技能优化流程**

```bash
# 步骤1: 分析现有技能问题
调用 skill-creator/SKILL.md --action=analyze-skill \
  --skill-path=".trae/skills/现有技能/SKILL.md" \
  --analysis-type="description|content|structure"

# 步骤2: 执行技能优化
调用 skill-creator/SKILL.md --action=optimize \
  --skill-path=".trae/skills/现有技能/SKILL.md" \
  --optimization-target="trigger-accuracy|output-quality|coverage"

# 步骤3: 对比测试
调用 skill-creator/SKILL.md --action=benchmark \
  --skill-path=".trae/skills/现有技能/SKILL.md" \
  --baseline-path=".trae/skills/现有技能/SKILL.md.bak" \
  --iterations=5
```

#### 技能评估流程

**评估检查清单：**

| 评估项 | 检查内容 | 通过标准 | 评估工具 |
|--------|----------|----------|----------|
| 描述准确性 | 技能描述是否清晰准确 | 描述能正确触发技能 | skill-creator评估 |
| 内容完整性 | 技能内容是否完整 | 覆盖所有预期场景 | 测试用例覆盖 |
| 输出质量 | 技能输出是否符合预期 | 质量评分≥0.85 | 盲比较测试 |
| 执行效率 | 技能执行时间和资源消耗 | 执行时间<5秒 | 性能基准测试 |
| 可维护性 | 技能结构是否清晰 | 结构评分≥0.8 | 代码审查 |

**评估执行命令：**

```bash
# 完整技能评估
调用 skill-creator/SKILL.md --action=full-evaluation \
  --skill-path=".trae/skills/目标技能/SKILL.md" \
  --evaluation-type="comprehensive" \
  --output-format="json"

# 触发准确性评估
调用 skill-creator/SKILL.md --action=evaluate-trigger \
  --skill-path=".trae/skills/目标技能/SKILL.md" \
  --test-queries="tests/queries.json"

# 输出质量评估
调用 skill-creator/SKILL.md --action=evaluate-quality \
  --skill-path=".trae/skills/目标技能/SKILL.md" \
  --reference-outputs="tests/reference/"
```

#### 集成调用示例

**示例1: 创建项目专用技能**

```bash
#!/bin/bash
# scripts/create_project_skill.sh

SKILL_NAME="project-analyzer"
PROJECT_CONTEXT="电商平台代码分析"

echo "[1/5] 分析技能需求..."
调用 skill-creator/SKILL.md --action=analyze-requirements \
  --skill-purpose="分析电商平台代码结构和依赖关系" \
  --target-users="开发团队" \
  --expected-output="代码分析报告、依赖图谱、优化建议"

echo "[2/5] 创建技能..."
调用 skill-creator/SKILL.md --action=create-skill \
  --skill-name="${SKILL_NAME}" \
  --skill-category="development" \
  --project-context="${PROJECT_CONTEXT}" \
  --output-path=".trae/skills/"

echo "[3/5] 生成测试用例..."
调用 skill-creator/SKILL.md --action=generate-tests \
  --skill-path=".trae/skills/${SKILL_NAME}/SKILL.md" \
  --test-count=15 \
  --coverage-target="structure,dependencies,quality"

echo "[4/5] 执行技能评估..."
调用 skill-creator/SKILL.md --action=evaluate \
  --skill-path=".trae/skills/${SKILL_NAME}/SKILL.md" \
  --test-suite="tests/${SKILL_NAME}/" \
  --evaluation-criteria="accuracy,completeness,usefulness"

echo "[5/5] 注册技能..."
# 更新外部技能注册表
调用 ./SKILL.md --action=register-skill \
  --skill-name="${SKILL_NAME}" \
  --skill-path=".trae/skills/${SKILL_NAME}/SKILL.md" \
  --skill-category="development"

echo "技能创建完成: ${SKILL_NAME}"
```

**示例2: 优化现有技能**

```bash
#!/bin/bash
# scripts/optimize_existing_skill.sh

SKILL_PATH=".trae/skills/sanliu/shangshusheng/SKILL.md"

echo "[1/4] 分析技能现状..."
调用 skill-creator/SKILL.md --action=analyze-skill \
  --skill-path="${SKILL_PATH}" \
  --analysis-type="comprehensive" \
  --check-trigger-accuracy=true \
  --check-output-quality=true

echo "[2/4] 备份原技能..."
cp "${SKILL_PATH}" "${SKILL_PATH}.bak.$(date +%Y%m%d)"

echo "[3/4] 执行优化..."
调用 skill-creator/SKILL.md --action=optimize \
  --skill-path="${SKILL_PATH}" \
  --optimization-target="all" \
  --improve-description=true \
  --improve-structure=true \
  --improve-examples=true

echo "[4/4] 验证优化效果..."
调用 skill-creator/SKILL.md --action=benchmark \
  --skill-path="${SKILL_PATH}" \
  --baseline-path="${SKILL_PATH}.bak.*" \
  --iterations=10 \
  --metrics="trigger-accuracy,output-quality,response-time"

echo "技能优化完成"
```

#### 错误处理机制

| 错误类型 | 错误描述 | 处理策略 | 重试机制 |
|----------|----------|----------|----------|
| 需求不明确 | 技能需求描述模糊 | 返回补充需求信息 | 人工确认后重试 |
| 创建失败 | 技能创建过程出错 | 检查输出路径权限 | 自动重试3次 |
| 评估失败 | 测试用例执行失败 | 检查测试环境 | 手动修复后重试 |
| 优化失败 | 技能优化未达预期 | 分析失败原因 | 调整参数后重试 |
| 注册失败 | 技能注册表更新失败 | 检查文件权限 | 自动重试3次 |

**错误处理示例代码：**

```bash
# 带错误处理的技能创建
function create_skill_with_retry() {
    local skill_name=$1
    local max_retries=3
    local retry_count=0
    
    while [ $retry_count -lt $max_retries ]; do
        echo "尝试创建技能: ${skill_name} (第 $((retry_count + 1)) 次)"
        
        if 调用 skill-creator/SKILL.md --action=create-skill \
            --skill-name="${skill_name}" \
            --output-path=".trae/skills/"; then
            echo "技能创建成功"
            return 0
        else
            retry_count=$((retry_count + 1))
            echo "创建失败，${retry_count}秒后重试..."
            sleep $retry_count
        fi
    done
    
    echo "错误: 技能创建失败，已达到最大重试次数"
    # 记录错误日志
    log_error "skill_creation_failed" "${skill_name}"
    return 1
}
```

#### 日志记录规范

**技能集成日志格式：**

```json
{
  "log_id": "SKILL-CREATE-001",
  "timestamp": "2024-01-01T00:00:00Z",
  "operation": "create|optimize|evaluate",
  "skill_name": "技能名称",
  "skill_path": ".trae/skills/技能/SKILL.md",
  "requesting_department": "礼部|吏部|兵部",
  "trigger_context": "触发上下文描述",
  "execution_steps": [
    {
      "step": 1,
      "action": "analyze-requirements",
      "status": "success|failure",
      "duration_ms": 5000,
      "output_summary": "步骤输出摘要"
    }
  ],
  "final_result": {
    "status": "success|failure|partial",
    "skill_created": true,
    "tests_generated": 10,
    "evaluation_score": 0.92,
    "artifacts": ["SKILL.md", "tests/", "assets/"]
  },
  "errors": [
    {
      "error_type": "类型",
      "error_message": "错误信息",
      "recovery_action": "恢复操作"
    }
  ],
  "performance_metrics": {
    "total_duration_ms": 30000,
    "token_usage": 5000,
    "api_calls": 5
  }
}
```

**日志记录命令：**

```bash
# 记录技能集成日志
调用 ./SKILL.md --action=log-skill-integration \
  --log-data="logs/skill_integration.json" \
  --log-level="info|warning|error"

# 查询技能集成历史
调用 ./SKILL.md --action=query-skill-logs \
  --skill-name="技能名称" \
  --date-range="2024-01-01,2024-01-31"
```

---

## 附录：完整开发流程协调图

```
项目启动
    ↓
[尚书省] 环境检测 → 资源分配 → 计划制定
    ↓
[吏部] 任务分配
    ↓
[户部] 资源配置
    ↓
[礼部] 规范制定
    ↓
迭代循环（每个功能点）：
    ┌─────────────────────────────────────────┐
    ↓                                         |
  [兵部] 红阶段：编写测试（测试先行）          |
    ↓                                         |
  [工部] 绿阶段：编写代码（最小实现）          |
    ↓                                         |
  [刑部] 重构阶段：优化代码（保持行为）        |
    ↓                                         |
  [兵部] 验证测试仍通过                        |
    └─────────────────────────────────────────┘
    ↓
[工部] 集成测试
    ↓
[刑部] 静态分析
    ↓
[兵部] 全面测试
    ↓
[工部] 部署交付
    ↓
[尚书省] 进度汇总 → 上报门下省
```

---

## 协同效果评估能力（增强版）

### 执行协同评估指标

尚书省作为执行统筹机构，负责评估三省六部协同执行效果。

| 评估维度 | 指标 | 目标值 | 度量方法 |
|----------|------|--------|----------|
| 执行效率 | 任务平均完成时间 | ≤30分钟 | 时间戳差值统计 |
| 资源利用率 | 资源使用效率 | 70-85% | 资源监控数据 |
| 六部协调效率 | 部门间协作效率 | ≥90% | 协作时间统计 |
| TDD循环效率 | TDD循环平均时长 | ≤30分钟 | 循环时间统计 |
| 流水线通过率 | 一次通过流水线比例 | ≥85% | 流水线统计 |

### 执行协同评估流程

```
[1] 收集执行数据
    ↓
[2] 计算执行效率指标
    ↓
[3] 分析资源利用
    ↓
[4] 评估六部协调
    ↓
[5] 生成优化建议
    ↓
输出《执行协同评估报告》
```

### 执行协同评估报告格式

```json
{
  "evaluation_id": "EVAL-SHANG-001",
  "timestamp": "2024-01-01T00:00:00Z",
  "period": {
    "start": "2024-01-01T00:00:00Z",
    "end": "2024-01-07T23:59:59Z"
  },
  "execution_metrics": {
    "total_tasks": 50,
    "completed_tasks": 47,
    "failed_tasks": 3,
    "avg_completion_time_minutes": 25,
    "on_time_rate": 0.94
  },
  "resource_metrics": {
    "cpu_utilization": 0.78,
    "memory_utilization": 0.82,
    "human_resource_efficiency": 0.85,
    "resource_conflicts": 2
  },
  "coordination_metrics": {
    "cross_department_collaborations": 15,
    "avg_collaboration_time_minutes": 12,
    "coordination_efficiency": 0.92,
    "bottleneck_departments": []
  },
  "tdd_metrics": {
    "total_cycles": 30,
    "avg_cycle_time_minutes": 22,
    "refactor_rate": 0.75,
    "test_first_compliance": 1.0
  },
  "pipeline_metrics": {
    "total_pipelines": 5,
    "first_pass_rate": 0.80,
    "avg_pipeline_duration_hours": 4.5,
    "gate_failure_rate": 0.15
  },
  "province_coordination": {
    "zhongshusheng": {
      "decision_requests": 3,
      "avg_response_time_minutes": 15,
      "coordination_quality": 0.95
    },
    "menxiasheng": {
      "review_requests": 5,
      "avg_review_time_minutes": 45,
      "approval_rate": 0.90
    }
  },
  "recommendations": [
    {
      "category": "pipeline_optimization",
      "priority": "high",
      "description": "优化流水线门禁检查，减少失败率",
      "expected_impact": "预计一次通过率提升至90%"
    }
  ]
}
```

---

## 流水线协调能力（增强版）

### 白盒化7阶段流水线管理

尚书省负责管理和协调白盒化7阶段流水线的执行。

| 阶段 | 名称 | 负责省/部 | 尚书省角色 | 协调内容 |
|------|------|-----------|------------|----------|
| 1 | 需求分析 | 中书省 | 监督 | 接收需求，监控进度 |
| 2 | SDD规范定义 | 中书省 | 监督 | 协调规范制定 |
| 3 | 审议批准 | 门下省 | 协调 | 协调审议流程 |
| 4 | 测试先行 | 兵部 | 主导 | 分配任务，监控执行 |
| 5 | 代码实现 | 工部 | 主导 | 分配任务，协调开发 |
| 6 | 持续重构 | 刑部 | 主导 | 分配任务，验证效果 |
| 7 | 部署发布 | 工部 | 主导 | 协调部署，验证发布 |

### 流水线协调配置

```yaml
pipeline_coordination:
  stage_transitions:
    automatic: true
    require_approval: false
    approval_stages: [3, 7]
    
  timeout_settings:
    stage_timeout_minutes: 60
    pipeline_timeout_hours: 8
    escalation_after_minutes: 30
    
  retry_policy:
    max_retries: 3
    retry_delay_seconds: 60
    exponential_backoff: true
    
  notification:
    on_stage_complete: true
    on_stage_fail: true
    on_pipeline_complete: true
    channels: ["event_bus", "log", "callback"]
```

### 流水线协调流程

```
流水线启动
    ↓
[1] 初始化流水线状态
    ↓
[2] 协调阶段1: 需求分析
    ↓ [门禁检查]
[3] 协调阶段2: SDD规范定义
    ↓ [门禁检查]
[4] 协调阶段3: 审议批准
    ↓ [门禁检查]
[5] 协调阶段4: 测试先行
    ↓ [门禁检查]
[6] 协调阶段5: 代码实现
    ↓ [门禁检查]
[7] 协调阶段6: 持续重构
    ↓ [门禁检查]
[8] 协调阶段7: 部署发布
    ↓
流水线完成
```

### 流水线异常处理

| 异常类型 | 检测条件 | 处理策略 | 升级条件 |
|----------|----------|----------|----------|
| 阶段超时 | 阶段执行超过设定时间 | 自动重试或跳过 | 重试3次失败 |
| 门禁失败 | 质量门禁检查不通过 | 阻断并通知 | 严重问题 |
| 依赖阻塞 | 上游依赖未完成 | 等待或重新调度 | 阻塞超过1小时 |
| 资源不足 | 执行资源不够 | 动态调配或排队 | 无法调配时 |

### 流水线协调报告

```json
{
  "coordination_id": "COORD-PL-001",
  "timestamp": "2024-01-01T00:00:00Z",
  "pipeline_id": "PIPE-001",
  "coordination_events": [
    {
      "event_id": "EVT-001",
      "event_type": "stage_transition",
      "from_stage": "test_first",
      "to_stage": "implementation",
      "timestamp": "2024-01-01T10:00:00Z",
      "gate_result": "passed",
      "duration_seconds": 1800
    },
    {
      "event_id": "EVT-002",
      "event_type": "resource_allocation",
      "department": "gongbu",
      "resources": {"cpu": 4, "memory": "8GB"},
      "timestamp": "2024-01-01T10:05:00Z"
    }
  ],
  "coordination_metrics": {
    "total_coordination_time_minutes": 15,
    "resource_allocation_count": 3,
    "issue_resolution_count": 1,
    "escalation_count": 0
  },
  "issues_resolved": [
    {
      "issue_id": "ISSUE-001",
      "type": "resource_conflict",
      "description": "工部和兵部资源冲突",
      "resolution": "按优先级分配给工部",
      "resolution_time_seconds": 120
    }
  ]
}
```

---

## 智能调度支持

### 任务智能调度算法

```python
def calculate_task_priority(task, context):
    weights = {
        "business_value": 0.25,
        "technical_dependency": 0.20,
        "resource_availability": 0.20,
        "deadline_urgency": 0.15,
        "risk_level": 0.10,
        "historical_performance": 0.10
    }
    
    scores = {
        "business_value": evaluate_business_value(task),
        "technical_dependency": evaluate_dependencies(task, context),
        "resource_availability": check_resource_availability(task, context),
        "deadline_urgency": calculate_deadline_urgency(task),
        "risk_level": assess_risk_level(task),
        "historical_performance": get_historical_performance(task.assignee)
    }
    
    return sum(scores[k] * weights[k] for k in weights)
```

### 部门能力匹配

```json
{
  "capability_matching": {
    "libu": {
      "strengths": ["agent_allocation", "skill_matching", "load_balancing"],
      "capacity": 10,
      "current_load": 3,
      "availability": 0.7
    },
    "hubu": {
      "strengths": ["environment_config", "resource_allocation", "dependency_management"],
      "capacity": 8,
      "current_load": 2,
      "availability": 0.75
    },
    "liibu": {
      "strengths": ["code_review", "standard_definition", "documentation"],
      "capacity": 6,
      "current_load": 1,
      "availability": 0.83
    },
    "bingbu": {
      "strengths": ["test_design", "test_first", "boundary_testing"],
      "capacity": 12,
      "current_load": 5,
      "availability": 0.58
    },
    "xingbu": {
      "strengths": ["code_refactoring", "quality_optimization", "bug_fixing"],
      "capacity": 8,
      "current_load": 3,
      "availability": 0.63
    },
    "gongbu": {
      "strengths": ["code_implementation", "feature_development", "deployment"],
      "capacity": 15,
      "current_load": 8,
      "availability": 0.47
    }
  }
}
```

### 调度决策支持

```json
{
  "scheduling_decision_id": "SCHED-001",
  "timestamp": "2024-01-01T00:00:00Z",
  "task_id": "TASK-001",
  "decision": {
    "assigned_department": "gongbu",
    "priority": "high",
    "estimated_duration_minutes": 45,
    "required_resources": {
      "cpu": 2,
      "memory": "4GB"
    },
    "dependencies": ["TASK-000"],
    "scheduled_start": "2024-01-01T10:00:00Z"
  },
  "reasoning": {
    "capability_match_score": 0.95,
    "load_balance_score": 0.85,
    "dependency_satisfied": true,
    "resource_available": true
  },
  "alternatives": [
    {
      "department": "xingbu",
      "score": 0.75,
      "rejected_reason": "当前负载较高"
    }
  ]
}
```

---

## 增强功能集成

### 与provincial_coordinator集成

尚书省通过provincial_coordinator.py实现执行流程的自动化和协同：

```python
from scripts.provincial_coordinator import (
    ProvincialCoordinator,
    SmartDispatcher,
    PipelineManager,
    ExecutionAnalyzer,
    CoordinationEvaluator
)

coordinator = ProvincialCoordinator()
dispatcher = SmartDispatcher()
pipeline_manager = PipelineManager()
analyzer = ExecutionAnalyzer()
evaluator = CoordinationEvaluator()

def coordinate_execution(project_id: str):
    pipeline = pipeline_manager.create_pipeline(project_id)
    pipeline_manager.start_pipeline(pipeline.pipeline_id)
    
    while pipeline.status != "completed":
        status = pipeline_manager.get_pipeline_status(pipeline.pipeline_id)
        
        if status["status"] == "failed":
            handle_pipeline_failure(pipeline)
            break
        
        coordinate_current_stage(status)
        
    evaluation = evaluator.evaluate_coordination(
        list(coordinator.tasks.values()),
        list(analyzer.results.values())
    )
    
    return evaluation
```

### 智能分发集成

```python
from scripts.provincial_coordinator import TaskRequirement, SmartDispatcher, TaskPriority

dispatcher = SmartDispatcher()

requirement = TaskRequirement(
    task_id="EXEC-001",
    required_capabilities={
        "code_implementation": 0.9,
        "feature_development": 0.85
    },
    preferred_specializations=["gongbu"],
    priority=TaskPriority.HIGH
)

decision = dispatcher.find_best_match(requirement, "ministry")
print(f"最佳匹配部门: {decision.assigned_entity}")
print(f"综合得分: {decision.overall_score}")
```

---

## 执行质量保障

### 执行质量检查清单

```
□ 执行计划完整，任务分解合理
□ 资源分配充分，无资源冲突
□ 六部协调顺畅，无阻塞问题
□ TDD循环规范，测试先行
□ 流水线执行正常，门禁通过
□ 进度跟踪及时，报告准确
□ 异常处理及时，恢复有效
□ 协同效果良好，持续优化
```

### 执行质量评分

| 评分项 | 权重 | 评分标准 |
|--------|------|----------|
| 计划完整性 | 20% | 执行计划完整、可执行 |
| 资源利用率 | 20% | 资源分配合理、使用高效 |
| 协调效率 | 20% | 六部协调顺畅、响应及时 |
| 任务完成率 | 20% | 任务按时完成、质量达标 |
| 异常处理 | 10% | 异常处理及时、恢复有效 |
| 持续改进 | 10% | 持续优化、效果提升 |

---

## 目录创建策略

### 尚书省目录管理

尚书省作为执行统筹机构，在产出执行文档时遵循**按需创建目录**原则：

| 产出物 | 存储目录 | 创建时机 |
|--------|----------|----------|
| 执行计划 | `docs/workflow/execution/` | 计划制定时 |
| 调度日志 | `data/logs/coordination/` | 调度执行时 |
| 进度报告 | `docs/workflow/reports/` | 报告生成时 |
| TDD执行报告 | `docs/workflow/tdd/` | TDD循环完成时 |
| 外部技能调用记录 | `data/skill_calls/` | 技能调用时 |

### 六部目录管理

| 部门 | 产出物目录 | 创建时机 |
|------|------------|----------|
| 吏部 | `docs/workflow/tasks/` | 任务分配时 |
| 户部 | `docs/workflow/resources/` | 资源配置时 |
| 礼部 | `docs/workflow/standards/` | 规范制定时 |
| 兵部 | `docs/workflow/tests/` | 测试执行时 |
| 刑部 | `docs/workflow/refactoring/` | 重构完成时 |
| 工部 | `docs/workflow/implementation/` | 开发部署时 |

### 路径配置

```yaml
shangshusheng_paths:
  output_base: "docs/workflow/"
  execution_plans: "docs/workflow/execution/"
  coordination_logs: "data/logs/coordination/"
  progress_reports: "docs/workflow/reports/"
  tdd_reports: "docs/workflow/tdd/"
  skill_calls: "data/skill_calls/"
```

### 目录创建命令

```bash
# 通过路径配置管理器创建目录
python skillscripts/utils/path_config_manager.py create --type execution
python skillscripts/utils/path_config_manager.py create --type tdd
python skillscripts/utils/path_config_manager.py create --type logs
```

---

## 版本历史

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| 2.3.0 | 2026-03-30 | 新增协同效果评估、流水线协调、智能调度支持能力 |
| 2.4.0 | 2026-03-30 | 新增需求追溯集成、外部技能调用增强、TDD循环管理增强 |
| 2.7.1 | 2026-03-31 | 新增目录创建策略说明、六部路径配置、执行报告路径管理 |
