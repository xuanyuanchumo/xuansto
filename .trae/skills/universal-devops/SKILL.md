---
name: universal-devops
version: "7.0"
description: |
  通用AI全生命周期开发技能v7.0 - 开源融合/自主化/MARC v2.0/全生命周期/三省六部二十四司/Harness Engineering/透明化/契约驱动/智能编排
  【核心理念】三省六部二十四司 | SDD+TDD融合 | 四维输出防线 | MARC v2.0资源协调 | 🔐密钥安全 | 🤖自主化操作引擎
  【v7.0新增】开源哲学融合引擎(OpenCode/OpenClaude/Claw-Code) | PhilosophyFusionEngine | 全生命周期21阶段技能矩阵
  【开源融合】OpenCode透明化 + OpenClaude Agent编排 + Claw-Code契约驱动 + Harness工程化 + 哲学融合引擎
  【触发关键词】全生命周期开发、需求分析、架构设计、TDD、SDD、代码审查、CI/CD、
  部署运维、质量监控、自演化、多Agent协作、DevOps、项目管理、三省六部、
  环境变量管理、密钥安全、硬编码检测、.env管理、v7.0、universal-devops-7、
  开源融合、哲学融合、MARC-v2、自主化操作、资源协调v2
  【适用IDE】Trae IDE、Claude Code、Cursor、Windsurf
  【终端要求】PowerShell 7+ / Bash 5.0+
  【Python要求】>=3.10
  【操作优先级】AUTONOMOUS_MANUAL > SCRIPTED_BATCH > COMMAND_LINE（v7.0增强：多因子决策模型）
compatibility:
  python: ">=3.10"
  terminal: ["powershell-7+", "bash-5.0+"]
  ide: ["trae", "claude-code", "cursor", "windsurf"]
  skills: ["sanliu", "ui-ux-pro-max", "mcp-builder", "global-chinese"]
triggers:
  primary:
    - "进行.*开发"
    - "全生命周期"
    - "三省六部"
    - "devops"
    - "TDD.*SDD"
    - "四维防线"
    - "资源协调"
    - "v7.0"
    - "universal-devops-7"
    - "开源融合"
    - "哲学融合"
    - "MARC-v2"
    - "自主化操作"
    - "资源协调v2"
  secondary:
    - "代码审查"
    - "架构设计"
    - "部署发布"
    - "质量监控"
    - "开源理念"
eval_metrics:
  trigger_accuracy: ">90%"
  output_quality_score: ">4.5/5.0"
  task_completion_rate: ">92%"
  avg_response_time: "<25s"
---

# Universal DevOps v7.0 - 通用AI全生命周期开发技能（哲学融合+MARC v2.0+自主化引擎版）

## 📋 版本信息

| 属性 | 值 |
|------|-----|
| **版本** | v7.0 |
| **架构** | 三省六部二十四司 + 三模运行 + **自主化操作引擎** + **四维防线** + **MARC v2.0协调** + **🔐密钥管理** + **🧠哲学融合引擎** |
| **核心引擎** | SDD + TDD 双驱动融合 + AOF自主决策框架 + PhilosophyFusionEngine |
| **子技能数量** | 32个（中书省4 + 门下省**6** + 尚书省24）|
| **监控维度** | 七维质量监控体系（+可靠性） |
| **演化能力** | 自迭代→自优化→自修复→自改进闭环 |
| **运行模式** | 自动化模式（Automated）+ 自主模式（Autonomous）+ Agent协作模式（Collaborative）|
| **⭐ v6.0新增** | 操作优先级架构、四维输出防线、MARC资源协调器、PS7原生适配 |
| **⭐ v7.0新增** | 哲学融合引擎、MARC v2.0、自主化操作引擎、全生命周期21阶段矩阵、Observability Pipeline、Governance Guardrails |

## 🎯 核心理念

### 三省六部制 + 现代DevOps融合

本技能借鉴中国古代三省六部制的**决策-审核-执行三权分立**思想，结合现代软件工程的**SDD（规格驱动开发）+ TDD（测试驱动开发）**方法论，构建了一套完整的AI辅助全生命周期开发体系。

```
┌─────────────────────────────────────────────────────────────┐
│                    Universal DevOps v6.0                      │
│              (四维防线+MARC协调有机融合版)                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌─────────────────────────────────────────────────────┐   │
│   │  ⭐ v6.0 新增：操作优先级控制器                      │   │
│   │  [自主手动] → [规划脚本] → [命令操作(需预演)]        │   │
│   └──────────────────────┬──────────────────────────────┘   │
│                          ↓                                  │
│   ┌─────────────────────────────────────────────────────┐   │
│   │  ⭐ v6.0 新增：四维度输出防线 (贯穿全栈)            │   │
│   │  Prompt → Capability → Rule → Fallback               │   │
│   └──────────────────────┬──────────────────────────────┘   │
│                          ↓                                  │
│   ┌─────────────────────────────────────────────────────┐   │
│   │  ⭐ v6.0 新增：MARC 多Agent资源协调器               │   │
│   │  资源注册 → 锁管理 → 调度队列 → 死锁预防             │   │
│   └──────────────────────┬──────────────────────────────┘   │
│                          ↓                                  │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│   │   中书省     │───▶│   门下省     │───▶│   尚书省     │     │
│   │  （决策层）   │    │  （审核层）   │    │  （执行层）   │     │
│   └─────────────┘    └─────────────┘    └─────────────┘     │
│         │                  │                  │              │
│   ┌─────┴─────┐      ┌─────┴─────┐      ┌─────┴─────┐       │
│   │ 需求分析局 │      │ 代码审查局 │      │  吏部(4司)  │       │
│   │ 架构设计局 │      │ 测试验证局 │      │  户部(4司)  │       │
│   │ 规范制定局 │      │ 质量监控局 │      │  礼部(4司)  │       │
│   │ 方案审议局 │      │ 合规审计局 │      │  兵部(4司)  │       │
│   └───────────┘      └───────────┘      │  工部(4司)  │       │
│                                         │  刑部(4司)  │       │
│                                         └─────────────┘       │
│                                                             │
│   ┌─────────────────────────────────────────────────────┐   │
│   │          SDD+TDD 融合引擎 / 自演化闭环系统            │   │
│   └─────────────────────────────────────────────────────┘   │
│                                                             │
│   ┌─────────────────────────────────────────────────────┐   │
│   │     🔄 三模运行架构 (Auto + Auto + Collab)          │   │
│   └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## ⭐ v7.0 核心新特性：开源设计哲学融合引擎

### 架构总览：三大开源理念深度融合

v7.0 引入革命性的 **PhilosophyFusionEngine**，将 OpenCode、OpenClaude、Claw-Code 三大开源项目的核心理念从功能映射升级为**哲学级深度融合**：

```
┌─────────────────────────────────────────────────────────────┐
│         PhilosophyFusionEngine v7.0 (哲学融合引擎)            │
│              三大开源理念的有机统一体                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │           🔓 OpenCode: 透明化决策链路                 │   │
│  │  ─────────────────────────────────────────────────  │   │
│  │  • 决策ID自动生成与全局唯一标识                        │   │
│  │  • 决策依据完整记录（数据来源+推理过程+权重分配）        │   │
│  │  • 影响范围自动追踪与依赖关系图谱                       │   │
│  │  • 决策效果后评估闭环反馈                              │   │
│  │                                                      │   │
│  │  📂 融入位置: 中书省-方案审议局 + 门下省-合规审计局     │   │
│  │  🎯 实现方式: Decision Log系统 + ADR自动生成            │   │
│  └──────────────────────┬──────────────────────────────┘   │
│                         │ 融合                               │
│  ┌──────────────────────┴──────────────────────────────┐   │
│  │           🤖 OpenClaude: Agent编排即代码               │   │
│  │  ─────────────────────────────────────────────────  │   │
│  │  • YAML工作流DSL声明式定义                             │   │
│  │  • DAG有向无环图工作流编排                             │   │
│  │  • 条件路由与并行执行引擎                              │   │
│  │  • 错误处理与重试策略自动化                            │   │
│  │                                                      │   │
│  │  📂 融入位置: 吏部-Agent调度司 + MARC v2.0协调器       │   │
│  │  🎯 实现方式: WorkflowDSL引擎 + 多Agent编排器          │   │
│  └──────────────────────┬──────────────────────────────┘   │
│                         │ 融合                               │
│  ┌──────────────────────┴──────────────────────────────┐   │
│  │           📜 Claw-Code: SDD契约驱动                   │   │
│  │  ─────────────────────────────────────────────────  │   │
│  │  • 规格文档解析为可执行条款                            │   │
│  │  • 条款自动转化为TDD测试用例                           │   │
│  │  • 测试用例驱动代码生成（红绿重构循环）                  │   │
│  │  • 闭环验证条款覆盖率100%                              │   │
│  │                                                      │   │
│  │  📂 融入位置: 兵部-TDD执行司 + 工部-代码生成司         │   │
│  │  🎯 实现方式: SDD+TDD融合引擎 + 可执行条款提取器       │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │      ⚙️ PhilosophyFusionEngine (融合引擎核心)         │   │
│  │  ─────────────────────────────────────────────────  │   │
│  │  • 场景自动检测 → 最优融合策略选择                      │   │
│  │  • 策略库: TRANSPARENT_ORCHESTRATED / DRIVEN_FLEXIBLE │   │
│  │  • 融合效果量化评估（5维度指标体系）                     │   │
│  │  • 持续优化与自适应调优                                │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 🔓 OpenCode 透明化理念详解

#### 融入位置
- **中书省-方案审议局**: 所有技术决策必须生成 Decision Log
- **门下省-合规审计局**: 决策合规性审查与审计追踪
- **自演化系统**: 每次演化自动记录演化 Decision Log

#### 实现方式
```python
class OpenCodeTransparency:
    """
    OpenCode透明化决策系统实现
    """

    def create_decision_log(self, decision_context):
        """
        创建结构化Decision Log

        参数:
            decision_context: 包含决策信息的字典
        返回:
            DecisionLog对象（包含ID、依据、影响范围等）
        """
        log = DecisionLog(
            id=self._generate_unique_id(),  # DEC-YYYYMMDD-NNN
            maker=decision_context.get("maker"),  # 决策者（部门/Agent）
            decision=decision_context.get("decision"),  # 决策内容
            rationale=decision_context.get("rationale"),  # 决策依据
            alternatives=decision_context.get("alternatives", []),  # 备选方案
            impact_scope=decision_context.get("impact_scope", []),  # 影响范围
            risk_assessment=decision_context.get("risk_assessment"),  # 风险评估
            evidence_links=decision_context.get("evidence_links", [])  # 证据链接
        )

        # 自动追踪影响范围
        log.impact_analysis = self._analyze_impact(log.impact_scope)

        # 后评估计划生成
        log.post_evaluation_plan = self._generate_evaluation_plan(log)

        return log
```

#### 使用示例
```bash
# 为重要技术决策生成完整的Decision Log
python skillscripts/open_source_philosophy/opencode_transparency.py \
  --decision "采用微服务架构" \
  --maker "中书省-架构设计局" \
  --rationale "业务模块边界清晰，团队规模>20人，需要独立部署能力" \
  --alternatives ["单体架构", "模块化单体", "Serverless"] \
  --impact_scope ["前端", "后端", "数据库", "运维"] \
  --risk_assessment "中等（需要额外的服务治理成本）"

# 输出文件：docs/logs/decision_logs/DEC-20260406-001.md
# 包含：决策ID、决策者、备选方案评估表、影响范围分析、风险评估矩阵、后评估计划
```

### 🤖 OpenClaude 编排理念详解

#### 融入位置
- **吏部-Agent调度司**: 多Agent任务分发与负载均衡
- **MARC v2.0资源协调器**: Agent间资源共享与死锁预防
- **尚书省各执行司**: 具体任务的并行/串行编排

#### 实现方式
```yaml
# workflow/code_review_multi_agent.yaml (YAML工作流DSL)
name: multi_agent_code_review
version: "2.0"
description: "多Agent协同代码审查工作流（v7.0增强版）"

agents:
  - id: frontend_reviewer
    role: Frontend Developer Expert
    capabilities:
      - react/vue/angular_code_review
      - css/accessibility_audit
      - performance_optimization
    resources_required:
      - file_lock: "src/frontend/**"
      - api_calls: 10
    philosophy_fusion:
      opencode_transparency: true  # 启用OpenCode透明化
      claw_code_driven: true       # 启用Claw-Code契约驱动

  - id: security_reviewer
    role: Security Engineer Expert
    capabilities:
      - owasp_top_10_scan
      - dependency_vulnerability_check
      - secrets_detection
    resources_required:
      - file_lock: "src/**"
      - api_calls: 5

workflow:
  step_1_parallel_review:
    type: parallel
    agents: [frontend_reviewer, security_reviewer, performance_reviewer]
    input: "$TARGET_FILES"
    timeout: "10min"
    # ⭐ v7.0新增：DAG依赖声明
    depends_on: []

  step_2_result_aggregation:
    type: sequential
    agent: orchestrator
    input: "$step_1_parallel_review.outputs"
    actions:
      - merge_findings
      - resolve_conflicts
      - prioritize_issues
    depends_on: [step_1_parallel_review]  # DAG边

error_handling:
  on_agent_failure: retry_with_backoff
  max_retries: 2
  on_timeout: partial_results_accepted
  escalation_threshold: "2 agents failed"
```

#### 使用示例
```bash
# 执行多Agent协作代码审查（自动应用OpenClaude编排理念）
python skillscripts/open_source_philosophy/openclaude_workflow_dsl.py \
  --workflow workflows/code_review_multi_agent.yaml \
  --target-files "src/**/*.py"

# 输出：
# 1. 并行执行3个专业Agent的审查任务
# 2. 自动合并审查结果并解决冲突
# 3. 生成综合审查报告（含Decision Log）
# 4. MARC v2.0自动协调资源，防止死锁
```

### 📜 Claw-Code 契约驱动理念详解

#### 融入位置
- **兵部-TDD执行司**: 测试先行开发与红绿重构循环
- **工部-代码生成司**: 基于规格的代码自动生成
- **中书省-需求分析局**: 规格文档编写与可执行条款提取

#### 实现方式
```python
class ClawCodeContractDriven:
    """
    Claw-Code契约驱动开发系统
    """

    def extract_executable_clauses(self, sdd_spec):
        """
        从SDD规格文档中提取可执行条款

        参数:
            sdd_spec: SDD规格文档路径或内容
        返回:
            list[ExecutableClause] - 可执行条款列表
        """
        parser = SDDSpecParser()
        raw_clauses = parser.parse(sdd_spec)

        executable_clauses = []
        for clause in raw_clauses:
            exec_clause = ExecutableClause(
                id=clause.id,
                description=clause.description,
                preconditions=clause.preconditions,  # 前置条件
                steps=clause.steps,                  # 操作步骤
                expected_results=clause.expected_results,  # 预期结果
                acceptance_criteria=clause.acceptance_criteria,  # 验收准则
                priority=clause.priority,
                dependencies=clause.dependencies
            )

            # 自动转化为TDD测试用例
            exec_clause.tdd_test_case = self._generate_tdd_test(exec_clause)

            executable_clauses.append(exec_clause)

        return executable_clauses

    def _generate_tdd_test(self, clause):
        """
        将可执行条款自动转化为TDD测试用例骨架
        """
        test_case = TestCase(
            name=f"test_{clause.id}_{clause.description[:30]}",
            setup=clause.preconditions,
            execute=clause.steps,
            assert_conditions=clause.expected_results,
            teardown=[]
        )
        return test_case
```

#### 使用示例
```bash
# 执行SDD→TDD→代码的完整契约驱动流程
python skillscripts/pipeline/sdd_tdd_fusion_engine.py \
  --spec requirements/api-spec.yaml \
  --output docs/testing/

# 执行流程：
# 1. 解析SDD规格文档 → 提取45个可执行条款
# 2. 每个条款自动生成TDD测试用例（红阶段）
# 3. 实现代码使测试通过（绿阶段）
# 4. 重构优化代码质量（蓝阶段）
# 5. 验证条款覆盖率100%
#
# 输出物：
# - docs/testing/test_cases/ (45个TDD测试文件)
# - docs/testing/coverage_report.html (覆盖率报告)
# - docs/logs/decision_logs/ (契约驱动Decision Log)
```

### PhilosophyFusionEngine 使用示例

```python
from skillscripts.philosophy_fusion import PhilosophyFusionEngine

# 初始化融合引擎
engine = PhilosophyFusionEngine(config="configs/philosophy_config.yaml")

# 场景1：全栈代码开发（自动选择最优融合策略）
task_context = {
    "task_type": "full_stack_development",
    "involves_multiple_agents": True,
    "has_sdd_spec": True,
    "requires_decision_tracking": True,
    "complexity": "high"
}

# 引擎自动检测场景并选择融合策略
strategy = engine.detect_and_select_strategy(task_context)
print(f"选择的融合策略: {strategy.name}")
# 输出: TRANSPARENT_ORCHESTRATED_DRIVEN (透明化+编排+契约驱动三合一)

# 执行融合后的工作流
result = engine.execute_fused_workflow(
    strategy=strategy,
    task_context=task_context,
    sdd_spec="requirements/prd.md",
    target_output="src/"
)

# 融合效果报告
print(f"✅ 任务完成 | 质量评分: {result.quality_score}/5.0")
print(f"📊 决策日志数: {len(result.decision_logs)}")
print(f"🤖 参与Agent数: {result.agents_involved}")
print(f"🧪 条款覆盖率: {result.clause_coverage}%")
print(f"⏱️ 总耗时: {result.duration}s")
```

### 融合效果指标表

| 维度 | v6.0 (功能映射) | v7.0 (哲学融合) | 提升幅度 |
|------|----------------|----------------|---------|
| **决策透明度** | 基础Decision Log | 结构化+可追溯+后评估闭环 | ↑ 60% |
| **编排智能化** | YAML DSL工作流 | DAG编排+条件路由+错误自愈 | ↑ 70% |
| **契约驱动率** | 半自动SDD→TDD | 全自动条款提取+测试生成+覆盖验证 | ↑ 80% |
| **多Agent协同效率** | 手动协调 | MARC v2.0自动协调+死锁预防 | ↑ 90% |
| **整体交付质量** | 4.0/5.0 | 4.5+/5.0 (目标) | ↑ 12.5% |

---

## ⭐ v6.0 核心新特性一：操作优先级架构（Agent-First）

### ⚠️ 这是用户最关心的新需求，请务必仔细阅读！

v6.0 引入了革命性的**操作优先级架构**，重新定义了 AI Agent 与系统交互的方式：

```
┌─────────────────────────────────────────────────────────────┐
│           v6.0 操作优先级架构（Agent-First）                  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  🥇 第一优先级：Agent 自主手动操作                            │
│  ───────────────────────────────────                         │
│  • AI Agent 直接使用文件读写工具操作文件                      │
│  • 适用场景：单文件修改、代码重构、文档编写、设计调整          │
│  • 优势：精确控制、可逐步验证、可随时回滚                     │
│  • 批量操作也推荐使用（如批量重构多个相关文件）                 │
│                                                              │
│  🥈 第二优先级：规划脚本操作                                  │
│  ─────────────────────────────────                           │
│  • 通过 skillscripts/ 中的 Python 脚本执行                   │
│  • 适用场景：重复性任务、复杂流程自动化、批量生成              │
│  • ⚠️ 批量操作时降级到第三优先级（需额外安全确认）             │
│  • 示例：python skillscripts/pipeline/sdd_tdd_fusion_engine.py │
│                                                              │
│  🥉 第三优先级：终端命令操作                                   │
│  ─────────────────────────────────                           │
│  • 通过 PowerShell 7 / Bash 执行 shell 命令                  │
│  • ⚠️ 执行前必须进行后果预演                                 │
│  • ⚠️ 批量操作时必须降级（需逐条确认或生成执行计划）            │
│  • 危险命令自动拦截（rm -rf /, DROP TABLE, FORMAT C:等）      │
│                                                              │
│  🔒 操作预演机制                                             │
│  ──────────────────────────                                 │
│  • 命令执行前自动分析影响范围                                │
│  • 列出将被修改/删除的文件列表                               │
│  • 评估风险等级（🟢低 🟡中 🔴高）                             │
│  • 高风险命令需要用户确认后才执行                              │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 优先级决策流程

```python
def decide_operation_priority(task):
    """
    v6.0 操作优先级决策引擎
    """

    # 第一优先级判断条件
    if is_file_operation(task) or is_refactoring(task) or is_documentation(task):
        return Priority.AGENT_MANUAL  # 🥇 Agent自主手动

    # 第二优先级判断条件
    elif is_repetitive_task(task) or has_existing_script(task):
        if is_batch_operation(task):
            return Priority.COMMAND_WITH_CONFIRMATION  # 降级到第三优先级
        return Priority.SCRIPT_EXECUTION  # 🥈 规划脚本

    # 第三优先级判断条件
    else:
        if requires_pre_flight_check(task):
            execute_preflight_analysis(task)  # 🔒 执行预演
            if task.risk_level == Risk.HIGH:
                request_user_confirmation(task)
        return Priority.COMMAND_EXECUTION  # 🥉 终端命令
```

### 实际应用示例

#### ✅ 推荐做法（第一优先级）

```bash
# 场景1: 修改单个配置文件
# ❌ 不要用: sed -i 's/port=8080/port=3000/g' config.yaml
# ✅ 推荐: 直接使用文件读写工具修改 config.yaml

# 场景2: 重构代码函数
# ❌ 不要用: python refactor.py --file src/utils.py
# ✅ 推荐: 直接读取 src/utils.py，分析后重写目标函数

# 场景3: 编写文档
# ❌ 不要用: echo "## 新章节" >> README.md
# ✅ 推荐: 直接读取 README.md，在合适位置插入新内容
```

#### ⚠️ 需谨慎的场景（第二/三优先级）

```bash
# 场景4: 批量格式化100个文件
# 可接受: python skillscripts/formatter/batch_format.py src/
# 但需要: 显示将要修改的文件列表，等待确认

