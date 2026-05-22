#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动修复系统主入口 - Auto Repair System Main Entry

三省六部技能自动修复能力增强系统

使用示例:
    # 声明式使用
    python auto_repair_system.py --file code.py
    
    # 预览模式
    python auto_repair_system.py --file code.py --preview
    
    # 项目模式
    python auto_repair_system.py --project
    
    # 编程式使用
    from auto_repair import AutoRepairWorkflow, WorkflowConfig
    
    config = WorkflowConfig(auto_apply=True, confidence_threshold=0.8)
    workflow = AutoRepairWorkflow(config=config)
    result = workflow.repair_file("code.py")
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# 添加当前目录到路径
sys.path.insert(0, str(get_path_config().SKILL_ROOT))

try:
    from .auto_repair_workflow import AutoRepairWorkflow, WorkflowConfig, WorkflowResult, WorkflowStatus
    from .issue_detector import IssueDetector, IssueCategory, IssueSeverity
    from .fix_strategy import FixStrategyLibrary
    from .fix_executor import FixExecutor
except ImportError:
    try:
        from auto_repair_workflow import AutoRepairWorkflow, WorkflowConfig, WorkflowResult, WorkflowStatus
        from issue_detector import IssueDetector, IssueCategory, IssueSeverity
        from fix_strategy import FixStrategyLibrary
        from fix_executor import FixExecutor
