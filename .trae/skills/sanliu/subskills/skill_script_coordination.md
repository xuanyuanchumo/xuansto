# 子技能与脚本协同调用指南

> 🔗 **协同工作，高效执行** - 通过标准化接口实现子技能与脚本的无缝协同调用

---

## 概述

子技能与脚本协同调用是三省六部技能的核心能力之一，它允许不同类型的组件之间进行标准化交互，实现复杂的业务流程自动化。

### 核心特性

- **标准化调用接口**：统一的技能调用协议
- **跨类型调用支持**：子技能、脚本、服务之间的互调
- **调用链追踪**：完整的调用历史和状态追踪
- **错误处理机制**：自动重试、降级和回滚
- **性能监控**：调用耗时、成功率统计

---

## 协同调用架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        子技能与脚本协同调用架构                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                      调用协调层                                       │   │
│   │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│   │  │ 调用调度器   │  │ 路由解析器   │  │ 负载均衡器   │              │   │
│   │  │  Dispatcher  │  │   Router     │  │   Balancer   │              │   │
│   │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                      执行适配层                                       │   │
│   │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│   │  │ 子技能适配器 │  │ 脚本适配器   │  │ 服务适配器   │              │   │
│   │  │   Subskill   │  │   Script     │  │   Service    │              │   │
│   │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                      监控追踪层                                       │   │
│   │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│   │  │ 调用链追踪   │  │ 性能监控     │  │ 日志记录     │              │   │
│   │  │   Tracing    │  │  Monitoring  │  │   Logging    │              │   │
│   │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                      错误处理层                                       │   │
│   │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│   │  │ 重试管理器   │  │ 降级处理器   │  │ 回滚管理器   │              │   │
│   │  │   Retry      │  │  Fallback    │  │  Rollback    │              │   │
│   │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 子技能与脚本协同调用指南

### 调用类型

| 调用类型 | 说明 | 使用场景 |
|----------|------|----------|
| `subskill_to_script` | 子技能调用脚本 | 子技能需要执行脚本功能 |
| `script_to_subskill` | 脚本调用子技能 | 脚本需要获取子技能能力 |
| `subskill_to_subskill` | 子技能互调 | 子技能之间的协作 |
| `script_to_script` | 脚本互调 | 脚本之间的协作 |

### 调用方式

#### 1. 子技能调用脚本

```python
from skillscripts.core.skill_caller import SkillCaller

caller = SkillCaller()

result = caller.call_script(
    script_name='auto_fixer',
    script_type='optimization',
    params={
        'target': './src',
        'error_type': 'ImportError',
        'dry_run': False
    }
)

print(f"执行结果: {result['status']}")
print(f"修复数量: {result['fixes_count']}")
```

#### 2. 脚本调用子技能

```python
from skillscripts.core.skill_caller import SkillCaller

caller = SkillCaller()

result = caller.call_subskill(
    subskill_name='test',
    params={
        'test_type': 'unit',
        'coverage': True,
        'report_format': 'markdown'
    }
)

print(f"测试结果: {result['status']}")
print(f"覆盖率: {result['coverage']}")
```

#### 3. 链式调用

```python
from skillscripts.core.skill_caller import SkillCaller

caller = SkillCaller()

chain_result = caller.execute_chain([
    {
        'type': 'subskill',
        'name': 'xuqiu_fenxi',
        'params': {'requirement_text': '构建电商平台'}
    },
    {
        'type': 'script',
        'name': 'requirement_parser',
        'script_type': 'requirements',
        'params': {}
    },
    {
        'type': 'subskill',
        'name': 'xitong_sheji',
        'params': {}
    }
])

print(f"链式执行结果: {chain_result['status']}")
for step in chain_result['steps']:
    print(f"  - {step['name']}: {step['status']}")
```

### 命令行调用

```bash
python skillscripts/utils/skill_caller.py call \
  --type script \
  --name auto_fixer \
  --script-type optimization \
  --params '{"target": "./src"}'

python skillscripts/utils/skill_caller.py call \
  --type subskill \
  --name test \
  --params '{"test_type": "unit"}'

python skillscripts/utils/skill_caller.py chain \
  --manifest call_chain.yaml
```

---

## 跨类型调用说明

### 调用协议

所有跨类型调用遵循统一的调用协议：

