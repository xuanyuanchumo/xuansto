#!/usr/bin/env python3
"""
自动迭代器 - 智能版本迭代系统
实现基于触发条件的自动版本迭代，包括错误率监控、性能监控、安全检查等

功能特性:
1. 自迭代触发条件检测
2. 智能版本升级决策
3. 自动化发布流程
4. 迭代效果评估
5. 持续集成集成
6. 发布检查清单
"""

import json
import os
import sys
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
import logging

from .version_iterator import (
    VersionIterator,
    VersionBumpType,
    ChangeType,
    ChangeEntry,
    IterationTriggerType,
    IterationTrigger,
    VersionEntry
)


class IterationTriggerDetector:
    """自迭代触发条件检测器"""

    DEFAULT_THRESHOLDS = {
        IterationTriggerType.ERROR_RATE: 0.05,
        IterationTriggerType.CONTINUOUS_FAILURE: 3,
        IterationTriggerType.PERFORMANCE_DEGRADATION: 0.5,
        IterationTriggerType.SECURITY_ALERT: 1,
        IterationTriggerType.CODE_QUALITY: 0.7,
        IterationTriggerType.TEST_FAILURE: 0.1,
        IterationTriggerType.DEPENDENCY_UPDATE: 1,
    }

    def __init__(self, version_iterator: VersionIterator, thresholds: Optional[Dict[IterationTriggerType, float]] = None):
        self.vi = version_iterator
        self.thresholds = thresholds or self.DEFAULT_THRESHOLDS.copy()
        self.logger = logging.getLogger('IterationTriggerDetector')

    def check_all_triggers(self, metrics: Dict[str, Any]) -> List[IterationTrigger]:
        """检查所有触发条件"""
        triggers = []

        triggers.append(self._check_error_rate(metrics.get('error_rate', 0)))
        triggers.append(self._check_continuous_failure(metrics.get('continuous_failures', 0)))
        triggers.append(self._check_performance(metrics.get('performance_baseline', {}), 
                                                metrics.get('current_performance', {})))
        triggers.append(self._check_security(metrics.get('security_alerts', [])))
        triggers.append(self._check_code_quality(metrics.get('code_quality_score', 1.0)))
        triggers.append(self._check_test_failure(metrics.get('test_failure_rate', 0)))
        triggers.append(self._check_dependency_update(metrics.get('dependency_updates', [])))

        return [t for t in triggers if t.triggered]

    def _check_error_rate(self, error_rate: float) -> IterationTrigger:
        """检查错误率"""
        threshold = self.thresholds[IterationTriggerType.ERROR_RATE]
        triggered = error_rate > threshold

        return IterationTrigger(
            trigger_type=IterationTriggerType.ERROR_RATE,
            threshold=threshold,
            current_value=error_rate,
            triggered=triggered,
            details={"message": f"错误率 {error_rate:.2%} {'超过' if triggered else '未超过'} 阈值 {threshold:.2%}"}
        )

    def _check_continuous_failure(self, failure_count: int) -> IterationTrigger:
        """检查连续失败次数"""
        threshold = self.thresholds[IterationTriggerType.CONTINUOUS_FAILURE]
        triggered = failure_count >= threshold

        return IterationTrigger(
            trigger_type=IterationTriggerType.CONTINUOUS_FAILURE,
            threshold=threshold,
            current_value=float(failure_count),
            triggered=triggered,
            details={"message": f"连续失败 {failure_count} 次 {'达到' if triggered else '未达到'} 阈值 {threshold}"}
        )

    def _check_performance(self, baseline: Dict[str, float], 
                          current: Dict[str, float]) -> IterationTrigger:
        """检查性能下降"""
        threshold = self.thresholds[IterationTriggerType.PERFORMANCE_DEGRADATION]
        degradation = 0.0
        details = {}

        if baseline and current:
            for key in baseline:
                if key in current and baseline[key] > 0:
                    ratio = (current[key] - baseline[key]) / baseline[key]
                    if ratio > degradation:
                        degradation = ratio
                        details["metric"] = key
                        details["baseline"] = baseline[key]
                        details["current"] = current[key]

        triggered = degradation > threshold

        return IterationTrigger(
            trigger_type=IterationTriggerType.PERFORMANCE_DEGRADATION,
            threshold=threshold,
            current_value=degradation,
            triggered=triggered,
            details=details
        )

    def _check_security(self, alerts: List[Dict[str, Any]]) -> IterationTrigger:
        """检查安全警告"""
        threshold = self.thresholds[IterationTriggerType.SECURITY_ALERT]
        alert_count = len(alerts)
        triggered = alert_count >= threshold

        return IterationTrigger(
            trigger_type=IterationTriggerType.SECURITY_ALERT,
            threshold=threshold,
            current_value=float(alert_count),
            triggered=triggered,
            details={"alerts": alerts}
        )

    def _check_code_quality(self, quality_score: float) -> IterationTrigger:
        """检查代码质量"""
        threshold = self.thresholds[IterationTriggerType.CODE_QUALITY]
        triggered = quality_score < threshold

        return IterationTrigger(
            trigger_type=IterationTriggerType.CODE_QUALITY,
            threshold=threshold,
            current_value=quality_score,
            triggered=triggered,
            details={"message": f"代码质量分数 {quality_score:.2f} {'低于' if triggered else '高于'} 阈值 {threshold:.2f}"}
        )

    def _check_test_failure(self, failure_rate: float) -> IterationTrigger:
        """检查测试失败率"""
        threshold = self.thresholds[IterationTriggerType.TEST_FAILURE]
        triggered = failure_rate > threshold

        return IterationTrigger(
            trigger_type=IterationTriggerType.TEST_FAILURE,
            threshold=threshold,
            current_value=failure_rate,
            triggered=triggered,
            details={"message": f"测试失败率 {failure_rate:.2%} {'超过' if triggered else '未超过'} 阈值 {threshold:.2%}"}
        )

    def _check_dependency_update(self, updates: List[Dict[str, Any]]) -> IterationTrigger:
        """检查依赖更新"""
        threshold = self.thresholds[IterationTriggerType.DEPENDENCY_UPDATE]
        update_count = len(updates)
        triggered = update_count >= threshold

        return IterationTrigger(
            trigger_type=IterationTriggerType.DEPENDENCY_UPDATE,
            threshold=threshold,
            current_value=float(update_count),
            triggered=triggered,
            details={"updates": updates, "message": f"发现 {update_count} 个依赖更新"}
        )

    def determine_bump_type(self, triggers: List[IterationTrigger]) -> VersionBumpType:
        """根据触发条件确定版本升级类型"""
        trigger_types = {t.trigger_type for t in triggers}

        if IterationTriggerType.SECURITY_ALERT in trigger_types:
            return VersionBumpType.PATCH

        if IterationTriggerType.CONTINUOUS_FAILURE in trigger_types:
            return VersionBumpType.PATCH

        if IterationTriggerType.ERROR_RATE in trigger_types:
            return VersionBumpType.PATCH

        if IterationTriggerType.TEST_FAILURE in trigger_types:
            return VersionBumpType.PATCH

        if IterationTriggerType.PERFORMANCE_DEGRADATION in trigger_types:
            return VersionBumpType.MINOR

        if IterationTriggerType.CODE_QUALITY in trigger_types:
            return VersionBumpType.MINOR

        if IterationTriggerType.DEPENDENCY_UPDATE in trigger_types:
            return VersionBumpType.PATCH

        return VersionBumpType.PATCH

    def generate_trigger_report(self, triggers: List[IterationTrigger]) -> str:
        """生成触发条件报告"""
        lines = [
            "# 自迭代触发条件检测报告",
            "",
            f"检测时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## 触发条件状态",
            "",
        ]

        for trigger in triggers:
            status = "✅ 触发" if trigger.triggered else "❌ 未触发"
            lines.append(f"### {trigger.trigger_type.value}")
            lines.append(f"- 状态: {status}")
            lines.append(f"- 阈值: {trigger.threshold}")
            lines.append(f"- 当前值: {trigger.current_value}")
            if trigger.details:
                lines.append(f"- 详情: {trigger.details.get('message', '')}")
            lines.append("")

        if any(t.triggered for t in triggers):
            lines.extend([
                "## 建议操作",
                "",
                f"- 建议版本升级类型: {self.determine_bump_type(triggers).value}",
                "- 建议执行自迭代流程",
            ])

        return '\n'.join(lines)


