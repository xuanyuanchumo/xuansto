---
name: huigui_ceshi_si
description: 回归测试司，负责回归套件管理、冒烟测试、全量回归。确保每次变更不破坏已有功能。
---
# 回归测试司技能指令

## 职责
- 回归测试套件的维护与管理
- 冒烟测试（Smoke Test）快速验证
- 全量回归测试执行与结果分析
- 回归缺陷追踪与趋势分析
- 测试用例生命周期管理

## 回归测试分层策略

### 测试金字塔中的回归定位

```
          ╱╲
         ╱E2E╲         ← 冒烟回归（核心路径）
        ╱──────╲
       ╱集成测试 ╲      ← 功能回归（受影响模块）
      ╱──────────╲
     ╱  单元测试   ╲    ← 全量回归（每日构建）
    ╱──────────────╲
```

### 回归分层执行策略

| 层级 | 触发时机 | 范围 | 执行时长 | 目标 |
|------|----------|------|----------|------|
| 冒烟测试 | 每次提交后 | 核心用户路径(5-10%) | ≤5min | 快速反馈 |
| 功能回归 | PR合并前 | 变更影响域(30-50%) | ≤30min | 保证质量 |
| 全量回归 | 每日构建/发布前 | 全部用例(100%) | ≤2h | 全面保障 |
| 发布回归 | 版本发布前 | 全部+性能+安全 | ≤4h | 最终把关 |

## 冒烟测试套件

### 核心冒烟用例选择标准

```yaml
smoke_test_selection:
  criteria:
    - user_facing: true          # 用户可见的功能
    - critical_path: true        # 核心业务路径
    - high_failure_impact: true  # 失败影响大
    - frequently_used: true      # 高频使用的功能

  typical_smoke_suite:
    - "用户登录/登出"
    - "核心CRUD操作"
    - "API健康检查"
    - "数据库连接"
    - "核心搜索功能"
    - "权限验证"
    - "支付流程(如有)"

  execution_config:
    parallel: true
    max_parallel_workers: 4
    timeout_per_test: "60s"
    fail_fast: true
    retry_on_flaky: 1
```

## 回归缺陷管理

### 缺陷趋势分析

```python
def analyze_regression_trend(defect_history):
    trend_analysis = {
        "total_defects": len(defect_history),
        "defects_by_severity": count_by_severity(defect_history),
        "defects_by_category": count_by_category(defect_history),
        "escape_rate": calculate_escape_rate(defect_history),
        "mean_time_to_detect": calculate_mttd(defect_history),
        "recurring_defects": identify_recurring(defect_history),
        "trend_direction": detect_trend(defect_history)
    }

    alerts = []
    if trend_analysis["escape_rate"] > 0.05:
        alerts.append("缺陷逃逸率超标，需加强回归覆盖")
    if len(trend_analysis["recurring_defects"]) > 3:
        alerts.append(f"发现{len(trend_analysis['recurring_defects'])}个重复缺陷，需根治")

    return RegressionReport(analysis=trend_analysis, alerts=alerts)
```

### 用例健康度管理

| 健康状态 | 定义 | 处理方式 |
|----------|------|----------|
| 健康 | 连续20次通过 | 正常执行 |
| 不稳定 | 10次运行中失败1-3次 | 标记flaky，排查原因 |
| 过时 | 关联功能已变更或移除 | 更新或归档用例 |
| 冗余 | 与其他用例高度重复 | 合并或删除 |

## 工作流程

```
1. 监控触发条件（提交/PR/定时/发布）
2. 确定回归测试层级和范围
3. 选择对应测试套件
4. 执行回归测试
5. 收集和分析结果
6. 分类处理失败的用例
7. 新增回归缺陷到追踪系统
8. 生成回归测试报告
9. 更新用例健康度状态
10. 将重要发现记录到DecisionLog
```

## 协同接口

| 接口 | 描述 | 调用方 |
|------|------|--------|
| `run_smoke` | 执行冒烟测试 | 每次CI |
| `run_regression` | 执行回归 | PR/发布前 |
| `manage_suite` | 套件管理 | 定期维护 |
| `report_trend` | 趋势报告 | 周报/月报 |
