---
name: guifan_jiexi
description: 规范解析子技能，将自然语言需求或结构化规范解析为可执行的中间表示。
---

# 规范解析子技能

## 概述
将自然语言需求或结构化规范（YAML/JSON）解析为统一的中间表示（IR），为后续代码生成、测试设计等环节提供标准化输入。

## 调用时机
- 中书省接收用户需求时
- 结构化规范输入时
- 需求变更重新解析时

## 规范解析流程

```
输入（自然语言/结构化规范）
    ↓
预处理（文本清洗、格式标准化）
    ↓
实体提取（识别关键实体）
    ↓
关系提取（识别实体间关系）
    ↓
约束提取（识别业务约束）
    ↓
中间表示（IR）生成
    ↓
验证与输出
```

## 自然语言解析规则

### 1. 关键词识别

| 类别 | 关键词模式 | 解析动作 |
|------|-----------|----------|
| 实体定义 | "用户"、"订单"、"商品"、"系统"等名词 | 标记为实体候选 |
| 属性描述 | "包含"、"具有"、"拥有"、"字段" | 提取实体属性 |
| 关系描述 | "属于"、"关联"、"引用"、"包含" | 提取实体关系 |
| 约束条件 | "必须"、"不能"、"应当"、"禁止" | 提取业务约束 |
| 操作动作 | "创建"、"删除"、"修改"、"查询" | 提取CRUD操作 |
| 条件判断 | "如果"、"当...时"、"若" | 提取条件逻辑 |
| 数量限定 | "至少"、"最多"、"恰好"、"范围" | 提取数量约束 |

### 2. 实体提取规则

**识别模式：**
```
实体 = {
  名称: string,           // 实体名称
  类型: "核心" | "辅助" | "外部",  // 实体类型
  属性列表: Attribute[],  // 属性集合
  描述: string           // 实体描述
}

Attribute = {
  名称: string,
  类型: "string" | "number" | "boolean" | "date" | "object" | "array",
  必填: boolean,
  默认值: any,
  描述: string
}
```

**提取步骤：**
1. 识别句子中的主语名词作为实体候选
2. 过滤通用词（如"系统"、"平台"等除非特指）
3. 提取实体相关的属性描述
4. 推断属性类型和约束

**示例：**
```
输入: "用户包含用户名、密码、邮箱，用户名必须唯一"

输出:
实体: User
属性:
  - username: string, 必填, 唯一约束
  - password: string, 必填
  - email: string, 必填
```

### 3. 关系推断规则

**关系类型：**
| 关系类型 | 关键词 | 基数 |
|---------|--------|------|
| 一对一 | "唯一关联"、"对应" | 1:1 |
| 一对多 | "包含多个"、"拥有列表" | 1:N |
| 多对多 | "相互关联"、"双向" | M:N |
| 属于 | "属于"、"归属于" | N:1 |

**关系表示：**
```
Relation = {
  名称: string,
  源实体: string,
  目标实体: string,
  类型: "1:1" | "1:N" | "N:1" | "M:N",
  导航属性: {
    正向: string,  // 源到目标的属性名
    反向: string   // 目标到源的属性名（可选）
  },
  级联操作: {
    删除: "cascade" | "restrict" | "set_null",
    更新: "cascade" | "restrict" | "set_null"
  }
}
```

**示例：**
```
输入: "订单包含多个商品项，每个商品项关联一个商品"

输出:
关系: Order -> OrderItem (1:N)
关系: OrderItem -> Product (N:1)
```

## 结构化规范解析规则

### 1. YAML 格式解析

**支持的 YAML 结构：**
```yaml
entities:
  - name: User
    attributes:
      - name: id
        type: string
        required: true
      - name: username
        type: string
        required: true
        unique: true

relations:
  - name: user_orders
    from: User
    to: Order
    type: 1:N

constraints:
  - type: unique
    entity: User
    field: username
  - type: range
    entity: Order
    field: total
    min: 0
```

**解析规则：**
- `entities` 节点映射为实体集合
- `relations` 节点映射为关系集合
- `constraints` 节点映射为约束集合
- 未识别的字段保留到扩展属性

### 2. JSON 格式解析

**支持的 JSON 结构：**
```json
{
  "entities": [
    {
      "name": "User",
      "attributes": [
        {"name": "id", "type": "string", "required": true}
      ]
    }
  ],
  "relations": [...],
  "constraints": [...]
}
```

**解析规则：**
- 遵循与 YAML 相同的语义映射
- 支持嵌套对象展开
- 数组类型自动识别

## 约束提取规则

### 1. 约束类型定义

| 约束类型 | 描述 | 示例 |
|---------|------|------|
| unique | 唯一性约束 | 用户名唯一 |
| required | 非空约束 | 密码必填 |
| range | 范围约束 | 年龄 0-150 |
| pattern | 正则约束 | 邮箱格式 |
| enum | 枚举约束 | 状态：启用/禁用 |
| custom | 自定义约束 | 业务规则表达式 |

### 2. 约束表示

```
Constraint = {
  id: string,              // 约束唯一标识
  类型: "unique" | "required" | "range" | "pattern" | "enum" | "custom",
  实体: string,            // 约束所属实体
  字段: string | string[], // 约束字段（支持组合约束）
  参数: {                  // 约束参数
    min?: number,
    max?: number,
    pattern?: string,
    values?: any[],
    expression?: string    // 自定义表达式
  },
  错误消息: string         // 违反约束时的提示
}
```

