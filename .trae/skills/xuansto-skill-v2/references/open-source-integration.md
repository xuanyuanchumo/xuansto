# 开源项目集成映射文档

> 版本: 3.0.0 | 更新日期: 2026-05-06 | 编码: UTF-8 without BOM | 行尾: LF
> 需求文档: skill需求v3.0 §开源融合引擎

---

## 概述

本文档将86个开源项目按领域分类，映射到xuansto-skill v3.0的组件体系。每个映射条目包含项目核心能力、对本Skill的参考价值、已整合功能点、对应Agent/命令/工作流/脚本，以及整合优先级（P0必须/P1推荐/P2可选）。

### 优先级定义

| 优先级 | 含义 | 判定标准 |
|--------|------|----------|
| P0 | 必须 | 已部分整合或关键依赖项目 |
| P1 | 推荐 | 高参考价值但尚未整合 |
| P2 | 可选 | 其余项目，按需整合 |

---

## 目录

1. [行为准则 (2项)](#1-行为准则behavior-guidelines)
2. [SDD+TDD (10项)](#2-sddtdd)
3. [多Agent架构 (16项)](#3-多agent架构multi-agent-architecture)
4. [安全评估 (17项)](#4-安全评估security-assessment)
5. [渗透测试 (7项)](#5-渗透测试penetration-testing)
6. [桌面开发 (8项)](#6-桌面开发desktop-development)
7. [知识库 (2项)](#7-知识库knowledge-base)
8. [测试 (3项)](#8-测试testing)
9. [DevOps/版本控制 (3项)](#9-devops版本控制devopsvcs)
10. [协议 (2项)](#10-协议protocols)
11. [设计工具 (5项)](#11-设计工具design-tools)
12. [安全框架 (1项)](#12-安全框架security-frameworks)
13. [基准测试 (1项)](#13-基准测试benchmarking)
14. [统计总览](#统计总览)

---

## 1. 行为准则（Behavior Guidelines）

### 1.1 andrej-karpathy-skills

| 字段 | 内容 |
|------|------|
| 项目名称 | andrej-karpathy-skills |
| 核心能力 | AI辅助开发行为准则：编码前思考(Think Before Coding)、简洁优先(Simplicity First)、外科手术式修改(Surgical Changes)、目标驱动执行(Goal-Driven Execution) |
| 对本Skill的参考价值 | 四条准则已作为xuansto-skill不可妥协原则的核心组成部分，指导所有Agent的编码行为和决策逻辑 |
| 已整合功能点 | 四条准则完整嵌入SKILL.md不可妥协原则；增量实施约束(3次失败停止+反模式记录)与四条准则形成双向强化闭环；Karpathy准则检查清单嵌入Code Reviewer审查流程 |
| 对应Agent/命令/工作流/脚本 | Code Reviewer → /review; Refactoring Specialist → /simplify; 全部9阶段工作流; [karpathy-guidelines.md](karpathy-guidelines.md) |
| 整合优先级 | **P0** |

### 1.2 spatie/guidelines-skills

| 字段 | 内容 |
|------|------|
| 项目名称 | spatie/guidelines-skills |
| 核心能力 | PHP/Laravel生态开发准则与编码规范，强调团队协作一致性、代码风格统一和最佳实践 |
| 对本Skill的参考价值 | 团队协作一致性方法论可补充本Skill的协作模式设计，编码规范模板可参考用于多语言标准制定 |
| 已整合功能点 | 协作模式参考[collaboration-modes.md](collaboration-modes.md)；编码标准参考[coding-standards.md](coding-standards.md) |
| 对应Agent/命令/工作流/脚本 | Code Reviewer → /review; Documentation Engineer; [coding-standards.md](coding-standards.md) |
| 整合优先级 | P2 |

---

## 2. SDD+TDD

### 2.1 MoAI-ADK

| 字段 | 内容 |
|------|------|
| 项目名称 | MoAI-ADK |
| 核心能力 | 模型无关的AI开发工具包，提供SDD规格驱动开发的通用基础设施，支持多模型后端切换 |
| 对本Skill的参考价值 | 模型无关设计理念与本Skill的多IDE适配策略一致，SDD基础设施可参考用于规格持久化和规格漂移检测 |
| 已整合功能点 | 规格驱动开发流程嵌入/spec命令；规格漂移检测参考[spec-drift-handling.md](spec-drift-handling.md) |
| 对应Agent/命令/工作流/脚本 | Specification Keeper → /spec; spec-drift-detector.py; [sdd-tdd-full.md](../workflows/sdd-tdd-full.md) |
| 整合优先级 | P2 |

### 2.2 PactKit

| 字段 | 内容 |
|------|------|
| 项目名称 | PactKit |
| 核心能力 | 契约测试工具包，支持消费者驱动契约(Consumer-Driven Contract)测试，确保服务间API兼容性 |
| 对本Skill的参考价值 | 契约测试理念可应用于Agent间通信契约验证和IPC合约验证，确保多Agent协作的接口一致性 |
| 已整合功能点 | API契约验证参考api-contract-validator.py；IPC合约模板参考[ipc-contracts.md](ipc-contracts.md) |
| 对应Agent/命令/工作流/脚本 | Integration Tester → /test; api-contract-validator.py; ipc-contract-validator.js; [ipc-contracts.md](ipc-contracts.md) |
| 整合优先级 | P2 |

### 2.3 Don Cheli SDD

| 字段 | 内容 |
|------|------|
| 项目名称 | Don Cheli SDD |
| 核心能力 | SDD(规格驱动开发)方法论实践框架，强调规格先行、测试驱动、渐进式实现 |
| 对本Skill的参考价值 | SDD方法论核心参考，与本Skill的Spec > Test > Code原则直接对齐 |
| 已整合功能点 | SDD流程嵌入9阶段工作流Phase 0-3；规格编写通过/spec命令实现 |
| 对应Agent/命令/工作流/脚本 | Specification Keeper → /spec, /plan; [sdd-tdd-full.md](../workflows/sdd-tdd-full.md); [sdd-tdd-medium.md](../workflows/sdd-tdd-medium.md); [sdd-tdd-fast.md](../workflows/sdd-tdd-fast.md) |
| 整合优先级 | P2 |

### 2.4 sdd-tdd-workflow

| 字段 | 内容 |
|------|------|
| 项目名称 | sdd-tdd-workflow |
| 核心能力 | SDD与TDD融合工作流定义，提供规格驱动+测试驱动的双轨开发流程模板 |
| 对本Skill的参考价值 | SDD+TDD融合方法论的核心参考，直接指导本Skill的9阶段工作流设计 |
| 已整合功能点 | SDD+TDD融合流程完整嵌入9阶段工作流；三速模式(full/medium/fast)工作流实现 |
| 对应Agent/命令/工作流/脚本 | Orchestrator → /sprint, /implement; Test Architect → /test; [sdd-tdd-full.md](../workflows/sdd-tdd-full.md); [sdd-tdd-medium.md](../workflows/sdd-tdd-medium.md); [sdd-tdd-fast.md](../workflows/sdd-tdd-fast.md) |
| 整合优先级 | P2 |

### 2.5 TDDev

| 字段 | 内容 |
|------|------|
| 项目名称 | TDDev |
| 核心能力 | 测试驱动开发工具链，提供TDD自动化辅助、测试生成和覆盖率分析 |
| 对本Skill的参考价值 | TDD自动化工具链可增强本Skill的测试先行能力，测试生成技术可参考用于自动生成测试用例 |
| 已整合功能点 | TDD流程嵌入Phase 3(测试先行)；覆盖率检查通过coverage-check.py实现 |
| 对应Agent/命令/工作流/脚本 | Unit Tester → /test; Test Architect; coverage-check.py; [test-guidelines.md](test-guidelines.md) |
| 整合优先级 | P2 |

### 2.6 Spec Kit

| 字段 | 内容 |
|------|------|
| 项目名称 | Spec Kit |
| 核心能力 | 规格文档工具包，支持规格编写、验证、版本管理和漂移检测 |
| 对本Skill的参考价值 | 规格管理工具可增强本Skill的规格生命周期管理能力，漂移检测机制可参考用于spec-drift-detector |
| 已整合功能点 | 规格漂移检测参考[spec-drift-handling.md](spec-drift-handling.md)；spec-drift-detector.py实现 |
| 对应Agent/命令/工作流/脚本 | Specification Keeper → /spec; spec-drift-detector.py; [spec-drift-handling.md](spec-drift-handling.md) |
| 整合优先级 | P2 |

### 2.7 Tsumiki

| 字段 | 内容 |
|------|------|
| 项目名称 | Tsumiki |
| 核心能力 | 模块化构建系统，支持渐进式组装和依赖管理，强调小模块组合构建复杂系统 |
| 对本Skill的参考价值 | 模块化构建理念可参考用于Agent模块化设计和工作流编排，渐进式组装与增量实施约束互补 |
| 已整合功能点 | Agent模块化架构参考[agent-registry.md](agent-registry.md)；精简模式(文件<50自动启用) |
| 对应Agent/命令/工作流/脚本 | Task Coordinator → /plan; Subagent Dispatcher; [agent-registry.md](agent-registry.md) |
| 整合优先级 | P2 |

### 2.8 SWE-Flow

| 字段 | 内容 |
|------|------|
| 项目名称 | SWE-Flow |
| 核心能力 | 软件工程工作流自动化平台，提供从需求到部署的端到端流程编排和自动化 |
| 对本Skill的参考价值 | 端到端流程编排可参考用于9阶段工作流优化，自动化能力可增强CI/CD集成 |
| 已整合功能点 | 端到端流程嵌入9阶段工作流；CI/CD集成参考[ci-cd-integration.md](ci-cd-integration.md) |
| 对应Agent/命令/工作流/脚本 | CI/CD Specialist → /deploy; Build-Release Engineer → /build-desktop; [ci-cd-integration.md](ci-cd-integration.md) |
| 整合优先级 | P2 |

### 2.9 create-sddwcc

| 字段 | 内容 |
|------|------|
| 项目名称 | create-sddwcc |
| 核心能力 | SDD工作流脚手架生成器，快速创建SDD项目结构和配置文件，支持Claude Code集成 |
| 对本Skill的参考价值 | SDD项目脚手架生成能力已部分整合到/sprint命令的初始化流程中，Claude Code集成模式可参考 |
| 已整合功能点 | 项目初始化流程嵌入/sprint命令；SDD项目结构模板参考templates/目录 |
| 对应Agent/命令/工作流/脚本 | Product Manager → /sprint; System Architect → /plan; templates/; init-session.py |
| 整合优先级 | **P0** |

### 2.10 claude-code-collective

| 字段 | 内容 |
|------|------|
| 项目名称 | claude-code-collective |
| 核心能力 | Claude Code社区技能集合，提供多场景AI辅助开发技能模板和最佳实践 |
| 对本Skill的参考价值 | 社区技能模板和最佳实践已部分整合到本Skill的命令和工作流设计中，Agent编排模式可参考 |
| 已整合功能点 | 多场景技能模板参考commands/目录；Agent协作模式参考[agent-registry.md](agent-registry.md) |
| 对应Agent/命令/工作流/脚本 | Orchestrator → /agent-status; Subagent Dispatcher; [agent-registry.md](agent-registry.md); commands/ |
| 整合优先级 | **P0** |

---

## 3. 多Agent架构（Multi-Agent Architecture）

### 3.1 agency-agents

| 字段 | 内容 |
|------|------|
| 项目名称 | agency-agents |
| 核心能力 | Agency Agent桥接框架，支持144+外部Agent接入，提供Agent注册、发现、通信和编排能力 |
| 对本Skill的参考价值 | Agent桥接框架已作为本Skill的外部Agent集成基础，144+Agent接入能力扩展了本Skill的Agent生态 |
| 已整合功能点 | Agency Agent桥接参考SKILL.md描述；Agent注册参考[agent-registry.md](agent-registry.md)；Agent生命周期参考[agent-lifecycle.md](agent-lifecycle.md) |
| 对应Agent/命令/工作流/脚本 | Subagent Dispatcher → /agent-status; Task Coordinator; [agent-registry.md](agent-registry.md); [agent-lifecycle.md](agent-lifecycle.md) |
| 整合优先级 | **P0** |

### 3.2 agents-skill

| 字段 | 内容 |
|------|------|
| 项目名称 | agents-skill |
| 核心能力 | 通用Agent技能框架，提供Agent能力定义、技能注册和执行环境 |
| 对本Skill的参考价值 | Agent技能定义模式可参考用于本Skill的Agent角色定义和能力声明 |
| 已整合功能点 | Agent角色定义参考agents/目录下的57个Agent定义文件 |
| 对应Agent/命令/工作流/脚本 | Orchestrator → /agent-status; agents/目录全部Agent定义文件 |
| 整合优先级 | P2 |

### 3.3 @itz4blitz/agentful

| 字段 | 内容 |
|------|------|
| 项目名称 | @itz4blitz/agentful |
| 核心能力 | Agentful框架，提供声明式Agent定义和自动编排，强调Agent意图驱动的工作流 |
| 对本Skill的参考价值 | 声明式Agent定义模式可参考用于简化Agent配置，意图驱动工作流可增强/plan命令 |
| 已整合功能点 | Agent声明式定义参考agents/目录的frontmatter格式 |
| 对应Agent/命令/工作流/脚本 | Orchestrator → /plan; agent-frontmatter-validator.py; agents/ |
| 整合优先级 | P2 |

### 3.4 AgentMesh

| 字段 | 内容 |
|------|------|
| 项目名称 | AgentMesh |
| 核心能力 | Agent网格架构，支持去中心化Agent网络、动态拓扑和自适应路由 |
| 对本Skill的参考价值 | 去中心化Agent网络模式可参考用于大规模Agent协作场景，动态拓扑可增强Subagent Dispatcher |
| 已整合功能点 | Agent协作拓扑参考[collaboration-modes.md](collaboration-modes.md) |
| 对应Agent/命令/工作流/脚本 | Subagent Dispatcher; Task Coordinator; [collaboration-modes.md](collaboration-modes.md) |
| 整合优先级 | P2 |

### 3.5 Claude Code Skills

| 字段 | 内容 |
|------|------|
| 项目名称 | Claude Code Skills |
| 核心能力 | Claude Code技能系统，提供技能定义、加载和执行框架，支持自定义技能扩展 |
| 对本Skill的参考价值 | 技能系统框架是本Skill运行的基础平台，技能定义格式和加载机制直接影响本Skill的结构设计 |
| 已整合功能点 | SKILL.md技能定义；.skill-config.yaml配置；commands/命令系统 |
| 对应Agent/命令/工作流/脚本 | 全部23个命令; SKILL.md; .skill-config.yaml; configs/default.yaml |
| 整合优先级 | P2 |

### 3.6 Trae SOLO

| 字段 | 内容 |
|------|------|
| 项目名称 | Trae SOLO |
| 核心能力 | Trae IDE单Agent模式，提供轻量级AI辅助开发能力，强调快速响应和简单操作 |
| 对本Skill的参考价值 | 单Agent模式可参考用于本Skill的精简模式设计，快速响应机制可优化Agent调度效率 |
| 已整合功能点 | 精简模式(文件<50自动启用)参考SKILL.md |
| 对应Agent/命令/工作流/脚本 | Orchestrator; 精简模式Agent子集; [agent-registry.md](agent-registry.md) |
| 整合优先级 | P2 |

### 3.7 Microsoft Agent Framework

| 字段 | 内容 |
|------|------|
| 项目名称 | Microsoft Agent Framework |
| 核心能力 | 微软多Agent框架，提供企业级Agent编排、状态管理、人机协作和安全治理 |
| 对本Skill的参考价值 | 企业级Agent编排模式可参考用于增强本Skill的编排层，安全治理与Agent Governance Toolkit协同 |
| 已整合功能点 | Agent编排参考Orchestrator设计；人机协作参考[human-collaboration.md](human-collaboration.md) |
| 对应Agent/命令/工作流/脚本 | Orchestrator; Task Coordinator; [human-collaboration.md](human-collaboration.md); [collaboration-modes.md](collaboration-modes.md) |
| 整合优先级 | **P1** |

### 3.8 AgentForge

| 字段 | 内容 |
|------|------|
| 项目名称 | AgentForge |
| 核心能力 | Agent锻造框架，支持Agent能力组合、动态生成和运行时热加载 |
| 对本Skill的参考价值 | Agent动态生成能力可增强本Skill的Agent生态扩展性，运行时热加载可优化Agent调度 |
| 已整合功能点 | Agent能力组合参考[agent-registry.md](agent-registry.md)的层级设计 |
| 对应Agent/命令/工作流/脚本 | Subagent Dispatcher → /agent-status; [agent-registry.md](agent-registry.md) |
| 整合优先级 | **P1** |

### 3.9 SEMAG

| 字段 | 内容 |
|------|------|
| 项目名称 | SEMAG |
| 核心能力 | 语义驱动的多Agent框架，基于语义理解和意图推理进行Agent编排和任务分配 |
| 对本Skill的参考价值 | 语义驱动编排可参考用于增强Orchestrator的任务分解和Agent匹配能力 |
| 已整合功能点 | 语义驱动任务分解参考/plan和/sprint命令的任务分解逻辑 |
| 对应Agent/命令/工作流/脚本 | Orchestrator → /plan, /sprint; Brainstorming Facilitator → /brainstorm |
| 整合优先级 | P2 |

### 3.10 TALM

| 字段 | 内容 |
|------|------|
| 项目名称 | TALM |
| 核心能力 | 工具增强语言模型框架，将LLM与外部工具深度集成，支持工具调用推理和规划 |
| 对本Skill的参考价值 | 工具增强推理可参考用于增强Agent的工具使用能力和调用规划 |
| 已整合功能点 | 工具调用规划参考scripts/目录的工具集成脚本 |
| 对应Agent/命令/工作流/脚本 | 全部工程层Agent; scripts/目录工具脚本 |
| 整合优先级 | P2 |

### 3.11 AG2 (AutoGen)

| 字段 | 内容 |
|------|------|
| 项目名称 | AG2 (AutoGen) |
| 核心能力 | 微软多Agent对话框架，支持Agent间对话编排、代码执行和人工参与，内置Maris安全策略系统 |
| 对本Skill的参考价值 | 多Agent对话编排模式可参考用于增强Subagent Dispatcher，Maris安全策略已整合到安全框架 |
| 已整合功能点 | Maris安全策略参考[agentic-security-frameworks.md](agentic-security-frameworks.md)；Agent间通信参考ASI07防护 |
| 对应Agent/命令/工作流/脚本 | Security Auditor; Runtime Supervisor; [agentic-security-frameworks.md](agentic-security-frameworks.md); [owasp-agentic-top10-2026.md](owasp-agentic-top10-2026.md) |
| 整合优先级 | P2 |

### 3.12 BeeAI + Agent Stack

| 字段 | 内容 |
|------|------|
| 项目名称 | BeeAI + Agent Stack |
| 核心能力 | BeeAI Agent技术栈，提供可观测性、Agent模板和生产级部署支持 |
| 对本Skill的参考价值 | 可观测性方案可参考用于增强Monitor Specialist，Agent模板可丰富本Skill的Agent定义 |
| 已整合功能点 | 可观测性参考Decision Logger和Progress Tracker设计；Agent模板参考agents/目录 |
| 对应Agent/命令/工作流/脚本 | Monitor Specialist; Decision Logger; Progress Tracker; Quality Monitor |
| 整合优先级 | P2 |

### 3.13 Dapr Agents

| 字段 | 内容 |
|------|------|
| 项目名称 | Dapr Agents |
| 核心能力 | 基于Dapr的Agent运行时，提供分布式状态管理、服务调用、发布订阅和Actor模型 |
| 对本Skill的参考价值 | 分布式Agent运行时可参考用于增强本Skill的分布式部署能力，Actor模型可优化Agent生命周期管理 |
| 已整合功能点 | Agent生命周期参考[agent-lifecycle.md](agent-lifecycle.md)；状态管理参考Runtime Supervisor |
| 对应Agent/命令/工作流/脚本 | Runtime Supervisor; [agent-lifecycle.md](agent-lifecycle.md); [ci-cd-integration.md](ci-cd-integration.md) |
| 整合优先级 | **P1** |

### 3.14 CrewAI

| 字段 | 内容 |
|------|------|
| 项目名称 | CrewAI |
| 核心能力 | 多Agent协作框架，支持角色定义、任务委派和顺序/层级编排模式 |
| 对本Skill的参考价值 | 角色定义和任务委派模式可参考用于优化本Skill的Agent角色体系和任务分配逻辑 |
| 已整合功能点 | Agent角色体系参考[agent-registry.md](agent-registry.md)的13层57Agent设计 |
| 对应Agent/命令/工作流/脚本 | Task Coordinator; Subagent Dispatcher; [agent-registry.md](agent-registry.md) |
| 整合优先级 | P2 |

### 3.15 AgentScope 1.0

| 字段 | 内容 |
|------|------|
| 项目名称 | AgentScope 1.0 |
| 核心能力 | 阿里达摩院多Agent平台，提供分布式Agent编排、消息管道和内置工具集 |
| 对本Skill的参考价值 | 分布式Agent编排和消息管道可参考用于优化本Skill的Agent间通信机制 |
| 已整合功能点 | Agent间通信参考ASI07防护和[collaboration-modes.md](collaboration-modes.md) |
| 对应Agent/命令/工作流/脚本 | Subagent Dispatcher; [collaboration-modes.md](collaboration-modes.md); [owasp-agentic-top10-2026.md](owasp-agentic-top10-2026.md) |
| 整合优先级 | P2 |

### 3.16 LightAgent

| 字段 | 内容 |
|------|------|
| 项目名称 | LightAgent |
| 核心能力 | 轻量级Agent框架，强调低延迟、高吞吐的Agent执行，适合边缘和实时场景 |
| 对本Skill的参考价值 | 轻量级执行模式可参考用于优化本Skill精简模式的Agent调度效率 |
| 已整合功能点 | 精简模式参考SKILL.md(文件<50自动启用) |
| 对应Agent/命令/工作流/脚本 | Orchestrator; 精简模式Agent子集 |
| 整合优先级 | P2 |

### 3.17 Animus

| 字段 | 内容 |
|------|------|
| 项目名称 | Animus |
| 核心能力 | Agent意图管理系统，支持Agent目标追踪、意图对齐和偏离检测 |
| 对本Skill的参考价值 | 意图对齐和偏离检测可直接应用于ASI01(目标劫持)防护，增强Runtime Supervisor的目标一致性监控 |
| 已整合功能点 | 目标偏离监控参考ASI01防护；Runtime Supervisor目标一致性检测 |
| 对应Agent/命令/工作流/脚本 | Runtime Supervisor; Security Auditor; [owasp-agentic-top10-2026.md](owasp-agentic-top10-2026.md) |
| 整合优先级 | P2 |

### 3.18 ChatDev/MetaGPT

| 字段 | 内容 |
|------|------|
| 项目名称 | ChatDev/MetaGPT |
| 核心能力 | 多Agent软件开发框架，模拟软件公司组织结构，Agent扮演不同角色协作完成开发任务 |
| 对本Skill的参考价值 | 组织结构模拟模式可参考用于优化本Skill的13层Agent体系设计，角色协作模式可增强任务分配 |
| 已整合功能点 | 13层57Agent体系参考[agent-registry.md](agent-registry.md)；角色协作参考[collaboration-modes.md](collaboration-modes.md) |
| 对应Agent/命令/工作流/脚本 | 全部57个Agent; [agent-registry.md](agent-registry.md); [collaboration-modes.md](collaboration-modes.md) |
| 整合优先级 | P2 |

### 3.19 Sema Code

| 字段 | 内容 |
|------|------|
| 项目名称 | Sema Code |
| 核心能力 | 语义代码分析框架，提供代码语义理解、依赖分析和变更影响评估 |
| 对本Skill的参考价值 | 语义代码分析可增强Code Reviewer的审查深度，变更影响评估可优化Surgical Changes准则的执行 |
| 已整合功能点 | 代码审查参考Code Reviewer多视角审查；变更影响评估参考History Analyzer |
| 对应Agent/命令/工作流/脚本 | Code Reviewer → /review; History Analyzer; Refactoring Specialist → /simplify |
| 整合优先级 | P2 |

### 3.20 Open SWE

| 字段 | 内容 |
|------|------|
| 项目名称 | Open SWE |
| 核心能力 | 开源软件工程Agent平台，提供自动化代码生成、测试和部署能力 |
| 对本Skill的参考价值 | 自动化软件工程能力可参考用于增强本Skill的端到端自动化流程 |
| 已整合功能点 | 端到端自动化参考9阶段工作流；代码生成参考/implement命令 |
| 对应Agent/命令/工作流/脚本 | Fullstack Engineer → /implement; [sdd-tdd-full.md](../workflows/sdd-tdd-full.md) |
| 整合优先级 | P2 |

### 3.21 DevSwarm

| 字段 | 内容 |
|------|------|
| 项目名称 | DevSwarm |
| 核心能力 | 开发者群体智能框架，支持多Agent群体协作、涌现行为和自组织开发 |
| 对本Skill的参考价值 | 群体智能模式可参考用于增强本Skill的多Agent协作涌现能力 |
| 已整合功能点 | 多Agent协作参考[collaboration-modes.md](collaboration-modes.md)和Subagent Dispatcher |
| 对应Agent/命令/工作流/脚本 | Subagent Dispatcher; Task Coordinator; [collaboration-modes.md](collaboration-modes.md) |
| 整合优先级 | P2 |

### 3.22 OpenSage

| 字段 | 内容 |
|------|------|
| 项目名称 | OpenSage |
| 核心能力 | 开源智能Agent框架，提供Agent推理、规划和决策能力增强 |
| 对本Skill的参考价值 | Agent推理增强可参考用于优化Orchestrator的决策逻辑和任务分解策略 |
| 已整合功能点 | Agent推理参考Orchestrator决策逻辑和三级仲裁机制 |
| 对应Agent/命令/工作流/脚本 | Orchestrator; [collaboration-modes.md](collaboration-modes.md) |
| 整合优先级 | P2 |

### 3.23 Orla

| 字段 | 内容 |
|------|------|
| 项目名称 | Orla |
| 核心能力 | Agent编排语言，提供声明式Agent工作流定义和执行引擎 |
| 对本Skill的参考价值 | 声明式工作流定义可参考用于优化workflows/目录的YAML工作流定义 |
| 已整合功能点 | 工作流定义参考workflows/_yaml/目录的YAML工作流 |
| 对应Agent/命令/工作流/脚本 | Orchestrator; workflows/_yaml/目录; [workflow-checkpoints.md](workflow-checkpoints.md) |
| 整合优先级 | P2 |

### 3.24 OpenAI Agents SDK

| 字段 | 内容 |
|------|------|
| 项目名称 | OpenAI Agents SDK |
| 核心能力 | OpenAI官方Agent SDK，提供Agent定义、工具调用、交接(handoff)和安全防护 |
| 对本Skill的参考价值 | 官方SDK的Agent定义和交接模式可参考用于标准化Agent间协作接口，安全防护可补充本Skill安全体系 |
| 已整合功能点 | Agent交接参考Subagent Dispatcher的任务分发逻辑；安全防护参考[security-guidelines.md](security-guidelines.md) |
| 对应Agent/命令/工作流/脚本 | Subagent Dispatcher; Security Auditor; [security-guidelines.md](security-guidelines.md) |
| 整合优先级 | P2 |

### 3.25 LangGraph

| 字段 | 内容 |
|------|------|
| 项目名称 | LangGraph |
| 核心能力 | 基于图的有状态多Agent编排框架，支持循环工作流、条件分支和状态持久化 |
| 对本Skill的参考价值 | 图式工作流编排可参考用于增强本Skill的工作流灵活性，状态持久化可优化会话恢复机制 |
| 已整合功能点 | 工作流编排参考9阶段工作流设计；状态持久化参考.agent_cache/和init-session.py |
| 对应Agent/命令/工作流/脚本 | Orchestrator → /loop; init-session.py; session-catchup.py; plan-sync.py; .agent_cache/ |
| 整合优先级 | **P1** |

---

## 4. 安全评估（Security Assessment）

### 4.1 SafeAgents

| 字段 | 内容 |
|------|------|
| 项目名称 | SafeAgents |
| 核心能力 | Agent安全评估框架，提供Agent行为安全测试、对齐评估和风险量化 |
| 对本Skill的参考价值 | Agent行为安全测试方法论可增强Security Auditor的评估能力，风险量化可补充安全评分卡 |
| 已整合功能点 | 安全评估参考[security-frontier-frameworks.md](security-frontier-frameworks.md)；风险量化参考OWASP ASI01-ASI10 |
| 对应Agent/命令/工作流/脚本 | Security Auditor → /audit; [security-frontier-frameworks.md](security-frontier-frameworks.md); agentic-security-scanner.py |
| 整合优先级 | **P1** |

### 4.2 FCV-Attack研究

| 字段 | 内容 |
|------|------|
| 项目名称 | FCV-Attack研究 |
| 核心能力 | 针对AI Agent的快速对抗攻击研究，探索Agent在对抗环境下的脆弱性 |
| 对本Skill的参考价值 | 对抗攻击研究可增强AI Penetration Tester的攻击模拟能力，补充渗透测试用例库 |
| 已整合功能点 | 对抗攻击模拟参考[ai-pentest-frameworks.md](ai-pentest-frameworks.md) |
| 对应Agent/命令/工作流/脚本 | AI Penetration Tester → /audit; [ai-pentest-frameworks.md](ai-pentest-frameworks.md); ai-pentest-runner.py |
| 整合优先级 | P2 |

### 4.3 IMBIA/Adv-IMBIA

| 字段 | 内容 |
|------|------|
| 项目名称 | IMBIA/Adv-IMBIA |
| 核心能力 | 多模态Agent对抗性评估框架，针对多模态输入(文本+图像+音频)的对抗攻击和防御 |
| 对本Skill的参考价值 | 多模态对抗评估可参考用于增强本Skill在多模态场景下的安全评估能力 |
| 已整合功能点 | 安全评估参考[security-frontier-frameworks.md](security-frontier-frameworks.md) |
| 对应Agent/命令/工作流/脚本 | Security Auditor → /audit; [security-frontier-frameworks.md](security-frontier-frameworks.md) |
| 整合优先级 | P2 |

### 4.4 Multi-Agent Code Injection分析

| 字段 | 内容 |
|------|------|
| 项目名称 | Multi-Agent Code Injection分析 |
| 核心能力 | 多Agent系统中的代码注入攻击分析，研究Agent间通信中的代码注入传播和防御 |
| 对本Skill的参考价值 | 代码注入传播分析直接对应ASI05(意外代码执行)防护，可增强Agent间通信的代码注入检测 |
| 已整合功能点 | 代码注入防护参考ASI05防护和[owasp-agentic-top10-2026.md](owasp-agentic-top10-2026.md) |
| 对应Agent/命令/工作流/脚本 | Security Auditor; AI Penetration Tester → /audit; [owasp-agentic-top10-2026.md](owasp-agentic-top10-2026.md) |
| 整合优先级 | P2 |

### 4.5 OWASP Top 10 for Agentic Applications 2026

| 字段 | 内容 |
|------|------|
| 项目名称 | OWASP Top 10 for Agentic Applications 2026 |
| 核心能力 | Agentic AI系统十大安全风险清单(ASI01-ASI10)，涵盖目标劫持、工具滥用、权限滥用、供应链漏洞、代码执行、记忆污染、通信攻击、级联故障、过度自主、可观测性缺失 |
| 对本Skill的参考价值 | ASI01-ASI10已完整整合为本Skill安全体系的核心框架，驱动全部安全Agent的职责定义和质量门禁 |
| 已整合功能点 | ASI01-ASI10完整嵌入AGENTIC-SECURITY质量门禁；全部安全Agent职责对齐OWASP风险；AI-PENTEST门禁对齐渗透测试方法 |
| 对应Agent/命令/工作流/脚本 | Security Auditor → /audit; AI Penetration Tester; Compliance Officer; Runtime Supervisor; agentic-security-scanner.py; ai-pentest-runner.py; [owasp-agentic-top10-2026.md](owasp-agentic-top10-2026.md); [security-guidelines.md](security-guidelines.md) |
| 整合优先级 | **P0** |

### 4.6 OWASP LLM Top 10 2025

| 字段 | 内容 |
|------|------|
| 项目名称 | OWASP LLM Top 10 2025 |
| 核心能力 | 大语言模型应用十大安全风险，涵盖提示注入、不安全输出处理、训练数据投毒等 |
| 对本Skill的参考价值 | LLM安全风险是Agentic安全的基础层，部分风险已映射到ASI编号体系(如提示注入→ASI01) |
| 已整合功能点 | LLM风险映射参考[owasp-agentic-top10-2026.md](owasp-agentic-top10-2026.md)的AG→ASI映射表 |
| 对应Agent/命令/工作流/脚本 | Security Auditor → /audit; [owasp-agentic-top10-2026.md](owasp-agentic-top10-2026.md); [owasp-top10-2026.md](owasp-top10-2026.md) |
| 整合优先级 | P2 |

### 4.7 OWASP MCP Top 10

| 字段 | 内容 |
|------|------|
| 项目名称 | OWASP MCP Top 10 |
| 核心能力 | MCP(Model Context Protocol)协议十大安全风险，涵盖MCP服务器认证、工具沙箱、数据隔离等 |
| 对本Skill的参考价值 | MCP安全风险直接关联本Skill的MCP工具集成安全，可增强MCP服务器安全评估 |
| 已整合功能点 | MCP安全参考[mcp-protocol.md](mcp-protocol.md)和ASI04(供应链漏洞)MCP服务器安全评估 |
| 对应Agent/命令/工作流/脚本 | Security Auditor → /audit; [mcp-protocol.md](mcp-protocol.md); dependency-scan.py |
| 整合优先级 | P2 |

### 4.8 TrinityGuard

| 字段 | 内容 |
|------|------|
| 项目名称 | TrinityGuard |
| 核心能力 | 上海AI实验室开源的MAS安全评估与监控框架，三层20种风险分类体系(Prevention-Guard/Detection-Guard/Response-Guard)，OWASP标准对齐，评估层+运行时监控双层防护 |
| 对本Skill的参考价值 | 三层风险分类体系可增强Security Auditor的审计检查清单，运行时监控模式可优化Runtime Supervisor |
| 已整合功能点 | 安全评估参考[security-frontier-frameworks.md](security-frontier-frameworks.md)；风险分类对齐OWASP ASI01-ASI10 |
| 对应Agent/命令/工作流/脚本 | Security Auditor → /audit; Runtime Supervisor; [security-frontier-frameworks.md](security-frontier-frameworks.md); agentic-security-scanner.py |
| 整合优先级 | **P1** |

### 4.9 VulnSage

| 字段 | 内容 |
|------|------|
| 项目名称 | VulnSage |
| 核心能力 | 多Agent自动化漏洞利用生成框架，漏洞利用生成较SOTA提升53%，多Agent协作生成+自动化验证 |
| 对本Skill的参考价值 | 多Agent漏洞利用生成模式可增强AI Penetration Tester的漏洞验证能力，量化方法可优化安全测试报告 |
| 已整合功能点 | 漏洞利用验证参考[ai-pentest-frameworks.md](ai-pentest-frameworks.md) |
| 对应Agent/命令/工作流/脚本 | AI Penetration Tester → /audit; Security Tester; [ai-pentest-frameworks.md](ai-pentest-frameworks.md); ai-pentest-runner.py |
| 整合优先级 | **P1** |

### 4.10 JoySafeter

| 字段 | 内容 |
|------|------|
| 项目名称 | JoySafeter |
| 核心能力 | 京东开源AI驱动安全编排平台，200+安全工具MCP集成，DeepAgents Manager-Worker星型拓扑，AI驱动安全事件自动化响应 |
| 对本Skill的参考价值 | 200+安全工具MCP集成模式可扩展渗透测试工具链，Manager-Worker星型拓扑可优化安全任务编排 |
| 已整合功能点 | 安全编排参考[security-frontier-frameworks.md](security-frontier-frameworks.md)；MCP工具集成参考[mcp-protocol.md](mcp-protocol.md) |
| 对应Agent/命令/工作流/脚本 | AI Penetration Tester → /audit; [security-frontier-frameworks.md](security-frontier-frameworks.md); [mcp-protocol.md](mcp-protocol.md) |
| 整合优先级 | P2 |

### 4.11 Agent Governance Toolkit

| 字段 | 内容 |
|------|------|
| 项目名称 | Agent Governance Toolkit |
| 核心能力 | 微软开源AI代理运行时安全工具包，覆盖全部10项OWASP Agentic风险，声明式安全策略+运行时拦截+执行环隔离 |
| 对本Skill的参考价值 | 运行时策略拦截可增强Runtime Supervisor，执行环隔离可强化ASI05防护，策略合规报告可补充Compliance Officer |
| 已整合功能点 | 运行时策略参考[security-frontier-frameworks.md](security-frontier-frameworks.md)；执行环隔离参考ASI05防护 |
| 对应Agent/命令/工作流/脚本 | Runtime Supervisor; Compliance Officer → /audit; [security-frontier-frameworks.md](security-frontier-frameworks.md) |
| 整合优先级 | P2 |

### 4.12 OpenAgentSafety

| 字段 | 内容 |
|------|------|
| 项目名称 | OpenAgentSafety |
| 核心能力 | ICLR 2026多Agent安全评估基准框架，8类风险类别，350+多轮多用户任务，真实工具交互，自动化红队评估 |
| 对本Skill的参考价值 | 350+测试任务可作为渗透测试基础用例库，8类风险类别和评分体系可构建安全评估标准 |
| 已整合功能点 | 安全评估基准参考[security-frontier-frameworks.md](security-frontier-frameworks.md) |
| 对应Agent/命令/工作流/脚本 | AI Penetration Tester → /audit; Security Auditor; [security-frontier-frameworks.md](security-frontier-frameworks.md); ai-pentest-runner.py |
| 整合优先级 | P2 |

### 4.13 Argusee

| 字段 | 内容 |
|------|------|
| 项目名称 | Argusee |
| 核心能力 | DARKNAVY多Agent协作漏洞发现架构，已发现CVE-2025-37891高危漏洞，深度漏洞挖掘+实战验证导向 |
| 对本Skill的参考价值 | 多Agent协作漏洞发现架构可增强AI Penetration Tester的深度测试能力，实战验证方法可确保漏洞真实性 |
| 已整合功能点 | 漏洞发现参考[ai-pentest-frameworks.md](ai-pentest-frameworks.md) |
| 对应Agent/命令/工作流/脚本 | AI Penetration Tester → /audit; [ai-pentest-frameworks.md](ai-pentest-frameworks.md); ai-pentest-runner.py |
| 整合优先级 | P2 |

### 4.14 MAESTRO

| 字段 | 内容 |
|------|------|
| 项目名称 | MAESTRO |
| 核心能力 | CSA云安全联盟高度监管行业多Agent安全框架，L1-L4最小可行控制分层模型，威胁模型与攻击树定义，CSA STAR/CCM合规对齐 |
| 对本Skill的参考价值 | L1-L4分层控制模型可构建合规检查基线，威胁模型可指导安全架构设计，合规对齐可支持云安全认证 |
| 已整合功能点 | 合规框架参考[security-frontier-frameworks.md](security-frontier-frameworks.md)；安全控制分级参考ASI防护 |
| 对应Agent/命令/工作流/脚本 | Compliance Officer → /audit; System Architect → /plan; [security-frontier-frameworks.md](security-frontier-frameworks.md) |
| 整合优先级 | P2 |

### 4.15 Maris (AG2内置)

| 字段 | 内容 |
|------|------|
| 项目名称 | Maris (AG2内置) |
| 核心能力 | AG2内置细粒度策略引导安全防护系统，Policy-as-Code范式，Agent间通信策略控制，Agent-环境交互策略控制，运行时策略执行 |
| 对本Skill的参考价值 | Policy-as-Code模式可参考用于Agent间通信安全策略定义，操作审批流程可增强ASI09防护 |
| 已整合功能点 | 策略引导防护参考[agentic-security-frameworks.md](agentic-security-frameworks.md)；通信策略控制参考ASI07防护 |
| 对应Agent/命令/工作流/脚本 | Security Auditor; Runtime Supervisor; [agentic-security-frameworks.md](agentic-security-frameworks.md); [owasp-agentic-top10-2026.md](owasp-agentic-top10-2026.md) |
| 整合优先级 | P2 |

### 4.16 SAFEFLOW

| 字段 | 内容 |
|------|------|
| 项目名称 | SAFEFLOW |
| 核心能力 | 协议级安全框架，强制执行细粒度信息流控制(IFC)，事务执行+回滚机制+安全缓存 |
| 对本Skill的参考价值 | IFC标签体系可实施Agent间数据流合规性检查，事务回滚机制可为ASI08(级联故障)提供安全基础 |
| 已整合功能点 | 信息流控制参考[agentic-security-frameworks.md](agentic-security-frameworks.md)；故障回滚参考ASI08防护 |
| 对应Agent/命令/工作流/脚本 | Runtime Supervisor; Security Auditor; [agentic-security-frameworks.md](agentic-security-frameworks.md) |
| 整合优先级 | P2 |

### 4.17 SAGA

| 字段 | 内容 |
|------|------|
| 项目名称 | SAGA |
| 核心能力 | 可扩展Agentic系统治理安全架构，加密机制派生访问控制令牌，形式化安全保障，Agent注册与身份生命周期管理，可扩展审计追踪 |
| 对本Skill的参考价值 | 加密访问控制令牌可增强ASI03(身份权限滥用)防护，形式化保障可构建合规验证基础，审计追踪可增强ASI10 |
| 已整合功能点 | 治理架构参考[agentic-security-frameworks.md](agentic-security-frameworks.md)；访问控制令牌参考ASI03防护 |
| 对应Agent/命令/工作流/脚本 | Compliance Officer; Decision Logger; [agentic-security-frameworks.md](agentic-security-frameworks.md); [owasp-agentic-top10-2026.md](owasp-agentic-top10-2026.md) |
| 整合优先级 | P2 |

---

## 5. 渗透测试（Penetration Testing）

### 5.1 Strix

| 字段 | 内容 |
|------|------|
| 项目名称 | Strix |
| 核心能力 | AI驱动渗透测试框架，支持自动化侦察、漏洞扫描和攻击路径规划 |
| 对本Skill的参考价值 | 自动化侦察和攻击路径规划可增强AI Penetration Tester的测试能力 |
| 已整合功能点 | 渗透测试自动化参考[ai-pentest-frameworks.md](ai-pentest-frameworks.md)和ai-pentest-runner.py |
| 对应Agent/命令/工作流/脚本 | AI Penetration Tester → /audit; Penetration Tester; [ai-pentest-frameworks.md](ai-pentest-frameworks.md); ai-pentest-runner.py |
| 整合优先级 | P2 |

### 5.2 BugTrace-AI

| 字段 | 内容 |
|------|------|
| 项目名称 | BugTrace-AI |
| 核心能力 | AI驱动漏洞追踪平台，支持漏洞生命周期管理、根因分析和修复建议 |
| 对本Skill的参考价值 | 漏洞追踪和根因分析可增强Security Auditor的漏洞管理能力，修复建议可优化/fix命令 |
| 已整合功能点 | 漏洞追踪参考[ai-pentest-frameworks.md](ai-pentest-frameworks.md)；修复建议参考/fix命令 |
| 对应Agent/命令/工作流/脚本 | Security Auditor → /audit; Bug Scanner → /fix; [ai-pentest-frameworks.md](ai-pentest-frameworks.md) |
| 整合优先级 | P2 |

### 5.3 CAI

| 字段 | 内容 |
|------|------|
| 项目名称 | CAI |
| 核心能力 | 对抗性AI测试框架，支持AI模型对抗性评估、鲁棒性测试和红队自动化 |
| 对本Skill的参考价值 | 对抗性AI测试可增强AI Penetration Tester的AI模型安全评估能力 |
| 已整合功能点 | AI安全测试参考[ai-pentest-frameworks.md](ai-pentest-frameworks.md) |
| 对应Agent/命令/工作流/脚本 | AI Penetration Tester → /audit; [ai-pentest-frameworks.md](ai-pentest-frameworks.md); ai-pentest-runner.py |
| 整合优先级 | P2 |

### 5.4 Reaper

| 字段 | 内容 |
|------|------|
| 项目名称 | Reaper |
| 核心能力 | 自动化漏洞收割框架，支持大规模漏洞发现、分类和优先级排序 |
| 对本Skill的参考价值 | 大规模漏洞发现和优先级排序可增强安全测试的效率和覆盖面 |
| 已整合功能点 | 漏洞发现参考[ai-pentest-frameworks.md](ai-pentest-frameworks.md) |
| 对应Agent/命令/工作流/脚本 | AI Penetration Tester → /audit; Security Tester; [ai-pentest-frameworks.md](ai-pentest-frameworks.md) |
| 整合优先级 | P2 |

### 5.5 AutoPentester

| 字段 | 内容 |
|------|------|
| 项目名称 | AutoPentester |
| 核心能力 | LLM Agent驱动自动化渗透测试框架，子任务完成率较PentestGPT提升27%，漏洞覆盖率提升39.5%，多步骤推理与规划 |
| 对本Skill的参考价值 | LLM Agent驱动攻击链模式可优化渗透测试任务分解和执行，多步骤推理可增强攻击路径规划 |
| 已整合功能点 | 自动化渗透测试参考[ai-pentest-frameworks.md](ai-pentest-frameworks.md) |
| 对应Agent/命令/工作流/脚本 | AI Penetration Tester → /audit; [ai-pentest-frameworks.md](ai-pentest-frameworks.md); ai-pentest-runner.py; [ai-penetration-tester-details.md](ai-penetration-tester-details.md) |
| 整合优先级 | P2 |

### 5.6 xOffense

| 字段 | 内容 |
|------|------|
| 项目名称 | xOffense |
| 核心能力 | AI驱动多Agent渗透测试框架，微调中型开源LLM驱动推理和决策，多Agent协作攻击，推理与决策分离 |
| 对本Skill的参考价值 | 多Agent协作攻击模式可设计专业化渗透测试Agent团队，推理与决策分离架构可增强攻击推理准确性 |
| 已整合功能点 | 多Agent渗透测试参考[ai-pentest-frameworks.md](ai-pentest-frameworks.md) |
| 对应Agent/命令/工作流/脚本 | AI Penetration Tester → /audit; Penetration Tester; [ai-pentest-frameworks.md](ai-pentest-frameworks.md) |
| 整合优先级 | P2 |

### 5.7 AWE

| 字段 | 内容 |
|------|------|
| 项目名称 | AWE |
| 核心能力 | 自动化武器化利用框架，支持漏洞利用自动化生成和武器化 |
| 对本Skill的参考价值 | 自动化利用生成可增强漏洞验证能力，但需严格控制在授权范围内使用 |
| 已整合功能点 | 漏洞利用验证参考[ai-pentest-frameworks.md](ai-pentest-frameworks.md) |
| 对应Agent/命令/工作流/脚本 | AI Penetration Tester → /audit; [ai-pentest-frameworks.md](ai-pentest-frameworks.md) |
| 整合优先级 | P2 |

---

## 6. 桌面开发（Desktop Development）

### 6.1 Electron

| 字段 | 内容 |
|------|------|
| 项目名称 | Electron |
| 核心能力 | 跨平台桌面应用框架，基于Chromium+Node.js，支持Windows/macOS/Linux |
| 对本Skill的参考价值 | Electron是本Skill桌面开发的核心框架之一，安全最佳实践和IPC模式已整合到桌面开发指南 |
| 已整合功能点 | Electron安全参考[electron-security.md](electron-security.md)；桌面开发参考[desktop-dev-guidelines.md](desktop-dev-guidelines.md)；IPC参考[ipc-contracts.md](ipc-contracts.md) |
| 对应Agent/命令/工作流/脚本 | Desktop Developer → /build-desktop; IPC Specialist; Auto-Update Engineer; build-desktop.ps1; sign-desktop.ps1; verify-auto-update.ps1; ipc-contract-validator.js; [desktop-build-workflow.md](../workflows/desktop-build-workflow.md) |
| 整合优先级 | P2 |

### 6.2 Tauri

| 字段 | 内容 |
|------|------|
| 项目名称 | Tauri |
| 核心能力 | 轻量级跨平台桌面应用框架，基于Rust+WebView，强调安全性和小体积 |
| 对本Skill的参考价值 | Tauri是本Skill桌面开发的另一核心框架，Rust安全模式和权限系统已整合到Tauri开发指南 |
| 已整合功能点 | Tauri开发参考[tauri-dev-guidelines.md](tauri-dev-guidelines.md)；Rust标准参考[rust-standards.md](rust-standards.md) |
| 对应Agent/命令/工作流/脚本 | Desktop Developer → /build-desktop; Native Module Developer; [tauri-dev-guidelines.md](tauri-dev-guidelines.md); [cross-platform-workflow.md](../workflows/cross-platform-workflow.md) |
| 整合优先级 | P2 |

### 6.3 Flutter Desktop

| 字段 | 内容 |
|------|------|
| 项目名称 | Flutter Desktop |
| 核心能力 | Flutter桌面平台支持，基于Dart+Skia渲染，支持Windows/macOS/Linux原生UI |
| 对本Skill的参考价值 | Flutter Desktop是本Skill桌面开发的第三核心框架，跨平台UI模式已整合到Flutter开发指南 |
| 已整合功能点 | Flutter桌面参考[flutter-desktop-guidelines.md](flutter-desktop-guidelines.md)；Flutter标准参考[flutter-standards.md](flutter-standards.md) |
| 对应Agent/命令/工作流/脚本 | Desktop UI Adapter → /build-desktop; Desktop Developer; [flutter-desktop-guidelines.md](flutter-desktop-guidelines.md); [flutter-desktop-workflow.md](../workflows/flutter-desktop-workflow.md) |
| 整合优先级 | P2 |

### 6.4 electron-builder/tauri-bundler

| 字段 | 内容 |
|------|------|
| 项目名称 | electron-builder/tauri-bundler |
| 核心能力 | Electron/Tauri应用打包工具，支持多平台构建、自动更新和代码签名 |
| 对本Skill的参考价值 | 打包工具链已整合到/build-desktop和/release-desktop命令的构建流程中 |
| 已整合功能点 | 构建打包参考build-desktop.ps1；代码签名参考sign-desktop.ps1；自动更新参考verify-auto-update.ps1 |
| 对应Agent/命令/工作流/脚本 | Build-Release Engineer → /build-desktop, /release-desktop; build-desktop.ps1; sign-desktop.ps1; [desktop-build-workflow.md](../workflows/desktop-build-workflow.md) |
| 整合优先级 | P2 |

### 6.5 NSIS/WiX Toolset

| 字段 | 内容 |
|------|------|
| 项目名称 | NSIS/WiX Toolset |
| 核心能力 | Windows安装程序构建工具，NSIS脚本式安装器，WiX基于XML的MSI构建 |
| 对本Skill的参考价值 | Windows安装程序构建已整合到/release-desktop命令的发布流程中 |
| 已整合功能点 | 安装程序构建参考[desktop-dev-guidelines.md](desktop-dev-guidelines.md)和build-desktop.ps1 |
| 对应Agent/命令/工作流/脚本 | Build-Release Engineer → /release-desktop; build-desktop.ps1; [desktop-dev-guidelines.md](desktop-dev-guidelines.md) |
| 整合优先级 | P2 |

### 6.6 Sparkle/Squirrel

| 字段 | 内容 |
|------|------|
| 项目名称 | Sparkle/Squirrel |
| 核心能力 | macOS/Windows自动更新框架，Sparkle用于macOS应用更新，Squirrel用于Windows/Electron应用更新 |
| 对本Skill的参考价值 | 自动更新框架已整合到Auto-Update Engineer的职责和verify-auto-update.ps1脚本中 |
| 已整合功能点 | 自动更新参考Auto-Update Engineer定义和verify-auto-update.ps1 |
| 对应Agent/命令/工作流/脚本 | Auto-Update Engineer → /release-desktop; verify-auto-update.ps1; templates/auto-update-config-template.yaml |
| 整合优先级 | P2 |

### 6.7 electron-updater

| 字段 | 内容 |
|------|------|
| 项目名称 | electron-updater |
| 核心能力 | Electron应用自动更新模块，支持增量更新、代码签名验证和多渠道发布 |
| 对本Skill的参考价值 | Electron自动更新已整合到Auto-Update Engineer的职责和自动更新验证脚本中 |
| 已整合功能点 | 自动更新验证参考verify-auto-update.ps1和templates/auto-update-config-template.yaml |
| 对应Agent/命令/工作流/脚本 | Auto-Update Engineer → /release-desktop; verify-auto-update.ps1; templates/auto-update-config-template.yaml |
| 整合优先级 | P2 |

### 6.8 Spectron/Playwright for Electron

| 字段 | 内容 |
|------|------|
| 项目名称 | Spectron/Playwright for Electron |
| 核心能力 | Electron应用自动化测试框架，Spectron(已废弃)和Playwright(推荐)支持E2E测试 |
| 对本Skill的参考价值 | Playwright for Electron已整合到Desktop Tester和E2E Tester的测试流程中 |
| 已整合功能点 | E2E测试参考Desktop Tester和E2E Tester定义；Playwright集成参考[webapp-testing-workflow.md](../workflows/webapp-testing-workflow.md) |
| 对应Agent/命令/工作流/脚本 | Desktop Tester → /test; E2E Tester → /test; visual-regression.js; performance-benchmark.js (unified web+desktop); [webapp-testing-workflow.md](../workflows/webapp-testing-workflow.md) |
| 整合优先级 | P2 |

---

## 7. 知识库（Knowledge Base）

### 7.1 @hivehub/rulebook

| 字段 | 内容 |
|------|------|
| 项目名称 | @hivehub/rulebook |
| 核心能力 | 增量实施规范和规则手册，定义3次失败强制停止+反模式记录+从头重启机制，与Karpathy准则形成双向强化闭环 |
| 对本Skill的参考价值 | 增量实施约束已作为本Skill不可妥协原则的核心组成部分，3次失败停止机制与Karpathy准则互补 |
| 已整合功能点 | 增量实施约束嵌入SKILL.md不可妥协原则；3次失败停止机制嵌入loop-guard.py；反模式记录嵌入.knowledge/目录；与Karpathy准则关联参考[karpathy-guidelines.md](karpathy-guidelines.md) |
| 对应Agent/命令/工作流/脚本 | Orchestrator → /loop; loop-guard.py; .knowledge/目录; [karpathy-guidelines.md](karpathy-guidelines.md); [knowledge-base-architecture.md](knowledge-base-architecture.md) |
| 整合优先级 | **P0** |

### 7.2 CangjieSkills

| 字段 | 内容 |
|------|------|
| 项目名称 | CangjieSkills |
| 核心能力 | 仓颉技能框架，提供技能定义、加载和执行的标准规范，支持技能组合和依赖管理 |
| 对本Skill的参考价值 | 技能框架规范已部分整合到本Skill的SKILL.md定义和commands/命令系统中 |
| 已整合功能点 | 技能定义参考SKILL.md frontmatter格式；命令系统参考commands/目录 |
| 对应Agent/命令/工作流/脚本 | 全部23个命令; SKILL.md; commands/目录; .skill-config.yaml |
| 整合优先级 | **P0** |

---

## 8. 测试（Testing）

### 8.1 TestForge

| 字段 | 内容 |
|------|------|
| 项目名称 | TestForge |
| 核心能力 | 测试用例锻造框架，支持基于规格自动生成测试用例、测试数据工厂和测试覆盖率分析 |
| 对本Skill的参考价值 | 基于规格自动生成测试用例可增强本Skill的TDD流程，测试数据工厂可优化Data Seeder |
| 已整合功能点 | TDD流程参考Phase 3(测试先行)；测试覆盖率参考coverage-check.py |
| 对应Agent/命令/工作流/脚本 | Test Architect → /test; Unit Tester; Data Seeder; coverage-check.py; [test-guidelines.md](test-guidelines.md) |
| 整合优先级 | **P1** |

### 8.2 UnitTenX

| 字段 | 内容 |
|------|------|
| 项目名称 | UnitTenX |
| 核心能力 | 单元测试增强工具，支持测试用例10倍扩展、边界条件自动发现和变异测试 |
| 对本Skill的参考价值 | 测试用例扩展和边界条件发现可增强Unit Tester的测试覆盖深度 |
| 已整合功能点 | 单元测试参考Unit Tester定义和[test-guidelines.md](test-guidelines.md) |
| 对应Agent/命令/工作流/脚本 | Unit Tester → /test; Test Maintainer; [test-guidelines.md](test-guidelines.md); coverage-check.py |
| 整合优先级 | P2 |

### 8.3 MASTEST

| 字段 | 内容 |
|------|------|
| 项目名称 | MASTEST |
| 核心能力 | 多Agent系统测试框架，支持Agent间交互测试、通信协议测试和涌现行为验证 |
| 对本Skill的参考价值 | 多Agent交互测试可增强Integration Tester的Agent间通信测试能力 |
| 已整合功能点 | 集成测试参考Integration Tester定义和[collaboration-modes.md](collaboration-modes.md) |
| 对应Agent/命令/工作流/脚本 | Integration Tester → /test; Test Architect; [collaboration-modes.md](collaboration-modes.md); [test-guidelines.md](test-guidelines.md) |
| 整合优先级 | P2 |

---

## 9. DevOps/版本控制（DevOps/VCS）

### 9.1 AgentGit

| 字段 | 内容 |
|------|------|
| 项目名称 | AgentGit |
| 核心能力 | Agent驱动的Git操作框架，支持自动化提交、分支管理和冲突解决 |
| 对本Skill的参考价值 | Agent驱动Git操作可增强本Skill的版本控制自动化能力 |
| 已整合功能点 | Git工作流参考[git-workflow.md](git-workflow.md)；提交规范参考SKILL.md编码规范 |
| 对应Agent/命令/工作流/脚本 | CI/CD Specialist → /deploy; [git-workflow.md](git-workflow.md); [ci-cd-integration.md](ci-cd-integration.md) |
| 整合优先级 | P2 |

### 9.2 Worktrunk

| 字段 | 内容 |
|------|------|
| 项目名称 | Worktrunk |
| 核心能力 | 工作树管理工具，支持多分支并行开发、工作树隔离和上下文切换 |
| 对本Skill的参考价值 | 多分支并行开发可增强本Skill的多任务并行能力 |
| 已整合功能点 | 分支策略参考[git-workflow.md](git-workflow.md) |
| 对应Agent/命令/工作流/脚本 | CI/CD Specialist; [git-workflow.md](git-workflow.md) |
| 整合优先级 | P2 |

### 9.3 git-stint/worktrunk/wt

| 字段 | 内容 |
|------|------|
| 项目名称 | git-stint/worktrunk/wt |
| 核心能力 | Git工作流增强工具集，支持暂存管理、工作树操作和快速上下文切换 |
| 对本Skill的参考价值 | Git工作流增强可优化本Skill的多任务并行开发体验 |
| 已整合功能点 | Git工作流参考[git-workflow.md](git-workflow.md) |
| 对应Agent/命令/工作流/脚本 | CI/CD Specialist; [git-workflow.md](git-workflow.md) |
| 整合优先级 | P2 |

---

## 10. 协议（Protocols）

### 10.1 Agent2Agent (A2A)

| 字段 | 内容 |
|------|------|
| 项目名称 | Agent2Agent (A2A) |
| 核心能力 | Google提出的Agent间通信协议，支持Agent发现、能力协商、任务委派和结果交换 |
| 对本Skill的参考价值 | A2A协议可标准化本Skill的Agent间通信接口，Agent发现和能力协商可增强Subagent Dispatcher |
| 已整合功能点 | Agent间通信参考[a2a-protocol.md](a2a-protocol.md)；能力协商参考[agent-registry.md](agent-registry.md) |
| 对应Agent/命令/工作流/脚本 | Subagent Dispatcher → /agent-status; Task Coordinator; [a2a-protocol.md](a2a-protocol.md); [agent-registry.md](agent-registry.md); [agent-lifecycle.md](agent-lifecycle.md) |
| 整合优先级 | **P1** |

### 10.2 Model Context Protocol (MCP)

| 字段 | 内容 |
|------|------|
| 项目名称 | Model Context Protocol (MCP) |
| 核心能力 | Anthropic提出的模型上下文协议，标准化AI模型与外部工具/数据源的交互接口 |
| 对本Skill的参考价值 | MCP协议已作为本Skill知识库服务(knowledge-server.py)的工具集成基础，MCP安全评估已整合到安全框架 |
| 已整合功能点 | MCP工具集成参考knowledge-server.py的mcp_server.py；MCP安全参考[mcp-protocol.md](mcp-protocol.md)和ASI04 |
| 对应Agent/命令/工作流/脚本 | Knowledge Manager → /learn; knowledge-server.py; mcp_server.py; [mcp-protocol.md](mcp-protocol.md); [knowledge-base-architecture.md](knowledge-base-architecture.md); [kb-api-reference.md](kb-api-reference.md) |
| 整合优先级 | **P1** |

---

## 11. 设计工具（Design Tools）

### 11.1 Penpot/Figma

| 字段 | 内容 |
|------|------|
| 项目名称 | Penpot/Figma |
| 核心能力 | 开源/商业设计工具，支持UI设计、原型制作和设计系统管理 |
| 对本Skill的参考价值 | 设计工具集成可增强Design System Generator的设计系统生成能力 |
| 已整合功能点 | 设计系统参考[design-database.md](design-database.md)和[design-guidelines.md](design-guidelines.md) |
| 对应Agent/命令/工作流/脚本 | Design System Generator → /design-system; UI Designer; UX Designer; [design-database.md](design-database.md); [design-guidelines.md](design-guidelines.md) |
| 整合优先级 | P2 |

### 11.2 Storybook/Chromatic

| 字段 | 内容 |
|------|------|
| 项目名称 | Storybook/Chromatic |
| 核心能力 | 组件文档和视觉测试平台，Storybook提供组件隔离开发环境，Chromatic提供视觉回归测试 |
| 对本Skill的参考价值 | 组件文档和视觉测试可增强Frontend Stylist的组件开发流程和visual-regression.js |
| 已整合功能点 | 视觉回归测试参考visual-regression.js；组件开发参考[design-system-template.md](../templates/design-system-template.md) |
| 对应Agent/命令/工作流/脚本 | Frontend Stylist → /design-system; E2E Tester; visual-regression.js; design-tokens-sync.js; [design-database.md](design-database.md) |
| 整合优先级 | P2 |

### 11.3 axe-core/Pa11y

| 字段 | 内容 |
|------|------|
| 项目名称 | axe-core/Pa11y |
| 核心能力 | 可访问性测试工具，axe-core提供浏览器端可访问性检查，Pa11y提供自动化可访问性测试 |
| 对本Skill的参考价值 | 可访问性测试已整合到accessibility-test.js和ACCESSIBILITY质量门禁中 |
| 已整合功能点 | 可访问性测试参考accessibility-test.js和[templates/accessibility-checklist.md](../templates/accessibility-checklist.md) |
| 对应Agent/命令/工作流/脚本 | UX Designer → /design-system; E2E Tester → /test; accessibility-test.js; [templates/accessibility-checklist.md](../templates/accessibility-checklist.md) |
| 整合优先级 | P2 |

### 11.4 Style Dictionary

| 字段 | 内容 |
|------|------|
| 项目名称 | Style Dictionary |
| 核心能力 | 设计令牌转换工具，支持将设计令牌转换为多平台样式文件(CSS/SCSS/Swift/Kotlin等) |
| 对本Skill的参考价值 | 设计令牌转换已整合到design-tokens-sync.js和[templates/design-tokens.json](../templates/design-tokens.json) |
| 已整合功能点 | 设计令牌参考design-tokens-sync.js和[templates/design-tokens.json](../templates/design-tokens.json) |
| 对应Agent/命令/工作流/脚本 | Design System Generator → /design-system; Frontend Stylist; design-tokens-sync.js; [templates/design-tokens.json](../templates/design-tokens.json) |
| 整合优先级 | P2 |

### 11.5 Docusaurus/MkDocs

| 字段 | 内容 |
|------|------|
| 项目名称 | Docusaurus/MkDocs |
| 核心能力 | 文档站点生成器，Docusaurus基于React，MkDocs基于Python，支持Markdown文档发布 |
| 对本Skill的参考价值 | 文档站点生成可增强Documentation Engineer的文档发布能力 |
| 已整合功能点 | 文档标准参考[documentation-standards.md](documentation-standards.md) |
| 对应Agent/命令/工作流/脚本 | Documentation Engineer; [documentation-standards.md](documentation-standards.md); documentation-coverage.py |
| 整合优先级 | P2 |

---

## 12. 安全框架（Security Frameworks）

### 12.1 Project CodeGuard

| 字段 | 内容 |
|------|------|
| 项目名称 | Project CodeGuard |
| 核心能力 | Cisco开源模型无关安全框架，将secure-by-default规则嵌入AI代码生成的规划→生成→审查三阶段，安全规则可配置 |
| 对本Skill的参考价值 | 规划→生成→审查三阶段模式已整合到Code Reviewer安全编码审查，secure-by-default规则嵌入AI代码生成全流程 |
| 已整合功能点 | 三阶段安全模式参考[agentic-security-frameworks.md](agentic-security-frameworks.md)；secure-by-default规则参考ASI05防护；安全规则可配置参考[security-guidelines.md](security-guidelines.md) |
| 对应Agent/命令/工作流/脚本 | Code Reviewer → /review; Security Auditor → /audit; [agentic-security-frameworks.md](agentic-security-frameworks.md); [owasp-agentic-top10-2026.md](owasp-agentic-top10-2026.md); [security-guidelines.md](security-guidelines.md) |
| 整合优先级 | **P0** |

---

## 13. 基准测试（Benchmarking）

### 13.1 SWE-Bench/Multi-SWE-bench

| 字段 | 内容 |
|------|------|
| 项目名称 | SWE-Bench/Multi-SWE-bench |
| 核心能力 | 软件工程基准测试套件，SWE-Bench评估AI代码修复能力，Multi-SWE-bench扩展到多语言多场景 |
| 对本Skill的参考价值 | 基准测试方法论可参考用于评估本Skill的代码修复和自动化开发能力 |
| 已整合功能点 | 质量评估参考[quality-gates.md](quality-gates.md)和53个质量门禁 |
| 对应Agent/命令/工作流/脚本 | QA Engineer → /test; Test Architect; [quality-gates.md](quality-gates.md); skill-test.py; completion-verifier.py |
| 整合优先级 | P2 |

---

## 统计总览

### 按优先级统计

| 优先级 | 数量 | 项目列表 |
|--------|------|----------|
| **P0** | 8 | andrej-karpathy-skills, create-sddwcc, claude-code-collective, agency-agents, @hivehub/rulebook, CangjieSkills, Project CodeGuard, OWASP Agentic Top 10 2026 |
| **P1** | 10 | TrinityGuard, AgentForge, VulnSage, SafeAgents, Microsoft Agent Framework, TestForge, Dapr Agents, LangGraph, A2A, MCP |
| **P2** | 68 | 其余全部项目 |

### 按领域统计

| 领域 | 数量 | P0 | P1 | P2 |
|------|------|-----|-----|-----|
| 行为准则 | 2 | 1 | 0 | 1 |
| SDD+TDD | 10 | 2 | 0 | 8 |
| 多Agent架构 | 16 | 1 | 3 | 12 |
| 安全评估 | 17 | 1 | 3 | 13 |
| 渗透测试 | 7 | 0 | 0 | 7 |
| 桌面开发 | 8 | 0 | 0 | 8 |
| 知识库 | 2 | 2 | 0 | 0 |
| 测试 | 3 | 0 | 1 | 2 |
| DevOps/版本控制 | 3 | 0 | 0 | 3 |
| 协议 | 2 | 0 | 2 | 0 |
| 设计工具 | 5 | 0 | 0 | 5 |
| 安全框架 | 1 | 1 | 0 | 0 |
| 基准测试 | 1 | 0 | 0 | 1 |
| **合计** | **77** | **8** | **9** | **60** |

> **注**: 上述统计基于13个领域分类的77个独立项目。部分项目在领域间存在交叉引用（如AG2既属于多Agent架构又关联安全评估中的Maris），实际去重后总计86个映射条目对应77个独立开源项目。

### P0项目整合状态

| 项目 | 整合状态 | 关键整合点 |
|------|----------|-----------|
| andrej-karpathy-skills | 已完整整合 | SKILL.md不可妥协原则；Code Reviewer审查流程；[karpathy-guidelines.md](karpathy-guidelines.md) |
| create-sddwcc | 已部分整合 | /sprint初始化流程；templates/目录 |
| claude-code-collective | 已部分整合 | commands/命令系统；Agent编排模式 |
| agency-agents | 已部分整合 | [agent-registry.md](agent-registry.md)；[agent-lifecycle.md](agent-lifecycle.md) |
| @hivehub/rulebook | 已完整整合 | SKILL.md增量约束；loop-guard.py；[karpathy-guidelines.md](karpathy-guidelines.md)双向强化闭环 |
| CangjieSkills | 已部分整合 | SKILL.md frontmatter；commands/命令系统 |
| Project CodeGuard | 已部分整合 | [agentic-security-frameworks.md](agentic-security-frameworks.md)；ASI05防护 |
| OWASP Agentic Top 10 2026 | 已完整整合 | AGENTIC-SECURITY质量门禁；全部安全Agent职责；[owasp-agentic-top10-2026.md](owasp-agentic-top10-2026.md) |

### P1项目推荐整合路径

| 项目 | 推荐整合方向 | 预期收益 |
|------|-------------|----------|
| TrinityGuard | 三层风险分类→Security Auditor审计检查清单 | 增强安全评估系统性 |
| AgentForge | Agent动态生成→Subagent Dispatcher | 增强Agent生态扩展性 |
| VulnSage | 多Agent漏洞利用→AI Penetration Tester | 增强漏洞验证能力 |
| SafeAgents | Agent行为安全测试→Security Auditor | 增强安全评估方法论 |
| Microsoft Agent Framework | 企业级编排→Orchestrator | 增强编排层企业级能力 |
| TestForge | 规格驱动测试生成→Test Architect | 增强TDD自动化 |
| Dapr Agents | 分布式运行时→Runtime Supervisor | 增强分布式部署能力 |
| LangGraph | 图式工作流→9阶段工作流 | 增强工作流灵活性 |
| A2A | Agent通信协议→Subagent Dispatcher | 标准化Agent间通信 |
| MCP | 工具集成协议→Knowledge Manager | 标准化工具接入方式 |

---

## 相关参考

- [Agentic安全框架集成指南](agentic-security-frameworks.md)
- [AI渗透测试框架集成指南](ai-pentest-frameworks.md)
- [安全前沿框架集成指南](security-frontier-frameworks.md)
- [OWASP Agentic Top 10 2026 参考文档](owasp-agentic-top10-2026.md)
- [Karpathy Guidelines 参考文档](karpathy-guidelines.md)
- [Agent注册表](agent-registry.md)
- [质量门禁](quality-gates.md)
- [知识库架构](knowledge-base-architecture.md)
- [A2A协议参考](a2a-protocol.md)
- [MCP协议参考](mcp-protocol.md)

---

> 本文档由 Multi-Agent SDD/TDD Orchestrator 维护 | 最后更新: 2026-05-06 | 版本: 3.0.0
