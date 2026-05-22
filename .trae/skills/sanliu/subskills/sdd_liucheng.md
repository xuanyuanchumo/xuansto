---
name: sdd_liucheng
description: 规范驱动开发（SDD）流程指导，包含规范解析、代码生成、验证循环详细步骤、最佳实践和常见问题。
---
# SDD流程指导

## 规范驱动开发循环

### 循环概述
规范驱动开发（Specification-Driven Development，SDD）是一种以规范为核心的软件开发方法，其核心是"规范定义 → 规范解析 → 代码生成 → 验证"循环。这个循环强调在编写代码之前先定义清晰的规范，通过规范来驱动代码的设计和实现。SDD的核心思想是：先明确规范（定义契约），再解析规范（结构化信息），然后生成代码（实现功能），最后验证一致性（确保合规）。

循环的四个阶段紧密相连，形成一个持续迭代的开发流程。每个循环应该保持聚焦，确保规范与实现的一致性，提高代码质量和可维护性。

### 规范定义阶段

#### 目标
定义清晰、完整、可执行的规范，明确系统或模块的预期行为和约束条件。

#### 详细步骤

1. **需求分析与规范范围确定**
   - 分析业务需求，明确规范覆盖的功能范围
   - 识别关键业务规则和约束条件
   - 确定规范的边界和与其他规范的接口关系
   - 评估规范的复杂度，必要时进行拆分

2. **规范结构设计**
   - 选择合适的规范描述语言或格式（如 OpenAPI、JSON Schema、DSL 等）
   - 设计规范的层次结构和组织方式
   - 定义规范的版本管理策略
   - 确定规范的命名约定和标识符规则

3. **编写规范内容**
   - 使用精确、无歧义的语言描述预期行为
   - 定义输入参数、输出结果的类型和约束
   - 描述正常流程和异常处理逻辑
   - 添加必要的示例和说明文档
   - 定义性能、安全等非功能性约束

4. **规范评审与确认**
   - 组织团队成员进行规范评审
   - 验证规范的完整性和一致性
   - 确认规范与业务需求的对应关系
   - 记录评审意见并修订规范

#### 输出格式

```yaml
规范定义输出:
  规范标识: string          # 唯一标识符
  规范名称: string          # 规范名称
  版本号: string            # 语义化版本号
  适用范围: string[]        # 规范适用的模块或功能
  定义内容:
    接口定义: object        # API 或函数接口定义
    数据模型: object        # 数据结构定义
    业务规则: object[]      # 业务规则列表
    约束条件: object[]      # 约束条件列表
  示例: object[]           # 使用示例
  元数据:
    创建者: string
    创建时间: datetime
    最后修改: datetime
    状态: draft | review | approved | deprecated
```

#### 注意事项
- 规范应该独立于具体实现，关注"做什么"而非"怎么做"
- 使用标准化术语，避免模糊表述
- 规范粒度要适中，过大会难以管理，过小会增加维护成本
- 保持规范的向后兼容性或明确定义版本迁移策略

### 规范解析阶段

#### 目标
将定义的规范解析为结构化的、可被代码生成器理解的中间表示，为代码生成做准备。

#### 详细步骤

1. **规范加载与验证**
   - 加载规范定义文件
   - 验证规范格式的正确性
   - 检查规范的完整性和一致性
   - 解析规范的依赖关系

2. **语法分析与语义提取**
   - 解析规范的语法结构
   - 提取接口定义、数据模型、业务规则等语义信息
   - 识别规范中的引用和继承关系
   - 构建规范的抽象语法树（AST）或中间表示（IR）

3. **规则转换与映射**
   - 将业务规则转换为可执行的验证逻辑
   - 建立规范元素到代码结构的映射关系
   - 识别需要特殊处理的复杂规则
   - 生成验证规则的数据结构

4. **生成中间表示**
   - 构建规范解析的中间表示（IR）
   - 包含类型信息、约束条件、默认值等元数据
   - 生成规范解析报告
   - 缓存解析结果以提高后续处理效率

#### 输出格式

```yaml
规范解析输出:
  解析状态: success | partial | failed
  规范标识: string
  中间表示:
    类型定义:
      - 名称: string
        基类型: string
        属性:
          - 名称: string
            类型: string
            约束: object
            默认值: any
    接口定义:
      - 名称: string
        方法: string
        参数:
          - 名称: string
            类型: string
            必需: boolean
        返回值:
          类型: string
          描述: string
    验证规则:
      - 规则标识: string
        适用元素: string
        规则类型: range | pattern | custom | composite
        规则定义: object
        错误信息: string
  依赖关系:
    - 规范标识: string
      依赖类型: extends | references | includes
  解析报告:
    警告: string[]
    错误: string[]
    建议: string[]
```

#### 注意事项
- 解析过程应该是确定性的，相同规范产生相同结果
- 保留规范中的注释和文档信息，便于生成代码文档
- 处理好规范之间的循环依赖问题
- 提供详细的错误信息，帮助定位规范问题

### 代码生成阶段

