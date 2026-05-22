# 架构概览

> 🏛️ **三省六部架构体系** - 以SDD规范为契约，以TDD红绿蓝循环为引擎，构建高质量、可维护、可追溯的软件工程体系 | **v3.3.0: CI/CD自动化 + 六维监控 + 测试体系完善**

---

## 版本更新 (v3.3.0)

### 🚀 新增架构组件

- **🔄 CI/CD自动化流水线** - 完整的GitHub Actions流水线架构
  - 多Python版本矩阵测试（3.10/3.11/3.12）
  - Skillscripts单元测试独立Job
  - 后端完整测试套件（lint/type-check/unit/integration/e2e/security）
  - 质量门禁自动检查与报告归档

- **📊 六维质量监控体系** - 从4维升级至6维
  - 新增：安全合规维度、文档质量维度
  - 集成Bandit安全扫描和Safety依赖检查

- **✅ 测试体系完善** - 258+新增测试用例
  - PathConfigCenter边界条件测试（62个）
  - SDD-TDD融合引擎完整循环测试（53个）
  - 质量监控六维体系集成测试（64个）

- **📝 自动报告生成系统** - 新增auto_report_generator.py
  - 自动收集测试结果数据
  - Markdown格式报告生成与归档
  - 版本号自动递增功能

## 核心工作流程

### 阶段流程总览

| 阶段 | 负责机构 | 核心职责 | 输出物 | 耗时估计 |
|------|----------|----------|--------|----------|
| 🔧 **服务启动** | 系统 | 启动数据库、后端、前端服务 | 服务状态报告 | 1-2 min |
| 🔍 **环境检测** | 系统 | 检测服务状态、Docker、依赖关系 | 环境检测报告 | 30s-1min |
| 📋 **SDD规范定义** | 中书省 | 定义接口、数据模型、行为规范 | 规范文件 (sdd_*.md) | 15-30 min |
| 📊 **需求分析** | 中书省 | 需求结构化、可行性研究、架构预检 | 需求规格说明书、验收测试用例 | 20-40 min |
| 🏗️ **概要设计** | 中书省 | 系统架构、模块划分、技术选型 | 概要设计说明书 | 30-60 min |
| ✍️ **方案审议** | 门下省 | 评审需求、测试覆盖、架构合规性 | 审议意见书 | 15-30 min |
| 🔄 **规范解析** | 系统 | 解析规范生成测试用例和代码骨架 | 测试代码、代码骨架 | 5-10 min |
| ⚙️ **执行统筹** | 尚书省 | 协调六部、TDD循环、外部技能调用 | 执行计划、进度报告 | 持续进行 |
| 📝 **状态记录** | 系统 | 记录技能调用、透明度数据 | 状态日志、追溯链 | 实时记录 |

### 详细工作流程图

```
┌────────────────────────────────────────────────────────────────────┐
│                        三省六部工作流程                             │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐         │
│  │   中书省     │───→│   门下省     │───→│   尚书省     │         │
│  │  (决策制定)  │    │  (审议监督)  │    │  (执行统筹)  │         │
│  └──────────────┘    └──────────────┘    └──────┬───────┘         │
│         │                                        │                 │
│         ↓                                        ↓                 │
│  ┌──────────────┐                       ┌──────────────────┐      │
│  │ • 需求分析   │                       │     六部协同     │      │
│  │ • 架构设计   │                       ├────────┬─────────┤      │
│  │ • SDD规范    │                       │        │         │      │
│  │ • 验收测试   │                       ↓        ↓         ↓      │
│  └──────────────┘               ┌────────┐ ┌────────┐ ┌────────┐ │
│                                 │  吏部  │ │  户部  │ │  礼部  │ │
│                                 │ (调度) │ │ (资源) │ │ (规范) │ │
│                                 └───┬────┘ └───┬────┘ └───┬────┘ │
│                                     │          │          │      │
│                                     └──────────┼──────────┘      │
│                                                ↓                  │
│                                        ┌──────────────┐          │
│                                        │   兵部 ⭐    │          │
│                                        │  (测试先行)  │          │
│                                        └──────┬───────┘          │
│                                               │                   │
│                    ┌──────────────────────────┼──────────────────┐│
│                    ↓                          ↓                  ↓│
│            ┌──────────┐              ┌──────────┐        ┌────────┐│
│            │  刑部 ⭐  │←────────────→│  工部 ⭐  │        │  结束  ││
│            │(重构优化)│   红绿蓝循环  │(代码实现)│        │  交付  ││
│            └────┬─────┘              └────┬─────┘        └────────┘│
│                 │                         │                       │
│                 └─────────────────────────┘                       │
│                           持续迭代                                │
└────────────────────────────────────────────────────────────────────┘
```

---

## 三省协调机制概览

