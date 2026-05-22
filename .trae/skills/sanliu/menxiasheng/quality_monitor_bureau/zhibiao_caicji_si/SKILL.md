---
name: zhibiao_caicji_si
description: 指标采集司，负责六维质量指标采集（代码质量/测试覆盖/技术债务/性能/安全合规/文档质量）。数据源：SonarQube/pytest coverage/Bandit等。
---

# 指标采集司技能指令

## 职责定义

指标采集司作为质量监控局的数据基础核心，承担以下职责：

| 职责类别 | 具体职责 | 关键产出 |
|----------|----------|----------|
| **指标定义** | 六维质量指标体系建立与维护 | 指标定义文档 |
| **数据采集** | 多源质量数据自动采集 | 原始数据集 |
| **数据标准化** | 数据清洗与格式统一 | 标准化数据 |
| **存储管理** | 时序数据存储与管理 | 数据仓库 |

---

## 六维质量指标体系

```yaml
six_dimensional_quality_metrics:
  dimension_1_code_quality:
    name: "代码质量"
    weight: 0.20
    description: "评估代码的可维护性、可读性和规范性"
    
    sub_metrics:
      - name: "cyclomatic_complexity_avg"
        display_name: "平均圈复杂度"
        unit: "数值"
        target: "<= 10"
        data_source: "SonarQube / Radon"
        collection_frequency: "per_commit"
        
      - name: "code_duplication_percent"
        display_name: "代码重复率"
        unit: "%"
        target: "<= 5%"
        data_source: "SonarQube / JSCPD"
        
      - name: "technical_debt_ratio"
        display_name: "技术债务比率"
        unit: "%"
        target: "<= 5%"
        data_source: "SonarQube"
        formula: "(debt_hours / development_cost_hours) * 100"
        
      - name: "code_smell_density"
        display_name: "代码异味密度"
        unit: "每千行异味数"
        target: "<= 1.0"
        data_source: "SonarQube / ESLint"
        
      - name: "coding_standards_compliance"
        display_name: "编码规范符合率"
        unit: "%"
        target: ">= 95%"
        data_source: "Pylint / ESLint score"
        
  dimension_2_test_coverage:
    name: "测试覆盖率"
    weight: 0.20
    description: "衡量测试对代码的保护程度"
    
    sub_metrics:
      - name: "line_coverage_percent"
        display_name: "行覆盖率"
        unit: "%"
        target: ">= 85%"
        data_source: "Coverage.py / Istanbul / JaCoCo"
        
      - name: "branch_coverage_percent"
        display_name: "分支覆盖率"
        unit: "%"
        target: ">= 80%"
        data_source: "Coverage.py / Istanbul"
        
      - name: "function_coverage_percent"
        display_name: "函数覆盖率"
        unit: "%"
        target: ">= 90%"
        data_source: "Coverage.py / Istanbul"
        
      - name: "test_pass_rate"
        display_name: "测试通过率"
        unit: "%"
        target: "100%"
        data_source: "pytest / Jest results"
        
      - name: "test_execution_time"
        display_name: "测试执行时间"
        unit: "秒"
        target: "<= 600 (10分钟)"
        data_source: "CI/CD pipeline logs"
        
  dimension_3_technical_debt:
    name: "技术债务"
    weight: 0.15
    description: "追踪需要未来修复的技术问题累积"
    
    sub_metrics:
      - name: "total_debt_hours"
        display_name: "总技术债务(小时)"
        unit: "hours"
        trend: "should_decrease"
        data_source: "SonarQube Technical Debt Module"
        
      - name: "new_debt_this_sprint"
        display_name: "本期新增债务"
        unit: "hours"
        target: "<= previous_sprint * 1.1"
        data_source: "SonarQube diff analysis"
        
      - name: "bug_count"
        display_name: "已知Bug数量"
        unit: "count"
        target: "trend_decreasing"
        data_source: "Issue Tracker (Jira/GitHub)"
        
      - name: "vulnerability_count"
        display_name: "安全漏洞数量"
        unit: "count"
        by_severity: ["critical", "major", "minor"]
        target: "critical=0, major<=5"
        data_source: "Snyk / Dependabot / SonarQube Security"
        
      - name: "code_ages"
        display_name: "代码老化程度"
        unit: "days since last change"
        alert_threshold: "> 180 days without test update"
        
  dimension_4_performance:
    name: "性能指标"
    weight: 0.15
    description: "系统运行时性能表现"
    
    sub_metrics:
      - name: "api_p50_response_time_ms"
        display_name: "API P50响应时间"
        unit: "ms"
        target: "<= 200ms"
        data_source: "APM (Datadog/New Relic) / Custom metrics"
        
      - name: "api_p95_response_time_ms"
        display_name: "API P95响应时间"
        unit: "ms"
        target: "<= 500ms"
        data_source: "APM"
        
      - name: "api_p99_response_time_ms"
        display_name: "API P99响应时间"
        unit: "ms"
        target: "<= 1000ms"
        data_source: "APM"
        
      - name: "error_rate_percent"
        display_name: "错误率"
        unit: "%"
        target: "<= 0.1%"
        data_source: "APM / Application logs"
        
      - name: "throughput_rps"
        display_name: "吞吐量"
        unit: "requests/second"
        target: ">= baseline * 0.9"
        data_source: "Load balancer / APM"
        
      - name: "memory_usage_mb"
        display_name: "内存使用量"
        unit: "MB"
        target: "<= limit * 0.8"
        data_source: "Container metrics / CloudWatch"
        
      - name: "cpu_usage_percent"
        display_name: "CPU使用率"
        unit: "%"
        target: "<= 70% average"
        data_source: "Container metrics"
        
  dimension_5_security_compliance:
    name: "安全合规"
    weight: 0.15
    description: "安全状态和合规性水平"
    
    sub_metrics:
      - name: "owasp_vulnerability_score"
        display_name: "OWASP漏洞评分"
        unit: "A-F grade"
        target: ">= B"
        data_source: "SonarQube Security / Snyk"
        grading:
          A: "0 critical, 0 high"
          B: "0 critical, 1-3 high"
          C: "0 critical, 4-6 high"
          D: "1+ critical or 7+ high"
          F: "multiple critical"
          
      - name: "dependency_vulnerability_count"
        display_name: "依赖漏洞数"
        unit: "count"
        target: "critical=0, high<=2"
        data_source: "Snyk / Dependabot / npm audit"
        
      - name: "secret_exposure_count"
        display_name: "密钥暴露次数"
        unit: "count"
        target: "0"
        data_source: "GitLeaks / HardcodedDetector scan results"
        
      - name: "security_scan_pass_rate"
        display_name: "安全扫描通过率"
        unit: "%"
        target: "100% (no blocking issues)"
        data_source: "Bandit / SAST tool results"
        
      - name: "compliance_score"
        display_name: "合规评分"
        unit: "0-100"
        target: ">= 80"
        data_source: "Custom compliance checker (SOC2/GDPR rules)"
        
  dimension_6_documentation_quality:
    name: "文档质量"
    weight: 0.15
    description: "项目文档的完整性和质量"
    
    sub_metrics:
      - name: "api_documentation_coverage"
        display_name: "API文档覆盖率"
        unit: "%"
        target: ">= 90%"
        data_source: "Swagger/OpenAPI spec completeness check"
        
      - name: "code_comment_density"
        display_name: "代码注释密度"
        unit: "%"
        target: "15-25% (not too low, not too high)"
        data_source: "Static analysis (Docstring/Comment ratio)"
        
      - name: "readme_completeness"
        display_name: "README完整性评分"
        unit: "0-100"
        target: ">= 80"
        data_source: "README checklist scorer"
        checklist_items:
          - project_description: 10
          - installation_guide: 15
          - usage_examples: 15
          - api_documentation_link: 10
          - configuration_guide: 10
          - contributing_guide: 10
          - license_info: 5
          - badges_ci_status: 5
          - changelog_link: 5
          - contact_info: 5
          - architecture_diagram: 10
          
      - name: "sdd_specification_coverage"
        display_name: "SDD规范覆盖度"
        unit: "%"
        target: ">= 95% of public APIs documented in SDD"
        data_source: "SDD document analyzer"
        
      - name: "doc_freshness_days"
        display_name: "文档新鲜度"
        unit: "days since last update"
        target: "<= code_change_age + 7 days"
```

