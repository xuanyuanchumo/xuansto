# 无障碍测试自动化参考文档

## Core Points
- WCAG 2.1 AA合规标准基于四大原则：可感知、可操作、可理解、健壮性
- axe-core是核心自动化测试引擎，支持Playwright和Jest集成，可配置规则和标签过滤
- Pa11y提供命令行和CI/CD集成能力，支持多URL批量测试和登录态测试
- 测试金字塔：全自动(axe-core/Pa11y CI) → 半自动(axe DevTools) → 手动(屏幕阅读器/键盘导航)
- 与xuansto集成点：Quality Gates门禁检查、Webapp Testing流水线、组件级jest-axe断言

## Applicable Scenarios
- 实现无障碍自动化测试和CI/CD集成
- 配置WCAG 2.1 AA合规检查规则
- 设计无障碍测试策略（自动化+手动）
