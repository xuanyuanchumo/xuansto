---
name: zhixing_guanli_si
description: 执行管理司，负责测试执行调度、并行测试管理、Flaky test处理。工具集成pytest/Jest/Cypress。
---

# 执行管理司技能指令

## 职责定义

执行管理司作为测试验证局的执行控制核心，承担以下职责：

| 职责类别 | 具体职责 | 关键产出 |
|----------|----------|----------|
| **执行调度** | 测试任务分配与调度策略 | 执行计划 |
| **并行管理** | 并行测试执行与资源优化 | 并行配置 |
| **Flaky处理** | 不稳定测试识别、隔离和修复指导 | Flaky报告 |
| **结果收集** | 测试结果汇总与分析 | 执行报告 |

---

## 工具集成

### 核心测试执行工具

| 工具 | 用途 | 语言/框架 |
|------|------|-----------|
| **pytest** | Python测试框架与执行器 | Python |
| **Jest** | JavaScript测试框架 | JS/TS |
| **Cypress** | E2E Web应用测试 | Web |
| **Playwright** | 现代化浏览器自动化 | Web |
| **pytest-xdist** | pytest并行执行扩展 | Python |

### 工具配置模板

```yaml
tool_configurations:
  pytest:
    config_file: "pytest.ini"
    key_options:
      - "-v"  # 详细输出
      - "--tb=short"  # 简短traceback
      - "-x"  # 首次失败停止 (可选)
      - "--cov=src"  # 覆盖率
      - "--cov-report=term-missing"  # 显示未覆盖行
      - "-n auto"  # 自动检测CPU核心数进行并行
      
    ini_config: |
      [pytest]
      testpaths = tests
      python_files = test_*.py *_test.py
      python_classes = Test*
      python_functions = test_*
      addopts = -v --tb=short --strict-markers
      markers =
          slow: marks tests as slow (deselect with '-m "not slow"')
          integration: marks tests as integration tests
          e2e: marks as end-to-end tests
          flaky: marks known flaky tests
      filterwarnings =
          ignore::DeprecationWarning
          
  jest:
    config_file: "jest.config.js"
    key_features:
      - "parallel execution"
      - "snapshot testing"
      - "coverage collection"
      
    config_template: |
      module.exports = {
        preset: 'ts-jest',
        testEnvironment: 'node',
        roots: ['<rootDir>/tests'],
        testMatch: ['**/*.test.ts', '**/*.spec.ts'],
        collectCoverageFrom: [
          'src/**/*.{ts,tsx}',
          '!src/**/*.d.ts',
          '!src/index.ts'
        ],
        coverageThreshold: {
          global: {
            branches: 80,
            functions: 85,
            lines: 85,
            statements: 85
          }
        },
        maxWorkers: '50%',
        testTimeout: 10000
      };
      
  cypress:
    config_file: "cypress.config.js"
    key_features:
      - "E2E testing"
      - "visual regression"
      - "network stubbing"
      
    config_template: |
      const { defineConfig } = require('cypress');
      
      module.exports = defineConfig({
        e2e: {
          baseUrl: 'http://localhost:3000',
          specPattern: 'e2e/**/*.cy.{js,ts}',
          viewportWidth: 1280,
          viewportHeight: 720,
          video: false,
          screenshotOnFailure: true,
          defaultCommandTimeout: 10000,
          requestTimeout: 10000,
          responseTimeout: 10000,
          retries: {
            runMode: 2,
            openMode: 0
          }
        }
      });
```

---

## 工作流程

### 阶段一：测试执行准备

```
收到测试执行请求
    ↓
[1] 执行环境检查
    ↓
[2] 测试依赖安装验证
    ↓
[3] 数据库/服务状态确认
    ↓
[4] 测试数据准备
    ↓
[5] 执行计划生成
    ↓
进入测试执行阶段
```

#### 环境健康检查清单

