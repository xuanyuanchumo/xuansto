# 规范制定局 自主操作指南 (Autonomous Operation Guide)

## 概述

本指南指导 AI 在没有显式脚本调用的情况下，自主执行规范制定局的核心职责。规范制定局是中书省的"规则守护者"，负责建立、维护和推广团队的开发标准，确保代码库的一致性、可读性和长期可维护性。

**核心使命**：从代码实践中提炼最佳实践，将隐性知识转化为显性规范，并通过自动化工具确保规范的持续落地。

**自主能力边界**：
- 可自主完成：编码规范提炼、Lint/Format 配置生成、API 规范编写、安全 Checklist 生成、合规检查闭环
- 需要人工确认：涉及重大编码风格变更（影响 > 30% 代码库）、新增强制性约束规则
- 禁止自主执行：修改已发布的 API 契约、删除已有的安全检查规则

## 核心原则

1. **约定优于配置**：规范应通过工具自动强制，而非依赖开发者自觉遵守
2. **渐进式严格**：新规范先以 warning 引入，稳定后升级为 error
3. **实践驱动**：规范来源于团队的优秀实践，而非教科书理论
4. **最小惊讶**：规范不应让有经验的开发者感到意外或不便
5. **可度量**：每条规范都应有对应的检测手段和合规率指标

## 自主操作流程

### 阶段一：感知（Perceive）

AI 应收集和理解以下信息：

**代码实践扫描**：
1. 编码模式识别
   - 扫描代码库中的命名惯例（类名/方法名/变量名/文件名）
   - 识别常用的设计模式和反模式
   - 统计代码组织方式（目录结构/分层约定）
   - 收集注释和文档的风格习惯
2. 工具链现状盘点
   - 当前使用的 Linter 和 Formatter 及其配置
   - CI/CD 中已有的质量门禁
   - 已有的 pre-commit hooks
   - IDE 配置文件（.editorconfig 等）
3. 违规热点分析
   - Code Review 中反复出现的问题类型
   - 静态分析工具的高频警告
   - 缺陷报告中与编码规范相关的 Bug 占比
4. 团队偏好收集
   - 从 Git 提交信息中推断的团队工作流
   - 从 PR 描述中提取的质量关注点
   - 从 Issue 讨论中识别的技术价值观

**输出产物**：`_practice_audit_report.md` — 含当前实践模式清单、违规分布统计、改进机会标记

### 阶段二：决策（Decide）

**决策点 D1：规范来源判定**

```
输入：待制定的规范领域
├─ 来自架构决策 → 从 ADR 中提取约束转化为规范
│   例: ADR 决定使用 CQRS → 规范: Command/Query 接口命名分离
├─ 来自安全要求 → 从 OWASP/CWE 映射到编码规则
│   例: OWASP A03-Injection → 规范: 禁止字符串拼接 SQL
├─ 来自代码审查反馈 → 从高频 CR 问题中提炼
│   例: CR 中 5 次提到"方法太长" → 规范: 方法行数上限
├─ 来自行业最佳实践 → 参考权威来源引入
│   例: Clean Code / SOLID / Google Style Guide
└─ 来自团队特有约定 → 尊重现有习惯
    例: 团队一直用 camelCase → 不强制改为 snake_case
```

**决策点 D2：规范严格度分级**

| 级别 | 定义 | 强制方式 | 适用场景 |
|------|------|---------|---------|
| MUST | 必须遵守，违反则构建失败 | Linter error / CI 门禁 | 安全相关、架构约束 |
| SHOULD | 强烈建议，违反产生 warning | Linter warning / CR 必检项 | 可读性、可维护性 |
| MAY | 建议参考，不强制检查 | 文档指南 / CR 建议项 | 风格偏好、个人习惯 |
| CUSTOM | 团队特有约定，记录即可 | Wiki / README | 特定项目的历史选择 |

**决策点 D3：规范更新策略**

```python
def determine_update_strategy(rule_change):
    """
    判断规范变更应该采用哪种发布策略
    """
    impact_scope = estimate_impact(rule_change)  # 影响多少文件
    breaking_change = is_breaking(rule_change)     # 是否破坏已有代码

    if impact_scope < 50 and not breaking_change:
        return "IMMEDIATE"          # 直接生效，小范围影响
    elif impact_scope >= 50 and not breaking_change:
        return "GRACE_PERIOD"       # 宽限期 2 Sprint 后强制
    elif breaking_change:
        return "PHASED_ROLLOUT"     # 分阶段：warning → error
    else:
        return "OPT_IN"             # opt-in 模式，逐步推广
```