### 3. 约束提取示例

```
输入: "用户年龄必须在18到120之间，邮箱需符合标准格式"

输出:
约束1: {
  类型: range,
  实体: User,
  字段: age,
  参数: { min: 18, max: 120 }
}
约束2: {
  类型: pattern,
  实体: User,
  字段: email,
  参数: { pattern: "^[\\w-\\.]+@([\\w-]+\\.)+[\\w-]{2,4}$" }
}
```

## 中间表示（IR）格式定义

### 完整 IR 结构

```typescript
interface IntermediateRepresentation {
  version: string;           // IR 版本号
  metadata: {
    项目名称: string;
    创建时间: string;
    来源: "natural_language" | "yaml" | "json";
  };
  entities: Entity[];        // 实体集合
  relations: Relation[];     // 关系集合
  constraints: Constraint[]; // 约束集合
  operations: Operation[];   // 操作集合
  validations: Validation[]; // 验证规则集合
}

interface Operation {
  名称: string;
  类型: "create" | "read" | "update" | "delete" | "custom";
  实体: string;
  输入参数: Parameter[];
  输出: ReturnType;
  前置条件: string[];
  后置条件: string[];
}

interface Validation {
  名称: string;
  适用实体: string;
  规则: ValidationRule[];
}
```

### IR 验证规则

1. **完整性检查**
   - 所有实体必须有唯一名称
   - 关系引用的实体必须存在
   - 约束引用的实体和字段必须存在

2. **一致性检查**
   - 无循环依赖（实体关系）
   - 无冲突约束（如同时要求必填和可为空）

3. **有效性检查**
   - 类型定义合法
   - 约束参数有效

## 解析示例

### 示例1：自然语言解析

**输入：**
```
电商系统需要管理用户和订单。用户包含用户名、密码、邮箱，
用户名必须唯一，邮箱需符合标准格式。每个用户可以创建多个订单，
订单包含订单号、创建时间、总金额，总金额必须大于0。
订单包含多个商品项，每个商品项关联一个商品，包含商品数量和单价。
```

**输出 IR：**
```json
{
  "version": "1.0",
  "metadata": {
    "项目名称": "电商系统",
    "来源": "natural_language"
  },
  "entities": [
    {
      "名称": "User",
      "类型": "核心",
      "属性列表": [
        {"名称": "username", "类型": "string", "必填": true},
        {"名称": "password", "类型": "string", "必填": true},
        {"名称": "email", "类型": "string", "必填": true}
      ]
    },
    {
      "名称": "Order",
      "类型": "核心",
      "属性列表": [
        {"名称": "orderNo", "类型": "string", "必填": true},
        {"名称": "createdAt", "类型": "date", "必填": true},
        {"名称": "totalAmount", "类型": "number", "必填": true}
      ]
    },
    {
      "名称": "OrderItem",
      "类型": "辅助",
      "属性列表": [
        {"名称": "quantity", "类型": "number", "必填": true},
        {"名称": "unitPrice", "类型": "number", "必填": true}
      ]
    },
    {
      "名称": "Product",
      "类型": "核心",
      "属性列表": []
    }
  ],
  "relations": [
    {"名称": "user_orders", "源实体": "User", "目标实体": "Order", "类型": "1:N"},
    {"名称": "order_items", "源实体": "Order", "目标实体": "OrderItem", "类型": "1:N"},
    {"名称": "item_product", "源实体": "OrderItem", "目标实体": "Product", "类型": "N:1"}
  ],
  "constraints": [
    {"类型": "unique", "实体": "User", "字段": "username"},
    {"类型": "pattern", "实体": "User", "字段": "email", "参数": {"pattern": "email"}},
    {"类型": "range", "实体": "Order", "字段": "totalAmount", "参数": {"min": 0, "exclusiveMin": true}}
  ]
}
```

### 示例2：YAML 规范解析

**输入：**
```yaml
entities:
  - name: Task
    attributes:
      - name: id
        type: string
        required: true
      - name: title
        type: string
        required: true
      - name: status
        type: enum
        values: [pending, in_progress, completed]
      - name: dueDate
        type: date

relations:
  - name: task_assignee
    from: Task
    to: User
    type: N:1

constraints:
  - type: required
    entity: Task
    field: title
  - type: enum
    entity: Task
    field: status
    values: [pending, in_progress, completed]
```

**输出 IR：**
```json
{
  "version": "1.0",
  "metadata": {
    "来源": "yaml"
  },
  "entities": [
    {
      "名称": "Task",
      "类型": "核心",
      "属性列表": [
        {"名称": "id", "类型": "string", "必填": true},
        {"名称": "title", "类型": "string", "必填": true},
        {"名称": "status", "类型": "enum", "必填": false, "枚举值": ["pending", "in_progress", "completed"]},
        {"名称": "dueDate", "类型": "date", "必填": false}
      ]
    }
  ],
  "relations": [
    {"名称": "task_assignee", "源实体": "Task", "目标实体": "User", "类型": "N:1"}
  ],
  "constraints": [
    {"类型": "required", "实体": "Task", "字段": "title"},
    {"类型": "enum", "实体": "Task", "字段": "status", "参数": {"values": ["pending", "in_progress", "completed"]}}
  ]
}
```

## 输出物
- 中间表示（IR）文档
- 实体关系图描述
- 约束清单
- 解析日志（含歧义警告）

