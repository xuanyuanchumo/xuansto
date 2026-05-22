---
name: fugai_fenxi_si
description: 覆盖分析司，负责行/分支/函数覆盖率分析、覆盖缺口定位。工具集成Coverage.py/Istanbul/covtrace。集成闭环验证器的条款覆盖率统计。
---

# 覆盖分析司技能指令

## 职责定义

覆盖分析司作为测试验证局的质量度量核心，承担以下职责：

| 职责类别 | 具体职责 | 关键产出 |
|----------|----------|----------|
| **覆盖率采集** | 行/分支/函数/语句覆盖率数据采集 | 覆盖率原始数据 |
| **缺口定位** | 未覆盖代码定位与分类 | 覆盖缺口报告 |
| **趋势追踪** | 覆盖率变化趋势分析与预测 | 趋势分析报告 |
| **条款映射** | SDD条款到测试用例的覆盖率映射 | 条款覆盖矩阵 |

---

## 工具集成

### 核心覆盖率工具

| 工具 | 用途 | 语言支持 | 输出格式 |
|------|------|----------|----------|
| **Coverage.py** | Python覆盖率采集 | Python | XML, HTML, JSON |
| **Istanbul (nyc)** | JavaScript覆盖率采集 | JS/TS | JSON, HTML, LCOV |
| **JaCoCo** | Java覆盖率采集 | Java | XML, HTML, exec |
| **covtrace** | 多语言统一覆盖率追踪 | 多语言 | 统一格式 |
| **llvm-cov** | Rust/C++覆盖率 | Rust/C++ | JSON |

### 四维防线闭环验证器集成

```yaml
closed_loop_verifier_integration:
  description: "将SDD规范的可执行条款与实际测试用例关联，实现条款级别的覆盖率统计"
  
  clause_coverage_tracking:
    mapping_mechanism:
      source: "SDD specification clauses (from yongli_sheji_si)"
      target: "executed test cases (from zhixing_guanli_si)"
      linkage: "test case metadata contains clause_id reference"
      
    coverage_calculation:
      total_clauses: "{{count of executable clauses in SDD}}"
      covered_clauses: "{{count of clauses with ≥1 passing test}}"
      clause_coverage_percent: "(covered_clauses / total_clauses) * 100"
      
    granularity_levels:
      specification_level:
        unit: "SDD document"
        example: "auth_spec.md coverage: 92%"
        
      feature_level:
        unit: "feature/module"
        example: "User authentication coverage: 95%"
        
      clause_level:
        unit: "individual requirement clause"
        example: "REQ-AUTH-001: Covered by TC-USR-001~TC-USR-008"
        
  verification_feedback_loop:
    when_coverage_drops:
      action: "Alert quality_monitor_bureau"
      threshold: "drop > 3% from baseline"
      
    when_clause_uncovered:
      action: "Notify yongli_sheji_si to generate missing tests"
      priority: "based on clause risk level"
      
    when_target_achieved:
      action: "Log achievement, update baseline if higher"
      celebration: "🎉 Coverage milestone reached!"
```

---

## 工作流程

### 阶段一：覆盖率数据采集

```
测试执行完成
    ↓
[1] 触发覆盖率工具
    ↓
[2] 原始数据收集
    ↓
[3] 数据标准化处理
    ↓
[4] 元数据附加（版本、分支等）
    ↓
进入覆盖率分析阶段
```

#### 采集配置

```yaml
coverage_collection_config:
  tools_configuration:
    coverage_py:
      command: >
        pytest --cov=src 
               --cov-report=xml:coverage.xml 
               --cov-report=html:htmlcov/
               --cov-report=term-missing
               --cov-config=.coveragerc
               
      configuration_file: ".coveragerc"
      settings: |
        [run]
        source = src
        branch = True
        omit = 
            */tests/*
            */__pycache__/*
            */migrations/*
            */venv/*
            */.tox/*
            
        [report]
        exclude_lines =
            pragma: no cover
            def __repr__
            raise NotImplementedError
            if TYPE_CHECKING:
            @abstractmethod
            
        [html]
        directory = htmlcov
        
    istanbul:
      command: >
        npx nyc --reporter=html 
              --reporter=text 
              --reporter=json-summary 
              --report-dir=coverage/
              npm test
              
      configuration: "package.json (nyc config section)"
      settings: |
        {
          "nyc": {
            "extends": "@istanbuljs/nyc-config-typescript",
            "all": true,
            "include": ["src/**/*.ts", "src/**/*.tsx"],
            "exclude": [
              "**/*.d.ts",
              "**/*.spec.ts",
              "**/*.test.ts",
              "**/node_modules/**"
            ],
            "check-coverage": true,
            "branches": 80,
            "functions": 85,
            "lines": 85,
            "statements": 85
          }
        }
        
  data_collection_points:
    - point: "after_unit_tests"
      tools: ["coverage.py", "istanbul"]
      granularity: "statement, branch, function"
      
    - point: "after_integration_tests"
      tools: ["coverage.py", "istanbul"]
      granularity: "statement, branch, function, condition"
      
    - point: "after_e2e_tests"
      tools: ["istanbul (for frontend code)"]
      granularity: "statement, branch"
      
  metadata_collection:
    always_include:
      - commit_hash
      - branch_name
      - timestamp
      - pr_number (if applicable)
      - author
      - build_number
      
    optional:
      - test_execution_duration
      - environment_info
      - custom_tags
```

