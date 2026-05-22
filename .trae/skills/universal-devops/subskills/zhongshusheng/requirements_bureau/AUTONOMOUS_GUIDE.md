# 需求分析局 自主操作指南 (Autonomous Operation Guide)

## 概述

本指南指导 AI 如何在没有显式脚本调用的情况下，自主执行需求分析局的核心职责。需求分析局是中书省的"大脑前额叶"，负责将模糊的业务意图转化为精确、可执行、可验收的技术需求规格。

**核心使命**：从混沌的业务描述中提取结构化需求模型，确保每个需求都具备可验证性、可追踪性、可优先级排序性。

**自主能力边界**：
- 可自主完成：领域建模、用户故事提炼、优先级排序、验收标准生成
- 需要人工确认：业务目标对齐确认、非功能性需求取舍、最终优先级审批
- 禁止自主执行：删除或否定已确认的需求、修改业务战略方向

## 核心原则

1. **需求即契约**：每条需求必须包含明确的"谁、做什么、为什么、验收标准"
2. **模型驱动**：先建模型再写文档，DDD 战略建模是所有需求分析的起点
3. **渐进细化**：从 Epic → Feature → Story → Task 逐层拆解，禁止跳跃
4. **可追溯**：每个子需求必须能追溯到父需求和业务目标
5. **证据导向**：需求优先级必须有量化依据，拒绝"我觉得重要"

## 自主操作流程

### 阶段一：感知（Perceive）

AI 应收集和理解以下信息：

**信息收集清单**：
1. 业务上下文扫描
   - 项目现有代码结构和模块划分
   - 已有的 PRD / 文档 / Wiki
   - 数据库 Schema（理解当前数据模型）
   - API 接口列表（了解已有能力边界）
   - Git 提交历史（理解近期开发重点和趋势）
2. 用户意图解析
   - 识别显式需求（用户直接说出的）
   - 识别隐式需求（用户未说但必须有的）
   - 识别反模式需求（与系统设计原则冲突的需求）
3. 利益相关者画像
   - 谁提出的需求？（角色：产品/运营/技术/管理层）
   - 谁会使用该功能？（终端用户类型）
   - 谁会受影响？（上下游系统/依赖方）
4. 竞品/行业基准
   - 同类功能在竞品中的实现方式
   - 行业最佳实践参考

**输出产物**：`_perception_report.md` — 包含上下文摘要、关键发现、信息缺口标记

### 阶段二：决策（Decide）

基于感知结果进行以下决策：

**决策点 D1：需求分类**
```
输入：原始需求描述
├─ 功能型需求 → 进入 DDD 建模流程
├─ 非功能型需求 → 进入 NFR 分类矩阵
│   ├─ 性能需求 → 量化指标定义
│   ├─ 安全需求 → OWASP 映射
│   ├─ 可用性需求 → SLA 定义
│   └─ 可维护性需求 → 架构约束声明
└─ 边界需求 → 标记为假设条件
```

**决策点 D2：建模策略选择**
| 场景 | 建模方法 | 触发条件 |
|------|---------|---------|
| 新业务域 | 完整 DDD 战略建模 | 全新业务模块，无历史代码参考 |
| 已有域扩展 | 事件风暴 + 上下文映射 | 在现有 bounded context 内新增能力 |
| 重构场景 | 现状建模 + 目标建模对比 | 涉及核心域的重大变更 |
| 小功能增强 | 轻量聚合根分析 | 单一实体 CRUD 扩展 |

**决策点 D3：优先级方法论选择**
- MoSCoW 法：适用于需求量 < 20 条的场景
- RICE 加权法：适用于需求量 > 20 条且需要精细化排期的场景
- Kano 模型：适用于用户体验类需求的优先级判断
- WSJF（加权最短作业优先）：适用于敏捷迭代规划

### 阶段三：执行（Execute）

#### 3.1 DDD 战略建模完整流程

**步骤 1：领域识别**

扫描以下信号源来识别领域概念：
- 名词提取：从需求描述中提取所有业务名词
- 动词提取：提取业务动作（对应领域服务候选）
- 关系连线：名词之间的关联关系
- 约束提取：业务规则和不变量

输出：初始领域词汇表（Ubiquitous Language 候选词表）

**步骤 2：聚合根识别**

