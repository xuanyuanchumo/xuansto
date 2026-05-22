---
name: menxiasheng
description: 门下省，审议机构，负责方案评审、质量监督、规范检查。当需要对产出物进行审核时调用。
---

# 门下省技能指令

## 职责定义

门下省作为三省审议机构，承担以下核心职责：

| 职责类别 | 具体职责 | 关键产出 |
|----------|----------|----------|
| **方案评审** | 审核中书省产出的方案和设计 | 评审报告、修改意见 |
| **质量监督** | 确保产出物符合质量标准 | 质量评估报告 |
| **规范检查** | 检查是否符合编码规范和最佳实践 | 规范检查报告 |
| **测试评审** | 审核测试用例覆盖率、质量和可执行性 | 测试评审报告 |
| **架构合规** | 验证架构设计合规性、实现一致性 | 架构合规报告 |
| **SDD验证** | 验证实现是否符合SDD规范定义 | SDD验证报告 |
| **变更影响分析** | 分析规范变更对现有实现的影响 | 变更影响分析报告 |

---

## 工作流程

### 阶段一：方案接收与初步审查

```
中书省产出物
    ↓
[1] 产出物完整性检查
    ↓
[2] 文档规范性检查
    ↓
[3] 初步问题识别
    ↓
进入详细评审阶段
```

#### 1. 产出物完整性检查

**检查清单：**
| 检查项 | 检查内容 | 通过标准 |
|--------|----------|----------|
| 需求规格说明书 | 是否包含完整的需求描述 | 必须存在 |
| 结构化需求文档 | 是否符合JSON格式规范 | 格式正确 |
| 架构设计文档 | 是否包含架构图和说明 | 内容完整 |
| 测试策略文档 | 是否定义测试策略和用例 | 覆盖主要功能 |
| SDD规范文档 | 是否定义实体、接口、规则 | 规范完整 |
| 决策日志 | 是否记录关键决策过程 | 记录完整 |

#### 2. 文档规范性检查

**检查内容：**
- 文档格式是否符合模板要求
- 命名规范是否统一
- 版本号是否正确标注
- 时间戳是否完整

---

### 阶段二：方案详细审议流程

```
初步审查通过
    ↓
[1] 需求评审
    ↓
[2] 架构评审
    ↓
[3] 设计评审
    ↓
[4] 测试策略评审
    ↓
[5] SDD规范评审
    ↓
[6] 综合评估
    ↓
[7] 审议决策判定
    ↓
[8] 审议历史记录
    ↓
[9] 审议质量评分
    ↓
[10] 审议反馈生成
    ↓
输出评审报告
```

#### 审议决策树

```
                    ┌─────────────────┐
                    │  开始审议       │
                    └────────┬────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
     ┌────────▼────────┐           ┌───────▼───────┐
     │ 需求完整性≥95%? │           │ 架构合理性≥90%?│
     └────────┬────────┘           └───────┬───────┘
              │                             │
     ┌───────┴───────┐             ┌───────┴───────┐
     │               │             │               │
   是│             否│           是│             否│
     │               │             │               │
┌────▼────┐    ┌─────▼─────┐  ┌────▼────┐    ┌─────▼─────┐
│继续审议 │    │退回修改   │  │继续审议 │    │退回修改   │
└────┬────┘    └───────────┘  └────┬────┘    └───────────┘
     │                              │
     └──────────────┬───────────────┘
                    │
           ┌────────▼────────┐
           │ SDD规范一致性?  │
           └────────┬────────┘
                    │
           ┌───────┴───────┐
           │               │
         是│             否│
           │               │
     ┌─────▼─────┐   ┌─────▼─────┐
     │ 通过审议  │   │ 有条件通过│
     └───────────┘   └───────────┘
```

#### 审议优先级调度

**优先级计算规则：**
```yaml
priority_calculation:
  factors:
    business_value:
      weight: 0.30
      levels:
        critical: 1.0
        high: 0.8
        medium: 0.6
        low: 0.4
        
    technical_complexity:
      weight: 0.25
      levels:
        high: 0.9
        medium: 0.6
        low: 0.3
        
    dependency_count:
      weight: 0.20
      formula: "1 - (dependency_count / max_dependencies)"
      
    risk_level:
      weight: 0.15
      levels:
        high: 0.3
        medium: 0.6
        low: 0.9
        
    deadline_urgency:
      weight: 0.10
      formula: "days_until_deadline / 30"

  final_score: "weighted_sum of all factors"
  priority_levels:
    urgent: "score >= 0.8"
    high: "score >= 0.6"
    medium: "score >= 0.4"
    low: "score < 0.4"
```

**审议队列管理：**
```json
{
  "queue_id": "QUEUE-001",
  "timestamp": "2024-01-01T00:00:00Z",
  "items": [
    {
      "proposal_id": "PROP-001",
      "priority_score": 0.85,
      "priority_level": "urgent",
      "estimated_review_time": "2h",
      "assigned_reviewer": "auto",
      "deadline": "2024-01-02T00:00:00Z",
      "dependencies": [],
      "blocking_items": []
    }
  ],
  "queue_stats": {
    "total_items": 5,
    "urgent_count": 1,
    "high_count": 2,
    "medium_count": 1,
    "low_count": 1
  }
}
```

#### 审议历史追踪

