# 安全前沿框架集成指南

> 版本: 3.1.0 | 更新日期: 2026-05-06 | 编码: UTF-8 without BOM | 行尾: LF
> 质量门禁: AGENTIC-SECURITY | 需求文档: skill需求v3.0 §安全框架集成

---

## 概述

本文档收录当前多Agent安全领域的前沿框架，为xuansto-skill v3.0安全框架集成提供参考。涵盖安全评估监控、运行时安全工具包、安全基准测试、合规框架和安全编排平台五大方向，每个框架提供核心能力描述及与本Skill的集成方式。

---

## 目录

1. [TrinityGuard](#trinityguard)
2. [Agent Governance Toolkit](#agent-governance-toolkit)
3. [OpenAgentSafety](#openagentsafety)
4. [MAESTRO](#maestro)
5. [JoySafeter](#joysafeter)
6. [Maris](#maris)
7. [SAFEFLOW](#safeflow)
8. [SAGA](#saga)
9. [Project CodeGuard](#project-codeguard)
10. [框架对比矩阵](#框架对比矩阵)
11. [参考资料](#参考资料)

---

## TrinityGuard

### 基本信息

| 属性 | 说明 |
|------|------|
| 名称 | TrinityGuard |
| 来源 | 上海AI实验室（Shanghai AI Lab）开源 |
| 定位 | MAS安全评估与监控框架 |
| 许可证 | Apache 2.0 |

### 核心能力

TrinityGuard是面向多Agent系统（MAS）的安全评估与监控框架，采用三层守护架构提供全生命周期安全防护：

- **三层20种风险分类体系**: Prevention-Guard、Detection-Guard、Response-Guard三层架构，覆盖20种多Agent系统特有风险类型
- **OWASP标准对齐**: 风险分类与OWASP Agentic Top 10 2026（ASI01-ASI10）全面对齐，确保国际标准合规
- **评估层+运行时监控双层防护**:
  - 评估层（Evaluation Layer）：Agent行为基线建模、安全基准测试、风险量化评分，覆盖20个风险类别的静态风险评估
  - 运行时监控层（Runtime Monitoring Layer）：目标劫持检测、工具调用合规性验证、记忆完整性实时校验，对Agent行为进行实时监控和异常检测
- **LLM Judge Factory统一协调**: 提供LLM Judge Factory机制，统一协调多个安全评估Judge的判定逻辑，确保评估结果的一致性和可复现性，支持自定义Judge规则注入

### 三层详细定义

#### Layer 1: 评估层（Evaluation Layer）

评估层在系统部署前和代码审查阶段执行静态风险评估，覆盖20个风险类别：

| 编号 | 风险类别 | 评估要点 | 对应ASI |
|------|----------|----------|---------|
| TG-R01 | 提示注入 | 系统提示可被用户输入覆盖；间接注入向量存在 | ASI01 |
| TG-R02 | 权限滥用 | Agent可突破预设权限边界；工具调用缺少权限校验 | ASI03 |
| TG-R03 | 数据泄露 | Agent响应泄露系统提示/内部指令；意外暴露用户数据 | ASI05 |
| TG-R04 | 目标劫持 | Agent可被诱导偏离原始任务目标；目标完整性校验缺失 | ASI01 |
| TG-R05 | 工具滥用 | Agent可调用未授权工具；工具参数缺少输入验证 | ASI02 |
| TG-R06 | 记忆投毒 | Agent长期记忆未加密存储；记忆数据可被未授权修改 | ASI06 |
| TG-R07 | 身份冒充 | Agent间身份认证不可靠；存在身份伪造可能 | ASI03 |
| TG-R08 | 供应链攻击 | Agent依赖的工具/MCP服务不可信；第三方插件缺少安全审查 | ASI04 |
| TG-R09 | 不安全输出处理 | Agent输出未经消毒即执行/渲染；存在命令注入风险 | ASI05 |
| TG-R10 | 过度自主 | Agent拥有不必要操作权限；缺少人工确认机制 | ASI09 |
| TG-R11 | 系统提示泄露 | 可通过技巧获取系统提示；系统提示包含敏感信息 | ASI01 |
| TG-R12 | 不安全记忆管理 | 记忆存储未加密；记忆访问缺少权限控制 | ASI06 |
| TG-R13 | 拒绝服务 | 可触发Agent无限循环/资源耗尽；缺少请求频率限制 | ASI08 |
| TG-R14 | 不安全工具集成 | MCP服务未验证调用者身份；工具参数缺少输入验证 | ASI02 |
| TG-R15 | 级联故障 | 单Agent故障可传播至整个系统；缺少熔断机制 | ASI08 |
| TG-R16 | Agent间通信不安全 | Agent间消息未加密传输；缺少消息完整性校验 | ASI07 |
| TG-R17 | 意外代码执行 | Agent生成代码未在沙箱中执行；缺少代码签名验证 | ASI05 |
| TG-R18 | 可观测性缺失 | Agent行为缺少完整审计日志；异常行为缺少告警 | ASI10 |
| TG-R19 | 伦理违规 | Agent输出未经伦理审查；缺少内容过滤机制 | ASI09 |
| TG-R20 | 不可解释性 | Agent决策不可追溯；缺少决策日志和推理链记录 | ASI10 |

#### Layer 2: 运行时监控层（Runtime Monitoring Layer）

运行时监控层在系统运行阶段执行，对Agent行为进行实时监控和异常检测：

- **Agent行为监控**: 目标一致性监控、工具调用模式异常检测、输出内容异常检测、决策路径异常检测
- **通信安全监控**: Agent间消息完整性校验、通信加密状态监控、重放攻击检测、通信频率异常检测
- **资源使用监控**: CPU/内存使用异常检测、网络流量异常检测、工具调用频率异常检测、Token消耗异常检测

#### Layer 3: LLM Judge Factory（统一结果协调层）

LLM Judge Factory统一协调多个安全评估Judge的判定逻辑：

- **Judge类型**: Prompt Injection Judge、Permission Judge、Data Leakage Judge、Tool Safety Judge、Memory Integrity Judge、Communication Judge、Agency Judge、Observability Judge
- **协调机制**: Judge调度→评判执行→结果聚合→冲突解决→综合评分（0-100）
- **自定义Judge**: 支持注入自定义Judge规则，适配特定业务场景的安全评估需求

### 对本Skill的集成方式

| 集成点 | 集成方式 | 对应ASI风险 |
|--------|----------|-------------|
| Security Auditor安全评估 | 参考TrinityGuard三层风险分类体系，构建安全审计检查清单 | ASI01-ASI10 |
| Runtime Supervisor运行时监控 | 集成TrinityGuard运行时监控模式，实施目标一致性检测和工具调用合规验证 | ASI01, ASI02 |
| AI Penetration Tester测试设计 | 参考TrinityGuard 20种风险分类设计渗透测试用例 | ASI01-ASI10 |
| 安全评估报告模板 | 采用TrinityGuard风险量化评分体系，生成标准化安全评分卡 | 全局 |
| LLM Judge Factory评估协调 | 集成LLM Judge Factory统一协调机制，实现多Judge安全评估判定的一致性保障 | ASI01-ASI10 |

### 参考链接

- GitHub: https://github.com/InternLM/TrinityGuard
- 论文: TrinityGuard: A Three-Layer Framework for Multi-Agent System Security Assessment and Monitoring

---

## Agent Governance Toolkit

### 基本信息

| 属性 | 说明 |
|------|------|
| 名称 | Agent Governance Toolkit |
| 来源 | 微软（Microsoft）开源 |
| 定位 | AI代理运行时安全工具包 |
| 许可证 | MIT |

### 核心能力

微软推出的AI代理运行时安全工具包，为AI代理提供声明式安全策略定义与运行时强制执行能力：

- **覆盖全部10项OWASP Agentic风险**: 完整覆盖ASI01-ASI10全部风险项，提供对应的安全控制措施
- **Agent OS策略引擎**: 提供声明式安全策略定义与运行时强制执行的策略引擎，支持策略热更新和版本管理，为Agent行为提供全局策略约束
- **Agent Mesh安全通信**: 提供Agent间通信加密、身份验证和消息完整性校验的标准化实现，构建安全的多Agent通信网格
- **Agent Runtime动态执行环**: 为Agent代码执行提供沙箱隔离环境，限制资源访问和系统调用范围，支持动态执行策略调整和运行时行为拦截

### 对本Skill的集成方式

| 集成点 | 集成方式 | 对应ASI风险 |
|--------|----------|-------------|
| Runtime Supervisor策略拦截 | 集成Agent Governance Toolkit Agent OS策略引擎，实施操作拦截和审批门禁 | ASI09 |
| Agent间通信安全 | 参考Agent Governance Toolkit Agent Mesh安全通信方案，增强ASI07防护 | ASI07 |
| 代码执行沙箱 | 采用Agent Governance Toolkit Agent Runtime动态执行环模式，强化ASI05防护 | ASI05 |
| Compliance Officer合规检查 | 参考Agent Governance Toolkit策略合规报告，生成合规性证明 | ASI03, ASI09 |

### 参考链接

- GitHub: https://github.com/microsoft/agent-governance-toolkit
- 文档: Microsoft Agent Governance Toolkit Documentation

---

## OpenAgentSafety

### 基本信息

| 属性 | 说明 |
|------|------|
| 名称 | OpenAgentSafety |
| 来源 | ICLR 2026 接收论文，开源评估框架 |
| 定位 | 多Agent安全评估基准框架 |
| 许可证 | MIT |

### 核心能力

面向多Agent系统的综合安全评估框架，提供标准化的安全基准测试套件：

- **8类风险类别**: 覆盖提示注入、工具滥用、权限提升、数据泄露、目标劫持、记忆污染、通信攻击、过度自主8大风险类别
- **350+多轮多用户任务**: 提供超过350个多轮交互、多用户参与的安全测试任务，模拟真实攻击场景
- **真实工具交互**: 测试任务涉及真实工具调用（文件操作、网络请求、数据库访问等），而非模拟环境
- **自动化红队评估**: 支持自动化红队攻击模拟，生成安全评分卡和风险等级量化报告
- **关键发现**: Claude-Sonnet-3.7在51.2%安全脆弱任务中出现不安全行为，揭示了当前最先进LLM在Agent安全场景下仍存在显著安全隐患

### 对本Skill的集成方式

| 集成点 | 集成方式 | 对应ASI风险 |
|--------|----------|-------------|
| AI Penetration Tester测试套件 | 采用OpenAgentSafety 350+测试任务作为渗透测试基础用例库 | ASI01-ASI10 |
| Security Auditor安全评估 | 参考OpenAgentSafety 8类风险类别和评分体系，构建安全评估标准 | ASI01-ASI10 |
| 安全测试自动化 | 集成OpenAgentSafety自动化红队评估流程，实现安全测试CI/CD集成 | 全局 |
| 安全评分卡 | 采用OpenAgentSafety风险量化方法，生成项目安全评分卡 | 全局 |
| 安全基线参考 | 参考OpenAgentSafety关键发现（Claude-Sonnet-3.7 51.2%不安全行为率），建立安全基线参考标准 | ASI01-ASI10 |

### 参考链接

- GitHub: https://github.com/OpenAgentSafety/OpenAgentSafety
- 论文: OpenAgentSafety: A Comprehensive Framework for Evaluating Multi-Agent System Safety (ICLR 2026)

---

## MAESTRO

### 基本信息

| 属性 | 说明 |
|------|------|
| 名称 | MAESTRO |
| 来源 | CSA（云安全联盟，Cloud Security Alliance）发布 |
| 定位 | 高度监管行业多Agent安全框架 |
| 许可证 | 公开标准 |

### 核心能力

MAESTRO是CSA云安全联盟针对高度监管行业发布的多Agent安全框架，提供最小可行控制分层模型：

- **7层最小可行控制模型**: 定义7层安全控制层级，逐层递进提供纵深防御：
  - L1 基础模型层：模型安全基线、输出过滤、内容安全策略
  - L2 数据操作层：数据血缘追踪、输入验证、数据脱敏
  - L3 Agent框架层：Agent身份认证、权限边界、行为约束
  - L4 部署基础设施层：容器隔离、网络分段、资源配额
  - L5 评估可观测性层：安全评估、行为监控、异常检测
  - L6 安全合规层：合规审计、策略执行、证据收集
  - L7 Agent生态层：生态安全、供应链安全、第三方集成管控
- **针对高度监管行业**: 专为金融、医疗、政府等高度监管行业设计，满足严格合规要求
- **威胁模型与攻击树定义**: 提供多Agent系统专用威胁模型和攻击树，支持威胁建模和风险评估
- **与CSA STAR/CCM合规框架对齐**: 安全控制要求与CSA STAR、Cloud Controls Matrix对齐，支持云合规认证

### 对本Skill的集成方式

| 集成点 | 集成方式 | 对应ASI风险 |
|--------|----------|-------------|
| Compliance Officer合规框架 | 采用MAESTRO 7层最小可行控制模型，构建合规检查基线 | ASI03, ASI09 |
| 安全架构设计 | 参考MAESTRO威胁模型和攻击树，指导系统安全架构设计 | ASI01-ASI10 |
| 合规认证 | 对齐MAESTRO与CSA STAR/CCM，支持云安全合规认证 | 全局 |
| 安全控制分级 | 采用MAESTRO 7层最小可行控制模型，实施安全控制分级管理 | ASI04, ASI08 |

### 参考链接

- CSA官网: https://cloudsecurityalliance.org/
- 文档: MAESTRO: Multi-Agent Environment Security Framework for Highly Regulated Industries

---

## JoySafeter

### 基本信息

| 属性 | 说明 |
|------|------|
| 名称 | JoySafeter |
| 来源 | 京东（JD.com）开源 |
| 定位 | AI驱动安全编排平台 |
| 许可证 | Apache 2.0 |

### 核心能力

京东开源的AI驱动安全编排平台，将AI Agent技术与安全运营（SecOps）深度融合：

- **200+安全工具MCP集成**: 通过MCP协议集成超过200种安全工具（Nmap、Burp Suite、Nessus、OpenVAS等），实现安全工具统一编排
- **DeepAgents Manager-Worker星型拓扑**: 采用Manager-Worker星型拓扑架构，Manager Agent负责任务分解和编排，Worker Agent负责具体安全任务执行
- **AI驱动安全事件自动化响应**: 基于AI推理自动识别安全事件类型，触发对应响应工作流
- **威胁情报集成与关联分析**: 集成多源威胁情报，支持跨源关联分析和攻击趋势预测
- **长短期记忆系统**: 内置长短期记忆机制，短期记忆用于当前安全任务上下文维护，长期记忆用于历史攻击模式积累和安全知识沉淀，支持跨任务经验复用
- **全链路Langfuse可观测性**: 集成Langfuse实现安全运营全链路可观测性，覆盖Agent决策追踪、工具调用审计、安全事件时间线、性能指标监控，支持安全运营事后复盘和根因分析

### 对本Skill的集成方式

| 集成点 | 集成方式 | 对应ASI风险 |
|--------|----------|-------------|
| AI Penetration Tester工具编排 | 参考JoySafeter 200+安全工具MCP集成模式，扩展渗透测试工具链 | ASI02, ASI05 |
| 多Agent协作架构 | 采用JoySafeter DeepAgents Manager-Worker星型拓扑，优化安全任务编排 | ASI07, ASI08 |
| 安全事件响应 | 集成JoySafeter安全事件自动化响应流程，增强安全事件处置能力 | ASI10 |
| MCP安全工具集成 | 参考JoySafeter MCP集成规范，标准化安全工具接入方式 | ASI04 |
| 安全运营记忆系统 | 采用JoySafeter长短期记忆系统架构，实现安全知识积累和跨任务经验复用 | ASI01, ASI02 |
| 安全可观测性 | 集成JoySafeter全链路Langfuse可观测性方案，实现安全运营全链路追踪和审计 | 全局 |

### 参考链接

- GitHub: https://github.com/jd-opensource/JoySafeter
- 文档: JoySafeter: AI-Driven Security Orchestration Platform

---

## Maris

### 基本信息

| 属性 | 说明 |
|------|------|
| 名称 | Maris |
| 来源 | AG2（原AutoGen）内置安全防护系统 |
| 定位 | 细粒度策略引导的安全防护系统 |
| 许可证 | Apache 2.0（随AG2发布） |

### 核心能力

Maris是AG2（原Microsoft AutoGen）框架内置的细粒度策略引导安全防护系统，为多Agent系统提供通信级和交互级的安全控制：

- **细粒度策略引导**: 提供细粒度的安全策略定义和引导机制，支持针对不同Agent角色、不同交互场景配置差异化的安全策略
- **Agent间通信控制**: 控制Agent间通信的可见性和权限，防止未授权的信息传递和指令注入，支持通信白名单和黑名单机制
- **Agent-环境交互控制**: 控制Agent与环境（工具、API、文件系统等）的交互行为，限制Agent可访问的环境资源和操作范围
- **策略即代码**: 安全策略以代码形式定义和管理，支持策略版本控制、审计追踪和动态更新

### 对本Skill的集成方式

| 集成点 | 集成方式 | 对应ASI风险 |
|--------|----------|-------------|
| Agent间通信安全 | 参考Maris Agent间通信控制机制，实现细粒度的Agent通信权限管理 | ASI07 |
| Agent-环境交互约束 | 采用Maris Agent-环境交互控制模式，限制Agent可访问的环境资源和操作范围 | ASI02, ASI05 |
| 策略即代码 | 集成Maris策略即代码方案，实现安全策略的版本化管理和动态更新 | ASI09 |
| Runtime Supervisor策略引导 | 参考Maris细粒度策略引导机制，增强运行时安全策略的精确性和灵活性 | ASI01, ASI08 |

### 参考链接

- GitHub: https://github.com/ag2ai/ag2
- 文档: Maris: Fine-Grained Policy-Guided Safety for Multi-Agent Systems

---

## SAFEFLOW

### 基本信息

| 属性 | 说明 |
|------|------|
| 名称 | SAFEFLOW |
| 来源 | 安全研究开源项目 |
| 定位 | 协议级安全框架 |
| 许可证 | 研究许可 |

### 核心能力

SAFEFLOW是协议级安全框架，从协议层面强制执行细粒度信息流控制，为多Agent系统提供信息安全和事务安全的基础保障：

- **强制执行细粒度信息流控制（IFC）**: 在协议层面强制执行细粒度信息流控制策略，确保敏感信息不会通过Agent间通信或环境交互泄露到未授权的接收方
- **事务执行机制**: 引入事务执行机制，Agent操作以事务为单位执行，确保操作的原子性和一致性，防止部分执行导致的安全状态不一致
- **回滚机制**: 提供事务回滚机制，当检测到安全违规或操作异常时，自动回滚到安全状态，消除不安全操作的影响
- **协议级安全保障**: 安全控制在协议层面实现，与具体Agent实现解耦，确保安全策略的强制执行不受Agent行为影响

### 对本Skill的集成方式

| 集成点 | 集成方式 | 对应ASI风险 |
|--------|----------|-------------|
| 信息流控制 | 采用SAFEFLOW细粒度IFC机制，实现Agent间信息传递的安全控制 | ASI06, ASI07 |
| 事务安全 | 集成SAFEFLOW事务执行机制，确保Agent操作的原子性和一致性 | ASI05, ASI10 |
| 安全回滚 | 参考SAFEFLOW回滚机制，实现安全违规时的自动状态恢复 | ASI10 |
| 协议级安全架构 | 参考SAFEFLOW协议级安全设计，构建与Agent实现解耦的安全控制层 | ASI01-ASI10 |

### 参考链接

- 论文: SAFEFLOW: Protocol-Level Security Framework with Information Flow Control for Multi-Agent Systems

---

## SAGA

### 基本信息

| 属性 | 说明 |
|------|------|
| 名称 | SAGA |
| 来源 | 安全研究开源项目 |
| 定位 | 可扩展的Agentic系统治理安全架构 |
| 许可证 | 研究许可 |

### 核心能力

SAGA是可扩展的Agentic系统治理安全架构，提供用户对Agent生命周期的全面监督和治理能力：

- **Agent生命周期监督**: 提供用户对Agent完整生命周期的监督能力，覆盖Agent创建、配置、执行、暂停、终止等全生命周期阶段
- **可扩展治理架构**: 采用可扩展的治理架构设计，支持根据业务需求动态添加治理规则和监督机制
- **用户授权与审批**: 关键Agent操作需要用户显式授权和审批，防止Agent自主执行超出权限范围的危险操作
- **生命周期审计追踪**: 对Agent生命周期中的所有关键事件进行审计追踪，支持事后审查和合规证明

### 对本Skill的集成方式

| 集成点 | 集成方式 | 对应ASI风险 |
|--------|----------|-------------|
| Agent生命周期管理 | 采用SAGA生命周期监督机制，实现Agent从创建到终止的全生命周期安全管理 | ASI08, ASI10 |
| 用户授权审批 | 集成SAGA用户授权与审批机制，为关键操作提供人工审批门禁 | ASI09 |
| 治理规则扩展 | 参考SAGA可扩展治理架构，支持动态添加安全治理规则 | ASI03 |
| 生命周期审计 | 采用SAGA生命周期审计追踪，实现Agent行为全生命周期可审计 | ASI03, ASI09 |

### 参考链接

- 论文: SAGA: Scalable Governance Security Architecture for Agentic Systems

---

## Project CodeGuard

### 基本信息

| 属性 | 说明 |
|------|------|
| 名称 | Project CodeGuard |
| 来源 | Cisco开源，已捐赠至CoSAI（Coalition for Secure AI） |
| 定位 | 模型无关安全框架 |
| 许可证 | Apache 2.0 |

### 核心能力

Project CodeGuard是Cisco开源的模型无关安全框架，将secure-by-default规则嵌入AI编码工作流，从代码生成源头保障安全性：

- **模型无关安全框架**: 安全规则与具体AI模型解耦，适用于任何AI编码助手或代码生成模型，确保安全控制的普适性
- **Secure-by-default规则嵌入**: 将安全规则以默认安全的方式嵌入AI编码工作流，开发者在代码生成过程中自动获得安全保障
- **规划→生成→审查三阶段**: 定义标准化的三阶段安全编码流程：
  - 规划阶段：分析编码需求，识别潜在安全风险，生成安全约束
  - 生成阶段：在安全约束指导下生成代码，确保代码符合安全规范
  - 审查阶段：对生成的代码进行安全审查，检测和修复安全缺陷
- **已捐赠至CoSAI**: 项目已捐赠至CoSAI（Coalition for Secure AI）联盟，成为行业标准级安全框架，获得更广泛的社区支持和持续维护

### 对本Skill的集成方式

| 集成点 | 集成方式 | 对应ASI风险 |
|--------|----------|-------------|
| 代码生成安全 | 采用CodeGuard规划→生成→审查三阶段流程，增强AI代码生成的安全性 | ASI05 |
| Secure-by-default编码规范 | 集成CodeGuard secure-by-default规则，将安全规则嵌入编码工作流 | ASI05, ASI09 |
| 模型无关安全控制 | 参考CodeGuard模型无关设计，实现与具体LLM解耦的安全控制层 | ASI04 |
| 代码安全审查 | 采用CodeGuard审查阶段安全检测方法，增强Security Auditor代码安全审查能力 | ASI05 |

### 参考链接

- GitHub: https://github.com/cisco-open/Project-CodeGuard
- CoSAI: https://coSAI.dev/
- 文档: Project CodeGuard: Model-Agnostic Security Framework for AI Coding Workflows

---

## 框架对比矩阵

| 框架 | 核心定位 | 侧重领域 | OWASP覆盖 | 集成难度 | 适用规模 | 适用场景 |
|------|----------|----------|-----------|----------|----------|----------|
| TrinityGuard | MAS安全评估监控 | 评估+监控 | ASI01-ASI10 | 中 | 中大型 | 安全评估与持续监控 |
| Agent Governance Toolkit | 运行时安全工具包 | 治理+控制 | ASI01-ASI10 | 低 | 企业级 | 运行时策略拦截与合规 |
| OpenAgentSafety | 安全评估基准 | 评估+认证 | 8类风险 | 中 | 通用 | 安全基准测试与认证 |
| MAESTRO | 安全框架标准 | 架构+合规 | 7层控制模型 | 低 | 云原生 | 高度监管行业合规 |
| JoySafeter | 安全编排平台 | 运营+响应 | 工具链覆盖 | 中 | 企业级 | 安全运营自动化 |
| Maris | 策略引导安全防护 | 通信+交互控制 | 细粒度策略 | 低 | 通用 | Agent通信与交互安全 |
| SAFEFLOW | 协议级安全框架 | 信息流+事务安全 | IFC+回滚 | 高 | 通用 | 信息流控制与事务安全 |
| SAGA | 治理安全架构 | 生命周期监督 | 治理+审计 | 中 | 企业级 | Agent生命周期治理 |
| Project CodeGuard | 模型无关安全框架 | 代码生成安全 | 编码安全 | 低 | 通用 | AI编码工作流安全 |

---

## 参考资料

- [OWASP Agentic Top 10 2026](https://owasp.org/www-project-agentic-security/)
- [CSA Cloud Security Alliance](https://cloudsecurityalliance.org/)
- [TrinityGuard - Shanghai AI Lab](https://github.com/InternLM/TrinityGuard)
- [Microsoft Agent Governance Toolkit](https://github.com/microsoft/agent-governance-toolkit)
- [OpenAgentSafety - ICLR 2026](https://github.com/OpenAgentSafety/OpenAgentSafety)
- [JoySafeter - JD.com](https://github.com/jd-opensource/JoySafeter)
- [AG2 (AutoGen) - Maris](https://github.com/ag2ai/ag2)
- [Cisco Project CodeGuard](https://github.com/cisco-open/Project-CodeGuard)
- [CoSAI - Coalition for Secure AI](https://coSAI.dev/)

---

> 本文档由 Multi-Agent SDD/TDD Orchestrator 维护 | 最后更新: 2026-05-06 | 版本: 3.1.0

---

## 相关参考

- [AI渗透测试框架集成指南](ai-pentest-frameworks.md) — AI驱动渗透测试框架参考
- [Agentic安全框架集成指南](agentic-security-frameworks.md) — Agentic安全框架参考
- [OWASP Agentic Top 10 2026 参考文档](owasp-agentic-top10-2026.md) — Agentic AI系统安全风险清单及测试框架
- [安全指南参考文档](security-guidelines.md) — 安全编码实践与Agentic安全防护体系
