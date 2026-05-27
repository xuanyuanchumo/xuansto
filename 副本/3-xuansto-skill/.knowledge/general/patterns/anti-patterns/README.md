---
id: anti-patterns
type: knowledge
category: patterns
tags: [反模式, 代码坏味道, God Class, Spaghetti Code, 重构]
version: 1.0.0
created: 2026-04-28
updated: 2026-04-28
confidence: high
---

# 反模式索引

反模式 (Anti-Pattern) 是看似合理但实际有害的解决方案模式。识别反模式是代码质量改进的起点。

## 代码级反模式

| 反模式 | 表现 | 危害 | 修复方向 |
|--------|------|------|----------|
| **God Class** | 单个类承担过多职责，数千行代码 | 难以理解/测试/修改 | 拆分为多个高内聚类 |
| **Spaghetti Code** | 逻辑纠缠不清，控制流混乱 | 无法维护和调试 | 重构为清晰模块结构 |
| **Magic Numbers** | 代码中出现未解释的硬编码数值 | 语义不明，修改易遗漏 | 提取为命名常量 |
| **Copy-Paste Programming** | 复制代码而非抽象复用 | 修改需同步多处 | 提取公共方法/基类 |
| **Premature Optimization** | 过早优化非关键路径 | 增加复杂度，偏离需求 | 先正确后优化，基于度量 |
| **Golden Hammer** | 熟悉一种工具就到处使用 | 方案不适配问题 | 拓宽技术视野，按需选型 |

## 架构级反模式

| 反模式 | 表现 | 危害 | 修复方向 |
|--------|------|------|----------|
| **Big Ball of Mud** | 无清晰架构，随意耦合 | 系统不可演化 | 引入分层和模块边界 |
| **Vendor Lock-in** | 深度绑定特定供应商 | 迁移成本极高 | 使用抽象层隔离 |
| **Distributed Monolith** | 微服务间强耦合 | 兼具两者缺点 | 服务自治，异步通信 |
| **Architecture by Implication** | 隐含假设驱动架构决策 | 决策缺乏依据 | 显式记录架构决策(ADR) |

## 流程级反模式

| 反模式 | 表现 | 修复方向 |
|--------|------|----------|
| **Analysis Paralysis** | 过度分析迟迟不行动 | 设定决策时限，迭代完善 |
| **Not Invented Here** | 拒绝使用外部方案 | 评估总拥有成本，优先复用 |
| **Bikeshedding** | 在琐碎问题上过度争论 | 聚焦核心决策，委托次要问题 |

## 检测方法

- 代码审查中重点关注：类行数 > 300、方法行数 > 30、圈复杂度 > 10
- 静态分析工具：SonarQube / ESLint / Pylint
- 架构守护：ArchUnit / Deptrac 验证依赖规则
