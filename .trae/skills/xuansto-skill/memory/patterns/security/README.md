# 安全模式记录

本目录用于存储安全设计模式的记录，包括认证授权、数据加密、输入校验、审计日志、防重放攻击等。

## 记录格式

```json
{
  "id": "PAT-SE-YYYYMMDD-NNN",
  "timestamp": "ISO8601时间戳",
  "patternName": "模式名称",
  "patternType": "认证|授权|加密|校验|审计|防重放|防注入|脱敏",
  "description": "模式描述",
  "problem": "解决的安全问题",
  "solution": "解决方案",
  "threatModel": "威胁模型",
  "applicableScenario": "适用场景",
  "implementation": "实现要点",
  "examples": ["代码示例或伪代码"],
  "advantages": ["优势列表"],
  "disadvantages": ["劣势列表"],
  "compliance": "相关合规要求",
  "references": ["参考来源"]
}
```

## 示例记录

```json
{
  "id": "PAT-SE-20260428-001",
  "timestamp": "2026-04-28T17:00:00.000Z",
  "patternName": "请求签名防篡改(HMAC签名)",
  "patternType": "防重放",
  "description": "对API请求使用HMAC算法生成签名，服务端验证签名确保请求未被篡改和伪造",
  "problem": "API请求可能被中间人截获篡改，或被恶意重放攻击",
  "solution": "客户端使用共享密钥对请求关键要素(时间戳+路径+参数)生成HMAC签名，服务端验证签名和时效性",
  "threatModel": "中间人攻击、请求篡改、重放攻击",
  "applicableScenario": "开放API、第三方集成、敏感操作接口",
  "implementation": "签名要素：HTTP方法+路径+时间戳+请求体哈希，密钥通过安全通道分发，时间戳5分钟有效期",
  "examples": ["Authorization: HMAC-SHA256 Credential=ak-xxx, Timestamp=20260428T170000Z, Signature=xxxx"],
  "advantages": ["防止请求篡改", "防止重放攻击", "无需传输密钥本身"],
  "disadvantages": ["密钥管理复杂", "客户端和服务端时间需同步", "增加请求开销"],
  "compliance": "OWASP API Security Top 10, PCI DSS",
  "references": ["AWS Signature V4", "RFC 2104 - HMAC"]
}
```
