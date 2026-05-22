# 知识管理司 自主操作指南 (Autonomous Operation Guide)

## 概述

知识管理司（knowledge_base_si）是尚书省礼部负责技术知识资产治理的核心单元。本司维护包含23种GOF设计模式完整库、30+最佳实践条目、以及从Code Review和Bug Fix中持续提炼的经验沉淀系统。本司以"让每次错误只发生一次、每个经验被最大化复用"为使命，构建概念间的关系网络（知识图谱），并提供语义检索能力接口。

**核心目标：**
- 维护23种GOF设计模式的完整知识库，每种模式含适用场景/代码示例/反模式
- 积累30+从真实项目中提炼的最佳实践与经验法则
- 构建知识图谱：模式→原则→反模式→示例的关联网络
- 从Code Review中自动识别并沉淀常见问题的解决方案
- 从Bug Fix记录中提取缺陷模式和预防措施
- 提供384维向量语义检索接口（预留），支持自然语言查询

## 核心原则

1. **经验复用优先（Reuse Over Reinvention）**：遇到问题时先查知识库，已有解决方案直接复用而非重新发明
2. **来源可追溯（Traceable Origin）**：每条知识必须标注来源（项目/PR/Issue/作者），支持溯源验证
3. **渐进式成熟度（Progressive Maturity）**：知识条目经历 Proposed → Validated → Canonical 的成熟度晋升流程
4. **去重与合并（Deduplicate & Merge）**：相似知识自动聚类合并，避免知识膨胀
5. **语境感知（Context-Aware）**：推荐方案时考虑调用者的技术栈、项目阶段、团队能力等上下文
6. **主动进化（Proactive Evolution）**：知识不是静态资产，随技术生态演进而持续更新

## 自主操作流程

### 阶段一：感知（Perceive）

**1.1 知识信号采集源**

```
实时信号源：
├── Code Review 事件
│   ├── PR中的review comment（建议类、问题类）
│   ├── PR description中的"lessons learned"
│   └── approve/request changes 决策理由
│
├── Bug Fix 事件
│   ├── issue 标记为 bug 并被关闭
│   ├── commit message 含 "fix" 类型
│   ├── root cause analysis 文档
│   └── postmortem 报告
│
├── 技术讨论事件
│   ├── 内部wiki编辑
│   ├── 技术分享会纪要
│   ├── 架构决策记录（ADR）
│   └── Slack/钉钉/飞书中的技术问答
│
└── 外部信号源
    ├── 官方文档更新通知
    ├── 安全公告（CVE/NVD）
    ├── 技术博客/RSS订阅
    └── 社区最佳实践趋势变化
```

**1.2 23种GOF设计模式完整清单**

#### 创建型模式（Creational Patterns）— 5种

| # | 模式名称 | 英文 | 核心意图 | 典型适用场景 |
|---|----------|------|----------|--------------|
| C1 | 工厂方法 | Factory Method | 定义创建对象的接口，让子类决定实例化哪个类 | 框架扩展点、日志框架切换 |
| C2 | 抽象工厂 | Abstract Factory | 创建相关或依赖对象家族，无需指定具体类 | UI主题切换、数据库驱动族 |
| C3 | 建造者 | Builder | 分步构建复杂对象，同样构造过程可产生不同表示 | 配置对象构建、DSL解析器 |
| C4 | 原型 | Prototype | 通过复制原型创建新对象 | 大对象克隆、对象池管理 |
| C5 | 单例 | Singleton | 确保类只有一个实例，提供全局访问点 | 配置管理器、连接池、日志器 |

#### 结构型模式（Structural Patterns）— 7种

| # | 模式名称 | 英文 | 核心意图 | 典型适用场景 |
|---|----------|------|----------|--------------|
| S1 | 适配器 | Adapter | 将一个类的接口转换成客户期望的另一个接口 | 第三方SDK适配、遗留系统集成 |
| S2 | 桥接 | Bridge | 将抽象部分与实现部分分离，使二者独立变化 | 跨平台UI、多数据库支持 |
| S3 | 组合 | Composite | 将对象组合成树形结构以表示"部分-整体"层次 | 文件系统、UI组件树、组织架构 |
| S4 | 装饰器 | Decorator | 动态地给对象添加额外职责 | 日志装饰、缓存装饰、权限装饰 |
| S5 | 外观 | Facade | 为子系统中的一组接口提供一个统一的高层接口 | 复杂子系统封装、API网关 |
| S6 | 享元 | Flyweight | 运用共享技术有效支持大量细粒度对象 | 字符串常量池、游戏对象渲染 |
| S7 | 代理 | Proxy | 为其他对象提供一种代理以控制对这个对象的访问 | 懒加载、远程代理、保护代理 |

#### 行为型模式（Behavioral Patterns）— 11种

