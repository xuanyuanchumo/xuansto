"""
技能自评估器 - 对32个子技能进行全面健康检查与效能评估
提供健康检查、触发率分析、有效性评分、满意度追踪四大能力
"""
from __future__ import annotations

import json
import time
import uuid
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


class EvaluationError(Exception):
    """自评估异常"""
    pass


class SkillHealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    BROKEN = "broken"
    MISSING = "missing"


@dataclass
class SubSkillScore:
    """单个子技能的评估得分"""
    skill_name: str
    province: str = ""
    department: str = ""
    health_score: float = 100.0
    trigger_rate_score: float = 0.0
    effectiveness_score: float = 0.0
    satisfaction_score: float = 80.0
    composite_score: float = 0.0
    rank: int = 0
    health_status: SkillHealthStatus = SkillHealthStatus.HEALTHY
    issues: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    last_triggered_at: str | None = None
    total_triggers: int = 0
    avg_effectiveness: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "skill_name": self.skill_name,
            "province": self.province,
            "department": self.department,
            "health_score": round(self.health_score, 2),
            "trigger_rate_score": round(self.trigger_rate_score, 2),
            "effectiveness_score": round(self.effectiveness_score, 2),
            "satisfaction_score": round(self.satisfaction_score, 2),
            "composite_score": round(self.composite_score, 2),
            "rank": self.rank,
            "health_status": self.health_status.value,
            "issues": self.issues,
            "recommendations": self.recommendations,
            "last_triggered_at": self.last_triggered_at,
            "total_triggers": self.total_triggers,
            "avg_effectiveness": round(self.avg_effectiveness, 2),
        }


@dataclass
class SkillEvaluationReport:
    """技能评估总报告"""
    report_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    total_skills: int = 0
    healthy_count: int = 0
    degraded_count: int = 0
    broken_count: int = 0
    missing_count: int = 0
    avg_composite_score: float = 0.0
    top_performers: list[SubSkillScore] = field(default_factory=list)
    bottom_performers: list[SubSkillScore] = field(default_factory=list)
    all_scores: list[SubSkillScore] = field(default_factory=list)
    summary: str = ""
    action_items: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "generated_at": self.generated_at,
            "total_skills": self.total_skills,
            "healthy_count": self.healthy_count,
            "degraded_count": self.degraded_count,
            "broken_count": self.broken_count,
            "missing_count": self.missing_count,
            "avg_composite_score": round(self.avg_composite_score, 2),
            "top_performers": [s.to_dict() for s in self.top_performers],
            "bottom_performers": [s.to_dict() for s in self.bottom_performers],
            "all_scores": [s.to_dict() for s in self.all_scores],
            "summary": self.summary,
            "action_items": self.action_items,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


