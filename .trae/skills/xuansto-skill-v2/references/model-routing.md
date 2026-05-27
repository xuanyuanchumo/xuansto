# 模型路由策略

## 模型路由策略概述

模型路由策略是基于任务复杂度智能选择模型层级的机制，确保在保证任务质量的前提下优化Token消耗和响应速度。

- 在Agent frontmatter的`model`字段中声明该Agent所需的模型层级
- Orchestrator分派任务时根据`model`字段选择对应的执行策略
- 未声明`model`字段的Agent默认使用`standard`层级

## 模型层级定义

| 层级 | 值 | 适用场景 | 典型Agent |
|------|-----|---------|----------|
| 快速 | `fast` | 文件搜索、简单编辑、文档查找 | Token Optimizer, Doc Reviewer, Bug Scanner, Monitor Specialist |
| 标准 | `standard` | 多文件实现、代码审查、测试编写 | Backend/Frontend/Fullstack Developer, Code Reviewer, QA Engineer |
| 深度 | `deep` | 架构设计、安全分析、复杂调试 | System Architect, Security Auditor, AI Penetration Tester, Orchestrator |

## 57个Agent的model分配

> 权威来源：`agents/registry.yaml`，本文档保持同步。

### fast（8个）

| Agent | model |
|-------|-------|
| Token Optimizer | fast |
| Comment Verifier | fast |
| Doc Reviewer | fast |
| Data Seeder | fast |
| Progress Tracker | fast |
| Decision Logger | fast |
| Quality Monitor | fast |
| Bug Scanner | fast |
| Monitor Specialist | fast |
| Unit Tester | fast |

### standard（33个）

| Agent | model |
|-------|-------|
| Backend Developer | standard |
| Frontend Developer | standard |
| Fullstack Engineer | standard |
| Mobile Developer | standard |
| Code Reviewer | standard |
| Integration Tester | standard |
| QA Engineer | standard |
| E2E Tester | standard |
| Desktop Tester | standard |
| Performance Tester | standard |
| Test Maintainer | standard |
| Refactoring Specialist | standard |
| CI/CD Specialist | standard |
| Build-Release Engineer | standard |
| Data Modeler | standard |
| DBA | standard |
| Compliance Officer | standard |
| UX Designer | standard |
| Frontend Stylist | standard |
| Desktop Developer | standard |
| Desktop UI Adapter | standard |
| Auto-Update Engineer | standard |
| Technical Writer | standard |
| Product Manager | standard |
| Brainstorming Facilitator | standard |
| Subagent Dispatcher | standard |
| Task Coordinator | standard |
| Database Engineer | standard |
| DevOps Engineer | standard |
| Documentation Engineer | standard |
| Specification Keeper | standard |
| Knowledge Manager | standard |
| Learning Specialist | standard |
| History Analyzer | standard |
| Compliance Reviewer | standard |
| Runtime Supervisor | standard |

### deep（10个）

| Agent | model |
|-------|-------|
| Orchestrator | deep |
| System Architect | deep |
| Security Auditor | deep |
| Penetration Tester | deep |
| AI Penetration Tester | deep |
| Security Tester | deep |
| Design System Generator | deep |
| Native Module Developer | deep |
| IPC Specialist | deep |
| Test Architect | deep |

## Orchestrator路由决策逻辑

Orchestrator在分派任务时按以下逻辑进行模型路由：

1. **读取Agent frontmatter的`model`字段**：每个Agent定义中包含`model`字段，Orchestrator优先遵循该声明
2. **默认策略**：未声明`model`字段的Agent默认使用`standard`层级
3. **Token降级策略**：当Token预算紧张时，按层级降级执行
   - L1 → `fast`优先：知识检索、文档查找、简单编辑等任务优先使用fast模型
   - L2 → `standard`：常规开发、测试、审查任务使用standard模型
   - L3 → `deep`（仅核心推理）：架构决策、安全分析、复杂调试等核心推理任务保留deep模型

## Token优化建议

### 基本原则

90%的编码任务使用`standard`模型即可满足需求，无需盲目升级到`deep`层级。

### 升级到deep的条件

满足以下任一条件时，应将任务升级到`deep`模型：

- 首次使用`standard`模型尝试失败
- 任务涉及跨5个以上文件的修改
- 需要做出架构层面的决策
- 涉及安全关键代码的编写或审查

### 降级到fast的条件

满足以下任一条件时，可将任务降级到`fast`模型：

- 仅涉及单文件的简单编辑
- 纯搜索或查找类任务
- 文档生成或格式化任务
