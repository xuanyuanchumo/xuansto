# 省部协调机制

> 🏛️ **三省协同，六部联动** - 通过中书省、门下省、尚书省的协同工作，实现软件开发过程的规范化治理 | **v3.3.0: 集成CI/CD流水线与自动化报告**

---

## v3.3.0 更新

### 🔄 CI/CD集成增强

省部协调机制现已深度集成CI/CD自动化流水线：

```bash
# 在CI/CD流水线中自动触发三省协调
python skillscripts/core/provincial_coordinator.py \
  --coordinate \
  --task-id $TASK_ID \
  --ci-mode  # CI/CD模式，自动记录结果到报告
```

**新增功能**：
- ✅ 协调结果自动归档至 `docs/迭代版本/v{version}/`
- ✅ 质量门禁检查集成（覆盖率/缺陷数/安全扫描）
- ✅ 自动生成Markdown格式协调报告
- ✅ 支持GitHub Actions环境变量注入

### 📊 六维监控集成

协调流程新增六维质量数据采集：

| 监控维度 | 数据来源 | 采集时机 |
|----------|----------|----------|
| 代码质量 | 圈复杂度/重复率 | 刑部重构阶段 |
| 测试覆盖 | 覆盖率报告 | 兵部测试阶段 |
| 技术债务 | 债务追踪器 | 尚书省统筹阶段 |
| 性能基准 | 性能测试 | E2E测试阶段 |
| 安全合规 | Bandit/Safety | Security Scan Job |
| 文档质量 | 格式检查器 | 门下省审议阶段 |

---

## 概述

省部协调机制是三省六部技能的核心治理架构，通过中书省（决策制定）、门下省（审议监督）、尚书省（执行统筹）的协同工作，确保软件开发过程的规范性和高质量。

---

## 省部司协同调用

### 概述

省部司协同调用是通过 `provincial_coordinator.py` 脚本实现的三省六部自动化协同机制，支持任务创建、三省协调、六部分发和状态查询等核心功能。

### 协同调用流程

```
┌─────────────────────────────────────────────────────────────────────┐
│                     省部司协同调用流程                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐                                                   │
│  │  创建任务    │  python skillscripts/core/provincial_coordinator.py         │
│  │  --create    │    --type feature --description "任务描述"        │
│  └──────┬───────┘                                                   │
│         │                                                           │
│         ▼                                                           │
│  ┌──────────────┐                                                   │
│  │  三省协调    │  中书省(决策) → 门下省(审议) → 尚书省(执行)        │
│  │  --coordinate│                                                   │
│  └──────┬───────┘                                                   │
│         │                                                           │
│         ▼                                                           │
│  ┌──────────────┐                                                   │
│  │  六部分发    │  吏部→户部→礼部→兵部→工部→刑部                    │
│  │  --dispatch  │                                                   │
│  └──────┬───────┘                                                   │
│         │                                                           │
│         ▼                                                           │
│  ┌──────────────┐                                                   │
│  │  状态查询    │  查询任务执行状态和进度                            │
│  │  --status    │                                                   │
│  └──────────────┘                                                   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 三省协调流程

| 阶段 | 负责机构 | 核心操作 | 输出 |
|------|----------|----------|------|
| **决策制定** | 中书省 | 需求分析、架构设计、SDD规范定义 | 规格说明书、规范文件 |
| **方案审议** | 门下省 | 需求评审、架构合规检查、测试覆盖审查 | 审议意见书 |
| **执行统筹** | 尚书省 | 任务分发、TDD循环管理、进度跟踪 | 执行报告 |

### 六部分发流程

```
尚书省接收审议通过方案
        │
        ▼
┌───────────────────────────────────────────────────────────────┐
│                    六部分发时序                                │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  阶段1: 准备阶段                                              │
│  ├─ 吏部: 分配Agent角色、创建任务清单                         │
│  ├─ 户部: 配置环境资源、分配测试环境                          │
│  └─ 礼部: 制定编码规范、审查标准                              │
│                                                               │
│  阶段2: TDD循环 (红→绿→蓝)                                    │
│  ├─ 兵部 🔴: 编写测试用例 (红阶段)                            │
│  ├─ 工部 🟢: 实现代码 (绿阶段)                                │
│  └─ 刑部 🔵: 重构优化 (蓝阶段)                                │
│                                                               │
│  阶段3: 验收交付                                              │
│  └─ 各司协作完成最终交付                                      │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