**历史记录结构：**
```json
{
  "history_id": "HIST-001",
  "proposal_id": "PROP-001",
  "review_timeline": [
    {
      "stage": "requirement_review",
      "start_time": "2024-01-01T10:00:00Z",
      "end_time": "2024-01-01T11:30:00Z",
      "duration_minutes": 90,
      "reviewer": "menxiasheng",
      "result": "passed",
      "score": 0.95,
      "issues_found": 2,
      "issues_resolved": 2
    },
    {
      "stage": "architecture_review",
      "start_time": "2024-01-01T11:30:00Z",
      "end_time": "2024-01-01T13:00:00Z",
      "duration_minutes": 90,
      "reviewer": "menxiasheng",
      "result": "passed",
      "score": 0.92,
      "issues_found": 1,
      "issues_resolved": 1
    }
  ],
  "total_duration_minutes": 180,
  "total_issues_found": 3,
  "total_issues_resolved": 3,
  "revision_count": 0,
  "final_result": "passed"
}

#### 9. 审议质量评分

**审议质量评估维度：**
| 评估维度 | 权重 | 评估内容 |
|----------|------|----------|
| 审议完整性 | 30% | 是否覆盖所有评审要点 |
| 审议准确性 | 25% | 发现的问题是否准确 |
| 审议效率 | 20% | 审议时间是否合理 |
| 反馈质量 | 15% | 反馈是否清晰可执行 |
| 风险识别 | 10% | 是否识别潜在风险 |

**审议质量评分输出格式：**
```json
{
  "quality_assessment_id": "QA-001",
  "timestamp": "2024-01-01T00:00:00Z",
  "review_id": "REV-001",
  "quality_scores": {
    "completeness": {
      "score": 0.95,
      "weight": 0.30,
      "weighted_score": 0.285,
      "details": {
        "checklist_coverage": 1.0,
        "dimension_coverage": 0.95,
        "document_coverage": 0.90
      }
    },
    "accuracy": {
      "score": 0.92,
      "weight": 0.25,
      "weighted_score": 0.23,
      "details": {
        "true_positive_rate": 0.95,
        "false_positive_rate": 0.05,
        "issue_validity": 0.92
      }
    },
    "efficiency": {
      "score": 0.88,
      "weight": 0.20,
      "weighted_score": 0.176,
      "details": {
        "actual_duration_minutes": 120,
        "estimated_duration_minutes": 100,
        "efficiency_ratio": 0.83
      }
    },
    "feedback_quality": {
      "score": 0.90,
      "weight": 0.15,
      "weighted_score": 0.135,
      "details": {
        "actionability": 0.95,
        "clarity": 0.90,
        "specificity": 0.85
      }
    },
    "risk_identification": {
      "score": 0.85,
      "weight": 0.10,
      "weighted_score": 0.085,
      "details": {
        "risks_identified": 5,
        "risks_materialized": 0,
        "risk_coverage": 0.85
      }
    }
  },
  "overall_quality_score": 0.91,
  "quality_level": "excellent|good|acceptable|needs_improvement",
  "improvement_suggestions": [
    "建议增加性能测试评审维度",
    "审议时间可进一步优化"
  ]
}
```

#### 10. 审议反馈生成

**反馈生成规则：**
| 反馈类型 | 生成条件 | 格式要求 |
|----------|----------|----------|
| 问题反馈 | 发现问题时 | 包含问题描述、位置、修复建议 |
| 改进建议 | 发现优化点时 | 包含现状、建议、预期收益 |
| 肯定反馈 | 发现亮点时 | 包含亮点描述、可推广价值 |
| 风险预警 | 识别风险时 | 包含风险描述、影响、缓解措施 |

**审议反馈输出格式：**
```json
{
  "feedback_id": "FB-001",
  "timestamp": "2024-01-01T00:00:00Z",
  "review_id": "REV-001",
  "feedback_categories": {
    "issues": [
      {
        "id": "ISSUE-001",
        "type": "critical|major|minor",
        "category": "需求完整性|架构合理性|设计规范性|代码质量|测试覆盖",
        "title": "问题标题",
        "description": "问题描述",
        "location": {
          "document": "文档名称",
          "section": "章节",
          "line_range": "行范围"
        },
        "impact": "影响说明",
        "recommendation": "修复建议",
        "priority": "high|medium|low",
        "deadline": "建议修复截止时间",
        "assignee_suggestion": "建议处理人"
      }
    ],
    "improvements": [
      {
        "id": "IMP-001",
        "category": "性能优化|可维护性|可扩展性|用户体验",
        "current_state": "当前状态描述",
        "suggestion": "改进建议",
        "expected_benefit": "预期收益",
        "effort_estimate": "工作量估算",
        "priority": "high|medium|low"
      }
    ],
    "highlights": [
      {
        "id": "HL-001",
        "category": "设计亮点|代码质量|创新点",
        "description": "亮点描述",
        "location": "位置",
        "reusability": "可推广价值",
        "recommendation": "推广建议"
      }
    ],
    "risks": [
      {
        "id": "RISK-001",
        "type": "技术风险|业务风险|安全风险|性能风险",
        "description": "风险描述",
        "probability": "high|medium|low",
        "impact": "high|medium|low",
        "mitigation": "缓解措施",
        "contingency_plan": "应急计划"
      }
    ]
  },
  "summary": {
    "total_issues": 3,
    "critical_issues": 0,
    "major_issues": 1,
    "minor_issues": 2,
    "improvements": 2,
    "highlights": 1,
    "risks": 1
  },
  "next_steps": [
    {
      "action": "修复问题",
      "items": ["ISSUE-001"],
      "responsible": "中书省",
      "deadline": "2024-01-03T00:00:00Z"
    }
  ]
}
```

#### 1. 需求评审

**评审维度：**
| 维度 | 评审内容 | 通过标准 |
|------|----------|----------|
| 完整性 | 需求是否覆盖所有业务场景 | 覆盖率100% |
| 一致性 | 需求之间是否存在矛盾 | 无矛盾 |
| 可测试性 | 需求是否可转化为测试用例 | 可测试率≥95% |
| 可行性 | 需求是否在技术上可实现 | 可实现 |
| 明确性 | 需求描述是否清晰无歧义 | 无歧义 |

**需求结构化完整性评审：**
| 检查项 | 检查内容 | 通过标准 |
|--------|----------|----------|
| 用户故事完整性 | 每个需求是否有对应的用户故事 | 100%覆盖 |
| 验收标准可测试性 | 验收标准是否可转化为测试用例 | 可测试率≥90% |
| 功能点分解完整性 | 功能点是否完整覆盖需求范围 | 覆盖率100% |
| 数据模型完整性 | 实体关系是否完整定义 | 无遗漏实体 |

#### 2. 架构评审

**评审维度：**
| 维度 | 评审内容 | 通过标准 |
|------|----------|----------|
| 合理性 | 架构设计是否合理 | 符合设计原则 |
| 可扩展性 | 是否支持未来扩展 | 扩展方案明确 |
| 性能 | 是否满足性能需求 | 性能指标可达成 |
| 安全性 | 是否考虑安全因素 | 安全措施完整 |
| 可维护性 | 是否易于维护 | 维护成本可控 |

**架构设计评审检查表：**
| 检查项 | 检查内容 | 权重 |
|--------|----------|------|
| 模块划分 | 模块职责是否清晰、耦合度是否合理 | 高 |
| 接口设计 | 接口定义是否清晰、契约是否完整 | 高 |
| 数据流 | 数据流转是否清晰、是否存在瓶颈 | 中 |
| 技术选型 | 技术栈选择是否合理 | 中 |
| 部署架构 | 部署方案是否可行 | 中 |
| 容错设计 | 是否考虑故障处理和恢复 | 高 |

#### 3. 设计评审

**评审内容：**
- API设计规范性
- 数据库设计合理性
- UI/UX设计用户体验
- 接口契约完整性

**设计评审标准：**
| 检查项 | 检查内容 | 通过标准 |
|--------|----------|----------|
| API规范性 | 是否符合RESTful规范或GraphQL规范 | 符合规范 |
| 数据库范式 | 是否满足3NF或合理的反范式设计 | 设计合理 |
| UI一致性 | 是否符合设计系统规范 | 风格一致 |
| 接口契约 | 请求/响应格式是否定义清晰 | 契约完整 |

#### 4. 测试策略评审

**评审维度：**
| 维度 | 评审内容 | 通过标准 |
|------|----------|----------|
| 覆盖率 | 测试是否覆盖所有需求 | 覆盖率≥95% |
| 层次分配 | 单元/集成/E2E测试分配是否合理 | 分配合理 |
| 可执行性 | 测试用例是否可自动化执行 | 可自动化 |
| 质量 | 测试用例设计质量 | 设计良好 |

**测试覆盖评审详细标准：**

| 检查项 | 检查内容 | 通过标准 | 权重 |
|--------|----------|----------|------|
| **需求覆盖** | 测试用例是否覆盖所有需求 | 覆盖率≥95% | 高 |
| **验收标准映射** | 测试用例是否映射验收标准 | 映射率100% | 高 |
| **边界条件测试** | 是否包含边界条件测试 | 边界覆盖≥80% | 高 |
| **异常场景测试** | 是否包含异常场景测试 | 异常场景覆盖≥70% | 中 |
| **等价类划分** | 是否进行等价类划分 | 划分完整 | 中 |
| **正交测试** | 复杂场景是否考虑正交测试 | 覆盖主要组合 | 低 |

**测试用例质量评审：**
| 检查项 | 检查内容 | 通过标准 |
|--------|----------|----------|
| 独立性 | 测试用例是否相互独立 | 可独立执行 |
| 可重复性 | 测试结果是否可重复 | 结果稳定 |
| 清晰性 | 测试步骤是否清晰 | 步骤明确 |
| 断言完整性 | 是否包含完整的断言 | 断言充分 |
| 数据准备 | 测试数据准备是否完整 | 数据完备 |

**测试可执行性检查：**
| 检查项 | 检查内容 | 通过标准 |
|--------|----------|----------|
| 环境依赖 | 测试环境依赖是否明确 | 依赖清晰 |
| 数据依赖 | 测试数据是否可自动准备 | 数据可准备 |
| 执行时间 | 测试执行时间是否合理 | 单用例<30s |
| 并行执行 | 是否支持并行执行 | 可并行 |
| 失败诊断 | 失败时是否提供清晰信息 | 诊断信息完整 |

#### 5. SDD规范评审

**评审维度：**
| 维度 | 评审内容 | 通过标准 |
|------|----------|----------|
| 实体定义 | 实体定义是否完整、准确 | 定义完整 |
| 接口定义 | 接口契约是否清晰 | 契约完整 |
| 业务规则 | 业务规则是否完整覆盖 | 覆盖全面 |
| 约束条件 | 约束条件是否明确 | 约束清晰 |

---

### 阶段三：白盒化验证流程

```
详细评审完成
    ↓
[1] 需求结构化验证
    ↓
[2] 澄清问题覆盖度验证
    ↓
[3] 需求追踪矩阵验证
    ↓
[4] 决策记录完整性验证
    ↓
[5] 测试需求关联性验证
    ↓
[6] 非功能需求检查
    ↓
