# 开源Agent框架概览参考文档

> 版本: 3.2.0 | 更新日期: 2026-05-06 | 编码: UTF-8 without BOM | 行尾: LF

---

## 概述

本文档综述主流开源AI Agent框架的架构特征、核心能力和适用场景，为多Agent系统设计提供技术选型参考。涵盖AG2/AutoGen、CrewAI、LangGraph、BeeAI、Dapr Agents、AgentScope、LightAgent、Animus、ChatDev/MetaGPT、OpenAI Agents SDK共10个框架。

---

## 框架对比矩阵

| 框架 | 核心范式 | 多Agent | 状态管理 | 工具集成 | 生产就绪 |
|------|---------|---------|---------|---------|---------|
| AG2/AutoGen | 对话驱动 | ✅ | 内存 | MCP/Function | ★★★ |
| CrewAI | 角色协作 | ✅ | 内存+持久化 | MCP/Tool | ★★★ |
| LangGraph | 图状态机 | ✅ | 持久化检查点 | LangChain | ★★★★ |
| BeeAI | 生产化 | ✅ | 持久化 | MCP/ACPA | ★★★★★ |
| Dapr Agents | 微服务 | ✅ | Dapr状态存储 | Dapr绑定 | ★★★★ |
| AgentScope | 消息传递 | ✅ | 分布式 | Pipeline | ★★★ |
| LightAgent | 轻量级 | ✅ | 内存 | MCP | ★★ |
| Animus | 认知架构 | ✅ | 向量存储 | 自定义 | ★★ |
| ChatDev/MetaGPT | 软件开发 | ✅ | 消息流 | 代码执行 | ★★★ |
| OpenAI Agents SDK | 官方SDK | ✅ | RunContext | Function | ★★★★ |

---

## 各框架详解

### 1. AG2/AutoGen

**架构：** 对话驱动的多Agent协作框架，Agent通过消息传递进行交互。

```yaml
ag2_autogen:
  paradigm: conversation_driven
  core_concepts:
    - ConversableAgent: 可对话Agent基类
    - AssistantAgent: AI助手Agent
    - GroupChat: 群组对话管理
    - HumanInputMode: 人工介入模式
  strengths:
    - 灵活的对话编排
    - 支持人工介入
    - 代码执行沙箱
  limitations:
    - 状态管理较弱
    - 生产部署需额外工作
  use_cases: [research, data_analysis, code_generation]
```

### 2. CrewAI

**架构：** 基于角色的Agent协作框架，定义Crew（团队）、Agent（角色）和Task（任务）。

```yaml
crewai:
  paradigm: role_based_collaboration
  core_concepts:
    - Crew: Agent团队定义
    - Agent: 角色化Agent（含目标、背景、工具）
    - Task: 带预期输出的任务
    - Process: 协作流程（sequential/hierarchical）
  strengths:
    - 角色定义直观
    - 内置任务编排
    - 支持MCP工具
  limitations:
    - 复杂工作流支持有限
    - 调试困难
  use_cases: [content_creation, research, automation]
```

### 3. LangGraph

**架构：** 基于图的状态机框架，支持循环、分支和持久化检查点。

```yaml
langgraph:
  paradigm: graph_state_machine
  core_concepts:
    - StateGraph: 状态图定义
    - Node: 处理节点
    - Edge: 条件转移边
    - Checkpoint: 持久化检查点
  strengths:
    - 精确的流程控制
    - 持久化状态管理
    - 人工介入检查点
    - LangChain生态集成
  limitations:
    - 学习曲线较陡
    - 图定义冗长
  use_cases: [complex_workflows, stateful_agents, human_in_loop]
```

### 4. BeeAI

**架构：** 面向生产环境的企业级Agent框架，强调可观测性和可靠性。

```yaml
beeai:
  paradigm: production_ready
  core_concepts:
    - Agent: 生产化Agent基类
    - Workflow: 工作流编排
    - Memory: 持久化记忆
    - ACPA: Agent通信协议适配
  strengths:
    - 生产级可靠性
    - 内置可观测性
    - MCP协议支持
    - 企业级安全
  limitations:
    - 相对较新
    - 社区规模较小
  use_cases: [enterprise_automation, customer_service, data_pipeline]
```

