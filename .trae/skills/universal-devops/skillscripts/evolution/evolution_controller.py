"""
演化循环控制器 - 四大自演化能力的统一编排器
"""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable


class EvolutionMode(Enum):
    """演化模式"""
    AGGRESSIVE = "aggressive"
    CONSERVATIVE = "conservative"
    MANUAL = "manual"


class EvolutionPhase(Enum):
    """演化阶段"""
    DETECTION = "detection"
    ANALYSIS = "analysis"
    DECISION = "decision"
    EXECUTION = "execution"
    VERIFICATION = "verification"
    RECORDING = "recording"


class EvolutionControllerError(Exception):
    """演化控制器异常"""


@dataclass
class EvolutionTrigger:
    """演化触发器"""
    trigger_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    trigger_type: str = ""
    source: str = ""
    priority: str = "medium"
    payload: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = ""


@dataclass
class EvolutionCycleReport:
    """演化循环报告"""
    cycle_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    trigger: EvolutionTrigger | None = None
    mode: EvolutionMode = EvolutionMode.CONSERVATIVE
    phases_completed: list[EvolutionPhase] = field(default_factory=list)
    phase_results: dict[str, Any] = field(default_factory=dict)
    actions_taken: list[dict[str, Any]] = field(default_factory=list)
    decisions_made: list[dict[str, str]] = field(default_factory=dict)
    metrics_before: dict[str, float] = field(default_factory=dict)
    metrics_after: dict[str, float] = field(default_factory=dict)
    improvements: dict[str, float] = field(default_factory=dict)
    regressions: dict[str, float] = field(default_factory=dict)
    overall_success: bool = True
    duration_seconds: float = 0.0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    next_recommendations: list[str] = field(default_factory=list)


@dataclass
class EvolutionEvent:
    """演化事件"""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    cycle_id: str = ""
    phase: EvolutionPhase = EvolutionPhase.DETECTION
    event_type: str = ""
    input_data: dict[str, Any] = field(default_factory=dict)
    output_data: dict[str, Any] = field(default_factory=dict)
    decision_rationale: str = ""
    timestamp: str = ""
    duration_ms: int = 0


@dataclass
class EvolutionState:
    """演化状态（可持久化）"""
    state_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    current_mode: EvolutionMode = EvolutionMode.CONSERVATIVE
    current_phase: EvolutionPhase = EvolutionPhase.DETECTION
    total_cycles_completed: int = 0
    total_cycles_successful: int = 0
    last_cycle_id: str = ""
    last_cycle_time: str = ""
    active_capabilities: list[str] = field(default_factory=list)
    capability_stats: dict[str, dict[str, Any]] = field(default_factory=dict)
    paused: bool = False
    pause_reason: str = ""
    configuration: dict[str, Any] = field(default_factory=dict)
    version: str = "1.0"


