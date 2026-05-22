# 自迭代机制说明文档

> 🔄 **持续迭代，自我进化** - 通过自动化工具链实现技能的自我改进和优化

---

## 概述

自迭代机制是 sanliu 技能的核心能力之一，它允许技能通过分析日志、定位问题、自动修复和版本管理来实现持续改进。这一机制确保技能能够在使用过程中不断学习和优化。

### 核心组件

```
┌─────────────────────────────────────────────────────────────────┐
│                      自迭代机制架构                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐     │
│   │ 日志分析器    │───→│ 问题定位器    │───→│ 自动修复器    │     │
│   │ log_analyzer │    │ issue_locator│    │  auto_fixer  │     │
│   └──────────────┘    └──────────────┘    └──────────────┘     │
│          │                   │                   │              │
│          └───────────────────┼───────────────────┘              │
│                              ↓                                  │
│                    ┌──────────────────┐                         │
│                    │   触发条件检测    │                         │
│                    │ trigger_detector │                         │
│                    └──────────────────┘                         │
│                              │                                  │
│                              ↓                                  │
│                    ┌──────────────────┐                         │
│                    │   版本迭代器      │                         │
│                    │ version_iterator │                         │
│                    └──────────────────┘                         │
│                              │                                  │
│                              ↓                                  │
│                    ┌──────────────────┐                         │
│                    │   回滚管理器      │                         │
│                    │ rollback_manager │                         │
│                    └──────────────────┘                         │
│                              │                                  │
│                              ↓                                  │
│                    ┌──────────────────┐                         │
│                    │   迭代历史记录    │                         │
│                    │  version.json    │                         │
│                    └──────────────────┘                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 触发条件检测

### 触发条件类型

| 触发类型 | 说明 | 默认阈值 | 优先级 |
|---------|------|---------|--------|
| `error_rate` | 错误率超过阈值 | 5% | 高 |
| `continuous_failure` | 连续失败次数 | 3次 | 高 |
| `performance_degradation` | 性能下降比例 | 50% | 中 |
| `security_alert` | 安全警告数量 | 1个 | 高 |
| `code_quality` | 代码质量分数低于阈值 | 0.7 | 中 |
| `test_failure` | 测试失败率超过阈值 | 10% | 高 |
| `dependency_update` | 依赖更新数量 | 1个 | 中 |
| `scheduled` | 定时触发 | - | 低 |
| `manual` | 手动触发 | - | 高 |

### 触发条件检测命令

```bash
# 检查触发条件
python scripts/version_iterator.py check \
  --error-rate 0.08 \
  --failures 4 \
  --quality-score 0.6

# 检查并自动触发迭代
python scripts/version_iterator.py check \
  --error-rate 0.1 \
  --trigger

# 输出示例:
# === 迭代触发条件检查 ===
# 需要迭代: 是
# 
# 触发的条件:
#   - error_rate: 当前值 0.1, 阈值 0.05
#     详情: 错误率 10.00% 超过 阈值 5.00%
#   - continuous_failure: 当前值 4.0, 阈值 3
#     详情: 连续失败 4 次 达到 阈值 3
#
# 建议版本升级类型: patch
```

## 编程接口

```python
from scripts.version_iterator import VersionIterator, IterationTriggerType

iterator = VersionIterator(project_root='./')

# 检查是否需要迭代
metrics = {
    'error_rate': 0.08,
    'continuous_failures': 4,
    'code_quality_score': 0.65,
    'security_alerts': [],
    'performance_baseline': {'response_time': 100},
    'current_performance': {'response_time': 180},
    'test_failure_rate': 0.15,
    'dependency_updates': [{'name': 'requests', 'version': '2.28.0'}]
}

result = iterator.check_iteration_needed(metrics)

if result['needs_iteration']:
    print("需要执行自迭代")
    for cond in result['triggered_conditions']:
        print(f"触发条件: {cond['type']}")
    
    # 执行自迭代
    entry = iterator.trigger_iteration(metrics)
    print(f"新版本: {entry.version}")
```

---

## 自迭代触发条件检测详解

### 检测器配置

```python
from scripts.version_iterator import IterationTriggerDetector, IterationTriggerType

# 自定义阈值配置
custom_thresholds = {
    IterationTriggerType.ERROR_RATE: 0.03,
    IterationTriggerType.CONTINUOUS_FAILURE: 2,
    IterationTriggerType.PERFORMANCE_DEGRADATION: 0.3,
    IterationTriggerType.SECURITY_ALERT: 1,
    IterationTriggerType.CODE_QUALITY: 0.8,
    IterationTriggerType.TEST_FAILURE: 0.05,
    IterationTriggerType.DEPENDENCY_UPDATE: 1,
}

detector = IterationTriggerDetector(
    version_manager=iterator.vm,
    thresholds=custom_thresholds
)
```

## 触发条件优先级规则

1. **高优先级** - 立即触发迭代
   - 安全警告 (`security_alert`)
   - 连续失败 (`continuous_failure`)
   - 高错误率 (`error_rate`)
   - 测试失败 (`test_failure`)

2. **中优先级** - 计划迭代
   - 性能下降 (`performance_degradation`)
   - 代码质量 (`code_quality`)
   - 依赖更新 (`dependency_update`)

3. **低优先级** - 可选迭代
   - 定时触发 (`scheduled`)

### 触发条件报告生成

```python
# 生成触发条件报告
triggers = detector.check_all_triggers(metrics)
report = detector.generate_trigger_report(triggers)

print(report)
```

---

## 自迭代执行流程

### 完整迭代流程图

```
触发条件检测
    │
    ├─── 未触发 ──→ 等待下次检查
    │
    ▼ 触发
┌─────────────────────────────────────────────────────────────┐
│ 1. 日志收集与分析                                            │
│    ├─ 收集技能调用日志                                        │
│    ├─ 分析错误模式                                           │
│    └─ 生成错误统计报告                                        │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. 问题定位与诊断                                            │
│    ├─ 解析堆栈跟踪                                           │
│    ├─ 分析影响范围                                           │
│    └─ 生成诊断报告                                           │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. 自动修复                                                   │
│    ├─ 语法错误修复                                           │
│    ├─ 导入问题修复                                           │
│    ├─ 安全问题修复                                           │
│    └─ 代码风格修复                                           │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. 验证与测试                                                │
│    ├─ 语法验证                                               │
│    ├─ 单元测试                                               │
│    └─ 集成测试                                               │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. 版本迭代                                                   │
│    ├─ 确定版本升级类型                                       │
│    ├─ 升级版本号                                             │
│    ├─ 记录变更日志                                           │
│    └─ 生成变更报告                                           │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. 创建快照                                                   │
│    ├─ 保存当前版本状态                                       │
│    ├─ 记录文件哈希                                           │
│    └─ 存储验证信息                                           │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│ 7. 迭代完成                                                   │
│    ├─ 更新版本历史                                           │
│    ├─ 归档修复记录                                           │
│    └─ 准备下一次迭代                                         │
└─────────────────────────────────────────────────────────────┘
```

### 执行流程编程接口

```python
from scripts.self_iteration_trigger import SelfIterationTrigger, MonitoringMetrics

trigger = SelfIterationTrigger(project_root='./')

# 方式1: 自动检测并执行
result = trigger.check_and_trigger(
    auto_execute=True,
    log_dir='./logs',
    test_result_file='./test_results.json'
)

# 方式2: 手动指定指标
metrics = MonitoringMetrics(
    error_rate=0.08,
    continuous_failures=3,
    code_quality_score=0.65,
    security_alerts=[{'type': 'CVE', 'severity': 'high'}]
)

result = trigger.check_and_trigger(metrics=metrics, auto_execute=True)

# 查看触发历史
history = trigger.get_trigger_history(limit=10)

# 获取指标趋势
trend = trigger.get_metrics_trend(hours=24)

# 生成报告
report = trigger.generate_report(output_path='./iteration_report.md')
```

---

## 版本管理增强

### 语义化版本控制 (SemVer 2.0.0)

```
主版本号.次版本号.修订号-预发布版本+构建元数据
   │       │       │        │          │
   │       │       │        │          └─ 构建信息（如：20240329120000）
   │       │       │        └─ 预发布标识（如：alpha.1, beta.2）
   │       │       └─ 修订号（bug修复）
   │       └─ 次版本号（新功能，向后兼容）
   └─ 主版本号（重大变更，不向后兼容）
