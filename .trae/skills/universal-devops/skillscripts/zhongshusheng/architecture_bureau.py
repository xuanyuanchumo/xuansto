"""
架构设计局 - 中书省第二局

负责技术选型决策、系统架构图生成(C4模型)、设计模式推荐、模块划分(DDD/分层/六边形/洋葱)、
依赖关系分析、API边界定义、架构决策记录(ADR)及非功能性需求定义。
"""
from __future__ import annotations

import json
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any


class ArchitectureError(Exception):
    """架构设计局相关异常"""
    pass


class ProblemType(str, Enum):
    """问题类型枚举（用于设计模式推荐）"""
    OBJECT_CREATION = "object_creation"
    STRUCTURE_COMPOSITION = "structure_composition"
    BEHAVIOR_ALLOCATION = "behavior_allocation"
    ALGORITHM_ENCAPSULATION = "algorithm_encapsulation"
    STATE_MANAGEMENT = "state_management"
    CONCURRENCY_CONTROL = "concurrency_control"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    DATA_ACCESS = "data_access"
    EVENT_HANDLING = "event_handling"
    DISTRIBUTED_SYSTEM = "distributed_system"
    ENTERPRISE_INTEGRATION = "enterprise_integration"


class ArchitectureStyle(str, Enum):
    """架构风格枚举"""
    LAYERED = "layered"
    HEXAGONAL = "hexagonal"  # 六边形/端口适配器
    ONION = "onion"          # 洋葱架构
    DDD = "ddd"              # 领域驱动设计
    EVENT_DRIVEN = "event_driven"
    MICROSERVICES = "microservices"
    SERVERLESS = "serverless"


class ADRStatus(str, Enum):
    """ADR状态枚举"""
    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    DEPRECATED = "deprecated"
    SUPERSEDED = "superseded"


@dataclass
class TechOption:
    """技术选项数据类"""
    name: str
    category: str
    description: str = ""
    scores: dict[str, float] = field(default_factory=dict)
    pros: list[str] = field(default_factory=list)
    cons: list[str] = field(default_factory=list)
    maturity: str = "stable"
    community: str = "active"
    license: str = ""
    learning_curve: str = "medium"

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "scores": self.scores,
            "pros": self.pros,
            "cons": self.cons,
            "maturity": self.maturity,
            "community": self.community,
        }


@dataclass
class TechDecision:
    """技术选型决策结果"""
    selected_option: TechOption
    runner_up: TechOption | None = None
    criteria_used: dict[str, float] = field(default_factory=dict)
    weighted_scores: dict[str, float] = field(default_factory=dict)
    rationale: str = ""
    confidence: float = 0.8
    decided_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_markdown(self) -> str:
        lines = [
            "# 技术选型决策",
            f"\n**选定方案**: **{self.selected_option.name}** ({self.selected_option.category})",
            f"**置信度**: {self.confidence:.0%}",
            f"**决策时间**: {self.decided_at}\n",
            "## 评分详情\n",
            "| 维度 | 权重 | 得分 | 加权分 |",
            "|------|------|------|--------|",
        ]
        for criterion, weight in self.criteria_used.items():
            raw_score = self.selected_option.scores.get(criterion, 0)
            weighted = raw_score * weight
            lines.append(f"| {criterion} | {weight} | {raw_score} | {weighted:.2f} |")

        if self.runner_up:
            lines.append(f"\n## 备选方案: {self.runner_up.name}")
        if self.rationale:
            lines.append(f"\n## 决策依据\n{self.rationale}")

        return "\n".join(lines)


@dataclass
class PatternRecommendation:
    """设计模式推荐结果"""
    pattern_name: str
    category: str           # GOF / Enterprise / Concurrency / DDD
    problem_description: str
    solution_summary: str
    applicability: float     # 0.0-1.0
    complexity: str = "medium"
    code_example: str = ""
    related_patterns: list[str] = field(default_factory=list)
    trade_offs: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "pattern_name": self.pattern_name,
            "category": self.category,
            "problem": self.problem_description,
            "solution": self.solution_summary,
            "applicability": round(self.applicability, 2),
            "complexity": self.complexity,
            "related_patterns": self.related_patterns,
        }


@dataclass
class ModuleInfo:
    """模块信息"""
    name: str
    layer: str = ""
    responsibility: str = ""
    dependencies: list[str] = field(default_factory=list)
    classes: list[str] = field(default_factory=list)
    interfaces: list[str] = field(default_factory=list)
    path: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "layer": self.layer,
            "responsibility": self.responsibility,
            "dependencies": self.dependencies,
            "classes_count": len(self.classes),
            "interfaces_count": len(self.interfaces),
        }


@dataclass
class LayerDefinition:
    """层定义"""
    name: str
    modules: list[ModuleInfo] = field(default_factory=list)
    description: str = ""
    access_direction: str = ""  # upward/downward/inward

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "modules": [m.to_dict() for m in self.modules],
            "description": self.description,
        }


@dataclass
class ModuleStructure:
    """模块结构"""
    architecture_style: ArchitectureStyle
    layers: list[LayerDefinition] = field(default_factory=list)
    cross_cutting_concerns: list[str] = field(default_factory=list)
    package_mapping: dict[str, str] = field(default_factory=dict)

    def to_mermaid(self) -> str:
        lines = ["graph TB"]
        layer_colors = [
            ("#e3f2fd", "presentation"),
            ("#fff3e0", "application"),
            ("#e8f5e9", "domain"),
            ("#fce4ec", "infrastructure"),
        ]
        module_nodes: dict[str, str] = {}

        for idx, layer in enumerate(self.layers):
            color = layer_colors[idx % len(layer_colors)][0]
            lines.append(f'    subgraph L{idx}["{layer.name}"]')
            for mod in layer.modules:
                node_id = f"{layer.name}_{mod.name}".replace(" ", "_")
                module_nodes[mod.name] = node_id
                lines.append(f'        {node_id}["{mod.name}"]')
            lines.append(f"    end")
            lines.append(f'    classDef layer{idx} fill:{color},stroke:#333')

        for layer in self.layers:
            for mod in layer.modules:
                src_node = module_nodes.get(mod.name, "")
                for dep in mod.dependencies:
                    dep_node = module_nodes.get(dep, "")
                    if dep_node and dep_node != src_node:
                        lines.append(f"    {src_node} --> {dep_node}")

        classes_str = " ".join([f"layer{i}" for i in range(len(self.layers))])
        all_nodes = ",".join(module_nodes.values())
        if all_nodes:
            lines.append(f"    class {all_nodes} {classes_str}")

        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return {
            "architecture_style": self.architecture_style.value,
            "layers": [l.to_dict() for l in self.layers],
            "cross_cutting_concerns": self.cross_cutting_concerns,
            "package_mapping": self.package_mapping,
        }


@dataclass
class DependencyEdge:
    """依赖边"""
    from_module: str
    to_module: str
    dependency_type: str = "uses"  # uses / imports / implements / extends
    strength: str = "strong"       # strong / weak / optional

    def to_tuple(self) -> tuple[str, str, str]:
        return (self.from_module, self.to_module, self.dependency_type)


@dataclass
class DependencyGraph:
    """依赖关系图"""
    nodes: list[str] = field(default_factory=list)
    edges: list[DependencyEdge] = field(default_factory=list)
    circular_dependencies: list[list[str]] = field(default_factory=list)
    depth_map: dict[str, int] = field(default_factory=dict)
    fan_in: dict[str, int] = field(default_factory=dict)
    fan_out: dict[str, int] = field(default_factory=dict)

    def has_circular_deps(self) -> bool:
        return len(self.circular_dependencies) > 0

    def to_mermaid(self) -> str:
        lines = ["graph LR"]
        for edge in self.edges:
            style = "-->" if edge.strength == "strong" else "-.->"
            label = f" / '{edge.dependency_type}'" if edge.dependency_type != "uses" else ""
            lines.append(f"    {edge.from_module}{style}{edge.to_module}{label}")

        if self.circular_dependencies:
            lines.append("\n    %% 循环依赖警告")
            for cycle in self.circular_dependencies:
                cycle_str = " → ".join(cycle)
                lines.append(f"    %% ⚠️ 循环: {cycle_str}")

        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": self.nodes,
            "edges": [e.to_tuple() for e in self.edges],
            "circular_dependencies": self.circular_dependencies,
            "has_circular_deps": self.has_circular_deps(),
            "depth_map": self.depth_map,
            "fan_in": self.fan_in,
            "fan_out": self.fan_out,
        }


@dataclass
class APIEndpoint:
    """API端点定义"""
    method: str
    path: str
    description: str = ""
    request_schema: dict[str, Any] = field(default_factory=dict)
    response_schema: dict[str, Any] = field(default_factory=dict)
    auth_required: bool = True
    rate_limit: str = ""
    version: str = "v1"

    def to_openapi_fragment(self) -> dict[str, Any]:
        return {
            self.method.lower(): {
                "summary": self.description,
                "parameters": [],
                "requestBody": self.request_schema if self.request_schema else None,
                "responses": {"200": {"description": "成功", "content": {"application/json": {"schema": self.response_schema or {}}}}},
                "security": [{"bearerAuth": []}] if self.auth_required else [],
            }
        }


