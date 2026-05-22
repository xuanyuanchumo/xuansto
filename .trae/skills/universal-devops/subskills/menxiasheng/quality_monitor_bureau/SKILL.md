---
name: quality-monitor-bureau
parent: universal-devops
province: menxiasheng
description: |
  质量监控局 - 门下省持续质量监测单元

  【职责】质量指标采集、趋势分析、预警告警、质量门禁、质量仪表盘

  【触发条件】
  - 需要建立持续质量监控体系
  - 项目质量指标追踪和分析
  - 质量退化和预警处理

  【输出物】
  - 质量仪表盘
  - 趋势分析报告
  - 告警通知记录
  - 质量改进建议
---

# 质量监控局 (Quality Monitor Bureau)

> 门下省 · 审核层 · Universal DevOps v4.0

**状态**: 占位符 - 具体内容由后续任务填充

## 🤖 自主化操作指南 (v7.0)

### 推荐操作模式
| 操作场景 | 推荐模式 | 置信度 | 说明 |
|---------|---------|--------|------|
| 质量指标采集 | SCRIPTED_BATCH | 96% | 监探系统自动采集，高度标准化 |
| 质量报告生成 | HYBRID_ASSISTED | 88% | 数据自动聚合 + 人工解读趋势 |
| 质量阈值告警 | SCRIPTED_BATCH | 95% | 规则引擎自动触发告警 |
| 质量改进方案制定 | AUTONOMOUS_MANUAL | 75% | 需要综合分析和跨部门协调 |

### 常用工具组合
- **读操作**: Read, SearchCodebase, Grep（读取质量指标、历史基线）
- **写操作**: Write, SearchReplace（生成质量报告、改进计划）
- **批量操作**: Grafana dashboard配置、Prometheus查询语句、质量数据ETL脚本
- **验证操作**: 统计显著性检验工具、趋势预测算法

### 注意事项
- ⚠️ 质量指标应遵循SMART原则（Specific, Measurable, Achievable, Relevant, Time-bound）
- ⚠️ 避免指标博弈(Vanity Metrics)：选择能真实反映质量的leading indicators而非lagging indicators
- ✅ 建立"质量成本"意识：预防成本 < 鉴定成本 < 失败成本，投资预防最划算
- ✅ 质量改进采用PDCA循环：Plan → Do → Check → Act，持续迭代优化

## 🔗 资源协调要点 (v7.0)

### 常访问资源
| 资源类型 | 典型路径 | 锁策略建议 |
|---------|---------|-----------|
| METRIC | Prometheus/Grafana指标 | SHARED (读) |
| FILE | /docs/quality-reports/ | EXCLUSIVE (写) |
| DATABASE | 质量数据仓库 | SHARED (读) / EXCLUSIVE (写入) |
| API | 监控告警平台接口 | REAL_TIME |
| CONFIG | 质量阈值配置文件 | SHARED (读) / EXCLUSIVE (修改) |

### 竞争规避策略
1. **指标所有权明确**: 每个质量指标有唯一的owner，避免多头管理导致的混乱
2. **数据采集去重**: 多个监控系统采集相同指标时，建立单一数据源(single source of truth)
3. **告警抑制机制**: 相关联的质量问题合并告警，避免告警风暴淹没关键信息

## 💡 开源哲学应用 (v7.0)

### OpenCode 透明化
- 质量数据完全开放：所有团队成员可随时查看当前质量状态和历史趋势
- 质量目标对齐透明：公司级/部门级/团队级质量目标层级清晰，上下对齐
- 问题根因分享文化：质量问题复盘报告全员共享，鼓励从错误中学习

### OpenClaude 编排
- 异常检测智能化：利用机器学习算法自动识别质量指标的异常波动模式
- 预测性质量管理：基于历史数据预测未来质量趋势，提前预警潜在风险
- 跨团队质量协同：自动识别跨模块的质量依赖关系，协调联合改进行动

### Claw-Code 契约驱动
- 质量SLA量化定义：明确每个质量指标的达标线和容忍范围，写入服务等级协议
- 自动化质量门禁：质量指标不达标时自动阻止代码合入或产品发布
- 持续改进契约：每个迭代必须至少解决一个top质量问题，形成改进闭环
