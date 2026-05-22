---
name: xingneng_shenji_si
description: 性能审计司，负责算法复杂度分析、内存泄漏检测、N+1查询检测。集成四维防线第3层RuleValidationLayer的性能基线子模块。
---

# 性能审计司技能指令

## 职责定义

性能审计司作为代码审查局的性能保障核心，承担以下职责：

| 职责类别 | 具体职责 | 关键产出 |
|----------|----------|----------|
| **算法分析** | 时间/空间复杂度分析 | 复杂度分析报告 |
| **内存检测** | 内存泄漏、内存溢出检测 | 内存分析报告 |
| **查询优化** | N+1查询、慢查询检测 | 查询优化报告 |
| **性能基线** | 性能指标基准线建立与监控 | 性能基线报告 |

---

## 工具集成

### 核心性能工具链

| 工具 | 用途 | 语言支持 |
|------|------|----------|
| **cProfile** | Python性能剖析 | Python |
| **Memory Profiler** | 内存使用分析 | Python |
| **Py-Spy** | 无侵入性能采样 | Python |
| **profiling tools** | Node.js性能分析 | JS/TS |
| **heapdump** | 内存快照分析 | Node.js |
| **django-debug-toolbar** | Django请求分析 | Django |
| **SQLAlchemy事件系统** | ORM查询监控 | SQLAlchemy |

### 四维防线第3层集成

```yaml
four_dimensional_defense:
  layer: 3
  component: "RuleValidationLayer"
  submodule: "performance_baseline"

performance_baseline_rules:
  response_time:
    api_endpoints:
      p50_threshold_ms: 100
      p95_threshold_ms: 500
      p99_threshold_ms: 1000
      
    web_pages:
      first_contentful_paint_ms: 1500
      largest_contentful_paint_ms: 2500
      
  resource_usage:
    memory_mb_per_request: 50
    cpu_usage_percent: 80
    connection_pool_size: 20
    
  algorithmic_complexity:
    time_complexity_limit: "O(n log n)"
    space_complexity_limit: "O(n)"
    
  database_queries:
    max_queries_per_request: 10
    n_plus_one_detection: true
    slow_query_threshold_ms: 1000
```

---

## 工作流程

### 阶段一：性能审计准备

```
代码提交/性能测试触发
    ↓
[1] 审计范围确定
    ↓
[2] 基准数据加载
    ↓
[3] 性能配置加载
    ↓
进入性能审计阶段
```

#### 审计范围配置

```yaml
performance_audit_config:
  audit_modes:
    - "incremental"  # 只审计变更代码
    - "full"         # 全量审计
    - "targeted"     # 指定端点/函数审计
    
  focus_areas:
    - "api_endpoints"
    - "database_operations"
    - "memory_intensive_operations"
    - "algorithm_implementations"
    
  baseline_source:
    - "historical_data"
    - "configured_thresholds"
    - "industry_standards"
```

---

### 阶段二：算法复杂度分析流程

```
审计准备完成
    ↓
[1] 函数/方法识别
    ↓
[2] 循环结构分析
    ↓
[3] 递归深度分析
    ↓
[4] 数据结构操作分析
    ↓
[5] 大O表示法推导
    ↓
[6] 复杂度评级
    ↓
输出复杂度分析报告
```

#### 复杂度评级标准

| 复杂度 | 表示法 | 性能特征 | 评级 | 建议 |
|--------|--------|----------|------|------|
| 常数 | O(1) | 最优 | ✅ 优秀 | 保持 |
| 对数 | O(log n) | 极好 | ✅ 优秀 | 保持 |
| 线性 | O(n) | 良好 | ✅ 良好 | 可接受 |
| 线性对数 | O(n log n) | 较好 | ⚠️ 可接受 | 关注大数据量 |
| 平方 | O(n²) | 较差 | ❌ 不佳 | 需优化 |
| 立方 | O(n³) | 差 | 🔴 严重 | 必须优化 |
| 指数 | O(2ⁿ) | 极差 | 🔴 致命 | 禁止使用 |
| 阶乘 | O(n!) | 不可接受 | 🔴 致命 | 禁止使用 |

