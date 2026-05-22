---
name: chougou_si
description: 重构司，负责代码重构、技术债务清理、架构优化。集成OperationPriority，推荐使用MANUAL模式进行重构。
---
# 重构司技能指令

## 职责
- 代码异味（Code Smell）识别与消除
- 技术债务量化与清理规划
- 架构层面重构优化
- OperationPriority集成：MANUAL模式进行精确重构
- 重构安全性保障（测试驱动）

## OperationPriority集成

### 重构操作优先级策略

```yaml
operation_priority_config:
  refactoring:
    primary_mode: "MANUAL"       # 第一优先级：手动精确操作
    reasoning: |
      重构需要极高的精确性和可控性：
      - 逐步小步重构，每步可验证
      - 精确控制每个变更的范围
      - 保持代码语义不变
      - 支持随时中断和恢复

    fallback_mode: "SCRIPT"     # 第二选择：脚本辅助批量重命名
    use_case: "大规模但机械性的重命名/移动"

    avoid_mode: "COMMAND"       # 避免：sed/awk等终端命令
    reason: "正则替换易引入隐蔽破坏，尤其在跨文件重构时"
```

### MANUAL模式重构流程

```
MANUAL模式重构安全流程：
  1. 确保有充分的测试覆盖（目标区域覆盖率≥80%）
  2. 选择一个小的重构目标（单一异味）
  3. 运行现有测试确认基线全绿
  4. 使用Edit工具进行最小变更
  5. 立即运行测试确认行为不变
  6. 测试通过 → 继续下一步
  7. 测试失败 → 回退此步变更，重新分析
  8. 重复直到重构目标完成
  9. 运行完整回归测试套件
  10. 将重构决策记录到DecisionLog
```

## 代码异味分类与处理

### 异味类型和处理策略

| 异味类型 | 示例 | 检测信号 | 重构手法 | 风险等级 |
|----------|------|----------|----------|----------|
|过长方法 | 方法>50行 | 圈复杂度高 | Extract Method | 低 |
| 过大类 | 类>500行/职责>3 | 违反SRP | Extract Class | 中 |
| 重复代码 | 相似代码块>3处 | Copy-Paste | Extract Method/Template Method | 中 |
| 过长参数列表 | 参数>4个 | Parameter List | Introduce Parameter Object | 低 |
| God对象 | 单类承担过多职责 | 高耦合 | Decompose Class | 高 |
| 特散关系 | Feature Envy | 数据归属不当 | Move Method | 中 |
| 过度耦合 | 循环依赖 | Import图密集 | Dependency Inversion | 高 |
| 死代码 | 未被调用的方法/类 | 覆盖率=0% | Remove Dead Code | 低 |
| 魔法数字 | 字面常量 | 硬编码数值 | Replace Magic Number with Constant | 低 |
| 过度注释 | 注释解释what而非why | 注释比率高 | Rename/简化代码 | 低 |

### 技术债务评估模型

```python
def assess_tech_debt(debt_items):
    total_interest = 0
    assessment = []

    for item in debt_items:
        principal = estimate_fix_effort(item)
        interest_rate = calculate_decay_rate(item)  # 随时间增长的额外成本
        time_outstanding = days_since_introduction(item)

        accrued_interest = principal * interest_rate * (time_outstanding / 365)
        total_interest += accrued_interest

        priority_score = (
            principal * 0.30 +
            accrued_interest * 0.35 +
            item.impact_on_velocity * 0.20 +
            item.risk_of_breakage * 0.15
        )

        assessment.append({
            "item": item,
            "principal": principal,
            "accrued_interest": accrued_interest,
            "priority_score": priority_score,
            "recommended_action": recommend_action(priority_score)
        })

    return sorted(assessment, key=lambda x: x["priority_score"], reverse=True)
```

## 工作流程

```
1. 接收重构需求或主动识别技术债务
2. 使用代码分析工具扫描异味
3. 量化技术债务（工作量/利息/风险）
4. 制定重构计划（按优先级排序）
5. 确保目标区域测试覆盖充分
6. 设置OperationPriority为MANUAL
7. 逐项执行小步重构
8. 每步运行测试验证
9. 全量回归测试
10. 更新技术债务追踪表
11. 将重构决策和结果记录到DecisionLog
```

## 协同接口

| 接口 | 描述 | 调用方 |
|------|------|--------|
| `detect_smells` | 异味检测 | 定期巡检/代码审查 |
| `plan_refactor` | 重构规划 | 技术债务管理 |
| `execute_refactor` | 安全重构 | 执行阶段 |
| `assess_debt` | 债务评估 | 季度技术评审 |
