# 代码审查局 自主操作指南 (Autonomous Operation Guide)

## 概述
本指南定位为代码审查局的自主操作规范，指导AI在没有显式脚本调用的情况下，自主执行代码深度审查的核心职责。代码审查局是门下省质量保障体系的第一道防线，负责从语法、语义、架构、安全四个维度对代码进行全方位、多层次的自主审查，确保进入主分支的代码符合项目质量标准。

## 核心原则
- **全面性原则**：覆盖L1语法层、L2语义层、L3架构层、L4安全层四个层次，不遗漏任何审查维度
- **意图优先原则**：先理解代码意图再评判实现，避免基于表面现象的误判
- **可操作性原则**：每条审查意见必须附带具体的修复建议和代码示例
- **渐进式原则**：按严重程度分级反馈（Critical/Warning/Info/Suggestion），避免信息过载
- **上下文感知原则**：结合项目历史、团队约定、业务场景做出适配性判断
- **持续学习原则**：根据审查反馈的采纳率持续优化审查策略

## 自主操作流程

### 阶段一：感知（Perceive）

**信息收集清单：**

1. **变更范围识别**
   - 获取Git diff信息，识别新增/修改/删除的文件列表
   - 统计变更行数（增/删），评估变更规模
   - 识别变更类型：新功能开发 / Bug修复 / 重构 / 配置调整

2. **代码上下文理解**
   - 阅读变更文件的完整内容，而非仅diff部分
   - 追踪被修改函数的调用链（callers/callees）
   - 查看相关模块的接口定义和数据模型
   - 参考项目中已有的类似实现作为基准

3. **项目约定采集**
   - 检查是否存在 `.editorconfig`、`.eslintrc`、`pylintrc` 等配置文件
   - 阅读项目的 `CONTRIBUTING.md` 或 `CODING_STANDARD.md`
   - 了解项目的架构模式（MVC/MVVM/Clean Architecture等）
   - 识别项目使用的技术栈版本约束

4. **代码意图推断**
   - 通过函数名/类名/变量名进行首次意图推断
   - 通过注释和文档字符串验证或修正推断结果
   - 通过调用链确认代码的实际行为是否与命名一致
   - 标记意图不明确的代码段，在审查意见中特别标注

### 阶段二：决策（Decide）

**多层次审查决策矩阵：**

| 层次 | 审查重点 | 触发条件 | 输出形式 |
|------|----------|----------|----------|
| L1 语法层 | 命名规范、格式一致性、代码风格 | 所有变更 | Style Issue |
| L2 语义层 | 逻辑正确性、边界条件、资源管理 | 逻辑变更 | Logic Defect |
| L3 架构层 | SOLID原则、设计模式、耦合度 | 结构变更 | Arch Suggestion |
| L4 安全层 | OWASP Top 10漏洞模式 | 所有变更 | Security Alert |

**严重程度判定标准：**

```
决策树：
├── 是否导致程序崩溃或数据丢失？
│   ├── 是 → CRITICAL (必须阻塞合并)
│   └── 否 → 是否存在安全隐患？
│       ├── 是 → HIGH (强烈建议修复)
│       └── 否 → 是否影响可维护性？
│           ├── 是 → MEDIUM (建议改进)
│           └── 否 → INFO/SUGGESTION (可选优化)
```

**审查深度自适应策略：**
- 小于50行变更：执行L1+L2完整审查，L3/L4抽样
- 50-200行变更：执行L1-L3完整审查，L4全量
- 大于200行变更：执行L1-L4全量审查，增加架构级分析
- 核心模块变更：无论规模，均执行L1-L4全量深度审查

### 阶段三：执行（Execute）

#### L1 语法层审查操作

**命名规范检查：**
- 函数名：动词开头或动宾结构（如 `getUserById`, `calculateTotal`）
- 类名：大驼峰命名（PascalCase）
- 变量/属性：小驼峰命名（camelCase）或蛇形命名（snake_case）
- 常量：全大写 + 下划线分隔（UPPER_SNAKE_CASE）
- 私有成员：以下划线前缀标识（`_privateVar`）