| # | 模式名称 | 英文 | 核心意图 | 典型适用场景 |
|---|----------|------|----------|--------------|
| B1 | 职责链 | Chain of Responsibility | 避免请求发送者与接收者耦合，将请求沿链传递 | 中间件管道、审批流、异常处理链 |
| B2 | 命令 | Command | 将请求封装为对象，从而可用不同的请求对客户进行参数化 | 操作撤销/重做、任务队列、事务 |
| B3 | 解释器 | Interpreter | 给定语言定义其文法表示，并定义一个解释器 | SQL解析器、模板引擎、配置文件解析 |
| B4 | 迭代器 | Iterator | 提供一种方法顺序访问聚合对象中元素而不暴露其底层表示 | 集合遍历、分页查询、流式处理 |
| B5 | 中介者 | Mediator | 封装一系列对象交互，使各对象不需要显式引用 | 聊天室、MVC控制器、事件总线 |
| B6 | 备忘录 | Memento | 捕获并恢复对象的内部状态而不破坏封装性 | 撤销机制、游戏存档、事务回滚点 |
| B7 | 观察者 | Observer | 定义对象间一对多的依赖关系，当一个对象改变时所有依赖者收到通知 | 事件系统、响应式编程、发布订阅 |
| B8 | 状态 | State | 对象在其内部状态改变时改变其行为 | 订单状态机、TCP连接、游戏角色状态 |
| B9 | 策略 | Strategy | 定义算法族，使它们可以互相替换且算法的变化独立于客户端 | 支付方式选择、排序算法、压缩格式 |
| B10 | 模板方法 | Template Method | 定义算法骨架，将某些步骤延迟到子类 | 框架基类、数据处理流水线 |
| B11 | 访问者 | Visitor | 将算法与对象结构分离，在不修改结构的前提下定义新操作 | AST遍历、编译器、报表生成 |

**1.3 最佳实践分类索引**

```yaml
best_practices_library:
  架构设计:
    - id: BP-ARCH-001
      name: "领域驱动设计（DDD）分层架构"
      summary: "严格按Domain/Application/Infrastructure/Interface分层，禁止跨层直接调用"
      maturity: canonical
      sources: ["project-alpha", "project-beta", "community-consensus"]

    - id: BP-ARCH-002
      name: "API版本化策略"
      summary: "URL路径版本(/api/v1/)优于Header版本，重大变更使用新版本号而非修改旧版"
      maturity: validated
      sources: ["api-gateway-project"]

    - id: BP-ARCH-003
      name: "CQRS读写分离"
      summary: "高读低写场景下分离Command和Query模型，各自优化数据存储"
      maturity: proposed
      sources: ["internal-research"]

  代码质量:
    - id: BP-CODE-001
      name: "函数单一职责原则（SRP）量化标准"
      summary: "单个函数不超过20行，圈复杂度≤10，参数不超过4个（超出考虑参数对象）"
      maturity: canonical
      sources: ["code-review-stats-2025"]

    - id: BP-CODE-002
      name: "错误处理的统一契约"
      summary: "所有公开API返回统一的Error Response结构{code, message, details, trace_id}"
      maturity: canonical
      sources: ["all-services"]

    - id: BP-CODE-003
      name: "异步操作的超时与取消模式"
      summary: "所有外部调用必须设置超时，支持context/cancellation传播"
      maturity: validated
      sources: ["incident-postmortem-2025-Q3"]

  安全实践:
    - id: BP-SEC-001
      name: "最小权限原则在代码中的落地"
      summary: "每个服务账户仅授予完成任务所需的最小权限集，定期审计"
      maturity: canonical
      sources: ["security-audit-2025"]

    - id: BP-SEC-002
      name: "输入验证的纵深防御策略"
      summary: "在API边界、业务逻辑层、数据持久层三层分别做输入校验"
      maturity: canonical
      sources: ["owasp-top-10-mapping"]

  性能优化:
    - id: BP-PERF-001
      name: "N+1查询检测与预防"
      summary: "ORM查询必须使用eager loading或显式JOIN，禁止循环内单条查询"
      maturity: canonical
      sources: ["performance-audit-2025"]

    - id: BP-PERF-002
      name: "缓存失效策略选择矩阵"
      summary: "根据数据一致性要求选择Cache-Aside/Read-Through/Write-Through策略"
      maturity: validated
      sources: ["cache-design-doc"]

  可观测性:
    - id: BP-OBS-001
      name: "结构化日志三要素规范"
      summary: "每条日志必须包含{timestamp, level, trace_id, service, message, context}"
      maturity: canonical
      sources: ["logging-standard-v2"]

  测试策略:
    - id: BP-TEST-001
      name: "测试金字塔落地比例"
      summary: "单元测试70% / 集成测试20% / E2E测试10%，按此比例分配测试资源"
      maturity: validated
      sources: ["test-coverage-report"]
```

### 阶段二：决策（Decide）

**2.1 知识条目准入评估**

当采集到新的候选知识时，执行以下评估流程：

```
候选知识 → [唯一性检查] → [质量评分] → [相关性判定] → 准入决定

唯一性检查：
  1. 使用语义相似度计算与现有知识条目的距离
  2. 相似度 > 0.85 → 视为重复，合并到现有条目（追加source）
  3. 相似度 0.6~0.85 → 视为相关但不同，建立关联关系
  4. 相似度 < 0.6 → 全新知识，进入新建流程

质量评分（0-100）：
  - 来源可信度（0-25）：官方文档>知名博客>内部文档>口头交流
  - 示例可运行性（0-25）：有可运行的完整代码示例得满分
  - 反面案例覆盖（0-15）：包含"不该怎么做"的反模式说明
  - 适用场景明确性（0-15）：清楚说明何时用何时不该用
  - 语言中立性（0-20）：不绑定特定语言/框架的实现细节

准入阈值：
  score >= 70 → 进入 VALIDATED 状态
  score >= 50 → 进入 PROPOSED 状态，等待更多证据
  score < 50  → 暂不收录，记录到候选池观察
```

