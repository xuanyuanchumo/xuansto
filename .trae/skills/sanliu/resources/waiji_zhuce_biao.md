# 外部技能注册表

本文档记录了已注册的外部技能，定义了技能分类和适用场景，为技能调用提供参考依据。

---

## 技能分类

| 分类 | 说明 | 典型技能 |
|------|------|----------|
| **语言处理** | 处理多语言输入输出、语言转换、本地化 | global-chinese |
| **开发工具** | 辅助开发、构建工具、协议实现 | mcp-builder |
| **技能管理** | 创建、修改、优化、测试技能 | skill-creator |
| **设计系统** | UI/UX设计、视觉规范、交互模式 | ui-ux-pro-max |
| **Agent角色库** | 专业Agent角色集合，覆盖开发、设计、营销、测试等领域 | agency-agents |

---

## 已注册技能列表

### global-chinese

- **名称**：global-chinese
- **路径**：.trae/skills/global-chinese/SKILL.md
- **功能描述**：通用中文响应技能，确保无论用户使用什么语言提问，系统都能正确理解并触发对应语言的技能，最终所有输出内容都用简体中文回答。解决多语言交互场景下的语言一致性问题。
- **适用场景**：
  - 用户使用非中文语言提问，但需要中文输出
  - 需要确保所有交互都以简体中文进行
  - 智能选择最合适的技能（中文或英文）完成任务
  - 多语言环境下的统一输出格式
- **调用部门**：门下省（中枢纽带）、尚书省（执行层）、中书省（协调层）
- **核心能力**：
  - 语言无关性接收：接受任何语言的输入
  - 智能技能触发：基于任务需求选择最佳技能
  - 强制简体中文输出：所有最终输出必须为简体中文

---

### mcp-builder

- **名称**：mcp-builder
- **路径**：.trae/skills/mcp-builder/SKILL.md
- **功能描述**：MCP（Model Context Protocol）服务器开发指南，用于创建高质量的MCP服务器，使LLM能够通过精心设计的工具与外部服务交互。支持Python（FastMCP）和Node/TypeScript（MCP SDK）两种技术栈。
- **适用场景**：
  - 构建MCP服务器以集成外部API或服务
  - 开发LLM与外部系统的交互接口
  - 实现工具定义、资源管理和提示词模板
  - 创建可复用的服务集成层
- **调用部门**：工部（建设实施）、户部（数据管理）
- **核心能力**：
  - 四阶段开发流程：研究规划 → 实现 → 审查测试 → 创建评估
  - 完整的TypeScript/Python实现指南
  - 工具命名、上下文管理、错误处理最佳实践
  - 评估测试框架支持

---

# 外部技能注册表

本文档记录了已注册的外部技能，定义了技能分类和适用场景，为技能调用提供参考依据。

---

## 技能分类

| 分类 | 说明 | 典型技能 |
|------|------|----------|
| **语言处理** | 处理多语言输入输出、语言转换、本地化 | global-chinese |
| **开发工具** | 辅助开发、构建工具、协议实现 | mcp-builder |
| **技能管理** | 创建、修改、优化、测试技能 | skill-creator |
| **设计系统** | UI/UX设计、视觉规范、交互模式 | ui-ux-pro-max |
| **Agent角色库** | 专业Agent角色集合，覆盖开发、设计、营销、测试等领域 | agency-agents |

---

## 已注册技能列表

### global-chinese

- **名称**：global-chinese
- **路径**：.trae/skills/global-chinese/SKILL.md
- **功能描述**：通用中文响应技能，确保无论用户使用什么语言提问，系统都能正确理解并触发对应语言的技能，最终所有输出内容都用简体中文回答。解决多语言交互场景下的语言一致性问题。
- **适用场景**：
  - 用户使用非中文语言提问，但需要中文输出
  - 需要确保所有交互都以简体中文进行
  - 智能选择最合适的技能（中文或英文）完成任务
  - 多语言环境下的统一输出格式
- **调用部门**：门下省（中枢纽带）、尚书省（执行层）、中书省（协调层）
- **核心能力**：
  - 语言无关性接收：接受任何语言的输入
  - 智能技能触发：基于任务需求选择最佳技能
  - 强制简体中文输出：所有最终输出必须为简体中文

