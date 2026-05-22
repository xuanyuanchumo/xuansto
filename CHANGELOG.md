# 变更日志 (CHANGELOG)

## [1.0.0] - 2026-04-17

### 重命名
- **BREAKING**: 将项目从 `multi-agent-sdd-tdd-orchestrator` 重命名为 `xuansto-skill`
- 更新所有文件中的 Skill 名称引用
- 更新 SKILL.md 的 YAML frontmatter
- 更新 README.md 中的项目名称和描述
- 更新所有平台适配文件中的引用

### 新增
- 添加新的触发词 "xuansto"
- 在 SKILL.md 中添加 xuansto 标签
- 创建 Claude Code 平台适配指南
- 创建 Cursor 平台适配指南
- 创建 Windsurf 平台适配指南

### 优化
- 优化 SKILL.md 描述，使其更加清晰和易于触发
- 优化 README.md 结构，添加中英文双语说明
- 完善平台兼容性文档

### 检查与验证
- 验证所有文件编码为 UTF-8 without BOM
- 验证 YAML frontmatter 格式正确
- 验证所有 Agent 定义文件完整（35个）
- 验证所有工作流文件完整（8个）
- 验证所有命令文件完整（13个）
- 验证所有模板文件完整（12个）
- 验证所有脚本文件完整（12个）
- 验证所有参考文档完整（14个）

### 平台兼容性
- ✅ Trae IDE: 完全兼容
- ✅ Claude Code: 提供适配指南
- ✅ Cursor: 提供适配指南
- ✅ Windsurf: 提供适配指南

### 已知问题
- ⚠️ SKILL.md 主体内容 765 行，超过推荐的 500 行限制
  - **说明**: 内容结构清晰、模块化良好，暂不进行精简
  - **建议**: 后续版本可考虑将详细内容拆分到 references 目录

---

## 项目历史

### 原始版本 (multi-agent-sdd-tdd-orchestrator)
- 基于 SDD+TDD 融合的多Agent自主开发编排器
- 35个专业Agent角色
- 8个工作流定义
- 13个命令定义
- 15个质量门禁
- 完整的安全体系（OWASP Top 10 + Agentic Top 10）
