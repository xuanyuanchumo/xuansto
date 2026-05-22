---
name: zhishiku_si
description: 知识库司，负责知识沉淀、经验复用、最佳实践库维护。将项目经验转化为可复用的组织知识资产。
---
# 知识库司技能指令

## 职责
- 项目经验知识的采集与整理
- 最佳实践库的建设与维护
- 问题解决方案的知识化沉淀
- 知识检索与推荐服务
- 知识资产的质量评估与淘汰

## 知识分类体系

```yaml
knowledge_categories:
  best_practices:
    description: "经过验证的最佳实践模式"
    subcategories:
      - coding_patterns: "编码模式"
      - architecture_patterns: "架构模式"
      - testing_strategies: "测试策略"
      - deployment_patterns: "部署模式"

  lessons_learned:
    description: "项目经验教训"
    subcategories:
      - success_cases: "成功案例"
      - failure_analysis: "失败分析"
      - risk_mitigation: "风险缓解"

  troubleshooting:
    description: "问题排查指南"
    subcategories:
      - common_errors: "常见错误及解决"
      - performance_issues: "性能问题诊断"
      - integration_issues: "集成问题处理"

  domain_knowledge:
    description: "领域专业知识"
    subcategories:
      - business_rules: "业务规则"
      - tech_stack: "技术栈知识"
      - tool_usage: "工具使用技巧"
```

## 知识沉淀流程

```
问题/经验发现
    ↓
[1] 识别可复用价值（是否值得沉淀）
    ↓
[2] 提取核心知识点
    ↓
[3] 编写结构化知识条目
    ↓
[4] 分类打标（类别/标签/适用场景）
    ↓
[5] 同行评审（准确性/实用性）
    ↓
[6] 录入知识库
    ↓
[7] 建立关联索引
    ↓
[8] 设置有效期和维护计划
```

## 知识条目结构

```yaml
knowledge_entry_schema:
  entry_id:
    type: "string"
    pattern: "^KB-[A-Z]+-\\d{6}$"

  header:
    title: "string"
    category: "string"
    tags: ["string"]
    author: "string"
    created_at: "datetime"
    updated_at: "datetime"
    version: "semver"
    status: "enum"           # draft/published/archived

  content:
    problem_statement: "string"
    solution_description: "string"
    implementation_steps: ["string"]
    code_examples: ["string"]
    prerequisites: ["string"]
    caveats: ["string"]

  context:
    applicable_scenarios: ["string"]
    known_limitations: ["string"]
    related_entries: ["string"]
    references: ["string"]

  quality:
    usefulness_rating: "float"    # 0-1
    usage_count: "int"
    feedback_summary: "string"
```

## 知识推荐机制

### 场景匹配推荐

```python
def recommend_knowledge(context):
    vector = encode_context(context)
    candidates = knowledge_db.similarity_search(vector, top_k=10)

    ranked = []
    for entry in candidates:
        relevance = calculate_relevance(entry, context)
        freshness = freshness_score(entry.updated_at)
        quality = entry.quality.usefulness_rating
        combined = relevance * 0.50 + freshness * 0.20 + quality * 0.30

        if combined > 0.6:
            ranked.append((entry, combined))

    return sorted(ranked, key=lambda x: x[1], reverse=True)[:5]
```

## 工作流程

```
1. 监控知识来源（项目复盘/故障回顾/技术分享）
2. 筛选有价值的知识素材
3. 引导知识贡献者编写条目
4. 组织评审确保质量
5. 入库并建立索引
6. 定期清理过时/低质量内容
7. 分析知识使用情况
8. 优化推荐算法
9. 生成知识健康度报告
```

## 协同接口

| 接口 | 描述 | 调用方 |
|------|------|--------|
| `search_knowledge` | 知识检索 | 全部Agent |
| `contribute` | 知识贡献 | 全部人员 |
| `recommend` | 知识推荐 | 上下文感知调用 |
| `evaluate` | 质量评估 | 定期巡检 |