---

### 阶段二：多维度覆盖率分析

```
数据采集完成
    ↓
[1] 行覆盖率分析
    ↓
[2] 分支覆盖率分析
    ↓
[3] 函数/方法覆盖率分析
    ↓
[4] 条件覆盖率分析
    ↓
[5] 综合评分计算
    ↓
输出详细覆盖率分析报告
```

#### 覆盖率维度定义

```yaml
coverage_dimensions:
  line_coverage:
    definition: "被执行的代码行占总可执行行的百分比"
    calculation: "(executed_lines / total_executable_lines) * 100"
    importance: "基础指标，最直观"
    target: 85%
    weight_in_composite_score: 0.30
    
  branch_coverage:
    definition: "被执行的代码分支（if/else等）占总分支数的百分比"
    calculation: "(taken_branches / total_branches) * 100"
    importance: "反映条件逻辑覆盖程度"
    target: 80%
    weight_in_composite_score: 0.25
    
  function_coverage:
    definition: "被调用的函数/方法占总函数数的百分比"
    calculation: "(called_functions / total_functions) * 100"
    importance: "反映API级别覆盖"
    target: 90%
    weight_in_composite_score: 0.20
    
  statement_coverage:
    definition: "被执行的语句占总语句数的百分比"
    importance: "类似行覆盖率但更细粒度"
    target: 85%
    weight_in_composite_score: 0.15
    
  condition_coverage:
    definition: "每个布尔子条件的真/假值都被测试到的程度"
    importance: "最高级别的逻辑覆盖"
    target: 70%
    weight_in_composite_score: 0.10
    
  composite_score:
    formula: >
      weighted_sum(
        line_coverage * 0.30 +
        branch_coverage * 0.25 +
        function_coverage * 0.20 +
        statement_coverage * 0.15 +
        condition_coverage * 0.10
      )
```

#### 详细覆盖率分析报告格式