class SkillHealthChecker:
    """
    技能健康检查器

    检查32个子技能的文件完整性、加载可用性、依赖满足度。
    基于多维度指标输出每个技能的健康状态。
    """

    REQUIRED_FILES: list[str] = ["SKILL.md", "__init__.py"]
    OPTIONAL_FILES: list[str] = ["README.md", "config.json", "examples/"]

    def __init__(self, skill_root: Path | str | None = None) -> None:
        self._skill_root: Path = (
            Path(skill_root).resolve() if skill_root
            else Path(__file__).parent.parent.parent.resolve()
        )
        self._check_results: dict[str, dict[str, Any]] = {}

    def check_skill_health(
        self, skill_info: dict[str, Any], skill_path: Path | None = None
    ) -> tuple[float, SkillHealthStatus, list[str]]:
        """
        检查单个子技能的健康状态

        Args:
            skill_info: 子技能信息字典（含name, province, department等）
            skill_path: 子技能目录路径（可选，自动推断）

        Returns:
            (健康分数, 健康状态, 问题列表)
        """
        name: str = skill_info.get("name", "")
        if not skill_path:
            skill_path = self._infer_skill_path(name)

        score: float = 100.0
        issues: list[str] = []
        status: SkillHealthStatus = SkillHealthStatus.HEALTHY

        if not skill_path or not skill_path.exists():
            return (0.0, SkillHealthStatus.MISSING, [f"技能目录不存在: {skill_path}"])

        required_missing: list[str] = []
        for req_file in self.REQUIRED_FILES:
            target = skill_path / req_file
            if not target.exists():
                required_missing.append(req_file)

        if required_missing:
            penalty = len(required_missing) * 20
            score -= penalty
            for f in required_missing:
                issues.append(f"缺少必需文件: {f}")

        init_py = skill_path / "__init__.py"
        if init_py.exists():
            try:
                with open(init_py, "r", encoding="utf-8") as fh:
                    content = fh.read()
                if len(content.strip()) < 10:
                    score -= 5
                    issues.append("__init__.py 内容过短或为空")
            except (OSError, UnicodeDecodeError):
                score -= 15
                issues.append("__init__.py 无法读取")

        skill_md = skill_path / "SKILL.md"
        if skill_md.exists():
            try:
                with open(skill_md, "r", encoding="utf-8") as fh:
                    md_content = fh.read()
                if len(md_content) < 50:
                    score -= 10
                    issues.append("SKILL.md 内容过短")
                lines = md_content.splitlines()
                has_description = any("description" in line.lower() for line in lines[:10])
                has_triggers = any("trigger" in line.lower() for line in lines[:15])
                if not has_description:
                    score -= 8
                    issues.append("SKILL.md 缺少 description 字段")
                if not has_triggers:
                    score -= 5
                    issues.append("SKILL.md 缺少触发词定义")
            except (OSError, UnicodeDecodeError):
                score -= 15
                issues.append("SKILL.md 无法读取")

        deps = skill_info.get("dependencies", [])
        if deps:
            satisfied_deps: list[str] = []
            missing_deps: list[str] = []
            for dep in deps:
                dep_path = self._infer_skill_path(dep)
                if dep_path and dep_path.exists():
                    satisfied_deps.append(dep)
                else:
                    missing_deps.append(dep)
            if missing_deps:
                score -= len(missing_deps) * 10
                issues.append(f"依赖缺失: {', '.join(missing_deps)}")

        score = max(0.0, min(100.0, score))

        match score:
            case s if s >= 85:
                status = SkillHealthStatus.HEALTHY
            case s if s >= 60:
                status = SkillHealthStatus.DEGRADED
            case s if s > 0:
                status = SkillHealthStatus.BROKEN
            case _:
                status = SkillHealthStatus.MISSING

        self._check_results[name] = {
            "score": score,
            "status": status.value,
            "issues": issues,
            "path": str(skill_path),
        }
        return (score, status, issues)

    def _infer_skill_path(self, skill_name: str) -> Path | None:
        """根据技能名推断其路径"""
        candidates: list[Path] = [
            self._skill_root / "subskills" / skill_name,
            self._skill_root / "skillscripts" / "shangshusheng" / skill_name.replace("_si", ""),
            self._skill_root / "skillscripts" / "zhongshusheng" / skill_name.replace("_bureau", ""),
        ]
        for c in candidates:
            if c.exists():
                return c
        return candidates[0]

    def get_check_summary(self) -> dict[str, Any]:
        """获取健康检查摘要"""
        if not self._check_results:
            return {"message": "尚未执行任何健康检查"}

        statuses: Counter[str] = Counter(r["status"] for r in self._check_results.values())
        avg_score: float = sum(r["score"] for r in self._check_results.values()) / max(len(self._check_results), 1)
        return {
            "total_checked": len(self._check_results),
            "average_score": round(avg_score, 2),
            "status_distribution": dict(statuses),
            "critical_issues": [
                {"skill": k, **v}
                for k, v in self._check_results.items()
                if v["score"] < 40
            ],
        }