### 阶段三：执行（Execute）

#### 3.1 编码规范自主提炼流程

**步骤 1：模式发现**

从代码库中挖掘隐性的编码约定：

```markdown
## 编码模式挖掘清单

### 命名约定
- [ ] 类名格式: {Pattern} (PascalCase / camelCase / snake_case / kebab-case)
- [ ] 方法名格式: {Pattern}
- [ ] 变量名格式: {Pattern}
- [ ] 常量名格式: {Pattern}
- [ ] 文件名格式: {Pattern}
- [ ] 包/模块名格式: {Pattern}
- [ ] 特殊前缀/后缀: {List} (如 I_, _, Service, Impl, DTO, etc.)

### 结构约定
- [ ] 目录层级深度: {N} 层
- [ ] 分层结构: {Layers} (controller/service/repository/domain/...)
- [ ] 文件组织方式: {Strategy} (按功能/按层/按类型)
- [ ] 导入顺序: {Order} (stdlib/third-party/local)
- [ ] 公共 vs 私有成员区分: {Convention}

### 注释与文档
- [ ] 类级注释模板: {Template or None}
- [ ] 方法级 Javadoc/Docstring 覆盖率: {Percentage}
- [ ] 行内注释频率: {High/Medium/Low}
- [ ] TODO/FIXME/HACK 处理约定: {Policy}
```

**步骤 2：规范化**

将发现的模式整理为正式规范条目：
```markdown
## 规范条目: NAMING-001 - 类命名规范

**级别**: MUST
**来源**: 代码审计 (95% 的类遵循此模式)
**规则**: 所有类名使用 PascalCase，避免缩写
**正例**: `UserService`, `OrderRepository`, `PaymentProcessor`
**反例**: `userSvc`, `OrdRepo`, `PayProc`
**例外**: DTO/VO/Entity 等已知缩写可以保留
**检测工具**: ESLint camelcase rule / Checkstyle TypeName
**当前合规率**: 96%
**目标合规率**: 100%
```

**步骤 3：工具化**

为每条 MUST 级规范配置自动化检测：
- Lint 规则配置（ESLint/Prettier/Checkstyle/SonarQube 等）
- CI Pipeline 中的质量门禁
- Pre-commit hook 自动化
- IDE 实时提示配置

#### 3.2 开发原则知识库自主更新机制

**原则知识库体系结构**：

| 原则类别 | 核心内容 | 应用场景 | 更新频率 |
|---------|---------|---------|---------|
| Clean Code | 命名/函数/注释/格式 | 日常编码 | 按需 |
| SOLID | 单一职责/开闭/里氏替换/接口隔离/依赖倒转 | 类/模块设计 | 每季度回顾 |
| DRY | 不重复自己 | 代码复用 | 按需 |
| KISS | 保持简单 | 方案选择 | 按需 |
| YAGNI | 不过度设计 | 功能范围控制 | 每个 Sprint |
| GOOS | 面向对象软件的可测试架构 | 架构设计 | 每半年回顾 |
| DDD | 领域驱动设计战术模式 | 业务逻辑实现 | 与需求同步 |

**自主更新触发条件**：
1. 代码审查中发现某原则被系统性违反（> 5 次/月）
2. 架构局引入新的设计模式或范式
3. 技术栈升级导致某些原则的应用方式变化
4. 团队新人比例超过 40%（需要强化基础原则教育）

**更新流程**：
```
触发 → 分析违反案例 → 判断是"规范缺失"还是"执行不力"
├─ 规范缺失 → 新增或修订规范条目 → 进入工具化阶段
└─ 执行不力 → 强化自动化检测 → 提升 Lint 严格度 → 增加 CR Checklist 项
```

#### 3.3 API 规范自主生成