```json
{
  "analysis_report_id": "COVG-ANALYSIS-001",
  "timestamp": "2024-01-01T00:00:00Z",
  "build_context": {
    "commit_hash": "abc123def456",
    "branch": "feature/user-auth",
    "pr_number": 123,
    "author": "developer@company.com",
    "build_number": "CI-20240101-0145"
  },
  
  "overall_metrics": {
    "composite_coverage_score": 84.7,
    "grade": "B+",
    "target_met": false,
    "gap_to_target": -0.3,
    "vs_previous_build": "+1.2",
    "trend": "improving"
  },
  
  "dimensional_breakdown": {
    "line_coverage": {
      "value": 86.2,
      "target": 85.0,
      "status": "met",
      "covered_lines": 12548,
      "total_lines": 14562,
      "missing_lines": 2014,
      "partial_lines": 89,
      "weight": 0.30,
      "weighted_score": 25.86
    },
    
    "branch_coverage": {
      "value": 79.5,
      "target": 80.0,
      "status": "not_met",
      "gap": -0.5,
      "taken_branches": 3842,
      "total_branches": 4832,
      "not_taken_branches": 990,
      "weight": 0.25,
      "weighted_score": 19.88
    },
    
    "function_coverage": {
      "value": 91.3,
      "target": 90.0,
      "status": "exceeded",
      "called_functions": 432,
      "total_functions": 473,
      "uncalled_functions": 41,
      "weight": 0.20,
      "weighted_score": 18.26
    },
    
    "statement_coverage": {
      "value": 87.1,
      "target": 85.0,
      "status": "exceeded",
      "executed_statements": 18932,
      "total_statements": 21736,
      "weight": 0.15,
      "weighted_score": 13.07
    },
    
    "condition_coverage": {
      "value": 72.4,
      "target": 70.0,
      "status": "exceeded",
      "true_conditions_evaluated": 2156,
      "false_conditions_evaluated": 1987,
      "total_conditions": 5743,
      "weight": 0.10,
      "weighted_score": 7.24
    }
  },
  
  "module_breakdown": [
    {
      "module": "src/services/user_service.py",
      "path": "src/services/user_service.py",
      "language": "Python",
      "metrics": {
        "line_coverage": 94.5,
        "branch_coverage": 91.2,
        "function_coverage": 100.0,
        "complexity": 8.2
      },
      "status": "excellent",
      "tested_functions": ["create_user", "get_user", "update_user", "delete_user"],
      "untested_functions": [],
      "risk_assessment": "low"
    },
    {
      "module": "src/services/payment_service.py",
      "path": "src/services/payment_service.py",
      "language": "Python",
      "metrics": {
        "line_coverage": 78.3,
        "branch_coverage: 71.5,
        "function_coverage": 85.7,
        "complexity": 15.4
      },
      "status": "needs_attention",
      "tested_functions": ["process_payment", "refund_payment"],
      "untested_functions": ["handle_dispute", "apply_promotion", "calculate_tax"],
      "risk_assessment": "medium-high (payment logic is critical)"
    },
    {
      "module": "src/utils/helpers.py",
      "path": "src/utils/helpers.py",
      "language": "Python",
      "metrics": {
        "line_coverage": 62.1,
        "branch_coverage: 55.8,
        "function_coverage": 70.0,
        "complexity": 5.2
      },
      "status": "below_threshold",
      "tested_functions": ["format_date", "validate_email"],
      "untested_functions": ["parse_csv", "generate_uuid", "hash_password", "sanitize_html"],
      "risk_assessment": "medium (utility functions widely used)"
    }
  ],
  
  "coverage_hotspots": {
    "least_covered_modules": [
      {"module": "src/utils/helpers.py", "coverage": 62.1, "priority": "high"},
      {"module": "src/middleware/rate_limiter.py", "coverage": 68.5, "priority": "medium"},
      {"module": "src/services/notification_service.py", "coverage": 72.3, "priority": "medium"}
    ],
    
    "critical_uncovered_code": [
      {
        "file": "src/services/payment_service.py",
        "line_range": [234, 289],
        "function": "handle_dispute",
        "reason_uncovered": "No integration test for dispute workflow",
        "business_risk": "High - financial impact possible",
        "suggested_action": "Create dispute scenario integration test"
      },
      {
        "file": "src/utils/helpers.py",
        "line_range": [156, 198],
        "function": "sanitize_html",
        "reason_uncovered": "Utility function rarely directly tested",
        "security_risk": "Medium - XSS prevention relies on this",
        "suggested_action": "Add security-focused unit tests with XSS payloads"
      }
    ],
    
    "complexity_vs_coverage_correlation": {
      observation: "Higher complexity functions tend to have lower coverage",
      "data_points": [
        {"complexity": 3, "avg_coverage": 95.2},
        {"complexity": 5-8, "avg_coverage": 88.5},
        {"complexity": 9-12, "avg_coverage": 76.3},
        {"complexity": ">12, "avg_coverage": 64.8}
      ],
      "recommendation": "Focus testing effort on high-complexity functions"
    }
  }
}
```

---

### 阶段三：覆盖缺口定位与分析

```
多维分析完成
    ↓
[1] 缺口识别（未覆盖代码块）
    ↓
[2] 缺口分类（按原因和风险）
    ↓
[3] 影响评估（业务影响和技术债务）
    ↓
[4] 补测建议生成
    ↓
[5] 优先级排序
    ↓
输出覆盖缺口报告
```

#### 缺口分类体系