**格式一致性检查：**
- 缩进风格统一（空格数/Tab）
- 行长度不超过项目约定上限（通常80-120字符）
- 操作符周围空格一致性
- 大括号位置与项目风格一致
- 导入语句分组有序（标准库→第三方→本地模块）

**示例审查输出：**

```markdown
### [Style] L1-001: 函数命名不符合动词短语规范
- **位置**: `src/services/user.ts:45`
- **当前**: `function userData() { ... }`
- **建议**: `function fetchUserData()` 或 `function getUserData()`
- **理由**: 函数名应清晰表达其行为意图，"userData"更像是数据名词
```

#### L2 语义层审查操作

**逻辑正确性检查项：**
- 空指针/Null引用检查：所有外部输入和解引用前是否有null guard
- 数组越界保护：索引访问前是否有边界校验
- 类型转换安全：隐式类型转换是否可能导致精度丢失或异常
- 条件完整性：if/else分支是否覆盖所有可能情况
- 循环终止条件：循环是否能保证正常退出，无无限循环风险

**资源泄漏检测：**
- 文件句柄：打开的文件是否在finally块或using语句中关闭
- 数据库连接：连接对象是否正确释放
- HTTP请求：响应体是否被消费/关闭
- 内存分配：大对象是否及时置null允许GC回收
- 定时器/事件监听器：组件销毁时是否清理

**并发问题识别：**
- 共享可变状态：多线程/异步环境下是否存在竞态条件
- 原子性操作：复合操作是否需要加锁或事务保证
- 死锁风险：锁获取顺序是否一致，是否有嵌套锁

**示例审查输出：**

```markdown
### [Logic] L2-015: 潜在空指针异常
- **位置**: `src/utils/parser.js:112`
- **问题**: `result.data.items.forEach(...)` 未检查 `data` 和 `items` 是否存在
- **风险**: 当API返回异常结构时将抛出 TypeError
- **建议**: 
  ```javascript
  const items = result?.data?.items ?? [];
  items.forEach(item => process(item));
  ```
```

#### L3 架构层审查操作

**SOLID原则违反检测：**

| 原则 | 违反模式 | 识别方法 |
|------|----------|----------|
| SRP | 类承担多种职责 | 检查类方法是否属于同一抽象域 |
| OCP | 修改已有代码扩展功能 | 检查是否有大量 if-else/switch 分支 |
| LSP | 子类破坏父类契约 | 检查重写方法是否弱化前置条件 |
| ISP | 接口过胖 | 检查接口方法数量和使用频率 |
| DIP | 高层依赖低层具体实现 | 检查import是否直接引用具体类 |

**设计模式误用识别：**
- Singleton滥用：全局状态过多时应考虑依赖注入
- 工厂方法过度：简单对象的创建不需要工厂封装
- 观察者链过长：事件传递层级超过3级应简化
- 策略模式空洞：策略之间差异极小应合并

**耦合度评估指标：**
- 直接耦合：A直接引用B的类/函数/常量
- 间接耦合：A通过参数/返回值间接依赖B的类型
- 内容耦合：A访问B的内部实现细节
- **阈值警告**：单个模块直接耦合超过7个其他模块时触发架构建议

**架构级改进建议生成流程：**

```
识别重复代码模式
    ↓
计算重复度（相似行数/总行数）
    ↓
>30%? → 提取公共模块/工具函数/基类建议
    ↓
<30% → 记录为潜在重构点，暂不建议立即行动
```

```
识别过长函数（>50行）
    ↓
分析函数职责划分点
    ↓
生成拆分方案：按步骤/按职责/按数据流
    ↓
输出拆分后的函数签名和调用关系图
```

```
识别过深嵌套（>4层）
    ↓
标记嵌套起点和终点
    ↓
应用扁平化策略：
  - 提取守卫子句（Early Return）
  - 提取独立逻辑为函数
  - 使用多态替代条件判断
  - 使用策略模式处理分支
```