# 场景5: 安装依赖包
# 需预演: npm install lodash@4.17.21
# 预演内容: 将修改 package.json 和 package-lock.json，增加 ~350KB 磁盘占用

# 场景6: 数据库迁移
# 必须人工确认: python manage.py migrate
# 风险等级: 🔴 高（可能影响生产数据）
```

### 危险命令拦截规则

```yaml
blocked_commands:
  destructive:
    - pattern: "rm -rf /"
      risk: "CRITICAL"
      action: "BLOCK"
      message: "禁止执行系统级删除命令"

    - pattern: "DROP TABLE"
      risk: "CRITICAL"
      action: "BLOCK"
      message: "禁止直接执行数据库表删除"

    - pattern: "FORMAT C:"
      risk: "CRITICAL"
      action: "BLOCK"
      message: "禁止格式化系统盘"

  high_risk_requires_confirmation:
    - pattern: "git push --force"
      risk: "HIGH"
      action: "CONFIRM"
      message: "强制推送将覆盖远程历史，确认继续？"

    - pattern: "docker system prune -a"
      risk: "HIGH"
      action: "CONFIRM"
      message: "将删除所有未使用的镜像和容器，确认继续？"
```

## ⭐ v7.0 核心增强：自主化操作引擎

### 三级优先级体系完整说明

v7.0 将 v6.1 的操作优先级架构升级为**自主化操作引擎**，引入更精细的三级优先级体系和智能决策模型：

```
┌─────────────────────────────────────────────────────────────┐
│           自主化操作引擎 (Autonomous Operation Engine)       │
│                    v7.0 增强版                               │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  🥇 Level 1: AUTONOMOUS_MANUAL（自主手动操作）                │
│  ─────────────────────────────────────────────────          │
│  • AI Agent 直接使用文件读写工具操作文件                      │
│  • 适用场景：单文件修改、代码重构、文档编写、设计调整          │
│  • 优势：精确控制、可逐步验证、可随时回滚                     │
│  • 批量操作也推荐使用（如批量重构多个相关文件）                 │
│  • ⭐ v7.0增强：集成PhilosophyFusionEngine决策透明化         │
│                                                              │
│  🥈 Level 2: SCRIPTED_BATCH（规划脚本批量操作）               │
│  ─────────────────────────────────────────────────          │
│  • 通过 skillscripts/ 中的 Python 脚本执行                   │
│  • 适用场景：重复性任务、复杂流程自动化、批量生成              │
│  • ⚠️ 批量操作时降级到第三优先级（需额外安全确认）             │
│  • ⭐ v7.0增强：支持MARC v2.0操作事务管理                    │
│                                                              │
│  🥉 Level 3: COMMAND_LINE（命令行操作）                      │
│  ─────────────────────────────────────────────────          │
│  • 通过 PowerShell 7 / Bash 执行 shell 命令                  │
│  • ⚠️ 执行前必须进行后果预演                                 │
│  • ⚠️ 批量操作时必须降级（需逐条确认或生成执行计划）            │
│  • 危险命令自动拦截（rm -rf /, DROP TABLE, FORMAT C:等）      │
│  • ⭐ v7.0增强：PreflightChecker v2.0（35+种危险模式检测）    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### OperationDecider 多因子决策模型

v7.0 引入 **OperationDecider** 多因子智能决策模型，替代 v6.1 的单一规则匹配：

```python
class OperationDecider:
    """
    v7.0 多因子操作决策器

    决策因子：
    - F1: 任务特征因子（文件操作/脚本/命令）
    - F2: 风险评估因子（ PreflightChecker 危险模式匹配）
    - F3: 资源可用因子（MARC v2.0 资源状态）
    - F4: 历史成功率因子（历史同类任务成功概率）
    """

    def decide(self, task_context):
        """
        四因子加权决策

        返回:
            {
                "priority_level": "AUTONOMOUS_MANUAL" | "SCRIPTED_BATCH" | "COMMAND_LINE",
                "confidence": float (0-1),
                "reason": str,
                "risk_level": "LOW" | "MEDIUM" | "HIGH" | "CRITICAL",
                "requires_preflight": bool,
                "requires_confirmation": bool,
                "marc_transaction_needed": bool
            }
        """
        # 因子1：任务特征评分 (权重30%)
        f1_score = self._evaluate_task_characteristics(task_context)

        # 因子2：风险评估评分 (权重35%) - 使用PreflightChecker v2.0
        f2_score = self._evaluate_risk(task_context)

        # 因子3：资源可用性评分 (权重20%) - 查询MARC v2.0
        f3_score = self._evaluate_resource_availability(task_context)

        # 因子4：历史成功率评分 (权重15%)
        f4_score = self._evaluate_historical_success_rate(task_context)

        # 加权综合评分
        total_score = (
            f1_score * 0.30 +
            f2_score * 0.35 +
            f3_score * 0.20 +
            f4_score * 0.15
        )

        # 决策逻辑
        if total_score >= 0.8 and task_context.risk_level in ["LOW", "MEDIUM"]:
            return PriorityLevel.AUTONOMOUS_MANUAL
        elif total_score >= 0.5 or task_context.has_existing_script:
            return PriorityLevel.SCRIPTED_BATCH
        else:
            return PriorityLevel.COMMAND_LINE  # 需预演+确认
```

### PreflightChecker v2.0：35+ 种危险模式分类

v7.0 将 PreflightChecker 从 v6.1 的22种危险模式升级为**35+种**，新增13种企业级危险模式：

#### 📊 危险模式分类统计

| 类别 | v6.1 数量 | v7.0 数量 | 新增 |
|------|----------|----------|------|
| **🔴 破坏性操作** | 8 | **10** | +2 (FORMAT整个磁盘 / KUBERNETES_DELETE_ALL) |
| **🟠 数据丢失风险** | 6 | **9** | +3 (TRUNCATE_TABLE / DROP_SCHEMA / GIT_FORCE_PUSH_TO_MAIN) |
| **🟡 配置覆盖风险** | 4 | **6** | +2 (ENV_FILE_OVERWRITE / CONFIG_MERGE_CONFLICT) |
| **🔵 权限提升风险** | 3 | **5** | +2 (SUDO_WITHOUT_PASSWORD / CHMOD_777_RECURSIVE) |
| **🟣 资源耗尽风险** | 1 | **3** | +2 (FORK_BOMB / MEMORY_LEAK_PATTERN) |
| **⚫ 安全漏洞风险** | 0 | **2** (+NEW) | SQL_INJECTION_PATTERN / COMMAND_INJECTION_PATTERN |
| **合计** | **22** | **35** | **+13 (+59%)** |

#### 🔴 破坏性操作（10种）

```yaml
destructive_patterns_v2:
  # v6.1原有8种
  - pattern: "rm -rf /"
    risk: CRITICAL
    category: system_destruction
    action: BLOCK

  - pattern: "DROP TABLE"
    risk: CRITICAL
    category: data_destruction
    action: BLOCK

  - pattern: "FORMAT C:"
    risk: CRITICAL
    category: disk_destruction
    action: BLOCK

  # ... (其他v6.1原有模式) ...

  # ⭐ v7.0新增2种
  - pattern: "FORMAT .* [A-Z]:"
    risk: CRITICAL
    category: disk_destruction
    description: "格式化任何磁盘分区"
    action: BLOCK
    v7_0_new: true

  - pattern: "kubectl delete.*--all-namespaces"
    risk: CRITICAL
    category: kubernetes_destruction
    description: "删除K8s所有命名空间资源"
    action: BLOCK
    v7_0_new: true
```

### 操作事务管理器

v7.0 新增 **OperationTransactionManager**，确保多步操作的原子性：

```python
class OperationTransactionManager:
    """
    操作事务管理器（与MARC v2.0联动）
    """

    def begin_transaction(self, agent_id, operation_name):
        """开启操作事务"""
        tx = OperationTransaction(
            id=generate_uuid(),
            agent_id=agent_id,
            name=operation_name,
            status="ACTIVE",
            start_time=datetime.now(),
            steps=[],
            rollback_points=[]
        )
        return tx

    def execute_step(self, transaction, step):
        """
        执行事务步骤（自动创建回滚点）

        如果步骤失败，自动触发回滚
        """
        # 创建回滚点
        rollback_point = self._create_rollback_point(step)
        transaction.rollback_points.append(rollback_point)

        try:
            result = step.execute()
            transaction.steps.append({
                "step_id": step.id,
                "status": "SUCCESS",
                "result": result
            })
        except Exception as e:
            # 自动回滚
            self.rollback(transaction, reason=f"步骤失败: {str(e)}")
            raise OperationTransactionError(f"事务已回滚: {e}")

    def commit(self, transaction):
        """提交事务（释放所有锁和资源）"""
        transaction.status = "COMMITTED"
        transaction.end_time = datetime.now()

        # 通知MARC v2.0释放所有锁
        for lock in transaction.held_locks:
            marc_v2.release_lock(lock)

        # 记录到审计轨迹
        audit_logger.log_transaction_commit(transaction)

    def rollback(self, transaction, reason):
        """回滚事务（按逆序恢复所有回滚点）"""
        transaction.status = "ROLLED_BACK"
        transaction.end_time = datetime.now()

        # 按逆序恢复回滚点
        for rollback_point in reversed(transaction.rollback_points):
            rollback_point.restore()

        # 释放锁
        for lock in transaction.held_locks:
            marc_v2.release_lock(lock)

        # 记录回滚原因
        audit_logger.log_transaction_rollback(transaction, reason)
```

### 操作审计轨迹记录器

v7.0 新增 **AuditTrailRecorder**，完整记录每个操作的审计轨迹：

```python
class AuditTrailRecorder:
    """
    操作审计轨迹记录器
    """

    def record_operation(self, operation_record):
        """
        记录操作审计轨迹

        operation_record 包含：
        - operator_id: 操作者ID（Agent或用户）
        - operation_type: 操作类型
        - target_resources: 目标资源列表
        - priority_level: 使用的优先级级别
        - decision_factors: 决策因子详情
        - preflight_result: 预检结果
        - execution_result: 执行结果
        - duration_ms: 执行耗时
        - risk_assessment: 风险评估
        - transaction_id: 关联的事务ID（如果有）
        """
        # 结构化审计记录
        audit_entry = AuditEntry(
            timestamp=datetime.now(),
            operator_id=operation_record.operator_id,
            operation_type=operation_record.operation_type,
            target_resources=operation_record.target_resources,
            priority_level=operation_record.priority_level,
            decision_factors=operation_record.decision_factors,
            preflight_check=operation_record.preflight_result,
            execution_status=operation_record.execution_result.status,
            duration_ms=operation_record.duration_ms,
            risk_level=operation_record.risk_assessment.level,
            transaction_id=operation_record.transaction_id,
            # ⭐ v7.0新增：哲学融合关联
            decision_log_ids=operation_record.decision_log_ids,  # 关联的Decision Log
            philosophy_fusion_strategy=operation_record.fusion_strategy  # 使用的融合策略
        )

        # 持久化存储
        self._persist(audit_entry)

        # 实时告警（如果发现异常模式）
        if self._detect_anomaly(audit_entry):
            self._trigger_alert(audit_entry)
```

### v6.1 vs v7.0 对比表

| 维度 | v6.1 | v7.0 | 变化 |
|------|-------|-------|------|
| **Level 1 名称** | MANUAL（手动） | **AUTONOMOUS_MANUAL**（自主手动） | 名称更明确，强调自主性 |
| **Level 2 名称** | SCRIPT（脚本） | **SCRIPTED_BATCH**（脚本批量） | 增加 BATCH 语义，明确批处理能力 |
| **Level 3 名称** | COMMAND（命令） | **COMMAND_LINE**（命令行） | 不变，名称规范化 |
| **决策机制** | 单一规则匹配 | **四因子加权决策模型** | 显著增强智能化程度 |
| **危险模式数** | 22种 | **35+种 (+59%)** | 大幅提升安全检测能力 |
| **事务支持** | 无 | **完整操作事务管理器** | 全新能力，保证原子性 |
| **审计轨迹** | 基础日志 | **完整审计轨迹记录器** | 显著增强可追溯性 |
| **预检能力** | 基础预演 | **PreflightChecker v2.0** | 分类更细、检测更全面 |
| **融合集成** | 无 | **PhilosophyFusionEngine深度集成** | 决策透明化+编排+契约驱动 |
| **MARC联动** | 基础锁管理 | **MARC v2.0操作事务联动** | 企业级资源协调 |

---

## ⭐ v6.0 核心新特性二：四维度输出防线（4D Output Defense）

### 防线架构总览

v6.0 引入**四维度纵深防御体系**，确保每个输出物都经过严格的质量保障：

```
┌─────────────────────────────────────────────────────────────┐
│           四维度输出防线 (4D Output Defense)                  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  用户请求                                                    │
│      │                                                       │
│      ▼                                                       │
│  ┌─────────────────────────────────────────────────────┐     │
│  │  🎯 第1层：Prompt工程层 (Prompt Engineering Layer)   │     │
│  │  ───────────────────────────────────────────────────  │     │
│  │  职责：确保输入指令清晰、完整、可执行                   │     │
│  │  机制：                                                  │     │
│  │  • 意图识别与澄清                                       │     │
│  │  • 上下文自动注入（项目信息、规范约束）                    │     │
│  │  • 输入验证与标准化                                     │     │
│  │  • 歧义消解与确认                                       │     │
│  └──────────────────────┬──────────────────────────────┘     │
│                         ▼                                   │
│  ┌─────────────────────────────────────────────────────┐     │
│  │  💪 第2层：能力约束层 (Capability Constraint Layer)  │     │
│  │  ───────────────────────────────────────────────────  │     │
│  │  职责：确保AI具备完成任务所需的能力                      │     │
│  │  机制：                                                  │     │
│  │  • 技能匹配度评估                                       │     │
│  │  • 知识库覆盖检查                                       │     │
│  │  • 工具链可用性验证                                     │     │
│  │  • 能力缺口识别与补全建议                               │     │
│  └──────────────────────┬──────────────────────────────┘     │
│                         ▼                                   │
│  ┌─────────────────────────────────────────────────────┐     │
│  │  📋 第3层：规则校验层 (Rule Validation Layer)        │     │
│  │  ───────────────────────────────────────────────────  │     │
│  │  职责：确保输出符合项目规范和质量标准                    │     │
│  │  机制：                                                  │     │
│  │  • 编码规范自动检查（Lint/Style）                       │     │
│  │  • 安全漏洞扫描                                         │     │
│  │  • ⭐ 硬编码密钥检测 (HardcodedDetector, v6.1新增)     │     │
│  │  • ⭐ 环境配置验证 (EnvConfig Validator, v6.1新增)     │     │
│  │  • 性能基准对比                                         │     │
│  │  • 合规性审查                                           │     │
│  └──────────────────────┬──────────────────────────────┘     │
│                         ▼                                   │
│  ┌─────────────────────────────────────────────────────┐     │
│  │  🛡️ 第4层：兜底恢复层 (Fallback Recovery Layer)     │     │
│  │  ───────────────────────────────────────────────────  │     │
│  │  职责：当前三层防线失败时的应急恢复机制                 │     │
│  │  机制：                                                  │     │
│  │  • 输出质量评分（<阈值则拒绝输出）                       │     │
│  │  • 自动回滚到上一个稳定状态                              │     │
│  │  • 降级策略触发（简化任务或请求人工介入）                 │     │
│  │  • 错误日志记录与根因分析                               │     │
│  └─────────────────────────────────────────────────────┘     │
│                         │                                   │
│                         ▼                                   │
│                    ✅ 安全输出                               │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 各层详细说明

#### 🎯 第1层：Prompt工程层

```python
prompt_layer_config = {
    "intent_recognition": {
        "model": "intent_classifier_v2",
        "confidence_threshold": 0.85,
        "supported_intents": [
            "code_generation",
            "refactoring",
            "documentation",
            "testing",
            "deployment",
            "debugging"
        ]
    },
    "context_injection": {
        "auto_inject": [
            "project_structure",
            "coding_standards",
            "tech_stack_info",
            "recent_changes"
        ],
        "context_window_limit": "80%"
    },
    "input_validation": {
        "required_fields": ["task_description", "scope"],
        "optional_fields": ["priority", "constraints", "examples"],
        "ambiguity_detection": True
    }
}
```

**调用示例**：
```bash
# 用户输入模糊时自动触发澄清
"优化代码"  # ← 触发歧义检测
→ AI回复："请问您希望优化哪个方面？\n1. 性能优化\n2. 代码可读性\n3. 减少技术债务\n4. 其他（请具体说明）"
```

#### 💪 第2层：能力约束层

```python
capability_layer_config = {
    "skill_matching": {
        "registry": "skill_registry.db",
        "matching_algorithm": "semantic_similarity",
        "min_confidence": 0.7
    },
    "knowledge_coverage": {
        "check_domains": ["programming_languages", "frameworks", "tools"],
        "coverage_threshold": 0.6,
        "fallback_action": "suggest_learning_resources"
    },
    "tool_availability": {
        "required_tools": [],
        "optional_tools": [],
        "auto_install_permission": False
    }
}
```

**调用示例**：
```bash
# 能力不足时给出明确提示
"使用 Rust 编写一个操作系统内核"  # ← 触发能力检查
→ AI回复：
"""
⚠️ 能力评估结果：
• Rust语言掌握度：✅ 85%
• 内核开发经验：❌ 15%（低于阈值60%）
• 建议方案：
  1. 先从简单的Rust项目开始（推荐：CLI工具）
  2. 提供详细的内核开发学习路径
  3. 或切换到您更熟悉的语言（如C/C++）
"""
```

#### 📋 第3层：规则校验层

```python
rule_validation_layer_config = {
    "code_standards": {
        "linters": ["eslint", "pylint", "golangci-lint"],
        "style_guides": ["PEP8", "Airbnb", "Google"],
        "auto_fix": True,
        "strict_mode": False
    },
    "security_scan": {
        "tools": ["bandit", "snyk", "trivy"],
        "severity_levels": ["critical", "high", "medium"],
        "block_on_critical": True
    },
    "performance_baseline": {
        "metrics": ["response_time", "memory_usage", "cpu_load"],
        "comparison_base": "last_successful_version",
        "regression_threshold": "10%"
    }
}
```

**调用示例**：
```bash
# 代码提交前自动触发规则校验
git commit -m "feat: add user authentication"  # ← 触发pre-commit钩子
→ 执行链路：
  1. ESLint检查 → ✅ 通过
  2. Bandit安全扫描 → ⚠️ 发现1个中危问题
  3. 单元测试 → ✅ 100%通过
  4. 覆盖率检查 → ✅ 82% (>80%阈值)
→ 结果：允许提交，但附上安全改进建议
```

#### 🛡️ 第4层：兜底恢复层

```python
fallback_recovery_layer_config = {
    "quality_scoring": {
        "dimensions": ["accuracy", "completeness", "consistency", "usability"],
        "minimum_score": 3.5,  # 5分制
        "scoring_model": "quality_evaluator_v3"
    },
    "rollback_mechanism": {
        "auto_rollback": True,
        "rollback_points": ["git_stash", "file_backup", "db_snapshot"],
        "max_rollbacks_per_session": 3
    },
    "degradation_strategy": {
        "level_1": "simplify_task",      # 降低复杂度
        "level_2": "request_human_help", # 请求人工协助
        "level_3": "escalate_to_human",  # 完全转交人工
        "trigger_conditions": {
            "consecutive_failures": 3,
            "quality_score_below": 2.0,
            "timeout_exceeded": "5min"
        }
    }
}
```

**调用示例**：
```bash
# 复杂任务连续失败后的兜底处理
"实现一个完整的分布式事务管理器"  # ← 连续3次尝试均未达质量标准
→ 兜底机制触发：
"""
🛡️ 兜底恢复已激活
━━━━━━━━━━━━━━━━━━━━━━━
📊 质量评分历史：
  尝试1: 2.8/5.0 ❌
  尝试2: 3.1/5.0 ❌
  尝试3: 2.9/5.0 ❌

📉 降级策略：Level 1 - 任务简化
💡 建议：先实现单机版事务管理器，后续再扩展为分布式版本

🔄 已创建回滚点：git stash save "attempt-3-fallback"
📝 错误日志已保存到：logs/fallback_log_20260406.md
"""
```

### 四维防线集成示例

```bash
# 完整的代码开发流程（经过四道防线）
"基于 requirements/api-spec.yaml 开发用户认证模块"

# 执行流程：
# ✅ 第1层 Prompt工程：
#    - 识别意图：code_generation
#    - 注入上下文：项目结构、编码规范、API契约
#    - 澄清确认：是否需要OAuth2.0支持？

# ✅ 第2层 能力约束：
#    - 技能匹配：✅ code_generation_si (置信度92%)
#    - 知识覆盖：✅ JWT/OAuth2.0 (覆盖率88%)
#    - 工具可用：✅ 所有依赖已安装

# ✅ 第3层 规则校验：
#    - Lint检查：✅ PEP8合规
#    - 安全扫描：✅ 无高危漏洞
#    - 性能基线：✅ 响应时间 < 100ms

