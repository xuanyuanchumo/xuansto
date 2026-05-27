# API设计模式记录

本目录用于存储API设计模式的记录，包括RESTful设计、GraphQL模式、版本策略、分页模式、过滤排序等。

## 记录格式

```json
{
  "id": "PAT-AP-YYYYMMDD-NNN",
  "timestamp": "ISO8601时间戳",
  "patternName": "模式名称",
  "patternType": "资源设计|版本管理|分页|过滤排序|错误响应|认证授权|幂等性",
  "description": "模式描述",
  "problem": "解决的问题",
  "solution": "解决方案",
  "applicableScenario": "适用场景",
  "interface": "接口定义示例",
  "requestExample": "请求示例",
  "responseExample": "响应示例",
  "advantages": ["优势列表"],
  "disadvantages": ["劣势列表"],
  "references": ["参考来源"]
}
```

## 示例记录

```json
{
  "id": "PAT-AP-20260428-001",
  "timestamp": "2026-04-28T16:00:00.000Z",
  "patternName": "游标分页(Cursor-based Pagination)",
  "patternType": "分页",
  "description": "使用游标而非偏移量进行分页，基于唯一有序字段定位数据起始点",
  "problem": "偏移分页在大数据集下性能差，且数据变更时出现跳过或重复",
  "solution": "返回游标(通常为加密的排序字段值)，客户端下次请求携带游标获取后续数据",
  "applicableScenario": "大数据集列表查询、实时数据流、无限滚动场景",
  "interface": "GET /api/v1/orders?cursor=eyJpZCI6MTAwfQ&limit=20",
  "requestExample": "GET /api/v1/orders?cursor=eyJpZCI6MTAwfQ&limit=20",
  "responseExample": "{\"data\":[...],\"pagination\":{\"nextCursor\":\"eyJpZCI6MTIwfQ\",\"hasMore\":true}}",
  "advantages": ["大数据集性能稳定", "数据变更不丢不重", "支持无限滚动"],
  "disadvantages": ["不支持跳页", "游标需加密防止篡改", "实现较偏移分页复杂"],
  "references": ["Stripe API Pagination", "Relay Cursor Connections Spec"]
}
```
