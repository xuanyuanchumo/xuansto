# 验证评估框架

## 验证评估框架概述

参照ECC的eval模式，建立多维度质量评估体系。

## pass@k指标

- pass@k: k次尝试中至少一次成功的概率
- pass@1=70%, pass@3=91%, pass@5=97%
- pass^k: k次尝试全部成功（一致性要求）
- 使用pass@k当只需成功一次，pass^k当一致性至关重要

## 检查点评估

关键Phase转换时执行显式检查点验证：

- Phase 2→3: 架构设计→测试先行（确认PLAN-ATOMIC通过）
- Phase 3→4: 测试先行→代码实现（确认TEST-FIRST通过+覆盖率≥80%）
- Phase 5→6: 测试验证→验收确认（确认所有E2E测试通过）

## 连续评估

每N次工具调用后自动运行测试套件+lint，确保增量变更不引入回归。

## GAN式生成-评估器

一个Agent生成代码，另一个Agent评估质量，形成对抗式改进循环：

- 生成器: Engineering层Agent
- 评估器: Quality层Agent（Code Reviewer + Bug Scanner）
- 循环: 生成→评估→反馈→改进，直到评估器评分≥80%

## 质量门禁与pass@k集成

门禁检查时记录pass@1和pass@3，用于追踪项目质量趋势和改进效果。