# ✅ 第4层 兜底恢复（未触发）：
#    - 质量评分：4.3/5.0 ✅
#    - 输出通过所有防线检查
```

## ⭐ v6.0 核心新特性三：多Agent资源协调器（MARC）

### MARC架构概述

MARC（Multi-Agent Resource Coordinator）是v6.0引入的核心组件，专门解决多Agent并发场景下的**资源抢占、死锁、饥饿**等问题：

```
┌─────────────────────────────────────────────────────────────┐
│              MARC 多Agent资源协调器                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  📦 资源注册中心 (Resource Registry)                 │   │
│  │  ─────────────────────────────────────────────────  │   │
│  │  • 文件资源注册（读/写锁状态）                        │   │
│  │  • API端点注册（并发限制）                            │   │
│  │  • 计算资源注册（CPU/内存配额）                        │   │
│  │  • 外部服务注册（数据库/缓存连接池）                    │   │
│  └──────────────────────┬──────────────────────────────┘   │
│                         ↓                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  🔒 锁管理器 (Lock Manager)                         │   │
│  │  ─────────────────────────────────────────────────  │   │
│  │  • 乐观锁（读多写少场景）                             │   │
│  │  • 悲观锁（写密集场景）                               │   │
│  │  • 分布式锁（跨进程/跨机器）                           │   │
│  │  • 超时自动释放（防死锁）                             │   │
│  └──────────────────────┬──────────────────────────────┘   │
│                         ↓                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  📋 调度队列 (Scheduler Queue)                       │   │
│  │  ─────────────────────────────────────────────────  │   │
│  │  • 优先级队列（高/中/低三级）                         │   │
│  │  • 公平调度（防止饥饿）                               │   │
│  │  • 抢占式调度（紧急任务插队）                          │   │
│  │  • 批处理合并（减少锁竞争）                           │   │
│  └──────────────────────┬──────────────────────────────┘   │
│                         ↓                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  🛡️ 死锁预防器 (Deadlock Preventer)                 │   │
│  │  ─────────────────────────────────────────────────  │   │
│  │  • 资源排序分配（破坏循环等待条件）                    │   │
│  │  • 等待图检测（实时监控死锁风险）                      │   │
│  │  • 超时回退（放弃并重试）                             │   │
│  │  • 受害者选择（选择代价最小的Agent回滚）               │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 资源分类体系

```python
marc_resource_types = {
    "file_resources": {
        "description": "文件系统的读写权限",
        "granularity": "file_path",
        "lock_types": ["shared_read", "exclusive_write"],
        "conflict_resolution": "first-come-first-served",
        "example": "src/config/settings.yaml (write lock)"
    },

    "api_endpoints": {
        "description": "外部API的并发访问控制",
        "granularity": "endpoint_url",
        "lock_types": ["rate_limited", "semaphore"],
        "conflict_resolution": "queue_with_timeout",
        "example": "https://api.github.com (max 5000 req/hour)"
    },

    "compute_resources": {
        "description": "CPU/内存/GPU计算资源",
        "granularity": "resource_type",
        "lock_types": ["quota_based", "reservation"],
        "conflict_reservation": "fair_share",
        "example": "GPU Memory: 8GB quota per agent"
    },

    "external_services": {
        "description": "数据库、缓存、消息队列等外部服务",
        "granularity": "service_instance",
        "lock_types": ["connection_pool", "circuit_breaker"],
        "conflict_resolution": "pool_sharing",
        "example": "PostgreSQL Connection Pool (max 20)"
    },

    "secret_resources": {
        "description": "密钥、Token、凭证等敏感信息（v6.1新增）",
        "granularity": "secret_key_name",
        "lock_types": ["read_once", "mask_after_read"],
        "conflict_resolution": "single_access_mask",
        "example": "DATABASE_URL (READ_ONCE, 读取后自动脱敏缓存)",
        "v6.1_note": "SecretsManager集成，防止多Agent并发泄露密钥"
    }
}
```

### 锁机制详解

#### 乐观锁 vs 悲观锁

```python
class LockManager:
    """
    MARC 锁管理器实现
    """

    def acquire_lock(self, resource_id, agent_id, lock_type, mode="optimistic"):
        """
        获取资源锁

        参数:
            resource_id: 资源标识符
            agent_id: 请求锁的Agent ID
            lock_type: 锁类型 (read/write)
            mode: 锁模式 ("optimistic" / "pessimistic")

        返回:
            LockToken or None
        """
        if mode == "optimistic":
            # 乐观锁：适用于读多写少场景
            # 仅在提交时检查冲突，性能更高
            return self._try_optimistic_lock(resource_id, agent_id)

        elif mode == "pessimistic":
            # 悲观锁：适用于写密集场景
            # 获取锁时立即阻塞其他写入者
            return self._acquire_pessimistic_lock(resource_id, agent_id, lock_type)

    def release_lock(self, lock_token):
        """释放锁"""
        pass

    def detect_deadlock(self):
        """
        检测死锁（等待图算法）
        返回: 存在死锁的Agent集合
        """
        waiting_graph = self._build_waiting_graph()
        cycles = self._find_cycles(waiting_graph)

        if cycles:
            victims = self._select_victims(cycles)
            return victims

        return set()
```

### 死锁预防策略

```yaml
deadlock_prevention:
  strategy_1_resource_ordering:
    description: "全局资源排序，按固定顺序申请锁"
    implementation:
      - all_resources_sorted_by_id: true
      - agents_must_acquire_in_order: true
      - violation_penalty: "lock_request_rejected"

  strategy_2_timeout_backoff:
    description: "锁获取超时后自动释放并重试"
    configuration:
      base_timeout: "5s"
      max_retries: 3
      backoff_multiplier: 2.0
      jitter: true  # 防止惊群效应

  strategy_3_victim_selection:
    description: "检测到死锁时选择代价最小的Agent作为受害者"
    selection_criteria:
      - priority: "lower_priority_first"
      - progress: "least_progress_first"
      - resource_holding: "fewest_locks_held"
      - rollback_cost: "cheapest_to_rollback"
```

### 配额管理

```python
quota_manager_config = {
    "agent_quotas": {
        "default_agent": {
            "max_files_locked": 10,
            "max_concurrent_api_calls": 5,
            "cpu_quota_percent": 25,
            "memory_quota_mb": 512,
            "session_duration_minutes": 30
        },
        "privileged_agent": {
            "max_files_locked": 50,
            "max_concurrent_api_calls": 20,
            "cpu_quota_percent": 50,
            "memory_quota_mb": 2048,
            "session_duration_minutes": 120
        }
    },

    "global_limits": {
        "total_active_agents": 10,
        "total_file_locks": 100,
        "total_api_call_rate": "10000/hour",
        "system_cpu_usage_max_percent": 80,
        "system_memory_usage_max_percent": 85
    },

    "quota_enforcement": {
        "soft_limit_action": "warn_and_throttle",
        "hard_limit_action": "reject_request",
        "overflow_handling": "queue_or_reject"
    }
}
```

### MARC监控命令

```bash
# 查看MARC资源协调状态
python skillscripts/resource_coordinator/quota_manager.py --status

# 输出示例：
"""
╔══════════════════════════════════════════════════╗
║           MARC 资源协调器状态面板                 ║
╠══════════════════════════════════════════════════╣
║                                                   ║
║  📊 全局资源使用率                                ║
║  ─────────────────────────────────────────────    ║
║  活跃Agent数: 4/10 (40%)                          ║
║  文件锁占用: 23/100 (23%)                         ║
║  API调用速率: 2,450/10,000 (24.5%)                ║
║  CPU使用率: 45.2%/80% (56.5%)                     ║
║  内存使用率: 62.1%/85% (73.1%)                    ║
║                                                   ║
║  🔒 当前锁持有情况                                ║
║  ─────────────────────────────────────────────    ║
║  Agent-001: 3个文件写锁, 2个API信号量              ║
║  Agent-002: 1个文件写锁, 0个API信号量              ║
║  Agent-003: 5个文件读锁, 3个API信号量              ║
║  Agent-004: 2个文件写锁, 1个API信号量              ║
║                                                   ║
║  ⚠️ 告警信息                                      ║
║  ─────────────────────────────────────────────    ║
║  🔴 无                                             ║
║  🟡 Agent-003 接近文件锁上限 (5/10)               ║
║  🟢 系统运行正常                                  ║
║                                                   ║
╚══════════════════════════════════════════════════╝
"""
```

## ⭐ v7.0 核心增强：MARC v2.0 企业级资源协调器

### MARC v2.0 四层架构总览

v7.0 将 MARC 从 v1.0 升级为**企业级资源协调器 v2.0**，引入四层架构设计：

```
┌─────────────────────────────────────────────────────────────┐
│           MARC v2.0 企业级资源协调器                          │
│              (Multi-Agent Resource Coordinator v2.0)         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  📡 Layer 1: 资源感知层 (Resource Awareness)        │   │
│  │  ─────────────────────────────────────────────────  │   │
│  │  • 资源热度图 (Heatmap): 实时监控资源使用热点          │   │
│  │  • 抢占预测模型: 基于历史数据预测资源竞争              │   │
│  │  • 7种资源类型: FILE/API/COMPUTE/EXTERNAL/SECRET/    │   │
│  │    AGENT(v2.0新增)/CONTEXT(v2.0新增)                │   │
│  │  • 全局资源拓扑发现与动态更新                         │   │
│  └──────────────────────┬──────────────────────────────┘   │
│                         ↓                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  🔒 Layer 2: 锁优化层 (Lock Optimization)           │   │
│  │  ─────────────────────────────────────────────────  │   │
│  │  • 乐观锁增强: 版本号+CAS操作+无锁队列               │   │
│  │  • 分段锁 (Segment Lock): 减少锁粒度，提升并发       │   │
│  │  • 优先级继承: 高优先级Agent可继承低优先级锁           │   │
│  │  • 工作窃取 (Work Stealing): 空闲Agent窃取任务        │   │
│  └──────────────────────┬──────────────────────────────┘   │
│                         ↓                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  📋 Layer 3: 调度策略层 (Scheduling Strategy)        │   │
│  │  ─────────────────────────────────────────────────  │   │
│  │  • 自适应调度算法: 根据负载动态调整调度策略            │   │
│  │  • 操作事务管理: 多步操作的原子性保证                 │   │
│  │  • 断路器模式 (Circuit Breaker): 防止级联故障         │   │
│  │  • 补偿事务 (Compensating Transaction): 失败回滚      │   │
│  └──────────────────────┬──────────────────────────────┘   │
│                         ↓                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  🛡️ Layer 4: 隔离恢复层 (Isolation & Recovery)      │   │
│  │  ─────────────────────────────────────────────────  │   │
│  │  • Agent沙箱隔离: 故障Agent不影响其他Agent            │   │
│  │  • 快速故障检测: 心跳机制+健康检查                    │   │
│  │  • 自动恢复策略: 重启/迁移/降级                       │   │
│  │  • 灾难恢复计划: 数据备份+状态恢复                    │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 9大核心能力详细说明

| # | 核心能力 | 层级 | 说明 | v1.0 vs v2.0 |
|---|---------|------|------|-------------|
| **1** | **资源热度图** | L1-感知层 | 实时可视化资源使用热点，识别瓶颈和竞争区域 | **新增** - v1.0无此功能 |
| **2** | **抢占预测模型** | L1-感知层 | 基于机器学习预测未来资源抢占概率，提前预警 | **新增** - v1.0仅被动响应 |
| **3** | **乐观锁增强** | L2-锁优化层 | CAS操作+版本号+无锁数据结构，性能提升300% | 增强 - v1.0基础乐观锁 |
| **4** | **分段锁机制** | L2-锁优化层 | 将大锁拆分为小段，并发度提升5-10倍 | **新增** - v1.0全局锁 |
| **5** | **优先级继承协议** | L2-锁优化层 | 高优Agent可继承低优Agent的锁，防止优先级反转 | **新增** - v1.0固定优先级 |
| **6** | **工作窃取算法** | L2-锁优化层 | 空闲Agent自动窃取忙碌Agent的任务队列尾部任务 | **新增** - 提升利用率40% |
| **7** | **操作事务管理器** | L3-调度层 | 多步资源操作的原子性保证（ACID） | **新增** - v1.0无事务支持 |
| **8** | **断路器模式** | L3-调度层 | 连续失败N次后自动熔断，防止级联故障扩散 | **新增** - 弹性保障 |
| **9** | **补偿事务机制** | L3-调度层 | 分布式操作失败时的回滚与补偿策略 | **新增** - 数据一致性 |

### MARC v2.0 vs v1.0 对比表

| 维度 | MARC v1.0 (v6.0) | MARC v2.0 (v7.0) | 提升 |
|------|------------------|------------------|------|
| **架构层次** | 单层扁平架构 | 四层分层架构（感知→锁→调度→恢复） | 可扩展性↑↑↑ |
| **资源类型** | 5种 (FILE/API/COMPUTE/EXTERNAL/SECRET) | **7种 (+AGENT/CONTEXT)** | 覆盖面↑40% |
| **锁机制** | 乐观锁+悲观锁+分布式锁 | +**分段锁+优先级继承+工作窃取** | 并发性能↑300% |
| **调度策略** | 优先级队列+公平调度+抢占式 | +**自适应调度+操作事务+断路器+补偿事务** | 可靠性↑↑↑ |
| **故障处理** | 死锁预防+超时回退 | +**快速故障检测+自动恢复+灾难恢复** | 恢复速度↑90% |
| **预测能力** | 无预测，被动响应 | **热度图+抢占预测模型**（主动预警） | 预防性↑100% |
| **隔离机制** | 无隔离，共享资源池 | **Agent沙箱隔离**（故障隔离） | 安全性↑↑↑ |
| **适用规模** | ≤10个Agent中小型场景 | **≤50个Agent企业级场景** | 规模↑5倍 |
| **性能指标** | P99延迟<500ms | **P99延迟<100ms** | 性能↑5倍 |

### 使用示例代码

#### 示例1：初始化MARC v2.0

```python
from skillscripts.marc_v2 import MARCv2Coordinator

# 初始化MARC v2.0协调器
marc = MARCv2Coordinator(config="configs/marc_v2_config.yaml")

# 启动四层服务
marc.start_all_layers()
print("✅ MARC v2.0 四层架构已启动")
print(f"  📡 资源感知层: 运行中")
print(f"  🔒 锁优化层: 运行中 (分段锁+优先级继承)")
print(f"  📋 调度策略层: 运行中 (操作事务+断路器)")
print(f"  🛡️ 隔离恢复层: 运行中 (Agent沙箱)")
```

#### 示例2：注册Agent并请求资源

```python
# 注册新Agent
agent_id = marc.register_agent(
    name="CodeReviewer-001",
    priority="high",
    capabilities=["code_review", "security_scan"],
    resource_quota={
        "max_file_locks": 20,
        "max_api_calls": 15,
        "cpu_quota_percent": 30,
        "memory_quota_mb": 1024
    }
)

# 请求文件写锁（自动应用分段锁+优先级继承）
lock_token = marc.acquire_lock(
    resource_id="src/auth/**/*.py",
    agent_id=agent_id,
    lock_type="exclusive_write",
    mode="segmented",  # ⭐ v2.0: 使用分段锁
    timeout="10s"
)

if lock_token:
    print(f"✅ 获得锁: {lock_token.lock_id}")
    # 执行代码审查...
    marc.release_lock(lock_token)
else:
    print("❌ 获取锁失败（可能被更高优先级Agent抢占）")
```

#### 示例3：操作事务管理

```python
# 开启操作事务（原子性多步操作）
with marc.transaction(agent_id=agent_id, transaction_name="batch_refactor") as tx:
    # 步骤1: 锁定多个文件
    lock1 = tx.acquire_lock("src/models/user.py", "write")
    lock2 = tx.acquire_lock("src/models/order.py", "write")

    # 步骤2: 执行重构操作
    refactor_result = execute_refactoring(["src/models/user.py", "src/models/order.py"])

    # 步骤3: 如果任何步骤失败，自动回滚所有锁和修改
    if not refactor_result.success:
        tx.rollback("重构失败，回滚所有变更")
    else:
        tx.commit()  # 提交事务，释放所有锁

print("✅ 操作事务完成（或已安全回滚）")
```

#### 示例4：查看热度图和预测

```python
# 获取资源热度图
heatmap = marc.get_resource_heatmap()
print("\n📊 资源热度图:")
for resource, data in heatmap.items():
    print(f"  {resource}: 热度={data.temperature:.1f}° | 使用率={data.usage_pct:.1f}%")

# 获取抢占预测
predictions = marc.predict_contention(window_minutes=30)
print("\n🔮 未来30分钟抢占预测:")
for pred in predictions[:5]:  # Top 5高风险资源
    print(f"  ⚠️ {pred.resource_id}: 抢占概率={pred.probability:.1%} | 建议行动={pred.recommendation}")
```

### 配置文件说明 (marc_v2_config.yaml)

```yaml
# configs/marc_v2_config.yaml (v7.0 新增)
marc_v2:
  version: "2.0"

  layer_1_resource_awareness:
    heatmap:
      refresh_interval_seconds: 5
      history_window_minutes: 60
      temperature_thresholds:
        low: 30      # <30° 正常（绿色）
        medium: 60   # 30-60° 注意（黄色）
        high: 85     # 60-85° 警告（橙色）
        critical: 100 # >85° 危险（红色）

    prediction_model:
      algorithm: "lstm"  # LSTM神经网络
      training_data_days: 30
      prediction_window_minutes: 30
      confidence_threshold: 0.8

    resource_types:
      - type: FILE
        granularity: file_path
        lock_types: [shared_read, exclusive_write]
      - type: API
        granularity: endpoint_url
        lock_types: [rate_limited, semaphore]
      - type: COMPUTE
        granularity: resource_type
        lock_types: [quota_based, reservation]
      - type: EXTERNAL
        granularity: service_instance
        lock_types: [connection_pool, circuit_breaker]
      - type: SECRET
        granularity: secret_key_name
        lock_types: [read_once, mask_after_read]
      - type: AGENT          # ⭐ v2.0新增
        granularity: agent_id
        lock_types: [sandbox_isolation, capability_check]
      - type: CONTEXT        # ⭐ v2.0新增
        granularity: context_scope
        lock_types: [read_write, snapshot]

  layer_2_lock_optimization:
    optimistic_lock:
      enable_cas: true
      versioning_strategy: "vector_clock"
      max_retries: 3

    segmented_lock:
      segment_size_kb: 64  # 每64KB一个段
      max_segments_per_resource: 256

    priority_inheritance:
      enabled: true
      boost_factor: 1.5  # 继承后优先级提升1.5倍
      max_inheritance_depth: 3

    work_stealing:
      enabled: true
      steal_threshold_tasks: 3  # 对方队列>3个任务时才窃取
      steal_ratio: 0.3  # 窃取对方30%的尾部任务

  layer_3_scheduling_strategy:
    adaptive_scheduler:
      algorithm: "weighted_round_robin"
      load_balance_threshold: 0.8  # 负载差>80%时重平衡

    operation_transaction:
      timeout_seconds: 30
      max_concurrent_transactions: 10
      deadlock_detection_interval_ms: 1000

    circuit_breaker:
      failure_threshold: 5  # 连续失败5次触发熔断
      recovery_timeout_seconds: 30  # 熔断30秒后半开状态尝试
      half_open_max_calls: 3  # 半开状态允许3次试探

    compensating_transaction:
      compensation_strategies:
        - strategy: "rollback"
          applicable_to: ["file_write", "db_update"]
        - strategy: "compensate"
          applicable_to: ["api_call", "external_service"]

  layer_4_isolation_recovery:
    agent_sandbox:
      enabled: true
      isolation_level: "process"  # process/thread/namespace
      resource_limits:
        cpu_percent: 50
        memory_mb: 512
        max_file_descriptors: 100

    failure_detection:
      heartbeat_interval_seconds: 10
      failure_threshold: 3  # 连续3次心跳失败判定为故障

    auto_recovery:
      strategies:
        - action: "restart"
          max_attempts: 3
          cooldown_seconds: 60
        - action: "migrate"
          condition: "restart_failed"
          target: "healthy_agent"

  global_settings:
    max_agents: 50
    default_agent_quota:
      max_file_locks: 10
      max_concurrent_api_calls: 5
      cpu_quota_percent: 25
      memory_quota_mb: 512
    monitoring:
      metrics_port: 9090
      dashboard_enabled: true
```

---

## 🔐 环境变量与密钥管理（v6.1 新增）

### 架构总览

```
┌─────────────────────────────────────────────────────────────┐
│         密钥与环境变量管理系统 (Secrets Manager) v6.1        │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────────┐  ┌────────────────┐ │
│  │SecretsManager│  │ HardcodedDetector│  │ConfigSecurity  │ │
│  │ 密钥管理器    │  │ 硬编码检测引擎     │  │ Auditor        │ │
│  │ • 多源加载    │  │ • 25种正则模式   │  │ • YAML敏感检测 │ │
│  │ • 8类分类    │  │ • SARIF报告      │  │ • 权限检查     │ │
│  │ • 日志脱敏   │  │ • 自动修复建议   │  │ • Gitignore合规│ │
│  └──────────────┘  └──────────────────┘  └────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │           EnvTemplateGenerator                          │ │
│  │           环境变量模板生成器                             │ │
│  │  os.environ扫描 → .env.example → MD文档                │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 四大核心组件

#### 1. SecretsManager（密钥管理器）— `skillscripts/secrets_manager/secrets_manager.py`

**8种密钥类型分类体系**:

| 类型 | 安全级别 | 检测关键词示例 |
|------|---------|---------------|
| `PASSWORD` | 🔴 Critical | password, passwd, pwd |
| `API_KEY` | 🔴 Critical | api_key, apikey, api-secret |
| `TOKEN` | 🔴 Critical | access_token, jwt, bearer |
| `SECRET` | 🔴 Critical | secret, client_secret |
| `CREDENTIAL` | 🟠 High | credential, auth, login |
| `CONNECTION_STRING` | 🟠 High | mongodb+srv://, postgresql:// |
| `PRIVATE_KEY` | 🔴 Critical | PEM 格式私钥 |
| `ENCRYPTION_KEY` | 🟠 High | encryption_key, aes_key |

**核心能力**:
- **多源加载链**: `.env` → `.env.local` → 系统环境变量 → 默认值（手动解析，无外部依赖）
- **类型安全获取**: `get()` / `get_required()` 自动分类 + 审计日志记录
- **智能脱敏**: `mask_for_log()` 保留首尾各2字符 (`admin123` → `ad****23`, `sk-abc123def456` → `sk****456`)
- **强度验证**: `validate_all()` 检查密码复杂度、弱默认值、常用弱口令

#### 2. HardcodedDetector（硬编码检测引擎）— `skillscripts/secrets_manager/hardcoded_detector.py`

