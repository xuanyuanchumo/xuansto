---
name: shenchabaogao_si
description: 审查报告司，负责审查报告生成、问题分类统计、改进建议汇总。输出文档至docs/reviews/code_reviews/。
---

# 审查报告司技能指令

## 职责定义

审查报告司作为代码审查局的报告中心，承担以下职责：

| 职责类别 | 具体职责 | 关键产出 |
|----------|----------|----------|
| **报告生成** | 整合各司分析结果生成综合报告 | 审查报告 |
| **问题统计** | 问题分类、分级、趋势统计 | 统计报表 |
| **建议汇总** | 收集整理改进建议并优先级排序 | 改进建议书 |
| **报告分发** | 向相关方推送审查结果 | 通知消息 |

---

## 工作流程

### 阶段一：数据收集与整合

```
各司分析完成
    ↓
[1] 接收静态分析司数据
    ↓
[2] 接收安全扫描司数据
    ↓
[3] 接收性能审计司数据
    ↓
[4] 数据标准化处理
    ↓
[5] 数据完整性校验
    ↓
进入报告生成阶段
```

#### 数据接收规范

```yaml
data_reception_specification:
  source_departments:
    - department: "jingtaifenxi_si"
      data_types:
        - "complexity_analysis.json"
        - "duplication_report.json"
        - "code_smell_report.json"
        
    - department: "anquan_saomiao_si"
      data_types:
        - "owasp_scan_report.json"
        - "dependency_security_report.json"
        - "hardcoded_key_report.json"
        
    - department: "xingneng_shenji_si"
      data_types:
        - "algorithmic_complexity.json"
        - "memory_analysis.json"
        - "query_optimization.json"
        
  data_validation:
    required_fields: ["report_id", "timestamp", "summary"]
    schema_validation: true
    timestamp_sync_tolerance: "5 minutes"
```

---

### 阶段二：问题分类与统计

```
数据整合完成
    ↓
[1] 问题统一编号
    ↓
[2] 严重级别标准化
    ↓
[3] 分类标签分配
    ↓
[4] 影响范围评估
    ↓
[5] 统计指标计算
    ↓
输出问题统计报表
```

#### 问题分类体系

```yaml
issue_classification_system:
  severity_levels:
    critical:
      score: 4
      color: "#DC2626"
      icon: "🔴"
      definition: "必须立即修复，阻塞发布"
      examples: ["安全漏洞", "数据丢失风险", "服务中断风险"]
      
    major:
      score: 3
      color: "#EA580C"
      icon: "🟠"
      definition: "应在本次迭代修复"
      examples: ["性能严重退化", "核心功能异常", "重要安全警告"]
      
    minor:
      score: 2
      color: "#EAB308"
      icon: "🟡"
      definition: "可在近期迭代修复"
      examples: ["代码质量问题", "轻微性能问题", "非关键bug"]
      
    info:
      score: 1
      color: "#3B82F6"
      icon: "🔵"
      definition: "建议性改进"
      examples: ["代码风格", "文档完善", "最佳实践"]
      
  category_taxonomy:
    security:
      subcategories:
        - "owasp_vulnerability"
        - "dependency_vulnerability"
        - "credential_leak"
        - "authentication_issue"
        - "authorization_issue"
        
    performance:
      subcategories:
        - "algorithmic_complexity"
        - "memory_leak"
        - "n_plus_one_query"
        - "slow_query"
        - "resource_contention"
        
    quality:
      subcategories:
        - "code_duplication"
        - "code_smell"
        - "naming_convention"
        - "documentation_gap"
        - "test_coverage"
        
    architecture:
      subcategories:
        - "coupling_issue"
        - "design_pattern_violation"
        - "scalability_concern"
        - "maintainability_risk"
```

#### 问题统计报表格式

