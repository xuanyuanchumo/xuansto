---
name: zhongshusheng
description: 中书省，决策中枢，负责需求分析、项目立项、技术选型、设计规划、测试策略规划。当需要启动新项目或进行重大决策时调用。
---

# 中书省技能指令

## 职责定义

中书省作为三省决策中枢，承担以下核心职责：

| 职责类别 | 具体职责 | 关键产出 |
|----------|----------|----------|
| **需求工程** | 需求收集、分析、结构化、追踪 | 需求规格说明书、结构化需求文档 |
| **项目立项** | 可行性评估、项目计划制定 | 项目计划书、立项报告 |
| **技术决策** | 技术选型、架构设计 | 技术选型报告、架构设计文档 |
| **规范定义** | SDD规范定义、代码骨架生成 | SDD规范文档、代码骨架 |
| **测试规划** | 测试策略制定、验收标准定义 | 测试策略文档、验收测试用例 |
| **外部技能发现** | 技能扫描、匹配度评估 | 外部技能推荐列表 |

---

## 工作流程

### 阶段一：需求分析流程

```
用户需求输入
    ↓
[1] 需求收集与理解
    ↓
[2] 需求结构化（白盒化步骤1）
    ↓
[3] 澄清问题生成
    ↓
[4] 需求确认与记录
    ↓
[5] 需求追踪矩阵建立
    ↓
[6] 可行性研究
    ↓
[7] 需求优先级排序
    ↓
[8] 需求依赖分析
    ↓
[9] 需求变更影响预评估
    ↓
[10] 需求风险识别与缓解
    ↓
输出《需求规格说明书》
```

#### 1. 需求收集与理解

**操作指南：**
- 调用 `../subskills/xuqiu_fenxi.md` 进行需求分析
- 记录需求理解推理过程
- 识别隐含需求并记录推断依据

**关键活动：**
| 活动 | 描述 | 输出 |
|------|------|------|
| 利益相关者识别 | 识别所有相关方及其需求 | 利益相关者列表 |
| 需求来源分析 | 分析需求来源和背景 | 需求来源文档 |
| 需求分类 | 按功能/非功能/约束分类 | 需求分类表 |
| 优先级初判 | 初步评估需求优先级 | 优先级初稿 |