```yaml
environment_health_check:
  infrastructure:
    - check: "CPU可用性 > 20%"
      command: "top -bn1 | grep 'Cpu(s)'"
      threshold: "idle > 20"
      
    - check: "内存可用 > 2GB"
      command: "free -m"
      threshold: "available > 2048"
      
    - check: "磁盘空间 > 5GB"
      command: "df -h /"
      threshold: "available > 5G"
      
  services:
    - check: "PostgreSQL可达"
      command: "pg_isready -h localhost -p 5432"
      timeout: "5 seconds"
      
    - check: "Redis可达"
      command: "redis-cli ping"
      expected_response: "PONG"
      
    - check: "应用服务启动"
      command: "curl -sf http://localhost:3000/health"
      timeout: "10 seconds"
      
  test_dependencies:
    - check: "Python依赖完整"
      command: "pip check"
      
    - check: "Node.js依赖完整"
      command: "npm ls --depth=0"
      
  data_readiness:
    - check: "测试数据库可写"
      action: "INSERT test record and DELETE"
      
    - check: "测试 fixtures 可用"
      action: "Verify fixture files exist"
```

---

### 阶段二：测试执行调度

```
环境准备完成
    ↓
[1] 测试套件分析
    ↓
[2] 依赖关系解析
    ↓
[3] 执行顺序优化
    ↓
[4] 资源分配
    ↓
[5] 并行度计算
    ↓
开始执行测试
```

#### 智能调度算法

```yaml
scheduling_algorithm:
  strategy: "priority + dependency + parallelism aware"
  
  priority_weights:
    critical_path_tests: 0.35
    recently_changed: 0.25
    failure_history: 0.20
    execution_time: 0.10
    resource_requirements: 0.10
    
  scheduling_rules:
    rule_1_critical_first:
      description: "关键路径和高优先级测试优先执行"
      condition: "test.marked_as('critical') or test.in_critical_path"
      action: "schedule_in_first_batch"
      
    rule_2_dependency_order:
      description: "有依赖关系的测试按拓扑序执行"
      condition: "test.has_dependencies"
      action: "execute_after_dependencies_complete"
      
    rule_3_parallel_safe:
      description: "无共享状态的测试可以并行执行"
      condition: "test.is_isolated and no_shared_resources"
      action: "assign_to_worker_pool"
      
    rule_4_flaky_quarantine:
      description: "已知flaky的测试单独执行并重试"
      condition: "test.marked_as('flaky')"
      action: "execute_with_retries in isolated environment"
      
  parallel_execution_config:
    worker_count_detection:
      method: "auto"
      formula: "min(cpu_count, max_workers_configured)"
      default_max_workers: 8
      
    load_balancing:
      strategy: "work_stealing"
      description: "空闲worker从繁忙worker偷取任务"
      
    resource_constraints:
      database_connections_per_worker: 5
      memory_per_worker_mb: 512
      port_ranges_per_worker: "20000-20100"
```

#### 执行计划输出格式

