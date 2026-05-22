# Claude Code 平台适配指南 - Xuansto Skill

## 方法一：创建软链接（推荐）

### Windows (PowerShell)
```powershell
# 在项目根目录执行
New-Item -ItemType Junction -Path ".claude\skills\xuansto-skill" -Target ".trae\skills\xuansto-skill"
```

### Linux/macOS
```bash
# 在项目根目录执行
mkdir -p .claude/skills
ln -s ../../.trae/skills/xuansto-skill .claude/skills/xuansto-skill
```

## 方法二：使用适配版SKILL.md

如果软链接方式不可行，可以创建适配版SKILL.md：

### 步骤

1. 创建目录结构：
   ```bash
   mkdir -p .claude/skills/multi-agent-sdd-tdd-orchestrator
   ```

2. 复制并修改SKILL.md：
   - 复制 `.trae/skills/multi-agent-sdd-tdd-orchestrator/SKILL.md` 到 `.claude/skills/multi-agent-sdd-tdd-orchestrator/SKILL.md`
   - 简化YAML frontmatter格式（如果需要）

## Anthropic Skills 2.0 规范兼容性

本Skill符合Anthropic Skills 2.0规范，主要特性：

- ✅ YAML frontmatter格式
- ✅ name、description、version字段
- ✅ 渐进式披露设计
- ✅ Markdown格式指令

## 触发词

在Claude Code中，可以使用以下触发词激活Skill：

- "xuansto"
- "多Agent开发"
- "SDD"
- "TDD"
- "测试驱动开发"
- "规格驱动开发"
- "自主开发"
- "质量门禁"
- "Agent协作"
- "multi-agent"
- "orchestration"

## 验证安装

安装后，重启Claude Code并尝试使用触发词，应该能看到Skill被激活。

## 注意事项

- 软链接方式更简单，推荐使用
- 如果遇到权限问题，请使用方法二
- 确保Skill目录路径正确