```json
{
  "statistics_report_id": "STATS-001",
  "timestamp": "2024-01-01T00:00:00Z",
  "report_period": {
    "start": "2024-01-01T00:00:00Z",
    "end": "2024-01-01T23:59:59Z",
    "type": "pull_request_review"
  },
  "review_metadata": {
    "pr_number": 123,
    "branch": "feature/user-auth",
    "author": "developer",
    "files_changed": 15,
    "lines_added": 450,
    "lines_deleted": 120
  },
  "issue_statistics": {
    "total_issues": 28,
    "by_severity": {
      "critical": {
        "count": 3,
        "percentage": 10.7,
        "trend_vs_previous": "+1"
      },
      "major": {
        "count": 7,
        "percentage": 25.0,
        "trend_vs_previous": "-2"
      },
      "minor": {
        "count": 12,
        "percentage": 42.9,
        "trend_vs_previous": "+3"
      },
      "info": {
        "count": 6,
        "percentage": 21.4,
        "trend_vs_previous": "0"
      }
    },
    "by_category": {
      "security": {
        "total": 8,
        "breakdown": {
          "owasp_vulnerability": 3,
          "dependency_vulnerability": 2,
          "credential_leak": 2,
          "authentication_issue": 1
        }
      },
      "performance": {
        "total": 7,
        "breakdown": {
          "algorithmic_complexity": 2,
          "memory_leak": 1,
          "n_plus_one_query": 2,
          "slow_query": 1,
          "resource_contention": 1
        }
      },
      "quality": {
        "total": 9,
        "breakdown": {
          "code_duplication": 2,
          "code_smell": 3,
          "naming_convention": 2,
          "documentation_gap": 2
        }
      },
      "architecture": {
        "total": 4,
        "breakdown": {
          "coupling_issue": 1,
          "design_pattern_violation": 1,
          "scalability_concern": 1,
          "maintainability_risk": 1
        }
      }
    },
    "by_source_department": {
      "jingtaifenxi_si": 9,
      "anquan_saomiao_si": 8,
      "xingneng_shenji_si": 7,
      "manual_review": 4
    },
    "by_file": [
      {
        "file": "src/auth/authentication.py",
        "issues": 6,
        "critical": 2,
        "major": 2,
        "minor": 2
      },
      {
        "file": "src/services/user_service.py",
        "issues": 5,
        "critical": 1,
        "major": 2,
        "minor": 2
      },
      {
        "file": "src/repository/order_repository.py",
        "issues": 4,
        "critical": 0,
        "major": 2,
        "minor": 2
      }
    ],
    "density_metrics": {
      "issues_per_100_lines": 5.2,
      "issues_per_file": 1.87,
      "critical_issues_per_file": 0.2
    }
  },
  "trend_analysis": {
    "vs_last_week": {
      "total_issues_change": "+12%",
      "critical_change": "+50%",
      "quality_score_change": "-5%"
    },
    "vs_last_month": {
      "total_issues_change": "+8%",
      "critical_change": "+20%",
      "quality_score_change": "-3%"
    },
    "projection": {
      "if_no_action": "Critical issues expected to increase 15% next sprint",
      "with_remediation": "Expected 70% reduction in 2 sprints"
    }
  },
  "hotspots": {
    "most_problematic_files": [
      {"file": "src/auth/authentication.py", "issue_count": 6},
      {"file": "src/services/user_service.py", "issue_count": 5}
    ],
    "most_common_categories": ["security", "quality"],
    "emerging_patterns": ["credential_hardcoding", "n_plus_one_queries"]
  }
}
```

---

### 阶段三：改进建议汇总

```
问题统计完成
    ↓
[1] 收集各司改进建议
    ↓
[2] 去重与合并
    ↓
[3] 影响评估
    ↓
[4] ROI分析
    ↓
[5] 优先级排序
    ↓
[6] 责任人分配
    ↓
输出改进建议书
```

#### 优先级排序算法

```yaml
priority_sorting_algorithm:
  factors:
    severity_weight: 0.35
    impact_weight: 0.25
    effort_weight: 0.20
    frequency_weight: 0.10
    dependency_weight: 0.10
    
  scoring_formula: >
    priority_score = (
      severity * 0.35 +
      impact * 0.25 +
      (1/normalized_effort) * 0.20 +
      frequency * 0.10 +
      dependency_blocking * 0.10
    )
    
  priority_levels:
    p0_critical:
      score_range: [0.8, 1.0]
      sla: "24 hours"
      required_approvers: 1
      blocks_merge: true
      
    p1_urgent:
      score_range: [0.6, 0.8)
      sla: "1 week"
      required_approvers: 1
      blocks_merge: false
      
    p2_important:
      score_range: [0.4, 0.6)
      sla: "2 weeks"
      required_approvers: 0
      blocks_merge: false
      
    p3_enhancement:
      score_range: [0.0, 0.4)
      sla: "backlog"
      required_approvers: 0
      blocks_merge: false
```

#### 改进建议书格式

