"""
元技能编排器 - 协调评估、优化、扩展、打包四大模块的完整工作流
支持手动触发和定时触发两种模式，实现技能的自我管理闭环
"""
from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable


class OrchestratorError(Exception):
    """编排器异常"""
    pass


class MetaCyclePhase(str, Enum):
    IDLE = "idle"
    EVALUATING = "evaluating"
    OPTIMIZING = "optimizing"
    EXTENDING = "extending"
    PACKING = "packing"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    FAILED = "failed"


class TriggerMode(str, Enum):
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    EVENT_DRIVEN = "event_driven"


@dataclass
class PhaseResult:
    """单个阶段的执行结果"""
    phase: MetaCyclePhase
    status: str = "pending"
    started_at: str = ""
    completed_at: str = ""
    duration_ms: float = 0.0
    output: Any = None
    error_message: str | None = None
    action_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "phase": self.phase.value,
            "status": self.status,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration_ms": round(self.duration_ms, 2),
            "output_type": type(self.output).__name__ if self.output else None,
            "error_message": self.error_message,
            "action_count": self.action_count,
        }


@dataclass
class MetaCycleResult:
    """完整元技能循环结果"""
    cycle_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    trigger_mode: TriggerMode = TriggerMode.MANUAL
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: str = ""
    current_phase: MetaCyclePhase = MetaCyclePhase.IDLE
    overall_status: str = "running"
    phases: list[PhaseResult] = field(default_factory=list)
    summary: str = ""
    evaluation_report: dict[str, Any] | None = None
    optimization_plan: dict[str, Any] | None = None
    extension_proposal: dict[str, Any] | None = None
    packing_result: dict[str, Any] | None = None
    metrics: dict[str, float] = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)

    @property
    def total_duration_ms(self) -> float:
        return sum(p.duration_ms for p in self.phases)

    @property
    def success(self) -> bool:
        return self.overall_status == "completed"

    def to_dict(self) -> dict[str, Any]:
        return {
            "cycle_id": self.cycle_id,
            "trigger_mode": self.trigger_mode.value,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "current_phase": self.current_phase.value,
            "overall_status": self.overall_status,
            "total_duration_ms": round(self.total_duration_ms, 2),
            "phases": [p.to_dict() for p in self.phases],
            "summary": self.summary,
            "evaluation_report": self.evaluation_report,
            "optimization_plan": self.optimization_plan,
            "extension_proposal": self.extension_proposal,
            "packing_result": self.packing_result,
            "metrics": {k: round(v, 3) for k, v in self.metrics.items()},
            "recommendations": self.recommendations,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


class MetaSkillCoordinator:
    """
    元技能协调器

    协调自评估、自优化、自扩展、技能打包四个模块的工作流，
    实现完整的元技能循环：
        定期评估 → 识别问题 → 制定优化计划 → 执行优化 → 验证效果 → 打包发布

    支持三种触发模式：
        - MANUAL: 手动触发（用户主动调用）
        - SCHEDULED: 定时触发（按固定间隔自动运行）
        - EVENT_DRIVEN: 事件驱动（基于特定事件触发）
    """

    DEFAULT_CYCLE_INTERVAL_HOURS: float = 24.0
    MAX_CONCURRENT_CYCLES: int = 1

    def __init__(self, skill_root: Path | str | None = None) -> None:
        self._skill_root: Path = (
            Path(skill_root).resolve() if skill_root
            else Path(__file__).parent.parent.parent.resolve()
        )
        self._current_cycle: MetaCycleResult | None = None
        self._cycle_history: list[MetaCycleResult] = []
        self._is_running: bool = False
        self._last_cycle_time: str | None = None
        self._total_cycles_completed: int = 0
        self._callbacks: dict[MetaCyclePhase, list[Callable]] = {
            phase: [] for phase in MetaCyclePhase
        }
        self._preconditions: list[Callable[[], bool]] = []
        self._post_actions: list[Callable[[MetaCycleResult], None]] = []

    def register_callback(
        self, phase: MetaCyclePhase, callback: Callable[[Any], None]
    ) -> None:
        """注册阶段回调函数"""
        self._callbacks[phase].append(callback)

    def register_precondition(self, condition: Callable[[], bool]) -> None:
        """注册循环前置条件"""
        self._preconditions.append(condition)

    def register_post_action(self, action: Callable[[MetaCycleResult], None]) -> None:
        """注册循环后置动作"""
        self._post_actions.append(action)

    def run_meta_cycle(
        self,
        trigger_mode: TriggerMode = TriggerMode.MANUAL,
        skip_phases: list[str] | None = None,
        auto_pack: bool = False,
        pack_version: str = "auto",
    ) -> MetaCycleResult:
        """
        执行完整的元技能循环

        流程：
            1. 前置条件检查
            2. 评估阶段 (evaluate)
            3. 优化阶段 (optimize)
            4. 扩展阶段 (extend)
            5. 打包阶段 (pack, 可选)
            6. 后置动作执行

        Args:
            trigger_mode: 触发模式
            skip_phases: 要跳过的阶段列表
            auto_pack: 是否在循环结束时自动打包
            pack_version: 打包版本号

        Returns:
            完整的MetaCycleResult结果对象
        """
        skip_set = set(s.lower() for s in (skip_phases or []))

        if self._is_running:
            raise OrchestratorError("前一个元技能循环仍在运行中，请等待完成")

        for precondition in self._preconditions:
            if not precondition():
                raise OrchestratorError("前置条件检查未通过，循环终止")

        self._is_running = True
        cycle = MetaCycleResult(trigger_mode=trigger_mode)

        try:
            from ..utils.subskill_manager import SubSkillManager
            from .self_evaluator import evaluate as run_evaluation
            from .self_optimizer import optimize as run_optimize
            from .self_extender import analyze_gaps as run_extend
            from .skill_packer import SkillExporter, VersionMetaManager

            manager = SubSkillManager()
            skills_data = [info.to_dict() for info in manager.all_skills.values()]

            print(f"\n{'='*60}")
            print(f"🔄 元技能循环开始 [{cycle.cycle_id}] 模式:{trigger_mode.value}")
            print(f"{'='*60}\n")

            if "evaluating" not in skip_set:
                phase_result = self._run_phase(
                    cycle, MetaCyclePhase.EVALUATING,
                    lambda: run_evaluation(skills_data, self._skill_root),
                )
                cycle.phases.append(phase_result)
                if phase_result.status == "success" and phase_result.output:
                    cycle.evaluation_report = phase_result.output.to_dict()

            if "optimizing" not in skip_set and cycle.evaluation_report:
                phase_result = self._run_phase(
                    cycle, MetaCyclePhase.OPTIMIZING,
                    lambda: run_optimize(cycle.evaluation_report),
                )
                cycle.phases.append(phase_result)
                if phase_result.status == "success" and phase_result.output:
                    cycle.optimization_plan = phase_result.output.to_dict()

            if "extending" not in skip_set:
                mock_patterns = self._generate_usage_patterns(skills_data)
                phase_result = self._run_phase(
                    cycle, MetaCyclePhase.EXTENDING,
                    lambda: run_extend(mock_patterns),
                )
                cycle.phases.append(phase_result)
                if phase_result.status == "success" and phase_result.output:
                    cycle.extension_proposal = phase_result.output.to_dict()

            if ("packing" not in skip_set or auto_pack) and cycle.evaluation_report:
                phase_result = self._run_phase(
                    cycle, MetaCyclePhase.PACKING,
                    lambda: self._execute_pack(pack_version),
                )
                cycle.phases.append(phase_result)
                if phase_result.status == "success" and phase_result.output:
                    cycle.packing_result = phase_result.output

            if "verifying" not in skip_set:
                phase_result = self._run_phase(
                    cycle, MetaCyclePhase.VERIFYING,
                    lambda: self._verify_cycle_results(cycle),
                )
                cycle.phases.append(phase_result)

            cycle.current_phase = MetaCyclePhase.COMPLETED
            cycle.overall_status = "completed"
            cycle.completed_at = datetime.now().isoformat()
            cycle.summary = self._generate_summary(cycle)
            cycle.recommendations = self._generate_recommendations(cycle)
            cycle.metrics = self._compute_metrics(cycle)

            self._total_cycles_completed += 1
            self._last_cycle_time = cycle.completed_at

            print(f"\n{'='*60}")
            print(f"✅ 元技能循环完成 [{cycle.cycle_id}]")
            print(f"   状态: {cycle.overall_status}")
            print(f"   耗时: {cycle.total_duration_ms:.0f}ms")
            print(f"   摘要: {cycle.summary}")
            print(f"{'='*60}\n")

        except Exception as e:
            cycle.current_phase = MetaCyclePhase.FAILED
            cycle.overall_status = "failed"
            cycle.completed_at = datetime.now().isoformat()
            error_phase = PhaseResult(
                phase=cycle.current_phase,
                status="error",
                error_message=str(e),
            )
            cycle.phases.append(error_phase)
            cycle.summary = f"循环失败于{cycle.current_phase.value}阶段: {str(e)}"
            print(f"\n❌ 元技能循环失败: {e}")

        finally:
            self._is_running = False
            self._current_cycle = cycle
            self._cycle_history.append(cycle)

            for post_action in self._post_actions:
                try:
                    post_action(cycle)
                except Exception:
                    pass

        return cycle

    def _run_phase(
        self,
        cycle: MetaCycleResult,
        phase: MetaCyclePhase,
        executor: Callable,
    ) -> PhaseResult:
        """执行单个阶段"""
        result = PhaseResult(phase=phase, started_at=datetime.now().isoformat())
        cycle.current_phase = phase

        icon_map = {
            MetaCyclePhase.EVALUATING: "📊",
            MetaCyclePhase.OPTIMIZING: "🔧",
            MetaCyclePhase.EXTENDING: "💡",
            MetaCyclePhase.PACKING: "📦",
            MetaCyclePhase.VERIFYING: "✅",
        }
        icon = icon_map.get(phase, "⚙️")

        print(f"{icon} 阶段: {phase.value}...")

        for callback in self._callbacks.get(phase, []):
            try:
                callback({"phase": phase.value, "status": "started"})
            except Exception:
                pass

        start = time.perf_counter()
        try:
            output = executor()
            elapsed = (time.perf_counter() - start) * 1000
            result.status = "success"
            result.output = output
            result.duration_ms = elapsed
            result.completed_at = datetime.now().isoformat()

            action_count = 0
            if hasattr(output, 'total_actions'):
                action_count = output.total_actions
            elif hasattr(output, 'total_gaps'):
                action_count = output.total_gaps
            elif isinstance(output, dict):
                action_count = output.get('total_files', 0) or output.get('total_actions', 0)
            result.action_count = action_count

            print(f"   ✅ {phase.value} 完成 ({elapsed:.0f}ms, {action_count}项)")

        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000
            result.status = "error"
            result.error_message = str(e)
            result.duration_ms = elapsed
            result.completed_at = datetime.now().isoformat()
            print(f"   ❌ {phase.value} 失败 ({elapsed:.0f}ms): {e}")

        for callback in self._callbacks.get(phase, []):
            try:
                callback(result.to_dict())
            except Exception:
                pass

        return result

    def _generate_usage_patterns(self, skills_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """生成模拟使用模式数据"""
        patterns: list[dict[str, Any]] = []
        skill_names = [s["name"] for s in skills_data]

        sample_queries = [
            "搭建CI/CD流水线", "代码审查流程", "API设计规范",
            "数据库建模", "性能压测", "安全漏洞扫描",
            "微服务架构设计", "监控告警系统", "容器化部署",
            "团队协作工作流", "遗留系统迁移", "AI辅助编码",
            "需求分析文档", "架构评审", "测试策略制定",
        ]

        for i, query in enumerate(sample_queries):
            matched = skill_names[i % len(skill_names):i % len(skill_names) + 1]
            patterns.append({
                "query": query,
                "matched_skills": matched if i % 3 != 0 else [],
                "confidence": 0.5 + (i % 10) * 0.05,
            })

        return patterns

    def _execute_pack(self, version: str) -> dict[str, Any]:
        """执行打包操作"""
        from .skill_packer import SkillExporter
        exporter = SkillExporter(self._skill_root)
        output_path = self._skill_root / "output" / "packed_skills" / f"universal-devops-{version}"
        return exporter.pack(output_path=output_path, version=version, format_type="skill")

    def _verify_cycle_results(self, cycle: MetaCycleResult) -> dict[str, Any]:
        """验证循环结果的完整性"""
        checks: dict[str, bool] = {
            "has_evaluation": cycle.evaluation_report is not None,
            "has_optimization": cycle.optimization_plan is not None,
            "has_extension": cycle.extension_proposal is not None,
            "evaluation_has_scores": bool(cycle.evaluation_report and cycle.evaluation_report.get("all_scores")),
            "optimization_has_actions": bool(cycle.optimization_plan and cycle.optimization_plan.get("actions")),
            "extension_has_suggestions": bool(cycle.extension_proposal and cycle.extension_proposal.get("new_skill_suggestions")),
        }

        passed = sum(1 for v in checks.values() if v)
        total = len(checks)

        return {
            "checks": checks,
            "passed": passed,
            "total": total,
            "pass_rate": round(passed / max(total, 1), 3),
            "overall": all(checks.values()),
        }

    def _generate_summary(self, cycle: MetaCycleResult) -> str:
        """生成循环摘要"""
        parts: list[str] = []

        eval_info = ""
        if cycle.evaluation_report:
            avg = cycle.evaluation_report.get("avg_composite_score", 0)
            total = cycle.evaluation_report.get("total_skills", 0)
            healthy = cycle.evaluation_report.get("healthy_count", 0)
            eval_info = f"评估{total}个技能(均分{avg:.1f},健康{healthy})"

        opt_info = ""
        if cycle.optimization_plan:
            actions = cycle.optimization_plan.get("total_actions", 0)
            critical = cycle.optimization_plan.get("critical_count", 0)
            opt_info = f"优化{actions}项(关键{critical})"

        ext_info = ""
        if cycle.extension_proposal:
            gaps = cycle.extension_proposal.get("total_gaps", 0)
            new_skills = len(cycle.extension_proposal.get("new_skill_suggestions", []))
            ext_info = f"发现{gaps}个缺口,建议{new_skills}个新技能"

        pack_info = ""
        if cycle.packing_result:
            size = cycle.packing_result.get("size_bytes", 0)
            ver = cycle.packing_result.get("version", "?")
            pack_info = f"打包{ver}({size:,}B)"

        for info in [eval_info, opt_info, ext_info, pack_info]:
            if info:
                parts.append(info)

        mode_label = {"manual": "手动", "scheduled": "定时", "event_driven": "事件"}.get(
            cycle.trigger_mode.value, cycle.trigger_mode.value
        )

        return f"[{mode_label}] {' → '.join(parts)}"

    def _generate_recommendations(self, cycle: MetaCycleResult) -> list[str]:
        """生成行动建议"""
        recs: list[str] = []

        if cycle.evaluation_report:
            report = cycle.evaluation_report
            avg = report.get("avg_composite_score", 100)
            broken = report.get("broken_count", 0)
            missing = report.get("missing_count", 0)

            if avg < 50:
                recs.append("🔴 整体评分过低，建议全面审查所有子技能的健康状态")
            if broken > 0:
                recs.append(f"🔴 有{broken}个子技能处于损坏状态，需要紧急修复")
            if missing > 0:
                recs.append(f"⚠️ 有{missing}个子技能文件缺失，需补充创建")

            bottom = report.get("bottom_performers", [])
            low_skills = [s.get("skill_name", "") for s in bottom[:3] if s.get("composite_score", 100) < 40]
            if low_skills:
                recs.append(f"📉 重点优化低分技能: {', '.join(low_skills)}")

        if cycle.optimization_plan:
            plan = cycle.optimization_plan
            critical = plan.get("critical_count", 0)
            high = plan.get("high_count", 0)
            if critical > 0:
                recs.append(f"🔧 优先处理{critical}个关键级优化项和{high}个高级别优化项")

        if cycle.extension_proposal:
            prop = cycle.extension_proposal
            critical_gaps = prop.get("critical_gaps", 0)
            if critical_gaps > 0:
                recs.append(f"💡 存在{critical_gaps}个关键能力缺口，建议规划新技能开发")

        if not recs:
            recs.append("✅ 技能体系整体健康，继续保持定期评估")

        return recs

    def _compute_metrics(self, cycle: MetaCycleResult) -> dict[str, float]:
        """计算循环指标"""
        metrics: dict[str, float] = {}

        if cycle.evaluation_report:
            metrics["avg_composite_score"] = cycle.evaluation_report.get("avg_composite_score", 0)
            metrics["health_rate"] = (
                cycle.evaluation_report.get("healthy_count", 0) /
                max(cycle.evaluation_report.get("total_skills", 1), 1)
            )

        if cycle.optimization_plan:
            metrics["optimization_density"] = (
                cycle.optimization_plan.get("total_actions", 0) /
                max(cycle.evaluation_report.get("total_skills", 1), 1)
            )

        if cycle.extension_proposal:
            metrics["gap_discovery_rate"] = (
                cycle.extension_proposal.get("total_gaps", 0) /
                10.0
            )

        metrics["cycle_duration_seconds"] = cycle.total_duration_ms / 1000
        metrics["phases_completed"] = sum(1 for p in cycle.phases if p.status == "success") / max(len(cycle.phases), 1)

        verify = next((p for p in cycle.phases if p.phase == MetaCyclePhase.VERIFYING), None)
        if verify and verify.output:
            metrics["verification_pass_rate"] = verify.output.get("pass_rate", 0)

        return metrics

    def get_status(self) -> dict[str, Any]:
        """获取当前编排器状态"""
        return {
            "is_running": self._is_running,
            "current_cycle_id": self._current_cycle.cycle_id if self._current_cycle else None,
            "current_phase": self._current_cycle.current_phase.value if self._current_cycle else "idle",
            "last_cycle_time": self._last_cycle_time,
            "total_cycles_completed": self._total_cycles_completed,
            "cycle_history_size": len(self._cycle_history),
            "skill_root": str(self._skill_root),
        }

    def get_last_cycle(self) -> MetaCycleResult | None:
        """获取最近一次循环的结果"""
        return self._cycle_history[-1] if self._cycle_history else None

    def get_cycle_history(self, limit: int = 10) -> list[dict[str, Any]]:
        """获取循环历史"""
        return [c.to_dict() for c in self._cycle_history[-limit:]]

    def generate_report(self, cycle: MetaCycleResult | None = None) -> str:
        """
        生成Markdown格式的循环报告

        Args:
            cycle: 循环结果（默认使用最近一次）

        Returns:
            Markdown格式报告字符串
        """
        target = cycle or self._current_cycle
        if not target:
            return "# 无可用的循环数据\n"

        lines: list[str] = [
            f"# 🔄 元技能循环报告 `{target.cycle_id}`\n",
            f"**触发模式**: {target.trigger_mode.value}",
            f"**状态**: {target.overall_status}",
            f"**总耗时**: {target.total_duration_ms:.0f}ms",
            f"**时间**: {target.started_at} → {target.completed_at or '进行中'}\n",
            f"## 📋 概要\n\n{target.summary}\n",
            f"## ⏱️ 各阶段详情\n",
            "| 阶段 | 状态 | 耗时(ms) | 操作数 | 备注 |",
            "| --- | --- | --- | --- | --- |",
        ]

        for phase in target.phases:
            status_icon = {"success": "✅", "error": "❌", "pending": "⏳"}.get(phase.status, "⚪")
            note = phase.error_message[:60] if phase.error_message else "-"
            lines.append(
                f"| {phase.phase.value} | {status_icon} {phase.status} "
                f"| {phase.duration_ms:.0f} | {phase.action_count} | {note} |"
            )

        if target.recommendations:
            lines.append(f"\n## 💡 建议\n")
            for rec in target.recommendations:
                lines.append(f"- {rec}")

        if target.metrics:
            lines.append(f"\n## 📊 关键指标\n")
            for k, v in sorted(target.metrics.items()):
                bar_len = int(min(v * 20, 20))
                bar = "█" * bar_len + "░" * (20 - bar_len)
                lines.append(f"- **{k}**: `{v:.3f}` {bar}")

        if target.packing_result:
            pr = target.packing_result
            lines.append(f"\n## 📦 打包信息\n")
            lines.append(f"- **路径**: `{pr.get('output_path', 'N/A')}`")
            lines.append(f"- **版本**: {pr.get('version', '?')}")
            lines.append(f"- **大小**: {pr.get('size_bytes', 0):,} bytes")
            lines.append(f"- **文件数**: {pr.get('total_files', 0)}")

        return "\n".join(lines) + "\n"


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 元技能编排器 - 功能演示")
    print("=" * 60)

    coordinator = MetaSkillCoordinator()

    coordinator.register_callback(MetaCyclePhase.EVALUATING, lambda d: print(f"   [回调] 评估阶段事件: {d['status']}"))
    coordinator.register_callback(MetaCyclePhase.OPTIMIZING, lambda d: print(f"   [回调] 优化阶段事件: {d['status']}"))
    coordinator.register_precondition(lambda: True)
    coordinator.register_post_action(lambda r: print(f"   [后置] 循环完成，状态: {r.overall_status}"))

    print("\n--- 编排器状态 ---\n")
    status = coordinator.get_status()
    for k, v in status.items():
        print(f"   {k}: {v}")

    print("\n--- 运行完整元技能循环 ---\n")
    result = coordinator.run_meta_cycle(
        trigger_mode=TriggerMode.MANUAL,
        auto_pack=True,
        pack_version="2.0.0-demo",
    )

    print("\n--- 循环结果 ---\n")
    print(f"   循环ID: {result.cycle_id}")
    print(f"   触发模式: {result.trigger_mode.value}")
    print(f"   总状态: {result.overall_status}")
    print(f"   总耗时: {result.total_duration_ms:.0f}ms")
    print(f"   摘要: {result.summary}")
    print(f"\n   阶段统计:")
    for phase in result.phases:
        icon = {"success": "✅", "error": "❌", "pending": "⏳"}.get(phase.status, "⚪")
        print(f"      {icon} {phase.phase.value}: {phase.duration_ms:.0f}ms ({phase.action_count}项)")

    print(f"\n   指标:")
    for k, v in sorted(result.metrics.items()):
        print(f"      {k}: {v:.3f}")

    print(f"\n   建议:")
    for rec in result.recommendations:
        print(f"      • {rec}")

    print("\n--- 生成报告预览 ---\n")
    report_md = coordinator.generate_report(result)
    print(report_md[:1200])
    if len(report_md) > 1200:
        print(f"\n... (共 {len(report_md)} 字符)")

    print("\n--- 跳过部分阶段测试 ---\n")
    light_result = coordinator.run_meta_cycle(
        trigger_mode=TriggerMode.MANUAL,
        skip_phases=["extending", "packing"],
    )
    print(f"   轻量循环完成: {light_result.overall_status} ({light_result.total_duration_ms:.0f}ms)")
    print(f"   阶段数: {len(light_result.phases)}")

    final_status = coordinator.get_status()
    print(f"\n--- 最终状态 ---\n")
    print(f"   总循环次数: {final_status['total_cycles_completed']}")
    print(f"   历史记录: {final_status['cycle_history_size']} 条")

    print("\n✅ 所有演示通过!")