class TriggerRateAnalyzer:
    """
    触发率统计与分析器

    分析每个子技能的触发频率、趋势、覆盖范围，
    识别低触发率技能并给出原因诊断。
    """

    def __init__(self) -> None:
        self._trigger_history: list[dict[str, Any]] = []

    def record_trigger(
        self, skill_name: str, context: str = "", success: bool = True
    ) -> None:
        """
        记录一次触发事件

        Args:
            skill_name: 被触发的技能名
            context: 触发上下文（用户输入片段）
            success: 触发是否成功匹配
        """
        self._trigger_history.append({
            "skill_name": skill_name,
            "context": context[:200],
            "success": success,
            "timestamp": datetime.now().isoformat(),
        })

    def load_trigger_data(self, data: list[dict[str, Any]]) -> None:
        """批量加载历史触发数据"""
        self._trigger_history.extend(data)

    def analyze_trigger_rate(
        self, all_skills: list[dict[str, Any]], window_days: int = 30
    ) -> dict[str, dict[str, Any]]:
        """
        分析所有子技能的触发率

        Args:
            all_skills: 所有子技能信息列表
            window_days: 统计窗口（天）

        Returns:
            以技能名为键的触发统计字典
        """
        cutoff = (datetime.now().__class__(datetime.now().year, datetime.now().month, datetime.now().day - window_days)).isoformat()

        recent_triggers = [
            t for t in self._trigger_history
            if t.get("timestamp", "") >= cutoff
        ]

        skill_counts: Counter[str] = Counter(t["skill_name"] for t in recent_triggers if t.get("success"))
        total_triggers: int = sum(skill_counts.values()) or 1

        result: dict[str, dict[str, Any]] = {}
        for skill in all_skills:
            name: str = skill.get("name", "")
            count = skill_counts.get(name, 0)
            rate = count / total_triggers * 100
            triggers = skill.get("triggers", [])

            trend = self._calculate_trend(name, recent_triggers)
            coverage_gap = self._detect_coverage_gaps(triggers, recent_triggers)

            result[name] = {
                "total_triggers": count,
                "trigger_rate_pct": round(rate, 3),
                "trend": trend,
                "trigger_keywords": triggers,
                "coverage_gaps": coverage_gap,
                "score": self._rate_to_score(rate, count, len(triggers)),
            }
        return result

    def _calculate_trend(
        self, skill_name: str, triggers: list[dict[str, Any]]
    ) -> str:
        """计算触发趋势"""
        skill_triggers = [t for t in triggers if t["skill_name"] == skill_name]
        if len(skill_triggers) < 3:
            return "insufficient_data"

        half = len(skill_triggers) // 2
        first_half = skill_triggers[:half]
        second_half = skill_triggers[half:]

        first_rate = len(first_half) / max(len(first_half), 1)
        second_rate = len(second_half) / max(len(second_half), 1)

        ratio = second_rate / max(first_rate, 0.001)
        match True:
            case _ if ratio > 1.3:
                return "rising"
            case _ if ratio < 0.7:
                return "declining"
            case _:
                return "stable"

    def _detect_coverage_gaps(
        self, triggers: list[str], history: list[dict[str, Any]]
    ) -> list[str]:
        """检测关键词覆盖缺口"""
        gaps: list[str] = []
        contexts = [t.get("context", "").lower() for t in history if t.get("context")]
        combined_context = " ".join(contexts)

        for keyword in triggers:
            kw_lower = keyword.lower()
            if kw_lower and kw_lower not in combined_context:
                gaps.append(keyword)

        return gaps

    def _rate_to_score(
        self, rate_pct: float, count: int, num_triggers: int
    ) -> float:
        """将触发率转换为0-100分"""
        if count == 0:
            base = 20.0
        elif rate_pct > 10:
            base = 95.0
        elif rate_pct > 5:
            base = 80.0 + (rate_pct - 5) * 3
        elif rate_pct > 1:
            base = 60.0 + (rate_pct - 1) * 4
        else:
            base = 40.0 + rate_pct * 20

        trigger_bonus = min(num_triggers * 3, 15)
        return min(base + trigger_bonus, 100.0)


