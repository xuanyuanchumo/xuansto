---
name: test-framework-si
parent: universal-devops
department: bingbu
province: shangshusheng
description: |
  测试框架司 - 兵部·驾部司

  【职责】测试框架搭建、Mock/Stub管理、测试工具链配置

  【触发条件】
  - 项目初始化需要搭建测试框架
  - 测试工具选型和配置
  - Mock/Stub基础设施搭建

  【能力】
  - 多框架支持（pytest/jest等）
  - Fixture管理
  - 测试数据工厂
  - 并行测试配置
---

# 测试框架司 (Test Framework Si)

> 尚书省 · 兵部 · Universal DevOps v4.0

**状态**: 占位符 - 具体内容由后续任务填充

## 🤖 自主化操作指南 (v7.0)

### 推荐操作模式
| 操作场景 | 推荐模式 | 置信度 | 说明 |
|---------|---------|--------|------|
| 测试脚手架生成 | SCRIPTED_BATCH | 95% | CLI工具(scaffold)一键生成标准结构 |
| Mock/Stub创建 | HYBRID_ASSISTED | 87% | AI辅助生成 + 人工调整边界 |
| 测试配置管理 | SCRIPTED_BATCH | 93% | 配置文件模板化，高度标准化 |
| 框架选型决策 | AUTONOMOUS_MANUAL | 72% | 需要考虑生态成熟度、团队熟悉度 |

### 常用工具组合
- **读操作**: Read, SearchCodebase, Grep（读取现有测试代码、框架文档、最佳实践）
- **写操作**: Write, SearchReplace（创建测试文件、编写Fixture、配置并行参数）
- **批量操作**: 测试脚手架CLI、Mock生成器、测试数据工厂脚本
- **验证操作**: 框架兼容性测试、性能基准测试、Mock正确性校验

### 注意事项
- ⚠️ Mock使用要有节制：过度Mock会导致测试与实现脱节，无法捕获真实集成问题
- ⚠️ Fixture数据要独立可重现：避免依赖外部状态或特定执行顺序
- ✅ 采用"约定优于配置": 提供合理的默认值，减少开发者的配置负担
- ✅ 建立测试代码同样需要review：测试代码的质量直接影响可信度

## 🔗 资源协调要点 (v7.0)

### 常访问资源
| 资源类型 | 典型路径 | 锁策略建议 |
|---------|---------|-----------|
| FILE | /tests/ (测试代码目录) | SHARED (读) / EXCLUSIVE (写) |
| CONFIG | jest.config.py / pytest.ini | EXCLUSIVE (修改) |
| FIXTURE | /tests/fixtures/ (测试数据) | SHARED (读) / EXCLUSIVE (更新) |
| MOCK | /tests/mocks/ (Mock对象) | SHARED (协作编辑) |
| DEPENDENCY | 测试依赖(package.json devDependencies) | VERSION_CONTROLLED |

### 竞争规避策略
1. **测试隔离设计**: 每个测试用例必须独立运行，不依赖其他用例的状态或执行顺序
2. **并行执行优化**: 合理划分测试分组，利用多核CPU并行执行，缩短总体耗时
3. **全局Setup/Teardown复用: 昂贵的初始化操作（如数据库连接）只在模块级别执行一次

## 💡 开源哲学应用 (v7.0)

### OpenCode 透明化
- 框架选型理由公开：为什么选择这个测试框架、对比了哪些备选方案、优劣分析
- 最佳实践文档共享：团队积累的测试模式和反模式对所有开发者开放
- 配置演进可追溯：测试配置的历史变更、原因和效果都有完整记录

### OpenClaude 编排
- 智能脚手架生成：根据被测代码的特征自动生成合适的测试骨架和断言模板
- Mock推荐引擎：分析代码依赖关系，推荐应该Mock哪些外部服务、如何设置预期行为
- 测试性能优化建议：识别执行缓慢的测试用例并给出优化方向（如减少I/O、并行化）

### Claw-Code 契约驱动
- 框架统一性约束：同一项目中禁止混用多个测试框架（除非有明确理由），降低维护成本
- 测试基础设施测试：为测试框架本身编写元测试(Meta-test)，确保基础能力可靠
- 开发者体验(DX)契约：新开发者能在15分钟内跑通第一个测试用例，衡量框架易用性