## 规范解析规则

### 解析规则分类

```
规范解析规则
├── 语法解析规则
│   ├── YAML解析规则
│   ├── JSON解析规则
│   └── Markdown解析规则
├── 语义解析规则
│   ├── 实体语义规则
│   ├── 接口语义规则
│   └── 规则语义规则
├── 类型推断规则
│   ├── 基础类型推断
│   ├── 复合类型推断
│   └── 泛型类型推断
└── 约束解析规则
    ├── 验证约束解析
    ├── 业务约束解析
    └── 安全约束解析
```

### 语法解析规则

#### YAML 解析规则

```yaml
yamlParsingRules:
  documentStart:
    pattern: "^---\\s*$"
    action: "开始新文档解析"
    
  documentEnd:
    pattern: "^\\.\\.\\.\\s*$"
    action: "结束当前文档解析"
    
  keyValue:
    pattern: "^([a-zA-Z_][a-zA-Z0-9_]*)\\s*:\\s*(.*)$"
    action: "解析键值对"
    groups:
      - name: key
        transform: "camelCase"
      - name: value
        transform: "parseValue"
        
  nestedBlock:
    pattern: "^([ \\t]+)([a-zA-Z_][a-zA-Z0-9_]*)\\s*:\\s*$"
    action: "开始嵌套块"
    groups:
      - name: indent
        transform: "indentLevel"
      - name: key
        transform: "camelCase"
        
  listItem:
    pattern: "^[ \\t]*-\\s+(.*)$"
    action: "解析列表项"
    groups:
      - name: value
        transform: "parseValue"
        
  multiLineString:
    patterns:
      - type: literal
        start: "\\|"
        preserve: newlines
      - type: folded
        start: ">"
        fold: newlines
```

#### JSON 解析规则

```yaml
jsonParsingRules:
  objectType:
    start: "{"
    end: "}"
    action: "解析对象"
    rules:
      - keyMustBeString: true
      - allowTrailingComma: false
      
  arrayType:
    start: "["
    end: "]"
    action: "解析数组"
    rules:
      - homogeneousElements: false
      - allowTrailingComma: false
      
  stringType:
    quote: ['"', "'"]
    escape: "\\"
    action: "解析字符串"
    
  numberType:
    patterns:
      - integer: "^-?[0-9]+$"
      - float: "^-?[0-9]+\\.[0-9]+([eE][+-]?[0-9]+)?$"
    action: "解析数值"
    
  booleanType:
    values: [true, false]
    action: "解析布尔值"
    
  nullType:
    values: [null]
    action: "解析空值"
```

### 语义解析规则

#### 实体语义规则

```yaml
entitySemanticRules:
  identifier:
    rules:
      - name: "主键识别"
        patterns:
          - "id"
          - "{entity}_id"
          - "_id"
        action: "标记为主键属性"
        priority: 1
        
      - name: "复合主键识别"
        condition: "多个属性标记为 primary: true"
        action: "创建复合主键定义"
        
  timestamp:
    rules:
      - name: "创建时间识别"
        patterns:
          - "created_at"
          - "createdAt"
          - "create_time"
          - "createTime"
        action: "标记为创建时间，自动填充"
        
      - name: "更新时间识别"
        patterns:
          - "updated_at"
          - "updatedAt"
          - "update_time"
          - "updateTime"
          - "modified_at"
        action: "标记为更新时间，自动更新"
        
      - name: "软删除识别"
        patterns:
          - "deleted_at"
          - "deletedAt"
          - "delete_time"
        action: "标记为软删除字段"
        
  relationship:
    rules:
      - name: "外键识别"
        patterns:
          - "{entity}_id"
          - "{entity}Id"
        action: "识别为外键关系"
        inference:
          type: "many_to_one"
          target: "{Entity}"
          
      - name: "关联表识别"
        patterns:
          - "{entity1}_{entity2}"
          - "{entity1}{entity2}"
        action: "识别为关联表"
        inference:
          type: "many_to_many"
          participants: ["{Entity1}", "{Entity2}"]
          
  enumeration:
    rules:
      - name: "枚举类型识别"
        indicators:
          - "type: enum"
          - "enum: [...]"
          - "values: [...]"
        action: "创建枚举类型定义"
```

#### 接口语义规则

```yaml
interfaceSemanticRules:
  httpMethod:
    rules:
      - name: "CRUD操作映射"
        mappings:
          - prefix: "get"
            method: GET
            operation: read
          - prefix: "list"
            method: GET
            operation: list
          - prefix: "create"
            method: POST
            operation: create
          - prefix: "update"
            method: PUT
            operation: update
          - prefix: "patch"
            method: PATCH
            operation: partial_update
          - prefix: "delete"
            method: DELETE
            operation: delete
            
  pathParameter:
    rules:
      - name: "路径参数识别"
        pattern: "\\{([a-zA-Z_][a-zA-Z0-9_]*)\\}"
        action: "提取为路径参数"
        example:
          input: "/users/{userId}/orders/{orderId}"
          output: ["userId", "orderId"]
          
  queryParameter:
    rules:
      - name: "查询参数识别"
        indicators:
          - "in: query"
          - "paramType: query"
        commonPatterns:
          - name: "分页参数"
            params: [page, pageSize, limit, offset]
          - name: "排序参数"
            params: [sortBy, sortOrder, order]
          - name: "过滤参数"
            pattern: "filter[A-Z].*"
            
  requestBody:
    rules:
      - name: "请求体类型推断"
        contentType:
          - "application/json"
          - "application/x-www-form-urlencoded"
          - "multipart/form-data"
        action: "解析请求体结构"
        
  responseCode:
    rules:
      - name: "成功响应识别"
        codes: [200, 201, 204]
        action: "标记为成功响应"
        
      - name: "错误响应识别"
        codes: [400, 401, 403, 404, 500]
        action: "标记为错误响应，提取错误信息"
```

