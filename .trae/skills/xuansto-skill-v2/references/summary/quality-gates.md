# 质量门禁详细定义

## Core Points
- 54项质量门禁完整定义，覆盖9阶段工作流全过程
- 门禁别名映射：语义化别名(如TEST-PASS)与结构化ID(如GATE-008)的对应关系
- 门禁分类：设计评审(Phase 0)、需求验证(Phase 1)、架构验证(Phase 2)、测试先行(Phase 3)、代码质量(Phase 4)、安全审计(Phase 5-6)、部署验证(Phase 7)、文档完整(Phase 8)
- 门禁执行：blocking(阻断流水线)和non-blocking(仅告警)两种模式

## Applicable Scenarios
- Code Reviewer Agent执行质量门禁检查
- Runtime Supervisor管理门禁恢复流程
- 配置项目质量门禁和通过标准
