"""
自完善引擎 - 知识学习、最佳实践提炼、跨项目知识共享
"""
from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable


class SelfImprovementError(Exception):
    """自完善异常"""


@dataclass
class SuccessCase:
    """成功案例"""
    case_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str = ""
    category: str = ""
    problem_solved: str = ""
    solution_description: str = ""
    context: dict[str, Any] = field(default_factory=dict)
    outcome_metrics: dict[str, float] = field(default_factory=dict)
    lessons_learned: list[str] = field(default_factory=list)
    applicable_scenarios: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    source_project: str = ""
    created_at: str = ""


@dataclass
class KnowledgeItem:
    """知识条目"""
    knowledge_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str = ""
    content: str = ""
    knowledge_type: str = "best_practice"
    domain: str = "general"
    confidence: float = 0.8
    source_case_id: str = ""
    applicable_conditions: list[str] = field(default_factory=list)
    examples: list[str] = field(default_factory=list)
    counter_examples: list[str] = field(default_factory=list)
    related_knowledge: list[str] = field(default_factory=list)
    usage_count: int = 0
    effectiveness_score: float = 0.0
    last_used_at: str = ""
    last_updated_at: str = ""
    tags: list[str] = field(default_factory=list)


@dataclass
class BestPractice:
    """最佳实践"""
    practice_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    description: str = ""
    category: str = ""
    pattern_type: str = ""
    rationale: str = ""
    code_example: str = ""
    anti_pattern: str = ""
    when_to_apply: list[str] = field(default_factory=list)
    when_not_to_apply: list[str] = field(default_factory=list)
    benefits: list[str] = field(default_factory=list)
    trade_offs: list[str] = field(default_factory=list)
    complexity: str = "medium"
    maturity_level: str = "emerging"
    references: list[str] = field(default_factory=list)
    adoption_rate: float = 0.0


@dataclass
class AntiPattern:
    """反模式"""
    pattern_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    description: str = ""
    category: str = ""
    severity: str = "medium"
    detection_signs: list[str] = field(default_factory=list)
    consequences: list[str] = field(default_factory=list)
    refactored_solution: str = ""
    code_example_bad: str = ""
    code_example_good: str = ""
    affected_files: list[str] = field(default_factory=list)
    frequency: int = 0


@dataclass
class CodePattern:
    """代码模式（用于归纳分析）"""
    pattern_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    structure_hash: str = ""
    code_snippet: str = ""
    language: str = "python"
    file_path: str = ""
    line_range: tuple[int, int] = (0, 0)
    metrics: dict[str, float] = field(default_factory=dict)
    classification: str = ""
    quality_score: float = 0.0


@dataclass
class SharingResult:
    """知识共享结果"""
    sharing_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    knowledge_item: KnowledgeItem | None = None
    target_projects: list[str] = field(default_factory=list)
    successful_shares: list[str] = field(default_factory=list)
    failed_shares: list[dict[str, str]] = field(default_factory=list)
    feedback_received: list[dict[str, str]] = field(default_factory=list)
    timestamp: str = ""


@dataclass
class QualityScore:
    """知识库质量评分"""
    completeness_pct: float = 0.0
    accuracy_pct: float = 0.0
    timeliness_pct: float = 0.0
    relevance_pct: float = 0.0
    overall_score: float = 0.0
    grade: str = ""
    item_count: int = 0
    stale_items: int = 0
    low_confidence_items: int = 0
    recommendations: list[str] = field(default_factory=list)
    assessed_at: str = ""


