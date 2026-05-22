---
name: tdd-execution-si
parent: universal-devops
department: bingbu
province: shangshusheng
description: |
  TDD执行司 - 兵部·职方司

  【职责】测试先行开发、红绿重构循环、测试用例编写

  【触发条件】
  - 需要采用TDD方法论开发
  - 编写单元测试和集成测试
  - 测试驱动重构

  【能力】
  - Red-Green-Refactor循环
  - 测试骨架自动生成
  - Mock/Stub管理
  - 断言库支持
---

# TDD执行司 (TDD Execution Si)

> 尚书省 · 兵部 · Universal DevOps v4.0

**状态**: 占位符 - 具体内容由后续任务填充

## 🤖 自主化操作指南 (v7.0)

### 推荐操作模式
| 操作场景 | 推荐模式 | 置信度 | 说明 |
|---------|---------|--------|------|
| 测试先行编写(Red阶段) | HYBRID_ASSISTED | 88% | AI辅助生成测试骨架 + 人工细化场景 |
| 实现代码编写(Green阶段) | AUTONOMOUS_MANUAL | 80% | 需要创造性思维和算法设计 |
| 重构(Refactor阶段) | HYBRID_ASSISTED | 85% | IDE重构工具 + 人工确认语义不变 |
| 测试骨架生成 | SCRIPTED_BATCH | 94% | 基于函数签名自动生成测试模板 |

### 常用工具组合
- **读操作**: Read, SearchCodebase, Grep（读取需求规格、现有测试、类似实现）
- **写操作**: Write, SearchReplace（编写测试用例、实现功能代码、重构优化）
- **批量操作**: TDD循环自动化脚本、测试运行监视器、重构安全检查工具
- **验证操作**: 测试覆盖率实时监控、重构安全性验证(Refactoring Safety Checker)

### 注意事项
- ⚠️ TDD不是银弹：并非所有场景都适合TDD（如UI原型探索、算法研究阶段）
- ⚠️ 避免"假绿": 通过Hack方式让测试通过而不真正解决问题，违背TDD初衷
- ✅ 保持小步快跑：每个Red-Green-Refactor循环应在5-15分钟内完成
- ✅ 测试命名要表达意图：`should_return_error_when_input_is_invalid`比`test1`更有价值

## 🔗 资源协调要点 (v7.0)

### 常访问资源
| 资源类型 | 典型路径 | 锁策略建议 |
|---------|---------|-----------|
| FILE | /src/ 和对应的 /tests/ | PAIR_EDIT (同步修改) |
| WATCH | 文件变动监听(watch mode) | REAL_TIME |
| COVERAGE | 实时覆盖率面板 | LIVE_UPDATING |
| REFACTORING | IDE重构操作 | UNDO_SAFE (支持一键回滚) |
| SNAPSHOT | 快照测试文件(__snapshots__) | VERSION_CONTROLLED |

### 竞争规避策略
1. **Watch Mode隔离**: 每个开发者使用独立的watch进程，避免端口冲突
2. **测试并行化**: 利用多核CPU并行执行测试，保持Red-Green循环的快速反馈
3. **原子提交习惯**: 每个TDD循环完成后立即commit，保证版本库始终处于Green状态

## 💡 开源哲学应用 (v7.0)

### OpenCode 透明化
- TDD过程可视化：展示Red-Green-Refactor循环的频率、平均耗时、成功率等指标
- 测试驱动的设计决策公开：测试如何引导了API设计、边界条件处理等架构选择
- 重构勇气文化：鼓励大胆重构（因为有测试保护），分享重构前后的改进成果

### OpenClaude 编排
- 智能测试生成：基于函数签名和行为描述自动生成符合TDD规范的初始测试用例
- Red-Green循环计时器：监控每个循环的时长，超过阈值时提醒可能步子太大
- 重构建议引擎：检测代码中的坏味道(Bad Smell)并推荐安全的重构步骤

### Claw-Code 契约驱动
- 测试先行强制门禁：新功能必须先有失败的测试才能开始写实现代码
- 重构安全契约：重构前后必须保持所有测试通过+覆盖率不下降，否则阻止合入
- TDD纪律度量：跟踪团队的TDD采用率（测试先写的比例）、循环完成率等过程指标