```json
{
  "recommendation_report_id": "REC-001",
  "timestamp": "2024-01-01T00:00:00Z",
  "pr_reference": 123,
  "executive_summary": {
    "total_recommendations": 15,
    "p0_critical": 3,
    "p1_urgent": 5,
    "p2_important": 4,
    "p3_enhancement": 3,
    "estimated_total_effort_days": 8,
    "expected_quality_improvement_percent": 65,
    "merge_decision": "CONDITIONAL_PASS - Fix P0 issues required"
  },
  "prioritized_recommendations": [
    {
      "id": "REC-P0-001",
      "priority": "P0 - Critical",
      "score": 0.92,
      "title": "Remove hardcoded database credentials",
      "related_issues": ["FINDING-001", "VULN-003"],
      "category": "security.credential_leak",
      "current_state": "Database password hardcoded in config/database.py line 23",
      "proposed_solution": "Migrate to AWS Secrets Manager or environment variables",
      "implementation_steps": [
        "Remove hardcoded password from source code",
        "Add os.environ.get('DB_PASSWORD') with validation",
        "Configure AWS Secrets Manager for production",
        "Update deployment documentation",
        "Rotate existing credential immediately"
      ],
      "effort_estimate": {
        "hours": 4,
        "complexity": "low",
        "dependencies": []
      },
      "impact_assessment": {
        "security_improvement": "Eliminates critical credential exposure risk",
        "compliance_impact": "Resolves GDPR Article 32 violation risk",
        "risk_if_not_fixed": "Database compromise if code repository breached"
      },
      "roi": {
        "cost_of_fix": "4 hours developer time",
        "cost_of_breach_estimated": "$150,000-$3,000,000 (IBM Cost of Data Breach 2023)",
        "roi_ratio": "extremely_high"
      },
      "assignee": "Security Engineer",
      "due_date": "2024-01-02",
      "blocks_merge": true,
      "verification_criteria": [
        "No hardcoded passwords found by hardcoded_detector.py",
        "All tests pass with environment variable configuration",
        "Production deployment uses Secrets Manager"
      ]
    },
    {
      "id": "REC-P0-002",
      "priority": "P0 - Critical",
      "score": 0.88,
      "title": "Fix SQL injection vulnerability in user repository",
      "related_issues": ["VULN-001"],
      "category": "security.owasp_vulnerability",
      "current_state": "String concatenation used in SQL query construction",
      "proposed_solution": "Convert to parameterized queries",
      "effort_estimate": {
        "hours": 2,
        "complexity": "low"
      },
      "blocks_merge": true
    },
    {
      "id": "REC-P0-003",
      "priority": "P0 - Critical",
      "score": 0.85,
      "title": "Fix database connection leak causing pool exhaustion",
      "related_issues": ["LEAK-002"],
      "category": "performance.memory_leak",
      "current_state": "Connections not closed in exception paths",
      "proposed_solution": "Implement context manager pattern with proper cleanup",
      "effort_estimate": {
        "hours": 4,
        "complexity": "medium"
      },
      "blocks_merge": true
    },
    {
      "id": "REC-P1-001",
      "priority": "P1 - Urgent",
      "score": 0.72,
      "title": "Resolve N+1 query problem in user orders endpoint",
      "related_issues": ["N+1-001"],
      "category": "performance.n_plus_one_query",
      "current_state": "52 queries executed where 2 would suffice",
      "proposed_solution": "Implement eager loading with joinedload",
      "effort_estimate": {
        "hours": 2,
        "complexity": "low"
      },
      "performance_gain": "8x faster response time",
      "blocks_merge": false
    },
    {
      "id": "REC-P1-002",
      "priority": "P1 - Urgent",
      "score": 0.68,
      "title": "Reduce cyclomatic complexity in validate_user function",
      "related_issues": ["COMP-FUNC-001"],
      "category": "quality.algorithmic_complexity",
      "current_state": "Complexity 12 exceeds threshold of 10",
      "proposed_solution": "Extract validation rules into strategy pattern",
      "effort_estimate": {
        "hours": 6,
        "complexity": "medium"
      },
      "maintainability_gain": "Improved readability and testability"
    }
  ],
  "grouped_by_theme": {
    "security_hardening": {
      "recommendations": ["REC-P0-001", "REC-P0-002"],
      "total_effort_hours": 6,
      "combined_impact": "Eliminate all critical security vulnerabilities"
    },
    "performance_optimization": {
      "recommendations": ["REC-P0-003", "REC-P1-001"],
      "total_effort_hours": 6,
      "combined_impact": "8x performance improvement, prevent outages"
    },
    "code_quality": {
      "recommendations": ["REC-P1-002", "REC-P2-*"],
      "total_effort_hours": 12,
      "combined_impact": "Improved maintainability and reduced technical debt"
    }
  },
  "implementation_roadmap": {
    "phase_1_immediate_24h": {
      "items": ["REC-P0-001", "REC-P0-002", "REC-P0-003"],
      "team_assignment": "Security + Backend teams",
      "goal": "Unblock merge, eliminate critical risks"
    },
    "phase_2_this_sprint": {
      "items": ["REC-P1-001", "REC-P1-002", "REC-P1-003", "REC-P1-004", "REC-P1-005"],
      "team_assignment": "Backend team",
      "goal": "Complete urgent improvements"
    },
    "phase_3_next_sprint": {
      "items": ["REC-P2-*"],
      "team_assignment": "All teams",
      "goal": "Address important improvements"
    }
  }
}
```