### 类型推断规则

```yaml
typeInferenceRules:
  primitiveTypes:
    rules:
      - name: "字符串类型推断"
        patterns:
          - "type: string"
          - "type: varchar"
          - "type: text"
        inference:
          baseType: string
          
      - name: "数值类型推断"
        patterns:
          - "type: int"
          - "type: integer"
          - "type: bigint"
          - "type: number"
        inference:
          baseType: number
          
      - name: "布尔类型推断"
        patterns:
          - "type: bool"
          - "type: boolean"
        inference:
          baseType: boolean
          
      - name: "日期类型推断"
        patterns:
          - "type: date"
          - "type: datetime"
          - "type: timestamp"
        inference:
          baseType: Date
          
  compositeTypes:
    rules:
      - name: "数组类型推断"
        patterns:
          - "type: array"
          - "type: '[]'"
          - suffix: "[]"
        inference:
          baseType: Array
          elementType: "infer from items"
          
      - name: "对象类型推断"
        patterns:
          - "type: object"
          - "properties: {...}"
        inference:
          baseType: Object
          properties: "infer from properties"
          
      - name: "Map类型推断"
        patterns:
          - "type: map"
          - "additionalProperties: {...}"
        inference:
          baseType: Map
          valueType: "infer from additionalProperties"
          
  genericTypes:
    rules:
      - name: "可选类型推断"
        indicators:
          - "required: false"
          - "nullable: true"
        inference:
          wrapper: Optional
          innerType: "base type"
          
      - name: "Promise类型推断"
        context:
          - "async: true"
          - "returns: Promise"
        inference:
          wrapper: Promise
          innerType: "return type"
```

### 约束解析规则

```yaml
constraintParsingRules:
  validationConstraints:
    rules:
      - name: "必填约束"
        indicators:
          - "required: true"
          - "nullable: false"
        output:
          type: required
          validator: "isNotEmpty"
          
      - name: "长度约束"
        indicators:
          - "minLength: n"
          - "maxLength: n"
          - "length: n"
        output:
          type: length
          validator: "lengthInRange"
          params: [min, max]
          
      - name: "范围约束"
        indicators:
          - "minimum: n"
          - "maximum: n"
          - "exclusiveMinimum: true"
        output:
          type: range
          validator: "inRange"
          params: [min, max, exclusive]
          
      - name: "格式约束"
        indicators:
          - "format: email|uri|date|uuid"
          - "pattern: regex"
        output:
          type: format
          validator: "matchesFormat"
          params: [format|pattern]
          
  businessConstraints:
    rules:
      - name: "唯一性约束"
        indicators:
          - "unique: true"
          - "uniqueKey: [...]"
        output:
          type: unique
          scope: entity | table
          
      - name: "引用完整性约束"
        indicators:
          - "foreignKey: entity.field"
          - "references: entity"
        output:
          type: referential
          target: entity
          onDelete: cascade|restrict|setNull
          
      - name: "状态约束"
        indicators:
          - "status: [...]"
          - "stateMachine: {...}"
        output:
          type: state
          allowedTransitions: [...]
          
  securityConstraints:
    rules:
      - name: "敏感数据约束"
        indicators:
          - "sensitive: true"
          - "pii: true"
          - "encrypted: true"
        output:
          type: sensitive
          handling: encrypt|mask|audit
          
      - name: "访问控制约束"
        indicators:
          - "permission: ..."
          - "role: ..."
          - "scope: ..."
        output:
          type: accessControl
          requiredPermission: ...
```

## 规范到代码映射

### 映射规则概述

```
规范元素 → 代码结构映射
├── 实体规范 → 数据模型
│   ├── 属性 → 类属性/字段
│   ├── 关系 → 关联关系
│   └── 约束 → 验证逻辑
├── 接口规范 → API实现
│   ├── 端点 → 路由/控制器
│   ├── 参数 → 请求模型
│   └── 响应 → 响应模型
├── 业务规则 → 业务逻辑
│   ├── 条件 → 条件判断
│   ├── 动作 → 执行逻辑
│   └── 异常 → 错误处理
└── 约束规范 → 验证器
    ├── 数据约束 → 数据验证
    ├── 业务约束 → 业务验证
    └── 安全约束 → 安全验证
```

### 实体到代码映射

#### Python 映射规则