```
识别God Object特征
    ↓
统计类的属性和方法数量
    ↓
属性>15 或 方法>20 或 职责域>3?
    ↓
输出职责分离建议：
  - 列出每个方法所属的职责域
  - 建议拆分为N个独立类
  - 给出拆分后的类协作方式
```

#### L4 安全层审查操作

**OWASP Top 10 逐项检查清单：**

| # | 漏洞类别 | 检查要点 | 典型代码模式 |
|---|----------|----------|--------------|
| A01 | 权限控制失效 | 权限校验是否在每个端点 | 缺少 `@RequiresRole` 注解 |
| A02 | 加密机制失败 | 敏感数据是否加密存储 | 密码明文存储 |
| A03 | 注入攻击 | SQL/NoSQL/命令拼接 | 字符串拼接SQL |
| A04 | 不安全设计 | 认证流程是否健壮 | 弱密码策略 |
| A05 | 安全配置错误 | 默认凭证/调试模式 | 硬编码密码 |
| A06 | 过时组件 | 依赖版本CVE检查 | 使用已知漏洞版本 |
| A07 | 身份认证失效 | Session/Token管理 | Token无过期时间 |
| A08 | 数据完整性失败 | 反序列化/签名验证 | 无输入校验 |
| A09 | 日志监控不足 | 敏感信息日志泄露 | 日志打印密码 |
| A10 | SSRF服务伪造 | URL验证不足 | 用户输入直接请求 |

**注入攻击专项检测：**
- SQL注入：搜索字符串拼接构建查询的模式
- XSS：搜索未经转义的用户输入直接插入DOM/HTML
- 命令注入：搜索 `exec`/`spawn`/`subprocess` 调用中的用户输入
- LDAP注入：搜索LDAP查询字符串拼接
- XPath注入：搜索XPath表达式动态构建

**示例安全审查输出：**

```markdown
### [Security] L4-007: SQL注入风险 (OWASP A03)
- **位置**: `src/repository/order.go:78`
- **问题**: 使用 fmt.Sprintf 拼接用户输入到SQL语句
- **CVSS预估**: 9.8 (Critical)
- **建议**: 使用参数化查询
  ```go
  // 危险写法
  query := fmt.Sprintf("SELECT * FROM orders WHERE id = %s", userInput)
  
  // 安全写法
  query := "SELECT * FROM orders WHERE id = $1"
  db.QueryRow(query, userInput)
  ```
- **参考**: OWASP Cheat Sheet - SQL Injection Prevention
```

### 阶段四：Verify（验证）

**自我验证检查清单：**
- [ ] 每条审查意见都有明确的位置定位（文件:行号）
- [ ] 每条Critical/High级别意见都附带了修复代码示例
- [ ] 审查意见没有遗漏任何变更文件
- [ ] 对正面实践也给予了认可（正向反馈）
- [ ] 审查语言客观专业，避免主观贬低
- [ ] 建议的修复方案不会引入新的问题
- [ ] 引用的外部规范（OWASP/SOLID）链接准确

**审查报告质量自检：**
- Critical问题数是否合理（过多则可能是误判）
- 是否区分了"必须修复"和"建议优化"
- 总体评价是否平衡（既指出问题也肯定亮点）

### 阶段五：Record（记录）

**审查记录输出格式：**
- 执行摘要：总体评分（A/B/C/D）、关键发现数量、风险评估
- 问题清单：按严重程度排序的所有发现
- 统计数据：各层次发现问题分布、热点文件排行
- 改进建议汇总：架构级建议单独列出
- 正向亮点：值得推广的优秀实践

## 典型自主场景

### 场景1：PR代码自主审查
**触发条件**：检测到新的Pull Request创建或更新
**自主执行步骤**：
1. 自动拉取PR diff，解析变更文件列表
2. 对每个变更文件执行L1-L4分层审查
3. 生成结构化审查评论，按严重程度排序
4. 在PR页面发布审查意见，支持内联代码评论
5. 如发现CRITICAL级别问题，自动添加 "Request Changes" 标签
6. 生成审查摘要报告附加到PR描述中

