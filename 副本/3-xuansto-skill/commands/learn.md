---
name: /learn
aliases:
  - ln
category: knowledge
phase: "cross-phase"
description: 知识学习与经验沉淀
trigger: 需要学习新知识或沉淀项目经验时
execution_mode: inline
---

# /learn 命令

## 命令描述

`/learn` 命令用于模式学习与知识沉淀，是系统自演化的核心命令。该命令从历史执行记录中提取成功模式和最佳实践，构建知识图谱，优化决策模型，实现系统的持续学习和自我进化。

---

## 触发条件

| 触发方式 | 说明 |
|----------|------|
| 命令输入 | 用户输入 `/learn` |
| 关键词触发 | 用户提及"知识学习"、"模式学习"、"经验沉淀" |
| 自动触发 | 冲刺完成后自动触发模式学习 |
| 条件触发 | 知识库置信度低于阈值或发现新模式时自动触发 |

---

## 命令名称与语法

```
/learn [topic|pattern-id] [options]
```

---

## 参数定义

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| topic | string | 否 | all | 学习主题或模式ID |
| --source | string | 否 | auto | 学习来源：auto、history、feedback、external |
| --scope | string | 否 | project | 学习范围：project、team、global |
| --depth | string | 否 | standard | 学习深度：quick、standard、deep |
| --apply | boolean | 否 | false | 自动应用学习结果 |
| --export | string | 否 | - | 导出学习结果到文件 |
| --validate | boolean | 否 | true | 验证学习结果有效性 |
| --min-samples | number | 否 | 5 | 最小样本数量 |
| --confidence | number | 否 | 0.8 | 置信度阈值 |

---

## 执行流程

> 标准四步框架：1. 输入验证 → 2. Agent调度 → 3. 任务执行 → 4. 结果验证

```
┌─────────────────────────────────────────────────────────────┐
│                    /learn 执行流程                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. 学习目标分析                                             │
│     ├── 解析学习主题和范围                                    │
│     ├── 确定学习目标                                         │
│     ├── 评估学习价值                                         │
│     ├── 制定学习计划                                         │
│     └── 记录学习意图到 Decision Log                          │
│                                                             │
│  2. 数据收集阶段                                             │
│     ├── 收集历史执行记录                                      │
│     ├── 提取决策日志                                         │
│     ├── 获取用户反馈                                         │
│     ├── 收集性能指标                                         │
│     └── 整理错误和修复记录                                    │
│                                                             │
│  3. 模式识别阶段                                             │
│     ├── 执行数据预处理                                       │
│     ├── 特征提取和向量化                                      │
│     ├── 聚类分析                                             │
│     ├── 序列模式挖掘                                         │
│     └── 异常模式检测                                         │
│                                                             │
│  4. 知识提取阶段                                             │
│     ├── 识别成功模式                                         │
│     ├── 提取最佳实践                                         │
│     ├── 总结失败教训                                         │
│     ├── 归纳决策规则                                         │
│     └── 构建知识条目                                         │
│                                                             │
│  5. 验证阶段                                                 │
│     ├── 交叉验证学习结果                                      │
│     ├── 统计显著性检验                                       │
│     ├── 专家评审（如需要）                                    │
│     ├── A/B测试验证                                         │
│     └── 计算置信度分数                                       │
│                                                             │
│  6. 知识存储阶段                                             │
│     ├── 更新知识库                                           │
│     ├── 构建知识图谱                                         │
│     ├── 建立知识索引                                         │
│     ├── 设置知识关联                                         │
│     └── 记录版本历史                                         │
│                                                             │
│  7. 应用阶段（可选）                                          │
│     ├── 更新决策模型                                         │
│     ├── 优化Agent行为                                        │
│     ├── 调整工作流程                                         │
│     ├── 更新配置参数                                         │
│     └── 通知相关Agent                                        │
│                                                             │
│  8. 报告阶段                                                 │
│     ├── 生成学习报告                                         │
│     ├── 展示关键发现                                         │
│     ├── 提供应用建议                                         │
│     └── 记录学习成果                                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 涉及Agent

| Agent | 角色 | 职责 |
|-------|------|------|
| Orchestrator | 主导 | 学习流程协调 |
| documentation-engineer | 辅助 | 知识文档化与整理 |
| system-architect | 辅助 | 架构模式学习 |
| code-reviewer | 辅助 | 代码模式学习 |
| refactoring-specialist | 辅助 | 重构模式学习 |
| test-architect | 辅助 | 测试模式学习 |
| technical-writer | 辅助 | 知识文档化 |

---

## 输出格式

### 1. 学习报告 (learning-report.md)

```markdown
# 模式学习报告