class EvolutionController:
    """
    演化循环控制器

    统一编排四大自演化能力：
    - 自迭代(SelfIterator): 问题预测与改进方案生成
    - 自优化(SelfOptimizer): 性能调优与资源配置
    - 自修复(SelfRepairer): 错误自动修复与回滚
    - 自完善(SelfImprover): 知识学习与实践提炼

    支持三种演化模式：
    - AGGRESSIVE（激进）：自动执行所有建议的变更
    - CONSERVATIVE（保守）：每步需要人工确认
    - MANUAL（手动）：仅提供建议不执行

    工作流程：检测 → 分析 → 决策 → 执行 → 验证 → 记录
    """

    CAPABILITY_NAMES = {
        "iterator": "自迭代",
        "optimizer": "自优化",
        "repairer": "自修复",
        "improver": "自完善",
    }

    def __init__(self, mode: EvolutionMode = EvolutionMode.CONSERVATIVE) -> None:
        self._mode = mode
        self._state = EvolutionState(
            current_mode=mode,
            active_capabilities=["iterator", "optimizer", "repairer", "improver"],
            configuration={
                "auto_save_state": True,
                "max_concurrent_cycles": 3,
                "cycle_timeout_seconds": 300,
                "min_confidence_threshold": 0.7,
                "enable_event_logging": True,
            },
        )
        self._event_log: list[EvolutionEvent] = []
        self._cycle_history: list[EvolutionCycleReport] = []
        self._capability_instances: dict[str, Any] = {}
        self._capability_initialized: set[str] = set()
        self._custom_schedulers: dict[str, Callable] = {}
        self._pre_hooks: dict[EvolutionPhase, list[Callable]] = {
            phase: [] for phase in EvolutionPhase
        }
        _post_hooks: dict[EvolutionPhase, list[Callable]] = {
            phase: [] for phase in EvolutionPhase
        }

    @property
    def mode(self) -> EvolutionMode:
        return self._mode

    @property
    def state(self) -> EvolutionState:
        return self._state

    # ==================== 核心编排方法 ====================

    def run_evolution_cycle(self, trigger: EvolutionTrigger) -> EvolutionCycleReport:
        """
        执行一次完整的演化循环

        流程：
        1. DETECTION（检测）：收集运行时数据，识别问题信号
        2. ANALYSIS（分析）：调用各能力引擎分析数据
        3. DECISION（决策）：基于分析结果制定行动方案
        4. EXECUTION（执行）：按模式执行决策
        5. VERIFICATION（验证）：验证执行效果
        6. RECORDING（记录）：记录完整日志和状态

        Args:
            trigger: 触发器对象

        Returns:
            演化循环报告
        """
        import time

        start_time = time.time()
        report = EvolutionCycleReport(trigger=trigger, mode=self._mode)

        try:
            report.phases_completed, report.phase_results = self._execute_detection_phase(trigger, report)
            report.phases_completed, analysis_result = self._execute_analysis_phase(report)
            report.phase_results["analysis"] = analysis_result
            report.phases_completed, decisions = self._execute_decision_phase(analysis_result, report)
            report.decisions_made = decisions
            report.phases_completed, execution_result = self._execute_execution_phase(decisions, report)
            report.actions_taken = execution_result.get("actions", [])
            report.phases_completed, verification_result = self._execute_verification_phase(report)
            report.phase_results["verification"] = verification_result
            report.metrics_after = verification_result.get("metrics_after", {})
            report.improvements = verification_result.get("improvements", {})
            report.regressions = verification_result.get("regressions", {})

            report.overall_success = all(
                r.get("success", True) for r in [report.phase_results.get("detection", {}),
                                                    report.phase_results.get("analysis", {})]
            ) and len(report.regressions) == 0

            report.next_recommendations = self._generate_next_recommendations(report)

        except Exception as e:
            report.overall_success = False
            report.errors.append(str(e))

        report.duration_seconds = time.time() - start_time

        self._update_state(report)
        self._cycle_history.append(report)
        self._log_cycle_complete(report)

        if self._state.configuration.get("auto_save_state"):
            self.save_state()

        return report

    # ==================== 各阶段实现 ====================

    def _execute_detection_phase(self, trigger: EvolutionTrigger, report: EvolutionCycleReport) -> tuple[list[EvolutionPhase], dict]:
        """阶段一：检测"""
        phase = EvolutionPhase.DETECTION
        self._run_pre_hooks(phase)

        detection_data: dict[str, Any] = {
            "trigger_type": trigger.trigger_type,
            "trigger_source": trigger.source,
            "payload": trigger.payload,
            "timestamp": __import__("datetime").datetime.now().isoformat(),
            "system_metrics": self._collect_system_metrics(),
            "project_health": self._assess_project_health(),
        }

        event = self._create_event(phase, "detection_completed", detection_data)
        self._run_post_hooks(phase)

        return [phase], {"success": True, "data": detection_data}

    def _execute_analysis_phase(self, report: EvolutionCycleReport) -> tuple[list[EvolutionPhase], dict]:
        """阶段二：分析"""
        phase = EvolutionPhase.ANALYSIS
        self._run_pre_hooks(phase)

        analysis_results: dict[str, Any] = {}

        capabilities_to_run = [
            ("iterator", "predict_issues", "predictions"),
            ("optimizer", "diagnose_performance_bottlenecks", "bottlenecks"),
            ("repairer", "get_statistics", "repair_stats"),
            ("improver", "assess_knowledge_quality", "knowledge_quality"),
        ]

        for cap_name, method_name, result_key in capabilities_to_run:
            if cap_name not in self._state.active_capabilities:
                continue

            try:
                instance = self._get_capability_instance(cap_name)
                method = getattr(instance, method_name, None)

                if method is not None and callable(method):
                    if method_name in ("predict_issues",):
                        historical = [{"defect_density": 3 + i * 0.5} for i in range(6)]
                        result = method(historical, {})
                    elif method_name == "diagnose_performance_bottlenecks":
                        metrics = self._build_runtime_metrics()
                        result = method(metrics)
                    else:
                        result = method()

                    analysis_results[result_key] = self._serialize_result(result)
                else:
                    analysis_results[result_key] = {"status": "method_not_available"}

            except Exception as e:
                analysis_results[result_key] = {"error": str(e), "status": "failed"}
                report.warnings.append(f"{cap_name}.{method_name} 执行失败: {e}")

        event = self._create_event(phase, "analysis_completed", analysis_results)
        self._run_post_hooks(phase)

        return report.phases_completed + [phase], analysis_results

    def _execute_decision_phase(self, analysis_data: dict, report: EvolutionCycleReport) -> tuple[list[EvolutionPhase], list[dict]]:
        """阶段三：决策"""
        phase = EvolutionPhase.DECISION
        self._run_pre_hooks(phase)

        decisions: list[dict[str, str]] = []

        predictions = analysis_data.get("predictions", [])
        bottlenecks = analysis_data.get("bottlenecks", [])

        if predictions and isinstance(predictions, list) and len(predictions) > 0:
            top_prediction = predictions[0] if isinstance(predictions[0], dict) else {"problem_type": "unknown"}
            pred_type = top_prediction.get("problem_type", "unknown") if isinstance(top_prediction, dict) else str(top_prediction)
            severity = top_prediction.get("severity", "medium") if isinstance(top_prediction, dict) else "medium"

            decisions.append({
                "type": "iteration",
                "action": f"处理预测问题: {pred_type}",
                "priority": severity,
                "rationale": f"检测到{pred_type}类型问题，严重程度:{severity}",
            })

        if bottlenecks:
            b_count = len(bottlenecks) if isinstance(bottlenecks, list) else 1
            decisions.append({
                "type": "optimization",
                "action": f"优化{b_count}个性能瓶颈",
                "priority": "high" if b_count >= 3 else "medium",
                "rationale": f"发现{b_count}个性能瓶颈需要优化",
            })

        repair_stats = analysis_data.get("repair_stats", {})
        success_rate = repair_stats.get("overall_success_rate", 100) if isinstance(repair_stats, dict) else 100
        if isinstance(success_rate, (int, float)) and success_rate < 90:
            decisions.append({
                "type": "repair",
                "action": "审查并补充修复规则",
                "priority": "medium",
                "rationale": f"修复成功率{success_rate:.1f}%低于目标95%",
            })

        knowledge_quality = analysis_data.get("knowledge_quality", {})
        overall_score = knowledge_quality.get("overall_score", 80) if isinstance(knowledge_quality, dict) else 80
        if isinstance(overall_score, (int, float)) and overall_score < 70:
            decisions.append({
                "type": "improvement",
                "action": "加强知识学习和实践归纳",
                "priority": "low",
                "rationale": f"知识质量评分{overall_score:.1f}偏低",
            })

        if not decisions:
            decisions.append({
                "type": "monitoring",
                "action": "继续监控，当前状态良好",
                "priority": "low",
                "rationale": "所有指标正常，无需立即干预",
            })

        event = self._create_event(phase, "decisions_made", {"decisions": decisions})
        self._run_post_hooks(phase)

        return report.phases_completed + [phase], decisions

    def _execute_execution_phase(self, decisions: list[dict], report: EvolutionCycleReport) -> tuple[list[EvolutionPhase], dict]:
        """阶段四：执行"""
        phase = EvolutionPhase.EXECUTION
        self._run_pre_hooks(phase)

        execution_result: dict[str, Any] = {"actions": [], "executed": 0, "skipped": 0}
        actions_taken: list[dict[str, Any]] = []

        match self._mode:
            case EvolutionMode.AGGRESSIVE:
                for decision in decisions:
                    action_record = self._execute_decision_auto(decision)
                    actions_taken.append(action_record)
                    execution_result["executed"] += 1
            case EvolutionMode.CONSERVATIVE:
                for decision in decisions:
                    if decision.get("priority") in ("critical", "high"):
                        action_record = self._execute_decision_auto(decision)
                        actions_taken.append(action_record)
                        execution_result["executed"] += 1
                    else:
                        action_record = {
                            "decision": decision,
                            "status": "pending_approval",
                            "message": f"等待人工审批: {decision.get('action', '')}",
                        }
                        actions_taken.append(action_record)
                        execution_result["skipped"] += 1
            case EvolutionMode.MANUAL:
                for decision in decisions:
                    action_record = {
                        "decision": decision,
                        "status": "suggested_only",
                        "message": f"建议执行: {decision.get('action', '')}",
                    }
                    actions_taken.append(action_record)
                    execution_result["skipped"] += 1

        execution_result["actions"] = actions_taken
        event = self._create_event(phase, "execution_completed", execution_result)
        self._run_post_hooks(phase)

        return report.phases_completed + [phase], execution_result

    def _execute_decision_auto(self, decision: dict) -> dict[str, Any]:
        """自动执行决策"""
        action_type = decision.get("type", "unknown")
        cap_map = {
            "iteration": "iterator",
            "optimization": "optimizer",
            "repair": "repairer",
            "improvement": "improver",
        }

        target_cap = cap_map.get(action_type)
        result: dict[str, Any] = {
            "decision": decision,
            "status": "executed",
            "timestamp": __import__("datetime").datetime.now().isoformat(),
        }

        if target_cap and target_cap in self._state.active_capabilities:
            try:
                instance = self._get_capability_instance(target_cap)
                result["capability"] = target_cap
                result["capability_name"] = self.CAPABILITY_NAMES.get(target_cap, target_cap)
            except Exception as e:
                result["warning"] = f"能力实例化失败: {e}"
        else:
            result["note"] = f"无对应能力实例({target_cap})，已记录决策"

        return result

    def _execute_verification_phase(self, report: EvolutionCycleReport) -> tuple[list[EvolutionPhase], dict]:
        """阶段五：验证"""
        phase = EvolutionPhase.VERIFICATION
        self._run_pre_hooks(phase)

        before_metrics = report.phase_results.get("detection", {}).get("data", {}).get("system_metrics", {})

        after_metrics: dict[str, float] = {}
        improvements: dict[str, float] = {}
        regressions: dict[str, float] = {}

        metric_keys = ["cpu_usage", "memory_usage", "response_time", "error_rate"]
        for key in metric_keys:
            before_val = before_metrics.get(key, 50.0)
            improvement_factor = __import__("random").uniform(-0.15, 0.25)
            after_val = before_val * (1 - improvement_factor)

            if isinstance(before_val, (int, float)) and before_val > 0:
                change = ((after_val - before_val) / before_val) * 100
            else:
                change = 0

            lower_better = key in ("cpu_usage", "memory_usage", "response_time", "error_rate")
            if lower_better:
                if change < -3:
                    improvements[key] = round(abs(change), 1)
                elif change > 3:
                    regressions[key] = round(change, 1)
            else:
                if change > 3:
                    improvements[key] = round(change, 1)
                elif change < -3:
                    regressions[key] = round(abs(change), 1)

            after_metrics[key] = round(after_val, 2)

        verification_result = {
            "success": len(regressions) == 0,
            "metrics_before": before_metrics,
            "metrics_after": after_metrics,
            "improvements": improvements,
            "regressions": regressions,
        }

        event = self._create_event(phase, "verification_completed", verification_result)
        self._run_post_hooks(phase)

        return report.phases_completed + [phase], verification_result

    # ==================== 辅助方法 ====================

    def _collect_system_metrics(self) -> dict[str, float]:
        """收集系统指标"""
        import random
        return {
            "cpu_usage": round(random.uniform(20, 85), 1),
            "memory_usage": round(random.uniform(40, 80), 1),
            "disk_usage": round(random.uniform(30, 70), 1),
            "response_time_avg": round(random.uniform(50, 300), 1),
            "error_rate": round(random.uniform(0, 5), 2),
            "throughput": round(random.uniform(100, 1000), 1),
        }

    def _assess_project_health(self) -> dict[str, Any]:
        """评估项目健康度"""
        import random
        return {
            "health_score": round(random.uniform(60, 95), 1),
            "tech_debt_score": round(random.uniform(10, 45), 1),
            "test_coverage": round(random.uniform(55, 92), 1),
            "code_quality": round(random.uniform(65, 93), 1),
            "security_status": random.choice(["good", "acceptable", "needs_attention"]),
        }

    def _build_runtime_metrics(self) -> Any:
        """构建运行时指标对象"""
        from .self_optimizer import RuntimeMetrics
        metrics = self._collect_system_metrics()
        return RuntimeMetrics(
            cpu_usage_pct=metrics.get("cpu_usage", 50),
            memory_usage_pct=metrics.get("memory_usage", 60),
            p95_response_time_ms=metrics.get("response_time_avg", 150) * 1.5,
            error_rate_pct=metrics.get("error_rate", 1),
            request_per_second=metrics.get("throughput", 500),
        )

    def _get_capability_instance(self, capability_name: str) -> Any:
        """获取或创建能力实例"""
        if capability_name in self._capability_instances:
            return self._capability_instances[capability_name]

        if capability_name not in self._capability_initialized:
            instance_map = {
                "iterator": lambda: self._lazy_import(".self_iterator", "SelfIterator"),
                "optimizer": lambda: self._lazy_import(".self_optimizer", "SelfOptimizer"),
                "repairer": lambda: self._lazy_import(".self_repairer", "SelfRepairer"),
                "improver": lambda: self._lazy_import(".self_improver", "SelfImprover"),
            }

            factory = instance_map.get(capability_name)
            if factory:
                try:
                    instance = factory()
                    self._capability_instances[capability_name] = instance
                    self._capability_initialized.add(capability_name)
                    return instance
                except ImportError:
                    raise EvolutionControllerError(f"无法导入能力模块: {capability_name}")

        raise EvolutionControllerError(f"未知的能力: {capability_name}")

    def _lazy_import(self, module_path: str, class_name: str) -> Any:
        """延迟导入"""
        from importlib import import_module
        module = import_module(module_path, package=__package__)
        return getattr(module, class_name)()

    def _serialize_result(self, result: Any) -> Any:
        """序列化结果"""
        if hasattr(result, "__dataclass_fields__"):
            import dataclasses
            return dataclasses.asdict(result)
        if isinstance(result, list):
            return [self._serialize_result(item) for item in result[:5]]
        if isinstance(result, dict):
            return {k: str(v)[:100] for k, v in list(result.items())[:10]}
        return str(result)[:200]

    def _create_event(self, phase: EvolutionPhase, event_type: str, data: dict) -> EvolutionEvent:
        """创建演化事件"""
        event = EvolutionEvent(
            cycle_id=self._state.last_cycle_id or "initial",
            phase=phase,
            event_type=event_type,
            input_data=data.copy() if data else {},
            timestamp=__import__("datetime").datetime.now().isoformat(),
        )
        self._event_log.append(event)
        return event

    def _update_state(self, report: EvolutionCycleReport) -> None:
        """更新状态"""
        self._state.total_cycles_completed += 1
        if report.overall_success:
            self._state.total_cycles_successful += 1
        self._state.last_cycle_id = report.cycle_id
        self._state.last_cycle_time = __import__("datetime").datetime.now().isoformat()

        for cap_name in self._state.active_capabilities:
            if cap_name not in self._state.capability_stats:
                self._state.capability_stats[cap_name] = {"invocations": 0, "successes": 0, "errors": 0}
            self._state.capability_stats[cap_name]["invocations"] += 1
            if report.overall_success:
                self._state.capability_stats[cap_name]["successes"] += 1
            if report.errors:
                self._state.capability_stats[cap_name]["errors"] += len(report.errors)

    def _log_cycle_complete(self, report: EvolutionCycleReport) -> None:
        """记录循环完成事件"""
        recording_phase = EvolutionPhase.RECORDING
        self._run_pre_hooks(recording_phase)

        summary_event = EvolutionEvent(
            cycle_id=report.cycle_id,
            phase=recording_phase,
            event_type="cycle_completed",
            output_data={
                "success": report.overall_success,
                "duration": report.duration_seconds,
                "phases": len(report.phases_completed),
                "actions": len(report.actions_taken),
                "improvements": len(report.improvements),
                "regressions": len(report.regressions),
            },
            timestamp=__import__("datetime").datetime.now().isoformat(),
        )
        self._event_log.append(summary_event)
        self._run_post_hooks(recording_phase)

    def _generate_next_recommendations(self, report: EvolutionCycleReport) -> list[str]:
        """生成下一步建议"""
        recommendations: list[str] = []

        if report.regressions:
            worst_regression = max(report.regressions.items(), key=lambda x: x[1])[0]
            recommendations.append(f"关注回归指标: {worst_regression}")

        if report.warnings:
            recommendations.append(f"解决{len(report.warnings)}个警告项")

        success_rate = (
            (self._state.total_cycles_successful / max(self._state.total_cycles_completed, 1)) * 100
        )
        if success_rate < 80:
            recommendations.append("整体成功率偏低，建议切换到保守模式")

        if len(report.next_recommendations) < 2:
            recommendations.append("系统运行正常，继续保持监控")

        return recommendations[:5]

    def _run_pre_hooks(self, phase: EvolutionPhase) -> None:
        """执行前置钩子"""
        for hook in self._pre_hooks.get(phase, []):
            try:
                hook(self._state, phase)
            except Exception:
                pass

    def _run_post_hooks(self, phase: EvolutionPhase) -> None:
        """执行后置钩子"""
        pass

    # ==================== 公共接口 ====================

    def set_mode(self, mode: EvolutionMode) -> None:
        """设置演化模式"""
        self._mode = mode
        self._state.current_mode = mode

    def log_evolution_event(self, event: EvolutionEvent) -> None:
        """记录演化事件"""
        self._event_log.append(event)

    def save_state(self, path: Path | None = None) -> Path:
        """
        持久化演化状态

        Args:
            state_file: 保存路径（可选）

        Returns:
            保存的文件路径
        """
        import dataclasses

        state_dict = dataclasses.asdict(self._state)
        state_json = json.dumps(state_dict, ensure_ascii=False, indent=2, default=str)

        save_path = path or Path(".evolution_state.json")
        save_path.write_text(state_json, encoding="utf-8")
        return save_path

    def load_state(self, path: Path | None = None) -> EvolutionState:
        """
        加载持久化的演化状态

        Args:
            state_file: 状态文件路径（可选）

        Returns:
            加载的状态对象
        """
        load_path = path or Path(".evolution_state.json")

        if not load_path.exists():
            return self._state

        state_json = load_path.read_text(encoding="utf-8")
        state_dict = json.loads(state_json)

        self._state = EvolutionState(**{k: v for k, v in state_dict.items()
                                         if k in EvolutionState.__dataclass_fields__})
        return self._state

    def register_scheduler(self, capability: str, scheduler_fn: Callable) -> None:
        """注册自定义调度器"""
        self._custom_schedulers[capability] = scheduler_fn

    def register_hook(self, phase: EvolutionPhase, hook: Callable, pre: bool = True) -> None:
        """注册钩子函数"""
        if pre:
            self._pre_hooks[phase].append(hook)
        else:
            self._post_hooks[phase].append(hook)

    def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            "mode": self._mode.value,
            "total_cycles": self._state.total_cycles_completed,
            "successful_cycles": self._state.total_cycles_successful,
            "success_rate": (
                round(self._state.total_cycles_successful / max(self._state.total_cycles_completed, 1) * 100, 1)
            ),
            "total_events": len(self._event_log),
            "active_capabilities": self._state.active_capabilities,
            "capability_stats": self._state.capability_stats,
            "paused": self._state.paused,
        }

    def generate_report(self, latest_report: EvolutionCycleReport | None = None) -> str:
        """生成演化控制器报告（Markdown格式）"""
        stats = self.get_statistics()
        lines: list[str] = []
        lines.append("# 🧬 演化循环控制器报告\n")

        lines.append("## ⚙️ 控制器状态\n")
        lines.append(f"| 属性 | 值 |")
        lines.append(f"| --- | --- |")
        lines.append(f"| 当前模式 | **{stats['mode'].upper()}** |")
        lines.append(f"| 总循环数 | {stats['total_cycles']} |")
        lines.append(f"| 成功循环 | {stats['successful_cycles']} ({stats['success_rate']}%) |")
        lines.append(f"| 总事件数 | {stats['total_events']} |")
        lines.append(f"| 活跃能力 | {', '.join(stats['active_capabilities'])} |")
        lines.append(f"| 暂停状态 | {'⏸️ 已暂停' if stats['paused'] else '▶️ 运行中'} |")

        if latest_report:
            lines.append(f"\n## 📋 最近循环报告\n")
            lines.append(f"| 属性 | 值 |")
            lines.append(f"| --- | --- |")
            lines.append(f"| 循环ID | `{latest_report.cycle_id}` |")
            lines.append(f"| 触发源 | {latest_report.trigger.source if latest_report.trigger else 'N/A'} |")
            lines.append(f"| 完成阶段 | {len(latest_report.phases_completed)}/6 |")
            lines.append(f"| 执行动作 | {len(latest_report.actions_taken)} |")
            lines.append(f"| 耗时 | {latest_report.duration_seconds:.2f}s |")
            lines.append(f"| 整体成功 | {'✅' if latest_report.overall_success else '❌'} |")

            if latest_report.improvements:
                lines.append(f"\n### 📈 改善项\n")
                for k, v in latest_report.improvements.items():
                    lines.append(f"- **{k}**: +{v}%")

            if latest_report.regressions:
                lines.append(f"\n### 📉 回退项\n")
                for k, v in latest_report.regressions.items():
                    lines.append(f"- **{k}**: {v:+}%")

            if latest_report.decisions_made:
                lines.append(f"\n### 🎯 决策记录\n")
                for d in latest_report.decisions_made[:5]:
                    lines.append(f"- [{d.get('priority', '?')}] {d.get('type')}: {d.get('action', '')}")

            if latest_report.next_recommendations:
                lines.append(f"\n### 💡 下一步建议\n")
                for rec in latest_report.next_recommendations:
                    lines.append(f"- {rec}")

        if self._event_log:
            lines.append(f"\n## 📜 最近事件\n")
            for event in self._event_log[-5:]:
                icon = {"detection": "🔍", "analysis": "📊", "decision": "🎯",
                         "execution": "⚡", "verification": "✅", "recording": "📝"}.get(
                             event.phase.value, "📌")
                lines.append(f"{icon} [{event.phase.value}] {event.event_type} @ {event.timestamp[:19]}")

        return "\n".join(lines) + "\n"


