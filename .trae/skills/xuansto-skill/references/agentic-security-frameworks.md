# Agentic安全框架集成指南

> 版本: 3.1.0 | 更新日期: 2026-05-06 | 编码: UTF-8 without BOM | 行尾: LF
> 质量门禁: AGENTIC-SECURITY | 需求文档: skill需求v3.0 §安全框架集成

---

## 概述

本文档收录当前Agentic安全领域的前沿框架，为xuansto-skill v3.0 Agentic安全防护能力增强提供参考。涵盖策略引导防护、协议级信息流控制、治理安全架构和模型无关安全框架四大方向，每个框架提供核心能力描述及与本Skill的集成方式。

---

## 目录

1. [Maris (AG2内置)](#maris-ag2内置)
2. [SAFEFLOW](#safeflow)
3. [SAGA](#saga)
4. [Project CodeGuard](#project-codeguard)
5. [框架对比矩阵](#框架对比矩阵)
6. [参考资料](#参考资料)

---

## Maris (AG2内置)

### 基本信息

| 属性 | 说明 |
|------|------|
| 名称 | Maris |
| 来源 | AG2（原AutoGen）项目内置 |
| 定位 | 细粒度策略引导安全防护系统 |
| 许可证 | MIT（随AG2发布） |

### 核心能力

Maris是AG2多Agent框架内置的细粒度策略引导安全防护系统，为Agent间交互提供运行时安全策略执行：

- **细粒度策略引导安全防护**: 采用Policy-as-Code范式，允许开发者定义Agent行为约束、通信规则和操作审批流程
- **控制Agent间通信**: 对Agent间消息传递实施策略控制，包括消息内容过滤、通信频率限制和通信对象白名单
- **控制Agent-环境交互**: 对Agent与外部环境（工具、API、文件系统等）的交互实施策略控制，限制操作范围和权限
- **运行时策略执行**: 在Agent运行时实时执行安全策略，违规操作即时拦截并记录审计日志

### 对本Skill的集成方式

| 集成点 | 集成方式 | 对应ASI风险 |
|--------|----------|-------------|
| Security Auditor通信安全审计 | 参考Maris策略引导防护模式，为ASI07提供框架级实现 | ASI07 |
| Runtime Supervisor运行时防护 | 集成Maris作为运行时防护组件，实施Agent间通信策略控制 | ASI07, ASI09 |
| Agent间通信策略 | 采用Maris Policy-as-Code模式，定义Agent间通信安全策略 | ASI07 |
| 操作审批流程 | 参考Maris操作审批流程，为敏感操作设置策略审批门禁 | ASI09 |

### 参考链接

- GitHub: https://github.com/ag2ai/ag2
- 文档: AG2 (AutoGen) Maris Security Policy Documentation

---

## SAFEFLOW

### 基本信息

| 属性 | 说明 |
|------|------|
| 名称 | SAFEFLOW |
| 来源 | 学术研究开源项目 |
| 定位 | 协议级安全框架 |
| 许可证 | Apache 2.0 |

### 核心能力

SAFEFLOW是协议级安全框架，在Agent通信协议层强制执行细粒度信息流控制（IFC），防止敏感数据在Agent间未经授权传播：

- **强制执行细粒度信息流控制(IFC)**: 基于信息流控制理论，为每条消息标注安全标签，在协议层强制执行标签兼容性检查
- **事务执行**: 引入事务执行机制，Agent操作在事务内执行，确保操作的原子性和一致性
- **回滚机制**: 支持事务回滚，当操作违反安全策略或执行失败时，自动回滚到安全状态
- **安全缓存**: 提供安全缓存机制，对敏感数据实施缓存隔离和访问控制，防止缓存侧信道攻击

### 对本Skill的集成方式

| 集成点 | 集成方式 | 对应ASI风险 |
|--------|----------|-------------|
| Runtime Supervisor状态管理安全 | 集成SAFEFLOW事务执行和回滚机制，为状态管理提供安全基础 | ASI08 |
| Runtime Supervisor故障回滚 | 采用SAFEFLOW回滚机制，实现故障时自动回滚到安全状态 | ASI08 |
| 数据流合规检查 | 参考SAFEFLOW IFC标签体系，实施Agent间数据流合规性检查 | ASI07 |
| 策略违规恢复 | 集成SAFEFLOW策略违规恢复流程，自动恢复策略违规导致的状态异常 | ASI09 |

### 参考链接

- 论文: SAFEFLOW: Protocol-Level Security Framework with Information Flow Control for Agentic Systems

---

## SAGA

### 基本信息

| 属性 | 说明 |
|------|------|
| 名称 | SAGA (Scalable Agentic Governance Architecture) |
| 来源 | 学术研究开源项目 |
| 定位 | 可扩展Agentic系统治理安全架构 |
| 许可证 | Apache 2.0 |

### 核心能力

SAGA是面向可扩展Agentic系统的治理安全架构，提供Agent注册、行为策略、审计追踪和合规验证的全链路治理能力：

- **加密机制派生访问控制令牌**: 使用加密机制（如HMAC、数字签名）派生访问控制令牌，确保令牌不可伪造、不可篡改
- **形式化安全保障**: 提供形式化的安全保障证明，包括安全性不变量定义、威胁模型形式化和安全属性验证
- **Agent注册与身份生命周期管理**: 支持Agent注册、身份验证、权限分配和身份撤销的全生命周期管理
- **可扩展审计追踪与事件存储**: 分布式审计追踪系统，支持水平扩展的事件存储和查询

### 对本Skill的集成方式

| 集成点 | 集成方式 | 对应ASI风险 |
|--------|----------|-------------|
| Compliance Officer治理框架 | 采用SAGA加密访问控制令牌机制，为ASI03提供治理框架参考 | ASI03 |
| Compliance Officer形式化保障 | 参考SAGA形式化安全保障方法，构建合规验证的形式化基础 | ASI03 |
| 跨Agent权限控制 | 集成SAGA访问控制令牌机制，实现跨Agent权限控制和委派链验证 | ASI03 |
| 审计追踪系统 | 参考SAGA可扩展审计追踪架构，增强审计日志的完整性和可查询性 | ASI10 |

### 参考链接

- 论文: SAGA: Scalable Agentic Governance Architecture with Formal Security Guarantees

---

## Project CodeGuard

### 基本信息

| 属性 | 说明 |
|------|------|
| 名称 | Project CodeGuard |
| 来源 | Cisco（思科）开源 |
| 定位 | 模型无关安全框架 |
| 许可证 | Apache 2.0 |

### 核心能力

Project CodeGuard是Cisco开源的模型无关安全框架，将secure-by-default规则嵌入AI代码生成的全流程：

- **模型无关**: 不依赖特定AI模型，可与任何代码生成模型（GPT、Claude、Codex等）集成
- **secure-by-default规则嵌入**: 将安全编码规则作为默认约束嵌入代码生成过程，确保生成的代码默认满足安全要求
- **规划→生成→审查三阶段**: 将安全保护嵌入三个阶段：
  - 规划阶段：在代码生成前注入安全约束和最佳实践
  - 生成阶段：在代码生成过程中实时检查安全规则合规性
  - 审查阶段：对生成的代码进行安全审查和漏洞检测
- **安全规则可配置**: 支持自定义安全规则集，可根据项目安全要求灵活配置

### 对本Skill的集成方式

| 集成点 | 集成方式 | 对应ASI风险 |
|--------|----------|-------------|
| Code Reviewer安全编码审查 | 采用CodeGuard规划→生成→审查三阶段模式，嵌入安全编码规则 | ASI05 |
| AI代码生成安全保护 | 集成CodeGuard secure-by-default规则，确保AI生成代码默认满足安全要求 | ASI05 |
| Security Auditor代码安全检查 | 参考CodeGuard安全规则集，构建代码安全检查规则库 | ASI05 |
| 安全编码规范 | 采用CodeGuard安全规则可配置模式，支持项目级安全编码规范定制 | ASI05 |

### 参考链接

- GitHub: https://github.com/cisco/CodeGuard
- 文档: Project CodeGuard: Model-Agnostic Secure-by-Default Framework for AI Code Generation

---

## 框架对比矩阵

| 框架 | 核心定位 | 安全机制 | 形式化保障 | 集成难度 | 适用场景 |
|------|----------|----------|-----------|----------|----------|
| Maris | 策略引导防护 | Policy-as-Code | 策略验证 | 低（AG2原生） | Agent间通信与交互控制 |
| SAFEFLOW | 协议级IFC | 信息流控制+事务回滚 | IFC标签兼容性证明 | 高 | 数据隔离与故障恢复 |
| SAGA | 治理安全架构 | 加密令牌+形式化验证 | 形式化安全保障 | 中 | 大规模Agent治理与合规 |
| Project CodeGuard | 模型无关安全 | 规划→生成→审查三阶段 | 安全规则合规性 | 低 | AI代码生成安全保护 |

---

## 参考资料

- [OWASP Agentic Top 10 2026](https://owasp.org/www-project-agentic-security/)
- [AG2 (AutoGen) Framework](https://github.com/ag2ai/ag2)
- [Cisco Open Source Projects](https://github.com/cisco)
- [NIST SP 800-53 Security and Privacy Controls](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final)

---

> 本文档由 Multi-Agent SDD/TDD Orchestrator 维护 | 最后更新: 2026-05-05 | 版本: 3.0.0

---

## 相关参考

- [安全前沿框架集成指南](security-frontier-frameworks.md) — 多Agent安全前沿框架参考
- [AI渗透测试框架集成指南](ai-pentest-frameworks.md) — AI驱动渗透测试框架参考
- [OWASP Agentic Top 10 2026 参考文档](owasp-agentic-top10-2026.md) — Agentic AI系统安全风险清单及测试框架
- [安全指南参考文档](security-guidelines.md) — 安全编码实践与Agentic安全防护体系

---

## OWASP Agentic ASI01-ASI10 风险分类与防护策略映射

### 风险分类总览

| 编号 | 风险名称 | 核心威胁 | 关键防护策略 | 对应安全框架 |
|------|----------|----------|-------------|-------------|
| ASI01 | 目标劫持 (Goal Hijacking) | Agent目标被恶意篡改 | 意图验证、输出约束 | Maris策略引导 |
| ASI02 | 工具滥用 (Tool Misuse) | Agent工具被非法调用 | 工具权限控制、调用审计 | Maris操作审批 |
| ASI03 | 身份权限滥用 (Identity/Permission Abuse) | Agent权限越界 | 最小权限、身份验证 | SAGA治理架构 |
| ASI04 | 供应链漏洞 (Supply Chain Vulnerabilities) | 外部组件被投毒 | 依赖审计、签名验证 | CodeGuard安全规则 |
| ASI05 | 意外代码执行 (Unintended Code Execution) | 恶意代码被触发执行 | 沙箱隔离、代码审查 | CodeGuard三阶段 |
| ASI06 | 记忆中毒 (Memory Poisoning) | Agent记忆被恶意注入 | 记忆验证、置信度过滤 | TrinityGuard检测层 |
| ASI07 | 不安全Agent间通信 (Insecure Inter-Agent Communication) | 通信被窃听或篡改 | 加密通信、消息验证 | SAFEFLOW信息流控制 |
| ASI08 | 级联故障 (Cascading Failures) | 单点故障扩散 | 断路器、降级策略 | SAFEFLOW事务回滚 |
| ASI09 | 过度自主 (Excessive Autonomy) | Agent越权自主决策 | 人机协作断点、权限分级 | Maris策略约束 |
| ASI10 | 可观测性缺失 (Lack of Observability) | 安全事件无法追溯 | 审计日志、指标监控 | SAGA审计追踪 |

### ASI01 目标劫持 — 防护策略详解

**威胁模型**：攻击者通过Prompt Injection、RAG投毒或Agent间消息注入，使Agent偏离原始任务目标。

**防护策略**：

1. **意图验证 (Intent Verification)**
   - 在Agent规划阶段注入目标完整性校验，使用ImmutableGoal封装原始目标
   - 对每轮Agent输出执行语义相似度检测，偏离阈值(默认0.3)时触发告警
   - 对用户输入执行注入模式检测，过滤"忽略指令"等劫持模式
   - RAG检索结果实施内容安全检查，过滤潜在的隐藏指令

2. **输出约束 (Output Constraint)**
   - 定义Agent输出的Schema约束，限制输出格式和内容范围
   - 对Agent决策结果执行目标一致性审计，记录所有目标偏离事件
   - 长期记忆写入前执行目标对齐验证，防止恶意目标跨会话持续生效

**框架集成**：Maris策略引导防护为ASI01提供运行时策略执行，可在Agent间通信层拦截目标劫持指令。

### ASI02 工具滥用 — 防护策略详解

**威胁模型**：攻击者引导Agent在合法权限内错误使用工具，造成数据泄露或业务破坏。

**防护策略**：

1. **工具权限控制 (Tool Permission Control)**
   - 实施基于角色的工具访问控制(RBAC)，每个Agent只能调用其角色允许的工具集
   - 工具参数白名单校验，拒绝SQL注入、路径遍历等恶意参数模式
   - 工具调用链深度限制(默认max_depth=5)，防止递归调用攻击

2. **调用审计 (Invocation Audit)**
   - 记录所有工具调用的完整上下文：调用者、参数、返回值、耗时
   - 实施基于工具维度的API限流(默认100次/分钟)，防止拒绝服务
   - 工具输出过滤，检测并移除返回结果中的注入内容

**框架集成**：Maris操作审批流程为ASI02提供敏感工具调用的策略审批门禁。

### ASI03 身份权限滥用 — 防护策略详解

**威胁模型**：攻击者操纵Agent委派关系或冒用身份，获取不应拥有的权限。

**防护策略**：

1. **最小权限 (Least Privilege)**
   - 每个Agent仅授予完成任务所需的最小权限集
   - 权限矩阵验证：Compliance Officer维护细粒度权限矩阵
   - 委派链深度控制，防止权限通过委派链无限传播

2. **身份验证 (Identity Verification)**
   - 使用SAGA加密令牌机制，所有Agent凭证具有TTL，过期自动失效
   - 会话权限隔离：每个会话权限独立管理，会话结束自动回收
   - 禁止将API密钥、令牌等凭证写入Agent上下文或长期记忆

**框架集成**：SAGA加密访问控制令牌和形式化验证为ASI03提供治理框架基础。

### ASI04 供应链漏洞 — 防护策略详解

**威胁模型**：Agent依赖的外部组件(模型、工具、插件、Prompt模板)被投毒或篡改。

**防护策略**：

1. **依赖审计 (Dependency Audit)**
   - 对所有外部组件执行哈希校验，确保与预期一致
   - 模型指纹验证：为每个模型注册唯一指纹，加载时验证匹配
   - MCP服务器安全评估：扫描TLS、认证等安全配置

2. **签名验证 (Signature Verification)**
   - 使用数字签名确保组件来源可信且未被篡改
   - 只允许从可信来源加载插件，所有插件需经过安全审查
   - 依赖链传播检测：扫描组件依赖关系，识别被污染的传递依赖

**框架集成**：Project CodeGuard的secure-by-default规则为ASI04提供代码生成阶段的安全约束。

### ASI05 意外代码执行 — 防护策略详解

**威胁模型**：Agent生成或处理的文本被解释为可执行代码，触发非预期执行。

**防护策略**：

1. **沙箱隔离 (Sandbox Isolation)**
   - 所有代码在受限沙箱中执行，限制可用模块、内存(256MB)、CPU时间(30s)和网络访问
   - 沙箱使用受限`__builtins__`，禁止`__import__`、`eval`、`exec`等危险函数
   - Electron环境使用sandboxed BrowserWindow，启用contextIsolation和nodeIntegration:false

2. **代码审查 (Code Review)**
   - 执行前分析代码内容，检测恶意模式(如`os.system`、`subprocess`、`pickle.loads`)
   - 集成SAST扫描，对Agent生成代码进行静态安全测试
   - 高风险代码执行需经过人工审批或安全层Agent审核

**框架集成**：Project CodeGuard规划→生成→审查三阶段模式为ASI05提供全流程安全保护。

### ASI06 记忆中毒 — 防护策略详解

**威胁模型**：恶意数据被注入Agent持久化记忆或RAG存储，持续影响后续推理。

**防护策略**：

1. **记忆验证 (Memory Validation)**
   - 对所有写入持久化记忆的内容执行污染模式检测，拒绝恶意内容
   - 记忆条目附带置信度评分，低置信度记忆标记为待验证
   - 定期验证Agent上下文完整性，检测注入和篡改

2. **置信度过滤 (Confidence Filtering)**
   - 对RAG检索结果执行置信度评估，低置信度内容降权或过滤
   - 上下文窗口大小限制(默认4000 tokens)，防止超长输入挤出安全指令
   - Omega Walls运行时防御：监控记忆状态变化，异常变化触发告警

**框架集成**：TrinityGuard Detection-Guard为ASI06提供实时检测能力。

### ASI07 不安全Agent间通信 — 防护策略详解

**威胁模型**：Agent间通信缺乏加密或验证，攻击者可实施中间Agent攻击、重放或窃听。

**防护策略**：

1. **加密通信 (Encrypted Communication)**
   - 所有Agent间通信使用端到端加密(AES-256-GCM)，会话密钥定期轮换
   - 通信通道建立时执行双向身份验证
   - 消息格式Schema校验，防止协议降级和格式篡改

2. **消息验证 (Message Verification)**
   - 每条消息附带HMAC-SHA256数字签名，接收方验证消息来源和完整性
   - Nonce防重放机制，过期Nonce(默认TTL=300s)自动清理
   - 通信频率限制，防止消息洪泛攻击

**框架集成**：SAFEFLOW信息流控制(IFC)为ASI07提供协议级安全标签和兼容性检查。

### ASI08 级联故障 — 防护策略详解

**威胁模型**：单个Agent故障通过依赖关系和工作流链条向外传播，演变为大规模事故。

**防护策略**：

1. **断路器 (Circuit Breaker)**
   - 实施Circuit Breaker模式，连续失败超过阈值(默认5次)时自动熔断
   - 熔断后进入半开状态，允许探测性请求验证恢复
   - 故障Agent自动隔离到独立区域，切断与其他Agent的依赖关系

2. **降级策略 (Degradation Strategy)**
   - 工作流关键节点创建检查点，故障时回滚到最近安全状态
   - Runtime Supervisor持续监控Agent健康状态，异常时自动隔离
   - 定义服务降级方案：核心功能保障，非核心功能可临时关闭

**框架集成**：SAFEFLOW事务执行和回滚机制为ASI08提供状态管理安全基础。

### ASI09 过度自主 — 防护策略详解

**威胁模型**：Agent在缺乏约束的情况下执行敏感操作，超出预期决策范围。

**防护策略**：

1. **人机协作断点 (Human-in-the-Loop Breakpoint)**
   - 高风险操作(删除、支付、配置修改)设置人工审批门禁
   - 分层决策控制：低风险自动批准、中风险人工推荐、高风险强制人工确认
   - 自主决策审计：记录所有决策的完整上下文(依据、置信度、审批状态)

2. **权限分级 (Permission Tiering)**
   - 为每个Agent定义明确的权限边界，禁止执行超出范围的操作
   - 操作风险等级分类：low(查询/读取)、medium(更新/创建)、high(删除/执行)
   - 约束完整性验证：定期验证Agent约束条件是否被绕过或弱化

**框架集成**：Maris策略约束为ASI09提供运行时行为边界控制。

### ASI10 可观测性缺失 — 防护策略详解

**威胁模型**：多Agent系统运行时行为缺乏监控和审计，安全事件无法及时检测。

**防护策略**：

1. **审计日志 (Audit Logging)**
   - 使用哈希链保证审计日志不可篡改，支持完整性验证
   - 记录所有Agent决策的完整上下文：输入、输出、置信度、时间戳
   - 日志分级存储：热数据(7天)、温数据(90天)、冷数据(1年)

2. **指标监控 (Metrics Monitoring)**
   - 采集关键运行指标：Agent调用成功率、错误率、延迟P99、资源使用率
   - 基于基线指标实施异常检测，自动识别偏离正常范围的行为
   - 分级告警：critical(PagerDuty+Slack)、high(Slack+Email)、medium(Email)、low(日志)

**框架集成**：SAGA可扩展审计追踪为ASI10提供分布式事件存储和查询能力。

---

## TrinityGuard

### 基本信息

| 属性 | 说明 |
|------|------|
| 名称 | TrinityGuard |
| 来源 | 上海AI实验室开源 |
| 定位 | MAS安全评估与监控框架 |
| 许可证 | Apache 2.0 |

### 核心集成点

TrinityGuard提供三层20种风险分类体系（Prevention-Guard / Detection-Guard / Response-Guard），与OWASP ASI01-ASI10对齐：

- **Prevention-Guard**：预防层风险分类，对应ASI01(目标劫持)、ASI03(权限滥用)、ASI04(供应链)、ASI09(过度自主)的预防性控制
- **Detection-Guard**：检测层风险分类，对应ASI05(代码执行)、ASI06(记忆污染)、ASI07(通信攻击)、ASI10(可观测性)的实时检测
- **Response-Guard**：响应层风险分类，对应ASI02(工具滥用)、ASI08(级联故障)的应急响应和恢复

集成方式：Security Auditor审计检查清单可参考TrinityGuard三层分类组织审计项；Runtime Supervisor运行时监控可参考Detection-Guard检测模式。

---

## SafeAgents

### 基本信息

| 属性 | 说明 |
|------|------|
| 名称 | SafeAgents |
| 来源 | 学术研究开源项目 |
| 定位 | Agent行为安全评估框架 |
| 许可证 | MIT |

### 核心集成点

SafeAgents提供多Agent安全评估方法论，包括Agent行为安全测试、对齐评估和风险量化：

- **行为安全测试**：对Agent决策行为进行安全性测试，验证Agent在对抗输入下不偏离预期行为，补充ASI01防护的测试方法论
- **对齐评估**：评估Agent行为与设计意图的对齐程度，量化对齐分数，增强Runtime Supervisor的目标一致性监控
- **风险量化**：将Agent安全风险量化为可度量指标，构建安全评分卡，补充AGENTIC-SECURITY质量门禁的量化评估维度

集成方式：Security Auditor可参考SafeAgents评估方法论构建安全评分卡；AI Penetration Tester可参考行为安全测试用例设计对抗性测试场景。