**需求理解推理记录格式：**
```json
{
  "understanding_id": "UND-001",
  "timestamp": "2024-01-01T00:00:00Z",
  "original_requirement": "用户原始需求描述",
  "interpreted_requirement": "理解后的需求描述",
  "assumptions": [
    {
      "assumption": "假设内容",
      "basis": "假设依据",
      "risk": "假设风险"
    }
  ],
  "implicit_requirements": [
    {
      "requirement": "隐含需求",
      "inferred_from": "推断来源",
      "confidence": "high|medium|low"
    }
  ],
  "questions": [
    {
      "question": "待确认问题",
      "impact": "问题影响",
      "suggested_answers": ["建议答案"]
    }
  ]
}

#### 2. 需求结构化（强制白盒化）

**操作指南：**
- 调用 `../subskills/xuqiu_jiegouhua.md` 进行需求结构化
- 必须生成标准格式的结构化需求文档

**结构化要求：**

| 结构化项 | 必填 | 详细说明 |
|----------|------|----------|
| 用户故事 | 是 | 每个需求必须有对应的用户故事（As a/I want/So that） |
| 验收标准 | 是 | 每个用户故事必须有可测试的验收条件 |
| 功能点分解 | 是 | 功能分解到可独立实现的粒度 |
| 数据模型 | 是 | 定义实体、属性、关系、约束 |
| 接口需求 | 条件 | 涉及集成的需求必须定义接口 |
| 非功能需求 | 是 | 性能、安全、可用性等要求 |

#### 3. 澄清问题生成

**操作指南：**
- 识别需求中的所有模糊点、歧义、遗漏
- 按类别（功能/数据/接口/性能/安全）分类问题
- 评估每个问题的影响和优先级

**澄清问题列表格式：**
```json
{
  "clarification_id": "CLAR-001",
  "timestamp": "2024-01-01T00:00:00Z",
  "questions": [
    {
      "id": "Q-001",
      "category": "功能|数据|接口|性能|安全",
      "question": "具体问题描述",
      "context": "问题上下文",
      "impact": "未澄清的影响描述",
      "suggested_answers": ["建议答案A", "建议答案B"],
      "priority": "high|medium|low",
      "status": "pending|clarified|deferred"
    }
  ]
}
```

#### 4. 需求确认与记录

**操作指南：**
- 整理所有澄清问题及确认答案
- 建立需求确认记录
- 确保需求理解一致性

#### 5. 需求追踪矩阵建立

**操作指南：**
- 建立需求到测试用例、设计文档、代码的追踪关系
- 定义需求状态流转规则

**需求追踪矩阵格式：**
```json
{
  "trace_matrix_id": "TRM-001",
  "requirements": [
    {
      "req_id": "REQ-001",
      "user_story_id": "US-001",
      "feature_ids": ["F-001"],
      "test_case_ids": ["TC-001", "TC-002"],
      "design_doc_id": "DES-001",
      "code_modules": ["module1.py"],
      "status": "draft|confirmed|implemented|verified"
    }
  ],
  "coverage_report": {
    "total_requirements": 10,
    "covered_by_tests": 8,
    "covered_by_design": 9,
    "coverage_percentage": 80.0
  }
}
```

#### 6. 可行性研究

**操作指南：**
- 技术可行性：评估技术实现难度
- 经济可行性：评估成本效益
- 时间可行性：评估交付周期
- 风险可行性：评估主要风险

#### 7. 需求优先级排序

**优先级评估矩阵：**
| 评估维度 | 权重 | 评分标准 |
|----------|------|----------|
| 业务价值 | 30% | 高(3)/中(2)/低(1) |
| 技术复杂度 | 20% | 低(3)/中(2)/高(1) |
| 依赖关系 | 20% | 无依赖(3)/弱依赖(2)/强依赖(1) |
| 风险程度 | 15% | 低风险(3)/中风险(2)/高风险(1) |
| 资源可用性 | 15% | 充足(3)/一般(2)/紧张(1) |

**优先级计算公式：**
```
优先级得分 = 业务价值×0.3 + 技术复杂度×0.2 + 依赖关系×0.2 + 风险程度×0.15 + 资源可用性×0.15
```

#### 8. 需求依赖分析

**依赖关系类型：**
| 依赖类型 | 说明 | 处理策略 |
|----------|------|----------|
| 强依赖 | 必须先完成前置需求 | 按顺序执行 |
| 弱依赖 | 前置需求影响实现方式 | 并行执行，后期调整 |
| 互斥依赖 | 与其他需求冲突 | 协商取舍 |
| 资源依赖 | 共享资源竞争 | 资源调度优化 |

**依赖图生成格式：**
```json
{
  "dependency_graph": {
    "nodes": [
      {"id": "REQ-001", "name": "需求名称", "priority_score": 8.5}
    ],
    "edges": [
      {"from": "REQ-001", "to": "REQ-002", "type": "strong", "reason": "依赖原因"}
    ]
  },
  "execution_order": ["REQ-001", "REQ-002", "REQ-003"],
  "parallel_groups": [
    ["REQ-002", "REQ-003"]
  ]
}
```

#### 9. 需求变更影响预评估

**变更影响评估维度：**
| 影响维度 | 评估内容 | 输出 |
|----------|----------|------|
| 代码影响 | 受影响的模块、类、方法 | 代码影响报告 |
| 测试影响 | 需要新增/修改的测试用例 | 测试影响报告 |
| 文档影响 | 需要更新的文档 | 文档更新清单 |
| 进度影响 | 对项目里程碑的影响 | 进度调整建议 |
| 成本影响 | 额外的开发成本 | 成本变更估算 |

**变更影响评估输出格式：**
```json
{
  "impact_assessment_id": "IA-001",
  "timestamp": "2024-01-01T00:00:00Z",
  "change_description": "变更描述",
  "impacts": {
    "code": {
      "affected_modules": ["module1", "module2"],
      "affected_files": 15,
      "estimated_effort_hours": 8
    },
    "test": {
      "new_tests_required": 5,
      "tests_to_modify": 3,
      "regression_risk": "medium"
    },
    "documentation": {
      "docs_to_update": ["API.md", "README.md"],
      "estimated_effort_hours": 2
    },
    "schedule": {
      "milestone_impact": "延期2天",
      "critical_path_affected": false
    },
    "cost": {
      "additional_hours": 10,
      "resource_impact": "需要额外前端资源"
    }
  },
  "recommendation": "建议采纳，需调整里程碑"
}
```

#### 10. 需求风险识别与缓解

**风险识别清单：**
| 风险类别 | 风险项 | 概率 | 影响 | 缓解措施 |
|----------|--------|------|------|----------|
| 技术风险 | 技术方案不可行 | 低 | 高 | 技术预研、POC验证 |
| 资源风险 | 关键人员离职 | 中 | 高 | 知识文档化、交叉培训 |
| 进度风险 | 需求蔓延 | 高 | 中 | 变更控制流程、优先级管理 |
| 外部风险 | 第三方服务不稳定 | 中 | 高 | 服务降级方案、备用服务 |

**风险缓解计划格式：**
```json
{
  "risk_plan_id": "RP-001",
  "risks": [
    {
      "risk_id": "R-001",
      "category": "技术风险",
      "description": "风险描述",
      "probability": "high|medium|low",
      "impact": "high|medium|low",
      "risk_score": 9,
      "mitigation_strategy": "缓解策略",
      "contingency_plan": "应急计划",
      "owner": "负责人",
      "status": "open|mitigating|closed"
    }
  ],
  "summary": {
    "total_risks": 5,
    "high_risks": 1,
    "medium_risks": 3,
    "low_risks": 1
  }
}
```

---

### 阶段二：项目规划流程

```
需求规格说明书
    ↓
[1] 任务分解（WBS）
    ↓
[2] 资源评估
    ↓
[3] 里程碑定义
    ↓
[4] 风险评估
    ↓
输出《项目计划书》
```

**操作指南：**
- 调用 `../subskills/xiangmu_guihua.md` 进行项目规划
- 生成任务分解清单（WBS）
- 定义里程碑和关键路径

---

### 阶段三：技术选型与架构设计流程

```
项目计划书
    ↓
[1] 技术栈调研
    ↓
[2] 技术选型决策
    ↓
[3] 概要设计
    ↓
[4] 系统架构设计
    ↓
[5] 架构评审准备
    ↓