**预期输出**：
- PR上的结构化审查评论集合
- 包含严重程度标签的问题清单
- 可操作的修复建议及代码示例
- 审查通过/需修改的总体结论

### 场景2：存量代码健康度巡检
**触发条件**：定时任务触发（每周/每月）或手动发起
**自主执行步骤**：
1. 选择巡检范围（全仓库/指定模块/指定作者）
2. 按复杂度和最近修改时间排序选取目标文件
3. 执行L3架构层为主、L2语义层为辅的深度审查
4. 识别技术债务聚集区域和技术债热点文件
5. 生成技术债务地图和质量趋势报告
6. 将高优先级债务项录入技术债务追踪系统

**预期输出**：
- 技术债务热力图（按模块/文件维度）
- 高风险代码段清单及修复建议
- 重构优先级排序列表
- 与上次巡检的对比趋势分析

### 场景3：安全漏洞专项扫描
**触发条件**：依赖更新后、安全事件通报后、或定期扫描
**自主执行步骤**：
1. 全量扫描代码库中的OWASP Top 10漏洞模式
2. 对每个匹配模式进行人工级别的上下文分析（非误报判断）
3. 对确认的漏洞进行CVSS评分估算
4. 按风险等级生成修复工单
5. 关联受影响的测试用例，评估回归风险
6. 输出安全态势报告和修复路线图

**预期输出**：
- 已确认的安全漏洞清单（含CVSS评分）
- 每个漏洞的详细利用路径分析
- 分优先级的修复计划和代码补丁建议
- 安全合规差距分析报告

### 场景4：代码风格统一性纠偏
**触发条件**：新成员加入、项目迁移、编码规范更新
**自主执行步骤**：
1. 全量扫描项目代码的风格违规情况
2. 分类统计各类违规的出现频次和分布
3. 识别最普遍的风格问题和最顽固的违规区域
4. 生成批量修复建议和自动化规则配置
5. 对于高频违规，提供IDE配置和lint rule推荐
6. 输出风格合规度评分和改进计划

**预期输出**：
- 风格违规分布统计报告
- 按模块/作者的合规度排名
- 推荐的lint配置增强方案
- 批量修复脚本（可选自动执行）

## 决策框架

### 审查严格度自适应决策树

```
输入：变更信息
  │
  ├─ 变更文件是否为核心模块？
  │   ├─ 是 → 严格模式（全量L1-L4，零容忍Critical）
  │   └─ 否 → 是否涉及用户数据？
  │       ├─ 是 → 标准模式（L1-L4全量，Critical必须修）
  │       └─ 否 → 是否为纯UI/样式变更？
  │           ├─ 是 → 宽松模式（L1为主，L2抽样）
  │           └─ 否 → 常规模式（L1-L3全量，L4抽样）
  │
  ├─ 变更人是否为新贡献者？
  │   ├─ 是 → 增加解释性注释要求
  │   └─ 否 → 保持常规标准
  │
  └─ 是否处于发布冻结期？
      ├─ 是 → 仅允许Bug修复类变更，其余驳回
      └─ 否 → 正常审查流程
```

### 问题升级决策标准

| 条件 | 动作 |
|------|------|
| 单个PR出现 >5 个 Critical 问题 | 阻止合并，要求作者重新提交 |
| 同一作者连续3次PR出现同类问题 | 触发 mentoring 建议，通知技术负责人 |
| 发现已知CVE相关代码模式 | 立即标记安全事件，通知安全团队 |
| 架构变更影响 >5 个模块 | 要求补充架构设计文档（ADR） |
| 测试覆盖率下降 >5% | 要求补充测试后再审查 |

## 安全与治理

### 风险评估标准
- **高风险操作**：修改认证/授权逻辑、数据库Schema变更、支付相关代码
- **中风险操作**：API接口变更、核心业务逻辑修改、缓存策略变更
- **低风险操作**：样式调整、文案修改、日志格式变更、测试代码更新

