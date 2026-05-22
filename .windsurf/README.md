# Windsurf 平台适配指南 - Xuansto Skill

## 概述

Windsurf使用YAML配置文件来定义Skills。本指南说明如何将xuansto-skill适配到Windsurf。

## 方法一：创建skills.yaml配置文件

### 目录结构

```
.windsurf/
├── skills.yaml
└── README.md
```

### skills.yaml配置示例

创建 `.windsurf/skills.yaml` 文件：

```yaml
version: "1.0"
skills:
  - name: xuansto-skill
    description: |
      Xuansto Skill - 多Agent自主开发编排器
      基于SDD+TDD融合的智能开发协调系统，支持多Agent协作、质量门禁、自主迭代与持续演化
    version: "1.0.0"
    author: skiller-team
    tags:
      - xuansto
      - multi-agent
      - sdd
      - tdd
      - orchestration
      - autonomous-development
      - quality-gates
    trigger_words:
      - xuansto
      - 多Agent开发
      - SDD
      - TDD
      - 测试驱动开发
      - 规格驱动开发
      - 自主开发
      - 质量门禁
      - Agent协作
      - multi-agent
      - orchestration
    path: .trae/skills/xuansto-skill
    enabled: true
    
    # 工作流配置
    workflows:
      - name: sdd-tdd-full
        description: 完整SDD+TDD工作流
        path: workflows/sdd-tdd-full.md
      - name: sdd-tdd-fast
        description: 快速SDD+TDD工作流
        path: workflows/sdd-tdd-fast.md
      - name: ui-ux-workflow
        description: UI/UX设计工作流
        path: workflows/ui-ux-workflow.md
      - name: security-audit
        description: 安全审计工作流
        path: workflows/security-audit.md
      - name: ai-pentest
        description: AI渗透测试工作流
        path: workflows/ai-pentest.md
      - name: performance-test
        description: 性能测试工作流
        path: workflows/performance-test.md
      - name: acceptance
        description: 验收工作流
        path: workflows/acceptance.md
      - name: bug-fix
        description: Bug修复工作流
        path: workflows/bug-fix.md
    
    # 命令配置
    commands:
      - name: sprint
        description: 启动Sprint开发周期
        path: commands/sprint.md
      - name: clarify
        description: 需求澄清
        path: commands/clarify.md
      - name: plan
        description: 规划与规格
        path: commands/plan.md
      - name: spec
        description: 规格文档
        path: commands/spec.md
      - name: design
        description: UI/UX设计
        path: commands/design.md
      - name: implement
        description: 实施
        path: commands/implement.md
      - name: test
        description: 测试
        path: commands/test.md
      - name: review
        description: 代码审查
        path: commands/review.md
      - name: fix
        description: 修复问题
        path: commands/fix.md
      - name: accept
        description: 验收
        path: commands/accept.md
      - name: deploy
        description: 部署
        path: commands/deploy.md
      - name: agent-status
        description: Agent状态查询
        path: commands/agent-status.md
      - name: learn
        description: 学习与演化
        path: commands/learn.md
    
    # Agent配置
    agents:
      layer: orchestrator
      count: 35
      layers:
        - orchestrator
        - product
        - design
        - engineering
        - database
        - testing
        - security
        - devops
        - quality
        - documentation
    
    # 质量门禁配置
    quality_gates:
      count: 15
      enforcement: strict
      gates:
        - SPEC-COMPLETE
        - TEST-COVERAGE
        - CODE-REVIEW
        - SECURITY-SCAN
        - PERFORMANCE
        - DOC-COMPLETE
        - DESIGN-TOKENS
        - ACCESSIBILITY
        - VISUAL-REGRESSION
        - AI-PENETRATION
        - AGENTIC-SECURITY
        - UX-ACCEPTANCE
        - COMPLIANCE
        - DEPLOYMENT
        - MONITORING
```

## 方法二：使用配置生成脚本

### Python脚本示例

```python
import yaml
import os

def generate_windsurf_config():
    skill_dir = ".trae/skills/multi-agent-sdd-tdd-orchestrator"
    
    config = {
        "version": "1.0",
        "skills": [{
            "name": "xuansto-skill",
            "description": "Xuansto Skill - 多Agent自主开发编排器 | 基于SDD+TDD融合的智能开发协调系统",
            "version": "1.0.0",
            "author": "skiller-team",
            "tags": [
                "xuansto", "multi-agent", "sdd", "tdd", "orchestration",
                "autonomous-development", "quality-gates"
            ],
            "trigger_words": [
                "xuansto", "多Agent开发", "SDD", "TDD", "测试驱动开发",
                "规格驱动开发", "自主开发", "质量门禁",
                "Agent协作", "multi-agent", "orchestration"
            ],
            "path": skill_dir,
            "enabled": True
        }]
    }
    
    # 创建目录
    os.makedirs(".windsurf", exist_ok=True)
    
    # 写入配置文件
    with open(".windsurf/skills.yaml", "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
    
    print("Windsurf配置文件已生成！")

if __name__ == "__main__":
    generate_windsurf_config()
```

## 验证安装

1. 重启Windsurf
2. 检查配置文件是否正确加载
3. 使用触发词测试Skill是否激活

## 注意事项

- Windsurf的YAML配置格式可能与版本相关
- 确保path路径正确
- trigger_words字段用于自动激活Skill
- enabled字段控制Skill是否启用

## 高级配置

### 环境变量

可以在skills.yaml中配置环境变量：

```yaml
environment:
  SKILL_DEBUG: "false"
  QUALITY_GATE_STRICT: "true"
  AGENT_TIMEOUT: "300"
```

### 自定义触发器

```yaml
triggers:
  - type: keyword
    keywords: ["多Agent", "SDD", "TDD"]
  - type: file_pattern
    patterns: ["**/*.spec.md", "**/*.test.js"]
  - type: command
    commands: ["/sprint", "/clarify", "/plan"]
```