---

## 工作流程

### 阶段一：数据源配置与连接

```
系统初始化或配置更新
    ↓
[1] 数据源注册
    ↓
[2] 认证凭据配置
    ↓
[3] 采集频率设定
    ↓
[4] 连接性测试
    ↓
进入数据采集阶段
```

#### 数据源配置模板

```yaml
data_sources_configuration:
  sonarqube:
    enabled: true
    url: "${SONARQUBE_URL}"
    token: "${SONARQUBE_TOKEN}"
    project_key: "${PROJECT_KEY}"
    
    collected_metrics:
      - "ncloc"  # Lines of code
      - "coverage"  # Coverage percentage
      - "duplicated_lines_density"
      - "sqale_index"  # Technical debt
      - "alert_status"
      - "quality_gate_status"
      - "vulnerabilities"
      - "code_smells"
      - "bugs"
      
    collection_schedule:
      mode: "webhook + polling"
      webhook_trigger: "analysis_completed"
      poll_interval_minutes: 30
      
  pytest_coverage:
    enabled: true
    source: "CI/CD artifacts"
    artifact_patterns:
      - "coverage.xml"
      - ".coverage"
      - "htmlcov/index.html"
      
    extracted_metrics:
      - "line_coverage"
      - "branch_coverage"
      - "function_coverage"
      - "total_statements"
      - "missing_statements"
      - "total_tests"
      - "passed_tests"
      - "failed_tests"
      - "skipped_tests"
      - "execution_time_seconds"
      
  security_scanners:
    bandit:
      enabled: true
      report_format: "json"
      artifact: "bandit-report.json"
      metrics:
        - "severity_counts"
        - "confidence_counts"
        - "total_issues"
        
    snyk:
      enabled: true
      api_endpoint: "https://api.snyk.io/v1"
      metrics:
        - "vulnerability_counts_by_severity"
        - "dependency_counts"
        - "license_issues"
        
    git_leaks:
      enabled: true
      metrics:
        - "secrets_found_count"
        - "secret_types_found"
        
  apm_system:
    datadog:
      enabled: false  # Enable if using Datadog
      api_key: "${DATADOG_API_KEY}"
      app_key: "${DATADOG_APP_KEY}"
      metrics_query_interval: "5m"
      
    custom_metrics:
      enabled: true
      endpoint: "/api/v1/metrics/push"
      authentication: "Bearer token"
      supported_metrics:
        - "response_time_p50"
        - "response_time_p95"
        - "error_rate"
        - "throughput"
        - "active_users"
        
  git_repository:
    github_api:
      enabled: true
      token: "${GITHUB_TOKEN}"
      repository: "${GITHUB_REPO}"
      
      collected_data:
        - "commit_frequency"
        - "contributors_count"
        - "pr_stats (open/closed/merged)"
        - "issue_stats (by_type, by_severity)"
        - "code_churn (additions/deletions)"
        - "review_coverage"
```

