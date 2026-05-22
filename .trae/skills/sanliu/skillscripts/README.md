# 三省六部协同开发系统 - 脚本目录

本目录包含三省六部协同开发系统的所有管理、分析和优化脚本。

## 目录结构

```
skillscripts/
├── core/                    # 核心流程脚本
├── pipeline/                # 流水线脚本
├── test/                    # 测试脚本
├── analysis/                # 分析脚本
├── optimization/            # 优化脚本
├── requirements/            # 需求脚本
└── utils/                   # 工具脚本
```

## 脚本规范

### 统一参数规范

所有脚本支持以下通用参数：

```bash
--json           # JSON 格式输出
--markdown       # Markdown 格式输出
-v, --verbose    # 详细输出模式
-q, --quiet      # 静默模式（仅输出错误）
--output-file    # 输出文件路径
```

### 统一退出码规范

| 退出码 | 含义 | 说明 |
|--------|------|------|
| 0 | 成功 | 脚本执行成功，无错误 |
| 1 | 错误 | 脚本执行失败 |
| 2 | 警告 | 部分操作失败，但整体可接受 |

### 统一输出格式

脚本支持三种输出格式：

1. **控制台输出**（默认）：带图标和格式的可读输出
2. **JSON 输出**（`--json`）：结构化 JSON 数据
3. **Markdown 输出**（`--markdown`）：Markdown 格式报告

## 脚本分类

### 核心流程脚本 (core/)

| 脚本 | 功能 | 示例 |
|------|------|------|
| [provincial_coordinator.py](core/provincial_coordinator.py) | 省部司协同调用 | `python core/provincial_coordinator.py --create-task` |
| [start_services.py](core/start_services.py) | 启动所有服务 | `python core/start_services.py` |
| [stop_services.py](core/stop_services.py) | 停止所有服务 | `python core/stop_services.py --all` |
| [health_check.py](core/health_check.py) | 系统健康检查 | `python core/health_check.py --json` |
| [check_environment.py](core/check_environment.py) | 环境依赖检查 | `python core/check_environment.py` |
| [docker_manager.py](core/docker_manager.py) | Docker 容器管理 | `python core/docker_manager.py status` |
| [init_db.py](core/init_db.py) | 数据库初始化 | `python core/init_db.py --reset` |
| [query_status.py](core/query_status.py) | 系统状态查询 | `python core/query_status.py --dashboard` |
| [assign_agent.py](core/assign_agent.py) | Agent 分配 | `python core/assign_agent.py --role 兵部` |
| [agent_selector.py](core/agent_selector.py) | Agent 选择器 | `python core/agent_selector.py` |
| [record_skill_call.py](core/record_skill_call.py) | 技能调用记录 | `python core/record_skill_call.py --skill sanliu` |

### 流水线脚本 (pipeline/)

| 脚本 | 功能 | 示例 |
|------|------|------|
| [automated_pipeline.py](pipeline/automated_pipeline.py) | 自动化流水线 | `python pipeline/automated_pipeline.py` |
| [sdd_cli.py](pipeline/sdd_cli.py) | SDD命令行工具 | `python pipeline/sdd_cli.py generate` |
| [sdd_code_generator.py](pipeline/sdd_code_generator.py) | SDD代码生成 | `python pipeline/sdd_code_generator.py spec.md` |
| [sdd_spec_parser.py](pipeline/sdd_spec_parser.py) | SDD规范解析 | `python pipeline/sdd_spec_parser.py spec.md` |
| [sdd_tdd_cycle.py](pipeline/sdd_tdd_cycle.py) | SDD-TDD循环 | `python pipeline/sdd_tdd_cycle.py --phase red` |
| [tdd_blue_refactoring_pipeline.py](pipeline/tdd_blue_refactoring_pipeline.py) | TDD蓝阶段重构 | `python pipeline/tdd_blue_refactoring_pipeline.py` |
| [code_review_automation.py](pipeline/code_review_automation.py) | 代码审查自动化 | `python pipeline/code_review_automation.py` |
| [doc_generator.py](pipeline/doc_generator.py) | 文档生成 | `python pipeline/doc_generator.py` |
| [ui_ux_integration.py](pipeline/ui_ux_integration.py) | UI/UX集成 | `python pipeline/ui_ux_integration.py` |

### 测试脚本 (test/)