**2.2 知识推荐决策**

当开发者发起知识查询时的推荐逻辑：

```python
def recommend_knowledge(query_context):
    """
    query_context 包含：
    - query_text: 自然语言查询文本
    - tech_stack: 当前技术栈标签
    - project_phase: 项目阶段（init/dev/maintain）
    - problem_category: 问题分类（architecture/code/security/perf/test）
    - team_experience_level: 团队经验水平（junior/mid/senior）
    """
    
    # Step 1: 向量语义检索（384维embedding）
    candidates = vector_search(query_text, top_k=20, dimension=384)
    
    # Step 2: 上下文过滤
    filtered = []
    for item in candidates:
        # 技术栈匹配加权
        tech_match = calculate_tech_stack_overlap(item.tech_tags, query_context.tech_stack)
        
        # 项目阶段适配
        phase_fit = evaluate_phase_suitability(item.applicable_phases, query_context.project_phase)
        
        # 团队经验适配（新手团队推荐更详细的条目）
        exp_fit = 1.0 if query_context.team_experience_level == 'senior' \
                   else item.detail_level_score
        
        # 综合排序分数
        item.final_score = (
            item.semantic_similarity * 0.40 +
            tech_match * 0.25 +
            phase_fit * 0.20 +
            exp_fit * 0.15
        )
        filtered.append(item)
    
    # Step 3: 知识图谱关联扩展
    for item in sorted(filtered, key=lambda x: x.final_score)[:5]:
        # 找出与该条目相关的其他知识（通过图谱边关系）
        related = knowledge_graph.get_related_nodes(item.id, depth=2, max_results=3)
        item.related_suggestions = related
    
    return sorted(filtered, key=lambda x: x.final_score, reverse=True)[:10]
```

### 阶段三：执行（Execute）

**3.1 知识条目标准结构**

每条知识条目遵循统一的Schema：

```json
{
  "id": "KB-GOF-S07-PROXY",
  "type": "design_pattern",
  "category": "structural",
  "name": {
    "zh": "代理模式",
    "en": "Proxy Pattern"
  },
  "aliases": ["Surrogate", "Placeholder"],
  "intent": "为其他对象提供一种代理以控制对这个对象的访问",
  "motivation": "在某些情况下，一个对象不适合或者不能直接引用另一个对象，而代理对象可以在客户端和目标对象之间起到中介的作用",
  "applicability": {
    "when_to_use": [
      "远程代理（Remote Proxy）：为一个位于不同地址空间的对象提供本地代表",
      "虚拟代理（Virtual Proxy）：根据需要创建开销大的对象（如懒加载大图）",
      "保护代理（Protection Proxy）：控制对原始对象的访问权限",
      "智能引用（Smart Reference）：取代了简单的指针，在访问对象时执行额外操作"
    ],
    "when_not_to_use": [
      "对象访问没有额外的控制需求时",
      "引入代理会增加系统复杂性，简单场景不值得"
    ]
  },
  "structure": {
    "participants": [
      {"role": "Subject", "desc": "定义RealSubject和Proxy的共同接口"},
      {"role": "RealSubject", "desc": "定义Proxy所代表的真实对象"},
      {"role": "Proxy", "desc": "持有一个RealSubject引用，控制对其的访问"}
    ],
    "collaborations": "Proxy将请求转发给RealSubject，可在前后添加额外行为"
  },
  "examples": [
    {
      "language": "python",
      "title": "虚拟代理 — 懒加载重型资源",
      "code": "...完整可运行示例...",
      "explanation": "演示如何延迟加载大型图像直到真正需要显示时"
    },
    {
      "language": "typescript",
      "title": "保护代理 — 权限控制",
      "code": "...完整可运行示例...",
      "explanation": "演示如何在代理层实现基于角色的访问控制"
    }
  ],
  "anti_patterns": [
    {
      "name": "过度代理",
      "description": "为每个对象都创建代理类，导致类数量爆炸",
      "symptom": "项目中出现大量XxxProxy类，维护困难",
      "solution": "使用动态代理（如Python __getattr__、ES6 Proxy）减少样板代码"
    },
    {
      "name": "代理穿透",
      "description": "绕过代理直接访问真实对象",
      "symptom": "安全控制或懒加载逻辑被绕过",
      "solution": "将RealSubject设为私有/模块级不可导出，仅通过Proxy暴露"
    }
  ],
  "related_patterns": [
    {"pattern": "Adapter", "relation": "都提供间接访问，但Adapter改变接口而Proxy保持相同接口"},
    {"pattern": "Decorator", "relation": "都包装对象，但Decorator关注增强功能而Proxy关注控制访问"},
    {"pattern": "Facade", "relation": "都是间接层，但Facade简化接口而Proxy保持原接口"}
  ],
  "known_uses": [
    "Java动态代理（java.lang.reflect.Proxy）",
    "SQLAlchemy ORM的lazy loading",
    "Vue3的reactive Proxy",
    "gRPC的Stub/Channel代理"
  ],
  "maturity": "canonical",
  "sources": [
    {"type": "book", "ref": "GoF Design Patterns, 1994"},
    {"type": "project", "ref": "project-gamma v2.3 Proxy layer design"},
    {"type": "community", "ref": "refactoring.guru proxy pattern"}
  ],
  "created_at": "2025-01-15T00:00:00Z",
  "updated_at": "2026-03-20T00:00:00Z",
  "version": "2.1",
  "tags": ["proxy", "indirection", "lazy-loading", "access-control", "structural"],
  "search_vector": [0.0123, -0.0456, ...] // 384维embedding（截断展示）
}
```