```json
{
  "execution_plan_id": "EXEC-PLAN-001",
  "timestamp": "2024-01-01T00:00:00Z",
  "trigger": "pull_request",
  "pr_number": 123,
  "branch": "feature/user-auth",
  
  "environment": {
    "os": "Ubuntu 22.04",
    "python_version": "3.11.0",
    "node_version": "18.17.0",
    "cpu_cores": 8,
    "memory_gb": 16,
    "workers_allocated": 6
  },
  
  "test_inventory": {
    "total_test_count": 245,
    "by_type": {
      "unit_tests": 180,
      "integration_tests": 45,
      "e2e_tests": 15,
      "performance_tests": 5
    },
    "by_marker": {
      "critical": 35,
      "slow": 20,
      "flaky": 3,
      "skip": 2
    },
    "estimated_duration_seconds": {
      "sequential": 480,
      "parallel_optimal": 95,
      "with_cache": 65
    }
  },
  
  "execution_schedule": {
    "phase_1_critical_unit":
      start_time: "T+0s",
      duration_seconds: 30,
      tests_count: 35,
      workers: 6,
      parallelism: true,
      description: "Critical unit tests first for fast feedback"
    
    phase_2_remaining_unit:
      start_time: "T+30s",
      duration_seconds: 40,
      tests_count: 145,
      workers: 6,
      parallelism: true
    
    phase_3_integration:
      start_time: "T+70s",
      duration_seconds: 35,
      tests_count: 45,
      workers: 4,
      parallelism: true,
      requires_database: true
    
    phase_4_e2e:
      start_time: "T+105s",
      duration_seconds: 120,
      tests_count: 15,
      workers: 3,
      parallelism: true,
      requires_browser: true
    
    phase_5_flaky_retry:
      start_time: "T+225s",
      duration_seconds: 60,
      tests_count: 3,
      workers: 1,
      parallelism: false,
      retry_count: 3
  },
  
  "total_estimated_duration": "285 seconds (~4.75 minutes)",
  "optimization_applied": [
    "Test ordering by failure probability",
    "Parallel execution with 6 workers",
    "Database fixture sharing",
    "Selective re-run based on changes"
  ]
}
```

---

### 阶段三：并行测试管理与监控

```
测试开始执行
    ↓
[1] Worker进程启动与管理
    ↓
[2] 任务分发与负载均衡
    ↓
[3] 实时进度监控
    ↓
[4] 资源使用监控
    ↓
[5] 异常处理与恢复
    ↓
[6] 结果收集与合并
    ↓
输出执行日志与中间结果
```

#### 并行执行监控仪表板

```yaml
realtime_monitoring_dashboard:
  metrics_collected:
    execution_progress:
      - metric: "tests_completed"
        type: "counter"
        display: "progress_bar"
        
      - metric: "tests_failed"
        type: "counter"
        display: "alert_badge"
        
      - metric: "current_phase"
        type: "enum"
        values: ["unit", "integration", "e2e", "cleanup"]
        
    performance_metrics:
      - metric: "tests_per_second"
        type: "gauge"
        display: "speedometer"
        
      - metric: "average_test_duration_ms"
        type: "histogram"
        display: "line_chart"
        
      - metric: "worker_utilization_percent"
        type: "gauge"
        range: [0, 100]
        
    resource_metrics:
      - metric: "cpu_usage_percent"
        type: "gauge"
        alert_threshold: 90
        
      - metric: "memory_usage_mb"
        type: "gauge"
        alert_threshold: "14GB (of 16GB)"
        
      - metric: "database_connection_pool_size"
        type: "gauge"
        range: [0, 50]
        
  alerting_rules:
    - name: "test_execution_stalled"
      condition: "no_progress_for > 60 seconds"
      severity: "warning"
      action: "check_worker_logs, consider restart"
      
    - name: "resource_exhaustion"
      condition: "cpu > 95% or memory > 90% for > 30 seconds"
      severity: "critical"
      action: "pause new tests, scale workers down"
      
    - name: "failure_rate_spike"
      condition: "failure_rate > 20% in last 50 tests"
      severity: "warning"
      action: "investigate common failure pattern"
      
  log_levels:
    debug: "Individual test start/end"
    info: "Phase transitions, summary statistics"
    warning: "Slow tests (>10s), retries"
    error: "Test failures, worker crashes"
```

---

### 阶段四：Flaky Test处理

```
测试执行中或完成后
    ↓
[1] Flaky模式识别（间歇性失败）
    ↓
[2] 失败历史分析
    ↓
[3] 根因分类
    ↓
[4] 隔离与标记
    ↓
[5] 修复建议生成
    ↓
[6] 修复验证跟踪
    ↓
输出Flaky Test报告
```

#### Flaky Test检测机制