#### 目标
根据解析后的规范中间表示，生成符合规范的代码实现，包括数据模型、接口实现、验证逻辑等。

#### 详细步骤

1. **模板选择与配置**
   - 根据目标语言和框架选择合适的代码模板
   - 配置代码生成参数（命名风格、目录结构等）
   - 加载自定义模板或覆盖默认模板
   - 设置代码风格和格式化规则

2. **类型定义生成**
   - 根据规范中的数据模型生成类型定义
   - 生成属性、方法、构造函数等代码
   - 添加类型注解和文档注释
   - 生成序列化/反序列化相关代码

3. **接口实现生成**
   - 根据规范中的接口定义生成接口声明
   - 生成方法签名和参数验证代码
   - 生成骨架实现或默认实现
   - 添加错误处理和异常抛出代码

4. **验证逻辑生成**
   - 根据规范中的约束条件生成验证代码
   - 生成输入参数验证逻辑
   - 生成业务规则检查逻辑
   - 生成验证错误信息处理代码

5. **辅助代码生成**
   - 生成工厂方法或构建器模式代码
   - 生成测试用例骨架
   - 生成API文档或注释
   - 生成配置文件或依赖注入代码

#### 输出格式

```yaml
代码生成输出:
  生成状态: success | partial | failed
  规范标识: string
  生成文件:
    - 文件路径: string
      文件类型: model | interface | validator | test | config | doc
      生成内容: string
      覆盖策略: create | overwrite | merge | skip
  生成统计:
    总文件数: number
    新增文件: number
    修改文件: number
    跳过文件: number
  生成报告:
    警告: string[]
    错误: string[]
    待办事项: string[]    # 需要人工补充的实现
```

#### 代码模板示例

```yaml
模板定义:
  模板标识: string
  目标语言: string
  目标框架: string
  模板内容:
    文件命名规则: string    # 如 "{name}.{ext}"
    目录结构规则: string    # 如 "src/models/{name}"
    代码模板: string        # 使用模板语法的代码模板
  变量定义:
    - 变量名: string
      来源: spec | config | computed
      描述: string
  代码片段:
    - 片段标识: string
      触发条件: string
      代码内容: string
```

#### 注意事项
- 生成的代码应该符合目标语言的最佳实践和编码规范
- 保留人工修改的空间，支持部分代码的手动覆盖
- 生成的代码应该具有良好的可读性，添加必要的注释
- 处理好生成代码与手写代码的边界和集成方式

### 验证阶段

#### 目标
验证生成的代码是否符合规范定义，确保实现与规范的一致性，发现并修复偏差。

#### 详细步骤

1. **静态验证**
   - 检查生成代码的语法正确性
   - 验证类型定义与规范的一致性
   - 检查接口签名与规范定义的匹配度
   - 运行静态代码分析工具

2. **动态验证**
   - 运行自动生成的测试用例
   - 执行验证逻辑测试
   - 进行边界条件和异常情况测试
   - 验证性能约束是否满足

3. **一致性检查**
   - 对比代码实现与规范定义
   - 检查是否有遗漏的规范元素
   - 验证业务规则的完整实现
   - 检查约束条件的正确应用

4. **偏差分析与修复**
   - 记录发现的偏差和不一致
   - 分析偏差原因（规范问题或生成问题）
   - 修复规范定义或重新生成代码
   - 更新验证报告

#### 输出格式

```yaml
验证输出:
  验证状态: passed | failed | warning
  规范标识: string
  验证结果:
    静态验证:
      状态: passed | failed
      检查项:
        - 检查名称: string
          状态: passed | failed | skipped
          详情: string
    动态验证:
      状态: passed | failed
      测试用例:
        - 用例名称: string
          状态: passed | failed | skipped
          执行时间: number
          错误信息: string
    一致性检查:
      状态: passed | failed
      偏差列表:
        - 偏差类型: missing | mismatch | extra
          规范元素: string
          代码位置: string
          描述: string
  验证报告:
    通过率: number
    问题列表:
      - 问题级别: error | warning | info
        问题描述: string
        建议修复: string
```

#### 注意事项
- 验证应该是自动化的，可集成到CI/CD流程中
- 验证结果应该清晰明确，便于定位问题
- 区分规范问题和实现问题，分别处理
- 保持验证的可追溯性，记录验证历史

## SDD最佳实践

### 规范编写原则

1. **SMART原则**
   - Specific（具体）：规范应该明确具体，避免模糊表述
   - Measurable（可度量）：规范中的约束条件应该可以量化验证
   - Achievable（可实现）：规范定义的功能应该是可实现的
   - Relevant（相关）：规范应该与业务需求紧密相关
   - Time-bound（有时限）：规范应该有明确的版本和生命周期

2. **单一职责**
   - 每个规范应该只描述一个功能或模块
   - 规范之间应该有清晰的边界
   - 避免规范之间的交叉和重叠
   - 通过引用和继承实现规范复用

3. **规范命名规范**
   - 使用一致的命名约定
   - 名称应该能够反映规范的内容和用途
   - 避免使用缩写或技术术语，优先使用业务术语
   - 保持命名在不同语言和格式中的一致性

