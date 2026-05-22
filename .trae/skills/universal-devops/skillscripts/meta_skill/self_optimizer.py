"""
技能自优化器 - 基于评估报告自动生成优化方案
提供描述优化、触发条件调优、内容精炼、性能剖析四大能力
"""
from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


class OptimizationError(Exception):
    """自优化异常"""
    pass


class OptimizationPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class OptimizationAction:
    """单条优化操作"""
    action_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    target_skill: str = ""
    action_type: str = ""
    priority: OptimizationPriority = OptimizationPriority.MEDIUM
    description: str = ""
    current_value: str = ""
    suggested_value: str = ""
    rationale: str = ""
    estimated_impact: str = ""
    effort: str = "small"
    status: str = "pending"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_id": self.action_id,
            "target_skill": self.target_skill,
            "action_type": self.action_type,
            "priority": self.priority.value,
            "description": self.description,
            "current_value": self.current_value,
            "suggested_value": self.suggested_value,
            "rationale": self.rationale,
            "estimated_impact": self.estimated_impact,
            "effort": self.effort,
            "status": self.status,
            "created_at": self.created_at,
        }


@dataclass
class OptimizationPlan:
    """完整优化计划"""
    plan_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    source_report_id: str = ""
    total_actions: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    actions: list[OptimizationAction] = field(default_factory=list)
    summary: str = ""
    estimated_total_effort: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "generated_at": self.generated_at,
            "source_report_id": self.source_report_id,
            "total_actions": self.total_actions,
            "critical_count": self.critical_count,
            "high_count": self.high_count,
            "medium_count": self.medium_count,
            "low_count": self.low_count,
            "actions": [a.to_dict() for a in self.actions],
            "summary": self.summary,
            "estimated_total_effort": self.estimated_total_effort,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