```

### 版本升级规则

| 变更类型 | 版本升级 | 示例 |
|---------|---------|------|
| 重大变更 (breaking) | MAJOR | 1.0.0 → 2.0.0 |
| 新功能 (feat) | MINOR | 1.0.0 → 1.1.0 |
| Bug修复 (fix) | PATCH | 1.0.0 → 1.0.1 |
| 安全修复 (security) | PATCH | 1.0.0 → 1.0.1 |
| 性能优化 (perf) | PATCH | 1.0.0 → 1.0.1 |
| 重构 (refactor) | PATCH | 1.0.0 → 1.0.1 |
| 文档 (docs) | 不升级 | - |
| 测试 (test) | 不升级 | - |

### 版本约束解析

```python
from scripts.version_iterator import VersionRange, VersionInfo

# 解析版本范围约束
range1 = VersionRange.parse(">=1.0.0,<2.0.0")
range2 = VersionRange.parse("^1.2.3")
range3 = VersionRange.parse("~=1.4.0")

# 检查版本是否满足约束
version = VersionInfo.parse("1.5.0")
print(range1.matches(version))  # True
print(range2.matches(version))  # True
print(range3.matches(version))  # True
```

## 版本分支管理

```python
# 创建版本分支
branch = iterator.vm.create_branch(
    branch_name="feature/new-api",
    base_version="1.2.0",
    description="新API功能开发"
)

# 获取分支信息
branch_info = iterator.vm.get_branch("feature/new-api")

# 合并分支
entry = iterator.vm.merge_branch(
    branch_name="feature/new-api",
    bump_type=VersionBumpType.MINOR
)
```

## 版本发布管理

```python
# 创建版本发布
release = iterator.vm.create_release(
    version="1.3.0",
    release_type="stable",
    release_notes="新功能发布",
    artifacts=["dist/package-1.3.0.tar.gz"]
)

# 标记版本废弃
iterator.vm.deprecate_version(
    version="1.0.0",
    message="请升级到最新版本"
)

# 获取最新稳定版本
latest = iterator.vm.get_latest_stable_version()
```

## 版本文档生成

```python
# 生成版本文档
docs_path = iterator.vm.generate_version_documentation(
    version="1.3.0",
    output_dir="./docs/libs/1.3.0"
)
```

## 版本统计命令

```bash
# 查看版本状态（含详细统计）
python scripts/version_iterator.py status --detailed

# 查看版本统计信息
python scripts/version_iterator.py stats

# 检查版本兼容性
python scripts/version_iterator.py compatibility 1.0.0 2.0.0

# 导出版本历史
python scripts/version_iterator.py export -o version_history.json
```

## 版本统计输出示例

```
# 版本统计信息

## 概览
- 总版本数: 15
- 主版本数: 2
- 次版本数: 5
- 修订版本数: 8
- 预发布版本数: 0

## 变更统计
- 平均每版本变更数: 3.5
- 最近迭代速度: 1.25 版本/周
- 最活跃范围: api

## 变更类型分布
- feat: 25
- fix: 18
- refactor: 8
- docs: 5
- test: 3
```

---

## 回滚机制

### 回滚类型

| 类型 | 说明 | 使用场景 |
|-----|------|---------|
| `version` | 版本回滚 | 回滚到特定版本 |
| `fix` | 修复回滚 | 回滚单个修复 |
| `snapshot` | 快照回滚 | 从快照恢复 |
| `partial` | 部分回滚 | 回滚部分文件 |
| `emergency` | 紧急回滚 | 快速回滚到稳定版本 |

### 回滚命令

```bash
# 创建版本快照
python scripts/rollback_manager.py snapshot -v 1.2.0 -p ./

# 列出所有快照
python scripts/rollback_manager.py snapshots

# 从快照恢复
python scripts/rollback_manager.py restore-snapshot -s SNAP-1.2.0-20240329120000 -p ./

# 分析回滚影响
python scripts/rollback_manager.py impact -v 1.1.0

# 创建回滚计划
python scripts/rollback_manager.py plan -v 1.1.0 -p ./

# 执行回滚计划（需批准）
python scripts/rollback_manager.py plan -v 1.1.0 --approve

# 验证回滚
python scripts/rollback_manager.py verify -b BACKUP-xxx --level thorough

# 查看回滚统计
python scripts/rollback_manager.py stats
```

## 回滚验证级别

| 级别 | 检查项 |
|-----|-------|
| `basic` | 文件存在检查、备份文件完整性 |
| `standard` | basic + 文件哈希验证、配置文件格式 |
| `thorough` | standard + 语法检查、导入检查、测试运行 |

### 回滚影响分析输出

```
=== 回滚影响分析 ===
目标版本: 1.1.0
快照可用: 是
风险等级: low
影响文件数: 25

建议:
  - 建议使用快照恢复
```

---

## 触发条件

### 自动触发条件

| 条件 | 说明 | 优先级 |
|------|------|--------|
| 错误率超过阈值 | 日志中错误率 > 5% | 高 |
| 连续失败次数 | 同一操作连续失败 > 3 次 | 高 |
| 性能下降 | 响应时间超过基线 50% | 中 |
| 安全警告 | 检测到安全漏洞 | 高 |
| 代码异味 | 检测到代码质量问题 | 低 |
| 测试失败率 | 测试失败率 > 10% | 高 |
| 依赖更新 | 有新的依赖更新 | 中 |

### 手动触发条件

```bash
# 手动触发完整迭代流程
python skillscripts/optimization/auto_fixer.py --full

# 仅分析日志
python skillscripts/analysis/log_analyzer.py logs/

# 仅定位问题
python skillscripts/analysis/issue_locator.py --scan-project

# 仅执行修复
python skillscripts/optimization/auto_fixer.py --target ./

# 仅迭代版本
python skillscripts/utils/version_manager.py iterate --auto
```

---

## 执行步骤

### 步骤 1: 日志分析

```bash
# 分析日志文件
python skillscripts/analysis/log_analyzer.py logs/ -o analysis_report.md

# 分析特定日志
python skillscripts/analysis/log_analyzer.py app.log --format json
```

**输出示例：**
```markdown
# 日志分析报告

## 统计概览
- 总日志条目: 1523
- 错误数量: 45
- 警告数量: 128
- 错误率: 2.95%

## 错误模式分析
### E001: ImportError
- **描述**: 模块导入错误
- **出现次数**: 12
- **修复建议**: 检查依赖安装
```

### 步骤 2: 问题定位

```bash
# 从错误文本定位
python skillscripts/analysis/issue_locator.py --error-text "ImportError: No module named 'requests'"

# 扫描整个项目
python skillscripts/analysis/issue_locator.py --scan-project -o diagnosis_report.md

# 定位特定文件
python skillscripts/analysis/issue_locator.py --file app.py --line 42
```

**输出示例：**
```markdown
# 问题诊断报告

## HIGH 优先级问题

### ISSUE-20240329-0001: dependency: 模块 'requests' 未安装
**位置**: app.py:15
**根因分析** (80% 置信度):
模块 'requests' 未安装

**修复建议**:
- 运行: pip install requests

**影响范围**: 高 - 影响API接口
```

### 步骤 3: 自动修复

```bash
# 自动修复文件
python skillscripts/optimization/auto_fixer.py app.py --error "ImportError" --line 15

# 自动修复整个项目
python skillscripts/optimization/auto_fixer.py ./ --project-root ./

# 预览修复（不实际执行）
python skillscripts/optimization/auto_fixer.py app.py --dry-run
```

**修复策略：**

| 策略 | 说明 | 成功率 |
|------|------|--------|
| 语法修复 | 修复语法错误 | 90% |
| 导入修复 | 安装缺失依赖 | 85% |
| 安全修复 | 修复安全问题 | 95% |
| 风格修复 | 格式化代码 | 99% |

## 步骤 4: 版本迭代

```bash
# 自动迭代版本
python skillscripts/utils/version_manager.py iterate --auto