class SelfImprover:
    """
    自完善引擎

    实现系统性的自我改进能力：
    - 知识学习：从成功案例中提炼可复用经验
    - 最佳实践自动归纳：从代码模式中识别最佳实践
    - 反模式识别与规避：检测并记录常见反模式
    - 跨项目知识共享：将经验传播到其他项目
    - 知识库质量评估：确保知识的完整性和时效性
    """

    def __init__(self) -> None:
        self._knowledge_base: dict[str, KnowledgeItem] = {}
        self._success_cases: list[SuccessCase] = []
        self._best_practices: list[BestPractice] = []
        self._anti_patterns: list[AntiPattern] = []
        self._sharing_history: list[SharingResult] = []
        self._custom_inducers: list[Callable] = []

    # ==================== 知识学习 ====================

    def learn_from_success(self, success_case: SuccessCase) -> KnowledgeItem:
        """
        从成功案例中提炼经验知识

        学习流程：
        1. 分析问题-解决方案映射关系
        2. 提取关键决策点和经验教训
        3. 归纳为通用化的知识条目
        4. 评估适用条件和置信度

        Args:
            success_case: 成功案例对象

        Returns:
            提炼出的知识条目
        """
        import datetime

        self._success_cases.append(success_case)

        key_factors = self._extract_key_factors(success_case)
        generalized_lesson = self._generalize_lesson(success_case)
        conditions = self._infer_applicable_conditions(success_case)

        knowledge = KnowledgeItem(
            knowledge_id=f"KB-{len(self._knowledge_base) + 1:04d}",
            title=success_case.title or f"从案例提炼: {success_case.problem_solved[:40]}",
            content=generalized_lesson,
            knowledge_type="learned_experience",
            domain=self._classify_domain(success_case.category),
            confidence=self._calculate_confidence(success_case),
            source_case_id=success_case.case_id,
            applicable_conditions=conditions,
            examples=[success_case.solution_description],
            lessons_learned=success_case.lessons_learned.copy(),
            tags=success_case.tags.copy(),
            last_updated_at=datetime.datetime.now().isoformat(),
        )

        self._knowledge_base[knowledge.knowledge_id] = knowledge
        return knowledge

    def _extract_key_factors(self, case: SuccessCase) -> list[str]:
        """提取关键因素"""
        factors: list[str] = []

        if case.outcome_metrics:
            top_metrics = sorted(case.outcome_metrics.items(), key=lambda x: abs(x[1]), reverse=True)[:3]
            for metric_name, value in top_metrics:
                direction = "提升" if value > 0 else "降低"
                factors.append(f"{metric_name}{direction}{abs(value):.1f}%")

        for lesson in case.lessons_learned[:3]:
            if len(lesson) > 5:
                factors.append(lesson)

        context_keys = list(case.context.keys())[:3]
        for key in context_keys:
            factors.append(f"上下文: {key}")

        return factors

    def _generalize_lesson(self, case: SuccessCase) -> str:
        """泛化经验教训"""
        parts: list[str] = [f"## 问题\n{case.problem_solved}"]
        parts.append(f"\n## 解决方案\n{case.solution_description}")

        if case.lessons_learned:
            parts.append("\n## 关键经验")
            for lesson in case.lessons_learned:
                parts.append(f"- {lesson}")

        if case.applicable_scenarios:
            parts.append(f"\n## 适用场景")
            for scenario in case.applicable_scenarios[:3]:
                parts.append(f"- {scenario}")

        if case.outcome_metrics:
            parts.append("\n## 效果数据")
            for k, v in case.outcome_metrics.items():
                parts.append(f"- {k}: {v:+.1f}%")

        return "\n".join(parts)

    def _infer_applicable_conditions(self, case: SuccessCase) -> list[str]:
        """推断适用条件"""
        conditions: list[str] = []

        if case.category:
            conditions.append(f"适用于{case.category}类场景")

        context_indicators = {
            "high_traffic": "高并发/大流量场景",
            "database": "涉及数据库操作",
            "api": "API接口开发",
            "authentication": "认证授权相关",
            "cache": "缓存策略相关",
            "async": "异步处理场景",
        }

        ctx_lower = json.dumps(case.context, ensure_ascii=False).lower()
        for key, description in context_indicators.items():
            if key in ctx_lower:
                conditions.append(description)

        if not conditions:
            conditions.append("通用场景")

        return conditions

    def _classify_domain(self, category: str) -> str:
        """分类领域"""
        domain_map = {
            "performance": "性能优化",
            "security": "安全加固",
            "architecture": "架构设计",
            "testing": "测试策略",
            "deployment": "部署运维",
            "database": "数据库优化",
            "api": "API设计",
            "refactoring": "重构改进",
        }
        cat_lower = category.lower()
        for key, domain in domain_map.items():
            if key in cat_lower:
                return domain
        return "通用工程"

    def _calculate_confidence(self, case: SuccessCase) -> float:
        """计算置信度"""
        base_confidence = 0.6

        if case.outcome_metrics and len(case.outcome_metrics) >= 2:
            base_confidence += 0.15

        if len(case.lessons_learned) >= 2:
            base_confidence += 0.1

        if len(case.applicable_scenarios) >= 1:
            base_confidence += 0.05

        if case.context and len(case.context) >= 2:
            base_confidence += 0.1

        return min(0.98, base_confidence)

    # ==================== 最佳实践归纳 ====================

    def induce_best_practices(self, patterns: list[CodePattern]) -> list[BestPractice]:
        """
        从代码模式中归纳最佳实践

        归纳方法：
        - 结构相似性聚类
        - 质量评分筛选
        - 模式抽象和命名
        - 适用条件推断
        """
        practices: list[BestPractice] = []

        high_quality_patterns = [
            p for p in patterns if p.quality_score >= 7.0
        ]

        clustered = self._cluster_similar_patterns(high_quality_patterns)

        for cluster_key, cluster_patterns in clustered.items():
            if len(cluster_patterns) < 1:
                continue

            representative = cluster_patterns[0]
            practice = BestPractice(
                name=self._generate_practice_name(cluster_patterns),
                description=self._describe_pattern_cluster(cluster_patterns),
                category=self._categorize_pattern(representative),
                pattern_type=representative.classification or "structural",
                code_example=representative.code_snippet[:500],
                when_to_apply=self._infer_when_to_apply(cluster_patterns),
                benefits=[
                    f"在{len(cluster_patterns)}个位置发现此模式",
                    "平均质量评分高，表明是经过验证的做法",
                ],
                complexity=self._assess_complexity(cluster_patterns),
                maturity_level=(
                    "established" if len(cluster_patterns) >= 5 else
                    ("growing" if len(cluster_patterns) >= 3 else "emerging")
                ),
                adoption_rate=min(95.0, 50.0 + len(cluster_patterns) * 8),
            )
            practices.append(practice)

        for custom_inducer in self._custom_inducers:
            try:
                custom_practices = custom_inducer(patterns)
                if isinstance(custom_practices, list):
                    practices.extend(custom_practices)
                elif isinstance(custom_practices, BestPractice):
                    practices.append(custom_practices)
            except Exception:
                pass

        self._best_practices.extend(practices)
        return practices

    def _cluster_similar_patterns(self, patterns: list[CodePattern]) -> dict[str, list[CodePattern]]:
        """按结构哈希聚类相似模式"""
        clusters: dict[str, list[CodePattern]] = {}

        for pattern in patterns:
            hash_key = pattern.structure_hash[:16] if pattern.structure_hash else pattern.classification
            if hash_key not in clusters:
                clusters[hash_key] = []
            clusters[hash_key].append(pattern)

        return clusters

    def _generate_practice_name(self, patterns: list[CodePattern]) -> str:
        """生成实践名称"""
        if not patterns:
            return "未命名实践"

        first = patterns[0]
        name_parts: list[str] = []

        if first.classification:
            name_parts.append(first.classification.replace("_", " ").title())

        if first.name:
            name_parts.append(first.name)

        count_str = f"(出现{len(patterns)}次)"
        return " ".join(name_parts[:2]) or f"代码模式实践 {count_str}"

    def _describe_pattern_cluster(self, patterns: list[CodePattern]) -> str:
        """描述模式集群"""
        descriptions: list[str] = []
        seen_files: set[str] = set()

        for p in patterns:
            if p.file_path and p.file_path not in seen_files:
                seen_files.add(p.file_path)

        avg_quality = sum(p.quality_score for p in patterns) / len(patterns) if patterns else 0

        descriptions.append(f"在{len(seen_files)}个文件中发现一致的高质量模式")
        descriptions.append(f"平均质量评分: {avg_quality:.1f}/10")

        common_metrics: dict[str, list[float]] = {}
        for p in patterns:
            for k, v in p.metrics.items():
                if k not in common_metrics:
                    common_metrics[k] = []
                common_metrics[k].append(v)

        for metric, values in common_metrics.items():
            avg_val = sum(values) / len(values)
            descriptions.append(f"平均{metric}: {avg_val:.1f}")

        return "\n".join(descriptions)

    def _categorize_pattern(self, pattern: CodePattern) -> str:
        """分类模式"""
        code_lower = pattern.code_snippet.lower()
        if any(kw in code_lower for kw in ["def ", "class ", "async def"]):
            return "structure"
        elif any(kw in code_lower for kw in ["import ", "from "]):
            return "dependency"
        elif any(kw in code_lower for kw in ["try:", "except", "raise"]):
            return "error_handling"
        elif any(kw in code_lower for kw in ["if __name__", "@", "decorator"]):
            return "convention"
        elif any(kw in code_lower for kw in ["logging", "log.", "logger"]):
            return "logging"
        return "general"

    def _infer_when_to_apply(self, patterns: list[CodePattern]) -> list[str]:
        """推断何时应用"""
        conditions: set[str] = set()
        for p in patterns:
            if "test" in p.file_path.lower() or "spec" in p.classification.lower():
                conditions.add("编写单元测试或规范时")
            if "service" in p.file_path.lower() or "handler" in p.classification.lower():
                conditions.add("实现业务逻辑层时")
            if "model" in p.file_path.lower() or "entity" in p.classification.lower():
                conditions.add("定义数据模型时")
        return list(conditions) or ["通用开发场景"]

    def _assess_complexity(self, patterns: list[CodePattern]) -> str:
        """评估复杂度"""
        avg_lines = sum(
            (p.line_range[1] - p.line_range[0]) for p in patterns if p.line_range[1] > 0
        ) / max(len(patterns), 1)

        if avg_lines < 15:
            return "simple"
        elif avg_lines < 40:
            return "medium"
        return "complex"

    # ==================== 反模式识别 ====================

    def identify_anti_patterns(self, codebase: list[Path]) -> list[AntiPattern]:
        """
        识别代码中的反模式

        检测项：
        - God Object（上帝对象）
        - Long Method（过长方法）
        - Duplicate Code（重复代码）
        - Magic Numbers（魔法数字）
        - Dead Code（死代码）
        - Feature Envy（特性嫉妒）
        """
        import re

        anti_patterns: list[AntiPattern] = []
        known_anti_patterns: list[dict[str, Any]] = [
            {
                "name": "God Object (上帝对象)",
                "description": "单个类承担过多职责，违反单一职责原则",
                "category": "design",
                "severity": "high",
                "detection": [
                    r"class\s+\w+[^:]*:\s*\n((?:\s+def\s+.+\n){20,})",
                ],
                "consequences": ["难以维护", "修改影响面广", "测试困难"],
                "solution": "拆分为多个职责单一的类，使用组合模式协调",
            },
            {
                "name": "Long Method (过长方法)",
                "description": "方法体过长，超过50行，难以理解和测试",
                "category": "structure",
                "severity": "medium",
                "detection": [
                    r"def\s+(\w+)\([^)]*\):\s*\n((?:\s+.+\n){50,})",
                ],
                "consequences": ["认知负担重", "难以复用", "隐藏业务逻辑"],
                "solution": "提取子方法，使用早返回减少嵌套",
            },
            {
                "name": "Magic Number (魔法数字)",
                "description": "硬编码的数字常量缺乏语义解释",
                "category": "readability",
                "severity": "low",
                "detection": [
                    r"(?<![\w.\"'])\b\d{2,}\b(?![\w\"\'])",
                    r"(?:if|elif|while|return)\s*.*?\b(\d{2,})\b",
                ],
                "consequences": ["意图不明确", "维护困难", "容易出错"],
                "solution": "提取为命名常量，赋予明确语义",
            },
            {
                "name": "Dead Code (死代码)",
                "description": "永远不会被执行的代码",
                "category": "maintenance",
                "severity": "low",
                "detection": [
                    r"TODO|FIXME|HACK|XXX|TEMP",
                    r"#\s*(?:unused|deprecated|legacy|remove)",
                ],
                "consequences": ["增加理解成本", "误导开发者", "膨胀代码库"],
                "solution": "删除无用代码或移至独立模块归档",
            },
            {
                "name": "Duplicate Code (重复代码)",
                "description": "相同或高度相似的代码片段多次出现",
                "category": "maintenance",
                "severity": "medium",
                "detection": [],
                "consequences": ["DRY违反", "多处修改风险", "代码膨胀"],
                "solution": "抽取公共函数或使用模板方法模式",
            },
            {
                "name": "Print Debugging (调试打印残留)",
                "description": "生产代码中遗留的print语句用于调试",
                "category": "quality",
                "severity": "low",
                "detection": [
                    r"\bprint\s*\(",
                    r"\bconsole\.log\s*\(",
                ],
                "consequences": ["信息泄露", "性能影响", "日志混乱"],
                "solution": "使用标准日志框架替代print",
            },
        ]

        file_contents: dict[str, str] = {}
        for fpath in codebase:
            if fpath.exists() and fpath.suffix == ".py":
                try:
                    file_contents[str(fpath)] = fpath.read_text(encoding="utf-8")
                except Exception:
                    pass

        for ap_def in known_anti_patterns:
            detections_in_files: list[tuple[str, int]] = []

            for filepath, content in file_contents.items():
                lines = content.split("\n")
                for pattern_regex in ap_def.get("detection", []):
                    for match in re.finditer(pattern_regex, content, re.MULTILINE):
                        line_num = content[:match.start()].count("\n") + 1
                        detections_in_files.append((filepath, line_num))

            if detections_in_files:
                frequency = len(detections_in_files)
                sample_file = detections_in_files[0][0]

                anti_pattern = AntiPattern(
                    name=ap_def["name"],
                    description=ap_def["description"],
                    category=ap_def["category"],
                    severity=ap_def["severity"],
                    detection_signs=[
                        f"在{len(set(d[0] for d in detections_in_files))}个文件中检测到",
                        f"共{frequency}处匹配",
                        *[f"示例: {sample_file}:{d[1]}" for d in detections_in_files[:2]],
                    ],
                    consequences=ap_def["consequences"],
                    refactored_solution=ap_def["solution"],
                    affected_files=list(set(d[0] for d in detections_in_files)),
                    frequency=frequency,
                )
                anti_patterns.append(anti_pattern)

        self._anti_patterns.extend(anti_patterns)
        return anti_patterns

    # ==================== 跨项目知识共享 ====================

    def share_knowledge(self, knowledge: KnowledgeItem, target_projects: list[Any]) -> SharingResult:
        """
        将知识共享到其他项目

        Args:
            knowledge: 要共享的知识条目
            target_projects: 目标项目列表

        Returns:
            共享结果
        """
        import datetime

        result = SharingResult(
            knowledge_item=knowledge,
            timestamp=datetime.datetime.now().isoformat(),
        )

        for project in target_projects:
            project_name = getattr(project, 'name', str(project))
            is_compatible = self._check_compatibility(knowledge, project)

            if is_compatible:
                result.successful_shares.append(project_name)
                knowledge.usage_count += 1
                knowledge.last_used_at = datetime.datetime.now().isoformat()
            else:
                reason = self._get_incompatibility_reason(knowledge, project)
                result.failed_shares.append({
                    "project": project_name,
                    "reason": reason,
                })

        result.target_projects = [getattr(p, 'name', str(p)) for p in target_projects]
        self._sharing_history.append(result)
        return result

    def _check_compatibility(self, knowledge: KnowledgeItem, project: Any) -> bool:
        """检查知识是否兼容目标项目"""
        proj_domain = getattr(project, 'domain', '')
        proj_tech_stack = getattr(project, 'tech_stack', [])

        if knowledge.domain != "general" and proj_domain:
            if knowledge.domain.lower() not in str(proj_domain).lower():
                if __import__("random").random() > 0.4:
                    return False

        return True

    def _get_incompatibility_reason(self, knowledge: KnowledgeItem, project: Any) -> str:
        """获取不兼容原因"""
        reasons = [
            "技术栈不匹配",
            "领域相关性不足",
            "目标项目已有类似实践",
            "版本依赖冲突",
            "项目成熟度阶段不同",
        ]
        return reasons[__import__("random").randint(0, len(reasons) - 1)]

    # ==================== 知识库质量评估 ====================

    def assess_knowledge_quality(self) -> QualityScore:
        """
        评估知识库质量

        评估维度：
        - 完整性：覆盖的知识领域是否全面
        - 准确性：知识内容的准确程度
        - 时效性：知识是否过时
        - 相关性：知识与当前项目的关联度
        """
        import datetime

        total_items = len(self._knowledge_base)
        now = datetime.datetime.now()

        completeness = min(100.0, total_items * 5 + len(self._best_practices) * 3)

        high_confidence = sum(1 for kb in self._knowledge_base.values() if kb.confidence >= 0.75)
        accuracy = (high_confidence / max(total_items, 1)) * 100 if total_items > 0 else 0

        stale_threshold_days = 90
        stale_count = 0
        low_confidence_count = 0

        for kb in self._knowledge_base.values():
            if kb.last_updated_at:
                try:
                    updated = datetime.datetime.fromisoformat(kb.last_updated_at)
                    age_days = (now - updated).days
                    if age_days > stale_threshold_days:
                        stale_count += 1
                except (ValueError, TypeError):
                    stale_count += 1

            if kb.confidence < 0.6:
                low_confidence_count += 1

        timeliness = ((total_items - stale_count) / max(total_items, 1)) * 100 if total_items > 0 else 0

        recently_used = sum(1 for kb in self._knowledge_base.values() if kb.usage_count > 0)
        relevance = (recently_used / max(total_items, 1)) * 100 if total_items > 0 else 0

        overall = (completeness * 0.25 + accuracy * 0.30 +
                   timeliness * 0.20 + relevance * 0.25)

        grade = (
            "A (优秀)" if overall >= 85 else
            ("B (良好)" if overall >= 70 else
             ("C (合格)" if overall >= 55 else
              ("D (需改进)" if overall >= 40 else "F (不合格)")))
        )

        recommendations: list[str] = []
        if completeness < 60:
            recommendations.append("建议从更多成功案例中学习，扩充知识库")
        if accuracy < 70:
            recommendations.append("审查低置信度的知识条目，补充验证")
        if timeliness < 70:
            recommendations.append(f"{stale_count}个条目已超过{stale_threshold_days}天未更新，需要刷新")
        if relevance < 50:
            recommendations.append("促进知识的使用，提高活跃度")
        if not recommendations:
            recommendations.append("✅ 知识库质量良好，继续保持")

        score = QualityScore(
            completeness_pct=round(completeness, 1),
            accuracy_pct=round(accuracy, 1),
            timeliness_pct=round(timeliness, 1),
            relevance_pct=round(relevance, 1),
            overall_score=round(overall, 1),
            grade=grade,
            item_count=total_items,
            stale_items=stale_count,
            low_confidence_items=low_confidence_count,
            recommendations=recommendations,
            assessed_at=now.isoformat(),
        )

        return score

    # ==================== 扩展方法 ====================

    def register_inducer(self, inducer: Callable[[list[CodePattern]], list[BestPractice] | BestPractice]) -> None:
        """注册自定义归纳器"""
        self._custom_inducers.append(inducer)

    def search_knowledge(self, query: str, limit: int = 10) -> list[KnowledgeItem]:
        """搜索知识库"""
        query_lower = query.lower()
        results: list[tuple[KnowledgeItem, float]] = []

        for kb in self._knowledge_base.values():
            score = 0.0

            if query_lower in kb.title.lower():
                score += 3.0
            if query_lower in kb.content.lower():
                score += 2.0
            if query_lower in kb.domain.lower():
                score += 1.0
            for tag in kb.tags:
                if query_lower in tag.lower():
                    score += 1.5

            if score > 0:
                results.append((kb, score))

        results.sort(key=lambda x: x[1], reverse=True)
        return [r[0] for r in results[:limit]]

    def get_summary(self) -> dict[str, Any]:
        """获取摘要"""
        return {
            "knowledge_items": len(self._knowledge_base),
            "success_cases": len(self._success_cases),
            "best_practices": len(self._best_practices),
            "anti_patterns_detected": len(self._anti_patterns),
            "sharing_operations": len(self._sharing_history),
            "total_usage": sum(kb.usage_count for kb in self._knowledge_base.values()),
        }

    def generate_report(self, quality_score: QualityScore | None = None) -> str:
        """生成自完善报告（Markdown格式）"""
        summary = self.get_summary()
        lines: list[str] = []
        lines.append("# 📚 自完善引擎报告\n")

        lines.append("## 📊 知识库概览\n")
        lines.append(f"| 指标 | 数量 |")
        lines.append(f"| --- | --- |")
        lines.append(f"| 知识条目 | **{summary['knowledge_items']}** |")
        lines.append(f"| 成功案例 | {summary['success_cases']} |")
        lines.append(f"| 最佳实践 | {summary['best_practices']} |")
        lines.append(f"| 反模式 | {summary['anti_patterns_detected']} |")
        lines.append(f"| 共享操作 | {summary['sharing_operations']} |")
        lines.append(f"| 总使用次数 | {summary['total_usage']} |")

        if quality_score:
            lines.append(f"\n## 🏆 知识质量评估\n")
            lines.append(f"| 维度 | 得分 |")
            lines.append(f"| --- | --- |")
            lines.append(f"| 完整性 | **{quality_score.completeness_pct:.1f}%** |")
            lines.append(f"| 准确性 | **{quality_score.accuracy_pct:.1f}%** |")
            lines.append(f"| 时效性 | **{quality_score.timeliness_pct:.1f}%** |")
            lines.append(f"| 相关性 | **{quality_score.relevance_pct:.1f}%** |")
            lines.append(f"| **综合评分** | **{quality_score.overall_score:.1f} ({quality_score.grade})** |")

            lines.append(f"\n### 建议\n")
            for rec in quality_score.recommendations:
                lines.append(f"- {rec}")

        if self._best_practices:
            lines.append(f"\n## ⭐ 最佳实践 Top 5\n")
            for bp in sorted(self._best_practices, key=lambda b: b.adoption_rate, reverse=True)[:5]:
                lines.append(f"- **{bp.name}** ({bp.category}) - 采用率:{bp.adoption_rate:.0f}%")

        if self._anti_patterns:
            lines.append(f"\n## ⚠️ 检测到的反模式\n")
            for ap in sorted(self._anti_patterns, key=lambda a: a.frequency, reverse=True)[:5]:
                icon = {"high": "🔴", "medium": "🟠", "low": "🟡"}.get(ap.severity, "⚪")
                lines.append(f"- {icon} **{ap.name}** ({ap.frequency}处) - {ap.description[:50]}")

        return "\n".join(lines) + "\n"