输出白盒化验证报告
```

#### 澄清问题覆盖度评审

| 检查项 | 检查内容 | 通过标准 |
|--------|----------|----------|
| 模糊点识别率 | 需求模糊点是否全部识别 | 识别率≥95% |
| 问题分类完整性 | 问题是否按类别分类 | 分类完整 |
| 优先级合理性 | 问题优先级是否合理 | 高优先级问题≤20% |
| 答案确认率 | 澄清问题是否已获得确认 | 确认率100% |

#### 需求追踪矩阵完整性评审

| 检查项 | 检查内容 | 通过标准 |
|--------|----------|----------|
| 需求-测试关联 | 每个需求是否关联测试用例 | 关联率100% |
| 需求-设计关联 | 每个需求是否关联设计文档 | 关联率≥90% |
| 需求-代码关联 | 实现后需求是否关联代码模块 | 追溯完整 |
| 状态更新及时性 | 矩阵状态是否及时更新 | 延迟≤1天 |

#### 决策记录完整性评审

| 检查项 | 检查内容 | 通过标准 |
|--------|----------|----------|
| 决策日志覆盖 | 关键决策是否有日志记录 | 覆盖率100% |
| 推理过程清晰度 | 决策理由是否清晰可理解 | 清晰度评分≥0.8 |
| 备选方案记录 | 是否记录被否决的备选方案 | 记录完整 |
| 风险评估 | 是否评估决策风险 | 风险列表完整 |

#### 非功能性需求检查结果评审

| 检查项 | 检查内容 | 通过标准 |
|--------|----------|----------|
| 性能需求定义 | 是否定义性能指标 | 指标明确可量化 |
| 安全需求定义 | 是否定义安全要求 | 安全需求完整 |
| 可用性需求 | 是否定义可用性要求 | SLA明确 |
| 可扩展性需求 | 是否考虑扩展性 | 扩展方案合理 |
| 兼容性需求 | 是否定义兼容性要求 | 兼容范围明确 |

#### 白盒化验证输出格式

```json
{
  "review_id": "REV-001",
  "timestamp": "2024-01-01T00:00:00Z",
  "pipeline_stage": "需求结构化|测试先行|实现决策|静态分析|测试执行|验收报告",
  "whitebox_validation": {
    "requirement_structuring": {
      "score": 0.95,
      "user_story_completeness": true,
      "acceptance_criteria_testable": 0.95,
      "feature_coverage": 1.0,
      "data_model_complete": true
    },
    "clarification_coverage": {
      "score": 0.98,
      "ambiguity_identification_rate": 0.98,
      "classification_complete": true,
      "priority_reasonable": true,
      "answer_confirmation_rate": 1.0
    },
    "trace_matrix_completeness": {
      "score": 0.95,
      "req_test_linkage": 1.0,
      "req_design_linkage": 0.95,
      "req_code_linkage": 0.90,
      "status_update_timely": true
    },
    "decision_record_completeness": {
      "score": 0.90,
      "log_coverage": 1.0,
      "reasoning_clarity": 0.85,
      "alternatives_recorded": true,
      "risk_assessed": true
    },
    "test_requirement_linkage": {
      "score": 0.92,
      "requirement_coverage": 0.97,
      "acceptance_mapping": 1.0,
      "boundary_coverage": 0.82,
      "exception_coverage": 0.75
    },
    "nonfunctional_check": {
      "score": 0.88,
      "performance_defined": true,
      "security_defined": true,
      "availability_defined": true,
      "scalability_defined": true,
      "compatibility_defined": true
    }
  },
  "overall_whitebox_score": 0.93,
  "pass_threshold": 0.85,
  "passed": true,
  "issues": [
    {
      "category": "需求结构化|澄清覆盖|追踪矩阵|决策记录|测试关联|非功能检查",
      "severity": "critical|major|minor",
      "description": "问题描述",
      "recommendation": "改进建议"
    }
  ]
}
```

---

### 阶段四：SDD规范一致性验证流程

```
白盒化验证通过
    ↓
[1] 规范元素覆盖验证
    ↓
[2] 接口契约验证
    ↓
[3] 业务规则覆盖验证
    ↓
[4] 约束条件验证
    ↓
[5] 架构合规性验证
    ↓
输出SDD验证报告
```

#### 规范与实现一致性检查

| 检查项 | 检查内容 | 通过标准 |
|--------|----------|----------|
| 规范元素覆盖 | 实现是否覆盖规范中所有定义的元素 | 覆盖率100% |
| 功能点对应 | 每个规范功能点是否有对应实现 | 对应率100% |
| 数据结构一致性 | 实现数据结构是否与规范定义一致 | 一致性100% |
| 行为一致性 | 实现行为是否符合规范描述 | 符合率≥95% |

#### 接口契约验证

| 检查项 | 检查内容 | 通过标准 |
|--------|----------|----------|
| 接口签名一致性 | 实现接口签名是否与规范定义一致 | 一致性100% |
| 参数类型验证 | 参数类型是否符合规范定义 | 符合率100% |
| 返回值验证 | 返回值类型和结构是否符合规范 | 符合率100% |
| 异常处理验证 | 异常处理是否符合规范定义 | 覆盖率≥90% |

#### 业务规则覆盖验证

| 检查项 | 检查内容 | 通过标准 |
|--------|----------|----------|
| 业务规则实现 | 规范中的业务规则是否全部实现 | 实现率100% |
| 规则优先级 | 业务规则优先级处理是否正确 | 正确率100% |
| 规则冲突处理 | 规则冲突处理是否符合规范 | 符合规范 |
| 规则执行顺序 | 规则执行顺序是否正确 | 正确率100% |

#### 约束条件验证

| 检查项 | 检查内容 | 通过标准 |
|--------|----------|----------|
| 数据约束 | 数据约束条件是否全部实现 | 实现率100% |
| 业务约束 | 业务约束条件是否全部实现 | 实现率100% |
| 安全约束 | 安全约束条件是否全部实现 | 实现率100% |
| 性能约束 | 性能约束条件是否满足 | 满足率≥95% |

#### 架构合规性检查

| 检查项 | 检查内容 | 通过标准 |
|--------|----------|----------|
| 架构遵循 | 实现是否遵循架构设计 | 遵循率100% |
| 设计模式 | 是否正确应用设计模式 | 应用正确 |
| 分层架构 | 是否遵循分层架构原则 | 分层正确 |
| 依赖关系 | 依赖关系是否符合架构设计 | 依赖正确 |

#### SDD规范验证输出格式

```json
{
  "validation_id": "VAL-001",
  "timestamp": "2024-01-01T00:00:00Z",
  "specification_version": "1.0.0",
  "implementation_version": "1.0.0",
  "validation_results": {
    "specification_implementation_consistency": {
      "score": 0.98,
      "element_coverage": 1.0,
      "function_mapping": 1.0,
      "data_structure_consistency": 1.0,
      "behavior_consistency": 0.95,
      "details": [
        {
          "spec_element": "规范元素名称",
          "implementation_element": "实现元素名称",
          "consistency": true,
          "deviation": "偏差描述（如有）"
        }
      ]
    },
    "interface_contract_validation": {
      "score": 1.0,
      "signature_consistency": 1.0,
      "parameter_type_match": 1.0,
      "return_value_match": 1.0,
      "exception_handling_coverage": 0.92,
      "details": [
        {
          "interface_name": "接口名称",
          "spec_signature": "规范签名",
          "implementation_signature": "实现签名",
          "match": true,
          "issues": []
        }
      ]
    },
    "business_rule_coverage": {
      "score": 1.0,
      "rule_implementation_rate": 1.0,
      "priority_handling_correct": true,
      "conflict_resolution_valid": true,
      "execution_order_correct": true,
      "details": [
        {
          "rule_id": "规则ID",
          "rule_name": "规则名称",
          "implemented": true,
          "test_covered": true,
          "issues": []
        }
      ]
    },
    "constraint_validation": {
      "score": 0.96,
      "data_constraint_implementation": 1.0,
      "business_constraint_implementation": 1.0,
      "security_constraint_implementation": 1.0,
      "performance_constraint_satisfaction": 0.96,
      "details": [
        {
          "constraint_type": "data|business|security|performance",
          "constraint_name": "约束名称",
          "spec_value": "规范值",
          "implementation_value": "实现值",
          "satisfied": true
        }
      ]
    },
    "architecture_compliance": {
      "score": 0.95,
      "architecture_followed": 1.0,
      "design_pattern_correct": true,
      "layer_architecture_correct": true,
      "dependency_correct": true
    }
  },
  "overall_consistency_score": 0.98,
  "pass_threshold": 0.90,
  "passed": true,
  "issues": [
    {
      "category": "规范一致性|接口契约|业务规则|约束条件|架构合规",
      "severity": "critical|major|minor",
      "spec_reference": "规范引用位置",
      "implementation_location": "实现位置",
      "description": "问题描述",
      "recommendation": "改进建议"
    }
  ],
  "validation_summary": {
    "total_checks": 50,
    "passed_checks": 48,
    "failed_checks": 0,
    "warnings": 2
  }
}
```

---

### 阶段五：规范变更影响分析流程

```
收到规范变更通知
    ↓
