# 技能健康度评估系统说明文档

> 🏥 **健康监测，持续优化** - 通过全面的健康度评估确保技能系统稳定运行

---

## 概述

技能健康度评估系统是 sanliu 技能的核心监控组件，通过多维度评估技能系统的健康状态，为持续演化提供数据支持和决策依据。

### 核心功能

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      健康度评估系统架构                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                      数据采集层                                       │   │
│   │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│   │  │ 文档扫描器   │  │ 脚本检查器   │  │ 配置解析器   │              │   │
│   │  │    Doc       │  │   Script     │  │   Config     │              │   │
│   │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│   │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│   │  │ 路径验证器   │  │ 元数据提取器 │  │ 依赖检查器   │              │   │
│   │  │    Path      │  │  Metadata    │  │  Dependency  │              │   │
│   │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                      评估计算层                                       │   │
│   │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│   │  │ 权重计算器   │  │ 评分引擎     │  │ 等级判定器   │              │   │
│   │  │   Weight     │  │   Scoring    │  │   Level      │              │   │
│   │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                      报告生成层                                       │   │
│   │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│   │  │ 报告生成器   │  │ 建议生成器   │  │ 趋势分析器   │              │   │
│   │  │   Report     │  │Recommendation│  │    Trend     │              │   │
│   │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 健康度评分维度

### 评估维度概览

| 维度 | 权重 | 说明 | 关键指标 |
|------|------|------|----------|
| 文档完整性 | 25% | SKILL.md、子技能文档完整性 | 文件存在、章节完整、格式正确 |
| 脚本可用性 | 30% | 核心脚本存在性、语法正确性 | 文件存在、语法正确、导入有效 |
| 配置一致性 | 20% | 环境配置、Docker 配置完整性 | 格式正确、字段完整、值有效 |
| 路径结构 | 15% | 目录结构完整性 | 目录存在、权限正确 |
| 元数据 | 10% | Frontmatter、版本信息完整性 | 字段完整、格式正确 |

### 健康等级定义

| 等级 | 分数范围 | 状态 | 说明 |
|------|----------|------|------|
| `excellent` | 90-100 | 优秀 | 技能系统健康，无需改进 |
| `good` | 80-89 | 良好 | 技能系统基本健康，有小幅改进空间 |
| `fair` | 70-79 | 一般 | 技能系统存在一些问题，建议改进 |
| `poor` | 60-69 | 较差 | 技能系统存在较多问题，需要改进 |
| `critical` | 0-59 | 危急 | 技能系统存在严重问题，急需修复 |

---

## 详细评估维度

### 1. 文档完整性评估

#### 评估内容

| 检查项 | 权重 | 说明 |
|--------|------|------|
| SKILL.md 存在性 | 20% | 检查主技能文档是否存在 |
| 子技能文档存在性 | 20% | 检查所有子技能文档是否存在 |
| 章节完整性 | 25% | 检查必需章节是否完整 |
| 格式正确性 | 20% | 检查 Markdown 格式是否正确 |
| 链接有效性 | 15% | 检查内部链接是否有效 |

#### 必需章节列表

```python
REQUIRED_SECTIONS = {
    "SKILL.md": [
        "概述",
        "核心能力",
        "使用指南",
        "配置说明",
        "最佳实践"
    ],
    "subskills/*.md": [
        "概述",
        "核心功能",
        "使用示例",
        "配置选项"
    ]
}
```

#### 评分规则

```python
def calculate_documentation_score(skill_root):
    score = 0
    
    if os.path.exists(f"{skill_root}/SKILL.md"):
        score += 20
    
    subskills_dir = f"{skill_root}/subskills"
    if os.path.exists(subskills_dir):
        md_files = glob.glob(f"{subskills_dir}/*.md")
        expected_files = get_expected_subskill_docs()
        coverage = len(md_files) / len(expected_files)
        score += 20 * coverage
    
    for section in REQUIRED_SECTIONS["SKILL.md"]:
        if section_in_file(f"{skill_root}/SKILL.md", section):
            score += 5
    
    return min(score, 100)
```

### 2. 脚本可用性评估

#### 评估内容

