---
name: celue_zhiding_si
description: 策略制定司，负责测试金字塔策略、覆盖率目标设定、测试环境规划。输出文档至docs/testing/test_strategy.md。
---

# 策略制定司技能指令

## 职责定义

策略制定司作为测试验证局的策略规划核心，承担以下职责：

| 职责类别 | 具体职责 | 关键产出 |
|----------|----------|----------|
| **策略制定** | 测试金字塔策略设计与优化 | 测试策略文档 |
| **目标设定** | 覆盖率指标与质量门禁设定 | 覆盖率目标配置 |
| **环境规划** | 测试环境架构与资源规划 | 环境规划方案 |
| **标准建立** | 测试规范与最佳实践制定 | 测试规范指南 |

---

## 核心概念

### 测试金字塔模型

```
        /\
       /  \     E2E Tests (10%)
      /    \    - 用户场景验证
     /------\   - 关键路径覆盖
    /  集成   \  - 跨服务交互
   /   测试    \
  /------------\ 单元测试 (70%)
 /   Unit      \
/     Tests     \
------------------
```

**各层特点：**

| 层级 | 占比 | 执行速度 | 成本 | 可靠性 | 维护成本 |
|------|------|----------|------|--------|----------|
| **单元测试** | 70% | 秒级 | 低 | 高 | 低 |
| **集成测试** | 20% | 分钟级 | 中 | 中 | 中 |
| **E2E测试** | 10% | 十分钟级 | 高 | 较低 | 高 |

---

## 工作流程

### 阶段一：项目分析与需求理解

```
项目启动或迭代开始
    ↓
[1] 业务需求分析
    ↓
[2] 技术架构评估
    ↓
[3] 风险识别与分级
    ↓
[4] 约束条件收集
    ↓
进入策略设计阶段
```

#### 项目分析检查清单

```yaml
project_analysis_checklist:
  business_context:
    - domain_type: ["电商", "金融", "社交", "企业应用"]
    - user_scale: ["<1K", "1K-100K", "100K-1M", ">1M"]
    - criticality_level: ["low", "medium", "high", "critical"]
    
  technical_architecture:
    - architecture_pattern: ["monolith", "microservices", "serverless"]
    - tech_stack: ["Python/Django", "Node.js/Express", "Java/Spring"]
    - database: ["PostgreSQL", "MySQL", "MongoDB", "Redis"]
    - external_apis_count: [0, 1-5, 5-20, >20]
    
  testing_constraints:
    - execution_environment: ["CI/CD only", "CI + local", "cloud-based"]
    - time_budget_per_build: ["<5min", "5-15min", "15-30min", ">30min"]
    - team_test_expertise: ["beginner", "intermediate", "advanced", "expert"]
    - legacy_code_percentage: ["<10%", "10-30%", "30-60%", ">60%"]
```

---

### 阶段二：测试策略设计

```
项目分析完成
    ↓
[1] 测试层级划分
    ↓
[2] 各层比例确定
    ↓
[3] 测试工具选型
    ↓
[4] 自动化程度规划
    ↓
[5] 策略文档编写
    ↓
输出测试策略文档
```

#### 测试策略模板