class EffectivenessScorer:
    """
    有效性评分器

    基于输出质量、执行效率、错误率等维度对每个子技能进行有效性打分。
    """

    WEIGHTS: dict[str, float] = {
        "output_quality": 0.35,
        "execution_success": 0.25,
        "response_time": 0.15,
        "error_recovery": 0.15,
        "resource_efficiency": 0.10,
    }

    def __init__(self) -> None:
        self._execution_records: list[dict[str, Any]] = []

    def record_execution(
        self,
        skill_name: str,
        success: bool,
        output_quality: float = 0.0,
        execution_time_ms: float = 0.0,
        error_message: str | None = None,
    ) -> None:
        """记录一次执行结果"""
        self._execution_records.append({
            "skill_name": skill_name,
            "success": success,
            "output_quality": output_quality,
            "execution_time_ms": execution_time_ms,
            "error_message": error_message,
            "timestamp": datetime.now().isoformat(),
        })

    def load_execution_data(self, data: list[dict[str, Any]]) -> None:
        """批量加载执行数据"""
        self._execution_records.extend(data)

    def score_effectiveness(
        self, skill_name: str
    ) -> tuple[float, dict[str, float]]:
        """
        计算单个技能的有效性得分

        Returns:
            (综合有效性得分, 各维度得分字典)
        """
        records = [r for r in self._execution_records if r["skill_name"] == skill_name]
        if not records:
            return (50.0, {})

        total = len(records)
        successes = sum(1 for r in records if r["success"])
        failures = total - successes

        success_rate = successes / max(total, 1)
        quality_scores = [r.get("output_quality", 70.0) for r in records if r.get("success")]
        avg_quality = sum(quality_scores) / max(len(quality_scores), 1)
        times = [r.get("execution_time_ms", 0) for r in records if r.get("success")]
        avg_time = sum(times) / max(len(times), 1)

        dim_scores: dict[str, float] = {
            "output_quality": avg_quality,
            "execution_success": success_rate * 100,
            "response_time": self._time_to_score(avg_time),
            "error_recovery": max(0, 100 - failures / max(total, 1) * 100),
            "resource_efficiency": 75.0,
        }

        composite = sum(
            dim_scores.get(dim, 0) * weight
            for dim, weight in self.WEIGHTS.items()
        )
        return (round(composite, 2), {k: round(v, 2) for k, v in dim_scores.items()})

    def _time_to_score(self, avg_time_ms: float) -> float:
        """将平均响应时间转换为得分"""
        match avg_time_ms:
            case t if t <= 50:
                return 100.0
            case t if t <= 200:
                return 90.0 - (t - 50) / 150 * 20
            case t if t <= 1000:
                return 70.0 - (t - 200) / 800 * 30
            case t if t <= 5000:
                return 40.0 - (t - 1000) / 4000 * 25
            case _:
                return max(10.0, 15.0 - (avg_time_ms - 5000) / 10000 * 5)


class SatisfactionTracker:
    """
    用户满意度追踪器

    追踪隐式反馈（是否采纳建议）和显式反馈（直接评价），
    构建满意度画像。
    """

    def __init__(self) -> None:
        self._implicit_feedback: list[dict[str, Any]] = []
        self._explicit_feedback: list[dict[str, Any]] = []

    def record_implicit(
        self, skill_name: str, adopted: bool, context: str = ""
    ) -> None:
        """记录隐式反馈（采纳/拒绝）"""
        self._implicit_feedback.append({
            "skill_name": skill_name,
            "adopted": adopted,
            "context": context[:200],
            "timestamp": datetime.now().isoformat(),
        })

    def record_explicit(
        self, skill_name: str, rating: int, comment: str = ""
    ) -> None:
        """
        记录显式反馈（1-5星评分）

        Args:
            skill_name: 技能名称
            rating: 评分（1-5）
            comment: 评论内容
        """
        rating = max(1, min(5, rating))
        self._explicit_feedback.append({
            "skill_name": skill_name,
            "rating": rating,
            "comment": comment[:500],
            "timestamp": datetime.now().isoformat(),
        })

    def calculate_satisfaction(self, skill_name: str) -> float:
        """
        计算单个技能的综合满意度得分（0-100）

        结合隐式和显式反馈加权计算
        """
        implicit_records = [f for f in self._implicit_feedback if f["skill_name"] == skill_name]
        explicit_records = [f for f in self._explicit_feedback if f["skill_name"] == skill_name]

        implicit_score: float = 50.0
        if implicit_records:
            adopted_count = sum(1 for f in implicit_records if f["adopted"])
            implicit_score = adopted_count / len(implicit_records) * 100

        explicit_score: float = 75.0
        if explicit_records:
            avg_rating = sum(f["rating"] for f in explicit_records) / len(explicit_records)
            explicit_score = (avg_rating / 5.0) * 100

        total_feedback = len(implicit_records) + len(explicit_records)
        if total_feedback == 0:
            return 75.0

        implicit_weight = len(implicit_records) / total_feedback
        explicit_weight = len(explicit_records) / total_feedback

        return round(implicit_score * implicit_weight + explicit_score * explicit_weight, 2)

    def get_satisfaction_summary(self) -> dict[str, Any]:
        """获取整体满意度摘要"""
        all_skills_implicit = set(f["skill_name"] for f in self._implicit_feedback)
        all_skills_explicit = set(f["skill_name"] for f in self._explicit_feedback)
        all_skills = all_skills_implicit | all_skills_explicit

        scores: dict[str, float] = {}
        for sk in all_skills:
            scores[sk] = self.calculate_satisfaction(sk)

        sorted_skills = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return {
            "total_skills_rated": len(scores),
            "top_satisfied": sorted_skills[:5],
            "least_satisfied": sorted_skills[-5:] if sorted_skills else [],
            "avg_satisfaction": round(sum(scores.values()) / max(len(scores), 1), 2),
            "total_implicit_feedback": len(self._implicit_feedback),
            "total_explicit_feedback": len(self._explicit_feedback),
        }