```python
{
    "call_id": "CALL-20240329120000",
    "call_type": "subskill_to_script",
    "source": {
        "type": "subskill",
        "name": "test",
        "version": "1.0.0"
    },
    "target": {
        "type": "script",
        "name": "auto_fixer",
        "script_type": "optimization"
    },
    "params": {
        "target": "./src"
    },
    "options": {
        "timeout": 30000,
        "retry": 3,
        "async": false
    },
    "context": {
        "trace_id": "TRACE-xxx",
        "parent_call_id": null
    }
}
```

### 调用适配器

#### 子技能适配器

```python
from skillscripts.core.call_adapters import SubskillAdapter

adapter = SubskillAdapter()

result = adapter.invoke(
    subskill_name='test',
    params={'test_type': 'unit'},
    context={'trace_id': 'TRACE-xxx'}
)
```

#### 脚本适配器

```python
from skillscripts.core.call_adapters import ScriptAdapter

adapter = ScriptAdapter()

result = adapter.invoke(
    script_name='auto_fixer',
    script_type='optimization',
    params={'target': './src'},
    context={'trace_id': 'TRACE-xxx'}
)
```

#### 服务适配器

```python
from skillscripts.core.call_adapters import ServiceAdapter

adapter = ServiceAdapter()

result = adapter.invoke(
    service_name='evolution_api',
    endpoint='/api/evolution/trigger',
    method='POST',
    params={'evolution_type': 'skill_optimization'},
    context={'trace_id': 'TRACE-xxx'}
)
```

### 跨类型调用配置

```yaml
cross_type_calling:
  enabled: true
  
  adapters:
    subskill:
      timeout: 60000
      retry: 3
      fallback_enabled: true
    script:
      timeout: 300000
      retry: 2
      fallback_enabled: true
    service:
      timeout: 30000
      retry: 3
      fallback_enabled: true
  
  routing:
    auto_discover: true
    cache_routes: true
    cache_ttl: 300
  
  security:
    auth_required: true
    allowed_callers:
      - subskill
      - script
    rate_limit: 100
```

---

## 调用链追踪使用指南

### 追踪架构

```
调用链追踪:

┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   调用入口 ──▶ TraceID生成 ──▶ Span创建 ──▶ 执行调用 ──▶ Span结束          │
│       │            │             │            │            │                │
│       ▼            ▼             ▼            ▼            ▼                │
│   ┌───────┐   ┌───────┐    ┌───────┐   ┌───────┐   ┌───────┐             │
│   │请求   │   │唯一   │    │调用   │   │记录   │   │计算   │             │
│   │接收   │   │标识   │    │信息   │   │指标   │   │耗时   │             │
│   │解析   │   │生成   │    │封装   │   │日志   │   │状态   │             │
│   └───────┘   └───────┘    └───────┘   └───────┘   └───────┘             │
│                                                                             │
│   子调用 ──▶ 继承TraceID ──▶ 创建子Span ──▶ 执行 ──▶ 结束子Span            │
│       │            │              │            │            │              │
│       ▼            ▼              ▼            ▼            ▼              │
│   ┌───────┐   ┌───────┐     ┌───────┐   ┌───────┐   ┌───────┐           │
│   │嵌套   │   │保持   │     │关联   │   │执行   │   │记录   │           │
│   │调用   │   │链路   │     │父子   │   │子调用 │   │结果   │           │
│   │检测   │   │标识   │     │关系   │   │       │   │       │           │
│   └───────┘   └───────┘     └───────┘   └───────┘   └───────┘           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 使用示例

#### 启用追踪

```python
from skillscripts.core.call_tracer import CallTracer

tracer = CallTracer(enabled=True)

with tracer.trace(
    operation='skill_call',
    target='auto_fixer',
    params={'target': './src'}
) as span:
    span.set_tag('script_type', 'optimization')
    span.set_tag('caller', 'subskill:test')
    
    result = execute_fix()
    
    span.set_result(result)
    span.set_status('success')

print(f"TraceID: {span.trace_id}")
print(f"耗时: {span.duration_ms}ms")
```

#### 查询调用链

```python
from skillscripts.core.call_tracer import CallTracer

tracer = CallTracer()

trace = tracer.get_trace('TRACE-20240329120000')

print(f"调用链: {trace.operation}")
print(f"总耗时: {trace.total_duration_ms}ms")
print(f"调用层级: {trace.depth}")