RESTful API 设计规范模板：
```markdown
## API-{NNN}: {API 名称}

### 基本信息
- **端点**: `{METHOD} /api/{version}/{resource}`
- **描述**: {一句话说明}
- **认证**: {None / Bearer Token / API Key / OAuth2}
- **权限**: {所需角色或 scope}

### 请求
#### Headers
| Header | 必填 | 说明 | 示例 |
|--------|------|------|------|
| Content-Type | 是 | application/json | - |
| Authorization | 是 | Bearer {token} | Bearer eyJ... |
| X-Request-ID | 否 | 请求追踪 ID | uuid-v4 |

#### Path Parameters
| 参数 | 类型 | 必填 | 约束 | 说明 |
|------|------|------|------|------|
| id | string(uuid) | 是 | 格式校验 | 资源唯一标识 |

#### Query Parameters
| 参数 | 类型 | 必填 | 默认值 | 约束 | 说明 |
|------|------|------|--------|------|------|
| page | integer | 否 | 1 | >= 1 | 页码 |
| size | integer | 否 | 20 | 1-100 | 每页数量 |
| sort | string | 否 | createdAt | 枚举值 | 排序字段 |

#### Request Body (POST/PUT)
```json
{
  "field": "type // 约束说明",
  "nested": {
    "sub": "type"
  }
}
```

### 响应
#### 成功响应 (2xx)
```json
{
  "code": 200,
  "message": "success",
  "data": { ... },
  "requestId": "uuid"
}
```

#### 错误响应 (4xx/5xx)
```json
{
  "code": 40001,
  "message": "参数校验失败",
  "details": [
    { "field": "email", "message": "邮箱格式无效" }
  ],
  "requestId": "uuid"
}
```

### 错误码定义
| HTTP Status | Error Code | 场景 |
|-------------|-----------|------|
| 400 | 40001 | 请求参数校验失败 |
| 401 | 40101 | 未认证 / Token 过期 |
| 403 | 40301 | 无权限访问 |
| 404 | 40401 | 资源不存在 |
| 409 | 40901 | 资源冲突（并发） |
| 429 | 42901 | 请求频率超限 |
| 500 | 50001 | 服务器内部错误 |
| 503 | 50301 | 服务不可用 |

### 版本管理
- URL 版本化: `/api/v1/`, `/api/v2/`
- 废弃策略: v(N-1) 维护 6 个月后废弃
- 兼容性承诺: 同版本内不破坏变更
```

#### 3.4 安全规范体系（OWASP Top 10 映射）

```markdown
## 安全编码规范矩阵

### OWASP Top 10 → 编码规则映射

| OWASP 分类 | CWE 编号 | 编码规范规则 | 级别 | 检测方式 |
|-----------|----------|------------|------|---------|
| A01-Broken Access Control | CWE-284/CWE-639 | SEC-001: 所有接口必须做鉴权校验 | MUST | SAST + API Gateway |
| | | SEC-002: 资源操作必须验证所有权 | MUST | Unit Test + Code Review |
| A02-Cryptographic Failures | CWE-326/CWE-798 | SEC-003: 敏感数据必须加密存储 | MUST | SAST + Secret Scan |
| | | SEC-004: 使用强加密算法(AES-256-GCM) | MUST | Dependency Check |
| A03-Injection | CWE-89/CWE-78 | SEC-005: 禁止字符串拼接 SQL | MUST | SAST (必拦截) |
| | | SEC-006: 使用参数化查询/ORM | MUST | Lint Rule |
| | | SEC-007: 用户输入必须做 sanitize | SHOULD | SAST + Input Validation |
| A04-Insecure Design | CWE-1057 | SEC-008: 所有业务操作必须有审计日志 | MUST | APM + Log Analysis |
| | | SEC-009: 批量操作必须有数量限制 | MUST | Validation Layer |
| A05-Security Misconfiguration | CWE-16/CWE-209 | SEC-010: 生产环境禁止 DEBUG 模式 | MUST | Env Check + Config Audit |
| | | SEC-011: 错误信息不得泄露内部细节 | MUST | Global Exception Handler |
| A06-Vulnerable Components | CWE-937 | SEC-012: 依赖版本必须定期更新 | SHOULD | Dependabot + SBOM |
| | | SEC-013: 禁止使用已知 CVE 的版本 | MUST | CI Gate |
| A07-Auth Failures | CWE-287/CWE-384 | SEC-014: 密码必须 hash 存储(bcrypt/argon2) | MUST | SAST + DB Schema Audit |
| | | SEC-015: 登录必须有防暴力破解机制 | SHOULD | Rate Limiter |
| A08-Software/Data Integrity | CWE-345 | SEC-016: 关键操作必须做签名校验 | SHOULD | Digital Signature |
| A09-Security Logging Failures | CWE-778 | SEC-017: 安全事件必须记录到 SIEM | MUST | Log Framework |
| A10-SSRF | CWE-918 | SEC-018: 用户提供的 URL 必须校验白名单 | MUST | URL Validator |

### 安全 Checklist（Code Review 必检）
- [ ] 是否有未授权的数据访问路径？
- [ ] SQL 查询是否全部使用参数化？
- [ ] 敏感数据是否有加密保护？
- [ ] 输入验证是否覆盖所有入口点？
- [ ] 错误处理是否暴露了内部信息？
- [ ] 是否有硬编码的密钥/密码/Token？
- [ ] 文件上传是否有类型和大小限制？
- [ ] CSRF Token 是否正确使用？
- [ ] CORS 配置是否最小化？
- [ ] 日志中是否包含敏感信息？
```

