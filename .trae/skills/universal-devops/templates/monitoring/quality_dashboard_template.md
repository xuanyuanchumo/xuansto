# {项目名称} 可观测性质量仪表板

> 生成时间: {timestamp} | 观测周期: {period} | 版本: {version}

## 📊 总览概览

| 维度 | 当前值 | 基线 | 状态 | 趋势 |
|------|--------|------|------|------|
| 综合健康评分 | {health_score}/100 | {baseline_health} | {status} | {trend} |
| SLA 达标率 | {sla_rate}% | {target_sla}% | {status} | {trend} |
| 平均响应时间 | {avg_latency}ms | {target_latency}ms | {status} | {trend} |
| 错误率 | {error_rate}% | {max_error}% | {status} | {trend} |

## 🔍 日志分析

### 最近告警 ({alert_count} 条)

| 时间 | 级别 | 来源 | 内容 | 状态 |
|------|------|------|------|------|
{alerts_table}

### 日志模式

{log_patterns}

## 📈 指标监控

### 核心指标

{metrics_section}

### 性能基线对比

{baseline_comparison}

## 🔗 追踪分析

### 慢请求 Top {top_n}

{slow_requests}

### 错误请求追踪

{error_traces}

## 🚨 异常检测结果

{anomaly_detection}

## 📋 建议

{recommendations}

---
*由 Universal DevOps v7.0 Observability Pipeline 自动生成*