**3.2 从Code Review中提炼知识**

自动化提炼流程：

```yaml
Code Review 知识提炼管线:

  输入: PR Review Comments + PR Diff
  
  Step 1 — 评论分类:
    分类器将每条review comment归类:
    - style: 代码风格建议（命名、格式）
    - bug: 潜在bug指出
    - performance: 性能改进建议
    - architecture: 架构层面建议
    - security: 安全相关问题
    - best-practice: 最佳实践推荐
    - question: 疑问（非知识性）

  Step 2 — 知识价值评估:
    仅对以下类别触发知识提炼:
    - architecture + 有详细解释 → 高价值候选
    - best-practice + 引用了具体原则 → 高价值候选
    - security + 给出了修复方案 → 高价值候选
    - performance + 附带benchmark数据 → 高价值候选
    - bug + 是反复出现的同类问题 → 高价值候选

  Step 3 — 结构化提取:
    从评论中提取:
    - 问题/现象描述（What）
    - 推荐做法（How）
    - 底层原理/原因（Why）
    - 适用范围（When/Where）
    - 反例/反面教材（Anti-pattern）

  Step 4 — 去重与入库:
    与现有知识库做语义去重:
    - 新知识 → 创建 PROPOSED 条目
    - 已有知识的补充 → 追加 source 和 example
    - 与多条知识相关 → 在知识图谱中建立新的边

  Step 5 — 回馈Review者:
    自动回复确认:
    "感谢您的review意见！已将其作为经验沉淀至知识库 (KB-CR-XXXX)"
```

**3.3 从Bug Fix中学习**

```python
def learn_from_bug_fix(bug_report, fix_commit, root_cause_analysis):
    """
    从一次完整的Bug修复过程中提取可复用的知识。
    """
    
    knowledge_entry = {
        "type": "defect_pattern",
        "id": generate_kb_id("DEFECT"),
        
        # 缺陷画像
        "defect_profile": {
            "symptom": bug_report.symptom_description,
            "severity": bug_report.severity,           # critical/major/minor
            "category": classify_defect_category(bug_report),  # logic/race-condition/resource-leak/etc.
            "detection_method": bug_report.how_found,  # production-alert/user-report/code-review/static-analysis
            "impact_scope": estimate_impact(bug_report),       # affected_users, downtime_minutes
        },
        
        # 根因分析
        "root_cause": {
            "type": root_cause_analysis.cause_type,     # missing-check/timing-issue/config-error/etc.
            "description": root_cause_analysis.explanation,
            "code_location": fix_commit.changed_files,   # 受影响的文件和行号范围
            "trigger_condition": root_cause_analysis.when_it_happens,
        },
        
        # 修复方案
        "fix": {
            "approach": summarize_fix_approach(fix_commit),
            "code_diff": fix_commit.diff_summary,
            "verification": how_fix_was_verified(fix_commit),  # test-added/regression-test/manual-verify
        },
        
        # 预防措施（核心产出）
        "prevention": {
            "coding_guidelines": extract_new_rules(root_cause_analysis),
            "static_analysis_rules": generate_lint_rule_if_applicable(fix_commit),
            "test_strategies": suggest_test_patterns(bug_report, fix_commit),
            "review_checklist_items": generate_review_checkpoints(bug_report),
            "architecture_improvements": suggest_structural_prevention(root_cause_analysis),
        },
        
        # 关联知识
        "related_knowledge": find_related_patterns_and_practices(
            defect_type=root_cause_analysis.cause_type,
            affected_components=fix_commit.changed_files
        ),
        
        "maturity": "proposed",  # Bug Fix衍生的知识默认proposed，需后续验证
        "sources": [
            {"type": "bug_report", "ref": f"Issue #{bug_report.issue_number}"},
            {"type": "fix_commit", "ref": fix_commit.sha},
            {"type": "rca", "ref": root_case_analysis.document_id}
        ]
    }
    
    return knowledge_entry
```

**3.4 知识图谱构建规则**