```yaml
entityToPython:
  class:
    template: |
      class {{className}}(Base):
          """{{description}}"""
          __tablename__ = '{{tableName}}'
          
          {{#each attributes}}
          {{name}} = Column({{columnType}}{{#if primary}}, primary_key=True{{/if}}{{#if unique}}, unique=True{{/if}}{{#if nullable is false}}, nullable=False{{/if}})
          {{/each}}
          
          {{#each relationships}}
          {{relationName}} = relationship('{{targetEntity}}', {{relationshipConfig}})
          {{/each}}
          
    typeMapping:
      string: "String({{length}})"
      text: "Text"
      integer: "Integer"
      bigint: "BigInteger"
      float: "Float"
      decimal: "Numeric({{precision}}, {{scale}})"
      boolean: "Boolean"
      date: "Date"
      datetime: "DateTime"
      json: "JSON"
      
  validator:
    template: |
      class {{className}}Validator:
          @staticmethod
          def validate(data: dict) -> List[str]:
              errors = []
              {{#each validationRules}}
              if not {{validationLogic}}:
                  errors.append("{{errorMessage}}")
              {{/each}}
              return errors
              
  pydantic:
    template: |
      class {{className}}Base(BaseModel):
          {{#each attributes}}
          {{name}}: {{#if required}}{{pythonType}}{{else}}Optional[{{pythonType}}] = None{{/if}}
          {{/each}}
          
          class Config:
              from_attributes = True
              
    typeMapping:
      string: "str"
      integer: "int"
      float: "float"
      boolean: "bool"
      date: "date"
      datetime: "datetime"
      array: "List[{{itemType}}]"
      object: "dict"
```

#### TypeScript 映射规则

```yaml
entityToTypeScript:
  interface:
    template: |
      export interface {{interfaceName}} {
        {{#each attributes}}
        {{name}}{{#unless required}}?{{/unless}}: {{typescriptType}};
        {{/each}}
      }
      
    typeMapping:
      string: "string"
      integer: "number"
      float: "number"
      boolean: "boolean"
      date: "Date"
      datetime: "Date"
      array: "{{itemType}}[]"
      object: "Record<string, {{valueType}}>"
      map: "Map<{{keyType}}, {{valueType}}>"
      
  class:
    template: |
      @Entity('{{tableName}}')
      export class {{className}} {
        {{#each attributes}}
        @Column({ {{columnOptions}} })
        {{name}}: {{typescriptType}};
        
        {{/each}}
        
        {{#each relationships}}
        @{{relationDecorator}}({{relationConfig}})
        {{relationName}}: {{relationType}};
        {{/each}}
      }
      
  zod:
    template: |
      export const {{schemaName}}Schema = z.object({
        {{#each attributes}}
        {{name}}: {{zodType}}{{#unless required}}.optional(){{/unless}},
        {{/each}}
      });
      
    typeMapping:
      string: "z.string()"
      integer: "z.number().int()"
      float: "z.number()"
      boolean: "z.boolean()"
      date: "z.date()"
      datetime: "z.date()"
      email: "z.string().email()"
      uuid: "z.string().uuid()"
      array: "z.array({{itemSchema}})"
```

### 接口到代码映射

#### FastAPI 映射规则

```yaml
interfaceToFastAPI:
  router:
    template: |
      from fastapi import APIRouter, Depends, HTTPException
      from pydantic import BaseModel
      
      router = APIRouter(prefix="{{baseUrl}}", tags=["{{tag}}"])
      
      {{#each endpoints}}
      @router.{{method}}("{{path}}")
      async def {{operationId}}(
          {{#each parameters}}
          {{name}}: {{paramType}}{{#if required}}{{else}} = None{{/if}},
          {{/each}}
      ) -> {{returnType}}:
          """{{description}}"""
          {{#if hasValidation}}
          # 参数验证
          {{validationCode}}
          {{/if}}
          # TODO: 实现业务逻辑
          raise HTTPException(status_code=501, detail="Not implemented")
          
      {{/each}}
      
  requestModel:
    template: |
      class {{requestName}}(BaseModel):
          {{#each properties}}
          {{name}}: {{#if required}}{{pythonType}}{{else}}Optional[{{pythonType}}] = None{{/if}}
          {{#if description}}
          """{{description}}"""
          {{/if}}
          {{/each}}
          
  responseModel:
    template: |
      class {{responseName}}(BaseModel):
          code: int = 0
          message: str = "success"
          data: {{#if dataProperties}}{{dataType}}{{else}}None{{/if}}
          
      class {{errorResponseName}}(BaseModel):
          code: int
          message: str
          details: Optional[dict] = None
```

## Express 映射规则

```yaml
interfaceToExpress:
  router:
    template: |
      import { Router, Request, Response, NextFunction } from 'express';
      import { validateRequest } from '../middleware';
      import * as {{controllerName}} from '../controllers/{{controllerFile}}';
      
      const router = Router();
      
      {{#each endpoints}}
      router.{{method}}('{{path}}', 
        {{#each middleware}}
        {{name}},
        {{/each}}
        {{controllerName}}.{{handlerName}}
      );
      
      {{/each}}
      
      export default router;
      
  controller:
    template: |
      import { Request, Response, NextFunction } from 'express';
      import { {{serviceName}} } from '../services/{{serviceFile}}';
      
      export const {{handlerName}} = async (req: Request, res: Response, next: NextFunction) => {
        try {
          {{#if hasPathParams}}
          const { {{pathParams}} } = req.params;
          {{/if}}
          {{#if hasQueryParams}}
          const { {{queryParams}} } = req.query;
          {{/if}}
          {{#if hasBody}}
          const body = req.body;
          {{/if}}
          
          const result = await {{serviceName}}.{{methodName}}({{args}});
          
          res.json({ code: 0, message: 'success', data: result });
        } catch (error) {
          next(error);
        }
      };
```

### 业务规则到代码映射