### 审批门禁条件
- Critical问题数 > 0 时禁止合并
- High问题数 > 3 时建议修改后重新审查
- 安全相关问题必须在合并前修复或提供风险接受说明
- 缺少测试的新功能代码需要额外审查确认测试计划

### 回滚策略
- 审查意见以评论形式附加到PR，不影响原代码
- 作者可根据意见选择性采纳，但Critical/Hight级别需回应处理决定
- 审查历史永久保留，可用于后续审计和质量追溯
- 如审查本身有误判，可在评论中追加更正说明

## 与其他司/局的协作关系

### 与测试验证局的协作
- 代码审查局发现的Logic Defect应同步给测试验证局，作为测试用例补充的输入
- 审查中标识的高风险代码段应标记为测试验证局的P0测试重点区域
- 测试验证局发现的Bug根因分析结果应反馈给审查局，用于优化审查规则

### 与质量监控局的协作
- 代码审查局每次审查的质量评分数据应上报质量监控局，纳入六维质量指标
- 质量监控局识别的质量下降趋势应触发审查局对该区域的定向深度审查
- 两局共同维护技术债务登记簿，审查局发现债务，监控局跟踪清偿进度

### 与合规审计局的协作
- 代码审查局L4安全层的发现应实时同步给合规审计局
- 合规审计局发布的最新安全基线应成为审查局L4层的审查标准更新依据
- 合规审计局进行的依赖许可证审计结果应影响审查局对第三方库使用的审查态度

---

## 🤝 v5.1 增强：Agency Agent 协作指南

### 可调用的 Agency Agents

本局可通过 Agency-Agent Bridge 调用以下专业智能体：

| Agent 名称 | 所属部门 | 协作模式 | 适用场景 |
|-----------|---------|---------|---------|
| Code Reviewer | Development Division | 主动调用 | PR代码深度审查、建设性反馈意见生成、最佳实践建议 |
| Senior Developer | Development Division | 咨询辅助 | 架构级评审、复杂技术决策咨询、设计模式验证 |
| Security Engineer | Security Division | 联动触发 | 安全漏洞专项审查、OWASP Top 10逐项检查、CVSS评分估算 |

### Agent 协作工作流

**Step 1 - 审查任务接收与预处理**
- 接收PR变更信息，执行初步的L1语法层快速扫描
- 自动识别变更类型和风险等级，判断是否需要引入外部Agent协作
- 对于涉及认证/授权/加密等安全敏感代码，自动标记需要Security Engineer联动

**Step 2 - Code Reviewer 主导的分层审查**
- Code Reviewer Agent 执行L1-L3层的完整审查（语法/语义/架构）
- 生成结构化审查意见，按严重程度分级（Critical/Warning/Info/Suggestion）
- 每条意见附带具体的修复建议和代码示例，确保可操作性

**Step 3 - Senior Developer 架构级增强（条件触发）**
- 当检测到以下情况时，自动咨询Senior Developer：
  - 变更影响超过5个模块的架构级改动
  - 引入新的设计模式或技术栈选型
  - 圈复杂度超过阈值的函数重构方案
- Senior Developer提供架构层面的专业意见，补充架构决策记录(ADR)建议

**Step 4 - Security Engineer 安全专项联动（条件触发）**
- 当L4安全层发现潜在问题时，自动触发Security Engineer进行深度分析
- Security Engineer提供：
  - 漏洞利用路径的详细分析
  - CVSS评分的专业估算
  - 符合OWASP/ CWE标准的修复方案
  - 安全编码最佳实践指导
- 安全审查结果自动注入到主审查报告中，作为独立的安全章节

**Step 5 - 综合报告生成与发布**
- 整合所有Agent的审查结果，生成统一的综合审查报告
- 在PR页面发布审查评论，支持内联代码注释
- 根据Critical问题数量，自动设置"Request Changes"或"Approved"标签
- 将审查摘要附加到PR描述中，便于后续追溯

**Step 6 - 反馈闭环与持续学习**
- 收集开发者对审查意见的采纳率数据
- 分析误判率和漏判率，优化各Agent的审查策略
- 将典型安全案例同步给Security Engineer的知识库
- 将优秀实践案例同步给Code Reviewer的模式库