```
节点类型（Node Types）：
├── Pattern          设计模式节点（23个GOF + 扩展模式）
├── Principle        设计原则节点（SOLID/KISS/DRY/YAGNI等）
├── AntiPattern      反模式节点
├── BestPractice     最佳实践节点
├── DefectPattern    缺陷模式节点（从Bug Fix中提炼）
├── Example          代码示例节点
├── Technology       技术栈/语言/框架节点
└── Concept          通用概念节点

边类型（Edge Types）与权重：
├── implements       Pattern → Principle      [weight: 1.0]  "实现了某个原则"
├── violates         AntiPattern → Principle  [weight: 0.8]  "违反了某个原则"
├── solves           Pattern → ProblemType    [weight: 0.9]  "解决了某类问题"
├── alternative_of   Pattern ↔ Pattern        [weight: 0.7]  "互为替代方案"
├── evolves_into     Pattern → Pattern        [weight: 0.6]  "演进变体"
├── has_example      Pattern → Example        [weight: 0.5]  "拥有示例"
├── prevents         BestPractice → AntiPattern[weight: 0.8]  "防止了某种反模式"
├── addresses        BestPractice → DefectPattern [weight:0.9]"解决了某类缺陷"
├── applicable_in    Pattern/Practice → Tech  [weight: 0.4]  "适用于某技术"
├── related_to       Node ↔ Node              [weight: 0.3]  "一般关联"

图谱遍历策略：
  深度优先（DFS）：用于深入探索某一模式的完整知识网络
  广度优先（BFS）：用于发现相关模式簇（如"所有创建型模式"）
  加权最短路径：用于找到"从当前问题到解决方案的最短知识路径"
```

### 阶段四：Verify（验证）

**4.1 知识条目质量审核**

每条知识在晋升 maturity level 时必须经过验证：

```
PROPOSED → VALIDATED 的条件：
  ✓ 至少2个独立来源佐证（不同项目/不同团队/官方文档）
  ✓ 包含至少1个可运行的代码示例
  ✓ 无已知反例或局限性未被记录
  ✓ 最近90天内被成功应用至少1次

VALIDATED → CANONICAL 的条件：
  ✓ 至少5个独立来源佐证
  ✓ 包含多语言示例（≥2种语言）
  ✓ 经过团队技术评审会议认可
  ✓ 被纳入正式编码规范或培训材料
  ✓ 连续180天内无有效性挑战
```

**4.2 代码示例可运行性验证**

```yaml
示例验证流程:
  1. 提取知识条目中的所有代码块
  2. 按 language 分发到对应语言的沙箱环境
  3. Python: 
     - ast.parse() 语法校验
     - mypy --strict 类型检查（如有类型注解）
     - pytest 运行（如果包含测试用例）
  4. TypeScript:
     - tsc --noEmit --strict 编译检查
     - vitest 运行（如果包含测试用例）
  5. Go:
     - go vet 检查
     - go build 编译验证
     - go test 运行（如果包含 *_test.go）
  6. 通用:
     - 括号/引号配对平衡检查
     - 缩进一致性检查
  7. 结果标记:
     - PASS: 示例完全正确可运行
     - WARN: 语法正确但有lint警告
     - FAIL: 存在语法/类型/逻辑错误 → 阻断晋升
```

**4.3 知识时效性监控**

```yaml
过期检测规则:
  - 规则1: 技术版本过时
    condition: 条目中引用的框架/库版本落后当前稳定版 > 2个minor版本
    action: 标记 "needs-review"，提示更新示例代码

  - 规则2: 官方推荐已变更
    condition: 官方文档/指南中推荐的写法与知识条目不一致
    action: 标记 "potentially-outdated"，追踪官方变更

  - 规则3: 社区共识转移
    condition: 社区投票/调查中该实践的支持率从 >70% 降至 <50%
    action: 标记 "controversial"，追加正反两方观点

  - 规则4: 长期未使用
    condition: CANONICAL级别的条目连续365天无查询/无引用
    action: 标记 "stale"，考虑降级或归档
```

### 阶段五：Record（记录）

**5.1 知识操作审计日志**

```json
{
  "operationId": "kb-op-20260406-007",
  "timestamp": "2026-04-06T16:45:00Z",
  "operator": "knowledge_base_si[autonomous]",
  "operationType": "extract_from_code_review",
  "source": {
    "type": "pull_request_review",
    "pr_number": 203,
    "repository": "core-service",
    "reviewer": "zhangsan",
    "comment_body": "这里应该使用Strategy模式而不是大量的if-else..."
  },
  "action": {
    "result": "knowledge_created",
    "entryId": "KB-BP-CODE-004",
    "entryTitle": "消除条件逻辑的策略模式替换",
    "maturity": "proposed"
  },
  "confidenceScore": 0.82,
  "relatedEntriesLinked": ["KB-GOF-B09-STRATEGY", "KB-ANTI-IF-HELL"],
  "nextReviewDate": "2026-07-06"
}
```

**5.2 知识库统计仪表盘指标**

```yaml
统计维度:
  总量指标:
    - total_entries: 知识条目总数
    - by_maturity: { proposed: N, validated: N, canonical: N }
    - by_type: { design_pattern: 23, best_practice: 30+, defect_pattern: N, ... }

  质量指标:
    - avg_quality_score: 所有条目的平均质量分
    - examples_with_pass_rate: 代码示例通过率
    - stale_entry_count: 过期条目数量

  活跃度指标:
    - queries_per_day: 日均查询量
    - top_queried_entries: 最常被查询的Top10条目
    - extraction_rate: 每周从CR/Bug中提炼的新知识数
    - adoption_rate: 知识被实际采纳应用的比率

  覆盖率指标:
    - pattern_coverage: 23种GOF模式的知识完备度
    - tech_stack_coverage: 各技术栈的知识覆盖情况
    - anti_pattern_catalog: 反模式目录完整性
```