```yaml
ruleToCode:
  calculationRule:
    template: |
      def {{ruleName}}({{#each inputs}}{{name}}: {{type}}{{#unless @last}}, {{/unless}}{{/each}}) -> {{returnType}}:
          """
          {{description}}
          
          规则ID: {{ruleId}}
          版本: {{version}}
          """
          {{#each conditions}}
          # {{name}}: {{expression}}
          {{variableName}} = {{pythonExpression}}
          {{/each}}
          
          {{#each actions}}
          {{#if condition}}
          if {{condition}}:
              {{variableName}} = {{formula}}
          {{else}}
          {{variableName}} = {{formula}}
          {{/if}}
          {{/each}}
          
          return {{outputVariable}}
          
  validationRule:
    template: |
      def validate_{{ruleName}}(data: dict) -> ValidationResult:
          """
          {{description}}
          
          规则ID: {{ruleId}}
          """
          errors = []
          
          {{#each conditions}}
          if not ({{expression}}):
              errors.append(ValidationError(
                  field="{{field}}",
                  message="{{errorMessage}}",
                  rule_id="{{ruleId}}"
              ))
          {{/each}}
          
          return ValidationResult(
              valid=len(errors) == 0,
              errors=errors
          )
          
  stateTransitionRule:
    template: |
      class {{entityName}}StateMachine:
          """
          {{entityName}} 状态机
          
          规则ID: {{ruleId}}
          """
          
          ALLOWED_TRANSITIONS = {
              {{#each transitions}}
              '{{currentState}}': [{{#each allowedNext}}'{{this}}'{{#unless @last}}, {{/unless}}{{/each}}],
              {{/each}}
          }
          
          @classmethod
          def can_transition(cls, current_state: str, target_state: str) -> bool:
              return target_state in cls.ALLOWED_TRANSITIONS.get(current_state, [])
              
          @classmethod
          def transition(cls, entity: {{entityName}}, target_state: str) -> {{entityName}}:
              if not cls.can_transition(entity.status, target_state):
                  raise InvalidStateTransitionError(
                      f"Cannot transition from {entity.status} to {target_state}"
                  )
              entity.status = target_state
              return entity
```

## 约束到验证器映射

```yaml
constraintToValidator:
  pythonValidator:
    template: |
      from pydantic import validator, root_validator
      from typing import List
      
      class {{entityName}}Validator:
          {{#each constraints}}
          @validator('{{field}}')
          def validate_{{constraintName}}(cls, v):
              {{#if pattern}}
              import re
              if not re.match(r'{{pattern}}', v):
                  raise ValueError('{{errorMessage}}')
              {{/if}}
              {{#if range}}
              if not ({{min}} <= v <= {{max}}):
                  raise ValueError('{{errorMessage}}')
              {{/if}}
              {{#if enum}}
              if v not in {{enumValues}}:
                  raise ValueError('{{errorMessage}}')
              {{/if}}
              return v
              
          {{/each}}
          
  typescriptValidator:
    template: |
      import { z } from 'zod';
      
      export const {{entityName}}Schema = z.object({
        {{#each attributes}}
        {{name}}: {{baseSchema}}
          {{#each constraints}}
          .{{constraintMethod}}({{constraintParams}})
          {{/each}},
        {{/each}}
      });
      
      export type {{entityName}} = z.infer<typeof {{entityName}}Schema>;
      
  constraintMapping:
    required:
      python: "v is not None"
      typescript: ".min(1)"
      zod: ""
    minLength:
      python: "len(v) >= {{value}}"
      typescript: ".min({{value}})"
      zod: ".min({{value}})"
    maxLength:
      python: "len(v) <= {{value}}"
      typescript: ".max({{value}})"
      zod: ".max({{value}})"
    pattern:
      python: "re.match(r'{{value}}', v)"
      typescript: ".regex(/{{value}}/)"
      zod: ".regex(/{{value}}/)"
    minimum:
      python: "v >= {{value}}"
      typescript: ".min({{value}})"
      zod: ".min({{value}})"
    maximum:
      python: "v <= {{value}}"
      typescript: ".max({{value}})"
      zod: ".max({{value}})"
    email:
      python: "re.match(r'^[\\w.-]+@[\\w.-]+\\.\\w+$', v)"
      typescript: ".isEmail()"
      zod: ".email()"
```

## 规范一致性检查

### 一致性检查框架

```
一致性检查框架
├── 内部一致性
│   ├── 规范内部完整性
│   ├── 引用完整性
│   └── 约束一致性
├── 跨规范一致性
│   ├── 类型定义一致性
│   ├── 接口契约一致性
│   └── 命名一致性
├── 规范与代码一致性
│   ├── 结构一致性
│   ├── 行为一致性
│   └── 约束一致性
└── 规范与文档一致性
    ├── 描述一致性
    ├── 示例一致性
    └── 版本一致性
```

### 内部一致性检查