使用以下启发式规则识别聚合根：
```python
# 聚合根识别决策树
def identify_aggregate_root(entity):
    if entity.has_global_identity():
        if entity.is_lifecycle_owner():
            return "AGGREGATE_ROOT"
        elif entity.cannot_exist_independently():
            return "ENTITY (belongs to parent AR)"
        else:
            return "ENTITY (potential standalone AR)"
    else:
        if entity.is_value_object():
            return "VALUE_OBJECT"
        else:
            return "REVIEW_NEEDED"
```

关键判断标准：
- 是否有独立生命周期？→ 是则可能是聚合根
- 是否被其他实体引用其完整身份？→ 是则是聚合根
- 是否需要保证事务一致性边界？→ 是则必须是聚合根

**步骤 3：领域事件风暴**

事件风暴模板：
```markdown
## 领域事件：[事件名称]
- **触发者**：谁触发了这个事件？
- **触发条件**：什么条件下发生？
- **携带数据**：事件负载包含哪些字段？
- **订阅者**：哪些下游需要响应此事件？
- **幂等性要求**：是否需要去重处理？
```

事件命名规范：`[聚合根名] + [过去时动词]`
- 正例：OrderPlaced, PaymentCompleted, InventoryReserved
- 反例：PlaceOrder, DoPayment, ReserveInventory

**步骤 4：边界上下文划分（Bounded Context Mapping）**

上下文映射关系类型判定：
| 关系类型 | 判定标准 | 示例 |
|---------|---------|------|
| Shared Kernel | 共享的基础数据/工具库 | 共享的 User 类型定义 |
| Customer/Supplier | 上游提供API，下游依赖 | 支付服务 → 订单服务 |
| Conformist | 下游完全采用上游模型 | 认证服务 → 各微服务 |
| Anti-Corruption Layer | 需要翻译层隔离外部模型 | 第三方系统集成 |
| Open Host Service | 统一的公开协议 | 开放 API 平台 |
| Published Language | 双方约定的共享语言 | 跨团队接口契约 |

#### 3.2 用户故事自主提炼

用户故事模板（增强版 INVEST）：
```markdown
## User Story: [ID]
**作为** [角色]
**我希望** [功能]
**以便于** [价值]

### 验收标准 (Acceptance Criteria)
- AC1: Given ... When ... Then ...
- AC2: Given ... When ... Then ...

### 元数据
- 来源需求: [追溯到 PRD 或 Epic]
- 优先级: P0/P1/P2/P3
- 故事点: [估算值]
- 依赖项: [前置故事 ID 列表]
- 非功能约束: [性能/安全等标签]
```

验收标准编写规范（Given-When-Then 三段式）：
- Given：前置条件和已知状态（不可省略）
- When：触发动作（单一明确动作）
- Then：可观测的结果断言（可自动化测试）

#### 3.3 需求优先级自主排序

**MoSCoW 分类标准**：
| 类别 | 定义 | 占比建议 | 处理方式 |
|------|------|---------|---------|
| Must | 没有它系统无法上线 | ≤ 50% | 本迭代必做 |
| Should | 重要但可延后 | ≤ 30% | 下迭代优先 |
| Could | 有则更好 | ≤ 15% | 有空再做 |
| Won't | 本期不做但记录 | 其余 | 移入 Backlog |

**RICE 加权计算公式**：
```
RICE Score = (Reach × Impact × Confidence) / Effort

- Reach (触达范围): 受影响的用户数/请求数（0-100 归一化）
- Impact (影响程度): 3=大规模, 2=中等, 1=小规模, 0.25=微小
- Confidence (置信度): 100%=高, 80%=中, 50%=低
- Effort (工作量): 人周数为单位
```

RICE 排序示例：
| 需求 | Reach | Impact | Confidence | Effort | RICE |
|------|-------|--------|------------|--------|------|
| 用户注册优化 | 80 | 3 | 90% | 2 | 108 |
| 支付流程重构 | 60 | 3 | 70% | 8 | 15.75 |
| 后台报表导出 | 20 | 2 | 95% | 1 | 38 |

### 阶段四：验证（Verify）

**自检清单**：
- [ ] 每条需求都有唯一标识符和来源追溯
- [ ] 所有验收标准都符合 Given-When-Then 格式
- [ ] 聚合根之间无循环依赖
- [ ] 事件命名统一使用过去时态
- [ ] 优先级排序有量化依据（非主观判断）
- [ ] 非功能需求已单独列出并有量化指标
- [ ] 用户故事的 INVEST 原则全部满足
- [ ] 领域词汇表中无歧义词