输出《技术选型报告》《架构设计文档》
```

#### 技术选型指导

**选型维度：**
| 维度 | 评估内容 | 权重 |
|------|----------|------|
| 功能匹配度 | 是否满足功能需求 | 高 |
| 技术成熟度 | 社区活跃度、版本稳定性 | 高 |
| 团队熟悉度 | 团队技术储备 | 中 |
| 生态系统 | 周边工具、库支持 | 中 |
| 性能表现 | 基准测试结果 | 中 |
| 长期维护 | 维护成本、升级路径 | 中 |

**技术选型决策记录格式：**
```json
{
  "decision_id": "DEC-001",
  "decision_type": "技术选型",
  "options": [
    {
      "name": "选项A",
      "pros": ["优点1", "优点2"],
      "cons": ["缺点1", "缺点2"],
      "score": 85
    }
  ],
  "selected": "选项A",
  "reasoning": "选择理由",
  "risks": ["风险1", "风险2"]
}
```

#### 架构设计指导

**架构设计原则：**
| 原则 | 说明 | 应用建议 |
|------|------|----------|
| 单一职责 | 每个模块只负责一个功能 | 按业务领域划分模块 |
| 开闭原则 | 对扩展开放，对修改关闭 | 使用接口和抽象类 |
| 依赖倒置 | 依赖抽象而非具体实现 | 采用依赖注入 |
| 接口隔离 | 客户端不应依赖不需要的接口 | 接口粒度适中 |
| 最小知识 | 减少模块间的耦合 | 通过中间层通信 |

**架构设计输出要求：**
- 系统架构图（C4模型：上下文、容器、组件、代码）
- 模块划分及职责说明
- 接口定义（API契约）
- 数据流图
- 部署架构图

---

### 阶段四：测试策略规划流程

```
架构设计文档
    ↓
[1] 测试类型识别
    ↓
[2] 测试层次定义
    ↓
[3] 验收标准细化
    ↓
[4] 测试用例设计
    ↓
[5] 测试资源规划
    ↓
输出《测试策略文档》《验收测试用例》
```

**操作指南：**
- 调用 `../subskills/yan_shou_ceshi.md` 进行验收测试设计
- 确定测试类型分配（单元/集成/E2E）

**测试策略矩阵：**
| 测试类型 | 覆盖范围 | 目标覆盖率 | 负责部门 |
|----------|----------|------------|----------|
| 单元测试 | 函数/方法级别 | ≥80% | 工部 |
| 集成测试 | 模块间交互 | ≥70% | 工部 |
| E2E测试 | 端到端流程 | 核心流程100% | 兵部 |
| 性能测试 | 性能指标 | 关键指标100% | 兵部 |
| 安全测试 | 安全漏洞 | 高危漏洞0 | 兵部 |

---

### 阶段五：SDD 规范定义流程

```
架构设计文档
    ↓
[1] 实体定义
    ↓
[2] 接口定义
    ↓
[3] 业务规则定义
    ↓
[4] 约束条件定义
    ↓
[5] 规范验证
    ↓
[6] 代码骨架生成
    ↓
[7] 规范版本管理
    ↓
[8] 规范变更检测配置
    ↓
[9] 规范一致性校验
    ↓
[10] 规范文档自动生成
    ↓
输出《SDD规范文档》《代码骨架》
```

#### SDD 规范定义增强流程

**步骤1-6详见下文SDD规范解析能力**

#### 7. 规范版本管理

**版本管理策略：**
| 策略 | 说明 | 适用场景 |
|------|------|----------|
| 语义化版本 | MAJOR.MINOR.PATCH | 正式发布版本 |
| 时间戳版本 | YYYYMMDD.HHMMSS | 开发迭代版本 |
| 分支版本 | branch-name.timestamp | 并行开发版本 |

**版本兼容性规则：**
```yaml
version_compatibility:
  major_change:
    description: "破坏性变更，不兼容旧版本"
    examples:
      - "删除实体"
      - "修改接口签名"
      - "删除业务规则"
    action: "必须更新主版本号"
    
  minor_change:
    description: "新增功能，兼容旧版本"
    examples:
      - "新增实体"
      - "新增接口方法"
      - "新增业务规则"
    action: "更新次版本号"
    
  patch_change:
    description: "修复问题，完全兼容"
    examples:
      - "修复约束条件"
      - "优化描述"
      - "修正错误"
    action: "更新修订号"
```

#### 8. 规范变更检测配置

**变更检测配置：**
```yaml
change_detection:
  triggers:
    - type: "file_modified"
      patterns: ["**/*.spec.json", "**/SDD_*.json"]
    - type: "scheduled"
      interval: "daily"
    - type: "manual"
      
  detection_scope:
    - "entity_definitions"
    - "interface_contracts"
    - "business_rules"
    - "constraints"
    - "validation_rules"
    
  impact_analysis:
    enabled: true
    analyze_code_impact: true
    analyze_test_impact: true
    generate_migration_guide: true
    
  notifications:
    on_breaking_change: ["zhongshusheng", "menxiasheng", "shangshusheng"]
    on_minor_change: ["shangshusheng"]
    channels: ["log", "callback", "webhook"]
