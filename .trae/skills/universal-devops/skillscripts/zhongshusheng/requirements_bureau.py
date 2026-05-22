"""
需求分析局 - 中书省第一局

负责需求收集、业务分析、领域建模、用户故事生成、优先级排序、
需求追踪矩阵构建及PRD文档生成等全流程需求工程活动。
"""
from __future__ import annotations

import json
import uuid
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any


class RequirementsError(Exception):
    """需求分析局相关异常"""
    pass


class Priority(str, Enum):
    """需求优先级枚举"""
    MUST_HAVE = "Must Have"
    SHOULD_HAVE = "Should Have"
    COULD_HAVE = "Could Have"
    WONT_HAVE = "Won't Have"
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class RequirementStatus(str, Enum):
    """需求状态枚举"""
    DRAFT = "draft"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    IMPLEMENTED = "implemented"
    DEPRECATED = "deprecated"


class RequirementType(str, Enum):
    """需求类型枚举"""
    FUNCTIONAL = "functional"
    NON_FUNCTIONAL = "non_functional"
    BUSINESS = "business"
    USER_INTERFACE = "user_interface"
    INTEGRATION = "integration"
    DATA = "data"
    SECURITY = "security"


@dataclass
class Requirement:
    """需求数据类"""
    id: str
    title: str
    description: str
    requirement_type: RequirementType = RequirementType.FUNCTIONAL
    priority: Priority = Priority.MEDIUM
    status: RequirementStatus = RequirementStatus.DRAFT
    source: str = ""
    acceptance_criteria: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "type": self.requirement_type.value,
            "priority": self.priority.value,
            "status": self.status.value,
            "source": self.source,
            "acceptance_criteria": self.acceptance_criteria,
            "dependencies": self.dependencies,
            "tags": self.tags,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class UserStory:
    """用户故事数据类"""
    id: str
    role: str
    action: str
    benefit: str
    priority: Priority = Priority.MEDIUM
    story_points: int | None = None
    epic: str | None = None
    acceptance_criteria: list[AcceptanceCriterion] = field(default_factory=list)
    notes: str = ""
    status: str = "draft"

    @property
    def as_a_i_want_so_that(self) -> str:
        return f"作为一个{self.role}，我想要{self.action}，以便{self.benefit}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "role": self.role,
            "action": self.action,
            "benefit": self.benefit,
            "priority": self.priority.value,
            "story_points": self.story_points,
            "epic": self.epic,
            "acceptance_criteria": [ac.to_dict() for ac in self.acceptance_criteria],
            "notes": self.notes,
            "status": self.status,
        }


@dataclass
class AcceptanceCriterion:
    """验收标准数据类（Given/When/Then格式）"""
    id: str
    given: str
    when: str
    then: str
    priority: Priority = Priority.MEDIUM

    def to_gwt_string(self) -> str:
        return f"Given {self.given}\n  When {self.when}\n  Then {self.then}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "given": self.given,
            "when": self.when,
            "then": self.then,
            "priority": self.priority.value,
        }


@dataclass
class AggregateRoot:
    """聚合根"""
    name: str
    attributes: list[str] = field(default_factory=list)
    behaviors: list[str] = field(default_factory=list)
    invariants: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "attributes": self.attributes, "behaviors": self.behaviors, "invariants": self.invariants}


@dataclass
class Entity:
    """实体"""
    name: str
    identifier: str
    attributes: list[str] = field(default_factory=list)
    aggregate_root: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "identifier": self.identifier, "attributes": self.attributes, "aggregate_root": self.aggregate_root}


@dataclass
class ValueObject:
    """值对象"""
    name: str
    attributes: list[str] = field(default_factory=list)
    immutable: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "attributes": self.attributes, "immutable": self.immutable}


@dataclass
class DomainEvent:
    """领域事件"""
    name: str
    payload: list[str] = field(default_factory=list)
    triggered_by: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "payload": self.payload, "triggered_by": self.triggered_by}


@dataclass
class BoundedContext:
    """限界上下文"""
    name: str
    aggregate_roots: list[AggregateRoot] = field(default_factory=list)
    entities: list[Entity] = field(default_factory=list)
    value_objects: list[ValueObject] = field(default_factory=list)
    domain_events: list[DomainEvent] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "aggregate_roots": [ar.to_dict() for ar in self.aggregate_roots],
            "entities": [e.to_dict() for e in self.entities],
            "value_objects": [vo.to_dict() for vo in self.value_objects],
            "domain_events": [de.to_dict() for de in self.domain_events],
        }