# 指定版本类型
python skillscripts/utils/version_manager.py iterate --type minor

# 添加变更记录
python skillscripts/utils/version_manager.py iterate --change "feat:新增自动修复功能" --change "fix:修复日志解析问题"

# 生成变更日志
python skillscripts/utils/version_manager.py changelog -o CHANGELOG.md
```

**版本号规则：**

```
主版本号.次版本号.修订号-预发布版本+构建元数据
   │       │       │        │          │
   │       │       │        │          └─ 构建信息（如：20240329120000）
   │       │       │        └─ 预发布标识（如：alpha.1, beta.2）
   │       │       └─ 修订号（bug修复）
   │       └─ 次版本号（新功能）
   └─ 主版本号（重大变更）
```

---

## 最佳实践

### 1. 定期执行

```bash
# 添加到定时任务（crontab）
# 每天凌晨 2 点执行迭代检查
0 2 * * * cd /path/to/project && python skillscripts/optimization/auto_fixer.py --check

# 每周日凌晨 3 点执行完整迭代
0 3 * * 0 cd /path/to/project && python skillscripts/optimization/auto_fixer.py --full
```

## 2. 集成到 CI/CD

```yaml
# .github/workflows/self-iteration.yml
name: Self Iteration

on:
  schedule:
    - cron: '0 2 * * *'
  workflow_dispatch:

jobs:
  iterate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Analyze Logs
        run: python skillscripts/analysis/log_analyzer.py logs/ -o reports/analysis.md

      - name: Locate Issues
        run: python skillscripts/analysis/issue_locator.py --scan-project -o reports/issues.md

      - name: Auto Fix
        run: python skillscripts/optimization/auto_fixer.py ./ --dry-run

      - name: Upload Reports
        uses: actions/upload-artifact@v3
        with:
          name: iteration-reports
          path: reports/
```

## 3. 监控与告警

```python
# 监控脚本示例
from scripts.log_analyzer import LogAnalyzer
from scripts.issue_locator import IssueLocator

def monitor_and_alert():
    analyzer = LogAnalyzer()
    result = analyzer.analyze(['logs/'])

    # 错误率超过阈值时告警
    if result.error_count / result.total_entries > 0.05:
        send_alert(f"错误率过高: {result.error_rate:.2f}%")

    # 发现严重问题时触发修复
    critical_patterns = [p for p in result.patterns_found if p.severity == "critical"]
    if critical_patterns:
        trigger_auto_fix()
```

## 4. 版本管理策略

```bash
# 功能开发完成后迭代次版本号
python scripts/version_iterator.py iterate --type minor \
  --change "feat:新增日志分析功能" \
  --change "feat:新增问题定位功能"

# Bug 修复后迭代修订号
python scripts/version_iterator.py iterate --type patch \
  --change "fix:修复日志解析错误" \
  --change "fix:修复导入问题"

# 重大变更时迭代主版本号
python scripts/version_iterator.py iterate --type major \
  --change "breaking:重构核心架构" \
  --notes "此版本包含重大变更，请查看迁移指南"
```

## 5. 回滚策略

```bash
# 查看版本历史
python scripts/version_iterator.py status

# 回滚到上一版本
python scripts/version_iterator.py rollback

# 回滚到指定版本
python scripts/version_iterator.py rollback --to 1.2.3

# 回滚自动修复
python scripts/auto_fixer.py --rollback FIX-20240329-0001

# 回滚所有修复
python scripts/auto_fixer.py --rollback-all
```

---

## 脚本使用指南

### log_analyzer.py - 日志分析脚本

**功能：**
- 分析技能调用日志
- 识别常见错误模式
- 生成错误统计报告
- 支持多种日志格式（JSON、文本、结构化）

**用法：**
```bash
python scripts/log_analyzer.py <日志文件或目录> [选项]

选项：
  -o, --output      报告输出路径
  -f, --format      输出格式 (markdown/json)
  --pattern         日志文件匹配模式 (默认: *.log)
```

**示例：**
```bash
# 分析目录中的所有日志
python scripts/log_analyzer.py logs/ -o reports/analysis.md

# 分析特定文件，JSON输出
python scripts/log_analyzer.py app.log --format json
```

## issue_locator.py - 问题定位脚本

**功能：**
- 自动定位问题根源
- 分析问题影响范围
- 生成问题诊断报告
- 提供修复建议

**用法：**
```bash
python scripts/issue_locator.py [选项]

选项：
  --error-file      包含错误信息的文件
  --error-text      直接提供错误文本
  --file            问题所在文件
  --line            问题所在行号
  --project-root    项目根目录
  --scan-project    扫描整个项目
  -o, --output      报告输出路径
  -f, --format      输出格式
```

**示例：**
```bash
# 从错误文本定位
python scripts/issue_locator.py --error-text "ImportError: No module named 'requests'"

# 扫描项目
python scripts/issue_locator.py --scan-project -o diagnosis.md
```

## auto_fixer.py - 自动修复脚本

**功能：**
- 自动修复常见问题
- 支持多种修复策略
- 生成修复报告
- 记录修复历史

**用法：**
```bash
python scripts/auto_fixer.py <目标文件或目录> [选项]

选项：
  --error           错误信息
  --line            错误所在行号
  --project-root    项目根目录
  --backup-dir      备份目录
  --rollback        回滚指定修复
  --rollback-all    回滚所有修复
  --dry-run         仅预览不执行
```

**示例：**
```bash
# 自动修复项目
python scripts/auto_fixer.py ./ --project-root ./

# 预览修复
python scripts/auto_fixer.py app.py --dry-run

# 回滚修复
python scripts/auto_fixer.py --rollback FIX-20240329-0001
```

## version_iterator.py - 版本迭代脚本

**功能：**
- 管理版本号
- 记录迭代历史
- 生成版本变更日志
- 支持版本回滚

**用法：**
```bash
python scripts/version_iterator.py <命令> [选项]

命令：
  iterate      执行版本迭代
  status       查看版本状态
  rollback     回滚版本
  changelog    生成变更日志
  report       生成迭代报告

选项：
  --type        版本升级类型 (major/minor/patch/prerelease/build)
  --change      变更描述
  --author      迭代作者
  --notes       版本说明
```

**示例：**
```bash
# 自动迭代
python scripts/version_iterator.py iterate --auto

# 指定变更
python scripts/version_iterator.py iterate --type minor \
  --change "feat:新增功能" --change "fix:修复bug"

# 生成变更日志
python scripts/version_iterator.py changelog -o CHANGELOG.md
```

---

## 配置文件

### version.json

版本历史配置文件：

```json
{
  "project_name": "sanliu",
  "current_version": "1.2.3",
  "iteration_count": 15,
  "versions": [
    {
      "version": "1.2.3",
      "previous_version": "1.2.2",
      "timestamp": "2024-03-29T10:30:00",
      "changes": [
        {
          "type": "feat",
          "description": "新增自动修复功能",
          "scope": "scripts",
          "breaking": false
        }
      ],
      "author": "Developer",
      "commit_hash": "abc1234",
      "tag_name": "v1.2.3"
    }
  ]
}
```

---

## 故障排除

### 常见问题

**Q: 日志分析找不到日志文件？**
```bash
# 确保日志目录存在
mkdir -p logs/

# 指定正确的日志路径
python scripts/log_analyzer.py /path/to/logs/
```

**Q: 自动修复失败？**
```bash
# 检查文件权限
chmod +w target_file.py

# 使用预览模式查看问题
python scripts/auto_fixer.py target.py --dry-run

# 查看修复历史
ls -la .fix_backups/
```

**Q: 版本迭代冲突？**
```bash
# 先拉取最新变更
git pull

# 解决冲突后重新迭代
python scripts/version_iterator.py iterate --auto
```

---

## 总结

自迭代机制通过四个核心脚本实现：

1. **log_analyzer.py** - 发现问题
2. **issue_locator.py** - 定位问题
3. **auto_fixer.py** - 修复问题
4. **version_iterator.py** - 记录改进

通过定期执行迭代流程，技能可以持续自我改进，提高稳定性和可靠性。

---

## 新增脚本使用说明

### 协同调用脚本

自迭代机制现已支持协同调用接口，可通过标准化接口与其他技能进行交互。

#### skill_caller.py - 技能调用脚本

**功能：**
- 标准化技能调用接口
- 支持同步和异步调用
- 自动重试和错误处理
- 调用日志记录

**用法：**
```bash
python scripts/skill_caller.py <目标技能> <接口名称> [选项]

