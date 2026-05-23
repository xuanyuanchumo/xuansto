# 人机协作断点交互规范

<!-- version: 2.0.0 | 编码: UTF-8 -->

> 本文档定义了 Xuansto Skill 多Agent自主开发编排器中人机协作断点的完整交互规范，
> 涵盖断点分类、通知机制、超时处理、决策分级和度量指标。

## 1. 决策检查点类型

人机协作过程中，系统在以下五类关键节点暂停执行并请求人工决策：

### 1.1 安全确认（SECURITY_GATE）

涉及生产环境部署、密钥操作、数据删除等高风险操作时触发。

触发条件：
- 向生产环境执行部署操作
- 创建、修改或删除密钥、证书、令牌等敏感凭证
- 执行不可逆的数据删除操作（DROP TABLE、删除文件等）
- 修改安全策略或访问控制配置
- 执行涉及外部服务的写操作（支付、通知、邮件发送等）
- 数据库迁移中包含破坏性变更

决策选项：
- `PROCEED`：确认执行，继续操作
- `ABORT`：终止当前操作
- `MODIFY`：修改操作参数后重新提交
- `ESCALATE`：升级至更高级别审核

### 1.2 架构决策（ARCHITECTURE_DECISION）

涉及技术栈选择、系统架构变更、API设计等重大决策时触发。

触发条件：
- 引入新的依赖库或框架
- 变更系统架构模式（如单体→微服务、REST→GraphQL）
- 修改公共API接口（新增、删除、变更签名）
- 数据模型变更（新增表、修改字段类型、变更关联关系）
- 变更通信协议或数据序列化格式
- 性能关键路径的实现方案选择

决策选项：
- `APPROVE`：批准当前方案
- `REJECT`：否决当前方案，要求重新设计
- `ALTERNATIVE`：提供替代方案供选择
- `DEFER`：推迟决策，标记为待定

### 1.3 需求歧义（REQUIREMENT_AMBIGUITY）

需求描述存在多种理解，需要用户明确意图时触发。

触发条件：
- 需求描述中存在模糊术语或歧义表述
- 同一需求在不同上下文中存在矛盾
- 用户意图可映射为两种或以上不同的实现路径
- 隐含的业务规则未明确说明
- 非功能性需求缺失（性能、安全、兼容性等）

决策选项：
- `CLARIFY`：提供澄清后的需求描述
- `CHOOSE_OPTION`：从系统提供的候选理解中选择
- `PROVIDE_CONTEXT`：补充上下文信息以消除歧义
- `SKIP`：跳过歧义部分，后续再处理

### 1.4 迭代不收敛（ITERATION_DIVERGENCE）

连续3次迭代未通过质量门禁，需要人工判断方向时触发。

触发条件：
- 同一任务连续3次迭代未通过质量门禁
- 修复一个问题导致另一个问题出现的循环
- 测试覆盖率在多次迭代后仍不达标
- 性能优化后回归测试失败超过2次
- 代码审查意见在迭代中反复出现

决策选项：
- `RESET_PHASE`：重置当前Phase，从规格重新出发
- `CHANGE_APPROACH`：更换实现策略
- `RELAX_CRITERIA`：调整质量门禁标准（需说明理由）
- `ESCALATE_REVIEW`：请求更深入的代码审查
- `PAUSE`：暂停任务，等待外部资源或信息

### 1.5 规格漂移（SPEC_DRIFT）

实现偏离规格定义，需要确认是否为有意的规格演进时触发。

触发条件：
- 实现代码与规格文档描述不一致
- 新增了规格中未定义的功能或行为
- 规格中定义的功能被省略或替换
- 接口契约与规格定义存在偏差
- 数据结构或算法与规格描述不同

决策选项：
- `UPDATE_SPEC`：确认漂移为有意的规格演进，更新规格文档
- `ROLLBACK_IMPL`：回滚实现以符合原始规格
- `PARTIAL_ACCEPT`：部分接受漂移，部分回滚
- `REDEFINE`：重新定义规格，触发新一轮规格编写流程

---

