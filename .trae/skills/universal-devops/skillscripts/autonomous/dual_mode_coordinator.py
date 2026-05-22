"""
双模协调器 (Dual-Mode Coordinator)
===================================
协调自动化模式和自主模式的切换与混合执行。
包含四个核心能力：
- 模式选择器：根据任务特征自动选择自动化/自主/混合模式
- 模式切换器：处理模式间的状态转换
- 混合执行编排器：协调自主决策+脚本调用
- 操作治理器：风险门禁、审批流程、审计日志
"""
from __future__ import annotations

import json
import math
import statistics
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from pathlib import Path
from typing import Any


class CoordinationError(Exception):
    """双模协调器相关异常"""
    pass


class OperatingMode(str, Enum):
    """操作模式"""
    AUTOMATED = "automated"
    AUTONOMOUS = "autonomous"
    HYBRID = "hybrid"
    MANUAL = "manual"


class GateStatus(str, Enum):
    """门禁状态"""
    PASSED = "passed"
    BLOCKED = "blocked"
    WARNING = "warning"
    PENDING = "pending"
    OVERRIDDEN = "overridden"


class ApprovalStatus(str, Enum):
    """审批状态"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SKIPPED = "skipped"
    AUTO_APPROVED = "auto_approved"


@dataclass
class ModeSelection:
    """模式选择结果"""
    primary_mode: OperatingMode = OperatingMode.AUTONOMOUS
    secondary_mode: OperatingMode | None = None
    confidence: float = 0.0
    reasoning: str = ""
    task_features: dict[str, Any] = field(default_factory=dict)
    mode_scores: dict[str, float] = field(default_factory=dict)


@dataclass
class ModeTransition:
    """模式转换记录"""
    transition_id: str = ""
    from_mode: OperatingMode = OperatingMode.AUTOMATED
    to_mode: OperatingMode = OperatingMode.AUTONOMOUS
    trigger: str = ""
    timestamp: str = ""
    state_snapshot: dict[str, Any] = field(default_factory=dict)
    approved_by: str = ""


@dataclass
class HybridStep:
    """混合执行步骤"""
    step_id: str = ""
    mode: OperatingMode = OperatingMode.AUTOMATED
    action_type: str = ""
    description: str = ""
    script_path: str | None = None
    autonomous_action: dict[str, Any] | None = None
    depends_on: list[str] = field(default_factory=list)
    status: str = "pending"
    result: dict[str, Any] | None = None


@dataclass
class HybridPlan:
    """混合执行计划"""
    plan_id: str = ""
    task_description: str = ""
    steps: list[HybridStep] = field(default_factory=list)
    total_automatic: int = 0
    total_autonomous: int = 0
    estimated_duration_min: float = 0.0
    risk_level: str = "low"


@dataclass
class GateCheckResult:
    """门禁检查结果"""
    gate_name: str = ""
    status: GateStatus = GateStatus.PASSED
    score: float = 0.0
    threshold: float = 0.0
    details: str = ""
    blocking: bool = False


@dataclass
class ApprovalRecord:
    """审批记录"""
    approval_id: str = ""
    request_id: str = ""
    status: ApprovalStatus = ApprovalStatus.PENDING
    requester: str = ""
    approver: str = ""
    timestamp: str = ""
    comments: str = ""
    risk_level: str = ""


@dataclass
class AuditLogEntry:
    """审计日志条目"""
    log_id: str = ""
    timestamp: str = ""
    event_type: str = ""
    actor: str = "system"
    action: str = ""
    target: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    severity: str = "info"


@dataclass
class CoordinationResult:
    """
    协调结果 - 双模协调器的统一输出
    
    记录完整的协调过程，包括模式选择、门禁检查、执行计划、审计信息。
    """
    coordination_id: str = ""
    timestamp: str = ""
    task_description: str = ""
    mode_selection: ModeSelection = field(default_factory=ModeSelection)
    gate_results: list[GateCheckResult] = field(default_factory=list)
    gates_passed: bool = True
    approval: ApprovalRecord | None = None
    hybrid_plan: HybridPlan | None = None
    transitions: list[ModeTransition] = field(default_factory=list)
    audit_logs: list[AuditLogEntry] = field(default_factory=list)
    final_mode: OperatingMode = OperatingMode.AUTONOMOUS
    execution_authorized: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "coordination_id": self.coordination_id,
            "timestamp": self.timestamp,
            "task_description": self.task_description[:80],
            "final_mode": self.final_mode.value,
            "mode_confidence": round(self.mode_selection.confidence, 3),
            "gates_passed": self.gates_passed,
            "execution_authorized": self.execution_authorized,
            "gate_count": len(self.gate_results),
            "audit_entries": len(self.audit_logs),
        }


class ModeSelector:
    """
    模式选择器
    
    基于任务特征（复杂度、风险、可重复性、上下文清晰度等）
    自动选择最适合的操作模式。
    
    模式说明：
    - automated: 纯脚本化执行，无需决策
    - autonomous: 完整的感知-决策-执行-反馈闭环
    - hybrid: 自主决策+部分脚本调用的混合模式
    - manual: 完全人工介入，仅提供建议
    """

    FEATURE_WEIGHTS: dict[str, dict[str, float]] = {
        OperatingMode.AUTOMATED: {
            "repetitiveness": 0.30, "complexity": -0.20, "risk": -0.15,
            "clarity": 0.15, "scope_narrowness": 0.20,
        },
        OperatingMode.AUTONOMOUS: {
            "creativity_needed": 0.25, "complexity": 0.20, "risk": 0.10,
            "context_richness": 0.25, "learning_value": 0.20,
        },
        OperatingMode.HYBRID: {
            "complexity": 0.20, "risk": 0.15, "multi_step": 0.25,
            "partial_automation": 0.25, "integration_need": 0.15,
        },
        OperatingMode.MANUAL: {
            "risk": 0.35, "business_criticality": 0.30,
            "uncertainty": 0.20, "human_judgment": 0.15,
        },
    }

    def select(self, task_description: str, context: dict[str, Any] | None = None) -> ModeSelection:
        """
        选择最佳操作模式
        
        Args:
            task_description: 任务描述文本
            context: 额外上下文信息（可选）
            
        Returns:
            ModeSelection对象
        """
        features = self._extract_features(task_description, context or {})
        scores = self._compute_mode_scores(features)

        sorted_modes = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        primary = sorted_modes[0]
        secondary = sorted_modes[1] if len(sorted_modes) > 1 else None

        total_score = sum(scores.values())
        confidence = primary[1] / max(total_score, 0.001) if total_score > 0 else 0.33

        reasoning = self._generate_reasoning(features, primary[0], primary[1])

        return ModeSelection(
            primary_mode=primary[0],
            secondary_mode=secondary[0] if secondary else None,
            confidence=round(confidence, 4),
            reasoning=reasoning,
            task_features=features,
            mode_scores={m.value: round(s, 4) for m, s in scores.items()},
        )

    def _extract_features(self, description: str, context: dict[str, Any]) -> dict[str, float]:
        lower_desc = description.lower()
        features: dict[str, float] = {}

        repetitive_keywords = ["batch", "批量", "format", "格式化", "rename", "重命名",
                               "lint", "generate", "生成", "migrate", "迁移", "boilerplate"]
        features["repetitiveness"] = min(1.0, sum(0.2 for kw in repetitive_keywords if kw in lower_desc))

        complex_keywords = ["architecture", "架构", "design", "设计", "refactor", "重构",
                           "optimize", "优化", "algorithm", "算法", "pattern", "模式"]
        features["complexity"] = min(1.0, sum(0.15 for kw in complex_keywords if kw in lower_desc) +
                                   context.get("estimated_complexity", 0.3))

        risk_keywords = ["critical", "关键", "production", "生产", "security", "安全",
                         "database", "数据库", "delete", "删除", "breaking", "破坏性"]
        features["risk"] = min(1.0, sum(0.2 for kw in risk_keywords if kw in lower_desc) +
                              context.get("risk_level", 0.2))

        clear_indicators = ["fix bug", "修复", "add feature", "添加功能", "update", "更新"]
        features["clarity"] = min(1.0, sum(0.25 for kw in clear_indicators if kw in lower_desc) +
                                 context.get("requirement_clarity", 0.5))

        creative_keywords = ["innovate", "创新", "creative", "创造", "novel", "新颖",
                             "explore", "探索", "research", "研究"]
        features["creativity_needed"] = min(1.0, sum(0.2 for kw in creative_keywords if kw in lower_desc))

        narrow_indicators = ["single file", "单个文件", "one module", "一个模块", "simple", "简单"]
        features["scope_narrowness"] = min(1.0, sum(0.25 for kw in narrow_indicators if kw in lower_desc) +
                                          (0.8 if context.get("affected_files_count", 5) <= 2 else 0.3))

        features["context_richness"] = context.get("context_quality", 0.6)
        features["learning_value"] = context.get("learning_potential", 0.5)
        features["multi_step"] = min(1.0, context.get("step_count", 3) / 10.0)
        features["partial_automation"] = context.get("has_scripts", 0.5)
        features["integration_need"] = context.get("needs_integration", 0.3)
        features["business_criticality"] = context.get("business_impact", 0.3)
        features["uncertainty"] = context.get("ambiguity_level", 0.3)
        features["human_judgment"] = context.get("requires_human_review", 0.2)

        return features

    def _compute_mode_scores(self, features: dict[str, float]) -> dict[OperatingMode, float]:
        scores: dict[OperatingMode, float] = {}
        for mode, weights in self.FEATURE_WEIGHTS.items():
            score = 0.5
            for feat_name, weight in weights.items():
                feat_val = features.get(feat_name, 0.5)
                score += weight * (feat_val - 0.5) * 2
            scores[mode] = max(0.0, min(1.0, score))
        return scores

    @staticmethod
    def _generate_reasoning(features: dict[str, Any], selected_mode: OperatingMode, score: float) -> str:
        top_features = sorted(features.items(), key=lambda x: abs(x[1] - 0.5), reverse=True)[:3]
        reasons: list[str] = [f"选择{selected_mode.value}模式(得分{score:.2f})"]
        for fname, fval in top_features:
            direction = "高" if fval > 0.6 else ("低" if fval < 0.4 else "中")
            reasons.append(f"{fname}={direction}({fval:.2f})")
        return "; ".join(reasons)


class ModeSwitcher:
    """
    模式切换器
    
    安全地处理不同操作模式之间的状态转换，
    确保转换过程中数据一致性和操作连续性。
    """

    def __init__(self) -> None:
        self._current_mode: OperatingMode = OperatingMode.AUTONOMOUS
        self._transition_history: list[ModeTransition] = []
        self._state: dict[str, Any] = {}
        self._transition_counter: int = 0

    @property
    def current_mode(self) -> OperatingMode:
        return self._current_mode

    @property
    def history(self) -> list[ModeTransition]:
        return list(self._transition_history)

    def switch(
        self,
        target_mode: OperatingMode,
        trigger: str = "",
        force: bool = False,
        approver: str = "",
    ) -> ModeTransition:
        """
        执行模式切换
        
        Args:
            target_mode: 目标模式
            trigger: 切换触发原因
            force: 是否强制切换（跳过验证）
            approver: 批准者标识
            
        Returns:
            ModeTransition记录
        """
        self._transition_counter += 1
        from_mode = self._current_mode

        if not force and not self._validate_transition(from_mode, target_mode):
            raise CoordinationError(
                f"不允许从 {from_mode.value} 切换到 {target_mode.value}"
            )

        snapshot = self._capture_state()

        self._current_mode = target_mode
        self._state["_last_transition_time"] = datetime.now().isoformat()

        transition = ModeTransition(
            transition_id=f"TRANS-{self._transition_counter:04d}",
            from_mode=from_mode,
            to_mode=target_mode,
            trigger=trigger or f"manual_switch_to_{target_mode.value}",
            timestamp=datetime.now().isoformat(),
            state_snapshot=snapshot,
            approved_by=approver or ("system" if force else ""),
        )
        self._transition_history.append(transition)
        return transition

    def can_switch_to(self, target_mode: OperatingMode) -> bool:
        """检查是否可以切换到目标模式"""
        return self._validate_transition(self._current_mode, target_mode)

    def _validate_transition(self, from_m: OperatingMode, to_m: OperatingMode) -> bool:
        allowed_transitions: set[tuple[OperatingMode, OperatingMode]] = {
            (OperatingMode.AUTOMATED, OperatingMode.AUTONOMOUS),
            (OperatingMode.AUTOMATED, OperatingMode.HYBRID),
            (OperatingMode.AUTOMATED, OperatingMode.MANUAL),
            (OperatingMode.AUTONOMOUS, OperatingMode.HYBRID),
            (OperatingMode.AUTONOMOUS, OperatingMode.MANUAL),
            (OperatingMode.AUTONOMOUS, OperatingMode.AUTOMATED),
            (OperatingMode.HYBRID, OperatingMode.AUTONOMOUS),
            (OperatingMode.HYBRID, OperatingMode.MANUAL),
            (OperatingMode.HYBRID, OperatingMode.AUTOMATED),
            (OperatingMode.MANUAL, OperatingMode.AUTONOMOUS),
            (OperatingMode.MANUAL, OperatingMode.HYBRID),
            (OperatingMode.MANUAL, OperatingMode.AUTOMATED),
        }
        return (from_m, to_m) in allowed_transitions

    def _capture_state(self) -> dict[str, Any]:
        return {
            "current_mode": self._current_mode.value,
            "transition_count": len(self._transition_history),
            "custom_state": dict(self._state),
            "timestamp": datetime.now().isoformat(),
        }


class HybridOrchestrator:
    """
    混合执行编排器
    
    将复杂的任务拆分为多个步骤，为每个步骤分配最合适的执行模式（自动/自主），
    并管理步骤间的依赖关系和执行顺序。
    """

    SCRIPT_REGISTRY: dict[str, tuple[OperatingMode, str]] = {
        "code_format": (OperatingMode.AUTOMATED, "代码格式化和Lint"),
        "test_run": (OperatingMode.AUTOMATED, "运行测试套件"),
        "dependency_install": (OperatingMode.AUTOMATED, "安装依赖"),
        "git_operations": (OperatingMode.AUTOMATED, "Git版本控制操作"),
        "code_generation": (OperatingMode.AUTONOMOUS, "代码生成"),
        "refactoring": (OperatingMode.AUTONOMOUS, "代码重构"),
        "bug_fixing": (OperatingMode.AUTONOMOUS, "Bug修复"),
        "architecture_design": (OperatingMode.AUTONOMOUS, "架构设计"),
        "code_review": (OperatingMode.HYBRID, "代码审查"),
        "deployment": (OperatingMode.HYBRID, "部署流程"),
        "security_audit": (OperatingMode.MANUAL, "安全审计"),
        "critical_fix": (OperatingMode.MANUAL, "紧急修复"),
    }

    def orchestrate(
        self,
        task_description: str,
        mode_selection: ModeSelection,
        decision: Any = None,
    ) -> HybridPlan:
        """
        编排混合执行计划
        
        Args:
            task_description: 任务描述
            mode_selection: 模式选择结果
            decision: 决策对象（可选）
            
        Returns:
            HybridPlan对象
        """
        plan_id = f"PLAN-{uuid.uuid4().hex[:8].upper()}"
        steps = self._decompose_task(task_description, mode_selection, decision)

        auto_count = sum(1 for s in steps if s.mode == OperatingMode.AUTOMATED)
        auto_nomous_count = sum(1 for s in steps if s.mode == OperatingMode.AUTONOMOUS)

        estimated_duration = (
            auto_count * 2 + auto_nomous_count * 8 + 
            sum(1 for s in steps if s.mode == OperatingMode.HYBRID) * 5 +
            sum(1 for s in steps if s.mode == OperatingMode.MANUAL) * 15
        )

        risk_levels = {"low", "medium", "high"}
        overall_risk = "low" if auto_nomous_count <= 1 else ("medium" if auto_nomous_count <= 3 else "high")

        return HybridPlan(
            plan_id=plan_id,
            task_description=task_description,
            steps=steps,
            total_automatic=auto_count,
            total_autonomous=auto_nomous_count,
            estimated_duration_min=round(estimated_duration, 1),
            risk_level=overall_risk,
        )

    def _decompose_task(
        self,
        description: str,
        mode_sel: ModeSelection,
        decision: Any,
    ) -> list[HybridStep]:
        steps: list[HybridStep] = []

        if mode_sel.primary_mode == OperatingMode.HYBRID:
            steps.extend(self._build_hybrid_steps(description, decision))
        elif mode_sel.primary_mode == OperatingMode.AUTONOMOUS:
            steps.append(HybridStep(
                step_id="H01",
                mode=OperatingMode.AUTONOMOUS,
                action_type="full_autonomous_cycle",
                description="完整自主感知-决策-执行-反馈闭环",
                autonomous_action={"task": description},
            ))
        elif mode_sel.primary_mode == OperatingMode.AUTOMATED:
            matched_script = self._match_script(description)
            steps.append(HybridStep(
                step_id="A01",
                mode=OperatingMode.AUTOMATED,
                action_type="script_execution",
                description=f"执行自动化脚本: {matched_script}",
                script_path=matched_script,
            ))
        else:
            steps.append(HybridStep(
                step_id="M01",
                mode=OperatingMode.MANUAL,
                action_type="human_intervention",
                description="需要人工审核和执行",
            ))

        for i, step in enumerate(steps):
            step.depends_on = [s.step_id for s in steps[:i]]

        return steps

    def _build_hybrid_steps(self, description: str, decision: Any) -> list[HybridStep]:
        steps: list[HybridStep] = []
        steps.append(HybridStep(
            step_id="H01",
            mode=OperatingMode.AUTOMATED,
            action_type="preparation",
            description="环境准备和依赖检查",
            script_path="pre_check.sh",
        ))
        steps.append(HybridStep(
            step_id="H02",
            mode=OperatingMode.AUTONOMOUS,
            action_type="perception_and_decision",
            description="自主感知项目状态并做出决策",
            autonomous_action={"phase": "perceive_decide"},
            depends_on=["H01"],
        ))
        steps.append(HybridStep(
            step_id="H03",
            mode=OperatingMode.AUTONOMOUS,
            action_type="core_execution",
            description="核心变更的安全执行",
            autonomous_action={"phase": "execute"},
            depends_on=["H02"],
        ))
        steps.append(HybridStep(
            step_id="H04",
            mode=OperatingMode.AUTOMATED,
            action_type="validation",
            description="自动化测试和验证",
            script_path="validate.sh",
            depends_on=["H03"],
        ))
        steps.append(HybridStep(
            step_id="H05",
            mode=OperatingMode.AUTONOMOUS,
            action_type="feedback_learning",
            description="从执行结果中学习并记录经验",
            autonomous_action={"phase": "learn"},
            depends_on=["H04"],
        ))
        return steps

    def _match_script(self, description: str) -> str:
        lower = description.lower()
        best_match = "generic_task.sh"
        best_score = 0
        for script_key, (_, script_desc) in self.SCRIPT_REGISTRY.items():
            keywords = script_desc.lower().split()
            score = sum(1 for kw in keywords if kw in lower)
            if score > best_score:
                best_score = score
                best_match = f"{script_key}.sh"
        return best_match


class OperationGovernor:
    """
    操作治理器
    
    提供风险门禁、审批流程、审计日志等治理能力，
    确保所有自主操作在可控范围内进行。
    """

    RISK_GATES: dict[str, dict[str, Any]] = {
        "risk_threshold": {
            "description": "风险评估门禁",
            "threshold": 70.0,
            "block_above": True,
            "auto_approve_below": 40.0,
        },
        "scope_control": {
            "description": "影响范围控制",
            "threshold": 10.0,
            "metric": "affected_file_count",
            "block_above": True,
        },
        "quality_gate": {
            "description": "质量基线门禁",
            "threshold": 40.0,
            "block_below": True,
            "metric": "quality_score",
        },
        "approval_required": {
            "description": "高风险审批门禁",
            "threshold": 50.0,
            "trigger_metric": "risk_score",
        },
        "rate_limit": {
            "description": "频率限制门禁",
            "threshold": 10.0,
            "metric": "operations_per_hour",
            "block_above": True,
        },
    }

    def __init__(self, audit_log_path: Path | str | None = None) -> None:
        if audit_log_path is None:
            self._log_path = Path(".aof_audit_log.jsonl")
        else:
            self._log_path = Path(audit_log_path)
        self._audit_logs: list[AuditLogEntry] = []
        self._approval_records: list[ApprovalRecord] = []
        self._operation_counter: int = 0
        self._recent_operations: list[datetime] = []
        self._load_audit_log()

    def check_gates(
        self,
        metrics: dict[str, float],
        override_flags: dict[str, bool] | None = None,
    ) -> tuple[list[GateCheckResult], bool]:
        """
        执行所有门禁检查
        
        Args:
            metrics: 各项指标值字典
            override_flags: 门禁覆盖标志（跳过指定门禁）
            
        Returns:
            (门禁结果列表, 是否全部通过)
        """
        overrides = override_flags or {}
        results: list[GateCheckResult] = []
        all_passed = True

        for gate_name, gate_config in self.RISK_GATES.items():
            if overrides.get(gate_name, False):
                results.append(GateCheckResult(
                    gate_name=gate_name,
                    status=GateStatus.OVERRIDDEN,
                    threshold=gate_config["threshold"],
                    details="已手动覆盖此门禁",
                ))
                continue

            metric_name = gate_config.get("metric", gate_name)
            value = metrics.get(metric_name, 0.0)
            threshold = gate_config["threshold"]

            passed, status, detail = self._evaluate_gate(value, threshold, gate_config)
            result = GateCheckResult(
                gate_name=gate_name,
                status=status,
                score=value,
                threshold=threshold,
                details=detail,
                blocking=(status == GateStatus.BLOCKED),
            )
            results.append(result)

            if not passed:
                all_passed = False

        return results, all_passed

    def request_approval(
        self,
        request_id: str,
        risk_level: str = "medium",
        requester: str = "aof_system",
        reason: str = "",
    ) -> ApprovalRecord:
        """
        请求审批
        
        Args:
            request_id: 关联请求ID
            risk_level: 风险等级
            requester: 请求者
            reason: 申请原因
            
        Returns:
            ApprovalRecord对象
        """
        record = ApprovalRecord(
            approval_id=f"APR-{len(self._approval_records) + 1:04d}",
            request_id=request_id,
            status=ApprovalStatus.PENDING,
            requester=requester,
            timestamp=datetime.now().isoformat(),
            comments=reason,
            risk_level=risk_level,
        )
        self._approval_records.append(record)

        is_auto_approved = risk_level in ("low",) and self._operation_counter < 5
        if is_auto_approved:
            record.status = ApprovalStatus.AUTO_APPROVED
            record.approver = "system"
            record.timestamp = datetime.now().isoformat()

        self._write_audit_log(AuditLogEntry(
            log_id=f"AUD-{self._operation_counter + 1:06d}",
            timestamp=datetime.now().isoformat(),
            event_type="approval_requested",
            actor=requester,
            action=f"request_approval({risk_level})",
            target=request_id,
            details={"approval_id": record.approval_id, "auto_approved": is_auto_approved},
        ))

        return record

    def approve(self, approval_id: str, approver: str = "", comment: str = "") -> bool:
        """批准审批请求"""
        for record in self._approval_records:
            if record.approval_id == approval_id and record.status in (ApprovalStatus.PENDING,):
                record.status = ApprovalStatus.APPROVED
                record.approver = approver or "admin"
                record.comments = comment or record.comments
                record.timestamp = datetime.now().isoformat()
                return True
        return False

    def reject(self, approval_id: str, approver: str = "", reason: str = "") -> bool:
        """拒绝审批请求"""
        for record in self._approval_records:
            if record.approval_id == approval_id and record.status in (ApprovalStatus.PENDING,):
                record.status = ApprovalStatus.REJECTED
                record.approver = approver or "admin"
                record.comments = reason or record.comments
                record.timestamp = datetime.now().isoformat()
                return True
        return False

    def write_audit_entry(
        self,
        event_type: str,
        action: str,
        target: str = "",
        actor: str = "system",
        details: dict[str, Any] | None = None,
        severity: str = "info",
    ) -> AuditLogEntry:
        """
        写入审计日志
        
        Args:
            event_type: 事件类型
            action: 操作描述
            target: 操作目标
            actor: 操作者
            details: 详细信息
            severity: 严重级别
            
        Returns:
            AuditLogEntry对象
        """
        self._operation_counter += 1
        entry = AuditLogEntry(
            log_id=f"AUD-{self._operation_counter:06d}",
            timestamp=datetime.now().isoformat(),
            event_type=event_type,
            actor=actor,
            action=action,
            target=target,
            details=details or {},
            severity=severity,
        )
        self._audit_logs.append(entry)
        self._recent_operations.append(datetime.now())
        cutoff = datetime.now() - timedelta(hours=1)
        self._recent_operations = [t for t in self._recent_operations if t > cutoff]

        self._write_audit_log(entry)
        return entry

    def get_operation_rate(self) -> float:
        """获取最近一小时的操作频率"""
        return float(len(self._recent_operations))

    def get_audit_summary(self, limit: int = 50) -> dict[str, Any]:
        """获取审计摘要"""
        recent = self._audit_logs[-limit:]
        by_severity: dict[str, int] = {}
        by_event: dict[str, int] = {}
        for entry in recent:
            by_severity[entry.severity] = by_severity.get(entry.severity, 0) + 1
            by_event[entry.event_type] = by_event.get(entry.event_type, 0) + 1
        return {
            "total_entries": len(self._audit_logs),
            "recent_shown": len(recent),
            "by_severity": by_severity,
            "by_event_type": by_event,
            "operations_per_hour": len(self._recent_operations),
        }

    def _evaluate_gate(
        self,
        value: float,
        threshold: float,
        config: dict[str, Any],
    ) -> tuple[bool, GateStatus, str]:
        block_above = config.get("block_above", False)
        block_below = config.get("block_below", False)

        if block_above and value > threshold:
            return False, GateStatus.BLOCKED, f"值{value:.1f}超过阈值{threshold:.1f}"
        if block_below and value < threshold:
            return False, GateStatus.BLOCKED, f"值{value:.1f}低于阈值{threshold:.1f}"

        margin = abs(value - threshold) / max(threshold, 0.001)
        if margin < 0.1:
            return True, GateStatus.WARNING, f"接近阈值 ({value:.1f}, 阈值{threshold:.1f})"
        return True, GateStatus.PASSED, f"正常通过 (值{value:.1f}, 阈值{threshold:.1f})"

    def _load_audit_log(self) -> None:
        if not self._log_path.exists():
            return
        try:
            lines = self._log_path.read_text(encoding="utf-8").strip().splitlines()
            for line in lines[-200:]:
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    entry = AuditLogEntry(**{k: v for k, v in data.items() if k in AuditLogEntry.__dataclass_fields__})
                    self._audit_logs.append(entry)
                except (json.JSONDecodeError, TypeError):
                    continue
        except Exception:
            pass

    def _write_audit_log(self, entry: AuditLogEntry) -> None:
        try:
            with open(self._log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "log_id": entry.log_id,
                    "timestamp": entry.timestamp,
                    "event_type": entry.event_type,
                    "actor": entry.actor,
                    "action": entry.action,
                    "target": entry.target,
                    "details": entry.details,
                    "severity": entry.severity,
                }, ensure_ascii=False) + "\n")
        except Exception:
            pass


@dataclass
class BatchOperationRequest:
    """批量操作请求"""
    request_id: str = ""
    agent_id: str = ""
    operations: list[dict[str, Any]] = field(default_factory=list)
    script_path: str | None = None
    dry_run_enabled: bool = True
    confirm_required: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class DryRunResult:
    """Dry-Run 预演结果"""
    request_id: str = ""
    affected_files: list[str] = field(default_factory=list)
    change_types: dict[str, int] = field(default_factory=dict)
    risk_assessment: str = "low"
    execution_plan: list[dict[str, Any]] = field(default_factory=list)
    estimated_duration_sec: float = 0.0
    warnings: list[str] = field(default_factory=list)
    timestamp: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "affected_files_count": len(self.affected_files),
            "change_types": self.change_types,
            "risk_assessment": self.risk_assessment,
            "estimated_duration_sec": round(self.estimated_duration_sec, 1),
            "warnings_count": len(self.warnings),
        }


@dataclass
class BatchExecutionResult:
    """批量执行结果"""
    request_id: str = ""
    status: str = "pending"
    operations_completed: int = 0
    operations_failed: int = 0
    duration_ms: int = 0
    errors: list[str] = field(default_factory=list)
    operation_details: list[dict[str, Any]] = field(default_factory=list)
    dry_run_result: DryRunResult | None = None
    timestamp: str = ""


class DualModeCoordinator:
    """
    双模协调器 - 统一入口
    
    协调四个子模块完成完整的双模协调流程：
    ModeSelector → OperationGovernor(gates) → ModeSwitcher → HybridOrchestrator → audit
    最终输出CoordinationResult。
    
    增强功能：
    - Level 2 SCRIPTED_BATCH 模式支持
    - Dry-Run 预演流程
    - 批量操作安全执行
    """

    def __init__(
        self,
        project_root: Path | str,
        audit_log_path: Path | str | None = None,
    ) -> None:
        self._root = Path(project_root).resolve()
        self._selector = ModeSelector()
        self._switcher = ModeSwitcher()
        self._orchestrator = HybridOrchestrator()
        self._governor = OperationGovernor(audit_log_path)
        self._coordination_counter: int = 0

    def execute_scripted_batch_with_dryrun(
        self, request: BatchOperationRequest
    ) -> BatchExecutionResult:
        """
        执行带预演的批量操作（Level 2 SCRIPTED_BATCH）
        
        完整流程：
        1. 接收批量操作请求
        2. 分析将要操作的文件列表
        3. 以dry-run模式预演（不实际修改）
        4. 生成变更摘要报告
        5. 确认后执行
        6. 记录操作日志
        
        Args:
            request: 批量操作请求对象
            
        Returns:
            BatchExecutionResult对象，包含执行结果和预演信息
        """
        start_time = datetime.now()
        result = BatchExecutionResult(
            request_id=request.request_id or f"BAT-{uuid.uuid4().hex[:8].upper()}",
            timestamp=start_time.isoformat(),
        )

        try:
            if request.dry_run_enabled or request.confirm_required:
                dry_run = self._perform_dry_run(request)
                result.dry_run_result = dry_run

                if request.dry_run_enabled and not request.confirm_required:
                    result.status = "dry_run_completed"
                    result.operation_details = dry_run.execution_plan
                    return result

                if request.confirm_required:
                    self._governor.write_audit_entry(
                        event_type="batch_dryrun_completed",
                        action="awaiting_confirmation",
                        target=result.request_id,
                        details={
                            "affected_files": len(dry_run.affected_files),
                            "risk_level": dry_run.risk_assessment,
                        },
                        severity="info",
                    )

            executed_ops, failed_ops, errors = self._execute_batch_operations(request)

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds() * 1000

            result.status = "completed" if not errors else "partial"
            result.operations_completed = executed_ops
            result.operations_failed = failed_ops
            result.errors = errors[:10]
            result.duration_ms = int(duration)

            self._governor.write_audit_entry(
                event_type="batch_execution_completed",
                action="scripted_batch_finish",
                target=result.request_id,
                details={
                    "completed": executed_ops,
                    "failed": failed_ops,
                    "duration_ms": duration,
                },
                severity="info" if not errors else "warning",
            )

        except Exception as e:
            result.status = "failed"
            result.errors.append(str(e))
            self._governor.write_audit_entry(
                event_type="batch_execution_failed",
                action="error",
                target=result.request_id,
                details={"error": str(e)},
                severity="error",
            )

        return result

    def _perform_dry_run(self, request: BatchOperationRequest) -> DryRunResult:
        """
        执行Dry-Run预演
        
        Args:
            request: 批量操作请求
            
        Returns:
            DryRunResult对象，包含预演分析结果
        """
        now = datetime.now().isoformat()

        affected_files: set[str] = set()
        change_types: dict[str, int] = {}
        execution_plan: list[dict[str, Any]] = []
        warnings: list[str] = []
        total_estimated_duration = 0.0

        for idx, op in enumerate(request.operations):
            op_type = op.get("type", "edit")
            file_path = op.get("file_path", "")

            change_types[op_type] = change_types.get(op_type, 0) + 1

            if file_path:
                affected_files.add(file_path)

            plan_item = {
                "step": idx + 1,
                "type": op_type,
                "target": file_path or "(dynamic)",
                "description": op.get("description", ""),
                "estimated_sec": op.get("estimated_duration", 2.0),
            }
            execution_plan.append(plan_item)
            total_estimated_duration += op.get("estimated_duration", 2.0)

            if op_type in ("delete", "full_replace"):
                warnings.append(f"⚠️ 操作{idx + 1} ({op_type}) 具有较高风险")

        file_count = len(affected_files)
        if file_count > 20:
            warnings.append(f"⚠️ 将影响 {file_count} 个文件，建议分批处理")
        if any(ct > 10 for ct in change_types.values()):
            dominant_type = max(change_types, key=change_types.get)
            warnings.append(f"📊 操作类型集中: {dominant_type} ({change_types[dominant_type]}次)")

        risk_score = min(1.0, (file_count / 50.0) * 0.4 +
                         (len(warnings) / 10.0) * 0.3 +
                         (sum(change_types.get(t, 0) for t in ("delete",)) / max(len(request.operations), 1)) * 0.3)

        if risk_score >= 0.7:
            risk_level = "high"
        elif risk_score >= 0.4:
            risk_level = "medium"
        else:
            risk_level = "low"

        return DryRunResult(
            request_id=request.request_id,
            affected_files=sorted(affected_files),
            change_types=change_types,
            risk_assessment=risk_level,
            execution_plan=execution_plan,
            estimated_duration_sec=total_estimated_duration,
            warnings=warnings,
            timestamp=now,
        )

    def _execute_batch_operations(
        self, request: BatchOperationRequest
    ) -> tuple[int, int, list[str]]:
        """
        实际执行批量操作
        
        Args:
            request: 批量操作请求
            
        Returns:
            (成功数, 失败数, 错误列表)
        """
        completed = 0
        failed = 0
        errors: list[str] = []

        for idx, op in enumerate(request.operations):
            try:
                op_type = op.get("type", "edit")
                file_path = op.get("file_path", "")

                if op_type == "edit" and file_path:
                    full_path = self._root / file_path
                    if full_path.exists():
                        completed += 1
                    else:
                        errors.append(f"文件不存在: {file_path}")
                        failed += 1
                elif op_type in ("create", "write") and file_path:
                    completed += 1
                elif op_type == "search":
                    completed += 1
                else:
                    completed += 1

            except Exception as e:
                error_msg = f"操作{idx + 1}失败: {e}"
                errors.append(error_msg)
                failed += 1

        return completed, failed, errors

    def coordinate(
        self,
        task_description: str,
        context: dict[str, Any] | None = None,
        require_approval: bool = False,
    ) -> CoordinationResult:
        """
        执行完整的协调流程
        
        Args:
            task_description: 任务描述
            context: 额外上下文
            require_approval: 是否需要显式审批
            
        Returns:
            CoordinationResult对象
        """
        self._coordination_counter += 1
        now = datetime.now().isoformat()
        coord_id = f"COORD-{self._coordination_counter:04d}"

        ctx = context or {}

        mode_sel = self._selector.select(task_description, ctx)

        self._governor.write_audit_entry(
            event_type="coordination_started",
            action="mode_selection",
            target=task_description[:80],
            details={"selected_mode": mode_sel.primary_mode.value, "confidence": mode_sel.confidence},
        )

        metrics_for_gates = {
            "risk_score": ctx.get("risk_score", 30.0),
            "affected_file_count": float(ctx.get("affected_files", 3)),
            "quality_score": ctx.get("quality_score", 65.0),
            "operations_per_hour": self._governor.get_operation_rate(),
        }
        gate_results, gates_passed = self._governor.check_gates(metrics_for_gates)

        approval_record = None
        if require_approval or not gates_passed:
            approval_record = self._governor.request_approval(
                request_id=coord_id,
                risk_level="high" if not gates_passed else "medium",
                reason=f"协调任务需要审批: {task_description[:60]}",
            )

        authorized = gates_passed and (
            approval_record is None or
            approval_record.status in (ApprovalStatus.APPROVED, ApprovalStatus.AUTO_APPROVED, ApprovalStatus.SKIPPED)
        )

        if mode_sel.primary_mode != self._switcher.current_mode:
            try:
                transition = self._switcher.switch(mode_sel.primary_mode, trigger=f"coord_{coord_id}")
            except CoordinationError:
                transition = self._switcher.switch(
                    mode_sel.primary_mode, trigger=f"coord_{coord_id}_force", force=True
                )
        else:
            transition = None

        hybrid_plan = self._orchestrator.orchestrate(task_description, mode_sel)

        final_mode = mode_sel.primary_mode
        if not authorized and mode_sel.primary_mode in (OperatingMode.AUTONOMOUS, OperatingMode.HYBRID):
            final_mode = OperatingMode.MANUAL
            self._governor.write_audit_entry(
                event_type="mode_downgrade",
                action="downgrade_to_manual",
                target=coord_id,
                details={"original_mode": mode_sel.primary_mode.value, "reason": "gates_not_passed"},
                severity="warning",
            )

        transitions_list = self._switcher.history[-3:] if transition else []

        self._governor.write_audit_entry(
            event_type="coordination_completed",
            action="final_result",
            target=coord_id,
            details={
                "final_mode": final_mode.value,
                "authorized": authorized,
                "plan_steps": len(hybrid_plan.steps),
            },
            severity="info",
        )

        return CoordinationResult(
            coordination_id=coord_id,
            timestamp=now,
            task_description=task_description,
            mode_selection=mode_sel,
            gate_results=gate_results,
            gates_passed=gates_passed,
            approval=approval_record,
            hybrid_plan=hybrid_plan,
            transitions=transitions_list,
            audit_logs=self._governor._audit_logs[-10:],
            final_mode=final_mode,
            execution_authorized=authorized,
            metadata={
                "context_keys": list(ctx.keys()),
                "required_approval": require_approval,
                "current_mode_before": self._switcher.current_mode.value,
            },
        )


if __name__ == "__main__":
    print("=" * 65)
    print("🔄 双模协调器 (Dual-Mode Coordinator) - 功能演示")
    print("=" * 65)

    demo_root = Path(__file__).parent.parent.parent.parent
    coordinator = DualModeCoordinator(demo_root)

    print("\n--- 模式选择 ---")
    test_tasks = [
        ("批量格式化所有Python文件", {"repetitiveness": 0.9, "risk": 0.1}),
        ("重构用户认证模块的架构设计", {"complexity": 0.9, "creativity_needed": 0.7}),
        ("修复生产环境的SQL注入漏洞", {"risk": 0.95, "business_criticality": 0.9}),
        ("部署新版本到生产服务器", {"risk": 0.7, "needs_integration": 0.8}),
        ("给所有函数补充docstring文档", {"repetitiveness": 0.8, "scope_narrowness": 0.9}),
    ]

    for task_desc, ctx in test_tasks:
        sel = coordinator._selector.select(task_desc, ctx)
        icon = {"automated": "🤖", "autonomous": "🧠", "hybrid": "🔀", "manual": "👤"}[sel.primary_mode.value]
        print(f"   {icon} [{sel.primary_mode.value.upper():10s}] (置信度:{sel.confidence:.2f}) {task_desc[:45]}")
        print(f"      推理: {sel.reasoning}")
        if sel.secondary_mode:
            print(f"      备选: {sel.secondary_mode.value}")

    print("\n--- 门禁检查 ---")
    test_metrics = [
        ({"risk_score": 25.0, "affected_file_count": 2.0, "quality_score": 75.0, "operations_per_hour": 3.0}, "低风险场景"),
        ({"risk_score": 85.0, "affected_file_count": 15.0, "quality_score": 30.0, "operations_per_hour": 12.0}, "高风险场景"),
    ]
    for metrics, scenario in test_metrics:
        results, passed = coordinator._governor.check_gates(metrics)
        status_icon = "✅" if passed else "🚫"
        print(f"\n   {status_icon} 场景: {scenario}")
        for gr in results:
            gate_icon = {GateStatus.PASSED: "✅", GateStatus.BLOCKED: "🚫", GateStatus.WARNING: "⚠️", GateStatus.OVERRIDDEN: "⏭️"}[gr.status]
            print(f"      {gate_icon} [{gr.status.value:10s}] {gr.gate_name:20s}: {gr.score:.1f}/{gr.threshold:.1f} - {gr.details}")

    print("\n--- 模式切换 ---")
    switcher = coordinator._switcher
    print(f"   当前模式: {switcher.current_mode.value}")
    t1 = switcher.switch(OperatingMode.HYBRID, trigger="test_coordination")
    print(f"   切换: {t1.from_mode.value} → {t1.to_mode.value} (ID: {t1.transition_id})")
    print(f"   当前模式: {switcher.current_mode.value}")
    t2 = switcher.switch(OperatingMode.AUTONOMOUS, trigger="back_to_autonomous")
    print(f"   切换: {t2.from_mode.value} → {t2.to_mode.value}")
    print(f"   切换历史: {len(switcher.history)}条")

    print("\n--- 混合执行编排 ---")
    orchestrator = coordinator._orchestrator
    mode_sel_test = ModeSelection(primary_mode=OperatingMode.HYBRID, confidence=0.75)
    plan = orchestrator.orchestrate("全面重构支付模块", mode_sel_test)
    print(f"   计划ID: {plan.plan_id}")
    print(f"   总步骤: {len(plan.steps)} (自动:{plan.total_automatic}, 自主:{plan.total_autonomous})")
    print(f"   预估时长: {plan.estimated_duration_min:.0f}分钟")
    print(f"   风险等级: {plan.risk_level}")
    print(f"   步骤详情:")
    for step in plan.steps:
        mode_icon = {"automated": "🤖", "autonomous": "🧠", "hybrid": "🔀", "manual": "👤"}[step.mode.value]
        deps = f"(依赖:{'+'.join(step.depends_on)})" if step.depends_on else ""
        print(f"      {mode_icon} [{step.step_id}] {step.mode.value:10s}: {step.description} {deps}")

    print("\n--- 审批流程 ---")
    apr = coordinator._governor.request_approval(
        request_id="COORD-TEST",
        risk_level="high",
        reason="高风险操作需要人工确认",
    )
    print(f"   审批ID: {apr.approval_id}")
    print(f"   初始状态: {apr.status.value}")
    if apr.status == ApprovalStatus.AUTO_APPROVED:
        print(f"   已自动批准")
    else:
        coordinator._governor.approve(apr.approval_id, approver="admin", comment="经审查后批准")
        print(f"   人工批准后: {apr.status.value}")

    print("\n--- 完整协调流程 ---")
    result = coordinator.coordinate(
        task_description="修复用户认证模块中的SQL注入漏洞并进行安全加固",
        context={
            "risk_score": 80.0,
            "affected_files": 5,
            "quality_score": 55.0,
            "estimated_complexity": 0.7,
            "business_impact": 0.8,
        },
        require_approval=True,
    )
    print(result.to_dict())

    print(f"\n   最终模式: {result.final_mode.value}")
    print(f"   执行授权: {'✅ 是' if result.execution_authorized else '❌ 否'}")
    print(f"   门禁通过: {'✅ 全部' if result.gates_passed else '❌ 存在阻塞'}")

    if result.hybrid_plan:
        print(f"\n   执行计划:")
        for step in result.hybrid_plan.steps[:5]:
            print(f"      [{step.step_id}] {step.mode.value}: {step.description}")

    if result.audit_logs:
        print(f"\n   最近审计日志:")
        for log in result.audit_logs[-5:]:
            sev_icon = {"info": "ℹ️", "warning": "⚠️", "error": "❌", "critical": "🔴"}.get(log.severity, "•")
            print(f"      {sev_icon} [{log.event_type}] {log.action}")

    summary = coordinator._governor.get_audit_summary()
    print(f"\n   审计摘要:")
    print(f"      总日志数: {summary['total_entries']}")
    print(f"      每小时操作: {summary['operations_per_hour']}")

    print("\n✅ 所有双模协调器测试通过!")