参数：
  目标技能        目标技能路径或标识
  接口名称        要调用的接口名称

选项：
  --params        接口参数（JSON格式）
  --async         异步调用模式
  --timeout       超时时间（毫秒）
  --retry         重试次数
  --callback      回调接口地址
```

**示例：**
```bash
# 同步调用中书省需求分析接口
python scripts/skill_caller.py zhongshusheng analyze_requirements \
  --params='{"requirement_text":"构建电商平台"}'

# 异步调用尚书省执行协调接口
python scripts/skill_caller.py shangshusheng coordinate_execution \
  --params='{"project_id":"PROJ-001"}' \
  --async \
  --callback="http://localhost:8080/callback"

# 调用工部代码生成接口
python scripts/skill_caller.py gongbu generate_code \
  --params='{"spec":{"entities":[{"name":"User"}]}}'
```

## skill_registry.py - 技能注册脚本

**功能：**
- 技能注册与发现
- 接口元数据管理
- 技能健康检查
- 调用统计

**用法：**
```bash
python scripts/skill_registry.py <命令> [选项]

命令：
  register        注册新技能
  unregister      注销技能
  list            列出所有技能
  info            查看技能详情
  health          健康检查
  stats           调用统计

选项：
  --skill-id      技能ID
  --skill-path    技能路径
  --interfaces    接口列表（JSON格式）
```

**示例：**
```bash
# 注册新技能
python scripts/skill_registry.py register \
  --skill-id="custom-analyzer" \
  --skill-path=".trae/skills/custom/analyzer/" \
  --interfaces='[{"name":"analyze","description":"分析接口"}]'

# 查看所有技能
python scripts/skill_registry.py list

# 查看技能详情
python scripts/skill_registry.py info --skill-id="zhongshusheng"

# 健康检查
python scripts/skill_registry.py health --skill-id="shangshusheng"
```

## interface_validator.py - 接口验证脚本

**功能：**
- 验证接口参数格式
- 验证输出格式合规性
- 接口契约测试
- 生成接口文档

**用法：**
```bash
python scripts/interface_validator.py <命令> [选项]

命令：
  validate        验证接口调用
  test            执行接口测试
  doc             生成接口文档
  schema          生成参数Schema

选项：
  --skill         技能标识
  --interface     接口名称
  --params        参数文件或JSON
  --expected      期望输出文件
```

**示例：**
```bash
# 验证接口参数
python scripts/interface_validator.py validate \
  --skill="zhongshusheng" \
  --interface="analyze_requirements" \
  --params='{"requirement_text":"测试需求"}'

# 执行接口测试
python scripts/interface_validator.py test \
  --skill="bingbu" \
  --interface="run_tests"

# 生成接口文档
python scripts/interface_validator.py doc \
  --skill="gongbu" \
  --output="docs/interfaces/gongbu.md"
```

## 协同迭代流程

#### 跨技能迭代触发

```bash
# 触发跨技能迭代
python scripts/self_iterate.py --cross-skill \
  --trigger-skill="bingbu" \
  --target-skill="xingbu" \
  --issue-file="reports/issues.json"
```

## 迭代协调器

```bash
# 启动迭代协调器
python scripts/iteration_coordinator.py start \
  --skills='["zhongshusheng","menxiasheng","shangshusheng"]' \
  --mode="sequential"

# 查看迭代状态
python scripts/iteration_coordinator.py status

# 暂停/恢复迭代
python scripts/iteration_coordinator.py pause
python scripts/iteration_coordinator.py resume
```

## 配置文件扩展

#### interfaces.json - 接口配置

```json
{
  "version": "1.0.0",
  "interfaces": {
    "zhongshusheng": {
      "analyze_requirements": {
        "input_schema": "schemas/analyze_requirements_input.json",
        "output_schema": "schemas/analyze_requirements_output.json",
        "timeout_ms": 30000,
        "retry_count": 3
      }
    }
  }
}
```

#### skill_dependencies.json - 技能依赖配置

```json
{
  "version": "1.0.0",
  "dependencies": {
    "shangshusheng": {
      "depends_on": ["zhongshusheng", "menxiasheng"],
      "call_order": ["zhongshusheng", "menxiasheng", "shangshusheng"]
    },
    "gongbu": {
      "depends_on": ["shangshusheng", "bingbu", "liibu"],
      "call_order": ["liibu", "bingbu", "gongbu"]
    }
  }
}
```

---

## 与持续演化系统的集成

自迭代机制与持续演化系统深度集成，形成完整的自我改进闭环。持续演化系统在自迭代机制之上提供更高级的自动化和智能化能力。

### 集成架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    自迭代与持续演化集成架构                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌───────────────────────────────────────────────────────────────────────┐ │
│   │                        持续演化系统 (上层)                              │ │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │ │
│   │  │  监控分析   │  │  策略决策   │  │  效果验证   │  │  趋势预测   │  │ │
│   │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │ │
│   └───────────────────────────────────────────────────────────────────────┘ │
│                              │ 触发/反馈                                     │
│                              ▼                                               │
│   ┌───────────────────────────────────────────────────────────────────────┐ │
│   │                        自迭代机制 (基础层)                              │ │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │ │
│   │  │ 日志分析器  │  │ 问题定位器  │  │ 自动修复器  │  │ 版本迭代器  │  │ │
│   │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │ │
│   └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 集成点说明

| 集成点 | 方向 | 说明 |
|--------|------|------|
| 问题检测 | 演化→迭代 | 演化系统监控到问题后触发自迭代流程 |
| 修复执行 | 迭代→演化 | 自迭代执行修复后反馈到演化系统 |
| 效果验证 | 迭代→演化 | 自迭代完成后由演化系统验证效果 |
| 版本记录 | 迭代→演化 | 自迭代版本迭代信息同步到演化历史 |
| 策略调整 | 演化→迭代 | 演化系统根据历史调整迭代策略 |

### 集成配置

```yaml
evolution_integration:
  enabled: true
  
  trigger_conditions:
    performance_degradation:
      threshold: 0.15
      action: trigger_skill_optimization
    error_rate_spike:
      threshold: 0.05
      action: trigger_self_iteration
    security_alert:
      threshold: 1
      action: trigger_immediate_iteration
  
  feedback_config:
    report_to_evolution: true
    include_metrics: true
    include_changes: true
  
  shared_components:
    problem_detector: true
    version_manager: true
    rollback_manager: true
    metrics_collector: true
```

### 集成使用示例

#### 从演化系统触发自迭代

```python
from scripts.self_iteration_intelligent import SelfIterationOrchestrator
from scripts.evolution_manager import EvolutionManager

iteration_orchestrator = SelfIterationOrchestrator(project_root='./')
evolution_manager = EvolutionManager(project_root='./')

problems = iteration_orchestrator.detector.detect_problems('./src')

should_evolve, evolution_type = evolution_manager.analyze_evolution_need(problems)

if should_evolve:
    if evolution_type == 'skill_optimization':
        result = iteration_orchestrator.run_iteration_cycle(
            target_path='./src',
            auto_trigger=True
        )
        
        evolution_manager.record_iteration_result(
            iteration_id=result['plan']['plan_id'],
            evolution_type=evolution_type,
            metrics_before=result['quality_score'],
            problems_fixed=len(result['problems_detected'])
        )
        
        print(f"自迭代已触发并记录到演化系统: {result['plan']['plan_id']}")
```

#### 自迭代结果反馈到演化系统

```python
from scripts.self_iteration_trigger import SelfIterationTrigger

trigger = SelfIterationTrigger(project_root='./')

result = trigger.check_and_trigger(
    auto_execute=True,
    log_dir='./logs',
    test_result_file='./test_results.json'
)

if result['iteration_performed']:
    from scripts.evolution_manager import EvolutionManager
    evolution_manager = EvolutionManager(project_root='./')
    
    evolution_manager.update_evolution_metrics(
        iteration_id=result['iteration_id'],
        success=result['success'],
        metrics_after=result['metrics_after'],
        changes_made=result['changes_count']
    )
    
    print("自迭代结果已反馈到演化系统")