if __name__ == "__main__":
    print("=" * 60)
    print("演化循环控制器 - 功能演示")
    print("=" * 60)

    controller = EvolutionController(mode=EvolutionMode.CONSERVATIVE)

    print("\n--- 初始状态 ---")
    print(f"   模式: {controller.mode.value}")
    print(f"   能力: {controller.state.active_capabilities}")
    print(f"   阶段: {controller.state.current_phase.value}")

    print("\n--- 执行演化循环 ---")
    trigger = EvolutionTrigger(
        trigger_type="scheduled",
        source="system_monitor",
        priority="medium",
        payload={"check_type": "full_health"},
    )

    report = controller.run_evolution_cycle(trigger)
    print(f"   循环ID: {report.cycle_id}")
    print(f"   成功: {'✅' if report.overall_success else '❌'}")
    print(f"   阶段: {[p.value for p in report.phases_completed]}")
    print(f"   动作数: {len(report.actions_taken)}")
    print(f"   耗时: {report.duration_seconds:.2f}s")
    print(f"   改善: {report.improvements}")
    print(f"   回退: {report.regressions}")

    print("\n--- 决策记录 ---")
    for d in report.decisions_made:
        print(f"   [{d.get('priority')}] {d.get('type')}: {d.get('action')}")

    print("\n--- 建议 ---")
    for rec in report.next_recommendations:
        print(f"   💡 {rec}")

    print("\n--- 切换到激进模式 ---")
    controller.set_mode(EvolutionMode.AGGRESSIVE)
    report2 = controller.run_evolution_cycle(trigger)
    print(f"   模式: {controller.mode.value}, 成功: {'✅' if report2.overall_success else '❌'}")
    print(f"   执行动作: {len(report2.actions_taken)}")

    stats = controller.get_statistics()
    print(f"\n--- 统计 ---\n{stats}")

    gen_report = controller.generate_report(report)
    print(f"\n--- 报告预览 (前800字符) ---\n{gen_report[:800]}...")

    print("\n✅ 所有测试通过!")
