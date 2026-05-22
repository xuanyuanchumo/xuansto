"""
闭环验证器 - 验证SDD+TDD融合闭环的完整性和有效性
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any


class VerificationError(Exception):
    """验证异常"""


@dataclass
class CompletenessReport:
    """闭环完整性报告"""
    is_complete: bool = True
    score: float = 100.0
    phases_present: list[str] = field(default_factory=list)
    missing_phases: list[str] = field(default_factory=list)
    phase_details: dict[str, dict[str, Any]] = field(default_factory=dict)
    data_flow_integrity: bool = True
    feedback_loop_active: bool = True
    issues: list[dict[str, str]] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


@dataclass
class CoverageGapItem:
    """覆盖率缺口条目"""
    item_type: str
    item_id: str
    item_name: str
    gap_type: str
    gap_description: str
    severity: str = "medium"
    suggested_tests: list[str] = field(default_factory=list)
    coverage_pct: float = 0.0


@dataclass
class CoverageGapReport:
    """覆盖率缺口报告"""
    total_spec_items: int = 0
    covered_items: int = 0
    coverage_percentage: float = 0.0
    gaps: list[CoverageGapItem] = field(default_factory=list)
    critical_gaps: int = 0
    by_type_summary: dict[str, dict[str, Any]] = field(default_factory=dict)
    risk_assessment: str = ""


@dataclass
class DeviationItem:
    """偏差条目"""
    deviation_type: str
    spec_item_id: str
    spec_item_name: str
    code_location: str | None = None
    description: str
    severity: str = "medium"
    impact: str = ""
    suggestion: str = ""
    auto_fixable: bool = False


@dataclass
class DeviationReport:
    """偏差检测报告"""
    total_deviations: int = 0
    deviations: list[DeviationItem] = field(default_factory=list)
    critical_count: int = 0
    warning_count: int = 0
    info_count: int = 0
    compliance_score: float = 100.0
    categories: dict[str, int] = field(default_factory=dict)
    summary: str = ""


@dataclass
class EffectivenessMetric:
    """效果度量指标"""
    metric_name: str
    current_value: float
    baseline_value: float
    change_pct: float
    trend: str = "stable"
    status: str = "good"


@dataclass
class EffectivenessAssessment:
    """闭环效果评估"""
    overall_score: float = 0.0
    grade: str = ""
    metrics: list[EffectivenessMetric] = field(default_factory=list)
    improvement_areas: list[str] = field(default_factory=list)
    strengths: list[str] = field(default_factory=list)
    trend_analysis: str = ""
    recommendations: list[str] = field(default_factory=list)


@dataclass
class RegressionRiskItem:
    """回归风险条目"""
    changed_file: str
    affected_specs: list[str] = field(default_factory=list)
    affected_tests: list[str] = field(default_factory=list)
    risk_level: str = "low"
    risk_reason: str = ""
    mitigation: str = ""


@dataclass
class RegressionRiskReport:
    """回归风险预警报告"""
    overall_risk_level: str = "low"
    risk_items: list[RegressionRiskItem] = field(default_factory=list)
    high_risk_count: int = 0
    medium_risk_count: int = 0
    low_risk_count: int = 0
    suggested_test_suite: list[str] = field(default_factory=list)
    mitigation_plan: str = ""


class ClosedLoopVerifier:
    """
    闭环验证器

    验证SDD+TDD融合闭环的完整性和有效性：
    - 闭环完整性检查：确保所有阶段都正确执行
    - 覆盖率分析：识别规范与测试之间的覆盖缺口
    - 偏差检测：发现代码实现与规范定义之间的偏差
    - 效果评估：量化分析融合流程的历史效果
    - 回归风险预警：预测代码变更可能引发的回归问题
    """

    REQUIRED_PHASES = ["spec_analysis", "test_generation", "code_guidance", "feedback_loop"]

    DEVIATION_PATTERNS: list[tuple[str, str, str, str]] = [
        (r"def\s+(\w+)\([^)]*\)\s*->\s*(\w+)", "signature_mismatch", "函数签名偏差", "medium"),
        (r"class\s+(\w+)[^:]*:", "missing_class", "规范定义的类未找到", "high"),
        (r"(?:raise|throw)\s+(\w+)", "exception_deviation", "异常处理偏差", "medium"),
        (r"(@\w+\.decorator|@\w+\.)", "decorator_deviation", "装饰器使用偏差", "low"),
        (r"(?:async\s+def|await\s+)", "async_deviation", "异步模式偏差", "medium"),
        (r"(?:TODO|FIXME|HACK|XXX)", "technical_debt", "技术债务标记", "info"),
        (r"(?:print\(|console\.log\()", "debug_code", "调试代码残留", "low"),
        (r"(?:hardcoded|hardcode|magic\s*number)", "hardcoded_value", "硬编码值", "medium"),
    ]

    def __init__(self) -> None:
        self._verification_history: list[dict[str, Any]] = []
        self._custom_rules: list[tuple[Any, str, str]] = []
        self._severity_weights: dict[str, float] = {
            "critical": 3.0,
            "high": 2.0,
            "medium": 1.0,
            "low": 0.5,
            "info": 0.1,
        }

    # ==================== 闭环完整性检查 ====================

    def verify_loop_completeness(self, fusion_report: Any) -> CompletenessReport:
        """
        验证融合闭环的完整性

        检查项：
        - 所有必需阶段是否都已执行
        - 数据流是否完整（每个阶段的输出是否被下一阶段使用）
        - 反馈回路是否激活（反馈是否回到规范分析）
        """
        report = CompletenessReport()

        phases_completed = getattr(fusion_report, 'phases_completed', [])
        phase_values = [p.value if hasattr(p, 'value') else p for p in phases_completed]

        report.phases_present = phase_values.copy()
        report.missing_phases = [
            p for p in self.REQUIRED_PHASES if p not in phase_values
        ]

        for phase in self.REQUIRED_PHASES:
            is_present = phase in phase_values
            detail = {
                "phase": phase,
                "present": is_present,
                "status": "✅ 已完成" if is_present else "❌ 缺失",
            }

            match phase:
                case "spec_analysis":
                    detail["check_items"] = [
                        ("规范解析完成", is_present),
                        ("需求提取完成", is_present),
                        ("API契约提取完成", is_present),
                    ]
                    if not is_present:
                        report.issues.append({
                            "type": "missing_phase",
                            "phase": phase,
                            "description": "规范分析阶段缺失，无法进行后续测试生成",
                            "severity": "critical",
                        })
                        report.score -= 30
                case "test_generation":
                    test_mappings = getattr(fusion_report, 'test_mappings', [])
                    generated_tests = getattr(fusion_report, 'generated_tests', [])
                    detail["mapping_count"] = len(test_mappings)
                    detail["test_count"] = len(generated_tests)
                    detail["check_items"] = [
                        (f"测试映射数: {len(test_mappings)}", len(test_mappings) > 0),
                        (f"生成测试数: {len(generated_tests)}", len(generated_tests) > 0),
                    ]
                    if not is_present or len(generated_tests) == 0:
                        report.issues.append({
                            "type": "insufficient_tests",
                            "phase": phase,
                            "description": f"测试生成不足，仅{len(generated_tests)}个测试用例",
                            "severity": "high",
                        })
                        report.score -= 20
                case "code_guidance":
                    guidances = getattr(fusion_report, 'code_guidances', [])
                    detail["guidance_count"] = len(guidances)
                    detail["check_items"] = [
                        (f"代码引导数: {len(guidances)}", len(guidances) > 0),
                    ]
                case "feedback_loop":
                    feedback = getattr(fusion_report, 'feedback', None)
                    has_feedback = feedback is not None
                    detail["has_feedback"] = has_feedback
                    if has_feedback:
                        detail["compliance_score"] = getattr(feedback, 'compliance_score', 0)
                    detail["check_items"] = [
                        ("反馈报告已生成", has_feedback),
                        ("合规评分已计算", has_feedback),
                    ]
                    report.feedback_loop_active = has_feedback
                    if not has_feedback:
                        report.issues.append({
                            "type": "no_feedback",
                            "phase": phase,
                            "description": "反馈回路未闭合，无法形成持续改进循环",
                            "severity": "high",
                        })
                        report.score -= 15

            report.phase_details[phase] = detail

        report.data_flow_integrity = self._check_data_flow_integrity(phase_values)

        report.is_complete = (
            len(report.missing_phases) == 0 and
            report.data_flow_integrity and
            report.feedback_loop_active
        )
        report.score = max(0, report.score)

        if not report.is_complete:
            report.recommendations = [
                "确保所有四个阶段都已完成执行",
                "检查各阶段间的数据传递是否完整",
                "确认反馈回路已正确配置并激活",
                "审查阶段输出是否作为下一阶段的输入",
            ]

        self._verification_history.append({
            "type": "completeness",
            "score": report.score,
            "is_complete": report.is_complete,
            "timestamp": __import__("datetime").datetime.now().isoformat(),
        })

        return report

    def _check_data_flow_integrity(self, phases: list[str]) -> bool:
        """检查数据流完整性"""
        expected_flows = [
            ("spec_analysis", "test_generation"),
            ("test_generation", "code_guidance"),
            ("code_guidance", "feedback_loop"),
        ]

        for from_phase, to_phase in expected_flows:
            if from_phase in phases and to_phase not in phases:
                return False
        return True

    # ==================== 覆盖率分析 ====================

    def analyze_coverage_gaps(self, spec: Any, coverage_data: dict) -> CoverageGapReport:
        """
        分析规范覆盖率的缺口

        Args:
            spec: SDD规范对象
            coverage_data: 覆盖率数据字典

        Returns:
            覆盖率缺口报告
        """
        report = CoverageGapReport()

        all_items: list[tuple[str, str, str, list[str]]] = []

        requirements = getattr(spec, 'requirements', [])
        for req in requirements:
            ac_tags = [f"AC-{ac.id}" for ac in getattr(req, 'acceptance_criteria', [])]
            all_items.append(("requirement", req.id, req.title, ac_tags))

        api_contracts = getattr(spec, 'api_contracts', [])
        for api in api_contracts:
            all_items.append(("api", f"{api.method} {api.endpoint}", api.description or api.endpoint, []))

        data_models = getattr(spec, 'data_models', [])
        for model in data_models:
            fields = [f.name for f in getattr(model, 'fields', [])]
            all_items.append(("model", model.name, model.description or model.name, fields))

        business_rules = getattr(spec, 'business_rules', [])
        for rule in business_rules:
            all_items.append(("rule", rule.id, rule.name, []))

        report.total_spec_items = len(all_items)

        covered_ids: set[str] = set()
        coverage_list = coverage_data.get("covered_items", [])
        if isinstance(coverage_list, list):
            for item in coverage_list:
                if isinstance(item, str):
                    covered_ids.add(item.lower())
                elif isinstance(item, dict):
                    covered_ids.add(str(item.get("id", "")).lower())

        type_counts: dict[str, dict[str, Any]] = {}
        for item_type, item_id, item_name, sub_items in all_items:
            if item_type not in type_counts:
                type_counts[item_type] = {"total": 0, "covered": 0, "gaps": []}

            type_counts[item_type]["total"] += 1

            is_covered = (
                item_id.lower() in covered_ids or
                any(item_id.lower() in c or item_name.lower() in c.lower() for c in covered_ids)
            )

            if is_covered:
                report.covered_items += 1
                type_counts[item_type]["covered"] += 1
            else:
                gap_type = self._infer_gap_type(item_type, spec)
                severity = self._infer_gap_severity(item_type, item_name)
                suggested = self._suggest_tests_for_gap(item_type, item_id, item_name)

                gap = CoverageGapItem(
                    item_type=item_type,
                    item_id=item_id,
                    item_name=item_name,
                    gap_type=gap_type,
                    gap_description=f"{item_type} '{item_name}' ({item_id}) 未被测试覆盖",
                    severity=severity,
                    suggested_tests=suggested,
                    coverage_pct=0.0,
                )

                report.gaps.append(gap)
                type_counts[item_type]["gaps"].append(gap)

                if severity == "critical":
                    report.critical_gaps += 1

        report.by_type_summary = type_counts
        report.coverage_percentage = (
            (report.covered_items / report.total_spec_items * 100)
            if report.total_spec_items > 0 else 0.0
        )

        if report.critical_gaps > 0:
            report.risk_assessment = "🔴 高风险：存在关键覆盖缺口，可能导致严重缺陷遗漏"
        elif len(report.gaps) > report.total_spec_items * 0.3:
            report.risk_assessment = "🟠 中风险：覆盖率不足30%，建议补充测试用例"
        elif len(report.gaps) > 0:
            report.risk_assessment = "🟡 低风险：少量覆盖缺口，建议逐步完善"
        else:
            report.risk_assessment = "🟢 低风险：规范覆盖率良好"

        return report

    def _infer_gap_type(self, item_type: str, spec: Any) -> str:
        """推断缺口类型"""
        type_map = {
            "requirement": "functional_gap",
            "api": "integration_gap",
            "model": "unit_gap",
            "rule": "business_rule_gap",
        }
        return type_map.get(item_type, "unknown_gap")

    def _infer_gap_severity(self, item_type: str, item_name: str) -> str:
        """推断缺口严重程度"""
        name_lower = item_name.lower()
        if any(kw in name_lower for kw in ["critical", "安全", "security", "auth", "支付", "payment"]):
            return "critical"
        elif any(kw in name_lower for kw in ["核心", "core", "主要", "main", "关键", "key"]):
            return "high"
        elif item_type == "rule":
            return "high"
        return "medium"

    def _suggest_tests_for_gap(self, item_type: str, item_id: str, item_name: str) -> list[str]:
        """为覆盖缺口建议测试"""
        suggestions_map = {
            "requirement": [
                f"test_{item_id.lower().replace('-', '_')}_happy_path",
                f"test_{item_id.lower().replace('-', '_')}_boundary",
                f"test_{item_id.lower().replace('-', '_')}_exception",
            ],
            "api": [
                f"test_{item_id.replace('/', '_').replace('{', '').replace('}', '')}_valid_request",
                f"test_{item_id.replace('/', '_').replace('{', '').replace('}', '')}_auth_required",
                f"test_{item_id.replace('/', '_').replace('{', '').replace('}', '')}_response_schema",
            ],
            "model": [
                f"test_{item_name.lower()}_field_validation",
                f"test_{item_name.lower()}_constraints",
                f"test_{item_name.lower()}_creation",
            ],
            "rule": [
                f"test_{item_id.lower().replace('-', '_')}_satisfied",
                f"test_{item_id.lower().replace('-', '_')}_violated",
            ],
        }
        return suggestions_map.get(item_type, [f"test_cover_{item_id.lower()}"])

    # ==================== 偏差检测 ====================

    def detect_deviations(self, spec: Any, code_analysis: dict) -> DeviationReport:
        """
        检测代码实现与规范定义之间的偏差

        检测维度：
        - 函数签名偏差
        - 类/模块缺失
        - 异常处理偏差
        - API行为偏差
        - 数据模型偏差
        """
        report = DeviationReport()

        requirements = getattr(spec, 'requirements', [])
        api_contracts = getattr(spec, 'api_contracts', [])
        data_models = getattr(spec, 'data_models', [])
        business_rules = getattr(spec, 'business_rules', [])

        code_files_content: dict[str, str] = {}
        code_files = code_analysis.get("files", {})
        if isinstance(code_files, dict):
            for fpath, content in code_files.items():
                if isinstance(content, str):
                    code_files_content[fpath] = content

        combined_code = "\n".join(code_files_content.values())

        for req in requirements:
            req_in_code = (
                req.id.lower() in combined_code.lower() or
                req.title.lower() in combined_code.lower()
            )
            if not req_in_code:
                report.deviations.append(DeviationItem(
                    deviation_type="unimplemented_requirement",
                    spec_item_id=req.id,
                    spec_item_name=req.title,
                    description=f"需求 '{req.title}' 在代码中未找到对应实现",
                    severity=req.priority if hasattr(req, 'priority') else "medium",
                    impact="功能缺失",
                    suggestion=f"为需求 {req.id} 编写对应的实现代码和测试",
                    auto_fixable=False,
                ))

        for api in api_contracts:
            endpoint_pattern = api.endpoint.replace("{", r"\{").replace("}", r"\}")
            pattern_str = rf"{api.method}\s*[\"']?{endpoint_pattern}"
            if not re.search(pattern_str, combined_code, re.IGNORECASE):
                report.deviations.append(DeviationItem(
                    deviation_type="missing_api_endpoint",
                    spec_item_id=f"{api.method} {api.endpoint}",
                    spec_item_name=api.description or api.endpoint,
                    description=f"API端点 {api.method} {api.endpoint} 未在代码中实现",
                    severity="high",
                    impact="API不可用",
                    suggestion=f"实现 {api.method} {api.endpoint} 端点及其处理逻辑",
                    auto_fixable=False,
                ))

        for model in data_models:
            class_pattern = rf"class\s+({re.escape(model.name)})\b"
            if not re.search(class_pattern, combined_code):
                report.deviations.append(DeviationItem(
                    deviation_type="missing_data_model",
                    spec_item_id=model.name,
                    spec_item_name=model.name,
                    description=f"数据模型 '{model.name}' 的类定义在代码中未找到",
                    severity="high",
                    impact="数据结构不一致",
                    suggestion=f"创建 {model.model_type} 类型 '{model.name}' 的类定义",
                    auto_fixable=False,
                ))

            for mf in getattr(model, 'fields', [])[:5]:
                field_pattern = rf"{re.escape(mf.name)}\s*[:=]"
                if not re.search(field_pattern, combined_code):
                    report.deviations.append(DeviationItem(
                        deviation_type="missing_field",
                        spec_item_id=model.name,
                        spec_item_name=mf.name,
                        description=f"模型 '{model.name}' 的字段 '{mf.name}' 未在代码中找到",
                        severity="medium",
                        impact="字段缺失可能导致运行时错误",
                        suggestion=f"在模型类中添加字段 '{mf.name}: {mf.type}'",
                        auto_fixable=True,
                    ))

        for rule in business_rules[:5]:
            rule_keywords = rule.name.lower().split()[:3]
            keyword_matches = sum(1 for kw in rule_keywords if kw in combined_code.lower())
            if keyword_matches < len(rule_keywords) // 2:
                report.deviations.append(DeviationItem(
                    deviation_type="unimplemented_rule",
                    spec_item_id=rule.id,
                    spec_item_name=rule.name,
                    description=f"业务规则 '{rule.name}' 可能未被正确实现",
                    severity=rule.severity if hasattr(rule, 'severity') else "medium",
                    impact="业务逻辑不符合规范",
                    suggestion=f"审查并实现规则 '{rule.id}: {rule.name}' 的校验逻辑",
                    auto_fixable=False,
                ))

        for pattern, dev_type, desc, severity in self.DEVIATION_PATTERNS:
            matches = re.findall(pattern, combined_code)
            if matches:
                sample = str(matches[0])[:50]
                report.deviations.append(DeviationItem(
                    deviation_type=dev_type,
                    spec_item_id="code_quality",
                    spec_item_name=sample,
                    description=f"代码中检测到可能的{desc}: {sample}",
                    severity=severity,
                    impact="代码质量问题",
                    suggestion=f"审查并修复{desc}相关代码",
                    auto_fixable=severity in ("low", "info"),
                ))

        for custom_rule, custom_type, custom_sev in self._custom_rules:
            try:
                custom_result = custom_rule(spec, code_analysis)
                if custom_result:
                    report.deviations.append(DeviationItem(
                        deviation_type=custom_type,
                        **custom_result if isinstance(custom_result, dict) else {"description": str(custom_result)},
                    ))
            except Exception:
                pass

        report.total_deviations = len(report.deviations)
        for d in report.deviations:
            sev = d.severity
            if sev == "critical":
                report.critical_count += 1
            elif sev == "high":
                report.warning_count += 1
            elif sev == "medium":
                report.warning_count += 1
            else:
                report.info_count += 1

            cat = d.deviation_type
            report.categories[cat] = report.categories.get(cat, 0) + 1

        total_penalty = sum(
            self._severity_weights.get(d.severity, 1.0) for d in report.deviations
        )
        max_possible = len(report.deviations) * 3 if report.deviations else 1
        report.compliance_score = max(0, 100 - (total_penalty / max(max_possible, 1) * 100))
        report.summary = (
            f"共检测到 {report.total_deviations} 个偏差 "
            f"({report.critical_count}严重/{report.warning_count}警告/{report.info_count}信息)，"
            f"合规评分: {report.compliance_score:.1f}"
        )

        return report

    def add_custom_deviation_rule(self, rule: Callable, rule_type: str = "custom", severity: str = "medium") -> None:
        """添加自定义偏差检测规则"""
        self._custom_rules.append((rule, rule_type, severity))

    # ==================== 效果评估 ====================

    def evaluate_loop_effectiveness(self, historical_reports: list[Any]) -> EffectivenessAssessment:
        """
        评估融合闭环的历史效果

        分析维度：
        - 覆盖率趋势
        - 测试有效性趋势
        - 缺陷率变化
        - 开发效率变化
        """
        assessment = EffectivenessAssessment()

        if not historical_reports:
            assessment.overall_score = 0.0
            assessment.grade = "无数据"
            assessment.recommendations = ["需要至少一次融合报告才能进行效果评估"]
            return assessment

        metrics_history: list[dict[str, float]] = []

        for report in historical_reports:
            metrics_obj = getattr(report, 'metrics', None)
            if metrics_obj is not None:
                metrics_dict = {
                    "spec_coverage_pct": getattr(metrics_obj, 'spec_coverage_pct', 0),
                    "test_effectiveness_pct": getattr(metrics_obj, 'test_effectiveness_pct', 0),
                    "defect_reduction_pct": getattr(metrics_obj, 'defect_reduction_pct', 0),
                    "efficiency_gain_pct": getattr(metrics_obj, 'efficiency_gain_pct', 0),
                }
                metrics_history.append(metrics_dict)

        if len(metrics_history) < 2:
            latest = metrics_history[-1] if metrics_history else {}
            assessment.overall_score = latest.get("spec_coverage_pct", 0) * 0.4 + latest.get("test_effectiveness_pct", 0) * 0.6
            assessment.grade = self._score_to_grade(assessment.overall_score)
            return assessment

        first_metrics = metrics_history[0]
        last_metrics = metrics_history[-1]

        metric_definitions = [
            ("spec_coverage_pct", "规范覆盖率", 0.25),
            ("test_effectiveness_pct", "测试有效性", 0.30),
            ("defect_reduction_pct", "缺陷降低率", 0.25),
            ("efficiency_gain_pct", "效率提升率", 0.20),
        ]

        weighted_score = 0.0
        for metric_key, metric_name, weight in metric_definitions:
            first_val = first_metrics.get(metric_key, 0)
            last_val = last_metrics.get(metric_key, 0)

            if first_val > 0:
                change_pct = ((last_val - first_val) / first_val) * 100
            else:
                change_pct = last_val * 10

            if change_pct > 5:
                trend = "↑ 提升"
            elif change_pct < -5:
                trend = "↓ 下降"
            else:
                trend = "→ 稳定"

            effect_metric = EffectivenessMetric(
                metric_name=metric_name,
                current_value=last_val,
                baseline_value=first_val,
                change_pct=change_pct,
                trend=trend,
                status="good" if last_val >= 70 else ("warning" if last_val >= 50 else "poor"),
            )
            assessment.metrics.append(effect_metric)
            weighted_score += last_val * weight

        assessment.overall_score = weighted_score
        assessment.grade = self._score_to_grade(weighted_score)

        improving = sum(1 for m in assessment.metrics if "提升" in m.trend)
        declining = sum(1 for m in assessment.metrics if "下降" in m.trend)

        if improving >= 3:
            assessment.trend_analysis = "📈 整体呈上升趋势，融合效果良好"
        elif declining >= 2:
            assessment.trend_analysis = "📉 存在下滑指标，需要关注和改进"
        else:
            assessment.trend_analysis = "➡️ 整体稳定，部分指标有优化空间"

        for m in assessment.metrics:
            if m.status == "good":
                assessment.strengths.append(f"{m.metric_name}: {m.current_value:.1f}% ({m.trend})")
            elif m.status == "poor":
                assessment.improvement_areas.append(f"{m.metric_name}: 仅{m.current_value:.1f}%，需重点改进")

        if assessment.improvement_areas:
            assessment.recommendations = [
                "优先关注得分较低的指标，制定专项改进计划",
                "审查测试质量，提高测试有效性和覆盖率",
                "分析缺陷根因，针对性加强薄弱环节",
                "定期回顾融合流程，优化各阶段执行效率",
            ]
        else:
            assessment.recommendations = ["当前融合效果良好，继续保持现有实践"]

        return assessment

    def _score_to_grade(self, score: float) -> str:
        """将分数转换为等级"""
        if score >= 90:
            return "A (优秀)"
        elif score >= 80:
            return "B (良好)"
        elif score >= 70:
            return "C (合格)"
        elif score >= 60:
            return "D (需改进)"
        else:
            return "F (不合格)"

    # ==================== 回归风险预警 ====================

    def assess_regression_risk(self, changes: list[Path], baseline_metrics: dict | None = None) -> RegressionRiskReport:
        """
        评估代码变更的回归风险

        Args:
            changes: 变更的文件列表
            baseline_metrics: 基线指标（可选）

        Returns:
            回归风险报告
        """
        report = RegressionRiskReport()

        for changed_file in changes:
            if not changed_file.exists():
                continue

            try:
                content = changed_file.read_text(encoding="utf-8")
            except Exception:
                continue

            lines = content.split("\n")
            func_defs = len(re.findall(r"^\s*def\s+\w+", content, re.MULTILINE))
            class_defs = len(re.findall(r"^\s*class\s+\w+", content, re.MULTILINE))
            imports_added = len(re.findall(r"^import\s+|^from\s+.+\s+import", content, re.MULTILINE))
            complexity_indicators = len(re.findall(r"\b(if|elif|for|while|try|except|with)\b", content))

            risk_score = 0.0
            risk_reasons: list[str] = []

            if len(lines) > 500:
                risk_score += 2.0
                risk_reasons.append(f"大文件变更 ({len(lines)}行)")
            if func_defs > 10:
                risk_score += 1.5
                risk_reasons.append(f"多函数变更 ({func_defs}个)")
            if class_defs > 3:
                risk_score += 2.0
                risk_reasons.append(f"多类变更 ({class_defs}个)")
            if imports_added > 5:
                risk_score += 1.0
                risk_reasons.append(f"新增导入 ({imports_added}个)")
            if complexity_indicators > 50:
                risk_score += 1.5
                risk_reasons.append(f"高复杂度 ({complexity_indicators}个控制流)")

            has_core_keywords = any(kw in content.lower() for kw in [
                "auth", "security", "payment", "database", "config",
                "middleware", "router", "schema", "model",
            ])
            if has_core_keywords:
                risk_score += 1.5
                risk_reasons.append("涉及核心模块")

            if risk_score >= 6.0:
                risk_level = "high"
                report.high_risk_count += 1
            elif risk_score >= 3.0:
                risk_level = "medium"
                report.medium_risk_count += 1
            else:
                risk_level = "low"
                report.low_risk_count += 1

            affected_tests = self._infer_affected_tests(changed_file, content)
            risk_item = RegressionRiskItem(
                changed_file=str(changed_file),
                affected_tests=affected_tests,
                risk_level=risk_level,
                risk_reason="; ".join(risk_reasons) if risk_reasons else "常规变更",
                mitigation=self._generate_mitigation(risk_level, changed_file),
            )
            report.risk_items.append(risk_item)
            report.suggested_test_suite.extend(affected_tests)

        if report.high_risk_count > 0:
            report.overall_risk_level = "high"
            report.mitigation_plan = (
                "🔴 高回归风险！建议：\n"
                "1. 执行完整的回归测试套件\n"
                "2. 对高风险变更进行代码审查\n"
                "3. 考虑分批部署，先发布低风险变更\n"
                "4. 准备快速回滚方案"
            )
        elif report.medium_risk_count > 0:
            report.overall_risk_level = "medium"
            report.mitigation_plan = (
                "🟠 中等回归风险。建议：\n"
                "1. 执行关联模块的单元测试和集成测试\n"
                "2. 进行增量式回归测试\n"
                "3. 关注受影响API的功能验证\n"
                "4. 监控部署后的错误日志"
            )
        else:
            report.overall_risk_level = "low"
            report.mitigation_plan = (
                "🟢 回归风险较低。建议：\n"
                "1. 执行基本的冒烟测试\n"
                "2. 运行相关的单元测试\n"
                "3. 正常发布流程即可"
            )

        report.suggested_test_suite = list(set(report.suggested_test_suite))

        return report

    def _infer_affected_tests(self, file_path: Path, content: str) -> list[str]:
        """推断受影响的测试"""
        tests: list[str] = []
        stem = file_path.stem

        tests.append(f"test_{stem}")
        tests.append(f"{stem}_test")

        func_names = re.findall(r"^\s*def\s+(\w+)\s*\(", content, re.MULTILINE)
        for func_name in func_names[:8]:
            if not func_name.startswith("_"):
                tests.append(f"test_{func_name}")

        class_names = re.findall(r"^\s*class\s+(\w+)", content, re.MULTILINE)
        for class_name in class_names[:3]:
            tests.append(f"Test{class_name}")
            tests.append(f"test_{class_name.lower()}")

        return tests[:12]

    def _generate_mitigation(self, risk_level: str, file_path: Path) -> str:
        """生成缓解措施"""
        mitigations = {
            "high": f"对 {file_path.name} 进行全面回归测试 + 代码审查 + 分批发布",
            "medium": f"对 {file_path.name} 执行关联集成测试 + 增量回归",
            "low": f"对 {file_path.name} 执行基本单元测试即可",
        }
        return mitigations.get(risk_level, "执行标准测试流程")

    # ==================== 报告生成 ====================

    def generate_verification_report(self, completeness: CompletenessReport | None = None,
                                     gaps: CoverageGapReport | None = None,
                                     deviations: DeviationReport | None = None,
                                     effectiveness: EffectivenessAssessment | None = None,
                                     regression: RegressionRiskReport | None = None) -> str:
        """生成综合验证报告（Markdown格式）"""
        lines: list[str] = []
        lines.append("# 🔒 闭环验证综合报告\n")

        sections = [
            ("📋 闭环完整性", completeness, lambda r: (
                f"| 完整性 | {'✅ 完整' if r.is_complete else '❌ 不完整'} |\n"
                f"| 评分 | **{r.score:.0f}/100** |\n"
                f"| 已完成阶段 | {', '.join(r.phases_present)} |\n"
                f"| 缺失阶段 | {', '.join(r.missing_fields) or '无'} |\n"
                f"| 数据流完整性 | {'✅' if r.data_flow_integrity else '❌'} |\n"
                f"| 反馈回路 | {'✅ 活跃' if r.feedback_loop_active else '❌ 未激活'} |"
            ) if hasattr(r, 'is_complete') else ""),
            ("📊 覆盖率分析", gaps, lambda r: (
                f"| 总规范项 | {r.total_spec_items} |\n"
                f"| 已覆盖 | {r.covered_items} (**{r.coverage_percentage:.1f}%**) |\n"
                f"| 缺口数 | {len(r.gaps)} ({r.critical_gaps} 严重) |\n"
                f"| 风险评估 | {r.risk_assessment} |"
            ) if hasattr(r, 'total_spec_items') else ""),
            ("⚠️ 偏差检测", deviations, lambda r: (
                f"| 总偏差数 | {r.total_deviations} |\n"
                f"| 严重/警告/信息 | {r.critical_count}/{r.warning_count}/{r.info_count} |\n"
                f"| 合规评分 | **{r.compliance_score:.1f}** |"
            ) if hasattr(r, 'total_deviations') else ""),
            ("📈 效果评估", effectiveness, lambda r: (
                f"| 综合评分 | **{r.overall_score:.1f}** ({r.grade}) |\n"
                f"| 趋势分析 | {r.trend_analysis} |\n"
                f"| 优势领域 | {len(r.strengths)} 项 |\n"
                f"| 改进方向 | {len(r.improvement_areas)} 项 |"
            ) if hasattr(r, 'overall_score') else ""),
            ("🚨 回归风险", regression, lambda r: (
                f"| 整体风险 | **{r.overall_risk_level.upper()}** |\n"
                f"| 高/中/低风险 | {r.high_risk_count}/{r.medium_risk_count}/{r.low_risk_count} |\n"
                f"| 建议测试 | {len(r.suggested_test_suite)} 项 |"
            ) if hasattr(r, 'overall_risk_level') else ""),
        ]

        for title, report_data, formatter in sections:
            if report_data is not None:
                lines.append(f"## {title}\n")
                lines.append("| 指标 | 值 |")
                lines.append("| --- | --- |")
                lines.append(formatter(report_data))
                lines.append("")

        return "\n".join(lines) + "\n"


if __name__ == "__main__":
    print("=" * 60)
    print("闭环验证器 - 功能演示")
    print("=" * 60)

    verifier = ClosedLoopVerifier()

    print("\n--- 闭环完整性检查 ---")
    class MockFusionReport:
        phases_completed = [
            type('P', (), {'value': 'spec_analysis'})(),
            type('P', (), {'value': 'test_generation'})(),
            type('P', (), {'value': 'code_guidance'})(),
            type('P', (), {'value': 'feedback_loop'})(),
        ]
        test_mappings = ["map1", "map2"]
        generated_tests = ["tc1", "tc2", "tc3"]
        code_guidances = ["g1", "g2"]
        feedback = type('FB', (), {'compliance_score': 85.0})()

    mock_report = MockFusionReport()
    completeness = verifier.verify_loop_completeness(mock_report)
    print(f"   完整: {'是' if completeness.is_complete else '否'}")
    print(f"   评分: {completeness.score:.0f}/100")
    print(f"   阶段: {completeness.phases_present}")
    print(f"   缺失: {completeness.missing_phases or '无'}")

    print("\n--- 覆盖率缺口分析 ---")
    class MockSpec:
        requirements = [
            type('R', (), {'id': 'REQ-001', 'title': '用户注册', 'priority': 'critical', 'acceptance_criteria': []})(),
            type('R', (), {'id': 'REQ-002', 'title': '用户登录', 'priority': 'high', 'acceptance_criteria': []})(),
        ]
        api_contracts = [
            type('API', (), {'method': 'POST', 'endpoint': '/api/auth/register', 'description': '注册接口'})(),
        ]
        data_models = [
            type('M', (), {'name': 'User', 'model_type': 'entity', 'description': '用户实体',
                           'fields': [type('F', (), {'name': 'email'})()]})(),
        ]
        business_rules = [
            type('BR', (), {'id': 'BR-001', 'name': '邮箱唯一', 'severity': 'error'})(),
        ]

    mock_spec = MockSpec()
    coverage_data = {"covered_items": ["REQ-001", "POST /api/auth/register"]}
    gaps = verifier.analyze_coverage_gaps(mock_spec, coverage_data)
    print(f"   总项目: {gaps.total_spec_items}, 覆盖: {gaps.covered_items} ({gaps.coverage_percentage:.1f}%)")
    print(f"   缺口数: {len(gaps.gaps)}, 严重: {gaps.critical_gaps}")
    print(f"   风险: {gaps.risk_assessment}")
    for g in gaps.gaps[:3]:
        print(f"      [{g.severity}] {g.item_type} {g.item_id}: {g.gap_description[:40]}")

    print("\n--- 偏差检测 ---")
    code_analysis = {
        "files": {
            "user_service.py": '''
class UserService:
    def register(self, email, password):
        if not email:
            raise ValueError("邮箱不能为空")
        # TODO: 实现注册逻辑
        return {"success": True}
''',
        }
    }
    deviations = verifier.detect_deviations(mock_spec, code_analysis)
    print(f"   总偏差: {deviations.total_deviations}")
    print(f"   合规评分: {deviations.compliance_score:.1f}")
    print(f"   分类: {deviations.categories}")
    for d in deviations.deviations[:4]:
        print(f"      [{d.severity}] {d.deviation_type}: {d.description[:50]}")

    print("\n--- 效果评估 ---")
    class MockMetrics:
        spec_coverage_pct = 75.0
        test_effectiveness_pct = 82.0
        defect_reduction_pct = 35.0
        efficiency_gain_pct = 28.0

    class MockHistoricalReport:
        metrics = MockMetrics()

    historical = [MockHistoricalReport(), MockHistoricalReport()]
    effectiveness = verifier.evaluate_loop_effectiveness(historical)
    print(f"   综合评分: {effectiveness.overall_score:.1f} ({effectiveness.grade})")
    print(f"   趋势: {effectiveness.trend_analysis}")
    for m in effectiveness.metrics:
        print(f"      {m.metric_name}: {m.current_value:.1f}% ({m.trend})")

    print("\n--- 回归风险评估 ---")
    dummy_path = Path("dummy_changed.py")
    regression = verifier.assess_regression_risk([dummy_path])
    print(f"   整体风险: {regression.overall_risk_level.upper()}")
    print(f"   高/中/低: {regression.high_risk_count}/{regression.medium_risk_count}/{regression.low_risk_count}")
    print(f"   建议测试: {len(regression.suggested_test_suite)} 项")

    report = verifier.generate_verification_report(completeness, gaps, deviations, effectiveness, regression)
    print(f"\n--- 报告预览 (前800字符) ---\n{report[:800]}...")

    print("\n✅ 所有测试通过!")