for span in trace.spans:
    print(f"  [{span.level}] {span.operation}")
    print(f"      目标: {span.target}")
    print(f"      耗时: {span.duration_ms}ms")
    print(f"      状态: {span.status}")
```

#### 调用链可视化

```python
from skillscripts.core.call_tracer import CallTracer

tracer = CallTracer()

trace = tracer.get_trace('TRACE-20240329120000')

visualization = tracer.visualize(trace, format='tree')
print(visualization)
```

**输出示例：**
```
TRACE-20240329120000 (总耗时: 1500ms)
├── [1] skill_call: auto_fixer (1200ms) ✓
│   ├── [2] script_call: issue_locator (400ms) ✓
│   │   └── [3] file_scan (200ms) ✓
│   └── [4] script_call: auto_fix (600ms) ✓
│       ├── [5] backup_create (100ms) ✓
│       └── [6] fix_apply (400ms) ✓
└── [7] validation (200ms) ✓
```

### 追踪配置

```yaml
call_tracing:
  enabled: true
  
  sampling:
    rate: 1.0
    max_traces_per_second: 100
  
  storage:
    type: file
    path: "./logs/traces"
    retention_days: 7
  
  export:
    enabled: false
    endpoint: "http://jaeger:14268/api/traces"
  
  tags:
    default:
      - skill_id
      - version
      - environment
    custom: []
```

### 追踪命令

```bash
python skillscripts/utils/call_tracer.py query \
  --trace-id TRACE-20240329120000

python skillscripts/utils/call_tracer.py list \
  --limit 20 \
  --operation skill_call

python skillscripts/utils/call_tracer.py stats \
  --period 24h

python skillscripts/utils/call_tracer.py export \
  --format json \
  --output traces.json
```

---

## 最佳实践

### 1. 使用统一的调用接口

```python
from skillscripts.core.skill_caller import SkillCaller

caller = SkillCaller()

result = caller.call(
    target_type='script',
    target_name='auto_fixer',
    params={'target': './src'}
)
```

### 2. 添加超时和重试机制

```python
from skillscripts.core.skill_caller import SkillCaller

caller = SkillCaller()

result = caller.call(
    target_type='script',
    target_name='auto_fixer',
    params={'target': './src'},
    options={
        'timeout': 60000,
        'retry': 3,
        'retry_delay': 1000
    }
)
```

### 3. 启用调用链追踪

```python
from skillscripts.core.skill_caller import SkillCaller

caller = SkillCaller(enable_tracing=True)

with caller.trace_context('my_operation'):
    result1 = caller.call(...)
    result2 = caller.call(...)
```

### 4. 处理调用失败

```python
from skillscripts.core.skill_caller import SkillCaller, CallError

caller = SkillCaller()

try:
    result = caller.call(
        target_type='script',
        target_name='auto_fixer',
        params={'target': './src'}
    )
except CallError as e:
    print(f"调用失败: {e.message}")
    print(f"错误码: {e.code}")
    print(f"可重试: {e.retryable}")
    
    if e.retryable:
        result = caller.retry(e.call_id)
```

### 5. 使用异步调用

```python
from skillscripts.core.skill_caller import SkillCaller

caller = SkillCaller()

future = caller.call_async(
    target_type='script',
    target_name='auto_fixer',
    params={'target': './src'},
    callback=lambda result: print(f"完成: {result}")
)

print("调用已提交，继续执行其他任务...")

result = future.wait(timeout=60000)
print(f"结果: {result}")
```

### 6. 配置降级策略

```python
from skillscripts.core.skill_caller import SkillCaller

caller = SkillCaller()

result = caller.call(
    target_type='script',
    target_name='auto_fixer',
    params={'target': './src'},
    fallback={
        'enabled': True,
        'action': 'use_cache',
        'cache_key': 'auto_fix_result'
    }
)
```

### 7. 批量调用优化

```python
from skillscripts.core.skill_caller import SkillCaller

caller = SkillCaller()

calls = [
    {'target_type': 'script', 'target_name': 'script1', 'params': {}},
    {'target_type': 'script', 'target_name': 'script2', 'params': {}},
    {'target_type': 'script', 'target_name': 'script3', 'params': {}},
]

results = caller.batch_call(calls, parallel=True, max_concurrent=3)

for i, result in enumerate(results):
    print(f"调用 {i+1}: {result['status']}")
```

---

## 常见问题

### Q: 调用超时如何处理？

```python
from skillscripts.core.skill_caller import SkillCaller, CallTimeoutError