4. **文档化原则**
   - 每个规范元素都应该有清晰的描述
   - 提供足够的使用示例
   - 记录规范的设计决策和变更历史
   - 维护规范的变更日志

### 循环控制

1. **保持循环聚焦**
   - 每个SDD循环应该围绕一个明确的规范
   - 避免在一个循环中处理多个不相关的规范
   - 规范变更时及时触发新的循环

2. **增量迭代**
   - 从核心规范开始，逐步扩展
   - 每次迭代添加或修改少量规范元素
   - 保持每个迭代的可验证性

3. **持续验证**
   - 规范变更后立即进行验证
   - 代码生成后立即进行一致性检查
   - 集成到开发流程中，形成闭环

### 代码生成策略

1. **模板管理**
   - 建立可复用的模板库
   - 支持模板的版本管理和更新
   - 允许项目级别的模板覆盖
   - 保持模板的简洁和可维护性

2. **生成控制**
   - 明确哪些代码由生成器管理
   - 支持部分代码的手动扩展
   - 使用注解或标记区分生成代码和手写代码
   - 提供代码合并策略选项

3. **质量保证**
   - 生成的代码应该通过代码审查
   - 运行静态分析工具检查生成代码
   - 确保生成代码符合项目编码规范
   - 定期审查和优化生成模板

### 团队协作

1. **规范所有权**
   - 明确规范的负责人和审核人
   - 建立规范变更的审批流程
   - 记录规范的变更历史和原因

2. **版本管理**
   - 使用语义化版本号管理规范
   - 维护规范的兼容性声明
   - 提供规范的迁移指南

3. **知识共享**
   - 建立规范文档中心
   - 定期进行规范评审和分享
   - 培训团队成员规范编写技能

## 常见问题和解决方案

### 问题1：规范过于抽象难以实现

**问题描述**：规范定义过于抽象，缺乏具体的实现指导，导致代码生成困难。

**解决方案**：
- 在规范中添加具体的示例和边界条件
- 将抽象规范拆分为更具体的子规范
- 补充技术约束和实现建议
- 建立规范模板，提供标准化的结构

### 问题2：规范频繁变更导致代码不稳定

**问题描述**：业务需求变化导致规范频繁修改，生成的代码需要不断调整。

**解决方案**：
- 使用版本管理，保持旧版本的兼容性
- 设计灵活的规范结构，预留扩展空间
- 采用增量生成策略，减少变更影响范围
- 建立规范变更的影响评估机制

### 问题3：生成的代码质量不高

**问题描述**：自动生成的代码可读性差、性能不佳或不符合项目规范。

**解决方案**：
- 优化代码生成模板，遵循最佳实践
- 添加代码格式化和静态检查步骤
- 进行代码审查，收集改进建议
- 建立代码质量度量标准，持续改进

### 问题4：规范与实现不一致

**问题描述**：手动修改代码后，规范与实际实现产生偏差。

**解决方案**：
- 明确区分生成代码和手写代码的边界
- 使用部分类或扩展模式隔离手写代码
- 建立定期的一致性检查机制
- 规范变更时同步更新相关代码

### 问题5：规范解析错误难以定位

**问题描述**：规范解析失败时，错误信息不够清晰，难以定位问题。

**解决方案**：
- 提供详细的解析错误信息和位置
- 使用规范的IDE插件进行实时验证
- 建立规范的测试用例，验证解析正确性
- 提供规范调试工具

### 问题6：模板维护成本高

**问题描述**：随着项目发展，代码生成模板变得复杂，维护困难。

**解决方案**：
- 模块化设计模板，提高复用性
- 建立模板版本管理和变更日志
- 定期重构和简化模板
- 提供模板测试工具，验证模板正确性

### 问题7：团队对SDD接受度低

**问题描述**：团队成员对规范驱动开发持怀疑态度，不愿意采用。

**解决方案**：
- 从小范围试点开始，展示实际收益
- 提供培训和指导，降低学习曲线
- 建立规范编写指南和最佳实践文档
- 收集反馈，持续改进流程和工具

### 问题8：遗留系统难以应用SDD

**问题描述**：现有系统没有规范文档，难以应用规范驱动开发。

**解决方案**：
- 从现有代码逆向生成规范
- 优先为新功能应用SDD
- 逐步补充核心模块的规范
- 建立规范与代码的映射关系

### 问题9：规范粒度难以把握

**问题描述**：规范粒度过大难以管理，过小增加维护成本。

**解决方案**：
- 根据业务领域划分规范边界
- 遵循单一职责原则
- 建立规范的层次结构
- 定期审查和调整规范粒度

### 问题10：多语言环境下的规范管理

**问题描述**：项目使用多种编程语言，规范需要支持多种代码生成。

**解决方案**：
- 使用语言无关的规范描述格式
- 为每种语言建立独立的模板库
- 统一规范定义，分离代码生成配置
- 建立跨语言的规范验证机制

## 规范文件结构定义

### 规范文件组织架构