def evaluate(
    skills_data: list[dict[str, Any]],
    skill_root: Path | str | None = None,
) -> SkillEvaluationReport:
    """
    执行完整的技能评估流程

    整合健康检查、触发率分析、有效性评分和满意度追踪，
    输出包含各子技能评分和排名的完整报告。

    Args:
        skills_data: 所有子技能的信息列表
        skill_root: 技能根目录路径

    Returns:
        完整的SkillEvaluationReport对象
    """
    start_time = time.perf_counter()

    health_checker = SkillHealthChecker(skill_root)
    trigger_analyzer = TriggerRateAnalyzer()
    effectiveness_scorer = EffectivenessScorer()
    satisfaction_tracker = SatisfactionTracker()

    all_scores: list[SubSkillScore] = []

    for skill in skills_data:
        name: str = skill.get("name", "")

        health_score, health_status, issues = health_checker.check_skill_health(skill)

        trigger_result = trigger_analyzer.analyze_trigger_rate([skill]).get(name, {})
        trigger_score = trigger_result.get("score", 0.0)
        total_triggers = trigger_result.get("total_triggers", 0)

        eff_score, _ = effectiveness_scorer.score_effectiveness(name)
        sat_score = satisfaction_tracker.calculate_satisfaction(name)

        composite = (
            health_score * 0.25 +
            trigger_score * 0.25 +
            eff_score * 0.30 +
            sat_score * 0.20
        )

        recs: list[str] = []
        if health_score < 70:
            recs.append("修复文件完整性问题")
        if trigger_score < 40:
            recs.append("优化触发词以提升命中率")
        if eff_score < 50:
            recs.append("改进输出质量和执行稳定性")
        if sat_score < 60:
            recs.append("收集用户反馈并改进交互体验")

        sub_score = SubSkillScore(
            skill_name=name,
            province=skill.get("province", ""),
            department=skill.get("department", ""),
            health_score=health_score,
            trigger_rate_score=trigger_score,
            effectiveness_score=eff_score,
            satisfaction_score=sat_score,
            composite_score=composite,
            health_status=health_status,
            issues=issues,
            recommendations=recs,
            total_triggers=total_triggers,
            avg_effectiveness=eff_score,
        )
        all_scores.append(sub_score)

    all_scores.sort(key=lambda s: s.composite_score, reverse=True)
    for i, s in enumerate(all_scores):
        s.rank = i + 1

    healthy = sum(1 for s in all_scores if s.health_status == SkillHealthStatus.HEALTHY)
    degraded = sum(1 for s in all_scores if s.health_status == SkillHealthStatus.DEGRADED)
    broken = sum(1 for s in all_scores if s.health_status == SkillHealthStatus.BROKEN)
    missing = sum(1 for s in all_scores if s.health_status == SkillHealthStatus.MISSING)

    avg_comp = sum(s.composite_score for s in all_scores) / max(len(all_scores), 1)

    action_items: list[str] = []
    if broken > 0:
        action_items.append(f"🔴 紧急修复 {broken} 个损坏状态的子技能")
    if degraded > 0:
        action_items.append(f"🟡 关注 {degraded} 个降级状态的子技能")
    bottom_5 = all_scores[-5:] if len(all_scores) >= 5 else all_scores
    low_performers = [s for s in bottom_5 if s.composite_score < 45]
    if low_performers:
        names = ", ".join(s.skill_name for s in low_performers)
        action_items.append(f"📉 重点优化低分技能: {names}")

    elapsed_ms = (time.perf_counter() - start_time) * 1000

    report = SkillEvaluationReport(
        total_skills=len(all_scores),
        healthy_count=healthy,
        degraded_count=degraded,
        broken_count=broken,
        missing_count=missing,
        avg_composite_score=round(avg_comp, 2),
        top_performers=all_scores[:5],
        bottom_performers=all_scores[-5:] if len(all_scores) >= 5 else all_scores,
        all_scores=all_scores,
        summary=(
            f"共评估 {len(all_skills_data)} 个子技能，"
            f"均分 {avg_comp:.1f}/100，"
            f"健康 {healthy} / 降级 {degraded} / 损坏 {broken} / 缺失 {missing}"
        ),
        action_items=action_items,
    )

    print(f"✅ 评估完成 ({elapsed_ms:.0f}ms): {report.summary}")
    return report