| 脚本 | 功能 | 示例 |
|------|------|------|
| [intelligent_test_generator.py](test/intelligent_test_generator.py) | 智能测试生成 | `python test/intelligent_test_generator.py src/` |
| [sdd_test_generator.py](test/sdd_test_generator.py) | SDD测试生成 | `python test/sdd_test_generator.py spec.md` |
| [sdd_test_generator_enhanced.py](test/sdd_test_generator_enhanced.py) | 增强测试生成 | `python test/sdd_test_generator_enhanced.py spec.md` |
| [unit_test_enhancer.py](test/unit_test_enhancer.py) | 单元测试增强 | `python test/unit_test_enhancer.py tests/` |
| [integration_test_enhancer.py](test/integration_test_enhancer.py) | 集成测试增强 | `python test/integration_test_enhancer.py tests/` |
| [e2e_test_enhancer.py](test/e2e_test_enhancer.py) | E2E测试增强 | `python test/e2e_test_enhancer.py e2e/` |
| [database_test_enhancer.py](test/database_test_enhancer.py) | 数据库测试增强 | `python test/database_test_enhancer.py tests/` |
| [performance_test_enhancer.py](test/performance_test_enhancer.py) | 性能测试增强 | `python test/performance_test_enhancer.py tests/` |
| [security_scanner.py](test/security_scanner.py) | 安全扫描 | `python test/security_scanner.py --strict` |
| [regression_test.py](test/regression_test.py) | 回归测试 | `python test/regression_test.py` |
| [test_failure_diagnostician.py](test/test_failure_diagnostician.py) | 测试失败诊断 | `python test/test_failure_diagnostician.py report.json` |
| [test_report_generator.py](test/test_report_generator.py) | 测试报告生成 | `python test/test_report_generator.py --markdown` |

### 分析脚本 (analysis/)

| 脚本 | 功能 | 示例 |
|------|------|------|
| [architecture_check.py](analysis/architecture_check.py) | 架构检查 | `python analysis/architecture_check.py` |
| [code_problem_scanner.py](analysis/code_problem_scanner.py) | 代码问题扫描 | `python analysis/code_problem_scanner.py --json` |
| [coverage_analyzer.py](analysis/coverage_analyzer.py) | 覆盖率分析 | `python analysis/coverage_analyzer.py` |
| [nesting_analyzer.py](analysis/nesting_analyzer.py) | 嵌套层级分析 | `python analysis/nesting_analyzer.py --max-depth 4` |
| [performance_detector.py](analysis/performance_detector.py) | 性能检测 | `python analysis/performance_detector.py` |
| [log_analyzer.py](analysis/log_analyzer.py) | 日志分析 | `python analysis/log_analyzer.py logs/` |
| [issue_locator.py](analysis/issue_locator.py) | 问题定位 | `python analysis/issue_locator.py --scan-project` |
| [check_coverage.py](analysis/check_coverage.py) | 覆盖率检查 | `python analysis/check_coverage.py --threshold 80` |
| [validate_test_coverage.py](analysis/validate_test_coverage.py) | 测试覆盖验证 | `python analysis/validate_test_coverage.py` |

### 优化脚本 (optimization/)

| 脚本 | 功能 | 示例 |
|------|------|------|
| [auto_fixer.py](optimization/auto_fixer.py) | 自动修复 | `python optimization/auto_fixer.py ./ --project-root ./` |
| [systematic_optimizer.py](optimization/systematic_optimizer.py) | 系统化优化 | `python optimization/systematic_optimizer.py` |
| [refactoring_suggestion_generator.py](optimization/refactoring_suggestion_generator.py) | 重构建议生成 | `python optimization/refactoring_suggestion_generator.py` |
| [refactoring_validator.py](optimization/refactoring_validator.py) | 重构验证 | `python optimization/refactoring_validator.py` |

### 需求脚本 (requirements/)

| 脚本 | 功能 | 示例 |
|------|------|------|
| [requirement_parser.py](requirements/requirement_parser.py) | 需求解析 | `python requirements/requirement_parser.py requirement.md` |
| [requirement_spec_generator.py](requirements/requirement_spec_generator.py) | 需求规格生成 | `python requirements/requirement_spec_generator.py` |
| [requirement_trace_manager.py](requirements/requirement_trace_manager.py) | 需求追溯管理 | `python requirements/requirement_trace_manager.py` |
| [business_rule_extractor.py](requirements/business_rule_extractor.py) | 业务规则提取 | `python requirements/business_rule_extractor.py spec.md` |
| [business_rule_recognizer.py](requirements/business_rule_recognizer.py) | 业务规则识别 | `python requirements/business_rule_recognizer.py` |
| [rule_library_manager.py](requirements/rule_library_manager.py) | 规则库管理 | `python requirements/rule_library_manager.py` |
| [trace_matrix_visualizer.py](requirements/trace_matrix_visualizer.py) | 追溯矩阵可视化 | `python requirements/trace_matrix_visualizer.py` |
| [trace_report_generator.py](requirements/trace_report_generator.py) | 追溯报告生成 | `python requirements/trace_report_generator.py` |
| [rule_validator.py](requirements/rule_validator.py) | 规则验证 | `python requirements/rule_validator.py` |

### 工具脚本 (utils/)

