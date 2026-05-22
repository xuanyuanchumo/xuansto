# Universal DevOps v6.0 规格说明书（Spec）- 全面增强版

> **版本**: v6.0.0-spec-full-enhanced
> **日期**: 2026-04-06
> **状态**: 草案（待评审）
> **编码格式**: UTF-8 无 BOM
> **基于**: v6.0.0-spec-enhanced 全面审查与补充

---

## 📋 文档概述

### 1.1 项目背景与目标

#### 1.1.1 项目愿景

构建一个**通用AI全生命周期开发技能系统（Universal SKILL）**，用于 **Trae IDE** 或 **Claude Code** 环境中进行 AI 自动自主化软件开发指导。本系统不是简单的脚本自动化工具，而是一套**AI可自主遵循的工程方法论体系**，让AI能够像资深工程师一样进行项目开发的全流程管理。

#### 1.1.2 设计理念来源（非集成，仅借鉴）

| 理念来源 | 借鉴内容 | 本系统实现方式 |
|---------|---------|--------------|
| **OpenCode** | 透明化开发、多Agent分工、ReAct决策循环、Tool抽象、权限控制 | 三省六部透明决策、二十四司职责分离、AOF四层框架、各司Python脚本、RBAC权限模型 |
| **OpenClaude** | Coordinator编排模式、Team System协作、TaskQueue调度、SubAgent技能化 | Agency-Agent Bridge、尚书省六部协作、吏部任务调度、24司=24个专业SubAgent |
| **claw-code (OpenClaw)** | Agent Engineering人机协同、SDD规范驱动、TDD测试驱动、Gateway控制平面、纪律性工程方法 | AOG自主操作指南、SDD+TDD融合引擎、三省协调器、结构化开发流程 |
| **Harness Engineering** | 渐进式发布、Pipeline as Code、SRE实践、安全左移STO、Feature Flags、混沌工程、FinOps成本优化 | CD部署管理器、CI Pipeline Orchestrator、SRE可靠性引擎、Security STO编排器等七大模块 |

#### 1.1.3 核心架构：三省六部二十四司

```
┌─────────────────────────────────────────────────────────────┐
│                Universal DevOps v6.0 架构                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│   │   中书省     │───▶│   门下省     │───▶│   尚书省     │     │
│   │  （决策层）   │    │  （审核层）   │    │  （执行层）   │     │
│   │  4局 × 1    │    │  4局 × 1    │    │  6部×4司=24 │     │
│   └─────────────┘    └─────────────┘    └─────────────┘     │
│                                                             │
│   ┌─────────────────────────────────────────────────────┐  │
│   │          四维度输出防线 (4D Output Defense)           │  │
│   │  提示词层 + 原生能力层 + 底层约束层 + 兜底机制层      │  │
│   └─────────────────────────────────────────────────────┘  │
│                                                             │
│   ┌─────────────────────────────────────────────────────┐  │
│   │     三模运行架构: 自动化 + 自主 + Agent协作          │  │
│   └─────────────────────────────────────────────────────┘  │
│                                                             │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│   │ SDD+TDD     │  │ Agency-Agent │  │ Harness      │       │
│   │ 融合引擎     │  │ Bridge       │  │ Integration  │       │
│   └─────────────┘  └─────────────┘  └─────────────┘       │
│                                                             │
│   ┌─────────────────────────────────────────────────────┐  │
│   │              元技能层 (Meta-Skill Layer)              │  │
│   │         自评估 │ 自优化 │ 自扩展 │ 自打包             │  │
│   └─────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 🌟 四维度输出防线体系（核心创新）

这是本系统的**核心质量保障机制**，确保AI在任何情况下都能产出高质量、可靠的输出物。

```
┌─────────────────────────────────────────────────────────────┐
│              四维度输出防线 (4D Output Defense)               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  第一维：提示词层 (Prompt Layer)                        │  │
│  │  ─────────────────────────────────────────────────    │  │
│  │  • AOG（自主操作指南）= 每个司/局的SKILL.md            │  │
│  │  • 任务触发词库 = 自然语言→精确任务映射                 │  │
│  │  • 上下文注入模板 = 项目信息/历史决策/当前状态          │  │
│  │  • 角色扮演指令 = "你是XX司的AI专家，请..."            │  │
│  │  • 输出格式约束 = 必须使用MD格式/UTF-8无BOM            │  │
│  └───────────────────────────────────────────────────────┘  │
│                          ▼                                  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  第二维：原生能力层 (Native Capability Layer)          │  │
│  │  ─────────────────────────────────────────────────    │  │
│  │  • AI原生代码理解能力 = 阅读分析任意代码               │  │
│  │  • AI原生设计能力 = 架构/UI/数据库/API设计             │  │
│  │  • AI原生测试能力 = 编写/执行/分析测试用例             │  │
│  │  • AI原生重构能力 = 识别坏味道并安全重构              │  │
│  │  • AI原生修复能力 = 根因分析+方案设计+补丁生成        │  │
│  │  💡 这是"自主化"的核心：AI不依赖脚本能独立完成这些      │  │
│  └───────────────────────────────────────────────────────┘  │
│                          ▼                                  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  第三维：底层约束层 (Underlying Constraint Layer)      │  │
│  │  ─────────────────────────────────────────────────    │  │
│  │  • 质量门禁阈值 = 不达标禁止合并/发布                  │  │
│  │  • 安全边界规则 = 高风险操作(≥7级)需审批/≥9级阻断     │  │
│  │  • 编码规范强制 = PEP8/ESLint/StyleGuide自动检查       │  │
│  │  • 文档格式约束 = UTF-8无BOM / MD格式 / 结构化模板    │  │
│  │  • API契约约束 = OpenAPI规范一致性校验                 │  │
│  │  • 性能基线约束 = P99延迟/CPU/内存阈值监控             │  │
│  └───────────────────────────────────────────────────────┘  │
│                          ▼                                  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  第四维：兜底机制层 (Fallback Mechanism Layer)         │  │
│  │  ─────────────────────────────────────────────────    │  │
│  │  • 回滚机制 = Git快照/备份点/一键回滚                  │  │
│  │  • 降级策略 = AI自主失败→切换到自动化脚本模式          │  │
│  │  • 审计日志 = 每步操作完整记录，支持追溯              │  │
│  │  • 人工干预 = Ctrl+C/"停止"/关键节点确认               │  │
│  │  • 应急预案 = 已知故障模式+标准恢复流程               │  │
│  │  • 幂等保证 = 重复执行不会产生副作用                   │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### 四维度详细说明