### 各司协作接口

| 接口 | 功能 | 参数 | 返回 |
|------|------|------|------|
| `create_task` | 创建新任务 | type, description | task_id |
| `coordinate` | 执行三省协调 | task_id | 协调结果 |
| `dispatch` | 分发至六部 | task_id | 分发状态 |
| `query_status` | 查询任务状态 | task_id | 状态详情 |

### 使用示例

```bash
# 示例：开发用户认证模块

# 1. 创建任务
python skillscripts/core/provincial_coordinator.py \
  --create-task \
  --type feature \
  --description "开发用户认证模块，支持注册、登录、密码重置功能"

# 输出: Task created: TASK-2024-001

# 2. 执行三省协调
python skillscripts/core/provincial_coordinator.py \
  --coordinate \
  --task-id TASK-2024-001

# 输出: 
# 中书省: 需求分析完成 ✓
# 门下省: 审议通过 ✓
# 尚书省: 准备执行 ✓

# 3. 分发至六部
python skillscripts/core/provincial_coordinator.py \
  --dispatch \
  --task-id TASK-2024-001

# 输出:
# 吏部: 角色分配完成
# 户部: 环境配置完成
# 礼部: 规范制定完成
# 兵部: 测试用例编写中...
# 工部: 等待测试完成
# 刑部: 等待代码实现

# 4. 查询状态
python skillscripts/core/provincial_coordinator.py \
  --status \
  --task-id TASK-2024-001

# 输出:
# 任务状态: 进行中
# 当前进度: 45%
# 当前阶段: TDD循环 (红阶段)
# 负责部门: 兵部
```

---

## 三省协调机制详解

### 中书省 - 决策制定中心

#### 核心职责

- 📋 需求结构化分析
- 🏗️ 系统架构设计
- 📐 SDD 规范定义
- ✅ 验收测试设计

#### 工作模式

```
输入：原始需求
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│ 中书省处理流程                                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. 需求分析                                                │
│     • 需求结构化                                            │
│     • 可行性研究                                            │
│     • 风险评估                                              │
│     • 输出：需求规格说明书                                  │
│                                                             │
│  2. 架构设计                                                │
│     • 系统架构设计                                          │
│     • 模块划分                                              │
│     • 技术选型                                              │
│     • 输出：概要设计说明书                                  │
│                                                             │
│  3. SDD规范定义                                             │
│     • 接口规范                                              │
│     • 数据模型规范                                          │
│     • 行为规则规范                                          │
│     • 输出：SDD规范文件                                     │
│                                                             │
│  4. 验收测试设计                                            │
│     • 验收测试用例                                          │
│     • 测试场景                                              │
│     • 验收标准                                              │
│     • 输出：验收测试文档                                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
输出：规格说明书 + 规范文件 + 验收测试
```

#### 输出物

| 输出物 | 描述 | 格式 |
|--------|------|------|
| **需求规格说明书** | 结构化的需求文档 | Markdown |
| **概要设计说明书** | 系统架构和模块设计 | Markdown |
| **SDD规范文件** | 接口、数据模型、行为规范 | Markdown (sdd_*.md) |
| **验收测试文档** | 验收测试用例和标准 | Markdown |

---

### 门下省 - 审议监督中心

#### 核心职责

- ✍️ 需求完整性评审
- 🏗️ 架构合规性检查
- 📊 测试覆盖率审查
- 🚦 质量门禁把控

#### 工作模式

```
输入：中书省输出
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│ 门下省审议流程                                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. 需求评审                                                │
│     • 完整性检查                                            │
│     • 一致性检查                                            │
│     • 可追溯性检查                                          │
│     • 输出：需求评审报告                                    │
│                                                             │
│  2. 架构合规检查                                            │
│     • MVVM/MVC架构检查                                      │
│     • SOLID原则验证                                         │
│     • 简洁原则检查                                          │
│     • 输出：架构合规报告                                    │
│                                                             │
│  3. 测试覆盖审查                                            │
│     • 测试覆盖率检查                                        │
│     • 测试场景完整性                                        │
│     • 边界条件覆盖                                          │
│     • 输出：测试覆盖报告                                    │
│                                                             │
│  4. 质量门禁                                                │
│     • 综合质量评估                                          │
│     • 风险评估                                              │
│     • 通过/不通过决策                                       │
│     • 输出：审议意见书                                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
    │
    ├─→ 不通过 ──→ 返回中书省修改
    │
    ▼ 通过
输出：审议意见书
```