```
project/
├── specs/                          # 规范根目录
│   ├── core/                       # 核心规范
│   │   ├── entities/               # 实体定义规范
│   │   │   ├── user.spec.yaml
│   │   │   └── order.spec.yaml
│   │   ├── interfaces/             # 接口契约规范
│   │   │   ├── api.spec.yaml
│   │   │   └── internal.spec.yaml
│   │   └── constraints/            # 约束条件规范
│   │       ├── business.spec.yaml
│   │       └── security.spec.yaml
│   ├── modules/                    # 模块级规范
│   │   ├── auth/
│   │   │   ├── auth.spec.yaml      # 模块主规范
│   │   │   └── rules/              # 业务规则
│   │   └── order/
│   ├── shared/                     # 共享规范
│   │   ├── types/                  # 公共类型定义
│   │   ├── enums/                  # 枚举定义
│   │   └── constants/              # 常量定义
│   └── meta/                       # 元数据
│       ├── registry.yaml           # 规范注册表
│       └── dependencies.yaml       # 依赖关系图
├── templates/                      # 代码生成模板
│   ├── python/
│   ├── typescript/
│   └── java/
└── generated/                      # 生成代码输出
    ├── models/
    ├── apis/
    └── tests/
```

### 规范文件命名约定

| 规范类型 | 命名模式 | 示例 |
|---------|---------|------|
| 实体规范 | `{entity}.entity.spec.yaml` | `user.entity.spec.yaml` |
| 接口规范 | `{module}.api.spec.yaml` | `auth.api.spec.yaml` |
| 业务规则 | `{rule}.rule.spec.yaml` | `discount.rule.spec.yaml` |
| 约束规范 | `{constraint}.constraint.spec.yaml` | `password.constraint.spec.yaml` |
| 验收标准 | `{feature}.acceptance.spec.yaml` | `login.acceptance.spec.yaml` |
| 模块规范 | `{module}.module.spec.yaml` | `order.module.spec.yaml` |

### 规范文件标准格式

```yaml
# 规范文件标准头部
apiVersion: sdd/v1
kind: EntitySpec | InterfaceSpec | RuleSpec | ConstraintSpec | AcceptanceSpec
metadata:
  name: string                    # 规范名称
  version: string                 # 语义化版本号
  namespace: string               # 命名空间/模块
  labels:                         # 标签
    - key: value
  annotations:                    # 注解
    author: string
    created: datetime
    modified: datetime
    status: draft | review | approved | deprecated
  dependencies:                   # 依赖的其他规范
    - name: string
      version: string
      type: extends | references | includes

spec:                             # 规范具体内容
  # 根据规范类型定义
```

## 规范文件类型定义

#### 实体规范文件结构

```yaml
apiVersion: sdd/v1
kind: EntitySpec
metadata:
  name: User
  version: 1.2.0
  namespace: auth
spec:
  description: "系统用户实体"
  type: aggregate_root | entity | value_object | enum
  tableName: users
  attributes:
    - name: id
      type: bigint
      primary: true
      autoIncrement: true
    - name: username
      type: string
      length: 50
      required: true
      unique: true
      validation:
        pattern: "^[a-zA-Z][a-zA-Z0-9_]{2,49}$"
    - name: email
      type: string
      length: 100
      required: true
      unique: true
      validation:
        format: email
    - name: status
      type: enum
      enumType: UserStatus
      defaultValue: active
  relationships:
    - name: user_roles
      target: Role
      type: one_to_many
      cascade: [delete]
  indexes:
    - name: idx_user_email
      fields: [email]
      unique: true
    - name: idx_user_status
      fields: [status]
```

#### 接口规范文件结构

```yaml
apiVersion: sdd/v1
kind: InterfaceSpec
metadata:
  name: AuthAPI
  version: 2.0.0
  namespace: auth
spec:
  baseUrl: /api/v1/auth
  endpoints:
    - name: login
      method: POST
      path: /login
      description: "用户登录"
      request:
        contentType: application/json
        body:
          type: object
          properties:
            username:
              type: string
              required: true
            password:
              type: string
              required: true
      response:
        contentType: application/json
        statusCode: 200
        body:
          type: object
          properties:
            access_token:
              type: string
            token_type:
              type: string
            expires_in:
              type: integer
      errors:
        - code: 10001
          message: "用户名或密码错误"
          statusCode: 401
        - code: 10002
          message: "账号已被锁定"
          statusCode: 403
```

#### 业务规则规范文件结构

```yaml
apiVersion: sdd/v1
kind: RuleSpec
metadata:
  name: DiscountCalculationRule
  version: 1.0.0
  namespace: order
spec:
  type: calculation | validation | transition
  priority: 100
  trigger:
    event: order_created | order_updated
    condition: "order.totalAmount > 0"
  conditions:
    - name: isVipUser
      expression: "user.level IN ['GOLD', 'PLATINUM']"
    - name: isSeasonalPromotion
      expression: "now() BETWEEN promotion.start AND promotion.end"
  actions:
    - name: calculateBaseDiscount
      type: calculation
      formula: "order.totalAmount * user.discountRate"
    - name: applySeasonalBonus
      type: calculation
      formula: "baseDiscount * 1.1"
      condition: "isSeasonalPromotion"
  output:
    type: DiscountResult
    properties:
      discountRate:
        type: number
      discountAmount:
        type: number
      finalAmount:
        type: number
```