caller = SkillCaller()

try:
    result = caller.call(
        target_type='script',
        target_name='long_running_script',
        params={},
        options={'timeout': 30000}
    )
except CallTimeoutError:
    print("调用超时，已自动取消")
```

### Q: 如何查看调用历史？

```python
from skillscripts.core.call_tracer import CallTracer

tracer = CallTracer()

history = tracer.get_call_history(
    caller='subskill:test',
    limit=10
)

for call in history:
    print(f"[{call.timestamp}] {call.target}: {call.status}")
```

### Q: 如何实现调用链传递？

```python
from skillscripts.core.skill_caller import SkillCaller

caller = SkillCaller()

context = caller.create_context(trace_id='TRACE-xxx')

result1 = caller.call(
    target_type='script',
    target_name='script1',
    params={},
    context=context
)

result2 = caller.call(
    target_type='script',
    target_name='script2',
    params={},
    context=context
)
```

---

## v4.0 更新

### 🔧 新模块协同架构

v4.0 在原有 `skillscripts/` 目录基础上新增了 **5大核心模块**，构建了完整的全生命周期技能协同体系。

#### v4.0 模块目录结构

```
skillscripts/
├── core/                          # 核心模块 (v4.0 新增/增强)
│   ├── operation_priority.py      # ⭐ 操作优先级控制器
│   ├── four_d_defense.py          # ⭐ 四维度输出防线
│   ├── resource_coordinator.py    # ⭐ MARC-Lite 资源协调器
│   ├── decision_log.py            # ⭐ 决策日志系统
│   ├── workflow_dsl_engine.py     # ⭐ YAML工作流DSL引擎
│   ├── evolution_*.py             # 演化系统 (已有)
│   └── provincial_coordinator.py  # 省部协调器 (已有)
│
├── security/                      # 🔐 安全模块 (v4.0 全新增)
│   ├── secrets_manager.py         # 密钥管理器
│   ├── hardcoded_detector.py      # 硬编码检测器
│   ├── config_security_auditor.py # 配置安全审计
│   └── env_template_generator.py  # 环境模板生成器
│
├── integration/                   # 🤝 集成模块 (v4.0 全新增)
│   ├── agency_bridge.py           # Agency Agents桥接层
│   └── ux_integration.py          # UI/UX协同集成
│
├── platform_adapter.py            # 💻 平台适配器 (v4.0 新增)
│
└── utils/                         # 工具模块 (已有)
    ├── path_config_manager.py
    ├── skill_caller.py
    └── call_tracer.py
```

#### 模块依赖关系图

```
                    ┌─────────────────────────────┐
                    │     v4.0 模块协同调用架构      │
                    └──────────────┬──────────────┘
                                   │
           ┌───────────────────────┼───────────────────────┐
           │                       │                       │
           ▼                       ▼                       ▼
   ┌───────────────┐     ┌───────────────┐     ┌───────────────┐
   │   入口层       │     │   核心层       │     │   安全层       │
   │               │     │               │     │               │
   │ Platform      │◄───►│ Operation     │     │ Secrets       │
   │ Adapter       │     │ Priority      │     │ Manager       │
   │               │     │ Controller    │     │               │
   │ [PS7/Bash     │     │       ▼       │     │ Hardcoded     │
   │  适配]        │     │  Four-D       │     │ Detector      │
   └───────────────┘     │  Defense       │     │               │
                         │  (4层防线)     │     └───────┬───────┘
                         │       │       │             │
                         │       ▼       │             ▼
                         │  Resource     │     ┌───────────────┐
                         │  Coordinator  │     │   集成层       │
                         │  (MARC-Lite)  │     │               │
                         │       │       │     │ Agency Bridge │
                         │       ▼       │     │               │
                         │  Workflow DSL │     │ UX Integration│
                         │  Engine       │     │               │
                         │       │       │     └───────┬───────┘
                         │       ▼       │             │
                         │  Decision Log │             ▼
                         └───────────────┘     ┌───────────────┐
                                               │   外部生态     │
                                               │ agency-agents  │
                                               │ ui-ux-pro-max  │
                                               └───────────────┘