class DescriptionOptimizer:
    """
    描述优化算法

    基于trigger rate低的原因分析，优化SKILL.md的description字段。
    分析描述的清晰度、关键词覆盖度、用户意图匹配度。
    """

    DESCRIPTION_PATTERNS: dict[str, tuple[str, str]] = {
        "too_vague": (
            r"^(负责|处理|管理|进行|实现)\S{0,4}$",
            "描述过于笼统，缺少具体能力边界和适用场景"
        ),
        "missing_keywords": (
            r"(?!(?:API|数据库|测试|部署|架构|文档|安全|性能|DevOps|CI|CD))",
            "描述缺少领域关键词，降低搜索引擎匹配概率"
        ),
        "too_long": (
            r".{120,}",
            "描述过长，建议精简至80字以内以提升可读性"
        ),
        "no_action_verb": (
            r"(?^(?!.*(?:提供|支持|实现|生成|分析|设计|构建|管理|优化|检查)))",
            "缺少动作动词，无法清晰传达技能的核心价值"
        ),
    }

    def __init__(self) -> None:
        self._optimization_history: list[dict[str, Any]] = []

    def analyze_description(
        self, skill_name: str, current_desc: str, trigger_score: float
    ) -> dict[str, Any]:
        """
        分析当前描述的质量问题

        Args:
            skill_name: 技能名称
            current_desc: 当前描述文本
            trigger_score: 触发率得分

        Returns:
            包含诊断结果和建议的字典
        """
        issues: list[dict[str, str]] = []
        score: float = 100.0

        for pattern_name, (pattern, issue_desc) in self.DESCRIPTION_PATTERNS.items():
            if pattern_name == "missing_keywords":
                has_keyword = bool(re.search(
                    r"(?:API|数据库|测试|部署|架构|文档|安全|性能|DevOps|CI|CD|代码|需求|设计)",
                    current_desc
                ))
                if not has_keyword and len(current_desc) > 5:
                    issues.append({
                        "type": pattern_name,
                        "issue": issue_desc,
                        "severity": "medium",
                    })
                    score -= 15
                continue

            match_obj = re.search(pattern, current_desc, re.MULTILINE)
            if match_obj:
                severity = "high" if pattern_name in ("too_vague", "too_long") else "medium"
                issues.append({
                    "type": pattern_name,
                    "issue": issue_desc,
                    "severity": severity,
                })
                penalty = 20 if severity == "high" else 10
                score -= penalty

        if trigger_score < 30 and len(current_desc) < 20:
            issues.append({
                "type": "low_trigger_correlation",
                "issue": f"触发率得分仅{trigger_score:.1f}，描述可能未覆盖常见查询模式",
                "severity": "high",
            })
            score -= 15

        score = max(0.0, min(100.0, score))

        return {
            "skill_name": skill_name,
            "current_description": current_desc,
            "quality_score": round(score, 2),
            "issues": issues,
            "needs_optimization": score < 70 or len(issues) > 1,
        }

    def generate_optimized_description(
        self, skill_name: str, current_desc: str, triggers: list[str], province: str = ""
    ) -> str:
        """
        生成优化后的描述

        基于现有描述、触发词和所属省/部信息，生成更精准的描述
        """
        base_verbs = ["提供", "支持", "实现", "负责"]
        domain_terms = set(triggers)

        clean_triggers = [t for t in triggers if len(t) > 1]
        key_domains = sorted(clean_triggers, key=len, reverse=True)[:3]

        verb = "提供"
        for v in base_verbs:
            if v not in current_desc:
                verb = v
                break

        province_label = {"zhongshusheng": "中书省", "menxiasheng": "门下省", "shangshusheng": "尚书省"}.get(province, "")

        parts = [verb]
        if key_domains:
            domain_str = "、".join(key_domains[:2])
            parts.append(f"{domain_str}等")
        parts.append("能力的")

        core_capability = self._extract_core_capability(current_desc)
        if core_capability:
            parts.append(core_capability)
        else:
            parts.append("全流程解决方案")

        scenario_hints = self._infer_scenario(triggers)
        if scenario_hints:
            parts.append(f"，覆盖{scenario_hints}等场景")

        optimized = "".join(parts)
        if len(optimized) > 100:
            optimized = optimized[:97] + "..."

        self._optimization_history.append({
            "skill_name": skill_name,
            "original": current_desc,
            "optimized": optimized,
            "timestamp": datetime.now().isoformat(),
        })

        return optimized

    def _extract_core_capability(self, desc: str) -> str:
        """从描述中提取核心能力短语"""
        patterns = [
            r"(?:负责|提供|支持|实现)\s*(.+?)(?:[，,。]|$)",
            r"(.+?)(?:能力|功能|服务|系统|平台|工具)",
        ]
        for p in patterns:
            m = re.search(p, desc)
            if m:
                cap = m.group(1).strip()
                if len(cap) >= 4:
                    return cap
        return ""

    def _infer_scenario(self, triggers: list[str]) -> str:
        """根据触发词推断典型使用场景"""
        scenario_map = {
            "测试": "单元/集成/回归测试",
            "部署": "CI/CD流水线与自动化部署",
            "API": "接口设计与文档生成",
            "数据库": "建模/迁移/优化",
            "安全": "合规审计与漏洞扫描",
            "文档": "知识沉淀与技术转移",
            "架构": "技术选型与系统设计",
            "代码": "开发规范与质量保障",
        }
        matched: list[str] = []
        for keyword, scenario in scenario_map.items():
            if any(keyword.lower() in t.lower() for t in triggers):
                matched.append(scenario)
        return "、".join(matched[:3]) if matched else "多种业务"