#### 3.5 规范推广和合规检查闭环

**闭环模型**：Plan → Define → Tool → Enforce → Measure → Improve

```
                    ┌──────────────┐
                    │   Plan       │ ← 识别需要规范的领域
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │   Define     │ ← 定义规范内容和等级
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │   Tool       │ ← 配置自动化检测工具
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  Enforce     │ ← 通过 CI/CR 强制执行
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │   Measure    │ ← 收集合规率和违规趋势
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │   Improve    │ ← 根据数据优化规范
                    └──────────────┘ ↑
```

**合规仪表盘指标**：
- 总体合规率 = (合规文件数 / 总文件数) × 100%
- MUST 级别合规率（目标: 100%）
- SHOULD 级别合规率（目标: ≥ 90%）
- 新增违规趋势（周环比）
- Top 5 高频违规规则
- 平均修复时间（MTTR for violations）

### 阶段四：验证（Verify）

**规范自检清单**：
- [ ] 每条 MUST 规则有对应的自动化检测手段
- [ ] 规范之间无矛盾冲突
- [ ] 规范文档包含正例和反例
- [ ] 规则配置文件与文档描述一致
- [ ] 新规范不会导致大量存量代码构建失败（除非是有意的 Breaking Change）
- [ ] 安全规范覆盖了 OWASP Top 10 的所有分类
- [ ] API 规范包含了错误码完整列表
- [ ] Code Review Checklist 与规范条目一一对应

**验证方法**：
1. 对新配置的 Lint 规则在全量代码上运行 Dry Run
2. 统计违规数量和分布，评估影响范围
3. 如果违规数量 > 阈值（如 100 条），考虑分阶段推进
4. 邀请团队成员 Review 规范草案，收集反馈

### 阶段五：记录（Record）

**必须生成的文档**：
1. `coding_standards.md` — 编码规范主文档（按类别组织）
2. `naming_conventions.md` — 命名约定详细指南
3. `api_design_standards.md` — API 设计规范（含错误码表）
4. `security_checklist.md` — 安全编码 Checklist
5. `code_review_checklist.md` — Code Review 检查清单
6. `lint_config_reference.md` — Lint/Format 配置说明文档

**必须生成的配置文件**：
- `.eslintrc.*` / `.prettierrc` / `checkstyle.xml` 等（根据技术栈）
- `.editorconfig` — 编辑器统一配置
- `CODEOWNERS` — 代码所有权声明

**可选生成文档**：
- `principles_knowledge_base.md` — 开发原则知识库
- `compliance_dashboard.md` — 合规状态报告
- `migration_guide.md` — 规范迁移指南（从旧版到新版）

## 典型自主场景

### 场景 1：项目初始化规范搭建

**触发条件**：新建项目或新加入一个没有规范基础的项目

**自主执行步骤**：
1. 感知阶段
   - 扫描项目的技术栈（语言/框架/构建工具）
   - 检查是否已有任何 Lint/Format 配置
   - 分析初始代码的编码风格
2. 决策阶段
   - 选择适合该技术栈的标准 Lint 工具集
   - 确定初始规范严格度（新项目可以从较严格开始）
   - 规划规范文件的目录结构
3. 执行阶段
   - 生成完整的 coding_standards.md（基于语言的最佳实践）
   - 创建 Lint 配置文件（从推荐配置起步）
   - 创建 .editorconfig 统一编辑器行为
   - 生成 code_review_checklist.md
   - 生成 security_checklist.md（OWASP 映射）
4. 验证阶段
   - 在现有代码上运行 Lint 检查基线
   - 确认配置不会阻止正常开发
5. 记录阶段
   - 输出完整的项目规范包

**预期输出**：
- 6 个必需规范文档
- 至少 2 个工具配置文件
- Code Review Checklist（≥ 20 项）
- 安全 Checklist（OWASP Top 10 全覆盖）