```yaml
test_strategy_template:
  document_info:
    version: "1.0.0"
    project_name: "{{project_name}}"
    last_updated: "{{date}}"
    author: "celue_zhiding_si"
    
  executive_summary: |
    本文档定义了{{project_name}}项目的测试策略，
    包括测试范围、方法、工具、资源和时间表。
    
  testing_philosophy:
    approach: "shift-left testing"
    principles:
      - "测试先行 (TDD)"
      - "自动化优先"
      - "持续测试"
      - "风险驱动"
      
  test_pyramid_configuration:
    unit_tests:
      percentage: 70
      target_coverage:
        line_coverage: 85
        branch_coverage: 80
        function_coverage: 90
      tools:
        python: "pytest + coverage.py"
        javascript: "Jest + Istanbul"
        java: "JUnit + JaCoCo"
      execution_time_target: "< 2 minutes"
      
    integration_tests:
      percentage: 20
      target_coverage:
        api_coverage: 90
        service_integration: 80
        database_operations: 85
      tools:
        api_testing: "Postman/Newman or pytest-requests"
        service_testing: "TestContainers or local services"
        contract_testing: "Pact or Spring Cloud Contract"
      execution_time_target: "< 8 minutes"
      
    e2e_tests:
      percentage: 10
      target_coverage:
        critical_user_journeys: 100
        happy_path_scenarios: 95
        error_scenarios: 80
      tools:
        web_ui: "Playwright/Cypress/Selenium"
        api_e2e: "Postman collections or custom scripts"
        mobile: "Appium or Detox"
      execution_time_target: "< 15 minutes"
      
  risk_based_prioritization:
    high_risk_areas:
      - authentication_and_authorization
      - payment_processing
      - personal_data_handling
      - data_integrity_operations
      
    medium_risk_areas:
      - business_logic
      - third_party_integrations
      - reporting_features
      
    low_risk_areas:
      - ui_polishing
      - logging_and_monitoring
      - configuration_options
      
  automation_strategy:
    automated:
      - unit_tests: 100%
      - integration_tests: 95%
      - smoke_tests: 100%
      - regression_tests: 90%
      
    manual:
      - exploratory_testing: 100%
      - usability_testing: 80%
      - accessibility_testing: 50%
      - visual_regression: 30%
      
  quality_gates:
    pre_commit:
      - unit_tests_pass: true
      - linting_pass: true
      - no_security_issues: true
      
    pre_push:
      - unit_coverage_threshold: 80
      - integration_tests_pass: true
      - no_regression: true
      
    pre_merge:
      - full_suite_pass: true
      - coverage_targets_met: true
      - performance_baselines_met: true
      
    pre_release:
      - e2e_tests_pass: true
      - security_scan_clean: true
      - load_test_passed: true
```

#### 测试策略文档输出格式（Markdown）

