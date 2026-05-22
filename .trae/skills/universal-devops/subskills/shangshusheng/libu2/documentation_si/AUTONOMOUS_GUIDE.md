# 文档生成司 自主操作指南 (Autonomous Operation Guide)

## 概述

文档生成司（documentation_si）是尚书省礼部下属的核心技术文档管理单元，负责代码与文档之间的双向同步维护、多格式文档输出、以及自动化文档生成流水线的自主运行。本司以"代码即文档、文档即契约"为核心理念，确保技术资产在项目全生命周期中始终保持一致性和时效性。

**核心目标：**
- 实现代码与文档的实时双向同步，消除信息孤岛
- 构建覆盖 Markdown/HTML/PDF/OpenAPI JSON 的多格式输出能力
- 建立基于 Conventional Commits 规范的 CHANGELOG 自动生成机制
- 提供过时内容识别与废弃标记的主动治理能力
- 确保交叉引用完整性与术语表全局一致性

## 核心原则

1. **单一事实源（Single Source of Truth）**：代码是第一性文档源，所有派生文档必须可追溯到代码
2. **变更感知优先（Change-Aware First）**：任何代码变更触发前，先评估其对文档链的影响范围
3. **渐进式同步（Incremental Sync）**：不追求一次性完美，而是持续迭代逼近一致性
4. **格式无关性（Format Agnostic）**：内容模型与渲染格式解耦，同一份结构化数据支持多端输出
5. **可审计性（Auditability）**：每次文档操作均记录时间戳、操作者、变更摘要和影响范围
6. **零信任验证（Zero-Trust Verify）**：生成的文档不默认可信，必须经过自动验证流程后才能发布

## 自主操作流程

### 阶段一：感知（Perceive）

本阶段负责全面扫描项目状态，识别需要文档处理的信号。

**1.1 代码变更检测**

```
输入信号：
├── Git diff 检测（未暂存 + 已暂存 + 最近N次提交）
├── 分支策略识别（feature/hotfix/release/main）
├── PR/MR 事件监听（创建/更新/合并/关闭）
└── 定时巡检触发（每日凌晨 / 版本发布前24h）

检测维度：
├── API签名变更：函数/方法/接口的参数增删改、返回值类型变化
├── 结构体/类型定义变更：字段增删改、枚举值变化
├── 配置项变更：新增配置、默认值修改、弃用标记
├── 路由/端点变更：RESTful路径、HTTP方法、中间件链
└── 依赖版本变更：升级/降级/引入/移除
```

**1.2 文档现状评估**

对现有文档库执行健康度扫描：

| 扫描项 | 检测方法 | 输出指标 |
|--------|----------|----------|
| API文档覆盖率 | AST解析 vs 文档条目 | 覆盖率百分比 |
| 过时内容占比 | 最后修改时间 vs 代码最后修改时间 | 过时率百分比 |
| 交叉引用完整性 | 链接有效性检查 | 断链数量 |
| 术语表一致性 | 全文术语提取 vs 术语表 | 未收录术语数 |
| 示例代码可用性 | 示例运行测试 | 通过/失败计数 |

**1.3 外部信号采集**

- 监听 CI/CD 流水线事件（构建成功/失败、部署完成）
- 采集 issue 中与文档相关的反馈标签（`docs`, `documentation`）
- 检测版本号变更（package.json/pyproject.toml/Cargo.toml 等）
- 识别语义化版本号跳跃（major/minor/patch）

### 阶段二：决策（Decide）

基于感知结果，自主判定下一步行动方案。

**2.1 变更分类决策树**

```
根节点：检测到代码变更
├── 是否涉及公开API？
│   ├── 是 → 进入【API文档同步】流程
│   └── 否 → 是否涉及内部模块接口？
│       ├── 是 → 进入【内部文档标注】流程
│       └── 否 → 是否涉及配置或部署？
│           ├── 是 → 进入【运维文档更新】流程
│           └── 否 → 记录日志，无需文档动作
```

**2.2 文档生成触发条件矩阵**

| 触发场景 | 触发条件 | 自动执行动作 | 人工确认门槛 |
|----------|----------|--------------|--------------|
| PR合并到main | 合并事件 + 含代码文件变更 | 全量diff分析 + 增量文档更新 | 删除类变更需确认 |
| 版本发布前 | tag 创建 / version bump | 全量文档重新生成 + 多格式导出 | 必须人工审核 |
| 重大重构后 | 单次提交 >50文件 或 >1000行变更 | 生成变更报告 + 文档迁移建议 | 强制人工介入 |
| 定时巡检 | 每日定时任务 | 过时内容标记 + 一致性报告 | 仅告警，不自动修复 |
| 废弃API标记 | 代码中添加 @deprecated 注解 | 自动添加废弃横幅 + 迁移指南链接 | 无需确认 |
| 新API首次出现 | 新增公开函数/类/接口 | 从docstring/注释提取初始文档 | 草稿模式，需审阅 |