### 5. Dapr Agents

**架构：** 基于Dapr微服务运行时的Agent框架，天然支持分布式部署。

```yaml
dapr_agents:
  paradigm: microservice_based
  core_concepts:
    - Actor: Dapr Actor模型Agent
    - Pub/Sub: 事件驱动通信
    - State Store: 分布式状态管理
    - Binding: 外部系统集成
  strengths:
    - 天然分布式
    - 成熟的状态管理
    - 丰富的集成绑定
  limitations:
    - 依赖Dapr运行时
    - 部署复杂度较高
  use_cases: [distributed_systems, iot, event_driven]
```

### 6. AgentScope

**架构：** 基于消息传递的分布式Agent框架，强调灵活性和可扩展性。

```yaml
agentscope:
  paradigm: message_passing
  core_concepts:
    - AgentBase: Agent基类
    - Msg: 消息对象
    - Pipeline: 执行管道
    - Service: 工具服务
  strengths:
    - 灵活的消息传递
    - 支持分布式部署
    - 丰富的内置服务
  limitations:
    - 文档相对不足
    - 社区活跃度一般
  use_cases: [multi_agent_simulation, distributed_computing]
```

### 7. LightAgent

**架构：** 轻量级Agent框架，适合快速原型和简单场景。

```yaml
lightagent:
  paradigm: lightweight
  core_concepts:
    - Agent: 轻量Agent
    - Tool: MCP工具集成
    - Memory: 简单记忆管理
  strengths:
    - 极简设计
    - 快速上手
    - MCP原生支持
  limitations:
    - 功能有限
    - 不适合复杂场景
  use_cases: [prototyping, simple_automation, chatbot]
```

### 8. Animus

**架构：** 基于认知架构的Agent框架，模拟人类认知过程。

```yaml
animus:
  paradigm: cognitive_architecture
  core_concepts:
    - CognitiveAgent: 认知Agent
    - Belief: 信念系统
    - Desire: 目标系统
    - Intention: 意图系统
  strengths:
    - BDI认知模型
    - 向量存储集成
    - 复杂推理能力
  limitations:
    - 概念抽象
    - 实际应用案例较少
  use_cases: [complex_reasoning, autonomous_systems, simulation]
```

### 9. ChatDev/MetaGPT

**架构：** 面向软件开发的Agent框架，模拟软件公司组织结构。

```yaml
chatdev_metagpt:
  paradigm: software_development_simulation
  core_concepts:
    - Role: 软件开发角色（PM/Architect/Engineer/QA）
    - Action: 角色行为定义
    - Environment: 协作环境
    - MessageStream: 结构化消息流
  strengths:
    - 软件开发专用
    - 角色分工明确
    - 输出结构化
  limitations:
    - 领域特定
    - 代码质量依赖Prompt
  use_cases: [software_development, code_generation, documentation]
```

### 10. OpenAI Agents SDK

**架构：** OpenAI官方Agent SDK，基于RunContext和Function Calling。

```yaml
openai_agents_sdk:
  paradigm: official_sdk
  core_concepts:
    - Agent: Agent定义
    - RunContext: 运行上下文
    - FunctionTool: 函数工具
    - Runner: 执行器
  strengths:
    - 官方支持
    - 与OpenAI模型深度集成
    - 简洁API设计
    - 内置Guardrails
  limitations:
    - 绑定OpenAI生态
    - 多模型支持有限
  use_cases: [openai_integration, rapid_development, production]
```

---

## 选型建议

| 场景 | 推荐框架 | 理由 |
|------|---------|------|
| 复杂工作流 | LangGraph | 精确状态控制+持久化 |
| 企业生产 | BeeAI | 可观测性+可靠性 |
| 软件开发 | ChatDev/MetaGPT | 角色分工+结构化输出 |
| 快速原型 | LightAgent | 极简+MCP支持 |
| 分布式系统 | Dapr Agents | 微服务+状态管理 |
| 研究探索 | AG2/AutoGen | 灵活对话+人工介入 |

---

> 本文档由 Multi-Agent SDD/TDD Orchestrator 维护 | 最后更新: 2026-05-06