```markdown
# {{project_name}} 测试策略文档

**版本**: {{version}}  
**日期**: {{last_updated}}  
**制定者**: 策略制定司  

---

## 📋 文档目的

本文档定义了{{project_name}}项目的完整测试策略，包括：
- 测试范围和目标
- 测试方法和层级
- 工具和技术栈
- 资源需求和时间表
- 质量标准和门禁

## 🎯 测试目标

### 主要目标
- 缺陷发现效率提升 **40%**
- 回归测试时间减少 **60%**
- 生产缺陷率降低 **70%**
- 代码覆盖率维持在 **85%+**

### SMART目标
| 目标 | 指标 | 目标值 | 时间框架 |
|------|------|--------|----------|
| 单元测试覆盖率 | 行覆盖率 | ≥85% | 每次提交 |
| 集成测试通过率 | 通过率 | 100% | 每次构建 |
| E2E测试执行时间 | 执行时长 | <15分钟 | 每次发布 |
| 自动化率 | 自动化占比 | ≥90% | Q2结束 |

## 📐 测试金字塔

### 层级分布
- **单元测试**: 70%（快速、可靠、低成本）
- **集成测试**: 20%（服务间交互验证）
- **E2E测试**: 10%（端到端业务流程）

### 各层详细说明

#### 1️⃣ 单元测试层
**目标**: 验证单个函数/方法的正确性

**范围**:
- ✅ 所有业务逻辑函数
- ✅ 数据转换和处理
- ✅ 工具类和辅助函数
- ❌ 不涉及外部依赖

**工具栈**:
- Python: pytest + pytest-cov + coverage.py
- JavaScript: Jest + @jest/globals
- Java: JUnit 5 + Mockito

**示例**:
\`\`\`python
# tests/unit/services/test_user_service.py
def test_create_user_success():
    # Given
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "SecurePass123!"
    }
    mock_repo = Mock()
    service = UserService(mock_repo)
    
    # When
    result = service.create_user(user_data)
    
    # Then
    assert result.username == "testuser"
    assert result.is_active is True
    mock_repo.save.assert_called_once()
\`\`\`

#### 2️⃣ 集成测试层
**目标**: 验证组件间的协作正确性

**范围**:
- API端点测试
- 数据库操作测试
- 外部服务集成测试
- 缓存机制测试

**工具栈**:
- API测试: pytest-requests + responses
- 数据库: pytest-postgresql + factory-boy
- 服务集成: TestContainers

**示例**:
\`\`\`python
# tests/integration/api/test_user_api.py
def test_create_user_endpoint(client, db_session):
    # Given
    payload = {
        "username": "newuser",
        "email": "new@example.com"
    }
    
    # When
    response = client.post("/api/users", json=payload)
    
    # Then
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "newuser"
    # Verify database record created
    user = db_session.query(User).filter_by(username="newuser").first()
    assert user is not None
\`\`\`

#### 3️⃣ E2E测试层
**目标**: 验证完整的用户旅程

**关键场景**:
- 用户注册登录流程
- 核心业务操作流程
- 支付结算流程
- 数据导出流程

**工具栈**:
- Web UI: Playwright
- API E2E: Postman Newman

**示例**:
\`\`\`typescript
// e2e/tests/user-journey.spec.ts
import { test, expect } from '@playwright/test';

test('complete user registration journey', async ({ page }) => {
  // Navigate to registration page
  await page.goto('/register');
  
  // Fill registration form
  await page.fill('#username', 'testuser');
  await page.fill('#email', 'test@example.com');
  await page.fill('#password', 'SecurePass123!');
  await page.click('button[type="submit"]');
  
  // Verify successful registration
  await expect(page).toHaveURL('/dashboard');
  await expect(page.locator('.welcome-message')).toContainText('Welcome, testuser!');
});
\`\`\`

## 🔧 工具链配置

### CI/CD集成
\`\`\`yaml
# .github/workflows/test.yml
name: Test Suite

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt -r requirements-dev.txt
      - name: Run unit tests
        run: |
          pytest tests/unit/ \
            --cov=src \
            --cov-report=xml \
            --cov-fail-under=80 \
            -v
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        
  integration-tests:
    runs-on: ubuntu-latest
    needs: unit-tests
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v3
      - name: Run integration tests
        env:
          DATABASE_URL: postgresql://postgres:test@localhost:5432/testdb
        run: pytest tests/integration/ -v --tb=short
        
  e2e-tests:
    runs-on: ubuntu-latest
    needs: integration-tests
    steps:
      - uses: actions/checkout@v3
      - name: Run E2E tests
        run: npx playwright test e2e/
\`\`\`

## 📊 质量门禁

### 门禁规则
| 阶段 | 规则 | 阈值 | 阻塞性 |
|------|------|------|--------|
| Pre-commit | Linting通过 | 0 errors | ✅ 是 |
| Pre-commit | 单元测试 | 100% pass | ✅ 是 |
| Pre-push | 行覆盖率 | ≥80% | ✅ 是 |
| Pre-push | 分支覆盖率 | ≥75% | ⚠️ 警告 |
| PR Merge | 全套测试通过 | 100% pass | ✅ 是 |
| PR Merge | 总覆盖率 | ≥85% | ✅ 是 |
| Release | E2E测试 | 100% pass | ✅ 是 |
| Release | 安全扫描 | 0 critical | ✅ 是 |

## 👥 资源规划

### 团队角色
| 角色 | 职责 | 配置建议 |
|------|------|----------|
| 测试架构师 | 策略制定、工具选型 | 1人 |
| 自动化工程师 | 测试开发、CI维护 | 2人 |
| 手动测试师 | 探索性测试、UAT | 1人 |

### 基础设施需求
- CI构建机器: 3台（并行执行）
- 测试数据库: PostgreSQL 15
- 测试环境: Staging环境
- 浏览器: Chrome, Firefox, Safari

## 📈 度量与改进

### 关键指标
| 指标 | 当前基线 | 目标 | 测量方式 |
|------|----------|------|----------|
| 缺陷逃逸率 | 15% | <5% | 生产bug/总bug |
| 测试执行时间 | 25min | <15min | CI流水线耗时 |
| 自动化率 | 65% | >90% | 自动化用例/总用例 |
| 代码覆盖率 | 78% | >85% | coverage工具 |
| 平均修复时间(MTTR) | 4h | <2h | issue追踪系统 |

### 改进计划
- **Q1**: 提升单元测试覆盖率至85%
- **Q2**: 实现E2E测试自动化率达90%
- **Q3**: 建立性能测试基准线
- **Q4**: 引入混沌工程测试

---

**文档审批**:  
- 制定者: 策略制定司  
- 审核: 测试验证局局长  
- 批准: 门下省审议官  
- 生效日期: {{effective_date}}
```