## 2. 通知机制规范

### 2.1 IDE终端输出格式

当断点触发时，系统在IDE终端输出以下格式的通知：

```
⏸️ [BREAKPOINT] {checkpoint_type}
📋 任务: {task_description}
❓ 待决策: {decision_description}
💡 建议: {suggested_option}
⏱️ 超时: 30:00 (默认策略: {default_strategy})
```

各字段说明：
- `checkpoint_type`：检查点类型枚举值（SECURITY_GATE / ARCHITECTURE_DECISION / REQUIREMENT_AMBIGUITY / ITERATION_DIVERGENCE / SPEC_DRIFT）
- `task_description`：当前任务的简要描述
- `decision_description`：需要人工决策的具体问题描述
- `suggested_option`：系统推荐的决策选项及理由
- `default_strategy`：超时后的默认策略名称

### 2.2 输出示例

```
⏸️ [BREAKPOINT] SECURITY_GATE
📋 任务: 部署用户服务至生产环境
❓ 待决策: 即将执行生产环境部署，目标集群 prod-cluster-01，包含数据库迁移脚本
💡 建议: PROCEED - 迁移脚本已通过预演验证，建议执行
⏱️ 超时: 30:00 (默认策略: CONSERVATIVE_ABORT)
```

```
⏸️ [BREAKPOINT] ARCHITECTURE_DECISION
📋 任务: 实现实时通知模块
❓ 待决策: 通信协议选择 - WebSocket 长连接 vs Server-Sent Events 单向推送
💡 建议: ALTERNATIVE - 推荐WebSocket，因需求包含双向通信场景
⏱️ 超时: 30:00 (默认策略: CONSERVATIVE_HOLD)
```

```
⏸️ [BREAKPOINT] REQUIREMENT_AMBIGUITY
📋 任务: 实现用户权限管理
❓ 待决策: "管理员"角色是否包含数据导出权限？规格中未明确说明
💡 建议: CLARIFY - 建议将数据导出权限独立为单独权限项
⏱️ 超时: 30:00 (默认策略: CONSERVATIVE_MINIMAL)
```

### 2.3 通知级别

| 检查点类型 | 通知级别 | 是否阻塞执行 | 提示方式 |
|---|---|---|---|
| SECURITY_GATE | 🔴 严重 | 是 | 终端输出 + 状态栏警告 |
| ARCHITECTURE_DECISION | 🟠 重要 | 是 | 终端输出 |
| REQUIREMENT_AMBIGUITY | 🟡 一般 | 是 | 终端输出 |
| ITERATION_DIVERGENCE | 🟠 重要 | 是 | 终端输出 + 状态栏提示 |
| SPEC_DRIFT | 🟡 一般 | 是 | 终端输出 |

---

## 3. 超时处理策略

### 3.1 超时时间

所有断点的默认超时时间为 **30分钟**。用户可在项目配置中自定义超时时间。

### 3.2 超时后行为

超时后系统按以下顺序执行：

1. **采用保守默认策略**：选择风险最低的选项

   各检查点类型的默认保守策略：

   | 检查点类型 | 默认策略 | 说明 |
   |---|---|---|
   | SECURITY_GATE | CONSERVATIVE_ABORT | 终止高风险操作 |
   | ARCHITECTURE_DECISION | CONSERVATIVE_HOLD | 保持现有架构不变 |
   | REQUIREMENT_AMBIGUITY | CONSERVATIVE_MINIMAL | 采用最小化理解，不扩展功能范围 |
   | ITERATION_DIVERGENCE | CONSERVATIVE_RESET | 重置当前Phase |
   | SPEC_DRIFT | CONSERVATIVE_ROLLBACK | 回滚实现以符合原始规格 |

2. **记录超时事件**：在知识库中记录超时事件

   存储路径：`.knowledge/decisions/timeout-log.json`

   记录格式：
   ```json
   {
     "timeout_id": "timeout-{timestamp}-{random}",
     "decision_id": "{关联的decision_id}",
     "checkpoint_type": "{检查点类型}",
     "task_description": "{任务描述}",
     "timeout_at": "{超时时间戳}",
     "default_strategy_applied": "{应用的默认策略}",
     "resolved": false
   }
   ```