class ReleaseAutomator:
    """发布自动化器"""

    def __init__(self, version_iterator: VersionIterator):
        self.vi = version_iterator
        self.logger = logging.getLogger('ReleaseAutomator')

    def prepare_release(
        self,
        bump_type: VersionBumpType,
        changes: List[ChangeEntry],
        author: str = "",
        notes: str = ""
    ) -> Dict[str, Any]:
        """准备发布"""
        current_version = self.vi.get_current_version()
        
        snapshot = self.vi.create_snapshot(str(current_version), f"Pre-release snapshot for {current_version}")
        
        new_version = self.vi.bump_version(bump_type)
        
        version_entry = self.vi.create_version_entry(
            new_version=new_version,
            changes=changes,
            author=author,
            notes=notes
        )
        
        release_notes = self.vi.changelog_generator.generate_release_notes(new_version)
        
        return {
            "previous_version": str(current_version),
            "new_version": new_version,
            "snapshot_id": snapshot.snapshot_id,
            "version_entry": version_entry,
            "release_notes": release_notes,
            "changelog_updated": True
        }

    def execute_release(
        self,
        version: str,
        create_tag: bool = True,
        push_tag: bool = False,
        run_tests: bool = True
    ) -> Dict[str, Any]:
        """执行发布"""
        results = {
            "version": version,
            "success": True,
            "steps": []
        }
        
        if run_tests:
            test_result = self._run_tests()
            results["steps"].append({
                "name": "run_tests",
                "success": test_result,
                "message": "测试通过" if test_result else "测试失败"
            })
            
            if not test_result:
                results["success"] = False
                results["error"] = "测试失败，发布中止"
                return results
        
        if create_tag:
            tag_result = self._create_git_tag(version)
            results["steps"].append({
                "name": "create_tag",
                "success": tag_result,
                "message": f"标签 v{version} 创建成功" if tag_result else "标签创建失败"
            })
            
            if push_tag and tag_result:
                push_result = self._push_git_tag(version)
                results["steps"].append({
                    "name": "push_tag",
                    "success": push_result,
                    "message": f"标签 v{version} 推送成功" if push_result else "标签推送失败"
                })
        
        results["steps"].append({
            "name": "update_changelog",
            "success": True,
            "message": "变更日志已更新"
        })
        
        return results

    def _run_tests(self) -> bool:
        """运行测试"""
        test_commands = [
            [sys.executable, '-m', 'pytest', '-x'],
            [sys.executable, '-m', 'unittest', 'discover'],
        ]
        
        for cmd in test_commands:
            try:
                result = subprocess.run(
                    cmd,
                    cwd=self.vi.project_root,
                    capture_output=True,
                    timeout=300
                )
                
                if result.returncode == 0:
                    return True
            except Exception:
                continue
        
        return False

    def _create_git_tag(self, version: str) -> bool:
        """创建Git标签"""
        try:
            subprocess.run(
                ['git', 'tag', '-a', f'v{version}', '-m', f'Release version {version}'],
                cwd=self.vi.project_root,
                check=True,
                capture_output=True,
                timeout=10
            )
            return True
        except Exception:
            return False

    def _push_git_tag(self, version: str) -> bool:
        """推送Git标签"""
        try:
            subprocess.run(
                ['git', 'push', 'origin', f'v{version}'],
                cwd=self.vi.project_root,
                check=True,
                capture_output=True,
                timeout=30
            )
            return True
        except Exception:
            return False

    def generate_release_checklist(self, version: str) -> List[Dict[str, Any]]:
        """生成发布检查清单"""
        checklist = [
            {
                "category": "代码质量",
                "items": [
                    {"task": "所有测试通过", "checked": False},
                    {"task": "代码审查完成", "checked": False},
                    {"task": "静态分析无错误", "checked": False},
                    {"task": "文档已更新", "checked": False},
                ]
            },
            {
                "category": "版本管理",
                "items": [
                    {"task": f"版本号已更新为 {version}", "checked": False},
                    {"task": "变更日志已更新", "checked": False},
                    {"task": "Git标签已创建", "checked": False},
                    {"task": "快照已创建", "checked": False},
                ]
            },
            {
                "category": "发布准备",
                "items": [
                    {"task": "发布说明已生成", "checked": False},
                    {"task": "依赖已检查", "checked": False},
                    {"task": "环境配置已验证", "checked": False},
                    {"task": "回滚方案已准备", "checked": False},
                ]
            },
            {
                "category": "发布后",
                "items": [
                    {"task": "标签已推送", "checked": False},
                    {"task": "发布公告已发布", "checked": False},
                    {"task": "监控已配置", "checked": False},
                    {"task": "旧版本快照已清理", "checked": False},
                ]
            }
        ]
        
        return checklist