## 典型自主场景

### 场景1：Code Review中的模式识别与知识沉淀

**背景**：高级工程师在PR #203的review中指出一段复杂的条件分发代码应使用策略模式重构。

**自主执行流程：**

1. **感知**：监听到PR review comment，经NLP分类器识别为 `architecture` + `best-practice` 类别，置信度0.89
2. **决策**：评论内容详实且有代码示例指向 → 高价值候选 → 触发知识提取流程
3. **执行**：
   - 从review comment和PR diff中提取：原始if-else代码片段、建议的重构方向、涉及的模块
   - 生成新的知识条目 `KB-BP-CODE-004`："消除长条件链的策略模式实践"
   - 补充Python和TypeScript双语示例代码
   - 在知识图谱中建立与 Strategy模式（KB-GOF-B09）、SRP原则（KB-PRIN-SRP）、反模式"Arrow Anti-Pattern"（KB-ANTI-ARROW）的关联边
   - maturity设为 `proposed`
4. **验证**：
   - 双语示例均通过语法+类型检查 ✓
   - 与现有知识库无重复（相似度最高0.42）✓
   - 质量评分78分 → 达到PROPOSED门槛 ✓
5. **记录**：写入审计日志，向reviewer发送致谢通知

### 场景2：生产事故后的缺陷模式提炼

**背景**：线上服务发生内存泄漏导致OOM重启，经过root cause分析定位为goroutine泄漏——某个请求处理器中启动了goroutine但在错误路径上未正确处理其生命周期。

**自主执行流程：**

1. **感知**：接收到postmortem报告文档，自动解析其中的root cause章节
2. **决策**：这是一个典型的并发缺陷模式 → 属于高价值知识 → 立即提取
3. **执行**：
   - 创建 `KB-DEFECT-017`："Goroutine泄漏 — 未cancel的background worker"
   - 记录缺陷画像：symptom=内存渐进增长直至OOM，category=resource-leak，severity=critical
   - 记录根因：errgroup/context未正确传播cancel信号
   - 提炼预防措施：
     - 编码准则："所有goroutine必须可通过context cancel"
     - Lint规则建议：检测 `go func()` 但体内无 `<-ctx.Done()` 的模式
     - Review checklist新增项："检查所有goroutine是否有退出路径"
     - Test strategy：添加资源泄漏的race detector测试
   - 关联到已有的BestPractice `BP-CODE-003`（异步操作超时与取消模式）
4. **验证**：
   - 预防措施的Lint规则可在golangci-lint中实现 ✓
   - 测试策略已在类似场景验证有效 ✓
   - 与现有知识形成良好互补 ✓
5. **记录**：标记为proposed，安排在下次技术评审会议上讨论是否升级为validated

### 场景3：开发者自然语言查询 — 语义检索

**背景**：一名中级开发者在编写一个新的支付模块，想了解"如何在多种支付方式之间灵活切换而不写大量if-else"。

**自主执行流程：**

1. **感知**：接收到自然语言查询，tech_stack=Python/Django，problem_category=architecture
2. **决策**：这是典型的设计模式查询 → 启动语义检索 + 图谱推理
3. **执行**：
   - 将查询文本转换为384维embedding向量
   - 在向量索引中执行近似最近邻搜索（ANN），获取top-20候选
   - 应用上下文过滤：Python技术栈权重提升、架构类知识优先
   - 综合排序后返回Top-10结果：
     1. **策略模式**（KB-GOF-B09，score=0.94）— 直接命中，含Python支付策略示例
     2. **工厂模式**（KB-GOF-C01/C02，score=0.87）— 相关，可用于创建不同支付处理器
     3. **命令模式**（KB-GOF-B02，score=0.76）— 相关，可用于支付操作的封装与撤销
     4. **BP-ARCH-002 API版本化策略**（score=0.71）— 弱相关但可能有用
     5. ...
   - 对Top-3结果，通过知识图谱扩展推荐关联知识：
     - 策略模式 → 开闭原则(OCP) → "对扩展开放对修改关闭"
     - 策略模式 → 反模式"Switch Statement Hell" → 不该怎么做
     - 策略模式 → Django示例：payment_strategy.py
4. **验证**：推荐结果的相关性由用户反馈闭环优化（thumbs up/down）
5. **记录**：记录查询日志，用于优化检索模型的召回率和精确率

## 决策框架

### 知识生命周期管理

```
                    ┌─────────────┐
     新采集 ──────→ │  PROPOSED   │
                    │  (提议)      │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              ↓ 2+来源证实  │             ↓ 90天无进展
       ┌────────────┐      │      ┌────────────┐
       │  VALIDATED  │      │      │  ARCHIVED   │
       │  (已验证)    │      └────→ │  (已归档)    │
       └──────┬──────┘             └────────────┘
              │
              ↓ 5+来源+评审通过
       ┌─────────────┐
       │  CANONICAL   │
       │  (典范)       │
       └──────┬──────┘
              │
              ↓ 365天无引用
       ┌─────────────┐
       │  DEPRECATED │  ← 或被更好的知识替代
       │  (已废弃)    │
       └─────────────┘
```

### 自主行动边界

