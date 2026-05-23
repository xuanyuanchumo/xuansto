# @hivehub/rulebook 集成模式参考文档

> 版本: 3.2.0 | 更新日期: 2026-05-06 | 编码: UTF-8 without BOM | 行尾: LF

---

## 概述

@hivehub/rulebook 是一套面向AI Agent的规则引擎与行为约束框架，通过结构化规则定义、强制工作流和持久化记忆机制，确保多Agent协作的可预测性和可追溯性。本文档描述其核心集成模式及与xuansto-skill的对接方式。

---

## 核心机制

### 1. 三次尝试重启规则（3-Attempt Restart Rule）

当Agent在同一错误上连续3次尝试失败时，强制停止当前执行路径并从头重启，而非继续在错误方向上尝试。

**规则定义：**

```yaml
restart_rule:
  max_attempts: 3
  on_exhaust:
    action: restart_from_beginning
    record_anti_pattern: true
    notify_supervisor: true
```

**执行流程：**

1. Agent执行任务步骤 → 失败 → 记录错误类型
2. 第二次尝试 → 仍失败 → 记录错误模式
3. 第三次尝试 → 仍失败 → 触发重启
4. 将失败模式写入anti-patterns知识库
5. 从任务起点重新开始，新迭代可参考anti-patterns避免重复错误

**与Karpathy准则的映射：**

| Karpathy准则 | 重启规则关联 |
|-------------|-------------|
| Think Before Coding | 3次失败后强制重新审视假设 |
| Simplicity First | 单步3次不过说明步骤过于复杂，需进一步拆分 |
| Surgical Changes | 重启防止"补丁叠补丁"的变更膨胀 |
| Goal-Driven Execution | 重启不是放弃目标，而是以更优路径重新迭代 |

### 2. 知识库强制工作流（Knowledge Base Forced Workflow）

强制Agent在执行关键决策前查询知识库，确保决策基于已有知识而非凭空推测。

**工作流定义：**

```yaml
forced_workflow:
  trigger: critical_decision
  steps:
    - query_knowledge_base
    - validate_against_patterns
    - record_decision_with_evidence
```

**决策类型分类：**

- 架构决策：技术选型、模块划分、接口设计
- 安全决策：权限配置、数据加密、输入验证
- 性能决策：缓存策略、并发模型、资源分配

### 3. Ralph自主循环（Ralph Autonomous Loop）

Ralph循环是一种自我驱动的任务执行模式，Agent在无人干预下持续迭代直到达成目标或触发停止条件。

**循环结构：**

```
┌─────────────────────────────────┐
│  Ralph Autonomous Loop          │
│                                 │
│  1. 评估当前状态                │
│  2. 确定下一步行动              │
│  3. 执行并验证结果              │
│  4. 更新知识库                  │
│  5. 检查停止条件                │
│     ├── 目标达成 → 退出         │
│     ├── 3次失败 → 重启          │
│     └── 继续循环                │
└─────────────────────────────────┘
```

**停止条件：**

- 目标验证通过（definition-done框架）
- 连续3次失败触发重启
- 人工干预信号
- Token预算耗尽

### 4. 持久化记忆（Persistent Memory: BM25+HNSW）

双层记忆架构结合关键词检索与语义检索，确保Agent跨会话知识持久化。

**架构设计：**

```yaml
memory_architecture:
  layer_1:
    type: BM25
    purpose: 关键词精确匹配
    use_cases:
      - 代码符号查找
      - 错误码检索
      - 配置项定位
    update_strategy: incremental

  layer_2:
    type: HNSW
    purpose: 语义相似度检索
    use_cases:
      - 概念关联查找
      - 上下文推理
      - 反模式匹配
    update_strategy: periodic_reindex

  integration:
    query_strategy: reciprocal_rank_fusion
    cache_ttl: 3600
    max_results: 10
```

**BM25与HNSW协同：**

| 维度 | BM25 | HNSW |
|------|------|------|
| 检索方式 | 关键词精确匹配 | 向量语义相似度 |
| 延迟 | <5ms | <20ms |
| 适用场景 | 确定性查询 | 模糊性推理 |
| 更新成本 | 低（增量） | 中（需重索引） |
| 精确度 | 高（精确匹配） | 中（近似最近邻） |

