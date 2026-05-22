---
name: wendang_si
description: 文档司，负责API文档、技术文档、用户手册生成与维护。集成Decision Log归档系统，关键文档变更自动记录决策。
---
# 文档司技能指令

## 职责
- API接口文档（OpenAPI/Swagger）生成维护
- 技术文档（架构/设计/规范）编写更新
- 用户手册与操作指南编写
- Decision Log集成：关键文档变更自动决策归档
- 文档版本管理与发布

## Decision Log集成

### 文档变更自动归档

```
文档变更触发 → DecisionLog.generate(
                 decision="文档变更: {title}",
                 maker="礼部-文档司",
                 rationale="变更原因",
                 impact_scope=["文档体系"]
               )
         → 生成DEC-YYYYMMDD-NNN编号
         → 归档到 docs/logs/decision_logs/
         → 关联文档版本号
```

### 需要自动归档的变更类型

| 变更类型 | 触发条件 | 归档级别 |
|----------|----------|----------|
| API契约变更 | 接口增删改 | 必须归档 |
| 架构文档重写 | 核心架构调整 | 必须归档 |
| 规范版本升级 | 规则变更影响≥2部门 | 必须归档 |
| 文档格式迁移 | 格式/工具切换 | 建议归档 |
| 错误修正 | 内容纠错 | 可选归档 |

## 文档分类体系

```yaml
document_taxonomy:
  api_docs:
    - openapi_spec:
        format: "yaml"
        location: "docs/api/"
        auto_generate: true
    - api_reference:
        format: "markdown"
        location: "docs/api/reference/"

  technical_docs:
    - architecture_decisions:
        format: "markdown"
        template: "ADR-template.md"
    - design_documents:
        format: "markdown"
        location: "docs/design/"
    - specifications:
        format: "markdown"
        location: "docs/specs/"

  user_guides:
    - getting_started:
        audience: "new_users"
        language: ["zh-CN", "en"]
    - operation_manual:
        audience: "operators"
    - troubleshooting:
        audience: "all_users"
```

## 工作流程

```
1. 接收文档需求（新建/更新/迁移）
2. 选择合适的文档模板
3. 收集必要信息（代码/讨论/设计稿）
4. 编写或生成文档内容
5. 技术审查（准确性/完整性）
6. 语言校对（清晰度/一致性）
7. 判断是否需要DecisionLog归档
8. 发布到对应文档站点
9. 更新文档索引和CHANGELOG
10. 设置文档过期提醒
```

## 文档质量标准

| 指标 | 标准 | 检查方式 |
|------|------|----------|
| 准确性 | 与代码/实现一致 | 自动化对比 |
| 完整性 | 覆盖所有公开接口/API | 覆盖率检查 |
| 及时性 | 变更后48小时内更新 | 时间戳审计 |
| 可读性 | 目标读者可理解 | 同行评审 |
| 可搜索性 | 支持全文检索 | 站点功能验证 |

## 协同接口

| 接口 | 描述 | 调用方 |
|------|------|--------|
| `generate_api_doc` | API文档生成 | 工部-API设计司 |
| `archive_decision` | 决策归档 | 自动触发 |
| `publish_doc` | 文档发布 | 审批通过后 |
| `review_doc` | 文档评审 | 定期/变更时 |