class IterationEffectEvaluator:
    """迭代效果评估器"""

    def __init__(self, version_iterator: VersionIterator):
        self.vi = version_iterator
        self.logger = logging.getLogger('IterationEffectEvaluator')

    def evaluate_iteration(self, version: str, metrics_before: Dict[str, Any], metrics_after: Dict[str, Any]) -> Dict[str, Any]:
        """评估迭代效果"""
        evaluation = {
            "version": version,
            "timestamp": datetime.now().isoformat(),
            "improvements": [],
            "regressions": [],
            "overall_score": 0.0,
            "recommendations": []
        }

        error_rate_change = metrics_before.get('error_rate', 0) - metrics_after.get('error_rate', 0)
        if error_rate_change > 0:
            evaluation["improvements"].append({
                "metric": "error_rate",
                "change": error_rate_change,
                "description": f"错误率降低 {error_rate_change:.2%}"
            })
        elif error_rate_change < 0:
            evaluation["regressions"].append({
                "metric": "error_rate",
                "change": abs(error_rate_change),
                "description": f"错误率上升 {abs(error_rate_change):.2%}"
            })

        quality_change = metrics_after.get('code_quality_score', 0) - metrics_before.get('code_quality_score', 0)
        if quality_change > 0:
            evaluation["improvements"].append({
                "metric": "code_quality",
                "change": quality_change,
                "description": f"代码质量提升 {quality_change:.2f}"
            })
        elif quality_change < 0:
            evaluation["regressions"].append({
                "metric": "code_quality",
                "change": abs(quality_change),
                "description": f"代码质量下降 {abs(quality_change):.2f}"
            })

        perf_before = metrics_before.get('performance', {})
        perf_after = metrics_after.get('performance', {})
        
        for key in perf_before:
            if key in perf_after:
                perf_change = perf_before[key] - perf_after[key]
                if perf_change > 0:
                    evaluation["improvements"].append({
                        "metric": f"performance_{key}",
                        "change": perf_change,
                        "description": f"{key} 性能提升 {perf_change:.2f}"
                    })
                elif perf_change < 0:
                    evaluation["regressions"].append({
                        "metric": f"performance_{key}",
                        "change": abs(perf_change),
                        "description": f"{key} 性能下降 {abs(perf_change):.2f}"
                    })

        improvement_count = len(evaluation["improvements"])
        regression_count = len(evaluation["regressions"])
        
        if improvement_count > 0 and regression_count == 0:
            evaluation["overall_score"] = 1.0
            evaluation["recommendations"].append("迭代效果良好，建议继续保持")
        elif improvement_count > regression_count:
            evaluation["overall_score"] = 0.7
            evaluation["recommendations"].append("迭代整体有效，但需要关注回归问题")
        elif improvement_count == regression_count:
            evaluation["overall_score"] = 0.5
            evaluation["recommendations"].append("迭代效果一般，建议优化迭代策略")
        else:
            evaluation["overall_score"] = 0.3
            evaluation["recommendations"].append("迭代效果不佳，建议回滚或重新评估")

        return evaluation

    def generate_evaluation_report(self, evaluation: Dict[str, Any]) -> str:
        """生成评估报告"""
        lines = [
            f"# 迭代效果评估报告",
            "",
            f"**版本**: {evaluation['version']}",
            f"**评估时间**: {evaluation['timestamp']}",
            f"**总体评分**: {evaluation['overall_score']:.2f}",
            "",
        ]

        if evaluation["improvements"]:
            lines.extend([
                "## 改进项",
                "",
            ])
            for imp in evaluation["improvements"]:
                lines.append(f"- ✅ {imp['description']}")

        if evaluation["regressions"]:
            lines.extend([
                "",
                "## 回归项",
                "",
            ])
            for reg in evaluation["regressions"]:
                lines.append(f"- ❌ {reg['description']}")

        if evaluation["recommendations"]:
            lines.extend([
                "",
                "## 建议",
                "",
            ])
            for rec in evaluation["recommendations"]:
                lines.append(f"- {rec}")

        return '\n'.join(lines)