class TriggerConditionTuner:
    """
    触发条件调优器

    分析误触发/漏触发的模式，调整关键词覆盖范围，
    平衡精确率和召回率。
    """

    def __init__(self) -> None:
        self._false_positive_log: list[dict[str, Any]] = []
        self._false_negative_log: list[dict[str, Any]] = []

    def record_false_positive(
        self, skill_name: str, query: str, reason: str = ""
    ) -> None:
        """记录误触发（不该匹配但匹配了）"""
        self._false_positive_log.append({
            "skill_name": skill_name,
            "query": query[:200],
            "reason": reason,
            "timestamp": datetime.now().isoformat(),
        })

    def record_false_negative(
        self, skill_name: str, missed_query: str, reason: str = ""
    ) -> None:
        """记录漏触发（应该匹配但没匹配到）"""
        self._false_negative_log.append({
            "skill_name": skill_name,
            "missed_query": missed_query[:200],
            "reason": reason,
            "timestamp": datetime.now().isoformat(),
        })

    def analyze_trigger_patterns(
        self, skill_name: str, current_triggers: list[str]
    ) -> dict[str, Any]:
        """
        分析触发条件的问题模式

        Returns:
            包含误触/漏触分析和调优建议的字典
        """
        fp_records = [r for r in self._false_positive_log if r["skill_name"] == skill_name]
        fn_records = [r for r in self._false_negative_log if r["skill_name"] == skill_name]

        fp_queries = [r["query"].lower() for r in fp_records]
        fn_queries = [r["missed_query"].lower() for r in fn_records]

        over_broad: list[str] = []
        under_narrow: list[str] = []

        for trigger in current_triggers:
            t_lower = trigger.lower()
            fp_matches = sum(1 for q in fp_queries if t_lower in q)
            fn_misses = sum(1 for q in fn_queries if t_lower not in q and any(
                kw in q for kw in current_triggers
            ))

            if fp_matches > len(fp_queries) * 0.3 and len(fp_queries) > 3:
                over_broad.append((trigger, fp_matches))
            if fn_misses > len(fn_queries) * 0.3 and len(fn_queries) > 3:
                under_narrow.append(trigger)

        new_candidates: list[str] = self._suggest_new_triggers(fn_queries, current_triggers)

        remove_candidates: list[tuple[str, str]] = [
            (t, f"过宽泛，导致 {cnt} 次误触发") for t, cnt in over_broad
        ]

        precision = 1 - (len(fp_records) / max(len(fp_records) + len(fn_records) + 1, 1))
        recall = 1 - (len(fn_records) / max(len(fp_records) + len(fn_records) + 1, 1))

        return {
            "skill_name": skill_name,
            "current_triggers": current_triggers,
            "false_positives": len(fp_records),
            "false_negatives": len(fn_records),
            "precision": round(precision, 3),
            "recall": round(recall, 3),
            "over_broad_triggers": over_broad,
            "under_narrow_coverage": under_narrow,
            "new_trigger_suggestions": new_candidates[:8],
            "remove_suggestions": remove_candidates,
            "needs_tuning": len(fp_records) > 2 or len(fn_records) > 2,
        }

    def _suggest_new_triggers(
        self, missed_queries: list[str], existing: list[str]
    ) -> list[str]:
        """基于漏触发查询建议新触发词"""
        from collections import Counter

        word_freq: Counter[str] = Counter()
        stop_words = {"的", "是", "我", "要", "在", "和", "了", "与", "或", "对", "如何", "怎么"}

        for query in missed_queries:
            words = re.findall(r'[\u4e00-\u9fff]{2,6}|[a-zA-Z]{3,}', query)
            for w in words:
                w_lower = w.lower()
                if w_lower not in stop_words and not any(
                    e.lower() in w_lower or w_lower in e.lower()
                    for e in existing
                ):
                    word_freq[w] += 1

        return [w for w, _ in word_freq.most_common(12)]