**2.3 优先级排序算法**

```
P_score = W_api × I_api + W_stale × I_stale + W_breaking × I_breaking + W_critical × I_critical

其中：
- W_api = 0.30 （API完整性权重）
- W_stale = 0.25 （过时内容紧迫性权重）
- W_breaking = 0.25 （破坏性变更权重）
- W_critical = 0.20 （关键路径权重）

I_api = 未文档化的公开API数量 / 公开API总数
I_stale = 过时文档条目数量 / 总文档条目数量
I_breaking = 破坏性变更涉及的文档条目数
I_critical = 关键用户路径上受影响的文档条目数

P_score >= 0.7 → 高优先级，立即处理
P_score >= 0.4 → 中优先级，排入当批次队列
P_score < 0.4  → 低优先级，记录并纳入下次巡检
```

### 阶段三：执行（Execute）

按决策结果执行具体的文档操作。

**3.1 代码→文档双向同步**

**正向同步（Code → Doc）：**
- 从源码AST中提取：函数签名、参数类型、返回值、异常列表、默认值
- 从docstring/注释中提取：功能描述、使用示例、注意事项、跨引用提示
- 从类型注解中推断：参数约束、返回值结构、泛型参数
- 从装饰器/注解中获取：权限要求、速率限制、缓存策略、版本标记

**反向同步（Doc → Code）检测：**
- 文档中描述的API是否在代码中存在对应实现
- 文档中的参数说明是否与实际函数签名匹配
- 文档中的示例代码是否能通过编译/解释器检查
- 文档中的版本兼容性声明是否与实际版本号一致

**3.2 过时内容识别与处置**

```python
# 过时判定规则引擎伪代码
def classify_staleness(doc_entry, code_entity):
    doc_last_modified = doc_entry.last_updated
    code_last_modified = code_entity.last_modified
    time_delta = doc_last_modified - code_last_modified

    if time_delta.days > 90 and code_entity.has_signature_change:
        return "STALE_CRITICAL"    # 严重过时，立即标记+通知
    elif time_delta.days > 30:
        return "STALE_WARNING"     # 警告级别，添加过期标记
    elif code_entity.is_deprecated and not doc_entry.marked_deprecated:
        return "DEPRECATION_MISMATCH"  # 弃用状态不一致
    else:
        return "CURRENT"            # 当前有效
```

处置策略：
- `STALE_CRITICAL`：在文档顶部插入醒目的"⚠️ 此文档可能已过时"横幅，同时向维护者发送告警
- `STALE_WARNING`：在文档末尾追加"最后验证日期"戳，建议审阅
- `DEPRECATION_MISMATCH`：自动补充 `@deprecated` 标记及迁移指引
- `CURRENT`：无额外动作，维持现状

**3.3 多格式输出管线**

```
统一中间表示（IR）格式：
{
  "meta": { "title", "version", "lastUpdated", "authors", "tags" },
  "sections": [
    {
      "id": "unique-id",
      "heading": { "level": 1..6, "text": "..." },
      "body": [ /* 富文本节点数组 */ ],
      "codeBlocks": [ { "lang", "source", "executable": bool } ],
      "crossRefs": [ { "targetId", "refType": "see-also/api/example" } },
      "metadata": { "apiSignature", "sinceVersion", "deprecated": bool }
    }
  ]
}
```

| 目标格式 | 渲染引擎 | 输出特征 | 适用场景 |
|----------|----------|----------|----------|
| Markdown | 内置模板引擎 | GitHub Flavored Markdown，含表格/代码块/目录 | 开发者阅读、Git托管 |
| HTML | Jinja2模板 + highlight.js | 响应式布局、侧边导航、搜索索引 | 在线文档站、内部门户 |
| PDF | WeasyPrint / wkhtmltopdf | 分页控制、目录书签、页眉页脚 | 离线归档、合规交付 |
| OpenAPI JSON | JSON Schema校验 | 符合OAS 3.1规范，含schema/examples | API网关导入、客户端SDK生成 |

