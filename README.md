# Xuansto Skill - AI Skill Development Framework

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform](https://img.shields.io/badge/Platform-Trae%20IDE%20%7C%20Claude%20Code%20%7C%20Cursor%20%7C%20Windsurf-blue)]()
[![Version](https://img.shields.io/badge/Version-1.0.0-green)]()

**Xuansto Skill - 多Agent自主开发编排器 | 基于SDD+TDD融合的智能开发协调系统**

[English](#english) | [简体中文](#简体中文)

</div>

---

## 简体中文

### 📖 项目简介

Xuansto Skill (原名 Skiller) 是一个功能完善的AI Skill开发框架，旨在为Trae IDE、Claude Code、Cursor、Windsurf等主流AI开发工具提供多Agent自主开发指导系统。本项目基于SDD（规格驱动开发）+ TDD（测试驱动开发）循环，覆盖分析、设计、开发、测试、修复、完善、优化、验收、迭代的全流程。

### ✨ 核心特性

- **🤖 多Agent协作**：35个专业Agent角色，覆盖产品、设计、工程、测试、安全、运维等全栈开发领域
- **📋 SDD+TDD双循环**：强制实施"Spec → Test → Code"的开发范式，确保规格即法律、测试即标准
- **🛡️ Karpathy行为准则**：所有Agent遵循Think Before Coding、Simplicity First、Surgical Changes、Goal-Driven Execution四条原则
- **🔒 完整安全体系**：覆盖OWASP Top 10 + Agentic Top 10，支持AI自主渗透测试
- **🎨 UI/UX设计自动化**：支持设计系统生成、原型评审、可访问性检查、设计稿转代码
- **📊 质量门禁体系**：15个质量门禁，确保每个阶段交付物符合标准
- **🔄 自主迭代演化**：支持从需求到交付的持续迭代优化，具备自修复、知识沉淀能力

### 🏗️ 项目结构

```
xuansto-skill/
├── .trae/
│   └── skills/
│       ├── xuansto-skill/                       # 主Skill项目
│       │   ├── agents/                          # 35个Agent定义
│       │   │   ├── orchestrator/                # 编排层
│       │   │   ├── product/                     # 产品层
│       │   │   ├── design/                      # 设计层
│       │   │   ├── engineering/                 # 工程层
│       │   │   ├── database/                    # 数据库层
│       │   │   ├── testing/                     # 测试层
│       │   │   ├── security/                    # 安全层
│       │   │   ├── devops/                      # 运维层
│       │   │   ├── quality/                     # 质量层
│       │   │   └── documentation/               # 文档层
│       │   ├── commands/                        # 13个命令定义
│       │   ├── workflows/                       # 8个工作流定义
│       │   ├── templates/                       # 12个模板文件
│       │   ├── scripts/                         # 12个辅助脚本
│       │   ├── references/                      # 14个参考文档
│       │   ├── memory/                          # 记忆系统
│       │   └── SKILL.md                         # 主入口文件
│       ├── agency-agents/                       # Agency Agents参考实现
│       ├── global-chinese/                      # 全局中文响应技能
│       ├── mcp-builder/                         # MCP服务器构建技能
│       ├── sanliu/                              # 三省六部系统
│       └── universal-devops/                    # 通用DevOps技能
└── docs/
    └── skill需求.md                             # 详细需求文档
```

### 🚀 快速开始

#### 在Trae IDE中使用

1. 将项目克隆到本地：
   ```bash
   git clone <repository-url>
   cd xuansto-skill
   ```

2. Skill会自动加载到Trae IDE中（路径：`.trae/skills/`）

3. 使用触发词激活Skill：
   - "xuansto"
   - "多Agent开发"
   - "SDD"
   - "TDD"
   - "测试驱动开发"
   - "规格驱动开发"
   - "multi-agent"
   - "orchestration"

#### 在Claude Code中使用

```powershell
# 创建软链接
New-Item -ItemType Junction -Path ".claude\skills\xuansto-skill" -Target ".trae\skills\xuansto-skill"
```

#### 在Cursor中使用

参考 `.cursor/` 目录中的适配文件（待创建）

#### 在Windsurf中使用

参考 `.windsurf/` 目录中的适配文件（待创建）

### 📚 核心工作流

#### 7阶段SDD+TDD工作流

```
Phase 0: UX/UI Design → Phase 1: Clarify → Phase 2: Plan & Spec
    ↓
Phase 3: Test Design → Phase 4: Implementation → Phase 5: Verification
    ↓
Phase 6: Acceptance → Phase 7: Iteration
```

#### 质量门禁体系

| 门禁ID | 门禁名称 | 检查内容 | 阻塞级别 |
|--------|---------|---------|---------|
| GATE-01 | SPEC-COMPLETE | 规格完整性 | BLOCK |
| GATE-02 | TEST-COVERAGE | 测试覆盖率≥80% | BLOCK |
| GATE-03 | CODE-REVIEW | 代码审查通过 | BLOCK |
| GATE-04 | SECURITY-SCAN | 无P0/P1安全问题 | BLOCK |
| GATE-05 | PERFORMANCE | 性能基准达标 | WARN |
| GATE-06 | DOC-COMPLETE | 文档覆盖率100% | BLOCK |
| GATE-07 | DESIGN-TOKENS | 设计令牌同步 | BLOCK |
| GATE-08 | ACCESSIBILITY | 无A级可访问性违规 | BLOCK |
| GATE-09 | VISUAL-REGRESSION | 视觉差异<0.1% | WARN |
| GATE-10 | AI-PENETRATION | AI渗透测试通过 | BLOCK |
| GATE-11 | AGENTIC-SECURITY | Agentic Top 10合规 | BLOCK |
| GATE-12 | UX-ACCEPTANCE | 用户体验验收通过 | BLOCK |
| GATE-13 | COMPLIANCE | 合规检查通过 | BLOCK |
| GATE-14 | DEPLOYMENT | 部署验证通过 | BLOCK |
| GATE-15 | MONITORING | 监控指标正常 | WARN |

### 🤝 Agent角色体系

#### 编排层
- **Orchestrator**: 任务接收、分解、Agent调度、结果汇总

#### 产品层
- **Product Manager**: 需求澄清、功能分解、用户故事编写
- **System Architect**: 系统架构设计、技术选型、模块划分
- **Technical Writer**: 技术文档编写、API文档生成

#### 设计层
- **UI Designer**: 视觉设计、设计系统建立、设计令牌生成
- **UX Designer**: 用户研究、交互设计、原型制作
- **Frontend Stylist**: 设计稿转代码、响应式布局、动画效果

#### 工程层
- **Frontend Developer**: 前端代码实现、组件开发、状态管理
- **Backend Developer**: 后端代码实现、API开发、业务逻辑
- **Full-Stack Engineer**: 前后端联调、接口对接、数据流设计
- **Database Engineer**: 数据库设计、Schema管理、查询优化
- **Mobile Developer**: 移动端适配、跨端一致性
- **DevOps Engineer**: 部署配置、CI/CD流水线、环境管理

#### 测试层
- **Test Architect**: 测试策略制定、测试金字塔规划
- **Unit Tester**: 单元测试编写、TDD红绿重构
- **Integration Tester**: 集成测试编写、契约测试
- **E2E Tester**: 端到端测试编写、用户旅程模拟
- **Performance Tester**: 性能测试、负载测试、压力测试
- **Security Tester**: 安全测试、漏洞扫描、渗透测试
- **AI Penetration Tester**: AI驱动的自主渗透测试
- **Test Maintainer**: 测试用例维护、失败分析

#### 安全层
- **Security Auditor**: 代码安全审计、依赖漏洞扫描
- **Penetration Tester**: 渗透测试、漏洞验证、攻击面分析
- **Compliance Officer**: 合规检查、数据隐私审计

#### 运维层
- **CI/CD Specialist**: 流水线配置、自动化构建
- **Monitor Specialist**: 应用监控、日志聚合、告警配置
- **Runtime Supervisor**: Agent运行时健康监控、状态恢复

#### 质量层
- **Code Reviewer**: 代码审查、规范检查、最佳实践建议
- **Refactoring Specialist**: 代码重构、技术债务清理
- **Documentation Reviewer**: 文档审查、API文档一致性

#### 文档层
- **Documentation Engineer**: 编写和维护用户手册、开发者指南
- **Specification Keeper**: 维护规格文档索引、确保文档一致性

### 🔐 安全特性

#### OWASP Top 10 + Agentic Top 10 覆盖

- **ASI01**: Agent Goal Hijack（目标劫持）防护
- **ASI02**: Tool Misuse & Exploitation（工具滥用）防护
- **ASI03**: Identity & Privilege Abuse（身份权限滥用）防护
- **ASI04**: Agentic Supply Chain Vulnerabilities（供应链漏洞）防护
- **ASI05**: Unexpected Code Execution（意外代码执行）防护
- **ASI06**: Memory & Context Poisoning（记忆中毒）防护
- **ASI07**: Insecure Inter-Agent Communication（不安全Agent间通信）防护
- **ASI08**: Cascading Failures（级联故障）防护
- **ASI09**: Excessive Agency（过度自主）防护
- **ASI10**: Observability & Monitoring Gaps（可观测性缺失）防护

### 📖 参考开源项目

本项目充分借鉴以下开源项目的设计理念和最佳实践：

- **andrej-karpathy-skills**: Karpathy Guidelines四条行为准则
- **@hivehub/rulebook**: 工具无关的AI开发框架
- **agency-agents**: 角色分工矩阵、轻量级Markdown Agent定义
- **MoAI-ADK**: SPEC-First + TDD框架
- **Microsoft Agent Framework**: 生产级多Agent SDK
- **OpenAI Agents SDK**: 轻量级多Agent框架
- **LangGraph**: 图式化Agent编排

### 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

### 🤝 贡献指南

欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详情

---

## English

### 📖 Introduction

Skiller is a comprehensive AI Skill development framework designed to provide multi-agent autonomous development guidance for mainstream AI development tools such as Trae IDE, Claude Code, Cursor, and Windsurf. This project is based on SDD (Specification-Driven Development) + TDD (Test-Driven Development) cycles, covering the entire process from analysis, design, development, testing, fixing, improvement, optimization, acceptance to iteration.

### ✨ Core Features

- **🤖 Multi-Agent Collaboration**: 35 professional agent roles covering full-stack development domains
- **📋 SDD+TDD Dual Cycle**: Enforces "Spec → Test → Code" development paradigm
- **🛡️ Karpathy Guidelines**: All agents follow four principles: Think Before Coding, Simplicity First, Surgical Changes, Goal-Driven Execution
- **🔒 Complete Security System**: Covers OWASP Top 10 + Agentic Top 10, supports AI autonomous penetration testing
- **🎨 UI/UX Design Automation**: Supports design system generation, prototype review, accessibility checking, design-to-code
- **📊 Quality Gate System**: 15 quality gates ensuring deliverables meet standards at each stage
- **🔄 Autonomous Iteration Evolution**: Supports continuous iterative optimization from requirements to delivery

### 🚀 Quick Start

#### Using in Trae IDE

1. Clone the project:
   ```bash
   git clone <repository-url>
   cd skiller
   ```

2. Skills will automatically load into Trae IDE (path: `.trae/skills/`)

3. Activate skills using trigger words:
   - "multi-agent"
   - "SDD"
   - "TDD"
   - "test-driven development"
   - "specification-driven development"
   - "orchestration"

#### Using in Claude Code

```powershell
# Create junction link
New-Item -ItemType Junction -Path ".claude\skills\multi-agent-sdd-tdd-orchestrator" -Target ".trae\skills\multi-agent-sdd-tdd-orchestrator"
```

### 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details

---

<div align="center">

**Made with ❤️ by Skiller Team**

</div>