```yaml
flaky_detection_mechanism:
  detection_criteria:
    intermittent_failure:
      definition: "同一测试在不同执行中有时通过有时失败，无代码变更"
      threshold: "failed at least 2 times in last 10 runs"
      pattern: "pass-fail-pass or fail-pass-fail"
      
    timing_dependent:
      definition: "测试对执行时间或顺序敏感"
      indicators:
        - "passes when run alone but fails in suite"
        - "fails under heavy load but passes normally"
        - "timing-related assertions too strict"
        
    state_leakage:
      definition: "测试间存在共享状态污染"
      indicators:
        - "fails after specific other tests"
        - "passes when execution order changed"
        - "global state modified not cleaned up"
        
    external_dependency:
      definition: "依赖外部服务或资源不稳定"
      indicators:
        - "network timeout failures"
        - "database connection issues"
        - "file system race conditions"
        
  classification_taxonomy:
    async_race_condition:
      symptoms: ["TimeoutError", "AssertionError on timing", "intermittent state"]
      common_causes:
        - "Missing await/async handling"
        - "Insufficient wait time"
        - "Callback order assumptions"
      fix_patterns:
        - "Add proper async/await"
        - "Use explicit waits instead of fixed delays"
        - "Implement proper synchronization"
        
    shared_state_pollution:
      symptoms: ["Passes alone, fails in suite", "Order-dependent failures"]
      common_causes:
        - "Global variable modification"
        - "Singleton state not reset"
        - "Database records not cleaned"
      fix_patterns:
        - "Use pytest fixtures with scope='function'"
        - "Implement proper teardown/cleanup"
        - "Isolate database transactions"
        
    assertion_too_strict:
      symptoms: ["Intermittent assertion failures on timing/count"]
      common_causes:
        - "Exact match on floating point numbers"
        - "Exact count of async operations"
        - "Timestamp comparisons without tolerance"
      fix_patterns:
        - "Use approximate equality (pytest.approx)"
        - "Add tolerance ranges to assertions"
        - "Use relative time comparisons"
        
    resource_contention:
      symptoms: ["Port already in use", "Connection pool exhausted", "File locked"]
      common_causes:
        - "Hardcoded port numbers"
        - "Insufficient connection pool size"
        - "Missing cleanup of temp resources"
      fix_patterns:
        - "Use dynamic port allocation"
        - "Increase pool sizes or use pooling wisely"
        - "Ensure proper resource cleanup in finally blocks"
```

#### Flaky Test报告格式