| 检查项 | 权重 | 说明 |
|--------|------|------|
| 核心脚本存在性 | 30% | 检查核心脚本文件是否存在 |
| 语法正确性 | 30% | 检查 Python 脚本语法是否正确 |
| 导入有效性 | 25% | 检查导入语句是否有效 |
| 执行权限 | 15% | 检查脚本是否有执行权限 |

#### 核心脚本列表

```python
CORE_SCRIPTS = {
    "required": [
        "skillscripts/core/skill_health_assessor.py",
        "skillscripts/core/skill_auto_repairer.py",
        "skillscripts/core/evolution_manager.py",
        "skillscripts/core/version_iterator.py"
    ],
    "recommended": [
        "skillscripts/analysis/log_analyzer.py",
        "skillscripts/analysis/issue_locator.py",
        "skillscripts/optimization/auto_fixer.py",
        "skillscripts/utils/path_config_manager.py"
    ]
}
```

#### 评分规则

```python
def calculate_script_score(skill_root):
    score = 0
    
    for script in CORE_SCRIPTS["required"]:
        script_path = f"{skill_root}/{script}"
        if os.path.exists(script_path):
            score += 7.5
            
            try:
                with open(script_path, 'r') as f:
                    compile(f.read(), script_path, 'exec')
                score += 7.5
            except SyntaxError:
                pass
    
    for script in CORE_SCRIPTS["recommended"]:
        script_path = f"{skill_root}/{script}"
        if os.path.exists(script_path):
            score += 2.5
    
    return min(score, 100)
```

### 3. 配置一致性评估

#### 评估内容

| 检查项 | 权重 | 说明 |
|--------|------|------|
| 环境配置完整性 | 30% | 检查 .env.example 是否完整 |
| Docker 配置完整性 | 25% | 检查 Docker 相关配置文件 |
| 技能配置完整性 | 25% | 检查技能配置文件 |
| 配置格式正确性 | 20% | 检查配置文件格式是否正确 |

#### 配置文件检查

```python
REQUIRED_CONFIGS = {
    "environment": [
        ".env.example",
        "config/environment.yaml"
    ],
    "docker": [
        "docker/Dockerfile",
        "docker/docker-compose.yml"
    ],
    "skill": [
        "config/skill.yaml",
        "config/interfaces.json"
    ]
}
```

#### 评分规则

```python
def calculate_config_score(skill_root):
    score = 0
    
    for config in REQUIRED_CONFIGS["environment"]:
        if os.path.exists(f"{skill_root}/{config}"):
            score += 15
    
    for config in REQUIRED_CONFIGS["docker"]:
        if os.path.exists(f"{skill_root}/{config}"):
            score += 12.5
    
    for config in REQUIRED_CONFIGS["skill"]:
        if os.path.exists(f"{skill_root}/{config}"):
            score += 12.5
    
    return min(score, 100)
```

### 4. 路径结构评估

#### 评估内容

| 检查项 | 权重 | 说明 |
|--------|------|------|
| 核心目录存在性 | 40% | 检查核心目录是否存在 |
| 子目录完整性 | 30% | 检查子目录结构是否完整 |
| 权限正确性 | 30% | 检查目录权限是否正确 |

#### 必需目录结构

```python
REQUIRED_DIRECTORIES = {
    "core": [
        "skillscripts/core",
        "skillscripts/utils",
        "skillscripts/analysis"
    ],
    "docs": [
        "subskills"
    ],
    "config": [
        "config"
    ],
    "resources": [
        "resources/templates",
        "resources/data"
    ]
}
```

#### 评分规则

```python
def calculate_path_score(skill_root):
    score = 0
    
    for dir_path in REQUIRED_DIRECTORIES["core"]:
        if os.path.isdir(f"{skill_root}/{dir_path}"):
            score += 10
    
    for dir_path in REQUIRED_DIRECTORIES["docs"]:
        if os.path.isdir(f"{skill_root}/{dir_path}"):
            score += 15
    
    for dir_path in REQUIRED_DIRECTORIES["config"]:
        if os.path.isdir(f"{skill_root}/{dir_path}"):
            score += 10
    
    for dir_path in REQUIRED_DIRECTORIES["resources"]:
        if os.path.isdir(f"{skill_root}/{dir_path}"):
            score += 7.5
    
    return min(score, 100)
```

