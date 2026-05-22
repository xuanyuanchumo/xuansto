---
name: qushi_fenxi_si
description: 趋势分析司，负责质量趋势分析、回归检测、基线对比。输出趋势图表、预测报告。
---

# 趋势分析司技能指令

## 职责定义

趋势分析司作为质量监控局的分析核心，承担以下职责：

| 职责类别 | 具体职责 | 关键产出 |
|----------|----------|----------|
| **趋势分析** | 质量指标时间序列趋势识别与分析 | 趋势分析报告 |
| **回归检测** | 质量退化检测与预警 | 回归警报 |
| **基线对比** | 与历史基线/行业基准对比分析 | 对比报告 |
| **预测建模** | 基于历史数据的未来趋势预测 | 预测报告 |

---

## 分析方法论

### 时间序列分析方法

```yaml
time_series_analysis_methods:
  trend_identification:
    moving_average:
      simple_ma:
        windows: [7, 14, 30]  # 天
        use_case: "短期波动平滑"
        
      exponential_ma:
        alpha_values: [0.3, 0.5, 0.7]
        use_case: "近期数据权重更高"
        
      weighted_ma:
        weights: "linear decay over window"
        use_case: "季节性调整"
        
  seasonality_detection:
    methods:
      - "STL decomposition (Seasonal-Trend decomposition using Loess)"
      - "Fourier analysis for periodic patterns"
      - "Autocorrelation function (ACF) analysis"
      
    common_patterns:
      weekly_cycle: "Development activity patterns (Mon-Fri vs weekend)"
      sprint_cycle: "2-week sprint rhythm effects"
      release_cycle: "Quality dips before releases, improvements after"
      seasonal: "Team capacity variations (vacations, hiring)"
      
  change_point_detection:
    algorithms:
      - "CUSUM (Cumulative Sum Control Chart)"
      - "Bayesian Online Change Point Detection (BOCPD)"
      - "PELT (Pruned Exact Linear Time) algorithm"
      
    application: "Identify when significant quality shifts occurred"
    
  regression_analysis:
    linear_regression:
      use_case: "Overall trend direction (improving/declining/stable)"
      output: "slope + R² + confidence interval"
      
    polynomial_regression:
      degrees: [2, 3]
      use_case: "Non-linear trends (acceleration/deceleration)"
      
    multiple_regression:
      use_case: "Correlate multiple factors with quality outcomes"
      example_factors: ["team_size", "code_churn", "tech_stack_changes"]
```

### 回归检测算法

```yaml
regression_detection_algorithms:
  definition: "Detect when current quality metrics significantly deviate from expected/historical norms"
  
  detection_methods:
    z_score_based:
      calculation: "(current_value - historical_mean) / historical_std_dev"
      thresholds:
        warning: "|z-score| > 2"
        critical: "|z-score| > 3"
      advantages: "Simple, interpretable"
      limitations: "Assumes normal distribution"
      
    percentile_based:
      calculation: "Current value's position in historical distribution"
      thresholds:
        warning: "Below 10th percentile or above 90th percentile"
        critical: "Below 5th percentile or above 95th percentile"
      advantages: "Distribution-free"
      
    control_chart:
      type: "Western Electric Rules"
      rules:
        - "Rule 1: Point beyond 3σ"
        - "Rule 2: 2 of 3 points beyond 2σ (same side)"
        - "Rule 3: 4 of 5 points beyond 1σ (same side)"
        - "Rule 4: 8 consecutive points on same side of mean"
      advantages: "Industry-standard for process monitoring"
      
    ml_anomaly_detector:
      algorithm: "Isolation Forest or Autoencoder"
      training: "Unsupervised on historical normal data"
      detection: "Anomaly score threshold"
      advantages: "Can detect complex multi-variate anomalies"
      
  regression_categories:
    sudden_regression:
      description: "Sharp drop in a short time period"
      example: "Coverage drops from 88% to 75% in 2 days"
      likely_causes: ["Broken test infrastructure", "Major refactoring", "Dependency upgrade"]
      urgency: "Critical - investigate immediately"
      
    gradual_regression:
      description: "Slow degradation over weeks"
      example: "Technical debt increases 0.5% per week for 6 weeks"
      likely_causes: ["Accumulating shortcuts", "Team turnover", "Scope creep"]
      urgency: "High - plan intervention soonest"
      
    cyclic_regression:
      description: "Recurring drops following a pattern"
      example: "Error rate spikes every 2 weeks before release"
      likely_causes: ["Rushed changes before deadlines", "Insufficient testing in crunch periods"]
      urgency: "Medium - address root cause (process issue)"
      
    false_positive:
      description: "Detected regression that isn't real"
      handling: "Human review required, tune thresholds"
```