```

**变更检测输出：**
```json
{
  "detection_id": "DET-001",
  "timestamp": "2024-01-01T00:00:00Z",
  "changes": [
    {
      "change_type": "entity_modified",
      "target": "User",
      "description": "添加了新属性 phone",
      "impact_level": "minor",
      "affected_files": ["models/user.py", "services/user_service.py"],
      "affected_tests": ["tests/test_user.py"],
      "migration_required": false,
      "auto_fixable": true
    }
  ],
  "summary": {
    "total_changes": 1,
    "breaking_changes": 0,
    "minor_changes": 1,
    "patch_changes": 0
  },
  "recommendations": [
    {
      "type": "update_code",
      "description": "更新User模型添加phone属性",
      "priority": "medium"
    },
    {
      "type": "update_tests",
      "description": "添加phone属性的测试用例",
      "priority": "medium"
    }
  ]
}
```

#### 9. 规范一致性校验

**一致性校验维度：**
| 校验维度 | 校验内容 | 错误级别 |
|----------|----------|----------|
| 实体一致性 | 实体定义与数据库模型一致 | 错误 |
| 接口一致性 | 接口定义与实现一致 | 错误 |
| 规则一致性 | 业务规则与代码逻辑一致 | 警告 |
| 约束一致性 | 约束条件与验证逻辑一致 | 错误 |
| 命名一致性 | 命名规范统一 | 警告 |

**一致性校验输出格式：**
```json
{
  "consistency_check_id": "CC-001",
  "timestamp": "2024-01-01T00:00:00Z",
  "check_results": [
    {
      "dimension": "entity_consistency",
      "status": "pass|fail|warning",
      "details": [
        {
          "item": "User实体",
          "check": "属性数量匹配",
          "expected": 5,
          "actual": 5,
          "status": "pass"
        },
        {
          "item": "User实体",
          "check": "属性类型匹配",
          "field": "email",
          "expected": "string",
          "actual": "varchar",
          "status": "pass",
          "note": "类型映射正确"
        }
      ]
    }
  ],
  "summary": {
    "total_checks": 15,
    "passed": 13,
    "warnings": 1,
    "errors": 1
  },
  "recommendations": [
    {
      "type": "fix_required",
      "description": "Order实体缺少status字段定义",
      "priority": "high"
    }
  ]
}
```

#### 10. 规范文档自动生成

**文档生成配置：**
```yaml
document_generation:
  templates:
    - name: "API文档"
      template: "api_doc_template.md"
      output: "docs/api/"
    - name: "数据模型文档"
      template: "data_model_template.md"
      output: "docs/data/"
    - name: "业务规则文档"
      template: "business_rules_template.md"
      output: "docs/business/"
  
  formats:
    - markdown
    - html
    - pdf
  
  include_diagrams: true
  diagram_types:
    - er_diagram
    - class_diagram
    - sequence_diagram
    - flowchart
```

**文档生成输出：**
```json
{
  "generation_id": "GEN-001",
  "timestamp": "2024-01-01T00:00:00Z",
  "generated_documents": [
    {
      "type": "API文档",
      "path": "docs/api/index.md",
      "sections": ["概述", "认证", "接口列表", "错误码"],
      "word_count": 2500
    },
    {
      "type": "数据模型文档",
      "path": "docs/data/models.md",
      "diagrams": ["ER图", "类图"],
      "word_count": 1800
    }
  ],
  "diagrams_generated": [
    {
      "type": "er_diagram",
      "format": "plantuml",
      "path": "docs/diagrams/er.puml"
    }
  ],
  "summary": {
    "total_documents": 3,
    "total_diagrams": 2,
    "generation_time_ms": 1500
  }
}
```

#### SDD 规范解析能力

**调用子技能：**
- 调用 `../subskills/sdd_liucheng.md` 进行 SDD 流程
- 调用 `../subskills/guifan_jiexi.md` 进行规范解析

**SDD 规范输出格式：**
```json
{
  "spec_id": "SPEC-001",
  "version": "1.0.0",
  "parsed_at": "2024-01-01T00:00:00Z",
  "entities": [
    {
      "id": "ENT-001",
      "name": "实体名称",
      "type": "aggregate|entity|value_object",
      "attributes": [
        {
          "name": "属性名",
          "type": "数据类型",
          "required": true,
          "validation": {"rule": "验证规则"}
        }
      ],
      "behaviors": [
        {
          "name": "行为名称",
          "description": "行为描述",
          "parameters": [],
          "return_type": "返回类型"
        }
      ]
    }
  ],
  "interfaces": [
    {
      "id": "INT-001",
      "name": "接口名称",
      "type": "api|repository|service",
      "methods": [
        {
          "name": "方法名",
          "http_method": "GET|POST|PUT|DELETE",
          "path": "/api/path",
          "parameters": [],
          "return_type": "返回类型",
          "error_handling": "错误处理策略"
        }
      ]
    }
  ],
  "business_rules": [
    {
      "id": "BR-001",
      "name": "规则名称",
      "description": "规则描述",
      "condition": "触发条件",
      "action": "执行动作",
      "priority": "high|medium|low",
      "scope": "global|entity|process"
    }
  ],
  "constraints": [
    {
      "id": "CON-001",
      "type": "technical|business|regulatory",
      "description": "约束描述",
      "impact": "影响范围"
    }
  ]
}
```

#### 代码骨架生成

**生成规则：**
| 规则 | 说明 |
|------|------|
| 目录结构生成 | 根据实体和模块自动生成项目目录 |
| 文件命名规范 | 遵循项目约定的命名规范 |
| 代码模板应用 | 使用预定义模板生成基础代码框架 |
| 依赖注入配置 | 自动配置依赖注入和模块引用 |
| 接口占位符 | 为每个接口生成方法签名和 TODO 注释 |

**骨架输出示例：**
```
project/
├── src/
│   ├── entities/
│   │   └── {entity_name}.ts      # 实体定义
│   ├── interfaces/
│   │   └── {interface_name}.ts   # 接口定义
│   ├── services/
│   │   └── {service_name}.ts     # 服务层
│   ├── repositories/
│   │   └── {repository_name}.ts  # 数据访问层
│   └── config/
│       └── index.ts              # 配置文件
├── tests/
│   └── {module}_test.ts          # 测试文件
└── docs/
    └── api.md                    # API 文档
```

---

### 阶段六：外部技能发现流程

```
需求规格说明书
    ↓
[1] 技能需求分析
    ↓
[2] 技能目录扫描
    ↓
[3] 匹配度评估
    ↓
[4] 推荐列表生成
    ↓
