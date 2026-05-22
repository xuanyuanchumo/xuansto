---
name: jingtaifenxi_si
description: 静态分析司，负责代码复杂度分析、代码重复检测、代码异味识别。集成四维防线第3层RuleValidationLayer的编码规范检查子模块。
---

# 静态分析司技能指令

## 职责定义

静态分析司作为代码审查局的核心司，承担以下职责：

| 职责类别 | 具体职责 | 关键产出 |
|----------|----------|----------|
| **复杂度分析** | 圈复杂度、认知复杂度、耦合度分析 | 复杂度报告 |
| **重复检测** | 代码块相似性检测、重复率统计 | 重复报告 |
| **异味识别** | 代码反模式、设计问题识别 | 异味清单 |
| **规范检查** | 编码规范合规性检查 | 规范检查报告 |

---

## 工具集成

### 核心工具链

| 工具 | 用途 | 语言支持 |
|------|------|----------|
| **Pylint** | Python代码质量检查 | Python |
| **ESLint** | JavaScript/TypeScript代码质量检查 | JS/TS |
| **SonarQube** | 综合代码质量平台 | 多语言 |
| **Radon** | Python复杂度计算 | Python |
| **JSCPD** | 代码重复检测 | 多语言 |

### 四维防线第3层集成

```yaml
four_dimensional_defense:
  layer: 3
  component: "RuleValidationLayer"
  submodule: "coding_standards_check"

integration_points:
  - name: "complexity_validation"
    description: "代码复杂度阈值验证"
    trigger: "代码提交时自动触发"
    threshold:
      cyclomatic_complexity: 10
      cognitive_complexity: 15
      coupling_degree: 5

  - name: "duplication_detection"
    description: "代码重复检测"
    trigger: "PR创建时自动触发"
    threshold:
      duplication_percentage: 5
      similarity_threshold: 0.8
      minimum_lines: 5

  - name: "code_smell_detection"
    description: "代码异味识别"
    trigger: "持续集成时触发"
    categories:
      - "长方法"
      - "大类"
      - "特征 envy"
      - "数据泥团"
```

---

## 工作流程

### 阶段一：代码接收与预处理

```
代码提交/PR创建
    ↓
[1] 代码文件收集
    ↓
[2] 文件类型识别
    ↓
[3] 工具配置加载
    ↓
进入分析阶段
```

#### 1. 代码文件收集

**收集范围：**
- 新增和修改的文件（增量分析）
- 全量代码库（全量分析）
- 指定目录或文件（定向分析）

#### 2. 文件类型识别

**支持的文件类型：**
| 类型 | 扩展名 | 分析工具 |
|------|--------|----------|
| Python | .py | Pylint, Radon, Bandit |
| JavaScript | .js | ESLint, JSCPD |
| TypeScript | .ts, .tsx | ESLint, TSLint |
| Java | .java | SonarQube, PMD |
| Go | .go | golint, staticcheck |

---

### 阶段二：复杂度分析流程

```
预处理完成
    ↓
[1] 圈复杂度计算
    ↓
[2] 认知复杂度评估
    ↓
[3] 耦合度分析
    ↓
[4] 内聚度计算
    ↓
[5] 复杂度趋势对比
    ↓
输出复杂度分析报告
```

#### 圈复杂度分析标准

| 复杂度等级 | 分数范围 | 状态 | 处理建议 |
|------------|----------|------|----------|
| 优秀 | 1-5 | ✅ 通过 | 维持现状 |
| 良好 | 6-10 | ⚠️ 警告 | 建议优化 |
| 较差 | 11-20 | ❌ 不通过 | 必须重构 |
| 不可接受 | >20 | 🔴 严重 | 立即重构 |

**圈复杂度输出格式：**
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
          "status": "pass",
          "line_range": [45, 80]
        },
        {
          "name": "validate_user",
          "value": 12,
          "status": "fail",
          "line_range": [85, 120],
          "recommendation": "建议拆分为多个小函数"
        }
      ]
    },
    "cognitive_complexity": {
      "value": 14,
      "threshold": 15,
      "status": "pass"
    }
  },
  "overall_status": "conditional_pass"
}
```

#### 认知复杂度分析维度

| 维度 | 描述 | 权重 |
|------|------|------|
| **嵌套深度** | 代码嵌套层级 | 高 |
| **结构化跳转** | break/continue使用 | 中 |
| **逻辑运算符** | &&/\|\|嵌套 | 低 |
| **递归调用** | 函数自身调用 | 高 |

---

### 阶段三：代码重复检测流程

```
复杂度分析完成
    ↓
[1] Token序列提取
    ↓
[2] 相似度计算
    ↓
[3] 重复块聚类
    ↓
[4] 重复位置定位
    ↓
[5] 重构建议生成
    ↓