**融合检索策略（Reciprocal Rank Fusion）：**

```python
def reciprocal_rank_fusion(bm25_results, hnsw_results, k=60):
    scores = {}
    for rank, doc in enumerate(bm25_results):
        scores[doc.id] = scores.get(doc.id, 0) + 1 / (k + rank + 1)
    for rank, doc in enumerate(hnsw_results):
        scores[doc.id] = scores.get(doc.id, 0) + 1 / (k + rank + 1)
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)
```

---

## 集成配置

```yaml
hivehub_rulebook:
  version: "3.2.0"
  restart_rule:
    enabled: true
    max_attempts: 3
  forced_workflow:
    enabled: true
    critical_decisions: [architecture, security, performance]
  ralph_loop:
    enabled: true
    max_iterations: 50
    checkpoint_interval: 5
  persistent_memory:
    bm25:
      index_path: ".knowledge/bm25_index"
      tokenizer: "jieba"
    hnsw:
      index_path: ".knowledge/hnsw_index"
      embedding_model: "text-embedding-3-small"
      dimensions: 1536
      m: 16
      ef_construction: 200
```

---

## 与xuansto-skill的对接

| xuansto模块 | rulebook机制 | 对接方式 |
|------------|-------------|---------|
| Quality Gates | 3-Attempt Restart | 门禁失败3次触发重启 |
| Agent Registry | Forced Workflow | 关键Agent调度前查询知识库 |
| Ralph Loop | Ralph Autonomous Loop | 共享循环控制逻辑 |
| Knowledge Base | BM25+HNSW Memory | 统一记忆存储与检索 |

---

## 增量实现规范详细映射

### 3次失败重启规则 → 工作流Phase映射

| Phase | 失败场景 | 3次触发条件 | 重启动作 | 反模式记录 |
|-------|---------|------------|---------|-----------|
| Phase 1 需求分析 | 需求歧义无法澄清 | 连续3次产出被拒 | 回到需求收集起点 | `anti-patterns/requirements/vague-requirements.md` |
| Phase 2 架构设计 | 架构方案被否决 | 连续3次方案未通过GATE-003 | 回到架构规划起点 | `anti-patterns/architecture/rejected-patterns.md` |
| Phase 3 测试先行 | 测试用例设计失败 | 连续3次测试用例无法覆盖关键路径 | 回到测试策略制定 | `anti-patterns/testing/untestable-design.md` |
| Phase 4 代码实现 | 实现方案反复失败 | 连续3次代码未通过REVIEW-CONFIDENCE | 回到实现方案设计 | `anti-patterns/implementation/failed-approaches.md` |
| Phase 5 测试验证 | 测试持续失败 | 连续3次测试运行未通过GATE-011 | 回到测试修复起点 | `anti-patterns/testing/flaky-tests.md` |
| Phase 6 验收确认 | 验收标准不满足 | 连续3次验收检查未通过GATE-013 | 回到验收标准定义 | `anti-patterns/acceptance/unclear-criteria.md` |
| Phase 7 持续重构 | 重构引入回归 | 连续3次重构后测试失败 | 回到重构前检查点 | `anti-patterns/refactoring/regression-prone.md` |
| Phase 8 部署交付 | 部署失败 | 连续3次部署流水线失败 | 回到部署配置检查 | `anti-patterns/deployment/failed-configs.md` |

### 3次失败重启规则 → Agent角色映射