| 动作 | 自主执行 | 需确认 | 禁止 |
|------|---------|--------|------|
| 从CR/Bug中提取新知识（PROPOSED级别） | ✅ | — | — |
| 知识条目微调（修正错别字、更新版本号） | ✅ | — | — |
| 知识图谱边的增删（基于明确的关联关系） | ✅ | — | — |
| PROPOSED → VALIDATED 晋升 | — | ✅ 需来源复核 | — |
| VALIDATED → CANONICAL 晋升 | — | ✅ 需技术评审 | — |
| 删除CANONICAl级别知识 | — | ✅ 必须确认 | — |
| 修改安全相关知识条目 | — | ✅ 安全审核 | — |

## 安全与治理

### 知识安全

- 知识条目中不得包含生产环境密钥、内部IP地址、用户个人信息等敏感数据
- 从Code Review和Bug Report提取知识时自动脱敏（变量名、URL、堆栈信息中的敏感字段）
- 不同保密级别的知识实行分级访问控制

### 知识准确性治理

- 每条CANONICAL级别知识每季度复审一次
- 用户可对任何知识条目提交质疑（challenge），触发重新评估流程
- 当知识所基于的技术/框架发生breaking change时，自动标记受影响条目
- 引入"知识衰减曲线"模型，长期未被验证的知识逐步降低推荐权重

### 版权与合规

- 从外部来源提取的知识必须注明出处
- 代码示例遵循对应开源协议（MIT/Apache-2.0等）
- 商业机密和专有算法不得录入公共知识库

## 协作关系

### 上游依赖

| 协作对象 | 交互内容 | 频率 | 协议 |
|----------|----------|------|------|
| Git仓库（PR/Commit） | Code Review comments, Bug Fix commits | 实时 | Webhook + Git CLI |
| Issue跟踪系统 | Bug reports, Postmortem docs | 事件驱动 | REST API |
| 技术Wiki/Confluence | 架构文档, ADR, 技术分享 | 定时爬取 | RSS/API |
| 外部技术社区 | 官方文档更新, CVE公告, 博客 | 定时轮询 | RSS/WebFetch |

### 下游消费者

| 协作对象 | 提供内容 | 格式 | 更新策略 |
|----------|----------|------|----------|
| 开发者（查询端） | 知识搜索结果、模式推荐 | 结构化JSON + Markdown | 实时查询 |
| documentation_si | 知识条目→文档素材 | Markdown片段 | 变更时推送 |
| template_management_si | 最佳实践→模板内置checklist | Checklist JSON | 定期同步 |
| standardization_si | 编码规范→Lint规则 | Rule definition | 变更时推送 |
| 培训系统 | 知识库→课程内容 | 课程大纲 + 示例 | 按需导出 |

### 同级协作

| 协作对象 | 协作场景 | 协议 |
|----------|----------|------|
| 其他三司 | 跨域知识共享、联合巡检报告 | 共享事件总线 |
| AI编码助手 | 知识库作为上下文注入编码建议 | Embedding API + RAG |

---

## 🤝 v5.1 增强：Agency Agent 协作指南

### 可调用的 Agency Agents

| Agent 名称 | 所属部门 | 协作模式 | 适用场景 |
|-----------|---------|---------|---------|
| ZK Steward | 知识治理部 | 双向同步 | Zettelkasten知识管理方法落地与维护 |
| Developer Advocate | 开发者生态部 | 内容分发 | 开发者经验沉淀、技术分享与社区互动 |

### Agent 协作工作流

1. **知识采集触发**：knowledge_base_si 从Code Review/Bug Fix/技术讨论中识别高价值知识候选
2. **初步处理**：本司完成去重、质量评分和结构化提取，生成PROPOSED级别知识条目
3. **Agent 委派**：
   - 知识条目需要按Zettelkasten方法组织永久笔记 → 调用 **ZK Steward** 执行原子化拆分、双向链接建立、笔记网络拓扑优化
   - 知识条目具备广泛传播价值 → 调用 **Developer Advocate** 将技术要点转化为博客文章、技术分享PPT或社区教程
4. **协同验证**：ZK Steward 返回的笔记网络经knowledge_base_si的图谱一致性校验后入库；Developer Advocate 产出的内容反向丰富知识库的外部引用来源
5. **持续演化**：定期由ZK Steward审计笔记网络的链接健康度和结构均衡性，由Developer Advocate追踪内容的影响力和反馈
6. **闭环反馈**：开发者通过知识库查询或阅读生态内容后的反馈，驱动知识条目的成熟度晋升（PROPOSED → VALIDATED → CANONICAL）

### 典型协作场景

- **场景1 - 架构决策记录（ADR）知识转化**：knowledge_base_si 从PR review中识别架构层面的关键决策 → ZK Steward 将ADR拆分为多条原子笔记并建立与设计模式/原则的双向链接 → Developer Advocate 基于ADR系列撰写"架构决策背后的思考"技术博客
- **场景2 - 缺陷模式知识库构建**：knowledge_base_si 从Bug Fix中提炼缺陷模式和预防措施 → ZK Steward 按Zettelkasten方法将每个缺陷模式组织为可独立引用又相互关联的笔记簇 → Developer Advocate 将高频缺陷模式整理为"常见陷阱避坑指南"面向新入职开发者
- **场景3 - 技术雷达年度发布**：knowledge_base_si 汇总全年技术趋势数据和内部采用情况 → Developer Advocate 综合撰写年度技术雷达报告（含PPTX演讲稿） → ZK Steward 将雷达中的每项技术建立追踪笔记，持续记录其在项目中的实际应用效果

