---
id: documentation-standards
type: knowledge
category: standards
tags: [文档规范, README, CHANGELOG, API文档, 代码注释]
version: 1.0.0
created: 2026-04-28
updated: 2026-04-28
confidence: high
---

# 文档编写规范

## README 规范

README 是项目门面，必须包含以下结构：

1. **项目名称与简介**：一句话说明项目用途
2. **快速开始**：安装 → 配置 → 运行的最小步骤
3. **使用示例**：核心功能的代码示例
4. **配置说明**：环境变量、配置项及其默认值
5. **开发指南**：构建、测试、贡献流程
6. **许可证**：开源协议声明

## CHANGELOG 规范

遵循 [Keep a Changelog](https://keepachangelog.com) 格式：

```markdown
## [1.2.0] - 2026-04-28
### Added - 新增功能
### Changed - 功能变更
### Deprecated - 即将移除
### Removed - 已移除
### Fixed - 问题修复
### Security - 安全相关
```

版本号遵循 Semantic Versioning：MAJOR.MINOR.PATCH。

## API 文档规范

- 每个公开接口必须包含：描述、参数（名称/类型/必填/默认值/说明）、返回值、异常、示例
- 使用 OpenAPI/Swagger 规范描述 REST API
- GraphQL Schema 自描述，补充业务语义注释
- gRPC 使用 proto 文件注释生成文档

## 代码注释规范

| 类型 | 用途 | 示例 |
|------|------|------|
| 文件头 | 模块职责说明 | 简述文件职责和关键依赖 |
| 函数注释 | 契约说明 | JSDoc/TSDoc/Docstring |
| 行内注释 | Why 而非 What | 解释决策原因而非代码行为 |
| TODO | 待办标记 | `// TODO(username): 描述` |
| FIXME | 已知缺陷 | `// FIXME: 临时方案，需重构` |

## 原则

- 代码即文档：命名清晰时减少注释需求
- 注释说明意图（Why），代码表达行为（What）
- 过时注释比无注释更危险，修改代码时同步更新注释
- 公开 API 文档覆盖率 100%，内部实现按需注释