**3.4 Conventional Commits → CHANGELOG 自动生成**

映射规则：

| Commit Type | CHANGELOG 分类 | 格式模板 |
|-------------|----------------|----------|
| `feat` | Added / 新增 | `- 新增: {{subject}} (#{{PR号}})` |
| `fix` | Fixed / 修复 | `- 修复: {{subject}} (#{{PR号}})` | 
| `perf` | Performance / 性能优化 | `- 性能: {{subject}}` |
| `refactor` | Changed / 变更 | `- 重构: {{subject}}` |
| `docs` | Documentation / 文档 | `- 文档: {{subject}}` |
| `style` | -（通常不入CHANGELOG） | 跳过 |
| `test` | -（通常不入CHANGELOG） | 跳过 |
| `chore` | -（依赖升级等可能入） | 条件判断 |
| `BREAKING CHANGE` | ⚠️ BREAKING CHANGES 专区 | 独立章节，高亮显示 |

CHANGELOG 结构模板：

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- （待发布的feat commits）

### Fixed
- （待发布的fix commits）

## [{{version}}] - {{YYYY-MM-DD}}

### Added
...

### Fixed
...

### ⚠️ Breaking Changes
...
```

### 阶段四：验证（Verify）

所有文档产出必须通过验证关卡才能发布。

**4.1 交叉引用验证**

- **内部链接检查**：遍历所有 `[text](target)` 形式的Markdown链接，验证 target 对应的锚点/文件是否存在
- **外部链接存活探测**：对HTTP(S)外链执行HEAD请求，记录301/302重定向链和404状态
- **术语表交叉验证**：全文提取术语实体后逐一核对术语表，发现未收录术语时自动提议新增
- **API引用一致性**：文档中引用的 `ClassName.methodName()` 必须能在代码AST中定位到对应节点

**4.2 示例代码可执行性验证**

```yaml
验证流程:
  1. 从文档中提取所有 fenced code blocks（语言标识非空的）
  2. 按 language 字段分发给对应语言的验证器
  3. Python: ast.parse() 语法检查 + 类型推断
  4. JavaScript/TypeScript: acorn/swc 解析检查
  5. Go: go/parser 解析
  6. 通用: 至少保证括号/引号配对平衡
  6. 记录每个代码块的验证结果（PASS/WARN/SKIP/FAIL）
  7. FAIL的代码块阻止文档发布，需修复后重验