输出《外部技能推荐列表》
```

**操作指南：**
- 扫描 `.trae/skills/` 目录下的外部技能
- 评估外部技能与需求的匹配度
- 输出外部技能推荐列表

---

### 阶段七：决策记录与移交

```
所有产出物
    ↓
[1] 决策过程记录
    ↓
[2] 产出物整理
    ↓
[3] 质量自检
    ↓
[4] 移交门下省审议
    ↓
完成
```

**操作指南：**
- 调用 `../scripts/record_skill_call.py` 记录决策过程
- 确保所有产出物完整
- 移交门下省审议

---

## 协作说明

### 与门下省的协作

| 协作点 | 协作内容 | 交付物 |
|--------|----------|--------|
| 方案移交 | 将完整方案移交门下省审议 | 全套产出物 |
| 审议反馈 | 接收并处理审议意见 | 修改后的方案 |
| 规范验证 | 配合门下省进行规范一致性验证 | 补充材料 |

### 与尚书省的协作

| 协作点 | 协作内容 | 交付物 |
|--------|----------|--------|
| 执行计划 | 提供执行所需的设计文档和规范 | 技术文档包 |
| 规范解释 | 解答执行过程中的规范问题 | 规范说明 |
| 变更处理 | 处理执行阶段发现的规范问题 | 规范变更 |

---

## 透明度记录要求

### 需求分析阶段透明度记录

**必须记录：**
- **需求理解推理过程**：如何从用户描述中提取核心需求
- **隐含需求推断**：基于经验推断的隐含需求及依据
- **需求优先级判断依据**：优先级排序的决策依据

### 设计阶段透明度记录

**必须记录：**
- **设计决策依据**：每个关键设计决策的输入条件、约束因素、决策理由
- **技术选型理由**：技术栈选择的比较分析
- **备选方案及放弃原因**：被否决的备选方案记录

### 透明度输出格式
```json
{
  "timestamp": "决策时间戳",
  "phase": "需求分析|设计阶段",
  "decision_type": "决策类型",
  "input": {
    "context": "决策上下文",
    "constraints": ["约束条件列表"]
  },
  "reasoning": {
    "analysis": "推理分析过程",
    "factors": ["影响因素列表"],
    "assumptions": ["假设条件列表"]
  },
  "alternatives": [
    {
      "option": "备选方案描述",
      "pros": ["优点"],
      "cons": ["缺点"],
      "rejected_reason": "放弃原因"
    }
  ],
  "decision": {
    "conclusion": "最终决策",
    "confidence": "置信度（高/中/低）",
    "risks": ["风险列表"]
  }
}
```

---

## 规范变更检测能力

### 变更检测机制

| 机制 | 说明 |
|------|------|
| 版本对比 | 对比新旧版本规范，识别变更点 |
| 影响分析 | 分析变更对现有代码的影响范围 |
| 变更分类 | 将变更分为破坏性变更、兼容性变更、新增功能 |
| 迁移建议 | 生成变更迁移指南和代码修改建议 |

### 变更检测输出格式
```json
{
  "change_id": "CHG-001",
  "detected_at": "检测时间戳",
  "changes": [
    {
      "type": "entity_added|entity_modified|entity_removed|interface_changed|rule_updated",
      "target": "变更目标",
      "description": "变更描述",
      "impact_level": "breaking|compatible|minor",
      "affected_files": ["受影响文件列表"],
      "migration_guide": "迁移指南",
      "auto_fixable": true
    }
  ],
  "summary": {
    "total_changes": 5,
    "breaking_changes": 1,
    "compatible_changes": 3,
    "minor_changes": 1
  }
}
```

---

## 输出物清单

| 输出物 | 格式 | 移交对象 |
|--------|------|----------|
| 需求规格说明书（SRS） | Markdown | 门下省 |
| 结构化需求文档 | JSON | 门下省 |
| 澄清问题列表 | JSON | 门下省 |
| 需求确认记录 | JSON | 门下省 |
| 需求追踪矩阵 | JSON | 门下省、尚书省 |
| 项目计划书 | Markdown | 门下省 |
| 任务分解清单 | Markdown/JSON | 尚书省 |
| 里程碑计划 | Markdown | 尚书省 |
| 技术选型报告 | Markdown | 门下省 |
| 架构设计文档 | Markdown | 门下省、尚书省 |
| 系统架构图 | 图片/PlantUML | 门下省、尚书省 |
| 测试策略文档 | Markdown | 门下省、兵部 |
| 验收测试用例 | Markdown/JSON | 兵部 |
| 外部技能推荐列表 | JSON | 尚书省 |
| 决策日志文件 | decision_log.json | 门下省 |
| SDD 规范文档 | JSON | 门下省、尚书省 |
| 代码骨架 | 代码文件 | 尚书省 |

---

## 协同调用接口

### 接口定义

中书省作为决策中枢，提供以下协同调用接口供其他技能调用：

| 接口名称 | 接口描述 | 调用方 |
|----------|----------|--------|
| `analyze_requirements` | 需求分析接口 | 外部技能、尚书省 |
| `create_project_plan` | 项目规划接口 | 尚书省 |
| `design_architecture` | 架构设计接口 | 工部 |
| `define_sdd_spec` | SDD规范定义接口 | 礼部、工部 |
| `discover_external_skills` | 外部技能发现接口 | 尚书省 |

### 输入参数规范

#### 需求分析接口参数

```json
{
  "interface": "analyze_requirements",
  "version": "1.0.0",
  "timestamp": "2024-01-01T00:00:00Z",
  "caller": "调用方标识",
  "parameters": {
    "requirement_text": "用户需求描述文本",
    "context": {
      "project_type": "web|mobile|api|desktop",
      "domain": "业务领域",
      "constraints": ["约束条件列表"]
    },
    "options": {
      "detail_level": "high|medium|low",
      "output_format": "json|markdown"
    }
  }
}
```

#### 项目规划接口参数

```json
{
  "interface": "create_project_plan",
  "version": "1.0.0",
  "timestamp": "2024-01-01T00:00:00Z",
  "caller": "调用方标识",
  "parameters": {
    "requirement_doc_id": "需求文档ID",
    "constraints": {
      "deadline": "截止日期",
      "budget": "预算限制",
      "team_size": "团队规模"
    },
    "milestones": [
      {
        "name": "里程碑名称",
        "target_date": "目标日期"
      }
    ]
  }
}
```

#### 架构设计接口参数

```json
{
  "interface": "design_architecture",
  "version": "1.0.0",
  "timestamp": "2024-01-01T00:00:00Z",
  "caller": "调用方标识",
  "parameters": {
    "project_plan_id": "项目计划ID",
    "tech_stack_preferences": ["技术栈偏好"],
    "architecture_style": "monolith|microservice|serverless",
    "quality_attributes": {
      "performance": "high|medium|low",
      "scalability": "high|medium|low",
      "security": "high|medium|low"
    }
  }
}
```

### 输出格式规范

#### 标准响应格式

```json
{
  "interface": "接口名称",
  "call_id": "CALL-001",
  "timestamp": "2024-01-01T00:00:00Z",
  "status": "success|failure|partial",
  "result": {
    "output_type": "文档类型",
    "content": "输出内容",
    "artifacts": ["产出物列表"]
  },
  "metrics": {
    "execution_time_ms": 5000,
    "token_usage": 1500
  },
  "errors": [
    {
      "code": "错误码",
      "message": "错误信息",
      "severity": "critical|major|minor"
    }
  ]
}
```

### 调用示例

#### 示例1：需求分析调用

```bash
# 调用需求分析接口
调用 ./SKILL.md --interface=analyze_requirements \
  --requirement-text="构建一个电商平台" \
  --context='{"project_type":"web","domain":"ecommerce"}' \
  --output-format=json