**交叉验证机制**：
1. 与架构局交叉验证：需求中的实体关系是否与现有架构一致
2. 与审议局交叉验证：高风险需求是否已标记并评估
3. 与规范局交叉验证：需求是否隐含新的编码规范要求

### 阶段五：记录（Record）

**必须生成的文档**：
1. `PRD_v{version}.md` — 产品需求文档（主文档）
2. `domain_model.md` — DDD 领域模型（含 Mermaid 图）
3. `user_stories.md` — 用户故事列表及验收标准
4. `priority_matrix.md` — 优先级排序矩阵及依据
5. `context_map.md` — 上下文映射图
6. `glossary.md` — 统一语言词汇表

**可选生成文档**：
- `competitive_analysis.md` — 竞品分析报告
- `process_flow.md` — 业务流程图（Mermaid）
- `assumptions_log.md` — 假设条件日志

## 典型自主场景

### 场景 1：新业务模块需求分析

**触发条件**：用户提出一个全新的业务功能需求，如"我们需要一个会员积分系统"

**自主执行步骤**：
1. 感知阶段
   - 扫描项目中是否有现有的用户体系、订单系统可作为参照
   - 检查数据库中是否有 user/order 相关表
   - 搜索代码中是否有 loyalty/reward/point 相关实现
2. 决策阶段
   - 判定：这是一个全新 Bounded Context → 选择完整 DDD 战略建模
   - 判定：需求量预估 > 10 个 story → 使用 RICE 加权排序
3. 执行阶段
   - 提取领域词汇：Member, Point, Rule, Transaction, Tier, Expiration
   - 识别聚合根：Member(AR), PointAccount(AR), EarnRule(AR), RedemptionRule(AR)
   - 事件风暴：PointsEarned, PointsRedeemed, TierUpgraded, PointsExpired
   - 划分上下文：Membership Context（核心域）+ Integration Context（支撑域）
   - 编写用户故事（预计 12-18 个 story）
   - RICE 优先级排序
4. 验证阶段
   - 运行自检清单
   - 生成 Mermaid 领域模型图验证一致性
5. 记录阶段
   - 输出完整的 PRD 文档包

**预期输出**：
- 完整的 PRD 文档（含 6 个必需文件）
- 至少 10 条结构化用户故事
- Mermaid 格式的领域模型图和上下文映射图
- 量化的优先级排序矩阵

### 场景 2：已有功能的增强需求

**触发条件**：用户在现有功能上提出增量改进，如"购物车需要支持批量操作"

**自主执行步骤**：
1. 感知阶段
   - 定位现有 Cart 相关代码（entity, service, controller, repository）
   - 分析现有 Cart 的聚合根和数据模型
   - 检查 Cart 相关的现有 API 和前端调用
2. 决策阶段
   - 判定：在现有 Context 内扩展 → 使用轻量聚合根分析
   - 判定：需求量 < 5 个 story → 使用 MoSCoW 快速分类
3. 执行阶段
   - 识别变化点：Cart 新增 batchSelect/batchRemove/batchMove 方法
   - 识别新事件：CartItemsBatchUpdated
   - 提炼 3-5 个用户故事
   - MoSCoW 分类：Must(批量选中/移除) + Should(批量移到收藏) + Could(批量备注)
4. 验证阶段
   - 确认新功能不破坏现有 Cart 的事务边界
   - 确认批量操作的并发安全策略
5. 记录阶段
   - 输出精简版 PRD（聚焦变更部分）

**预期输出**：
- 变更需求文档（Change Request）
- 3-5 条用户故事及验收标准
- 对现有领域模型的影响分析

### 场景 3：竞品分析与差异化需求提炼

**触发条件**：用户要求"参考 XX 产品做一个类似的功能，但要更好"

**自主执行步骤**：
1. 感知阶段
   - 通过 WebSearch 收集竞品的功能特性信息
   - 分析竞品的公开 API 文档和技术博客
   - 整理竞品功能矩阵
2. 决策阶段
   - 使用 SWOT 框架分析竞品优劣
   - 识别差异化机会点
3. 执行阶段
   - 构建竞品功能对比矩阵
   - 从差异点反向推导用户故事
   - 为每个差异化需求标注创新等级
4. 验证阶段
   - 差异化需求的技术可行性评估
   - 差异化的投入产出比分析