---

### mcp-builder

- **名称**：mcp-builder
- **路径**：.trae/skills/mcp-builder/SKILL.md
- **功能描述**：MCP（Model Context Protocol）服务器开发指南，用于创建高质量的MCP服务器，使LLM能够通过精心设计的工具与外部服务交互。支持Python（FastMCP）和Node/TypeScript（MCP SDK）两种技术栈。
- **适用场景**：
  - 构建MCP服务器以集成外部API或服务
  - 开发LLM与外部系统的交互接口
  - 实现工具定义、资源管理和提示词模板
  - 创建可复用的服务集成层
- **调用部门**：工部（建设实施）、户部（数据管理）
- **核心能力**：
  - 四阶段开发流程：研究规划 → 实现 → 审查测试 → 创建评估
  - 完整的TypeScript/Python实现指南
  - 工具命名、上下文管理、错误处理最佳实践
  - 评估测试框架支持

---

### skill-creator

- **名称**：skill-creator
- **路径**：.trae/skills/skill-creator/SKILL.md
- **功能描述**：用于创建新技能、修改和改进现有技能、测量技能性能的元技能。提供完整的技能生命周期管理，包括草稿编写、测试验证、迭代优化和性能基准测试。
- **适用场景**：
  - 从零创建新的技能
  - 编辑或优化现有技能
  - 运行评估测试技能效果
  - 基准测试技能性能与方差分析
  - 优化技能描述以提高触发准确性
- **调用部门**：吏部（技能管理）、礼部（规范制定）
- **核心能力**：
  - 意图捕获与需求访谈
  - SKILL.md编写与渐进式披露设计
  - 测试用例生成与基准测试
  - 描述优化循环（触发准确性）
  - 盲比较与质量分析

---

### ui-ux-pro-max

- **名称**：ui-ux-pro-max
- **路径**：.trae/skills/ui-ux-pro-max-skill-main/.claude/skills/ui-ux-pro-max/SKILL.md
- **功能描述**：全面的UI/UX设计智能技能，包含50+风格、161色彩调色板、57字体配对、161产品类型、99 UX指南和25图表类型，覆盖10种技术栈（React、Next.js、Vue、Svelte、SwiftUI、React Native、Flutter、Tailwind、shadcn/ui、HTML/CSS）。
- **适用场景**：
  - 设计新页面（落地页、仪表板、管理后台、SaaS、移动应用）
  - 创建或重构UI组件（按钮、模态框、表单、表格、图表等）
  - 选择配色方案、字体系统、间距标准、布局系统
  - 审查UI代码的用户体验、可访问性、视觉一致性
  - 实现导航结构、动画、响应式行为
  - 产品级设计决策（风格、信息层级、品牌表达）
- **调用部门**：工部（UI实现）、礼部（视觉规范）
- **核心能力**：
  - 设计系统生成（--design-system）
  - 多维度域搜索（产品、风格、颜色、字体、图表、UX等）
  - 技术栈特定指南（React Native等）
  - 10大优先级规则类别（可访问性、触摸交互、性能等）
  - 交付前检查清单

---

### agency-agents

- **名称**：agency-agents
- **路径**：.trae/skills/agency-agents/
- **功能描述**：包含157+专业Agent角色的外部技能库，覆盖软件开发、设计、营销、测试、游戏开发、空间计算等多个领域。提供从需求分析到部署运维的全流程Agent支持。
- **适用场景**：
  - 需要专业领域Agent支持（前端开发、后端架构、测试等）
  - 跨部门协作任务（产品、设计、开发、测试）
  - 行业垂直场景（营销、游戏、空间计算）
  - 多Agent协同编排
- **调用部门**：
  - 中书省：Product Manager, Trend Researcher, Sprint Prioritizer
  - 门下省：Code Reviewer, Reality Checker, Compliance Auditor
  - 尚书省：Agents Orchestrator, Project Manager
  - 吏部：Recruitment Specialist, Training Designer
  - 户部：Finance Tracker, Data Engineer
  - 礼部：UX Architect, Software Architect, Brand Guardian
  - 兵部：API Tester, Performance Benchmarker, Accessibility Auditor
  - 刑部：Security Engineer, SRE, Database Optimizer
  - 工部：Frontend Developer, Backend Architect, AI Engineer