3. **标记决策为"自动决策-待审核"**：在决策记录中将 `is_auto` 字段设为 `true`，状态标记为 `PENDING_REVIEW`

4. **用户可随时恢复审核**：通过 `/review-decisions` 命令查看和修改所有自动决策

### 3.3 超时配置

项目级配置文件路径：`.knowledge/config/breakpoint-config.json`

```json
{
  "default_timeout_minutes": 30,
  "per_type_timeout": {
    "SECURITY_GATE": 60,
    "ARCHITECTURE_DECISION": 45,
    "REQUIREMENT_AMBIGUITY": 20,
    "ITERATION_DIVERGENCE": 30,
    "SPEC_DRIFT": 20
  },
  "auto_approve_rules": [
    {
      "checkpoint_type": "REQUIREMENT_AMBIGUITY",
      "pattern": "注释风格*",
      "default_option": "CONSERVATIVE_MINIMAL"
    }
  ]
}
```

---

## 4. 决策记录规范

### 4.1 存储路径

决策记录存储在知识库目录下：

```
.knowledge/decisions/{task_id}/
```

每个任务对应一个独立目录，目录下包含该任务的所有决策记录。

### 4.2 记录格式

每条决策记录包含以下字段：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `decision_id` | string | 是 | 决策唯一标识，格式：`dec-{task_id}-{sequence}` |
| `checkpoint_type` | enum | 是 | 检查点类型枚举值 |
| `description` | string | 是 | 决策问题描述 |
| `options` | array | 是 | 可选决策选项列表 |
| `chosen` | string | 是 | 最终选择的选项 |
| `reason` | string | 是 | 选择理由 |
| `is_auto` | boolean | 是 | 是否为自动决策（超时触发） |
| `timestamp` | string | 是 | 决策时间戳（ISO 8601格式） |
| `reviewer` | string | 否 | 审核人标识（人工决策时为用户标识，自动决策时为null） |

### 4.3 记录文件示例

文件路径：`.knowledge/decisions/task-20260502-001/dec-001.json`

```json
{
  "decision_id": "dec-task-20260502-001-001",
  "checkpoint_type": "SECURITY_GATE",
  "description": "部署用户服务至生产环境，包含数据库迁移脚本",
  "options": ["PROCEED", "ABORT", "MODIFY", "ESCALATE"],
  "chosen": "PROCEED",
  "reason": "迁移脚本已通过预演验证，风险可控",
  "is_auto": false,
  "timestamp": "2026-05-02T14:30:00+08:00",
  "reviewer": "user:admin"
}
```

文件路径：`.knowledge/decisions/task-20260502-002/dec-001.json`

```json
{
  "decision_id": "dec-task-20260502-002-001",
  "checkpoint_type": "ARCHITECTURE_DECISION",
  "description": "实时通知模块通信协议选择",
  "options": ["APPROVE", "REJECT", "ALTERNATIVE", "DEFER"],
  "chosen": "ALTERNATIVE",
  "reason": "超时自动决策：采用保守策略，保持现有架构不变",
  "is_auto": true,
  "timestamp": "2026-05-02T15:00:00+08:00",
  "reviewer": null
}
```

### 4.4 自动决策标记规则

- `is_auto=true` 的决策在下次人机交互时优先展示
- 展示顺序按时间倒序排列（最新的自动决策优先展示）
- 每次交互最多展示5条待审核的自动决策
- 用户审核后，`reviewer` 字段更新为审核人标识，`is_auto` 保持 `true` 不变（保留历史标记）

---

## 5. 决策恢复与修改

### 5.1 查看自动决策

用户通过 `/review-decisions` 命令查看所有自动决策：

```
/review-decisions              # 查看所有待审核的自动决策
/review-decisions --all        # 查看所有决策（含已审核）
/review-decisions --type SECURITY_GATE  # 按类型筛选
/review-decisions --task task-001       # 按任务筛选
```

输出格式：