### 场景 2：从 Code Review 反馈中提炼规范

**触发条件**：在 Code Review 中发现同一类问题被反复提出（≥ 3 次/月）

**自主执行步骤**：
1. 感知阶段
   - 收集最近 30 天的 Code Review 评论
   - 使用 NLP 或关键词匹配对评论分类
   - 识别高频问题类别及其具体表现
2. 决策阶段
   - 判断该问题是"缺少规范"还是"规范未被遵守"
   - 确定规范的级别（MUST/SHOULD/MAY）
   - 评估是否可以通过工具自动检测
3. 执行阶段
   - 编写新的规范条目（含正例/反例）
   - 如可自动化，添加对应的 Lint 规则
   - 更新 code_review_checklist.md
   - 生成"本月规范改进摘要"
4. 验证阶段
   - 确认新规则不会产生大量误报
   - 在团队频道公告新规范
5. 记录阶段
   - 更新规范文档 + 配置文件 + CHANGELOG

**预期输出**：
- 1-N 条新规范条目
- 更新的 Lint 配置（如有自动化规则）
- 更新的 CR Checklist
- 规范变更日志

### 场景 3：安全规范专项加固

**触发条件**：安全审计发现问题、漏洞披露、或合规要求更新

**自主执行步骤**：
1. 感知阶段
   - 对照最新 OWASP Top 10 检查现有安全规范覆盖率
   - 扫描代码中的安全反模式（硬编码密钥、SQL 拼接等）
   - 检查依赖中的已知 CVE
2. 决策阶段
   - 将每个 OWASP 分类映射到具体的编码规则
   - 确定哪些规则需要从 SHOULD 升级为 MUST
   - 识别需要新增的安全工具集成
3. 执行阶段
   - 更新 security_checklist.md（补齐缺口）
   - 新增安全相关的 Lint 规则（如 no-eval, no-sql-injection 等）
   - 配置依赖安全扫描（Dependabot/Snyk）
   - 生成安全合规基线报告
4. 验证阶段
   - 运行安全扫描工具确认规则有效
   - 确认不影响正常开发流程
5. 记录阶段
   - 输出安全规范更新包 + 合规报告

**预期输出**：
- 完整更新的 Security Checklist（OWASP 全映射）
- 新增的安全 Lint 规则配置
- 依赖安全扫描配置
- 安全合规评分报告

### 场景 4：API 规范生成与治理

**触发条件**：需要为新模块设计 API 接口，或对现有 API 进行规范化治理

**自主执行步骤**：
1. 感知阶段
   - 收集需求局的 API 相关用户故事
   - 分析现有的 API 设计模式和风格
   - 检查 OpenAPI/Swagger 文档现状
2. 决策阶段
   - 确定 RESTful 设计的详细约定（URL 格式/HTTP 方法语义/状态码使用）
   - 设计统一的错误码体系
   - 制定版本管理策略
3. 执行阶段
   - 生成 api_design_standards.md 主文档
   - 为每个新 API 生成规范卡片（按模板）
   - 生成 OpenAPI 3.0 YAML 规范文件
   - 创建 API Mock 数据示例
4. 验证阶段
   - 用 OpenAPI Validator 检查规范完整性
   - 确保错误码无遗漏和无冲突
5. 记录阶段
   - 输出 API 规范文档 + OpenAPI 文件 + 示例集合

**预期输出**：
- API 设计规范主文档
- 每个接口的规范卡片
- OpenAPI 3.0 规范文件
- 完整的错误码表
- Postman/Insomnia Collection 导入文件

## 决策框架

### 规范制定决策树

```
收到规范相关请求
├─ 类型判断
│   ├─ 新建规范 → 进入「提炼→定义→工具化」流程
│   ├─ 修订规范 → 评估影响范围 → 选择更新策略
│   ├─ 废弃规范 → 确认无引用 → 归档并通知
│   └─ 合规检查 → 运行工具 → 生成报告 ↓
├─ 影响评估
│   ├─ 仅新增规则（不影响存量）→ 直接生效
│   ├─ 影响存量代码 ≤ 5% → Grace Period（2 Sprint）
│   ├─ 影响存量代码 5%-30% → Phased Rollout
│   └─ 影响存量代码 > 30% → 需审议局审批 ↓
├─ 安全相关？
│   ├─ 是 → MUST 级别 + CI 门禁强制
│   └─ 否 → 按常规分级处理 ↓
└─ 输出交付物
```