if __name__ == "__main__":
    from ..utils.subskill_manager import SubSkillManager

    print("=" * 60)
    print("🧪 技能自评估器 - 功能演示")
    print("=" * 60)

    manager = SubSkillManager()
    skills_data = [info.to_dict() for info in manager.all_skills.values()]

    print(f"\n📊 待评估技能数: {len(skills_data)}")

    print("\n--- 单独测试各组件 ---\n")

    hc = SkillHealthChecker()
    sample_skill = skills_data[0]
    h_score, h_status, h_issues = hc.check_skill_health(sample_skill)
    print(f"[{sample_skill['name']}] 健康: {h_score:.1f} ({h_status.value})")
    if h_issues:
        for issue in h_issues:
            print(f"   ⚠️ {issue}")

    ta = TriggerRateAnalyzer()
    for i in range(20):
        skill_names = list(manager.all_skills.keys())
        ta.record_trigger(
            skill_names[i % len(skill_names)],
            context=f"测试触发{i}",
            success=True,
        )
    trigger_stats = ta.analyze_trigger_rate(skills_data)
    top_triggered = sorted(trigger_stats.items(), key=lambda x: x[1]["total_triggers"], reverse=True)[:3]
    print(f"\n[触发率Top3]:")
    for name, stats in top_triggered:
        print(f"   📈 {name}: {stats['total_triggers']}次 ({stats['trigger_rate_pct']:.2f}%) 趋势:{stats['trend']}")

    es = EffectivenessScorer()
    for i in range(15):
        skill_names = list(manager.all_skills.keys())
        es.record_execution(
            skill_names[i % len(skill_names)],
            success=(i % 7 != 0),
            output_quality=65.0 + (i % 5) * 6,
            execution_time_ms=50.0 + (i % 10) * 30,
        )
    eff_name = skills_data[0]["name"]
    eff_total, eff_dims = es.score_effectiveness(eff_name)
    print(f"\n[{eff_name}] 有效性: {eff_total:.1f}")
    for dim, val in eff_dims.items():
        print(f"   {dim}: {val}")

    st = SatisfactionTracker()
    for i in range(12):
        skill_names = list(manager.all_skills.keys())
        st.record_implicit(skill_names[i % len(skill_names)], adopted=(i % 3 != 0))
    for i in range(8):
        skill_names = list(manager.all_skills.keys())
        st.record_explicit(skill_names[i % len(skill_names)], rating=3 + (i % 3))
    sat_summary = st.get_satisfaction_summary()
    print(f"\n[满意度] 平均: {sat_summary['avg_satisfaction']:.1f}")
    print(f"   隐式反馈: {sat_summary['total_implicit_feedback']}条")
    print(f"   显式反馈: {sat_summary['total_explicit_feedback']}条")

    print("\n--- 完整评估 ---\n")
    report = evaluate(skills_data)
    print(f"\n📋 报告ID: {report.report_id}")
    print(f"📊 总览: {report.summary}")
    print(f"🏆 Top5:")
    for s in report.top_performers:
        icon = "🟢" if s.composite_score >= 70 else ("🟡" if s.composite_score >= 45 else "🔴")
        print(f"   {icon} #{s.rank} {s.skill_name}: {s.composite_score:.1f}")
    print(f"⚠️ Bottom5:")
    for s in report.bottom_performers:
        icon = "🔴" if s.composite_score < 45 else "🟡"
        print(f"   {icon} #{s.rank} {s.skill_name}: {s.composite_score:.1f}")
    print(f"\n📝 行动项:")
    for item in report.action_items:
        print(f"   • {item}")

    print("\n✅ 所有演示通过!")
