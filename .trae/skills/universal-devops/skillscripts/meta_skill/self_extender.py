"""
技能自扩展建议器 - 识别能力缺口并建议新技能方向
提供缺口分析、新技能提案、能力映射、集成规划四大能力
"""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


class ExtensionError(Exception):
    """自扩展异常"""
    pass


class GapSeverity(str, Enum):
    CRITICAL = "critical"
    SIGNIFICANT = "significant"
    MODERATE = "moderate"
    MINOR = "minor"


@dataclass
class GapRecord:
    """能力缺口记录"""
    gap_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    category: str = ""
    description: str = ""
    severity: GapSeverity = GapSeverity.MODERATE
    evidence: list[str] = field(default_factory=list)
    affected_users: int = 0
    existing_coverage: float = 0.0
    suggested_solution: str = ""
    confidence: float = 0.5

    def to_dict(self) -> dict[str, Any]:
        return {
            "gap_id": self.gap_id,
            "category": self.category,
            "description": self.description,
            "severity": self.severity.value,
            "evidence": self.evidence,
            "affected_users": self.affected_users,
            "existing_coverage": round(self.existing_coverage, 3),
            "suggested_solution": self.suggested_solution,
            "confidence": round(self.confidence, 2),
        }


@dataclass
class NewSkillSuggestion:
    """新技能建议"""
    suggestion_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    proposed_department: str = ""
    province: str = "shangshusheng"
    description: str = ""
    triggers: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    rationale: str = ""
    estimated_complexity: str = "medium"
    priority: str = "medium"
    source_gap_ids: list[str] = field(default_factory=list)
    similarity_to_existing: float = 0.0
    value_proposition: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "suggestion_id": self.suggestion_id,
            "name": self.name,
            "proposed_department": self.proposed_department,
            "province": self.province,
            "description": self.description,
            "triggers": self.triggers,
            "dependencies": self.dependencies,
            "rationale": self.rationale,
            "estimated_complexity": self.estimated_complexity,
            "priority": self.priority,
            "source_gap_ids": self.source_gap_ids,
            "similarity_to_existing": round(self.similarity_to_existing, 3),
            "value_proposition": self.value_proposition,
        }


@dataclass
class ExtensionProposal:
    """完整扩展提案"""
    proposal_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    total_gaps: int = 0
    critical_gaps: int = 0
    new_skill_suggestions: list[NewSkillSuggestion] = field(default_factory=list)
    gaps: list[GapRecord] = field(default_factory=list)
    integration_roadmap: list[dict[str, Any]] = field(default_factory=list)
    summary: str = ""
    risk_assessment: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "generated_at": self.generated_at,
            "total_gaps": self.total_gaps,
            "critical_gaps": self.critical_gaps,
            "new_skill_suggestions": [s.to_dict() for s in self.new_skill_suggestions],
            "gaps": [g.to_dict() for g in self.gaps],
            "integration_roadmap": self.integration_roadmap,
            "summary": self.summary,
            "risk_assessment": self.risk_assessment,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


PROVINCE_DEPT_MAP: dict[str, dict[str, Any]] = {
    "zhongshusheng": {
        "label": "中书省",
        "departments": ["requirements_bureau", "architecture_bureau", "standards_bureau", "review_bureau"],
        "focus": "顶层规划与标准制定",
        "capacity_keywords": ["需求", "架构", "标准", "审查", "设计", "规划"],
    },
    "menxiasheng": {
        "label": "门下省",
        "departments": ["code_review_bureau", "testing_bureau", "quality_monitor_bureau", "compliance_bureau"],
        "focus": "质量保障与合规检查",
        "capacity_keywords": ["审查", "测试", "质量", "合规", "安全", "审计"],
    },
    "shangshusheng": {
        "label": "尚书省",
        "departments": [
            "libu", "hubu", "libu2",
            "bingbu", "gongbu", "xingbu",
        ],
        "focus": "执行落地与技术实现",
        "capacity_keywords": [
            "调度", "环境", "依赖", "基础设施", "文档", "模板",
            "知识库", "标准化", "TDD", "测试框架", "覆盖率",
            "代码生成", "UI/UX", "数据库", "API", "Bug修复",
            "重构", "进化", "版本控制",
        ],
    },
}


