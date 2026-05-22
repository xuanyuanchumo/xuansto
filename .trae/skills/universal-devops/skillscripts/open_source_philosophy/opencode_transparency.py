"""
OpenCode Transparency Engine - 透明化决策引擎
理念来源：OpenCode项目的"透明化开发"和"开发者体验优先"核心理念

核心功能：
1. Decision Log自动生成系统 - AI决策自动记录为Markdown格式
2. 决策链路追溯系统 - 从最终决策回溯到初始需求的全链路追踪
3. DX评分系统 - 每次AI输出附带开发者体验评估
4. 渐进式复杂度管理 - 任务原子化分解与独立回滚
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from pathlib import Path
from typing import Any


class RiskLevel(Enum):
    """风险等级枚举"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ComplexityLevel(Enum):
    """复杂度等级枚举"""
    TRIVIAL = auto()
    SIMPLE = auto()
    MEDIUM = auto()
    COMPLEX = auto()
    CRITICAL = auto()


@dataclass
class Alternative:
    """备选方案"""
    name: str
    pros: list[str] = field(default_factory=list)
    cons: list[str] = field(default_factory=list)
    selected: bool = False

    def to_markdown(self) -> str:
        """转换为Markdown格式"""
        selected_marker = " ✅ 选择" if self.selected else ""
        lines = [f"{self.name} ({', '.join(f'+{p}' for p in self.pros)}, {', '.join(f'-{c}' for c in self.cons)}){selected_marker}"]
        return "\n      ".join(lines)


@dataclass
class RiskAssessment:
    """风险评估"""
    high_risks: list[str] = field(default_factory=list)
    medium_risks: list[str] = field(default_factory=list)
    low_risks: list[str] = field(default_factory=list)
    overall_risk_level: RiskLevel = RiskLevel.LOW

    def to_markdown(self) -> str:
        """转换为Markdown格式"""
        lines = []
        if self.high_risks:
            lines.extend([f"- 高风险: {risk}" for risk in self.high_risks])
        if self.medium_risks:
            lines.extend([f"- 中风险: {risk}" for risk in self.medium_risks])
        if self.low_risks:
            lines.extend([f"- 低风险: {risk}" for risk in self.low_risks])
        return "\n".join(lines) if lines else "- 无已知风险"


@dataclass
class DecisionRecord:
    """决策记录数据结构"""
    decision_id: str
    timestamp: datetime
    decision_maker: str
    decision_content: str
    rationale: list[str]
    alternatives: list[Alternative]
    risk_assessment: RiskAssessment
    impact_scope: list[str]
    parent_decision_id: str | None = None
    child_decision_ids: list[str] = field(default_factory=list)

    def to_markdown(self) -> str:
        """将决策记录转换为Markdown格式"""
        timestamp_str = self.timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        md_lines = [
            f"## 决策记录 #{self.decision_id}",
            f"- **时间**: {timestamp_str}",
            f"- **决策者**: {self.decision_maker}",
            f"- **决策内容**: {self.decision_content}",
            "- **决策依据**:",
        ]
        
        for rationale_item in self.rationale:
            md_lines.append(f"  - {rationale_item}")
        
        md_lines.append("- **备选方案**:")
        for i, alt in enumerate(self.alternatives, 1):
            md_lines.append(f"  {i}. {alt.to_markdown()}")
        
        md_lines.extend([
            "- **风险评估**:",
            f"  {self.risk_assessment.to_markdown()}",
            "- **影响范围**: " + ", ".join(self.impact_scope),
        ])
        
        if self.parent_decision_id:
            md_lines.append(f"- **父决策ID**: #{self.parent_decision_id}")
        
        if self.child_decision_ids:
            child_refs = ", ".join(f"#{cid}" for cid in self.child_decision_ids)
            md_lines.append(f"- **子决策ID**: {child_refs}")
        
        return "\n".join(md_lines)