### 典型协作场景

**场景1：安全敏感PR的多Agent联合审查**
- **触发条件**：PR涉及认证逻辑修改、数据库Schema变更、支付相关代码
- **协作流程**：Code Reviewer完成L1-L3基础审查 → 自动触发Security Engineer进行L4深度安全扫描 → Senior Developer对架构变更提供专业评估 → 生成包含安全专项章节的综合审查报告
- **输出特点**：安全审查意见带有CVSS评分和CVE参考编号，修复建议符合安全编码标准

**场景2：大规模重构的架构级审查**
- **触发条件**：PR变更超过500行或影响超过5个核心模块
- **协作流程**：Code Reviewer识别所有变更点和风险区域 → Senior Developer评估架构合理性并提供ADR建议 → Security Engineer审查重构是否引入新的攻击面 → 输出包含架构改进建议和安全风险评估的综合报告
- **输出特点**：包含架构级改进建议、SOLID原则违反检测、耦合度评估图表

**场景3：新成员代码的辅导式审查**
- **触发条件**：贡献者是首次提交或近期有多次同类问题的作者
- **协作流程**：Code Reviewer以教育性口吻提供详细解释 → Senior Developer补充行业最佳实践对比 → 对高频错误模式生成定制化的编码规范提醒卡片
- **输出特点**：审查语言更具建设性，附带学习资源和最佳实践链接，帮助新人快速融入团队

---

## 🏗️ v5.1 增强：Harness 工程实践

### 相关 Harness 模块

| 模块名称 | 集成阶段 | 与本局的关联点 |
|----------|----------|---------------|
| **Security STO (Pre-commit)** | Pre-commit Hook | SAST扫描结果自动注入代码审查流程，作为L4安全层的输入源 |
| **Security STO (Build)** | CI Build 阶段 | DAST/依赖扫描结果作为安全审查的补充证据，增强审查准确性 |
| **CI Quality Gates** | CI Pipeline | 质量门禁配置与本局的审查标准对齐，实现"审查通过=门禁通过"的一致性保证 |

### 实践指南

**实践1：STO扫描结果自动注入代码审查流程**
```
集成架构：
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│ STO SAST    │ ──→ │ 代码审查局 L4层   │ ──→ │ 综合审查报告     │
│ 扫描引擎     │     │ 安全审查引擎      │     │ (含安全章节)     │
└─────────────┘     └──────────────────┘     └─────────────────┘
       ↑                    ↑                        ↑
       │                    │                        │
  PR触发扫描          自动解析扫描结果            安全问题带CVSS评分
  (Pre-commit)        过滤误报+严重程度评定         和修复建议
```
- 当PR创建时，Harness STO自动启动SAST扫描
- 本局自动拉取STO扫描结果，将其作为L4安全层的输入
- 对STO发现的每个安全问题进行上下文分析，排除误报
- 将确认的安全问题注入审查报告，附带STO原始扫描ID以便追溯
- 修复建议结合STO推荐的修复模式和本局的最佳实践经验

**实践2：CI质量门禁与审查标准对齐**
- 定义统一的质量门槛配置，确保CI门禁和人工审查使用相同的标准
- Critical级别问题：CI门禁直接阻断 + 审查局标记为必须修复
- High级别问题：CI门禁警告 + 审查局强烈建议修复并跟踪
- Medium/Low级别问题：CI门禁记录 + 审查局提供建议性意见
- 定期（每月）对齐CI门禁规则和本局的审查规则，保持一致性

**实践3：构建时间线的安全扫描全链路追踪**
- Pre-commit阶段：轻量级SAST快速扫描（聚焦高危模式）
- Build阶段：完整SAST + 依赖漏洞扫描 + DAST预扫描
- 代码审查阶段：基于STO结果的深度上下文分析 + 人工级别的误报过滤
- 发布前阶段：完整DAST扫描 + 渗透测试协调
- 每个阶段的扫描结果都关联到同一个PR，形成完整的扫描时间线视图