class ContentRefiner:
    """
    内容精炼器

    移除无效指令、补充缺失场景、优化示例代码，
    确保SKILL.md内容质量持续提升。
    """

    INVALID_PATTERNS: list[tuple[str, str, str]] = [
        (r"TODO|FIXME|HACK|XXX", "待办标记", "应替换为已完成的内容或移除"),
        (r"http://example\.com|https://example\.com", "占位URL", "替换为实际资源链接"),
        (r"复制粘贴|copy.paste| boilerplate ", "模板化指令", "根据实际场景定制"),
        (r"\.\.\.(?!$)", "不完整的句子", "补全内容或删除"),
        (r"^#\s*$", "空标题行", "添加有意义的章节标题"),
    ]

    MISSING_SECTIONS: list[tuple[str, str, list[str]]] = [
        ("usage_example", "使用示例", ["## 使用示例", "### 示例"]),
        ("error_handling", "错误处理", ["## 错误处理", "### 异常情况"]),
        ("edge_case", "边缘场景", ["## 边缘场景", "### 特殊情况"]),
        ("best_practice", "最佳实践", ["## 最佳实践", "### 建议"]),
        ("troubleshooting", "故障排查", ["## 故障排查", "### 常见问题"]),
    ]

    def __init__(self) -> None:
        self._refinement_history: list[dict[str, Any]] = []

    def analyze_content(
        self, content: str, skill_name: str = ""
    ) -> dict[str, Any]:
        """
        分析SKILL.md内容质量

        Returns:
            内容质量分析报告
        """
        lines = content.splitlines()
        total_lines = len(lines)
        empty_lines = sum(1 for line in lines if not line.strip())

        invalid_finds: list[dict[str, Any]] = []
        for pattern, label, advice in self.INVALID_PATTERNS:
            matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
            if matches:
                invalid_finds.append({
                    "pattern_label": label,
                    "count": len(matches),
                    "advice": advice,
                    "samples": matches[:3],
                })

        missing_sections: list[dict[str, str]] = []
        for section_key, section_label, markers in self.MISSING_SECTIONS:
            found = any(marker in content for marker in markers)
            if not found:
                missing_sections.append({
                    "key": section_key,
                    "label": section_label,
                    "importance": "high" if section_key in ("usage_example", "error_handling") else "medium",
                })

        code_blocks = re.findall(r'```[\w]*\n(.+?)```', content, re.DOTALL)
        has_examples = len(code_blocks) > 0

        quality_score: float = 100.0
        quality_score -= len(invalid_finds) * 10
        quality_score -= len(missing_sections) * 8
        if not has_examples:
            quality_score -= 12
        if empty_lines / max(total_lines, 1) > 0.4:
            quality_score -= 8
        quality_score = max(0.0, min(100.0, quality_score))

        return {
            "skill_name": skill_name,
            "total_lines": total_lines,
            "empty_line_ratio": round(empty_lines / max(total_lines, 1), 3),
            "has_code_examples": has_examples,
            "code_block_count": len(code_blocks),
            "invalid_patterns": invalid_finds,
            "missing_sections": missing_sections,
            "quality_score": round(quality_score, 2),
            "needs_refinement": quality_score < 75 or len(invalid_finds) > 0,
        }

    def generate_refinement_plan(
        self, analysis: dict[str, Any], skill_name: str = ""
    ) -> list[OptimizationAction]:
        """
        基于分析结果生成精炼操作列表
        """
        actions: list[OptimizationAction] = []

        for inv in analysis.get("invalid_patterns", []):
            actions.append(OptimizationAction(
                target_skill=skill_name,
                action_type="content_remove_invalid",
                priority=OptimizationPriority.HIGH,
                description=f"移除{inv['pattern_label']}: 发现{inv['count']}处",
                current_value=f"包含 {inv['pattern_label']} 模式",
                suggested_value="已清理或替换为有效内容",
                rationale=inv.get("advice", ""),
                estimated_impact="提升内容专业度和可信度",
                effort="small",
            ))

        for missing in analysis.get("missing_sections", []):
            prio = (
                OptimizationPriority.HIGH
                if missing["importance"] == "high"
                else OptimizationPriority.MEDIUM
            )
            actions.append(OptimizationAction(
                target_skill=skill_name,
                action_type="content_add_section",
                priority=prio,
                description=f"补充缺失章节: {missing['label']}",
                current_value="章节不存在",
                suggested_value=f"新增 ## {missing['label']} 章节",
                rationale=f"{missing['label']}章节有助于用户快速上手和排障",
                estimated_impact="降低用户学习成本和使用障碍",
                effort="medium",
            ))

        if not analysis.get("has_code_examples"):
            actions.append(OptimizationAction(
                target_skill=skill_name,
                action_type="content_add_example",
                priority=OptimizationPriority.MEDIUM,
                description="添加使用示例代码块",
                current_value="无代码示例",
                suggested_value="新增 ``` 语言 代码块示例",
                rationale="代码示例是最有效的使用说明形式",
                estimated_impact="显著降低用户尝试门槛",
                effort="medium",
            ))

        self._refinement_history.append({
            "skill_name": skill_name,
            "action_count": len(actions),
            "timestamp": datetime.now().isoformat(),
        })

        return actions