[1] 变更识别与分类
    ↓
[2] 影响范围识别
    ↓
[3] 影响程度评估
    ↓
[4] 风险评估
    ↓
[5] 变更建议生成
    ↓
输出变更影响分析报告
```

#### 变更影响分析步骤

**1. 变更识别**
- 识别规范变更的具体内容
- 分类变更类型（新增/修改/删除）
- 确定变更优先级

**2. 影响范围识别**
- 识别受影响的实现模块
- 识别受影响的接口定义
- 识别受影响的数据结构
- 识别受影响的业务规则

**3. 影响程度评估**
- 评估对现有功能的影响程度
- 评估对系统架构的影响程度
- 评估对数据完整性的影响程度
- 评估对系统性能的影响程度

**4. 风险评估**
- 识别潜在风险点
- 评估风险等级（高/中/低）
- 制定风险缓解措施

**5. 变更建议**
- 提出实现调整建议
- 提出测试补充建议
- 提出文档更新建议

#### 变更影响分析输出格式

```json
{
  "change_id": "CHG-001",
  "timestamp": "2024-01-01T00:00:00Z",
  "specification_changes": [
    {
      "change_type": "add|modify|delete",
      "element_type": "function|interface|data|rule|constraint",
      "element_name": "元素名称",
      "description": "变更描述"
    }
  ],
  "impact_analysis": {
    "affected_modules": [
      {
        "module_name": "模块名称",
        "impact_level": "high|medium|low",
        "impact_description": "影响描述",
        "required_changes": ["需要的变更列表"]
      }
    ],
    "affected_interfaces": [
      {
        "interface_name": "接口名称",
        "impact_type": "signature|behavior|deprecated",
        "description": "影响描述"
      }
    ],
    "affected_data_structures": [
      {
        "structure_name": "数据结构名称",
        "change_required": true,
        "migration_needed": true,
        "description": "影响描述"
      }
    ],
    "affected_business_rules": [
      {
        "rule_name": "规则名称",
        "impact_type": "modified|removed|new_priority",
        "description": "影响描述"
      }
    ]
  },
  "risk_assessment": [
    {
      "risk_id": "风险ID",
      "risk_level": "high|medium|low",
      "risk_description": "风险描述",
      "affected_components": ["受影响组件列表"],
      "mitigation_strategy": "缓解策略"
    }
  ],
  "recommendations": {
    "implementation_changes": ["实现变更建议"],
    "test_additions": ["测试补充建议"],
    "documentation_updates": ["文档更新建议"]
  },
  "overall_impact_score": 0.5,
  "approval_required": true
}
```

---

### 阶段六：审议结论与移交

```
所有评审完成
    ↓
[1] 综合评估
    ↓
[2] 审议结论生成
    ↓
[3] 决策记录
    ↓
通过 → 移交尚书省执行
不通过 → 退回中书省修改
```

**审议结论标准：**
| 结论 | 条件 | 后续动作 |
|------|------|----------|
| 通过 | 所有检查项通过，无严重问题 | 移交尚书省执行 |
| 有条件通过 | 存在轻微问题，不影响核心功能 | 通过并记录问题，要求限期修复 |
| 不通过 | 存在严重问题或关键检查项失败 | 退回中书省修改 |

**操作指南：**
- 调用 `../scripts/record_skill_call.py` 记录审议过程
- 生成完整的评审报告
- 通过后移交尚书省执行，不通过则退回中书省修改

---

## 评审标准汇总

### 综合评审标准

| 评审类别 | 权重 | 通过阈值 |
|----------|------|----------|
| 需求完整性 | 20% | ≥95% |
| 设计合理性 | 20% | ≥90% |
| 架构合规性 | 15% | ≥95% |
| 代码质量 | 15% | 无严重问题 |
| 测试覆盖率 | 15% | ≥80% |
| 规范一致性 | 15% | ≥90% |

### 问题严重级别定义

| 级别 | 定义 | 处理要求 |
|------|------|----------|
| Critical | 导致系统无法运行或严重安全漏洞 | 必须修复才能通过 |
| Major | 影响核心功能或性能 | 建议修复，可记录限期处理 |
| Minor | 影响用户体验或代码质量 | 可记录，非阻塞 |
| Info | 建议性改进 | 参考性意见 |

---

## 透明度验证要求

### 透明度评审标准

在评审过程中，需额外验证以下透明度相关标准：
- **决策日志完整性**：检查中书省输出的决策日志是否完整记录了关键决策的推理过程
- **输入输出可追溯性**：验证每个决策的输入条件和输出结果是否可追溯
- **代码变更可解释性**：确保代码变更能够通过决策日志解释其来源和原因
- **推理过程清晰度**：评估推理过程描述是否清晰、逻辑是否连贯

### 透明度验证流程

**1. 决策日志检查**
- 检查关键决策是否有完整日志记录
- 验证日志格式是否符合规范
- 确认时间戳和决策链完整性

**2. 可追溯性验证**
- 检查数据流转是否可追溯
- 验证需求到设计到代码的映射关系
- 确认变更历史与决策日志对应

**3. 透明度评分**
- 完整性评分：日志覆盖关键决策的比例
- 清晰度评分：推理过程描述的可理解程度
- 可追溯性评分：输入输出链路的完整程度

### 透明度验证输出

```json
{
  "review_id": "评审ID",
  "timestamp": "评审时间戳",
  "transparency_score": {
    "completeness": 0.95,
    "clarity": 0.90,
    "traceability": 0.92,
    "overall": 0.92
  },
  "issues": [
    {
      "type": "missing_log|unclear_reasoning|broken_trace",
      "location": "问题位置",
      "description": "问题描述",
      "severity": "high|medium|low"
    }
  ],
  "recommendations": ["改进建议列表"]
}
```

---

## 协作说明

### 与中书省的协作

| 协作点 | 协作内容 | 交付物 |
|--------|----------|--------|
| 方案接收 | 接收中书省移交的产出物 | 全套产出物 |
| 问题反馈 | 向中书省反馈评审问题 | 评审问题清单 |
| 修改确认 | 确认中书省的修改是否满足要求 | 确认结果 |

### 与尚书省的协作

| 协作点 | 协作内容 | 交付物 |
|--------|----------|--------|
| 方案移交 | 将通过审议的方案移交尚书省 | 评审通过标记 |
| 执行监督 | 监督尚书省的执行情况 | 监督报告 |
| 问题上报 | 将执行中的问题上报 | 问题报告 |

---

## 输出物清单

| 输出物 | 格式 | 移交对象 |
|--------|------|----------|
| 评审报告 | Markdown | 中书省、尚书省 |
| 白盒化验证报告 | JSON | 中书省、尚书省 |
| SDD验证报告 | JSON | 中书省、尚书省 |
| 变更影响分析报告 | JSON | 中书省、尚书省 |
| 问题清单 | Markdown/JSON | 中书省 |
| 决策记录 | JSON | 存档 |
| 透明度验证报告 | JSON | 中书省 |

---

## 协同调用接口

### 接口定义

门下省作为审议机构，提供以下协同调用接口供其他技能调用：

| 接口名称 | 接口描述 | 调用方 |
|----------|----------|--------|
| `review_proposal` | 方案评审接口 | 中书省、尚书省 |
| `validate_whitebox` | 白盒化验证接口 | 中书省、尚书省 |
| `verify_sdd_compliance` | SDD规范验证接口 | 工部 |
| `analyze_change_impact` | 变更影响分析接口 | 中书省、尚书省 |
| `approve_deployment` | 部署审批接口 | 工部 |

### 输入参数规范

#### 方案评审接口参数

```json
{
  "interface": "review_proposal",
  "version": "1.0.0",
  "timestamp": "2024-01-01T00:00:00Z",
  "caller": "调用方标识",
  "parameters": {
    "proposal_id": "方案ID",
    "proposal_type": "requirement|architecture|design|test",
    "deliverables": [
      {
        "type": "document_type",
        "path": "文档路径",
        "format": "markdown|json"
      }
    ],
    "review_scope": ["需求完整性", "架构合理性", "设计规范性"],
    "strictness": "high|medium|low"
  }
}
```

#### 白盒化验证接口参数

```json
{
  "interface": "validate_whitebox",
  "version": "1.0.0",
  "timestamp": "2024-01-01T00:00:00Z",
  "caller": "调用方标识",
  "parameters": {
    "project_id": "项目ID",
    "validation_scope": [
      "requirement_structuring",
      "clarification_coverage",
      "trace_matrix",
      "decision_record",
      "test_linkage"
    ],
    "threshold": 0.85
  }
}
```

#### SDD规范验证接口参数

```json
{
  "interface": "verify_sdd_compliance",
  "version": "1.0.0",
  "timestamp": "2024-01-01T00:00:00Z",
  "caller": "调用方标识",
  "parameters": {
    "spec_version": "1.0.0",
    "implementation_path": "实现代码路径",
    "validation_items": [
      "spec_element_coverage",
      "interface_contract",
      "business_rule_coverage",
      "constraint_validation",
      "architecture_compliance"
    ]
  }
}
```

### 输出格式规范

#### 评审报告格式

```json
{
  "interface": "review_proposal",
  "call_id": "REVIEW-001",
  "timestamp": "2024-01-01T00:00:00Z",
  "status": "passed|conditional|rejected",
  "result": {
    "overall_score": 0.92,
    "review_details": {
      "requirement_completeness": {"score": 0.95, "passed": true},
      "architecture_rationality": {"score": 0.90, "passed": true},
      "design_compliance": {"score": 0.92, "passed": true}
    },
    "issues": [
      {
        "id": "ISSUE-001",
        "category": "需求完整性|架构合理性|设计规范性",
        "severity": "critical|major|minor",
        "description": "问题描述",
        "recommendation": "改进建议",
        "location": "问题位置"
      }
    ],
    "conditional_pass_requirements": ["有条件通过需满足的条件"]
  },
  "next_action": "移交尚书省|退回中书省修改"
}
```

### 调用示例

#### 示例1：方案评审调用

```bash
# 调用方案评审接口
调用 ./SKILL.md --interface=review_proposal \
  --proposal-id="PROP-001" \
  --proposal-type="architecture" \
  --deliverables='[{"type":"architecture_doc","path":"docs/arch.md"}]' \
  --strictness=high