5. 记录阶段
   - 输出竞品分析报告 + 差异化需求列表

**预期输出**：
- 竞品功能对比矩阵（表格形式）
- 差异化需求清单（含可行性评级）
- 推荐实施路径（MVP → 增强 → 差异化）

### 场景 4：非功能需求专项分析

**触发条件**：系统面临性能瓶颈或合规要求，如"系统需要支持 10K QPS 并通过等保三级"

**自主执行步骤**：
1. 感知阶段
   - 收集当前系统的性能基线数据
   - 分析现有架构的性能热点
   - 梳理合规要求的检查清单
2. 决策阶段
   - 将模糊的非功能需求分解为可量化的技术指标
   - 识别指标之间的冲突和权衡空间
3. 执行阶段
   - 构建 NFR 矩阵（需求类别 → 指标 → 目标值 → 当前值 → Gap）
   - 为每个 NFR 关联到具体的功能需求
   - 生成性能测试用例和安全检查点
4. 验证阶段
   - 指标的可达性分析（是否有足够的技术手段达成）
   - 成本效益评估
5. 记录阶段
   - 输出 NFR 规格说明书
   - 性能/安全测试计划

**预期输出**：
- NFR 矩阵（含量化指标）
- 性能/安全测试方案
- 技术债务影响评估

## 决策框架

### 需求完整性决策树

```
开始
├─ 需求描述是否清晰？
│   ├─ 否 → 发起澄清对话（OpenClaude 模式）
│   │   └─ 最多 3 轮澄清后仍不清晰 → 标记为"需人工介入"
│   └─ 是 ↓
├─ 是否涉及全新业务域？
│   ├─ 是 → 启动完整 DDD 建模流程
│   └─ 否 → 启动轻量分析流程 ↓
├─ 需求数量是否 > 20？
│   ├─ 是 → 使用 RICE 加权排序
│   └─ 否 → 使用 MoSCoW 快速分类 ↓
├─ 是否存在跨系统依赖？
│   ├─ 是 → 生成上下文映射图 + 接口契约草案
│   └─ 否 ↓
├─ 是否涉及敏感数据处理？
│   ├─ 是 → 触发安全需求专项分析
│   └─ ↓
└─ 生成完整需求交付物包
```

### 需求冲突解决框架

当两条需求产生冲突时的处理顺序：
1. **功能 vs 非功能冲突**：非功能需求（安全/合规）> 功能需求
2. **Must vs Should 冲突**：Must 优先，Should 降级或延期
3. **不同利益相关者冲突**：提交审议局仲裁
4. **技术可行性冲突**：联合架构局评估替代方案

## 安全与治理

### 风险评估标准

| 风险等级 | 判定标准 | 处理方式 |
|---------|---------|---------|
| Critical | 涉及资金交易、个人敏感数据、核心业务逻辑 | 必须人工审核 + 审议局评审 |
| High | 涉及权限变更、数据迁移、第三方集成 | 需人工确认 + 架构局会签 |
| Medium | 涉及 UI 交互变更、新增查询功能 | AI 自主完成 + 结果通知 |
| Low | 文案调整、日志格式优化 | AI 全自主 |

### 审批门禁条件

以下情况必须暂停自主执行，请求人工确认：
- 需求涉及删除已有功能或废弃已有 API
- 需求涉及数据库 Schema 变更（DDL 操作）
- 需求涉及对外部系统的契约变更
- 需求的优先级分配与用户预期明显不符
- 发现需求中存在逻辑矛盾无法自行解决

### 回滚策略

- 所有需求文档使用语义化版本号管理（v1.0.0）
- 每次重大变更保留快照（git tag）
- 需求变更日志自动追加到 `CHANGELOG.md`
- 如果需求分析方向错误，回退到上一版本重新启动感知阶段

## 与其他司/局的协作关系

### 与架构设计局的协作

**上游关系（需求局 → 架构局）**：
- 需求局输出的领域模型是架构局进行技术设计的输入
- 需求局定义的 Bounded Context 直接映射到架构局的模块划分
- 需求局的事件清单决定架构局的消息队列设计

**协作接口**：
```
需求局输出                    架构局输入
──────────                   ──────────
domain_model.md       →      技术选型和模块划分依据
context_map.md        →      服务边界和通信模式
event_list.md         →      事件驱动架构设计
NFR_spec.md           →      非功能架构约束
user_stories.md       →      API 接口设计输入
```