| 维度 | 核心作用 | 关键组件 | 失败后果 | 兜底方式 |
|------|---------|---------|---------|---------|
| **① 提示词层** | 引导AI正确理解任务意图和执行方式 | AOG指南、触发词库、上下文模板 | AI误解需求或输出格式错误 | 第二维原生能力补偿 |
| **② 原生能力层** | AI自主完成创造性/判断性任务的核心能力 | 代码理解、设计、测试、重构、修复能力 | 任务无法完成或质量不达标 | 第三维约束层拦截低质量输出 |
| **③ 底层约束层** | 强制性质量/安全/合规底线 | 质量门禁、安全规则、编码规范、性能基线 | 低质量代码流入下一环节 | 第四维兜底机制回滚+告警 |
| **④ 兜底机制层** | 最后的安全网，确保系统永不崩溃 | 回滚、降级、审计、人工干预、应急预案 | 系统处于不可恢复状态 | 人工介入处理 |

---

## 🏛️ 架构设计

### 2.1 三省六部二十四司详细设计

#### 2.1.1 中书省（决策层）- 4局

| 局名 | 英文标识 | 核心职责 | 对应Agency Agents | 关键产出物 | Python脚本 |
|------|---------|---------|-------------------|-----------|-----------|
| **需求分析局** | `requirements_bureau` | 需求收集、分析、拆解、优先级排序、业务建模 | Product Manager, Sprint Prioritizer, Trend Researcher, Academic Historian | PRD、用户故事、验收标准、业务流程图 | `requirements_bureau.py` |
| **架构设计局** | `architecture_bureau` | 系统架构、技术选型、模块划分、接口定义、设计模式选择 | Software Architect, Backend Architect, Cloud Architect, UX Architect, ZK Steward | 架构图(mermaid)、ADR、API设计、模块规格 | `architecture_bureau.py` |
| **规范制定局** | `standards_bureau` | 编码规范、文档标准、流程规范、命名约定、Lint规则生成 | Senior Developer, Code Reviewer, Engineering SRE | 编码规范文档、Checklist、Lint配置、命名约定 | `standards_bureau.py` |
| **方案审议局** | `review_bureau` | 方案评审、风险评估、可行性分析、决策记录、技术债务评估 | Senior Project Manager, Experiment Tracker, Nexus Strategist | 评审报告、风险矩阵、决策日志、技术债务清单 | `review_bureau.py` |

#### 2.1.2 门下省（审核层）- 4局

| 局名 | 英文标识 | 核心职责 | 对应Agency Agents | 关键产出物 | Python脚本 |
|------|---------|---------|-------------------|-----------|-----------|
| **代码审查局** | `code_review_bureau` | Code Review、静态分析、安全扫描、性能审计、坏味道检测 | Code Reviewer, Security Engineer, Performance Benchmarker, Engineering SRE | 审查报告、问题清单、改进建议、安全扫描结果 | `code_review_bureau.py` |
| **测试验证局** | `testing_bureau` | 测试策略制定、测试用例设计、自动化测试执行、覆盖率分析 | API Tester, Evidence Collector, Test Results Analyzer, Testing API Tester | 测试报告、覆盖率报告、缺陷统计、测试策略文档 | `testing_bureau.py` |
| **质量监控局** | `quality_monitor_bureau` | 质量指标采集、趋势分析、预警告警、质量门禁、仪表盘生成 | Analytics Reporter, Reality Checker, Sales Engineer | 质量仪表盘、趋势图、告警通知、质量评分 | `quality_monitor_bureau.py` |
| **合规审计局** | `compliance_bureau` | 合规检查、许可证审计、安全合规、数据隐私、OWASP Top 10 | Compliance Auditor, Legal Compliance Checker, Security Engineer | 合规报告、审计日志、整改建议、许可证清单 | `compliance_bureau.py` |

#### 2.1.3 尚书省（执行层）- 六部二十四司

##### 吏部（Libu）- 人员与调度管理（4司）

