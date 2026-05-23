# 多Agent自主开发指导Skill - 需求分析说明书

***

## 文档信息

| 项目          | 内容                                                   |
| :---------- | :--------------------------------------------------- |
| **Skill名称** | `xuansto-skill`                                      |
| **版本**      | v1.2.0                                               |
| **文档类型**    | 需求分析说明书                                              |
| **目标平台**    | Trae / Claude Code / Cursor / Windsurf / Antigravity |
| **编写日期**    | 2026-04-14                                           |
| **修订日期**    | 2026-04-17                                           |

***

## 零、Karpathy Guidelines：LLM编码行为准则

> **整合说明**：本Skill的Agent行为准则融合了[Andrej Karpathy对LLM编码常见陷阱的观察](https://x.com/karpathy/status/2015883857489522876)及其后续开源社区总结形成的**Karpathy Guidelines**。这些准则旨在减少LLM编码中常见的过度复杂化、擅自假设、范围蔓延等问题，与本Skill的SDD+TDD方法论形成互补——Karpathy Guidelines约束“如何正确地做事”，SDD+TDD规范“做什么正确的事”。

### 0.1 准则来源

Karpathy Guidelines由开源社区（[forrestchang/andrej-karpathy-skills](https://github.com/forrestchang/andrej-karpathy-skills)，截至2026年4月已积累超过29K stars）从Andrej Karpathy对LLM编程助手失败模式的系统观察中提炼而成。该项目将Karpathy的核心洞察整理为一个精简的CLAUDE.md / SKILL.md配置文件，直接集成到AI编程助手的上下文中，有效约束AI的编码行为。

Karpathy的核心观点是：AI编程助手在大量参与开发时暴露出的问题，不是简单的语法错误，而是更接近一个“会写代码但判断并不稳的初级工程师”——它会擅自假设、把简单问题复杂化、顺手改动不理解的东西。

### 0.2 四条核心原则

#### 0.2.1 Think Before Coding（编码前思考）

**不要擅自假设。不要隐藏困惑。主动呈现方案权衡。**

在动手实现之前，Agent必须：

- 明确陈述自己的假设。如果不确定，必须提问。
- 如果存在多种解释，呈现所有选项——不要悄悄选择其中一个。
- 如果存在更简单的方案，主动指出。在合理的场景下要敢于质疑或“顶嘴”。
- 如果某处不清楚，停下来。说出困惑之处。提问。

**设计意图**：很多AI编程事故并非代码能力不足，而是在需求定义阶段已经偏离——人在下指令，AI以为自己理解，双方在不同轨道上高速前进。这条准则强制将歧义在编码前暴露。

**本Skill中的映射**：本准则与Phase 1（Clarify）阶段的要求完全一致，要求Product Manager Agent在编写规格前完成歧义检测和需求澄清。所有Agent在执行任务时也应遵循此原则——遇到不确定时先提问，而非擅自推断。

#### 0.2.2 Simplicity First（简洁优先）

**用最少代码解决问题。不添加任何推测性内容。**

在编写代码时，Agent必须：

- 不添加需求之外的功能。
- 不为只使用一次的代码创建抽象层。
- 不凭空增加未被要求的“灵活性”或“可配置性”。
- 不为不可能发生的场景编写防御性逻辑。
- 如果写了200行而50行就能解决——重写。

**检验标准**：“一位资深工程师会认为这段代码过度复杂吗？”如果是，请简化。

**设计意图**：AI非常擅长把“也许以后有用”的结构提前建好，但在真实工程中，很多复杂度不是资产而是负债。

**本Skill中的映射**：本准则与Phase 4（Implementation）中的重构步骤、Phase 7（Iteration）中的代码优化要求一致。Code Reviewer Agent在审查时应严格检查是否引入了不必要的复杂度。

#### 0.2.3 Surgical Changes（外科手术式修改）

**只触碰必须触碰的内容。只清理自己制造的混乱。**

在编辑现有代码时，Agent必须：

- 不“顺手优化”相邻的代码、注释或格式。
- 不重构没有坏的东西。
- 匹配现有代码风格，即使你认为有其他更好的方式。
- 如果注意到无关的死代码，提出来——但不要擅自删除。
- 当Agent自己的修改造成“孤儿”（未使用的导入/变量/函数）时，必须清理。但不要删除原本就存在的死代码，除非明确要求。

**检验标准**：每一个被修改的行都应该能直接追溯到用户的具体请求。

**设计意图**：解决AI改代码时“手太长”的问题——修一个小bug却改掉半个文件，顺便重排格式、重写注释、删除它觉得没用的函数。

**本Skill中的映射**：本准则与多Agent协作模式中的Code Reviewer Agent的审查职责高度一致。Code Reviewer在审查PR时应确保每个变更都可追溯到需求或规格。

#### 0.2.4 Goal-Driven Execution（目标驱动执行）

**定义成功标准。循环执行直到验证通过。**

将模糊的指令式任务转化为可验证的目标：

- “添加验证” → “为无效输入编写测试，然后修改代码使测试通过”
- “修复Bug” → “编写一个能复现Bug的测试，然后修改代码使测试通过”
- “重构X” → “确保测试在重构前后都通过”

对于多步骤任务，应陈述一个简明的计划：

```
1. [步骤] → 验证: [检查点]
2. [步骤] → 验证: [检查点]
3. [步骤] → 验证: [检查点]
```

强有力的成功标准让Agent可以独立循环迭代。薄弱的成功标准（“把它做出来”）则需要不断人工澄清。

**本Skill中的映射**：本准则与本Skill的核心SDD+TDD方法论高度契合——测试即验收标准，规格即法律。Phase 3（Test Design）的输出正是可验证的目标，Phase 4（Implementation）的TDD循环正是“编写测试→使测试通过→重构”的实践。

### 0.3 准则有效性验证

Karpathy Guidelines的有效性已得到社区实证。LangChain团队使用Claude Code与Sonnet 4.6进行基准测试发现：未启用Skills时，代码生成任务通过率仅为25%\~29%；启用Skills（包括类似Karpathy Guidelines的行为约束规则集）后，通过率跃升至95%。

### 0.4 本Skill的Karpathy Guidelines实现

本Skill通过以下机制将Karpathy Guidelines固化为所有Agent的基础行为准则：

| 准则                        | 本Skill实现机制                                                    | 负责Agent                               |
| :------------------------ | :------------------------------------------------------------ | :------------------------------------ |
| **Think Before Coding**   | Phase 1（Clarify）歧义检测强制流程；规格编写前必须陈述假设                          | Product Manager, System Architect     |
| **Simplicity First**      | Phase 4实施中的重构步骤；Code Reviewer复杂度检查；Refactoring Specialist优化审查 | Code Reviewer, Refactoring Specialist |
| **Surgical Changes**      | PR审查中的变更范围检查；Git提交信息可追溯性要求；DiffView变更汇总                       | Code Reviewer, Orchestrator           |
| **Goal-Driven Execution** | Phase 3测试用例设计→Phase 4 TDD循环→Phase 5/6验证与验收的完整闭环               | Test Architect, 全体Agent               |

此外，本Skill在Agent定义模板中新增了`# Behavioral Guidelines`章节，要求每个Agent明确如何在其职责范围内实践上述四条准则。

### 0.5 参考开源项目更新（Karpathy Guidelines相关）

| 项目                                                    | 说明                                                         | 对本Skill的参考价值                |
| :---------------------------------------------------- | :--------------------------------------------------------- | :-------------------------- |
| **andrej-karpathy-skills**（forrestchang, \~29K stars） | 基于Andrej Karpathy对LLM编码陷阱观察总结的行为准则，整合为CLAUDE.md            | 本Skill核心行为准则的直接来源，约束Agent行为 |
| **@hivehub/rulebook**                                 | 工具无关的AI开发框架，跨Claude Code/Cursor/Gemini等28种语言标准化            | 质量门禁自动化、增量实施规范、知识库强制工作流     |
| **spatie/guidelines-skills**                          | Spatie团队编码规范以Skills形式分发，含Laravel PHP/JavaScript/安全/版本控制四技能 | 领域专用Skills的组织方式、渐进式激活机制     |
| **Project CodeGuard**（Cisco开源）                        | 模型无关的安全框架，将secure-by-default实践嵌入AI编码工作流                    | 安全Skill架构设计、规则库组织方式         |
| **CangjieSkills**（仓颉语言开源）                             | 结构化技能知识库替代原始文档检索，实测降低60% Token消耗                           | 技能知识蒸馏方法、成本优化策略             |

***

## 一、概述

### 1.1 项目背景

随着AI辅助编程工具（Trae、Claude Code、Cursor、Windsurf等）的普及，开发者面临的挑战从“如何写出代码”转变为“如何系统化地管理AI驱动的软件开发全生命周期”。单一通用大模型“样样通、样样松”的局限性日益凸显，无法胜任从需求分析到生产交付的端到端复杂开发任务。

当前业界领先的多Agent框架（如agency-agents、MoAI-ADK、PactKit、TDDev等）已经证明了“专业分工协作”模式的有效性。agency-agents通过将复杂业务流程拆解成几十个高度专业化的Agent角色，以Markdown为载体，构建了一个“即插即用的全功能AI外包机构”，每个Agent具备深度专业化、独特人格和交付导向的特性。MoAI-ADK则结合SPEC-First开发方法论、TDD和24个专业AI Agent，提供完整的开发生命周期管理。同时，以Microsoft Agent Framework、Dapr Agents、CrewAI为代表的新一代多Agent基础框架，提供了生产级的运行时基础设施（图工作流、状态持久化、A2A/MCP跨运行时互操作），为多Agent系统的规模化部署奠定了技术基础。

2026年AI Agent框架生态持续蓬勃发展。Microsoft Agent Framework于2026年2月达到Release Candidate状态，API表面已锁定，整合了Semantic Kernel与AutoGen，提供企业级多Agent编排能力与长期支持承诺，支持Python和.NET双语言生态，稳定API涵盖单Agent抽象、图工作流、多Agent编排模式（顺序/并发/移交/群聊/Magentic-One）等，并原生支持A2A、AG-UI和MCP标准互操作。OpenAI于2025年推出Agents SDK（Python和JavaScript/TypeScript版本），以轻量、易用的设计理念构建多Agent工作流，并提供细粒度控制和人工审批机制。Anthropic于2025年12月发布了Agent Skills规范，该规范已被Claude、OpenAI Codex、GitHub Copilot、Cursor等多个Agent平台采纳，Microsoft、Atlassian、Figma、Canva等企业已为其平台构建了专属Skills。同时，开源社区涌现出一批创新框架：OpenSage实现了Agent自编程生成能力，让LLM自动创建Agent拓扑和工具集；Sema Code将AI编码Agent引擎与客户端解耦，实现可嵌入式基础设施架构；AgentForge提出执行验证型多Agent框架，将Bug修复分解为Planner、Coder、Tester、Debugger、Critic五个专业Agent并强制每次代码变更的执行验证。这些发展表明，AI Agent框架正从实验阶段走向生产级部署，多Agent协作已成为企业级AI应用的核心架构模式。

本Skill旨在整合上述最佳实践，为Trae、Claude Code等主流AI开发工具提供一个功能完善的多Agent自主开发指导系统，基于SDD（规格驱动开发）+ TDD（测试驱动开发）循环，覆盖分析、设计（含UI/UX）、开发、测试、修复、完善、优化、验收、迭代的全流程。

### 1.2 核心目标

本Skill的核心目标是构建一个“多Agent开发指挥中心”，实现以下关键能力：

1. **自主任务分解**：根据用户输入的需求描述，自动分解任务并调度合适的专业Agent团队
2. **SDD+TDD双循环**：强制实施“Spec → Test → Code”的开发范式，确保规格即法律、测试即标准
3. **Karpathy行为准则约束**：所有Agent遵循Think Before Coding、Simplicity First、Surgical Changes、Goal-Driven Execution四条原则，从根本上减少LLM编码常见错误
4. **全栈协同开发**：支持前后端代码并行开发、数据库联调、接口契约管理
5. **完整自动化测试体系**：涵盖单元测试、集成测试、端到端测试、安全测试的完整测试金字塔
6. **UI/UX设计自动化**：支持设计系统生成、原型评审、可访问性检查、设计稿转代码
7. **文档规范化**：强制实施各类文档模板（PRD、技术设计、API文档、用户手册等）
8. **迭代闭环与验收**：支持从需求到交付的持续迭代优化，具备自修复、知识沉淀及正式验收门禁

### 1.3 适用场景

| 场景类型       | 触发条件        | 工作流强度                  |
| :--------- | :---------- | :--------------------- |
| 复杂新功能开发    | 涉及多组件、多文件   | 完整SDD+TDD全流程 + UI/UX设计 |
| 架构/技术决策    | 技术栈选型、模式选择  | ADR + 可行性分析            |
| 大规模重构      | 跨模块代码变更     | RFC + TDD循环            |
| 简单功能/Bug修复 | 单文件、小范围变更   | TDD快速流程                |
| 安全敏感功能     | 认证、授权、加密相关  | 强制安全审计流程               |
| UI/UX重设计   | 界面改版、设计系统更新 | 设计评审 + 视觉回归测试          |

### 1.4 参考开源项目

本Skill充分借鉴以下开源项目的设计理念和最佳实践：

| 项目                                             | 参考价值                                                                                                       |
| :--------------------------------------------- | :--------------------------------------------------------------------------------------------------------- |
| **andrej-karpathy-skills**                     | Karpathy Guidelines四条行为准则，约束LLM编码行为，减少过度复杂化、擅自假设、范围蔓延                                                      |
| **@hivehub/rulebook**                          | 工具无关的AI开发框架，跨28种语言标准化，增量实施规范（3次尝试重启规则）、知识库强制工作流、Ralph自主循环、持久化记忆，201次发布                                     |
| **spatie/guidelines-skills**                   | Spatie团队编码规范以Skills形式分发，含Laravel PHP/JavaScript/安全/版本控制四技能，渐进式激活机制                                         |
| **Project CodeGuard**                          | Cisco开源的模型无关安全框架，将secure-by-default规则嵌入AI编码工作流（规划→生成→审查三阶段），已捐赠至CoSAI                                      |
| **CangjieSkills**                              | 仓颉语言AI编程增强方案，DocFlow知识蒸馏流程，结构化技能知识库替代原始文档检索，实测降低60% Token消耗，基于OpenCode+GLM5验证                              |
| **create-sddwcc**                              | Claude Code多Agent架构驱动的完整SDD系统，18个专业Agent覆盖从需求到部署全流程，包含MCP集成和定义完成框架                                         |
| **claude-code-collective**                     | 30+ TDD强制专业Agent集合，包含Context7实时文档集成、智能任务路由、RED→GREEN→REFACTOR循环强制执行                                        |
| **agency-agents**                              | 角色分工矩阵、轻量级Markdown Agent定义、多工具集成                                                                           |
| **MoAI-ADK**                                   | SPEC-First + TDD框架、24个专业Agent、85%+测试覆盖率保证、EARS规格格式                                                         |
| **PactKit**                                    | Plan-Act-Check-Done生命周期、9个专业Agent、质量门禁体系                                                                   |
| **TDDev**                                      | 多Agent TDD全栈应用生成、可执行测试用例自动推导、迭代精化                                                                          |
| **AgentMesh**                                  | Planner-Coder-Debugger-Reviewer协作模式、任务分解与通信架构                                                              |
| **Don Cheli SDD Framework**                    | 71+命令、42技能、TDD强制、OWASP审计、Anthropic Skills 2.0兼容                                                            |
| **Trae SOLO**                                  | Plan模式（规划先于执行）、Sub Agent专项分工、DiffView变更汇总                                                                  |
| **agents-skill**                               | 智能路由、并行执行、静默失败处理、多模式协同、合成报告                                                                                |
| **@itz4blitz/agentful**                        | 三层Agent架构、Git worktree并行开发、质量门禁自动验证、模式学习                                                                   |
| **cursor-agent**                               | Cursor/Windsurf增强配置、进程规划与自进化                                                                               |
| **TestTeam**                                   | 70-Agent测试编排、自修复循环、信誉评分、持久记忆                                                                               |
| **Microsoft Agent Framework**                  | 生产级多Agent SDK+运行时，Semantic Kernel+AutoGen融合，图工作流、A2A/MCP互操作、RC状态（2026年2月）                                  |
| **AgentForge**                                 | 执行验证型多Agent框架，强制每次代码变更的Docker沙箱验证，SWE-bench Lite 40.0%解决率                                                  |
| **SEMAG**                                      | 自进化多Agent代码生成框架，按任务难度自适应调整工作流                                                                              |
| **TALM**                                       | 动态树结构多Agent框架，长期记忆与局部错误修正                                                                                  |
| **Dapr Agents**                                | 分布式Agent Actor模型，单核运行数千Agent，工作流持久化与自动重试                                                                   |
| **CrewAI**                                     | 角色驱动的Agent协作，任务/角色抽象，内置移交机制                                                                                |
| **Strix**                                      | AI多Agent协同渗透测试，Docker沙箱验证真实漏洞                                                                              |
| **Spec Kit**                                   | 四阶段规格驱动开发（Specify→Plan→Tasks→Implement），项目宪法支持                                                             |
| **A2A / MCP 协议**                               | Agent间互操作标准协议，跨框架Agent通信与工具连接基础设施                                                                          |
| **OpenAI Agents SDK**                          | 轻量级多Agent框架，支持Python和JavaScript/TypeScript，Agent/Handoff/Guardrail三原语，内置MCP集成与追踪系统                         |
| **AG2 (原AutoGen)**                             | 多Agent对话框架，人类介入工作流、群聊式协作、事件驱动架构                                                                            |
| **LangGraph**                                  | 图式化Agent编排，StateGraph状态管理、持久化、人工干预、多模式协作（Supervisor/Swarm/Collaborative）                                   |
| **OpenSage**                                   | Agent自编程生成引擎，LLM自动创建Agent拓扑与工具集，层次化图式记忆系统                                                                  |
| **Sema Code**                                  | 可嵌入式AI编码框架，Agent引擎与客户端解耦，多租户隔离、上下文压缩、MCP/Skills/Plugins三层生态集成                                              |
| **Orla**                                       | LLM多Agent系统服务库，阶段映射、工作流编排、跨边界KV缓存管理                                                                        |
| **AWE**                                        | 内存增强多Agent Web渗透测试框架，XSS成功率87%，盲SQLi成功率66.7%                                                               |
| **TestForge**                                  | 反馈驱动的Agentic测试套件生成，pass\@1率84.3%，单文件成本$0.63                                                                |
| **UnitTenX**                                   | AI多Agent遗留代码单元测试生成，结合形式验证                                                                                  |
| **AgentGit**                                   | Git式状态版本控制框架，支持MAS工作流的commit/revert/branch                                                                 |
| **Worktrunk**                                  | Git worktree CLI管理工具，专为并行AI Agent工作流设计                                                                     |
| **SafeAgents**                                 | 微软开源的多Agent安全评估框架，系统化暴露设计选择（计划构建策略、Agent间上下文共享、回退行为）对对抗性提示的敏感度，提出Dharma诊断度量识别薄弱环节                          |
| **FCV-Attack研究**                               | 揭示功能正确但存在漏洞的补丁（FCV patches）威胁，跨12种Agent-模型组合的SWE-Bench评估，攻击仅需黑盒访问和单次查询                                     |
| **IMBIA / Adv-IMBIA**                          | 隐蔽恶意行为注入攻击（IMBIA）及防御机制研究，显示编码和测试阶段Agent被攻陷的安全风险最大                                                          |
| **OWASP Top 10 for Agentic Applications 2026** | Agentic AI安全风险框架，涵盖目标劫持、工具滥用、身份权限滥用、供应链漏洞、代码执行、记忆中毒、Agent间不安全通信、级联故障、过度自主、监控与可观测性不足等十大风险                   |
| **TrinityGuard**                               | 上海AI实验室开源的多Agent系统安全评估与监控框架，三层20种风险分类，OWASP标准对齐，支持评估层+运行时监控双层防护                                            |
| **VulnSage**                                   | 多Agent自动化漏洞利用生成框架，模拟安全研究者工作流分解为Code Analyzer/Code Generation/Validation/Reflection Agents，已发现146个真实0-day漏洞 |
| **JoySafeter**                                 | 京东开源AI驱动安全编排平台，200+安全工具MCP集成，DeepAgents Manager-Worker星型拓扑，长短期记忆系统，全链路Langfuse可观测性                         |
| **Agent Governance Toolkit**                   | 微软开源的AI代理运行时安全工具包，MIT许可证，首个覆盖全部10项OWASP Agentic风险的工具集，Agent OS策略引擎+Agent Mesh安全通信+Agent Runtime动态执行环       |
| **OpenAgentSafety**                            | ICLR 2026接受的多Agent安全评估框架，8类关键风险类别，350+多轮多用户任务，真实工具交互（浏览器、代码执行、文件系统），Claude-Sonnet-3.7在51.2%的安全脆弱任务中出现不安全行为 |
| **Argusee**                                    | DARKNAVY提出的多Agent协作漏洞发现架构，模拟人类安全团队分工协作机制，在Linux USB协议栈测试中发现CVE-2025-37891高危漏洞                              |
| **MAESTRO**                                    | CSA云安全联盟发布的多Agent环境安全框架，针对银行业等高度监管行业设计，最小可行控制分层模型（基础模型/数据操作/Agent框架/部署基础设施/评估可观测性/安全合规/Agent生态）            |
| **Penpot / Figma API**                         | 开源设计工具集成，设计稿转代码、设计系统同步                                                                                     |
| **Storybook / Chromatic**                      | UI组件库开发、视觉回归测试、组件文档自动化                                                                                     |
| **Percy / Applitools**                         | 视觉测试与UI快照对比                                                                                                |
| **A11y (axe-core)**                            | 无障碍测试自动化                                                                                                   |
| **GitHub Docs / ReadTheDocs**                  | 文档托管与版本化规范                                                                                                 |
| **Maris (AG2内置)**                              | 细粒度策略引导的安全防护系统，控制Agent间通信和Agent-环境交互，内置Guardrails自动检测                                                      |
| **SAFEFLOW**                                   | 协议级安全框架，强制执行细粒度信息流控制（IFC），引入事务执行、冲突解决和回滚机制                                                                 |
| **SAGA**                                       | 可扩展的Agentic系统治理安全架构，提供用户对Agent生命周期的监督，引入加密机制派生访问控制令牌                                                       |
| **AutoPentester**                              | LLM Agent驱动的自动化渗透测试框架，子任务完成率较PentestGPT提升27.0%，漏洞覆盖率提升39.5%                                                |
| **xOffense**                                   | AI驱动的多Agent渗透测试框架，使用微调的中型开源LLM（Qwen3-32B）驱动推理和决策                                                           |
| **SWE-Bench / Multi-SWE-bench**                | 多语言软件工程Agent能力基准测试框架                                                                                       |

### 1.5 多语言开发规范支持

本Skill提供针对不同编程语言和技术栈的专门开发规范，确保Agent在处理各种语言项目时有统一的规范指导。

#### 1.5.1 语言规范文件索引

| 语言 | 规范文件 | 主要技术栈覆盖 |
|------|----------|----------------|
| **Python** | `references/python-standards.md` | PEP 8、Type Hints、pytest、FastAPI、Django、Flask |
| **Go** | `references/go-standards.md` | Effective Go、go mod、testify、Gin、Echo、Fiber |
| **Java** | `references/java-standards.md` | Java命名约定、JUnit 5、Spring Boot、Quarkus、Maven/Gradle |
| **Rust** | `references/rust-standards.md` | Rust API指南、Cargo、proptest、thiserror、unsafe准则 |
| **TypeScript/JavaScript** | `references/typescript-standards.md` | ESLint、React、Vue、Angular、NestJS、Express、Fastify |

#### 1.5.2 规范内容结构

每个语言规范文件包含以下完整章节：

| 章节 | 内容说明 |
|------|----------|
| **命名规范** | 变量、函数、类、文件、模块命名约定 |
| **代码风格** | 缩进、格式化、注释规范 |
| **项目结构** | 目录布局、模块划分、配置文件规范 |
| **依赖管理** | 包管理器使用、版本约束、安全审计 |
| **测试规范** | 单元测试、集成测试、E2E测试框架和最佳实践 |
| **安全规范** | 语言特定的安全编码准则和漏洞防护 |
| **框架规范** | 常见框架的最佳实践和代码示例 |
| **检查清单** | 提交前检查、代码审查检查项 |

#### 1.5.3 规范应用机制

```yaml
语言检测规则:
  Python项目:
    - 检测文件: pyproject.toml, setup.py, requirements.txt
    - 加载规范: references/python-standards.md
  
  Go项目:
    - 检测文件: go.mod
    - 加载规范: references/go-standards.md
  
  Java项目:
    - 检测文件: pom.xml, build.gradle
    - 加载规范: references/java-standards.md
  
  Rust项目:
    - 检测文件: Cargo.toml
    - 加载规范: references/rust-standards.md
  
  TypeScript/JavaScript项目:
    - 检测文件: package.json, tsconfig.json
    - 加载规范: references/typescript-standards.md

规范应用优先级:
  1. 项目自定义规范（.editorconfig, .eslintrc, pyproject.toml [tool.ruff]）
  2. 语言专用规范（references/[lang]-standards.md）
  3. 通用编码规范（references/coding-standards.md）
```

#### 1.5.4 Agent规范应用职责

| Agent角色 | 规范应用职责 |
|-----------|--------------|
| **Code Reviewer** | 根据被审查代码的语言加载对应规范，进行代码审查 |
| **Backend Developer** | 根据后端技术栈加载对应规范，实现代码 |
| **Frontend Developer** | 加载 TypeScript/JavaScript 规范，实现前端代码 |
| **Test Architect** | 根据项目语言加载测试规范章节，设计测试用例 |
| **Security Auditor** | 根据项目语言加载安全规范章节，进行安全审计 |

***

## 二、角色架构设计

### 2.1 角色矩阵总览

参考agency-agents的部门化角色组织方式，本Skill定义以下核心Agent角色：

```text
skill/
├── orchestrator/        # 编排层 - 核心调度角色（1个）
├── product/             # 产品层 - 需求与规格（3个）
├── design/              # 设计层 - UI/UX与交互设计（3个）
├── engineering/         # 工程层 - 前后端开发（6个）
├── database/            # 数据层 - 数据库设计与运维（3个）
├── testing/             # 测试层 - 各类测试专家（8个）
├── security/            # 安全层 - 安全审计与渗透（3个）
├── devops/              # 运维层 - 部署与监控（3个）
├── quality/             # 质量层 - 审查与优化（3个）
└── documentation/       # 文档层 - 文档编写与规范（2个）
# 总计：35个Agent
```

### 2.2 详细角色定义

#### 2.2.1 编排层（Orchestrator）

| 角色               | 职责                             | 核心能力                 | Karpathy行为准则实践             |
| :--------------- | :----------------------------- | :------------------- | :------------------------- |
| **Orchestrator** | 任务接收、分解、Agent调度、结果汇总、冲突仲裁、会话管理 | 智能路由、并行编排、上下文管理、故障恢复 | 任务分解前澄清歧义；确保每步有验证标准；不做过度编排 |

#### 2.2.2 产品层（Product）

| 角色                   | 职责                      | 核心能力                     | Karpathy行为准则实践           |
| :------------------- | :---------------------- | :----------------------- | :----------------------- |
| **Product Manager**  | 需求澄清、功能分解、用户故事编写、验收标准定义 | 需求分析、PRD生成、用户故事拆解        | 陈述假设；呈现多种方案；不擅自决定；明确验收标准 |
| **System Architect** | 系统架构设计、技术选型、模块划分、接口契约定义 | 架构决策记录（ADR）、技术可行性评估、依赖分析 | 呈现技术方案权衡；指出更简单方案；不隐藏困惑   |
| **Technical Writer** | 技术文档编写、API文档生成、README维护 | OpenAPI规范生成、文档一致性校验      | 匹配现有文档风格；手术式修改；不顺手优化     |

#### 2.2.3 设计层（Design）

| 角色                   | 职责                                     | 核心能力                           | Karpathy行为准则实践         |
| :------------------- | :------------------------------------- | :----------------------------- | :--------------------- |
| **UI Designer**      | 视觉设计、设计系统建立、设计令牌生成、设计稿输出（Figma/Penpot） | 色彩/字体/间距规范、图标设计、设计系统文档化        | 陈述设计假设；呈现多种方案；可验证的设计令牌 |
| **UX Designer**      | 用户研究、交互设计、原型制作、可用性测试规划                 | 用户旅程地图、线框图、可访问性设计（WCAG 2.1 AA） | 陈述交互假设；若不清楚用户行为，先提问    |
| **Frontend Stylist** | 设计稿转代码（CSS/SCSS/Tailwind）、响应式布局、动画效果   | 设计令牌转CSS变量、组件样式实现、跨浏览器兼容       | 简洁优先（不添加未要求的样式）；匹配现有风格 |

#### 2.2.4 工程层（Engineering）

| 角色                      | 职责                                            | 核心能力                          | Karpathy行为准则实践           |
| :---------------------- | :-------------------------------------------- | :---------------------------- | :----------------------- |
| **Frontend Developer**  | 前端代码实现（React/Vue/Angular）、组件开发、状态管理           | UI组件生成、响应式设计、性能优化             | 简洁优先；手术式修改；不添加未要求的功能     |
| **Backend Developer**   | 后端代码实现（Node/Python/Go/Java）、API开发、业务逻辑        | 路由设计、中间件开发、数据验证               | 最少代码解决问题；不为不可能场景写防御性逻辑   |
| **Full-Stack Engineer** | 前后端联调、接口对接、数据流设计                              | 契约测试、E2E数据流验证、Session管理       | 若接口契约有歧义，先澄清再实现          |
| **Database Engineer**   | 数据库设计（PostgreSQL/MySQL/MongoDB）、Schema管理、查询优化 | 表结构设计、索引优化、SQL审查              | 不添加未要求的索引/字段；手术式修改Schema |
| **Mobile Developer**    | 移动端适配（React Native/Flutter）、跨端一致性             | 响应式适配、移动端特有API                | 简洁优先；若200行能减到50行，重写      |
| **DevOps Engineer**     | 部署配置、CI/CD流水线、环境管理、监控告警                       | Docker配置、K8s编排、GitHub Actions | 目标驱动执行；定义部署验证标准；循环直到验证通过 |

#### 2.2.5 数据库层（Database）

| 角色               | 职责                    | 核心能力              | Karpathy行为准则实践        |
| :--------------- | :-------------------- | :---------------- | :-------------------- |
| **Data Modeler** | 数据建模、ER图设计、范式规范化、关系定义 | 概念/逻辑/物理模型设计      | 陈述建模假设；呈现备选方案；不擅自决定范式 |
| **DBA**          | 数据库运维、性能调优、备份恢复、迁移管理  | 慢查询分析、执行计划优化、锁分析  | 手术式修改索引/配置；不顺手优化无关内容  |
| **Data Seeder**  | 测试数据生成、数据工厂、Seed脚本管理  | 符合业务规则的数据生成、数据匿名化 | 不添加未要求的测试数据；清理自身生成的孤儿 |

#### 2.2.6 测试层（Testing）

| 角色                        | 职责                                       | 核心能力                                    | Karpathy行为准则实践          |
| :------------------------ | :--------------------------------------- | :-------------------------------------- | :---------------------- |
| **Test Architect**        | 测试策略制定、测试金字塔规划、测试框架选型                    | 测试覆盖率目标设定、测试类型分布规划                      | 目标驱动执行；测试即验收标准          |
| **Unit Tester**           | 单元测试编写（Jest/Vitest/Pytest/JUnit）、TDD红绿重构 | 边界条件测试、Mock/Stub设计、代码覆盖率分析              | 编写失败测试→使通过→重构，完整TDD循环   |
| **Integration Tester**    | 集成测试编写（API测试、数据库集成、第三方服务）                | 契约测试、数据库事务测试、消息队列测试                     | 每步有验证标准；明确成功/失败条件       |
| **E2E Tester**            | 端到端测试编写（Playwright/Cypress）、用户旅程模拟       | UI交互自动化、多页面流程、视觉回归                      | 关键用户旅程即验证标准             |
| **Performance Tester**    | 性能测试（k6/JMeter）、负载测试、压力测试                | 并发场景、响应时间分析、瓶颈定位                        | 定义性能基准；每次发布验证是否退化       |
| **Security Tester**       | 安全测试（OWASP Top 10）、漏洞扫描、渗透测试             | SQL注入检测、XSS检测、CSRF检测、认证绕过               | 不添加未要求的“防御”；验证现有安全机制有效性 |
| **AI Penetration Tester** | AI驱动的自主渗透测试                              | 多Agent协同侦察、注入攻击、权限提升、漏洞验证、Docker沙箱利用链验证 | 陈述测试假设；若发现边界，提问         |
| **Test Maintainer**       | 测试用例维护、失败分析、测试数据管理                       | 测试去重、Flaky测试检测、测试执行优化                   | 手术式修改测试；清理自身引入的孤立测试     |

#### 2.2.7 安全层（Security）

| 角色                     | 职责                             | 核心能力                 | Karpathy行为准则实践 |
| :--------------------- | :----------------------------- | :------------------- | :------------- |
| **Security Auditor**   | 代码安全审计、依赖漏洞扫描、OWASP合规检查        | SAST分析、CVE检测、安全编码规范  | 陈述审计发现；若有歧义，提问 |
| **Penetration Tester** | 渗透测试、漏洞验证、攻击面分析                | 认证绕过测试、权限提升测试、注入攻击模拟 | 目标驱动执行；验证漏洞真实性 |
| **Compliance Officer** | 合规检查（GDPR/PCI-DSS）、数据隐私审计、审计日志 | 敏感数据检测、加密合规、审计追踪     | 若有合规边界不清晰，先澄清  |

#### 2.2.8 运维层（DevOps）

| 角色                     | 职责                     | 核心能力                             | Karpathy行为准则实践         |
| :--------------------- | :--------------------- | :------------------------------- | :--------------------- |
| **CI/CD Specialist**   | 流水线配置、自动化构建、部署脚本       | GitHub Actions/GitLab CI配置、多环境部署 | 手术式修改流水线配置；不重构无关Job    |
| **Monitor Specialist** | 应用监控、日志聚合、告警配置         | Prometheus指标、Sentry错误追踪、ELK日志    | 目标驱动执行；定义告警阈值并持续验证     |
| **Runtime Supervisor** | Agent运行时健康监控、状态恢复、弹性伸缩 | Agent存活检测、工作流检查点恢复、资源动态调度、降级     | 循环检查直到验证通过；不强加未要求的保护措施 |

#### 2.2.9 质量层（Quality）

| 角色                         | 职责                  | 核心能力                                | Karpathy行为准则实践          |
| :------------------------- | :------------------ | :---------------------------------- | :---------------------- |
| **Code Reviewer**          | 代码审查、规范检查、最佳实践建议    | 代码规范（ESLint/Prettier/Pylint）、设计模式审查 | 手术式审查；检查复杂度是否超标；指出更简单方案 |
| **Refactoring Specialist** | 代码重构、技术债务清理、性能优化    | 代码异味检测、重构模式应用、复杂度降低                 | 简洁优先；确保测试在重构前后通过        |
| **Documentation Reviewer** | 文档审查、API文档一致性、注释完整性 | 文档覆盖率检查、OpenAPI一致性校验                | 匹配文档风格；手术式修改；不顺手优化      |

#### 2.2.10 文档层（Documentation）

| 角色                         | 职责                          | 核心能力                                                        | Karpathy行为准则实践          |
| :------------------------- | :-------------------------- | :---------------------------------------------------------- | :---------------------- |
| **Documentation Engineer** | 编写和维护用户手册、开发者指南、部署文档、故障排查手册 | Markdown/ReStructuredText编写、文档版本控制、文档站生成（Docusaurus/MkDocs） | 匹配文档风格；不添加未要求的内容        |
| **Specification Keeper**   | 维护规格文档索引、确保各文档间一致性、管理文档变更历史 | 文档间交叉引用检查、版本差异追踪、文档模板规范化                                    | 陈述一致性假设；若发现不一致，提问；手术式修改 |

### 2.3 Agent定义规范

参考agency-agents的Markdown Agent定义方式，并结合Karpathy Guidelines行为准则，每个Agent采用标准化模板：

```yaml
---
name: UI Designer
emoji: 🎨
description: 资深UI设计师，精通设计系统与视觉语言
color: pink
services: [design-system, visual-design, design-tokens]
---

# Identity & Memory
- **核心身份**：资深UI设计师，8年跨平台产品设计经验
- **工作记忆**：项目设计语言、组件库演进、用户反馈历史

# Core Mission
负责产品视觉设计、设计系统建立与维护、设计稿输出

# Behavioral Guidelines (Karpathy Guidelines)
- **Think Before Coding**：陈述设计假设；若存在多种风格选项，呈现所有备选方案；若设计约束不清晰，先提问
- **Simplicity First**：不添加未被要求的组件变体；不为单一场景创建设计系统
- **Surgical Changes**：只修改指定的设计组件；不顺手优化其他页面设计；匹配项目既有设计语言
- **Goal-Driven Execution**：每个设计任务明确定义可验证的输出（设计令牌、截图对比）

# Critical Rules
- 遵循WCAG 2.1 AA可访问性标准
- 设计令牌（颜色/字体/间距）必须与开发实现一致
- 设计稿必须包含暗色模式支持（如适用）
- 所有图标须提供SVG格式

# Technical Deliverables
- Figma/Penpot设计文件
- 设计系统文档（颜色、字体、组件变体）
- 设计令牌（JSON/CSS变量）
- 可访问性检查报告

# Workflow Process
1. 接收需求 → 2. 用户旅程分析 → 3. 线框原型 → 4. 高保真设计 → 5. 设计评审 → 6. 设计令牌输出

# Success Metrics
- 设计到代码实现一致性 > 95%
- 可访问性违规数为0
- 设计系统使用覆盖率 > 80%
```

### 2.4 角色与工作流阶段映射

为确保每个阶段都有明确的责任Agent，下表定义各Phase的参与角色：

| 工作流阶段                             | 主Agent                                 | 辅助Agent                                                                        | 触发条件           |
| :-------------------------------- | :------------------------------------- | :----------------------------------------------------------------------------- | :------------- |
| **Phase 0: UX Research & Design** | UX Designer, UI Designer               | Product Manager, Frontend Stylist                                              | 新功能/UI变更需求     |
| **Phase 1: Clarify**              | Product Manager                        | System Architect, UX Designer                                                  | 用户输入新需求        |
| **Phase 2: Plan & Spec**          | System Architect                       | Product Manager, Technical Writer, Specification Keeper                        | Clarify完成      |
| **Phase 3: Test Design**          | Test Architect                         | Security Auditor, Performance Tester, UX Designer（可用性测试）                       | Spec通过         |
| **Phase 4: Implementation**       | Frontend/Backend/Database Engineer（并行） | Unit Tester, Code Reviewer, Frontend Stylist                                   | 测试用例设计完成       |
| **Phase 5: Verification**         | QA Engineer（聚合）                        | Security Auditor, AI Penetration Tester, Performance Tester, UI Designer（视觉回归） | 代码实现完成         |
| **Phase 6: Acceptance**           | Product Manager                        | Compliance Officer, Documentation Engineer, UX Designer                        | Verification通过 |
| **Phase 7: Iteration**            | Orchestrator                           | Refactoring Specialist, Test Maintainer, Specification Keeper                  | 验收发现问题或用户反馈    |

此外，**数据库层**角色（Data Modeler, DBA, Data Seeder）在Phase 2、Phase 4、Phase 5中按需被调用；**运维层**角色（DevOps Engineer, CI/CD Specialist, Monitor Specialist, Runtime Supervisor）在Phase 5验证通过后介入部署与监控；**文档层**角色（Documentation Engineer, Specification Keeper）贯穿Phase 2至Phase 7，确保文档同步更新。

***

## 三、SDD+TDD双循环工作流（含UI/UX设计）

### 3.1 核心原则：Spec是法律

本Skill的核心原则：**Spec > Test > Code**。规格是唯一的真相来源，测试是从规格派生的验收标准，代码是实现。**设计系统也是规格的一部分**，设计令牌和组件变体必须与代码实现保持同步。

同时，所有Agent在执行过程中必须遵循**Karpathy Guidelines**四条行为准则：

- **Think Before Coding**：在动手前陈述假设、澄清歧义、呈现权衡
- **Simplicity First**：最少代码解决问题，不添加未要求的功能和抽象
- **Surgical Changes**：只触碰必须改的内容，不顺手优化无关部分
- **Goal-Driven Execution**：定义可验证的成功标准，循环迭代直到通过

此外，结合@hivehub/rulebook的**增量实施规范**理念，所有复杂任务的实施必须遵循“分解→单步实现→测试验证→重复”的渐进式方法：若Agent在同一错误上连续3次尝试失败，必须停止、记录反模式、从头重新开始。

### 3.2 完整工作流（7个阶段）

参考PactKit的Plan-Act-Check-Done生命周期、sdd-tdd-workflow的6阶段模型、Spec Kit的四阶段范式（Specify→Plan→Tasks→Implement）、create-sddwcc的18 Agent SDD系统架构、claude-code-collective的TDD强制执行模式、以及Karpathy Guidelines的Goal-Driven Execution原则，同时新增UI/UX设计阶段和验收阶段：

```text
┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                     SDD+TDD + UI/UX + 验收 完整工作流（7个阶段）                                         │
├─────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                     │
│  Phase 0: UX/UI Design    Phase 1: Clarify          Phase 2: Plan & Spec         Phase 3: Test Design│
│  ┌───────────────────┐    ┌─────────────────┐      ┌─────────────────┐          ┌─────────────────┐   │
│  │ 用户研究          │    │ 需求澄清        │      │ 规格编写        │          │ 测试用例设计    │   │
│  │ 交互设计          │───▶│ 歧义检测        │───▶  │ RFC/ADR         │───▶      │ Unit+Int+E2E    │   │
│  │ 视觉设计          │    │ 结构化问题      │      │ 实施计划        │          │ 可用性测试计划  │   │
│  │ 设计系统          │    └─────────────────┘      └─────────────────┘          └─────────────────┘   │
│  └───────────────────┘                                                                              │
│                                                                                                     │
│                                          ▼                                                          │
│                                                                                                     │
│  Phase 4: Implementation    Phase 5: Verification       Phase 6: Acceptance        Phase 7: Iteration│
│  ┌─────────────────┐        ┌─────────────────┐         ┌─────────────────┐        ┌─────────────────┐│
│  │ TDD 红-绿-重构  │  ───▶  │ 全量测试执行    │  ───▶  │ 用户验收测试    │  ───▶  │ 修复与优化      ││
│  │ 设计令牌同步    │        │ 安全审计        │         │ 合规验收        │        │ 模式学习        ││
│  │ 前后端联调      │        │ 性能测试        │         │ 文档验收        │        │ 知识沉淀        ││
│  └─────────────────┘        └─────────────────┘         └─────────────────┘        └─────────────────┘│
│                                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

#### Phase 0: UX/UI Design（设计与原型）

- **负责Agent**：UX Designer（主）、UI Designer（主）
- **涉及Agent**：Product Manager（需求输入），Frontend Stylist（技术可行性评估）
- **输入**：用户需求（来自Phase 1的澄清结果，或独立的设计请求）
- **输出**：
  - 用户旅程地图、线框图（低保真原型）
  - 高保真设计稿（Figma/Penpot导出为PNG/SVG）
  - 设计系统文档（颜色、字体、间距、组件变体）
  - 设计令牌（JSON/CSS变量，如`--primary-color: #0052CC`）
  - 可访问性评估报告（基于WCAG 2.1 AA）
  - 交互原型（可点击演示）
- **Karpathy行为准则应用**：
  - Think Before Coding：陈述设计假设；若用户旅程有歧义，先澄清；呈现多种设计方案备选
  - Simplicity First：不添加未要求的页面/组件；不为单一场景建立设计系统
  - Goal-Driven Execution：每个设计产出有明确的验证标准（设计令牌JSON、截图对比）
- **质量门禁**：
  - 设计稿通过内部设计评审
  - 设计令牌与开发技术栈兼容（如CSS自定义属性或Tailwind配置）
  - 可访问性无A级违规
  - 关键用户旅程已覆盖

#### Phase 1: Clarify（需求澄清）

- **负责Agent**：Product Manager
- **涉及Agent**：System Architect（按需提供技术可行性初步评估），UX Designer（提供用户体验视角）
- **输入**：用户自然语言需求描述
- **输出**：澄清问题列表（歧义检测）、结构化需求说明、初步用户故事（Given-When-Then格式）
- **Karpathy行为准则应用**：
  - Think Before Coding：陈述所有假设；若有多种解读，呈现所有选项；若某处不清楚，停下来提问
  - Goal-Driven Execution：将模糊需求转化为可验证的用户故事和验收标准
- **质量门禁**：所有歧义问题已解决或标注为待定

#### Phase 2: Plan & Spec（规格规划）

- **负责Agent**：System Architect（主）+ Product Manager（辅）
- **涉及Agent**：Technical Writer（协助文档模板），Data Modeler（若涉及数据模型），Specification Keeper（维护规格一致性）
- **输入**：澄清后的需求、设计稿（如有）
- **输出**：
  - RFC（功能规格文档）或ADR（架构决策记录）
  - 实施计划（任务分解、优先级、依赖关系）
  - 模块划分与接口契约定义（OpenAPI/GraphQL Schema）
  - 风险矩阵与缓解策略
  - 数据模型定义（ER图）
  - 设计令牌与组件映射表（设计元素→代码组件）
- **Karpathy行为准则应用**：
  - Think Before Coding：呈现多种技术方案及权衡；若存在更简单的架构，主动指出并推回
  - Simplicity First：拒绝过度工程化的架构设计；不添加未要求的技术组件
  - Goal-Driven Execution：每个模块定义可验证的接口契约
- **质量门禁**：规格完整性检查通过、接口契约已定义、技术可行性评估通过、设计令牌与代码组件一一对应

#### Phase 3: Test Design（测试设计）

- **负责Agent**：Test Architect（主）+ 各测试角色（辅）
- **涉及Agent**：Security Auditor（安全测试用例），Performance Tester（性能基线），UX Designer（可用性测试场景）
- **输入**：规格文档、接口契约、设计稿
- **输出**：
  - 单元测试用例设计
  - 集成测试场景设计
  - E2E测试用户旅程（与用户旅程地图对齐）
  - 安全测试清单（OWASP Top 10 + Agentic Top 10 + AI渗透测试场景）
  - 性能测试指标定义
  - 可用性测试计划（任务完成率、时间、满意度）
  - 视觉回归测试基线（Storybook/Chromatic快照）
- **Karpathy行为准则应用**：
  - Goal-Driven Execution：测试即验收标准——将每个需求点转化为可执行的测试用例
  - Think Before Coding：若有边界场景不确定，先澄清
- **质量门禁**：测试覆盖率预估达到目标阈值，可用性测试场景覆盖关键路径

#### Phase 4: Implementation（实施）

- **负责Agent**：Frontend/Backend/Database等工程Agent（并行执行）
- **涉及Agent**：Unit Tester（辅助编写测试），Code Reviewer（实时审查），Data Seeder（生成测试数据），Frontend Stylist（实现设计令牌和样式）
- **输入**：规格、测试用例设计、接口契约、设计令牌
- **执行方式**：TDD红-绿-重构-验证循环，参考claude-code-collective的强制TDD模式——测试先行，最小实现使测试通过，然后重构优化
  - **RED**：编写失败的测试用例
  - **GREEN**：编写最小代码使测试通过
  - **REFACTOR**：重构代码优化结构，保持测试通过
  - **VERIFY**：快速回归验证重构未引入新问题
- **增量实施约束**：参考@hivehub/rulebook的增量实施规范，Agent必须遵循“分解复杂任务→实现单个步骤→测试验证→重复”的工作模式；若在同一个错误上连续3次尝试失败，必须停止、记录反模式、从头重新开始
- **Karpathy行为准则应用**：
  - Simplicity First：用最少代码使测试通过；不添加未要求的功能；若200行可减至50行，重写
  - Surgical Changes：只修改与当前任务相关的文件；不顺手优化相邻代码或格式；匹配现有代码风格
  - Goal-Driven Execution：每个TDD循环有明确的验证点
- **设计令牌同步**：前端开发中，设计令牌（CSS变量/JS对象）必须与设计系统保持一致，通过自动化脚本同步（如`design-tokens sync`）
- **并行机制**：参考agentful的Git worktree并行开发，前后端+测试并发执行
- **Git分支操作**：每个功能开发必须在独立的 `feature/*` 分支上进行；分支命名规则 `feature/<功能简述>`；代码提交遵循约定式提交规范；完成后自动创建PR，触发CI流水线。
- **输出**：功能代码（前后端 + 数据库Schema）、通过的测试用例、代码审查报告、设计令牌实现代码

#### Phase 5: Verification（验证）

- **负责Agent**：QA Engineer（主）+ Security Auditor + AI Penetration Tester + Performance Tester
- **涉及Agent**：Integration Tester, E2E Tester, Compliance Officer（若需合规检查），UI Designer（视觉回归测试）
- **执行内容**：
  - 全量测试执行（单元+集成+E2E）
  - 安全扫描（SAST + 依赖漏洞）
  - AI自主渗透测试
  - 性能基准测试
  - 规格一致性校验
  - 文档完整性检查
  - 视觉回归测试（Chromatic/Percy）
  - 可访问性自动化测试（axe-core）
- **Karpathy行为准则应用**：
  - Goal-Driven Execution：每个测试门禁有明确的通过/失败标准
  - Think Before Coding：若测试失败原因不明确，先分析再修复；不盲目猜测
- **输出**：
  - 测试执行报告（通过率、覆盖率）
  - 安全审计报告（P0-P3严重等级）
  - 性能测试报告
  - 视觉差异报告
  - 可访问性违规清单
- **质量门禁**：所有测试通过 + 无P0/P1安全问题 + 覆盖率达标 + 视觉差异 < 1%（需人工审核）

#### Phase 6: Acceptance（验收）

- **负责Agent**：Product Manager（主）
- **涉及Agent**：Compliance Officer（合规验收），Documentation Engineer（文档验收），UX Designer（用户体验验收）
- **输入**：Phase 5验证通过的产物
- **执行内容**：
  - **用户验收测试（UAT）** ：基于用户故事和验收标准，由Product Manager模拟最终用户执行关键场景
  - **合规验收**：检查GDPR/PCI-DSS等法规要求（如适用）
  - **文档验收**：确保用户手册、API文档、部署指南完整且与实现一致
  - **体验验收**：检查设计实现是否与设计稿一致，可用性指标是否达标（任务完成率≥95%，满意度≥4/5）
  - **性能验收**：验证是否满足非功能性需求（响应时间、并发用户等）
  - **安全验收**：确认所有安全门禁已通过，无未修复的中高危漏洞
- **Karpathy行为准则应用**：
  - Goal-Driven Execution：以Phase 1定义的验收标准为唯一依据；不添加未声明的验收项
  - Think Before Coding：若验收发现问题，先明确问题归属再进入Iteration
- **输出**：
  - 用户验收测试报告
  - 合规检查清单签署
  - 文档完整性报告
  - 体验验收报告
  - 正式发布建议（批准/驳回）
- **质量门禁**：
  - 所有验收标准通过
  - 无阻塞性问题
  - 文档覆盖率100%（关键文档）
  - 体验指标达标
  - 若验收不通过，返回Phase 7迭代修复

#### Phase 7: Iteration（迭代）

- **负责Agent**：Orchestrator（主）+ Refactoring Specialist
- **涉及Agent**：Test Maintainer（分析失败测试），Code Reviewer（二次审查），Specification Keeper（更新规格文档）
- **输入**：验证阶段或验收阶段的反馈
- **执行内容**：
  - 失败测试分析与修复
  - 安全问题修复
  - 代码优化与重构
  - 设计不一致调整（视觉差异修复）
  - 模式学习（成功模式持久化）
  - 知识库更新
  - 规格文档与设计文档同步更新
- **Karpathy行为准则应用**：
  - Surgical Changes：修复只针对具体问题；不扩大变更范围
  - Simplicity First：修复方案选择最简单的可行选项
  - Goal-Driven Execution：每次修复后重新验证相关门禁
- **输出**：修复后的代码、迭代总结报告、学习到的模式、更新后的规格文档
- **循环**：如发现问题则返回Phase 4/5/6，直至通过全部门禁

***

## 四、UI/UX设计详细流程

### 4.1 设计阶段集成

为确保UI/UX设计无缝融入开发流水线，本Skill定义以下子流程：

#### 4.1.1 设计系统建立与维护

| 活动          | 负责Agent                        | 输出                              | 工具/格式                                |
| :---------- | :----------------------------- | :------------------------------ | :----------------------------------- |
| **设计系统初始化** | UI Designer                    | 设计令牌（颜色、字体、间距、阴影）、组件库基础         | Figma/Penpot，导出JSON/CSS变量            |
| **设计令牌管理**  | UI Designer + Frontend Stylist | `tokens.json` / `variables.css` | Style Dictionary / Token Transformer |
| **组件变体定义**  | UI Designer                    | 按钮、输入框、卡片等组件的所有状态（默认、悬停、禁用、加载）  | Figma组件集 / Storybook                 |
| **暗色模式支持**  | UI Designer                    | 暗色主题设计令牌                        | 媒体查询 `prefers-color-scheme`          |
| **设计系统文档**  | UI Designer + Technical Writer | 使用指南、代码示例、可访问性说明                | Storybook / Docusaurus               |

#### 4.1.2 设计稿到代码转换

| 步骤        | 负责Agent                               | 工具/方法                               |
| :-------- | :------------------------------------ | :---------------------------------- |
| 1. 设计稿导出  | UI Designer                           | Figma/Penpot导出为SVG/PNG，或使用Figma API |
| 2. 设计令牌提取 | UI Designer + Frontend Stylist        | Figma Tokens插件 / 手动映射               |
| 3. 组件代码生成 | Frontend Developer + Frontend Stylist | 基于设计系统生成React/Vue组件，应用CSS变量         |
| 4. 视觉回归测试 | E2E Tester / UI Designer              | Chromatic / Percy，对比设计稿截图与实现截图      |
| 5. 可访问性测试 | Security Auditor / E2E Tester         | axe-core / Pa11y，集成到CI              |

#### 4.1.3 用户体验研究方法

| 方法          | 负责Agent                        | 时机                      | 产出                   |
| :---------- | :----------------------------- | :---------------------- | :------------------- |
| **用户访谈**    | UX Designer                    | Phase 0                 | 需求优先级、用户痛点           |
| **可用性测试**   | UX Designer + Test Architect   | Phase 3（计划），Phase 6（执行） | 任务完成率、错误率、满意度问卷（SUS） |
| **A/B测试设计** | UX Designer + Product Manager  | Phase 2                 | 实验方案、指标定义            |
| **可访问性审计**  | UX Designer + Security Auditor | Phase 0、Phase 5         | WCAG 2.1 AA合规报告      |

### 4.2 设计相关模板

- `templates/design-system-template.md`：设计系统文档模板（包含颜色、排版、间距、组件变体表格）
- `templates/design-tokens.json`：设计令牌JSON示例
- `templates/usability-test-plan.md`：可用性测试计划模板
- `templates/accessibility-checklist.md`：可访问性检查清单（WCAG 2.1 AA）

### 4.3 设计质量门禁

| 门禁名称                  | 检查内容      | 通过标准                       | 阻塞级别            |
| :-------------------- | :-------- | :------------------------- | :-------------- |
| **DESIGN-REVIEW**     | 设计稿评审     | 关键流程和组件设计通过产品/技术/设计三方评审    | BLOCK           |
| **DESIGN-TOKENS**     | 设计令牌与代码同步 | 设计令牌JSON与CSS变量完全一致         | BLOCK           |
| **VISUAL-REGRESSION** | 视觉回归测试    | 差异像素 < 0.1% 或 所有差异需人工确认无影响 | WARN/BLOCK      |
| **ACCESSIBILITY**     | 可访问性检查    | 无A级违规，AA级违规数≤0             | BLOCK           |
| **UX-ACCEPTANCE**     | 用户体验验收    | 任务完成率≥95%，SUS分数≥70         | BLOCK（在Phase 6） |

***

## 五、文档规范

### 5.1 文档体系概览

本Skill强制建立分层文档体系，确保信息可追溯、可维护：

```text
docs/
├── product/                 # 产品文档
│   ├── prd.md               # 产品需求文档（包含用户故事、验收标准）
│   ├── user-journey.md      # 用户旅程地图
│   └── release-notes.md     # 版本发布说明
├── technical/               # 技术文档
│   ├── architecture/        # 架构决策记录（ADR）
│   │   ├── adr-001-use-postgresql.md
│   │   └── ...
│   ├── api/                 # API文档（OpenAPI 3.0）
│   │   └── openapi.yaml
│   ├── database/            # 数据库Schema文档
│   │   └── er-diagram.md
│   └── deployment/          # 部署指南
│       ├── docker.md
│       └── kubernetes.md
├── design/                  # 设计文档
│   ├── design-system.md     # 设计系统规范
│   ├── tokens.json          # 设计令牌
│   └── accessibility.md     # 可访问性声明
├── user/                    # 用户文档
│   ├── user-manual.md       # 用户手册
│   ├── faq.md               # 常见问题
│   └── troubleshooting.md   # 故障排查
└── development/             # 开发者文档
    ├── contributing.md      # 贡献指南
    ├── testing.md           # 测试指南
    └── git-workflow.md      # Git工作流规范
```

### 5.2 关键文档规范

#### 5.2.1 产品需求文档（PRD）模板

```markdown
# PRD: [功能名称]

## 版本历史
| 版本 | 日期 | 作者 | 变更说明 |
|------|------|------|----------|
| v1.2.0 | 2026-04-17 | - | SKILL.md精简(823→386行)、质量门禁文档化、Agent定义规范化 |
| v1.1.0 | 2026-04-17 | - | 新增多语言开发规范支持、参考开源项目更新 |
| v1.0.0 | 2026-04-14 | - | 初始版本，定义35个Agent角色和SDD+TDD工作流 |

## 1. 背景与目标
- 业务背景
- 用户目标
- 成功指标（KPI）

## 2. 用户故事
| ID | 角色 | 故事 | 验收标准（Given-When-Then） |
|----|------|------|------------------------------|

## 3. 功能需求
- 功能点1
- 功能点2

## 4. 非功能需求
- 性能：响应时间 < 200ms
- 安全：OWASP Top 10合规 + Agentic Top 10合规
- 可访问性：WCAG 2.1 AA

## 5. 依赖与约束
## 6. 附录（设计稿链接、数据字典）
```

#### 5.2.2 架构决策记录（ADR）模板

```markdown
# ADR: [决策标题]

## 状态
[提议中 / 已接受 / 已废弃 / 已取代]

## 上下文
描述需要做决策的背景、约束、相关目标。

## 决策
我们选择 [方案X]，因为 [理由]。

## 后果
### 正面影响
- 可维护性提升
### 负面影响
- 需要学习曲线

## 备选方案
- 方案Y（拒绝原因）
- 方案Z（拒绝原因）

## 参考资料
```

#### 5.2.3 API文档规范

- 必须符合OpenAPI 3.0规范，文件存储在 `docs/technical/api/openapi.yaml`
- 每个端点必须包含：描述、请求参数（路径/查询/请求体）、响应结构（成功/错误）、示例
- 使用工具（如Swagger UI）生成可视化文档，由 **Technical Writer** 保证与代码实现一致（通过契约测试验证）

#### 5.2.4 用户手册规范

- 必须包含：安装/配置说明、核心功能操作指南、常见问题解答、故障排查表
- 语言清晰，截图与最新UI保持一致
- 由 **Documentation Engineer** 在每次发布前更新，并通过 **Documentation Reviewer** 审核

#### 5.2.5 设计系统文档规范

- 包含：颜色（HEX/RGBA/CSS变量）、排版（字体族、字号、行高）、间距（栅格系统）、组件变体（按钮、输入框、模态框等）
- 每个组件提供：设计预览、代码示例（React/Vue）、可访问性说明
- 使用Storybook作为活文档，与代码库同步

### 5.3 文档质量门禁

| 文档类型   | 检查内容        | 通过标准                 | 负责Agent                              |
| :----- | :---------- | :------------------- | :----------------------------------- |
| PRD    | 完整性、用户故事覆盖率 | 所有功能点有对应的用户故事和验收标准   | Product Manager                      |
| ADR    | 合理性、影响分析    | 每个架构决策有明确理由和备选方案     | System Architect                     |
| API文档  | 与实现一致性      | OpenAPI与代码契约测试100%通过 | Technical Writer + Backend Developer |
| 用户手册   | 操作步骤准确性     | 关键流程可复现，无过时截图        | Documentation Engineer + QA          |
| 设计系统文档 | 设计令牌同步      | 设计令牌JSON与CSS变量diff为零 | UI Designer + Frontend Stylist       |

***

## 六、测试体系设计

### 6.1 测试金字塔

本Skill强制实施完整的测试金字塔模型，确保各层测试的合理分布：

```text
                    ┌─────────────┐
                    │  E2E Tests  │  5-10% - 关键用户旅程
                   ┌┴─────────────┴┐
                   │  Integration  │  15-25% - API契约、数据库、外部服务
                  ┌┴───────────────┴┐
                  │   Unit Tests   │  60-70% - 函数/方法/组件级别
                 └─────────────────┘
```

### 6.2 各层测试详细设计

#### 6.2.1 单元测试

| 维度         | 前端                    | 后端                       |
| :--------- | :-------------------- | :----------------------- |
| **测试框架**   | Jest / Vitest         | Pytest / JUnit / Go Test |
| **覆盖目标**   | ≥80% 语句覆盖             | ≥85% 语句覆盖                |
| **测试内容**   | 组件渲染、Hook逻辑、工具函数、状态管理 | 业务逻辑函数、数据验证、工具函数         |
| **Mock策略** | MSW Mock API、组件隔离测试   | Mock数据库层、Mock外部服务        |
| **强制场景**   | 边界条件、错误处理、空状态         | 边界值、异常处理、并发安全            |
| **自动化触发**  | 每次代码生成后自动执行           | 每次代码生成后自动执行              |

> **AI增强测试生成**：参考TestForge的迭代式测试生成方法（pass\@1率84.3%，行覆盖率44.4%，单文件成本仅$0.63），本Skill在Phase 4实施阶段支持反馈驱动的测试套件生成，通过测试执行和覆盖率报告持续优化测试质量。同时，对于遗留代码场景，可借鉴UnitTenX的多Agent形式化验证增强方法提升测试覆盖率。

#### 6.2.2 集成测试

| 维度        | 内容                                              |
| :-------- | :---------------------------------------------- |
| **测试框架**  | Supertest / Pytest-Integration / Testcontainers |
| **覆盖目标**  | ≥70% API端点覆盖                                    |
| **测试内容**  | API契约测试、数据库CRUD集成、第三方服务Mock集成、消息队列集成            |
| **数据库测试** | 使用Testcontainers启动真实数据库容器，测试Schema变更和数据一致性      |
| **契约测试**  | 前后端接口契约验证（OpenAPI规范一致性）                         |
| **自动化触发** | 代码变更后触发（CI流水线）                                  |

#### 6.2.3 端到端测试

| 维度        | 内容                         |
| :-------- | :------------------------- |
| **测试框架**  | Playwright / Cypress       |
| **测试环境**  | 完整应用栈（前端+后端+数据库）           |
| **测试内容**  | 关键用户旅程、跨页面流程、前后端数据流、浏览器兼容性 |
| **视觉测试**  | 关键页面的视觉回归测试（与设计稿对比）        |
| **自动化触发** | 每日构建 / PR合并前               |
| **重试机制**  | 自动重试Flaky测试（最多3次）          |

#### 6.2.4 安全测试

| 类别            | 测试内容                                      | 工具/方法                                          |
| :------------ | :---------------------------------------- | :--------------------------------------------- |
| **SAST**      | 代码静态安全分析                                  | 内置安全规则引擎 + Semgrep集成                           |
| **依赖扫描**      | 第三方库CVE漏洞检测                               | npm audit / pip-audit / OWASP Dependency Check |
| **注入测试**      | SQL注入、NoSQL注入、命令注入                        | 自动化攻击向量生成 + AI注入载荷构建                           |
| **XSS/CSRF**  | 跨站脚本、跨站请求伪造                               | 输出编码检查、CSRF Token验证                            |
| **认证授权**      | 认证绕过、权限提升、JWT安全                           | 边界测试、Token验证测试                                 |
| **敏感数据**      | 密钥泄露、日志脱敏、加密强度                            | 模式匹配扫描、加密算法检查                                  |
| **API安全**     | Rate Limiting、CORS配置、敏感信息暴露               | API安全基线检查                                      |
| **容器安全**      | Docker镜像漏洞、配置漂移                           | Trivy / Docker Scout                           |
| **Agentic安全** | 多Agent系统特有安全风险（OWASP Agentic Top 10 2026） | 目标劫持检测、工具滥用检测、Agent间通信加密、记忆中毒防御                |
| **AI自主渗透测试**  | 多Agent协同侦察、利用链编排、漏洞验证                     | 侦察Agent、注入Agent、权限提升Agent并行协作，Docker沙箱验证真实漏洞   |

**OWASP Agentic Top 10 2026覆盖**：本Skill的安全测试体系全面覆盖OWASP于2025年12月发布的Agentic Applications Top 10 2026十大风险，结合TrinityGuard的三层风险分类方法（单Agent漏洞、Agent间通信威胁、系统级涌现危害）和OpenAgentSafety的八大关键风险类别评估框架进行体系化设计：

| ASI编号     | 风险名称                                            | 风险描述                                                                                                                        | 本Skill测试机制                                                                     |
| :-------- | :---------------------------------------------- | :-------------------------------------------------------------------------------------------------------------------------- | :----------------------------------------------------------------------------- |
| **ASI01** | Agent Goal Hijack（目标劫持）                         | 攻击者通过提示注入、上下文污染或外部数据投毒，将隐藏指令嵌入用户输入、RAG检索结果、工具输出或Agent间通信中，使Agent在规划阶段误将恶意内容视为任务目标，从而改变整体决策方向。被劫持的目标还可能被写入长期记忆，在跨会话、跨任务中反复生效 | Security Auditor + AI Penetration Tester协同检测目标篡改；Runtime Supervisor监控Agent行为偏离 |
| **ASI02** | Tool Misuse & Exploitation（工具滥用）                | 攻击者引导Agent在合法权限范围内错误使用工具，调用不恰当API、使用错误参数或以异常顺序组合工具，造成数据泄露、资源消耗或业务破坏。支持自动执行和多工具链式调用的场景中，单次工具误用可能被迅速放大                        | 工具调用审计、API限流测试、递归调用检测；Agent-Environment交互Guardrails                            |
| **ASI03** | Identity & Privilege Abuse（身份权限滥用）              | 攻击者操纵Agent的委派关系、上下文或A2A通信，使Agent继承、缓存或冒用不应拥有的身份与权限。当Agent凭证被写入上下文或长期记忆后，权限滥用还可能跨任务、跨会话持续存在                                  | Compliance Officer权限矩阵验证、跨Agent信任链测试；SAGA访问控制令牌机制                              |
| **ASI04** | Agentic Supply Chain Vulnerabilities（供应链漏洞）     | 攻击者投毒、篡改或伪装Agent依赖的外部组件（模型、工具、插件、Prompt模板、Agent描述文件）。由于组件在运行时动态发现和加载，被污染的组件可能被多个Agent同时信任，快速扩散影响                            | 依赖扫描 + MCP服务器安全评估 + 插件来源验证；组件签名校验                                              |
| **ASI05** | Unexpected Code Execution（意外代码执行）               | 攻击者通过提示注入或上下文操纵，使Agent生成或处理的文本被直接或间接解释为可执行代码，触发非预期执行。在自动化编程、运维或自修复场景中尤为高危                                                   | 沙箱隔离测试、代码执行边界验证；SAST扫描代码注入模式                                                   |
| **ASI06** | Memory & Context Poisoning（记忆中毒）                | 攻击者将恶意数据注入Agent的持久化记忆系统、向量数据库或RAG存储中，使Agent在未来推理中被恶意数据持续影响，逐步偏离预期行为                                                         | 持久化记忆完整性校验、RAG存储安全测试；Omega Walls状态化运行时防御                                       |
| **ASI07** | Insecure Inter-Agent Communication（不安全Agent间通信） | Agent间通信缺乏强身份验证、加密或Schema验证，攻击者可实施欺骗、重放、协议降级和“中间Agent”攻击                                                                    | Agent间通信加密验证、消息签名校验、防重放测试；Maris策略防护系统                                          |
| **ASI08** | Cascading Failures（级联故障）                        | 单个被污染的记忆条目、错误规划或被攻陷应用，通过Agent依赖关系和工作流链条向外传播，将局部问题迅速演变为大规模事故                                                                 | Runtime Supervisor监控、工作流检查点恢复测试、熔断机制验证                                         |
| **ASI09** | Excessive Agency（过度自主）                          | Agent在缺乏足够约束和审批机制的情况下执行敏感操作，或在执行边界不清晰时做出超出预期的决策，源于权限范围过大或缺乏人工监督                                                             | 人工审批门禁测试、权限范围约束验证；Agent操作审计日志                                                  |
| **ASI10** | Observability & Monitoring Gaps（可观测性缺失）         | 多Agent系统运行时行为缺乏足够的监控、日志记录和审计追踪，导致安全事件无法及时检测、故障难以定位、合规性无法验证                                                                  | Monitor Specialist日志完整性检查、审计追踪验证；Agent调用成功率监控                                  |

> **OWASP参考信息**：上述十大安全风险框架基于OWASP于2025年12月发布的《OWASP Top 10 for Agentic Applications 2026》，同时与《OWASP Top 10 LLM 2025》、《OWASP Agentic AI威胁与防护框架》形成映射关系。非人类身份（Non-Human Identities, NHIs）在Agentic安全中扮演关键角色——每个有意义的Agent都依赖API密钥、服务账号、OAuth令牌等NHI，当这些NHI权限过大、不可见或暴露时，上述风险将迅速从理论变为事故。

**多Agent系统安全前沿框架补充**：

| 安全框架                         | 核心能力                                                                                                 | 对本Skill的参考价值                     |
| :--------------------------- | :--------------------------------------------------------------------------------------------------- | :------------------------------- |
| **TrinityGuard**             | 上海AI实验室开源MAS安全评估监控框架，三层20种风险分类，OWASP标准对齐，评估层+运行时监控双层防护，LLM Judge Factory统一协调                         | MAS安全架构设计参考，风险分类方法，运行时监控Agent实现  |
| **Agent Governance Toolkit** | 微软开源的AI代理运行时安全工具包，MIT许可证，首个覆盖全部10项OWASP Agentic风险的工具集，Agent OS策略引擎+Agent Mesh安全通信+Agent Runtime动态执行环 | 运行时策略拦截、多代理安全通信、执行环隔离、自动化合规验证    |
| **OpenAgentSafety**          | ICLR 2026接受框架，8类风险类别，350+多轮多用户任务，真实工具交互，Claude-Sonnet-3.7在51.2%的安全脆弱任务中出现不安全行为                       | 安全评估方法论、对抗性任务设计、真实工具交互测试         |
| **MAESTRO**                  | CSA云安全联盟发布，针对银行业等高度监管行业，最小可行控制分层模型（基础模型/数据操作/Agent框架/部署基础设施/评估可观测性/安全合规/Agent生态）                     | 分层安全控制模型、监管行业合规架构、跨层威胁建模         |
| **JoySafeter**               | 京东开源AI驱动安全编排平台，200+安全工具MCP集成，DeepAgents Manager-Worker星型拓扑，长短期记忆系统，全链路Langfuse可观测性                   | 安全工具MCP集成模式、可视化工作流编排、安全Agent记忆进化 |

**AI渗透测试Agent协作流程：**

1. **侦察Agent**：识别攻击面、端点枚举、技术栈指纹识别
2. **注入Agent**：SQLi/XSS/命令注入载荷生成与验证
3. **权限提升Agent**：认证绕过、越权漏洞测试
4. **前端漏洞Agent**：DOM XSS、CSP绕过、存储型漏洞
5. **Agentic漏洞Agent**：目标劫持、工具滥用、跨Agent权限提升测试
6. **验证Agent**：Docker沙箱内验证漏洞真实性、生成利用链报告

> **AI渗透测试前沿实践**：参考AWE（Adaptive Web Exploitation Framework）的设计理念，将结构化漏洞分析管道嵌入轻量级LLM编排层，结合上下文感知的载荷变异生成与持久化记忆，在XSS测试中达到87%成功率（较MAPTA提升30.5%），盲SQL注入成功率达66.7%（提升33.3%）。本Skill的AI Penetration Tester可借鉴该架构，在保证效率与确定性的同时提升漏洞发现能力。

**前沿AI渗透测试框架参考：**

| 框架名称              | 核心能力                                                                                               | 性能数据                                                                 | 参考价值                         |
| :---------------- | :------------------------------------------------------------------------------------------------- | :------------------------------------------------------------------- | :--------------------------- |
| **AutoPentester** | LLM Agent驱动的自动化渗透测试框架，给定目标IP后自动使用常见安全工具迭代执行渗透测试步骤，动态基于上一步工具输出生成攻击策略                                | 子任务完成率较PentestGPT提升27.0%，漏洞覆盖率提升39.5%，用户评分（3.93/5）较PentestGPT提升19.8% | 多Agent渗透测试的模块化设计、迭代攻击策略生成    |
| **xOffense**      | AI驱动的多Agent渗透测试框架，将劳动密集、专家驱动的渗透测试转变为全自动、机器可执行的工作流，核心使用微调的中型开源LLM（Qwen3-32B）驱动推理和决策                 | 支持侦察、漏洞分析、利用的多阶段协作流程                                                 | 多Agent渗透测试架构设计、轻量级LLM驱动的安全决策 |
| **RapidPen**      | 完全自动化的渗透测试框架，专注于实现初始立足点获取（IP-to-Shell）                                                             | 无需人工干预完成从目标识别到Shell获取的全流程                                            | Agent自主攻击链编排、自动化漏洞利用         |
| **VulnSage**      | 多Agent自动化漏洞利用生成框架，模拟安全研究者工作流分解为Code Analyzer/Code Generation/Validation/Reflection Agents，迭代式反馈自优化 | 漏洞利用生成较SOTA工具提升53%，已发现146个真实0-day漏洞                                  | 自动化漏洞利用生成、多Agent协作安全研究       |
| **Argusee**       | DARKNAVY多Agent协作漏洞发现架构，模拟人类安全团队分工协作机制                                                              | 在Linux USB协议栈测试中发现CVE-2025-37891高危漏洞，可root提权                         | 多Agent漏洞审计协作、精准入口点分析         |

**安全审计详细检查清单**（参考`templates/security-checklist.md`）：

- 所有数据库查询使用参数化或ORM，无字符串拼接SQL
- JWT令牌使用强密钥，合理过期时间（≤24小时），无敏感信息存储在payload中
- 密码存储使用bcrypt/argon2，不使用MD5/SHA1
- 所有用户输入在输出到HTML时进行转义，设置CSP头
- CSRF Token验证在所有状态变更请求（POST/PUT/DELETE）中启用
- API速率限制已实现（如每个用户每分钟100次）
- 敏感日志（密码、token）已脱敏
- 依赖库无已知CVE（`npm audit`或`pip-audit`通过）
- Docker镜像基于官方最小化镜像，无高危漏洞
- 错误响应不暴露堆栈信息、数据库结构等内部细节
- **（新增）Agent目标劫持防护**：Agent接收的指令来源可信验证、目标篡改检测机制
- **（新增）Agent间通信安全**：消息签名/加密、防重放机制、A2A安全最佳实践
- **（新增）工具滥用防护**：工具调用权限最小化、调用次数限制、危险操作审批门禁
- **（新增）记忆与上下文安全**：持久化记忆存储加密、RAG数据源完整性校验
- **（新增）Agentic供应链安全**：MCP服务器来源验证、Prompt模板签名校验
- **（新增）可观测性基线**：Agent行为监控指标定义、异常行为告警规则

> **多Agent系统安全研究前沿**：学术研究揭示了多Agent系统特有的安全风险——SafeAgents框架系统化暴露了设计选择（计划构建策略、Agent间上下文共享、回退行为）对对抗性提示的敏感度；IMBIA攻击研究显示编码和测试阶段被攻陷的Agent风险最大；FCV-Attack研究揭示功能正确但存在漏洞的补丁（FCV patches）威胁，跨12种Agent-模型组合评估，仅需黑盒访问和单次查询即可攻击。多Agent代码注入攻击分析表明，coder-reviewer-tester架构比coder和coder-tester架构更具韧性，但代码编写效率较低；添加安全分析Agent可在不牺牲效率的前提下提升韧性。本Skill的安全层角色设计（Security Auditor + AI Penetration Tester + Compliance Officer）和安全门禁体系正是对这一研究结论的工程化实现。

**前沿Agentic安全框架参考：**

| 安全框架                  | 核心能力                                                                                                                   | 与本Skill集成方式                                                             |
| :-------------------- | :--------------------------------------------------------------------------------------------------------------------- | :---------------------------------------------------------------------- |
| **Maris（AG2内置）**      | 细粒度策略引导的安全防护系统，控制Agent间通信和Agent-环境交互（工具、LLM、用户），支持策略类型包括Agent间信息流控制和Agent-环境交互控制。内置Guardrails自动选择和配置检测机制（正则或LLM-based） | 可集成到Security Auditor职责中，为Agent间通信安全提供框架级实现；作为Runtime Supervisor的运行时防护组件 |
| **SAFEFLOW**          | 协议级安全框架，强制执行细粒度信息流控制（IFC），精确追踪数据来源、完整性和机密性，引入事务执行、冲突解决和回滚机制，包含预写日志、回滚和安全缓存等机制                                          | 为Runtime Supervisor提供状态管理安全基础，支持故障回滚和策略违规恢复；增强数据完整性和机密性追踪               |
| **SAGA**              | 可扩展的Agentic系统治理安全架构，提供用户对Agent生命周期的监督，引入加密机制派生访问控制令牌，对Agent间交互提供细粒度控制和形式化安全保障                                          | 为Compliance Officer提供治理框架参考，支持跨Agent权限控制；提供形式化安全保证基础                    |
| **Project CodeGuard** | Cisco开源的模型无关安全框架，将secure-by-default规则嵌入规划→生成→审查三阶段，社区驱动规则库，支持Cursor/Windsurf/Copilot/Claude Code等主流AI编码平台              | 安全编码规则集成到Code Reviewer职责，AI代码生成前/中/后全流程安全保护                             |

#### 6.2.5 性能测试

| 维度        | 内容                                   |
| :-------- | :----------------------------------- |
| **测试框架**  | k6 / Artillery                       |
| **测试类型**  | 负载测试、压力测试、耐久测试、峰值测试                  |
| **测试指标**  | 响应时间（P50/P95/P99）、吞吐量（RPS）、错误率、资源使用率 |
| **基准建立**  | 每次主要功能发布前建立性能基准                      |
| **自动化触发** | 可选手动触发或版本发布前触发                       |

### 6.3 自动化测试流水线

```text
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          自动化测试流水线                                          │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐  │
│  │ 代码提交 │───▶│ 单元测试 │───▶│ 集成测试 │───▶│ E2E测试  │───▶│ 安全扫描 │  │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘  │
│       │              │               │               │               │          │
│       ▼              ▼               ▼               ▼               ▼          │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                        质量门禁（Quality Gates）                           │   │
│  │  ✓ 单元测试通过率 100%    ✓ 集成测试通过率 100%    ✓ E2E通过率 >95%        │   │
│  │  ✓ 代码覆盖率 ≥80%        ✓ 无P0/P1安全问题        ✓ 性能指标未退化       │   │
│  │  ✓ AI渗透测试无高危漏洞   ✓ 依赖漏洞无严重CVE       ✓ 视觉差异<0.1%       │   │
│  │  ✓ Agentic Top 10合规     ✓ 可访问性无A级违规        ✓ 文档覆盖率100%      │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                       │                                         │
│                                       ▼                                         │
│                    ┌──────────────────────────────────┐                         │
│                    │  通过 → 继续 / 失败 → 自动修复循环  │                         │
│                    └──────────────────────────────────┘                         │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 6.4 CI/CD集成示例（GitHub Actions）

以下示例配置应放置在 `.github/workflows/ci.yml`，由 **CI/CD Specialist** Agent 负责维护：

```yaml
name: CI Pipeline

on:
  pull_request:
    branches: [ develop, master ]
  push:
    branches: [ develop ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: npm ci
      - run: npm run test:unit
      - run: npm run test:integration
      - run: npm run test:e2e
      - name: Security Scan
        run: npm audit --production
      - name: Visual Regression
        run: npm run test:visual
      - name: Accessibility Check
        run: npm run test:a11y
      - name: Agentic Security Scan
        run: npm run test:agentic-security
      - name: Coverage Check
        run: npm run coverage -- --threshold 80
```

***

## 七、多Agent协作与通信

### 7.1 协作模式

| 模式                  | 说明                     | 适用场景       |
| :------------------ | :--------------------- | :--------- |
| **Auto Mode**       | 自动分析任务，选择最优Agent组合并行执行 | 通用任务（默认模式） |
| **Review Mode**     | 多Agent交叉审查代码           | PR审查、质量检查  |
| **Challenge Mode**  | 对抗性辩论，多Agent从不同角度论证    | 架构决策、技术选型  |
| **Consult Mode**    | 指定特定Agent专家进行咨询        | 深度专业问题     |
| **Sequential Mode** | 串行执行，Agent按序处理         | 强依赖任务链     |
| **Parallel Mode**   | 并行执行多个独立任务             | 前后端分离开发    |
| **Hivecoding Mode** | 多模型多Agent并行编码，择优合并     | 探索性功能、方案比选 |

### 7.2 任务路由机制

| 任务类型    | 主Agent                              | 辅助Agent                                         |
| :------ | :---------------------------------- | :---------------------------------------------- |
| 新功能开发   | System Architect + Frontend/Backend | Test Architect + Code Reviewer + UI/UX Designer |
| Bug修复   | Debugger（Backend/Frontend）          | Unit Tester                                     |
| 代码审查    | Code Reviewer                       | Security Auditor                                |
| 架构设计    | System Architect                    | Product Manager                                 |
| 性能优化    | Performance Tester                  | Refactoring Specialist                          |
| 安全审计    | Security Auditor                    | AI Penetration Tester                           |
| 文档生成    | Technical Writer                    | System Architect, Documentation Engineer        |
| 数据库变更   | Data Modeler + DBA                  | Backend Developer                               |
| UI/UX设计 | UI Designer + UX Designer           | Frontend Stylist, Product Manager               |

### 7.3 Agent通信协议

本Skill内部Agent通信采用标准化消息格式，同时兼容业界标准Agent通信协议：

- **A2A (Agent-to-Agent)** ：用于跨框架、跨运行时Agent互操作。2025年4月由Google引入，支持Agent之间互相发现能力，实现安全、结构化的通信与任务委派。
- **MCP (Model Context Protocol)** ：用于Agent与工具、数据源的标准连接。被喻为“AI Agent的USB-C端口”，通过客户端-服务器架构将LLM与外部系统连接，已在Cursor、VS Code、JetBrains等主流IDE中得到广泛支持。

> **A2A vs MCP定位差异**：MCP作为“通用适配器”，连接AI Agent与工具、API和数据源，解决上下文获取和数据连通性问题；A2A则是“协调层”，为自主AI Agent之间的通信与委派建立安全、结构化的标准。两者互为补充，共同构建Agentic AI的协议基础设施。Microsoft Agent Framework RC已原生支持A2A、AG-UI和MCP三种互操作标准。

```yaml
# Agent间通信消息格式（内部协议，可映射至A2A/MCP）
message:
  id: "uuid-v4"
  type: "request" | "response" | "broadcast" | "error"
  from: "agent-name"
  to: "agent-name" | "broadcast"
  timestamp: "ISO-8601"
  protocol: "internal" | "a2a" | "mcp"
  payload:
    task_id: "task-uuid"
    action: "analyze" | "generate" | "review" | "fix"
    context:
      files: ["path1", "path2"]
      spec_ref: "rfc-xxx"
      test_cases: ["TC001", "TC002"]
    data: {}
  signature: "agent-signature"
```

### 7.4 会话管理与上下文

| 能力          | 说明                                                                                                 |
| :---------- | :------------------------------------------------------------------------------------------------- |
| **上下文继承**   | Sub Agent继承主会话记忆，但拥有独立技能包                                                                          |
| **上下文压缩**   | 长对话分层摘要 + 关键Token保留，精度损失<2%（实现参考 `scripts/context-compressor.py`，使用递归摘要或关键句提取）                     |
| **持久化记忆**   | 错误模式存储、成功模式学习、跨会话知识复用。参考@hivehub/rulebook的持久化记忆架构——上下文跨AI会话存活，BM25+HNSW混合搜索，原生SQLite+WASM fallback |
| **会话隔离**    | 并行Agent拥有独立上下文，互不干扰                                                                                |
| **A2A互操作**  | 支持通过A2A协议与外部Agent系统协作                                                                              |
| **MCP工具连接** | 通过MCP协议标准化接入外部工具、数据源、API。@hivehub/rulebook已集成40个MCP工具覆盖任务管理、Skills、记忆、决策、知识、学习等领域                  |
| **检查点/恢复**  | 参考Dapr Agents工作流持久化，支持Agent状态检查点与故障恢复                                                              |

***

## 八、技术规格

### 8.1 Skill目录结构

```text
.claude/skills/multi-agent-sdd-tdd-orchestrator/
│
├── SKILL.md                          # Skill主文件（元数据 + 渐进式披露第一层）
│
├── agents/                           # Agent定义（35个）
│   ├── orchestrator/
│   │   └── AGENT.md
│   ├── product/
│   │   ├── product-manager.md
│   │   ├── system-architect.md
│   │   └── technical-writer.md
│   ├── design/
│   │   ├── ui-designer.md
│   │   ├── ux-designer.md
│   │   └── frontend-stylist.md
│   ├── engineering/
│   │   ├── frontend-developer.md
│   │   ├── backend-developer.md
│   │   ├── fullstack-engineer.md
│   │   ├── database-engineer.md
│   │   ├── mobile-developer.md
│   │   └── devops-engineer.md
│   ├── database/
│   │   ├── data-modeler.md
│   │   ├── dba.md
│   │   └── data-seeder.md
│   ├── testing/
│   │   ├── test-architect.md
│   │   ├── unit-tester.md
│   │   ├── integration-tester.md
│   │   ├── e2e-tester.md
│   │   ├── performance-tester.md
│   │   ├── security-tester.md
│   │   ├── ai-penetration-tester.md
│   │   └── test-maintainer.md
│   ├── security/
│   │   ├── security-auditor.md
│   │   ├── penetration-tester.md
│   │   └── compliance-officer.md
│   ├── devops/
│   │   ├── cicd-specialist.md
│   │   ├── monitor-specialist.md
│   │   └── runtime-supervisor.md
│   ├── quality/
│   │   ├── code-reviewer.md
│   │   ├── refactoring-specialist.md
│   │   └── doc-reviewer.md
│   └── documentation/
│       ├── documentation-engineer.md
│       └── specification-keeper.md
│
├── commands/                         # 用户可调用的命令
│   ├── /sprint.md
│   ├── /clarify.md
│   ├── /plan.md
│   ├── /spec.md
│   ├── /design.md
│   ├── /implement.md
│   ├── /test.md
│   ├── /review.md
│   ├── /fix.md
│   ├── /accept.md
│   ├── /deploy.md
│   ├── /agent-status.md
│   └── /learn.md
│
├── workflows/                        # 工作流定义
│   ├── sdd-tdd-full.md
│   ├── sdd-tdd-fast.md
│   ├── ui-ux-workflow.md
│   ├── security-audit.md
│   ├── ai-pentest.md
│   ├── performance-test.md
│   ├── acceptance.md
│   └── bug-fix.md
│
├── templates/                        # 模板文件
│   ├── rfc-template.md
│   ├── adr-template.md
│   ├── test-plan-template.md
│   ├── user-story-template.md
│   ├── api-contract-template.yaml
│   ├── security-checklist.md
│   ├── design-system-template.md
│   ├── design-tokens.json
│   ├── usability-test-plan.md
│   ├── accessibility-checklist.md
│   ├── prd-template.md
│   └── user-manual-template.md
│
├── scripts/                          # 辅助脚本
│   ├── coverage-check.py
│   ├── dependency-scan.py
│   ├── db-migration-validator.py
│   ├── api-contract-validator.py
│   ├── performance-benchmark.js
│   ├── test-reporter.py
│   ├── pattern-learner.py
│   ├── context-compressor.py
│   ├── design-tokens-sync.js
│   ├── visual-regression.js
│   └── accessibility-test.js
│
├── references/                       # 参考文档
│   ├── coding-standards.md
│   ├── test-guidelines.md
│   ├── security-guidelines.md
│   ├── database-guidelines.md
│   ├── owasp-top10-2026.md
│   ├── owasp-agentic-top10-2026.md
│   ├── karpathy-guidelines.md
│   ├── a2a-protocol.md
│   ├── mcp-protocol.md
│   ├── git-workflow.md
│   ├── ci-cd-integration.md
│   ├── design-guidelines.md
│   ├── documentation-standards.md
│   └── acceptance-criteria.md
│
└── memory/                           # 持久化记忆（自动生成）
    ├── patterns/
    ├── errors/
    ├── fixes/
    └── metrics/
```

### 8.2 渐进式披露设计

遵循Anthropic Agent Skills的三层渐进式披露设计：

| 层级           | 内容                                  | 加载时机        | 上下文占用   |
| :----------- | :---------------------------------- | :---------- | :------ |
| **第一层：元数据**  | YAML frontmatter（name, description） | Skill启动时预加载 | 极小      |
| **第二层：主体内容** | SKILL.md完整指令、工作流描述                  | 任务相关时按需加载   | 中等      |
| **第三层：附加资源** | 脚本、模板、参考文档                          | 特定场景需要时才加载  | 仅执行/读取时 |

### 8.3 质量门禁定义

| 门禁名称                  | 检查内容        | 通过标准                     | 阻塞级别                |
| :-------------------- | :---------- | :----------------------- | :------------------ |
| **SPEC-CONSISTENCY**  | 规格与实现一致性    | 100%一致                   | BLOCK               |
| **TEST-PASS**         | 测试通过率       | 100%                     | BLOCK               |
| **COVERAGE**          | 代码覆盖率       | ≥80%（单元），≥70%（集成）        | WARN/BLOCK          |
| **SECURITY**          | 安全漏洞扫描      | 无P0/P1漏洞                 | BLOCK               |
| **AGENTIC-SECURITY**  | Agentic安全合规 | 通过OWASP Agentic Top 10检查 | BLOCK               |
| **AI-PENTEST**        | AI渗透测试      | 无高危可利用漏洞                 | BLOCK               |
| **PERFORMANCE**       | 性能基准        | 未退化>10%                  | WARN                |
| **LINT**              | 代码规范检查      | 0错误                      | BLOCK               |
| **DOCUMENTATION**     | API文档一致性    | OpenAPI与实现一致             | WARN                |
| **CONTRACT**          | 接口契约验证      | 前后端契约一致                  | BLOCK               |
| **VISUAL-REGRESSION** | 视觉回归测试      | 差异像素 < 0.1%              | WARN/BLOCK          |
| **ACCESSIBILITY**     | 可访问性        | 无A级违规                    | BLOCK               |
| **UAT**               | 用户验收测试      | 所有验收场景通过                 | BLOCK               |
| **DOC-COMPLETENESS**  | 文档完整性       | 关键文档覆盖率100%              | BLOCK               |
| **FILE-ENCODING**     | 文件编码格式      | 所有文件为UTF-8 without BOM   | BLOCK               |
| **COMMENT-LANGUAGE**  | 注释语言规范      | 业务注释包含中文说明               | WARN（初期）/BLOCK（稳定期） |

### 8.4 编码与注释规范（新增）

为确保跨平台协作的一致性、可维护性与多Agent间的语义理解准确度，本Skill强制实施以下基础编码约束：

#### 8.4.1 文件编码规范

| 规范项          | 强制要求                    | 适用范围                                  | 验证方式                          |
| :----------- | :---------------------- | :------------------------------------ | :---------------------------- |
| **编码格式**     | **UTF-8 without BOM**   | 所有源代码文件、配置文件、Markdown文档、JSON/YAML数据文件 | 在CI流水线中通过 `file` 命令或编码检测脚本校验  |
| **行尾序列**     | LF (`\n`)               | 所有文本文件                                | Git `core.autocrlf` 配置 + CI检查 |
| **文件末尾空行**   | 文件应以一个空行结束              | 所有文本文件                                | EditorConfig / Prettier配置     |
| **禁止字节顺序标记** | 文件开头不得出现 BOM (`U+FEFF`) | 所有UTF-8文件                             | CI脚本扫描前3字节是否为 `EF BB BF`      |

> **设计意图**：UTF-8 without BOM 是Linux/macOS/Windows跨平台开发的事实标准，可避免因BOM导致的编译错误（如Python解释器、Shell脚本shebang行）、前端资源解析异常、以及Git diff中的不可见字符干扰。多Agent并行开发环境下，不同Agent可能在不同操作系统模拟环境中运行，统一编码可消除大量隐形故障。

#### 8.4.2 注释语言规范

| 规范项         | 强制要求                                                             | 适用范围               | 例外情况                    |
| :---------- | :--------------------------------------------------------------- | :----------------- | :---------------------- |
| **注释语言**    | **必须使用简体中文**撰写所有代码注释、文档字符串（docstring）、函数说明块                      | 业务逻辑注释、模块说明、复杂算法解释 | 第三方库原样引入的代码、自动生成的代码注释框架 |
| **英文术语处理**  | 技术术语（如 `JWT`、`DTO`、`Redis`）可直接使用英文，但解释性语句须用中文                    | 所有注释               | —                       |
| **API文档注释** | 公开API的文档注释（如JSDoc、Python docstring）建议中英双语（中文描述 + 英文参数名）          | 面向外部调用的接口          | 纯内部工具函数可仅用中文            |
| **提交信息**    | Git commit message 遵循约定式提交规范，**主体内容须使用中文**描述变更意图（type和scope仍用英文） | 所有Git提交            | —                       |

> **设计意图**：
>
> - **降低认知负担**：多Agent系统中的AI模型在理解中文注释时，可更精准地捕捉业务语义，减少因英文表述歧义导致的误解。
> - **团队协作友好**：中文注释便于人类开发者（尤其非英语母语团队）快速理解代码意图，符合国内多数项目的实际实践。
> - **与Karpathy Guidelines协同**：“Think Before Coding”准则要求Agent在编码前澄清歧义，而中文注释本身就是一种对代码意图的显式陈述。当注释必须用中文写出时，Agent被迫用更具体的语言描述“为什么这样做”，从而暴露潜在的逻辑漏洞。

#### 8.4.3 自动化校验配置

为确保上述规范被所有Agent自动遵守，在CI流水线和本地开发环境中强制启用以下工具链：

**EditorConfig 配置（`.editorconfig`）：**

```ini
root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true

[*.{py,js,ts,jsx,tsx,vue,go,java,kt,rs}]
charset = utf-8
indent_style = space
indent_size = 2
```

**CI 编码检查脚本（`scripts/check-encoding.sh`）：**

```bash
#!/bin/bash
# 检查所有文本文件是否为 UTF-8 without BOM
find . -type f \( -name "*.py" -o -name "*.js" -o -name "*.ts" -o -name "*.md" -o -name "*.json" -o -name "*.yaml" -o -name "*.yml" \) -print0 | while IFS= read -r -d '' file; do
    encoding=$(file -b --mime-encoding "$file")
    if [[ "$encoding" != "utf-8" && "$encoding" != "us-ascii" ]]; then
        echo "ERROR: $file is not UTF-8 (detected: $encoding)"
        exit 1
    fi
    # 检查BOM
    if [[ $(head -c 3 "$file" | xxd -p) == "efbbbf" ]]; then
        echo "ERROR: $file contains BOM"
        exit 1
    fi
done
```

**注释中文检测（`scripts/check-comment-lang.py`）：**

```python
import re
import sys

# 简化版检测：检查关键注释块是否包含中文
# 实际集成时可使用AST解析器针对性检查 docstring 和行注释
pattern_chinese = re.compile(r'[\u4e00-\u9fff]')
required_files = sys.argv[1:]

for filepath in required_files:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        # 如果文件中有注释但无中文字符，发出警告
        if '//' in content or '/*' in content or '#' in content:
            if not pattern_chinese.search(content):
                print(f"WARNING: {filepath} contains comments but no Chinese characters detected.")
```

**规范覆盖范围总结：**

- 所有新生成或修改的源代码文件必须符合 **UTF-8 without BOM** 编码。
- 所有Agent（包括Code Reviewer）在审查时必须检查注释是否包含中文说明（针对业务逻辑部分）。
- 违反编码规范的门禁级别为 **BLOCK**（阻止合并）。

***

## 九、Git分支管理规范

为确保多Agent协作开发过程的代码一致性、可追溯性和发布可靠性，本Skill强制实施标准化的Git分支管理策略。所有Agent在执行代码生成、修改、合并等操作时，必须遵循以下规范。

### 9.1 分支模型总览

采用基于 `master` / `develop` / `feature` / `hotfix` 的分支管理模型，核心原则：

- **master**：生产环境代码，始终保持可发布状态。所有发布基于 `master` 分支的Tag。
- **develop**：主开发分支，集成所有已完成的功能和修复。测试环境部署基于此分支。
- **feature/**\*：功能开发分支，从 `develop` 拉出，完成后合并回 `develop`。
- **hotfix/**\*：紧急修复分支，从 `master` 拉出，修复后同时合并回 `master` 和 `develop`。

> **可选扩展**：对于需要冻结功能的发布周期，可增加 `release/*` 分支，从 `develop` 拉出，完成最终测试和版本号调整后再合并到 `master`。本Skill默认支持直接合并模式，但也兼容 `release` 分支流程。

### 9.2 分支操作详细流程

#### 9.2.1 开发新功能 (Feature)

**适用场景**：新增功能、非紧急Bug修复（非生产环境）、重构等。

**流程步骤**：

1. **拉取功能分支**
   从最新的 `develop` 分支创建 `feature/<功能描述>` 分支（例如 `feature/user-login`）。
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/user-login
   ```
2. **开发与自测**
   在功能分支上进行代码开发，并执行单元测试、集成测试等自测验证。
3. **提交代码**
   遵循约定式提交规范（见9.3），提交代码到功能分支。
4. **发起Pull Request (PR)**
   将功能分支合并回 `develop`，要求：
   - PR标题和描述清晰说明变更内容。
   - 必须通过CI流水线（单元测试、集成测试、代码覆盖率、安全扫描、视觉回归等）。
   - 至少一名Code Reviewer（可指定`Code Reviewer` Agent）批准。
5. **合并到develop**
   PR通过后，合并至 `develop` 分支。
6. **集成测试**
   在 `develop` 分支上进行完整集成测试，确保与其它功能兼容。
7. **发版前同步master**
   在准备发布前，将 `master` 分支的最新代码（包含所有已发布的热修复）合并到 `develop`，解决可能的冲突：
   ```bash
   git checkout develop
   git pull origin master
   ```
8. **发布到生产**
   集成测试通过后，将 `develop` 合并到 `master`，并在 `master` 上打Tag发布。

```text
develop ──────────●─────────────────────────●─────────────▶
                  │                         │
                  └─ feature/login ─────────┘
                                    │
                                    ▼
                              Pull Request
                                    │
                                    ▼
                              merge to develop
```

#### 9.2.2 修复生产环境紧急Bug (Hotfix)

**适用场景**：生产环境出现严重缺陷，需立即修复。

**流程步骤**：

1. **从master拉取热修复分支**
   从当前生产版本对应的 `master` 分支创建 `hotfix/<修复描述>` 分支。
   ```bash
   git checkout master
   git pull origin master
   git checkout -b hotfix/login-error
   ```
2. **修复与测试**
   在热修复分支上完成Bug修复，并进行充分测试（单元测试、冒烟测试）。
3. **发起PR合并到master**
   提交PR将 `hotfix` 分支合并到 `master`。要求：
   - 通过CI流水线（包括安全快速扫描）。
   - 代码审查通过。
4. **打Tag发版**
   合并后，在 `master` 分支上打新的版本Tag（如 `v1.2.1`），基于Tag部署到生产环境。
5. **立即同步到develop**
   **关键步骤**：必须立即将热修复内容合并回 `develop` 分支，防止后续开发覆盖修复。
   ```bash
   git checkout develop
   git pull origin develop
   git merge master   # 或直接 cherry-pick hotfix 提交
   git push origin develop
   ```

```text
master ──────●───────────────●─────────────────▶
             │               │
             └─ hotfix ──────┘
                    │
                    ▼ (同步)
develop ────────────●─────────────────────────▶
```

#### 9.2.3 发布新版本 (Release)

**适用场景**：功能开发完成，集成测试通过，需要发布正式版本。

**流程**：

1. 确保 `develop` 分支已包含所有待发布功能和热修复。
2. 将 `develop` 合并到 `master`：
   ```bash
   git checkout master
   git pull origin master
   git merge develop --no-ff
   git push origin master
   ```
3. 在 `master` 分支上打Tag（遵循语义化版本）：
   ```bash
   git tag -a v1.3.0 -m "Release version 1.3.0"
   git push origin v1.3.0
   ```
4. 基于Tag进行生产环境部署。

> **重要**：Tag是唯一的发布依据。禁止直接基于分支发版，Tag保证了版本的可复现性。

#### 9.2.4 紧急回滚流程

若生产环境发布后发现严重问题（如P0级安全漏洞、核心功能不可用），立即执行回滚：

1. **识别上一个稳定Tag**：`git tag --sort=-v:refname | head -n 1` 获取最新Tag，选择前一个Tag。
2. **重新部署上一个Tag**：基于上一个Tag（如 `v1.2.0`）触发部署流水线。
3. **创建修复分支**：从 `master` 拉取 `hotfix/rollback-issue` 分支，分析问题并修复。
4. **修复后按标准Hotfix流程发布**：合并回 `master` 并打新Tag（如 `v1.3.1`），同步到 `develop`。

### 9.3 提交信息规范

所有Agent生成的提交必须遵循[约定式提交](https://www.conventionalcommits.org/)规范，格式如下：

```
<type>(<scope>): <subject>

[optional body]

[optional footer]
```

**type类型**：

| 类型         | 说明                |
| :--------- | :---------------- |
| `feat`     | 新功能               |
| `fix`      | Bug修复             |
| `docs`     | 文档变更              |
| `style`    | 代码格式（不影响逻辑）       |
| `refactor` | 重构（非新功能、非修复）      |
| `perf`     | 性能优化              |
| `test`     | 测试相关              |
| `chore`    | 构建/工具链变更          |
| `revert`   | 回滚提交              |
| `design`   | 设计变更（设计令牌、UI组件结构） |
| `security` | 安全相关变更（漏洞修复、安全加固） |

**示例**：

```
feat(backend): add user authentication API

- Implement JWT token generation
- Add login and refresh endpoints
- Include unit tests for auth service

Closes #123
```

### 9.4 分支保护与质量门禁

| 分支        | 保护规则                                                                                              |
| :-------- | :------------------------------------------------------------------------------------------------ |
| `master`  | - 禁止直接推送- 必须通过PR合并- PR必须通过所有CI检查（测试、安全、覆盖率、视觉回归、可访问性、Agentic安全）- 必须至少1人（或`Code Reviewer` Agent）批准 |
| `develop` | - 禁止直接推送- 必须通过PR合并- PR必须通过单元测试和集成测试- 覆盖率不得低于阈值                                                    |

### 9.5 与多Agent工作流的集成

本Skill的Agent在执行开发任务时，自动遵循上述Git规范：

| Agent/阶段                 | Git操作责任                                                   |
| :----------------------- | :-------------------------------------------------------- |
| **Orchestrator**         | 在任务开始时确定分支策略，指导Agent创建正确的分支类型                             |
| **Frontend/Backend Dev** | 在功能分支上提交代码，确保提交信息符合约定式规范                                  |
| **UI Designer**          | 设计令牌变更提交到 `feature/*` 分支，PR中包含设计截图对比                      |
| **Code Reviewer**        | 在PR审查时检查分支命名、提交信息规范，以及变更范围是否符合Surgical Changes原则          |
| **CI/CD Specialist**     | 配置流水线强制分支保护规则和质量门禁                                        |
| **Runtime Supervisor**   | 监控PR合并状态，触发后续集成测试                                         |
| **Release流程**            | `System Architect` 或 `DevOps Engineer` 负责执行合并到master及打Tag |

> **Git Worktree并行开发增强**：参考Worktrunk工具的设计理念，本Skill支持Git worktree并行开发模式。每个Agent可以在独立的工作目录中操作自己的分支，互不干扰。Worktrunk提供了简洁的CLI界面（如`wt switch`、`wt list`、`wt merge`）来管理worktree生命周期，并可集成LLM自动生成提交信息。同时，AgentGit框架进一步将Git式的版本控制（commit/revert/branch）引入多Agent系统工作流，支持状态回滚、分支探索与多轨迹并行比较，显著提升多Agent系统的可靠性与可扩展性。

**Git Worktree并行开发工具：**

| 工具            | 核心能力                                                                                   | 使用示例                           |
| :------------ | :------------------------------------------------------------------------------------- | :----------------------------- |
| **git-stint** | 为AI Agent并行开发设计，每个Agent拥有独立分支、独立工作树和独立生命周期，自动处理分支创建、跟踪、检查点和清理                          | `git stint start feature-name` |
| **worktrunk** | Git worktree CLI管理工具，三条核心命令（wt switch/wt list/wt merge）简化worktree生命周期管理，专为并行AI Agent设计 | `wt switch feature/branch`     |
| **wt**        | 轻量级CLI工具，在独立Git worktree中并行运行多个AI Agent，处理worktree创建和关联分支                              | `wt start --branch feature-1`  |

> **最佳实践**：CodeBuddy Code等AI编码平台支持自动为并行子Agent创建独立worktree，避免文件冲突。

***

## 十、故障处理与降级策略

为确保系统健壮性，定义常见故障模式及处理策略如下：

| 故障场景                | 检测方式                                  | 处理策略                                                         | 是否阻塞流程  |
| :------------------ | :------------------------------------ | :----------------------------------------------------------- | :------ |
| **单个Agent超时（>30秒）** | 内置超时计时器                               | 重试2次（指数退避）；若仍失败，记录错误并使用其他Agent结果（如有）                         | 否（降级）   |
| **质量门禁失败（非BLOCK级）** | 门禁检查器                                 | 记录警告，继续执行，但最终报告标记需人工复核                                       | 否（WARN） |
| **质量门禁失败（BLOCK级）**  | 门禁检查器                                 | 立即停止流水线，触发Iteration Phase，调用`Refactoring Specialist`修复       | 是       |
| **安全扫描发现P0/P1漏洞**   | Security Auditor + 依赖扫描               | 阻断合并，自动创建hotfix分支，指派`Security Auditor`和`Backend Developer`修复 | 是       |
| **Agentic安全门禁失败**   | Security Auditor + Agentic扫描          | 阻断发布，生成Agentic漏洞报告，强制进入安全审计流程                                | 是       |
| **AI渗透测试发现高危漏洞**    | AI Penetration Tester                 | 阻断发布，生成漏洞报告，强制进入安全审计流程                                       | 是       |
| **视觉回归失败（差异>阈值）**   | 视觉回归脚本                                | 阻断合并，自动生成差异图，要求`UI Designer`或`Frontend Developer`修复          | 是       |
| **可访问性违规**          | accessibility-test.js                 | 阻断合并，提供违规详情和修复建议                                             | 是       |
| **设计令牌不同步**         | design-tokens-sync.js                 | 阻断合并，自动同步或提示人工修复                                             | 是       |
| **CI/CD流水线执行失败**    | 流水线状态监控                               | 自动重试1次；若仍失败，通知`CI/CD Specialist` Agent介入                     | 是（人工）   |
| **Agent间通信丢失**      | 心跳检测（每5秒）                             | 尝试重新建立连接；若连续3次失败，使用本地缓存结果并降级                                 | 否       |
| **上下文窗口溢出**         | Token计数                               | 触发上下文压缩（`context-compressor.py`），压缩后若仍溢出则分段处理                | 否       |
| **工作流检查点恢复**        | 持久化存储状态                               | 从上一个检查点恢复，继续执行                                               | 否       |
| **生产环境发布后需紧急回滚**    | 监控告警 / 人工触发                           | 执行9.2.4回滚流程，部署上一个稳定Tag                                       | 是       |
| **Agent目标劫持检测**     | Runtime Supervisor + Security Auditor | 分析Agent行为异常，若目标偏离>阈值则冻结Agent并告警                              | 是（紧急）   |
| **增量实施死循环**         | 3次尝试失败计数器（@hivehub/rulebook增量实施规范）    | 停止执行，记录反模式到`.rulebook/knowledge/anti-patterns/`，从头重新开始       | 是（流程阻断） |

***

## 十一、非功能性需求

### 11.1 性能需求

| 指标        | 目标值             | 测试方法   |
| :-------- | :-------------- | :----- |
| Skill加载时间 | < 2秒            | 冷启动计时  |
| Agent并行数  | 支持≥10个Agent同时运行 | 压力测试   |
| 上下文压缩比    | >90%（精度损失<2%）   | 长对话测试  |
| 测试执行时间    | 单元测试<30秒        | CI计时   |
| 模式学习延迟    | < 5秒            | 同步存储计时 |
| 视觉回归对比时间  | < 30秒（100张截图）   | 脚本计时   |

### 11.2 可靠性需求

| 指标          | 目标值               |
| :---------- | :---------------- |
| Agent故障自动恢复 | 支持，静默降级（见第十章）     |
| 任务失败重试      | 最多3次，指数退避         |
| 部分Agent失败处理 | 使用可用结果继续，标注限制     |
| 会话断点续传      | 支持                |
| 工作流检查点/恢复   | 支持持久化状态，故障后从检查点恢复 |

### 11.3 兼容性需求

| 平台               | 兼容性                          |
| :--------------- | :--------------------------- |
| Claude Code      | 原生支持（Anthropic Skills 2.0兼容） |
| Trae             | 通过转换适配器支持                    |
| Cursor           | 转换为.mdc规则格式                  |
| Windsurf         | 转换为配置格式                      |
| Antigravity      | 通过集成适配器支持                    |
| GitHub Copilot   | 通过Agent定义转换支持                |
| A2A兼容            | 支持与A2A协议Agent互操作             |
| MCP兼容            | 支持MCP工具/数据源连接                |
| Figma/Penpot API | 设计导入与令牌同步                    |

### 11.4 安全性需求

| 需求项       | 说明                              |
| :-------- | :------------------------------ |
| 敏感数据保护    | 不在日志/输出中暴露密钥、密码                 |
| 权限控制      | Agent操作限于项目目录范围                 |
| 审计追踪      | 所有Agent操作留痕                     |
| 输入验证      | 用户输入安全校验                        |
| Agentic安全 | 遵循OWASP Agentic Top 10 2026最佳实践 |

### 11.5 可观测性需求

| 指标            | 采集方式                        | 用途            |
| :------------ | :-------------------------- | :------------ |
| 首次通过率（无人工干预）  | PR合并记录 / 测试执行日志             | 衡量自动化成熟度      |
| 平均修复时间（MTTR）  | 从发现问题到Hotfix发布的时间戳差         | 评估应急响应能力      |
| 代码审查时间减少比例    | 人工审查时间（对比非Skill项目）          | 验证效率提升        |
| 安全漏洞发现率       | 安全扫描报告中的漏洞数 / 总漏洞预估         | 评估安全测试覆盖      |
| Agentic安全事件数  | Agentic安全扫描 + 运行时异常检测       | 衡量Agentic安全水位 |
| 设计到代码一致性      | 视觉差异报告                      | 衡量UI/UX自动化质量  |
| 文档覆盖率         | `documentation-coverage` 脚本 | 门禁依据          |
| Agent调用成功率    | 每次Agent调用成功/失败计数            | 健康度监控         |
| Karpathy准则合规率 | Code Reviewer人工抽样 + 自动化检测   | 评估代码质量一致性     |
| Agent间通信延迟    | A2A消息时间戳差值                  | 评估协作效率        |

***

## 十二、实施路线图

### 12.1 阶段规划

| 阶段                  | 时间      | 交付物                                                                              |
| :------------------ | :------ | :------------------------------------------------------------------------------- |
| **Phase 1: 核心框架**   | 第1-2周   | SKILL.md核心、Orchestrator、3个核心Agent、基础工作流、Karpathy Guidelines集成                    |
| **Phase 2: 完整角色体系** | 第3-4周   | 35个Agent完整定义（含设计层、文档层、Karpathy行为准则）、角色模板、通信协议（含A2A/MCP适配）                        |
| **Phase 3: 工作流完善**  | 第5-6周   | 完整7阶段SDD+TDD工作流（含UI/UX、验收、Karpathy准则嵌入、增量实施规范）、所有命令实现                            |
| **Phase 4: 测试体系**   | 第7-8周   | 单元/集成/E2E/安全/性能测试全体系、AI渗透测试流程、Agentic安全测试（OWASP Agentic Top 10）、视觉回归、可访问性测试、辅助脚本 |
| **Phase 5: 智能增强**   | 第9-10周  | 模式学习、错误记忆、智能路由、上下文压缩、工作流检查点、设计令牌自动同步、知识库强制工作流                                    |
| **Phase 6: 多平台适配**  | 第11-12周 | Trae/Cursor/Windsurf/Antigravity适配器、A2A/MCP协议集成、Figma/Penpot API集成               |
| **Phase 7: 优化与文档**  | 第13-14周 | 性能优化、完整文档、示例项目、设计系统示例                                                            |

### 12.2 成功指标

| 指标            | 目标值                                     | 采集方法                        |
| :------------ | :-------------------------------------- | :-------------------------- |
| 开发效率提升        | 3-5倍（与传统开发对比）                           | 相同功能实现耗时对比                  |
| 测试覆盖率保证       | ≥85%                                    | `coverage-check.py` 自动报告    |
| 安全漏洞发现率       | OWASP Top 10 + Agentic Top 10 + AI渗透全覆盖 | 安全扫描报告 + AI渗透测试日志           |
| 首次通过率         | ≥80%（无人工干预完成全流程）                        | PR合并记录中无需额外修复的比例            |
| 代码审查效率        | 人工审查时间减少60%                             | 审查时间统计（对比基线）                |
| 设计实现一致性       | ≥95%                                    | 视觉差异报告 + 人工抽样               |
| 文档完整性         | 关键文档覆盖率100%                             | `documentation-coverage` 脚本 |
| Karpathy准则合规率 | ≥90%（Code Reviewer抽样评估）                 | 审查日志统计                      |

***

## 十三、参考资料

| 序号 | 项目                                         | 说明                                                                                                         |
| :- | :----------------------------------------- | :--------------------------------------------------------------------------------------------------------- |
| 1  | **andrej-karpathy-skills**                 | 基于Karpathy对LLM编码陷阱观察总结的行为准则，约束AI编码行为，减少过度复杂化、擅自假设、范围蔓延                                                     |
| 2  | **@hivehub/rulebook**                      | 工具无关的AI开发框架，跨28种语言标准化，增量实施规范（3次尝试重启规则）、知识库强制工作流、Ralph自主循环、持久化记忆（BM25+HNSW），201次发布                          |
| 3  | **spatie/guidelines-skills**               | Spatie团队编码规范以Skills形式分发，含Laravel PHP/JavaScript/安全/版本控制四技能                                                 |
| 4  | **Project CodeGuard**                      | Cisco开源的模型无关安全框架，secure-by-default规则嵌入AI编码工作流（规划→生成→审查三阶段），已捐赠至CoSAI，支持Cursor/Windsurf/Copilot/Claude Code |
| 5  | **CangjieSkills**                          | 仓颉语言AI编程增强方案，DocFlow知识蒸馏流程，结构化技能知识库替代原始文档检索，实测降低60% Token消耗，基于OpenCode+GLM5验证                              |
| 6  | **create-sddwcc**                          | Claude Code多Agent架构驱动的完整SDD系统，18个专业Agent覆盖从需求到部署全流程，包含MCP集成和定义完成框架                                         |
| 7  | **claude-code-collective**                 | 30+ TDD强制专业Agent集合，包含Context7实时文档集成、智能任务路由、RED→GREEN→REFACTOR循环强制执行                                        |
| 8  | **SafeAgents**                             | 微软开源的多Agent安全评估框架，系统化暴露设计选择对对抗性提示的敏感度，Dharma诊断度量                                                           |
| 9  | **FCV-Attack研究**                           | 揭示功能正确但存在漏洞的补丁（FCV patches）威胁，跨12种Agent-模型组合评估                                                             |
| 10 | **IMBIA / Adv-IMBIA**                      | 隐蔽恶意行为注入攻击及防御机制研究，显示编码和测试阶段Agent被攻陷风险最大                                                                    |
| 11 | **Multi-Agent Code Injection分析**           | 多Agent代码注入攻击分析，coder-reviewer-tester架构更具韧性；添加安全分析Agent提升效率与韧性                                              |
| 12 | agency-agents                              | 多Agent角色分工框架                                                                                               |
| 13 | MoAI-ADK                                   | SPEC-First + TDD开发框架                                                                                       |
| 14 | PactKit                                    | Plan-Act-Check-Done生命周期                                                                                    |
| 15 | Don Cheli SDD                              | 71+命令42技能                                                                                                  |
| 16 | agents-skill                               | 多Agent编排Skill                                                                                              |
| 17 | @itz4blitz/agentful                        | 并行开发工具包                                                                                                    |
| 18 | sdd-tdd-workflow                           | SDD+TDD集成工作流                                                                                               |
| 19 | TDDev                                      | 多Agent TDD全栈框架                                                                                             |
| 20 | AgentMesh                                  | 多Agent协作框架                                                                                                 |
| 21 | Claude Code Skills                         | Agent Skills实践                                                                                             |
| 22 | Trae SOLO                                  | Plan+Sub Agent模式                                                                                           |
| 23 | Microsoft Agent Framework                  | 生产级多Agent SDK+运行时，RC状态（2026年2月），Semantic Kernel+AutoGen融合，A2A/AG-UI/MCP互操作，Python和.NET双语言支持                |
| 24 | AgentForge                                 | 执行验证型多Agent框架，强制每次代码变更的Docker沙箱验证，SWE-bench Lite 40.0%解决率，Planner/Coder/Tester/Debugger/Critic五角色          |
| 25 | SEMAG                                      | 自进化多Agent代码生成框架，按任务难度自适应调整工作流                                                                              |
| 26 | TALM                                       | 动态树结构多Agent框架，长期记忆与局部错误修正                                                                                  |
| 27 | AG2 (AutoGen)                              | 开源多Agent协作框架，事件驱动架构                                                                                        |
| 28 | BeeAI + Agent Stack                        | IBM开源多Agent编排与部署                                                                                           |
| 29 | Dapr Agents                                | 分布式Agent框架，状态持久化与工作流恢复                                                                                     |
| 30 | CrewAI                                     | 角色驱动的多Agent编排框架                                                                                            |
| 31 | AgentScope 1.0                             | 阿里通义实验室三层多Agent框架                                                                                          |
| 32 | LightAgent                                 | 轻量级Agent框架（约1000行核心代码）                                                                                     |
| 33 | Animus                                     | 代币预算控制、质量门禁、共识投票的编排框架                                                                                      |
| 34 | ChatDev / MetaGPT                          | 模拟软件公司角色的多Agent协作                                                                                          |
| 35 | Sema Code                                  | 可嵌入的AI编码引擎，支持MCP/Skills集成                                                                                  |
| 36 | Open SWE                                   | 基于LangGraph的Deep Agents编码框架                                                                                |
| 37 | DevSwarm                                   | “hivecoding”并行迭代多模型编码环境                                                                                    |
| 38 | Strix                                      | AI多Agent协同渗透测试工具                                                                                           |
| 39 | BugTrace-AI                                | 一站式Web安全分析（SAST+DAST+AI侦察）                                                                                 |
| 40 | CAI (Cybersecurity AI)                     | 模块化AI渗透测试框架                                                                                                |
| 41 | Reaper                                     | 现代轻量级应用安全测试框架                                                                                              |
| 42 | Spec Kit                                   | GitHub四阶段SDD工具链                                                                                            |
| 43 | Tsumiki                                    | AI辅助TDD框架（红-绿-重构-验证）                                                                                       |
| 44 | SWE-Flow                                   | 从单元测试推断增量开发的TDD数据合成框架                                                                                      |
| 45 | Agent2Agent (A2A)                          | 跨框架Agent互操作开放协议（Google，2025）                                                                               |
| 46 | Model Context Protocol (MCP)               | Agent与工具/数据源的标准连接协议（Anthropic，2024-2025）                                                                   |
| 47 | OpenAI Agents SDK                          | 轻量级多Agent框架（Python/JavaScript），2025年发布                                                                     |
| 48 | LangGraph                                  | 图式化多Agent编排框架，支持Supervisor/Swarm/Collaborative模式                                                           |
| 49 | OpenSage                                   | Agent自编程生成引擎，LLM自动创建拓扑与工具集                                                                                 |
| 50 | Orla                                       | LLM多Agent系统服务库，阶段映射与KV缓存管理                                                                                 |
| 51 | AWE (Adaptive Web Exploitation)            | 内存增强多Agent Web渗透测试框架，XSS 87%/盲SQLi 66.7%                                                                   |
| 52 | TestForge                                  | 反馈驱动的Agentic测试套件生成，pass\@1率84.3%                                                                           |
| 53 | UnitTenX                                   | AI多Agent遗留代码单元测试生成，结合形式验证                                                                                  |
| 54 | MASTEST                                    | LLM多Agent RESTful API测试系统                                                                                  |
| 55 | AgentGit                                   | Git式状态版本控制框架，支持MAS工作流回滚与分支                                                                                 |
| 56 | Worktrunk                                  | Git worktree CLI管理工具，专为并行AI Agent设计                                                                        |
| 57 | OWASP Top 10 for Agentic Applications 2026 | Agentic AI安全风险框架，覆盖目标劫持、工具滥用、身份权限滥用等十大风险                                                                   |
| 58 | OWASP LLM Top 10 2025                      | LLM应用层安全风险框架                                                                                               |
| 59 | OWASP MCP Top 10                           | MCP工具连接层安全风险框架                                                                                             |
| 60 | TrinityGuard                               | 上海AI实验室开源MAS安全评估监控框架，三层20种风险分类，OWASP标准对齐，评估层+运行时监控双层防护，LLM Judge Factory统一协调                               |
| 61 | VulnSage                                   | 多Agent自动化漏洞利用生成框架，模拟安全研究者工作流分解，迭代式反馈自优化，已发现146个真实0-day漏洞，漏洞利用生成较SOTA工具提升53%                                |
| 62 | JoySafeter                                 | 京东开源AI驱动安全编排平台，200+安全工具MCP集成，DeepAgents Manager-Worker星型拓扑，长短期记忆系统，全链路Langfuse可观测性                         |
| 63 | Agent Governance Toolkit                   | 微软开源的AI代理运行时安全工具包，MIT许可证，首个覆盖全部10项OWASP Agentic风险的工具集，Agent OS策略引擎+Agent Mesh安全通信+Agent Runtime动态执行环       |
| 64 | OpenAgentSafety                            | ICLR 2026接受的多Agent安全评估框架，8类关键风险类别，350+多轮多用户任务，真实工具交互，Claude-Sonnet-3.7在51.2%的安全脆弱任务中出现不安全行为                |
| 65 | Argusee                                    | DARKNAVY多Agent协作漏洞发现架构，模拟人类安全团队分工协作机制，在Linux USB协议栈测试中发现CVE-2025-37891高危漏洞，可root提权                         |
| 66 | MAESTRO                                    | CSA云安全联盟发布的多Agent环境安全框架，针对银行业等高度监管行业设计，最小可行控制分层模型（基础模型/数据操作/Agent框架/部署基础设施/评估可观测性/安全合规/Agent生态）            |
| 67 | Penpot / Figma                             | 开源/商业设计工具，设计令牌导出API                                                                                        |
| 68 | Storybook / Chromatic                      | UI组件开发与视觉回归测试                                                                                              |
| 69 | axe-core / Pa11y                           | 可访问性测试自动化                                                                                                  |
| 70 | Style Dictionary                           | 设计令牌跨平台转换                                                                                                  |
| 71 | Docusaurus / MkDocs                        | 文档站生成器                                                                                                     |
| 72 | Maris (AG2内置)                              | 细粒度策略引导的安全防护系统，控制Agent间通信和Agent-环境交互                                                                       |
| 73 | SAFEFLOW                                   | 协议级安全框架，强制执行细粒度信息流控制（IFC），引入事务执行和回滚机制                                                                      |
| 74 | SAGA                                       | 可扩展的Agentic系统治理安全架构，提供用户对Agent生命周期的监督                                                                      |
| 75 | AutoPentester                              | LLM Agent驱动的自动化渗透测试框架，子任务完成率提升27.0%                                                                        |
| 76 | xOffense                                   | AI驱动的多Agent渗透测试框架，使用微调的中型开源LLM驱动推理和决策                                                                      |
| 77 | SWE-Bench / Multi-SWE-bench                | 多语言软件工程Agent能力基准测试框架                                                                                       |
| 78 | git-stint / worktrunk / wt                 | Git worktree并行开发工具集，专为AI Agent并行设计                                                                         |