- **核心能力**：
  - 157+专业Agent角色覆盖全开发流程
  - 三省六部角色映射机制
  - 行业垂直Agent支持（营销、游戏、空间计算）
  - 多Agent协同编排能力
- **子技能文档**：subskills/agency_agents_integration.md

---

## 技能调用指南

### 调用原则

1. **按需调用**：根据任务类型选择最匹配的技能，避免过度调用
2. **组合使用**：复杂任务可组合多个技能，如先用global-chinese确保中文输出，再用ui-ux-pro-max设计界面
3. **优先级判断**：当多个技能都适用时，优先选择专业度更高的技能

### 调用流程

```
1. 分析任务需求
   ↓
2. 匹配技能分类
   ↓
3. 选择具体技能
   ↓
4. 读取技能SKILL.md
   ↓
5. 按技能指引执行
   ↓
6. 验证输出质量
```

### 典型调用场景示例

| 任务场景 | 推荐技能 | 调用说明 |
|----------|----------|----------|
| 用户用英文提问，需要中文回答 | global-chinese | 确保输出为简体中文 |
| 开发MCP服务器集成外部API | mcp-builder | 按四阶段流程开发 |
| 创建新的自定义技能 | skill-creator | 从意图捕获到测试迭代 |
| 设计移动应用界面 | ui-ux-pro-max | 生成设计系统并实现 |
| 多语言项目的设计任务 | global-chinese + ui-ux-pro-max | 组合调用 |

### 跨技能协作

当任务需要多个技能协作时，建议按以下顺序：

1. **global-chinese**（如有语言需求）→ 确保输出语言一致
2. **skill-creator**（如需创建技能）→ 先定义技能框架
3. **mcp-builder**（如需外部集成）→ 构建服务接口
4. **ui-ux-pro-max**（如需界面设计）→ 实现视觉层

---

## 技能集成信息

### skill-creator 集成详情