class PerformanceProfiler:
    """
    性能剖析器

    识别耗时子技能，分析执行瓶颈，建议优化方向。
    """

    SLOW_THRESHOLDS: dict[str, tuple[float, str]] = {
        "very_slow": (5000.0, ">5秒 - 严重性能问题"),
        "slow": (2000.0, "2-5秒 - 需要关注"),
        "moderate": (800.0, "0.8-2秒 - 可接受但可优化"),
        "fast": (300.0, "<0.8秒 - 表现良好"),
    }

    def __init__(self) -> None:
        self._execution_profiles: list[dict[str, Any]] = []

    def record_profile(
        self,
        skill_name: str,
        execution_time_ms: float,
        memory_mb: float = 0.0,
        success: bool = True,
        sub_operations: list[dict[str, float]] | None = None,
    ) -> None:
        """记录一次执行的性能剖面数据"""
        self._execution_profiles.append({
            "skill_name": skill_name,
            "execution_time_ms": execution_time_ms,
            "memory_mb": memory_mb,
            "success": success,
            "sub_operations": sub_operations or [],
            "timestamp": datetime.now().isoformat(),
        })

    def load_profiles(self, profiles: list[dict[str, Any]]) -> None:
        """批量加载性能数据"""
        self._execution_profiles.extend(profiles)

    def profile_skills(
        self, all_skill_names: list[str]
    ) -> dict[str, dict[str, Any]]:
        """
        对所有子技能进行性能剖析

        Returns:
            以技能名为键的性能报告字典
        """
        result: dict[str, dict[str, Any]] = {}

        for name in all_skill_names:
            records = [p for p in self._execution_profiles if p["skill_name"] == name]
            if not records:
                result[name] = {
                    "avg_time_ms": 0,
                    "max_time_ms": 0,
                    "min_time_ms": 0,
                    "call_count": 0,
                    "success_rate": 0,
                    "performance_tier": "unknown",
                    "bottleneck_hint": "无足够数据",
                    "optimization_suggestion": "需要更多执行样本",
                }
                continue

            times = [p["execution_time_ms"] for p in records]
            avg_time = sum(times) / len(times)
            max_time = max(times)
            min_time = min(times)
            success_rate = sum(1 for p in records if p["success"]) / len(records)

            tier = "fast"
            tier_label = self.SLOW_THRESHOLDS["fast"][1]
            for threshold_key, (threshold_val, label) in self.SLOW_THRESHOLDS.items():
                if avg_time >= threshold_val:
                    tier = threshold_key
                    tier_label = label
                    break

            bottleneck = self._identify_bottleneck(records)
            suggestion = self._generate_suggestion(name, avg_time, success_rate, tier)

            result[name] = {
                "avg_time_ms": round(avg_time, 2),
                "max_time_ms": round(max_time, 2),
                "min_time_ms": round(min_time, 2),
                "call_count": len(records),
                "success_rate": round(success_rate, 3),
                "performance_tier": tier,
                "tier_description": tier_label,
                "bottleneck_hint": bottleneck,
                "optimization_suggestion": suggestion,
            }

        return result

    def _identify_bottleneck(
        self, records: list[dict[str, Any]]
    ) -> str:
        """识别主要瓶颈来源"""
        slow_records = [r for r in records if r["execution_time_ms"] > 1000]
        if not slow_records:
            return "无明显瓶颈"

        sub_op_totals: dict[str, list[float]] = {}
        for r in slow_records:
            for op in r.get("sub_operations", []):
                op_name = op.get("name", "unknown")
                op_time = op.get("time_ms", 0)
                if op_name not in sub_op_totals:
                    sub_op_totals[op_name] = []
                sub_op_totals[op_name].append(op_time)

        if not sub_op_totals:
            return "整体耗时较长，需进一步分解"

        top_ops = sorted(
            sub_op_totals.items(),
            key=lambda x: sum(x[1]) / len(x[1]),
            reverse=True,
        )[:2]

        hints: list[str] = []
        for op_name, times in top_ops:
            avg = sum(times) / len(times)
            hints.append(f"{op_name}(平均{avg:.0f}ms)")
        return "、".join(hints) if hints else "未知瓶颈"

    def _generate_suggestion(
        self, name: str, avg_time: float, success_rate: float, tier: str
    ) -> str:
        """生成优化建议"""
        suggestions = {
            "very_slow": (
                f"[紧急] {name} 平均响应时间 {avg_time:.0f}ms 过长。"
                f"建议：增加缓存层、异步化I/O操作、拆分为更小的子任务"
            ),
            "slow": (
                f"[关注] {name} 平均响应时间 {avg_time:.0f}ms。"
                f"建议：审查热点路径、减少不必要的计算、考虑预计算"
            ),
            "moderate": (
                f"[可选] {name} 响应时间 {avg_time:.0f}ms 处于临界值。"
                f"建议：监控趋势变化，必要时进行微优化"
            ),
            "fast": f"[良好] {name} 性能表现优秀，保持现状并持续监控",
        }
        base = suggestions.get(tier, "")
        if success_rate < 0.85:
            base += f"; 注意成功率仅{success_rate:.1%}，优先修复稳定性问题"
        return base

    def get_slowest_skills(self, n: int = 5) -> list[tuple[str, float]]:
        """获取最慢的N个技能"""
        skill_times: dict[str, float] = {}
        for p in self._execution_profiles:
            name = p["skill_name"]
            if name not in skill_times:
                skill_times[name] = []
            skill_times[name].append(p["execution_time_ms"])

        averages = [(n, sum(ts) / len(ts)) for n, ts in skill_times.items()]
        return sorted(averages, key=lambda x: x[1], reverse=True)[:n]