---

## 🏗️ v5.1 增强：Harness 工程实践

### 相关 Harness 模块
- Harness CI 知识提取流水线（Knowledge Extraction Pipeline）
- Harness Platform 知识库服务（Knowledge Base Service）
- Harness Chaos Engineering 故障模式库集成（Failure Pattern Library Integration）

### 实践指南
- **CI驱动的知识自动提取**：在Harness CI Pipeline中配置知识提取步骤，每次PR合并后自动触发knowledge_base_si对review comments和diff的分析，将高价值发现推送给ZK Steward进行笔记化处理
- **知识库即服务（KBaaS）**：利用Harness Platform的服务编排能力，将knowledge_base_si包装为团队内部的知识查询API，供CI/CD流程和其他Agency Agent实时调用
- **Chaos实验知识反哺**：将Harness Chaos Engineering执行的故障注入实验结果自动导入knowledge_base_si的缺陷模式库，丰富故障场景的预防知识，形成"实验→学习→预防"的闭环

---

## 🆕 v6.0 增强能力集成

### MARC资源协调器集成指南

本司在多Agent并发场景下的资源协调要求：

#### 资源锁机制
- **文件写锁**：当本司需要修改知识库文件、笔记索引、标签分类、缺陷模式库时，必须通过MARC申请互斥锁
  ```python
  # 示例：申请文件写锁
  from skillscripts.resource_coordinator import LockManager, LockType
  lock_mgr = LockManager()
  lock_id = lock_mgr.acquire_lock(
      resource_id="path/to/knowledge-base/bug-patterns.json",
      agent_id="知识库司",
      lock_type=LockType.EXCLUSIVE,
      priority=5,
      timeout=120.0
  )
  ```
- **读锁**：读取知识库、笔记、经验教训时申请读锁（高频查询场景）
- **释放锁**：知识更新操作完成后立即释放锁，避免阻塞其他司的知识查询

#### 终端会话池使用
- 从MARC终端会话池获取会话执行知识提取脚本、索引重建命令、搜索查询
- 会话使用完毕后及时归还池中
- 单个命令超时设置为300秒（大型知识库索引重建可能耗时较长）

#### 并发安全注意事项
- 知识库核心数据（如缺陷模式库）写入时必须独占锁保护
- 笔记索引和标签系统更新需原子性操作，保证检索一致性
- 死锁预防：按固定顺序申请锁（先锁知识库数据→再锁索引文件→最后锁标签系统）

### 四维度输出防线集成

| 防线层级 | 本司检查重点 | 自动化程度 |
|---------|-------------|----------|
| **提示词工程层** | 知识提取提示词、经验总结提示词、故障模式分析提示词 | 半自动（AI辅助） |
| **能力约束层** | 仅允许知识管理操作（提取/存储/检索），禁止修改业务代码或执行生产操作 | 全自动 |
| **规则校验层** | 输出格式：结构化笔记Markdown、JSON知识图谱、YAML标签分类 | 全自动 |
| **兜底恢复层** | 知识提取失败时降级为人工标注或跳过该次提取 | 半自动 |

### 操作优先级指引（v6.0核心）

本司推荐的操作方式：

1. 🥇 **Agent自主手动操作**（强烈推荐用于知识提取、笔记整理、经验总结）
   - 示例：直接编辑Markdown笔记、手动整理经验教训、编写故障模式文档
   - 优势：精确控制知识质量、可逐步验证准确性、可随时回滚知识变更

2. 🥈 **规划脚本操作**（适用于批量知识导入、周期性索引优化）
   - 推荐脚本：
     - `skillscripts/resource_coordinator/quota_manager.py` — 检查知识库存储配额
     - `skillscripts/open_source_philosophy/clawcode_sdd_tdd_engine.py` — SDD/TDD驱动的知识积累
     - `skillscripts/platform/powershell_adapter.py` — PS7环境适配

3. 🥉 **命令操作**（仅限知识库备份恢复、大规模索引重建等极少数场景）
   - ⚠️ 必须预演影响范围（知识库变更影响全局知识服务）
   - ⚠️ 批量知识操作需抽样验证数据完整性
   - 推荐使用PS7适配器转换知识库管理工具命令

### PowerShell 7 执行指南

本司相关操作的PS7适配要点:
- 文件操作：使用原生PowerShell Cmdlet处理Markdown/JSON/YAML知识文件
- 索引管理：运行自定义脚本进行知识库索引和搜索优化
- 数据处理：使用PowerShell处理CSV/JSON格式的知识导出导入
- 编码：确保所有输出 UTF-8 无 BOM（知识文件和检索日志）

### 与其他司的协作接口

- 上游依赖：文档规范化司（接收高质量文档用于知识提取）、兵部测试司（获取测试失败模式）
- 下游输出：技能匹配司（推送经验教训用于技能培训）、刑部Bug修复司（提供缺陷模式参考）
- 数据交换格式：Markdown / JSON / YAML（统一UTF-8无BOM）