```

#### 演化系统验证自迭代效果

```python
from scripts.evolution_manager import EvolutionManager

evolution_manager = EvolutionManager(project_root='./')

validation_result = evolution_manager.validate_iteration_effect(
    iteration_id='PLAN-20240329120000',
    metrics_before={'performance': 80, 'error_rate': 0.05},
    metrics_after={'performance': 85, 'error_rate': 0.02}
)

if validation_result['effective']:
    print(f"自迭代效果验证通过，性能提升: {validation_result['improvement']}%")
else:
    print("自迭代效果不明显，建议回滚")
    evolution_manager.trigger_rollback(iteration_id='PLAN-20240329120000')
```

### 集成API

#### 演化系统触发自迭代

```bash
POST /api/evolution/trigger
Content-Type: application/json

{
  "evolution_type": "skill_optimization",
  "reason": "技能性能下降，触发自迭代优化",
  "parameters": {
    "trigger_iteration": true,
    "iteration_target": "./src",
    "iteration_type": "auto"
  }
}
```

#### 查询演化与迭代关联

```bash
GET /api/evolution/history?include_iterations=true
```

**响应示例：**
```json
{
  "total": 10,
  "items": [
    {
      "id": 1,
      "evolution_type": "skill_optimization",
      "status": "completed",
      "linked_iterations": [
        {
          "iteration_id": "PLAN-20240329120000",
          "status": "completed",
          "problems_fixed": 15,
          "success_rate": 0.95
        }
      ]
    }
  ]
}
```

### 集成监控

```yaml
monitoring:
  integration_health:
    check_interval: 60
    metrics:
      - evolution_to_iteration_trigger_rate
      - iteration_to_evolution_feedback_rate
      - integration_latency
      - sync_error_count
  
  alerts:
    integration_failure:
      condition: sync_error_count > 5 in 1h
      severity: high
      notification: [email, slack]
    
    feedback_timeout:
      condition: feedback_delay > 300s
      severity: medium
      notification: [email]
```

### 集成最佳实践

1. **统一问题检测**
   - 使用共享的问题检测器，避免重复检测
   - 检测结果同时服务于自迭代和演化系统

2. **版本同步管理**
   - 自迭代版本变更自动同步到演化历史
   - 演化系统回滚时联动自迭代版本回滚

3. **指标共享**
   - 自迭代指标作为演化决策的输入
   - 演化趋势分析指导自迭代优先级

4. **回滚协调**
   - 演化系统回滚时通知自迭代系统
   - 自迭代回滚时更新演化状态

---

> 📌 **提示**：建议将自迭代机制集成到日常开发流程中，确保技能始终保持最佳状态。

---

## 技能内容自动更新

技能内容自动更新是自迭代机制的核心能力之一，支持技能文档、配置和知识库的自动更新。

### 更新架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        技能内容自动更新架构                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                      变更检测层                                       │   │
│   │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│   │  │ 文件变更监控 │  │ 内容差异分析 │  │ 版本对比器   │              │   │
│   │  │   Watcher    │  │    Diff      │  │   Compare    │              │   │
│   │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                      更新决策层                                       │   │
│   │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│   │  │ 更新策略选择 │  │ 影响范围评估 │  │ 优先级排序   │              │   │
│   │  │   Strategy   │  │   Impact     │  │  Priority    │              │   │
│   │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                      更新执行层                                       │   │
│   │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│   │  │ 文档更新器   │  │ 配置更新器   │  │ 知识库更新器 │              │   │
│   │  │    Doc       │  │   Config     │  │  Knowledge   │              │   │
│   │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                      验证反馈层                                       │   │
│   │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│   │  │ 格式验证器   │  │ 内容验证器   │  │ 反馈收集器   │              │   │
│   │  │   Format     │  │   Content    │  │   Feedback   │              │   │
│   │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 更新类型

| 更新类型 | 说明 | 触发条件 | 自动执行 |
|----------|------|----------|----------|
| `documentation` | 文档更新 | 内容变更、格式修正 | 是 |
| `configuration` | 配置更新 | 参数优化、结构调整 | 需审批 |
| `knowledge_base` | 知识库更新 | 新知识积累、规则更新 | 是 |
| `template` | 模板更新 | 模板优化、新增模板 | 需审批 |

### 使用示例

#### 自动更新技能文档

```python
from scripts.skill_content_updater import SkillContentUpdater

updater = SkillContentUpdater(skill_root='./')

result = updater.update_documentation(
    doc_type='subskill',
    doc_name='test_skill',
    update_source='logs/interactions.json',
    auto_apply=True
)

print(f"更新状态: {result['status']}")
print(f"变更数量: {len(result['changes'])}")
for change in result['changes']:
    print(f"  - {change['type']}: {change['description']}")
```

#### 命令行更新

```bash
python scripts/skill_content_updater.py update \
  --type documentation \
  --target subskills/test.md \
  --source logs/interactions.json \
  --auto-apply

python scripts/skill_content_updater.py update \
  --type configuration \
  --target config/skill.yaml \
  --dry-run
```

### 更新配置

```yaml
skill_content_update:
  enabled: true
  
  auto_update:
    documentation: true
    knowledge_base: true
    configuration: false
    template: false
  
  validation:
    format_check: true
    content_check: true
    link_check: true
  
  backup:
    enabled: true
    retention_days: 30
  
  notification:
    on_update: true
    on_failure: true
```

---

## 文档更新器使用指南

文档更新器是技能内容自动更新的核心工具，提供完整的文档管理和更新能力。

### 核心功能

#### 1. 文档变更检测

```python
from scripts.doc_updater import DocChangeDetector

detector = DocChangeDetector(skill_root='./')

changes = detector.detect_changes(
    doc_path='subskills/test.md',
    baseline_version='1.0.0'
)

print(f"检测到 {len(changes)} 处变更")
for change in changes:
    print(f"  [{change['type']}] {change['location']}")
    print(f"    旧内容: {change['old_content'][:50]}...")
    print(f"    新内容: {change['new_content'][:50]}...")
```

#### 2. 文档差异分析

```python
from scripts.doc_updater import DocDiffAnalyzer

analyzer = DocDiffAnalyzer()

diff = analyzer.analyze(
    old_content=old_doc_content,
    new_content=new_doc_content
)

print(f"新增段落: {diff['added_paragraphs']}")
print(f"删除段落: {diff['removed_paragraphs']}")
print(f"修改段落: {diff['modified_paragraphs']}")
print(f"相似度: {diff['similarity']:.2%}")
```

#### 3. 文档格式验证

```python
from scripts.doc_updater import DocFormatValidator

validator = DocFormatValidator()

result = validator.validate(
    doc_path='subskills/test.md',
    rules=['markdown', 'links', 'headers', 'code_blocks']
)

if result['valid']:
    print("文档格式验证通过")
else:
    print("验证失败:")
    for error in result['errors']:
        print(f"  - 行 {error['line']}: {error['message']}")
```

### 文档更新器命令

#### 基本命令

```bash
python scripts/doc_updater.py detect \
  --doc subskills/test.md \
  --baseline v1.0.0

python scripts/doc_updater.py diff \
  --old docs/old_version.md \
  --new docs/new_version.md

python scripts/doc_updater.py validate \
  --doc subskills/test.md \
  --rules markdown,links,headers

python scripts/doc_updater.py update \
  --doc subskills/test.md \
  --changes changes.json \
  --backup