输出重复检测报告
```

#### 重复检测配置

```yaml
duplication_config:
  minimum_tokens: 50
  minimum_lines: 5
  ignore_patterns:
    - "tests/**"
    - "**/*.min.js"
    - "**/generated/**"
    - "**/migrations/**"
    
  similarity_threshold: 0.8
  
  reporting:
    include_snippets: true
    max_snippet_lines: 10
    group_similar: true
```

#### 重复检测报告格式

```json
{
  "detection_id": "DUP-001",
  "timestamp": "2024-01-01T00:00:00Z",
  "scope": {
    "repository": "project-name",
    "branch": "main",
    "files_analyzed": 150
  },
  "duplications": [
    {
      "id": "DUP-BLOCK-001",
      "similarity": 0.95,
      "lines_count": 25,
      "tokens_count": 180,
      "locations": [
        {
          "file": "src/services/user_service.py",
          "start_line": 45,
          "end_line": 69
        },
        {
          "file": "src/services/admin_service.py",
          "start_line": 30,
          "end_line": 54
        }
      ],
      "suggested_refactoring": "提取公共方法到base_service.py",
      "estimated_savings": "减少15行重复代码"
    }
  ],
  "summary": {
    "total_duplications": 3,
    "total_duplicated_lines": 65,
    "duplication_percentage": 2.8,
    "status": "warning"
  },
  "recommendations": [
    "优先处理相似度>90%的重复块",
    "考虑使用模板方法模式消除重复",
    "建立公共工具类库"
  ]
}
```

---

### 阶段四：代码异味识别流程

```
重复检测完成
    ↓
[1] 反模式匹配
    ↓
[2] 设计问题识别
    ↓
[3] 异味分类定级
    ↓
[4] 影响范围评估
    ↓
[5] 修复方案推荐
    ↓
输出异味识别报告
```

#### 支持的代码异味类型

| 类别 | 异味名称 | 严重级别 | 检测规则 |
|------|----------|----------|----------|
| **过长** | Long Method | Medium | 方法行数>50行 |
| **过大** | Large Class | High | 类行数>500行 |
| **过长参数** | Long Parameter List | Medium | 参数数量>5个 |
| **特征envy** | Feature Envy | High | 过多访问其他类属性 |
| **数据泥团** | Data Clumps | Medium | 总是一起出现的数据组 |
| **发散式变化** | Divergent Change | High | 一个类因多种原因变化 |
| **散弹式修改** | Shotgun Surgery | Medium | 修改需要改动多个类 |
| **平行继承体系** | Parallel Inheritance | Low | 平行的继承层次结构 |
| **惰性类** | Lazy Class | Low | 功能过少的类 |
| **投机性泛化** | Speculative Generality | Medium | 不必要的抽象 |
| **令人迷惑的临时字段** | Temporary Field | Medium | 仅在特定情况下使用的字段 |
| **中间人** | Middle Man | Low | 过多的委托方法 |
| **过度亲密** | Inappropriate Intimacy | Medium | 过度依赖实现细节 |
| **拒绝遗赠** | Refused Bequest | Low | 子类重写大部分父类方法 |
| **注释** | Comments | Info | 注释过多说明代码不清晰 |

#### 代码异味检测配置

```yaml
code_smell_config:
  detection_rules:
    long_method:
      enabled: true
      threshold_lines: 50
      severity: "medium"
      
    large_class:
      enabled: true
      threshold_lines: 500
      severity: "high"
      
    long_parameter_list:
      enabled: true
      threshold_params: 5
      severity: "medium"
      
    feature_envy:
      enabled: true
      threshold_accesses: 10
      severity: "high"
      
  ignore_patterns:
    - "tests/**"
    - "**/*_test.py"
    - "**/*.spec.ts"
```

#### 代码异味报告格式

```json
{
  "detection_id": "SMELL-001",
  "timestamp": "2024-01-01T00:00:00Z",
  "analysis_scope": {
    "files_analyzed": 150,
    "total_lines": 25000
  },
  "smells_detected": [
    {
      "id": "SMELL-001",
      "type": "long_method",
      "severity": "medium",
      "location": {
        "file": "src/services/payment_service.py",
        "function": "process_payment",
        "line_start": 45,
        "line_end": 112
      },
      "description": "方法process_payment有67行，超过50行阈值",
      "metrics": {
        "actual_lines": 67,
        "threshold": 50,
        "excess": 17
      },
      "impact_assessment": {
        "readability": "降低可读性",
        "maintainability": "增加维护难度",
        "testability": "影响单元测试编写"
      },
      "refactoring_suggestion": {
        "pattern": "Extract Method",
        "steps": [
          "将验证逻辑提取为validate_payment()",
          "将支付处理逻辑提取为execute_payment()",
          "将通知逻辑提取为send_notification()"
        ],
        "expected_improvement": "方法长度降至30行以内"
      }
    },
    {
      "id": "SMELL-002",
      "type": "feature_envy",
      "severity": "high",
      "location": {
        "file": "src/controllers/user_controller.py",
        "function": "get_user_profile",
        "line_start": 78,
        "line_end": 95
      },
      "description": "方法频繁访问User类的内部属性",
      "metrics": {
        "foreign_access_count": 15,
        "threshold": 10,
        "target_class": "User"
      },
      "refactoring_suggestion": {
        "pattern": "Move Method",
        "steps": [
          "将get_user_profile移至User类",
          "或引入UserDTO封装访问逻辑"
        ]
      }
    }
  ],
  "summary": {
    "total_smells": 2,
    "by_severity": {
      "critical": 0,
      "high": 1,
      "medium": 1,
      "low": 0
    },
    "by_category": {
      "size_issues": 1,
      "coupling_issues": 1
    }
  },
  "priority_recommendations": [
    "优先修复Feature Envy问题，可能影响架构清晰度",
    "Long Method可在下次迭代中重构"
  ]
}
```

---

### 阶段五：综合分析与报告生成

```
所有分析完成
    ↓
