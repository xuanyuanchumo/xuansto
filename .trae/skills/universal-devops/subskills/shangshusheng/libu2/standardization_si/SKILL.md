---
name: standardization-si
parent: universal-devops
department: libu2
province: shangshusheng
description: |
  标准化司 - 礼部·仪制司

  【职责】命名规范、格式标准、文档结构统一

  【触发条件】
  - 需要统一项目命名规范
  - 文档格式标准制定
  - 结构一致性检查

  【能力】
  - 命名规范检查器
  - 格式标准定义
  - 文档结构验证
  - 自动化格式化
---

# 标准化司 (Standardization Si)

> 尚书省 · 礼部 · Universal DevOps v4.0

**状态**: 占位符 - 具体内容由后续任务填充

## 🤖 自主化操作指南 (v7.0)

### 推荐操作模式
| 操作场景 | 推荐模式 | 置信度 | 说明 |
|---------|---------|--------|------|
| 命名规范检查 | SCRIPTED_BATCH | 97% | Linter规则高度自动化执行 |
| 格式标准制定 | AUTONOMOUS_MANUAL | 78% | 需要行业调研和团队共识 |
| 文档结构验证 | SCRIPTED_BATCH | 95% | 基于Schema的结构校验 |
| 标准合规审计 | HYBRID_ASSISTED | 86% | 工具扫描 + 人工判断例外 |

### 常用工具组合
- **读操作**: Read, SearchCodebase, Grep（检查命名规范、格式一致性）
- **写操作**: Write, SearchReplace（编写标准文档、配置linter规则）
- **批量操作**: ESLint/Prettier/Hadolint等lint工具链、格式化脚本、CI检查pipeline
- **验证操作**: 合规率统计工具、标准覆盖率报告生成器

### 注意事项
- ⚠️ 标准制定应"自下而上": 收集团队最佳实践再提炼为标准，而非自上而下强推
- ⚠️ 避免"标准膨胀": 只制定真正必要的标准，过度标准化会增加认知负担
- ✅ 采用"渐进式强化": 新项目强制遵循，旧项目设置迁移时间线
- ✅ 标准必须附带示例：正例+反例+解释，降低理解和执行成本

## 🔗 资源协调要点 (v7.0)

### 常访问资源
| 资源类型 | 典型路径 | 锁策略建议 |
|---------|---------|-----------|
| CONFIG | .editorconfig / .prettierrc / linter配置 | EXCLUSIVE (修改) |
| FILE | /docs/standards/ | SHARED (读) / EXCLUSIVE (写) |
| CI/CD | 格式检查pipeline配置 | PROTECTED |
| CODEBASE | 项目源码目录 | SHARED (扫描) |
| TEMPLATE | 标准文档模板 | VERSION_CONTROLLED |

### 竞争规避策略
1. **标准版本化管理**: 使用语义化版本号管理标准变更，明确breaking changes
2. **Linter配置集中化**: 统一的lint配置通过npm包或git submodule共享，避免各项目不一致
3. **Auto-fix优先**: 能自动修复的格式问题不要阻塞人工review，让工具处理琐事

## 💡 开源哲学应用 (v7.0)

### OpenCode 透明化
- 标准制定过程民主化：草案公示→收集反馈→修订→正式发布，全程可追溯
- 合规数据透明化：各项目的标准达标率、常见违规类型定期公示
- 标准演进路线图可视：下一版标准的改进方向和时间规划公开讨论

### OpenClaude 编排
- 智能违规聚类：自动识别高频违规模式，针对性加强培训和工具配置
- 标准推荐引擎：根据项目技术栈和团队特点，推荐最合适的标准子集
- 违规影响评估：量化不规范代码带来的维护成本增加和技术债务积累

### Claw-Code 契约驱动
- 标准即代码：将编码规范转化为可执行的lint规则，CI阶段强制执行
- 标准准入门槛：新项目初始化时必须通过标准合规检查才能开始开发
- 持续改进闭环：定期review标准本身的有效性，废弃过时标准、采纳新实践