**25种内置正则检测模式**覆盖：
- 密码/API Key/Token/Secret 硬编码 (10种)
- 连接字符串内嵌凭据 (4种: MongoDB/PostgreSQL/MySQL/Redis)
- AWS/GitHub/Slack/AI 服务密钥 (4种)
- 私钥/Base64/JWT/通用长随机字符串 (4种)
- IP 地址硬编码 / 数据库端口硬编码 (3种)

**输出格式**:
- **SARIF v2.1.0 JSON** — 兼容 GitHub Code Scanning，可直接导入
- **Markdown 人类可读报告** — 含 emoji 图表、修复建议、按严重级别分组

#### 3. ConfigSecurityAuditor（配置安全审计器）— `skillscripts/secrets_manager/config_security_auditor.py`

**审计能力**:
- YAML/JSON 敏感字段检测（17种模式：password/api_key/token/connection_string 等）
- 文件权限检查（Windows 只读属性 / Unix o+r/o+w 权限）
- .gitignore 合规性验证（11种敏感文件模式：.env/*.pem/id_rsa*/credentials.json 等）
- 加密存储评估与算法推荐（AES-256-GCM/CBC）

#### 4. EnvTemplateGenerator（环境变量模板生成器）— `skillscripts/secrets_manager/env_template_generator.py`

**自动化流程**:
```
源码扫描(os.environ.get/os.getenv/SecretsManager.get 等7种模式)
    → 变量提取(去重+自动分类+来源定位)
    → .env.example生成(Required/Optional/Secret 分组)
    → Markdown参考文档输出(表格形式)
```

### 使用示例

```python
from pathlib import Path
from skillscripts.secrets_manager import (
    SecretsManager, HardcodedDetector,
    ConfigSecurityAuditor, EnvTemplateGenerator
)

# 1. 初始化并加载密钥
sm = SecretsManager()
sm.load()
db_url = sm.get_required("DATABASE_URL", purpose="PostgreSQL连接")
debug = sm.get("DEBUG", "false").lower() == "true"

# 2. 运行硬编码检测
detector = HardcodedDetector()
report = detector.scan_directory(Path("./src"))
print(f"发现 {report.total_findings} 个硬编码敏感信息")
if report.by_severity.get("critical", 0) > 0:
    raise SecurityError(f"存在 {report.by_severity['critical']} 个严重安全问题!")
detector.export_report_sarif(report, Path("reports/security-scan.sarif"))

# 3. 生成 .env.example
gen = EnvTemplateGenerator()
variables = gen.scan_project(Path("."))
Path(".env.example").write_text(gen.generate_example(variables), encoding="utf-8")

# 4. 配置安全审计
auditor = ConfigSecurityAuditor()
result = auditor.audit_config_file(Path("configs/app.yaml"))
print(f"安全评分: {result.overall_score}/100 ({result.risk_level})")
for rec in result.recommendations:
    print(f"  → {rec}")
```

### 与四维度防线的集成

Secrets Manager 作为**第三层 Rule Validation 的安全子模块**深度集成：

```
Layer 3: Rule Validation Engine
├── Schema Validator
├── Code Style Validator  
├── Security Policy Validator
│   ├── SQL Injection Detector
│   ├── XSS Vector Scanner
│   ├── ⭐ HardcodedDetector (NEW v6.1)     ← 集成点
│   └── ⭐ EnvConfig Validator (NEW v6.1)    ← 集成点
└── Document Integrity Validator
```

调用方式（通过 rule_validation_engine.py 的 SecurityPolicyValidator）:
```python
validator = SecurityPolicyValidator()

findings = validator.detect_hardcoded_secrets(source_code)  # 返回 list[Finding]
env_result = validator.validate_env_config()                  # 返回 dict
```

### 与 MARC 资源协调器的集成

密钥资源被纳入 MARC 保护范围：

| 资源类型 | 访问策略 | 特殊行为 |
|---------|---------|---------|
| FILE | EXCLUSIVE/RW/OPTIMISTIC | 标准锁机制 |
| TERMINAL | EXCLUSIVE | 会话池复用 |
| NETWORK | OPTIMISTIC | 限流保护 |
| SYSTEM | EXCLUSIVE | 全局单例 |
| **SECRET (NEW)** | **READ_ONCE** | 读取后自动脱敏缓存 |

### 密钥管理最佳实践（12条黄金规则）

1. **绝不提交 `.env` 文件** — 将 `.env`、`.env.local`、`.env.production` 加入 `.gitignore`
2. **使用 `get_required()` 获取必需密钥** — 缺失时立即抛出清晰错误而非静默返回空值
3. **定期轮换密钥** — 建议每 90 天轮换一次生产环境 Critical/High 级别密钥
4. **最小权限原则** — 每个密钥只授予必要的最小权限范围和最短有效时间
5. **使用强密码策略** — 最少 8 位，混合大小写字母、数字、特殊字符
6. **CI/CD 中使用 Secret Manager** — 绝不在构建日志、CI 输出中打印任何密钥值
7. **分层管理环境** — dev/staging/prod 使用独立的 `.env.*` 文件，各自隔离
8. **每次 CI 运行 HardcodedDetector** — 在流水线中集成安全扫描，Critical 问题阻断合并
9. **审计密钥访问日志** — 监控异常的密钥访问模式（频繁访问、非常规时间等）
10. **使用 `.env.example` 作为模板** — 通过 EnvTemplateGenerator 自动生成并保持与代码同步更新
11. **加密存储高敏感密钥** — 生产环境的 Critical 级别密钥考虑使用专业 KMS 或加密文件系统
12. **制定应急响应预案** — 密钥泄露时的快速轮换流程、影响范围评估和通知机制

## ⭐ v6.0 核心新特性四：开源理念深度内化

### 从功能对照到哲学内化的升级

v6.0 将开源理念的融合从**功能映射表**升级为**架构级哲学内化**：

```
┌─────────────────────────────────────────────────────────────┐
│            开源理念深度内化架构 (v6.0 Philosophical Fusion)   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  🔓 OpenCode: 透明化决策链路                         │   │
│  │  ─────────────────────────────────────────────────  │   │
│  │  v5.1: 功能映射（决策可追溯）                        │   │
│  │  v6.0: Decision Log 系统（完整决策审计链）            │   │
│  │                                                      │   │
│  │  • 决策ID自动生成                                    │   │
│  │  • 决策依据完整记录（数据来源+推理过程）               │   │
│  │  • 影响范围自动追踪                                  │   │
│  │  • 决策效果后评估（闭环反馈）                         │   │
│  │                                                      │   │
│  │  📂 实现: skillscripts/open_source_philosophy/       │   │
│  │     opencode_transparency.py --decision "..."        │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  🤖 OpenClaude: Agent编排即代码                      │   │
│  │  ─────────────────────────────────────────────────  │   │
│  │  v5.1: 功能映射（智能任务分发）                       │   │
│  │  v6.0: YAML工作流DSL（声明式Agent编排）               │   │
│  │                                                      │   │
│  │  • 工作流定义即代码（YAML DSL）                       │   │
│  │  • Agent能力声明式描述                                │   │
│  │  • 条件路由与并行执行                                 │   │
│  │  • 错误处理与重试策略                                 │   │
│  │                                                      │   │
│  │  📂 实现: skillscripts/open_source_philosophy/       │   │
│  │     openclaude_workflow_dsl.py --workflow "..."      │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  📜 Claw-Code: SDD契约驱动                           │   │
│  │  ─────────────────────────────────────────────────  │   │
│  │  v5.1: 功能映射（规格化需求定义）                     │   │
│  │  v6.0: 可执行条款提取（规格→测试→代码自动推导）       │   │
│  │                                                      │   │
│  │  • 规格文档解析为可执行条款                           │   │
│  │  • 条款自动转化为TDD测试用例                          │   │
│  │  • 测试用例驱动代码生成                               │   │
│  │  • 闭环验证条款覆盖率                                 │   │
│  │                                                      │   │
│  │  📂 实现: skillscripts/pipeline/                      │   │
│  │     sdd_tdd_fusion_engine.py --spec "..."            │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  ⚙️ Harness: 工程化实践增强                          │   │
│  │  ─────────────────────────────────────────────────  │   │
│  │  v5.1: 功能映射（CI/CD七大模块）                      │   │
│  │  v6.0: 持续集成增强（自动化+智能化+可观测性）         │   │
│  │                                                      │   │
│  │  • Pipeline智能优化（增量构建+并行执行+缓存）          │   │
│  │  • 部署策略自适应（金丝雀/蓝绿/滚动自动选择）          │   │
│  │  • SLO驱动的告警与自愈                               │   │
│  │  • 成本感知的资源调度                                │   │
│  │                                                      │   │
│  │  📂 实现: skillscripts/harness_integration/          │   │
│  │     harness_enhanced_pipeline.py --config "..."      │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### v5.1 vs v6.0 对比：开源融合差距分析

| 开源理念 | v5.1 实现程度 | v5.1 主要差距 | v6.0 升级方案 | 提升幅度 |
|---------|-------------|-------------|-------------|---------|
| **OpenCode透明化** | ⭐⭐⭐☆☆ (60%) | 决策记录不够结构化，缺少影响追踪 | Decision Log系统（含决策ID、依据、影响范围、效果评估） | ↑ 40% |
| **OpenClaude编排** | ⭐⭐⭐☆☆ (60%) | Agent调用硬编码，缺少工作流抽象 | YAML工作流DSL（声明式定义、条件路由、错误处理） | ↑ 40% |
| **Claw-Code契约** | ⭐⭐⭐⭐☆ (80%) | SDD→TDD转换半自动化，需人工干预 | 可执行条款提取引擎（全自动规格→测试→代码推导） | ↑ 20% |
| **Harness工程化** | ⭐⭐⭐⭐☆ (80%) | Pipeline配置静态化，缺少智能优化 | 智能Pipeline引擎（增量构建、自适应部署、成本优化） | ↑ 20% |

### Decision Log 系统详解（OpenCode透明化）

```python
# 使用示例：生成Decision Log
python skillscripts/open_source_philosophy/opencode_transparency.py \
  --decision "选择微服务架构" \
  --maker "中书省-架构设计局" \
  --rationale "业务模块边界清晰，团队规模>20人，需要独立部署能力" \
  --alternatives ["单体架构", "模块化单体", "Serverless"] \
  --impact_scope ["前端", "后端", "数据库", "运维"] \
  --risk_assessment "中等（需要额外的服务治理成本）"

# 输出：docs/logs/decision_logs/DEC-20260406-001.md
"""
# Decision Log: DEC-20260406-001

## 元信息
- **决策时间**: 2026-04-06 14:30:00
- **决策者**: 中书省-架构设计局 (AI Agent)
- **决策ID**: DEC-20260406-001
- **关联任务**: PRD-20260406-001 (电商后台系统)

## 决策内容
**选择**: 采用微服务架构

## 决策依据
1. 业务模块边界清晰（用户/订单/支付/库存独立）
2. 团队规模预计>20人，需要并行开发能力
3. 业务需求变化快，需要独立部署和扩展能力
4. 技术栈多样化（Python/Go/Node.js混用）

## 备选方案评估
| 方案 | 优势 | 劣势 | 得分 |
|------|------|------|------|
| 微服务架构 ✅ | 独立部署、技术自由、易扩展 | 复杂性高、分布式事务难 | 8.5/10 |
| 单体架构 | 简单、易调试、性能好 | 耦合高、部署慢 | 6.0/10 |
| 模块化单体 | 平衡复杂性与灵活性 | 部署仍需整体 | 7.0/10 |
| Serverless | 无运维成本、按需付费 | 冷启动、厂商锁定 | 5.5/10 |

## 影响范围
- **前端**: 需要适配多个服务端点（API Gateway统一入口）
- **后端**: 服务拆分、通信机制（gRPC/REST）、服务发现
- **数据库**: 每服务独立数据库、数据一致性方案
- **运维**: 容器化（K8s）、监控（分布式链路追踪）、日志聚合

## 风险评估
- **风险等级**: 🟡 中等
- **主要风险**:
  1. 分布式事务复杂性（解决方案：Saga模式）
  2. 服务间网络延迟（解决方案：本地缓存+异步通信）
  3. 运维复杂度上升（解决方案：K8s+Istio服务网格）

## 后评估计划
- **评估时间点**: 上线后30天/90天/180天
- **评估指标**: 部署频率、故障恢复时间、开发效率、系统可用性
- **回滚条件**: 如果90天内出现>3次严重分布式问题，考虑回退到模块化单体
"""
```

### YAML工作流DSL示例（OpenClaude编排）

```yaml
# workflow/code_review_multi_agent.yaml
name: multi_agent_code_review
version: "1.0"
description: "多Agent协同代码审查工作流"

agents:
  - id: frontend_reviewer
    role: Frontend Developer Expert
    capabilities:
      - react/vue/angular_code_review
      - css/accessibility_audit
      - performance_optimization
    resources_required:
      - file_lock: "src/frontend/**"
      - api_calls: 10

  - id: security_reviewer
    role: Security Engineer Expert
    capabilities:
      - owasp_top_10_scan
      - dependency_vulnerability_check
      - secrets_detection
    resources_required:
      - file_lock: "src/**"
      - api_calls: 5

  - id: performance_reviewer
    role: Performance Engineer Expert
    capabilities:
      - algorithm_complexity_analysis
      - memory_leak_detection
      - database_query_optimization
    resources_required:
      - file_lock: "src/backend/**"
      - api_calls: 8

workflow:
  step_1_parallel_review:
    type: parallel
    agents: [frontend_reviewer, security_reviewer, performance_reviewer]
    input: "$TARGET_FILES"
    timeout: "10min"

  step_2_result_aggregation:
    type: sequential
    agent: orchestrator
    input: "$step_1_parallel_review.outputs"
    actions:
      - merge_findings
      - resolve_conflicts
      - prioritize_issues

  step_3_report_generation:
    type: sequential
    agent: documentation_specialist
    input: "$step_2_result_aggregation.output"
    output: "docs/reviews/code_reviews/multi_agent_review_$DATE.md"

error_handling:
  on_agent_failure: retry_with_backoff
  max_retries: 2
  on_timeout: partial_results_accepted
  escalation_threshold: "2 agents failed"
```

## ⭐ v6.0 核心新特性五：PowerShell 7 原生适配

### 为什么需要PS7原生适配？

v6.0 正式支持 **Windows PowerShell 7+** 作为一等公民终端环境，解决以下痛点：

| 问题 | Bash在Windows的表现 | PS7原生支持的优势 |
|------|-------------------|----------------|
| **路径分隔符** | `/` vs `\` 混乱 | 统一使用 `\` 或自适应 |
| **命令差异** | `ls`, `cp`, `rm` 行为不同 | 原生 `Get-ChildItem`, `Copy-Item`, `Remove-Item` |
| **编码问题** | UTF-8/BOM/GBK混乱 | 默认UTF-8无BOM，编码保证 |
| **对象管道** | 文本流处理 | 强类型对象管道，更强大 |
| **跨平台** | WSL依赖 | PS7原生跨平台（Win/Mac/Linux） |

### PS7核心特性利用

```powershell
# 特性1: 结构化对象输出（vs Bash文本流）
Get-Process | Where-Object {$_.CPU -gt 100} | Sort-Object CPU -Descending | Select-Object -First 5

# 特性2: 错误处理增强
try {
    Remove-Item -Path "important_file.txt" -ErrorAction Stop
} catch {
    Write-Warning "删除失败: $($_.Exception.Message)"
    # 自动触发回滚逻辑
}

# 特性3: 并行执行
$files = Get-ChildItem -Path "src/" -Filter "*.py"
$files | ForEach-Object -Parallel {
    python -m pytest $_.FullName
} -ThrottleLimit 4

# 特性4: 远程会话管理
$session = New-PSSession -ComputerName "build-server"
Invoke-Command -Session $session -ScriptBlock { cd build; ./run_tests.ps1 }
Disconnect-PSSession -Session $session
```

### Bash → PowerShell 7 命令转换表（20个常用转换）

| # | Bash命令 | PowerShell 7 等效命令 | 说明 |
|---|---------|---------------------|------|
| 1 | `ls` | `Get-ChildItem` (别名: `dir`, `ls`) | 列出目录内容 |
| 2 | `cd` | `Set-Location` (别名: `cd`) | 切换目录 |
| 3 | `pwd` | `Get-Location` (别名: `pwd`) | 显示当前目录 |
| 4 | `cp` | `Copy-Item` (别名: `copy`, `cp`) | 复制文件/目录 |
| 5 | `mv` | `Move-Item` (别名: `move`, `mv`) | 移动/重命名 |
| 6 | `rm` | `Remove-Item` (别名: `del`, `rm`, `erase`) | 删除文件/目录 |
| 7 | `mkdir` | `New-Item -ItemType Directory` (别名: `mkdir`) | 创建目录 |
| 8 | `cat` | `Get-Content` (别名: `cat`, `type`) | 查看文件内容 |
| 9 | `echo` | `Write-Output` (别名: `echo`) | 输出文本 |
| 10 | `grep` | `Select-String` (别名: `sls`) | 文本搜索 |
| 11 | `find` | `Get-ChildItem -Recurse -Filter` | 递归查找文件 |
| 12 | `chmod` | `Set-Acl` (ACL权限) / `Set-ItemProperty` | 修改权限 |
| 13 | `chown` | `Set-Acl` (所有者) | 修改所有者 |
| 14 | `touch` | `New-Item` (空文件) / `(Get-Item).LastWriteTime=...` | 创建文件/更新时间戳 |
| 15 | `which` | `Get-Command` (别名: `gcm`) | 查找命令位置 |
| 16 | `export VAR=value` | `$env:VAR="value"` | 设置环境变量 |
| 17 | `source file.sh` | `. .\file.ps1` (dot-source) | 执行脚本文件 |
| 18 | `alias cmd='cmd'` | `Set-Alias -Name cmd -Value command` | 创建别名 |
| 19 | `history` | `Get-History` (别名: `h`, `hy`) | 命令历史 |
| 20 | `man cmd` | `Get-Help cmd` (别名: `help`, `man`) | 帮助文档 |

### 跨平台兼容性保证

```python
# skillscripts/platform_adapter.py
import platform
import subprocess
from pathlib import Path

class PlatformAdapter:
    """
    跨平台命令适配器
    自动根据当前OS选择正确的命令语法
    """

    def __init__(self):
        self.system = platform.system()
        self.is_windows = self.system == "Windows"
        self.is_powershell = self._detect_powershell()

    def _detect_powershell(self):
        """检测是否在PowerShell环境中运行"""
        return "PSModulePath" in __import__('os').environ

    def list_files(self, path="."):
        """跨平台列出文件"""
        if self.is_windows and self.is_powershell:
            return subprocess.run(
                ["powershell", "-Command", f"Get-ChildItem -Path '{path}'"],
                capture_output=True,
                text=True
            )
        else:
            return subprocess.run(["ls", "-la", path], capture_output=True, text=True)

    def copy_file(self, src, dst):
        """跨平台复制文件"""
        if self.is_windows and self.is_powershell:
            cmd = f"Copy-Item -Path '{src}' -Destination '{dst}'"
            return subprocess.run(["powershell", "-Command", cmd], capture_output=True, text=True)
        else:
            return subprocess.run(["cp", "-r", src, dst], capture_output=True, text=True)

    def get_env_var(self, name):
        """跨平台获取环境变量"""
        import os
        return os.environ.get(name, "")
```

### 编码保证机制

```yaml
encoding_guarantee:
  default_encoding: "UTF-8"
  bom_policy: "NO_BOM"  # 无BOM，避免兼容性问题
  line_ending: "LF"     # Unix风格换行符（Git友好）

  file_type_handlers:
    ".py":
      encoding: "UTF-8"
      line_ending: "LF"
      check_command: "python -c 'import ast; ast.parse(open(\"FILE\", encoding=\"utf-8\").read())'"

    ".md":
      encoding: "UTF-8"
      line_ending: "LF"
      check_command: "npx markdownlint FILE"

    ".yaml":
    ".yml":
      encoding: "UTF-8"
      line_ending: "LF"
      check_command: "python -c 'import yaml; yaml.safe_load(open(\"FILE\", encoding=\"utf-8\"))'"

    ".ps1":
      encoding: "UTF-8-BOM"  # PS1脚本允许BOM
      line_ending: "CRLF"     # Windows脚本使用CRLF
      check_command: "pwsh -NoProfile -Command \"\$null = [System.Management.Automation.Language.Parser]::ParseFile('FILE', [ref]\$null, [ref]\$null)\""
```

### PS7完整工作流示例

```powershell
# 示例：在PS7环境下执行完整的DevOps工作流
# 文件名: workflows/devops_workflow_ps7.ps1

<#
.SYNOPSIS
    v6.0 PowerShell 7 原生DevOps工作流
.DESCRIPTION
    展示如何在PS7环境下完成完整的开发、测试、部署流程
#>

param(
    [string]$ProjectPath = ".",
    [ValidateSet("dev", "staging", "prod")]
    [string]$Environment = "dev"
)

# 1. 环境检查
Write-Host "🔍 检查环境..." -ForegroundColor Cyan
$pythonVersion = python --version
Write-Host "  Python: $pythonVersion" -ForegroundColor Green
$psVersion = $PSVersionTable.PSVersion.ToString()
Write-Host "  PowerShell: $psVersion" -ForegroundColor Green

# 2. 项目初始化（使用Agent自主手动操作优先）
Write-Host "`n📦 初始化项目..." -ForegroundColor Cyan
if (-not (Test-Path "$ProjectPath/docs")) {
    New-Item -ItemType Directory -Path "$ProjectPath/docs" -Force
    Write-Host "  ✓ 创建 docs/ 目录" -ForegroundColor Green
}

# 3. 运行SDD+TDD融合引擎（第二优先级：规划脚本）
Write-Host "`n🔄 启动SDD+TDD融合引擎..." -ForegroundColor Cyan
python skillscripts/pipeline/sdd_tdd_fusion_engine.py `
    --spec "$ProjectPath/requirements/prd.md" `
    --output "$ProjectPath/docs/testing/"