三省协调机制是三省六部技能的核心治理架构，通过中书省（决策制定）、门下省（审议监督）、尚书省（执行统筹）的协同工作，确保软件开发过程的规范性和高质量。

### 机构职责

| 机构 | 核心职责 | 工作模式 | 子技能路径 |
|------|----------|----------|-----------|
| **中书省**<br>📋 决策中心 | • 需求结构化分析<br>• 系统架构设计<br>• SDD 规范定义<br>• 验收测试设计 | 输入：原始需求<br>处理：分析→设计→规范<br>输出：规格说明书 | [zhongshusheng/SKILL.md](../zhongshusheng/SKILL.md) |
| **门下省**<br>✍️ 审议监督 | • 需求完整性评审<br>• 架构合规性检查<br>• 测试覆盖率审查<br>• 质量门禁把控 | 输入：中书省输出<br>处理：评审→反馈→批准<br>输出：审议意见书 | [menxiasheng/SKILL.md](../menxiasheng/SKILL.md) |
| **尚书省**<br>⚙️ 执行引擎 | • 六部协调调度<br>• TDD 循环管理<br>• 外部技能调用<br>• 进度状态跟踪 | 输入：审议通过方案<br>处理：统筹→执行→监控<br>输出：交付成果 | [shangshusheng/SKILL.md](../shangshusheng/SKILL.md) |

> 📖 **详细信息**请参考 [省部协调机制](provincial_coordination.md)

---

## 六部协调机制概览

六部协调机制是尚书省下属的执行层，通过吏部、户部、礼部、兵部、工部、刑部的协同工作，实现TDD红绿蓝循环的完整执行。

### 部门职责矩阵

| 部门 | 核心职责 | TDD角色 | 关键产出 | 子技能路径 |
|------|----------|---------|----------|-----------|
| **吏部**<br>👥 | 人员调度<br>Agent分配 | 分配 TDD 角色 | 角色分配表<br>任务清单 | [shangshusheng/libu/SKILL.md](../shangshusheng/libu/SKILL.md) |
| **户部**<br>💰 | 资源管理<br>环境配置 | 管理测试环境资源 | 资源配置表<br>环境清单 | [shangshusheng/hubu/SKILL.md](../shangshusheng/hubu/SKILL.md) |
| **礼部**<br>📜 | 规范制定<br>代码审查 | 制定 TDD 编码规范 | 编码规范<br>审查清单 | [shangshusheng/liibu/SKILL.md](../shangshusheng/liibu/SKILL.md) |
| **兵部** ⭐<br>🧪 | **测试先行**<br>测试策略 | **编写测试用例**<br>红阶段 | 单元测试<br>集成测试<br>E2E测试 | [shangshusheng/bingbu/SKILL.md](../shangshusheng/bingbu/SKILL.md) |
| **刑部** ⭐<br>🔧 | **持续重构**<br>质量优化 | **优化代码质量**<br>蓝阶段 | 重构方案<br>质量报告 | [shangshusheng/xingbu/SKILL.md](../shangshusheng/xingbu/SKILL.md) |
| **工部** ⭐<br>🔨 | **测试执行**<br>代码实现 | **实现代码**<br>绿阶段 | 功能代码<br>实现文档 | [shangshusheng/gongbu/SKILL.md](../shangshusheng/gongbu/SKILL.md) |

> ⭐ 标记部门为 TDD 核心执行部门

> 📖 **详细信息**请参考 [六部工作流程](department_workflow.md)

---

## 架构原则技能

架构原则技能负责在设计和开发阶段确保代码架构符合业界最佳实践。

### 核心功能

- 🏗️ MVVM/MVC 架构检查
- 📐 SOLID 原则验证
- 🎯 简洁原则（DRY/YAGNI/KISS）
- 📊 架构质量评估

### 检查清单

```markdown
## 架构合规检查
- [ ] 单一职责原则 (SRP)
- [ ] 开闭原则 (OCP)
- [ ] 里氏替换原则 (LSP)
- [ ] 接口隔离原则 (ISP)
- [ ] 依赖倒置原则 (DIP)
- [ ] 不要重复自己 (DRY)
- [ ] 保持简单 (KISS)
- [ ] 不要过度设计 (YAGNI)
```

> 📖 **详细内容**请参考 [架构原则技能](jiagou_yuanze.md)

---

## 路径配置管理

### 概述

路径配置管理器是三省六部技能的基础设施组件，负责统一管理项目中所有路径配置，支持环境变量配置、动态路径解析和路径验证功能。

### 核心功能

| 功能 | 描述 | 使用场景 |
|------|------|----------|
| **路径注册** | 注册和管理项目路径 | 新增项目目录时 |
| **环境变量** | 支持环境变量配置路径 | 跨环境部署时 |
| **路径解析** | 动态解析相对/绝对路径 | 脚本执行时 |
| **路径验证** | 验证路径存在性和权限 | 启动检查时 |