```

#### 示例2：SDD规范验证调用

```bash
# 调用SDD规范验证接口
调用 ./SKILL.md --interface=verify_sdd_compliance \
  --spec-version="1.0.0" \
  --implementation-path="./src/" \
  --validation-items='["interface_contract","business_rule_coverage"]'
```

### 协同回调接口

门下省在完成审议后，会通过以下回调接口通知相关技能：

| 回调接口 | 触发时机 | 回调目标 |
|----------|----------|----------|
| `on_review_passed` | 评审通过时 | 尚书省 |
| `on_review_rejected` | 评审不通过时 | 中书省 |
| `on_compliance_verified` | 规范验证完成时 | 工部 |

#### 回调数据格式

```json
{
  "callback": "on_review_passed",
  "call_id": "REVIEW-001",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "proposal_id": "PROP-001",
    "review_result": "passed",
    "score": 0.92,
    "deliverables_approved": ["交付物列表"],
    "next_handler": "shangshusheng"
  }
}
```

---

## 子技能引用

| 子技能 | 用途 |
|--------|------|
| [代码审查](../subskills/daima_shencha.md) | 代码质量检查 |
| [人工确认](../subskills/rengong_queren.md) | 高风险决策点人工确认 |

---

## 代码审查流程（增强版）

### 代码审查流程概览

```
代码提交
    ↓
[1] 静态分析
    ↓
[2] 规范检查
    ↓
[3] 安全扫描
    ↓
[4] 复杂度分析
    ↓
[5] 重复代码检测
    ↓
[6] 依赖分析
    ↓
[7] 测试覆盖率检查
    ↓
[8] 人工审查要点生成
    ↓
[9] 代码质量趋势分析
    ↓
[10] 审查结果汇总与报告
    ↓
输出代码审查报告
```

### 1. 静态分析

**分析维度：**
| 维度 | 检查内容 | 工具建议 | 通过标准 |
|------|----------|----------|----------|
| 语法错误 | 代码语法正确性 | ESLint/Pylint | 0错误 |
| 类型检查 | 类型一致性 | TypeScript/mypy | 类型正确 |
| 未使用变量 | 变量使用情况 | 静态分析工具 | 无未使用变量 |
| 空指针风险 | 空值处理 | 静态分析工具 | 无空指针风险 |

### 2. 规范检查

**编码规范检查清单：**
```yaml
coding_standards:
  naming_conventions:
    - rule: "类名使用PascalCase"
      severity: "warning"
    - rule: "函数名使用camelCase或snake_case"
      severity: "warning"
    - rule: "常量使用UPPER_CASE"
      severity: "info"
    - rule: "私有成员使用_前缀"
      severity: "info"
      
  code_structure:
    - rule: "函数长度不超过50行"
      severity: "warning"
    - rule: "文件长度不超过500行"
      severity: "warning"
    - rule: "嵌套深度不超过4层"
      severity: "warning"
    - rule: "参数数量不超过5个"
      severity: "info"
      
  documentation:
    - rule: "公共函数必须有文档注释"
      severity: "warning"
    - rule: "复杂逻辑必须有注释说明"
      severity: "info"
    - rule: "TODO注释必须关联Issue"
      severity: "info"
```

### 3. 安全扫描

**安全检查项：**
| 检查项 | 描述 | 严重级别 |
|--------|------|----------|
| SQL注入 | 检查SQL拼接风险 | Critical |
| XSS漏洞 | 检查跨站脚本风险 | Critical |
| 敏感信息泄露 | 检查硬编码密钥/密码 | Critical |
| 权限绕过 | 检查权限校验完整性 | High |
| 输入验证 | 检查输入数据验证 | High |
| 日志安全 | 检查敏感信息日志 | Medium |

**安全扫描配置：**
```yaml
security_scan:
  rules:
    - id: "SEC-001"
      name: "硬编码密钥检测"
      pattern: "(password|secret|key|token)\\s*=\\s*['\"][^'\"]+['\"]"
      severity: "critical"
      
    - id: "SEC-002"
      name: "SQL注入检测"
      pattern: "execute\\(.*\\+.*\\)"
      severity: "critical"
      
    - id: "SEC-003"
      name: "XSS风险检测"
      pattern: "innerHTML\\s*=|document\\.write"
      severity: "high"
      
  exemptions:
    - path: "tests/**"
      rules: ["SEC-001"]
    - path: "config/**"
      rules: ["SEC-001"]
```

### 4. 复杂度分析

**复杂度指标：**
| 指标 | 计算方式 | 阈值 | 处理建议 |
|------|----------|------|----------|
| 圈复杂度 | 分支数量+1 | ≤10 | 拆分函数 |
| 认知复杂度 | 嵌套和跳转累加 | ≤15 | 简化逻辑 |
| 耦合度 | 依赖数量 | ≤5 | 解耦重构 |
| 内聚度 | 功能相关性 | ≥0.7 | 职责分离 |

**复杂度分析报告格式：**
```json
{
  "analysis_id": "COMP-001",
  "timestamp": "2024-01-01T00:00:00Z",
  "file_path": "src/services/user_service.py",
  "metrics": {
    "cyclomatic_complexity": {
      "value": 8,
      "threshold": 10,
      "status": "pass",
      "functions": [
        {
          "name": "create_user",
          "value": 5,
          "status": "pass"
        },
        {
          "name": "validate_user",
          "value": 3,
          "status": "pass"
        }
      ]
    },
    "cognitive_complexity": {
      "value": 12,
      "threshold": 15,
      "status": "pass"
    },
    "coupling": {
      "value": 4,
      "threshold": 5,
      "status": "pass",
      "dependencies": ["repository", "validator", "logger", "config"]
    },
    "cohesion": {
      "value": 0.85,
      "threshold": 0.7,
      "status": "pass"
    }
  },
  "overall_status": "pass",
  "recommendations": []
}
```

### 5. 重复代码检测

**检测配置：**
```yaml
duplication_detection:
  minimum_tokens: 50
  minimum_lines: 5
  ignore_patterns:
    - "tests/**"
    - "**/*.min.js"
    - "**/generated/**"
    
  similarity_threshold: 0.8
  
  reporting:
    include_snippets: true
    max_snippet_lines: 10
    group_similar: true