### 配置参考

```yaml
# harness/security-sto-integration.yaml
security_sto_integration:
  # Pre-commit阶段集成
  pre_commit:
    enabled: true
    scan_types:
      - sast_quick  # 快速SAST（仅高危模式）
    result_handling:
      auto_inject_to_review: true  # 自动注入到代码审查
      severity_threshold: medium   # 中度及以上才注入
      false_positive_filter: true  # 启用智能误报过滤
  
  # Build阶段集成
  build_stage:
    enabled: true
    scan_types:
      - sast_full    # 完整SAST
      - dependency   # 依赖漏洞扫描
      - dast_pre     # 预DAST扫描
    result_handling:
      inject_to_review_report: true  # 注入到审查报告的安全章节
      include_cvss_scores: true      # 包含CVSS评分
      attach_remediation_guides: true # 附带修复指南
  
  # CI质量门禁对齐
  quality_gates:
    align_with_review_bureau: true
    gate_rules:
      critical_issues: block_merge   # Critical: 阻断合并
      high_issues: warn_and_track    # High: 警告+跟踪
      medium_issues: log_only        # Medium: 仅记录
      low_issues: log_only           # Low: 仅记录
    
    # 审查局特殊标签映射
    review_labels:
      security_finding: "🔒 Security Review Required"
      architecture_change: "🏗️ Architecture Review Needed"
      needs_expert_input: "👨‍💻 Senior Dev Consultation"
```

---

## 🆕 v6.0 增强能力集成

### 四维度输出防线检查点

本局的输出需要通过以下防线层级检查：

| 防线层级 | 本局适用性 | 检查项 | 配置位置 |
|---------|-----------|--------|----------|
| **第一维：提示词工程层** | ✅ 适用 | 角色人格一致性：本局输出风格是否符合代码审查的专业规范（客观严谨、建设性、可操作性、分层反馈） | `configs/output_defense_config.yaml → prompt_engineering.role_consistency` |
| **第二维：能力约束层** | ✅ 适用 | 工具权限：本局操作是否在允许的工具白名单内（文件读写、Git diff分析、代码扫描） | `configs/output_defense_config.yaml → capability_guard.permissions` |
| **第三维：规则校验层** | ✅ 适用 | 输出格式：本局产出的审查报告是否符合Schema定义（L1-L4层次完整性、严重程度分级规范、修复建议可操作性） | `configs/output_defense_config.yaml → rule_validation.schema_validation` |
| **第四维：兜底恢复机制** | ⚠️ 备用 | 当本局输出不达标时，降级策略：精简版审查意见→关键问题清单→错误提示+人工介入 | `configs/output_defense_config.yaml → fallback_recovery` |

### MARC资源协调注意事项

当本局与其他局/司并发工作时，需注意：

- **资源申请**：如需访问规范局的编码标准、合规审计局的安全基线，应通过MARC锁管理器申请
- **Decision Log记录**：本局做出的重要审查结论（Critical/High级别问题判定、架构级建议）必须记录到Decision Log中
- **冲突预防**：避免与测试验证局同时修改同一代码区域的测试文件；避免在开发者活跃修改时进行大规模重构建议

### 操作优先级指引（v6.0核心）

本局推荐的操作方式优先级：

1. 🥇 **Agent自主手动操作**（首选）
   - 直接使用文件读写工具创建/修改审查报告、PR评论、技术债务记录
   - 适用场景：单PR审查、代码质量巡检、安全漏洞专项扫描、架构级改进建议
   
2. 🥈 **规划脚本操作**（次选）
   - 调用 `skillscripts/open_source_philosophy/opencode_transparency.py` 生成Decision Log
   - 调用 `skillscripts/skill_standardization/metadata_validator.py` 验证审查报告格式合规性
   
3. 🥉 **命令操作**（最后选择，需预演）
   - 仅在需要运行静态分析工具（ESLint/SonarQube）、复杂度扫描或批量生成报告时使用
   - 执行前必须运行后果预演确认安全性

### Decision Log 记录要求

