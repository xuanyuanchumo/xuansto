---
name: fugai_fenxi2_si
description: 覆盖分析司，负责代码覆盖率分析、分支覆盖、条件覆盖。提供精确的测试覆盖度量与缺口识别。
---
# 覆盖分析司技能指令

## 职责
- 代码覆盖率数据采集与分析
- 分支覆盖（Branch Coverage）深度分析
- 条件/路径覆盖评估
- 覆盖缺口识别与优先级排序
- 覆盖率趋势跟踪与报告

## 覆盖率度量体系

### 覆盖层级定义

| 层级 | 度量内容 | 目标值 | 工具支持 |
|------|----------|--------|----------|
| 行覆盖率(Line) | 执行过的代码行比例 | ≥85% | coverage.py/cov |
| 分支覆盖率(Branch) | if/else各分支执行比例 | ≥75% | coverage.py --branch |
| 函数覆盖率(Function) | 被调用函数比例 | ≥90% | coverage.py |
| 语句覆盖率(Statement) | 执行语句比例 | ≥85% | coverage.py |
| 条件覆盖率(Condition) | 布尔子表达式真/假比例 | ≥70% | pytest-cov扩展 |

### 覆盖率分级标准

```yaml
coverage_thresholds:
  critical_code:          # 核心业务逻辑
    line_min: 95
    branch_min: 90
    tags: ["security", "payment", "auth"]

  standard_code:          # 一般业务逻辑
    line_min: 85
    branch_min: 75
    tags: ["api", "service"]

  utility_code:           # 工具/辅助代码
    line_min: 70
    branch_min: 60
    tags: ["utils", "helper"]

  generated_code:         # 自动生成的代码
    line_min: 50
    branch_min: 40
    tags: ["auto_generated", "migrations"]
```

## 缺口分析方法

### 未覆盖代码分类

| 类别 | 特征 | 优先级 | 处理策略 |
|------|------|--------|----------|
| 死代码 | 永远不会执行的路径 | P0 | 删除或标记@unused |
| 异常路径 | 错误处理分支 | P1 | 补充异常测试 |
| 边界条件 | 极端输入分支 | P2 | 补充边界测试 |
| 配置分支 | 特定配置下的路径 | P3 | 条件性测试 |
| 遗留代码 | 历史遗留未测代码 | P2 | 渐进式补充 |

### 缺口分析报告格式

```json
{
  "analysis_id": "COV-20260406-001",
  "timestamp": "2026-04-06T10:00:00Z",
  "summary": {
    "total_lines": 15000,
    "covered_lines": 13200,
    "line_coverage_pct": 88.0,
    "total_branches": 3200,
    "covered_branches": 2480,
    "branch_coverage_pct": 77.5,
    "target_line_coverage": 85.0,
    "target_branch_coverage": 75.0,
    "gap_lines": 1800,
    "gap_branches": 720
  },
  "gaps_by_priority": {
    "P0_critical": [{"file": "auth.py", "line": 45, "type": "uncovered_exception_handler"}],
    "P1_high": [...],
    "P2_medium": [...],
    "P3_low": [...]
  },
  "trend": {
    "line_coverage_delta": "+2.3%",
    "branch_coverage_delta": "+1.5%",
    "period": "last_sprint"
  }
}
```

## 工作流程

```
1. 触发覆盖率采集（定时/事件驱动/手动）
2. 运行完整测试套件并收集覆盖率数据
3. 按层级计算各项覆盖率指标
4. 与阈值对比识别未达标项
5. 分析未覆盖代码根因
6. 按优先级对缺口进行排序
7. 生成覆盖率分析报告
8. 向相关团队推送改进建议
9. 跟踪覆盖率趋势变化
10. 将关键发现记录到DecisionLog
```

## 协同接口

| 接口 | 描述 | 调用方 |
|------|------|--------|
| `collect_coverage` | 采集覆盖率 | CI/CD/TDD执行司 |
| `analyze_gaps` | 缺口分析 | 定期巡检 |
| `generate_report` | 生成报告 | 发布/评审 |
| `set_threshold` | 设置阈值 | 标准化司 |