### 5. 元数据评估

#### 评估内容

| 检查项 | 权重 | 说明 |
|--------|------|------|
| Frontmatter 完整性 | 40% | 检查 SKILL.md 的 frontmatter |
| 版本信息完整性 | 30% | 检查 version.json 是否完整 |
| 依赖信息完整性 | 30% | 检查依赖声明是否完整 |

#### 必需 Frontmatter 字段

```yaml
---
name: skill_name
version: 1.0.0
description: 技能描述
author: 作者名称
created_at: 2024-01-01
updated_at: 2024-03-29
tags:
  - tag1
  - tag2
---
```

#### 评分规则

```python
def calculate_metadata_score(skill_root):
    score = 0
    
    frontmatter = extract_frontmatter(f"{skill_root}/SKILL.md")
    required_fields = ["name", "version", "description", "author"]
    for field in required_fields:
        if field in frontmatter:
            score += 10
    
    version_file = f"{skill_root}/version.json"
    if os.path.exists(version_file):
        with open(version_file) as f:
            version_data = json.load(f)
        if "current_version" in version_data:
            score += 15
        if "project_name" in version_data:
            score += 15
    
    return min(score, 100)
```

---

## 使用方法

### 命令行使用

#### 基本评估

```bash
# 执行完整健康度评估
python skillscripts/core/skill_health_assessor.py

# 指定技能根目录
python skillscripts/core/skill_health_assessor.py --skill-root ./

# 仅评估特定维度
python skillscripts/core/skill_health_assessor.py --category documentation
python skillscripts/core/skill_health_assessor.py --category scripts
python skillscripts/core/skill_health_assessor.py --category config

# 输出 JSON 格式
python skillscripts/core/skill_health_assessor.py --format json

# 输出到文件
python skillscripts/core/skill_health_assessor.py --output health_report.md
```

## 高级选项

```bash
# 设置健康度阈值触发演化
python skillscripts/core/skill_health_assessor.py --threshold 75 --auto-evolve

# 对比历史评估结果
python skillscripts/core/skill_health_assessor.py --compare previous

# 生成趋势报告
python skillscripts/core/skill_health_assessor.py --trend --days 30

# 详细输出模式
python skillscripts/core/skill_health_assessor.py --verbose
```

## 编程接口

#### 基本使用

```python
from skillscripts.core.skill_health_assessor import SkillHealthAssessor

assessor = SkillHealthAssessor(skill_root='./')

report = assessor.assess()

print(f"健康度评分: {report.overall_score}/100")
print(f"健康等级: {report.health_level.value}")
print(f"评估时间: {report.timestamp}")

for category, result in report.category_results.items():
    print(f"\n{category}:")
    print(f"  分数: {result.score}/100")
    print(f"  状态: {result.status}")
    for issue in result.issues:
        print(f"  - {issue}")
```

#### 分类评估

```python
from skillscripts.core.skill_health_assessor import SkillHealthAssessor, AssessmentCategory

assessor = SkillHealthAssessor(skill_root='./')

doc_report = assessor.assess_category(AssessmentCategory.DOCUMENTATION)
print(f"文档完整性: {doc_report.score}/100")

script_report = assessor.assess_category(AssessmentCategory.SCRIPTS)
print(f"脚本可用性: {script_report.score}/100")

config_report = assessor.assess_category(AssessmentCategory.CONFIG)
print(f"配置一致性: {config_report.score}/100")
```

#### 获取改进建议

```python
report = assessor.assess()

for recommendation in report.recommendations:
    print(f"优先级: {recommendation.priority}")
    print(f"类别: {recommendation.category}")
    print(f"建议: {recommendation.description}")
    print(f"预期提升: {recommendation.expected_improvement}")
    print("---")
```

#### 健康度趋势分析

```python
trend = assessor.get_health_trend(days=30)

print(f"30天健康度趋势:")
print(f"  起始分数: {trend['start_score']}")
print(f"  结束分数: {trend['end_score']}")
print(f"  变化趋势: {trend['trend']}")
print(f"  平均分数: {trend['average_score']}")
print(f"  最高分数: {trend['max_score']}")
print(f"  最低分数: {trend['min_score']}")
```