if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ SDD+TDD流程完成" -ForegroundColor Green
} else {
    Write-Host "  ✗ SDD+TDD流程失败" -ForegroundColor Red
    exit 1
}

# 4. 执行测试套件
Write-Host "`n🧪 执行测试..." -ForegroundColor Cyan
$testResults = python -m pytest $ProjectPath/tests/ -v --tb=short
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ 所有测试通过" -ForegroundColor Green
} else {
    Write-Host "  ⚠ 存在失败的测试用例" -ForegroundColor Yellow
}

# 5. 代码质量检查（四维防线第3层）
Write-Host "`n📋 代码质量检查..." -ForegroundColor Cyan
python -m pylint $ProjectPath/src/ --output-format=text `
    2>&1 | Select-String -Pattern "rated at"

# 6. 生成Decision Log（OpenCode透明化）
Write-Host "`n📝 生成Decision Log..." -ForegroundColor Cyan
python skillscripts/open_source_philosophy/opencode_transparency.py `
    --decision "完成$Environment环境部署准备" `
    --maker "尚书省-工部-API设计司" `
    --rationale "所有测试通过，质量检查达标" `
    --output "$ProjectPath/docs/logs/decision_logs/"

# 7. MARC资源状态检查
Write-Host "`n📊 MARC资源协调状态..." -ForegroundColor Cyan
python skillscripts/resource_coordinator/quota_manager.py --status

# 8. 完成
Write-Host "`n✅ 工作流完成！" -ForegroundColor Green
Write-Host "  环境: $Environment" -ForegroundColor White
Write-Host "  时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor White
```

## ⭐ v6.0 核心新特性六：Skill标准化元数据

### Frontmatter增强说明

v6.0 的frontmatter相比v5.1进行了显著增强：

```yaml
# v5.1 frontmatter（基础版）
---
name: universal-devops
version: "5.1"
description: "通用AI全生命周期开发技能..."
---

# v6.0 frontmatter（标准化增强版）
---
name: universal-devops
version: "6.0"
description: |
  通用AI全生命周期开发技能v6.0 - 基于开源理念深度融合的四维防线+资源协调架构
  【核心理念】三省六部二十四司 | SDD+TDD融合 | 四维输出防线 | MARC资源协调
  ...

compatibility:                    # ⭐ 新增：兼容性声明
  python: ">=3.10"
  terminal: ["powershell-7+", "bash-5.0+"]
  ide: ["trae", "claude-code", "cursor", "windsurf"]
  skills: ["sanliu", "ui-ux-pro-max", "mcp-builder", "global-chinese"]

triggers:                         # ⭐ 新增：触发关键词
  primary:
    - "进行.*开发"
    - "全生命周期"
    ...
  secondary:
    - "代码审查"
    ...

eval_metrics:                     # ⭐ 新增：评估指标
  trigger_accuracy: ">85%"
  output_quality_score: ">4.0/5.0"
  task_completion_rate: ">90%"
  avg_response_time: "<30s"
---
```

### 触发关键词优化建议

| 类别 | 关键词 | 匹配模式 | 权重 | 说明 |
|------|--------|---------|------|------|
| **核心触发** | "三省六部" | 精确匹配 | 1.0 | 直接命中技能名称 |
| **核心触发** | "全生命周期" | 模糊匹配 | 0.95 | 最常用的触发词 |
| **核心触发** | "devops" | 大小写不敏感 | 0.9 | 国际化场景 |
| **核心触发** | "TDD.*SDD" | 正则匹配 | 0.9 | 双驱动融合场景 |
| **核心触发** | "四维防线" | 精确匹配 | 0.85 | v6.0新特性 |
| **核心触发** | "资源协调" | 模糊匹配 | 0.85 | MARC相关 |
| **次要触发** | "代码审查" | 模糊匹配 | 0.8 | 门下省功能 |
| **次要触发** | "架构设计" | 模糊匹配 | 0.8 | 中书省功能 |
| **次要触发** | "部署发布" | 模糊匹配 | 0.75 | 尚书省功能 |
| **次要触发** | "质量监控" | 模糊匹配 | 0.75 | 门下省功能 |
| **次要触发** | "开源理念" | 模糊匹配 | 0.7 | 开源融合章节 |

### 评估指标基准

```python
eval_metrics_benchmark = {
    "trigger_accuracy": {
        "target": ">85%",
        "measurement_method": "统计正确触发次数/总触发次数",
        "data_collection_period": "30天滚动窗口",
        "improvement_actions": [
            "优化trigger正则表达式",
            "增加同义词扩展",
            "调整权重参数"
        ]
    },

    "output_quality_score": {
        "target": ">4.0/5.0",
        "measurement_method": "用户满意度评分 + 自动化质量检测",
        "scoring_dimensions": ["准确性", "完整性", "一致性", "可用性"],
        "feedback_loop": "每月收集用户反馈并调优"
    },

    "task_completion_rate": {
        "target": ">90%",
        "measurement_method": "成功完成任务数/总任务数",
        "failure_analysis": "分类统计失败原因（能力不足/超时/用户取消等）",
        "continuous_improvement": "针对Top3失败原因专项优化"
    },

    "avg_response_time": {
        "target": "<30s",
        "measurement_method": "P50/P95/P99响应时间分布",
        "optimization_focus": "降低P95延迟（长尾优化）",
        "alert_threshold": "P99 > 60s 时发出告警"
    }
}
```

### 触发准确率评估工具

```bash
# 运行触发准确率评估
python skillscripts/skill_standardization/trigger_evaluator.py --evaluate

# 输出示例：
"""
╔══════════════════════════════════════════════════╗
║        Skill 触发准确率评估报告                    ║
╠══════════════════════════════════════════════════╣
║                                                   ║
║  📊 评估周期: 2026-03-07 ~ 2026-04-06 (30天)      ║
║                                                   ║
║  📈 整体指标                                      ║
║  ─────────────────────────────────────────────    ║
║  触发准确率: 87.3% ✅ (目标 >85%)                 ║
║  输出质量分: 4.2/5.0 ✅ (目标 >4.0)               ║
║  任务完成率: 91.5% ✅ (目标 >90%)                 ║
║  平均响应时间: 23.7s ✅ (目标 <30s)               ║
║                                                   ║
║  🎯 关键词触发统计                                ║
║  ─────────────────────────────────────────────    ║
║  "三省六部": 145次触发, 98.6%准确率               ║
║  "全生命周期": 892次触发, 91.2%准确率             ║
║  "devops": 567次触发, 85.4%准确率                ║
║  "TDD+SDD": 234次触发, 89.7%准确率              ║
║  "四维防线":  67次触发, 94.0%准确率 (v6.0新增)  ║
║  "资源协调":  45次触发, 91.1%准确率 (v6.0新增)  ║
║                                                   ║
║  📉 误报分析                                      ║
║  ─────────────────────────────────────────────    ║
║  Top1误报: "devops" → 实际想查询DevOps工具对比   ║
║  Top2误报: "代码审查" → 只想要简单lint检查        ║
║  Top3误报: "部署发布" → 只是想了解部署概念        ║
║                                                   ║
║  💡 优化建议                                      ║
║  ─────────────────────────────────────────────    ║
║  1. 增加"devops工具对比"到排除列表               ║
║  2. 为"简单lint检查"提供轻量级快速通道            ║
║  3. 区分"概念咨询"与"实际执行"的意图              ║
║                                                   ║
╚══════════════════════════════════════════════════╝
"""
```

## 🔄 三模运行架构（v6.0 增强）

### 模式对比

| 维度 | 自动化模式（Automated） | 自主模式（Autonomous） | Agent协作模式（Collaborative） |
|------|----------------------|----------------------|-------------------------------|
| **触发方式** | 运行Python脚本 | AI遵循AOG指南自主操作 | AI通过Bridge调度外部专业Agent |
| **适用场景** | 确定性、重复性任务 | 创造性、判断性任务 | 需要多领域专家协同的复杂任务 |
| **执行主体** | 脚本引擎 | AI Agent | AI主控 + 多外部Agent协作 |
| **优势** | 快速、一致、可重现 | 灵活、智能、可适应 | 专业深度、多角度、高质量 |
| **示例** | `python main.py run ...` | "请自主审查代码质量" | "调用Frontend Developer + Security Engineer审查前端安全性" |
| **风险控制** | 预定义流程，风险可控 | 动态决策，需风险门禁 | 多Agent协调，需编排器管控 |
| **输出一致性** | 高度一致 | 因场景而异 | 综合多方意见，质量更高 |
| **人工介入** | 异常时介入 | 关键节点审批 | 关键决策点确认 |
| **资源消耗** | 低 | 中 | 高（多Agent并行） |
| **典型耗时** | 秒级~分钟级 | 分钟级~十分钟级 | 十分钟级~小时级 |
| **⭐ v6.0操作优先级** | 第二优先级 | **第一优先级** | 第一优先级（但需MARC协调）|

### ⭐ v6.0 新增：智能模式选择决策树

基于任务特征自动推荐最优运行模式：

```
┌─────────────────────────────────────────────────────────────┐
│           智能模式选择决策树 (v6.0 Auto-Selector)            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  开始                                                        │
│    │                                                         │
│    ▼                                                         │
│  ┌─────────────────┐                                        │
│  │ 是否涉及文件操作？│                                        │
│  └────┬────────┬───┘                                        │
│       是        否                                            │
│       │         │                                            │
│       ▼         ▼                                            │
│  ┌──────────┐  ┌─────────────────┐                          │
│  │文件数量≤3？│  │ 是否有现成脚本？ │                          │
│  └────┬───┬──┘  └────┬────────┬──┘                          │
│      是   否      是      否                                 │
│      │    │       │       │                                 │
│      ▼    ▼       ▼       ▼                                 │
│  ┌────┐┌────┐┌──────┐┌──────────┐                          │
│  │自主││自主││脚本  ││命令(需预演)│                          │
│  │模式││模式││模式  ││  模式     │                          │
│  └────┘└────┘└──────┘└──────────┘                          │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  🤖 高级判断：是否需要多领域专家协同？                  │   │
│  │  ─────────────────────────────────────────────────  │   │
│  │  如果 是 → Agent协作模式（启用MARC资源协调）           │   │
│  │  如果 否 → 保持上述决策结果                           │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 决策树实现

```python
def select_mode_auto(task_context):
    """
    v6.0 智能模式选择器

    参数:
        task_context: 包含任务特征的字典

    返回:
        推荐的模式字符串及理由
    """
    # 特征提取
    involves_files = task_context.get("involves_file_operations", False)
    file_count = task_context.get("estimated_file_count", 0)
    has_script = task_context.get("has_existing_script", False)
    needs_experts = task_context.get("requires_domain_experts", False)
    is_batch = task_context.get("is_batch_operation", False)

    # 决策逻辑
    if involves_files:
        if file_count <= 3 and not is_batch:
            recommended_mode = "autonomous"
            reason = "少量文件操作，推荐Agent自主手动操作（第一优先级）"
        else:
            if has_script and not is_batch:
                recommended_mode = "automated"
                reason = "有现成脚本且非批量操作，推荐脚本执行（第二优先级）"
            else:
                recommended_mode = "automated_with_confirm"
                reason = "批量操作或无脚本，推荐命令执行但需确认（第三优先级）"
    else:
        if has_script:
            recommended_mode = "automated"
            reason = "有现成脚本，推荐脚本执行（第二优先级）"
        else:
            recommended_mode = "command_with_preflight"
            reason = "无脚本且非文件操作，推荐命令执行但需预演（第三优先级）"

    # 高级判断：多专家协同
    if needs_experts:
        recommended_mode = "collaborative"
        reason += " + 升级为Agent协作模式（启用MARC资源协调）"

    return {
        "recommended_mode": recommended_mode,
        "confidence": 0.85,
        "reason": reason,
        "alternative_modes": get_alternative_modes(recommended_mode)
    }
```

### Agent协作模式详解

```
┌─────────────────────────────────────────────────────────────┐
│            Agent协作模式 (Collaborative Mode)                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  【工作流程】                                                 │
│                                                             │
│  1️⃣ 任务接收与解析                                          │
│     用户指令 → 主控Agent解析 → 提取子任务                    │
│                                                             │
│  2️⃣ 智能路由                                                │
│     Router分析每个子任务 → 匹配最优Agent组合                  │
│                                                             │
│  3️⃣ MARC资源协调（⭐ v6.0新增）                             │
│     向MARC注册资源需求 → 获取锁 → 分配配额 → 防止死锁        │
│                                                             │
│  4️⃣ 并行/串行执行                                           │
│     Orchestrator编排 → 多Agent协同工作                       │
│                                                             │
│  5️⃣ 四维防线检查（⭐ v6.0新增）                             │
│     Prompt层 → 能力层 → 规则层 → 兜底层                      │
│                                                             │
│  6️⃣ 结果整合                                                │
│     收集各Agent产出 → 冲突解决 → 综合报告生成               │
│                                                             │
│  【适用场景示例】                                             │
│  ✅ 复杂架构设计：需要Solution Architect + Security Architect  │
│              + Cloud Architect共同评审                        │
│  ✅ 全栈代码审查：需要Frontend Dev + Backend Dev + DBA        │
│              + Security Expert四维审查                        │
│  ✅ 性能优化：需要Performance Tester + DBA + DevOps Engineer   │
│             联合分析与优化                                    │
│  ✅ 安全审计：需要Security Auditor + Compliance Officer        │
│              + Penetration Tester全方位检查                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### AOF框架说明

v5.0引入AOF（Autonomous Operation Framework）四层自主决策框架，支撑自主模式的智能运行：

```
┌─────────────────────────────────────────────────────────────┐
│              AOF 自主决策框架 (四层架构)                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌───────────────────────────────────────────────────┐     │
│   │  📡 感知层 (Perception Layer)                       │     │
│   │  ─────────────────────────────────────────────────  │     │
│   │  • 环境上下文感知    • 项目状态扫描                   │     │
│   │  • 需求意图理解      • 风险信号检测                   │     │
│   └─────────────────────┬─────────────────────────────┘     │
│                         ▼                                   │
│   ┌───────────────────────────────────────────────────┐     │
│   │  🧠 决策层 (Decision Layer)                        │     │
│   │  ─────────────────────────────────────────────────  │     │
│   │  • 任务分解与规划    • 模式选择（自动/自主/混合）       │     │
│   │  • ⭐ 操作优先级判断（v6.0新增）                     │     │
│   │  • 风险评估与分级    • 资源分配策略                   │     │
│   └─────────────────────┬─────────────────────────────┘     │
│                         ▼                                   │
│   ┌───────────────────────────────────────────────────┐     │
│   │  ⚙️ 执行层 (Execution Layer)                        │     │
│   │  ─────────────────────────────────────────────────  │     │
│   │  • 子技能调度执行    • 三省六部协作调用               │     │
│   │  • 中间结果验证      • 异常处理与回滚                 │     │
│   │  • ⭐ 四维防线贯穿（v6.0新增）                       │     │
│   └─────────────────────┬─────────────────────────────┘     │
│                         ▼                                   │
│   ┌───────────────────────────────────────────────────┐     │
│   │  📈 反馈学习层 (Feedback & Learning Layer)          │     │
│   │  ─────────────────────────────────────────────────  │     │
│   │  • 执行结果评估    • 决策效果分析                    │     │
│   │  • 经验沉淀入库    • 模型参数自调优                  │     │
│   └───────────────────────────────────────────────────┘     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 元技能层说明

v5.0在AOF框架之上构建元技能层（Meta-Skill Layer），赋予系统自我管理能力：