```yaml
internalConsistencyChecks:
  referenceIntegrity:
    - id: REF_001
      name: "实体引用完整性"
      description: "检查实体关系引用的目标实体是否存在"
      check: |
        for entity in spec.entities:
          for relation in entity.relationships:
            if relation.target not in spec.entities:
              error(f"实体 {entity.name} 引用了不存在的实体 {relation.target}")
      severity: error
      
    - id: REF_002
      name: "类型引用完整性"
      description: "检查属性类型引用是否有效"
      check: |
        for entity in spec.entities:
          for attr in entity.attributes:
            if isCustomType(attr.type) and attr.type not in definedTypes:
              error(f"属性 {entity.name}.{attr.name} 引用了未定义的类型 {attr.type}")
      severity: error
      
    - id: REF_003
      name: "枚举值引用完整性"
      description: "检查枚举类型是否有值定义"
      check: |
        for attr in attributes where attr.type == 'enum':
          if not attr.enumValues and not attr.enumType:
            error(f"枚举属性 {attr.name} 缺少值定义")
      severity: warning
      
  constraintConsistency:
    - id: CONS_001
      name: "约束冲突检测"
      description: "检测相互冲突的约束"
      check: |
        for entity in spec.entities:
          for attr in entity.attributes:
            if attr.required and attr.default is not None:
              warning(f"属性 {attr.name} 同时设置了必填和默认值")
            if attr.minLength and attr.maxLength and attr.minLength > attr.maxLength:
              error(f"属性 {attr.name} 最小长度大于最大长度")
      severity: warning
      
    - id: CONS_002
      name: "约束冗余检测"
      description: "检测冗余的约束定义"
      check: |
        for attr in attributes:
          constraints = getConstraints(attr)
          if hasRedundantConstraints(constraints):
            warning(f"属性 {attr.name} 存在冗余约束")
      severity: info
      
  logicConsistency:
    - id: LOGIC_001
      name: "业务规则逻辑一致性"
      description: "检查业务规则的条件和动作是否一致"
      check: |
        for rule in spec.rules:
          for condition in rule.conditions:
            if not isValidExpression(condition.expression):
              error(f"规则 {rule.name} 的条件表达式无效: {condition.expression}")
          for action in rule.actions:
            if action.type == 'calculation' and not isValidFormula(action.formula):
              error(f"规则 {rule.name} 的计算公式无效: {action.formula}")
      severity: error
```

### 跨规范一致性检查

```yaml
crossSpecConsistencyChecks:
  typeDefinitionConsistency:
    - id: TYPE_001
      name: "共享类型一致性"
      description: "检查同一类型在不同规范中的定义是否一致"
      check: |
        sharedTypes = loadSharedTypes()
        for spec in allSpecs:
          for typeDef in spec.customTypes:
            if typeDef.name in sharedTypes:
              if not typesEqual(typeDef, sharedTypes[typeDef.name]):
                error(f"类型 {typeDef.name} 在规范 {spec.name} 中与共享定义不一致")
      severity: warning
      
    - id: TYPE_002
      name: "枚举值一致性"
      description: "检查枚举类型在不同规范中的值是否一致"
      check: |
        enumDefinitions = collectEnumDefinitions()
        for enumName, definitions in enumDefinitions:
          if len(set(map(str, definitions))) > 1:
            error(f"枚举 {enumName} 在不同规范中定义不一致")
      severity: error
      
  interfaceContractConsistency:
    - id: API_001
      name: "接口路径唯一性"
      description: "检查接口路径是否唯一"
      check: |
        endpoints = collectAllEndpoints()
        seen = {}
        for endpoint in endpoints:
          key = f"{endpoint.method} {endpoint.path}"
          if key in seen:
            error(f"接口路径重复: {key} 定义在 {seen[key]} 和 {endpoint.source}")
          seen[key] = endpoint.source
      severity: error
      
    - id: API_002
      name: "请求响应类型一致性"
      description: "检查接口请求和响应类型定义是否与实体定义一致"
      check: |
        for endpoint in endpoints:
          if endpoint.requestType:
            if not typeMatchesEntity(endpoint.requestType, entities):
              warning(f"接口 {endpoint.name} 的请求类型与实体定义不一致")
          if endpoint.responseType:
            if not typeMatchesEntity(endpoint.responseType, entities):
              warning(f"接口 {endpoint.name} 的响应类型与实体定义不一致")
      severity: warning
      
  namingConsistency:
    - id: NAME_001
      name: "命名风格一致性"
      description: "检查命名是否符合项目约定"
      check: |
        namingConventions = {
          'entity': 'PascalCase',
          'attribute': 'camelCase',
          'table': 'snake_case',
          'api': 'kebab-case'
        }
        for entity in entities:
          if not matchesConvention(entity.name, namingConventions['entity']):
            warning(f"实体名称 {entity.name} 不符合 PascalCase 约定")
      severity: warning
      
    - id: NAME_002
      name: "命名冲突检测"
      description: "检测不同规范中的命名冲突"
      check: |
        names = {}
        for spec in allSpecs:
          for entity in spec.entities:
            fullName = f"{spec.namespace}.{entity.name}"
            if fullName in names:
              error(f"命名冲突: {fullName} 定义在 {names[fullName]} 和 {spec.name}")
            names[fullName] = spec.name
      severity: error
```

### 规范与代码一致性检查