#### 审议维度

| 维度 | 检查内容 | 通过标准 |
|------|----------|----------|
| **需求完整性** | 需求是否完整、清晰、可追溯 | 100% 覆盖 |
| **架构合规性** | 是否符合架构原则和设计规范 | 符合SOLID原则 |
| **测试覆盖率** | 测试用例是否覆盖所有场景 | 覆盖率 ≥ 80% |
| **质量门禁** | 综合质量是否达标 | 质量评分 ≥ 70分 |

---

### 尚书省 - 执行统筹中心

#### 核心职责

- ⚙️ 六部协调调度
- 🔄 TDD 循环管理
- 🔗 外部技能调用
- 📊 进度状态跟踪

#### 工作模式

```
输入：审议通过方案
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│ 尚书省执行流程                                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. 任务分解                                                │
│     • 分解为可执行任务                                      │
│     • 分配优先级                                            │
│     • 估算工作量                                            │
│     • 输出：任务清单                                        │
│                                                             │
│  2. 六部协调                                                │
│     • 吏部：角色分配                                        │
│     • 户部：资源分配                                        │
│     • 礼部：规范制定                                        │
│     • 兵部：测试先行                                        │
│     • 工部：代码实现                                        │
│     • 刑部：重构优化                                        │
│     • 输出：执行计划                                        │
│                                                             │
│  3. TDD循环管理                                             │
│     • 红阶段：测试先行                                      │
│     • 绿阶段：代码实现                                      │
│     • 蓝阶段：重构优化                                      │
│     • 输出：TDD循环报告                                     │
│                                                             │
│  4. 外部技能调用                                            │
│     • 识别外部技能需求                                      │
│     • 调用外部技能                                          │
│     • 整合调用结果                                          │
│     • 输出：技能调用记录                                    │
│                                                             │
│  5. 进度跟踪                                                │
│     • 实时进度监控                                          │
│     • 状态更新                                              │
│     • 异常处理                                              │
│     • 输出：进度报告                                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
输出：交付成果
```

#### 执行策略

| 策略 | 描述 | 适用场景 |
|------|------|----------|
| **顺序执行** | 按顺序依次执行各阶段 | 小型项目、简单任务 |
| **并行执行** | 多个任务并行执行 | 大型项目、独立模块 |
| **迭代执行** | 多轮迭代逐步完善 | 复杂项目、需求不明确 |
| **混合执行** | 结合多种策略 | 中大型项目 |

---

## 三省协作流程

### 完整协作流程

```
用户需求
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│ 中书省：需求分析 + SDD规范定义                               │
│ • 输出《需求规格说明书》                                     │
│ • 输出《SDD规范文件》                                        │
│ • 输出《验收测试用例》                                       │
└─────────────────────────────────────────────────────────────┘
    │
    ▼ 提交审议
┌─────────────────────────────────────────────────────────────┐
│ 门下省：方案审议                                             │
│ • 评审需求完整性 ✓/✗                                        │
│ • 评审架构合规性 ✓/✗                                        │
│ • 评审测试覆盖率 ✓/✗                                        │
│ • 输出《审议意见书》                                         │
└─────────────────────────────────────────────────────────────┘
    │
    ├─→ 不通过 ──→ 返回中书省修改
    │
    ▼ 通过
┌─────────────────────────────────────────────────────────────┐
│ 尚书省：执行统筹 + TDD循环                                   │
│ • 协调六部资源                                               │
│ • 管理红绿蓝循环                                             │
│ • 调用外部技能                                               │
│ • 输出《执行报告》                                           │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
交付成果
```

### 协作时序图