## 规范验证流程

### 验证流程概述

```
规范验证流程
├── 1. 语法验证
│   ├── YAML/JSON 格式检查
│   ├── 必填字段完整性检查
│   └── 数据类型正确性检查
├── 2. 语义验证
│   ├── 引用完整性验证
│   ├── 业务逻辑一致性验证
│   └── 约束条件合理性验证
├── 3. 依赖验证
│   ├── 依赖存在性检查
│   ├── 版本兼容性检查
│   └── 循环依赖检测
├── 4. 一致性验证
│   ├── 跨规范一致性检查
│   ├── 命名冲突检测
│   └── 类型兼容性检查
└── 5. 可执行性验证
    ├── 规则可执行性验证
    ├── 表达式语法验证
    └── 测试用例生成验证
```

### 验证规则定义

```yaml
validationRules:
  syntax:
    - id: SYNTAX_001
      name: "YAML格式验证"
      severity: error
      check: "isValidYAML(content)"
      message: "规范文件YAML格式错误"
    - id: SYNTAX_002
      name: "必填字段验证"
      severity: error
      check: "hasRequiredFields(spec, ['metadata.name', 'metadata.version', 'spec'])"
      message: "缺少必填字段"
    - id: SYNTAX_003
      name: "版本号格式验证"
      severity: error
      check: "matchesPattern(metadata.version, '^[0-9]+\\.[0-9]+\\.[0-9]+$')"
      message: "版本号格式不正确，应为语义化版本号"

  semantic:
    - id: SEMANTIC_001
      name: "实体引用验证"
      severity: error
      check: "allReferencesExist(spec.relationships)"
      message: "引用的实体不存在"
    - id: SEMANTIC_002
      name: "类型引用验证"
      severity: error
      check: "allTypesExist(spec.attributes)"
      message: "引用的类型不存在"
    - id: SEMANTIC_003
      name: "枚举值完整性"
      severity: warning
      check: "enumHasValues(attribute)"
      message: "枚举类型缺少值定义"

  dependency:
    - id: DEP_001
      name: "依赖存在性验证"
      severity: error
      check: "allDependenciesExist(metadata.dependencies)"
      message: "依赖的规范不存在"
    - id: DEP_002
      name: "版本兼容性验证"
      severity: warning
      check: "isVersionCompatible(dependency.version, requiredVersion)"
      message: "依赖版本可能不兼容"
    - id: DEP_003
      name: "循环依赖检测"
      severity: error
      check: "noCircularDependencies(spec)"
      message: "检测到循环依赖"

  consistency:
    - id: CONSIST_001
      name: "命名唯一性验证"
      severity: error
      check: "isNameUnique(metadata.name, namespace)"
      message: "规范名称在命名空间内不唯一"
    - id: CONSIST_002
      name: "接口路径唯一性"
      severity: error
      check: "isPathUnique(endpoint.path, endpoint.method)"
      message: "接口路径重复"
    - id: CONSIST_003
      name: "类型定义一致性"
      severity: warning
      check: "typeDefinitionsMatch(spec, sharedTypes)"
      message: "类型定义与共享类型不一致"
```

### 验证执行流程

```yaml
validationPipeline:
  stages:
    - name: syntaxValidation
      parallel: true
      rules: [SYNTAX_001, SYNTAX_002, SYNTAX_003]
      onFailure: abort
      
    - name: semanticValidation
      parallel: true
      rules: [SEMANTIC_001, SEMANTIC_002, SEMANTIC_003]
      onFailure: continue
      
    - name: dependencyValidation
      parallel: false
      rules: [DEP_001, DEP_002, DEP_003]
      onFailure: abort
      
    - name: consistencyValidation
      parallel: false
      rules: [CONSIST_001, CONSIST_002, CONSIST_003]
      onFailure: continue
      
    - name: reportGeneration
      generate:
        - validationReport
        - dependencyGraph
        - issueList
```

### 验证报告格式

```yaml
validationReport:
  specId: "auth/User/1.2.0"
  validatedAt: "2024-03-15T10:30:00Z"
  overallStatus: passed | failed | warning
  
  summary:
    totalChecks: 15
    passed: 13
    warnings: 2
    errors: 0
    
  results:
    - ruleId: SYNTAX_001
      status: passed
      duration: 5ms
    - ruleId: SEMANTIC_002
      status: warning
      message: "类型 'Address' 未在共享类型中定义，使用内联定义"
      location:
        file: "user.entity.spec.yaml"
        line: 25
        field: "spec.attributes[3].type"
      suggestion: "建议将 Address 类型提取到 shared/types 目录"
      
  dependencies:
    valid:
      - name: "shared/types/Address"
        version: "1.0.0"
        status: resolved
    missing: []
    incompatible: []
```