```
📋 自动决策审核列表 (待审核: 3)

1. [SECURITY_GATE] dec-task-001-002
   描述: 生产环境数据库迁移
   自动选择: ABORT (保守策略)
   时间: 2026-05-02T15:00:00+08:00
   ⚠️ 待审核

2. [ARCHITECTURE_DECISION] dec-task-002-001
   描述: 通知模块协议选择
   自动选择: CONSERVATIVE_HOLD
   时间: 2026-05-02T14:45:00+08:00
   ⚠️ 待审核

3. [REQUIREMENT_AMBIGUITY] dec-task-003-001
   描述: 管理员权限范围
   自动选择: CONSERVATIVE_MINIMAL
   时间: 2026-05-02T14:20:00+08:00
   ⚠️ 待审核
```

### 5.2 修改自动决策

用户可对自动决策执行以下操作：

- `accept`：确认自动决策，无需修改
- `override`：覆盖自动决策，选择其他选项
- `rollback`：回滚自动决策产生的影响

操作示例：

```
/review-decisions override dec-task-001-002 --option PROCEED --reason "迁移脚本已验证通过"
```

### 5.3 影响范围评估

修改自动决策后，系统自动评估影响范围：

**影响范围限于当前Phase：**
- 直接重新执行当前Phase
- 保留已通过的中间产物
- 更新决策记录中的 `chosen`、`reason`、`reviewer` 字段
- 重新执行质量门禁检查

**影响范围跨Phase：**
- 触发规格漂移处理流程
- 标记受影响的后续Phase为 `NEEDS_REVIEW`
- 生成影响范围报告，包含：
  - 受影响的Phase列表
  - 需要重新执行的步骤
  - 可能的连锁影响
- 等待用户确认后再执行变更

### 5.4 跨Phase影响处理流程

```
用户修改自动决策
    │
    ▼
系统评估影响范围
    │
    ├── 影响限于当前Phase ──→ 直接重新执行当前Phase
    │
    └── 影响跨Phase
            │
            ▼
        触发规格漂移处理流程
            │
            ▼
        生成影响范围报告
            │
            ▼
        标记受影响Phase为 NEEDS_REVIEW
            │
            ▼
        用户确认变更方案
            │
            ├── 确认 ──→ 按方案重新执行受影响Phase
            └── 否决 ──→ 保持原自动决策结果
```

### 5.5 决策历史追溯

所有决策变更均保留完整历史记录：

```
.knowledge/decisions/{task_id}/
├── dec-{task_id}-001.json          # 决策记录（始终为最新状态）
├── dec-{task_id}-001.history.json  # 决策变更历史
└── dec-{task_id}-002.json
```

历史记录格式：

```json
[
  {
    "revision": 1,
    "chosen": "ABORT",
    "reason": "超时自动决策：采用保守策略",
    "is_auto": true,
    "timestamp": "2026-05-02T15:00:00+08:00",
    "reviewer": null
  },
  {
    "revision": 2,
    "chosen": "PROCEED",
    "reason": "迁移脚本已验证通过，风险可控",
    "is_auto": false,
    "timestamp": "2026-05-02T16:30:00+08:00",
    "reviewer": "user:admin",
    "change_reason": "用户审核后覆盖自动决策"
  }
]
```

---

## 6. 决策分级机制

### 6.1 自动决策 vs 人工决策

根据操作影响等级，决策分为自动决策和人工决策两类：

| 影响等级 | 决策方式 | 判定标准 | 示例 |
|----------|----------|----------|------|
| 低影响 | 自动决策 | 仅影响单一组件，不改变外部行为 | 变量命名调整、内部算法优化、注释修改 |
| 中影响 | 自动决策(带审核) | 影响模块间交互，但风险可控 | 接口参数顺序调整、配置项默认值变更 |
| 高影响 | 人工决策 | 影响外部API、安全模型或跨平台共享层 | API端点变更、权限模型修改、IPC契约变更 |

### 6.2 自动决策适用范围

自动决策仅适用于以下断点类型和场景：