```

**4.3 文档质量评分卡**

| 维度 | 权重 | 检查项 | 满分标准 |
|------|------|--------|----------|
| 完整性 | 25% | 所有公开API均有文档条目 | 100%覆盖 |
| 准确性 | 25% | 代码↔文档无矛盾点 | 0个不一致 |
| 可读性 | 15% | 有示例、有分层标题、有概述 | 每个API至少1个示例 |
| 链接健康 | 15% | 无断链、无死锚点 | 0个无效链接 |
| 时效性 | 20% | 最后更新距现在<30天 | 100%文档<30天未更新 |

总分 ≥ 90：A级，可直接发布
总分 ≥ 80：B级，有小瑕疵但可发布（附带改进建议）
总分 ≥ 70：C级，需修复关键问题后发布
总分 < 70：D/F级，禁止发布，回退至Execute阶段修正

### 阶段五：记录（Record）

**5.1 操作日志结构**

```json
{
  "operationId": "doc-op-20260406-001",
  "timestamp": "2026-04-06T10:30:00Z",
  "operator": "documentation_si[autonomous]",
  "trigger": "pr_merged",
  "triggerDetail": "PR #142 merged to main",
  "actions": [
    {
      "type": "sync_code_to_doc",
      "target": "src/api/users.py::UserAPI",
      "status": "success",
      "artifacts": ["docs/api/users.md", "docs/openapi.json"]
    },
    {
      "type": "changelog_append",
      "entriesAdded": 3,
      "status": "success"
    }
  ],
  "verificationScore": 92,
  "grade": "A",
  "nextReviewDate": "2026-05-06"
}
```

**5.2 知识沉淀**

- 将本次操作中发现的新模式/反模式录入 knowledge_base_si
- 将反复出现的文档问题形成 checklist 模板存入 template_management_si
- 统计各模块文档变更频率，为 standardization_si 提供数据支撑

## 典型自主场景

### 场景1：PR合并后的增量文档同步

**背景**：开发者提交了PR #156，包含3个新API端点和1个废弃端点的变更，PR已被合并至main分支。

**自主执行流程：**

1. **感知**：收到GitHub Webhook的 `pull_request.closed` 事件（merged=true），提取commit range
2. **决策**：检测到4个API相关变更 → P_score=0.82 → 高优先级 → 立即启动增量同步
3. **执行**：
   - 对3个新端点从路由注册代码+handler函数提取签名、参数、响应模型
   - 为每个端点生成Markdown文档片段（含请求/响应示例）
   - 对1个废弃端点在原有文档顶部插入 `@deprecated since v2.3.0` 横幅
   - 追加3条feat类型的CHANGELOG条目
   - 更新OpenAPI JSON schema
4. **验证**：
   - 交叉引用检查：新增的3个内部链接全部有效 ✓
   - 示例代码语法检查：Python示例全部通过ast.parse ✓
   - 废弃标记一致性：代码@deprecated ↔ 文档标记一致 ✓
   - 质量评分：94分（A级）
5. **记录**：写入操作日志，通知相关人员文档已更新

### 场景2：版本发布前的全量文档重建

**背景**：项目准备发布 v3.0.0（major版本），tag即将被打上。

**自主执行流程：**

1. **感知**：检测到version字段从 `2.x.x` 跳升至 `3.0.0`，且存在 `BREAKING CHANGE` commit
2. **决策**：Major版本发布 → 强制全量重建 → 触发全部4种格式输出
3. **执行**：
   - 全量AST解析当前代码库，重建完整的API文档索引
   - 逐个比对旧版文档，生成migration guide（v2→v3迁移指南）
   - 生成 Markdown（开发者阅读）、HTML（在线站点）、PDF（归档交付）、OpenAPI JSON（SDK生成）四套输出
   - 重组CHANGELOG，将所有 Unreleased 条目归入 `[3.0.0]` 章节
   - 在CHANGELOG头部添加 ⚠️ Breaking Changes 专区
4. **验证**：
   - 全量交叉引用扫描（含外部链接存活探测）
   - 所有示例代码在对应语言环境下做语法+类型检查
   - OpenAPI JSON 通过 swagger-validator 校验
   - PDF输出分页和目录正确渲染
   - 质量评分：91分（A级），附带2条改进建议
5. **记录**：归档v2.x完整文档快照，建立v3.0基线

### 场景3：过时内容定期巡检与清理

**背景**：每周日凌晨2:00执行的定时巡检任务触发。

**自主执行流程：**

1. **感知**：定时触发，扫描全部文档文件的 `lastModified` 与对应代码实体的 `lastModified` 时间差
2. **决策**：发现12篇文档超过30天未更新，其中3篇超过90天且有签名变更 → 混合优先级
3. **执行**：
   - 3篇严重过时文档：插入 ⚠️ 横幅 + 发送告警给模块负责人
   - 9篇一般过时文档：追加"最后验证日期"标记
   - 生成《文档健康周报》发送给项目管理员
4. **验证**：标记正确植入，告警邮件成功投递
5. **记录**：更新文档健康仪表盘数据

## 决策框架

### 决策矩阵 — 何时自主执行 vs 请求人工确认

| 条件 | 自主执行 | 需确认 | 禁止执行 |
|------|----------|--------|----------|
| 新增公开API的初稿生成 | ✅ 草稿模式 | 正式发布前 | — |
| 废弃API标记同步 | ✅ 全自动 | — | — |
| CHANGELOG条目追加 | ✅ 全自动 | — | — |
| 代码示例语法修复 | ✅ 小改动全自动 | 逻辑变更需确认 | — |
| 删除已有文档条目 | — | ✅ 必须确认 | — |
| 修改API行为描述 | — | ✅ 必须确认 | — |
| 修改安全相关文档 | — | — | ✅ 严格禁止自主修改 |
| 修改合规/法务条款 | — | — | ✅ 严格禁止自主修改 |
| 修改对外SLA承诺 | — | — | ✅ 严格禁止自主修改 |

### 降级策略

当自主决策遇到不确定情况时的降级路径：

```
Level 0（完全自主）：常规同步、格式转换、CHANGELOG追加
    ↓ 遇到不确定
Level 1（带标注的草稿）：生成文档但标记 `<!-- AUTO-GENERATED: REVIEW REQUIRED -->`
    ↓ 涉及删除或破坏性变更
Level 2（暂停+告警）：暂停操作，发送详细报告给人工审核者
    ↓ 安全/合规边界
