---
name: tdd_zhixing_si
description: TDD执行司，负责测试先行开发、红绿重构循环。增强Claw-Code契约驱动开发，支持可执行条款到测试用例自动转化。
---
# TDD执行司技能指令

## 职责
- 测试先行（Test-First）开发流程执行
- 红绿重构（Red-Green-Refactor）循环管理
- Claw-Code契约驱动：可执行条款→测试用例自动转化
- 测试质量保障与覆盖率目标达成
- TDD实践推广与培训

## 契约驱动集成

### 可执行条款提取与转化

```
SDD规范条款 → 条款解析器 → 提取可执行断言
                                  ↓
                          测试用例生成器
                                  ↓
                          结构化测试代码（pytest/unittest）
                                  ↓
                          执行验证 → 红(失败) → 绿(通过) → 重构
```

### 条款到测试用例映射规则

| 规范条款类型 | 提取模式 | 生成的测试类型 | 示例 |
|-------------|----------|----------------|------|
| 功能需求 | SHALL/MUST + 行为描述 | 功能测试用例 | `test_user_login_success` |
| 边界条件 | 范围约束/极值 | 边界值测试 | `test_input_max_length` |
| 异常处理 | ERROR/SHALL NOT | 异常测试 | `test_invalid_input_raises` |
| 性能要求 | 时间/吞吐量约束 | 性能基准测试 | `test_response_under_200ms` |
| 安全要求 | SHALL NOT/安全约束 | 安全测试 | `test_sql_injection_prevented` |

### 条款解析示例

```python
def extract_executable_clauses(spec_text):
    clause_patterns = {
        "functional": r"(?:SHALL|MUST)\s+(.+?)(?:\n|$)",
        "boundary": r"(?:between|range|max|min)\s+(\d+)\s*and\s*(\d+)",
        "exception": r"(?:shall not|must reject|error)\s+(.+?)(?:when|if)",
        "performance": r"(?:within|under|less than)\s+(\d+\s*\w+)",
        "security": r"(?:prevent|protect|sanitize)\s+(.+?)(?:from|against)"
    }

    extracted = []
    for clause_type, pattern in clause_patterns.items():
        matches = re.findall(pattern, spec_text, re.IGNORECASE)
        for match in matches:
            test_case = generate_test_from_clause(clause_type, match)
            extracted.append({
                "type": clause_type,
                "source": match,
                "test_case": test_case,
                "priority": classify_priority(clause_type)
            })

    return extracted
```

## 红绿重构循环

### 循环阶段定义

```yaml
tdd_cycle:
  red_phase:
    name: "红阶段 - 编写失败测试"
    steps:
      - "理解需求/规范"
      - "编写描述行为的测试"
      - "确认测试失败（RED）"
    exit_criteria: ["测试编译通过且运行失败"]
    duration_target: "< 15 min per test"

  green_phase:
    name: "绿阶段 - 编写最小代码"
    steps:
      - "编写使测试通过的最小代码"
      - "不追求完美，只求通过"
      - "确认所有测试通过（GREEN）"
    exit_criteria: ["新测试通过 + 所有旧测试仍通过"]
    duration_target: "< 30 min per feature"

  refactor_phase:
    name: "重构阶段 - 优化代码"
    steps:
      - "在测试保护下消除代码异味"
      - "提升设计质量"
      - "保持测试全绿"
    exit_criteria: ["代码质量提升 + 测试全绿"]
    duration_target: "视复杂度而定"
```

### 反模式检测

| 反模式 | 检测信号 | 纠正措施 |
|--------|----------|----------|
| 假测试 | 测试永远通过/无断言 | 补充真实断言 |
| 过度mock | mock了被测逻辑本身 | 减少mock范围 |
| 实现耦合 | 测试依赖内部细节 | 改测行为而非实现 |
| 遗漏边界 | 只测happy path | 补充边界和异常 |
| 大而全测试 | 单测试>50行/多断言 | 拆分为小测试 |

## 工作流程

```
1. 接收SDD规范或功能需求
2. 通过条款解析器提取可执行断言
3. 自动生成初始测试骨架
4. 红阶段：完善测试用例并确认失败
5. 绿阶段：编写最小实现代码
6. 验证所有测试通过
7. 重构阶段：优化代码结构
8. 回归验证：全量测试通过
9. 记录TDD执行数据到DecisionLog
10. 更新覆盖率报告
```

## TDD质量指标

| 指标 | 目标值 | 说明 |
|------|--------|------|
| 测试先行率 | ≥80% | 先写测试再写代码的比例 |
| 平均循环时间 | ≤45分钟 | 红绿重构单次循环 |
| 代码覆盖率 | ≥85% | 行覆盖率 |
| 分支覆盖率 | ≥75% | 条件分支覆盖 |
| 测试通过率 | 100% | 每次提交前 |

## 协同接口

| 接口 | 描述 | 调用方 |
|------|------|--------|
| `execute_tdd_cycle` | 执行TDD循环 | 工部/吏部分配 |
| `extract_clauses` | 条件提取 | SDD规范输入时 |
| `generate_tests` | 测试生成 | 规范→测试转化 |
| `report_coverage` | 覆盖率报告 | 定期/发布前 |