## 学习概要
- 学习时间: 2026-04-17 17:00:00
- 学习主题: API错误处理模式
- 数据范围: 2026-01-01 至 2026-04-17
- 样本数量: 156 个案例

## 发现的模式

### 模式1: 统一错误响应格式
- 置信度: 95%
- 样本支持: 142/156 (91%)
- 描述: 成功项目中API错误响应采用统一格式
- 模式定义:
  ```json
  {
    "error": {
      "code": "ERROR_CODE",
      "message": "Human readable message",
      "details": {},
      "trace_id": "uuid"
    }
  }
  ```
- 效果: 减少50%的错误处理时间

### 模式2: 错误分类策略
- 置信度: 88%
- 样本支持: 128/156 (82%)
- 描述: 按错误类型分类处理策略
- 分类:
  - 客户端错误 (4xx): 返回详细错误信息
  - 服务端错误 (5xx): 记录日志，返回通用信息
  - 业务错误: 返回业务错误码和描述

### 模式3: 错误重试机制
- 置信度: 82%
- 样本支持: 98/156 (63%)
- 描述: 对可重试错误实现指数退避重试
- 参数:
  - 最大重试次数: 3
  - 初始延迟: 1秒
  - 退避因子: 2

## 知识沉淀

### 新增知识条目
| ID | 类型 | 标题 | 置信度 |
|----|------|------|--------|
| KB-001 | pattern | 统一错误响应格式 | 95% |
| KB-002 | pattern | 错误分类策略 | 88% |
| KB-003 | best-practice | 指数退避重试 | 82% |

### 更新知识条目
| ID | 变更类型 | 说明 |
|----|----------|------|
| KB-ERR-001 | 增强 | 添加trace_id字段 |

## 应用建议
1. 在新项目中采用统一错误响应格式
2. 更新现有项目的错误处理模块
3. 在API设计规范中添加错误处理章节

## 后续行动
- [ ] 创建错误处理模板
- [ ] 更新API设计规范
- [ ] 培训团队成员
```

### 2. 知识条目 (knowledge-entry.json)

```json
{
  "entry_id": "KB-001",
  "type": "pattern",
  "title": "统一错误响应格式",
  "category": "api-design",
  "confidence": 0.95,
  "sample_count": 142,
  "created_at": "2026-04-17T17:00:00Z",
  "updated_at": "2026-04-17T17:00:00Z",
  "content": {
    "problem": "API错误响应格式不统一，增加客户端处理复杂度",
    "solution": "采用统一的错误响应格式，包含code、message、details、trace_id字段",
    "example": {
      "error": {
        "code": "VALIDATION_ERROR",
        "message": "输入参数验证失败",
        "details": {
          "field": "email",
          "reason": "格式不正确"
        },
        "trace_id": "abc-123-def"
      }
    },
    "benefits": [
      "减少客户端错误处理复杂度",
      "便于问题追踪和调试",
      "提高API一致性"
    ],
    "applicability": [
      "RESTful API设计",
      "微服务接口",
      "GraphQL错误处理"
    ]
  },
  "related_entries": ["KB-002", "KB-ERR-001"],
  "tags": ["api", "error-handling", "best-practice"],
  "source": {
    "type": "pattern-mining",
    "reference": "LRN-20260417-001"
  }
}
```

### 3. 知识图谱更新 (knowledge-graph.json)

```json
{
  "nodes": [
    {
      "id": "KB-001",
      "label": "统一错误响应格式",
      "type": "pattern",
      "weight": 0.95
    },
    {
      "id": "KB-002",
      "label": "错误分类策略",
      "type": "pattern",
      "weight": 0.88
    },
    {
      "id": "KB-003",
      "label": "指数退避重试",
      "type": "best-practice",
      "weight": 0.82
    }
  ],
  "edges": [
    {
      "source": "KB-001",
      "target": "KB-002",
      "relation": "complements",
      "weight": 0.85
    },
    {
      "source": "KB-002",
      "target": "KB-003",
      "relation": "enables",
      "weight": 0.75
    }
  ],
  "clusters": [
    {
      "id": "error-handling",
      "label": "错误处理模式集",
      "members": ["KB-001", "KB-002", "KB-003"]
    }
  ]
}
```

### 4. 决策模型更新 (decision-model.json)

```json
{
  "model_id": "DM-API-ERROR-001",
  "version": "2.0.0",
  "updated_at": "2026-04-17T17:00:00Z",
  "rules": [
    {
      "rule_id": "RULE-001",
      "condition": "api_error.type == 'validation'",
      "action": "return detailed_validation_error",
      "confidence": 0.95,
      "source": "KB-001"
    },
    {
      "rule_id": "RULE-002",
      "condition": "api_error.type == 'server' AND error.retryable == true",
      "action": "execute_exponential_backoff_retry",
      "confidence": 0.82,
      "source": "KB-003"
    }
  ],
  "performance_metrics": {
    "accuracy": 0.92,
    "precision": 0.89,
    "recall": 0.94
  }
}
```

---

## 示例用法

### 示例1: 自动学习

```bash
/learn
```

自动分析最近执行记录，提取新模式。

### 示例2: 主题学习

```bash
/learn api-design --depth=deep
```

深度学习API设计相关的模式。

### 示例3: 从历史学习

```bash
/learn --source=history --min-samples=10
```

从历史记录学习，要求至少10个样本。

### 示例4: 学习并应用

```bash
/learn refactoring --apply --validate
```

学习重构模式并自动应用，同时验证有效性。

### 示例5: 导出学习结果

```bash
/learn --export=learnings.json --format=json
```

学习并导出结果到JSON文件。

### 示例6: 全局范围学习

```bash
/learn --scope=global --confidence=0.9
```

从全局范围学习，置信度阈值设为0.9。

---

## 学习类型说明

### Pattern Mining（模式挖掘）

```
目标: 从历史数据中发现重复出现的模式
方法:
  - 序列模式挖掘
  - 频繁项集挖掘
  - 时序模式识别