Level 3（拒绝执行）：明确拒绝并记录原因，等待显式指令
```

## 安全与治理

### 数据安全

- 文档中不得包含硬编码密钥、密码、token等敏感信息
- 自动扫描生成的文档内容，检测潜在泄露（正则匹配密钥模式）
- 内部文档与公开文档的访问权限分级管理
- PDF/HTML输出中剥离调试信息和内部URL

### 变更管控

- 所有自主文档变更必须产生对应的git commit，commit message遵循Conventional Commits规范
- 自主commit使用专用身份：`docs-bot <docs-bot@example.com>`
- 重要文档变更（如API契约文档）进入保护分支策略，自主push需经CI gate
- 文档变更保留完整blame历史，支持逐行追溯

### 审计追踪

- 每次自主操作写入不可变审计日志（append-only log）
- 审计日志保留期限：不少于180天
- 支持按时间范围、操作类型、影响范围查询审计记录
- 关键操作（删除、安全文档修改）触发实时告警

## 协作关系

### 上游依赖

| 协作对象 | 交互内容 | 交互频率 | 接口协议 |
|----------|----------|----------|----------|
| 代码仓库（Git） | diff信息、commit元数据、branch/tag事件 | 实时（Webhook）+ 定时 | Git CLI / GitHub API |
| CI/CD流水线 | 构建/部署事件、版本号信息 | 事件驱动 | Webhook / 环境变量 |
| Issue跟踪系统 | 文档相关issue/PR标签 | 实时 | REST API |

### 下游消费者

| 协作对象 | 提供内容 | 交付物格式 | 更新策略 |
|----------|----------|------------|----------|
| template_management_si | 文档模板最佳实践 | Checklist + 示例 | 按需推送 |
| knowledge_base_si | 从文档中提炼的知识条目 | 结构化知识卡片 | 事件驱动 |
| standardization_si | 文档风格规范数据 | 规则集 + 违规统计 | 周报 |
| 开发团队 | 最终文档产物 | MD/HTML/PDF/OAS | 按触发条件 |
| API消费者 | OpenAPI规范 | JSON Schema | 版本发布时 |

### 同级协作

| 协作对象 | 协作场景 | 协议 |
|----------|----------|------|
| 其他三司 | 跨司知识共享、联合巡检 | 共享事件总线 |
| 外部文档工具（MkDocs/Sphinx/Docusaurus） | 文档站构建集成 | 配置文件 + Hook |

---

## 🤝 v5.1 增强：Agency Agent 协作指南

### 可调用的 Agency Agents

| Agent 名称 | 所属部门 | 协作模式 | 适用场景 |
|-----------|---------|---------|---------|
| Technical Writer | 内容创作部 | 请求-响应 | 复杂技术文档的深度撰写与润色 |
| Document Generator | 文档工程部 | 流水线集成 | PDF/PPTX/DOCX/XLSX 多格式自动化输出 |

### Agent 协作工作流

1. **需求分析**：documentation_si 接收文档生成请求，解析目标格式、受众和内容范围
2. **内容准备**：从代码/注释/已有Markdown中提取结构化内容，构建统一中间表示（IR）
3. **Agent 委派**：
   - 深度技术写作需求 → 调用 **Technical Writer** 进行专业撰写，确保技术准确性与可读性
   - 多格式发布需求 → 调用 **Document Generator** 执行PDF/PPTX/DOCX/XLSX渲染输出
4. **质量协同**：Agent返回初稿后，documentation_si执行交叉引用验证、示例代码可执行性检查
5. **整合交付**：将Agent产出纳入版本化管理，生成多格式交付物
6. **反馈闭环**：收集读者反馈，持续优化Agent协作参数与模板

### 典型协作场景

- **场景1 - API参考手册多格式发布**：documentation_si 从代码提取API签名和示例 → Technical Writer 撰写概念说明和使用指南 → Document Generator 输出PDF（离线归档）+ HTML（在线站点）+ DOCX（合规交付）
- **场景2 - 项目年度技术报告**：documentation_si 汇总全年CHANGELOG和技术指标 → Technical Writer 按照品牌叙事框架组织内容 → Document Generator 生成PPTX（管理层汇报）+ XLSX（数据附录）
- **场景3 - 客户交付文档包**：documentation_si 整合部署指南、API文档和FAQ → Technical Writer 针对客户技术背景调整表述风格 → Document Generator 打包输出完整交付物集

---

## 🏗️ v5.1 增强：Harness 工程实践

### 相关 Harness 模块
- Harness CI 文档发布流水线（Documentation Publish Pipeline）
- Harness CD 文档站点部署（Docs Site Deployment）
- Harness Feature Flags 文档版本切换（Doc Versioning）

### 实践指南
- **CI质量门禁集成**：在Harness CI Pipeline中将文档质量评分卡作为Gate条件，A级/B级自动发布至文档站，C级以下阻断并通知reviewer
- **CD多环境文档分发**：利用Harness CD的差异化部署能力，将内部详细文档部署至内部门户，将面向客户的精简版文档部署至公网文档站- **版本化文档管理**：结合Harness Service Overrides机制，为不同产品版本的文档维护独立但结构一致的发布通道

---

## 🆕 v6.0 增强能力集成

### MARC资源协调器集成指南

本司在多Agent并发场景下的资源协调要求：

#### 资源锁机制
- **文件写锁**：当本司需要修改文档文件（Markdown/RST/reStructuredText）、文档配置、索引文件时，必须通过MARC申请互斥锁
  ```python
  # 示例：申请文件写锁
  from skillscripts.resource_coordinator import LockManager, LockType
  lock_mgr = LockManager()
  lock_id = lock_mgr.acquire_lock(
      resource_id="path/to/docs/api-guide.md",
      agent_id="文档规范化司",
      lock_type=LockType.EXCLUSIVE,
      priority=5,
      timeout=120.0
  )
  ```
- **读锁**：读取共享文档、模板库、风格指南时申请读锁（高频查询场景）
- **释放锁**：文档更新操作完成后立即释放锁，避免阻塞其他司的文档访问

#### 终端会话池使用
- 从MARC终端会话池获取会话执行文档构建命令、链接检查脚本、格式化工具
- 会话使用完毕后及时归还池中
- 单个命令超时设置为300秒（大型文档站点构建可能耗时较长）

#### 并发安全注意事项
- 多Agent同时更新同一文档时需独占写锁保护，避免内容冲突
- 文档索引和交叉引用更新需原子性操作，保证链接一致性
- 死锁预防：按固定顺序申请锁（先锁目标文档→再锁索引文件→最后锁导航结构）

### 四维度输出防线集成

| 防线层级 | 本司检查重点 | 自动化程度 |
|---------|-------------|----------|
| **提示词工程层** | 文档生成提示词、API文档提取提示词、README生成提示词 | 半自动（AI辅助） |
| **能力约束层** | 仅允许文档操作（创建/编辑/格式化），禁止修改业务逻辑代码 | 全自动 |
| **规则校验层** | 输出格式：标准Markdown文档、RST技术文档、JSON元数据 | 全自动 |
| **兜底恢复层** | 文档构建失败时回滚至上一稳定版本并通知相关方 | 半自动 |

### 操作优先级指引（v6.0核心）

本司推荐的操作方式：

1. 🥇 **Agent自主手动操作**（强烈推荐用于文档编写、格式调整、质量审查）
   - 示例：直接编辑Markdown文档、手动调整文档结构、编写API使用示例
   - 优势：精确控制文档内容、可逐步验证准确性、可随时回滚变更

2. 🥈 **规划脚本操作**（适用于批量文档生成、周期性链接检查）
   - 推荐脚本：
     - `skillscripts/resource_coordinator/quota_manager.py` — 检查文档存储配额
     - `skillscripts/open_source_philosophy/clawcode_sdd_tdd_engine.py` — SDD/TDD驱动的文档实践
     - `skillscripts/platform/powershell_adapter.py` — PS7环境适配

3. 🥉 **命令操作**（仅限文档站点构建、批量格式转换等极少数场景）
   - ⚠️ 必须预演影响范围（文档变更影响用户阅读体验）
   - ⚠️ 批量文档操作需抽样检查输出质量
   - 推荐使用PS7适配器转换mkdocs/sphinx等构建工具命令

### PowerShell 7 执行指南

本司相关操作的PS7适配要点：
- 文档构建：mkdocs build / sphinx-build 等命令在PS7中原生可用
- 文件操作：使用原生PowerShell Cmdlet处理Markdown/RST文件
- 链接检查：运行link-checker或类似工具验证文档内部和外部链接
- 编码：确保所有输出 UTF-8 无 BOM（文档内容和构建日志）

### 与其他司的协作接口

- 上游依赖：工部代码司（接收API变更信息以更新文档）、兵部测试司（获取测试用例用于示例编写）
- 下游输出：知识库司（推送高质量文档供知识提取）、标准化司（提供文档风格规范）
- 数据交换格式：Markdown / RST / JSON（统一UTF-8无BOM）

```