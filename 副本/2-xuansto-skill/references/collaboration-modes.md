# 协作模式详细定义

> 版本: 1.9.0 | 更新日期: 2026-05-01 | 编码: UTF-8 | 行尾: LF

本文件定义Xuansto Skill的8种Agent协作模式，供Orchestrator根据任务特征自动选择或由用户通过命令手动指定。

## 目录

1. [Auto Mode（智能路由模式）](#auto-mode智能路由模式)
2. [Review Mode（交叉审查模式）](#review-mode交叉审查模式)
3. [Challenge Mode（对抗辩论模式）](#challenge-mode对抗辩论模式)
4. [Consult Mode（专家咨询模式）](#consult-mode专家咨询模式)
5. [Sequential Mode（串行执行模式）](#sequential-mode串行执行模式)
6. [Parallel Mode（并行执行模式）](#parallel-mode并行执行模式)
7. [Hivecoding Mode（蜂群编码模式）](#hivecoding-mode蜂群编码模式)
8. [Cross-Platform Mode（跨平台协同模式）](#cross-platform-mode跨平台协同模式)
9. [模式切换规则](#模式切换规则)
10. [Orchestrator路由逻辑](#orchestrator路由逻辑)

---

## Auto Mode（智能路由模式）

**触发条件**：默认模式，用户未指定模式时自动启用

**描述**：Orchestrator根据任务特征自动选择最合适的协作模式。分析任务复杂度、依赖关系、安全等级和Token预算，智能路由到最佳模式。

**路由决策矩阵**：

| 任务特征 | 路由目标模式 | 理由 |
|----------|-------------|------|
| 安全相关（审计/渗透测试） | Challenge | 需要对抗性视角发现盲点 |
| 架构决策 | Review + Consult | 需要专家审查和咨询 |
| 独立多模块开发 | Parallel | 模块间无依赖可并行 |
| 有依赖的流水线任务 | Sequential | 前序输出是后序输入 |
| Web+Desktop同时开发 | Cross-Platform | 需要共享层协同 |
| 高质量要求的核心模块 | Hivecoding | 多实现择优提升质量 |

**Agent组合策略**：Orchestrator动态选择2-5个Agent参与，优先激活精简模式（文件<50时仅核心Agent）。

---

## Review Mode（交叉审查模式）

**触发条件**：代码审查、架构评审、设计评审

**描述**：两个或多个Agent交叉审查对方的工作产出，确保质量和一致性。

**审查流程**：
1. Agent A完成工作产出（代码/文档/设计）
2. Agent B审查Agent A的产出，输出审查报告
3. Agent A根据审查报告修改
4. 如需多轮审查，重复2-3直到审查通过

**参与Agent**：
- 代码审查：Code Reviewer + 原开发者
- 架构评审：System Architect + Technical Writer
- 设计评审：UI Designer + UX Designer

**质量门禁**：GATE-009（代码审查）、DESIGN-REVIEW（设计评审）

---

## Challenge Mode（对抗辩论模式）

**触发条件**：安全审计、架构关键决策、高风险变更

**描述**：两个Agent持相反立场进行对抗性辩论，通过Red Team/Blue Team方式发现盲点和潜在问题。

**辩论流程**：
1. Red Team Agent提出攻击性观点或风险发现
2. Blue Team Agent提出防御性观点或反驳
3. 最多3轮辩论
4. Orchestrator裁决最终决策
5. 如Orchestrator无法裁决，升级至Level 2仲裁（+Architect ADR）

**参与Agent**：
- 安全审计：Security Auditor（Red） vs Penetration Tester（Blue）
- 架构决策：System Architect（方案A） vs 另一System Architect视角（方案B）

**仲裁机制**：
- Level 1：Orchestrator裁决（技术争议）
- Level 2：+System Architect ADR（策略争议）
- Level 3：人工断点（安全/产品关键决策）

---

## Consult Mode（专家咨询模式）

**触发条件**：需要特定领域专家知识、跨领域问题

**描述**：主Agent向专家Agent咨询特定领域问题，获取专业建议后继续执行。

**调用方式**：
1. 主Agent识别需要专家知识的领域
2. 向Orchestrator请求专家Agent咨询
3. 专家Agent提供咨询建议（不直接修改代码）
4. 主Agent整合建议后继续执行

**专家Agent映射**：

| 领域 | 专家Agent |
|------|----------|
| 数据库设计 | Data Modeler / DBA |
| 安全合规 | Security Auditor / Compliance Officer |
| 性能优化 | Performance Tester |
| 桌面开发 | Desktop Developer / Native Module Developer |
| UI/UX | UI Designer / UX Designer |

---

## Sequential Mode（串行执行模式）

**触发条件**：任务间存在强依赖关系（前序输出是后序输入）

**描述**：Agent按依赖顺序逐个执行，每个Agent完成后将输出传递给下一个Agent。

**执行规则**：
1. 严格按依赖顺序执行，不可并行
2. 前序Agent输出作为后序Agent输入
3. 前序Agent失败则后续Agent不启动
4. 每个Agent完成后执行质量门禁检查

**典型场景**：
- 需求分析 → 架构设计 → 代码实现
- Schema设计 → 迁移脚本 → 数据填充
- 设计系统 → 组件开发 → 视觉回归测试

---

## Parallel Mode（并行执行模式）

**触发条件**：任务间无依赖关系，可同时执行

**描述**：多个Agent同时执行独立任务，最大化执行效率。

**执行规则**：
1. 最大并行数受Token预算约束（见platform-config.yaml）
2. 并行Agent共享只读上下文，各自维护独立工作区
3. 并行结果由Orchestrator合并
4. 冲突时触发Review Mode解决

**典型场景**：
- 前端开发 + 后端开发（接口契约已定义）
- 单元测试编写 + 文档编写
- 多语言SDK同时开发

---

## Hivecoding Mode（蜂群编码模式）

**触发条件**：核心模块高质量要求、复杂算法实现、安全关键代码

**描述**：多个Agent独立实现同一功能的不同方案，Orchestrator择优合并或融合最佳实现。

**执行流程**：
1. Orchestrator向2-3个Agent分配相同任务
2. 每个Agent独立实现（不同算法/架构/风格）
3. Code Reviewer评估所有实现
4. Orchestrator选择最优实现或融合多个实现的优势
5. 被淘汰的实现存入经验知识库供参考

**择优标准**：
- 代码质量（可读性、可维护性）
- 性能（基准测试结果）
- 安全性（安全扫描结果）
- 测试覆盖率

**Token预算控制**：蜂群模式消耗较多Token，仅在Token预算充足时启用（使用率<50%时允许）。

---

## Cross-Platform Mode（跨平台协同模式）

**触发条件**：Web+Desktop同时开发、跨平台功能同步

**描述**：Web和Desktop Agent协同工作，共享业务逻辑层，各自处理平台特定实现。

**共享层策略**：
1. 共享层：业务逻辑、数据模型、API调用（由Full-Stack Engineer实现）
2. Web特定层：浏览器API、响应式布局（由Frontend Developer实现）
3. Desktop特定层：原生API、IPC通信、系统菜单（由Desktop Developer实现）

**协同流程**：
1. 共享层先实现，定义清晰接口
2. Web和Desktop Agent并行实现各自特定层
3. Desktop UI Adapter确保UI一致性
4. Cross-Platform Workflow验证功能一致性

**质量门禁**：DESKTOP-CROSS（跨平台一致性）、IPC-CONTRACT（IPC契约验证）

---

## 模式切换规则

| 当前模式 | 切换条件 | 目标模式 | 切换动作 |
|----------|---------|---------|---------|
| Auto | Token使用率>80% | Sequential | 降级为串行节省Token |
| Parallel | 检测到依赖冲突 | Review | 暂停并行，审查冲突 |
| Hivecoding | Token使用率>50% | Parallel | 减少并行Agent数 |
| 任何模式 | 安全门禁失败 | Challenge | 启动对抗性审查 |
| 任何模式 | 用户手动指定 | 指定模式 | 立即切换 |

---

## Orchestrator路由逻辑

```
function select_collaboration_mode(task):
    if user_specified_mode:
        return user_specified_mode
    
    if task.type in [SECURITY_AUDIT, PENETRATION_TEST]:
        return CHALLENGE
    
    if task.type == ARCHITECTURE_DECISION:
        return REVIEW + CONSULT
    
    if task.has_cross_platform:
        return CROSS_PLATFORM
    
    if task.modules are independent:
        if token_budget_usage < 50% and task.quality_tier == "critical":
            return HIVECODING
        return PARALLEL
    
    if task.has_sequential_dependencies:
        return SEQUENTIAL
    
    return AUTO
```

**路由优先级**：安全>架构>跨平台>质量>效率>默认