```json
{
  "flaky_report_id": "FLAKY-001",
  "timestamp": "2024-01-01T00:00:00Z",
  "analysis_period": {
    "start": "2024-01-01T00:00:00Z",
    "end": "2024-01-07T23:59:59Z",
    "total_executions": 50
  },
  
  "summary": {
    "total_tests_analyzed": 245,
    "flaky_tests_identified": 5,
    "flaky_rate_percent": 2.04,
    "flakiness_trend": "improving (-0.5% vs previous week)",
    "impact_on_ci": "12 builds affected by flaky failures"
  },
  
  "flaky_tests_detail": [
    {
      "test_id": "FLAKY-TEST-001",
      "test_name": "test_user_login_with_oauth_callback",
      "file_path": "tests/integration/auth/test_oauth.py",
      "line_number": 145,
      
      "failure_history": {
        "total_runs": 50,
        "pass_count": 42,
        "fail_count": 8,
        "flake_rate": 16.0,
        "recent_runs": ["PASS", "FAIL", "PASS", "PASS", "FAIL", "PASS", "PASS", "PASS", "FAIL", "PASS"],
        "first_seen": "2023-12-15",
        "last_failure": "2024-01-05"
      },
      
      "classification": {
        "primary_category": "external_dependency",
        "secondary_category": "timing_sensitive",
        "confidence": 0.85,
        "symptoms": [
          "requests.exceptions.ConnectionError: Max retries exceeded",
          "Intermittent OAuth provider timeouts"
        ]
      },
      
      "root_cause_analysis": {
        "likely_cause": "OAuth mock server occasionally slow to respond during CI load spikes",
        "evidence": [
          "Failures correlate with high CI queue times",
          "Timeout error message consistent across failures",
          "Always passes when run locally with dedicated mock"
        ],
        "affected_components": ["oauth_mock_server", "CI_infrastructure"]
      },
      
      "recommended_fixes": [
        {
          "priority": "high",
          "approach": "Increase timeout and add retry logic",
          "code_change": |
            @pytest.fixture
            def oauth_mock_server():
                server = OAuthMockServer(timeout=30)  # Increased from 10
                server.start()
                yield server
                server.stop()
            
            def test_user_login_with_oauth_callback(oauth_mock_server):
                # Add retry wrapper for resilience
                result = oauth_mock_server.simulate_callback_with_retry(
                    max_attempts=3,
                    delay=1.0
                )
                assert result.status == "success"
          ,
          "effort_estimate_hours": 2,
          "expected_flake_reduction": "90%"
        },
        {
          "priority": "medium",
          "approach: "Mark as flaky with automatic retry until fixed",
          "code_change": |
            import pytest
            
            @pytest.mark.flaky(reruns=3, reruns_delay=2)
            def test_user_login_with_oauth_callback(oauth_mock_server):
                # ... existing test code ...
          ,
          "effort_estimate_hours": 0.5,
          "expected_improvement": "Reduce CI noise while permanent fix is developed"
        }
      ],
      
      "status": "open",
      "assigned_to": "Backend Team",
      "due_date": "2024-01-12",
      "blocks_merge": false
    },
    {
      "test_id": "FLAKY-TEST-002",
      "test_name": "test_concurrent_order_processing",
      "file_path": "tests/integration/orders/test_concurrency.py",
      "line_number": 78,
      
      "failure_history": {
        "total_runs": 50,
        "pass_count": 38,
        "fail_count": 12,
        "flake_rate": 24.0,
        "pattern": "order_dependent"
      },
      
      "classification": {
        "primary_category": "shared_state_pollution",
        "symptoms": [
          "Fails when run after test_create_large_order",
          "AssertionError: Expected 10 orders, got 11"
        ]
      },
      
      "recommended_fixes": [
        {
          "approach": "Isolate test data with unique identifiers",
          "code_change": |
            @pytest.fixture(autouse=True)
            def isolate_order_data(db_session):
                # Use transaction-level isolation
                db_session.begin_nested()
                yield
                db_session.rollback()
                
            def test_concurrent_order_processing():
                user_id = f"test_user_{uuid.uuid4().hex[:8]}"
                # ... rest of test uses unique user_id
          ,
          "effort_estimate_hours": 3
        }
      ]
    }
  ],
  
  "action_items": [
    {
      "item": "Fix FLAKY-001 OAuth timeout issue",
      "priority": "high",
      "deadline": "2024-01-12",
      "owner": "Backend Team"
    },
    {
      "item": "Fix FLAKY-002 shared state pollution",
      "priority": "high",
      "deadline": "2024-01-10",
      "owner": "Backend Team"
    },
    {
      "item": "Add flaky detection to CI pipeline",
      "priority": "medium",
      "deadline": "2024-01-15",
      "owner": "DevOps Team"
    }
  ],
  
  "metrics_and_trends": {
    "flaky_rate_over_time": [
      {"week": "2023-W50", "rate": 3.5},
      {"week": "2023-W51", "rate": 3.2},
      {"week": "2023-W52", "rate": 2.8},
      {"week": "2024-W01", "rate": 2.54}
    ],
    "ci_builds_affected_by_flakes": {
      "this_week": 12,
      "previous_week": 18,
      "trend": "decreasing ✓"
    },
    "mean_time_to_fix_flaky_hours": 8.5
  }
}
```