```yaml
gap_classification_system:
  categories:
    untested_feature:
      description: "全新功能完全没有测试"
      risk: "high"
      remediation: "设计完整的测试套件 (yongli_sheji_si)"
      examples:
        - "New API endpoint without any tests"
        - "Added business logic not covered"
        
    partial_coverage:
      description: "功能有测试但覆盖不完整"
      risk: "medium"
      remediation: "补充边界和异常场景测试"
      subcategories:
        - "happy_path_only"  # 只测试正常路径
        - "missing_edge_cases"  # 缺少边界测试
        - "exception_paths_missing"  # 异常路径未覆盖
        - "branch_not_taken"  # 某些分支未执行
        
    dead_code:
      description: "无法到达或不再使用的代码"
      risk: "low (unless security-relevant)"
      remediation: "删除死代码或标记为遗留"
      identification_methods:
        - "0% coverage confirmed over multiple runs"
        - "No imports or references found"
        - "Marked as deprecated"
        
    excluded_intentionally:
      description: "有意排除的代码（如main入口）"
      risk: "none"
      should_be: "Documented in .coveragerc omit patterns"
      
    hard_to_test:
      description: "技术上难以测试的代码"
      risk: "varies"
      remediation: "Refactor for testability or accept risk"
      examples:
        - "GUI rendering code"
        - "Hardware interaction"
        - "Complex async operations"
        
  gap_priority_scoring:
    factors:
      business_criticality: 0.35
      security_impact: 0.25
      complexity: 0.15
      change_frequency: 0.15
      testability: 0.10
      
    priority_matrix:
      P0_Critical:
        score_range: [0.8, 1.0]
        action: "Must add tests before next release"
        sla: "This sprint"
        
      P1_High:
        score_range: [0.6, 0.8)
        action: "Plan tests for next sprint"
        sla: "Next 2 sprints"
        
      P2_Medium:
        score_range: [0.4, 0.6)
        action: "Add to backlog"
        sla: "Quarterly goal"
        
      P3_Low:
        score_range: [0.0, 0.4)
        action: "Accept or refactor"
        sla: "As needed"
```

#### 覆盖缺口报告格式

```markdown
# 覆盖缺口分析报告

**报告编号**: GAP-REPORT-20240101  
**分析日期**: 2024-01-01  
**基准线覆盖率**: 83.5%  
**当前覆盖率**: 84.7% (+1.2%)  

---

## 📊 执行摘要

### 总体状况: ⚠️ 接近目标，有关键缺口需填补

| 指标 | 当前 | 目标 | 差距 | 状态 |
|------|------|------|------|------|
| 综合覆盖率 | 84.7% | 85.0% | -0.3% | ⚠️ 接近 |
| 行覆盖率 | 86.2% | 85.0% | +1.2% | ✅ 达标 |
| 分支覆盖率 | 79.5% | 80.0% | -0.5% | ❌ 未达标 |
| 函数覆盖率 | 91.3% | 90.0% | +1.3% | ✅ 超标 |

### 关键发现

- 🔴 **3个高优先级缺口**涉及支付和安全相关代码
- 🟠 **分支覆盖率差0.5%**即可达标（约25个分支）
- 🟡 **工具函数模块**整体偏低（62.1%），影响面广
- ✅ **核心业务逻辑**覆盖率良好（>90%）

---

## 🔍 详细缺口清单

### P0-Critical 缺口 (必须修复)

#### GAP-P0-001: 支付争议处理函数未覆盖
- **位置**: `src/services/payment_service.py:234-289`
- **函数**: `handle_dispute()`
- **当前覆盖率**: 0% (完全未覆盖)
- **缺失分支**: 5个 (包括退款路径、通知路径)
- **业务风险**: 🔴 高 - 可能导致资金损失
- **安全风险**: 🟠 中 - 权限校验路径未验证
- **建议操作**:
  1. 创建争议场景集成测试 (优先)
  2. 添加权限边界测试
  3. 模拟异常支付状态测试
- **预估工作量**: 4小时
- **责任团队**: 后端支付组

#### GAP-P0-002: HTML清理函数未覆盖
- **位置**: `src/utils/helpers.py:156-198`
- **函数**: `sanitize_html()`
- **当前覆盖率**: 0%
- **安全风险**: 🔴 高 - XSS防护依赖此函数
- **缺失测试场景**:
  - Script标签注入
  - Event handler注入
  - URL协议注入
  - 编码绕过尝试
- **建议操作**:
  1. 创建XSS payload测试套件
  2. 使用已知XSS向量库测试
  3. 验证输出白名单有效性
- **预估工作量**: 3小时
- **责任团队**: 安全组

#### GAP-P0-003: 速率限制器边缘情况
- **位置**: `src/middleware/rate_limiter.py:45-112`
- **函数**: `check_rate_limit()`
- **当前覆盖率**: 55% (缺少边界和溢出场景)
- **性能风险**: 🟠 中 - 限制失效可能导致DoS
- **缺失测试**:
  - 计数器溢出/回绕
  - 分布式同步竞态
  - 白名单/黑名单边界
- **预估工作量**: 2小时

---

### P1-High 缺口 (近期修复)

| ID | 位置 | 当前覆盖率 | 主要缺失 | 风险 | 工作量 |
|----|------|------------|----------|------|--------|
| GAP-P1-001 | `notification_service.py` | 72.3% | 异常通知路径 | 中 | 2h |
| GAP-P1-002 | `auth/token_manager.py` | 75.8% | Token刷新边界 | 中高 | 3h |
| GAP-P1-003 | `cache/redis_client.py` | 68.2% | 连接池耗尽处理 | 中 | 2h |

---

### P2-Medium 缺口 (计划修复)

- **工具函数集合** (`helpers.py`) 整体提升至80%
- **配置加载器** 边界条件补充
- **日志记录器** 异常路径覆盖

---

## 📈 缺口修复路线图

### Sprint 1 (本周)
- [ ] 修复 GAP-P0-001 (支付争议)
- [ ] 修复 GAP-P0-002 (HTML清理)
- **预期收益**: 分支覆盖率 +1.5%, 综合覆盖率 +0.8%

### Sprint 2 (下周)
- [ ] 修复 GAP-P0-003 (速率限制)
- [ ] 修复 GAP-P1-001, GAP-P1-002
- **预期收益**: 分支覆盖率 +0.8%, 综合覆盖率 +0.5%

### Sprint 3 (两周后)
- [ ] 修复所有 P1 缺口
- [ ] 开始 P2 缺口处理
- **目标**: 达到并维持 88%+ 综合覆盖率

---

## 🎯 覆盖率提升策略

### 策略1: TDD强制 (新增代码)
- 所有新代码必须先写测试
- PR审查时检查增量覆盖率≥90%
- 工具: pre-commit hook + CI gate

### 策略2: 风险驱动补测 (存量代码)
- 优先覆盖高风险/高复杂度代码
- 使用变异测试识别弱测试
- 定期审计未覆盖代码

### 策略3: 架构级改进
- 降低圈复杂度（拆分大函数）
- 提升可测试性（依赖注入）
- 消除死代码

---

**报告编制**: 覆盖分析司  
**审核**: 测试验证局局长  
**下次分析**: 下次构建完成后
```