### 预定义路径

| 路径名称 | 默认值 | 环境变量 | 描述 |
|----------|--------|----------|------|
| `SKILL_ROOT` | `.trae/skills/sanliu` | `SANLIU_SKILL_ROOT` | 技能根目录 |
| `DATA_DIR` | `data` | `SANLIU_DATA_DIR` | 数据目录 |
| `LOGS_DIR` | `logs` | `SANLIU_LOGS_DIR` | 日志目录 |
| `REPORTS_DIR` | `docs/reports` | `SANLIU_REPORTS_DIR` | 报告目录 |
| `CACHE_DIR` | `data/cache` | `SANLIU_CACHE_DIR` | 缓存目录 |
| `CONFIG_DIR` | `config` | `SANLIU_CONFIG_DIR` | 配置目录 |
| `SCRIPTS_DIR` | `skillscripts` | `SANLIU_SCRIPTS_DIR` | 脚本目录 |
| `TEMP_DIR` | `data/temp` | `SANLIU_TEMP_DIR` | 临时目录 |

### 使用方法

```bash
# 查看所有路径配置
python skillscripts/utils/path_config_manager.py --list

# 查看特定路径
python skillscripts/utils/path_config_manager.py --get --name SKILL_ROOT

# 验证所有路径
python skillscripts/utils/path_config_manager.py --validate
```

> 📖 **详细内容**请参考 [路径配置管理](skill_path_management.md)

---

## docs/目录管理

### 概述

docs/目录是三省六部技能的统一文档输出目录，所有生成的报告、API文档、工作流文档和知识库文档都统一存放在此目录下，避免硬编码路径，便于统一管理和维护。

### 目录结构

```
docs/
├── reports/           # 报告目录
│   ├── evolution/     # 演化报告
│   ├── health/        # 健康度报告
│   ├── quality/       # 质量报告
│   └── test/          # 测试报告
│
├── api/               # API文档目录
│   ├── openapi/       # OpenAPI规范文档
│   ├── swagger/       # Swagger文档
│   └── graphql/       # GraphQL文档
│
├── workflow/          # 工作流文档目录
│   ├── requirements/  # 需求文档
│   ├── design/        # 设计文档
│   ├── implementation/# 实现文档
│   └── deployment/    # 部署文档
│
├── knowledge/         # 知识库目录
│   ├── patterns/      # 设计模式
│   ├── best_practices/# 最佳实践
│   ├── solutions/     # 解决方案
│   └── experiences/   # 经验总结
│
└── libs/              # 版本文档目录
    ├── v1.0.0/        # 版本1.0.0文档
    ├── v2.0.0/        # 版本2.0.0文档
    └── v2.11.0/       # 当前版本文档
```

### 四大子目录说明