```

#### 批量操作

```bash
python scripts/doc_updater.py batch-validate \
  --docs subskills/*.md \
  --report validation_report.json

python scripts/doc_updater.py batch-update \
  --manifest update_manifest.yaml \
  --dry-run
```

### 文档更新流程

```
文档更新流程:

┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   1. 变更检测 ──▶ 2. 差异分析 ──▶ 3. 格式验证 ──▶ 4. 内容验证              │
│       │              │              │              │                        │
│       ▼              ▼              ▼              ▼                        │
│   ┌───────┐      ┌───────┐      ┌───────┐      ┌───────┐                  │
│   │文件   │      │内容   │      │格式   │      │语义   │                  │
│   │监控   │      │对比   │      │检查   │      │检查   │                  │
│   │时间戳 │      │差异   │      │规范   │      │逻辑   │                  │
│   │哈希   │      │合并   │      │链接   │      │完整   │                  │
│   └───────┘      └───────┘      └───────┘      └───────┘                  │
│                                                                             │
│   5. 备份创建 ──▶ 6. 应用更新 ──▶ 7. 验证结果 ──▶ 8. 记录历史              │
│       │              │              │              │                        │
│       ▼              ▼              ▼              ▼                        │
│   ┌───────┐      ┌───────┐      ┌───────┐      ┌───────┐                  │
│   │原文件 │      │写入   │      │测试   │      │版本   │                  │
│   │备份   │      │更新   │      │验证   │      │记录   │                  │
│   │时间戳 │      │原子   │      │功能   │      │变更   │                  │
│   │标记   │      │操作   │      │检查   │      │日志   │                  │
│   └───────┘      └───────┘      └───────┘      └───────┘                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 文档更新配置

```yaml
doc_updater:
  detection:
    watch_enabled: true
    watch_interval: 60
    hash_algorithm: sha256
  
  validation:
    rules:
      - name: markdown
        enabled: true
        strict: false
      - name: links
        enabled: true
        check_external: false
      - name: headers
        enabled: true
        max_level: 6
      - name: code_blocks
        enabled: true
        check_syntax: true
  
  backup:
    enabled: true
    directory: "./.doc_backups"
    retention_days: 30
    max_backups: 100
  
  update:
    atomic: true
    create_if_missing: true
    preserve_permissions: true
```

---

## 回滚机制详解

回滚机制是自迭代系统的重要安全保障，支持多种回滚方式和精细化的回滚控制。

### 回滚类型

| 回滚类型 | 说明 | 使用场景 | 数据丢失风险 |
|----------|------|----------|--------------|
| `full_rollback` | 完全回滚 | 重大故障恢复 | 无 |
| `partial_rollback` | 部分回滚 | 局部问题修复 | 低 |
| `selective_rollback` | 选择性回滚 | 特定文件恢复 | 可控 |
| `emergency_rollback` | 紧急回滚 | 系统崩溃恢复 | 无 |

### 回滚管理器使用

#### 创建回滚点

```python
from scripts.rollback_manager import RollbackManager

manager = RollbackManager(project_root='./')

checkpoint = manager.create_checkpoint(
    checkpoint_type='pre_update',
    description='更新前备份',
    include_files=['subskills/', 'config/', 'resources/']
)

print(f"检查点ID: {checkpoint.checkpoint_id}")
print(f"包含文件: {checkpoint.file_count}")
print(f"总大小: {checkpoint.total_size} 字节")
```

#### 执行回滚

```python
from scripts.rollback_manager import RollbackManager, RollbackType

manager = RollbackManager(project_root='./')

result = manager.rollback(
    checkpoint_id='CP-20240329120000',
    rollback_type=RollbackType.FULL,
    verify_after=True,
    create_backup=True
)

if result['success']:
    print("回滚成功")
    print(f"恢复文件: {result['restored_files']}")
    print(f"验证状态: {result['verification_status']}")
else:
    print(f"回滚失败: {result['error']}")
```

#### 选择性回滚

```python
result = manager.selective_rollback(
    checkpoint_id='CP-20240329120000',
    files=[
        'subskills/test.md',
        'config/skill.yaml'
    ],
    verify_after=True
)
```

### 回滚命令行工具

#### 检查点管理

```bash
python scripts/rollback_manager.py checkpoint create \
  --type pre_update \
  --description "更新前备份" \
  --include subskills/,config/,resources/

python scripts/rollback_manager.py checkpoint list \
  --limit 20 \
  --type pre_update

python scripts/rollback_manager.py checkpoint info \
  --id CP-20240329120000

python scripts/rollback_manager.py checkpoint delete \
  --id CP-20240329120000 \
  --force
```

#### 回滚执行

```bash
python scripts/rollback_manager.py rollback \
  --checkpoint CP-20240329120000 \
  --type full \
  --verify

python scripts/rollback_manager.py rollback \
  --checkpoint CP-20240329120000 \
  --type selective \
  --files subskills/test.md,config/skill.yaml

python scripts/rollback_manager.py rollback \
  --version 1.2.0 \
  --type full
```

#### 回滚验证

```bash
python scripts/rollback_manager.py verify \
  --checkpoint CP-20240329120000 \
  --level thorough

python scripts/rollback_manager.py compare \
  --checkpoint CP-20240329120000 \
  --current
```

### 回滚验证级别

```
回滚验证级别:

┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   Level 1: Basic (基础验证)                                                 │
│   ├─ 文件存在检查                                                           │
│   ├─ 文件数量验证                                                           │
│   └─ 备份完整性检查                                                         │
│                                                                             │
│   Level 2: Standard (标准验证)                                              │
│   ├─ Basic 验证                                                             │
│   ├─ 文件哈希验证                                                           │
│   ├─ 配置文件格式验证                                                       │
│   └─ 目录结构验证                                                           │
│                                                                             │
│   Level 3: Thorough (彻底验证)                                              │
│   ├─ Standard 验证                                                          │
│   ├─ 语法检查                                                               │
│   ├─ 导入检查                                                               │
│   ├─ 测试运行                                                               │
│   └─ 功能验证                                                               │
│                                                                             │
│   Level 4: Complete (完整验证)                                              │
│   ├─ Thorough 验证                                                          │
│   ├─ 集成测试                                                               │
│   ├─ 性能基准测试                                                           │
│   └─ 安全扫描                                                               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 回滚配置

```yaml
rollback:
  enabled: true
  
  checkpoint:
    auto_create: true
    auto_create_triggers:
      - before_update
      - before_major_change
      - scheduled_daily
    retention_days: 90
    max_checkpoints: 100
    compression: true
  
  rollback:
    default_type: full
    verify_after: true
    verify_level: standard
    create_backup_before: true
  
  emergency:
    enabled: true
    auto_trigger_conditions:
      - error_rate > 0.5
      - system_crash
    fallback_checkpoint: last_stable
  
  notification:
    on_checkpoint_create: false
    on_rollback: true
    on_rollback_failure: true
```

### 回滚历史与审计

```python
from scripts.rollback_manager import RollbackHistory

history = RollbackHistory(project_root='./')

records = history.get_rollback_records(days=30)

print(f"30天内回滚记录: {len(records)} 次")
for record in records:
    print(f"  [{record['timestamp']}] {record['type']}")
    print(f"    原因: {record['reason']}")
    print(f"    结果: {'成功' if record['success'] else '失败'}")

stats = history.get_statistics(days=30)
print(f"成功率: {stats['success_rate']:.2%}")
print(f"平均恢复时间: {stats['avg_recovery_time']}秒")
```

### 回滚最佳实践

#### 1. 定期创建检查点

```bash
python scripts/rollback_manager.py checkpoint create \
  --type scheduled \
  --description "每日自动备份" \
  --cron "0 2 * * *"
```

#### 2. 更新前自动备份

```python
from scripts.rollback_manager import auto_checkpoint

@auto_checkpoint(description="更新前自动备份")
def update_skill_content(skill_id, updates):
    pass
```

#### 3. 回滚演练

```bash
python scripts/rollback_manager.py drill \
  --checkpoint CP-20240329120000 \
  --dry-run \
  --report drill_report.json
```

#### 4. 回滚影响评估

```python
from scripts.rollback_manager import RollbackImpactAnalyzer

analyzer = RollbackImpactAnalyzer(project_root='./')

impact = analyzer.analyze(
    checkpoint_id='CP-20240329120000',
    target_version='1.1.0'
)

print(f"影响文件: {impact['affected_files']}")
print(f"数据丢失风险: {impact['data_loss_risk']}")
print(f"建议: {impact['recommendations']}")
```

---

## 相关文档

- [持续演化系统](continuous_evolution.md)
- [知识库管理](knowledge_base.md)
- [路径配置管理](skill_path_management.md)
- [脚本协同调用](skill_script_coordination.md)

---

## 自优化机制

自优化机制是自迭代能力的核心组成部分，通过持续监控和分析系统性能，自动识别优化机会并执行优化操作。

### 优化类型

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          自优化机制架构                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                      性能监控层                                       │   │
│   │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│   │  │ 响应时间监控 │  │ 资源使用监控 │  │ 吞吐量监控   │              │   │
│   │  │  Latency     │  │  Resource    │  │  Throughput  │              │   │
│   │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                      优化分析层                                       │   │
│   │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│   │  │ 瓶颈识别器   │  │ 优化机会检测 │  │ 影响评估器   │              │   │
│   │  │  Bottleneck  │  │ Opportunity  │  │   Impact     │              │   │
│   │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                      优化执行层                                       │   │
│   │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│   │  │ 代码优化器   │  │ 配置优化器   │  │ 资源优化器   │              │   │
│   │  │   Code       │  │   Config     │  │  Resource    │              │   │
│   │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 优化策略

| 策略类型 | 说明 | 触发条件 | 优化措施 |
|----------|------|----------|----------|
| `code_optimization` | 代码优化 | 性能下降 > 20% | 算法优化、循环优化、缓存添加 |
| `config_optimization` | 配置优化 | 配置不当检测 | 参数调优、阈值调整 |
| `resource_optimization` | 资源优化 | 资源利用率异常 | 内存优化、连接池调整 |
| `query_optimization` | 查询优化 | 查询性能下降 | 索引优化、查询重写 |
| `cache_optimization` | 缓存优化 | 缓存命中率低 | 缓存策略调整、预热优化 |

### 使用示例

#### 命令行执行优化

```bash
python scripts/self_optimizer.py optimize \
  --target ./src \
  --type code_optimization \
  --auto-apply
```

**输出示例：**
```
=== 自优化执行报告 ===

优化类型: code_optimization
目标路径: ./src

检测到的优化机会:
  1. [HIGH] 循环优化: src/utils/parser.py:45
     - 问题: 嵌套循环复杂度 O(n²)
     - 建议: 使用字典查找替代，复杂度降为 O(n)
     - 预期提升: 60%
  
  2. [MEDIUM] 缓存优化: src/api/client.py:120
     - 问题: 重复计算相同结果
     - 建议: 添加 @lru_cache 装饰器
     - 预期提升: 40%

已应用优化: 2 个
性能提升: 平均 45%
```

#### 编程接口

```python
from scripts.self_optimizer import SelfOptimizer, OptimizationType

optimizer = SelfOptimizer(project_root='./')

result = optimizer.analyze_optimization_opportunities(
    target_path='./src',
    optimization_types=[
        OptimizationType.CODE,
        OptimizationType.CACHE,
        OptimizationType.QUERY
    ]
)

for opportunity in result['opportunities']:
    print(f"[{opportunity['priority']}] {opportunity['description']}")
    print(f"  预期提升: {opportunity['expected_improvement']}%")

if result['has_opportunities']:
    apply_result = optimizer.apply_optimizations(
        opportunities=result['opportunities'][:5],
        auto_rollback=True
    )
    print(f"应用优化: {apply_result['applied_count']} 个")
```

### 优化配置

```yaml
self_optimization:
  enabled: true
  
  monitoring:
    metrics_collection_interval: 60
    performance_baseline_update: daily
    anomaly_detection_sensitivity: medium
  
  triggers:
    performance_degradation:
      threshold: 0.20
      action: analyze_and_optimize
    resource_usage_spike:
      threshold: 0.85
      action: resource_optimization
    cache_hit_rate_low:
      threshold: 0.60
      action: cache_optimization
  
  strategies:
    code_optimization:
      enabled: true
      auto_apply: false
      require_approval: true
    config_optimization:
      enabled: true
      auto_apply: true
      require_approval: false
    resource_optimization:
      enabled: true
      auto_apply: true
      require_approval: false
  
  safety:
    max_optimizations_per_run: 10
    rollback_on_regression: true
    performance_test_after_optimize: true
```

---

## 自修复机制

自修复机制通过自动检测和修复系统问题，确保系统稳定运行。

### 修复流程

```
自修复流程:

┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   问题检测 ──▶ 问题分类 ──▶ 策略选择 ──▶ 修复执行 ──▶ 效果验证              │
│       │           │           │           │           │                    │
│       ▼           ▼           ▼           ▼           ▼                    │
│   ┌───────┐   ┌───────┐   ┌───────┐   ┌───────┐   ┌───────┐              │
│   │日志   │   │语法   │   │策略   │   │备份   │   │测试   │              │
│   │分析   │   │检查   │   │匹配   │   │原文件 │   │验证   │              │
│   │指标   │   │静态   │   │优先   │   │应用   │   │对比   │              │
│   │监控   │   │分析   │   │排序   │   │修复   │   │指标   │              │
│   └───────┘   └───────┘   └───────┘   └───────┘   └───────┘              │
│                                                                             │
│   验证失败 ──▶ 回滚修复 ──▶ 记录失败 ──▶ 人工通知                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 修复策略

| 策略 | 问题类型 | 修复方式 | 成功率 |
|------|----------|----------|--------|
| `syntax_fix` | 语法错误 | 自动修正语法 | 95% |
| `import_fix` | 导入错误 | 安装依赖/修正路径 | 85% |
| `type_fix` | 类型错误 | 类型转换/注解修正 | 80% |
| `security_fix` | 安全漏洞 | 应用安全补丁 | 90% |
| `performance_fix` | 性能问题 | 优化代码/配置 | 75% |
| `dependency_fix` | 依赖冲突 | 版本调整/替代方案 | 70% |

### 使用示例

#### 自动修复命令

```bash
python scripts/self_healer.py heal \
  --target ./src \
  --strategies syntax_fix,import_fix,security_fix \
  --auto-rollback
```

**输出示例：**
```
=== 自修复执行报告 ===

扫描路径: ./src
问题检测中...

检测到的问题:
  1. [CRITICAL] 安全漏洞: src/auth/login.py:45
     - 类型: SQL注入风险
     - 策略: security_fix
     - 状态: 待修复
  
  2. [HIGH] 导入错误: src/utils/helper.py:12
     - 类型: 模块未找到
     - 策略: import_fix
     - 状态: 待修复
  
  3. [MEDIUM] 语法警告: src/api/routes.py:89
     - 类型: 未使用变量
     - 策略: syntax_fix
     - 状态: 待修复

执行修复中...
  ✓ [CRITICAL] src/auth/login.py:45 - 安全漏洞已修复
  ✓ [HIGH] src/utils/helper.py:12 - 导入错误已修复
  ✓ [MEDIUM] src/api/routes.py:89 - 语法警告已修复

验证修复效果...
  ✓ 所有测试通过
  ✓ 无新错误产生

修复统计:
  总问题: 3
  已修复: 3
  失败: 0
  成功率: 100%
```

#### 编程接口

```python
from scripts.self_healer import SelfHealer, FixStrategy

healer = SelfHealer(project_root='./')

issues = healer.detect_issues(
    target_path='./src',
    issue_types=['syntax', 'import', 'security']
)

print(f"检测到 {len(issues)} 个问题")

result = healer.heal_issues(
    issues=issues,
    strategies=[
        FixStrategy.SYNTAX_FIX,
        FixStrategy.IMPORT_FIX,
        FixStrategy.SECURITY_FIX
    ],
    auto_rollback=True,
    validate_after_fix=True
)

print(f"修复成功: {result['fixed_count']}")
print(f"修复失败: {result['failed_count']}")

for fix in result['fixes']:
    print(f"  {fix['file']}:{fix['line']} - {fix['strategy']}")
```

### 修复配置

```yaml
self_healing:
  enabled: true
  
  detection:
    scan_on_startup: true
    scan_interval: 3600
    scan_patterns:
      - "**/*.py"
      - "**/*.js"
      - "**/*.ts"
  
  strategies:
    syntax_fix:
      enabled: true
      auto_apply: true
      priority: high
    import_fix:
      enabled: true
      auto_apply: true
      priority: high
    security_fix:
      enabled: true
      auto_apply: false
      priority: critical
      require_approval: true
    performance_fix:
      enabled: true
      auto_apply: false
      priority: medium
  
  safety:
    backup_before_fix: true
    backup_dir: "./.healing/backups"
    max_fixes_per_run: 20
    rollback_on_failure: true
    validate_after_fix: true
  
  notification:
    on_fix_applied: true
    on_fix_failed: true
    on_critical_issue: true