---

## 工作流程

### 阶段一：数据准备与预处理

```
收到分析请求或定时触发
    ↓
[1] 从指标采集司获取时序数据
    ↓
[2] 数据完整性检查
    ↓
[3] 缺失值插补
    ↓
[4] 异常值处理决策
    ↓
[5] 数据重采样（如需不同粒度）
    ↓
进入分析阶段
```

#### 数据预处理管道

```python
"""
趋势分析数据预处理管道
"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

class TrendAnalysisPreprocessor:
    """质量指标时序数据预处理器"""
    
    def __init__(self):
        self.max_gap_tolerance = timedelta(hours=6)
        self.outlier_method = "iqr"  # or "zscore"
        
    def preprocess(
        self, 
        raw_data: List[Dict], 
        metric_name: str,
        target_granularity: str = "daily"
    ) -> pd.DataFrame:
        """
        预处理原始指标数据
        
        Args:
            raw_data: 从指标采集司获取的原始数据列表
            metric_name: 要分析的指标名
            target_granularity: 目标时间粒度 (hourly/daily/weekly)
            
        Returns:
            预处理后的DataFrame，包含datetime索引和value列
        """
        # 转换为DataFrame
        df = pd.DataFrame(raw_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.set_index('timestamp').sort_index()
        
        # 选择目标指标
        if metric_name in df.columns:
            series = df[metric_name].astype(float)
        else:
            raise ValueError(f"Metric '{metric_name}' not found in data")
        
        # 1. 缺失值处理
        series = self._handle_missing_values(series)
        
        # 2. 异常值标记（不删除，仅标记）
        outliers = self._detect_outliers(series)
        series = series.to_frame()
        series['is_outlier'] = outliers
        
        # 3. 重采样到目标粒度
        resampled = self._resample(series, target_granularity)
        
        # 4. 添加派生特征
        resampled = self._add_derived_features(resampled)
        
        return resampled
    
    def _handle_missing_values(self, series: pd.Series) -> pd.Series:
        """智能缺失值处理"""
        # 小间隙：线性插值
        # 大间隙：前向填充 + 标记
        gap_lengths = series.isnull().astype(int).groupby((~series.isnull()).cumsum()).sum()
        
        for start_idx, gap_length in gap_lengths.items():
            if gap_length <= 6:  # 小于6个数据点的小间隙
                series.iloc[start_idx:start_idx + int(gap_length)] = \
                    series.iloc[start_idx:start_idx + int(gap_length)].interpolate()
            else:
                # 大间隙用前值填充但标记
                series.iloc[start_idx:start_idx + int(gap_length)] = \
                    series.iloc[start_idx - 1] if start_idx > 0 else np.nan
                    
        return series
    
    def _detect_outliers(self, series: pd.Series) -> pd.Series:
        """异常值检测"""
        if self.outlier_method == "iqr":
            Q1 = series.quantile(0.25)
            Q3 = series.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            return (series < lower_bound) | (series > upper_bound)
        else:  # zscore
            z_scores = np.abs((series - series.mean()) / series.std())
            return z_scores > 3
            
    def _resample(self, df: pd.DataFrame, granularity: str) -> pd.DataFrame:
        """重采样到目标时间粒度"""
        agg_rules = {
            'value': 'mean',
            'is_outlier': 'max'  # 如果该周期内任何点是异常值则标记
        }
        
        freq_map = {
            'hourly': 'H',
            'daily': 'D',
            'weekly': 'W-MON',  # 周一到周日
            'monthly': 'MS'
        }
        
        resampled = df.resample(freq_map[granularity]).agg(agg_rules)
        return resampled
    
    def _add_derived_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """添加用于趋势分析的派生特征"""
        # 移动平均
        for window in [7, 14, 30]:
            if len(df) >= window:
                df[f'ma_{window}'] = df['value'].rolling(window=window).mean()
                
        # 变化率（日环比）
        df['pct_change_1d'] = df['value'].pct_change() * 100
        
        # 加速度（变化率的变化）
        df['acceleration'] = df['pct_change_1d'].diff()
        
        # 滚动标准差（波动性）
        df['rolling_std_7d'] = df['value'].rolling(window=7).std()
        
        # 相对于均值的偏离程度
        df['deviation_from_mean'] = (df['value'] - df['value'].mean()) / df['value'].std()
        
        return df
```

