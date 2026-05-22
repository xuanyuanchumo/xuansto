---
name: api-design-si
parent: universal-devops
department: gongbu
province: shangshusheng
description: |
  API设计司 - 工部·工部司

  【职责】RESTful API设计、接口契约、版本管理、OpenAPI规范

  【触发条件】
  - RESTful API接口设计
  - OpenAPI/Swagger规范编写
  - API版本管理策略

  【能力】
  - RESTful最佳实践
  - OpenAPI Spec生成
  - 接口版本控制
  - API文档自动化
---

# API设计司 (API Design Si)

> 尚书省 · 工部 · Universal DevOps v4.0

**状态**: 占位符 - 具体内容由后续任务填充

## 🤖 自主化操作指南 (v7.0)

### 推荐操作模式
| 操作场景 | 推荐模式 | 置信度 | 说明 |
|---------|---------|--------|------|
| OpenAPI规范编写 | SCRIPTED_BATCH | 93% | YAML/JSON结构化，高度标准化 |
| API接口设计 | HYBRID_ASSISTED | 85% | AI辅助设计 + 人工审核业务合理性 |
| API版本管理 | SCRIPTED_BATCH | 96% | URL/Header版本策略模板化 |
| 接口契约测试生成 | SCRIPTED_BATCH | 94% | 基于OpenAPI Spec自动生成 |

### 常用工具组合
- **读操作**: Read, SearchCodebase, Grep（读取现有API定义、数据模型、业务规则）
- **写操作**: Write, SearchReplace（编写OpenAPI YAML、生成接口文档）
- **批量操作**: Swagger Codegen、OpenAPI Generator、Postman Collection生成
- **验证操作**: OpenAPI Linter(Spectral)、契约测试(Pact/Dredd)、Mock Server自动搭建

### 注意事项
- ⚠️ API设计先行：先定义接口契约再实现后端，避免"接口跟着代码走"
- ⚠️ 版本兼容性必须考虑：新版本不能破坏旧客户端，提供足够的deprecation周期
- ✅ 遵循RESTful最佳实践：正确的HTTP动词、状态码、资源命名（名词复数）
- ✅ 建立API Design Review机制：核心API变更需要多方review（前端+后端+安全）

## 🔗 资源协调要点 (v7.0)

### 常访问资源
| 资源类型 | 典型路径 | 锁策略建议 |
|---------|---------|-----------|
| FILE | /openapi/ /api-specs/ | VERSION_CONTROLLED (Git管理) |
| REGISTRY | API网关配置(Kong/Apisix) | SHARED (读) / EXCLUSIVE (修改) |
| DOCUMENT | API文档平台(Swagger Hub/Stoplight) | DEPLOYMENT_PIPELINE |
| MOCK | Mock Server(Prism/MSW) | AUTO_GENERATED |
| CLIENT | SDK生成输出目录 | AUTO_GENERATED |

### 竞争规避策略
1. **API Namespace隔离**: 不同团队/模块使用不同的URL前缀(/api/v1/users, /api/v1/orders)，避免冲突
2. **变更审批流程**: Breaking Change必须经过API Governance委员会审批，防止随意破坏兼容性
3. **灰度发布能力**: 新版API支持按比例灰度（如先10%流量），快速回滚能力

## 💡 开源哲学应用 (v7.0)

### OpenCode 透明化
- API规范完全开源：所有API的OpenAPI定义对前后端团队公开，作为协作的单一事实来源
- 变更日志透明化：每次API版本的变更内容、breaking changes、migration guide清晰记录
- 设计决策理由公开：为什么选择这种设计风格、权衡了哪些因素，都有文档说明

### OpenClaude 编排
- 智能API设计推荐：根据业务需求描述自动生成符合RESTful规范的初始API设计
- 向后兼容性分析：自动检测API变更是否会破坏现有客户端，给出风险评估
- 自动化SDK生成：基于OpenAPI Spec自动生成多语言SDK(TypeScript/Python/Java等)，保持同步

### Claw-Code 契约驱动
- 契约优先开发(Contract-First): OpenAPI Spec作为前后端协作的法律文书，双方共同遵守
- 自动化契约测试：Consumer-driven Contract Testing确保实现与规范一致
- API SLA量化定义：响应时间P99<200ms、可用性99.9%等服务等级协议写入spec并监控
