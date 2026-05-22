# 测试模式记录

本目录用于存储测试设计模式的记录，包括测试策略、测试组织、Mock模式、数据构建模式等。

## 记录格式

```json
{
  "id": "PAT-TS-YYYYMMDD-NNN",
  "timestamp": "ISO8601时间戳",
  "patternName": "模式名称",
  "patternType": "策略型|组织型|隔离型|数据型|断言型",
  "description": "模式描述",
  "problem": "解决的问题",
  "solution": "解决方案",
  "applicableScenario": "适用场景",
  "examples": ["代码示例或伪代码"],
  "advantages": ["优势列表"],
  "disadvantages": ["劣势列表"],
  "bestPractices": ["最佳实践"],
  "references": ["参考来源"]
}
```

## 示例记录

```json
{
  "id": "PAT-TS-20260428-001",
  "timestamp": "2026-04-28T14:00:00.000Z",
  "patternName": "测试数据构建器(Test Data Builder)",
  "patternType": "数据型",
  "description": "通过Builder模式创建测试数据对象，提供流畅的API和合理的默认值",
  "problem": "测试数据构造冗长重复，不同测试用例间数据构建代码大量重复",
  "solution": "为每个领域对象创建Builder类，提供链式调用API和合理默认值，仅覆盖测试关注的字段",
  "applicableScenario": "需要构造复杂领域对象的单元测试和集成测试",
  "examples": ["const order = OrderBuilder.create().withStatus('PAID').withAmount(99.9).build()"],
  "advantages": ["测试代码简洁可读", "默认值减少样板代码", "数据修改影响范围小"],
  "disadvantages": ["需要维护Builder类", "对象字段变更需同步更新Builder"],
  "bestPractices": ["为必填字段提供合理默认值", "Builder方法命名使用with前缀", "与Mother模式结合使用"],
  "references": ["Test Data Builder - Nat Pryce"]
}
```
