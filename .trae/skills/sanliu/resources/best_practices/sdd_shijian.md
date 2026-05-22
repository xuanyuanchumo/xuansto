# SDD 最佳实践指南

## SDD 最佳实践概述

规范驱动开发（Specification-Driven Development，SDD）是一种以规范为核心的软件开发方法论。通过先定义清晰的规范，再基于规范生成代码，确保代码与需求的一致性，提高开发效率和代码质量。

### 核心价值

- **一致性**：规范作为单一事实来源，确保所有实现与需求保持一致
- **可追溯性**：从代码到规范的双向追溯，便于理解和维护
- **自动化**：基于规范自动生成代码，减少人工错误
- **协作性**：规范作为团队沟通的通用语言

### SDD 工作流程

```
需求分析 → 规范编写 → 规范解析 → 代码生成 → 规范验证 → 持续迭代
```

---

## 规范编写最佳实践

### 1. 规范结构化

#### 使用标准化模板

```markdown
# 功能名称

## 概述
简要描述功能的目的和价值

## 接口定义
- 输入参数
- 输出结果
- 副作用

## 行为规范
- 正常流程
- 异常处理
- 边界条件

## 约束条件
- 性能要求
- 安全限制
- 兼容性要求

## 示例
提供具体的使用示例
```

#### 保持规范的层次性

```
规范文档
├── 模块级规范
│   ├── 组件规范
│   │   ├── 函数规范
│   │   └── 类型规范
│   └── 接口规范
└── 集成规范
```

### 2. 规范精确性

#### 使用明确的术语

```markdown
❌ 不好的示例：
处理用户请求，返回结果

✅ 好的示例：
接收 UserRequest 对象，验证字段完整性后，
调用 UserService.process() 方法，
返回 Promise<UserResponse> 或抛出 ValidationError
```

#### 量化约束条件

```markdown
❌ 不好的示例：
响应时间要快

✅ 好的示例：
API 响应时间在 P95 百分位下不超过 200ms
```

### 3. 规范完整性

#### 覆盖所有场景

- 正常流程（Happy Path）
- 异常流程（Error Path）
- 边界条件（Edge Cases）
- 并发场景（Concurrency）

#### 示例：完整的函数规范

```markdown
## 函数：calculateDiscount

### 描述
根据用户等级和订单金额计算折扣

### 参数
- `userLevel`: UserLevel - 用户等级枚举（NORMAL, SILVER, GOLD, PLATINUM）
- `orderAmount`: number - 订单金额，必须大于 0

### 返回值
- `DiscountResult` 对象，包含：
  - `discountRate`: number - 折扣率（0-1）
  - `discountAmount`: number - 折扣金额
  - `finalAmount`: number - 最终金额

### 异常
- `InvalidUserLevelError`: 用户等级无效时抛出
- `InvalidAmountError`: 订单金额小于等于 0 时抛出

### 业务规则
| 用户等级 | 折扣率 |
|---------|--------|
| NORMAL  | 0%     |
| SILVER  | 5%     |
| GOLD    | 10%    |
| PLATINUM| 15%    |

### 示例
```typescript
calculateDiscount('GOLD', 1000)
// 返回: { discountRate: 0.1, discountAmount: 100, finalAmount: 900 }

calculateDiscount('INVALID', 1000)
// 抛出: InvalidUserLevelError

calculateDiscount('GOLD', -100)
// 抛出: InvalidAmountError
```
```

### 4. 规范可维护性

#### 版本控制

```markdown
## 版本历史
- v2.0.0 (2024-03-15): 新增 PLATINUM 等级
- v1.1.0 (2024-02-01): 调整 GOLD 等级折扣率
- v1.0.0 (2024-01-01): 初始版本
```

#### 变更日志

```markdown
## 变更记录

### [2024-03-15] 新增 PLATINUM 等级
- 原因：引入高级会员体系
- 影响：折扣计算逻辑、用户等级枚举
- 迁移指南：现有 GOLD 用户需评估是否升级
```

---

## 规范解析最佳实践

### 1. 解析器设计原则

#### 单一职责

每个解析器只负责解析特定类型的规范：