```yaml
specCodeConsistencyChecks:
  structuralConsistency:
    - id: STRUCT_001
      name: "实体结构一致性"
      description: "检查代码实体与规范定义的结构是否一致"
      check: |
        for entity in spec.entities:
          codeEntity = findCodeEntity(entity.name)
          if not codeEntity:
            error(f"实体 {entity.name} 在代码中不存在")
            continue
            
          specAttrs = set(a.name for a in entity.attributes)
          codeAttrs = set(a.name for a in codeEntity.attributes)
          
          missing = specAttrs - codeAttrs
          extra = codeAttrs - specAttrs
          
          if missing:
            error(f"实体 {entity.name} 缺少属性: {missing}")
          if extra:
            warning(f"实体 {entity.name} 有额外属性: {extra}")
      severity: error
      
    - id: STRUCT_002
      name: "类型一致性"
      description: "检查代码中的类型与规范定义是否一致"
      check: |
        for entity in spec.entities:
          codeEntity = findCodeEntity(entity.name)
          if not codeEntity:
            continue
            
          for attr in entity.attributes:
            codeAttr = findAttribute(codeEntity, attr.name)
            if codeAttr and not typesCompatible(attr.type, codeAttr.type):
              error(f"属性 {entity.name}.{attr.name} 类型不一致: 规范={attr.type}, 代码={codeAttr.type}")
      severity: error
      
  behavioralConsistency:
    - id: BEHAV_001
      name: "接口行为一致性"
      description: "检查代码实现的接口行为与规范定义是否一致"
      check: |
        for endpoint in spec.endpoints:
          codeEndpoint = findCodeEndpoint(endpoint.path, endpoint.method)
          if not codeEndpoint:
            error(f"接口 {endpoint.method} {endpoint.path} 在代码中不存在")
            continue
            
          # 检查参数
          for param in endpoint.parameters:
            if not hasParameter(codeEndpoint, param.name):
              error(f"接口 {endpoint.path} 缺少参数 {param.name}")
              
          # 检查返回值
          if not returnTypesMatch(endpoint.response, codeEndpoint.returnType):
            warning(f"接口 {endpoint.path} 返回类型与规范不一致")
      severity: error
      
    - id: BEHAV_002
      name: "业务规则实现一致性"
      description: "检查业务规则的实现与规范定义是否一致"
      check: |
        for rule in spec.rules:
          codeRule = findCodeRule(rule.name)
          if not codeRule:
            warning(f"业务规则 {rule.name} 在代码中未找到实现")
            continue
            
          # 检查条件
          for condition in rule.conditions:
            if not conditionImplemented(codeRule, condition):
              error(f"规则 {rule.name} 的条件 {condition.name} 未实现")
              
          # 检查动作
          for action in rule.actions:
            if not actionImplemented(codeRule, action):
              error(f"规则 {rule.name} 的动作 {action.name} 未实现")
      severity: warning
      
  constraintConsistency:
    - id: CONSTRAINT_001
      name: "验证约束一致性"
      description: "检查代码中的验证逻辑与规范约束是否一致"
      check: |
        for entity in spec.entities:
          for constraint in entity.constraints:
            codeValidator = findValidator(entity.name, constraint.field)
            if not codeValidator:
              warning(f"实体 {entity.name} 的约束 {constraint.name} 未在代码中实现")
            elif not validatorMatchesConstraint(codeValidator, constraint):
              error(f"实体 {entity.name} 的约束 {constraint.name} 实现与规范不一致")
      severity: warning
```

## 一致性检查报告

```yaml
consistencyReport:
  reportFormat:
    summary:
      totalChecks: number
      passed: number
      warnings: number
      errors: number
      coverage: number
      
    details:
      - category: string
        checks:
          - id: string
            name: string
            status: passed | failed | warning | skipped
            message: string
            location:
              spec: string
              code: string
              line: number
            suggestion: string
            severity: error | warning | info
            
    recommendations:
      - priority: high | medium | low
        description: string
        affectedSpecs: string[]
        affectedCode: string[]
        
  reportExample:
    summary:
      totalChecks: 45
      passed: 38
      warnings: 5
      errors: 2
      coverage: 84.4%
      
    details:
      - category: "内部一致性"
        checks:
          - id: REF_001
            name: "实体引用完整性"
            status: passed
          - id: CONS_001
            name: "约束冲突检测"
            status: warning
            message: "属性 User.password 同时设置了必填和默认值"
            location:
              spec: "auth/User.entity.spec.yaml"
              line: 25
            suggestion: "移除默认值或取消必填约束"
            
      - category: "规范与代码一致性"
        checks:
          - id: STRUCT_001
            name: "实体结构一致性"
            status: failed
            message: "实体 Order 在代码中缺少属性: discountAmount"
            location:
              spec: "order/Order.entity.spec.yaml"
              code: "backend/models/order.py"
            suggestion: "在代码中添加 discountAmount 属性"
            
    recommendations:
      - priority: high
        description: "修复 Order 实体结构不一致问题"
        affectedSpecs: ["order/Order.entity.spec.yaml"]
        affectedCode: ["backend/models/order.py"]
      - priority: medium
        description: "统一 User 实体的密码约束定义"
        affectedSpecs: ["auth/User.entity.spec.yaml"]
```

### 一致性修复建议

```yaml
consistencyFixSuggestions:
  autoFixable:
    - type: "缺少属性"
      action: "自动添加属性到代码"
      requires: "确认属性类型和约束"
      
    - type: "命名不一致"
      action: "自动重命名"
      requires: "确认重命名影响范围"
      
    - type: "缺少验证器"
      action: "自动生成验证器"
      requires: "确认验证逻辑"
      
  manualFixRequired:
    - type: "类型不一致"
      action: "需要手动确认正确的类型"
      reason: "可能涉及数据迁移"
      
    - type: "业务规则不一致"
      action: "需要手动审查业务逻辑"
      reason: "可能影响业务功能"
      
    - type: "接口行为不一致"
      action: "需要手动确认接口契约"
      reason: "可能影响客户端调用"
```