```
时间轴 ──────────────────────────────────────────────────────────→

用户需求
    │
    ├─ 中书省 ──────────────────────────────────────────────────┐
    │  • 需求分析                                                │
    │  • 架构设计                                                │
    │  • SDD规范定义                                             │
    │  • 验收测试设计                                            │
    │                                                            │
    └─ 提交审议 ────────────────────────────────────────────────┤
                                                               │
                                   门下省 ─────────────────────┤
                                   • 需求评审                  │
                                   • 架构合规检查              │
                                   • 测试覆盖审查              │
                                   • 质量门禁                  │
                                                               │
                                   审议通过 ───────────────────┤
                                                               │
                                                        尚书省 ─┤
                                                        • 任务分解
                                                        • 六部协调
                                                        • TDD循环
                                                        • 进度跟踪
                                                               │
                                                        交付成果 ─┘
```

---

## 协作最佳实践

### 1. 需求传递规范

```yaml
需求传递规范:
  格式:
    - 使用标准化的需求模板
    - 包含完整的验收标准
    - 附带必要的上下文信息
    
  内容:
    - 功能需求清晰明确
    - 非功能需求完整
    - 约束条件明确
    
  追溯:
    - 建立需求追溯链
    - 记录需求变更历史
    - 保持需求一致性
```

### 2. 审议反馈机制

```yaml
审议反馈机制:
  反馈格式:
    - 明确指出问题点
    - 提供改进建议
    - 标注优先级
    
  反馈周期:
    - 快速反馈：1小时内
    - 详细反馈：1天内
    - 复杂问题：3天内
    
  沟通渠道:
    - 文档批注
    - 会议讨论
    - 即时通讯
```

### 3. 执行协调原则

```yaml
执行协调原则:
  任务分配:
    - 按能力分配任务
    - 避免任务过载
    - 保持任务独立性
    
  进度同步:
    - 定期进度汇报
    - 实时状态更新
    - 异常及时上报
    
  质量保证:
    - 每个阶段都有质量检查
    - 问题及时发现和解决
    - 保持代码质量标准
```

---

## 相关文档

- [架构概览](architecture_overview.md) - 整体架构说明
- [六部工作流程](department_workflow.md) - 六部协调与TDD流程
- [技能脚本协同](skill_script_coordination.md) - 子技能与脚本协同调用
- [需求分析](xuqiu_fenxi.md) - 需求分析详细说明
- [系统设计](xitong_sheji.md) - 系统设计详细说明

---

## v4.0 更新

### 🔄 MARC-Lite 资源协调机制集成

v4.0 在三省协调机制中深度集成了 **MARC-Lite (Multi-Agent Resource Coordinator Lite)** 资源协调器，解决多Agent并发执行时的资源抢占、死锁、饥饿问题。

#### MARC-Lite 架构总览

```
MARC-Lite 资源协调器
═══════════════════════

  ┌─────────────────────────────────────────────────────┐
  │              ResourceCoordinator (统一门面)          │
  │           acquire_context() 上下文管理器              │
  └──────────────────────┬──────────────────────────────┘
                         │
  ┌──────────────────────┼──────────────────────────────┐
  │                      │                               │
  ▼                      ▼                               ▼
┌─────────────┐   ┌─────────────┐               ┌─────────────┐
│ResourceRegistry│   │ LockManager │               │SchedulerQueue│
│  资源注册中心  │   │  锁管理器    │               │  调度队列     │
│             │   │             │               │             │
│ 5种资源类型: │   │ SHARED读锁  │               │ 优先级队列    │
│ FILE/API/   │   │ EXCLUSIVE写 │               │ 公平调度     │
│ COMPUTE/    │   │ 乐观/悲观   │               │ 批处理合并   │
│ TERMINAL/   │   │ 自动过期    │               │ 抢占式支持   │
│ SECRET      │   │             │               │             │
└──────┬──────┘   └──────┬──────┘               └──────┬──────┘
       │                 │                              │
       │                 ▼                              │
       │         ┌─────────────┐                       │
       │         │DeadlockPreventer                    │
       │         │  死锁预防器  │                       │
       │         │ 等待图DFS检测│                       │
       │         │ 受害者选择   │                       │
       │         └──────┬──────┘                       │
       │                │                              │
       ▼                ▼                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    QuotaManager 配额管理器                   │
│  per-Agent配额 (files/api/cpu/memory) + Global全局限制     │
│  使用率监控 + 超限告警                                     │
└─────────────────────────────────────────────────────────────┘
```