| 断点类型 | 可自动决策的场景 | 不可自动决策的场景 |
|----------|-----------------|-------------------|
| SECURITY_GATE | 无 | 所有安全确认必须人工决策 |
| ARCHITECTURE_DECISION | 非核心模块的技术选型 | 核心架构模式变更、公共API设计 |
| REQUIREMENT_AMBIGUITY | 非功能性需求的澄清 | 业务规则理解、核心功能定义 |
| ITERATION_DIVERGENCE | 无 | 所有迭代不收敛必须人工决策 |
| SPEC_DRIFT | 低影响漂移(仅内部实现) | 中/高影响漂移 |

### 6.3 自动决策安全约束

1. **安全确认不可自动**：SECURITY_GATE类型断点始终要求人工决策，不可自动批准
2. **迭代不收敛不可自动**：ITERATION_DIVERGENCE类型断点始终要求人工决策
3. **自动决策必须可追溯**：所有自动决策记录`is_auto=true`，可事后审核和覆盖
4. **自动决策必须可回滚**：自动决策产生的影响必须可回滚至决策前状态
5. **自动决策频率限制**：同一任务连续自动决策不超过3次，超过后强制人工介入

---

## 7. 协作工作流总览

```
Agent执行任务
    │
    ├── 遇到决策点 → 判定影响等级
    │       │
    │       ├── 低影响 → 自动决策 → 记录 → 继续执行
    │       │
    │       ├── 中影响 → 自动决策(带审核标记) → 记录 → 继续执行
    │       │                              ↓
    │       │                    事后审核(可覆盖)
    │       │
    │       └── 高影响 → 触发人机协作断点
    │                       │
    │               IDE终端输出通知
    │               (断点类型/决策摘要/建议选项/超时倒计时)
    │                       │
    │               ┌───────┴───────┐
    │               │               │
    │           人工响应          超时(30分钟)
    │               │               │
    │           执行决策      保守默认策略
    │               │               │
    │               │         记录至知识库
    │               │         标记待审核
    │               │               │
    │               └───────┬───────┘
    │                       │
    │                   继续执行
    │
    └── 任务完成 → 决策记录归档
```

---

## 8. 协作度量指标

### 8.1 核心KPI

| 指标名称 | 计算方式 | 目标值 | 说明 |
|----------|----------|--------|------|
| 断点触发频率 | 断点触发次数 / 任务总数 | ≤ 2次/任务 | 衡量Agent自主决策能力 |
| 人工响应时长 | 从断点触发到人工决策的平均时长 | ≤ 10分钟 | 衡量人工介入效率 |
| 超时率 | 超时决策数 / 总断点数 | ≤ 10% | 衡量人工参与度 |
| 自动决策覆盖率 | 自动决策数 / 总决策数 | ≥ 60% | 衡量自动化水平 |
| 自动决策覆盖率(审核后) | 被覆盖的自动决策数 / 自动决策总数 | ≤ 5% | 衡量自动决策准确性 |
| 决策回滚率 | 回滚的决策数 / 总决策数 | ≤ 3% | 衡量决策质量 |

### 8.2 断点类型分布分析

按断点类型统计触发频率，识别高频断点类型：

| 断点类型 | 预期占比 | 异常信号 |
|----------|----------|----------|
| SECURITY_GATE | 10-20% | >30%：安全策略过于保守，需优化审批规则 |
| ARCHITECTURE_DECISION | 15-25% | >35%：架构设计不够明确，需加强前期设计 |
| REQUIREMENT_AMBIGUITY | 20-30% | >40%：需求质量不足，需加强需求澄清 |
| ITERATION_DIVERGENCE | 5-10% | >15%：迭代策略需优化 |
| SPEC_DRIFT | 15-25% | >35%：规格质量不足，需加强规格编写 |

### 8.3 度量数据采集

- 断点触发时记录：断点类型、任务ID、触发时间、决策选项
- 决策完成时记录：决策结果、是否自动决策、响应时长
- 超时发生时记录：超时类型、默认策略、后续审核状态
- 数据存储路径：`.knowledge/metrics/collaboration/`