#### 算法复杂度分析输出格式

```json
{
  "analysis_id": "ALGO-COMP-001",
  "timestamp": "2024-01-01T00:00:00Z",
  "analysis_scope": {
    "repository": "project-name",
    "files_analyzed": 80,
    "functions_analyzed": 150
  },
  "complexity_results": [
    {
      "function_id": "FUNC-001",
      "function_name": "process_users",
      "file_path": "src/services/user_processor.py",
      "line_range": [45, 89],
      "time_complexity": {
        "big_o": "O(n²)",
        "derived_from": "nested loops over user list",
        "worst_case_n": "number of users",
        "estimated_ops_for_n_1000": 1000000
      },
      "space_complexity": {
        "big_o": "O(n)",
        "reason": "stores result list of size n"
      },
      "rating": "poor",
      "optimization_opportunities": [
        {
          "current_approach": "Nested loop iteration",
          "optimized_approach": "Use dictionary/hash map for O(1) lookups",
          "expected_improvement": "O(n²) → O(n)",
          "effort": "medium",
          "code_example": |
            # Current O(n²)
            for i, user_a in enumerate(users):
                for user_b in users[i+1:]:
                    if match(user_a, user_b):
                        results.append((user_a, user_b))
            
            # Optimized O(n)
            user_map = {}
            for user in users:
                key = generate_key(user)
                if key in user_map:
                    results.append((user_map[key], user))
                else:
                    user_map[key] = user
        }
      ],
      "performance_risk": "high",
      "recommendation": "Refactor to reduce time complexity before merging"
    },
    {
      "function_id": "FUNC-002",
      "function_name": "binary_search",
      "file_path": "src/utils/search_utils.py",
      "line_range": [23, 45],
      "time_complexity": {
        "big_o": "O(log n)",
        "derived_from": "halving search space each iteration"
      },
      "space_complexity": {
        "big_o": "O(1)"
      },
      "rating": "excellent",
      "recommendation": "Maintain current implementation"
    },
    {
      "function_id": "FUNC-003",
      "function_name": "generate_permutations",
      "file_path": "src/algorithms/combinatorics.py",
      "line_range": [12, 35],
      "time_complexity": {
        "big_o": "O(n!)",
        "derived_from": "recursive permutation generation"
      },
      "space_complexity": {
        "big_o": "O(n!)"
      },
      "rating": "fatal",
      "performance_risk": "critical",
      "recommendation": "This function is only acceptable for n < 10. Add input validation or use iterative approach for larger inputs."
    }
  ],
  "summary": {
    "total_functions_analyzed": 150,
    "by_rating": {
      "excellent": 120,
      "good": 20,
      "acceptable": 5,
      "poor": 4,
      "fatal": 1
    },
    "average_complexity": "O(n log n)",
    "high_risk_functions": 5,
    "optimization_potential": "Estimated 60% improvement possible"
  },
  "recommendations": [
    "Prioritize fixing the O(n!) function - add input size limits",
    "Address 4 functions with O(n²) complexity",
    "Consider caching for frequently called O(n log n) functions"
  ]
}
```

---

### 阶段三：内存泄漏检测流程

```
复杂度分析完成
    ↓
[1] 内存快照采集
    ↓
[2] 内存分配追踪
    ↓
[3] 未释放对象识别
    ↓
[4] 引用循环检测
    ↓
[5] 内存增长趋势分析
    ↓
[6] 泄漏点定位
    ↓
输出内存分析报告
```

#### 内存检测配置

```yaml
memory_detection_config:
  profiling_tools:
    python:
      tool: "memory_profiler"
      sampling_interval: "0.1s"
      include_children: true
      
    nodejs:
      tool: "heapdump + chrome devtools"
      allocation_sampling: true
      
  leak_detection_rules:
    unbounded_growth:
      threshold_mb: 100
      time_window_minutes: 10
      severity: "high"
      
    circular_references:
      enable_gc_detection: true
      weakref_usage_required: true
      severity: "medium"
      
    large_object_retention:
      object_size_threshold_mb: 50
      retention_time_hours: 1
      severity: "medium"
      
    connection_leaks:
      pool_exhaustion_threshold: 90  # percent
      connection_timeout_seconds: 300
      severity: "critical"
```