```

**重复代码报告格式：**
```json
{
  "detection_id": "DUP-001",
  "timestamp": "2024-01-01T00:00:00Z",
  "duplications": [
    {
      "id": "DUP-BLOCK-001",
      "similarity": 0.95,
      "locations": [
        {
          "file": "src/services/user_service.py",
          "start_line": 45,
          "end_line": 65
        },
        {
          "file": "src/services/admin_service.py",
          "start_line": 30,
          "end_line": 50
        }
      ],
      "lines_count": 20,
      "tokens_count": 150,
      "suggested_refactoring": "提取公共方法到base_service.py"
    }
  ],
  "summary": {
    "total_duplications": 1,
    "total_duplicated_lines": 20,
    "duplication_percentage": 2.5
  }
}
```

### 6. 依赖分析

**依赖检查项：**
| 检查项 | 描述 | 风险级别 |
|--------|------|----------|
| 循环依赖 | 模块间循环引用 | High |
| 过时依赖 | 使用过时版本 | Medium |
| 安全漏洞 | 依赖包安全漏洞 | Critical |
| 许可证合规 | 许可证兼容性 | Medium |
| 未使用依赖 | 声明但未使用 | Low |

**依赖分析输出：**
```json
{
  "analysis_id": "DEP-001",
  "timestamp": "2024-01-01T00:00:00Z",
  "dependencies": {
    "direct": [
      {
        "name": "express",
        "version": "4.18.2",
        "status": "ok",
        "latest_version": "4.18.2",
        "license": "MIT",
        "vulnerabilities": []
      }
    ],
    "dev": [
      {
        "name": "jest",
        "version": "29.0.0",
        "status": "outdated",
        "latest_version": "29.7.0",
        "license": "MIT",
        "vulnerabilities": []
      }
    ]
  },
  "issues": [
    {
      "type": "outdated",
      "dependency": "jest",
      "severity": "low",
      "recommendation": "升级到最新版本 29.7.0"
    }
  ],
  "circular_dependencies": [],
  "unused_dependencies": ["lodash"]
}
```

### 7. 测试覆盖率检查

**覆盖率标准：**
| 类型 | 最低覆盖率 | 目标覆盖率 |
|------|------------|------------|
| 行覆盖率 | 80% | 90% |
| 分支覆盖率 | 70% | 85% |
| 函数覆盖率 | 85% | 95% |
| 语句覆盖率 | 80% | 90% |

### 8. 人工审查要点生成

**自动生成审查要点：**
```json
{
  "review_id": "REV-001",
  "timestamp": "2024-01-01T00:00:00Z",
  "review_points": [
    {
      "category": "logic",
      "priority": "high",
      "location": "src/services/payment.py:45-60",
      "description": "支付逻辑需要重点审查",
      "reason": "涉及金钱交易，复杂度高",
      "checklist": [
        "确认支付状态转换正确",
        "验证并发处理逻辑",
        "检查异常处理完整性"
      ]
    },
    {
      "category": "security",
      "priority": "critical",
      "location": "src/auth/login.py:20-35",
      "description": "认证逻辑需要安全审查",
      "reason": "涉及用户认证和会话管理",
      "checklist": [
        "确认密码处理安全",
        "验证Token生成逻辑",
        "检查会话管理安全"
      ]
    }
  ],
  "estimated_review_time": "30分钟",
  "focus_areas": ["支付逻辑", "认证安全", "数据验证"]
}
```

### 9. 代码质量趋势分析

**趋势分析维度：**
| 分析维度 | 分析内容 | 输出形式 |
|----------|----------|----------|
| 质量趋势 | 代码质量随时间变化 | 趋势图 |
| 问题分布 | 问题类型分布变化 | 饼图/柱状图 |
| 复杂度趋势 | 代码复杂度变化 | 折线图 |
| 覆盖率趋势 | 测试覆盖率变化 | 折线图 |
| 技术债务 | 技术债务累积趋势 | 面积图 |

**趋势分析输出格式：**
```json
{
  "trend_analysis_id": "TREND-001",
  "timestamp": "2024-01-01T00:00:00Z",
  "analysis_period": {
    "start": "2024-01-01T00:00:00Z",
    "end": "2024-01-31T00:00:00Z",
    "granularity": "daily|weekly|monthly"
  },
  "trends": {
    "quality_score": {
      "current": 85.5,
      "previous": 82.3,
      "change": 3.2,
      "trend": "improving|declining|stable",
      "data_points": [
        {"date": "2024-01-01", "value": 82.3},
        {"date": "2024-01-15", "value": 84.0},
        {"date": "2024-01-31", "value": 85.5}
      ]
    },
    "issue_distribution": {
      "by_severity": {
        "critical": {"current": 0, "previous": 1, "trend": "improving"},
        "major": {"current": 2, "previous": 3, "trend": "improving"},
        "minor": {"current": 5, "previous": 4, "trend": "declining"}
      },
      "by_category": {
        "security": {"current": 1, "previous": 2},
        "performance": {"current": 2, "previous": 2},
        "maintainability": {"current": 4, "previous": 4}
      }
    },
    "complexity": {
      "average_cyclomatic": {"current": 8.5, "previous": 9.2, "trend": "improving"},
      "high_complexity_files": {"current": 3, "previous": 5, "trend": "improving"}
    },
    "test_coverage": {
      "line_coverage": {"current": 85.5, "previous": 82.0, "trend": "improving"},
      "branch_coverage": {"current": 78.2, "previous": 75.5, "trend": "improving"}
    },
    "technical_debt": {
      "total_hours": {"current": 24, "previous": 30, "trend": "improving"},
      "debt_ratio": {"current": 0.12, "previous": 0.15, "trend": "improving"}
    }
  },
  "predictions": {
    "quality_forecast": {
      "next_period": 87.0,
      "confidence": 0.85
    },
    "risk_areas": [
      {
        "area": "模块A复杂度持续上升",
        "risk_level": "medium",
        "recommendation": "建议进行重构"
      }
    ]
  },
  "insights": [
    "代码质量整体呈上升趋势",
    "安全问题显著减少",
    "测试覆盖率稳步提升"
  ]
}
```

### 10. 审查结果汇总与报告

**汇总报告结构：**
```json
{
  "report_id": "RPT-001",
  "timestamp": "2024-01-01T00:00:00Z",
  "review_scope": {
    "repository": "项目名称",
    "branch": "分支名称",
    "commit_range": ["commit1", "commit2"],
    "files_reviewed": 25
  },
  "executive_summary": {
    "overall_status": "pass|conditional_pass|fail",
    "overall_score": 85.5,
    "key_findings": [
      "代码质量良好，无严重问题",
      "测试覆盖率达标",
      "存在2个中等级别安全风险"
    ],
    "recommendation": "建议合并，需跟进中等级别问题修复"
  },
  "detailed_results": {
    "static_analysis": {
      "status": "pass",
      "score": 90,
      "summary": "静态分析通过，发现3个警告"
    },
    "security_scan": {
      "status": "conditional_pass",
      "score": 80,
      "summary": "发现2个中等级别安全风险"
    },
    "complexity_analysis": {
      "status": "pass",
      "score": 85,
      "summary": "复杂度在可接受范围内"
    },
    "test_coverage": {
      "status": "pass",
      "score": 85.5,
      "summary": "覆盖率达标"
    }
  },
  "issues_summary": {
    "by_severity": {
      "critical": 0,
      "major": 2,
      "minor": 5,
      "info": 10
    },
    "by_category": {
      "security": 2,
      "performance": 1,
      "maintainability": 4
    },
    "blocking_issues": 0
  },
  "action_items": [
    {
      "priority": "high",
      "item": "修复安全扫描发现的2个中等级别风险",
      "assignee": "开发团队",
      "deadline": "2024-01-05T00:00:00Z"
    }
  ],
  "metrics_comparison": {
    "vs_previous_review": {
      "score_change": 3.2,
      "issues_change": -2,
      "coverage_change": 3.5
    },
    "vs_baseline": {
      "score_change": 5.0,
      "issues_change": -5,
      "coverage_change": 8.0
    }
  },
  "approval": {
    "auto_approved": false,
    "required_approvers": 1,
    "current_approvals": 0,
    "approval_criteria_met": true
  },
  "attachments": [
    {
      "type": "trend_chart",
      "path": "reports/trend_20240101.png"
    },
    {
      "type": "coverage_report",
      "path": "reports/coverage_20240101.html"
    }
  ]
}
```

### 代码审查综合报告格式

```json
{
  "review_id": "CODE-REV-001",
  "timestamp": "2024-01-01T00:00:00Z",
  "commit_hash": "abc123def456",
  "branch": "feature/user-auth",
  "author": "developer",
  
  "summary": {
    "files_changed": 5,
    "lines_added": 250,
    "lines_deleted": 50,
    "overall_status": "conditional_pass"
  },
  
  "checks": {
    "static_analysis": {
      "status": "pass",
      "errors": 0,
      "warnings": 3,
      "info": 5
    },
    "coding_standards": {
      "status": "pass",
      "violations": 2
    },
    "security_scan": {
      "status": "pass",
      "critical": 0,
      "high": 0,
      "medium": 1,
      "low": 2
    },
    "complexity": {
      "status": "pass",
      "high_complexity_functions": 1
    },
    "duplication": {
      "status": "pass",
      "duplicated_lines": 15,
      "duplication_percentage": 2.5
    },
    "dependencies": {
      "status": "warning",
      "issues": 1
    },
    "test_coverage": {
      "status": "pass",
      "line_coverage": 85.5,
      "branch_coverage": 78.2,
      "function_coverage": 92.0
    }
  },
  
  "issues": [
    {
      "id": "ISSUE-001",
      "category": "security",
      "severity": "medium",
      "file": "src/auth/login.py",
      "line": 25,
      "description": "建议使用bcrypt替代SHA256进行密码哈希",
      "recommendation": "使用bcrypt或argon2进行密码哈希"
    }
  ],
  
  "recommendations": [
    "修复安全扫描中的中等级别问题",
    "升级过时的依赖包",
    "为新增的复杂函数添加单元测试"
  ],
  
  "approval_status": {
    "auto_approve": false,
    "required_reviewers": 1,
    "current_approvals": 0,
    "blocking_issues": 0
  }
}
```

---

## 协同效果评估能力

### 审议协同评估指标

门下省作为审议机构，负责评估审议环节在三省六部协同中的效果。

| 评估维度 | 指标 | 目标值 | 度量方法 |
|----------|------|--------|----------|
| 审议效率 | 平均审议时间 | ≤2小时 | 时间戳差值统计 |
| 审议质量 | 审议通过后无重大返工 | ≥95% | 返工率统计 |
| 问题发现率 | 审议发现的问题占全部问题比例 | ≥80% | 问题来源分析 |
| 决策一致性 | 审议决策与最终结果一致率 | ≥90% | 决策追踪分析 |
| 协同阻塞率 | 因审议导致的阻塞时间占比 | ≤10% | 阻塞时间统计 |

### 审议协同评估流程

```
[1] 收集审议数据
    ↓