| Agent | 典型失败场景 | 3次触发后行为 | 反模式示例 |
|-------|------------|-------------|-----------|
| Orchestrator | 任务调度死锁/冲突仲裁失败 | 重置Agent分配状态，从Phase入口重启 | `调度冲突：Agent A和B同时争抢同一资源` |
| Backend Developer | API实现反复未通过契约验证 | 重新审视API设计，从接口定义重启 | `契约不匹配：请求体字段与Spec定义不一致` |
| Frontend Developer | 组件实现未通过UI审查 | 回到组件设计，重新确认设计Token | `样式偏移：实现与设计稿不一致` |
| Security Auditor | 安全审计发现被误报推翻 | 重新定义审计范围，从扫描配置重启 | `误报模式：将框架安全头误判为配置缺失` |
| Test Architect | 测试策略无法覆盖关键路径 | 回到风险评估，重新确定测试优先级 | `覆盖盲区：忽略异步操作的竞态条件测试` |
| Code Reviewer | 审查意见被反复推翻 | 重新对齐审查标准，从规范确认重启 | `标准不一致：不同审查者采用不同代码风格标准` |

### 知识库强制工作流 → 决策点映射

```yaml
forced_workflow_decision_points:
  phase_0_initialization:
    - decision: "项目技术栈选型"
      kb_query: "technology-stack-selection"
      validation: "匹配已有项目经验，避免重复踩坑"
    - decision: "设计系统选择"
      kb_query: "design-system-patterns"
      validation: "复用已有设计Token，保持视觉一致性"

  phase_1_requirements:
    - decision: "需求优先级排序"
      kb_query: "requirement-prioritization-patterns"
      validation: "参考历史项目需求变更频率数据"
    - decision: "非功能需求定义"
      kb_query: "nfr-benchmarks"
      validation: "对齐行业标准性能基线"

  phase_2_architecture:
    - decision: "架构模式选择"
      kb_query: "architecture-patterns"
      validation: "验证模式与项目规模匹配度"
    - decision: "数据库选型"
      kb_query: "database-selection-criteria"
      validation: "参考同类项目数据库选型经验"

  phase_3_test_first:
    - decision: "测试框架选型"
      kb_query: "test-framework-comparison"
      validation: "确认框架与项目技术栈兼容"
    - decision: "测试覆盖率目标"
      kb_query: "coverage-targets-by-domain"
      validation: "参考领域特定覆盖率标准"

  phase_4_implementation:
    - decision: "代码实现方案"
      kb_query: "implementation-patterns"
      validation: "匹配项目已有代码风格和模式"
    - decision: "第三方库引入"
      kb_query: "dependency-risk-assessment"
      validation: "检查库的安全性和维护状态"

  phase_5_testing:
    - decision: "缺陷修复策略"
      kb_query: "defect-fix-patterns"
      validation: "参考同类缺陷的历史修复方案"
    - decision: "性能优化方向"
      kb_query: "performance-optimization-patterns"
      validation: "基于历史性能数据确定优化优先级"

  phase_6_acceptance:
    - decision: "验收标准确认"
      kb_query: "acceptance-criteria-templates"
      validation: "对齐项目定义的DoD标准"

  phase_7_refactoring:
    - decision: "重构范围确定"
      kb_query: "refactoring-safety-patterns"
      validation: "确认重构不会破坏已有功能契约"

  phase_8_deployment:
    - decision: "部署策略选择"
      kb_query: "deployment-strategy-patterns"
      validation: "参考同类项目部署经验和回滚策略"
```

### 知识库强制工作流 → 执行检查清单

每个Agent在执行关键决策时必须完成以下3步：

1. **检索（Query）**：向knowledge_server发送查询请求，获取相关历史经验和模式
   ```python
   result = knowledge_server.search(
       query="architecture-patterns microservice",
       min_relevance=0.7,
       top_k=5
   )
   ```

2. **验证（Validate）**：将决策与知识库中的模式进行比对，确认一致性或记录偏差
   ```python
   validation = validate_against_patterns(
       decision=current_decision,
       patterns=result.entries,
       threshold=0.8
   )
   ```

3. **记录（Record）**：将决策及其依据写入知识库，供后续Agent参考
   ```python
   knowledge_server.store(
       entry=KnowledgeEntry(
           type="decision",
           title=f"架构决策: {decision_title}",
           content=decision_detail,
           evidence=validation.evidence,
           source_agent=agent_name
       )
   )
   ```

---

> 本文档由 Multi-Agent SDD/TDD Orchestrator 维护 | 最后更新: 2026-05-06