@dataclass
class APIContract:
    """API契约"""
    base_url: str = "/api"
    version: str = "1.0.0"
    endpoints: list[APIEndpoint] = field(default_factory=list)
    shared_models: dict[str, dict] = field(default_factory=dict)
    authentication: dict[str, str] = field(default_factory=dict)
    rate_limiting: dict[str, str] = field(default_factory=dict)

    def to_openapi3(self) -> str:
        paths: dict[str, Any] = {}
        for ep in self.endpoints:
            full_path = f"{self.base_url}{ep.path}" if not ep.path.startswith("/") else ep.path
            paths.setdefault(full_path, {}).update(ep.to_openapi_fragment())

        spec = {
            "openapi": "3.0.3",
            "info": {"title": "API Contract", "version": self.version},
            "servers": [{"url": self.base_url}],
            "paths": paths,
            "components": {
                "securitySchemes": {
                    "bearerAuth": {"type": "http", "scheme": "bearer"},
                },
                "schemas": self.shared_models,
            },
        }

        return json.dumps(spec, ensure_ascii=False, indent=2)

    def to_markdown(self) -> str:
        lines = ["# API 接口契约", f"\n**Base URL**: `{self.base_url}`\n", "| Method | Path | Description | Auth |", "|--------|------|-------------|------|"]
        for ep in self.endpoints:
            lines.append(f"| {ep.method.upper()} | `{ep.path}` | {ep.description} | {'✅' if ep.auth_required else '❌'} |")
        return "\n".join(lines)


@dataclass
class ADR:
    """架构决策记录 (Architecture Decision Record)"""
    id: int
    title: str
    status: ADRStatus = ADRStatus.ACCEPTED
    context: str = ""
    decision: str = ""
    consequences: str = ""
    alternatives: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    authors: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)

    def to_markdown(self) -> str:
        lines = [
            f"# ADR-{self.id:04d}: {self.title}",
            "",
            f"- **状态**: {self.status.value}",
            f"- **日期**: {self.created_at[:10]}",
            *(f"- **作者**: {a}" for a in self.authors),
            *(f"- **标签**: {t}" for t in self.tags),
            "",
            "## Context (上下文)",
            self.context,
            "",
            "## Decision (决策)",
            self.decision,
            "",
            "## Consequences (后果)",
            self.consequences,
        ]
        if self.alternatives:
            lines.extend(["", "## Alternatives (备选方案)", *[f"- {alt}" for alt in self.alternatives]])
        return "\n".join(lines)


@dataclass
class NFRItem:
    """非功能需求条目"""
    category: str
    metric: str
    target_value: str
    current_value: str | None = None
    priority: str = "high"
    measurement_method: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "metric": self.metric,
            "target": self.target_value,
            "priority": self.priority,
        }


@dataclass
class NFRSpec:
    """非功能性需求规格说明"""
    scalability: list[NFRItem] = field(default_factory=list)
    reliability: list[NFRItem] = field(default_factory=list)
    security: list[NFRItem] = field(default_factory=list)
    performance: list[NFRItem] = field(default_factory=list)
    maintainability: list[NFRItem] = field(default_factory=list)
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_markdown(self) -> str:
        sections = {
            "可扩展性 (Scalability)": self.scalability,
            "可靠性 (Reliability)": self.reliability,
            "安全性 (Security)": self.security,
            "性能 (Performance)": self.performance,
            "可维护性 (Maintainability)": self.maintainability,
        }
        lines = ["# 非功能性需求规格 (NFR)", f"\n**生成时间**: {self.generated_at[:10]}\n"]
        for section_title, items in sections.items():
            if not items:
                continue
            lines.append(f"## {section_title}\n")
            lines.append("| 指标 | 目标值 | 优先级 | 测量方式 |")
            lines.append("|------|--------|--------|----------|")
            for item in items:
                lines.append(f"| {item.metric} | {item.target_value} | {item.priority} | {item.measurement_method or '-'} |")
            lines.append("")
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return {
            "scalability": [i.to_dict() for i in self.scalability],
            "reliability": [i.to_dict() for i in self.reliability],
            "security": [i.to_dict() for i in self.security],
            "performance": [i.to_dict() for i in self.performance],
            "maintainability": [i.to_dict() for i in self.maintainability],
        }


@dataclass
class ComponentInfo:
    """组件信息（用于架构图）"""
    name: str
    type: str = "component"      # system / container / component
    technology: str = ""
    description: str = ""
    connections: list[tuple[str, str]] = field(default_factory=list)  # (target, label)