#### 资源类型说明

| 资源类型 | 用途 | 锁模式 | 典型场景 | 三省中的使用 |
|----------|------|--------|----------|-------------|
| **FILE** | 文件读写 | SHARED读 / EXCLUSIVE写 | 代码审查、文件修改 | 门下省代码审查局、尚书省工部 |
| **API** | API端点调用 | 并发限制控制 | 外部服务调用 | 尚书省户部-基础设施司 |
| **COMPUTE** | CPU/内存计算 | 配额限制 | 大规模计算任务 | 尚书省工部-数据库设计司 |
| **TERMINAL** | 终端会话 | EXCLUSIVE互斥 | 命令执行 | 吏部-Agent调度司 |
| **SECRET** | 密钥资源 | READ_ONCE | 密钥加载 | 尚书省户部-环境配置司 |

#### 在三省协调流程中的MARC集成点

```
三省协调 + MARC 集成流程
═══════════════════════════

  【中书省 - 决策阶段】
  │
  ├─ 规范文件生成 → MARC注册 FILE 资源锁 (EXCLUSIVE)
  │   确保规范编写期间不被并发修改
  │
  └─ 决策记录 → DecisionLog系统集成
     记录每个重大决策的依据和影响范围

        ↓ 审议通过

  【门下省 - 审议阶段】
  │
  ├─ 并发代码审查 → MARC共享读锁 (SHARED)
  │   多个审查司同时读取同一文件
  │   ├─ 静态分析司 → 读锁 src/
  │   ├─ 安全扫描司 → 读锁 src/ (四维防线L3集成)
  │   └─ 性能审计司 → 读锁 src/
  │
  ├─ 测试验证 → MARC终端锁 (TERMINAL)
  │   测试执行环境互斥访问
  │
  └─ 质量监控 → 配额检查 (QuotaManager)
     确保不超过API调用和CPU限制

        ↓ 全部通过

  【尚书省 - 执行阶段】
  │
  ├─ 吏部(MARC) → 协调六部24司的资源竞争
  │   ├─ Agent调度司: 分配Agent角色, 注册任务资源
  │   ├─ 技能匹配司: 匹配最优Agent到任务
  │   └─ 协调司: 使用acquire_context统一协调
  │
  ├─ TDD循环 → 四维防线质量保障
  │   ├─ 🔴红阶段(兵部): L1 PromptLayer检查测试意图
  │   ├─ 🟢绿阶段(工部): L3 RuleValidationLayer检查代码
  │   └─ 🔵蓝阶段(刑部): L3+L4 重构后校验+兜底恢复
  │
  └─ 各司并行执行时:
     MARC自动处理:
     ├─ 锁竞争 → 排队等待或升级
     ├─ 死锁检测 → 选择受害者回滚
     └─ 配额超限 → 告警并降级
```

#### 使用示例：三省协同中使用MARC