---

### 阶段五：执行报告生成

```
所有测试执行完成
    ↓
[1] 结果数据汇总
    ↓
[2] 通过/失败统计
    ↓
[3] 性能指标计算
    ↓
[4] 趋势对比分析
    ↓
[5] 报告生成与发布
    ↓
输出综合执行报告
```

#### 综合执行报告格式

```markdown
# 测试执行报告

**报告编号**: EXEC-RPT-20240101-001  
**执行时间**: 2024-01-01 14:30:00 - 14:35:15  
**总耗时**: 5分15秒  
**触发**: PR #123  

---

## 📊 执行摘要

### 总体结果: ✅ 通过 (With Warnings)

| 指标 | 数值 | 目标 | 状态 |
|------|------|------|------|
| 总测试数 | 245 | - | - |
| 通过 | 237 | - | ✅ |
| 失败 | 5 | 0 | ❌ |
| 跳过 | 3 | - | ⏭️ |
| 错误 | 0 | 0 | ✅ |
| 通过率 | 96.7% | ≥95% | ✅ |
| 执行时间 | 5m 15s | <10m | ✅ |

### 关键发现

- 🔴 **5个测试失败**需要关注（其中2个为已知flaky）
- 🟡 **3个已知flaky测试**已自动重试并通过
- ✅ **覆盖率达标**: 行覆盖率86.2%，分支覆盖率81.5%
- ⚡ **性能良好**: 平均测试用时1.29秒

---

## 📈 详细结果

### 按类型统计

| 类型 | 总数 | 通过 | 失败 | 跳过 | 耗时 | 覆盖率 |
|------|------|------|------|------|------|--------|
| 单元测试 | 180 | 178 | 2 | 0 | 1m 45s | 88.5% |
| 集成测试 | 45 | 43 | 1 | 1 | 2m 10s | 82.3% |
| E2E测试 | 15 | 15 | 0 | 2 | 1m 15s | N/A |
| 性能测试 | 5 | 5 | 0 | 0 | 0m 5s | N/A |

### 失败测试详情

#### 1. ❌ test_create_user_duplicate_email [单元]
- **文件**: `tests/unit/services/test_user_service.py:156`
- **错误**: `AssertionError: Expected DuplicateError but got None`
- **首次失败**: 本次运行
- **历史**: 从未失败过
- **可能原因**: 新引入的回归问题
- **优先级**: P0

#### 2. ❌ test_order_total_calculation [单元]
- **文件**: `tests/unit/services/test_order_service.py:89`
- **错误**: `AssertionError: Expected 99.98 but got 99.97000000000001`
- **分析**: 浮点精度问题
- **优先级**: P2 (修复断言即可)

#### 3. ❌ test_payment_webhook_timeout [集成]
- **文件**: `tests/integration/payment/test_webhook.py:234`
- **错误**: `ConnectionError: Payment service unavailable`
- **分析**: 外部依赖超时（非代码问题）
- **优先级**: P3 (基础设施)

---

## ⚠️ Flaky Test 监控

| 测试名称 | 本周失败率 | 上周失败率 | 趋势 | 状态 |
|----------|------------|------------|------|------|
| test_oauth_callback | 16% | 22% | ↓ 改善 | 🔄 修复中 |
| test_concurrent_orders | 24% | 28% | ↓ 改善 | 🔄 修复中 |
| test_file_upload_large | 10% | 8% | ↑ 恶化 | 🆕 新发现 |

---

## 📊 性能指标

### 执行效率

| 指标 | 数值 | 基线 | 状态 |
|------|------|------|------|
| 总执行时间 | 5m 15s | 8m | ✅ 快34% |
| 并行度 | 6 workers | 4 workers | ✅ 提升50% |
| 吞吐量 | 47 tests/min | 30 tests/min | ✅ 提升57% |
| Worker利用率 | 78% | 70% | ✅ 优化 |

### 慢速测试 Top 5

| 排名 | 测试名称 | 耗时 | 类型 | 建议 |
|------|----------|------|------|------|
| 1 | test_full_checkout_flow | 28.5s | E2E | 考虑拆分 |
| 2 | test_bulk_import_1000_items | 18.2s | 集成 | 减少数据量 |
| 3 | test_report_generation_pdf | 12.8s | 集合 | Mock PDF生成 |
| 4 | test_search_with_filters | 8.5s | E2E | 优化查询 |
| 5 | test_email_sending_flow | 7.2s | 集成 | 使用Mailhog |

---

## 📉 趋势对比

### 与上次执行对比 (PR #122)

| 指标 | 本次 | 上次 | 变化 |
|------|------|------|------|
| 通过率 | 96.7% | 97.2% | -0.5% |
| 执行时间 | 5m 15s | 6m 02s | -47s ✅ |
| 失败数 | 5 | 3 | +2 ⚠️ |
| Flaky数 | 3 | 4 | -1 ✅ |
| 覆盖率 | 86.2% | 85.8% | +0.4% ✅ |

---

## 🎯 建议行动

### 立即行动 (本次PR合并前)
- [ ] 修复 `test_create_user_duplicate_email` (P0 回归)
- [ ] 修复浮点精度断言 `test_order_total_calculation` (P2)

### 近期改进
- [ ] 继续修复已知的flaky测试 (目标: 0 flaky by Jan 15)
- [ ] 优化慢速E2E测试 (目标: 最长<20s)

---

**报告生成**: 执行管理司  
**下次执行**: PR合并后或新提交时
```

