---
name: uiux-design-si
parent: universal-devops
department: gongbu
province: shangshusheng
description: |
  UI/UX设计司 - 工部·虞部司

  【职责】界面原型、交互设计、用户体验优化

  【触发条件】
  - 需要UI/UX设计和原型
  - 交互流程设计
  - 用户体验评估和优化

  【能力】
  - 线框图和原型生成
  - 组件库选择
  - 设计规范制定
  - 可访问性检查
---

# UI/UX设计司 (UI/UX Design Si)

> 尚书省 · 工部 · Universal DevOps v4.0

**状态**: 占位符 - 具体内容由后续任务填充

## 🤖 自主化操作指南 (v7.0)

### 推荐操作模式
| 操作场景 | 推荐模式 | 置信度 | 说明 |
|---------|---------|--------|------|
| 线框图/原型生成 | HYBRID_ASSISTED | 84% | AI辅助布局 + 人工调整视觉细节 |
| 组件库选型 | AUTONOMOUS_MANUAL | 77% | 需要考虑生态、定制性、团队能力 |
| 设计规范制定 | AUTONOMOUS_MANUAL | 73% | 涉及品牌一致性和用户体验策略 |
| 可访问性检查 | SCRIPTED_BATCH | 92% | Axe/WAVE等自动化工具高度成熟 |

### 常用工具组合
- **读操作**: Read, SearchCodebase, Grep（读取设计稿、组件文档、用户故事）
- **写操作**: Write, SearchReplace（编写设计规范、生成原型代码）
- **批量操作**: Figma/Sketch插件、Design Token导出工具、样式指南生成器
- **验证操作**: 可访问性审计工具(Axe/Core)、响应式测试、跨浏览器兼容性检查

### 注意事项
- ⚠️ 设计必须服务于功能：避免"为了设计而设计"，每个设计决策都应有用户体验依据
- ⚠️ 移动端优先(Mobile First): 从小屏幕开始设计再逐步增强，而非从桌面端裁剪
- ✅ 采用"设计系统"(Design System): 建立统一的组件库和设计Token，保证一致性
- ✅ 可访问性(A11y)不是可选项：遵循WCAG 2.1 AA标准，确保所有用户都能使用

## 🔗 资源协调要点 (v7.0)

### 常访问资源
| 资源类型 | 典型路径 | 锁策略建议 |
|---------|---------|-----------|
| DESIGN | Figma/Sketch设计文件 | COLLABORATIVE (多人协作) |
| ASSET | 图标/图片/字体资源库 | CDN_HOSTED |
| TOKEN | Design Tokens(JSON/CSS) | SINGLE_SOURCE_OF_TRUTH |
| COMPONENT | UI组件库(Storybook) | VERSION_CONTROLLED |
| STYLEGUIDE | 样式指南文档 | PUBLISHED (公开发布) |

### 竞争规避策略
1. **设计评审 gating**: 核心页面设计必须经过设计评审才能进入开发阶段
2. **Token统一管理**: 颜色/间距/字体等设计变量集中管理，避免各处硬编码不一致
3. **组件所有权明确**: 每个UI组件有明确的owner，避免多人同时修改导致冲突

## 💡 开源哲学应用 (v7.0)

### OpenCode 透明化
- 设计决策过程公开：为什么选择这个设计方案、参考了什么竞品、做了哪些A/B测试
- 设计系统完全开放：所有设计师和前端开发者可查阅和使用完整的组件库和设计规范
- 用户反馈闭环透明：收集的用户体验问题和改进建议的处理状态全程可见

### OpenClaude 编排
- 智能布局推荐：根据内容类型和用户场景自动推荐合适的布局方案（卡片/列表/表格）
- Design-to-Code自动转换：将Figma设计稿自动转换为高质量的前端代码(React/Vue)
- 一致性违规检测：自动识别不符合设计系统的实现（如错误的颜色值、间距偏差）

### Claw-Code 契约驱动
- 设计-开发一致性契约：Design Tokens作为设计和开发的单一事实来源，确保像素级一致
- 可访问性合规门禁：PR必须通过自动化可访问性检查(Axe Core)才能合入
- 设计债务追踪：标识出的UI不一致和技术债（如废弃的CSS类）纳入清理计划