def optimize(evaluation_report: Any) -> OptimizationPlan:
    """
    基于评估报告制定完整的优化计划

    整合描述优化、触发条件调优、内容精炼、性能剖析四个维度，
    输出结构化的优化行动清单。

    Args:
        evaluation_report: SkillEvaluationReport评估报告对象

    Returns:
        完整的OptimizationPlan优化计划
    """
    from .self_evaluator import SkillEvaluationReport as _SER

    plan = OptimizationPlan(source_report_id=getattr(evaluation_report, 'report_id', ''))

    desc_optimizer = DescriptionOptimizer()
    trigger_tuner = TriggerConditionTuner()
    content_refiner = ContentRefiner()
    perf_profiler = PerformanceProfiler()

    all_actions: list[OptimizationAction] = []

    for score in evaluation_report.all_scores:
        name = score.skill_name

        if score.trigger_rate_score < 40:
            desc_analysis = desc_optimizer.analyze_description(
                name, getattr(score, 'description', ''), score.trigger_rate_score
            )
            if desc_analysis.get("needs_optimization"):
                all_actions.append(OptimizationAction(
                    target_skill=name,
                    action_type="optimize_description",
                    priority=(
                        OptimizationPriority.CRITICAL
                        if score.trigger_rate_score < 20
                        else OptimizationPriority.HIGH
                    ),
                    description=f"优化{name}的描述以提升触发率（当前:{score.trigger_rate_score:.1f}）",
                    current_value=str(getattr(score, 'description', '(未获取)'))[:80],
                    suggested_value=desc_optimizer.generate_optimized_description(
                        name,
                        getattr(score, 'description', ''),
                        getattr(score, 'triggers', []),
                        score.province,
                    ),
                    rationale=desc_analysis.get("issues", [{}])[0].get("issue", "触发率过低"),
                    estimated_impact="预期触发率提升30-50%",
                    effort="small",
                ))

        if score.health_score < 65:
            all_actions.extend(content_refiner.generate_refinement_plan(
                {
                    "skill_name": name,
                    "invalid_patterns": [{"pattern_label": "文件完整性", "count": 1, "advice": "检查必需文件"}],
                    "missing_sections": [],
                    "has_code_examples": False,
                    "quality_score": score.health_score,
                    "needs_refinement": True,
                },
                skill_name=name,
            ))

        if score.effectiveness_score < 50:
            all_actions.append(OptimizationAction(
                target_skill=name,
                action_type="improve_effectiveness",
                priority=OptimizationPriority.HIGH,
                description=f"提升{name}的有效性（当前:{score.effectiveness_score:.1f}）",
                current_value=f"有效性得分 {score.effectiveness_score:.1f}",
                suggested_value="目标得分 > 70",
                rationale="输出质量和执行稳定性不足",
                estimated_impact="用户体验显著改善",
                effort="medium",
            ))

        if score.satisfaction_score < 55:
            all_actions.append(OptimizationAction(
                target_skill=name,
                action_type="improve_satisfaction",
                priority=OptimizationPriority.MEDIUM,
                description=f"提升{name}的用户满意度（当前:{score.satisfaction_score:.1f}）",
                current_value=f"满意度 {score.satisfaction_score:.1f}",
                suggested_value="目标满意度 > 75",
                rationale="用户反馈不佳，影响整体口碑",
                estimated_impact="用户留存率和推荐率提升",
                effort="large",
            ))

    all_actions.sort(key=lambda a: (
        0 if a.priority == OptimizationPriority.CRITICAL else
        1 if a.priority == OptimizationPriority.HIGH else
        2 if a.priority == OptimizationPriority.MEDIUM else 3
    ))

    critical = sum(1 for a in all_actions if a.priority == OptimizationPriority.CRITICAL)
    high = sum(1 for a in all_actions if a.priority == OptimizationPriority.HIGH)
    medium = sum(1 for a in all_actions if a.priority == OptimizationPriority.MEDIUM)
    low = sum(1 for a in all_actions if a.priority == OptimizationPriority.LOW)

    effort_map = {"small": 1, "medium": 3, "large": 7}
    total_effort_points = sum(effort_map.get(a.effort, 3) for a in all_actions)
    match True:
        case _ if total_effort_points <= 10:
            effort_str = "小型优化（约1-2天）"
        case _ if total_effort_points <= 30:
            effort_str = "中型优化（约3-5天）"
        case _ if total_effort_points <= 60:
            effort_str = "大型优化（约1-2周）"
        case _:
            effort_str = "重大优化（超过2周）"

    plan.actions = all_actions
    plan.total_actions = len(all_actions)
    plan.critical_count = critical
    plan.high_count = high
    plan.medium_count = medium
    plan.low_count = low
    plan.estimated_total_effort = effort_str
    plan.summary = (
        f"基于评估报告 {evaluation_report.report_id} 生成优化计划，"
        f"共 {len(all_actions)} 项优化行动 "
        f"(🔴{critical} 🟠{high} 🟡{medium} 🔵{low})"
    )

    print(f"✅ 优化计划已生成 ({plan.plan_id}): {plan.summary}")
    return plan