---

### 阶段四：条款覆盖率统计（闭环验证器集成）

```
缺口分析完成
    ↓
[1] 加载SDD可执行条款列表
    ↓
[2] 映射条款到测试用例
    ↓
[3] 统计各条款覆盖状态
    ↓
[4] 生成条款覆盖矩阵
    ↓
[5] 反馈给用例设计司
    ↓
输出条款覆盖率报告
```

#### 条款覆盖率矩阵格式

```yaml
clause_coverage_matrix:
  metadata:
    generated_at: "2024-01-01T00:00:00Z"
    generator: "fugai_fenxi_si (closed-loop-verifier-integration)"
    sdd_document: "auth_specification_v2.1.md"
    total_clauses: 45
    covered_clauses: 42
    overall_clause_coverage: 93.3%
    
  matrix_data:
    REQ-AUTH-001:
      text: "用户名长度必须在3-50字符之间，只能包含字母、数字和下划线"
      category: "validation"
      risk_level: "medium"
      status: "fully_covered"
      covering_test_cases:
        - "TC-USR-003" (boundary_min)
        - "TC-USR-004" (valid_min)
        - "TC-USR-007" (valid_max)
        - "TC-USR-008" (boundary_max_plus_one)
        - "TC-USR-009" (invalid_chars)
      coverage_quality: "excellent"
      last_passed: "2024-01-01T14:32:15Z"
      
    REQ-AUTH-002:
      text: "用户注册成功后应发送验证邮件"
      category: "postcondition"
      risk_level: "high"
      status: "partially_covered"
      covering_test_cases:
        - "TC-USR-021" (email_sent_check) ✅
        - "TC-USR-022" (email_content_validation) ✅
        - "TC-USR-023" (email_delivery_confirmation) ❌ MISSING
      missing_scenarios:
        - "邮件发送失败的回退行为"
        - "邮件内容中的链接正确性验证"
        - "验证码过期时间准确性"
      coverage_quality: "good (75%)"
      recommended_new_tests:
        - id: "TC-USR-NEW-001"
          scenario: "邮件服务不可达时的用户反馈"
          priority: "P1"
          
    REQ-AUTH-010:
      text: "连续5次登录失败应锁定账户30分钟"
      category: "security"
      risk_level: "critical"
      status: "not_covered"
      covering_test_cases: []
      gap_reason: "安全相关的极限测试尚未编写"
      recommended_urgent_tests:
        - id: "TC-AUTH-SEC-001"
          scenario: "第5次失败触发锁定"
          priority: "P0-Critical"
          
        - id: "TC-AUTH-SEC-002"
          scenario: "锁定期间拒绝登录"
          priority: "P0-Critical"
          
        - id: "TC-AUTH-SEC-003"
          scenario: "30分钟后自动解锁"
          priority: "P0-Critical"
          
  summary_statistics:
    by_status:
      fully_covered: 38 (84.4%)
      partially_covered: 4 (8.9%)
      not_covered: 3 (6.7%)
      
    by_risk_level:
      critical:
        total: 8
        covered: 6
        coverage: 75.0%
        gaps: ["REQ-AUTH-010", "REQ-AUTH-015"]
        
      high:
        total: 15
        covered: 14
        coverage: 93.3%
        gaps: ["REQ-AUTH-002 (partial)"]
        
      medium:
        total: 12
        covered: 12
        coverage: 100%
        
      low:
        total: 10
        covered: 10
        coverage: 100%
        
    by_category:
      validation: 95% (19/20)
      business_rule: 91% (10/11)
      security: 78% (7/9)
      performance: 100% (3/3)
      usability: 100% (2/2)
      
  action_items_from_verifier:
    immediate:
      - item: "为REQ-AUTH-010创建账户锁定测试 (P0)"
        assignee: "yongli_sheji_si"
        deadline: "2024-01-03"
        
    short_term:
      - item: "补充REQ-AUTH-002缺失的场景测试 (P1)"
        assignee: "yongli_sheji_si"
        deadline: "2024-01-08"
        
    feedback_to_yongli_sheji_si:
      message: "3个条款未被覆盖，其中2个为安全关键条款。请优先生成对应测试用例。"
      uncovered_clauses: ["REQ-AUTH-010", "REQ-AUTH-015", "REQ-AUTH-022"]
```