## 规范版本管理

### 版本号规则

遵循语义化版本规范（Semantic Versioning）：

```
MAJOR.MINOR.PATCH[-PRERELEASE][+BUILD]

MAJOR: 不兼容的API变更
MINOR: 向后兼容的功能新增
PATCH: 向后兼容的问题修复
PRERELEASE: 预发布版本标识（alpha, beta, rc）
BUILD: 构建元数据
```

### 版本生命周期

```yaml
versionLifecycle:
  states:
    - name: draft
      description: "草稿状态，规范正在编写中"
      transitions: [review]
      
    - name: review
      description: "评审状态，等待团队评审"
      transitions: [approved, draft]
      
    - name: approved
      description: "已批准，可用于代码生成"
      transitions: [deprecated, superseded]
      
    - name: deprecated
      description: "已废弃，不再推荐使用"
      transitions: [archived]
      
    - name: superseded
      description: "已被新版本替代"
      transitions: [archived]
      
    - name: archived
      description: "已归档，仅作历史记录"
      transitions: []
```

### 版本变更策略

```yaml
versionChangePolicy:
  major:
    triggers:
      - "删除或重命名实体"
      - "删除或重命名接口"
      - "修改必填字段为可选"
      - "修改返回值结构"
      - "删除枚举值"
    requires:
      - "团队评审通过"
      - "迁移指南编写"
      - "影响评估报告"
      
  minor:
    triggers:
      - "新增实体或接口"
      - "新增可选字段"
      - "新增枚举值"
      - "新增业务规则"
    requires:
      - "技术负责人审批"
      - "更新文档"
      
  patch:
    triggers:
      - "修复规范错误"
      - "补充描述信息"
      - "优化约束条件"
    requires:
      - "代码审查通过"
```

### 版本兼容性矩阵

```yaml
compatibilityMatrix:
  spec: "auth/User"
  versions:
    - version: "2.0.0"
      status: approved
      compatibleWith:
        - "auth/API/2.x.x"
        - "order/Order/1.x.x"
      breaking: true
      migrationGuide: "docs/migration/user-v2.md"
      
    - version: "1.5.0"
      status: deprecated
      deprecatedAt: "2024-03-01"
      sunsetAt: "2024-06-01"
      compatibleWith:
        - "auth/API/1.x.x"
        - "order/Order/1.x.x"
      breaking: false
      
    - version: "1.0.0"
      status: archived
      archivedAt: "2024-01-01"
```

### 规范变更记录

```yaml
changeLog:
  spec: "auth/User"
  changes:
    - version: "2.0.0"
      date: "2024-03-15"
      author: "张三"
      type: major
      summary: "新增用户等级系统"
      changes:
        - action: add
          path: "spec.attributes.level"
          description: "新增用户等级字段"
        - action: add
          path: "spec.attributes.experiencePoints"
          description: "新增经验值字段"
        - action: modify
          path: "spec.attributes.status.enumType"
          oldValue: "UserStatus"
          newValue: "UserStatusV2"
          description: "状态枚举新增 'suspended' 状态"
      impact:
        - module: "auth"
          severity: high
          description: "需要更新用户服务实现"
        - module: "order"
          severity: medium
          description: "订单折扣计算需适配新等级系统"
      migration:
        steps:
          - "更新数据库表结构，添加 level 和 experience_points 字段"
          - "迁移现有用户数据，设置默认等级"
          - "更新 API 返回结构"
          - "更新前端展示逻辑"
          
    - version: "1.5.0"
      date: "2024-02-01"
      author: "李四"
      type: minor
      summary: "新增用户头像字段"
      changes:
        - action: add
          path: "spec.attributes.avatar"
          description: "新增头像URL字段"
```

### 规范注册表

```yaml
registry:
  specs:
    - name: "auth/User"
      currentVersion: "2.0.0"
      latestStable: "2.0.0"
      versions:
        - "2.0.0"
        - "1.5.0"
        - "1.0.0"
      owner: "auth-team"
      tags: [core, user-management]
      
    - name: "auth/API"
      currentVersion: "2.1.0"
      latestStable: "2.1.0"
      versions:
        - "2.1.0"
        - "2.0.0"
        - "1.0.0"
      owner: "auth-team"
      tags: [api, authentication]
      
  dependencyGraph:
    nodes:
      - id: "auth/User"
        version: "2.0.0"
      - id: "auth/API"
        version: "2.1.0"
      - id: "order/Order"
        version: "1.0.0"
    edges:
      - from: "auth/API"
        to: "auth/User"
        type: references
      - from: "order/Order"
        to: "auth/User"
        type: references
```

### 版本回滚机制

```yaml
rollbackPolicy:
  allowedRollbacks:
    - from: "approved"
      to: "review"
      requires: "技术负责人审批"
      
    - from: "deprecated"
      to: "approved"
      requires: "团队评审通过"
      conditions:
        - "无替代版本"
        - "仍有活跃使用"
        
  rollbackSteps:
    - step: "创建回滚请求"
      action: "提交回滚原因和影响评估"
    - step: "审批流程"
      action: "获取必要审批"
    - step: "执行回滚"
      action: "更新规范状态，通知相关方"
    - step: "代码同步"
      action: "回滚相关生成代码"
    - step: "文档更新"
      action: "更新变更日志和文档"
```