if __name__ == "__main__":
    from ..utils.subskill_manager import SubSkillManager
    from .self_evaluator import evaluate, SkillEvaluationReport, SubSkillScore, SkillHealthStatus

    print("=" * 60)
    print("🧪 技能自优化器 - 功能演示")
    print("=" * 60)

    manager = SubSkillManager()
    skills_data = [info.to_dict() for info in manager.all_skills.values()]

    print("\n--- 创建模拟评估报告 ---\n")
    mock_scores: list[SubSkillScore] = []
    for i, info in enumerate(manager.all_skills.values()):
        mock_scores.append(SubSkillScore(
            skill_name=info.name,
            province=info.province,
            department=info.department or "",
            health_score=max(30.0, 100.0 - i * 2),
            trigger_rate_score=max(10.0, 90.0 - i * 2.5),
            effectiveness_score=max(25.0, 85.0 - i * 1.8),
            satisfaction_score=max(40.0, 95.0 - i * 1.5),
            composite_score=0,
            rank=0,
            health_status=SkillHealthStatus.HEALTHY if i < 20 else SkillHealthStatus.DEGRADED,
            triggers=list(info.triggers),
            description=info.description,
        ))
    mock_scores.sort(key=lambda s: s.composite_score, reverse=True)
    for i, s in enumerate(mock_scores):
        s.rank = i + 1
        s.composite_score = (
            s.health_score * 0.25 +
            s.trigger_rate_score * 0.25 +
            s.effectiveness_score * 0.30 +
            s.satisfaction_score * 0.20
        )

    report = SkillEvaluationReport(
        total_skills=len(mock_scores),
        healthy_count=20,
        degraded_count=8,
        broken_count=3,
        missing_count=1,
        avg_composite_score=sum(s.composite_score for s in mock_scores) / len(mock_scores),
        top_performers=mock_scores[:5],
        bottom_performers=mock_scores[-5:],
        all_scores=mock_scores,
        summary="模拟评估报告用于演示",
    )

    print(f"   技能数: {report.total_scores}")
    print(f"   均分: {report.avg_composite_score:.1f}")

    print("\n--- 描述优化器 ---\n")
    do = DescriptionOptimizer()
    sample_info = list(manager.all_skills.values())[0]
    analysis = do.analyze_description(sample_info.name, sample_info.description, 35.0)
    print(f"[{sample_info.name}] 描述质量: {analysis['quality_score']}")
    for issue in analysis['issues']:
        print(f"   ⚠️ [{issue['type']}] {issue['issue']}")
    optimized = do.generate_optimized_description(
        sample_info.name, sample_info.description, list(sample_info.triggers), sample_info.province
    )
    print(f"   ✨ 优化后: {optimized}")

    print("\n--- 触发条件调优 ---\n")
    tct = TriggerConditionTuner()
    for i in range(10):
        names = list(manager.all_skills.keys())
        tct.record_false_positive(names[i % len(names)], f"不相关查询{i}", "上下文不匹配")
        tct.record_false_negative(names[(i + 3) % len(names)], f"应该匹配的查询{i}", "关键词缺失")
    trigger_analysis = tct.analyze_trigger_patterns(
        sample_info.name, list(sample_info.triggers)
    )
    print(f"[{sample_info.name}] 精确率: {trigger_analysis['precision']:.2%}")
    print(f"   召回率: {trigger_analysis['recall']:.2%}")
    print(f"   新触发词建议: {trigger_analysis['new_trigger_suggestions'][:5]}")

    print("\n--- 内容精炼 ---\n")
    cr = ContentRefiner()
    sample_content = f"# {sample_info.name}\n\n{sample_info.description}\n\nTODO: 补充示例\n\nhttp://example.com/api"
    cr_analysis = cr.analyze_content(sample_content, sample_info.name)
    print(f"[{sample_info.name}] 质量分: {cr_analysis['quality_score']}")
    print(f"   无效模式: {len(cr_analysis['invalid_patterns'])} 个")
    print(f"   缺失章节: {[m['label'] for m in cr_analysis['missing_sections']]}")
    ref_actions = cr.generate_refinement_plan(cr_analysis, sample_info.name)
    print(f"   生成操作: {len(ref_actions)} 条")

    print("\n--- 性能剖析 ---\n")
    pp = PerformanceProfiler()
    names = list(manager.all_skills.keys())
    for i in range(40):
        pp.record_profile(
            names[i % len(names)],
            execution_time_ms=100.0 + (i % 15) * 250 + (i % 7) * 150,
            memory_mb=20.0 + (i % 10) * 5,
            success=(i % 8 != 0),
        )
    profiles = pp.profile_profiles(names)
    slowest = pp.get_slowest_skills(3)
    print(f"   最慢技能:")
    for sk_name, avg_t in slowest:
        prof = profiles.get(sk_name, {})
        print(f"      🐌 {sk_name}: 平均 {avg_t:.0f}ms ({prof.get('performance_tier', '?')})")

    print("\n--- 完整优化计划 ---\n")
    opt_plan = optimize(report)
    print(f"📋 计划ID: {opt_plan.plan_id}")
    print(f"📊 总览: {opt_plan.summary}")
    print(f"⏱️ 工作量: {opt_plan.estimated_total_effort}")
    print(f"\n🔴 关键操作:")
    for a in opt_plan.actions[:5]:
        print(f"   [{a.priority.value}] {a.target_skill}: {a.description[:60]}")
    print(f"\n   ... 共 {opt_plan.total_actions} 项操作")

    print("\n✅ 所有演示通过!")
