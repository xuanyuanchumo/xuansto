---
name: documentation-si
parent: universal-devops
department: libu2
province: shangshusheng
description: |
  文档司 - 礼部·祠部司

  【职责】API文档、技术文档、用户手册生成与维护

  【触发条件】
  - 需要生成或更新API文档
  - 技术文档编写和维护
  - 用户手册和帮助文档

  【能力】
  - 自动化API文档生成
  - 技术文档模板化
  - 多格式输出支持
  - 版本化管理
---

# 文档司 (Documentation Si)

> 尚书省 · 礼部 · Universal DevOps v4.0

**状态**: 占位符 - 具体内容由后续任务填充

## 🤖 自主化操作指南 (v7.0)

### 推荐操作模式
| 操作场景 | 推荐模式 | 置信度 | 说明 |
|---------|---------|--------|------|
| API文档自动生成 | SCRIPTED_BATCH | 96% | Swagger/OpenAPI注解驱动，高度自动化 |
| 技术文档编写 | HYBRID_ASSISTED | 84% | AI辅助生成初稿 + 人工审核完善 |
| 文档格式转换 | SCRIPTED_BATCH | 97% | Pandoc/Asciidoctor工具链标准化 |
| 文档架构设计 | AUTONOMOUS_MANUAL | 73% | 需要理解受众和信息架构 |

### 常用工具组合
- **读操作**: Read, SearchCodebase, Grep（读取源码注解、现有文档、API定义）
- **写操作**: Write, SearchReplace（生成文档、更新示例代码）
- **批量操作**: Swagger/JSDoc解析器、MkDocs/GitBook构建脚本、文档部署流水线
- **验证操作**: 文档链接检查器(dead link detector)、API mock测试、可访问性检查

### 注意事项
- ⚠️ 文档必须与代码同步更新：代码变更时必须触发文档review，避免"文档滞后"
- ⚠️ 避免过度文档化：不是所有代码都需要详细文档，关注公共接口和复杂逻辑即可
- ✅ 采用"文档即代码"(Docs as Code)理念：文档纳入版本控制，与代码同等对待
- ✅ 建立文档质量门禁：PR必须包含相关文档更新或明确标注"无需更新"理由

## 🔗 资源协调要点 (v7.0)

### 常访问资源
| 资源类型 | 典型路径 | 锁策略建议 |
|---------|---------|-----------|
| FILE | /docs/ /README.md | SHARED (读) / EXCLUSIVE (写) |
| SOURCE | 源码中的注释和docstring | SHARED (读) |
| API | 文档托管平台(GitHub Pages/Vercel) | DEPLOYMENT_PIPELINE |
| SEARCH | 全文搜索索引(Elasticsearch/Algolia) | READ_ONLY |
| VERSION | 文档版本号（对应产品版本） | SEMANTIC_VERSIONING |

### 竞争规避策略
1. **文档分支策略**: 采用docs/目录与代码同仓库管理，避免文档仓库与代码仓库分离导致脱节
2. **自动化同步机制**: CI阶段自动检测代码变更是否需要文档更新，发送提醒给作者
3. **文档review轻量化**: 文档PR采用快速通道，聚焦准确性和完整性而非风格问题

## 💡 开源哲学应用 (v7.0)

### OpenCode 透明化
- 文档贡献过程透明：谁编写了什么内容、何时更新、基于什么反馈都清晰可见
- 文档质量指标公开：文档覆盖率、链接有效性、用户满意度等指标dashboard展示
- 贡献者认可体系：文档贡献者的工作被记录和认可，鼓励持续参与

### OpenClaude 编排
- 智能文档推荐：根据用户角色和当前上下文，推荐最相关的文档片段
- 过期文档检测：自动识别长时间未更新的文档并标记为"可能过时"
- 多语言自动翻译：核心文档支持多语言版本，降低国际化门槛

### Claw-Code 契约驱动
- API文档契约驱动：OpenAPI/Swagger规范作为前后端协作的单一事实来源
- 文档覆盖率要求：公共API必须有100%的文档覆盖，否则阻止发布
- 文档 freshness SLA：定义文档的最大允许陈旧时间（如90天未更新则标记warning）