| 司名 | 英文标识 | 核心职责 | v6.0增强能力 | 对应Agents | Python脚本 |
|------|---------|---------|-------------|------------|-----------|
| **选司（Agent调度司）** | `agent_dispatch_si` | AI Agent的任务分配、负载均衡、优先级调度、跨工具协调 | 智能任务路由、动态负载感知、跨IDE协调(Trae/Claude/Cursor) | Agents Orchestrator, Studio Producer, Project Shepherd | `agent_dispatch_si.py` |
| **司封司（角色管理司）** | `role_management_si` | 角色定义、权限管理、职责边界划分、RBAC模型 | 自适应角色切换、权限自动收缩、动态RBAC | Senior Project Manager, Project Shepherd | `role_management_si.py` |
| **司勋司（技能匹配司）** | `skill_matching_si` | 技能识别、能力评估、最优Agent/Skill选择 | 意图驱动的技能推荐、多维度匹配算法、跨技能组合 | Rapid Prototyper | `skill_matching_si.py` |
| **考功司（协调司）** | `coordination_si` | 跨部门协作、冲突解决、进度同步、依赖管理 | 自主冲突调解、进度预测、DAG依赖管理 | Project Shepherd | `coordination_si.py` |

##### 户部（Hubu）- 环境与资源管理（4司）

| 司名 | 英文标识 | 核心职责 | v6.0增强能力 | Harness集成 | Python脚本 |
|------|---------|---------|-------------|-----------|-----------|
| **度支司（环境配置司）** | `environment_config_si` | 开发/测试/生产环境配置、环境一致性检测、PowerShell 7环境验证 | 自适应环境探测、配置漂移自修复、多环境同步、PS7兼容检测 | Harness Environment | `environment_config_si.py` |
| **金部司（依赖管理司）** | `dependency_mgmt_si` | 依赖版本管理、漏洞扫描(CVE)、依赖更新策略、兼容性分析 | 智能依赖升级决策、自动CVE扫描、兼容性矩阵生成 | Harness Security STO | `dependency_mgmt_si.py` |
| **仓部司（资源优化司）** | `resource_optimization_si` | 计算资源分配、成本优化(FinOps)、性能调优、资源利用率监控 | 动态资源伸缩预测、成本预警、资源效率报告 | Harness Cost Optimization | `resource_optimization_si.py` |
| **户部司（基础设施司）** | `infrastructure_si` | CI/CD流水线、容器化(Docker/K8s)、云资源管理、IaC生成 | 流水线自主编排、Kubernetes YAML生成、GitHub Actions/GitLab CI输出 | Harness CI/CD Pipeline | `infrastructure_si.py` |

##### 礼部（Libu2）- 文档与知识管理（4司）