```

#### 示例2：架构设计调用

```bash
# 调用架构设计接口
调用 ./SKILL.md --interface=design_architecture \
  --project-plan-id="PLAN-001" \
  --architecture-style="microservice" \
  --output-path="docs/architecture/"
```

### 协同回调接口

中书省在完成决策后，会通过以下回调接口通知相关技能：

| 回调接口 | 触发时机 | 回调目标 |
|----------|----------|----------|
| `on_decision_complete` | 决策完成时 | 门下省 |
| `on_spec_defined` | 规范定义完成时 | 礼部、工部 |
| `on_external_skill_needed` | 需要外部技能时 | 尚书省 |

#### 回调数据格式

```json
{
  "callback": "on_decision_complete",
  "call_id": "CALL-001",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "decision_type": "技术选型|架构设计|项目立项",
    "decision_result": "决策结果",
    "deliverables": ["交付物列表"],
    "next_steps": ["后续步骤"]
  }
}
```

---

## 子技能引用

| 子技能 | 用途 |
|--------|------|
| [需求分析](../subskills/xuqiu_fenxi.md) | 需求收集与分析 |
| [需求结构化](../subskills/xuqiu_jiegouhua.md) | 需求白盒化结构化 |
| [项目规划](../subskills/xiangmu_guihua.md) | 项目计划制定 |
| [系统设计](../subskills/xitong_sheji.md) | 详细系统设计 |
| [验收测试](../subskills/yan_shou_ceshi.md) | 验收测试设计 |
| [SDD流程](../subskills/sdd_liucheng.md) | SDD规范流程 |
| [规范解析](../subskills/guifan_jiexi.md) | 规范解析处理 |

---

## 协同效果评估能力

### 协同评估指标

中书省作为决策中枢，负责评估三省六部协同效果，确保决策执行的一致性和效率。

| 评估维度 | 指标 | 目标值 | 度量方法 |
|----------|------|--------|----------|
| 决策执行率 | 决策被正确执行的比例 | ≥95% | 执行结果与决策对比 |
| 协调效率 | 三省协调平均耗时 | ≤30分钟 | 时间戳差值统计 |
| 规范一致性 | 代码与规范一致率 | ≥90% | 自动化校验 |
| 需求覆盖率 | 需求被测试覆盖的比例 | ≥85% | 追踪矩阵分析 |
| 决策质量分 | 决策正确性和完整性评分 | ≥0.85 | 综合评分算法 |

### 协同评估流程

```
[1] 收集执行数据
    ↓
[2] 计算协同指标
    ↓
[3] 分析协同瓶颈
    ↓
[4] 生成优化建议
    ↓
[5] 反馈至相关部门
    ↓