### 与其他系统集成

#### 与自动修复系统集成

```python
from skillscripts.core.skill_health_assessor import SkillHealthAssessor
from skillscripts.core.skill_auto_repairer import SkillAutoRepairer

assessor = SkillHealthAssessor(skill_root='./')
repairer = SkillAutoRepairer(skill_root='./')

report = assessor.assess()

if report.overall_score < 75:
    print(f"健康度较低 ({report.overall_score})，触发自动修复...")
    
    repair_report = repairer.repair(
        fix_docs=True,
        fix_scripts=True,
        fix_config=True,
        dry_run=False
    )
    
    new_report = assessor.assess()
    print(f"修复后健康度: {new_report.overall_score}")
```

#### 与演化系统集成

```python
from skillscripts.core.skill_health_assessor import SkillHealthAssessor
from skillscripts.evolution_manager import EvolutionManager

assessor = SkillHealthAssessor(skill_root='./')
evolution_manager = EvolutionManager(project_root='./')

report = assessor.assess()

if report.overall_score < 70:
    evolution_manager.trigger_evolution(
        evolution_type="skill_optimization",
        reason=f"健康度评分低于阈值: {report.overall_score}",
        health_report=report.to_dict()
    )
```

#### 与实时监控集成

```python
from skillscripts.core.skill_health_assessor import SkillHealthAssessor
from skillscripts.monitoring.realtime_monitor import RealtimeMonitor

assessor = SkillHealthAssessor(skill_root='./')
monitor = RealtimeMonitor(skill_root='./')

def health_check_handler():
    report = assessor.assess()
    
    if report.overall_score < 75:
        monitor.send_alert(
            level="warning",
            message=f"健康度下降: {report.overall_score}"
        )

monitor.add_scheduled_task(health_check_handler, interval=3600)
monitor.start()
```

---

## 评估报告

### 报告格式

#### Markdown 格式

```markdown
# 技能健康度评估报告

## 概览

- **评估时间**: 2024-03-29 10:30:00
- **总体评分**: 85/100
- **健康等级**: 良好 (good)

## 分类评分

| 类别 | 分数 | 状态 | 权重 |
|------|------|------|------|
| 文档完整性 | 90/100 | ✓ 良好 | 25% |
| 脚本可用性 | 85/100 | ✓ 良好 | 30% |
| 配置一致性 | 80/100 | ✓ 良好 | 20% |
| 路径结构 | 95/100 | ✓ 优秀 | 15% |
| 元数据 | 75/100 | ⚠ 一般 | 10% |

## 问题详情

### 文档完整性

- ✓ SKILL.md 存在
- ✓ 子技能文档完整
- ⚠ 缺少最佳实践章节

### 脚本可用性

- ✓ 核心脚本存在
- ✓ 语法检查通过
- ⚠ 部分导入路径需要更新

## 改进建议

1. **[高优先级]** 添加缺失的最佳实践章节
2. **[中优先级]** 更新脚本导入路径
3. **[低优先级]** 完善 frontmatter 元数据
```

### JSON 格式

```json
{
  "timestamp": "2024-03-29T10:30:00",
  "overall_score": 85,
  "health_level": "good",
  "category_results": {
    "documentation": {
      "score": 90,
      "weight": 0.25,
      "status": "good",
      "issues": []
    },
    "scripts": {
      "score": 85,
      "weight": 0.30,
      "status": "good",
      "issues": [
        {
          "severity": "warning",
          "message": "部分导入路径需要更新",
          "location": "skillscripts/utils/helper.py"
        }
      ]
    }
  },
  "recommendations": [
    {
      "priority": "high",
      "category": "documentation",
      "description": "添加缺失的最佳实践章节",
      "expected_improvement": 5
    }
  ]
}
```

---

## 最佳实践

### 1. 定期评估

```bash
# 添加到定时任务
# 每天凌晨执行健康度评估
0 0 * * * cd /path/to/skill && python skillscripts/core/skill_health_assessor.py --output reports/health_$(date +\%Y\%m\%d).md
```

## 2. 集成到 CI/CD