| 脚本 | 功能 | 示例 |
|------|------|------|
| [script_utils.py](utils/script_utils.py) | 脚本工具基类 | - |
| [script_base.py](core/script_base.py) | 脚本基类 | - |
| [version_manager.py](utils/version_manager.py) | 版本管理 | `python utils/version_manager.py status` |
| [doc_version_manager.py](utils/doc_version_manager.py) | 文档版本管理 | `python utils/doc_version_manager.py` |
| [report_version_manager.py](utils/report_version_manager.py) | 报告版本管理 | `python utils/report_version_manager.py` |
| [path_config_manager.py](utils/path_config_manager.py) | 路径配置管理 | `python utils/path_config_manager.py` |
| [temp_file_manager.py](utils/temp_file_manager.py) | 临时文件管理 | `python utils/temp_file_manager.py` |
| [history_tracker.py](utils/history_tracker.py) | 历史追踪 | `python utils/history_tracker.py --report` |
| [benchmark_updater.py](utils/benchmark_updater.py) | 基准更新 | `python utils/benchmark_updater.py` |
| [priority_evaluator.py](utils/priority_evaluator.py) | 优先级评估 | `python utils/priority_evaluator.py` |
| [report_generator.py](utils/report_generator.py) | 报告生成 | `python utils/report_generator.py` |
| [doc_change_tracker.py](utils/doc_change_tracker.py) | 文档变更追踪 | `python utils/doc_change_tracker.py` |
| [script_dependency_manager.py](utils/script_dependency_manager.py) | 脚本依赖管理 | `python utils/script_dependency_manager.py` |

## 公共模块

### script_utils.py

提供脚本开发的公共基类和工具：

```python
from skillscripts.utils.script_utils import (
    ScriptBase,      # 脚本基类
    ScriptResult,    # 结果数据类
    ScriptLogger,    # 日志记录器
    ExitCode,        # 退出码枚举
    create_result,   # 结果创建函数
    run_script       # 脚本运行函数
)

class MyScript(ScriptBase):
    DEFAULT_DESCRIPTION = "我的脚本"
    
    def _add_arguments(self):
        self.parser.add_argument("--input", help="输入文件")
    
    def run(self) -> int:
        self.logger.info("开始执行...")
        
        result = create_result(
            success=True,
            message="执行成功",
            data={"processed": 10},
            duration_ms=self.get_duration_ms()
        )
        
        if self.args.json:
            self.output_json(result)
        else:
            self.output_console(result)
        
        return ExitCode.EXIT_CODE_SUCCESS.value

if __name__ == "__main__":
    sys.exit(run_script(MyScript))
```

## 快速开始

### 检查系统状态

```bash
# 健康检查
python core/health_check.py --json

# 环境检查
python core/check_environment.py

# 查看仪表盘
python core/query_status.py --dashboard
```

### 启动/停止服务

```bash
# 启动所有服务
python core/start_services.py

# 仅启动后端
python core/start_services.py --backend

# 停止所有服务
python core/stop_services.py --all
```

### 代码质量检查

```bash
# 安全扫描
python test/security_scanner.py --strict

# 嵌套层级分析
python analysis/nesting_analyzer.py --max-depth 4

# 代码问题扫描
python analysis/code_problem_scanner.py --json
```

### 生成报告

```bash
# 优化报告
python utils/report_generator.py

# 测试报告
python test/test_report_generator.py --markdown

# 历史报告
python utils/history_tracker.py --report --days 30
```

### 省部司协同调用

```bash
# 创建新任务
python core/provincial_coordinator.py --create-task --type feature --description "任务描述"

# 执行三省协调
python core/provincial_coordinator.py --coordinate --task-id TASK-xxx

# 分发至六部执行
python core/provincial_coordinator.py --dispatch --task-id TASK-xxx

# 查询任务状态
python core/provincial_coordinator.py --status --task-id TASK-xxx
```

## 开发规范

### 创建新脚本

1. 继承 `ScriptBase` 基类
2. 设置 `DEFAULT_DESCRIPTION` 和 `DEFAULT_EPILOG`
3. 在 `_add_arguments()` 中添加自定义参数
4. 实现 `run()` 方法返回退出码
5. 使用 `self.logger` 记录日志
6. 支持 `--json` 和 `--markdown` 输出

### 脚本模板

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
脚本名称 - 简短描述

详细功能描述...

使用示例:
    python script_name.py              # 默认执行
    python script_name.py --json       # JSON 格式输出
    python script_name.py --markdown   # Markdown 格式输出

退出码:
    0 - 成功
    1 - 错误
    2 - 警告
"""

import sys
from skillscripts.utils.script_utils import (
    ScriptBase, ExitCode, create_result
)


class ScriptName(ScriptBase):
    DEFAULT_DESCRIPTION = "脚本描述"
    DEFAULT_EPILOG = """
示例:
  python script_name.py
  python script_name.py --json

退出码:
  0 - 成功
  1 - 错误
"""
    
    def _add_arguments(self):
        self.parser.add_argument("--option", help="选项说明")
    
    def run(self) -> int:
        self.logger.info("开始执行...")
        
        result = create_result(
            success=True,
            message="执行成功",
            duration_ms=self.get_duration_ms()
        )
        
        if self.args.json:
            self.output_json(result)
        elif self.args.markdown:
            self.output_markdown(result)
        else:
            self.output_console(result)
        
        return ExitCode.EXIT_CODE_SUCCESS.value


def main():
    script = ScriptName()
    return script.execute()


if __name__ == "__main__":
    sys.exit(main())
```

## 脚本统计

- 总脚本数：60+
- 核心流程：11
- 流水线：9
- 测试：12
- 分析：9
- 优化：4
- 需求：9
- 工具：13+

---

*最后更新：2026-03-30*