---

### 阶段二：趋势分析与模式识别

```
预处理完成
    ↓
[1] 长期趋势提取
    ↓
[2] 周期性模式识别
    ↓
[3] 变点检测
    ↓
[4] 相关性分析（跨指标）
    ↓
[5] 趋势强度评级
    ↓
输出趋势分析结果
```

#### 趋势分析输出格式

```json
{
  "analysis_id": "TREND-ANALYSIS-001",
  "timestamp": "2024-01-08T00:00:00Z",
  "analysis_period": {
    "start": "2024-01-01T00:00:00Z",
    "end": "2024-01-07T23:59:59Z",
    "duration_days": 7
  },
  "analyzed_metrics": [
    {
      "metric_name": "line_coverage_percent",
      "display_name": "行覆盖率",
      "dimension": "test_coverage",
      "current_value": 86.2,
      "target": 85.0,
      
      "trend_analysis": {
        "direction": "improving",
        "confidence": 0.87,
        "slope_per_week": 0.65,
        "r_squared": 0.72,
        "interpretation": "覆盖率以每周0.65%的速度稳步提升，趋势统计显著"
      },
      
      "moving_averages": {
        "ma_7": 85.8,
        "ma_14": 84.9,
        "ma_30": 83.5,
        "signal": "Short-term MA above long-term MA → bullish signal"
      },
      
      "seasonality": {
        "detected": true,
        "pattern": "weekly_cycle",
        "amplitude": 1.2,
        "description": "周末覆盖率略低（开发活动减少），周初回升"
      },
      
      "change_points": [
        {
          "date": "2024-01-03",
          "type": "step_increase",
          "before_mean": 83.5,
          "after_mean": 86.0,
          "magnitude": "+2.5%",
          "likely_cause": "新测试套件部署",
          "significance": "high (p < 0.01)"
        }
      ],
      
      "volatility": {
        "std_dev_7d": 1.45,
        "coefficient_of_variation": 1.68,
        "assessment": "low volatility - stable improvement"
      },
      
      "forecast": {
        "method": "Holt-Winters exponential smoothing",
        "next_7_days_prediction": [86.8, 87.1, 87.4, 87.6, 87.9, 88.1, 88.3],
        "prediction_interval_95_lower": [85.2, 85.5, 85.8, 86.0, 86.3, 86.5, 86.7],
        "prediction_interval_95_upper": [88.4, 88.7, 89.0, 89.2, 89.5, 89.7, 89.9],
        "target_achievement_date": "Already achieved (current > target)",
        "stretch_target_date": "2024-01-22 (predicted to reach 90%)"
      }
    },
    {
      "metric_name": "technical_debt_ratio",
      "display_name: "技术债务比率",
      "current_value": 6.8,
      "target": 5.0,
      
      "trend_analysis": {
        "direction": "worsening",
        "confidence": 0.92,
        "slope_per_week": 0.35,
        "interpretation": "技术债务持续增长，需要干预"
      },
      
      "forecast": {
        "next_4_weeks_prediction": [7.15, 7.5, 7.85, 8.2],
        "target_breach_date": "2024-02-15 (will exceed 10% threshold)",
        "urgency": "HIGH - plan debt reduction sprints immediately"
      }
    }
  ],
  
  "cross_metric_correlations": {
    "strong_correlations": [
      {
        "metric_a": "code_duplication_percent",
        "metric_b": "technical_debt_ratio",
        "correlation_coefficient": 0.78,
        "insight": "高重复率直接导致技术债务积累，应优先解决重复代码"
      },
      {
        "metric_a": "test_coverage_line",
        "metric_b": "bug_count_new",
        "correlation_coefficient": -0.65,
        "insight": "更高的测试覆盖率与新Bug数量负相关，验证了测试价值"
      }
    ],
    "surprising_correlations": [
      {
        "metric_a": "documentation_quality_score",
        "metric_b": "onboarding_time_new_developers",
        "correlation_coefficient": -0.71,
        "insight": "文档质量显著影响新人上手速度，ROI明确"
      }
    ]
  },
  
  "regression_alerts": [
    {
      "alert_id": "REGRESS-001",
      "severity": "warning",
      "metric": "branch_coverage_percent",
      "detected_at": "2024-01-07",
      "current_value": 77.8,
      "expected_value_based_on_trend": 81.2,
      "deviation: "-3.4 (unexpected drop)",
      "z_score": -2.4,
      "likely_cause": "New feature added without adequate branch testing",
      "recommended_action": "Review recent PRs for missing edge case tests",
      "auto_assigned_to": "testing_team_lead"
    }
  ],
  
  "executive_summary": {
    "overall_health_score": 82,
    "health_trend": "stable_improving",
    "key_insights": [
      "✅ 测试覆盖率持续改善，预计2周后达到90% stretch goal",
      "⚠️ 技术债务增长率加速，将在6周后突破阈值",
      "📊 代码重复与技术债务强相关(0.78)，建议启动去重专项",
      "🔍 发现分支覆盖率异常下降(-3.4%)，需调查"
    ],
    "prioritized_recommendations": [
      {
        "rank": 1,
        "action": "Investigate branch coverage regression",
        "impact": "prevent further quality erosion",
        "effort": "2 hours investigation"
      },
      {
        "rank": 2,
        "action": "Plan technical debt reduction sprint",
        "impact": "avoid future crisis",
        "effort": "1 sprint planning"
      },
      {
        "rank": 3,
        "action": "Launch code deduplication initiative",
        "impact": "address root cause of debt accumulation",
        "effort": "2 sprints"
      }
    ]
  }
}
```