class GapAnalyzer:
    """
    缺口识别器

    分析用户需求与现有32个子技能之间的能力差距，
    基于使用模式、反馈数据和领域趋势识别缺口。
    """

    GAP_CATEGORIES: list[tuple[str, list[str], str]] = [
        (
            "devops_pipeline",
            ["CI/CD", "流水线", "发布", "回滚", "蓝绿部署", "金丝雀发布"],
            "DevOps流水线全流程自动化能力"
        ),
        (
            "observability",
            ["监控", "告警", "日志", "链路追踪", "指标", "APM"],
            "可观测性体系建设能力"
        ),
        (
            "security_hardening",
            ["渗透测试", "漏洞扫描", "SAST", "DAST", "密钥管理", "零信任"],
            "安全加固与纵深防御能力"
        ),
        (
            "ai_integration",
            ["AI辅助", "LLM", "智能编码", "代码补全", "AI审查", "生成式"],
            "AI/ML工具链集成能力"
        ),
        (
            "cloud_native",
            ["微服务", "服务网格", "容器编排", "Serverless", "事件驱动", "云原生"],
            "云原生架构演进能力"
        ),
        (
            "data_engineering",
            ["数据管道", "ETL", "数据湖", "数仓", "实时计算", "流处理"],
            "数据工程与治理能力"
        ),
        (
            "collaboration",
            ["协作", "Code Review", "PR", "Merge Request", "代码评审流", "团队协作"],
            "团队协作工作流优化能力"
        ),
        (
            "performance_engineering",
            ["性能调优", "压测", "负载测试", "容量规划", "性能基线", "剖析"],
            "性能工程与容量规划能力"
        ),
        (
            "legacy_modernization",
            ["遗留系统", "迁移", "重构策略", "技术债务", "现代化", "遗留改造"],
            "遗留系统现代化能力"
        ),
        (
            "compliance_automation",
            ["合规自动化", "审计跟踪", "变更管理", "配置 drift", "策略即代码", "Governance"],
            "合规自动化与治理能力"
        ),
    ]

    def __init__(self) -> None:
        self._usage_patterns: list[dict[str, Any]] = []
        self._feedback_data: list[dict[str, Any]] = []
        self._unmatched_queries: list[dict[str, Any]] = []

    def add_usage_pattern(
        self, query: str, matched_skills: list[str], confidence: float = 1.0
    ) -> None:
        """添加一条使用模式"""
        self._usage_patterns.append({
            "query": query[:300],
            "matched_skills": matched_skills,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat(),
        })

    def add_unmatched_query(self, query: str, reason: str = "") -> None:
        """添加未匹配的查询（潜在缺口信号）"""
        self._unmatched_queries.append({
            "query": query[:300],
            "reason": reason,
            "timestamp": datetime.now().isoformat(),
        })

    def add_feedback(self, skill_name: str, rating: int, comment: str = "") -> None:
        """添加用户反馈"""
        self._feedback_data.append({
            "skill_name": skill_name,
            "rating": max(1, min(5, rating)),
            "comment": comment[:500],
            "timestamp": datetime.now().isoformat(),
        })

    def load_patterns(self, patterns: list[dict[str, Any]]) -> None:
        """批量加载使用模式"""
        self._usage_patterns.extend(patterns)

    def analyze_gaps(
        self, existing_skills: list[dict[str, Any]]
    ) -> tuple[list[GapRecord], dict[str, Any]]:
        """
        执行全面的缺口分析

        Args:
            existing_skills: 现有子技能信息列表

        Returns:
            (缺口列表, 汇总统计)
        """
        existing_triggers: set[str] = set()
        existing_descriptions: str = ""
        for sk in existing_skills:
            existing_triggers.update(t.lower() for t in sk.get("triggers", []))
            existing_descriptions += " " + sk.get("description", "")

        gaps: list[GapRecord] = []
        unmatched_by_category: dict[str, list[str]] = {}

        for category, keywords, desc in self.GAP_CATEGORIES:
            matched_kw: list[str] = []
            unmatched_kw: list[str] = []

            for kw in keywords:
                kw_lower = kw.lower()
                if any(kw_lower in t or t in kw_lower for t in existing_triggers):
                    matched_kw.append(kw)
                else:
                    unmatched_kw.append(kw)

            coverage = len(matched_kw) / max(len(keywords), 1)
            related_unmatched = [
                u["query"] for u in self._unmatched_queries
                if any(kw.lower() in u["query"].lower() for kw in keywords)
            ]

            low_rating_skills = [
                f["skill_name"] for f in self._feedback_data
                if f["rating"] <= 2 and any(
                    kw.lower() in (f.get("comment") or "").lower()
                    for kw in keywords
                )
            ]

            if coverage < 0.6 or len(related_unmatched) > 2 or len(low_rating_skills) > 0:
                severity = GapSeverity.MINOR
                if coverage < 0.2 and len(related_unmatched) > 5:
                    severity = GapSeverity.CRITICAL
                elif coverage < 0.4 or len(related_unmatched) > 3:
                    severity = GapSeverity.SIGNIFICANT
                elif coverage < 0.6 or len(related_unmatched) > 1:
                    severity = GapSeverity.MODERATE

                evidence: list[str] = []
                if unmatched_kw:
                    evidence.append(f"未覆盖关键词: {', '.join(unmatched_kw)}")
                if related_unmatched:
                    evidence.append(f"相关未匹配查询: {len(related_unmatched)} 条")
                if low_rating_skills:
                    evidence.append(f"低评分关联技能: {', '.join(low_rating_skills[:3])}")
                if coverage < 1.0:
                    evidence.append(f"覆盖度仅 {coverage:.0%}")

                gaps.append(GapRecord(
                    category=category,
                    description=desc,
                    severity=severity,
                    evidence=evidence,
                    affected_users=len(related_unmatched),
                    existing_coverage=coverage,
                    suggested_solution=f"考虑新增或强化{desc}相关的子技能",
                    confidence=min(coverage * 0.3 + len(related_unmatched) * 0.1 + 0.4, 0.95),
                ))

                unmatched_by_category[category] = related_unmatched

        summary = {
            "total_categories_analyzed": len(self.GAP_CATEGORIES),
            "gaps_found": len(gaps),
            "by_severity": {
                s.value: sum(1 for g in gaps if g.severity == s)
                for s in GapSeverity
            },
            "total_unmatched_queries": len(self._unmatched_queries),
            "total_feedback_records": len(self._feedback_data),
            "avg_confidence": round(
                sum(g.confidence for g in gaps) / max(len(gaps), 1), 2
            ) if gaps else 0,
        }

        gaps.sort(key=lambda g: (
            0 if g.severity == GapSeverity.CRITICAL else
            1 if g.severity == GapSeverity.SIGNIFICANT else
            2 if g.severity == GapSeverity.MODERATE else 3,
            -g.confidence,
        ))

        return gaps, summary