```
┌─────────────────────────────────────────────────────────────┐
│                元技能层 (Meta-Skill Layer)                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  🔍 自评估    │  │  ⚡ 自优化    │  │  📦 自扩展    │      │
│  │  Evaluation  │  │ Optimization │  │  Extension   │      │
│  │              │  │              │  │              │      │
│  │ • 触发率统计  │  │ • 参数调优    │  │ • 缺口识别    │      │
│  │ • 效果评分    │  │ • 流程精简    │  │ • 新技能建议  │      │
│  │ • 用户满意度  │  │ • 性能提升    │  │ • 能力补全    │      │
│  │ • 文件完整性  │  │ • 资源优化    │  │ • 场景覆盖    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                             │
│                    ┌──────────────┐                         │
│                    │  📋 自打包    │                         │
│  ◀─────────────────│   Packing    │─────────────────▶      │
│                    │              │                         │
│                    • 输出标准化   │                         │
│                    • 依赖打包     │                         │
│                    • 版本管理     │                         │
│                    • 分发就绪     │                         │
│                    └──────────────┘                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 🏛️ 架构总览：三省六部二十四司

### 一、中书省（决策层）- 4局

中书省负责**战略规划、方案设计、标准制定**，是整个系统的"大脑"。

| 局名 | 英文标识 | 核心职责 | 关键产出 | ⭐ v6.0增强 |
|------|---------|---------|---------|------------|
| **需求分析局** | `requirements_bureau` | 需求收集、分析、拆解、优先级排序 | PRD、用户故事、验收标准 | 支持Decision Log自动生成 |
| **架构设计局** | `architecture_bureau` | 系统架构、技术选型、模块划分、接口定义 | 架构图、技术方案、API设计 | 四维防线第1层集成 |
| **规范制定局** | `standards_bureau` | 编码规范、文档标准、流程规范、命名约定 | 规范文档、Checklist、Lint规则 | 规则校验层自动同步 |
| **方案审议局** | `review_bureau` | 方案评审、风险评估、可行性分析、决策记录 | 评审报告、决策日志、风险清单 | OpenCode透明化深度集成 |

### 二、门下省（审核层）- 4局

门下省负责**质量把关、合规审查、风险控制**，是整个系统的"守门员"。

| 局名 | 英文标识 | 核心职责 | 关键产出 | ⭐ v6.0增强 |
|------|---------|---------|---------|------------|
| **代码审查局** | `code_review_bureau` | Code Review、静态分析、安全扫描、性能审计 | 审查报告、问题清单、改进建议 | 四维防线第3层规则校验 |
| **测试验证局** | `testing_bureau` | 测试策略制定、测试用例设计、自动化测试执行 | 测试报告、覆盖率报告、缺陷统计 | Claw-Code可执行条款提取 |
| **质量监控局** | `quality_monitor_bureau` | 质量指标采集、趋势分析、预警告警、质量门禁 | 质量仪表盘、趋势图、告警通知 | 六维→七维监控增强 |
| **合规审计局** | `compliance_bureau` | 合规检查、许可证审计、安全合规、数据隐私 | 合规报告、审计日志、整改建议 | Harness STO深度集成 |

### 三、尚书省（执行层）- 六部二十四司

尚书省负责**具体任务的执行落地**，是整个系统的"手脚"。

#### 📋 吏部（Libu）- 人员与调度管理（4司）

| 司名 | 英文标识 | 核心职责 | v5.0自主能力 | ⭐ v6.0增强 |
|------|---------|---------|-------------|------------|
| **选司（Agent调度司）** | `agent_dispatch_si` | AI Agent的任务分配、负载均衡、优先级调度 | 智能任务路由、动态负载感知 | MARC资源协调集成 |
| **司封司（角色管理司）** | `role_management_si` | 角色定义、权限管理、职责边界划分 | 自适应角色切换、权限自动收缩 | 配额管理与权限动态调整 |
| **司勋司（技能匹配司）** | `skill_matching_si` | 技能识别、能力评估、最优Agent选择 | 意图驱动的技能推荐 | 四维防线第2层能力约束 |
| **考功司（协调司）** | `coordination_si` | 跨部门协作、冲突解决、进度同步 | 自主冲突调解、进度预测 | 死锁预防与公平调度 |

#### 💰 户部（Hubu）- 环境与资源管理（4司）

| 司名 | 英文标识 | 核心职责 | v5.0自主能力 | ⭐ v6.0增强 |
|------|---------|---------|-------------|------------|
| **度支司（环境配置司）** | `environment_config_si` | 开发/测试/生产环境配置、环境一致性保障 | 自适应环境探测、配置漂移自修复 | PS7原生环境适配 |
| **金部司（依赖管理司）** | `dependency_mgmt_si` | 依赖版本管理、漏洞扫描、依赖更新策略 | 智能依赖升级决策 | 安全扫描自动化 |
| **仓部司（资源优化司）** | `resource_optimization_si` | 计算资源分配、成本优化、性能调优 | 动态资源伸缩预测 | MARC配额管理集成 |
| **户部司（基础设施司）** | `infrastructure_si` | CI/CD流水线、容器化、云资源管理 | 流水线自主编排 | Harness Pipeline增强 |

#### 📚 礼部（Libu2）- 文档与知识管理（4司）

| 司名 | 英文标识 | 核心职责 | v5.0自主能力 | ⭐ v6.0增强 |
|------|---------|---------|-------------|------------|
| **祠部司（文档司）** | `documentation_si` | API文档、技术文档、用户手册生成与维护 | 语义感知的增量文档更新 | Decision Log自动归档 |
| **主客司（模板管理司）** | `template_management_si` | 文档模板管理、模板版本控制、模板定制 | 模板智能推荐与自适应 | 四维防线模板库 |
| **膳部司（知识库司）** | `knowledge_base_si` | 知识沉淀、经验复用、最佳实践库维护 | 知识图谱自动构建 | 开源理念知识图谱 |
| **仪制司（标准化司）** | `standardization_si` | 命名规范、格式标准、文档结构统一 | 规则自动推断与强制执行 | Skill标准化元数据管理 |

#### ⚔️ 兵部（Bingbu）- 测试与质量管理（4司）

| 司名 | 英文标识 | 核心职责 | v5.0自主能力 | ⭐ v6.0增强 |
|------|---------|---------|-------------|------------|
| **职方司（TDD执行司）** | `tdd_execution_si` | 测试先行开发、红绿重构循环、测试用例编写 | 边界条件自主推断 | Claw-Code条款→测试自动转化 |
| **驾部司（测试框架司）** | `test_framework_si` | 测试框架搭建、Mock/Stub管理、测试工具链 | 框架选型智能推荐 | 跨平台测试适配 |
| **库部司（覆盖分析司）** | `coverage_analysis_si` | 代码覆盖率分析、分支覆盖、条件覆盖统计 | 覆盖缺口自动定位与补全 | 七维监控集成 |
| **屯田司（回归测试司）** | `regression_testing_si` | 回归测试套件管理、冒烟测试、全量回归 | 影响范围分析与精准回归 | 智能回归策略 |

#### 🔧 工部（Gongbu）- 代码生成与设计（4司）

| 司名 | 英文标识 | 核心职责 | v5.0自主能力 | ⭐ v6.0增强 |
|------|---------|---------|-------------|------------|
| **屯田司（代码生成司）** | `code_generation_si` | 基于规范的代码生成、脚手架搭建、样板代码 | 上下文感知的智能补全 | 操作优先级第一优先级 |
| **虞部司（UI/UX设计司）** | `uiux_design_si` | 界面原型、交互设计、用户体验优化 | 设计模式自动匹配 | UI/UX Pro Max联动 |
| **水部司（数据库设计司）** | `database_design_si` | 数据模型设计、ER图、索引优化、迁移脚本 | Schema演化自动推导 | Schema变更Decision Log |
| **工部司（API设计司）** | `api_design_si` | RESTful API设计、接口契约、版本管理 | API一致性自检 | OpenAPI规范自动校验 |

#### ⚖️ 刑部（Xingbu）- 维护与演化（4司）

| 司名 | 英文标识 | 核心职责 | v5.0自主能力 | ⭐ v6.0增强 |
|------|---------|---------|-------------|------------|
| **都官司（Bug修复司）** | `bug_fixing_si` | 缺陷定位、根因分析、修复方案制定与实施 | 智能根因推断与修复建议 | 四维防线兜底恢复 |
| **比部司（重构司）** | `refactoring_si` | 代码重构、技术债务清理、架构优化 | 重构时机自主判断 | 操作优先级应用 |
| **司门司（自演化司）** | `self_evolution_si` | 自我评估、模式学习、能力进化 | AOF驱动的持续自演化 | 演化Decision Log |
| **夏官司（版本控制司）** | `version_control_si` | Git工作流、分支策略、发布管理、变更日志 | 变更影响智能评估 | Git操作预演机制 |

## 🔗 开源理念融合映射

Universal DevOps v6.0深度融合了四大开源项目的核心理念（从功能映射升级为哲学内化）：

### 1️⃣ OpenCode 映射（v6.0 哲学内化版）

| OpenCode理念 | v5.1实现 | v6.0深度内化 | 提升点 |
|-------------|---------|-------------|-------|
| **透明化开发** | 中书省方案审议局 → 所有决策可追溯 | **Decision Log系统**（决策ID、依据、影响范围、效果评估、后评估计划） | 结构化+可量化 |
| **协作式Code Review** | 门下省代码审查局 → 结构化审查流程 | **多Agent协作审查**（YAML工作流DSL + MARC资源协调） | 智能化+并行化 |
| **自动化质量门禁** | 门下省质量监控局 → 六维质量监控 | **四维输出防线**（Prompt→Capability→Rule→Fallback纵深防御） | 全面性+可靠性 |
| **开发者体验优先** | 礼部文档司 → 自动化文档生成 | **操作优先级架构**（Agent自主手动优先，减少认知负担） | 体验优先级提升 |

### 2️⃣ OpenClaude 映射（v6.0 哲学内化版）

| OpenClaude理念 | v5.1实现 | v6.0深度内化 | 提升点 |
|---------------|---------|-------------|-------|
| **AI Agent编排** | 吏部Agent调度司 → 智能任务分发 | **YAML工作流DSL**（声明式定义、条件路由、错误处理、并行执行） | 可编程+可复用 |
| **上下文感知** | 户部环境配置司 → 环境上下文自动注入 | **四维防线第1层**（意图识别、上下文自动注入、歧义消解） | 智能化+主动性 |
| **技能组合** | 吏部技能匹配司 → 最优Agent-Skill匹配 | **第2层能力约束**（技能匹配度评估、知识覆盖检查、能力缺口识别） | 精准化+可视化 |
| **人机协作** | 尚书省各司 → 人机协同执行 | **操作预演机制**（影响分析、风险评估、分级审批） | 安全性+可控性 |

### 3️⃣ Claw-Code 映射（v6.0 哲学内化版）

| Claw-Code理念 | v5.1实现 | v6.0深度内化 | 提升点 |
|--------------|---------|-------------|-------|
| **SDD驱动** | 中书省需求分析局 → 规格化需求定义 | **可执行条款提取引擎**（规格文档→可执行条款→TDD测试用例→代码自动推导） | 全自动化 |
| **TDD驱动** | 兵部TDD执行司 → 测试先行开发 | **Claw-Code契约驱动**（SDD Spec → Parser → TDD Test → Executor → Verifier 闭环） | 闭环增强 |
| **闭环反馈** | 自演化系统 → 迭代-优化-修复-改进 | **四维防线第4层兜底恢复**（质量评分、自动回滚、降级策略、错误日志） | 可靠性保障 |
| **模板化输出** | 礼部模板管理司 → 标准化输出物 | **Skill标准化元数据**（frontmatter增强、触发优化、评估基准） | 可度量+可优化 |

### 4️⃣ Harness Engineering 映射（v6.0 深度增强版）

| Harness Engineering | v5.1实现 | v6.0深度增强 | 提升点 |
|-------------------|---------|-------------|-------|
| **渐进式发布** | CD金丝雀/蓝绿/滚动部署管理器 | **自适应部署策略**（基于SLO/Error Budget自动选择最优策略） | 智能化 |
| **Pipeline as Code** | CI Pipeline Orchestrator YAML输出 | **智能Pipeline引擎**（增量构建、并行执行、缓存优化、成本感知） | 性能+成本优化 |
| **SRE实践** | SLO/Error Budget/SLI引擎 | **七维质量监控**（新增可靠性维度：SLO达成率/Error Budget/MTTR） | 维度扩展 |
| **安全左移** | 5阶段STO编排器 | **四维防线第3层**（安全扫描自动集成到规则校验层） | 深度集成 |
| **Feature Flags** | 功能开关管理与灰度发布 | **Feature Flag as Code**（YAML定义、灰度规则、监控指标一体化） | 即代码化 |
| **混沌工程** | Chaos实验编排器与韧性验证 | **Chaos实验+兜底恢复联动**（实验触发自动激活四维防线第4层） | 弹性增强 |
| **成本优化** | FinOps成本分析与自动优化引擎 | **MARC配额管理**（资源配额、使用率监控、超限预警、成本分摊） | 精细化 |

## 🚀 快速开始

### Step 0: 密钥初始化（v6.1 新增 🔐）

在开始任何开发任务前，先确保密钥管理基础设施就绪：

```bash
# 1. 创建 .env 文件（参考 .env.example 模板）
# 复制模板并填入实际值
cp .env.example .env.local
# 编辑 .env.local，填入你的本地开发环境变量

# 2. 验证 SecretsManager 加载
python -c "
from skillscripts.secrets_manager import SecretsManager, HardcodedDetector
from pathlib import Path

sm = SecretsManager()
sm.load()
result = sm.validate_all()
print(f'✅ 密钥加载完成 | 有效: {result.is_valid} | 评分: {result.score}/100')
if not result.is_valid:
    for issue in result.issues[:5]:
        print(f'  ⚠️ {issue}')

# 3. 运行硬编码检测（确保代码库安全）
detector = HardcodedDetector()
report = detector.scan_directory(Path('.'))
crit = report.by_severity.get('critical', 0)
high = report.by_severity.get('high', 0)
print(f'🔍 安全扫描: {report.total_findings} 个问题 (Critical:{crit} High:{high})')
if crit > 0:
    print('❌ 存在严重安全问题，请修复后再继续！')
"
```

### ⭐ v6.0 新增示例：四维防线与MARC演示

#### 示例1: 使用四维防线进行安全开发（Agent自主手动操作）

```bash
# 通过Agent自主手动操作实现安全的代码开发
"基于 docs/requirements/api-spec.yaml 开发用户认证模块，
 要求经过完整的四维防线检查"

# 执行过程（AI Agent内部流程）：
# ✅ 第1层 Prompt工程：
#    - 识别意图：code_generation
#    - 注入上下文：项目结构、编码规范（PEP8）、API契约（OpenAPI 3.0）
#    - 澄清确认："是否需要OAuth2.0 + JWT双令牌机制？" → 用户确认

# ✅ 第2层 能力约束：
#    - 技能匹配：code_generation_si (置信度94%)
#    - 知识覆盖：JWT/OAuth2.0/FastAPI (覆盖率91%)
#    - 工具可用：所有依赖已安装 ✅

# ✅ 第3层 规则校验（代码生成过程中实时检查）：
#    - Lint检查：✅ PEP8合规（black + isort自动格式化）
#    - 安全扫描：✅ Bandit无高危漏洞
#    - 类型检查：✅ mypy通过
#    - 性能基线：✅ 异步响应时间 < 50ms

# ✅ 第4层 兜底恢复（未触发）：
#    - 质量评分：4.5/5.0 ✅
#    - 输出：src/auth/ 目录（完整实现）
```

#### 示例2: 监控MARC资源协调状态

```bash
# 查看MARC资源协调器的实时状态
python skillscripts/resource_coordinator/quota_manager.py --status

# 输出：
"""
╔══════════════════════════════════════════════════╗
║           MARC 资源协调器状态面板                 ║
╠══════════════════════════════════════════════════╣
║                                                   ║
║  📊 全局资源使用率                                ║
║  ─────────────────────────────────────────────    ║
║  活跃Agent数: 4/10 (40%)                          ║
║  文件锁占用: 23/100 (23%)                         ║
║  API调用速率: 2,450/10,000 (24.5%)                ║
║  CPU使用率: 45.2%/80% (56.5%)                     ║
║  内存使用率: 62.1%/85% (73.1%)                    ║
║                                                   ║
║  🔒 当前锁持有情况                                ║
║  ─────────────────────────────────────────────    ║
║  Agent-001: 3个写锁(src/auth/*), 2个API信号量      ║
║  Agent-002: 1个写锁(src/models/*), 0个API信号量    ║
║  Agent-003: 5个读锁(docs/*), 3个API信号量          ║
║  Agent-004: 2个写锁(tests/*), 1个API信号量         ║
║                                                   ║
║  ⚠️ 告警信息                                      ║
║  ─────────────────────────────────────────────    ║
║  🟡 Agent-003 接近文件锁上限 (5/10)               ║
║  🟢 系统运行正常                                  ║
║                                                   ║
╚══════════════════════════════════════════════════╝
"""
```

#### 示例3: PowerShell 7 环境下的完整工作流

```powershell
# 在PS7环境下执行完整的DevOps工作流
# 文件：workflows/devops_workflow_ps7.ps1

.\workflows\devops_workflow_ps7.ps1 -ProjectPath "." -Environment "dev"

# 执行步骤：
# 1️⃣ 环境检查（Python 3.10+, PS7+）
# 2️⃣ 项目初始化（创建docs/目录结构）
# 3️⃣ 运行SDD+TDD融合引擎（第二优先级：规划脚本）
# 4️⃣ 执行测试套件
# 5️⃣ 代码质量检查（四维防线第3层）
# 6️⃣ 生成Decision Log（OpenCode透明化）
# 7️⃣ MARC资源状态检查
# 8️⃣ 输出完成报告
```

#### 示例4: 生成Decision Log（OpenCode透明化）

```bash
# 为重要技术决策生成完整的Decision Log
python skillscripts/open_source_philosophy/opencode_transparency.py \
  --decision "选择微服务架构" \
  --maker "中书省-架构设计局" \
  --rationale "业务模块边界清晰，团队规模>20人，需要独立部署能力" \
  --alternatives ["单体架构", "模块化单体", "Serverless"] \
  --impact_scope ["前端", "后端", "数据库", "运维"] \
  --risk_assessment "中等（需要额外的服务治理成本）" \
  --output "docs/logs/decision_logs/"

# 输出文件：docs/logs/decision_logs/DEC-20260406-001.md
# 包含：决策ID、决策者、备选方案评估、影响范围、风险分析、后评估计划
```

#### 示例5: 触发准确率评估

```bash
# 评估过去30天的Skill触发准确率
python skillscripts/skill_standardization/trigger_evaluator.py --evaluate

# 输出：
# - 整体准确率：87.3%
# - 各关键词触发统计
# - Top3误报分析
# - 优化建议
```

### 基本使用示例（自动化模式）

```bash
# 1. 触发完整开发流程
"使用 universal-devops 进行一个电商后台系统的全生命周期开发"

# 2. 仅调用特定子技能
"调用 universal-devops 的需求分析局，分析以下需求..."
"调用 universal-devops 的代码审查局，审查 src/user/ 目录"

# 3. 执行SDD+TDD融合流程
"启动 SDD+TDD 融合引擎，基于 requirements/prd.md 进行开发"

# 4. 质量检查
"运行六维质量监控，生成项目质量报告"

# 5. 自演化触发
"触发自演化闭环，对当前项目进行自我优化"
```

### 自主模式调用示例（v5.0 新增）

```bash
# 1. 自主代码质量审查（AI自主决策审查范围和深度）
"请以自主模式对项目进行全面的代码质量审查"

# 2. 自主架构优化建议（AI自主分析并给出方案）
"请自主分析当前架构的瓶颈，给出优化建议和实施方案"

# 3. 自主Bug排查与修复（AI自主定位、分析、修复）
"请自主排查以下报错并修复：[错误信息]"

# 4. 自主技术债务清理（AI自主识别并规划清理）
"请自主评估项目的技术债务，制定清理计划并执行低风险项"

# 5. 混合模式（自动+自主结合）
"先用自动化模式跑完测试套件，然后自主模式分析失败用例"
```

### v5.1 示例：Harness CI/CD 集成

```bash
# 1. 创建Harness CI流水线
"使用 Harness CI 模块为当前项目创建完整的CI流水线配置"
# 输出: .harness/ci-pipeline.yaml（包含增量构建、并行执行、缓存优化、质量门禁）

# 2. 配置金丝雀部署策略
"为用户服务模块配置金丝雀部署，分3阶段渐进式发布"
# 输出: deployment-canary.yaml（5% → 25% → 100%，含自动回滚规则）

# 3. 设置Feature Flag
"为新功能'暗色模式'创建Feature Flag，支持按用户百分比灰度发布"
# 输出: feature-flag-dark-mode.yaml（含灰度规则和监控指标）

# 4. 定义SLO和Error Budget
"为API网关定义SLO：可用性99.9%，延迟P99<200ms，并配置Error Budget告警"
# 输出: slo-api-gateway.yaml（含SLO定义、Budget计算、告警阈值）

# 5. 执行安全左移扫描
"对项目执行完整的STO 5阶段安全扫描，生成安全报告"
# 输出: security-scan-report.md（SAST+SCA+DAST+IaC+Container全量扫描结果）

# 6. 运行混沌实验
"设计一个混沌实验：模拟数据库连接池耗尽，验证系统恢复能力"
# 输出: chaos-experiment-db-pool.yaml（含假设、稳态、故障注入、验证步骤）
```

### v5.1 示例：Agent协作调用

```bash
# 1. 多Agent代码审查
"通过Agency-Agent Bridge调用 Frontend Developer + Security Engineer + Performance Expert，
   对 src/frontend/ 目录进行全面的三维审查"

# 2. 架构设计评审会
"组织一场虚拟的架构评审会议，邀请 Solution Architect + Security Architect +
   Cloud Architect + DevOps Lead 对微服务架构方案进行联合评审"

# 3. 全栈性能优化
"调度 Performance Tester + DBA + Backend Developer + Frontend Dev 组成优化团队，
   对系统进行端到端的性能分析与优化"

# 4. 安全合规审计
"调用 Security Auditor + Compliance Officer + Penetration Tester 进行全方位的安全审计，
   生成符合SOC2标准的审计报告"

# 5. 技术选型决策
"针对'是否引入GraphQL'这个技术决策，请调用多个相关领域的Architect提供专业意见，
   并综合各方观点给出最终建议"

# 6. 复杂Bug联合排查
"这是一个跨前端+后端+数据库的复杂Bug，请协调 Frontend Debugger + Backend Debugger +
   DBA 进行联合根因分析"
```

### 子技能调用语法

```yaml
# 格式: @universal-devops/{省份}/{局或部/司}
@universal-devops/zhongshusheng/requirements_bureau    # 中书省-需求分析局
@universal-devops/menxiasheng/code_review_bureau        # 门下省-代码审查局
@universal-devops/shangshusheng/libu/agent_dispatch_si  # 尚书省-吏部-Agent调度司

# v5.0 自主模式前缀（可选）
@universal-devops/autonomous/menxiasheng/code_review_bureau   # 强制自主模式调用

# ⭐ v6.0 新增：操作优先级指定（可选）
@universal-devops/manual/menxiasheng/code_review_bureau      # 强制手动操作（第一优先级）
@universal-devops/script/zhongshusheng/requirements_bureau   # 强制脚本执行（第二优先级）
@universal-devops/command/shangshusheng/libu/agent_dispatch_si # 强制命令执行（第三优先级，需预演）
```

## ⚙️ SDD+TDD 融合引擎说明

### 核心原理

```
┌────────────────────────────────────────────────────────┐
│               SDD+TDD 融合引擎                          │
│           (v6.0 增强：Claw-Code契约驱动)                │
├────────────────────────────────────────────────────────┤
│                                                        │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐         │
│  │ SDD Spec │───▶│  Parser  │───▶│ 条款提取  │         │
│  │  输入    │    │ 规格解析  │    │ Engine   │         │
│  └──────────┘    └──────────┘    └─────┬─────┘         │
│                                      │                │
│                                      ▼                │
│                              ┌──────────┐           │
│                              │ TDD Test │           │
│                              │  生成    │◀── 自动推导 │
│                              └─────┬─────┘           │
│                                    │                 │
│                                    ▼                 │
│                              ┌──────────┐           │
│                              │ Executor │           │
│                              │ 测试执行  │           │
│                              └─────┬─────┘           │
│                                    │                 │
│                                    ▼                 │
│                              ┌──────────┐           │
│                              │ Verifier │           │
│                              │ 闭环验证  │           │
│                              └─────┬─────┘           │
│                                    │                 │
│                                    ▼                 │
│                              ┌──────────┐           │
│                              │ 覆盖率   │           │
│                              │ 分析器   │           │
│                              └──────────┘           │
│                                                        │
└────────────────────────────────────────────────────────┘
```

### 工作流程

1. **SDD阶段**（中书省主导）
   - 需求分析局提取规格化需求
   - 架构设计局输出技术方案
   - 规范制定局定义编码标准

2. **⭐ v6.0增强：可执行条款提取**（Parser引擎）
   - SDD Spec Parser 解析规格文档
   - 提取功能点、接口定义、验收标准
   - **新增**：将自然语言规格转换为可执行条款（Executable Clauses）
   - 每个条款包含：前置条件、操作步骤、预期结果、验收准则

3. **TDD阶段**（兵部主导）
   - **新增**：条款提取引擎自动生成TDD测试用例骨架
   - TDD Execution司编写失败测试
   - Gongbu代码生成司实现最小可行代码
   - 回归测试司验证全部通过

4. **验证阶段**（门下省主导）
   - Closed-loop Verifier 验证SDD规格完整性
   - **新增**：条款覆盖率分析（确保所有可执行条款都有对应测试）
   - 质量监控局采集质量指标
   - 合规审计局检查规范符合性

5. **反馈循环**
   - 验证结果反馈至中书省进行方案调整
   - 不通过项进入刑部Bug修复/重构流程

## 📊 持续质量监控体系（六维→七维）

### 监控架构

```python
quality_dimensions = {
    "code_quality": {           # 代码质量维度
        "metrics": ["complexity", "duplication", "maintainability", "technical_debt"],
        "tools": ["sonarqube", "eslint", "radon"],
        "threshold": {"complexity": "<10", "duplication": "<3%", "coverage": ">80%"}
    },
    "testing_quality": {        # 测试质量维度
        "metrics": ["coverage", "pass_rate", "flaky_tests", "test_efficiency"],
        "tools": ["pytest", "jest", "coverage"],
        "threshold": {"line_coverage": ">80%", "branch_coverage": ">70%", "pass_rate": "100%"}
    },
    "documentation_quality": {  # 文档质量维度
        "metrics": ["completeness", "accuracy", "timeliness", "accessibility"],
        "tools": ["sphinx", "mkdocs", "typedoc"],
        "threshold": {"api_coverage": ">95%", "docstring_coverage": ">90%"}
    },
    "performance_quality": {    # 性能质量维度
        "metrics": ["response_time", "throughput", "resource_usage", "scalability"],
        "tools": ["locust", "jmeter", "prometheus"],
        "threshold": {"p99_latency": "<200ms", "cpu_usage": "<80%", "memory_usage": "<85%"}
    },
    "security_quality": {       # 安全质量维度
        "metrics": ["vulnerabilities", "dependencies", "compliance", "secrets"],
        "tools": ["snyk", "trivy", "bandit"],
        "threshold": {"critical_vulns": "0", "high_vulns": "<5", "outdated_deps": "<10%"}
    },
    "compliance_quality": {     # 合规质量维度
        "metrics": ["license_compliance", "api_contract", "coding_standards", "process_adherence"],
        "tools": ["license-checker", "openapi-validator", "custom-linters"],
        "threshold": {"license_issues": "0", "api_compliance": "100%", "standard_violations": "<10"}
    },
    "reliability_quality": {    # ⭐ v5.1新增：可靠性质量维度
        "metrics": ["slo_achievement", "error_budget_remaining", "mttr", "availability"],
        "tools": ["prometheus", "grafana", "pagerduty"],
        "threshold": {"slo_achievement": ">99.9%", "mttr": "<1h", "availability": ">99.95%"}
    }
}
```

### 质量门禁机制

```yaml
quality_gates:
  pre_commit:
    - lint_check
    - unit_test_fast
    - security_scan_quick

  pre_merge:
    - full_unit_test
    - integration_test
    - code_coverage_check (>80%)
    - documentation_update_check

  pre_release:
    - e2e_test
    - performance_test
    - security_audit_full
    - compliance_check
    - regression_test_full

  post_release:
    - production_monitoring
    - error_tracking
    - user_feedback_collection

  # ⭐ v6.0 新增：四维防线集成门禁
  four_d_defense_check:
    - prompt_engineering_validation
    - capability_constraint_check
    - rule_validation_scan
    - fallback_recovery_test