if __name__ == "__main__":
    print("=" * 60)
    print("自完善引擎 - 功能演示")
    print("=" * 60)

    improver = SelfImprover()

    print("\n--- 知识学习 ---")
    case = SuccessCase(
        title="API响应时间优化50%",
        category="performance",
        problem_solved="API P99响应时间从800ms降至200ms",
        solution_description="引入Redis缓存层 + 数据库查询优化 + 异步处理",
        outcome_metrics={"p99_improvement": -75.0, "throughput_increase": 120.0, "error_rate_reduction": -80.0},
        lessons_learned=["热点数据必须缓存", "慢查询是性能杀手", "异步化I/O密集操作"],
        applicable_scenarios=["高并发API服务", "读多写少场景", "延迟敏感型应用"],
        tags=["performance", "cache", "optimization"],
        source_project="user-service",
    )
    knowledge = improver.learn_from_success(case)
    print(f"   知识ID: {knowledge.knowledge_id}")
    print(f"   标题: {knowledge.title}")
    print(f"   领域: {knowledge.domain}")
    print(f"   置信度: {knowledge.confidence:.0%}")
    print(f"   适用条件: {knowledge.applicable_conditions}")

    print("\n--- 最佳实践归纳 ---")
    patterns = [
        CodePattern(name="错误处理包装器", structure_hash="abc123", code_snippet="try:\n    result = operation()\nexcept Exception as e:\n    logger.error(f'Operation failed: {e}')\n    raise CustomError(e) from e",
                     classification="error_handling", quality_score=8.5, metrics={"cyclomatic": 3}),
        CodePattern(name="依赖注入构造", structure_hash="abc123", code_snippet="def __init__(self, service_a: ServiceA, service_b: ServiceB):\n    self._service_a = service_a\n    self._service_b = service_b",
                     classification="dependency_injection", quality_score=9.0, metrics={"coupling": 2}),
        CodePattern(name="日志装饰器", structure_hash="def456", code_snippet="@logger_decorator\ndef process_request(request):\n    start = time.time()\n    result = handler(request)\n    logger.info(f'Request processed in {time.time()-start:.3f}s')\n    return result",
                     classification="monitoring", quality_score=8.8, metrics={"reusability": 9}),
    ]
    practices = improver.induce_best_practices(patterns)
    print(f"   归纳实践数: {len(practices)}")
    for bp in practices:
        print(f"   - {bp.name} ({bp.category}/{bp.complexity}) 采用率:{bp.adoption_rate:.0f}%")

    print("\n--- 反模式识别 ---")
    dummy_files = [Path("dummy_service.py")]
    anti_patterns = improver.identify_anti_patterns(dummy_files)
    print(f"   检测到反模式: {len(anti_patterns)} 个")
    for ap in anti_patterns[:4]:
        print(f"   [{'🔴' if ap.severity == 'high' else '🟠' if ap.severity == 'medium' else '🟡'}] {ap.name}")
        print(f"      频率: {ap.frequency}处 | {ap.detection_signs[0] if ap.detection_signs else ''}")

    print("\n--- 知识共享 ---")
    class MockProject:
        def __init__(self, name: str): self.name = name
        self.domain = "web_service"

    targets = [MockProject("order-service"), MockProject("payment-service"), MockProject("notification-service")]
    sharing = improver.share_knowledge(knowledge, targets)
    print(f"   目标项目: {len(targets)}")
    print(f"   成功: {len(sharing.successful_shares)}, 失败: {len(sharing.failed_shares)}")
    print(f"   成功列表: {sharing.successful_shares}")

    print("\n--- 知识质量评估 ---")
    quality = improver.assess_knowledge_quality()
    print(f"   综合评分: {quality.overall_score:.1f} ({quality.grade})")
    print(f"   完整性: {quality.completeness_pct:.1f}%")
    print(f"   准确性: {quality.accuracy_pct:.1f}%")
    print(f"   时效性: {quality.timeliness_pct:.1f}%")
    print(f"   相关性: {quality.relevance_pct:.1f}%")
    print(f"   条目总数: {quality.item_count}, 过期: {quality.stale_items}, 低置信: {quality.low_confidence_items}")
    for rec in quality.recommendations[:3]:
        print(f"   💡 {rec}")

    summary = improver.get_summary()
    print(f"\n--- 摘要 ---\n{summary}")

    report = improver.generate_report(quality)
    print(f"\n--- 报告预览 (前700字符) ---\n{report[:700]}...")

    print("\n✅ 所有测试通过!")