---

### 阶段二：自动化数据采集

```
触发条件满足（定时/webhook/手动）
    ↓
[1] 并行发起各数据源请求
    ↓
[2] 原始数据获取
    ↓
[3] 数据验证与校验
    ↓
[4] 元数据附加
    ↓
[5] 写入临时存储
    ↓
进入数据处理阶段
```

#### 采集执行器设计

```python
"""
指标采集执行器示例
文件: skillscripts/metrics/collector.py
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, List
import aiohttp

class MetricsCollector:
    """六维质量指标采集器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.session = None
        self.raw_data_store = []
        
    async def collect_all(self) -> Dict[str, Any]:
        """并行采集所有维度的指标"""
        self.session = aiohttp.ClientSession()
        
        try:
            # 并行采集所有数据源
            tasks = [
                self._collect_sonarqube(),
                self._collect_test_coverage(),
                self._collect_security_metrics(),
                self._collect_performance_metrics(),
                self._collect_documentation_metrics(),
                self._collect_git_metrics(),
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 整合结果
            collection_result = {
                "collection_timestamp": datetime.utcnow().isoformat(),
                "collector_version": "1.0.0",
                "data_sources_status": {},
                "dimensions": {}
            }
            
            for i, result in enumerate(results):
                dim_name = list(self.config["data_sources"].keys())[i]
                if isinstance(result, Exception):
                    collection_result["data_sources_status"][dim_name] = {
                        "status": "error",
                        "error_message": str(result)
                    }
                else:
                    collection_result["data_sources_status"][dim_name] = {
                        "status": "success",
                        "records_collected": len(result) if isinstance(result, list) else 1
                    }
                    collection_result["dimensions"][dim_name] = result
                    
            return collection_result
            
        finally:
            await self.session.close()
            
    async def _collect_sonarqube(self) -> Dict:
        """采集SonarQube数据"""
        url = f"{self.config['sonarqube']['url']}/api/measures/component"
        params = {
            "component": self.config['sonarqube']['project_key'],
            "metricKeys": ",".join(self.config['sonarqube']['collected_metrics'])
        }
        headers = {"Authorization": f"Bearer {self.config['sonarqube']['token']}"}
        
        async with self.session.get(url, params=params, headers=headers) as response:
            data = await response.json()
            
            component = data.get("component", {})
            measures = component.get("measures", [])
            
            return {
                "source": "sonarqube",
                "metrics": {m["metric"]: m["value"] for m in measures},
                "quality_gate": component.get("qualityGate", {}),
                "collected_at": datetime.utcnow().isoformat()
            }
    
    async def _collect_test_coverage(self) -> Dict:
        """从CI artifacts采集测试覆盖率"""
        # 实现从Jenkins/GitHub Actions下载artifacts并解析
        pass
        
    async def _collect_security_metrics(self) -> Dict:
        """聚合多个安全扫描工具的数据"""
        security_data = {
            "bandit": await self._fetch_bandit_report(),
            "snyk": await self._query_snyk_api(),
            "git_leaks": await self._check_git_history()
        }
        
        # 聚合计算综合安全评分
        return self._aggregate_security_metrics(security_data)
```