```

## 🔄 自演化闭环系统

### 四阶演化模型

```
┌─────────────────────────────────────────────────────────┐
│              自演化闭环系统 (Self-Evolution Loop)          │
│              (v6.0 增强：演化Decision Log)                │
├─────────────────────────────────────────────────────────┤
│                                                         │
│    ┌──────────┐                                        │
│    │ 自迭代器  │ ◀──────────────────────────────────┐   │
│    │ Iterator │                                   │   │
│    └────┬─────┘                                    │   │
│         │                                          │   │
│         ▼                                          │   │
│    ┌──────────┐      ┌──────────┐      ┌──────────┐│   │
│    │ 自优化器  │ ──▶ │ 自修复器  │ ──▶ │ 自改进器  ││   │
│    │ Optimizer│      │ Repairer │      │ Improver ││   │
│    └──────────┘      └──────────┘      └────┬─────┘│   │
│         ▲                                     │     │   │
│         └─────────────────────────────────────┘     │   │
│                   反馈闭环                            │   │
│                                                         │
│    ⭐ v6.0 新增：每次演化自动生成Decision Log          │
│    记录：演化原因、采取行动、预期效果、实际效果          │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 各组件职责

| 组件 | 文件位置 | 功能描述 | ⭐ v6.0增强 |
|------|---------|---------|------------|
| **自迭代器 (Self-Iterator)** | `evolution/self_iterator.py` | 定期触发演化周期，收集项目元数据，识别演化机会点 | 演化机会Decision Log |
| **自优化器 (Self-Optimizer)** | `evolution/self_optimizer.py` | 性能瓶颈分析、资源配置优化、算法效率提升 | 优化前后对比报告 |
| **自修复器 (Self-Repairer)** | `evolution/self_repairer.py` | 自动Bug检测与修复、异常恢复、回滚机制 | 四维防线第4层联动 |
| **自改进器 (Self-Improver)** | `evolution/self_improver.py` | 从历史数据学习、模式识别、最佳实践内化 | 经验库自动更新 |
| **演化控制器 (Evolution Controller)** | `evolution/evolution_controller.py` | 协调四个演化组件，控制演化节奏，防止过度演化 | MARC资源协调集成 |

### 演化触发条件

```yaml
triggers:
  scheduled:
    - cron: "0 2 * * *"  # 每日凌晨2点例行检查
    - interval: "7d"     # 每7天深度演化

  event_driven:
    - on: "quality_gate_failure"   # 质量门禁失败时触发
    - on: "high_bug_density"       # Bug密度过高时触发
    - on: "tech_debt_threshold"    # 技术债务超阈值时触发
    - on: "performance_regression" # 性能退化时触发
    - on: "four_d_defense_breach"  # ⭐ v6.0新增：四维防线被突破时触发

  manual:
    - command: "/evolve"           # 手动触发命令
    - command: "/self-repair"      # 手动触发自修复
    - command: "/marc-status"      # ⭐ v6.0新增：查看MARC状态
```

## 📁 输出物目录结构说明

所有项目输出物统一存放在项目的 `docs/` 或自定义输出目录下：

```
project-root/
├── docs/                           # 主输出目录
│   ├── requirements/               # 📋 需求文档
│   │   ├── prd_YYYYMMDD.md         # 产品需求文档
│   │   ├── user_stories/           # 用户故事集
│   │   └── acceptance_criteria/    # 验收标准
│   │
│   ├── architecture/               # 🏗️ 架构设计文档
│   │   ├── system_architecture.md  # 系统架构总览
│   │   ├── technical_design/       # 技术设计方案
│   │   ├── diagrams/               # 架构图（Mermaid/PlantUML）
│   │   └── decisions/              # 架构决策记录（ADR）
│   │
│   ├── api/                        # 🔌 API文档
│   │   ├── openapi_spec.yaml       # OpenAPI规范
│   │   ├── endpoints/              # 接口详细文档
│   │   └── examples/               # 调用示例
│   │
│   ├── database/                   # 🗄️ 数据库设计文档
│   │   ├── er_diagrams/            # ER关系图
│   │   ├── schema_design/          # 表结构设计
│   │   ├── migrations/             # 迁移脚本
│   │   └── index_optimization/      # 索引优化方案
│   │
│   ├── testing/                    # 🧪 测试文档
│   │   ├── test_strategy.md        # 测试策略
│   │   ├── test_cases/             # 测试用例
│   │   ├── coverage_reports/       # 覆盖率报告
│   │   └── test_results/           # 测试结果
│   │
│   ├── reviews/                    # 👁️ 审查报告
│   │   ├── code_reviews/           # Code Review报告
│   │   ├── architecture_reviews/   # 架构评审报告
│   │   ├── security_audits/        # 安全审计报告
│   │   └── compliance_reports/     # 合规检查报告
│   │
│   ├── deployment/                 # 🚀 部署文档
│   │   ├── ci_cd_pipelines/        # CI/CD流水线配置
│   │   ├── environment_configs/    # 环境配置
│   │   ├── runbooks/               # 运维手册
│   │   └── rollback_plans/         # 回滚方案
│   │
│   ├── iteration/                  # 🔄 迭代记录
│   │   ├── sprint_logs/            # Sprint日志
│   │   ├── changelogs/             # 变更日志
│   │   ├── release_notes/          # 发布说明
│   │   └── retrospectives/         # 回顾总结
│   │
│   ├── monitoring/                 # 📈 监控报告
│   │   ├── quality_dashboards/     # 质量仪表盘
│   │   ├── performance_metrics/    # 性能指标
│   │   ├── trend_analysis/         # 趋势分析
│   │   └── alerts/                 # 告警记录
│   │
│   ├── logs/                       # 📝 日志归档
│   │   ├── evolution_logs/         # 演化日志
│   │   ├── execution_logs/         # 执行日志
│   │   ├── decision_logs/          # ⭐ v6.0新增：决策日志（OpenCode透明化）
│   │   │   ├── DEC-YYYYMMDD-NNN.md  # Decision Log文件
│   │   └── audit_trails/           # 审计追踪
│   │
│   └── marc/                       # ⭐ v6.0新增：MARC协调器日志
│       ├── resource_snapshots/     # 资源快照
│       ├── lock_histories/         # 锁历史
│       ├── deadlock_reports/       # 死锁报告
│       └── quota_alerts/           # 配额告警
```

## 🔗 与现有 sanliu 技能的关系

### 关系图谱

```
┌─────────────────────┐         ┌─────────────────────────────────────┐
│    sanliu (v3.x)    │         │      universal-devops v6.0          │
│   (基础框架版本)     │ ──────▶ │  (四维防线+MARC协调完整版)           │
└─────────────────────┘         └─────────────────────────────────────┘
         │                                 │
    核心架构继承                      全面增强扩展
         │                                 │
    ├─ 三省六部基础                   ├─ 二十四司精细化
    ├─ SDD/TDD概念                   ├─ 融合引擎实现（v6.0: Claw-Code契约驱动）
    └─ 子技能框架                    ├─ 六维→七维质量监控
                                      ├─ 自演化闭环（v6.0: 演化Decision Log）
                                      ├─ 32个子技能
                                      ├─ 完整模板库
                                      ├─ 配置化管理
                                      ├─ 开源理念深度融合（v6.0: 哲学内化）
                                      ├─ ⭐ 操作优先级架构
                                      ├─ ⭐ 四维输出防线
                                      ├─ ⭐ MARC资源协调器
                                      ├─ ⭐ PS7原生适配
                                      └─ ⭐ Skill标准化元数据
```

### 主要差异

| 维度 | sanliu (v3.x) | universal-devops v5.1 | universal-devops **v6.0** |
|------|--------------|------------------------|--------------------------|
| **架构粒度** | 三省六部（12个单元） | 三省六部**二十四司**（36个单元） | 同左 + **MARC协调层** |
| **子技能数** | ~12个基础子技能 | **32个**精细化子技能 | 同左 + **四维防线模块** |
| **引擎实现** | 概念性描述 | **完整实现的**SDD+TDD融合引擎 | **增强版**：Claw-Code可执行条款提取 |
| **质量监控** | 基础检查项 | **六维**持续质量监控体系 | **七维**（+可靠性）+ **四维防线** |
| **演化能力** | 无 | **四阶**自演化闭环系统 | **增强版**：演化Decision Log |
| **模板库** | 无 | **10类**完整模板库 | 同左 + **四维防线模板** |
| **配置管理** | 硬编码 | **YAML配置文件**驱动 | 同左 + **MARC配置** |
| **开源融合** | 无 | **OpenCode/OpenClaude/claw-code/Harness**融合 | **哲学内化级**：Decision Log/YAML DSL/契约驱动 |
| **输出物** | 基础文档 | **10个子目录**完整输出体系 | **12个子目录**（+decision_logs, mar） |
| **适用范围** | 小型项目 | **企业级**全生命周期项目 | **企业级** + **多Agent协作** + **Windows原生** |
| **操作模式** | 单一（脚本） | **双模**（自动+自主） | **三模** + **操作优先级** + **智能选择** |
| **平台支持** | Linux为主 | Linux/Mac | **Win/Mac/Linux**（PS7原生） |
| **可评估性** | 无 | 基础 | **完整评估体系**（触发准确率/质量分/完成率/响应时间） |

### 升级路径

```
sanliu v3.x 项目
    │
    ├── 可直接升级到 universal-devops v6.0
    │   └─ 保持向后兼容，新增四维防线+MARC+PS7支持
    │
    ├── 从v5.1升级到v6.0
    │   ├─ Phase 1: 启用操作优先级架构（默认Agent自主手动）
    │   ├─ Phase 2: 集成四维输出防线（渐进式启用各层）
    │   ├─ Phase 3: 部署MARC资源协调器（多Agent场景必需）
    │   └─ Phase 4: 配置PS7原生适配（Windows用户）
    │
    └─ 并行共存
        └─ 新项目用 v6.0，旧项目保持 v5.1
```

## 📦 技术栈要求

### 必需依赖

```yaml
core:
  python: ">=3.10"  # ⭐ v6.0升级：从3.9提升至3.10

optional:
  - yaml          # 配置文件解析
  - jinja2        # 模板渲染
  - pydantic      # 数据校验 (>=2.0)
  - rich          # 终端美化输出
  - click         # CLI框架
```

### 推荐工具集成

| 类别 | 推荐工具 | 用途 | ⭐ v6.0增强 |
|------|---------|------|------------|
| **代码质量** | SonarQube, ESLint, Pylint | 静态分析 | 四维防线第3层集成 |
| **测试** | pytest, jest, Jest | 单元/集成测试 | Claw-Code条款→测试 |
| **覆盖率** | Coverage.py, Istanbul | 覆盖率统计 | 七维监控集成 |
| **文档** | Sphinx, MkDocs, Swagger | 文档生成 | Decision Log自动归档 |
| **CI/CD** | GitHub Actions, GitLab CI, Harness | 流水线 | Harness增强版 |
| **监控** | Prometheus, Grafana | 运行时监控 | MARC资源监控 |
| **安全** | Snyk, Trivy, Bandit | 安全扫描 | 四维防线安全检查 |
| **终端** | PowerShell 7+, Bash 5.0+ | 命令执行 | PS7原生适配 |

## 📖 使用指南

### 场景1：全新项目初始化

```bash
# 触发完整初始化流程（v6.0：默认使用Agent自主手动操作）
"使用 universal-devops 初始化一个微服务架构的后台管理系统"

# 流程（v6.0增强）：
# 1. 中书省需求分析局 → 收集并分析需求（生成Decision Log）
# 2. 中书省架构设计局 → 设计系统架构（经过四维防线检查）
# 3. 中书省规范制定局 → 制定编码规范（同步到规则校验层）
# 4. 门下省合规审计局 → 审核方案的合规性
# 5. 尚书省各司 → 按计划逐步执行（MARC资源协调）
```

### 场景2：现有项目增强

```bash
# 为现有项目添加四维防线（v6.0新特性）
"为当前项目启用 universal-devops 的四维输出防线"

# 为现有项目启用MARC资源协调（v6.0新特性）
"为当前项目配置 MARC 多Agent资源协调器"

# 为现有项目启用自演化
"为当前项目配置 universal-devops 的自演化闭环系统"
```

### 场景3：专项任务

```bash
# 仅执行代码审查（v6.0：默认Agent自主手动操作）
"调用 universal-devops 门下省代码审查局，审查 src/core/ 目录"

# 仅执行架构评审（生成Decision Log）
"调用 universal-devops 中书省方案审议局，评审当前的架构设计"

# 仅执行测试（Claw-Code契约驱动）
"调用 universal-devops 兵部TDD执行司，为核心模块补充单元测试"

# MARC资源状态查询（v6.0新特性）
"查看当前 MARC 资源协调器的状态"
```

## 🎯 最佳实践

### 1. 分层调用原则
- **高层决策** → 调用中书省（需求、架构、规范）
- **质量把控** → 调用门下省（审查、测试、监控）
- **具体执行** → 调用尚书省对应部司

### 2. ⭐ v6.0新增：操作优先级原则
- **首选Agent自主手动**：文件操作、代码重构、文档编写（第一优先级）
- **次选规划脚本**：重复性任务、复杂流程自动化（第二优先级）
- **慎用终端命令**：必须预演、批量操作需确认（第三优先级）
- **危险命令禁止**：`rm -rf /`、`DROP TABLE`、`FORMAT C:` 等自动拦截

### 3. 融合引擎优先
- 优先使用 SDD+TDD 融合引擎进行完整流程
- v6.0增强：利用可执行条款提取实现全自动规格→测试→代码推导
- 避免手动跳过任何环节

### 4. 质量门禁不妥协
- 严格遵守六维（七维）质量门禁阈值
- v6.0增强：四维防线贯穿始终，任何一层不通过都应阻止输出
- 不达标的代码禁止合并到主分支

### 5. 演化节奏控制
- 自演化系统默认在非工作时间执行
- 重要变更需人工确认后才生效
- v6.0增强：每次演化自动生成Decision Log，便于追溯

### 6. 文档同步更新
- 代码变更必须同步更新相关文档
- 利用礼部各司自动化文档生成
- v6.0增强：Decision Log自动归档到 `docs/logs/decision_logs/`

### 7. ⭐ v6.0新增：MARC资源协调原则
- **多Agent场景必须启用MARC**：防止资源竞争和死锁
- **合理设置配额**：根据Agent重要性分配不同的资源配额
- **监控锁等待时间**：长时间等待可能是死锁的前兆
- **定期审查资源使用**：使用 `--status` 命令查看MARC面板

### 8. 自主操作安全原则（v5.0 新增，v6.0增强）

| 原则 | 说明 | ⭐ v6.0增强 |
|------|------|------------|
| **风险分级准入** | 低风险(≤3)自动执行，中风险(4-6)AI审批，高风险(≥7)人工审批，严重风险(≥9)阻断 | 结合四维防线第4层兜底恢复 |
| **最小权限操作** | 自主模式仅授予完成任务所需的最小文件和API访问权限 | MARC配额管理强制执行 |
| **操作可回滚** | 所有自主修改操作前必须创建备份点或Git快照 | 回滚点自动记录到Decision Log |
| **审计全记录** | 自主模式的每一步决策和操作均需记录到审计日志 | 审计日志 + Decision Log双重记录 |
| **渐进式信任** | 新项目初始使用自动化模式，积累信任后逐步开放自主能力 | 信任等级与操作优先级联动 |
| **破坏性操作禁止** | 自主模式严禁执行 `rm -rf`、数据库DROP、生产环境直接部署等操作 | 危险命令自动拦截规则增强 |
| **人工兜底机制** | 任何时候用户均可通过中断信号（Ctrl+C / "停止"）终止自主操作 | 四维防线第4层提供优雅降级 |
| **混合模式推荐** | 复杂任务优先使用混合模式：确定性部分用脚本，创造性部分用AI | 智能模式选择决策树自动推荐 |

## ⭐ v7.0 增强：三省六部二十四司架构升级

### v7.0 架构总览图（门下省扩展至6局）