---

### 阶段三：覆盖率目标设定

```
策略设计完成
    ↓
[1] 基线数据收集
    ↓
[2] 行业对标分析
    ↓
[3] 分阶段目标设定
    ↓
[4] 覆盖率工具配置
    ↓
[5] 门禁阈值确定
    ↓
输出覆盖率配置文件
```

#### 覆盖率目标配置

```yaml
coverage_targets:
  global:
    line_coverage:
      current: 78
      target: 85
      stretch_goal: 90
      deadline: "2024-03-31"
      
    branch_coverage:
      current: 72
      target: 80
      stretch_goal: 85
      deadline: "2024-03-31"
      
    function_coverage:
      current: 82
      target: 90
      stretch_goal: 95
      deadline: "2024-03-31"
      
  by_module:
    core_business_logic:
      line_coverage: 95
      branch_coverage: 90
      priority: "critical"
      
    authentication:
      line_coverage: 98
      branch_coverage: 95
      priority: "critical"
      
    payment_processing:
      line_coverage: 99
      branch_coverage: 97
      priority: "critical"
      
    utility_functions:
      line_coverage: 80
      branch_coverage: 75
      priority: "normal"
      
    configuration:
      line_coverage: 70
      branch_coverage: 65
      priority: "low"
      
  exclusion_rules:
    paths:
      - "__pycache__/**"
      - "migrations/**"
      - "**/tests/**"
      - "**/*_test.py"
      - "**/*.spec.ts"
      
    patterns:
      - "if __name__ == '__main__':"
      - "raise NotImplementedError()"
      - "# pragma: no cover"
      
  quality_gates:
    pre_commit:
      new_code_line_coverage: 80
      changed_files_only: true
      
    pr_merge:
      overall_line_coverage: 82
      minimum_file_coverage: 60
      allow_degradation: false
      
    release:
      overall_line_coverage: 85
      critical_modules_coverage: 95
```

---

### 阶段四：测试环境规划

```
覆盖率目标设定完成
    ↓
[1] 环境拓扑设计
    ↓
[2] 资源需求估算
    ↓
[3] 数据管理策略
    ↓
[4] 环境隔离方案
    ↓
[5] 运维自动化规划
    ↓
输出环境规划方案
```

#### 测试环境架构