---

## 与MARC资源协调器的资源需求

```yaml
marc_resource_requirements:
  compute_resources:
    cpu_cores: 2
    memory_gb: 4
    disk_space_gb: 10  # HTML reports can be large
    
  execution_time:
    data_collection: "< 30 seconds (during test execution)"
    analysis_processing: "< 2 minutes"
    report_generation: "< 1 minute"
    clause_mapping: "< 3 minutes"
    
  storage_requirements:
    raw_coverage_data:
      format: ["XML", "JSON"]
      retention_builds: 50
      estimated_size_per_build_mb: 5
      
    analysis_reports:
      location: "docs/testing/coverage_reports/"
      formats: ["Markdown", "JSON", "HTML"]
      retention_permanent: "latest + monthly snapshots"
      
    historical_trends:
      database: "SQLite or PostgreSQL"
      table: "coverage_history"
      retention_years: 2
      
  integrations:
    ci_cd_tools:
      - "GitHub Actions (coverage comment on PR)"
      - "CodeCov.io (coverage visualization)"
      - "SonarQube (quality gate integration)"
      
    notification_triggers:
      - "Coverage drops > 3% → Alert"
      - "Below threshold → Block merge option"
      - "Milestone reached → Celebrate 🎉"
```

---

## 协同调用接口

### 接口定义

| 接口名称 | 接口描述 | 调用方 |
|----------|----------|--------|
| `collect_coverage` | 采集覆盖率数据接口 | 执行管理司、CI流水线 |
| `analyze_coverage_gaps` | 分析覆盖缺口接口 | 门下省主流程、开发团队 |
| `calculate_clause_coverage` | 计算条款覆盖率接口 | 闭环验证器、用例设计司 |
| `generate_coverage_report` | 生成覆盖率报告接口 | 项目经理、质量门禁 |

### 调用示例

```bash
# 分析覆盖率并生成报告
python skillscripts/testing/coverage_analyzer.py \
  --input coverage.xml \
  --baseline .coverage_baseline.json \
  --include-clause-mapping \
  --sdd-spec docs/sdd/auth_spec.json \
  --output docs/testing/coverage_reports/$(date +%Y%m%d)/
```

---

## 版本历史

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| 1.0.0 | 2026-04-06 | 初始版本，包含完整的覆盖率采集、分析、缺口定位、条款映射能力 |