---

## v4.0 更新

### 📝 可执行条款提取引擎 (Clause Extraction Engine)

v4.0 在传统 SDD 规范定义→解析→生成→验证 的基础上，增加了 **可执行条款提取** 能力，使 SDD 规范能够更精确地驱动 TDD 测试生成，实现 SDD→TDD 的无缝衔接。

#### 增强后的SDD流程

```
v4.0 增强版 SDD 流程
═════════════════════

  传统流程:
  规范定义 → 规范解析 → 代码生成 → 验证

  v4.0 流程:
  规范定义 → 规范解析 → 条款提取 → 测试生成 → 代码生成 → 验证
                  │           │           │
                  ▼           ▼           ▼
             结构化中间表示  可执行条款集  TDD测试骨架
                           (前置+步骤+预期+验收)
```

#### 条款类型分类体系

| 类型 | 子类型 | 优先级 | 来源 | 说明 |
|------|--------|--------|------|------|
| **FunctionalClause** | PositiveClause | P0 | 功能规范 | 核心happy path |
| | BoundaryClause | P1 | 功能规范 | 边界值处理 |
| | ExceptionClause | P1 | 功能规范 | 异常处理 |
| **ApiClause** | ParamValidationClause | P1 | 接口规范 | 参数验证 |
| | PermissionClause | P1 | 接口规范 | 权限检查 |
| | ResponseFormatClause | P2 | 接口规范 | 响应格式 |
| **BusinessRuleClause** | TriggerClause | P0/P1 | 业务规则 | 触发条件 |
| | CalculationClause | P1 | 业务规则 | 计算逻辑 |
| | TransitionClause | P1 | 业务规则 | 状态流转 |
| **PerformanceClause** | LatencyClause | P2 | 性能规范 | 延迟要求 |
| **SecurityClause** | AuthClause | P0/P1 | 安全规范 | 认证授权 |

#### 条款提取规则引擎核心接口

```python
class ClauseExtractionEngine:
    """SDD规范可执行条款提取引擎"""
    
    EXTRACTION_RULES = {
        "function_spec": FunctionClauseExtractor(),     # 功能规范→功能条款
        "api_spec": ApiClauseExtractor(),               # 接口规范→API条款
        "business_rule_spec": BusinessRuleClauseExtractor(),  # 业务规则→规则条款
        "performance_spec": PerformanceClauseExtractor(),    # 性能规范→性能条款
        "security_spec": SecurityClauseExtractor()          # 安全规范→安全条款
    }
    
    def extract(self, parsed_spec: ParsedSpecification) -> ClauseSet:
        """从解析后的SDD规范提取可执行条款集合"""
        clause_set = ClauseSet(spec_id=parsed_spec.id)
        
        for section in parsed_spec.sections:
            extractor = self.EXTRACTION_RULES.get(section.type)
            if extractor:
                new_clauses = extractor.extract(section, clause_set.next_id())
                clause_set.add_clauses(new_clauses)
        
        # 后处理: 解析依赖/去重/分配优先级/估算工作量/完整性校验
        self._resolve_dependencies(clause_set)
        self._deduplicate(clause_set)
        self._assign_priorities(clause_set)
        self._estimate_effort(clause_set)
        self._validate_completeness(clause_set)
        
        return clause_set
```

#### 各类型提取器输出示例

**FunctionClauseExtractor 输出** (以登录功能为例):
```python
# 从功能规范自动提取的条款列表:
[
    ExecutableClause(
        id="CL-AUTH-001-001", type="functional_positive", priority="P0",
        preconditions=["用户存在于数据库", "密码未过期"],
        steps=[ClauseStep(1, "提交用户名和密码", {...})],
        expected_results=["返回有效JWT Token", "Token有效期24小时"],
        tags=["positive", "happy-path"]
    ),
    ExecutableClause(
        id="CL-AUTH-001-002", type="functional_boundary", priority="P1",
        preconditions=['username设为"ab" (2字符, < min 3)'],
        steps=[ClauseStep(1, "提交边界值用户名", {...})],
        expected_results=["返回ValidationError", "错误码10003"],
        tags=["boundary", "username"]
    ),
    ExecutableClause(
        id="CL-AUTH-001-005", type="functional_exception", priority="P1",
        preconditions=["用户连续失败5次", "账户未被手动解锁"],
        steps=[ClauseStep(1, "尝试登录", {...})],
        expected_results=["抛出AccountLockedError", "HTTP 403"],
        tags=["exception", "AccountLocked"]
    ),
]
```

