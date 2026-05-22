---
name: dependency-mgmt-si
parent: universal-devops
department: hubu
province: shangshusheng
description: |
  依赖管理司 - 户部·金部司

  【职责】依赖版本管理、漏洞扫描、依赖更新策略、许可证合规

  【触发条件】
  - 项目依赖管理和升级
  - 安全漏洞扫描和修复
  - 依赖版本冲突解决

  【能力】
  - 依赖图分析
  - 漏洞自动检测
  - 版本兼容性检查
  - 自动化更新策略
---

# 依赖管理司 (Dependency Mgmt Si)

> 尚书省 · 户部 · Universal DevOps v4.0

**状态**: 占位符 - 具体内容由后续任务填充

## 🤖 自主化操作指南 (v7.0)

### 推荐操作模式
| 操作场景 | 推荐模式 | 置信度 | 说明 |
|---------|---------|--------|------|
| 依赖版本升级 | SCRIPTED_BATCH | 94% | Dependabot/Renovate等工具自动化处理 |
| 漏洞扫描执行 | SCRIPTED_BATCH | 96% | Snyk/NPM Audit高度自动化 |
| 版本冲突解决 | HYBRID_ASSISTED | 83% | 工具分析依赖图 + 人工决策取舍 |
| 许可证合规审查 | AUTONOMOUS_MANUAL | 76% | 需要法律/合规知识判断 |

### 常用工具组合
- **读操作**: Read, SearchCodebase, Grep（读取package.json/pom.xml、分析依赖树）
- **写操作**: Write, SearchReplace（更新版本号、生成lock文件）
- **批量操作**: Dependabot配置、Renovatebot规则、漏洞批量修复脚本
- **验证操作**: 依赖兼容性测试套件、许可证扫描器(FOSSA/License Finder)

### 注意事项
- ⚠️ Major版本升级必须充分测试：breaking changes可能导致运行时故障
- ⚠️ 避免盲目追新：最新版可能有未发现的bug，建议滞后1-2个版本采用LTS
- ✅ 采用"锁文件提交"策略：package-lock.json/yarn.lock/pom.xml.resolved必须纳入版本控制
- ✅ 建立依赖准入标准：禁止引入已知有安全问题的库或不符合许可证要求的库

## 🔗 资源协调要点 (v7.0)

### 常访问资源
| 资源类型 | 典型路径 | 锁策略建议 |
|---------|---------|-----------|
| FILE | package.json / pom.xml / requirements.txt | EXCLUSIVE (修改) |
| FILE | package-lock.json / yarn.lock | AUTO_GENERATED (由工具管理) |
| CACHE | 依赖缓存目录(node_modules/.cache) | SHARED (读) / INVALIDATE (清理) |
| REGISTRY | NPM/PyPI/Maven仓库 | RATE_LIMITED |
| API | 漏洞数据库(NVD/CVE)接口 | CACHED (定期同步) |

### 竞争规避策略
1. **原子性升级**: 依赖更新作为独立PR提交，避免与其他功能变更混合导致难以回滚
2. **并行构建隔离**: 不同分支的依赖安装使用独立的缓存，避免缓存污染
3. **渐进式发布**: 先在canary环境验证，再逐步推广至production

## 💡 开源哲学应用 (v7.0)

### OpenCode 透明化
- 依赖清单完全公开：所有项目的直接和传递依赖及其许可证类型可视化展示
- 漏洞状态实时透明：每个已知漏洞的状态（已修复/待修复/已接受风险）对开发者可见
- 升级决策理由记录：为什么选择/拒绝某个版本的升级，记录技术判断依据

### OpenClaude 编排
- 智能升级优先级排序：基于CVSS评分、利用难度、影响范围自动计算升级紧迫度
- 突破性变更影响分析：自动识别Major版本升级的breaking changes并评估影响范围
- 许可证冲突预警：检测新引入依赖是否与现有许可证存在不兼容（如GPL与MIT混用）

### Claw-Code 契约驱动
- 依赖健康契约：定义最大允许的漏洞数量、过时依赖比例等指标作为合入门槛
- 自动化安全门禁：PR触发自动依赖扫描，发现Critical/High漏洞时阻止合入
- 许可证合规自动化：CI阶段检查依赖许可证是否符合组织政策，违规自动拦截