| 目录 | 路径 | 功能描述 | 主要内容 |
|------|------|----------|----------|
| **reports/** | `docs/reports/` | 报告存储目录 | 演化报告、健康度报告、质量报告、测试报告 |
| **api/** | `docs/api/` | API文档目录 | OpenAPI规范、Swagger文档、GraphQL文档 |
| **workflow/** | `docs/workflow/` | 工作流文档目录 | 需求文档、设计文档、实现文档、部署文档 |
| **knowledge/** | `docs/knowledge/` | 知识库目录 | 设计模式、最佳实践、解决方案、经验总结 |

---

## 持续演化系统

### 系统概述

三省六部技能内置完整的持续演化系统，实现自迭代、自优化、自修复、自完善四大核心能力，确保技能在使用过程中持续学习和进化。

### 四大核心能力

| 能力 | 描述 | 触发条件 | 执行频率 |
|------|------|----------|----------|
| **自迭代** | 自动检测问题并触发迭代改进循环 | 错误率 > 5%、性能下降 | 每小时 |
| **自优化** | 持续优化代码质量和性能 | 性能指标低于阈值 | 每6小时 |
| **自修复** | 自动检测并修复常见问题 | 检测到可修复问题 | 实时 |
| **自完善** | 持续学习和知识积累 | 有新的最佳实践 | 每日 |

### 核心组件

| 组件 | 脚本路径 | 功能描述 |
|------|----------|----------|
| **演化配置管理器** | [evolution_config_manager.py](../skillscripts/core/evolution_config_manager.py) | 演化触发条件配置、策略配置、热重载支持 |
| **演化告警系统** | [evolution_alert.py](../skillscripts/core/evolution_alert.py) | 告警规则引擎、通知机制、处理追踪 |
| **演化报告生成器** | [evolution_report_generator.py](../skillscripts/utils/evolution_report_generator.py) | 周期性报告、历史报告、对比报告生成 |
| **演化监控API** | [evolution_monitor.py](../backend/app/api/evolution_monitor.py) | WebSocket实时监控、状态查询、手动触发 |

> 📖 **详细内容**请参考 [持续演化系统](continuous_evolution.md)

---

## 永久演化模式

### 概述

永久演化模式是三省六部技能的高级运行模式，支持技能在后台持续运行并自动进行演化循环，实现真正的"永不停歇"的自我进化能力。

### 核心组件

| 组件 | 脚本路径 | 功能描述 |
|------|----------|----------|
| **演化循环执行器** | [evolution_cycle_executor.py](../skillscripts/core/evolution_cycle_executor.py) | 管理演化循环的持续执行 |
| **演化状态持久化** | [continuous_evolution_controller.py](../skillscripts/core/continuous_evolution_controller.py) | 演化状态的持久化存储和控制器 |
| **永久运行管理器** | [continuous_evolution_controller.py](../skillscripts/core/continuous_evolution_controller.py) | 永久运行模式的启动和管理 |

### 使用方法

```bash
# 启动永久演化模式（后台运行）
python skillscripts/core/continuous_evolution_controller.py --start

# 启动永久演化模式（前台运行，可查看日志）
python skillscripts/core/continuous_evolution_controller.py --start --foreground

# 停止永久演化模式
python skillscripts/core/continuous_evolution_controller.py --stop

# 查看运行状态
python skillscripts/core/continuous_evolution_controller.py --status
```

---

## 永久自演化系统

### 概述

永久自演化系统是三省六部技能的核心能力之一，使技能能够持续自我改进、自我优化和自我完善。该系统通过自动化工具链实现技能自身的演化，无需人工干预即可持续提升技能质量。

### 核心能力

| 能力 | 描述 | 触发条件 | 执行频率 |
|------|------|----------|----------|
| **自诊断** | 自动检测技能运行状态和潜在问题 | 错误率 > 5%、性能下降 | 每小时 |
| **自优化** | 自动优化技能配置和执行策略 | 性能指标低于阈值 | 每6小时 |
| **自修复** | 自动修复已知问题和错误模式 | 检测到可修复问题 | 实时 |
| **自完善** | 自动学习新知识并更新技能 | 有新的最佳实践 | 每日 |

### 启动和管理

```bash
# 启动永久自演化系统（后台模式）
python skillscripts/core/continuous_evolution_controller.py --start --mode self-evolution

# 查看演化状态
python skillscripts/core/continuous_evolution_controller.py --status

# 暂停演化
python skillscripts/core/continuous_evolution_controller.py --pause

# 恢复演化
python skillscripts/core/continuous_evolution_controller.py --resume
```

---

## 跨项目服务

### 概述

跨项目服务是三省六部技能的多项目管理能力，支持多个项目之间的知识共享、资源复用和协同演化，同时保证项目之间的隔离性。

### 核心组件

| 组件 | 脚本路径 | 功能描述 |
|------|----------|----------|
| **项目注册管理器** | [project_registration_manager.py](../skillscripts/core/project_registration_manager.py) | 管理项目注册、发现和生命周期 |
| **跨项目知识共享** | [cross_project_knowledge_sharing.py](../skillscripts/core/cross_project_knowledge_sharing.py) | 跨项目知识共享和同步 |
| **项目隔离管理器** | project_isolation_manager.py | 项目隔离和访问控制（待实现） |

### 使用示例

```bash
# 注册项目
python skillscripts/core/project_registration_manager.py \
  --register --name "my-project" --path "./project"

# 共享知识
python skillscripts/core/cross_project_knowledge_sharing.py \
  --share --project "my-project" --type "pattern" --name "auth-pattern"

# 配置隔离（TODO: 待实现）
# python skillscripts/core/project_isolation_manager.py \
#   --configure --project "my-project" --rules "moderate"
```

---

## 版本更新 (v4.0)

### 🚀 v4.0 架构全面升级

v4.0 在 v3.3.0 基础上实现了8大核心模块的全面升级，构建了更强大的全生命周期通用SKILL技能体系：

| 新增模块 | 核心能力 | 源码位置 |
|----------|----------|----------|
| **操作优先级控制器** | Agent-First 三级优先级决策 | `skillscripts/core/operation_priority.py` |
| **四维度输出防线** | Prompt→能力→规则→兜底 四层防御 | `skillscripts/core/four_d_defense.py` |
| **MARC-Lite 资源协调器** | 多Agent资源协调与死锁预防 | `skillscripts/core/resource_coordinator.py` |
| **密钥管理系统** | SecretsManager + HardcodedDetector | `skillscripts/security/` |
| **Agency Bridge 桥接层** | agency-agents 生态集成 | `skillscripts/integration/agency_bridge.py` |
| **UX Integration 集成层** | ui-ux-pro-max 深度协同 | `skillscripts/integration/ux_integration.py` |
| **Platform Adapter** | PowerShell 7 原生适配 | `skillscripts/platform_adapter.py` |
| **Decision Log 系统** | 决策追溯与效果评估 | `skillscripts/core/decision_log.py` |
| **Workflow DSL 引擎** | YAML声明式工作流编排 | `skillscripts/core/workflow_dsl_engine.py` |

---

## v4.0 核心架构组件详解

### 1. 操作优先级控制器 (OperationPriorityController)

**核心理念**: Agent-First - 优先使用AI自主手动操作文件，而非依赖脚本或命令。

**三级优先级体系**:
```
Level 1: MANUAL (优先级1) - Agent自主手动操作
  ├─ 适用场景: 文件读写/编辑、代码重构、文档编写
  ├─ 批量操作也推荐在此级别
  └─ 优势: 最灵活、最安全、可追溯

Level 2: SCRIPT (优先级2) - 规划脚本操作  
  ├─ 适用场景: 重复性任务、复杂自动化工作流
  ├─ 批量操作降级至此级别
  └─ 优势: 可重复、可版本控制

Level 3: COMMAND (优先级3) - 终端命令操作
  ├─ 适用场景: 环境操作、依赖安装、系统配置
  ├─ 必须经过 preflight_check() 预演检查
  └─ 危险命令自动拦截 (rm -rf /, DROP TABLE, FORMAT C:)
```

**决策树规则** (6条核心规则):
```python
决策逻辑:
  IF (领域专家需求 AND 精确度要求高) → MANUAL
  ELIF (单文件编辑操作) → MANUAL
  ELIF (批量操作 AND 有可用脚本) → SCRIPT
  ELIF (批量操作 AND 无可用脚本) → SCRIPT
  ELIF (环境操作/依赖安装) → COMMAND
  ELSE → MANUAL
```

**预演检查机制** (preflight_check):
- 检测 22+ 危险命令模式
- 风险评估: LOW / MEDIUM / HIGH
- 影响范围分析: 文件数/磁盘占用/网络请求
- 生成安全建议和降级策略

---

### 2. 四维度输出防线 (FourDimensionalDefense)

**架构图**:
```
四维度输出防线
═══════════════

  输入 → [Layer1 Prompt] → [Layer2 Capability] → [Layer3 Rule] → [Layer4 Fallback] → 输出
            │                  │                  │                │
            ▼                  ▼                  ▼                ▼
       意图识别           技能匹配           规则校验         质量评分
       上下文注入         知识覆盖           安全扫描         自动回滚
       歧义消解           工具可用           性能基线         降级策略
       输入验证           能力缺口           合规审查         错误日志
```

**Layer1 PromptLayer - 意图理解与上下文注入**:
- 意图识别: 7种 IntentType (CODE_GENERATION/REFACTORING/DEBUGGING/DOCUMENTATION/TESTING/ANALYSIS/OTHER)
- 上下文自动注入: 项目结构/技术栈/编码规范/历史上下文
- 歧义消解: 识别模糊表述并主动澄清
- 输入验证: 格式检查、完整性验证

**Layer2 CapabilityLayer - 能力约束层**:
- 技能匹配度评估: 语义相似度计算 (推荐阈值 > 0.8)
- 知识库覆盖检查: 语言/框架/工具/概念 四维度覆盖 (目标 > 80%)
- 工具链验证: 依赖工具是否可用、版本兼容性
- 能力缺口识别: 识别当前能力不足并建议补充

**Layer3 RuleValidationLayer - 规则校验层**:
- 安全扫描: 11种安全模式 (SQL注入/XSS/命令注入/硬编码密钥等)
- 编码规范检查: 行长度/命名规范/docstring完整性/复杂度
- 性能基准对比: 响应时间/内存占用/CPU使用率对比历史基线
- 合规审查: OWASP Top 10 / GDPR / 行业标准

**Layer4 FallbackRecoveryLayer - 兜底恢复层**:
- 质量评分: 5维度×5分制 (完整性/准确性/清晰度/可操作性/安全性)
  - 阈值: ≥3.5/5.0 通过, <3.5 触发降级
- 自动回滚: 创建回滚点, 质量不达标时自动恢复
- 降级策略: 5种 FallbackStrategy (ROLLBACK/DEGRADE/ESCALATE/RETRY/ABORT)
- 错误日志记录: 根因分析、影响范围、修复建议

---

### 3. MARC-Lite 资源协调器 (ResourceCoordinator)

**核心理念**: 解决多Agent并发执行时的资源抢占、死锁、饥饿问题。

**架构图**:
```
MARC-Lite (Multi-Agent Resource Coordinator Lite)
══════════════════════════════════════════════════

  ResourceRegistry (资源注册中心)
  ├─ 5种资源类型: FILE / API / COMPUTE / TERMINAL / SECRET
  └─ 按类型索引的快速查找

  LockManager (锁管理器)
  ├─ SHARED (共享读锁) - 多Agent并发读
  ├─ EXCLUSIVE (独占写锁) - 互斥写操作
  ├─ 乐观锁/悲观锁 双模式
  └─ 5s间隔自动过期清理线程

  SchedulerQueue (调度队列)
  ├─ heapq优先级队列 (HIGH > MEDIUM > LOW)
  ├─ 公平调度 (单Agent最多连续10次)
  ├─ 批处理合并 (5任务/1秒窗口)
  └─ 抢占式调度 (高优先级可插队)

  DeadlockPreventer (死锁预防器)
  ├─ 等待图DFS环检测 (5s间隔)
  ├─ 受害者选择算法 (hold_count*10 + wait_time)
  └─ 自动Agent回滚恢复

  QuotaManager (配额管理器)
  ├─ per-Agent配额 (files/api_calls/cpu/memory)
  ├─ Global全局限制 (active_agents/total_resources)
  └─ 使用率监控 + 超限告警
```

**使用示例**:
```python
from skillscripts.core.resource_coordinator import ResourceCoordinator, ResourceType, LockType

marc = ResourceCoordinator()

# 注册资源
marc.register_resource("src/main.py", ResourceType.FILE)
marc.register_resource("https://api.example.com", ResourceType.API)

# 使用上下文管理器获取资源 (推荐方式)
with marc.acquire_context(
    resource_id="src/main.py",
    agent_id="code-reviewer",
    lock_type=LockType.SHARED
) as ctx:
    # 在此上下文中安全地读取文件
    content = read_file("src/main.py")
    # ... 执行审查逻辑 ...
    # 离开上下文时自动释放锁

# 查看状态面板
report = marc.get_status()
print(report.to_panel())
```

**命令行用法**:
```bash
# 查看MARC状态面板
python skillscripts/core/resource_coordinator.py --status

# 注册新资源
python skillscripts/core/resource_coordinator.py \
  --register --resource-id "config.yaml" --type file

# 模拟多Agent竞争场景测试
python skillscripts/core/resource_coordinator.py \
  --simulate --agents 5 --tasks 20
```

---

### 4. 密钥管理系统 (SecretsManager + HardcodedDetector)

**SecretsManager - 统一密钥管理**:
- 8种密钥类型: PASSWORD/API_KEY/TOKEN/SECRET/CREDENTIAL/CONNECTION_STRING/PRIVATE_KEY/ENCRYPTION_KEY
- 多源加载链: `.env` → `.env.local` → `os.environ` → `defaults` (手动解析, 不依赖python-dotenv)
- 类型安全访问: `get()` / `get_required()` + 审计日志
- 日志脱敏: `mask_for_log()` 保留首尾2字符, 中间替换为 `****`
- 强度验证: 密码长度≥8、非空、无占位符、无弱模式、连接串协议、PEM标记

**HardcodedDetector - 硬编码检测引擎**:
- 25种内置正则模式, 5组:
  - Group1: 密码/API Key/Token/Secret (HW-001~HW-010)
  - Group2: 连接字符串 (HW-011~HW-014)
  - Group3: 云/AI服务密钥 AWS/GitHub/Slack/OpenAI/Anthropic (HW-015~HW-018)
  - Group4: 私钥/Base64/JWT/随机串 (HW-019~HW-022)
  - Group5: IP地址/端口/HTTP Basic Auth (HW-023~HW-025)
- 支持26种文件扩展名扫描, 跳过19个目录
- SARIF v2.1.0 JSON导出 + Markdown报告导出

**使用示例**:
```python
from skillscripts.security.secrets_manager import SecretsManager
from skillscripts.security.hardcoded_detector import HardcodedDetector

# SecretsManager 使用
sm = SecretsManager()
sm.load()  # 多源加载

db_url = sm.get_required("DATABASE_URL")
api_key = sm.get("API_KEY", default="dev-key")

# 日志中自动脱敏
logger.info(f"DB连接: {sm.mask_for_log(db_url)}")

# HardcodedDetector 使用
detector = HardcodedDetector()
report = detector.scan_directory("./src")

# 导出报告
detector.export_report_sarif(report, "reports/security.sarif")
detector.export_report_markdown(report, "reports/security_scan.md")

# 检查严重问题
critical_count = sum(1 for f in report.files for finding in f.findings 
                        if finding.severity in ["CRITICAL", "HIGH"])
if critical_count > 0:
    raise SecurityError(f"发现{critical_count}个严重安全问题!")
```

---

### 5. Agency Bridge 桥接层

**核心理念**: 打通 `.trae/skills/agency-agents/` 中144+专业智能体, 实现跨生态协同。

**架构图**:
```
Agency Bridge
════════════

  Agent注册表扫描
  ├─ 遍历 agency-agents 目录
  ├─ 解析 YAML frontmatter 元数据
  └─ 索引所有可用 Agent (按domain分类)

  SmartRouter 智能路由
  ├─ 20+ 关键词 → Agent 映射 (TASK_KEYWORD_MAPPING)
  ├─ 任务描述分析 + 模糊匹配
  └─ 推荐最优 Agent 组合 (含置信度)

  Agent 调用接口
  ├─ invoke_agent() - 同步调用
  ├─ invoke_agents_parallel() - 并行调用 (ThreadPoolExecutor)
  ├─ 可选集成 MARC 资源协调
  └─ 上下文传递 + 结果收集

  ResultAggregator 结果整合
  ├─ 多Agent输出收集
  ├─ 冲突检测 (modification_conflict / suggestion_conflict / severity_mismatch)
  ├─ 冲突解决策略
  └─ 生成综合报告

  Sanliu→Agency 映射矩阵
  ├─ 中书省6局 → Agency Agents
  ├─ 门下省5局 → Agency Agents
  └─ 尚书省11局 → Agency Agents (共22个映射关系)
```

**使用示例**:
```python
from skillscripts.integration.agency_bridge import AgencyBridge

bridge = AgencyBridge()

# 推荐最优 Agent 组合
recommendations = bridge.recommend_agents(
    task_description="全栈代码审查: 前端React + 后端Python FastAPI + 安全审计"
)
for rec in recommendations:
    print(f"[{rec.confidence:.1%}] {rec.agent_id}: {rec.reason}")

# 并行调用多个 Agent (集成MARC)
results = bridge.invoke_agents_parallel(
    agent_ids=[r.agent_id for r in recommendations[:4]],
    task=f"审查项目 ./my-project",
    use_marc=True,  # 启用MARC资源协调
    context={"project_path": "./my-project"}
)

# 整合结果 (含冲突检测)
aggregated = bridge.aggregate_results(results)
report = aggregated.to_markdown()
print(report)
```

---

### 6. UX Integration 集成层

**核心理念**: 与 `ui-ux-pro-max` 技能深度协同, 实现设计驱动开发。

**核心能力**:
- 设计系统生成: 调用 `ui-ux-pro-max --design-system` 生成产品定制化设计系统
- UX规则查询: 按11个domain (accessibility/responsive/dark_mode/animation等) 搜索99+规则
- UI代码验证: 对照UX指南检查代码质量
- 交付前检查清单: visual/interaction/dark-mode/layout/accessibility 五维度检查

**使用示例**:
```python
from skillscripts.integration.ux_integration import UXIntegration

ux = UXIntegration()

# 生成设计系统
design_system = ux.generate_design_system(
    product_type="admin dashboard saas data-dense",
    keywords="real-time monitoring analytics"
)
print(design_system.to_markdown())

# 查询特定领域规则
rules = ux.search_ux_rules(domain="accessibility", query="contrast ratio color blind")
for rule in rules:
    print(f"[{rule.category}] {rule.title}: {rule.description}")

# 交付前检查
checklist = ux.get_pre_delivery_checklist()
for item in checklist:
    print(f"[{'✓' if item.checked else ' '}] {item.category} - {item.description}")
```

---

### 7. Platform Adapter 平台适配器

**核心理念**: PowerShell 7 原生支持 + 跨平台兼容。

**核心能力**:
- ShellType枚举: POWERSHELL_7 / BASH / WSL / CMD / UNKNOWN
- EncodingType枚举: 8种编码类型 (UTF-8/UTF-16/ASCII/GBK等)
- 跨平台Shell检测: 自动识别当前运行环境
- Bash↔PS7命令转换: 20个常用命令映射表
- UTF-8 BOM/NoBOM编码格式验证

**使用示例**:
```python
from skillscripts.platform_adapter import PlatformAdapter

adapter = PlatformAdapter()

# 检测环境
env_info = adapter.detect_environment()
print(f"当前Shell: {env_info.shell_type}")
print(f"编码格式: {env_info.encoding}")

# 命令转换
bash_cmd = "ls -la"
ps7_cmd = adapter.adapt_command(bash_cmd, target_shell="POWERSHELL_7")
print(f"Bash: {bash_cmd}")
print(f"PS7:   {ps7_cmd}")  # Get-ChildItem -Force

# 编码验证
encoding_report = adapter.validate_file_encoding("src/main.py")
if not encoding_report.is_utf8_no_bom:
    adapter.fix_encoding("src/main.py", target_encoding="UTF-8", remove_bom=True)
```

---

### 8. Decision Log 决策日志系统

**核心理念**: 透明化决策链路, 支持效果评估与统计分析。

**数据结构**:
```python
DecisionRecord:
  id: "DEC-YYYYMMDD-NNN"  # 决策ID
  title: string              # 决策标题
  content: string            # 决策内容详情
  rationale: List[str]       # 决策依据 (为什么这么做)
  alternatives: List[Dict]   # 备选方案 (做了哪些考虑)
  selected_option: int       # 选中的方案索引
  impact_scope: List[str]    # 影响范围
  maker: string              # 决策制定者 (哪个司/局)
  evaluation_plan: string    # 评估计划 (何时/如何验证)

EvaluationResult:
  effectiveness_score: float # 效果评分 0.0 ~ 1.0
  lessons_learned: string    # 经验教训
  would_repeat: bool         # 是否会再做同样的决定
  actual_outcome: string     # 实际结果
  evaluated_at: datetime     # 评估时间
```

**使用示例**:
```python
from skillscripts.core.decision_log import DecisionLog

decisions = DecisionLog(output_dir="docs/logs/decision_logs/")

# 记录决策
record = decisions.generate(
    title="采用FastAPI而非Flask作为Web框架",
    content="对于用户认证微服务的技术选型...",
    rationale=["异步原生支持", "自动OpenAPI文档", "团队熟悉度高"],
    alternatives=[
        {"option": "FastAPI", "pros": ["异步", "自动文档"], "cons": ["较新"]},
        {"option": "Flask", "pros": ["成熟"], "cons": ["需手动配置"]},
    ],
    selected_option=0,
    impact_scope=["backend", "api-design"],
    maker="架构设计局-技术选型司",
    evaluation_plan="上线后3个月评估API性能和开发效率"
)
print(f"决策已记录: {record.id}")  # DEC-20260406-001

# 后评估
evaluation = decisions.evaluate_outcome(
    decision_id="DEC-20260406-001",
    effectiveness_score=0.9,  # 9/10分, 非常成功
    lessons_learned="FastAPI的选择非常正确...",
    would_repeat=True,
    actual_outcome="API性能超出预期, 开发效率提升40%"
)

# 查询和统计
recent = decisions.list_decisions(date_from="2026-04-01")
stats = decisions.get_statistics()
print(f"总决策数: {stats['total']}, 已评估: {stats['evaluated_count']}")
```

---

### 9. Workflow DSL 引擎

**核心理念**: YAML声明式工作流编排, 支持并行/串行/条件/单步四种步骤类型。

**StepType枚举**:
- PARALLEL: 并行执行子步骤 (ThreadPoolExecutor)
- SEQUENTIAL: 顺序执行子步骤
- CONDITIONAL: 条件分支执行 (支持10种运算符)
- SINGLE: 单步执行

**错误处理策略**:
- retry_with_backoff: 重试 (指数退避)
- fail_fast: 快速失败
- skip_and_continue: 跳过并继续
- escalate_to_human: 升级人工处理

**使用示例**:
```yaml
# workflow.yaml
name: sdd-tdd-fusion-pipeline
description: SDD规范驱动TDD的完整自动化流水线

steps:
  - name: clause_extraction
    type: single
    agent: bingbu-test-framework-si
    config:
      task: "运行ClauseExtractEngine提取可执行条款"
      
  - name: test_generation
    type: parallel
    steps:
      - name: unit_tests
        type: single
        agent: bingbu-tdd-execution-si
        config:
          task: "基于P0/P1条款生成单元测试骨架"
      - name: integration_tests
        type: single
        agent: bingbu-tdd-execution-si
        config:
          task: "基于API条款生成集成测试"
          
  - name: red_phase
    type: single
    agent: bingbu-tdd-execution-si
    config:
      task: "红阶段: 确认所有测试失败"
      
  - name: conditional_deploy
    type: conditional
    variable: test_coverage_pass
    operator: gte
    value: 0.95
    then_step:
      name: deploy_staging
      type: single
      agent: ops-engineer
    else_step:
      name: investigate_issues
      type: single
      agent: engineering-senior-developer

on_error: retry_with_backoff
```

```python
from skillscripts.core.workflow_dsl_engine import WorkflowDSLEngine

engine = WorkflowDSLEngine()

# 解析并验证工作流
with open("workflow.yaml", "r", encoding="utf-8") as f:
    workflow_yaml = f.read()

workflow = engine.parse_workflow(workflow_yaml)
validation = engine.validate_workflow(workflow)

if validation.is_valid:
    # 执行工作流
    result = engine.execute_workflow(workflow)
    print(f"工作流执行完成: {result.status.value}")
    for sr in result.step_results:
        print(f"  [{sr.status.value}] {sr.name}: {sr.duration_ms}ms")
```

---

## 相关文档

- [省部协调机制](provincial_coordination.md) - 三省协调详细说明
- [六部工作流程](department_workflow.md) - 六部协调与TDD流程
- [技能脚本协同](skill_script_coordination.md) - 子技能与脚本协同调用
- [持续演化系统](continuous_evolution.md) - 演化系统详细说明
- [架构原则技能](jiagou_yuanze.md) - 架构合规检查
- [路径配置管理](skill_path_management.md) - 路径管理详细说明