#### 内存分析报告格式

```json
{
  "analysis_id": "MEM-LEAK-001",
  "timestamp": "2024-01-01T00:00:00Z",
  "analysis_type": "memory_leak_detection",
  "environment": {
    "python_version": "3.11.0",
    "os": "Linux",
    "total_memory_gb": 16,
    "available_memory_gb": 12
  },
  "memory_metrics": {
    "baseline_memory_mb": 256,
    "peak_memory_mb": 512,
    "final_memory_mb: 480,
    "memory_growth_mb": 224,
    "growth_rate_mb_per_hour": 22.4,
    "gc_collections": 15,
    "objects_tracked": 50000
  },
  "leak_indicators": [
    {
      "id": "LEAK-001",
      "type": "unbounded_list_growth",
      "severity": "high",
      "location": {
        "file": "src/services/cache_service.py",
        "function": "CacheManager.__init__",
        "line": 34
      },
      "description": "Cache entries list grows without bounds, no eviction policy implemented",
      "evidence": {
        "initial_size": 0,
        "size_after_10min": 100000,
        "growth_rate": "10000 items/min",
        "memory_per_item_bytes": 512,
        "estimated_memory_usage_mb_after_1hour": 307
      },
      "root_cause": "Missing LRU eviction or TTL-based expiration",
      "fix_recommendation": |
        from collections import OrderedDict
        
        class LRUCache:
            def __init__(self, capacity: int = 10000):
                self.capacity = capacity
                self.cache = OrderedDict()
                
            def get(self, key):
                if key not in self.cache:
                    return None
                self.cache.move_to_end(key)
                return self.cache[key]
                
            def put(self, key, value):
                self.cache[key] = value
                self.cache.move_to_end(key)
                if len(self.cache) > self.capacity:
                    self.cache.popitem(last=False)
      ,
      "estimated_memory_saved_mb": ">300 per hour"
    },
    {
      "id": "LEAK-002",
      "type": "database_connection_leak",
      "severity": "critical",
      "location": {
        "file": "src/repository/base_repository.py",
        "function": "execute_query",
        "line": 67
      },
      "description": "Database connections not properly closed in exception paths",
      "evidence": {
        "active_connections_peak": 95,
        "pool_max_size": 100,
        "connection_timeout_occurrences": 15,
        "unclosed_connection_ratio": 0.23
      },
      "root_cause": "Missing finally block or context manager for connection cleanup",
      "fix_recommendation": |
        # Use context manager pattern
        def execute_query(self, sql, params=None):
            conn = None
            cursor = None
            try:
                conn = self.pool.getconn()
                cursor = conn.cursor()
                cursor.execute(sql, params or ())
                return cursor.fetchall()
            except Exception as e:
                logger.error(f"Query failed: {e}")
                raise
            finally:
                if cursor:
                    cursor.close()
                if conn:
                    self.pool.putconn(conn)
      ,
      "impact": "Connection pool exhaustion leading to service degradation"
    },
    {
      "id": "LEAK-003",
      "type": "event_listener_not_removed",
      "severity": "medium",
      "location": {
        "file": "src/events/event_bus.py",
        "function": "subscribe",
        "line": 45
      },
      "description": "Event listeners registered but never unsubscribed, causing memory retention",
      "evidence": {
        "listeners_count_growth": "+500 over 1 hour",
        "avg_listener_memory_bytes": 1024,
        "stale_listeners_ratio": 0.4
      }
    }
  ],
  "summary": {
    "total_leaks_detected": 3,
    "by_severity": {
      "critical": 1,
      "high": 1,
      "medium": 1,
      "low": 0
    },
    "estimated_memory_leak_rate_mb_per_hour": 25,
    "predicted_oom_time_hours": 12,
    "overall_status": "failed"
  },
  "action_items": [
    {
      "priority": "P0",
      "item": "Fix database connection leak immediately - service at risk of pool exhaustion",
      "deadline": "24 hours",
      "assignee": "Backend Team"
    },
    {
      "priority": "P1",
      "item": "Implement cache eviction policy (LRU/TTL)",
      "deadline": "1 week",
      "assignee": "Backend Team"
    },
    {
      "priority": "P2",
      "item": "Add unsubscribe mechanism for event listeners",
      "deadline": "2 weeks",
      "assignee": "Backend Team"
    }
  ],
  "memory_optimization_potential": {
    "current_peak_mb": 512,
    "target_peak_mb": 300,
    "potential_reduction_percent": 41,
    "estimated_performance_gain": "Reduced GC pauses, lower memory costs"
  }
}
```

