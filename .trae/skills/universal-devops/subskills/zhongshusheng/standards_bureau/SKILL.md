---
name: standards-bureau
parent: universal-devops
province: zhongshusheng
description: |
  规范制定局 - 中书省标准化管理单元

  【职责】编码规范制定、文档标准、流程规范、命名约定、Lint规则配置

  【触发条件】
  - 项目初始化需要建立编码规范
  - 需要统一团队开发标准
  - 需要配置代码质量检查工具

  【输出物】
  - 编码规范文档
  - Lint/Format配置文件
  - Code Review Checklist
  - 命名约定指南
---

# 规范制定局 (Standards Bureau)

> 中书省 · 决策层 · Universal DevOps v4.0

**状态**: 占位符 - 具体内容由后续任务填充

## 🤖 自主化操作指南 (v7.0)

### 推荐操作模式
| 操作场景 | 推荐模式 | 置信度 | 说明 |
|---------|---------|--------|------|
| 编码规范制定 | AUTONOMOUS_MANUAL | 82% | 需要行业最佳实践与团队习惯平衡 |
| 代码风格检查配置 | SCRIPTED_BATCH | 95% | ESLint/Prettier等工具配置高度标准化 |
| 命名规范文档编写 | SCRIPTED_BATCH | 90% | 基于既定模板快速生成 |
| 标准合规审计 | AUTONOMOUS_MANUAL | 78% | 需要人工判断例外情况和豁免条件 |

### 常用工具组合
- **读操作**: Read, SearchCodebase, Grep（调研现有代码风格、行业标准）
- **写操作**: Write, SearchReplace（创建规范文档、配置文件）
- **批量操作**: Linter配置生成器、代码格式化脚本、规范检查CI流水线
- **验证操作**: ESLint/Prettier dry-run、编码规范覆盖率统计工具

### 注意事项
- ⚠️ 规范制定前必须充分调研团队现有习惯，避免"空中楼阁"
- ⚠️ 新规范发布应有过渡期（grace period），允许逐步迁移
- ✅ 遵循"约定优于配置"原则，减少开发者认知负担
- ✅ 规范文档附带正反例代码片段，降低理解门槛

## 🔗 资源协调要点 (v7.0)

### 常访问资源
| 资源类型 | 典型路径 | 锁策略建议 |
|---------|---------|-----------|
| FILE | /.eslintrc.* / .prettierrc* | EXCLUSIVE (修改) |
| FILE | /docs/standards/coding-guidelines.md | SHARED (读) / EXCLUSIVE (写) |
| FILE | /docs/standards/naming-conventions.md | SHARED (读) / EXCLUSIVE (写) |
| CONFIG | CI/CD pipeline配置 | SHARED (读) / EXCLUSIVE (修改) |
| CODEBASE | 示例代码仓库 | SHARED (读) |

### 竞争规避策略
1. **规范版本化管理**: 采用语义化版本号（如v2.1.0），明确breaking changes
2. **渐进式强制执行**: 新代码强制遵循，旧代码设置deprecation deadline
3. **规范委员会机制**: 重大规范变更需经过投票表决，避免个人意志主导

## 💡 开源哲学应用 (v7.0)

### OpenCode 透明化
- 规范制定过程民主化：草案公示期收集团队反馈，修订记录完整保留
- 合规报告公开透明：定期发布编码规范 adherence report，展示各模块达标率
- 例外申请流程可视化：规范豁免请求的审批链路和理由对所有开发者可见

### OpenClaude 编排
- 智能规范推荐引擎：基于项目技术栈和团队历史偏好，自动推荐合适的lint规则集
- 违规模式聚类分析：自动识别高频违规类型，针对性加强培训和工具配置
- 规范演化预测：根据行业趋势和团队成长，提前规划下一版规范的改进方向

### Claw-Code 契约驱动
- 规则即测试：将编码规范转化为自动化lint规则，CI阶段强制执行
- 代码风格契约：通过EditorConfig、Prettier等工具确保跨IDE一致性
- 质量门禁集成：规范合规率作为代码合入的必要条件，不达标自动拦截