---

### 阶段三：基线对比分析

```
趋势分析完成
    ↓
[1] 加载历史基线数据
    ↓
[2] 加载行业基准数据
    ↓
[3] 同比/环比计算
    ↓
[4] 差距分析
    ↓
[5] 竞品对标（如有）
    ↓
输出对比分析报告
```

#### 基线对比报告格式

```markdown
# 质量基线对比报告

**报告期间**: 2024年1月第1周 (2024-01-01 ~ 2024-01-07)  
**对比基线**: 2023年12月月均值 & 行业基准  
**编制**: 趋势分析司  

---

## 📊 总体对比概览

| 维度 | 当前值 | 上期基线 | 环比变化 | 行业基准(P50) | vs行业 | 评级 |
|------|--------|----------|----------|---------------|--------|------|
| **代码质量** | 82.5 | 80.2 | +2.3 ✅ | 78.0 | +4.5 | A |
| **测试覆盖** | 88.2 | 86.5 | +1.7 ✅ | 82.0 | +6.2 | A |
| **技术债务** | 6.8%↑ | 5.2% | +1.6 ⚠️ | 4.0% | -2.8 | C |
| **性能** | 91.0 | 89.5 | +1.5 ✅ | 88.0 | +3.0 | A |
| **安全合规** | 75.5 | 78.0 | -2.5 ❌ | 80.0 | -4.5 | D |
| **文档质量** | 78.0 | 76.5 | +1.5 ✅ | 72.0 | +6.0 | B |

**综合评分**: **82.0/100 (B+)**  
**趋势**: 📈 改善中 (+1.8 vs上期)

---

## 🔍 各维度详细对比

### 1️⃣ 代码质量维度 (A - 优秀)

**当前表现**: 82.5/100

| 子指标 | 当前 | 基线 | 变化 | 目标 | 状态 |
|--------|------|------|------|------|------|
| 平均圈复杂度 | 8.3 | 9.1 | -0.8 ✅ | ≤10 | 达标 |
| 代码重复率 | 3.2% | 4.1% | -0.9% ✅ | ≤5% | 达标 |
| 编码规范符合率 | 96.2% | 94.5% | +1.7% ✅ | ≥95% | 超标 |
| 技术债务比率 | 6.8% | 5.2% | +1.6% ❌ | ≤5% | 未达标 |

**关键洞察**:
- ✅ 圈复杂度和重复率持续改善，反映代码重构成效
- ⚠️ 但技术债务比率反升，说明新代码引入速度超过偿还速度
- 💡 建议：平衡新功能开发与债务偿还的比例

**趋势图描述**:
```
代码质量评分走势
95 ┤                              ╭──╮
90 ┤                         ╭────╯  ╰──╮
85 ┤                    ╭────╯           ╰─╮
80 ┤               ╭────╯                  ╰──╮
75 ┤          ╭────╯                          ╰──
70 ┤     ╭────╯
65 ┤╭────╯
60 ┤
   └──────────────────────────────────────────→ 时间
    Oct   Nov   Dec   Jan(当前)