[2] 计算审议效率指标
    ↓
[3] 分析审议质量
    ↓
[4] 评估协同影响
    ↓
[5] 生成优化建议
    ↓
输出《审议协同评估报告》
```

### 审议协同评估报告格式

```json
{
  "evaluation_id": "EVAL-MEN-001",
  "timestamp": "2024-01-01T00:00:00Z",
  "period": {
    "start": "2024-01-01T00:00:00Z",
    "end": "2024-01-07T23:59:59Z"
  },
  "review_metrics": {
    "total_reviews": 15,
    "passed_reviews": 13,
    "conditional_passes": 2,
    "rejected_reviews": 0,
    "avg_review_time_minutes": 95,
    "avg_revision_count": 0.3
  },
  "quality_metrics": {
    "issues_found_in_review": 45,
    "issues_found_after_pass": 5,
    "issue_detection_rate": 0.90,
    "false_positive_rate": 0.05,
    "critical_issues_missed": 0
  },
  "coordination_impact": {
    "blocking_time_hours": 2.5,
    "blocking_ratio": 0.08,
    "parallel_reviews": 3,
    "queue_wait_time_minutes": 15
  },
  "province_coordination": {
    "zhongshusheng": {
      "submissions": 15,
      "avg_quality_on_submit": 0.85,
      "revision_rate": 0.20,
      "feedback_effectiveness": 0.92
    },
    "shangshusheng": {
      "handovers": 13,
      "execution_success_rate": 0.95,
      "return_rate": 0.05
    }
  },
  "recommendations": [
    {
      "category": "efficiency",
      "priority": "medium",
      "description": "优化审议队列调度，减少等待时间",
      "expected_impact": "预计等待时间减少30%"
    }
  ]
}
```

---

## 流水线审议能力

### 流水线审议节点

门下省在白盒化7阶段流水线中负责审议批准阶段，并参与其他阶段的质量门禁检查。

| 阶段 | 门下省角色 | 检查内容 | 通过标准 |
|------|------------|----------|----------|
| 需求分析 | 监督 | 需求完整性检查 | 完整性≥90% |
| SDD规范定义 | 监督 | 规范完整性检查 | 规范覆盖≥85% |
| 审议批准 | 主导 | 全面审议 | 综合评分≥85% |
| 测试先行 | 质量门禁 | 测试用例评审 | 覆盖率≥80% |
| 代码实现 | 质量门禁 | 代码审查 | 无严重问题 |
| 持续重构 | 质量门禁 | 重构效果验证 | 质量提升≥10% |
| 部署发布 | 审批 | 部署前审批 | 审批通过 |

### 质量门禁配置

```yaml
quality_gates:
  requirement_analysis:
    enabled: true
    checks:
      - name: "需求完整性"
        threshold: 0.90
        blocking: true
      - name: "验收标准可测试性"
        threshold: 0.95
        blocking: true
      - name: "决策日志完整性"
        threshold: 0.85
        blocking: false
        
  sdd_specification:
    enabled: true
    checks:
      - name: "实体定义完整性"
        threshold: 1.0
        blocking: true
      - name: "接口契约完整性"
        threshold: 0.95
        blocking: true
      - name: "业务规则覆盖"
        threshold: 0.90
        blocking: true
        
  review_approval:
    enabled: true
    checks:
      - name: "综合审议评分"
        threshold: 0.85
        blocking: true
      - name: "无严重问题"
        threshold: 0
        blocking: true
      - name: "透明度评分"
        threshold: 0.80
        blocking: false
        
  test_first:
    enabled: true
    checks:
      - name: "测试覆盖率"
        threshold: 0.80
        blocking: true
      - name: "边界测试覆盖"
        threshold: 0.75
        blocking: false
      - name: "测试用例质量"
        threshold: 0.85
        blocking: true
        
  implementation:
    enabled: true
    checks:
      - name: "代码质量评分"
        threshold: 0.80
        blocking: true
      - name: "安全扫描通过"
        threshold: 1.0
        blocking: true
      - name: "测试通过率"
        threshold: 1.0
        blocking: true
        
  refactoring:
    enabled: true
    checks:
      - name: "复杂度降低"
        threshold: 0.10
        blocking: false
      - name: "代码重复率降低"
        threshold: 0.15
        blocking: false
      - name: "测试仍然通过"
        threshold: 1.0
        blocking: true
        
  deployment:
    enabled: true
    checks:
      - name: "部署前检查通过"
        threshold: 1.0
        blocking: true
      - name: "回滚方案就绪"
        threshold: 1.0
        blocking: true
      - name: "监控配置完整"
        threshold: 0.90
        blocking: false
```

### 质量门禁检查流程

```
阶段完成
    ↓
[1] 触发质量门禁检查
    ↓
[2] 执行检查项
    ↓
[3] 汇总检查结果
    ↓
[4] 判定是否通过
    ↓
