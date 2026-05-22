# Cursor 平台适配指南 - Xuansto Skill

## 概述

Cursor使用 `.cursorrules` 文件和 `.mdc` (Markdown Command) 文件来定义AI行为。本指南说明如何将xuansto-skill适配到Cursor。

## 方法一：使用.cursorrules文件

### 创建.cursorrules文件

在项目根目录创建 `.cursorrules` 文件：

```bash
# .cursorrules
# Multi-Agent SDD+TDD Orchestrator

## 触发规则
当用户提到以下关键词时，激活多Agent开发模式：
- 多Agent开发、SDD、TDD、测试驱动开发、规格驱动开发
- multi-agent、orchestration、autonomous development

## 核心原则
1. Spec > Test > Code（规格优先级最高）
2. Karpathy Guidelines（Think Before Coding、Simplicity First、Surgical Changes、Goal-Driven Execution）
3. 质量门禁体系（15个质量门禁）

## 工作流
参考 .trae/skills/xuansto-skill/workflows/ 目录中的工作流定义
```

## 方法二：创建.mdc文件

### 目录结构

```
.cursor/
├── rules/
│   ├── xuansto-skill.mdc
│   └── ...
└── commands/
    ├── sprint.mdc
    ├── clarify.mdc
    ├── plan.mdc
    ├── spec.mdc
    ├── design.mdc
    ├── implement.mdc
    ├── test.mdc
    ├── review.mdc
    ├── fix.mdc
    ├── accept.mdc
    ├── deploy.mdc
    ├── agent-status.mdc
    └── learn.mdc
```

### 主Skill文件示例

创建 `.cursor/rules/xuansto-skill.mdc`：

```markdown
---
title: Xuansto Skill
description: Xuansto Skill - 多Agent自主开发编排器 | 基于SDD+TDD融合的智能开发协调系统
globs:
  - "**/*"
---

# Xuansto Skill - Multi-Agent SDD+TDD Orchestrator

## 概述
Xuansto Skill 是一个功能完善的多Agent自主开发编排器，融合规格驱动开发(SDD)与测试驱动开发(TDD)。

## 核心原则
- Spec > Test > Code
- Karpathy Guidelines
- 质量门禁体系

## Agent角色
参考 .trae/skills/xuansto-skill/agents/ 目录

## 工作流
参考 .trae/skills/xuansto-skill/workflows/ 目录
```

## 自动化转换脚本

可以使用以下Python脚本自动转换：

```python
import os
import shutil

def convert_to_cursor():
    skill_dir = ".trae/skills/xuansto-skill"
    cursor_dir = ".cursor"
    
    # 创建目录
    os.makedirs(f"{cursor_dir}/rules", exist_ok=True)
    os.makedirs(f"{cursor_dir}/commands", exist_ok=True)
    
    # 复制SKILL.md作为主规则文件
    shutil.copy(
        f"{skill_dir}/SKILL.md",
        f"{cursor_dir}/rules/xuansto-skill.mdc"
    )
    
    # 转换命令文件
    for cmd_file in os.listdir(f"{skill_dir}/commands"):
        if cmd_file.endswith(".md"):
            shutil.copy(
                f"{skill_dir}/commands/{cmd_file}",
                f"{cursor_dir}/commands/{cmd_file.replace('.md', '.mdc')}"
            )
    
    print("转换完成！")

if __name__ == "__main__":
    convert_to_cursor()
```

## 验证安装

1. 重启Cursor
2. 在聊天中使用触发词
3. 检查AI是否按照Skill定义的行为工作

## 注意事项

- Cursor的.mdc文件格式与标准Markdown略有不同
- 需要添加YAML frontmatter中的globs字段
- 命令文件需要放在commands目录下