```

#### 调用场景矩阵

| 场景 | 涉及模块 | 调用顺序 | 说明 |
|------|----------|----------|------|
| **代码生成全流程** | OpPriority → 4D-Defense → MARC → AgencyBridge | 1→2→3→4 | 最完整的调用链 |
| **安全初始化** | SecretsManager → HardcodedDetector | 1→2 | 项目启动安检 |
| **多Agent并行审查** | MARC → AgencyBridge → 4D-Defense(L3) | 1→2→3 | 并发资源协调 |
| **UI/UX驱动开发** | UXIntegration → 4D-Defense(L3) → OpPriority | 1→2→3 | 设计驱动实现 |
| **跨平台执行** | PlatformAdapter → OpPriority → MARC | 1→2→3 | PS7/Bash适配 |
| **决策追溯** | DecisionLog → WorkflowDSL | 1→2 | 决策记录+自动化 |
| **TDD+SDD融合** | 4D-Defense → DecisionLog → WorkflowDSL | 1→2→3 | 质量保障闭环 |

#### 典型调用链：操作优先级 → 四维防线 → MARC 联动

```python
"""最常用的完整调用链: Agent决定操作方式后经过四维防线检查，再通过MARC获取资源"""

from skillscripts.core.operation_priority import OperationPriorityController
from skillscripts.core.four_d_defense import FourDimensionalDefense
from skillscripts.core.resource_coordinator import ResourceCoordinator, ResourceType, LockType

def execute_task(task_context):
    # Step 1: 操作优先级决策
    priority_ctrl = OperationPriorityController()
    decision = priority_ctrl.decide(task_context)
    
    # Step 2: 如果是COMMAND类型，先做预演检查
    if decision.priority == "command":
        preflight = priority_ctrl.preflight_check(task_context.command)
        if preflight.risk_level == "HIGH":
            raise SecurityError(f"高风险命令被拦截: {preflight.blocked_patterns}")
    
    # Step 3: 四维防线检查
    defense = FourDimensionalDefense()
    defense_result = defense.run_full_check(task_context)
    
    if not defense_result.passed:
        return handle_fallback(defense_result)
    
    # Step 4: MARC资源协调
    marc = ResourceCoordinator()
    with marc.acquire_context(
        resource_id=task_context.target,
        agent_id=task_context.agent_id,
        lock_type=LockType.EXCLUSIVE if decision.priority == "manual" else LockType.SHARED
    ):
        result = execute_actual_task(task_context)
    
    return result
```

#### 安全校验链：SecretsManager → HardcodedDetector

```python
"""项目安全初始化的标准流程"""

from skillscripts.security.secrets_manager import SecretsManager
from skillscripts.security.hardcoded_detector import HardcodedDetector

def security_initialization(project_path):
    sm = SecretsManager()
    sm.load()  # .env → .env.local → os.environ → defaults
    
    validation = sm.validate_all()
    if not validation.is_valid:
        raise SecurityError(f"密钥验证失败: {validation.issues}")
    
    detector = HardcodedDetector()
    report = detector.scan_directory(project_path)
    
    critical_count = sum(1 for f in report.files 
                        for finding in f.findings 
                        if finding.severity in ["CRITICAL", "HIGH"])
    
    if critical_count > 0:
        detector.export_report_sarif(report, "reports/security.sarif")
        raise SecurityError(f"发现{critical_count}个严重安全问题!")
    
    detector.export_report_markdown(report, "reports/security_scan.md")
    return {"status": "secure", "secrets_loaded": len(sm._secrets)}
```

#### 跨生态协同：AgencyBridge → MARC → UXIntegration

```python
"""调用外部Agent进行全栈审查的完整流程"""

from skillscripts.integration.agency_bridge import AgencyBridge
from skillscripts.integration.ux_integration import UXIntegration
from skillscripts.core.resource_coordinator import ResourceCoordinator

def full_stack_review(project_path):
    bridge = AgencyBridge()
    marc = ResourceCoordinator()
    ux = UXIntegration()
    
    recommendations = bridge.recommend_agents(
        task_description="全栈代码审查: 前端React + 后端Python FastAPI + 安全审计"
    )
    
    agents_to_invoke = [r.agent_id for r in recommendations[:4]]
    
    results = bridge.invoke_agents_parallel(
        agent_ids=agents_to_invoke,
        task=f"审查项目 {project_path}",
        use_marc=True,
        context={"project_path": project_path}
    )
    
    aggregated = bridge.aggregate_results(results)
    
    if any("frontend" in r.agent_id.lower() for r in results):
        ux_rules = ux.search_ux_rules(domain="accessibility", query="contrast interaction")
        aggregated.add_metadata("ux_rules", ux_rules)
    
    return aggregated.to_markdown()