输出《协同效果评估报告》
```

### 协同评估报告格式

```json
{
  "evaluation_id": "EVAL-001",
  "timestamp": "2024-01-01T00:00:00Z",
  "period": {
    "start": "2024-01-01T00:00:00Z",
    "end": "2024-01-07T23:59:59Z"
  },
  "province_performance": {
    "zhongshusheng": {
      "decision_count": 15,
      "decision_success_rate": 0.93,
      "avg_decision_time_minutes": 25,
      "quality_score": 0.88
    },
    "menxiasheng": {
      "review_count": 15,
      "approval_rate": 0.87,
      "avg_review_time_minutes": 18,
      "quality_score": 0.90
    },
    "shangshusheng": {
      "execution_count": 15,
      "execution_success_rate": 0.91,
      "avg_execution_time_hours": 4.5,
      "quality_score": 0.85
    }
  },
  "ministry_performance": {
    "libu": {"task_count": 10, "success_rate": 0.95},
    "hubu": {"task_count": 8, "success_rate": 0.92},
    "liibu": {"task_count": 12, "success_rate": 0.88},
    "bingbu": {"task_count": 15, "success_rate": 0.93},
    "xingbu": {"task_count": 9, "success_rate": 0.90},
    "gongbu": {"task_count": 20, "success_rate": 0.87}
  },
  "overall_metrics": {
    "coordination_efficiency": 0.89,
    "quality_score": 0.87,
    "resource_utilization": 0.82,
    "task_success_rate": 0.91
  },
  "bottlenecks": [
    {
      "type": "review_delay",
      "location": "menxiasheng",
      "description": "审议环节平均耗时偏长",
      "impact": "medium",
      "suggestion": "优化审议流程，引入并行审议机制"
    }
  ],
  "recommendations": [
    {
      "category": "process_optimization",
      "priority": "high",
      "description": "简化三省协调路径",
      "expected_impact": "预计协调效率提升20%"
    }
  ]
}
```

---

## 流水线协调能力

### 白盒化7阶段流水线

中书省负责定义和管理白盒化7阶段流水线，确保开发流程透明可控。

| 阶段 | 名称 | 负责省/部 | 输入 | 输出 | 质量门禁 |
|------|------|-----------|------|------|----------|
| 1 | 需求分析 | 中书省 | 用户需求 | 需求文档 | 需求完整性≥90% |
| 2 | SDD规范定义 | 中书省 | 需求文档 | SDD规范 | 规范覆盖率≥85% |
| 3 | 审议批准 | 门下省 | SDD规范 | 审批决定 | 审议通过率≥80% |
| 4 | 测试先行 | 兵部 | SDD规范 | 测试用例 | 测试覆盖率≥80% |
| 5 | 代码实现 | 工部 | 测试用例 | 实现代码 | 测试通过率=100% |
| 6 | 持续重构 | 刑部 | 实现代码 | 优化代码 | 质量指标提升≥10% |
| 7 | 部署发布 | 工部 | 优化代码 | 部署产物 | 部署成功率=100% |

### 流水线状态监控

```json
{
  "pipeline_id": "PIPE-001",
  "task_id": "TASK-001",
  "status": "running",
  "current_stage": "implementation",
  "progress": 0.57,
  "stages": [
    {
      "stage": "requirement_analysis",
      "status": "completed",
      "duration_seconds": 1800,
      "quality_score": 0.92
    },
    {
      "stage": "sdd_specification",
      "status": "completed",
      "duration_seconds": 2400,
      "quality_score": 0.88
    },
    {
      "stage": "review_approval",
      "status": "completed",
      "duration_seconds": 1200,
      "quality_score": 0.90
    },
    {
      "stage": "test_first",
      "status": "completed",
      "duration_seconds": 3600,
      "quality_score": 0.85
    },
    {
      "stage": "implementation",
      "status": "running",
      "started_at": "2024-01-01T14:00:00Z",
      "estimated_remaining_seconds": 1800
    },
    {
      "stage": "refactoring",
      "status": "pending"
    },
    {
      "stage": "deployment",
      "status": "pending"
    }
  ],
  "estimated_completion": "2024-01-01T18:00:00Z"
}
```

### 流水线异常处理

| 异常类型 | 处理策略 | 负责实体 |
|----------|----------|----------|
| 阶段超时 | 自动升级通知 | 中书省 |
| 质量门禁失败 | 阻断并回退 | 门下省 |
| 依赖阻塞 | 重新调度 | 尚书省 |
| 资源不足 | 动态调配 | 户部 |

---

## 智能决策支持

### 决策辅助算法

中书省采用智能算法辅助决策，提高决策质量和效率。

#### 优先级决策算法

```python
def calculate_priority(requirement):
    weights = {
        "business_value": 0.30,
        "technical_complexity": 0.20,
        "dependency": 0.20,
        "risk": 0.15,
        "resource_availability": 0.15
    }
    
    scores = {
        "business_value": evaluate_business_value(requirement),
        "technical_complexity": evaluate_complexity(requirement),
        "dependency": evaluate_dependency(requirement),
        "risk": evaluate_risk(requirement),
        "resource_availability": evaluate_resources(requirement)
    }
    
    return sum(scores[k] * weights[k] for k in weights)
```

#### 技术选型决策矩阵

| 评估维度 | 权重 | 选项A得分 | 选项B得分 | 选项C得分 |
|----------|------|-----------|-----------|-----------|
| 功能匹配度 | 30% | 9 | 8 | 7 |
| 技术成熟度 | 25% | 8 | 9 | 6 |
| 团队熟悉度 | 20% | 7 | 6 | 9 |
| 生态系统 | 15% | 8 | 7 | 8 |
| 长期维护 | 10% | 7 | 8 | 7 |
| **加权总分** | - | **7.95** | **7.65** | **7.35** |

### 决策记录追溯

所有决策均记录完整的推理链，支持追溯和审计。

```json
{
  "decision_id": "DEC-001",
  "timestamp": "2024-01-01T00:00:00Z",
  "decision_type": "技术选型",
  "context": {
    "requirement_id": "REQ-001",
    "constraints": ["性能要求高", "团队熟悉React"],
    "stakeholders": ["产品经理", "技术负责人"]
  },
  "reasoning_chain": [
    {
      "step": 1,
      "type": "analysis",
      "content": "分析需求的技术要求",
      "output": "需要高性能前端框架"
    },
    {
      "step": 2,
      "type": "evaluation",
      "content": "评估候选方案",
      "output": "React、Vue、Angular三个候选"
    },
    {
      "step": 3,
      "type": "comparison",
      "content": "对比分析各方案优劣",
      "output": "React在团队熟悉度和生态上占优"
    },
    {
      "step": 4,
      "type": "decision",
      "content": "最终决策",
      "output": "选择React作为前端框架"
    }
  ],
  "decision": {
    "selected": "React",
    "confidence": 0.85,
    "risks": ["学习曲线", "版本升级"]
  },
  "alternatives": [
    {
      "option": "Vue",
      "rejected_reason": "团队熟悉度较低"
    },
    {
      "option": "Angular",
      "rejected_reason": "过于重量级"
    }
  ]
}
```

---

## 增强功能集成

### 与provincial_coordinator集成

中书省通过provincial_coordinator.py实现与其他省部的协同：

```python
from scripts.provincial_coordinator import (
    ProvincialCoordinator,
    SmartDispatcher,
    PipelineManager,
    CoordinationEvaluator
)