**ApiClauseExtractor 输出**:
```python
# 从接口规范自动提取的条款列表:
[
    ExecutableClause(id="CL-API-LOGIN-001", type="api_positive_request", priority="P0",
        preconditions=["使用有效认证令牌", "请求体格式正确"],
        steps=[ClauseStep(1, "POST /api/v1/auth/login", request_body)],
        expected_results=["HTTP 200", "响应含token"]),
    ExecutableClause(id="CL-API-LOGIN-002", type="api_missing_param", priority="P1",
        preconditions=['请求缺少"password"字段'],
        steps=[ClauseStep(1, "POST /login 无密码", {})],
        expected_results=["HTTP 400", '错误信息包含"password"']),
    ExecutableClause(id="CL-API-LOGIN-003", type="api_unauthorized", priority="P1",
        preconditions=["使用无效/缺失token"],
        steps=[ClauseStep(1, "POST /login 未认证", {})],
        expected_results=["HTTP 401 Unauthorized"]),
]
```

#### 条款集合与覆盖率报告

```python
@dataclass
class ClauseSet:
    spec_id: str
    clauses: List[ExecutableClause]
    
    def coverage_report(self, test_results) -> ClauseCoverageReport:
        covered_ids = {tc.clause_id for tc in test_results.passed_tests}
        return ClauseCoverageReport(
            total=len(self.clauses),
            covered=len(covered_ids),
            coverage_percent=len(covered_ids) / len(self.clauses) * 100,
            by_priority={p: CoverageDetail(...) for p in ["P0","P1","P2","P3"]},
            missing=[c for c in self.clauses if c.id not in covered_ids]
        )
    
    def to_markdown(self) -> str:
        """导出为Markdown格式的条款文档供审查"""
```

#### SDD v2.0 规范模板（支持条款提取）

在现有 `sdd/v1` 模板基础上增加条款提取友好标注：

```yaml
# v2.0 SDD 规范文件模板 (支持自动条款提取)
apiVersion: sdd/v2   # v2 支持条款提取
kind: FeatureSpec
metadata:
  name: UserAuthentication
  version: 1.0.0
  clause_extraction:
    enabled: true
    auto_generate_tests: true
    test_framework: pytest
spec:
  features:
    - id: AUTH-LOGIN
      name: 用户登录
      clause_hints:
        positive_scenarios: 1
        boundary_per_param: true
        exception_per_declared: true
      inputs:
        - name: username
          constraints:
            min_length: 3
            max_length: 50
          bounds:       # ← 边界值定义 (自动生成边界条款)
            - name: 最小长度; value: "ab"; expected: 应拒绝
            - name: 最大长度; value: "a"*51; expected: 应拒绝
        - name: password
          constraints:
            min_length: 8
      exceptions:      # ← 异常声明 (自动生成异常条款)
        - type: UserNotFoundError; trigger: 用户不存在; status_code: 401
        - type: InvalidPasswordError; trigger: 密码错误; status_code: 401
        - type: AccountLockedError; trigger: 连续5次失败; status_code: 403
      acceptance_criteria:
        - 成功登录返回JWT (24h有效)
        - 密码错误5次后锁定30分钟
      business_rules:  # ← 业务规则 (自动生成规则条款)
        - id: BR-AUTH-001
          type: calculation; priority: 100
          conditions: ["failed_attempts >= 5"]
          actions: [{action: lock_account, duration_minutes: 30}]
```

#### 与Workflow DSL的集成

```yaml
# 使用Workflow DSL定义条款提取→测试→实现的自动化流水线
name: sdd-clause-driven-pipeline
steps:
  - name: sdd_parsing
    type: single
    agent: zhongshusheng-guifan-zhiding-si
    
  - name: clause_extraction
    type: single
    agent: bingbu-ce-shihua-jishisi
    config:
      task: "运行ClauseExtractEngine"
      
  - name: test_generation
    type: parallel
    steps:
      - name: unit_tests
        type: single
        config: {clause_filter: "priority in ['P0','P1']"}
      - name: integration_tests
        type: single
        config: {clause_filter: "type starts_with 'api'"}
          
  - name: red_phase_confirm
    type: conditional
    variable: all_tests_fail
    operator: equals
    value: true
    then_step: {name: proceed_to_green, type: single, agent: gongbu-daima-shengchengsi}
    else_step: {name: investigate, type: single, agent: menxiasheng-daima-shenchajujing-fangan-pingsheni}

on_error: retry_with_backoff
metadata:
  clause_coverage_threshold: 95%
  required_priorities: ["P0", "P1"]
```

#### v4.0 SDD增强总结

| 维度 | v3.3.0 | v4.0 增强 | 提升 |
|------|--------|----------|------|
| **规范→测试** | 手动映射 | Clause Extraction Engine 自动提取 | 自动化率 60%→95% |
| **条款粒度** | 无概念 | 5大类×多子类型 | 覆盖面更全面 |
| **追溯关系** | 文档化 | clause_id ↔ test_id 自动绑定 | 可操作性提升 |
| **覆盖率度量** | 行/分支覆盖 | +条款覆盖率(Clause Coverage) | 质量更量化 |
| **工作流编排** | 手动协调 | Workflow DSL 声明式 | 可重复、可自动化 |