class AutoIterator:
    """自动迭代器主类"""

    def __init__(self, project_root: str = ".", version_file: Optional[str] = None):
        self.vi = VersionIterator(project_root, version_file)
        self.trigger_detector = IterationTriggerDetector(self.vi)
        self.release_automator = ReleaseAutomator(self.vi)
        self.effect_evaluator = IterationEffectEvaluator(self.vi)
        self.logger = self.vi.logger

    def check_iteration_needed(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """检查是否需要迭代"""
        triggers = self.trigger_detector.check_all_triggers(metrics)
        
        return {
            "needs_iteration": len(triggers) > 0,
            "triggered_conditions": [
                {
                    "type": t.trigger_type.value,
                    "threshold": t.threshold,
                    "current_value": t.current_value,
                    "details": t.details
                }
                for t in triggers
            ],
            "recommended_bump_type": self.trigger_detector.determine_bump_type(triggers).value if triggers else None
        }

    def trigger_iteration(
        self,
        metrics: Dict[str, Any],
        author: str = ""
    ) -> Optional[VersionEntry]:
        """基于触发条件执行自迭代"""
        triggers = self.trigger_detector.check_all_triggers(metrics)
        
        if not triggers:
            self.logger.info("没有触发自迭代条件")
            return None

        bump_type = self.trigger_detector.determine_bump_type(triggers)
        
        trigger_report = self.trigger_detector.generate_trigger_report(triggers)
        
        changes = [
            ChangeEntry(
                change_type=ChangeType.FIX if bump_type == VersionBumpType.PATCH else ChangeType.REFACTOR,
                description=f"自迭代修复: {t.trigger_type.value}",
                scope="auto_iteration",
                impact_level="medium"
            )
            for t in triggers
        ]

        entry = self.vi.iterate(
            bump_type=bump_type,
            changes=changes,
            author=author,
            notes=f"自动触发迭代\n\n{trigger_report}"
        )

        self.vi.history.iteration_triggers.extend(triggers)
        self.vi._save_history()

        return entry

    def auto_release(
        self,
        bump_type: VersionBumpType,
        changes: List[ChangeEntry],
        author: str = "",
        notes: str = "",
        run_tests: bool = True,
        create_tag: bool = True
    ) -> Dict[str, Any]:
        """自动发布流程"""
        self.logger.info(f"开始自动发布流程: {bump_type.value}")
        
        prepare_result = self.release_automator.prepare_release(
            bump_type=bump_type,
            changes=changes,
            author=author,
            notes=notes
        )
        
        execute_result = self.release_automator.execute_release(
            version=prepare_result["new_version"],
            create_tag=create_tag,
            run_tests=run_tests
        )
        
        return {
            "prepare": prepare_result,
            "execute": execute_result,
            "success": execute_result["success"]
        }

    def smart_iterate(
        self,
        changes: List[ChangeEntry],
        author: str = "",
        notes: str = "",
        auto_detect_type: bool = True
    ) -> VersionEntry:
        """智能迭代"""
        if auto_detect_type:
            has_breaking = any(c.breaking or c.change_type == ChangeType.BREAKING for c in changes)
            has_feature = any(c.change_type == ChangeType.FEATURE for c in changes)
            has_security = any(c.change_type == ChangeType.SECURITY for c in changes)
            
            if has_breaking:
                bump_type = VersionBumpType.MAJOR
            elif has_feature:
                bump_type = VersionBumpType.MINOR
            else:
                bump_type = VersionBumpType.PATCH
        else:
            bump_type = VersionBumpType.PATCH

        return self.vi.iterate(
            bump_type=bump_type,
            changes=changes,
            author=author,
            notes=notes
        )

    def evaluate_last_iteration(self, metrics_before: Dict[str, Any], metrics_after: Dict[str, Any]) -> Dict[str, Any]:
        """评估最后一次迭代效果"""
        if not self.vi.history.versions:
            return {"error": "没有版本历史"}
        
        last_version = self.vi.history.versions[0].version
        return self.effect_evaluator.evaluate_iteration(last_version, metrics_before, metrics_after)

    def integrate_with_fusion_engine(self, spec_path=None, max_cycles=3):
        """与 SDD-TDD 融合引擎对接
        
        在版本迭代的"执行改进"步骤中集成融合引擎，
        执行连续多轮深化循环以提升代码质量。
        
        Args:
            spec_path: 规范文件路径 (可选)
            max_cycles: 最大循环次数 (默认: 3)
            
        Returns:
            连续循环报告或 None
        """
        try:
            return self.vi.integrate_with_fusion_engine(spec_path, max_cycles)
        except Exception as e:
            self.logger.error(f"自动迭代器集成融合引擎失败: {e}")
            return None

    def get_iteration_status(self) -> Dict[str, Any]:
        """获取迭代状态"""
        status = self.vi.get_status()
        
        recent_triggers = [
            {
                "type": t.trigger_type.value,
                "triggered": t.triggered,
                "timestamp": t.timestamp.isoformat()
            }
            for t in self.vi.history.iteration_triggers[-10:]
        ]
        
        status["recent_triggers"] = recent_triggers
        status["auto_iteration_enabled"] = True
        
        return status

    def generate_iteration_report(self, output_path: Optional[str] = None) -> str:
        """生成迭代报告"""
        status = self.get_iteration_status()
        
        lines = [
            "# 自动迭代报告",
            f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"\n## 项目信息",
            f"- 项目名称: {status['project_name']}",
            f"- 当前版本: {status['current_version']}",
            f"- 迭代次数: {status['iteration_count']}",
            f"- 自动迭代: {'启用' if status['auto_iteration_enabled'] else '禁用'}",
        ]

        if status.get('recent_triggers'):
            lines.extend([
                f"\n## 最近触发条件",
                "| 类型 | 状态 | 时间 |",
                "|------|------|------|",
            ])
            
            for trigger in status['recent_triggers']:
                status_text = "✅ 触发" if trigger['triggered'] else "❌ 未触发"
                lines.append(
                    f"| {trigger['type']} | {status_text} | {trigger['timestamp'][:19]} |"
                )

        report = '\n'.join(lines)
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)
        
        return report


if __name__ == '__main__':
    print("自动迭代器模块已加载")