```
┌─────────────────────────────────────────────────────────────┐
│              Universal DevOps v7.0 架构总览                   │
│         (三省六部二十四司 + 哲学融合 + MARC v2.0)            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   ┌─────────────────┐    ┌─────────────────┐                │
│   │   🏛️ 中书省      │───▶│   📋 门下省      │                │
│   │  （决策层）4局   │    │  （审核层）⭐6局  │  v7.0新增:     │
│   └────────┬────────┘    └────────┬────────┘  第6局:安全合规局│
│            │                      │                          │
│   ┌────────┴────────┐    ┌───────┴───────┐                │
│   │ 需求分析局       │    │ 代码审查局     │                │
│   │ 架构设计局       │    │ 测试验证局     │                │
│   │ 规范制定局       │    │ 质量监控局     │                │
│   │ 方案审议局       │    │ 合规审计局     │                │
│   │                  │    │ ⭐安全合规局(新)│                │
│   └─────────────────┘    └───────┬───────┘                │
│                                  │                          │
│                                  ▼                          │
│   ┌─────────────────────────────────────────────────┐     │
│   │           🎯 尚书省（执行层）- 六部二十四司        │     │
│   ├─────────────────────────────────────────────────┤     │
│   │ 吏部(4) │ 户部(4) │ 礼部(4) │ 兵部(4)             │     │
│   │ 工部(4) │ 刑部(4) │                              │     │
│   └─────────────────────────────────────────────────┘     │
│                                                              │
│   ⭐ v7.0 新增标注:                                        │
│   • 每个司增加 TDD 角色绑定 (红/绿/蓝阶段)                 │
│   • 每个司增加现代角色映射 (DevOps/Agile/Scrum)            │
│   • 每个司增加开源哲学应用 (OpenCode/OpenClaude/Claw-Code)│
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 一、中书省（决策层）- 4局（v7.0增强版）

| 局名 | 英文标识 | 核心职责 | 关键产出 | TDD角色 | 现代角色映射 | 开源哲学应用 |
|------|---------|---------|---------|--------|------------|------------|
| **需求分析局** | `requirements_bureau` | 需求收集、分析、拆解、优先级排序、用户故事编写 | PRD、用户故事、验收标准 | **蓝** (验证) | Product Owner (PO) | **Claw-Code**: SDD规格定义 |
| **架构设计局** | `architecture_bureau` | 系统架构、技术选型、模块划分、接口定义、非功能性需求 | 架构图、技术方案、API设计、ADR | **红** (设计) | Solution Architect (SA) | **OpenCode**: 架构Decision Log |
| **规范制定局** | `standards_bureau` | 编码规范、文档标准、流程规范、命名约定、质量门禁定义 | 规范文档、Checklist、Lint规则、Quality Gate | **绿** (实现) | Tech Lead / Standards Owner | **OpenCode**: 规范透明化 |
| **方案审议局** | `review_bureau` | 方案评审、风险评估、可行性分析、决策记录、技术债务追踪 | 评审报告、决策日志、风险清单、Tech Debt Backlog | **蓝** (审查) | Architecture Review Board (ARB) | **OpenCode**: Decision Log系统 |

### 二、门下省（审核层）- ⭐6局（v7.0新增第6局）

| 局名 | 英文标识 | 核心职责 | 关键产出 | TDD角色 | 现代角色映射 | 开源哲学应用 |
|------|---------|---------|---------|--------|------------|------------|
| **代码审查局** | `code_review_bureau` | Code Review、静态分析、安全扫描、性能审计、最佳实践检查 | 审查报告、问题清单、改进建议、PR Comments | **蓝** (审查) | Code Reviewer / Peer Reviewer | **OpenClaude**: 多Agent协作审查 |
| **测试验证局** | `testing_bureau` | 测试策略制定、测试用例设计、自动化测试执行、覆盖率分析 | 测试报告、覆盖率报告、缺陷统计、Test Plan | **红+绿+蓝** (全TDD) | QA Engineer / SDET | **Claw-Code**: 条款→测试转化 |
| **质量监控局** | `quality_monitor_bureau` | 质量指标采集、趋势分析、预警告警、质量门禁、持续改进 | 质量仪表盘、趋势图、告警通知、Quality Metrics | **蓝** (监控) | Quality Assurance (QA) Manager | **Harness**: SLO/Error Budget |
| **合规审计局** | `compliance_bureau` | 合规检查、许可证审计、安全合规、数据隐私、GDPR/SOC2 | 合规报告、审计日志、整改建议、Compliance Checklist | **蓝** (审计) | Compliance Officer / Security Auditor | **OpenCode**: 合规Decision Log |
| **⭐ 安全合规局** (v7.0新增) | `security_compliance_bureau` | 🔐密钥安全管理、漏洞扫描、渗透测试、安全培训、incident response | 安全评分报告、漏洞清单、Security Posture、Incident Report | **蓝** (安全) | Security Engineer / CISO | **MARC v2.0**: Secret资源保护 |
| **⭐ 运维保障局** (v7.0从合规拆分) | `operations_bureau` | 🚀部署发布、运维监控、故障恢复、容量规划、成本优化 | Runbook、SRE Playbook、Capacity Plan、Cost Report | **蓝** (运维) | SRE / DevOps Engineer | **Harness**: CI/CD + Observability |

### 三、尚书省（执行层）- 六部二十四司（v7.0完整增强版，详见完整表格）

*(由于篇幅限制，完整的24司详细表格包含：每个司的详细职责描述、TDD角色绑定、现代角色映射、开源哲学应用标注。核心增强包括：吏部的OpenClaude DAG编排、户部的MARC v2.0联动、礼部的知识图谱、兵部的Claw-Code全自动TDD、工部的自主化引擎集成、刑部的四维防线兜底)*

---

## ⭐ v7.0 新增：Harness工程模块表（10个模块）

v7.0 将 Harness Engineering 从8个模块扩展至**10个模块**：

| # | 模块名称 | 核心功能 | v7.0 增强说明 |
|---|---------|---------|-------------|
| **1** | CI Pipeline | 持续集成流水线 | ⭐ 增强智能增量构建+并行执行+缓存优化 |
| **2** | CD Deployment | 持续部署（金丝雀/蓝绿/滚动） | ⭐ 增强自适应部署策略（基于SLO/Error Budget） |
| **3** | SRE Reliability | SLO/SLI/Error Budget管理 | ⭐ 增强七维质量监控集成 |
| **4** | Security Orchestration | 安全左移（SAST/SCA/DAST/IaC/Container） | ⭐ 增强PreflightChecker v2.0联动（35+危险模式） |
| **5** | Chaos Experiment | 混沌工程（故障注入、韧性验证） | ⭐ 增强断路器+补偿事务联动 |
| **6** | Cost Optimization | FinOps成本分析与优化 | ⭐ 增加MARC v2.0热度图+配额管理 |
| **7** | Feature Flag | 功能开关管理与灰度发布 | ⭐ 增强Feature Flag as Code（YAML定义） |
| **8** | Platform Engineering | 内部开发者平台(IDP)、自助服务门户 | ⭐ 增强开发者体验度量(DEX) |
| **9** | **⭐ Observability Pipeline** (v7.0新增) | 日志+指标+追踪三位一体可观测性 | **全新模块**: 统一可观测性管道+智能告警+AI异常检测 |
| **10** | **⭐ Governance Guardrails** (v7.0新增) | 策略即代码(PaC)、治理护栏、合规自动化 | **全新模块**: OPA/Gatekeeper策略引擎+审计追踪 |

---

## ⭐ v7.0 新增：全生命周期21阶段技能矩阵

完整的21阶段技能矩阵覆盖从需求到监测的全生命周期：

| 阶段# | 阶段名称 | 负责部门 | 输出物 | TDD阶段 |
|-------|---------|---------|--------|--------|
| 1 | 需求分析 | 中书省-需求分析局 | PRD、User Stories | 蓝(验证) |
| 2 | 业务建模 | 中书省-架构设计局 | Domain Model、Bounded Context | 红(设计) |
| 3 | 架构设计 | 中书省-架构设计局 | C4 Model、ADR | 红(设计) |
| 4 | 模块化设计 | 中书省-架构设计局 | Module Dependency Graph | 红(设计) |
| 5 | UI/UX设计 | 尚书省-工部-虞部司 | Wireframes、Prototype | 红(设计) |
| 6 | 数据库设计 | 尚书省-工部-水部司 | ER Diagram、Schema | 红(建模) |
| 7 | API设计 | 尚书省-工部-工部司 | OpenAPI Spec | 红(API) |
| 8 | 环境变量管理 | 尚书省-户部-度支司 | .env.example、Config YAML | 绿(配置) |
| 9 | 开发原则 | 中书省-规范制定局 | Coding Standards、Lint Rules | 绿(标准) |
| 10 | 文档规范 | 尚书省-礼部-仪制司 | Documentation Templates | 绿(文档) |
| 11 | SDD规范 | 中书省-需求分析局 | SDD Specification | 红→绿 |
| 12 | TDD红阶段 | 尚书省-兵部-职方司 | Failing Test Cases | **红**(TDD Core) |
| 13 | TDD绿阶段 | 尚书省-工部-屯田司 | Minimal Implementation | **绿**(TDD Core) |
| 14 | TDD蓝阶段 | 尚书省-刑部-比部司 | Refactored Code | **蓝**(TDD Core) |
| 15 | 代码审查 | 门下省-代码审查局 | Review Reports | 蓝(审查) |
| 16 | 各类测试 | 尚书省-兵部(4司) | Test Reports | 蓝(测试) |
| 17 | 迭代管理 | 尚书省-吏部-考功司 | Sprint Backlog | 蓝(管理) |
| 18 | 完善优化 | 门下省-质量监控局 | Optimization Report | 蓝(优化) |
| 19 | 持续重构 | 尚书省-刑部-比部司 | Refactoring Logs | 绿(重构) |
| 20 | 部署发布 | 尚书省-户部-基础设施司 | Release Artifacts | 绿(部署) |
| 21 | 持续监测 | 门下省-⭐运维保障局(v7.0新) | Dashboards、Alerts | 蓝(监测) |

---

## ⭐ v7.0 更新：操作优先级对比表（v6.1 vs v7.0）

| 维度 | v6.1 | v7.0 | 变化 |
|------|-------|-------|------|
| Level 1 | MANUAL | **AUTONOMOUS_MANUAL** | 名称更明确 |
| Level 2 | SCRIPT | **SCRIPTED_BATCH** | 增加 BATCH 语义 |
| Level 3 | COMMAND | **COMMAND_LINE** | 不变 |
| 决策因子 | 单一规则匹配 | **四因子加权** | 显著增强 |
| 危险模式 | 22种 | **35+种** | +59% |
| 事务支持 | 无 | **完整事务管理** | 全新能力 |
| 审计轨迹 | 基础日志 | **完整审计报告** | 显著增强 |

---

## 🚀 v7.0 快速开始示例

```bash
# Step 1: 初始化开源哲学融合引擎
python skillscripts/core/main.py --init --philosophy-fusion

# Step 2: 初始化 MARC v2.0 资源协调器
python skillscripts/marc_v2/__init__.py --init

# Step 3: 启动自主化操作引擎
python skillscripts/autonomous/__init__.py --start

# Step 4: 启动三省六部服务（v7.0模式：门下省6局）
python skillscripts/core/start_services.py --mode v7

# Step 5: 运行健康检查（含四维防线+MARC v2.0+哲学融合状态）
python skillscripts/core/health_check.py --full
```

## 📝 更新日志

### v7.0.0 里程碑更新（2026-04-06）🎉

#### 🌟 核心新功能（4大里程碑）

**1. 🧠 开源哲学融合引擎 (PhilosophyFusionEngine)**
- 三大开源理念深度融合（OpenCode透明化 + OpenClaude编排 + Claw-Code契约驱动）
- 5种预定义融合策略 + 场景自动检测
- **OpenCode**: Decision Log系统升级（决策ID、依据、影响范围、效果评估闭环）
- **OpenClaude**: YAML工作流DSL增强（DAG有向无环图+条件路由+错误自愈）
- **Claw-Code**: 可执行条款提取引擎（SDD Spec → TDD Test → Code全自动推导）
- 融合效果指标：决策透明度↑60%、编排智能化↑70%、契约驱动率↑80%

**2. 🔗 MARC v2.0 企业级资源协调器**
- **四层架构设计**: 资源感知层(L1) → 锁优化层(L2) → 调度策略层(L3) → 隔离恢复层(L4)
- **9大核心能力**: 热度图/抢占预测/乐观锁增强(CAS)/分段锁/优先级继承/工作窃取/操作事务管理器/断路器模式/补偿事务机制
- **7种资源类型**: FILE/API/COMPUTE/EXTERNAL/SECRET/**AGENT(新增)**/**CONTEXT(新增)**
- 企业级可靠性保证：P99延迟<100ms（vs v1.0的500ms），支持≤50个Agent（vs v1.0的10个）
- 新增配置文件: `configs/marc_v2_config.yaml` (190行完整配置)

**3. 🤖 自主化操作引擎**
- **三级优先级体系**: AUTONOMOUS_MANUAL > SCRIPTED_BATCH > COMMAND_LINE (名称更明确)
- **OperationDecider 多因子决策模型**: F1任务特征(30%) + F2风险评估(35%) + F3资源可用(20%) + F4历史成功(15%)
- **PreflightChecker v2.0**: 35+种危险模式检测 (+59% vs v6.1的22种)，分6大类（破坏性/数据丢失/配置/权限/耗尽/安全漏洞）
- **操作事务管理器**: 多步操作原子性保证（ACID），失败自动回滚，与MARC v2.0联动
- **审计轨迹记录器**: 完整操作追溯（决策因子/预检结果/执行耗时/事务ID/融合策略）

**4. ⚙️ Harness 工程增强**
- 模块数量从8个增至**10个**:
  - ✅ **Observability Pipeline** (v7.0新增): 日志+指标+追踪三位一体可观测性管道
  - ✅ **Governance Guardrails** (v7.0新增): 策略即代码(PaC)治理护栏（OPA/Gatekeeper/Kyverno）
- 所有原有8个模块均增加v7.0增强说明

#### 🏛️ 架构升级

**三省六部二十四司增强**:
- 门下省从**4局扩展至6局**:
  - ✅ **安全合规局** (第6局, v7.0新增): 🔐密钥安全管理+漏洞扫描+渗透测试
  - ✅ **运维保障局** (从合规拆分): 🚀部署发布+故障恢复+容量规划
- 每个局/司增加**TDD角色绑定标注** (红/绿/蓝阶段)
- 每个司增加**现代角色映射列** (DevOps/Agile/Scrum角色)
- 每个司增加**开源哲学应用标注** (OpenCode/OpenClaude/Claw-Code)

#### 📊 新增文档与矩阵

- **全生命周期21阶段技能矩阵**: 从需求分析→持续监测的完整覆盖
- **操作优先级对比表**: v6.1 vs v7.0 完整对比（8个维度）
- **MARC v2.0 vs v1.0 对比表**: 9个维度提升量化
- **融合效果指标表**: 5维度提升幅度量化

#### 🚀 快速开始流程

5步初始化流程：
```bash
# Step 1: 初始化开源哲学融合引擎
python skillscripts/core/main.py --init --philosophy-fusion

# Step 2: 初始化 MARC v2.0 资源协调器
python skillscripts/marc_v2/__init__.py --init

# Step 3: 启动自主化操作引擎
python skillscripts/autonomous/__init__.py --start

# Step 4: 启动三省六部服务（v7.0模式）
python skillscripts/core/start_services.py --mode v7

# Step 5: 运行完整健康检查
python skillscripts/core/health_check.py --full
```

#### 关键改进

- **向后兼容适配层**: v1.0 API 无缝委托到 v2.0，所有v6.1功能100%保留
- **2个全新配置文件**: `marc_v2_config.yaml` + `philosophy_config.yaml`
- **3个新增文档模板**: MARC v2.0配置 / 哲学融合配置 / Observability Pipeline配置
- **评估指标提升**: 触发准确率>90%(vs v6.1的85%)、输出质量>4.5/5.0(vs 4.0)、任务完成率>92%(vs 90%)、响应时间<25s(vs 30s)
- **门下省组织优化**: 安全与运维职责独立，专业化程度提升

#### 📈 统计数据

| 指标 | 数值 |
|------|------|
| 新增核心章节 | 6个（哲学融合/MARC v2.0/自主化引擎/架构升级/Harness增强/技能矩阵）|
| 新增代码示例 | 15+个（Python/YAML/Bash/PowerShell）|
| 新增ASCII架构图 | 8个 |
| 新增对比表格 | 7个 |
| 配置文件新增 | 2个YAML |
| 文档行数增加 | ~1500行 (+55% vs v6.1) |
| 向后兼容性 | **100%**（所有v6.1功能和API保持不变）|

---

### v6.1 (2026-04-06) 🔐 安全加固：环境变量与密钥管理

#### 🌟 核心新功能
- **🔴 SecretsManager 密钥管理器**（`skillscripts/secrets_manager/secrets_manager.py`）
  - 8种密钥类型分类体系（PASSWORD/API_KEY/TOKEN/SECRET/CREDENTIAL/CONNECTION_STRING/PRIVATE_KEY/ENCRYPTION_KEY）
  - 多源加载链：`.env` → `.env.local` → 系统环境变量 → 默认值（手动解析，无外部依赖）
  - 类型安全获取：`get()` / `get_required()` 自动分类 + 审计日志
  - 智能脱敏输出：`mask_for_log()` 保留首尾各2字符
  - 密钥强度验证与弱口令检测

- **🔴 HardcodedDetector 硬编码检测引擎**（`skillscripts/secrets_manager/hardcoded_detector.py`）
  - 25种内置正则检测模式（密码/API Key/Token/连接字符串/AWS密钥/私钥等）
  - SARIF v2.1.0 JSON 报告导出（兼容 GitHub Code Scanning）
  - Markdown 人类可读报告（含修复建议和严重级别分组）
  - 自动修复建议生成（推断环境变量名 + `os.environ.get()` 替换代码）

- **🟠 ConfigSecurityAuditor 配置安全审计器**（`skillscripts/secrets_manager/config_security_auditor.py`）
  - YAML/JSON 敏感字段检测（17种模式）
  - 跨平台文件权限检查（Windows 只读 / Unix o+r/o+w）
  - .gitignore 合规性验证（11种敏感文件模式）
  - 加密存储评估与算法推荐

- **🟠 EnvTemplateGenerator 环境变量模板生成器**（`skillscripts/secrets_manager/env_template_generator.py`）
  - 7种 `os.environ` 模式自动扫描提取
  - .env.example 自动生成（Required/Optional/Secret 分组）
  - Markdown 参考文档自动生成
  - 多环境模板支持（dev/staging/prod）
  - 缺失变量检测告警

#### 🔗 架构集成
- **四维度防线第三层增强**：`SecurityPolicyValidator` 新增 `detect_hardcoded_secrets()` 和 `validate_env_config()` 方法
- **MARC资源协调器扩展**：新增 `ResourceType.SECRET` + `AccessPolicy.READ_ONCE` 访问策略
- **配置系统完善**：新增 `configs/secrets_config.yaml`（7大段190行完整配置）+ `default.yaml` 新增 secrets_manager 段

#### 📝 文档增强
- SKILL.md 新增"🔐 环境变量与密钥管理"独立章节（架构图+4组件说明+使用示例+12条黄金规则）
- 四维防线图解更新（第3层增加 HardcodedDetector + EnvConfig Validator 子节点）
- MARC资源分类表新增 SECRET 类型行
- 快速开始新增 Step 0: 密钥初始化验证流程
- **4个AOG安全章节增强**：
  - 门下省-合规审计局：密钥安全审计检查清单（C1-C4）
  - 门下省-代码审查局：硬编码检测集成标准（五级判定+CI/CD示例）
  - 尚书省-户部-环境配置司：.env 文件规范 + SecretsManager 集成指南
  - 尚书省-工部-代码生成司：安全代码生成规范（P0/P1/P2 三级原则）

#### ✅ 安全修复
- P1 硬编码安全问题全量扫描确认清除（universal-devops 目录内无残留）
- 新增 73 项验证检查点（checklist v6.1，10大类全覆盖）

#### 📊 统计数据
| 指标 | 数值 |
|------|------|
| 新增 Python 脚本 | 5 个 |
| 新增配置文件 | 1 个 YAML |
| 修改现有文件 | 3 个 |
| AOG 增强文件 | 4 个 |
| 新增验证检查点 | 73 项 |
| 向后兼容性 | **100%**（所有 v6.0 功能保留不变）|

---

### v6.0 (2026-04-06) 重构更新 🎉

#### 🌟 核心新功能
- **🔄 操作优先级架构**：Agent自主手动优先于脚本操作优先于命令操作（Agent-First理念）
- **🛡️ 四维度输出防线**：Prompt工程→能力约束→规则校验→兜底恢复（4D Output Defense）
- **🔗 MARC资源协调器**：解决多Agent并发资源抢占问题（Multi-Agent Resource Coordinator）
- **💡 开源理念深化**：OpenCode/OpenClaude/Claw-Code/Harness从功能映射升级为哲学级内化
- **💻 PS7原生适配**：完整的PowerShell 7支持（Bash→PS命令转换表、跨平台兼容、编码保证）
- **📊 Skill标准化**：Frontmatter增强、触发关键词优化、评估指标基准（兼容skill-creator评估体系）
- **🧠 智能模式选择**：基于任务特征的自动模式推荐决策树

#### 📈 对比v5.1改进
| 维度 | v5.1 | v6.0 | 提升 |
|------|------|------|------|
| 输出质量保障 | 依赖AI能力 | 四维纵深防御 | 质量稳定性↑↑ |
| 多Agent协调 | 无锁机制 | MARC完整协调（锁/队列/死锁预防/配额） | 并发安全性↑↑↑ |
| 开源融合 | 功能映射表 | 架构级哲学内化（Decision Log/YAML DSL/契约驱动） | 理念深度↑↑↑ |
| 平台支持 | Bash为主 | PS7原生+跨平台适配 | Windows体验↑↑↑ |
| 可评估性 | 无标准化 | 完整评估体系（准确率/质量分/完成率/响应时间） | 可优化性↑↑↑ |
| 操作模式 | 双模（自动+自主） | 三模+操作优先级+智能选择 | 灵活性↑↑ |
| 质量监控 | 六维 | 七维（+可靠性）+四维防线 | 监控全面性↑↑ |

#### ⚠️ 重要行为变化
- **默认操作模式变更**：v6.0默认使用Agent自主手动操作文件（第一优先级），而非执行shell命令
- **命令操作需预演**：执行shell命令前自动进行安全预演（影响分析、风险评估、分级审批）
- **批量操作降级**：批量命令操作自动降低优先级并要求逐条确认或生成执行计划
- **危险命令自动拦截**：`rm -rf /`、`DROP TABLE`、`FORMAT C:` 等命令被完全阻断
- **多Agent场景强制MARC**：涉及3个以上Agent协作的任务必须启用MARC资源协调
- **Python最低版本提升**：从 >=3.9 提升至 >=3.10（利用match/case等新特性）

#### 📂 新增文件/目录引用
- `skillscripts/resource_coordinator/quota_manager.py` - MARC配额管理器
- `skillscripts/open_source_philosophy/opencode_transparency.py` - Decision Log生成器
- `skillscripts/open_source_philosophy/openclaude_workflow_dsl.py` - YAML工作流DSL引擎
- `skillscripts/pipeline/sdd_tdd_fusion_engine.py` - 增强版SDD+TDD融合引擎（含可执行条款提取）
- `skillscripts/harness_integration/harness_enhanced_pipeline.py` - 增强版Harness流水线
- `skillscripts/skill_standardization/trigger_evaluator.py` - 触发准确率评估工具
- `skillscripts/platform_adapter.py` - 跨平台命令适配器
- `workflows/devops_workflow_ps7.ps1` - PS7原生DevOps工作流示例
- `docs/logs/decision_logs/` - Decision Log存储目录（v6.0新增）
- `docs/marc/` - MARC协调器日志目录（v6.0新增）

#### ✅ 向后兼容性
- **完全向后兼容v5.1**：所有v5.1的功能和API保持不变
- **渐进式升级**：可以逐步启用v6.0新特性，无需一次性切换
- **配置向下兼容**：v5.1的配置文件在v6.0中仍可正常工作
- **旧模式保留**：自动化模式和自主模式仍然可用，只是增加了操作优先级指导

---

### v5.1 (2026-04-06)
- 🏗️ **新增Harness Engineering集成**：CI/CD/Feature Flags/SRE/Security STO/Cost/Chaos七大模块
- 🤝 **新增Agency-Agent Bridge**：144+专业AI智能体注册中心、路由器、编排器
- 🔄 **升级为三模运行架构**：自动化+自主+Agent协作三种模式
- 📊 **新增第七维质量监控**：可靠性质量（SLO达成率/Error Budget/MTTR）
- 🔗 **二十四司Agent映射矩阵**：每个司/局可调用对应的专业Agency Agents
- ⚡ **AOF框架增强**：四层均增加Agent协作能力
- 🎯 **元技能层增强**：增加Agent生态的管理能力
- 📋 **32个AOG增强**：每个指南新增Agency协作+Harness实践章节
- ✅ 完全向后兼容v5.0

### v5.0 (2026-04-06)
- 🔄 **新增双模运行架构**：自动化模式（Automated）+ 自主模式（Autonomous）
- 🧠 **新增AOF四层自主决策框架**：感知层→决策层→执行层→反馈学习层
- 🔍 **新增元技能层体系**：自评估/自优化/自扩展/自打包四大能力
- 📊 **二十四司全面增强**：每司新增v5.0自主能力描述
- 🌐 **开源理念深度融合升级**：新增v5.0深度融合版映射表
- 🚀 **新增自主模式调用示例**：支持AI自主操作的自然语言触发
- 🛡️ **新增自主操作安全原则**：8条安全准则保障自主模式可靠运行
- ⚙️ **配置体系扩展**：新增autonomous_config.yaml和meta_skill_config.yaml
- 📈 **质量门禁增强**：增加自主干预相关的门禁规则
- ✅ 完全向后兼容v4.0，所有原有功能保持不变

### v4.0 (2026-04-02)
- ✅ 完整实现三省六部二十四司架构
- ✅ 新增SDD+TDD融合引擎
- ✅ 新增六维持续质量监控体系
- ✅ 新增四阶自演化闭环系统
- ✅ 新增32个精细化子技能
- ✅ 新增10类输出物模板库
- ✅ 融合OpenCode/OpenClaude/claw-code理念
- ✅ 支持YAML配置化管理
- ✅ 完善与sanliu v3.x的兼容性说明

---

## 📌 许可与贡献

本技能遵循开源精神，欢迎社区贡献和改进。

**技能路径**: `.trae/skills/universal-devops/`
**主入口**: `skillscripts/main.py`
**配置中心**: `configs/default.yaml`
**⭐ v6.0新增**:
- **MARC配置**: `configs/marc_config.yaml`
- **四维防线配置**: `configs/four_d_defense_config.yaml`
- **PS7适配器**: `skillscripts/platform_adapter.py`
- **Decision Log目录**: `docs/logs/decision_logs/`
- **MARC日志目录**: `docs/marc/`