---

### 阶段三：数据标准化处理

```
原始数据收集完成
    ↓
[1] 格式统一转换
    ↓
[2] 单位标准化
    ↓
[3] 缺失值处理
    ↓
[4] 异常值检测
    ↓
[5] 数据质量评分
    ↓
输出标准化数据集
```

#### 数据标准化规则

```yaml
standardization_rules:
  format_conversion:
    numeric_fields:
      - rule: "Convert string numbers to float/int"
        pattern: "^\\d+(\\.\\d+)?$"
        action: "parseFloat or parseInt"
        
    timestamp_fields:
      - rule: "Normalize to ISO 8601 UTC"
        accepted_formats:
          - "ISO 8601"
          - "Unix epoch (seconds and milliseconds)"
          - "RFC 2822"
        output_format: "YYYY-MM-DDTHH:mm:ss.sssZ"
        
    enum_fields:
      severity:
        mapping:
          "CRITICAL": 4
          "HIGH": 3
          "MEDIUM": 2
          "LOW": 1
          "INFO": 0
          
      status:
        mapping:
          "OK": "passed"
          "ERROR": "failed"
          "WARNING": "warning"
          "NONE": "skipped"
          
  unit_normalization:
    time_units:
      milliseconds_to_seconds: "value / 1000"
      minutes_to_seconds: "value * 60"
      hours_to_seconds: "value * 3600"
      
    percentage_units:
      decimal_to_percent: "value * 100"
      ratio_to_percent: "value * 100"
      
  missing_value_handling:
    strategy: "context-dependent"
    
    rules:
      - condition: "metric is required for quality gate"
        action: "mark as null and flag for investigation"
        impact: "quality gate cannot be evaluated"
        
      - condition: "metric is optional/enhancement"
        action: "use last known value (forward fill)"
        max_gap_allowed: "3 collection periods"
        
      - condition: "metric has calculable default"
        action: "use derived value from related metrics"
        example: "if branch_coverage missing but line_coverage available, estimate as line_coverage * 0.94"
        
  outlier_detection:
    method: "IQR (Interquartile Range) + Z-score"
    
    parameters:
      iqr_multiplier: 1.5
      zscore_threshold: 3.0
      
    actions:
      - condition: "Value is statistical outlier"
        action: "Flag but keep (may indicate real issue)"
        tag: "statistical_outlier"
        
      - condition: "Value is impossible (e.g., negative time)"
        action: "Exclude and mark as invalid"
        tag: "invalid_data"
        
      - condition: "Value represents system error (e.g., -1 for timeout)"
        action: "Replace with null and note error condition"
```

