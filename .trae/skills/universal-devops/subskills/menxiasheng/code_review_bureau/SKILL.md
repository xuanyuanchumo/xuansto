---
name: code-review-bureau
parent: universal-devops
province: menxiasheng
description: |
  代码审查局 - 门下省质量把关核心单元

  【职责】Code Review、静态分析、安全扫描、性能审计、最佳实践检查

  【触发条件】
  - PR/MR提交需要代码审查
  - 代码质量专项检查
  - 安全漏洞扫描和审计

  【输出物】
  - Code Review报告
  - 问题清单和修复建议
  - 安全扫描结果
  - 代码质量评分
---

# 代码审查局 (Code Review Bureau)

> 门下省 · 审核层 · Universal DevOps v4.0

**状态**: 占位符 - 具体内容由后续任务填充

## 🤖 自主化操作指南 (v7.0)

### 推荐操作模式
| 操作场景 | 推荐模式 | 置信度 | 说明 |
|---------|---------|--------|------|
| PR代码审查 | AUTONOMOUS_MANUAL | 82% | 需要理解业务逻辑和代码意图 |
| 静态分析报告生成 | SCRIPTED_BATCH | 95% | ESLint/SonarQube等工具自动化扫描 |
| 安全漏洞检测 | HYBRID_ASSISTED | 88% | 工具初筛 + 人工确认误报 |
| 性能审计 | AUTONOMOUS_MANUAL | 78% | 需要结合业务场景判断优化价值 |

### 常用工具组合
- **读操作**: Read, SearchCodebase, Grep（深入阅读代码变更、历史实现）
- **写操作**: Write, SearchReplace（撰写review comments、审查报告）
- **批量操作**: SonarQube扫描任务、ESLint批量检查脚本
- **验证操作**: 代码复杂度计算工具、安全扫描规则引擎

### 注意事项
- ⚠️ 审查时应关注"为什么"而非仅"是什么"，理解代码背后的设计决策
- ⚠️ 避免在review中引入新的bug，建议只指出问题不直接修改代码
- ✅ 采用"友好建设性"原则：每条criticism都应附带改进建议
- ✅ 建立review checklist模板：安全性、可维护性、性能、测试覆盖

## 🔗 资源协调要点 (v7.0)

### 常访问资源
| 资源类型 | 典型路径 | 锁策略建议 |
|---------|---------|-----------|
| FILE | PR/MR diff内容 | SHARED (读) |
| FILE | /docs/review-checklist/ | SHARED (读) |
| CODEBASE | 目标分支代码 | SHARED (读) |
| API | Git托管平台API | RATE_LIMITED |
| DATABASE | Review记录数据库 | APPEND_ONLY |

### 竞争规避策略
1. **Review分配算法**: 基于领域 expertise 和负载均衡自动分配reviewer
2. **时效性保障机制**: 设置review SLA（如48小时），超时自动escalate
3. **冲突解决流程**: Reviewer意见不一致时，引入第三方tie-breaker或团队讨论

## 💡 开源哲学应用 (v7.0)

### OpenCode 透明化
- Review标准和尺度统一公开：所有reviewer遵循相同的checklist和评分标准
- 审查过程全程留痕：每条comment、每次approve/reject都有完整记录
- 质量趋势可视化：定期发布代码质量报告，展示各模块的review通过率、问题密度

### OpenClaude 编排
- 智能diff分析：自动识别高风险变更区域（核心模块、敏感数据操作）
- Review优先级排序：根据变更影响范围自动标记Critical/Major/Minor级别
- 知识库联动：发现重复问题时自动关联历史review中的类似案例和解决方案

### Claw-Code 契约驱动
- 代码合入契约：定义明确的merge条件（review通过+CI绿色+测试覆盖率达标）
- 自动化质量门禁：SonarQube Quality Gate作为PR合入的硬性门槛
- 技术债务追踪：将review中标识的"TODO""FIXME"自动录入技术债务清单并设定清理期限