```
SpecParser
├── ApiSpecParser      # API 规范解析
├── DataSpecParser     # 数据模型解析
├── BehaviorSpecParser # 行为规范解析
└── ConstraintParser   # 约束条件解析
```

#### 可扩展性

使用插件机制支持自定义解析器：

```typescript
interface SpecParser {
  type: string
  parse(content: string): ParsedSpec
  validate(spec: ParsedSpec): ValidationResult
}

class ParserRegistry {
  private parsers: Map<string, SpecParser>
  
  register(parser: SpecParser): void
  get(type: string): SpecParser
}
```

### 2. 解析验证

#### 语法验证

- 规范格式正确性
- 必填字段完整性
- 数据类型正确性

#### 语义验证

- 业务逻辑一致性
- 引用完整性
- 约束条件合理性

#### 示例：验证流程

```typescript
function validateSpec(spec: ParsedSpec): ValidationResult {
  const errors: ValidationError[] = []
  
  // 语法验证
  if (!spec.name || spec.name.trim() === '') {
    errors.push({ field: 'name', message: '规范名称不能为空' })
  }
  
  // 语义验证
  if (spec.parameters) {
    for (const param of spec.parameters) {
      if (param.required && param.defaultValue !== undefined) {
        errors.push({
          field: `parameters.${param.name}`,
          message: '必填参数不应有默认值'
        })
      }
    }
  }
  
  return { valid: errors.length === 0, errors }
}
```

### 3. 解析结果缓存

```typescript
class CachedSpecParser {
  private cache: Map<string, CachedResult>
  
  parse(specPath: string): ParsedSpec {
    const cached = this.cache.get(specPath)
    const lastModified = fs.statSync(specPath).mtime
    
    if (cached && cached.timestamp >= lastModified) {
      return cached.spec
    }
    
    const spec = this.doParse(specPath)
    this.cache.set(specPath, { spec, timestamp: new Date() })
    
    return spec
  }
}
```

---

## 代码生成最佳实践

### 1. 模板化生成

#### 模板设计原则

- 模板与逻辑分离
- 支持模板继承和组合
- 模板可测试

#### 示例：函数模板