输出: 模式定义、支持度、置信度
```

### Best Practice Extraction（最佳实践提取）

```
目标: 识别并提取成功的实践方法
方法:
  - 成功案例分析
  - 对比分析
  - 效果评估
输出: 最佳实践文档、应用指南
```

### Failure Learning（失败学习）

```
目标: 从失败案例中学习避免策略
方法:
  - 根因分析
  - 错误模式识别
  - 预防规则提取
输出: 避免指南、预警规则
```

### Performance Optimization（性能优化学习）

```
目标: 学习性能优化策略
方法:
  - 性能指标分析
  - 瓶颈识别
  - 优化效果评估
输出: 优化策略、配置建议
```

---

## 知识类型

| 类型 | 说明 | 示例 |
|------|------|------|
| pattern | 设计模式 | 仓储模式、策略模式 |
| best-practice | 最佳实践 | 代码审查清单 |
| anti-pattern | 反模式 | 上帝类、循环依赖 |
| principle | 设计原则 | SOLID原则 |
| guideline | 指导方针 | API设计指南 |
| template | 模板 | 项目结构模板 |

---

## 质量门禁

| 门禁标识 | 阻塞级别(BLOCK/WARN) | 通过标准 |
|----------|----------------------|----------|
| DOC-COMPLETENESS | WARN | 知识条目完整、描述清晰、示例可执行、关联关系正确 |
| PLAN-PERSISTENCE | WARN | 学习结果已持久化到知识库、决策模型已更新、知识图谱已同步 |
---

## 注意事项

1. **样本质量**: 确保学习数据的质量和代表性
2. **置信度**: 低置信度的学习结果应谨慎应用
3. **验证重要**: 学习结果应经过验证后再应用
4. **知识冲突**: 处理新旧知识的冲突和融合
5. **持续更新**: 知识库需要持续维护和更新

---

## 相关脚本

- `scripts/kb-migrate.py` - 知识库迁移器，管理知识库版本迁移和格式转换
- `scripts/pattern-learner.py` - 模式学习器，从历史执行记录中提取成功模式和最佳实践

---

## 相关工作流

- `workflows/sdd-tdd-full.md` (Phase 7) - SDD+TDD全生命周期工作流的知识沉淀与学习阶段

---

## 相关命令

- `/review` - 审查结果作为学习输入
- `/agent-status` - 查看学习Agent状态
- `/deploy` - 部署时应用学习结果