from skillscripts.core.path_config_center import get_path_config
    except ImportError as e:
        # 如果还是失败，创建空类以避免导入错误
        class AutoRepairWorkflow: pass
        class WorkflowConfig: pass
        class WorkflowResult: pass
        class WorkflowStatus: pass
        class IssueDetector: pass
        class IssueCategory: pass
        class IssueSeverity: pass
        class FixStrategyLibrary: pass
        class FixExecutor: pass
        logging.warning(f"无法导入自动修复组件: {e}")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AutoRepairSystem:
    """自动修复系统主类"""

    def __init__(
        self,
        project_root: Optional[Path] = None,
        config: Optional[WorkflowConfig] = None
    ):
        self.project_root = project_root or Path.cwd()
        self.config = config or WorkflowConfig()
        self.workflow = AutoRepairWorkflow(
            project_root=self.project_root,
            config=self.config
        )
        self.detector = IssueDetector(project_root=self.project_root)
        self.strategy_library = FixStrategyLibrary()
        self.executor = FixExecutor(project_root=self.project_root)

    def repair_file(
        self,
        file_path: str,
        preview_only: bool = False
    ) -> WorkflowResult:
        return self.workflow.repair_file(file_path, preview_only)

    def repair_project(
        self,
        file_pattern: str = "*.py"
    ) -> Dict[str, WorkflowResult]:
        return self.workflow.repair_project(file_pattern)

    def preview_repair(self, file_path: str):
        return self.workflow.preview_repair(file_path)

    def detect_issues(self, file_path: str):
        return self.detector.detect_file(file_path)

    def detect_project_issues(self, file_pattern: str = "*.py") -> Dict[str, DetectionResult]:
        return self.detector.detect_project(file_pattern)

    def get_fix_history(self, file_path: str):
        return self.executor.get_fix_history(file_path)

    def rollback_fix(self, fix_id: str):
        return self.executor.rollback(fix_id)

    def analyze_project_health(self) -> Dict[str, Any]:
        results = self.detect_project_issues()
        
        total_files = len(results)
        total_issues = sum(r.total_issues for r in results.values())
        total_critical = sum(r.critical_count for r in results.values())
        total_high = sum(r.high_count for r in results.values())
        total_medium = sum(r.medium_count for r in results.values())
        total_low = sum(r.low_count for r in results.values())
        
        files_with_issues = sum(1 for r in results.values() if r.total_issues > 0)
        files_with_critical = sum(1 for r in results.values() if r.critical_count > 0)
        
        health_score = 100.0
        if total_files > 0:
            health_score = max(0, 100 - (total_critical * 10 + total_high * 5 + total_medium * 2 + total_low * 0.5))
        
        issue_categories = defaultdict(int)
        for result in results.values():
            for issue in result.issues:
                category_prefix = issue.category.name.split('_')[0]
                issue_categories[category_prefix] += 1
        
        return {
            "project_root": str(self.project_root),
            "analysis_timestamp": datetime.now().isoformat(),
            "summary": {
                "total_files": total_files,
                "files_with_issues": files_with_issues,
                "files_with_critical": files_with_critical,
                "total_issues": total_issues,
                "critical_issues": total_critical,
                "high_issues": total_high,
                "medium_issues": total_medium,
                "low_issues": total_low
            },
            "health_score": round(health_score, 1),
            "issue_distribution": dict(issue_categories),
            "recommendations": self._generate_health_recommendations(
                total_critical, total_high, issue_categories
            )
        }

    def _generate_health_recommendations(
        self,
        critical_count: int,
        high_count: int,
        issue_categories: Dict[str, int]
    ) -> List[str]:
        recommendations = []
        
        if critical_count > 0:
            recommendations.append(f"发现 {critical_count} 个严重问题，建议立即处理")
        
        if high_count > 5:
            recommendations.append(f"发现 {high_count} 个高优先级问题，建议优先修复")
        
        if issue_categories.get("SECURITY", 0) > 0:
            recommendations.append("发现安全问题，建议进行安全代码审查")
        
        if issue_categories.get("SYNTAX", 0) > 0:
            recommendations.append("发现语法错误，需要立即修复才能运行代码")
        
        if issue_categories.get("TEST", 0) > 0:
            recommendations.append("发现测试相关问题，建议完善测试用例")
        
        if issue_categories.get("CODESMELL", 0) > 10:
            recommendations.append("发现较多代码异味，建议进行代码重构")
        
        if not recommendations:
            recommendations.append("代码健康状况良好，继续保持代码审查习惯")
        
        return recommendations

    def batch_repair(
        self,
        file_paths: List[str],
        auto_apply: bool = True
    ) -> Dict[str, WorkflowResult]:
        results = {}
        
        for file_path in file_paths:
            try:
                result = self.repair_file(file_path)
                results[file_path] = result
            except Exception as e:
                logger.error(f"批量修复失败: {file_path}, {e}")
        
        return results

    def get_repair_statistics(self) -> Dict[str, Any]:
        recent_fixes = self.executor.get_recent_fixes(50)
        
        if not recent_fixes:
            return {
                "total_fixes": 0,
                "successful_fixes": 0,
                "failed_fixes": 0,
                "success_rate": 0.0
            }
        
        total = len(recent_fixes)
        successful = sum(1 for f in recent_fixes if f.status == ExecutionStatus.SUCCESS)
        failed = sum(1 for f in recent_fixes if f.status == ExecutionStatus.FAILED)
        rolled_back = sum(1 for f in recent_fixes if f.status == ExecutionStatus.ROLLED_BACK)
        
        strategy_stats = defaultdict(lambda: {"count": 0, "success": 0})
        for fix in recent_fixes:
            for strategy in fix.metadata.get("strategies_used", []):
                strategy_stats[strategy]["count"] += 1
                if fix.status == ExecutionStatus.SUCCESS:
                    strategy_stats[strategy]["success"] += 1
        
        return {
            "total_fixes": total,
            "successful_fixes": successful,
            "failed_fixes": failed,
            "rolled_back_fixes": rolled_back,
            "success_rate": successful / total if total > 0 else 0.0,
            "strategy_statistics": dict(strategy_stats)
        }

    def generate_report(
        self,
        result: WorkflowResult,
        output_format: str = "markdown"
    ) -> str:
        if output_format == "json":
            return json.dumps(result.to_dict(), indent=2, ensure_ascii=False)
        
        lines = [
            "# 自动修复报告",
            f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"\n## 基本信息",
            f"- **文件**: {result.file_path}",
            f"- **状态**: {result.status.value}",
            f"- **工作流ID**: {result.workflow_id}",
            f"\n## 修复统计",
            f"- **检测问题**: {result.issues_detected}",
            f"- **修复成功**: {result.issues_fixed}",
            f"- **修复失败**: {result.issues_failed}",
            f"- **跳过问题**: {result.issues_skipped}",
            f"- **总耗时**: {result.total_duration_ms:.2f}ms",
        ]
        
        if result.stages:
            lines.extend([
                f"\n## 执行阶段",
                "| 阶段 | 状态 | 耗时 | 消息 |",
                "|------|------|------|------|",
            ])
            for stage in result.stages:
                lines.append(
                    f"| {stage.stage.name} | {stage.status.value} | {stage.duration_ms:.2f}ms | {stage.message[:50]} |"
                )
        
        if result.detection_result and result.detection_result.issues:
            lines.extend([
                f"\n## 检测到的问题 ({len(result.detection_result.issues)})",
            ])
            for issue in result.detection_result.issues[:10]:
                lines.append(
                    f"- [{issue.severity.value}] {issue.category.name}: {issue.message}"
                )
                lines.append(f"  位置: 行 {issue.line_number}")
        
        if result.knowledge_entries:
            lines.extend([
                f"\n## 知识积累 ({len(result.knowledge_entries)})",
            ])
            for entry in result.knowledge_entries[:5]:
                lines.append(
                    f"- {entry.issue_category.name}: {entry.fix_strategy} (成功率: {entry.success_rate:.0%})"
                )
        
        lines.extend([
            f"\n## 消息",
            result.message,
        ])
        
        return '\n'.join(lines)

    def save_report(
        self,
        result: WorkflowResult,
        output_path: str,
        output_format: str = "markdown"
    ) -> None:
        report = self.generate_report(result, output_format)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"报告已保存到: {output_path}")