**反馈回路**：架构局如果发现需求在技术上不可行，应通过 ADR 形式反馈给需求局，需求局据此调整需求或寻找替代方案。

### 与规范制定局的协作

**双向关系**：
- 需求局在提炼用户故事时，应参考规范局的编码规范确保验收标准的可实现性
- 规范局根据需求局的新需求类型，主动更新相关编码规范

**典型协作场景**：
- 需求引入了新的数据类型 → 规范局更新命名约定
- 需求引入了新的安全要求 → 规范局更新安全编码 Checklist
- 需求引入了新的 API 模式 → 规范局更新 RESTful API 设计规范

### 与方案审议局的协作

**下游关系（需求局 → 审议局）**：
- 高风险需求（Critical/High 级别）必须提交审议局评审
- 需求优先级的最终争议由审议局仲裁
- 跨系统需求的影响范围评估由审议局主导

**触发审议的条件**：
- 单个需求的 RICE 分数方差超过阈值
- 存在 Must 级需求超过总量的 60%（资源过载预警）
- 需求之间存在无法调和的目标冲突

---

## 🤝 v5.1 增强：Agency Agent 协作指南

### 可调用的 Agency Agents

本局可通过 Agency-Agent Bridge 调用以下专业智能体：

| Agent 名称 | 所属部门 | 协作模式 | 适用场景 |
|-----------|---------|---------|---------|
| Product Manager | Product Division | primary | PRD 评审、需求优先级对齐、用户价值验证 |
| Sprint Prioritizer | Product Division | supporting | 迭代规划、Backlog 排序、容量评估 |
| Trend Researcher | Research Division | consulting | 竞品分析、行业趋势调研、差异化机会识别 |
| Feedback Synthesizer | Customer Success Division | supporting | 用户反馈聚合、NPS 分析、痛点挖掘 |
| Behavioral Nudge Engine | Growth Division | consulting | 用户行为引导设计、转化率优化策略 |

### Agent 协作工作流

1. **任务接收** → 本局分析需求并判断是否需要外部Agent协作
2. **Agent选择** → 通过Agent Router匹配最优Agent组合
3. **上下文构建** → 为Agent准备项目背景、领域模型、约束条件、期望产出
4. **协作执行** → 与Agent协同工作（主从/并行/咨询三种模式）
5. **结果整合** → 收集Agent输出，与本局分析结果合并
6. **质量审核** → 提交门下省对应局进行最终审核

### 典型协作场景

- **PRD 评审增强**：当收到产品方提交的PRD时，本局先完成结构化需求建模，再调用 Product Manager Agent 进行独立视角的完整性审查和商业可行性评估，两者结果合并后生成增强版评审报告。
- **竞品深度分析**：在进行竞品分析与差异化需求提炼场景中，调用 Trend Researcher Agent 进行多维度市场扫描和技术趋势追踪，结合本局的 SWOT 框架分析，产出差异化的创新需求清单。

---

## 🏗️ v5.1 增强：Harness 工程实践

### 相关 Harness 模块

- **Feature Flags（功能开关）**：功能开关的需求定义与验收标准编写
- **SLO / SLI（服务等级目标）**：可用性/性能需求的量化定义与跟踪
- **Pipeline（CI/CD 流水线）**：需求驱动测试（DDT）的流水线集成

### 实践指南

- **Feature Flags 需求定义规范**：每个涉及功能开关的需求必须在 PRD 中明确开关名称、默认值、灰度策略、回滚条件和监控指标，确保开关的生命周期可追溯。
- **SLO 驱动的非功能需求**：将可用性目标（如 99.9% uptime）转化为具体的 NFR 矩阵条目，关联到对应的用户故事验收标准，并在 Harness SLO Dashboard 中配置对应的 Error Budget 策略。
- **需求变更与 Pipeline联动**：重大需求变更触发回归测试范围自动评估，通过 Harness Pipeline 的 Stage 条件执行机制实现按需扩展测试覆盖。

### 配置参考