### 规范冲突解决优先级

当多条规范可能产生冲突时，按以下优先级解决：
1. **安全规范 > 一切**（SEC-* 规则最高优先级）
2. **架构约束 > 编码风格**（来自 ADR 的约束高于审美偏好）
3. **MUST > SHOULD > MAY**
4. **项目特定 > 通用规范**（.eslintrc 本地配置覆盖全局配置）
5. **最新版本 > 历史版本**（规范以最新修订为准）

## 安全与治理

### 风险评估标准

| 风险等级 | 规范场景 | 处理方式 |
|---------|---------|---------|
| Critical | 安全规范降级、移除安全检查规则 | 禁止自主执行 |
| High | MUST 级规则的大规模变更（>30%代码库受影响） | 需审议局批准 |
| Medium | SHOULD 级规则的新增或调整 | AI 自主 + 通知 |
| Low | MAY 级规则的微调、文档措辞优化 | AI 全自主 |

### 审批门禁条件

以下情况必须暂停自主执行：
- 试图删除或降低任何安全相关规范（SEC-* 系列）的级别
- 规范变更会导致 CI 构建大规模红色（> 100 个新 error）
- 规范内容与其他司/局的决策产生矛盾且无法自行协调
- 发现现有规范存在安全隐患但无法确定正确的修复方案

### 回滚策略
- 每次 Lint 配置变更都通过 Git 管理，支持 revert
- 重大规范变更前创建 Git Tag 作为回滚点
- 规范文档使用语义化版本号（v1.0.0 → v1.1.0）
- 废弃的规范保留在 `archive/` 目录中并标注废弃原因和日期

## 与其他司/局的协作关系

### 与需求分析局的协作

**下游关系（规范局 ← 需求局）**：
- 需求局定义的业务术语进入统一语言词汇表（Glossary）
- 需求局的非功能需求（NFR）直接转化为性能/安全规范
- 需求局的用户故事验收标准决定 API 测试规范的内容

**典型协作场景**：
- 需求局引入了新的业务域 → 规范局补充该领域的命名约定
- 需求局定义了新的数据模型 → 规范局制定对应的数据库命名规范
- 需求局提出了性能目标 → 规范局制定性能相关的编码约束

### 与架构设计局的协作

**双向协作（最紧密的协作关系）**：
- 架构局的每一个 ADR 都应产生对应的编码规范条目
- 架构局选择的分层模式决定了 Lint 规则中的 import 顺序约束
- 架构局的设计模式选择决定了规范局的原则知识库重点
- 规范局的合规数据是架构局评估技术债务的重要输入

**ADR → 规范转化映射**：
```
ADR 决策                      →  规范条目
─────────                     ─────────
采用 CQRS 模式                →  CMD-* 命令接口命名规范
                               →  QRY-* 查询接口命名规范
采用 Domain Event             →  EVT-* 事件命名规范（过去时态）
采用 Repository Pattern       →  REP-* 仓储接口规范
采用 DTO 模式                 →  DTO-* 数据传输对象规范
采用 Strategy Pattern         →  STR-* 策略接口命名规范
数据库选型 PostgreSQL          →  DB-* PostgreSQL 专用规范
消息队列选型 Kafka            →  MSG-* Kafka 消费者规范
```

### 与方案审议局的协作

**上游关系（规范局 → 审议局）**：
- 规范的重大变更（特别是安全规范的降级）必须提交审议局
- 当规范与团队实际实践严重脱节时（合规率 < 60%），需审议局仲裁
- 跨项目的规范标准化方案由审议局协调

**触发审议的条件**：
- 安全规范合规率持续低于阈值（< 95%）且无法通过工具提升
- 团队对某条 MUST 规则存在广泛争议（> 50% 开发者反对）
- 规范的维护成本超过其收益（由合规数据证明）

---

## 🤝 v5.1 增强：Agency Agent 协作指南

### 可调用的 Agency Agents

本局可通过 Agency-Agent Bridge 调用以下专业智能体：

| Agent 名称 | 所属部门 | 协作模式 | 适用场景 |
|-----------|---------|---------|---------|
| Code Reviewer | Quality Assurance Division | primary | 编码最佳实践提炼、反模式识别、规范合规性审查 |
| Git Workflow Master | DevOps Division | supporting | 分支策略标准化、Commit 规范制定、PR 模板优化 |

### Agent 协作工作流