```typescript
// 模板定义
const functionTemplate = `
export function {{name}}({{#each parameters}}{{name}}: {{type}}{{#unless @last}}, {{/unless}}{{/each}}): {{returnType}} {
  {{#if hasValidation}}
  // 参数验证
  {{#each validations}}
  if ({{condition}}) {
    throw new {{errorType}}('{{errorMessage}}')
  }
  {{/each}}
  {{/if}}
  
  {{#if hasImplementation}}
  // 实现
  {{implementation}}
  {{else}}
  throw new Error('Not implemented')
  {{/if}}
}
`

// 生成器
function generateFunction(spec: FunctionSpec): string {
  return renderTemplate(functionTemplate, {
    name: spec.name,
    parameters: spec.parameters,
    returnType: spec.returnType,
    validations: buildValidations(spec),
    hasImplementation: spec.implementation !== undefined
  })
}
```

### 2. 增量生成

#### 识别变更范围

```typescript
interface GenerationPlan {
  added: Spec[]      // 新增规范
  modified: Spec[]   // 修改规范
  deleted: Spec[]    // 删除规范
  affected: Spec[]   // 受影响规范
}

function planGeneration(oldSpecs: Spec[], newSpecs: Spec[]): GenerationPlan {
  const oldMap = new Map(oldSpecs.map(s => [s.id, s]))
  const newMap = new Map(newSpecs.map(s => [s.id, s]))
  
  const added = newSpecs.filter(s => !oldMap.has(s.id))
  const deleted = oldSpecs.filter(s => !newMap.has(s.id))
  const modified = newSpecs.filter(s => {
    const old = oldMap.get(s.id)
    return old && !deepEqual(old, s)
  })
  
  const affected = findAffectedSpecs(modified, newSpecs)
  
  return { added, modified, deleted, affected }
}
```

#### 保护手工代码

```typescript
// 使用注解标记手工代码区域
/**
 * @sdd-generated-start: calculateDiscount
 */
export function calculateDiscount(userLevel: UserLevel, orderAmount: number): DiscountResult {
  // 自动生成的代码
  // ...
}
/**
 * @sdd-generated-end: calculateDiscount
 */

/**
 * @sdd-manual-start: custom-logic
 */
// 手工编写的自定义逻辑
function customDiscountLogic() {
  // ...
}
/**
 * @sdd-manual-end: custom-logic
 */
```

### 3. 代码质量保证

#### 生成代码风格统一

```typescript
const codeStyleConfig = {
  indent: '  ',
  semicolons: true,
  quotes: 'single',
  trailingComma: 'es5',
  printWidth: 100
}

function formatGeneratedCode(code: string): string {
  return prettier.format(code, {
    parser: 'typescript',
    ...codeStyleConfig
  })
}
```

#### 生成代码注释

```typescript
function generateWithComments(spec: Spec): string {
  const code = generateCode(spec)
  
  return `
/**
 * ${spec.description}
 * 
 * @sdd-spec ${spec.id}
 * @sdd-version ${spec.version}
 * @sdd-generated ${new Date().toISOString()}
 * 
 * @param {${spec.paramType}} ${spec.paramName} - ${spec.paramDescription}
 * @returns {${spec.returnType}} ${spec.returnDescription}
 * @throws {${spec.errorType}} ${spec.errorDescription}
 */
${code}
`
}
```

---

## 规范验证最佳实践

### 1. 一致性验证

#### 代码与规范一致性

```typescript
interface ConsistencyCheck {
  spec: Spec
  code: Code
  matches: MatchResult[]
  mismatches: MismatchResult[]
}

function checkConsistency(spec: Spec, code: Code): ConsistencyCheck {
  const matches: MatchResult[] = []
  const mismatches: MismatchResult[] = []
  
  // 检查函数签名
  if (spec.function) {
    const codeFunction = findFunction(code, spec.function.name)
    if (codeFunction) {
      const signatureMatch = compareSignature(spec.function, codeFunction)
      if (!signatureMatch.valid) {
        mismatches.push({
          type: 'signature',
          expected: signatureMatch.expected,
          actual: signatureMatch.actual
        })
      }
    }
  }
  
  return { spec, code, matches, mismatches }
}
```

### 2. 行为验证

#### 基于规范的测试生成

```typescript
function generateTestsFromSpec(spec: BehaviorSpec): TestCase[] {
  const tests: TestCase[] = []
  
  // 正常流程测试
  tests.push({
    name: `${spec.name} - 正常流程`,
    input: spec.happyPath.input,
    expected: spec.happyPath.output
  })
  
  // 异常流程测试
  for (const errorCase of spec.errorPaths) {
    tests.push({
      name: `${spec.name} - ${errorCase.description}`,
      input: errorCase.input,
      expectedError: errorCase.error
    })
  }
  
  // 边界条件测试
  for (const edgeCase of spec.edgeCases) {
    tests.push({
      name: `${spec.name} - 边界: ${edgeCase.description}`,
      input: edgeCase.input,
      expected: edgeCase.output
    })
  }
  
  return tests
}
```

### 3. 持续验证

#### CI/CD 集成

```yaml
# .github/workflows/sdd-validation.yml
name: SDD Validation

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Validate Specs
        run: sdd-cli validate --strict
        
      - name: Check Consistency
        run: sdd-cli check-consistency
        
      - name: Generate Tests
        run: sdd-cli generate-tests
        
      - name: Run Tests
        run: npm test
```

---

## SDD + TDD 融合最佳实践

### 1. 工作流整合

```
规范编写 → 测试用例生成 → 测试驱动开发 → 代码生成 → 验证
    ↓           ↓              ↓            ↓         ↓
  Spec       Test Cases    Red-Green    Code      Consistency
                          -Refactor              Check
```

### 2. 规范即测试

#### 使用规范定义测试

```markdown
## 函数：divide

### 行为规范

#### 正常除法
- 输入: dividend=10, divisor=2
- 输出: 5

#### 除以零
- 输入: dividend=10, divisor=0
- 异常: DivisionByZeroError

#### 浮点精度
- 输入: dividend=1, divisor=3
- 输出: 0.333... (精度 6 位小数)
```

#### 自动生成测试代码

```typescript
describe('divide', () => {
  it('正常除法', () => {
    expect(divide(10, 2)).toBe(5)
  })
  
  it('除以零', () => {
    expect(() => divide(10, 0)).toThrow(DivisionByZeroError)
  })
  
  it('浮点精度', () => {
    const result = divide(1, 3)
    expect(result).toBeCloseTo(0.333333, 6)
  })
})
```

### 3. TDD 反哺规范

#### 从测试完善规范

```typescript
// TDD 过程中发现边界情况
it('处理大数除法', () => {
  const result = divide(Number.MAX_SAFE_INTEGER, 2)
  expect(result).toBe(Number.MAX_SAFE_INTEGER / 2)
})

// 将发现的边界情况补充到规范
```

```markdown
## 函数：divide

### 边界条件

#### 大数处理
- 输入: dividend=Number.MAX_SAFE_INTEGER, divisor=2
- 输出: Number.MAX_SAFE_INTEGER / 2
- 注意: 需要考虑 JavaScript 数值精度限制
```

---

## 常见陷阱与避免方法

### 1. 规范过于抽象

#### 问题

```markdown
❌ 不好的示例：
用户管理模块负责管理用户
```

#### 解决方案

```markdown
✅ 好的示例：
用户管理模块提供以下功能：
1. 用户注册：接收 RegisterRequest，验证后创建 User 记录
2. 用户登录：接收 LoginRequest，验证后返回 AuthToken
3. 用户信息更新：接收 UpdateRequest，验证后更新 User 记录
```

### 2. 规范与实现脱节

#### 问题

规范更新后，代码未同步更新

#### 解决方案

- 建立规范变更通知机制
- 自动化一致性检查
- 代码审查时检查规范引用

```typescript
// 在代码中引用规范
/**
 * @sdd-spec user-service/create-user
 * @sdd-version 2.1.0
 */
async function createUser(request: RegisterRequest): Promise<User> {
  // 实现
}
```

### 3. 过度生成

#### 问题

生成过多不必要的代码，导致维护困难

#### 解决方案

- 只生成稳定的、重复性高的代码
- 复杂业务逻辑手工编写
- 使用部分生成策略

```typescript
// 只生成骨架，业务逻辑手工实现
/**
 * @sdd-generated-skeleton
 */
async function processOrder(order: Order): Promise<OrderResult> {
  // 验证逻辑 - 自动生成
  validateOrder(order)
  
  // 业务逻辑 - 手工实现
  // @sdd-manual-impl
  const result = await complexBusinessLogic(order)
  
  return result
}
```

### 4. 忽视规范演进

#### 问题

规范一成不变，无法适应需求变化

#### 解决方案

- 建立规范版本管理
- 定期评审规范有效性
- 收集使用反馈持续改进

```markdown
## 规范评审清单

- [ ] 规范是否反映当前业务需求？
- [ ] 是否有遗漏的场景？
- [ ] 约束条件是否仍然合理？
- [ ] 是否有更好的抽象方式？
- [ ] 团队是否理解并遵循规范？
```

---

## 团队协作最佳实践

### 1. 规范所有权

#### 角色定义

| 角色 | 职责 |
|------|------|
| 规范负责人 | 维护规范完整性，审批变更 |
| 规范贡献者 | 提出改进建议，参与评审 |
| 规范使用者 | 遵循规范，反馈问题 |

#### 变更流程

```
提出变更请求 → 技术评审 → 团队讨论 → 批准/拒绝 → 实施变更 → 通知相关方
```

### 2. 规范评审

#### 评审清单

```markdown
## 规范评审清单

### 完整性
- [ ] 是否覆盖所有场景？
- [ ] 是否定义所有接口？
- [ ] 是否说明异常处理？

### 清晰性
- [ ] 术语是否明确？
- [ ] 示例是否充分？
- [ ] 是否有歧义？

### 可行性
- [ ] 技术上是否可实现？
- [ ] 是否有性能风险？
- [ ] 是否与现有系统兼容？

### 可维护性
- [ ] 是否易于理解？
- [ ] 是否易于扩展？
- [ ] 是否有版本管理？
```

### 3. 知识共享

#### 规范文档化

- 使用统一的文档模板
- 提供丰富的示例
- 保持文档更新

#### 培训与指导

- 新成员规范培训
- 定期规范分享会
- 最佳实践案例库

### 4. 协作工具

#### 规范管理平台

- 集中存储规范文档
- 版本控制和历史追踪
- 变更通知和审批流程

#### 集成开发环境

- IDE 插件支持规范查看
- 代码与规范关联提示
- 实时一致性检查

---

## 工具链推荐

### 1. 规范编写工具

| 工具 | 用途 | 特点 |
|------|------|------|
| Markdown | 规范文档编写 | 简单易用，版本控制友好 |
| OpenAPI | API 规范定义 | 标准化，工具支持丰富 |
| JSON Schema | 数据模型定义 | 可验证，多语言支持 |
| PlantUML | 架构图绘制 | 文本化，易于维护 |

### 2. 规范解析工具

| 工具 | 用途 | 特点 |
|------|------|------|
| Ajv | JSON Schema 验证 | 高性能，标准兼容 |
| Spectral | OpenAPI 规范检查 | 可定制规则 |
| markdown-it | Markdown 解析 | 插件丰富 |

### 3. 代码生成工具

| 工具 | 用途 | 特点 |
|------|------|------|
| Handlebars | 模板引擎 | 灵活，易学习 |
| Prettier | 代码格式化 | 多语言支持 |
| Hygen | 代码生成器 | 交互式，模板化 |

### 4. 验证工具

| 工具 | 用途 | 特点 |
|------|------|------|
| Jest | 测试框架 | 快照测试，覆盖率 |
| Schema Matchers | 规范匹配 | Jest 集成 |
| diff 工具 | 一致性检查 | 变更可视化 |

### 5. CI/CD 集成

| 工具 | 用途 | 特点 |
|------|------|------|
| GitHub Actions | 自动化流程 | 与 GitHub 深度集成 |
| Husky | Git Hooks | 本地验证 |
| lint-staged | 增量检查 | 性能优化 |

### 6. 自定义工具链示例

```typescript
// sdd-cli.ts - 自定义 SDD 命令行工具

import { Command } from 'commander'
import { SpecParser } from './parsers'
import { CodeGenerator } from './generators'
import { ConsistencyChecker } from './validators'

const program = new Command()

program
  .command('validate')
  .description('验证规范文件')
  .option('--strict', '严格模式')
  .action(async (options) => {
    const parser = new SpecParser()
    const specs = await parser.parseAll('./specs')
    const results = specs.map(s => parser.validate(s))
    
    if (results.some(r => !r.valid)) {
      console.error('规范验证失败')
      process.exit(1)
    }
    
    console.log('规范验证通过')
  })

program
  .command('generate')
  .description('基于规范生成代码')
  .option('--incremental', '增量生成')
  .action(async (options) => {
    const generator = new CodeGenerator()
    await generator.generateAll(options.incremental)
    console.log('代码生成完成')
  })

program
  .command('check')
  .description('检查代码与规范一致性')
  .action(async () => {
    const checker = new ConsistencyChecker()
    const issues = await checker.check()
    
    if (issues.length > 0) {
      console.error('发现不一致:', issues)
      process.exit(1)
    }
    
    console.log('一致性检查通过')
  })

program.parse()
```

---

## 总结

SDD 最佳实践的核心要点：

1. **规范先行**：在编码前完成规范的编写和评审
2. **精确表达**：使用明确、可验证的语言描述规范
3. **自动化优先**：利用工具链实现规范解析、代码生成和验证的自动化
4. **持续验证**：建立规范与代码的一致性检查机制
5. **团队协作**：明确规范所有权，建立变更流程
6. **迭代改进**：根据实践反馈持续优化规范和工具链

通过遵循这些最佳实践，团队可以充分发挥 SDD 的价值，提高开发效率和代码质量。