| 司名 | 英文标识 | 核心职责 | v6.0增强能力 | 模板库支持 | Python脚本 |
|------|---------|---------|-------------|-----------|-----------|
| **祠部司（文档司）** | `documentation_si` | API文档(OpenAPI/Swagger)、技术文档、用户手册生成与维护 | 语义感知增量文档更新、自动API Doc生成(MD格式)、多格式导出 | api/, architecture/ | `documentation_si.py` |
| **主客司（模板管理司）** | `template_management_si` | 文档模板管理(Jinja2)、模板版本控制、模板定制与继承 | 模板智能推荐、模板继承链、10大类模板库管理 | templates/* (10类) | `template_management_si.py` |
| **膳部司（知识库司）** | `knowledge_base_si` | 知识沉淀、经验复用、最佳实践库维护、RAG检索 | 知识图谱自动构建、RAG检索增强、经验复用推荐 | knowledge/ | `knowledge_base_si.py` |
| **仪制司（标准化司）** | `standardization_si` | 命名规范强制、格式标准统一(MD/UTF-8无BOM)、Lint规则自动生成 | 规则自动推断、格式强制校验、编码风格统一 | coding_standards/ | `standardization_si.py` |

##### 兵部（Bingbu）- 测试与质量管理（4司）

| 司名 | 英文标识 | 核心职责 | v6.0增强能力 | 测试类型覆盖 | Python脚本 |
|------|---------|---------|-------------|-------------|-----------|
| **职方司（TDD执行司）** | `tdd_execution_si` | 测试先行开发、红绿蓝循环、测试用例编写(Python pytest) | 边界条件自主推断、属性基测试(PBT)、Mock/Stub自动管理 | 单元测试 | `tdd_execution_si.py` |
| **驾部司（测试框架司）** | `test_framework_si` | 测试框架搭建(pytest/jest/playwright)、Mock/Stub管理、测试金字塔实现 | 框架选型智能推荐、并行测试支持、多框架适配 | 测试基础设施 | `test_framework_si.py` |
| **库部司（覆盖分析司）** | `coverage_analysis_si` | 代码覆盖率分析(行/分支/条件)、覆盖缺口定位、增量覆盖率追踪 | 覆盖缺口自动定位与补全建议、覆盖率趋势分析、多维度报告(MD) | 覆盖率统计 | `coverage_analysis_si.py` |
| **屯田司（回归测试司）** | `regression_testing_si` | 回归测试套件管理、冒烟测试(Smoke)、全量回归、E2E测试编排 | 影响范围分析、精准回归、测试优先级排序、Playwright E2E | 回归/冒烟/E2E | `regression_testing_si.py` |

##### 工部（Gongbu）- 代码生成与设计（4司）

| 司名 | 英文标识 | 核心职责 | v6.0增强能力 | UI/UX集成 | Python脚本 |
|------|---------|---------|-------------|----------|-----------|
| **屯田司（代码生成司）** | `code_generation_si` | 基于规范的代码生成(Python/TS/Java等)、脚手架搭建、样板代码、设计模式应用 | 上下文感知智能补全、多语言代码生成、设计模式自动推荐 | - | `code_generation_si.py` |
| **虞部司（UI/UX设计司）** | `uiux_design_si` | 界面原型、交互设计、用户体验优化、响应式布局、无障碍性(WCAG) | 设计模式自动匹配、响应式布局生成、WCAG 2.1 AA检查 | ✅ ui-ux-pro-max | `uiux_design_si.py` |
| **水部司（数据库设计司）** | `database_design_si` | 数据模型设计、ER图生成、索引优化、迁移脚本(Alembic)、查询优化 | Schema演化自动推导、慢SQL检测、数据迁移规划 | - | `database_design_si.py` |
| **工部司（API设计司）** | `api_design_si` | RESTful API设计、接口契约(OpenAPI 3.x)、版本管理、GraphQL支持 | API一致性自检、版本兼容性管理、Mock Server生成 | - | `api_design_si.py` |

##### 刑部（Xingbu）- 维护与演化（4司）

| 司名 | 英文标识 | 核心职责 | v6.0增强能力 | 自主能力 | Python脚本 |
|------|---------|---------|-------------|---------|-----------|
| **都官司（Bug修复司）** | `bug_fixing_si` | 缺陷定位、根因分析(RCA)、修复方案制定与实施、补丁生成 | 智能根因推断(5Whys/A Fishbone)、自动补丁生成、修复验证 | AOF感知+决策+执行 | `bug_fixing_si.py` |
| **比部司（重构司）** | `refactoring_si` | 代码重构、技术债务清理、架构优化、坏味道检测与消除 | 重构时机自主判断( smells > threshold )、重构方案推荐、安全重构(测试保护) | 自主评估+执行 | `refactoring_si.py` |
| **司门司（自演化司）** | `self_evolution_si` | 自我评估、模式学习、能力进化、最佳实践内化 | AOF驱动的持续自演化、模式识别、经验沉淀、策略调优 | 完整AOF四层 | `self_evolution_si.py` |
| **夏官司（版本控制司）** | `version_control_si` | Git工作流、分支策略(GitFlow)、发布管理、变更日志(Changelog)、SemVer | 变更影响智能评估、自动化Changelog生成、SemVer管理、Tag策略 | 自动化管理 | `version_control_si.py` |

### 2.2 全生命周期流程详解

本技能覆盖软件开发的**完整生命周期**，每个阶段都有对应的司/局负责：

```
┌─────────────────────────────────────────────────────────────┐
│                  全生命周期流程图                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────┐                                               │
│  │  Phase 0  │  项目启动与环境准备                             │
│  │  环境检测  │  户部·度支司: PS7+Python环境检测               │
│  │  项目初始化│  吏部·选司: 项目骨架创建                       │
│  └────┬─────┘                                               │
│       ▼                                                     │
│  ┌──────────┐   ┌──────────┐                                │
│  │  Phase 1  │   │  Phase 2  │                                │
│  │ 需求与业务 │──▶│ 架构与设计 │                                │
│  │ 分析      │   │ 模块化设计 │                                │
│  │           │   │ UI/UX设计 │                                │
│  │中书省:     │   │           │                                │
│  │·需求分析局 │   │中书省:     │                                │
│  │·方案审议局 │   │·架构设计局 │  ← 集成ui-ux-pro-max            │
│  │           │   │·规范制定局 │    (工部·虞部司)                │
│  │产出:      │   │           │                                │
│  │·PRD MD    │   │产出:      │                                │
│  │·用户故事  │   │·架构图MD  │                                │
│  │·验收标准  │   │·ADR记录  │                                │
│  │·业务流程图│   │·API设计  │                                │
│  └────┬─────┘   │·DB设计   │                                │
│       ▼         │·UI规范   │                                │
│  ┌──────────┐   └────┬─────┘                                │
│  │  Phase 3  │        │                                      │
│  │ 开发原则  │        ▼                                      │
│  │ 与规范    │   ┌──────────┐                                │
│  │ 制定      │   │  Phase 4  │                                │
│  │           │   │ SDD+TDD   │                                │
│  │中书省:     │   │ 双驱开发   │                                │
│  │·规范制定局 │   │           │                                │
│  │           │   │兵部:      │                                │
│  │产出:      │   │·TDD执行司 │                                │
│  │·编码规范MD│   │·测试框架司 │  ← 红绿蓝循环                    │
│  │·Git规范  │   │·覆盖分析司 │    (Python pytest)              │
│  │·分支策略  │   │           │                                │
│  └────┬─────┘   │工部:      │                                │
│       ▼         │·代码生成司 │                                │
│  ┌──────────┐   │·DB设计司  │                                │
│  │  Phase 5  │   │·API设计司 │                                │
│  │ 代码开发  │   │           │                                │
│  │ 与实现    │   │产出:      │                                │
│  │           │   │·源代码    │                                │
│  │尚书省:     │   │·单元测试  │                                │
│  │·工部各司  │   │·集成测试  │                                │
│  │·兵部各司  │   │·覆盖率报告│                                │
│  └────┬─────┘   └────┬─────┘                                │
│       ▼              │                                       │
│  ┌──────────┐        ▼                                       │
│  │  Phase 6  │   ┌──────────┐                                │
│  │ 代码审查  │   │  Phase 7  │                                │
│  │ 与质量保障 │   │ 各类测试   │                                │
│  │           │   │           │                                │
│  │门下省:     │   │兵部+门下省:│                               │
│  │·代码审查局 │   │·TDD执行司 │  · 单元测试(pytest)            │
│  │·测试验证局 │   │·覆盖分析司 │  · 集成测试                    │
│  │·质量监控局 │   │·回归测试司 │  · E2E测试(Playwright)         │
│  │·合规审计局 │   │           │  · 性能测试(Locust)            │
│  │           │   │           │  · 安全测试(Bandit/Trivy)      │
│  │产出:      │   │           │  · 变异测试(Mutpy)             │
│  │·审查报告MD│   │产出:      │                                │
│  │·质量评分  │   │·测试报告MD │                               │
│  │·缺陷清单  │   │·覆盖率MD  │                                │
│  │·安全报告  │   │·性能报告MD │                               │
│  └────┬─────┘   └────┬─────┘                                │
│       ▼              │                                       │
│  ┌──────────┐        ▼                                       │
│  │  Phase 8  │   ┌──────────┐                                │
│  │ 迭代与     │   │  Phase 9  │                                │
│  │ 完善/优化  │   │ 文档生成   │                                │
│  │ /修复/重构│   │ 与路径管理 │                                │
│  │           │   │           │                                │
│  │刑部:      │   │礼部:      │                                │
│  │·Bug修复司 │   │·文档司    │  所有输出统一:                   │
│  │·重构司    │   │·模板管理司 │  · Markdown格式                  │
│  │·自演化司  │   │·标准化司  │  · UTF-8 无 BOM编码             │
│  │·版本控制司│   │·知识库司  │  · docs/ 目录结构               │
│  │           │   │           │                                │
│  │产出:      │   │产出:      │                                │
│  │·Changelog│   │·API文档MD │                                │
│  │·修复报告  │   │·部署手册MD │                               │
│  │·重构报告  │   │·知识库MD  │                                │
│  └────┬─────┘   │·日志归档  │                                │
│       ▼         └────┬─────┘                                │
│  ┌──────────┐        │                                       │
│  │ Phase 10  │        ▼                                       │
│  │ 部署与发布 │   ┌──────────┐                                │
│  │           │   │ Phase 11  │                                │
│  │户部:      │   │ 持续监测   │                                │
│  │·基础设施司│   │ 与运维    │                                │
│  │·环境配置司│   │           │                                │
│  │           │   │门下省:    │                                │
│  │Harness集成:│   │·质量监控局 │                               │
│  │·CI流水线  │   │户部:      │                                │
│  │·CD部署   │   │·资源优化司 │                                │
│  │·SLO监控  │   │           │                                │
│  │·混沌实验  │   │产出:      │                                │
│  │           │   │·监控仪表盘│                               │
│  │产出:      │   │·告警规则  │                                │
│  │·部署YAML  │   │·运维日志  │                                │
│  │·Runbook  │   │·SRE报告   │                                │
│  └────┬─────┘   └────┬─────┘                                │
│       ▼              │                                       │
│  ┌───────────────────┴───────────────────┐                   │
│  │           🔁 持续迭代循环 🔁          │                   │
│  │   (回到Phase 5/6/8, 进入下一个Sprint)  │                   │
│  └───────────────────────────────────────┘                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2.3 五大技能协同生态系统

```
┌─────────────────────────────────────────────────────────────┐
│                  五大技能协同生态系统                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │       universal-devops (总指挥官/核心调度引擎)        │  │
│  │  角色：三省六部二十四司治理 + 全生命周期管理          │  │
│  └──────────────────────┬──────────────────────────────┘  │
│                          │ 协调调用                          │
│     ┌────────────────────┼────────────────────┐            │
│     ▼                    ▼                    ▼            │
│  ┌────────┐      ┌────────────┐     ┌──────────┐         │
│  │ sanliu │      │ agency-    │     │ ui-ux-   │         │
│  │ (基础框 │      │ agents     │     │ pro-max  │         │
│  │ 架继承)│      │ (144+Agent)│     │ (UI/UX)  │         │
│  └───┬────┘      └─────┬──────┘     └────┬─────┘         │
│      │                 │                   │               │
│      ▼                 ▼                   ▼               │
│  ┌────────────────────────────────────────────────┐       │
│  │        skill-creator (技能工厂/元技能)          │       │
│  │  创建/改进/评估/打包 所有SKILL.md              │       │
│  └────────────────────────────────────────────────┘       │
│                                                             │
│  协同关系详情:                                              │
│  ├─ sanliu → 提供 三省六部基础框架 + SDD/TDD引擎         │
│  ├─ agency-agents → 提供 144+ 专业Agent供Bridge调用       │
│  ├─ ui-ux-pro-max → 工部·虞部司的UI/UX设计能力来源       │
│  └─ skill-creator → 维护和迭代所有技能的SKILL.md文件      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## ⚙️ 核心引擎设计

### 3.1 SDD+TDD 融合引擎

#### 3.1.1 引擎架构

```
┌────────────────────────────────────────────────────────────┐
│               SDD+TDD 融合引擎 v6.0                          │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  输入: SDD Spec (YAML/JSON/MD)                            │
│       ↓                                                    │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐ │
│  │ SDD Spec     │───▶│ Parser       │───▶│ TDD Test     │ │
│  │ (规格输入)    │    │ (规格解析)   │    │ (测试生成)   │ │
│  └──────────────┘    └──────────────┘    └──────────────┘ │
│       ▲                                         │         │
│       │                    🔄 红绿蓝循环         │         │
│       │                                         ▼         │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐ │
│  │ Verifier     │◀───│ Executor     │◀───│ Implementer  │ │
│  │ (闭环验证)   │    │ (测试执行)   │    │ (代码实现)   │ │
│  └──────────────┘    └──────────────┘    └──────────────┘ │
│                                                            │
│  输出: 通过的测试 + 符合规范的代码 + 覆盖率报告(MD)       │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### 3.2 AOF四层自主决策框架

| 层次 | 名称 | 核心能力 | 对应四维度 |
|------|------|---------|-----------|
| **Layer 1** | 感知层 (Perception) | 环境上下文感知、项目状态扫描、需求意图理解、风险信号检测 | 提示词层 + 原生能力层 |
| **Layer 2** | 决策层 (Decision) | 任务分解、模式选择(自动/自主/协作)、风险评估、资源分配 | 提示词层 + 底层约束层 |
| **Layer 3** | 执行层 (Execution) | 子技能调度、三省六部协作、中间结果验证、异常回滚 | 原生能力层 + 底层约束层 |
| **Layer 4** | 反馈学习层 (Feedback) | 结果评估、效果分析、经验沉淀、参数调优 | 兜底机制层 |

### 3.3 七维质量监控体系

| 维度 | 监控指标 | 工具 | 阈值 | 责任部门 |
|------|---------|------|------|---------|
| **1.代码质量** | 圈复杂度、重复率、可维护性、技术债务 | SonarQube/Pylint/ESLint | complexity<10, dup<3% | 门下省·代码审查局 |
| **2.测试质量** | 行/分支/函数覆盖率、通过率、Flaky测试 | pytest/Coverage/Istanbul | line>80%, branch>70% | 门下省·测试验证局 |
| **3.文档质量** | 完整性、准确性、时效性、可访问性 | Sphinx/MkDocs/docstr_coverage | api>95%, docstring>90% | 礼部·文档司 |
| **4.性能质量** | P99延迟、吞吐量、CPU/内存利用率 | Locust/JMeter/Prometheus | p99<200ms, cpu<80% | 门下省·质量监控局 |
| **5.安全质量** | Critical/High漏洞数、依赖风险、密钥泄露 | Snyk/Trivy/Bandit | critical=0, high<5 | 门下省·合规审计局 |
| **6.合规质量** | 许可证问题、API契约、编码标准 | license-checker/openapi-validator | license_issues=0 | 门下省·合规审计局 |
| **7.可靠性质量** | SLO达成率、Error Budget、MTTR、可用性 | Harness SRE Engine | availability>99.9%, mttr<1h | 户部·基础设施司 |

---

## 🔧 技术栈与运行环境

### 4.1 运行环境要求

| 组件 | 版本要求 | 用途 |
|------|---------|------|
| **PowerShell** | ≥ 7.0 | 主要终端环境（Windows） |
| **Python** | ≥ 3.9 | 技能脚本运行时 |
| **操作系统** | Windows 10/11 / Linux / macOS | 跨平台支持 |

### 4.2 Python核心依赖

```yaml
required:
  - pyyaml >= 6.0        # 配置文件解析(YAML)
  - jinja2 >= 3.1        # 模板渲染(MD文档生成)
  - pydantic >= 2.0      # 数据校验(规格解析)
  - rich >= 13.0         # 终端美化输出
  - click >= 8.1         # CLI框架(脚本入口)
  - httpx >= 0.25        # HTTP客户端(Agent通信)

testing:
  - pytest >= 7.4        # 测试框架
  - coverage >= 7.0      # 覆盖率统计
  - pytest-asyncio       # 异步测试支持

quality:
  - pylint >= 3.0        # 静态分析
  - black >= 24.0        # 代码格式化
  - mypy >= 1.8          # 类型检查
  - ruff >= 0.4          # 快速Linter

security:
  - bandit >= 1.7        # 安全扫描
  - safety >= 2.0        # 依赖漏洞检查
```

### 4.3 PowerShell 7+ 环境检测脚本

```powershell
# skillscripts/utils/check_environment.ps1
# 编码: UTF-8 无 BOM
# 用途: 检测PowerShell 7 + Python环境是否就绪

param([string]$ProjectRoot = ".")

$ErrorActionPreference = "Stop"
$Passed = $true

Write-Host "=== Universal DevOps 环境检测 ===" -ForegroundColor Cyan
Write-Host ""

# 1. PowerShell版本检测
$psVersion = $PSVersionTable.PSVersion.ToString()
Write-Host "[1/4] PowerShell版本: $psVersion" -NoNewline
if ($PSVersionTable.PSVersion -ge [version]"7.0") {
    Write-Host " ✅ (>=7.0)" -ForegroundColor Green
} else {
    Write-Host " ❌ (需要>=7.0, 当前:$psVersion)" -ForegroundColor Red
    $Passed = $false
}

# 2. Python检测
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
Write-Host "[2/4] Python:" -NoNewline
if ($pythonCmd) {
    $pyVersion = & python --version 2>&1
    Write-Host " ✅ $pyVersion" -ForegroundColor Green
} else {
    Write-Host " ❌ 未找到Python" -ForegroundColor Red
    $Passed = $false
}

# 3. 必需pip包检测
Write-Host "[3/4] Python依赖包:" -ForegroundColor Yellow
$requiredPackages = @("pyyaml", "jinja2", "pydantic", "rich", "click", "httpx")
foreach ($pkg in $requiredPackages) {
    $installed = & python -m pip show $pkg 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ $pkg" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $pkg (未安装)" -ForegroundColor Red
        $Passed = $false
    }
}

# 4. 项目目录检测
Write-Host "[4/4] 项目结构:" -NoNewline
$skillDir = Join-Path $ProjectRoot ".trae" "skills" "universal-devops"
if (Test-Path $skillDir) {
    Write-Host " ✅ universal-devops技能目录存在" -ForegroundColor Green
} else {
    Write-Host " ⚠️ universal-devops技能目录不存在" -ForegroundColor Yellow
}

# 输出摘要
Write-Host ""
if ($Passed) {
    Write-Host "=== 环境检测全部通过 ===" -ForegroundColor Green
    exit 0
} else {
    Write-Host "=== 环境检测存在问题，请修复后重试 ===" -ForegroundColor Red
    exit 1
}
```

---

## 📁 输出物目录结构与路径规范

### 5.1 标准化输出目录

所有项目输出物统一存放在项目的 `docs/` 目录下，**统一使用 Markdown 格式 (.md)，编码为 UTF-8 无 BOM**：

```
project-root/
├── docs/                              # 主输出目录 (UTF-8 MD)
│   ├── requirements/                  # 需求文档
│   │   ├── prd_YYYYMMDD.md          # 产品需求文档
│   │   ├── user_stories/            # 用户故事集
│   │   └── acceptance_criteria/     # 验收标准
│   ├── architecture/                 # 架构设计
│   │   ├── system_architecture.md   # 系统架构总览
│   │   ├── technical_design/        # 技术设计方案
│   │   ├── diagrams/               # 架构图 (Mermaid)
│   │   └── decisions/              # ADR架构决策记录
│   ├── api/                          # API文档
│   │   ├── openapi_spec.yaml        # OpenAPI 3.x 规范
│   │   ├── endpoints/              # 接口详细文档
│   │   └── examples/              # 调用示例
│   ├── database/                    # 数据库设计
│   │   ├── er_diagrams/            # ER关系图
│   │   ├── schema_design/          # 表结构设计
│   │   ├── migrations/            # 迁移脚本
│   │   └── index_optimization/     # 索引优化
│   ├── testing/                      # 测试文档
│   │   ├── test_strategy.md        # 测试策略
│   │   ├── test_cases/            # 测试用例
│   │   ├── coverage_reports/      # 覆盖率报告
│   │   └── test_results/          # 测试结果
│   ├── reviews/                      # 审查报告
│   │   ├── code_reviews/          # Code Review
│   │   ├── architecture_reviews/  # 架构评审
│   │   ├── security_audits/       # 安全审计
│   │   └── compliance_reports/    # 合规检查
│   ├── deployment/                   # 部署文档
│   │   ├── ci_cd_pipelines/       # CI/CD配置
│   │   ├── environment_configs/   # 环境配置
│   │   ├── runbooks/             # 运维手册
│   │   └── rollback_plans/        # 回滚方案
│   ├── iteration/                    # 迭代记录
│   │   ├── sprint_logs/           # Sprint日志
│   │   ├── changelogs/           # 变更日志
│   │   ├── release_notes/        # 发布说明
│   │   └── retrospectives/       # 回顾总结
│   ├── monitoring/                   # 监控报告
│   │   ├── quality_dashboards/    # 质量仪表盘
│   │   ├── performance_metrics/  # 性能指标
│   │   ├── trend_analysis/       # 趋势分析
│   │   └── alerts/              # 告警记录
│   └── logs/                         # 日志归档
│       ├── evolution_logs/       # 演化日志
│       ├── execution_logs/       # 执行日志
│       ├── decision_logs/        # 决策日志
│       └── audit_trails/        # 审计追踪
│
├── skillscripts/                    # Python脚本 (UTF-8 无 BOM)
│   ├── main.py                    # 主入口CLI
│   ├── core/                      # 核心模块
│   ├── pipeline/                  # 流水线引擎 (SDD+TDD)
│   ├── evolution/                 # 演化系统 (四阶闭环)
│   ├── monitoring/               # 监控模块 (七维)
│   ├── harness_integration/      # Harness集成 (七大模块)
│   ├── agency_bridge/            # Agent桥接 (Router/Orchestrator)
│   ├── autonomous/               # 自主模式 (AOF四层)
│   ├── meta_skill/               # 元技能层 (自评/优/扩/打)
│   └── utils/                    # 工具函数 (PS7检测/路径管理等)
│
├── configs/                        # YAML配置文件
│   ├── default.yaml              # 默认配置
│   ├── autonomous_config.yaml    # 自主模式配置
│   ├── evolution_config.yaml     # 演化配置
│   ├── harness_config.yaml       # Harness配置
│   ├── agency_bridge_config.yaml # Agent桥接配置
│   ├── meta_skill_config.yaml    # 元技能配置
│   └── quality_gate_config.yaml  # 质量门禁配置
│
├── templates/                      # MD文档模板 (Jinja2渲染)
│   ├── requirements/             # 需求文档模板
│   ├── architecture/             # 架构文档模板
│   ├── api/                      # API文档模板
│   ├── database/                 # 数据库文档模板
│   ├── testing/                  # 测试文档模板
│   ├── reviews/                  # 审查报告模板
│   ├── deployment/              # 部署文档模板
│   ├── iteration/               # 迭代文档模板
│   ├── monitoring/              # 监控文档模板
│   └── logs/                    # 日志模板
│
└── subskills/                      # 子技能SKILL.md定义
    ├── zhongshusheng/           # 中书省 (4局)
    ├── menxiasheng/             # 门下省 (4局)
    └── shangshusheng/           # 尚书省 (6部24司)
        ├── libu/               # 吏部 (4司)
        ├── hubu/               # 户部 (4司)
        ├── libu2/              # 礼部 (4司)
        ├── bingbu/             # 兵部 (4司)
        ├── gongbu/             # 工部 (4司)
        └── xingbu/             # 刑部 (4司)
```

### 5.2 路径生成规范

所有路径由 **礼部·仪制司（标准化司）** 统一管理和生成：

```python
# 路径生成规则:
# 1. 使用PathConfigCenter统一管理
# 2. 相对路径基于项目根目录
# 3. 文件名格式: {功能}_{日期}.{ext}
# 4. 目录名: 英文小写下划线
# 5. 编码: UTF-8 无 BOM
# 6. 格式: Markdown (.md)

PATH_RULES = {
    "doc_format": "markdown",
    "encoding": "utf-8-no-bom",
    "naming": "lowercase_underscore",
    "date_format": "%Y%m%d",
    "root_dir": "docs/",
    "script_dir": "skillscripts/",
    "config_dir": "configs/",
    "template_dir": "templates/",
    "subskill_dir": "subskills/",
}
```

---

## 🎯 成功指标与验收标准

### 6.1 质量目标

| 指标类别 | 目标值 | 测量方法 |
|---------|--------|---------|
| 规范覆盖率(SDD) | ≥95% | SDD Parser统计分析 |
| 代码覆盖率(TDD) | 行≥80%, 分支≥70% | Coverage.py |
| 缺陷密度 | <5个/KLOC | Bug Tracking |
| 技术债务等级 | 低/中 | SonarQube Debt Metric |
| 文档完整性(API) | ≥95% | Doc Coverage Checker |
| 安全漏洞 | Critical=0, High<5 | Snyk/Trivy |
| SLO达成率 | ≥99.9% | Harness SRE |
| MTTR | <1小时 | Incident Tracking |
| 自主操作成功率 | ≥90%(低中风险) | AOF审计日志 |

### 6.2 功能验收清单（阻塞项）

#### 🔴 必须通过的架构项

- [ ] **三省六部二十四司架构完整性**
  - [ ] 中书省4局 × SKILL.md + Python脚本
  - [ ] 门下省4局 × SKILL.md + Python脚本
  - [ ] 尚书省6部24司 × SKILL.md + Python脚本
  - [ ] 省部司三级协调机制正常

- [ ] **四维度输出防线**
  - [ ] 提示词层: AOG指南完整覆盖32个子技能
  - [ ] 原生能力层: AI可自主完成代码/设计/测试/重构/修复
  - [ ] 底层约束层: 质量/安全/性能/合规门禁生效
  - [ ] 兜底机制层: 回滚/降级/审计/人工干预可用

- [ ] **三模运行架构**
  - [ ] 自动化模式: Python脚本直接执行
  - [ ] 自主模式: AI根据AOG指南自主操作
  - [ ] Agent协作模式: 多Agent并行/串行执行
  - [ ] 模式间平滑切换 + 降级机制

- [ ] **五大技能协同**
  - [ ] sanliu基础框架继承正常
  - [ ] agency-agents 144+ Agent注册和路由
  - [ ] ui-ux-pro-max集成到工部·虞部司
  - [ ] skill-creator可用于技能维护

- [ ] **Harness七大模块**
  - [ ] CI Pipeline Orchestrator
  - [ ] CD Deployment Manager (金丝雀/蓝绿/滚动)
  - [ ] SRE Reliability Engine (SLO/Error Budget)
  - [ ] Security STO Orchestrator (5阶段)
  - [ ] Feature Flag Manager
  - [ ] Chaos Experimenter
  - [ ] Cost Optimizer (FinOps)

- [ ] **平台与环境**
  - [ ] Trae IDE 正常运行
  - [ ] Claude Code 正常运行
  - [ ] PowerShell 7+ 所有脚本可执行
  - [ ] Python 3.9+ 所有依赖可用
  - [ ] 所有输出 UTF-8 无 BOM MD 格式

---

## 📝 附录

### A. 术语表

| 术语 | 全称 | 定义 |
|------|------|------|
| **SDD** | Specification-Driven Development | 规范驱动开发 |
| **TDD** | Test-Driven Development | 测试驱动开发 |
| **AOF** | Autonomous Operation Framework | 自主操作框架(四层) |
| **AOG** | Autonomous Operation Guide | 自主操作指南(SKILL.md) |
| **PRD** | Product Requirements Document | 产品需求文档 |
| **ADR** | Architecture Decision Record | 架构决策记录 |
| **SLO** | Service Level Objective | 服务级别目标 |
| **SLI** | Service Level Indicator | 服务级别指标 |
| **MTTR** | Mean Time To Recovery | 平均恢复时间 |
| **STO** | Security Test Orchestration | 安全测试编排 |
| **RCA** | Root Cause Analysis | 根因分析 |
| **RBAC** | Role-Based Access Control | 基于角色的访问控制 |
| **PBT** | Property-Based Testing | 属性基测试 |
| **E2E** | End-to-End | 端到端测试 |
| **WCAG** | Web Content Accessibility Guidelines | Web无障碍指南 |
| **FinOps** | Financial Operations | 财务运营/成本优化 |
| **IaC** | Infrastructure as Code | 基础设施即代码 |

### B. 版本路线图

| 版本 | 时间 | 核心特性 | 状态 |
|------|------|---------|------|
| v6.0.0 | 2026-04-06 | 规格冻结，架构设计完成 | 🔴 进行中 |
| v6.1.0 | 2026-04-13 | 核心引擎实现，基础流程打通 | ⏳ 计划 |
| v6.2.0 | 2026-04-20 | Bridge完善，Harness集成 | ⏳ 计划 |
| v6.3.0 | 2026-05-01 | 自主模式增强，AOF优化 | ⏳ 远期 |
| v7.0.0 | 2026-06-01 | 生产级稳定版 | ⏳ 远期 |

---

**文档结束**

> 💡 本规格说明书是 Universal DevOps v6.0 的核心设计文档。特别强化了**四维度输出防线**和**自主化≠自动化**的核心理念。所有后续开发和测试活动应严格遵循本文档。