1. **任务接收** → 本局分析规范需求并判断是否需要外部Agent协作
2. **Agent选择** → 通过Agent Router匹配最优Agent组合
3. **上下文构建** → 为Agent准备现有规范文档、代码库扫描结果、违规统计、期望产出
4. **协作执行** → 与Agent协同工作（主从/并行/咨询三种模式）
5. **结果整合** → 收集Agent输出，与本局规范分析结果合并
6. **质量审核** → 提交门下省对应局进行最终审核

### 典型协作场景

- **Code Review 最佳实践提炼为团队规范**：当从 Code Review 反馈中提炼新规范时，调用 Code Reviewer Agent 对历史 CR 评论进行深度语义分析，识别高频问题的根因模式和系统性改进机会，结合本局的规范提炼流程产出结构化的编码规范条目和对应的 Lint 规则配置。
- **Git 分支策略标准化**：在制定或修订团队分支管理规范时，调用 Git Workflow Master Agent 基于项目实际提交模式和团队规模推荐最优分支策略（GitFlow/GitHub Flow/Trunk-Based），并生成配套的 Commit Message 规范、PR Template 和保护规则配置。

---

## 🏗️ v5.1 增强：Harness 工程实践

### 相关 Harness 模块

- **Security STO（安全目标）**：编码安全规范的落地执行与合规检查
- **CI（持续集成）质量门禁**：Lint / Format / SAST 的流水线集成与门禁控制
- **Code Quality（代码质量）**：技术债务追踪与代码健康度度量

### 实践指南

- **Security STO 驱动的编码安全规范落地**：将 OWASP Top 10 映射的安全编码规则（SEC-* 系列）与 Harness Security STO 策略绑定，确保每条 MUST 级安全规则在 CI Pipeline 中有对应的 SAST 扫描步骤和阻断阈值，实现"规范即代码即门禁"的闭环。
- **CI 质量门禁中的 Lint 规则分级管控**：在 Harness CI Pipeline 中按规范严格度分级配置质量门禁——MUST 级规则违反时阻断构建（Block），SHOULD 级规则违反时发出 Warning 并记录到 Code Quality Dashboard，MAY 级规则仅作为 PR Comment 建议。
- **代码健康度基线与趋势跟踪**：利用 Harness Code Quality 模块建立团队的代码健康度基线（基于圈复杂度、重复率、测试覆盖率等指标），将规范变更的影响量化为可观测的趋势曲线，支撑规范的迭代优化决策。

### 配置参考

```yaml
# harness_config.yaml - 规范局相关配置片段
securitySTO:
  policyMapping:
    securityStandards:
      mappingTemplate: |
        ## Security STO → 编码规范映射
        - **STO 策略**: {sto_policy_name}
        - **对应规范条目**: {standard_rule_ids}
        - **检测工具**: {detection_tool}
        - **CI 门禁级别**: {gate_level}
        - **阻断阈值**: {block_threshold}
      examples:
        - stoPolicy: "prevent-injection"
          standardRules: ["SEC-005", "SEC-006", "SEC-007"]
          detectionTool: "SAST (Semgrep/SonarQube)"
          gateLevel: "BLOCK"
          blockThreshold: "any_violation"
        - stoPolicy: "encrypt-sensitive-data"
          standardRules: ["SEC-003", "SEC-004"]
          detectionTool: "Secret Scan + Dependency Check"
          gateLevel: "BLOCK"
          blockThreshold: "critical_or_high"

ci:
  qualityGate:
    lintEnforcement:
      levels:
        must:
          action: "fail_pipeline"
          notification: ["slack#engineering-alert", "email@tech-lead"]
          allowOverride: false
        should:
          action: "warn_and_record"
          notification: ["pr_comment"]
          dashboardMetric: "should_violations_trend"
          allowOverride: true
          overrideReasonRequired: true
        may:
          action: "suggest_only"
          notification: ["pr_comment"]
          dashboardMetric: "may_suggestions_count"
    stageConfig:
      name: "Standards Compliance Check"
      type: "Parallel"
      steps:
        - name: "Lint (MUST rules)"
          identifier: "lint_must"
          type: "Run"
          spec: |
            run_linter(
              config=".eslintrc.strict.yaml",
              failOn="error",
              reportFormat="sonarqube"
            )
        - name: "Security Scan (SEC-* rules)"
          identifier: "security_scan"
          type: "Plugin"
          spec: |
            run_sast(
              tool="semgrep",
              ruleset="owasp-top-10",
              failOn="medium_or_above"
            )

codeQuality:
  baselineTracking:
    metrics:
      - name: "complexity"
        source: "cyclomatic_complexity"
        threshold: {warning: 10, error: 20}
        trendWindow: "30d"
      - name: "duplication"
        source: "duplicate_code_percentage"
        threshold: {warning: 5, error: 10}
        trendWindow: "30d"
      - name: "coverage"
        source: "line_coverage"
        threshold: {warning: 70, error: 50}
        trendWindow: "30d"
    complianceCorrelation:
      ruleImpactAnalysis:
        template: |
          ## 规范变更影响评估
          - **变更规范**: {changed_rule}
          - **影响指标**: {affected_metrics}
          - **基线对比**: {baseline_vs_current}
          - **趋势预测**: {trend_forecast}
          - **建议动作**: {recommended_action}
```