@dataclass
class DXScore:
    """开发者体验评分"""
    clarity: int
    actionability: int
    completeness: int
    format_compliance: int
    context_relevance: int
    average: float = 0.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self):
        """计算加权平均分"""
        weights = {"clarity": 1.2, "actionability": 1.3, "completeness": 1.1,
                   "format_compliance": 0.8, "context_relevance": 1.1}
        total_weight = sum(weights.values())
        weighted_sum = (
            self.clarity * weights["clarity"] +
            self.actionability * weights["actionability"] +
            self.completeness * weights["completeness"] +
            self.format_compliance * weights["format_compliance"] +
            self.context_relevance * weights["context_relevance"]
        )
        self.average = round(weighted_sum / total_weight, 2)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式"""
        return {
            "clarity": self.clarity,
            "actionability": self.actionability,
            "completeness": self.completeness,
            "format_compliance": self.format_compliance,
            "context_relevance": self.context_relevance,
            "average": self.average,
            "timestamp": self.timestamp.isoformat(),
        }

    def to_visual_bar(self) -> str:
        """生成分数可视化条形图"""
        dimensions = [
            ("可理解性", self.clarity),
            ("可操作性", self.actionability),
            ("完整性", self.completeness),
            ("格式规范性", self.format_compliance),
            ("上下文相关性", self.context_relevance),
        ]
        bars = []
        for name, score in dimensions:
            filled = "█" * score + "░" * (5 - score)
            bars.append(f"  {name}: {filled} {score}/5")
        bars.append(f"  {'加权平均':chr(12288)}: {'█' * int(self.average)}{'░' * (5 - int(self.average))} {self.average}/5")
        return "\n".join(bars)


@dataclass
class AtomicStep:
    """原子步骤（用于渐进式复杂度管理）"""
    step_id: str
    description: str
    complexity: ComplexityLevel
    status: str = "pending"
    rollback_action: str | None = None
    dependencies: list[str] = field(default_factory=list)
    output_artifacts: list[str] = field(default_factory=list)

    def can_rollback(self) -> bool:
        """检查是否可以回滚"""
        return self.rollback_action is not None and self.status in ("completed", "failed")


class OpenCodeTransparency:
    """
    OpenCode透明化决策引擎主类
    
    提供以下核心能力：
    - 自动Decision Log生成与持久化
    - 决策链路追溯与可视化
    - DX评分计算与报告
    - 任务渐进式分解与管理
    """

    def __init__(self, project_root: Path | str | None = None):
        """
        初始化透明化决策引擎
        
        Args:
            project_root: 项目根目录路径，默认使用当前工作目录
        """
        if isinstance(project_root, str):
            project_root = Path(project_root)
        self.project_root = project_root or Path.cwd()
        
        self._decision_logs_dir = self.project_root / "docs" / "logs" / "decision_logs"
        self._dx_scores_dir = self.project_root / "reports" / "dx_scores"
        self._decision_chain_file = self.project_root / "docs" / "logs" / "decision_chain.json"
        
        self._decisions: dict[str, DecisionRecord] = {}
        self._decision_chain: dict[str, list[str]] = {}
        self._atomic_steps: dict[str, AtomicStep] = {}
        self._dx_scores: list[DXScore] = []

        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """确保必要的目录存在"""
        for directory in [self._decision_logs_dir, self._dx_scores_dir]:
            directory.mkdir(parents=True, exist_ok=True)

    def record_decision(
        self,
        decision_maker: str,
        decision_content: str,
        rationale: list[str],
        alternatives: list[Alternative],
        impact_scope: list[str],
        risk_assessment: RiskAssessment | None = None,
        parent_decision_id: str | None = None,
    ) -> DecisionRecord:
        """
        记录一条决策并生成Decision Log
        
        Args:
            decision_maker: 决策者标识（如：中书省-架构设计局）
            decision_content: 决策内容描述
            rationale: 决策依据列表
            alternatives: 备选方案列表
            impact_scope: 影响范围列表
            risk_assessment: 风险评估对象
            parent_decision_id: 父决策ID（用于构建决策链）
            
        Returns:
            创建的DecisionRecord对象
        """
        decision_id = self._generate_decision_id()
        timestamp = datetime.now(timezone.utc)
        
        if risk_assessment is None:
            risk_assessment = RiskAssessment()
        
        decision = DecisionRecord(
            decision_id=decision_id,
            timestamp=timestamp,
            decision_maker=decision_maker,
            decision_content=decision_content,
            rationale=rationale,
            alternatives=alternatives,
            risk_assessment=risk_assessment,
            impact_scope=impact_scope,
            parent_decision_id=parent_decision_id,
        )
        
        self._decisions[decision_id] = decision
        
        if parent_decision_id and parent_decision_id in self._decisions:
            self._decisions[parent_decision_id].child_decision_ids.append(decision_id)
        
        self._update_decision_chain(decision_id, parent_decision_id)
        self._write_decision_log(decision)
        
        return decision

    def _generate_decision_id(self) -> str:
        """生成唯一决策ID"""
        return f"D-{uuid.uuid4().hex[:8].upper()}"

    def _update_decision_chain(self, decision_id: str, parent_id: str | None) -> None:
        """更新决策链路数据"""
        if parent_id:
            if parent_id not in self._decision_chain:
                self._decision_chain[parent_id] = []
            self._decision_chain[parent_id].append(decision_id)
        self._persist_decision_chain()

    def _persist_decision_chain(self) -> None:
        """持久化决策链到JSON文件"""
        self._decision_chain_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self._decision_chain_file, "w", encoding="utf-8") as f:
            json.dump(self._decision_chain, f, ensure_ascii=False, indent=2)

    def _write_decision_log(self, decision: DecisionRecord) -> None:
        """将决策记录写入Markdown格式的Decision Log文件"""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        log_file = self._decision_logs_dir / f"{today}_decision_log.md"
        
        markdown_content = decision.to_markdown() + "\n\n---\n\n"
        
        existing_content = ""
        if log_file.exists():
            existing_content = log_file.read_text(encoding="utf-8")
        
        log_file.write_text(markdown_content + existing_content, encoding="utf-8")

    def trace_decision_chain(self, decision_id: str, max_depth: int = 10) -> list[DecisionRecord]:
        """
        追溯决策链路（从指定决策向上追溯到根决策）
        
        Args:
            decision_id: 起始决策ID
            max_depth: 最大追溯深度
            
        Returns:
            从根到叶的决策链列表
        """
        chain = []
        current_id = decision_id
        depth = 0
        
        while current_id and depth < max_depth:
            if current_id not in self._decisions:
                break
            chain.append(self._decisions[current_id])
            current_id = self._decisions[current_id].parent_decision_id
            depth += 1
        
        chain.reverse()
        return chain

    def get_child_decisions(self, decision_id: str) -> list[DecisionRecord]:
        """获取某个决策的所有子决策"""
        if decision_id not in self._decisions:
            return []
        return [self._decisions[cid] for cid in self._decisions[decision_id].child_decision_ids]

    def visualize_decision_tree(self, root_decision_id: str | None = None) -> str:
        """
        可视化决策树结构
        
        Args:
            root_decision_id: 根决策ID，None则找所有根决策
            
        Returns:
            决策树的文本表示
        """
        if root_decision_id:
            roots = [root_decision_id] if root_decision_id in self._decisions else []
        else:
            roots = [did for did, d in self._decisions.items() if d.parent_decision_id is None]
        
        lines = ["# 决策树可视化", ""]
        for root_id in roots:
            lines.append(self._render_tree_node(root_id, "", True))
        
        return "\n".join(lines)

    def _render_tree_node(self, decision_id: str, prefix: str, is_last: bool) -> str:
        """递归渲染决策树节点"""
        if decision_id not in self._decisions:
            return ""
        
        decision = self._decisions[decision_id]
        connector = "└── " if is_last else "├── "
        content_preview = decision.decision_content[:50] + "..." if len(decision.decision_content) > 50 else decision.decision_content
        line = f"{prefix}{connector}[{decision_id}] {content_preview}"
        
        children = decision.child_decision_ids
        if not children:
            return line
        
        extension = "    " if is_last else "│   "
        child_lines = [line]
        for i, child_id in enumerate(children):
            is_last_child = i == len(children) - 1
            child_lines.append(self._render_tree_node(child_id, prefix + extension, is_last_child))
        
        return "\n".join(child_lines)

    def analyze_decision_impact(self, decision_id: str) -> dict[str, Any]:
        """
        分析决策的影响范围
        
        Args:
            decision_id: 要分析的决策ID
            
        Returns:
            包含影响分析结果的字典
        """
        if decision_id not in self._decisions:
            return {"error": "Decision not found"}
        
        decision = self._decisions[decision_id]
        affected_decisions = self._collect_affected_decisions(decision_id)
        
        return {
            "decision_id": decision_id,
            "direct_impact": decision.impact_scope,
            "affected_decisions": len(affected_decisions),
            "affected_decision_ids": affected_decisions,
            "risk_level": decision.risk_assessment.overall_risk_level.value,
            "has_children": len(decision.child_decision_ids) > 0,
        }

    def _collect_affected_decisions(self, decision_id: str) -> list[str]:
        """收集受影响的所有下游决策ID"""
        affected = []
        queue = [decision_id]
        
        while queue:
            current = queue.pop(0)
            if current in self._decisions:
                for child_id in self._decisions[current].child_decision_ids:
                    if child_id not in affected:
                        affected.append(child_id)
                        queue.append(child_id)
        
        return affected

    def evaluate_dx(
        self,
        clarity: int,
        actionability: int,
        completeness: int,
        format_compliance: int,
        context_relevance: int,
    ) -> DXScore:
        """
        评估并记录DX评分
        
        Args:
            clarity: 可理解性评分(1-5)
            actionability: 可操作性评分(1-5)
            completeness: 完整性评分(1-5)
            format_compliance: 格式规范性评分(1-5)
            context_relevance: 上下文相关性评分(1-5)
            
        Returns:
            DXScore对象
        """
        dx_score = DXScore(
            clarity=clarity,
            actionability=actionability,
            completeness=completeness,
            format_compliance=format_compliance,
            context_relevance=context_relevance,
        )
        
        self._dx_scores.append(dx_score)
        self._persist_dx_score(dx_score)
        
        return dx_score

    def _persist_dx_score(self, dx_score: DXScore) -> None:
        """持久化DX评分到JSON文件"""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        score_file = self._dx_scores_dir / f"{today}_dx_scores.json"
        
        scores_data = []
        if score_file.exists():
            scores_data = json.loads(score_file.read_text(encoding="utf-8"))
        
        scores_data.append(dx_score.to_dict())
        
        score_file.write_text(json.dumps(scores_data, ensure_ascii=False, indent=2), encoding="utf-8")

    def get_dx_summary(self) -> dict[str, Any]:
        """获取DX评分汇总统计"""
        if not self._dx_scores:
            return {"total_evaluations": 0, "message": "No DX scores recorded yet"}
        
        averages = {
            "clarity": sum(s.clarity for s in self._dx_scores) / len(self._dx_scores),
            "actionability": sum(s.actionability for s in self._dx_scores) / len(self._dx_scores),
            "completeness": sum(s.completeness for s in self._dx_scores) / len(self._dx_scores),
            "format_compliance": sum(s.format_compliance for s in self._dx_scores) / len(self._dx_scores),
            "context_relevance": sum(s.context_relevance for s in self._dx_scores) / len(self._dx_scores),
            "overall_average": sum(s.average for s in self._dx_scores) / len(self._dx_scores),
        }
        
        return {
            "total_evaluations": len(self._dx_scores),
            "averages": {k: round(v, 2) for k, v in averages.items()},
            "latest_score": self._dx_scores[-1].to_dict(),
        }

    def decompose_task(
        self,
        task_description: str,
        complexity: ComplexityLevel = ComplexityLevel.MEDIUM,
    ) -> list[AtomicStep]:
        """
        将任务分解为原子步骤
        
        Args:
            task_description: 任务描述
            complexity: 整体复杂度等级
            
        Returns:
            原子步骤列表
        """
        steps = self._generate_atomic_steps(task_description, complexity)
        
        for step in steps:
            self._atomic_steps[step.step_id] = step
        
        return steps

    def _generate_atomic_steps(self, task_description: str, complexity: ComplexityLevel) -> list[AtomicStep]:
        """根据任务描述和复杂度生成原子步骤"""
        base_id = f"S-{uuid.uuid4().hex[:6]}"
        
        step_templates = {
            ComplexityLevel.TRIVIAL: [
                ("分析需求", ComplexityLevel.TRIVIAL),
                ("执行操作", ComplexityLevel.TRIVIAL),
            ],
            ComplexityLevel.SIMPLE: [
                ("分析需求并明确目标", ComplexityLevel.SIMPLE),
                ("设计实现方案", ComplexityLevel.TRIVIAL),
                ("编写代码实现", ComplexityLevel.SIMPLE),
                ("验证结果正确性", ComplexityLevel.TRIVIAL),
            ],
            ComplexityLevel.MEDIUM: [
                ("深入分析需求和约束条件", ComplexityLevel.MEDIUM),
                ("设计技术方案和架构", ComplexityLevel.SIMPLE),
                ("拆分子任务和依赖关系", ComplexityLevel.TRIVIAL),
                ("逐步实现各子模块", ComplexityLevel.MEDIUM),
                ("编写单元测试用例", ComplexityLevel.SIMPLE),
                ("集成测试和验证", ComplexityLevel.MEDIUM),
                ("代码审查和优化", ComplexityLevel.SIMPLE),
            ],
            ComplexityLevel.COMPLEX: [
                ("全面需求分析和利益相关者调研", ComplexityLevel.COMPLEX),
                ("多方案技术评审和选型", ComplexityLevel.MEDIUM),
                ("详细架构设计和文档编写", ComplexityLevel.MEDIUM),
                ("模块接口定义和契约设计", ComplexityLevel.SIMPLE),
                ("核心模块并行开发", ComplexityLevel.COMPLEX),
                ("集成测试策略制定和执行", ComplexityLevel.MEDIUM),
                ("性能测试和安全审计", ComplexityLevel.MEDIUM),
                ("灰度发布和监控配置", ComplexityLevel.SIMPLE),
                ("生产环境验证和问题修复", ComplexityLevel.MEDIUM),
            ],
            ComplexityLevel.CRITICAL: [
                ("项目立项和可行性研究", ComplexityLevel.CRITICAL),
                ("技术栈选型和POC验证", ComplexityLevel.COMPLEX),
                ("系统架构设计和评审", ComplexityLevel.COMPLEX),
                ("安全架构和合规性设计", ComplexityLevel.HIGH),
                ("基础设施规划和部署", ComplexityLevel.MEDIUM),
                ("核心功能开发和单元测试", ComplexityLevel.COMPLEX),
                ("端到端集成测试", ComplexityLevel.HIGH),
                ("性能压测和容量规划", ComplexityLevel.HIGH),
                ("安全渗透测试", ComplexityLevel.MEDIUM),
                ("用户验收测试(UAT)", ComplexityLevel.MEDIUM),
                ("生产环境部署和监控", ComplexityLevel.HIGH),
                ("应急响应预案制定", ComplexityLevel.MEDIUM),
            ],
        }
        
        templates = step_templates.get(complexity, step_templates[ComplexityLevel.MEDIUM])
        steps = []
        
        for i, (desc, step_complexity) in enumerate(templates, 1):
            step = AtomicStep(
                step_id=f"{base_id}-{i:02d}",
                description=f"[{task_description}] {desc}",
                complexity=step_complexity,
                rollback_action=self._generate_rollback_action(desc),
                dependencies=[f"{base_id}-{i-1:02d}"] if i > 1 else [],
            )
            steps.append(step)
        
        return steps

    def _generate_rollback_action(self, step_description: str) -> str:
        """根据步骤描述生成回滚动作"""
        rollback_map = {
            "分析": "无需回滚",
            "设计": "恢复上一版本设计文档",
            "开发": "回退代码到上一个提交点",
            "测试": "清理测试数据和临时文件",
            "部署": "回滚到上一个稳定版本",
            "审查": "撤销审查意见",
        }
        
        for keyword, action in rollback_map.items():
            if keyword in step_description:
                return action
        
        return "手动检查并恢复"

    def rollback_step(self, step_id: str) -> bool:
        """
        回滚指定的原子步骤
        
        Args:
            step_id: 要回滚的步骤ID
            
        Returns:
            回滚是否成功
        """
        if step_id not in self._atomic_steps:
            return False
        
        step = self._atomic_steps[step_id]
        if not step.can_rollback():
            return False
        
        step.status = "rolled_back"
        return True

    def get_task_status(self, task_base_id: str) -> dict[str, Any]:
        """获取基于base ID的所有步骤状态"""
        related_steps = {
            sid: s for sid, s in self._atomic_steps.items()
            if sid.startswith(task_base_id)
        }
        
        if not related_steps:
            return {"error": "No steps found for this task"}
        
        status_counts = {}
        for step in related_steps.values():
            status_counts[step.status] = status_counts.get(step.status, 0) + 1
        
        return {
            "task_id": task_base_id,
            "total_steps": len(related_steps),
            "status_breakdown": status_counts,
            "steps": [
                {
                    "id": s.step_id,
                    "description": s.description,
                    "complexity": s.complexity.name,
                    "status": s.status,
                }
                for s in sorted(related_steps.values(), key=lambda x: x.step_id)
            ],
        }

    def generate_report(self) -> str:
        """生成综合报告（包含决策日志、DX评分、任务状态）"""
        report_sections = [
            "# OpenCode Transparency Report",
            f"\n*Generated at: {datetime.now(timezone.utc).isoformat()}*\n",
            "## Decision Summary",
            f"Total Decisions Recorded: {len(self._decisions)}\n",
            "## DX Score Summary",
        ]
        
        dx_summary = self.get_dx_summary()
        if dx_summary.get("total_evaluations", 0) > 0:
            report_sections.append(f"Total Evaluations: {dx_summary['total_evaluations']}")
            report_sections.append(f"Overall Average: {dx_summary['averages']['overall_average']}/5.0\n")
        else:
            report_sections.append("No DX scores recorded yet.\n")
        
        report_sections.extend([
            "## Active Tasks",
            f"Total Atomic Steps: {len(self._atomic_steps)}\n",
        ])
        
        if self._decisions:
            report_sections.extend([
                "---\n",
                "## Recent Decisions",
            ])
            recent_decisions = sorted(
                self._decisions.values(), key=lambda d: d.timestamp, reverse=True
            )[:5]
            for decision in recent_decisions:
                report_sections.append(decision.to_markdown() + "\n")
        
        return "\n".join(report_sections)