---

### 阶段四：综合审查报告生成

```
改进建议汇总完成
    ↓
[1] 执行摘要撰写
    ↓
[2] 详细内容编排
    ↓
[3] 图表可视化生成
    ↓
[4] 附录材料整理
    ↓
[5] 报告质量检查
    ↓
[6] 报告输出与存档
    ↓
输出最终审查报告
```

#### 综合审查报告格式

```markdown
# 代码审查报告

**报告编号**: CODE-REVIEW-20240101-001  
**审查日期**: 2024-01-01  
**审查分支**: feature/user-auth  
**PR编号**: #123  
**审查人**: 门下省代码审查局  

---

## 📊 执行摘要

### 总体评价: ⚠️ 有条件通过 (Conditional Pass)

**综合评分**: 62/100  
**问题总数**: 28 个  
**阻塞问题**: 3 个 (必须修复)

### 关键发现

- 🔴 **3个Critical安全问题**需要立即修复
- 🟠 **2个性能问题**可能导致生产事故
- 🟡 **代码质量整体良好**，但存在改进空间
- ✅ **测试覆盖率达标** (85%)

### 决策建议

**当前状态**: 🚫 **阻止合并**

**条件**: 修复以下P0级别问题后可以合并：
1. 移除硬编码数据库凭据
2. 修复SQL注入漏洞
3. 解决数据库连接泄漏

---

## 📈 问题概览

| 严重级别 | 数量 | 占比 | 趋势 |
|---------|------|------|------|
| 🔴 Critical | 3 | 10.7% | ↑ +1 |
| 🟠 Major | 7 | 25.0% | ↓ -2 |
| 🟡 Minor | 12 | 42.9% | ↑ +3 |
| 🔵 Info | 6 | 21.4% | → 0 |

---

## 🔐 安全问题详情 (8个)

### Critical (3个)

#### 1. 硬编码数据库凭据 [FINDING-001]
- **位置**: `config/database.py:23`
- **描述**: 数据库密码明文写在源代码中
- **风险**: 代码仓库泄露将导致数据库完全沦陷
- **修复**: 迁移至AWS Secrets Manager

#### 2. SQL注入漏洞 [VULN-001]
- **位置**: `src/repository/user_repository.py:45-48`
- **描述**: 使用f-string拼接SQL查询
- **风险**: 攻击者可执行任意SQL命令
- **修复**: 使用参数化查询

#### ... (详见附件)

---

## ⚡ 性能问题详情 (7个)

### Critical (1个)

#### 1. 数据库连接池泄漏 [LEAK-002]
- **位置**: `src/repository/base_repository.py:67`
- **描述**: 异常路径中连接未释放
- **风险**: 连接池耗尽导致服务不可用
- **修复**: 实现上下文管理器模式

---

## 📝 代码质量问题 (9个)

... (详见附件)

---

## 🎯 改进建议优先级列表

| 优先级 | 建议 | 工时 | 影响 | 责任人 |
|-------|------|------|------|--------|
| P0 | 移除硬编码凭据 | 4h | 消除安全风险 | Security Eng |
| P0 | 修复SQL注入 | 2h | 消除安全风险 | Backend Dev |
| P0 | 修复连接泄漏 | 4h | 防止服务中断 | Backend Lead |
| P1 | 解决N+1查询 | 2h | 8x性能提升 | Backend Dev |
| P1 | 降低函数复杂度 | 6h | 可维护性提升 | Backend Dev |

---

## 📊 趋势分析

### 与上周对比
- 问题总数: +12%
- Critical问题: +50% ⚠️
- 质量评分: -5%

### 与上月对比
- 问题总数: +8%
- Critical问题: +20% ⚠️
- 质量评分: -3%

---

## 📋 行动计划

### 立即行动 (24小时内)
- [ ] 修复3个Critical安全问题
- [ ] 轮换已暴露的凭据
- [ ] 更新CI/CD安全扫描规则

### 本周行动
- [ ] 完成5个P1级别改进
- [ ] 添加性能监控告警
- [ ] 进行团队安全编码培训

---

## 📎 附件

1. [详细问题清单](./issues_detail.json)
2. [安全扫描原始报告](../security/owasp_scan_20240101.json)
3. [性能审计报告](../performance/audit_20240101.json)
4. [静态分析报告](../static_analysis/report_20240101.json)

---

**报告生成**: 审查报告司  
**审核**: 门下省审议官  
**下次审查**: PR合并后或2024-01-08
```