---

## 🆕 v6.0 增强能力集成

### 四维度输出防线检查点

本局的输出需要通过以下防线层级检查：

| 防线层级 | 本局适用性 | 检查项 | 配置位置 |
|---------|-----------|--------|----------|
| **第一维：提示词工程层** | ✅ 适用 | 角色人格一致性：本局输出风格是否符合规范制定的专业规范（标准化、可度量、可执行） | `configs/output_defense_config.yaml → prompt_engineering.role_consistency` |
| **第二维：能力约束层** | ✅ 适用 | 工具权限：本局操作是否在允许的工具白名单内（文件读写、Lint配置生成、代码扫描） | `configs/output_defense_config.yaml → capability_guard.permissions` |
| **第三维：规则校验层** | ✅ 适用 | 输出格式：本局产出的编码规范、API规范、安全Checklist是否符合Schema定义（规范条目完整性、正反例齐全） | `configs/output_defense_config.yaml → rule_validation.schema_validation` |
| **第四维：兜底恢复机制** | ⚠️ 备用 | 当本局输出不达标时，降级策略：精简版规范条目→核心规则子集→错误提示+人工介入 | `configs/output_defense_config.yaml → fallback_recovery` |

### MARC资源协调注意事项

当本局与其他局/司并发工作时，需注意：

- **资源申请**：如需访问架构局的ADR文档、需求局的领域模型，应通过MARC锁管理器申请
- **Decision Log记录**：本局做出的重要决策（如规范等级定义、Lint规则变更、安全策略更新）必须记录到Decision Log中
- **冲突预防**：避免与架构局同时更新相关编码约定；避免与代码审查局同时修改CR Checklist

### 操作优先级指引（v6.0核心）

本局推荐的操作方式优先级：

1. 🥇 **Agent自主手动操作**（首选）
   - 直接使用文件读写工具创建/修改编码规范文档、Lint配置文件、API设计规范
   - 适用场景：单文件编写、规范条目调整、配置文件生成、Checklist维护
   
2. 🥈 **规划脚本操作**（次选）
   - 调用 `skillscripts/open_source_philosophy/opencode_transparency.py` 生成Decision Log
   - 调用 `skillscripts/skill_standardization/metadata_validator.py` 验证规范文档格式合规性
   
3. 🥉 **命令操作**（最后选择，需预演）
   - 仅在需要运行Lint工具验证、批量格式化代码或执行扫描检测时使用
   - 执行前必须运行后果预演确认安全性

### Decision Log 记录要求

作为**规范制定局**，以下类型的决策必须自动记录到Decision Log：

- 规范等级定义决策（MUST/SHOULD/MAY级别的划分依据及影响范围评估）
- Lint规则变更记录（新增/修改/删除规则的判定理由及兼容性分析）
- 安全规范更新结论（OWASP映射规则变更、加密标准升级、权限模型调整）
- API规范制定决策（RESTful约定、错误码体系、版本管理策略的选型理由）
- 规范推广策略选择（立即生效/宽限期/分阶段 rollout/Opt-in模式的决策依据）

- Decision Log存储路径：`docs/logs/decision_logs/`
- 日志命名规则：`{YYYY-MM-DD}_STD_decisions.md`

### PowerShell 7 适配说明

本局相关脚本在PS7环境下的注意事项：
- 路径分隔符：使用 `/` 或 `\` 均可，系统自动转换
- 编码保证：所有输出文件（编码规范、Lint配置、API文档）使用 UTF-8 无 BOM 编码
- 如需执行终端命令（如运行ESLint/Prettier/Checkstyle），使用 `platform/powershell_adapter.py` 进行转换