通过 → 进入下一阶段
不通过 → 阻断并反馈
```

### 质量门禁检查报告

```json
{
  "gate_check_id": "GATE-001",
  "timestamp": "2024-01-01T00:00:00Z",
  "pipeline_id": "PIPE-001",
  "stage": "implementation",
  "check_results": [
    {
      "check_name": "代码质量评分",
      "actual_value": 0.82,
      "threshold": 0.80,
      "passed": true,
      "details": {
        "complexity_score": 0.85,
        "duplication_score": 0.90,
        "maintainability_score": 0.78
      }
    },
    {
      "check_name": "安全扫描通过",
      "actual_value": 1.0,
      "threshold": 1.0,
      "passed": true,
      "details": {
        "critical_issues": 0,
        "high_issues": 0,
        "medium_issues": 1,
        "low_issues": 3
      }
    },
    {
      "check_name": "测试通过率",
      "actual_value": 1.0,
      "threshold": 1.0,
      "passed": true,
      "details": {
        "total_tests": 50,
        "passed_tests": 50,
        "failed_tests": 0,
        "skipped_tests": 0
      }
    }
  ],
  "overall_result": "passed",
  "blocking_issues": 0,
  "warnings": 1,
  "next_action": "proceed_to_refactoring"
}
```

---

## 智能审议支持

### 审议优先级智能排序

```python
def calculate_review_priority(proposal):
    weights = {
        "business_impact": 0.25,
        "technical_risk": 0.20,
        "dependency_blocking": 0.20,
        "deadline_urgency": 0.15,
        "submitter_reputation": 0.10,
        "historical_quality": 0.10
    }
    
    scores = {
        "business_impact": evaluate_business_impact(proposal),
        "technical_risk": evaluate_technical_risk(proposal),
        "dependency_blocking": count_blocking_dependencies(proposal),
        "deadline_urgency": calculate_deadline_urgency(proposal),
        "submitter_reputation": get_submitter_reputation(proposal.submitter),
        "historical_quality": get_historical_quality_score(proposal.submitter)
    }
    
    return sum(scores[k] * weights[k] for k in weights)
```

### 审议要点自动生成

```json
{
  "auto_review_points_id": "ARP-001",
  "timestamp": "2024-01-01T00:00:00Z",
  "proposal_id": "PROP-001",
  "proposal_type": "feature",
  "generated_review_points": [
    {
      "category": "requirement",
      "priority": "high",
      "point": "验证用户认证流程的完整性",
      "reason": "涉及安全敏感功能",
      "checklist": [
        "确认密码存储方案",
        "验证会话管理机制",
        "检查权限控制逻辑"
      ]
    },
    {
      "category": "architecture",
      "priority": "medium",
      "point": "评估模块划分合理性",
      "reason": "新增模块较多",
      "checklist": [
        "检查模块职责划分",
        "评估模块间耦合度",
        "验证接口设计合理性"
      ]
    },
    {
      "category": "test",
      "priority": "high",
      "point": "验证测试覆盖充分性",
      "reason": "核心功能需要充分测试",
      "checklist": [
        "确认单元测试覆盖",
        "验证集成测试场景",
        "检查边界条件测试"
      ]
    }
  ],
  "estimated_review_time_minutes": 45,
  "focus_areas": ["安全认证", "模块设计", "测试覆盖"],
  "risk_areas": [
    {
      "area": "密码存储",
      "risk_level": "high",
      "recommendation": "重点审查加密方案"
    }
  ]
}
```

### 审议知识库

```yaml
review_knowledge_base:
  patterns:
    - name: "认证模块审查模式"
      triggers:
        - "authentication"
        - "login"
        - "password"
      review_points:
        - "密码存储安全"
        - "会话管理"
        - "权限控制"
        - "防暴力破解"
        
    - name: "支付模块审查模式"
      triggers:
        - "payment"
        - "transaction"
        - "money"
      review_points:
        - "金额计算精度"
        - "事务一致性"
        - "幂等性处理"
        - "对账机制"
        
    - name: "数据迁移审查模式"
      triggers:
        - "migration"
        - "data_transfer"
        - "schema_change"
      review_points:
        - "数据完整性"
        - "回滚方案"
        - "性能影响"
        - "兼容性处理"
```

---

## 增强功能集成

### 与provincial_coordinator集成

门下省通过provincial_coordinator.py实现审议流程的自动化和协同：

```python
from scripts.provincial_coordinator import (
    ProvincialCoordinator,
    SmartDispatcher,
    PipelineManager,
    ExecutionAnalyzer
)

coordinator = ProvincialCoordinator()
pipeline_manager = PipelineManager()
analyzer = ExecutionAnalyzer()

def review_proposal(proposal_id: str):
    pipeline_status = pipeline_manager.get_pipeline_status(proposal_id)
    
    if pipeline_status:
        current_stage = pipeline_status["stages"][pipeline_status["current_stage_index"]]
        
        quality_gate_result = check_quality_gate(
            current_stage["stage"],
            proposal_id
        )
        
        if quality_gate_result["passed"]:
            advance_result = pipeline_manager.advance_stage(
                pipeline_status["pipeline_id"],
                quality_gate_result["outputs"],
                quality_gate_result["quality_metrics"]
            )
            return advance_result
        else:
            return pipeline_manager.fail_stage(
                pipeline_status["pipeline_id"],
                quality_gate_result["error"]
            )
    
    return {"error": "Pipeline not found"}
```

### 智能分发集成

```python
from scripts.provincial_coordinator import TaskRequirement, SmartDispatcher

dispatcher = SmartDispatcher()

requirement = TaskRequirement(
    task_id="REVIEW-001",
    required_capabilities={
        "review_supervision": 0.9,
        "plan_review": 0.85
    },
    preferred_specializations=["menxiasheng"],
    priority=TaskPriority.HIGH
)

decision = dispatcher.find_best_match(requirement, "province")
```

---

## 审议质量保障

### 审议质量检查清单

```
□ 审议覆盖所有必要维度
□ 问题识别准确，无重大遗漏
□ 反馈清晰可执行
□ 审议时间在合理范围内
□ 决策依据充分，可追溯
□ 风险已识别并有缓解建议
□ 审议过程符合规范流程
□ 审议结果已完整记录
```

### 审议质量评分

| 评分项 | 权重 | 评分标准 |
|--------|------|----------|
| 覆盖完整性 | 25% | 审议覆盖所有必要维度 |
| 问题准确性 | 25% | 发现的问题准确有效 |
| 反馈质量 | 20% | 反馈清晰、可执行 |
| 效率合理性 | 15% | 审议时间合理 |
| 风险识别 | 15% | 识别潜在风险并提供建议 |

---

## v2.4.0 新增能力

### 代码异味智能检测

v2.4.0 新增智能代码异味检测能力，自动识别代码质量问题：

| 新增脚本 | 功能描述 |
|----------|----------|
| `intelligent_code_smell_detector.py` | AI驱动的智能代码异味检测 |
| `solid_principle_checker.py` | SOLID原则合规验证 |
| `design_pattern_checker.py` | 设计模式使用分析 |
| `tech_debt_tracker.py` | 技术债务识别与追踪 |

### API一致性验证器

新增API一致性验证器，确保前后端API契约一致：

```bash
# API一致性验证
python skillscripts/analysis/api_consistency_validator.py \
  --frontend-spec docs/api/frontend.yaml \
  --backend-spec docs/api/backend.yaml \
  --report api_consistency_report.md
```

### 质量趋势分析器

新增质量趋势分析器，追踪项目质量变化趋势：

```bash
# 生成质量趋势报告
python skillscripts/analysis/quality_trend_analyzer.py \
  --since "2024-01-01" \
  --output reports/quality_trend.md
```

### 增强审议能力

新增审议能力增强：

- 智能审议优先级排序
- 自动生成审议要点
- 审议知识库扩展
- 质量门禁自动检查

### 版本历史

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| 2.3.0 | 2026-03-30 | 新增协同效果评估、流水线审议、智能审议支持能力 |
| 2.4.0 | 2026-03-30 | 新增代码异味智能检测、API一致性验证、质量趋势分析、审议能力增强 |
| 2.7.1 | 2026-03-31 | 新增目录创建策略说明、审议报告路径配置 |

---

## 目录创建策略

### 门下省目录管理

门下省作为审议机构，在产出审议文档时遵循**按需创建目录**原则：

| 产出物 | 存储目录 | 创建时机 |
|--------|----------|----------|
| 评审报告 | `docs/workflow/review/` | 审议完成时 |
| 白盒化验证报告 | `docs/workflow/verification/` | 验证完成时 |
| SDD验证报告 | `docs/workflow/verification/` | 验证完成时 |
| 变更影响分析报告 | `docs/workflow/impact/` | 分析完成时 |

### 路径配置

```yaml
menxiasheng_paths:
  output_base: "docs/workflow/"
  review_reports: "docs/workflow/review/"
  verification_reports: "docs/workflow/verification/"
  impact_reports: "docs/workflow/impact/"
```

### 目录创建命令

```bash
# 通过路径配置管理器创建目录
python skillscripts/utils/path_config_manager.py create --type review
python skillscripts/utils/path_config_manager.py create --type verification
```