作为**代码审查局**，以下类型的决策必须自动记录到Decision Log：

- Critical/High级别问题的判定依据及影响范围评估
- 安全漏洞发现记录（OWASP分类、CVSS评分估算、修复优先级建议）
- 架构层违规识别（SOLID原则违反、设计模式误用、耦合度超阈值）
- 审查严格度自适应决策（基于变更规模/模块/作者选择的审查模式及理由）
- 技术债务登记决定（新发现债务的量化评分、修复建议、跟踪编号）

- Decision Log存储路径：`docs/logs/decision_logs/`
- 日志命名规则：`{YYYY-MM-DD}_CR_decisions.md`

### PowerShell 7 适配说明

本局相关脚本在PS7环境下的注意事项：
- 路径分隔符：使用 `/` 或 `\` 均可，系统自动转换
- 编码保证：所有输出文件（审查报告、PR评论、债务记录）使用 UTF-8 无 BOM 编码
- 如需执行终端命令（如运行Git diff、静态分析工具），使用 `platform/powershell_adapter.py` 进行转换

---

## 🔍 硬编码检测集成（v6.1 新增）

### 检测工具：HardcodedDetector

**模块路径**: `skillscripts/secrets_manager/hardcoded_detector.py`

### 代码审查中的硬编码检查标准

#### 审查必检项（每次代码审查必须执行）

1. **运行 HardcodedDetector 扫描**
   ```python
   from skillscripts.secrets_manager.hardcoded_detector import HardcodedDetector
   
   detector = HardcodedDetector()
   report = detector.scan_directory(Path("src/"))
   
   if report.total_findings > 0:
       critical = report.by_severity.get("critical", 0)
       high = report.by_severity.get("high", 0)
       print(f"⚠️ 发现 {report.total_findings} 个问题 (Critical:{critical} High:{high})")
       for f in report.findings:
           if f.severity.value in ("critical", "high"):
               print(f"  🔴 {f.file_path}:{f.line} - {f.pattern_name}")
   ```

2. **严重级别判定标准**

| 严重级别 | 处理要求 | 审查结果 |
|---------|---------|---------|
| **Critical** | 必须阻塞合并，立即修复 | ❌ 不通过 |
| **High** | 强烈建议修复后合并 | ⚠️ 有条件通过 |
| **Medium** | 建议在下个迭代修复 | ✅ 通过（需跟踪） |
| **Low** | 记录即可 | ✅ 通过 |
| **Info** | 信息性提示 | ✅ 通过 |

3. **常见硬编码模式及修复方式**

| 错误写法 | 正确写法 | 说明 |
|---------|---------|------|
| `password = "admin123"` | `os.environ.get("APP_PASSWORD")` | 使用环境变量 |
| `api_key = "sk-abc123..."` | `SecretsManager.get_required("API_KEY")` | 通过密钥管理器 |
| `DB_HOST = "192.168.1.100"` | `os.environ.get("DB_HOST", "localhost")` | IP 也应参数化 |
| `token = "eyJhbGci..."` | 从安全存储动态获取 | Token 永不硬编码 |

4. **PR/MR 审查 Checklist 新增项**

在代码审查 checklist 中增加：
- [ ] 已运行 HardcodedDetector 扫描变更文件
- [ ] 无 Critical/High 级别的硬编码问题
- [ ] 新增的环境变量已更新到 `.env.example`
- [ ] 敏感配置已通过 ConfigSecurityAuditor 审核

### CI/CD 集成建议

在 CI 流水线中添加自动化安全扫描步骤：
```yaml
# GitHub Actions 示例
- name: Security Scan (HardcodedDetector)
  run: |
    python -c "
    from skillscripts.secrets_manager.hardcoded_detector import HardcodedDetector
    detector = HardcodedDetector()
    report = detector.scan_directory('.')
    if report.by_severity.get('critical', 0) > 0:
        raise SystemExit(f'Critical security issues found: {report.total_findings}')
    print(f'✅ Security scan passed ({report.total_findings} info-level findings)')
    "
```