| 集成项 | 详情 |
|--------|------|
| **集成文档** | [shangshusheng/SKILL.md - skill-creator集成](../shangshusheng/SKILL.md#skill-creator集成) |
| **集成脚本** | `scripts/skill_creator_integration.py` |
| **调用部门** | 礼部（规范制定）、吏部（技能管理）、兵部（性能测试） |
| **触发场景** | 创建新技能、优化现有技能、技能评估测试 |
| **集成流程** | 需求分析 → 技能创建/优化 → 评估测试 → 结果验证 → 注册更新 |
| **脚本功能** | 自动发现技能需求、执行技能评估、生成优化建议 |

**脚本使用示例：**
```bash
# 发现需要创建/优化的技能
python scripts/skill_creator_integration.py discover --scope=all

# 创建新技能
python scripts/skill_creator_integration.py create \
  --name=my-skill \
  --category=development \
  --purpose="技能用途描述"

# 优化现有技能
python scripts/skill_creator_integration.py optimize \
  --path=.trae/skills/my-skill/SKILL.md

# 评估技能质量
python scripts/skill_creator_integration.py evaluate \
  --path=.trae/skills/my-skill/SKILL.md

# 生成技能集成报告
python scripts/skill_creator_integration.py report --format=markdown
```

---

### ui-ux-pro-max 集成详情

| 集成项 | 详情 |
|--------|------|
| **集成文档** | [subskills/ui_ux_sheji.md - ui-ux-pro-max集成](../subskills/ui_ux_sheji.md#ui-ux-pro-max-集成指南) |
| **集成脚本** | `scripts/ui_ux_integration.py` |
| **调用部门** | 工部（UI实现）、礼部（视觉规范）、兵部（UI审查） |
| **触发场景** | 新页面设计、组件设计、UI代码审查、响应式设计 |
| **集成流程** | 需求分析 → 设计系统生成 → 页面/组件设计 → UI校验 → 文档生成 |
| **脚本功能** | 自动发现设计任务、执行UI设计、生成校验报告 |

**脚本使用示例：**
```bash
# 发现需要UI/UX设计的任务
python scripts/ui_ux_integration.py discover --scope=all

# 设计新页面
python scripts/ui_ux_integration.py design \
  --type=page \
  --name=dashboard \
  --tech-stack="React+Tailwind"

# 设计组件
python scripts/ui_ux_integration.py design \
  --type=component \
  --name=DataTable \
  --tech-stack="React+Tailwind"

# 执行UI校验
python scripts/ui_ux_integration.py validate \
  --path=src/components/ \
  --type=comprehensive

# 生成UI设计报告
python scripts/ui_ux_integration.py report --format=markdown
```

---

## 外部技能集成矩阵

| 技能名称 | 集成脚本 | 调用部门 | 主要功能 | 集成状态 |
|----------|----------|----------|----------|----------|
| skill-creator | `scripts/skill_creator_integration.py` | 礼部、吏部、兵部 | 技能创建、优化、评估 | ✅ 已集成 |
| ui-ux-pro-max | `scripts/ui_ux_integration.py` | 工部、礼部、兵部 | UI/UX设计、校验 | ✅ 已集成 |
| global-chinese | - | 三省六部 | 语言处理 | ✅ 已注册 |
| mcp-builder | - | 工部、户部 | MCP服务构建 | ✅ 已注册 |
| agency-agents | - | 三省六部 | Agent角色库 | ✅ 已注册 |

---

## 技能状态追踪

| 技能名称 | 状态 | 最后更新 | 备注 |
|----------|------|----------|------|
| global-chinese | 活跃 | - | 语言处理核心技能 |
| mcp-builder | 活跃 | - | MCP开发标准技能 |
| skill-creator | 活跃 | 2024-01 | 技能管理元技能，已集成 |
| ui-ux-pro-max | 活跃 | 2024-01 | UI/UX设计专业技能，已集成 |
| agency-agents | 活跃 | - | Agent角色库 |

---

## 技能发现机制

### 自动发现流程

```
1. 扫描技能目录
   ├── 检查 .trae/skills/ 下所有子目录
   ├── 查找 SKILL.md 文件
   └── 解析技能元数据

2. 注册表同步
   ├── 读取 waiji_zhuce_biao.md
   ├── 提取已注册技能信息
   └── 合并本地与注册表数据

3. 状态评估
   ├── 评估技能质量分数
   ├── 检测需要优化的技能
   └── 生成发现报告
```

### 发现脚本使用

```bash
# 发现所有技能
python scripts/skill_creator_integration.py discover --scope=all

# 发现需要优化的技能
python scripts/skill_creator_integration.py discover --scope=needs_optimization

# 从注册表发现外部技能
python scripts/skill_creator_integration.py discover --from-registry

# 输出JSON格式
python scripts/skill_creator_integration.py discover --scope=all --output=json
```

### 技能发现API

```python
from scripts.skill_creator_integration import SkillCreatorIntegration

integration = SkillCreatorIntegration()

# 发现所有技能
skills = integration.discover_skills("all")

# 发现需要创建的技能
needs_creation = integration.discover_skills("needs_creation")

# 发现需要优化的技能
needs_optimization = integration.discover_skills("needs_optimization")

# 从注册表发现
registered = integration.discover_skills_from_registry()
```

---

## 技能调用链

### 调用链概念

技能调用链定义了一系列技能的执行顺序和条件，支持复杂任务的自动化处理。

### 调用链结构

```json
{
  "chain_id": "CHAIN-XXXX",
  "name": "设计流程",
  "description": "完整的UI设计流程",
  "skills": ["skill-creator", "ui-ux-pro-max", "skill-creator"],
  "execution_order": [0, 1, 2],
  "conditions": {
    "skill_1_condition": {
      "type": "previous_success",
      "value": true
    }
  },
  "created_at": "2024-01-01T00:00:00Z"
}
```

### 预定义调用链

#### 1. 新技能创建链

```
skill-creator (创建) → skill-creator (评估) → skill-creator (优化)
```

**用途**: 创建新技能并确保质量

**触发条件**: 需要创建新技能时

**脚本命令**:
```bash
python scripts/skill_creator_integration.py chain --action=create \
  --name="新技能创建流程" \
  --skills="skill-creator,skill-creator,skill-creator"
```

#### 2. UI设计完整链

```
ui-ux-pro-max (设计系统) → ui-ux-pro-max (页面设计) → ui-ux-pro-max (校验)
```

**用途**: 完整的UI设计流程

**触发条件**: 新页面或组件设计任务

**脚本命令**:
```bash
python scripts/ui_ux_integration.py design --type=system --name=my-design
python scripts/ui_ux_integration.py design --type=page --name=dashboard
python scripts/ui_ux_integration.py validate --path=src/pages/dashboard.tsx
```

#### 3. 多语言设计链

```
global-chinese (语言处理) → ui-ux-pro-max (设计) → global-chinese (输出转换)
```

**用途**: 多语言环境下的设计任务

**触发条件**: 需要中文输出的设计任务

#### 4. MCP服务开发链

```
mcp-builder (规划) → mcp-builder (实现) → mcp-builder (测试)
```

**用途**: MCP服务器开发流程

**触发条件**: 需要创建MCP服务时

### 调用链管理

#### 创建调用链

```bash
python scripts/skill_creator_integration.py chain --action=create \
  --name="自定义流程" \
  --description="自定义技能调用流程" \
  --skills="skill1,skill2,skill3"
```

#### 执行调用链

```bash
python scripts/skill_creator_integration.py chain --action=execute \
  --chain-id=CHAIN-XXXX \
  --context='{"param1": "value1"}'
```

#### 列出所有调用链

```bash
python scripts/skill_creator_integration.py chain --action=list
```

### 调用链API

```python
from scripts.skill_creator_integration import SkillCreatorIntegration

integration = SkillCreatorIntegration()

# 创建调用链
success, message = integration.create_skill_chain(
    name="设计流程",
    description="完整的UI设计流程",
    skills=["skill-creator", "ui-ux-pro-max"],
    execution_order=[0, 1],
    conditions={"skill_1_condition": {"type": "previous_success"}}
)

# 执行调用链
success, result = integration.execute_skill_chain(
    chain_id="CHAIN-XXXX",
    context={"project_type": "web"}
)

# 列出调用链
chains = integration.list_skill_chains()
```

---

## 技能调用条件

### 条件类型

| 条件类型 | 说明 | 示例 |
|----------|------|------|
| `always` | 始终执行 | `{"type": "always"}` |
| `context_exists` | 上下文存在指定键 | `{"type": "context_exists", "key": "project_type"}` |
| `context_equals` | 上下文值等于指定值 | `{"type": "context_equals", "key": "lang", "value": "zh"}` |
| `previous_success` | 前一步骤成功 | `{"type": "previous_success", "value": true}` |

### 条件组合示例

```json
{
  "conditions": {
    "skill_1_condition": {
      "type": "context_equals",
      "key": "need_ui",
      "value": true
    },
    "skill_2_condition": {
      "type": "previous_success",
      "value": true
    }
  }
}
```

---

## 技能集成状态

### 集成完成度

| 技能 | 发现机制 | 创建接口 | 优化接口 | 调用链支持 |
|------|----------|----------|----------|------------|
| skill-creator | ✅ | ✅ | ✅ | ✅ |
| ui-ux-pro-max | ✅ | ✅ | ✅ | ✅ |
| global-chinese | ✅ | - | - | ✅ |
| mcp-builder | ✅ | - | - | ✅ |
| agency-agents | ✅ | - | - | ✅ |

### 脚本功能矩阵

| 功能 | skill_creator_integration.py | ui_ux_integration.py |
|------|------------------------------|----------------------|
| 发现任务 | `discover` | `discover` |
| 创建 | `create` | `design` |
| 优化 | `optimize` | - |
| 评估/校验 | `evaluate` | `validate` |
| 调用链 | `chain` | - |
| 报告生成 | `report` | `report` |
| UX检查 | - | `ux-check` |
| 设计系统 | - | `system` |

---

## 附录：技能路径映射

```
.trae/skills/
├── global-chinese/
│   └── SKILL.md
├── mcp-builder/
│   ├── SKILL.md
│   ├── reference/
│   └── scripts/
├── skill-creator/
│   ├── SKILL.md
│   ├── agents/
│   ├── assets/
│   ├── eval-viewer/
│   ├── references/
│   └── scripts/
└── ui-ux-pro-max-skill-main/
    └── .claude/skills/ui-ux-pro-max/
        └── SKILL.md
```