---

### 阶段四：N+1查询检测流程

```
内存检测完成
    ↓
[1] ORM操作识别
    ↓
[2] 查询模式分析
    ↓
[3] N+1模式匹配
    ↓
[4] 查询计数统计
    ↓
[5] 优化建议生成
    ↓
输出查询优化报告
```

#### N+1检测规则

```yaml
n_plus_one_detection:
  patterns:
    loop_query:
      description: "Query inside loop iterating over parent objects"
      severity: "high"
      example: |
        # N+1 Pattern
        users = User.query.all()  # 1 query
        for user in users:
            orders = Order.query.filter_by(user_id=user.id).all()  # N queries
            
      optimized: |
        # Fixed with eager loading
        users = User.query.options(joinedload(User.orders)).all()  # 1-2 queries
        
    lazy_loading_in_templates:
      description: "Accessing relationships in templates triggers additional queries"
      severity: "medium"
      
    select_related_missing:
      description: "Django ForeignKey access without select_related/prefetch_related"
      severity: "high"
      
  detection_methods:
    - "ORM event listening (SQLAlchemy/Django)"
    - "Query counting middleware"
    - "Static code analysis patterns"
    - "Runtime query logging"
    
  thresholds:
    max_queries_per_request: 10
    n_plus_one_ratio_threshold: 0.3  # 30% of total queries
    duplicate_query_threshold: 5
```

#### 查询优化报告格式

