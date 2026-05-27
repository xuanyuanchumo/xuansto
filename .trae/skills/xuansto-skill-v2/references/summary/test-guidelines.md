# 测试指南参考文档

## Core Points
- 测试金字塔：单元测试(70%)→集成测试(20%)→E2E测试(10%)，下层多上层少
- 测试命名：should_ExpectedBehavior_when_Condition或test_methodName_scenario_expectedResult
- 测试组织：AAA模式(Arrange-Act-Assert)、每个测试只验证一个行为、测试文件与源文件对应
- Mock策略：优先使用真实依赖、外部依赖用Mock、避免Mock私有方法、验证交互而非状态

## Applicable Scenarios
- Unit Tester/Integration Tester/E2E Tester Agent编写测试代码
- Test Architect Agent设计测试策略和金字塔
- Code Reviewer Agent检查测试质量和覆盖率