```yaml
test_environment_architecture:
  environments:
    local_development:
      purpose: "开发者日常测试"
      characteristics:
        - fast_feedback
        - full_debugging_capability
        - mocked_external_services
      infrastructure:
        - "Local PostgreSQL instance"
        - "In-memory Redis"
        - "Mock APIs via wiremock"
        
    ci_cd:
      purpose: "自动化流水线测试"
      characteristics:
        - deterministic and reproducible
        - isolated per build
        - parallel execution support
      infrastructure:
        - "GitHub Actions runners"
        - "Docker containers for services"
        - "TestContainers for databases"
      specs:
        runners: 3
        parallel_jobs: 6
        estimated_build_time: "12 minutes"
        
    staging:
      purpose: "预发布验证"
      characteristics:
        - production-like configuration
        - real external integrations (sandbox)
        - performance testing capable
      infrastructure:
        - "Managed Kubernetes cluster"
        - "Production database clone (anonymized)"
        - "Sandbox payment gateway"
      specs:
        replicas: 2
        auto_scaling: true
        monitoring: "full observability stack"
        
    performance:
      purpose: "负载和压力测试"
      characteristics:
        - scalable infrastructure
        - realistic traffic simulation
        - detailed metrics collection
      infrastructure:
        - "Load generator (k6/Locust)"
        - "Monitoring (Grafana/Prometheus)"
        - "APM (Datadog/New Relic)"
      specs:
        max_vusers: 10000
        test_duration: "30 minutes"
        ramp_up_strategy: "exponential"
        
  data_management:
    strategy: "synthetic + anonymized production subset"
    
    synthetic_data:
      generators:
        - "Faker library for PII"
        - "Factory Boy for ORM objects"
        - "Custom generators for business entities"
      volume_per_test: "100-1000 records"
      refresh_policy: "per test (isolated)"
      
    production_subset:
      source: "production backup (weekly)"
      anonymization_rules:
        - email: "hash + preserve format"
        - phone: "random valid format"
        - name: "fake names from dictionary"
        - financial_data: "scaled random values"
      volume: "10% of production data"
      usage: "staging environment only"
      
  environment_isolation:
    strategy: "namespace + resource naming conventions"
    
    rules:
      - "Each test suite gets unique database schema"
      - "Redis use separate DB numbers (0-15)"
      - "File storage use timestamped directories"
      - "External APIs use request-specific headers"
      
  cost_optimization:
    strategies:
      - "Spot/preemptible instances for non-critical tests"
      - "Parallel test execution to reduce total runtime"
      - "Smart caching of dependencies and test fixtures"
      - "Environment scaling based on pipeline triggers"
    target_cost_reduction: "40% vs always-on environments"
```

---

## 与MARC资源协调器的资源需求

```yaml
marc_resource_requirements:
  compute_resources:
    cpu_cores: 2
    memory_gb: 4
    disk_space_gb: 5
    
  execution_time:
    strategy_generation: "< 10 minutes"
    document_generation: "< 5 minutes"
    
  knowledge_base_access:
    required_templates:
      - "test_strategy_template.yaml"
      - "coverage_config_template.yaml"
      - "environment_spec_template.yaml"
    industry_benchmarks:
      - "testing_pyramid_best_practices"
      - "coverage_standards_by_domain"
      
  output_storage:
    location: "docs/testing/"
    files:
      - "test_strategy.md"
      - "coverage_config.yaml"
      - "environment_plan.md"
    retention: "permanent (living document)"
    
  collaboration_requirements:
    stakeholders:
      - "development_team_lead"
      - "qa_manager"
      - "devops_engineer"
      - "product_owner"
    approval_workflow: true
```

---

## 协同调用接口

### 接口定义

| 接口名称 | 接口描述 | 调用方 |
|----------|----------|--------|
| `create_test_strategy` | 创建测试策略文档接口 | 门下省主流程、项目管理员 |
| `set_coverage_targets` | 设定覆盖率目标接口 | 覆盖分析司、门禁把控司 |
| `plan_test_environment` | 规划测试环境接口 | 执行管理司、DevOps团队 |
| `update_strategy` | 更新测试策略接口 | 定期审查触发 |

### 调用示例

```bash
# 生成测试策略文档
python skillscripts/testing/strategy_generator.py \
  --project-name "user-management-system" \
  --tech-stack "python/django" \
  --architecture "monolith" \
  --risk-level "high" \
  --output docs/testing/test_strategy.md
```

---

## 版本历史

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| 1.0.0 | 2026-04-06 | 初始版本，包含完整的测试策略制定能力 |