def create_sample_config() -> WorkflowConfig:
    return WorkflowConfig(
        max_retries=3,
        auto_apply=True,
        create_backup=True,
        verify_fixes=True,
        confidence_threshold=0.7,
        risk_threshold="medium",
        skip_categories=[],
        knowledge_accumulation=True
    )


def print_banner():
    banner = """
╔──────────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│     █████╗ ██╗   ██╗ █████╗  ██████╗ ██████╗ ███████╗████████╗███████╗    │
│    ██╔══██╗██║   ██║██╔══██╗██╔══██╗██╔══██╗██╔════╝╚══██╔══╝██╔════╝    │
│    ███████║██║   ██║███████║██║  ██║██║  ██║█████╗     ██║   █████╗      │
│    ██╔══██║╚██╗ ██╔╝██╔══██║██║  ██║██║  ██║██╔══╝     ██║   ██╔══╝      │
│    ██║  ██║ ╚████╔╝ ██║  ██║██████╔╝██████╔╝███████╗   ██║   ███████╗    │
│    ╚═╝  ╚═╝  ╚═══╝  ╚═╝  ╚═╝╚═════╝ ╚═════╝ ╚══════╝   ╚═╝   ╚══════╝    │
│                                                                          │
│              三省六部技能 - 自动修复系统 v1.0.0                              │
│                                                                          │
│    功能:                                                                 │
│    • 问题检测: 语法错误、导入错误、类型错误、安全漏洞                   │
│    • 修复策略: 语法修复、导入修复、类型修复、安全修复                   │
│    • 执行能力: 预览、回滚、验证、历史记录                               │
│    • 工作流: 检测→建议→执行→验证→回滚→知识积累                           │
│                                                                          │
╚──────────────────────────────────────────────────────────────────────────────┘
"""
    print(banner)