```

### 2️⃣ 安全合规维度 (D - 需关注)

**当前表现**: 75.5/100 ⚠️

| 子指标 | 当前 | 基线 | 变化 | 目标 | 状态 |
|--------|------|------|------|------|------|
| OWASP评分 | B | A | -1级 ❌ | ≥A | 降级 |
| 依赖漏洞(High) | 3 | 1 | +2 ❌ | ≤2 | 超标 |
| 密钥暴露 | 0 | 0 | 0 ✅ | 0 | 达标 |
| 合规评分 | 78 | 82 | -4 ❌ | ≥80 | 未达标 |

**回归原因分析**:
1. **依赖漏洞增加**: 新引入的 `lodash@4.17.21` 包含已知CVE
2. **OWASP降级**: 新增API端点缺少输入验证
3. **合规扣分**: GDPR审计发现日志保留期限不符合要求

**紧急行动项**:
- 🔴 **P0**: 升级 lodash 或移除有漏洞的功能 (24h)
- 🔴 **P0**: 为新增API添加输入验证中间件 (48h)
- 🟠 **P1**: 更新日志保留策略至符合GDPR (1周)

---

## 📈 趋势预测

### 30天预测模型

基于 Holt-Winters 三参数指数平滑:

| 指标 | 当前 | 30天后预测 | 变化方向 | 置信度 |
|------|------|------------|----------|--------|
| 综合质量分 | 82.0 | 84.5 | ↑ 改善 | 82% |
| 测试覆盖率 | 88.2% | 91.0% | ↑ 改善 | 79% |
| 技术债务 | 6.8% | 8.2% | ↗ 恶化 | 88% |
| 安全评分 | 75.5 | 78.0 | → 稳定 | 65%* |

*\*安全评分预测置信度较低因近期波动大*

### 风险预警

| 风险事件 | 概率 | 影响 | 预计发生时间 | 应对措施 |
|----------|------|------|--------------|----------|
| 技术债务突破10%阈值 | 68% | 高 | ~8周后 | 启动偿债Sprint |
| 安全评分跌破70 | 25% | 极高 | ~12周后 | 加强安全培训 |
| 性能P99超1秒 | 15% | 中 | 不确定 | 监控负载增长 |

---

## 🎯 改进路线图

### 近期 (2周内)
- [ ] 修复依赖漏洞 (回归根因)
- [ ] 补充分支覆盖率测试
- [ ] 完善API输入验证

### 中期 (本月内)
- [ ] 启动技术债务偿还计划
- [ ] 文档质量提升至80+
- [ ] 建立安全编码检查清单

### 长期 (本季度)
- [ ] 综合评分目标: 85+
- [ ] 所有维度达到B级以上
- [ ] 建立行业领先实践

---

**报告审核**: 趋势分析司  
**分发**: 门下省、尚书省、项目管理办公室
```

---

## 与MARC资源协调器的资源需求

```yaml
marc_resource_requirements:
  compute_resources:
    cpu_cores: 4
    memory_gb: 8
    disk_space_gb: 20  # For model caching and intermediate results
    
  execution_time:
    trend_analysis: "< 3 minutes (7-day window)"
    regression_detection: "< 1 minute"
    forecast_generation: "< 2 minutes"
    full_report: "< 5 minutes"
    
  ml_model_requirements:
    libraries:
      - "scikit-learn (for regression, clustering, anomaly detection)"
      - "statsmodels (for time series analysis)"
      - "prophet (Meta's forecasting tool, optional)"
      - "scipy (for statistical tests)"
      
    models_trained:
      - "trend_extraction_model"
      - "seasonality_decomposition_model"
      - "anomaly_detection_model"
      - "forecasting_model"
      
  visualization_capabilities:
    chart_types:
      - "Line charts with confidence intervals"
      - "Heatmaps for correlation matrices"
      - "Control charts (X-bar, R, S charts)"
      - "Waterfall charts for change attribution"
      - "Forecast fan charts"
    output_formats: ["PNG", "SVG", "Interactive HTML (Plotly)"]
    
  data_access:
    read_from: "指标采集司的时序数据库"
    write_to: "reports/trend_analysis/"
    retention: "Keep all analyses, archive raw data after 2 years"
```

---

## 协同调用接口

| 接口名称 | 接口描述 | 调用方 |
|----------|----------|--------|
| `analyze_trends` | 执行趋势分析 | 定时任务、门下省主流程 |
| `detect_regression` | 检测质量回归 | 预警告警司、自动告警 |
| `compare_baseline` | 基线对比分析 | 项目经理、管理层汇报 |
| `generate_forecast` | 生成预测报告 | 规划会议、资源分配 |

---

## 版本历史

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| 1.0.0 | 2026-04-06 | 初始版本，包含完整的趋势分析、回归检测、基线对比、预测建模能力 |