---

## 与MARC资源协调器的资源需求

```yaml
marc_resource_requirements:
  compute_resources:
    cpu_cores: 8  # 用于并行执行
    memory_gb: 16
    disk_space_gb: 20
    
  execution_time:
    test_execution: "< 10 minutes (full suite)"
    report_generation: "< 2 minutes"
    flaky_analysis: "< 5 minutes"
    
  infrastructure:
    ci_cd_integration:
      - "GitHub Actions"
      - "GitLab CI"
      - "Jenkins"
    notification_channels:
      - "Pull Request comments"
      - "Slack alerts"
      - "Email digests"
      
  tool_dependencies:
    python:
      - "pytest>=7.4.0"
      - "pytest-xdist>=3.3.0"
      - "pytest-rerunfailures>=12.0"
      - "pytest-timeout>=2.1.0"
      - "pytest-html>=3.2.0"
    javascript:
      - "jest>=29.6.0"
      - "jest-stare>=2.3.0"
    e2e:
      - "playwright>=1.36.0"
      - "cypress>=13.0.0"
      
  output_storage:
    location: "docs/testing/reports/"
    files:
      - "execution_report_*.md"
      - "junit_xml_results.xml"
      - "coverage_report/"
      - "flaky_report.json"
    retention_days: 30
```

---

## 协同调用接口

### 接口定义

| 接口名称 | 接口描述 | 调用方 |
|----------|----------|--------|
| `execute_test_suite` | 执行完整测试套件接口 | CI/CD流水线、门禁把控司 |
| `run_specific_tests` | 运行指定测试子集接口 | 开发者本地调试 |
| `analyze_flaky_tests` | 分析Flaky测试接口 | 质量监控局、开发团队 |
| `generate_execution_report` | 生成执行报告接口 | 门下省主流程、项目经理 |

### 调用示例

```bash
# 执行完整测试套件并生成报告
python skillscripts/testing/test_executor.py \
  --suite full \
  --parallel-workers 6 \
  --include-flaky-retry \
  --generate-report \
  --output docs/testing/reports/exec_$(date +%Y%m%d_%H%M%S)/
```

---

## 版本历史

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| 1.0.0 | 2026-04-06 | 初始版本，包含完整的执行调度、并行管理、Flaky处理能力 |