class NewSkillProposer:
    """
    新技能建议生成器

    基于缺口分析结果提出具体的新子技能方案，
    包含名称、描述、触发词、依赖关系等完整定义。
    """

    SKILL_TEMPLATES: dict[str, dict[str, Any]] = {
        "ci_cd_si": {
            "name_template": "{prefix}_pipeline_si",
            "department": "hubu",
            "default_triggers": ["CI/CD", "流水线", "持续集成", "持续部署", "构建", "发布"],
            "base_description": "CI/CD流水线管理 - 负责构建、测试、部署的端到端自动化",
            "dependencies": ["environment_config_si", "infrastructure_si"],
        },
        "observability_si": {
            "name_template": "{prefix}_observability_si",
            "department": "hubu",
            "default_triggers": ["监控", "告警", "日志", "metrics", "trace", "APM"],
            "base_description": "可观测性管理 - 统一监控、日志和分布式追踪体系",
            "dependencies": ["infrastructure_si", "resource_optimization_si"],
        },
        "security_scan_si": {
            "name_template": "{prefix}_security_si",
            "department": "menxiasheng",
            "default_triggers": ["安全扫描", "漏洞检测", "SAST", "DAST", "渗透", "密钥"],
            "base_description": "安全扫描与防护 - 静态/动态分析及安全加固",
            "dependencies": ["compliance_bureau", "code_review_bureau"],
        },
        "ai_copilot_si": {
            "name_template": "{prefix}_ai_si",
            "department": "libu2",
            "default_triggers": ["AI辅助", "智能编码", "LLM", "代码生成", "AI Review", "Copilot"],
            "base_description": "AI编程助手 - 集成大语言模型提升开发效率",
            "dependencies": ["code_generation_si", "documentation_si"],
        },
        "microservice_si": {
            "name_template": "{prefix}_microservice_si",
            "department": "gongbu",
            "default_triggers": ["微服务", "服务拆分", "服务网格", "API网关", "熔断", "降级"],
            "base_description": "微服务架构 - 服务拆分设计与治理",
            "dependencies": ["api_design_si", "architecture_bureau"],
        },
        "performance_test_si": {
            "name_template": "{prefix}_perf_test_si",
            "department": "bingbu",
            "default_triggers": ["压测", "负载测试", "性能基准", "容量规划", "JMeter", "k6"],
            "base_description": "性能测试 - 压力测试与容量评估",
            "dependencies": ["regression_testing_si", "infrastructure_si"],
        },
        "migration_si": {
            "name_template": "{prefix}_migration_si",
            "department": "xingbu",
            "default_triggers": ["迁移", "升级", "版本迁移", "数据迁移", "平台迁移", "现代化"],
            "base_description": "系统迁移 - 遗留系统现代化与平滑迁移",
            "dependencies": ["version_control_si", "architecture_bureau"],
        },
        "collaboration_si": {
            "name_template": "{prefix}_collab_si",
            "department": "libu",
            "default_triggers": ["协作", "PR", "Code Review", "Merge Request", "工作流", "审批"],
            "base_description": "协作工作流 - 代码评审与合并流程管理",
            "dependencies": ["coordination_si", "code_review_bureau"],
        },
    }

    def __init__(self) -> None:
        self._existing_names: set[str] = set()

    def set_existing_skills(self, skill_names: list[str]) -> None:
        """设置已有技能名集合，避免重复建议"""
        self._existing_names = set(skill_names)

    def propose_skills(
        self, gaps: list[GapRecord], existing_skills: list[dict[str, Any]]
    ) -> list[NewSkillSuggestion]:
        """
        基于缺口列表生成新技能建议

        Args:
            gaps: 缺口记录列表
            existing_skills: 现有技能信息

        Returns:
            新技能建议列表
        """
        suggestions: list[NewSkillSuggestion] = []
        existing_names_set = self._existing_names or {s.get("name", "") for s in existing_skills}

        for gap in gaps:
            if gap.confidence < 0.35:
                continue

            template_key = self._match_template(gap.category)
            if not template_key:
                template_key = "ci_cd_si"

            template = self.SKILL_TEMPLATES[template_key]
            prefix = gap.category.split("_")[0]

            base_name = template["name_template"].format(prefix=prefix)
            candidate_name = base_name
            counter = 1
            while candidate_name in existing_names_set or any(s.name == candidate_name for s in suggestions):
                candidate_name = f"{base_name}_{counter}"
                counter += 1

            custom_triggers = self._derive_triggers_from_gap(gap)
            merged_triggers = list(dict.fromkeys(template["default_triggers"] + custom_triggers))

            value_props = self._generate_value_proposition(gap, template)

            suggestions.append(NewSkillSuggestion(
                name=candidate_name,
                proposed_department=template["department"],
                province=self._dept_to_province(template["department"]),
                description=self._craft_description(gap, template),
                triggers=merged_triggers,
                dependencies=list(template["dependencies"]),
                rationale=gap.description + "; " + "; ".join(gap.evidence[:2]),
                estimated_complexity=self._estimate_complexity(gap),
                priority=gap.severity.value,
                source_gap_ids=[gap.gap_id],
                similarity_to_existing=self._calc_similarity(candidate_name, existing_skills),
                value_proposition=value_props,
            ))

        suggestions.sort(key=lambda s: (
            0 if s.priority == "critical" else
            1 if s.priority == "significant" else
            2 if s.priority == "moderate" else 3,
            -s.confidence if hasattr(s, 'confidence') else 0,
        ))

        return suggestions

    def _match_template(self, category: str) -> str | None:
        """根据缺口类别匹配合适的模板"""
        mapping = {
            "devops_pipeline": "ci_cd_si",
            "observability": "observability_si",
            "security_hardening": "security_scan_si",
            "ai_integration": "ai_copilot_si",
            "cloud_native": "microservice_si",
            "performance_engineering": "performance_test_si",
            "legacy_modernization": "migration_si",
            "collaboration": "collaboration_si",
        }
        return mapping.get(category)

    def _dept_to_province(self, department: str) -> str:
        """根据部门推断所属省"""
        dept_province_map = {
            "requirements_bureau": "zhongshusheng",
            "architecture_bureau": "zhongshusheng",
            "standards_bureau": "zhongshusheng",
            "review_bureau": "zhongshusheng",
            "code_review_bureau": "menxiasheng",
            "testing_bureau": "menxiasheng",
            "quality_monitor_bureau": "menxiasheng",
            "compliance_bureau": "menxiasheng",
        }
        if department in dept_province_map:
            return dept_province_map[department]
        return "shangshusheng"

    def _derive_triggers_from_gap(self, gap: GapRecord) -> list[str]:
        """从缺口证据中提取触发词候选"""
        import re
        triggers: list[str] = []
        for ev in gap.evidence:
            words = re.findall(r'[\u4e00-\u9fff]{2,6}|[A-Za-z]{3,}', ev)
            triggers.extend(w for w in words if len(w) >= 2)
        return list(dict.fromkeys(triggers))[:10]

    def _craft_description(
        self, gap: GapRecord, template: dict[str, Any]
    ) -> str:
        """为建议的新技能编写描述"""
        base = template["base_description"]
        if gap.severity in (GapSeverity.CRITICAL, GapSeverity.SIGNIFICANT):
            base += "（高优先级：基于明确的用户需求缺口）"
        return base

    def _estimate_complexity(self, gap: GapRecord) -> str:
        """估算实现复杂度"""
        match gap.severity:
            case GapSeverity.CRITICAL:
                return "large"
            case GapSeverity.SIGNIFICANT:
                return "medium"
            case GapSeverity.MODERATE:
                return "small"
            case _:
                return "small"

    def _calc_similarity(
        self, new_name: str, existing_skills: list[dict[str, Any]]
    ) -> float:
        """计算与现有技能的相似度"""
        new_lower = new_name.lower().replace("_si", "").replace("_", "")
        max_sim: float = 0.0
        for sk in existing_skills:
            exist_lower = sk.get("name", "").lower().replace("_si", "").replace("_", "")
            common = set(new_lower) & set(exist_lower)
            sim = len(common) / max(len(set(new_lower) | set(exist_lower)), 1)
            max_sim = max(max_sim, sim)
        return max_sim

    def _generate_value_proposition(
        self, gap: GapRecord, template: dict[str, Any]
    ) -> str:
        """生成价值主张"""
        parts: list[str] = []
        parts.append(f"填补「{gap.category}」领域的空白")
        if gap.affected_users > 3:
            parts.append(f"响应 {gap.affected_users} 个未满足的用户请求")
        if gap.existing_coverage < 0.3:
            parts.append("当前覆盖度不足30%，新增后可显著提升")
        return "；".join(parts)