```yaml
# harness_config.yaml - 需求局相关配置片段
featureFlags:
  requirementDefinition:
    template: |
      ## Feature Flag: {flag_name}
      - **标识符**: {flag_key}
      - **默认值**: {default_value}
      - **所属 Epic**: {epic_id}
      - **灰度策略**: {rollout_strategy}
      - **验收标准**:
        - AC1: Given 开关开启 When 用户访问 Then 展示新功能
        - AC2: Given 开关关闭 When 用户访问 Then 保持原有行为
      - **监控指标**:
        - usage_rate: 功能使用率
        - error_rate: 错误率对比
        - conversion_impact: 转化率影响
    validation:
      uniqueKey: true
      epicLinkRequired: true

slo:
  requirementMapping:
    availabilityTarget:
      pattern: "^\\d+\\.?\\d*%$"
      mappingToNFR: "availability_requirement"
    errorBudgetPolicy:
      burnRateAlert:
        threshold: 2.0
        window: 1h
        action: "notify_requirements_bureau"

pipeline:
  requirementDrivenTest:
    stageName: "Requirement Validation"
    condition: "${requirement.change_scope} == 'major'"
    steps:
      - name: "Regression Scope Assessment"
        type: "Run"
        spec: |
          assess_regression_scope(
            changed_stories=${requirement.changed_stories},
            impact_analysis=${requirement.impact_map}
          )
```

---

## 🆕 v6.0 增强能力集成

### 四维度输出防线检查点

本局的输出需要通过以下防线层级检查：

| 防线层级 | 本局适用性 | 检查项 | 配置位置 |
|---------|-----------|--------|----------|
| **第一维：提示词工程层** | ✅ 适用 | 角色人格一致性：本局输出风格是否符合需求分析的专业规范（结构化、可验证、可追溯） | `configs/output_defense_config.yaml → prompt_engineering.role_consistency` |
| **第二维：能力约束层** | ✅ 适用 | 工具权限：本局操作是否在允许的工具白名单内（文件读写、代码扫描、Web搜索） | `configs/output_defense_config.yaml → capability_guard.permissions` |
| **第三维：规则校验层** | ✅ 适用 | 输出格式：本局产出的PRD、用户故事、领域模型是否符合Schema定义（Markdown结构、必需章节完整性） | `configs/output_defense_config.yaml → rule_validation.schema_validation` |
| **第四维：兜底恢复机制** | ⚠️ 备用 | 当本局输出不达标时，降级策略：精简版需求文档→骨架结构→错误提示+人工介入 | `configs/output_defense_config.yaml → fallback_recovery` |

### MARC资源协调注意事项

当本局与其他局/司并发工作时，需注意：

- **资源申请**：如需访问共享文档（如架构局的ADR、规范局的编码标准），应通过MARC锁管理器申请
- **Decision Log记录**：本局做出的重要决策（如需求优先级排序、建模策略选择）必须记录到Decision Log中
- **冲突预防**：避免与架构局同时修改同一领域的模型定义文件；避免与审议局同时评审同一批需求

### 操作优先级指引（v6.0核心）

本局推荐的操作方式优先级：

1. 🥇 **Agent自主手动操作**（首选）
   - 直接使用文件读写工具创建/修改PRD文档、用户故事、领域模型图
   - 适用场景：单文件编写、文档结构调整、内容审核批注、DDD模型绘制
   
2. 🥈 **规划脚本操作**（次选）
   - 调用 `skillscripts/open_source_philosophy/opencode_transparency.py` 生成Decision Log
   - 调用 `skillscripts/skill_standardization/metadata_validator.py` 验证文档格式合规性
   
3. 🥉 **命令操作**（最后选择，需预演）
   - 仅在需要批量生成报告或执行环境检测时使用
   - 执行前必须运行后果预演确认安全性

### Decision Log 记录要求

作为**需求分析局**，以下类型的决策必须自动记录到Decision Log：

- 需求分类决策（功能型/非功能型/边界需求的判定及理由）
- 建模策略选择（完整DDD建模/轻量分析/事件风暴的选型依据）
- 优先级排序结论（MoSCoW分类结果或RICE评分及排序理由）
- 需求冲突解决记录（当存在目标冲突时的取舍决策和依据）
- 风险评估结论（Critical/High/Medium/Low风险等级的评定理由）

- Decision Log存储路径：`docs/logs/decision_logs/`
- 日志命名规则：`{YYYY-MM-DD}_REQ_decisions.md`

### PowerShell 7 适配说明

本局相关脚本在PS7环境下的注意事项：
- 路径分隔符：使用 `/` 或 `\` 均可，系统自动转换
- 编码保证：所有输出文件（PRD、用户故事、领域模型）使用 UTF-8 无 BOM 编码
- 如需执行终端命令（如运行代码扫描工具），使用 `platform/powershell_adapter.py` 进行转换