```yaml
# .github/workflows/health-check.yml
name: Health Check

on:
  schedule:
    - cron: '0 0 * * *'
  workflow_dispatch:

jobs:
  health-assessment:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Run Health Assessment
        run: |
          python skillscripts/core/skill_health_assessor.py \
            --output health_report.md \
            --format json
      
      - name: Upload Report
        uses: actions/upload-artifact@v3
        with:
          name: health-report
          path: health_report.md
      
      - name: Check Threshold
        run: |
          SCORE=$(cat health_report.json | jq '.overall_score')
          if [ $SCORE -lt 75 ]; then
            echo "Health score below threshold: $SCORE"
            exit 1
          fi
```

## 3. 设置告警阈值

```yaml
# config/health_thresholds.yaml
thresholds:
  overall:
    excellent: 90
    good: 80
    fair: 70
    poor: 60
  
  categories:
    documentation:
      warning: 75
      critical: 60
    scripts:
      warning: 80
      critical: 70
    config:
      warning: 75
      critical: 60

alerts:
  - condition: overall_score < 70
    action: trigger_auto_repair
  - condition: overall_score < 60
    action: send_critical_alert
```

## 4. 健康度基线管理

```python
from skillscripts.core.skill_health_assessor import SkillHealthAssessor

assessor = SkillHealthAssessor(skill_root='./')

assessor.set_baseline(score=85)

report = assessor.assess()

if report.overall_score < assessor.get_baseline():
    deviation = assessor.get_baseline() - report.overall_score
    print(f"健康度低于基线 {deviation} 分")
```

### 5. 健康度历史追踪

```python
from skillscripts.core.skill_health_assessor import HealthHistory

history = HealthHistory(storage_path='./data/health_history')

history.record(report)

trend = history.get_trend(days=30)
print(f"30天趋势: {trend['direction']}")
print(f"平均分数: {trend['average']}")

history.export_report(
    output_path='./reports/health_trend.md',
    format='markdown'
)
```

---

## 配置选项

### 评估配置

```yaml
# config/health_assessment.yaml
assessment:
  categories:
    documentation:
      enabled: true
      weight: 0.25
      checks:
        - skill_md_exists
        - subskill_docs_complete
        - sections_complete
        - format_valid
        - links_valid
    
    scripts:
      enabled: true
      weight: 0.30
      checks:
        - core_scripts_exist
        - syntax_valid
        - imports_valid
        - permissions_correct
    
    config:
      enabled: true
      weight: 0.20
      checks:
        - env_config_complete
        - docker_config_complete
        - skill_config_complete
        - format_valid
    
    paths:
      enabled: true
      weight: 0.15
      checks:
        - core_dirs_exist
        - subdirs_complete
        - permissions_correct
    
    metadata:
      enabled: true
      weight: 0.10
      checks:
        - frontmatter_complete
        - version_info_complete
        - dependencies_declared

  thresholds:
    excellent: 90
    good: 80
    fair: 70
    poor: 60
    critical: 0

  output:
    format: markdown
    include_recommendations: true
    include_issues: true
    include_trend: false
```

---

## 故障排除

### 常见问题

**Q: 评估结果显示分数异常低？**

```bash
# 检查评估日志
python skillscripts/core/skill_health_assessor.py --verbose

# 检查特定类别
python skillscripts/core/skill_health_assessor.py --category documentation --verbose
```

**Q: 评估报告生成失败？**

```bash
# 检查输出目录权限
chmod 755 reports/

# 检查磁盘空间
df -h

# 使用绝对路径
python skillscripts/core/skill_health_assessor.py --output /absolute/path/report.md
```

**Q: 健康度趋势数据丢失？**

```bash
# 检查历史数据目录
ls -la data/health_history/

# 恢复历史数据
python skillscripts/core/skill_health_assessor.py --restore-history
```

---

## 相关文档

- [自迭代机制](self_iteration.md)
- [持续演化系统](continuous_evolution.md)
- [路径配置管理](skill_path_management.md)
- [自动修复系统](../skillscripts/core/skill_auto_repairer.py)

---

> 📌 **提示**：建议定期执行健康度评估，及时发现和解决技能系统中的问题，确保技能始终保持最佳状态。