class CapabilityMapper:
    """
    能力映射器

    将新的用户需求映射到现有的二十四司架构，
    或建议新增司/局来承载新能力。
    """

    def __init__(self) -> None:
        self._province_structure: dict[str, Any] = dict(PROVINCE_DEPT_MAP)

    def map_capability(
        self, requirement: str, existing_skills: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        将一个需求映射到最合适的承载位置

        Args:
            requirement: 用户需求描述
            existing_skills: 现有技能列表

        Returns:
            映射结果字典，包含推荐位置和理由
        """
        req_lower = requirement.lower()

        best_province: str = ""
        best_dept: str = ""
        best_score: float = 0.0
        alternatives: list[dict[str, Any]] = []

        for province, info in self._province_structure.items():
            keywords = info.get("capacity_keywords", [])
            match_score = sum(1 for kw in keywords if kw.lower() in req_lower)
            normalized_score = match_score / max(len(keywords), 1)

            depts = info.get("departments", [])
            for dept in depts:
                dept_score = normalized_score
                dept_skills = [s for s in existing_skills if s.get("department") == dept]
                if dept_skills:
                    dept_score += 0.15

                result_entry = {
                    "province": province,
                    "province_label": info.get("label", ""),
                    "department": dept,
                    "score": round(dept_score, 3),
                    "reason": f"关键词匹配度 {normalized_score:.0%}",
                }

                if dept_score > best_score:
                    if best_score > 0:
                        alternatives.append({
                            "province": best_province,
                            "department": best_dept,
                            "score": best_score,
                        })
                    best_score = dept_score
                    best_province = province
                    best_dept = dept
                elif dept_score > 0.2:
                    alternatives.append(result_entry)

        need_new_dept = best_score < 0.25
        recommendation = "new_department" if need_new_dept else "existing"

        return {
            "requirement": requirement,
            "recommendation_type": recommendation,
            "primary_mapping": {
                "province": best_province,
                "province_label": self._province_structure.get(best_province, {}).get("label", ""),
                "department": best_dept,
                "confidence": round(best_score, 3),
            } if best_province else None,
            "alternative_mappings": sorted(alternatives, key=lambda x: x["score"], reverse=True)[:3],
            "need_new_department": need_new_dept,
            "suggested_new_dept": self._suggest_new_dept(requirement) if need_new_dept else "",
        }

    def _suggest_new_dept(self, requirement: str) -> str:
        """建议新部门名称"""
        keyword_dept_map = {
            "监控": "monitoring_bureau",
            "安全": "security_bureau",
            "ai": "ai_bureau",
            "数据": "data_bureau",
            "平台": "platform_bureau",
            "网络": "network_bureau",
        }
        for kw, dept in keyword_dept_map.items():
            if kw in requirement.lower():
                return dept
        return "new_functional_bureau"


class IntegrationPlanner:
    """
    集成规划器

    规划新技能如何融入二十四司架构，
    定义依赖关系、接口规范和渐进式上线路径。
    """

    def __init__(self) -> None:
        self._integration_templates: dict[str, dict[str, Any]] = {
            "standard": {
                "phases": ["design", "prototype", "integrate", "validate", "release"],
                "duration_weeks": 4,
                "risk_level": "low",
            },
            "complex": {
                "phases": ["research", "design", "prototype", "pilot", "integrate", "validate", "release"],
                "duration_weeks": 12,
                "risk_level": "medium",
            },
            "strategic": {
                "phases": ["feasibility", "research", "architecture", "design", "prototype",
                          "pilot", "integrate", "validate", "optimize", "release"],
                "duration_weeks": 24,
                "risk_level": "high",
            },
        }

    def plan_integration(
        self, suggestion: NewSkillSuggestion, existing_skills: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        为单个新技能建议制定集成方案

        Args:
            suggestion: 新技能建议对象
            existing_skills: 现有技能列表

        Returns:
            集成方案字典
        """
        complexity = suggestion.estimated_complexity
        template = self._integration_templates.get(complexity, self._integration_templates["standard"])

        dep_chain = self._resolve_dependency_chain(suggestion.dependencies, existing_skills)
        interface_specs = self._define_interface_specs(suggestion)
        rollout_phases = self._build_rollout_phases(template["phases"], suggestion)

        integration_risk = self._assess_integration_risk(suggestion, existing_skills)

        return {
            "skill_name": suggestion.name,
            "template_type": complexity,
            "estimated_duration_weeks": template["duration_weeks"],
            "overall_risk_level": template["risk_level"],
            "dependency_chain": dep_chain,
            "interface_specifications": interface_specs,
            "rollout_plan": rollout_phases,
            "integration_risks": integration_risk,
            "success_criteria": self._define_success_criteria(suggestion),
            "rollback_strategy": self._define_rollback_strategy(suggestion),
        }

    def plan_batch_integration(
        self, suggestions: list[NewSkillSuggestion], existing_skills: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """批量规划多个新技能的集成"""
        plans: list[dict[str, Any]] = []
        for sug in suggestions:
            plans.append(self.plan_integration(sug, existing_skills))

        dependency_order = self._topological_sort(plans)
        return dependency_order

    def _resolve_dependency_chain(
        self, dependencies: list[str], existing_skills: list[dict[str, Any]]
    ) -> list[dict[str, str]]:
        """解析完整的依赖链"""
        chain: list[dict[str, str]] = []
        seen: set[str] = set()

        def resolve(dep: str, depth: int = 0):
            if depth > 5 or dep in seen:
                return
            seen.add(dep)
            sk = next((s for s in existing_skills if s.get("name") == dep), None)
            chain.append({
                "dependency": dep,
                "status": "exists" if sk else "missing",
                "type": sk.get("province", "unknown") if sk else "unknown",
            })
            if sk:
                for sub_dep in sk.get("dependencies", []):
                    resolve(sub_dep, depth + 1)

        for dep in dependencies:
            resolve(dep)

        return chain

    def _define_interface_specs(self, suggestion: NewSkillSuggestion) -> list[dict[str, str]]:
        """定义接口规范"""
        specs = [
            {"interface": "input_schema", "specification": "标准化的输入参数格式（JSON Schema）"},
            {"interface": "output_format", "specification": "统一的输出结果结构"},
            {"interface": "trigger_protocol", "specification": "基于关键词+语义匹配的触发协议"},
            {"interface": "error_handling", "specification": "标准化错误码和异常传播机制"},
            {"interface": "event_bus", "specification": "通过事件总线与其他司/局通信"},
        ]
        return specs

    def _build_rollout_phases(
        self, phases: list[str], suggestion: NewSkillSuggestion
    ) -> list[dict[str, str]]:
        """构建分阶段上线计划"""
        phase_details = {
            "research": ("需求调研与可行性分析", "1-2周"),
            "feasibility": ("技术可行性评估", "1周"),
            "architecture": ("架构设计与技术选型", "2周"),
            "design": ("详细设计与文档编写", "1-2周"),
            "prototype": ("原型开发与验证", "1-2周"),
            "pilot": ("小范围试点验证", "1-2周"),
            "integrate": ("与现有系统集成", "1周"),
            "validate": ("全面测试与验收", "1周"),
            "optimize": ("性能优化与调优", "1-2周"),
            "release": ("正式发布与推广", "1周"),
        }

        result: list[dict[str, str]] = []
        for i, phase in enumerate(phases):
            detail = phase_details.get(phase, (phase, "待定"))
            result.append({
                "phase": phase,
                "phase_index": i + 1,
                "description": detail[0],
                "duration": detail[1],
                "deliverables": f"{suggestion.name} {phase}阶段产物",
                "gate_criteria": f"{phase}阶段准入/准出标准",
            })
        return result

    def _assess_integration_risk(
        self, suggestion: NewSkillSuggestion, existing_skills: list[dict[str, Any]]
    ) -> list[dict[str, str]]:
        """评估集成风险"""
        risks: list[dict[str, str]] = []

        missing_deps = [d for d in suggestion.dependencies
                       if not any(s.get("name") == d for s in existing_skills)]
        if missing_deps:
            risks.append({
                "type": "dependency_gap",
                "level": "high",
                "description": f"依赖缺失: {', '.join(missing_deps)}",
                "mitigation": "优先创建或模拟缺失依赖",
            })

        high_similarity = [s for s in existing_skills
                         if suggestion.name.replace("_si", "") in s.get("name", "").replace("_si", "")
                         and s.get("name") != suggestion.name]
        if high_similarity:
            risks.append({
                "type": "naming_collision",
                "level": "medium",
                "description": f"与现有技能命名相似: {[s['name'] for s in high_similarity]}",
                "mitigation": "重新命名或明确职责边界",
            })

        if suggestion.estimated_complexity == "large":
            risks.append({
                "type": "complexity_risk",
                "level": "medium",
                "description": "复杂度高，开发周期长",
                "mitigation": "采用迭代交付方式，分阶段上线",
            })

        if not risks:
            risks.append({
                "type": "low_risk",
                "level": "low",
                "description": "集成风险较低",
                "mitigation": "按计划推进即可",
            })

        return risks

    def _define_success_criteria(self, suggestion: NewSkillSuggestion) -> list[str]:
        """定义成功标准"""
        return [
            f"{suggestion.name} 可被正确发现和加载",
            f"触发词命中率 >= 80%",
            f"执行成功率 >= 95%",
            f"平均响应时间 < 2000ms",
            f"用户满意度 >= 4.0/5.0",
            "与依赖技能正确协同工作",
            "无命名冲突或功能重叠",
        ]

    def _define_rollback_strategy(self, suggestion: NewSkillSuggestion) -> str:
        """定义回滚策略"""
        return (
            f"如{suggestion.name}上线后出现严重问题："
            "1) 立即禁用该技能（设置status=inactive）；"
            "2) 将其依赖技能的调用路由到备用路径；"
            "3) 收集问题日志并进行分析；"
            "4) 修复后重新走验证流程。"
        )

    def _topological_sort(
        self, plans: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """按依赖关系对集成计划进行拓扑排序"""
        sorted_plans: list[dict[str, Any]] = []
        visited: set[int] = set()

        def visit(idx: int):
            if idx in visited:
                return
            visited.add(idx)
            deps = plans[idx].get("dependency_chain", [])
            for dep_info in deps:
                dep_name = dep_info.get("dependency", "")
                for other_idx, other_plan in enumerate(plans):
                    if other_plan.get("skill_name") == dep_name:
                        visit(other_idx)
                        break
            sorted_plans.append(plans[idx])

        for i in range(len(plans)):
            visit(i)

        return sorted_plans


def analyze_gaps(usage_patterns: list[dict[str, Any]]) -> ExtensionProposal:
    """
    执行完整的缺口分析与扩展建议流程

    整合缺口识别、新技能建议、能力映射和集成规划，
    输出包含具体行动方案的扩展提案。

    Args:
        usage_patterns: 使用模式数据列表

    Returns:
        完整的ExtensionProposal扩展提案
    """
    from ..utils.subskill_manager import SubSkillManager

    manager = SubSkillManager()
    skills_data = [info.to_dict() for info in manager.all_skills.values()]

    analyzer = GapAnalyzer()
    proposer = NewSkillProposer()
    mapper = CapabilityMapper()
    planner = IntegrationPlanner()

    for pattern in usage_patterns:
        analyzer.add_usage_pattern(
            pattern.get("query", ""),
            pattern.get("matched_skills", []),
            pattern.get("confidence", 1.0),
        )

    for pattern in usage_patterns:
        if not pattern.get("matched_skills"):
            analyzer.add_unmatched_query(
                pattern.get("query", ""),
                pattern.get("reason", "无匹配技能"),
            )

    gaps, gap_summary = analyzer.analyze_gaps(skills_data)

    proposer.set_existing_skills(list(manager.all_skills.keys()))
    suggestions = proposer.propose_skills(gaps, skills_data)

    capability_maps: list[dict[str, Any]] = []
    for sug in suggestions[:5]:
        cap_map = mapper.map_capability(sug.description, skills_data)
        capability_maps.append(cap_map)

    integration_plans: list[dict[str, Any]] = planner.plan_batch_integration(
        suggestions[:5], skills_data
    )

    roadmap: list[dict[str, Any]] = []
    for i, (sug, integ_plan) in enumerate(zip(suggestions[:5], integration_plans)):
        phases = integ_plan.get("rollout_plan", [])
        roadmap.append({
            "priority_rank": i + 1,
            "skill_name": sug.name,
            "complexity": sug.estimated_complexity,
            "duration_weeks": integ_plan.get("estimated_duration_weeks", 0),
            "phases_count": len(phases),
            "first_phase": phases[0]["description"] if phases else "N/A",
            "risk_level": integ_plan.get("overall_risk_level", "unknown"),
        })

    critical_count = sum(1 for g in gaps if g.severity == GapSeverity.CRITICAL)

    risk_parts: list[str] = []
    if critical_count > 0:
        risk_parts.append(f"存在{critical_count}个关键能力缺口需要紧急填补")
    if len(suggestions) > 3:
        risk_parts.append(f"同时引入{len(suggestions)}个新技能可能带来集成复杂度")
    if any(p.get("overall_risk_level") == "high" for p in integration_plans):
        risk_parts.append("部分新技能集成风险较高，需分批推进")

    proposal = ExtensionProposal(
        total_gaps=len(gaps),
        critical_gaps=critical_count,
        new_skill_suggestions=suggestions,
        gaps=gaps,
        integration_roadmap=roadmap,
        summary=(
            f"分析完成：发现 {len(gaps)} 个能力缺口 "
            f"(🔴关键{critical_count})，"
            f"提出 {len(suggestions)} 个新技能建议"
        ),
        risk_assessment="；".join(risk_parts) if risk_parts else "整体风险可控",
    )

    print(f"✅ 扩展提案已生成 ({proposal.proposal_id}): {proposal.summary}")
    return proposal


if __name__ == "__main__":
    from ..utils.subskill_manager import SubSkillManager

    print("=" * 60)
    print("🧪 技能自扩展建议器 - 功能演示")
    print("=" * 60)

    manager = SubSkillManager()
    skills_data = [info.to_dict() for info in manager.all_skills.values()]

    mock_patterns = [
        {"query": "帮我搭建CI/CD流水线", "matched_skills": [], "confidence": 0.0},
        {"query": "我想做压力测试和性能分析", "matched_skills": [], "confidence": 0.1},
        {"query": "如何进行安全漏洞扫描", "matched_skills": [], "confidence": 0.05},
        {"query": "集成AI辅助编程工具", "matched_skills": [], "confidence": 0.0},
        {"query": "微服务架构设计", "matched_skills": ["architecture_bureau"], "confidence": 0.4},
        {"query": "搭建监控系统", "matched_skills": [], "confidence": 0.0},
        {"query": "代码审查工作流优化", "matched_skills": ["code_review_bureau"], "confidence": 0.5},
        {"query": "遗留系统迁移方案", "matched_skills": [], "confidence": 0.0},
        {"query": "数据库压测", "matched_skills": ["database_design_si"], "confidence": 0.3},
        {"query": "团队协作流程改进", "matched_skills": ["coordination_si"], "confidence": 0.45},
        {"query": "容器化部署Kubernetes", "matched_skills": ["infrastructure_si"], "confidence": 0.7},
        {"query": "API网关设计", "matched_skills": ["api_design_si"], "confidence": 0.65},
        {"query": "合规审计自动化", "matched_skills": ["compliance_bureau"], "confidence": 0.55},
        {"query": "数据管道ETL", "matched_skills": [], "confidence": 0.0},
        {"query": "服务网格Istio配置", "matched_skills": [], "confidence": 0.0},
    ]

    print("\n--- 缺口分析 ---\n")
    ga = GapAnalyzer()
    for p in mock_patterns:
        ga.add_usage_pattern(p["query"], p["matched_skills"], p["confidence"])
        if not p["matched_skills"]:
            ga.add_unmatched_query(p["query"])

    gaps, gap_summary = ga.analyze_gaps(skills_data)
    print(f"   发现缺口: {len(gaps)} 个")
    print(f"   按严重程度分布: {gap_summary['by_severity']}")
    for g in gaps[:5]:
        icon = {"critical": "🔴", "significant": "🟠", "moderate": "🟡", "minor": "🔵"}.get(g.severity.value, "⚪")
        print(f"   {icon} [{g.category}] {g.description[:50]} (置信度:{g.confidence:.0%})")

    print("\n--- 新技能建议 ---\n")
    np = NewSkillProposer()
    np.set_existing_skills(list(manager.all_skills.keys()))
    suggestions = np.propose_skills(gaps, skills_data)
    print(f"   建议数量: {len(suggestions)}")
    for s in suggestions[:6]:
        print(f"   💡 {s.name} ({s.province}/{s.proposed_department})")
        print(f"      描述: {s.description[:60]}")
        print(f"      触发词: {s.triggers[:5]}...")
        print(f"      复杂度: {s.estimated_complexity}, 价值: {s.value_proposition[:50]}")

    print("\n--- 能力映射 ---\n")
    cm = CapabilityMapper()
    test_requirements = ["搭建完整的CI/CD流水线", "实现应用性能监控APM", "AI驱动的代码审查"]
    for req in test_requirements:
        mapping = cm.map_capability(req, skills_data)
        primary = mapping.get("primary_mapping")
        print(f"   📌 「{req}」")
        if primary:
            print(f"      → {primary['province_label']}/{primary['department']} (置信度:{primary['confidence']:.0%})")
        if mapping.get("need_new_department"):
            print(f"      ⚠️ 建议: {mapping['suggested_new_dept']}")

    print("\n--- 集成规划 ---\n")
    ip = IntegrationPlanner()
    if suggestions:
        sample_plan = ip.plan_integration(suggestions[0], skills_data)
        print(f"   技能: {sample_plan['skill_name']}")
        print(f"   周期: {sample_plan['estimated_duration_weeks']} 周")
        print(f"   风险: {sample_plan['overall_risk_level']}")
        print(f"   阶段:")
        for phase in sample_plan.get("rollout_plan", []):
            print(f"      {phase['phase_index']}. {phase['description']} ({phase['duration']})")

    print("\n--- 完整扩展提案 ---\n")
    proposal = analyze_gaps(mock_patterns)
    print(f"📋 提案ID: {proposal.proposal_id}")
    print(f"📊 总览: {proposal.summary}")
    print(f"⚠️ 风险: {proposal.risk_assessment}")
    print(f"\n🗺️ 集成路线图:")
    for item in proposal.integration_roadmap[:5]:
        print(f"   #{item['priority_rank']} {item['skill_name']} ({item['complexity']}, {item['duration_weeks']}周)")

    print("\n✅ 所有演示通过!")