```python
from skillscripts.core.resource_coordinator import ResourceCoordinator, ResourceType, LockType
from skillscripts.core.provincial_coordinator import ProvincialCoordinator

# 初始化MARC和省部协调器
marc = ResourceCoordinator()
coordinator = ProvincialCoordinator()

# === 场景1: 中书省规范编写时的资源保护 ===
def zhongshusheng_write_spec(spec_id):
    """中书省编写SDD规范时注册文件锁"""
    spec_path = f"specs/{spec_id}.yaml"
    
    marc.register_resource(spec_path, ResourceType.FILE)
    
    with marc.acquire_context(
        resource_id=spec_path,
        agent_id="zhongshusheng-guifan-zhiding-si",
        lock_type=LockType.EXCLUSIVE  # 独占写锁
    ):
        # 编写规范内容...
        content = write_spec_content(spec_id)
        
    return {"status": "spec_written", "path": spec_path}

# === 场景2: 门下省多司并发审查 ===
def menxiasheng_parallel_review(project_path):
    """门下省多个审查司并发审查同一项目"""
    
    review_agents = [
        "menxiasheng-daima-shenchajujing-taijifenxisi",   # 静态分析司
        "menxiasheng-daima-shenchajujing-anquansaomiaosi",   # 安全扫描司
        "menxiasheng-daima-shenchajujing-xingnengshenjisi",   # 性能审计司
    ]
    
    results = []
    
    for agent in review_agents:
        # 每个审查司获取共享读锁
        with marc.acquire_context(
            resource_id=project_path,
            agent_id=agent,
            lock_type=LockType.SHARED  # 共享读锁，允许并发读
        ):
            result = run_review_agent(agent, project_path)
            results.append(result)
    
    return {"status": "review_complete", "results": results}

# === 场景3: 尚书省TDD循环中的资源协调 ===
def shangshusheng_tdd_with_marc(task):
    """尚书省TDD循环集成MARC资源协调"""
    
    # Step 1: 吏部分配资源和Agent
    task_resources = coordinator.dispatch_to_liubu(task)
    
    for res in task_resources:
        marc.register_resource(res.path, ResourceType.FILE)
    
    # Step 2: 兵部红阶段 - 测试编写(可并行)
    with marc.acquire_context("test_files", "bingbu-tdd-zhixingsi", LockType.EXCLUSIVE):
        red_result = bingbu_red_phase(task)
    
    # Step 3: 工部绿阶段 - 代码实现
    with marc.acquire_context("src_files", "gongbu-daima-shengchengsi", LockType.EXCLUSIVE):
        green_result = gongbu_green_phase(task, red_result.test_cases)
    
    # Step 4: 刑部蓝阶段 - 重构优化
    with marc.acquire_context("src_files", "xingbu-chonggou-youhuasi", LockType.EXCLUSIVE):
        blue_result = xingbu_blue_phase(task, green_result.code)
    
    # Step 5: 查看MARC状态
    status_report = marc.get_status()
    print(status_report.to_panel())
    
    return {"red": red_result, "green": green_result, "blue": blue_result}
```

#### 命令行集成

```bash
# 在CI/CD流水线中启用MARC协调的三省工作流
python skillscripts/core/provincial_coordinator.py \
  --coordinate \
  --task-id $TASK_ID \
  --ci-mode \
  --enable-marc \                    # 启用MARC资源协调
  --marc-config configs/marc_config.yaml

# 单独查看MARC资源状态
python skillscripts/core/resource_coordinator.py --status

# 模拟高并发场景下的三省协作
python skillscripts/core/provincial_coordinator.py \
  --simulate-concurrent \
  --agents 8 \
  --tasks 30 \
  --with-deadlock-scenario
```

#### MARC配置示例

```yaml
# configs/marc_config.yaml
marc_lite:
  # 资源注册
  auto_register:
    - pattern: "src/**/*.py"
      type: file
    - pattern: "specs/**/*.yaml"
      type: file
    - pattern: "tests/**/*.py"
      type: file
      
  # 锁配置
  locks:
    default_timeout: 300        # 默认锁超时(秒)
    cleanup_interval: 5          # 过期锁清理间隔(秒)
    optimistic_enabled: true    # 启用乐观锁
    
  # 调度配置
  scheduler:
    fairness_threshold: 10      # 单Agent最大连续调度次数
    batch_window_seconds: 1    # 批处理时间窗口
    max_batch_size: 5           # 最大批处理任务数
    
  # 死锁预防
  deadlock:
    detection_interval: 5       # 检测间隔(秒)
    victim_selection: rollback_cost  # 受害者选择策略
    
  # 配额
  quotas:
    per_agent:
      max_file_locks: 10
      max_api_calls_per_minute: 60
      max_cpu_percent: 30
      max_memory_mb: 512
    global:
      max_active_agents: 10
      max_total_file_locks: 50
    alert_threshold: 0.8         # 80%使用率触发告警
```

#### 与其他v4.0模块的联动关系

```
MARC-Lite 联动关系
═════════════════

  OperationPriorityController
    ↓ 决定操作优先级后
  MARC-Lite 根据优先级分配资源
    ↓ 资源分配完成后
  FourDimensionalDefense 对输出进行质量检查
    ↓ 质量通过后
  AgencyBridge 可选集成MARC进行跨Agent协调
    ↓
  DecisionLog 记录资源协调相关决策
```