def main():
    parser = argparse.ArgumentParser(
        description="三省六部技能自动修复系统",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--file", "-f",
        type=str,
        help="要修复的文件路径"
    )
    parser.add_argument(
        "--project", "-p",
        action="store_true",
        help="修复整个项目"
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="仅预览修复，不实际执行"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        help="报告输出路径"
    )
    parser.add_argument(
        "--format",
        type=str,
        choices=["markdown", "json"],
        default="markdown",
        help="报告输出格式"
    )
    parser.add_argument(
        "--config",
        type=str,
        help="配置文件路径 (JSON)"
    )
    parser.add_argument(
        "--auto-apply",
        action="store_true",
        help="自动应用修复 (无需确认)"
    )
    parser.add_argument(
        "--confidence",
        type=float,
        default=0.7,
        help="置信度阈值 (0.0-1.0)"
    )
    parser.add_argument(
        "--history",
        type=str,
        help="查看文件修复历史"
    )
    parser.add_argument(
        "--rollback",
        type=str,
        help="回滚指定修复ID"
    )
    parser.add_argument(
        "--detect-only",
        action="store_true",
        help="仅检测问题，不执行修复"
    )
    
    args = parser.parse_args()
    
    print_banner()
    
    config = create_sample_config()
    
    if args.config:
        try:
            with open(args.config, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            config = WorkflowConfig(**config_data)
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            return 1
    
    if args.auto_apply:
        config.auto_apply = True
    if args.confidence:
        config.confidence_threshold = args.confidence
    
    system = AutoRepairSystem(config=config)
    
    if args.history:
        history = system.get_fix_history(args.history)
        if history:
            print(f"\n文件: {history.file_path}")
            print(f"总修复次数: {history.total_fixes}")
            print(f"成功修复: {history.successful_fixes}")
            print(f"失败修复: {history.failed_fixes}")
            print(f"已回滚: {history.rolled_back_fixes}")
            print(f"\n最近修复记录:")
            for record in history.records[-5:]:
                print(f"  - {record.fix_id}: {record.status.value}")
                print(f"    时间: {record.applied_at}")
                print(f"    成功: {len(record.issues_fixed)}, 失败: {len(record.issues_failed)}")
        else:
            print("未找到历史记录")
        return 0
    
    if args.rollback:
        success, message = system.rollback_fix(args.rollback)
        print(f"\n回滚结果: {message}")
        return 0 if success else 1
    
    if args.detect_only and args.file:
        print(f"\n检测文件: {args.file}")
        result = system.detect_issues(args.file)
        
        print(f"\n检测结果:")
        print(f"状态: {result.status.value}")
        print(f"总问题数: {result.total_issues}")
        print(f"严重: {result.critical_count}")
        print(f"高: {result.high_count}")
        print(f"中: {result.medium_count}")
        print(f"低: {result.low_count}")
        print(f"检测耗时: {result.detection_time_ms:.2f}ms")
        
        if result.issues:
            print(f"\n问题列表:")
            for issue in result.issues:
                print(f"  [{issue.severity.value}] {issue.category.name}")
                print(f"    {issue.message}")
                print(f"    位置: 行 {issue.line_number}")
                if issue.suggested_fix:
                    print(f"    建议: {issue.suggested_fix}")
        
        return 0
    
    if args.file:
        if args.preview:
            print(f"\n预览修复: {args.file}")
            preview = system.preview_repair(args.file)
            
            if preview:
                print(f"\n修复预览:")
                print(f"文件: {preview.file_path}")
                print(f"风险等级: {preview.risk_level.value}")
                print(f"置信度: {preview.confidence:.0%}")
                print(f"可自动应用: {'是' if preview.can_auto_apply else '否'}")
                print(f"\n变更数量: {len(preview.changes)}")
                
                if preview.changes:
                    print("\n变更详情:")
                    for change in preview.changes[:5]:
                        print(f"  - 行 {change['line']}: {change['strategy']}")
                        print(f"    {change['message']}")
                
                print(f"\n差异预览:")
                print("-" * 60)
                for line in preview.diff.split('\n')[:30]:
                    print(line)
            else:
                print("无需修复或预览失败")
        else:
            print(f"\n修复文件: {args.file}")
            result = system.repair_file(args.file)
            
            print(f"\n工作流结果:")
            print(f"状态: {result.status.value}")
            print(f"工作流ID: {result.workflow_id}")
            print(f"检测问题: {result.issues_detected}")
            print(f"修复成功: {result.issues_fixed}")
            print(f"修复失败: {result.issues_failed}")
            print(f"跳过问题: {result.issues_skipped}")
            print(f"总耗时: {result.total_duration_ms:.2f}ms")
            print(f"\n消息: {result.message}")
            
            if args.output:
                system.save_report(result, args.output, args.format)
                print(f"\n报告已保存到: {args.output}")
    
    elif args.project:
        print(f"\n修复项目...")
        results = system.repair_project()
        
        total_files = len(results)
        total_fixed = sum(r.issues_fixed for r in results.values())
        total_failed = sum(r.issues_failed for r in results.values())
        total_detected = sum(r.issues_detected for r in results.values())
        
        print(f"\n项目修复结果:")
        print(f"处理文件数: {total_files}")
        print(f"总检测问题: {total_detected}")
        print(f"总修复成功: {total_fixed}")
        print(f"总修复失败: {total_failed}")
        
        success_files = [f for f in results.values() if f.status == WorkflowStatus.SUCCESS]
        print(f"成功文件: {len(success_files)}/{total_files}")
        
        if args.output:
            output_data = {
                "summary": {
                    "total_files": total_files,
                    "total_detected": total_detected,
                    "total_fixed": total_fixed,
                    "total_failed": total_failed,
                    "success_rate": len(success_files) / total_files if total_files > 0 else 0
                },
                "results": {k: v.to_dict() for k, v in results.items()}
            }
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            print(f"\n报告已保存到: {args.output}")
    
    else:
        parser.print_help()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