```json
{
  "report_id": "QUERY-OPT-001",
  "timestamp": "2024-01-01T00:00:00Z",
  "analysis_scope": {
    "endpoint": "/api/users/{id}/orders",
    "http_method": "GET",
    "orm_framework": "SQLAlchemy"
  },
  "query_analysis": {
    "total_queries_executed": 52,
    "unique_queries": 8,
    "duplicate_queries": 44,
    "query_time_total_ms": 1250,
    "average_query_time_ms": 24,
    "slowest_query_ms": 450
  },
  "n_plus_one_findings": [
    {
      "id": "N+1-001",
      "pattern_type": "loop_query",
      "severity": "high",
      "location": {
        "file": "src/api/user_api.py",
        "function": "get_user_orders",
        "line_range": [78, 92]
      },
      "problem_description": |
        When fetching user orders, the code executes a separate query 
        for each order's items inside the loop.
      ,
      "problematic_code": |
        @app.route('/users/<int:user_id>/orders')
        def get_user_orders(user_id):
            user = db.session.get(User, user_id)  # Query 1
            orders = user.orders  # Lazy load - Query 2
            
            result = []
            for order in orders:
                order_dict = order.to_dict()
                order_dict['items'] = []  # Query 3+N (one per order)
                for item in order.items:  # N+1 problem here!
                    order_dict['items'].append(item.to_dict())
                result.append(order_dict)
            
            return jsonify(result)
      ,
      "queries_generated": {
        "initial": 2,
        "per_iteration": 1,
        "total_for_50_orders": 52,
        "optimal": 2
      },
      "optimization_strategy": {
        "approach": "Eager loading with joinedload/subqueryload",
        "optimized_code": |
          from sqlalchemy.orm import joinedload, subqueryload
          
          @app.route('/users/<int:user_id>/orders')
          def get_user_orders(user_id):
              user = db.session.query(User).options(
                  joinedload(User.orders).subqueryload(Order.items)
              ).get(user_id)  # Single query with JOINs
              
              return jsonify([order.to_dict(with_items=True) for order in user.orders])
        ,
        "expected_improvement": {
          "queries_before": 52,
          "queries_after": 2,
          "reduction_percent": 96,
          "response_time_before_ms": 1250,
          "response_time_after_ms": 150,
          "speedup": "8.3x faster"
        }
      }
    },
    {
      "id": "N+1-002",
      "pattern_type": "select_related_missing",
      "severity": "medium",
      "location": {
        "file": "src/api/product_api.py",
        "function": "list_products",
        "line_range": [34, 48]
      },
      "problem_description": "Product listing accesses category.name without select_related",
      "queries_generated": {
        "initial": 1,
        "additional_per_product": 1,
        "total_for_100_products": 101
      },
      "optimization": {
        "approach": "Add select_related('category')",
        "expected_reduction": "99% fewer queries"
      }
    }
  ],
  "slow_queries": [
    {
      "id": "SLOW-001",
      "sql": "SELECT * FROM orders WHERE created_at > NOW() - INTERVAL '30 days' ORDER BY created_at DESC",
      "execution_time_ms": 450,
      "rows_examined": 500000,
      "rows_returned": 150,
      "issue": "Full table scan due to missing index on created_at",
      "recommendation": "CREATE INDEX idx_orders_created_at ON orders(created_at DESC)"
    }
  ],
  "summary": {
    "n_plus_one_issues_found": 2,
    "total_wasted_queries": 46,
    "potential_query_reduction_percent": 88,
    "slow_queries_found": 1,
    "overall_status": "needs_optimization"
  },
  "optimization_priority": [
    {
      "rank": 1,
      "item": "Fix N+1 in get_user_orders endpoint",
      "impact": "High - 96% query reduction",
      "effort": "Low - simple eager loading change"
    },
    {
      "rank": 2,
      "item": "Add index on orders.created_at",
      "impact": "Medium - eliminate slow query",
      "effort": "Low - single DDL statement"
    },
    {
      "rank": 3,
      "item": "Add select_related in product listing",
      "impact": "Medium - 99% query reduction for this endpoint",
      "effort": "Low - one line change"
    }
  ],
  "performance_baseline_integration": {
    "layer": 3,
    "submodule": "performance_baseline",
    "baseline_met": false,
    "thresholds_exceeded": [
      "max_queries_per_request (52 > 10)",
      "n_plus_one_detection_enabled (true)"
    ]
  }
}
```

---

### 阶段五：综合性能审计报告生成

```
所有性能审计完成
    ↓
[1] 数据汇总整合
    ↓
[2] 性能评分计算
    ↓
[3] 风险等级评定
    ↓
[4] 优化ROI分析
    ↓
[5] 报告生成与建议
    ↓
输出综合性能审计报告
```

#### 综合性能报告格式