coordinator = ProvincialCoordinator()
dispatcher = SmartDispatcher()
pipeline_manager = PipelineManager()
evaluator = CoordinationEvaluator()

task = coordinator.create_task(
    task_type="feature",
    description="实现用户认证功能",
    priority="high"
)

result = coordinator.coordinate_provinces(task)

pipeline = pipeline_manager.create_pipeline(task.task_id)
pipeline_manager.start_pipeline(pipeline.pipeline_id)

evaluation = evaluator.evaluate_coordination(
    list(coordinator.tasks.values()),
    list(analyzer.results.values())
)
```

### 智能分发集成

```python
requirement = TaskRequirement(
    task_id="TASK-001",
    required_capabilities={
        "code_implementation": 0.9,
        "feature_development": 0.85
    },
    preferred_specializations=["gongbu"],
    priority=TaskPriority.HIGH
)

decision = dispatcher.find_best_match(requirement, "ministry")
print(f"最佳匹配: {decision.assigned_entity}")
print(f"综合得分: {decision.overall_score}")
```

---

## 决策质量保障

### 决策质量检查清单

```
□ 决策依据充分，有数据支撑
□ 备选方案已充分评估
□ 风险已识别并有缓解措施
□ 决策过程已完整记录
□ 相关方已确认或通知
□ 决策可追溯、可审计
□ 决策与规范一致
□ 决策可实现、可验证
```

### 决策质量评分

| 评分项 | 权重 | 评分标准 |
|--------|------|----------|
| 依据充分性 | 25% | 有充分的数据和分析支撑 |
| 方案完整性 | 20% | 考虑了所有可行方案 |
| 风险识别度 | 20% | 识别了主要风险并有应对 |
| 可执行性 | 20% | 决策具体、可操作 |
| 可追溯性 | 15% | 决策过程完整记录 |

---

## v2.4.0 新增能力

### 需求追溯管理系统增强

v2.4.0 版本新增完整的需求追溯管理系统，提供需求到代码的双向追溯能力：

| 新增脚本 | 功能描述 |
|----------|----------|
| `requirement_trace_manager.py` | 需求追溯链管理，支持需求-设计-代码-测试双向追溯 |
| `requirement_change_impact_analyzer.py` | 需求变更影响分析，自动评估变更影响范围 |
| `trace_matrix_visualizer.py` | 追溯矩阵可视化，生成追溯关系图表 |
| `trace_report_generator.py` | 追溯报告生成，输出追溯分析报告 |

### 规范解析增强

新增增强版规范解析器 `sdd_spec_parser_enhanced.py`，提供：

- 更强大的规范解析能力
- 支持复杂嵌套结构解析
- 自动生成API文档
- 规范一致性自动校验

### 智能决策支持增强

新增智能决策支持能力：

```bash
# 需求变更影响分析
python skillscripts/requirements/requirement_change_impact_analyzer.py \
  --requirement-id REQ-001 \
  --change-type modify \
  --output impact_report.md

# 生成追溯矩阵
python skillscripts/requirements/trace_matrix_visualizer.py \
  --project-root ./ \
  --output docs/trace_matrix.html
```

### 版本历史

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| 2.3.0 | 2026-03-30 | 新增协同效果评估、流水线协调、智能决策支持能力 |
| 2.4.0 | 2026-03-30 | 新增需求追溯管理系统、增强版规范解析器、智能决策支持增强 |
| 2.7.1 | 2026-03-31 | 新增目录创建策略说明、路径配置管理集成 |

---

## 目录创建策略

### 中书省目录管理

中书省作为决策中枢，在产出文档时遵循**按需创建目录**原则：

| 产出物 | 存储目录 | 创建时机 |
|--------|----------|----------|
| 需求规格说明书 | `docs/workflow/requirements/` | 需求分析完成时 |
| 架构设计文档 | `docs/workflow/design/` | 架构设计完成时 |
| SDD规范文档 | `docs/workflow/specification/` | 规范定义完成时 |
| 决策日志 | `docs/workflow/decisions/` | 决策记录时 |

### 路径配置

```yaml
zhongshusheng_paths:
  output_base: "docs/workflow/"
  requirement_docs: "docs/workflow/requirements/"
  architecture_docs: "docs/workflow/design/"
  sdd_specs: "docs/workflow/specification/"
  decision_logs: "docs/workflow/decisions/"
```

### 目录创建命令

```bash
# 通过路径配置管理器创建目录
python skillscripts/utils/path_config_manager.py create --type requirement
python skillscripts/utils/path_config_manager.py create --type design
```