class ArchitectureBureau:
    """
    架构设计局

    负责技术选型决策(加权评分)、C4架构图生成、设计模式推荐(GOF/企业/并发)、
    模块划分(DDD/分层/六边形/洋葱)、依赖分析与循环检测、API边界定义、
    架构决策记录(ADR)及非功能性需求(NFR)定义。
    """

    _adr_counter: int = 0

    def __init__(self, output_dir: Path | str | None = None) -> None:
        self._output_dir = Path(output_dir) if output_dir else Path.cwd()
        self._adrs: list[ADR] = []
        self._tech_decisions: list[TechDecision] = []

    def tech_selection(
        self, criteria: dict[str, float], options: list[TechOption]
    ) -> TechDecision:
        """
        基于加权评分的多维度技术选型

        Args:
            criteria: 评估维度及其权重，如 {"性能": 0.3, "生态": 0.25, "学习成本": 0.2, ...}
            options: 候选技术选项列表

        Returns:
            TechDecision包含选定方案和详细评分信息
        """
        total_weight = sum(criteria.values())
        if total_weight == 0:
            raise ArchitectureError("评估权重总和不能为零")

        normalized_criteria = {k: v / total_weight for k, v in criteria.items()}
        scored_options: list[tuple[TechOption, float]] = []

        for option in options:
            weighted_sum = 0.0
            score_details: dict[str, float] = {}
            for criterion, weight in normalized_criteria.items():
                raw_score = option.scores.get(criterion, 5.0)
                weighted_score = raw_score * weight
                score_details[criterion] = weighted_score
                weighted_sum += weighted_score
            scored_options.append((option, weighted_sum))
            option.scores["_weighted_total"] = weighted_sum

        scored_options.sort(key=lambda x: x[1], reverse=True)
        selected, top_score = scored_options[0]
        runner_up = scored_options[1][0] if len(scored_options) > 1 else None

        rationale_parts = [
            f"{selected.name} 在综合评分中以 {top_score:.2f} 分位居第一",
        ]
        if runner_up:
            _, second_score = scored_options[1]
            rationale_parts.append(f"领先第二名 {runner_up.name} ({second_score:.2f}分) {top_score - second_score:.2f} 分")

        best_criteria = max(score_details.items(), key=lambda x: x[1])
        rationale_parts.append(f"最强项: {best_criteria[0]} ({best_criteria[1]:.2f})")

        decision = TechDecision(
            selected_option=selected,
            runner_up=runner_up,
            criteria_used=normalized_criteria,
            weighted_scores={opt.name: opt.scores.get("_weighted_total", 0) for opt, _ in scored_options},
            rationale="; ".join(rationale_parts),
            confidence=min(0.95, 0.6 + (top_score / 10)),
        )

        self._tech_decisions.append(decision)
        return decision

    def generate_architecture_diagram(
        self, components: list[ComponentInfo | dict], style: str = "c4"
    ) -> str:
        """
        生成系统架构图（Mermaid文本格式）

        Args:
            components: 组件信息列表
            style: 图样式 ('c4', 'deployment', 'flowchart')

        Returns:
            Mermaid格式的架构图文本
        """
        comp_infos: list[ComponentInfo] = []
        for c in components:
            if isinstance(c, ComponentInfo):
                comp_infos.append(c)
            elif isinstance(c, dict):
                comp_infos.append(ComponentInfo(
                    name=c.get("name", ""),
                    type=c.get("type", "component"),
                    technology=c.get("technology", ""),
                    description=c.get("description", ""),
                    connections=[(conn.get("target", ""), conn.get("label", "")) for conn in c.get("connections", [])],
                ))

        match style.lower():
            case "c4":
                return self._generate_c4_diagram(comp_infos)
            case "deployment":
                return self._generate_deployment_diagram(comp_infos)
            case "flowchart":
                return self._generate_flowchart_diagram(comp_infos)
            case _:
                raise ArchitectureError(f"不支持的架构图样式: {style}，支持: c4, deployment, flowchart")

    def _generate_c4_diagram(self, components: list[ComponentInfo]) -> str:
        """C4模型架构图"""
        type_shapes = {
            "person": "([\"{name}\"])",
            "system": "[\"{name}\"]",
            "container": "[\"/{name}/\\n({tech})\"]",
            "component": "[\"{name}\\n{desc}\"]",
            "database": "[(\"{name}\")]",
        }

        lines = ["C4Context", "    title 系统架构图 (C4 Model)", ""]

        type_groups: dict[str, list[ComponentInfo]] = defaultdict(list)
        for comp in components:
            type_groups.setdefault(comp.type, []).append(comp)

        group_labels = {
            "person": "用户/角色",
            "system": "外部系统",
            "container": "容器/服务",
            "component": "组件",
            "database": "数据存储",
        }

        for comp_type, comps in type_groups.items():
            shape_template = type_shapes.get(comp_type, "[\"{name}\"]")
            group_label = group_labels.get(comp_type, comp_type)
            lines.append(f'    Enterprise_Boundary(g{comp_type}, "{group_label}") {{')
            for i, comp in enumerate(comps):
                node_id = f"{comp_type}_{i}"
                shape = shape_template.format(name=comp.name, tech=comp.technology, desc=comp.description[:20])
                lines.append(f"        {node_id}{shape}")
            lines.append("    }")
            lines.append("")

        for comp_type, comps in type_groups.items():
            for i, comp in enumerate(comps):
                src_id = f"{comp_type}_{i}"
                for target, label in comp.connections:
                    target_comp = next((c for c in components if c.name == target), None)
                    if target_comp:
                        for ot, ocs in type_groups.items():
                            for j, oc in enumerate(ocs):
                                if oc.name == target:
                                    tgt_id = f"{ot}_{j}"
                                    line = f"    {src_id} --> {tgt_id}: {label}" if label else f"    {src_id} --> {tgt_id}"
                                    lines.append(line)

        return "\n".join(lines)

    def _generate_deployment_diagram(self, components: list[ComponentInfo]) -> str:
        """部署架构图"""
        lines = ["flowchart LR", "    subgraph 用户层 [[用户层]]"]
        user_comps = [c for c in components if c.type == "person"]
        for i, c in enumerate(user_comps):
            lines.append(f'        U{i}["{c.name}"]')
        lines.append("    end")

        server_types = ["container", "component", "database"]
        for st in server_types:
            svr_comps = [c for c in components if c.type == st]
            if svr_comps:
                label = {"container": "应用服务器", "component": "服务层", "database": "数据层"}.get(st, st)
                lines.append(f'    subgraph {st.capitalize()} [{label}]')
                for i, c in enumerate(svr_comps):
                    tech_info = f"\\n({c.technology})" if c.technology else ""
                    lines.append(f'        S{st[0]}{i}["{c.name}{tech_info}"]')
                lines.append("    end")

        ext_comps = [c for c in components if c.type == "system"]
        if ext_comps:
            lines.append('    subgraph External [[外部系统]]')
            for i, c in enumerate(ext_comps):
                lines.append(f'        E{i}["{c.name}"]')
            lines.append("    end")

        lines.extend([
            "    classDef user fill:#e1f5fe,#01579b",
            "    classDef app fill:#e8f5e9,#2e7d32",
            "    classDef db fill:#fff3e0,#e65100",
            "    classDef ext fill:#fce4ec,#c62828",
        ])

        return "\n".join(lines)

    def _generate_flowchart_diagram(self, components: list[ComponentInfo]) -> str:
        """流程式架构图"""
        lines = ["flowchart TB"]
        for i, comp in enumerate(components):
            tech_suffix = f"<br/>[{comp.technology}]" if comp.technology else ""
            lines.append(f'    C{i}[\"{comp.name}{tech_suffix}\"]')

        for i, comp in enumerate(components):
            for target, label in comp.connections:
                for j, c in enumerate(components):
                    if c.name == target:
                        suffix = f"|{label}|" if label else ""
                        lines.append(f"    C{i} --> C{j}{suffix}")

        return "\n".join(lines)

    def recommend_design_patterns(
        self, problem_type: str, context: dict[str, Any] | None = None
    ) -> list[PatternRecommendation]:
        """
        根据问题类型推荐设计模式（GOF/Enterprise/Concurrency/DDD）

        Args:
            problem_type: 问题类型字符串或ProblemType枚举值
            context: 额外上下文信息

        Returns:
            PatternRecommendation推荐列表
        """
        ctx = context or {}

        pattern_db: dict[str, list[dict[str, Any]]] = {
            ProblemType.OBJECT_CREATION.value: [
                {
                    "name": "Factory Method", "category": "GOF-Creational",
                    "problem": "需要将对象实例化延迟到子类", "solution": "定义创建对象的接口，由子类决定实例化哪个类",
                    "applicability": 0.92, "complexity": "low",
                    "related": ["Abstract Factory", "Builder"],
                    "trade_offs": {"优点": "符合开闭原则", "缺点": "类数量增加"},
                },
                {
                    "name": "Abstract Factory", "category": "GOF-Creational",
                    "problem": "需要创建相关对象家族而不指定具体类", "solution": "提供接口用于创建相关/依赖对象的家族",
                    "applicability": 0.85, "complexity": "medium",
                    "related": ["Factory Method", "Prototype"],
                    "trade_offs": {"优点": "产品族一致性保证", "缺点": "扩展新产品族困难"},
                },
                {
                    "name": "Builder", "category": "GOF-Creational",
                    "problem": "复杂对象的构建与其表示分离", "solution": "分步骤构建复杂对象，相同过程可产生不同表示",
                    "applicability": 0.80, "complexity": "medium",
                    "related": ["Abstract Factory", "Composite"],
                    "trade_offs": {"优点": "构建过程清晰可控", "缺点": "产品间差异大时需多个Builder"},
                },
                {
                    "name": "Singleton", "category": "GOF-Creational",
                    "problem": "确保类只有一个实例并提供全局访问点", "solution": "私有构造+静态方法/属性控制唯一实例",
                    "applicability": 0.75, "complexity": "low",
                    "related": ["Monostate", "Service Locator"],
                    "trade_offs": {"优点": "资源节约", "缺点": "测试困难/隐式耦合"},
                },
                {
                    "name": "Prototype", "category": "GOF-Creational",
                    "problem": "通过复制已有对象来创建新对象", "solution": "实现克隆接口，通过原型复制创建新实例",
                    "applicability": 0.70, "complexity": "low",
                    "related": ["Memento", "Builder"],
                    "trade_offs": {"优点": "隐藏创建复杂性", "缺点": "深拷贝可能复杂"},
                },
            ],
            ProblemType.STRUCTURE_COMPOSITION.value: [
                {
                    "name": "Adapter", "category": "GOF-Structural",
                    "problem": "接口不兼容的类需要协同工作", "solution": "将一个类的接口转换为客户期望的另一个接口",
                    "applicability": 0.93, "complexity": "low",
                    "related": ["Bridge", "Decorator", "Facade"],
                    "trade_offs": {"优点": "复用现有类", "缺点": "增加间接层"},
                },
                {
                    "name": "Facade", "category": "GOF-Structural",
                    "problem": "简化复杂子系统的访问接口", "solution": "为子系统提供统一的高层接口",
                    "applicability": 0.90, "complexity": "low",
                    "related": ["Adapter", "Mediator"],
                    "trade_offs": {"优点": "降低耦合简化调用", "缺点": "可能成为上帝对象"},
                },
                {
                    "name": "Decorator", "category": "GOF-Structural",
                    "problem": "动态地给对象添加额外职责", "solution": "将对象包装在装饰器中动态添加行为",
                    "applicability": 0.85, "complexity": "medium",
                    "related": ["Proxy", "Chain of Responsibility", "Composite"],
                    "trade_offs": {"优点": "灵活组合行为", "缺点": "装饰链过长影响调试"},
                },
                {
                    "name": "Composite", "category": "GOF-Structural",
                    "problem": "树形结构中一致对待个体与组合", "solution": "将对象组合成树形结构以表示部分-整体层次",
                    "applicability": 0.82, "complexity": "medium",
                    "related": ["Iterator", "Visitor", "Decorator"],
                    "trade_offs": {"优点": "统一处理简单/复杂元素", "缺点": "设计过度通用化风险"},
                },
                {
                    "name": "Bridge", "category": "GOF-Structural",
                    "problem": "抽象与实现需要独立变化", "solution": "将抽象部分与实现部分分离，使二者可独立演变",
                    "applicability": 0.78, "complexity": "medium",
                    "related": ["Adapter", "Strategy"],
                    "trade_offs": {"优点": "优秀的可扩展性", "缺点": "增加复杂度"},
                },
                {
                    "name": "Proxy", "category": "GOF-Structural",
                    "problem": "需要控制对对象的访问", "solution": "提供代理对象以控制对真实对象的访问",
                    "applicability": 0.85, "complexity": "low",
                    "related": ["Decorator", "Facade"],
                    "trade_offs": {"优点": "懒加载/缓存/权限控制", "缺点": "响应时间略增"},
                },
            ],
            ProblemType.BEHAVIOR_ALLOCATION.value: [
                {
                    "name": "Strategy", "category": "GOF-Behavioral",
                    "problem": "算法族需要在运行时互换", "solution": "定义一系列算法并封装使它们可以互相替换",
                    "applicability": 0.94, "complexity": "low",
                    "related": ["State", "Template Method", "Command"],
                    "trade_offs": {"优点": "开闭原则/消除条件语句", "缺点": "客户端需了解策略差异"},
                },
                {
                    "name": "Observer", "category": "GOF-Behavioral",
                    "problem": "对象状态变更时通知多个依赖者", "solution": "定义一对多依赖关系，主题变更自动通知所有观察者",
                    "applicability": 0.91, "complexity": "low",
                    "related": ["Mediator", "Pub/Sub", "Reactor"],
                    "trade_offs": {"优点": "松耦合事件通信", "缺点": "调试困难/内存泄漏风险"},
                },
                {
                    "name": "Command", "category": "GOF-Behavioral",
                    "problem": "操作需要封装为对象以便排队/撤销/日志", "solution": "将请求封装为对象从而参数化其他对象",
                    "applicability": 0.87, "complexity": "medium",
                    "related": ["Memento", "Chain of Responsibility", "Strategy"],
                    "trade_offs": {"优点": "撤销/重做/事务支持", "缺点": "可能导致类膨胀"},
                },
                {
                    "name": "Template Method", "category": "GOF-Behavioral",
                    "problem": "算法骨架不变但步骤可变", "solution": "定义算法骨架延迟某些步骤到子类",
                    "applicability": 0.83, "complexity": "low",
                    "related": ["Strategy", "Factory Method", "Hook Methods"],
                    "trade_offs": {"优点": "代码复用/反向控制", "缺点": "继承耦合/限制灵活性"},
                },
                {
                    "name": "State", "category": "GOF-Behavioral",
                    "problem": "对象行为随状态改变而不同", "solution": "将状态封装为独立对象，委托状态相关行为",
                    "applicability": 0.84, "complexity": "medium",
                    "related": ["Strategy", "Observer"],
                    "trade_offs": {"优点": "消除庞大条件语句", "缺点": "状态类数量增长"},
                },
                {
                    "name": "Chain of Responsibility", "category": "GOF-Behavioral",
                    "problem": "多个对象可处理同一请求", "solution": "将请求沿处理者链传递直到被处理",
                    "applicability": 0.78, "complexity": "medium",
                    "related": ["Command", "Decorator", "Composite"],
                    "trade_offs": {"优点": "解耦发送者和接收者", "缺点": "请求可能不被处理"},
                },
                {
                    "name": "Iterator", "category": "GOF-Behavioral",
                    "problem": "遍历聚合对象而不暴露内部表示", "solution": "提供顺序访问聚合元素而不暴露底层表示",
                    "applicability": 0.86, "complexity": "low",
                    "related": ["Composite", "Visitor", "Memento"],
                    "trade_offs": {"优点": "统一遍历接口", "缺点": "并行迭代复杂"},
                },
                {
                    "name": "Mediator", "category": "GOF-Behavioral",
                    "problem": "对象间引用复杂形成网状交互", "solution": "引入中介者封装对象间的交互",
                    "applicability": 0.80, "complexity": "medium",
                    "related": ["Observer", "Facade"],
                    "trade_offs": {"优点": "降低耦合集中控制", "缺点": "中介者可能过于复杂"},
                },
            ],
            ProblemType.CONCURRENCY_CONTROL.value: [
                {
                    "name": "Producer-Consumer", "category": "Concurrency",
                    "problem": "生产者和消费者速率不一致", "solution": "通过缓冲队列解耦生产消费速率",
                    "applicability": 0.90, "complexity": "medium",
                    "related": ["BlockingQueue", "Observer", "Reactor"],
                    "trade_offs": {"优点": "异步解耦背压控制", "缺点": "消息顺序/丢失风险"},
                },
                {
                    "name": "Read-Write Lock", "category": "Concurrency",
                    "problem": "读多写少场景的并发优化", "solution": "允许多读者并行但写者独占",
                    "applicability": 0.88, "complexity": "medium",
                    "related": ["Optimistic Locking", "STM"],
                    "trade_offs": {"优点": "读性能优秀", "缺点": "写饥饿风险"},
                },
                {
                    "name": "Thread Pool", "category": "Concurrency",
                    "problem": "频繁创建销毁线程开销大", "solution": "预创建线程池复用线程执行任务",
                    "applicability": 0.93, "complexity": "low",
                    "related": ["Work Stealing", "Fork/Join"],
                    "trade_offs": {"优点": "资源管理高效", "缺点": "任务阻塞会影响池"},
                },
                {
                    "name": "Actor Model", "category": "Concurrency/Distributed",
                    "problem": "共享状态并发修改困难", "solution": "每个Actor独立状态通过消息通信",
                    "applicability": 0.82, "complexity": "high",
                    "related": ["CSP", "STM", "Reactive Streams"],
                    "trade_offs": {"优点": "无锁天然并行", "缺点": "调试/消息排序复杂"},
                },
            ],
            ProblemType.ENTERPRISE_INTEGRATION.value: [
                {
                    "name": "Repository Pattern", "category": "Enterprise/DDD",
                    "problem": "领域逻辑与数据访问耦合", "solution": "定义集合式接口隔离领域与数据映射",
                    "applicability": 0.92, "complexity": "medium",
                    "related": ["Unit of Work", "Specification", "DAO"],
                    "trade_offs": {"优点": "领域纯净/可测试", "缺点": "查询能力受限"},
                },
                {
                    "name": "Unit of Work", "category": "Enterprise",
                    "problem": "多操作需保持事务一致性", "solution": "跟踪变更批量提交维护一致性",
                    "applicability": 0.89, "complexity": "medium",
                    "related": ["Repository", "Transaction Script"],
                    "trade_offs": {"优点": "事务原子性保证", "缺点": "内存占用/复杂度"},
                },
                {
                    "name": "CQRS", "category": "Enterprise/DDD",
                    "problem": "读写操作特性差异大", "solution": "命令查询职责分离使用不同模型",
                    "applicability": 0.78, "complexity": "high",
                    "related": ["Event Sourcing", "Repository"],
                    "trade_offs": {"优点": "读写各自优化", "缺点": "最终一致性/复杂度"},
                },
                {
                    "name": "Event Sourcing", "category": "Enterprise/DDD",
                    "problem": "需要完整审计和状态回放", "solution": "存储状态变更事件序列而非当前快照",
                    "applicability": 0.73, "complexity": "high",
                    "related": ["CQRS", "Snapshot"],
                    "trade_offs": {"优点": "完整审计/时序查询", "缺点": "事件重构复杂"},
                },
                {
                    "name": "API Gateway", "category": "Enterprise",
                    "problem": "微服务统一入口和横切关注点", "solution": "单一入口路由/认证/限流/熔断",
                    "applicability": 0.91, "complexity": "high",
                    "related": ["Service Mesh", "BFF"],
                    "trade_offs": {"优点": "集中管理/协议转换", "缺点": "单点故障/瓶颈风险"},
                },
                {
                    "name": "Saga Pattern", "category": "Enterprise/Distributed",
                    "problem": "跨服务长事务一致性", "solution": "拆分为本地事务+补偿操作序列",
                    "applicability": 0.85, "complexity": "high",
                    "related": ["Two-Phase Commit", "Outbox"],
                    "trade_offs": {"优点": "分布式最终一致性", "缺点": "补偿逻辑复杂"},
                },
            ],
            ProblemType.DISTRIBUTED_SYSTEM.value: [
                {
                    "name": "Circuit Breaker", "category": "Resilience",
                    "problem": "级联故障导致雪崩效应", "solution": "检测故障自动熔断快速失败",
                    "applicability": 0.95, "complexity": "low",
                    "related": ["Bulkhead", "Retry", "Timeout"],
                    "trade_offs": {"优点": "防止级联故障", "缺点": "半开态判断复杂"},
                },
                {
                    "name": "Bulkhead Isolation", "category": "Resilience",
                    "problem": "某资源耗尽影响整体可用性", "solution": "资源隔离防止故障蔓延",
                    "applicability": 0.88, "complexity": "medium",
                    "related": ["Circuit Breaker", "Rate Limiter"],
                    "trade_offs": {"优点": "故障隔离", "缺点": "资源利用率下降"},
                },
                {
                    "name": "Sidecar Pattern", "category": "Distributed",
                    "problem": "跨语言服务治理能力统一", "solution": "伴随主进程的辅助容器处理横切关注点",
                    "applicability": 0.83, "complexity": "high",
                    "related": ["Service Mesh", "Ambassador"],
                    "trade_offs": {"优点": "语言无关/透明代理", "缺点": "运维复杂度/资源开销"},
                },
            ],
        }

        pt_key = problem_type if isinstance(problem_type, str) else problem_type.value
        patterns_data = pattern_db.get(pt_key, pattern_db.get(ProblemType.BEHAVIOR_ALLOCATION.value, []))

        language = ctx.get("language", "")
        scale = ctx.get("scale", "")

        recommendations: list[PatternRecommendation] = []
        for pd in patterns_data:
            applicability = pd["applicability"]
            if language and language in ["python", "ruby", "javascript"]:
                if pd["complexity"] == "high":
                    applicability -= 0.10
            if scale == "large":
                if "Enterprise" in pd["category"] or "Distributed" in pd["category"]:
                    applicability += 0.05

            rec = PatternRecommendation(
                pattern_name=pd["name"],
                category=pd["category"],
                problem_description=pd["problem"],
                solution_summary=pd["solution"],
                applicability=max(0.0, min(1.0, applicability)),
                complexity=pd["complexity"],
                related_patterns=pd["related"],
                trade_offs=pd["trade_offs"],
            )
            recommendations.append(rec)

        recommendations.sort(key=lambda p: p.applicability, reverse=True)
        return recommendations

    def partition_modules(
        self, domain_model, strategy: str = "ddd"
    ) -> ModuleStructure:
        """
        模块划分（支持DDD/分层/六边形/洋葱等架构策略）

        Args:
            domain_model: 领域模型对象（DomainModel）
            strategy: 架构策略 ('ddd', 'layered', 'hexagonal', 'onion', 'event_driven')

        Returns:
            ModuleStructure模块结构
        """
        arch_style = ArchitectureStyle(strategy)

        match strategy.lower():
            case "ddd":
                return self._partition_ddd(domain_model)
            case "layered":
                return self._partition_layered(domain_model)
            case "hexagonal":
                return self._partition_hexagonal(domain_model)
            case "onion":
                return self._partition_onion(domain_model)
            case "event_driven":
                return self._partition_event_driven(domain_model)
            case _:
                raise ArchitectureError(f"不支持的架构策略: {strategy}，支持: ddd, layered, hexagonal, onion, event_driven")

    def _partition_ddd(self, domain_model) -> ModuleStructure:
        """DDD分层架构"""
        ar_names = []
        entity_names = []
        vo_names = []
        event_names = []

        if hasattr(domain_model, 'bounded_contexts') and domain_model.bounded_contexts:
            bc = domain_model.bounded_contexts[0]
            ar_names = [ar.name for ar in bc.aggregate_roots]
            entity_names = [e.name for e in bc.entities]
            vo_names = [vo.name for vo in bc.value_objects]
            event_names = [de.name for de in bc.domain_events]

        if not ar_names:
            ar_names = ["核心聚合"]
            entity_names = ["业务实体A", "业务实体B"]
            vo_names = ["值对象X"]

        layers = [
            LayerDefinition(
                name="Interface Layer (接口层)",
                description="用户界面/API网关/控制器",
                access_direction="downward",
                modules=[
                    ModuleInfo(name="Controllers", layer="interface", responsibility="HTTP请求处理与响应", dependencies=["ApplicationServices"]),
                    ModuleInfo(name="DTOs", layer="interface", responsibility="数据传输对象定义", dependencies=[]),
                    ModuleInfo(name="Presenters", layer="interface", responsibility="视图模型格式化", dependencies=["ApplicationServices"]),
                ],
            ),
            LayerDefinition(
                name="Application Layer (应用层)",
                description="用例编排/事务协调/DTO转换",
                access_direction="bidirectional",
                modules=[
                    ModuleInfo(name="ApplicationServices", layer="application", responsibility="用例编排与应用服务", dependencies=["DomainServices", "Repositories"]),
                    ModuleInfo(name="Commands", layer="application", responsibility="命令对象定义", dependencies=[]),
                    ModuleInfo(name="QueryHandlers", layer="application", responsibility="查询处理器", dependencies=["Repositories"]),
                    ModuleInfo(name="EventHandlers", layer="application", responsibility="领域事件处理", dependencies=["DomainServices"]),
                ],
            ),
            LayerDefinition(
                name="Domain Layer (领域层)",
                description="核心业务逻辑/聚合根/实体/值对象/领域服务",
                access_direction="core",
                modules=[
                    ModuleInfo(name="Aggregates", layer="domain", responsibility=f"聚合根: {', '.join(ar_names)}", dependencies=["ValueObjects", "DomainServices"]),
                    ModuleInfo(name="Entities", layer="domain", responsibility=f"实体: {', '.join(entity_names)}", dependencies=["ValueObjects"]),
                    ModuleInfo(name="ValueObjects", layer="domain", responsibility=f"值对象: {', '.join(vo_names)}", dependencies=[]),
                    ModuleInfo(name="DomainServices", layer="domain", responsibility="跨聚合领域服务", dependencies=["Aggregates"]),
                    ModuleInfo(name="DomainEvents", layer="domain", responsibility=f"领域事件: {', '.join(event_names[:5])}", dependencies=[]),
                    ModuleInfo(name="RepositoryInterfaces", layer="domain", responsibility="仓储接口定义", dependencies=["Aggregates"]),
                ],
            ),
            LayerDefinition(
                name="Infrastructure Layer (基础设施层)",
                description="持久化/外部服务/消息队列/配置",
                access_direction="upward",
                modules=[
                    ModuleInfo(name="Persistence", layer="infrastructure", responsibility="ORM/数据库访问实现", dependencies=["RepositoryInterfaces"]),
                    ModuleInfo(name="ExternalServices", layer="infrastructure", responsibility="第三方API集成", dependencies=[]),
                    ModuleInfo(name="Messaging", layer="infrastructure", responsibility="消息队列发布订阅", dependencies=["DomainEvents"]),
                    ModuleInfo(name="Configuration", layer="infrastructure", responsibility="配置管理与环境变量", dependencies=[]),
                    ModuleInfo(name="Security", layer="infrastructure", responsibility="认证授权加密实现", dependencies=[]),
                ],
            ),
        ]

        pkg_map = {
            "Controllers": "interfaces.controllers",
            "ApplicationServices": "application.services",
            "Aggregates": "domain.aggregates",
            "Entities": "domain.entities",
            "Persistence": "infrastructure.persistence",
        }

        return ModuleStructure(
            architecture_style=ArchitectureStyle.DDD,
            layers=layers,
            cross_cutting_concerns=["日志", "异常处理", "缓存", "国际化", "审计日志"],
            package_mapping=pkg_map,
        )

    def _partition_layered(self, domain_model) -> ModuleStructure:
        """经典三层架构"""
        layers = [
            LayerDefinition(
                name="Presentation Layer (表现层)",
                description="UI/Web API/移动端",
                access_direction="downward",
                modules=[
                    ModuleInfo(name="WebControllers", layer="presentation", responsibility="Web API端点", dependencies=["BusinessLogic"]),
                    ModuleInfo(name="Views", layer="presentation", responsibility="页面模板/SPA组件", dependencies=["BusinessLogic"]),
                    ModuleInfo(name="ViewModels", layer="presentation", responsibility="视图模型", dependencies=[]),
                ],
            ),
            LayerDefinition(
                name="Business Logic Layer (业务逻辑层)",
                description="核心规则/工作流/校验",
                access_direction="bidirectional",
                modules=[
                    ModuleInfo(name="BusinessLogic", layer="business", responsibility="业务规则引擎", dependencies=["DataAccess"]),
                    ModuleInfo(name="Services", layer="business", responsibility="业务服务编排", dependencies=["DataAccess"]),
                    ModuleInfo(name="Validators", layer="business", responsibility="输入校验规则", dependencies=[]),
                    ModuleInfo(name="Workflows", layer="business", responsibility="审批流程/状态机", dependencies=["DataAccess"]),
                ],
            ),
            LayerDefinition(
                name="Data Access Layer (数据访问层)",
                description="数据库CRUD/ORM/缓存",
                access_direction="upward",
                modules=[
                    ModuleInfo(name="DataAccess", layer="data", responsibility="数据访问对象", dependencies=[]),
                    ModuleInfo(name="Repositories", layer="data", responsibility="仓储实现", dependencies=[]),
                    ModuleInfo(name="DbContext", layer="data", responsibility="数据库上下文/连接管理", dependencies=[]),
                    ModuleInfo(name="Migrations", layer="data", responsibility="数据库迁移脚本", dependencies=[]),
                ],
            ),
        ]

        return ModuleStructure(
            architecture_style=ArchitectureStyle.LAYERED,
            layers=layers,
            cross_cutting_concerns=["日志", "异常处理", "缓存", "安全"],
            package_mapping={"WebControllers": "controllers", "BusinessLogic": "services", "DataAccess": "repositories"},
        )

    def _partition_hexagonal(self, domain_model) -> ModuleStructure:
        """六边形/端口适配器架构"""
        layers = [
            LayerDefinition(
                name="Ports In (入站端口)",
                description="用例接口定义",
                access_direction="inward",
                modules=[
                    ModuleInfo(name="UseCasePorts", layer="port-in", responsibility="用例接口(驱动端口)", dependencies=["DomainModel"]),
                    ModuleInfo(name="APIPorts", layer="port-in", responsibility="REST/gRPC接口定义", dependencies=[]),
                    ModuleInfo(name="EventListeners", layer="port-in", responsibility="事件监听器接口", dependencies=[]),
                ],
            ),
            LayerDefinition(
                name="Application Core (应用核心)",
                description="领域模型+用例实现",
                access_direction="core",
                modules=[
                    ModuleInfo(name="DomainModel", layer="core", responsibility="实体/值对象/领域服务", dependencies=[]),
                    ModuleInfo(name="UseCases", layer="core", responsibility="用例实现(驱动端口实现)", dependencies=["DomainModel", "PortsOut"]),
                    ModuleInfo(name="DomainEvents", layer="core", responsibility="领域事件定义与发布", dependencies=["DomainModel"]),
                ],
            ),
            LayerDefinition(
                name="Ports Out (出站端口)",
                description="副作用接口定义",
                access_direction="outward",
                modules=[
                    ModuleInfo(name="PortsOut", layer="port-out", responsibility="持久化/外部服务接口", dependencies=[]),
                    ModuleInfo(name="RepositoryPorts", layer="port-out", responsibility="仓储接口", dependencies=["DomainModel"]),
                ],
            ),
            LayerDefinition(
                name="Adapters (适配器)",
                description="入站/出站适配器实现",
                access_direction="external",
                modules=[
                    ModuleInfo(name="WebAdapter", layer="adapter-in", responsibility="HTTP入站适配器", dependencies=["UseCasePorts"]),
                    ModuleInfo(name="CLIAdapter", layer="adapter-in", responsibility="命令行入站适配器", dependencies=["UseCasePorts"]),
                    ModuleInfo(name="PersistenceAdapter", layer="adapter-out", responsibility="数据库出站适配器", dependencies=["RepositoryPorts"]),
                    ModuleInfo(name="ExternalServiceAdapter", layer="adapter-out", responsibility="第三方服务适配器", dependencies=["PortsOut"]),
                ],
            ),
        ]

        return ModuleStructure(
            architecture_style=ArchitectureStyle.HEXAGONAL,
            layers=layers,
            cross_cutting_concerns=["日志", "异常处理", "指标收集"],
            package_mapping={
                "UseCasePorts": "ports.in",
                "UseCases": "application",
                "PersistenceAdapter": "adapters.persistence",
            },
        )

    def _partition_onion(self, domain_model) -> ModuleStructure:
        """洋葱架构"""
        layers = [
            LayerDefinition(
                name="Domain Core (领域核心)",
                description="最内层：纯业务逻辑，零外部依赖",
                access_direction="innermost",
                modules=[
                    ModuleInfo(name="Entities", layer="domain-core", responsibility="业务实体与规则", dependencies=[]),
                    ModuleInfo(name="DomainServices", layer="domain-core", responsibility="领域服务接口", dependencies=["Entities"]),
                    ModuleInfo(name="DomainEvents", layer="domain-core", responsibility="领域事件定义", dependencies=[]),
                ],
            ),
            LayerDefinition(
                name="Domain Services (领域服务)",
                description="领域服务实现",
                access_direction="inward",
                modules=[
                    ModuleInfo(name="DomainServiceImpl", layer="domain-services", responsibility="领域服务实现", dependencies=["Entities"]),
                    ModuleInfo(name="RepositoryInterfaces", layer="domain-services", responsibility="仓储接口", dependencies=["Entities"]),
                    ModuleInfo(name="Specifications", layer="domain-services", responsibility="规约模式实现", dependencies=["Entities"]),
                ],
            ),
            LayerDefinition(
                name="Application (应用层)",
                description="用例编排/Application Services",
                access_direction="inward",
                modules=[
                    ModuleInfo(name="ApplicationServices", layer="application", responsibility="应用服务/用例", dependencies=["DomainServiceImpl", "RepositoryInterfaces"]),
                    ModuleInfo(name="DTOs", layer="application", responsibility="内部传输对象", dependencies=[]),
                    ModuleInfo(name="Interfaces", layer="application", responsibility="用例接口(供外层实现)", dependencies=["DTOs"]),
                ],
            ),
            LayerDefinition(
                name="Infrastructure (基础设施)",
                description="最外层：所有具体实现",
                access_direction="outermost",
                modules=[
                    ModuleInfo(name="Persistence", layer="infrastructure", responsibility="持久化实现", dependencies=["RepositoryInterfaces"]),
                    ModuleInfo(name="WebAPI", layer="infrastructure", responsibility="Web框架/控制器", dependencies=["ApplicationServices"]),
                    ModuleInfo(name="ExternalIntegrations", layer="infrastructure", responsibility="外部系统集成", dependencies=[]),
                    ModuleInfo(name="Messaging", layer="infrastructure", responsibility="消息队列实现", dependencies=[]),
                ],
            ),
        ]

        return ModuleStructure(
            architecture_style=ArchitectureStyle.ONION,
            layers=layers,
            cross_cutting_concerns=["日志", "异常处理", "安全", "缓存", "监控"],
            package_mapping={
                "Entities": "domain.entities",
                "ApplicationServices": "application.services",
                "Persistence": "infrastructure.persistence",
            },
        )

    def _partition_event_driven(self, domain_model) -> ModuleStructure:
        """事件驱动架构"""
        layers = [
            LayerDefinition(
                name="Event Producers (事件生产者)",
                description="产生领域事件的边界模块",
                access_direction="outward",
                modules=[
                    ModuleInfo(name="APIGateway", layer="producer", responsibility="接收请求触发事件", dependencies=["EventBus"]),
                    ModuleInfo(name="ScheduledJobs", layer="producer", responsibility="定时触发事件", dependencies=["EventBus"]),
                    ModuleInfo(name="Webhooks", layer="producer", responsibility="Webhook接收转事件", dependencies=["EventBus"]),
                ],
            ),
            LayerDefinition(
                name="Event Bus (事件总线)",
                description="事件路由/分发/持久化",
                access_direction="central",
                modules=[
                    ModuleInfo(name="EventBus", layer="bus", responsibility="事件发布/订阅/路由", dependencies=[]),
                    ModuleInfo(name="EventStore", layer="bus", responsibility="事件持久化存储", dependencies=[]),
                    ModuleInfo(name="SchemaRegistry", layer="bus", responsibility="事件 Schema 管理", dependencies=[]),
                ],
            ),
            LayerDefinition(
                name="Event Processors (事件处理器)",
                description="事件消费者/ Saga 编排",
                access_direction="inward",
                modules=[
                    ModuleInfo(name="Projectors", layer="processor", responsibility="投影/读模型更新", dependencies=["EventBus"]),
                    ModuleInfo(name="Sagas", layer="processor", responsibility="长事务编排/Saga", dependencies=["EventBus"]),
                    ModuleInfo(name="DomainHandlers", layer="processor", responsibility="领域事件处理", dependencies=["DomainCore"]),
                ],
            ),
            LayerDefinition(
                name="Domain Core (领域核心)",
                description="聚合根/领域服务",
                access_direction="core",
                modules=[
                    ModuleInfo(name="DomainCore", layer="domain", responsibility="聚合根与领域逻辑", dependencies=[]),
                    ModuleInfo(name="ReadModels", layer="domain", responsibility="CQRS 读模型", dependencies=[]),
                ],
            ),
        ]

        return ModuleStructure(
            architecture_style=ArchitectureStyle.EVENT_DRIVEN,
            layers=layers,
            cross_cutting_concerns=["事件版本化", "幂等处理", "死信队列", "监控告警"],
            package_mapping={
                "EventBus": "infra.eventbus",
                "Sagas": "application.sagas",
                "DomainCore": "domain",
            },
        )

    def analyze_dependencies(self, modules: list[ModuleInfo | str]) -> DependencyGraph:
        """
        分析模块间依赖关系并检测循环依赖

        Args:
            modules: 模块信息列表（ModuleInfo对象或模块名字符串）

        Returns:
            DependencyGraph依赖分析结果
        """
        module_infos: list[ModuleInfo] = []
        for m in modules:
            if isinstance(m, ModuleInfo):
                module_infos.append(m)
            elif isinstance(m, str):
                module_infos.append(ModuleInfo(name=m))

        nodes = [m.name for m in module_infos]
        edges: list[DependencyEdge] = []
        adj: dict[str, list[str]] = defaultdict(list)

        for mod in module_infos:
            for dep in mod.dependencies:
                if dep in nodes:
                    edge = DependencyEdge(from_module=mod.name, to_module=dep)
                    edges.append(edge)
                    adj[mod.name].append(dep)

        circular_deps = self._detect_cycles(adj, nodes)

        depth_map: dict[str, int] = {}
        fan_in: dict[str, int] = defaultdict(int)
        fan_out: dict[str, int] = defaultdict(int)

        for edge in edges:
            fan_out[edge.from_module] += 1
            fan_in[edge.to_module] += 1

        visited: set[str] = set()

        def calc_depth(node: str, current_depth: int = 0) -> None:
            if node in visited:
                return
            visited.add(node)
            deps = adj.get(node, [])
            if not deps:
                depth_map[node] = max(depth_map.get(node, 0), current_depth)
                return
            for dep in deps:
                calc_depth(dep, current_depth + 1)
            depth_map[node] = max(depth_map.get(node, 0), current_depth)

        for n in nodes:
            if n not in visited:
                calc_depth(n)

        for n in nodes:
            if n not in depth_map:
                depth_map[n] = 0

        return DependencyGraph(
            nodes=nodes,
            edges=edges,
            circular_dependencies=circular_deps,
            depth_map=dict(depth_map),
            fan_in=dict(fan_in),
            fan_out=dict(fan_out),
        )

    def _detect_cycles(self, adj: dict[str, list[str]], nodes: list[str]) -> list[list[str]]:
        """DFS检测循环依赖"""
        WHITE, GRAY, BLACK = 0, 1, 2
        color: dict[str, int] = {n: WHITE for n in nodes}
        cycles: list[list[str]] = []
        path: list[str] = []

        def dfs(node: str) -> None:
            color[node] = GRAY
            path.append(node)
            for neighbor in adj.get(node, []):
                if neighbor not in color:
                    continue
                if color[neighbor] == GRAY:
                    idx = path.index(neighbor)
                    cycles.append(path[idx:] + [neighbor])
                elif color[neighbor] == WHITE:
                    dfs(neighbor)
            path.pop()
            color[node] = BLACK

        for node in nodes:
            if color[node] == WHITE:
                dfs(node)

        unique_cycles: list[list[str]] = []
        seen: set[tuple[str, ...]] = set()
        for cycle in cycles:
            key = tuple(cycle)
            if key not in seen:
                seen.add(key)
                unique_cycles.append(cycle)

        return unique_cycles

    def define_api_boundaries(self, module_structure: ModuleStructure) -> APIContract:
        """
        定义模块间API接口契约

        Args:
            module_structure: 模块结构对象

        Returns:
            APIContract接口契约
        """
        endpoints: list[APIEndpoint] = []

        for layer in module_structure.layers:
            for mod in layer.modules:
                if any(kw in mod.responsibility.lower() for kw in ["crud", "增删改查", "查询", "管理", "controller", "api"]):
                    base_actions = [
                        ("GET", f"/{mod.name.lower()}/list", f"获取{mod.name}列表"),
                        ("GET", f"/{mod.name.lower()}/{{id}}", f"获取{mod.name}详情"),
                        ("POST", f"/{mod.name.lower()}", f"创建{mod.name}"),
                        ("PUT", f"/{mod.name.lower()}/{{id}}", f"更新{mod.name}"),
                        ("DELETE", f"/{mod.name.lower()}/{{id}}", f"删除{mod.name}"),
                    ]
                    for method, path, desc in base_actions:
                        endpoints.append(APIEndpoint(
                            method=method,
                            path=path,
                            description=desc,
                            request_schema={"type": "object"} if method in ("POST", "PUT") else {},
                            response_schema={"type": "object", "properties": {"code": {"type": "integer"}, "data": {"type": "object"}, "message": {"type": "string"}}},
                            auth_required=True,
                        ))
                elif "service" in mod.name.lower() or "handler" in mod.name.lower():
                    endpoints.append(APIEndpoint(
                        method="POST",
                        path=f"/{mod.name.lower()}/execute",
                        description=f"执行{mod.name}逻辑",
                        request_schema={"type": "object", "properties": {"action": {"type": "string"}}},
                        response_schema={"type": "object"},
                        auth_required=True,
                    ))

        if not endpoints:
            default_endpoints = [
                ("GET", "/health", "健康检查", False),
                ("GET", "/api/v1/resources", "资源列表", True),
                ("POST", "/api/v1/resources", "创建资源", True),
                ("GET", "/api/v1/resources/{id}", "资源详情", True),
                ("PUT", "/api/v1/resources/{id}", "更新资源", True),
                ("DELETE", "/api/v1/resources/{id}", "删除资源", True),
            ]
            for method, path, desc, auth in default_endpoints:
                endpoints.append(APIEndpoint(method=method, path=path, description=desc, auth_required=auth))

        shared_models = {
            "ApiResponse": {
                "type": "object",
                "properties": {
                    "code": {"type": "integer", "example": 200},
                    "message": {"type": "string", "example": "success"},
                    "data": {"oneOf": [{"type": "array"}, {"type": "object"}, {"type": "null"}]},
                },
            },
            "PaginatedResponse": {
                "type": "object",
                "properties": {
                    "items": {"type": "array"},
                    "total": {"type": "integer"},
                    "page": {"type": "integer"},
                    "page_size": {"type": "integer"},
                },
            },
            "ErrorResponse": {
                "type": "object",
                "properties": {
                    "code": {"type": "integer"},
                    "error": {"type": "string"},
                    "details": {"type": "array", "items": {"type": "string"}},
                },
            },
        }

        return APIContract(
            endpoints=endpoints,
            shared_models=shared_models,
            authentication={"type": "Bearer JWT", "token_url": "/auth/token"},
            rate_limiting={"requests_per_minute": "60", "burst": "100"},
        )

    def record_adr(
        self,
        title: str,
        context: str,
        decision: str,
        consequences: str,
        alternatives: list[str] | None = None,
        status: ADRStatus = ADRStatus.ACCEPTED,
        authors: list[str] | None = None,
        tags: list[str] | None = None,
    ) -> ADR:
        """
        记录架构决策 (Architecture Decision Record)

        Args:
            title: 决策标题
            context: 决策背景/上下文
            decision: 决策内容
            consequences: 决策后果
            alternatives: 备选方案列表
            status: ADR状态
            authors: 作者列表
            tags: 标签列表

        Returns:
            ADR架构决策记录
        """
        ArchitectureBureau._adr_counter += 1

        adr = ADR(
            id=ArchitectureBureau._adr_counter,
            title=title,
            status=status,
            context=context,
            decision=decision,
            consequences=consequences,
            alternatives=alternatives or [],
            authors=authors or ["Architecture Bureau"],
            tags=tags or [],
        )

        self._adrs.append(adr)
        output_path = self._output_dir / f"ADR-{adr.id:04d}-{title.replace(' ', '-')}.md"
        try:
            self._output_dir.mkdir(parents=True, exist_ok=True)
            output_path.write_text(adr.to_markdown(), encoding="utf-8")
        except OSError as e:
            raise ArchitectureError(f"写入ADR文件失败 [{output_path}]: {e}") from e

        return adr

    def define_nfrs(
        self,
        scalability: dict[str, Any] | None = None,
        reliability: dict[str, Any] | None = None,
        security: dict[str, Any] | None = None,
    ) -> NFRSpec:
        """
        定义非功能性需求规格

        Args:
            scalability: 可扩展性指标
            reliability: 可靠性指标
            security: 安全性指标

        Returns:
            NFRSpec非功能性需求规格
        """
        scal_items = [
            NFRItem(category="可扩展性", metric="水平扩展能力", target_value=scalability.get("horizontal", "支持至少3节点集群") if scalability else "支持至少3节点集群", priority="high", measurement_method="压力测试验证"),
            NFRItem(category="可扩展性", metric="垂直扩展效率", target_value=scalability.get("vertical", "CPU/内存利用率>70%") if scalability else "CPU/内存利用率>70%", priority="medium", measurement_method="资源监控"),
            NFRItem(category="可扩展性", metric="数据分片支持", target_value=scalability.get("sharding", "支持按业务维度分片") if scalability else "支持按业务维度分片", priority="medium", measurement_method="架构评审"),
        ]

        rel_items = [
            NFRItem(category="可靠性", metric="系统可用性(SLA)", target_value=reliability.get("sla", "99.9%") if reliability else "99.9%", priority="critical", measurement_method="持续监控统计"),
            NFRItem(category="可靠性", metric="平均恢复时间(MTTR)", target_value=reliability.get("mttr", "<30分钟") if reliability else "<30分钟", priority="high", measurement_method="故障演练"),
            NFRItem(category="可靠性", metric="数据持久性", target_value=reliability.get("data_durability", "99.9999999%") if reliability else "99.9999999%", priority="critical", measurement_method="备份恢复测试"),
            NFRItem(category="可靠性", metric="灾难恢复(RTO/RPO)", target_value=reliability.get("dr", "RTO<1h, RPO<5min") if reliability else "RTO<1h, RPO<5min", priority="high", measurement_method="灾备演练"),
        ]

        sec_items = [
            NFRItem(category="安全性", metric="身份认证", target_value=security.get("auth", "JWT/OAuth2 + MFA") if security else "JWT/OAuth2 + MFA", priority="critical", measurement_method="渗透测试"),
            NFRItem(category="安全性", metric="数据加密", target_value=security.get("encryption", "TLS1.3 + AES-256") if security else "TLS1.3 + AES-256", priority="critical", measurement_method="安全扫描"),
            NFRItem(category="安全性", metric="访问控制", target_value=security.get("access_control", "RBAC + ABAC") if security else "RBAC + ABAC", priority="high", measurement_method="权限审计"),
            NFRItem(category="安全性", metric="安全合规", target_value=security.get("compliance", "OWASP Top 10 + GDPR") if security else "OWASP Top 10 + GDPR", priority="high", measurement_method="合规审计"),
        ]

        perf_items = [
            NFRItem(category="性能", metric="API响应时间(P50/P95/P99)", target_value="<100ms / <500ms / <1000ms", priority="high", measurement_method="APM监控"),
            NFRItem(category="性能", metric="吞吐量(TPS/QPS)", target_value=">1000 QPS (核心接口)", priority="high", measurement_method="负载测试"),
            NFRItem(category="性能", metric="并发用户数", target_value=">=1000 并发用户", priority="medium", measurement_method="压力测试"),
        ]

        maint_items = [
            NFRItem(category="可维护性", metric="代码覆盖率", target_value=">=80% (核心路径)", priority="medium", measurement_method="CI报告"),
            NFRItem(category="可维护性", metric="技术债务占比", target_value="<15%", priority="medium", measurement_method="SonarQube扫描"),
            NFRItem(category="可维护性", metric="文档完整性", target_value="API文档覆盖率100%", priority="low", measurement_method="人工审核"),
        ]

        return NFRSpec(
            scalability=scal_items,
            reliability=rel_items,
            security=sec_items,
            performance=perf_items,
            maintainability=maint_items,
        )


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 架构设计局测试")
    print("=" * 60)

    bureau = ArchitectureBureau()

    print("\n--- 技术选型测试 ---")
    criteria = {"性能": 0.25, "生态": 0.20, "学习成本": 0.15, "社区活跃度": 0.15, "可维护性": 0.15, "安全性": 0.10}
    options = [
        TechOption(name="FastAPI", category="Web框架", description="高性能Python Web框架", scores={"性能": 9, "生态": 8, "学习成本": 7, "社区活跃度": 9, "可维护性": 8, "安全性": 8}, pros=["异步原生", "自动文档"], cons=["生态相对较新"]),
        TechOption(name="Django", category="Web框架", description="全功能Python Web框架", scores={"性能": 6, "生态": 10, "学习成本": 6, "社区活跃度": 10, "可维护性": 9, "安全性": 9}, pros=[" batteries included", "ORM/Admin"], cons=[ "同步默认", "重量级"]),
        TechOption(name="Flask", category="Web框架", description="轻量级Python微框架", scores={"性能": 7, "生态": 8, "学习成本": 9, "社区活跃度": 8, "可维护性": 7, "安全性": 7}, pros=["灵活轻量", "易上手"], cons=["需自行组装"]),
    ]
    decision = bureau.tech_selection(criteria, options)
    print(f"✅ 选定: {decision.selected_option.name} (置信度: {decision.confidence:.0%})")
    print(f"   理由: {decision.rationale[:60]}...")

    print("\n--- 架构图生成测试 ---")
    components = [
        ComponentInfo(name="用户", type="person", description="系统使用者"),
        ComponentInfo(name="Web前端", type="container", technology="React", description="单页应用", connections=[("API网关", "HTTPS")]),
        ComponentInfo(name="API网关", type="container", technology="Nginx/Kong", description="路由/限流/认证", connections=[("应用服务", "HTTP")]),
        ComponentInfo(name="应用服务", type="container", technology="Python/FastAPI", description="核心业务服务", connections=[("数据库", "SQL"), ("缓存", "Redis"), ("消息队列", "AMQP")]),
        ComponentInfo(name="数据库", type="database", technology="PostgreSQL", description="主数据存储"),
        ComponentInfo(name="缓存", type="database", technology="Redis", description="分布式缓存"),
        ComponentInfo(name="消息队列", type="container", technology="RabbitMQ", description="异步消息"),
    ]
    diagram_c4 = bureau.generate_architecture_diagram(components, "c4")
    diagram_deploy = bureau.generate_architecture_diagram(components, "deployment")
    diagram_flow = bureau.generate_architecture_diagram(components, "flowchart")
    print(f"✅ C4图长度: {len(diagram_c4)} 字符")
    print(f"✅ 部署图长度: {len(diagram_deploy)} 字符")
    print(f"✅ 流程图长度: {len(diagram_flow)} 字符")

    print("\n--- 设计模式推荐测试 ---")
    for ptype in [ProblemType.BEHAVIOR_ALLOCATION, ProblemType.ENTERPRISE_INTEGRATION, ProblemType.CONCURRENCY_CONTROL]:
        patterns = bureau.recommend_design_patterns(ptype.value, {"scale": "large"})
        print(f"✅ {ptype.value}: Top3 -> {[p.pattern_name for p in patterns[:3]]}")

    print("\n--- 模块划分测试 ---")
    dummy_domain = type('obj', (object,), {'bounded_contexts': []})()
    for strategy in ["ddd", "layered", "hexagonal", "onion", "event_driven"]:
        structure = bureau.partition_modules(dummy_domain, strategy)
        print(f"✅ {strategy}: {len(structure.layers)} 层, {sum(len(l.modules) for l in structure.layers)} 个模块")

    print("\n--- 依赖分析测试 ---")
    test_modules = [
        ModuleInfo(name="Controllers", dependencies=["Services", "DTOs"]),
        ModuleInfo(name="Services", dependencies=["Repositories", "Domain"]),
        ModuleInfo(name="Repositories", dependencies=["Domain", "Database"]),
        ModuleInfo(name="Domain", dependencies=[]),
        ModuleInfo(name="DTOs", dependencies=[]),
        ModuleInfo(name="Database", dependencies=[]),
        ModuleInfo(name="Utils", dependencies=["Domain"]),  # OK
    ]
    dep_graph = bureau.analyze_dependencies(test_modules)
    print(f"✅ 节点数: {len(dep_graph.nodes)}, 边数: {len(dep_graph.edges)}")
    print(f"✅ 循环依赖: {'有' if dep_graph.has_circular_deps() else '无'}")
    print(f"✅ 最大扇出: {(max(dep_graph.fan_out.values()) if dep_graph.fan_out else 0)}")
    print(f"依赖图(Mermaid):\n{dep_graph.to_mermaid()}")

    print("\n--- API边界定义测试 ---")
    ddd_structure = bureau.partition_modules(dummy_domain, "ddd")
    api_contract = bureau.define_api_boundaries(ddd_structure)
    print(f"✅ 端点数: {len(api_contract.endpoints)}")
    print(f"✅ 共享模型: {list(api_contract.shared_models.keys())}")
    print(f"OpenAPI预览:\n{api_contract.to_openapi3()[:400]}...")

    print("\n--- ADR记录测试 ---")
    adr = bureau.record_adr(
        title="选择FastAPI作为Web框架",
        context="项目需要高性能异步Web服务，同时要求良好的API文档自动化能力。",
        decision="采用FastAPI作为主要Web框架，基于Pydantic进行数据校验。",
        consequences="团队需要学习异步编程模式；获得原生OpenAPI支持和优异性能。",
        alternatives=["Django + DRF", "Flask + connexion", "Tornado"],
        tags=["web-framework", "tech-selection"],
    )
    print(f"✅ ADR-{adr.id:04d}: {adr.title}")
    print(f"   状态: {adr.status.value}, 备选方案: {len(adr.alternatives)} 个")

    print("\n--- NFR定义测试 ---")
    nfr_spec = bureau.define_nfrs(
        scalability={"horizontal": "支持Kubernetes自动扩缩容", "vertical": "CPU利用率>80%"},
        reliability={"sla": "99.95%", "mttr": "<15分钟"},
        security={"auth": "JWT + OAuth2.0 + FIDO2", "encryption": "TLS1.3 + AES-256-GCM"},
    )
    print(f"✅ 可扩展性指标: {len(nfr_spec.scalability)} 条")
    print(f"✅ 可靠性指标: {len(nfr_spec.reliability)} 条")
    print(f"✅ 安全性指标: {len(nfr_spec.security)} 条")
    print(f"✅ 性能指标: {len(nfr_spec.performance)} 条")
    print(f"NFR Markdown:\n{nfr_spec.to_markdown()[:500]}...")

    print("\n✅ 架构设计局所有测试通过!")