```json
{
  "audit_report_id": "PERF-AUDIT-001",
  "timestamp": "2024-01-01T00:00:00Z",
  "audit_context": {
    "trigger": "pull_request",
    "pr_number": 124,
    "branch": "feature/order-management",
    "commit_hash": "def456abc789",
    "author": "backend-developer"
  },
  "executive_summary": {
    "overall_performance_status": "NEEDS_ATTENTION",
    "performance_score": 58,
    "risk_level": "HIGH",
    "key_findings": [
      "1个致命复杂度函数(O(n!))需添加输入限制",
      "1个关键数据库连接泄漏可能导致服务中断",
      "2个N+1查询问题导致96%多余查询",
      "1个慢查询缺少索引"
    ],
    "blocking_issues": 2,
    "recommendation": "要求修复Critical级别问题后再合并"
  },
  "detailed_results": {
    "algorithmic_complexity": {
      "status": "warning",
      "score": 65,
      "functions_analyzed": 150,
      "high_risk_functions": 5,
      "worst_case": "O(n!) in generate_permutations"
    },
    "memory_analysis": {
      "status": "failed",
      "score": 42,
      "leaks_detected": 3,
      "critical_leaks": 1,
      "oom_risk": "high (12h predicted)"
    },
    "query_optimization": {
      "status": "failed",
      "score": 55,
      "n_plus_one_issues": 2,
      "wasted_queries": 46,
      "slow_queries": 1
    }
  },
  "performance_baseline_comparison": {
    "current_metrics": {
      "p50_response_time_ms": 280,
      "p95_response_time_ms": 850,
      "p99_response_time_ms": 1500,
      "memory_usage_mb": 480,
      "queries_per_request_avg": 15
    },
    "baseline_thresholds": {
      "p50_response_time_ms": 100,
      "p95_response_time_ms": 500,
      "p99_response_time_ms": 1000,
      "memory_usage_mb": 256,
      "queries_per_request_avg": 10
    },
    "thresholds_exceeded": 4,
    "thresholds_met": 2
  },
  "roi_analysis": {
    "optimizations_recommended": 4,
    "total_effort_estimate_days": 3,
    "expected_performance_gain_percent": 75,
    "top_roi_items": [
      {
        "item": "Fix connection leak",
        "effort_hours": 4,
        "impact": "Prevent potential outage",
        "roi": "critical"
      },
      {
        "item": "Fix N+1 queries",
        "effort_hours": 2,
        "impact": "8x faster endpoint",
        "roi": "very_high"
      }
    ]
  },
  "action_plan": {
    "immediate_actions": [
      {
        "priority": "P0",
        "deadline": "24 hours",
        "action": "Fix database connection leak in base_repository.py",
        "assignee": "Backend Lead"
      },
      {
        "priority": "P0",
        "deadline": "48 hours",
        "action": "Add input validation to generate_permutations (n<10)",
        "assignee": "Algorithm Developer"
      }
    ],
    "short_term_actions": [
      {
        "priority": "P1",
        "deadline": "1 week",
        "action": "Implement eager loading for user orders endpoint",
        "assignee": "Backend Developer"
      },
      {
        "priority": "P1",
        "deadline": "1 week",
        "action": "Create missing index on orders.created_at",
        "assignee": "DBA"
      }
    ]
  },
  "rule_validation_layer_integration": {
    "layer": 3,
    "submodule": "performance_baseline",
    "checks_executed": ["algorithmic_complexity", "memory_usage", "query_efficiency"],
    "baseline_checks_passed": false,
    "failed_checks": [
      "max_queries_per_request exceeded",
      "memory_growth detected",
      "O(n!) complexity found"
    ]
  }
}
```

---

## 与MARC资源协调器的资源需求

```yaml
marc_resource_requirements:
  compute_resources:
    cpu_cores: 4
    memory_gb: 8
    disk_space_gb: 15
    
  execution_time:
    complexity_analysis: "< 2 minutes"
    memory_profiling: "< 5 minutes"
    query_analysis: "< 3 minutes"
    full_audit: "< 10 minutes"
    
  runtime_environment:
    requires_production_like_data: true
    sample_data_size_mb: 100
    database_access: read_only
    
  tool_dependencies:
    - "memory-profiler>=0.60.0"
    - "py-spy>=0.3.0"
    - "django-debug-toolbar>=4.0.0"
    - "sqlalchemy>=1.4.0"
    
  output_storage:
    location: "docs/reviews/code_reviews/performance/"
    format: ["json", "html"]
    retention_days: 90
    
  monitoring_integration:
    metrics_export: "Prometheus format"
    alerting_on: "memory_growth, query_count, response_time"
```

---

## 协同调用接口

### 接口定义

| 接口名称 | 接口描述 | 调用方 |
|----------|----------|--------|
| `analyze_algorithmic_complexity` | 算法复杂度分析接口 | 审查报告司 |
| `detect_memory_leaks` | 内存泄漏检测接口 | 审查报告司、门禁把控司 |
| `detect_n_plus_one_queries` | N+1查询检测接口 | 审查报告司 |
| `run_full_performance_audit` | 完整性能审计接口 | 门下省主流程、门禁把控司 |

### 调用示例

```bash
# 执行完整性能审计
python skillscripts/analysis/performance_auditor.py \
  --audit-type full \
  --source ./src \
  --include-complexity \
  --include-memory \
  --include-queries \
  --baseline config/performance_baseline.yaml \
  --output docs/reports/performance/audit_$(date +%Y%m%d).json
```

---

## 版本历史

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| 1.0.0 | 2026-04-06 | 初始版本，包含复杂度分析、内存检测、N+1查询检测完整能力 |