#### JSON格式报告（用于程序化处理）

```json
{
  "report_id": "CODE-REVIEW-20240101-001",
  "metadata": {
    "generated_at": "2024-01-01T00:00:00Z",
    "generated_by": "shenchabaogao_si",
    "report_format": "comprehensive",
    "version": "1.0.0"
  },
  "review_context": {
    "pr_number": 123,
    "branch": "feature/user-auth",
    "commit_hash": "abc123def456",
    "author": "developer",
    "reviewers": ["menxiasheng-code-review-bureau"],
    "review_duration_minutes": 45
  },
  "verdict": {
    "decision": "conditional_pass",
    "overall_score": 62,
    "blocking_issues_count": 3,
    "merge_allowed": false,
    "conditions": [
      "Fix all P0-critical issues",
      "Re-run security scan after fixes"
    ]
  },
  "sections": {
    "executive_summary": {...},
    "issue_statistics": {...},
    "security_findings": {...},
    "performance_findings": {...},
    "quality_findings": {...},
    "recommendations": {...},
    "action_plan": {...},
    "attachments": [...]
  },
  "sign_off": {
    "prepared_by": "shenchabaogao_si",
    "reviewed_by": "menxiasheng_supervisor",
    "approved_by": null,
    "next_review_date": "2024-01-08T00:00:00Z"
  }
}
```

---

## 输出物管理

### 输出目录结构

```
docs/reviews/code_reviews/
├── 2024/
│   ├── 01/
│   │   ├── report_20240101.md          # 主报告(Markdown)
│   │   ├── report_20240101.json        # 结构化数据(JSON)
│   │   ├── statistics_20240101.json    # 统计数据
│   │   ├── recommendations_20240101.json # 改进建议
│   │   └── attachments/               # 附件
│   │       ├── owasp_scan.json
│   │       ├── performance_audit.json
│   │       └── static_analysis.json
│   └── ...
├── summary/
│   ├── monthly_summary_2024_01.md     # 月度汇总
│   └── quarterly_summary_2024_Q1.md   # 季度汇总
└── index.md                           # 报告索引
```

### 报告生命周期

```yaml
report_lifecycle:
  states:
    - name: "draft"
      description: "报告中"
      duration: "< 1 hour"
      
    - name: "under_review"
      description: "待审核"
      duration: "< 4 hours"
      
    - name: "approved"
      description: "已批准"
      retention: "permanent"
      
    - name: "archived"
      description: "已归档"
      retention: "2 years"
      
  naming_convention: "{type}_{date}_{sequence}.{format}"
  example: "code_review_20240101_001.md"
```

---

## 与MARC资源协调器的资源需求

```yaml
marc_resource_requirements:
  compute_resources:
    cpu_cores: 2
    memory_gb: 4
    disk_space_gb: 20
    
  execution_time:
    report_generation: "< 5 minutes"
    data_aggregation: "< 2 minutes"
    visualization_generation: "< 3 minutes"
    
  storage_requirements:
    output_directory: "docs/reviews/code_reviews/"
    estimated_monthly_size_mb: 500
    retention_policy: "2 years"
    
  dependencies:
    internal:
      - "jingtaifenxi_si outputs"
      - "anquan_saomiao_si outputs"
      - "xingneng_shenji_si outputs"
      
    external:
      - "template_engine (Jinja2/Mustache)"
      - "chart_library (matplotlib/plotly)"
      
  notification_channels:
    - "pull_request_comment"
    - "slack_notification"
    - "email_digest"
```

---

## 协同调用接口

### 接口定义

| 接口名称 | 接口描述 | 调用方 |
|----------|----------|--------|
| `generate_review_report` | 生成综合审查报告接口 | 门下省主流程 |
| `compile_statistics` | 编译问题统计接口 | 质量监控局 |
| `generate_recommendations` | 生成改进建议接口 | 门下省主流程 |
| `distribute_report` | 分发报告接口 | 通知系统 |

### 调用示例

```bash
# 生成审查报告
python skillscripts/report/generate_review_report.py \
  --pr-number 123 \
  --input-dir temp/analysis_results/ \
  --output-dir docs/reviews/code_reviews/2024/01/ \
  --format markdown,json \
  --include-statistics \
  --include-recommendations \
  --include-visualizations
```

---

## 版本历史

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| 1.0.0 | 2026-04-06 | 初始版本，包含完整的报告生成、统计和建议汇总能力 |