---

### 阶段四：数据存储与索引

```
数据标准化完成
    ↓
[1] 时序数据库写入
    ↓
[2] 索引构建
    ↓
[3] 数据归档策略执行
    ↓
[4] 存储空间监控
    ↓
[5] 备份验证
    ↓
完成采集周期
```

#### 存储架构

```yaml
storage_architecture:
  primary_storage:
    type: "Time Series Database"
    options: ["InfluxDB", "TimescaleDB (PostgreSQL)", "Prometheus"]
    selected: "TimescaleDB"
    reason: "SQL compatibility + powerful time-series features + PostgreSQL ecosystem"
    
  schema_design:
    table: "quality_metrics_snapshot"
    columns:
      - name: "timestamp"
        type: "TIMESTAMPTZ"
        not_null: true
        index: true
        
      - name: "dimension"
        type: "VARCHAR(50)"
        not_null: true
        index: true
        
      - name: "metric_name"
        type: "VARCHAR(100)"
        not_null: true
        index: true
        
      - name: "value"
        type: "DOUBLE PRECISION"
        
      - name: "unit"
        type: "VARCHAR(20)"
        
      - name: "target"
        type: "DOUBLE PRECISION"
        
      - name: "status"
        type: "VARCHAR(20)"  # passed/warning/failed
        
      - name: "source_system"
        type: "VARCHAR(50)"
        
      - name: "metadata_json"
        type: "JSONB"
        
    hypertable_config:
      partitioning_column: "timestamp"
      chunk_interval: "1 day"
      compression_policy: "after 30 days"
      retention_policy: "keep 2 years of raw data, aggregate older"
      
  aggregation_tables:
    hourly_aggregates:
      granularity: "1 hour"
      functions: ["avg", "min", "max", "count", "stddev"]
      retention: "13 months"
      
    daily_aggregates:
      granularity: "1 day"
      functions: ["avg", "min", "max", "sum", "count"]
      retention: "5 years"
      
    weekly_summary:
      granularity: "1 week"
      functions: ["avg", "delta", "trend_direction"]
      retention: "permanent"
      
  data_quality_checks:
    on_insert:
      - check: "timestamp is not in future (> 5 minutes ahead)"
        action: "reject with warning"
        
      - check: "value within reasonable bounds for metric"
        action: "flag for review if out of range"
        
      - check: "no duplicate (dimension + metric_name + timestamp) within window"
        action: "upsert (update existing)"
        
  backup_strategy:
    frequency: "daily at 02:00 UTC"
    retention: "30 days of backups"
    encryption: "at-rest AES-256"
    cross_region_replication: true
```

---

## 输出物格式

### 标准化采集结果JSON