```

### 修复历史管理

```bash
python scripts/self_healer.py history --limit 10

python scripts/self_healer.py rollback --fix-id FIX-20240329-0001

python scripts/self_healer.py stats
```

---

## 自完善机制

自完善机制通过持续学习和改进，使系统不断进化，提升整体质量。

### 完善维度

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          自完善机制架构                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                      学习层                                          │   │
│   │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│   │  │ 模式学习器   │  │ 最佳实践提取 │  │ 经验积累器   │              │   │
│   │  │   Pattern    │  │ BestPractice │  │  Experience  │              │   │
│   │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                      改进层                                          │   │
│   │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│   │  │ 代码质量提升 │  │ 文档完善     │  │ 测试覆盖增强 │              │   │
│   │  │   Quality    │  │ Documentation│  │   Coverage   │              │   │
│   │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                      反馈层                                          │   │
│   │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│   │  │ 效果评估器   │  │ 反馈收集器   │  │ 知识更新器   │              │   │
│   │  │  Evaluation  │  │   Feedback   │  │   Knowledge  │              │   │
│   │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 完善类型

| 类型 | 说明 | 触发条件 | 改进措施 |
|------|------|----------|----------|
| `code_quality` | 代码质量提升 | 质量分数下降 | 重构、简化、规范化 |
| `documentation` | 文档完善 | 文档缺失/过时 | 自动生成、更新文档 |
| `test_coverage` | 测试覆盖增强 | 覆盖率低于阈值 | 生成测试用例 |
| `error_handling` | 错误处理改进 | 异常处理不当 | 添加异常处理 |
| `logging` | 日志完善 | 日志不足/过多 | 调整日志级别和内容 |

### 使用示例

#### 执行自完善

```bash
python scripts/self_improver.py improve \
  --target ./src \
  --dimensions code_quality,documentation,test_coverage \
  --auto-apply