```

#### 决策自动化：DecisionLog + WorkflowDSL

```python
"""决策记录 + 工作流自动化组合使用"""

from skillscripts.core.decision_log import DecisionLog
from skillscripts.core.workflow_dsl_engine import WorkflowDSLEngine

def automated_decision_workflow():
    dec_log = DecisionLog(output_dir="docs/logs/decision_logs/")
    
    decision = dec_log.generate(
        title="采用事件驱动架构替代REST轮询",
        content="对于实时性要求高的模块，从REST轮询迁移到WebSocket+SSE",
        rationale=["减少API调用", "降低服务器负载", "提升实时性"],
        alternatives=[
            {"option": "保持REST轮询", "pros": "简单", "cons": "延迟高"},
            {"option": "WebSocket+SSE", "pros": "实时性好", "cons": "复杂度适中"}
        ],
        selected_option=1,
        impact_scope=["frontend", "backend", "infrastructure"],
        maker="架构设计局-系统架构司"
    )
    
    workflow_yaml = """
name: migration-to-event-driven
steps:
  - name: proof_of_concept
    type: single
    agent: engineering-senior-developer
  - name: parallel_review
    type: parallel
    steps:
      - name: frontend_review
        type: single
        agent: engineering-frontend-developer
      - name: backend_review
        type: single
        agent: engineering-backend-architect
  - name: conditional_deploy
    type: conditional
    variable: poc_success
    operator: equals
    value: true
    then_step:
      name: deploy_staging
      type: single
      agent: ops-engineer
on_error: retry_with_backoff
"""
    
    engine = WorkflowDSLEngine()
    workflow = engine.parse_workflow(workflow_yaml)
    validation = engine.validate_workflow(workflow)
    
    if validation.is_valid:
        execution_result = engine.execute_workflow(workflow)
        
        evaluation = dec_log.evaluate_outcome(
            decision_id=decision.id,
            effectiveness_score=0.85,
            lessons_learned="WebSocket方案显著降低了延迟",
            would_repeat=True
        )
        
        return {"decision": decision, "execution": execution_result, "evaluation": evaluation}
```

#### v4.0 模块推荐初始化顺序

```python
def initialize_v40_modules(project_root):
    """v4.0 模块推荐初始化顺序"""
    import os
    os.chdir(project_root)
    
    modules = {}
    
    # Phase 1: 基础设施（无依赖）
    from skillscripts.platform_adapter import PlatformAdapter
    modules["platform"] = PlatformAdapter()
    env_info = modules["platform"].detect_environment()
    
    # Phase 2: 安全基础（依赖Phase 1）
    from skillscripts.security.secrets_manager import SecretsManager
    modules["secrets"] = SecretsManager()
    modules["secrets"].load()
    
    from skillscripts.security.hardcoded_detector import HardcodedDetector
    modules["detector"] = HardcodedDetector()
    
    # Phase 3: 核心能力（依赖Phase 2）
    from skillscripts.core.operation_priority import OperationPriorityController
    modules["priority"] = OperationPriorityController()
    
    from skillscripts.core.four_d_defense import FourDimensionalDefense
    modules["defense"] = FourDimensionalDefense()
    
    from skillscripts.core.resource_coordinator import ResourceCoordinator
    modules["marc"] = ResourceCoordinator()
    
    # Phase 4: 高级功能（依赖Phase 3）
    from skillscripts.core.decision_log import DecisionLog
    modules["decisions"] = DecisionLog()
    
    from skillscripts.core.workflow_dsl_engine import WorkflowDSLEngine
    modules["workflow"] = WorkflowDSLEngine()
    
    from skillscripts.integration.agency_bridge import AgencyBridge
    modules["agency"] = AgencyBridge()
    
    from skillscripts.integration.ux_integration import UXIntegration
    modules["ux"] = UXIntegration()
    
    return modules
```

## 相关文档

- [持续演化系统](continuous_evolution.md)
- [自迭代机制](self_iteration.md)
- [路径配置管理](skill_path_management.md)
- [知识库管理](knowledge_base.md)
- [架构概览](architecture_overview.md) - v4.0核心组件详解
- [省部协调机制](provincial_coordination.md) - MARC-Lite集成说明