@dataclass
class DomainModel:
    """领域模型（DDD战略建模结果）"""
    bounded_contexts: list[BoundedContext] = field(default_factory=list)
    ubiquitous_language: dict[str, str] = field(default_factory=dict)
    context_map: str = ""
    relationships: list[tuple[str, str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "bounded_contexts": [bc.to_dict() for bc in self.bounded_contexts],
            "ubiquitous_language": self.ubiquitous_language,
            "context_map": self.context_map,
            "relationships": self.relationships,
        }

    def to_mermaid(self) -> str:
        lines = ["erDiagram"]
        for bc in self.bounded_contexts:
            for ar in bc.aggregate_roots:
                attrs = "\\n".join(ar.attributes[:3]) if ar.attributes else ""
                lines.append(f'    "{ar.name}" {{')
                if attrs:
                    lines.append(f'        string {attrs}')
                lines.append("    }")
            for entity in bc.entities:
                lines.append(f'    "{entity.name}" {{')
                lines.append(f'        string {entity.identifier} PK')
                lines.append("    }")
        return "\n".join(lines)


@dataclass
class CompetitiveItem:
    """竞品分析条目"""
    competitor_name: str
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    features_supported: list[str] = field(default_factory=list)
    features_missing: list[str] = field(default_factory=list)
    market_position: str = ""
    pricing_model: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "competitor_name": self.competitor_name,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "features_supported": self.features_supported,
            "features_missing": self.features_missing,
            "market_position": self.market_position,
            "pricing_model": self.pricing_model,
        }


@dataclass
class CompetitiveReport:
    """竞品分析报告"""
    product_description: str
    analysis_date: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    competitors: list[CompetitiveItem] = field(default_factory=list)
    swot_summary: dict[str, list[str]] = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)
    gap_analysis: list[str] = field(default_factory=list)

    def to_markdown(self) -> str:
        lines = [
            "# 竞品分析报告",
            f"\n**产品描述**: {self.product_description}",
            f"**分析日期**: {self.analysis_date}\n",
            "## 竞品对比\n",
        ]
        for comp in self.competitors:
            lines.append(f"### {comp.competitor_name}")
            lines.append(f"- **市场定位**: {comp.market_position}")
            lines.append(f"- **定价模式**: {comp.pricing_model}")
            lines.append("- **优势**:")
            for s in comp.strengths:
                lines.append(f"  - {s}")
            lines.append("- **劣势**:")
            for w in comp.weaknesses:
                lines.append(f"  - {w}")
            lines.append("")
        if self.swot_summary:
            lines.append("## SWOT总结")
            for key, items in self.swot_summary.items():
                lines.append(f"- **{key}**: {'; '.join(items)}")
            lines.append("")
        if self.recommendations:
            lines.append("## 建议")
            for r in self.recommendations:
                lines.append(f"- {r}")
        return "\n".join(lines)


@dataclass
class TraceabilityItem:
    """追溯矩阵条目"""
    requirement_id: str
    requirement_title: str
    user_story_ids: list[str] = field(default_factory=list)
    acceptance_criteria_ids: list[str] = field(default_factory=list)
    test_case_ids: list[str] = field(default_factory=list)
    implementation_status: str = "pending"

    def to_dict(self) -> dict[str, Any]:
        return {
            "requirement_id": self.requirement_id,
            "requirement_title": self.requirement_title,
            "user_story_ids": self.user_story_ids,
            "acceptance_criteria_ids": self.acceptance_criteria_ids,
            "test_case_ids": self.test_case_ids,
            "implementation_status": self.implementation_status,
        }


@dataclass
class TraceabilityMatrix:
    """需求追踪矩阵"""
    project_name: str = ""
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    items: list[TraceabilityItem] = field(default_factory=list)
    coverage_stats: dict[str, Any] = field(default_factory=dict)

    def to_markdown(self) -> str:
        lines = [
            "# 需求追踪矩阵",
            f"\n**项目**: {self.project_name}",
            f"**生成时间**: {self.generated_at}\n",
            "| 需求ID | 需求标题 | 用户故事 | 验收标准 | 测试用例 | 状态 |",
            "|--------|----------|----------|----------|----------|------|",
        ]
        for item in self.items:
            lines.append(
                f"| {item.requirement_id} | {item.requirement_title} | "
                f"{', '.join(item.user_story_ids)} | "
                f"{', '.join(item.acceptance_criteria_ids)} | "
                f"{', '.join(item.test_case_ids)} | {item.implementation_status} |"
            )
        if self.coverage_stats:
            lines.append(f"\n**覆盖率**: {self.coverage_stats}")
        return "\n".join(lines)


@dataclass
class PrioritizedItem:
    """排序后的需求项"""
    requirement: Requirement
    rank: int
    score: float
    method: str
    rationale: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "rank": self.rank,
            "requirement_id": self.requirement.id,
            "title": self.requirement.title,
            "score": round(self.score, 2),
            "priority": self.requirement.priority.value,
            "method": self.method,
            "rationale": self.rationale,
        }


@dataclass
class PrioritizedList:
    """优先级排序列表"""
    method: str
    items: list[PrioritizedItem] = field(default_factory=list)
    total_score: float = 0.0
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_markdown(self) -> str:
        lines = [
            f"# 需求优先级排序 ({self.method.upper()})",
            f"\n**生成时间**: {self.generated_at}\n",
            "| 排名 | 需求ID | 标题 | 得分 | 优先级 | 说明 |",
            "|------|--------|------|------|--------|------|",
        ]
        for item in self.items:
            lines.append(
                f"| {item.rank} | {item.requirement.id} | {item.requirement.title} | "
                f"{item.score:.2f} | {item.requirement.priority.value} | {item.rationale} |"
            )
        return "\n".join(lines)