[1] 数据汇总整合
    ↓
[2] 问题严重级别排序
    ↓
[3] 趋势对比分析
    ↓
[4] 改进建议汇总
    ↓
[5] 报告生成与分发
    ↓
输出静态分析综合报告
```

#### 综合分析报告格式

```json
{
  "report_id": "STATIC-ANALYSIS-001",
  "timestamp": "2024-01-01T00:00:00Z",
  "analysis_context": {
    "trigger": "pull_request",
    "pr_number": 123,
    "branch": "feature/user-auth",
    "commit_hash": "abc123def456",
    "author": "developer"
  },
  "executive_summary": {
    "overall_status": "conditional_pass",
    "overall_score": 82,
    "key_findings": [
      "发现1处高复杂度函数需重构",
      "检测到2处代码重复（2.8%重复率）",
      "识别2个代码异味（1个高级别）"
    ],
    "blocking_issues": 0,
    "recommendation": "建议合并，但需跟进高优先级问题"
  },
  "detailed_results": {
    "complexity_analysis": {
      "status": "conditional_pass",
      "score": 75,
      "high_complexity_functions": 1,
      "average_complexity": 6.8
    },
    "duplication_detection": {
      "status": "warning",
      "score": 88,
      "duplication_percentage": 2.8,
      "duplicate_blocks": 3
    },
    "code_smell_detection": {
      "status": "warning",
      "score": 80,
      "total_smells": 2,
      "high_severity_smells": 1
    }
  },
  "issues_summary": {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 0,
    "info": 0
  },
  "action_items": [
    {
      "priority": "high",
      "category": "complexity",
      "item": "重构validate_user函数（圈复杂度12）",
      "location": "src/services/user_service.py:85-120",
      "deadline": "2024-01-05",
      "assignee": "开发团队"
    },
    {
      "priority": "medium",
      "category": "duplication",
      "item": "消除user_service与admin_service的重复代码",
      "suggested_approach": "提取公共基类",
      "deadline": "2024-01-10"
    }
  ],
  "trend_comparison": {
    "vs_previous_analysis": {
      "score_change": 3.2,
      "issues_change": -1,
      "trend": "improving"
    },
    "vs_baseline": {
      "score_change": 7.5,
      "trend": "significant_improvement"
    }
  },
  "rule_validation_layer_integration": {
    "layer": 3,
    "submodule": "coding_standards_check",
    "checks_executed": ["complexity", "duplication", "code_smells"],
    "all_checks_passed": false,
    "warnings": 2
  }
}
```

---

## 与MARC资源协调器的资源需求

```yaml
marc_resource_requirements:
  compute_resources:
    cpu_cores: 2
    memory_gb: 4
    disk_space_gb: 10
    
  execution_time:
    incremental_analysis: "< 2 minutes"
    full_analysis: "< 15 minutes"
    
  tool_dependencies:
    - "pylint>=2.15.0"
    - "eslint>=8.0.0"
    - "radon>=5.1.0"
    - "jscpd>=3.5.0"
    
  output_storage:
    location: "docs/reviews/code_reviews/static_analysis/"
    format: ["json", "markdown"]
    retention_days: 90
```

---

## 协同调用接口

### 接口定义

| 接口名称 | 接口描述 | 调用方 |
|----------|----------|--------|
| `analyze_complexity` | 代码复杂度分析接口 | 审查报告司、门禁把控司 |
| `detect_duplication` | 代码重复检测接口 | 审查报告司 |
| `identify_code_smells` | 代码异味识别接口 | 审查报告司、性能审计司 |
| `run_full_static_analysis` | 完整静态分析接口 | 门下省主流程 |

### 调用示例

```bash
# 执行完整静态分析
python skillscripts/analysis/static_analyzer.py \
  --scope pr \
  --pr-number 123 \
  --output docs/reviews/code_reviews/static_analysis/report_20240101.json
```

---

## 版本历史

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| 1.0.0 | 2026-04-06 | 初始版本，包含完整静态分析能力 |