```

**输出示例：**
```
=== 自完善执行报告 ===

完善维度: code_quality, documentation, test_coverage
目标路径: ./src

代码质量改进:
  1. [HIGH] 复杂度降低: src/core/processor.py
     - 问题: 圈复杂度 15 (阈值 10)
     - 改进: 提取方法，复杂度降为 8
     - 状态: 已应用
  
  2. [MEDIUM] 重复代码消除: src/utils/
     - 问题: 检测到 5 处重复代码
     - 改进: 提取公共方法
     - 状态: 已应用

文档完善:
  1. [HIGH] 缺失文档: src/api/client.py
     - 问题: 12 个函数缺少文档字符串
     - 改进: 自动生成文档字符串
     - 状态: 已应用
  
  2. [MEDIUM] README 更新: README.md
     - 问题: 使用示例过时
     - 改进: 更新使用示例
     - 状态: 已应用

测试覆盖增强:
  1. [HIGH] 覆盖率提升: src/core/
     - 当前: 65%
     - 目标: 80%
     - 生成测试用例: 15 个
     - 新覆盖率: 82%
     - 状态: 已应用

完善统计:
  代码质量改进: 2 项
  文档完善: 2 项
  测试覆盖增强: 1 项
  总改进: 5 项
```

#### 编程接口

```python
from scripts.self_improver import SelfImprover, ImprovementDimension

improver = SelfImprover(project_root='./')

analysis = improver.analyze_improvement_needs(
    target_path='./src',
    dimensions=[
        ImprovementDimension.CODE_QUALITY,
        ImprovementDimension.DOCUMENTATION,
        ImprovementDimension.TEST_COVERAGE
    ]
)

print(f"需要改进: {len(analysis['improvements'])} 项")

result = improver.apply_improvements(
    improvements=analysis['improvements'],
    auto_rollback=True,
    validate_after_apply=True
)

print(f"已应用改进: {result['applied_count']} 项")
print(f"质量分数: {analysis['quality_before']} -> {result['quality_after']}")
```

### 完善配置

```yaml
self_improvement:
  enabled: true
  
  dimensions:
    code_quality:
      enabled: true
      metrics:
        - cyclomatic_complexity
        - code_duplication
        - maintainability_index
      thresholds:
        cyclomatic_complexity: 10
        code_duplication: 0.05
        maintainability_index: 0.7
    
    documentation:
      enabled: true
      auto_generate: true
      update_readme: true
      docstring_style: google
    
    test_coverage:
      enabled: true
      target_coverage: 0.80
      auto_generate_tests: true
      test_framework: pytest
  
  learning:
    enabled: true
    pattern_learning: true
    best_practice_extraction: true
    knowledge_base_update: true
  
  feedback:
    collect_user_feedback: true
    track_improvement_effect: true
    adjust_strategy_automatically: true
  
  schedule:
    analysis_interval: 86400
    improvement_interval: 604800
    max_improvements_per_run: 10
```

### 完善效果追踪

```python
from scripts.self_improver import ImprovementTracker

tracker = ImprovementTracker(project_root='./')

history = tracker.get_improvement_history(days=30)

print(f"30天内改进统计:")
print(f"  代码质量提升: {history['code_quality_improvements']} 次")
print(f"  文档完善: {history['documentation_improvements']} 次")
print(f"  测试覆盖增强: {history['test_coverage_improvements']} 次")

trend = tracker.get_quality_trend(days=30)
print(f"质量分数趋势: {trend['start_score']} -> {trend['end_score']}")
print(f"提升幅度: {trend['improvement']}%")
```

---

## 三大机制协同工作

自优化、自修复、自完善三大机制协同工作，形成完整的自我进化能力。

### 协同架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        三大机制协同架构                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│                          ┌─────────────────┐                               │
│                          │   监控触发器     │                               │
│                          │    Trigger      │                               │
│                          └────────┬────────┘                               │
│                                   │                                         │
│              ┌────────────────────┼────────────────────┐                   │
│              │                    │                    │                   │
│              ▼                    ▼                    ▼                   │
│   ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐          │
│   │   自优化机制     │  │   自修复机制     │  │   自完善机制     │          │
│   │                 │  │                 │  │                 │          │
│   │  性能监控       │  │  问题检测       │  │  质量分析       │          │
│   │  瓶颈识别       │  │  策略匹配       │  │  改进识别       │          │
│   │  优化执行       │  │  修复执行       │  │  完善执行       │          │
│   └────────┬────────┘  └────────┬────────┘  └────────┬────────┘          │
│            │                    │                    │                    │
│            └────────────────────┼────────────────────┘                    │
│                                 │                                          │
│                                 ▼                                          │
│                    ┌─────────────────────────┐                            │
│                    │     知识库更新          │                            │
│                    │   Knowledge Update      │                            │
│                    └─────────────────────────┘                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 协同配置

```yaml
mechanism_coordination:
  enabled: true
  
  priority_order:
    - self_healing
    - self_optimization
    - self_improvement
  
  shared_components:
    - problem_detector
    - metrics_collector
    - knowledge_base
    - rollback_manager
  
  coordination_rules:
    - condition: critical_issue_detected
      actions:
        - pause_optimization
        - trigger_healing
        - notify_admin
    
    - condition: healing_completed
      actions:
        - validate_fix
        - update_knowledge
        - resume_optimization
    
    - condition: optimization_regression
      actions:
        - rollback_optimization
        - trigger_healing
        - analyze_root_cause
```

### 协同使用示例

```python
from scripts.mechanism_coordinator import MechanismCoordinator

coordinator = MechanismCoordinator(project_root='./')

coordinator.start_coordinated_monitoring(
    enable_optimization=True,
    enable_healing=True,
    enable_improvement=True
)

status = coordinator.get_status()
print(f"优化状态: {status['optimization']['status']}")
print(f"修复状态: {status['healing']['status']}")
print(f"完善状态: {status['improvement']['status']}")

coordinator.stop_coordinated_monitoring()
```

---

> 📌 **提示**：建议将自迭代机制集成到日常开发流程中，确保技能始终保持最佳状态。