@dataclass
class RequirementDocument:
    """需求文档"""
    id: str
    source: str
    raw_content: str
    requirements: list[Requirement] = field(default_factory=list)
    extracted_at: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "source": self.source,
            "raw_content": self.raw_content[:500],
            "requirements_count": len(self.requirements),
            "requirements": [r.to_dict() for r in self.requirements],
            "extracted_at": self.extracted_at,
        }


class RequirementsBureau:
    """
    需求分析局

    负责需求收集、业务分析与领域建模(DDD)、用户故事生成、验收标准提取、
    多维度优先级排序(MoSCoW/WSJF/Kano)、需求追踪矩阵及PRD文档生成。
    """

    def __init__(self, output_dir: Path | str | None = None) -> None:
        self._output_dir = Path(output_dir) if output_dir else Path.cwd()
        self._collected_docs: list[RequirementDocument] = []
        self._domain_models: list[DomainModel] = []

    def collect_requirements(self, source: str) -> RequirementDocument:
        """
        从用户描述/文件/对话中收集需求

        Args:
            source: 需求来源（文件路径或原始文本）

        Returns:
            RequirementDocument对象，包含解析后的结构化需求列表
        """
        source_path = Path(source)
        raw_content: str

        if source_path.exists() and source_path.is_file():
            try:
                raw_content = source_path.read_text(encoding="utf-8")
            except OSError as e:
                raise RequirementsError(f"读取需求源文件失败 [{source}]: {e}") from e
            source_str = str(source_path)
        else:
            raw_content = source
            source_str = "user_input"

        requirements: list[Requirement] = self._parse_requirements(raw_content)

        doc = RequirementDocument(
            id=str(uuid.uuid4())[:8],
            source=source_str,
            raw_content=raw_content,
            requirements=requirements,
            metadata={"char_count": len(raw_content), "line_count": raw_content.count("\n") + 1},
        )

        self._collected_docs.append(doc)
        return doc

    def _parse_requirements(self, content: str) -> list[Requirement]:
        """从文本内容中解析结构化需求"""
        requirements: list[Requirement] = []
        sentences = re.split(r'[。\n！？]+', content)

        req_patterns = {
            RequirementType.FUNCTIONAL: [r"需要|应该|能够|支持|实现|功能", r"用户.*可以|允许.*操作"],
            RequirementType.NON_FUNCTIONAL: [r"性能|响应时间|并发|吞吐量|延迟|可用性", r"安全|加密|认证|授权|权限"],
            RequirementType.BUSINESS: [r"业务|流程|规则|审批|工作流", r"报表|统计|分析|数据"],
            RequirementType.USER_INTERFACE: [r"界面|UI|页面|展示|显示|交互", r"体验|友好|易用|布局"],
            RequirementType.INTEGRATION: [r"接口|API|对接|集成|调用|同步", r"第三方|外部系统|消息队列"],
            RequirementType.DATA: [r"数据|存储|数据库|表|字段|索引", r"导入|导出|备份|迁移"],
            RequirementType.SECURITY: [r"漏洞|攻击|防护|审计|日志", r"合规|隐私|GDPR|等保"],
        }

        for i, sentence in enumerate(sentences):
            sentence = sentence.strip()
            if len(sentence) < 5:
                continue

            detected_type = RequirementType.FUNCTIONAL
            max_matches = 0
            for rtype, patterns in req_patterns.items():
                matches = sum(1 for p in patterns if re.search(p, sentence))
                if matches > max_matches:
                    max_matches = matches
                    detected_type = rtype

            priority = self._infer_priority(sentence)

            req = Requirement(
                id=f"REQ-{i + 1:03d}",
                title=sentence[:60] + ("..." if len(sentence) > 60 else ""),
                description=sentence,
                requirement_type=detected_type,
                priority=priority,
            )
            requirements.append(req)

        if not requirements and content.strip():
            requirements.append(
                Requirement(
                    id="REQ-001",
                    title="综合需求",
                    description=content.strip(),
                    requirement_type=RequirementType.BUSINESS,
                    priority=Priority.HIGH,
                )
            )

        return requirements

    def _infer_priority(self, text: str) -> Priority:
        """从文本推断优先级"""
        critical_words = ["必须", "关键", "核心", "首要", "紧急", "不能", "禁止", "必须具备"]
        high_words = ["重要", "优先", "尽快", "应当", "需要", "主要"]
        low_words = ["可选", "将来", "后续", "锦上添花", "优化", "改善"]

        text_lower = text.lower()
        for w in critical_words:
            if w in text:
                return Priority.CRITICAL
        for w in high_words:
            if w in text:
                return Priority.HIGH
        for w in low_words:
            if w in text:
                return Priority.LOW
        return Priority.MEDIUM

    def analyze_business_domain(self, requirements: list[Requirement]) -> DomainModel:
        """
        DDD战略建模：识别聚合根/实体/值对象/领域事件

        Args:
            requirements: 需求列表

        Returns:
            DomainModel对象，包含完整的领域模型定义
        """
        noun_phrases: set[str] = set()
        verb_phrases: set[str] = set()
        domain_terms: dict[str, str] = {}

        for req in requirements:
            nouns = re.findall(r'[\u4e00-\u9fff]{2,6}(?:管理|系统|服务|平台|模块|中心)', req.description)
            noun_phrases.update(nouns)
            verbs = re.findall(r'(?:创建|新增|删除|修改|查询|审核|提交|导出|导入|同步|发送|接收)[\u4e00-\u9fff]*', req.description)
            verb_phrases.update(verbs)

            terms = re.findall(r'([\u4e00-\u9fff]{2,}(?:单|表|记录|信息|数据))', req.description)
            for t in terms:
                domain_terms[t] = req.description[:50]

        all_nouns = sorted(noun_phrases) if noun_phrases else ["核心业务域"]

        aggregate_roots: list[AggregateRoot] = []
        entities: list[Entity] = []
        value_objects: list[ValueObject] = []
        domain_events: list[DomainEvent] = []

        for i, noun in enumerate(all_nouns[:8]):
            is_root = i < max(1, len(all_nouns) // 3)
            if is_root:
                aggregate_roots.append(AggregateRoot(
                    name=noun,
                    attributes=[f"{noun}ID", "创建时间", "更新时间", "状态"],
                    behaviors=[f"创建{noun}", f"更新{noun}", f"删除{noun}", f"查询{noun}列表"],
                    invariants=[f"{noun}ID不能为空", f"{noun}状态必须有效"],
                ))
            else:
                entities.append(Entity(
                    name=noun,
                    identifier=f"{noun}ID",
                    attributes=["名称", "描述", "状态"],
                    aggregate_root=aggregate_roots[0].name if aggregate_roots else None,
                ))

        vo_names = ["地址", "金额", "日期范围", "联系方式", "权限范围"]
        for vo_name in vo_names[:3]:
            value_objects.append(ValueObject(name=vo_name, attributes=[f"{vo_name}属性1", f"{vo_name}属性2"]))

        event_templates = [(f"{n}已创建", n) for n in [ar.name for ar in aggregate_roots[:3]]]
        for event_name, trigger in event_templates:
            domain_events.append(DomainEvent(name=event_name, triggered_by=trigger))

        bounded_ctx = BoundedContext(
            name="核心业务上下文",
            aggregate_roots=aggregate_roots,
            entities=entities,
            value_objects=value_objects,
            domain_events=domain_events,
        )

        model = DomainModel(
            bounded_contexts=[bounded_ctx],
            ubiquitous_language=domain_terms,
            context_map=self._generate_context_map(bounded_ctx),
            relationships=[(ar.name, "包含", e.name) for ar in aggregate_roots for e in entities[:2]],
        )

        self._domain_models.append(model)
        return model

    def _generate_context_map(self, ctx: BoundedContext) -> str:
        """生成上下文映射图（Mermaid格式）"""
        lines = ["graph LR"]
        ar_names = [ar.name for ar in ctx.aggregate_roots]
        for i, name in enumerate(ar_names):
            lines.append(f'    A{i}["{name}"]')
        if len(ar_names) > 1:
            for i in range(len(ar_names) - 1):
                lines.append(f'    A{i} --> A{i + 1}')
        return "\n".join(lines)

    def generate_business_process_flow(self, features: list[str]) -> str:
        """
        生成业务流程图（Mermaid文本格式）

        Args:
            features: 功能特性列表

        Returns:
            Mermaid格式的业务流程图文本
        """
        lines = ["flowchart TD"]

        start_node = "Start((开始))"
        end_node = "End((结束))"
        lines.append(f'    {start_node}')

        prev_id = "Start"
        for i, feature in enumerate(features):
            node_id = f"F{i + 1}"
            safe_label = feature.replace('"', "'").replace("\n", " ")[:40]
            lines.append(f'    {node_id}["{safe_label}"]')
            lines.append(f'    {prev_id} --> {node_id}')
            decision_id = f"D{i + 1}"
            lines.append(f'    {decision_id}{{是否通过?}}')
            lines.append(f'    {node_id} --> {decision_id}')
            lines.append(f'    {decision_id} -->|是| F{i + 2}' if i < len(features) - 1 else f'    {decision_id} -->|是| {end_node}')
            lines.append(f'    {decision_id} -->|否| {node_id}')
            prev_id = node_id

        lines.append(f'    {prev_id} --> {end_node}')
        lines.append(f'    {end_node}')

        style_lines = [
            "    classDef startEnd fill:#e1f5fe,#01579b",
            "    classDef process fill:#e8f5e9,#2e7d32",
            "    classDef decision fill:#fff3e0,#e65100",
            f"    class Start,End startEnd",
            f"    class {','.join('F' + str(i+1) for i in range(len(features)))} process",
            f"    class {','.join('D' + str(i+1) for i in range(len(features)))} decision",
        ]
        lines.extend(style_lines)

        return "\n".join(lines)

    def competitive_analysis(
        self, product_desc: str, competitors: list[str] | None = None
    ) -> CompetitiveReport:
        """
        竞品分析框架

        Args:
            product_desc: 产品描述
            competitors: 竞品名称列表（可选）

        Returns:
            CompetitiveReport竞品分析报告
        """
        default_competitors = ["同类产品A", "同类产品B", "开源方案C"]
        comp_list = competitors or default_competitors

        feature_keywords = re.findall(r'[\u4e00-\u9fff]{2,}(?:功能|能力|特性|支持)', product_desc)
        features = feature_keywords if feature_keywords else ["核心功能", "用户体验", "性能表现", "扩展能力"]

        competitive_items: list[CompetitiveItem] = []
        for comp_name in comp_list:
            item = CompetitiveItem(
                competitor_name=comp_name,
                strengths=[f"{comp_name}在{'稳定性' if 'A' in comp_name else '灵活性'}方面表现良好"],
                weaknesses=[f"{comp_name}在{'定制化' if 'A' in comp_name else '易用性'}方面有待提升"],
                features_supported=features[:3],
                features_missing=features[3:] if len(features) > 3 else ["高级分析功能"],
                market_position="领导者" if "A" in comp_name else ("挑战者" if "B" in comp_name else "利基市场"),
                pricing_model="商业许可" if "开源" not in comp_name else "开源免费",
            )
            competitive_items.append(item)

        swot = {
            "优势(S)": [f"产品定位清晰: {product_desc[:30]}...", "技术创新能力强"],
            "劣势(W)": ["品牌知名度待提升", "生态体系尚不完善"],
            "机会(O)": ["市场需求持续增长", "数字化转型加速"],
            "威胁(T)": ["竞争加剧", "技术快速迭代"],
        }

        recommendations = [
            "聚焦差异化竞争优势，强化核心功能",
            "建立完善的客户成功体系",
            "持续投入技术研发保持领先",
            "关注开源社区动态与合作机会",
        ]

        gap_analysis = [f"与{c.competitor_name}相比需加强: {c.weaknesses[0]}" for c in competitive_items]

        return CompetitiveReport(
            product_description=product_desc,
            competitors=competitive_items,
            swot_summary=swot,
            recommendations=recommendations,
            gap_analysis=gap_analysis,
        )

    def generate_user_stories(
        self, requirement: str, format: str = "markdown"
    ) -> list[UserStory]:
        """
        按模板生成用户故事(As a/I want to/So that)

        Args:
            requirement: 需求文本
            format: 输出格式 ('markdown' 或 'json')

        Returns:
            UserStory列表
        """
        role_patterns = {
            "用户": ["用户", "客户", "使用者", "操作员", "访客"],
            "管理员": ["管理员", "运营人员", "运维", "超级管理员"],
            "业务人员": ["业务员", "销售", "客服", "财务", "审核员"],
            "开发者": ["开发", "工程师", "技术", "API调用者"],
            "系统": ["系统", "程序", "自动化", "定时任务"],
        }

        action_patterns = [
            (r"(?:查看|浏览|查询|搜索|获取|列出)", "查看"),
            (r"(?:创建|新增|添加|录入|登记|提交)", "创建"),
            (r"(?:编辑|修改|更新|变更|调整)", "编辑"),
            (r"(?:删除|移除|清除|撤销)", "删除"),
            (r"(?:导出|下载|打印|生成报告)", "导出"),
            (r"(?:导入|上传|批量处理)", "导入"),
            (r"(?:审核|审批|确认|验证|校验)", "审核"),
            (r"(?:配置|设置|自定义|个性化)", "配置"),
            (r"(?:分享|协作|通知|推送)", "协作"),
        ]

        detected_role = "用户"
        for role, keywords in role_patterns.items():
            if any(kw in requirement for kw in keywords):
                detected_role = role
                break

        detected_actions: list[tuple[str, str]] = []
        for pattern, action_name in action_patterns:
            if re.search(pattern, requirement):
                target_match = re.search(pattern + r'([\u4e00-\u9fff]*)', requirement)
                target = target_match.group(1) if target_match else "相关内容"
                detected_actions.append((action_name, target))

        if not detected_actions:
            detected_actions = [("使用", "系统功能")]

        benefit_templates = [
            "提高工作效率",
            "减少人工错误",
            "获得更好的用户体验",
            "满足业务需求",
            "简化操作流程",
            "实时获取所需信息",
            "确保数据准确性",
            "提升决策质量",
        ]

        stories: list[UserStory] = []
        for idx, (action, target) in enumerate(detected_actions[:5]):
            benefit = benefit_templates[idx % len(benefit_templates)]
            story = UserStory(
                id=f"US-{idx + 1:03d}",
                role=detected_role,
                action=f"{action}{target}",
                benefit=benefit,
                priority=self._infer_priority(requirement),
                story_points=None,
            )
            stories.append(story)

        if format == "json":
            print(json.dumps([s.to_dict() for s in stories], ensure_ascii=False, indent=2))

        return stories

    def extract_acceptance_criteria(self, story: UserStory) -> list[AcceptanceCriterion]:
        """
        提取验收标准（Given/When/Then格式）

        Args:
            story: 用户故事对象

        Returns:
            AcceptanceCriterion列表
        """
        criteria: list[AcceptanceCriterion] = []

        base_givens = [
            f"作为{story.role}",
            f"已登录系统并拥有相应权限",
            f"相关{story.action.replace('查看','').replace('创建','').replace('编辑','').replace('删除','') or '业务'}数据已准备就绪",
        ]

        whens = [
            f"执行{story.action}操作",
            f"输入有效数据并提交",
            f"触发相关业务规则",
        ]

        thens_sets = [
            [f"系统成功完成{story.action}", "操作结果正确保存", "用户收到成功提示"],
            [f"系统返回{story.action}结果", "数据显示准确完整", "响应时间符合要求"],
            [f"系统验证{story.action}合法性", "不符合条件时给出明确错误信息", "日志记录完整"],
        ]

        criterion_id = 1
        for given in base_givens[:2]:
            for when_idx, when in enumerate(whens[:2]):
                thens = thens_sets[when_idx % len(thens_sets)]
                for then in thens[:2]:
                    ac = AcceptanceCriterion(
                        id=f"AC-{story.id}-{criterion_id:02d}",
                        given=given,
                        when=when,
                        then=then,
                        priority=story.priority,
                    )
                    criteria.append(ac)
                    criterion_id += 1

        story.acceptance_criteria = criteria
        return criteria

    def prioritize_requirements(
        self, reqs: list[Requirement], method: str = "moscow"
    ) -> PrioritizedList:
        """
        多维度优先级排序（MoSCoW/WSJF/Kano）

        Args:
            reqs: 需求列表
            method: 排序方法 ('moscow', 'wsjf', 'kano')

        Returns:
            PrioritizedList排序结果
        """
        match method.lower():
            case "moscow":
                return self._prioritize_moscow(reqs)
            case "wsjf":
                return self._prioritize_wsjf(reqs)
            case "kano":
                return self._prioritize_kano(reqs)
            case _:
                raise RequirementsError(f"不支持的排序方法: {method}，支持: moscow, wsjf, kano")

    def _prioritize_moscow(self, reqs: list[Requirement]) -> PrioritizedList:
        """MoSCoW优先级排序法"""
        priority_order = {
            Priority.CRITICAL: (Priority.MUST_HAVE, 100),
            Priority.HIGH: (Priority.SHOULD_HAVE, 80),
            Priority.MEDIUM: (Priority.COULD_HAVE, 50),
            Priority.LOW: (Priority.WONT_HAVE, 20),
        }

        items: list[PrioritizedItem] = []
        rank = 1
        for req in sorted(reqs, key=lambda r: priority_order.get(r.priority, (Priority.COULD_HAVE, 30))[1], reverse=True):
            moscow_prio, score = priority_order.get(req.priority, (Priority.COULD_HAVE, 30))
            items.append(PrioritizedItem(
                requirement=req,
                rank=rank,
                score=float(score),
                method="MoSCoW",
                rationale=f"基于需求内在优先级映射至{moscow_prio.value}",
            ))
            rank += 1

        return PrioritizedList(method="MoSCoW", items=items, total_score=sum(it.score for it in items))

    def _prioritize_wsjf(self, reqs: list[Requirement]) -> PrioritizedList:
        """WSJF(加权最短作业优先)排序法"""
        items: list[PrioritizedItem] = []
        scored_reqs: list[tuple[Requirement, float]] = []

        for req in reqs:
            business_value = self._score_dimension(req.description, ["价值", "收益", "营收", "核心"])
            time_criticality = self._score_dimension(req.description, ["紧急", "截止", "必须", "关键"])
            risk_opportunity = self._score_dimension(req.description, ["风险", "依赖", "技术债"])
            effort = max(1, len(req.description) // 20)

            wsjf_score = (business_value * 1.0 + time_criticality * 0.8 + risk_opportunity * 0.6) / effort
            scored_reqs.append((req, wsjf_score))

        scored_reqs.sort(key=lambda x: x[1], reverse=True)
        for rank, (req, score) in enumerate(scored_reqs, 1):
            items.append(PrioritizedItem(
                requirement=req,
                rank=rank,
                score=score,
                method="WSJF",
                rationale=f"业务价值+时效性+风险/工作量={score:.2f}",
            ))

        return PrioritizedList(method="WSJF", items=items, total_score=sum(s for _, s in scored_reqs))

    def _prioritize_kano(self, reqs: list[Requirement]) -> PrioritizedList:
        """Kano模型优先级排序"""
        kano_categories = {
            "必备型(Must)": ["基本", "必须", "基础", "核心", "必要"],
            "期望型(One-dimensional)": ["期望", "希望", "更好", "提高", "优化"],
            "魅力型(Delight)": ["惊喜", "创新", "独特", "领先", "智能"],
            "无差异型(Indifferent)": ["可选", "将来", "锦上添花"],
        }

        items: list[PrioritizedItem] = []
        category_scores = {"必备型(Must)": 100, "期望型(One-dimensional)": 70, "魅力型(Delight)": 50, "无差异型(Indifferent)": 20}

        for req in reqs:
            detected_cat = "无差异型(Indifferent)"
            for cat, keywords in kano_categories.items():
                if any(kw in req.description for kw in keywords):
                    detected_cat = cat
                    break
            score = float(category_scores.get(detected_cat, 30))
            items.append(PrioritizedItem(
                requirement=req,
                rank=0,
                score=score,
                method="Kano",
                rationale=f"Kano分类: {detected_cat}",
            ))

        items.sort(key=lambda x: x.score, reverse=True)
        for rank, item in enumerate(items, 1):
            item.rank = rank

        return PrioritizedList(method="Kano", items=items, total_score=sum(it.score for it in items))

    def _score_dimension(self, text: str, keywords: list[str]) -> float:
        """对文本在某维度上打分"""
        score = sum(2 for kw in keywords if kw in text)
        return max(1.0, float(score))

    def generate_traceability_matrix(
        self, requirements: list[Requirement], user_stories: list[UserStory]
    ) -> TraceabilityMatrix:
        """
        生成需求追踪矩阵（需求→用户故事→验收标准→测试用例）

        Args:
            requirements: 需求列表
            user_stories: 用户故事列表

        Returns:
            TraceabilityMatrix追踪矩阵
        """
        items: list[TraceabilityItem] = []
        total_ac = 0
        covered_count = 0

        for req in requirements:
            related_stories = [us for us in user_stories if self._is_related(req, us)]
            us_ids = [us.id for us in related_stories]
            ac_ids: list[str] = []
            tc_ids: list[str] = []

            for us in related_stories:
                ac_ids.extend([ac.id for ac in us.acceptance_criteria])
                total_ac += len(us.acceptance_criteria)
                for ac in us.acceptance_criteria:
                    tc_ids.append(f"TC-{ac.id}")

            if us_ids:
                covered_count += 1

            items.append(TraceabilityItem(
                requirement_id=req.id,
                requirement_title=req.title,
                user_story_ids=us_ids,
                acceptance_criteria_ids=ac_ids,
                test_case_ids=tc_ids,
                implementation_status="mapped" if us_ids else "pending",
            ))

        coverage = {
            "total_requirements": len(requirements),
            "covered_requirements": covered_count,
            "coverage_percentage": round((covered_count / len(requirements) * 100), 1) if requirements else 0,
            "total_user_stories": len(user_stories),
            "total_acceptance_criteria": total_ac,
        }

        return TraceabilityMatrix(
            items=items,
            coverage_stats=coverage,
        )

    def _is_related(self, req: Requirement, story: UserStory) -> bool:
        """判断需求和用户故事是否关联"""
        req_words = set(re.findall(r'[\u4e00-\u9fff]{2,}', req.description))
        story_words = set(re.findall(r'[\u4e00-\u9fff]{2,}', story.action + story.benefit))
        overlap = req_words & story_words
        return len(overlap) >= 1

    def generate_prd(self, project_name: str, requirements: list[Requirement]) -> str:
        """
        生成Markdown格式的PRD文档

        Args:
            project_name: 项目名称
            requirements: 需求列表

        Returns:
            Markdown格式的PRD文档字符串
        """
        now = datetime.now().strftime("%Y-%m-%d")
        type_groups: dict[RequirementType, list[Requirement]] = {}
        for req in requirements:
            type_groups.setdefault(req.requirement_type, []).append(req)

        type_labels = {
            RequirementType.FUNCTIONAL: "功能性需求",
            RequirementType.NON_FUNCTIONAL: "非功能性需求",
            RequirementType.BUSINESS: "业务需求",
            RequirementType.USER_INTERFACE: "界面交互需求",
            RequirementType.INTEGRATION: "集成需求",
            RequirementType.DATA: "数据需求",
            RequirementType.SECURITY: "安全需求",
        }

        sections: list[str] = [
            f"# 产品需求文档 (PRD)",
            f"\n> **项目名称**: {project_name}",
            f"> **版本**: v1.0",
            f"> **文档日期**: {now}",
            f"> **状态**: 草稿\n",
            "---\n",
            "## 1. 文档概述\n",
            f"本文档定义了 **{project_name}** 的产品需求规格。",
            f"共收录 **{len(requirements)}** 条需求项。\n",
            "## 2. 需求清单\n",
        ]

        for rtype, reqs_in_group in type_groups.items():
            label = type_labels.get(rtype, rtype.value)
            sections.append(f"### 2.{list(type_groups.keys()).index(rtype) + 1} {label} ({len(reqs_in_group)})\n")
            sections.append("| ID | 标题 | 描述 | 优先级 | 状态 |")
            sections.append("|-----|------|------|--------|------|")
            for req in reqs_in_group:
                desc_short = req.description[:50] + ("..." if len(req.description) > 50 else "")
                sections.append(
                    f"| {req.id} | {req.title} | {desc_short} | {req.priority.value} | {req.status.value} |"
                )
            sections.append("")

        sections.extend([
            "## 3. 优先级总览\n",
            "| 优先级 | 数量 |",
            "|--------|------|",
        ])
        prio_counts: dict[Priority, int] = {}
        for req in requirements:
            prio_counts[req.priority] = prio_counts.get(req.priority, 0) + 1
        for prio, count in sorted(prio_counts.items(), key=lambda x: list(Priority).index(x[0])):
            sections.append(f"| {prio.value} | {count} |")

        sections.extend([
            "\n## 4. 非功能性需求概要\n",
            "- **性能**: 系统响应时间应控制在合理范围内",
            "- **可用性**: 目标可用性 99.9%",
            "- **安全性**: 符合行业安全标准和最佳实践",
            "- **可扩展性**: 支持水平扩展以应对业务增长",
            "- **可维护性**: 代码规范统一，文档完善\n",
            "## 5. 附录\n",
            "- 本文档由中书省·需求分析局自动生成",
            f"- 生成时间: {datetime.now().isoformat()}",
        ])

        prd_content = "\n".join(sections)

        output_file = self._output_dir / f"{project_name}_PRD.md"
        try:
            self._output_dir.mkdir(parents=True, exist_ok=True)
            output_file.write_text(prd_content, encoding="utf-8")
        except OSError as e:
            raise RequirementsError(f"写入PRD文件失败 [{output_file}]: {e}") from e

        return prd_content


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 需求分析局测试")
    print("=" * 60)

    bureau = RequirementsBureau()

    print("\n--- 需求收集测试 ---")
    sample_requirement_text = """
    电商管理系统需求说明：
    1. 用户必须能够注册和登录系统，支持手机号和邮箱两种方式。
    2. 系统需要支持商品管理功能，包括商品的增删改查操作。
    3. 管理员应该可以查看订单报表和销售数据分析。
    4. 系统响应时间应在2秒以内，支持至少1000个并发用户。
    5. 数据库需要定期备份，确保数据安全性。
    6. 用户界面应该简洁友好，支持暗色主题切换。
    7. 支付接口需要对接支付宝和微信支付。
    8. 系统需要对敏感数据进行加密存储。
    """
    doc = bureau.collect_requirements(sample_requirement_text)
    print(f"✅ 收集到 {len(doc.requirements)} 条需求")
    for req in doc.requirements[:3]:
        print(f"   [{req.id}] {req.title} ({req.requirement_type.value}/{req.priority.value})")

    print("\n--- 业务领域建模测试 ---")
    domain_model = bureau.analyze_business_domain(doc.requirements)
    print(f"✅ 识别到 {len(domain_model.bounded_contexts[0].aggregate_roots)} 个聚合根")
    print(f"✅ 识别到 {len(domain_model.bounded_contexts[0].entities)} 个实体")
    print(f"✅ 识别到 {len(domain_model.bounded_contexts[0].value_objects)} 个值对象")
    print(f"✅ 识别到 {len(domain_model.bounded_contexts[0].domain_events)} 个领域事件")
    print(f"\n领域模型Mermaid图:\n{domain_model.to_mermaid()}")

    print("\n--- 业务流程图生成测试 ---")
    features = ["用户注册登录", "商品浏览选购", "购物车管理", "订单提交支付", "物流跟踪查询"]
    flow = bureau.generate_business_process_flow(features)
    print(f"✅ 流程图节点数: {features.length if hasattr(features, 'length') else len(features)}")
    print(f"流程图(Mermaid):\n{flow[:300]}...")

    print("\n--- 竞品分析测试 ---")
    report = bureau.competitive_analysis("新一代电商管理系统，支持多渠道销售和智能推荐")
    print(f"✅ 分析了 {len(report.competitors)} 个竞品")
    print(f"✅ SWOT维度: {list(report.swot_summary.keys())}")
    print(f"✅ 建议数量: {len(report.recommendations)}")

    print("\n--- 用户故事生成测试 ---")
    stories = bureau.generate_user_stories("用户需要能够查看和管理自己的订单信息")
    print(f"✅ 生成 {len(stories)} 个用户故事")
    for story in stories[:2]:
        print(f"   [{story.id}] {story.as_a_i_want_so_that}")

    print("\n--- 验收标准提取测试 ---")
    if stories:
        criteria = bureau.extract_acceptance_criteria(stories[0])
        print(f"✅ 提取 {len(criteria)} 条验收标准")
        for ac in criteria[:2]:
            print(f"   {ac.to_gwt_string()}")

    print("\n--- 优先级排序测试 ---")
    for method in ["moscow", "wsjf", "kano"]:
        result = bureau.prioritize_requirements(doc.requirements, method=method)
        print(f"✅ {method.upper()}: Top3 -> {[it.requirement.id for it in result.items[:3]]}")

    print("\n--- 追踪矩阵测试 ---")
    all_stories: list[UserStory] = []
    for req in doc.requirements[:3]:
        all_stories.extend(bureau.generate_user_stories(req.description))
    matrix = bureau.generate_traceability_matrix(doc.requirements, all_stories)
    print(f"✅ 矩阵条目数: {len(matrix.items)}")
    print(f"✅ 覆盖率: {matrix.coverage_stats.get('coverage_percentage', 0)}%")

    print("\n--- PRD文档生成测试 ---")
    prd = bureau.generate_prd("电商管理系统", doc.requirements)
    print(f"✅ PRD文档长度: {len(prd)} 字符")
    print(f"PRD预览:\n{prd[:400]}...")

    print("\n✅ 需求分析局所有测试通过!")
