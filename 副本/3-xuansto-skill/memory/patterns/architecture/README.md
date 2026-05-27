# 架构模式记录

本目录用于存储项目架构设计模式的记录，包括分层架构、微服务、事件驱动、CQRS、六边形架构等。

## 记录格式

```json
{
  "id": "PAT-AR-YYYYMMDD-NNN",
  "timestamp": "ISO8601时间戳",
  "patternName": "模式名称",
  "patternType": "结构型|行为型|分布式|数据型",
  "description": "模式描述",
  "problem": "解决的问题",
  "solution": "解决方案",
  "structure": "架构结构描述",
  "applicableScenario": "适用场景",
  "advantages": ["优势列表"],
  "disadvantages": ["劣势列表"],
  "implementation": "实现要点",
  "relatedPatterns": ["关联模式"],
  "references": ["参考来源"]
}
```

## 示例记录

```json
{
  "id": "PAT-AR-20260428-001",
  "timestamp": "2026-04-28T11:00:00.000Z",
  "patternName": "六边形架构(端口与适配器)",
  "patternType": "结构型",
  "description": "将应用核心逻辑与外部依赖隔离，通过端口定义交互契约，适配器实现具体技术细节",
  "problem": "业务逻辑与框架、数据库、消息队列等基础设施强耦合，难以测试和替换",
  "solution": "核心域通过端口(Port)定义输入输出接口，适配器(Adapter)实现具体技术对接",
  "structure": "核心域 -> 端口(接口) <- 适配器(实现)",
  "applicableScenario": "需要保持业务逻辑独立性的中大型应用，特别是需要支持多种外部系统集成时",
  "advantages": ["业务逻辑可独立测试", "技术实现可替换", "关注点分离"],
  "disadvantages": ["接口数量增多", "初期开发成本较高"],
  "implementation": "定义入站端口(DrivingPort)和出站端口(DrivenPort)，分别在应用服务和基础设施层实现",
  "relatedPatterns": ["DDD", "整洁架构", "CQRS"],
  "references": ["Alistair Cockburn - Hexagonal Architecture"]
}
```