```json
{
  "collection_id": "COLLECT-20240101-143000",
  "timestamp": "2024-01-01T14:30:00Z",
  "collector_id": "zhibiao_caicji_si-v1.0",
  "collection_duration_seconds": 45,
  
  "collection_summary": {
    "total_metrics_collected": 42,
    "successful_collections": 39,
    "failed_collections": 3,
    "success_rate": 92.9,
    "data_quality_score": 94.5
  },
  
  "data_source_status": {
    "sonarqube": {"status": "success", "latency_ms": 234, "records": 12},
    "pytest_coverage": {"status": "success", "latency_ms": 45, "records": 8},
    "bandit_security": {"status": "success", "latency_ms": 123, "records": 4},
    "snyk_dependency": {"status": "partial", "latency_ms": 1200, "error": "rate_limited"},
    "apm_datadog": {"status": "skipped", "reason": "not_configured"},
    "github_api": {"status": "success", "latency_ms": 567, "records": 6}
  },
  
  "metrics_by_dimension": {
    "code_quality": {
      "overall_score": 82.5,
      "status": "warning",
      "metrics": [
        {
          "name": "cyclomatic_complexity_avg",
          "display_name": "平均圈复杂度",
          "value": 8.3,
          "unit": "numeric",
          "target": 10.0,
          "status": "passed",
          "trend": "improving (-0.5 vs last week)",
          "source": "sonarqube",
          "collected_at": "2024-01-01T14:29:45Z"
        },
        {
          "name": "code_duplication_percent",
          "display_name": "代码重复率",
          "value": 3.2,
          "unit": "%",
          "target": 5.0,
          "status": "passed",
          "source": "sonarqube"
        },
        {
          "name": "technical_debt_ratio",
          "display_name": "技术债务比率",
          "value": 6.8,
          "unit": "%",
          "target": 5.0,
          "status": "warning",
          "trend": "worsening (+0.8 vs last month)",
          "source": "sonarqube"
        }
      ]
    },
    
    "test_coverage": {
      "overall_score": 88.2,
      "status": "passed",
      "metrics": [...]
    },
    
    "performance": {
      "overall_score": 91.0,
      "status": "passed",
      "metrics": [...]
    },
    
    "security_compliance": {
      "overall_score: 75.5,
      "status": "warning",
      "metrics": [...]
    },
    
    "documentation_quality": {
      "overall_score": 78.0,
      "status": "warning",
      "metrics": [...]
    }
  },
  
  "raw_data_references": {
    "sonarqube_export": "s3://metrics-bucket/raw/2024/01/01/sonarqube_143000.json",
    "coverage_xml": "s3://metrics-bucket/raw/2024/01/01/coverage_143000.xml",
    "security_reports": "s3://metrics-bucket/raw/2024/01/01/security_143000/"
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
    disk_space_gb: 50  # For local cache before cloud upload
    
  execution_time:
    full_collection_cycle: "< 2 minutes"
    single_dimension: "< 30 seconds"
    
  network_requirements:
    outbound_connections:
      - "SonarQube API"
      - "GitHub API"
      - "Snyk API (optional)"
      - "Cloud storage (S3/GCS)"
    bandwidth_required: "Low (< 10MB per collection)"
    
  storage_requirements:
    local_cache: "1 GB (rolling 7 days)"
    cloud_storage: "~50GB/year (compressed)"
    
  reliability:
    retry_policy:
      max_retries: 3
      backoff_strategy: "exponential (1s, 2s, 4s)"
      retryable_errors: [503, 504, 429 (rate_limit)]
      
    failure_handling:
      partial_collection: "Accept and mark missing sources"
      total_failure: "Alert and queue for retry in 5 minutes"
```

---

## 协同调用接口

| 接口名称 | 接口描述 | 调用方 |
|----------|----------|--------|
| `collect_metrics` | 触发全量指标采集 | 定时任务、手动触发 |
| `get_latest_metrics` | 获取最新指标快照 | 趋势分析司、预警告警司 |
| `get_historical_range` | 获取历史时间范围数据 | 趋势分析司 |
| `validate_data_quality` | 数据质量检查 | 系统管理员 |

---

## 版本历史

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| 1.0.0 | 2026-04-06 | 初始版本，包含完整的六维指标体系和多源采集能力 |
